"""Explicit fresh attempts after terminal model failures, preserving prior costs.

No timer or worker calls this module. A supervising agent/operator must provide
a reason and attribution. Local request completion is not proof that a remote
provider stopped computing or did not charge for a timed-out request.
"""
import json
from pathlib import Path

from . import adapters, reading, screening
from .common import digest, file_hash, inside
from .profiles import profile_fingerprint, validate_profile

MODEL_STAGES = {"title", "abstract", "rescue", "audit", "reader"}


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _source(coordinator, job):
    payload, stage = job["payload"], job["stage"]
    if stage == "reader":
        path = inside(coordinator.run_dir / payload["packet_path"], coordinator.run_dir)
        source = _load(path)
        expected = payload.get("packet_sha256") or path.name.split(".", 1)[0]
        _require(digest(source) == expected, "Retry source packet no longer matches its immutable job binding")
        from .workflow import prepare_reader
        return source, prepare_reader(source, payload)
    records = payload["source_records"]
    _require(digest(records) == payload["source_sha256"], "Retry metadata snapshot hash changed")
    _require([record["paper_id"] for record in records] == payload["paper_ids"], "Retry metadata membership changed")
    papers = []
    for record in records:
        paper = {key: record.get(key) for key in ("paper_id", "title", "year", "authors", "doi")}
        if stage != "title":
            paper["abstract"] = record.get("abstract") or None
        papers.append(paper)
    from .workflow import prepare_screen
    return {"papers": papers}, prepare_screen(stage, papers, payload)


def terminal_evidence(coordinator, job, conn=None, history=None):
    """Verify source, settings, receipt and locally terminal transport read-only."""
    _require(job is not None and job["state"] == "failed", "Only a failed terminal model job can receive a fresh retry")
    _require(job["stage"] in MODEL_STAGES, "Fresh retries apply only to terminal model jobs")
    _require(job.get("owner") is None and job.get("lease_until") is None,
             "A failed retry parent cannot retain a live lease")
    root = Path(coordinator.run_dir).resolve()
    directory = inside(root / "jobs" / job["id"], root)
    execution = inside(directory / "execution", root)
    receipt_path = inside(execution / "receipt.json", root)
    receipt = _load(receipt_path)
    binding = _load(inside(execution / "binding.json", root))
    _require(file_hash(execution / "binding.json") == receipt.get("binding_sha256"), "Failed receipt binding hash changed")
    _require(receipt.get("status") in {"failed", "deferred", "completed"} and receipt.get("completed_at"),
             "Request lacks a terminal receipt; reconcile the original worker before considering a retry")
    _require(receipt.get("admission") in {"admitted", "unknown"},
             "Confirmed nonadmission uses normal deferred work, not a fresh charged attempt")
    profile = validate_profile(coordinator.profile_for_job(job))
    _require(binding.get("profile") == profile, "Retry cannot change the immutable run's model or settings")
    from .continuation import compatible_adapter_hash
    _require(binding.get("version") == adapters.VERSION and compatible_adapter_hash(coordinator, binding.get("adapter_source_sha256")),
             "Retry adapter differs from the current or explicitly continued predecessor runtime")
    _require(receipt.get("requested_model") == profile["model"] and receipt.get("requested_effort") == profile["effort"],
             "Failed receipt model/effort differs from the selected profile")
    source, (prompt, schema) = _source(coordinator, job)
    _require(_load(directory / "source.json") == source, "Prepared retry source differs from queued evidence")
    _require((directory / "prompt.txt").read_bytes() == prompt.encode(), "Scientific instructions changed since the failed attempt")
    _require(_load(directory / "schema.json") == schema, "Scientific schema changed since the failed attempt")
    task = _load(directory / "task.json")
    _require(task.get("job_id") == job["id"] and task.get("stage") == job["stage"] and task.get("token") == job["token"],
             "Failed prepared task identity changed")
    _require(task.get("source") == source and task.get("source_sha256") == digest(source), "Failed prepared source hash changed")
    prompt_hash = digest(prompt.encode())
    _require(task.get("prompt_sha256") == prompt_hash and task.get("schema_sha256") == digest(schema),
             "Failed prepared prompt/schema binding changed")
    _require(binding.get("prompt_sha256") == prompt_hash and file_hash(execution / "prompt.txt") == prompt_hash,
             "Failed provider prompt differs from prepared task")
    _require(file_hash(execution / "schema.json") == binding.get("schema_sha256") and _load(execution / "schema.json") == schema,
             "Failed provider schema differs from prepared task")
    dispatch = _load(execution / "dispatch.json")
    _require(dispatch.get("binding_sha256") == receipt["binding_sha256"], "Failed dispatch marker changed")
    if binding.get("base_instructions_sha256") is not None:
        _require(file_hash(execution / "base_instructions.txt") == binding["base_instructions_sha256"] == receipt.get("base_instructions_sha256"),
                 "Failed base-instruction binding changed")
    if receipt["status"] == "completed":
        _require(file_hash(execution / "result.json") == receipt.get("result_sha256") and _load(execution / "result.json") == receipt.get("result"),
                 "Completed provider result changed after failing stage validation")
    if profile["adapter"] in {"codex", "claude", "command"}:
        code = receipt.get("exit_code")
        _require((isinstance(code, int) and not isinstance(code, bool) and receipt.get("timed_out") is False)
                 or (code is None and receipt.get("timed_out") is True),
                 "CLI receipt does not establish that its child exited or was killed and waited for")
        terminal = "local-process-exited"
    else:
        _require(profile["adapter"] == "openai-compatible", "Manual exchange is resolved by its supervising agent")
        terminal = "http-request-returned"

    def recorded(connection):
        event = None
        if history is not None:
            candidate = history("model_receipt", job["id"])
            event = candidate.get("receipt") if candidate else None
        else:
            for row in connection.execute("SELECT payload FROM events WHERE kind='model_receipt' ORDER BY id DESC"):
                candidate = json.loads(row[0])
                if candidate.get("job_id") == job["id"]:
                    event = candidate["receipt"]
                    break
        # Cache recovery can add this operational flag without changing the
        # immutable receipt bytes. No scientific/output field may differ.
        if event is not None:
            event = {key: value for key, value in event.items() if key != "recovered"}
        _require(event == {key: value for key, value in receipt.items() if key != "recovered"},
                 "Failed receipt differs from its durable model receipt event")
        reservation = connection.execute("SELECT state,admitted FROM reservations WHERE job_id=? ORDER BY created_at DESC,id DESC LIMIT 1", (job["id"],)).fetchone()
        _require(reservation is not None and reservation["admitted"] and reservation["state"] in {"unknown", "settled", "unmetered"},
                 "Failed request's budget reservation must remain durably charged before a fresh attempt")

    if conn is None:
        with coordinator.store._connection() as connection:
            recorded(connection)
    else:
        recorded(conn)
    return {"kind": "terminal-model-receipt", "receipt_path": str(receipt_path.relative_to(root)),
            "receipt_sha256": file_hash(receipt_path), "binding_sha256": receipt["binding_sha256"],
            "prompt_sha256": prompt_hash, "schema_sha256": digest(schema), "source_sha256": digest(source),
            "profile_sha256": profile_fingerprint(profile), "terminal_transport": terminal,
            "receipt_status": receipt["status"], "admission": receipt["admission"], "completed_at": receipt["completed_at"]}


