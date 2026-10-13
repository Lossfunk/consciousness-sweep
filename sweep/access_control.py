"""Explicit recovery of operational access blocks, never scientific decisions.

Blocks prevent unattended polling of authentication/configuration failures.
Resolution authorizes only a fresh access check under unchanged run settings.
An unknown/admitted failure still needs the normal charged-attempt retry path.
"""
import datetime as dt
import json
import time

from .common import canonical, file_hash
from .profiles import profile_fingerprint


def _store(value):
    return value.store if hasattr(value, "store") else value


def active_blocks(coordinator_or_store):
    with _store(coordinator_or_store)._connection() as conn:
        rows = conn.execute("SELECT key,value FROM meta WHERE key LIKE 'state:access-block:%' ORDER BY key")
        result = []
        for row in rows:
            value = json.loads(row["value"])
            if value and value.get("active"):
                result.append(dict(value, block_key=row["key"][len("state:"):]))
        return result


def blocked_profiles(coordinator_or_store):
    return {b["profile_sha256"] for b in active_blocks(coordinator_or_store) if b["scope"] == "profile"}


def blocked_jobs(coordinator_or_store):
    return {b["job_id"] for b in active_blocks(coordinator_or_store) if b["scope"] == "job"}


def _set(store, conn, key, previous, value, reason):
    store._event(conn, "control_updated", {"key": key, "previous": previous, "value": value, "reason": reason})
    conn.execute("INSERT OR REPLACE INTO meta(key,value) VALUES(?,?)", ("state:" + key, canonical(value)))


def reconcile_nonadmission(coordinator, job, prompt, schema):
    """Recover a verified denial written before its reservation was reconciled.

    A coordinator crash can leave a confirmed HTTP rejection conservatively
    charged as unknown. Reconcile that exact immutable request before its
    adapter archives the denial and attempts another admission. A timeout,
    absent receipt, changed binding or unverified local failure cannot refund it.
    """
    from . import adapters
    from .profiles import validate_profile

    store = coordinator.store
    reservation = store.reservation_for_job(job["id"])
    if not reservation or reservation["state"] not in {"admitted", "unknown"}:
        return False
    directory = coordinator.run_dir / "jobs" / job["id"] / "execution"
    path = directory / "receipt.json"
    if not path.is_file():
        return False
    receipt = json.loads(path.read_text())
    if receipt.get("admission") != "not-admitted":
        return False
    profile = validate_profile(coordinator.profile_for_job(job))
    if (profile["adapter"] != "openai-compatible" or receipt.get("http_status") not in {401, 403, 429}
            or receipt.get("status") not in {"deferred", "failed"} or not receipt.get("completed_at")):
        raise ValueError("Unsettled admission lacks a confirmed terminal HTTP rejection")
    binding_path = directory / "binding.json"
    binding = json.loads(binding_path.read_text())
    expected = {"version": adapters.VERSION, "profile": profile,
        "prompt_sha256": adapters._sha(prompt.encode()), "schema_sha256": adapters._sha(adapters._bytes(schema)),
        "adapter_source_sha256": file_hash(adapters.__file__), "base_instructions_sha256": None}
    if (binding != expected or file_hash(binding_path) != receipt.get("binding_sha256")
            or file_hash(directory / "prompt.txt") != expected["prompt_sha256"]
            or file_hash(directory / "schema.json") != expected["schema_sha256"]
            or receipt.get("requested_model") != profile["model"]
            or receipt.get("requested_effort") != profile["effort"]):
        raise ValueError("Rejection recovery no longer matches the immutable source/profile request")
    dispatch = json.loads((directory / "dispatch.json").read_text())
    if dispatch.get("binding_sha256") != receipt["binding_sha256"] or dispatch.get("admission") != "unknown":
        raise ValueError("Rejection recovery dispatch binding changed")
    times = [dt.datetime.fromisoformat(value) for value in
             (receipt["started_at"], dispatch["reserved_at"], receipt["completed_at"])]
    if any(value.tzinfo is None for value in times) or not times[0] <= times[1] <= times[2]:
        raise ValueError("Rejection recovery lacks an ordered terminal request receipt")
    store.event("model_receipt", {"job_id": job["id"], "receipt": dict(receipt, recovered=True)})
    store.reject_admission(reservation["id"], "Recovered exact confirmed HTTP nonadmission after interrupted bookkeeping", receipt)
    return True


