"""Operational supervision and dispatch health; never a scientific stopping rule.

The harness supplies the continuation mechanism. This module reports actionable
work, records observed wake-up configuration, and fences deliberate checkpoints.
It neither launches models nor retries, refunds, recovers leases or resumes runs.
"""
from datetime import datetime, timezone
import json
import time

from .common import canonical

KEY = "supervision"
MODEL_STAGES = ("title", "abstract", "rescue", "audit", "reader")
NATIVE_CACHE = "cache:supervision-native-readiness"


def material_revision(conn):
    from .validation import NONMATERIAL_EVENTS
    marks = ",".join("?" for _ in NONMATERIAL_EVENTS)
    row = conn.execute("SELECT id FROM events WHERE kind NOT IN (" + marks + ") ORDER BY id DESC LIMIT 1", NONMATERIAL_EVENTS).fetchone()
    return row[0] if row else 0


def observe_native(conn, tasks):
    """Cache already derived dispatch metadata, never calibration expectations.

    Called within normal native reconciliation's write transaction. A changed
    ledger invalidates this observation; monitors ask the coordinator to refresh
    it rather than evaluating calibration or scientific rules themselves.
    """
    fields = ("task_id", "task", "paper_id", "deferred_for_source_generation")
    value = {"revision": material_revision(conn),
             "tasks": [{key: task[key] for key in fields if key in task} for task in tasks]}
    encoded = canonical(value)
    old = conn.execute("SELECT value FROM meta WHERE key=?", (NATIVE_CACHE,)).fetchone()
    if not old or old[0] != encoded:
        conn.execute("INSERT OR REPLACE INTO meta VALUES(?,?)", (NATIVE_CACHE, encoded))
    return value


def control(conn):
    row = conn.execute("SELECT value FROM meta WHERE key=?", ("state:" + KEY,)).fetchone()
    return json.loads(row[0]) if row else {}


def admission_hold(conn, run_dir):
    if (run_dir / "STOP").exists():
        return "paused"
    if control(conn).get("mode") == "checkpoint":
        return "checkpoint"
    return None


def record(c, *, actor, reason, mode="active", wakeup=None):
    if mode not in {"active", "checkpoint"} or not all(isinstance(x, str) and x.strip() for x in (actor, reason)):
        raise ValueError("Supervision requires actor, reason and active/checkpoint mode")
    if wakeup is not None:
        required = {"kind", "identifier", "target", "observed_at", "evidence", "status"}
        if not isinstance(wakeup, dict) or set(wakeup) != required or not all(isinstance(v, str) and v.strip() for v in wakeup.values()):
            raise ValueError("Wake-up observation requires kind, identifier, target, observed_at, evidence and status")
        if wakeup["kind"] not in {"same-chat-schedule", "external-supervisor", "interactive-only"} or wakeup["status"] not in {"active", "unavailable", "disabled"}:
            raise ValueError("Unsupported wake-up observation")
        try:
            observed = datetime.fromisoformat(wakeup["observed_at"].replace("Z", "+00:00"))
            if observed.tzinfo is None or observed > datetime.now(timezone.utc):
                raise ValueError()
        except ValueError as exc:
            raise ValueError("Wake-up observation requires a past timezone-bearing timestamp") from exc
        if wakeup["kind"] == "interactive-only" and wakeup["status"] == "active":
            raise ValueError("Interactive supervision does not establish an active wake-up mechanism")
    with c.store._transaction() as conn:
        if mode == "active" and (c.run_dir / "STOP").exists():
            raise ValueError("Run is paused; supervision cannot remove STOP or authorize resume")
        old = control(conn)
        value = dict(old, actor=actor, reason=reason, mode=mode, observed_at=time.time())
        if wakeup is not None:
            value["wakeup"] = wakeup
        # Dedicated operational events do not invalidate a quiet ledger audit.
        c.store._event(conn, "supervision_updated", {"previous": old, "value": value, "reason": reason})
        conn.execute("INSERT OR REPLACE INTO meta VALUES(?,?)", ("state:" + KEY, canonical(value)))
    return value


