"""Connect public discovery to the durable prospect coordinator.

The network adapters perform retrieval, not native scientific certification.
Agent work exchange handles native route decisions and citation-wave audits.
The frozen native ledger/validator remains the authority for certification.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path
import time

from . import frontiers, sources
from .common import canonical, digest, file_hash, inside, save_json, science_root

STATE = "discovery_frontiers"


def _change(c, function, reason):
    return c.store.mutate_state_compact(STATE, function, reason, history_field="history")


def _ingest_once(c, key, record, provenance):
    """One atomic source encounter per saved snapshot ordinal, including restart."""
    marker = "state:encounter:" + key
    with c.store._transaction() as conn:
        old = conn.execute("SELECT value FROM meta WHERE key=?", (marker,)).fetchone()
        if old:
            return tuple(json.loads(old[0]))
        record = dict(record, discovery_bridge_depths=[provenance.get("bridge_depth", 0)])
        result = c.store._add_paper(conn, record, provenance)
        retained = json.loads(conn.execute("SELECT record FROM papers WHERE id=?", (result[0],)).fetchone()[0])
        depths = sorted(set(retained.get("discovery_bridge_depths", []) + [provenance.get("bridge_depth", 0)]))
        if retained.get("discovery_bridge_depths") != depths:
            retained["discovery_bridge_depths"] = depths
            c.store._event(conn, "bridge_lineage_encounter", {"paper_id": result[0], "depths": depths, "provenance": provenance})
            conn.execute("UPDATE papers SET record=?,updated_at=? WHERE id=?", (canonical(retained), time.time(), result[0]))
        conn.execute("INSERT INTO meta VALUES(?,?)", (marker, canonical(result)))
        return result


def initialize_discovery(c):
    if c.plan.get("mode") != "discovery":
        raise ValueError("Discovery initialization requires an explicitly selected discovery run")
    if c.store.get_state(STATE) is None:
        c.store.set_state(STATE, frontiers.initial_state(), "Frozen principal-first discovery obligations initialized")
    for filename, role in (("seeds_empirical.csv", "empirical-seed"), ("seeds_reviews.csv", "review-anchor")):
        path = science_root() / filename
        source_hash = file_hash(path)
        with path.open(newline="", encoding="utf-8-sig") as handle:
            rows = list(csv.DictReader(handle))
        # Validate every identity before allocating an ID from this input.
        if any(not row.get("title", "").strip() for row in rows):
            raise ValueError("Frozen seed identity lacks title")
        for ordinal, record in enumerate(rows):
            record = {k: record.get(k) for k in ("title", "authors", "year", "doi", "url")}
            record["status"] = "discovery-anchor" if role == "review-anchor" else "discovered"
            key = "seed:" + source_hash + ":" + str(ordinal)
            pid, _ = _ingest_once(c, key, record, {"route": role, "source_sha256": source_hash, "ordinal": ordinal, "bridge_depth": 0})
            paper = c.store.paper(pid)
            _change(c, lambda s, p=paper: frontiers.add_anchor(s, p, role=role, reason="Frozen seed/anchor identity initializes the principal route"), "Principal seed obligation recorded")
            if role == "empirical-seed" and paper["status"] == "discovered":
                c._enqueue_batch("title", [pid], key_prefix=key + ":")
                c.store.update_paper(pid, {"status": "title-pending"}, "Frozen empirical seed enters source-specific semantic screening")
    _change(c, lambda s: frontiers.initialize_principal(s, seeds_complete=True, anchors_complete=True,
              reason="All frozen empirical seeds and review anchors indexed"), "Principal input initialization complete")
    c.store.set_state("discovery_initialized", True, "Frozen discovery seed initialization complete")
    return discovery_tick(c)


def _all_papers(c):
    cursor = None
    while True:
        batch = c.store.papers(limit=1000, after_id=cursor)
        if not batch:
            return
        yield from batch
        cursor = batch[-1]["paper_id"]


def _pending_semantic(c):
    status = c.store.status()
    return sum(n for stage, counts in status["jobs"].items() if stage != "search"
               for state, n in counts.items() if state != "complete")


def discovery_tick(c):
    if c.plan.get("mode") != "discovery":
        return None
    state = c.store.get_state(STATE)
    if state is None:
        return initialize_discovery(c)
    # Reconcile one bounded indexed page of completed reader jobs, not a scan
    # of the potentially 450k-paper corpus on every scheduler tick. The normal
    # reader projection hook queues immediately; this is restart repair only.
    cursor = c.store.get_state("discovery_reader_cursor")
    jobs = c.store.list_jobs(stage="reader", state="complete", limit=100, after_id=cursor)
    for job in jobs:
        paper = c.store.paper(job["payload"]["paper_id"])
        if paper and paper["status"] in {"assessed", "reading-incomplete"}:
            queue_native_after_reader(c, paper["paper_id"])
        else:
            # Do not advance past an unprojected completed result.
            break
        c.store.set_state("discovery_reader_cursor", job["id"], "Bounded completed-reader audit reconciliation cursor")
    state = c.store.get_state(STATE)
    scheduled = 0
    for obligation in frontiers.due_obligations(state):
        if obligation.get("task") == "replay-citation-provenance":
            _replay_lineage(c, obligation)
            continue
        if obligation.get("task"):
            continue
        payload = {k: obligation.get(k) for k in ("source", "query", "limit", "cursor", "kind", "parent", "phase", "window_key", "obligation_id", "child_bridge_depth")}
        key = digest(payload)
        if c.store.job_by_key("search", key) is not None:
            continue
        c.store.enqueue("search", key, payload, priority=10)
        scheduled += 1
    return {"phase": state["phase"], "scheduled_source_jobs": scheduled,
            "native_tasks": len(state["native_assessment_pending"]), "native_scientific_completion": False}


def queue_native_after_reader(c, paper_id):
    if c.plan.get("mode") != "discovery":
        return
    state = c.store.get_state(STATE)
    if not state:
        return
    paper = c.store.paper(paper_id)
    existing = state["nodes"].get(paper_id, {})
    if not paper or paper["status"] not in {"assessed", "reading-incomplete"} or paper_id in state["native_assessment_pending"]:
        return
    if existing and existing["status"] not in {"provisional-core", "not-assessable-missing-fulltext"}:
        saved = c.store.get_state("native-assessment:" + paper_id)
        if saved and paper.get("packet_path") and digest(json.loads((c.run_dir / paper["packet_path"]).read_text())) == saved["packet_sha256"]:
            return
    ids = [a["asset_id"] for a in paper.get("retrieval", {}).get("assets", [])]
    _change(c, lambda s: frontiers.require_native_assessment(s, paper_id,
            "Full text is available; native discovery eligibility remains independently unassessed", source_asset_ids=ids), "Native discovery audit queued")


def queue_native_after_missing_source(c, paper_id):
    if c.plan.get("mode") != "discovery":
        return
    state = c.store.get_state(STATE)
    if state and paper_id not in state["nodes"] and paper_id not in state["native_assessment_pending"]:
        _change(c, lambda s: frontiers.require_native_assessment(s, paper_id,
            "Full text remains unavailable; assess explicit abstract-based provisional CORE and record missing-text priority. Missing text cannot establish BRIDGE."), "Missing-source/provisional-node audit queued")


def execute_search(c, job, client=None):
    client = client or sources.SourceClient()
    payload = job["payload"]
    path = c.run_dir / "searches" / (job["id"] + ".json")
    if path.exists():
        snapshot = sources.load_snapshot(path)
    else:
        snapshot = client.search(payload["source"], payload.get("query") or "", payload.get("limit") or 100,
                                 payload.get("cursor"), kind=payload["kind"], parent=payload.get("parent"))
        if snapshot["status"] == "complete":
            # The complete ordered retrieval is frozen before any paper row or
            # source encounter can be published by the coordinator.
            sources.save_snapshot(path, snapshot)
        else:
            directory = c.run_dir / "searches" / (job["id"] + ".attempts")
            save_json(directory / (str(time.time_ns()) + ".json"), snapshot)
            c.store.event("source_retrieval_failure", {"job_id": job["id"], "receipt": snapshot})
            if snapshot["status"] == "deferred":
                c.store.defer(job["id"], job["owner"], job["token"], snapshot["reason"],
                              delay_seconds=max(30, snapshot.get("retry_after") or 60))
                return snapshot
    result = {"snapshot_path": str(path.relative_to(c.run_dir)) if snapshot["status"] == "complete" else None,
              "snapshot_sha256": file_hash(path) if snapshot["status"] == "complete" else None,
              "retrieval_status": snapshot["status"], "failure": snapshot if snapshot["status"] != "complete" else None}
    c.store.complete(job["id"], job["owner"], job["token"], result)
    return result


def _schedule_new(c, rows, prefix):
    ids = [pid for pid, _ in rows if c.store.paper(pid)["status"] == "discovered"]
    if ids:
        c._enqueue_batch("title", list(dict.fromkeys(ids)), key_prefix=prefix)
        for pid in set(ids):
            c.store.update_paper(pid, {"status": "title-pending"}, "New logical work requires its own semantic screening decision")


def project_discovery(c, job):
    payload, result = job["payload"], job["result"]
    marker = "search-projection:" + job["id"]
    if c.store.get_state(marker):
        c.store.mark_projected(job["id"])
        return
    if result["retrieval_status"] != "complete":
        if payload.get("obligation_id"):
            _change(c, lambda s: frontiers.citation_failure(s, payload["obligation_id"], result["failure"],
                    reason="Source failure retained; fallback only for established unavailable coverage"), "Citation coverage failure recorded")
        else:
            c.store.set_state("source-resolution:" + job["id"], {"task": "resolve-required-source-window", "task_id": "source:" + job["id"], "job_id": job["id"],
                "request": payload, "failure": result["failure"], "reason": "Required window remains incomplete; resolve interface/access before resubmission"}, "Required query window could not complete")
    else:
        path = inside(c.run_dir / result["snapshot_path"], c.run_dir)
        if file_hash(path) != result["snapshot_sha256"]:
            raise ValueError("Saved source snapshot changed after publication")
        snapshot = sources.load_snapshot(path)
        ingested = []
        for index, record in enumerate(snapshot["results"]):
            key = job["id"] + ":" + str(index)
            provenance = {"route": payload["phase"], "search_job_id": job["id"], "snapshot_sha256": result["snapshot_sha256"],
                          "result_rank": index + 1, "source": payload["source"], "bridge_depth": payload.get("child_bridge_depth") or 0}
            if not record.get("title", "").strip():
                c.store.set_state("identity-resolution:" + key, {"task": "bibliographic-identity-resolution", "task_id": "identity:" + key,
                    "record": record, "provenance": provenance, "reason": "Source encountered this result, but identity lacks a title; do not drop it or invent one"}, "Encounter awaits bibliographic identity resolution")
                continue
            pid, new = _ingest_once(c, key, record, provenance)
            ingested.append((pid, new))
            # A known bridge can gain a new eligible depth-zero lineage even
            # when semantic screening is properly reused for the same work.
            saved = c.store.get_state("native-assessment:" + pid)
            if saved:
                retained = c.store.paper(pid)
                if not retained.get("packet_path") or digest(json.loads((c.run_dir / retained["packet_path"]).read_text())) != saved["packet_sha256"]:
                    raise ValueError("Native node reuse requires unchanged decision-relevant source evidence")
                _change(c, lambda s, p=retained, v=saved, d=provenance["bridge_depth"]: frontiers.record_node(s,
                    dict(p, **v["paper_state"]), v["groups"], encounter_depth=d,
                    reason="Rediscovery reuses unchanged source-bound native eligibility with new lineage"), "Native node lineage reconciled")
        _schedule_new(c, ingested, "search:" + job["id"] + ":")
        # A crash after ingestion is harmless: ordinal publication above is
        # idempotent, and each frontier completion is checked before replay.
        state = c.store.get_state(STATE)
        if payload.get("obligation_id"):
            obligation = state["citation_obligations"][payload["obligation_id"]]
            already = any(p["request_sha256"] == snapshot["request_sha256"] for p in obligation["pages"])
            if not already:
                _change(c, lambda s: frontiers.citation_page(s, payload["obligation_id"], snapshot,
                         snapshot_path=result["snapshot_path"], reason="Frozen citation page ingested with complete encounter provenance"), "Citation page advanced")
        else:
            _change(c, lambda s: frontiers.complete_window(s, payload["window_key"], snapshot,
                     snapshot_path=result["snapshot_path"], reason="Frozen query window ingested; no second page or reranking"), "Bounded window completed")
    c.store.set_state(marker, True, "Search result fully projected into durable encounter and frontier state")
    c.store.mark_projected(job["id"])


def _replay_lineage(c, task):
    """CORE revisions add new lineage encounters from existing source snapshots."""
    for page_index, page in enumerate(task["pages"]):
        snapshot = sources.load_snapshot(inside(c.run_dir / page["path"], c.run_dir))
        for index, record in enumerate(snapshot["results"]):
            key = "lineage:" + task["obligation_id"] + ":" + str(page_index) + ":" + str(index)
            provenance = {"route": "core-lineage-replay", "parent_obligation": task["obligation_id"],
                          "snapshot_path": page["path"], "result_rank": index + 1, "bridge_depth": 0,
                          "reason": task["reason"]}
            if not record.get("title"):
                c.store.set_state("identity-resolution:" + key, {"task": "bibliographic-identity-resolution", "task_id": "identity:" + key,
                    "record": record, "provenance": provenance, "reason": "Replayed source identity remains unresolved"}, "CORE lineage replay retained unresolved encountered identity")
                continue
            pid, _ = _ingest_once(c, key, record, provenance)
            saved = c.store.get_state("native-assessment:" + pid)
            paper = c.store.paper(pid)
            if saved and paper.get("packet_path") and digest(json.loads((c.run_dir / paper["packet_path"]).read_text())) == saved["packet_sha256"]:
                _change(c, lambda s, p=paper, v=saved: frontiers.record_node(s, dict(p, **v["paper_state"]),
                    v["groups"], encounter_depth=0, reason="CORE parent revision supplies a new depth-zero encounter from an unchanged snapshot"), "Replayed eligible lineage reconciled")
    _change(c, lambda s: frontiers.complete_lineage_replay(s, task["obligation_id"], reason="Every retained snapshot result replayed with depth-zero provenance"), "CORE lineage replay complete")


def _resolution_tasks(c):
    with c.store._connection() as conn:
        rows = conn.execute("SELECT key,value FROM meta WHERE key LIKE 'state:identity-resolution:%' OR key LIKE 'state:source-resolution:%' ORDER BY key").fetchall()
    return [json.loads(row["value"]) for row in rows if not json.loads(row["value"]).get("resolved")]


def next_native_task(c):
    state = c.store.get_state(STATE)
    if not state:
        return None
    resolutions = _resolution_tasks(c)
    if resolutions:
        return resolutions[0]
    for task in frontiers.due_obligations(state):
        if task.get("task"):
            task = dict(task)
            if task.get("obligation_id"):
                task["task_id"] = "citation-source:" + task["obligation_id"]
                task["submission_contract"] = {"action": "retry-same-request | extracted-reference-list",
                    "reason": "What resolved access/coverage, or why the reference list is complete",
                    "records": "For extracted-reference-list only: every reference identity in source order",
                    "source_locations": "For extracted-reference-list: source-bound asset/unit observations",
                    "exhaustion_evidence": "For extracted-reference-list: location of complete reference-list boundaries"}
            if task.get("paper_id"):
                paper = c.store.paper(task["paper_id"])
                task["paper"] = paper
                task["packet_path"] = paper.get("packet_path")
                task["schema_paths"] = {name: str(science_root() / "schemas" / (name + ".schema.json"))
                                        for name in ("experiment_groups", "experiments")}
                task["submission_contract"] = {"paper_state": "native fulltext_status/current_status/bridge_empirical_status",
                    "groups": "complete typed physical experiment-group records", "source_locations": "[{asset_id, unit_id, observation}]",
                    "process_audit": "{status: no-eligible-comparison | eligible-comparisons-recorded | unresolved, reason}",
                    "process_activations": "[{comparison: complete typed native row, variants: provenance-bearing lexical variants, normalization_reason}]",
                    "reason": "source-grounded eligibility reasoning; no prospect-label substitution"}
                if not paper.get("packet_path"):
                    task["task"] = "missing-source-provisional-node-audit"
                    task["submission_contract"] = {"missing_source_audit": {
                        "decision": "provisional-core | not-established | unresolved", "priority": "high | medium | low",
                        "reason": "Abstract-source reasoning and missing-text request priority",
                        "ingredients": "For provisional-core: specific_x, awareness_attempt, functional_y; each {status:'present',source_observation:'exact located abstract evidence'}"},
                        "reason": "Why provisional expansion is or is not established; missing text never establishes a strict bridge"}
            return task
    if not _pending_semantic(c) and not any(o["status"] != "complete" for o in state["citation_obligations"].values()) and not any(w["status"] != "complete" for w in state["process_windows"].values()):
        return {"task": "citation-wave-and-frontier-audit", "task_id": "wave-audit", "state": state,
                "instructions": "Reconcile the complete backward/forward wave, deduplication, all title/abstract/rescue/audit decisions and missing text requests. Submit wave_id, obligation_ids, new_potentially_relevant, screening_complete, reason. A zero yield is a factual post-screening count, not an assumption from an empty queue. After a current zero-yield wave, enter the mandatory blind lane; do not claim native certification."}
    return None


def _source_proof(c, paper, payload):
    if not paper.get("packet_path"):
        raise ValueError("Native full-text decisions need a verified source packet")
    packet = json.loads(inside(c.run_dir / paper["packet_path"], c.run_dir).read_text())
    units = {s["asset_id"]: {u["unit_id"] for u in s["units"]} for s in packet["sources"]}
    locations = payload.get("source_locations") or []
    if not locations:
        raise ValueError("Native route decisions require source-located observations")
    for item in locations:
        if item.get("asset_id") not in units or item.get("unit_id") not in units[item["asset_id"]] or not str(item.get("observation", "")).strip():
            raise ValueError("Native route decision cites an unavailable source unit or lacks an observation")
    return digest(packet)


def submit_native(c, paper_id, payload, actor):
    if not str(actor).strip() or not str(payload.get("reason", "")).strip():
        raise ValueError("Native submission requires actor and reason")
    if paper_id.startswith("source:") or paper_id.startswith("citation-source:"):
        return _submit_source_resolution(c, paper_id, payload, actor)
    if paper_id == "wave-audit":
        if _pending_semantic(c) or _resolution_tasks(c):
            raise ValueError("Pending semantic/source-identity work prevents a completed wave audit")
        fields = {k: payload[k] for k in ("wave_id", "obligation_ids", "new_potentially_relevant", "screening_complete", "reason")}
        state = _change(c, lambda s: frontiers.audit_wave(s, **fields), "Source-grounded complete-wave audit submitted by " + actor)
        if not state["principal_provisionally_satisfied"] and not frontiers.principal_errors(state):
            _change(c, lambda s: frontiers.enter_blind_lane(s, reason="Principal obligations and explicit zero-yield wave audit satisfied"), "Mandatory blind lane opened")
    elif paper_id.startswith("identity:"):
        key = paper_id[len("identity:"):]
        task = c.store.get_state("identity-resolution:" + key)
        if not task:
            raise ValueError("Unknown bibliographic identity task")
        record = payload["record"]
        if not record.get("title") or not payload.get("source_location"):
            raise ValueError("Identity resolution needs actual title and source pointer")
        value = _ingest_once(c, key, record, dict(task["provenance"], identity_resolution_reason=payload["reason"], identity_source=payload["source_location"]))
        _schedule_new(c, [value], "resolved:" + key + ":")
        c.store.set_state("identity-resolution:" + key, dict(task, resolved=True), "Bibliographic identity resolved by " + actor)
    else:
        paper = c.store.paper(paper_id)
        if not paper:
            raise ValueError("Unknown paper")
        if "missing_source_audit" in payload:
            if paper.get("packet_path"):
                raise ValueError("Available full text requires the ordinary source-based native audit")
            _change(c, lambda s: frontiers.record_missing_source(s, paper, payload["missing_source_audit"], reason=payload["reason"]),
                    "Abstract-source provisional node audit submitted by " + actor)
            c.store.set_state("missing-source-audit:" + paper_id, dict(payload, actor=actor, abstract_sha256=digest(paper.get("abstract"))),
                              "Missing-text priority and source-bound provisional expansion reason retained")
            return discovery_tick(c)
        packet_hash = _source_proof(c, paper, payload)
        process = payload.get("process_audit", {})
        if process.get("status") not in {"no-eligible-comparison", "eligible-comparisons-recorded", "unresolved"} or not str(process.get("reason", "")).strip():
            raise ValueError("Native audit must separately resolve independently earned process searches")
        if process["status"] == "unresolved":
            c.store.event("native_route_unresolved", {"paper_id": paper_id, "actor": actor, "payload": payload, "packet_sha256": packet_hash})
            return {"status": "unresolved", "reason": process["reason"], "native_scientific_completion": False}
        native_paper = dict(paper, **payload["paper_state"])
        if native_paper["paper_id"] != paper_id:
            raise ValueError("Cannot replace native focal paper identity")
        activations = payload.get("process_activations", [])
        if (process["status"] == "eligible-comparisons-recorded") != bool(activations):
            raise ValueError("Process audit and activation records disagree")
        def apply(state):
            result = frontiers.record_node(state, native_paper, payload["groups"],
                                           encounter_depth=min(paper.get("discovery_bridge_depths") or [0]), reason=payload["reason"])
            for activation in activations:
                if activation["comparison"]["paper_id"] != paper_id:
                    raise ValueError("Process trigger belongs to another paper")
                result = frontiers.activate_process(result, activation["comparison"], activation["variants"], normalization_reason=activation["normalization_reason"])
            return result
        _change(c, apply, "Source-bound native discovery assessment submitted by " + actor)
        c.store.set_state("native-assessment:" + paper_id, dict(payload, packet_sha256=packet_hash, actor=actor), "Native route judgment and source identity retained for lineage reuse")
    c.store.event("native_discovery_submission", {"paper_id": paper_id, "actor": actor, "payload_sha256": digest(payload), "reason": payload["reason"]})
    return discovery_tick(c)


def _submit_source_resolution(c, task_id, payload, actor):
    if task_id.startswith("source:"):
        job_id = task_id[len("source:"):]
        task = c.store.get_state("source-resolution:" + job_id)
        if not task:
            raise ValueError("Unknown required-source resolution task")
        request = task["request"]
        obligation_id = None
    else:
        obligation_id = task_id[len("citation-source:"):]
        state = c.store.get_state(STATE)
        obligation = state["citation_obligations"].get(obligation_id)
        if not obligation:
            raise ValueError("Unknown citation-source obligation")
        request = {"source": obligation["source"], "query": "", "limit": 100, "cursor": obligation["cursor"],
                   "kind": obligation["direction"], "parent": obligation["parent"], "phase": "citation",
                   "obligation_id": obligation_id, "child_bridge_depth": obligation["child_bridge_depth"], "window_key": None}
    generation_key = "source-resolution-generation:" + task_id
    generation = c.store.get_state(generation_key, 0) + 1
    action = payload.get("action")
    if action not in {"retry-same-request", "extracted-reference-list"}:
        raise ValueError("Source resolution requires retry-same-request or extracted-reference-list")
    if action == "extracted-reference-list":
        if not obligation_id or request["source"] != "publisher-or-repository-reference-list" or request["kind"] != "backward":
            raise ValueError("Extracted reference list is the last backward fallback, never a forward substitute")
        if not str(payload.get("exhaustion_evidence", "")).strip():
            raise ValueError("Reference-list exhaustion needs explicit source-located evidence")
        paper = c.store.paper(request["parent"]["paper_id"])
        packet_sha = _source_proof(c, paper, payload)
        records = payload.get("records")
        if not isinstance(records, list) or any(not isinstance(record, dict) for record in records):
            raise ValueError("Reference list needs every encountered identity in order")
        snapshot_request = {k: request.get(k) for k in ("source", "query", "limit", "cursor", "kind", "parent")}
        snapshot_request["publication_cutoff"] = None
        snapshot = {"status": "complete", "request": snapshot_request, "retrieved_at": sources.now(),
                    "results": records, "next_cursor": None, "exhausted": True, "reported_total": len(records),
                    "raw_responses": [], "request_sha256": sources.digest(snapshot_request), "result_set_sha256": sources.digest(records),
                    "reason": payload["reason"], "source_proof": {"packet_sha256": packet_sha, "locations": payload["source_locations"],
                    "exhaustion_evidence": payload["exhaustion_evidence"], "actor": actor}}
        # The ordinary worker sees the saved immutable snapshot and publishes
        # it without another network call or separate scientific interpretation.
        job_id = c.store.enqueue("search", digest({"request": request, "resolution": generation}), request, priority=10)
        sources.save_snapshot(c.run_dir / "searches" / (job_id + ".json"), snapshot)
    else:
        if request["source"] == "publisher-or-repository-reference-list":
            raise ValueError("Publisher reference-list fallback requires extracted-reference-list work, not a network adapter retry")
        job_id = c.store.enqueue("search", digest({"request": request, "resolution": generation}), request, priority=10)
    c.store.set_state(generation_key, generation, "Explicit source resolution permits an auditable continuation with unchanged request")
    if task_id.startswith("source:"):
        c.store.set_state("source-resolution:" + task_id[len("source:"):], dict(task, resolved=True), "Agent resolved source access/interface without changing frozen query")
    c.store.event("source_resolution_submitted", {"task_id": task_id, "job_id": job_id, "actor": actor, "action": action, "reason": payload["reason"]})
    return {"job_id": job_id, "status": "continuation-queued", "native_scientific_completion": False}


def discovery_status(c):
    state = c.store.get_state(STATE)
    if not state:
        return {"initialized": False, "native_scientific_completion": False}
    checked = frontiers.readiness(state, pending_semantic_jobs=_pending_semantic(c), missing_texts_current=False, durable_validation_passed=False)
    task = next_native_task(c)
    task_summary = {key: task.get(key) for key in ("task", "task_id", "paper_id", "reason") if task.get(key) is not None} if task else None
    return {"initialized": True, "phase": state["phase"], "pending_agent_task": task_summary,
            "frontier_checks": checked, "native_scientific_completion": False,
            "reason": "Portable discovery orchestrates prospects; certification still requires the frozen native ledger and validator"}