def resolve(coordinator, reason, actor="supervising-agent"):
    """Record explicit intervention without changing caps, profiles or evidence."""
    if not isinstance(reason, str) or not reason.strip() or not isinstance(actor, str) or not actor.strip():
        raise ValueError("Access resolution requires the actual fix/reason and an actor")
    store = coordinator.store
    blocks = active_blocks(store)
    grants, failed = {}, []
    for job_id in sorted({b["job_id"] for b in blocks}):
        job = store.job(job_id)
        if not job:
            raise ValueError("Access block references an absent job")
        if job["state"] == "running":
            raise ValueError("Resolve access after the affected worker has reached a checkpoint")
        if job["state"] == "failed":
            failed.append(job_id)
            continue
        directory = coordinator.run_dir / "jobs" / job_id / "execution"
        receipt_path, binding_path = directory / "receipt.json", directory / "binding.json"
        if not receipt_path.exists():
            # A budget rejection can occur in the admission callback before a
            # request marker or receipt exists. Recheck the same budget later.
            if (directory / "dispatch.json").exists() or job.get("attempts"):
                raise ValueError("Cannot resolve a possibly admitted request without its terminal receipt")
            continue
        receipt = json.loads(receipt_path.read_text())
        if receipt.get("admission") != "not-admitted" or not receipt.get("completed_at"):
            raise ValueError("Pending access recovery requires confirmed terminal nonadmission")
        binding = json.loads(binding_path.read_text())
        profile = coordinator.profile_for_job(job)
        if binding.get("profile") != profile or receipt.get("binding_sha256") != file_hash(binding_path):
            raise ValueError("Access recovery cannot change or bypass the bound profile/source request")
        if file_hash(directory / "prompt.txt") != binding.get("prompt_sha256") or file_hash(directory / "schema.json") != binding.get("schema_sha256"):
            raise ValueError("Access recovery source instructions or schema changed")
        latest = store.reservation_for_job(job_id)
        if latest and latest["state"] != "released":
            raise ValueError("Confirmed nonadmission must be reconciled before access recovery")
        previous = store.get_state("admission-retry:" + job_id) or {}
        grants[job_id] = {"active": True, "generation": previous.get("generation", 0) + 1,
            "profile_sha256": profile_fingerprint(profile), "binding_sha256": receipt["binding_sha256"],
            "receipt_sha256": file_hash(receipt_path), "reason": reason.strip(), "actor": actor.strip(),
            "authorized_at": time.time(), "admission": "not-admitted"}
    with store._transaction() as conn:
        for block in blocks:
            key = block["block_key"]
            row = conn.execute("SELECT value FROM meta WHERE key=?", ("state:" + key,)).fetchone()
            previous = {k: v for k, v in block.items() if k != "block_key"}
            if not row or json.loads(row[0]) != previous:
                raise ValueError("Access state changed during resolution; read the current checkpoint first")
            value = dict(previous, active=False, resolved_at=time.time(), resolution_reason=reason.strip(), resolved_by=actor.strip())
            _set(store, conn, key, previous, value, "Explicit access recovery under unchanged settings: " + reason.strip())
        for job_id, value in grants.items():
            key = "admission-retry:" + job_id
            row = conn.execute("SELECT value FROM meta WHERE key=?", ("state:" + key,)).fetchone()
            _set(store, conn, key, json.loads(row[0]) if row else None, value,
                 "Explicit fresh admission check after verified nonadmission")
        store._event(conn, "access_blocks_resolved", {"reason": reason.strip(), "actor": actor.strip(),
            "block_keys": [b["block_key"] for b in blocks], "nonadmission_retry_jobs": sorted(grants),
            "failed_jobs_requiring_charged_retry": failed, "budgets_changed": False, "profiles_changed": False})
    return {"cleared_blocks": len(blocks), "nonadmission_retry_jobs": sorted(grants),
            "failed_jobs_requiring_charged_retry": failed, "budgets_changed": False,
            "reason": "Access will be rechecked under the same caps and settings; unknown/admitted failures were not retried."}


def retry_permission(coordinator, job):
    grant = coordinator.store.get_state("admission-retry:" + job["id"])
    if not grant or not grant.get("active"):
        return None
    directory = coordinator.run_dir / "jobs" / job["id"] / "execution"
    receipt = json.loads((directory / "receipt.json").read_text())
    if grant.get("profile_sha256") != profile_fingerprint(coordinator.profile_for_job(job)) or grant.get("binding_sha256") != receipt.get("binding_sha256"):
        raise ValueError("Explicit nonadmission retry grant no longer matches its request receipt")
    if grant.get("receipt_sha256") != file_hash(directory / "receipt.json"):
        # A crash after dispatch can precede grant consumption. A preserved
        # exact rejection plus a new bound dispatch proves the authorized check
        # already started; recover that receipt instead of duplicating it.
        archived = any(file_hash(path) == grant["receipt_sha256"]
                       for path in (directory / "rejections").glob("rejection-*/receipt.json"))
        marker = directory / "dispatch.json"
        if archived and marker.exists() and json.loads(marker.read_text()).get("binding_sha256") == grant["binding_sha256"]:
            consume_retry_permission(coordinator, job, grant)
            return None
        raise ValueError("Explicit nonadmission retry grant no longer matches its request receipt")
    if receipt.get("admission") != "not-admitted":
        raise ValueError("A nonadmission retry cannot release an uncertain or admitted request")
    return grant


def consume_retry_permission(coordinator, job, grant):
    coordinator.store.set_state("admission-retry:" + job["id"], dict(grant, active=False, consumed_at=time.time()),
                               "The explicitly authorized fresh admission check returned; permission is not reusable")