def snapshot(c, *, now=None):
    """One non-mutating database snapshot, without source hydration or inference."""
    from .transactions import transaction_view
    with c.store._connection() as conn:
        own = not conn.in_transaction
        if own:
            conn.execute("BEGIN")
        try:
            return _snapshot(transaction_view(c, conn), conn, time.time() if now is None else now)
        finally:
            if own:
                conn.rollback()


def _snapshot(c, conn, now):
    from .execution_policy import load, free_slots, native_rank, primary_pending
    from .host_access import profile_blocked
    from .profiles import profile_fingerprint
    from .scheduling import pressure

    policy, saved = load(conn), control(conn)
    hold = admission_hold(conn, c.run_dir)
    host = c.store.get_state("host-access") or {}
    blocks = [json.loads(r[0]) for r in conn.execute("SELECT value FROM meta WHERE key LIKE 'state:access-block:%'")]
    blocks = [b for b in blocks if b.get("active")]
    profiles = {b.get("profile_sha256") for b in blocks if b.get("scope") == "profile"}
    budget = c.store.budget()
    caps = c.plan.get("budgets", {})
    budget_held = any(b.get("scope") == "budget" for b in blocks) or any(
        caps.get(cap) is not None and budget[used] >= caps[cap]
        for cap, used in (("max_calls", "calls"), ("max_tokens", "tokens")))
    deadline = c.store.get_state("execution_deadline")
    timed_out = bool(deadline and now >= deadline["deadline_at"])
    owned = [dict(r) for r in conn.execute("SELECT stage,lease_until,updated_at FROM jobs WHERE state='running'")]
    has_native = conn.execute("SELECT 1 FROM sqlite_master WHERE name='native_task_control'").fetchone()
    controls = {r["task_id"]: dict(r) for r in conn.execute("SELECT * FROM native_task_control")} if has_native else {}
    native_owned = [r for r in controls.values() if r.get("owner")]
    expired = sum(r["lease_until"] is not None and r["lease_until"] <= now for r in owned + native_owned)
    model_owned = sum(r["stage"] in MODEL_STAGES for r in owned) + len(native_owned)
    network_owned = sum(r["stage"] in {"search", "retrieval"} for r in owned)
    slots = free_slots(conn)
    network_slots = max(0, c.plan.get("resources", {}).get("retrieval_workers", 2) - network_owned)
    ready = {"model": 0, "native": 0, "retrieval": 0, "search": 0}
    earliest = []
    predicate, args = c.store.claimable_sql(conn, [*MODEL_STAGES, "retrieval", "search"], now=now)
    pressured = pressure(c)["search_admission_paused"]
    for row in conn.execute("SELECT j.stage,j.available_at,coalesce(json_extract(j.payload,'$.calibration_review'),0) review," + c.store.local_retrieval_sql("j", untried_during_hold=True) + " local_source FROM jobs j WHERE " + predicate, args):
        stage = row["stage"]
        if stage in MODEL_STAGES:
            profile = c.plan.get("calibration_review_profile") if row["review"] else c.plan["profiles"]["reader" if stage == "reader" else "rescue" if stage in {"rescue", "audit"} else stage]
            if budget_held or not profile or profile_fingerprint(profile) in profiles or profile_blocked(host, profile):
                continue
            ready["model"] += 1
        else:
            if stage == "search" and (pressured or host.get("network")):
                continue
            if stage == "retrieval" and host.get("network") and not row["local_source"]:
                continue
            ready[stage] += 1
        earliest.append(row["available_at"])
    discovery_needed = False
    discovery_actionable = False
    native_current = True
    if c.plan.get("mode") == "discovery":
        from .discovery import STATE, _search_candidate
        from . import frontiers
        row = conn.execute("SELECT value FROM meta WHERE key=?", (NATIVE_CACHE,)).fetchone()
        cached = json.loads(row[0]) if row else {}
        native_current = cached.get("revision") == material_revision(conn)
        discovery_needed = not native_current
        discovery_actionable = discovery_needed and slots != 0
        preferred = policy["retained_first"] and primary_pending(conn)
        for task in cached.get("tasks", []) if native_current else []:
            ctl = controls.get(task["task_id"], {})
            if task.get("deferred_for_source_generation") or ctl.get("owner") or ctl.get("available_at", 0) > now:
                continue
            if preferred and native_rank(conn, task, policy)[0]:
                continue
            ready["native"] += 1
            earliest.append(ctl.get("available_at", 0))
        state = c.store.get_state(STATE)
        if not state:
            discovery_needed = True
            discovery_actionable = True
        else:
            for obligation in frontiers.due_obligations(state):
                if obligation.get("task") == "replay-citation-provenance":
                    discovery_needed = True
                    discovery_actionable = True
                elif not obligation.get("task") and not pressured and not host.get("network"):
                    _, _, old = _search_candidate(c, obligation)
                    if old is None:
                        discovery_needed = True
                        discovery_actionable = True
    inference_ready = bool((ready["model"] or ready["native"]) and slots != 0)
    network_ready = bool((ready["search"] or ready["retrieval"]) and network_slots)
    projection_needed = bool(c.store.unprojected_results(limit=1))
    actionable = (inference_ready or network_ready or projection_needed or discovery_actionable) and not hold and not timed_out
    # A monitoring heartbeat must never hide a dispatch stall. Use work events,
    # not the supervisor's self-reported contact time, to measure the idle gap.
    event = conn.execute("SELECT at FROM events WHERE kind IN ('job_claimed','native_task_reserved','job_completed','native_task_submission_finished','execution_session_finished') ORDER BY id DESC LIMIT 1").fetchone()
    latest = event[0] if event else 0
    initialized = conn.execute("SELECT min(at) FROM events").fetchone()[0] or now
    since = max(latest, min(earliest) if earliest else 0, initialized)
    idle_seconds = max(0, now - since) if actionable else 0
    total_owned = len(owned) + len(native_owned)
    integrity_error = None
    from .validation import require_integrity
    try:
        require_integrity(c)
    except ValueError as exc:
        integrity_error = str(exc)
    if hold:
        state, action = hold, "Drain admitted workers; do not dispatch or automatically clear this hold."
    elif integrity_error:
        state, action = "blocked", "Resolve the recorded integrity failure before new admissions."
    elif timed_out:
        state, action = "blocked", "Recorded execution allowance expired; retain pending work."
    elif actionable:
        state = "stalled" if not total_owned and idle_seconds >= 60 else "awaiting-supervisor"
        action = "Refill eligible free slots now through work/native-work and the managed runner; retain all existing leases."
    elif total_owned:
        state, action = "awaiting-worker-reconciliation" if expired else "working", "Wait for the next completion, reconcile it, then refill immediately. Expiry alone never authorizes reclaim."
    else:
        pending = conn.execute("SELECT count(*) FROM jobs j WHERE j.state IN ('pending','failed','parked') AND NOT EXISTS(SELECT 1 FROM job_supersessions s WHERE s.job_id=j.id) AND NOT EXISTS(SELECT 1 FROM retry_links r WHERE r.parent_id=j.id)").fetchone()[0]
        state = "blocked-or-waiting" if pending or blocks else "no-ready-work"
        action = "Inspect unresolved obligations and deferred work; this is not scientific completion."
    if integrity_error or timed_out or hold:
        actionable = False
    wakeup = saved.get("wakeup")
    return {"state": state, "next_action": action, "observed_at": now,
        "active_workers": total_owned, "active_inference_workers": model_owned,
        "expired_owned_leases": expired, "free_inference_slots": slots, "free_retrieval_slots": network_slots,
        "eligible_work": ready, "dispatch_needed": actionable,
        "projection_needed": projection_needed,
        "native_readiness_current": native_current,
        "discovery_reconciliation_needed": discovery_needed,
        "idle_seconds": idle_seconds, "may_end_turn": not total_owned and not actionable,
        "supervisor": saved, "wakeup_observation": wakeup,
        "continuation_configured": bool(wakeup and wakeup["status"] == "active"),
        "continuation_verified_by_runtime": False,
        "integrity_error": integrity_error, "scientific_completion": False,
        "limitations": "The harness must install and verify its same-run wake-up mechanism and external worker allowance. This command does not schedule future execution or infer worker death."}
