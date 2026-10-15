"""Execution-only queue controls; no scientific decision or total-work cutoff.

Small, untouched screening jobs may share a new immutable request. Search
backpressure delays admission while downstream work catches up; every frontier
and already retrieved encounter remains durable.
"""
import json
import time

from .common import canonical, digest


def pressure(coordinator):
    resources = coordinator.plan.get("resources", {})
    high = resources.get("discovery_buffer_papers") or max(250, 100 * resources.get("model_workers", 1))
    with coordinator.store._connection() as conn:
        # The status index bounds work to the live backlog, not all assessed papers.
        counts = {r["status"]: r["n"] for r in conn.execute(
            "SELECT status,count(*) n FROM papers WHERE status IN "
            "('discovered','title-pending','abstract-pending','rescue-pending',"
            "'retrieval-pending','reader-pending') GROUP BY status")}
        search_jobs = conn.execute("SELECT count(*) FROM jobs j WHERE stage='search' "
            "AND state IN ('pending','running') AND NOT EXISTS "
            "(SELECT 1 FROM job_supersessions s WHERE s.job_id=j.id)").fetchone()[0]
    from .workflow import enabled
    if enabled(coordinator):
        with coordinator.store._connection() as conn:
            counts = {r["status"]: r["n"] for r in conn.execute(
                "SELECT status,count(*) n FROM papers WHERE status IN ('discovered','title-pending','abstract-pending','abstract-lookup-pending','rescue-pending','retrieval-pending','reader-pending') AND coalesce(json_extract(record,'$.workflow_defer.active'),0)=0 GROUP BY status")}
    with coordinator.store._connection() as conn:
        audits = conn.execute("SELECT count(DISTINCT p.id) FROM meta m,json_each(m.value,'$.native_assessment_pending') n JOIN papers p ON p.id=n.key WHERE m.key='state:discovery_frontiers' AND p.status IN ('assessed','reading-incomplete') AND json_extract(p.record,'$.packet_path') IS NOT NULL AND coalesce(json_extract(p.record,'$.workflow_defer.active'),0)=0").fetchone()[0]
    if audits:
        counts["native-assessment-pending"] = audits
    total = sum(counts.values())
    from .execution_policy import for_coordinator, uncertain_sql, contextual_followup_sql
    policy = for_coordinator(coordinator)
    contextual = 0
    if policy.get("workflow") == "focused-v1" and policy["retained_first"]:
        with coordinator.store._connection() as conn:
            contextual = conn.execute("SELECT count(DISTINCT p.id) FROM meta m,json_each(m.value,'$.native_assessment_pending') n JOIN papers p ON p.id=n.key WHERE m.key='state:discovery_frontiers' AND coalesce(json_extract(p.record,'$.workflow_defer.active'),0)=0 AND " + contextual_followup_sql()).fetchone()[0]
    deferred = 0
    if policy["retained_first"] and not enabled(coordinator):
        with coordinator.store._connection() as conn:
            deferred = conn.execute("SELECT count(*) FROM papers p WHERE p.status IN ('retrieval-pending','reader-pending') AND " + uncertain_sql()).fetchone()[0]
    backlog = total - deferred - contextual
    return {"papers_waiting": backlog, "total_papers_waiting": total, "deferred_uncertain": deferred,
            "background_contextual_native": contextual, "by_status": counts,
            "high_water_papers": high, "search_admission_paused": backlog >= high,
            "queued_search_jobs": search_jobs,
            "search_queue_target": max(2, 2 * resources.get("retrieval_workers", 2)),
            "scope": "temporary admission control, not a search or paper limit"}


def coalesce(coordinator, *, max_candidates=100):
    """Atomically combine unclaimed partial title/abstract requests.

    Never edit an existing job or combine different evidence for one paper.
    Prepared, leased, retried, dependency-bound and admitted jobs are untouched.
    The old jobs point to the successor and retain their complete provenance.
    A partial tail remains immediately dispatchable (no wait-for-full-batch).
    """
    store = coordinator.store
    merged = []
    with store._transaction() as conn:
        for stage, size in (("title", 25), ("abstract", 10)):
            rows = conn.execute("SELECT j.* FROM jobs j WHERE j.stage=? AND j.state='pending' "
                "AND j.token=0 AND j.attempts=0 AND j.available_at<=? "
                "AND json_array_length(j.payload,'$.paper_ids')<? "
                "AND NOT EXISTS(SELECT 1 FROM job_supersessions s WHERE s.job_id=j.id) "
                "AND NOT EXISTS(SELECT 1 FROM dependencies d WHERE d.job_id=j.id OR d.dependency_id=j.id) "
                "AND NOT EXISTS(SELECT 1 FROM reservations r WHERE r.job_id=j.id) "
                "ORDER BY j.id LIMIT ?", (stage, time.time(), size, max_candidates)).fetchall()
            group, seen, origin, priority, workflow = [], set(), None, None, None

            def flush():
                if len(group) < 2:
                    return
                payload = {"paper_ids": [], "source_records": [], "metadata_revisions": {},
                           "screen_evidence_bindings": {}}
                for row, data in group:
                    payload["paper_ids"].extend(data["paper_ids"])
                    payload["source_records"].extend(data["source_records"])
                    for name in ("metadata_revisions", "screen_evidence_bindings"):
                        payload[name].update(data.get(name, {}))
                payload["source_sha256"] = digest(payload["source_records"])
                if origin is not None:
                    payload["origin"] = origin
                if workflow is not None:
                    payload["screening_workflow"] = workflow
                parents = [r["id"] for r, _ in group]
                key = "coalesced:" + digest([parents, payload])
                jid, now = store._id(conn, "job", "J"), time.time()
                encoded = canonical(payload)
                conn.execute("INSERT INTO jobs(id,stage,key,payload,priority,state,available_at,created_at,updated_at) "
                    "VALUES(?,?,?,?,?,'pending',?,?,?)", (jid, stage, key, encoded, priority, now, now, now))
                store._event(conn, "job_enqueued", {"job_id": jid, "stage": stage, "key": key,
                    "payload_sha256": digest(encoded.encode()), "dependencies": []})
                for parent in parents:
                    store._supersede_job(conn, parent, jid, "Unclaimed compatible partial batches combined; original source snapshots retained")
                store._event(conn, "screen_batches_coalesced", {"source_job_ids": parents, "job_id": jid,
                    "paper_ids": payload["paper_ids"], "reason": "Amortize context without dropping papers or changing paper-specific evidence"})
                merged.append(jid)

            for row in rows:
                data = json.loads(row["payload"])
                ids = data.get("paper_ids", [])
                if ((coordinator.run_dir / "jobs" / row["id"]).exists()
                        or set(data) - {"paper_ids", "source_records", "source_sha256", "metadata_revisions", "screen_evidence_bindings", "origin", "screening_workflow"}
                        or not ids or [p.get("paper_id") for p in data.get("source_records", [])] != ids
                        or digest(data["source_records"]) != data.get("source_sha256")):
                    continue
                if group and (len(seen) + len(ids) > size or seen.intersection(ids)
                              or data.get("origin") != origin or row["priority"] != priority or data.get("screening_workflow") != workflow):
                    flush()
                    group, seen = [], set()
                if not group:
                    origin, priority, workflow = data.get("origin"), row["priority"], data.get("screening_workflow")
                group.append((row, data))
                seen.update(ids)
            flush()
    return merged