def retry(coordinator, job_id, reason, actor):
    """Queue exactly one new child; reissuing the command returns that child."""
    _require(str(reason).strip() and str(actor).strip(), "A fresh retry requires a substantive reason and actor")
    job = coordinator.store.job(job_id)
    evidence = terminal_evidence(coordinator, job)
    child_id = coordinator.store.retry_failed(job_id, reason, actor, evidence)
    return {"parent_job_id": job_id, "job_id": child_id, "status": coordinator.store.job(child_id)["state"],
            "reason": "Explicit fresh attempt queued with unchanged evidence/settings; previous request remains charged and auditable.",
            "budget": coordinator.store.budget(),
            "limitations": ["A timeout does not establish remote nonexecution or zero provider cost.",
                            "The fresh attempt must fit the remaining run allowance; unknown usage can still block token/cost-capped dispatch."]}


def validate_retries(coordinator, conn, error, checked, history):
    """Include every old receipt and lineage in a quiet operational audit."""
    for row in conn.execute("SELECT * FROM retry_links ORDER BY parent_id"):
        try:
            parent_row = conn.execute("SELECT * FROM jobs WHERE id=?", (row["parent_id"],)).fetchone()
            child = conn.execute("SELECT * FROM jobs WHERE id=?", (row["child_id"],)).fetchone()
            _require(parent_row is not None and child is not None, "Retry lineage references an absent job")
            parent = coordinator.store._job(parent_row)
            _require(all(parent_row[key] == child[key] for key in ("stage", "payload", "priority")), "Retry changed its parent's immutable work unit")
            _require(child["created_at"] >= parent_row["created_at"] and child["id"] > parent["id"], "Retry lineage is not forward-only")
            evidence = terminal_evidence(coordinator, parent, conn, history)
            _require(json.loads(row["evidence"]) == evidence, "Retry's original terminal evidence changed")
            _require(str(row["reason"]).strip() and str(row["actor"]).strip(), "Retry lacks supervisory attribution or reason")
            value = history("job_retry_authorized", row["parent_id"])
            _require(value is not None, "Retry lineage has no authorization event")
            _require(value.get("child_id") == row["child_id"] and value.get("evidence") == evidence
                     and value.get("reason") == row["reason"] and value.get("actor") == row["actor"],
                     "Retry lineage differs from its authorization history")
            dependencies = lambda jid: [d[0] for d in conn.execute("SELECT dependency_id FROM dependencies WHERE job_id=? ORDER BY dependency_id", (jid,))]
            _require(dependencies(parent["id"]) == dependencies(child["id"]), "Retry changed its parent's dependency inputs")
            checked("terminal_retries")
        except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
            error("retry_binding", row["parent_id"], exc)
