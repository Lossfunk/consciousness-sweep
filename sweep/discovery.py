"""Connect public discovery to the durable prospect coordinator.

The network adapters perform retrieval, not native scientific certification.
Agent work exchange handles native route decisions and citation-wave audits.
The frozen native ledger/validator remains the authority for certification.
"""
from __future__ import annotations

from collections import deque
import csv
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import time

from . import citation_depth, frontiers, sources
from .common import canonical, digest, file_hash, inside, save_json, science_root
from .transactions import atomic_operation

STATE = "discovery_frontiers"


def _deadline_expired(c):
    deadline = getattr(c, "session_deadline", None)
    return deadline is not None and time.monotonic() >= deadline


def _packet_is_current(paper):
    generation = paper.get("source_generation", 1)
    return (type(generation) is int and generation >= 1 and bool(paper.get("packet_path"))
            and type(paper.get("packet_source_generation")) is int
            and paper["packet_source_generation"] == generation)


def _native_source_wait(paper):
    if _packet_is_current(paper):
        return None
    if (paper.get("source_generation", 1) > 1 or paper.get("packet_path")
            or paper.get("status") == "retrieval-pending"):
        return "The latest source generation has no verified packet; historical native evidence remains historical"
    return None


def _saved_native_is_current(c, paper, saved):
    return (_packet_is_current(paper) and saved.get("source_generation") == paper.get("source_generation", 1)
            and digest(json.loads(inside(c.run_dir / paper["packet_path"], c.run_dir).read_text())) == saved["packet_sha256"])


def source_job_key(payload):
    """Bridge provenance is not part of the source retrieval identity."""
    return digest({key: value for key, value in payload.items() if key != "child_bridge_depth"})


def _change(c, function, reason):
    return c.store.mutate_state_compact(STATE, function, reason, history_field="history")


def _sync_citation_depths(c):
    """Refresh affected eligible parents in bounded batches; resume is idempotent."""
    while True:
        with c.store._transaction() as conn:
            citation_depth.ensure_tables(conn)
            rows = conn.execute("SELECT p.paper_id,p.depth,p.origin FROM citation_depth_sync s JOIN citation_paths p ON p.paper_id=s.paper_id LIMIT 1000").fetchall()
        if not rows:
            return
        paths = {row[0]: {"depth": row[1], "origin": json.loads(row[2])} for row in rows}
        state = c.store.get_state(STATE)
        eligible = {pid: path for pid, path in paths.items() if state and any(pid + ":" + d in state["citation_obligations"] for d in ("backward", "forward"))}
        if eligible:
            _change(c, lambda s: frontiers.refresh_citation_depths(s, eligible,
                    reason="Indexed encounter paths lowered these eligible parents' ordinary citation distance"), "Eligible parent citation distances reconciled")
        with c.store._transaction() as conn:
            # A concurrent further improvement must remain pending for replay.
            conn.executemany("DELETE FROM citation_depth_sync WHERE paper_id=? AND EXISTS(SELECT 1 FROM citation_paths p WHERE p.paper_id=? AND p.depth=?)",
                             [(pid, pid, path["depth"]) for pid, path in paths.items()])


def _ingest_once(c, key, record, provenance, *, defer_depth_sync=False):
    """One atomic source encounter per saved snapshot ordinal, including restart."""
    marker = "state:encounter:" + key
    with c.store._transaction() as conn:
        old = conn.execute("SELECT value FROM meta WHERE key=?", (marker,)).fetchone()
        if old:
            result = tuple(json.loads(old[0]))
        else:
            record = {name: value for name, value in record.items() if name not in {"citation_depth", "citation_origin"}}
            record = dict(record, discovery_bridge_depths=[provenance.get("bridge_depth", 0)])
            result = c.store._add_paper(conn, record, provenance)
            retained = json.loads(conn.execute("SELECT record FROM papers WHERE id=?", (result[0],)).fetchone()[0])
            depths = sorted(set(retained.get("discovery_bridge_depths", []) + [provenance.get("bridge_depth", 0)]))
            if retained.get("discovery_bridge_depths") != depths:
                retained["discovery_bridge_depths"] = depths
                c.store._event(conn, "bridge_lineage_encounter", {"paper_id": result[0], "depths": depths, "provenance": provenance})
                conn.execute("UPDATE papers SET record=?,updated_at=? WHERE id=?", (canonical(retained), time.time(), result[0]))
            conn.execute("INSERT INTO meta VALUES(?,?)", (marker, canonical(result)))
        citation_depth.record(conn, c.store, result[0], provenance)
    if not defer_depth_sync:
        _sync_citation_depths(c)
    return result


def initialize_discovery(c):
    if c.plan.get("mode") != "discovery":
        raise ValueError("Discovery initialization requires an explicitly selected discovery run")
    if c.store.get_state(STATE) is None:
        c.store.set_state(STATE, frontiers.initial_state(max_citation_depth=c.plan.get("resources", {}).get("max_citation_depth")),
                          "Frozen principal-first discovery obligations initialized with the selected execution depth boundary")
    for filename, role in (("seeds_empirical.csv", "empirical-seed"), ("seeds_reviews.csv", "review-anchor")):
        path = science_root() / filename
        source_hash = file_hash(path)
        with path.open(newline="", encoding="utf-8-sig") as handle:
            rows = list(csv.DictReader(handle))
        # Validate every identity before allocating an ID from this input.
        if any(not row.get("title", "").strip() for row in rows):
            raise ValueError("Frozen seed identity lacks title")
        seed_screen_ids = []
        for ordinal, record in enumerate(rows):
            record = {k: record.get(k) for k in ("title", "authors", "year", "doi", "url")}
            record["status"] = "discovery-anchor" if role == "review-anchor" else "discovered"
            record["seed_role"] = role
            key = "seed:" + source_hash + ":" + str(ordinal)
            pid, _ = _ingest_once(c, key, record, {"route": role, "source_sha256": source_hash, "ordinal": ordinal, "bridge_depth": 0})
            paper = c.store.paper(pid)
            _change(c, lambda s, p=paper: frontiers.add_anchor(s, p, role=role, reason="Frozen seed/anchor identity initializes the principal route"), "Principal seed obligation recorded")
            if role == "empirical-seed" and paper["status"] == "discovered":
                seed_screen_ids.append(pid)
        c._enqueue_batch("title", seed_screen_ids, key_prefix="seed:" + source_hash + ":")
        for pid in seed_screen_ids:
            c.store.update_paper(pid, {"status": "title-pending"}, "Frozen empirical seed enters bounded paper-specific semantic screening")
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
    from .workflow import enabled, job_hold_sql
    if enabled(c):
        with c.store._connection() as conn:
            return conn.execute("SELECT count(*) FROM jobs j WHERE stage!='search' AND state NOT IN ('complete','parked') AND NOT EXISTS(SELECT 1 FROM job_supersessions s WHERE s.job_id=j.id) AND NOT EXISTS(SELECT 1 FROM retry_links r WHERE r.parent_id=j.id)" + job_hold_sql()).fetchone()[0]
    status = c.store.status()
    return sum(n for stage, counts in status["jobs"].items() if stage != "search"
               for state, n in counts.items() if state != "complete")


def _search_candidate(c, obligation):
    """Exact request identity shared by admission and read-only supervision."""
    payload = {k: obligation.get(k) for k in ("source", "query", "limit", "cursor", "kind", "parent", "phase", "window_key", "obligation_id", "child_bridge_depth")}
    if obligation.get("coverage_generation"):
        payload["coverage_generation"] = obligation["coverage_generation"]
    key = source_job_key(payload)
    old = c.store.job_by_key("search", key)
    while old and c.store.get_state("depth-deferred-search:" + old["id"]):
        payload = dict(payload, depth_resume_from=old["id"])
        key = source_job_key(payload)
        old = c.store.job_by_key("search", key)
    return payload, key, old


def _search_admissions(c, obligations):
    """Rotate only already eligible source windows; never alter their contents."""
    from .execution_policy import for_coordinator
    policy = for_coordinator(c)
    from .search_holds import active_keys
    held = active_keys(c)
    sources = [o for o in obligations if not o.get('task') and o.get('window_key') not in held]
    if policy.get('workflow') != 'focused-v1' or not policy['retained_first']:
        for obligation in sources:
            payload, key, old = _search_candidate(c, obligation)
            if old is None:
                yield payload, key, None
        return
    names = ('principal-citation', 'deeper-citation', 'earned-query')
    buckets = {name: [] for name in names}
    for obligation in sources:
        lane = ('earned-query' if obligation.get('phase') != 'citation' else
                'deeper-citation' if (obligation.get('parent_citation_depth') or 0) > 0 else 'principal-citation')
        buckets[lane].append(obligation)
    previous = c.store.get_state('search-admission-last-lane', names[0])
    start = (names.index(previous) + 1) % len(names) if previous in names else 0
    lanes = deque(names[start:] + names[:start])
    buckets = {name: iter(values) for name, values in buckets.items()}
    while lanes:
        lane = lanes.popleft()
        for obligation in buckets[lane]:
            payload, key, old = _search_candidate(c, obligation)
            if old is None:
                lanes.append(lane)
                yield payload, key, lane
                break


def discovery_tick(c):
    if c.plan.get("mode") != "discovery":
        return None
    if _deadline_expired(c):
        return {"status": "session-checkpoint", "scheduled_source_jobs": 0,
                "native_scientific_completion": False}
    state = c.store.get_state(STATE)
    if state is None:
        return initialize_discovery(c)
    if state.get("max_citation_depth") != c.plan.get("resources", {}).get("max_citation_depth"):
        raise ValueError("Discovery state and immutable execution plan have different citation depth limits")
    _sync_citation_depths(c)
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
    from .scheduling import pressure
    backlog = pressure(c)
    slots = max(0, backlog["search_queue_target"] - backlog["queued_search_jobs"])
    if backlog["search_admission_paused"]:
        slots = 0
    obligations = frontiers.due_obligations(state)
    for obligation in obligations:
        if _deadline_expired(c):
            break
        if obligation.get("task") == "replay-citation-provenance":
            _replay_lineage(c, obligation)
            continue
    admissions = _search_admissions(c, obligations)
    while scheduled < slots and not _deadline_expired(c):
        candidate = next(admissions, None)
        if candidate is None:
            break
        payload, key, lane = candidate
        c.store.enqueue("search", key, payload, priority=10)
        if lane is not None:
            c.store.set_state('search-admission-last-lane', lane,
                'Rotate bounded source admission among principal, deeper citation and earned query windows')
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
    from .workflow import enabled, deferred
    if enabled(c) and deferred(paper):
        return
    if enabled(c) and paper:
        saved = c.store.get_state("native-assessment:" + paper_id)
        if saved and _saved_native_is_current(c, paper, saved):
            return  # A current source reading may honestly remain insufficient.
    existing = state["nodes"].get(paper_id, {})
    if not paper or paper["status"] not in {"assessed", "reading-incomplete"} or paper_id in state["native_assessment_pending"]:
        return
    if existing and existing["status"] not in {"provisional-core", "not-assessable-missing-fulltext"}:
        saved = c.store.get_state("native-assessment:" + paper_id)
        if saved and _saved_native_is_current(c, paper, saved):
            return
    ids = [a["asset_id"] for a in paper.get("retrieval", {}).get("assets", [])]
    _change(c, lambda s: frontiers.require_native_assessment(s, paper_id,
            "Full text is available; native discovery eligibility remains independently unassessed", source_asset_ids=ids), "Native discovery audit queued")


def queue_native_after_missing_source(c, paper_id):
    if c.plan.get("mode") != "discovery":
        return
    state = c.store.get_state(STATE)
    paper = c.store.paper(paper_id)
    from .workflow import enabled, on_source_missing
    if enabled(c):
        on_source_missing(c, paper_id)
        return
    saved = c.store.get_state("native-assessment:" + paper_id)
    replacement_unresolved = bool(saved and not _saved_native_is_current(c, paper, saved))
    if state and (paper_id not in state["nodes"] or replacement_unresolved) and paper_id not in state["native_assessment_pending"]:
        _change(c, lambda s: frontiers.require_native_assessment(s, paper_id,
            "Replacement source generation remains unavailable; retain historical judgments and defer its current native audit." if replacement_unresolved else
            "Full text remains unavailable; assess explicit abstract-based provisional CORE and record missing-text priority. Missing text cannot establish BRIDGE."), "Missing-source/provisional-node audit queued")


def _citation_block(c, payload):
    if payload.get("kind") not in {"backward", "forward"}:
        return None
    state = c.store.get_state(STATE) or {}
    if state.get("max_citation_depth") != c.plan.get("resources", {}).get("max_citation_depth"):
        raise ValueError("Discovery state and immutable execution plan have different citation depth limits")
    obligation = state.get("citation_obligations", {}).get(payload.get("obligation_id"))
    if obligation is None:
        return "depth-unresolved" if c.plan.get("resources", {}).get("max_citation_depth") is not None else None
    return frontiers.citation_fetch_block(state, obligation)


def _native_paper(paper, scientific_state):
    """Scientific submissions cannot replace execution-derived path metadata."""
    result = dict(paper, **scientific_state)
    for key in ("citation_depth", "citation_origin"):
        if key in paper:
            result[key] = paper[key]
        else:
            result.pop(key, None)
    return result


def execute_search(c, job, client=None):
    # Recheck the durable lease before any source I/O. Hold publication refuses
    # running jobs, so a claim/hold race has exactly one winner.
    from .search_holds import require_unheld
    with c.store._connection() as conn:
        owned = c.store._owned(conn, job["id"], job["owner"], job["token"])
        payload = json.loads(owned["payload"])
        require_unheld(c, payload)
    state = c.store.get_state(STATE) or {}
    obligation = state.get("citation_obligations", {}).get(payload.get("obligation_id"))
    if obligation and payload.get("coverage_generation", 0) != obligation.get("coverage_generation", 0):
        result = {"retrieval_status": "superseded", "reason": "An explicit coverage generation replaced this queued request",
                  "snapshot_path": None, "snapshot_sha256": None}
        c.store.complete(job["id"], job["owner"], job["token"], result)
        return result
    block = _citation_block(c, payload)
    if block:
        result = {"retrieval_status": block, "snapshot_path": None, "snapshot_sha256": None,
                  "reason": "The current ordinary citation distance blocks this queued retrieval; the scientific frontier remains pending"}
        c.store.complete(job["id"], job["owner"], job["token"], result)
        return result
    deadline = getattr(c, "session_deadline", None)
    client = client or sources.SourceClient(**({"deadline": deadline} if deadline is not None else {}))
    path = c.run_dir / "searches" / (job["id"] + ".json")
    if not path.exists() and payload.get("depth_resume_from"):
        previous = c.store.job(payload["depth_resume_from"])
        result = previous.get("result") or {}
        if result.get("snapshot_path"):
            if any(previous["payload"].get(k) != payload.get(k) for k in ("source", "query", "limit", "cursor", "kind", "parent")):
                raise ValueError("Depth continuation cannot change an existing citation request")
            saved = inside(c.run_dir / result["snapshot_path"], c.run_dir)
            if file_hash(saved) != result["snapshot_sha256"]:
                raise ValueError("Depth continuation snapshot changed")
            sources.save_snapshot(path, sources.load_snapshot(saved))
    if path.exists():
        try:
            snapshot = sources.load_snapshot(path)
        except (ValueError, OSError) as exc:
            result = {"retrieval_status": "incomplete", "snapshot_path": None, "snapshot_sha256": None,
                      "failure": {"status": "incomplete", "reason": "Stored response requires quarantine: " + str(exc),
                                  "quarantined_path": str(path.relative_to(c.run_dir))}}
            c.store.complete(job["id"], job["owner"], job["token"], result)
            return result
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


@atomic_operation
def project_discovery(c, job):
    # Only local, bounded snapshot projection belongs here. Keep the replay
    # check, encounter publication, frontier transition and acknowledgement on
    # one write snapshot; retrieval and inference have already finished.
    payload, result = job["payload"], job["result"]
    marker = "search-projection:" + job["id"]
    if c.store.get_state(marker):
        c.store.mark_projected(job["id"])
        return
    state = c.store.get_state(STATE) or {}
    obligation = state.get("citation_obligations", {}).get(payload.get("obligation_id"))
    if result["retrieval_status"] == "superseded" or obligation and payload.get("coverage_generation", 0) != obligation.get("coverage_generation", 0):
        c.store.set_state("quarantined-search:" + job["id"], {"status": "superseded", "job_id": job["id"],
            "snapshot_path": result.get("snapshot_path"), "snapshot_sha256": result.get("snapshot_sha256"),
            "reason": "Earlier-generation response retained without changing the active citation coverage generation"}, "Obsolete citation response retained")
        c.store.set_state(marker, True, "Obsolete request disposed without source failure or coverage promotion")
        c.store.mark_projected(job["id"])
        return
    block = _citation_block(c, payload)
    if block or result["retrieval_status"] in {"depth-limited", "depth-unresolved"}:
        c.store.set_state("depth-deferred-search:" + job["id"], {"status": block or result["retrieval_status"],
                          "reason": "Operational depth prevents projection/expansion; saved snapshots remain available for an eligible shorter-path continuation"},
                          "Citation retrieval deferred without closing or failing its scientific obligation")
        c.store.set_state(marker, True, "Execution job deferred at citation depth boundary; scientific frontier remains pending")
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
        # Coverage must be checked before publishing any result into the candidate
        # pool. An immutable bad response is retained, not replayed forever.
        state = c.store.get_state(STATE)
        obligation = state["citation_obligations"].get(payload.get("obligation_id"))
        already = obligation and any(p["request_sha256"] == snapshot["request_sha256"] and
                    p.get("coverage_generation", 0) == obligation.get("coverage_generation", 0)
                    for p in obligation["pages"])
        try:
            if obligation and not already:
                if payload.get("coverage_generation", 0) != obligation.get("coverage_generation", 0):
                    raise ValueError("Response belongs to an obsolete citation coverage generation")
                frontiers.citation_page(state, payload["obligation_id"], snapshot,
                    snapshot_path=result["snapshot_path"], reason="Validate response before candidate publication")
            elif not obligation:
                frontiers.complete_window(state, payload["window_key"], snapshot,
                    snapshot_path=result["snapshot_path"], reason="Validate response before candidate publication")
        except ValueError as exc:
            failure = {"status": "incomplete", "reason": str(exc), "quarantined_job_id": job["id"],
                       "snapshot_path": result["snapshot_path"], "snapshot_sha256": result["snapshot_sha256"]}
            c.store.set_state("quarantined-search:" + job["id"], failure,
                              "Inconsistent response retained without publishing candidates or closing coverage")
            if obligation:
                _change(c, lambda s: frontiers.citation_failure(s, payload["obligation_id"], failure,
                    reason="Coverage inconsistency requires explicit same-request retry or new coverage generation"), "Citation response quarantined")
            else:
                c.store.set_state("source-resolution:" + job["id"], {"task": "resolve-required-source-window",
                    "task_id": "source:" + job["id"], "job_id": job["id"], "request": payload,
                    "failure": failure, "reason": str(exc)}, "Bounded window response quarantined")
            c.store.set_state(marker, True, "Quarantine disposition completes execution projection; scientific obligation remains unresolved")
            c.store.mark_projected(job["id"])
            return
        ingested = []
        depth_encounters = []
        state = c.store.get_state(STATE)
        obligation = state["citation_obligations"].get(payload.get("obligation_id"))
        for index, record in enumerate(snapshot["results"]):
            key = job["id"] + ":" + str(index)
            provenance = {"route": payload["phase"], "search_job_id": job["id"], "snapshot_sha256": result["snapshot_sha256"],
                          "result_rank": index + 1, "source": payload["source"],
                          "bridge_depth": obligation["child_bridge_depth"] if obligation else payload.get("child_bridge_depth") or 0,
                          "parent_paper_id": obligation["parent"]["paper_id"] if obligation else None,
                          "parent_obligation": payload.get("obligation_id"), "window_key": payload.get("window_key"),
                          "citation_depth": obligation.get("child_citation_depth") if obligation else 0,
                          "citation_origin": obligation.get("citation_origin") if obligation else {"route": payload["phase"]}}
            if not record.get("title", "").strip():
                c.store.set_state("identity-resolution:" + key, {"task": "bibliographic-identity-resolution", "task_id": "identity:" + key,
                    "record": record, "provenance": provenance, "reason": "Source encountered this result, but identity lacks a title; do not drop it or invent one"}, "Encounter awaits bibliographic identity resolution")
                continue
            pid, new = _ingest_once(c, key, record, provenance, defer_depth_sync=True)
            ingested.append((pid, new))
            depth_encounters.append((pid, provenance))
        if hasattr(c, "reconcile_metadata"):
            c.reconcile_metadata([pid for pid, _ in ingested])
        _sync_citation_depths(c)
        for pid, provenance in depth_encounters:
            # A known bridge can gain a new eligible depth-zero lineage even
            # when semantic screening is properly reused for the same work.
            saved = c.store.get_state("native-assessment:" + pid)
            if saved:
                retained = c.store.paper(pid)
                if not _saved_native_is_current(c, retained, saved):
                    queue_native_after_reader(c, pid)
                    continue
                _change(c, lambda s, p=retained, v=saved, d=provenance["bridge_depth"]: frontiers.record_node(s,
                    _native_paper(p, v["paper_state"]), v["groups"], encounter_depth=d,
                    reason="Rediscovery reuses unchanged source-bound native eligibility with new lineage"), "Native node lineage reconciled")
        _schedule_new(c, ingested, "search:" + job["id"] + ":")
        # A crash after ingestion is harmless: ordinal publication above is
        # idempotent, and each frontier completion is checked before replay.
        state = c.store.get_state(STATE)
        if payload.get("obligation_id"):
            obligation = state["citation_obligations"][payload["obligation_id"]]
            already = any(p["request_sha256"] == snapshot["request_sha256"] and
                          p.get("coverage_generation", 0) == obligation.get("coverage_generation", 0) for p in obligation["pages"])
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
        if _deadline_expired(c):
            return
        snapshot = sources.load_snapshot(inside(c.run_dir / page["path"], c.run_dir))
        for index, record in enumerate(snapshot["results"]):
            if _deadline_expired(c):
                return
            key = "lineage:" + task["obligation_id"] + ":" + str(page_index) + ":" + str(index)
            provenance = {"route": "core-lineage-replay", "parent_obligation": task["obligation_id"],
                          "snapshot_path": page["path"], "result_rank": index + 1, "bridge_depth": 0,
                          "reason": task["reason"]}
            if not record.get("title"):
                c.store.set_state("identity-resolution:" + key, {"task": "bibliographic-identity-resolution", "task_id": "identity:" + key,
                    "record": record, "provenance": provenance, "reason": "Replayed source identity remains unresolved"}, "CORE lineage replay retained unresolved encountered identity")
                continue
            pid, _ = _ingest_once(c, key, record, provenance, defer_depth_sync=True)
            saved = c.store.get_state("native-assessment:" + pid)
            paper = c.store.paper(pid)
            if saved and _saved_native_is_current(c, paper, saved):
                _change(c, lambda s, p=paper, v=saved: frontiers.record_node(s, _native_paper(p, v["paper_state"]),
                    v["groups"], encounter_depth=0, reason="CORE parent revision supplies a new depth-zero encounter from an unchanged snapshot"), "Replayed eligible lineage reconciled")
    _sync_citation_depths(c)
    _change(c, lambda s: frontiers.complete_lineage_replay(s, task["obligation_id"], reason="Every retained snapshot result replayed with bridge-depth-zero provenance; ordinary hop distance retained"), "CORE lineage replay complete")


def _resolution_tasks(c):
    with c.store._connection() as conn:
        rows = conn.execute("SELECT key,value FROM meta WHERE key LIKE 'state:identity-resolution:%' OR key LIKE 'state:source-resolution:%' ORDER BY key").fetchall()
    from .search_holds import active_keys
    held = active_keys(c)
    tasks = [json.loads(row["value"]) for row in rows]
    return [t for t in tasks if not t.get("resolved") and not t.get("workflow_parked")
            and (t.get("request") or {}).get("window_key") not in held]


def _hydrate_native_task(c, task):
    task = dict(task)
    from .workflow import hydrate_operational_task
    operational = hydrate_operational_task(c, task)
    if operational is not None:
        return operational
    if task.get("paper_id"):
        # Pending task explanations and deferral notes can contain earlier
        # scientific judgments. Keep them in durable history, not reader inputs.
        # Construct this boundary explicitly so new ledger fields cannot leak.
        original = task
        task = {key: original[key] for key in ("task", "task_id", "paper_id") if key in original}
        if "control" in original:
            task["control"] = {key: original["control"][key] for key in
                ("task_id", "owner", "token", "lease_until", "available_at", "last_served", "binding")
                if key in original["control"]}
        task["reason"] = "Assess the current supplied sources under the scientific protocol; record source-grounded findings and unresolved evidence."
        paper = c.store.paper(task["paper_id"])
        from .source_intake import source_manifest
        # A fresh native reader receives bibliography and source evidence only.
        # Prior screening, reader, human and calibration judgments stay in the ledger.
        task["paper"] = dict(source_manifest(paper), abstract=paper.get("abstract"))
        task["execution_role"] = "source-only-native-reader"
        task["packet_path"] = paper.get("packet_path") if _packet_is_current(paper) else None
        task["source_generation"] = paper.get("source_generation", 1)
        task["schema_paths"] = {name: str(science_root() / "schemas" / (name + ".schema.json"))
                                for name in ("experiment_groups", "experiments")}
        task["submission_contract"] = {"source_generation": "Echo the current task source_generation; older packet generations cannot be submitted",
            "identifier_allocation": "Before authoring groups, call native-allocate --paper-id ID --experiment-key STABLE_LABEL [--comparison-key STABLE_X_Y_KEY] --actor WORKER --reason REASON; reuse returned IDs. Reservation is not scientific certification.",
            "paper_state": "native fulltext_status/current_status/bridge_empirical_status",
            "groups": "complete typed physical experiment-group records", "source_locations": "[{asset_id, unit_id, observation}]",
            "process_audit": "{status: no-eligible-comparison | eligible-comparisons-recorded | unresolved, reason}",
            "process_activations": "[{comparison: complete typed native row, variants: provenance-bearing lexical variants, normalization_reason}]",
            "reason": "source-grounded eligibility reasoning; no prospect-label substitution"}
        waiting = _native_source_wait(paper)
        if waiting:
            task.update(task="native-source-generation-pending", deferred_for_source_generation=waiting)
            task["submission_contract"] = {"waiting": "Obtain/verify the latest source generation before a new native judgment; retain earlier activations as historical provenance"}
        elif not _packet_is_current(paper):
            task["task"] = "missing-source-provisional-node-audit"
            task["submission_contract"] = {"missing_source_audit": {
                "decision": "provisional-core | not-established | unresolved", "priority": "high | medium | low",
                "reason": "Abstract-source reasoning and missing-text request priority",
                "ingredients": "For provisional-core: specific_x, awareness_attempt, functional_y; each {status:'present',source_observation:'exact located abstract evidence'}"},
                "reason": "Why provisional expansion is or is not established; missing text never establishes a strict bridge"}
    elif task.get("obligation_id") and task.get("source") == "publisher-or-repository-reference-list":
        paper = c.store.paper(task["parent"]["paper_id"])
        task["packet_path"] = paper.get("packet_path") if _packet_is_current(paper) else None
        task["source_generation"] = paper.get("source_generation", 1)
        task["submission_contract"] = dict(task.get("submission_contract", {}),
            source_generation="Echo this source generation with extracted-reference-list proof from its current verified packet")
    return task


@atomic_operation
def _native_candidates(c, *, hydrate=True):
    tasks = _compute_native_candidates(c, hydrate=hydrate)
    from .supervision import observe_native
    with c.store._connection() as conn:
        observe_native(conn, tasks)
    return tasks


def _compute_native_candidates(c, *, hydrate=True):
    state = c.store.get_state(STATE)
    if not state:
        return []
    result = _resolution_tasks(c)
    from .workflow import acquisition_tasks
    result.extend(acquisition_tasks(c))
    from .calibration import pending_tasks
    from .workflow import enabled
    if not enabled(c):
        result.extend(pending_tasks(c))
    for task in frontiers.due_obligations(state):
        if task.get("task"):
            task = dict(task)
            if task.get("obligation_id"):
                task["task_id"] = "citation-source:" + task["obligation_id"]
                task["submission_contract"] = {"action": "retry-same-request | restart-citation-window | resolve-parent-identity | extracted-reference-list",
                    "identity": "For resolve-parent-identity: source-specific service ID fields; supply source_location and identity_reason",
                    "reason": "What resolved access/coverage, or why the reference list is complete",
                    "records": "For extracted-reference-list only: every reference identity in source order",
                    "source_locations": "For extracted-reference-list: source-bound asset/unit observations",
                    "exhaustion_evidence": "For extracted-reference-list: location of complete reference-list boundaries"}
            if hydrate:
                task = _hydrate_native_task(c, task)
            elif task.get("paper_id"):
                with c.store._connection() as conn:
                    row = conn.execute("SELECT json_extract(record,'$.source_generation'),json_extract(record,'$.packet_source_generation'),json_extract(record,'$.packet_path'),json_extract(record,'$.status') FROM papers WHERE id=?", (task["paper_id"],)).fetchone()
                source = dict(zip(("source_generation","packet_source_generation","packet_path","status"), row)) if row else {}
                if source.get("source_generation") is None:
                    source["source_generation"] = 1
                waiting = _native_source_wait(source)
                if waiting:
                    task["deferred_for_source_generation"] = waiting
            task.setdefault("task_id", task.get("paper_id"))
            result.append(task)
    pending_semantic = _pending_semantic(c)
    # Quiet queues request an audit only until the existing stopping predicate
    # has current evidence. Repeating an unchanged zero-yield audit indefinitely
    # creates work without learning anything. New/revised citation obligations
    # invalidate its bound hash and make the ordinary audit available again.
    current_principal_evidence = (state["principal_provisionally_satisfied"]
                                  and not frontiers.principal_errors(state, pending_semantic_jobs=pending_semantic))
    if not result and not pending_semantic and not current_principal_evidence and not any(o["status"] != "complete" for o in state["citation_obligations"].values()) and not any(w["status"] != "complete" for w in state["process_windows"].values()):
        result.append({"task": "citation-wave-and-frontier-audit", "task_id": "wave-audit", "state": state,
                "instructions": "Reconcile the complete backward/forward wave, deduplication, all title/abstract/rescue/audit decisions and missing text requests. Submit wave_id, obligation_ids, new_potentially_relevant, screening_complete, reason. A zero yield is a factual post-screening count, not an assumption from an empty queue. After a current zero-yield wave, enter the mandatory blind lane; do not claim native certification."})
    from .workflow import enabled
    if enabled(c):
        for task in result:
            if task.get("task_id") == "wave-audit":
                task["instructions"] = "Audit the focused-v1 active coverage only. Reconcile completed citation windows and genuinely new eligible nodes; report wave_id, obligation_ids, new_potentially_relevant, screening_complete and source-grounded reason. Add coverage_scope:'focused-v1'. Report deferred coverage separately; held uncertain/unavailable papers are not exclusions or evidence of scientific saturation. The mandatory blind lane and earned process windows still apply."
    return result


def _native_controls(conn):
    conn.execute("CREATE TABLE IF NOT EXISTS native_task_control(task_id TEXT PRIMARY KEY,owner TEXT,token INTEGER NOT NULL DEFAULT 0,lease_until REAL,available_at REAL NOT NULL DEFAULT 0,last_served REAL NOT NULL DEFAULT 0,reason TEXT,binding TEXT)")


def _native_transaction_view(c, conn):
    # Native leases and all nested writes share the same atomic source snapshot.
    from .transactions import transaction_view
    return transaction_view(c, conn)


def _native_binding(c, task):
    pid = task.get("paper_id")
    if pid:
        paper = c.store.paper(pid)
        packet = paper.get("packet_path")
        return digest({"task_id": task["task_id"], "source_generation": paper.get("source_generation", 1),
            "packet_source_generation": paper.get("packet_source_generation"),
            "source": file_hash(inside(c.run_dir / packet, c.run_dir)) if packet and _packet_is_current(paper) else digest(paper.get("abstract"))})
    return digest({key: value for key, value in task.items() if key not in {"control", "native_lease", "execution_role", "intended_profile", "instructions"}})


def list_native_tasks(c, *, limit=100, include_deferred=False):
    if type(limit) is not int or not 1 <= limit <= 1000:
        raise ValueError("Native task list limit must be 1..1000")
    candidates = _native_candidates(c, hydrate=False)
    with c.store._transaction() as conn:
        _native_controls(conn)
        controls = {row["task_id"]: dict(row) for row in conn.execute("SELECT * FROM native_task_control")}
    from .execution_policy import native_rank, primary_pending, load
    now = time.time()
    tasks = []
    with c.store._connection() as conn:
        policy = load(conn)
        preferred_pending = policy["retained_first"] and primary_pending(conn)
        for index, task in enumerate(candidates):
            control = controls.get(task["task_id"], {})
            if not include_deferred and (task.get("deferred_for_source_generation") or control.get("owner") or control.get("available_at", 0) > now):
                continue
            rank = native_rank(conn, task, policy)
            if not include_deferred and rank[0] and preferred_pending:
                continue
            task = dict(task, control=control)
            tasks.append((rank, control.get("last_served", 0), index, task))
    return [_hydrate_native_task(c, task) for _, _, _, task in sorted(tasks)[:limit]]


def next_native_task(c, *, owner=None, lease_seconds=900):
    if owner is None:
        tasks = list_native_tasks(c, limit=1)
        return tasks[0] if tasks else None
    if not isinstance(owner, str) or not owner.strip() or type(lease_seconds) is not int or not 1 <= lease_seconds <= 86400:
        raise ValueError("Native reservation requires an owner and lease_seconds in 1..86400")
    if getattr(c, "plan", {}).get("resources", {}).get("max_wall_seconds") is not None:
        if time.time() >= c._plan_deadline():
            raise ValueError("The recorded total wall-clock allowance has expired; pending native work is preserved")
    with c.store._transaction() as conn:
        from .supervision import admission_hold
        if admission_hold(conn, c.run_dir):
            return None
        _native_controls(conn)
        view = _native_transaction_view(c, conn)
        candidates = _native_candidates(view, hydrate=False)
        controls = {row["task_id"]: dict(row) for row in conn.execute("SELECT * FROM native_task_control")}
        now = time.time()
        from .execution_policy import native_rank, primary_pending, free_slots, load
        policy = load(conn)
        preferred_pending, slots = policy["retained_first"] and primary_pending(conn), free_slots(conn)
        choices = []
        for index, task in enumerate(candidates):
            control = controls.get(task["task_id"], {})
            # Expiration alone is not evidence that another worker died.
            if task.get("deferred_for_source_generation") or control.get("owner") not in {None, owner} or control.get("available_at", 0) > now:
                continue
            rank = native_rank(conn, task, policy)
            if control.get("owner") != owner and ((rank[0] and preferred_pending) or slots == 0):
                continue
            choices.append((0 if control.get("owner") == owner else 1, rank, control.get("last_served", 0), index, task, control))
        if not choices:
            return None
        _, _, _, _, task, control = min(choices, key=lambda value: value[:4])
        from .workflow import start_operational
        task = start_operational(view, task)
        task = _hydrate_native_task(view, task)
        token = control.get("token", 0) if control.get("owner") == owner else control.get("token", 0) + 1
        until = now + lease_seconds
        binding = control.get("binding") if control.get("owner") == owner else _native_binding(view, task)
        conn.execute("INSERT OR REPLACE INTO native_task_control VALUES(?,?,?,?,?,?,?,?)",
                     (task["task_id"], owner, token, until, 0, now, "Explicit native worker reservation", binding))
        c.store._event(conn, "native_task_reserved", {"task_id": task["task_id"], "owner": owner,
                       "token": token, "lease_until": until, "task_sha256": digest(task)})
        return dict(task, native_lease={"owner": owner, "token": token, "lease_until": until})


def defer_native_task(c, task_id, *, actor, reason, delay_seconds=300, lease_token=None):
    if not str(actor).strip() or not str(reason).strip() or type(delay_seconds) is not int or not 0 <= delay_seconds <= 604800:
        raise ValueError("Native deferral requires actor/reason and delay_seconds in 0..604800")
    if task_id not in {task["task_id"] for task in _native_candidates(c, hydrate=False)}:
        raise ValueError("Unknown or already completed native task")
    with c.store._transaction() as conn:
        _native_controls(conn)
        row = conn.execute("SELECT * FROM native_task_control WHERE task_id=?", (task_id,)).fetchone()
        old = dict(row) if row else {}
        if old.get("owner") and (old["owner"] != actor or old["token"] != lease_token):
            raise ValueError("Only the reserving owner with its token may defer/release this native task")
        now = time.time()
        conn.execute("INSERT OR REPLACE INTO native_task_control VALUES(?,?,?,?,?,?,?,?)",
                     (task_id, None, old.get("token", 0), None, now + delay_seconds, now, reason, None))
        c.store._event(conn, "native_task_deferred", {"task_id": task_id, "actor": actor,
                       "reason": reason, "available_at": now + delay_seconds})
    return {"task_id": task_id, "status": "deferred", "available_at": now + delay_seconds}


def recover_native_task(c, task_id, *, owner, lease_token, actor, reason, proof):
    """Fence an abandoned external-agent reservation using observed termination.

    A short-lived CLI PID is not the external agent's lifetime. The supervisor
    must therefore supply its actual harness/task termination observation, bound
    to the recorded owner. Expiration, silence, and elapsed time alone are never
    accepted. Live work must be interrupted and observed terminated first.
    """
    if (not all(isinstance(v, str) and v.strip() for v in (task_id, owner, actor, reason))
            or type(lease_token) is not int or lease_token < 1):
        raise ValueError("Native recovery requires task, owner, current token, actor and reason")
    if (not isinstance(proof, dict) or proof.get("kind") != "supervisor-observed-termination"
            or proof.get("owner") != owner
            or proof.get("terminal_status") not in {"completed", "failed", "interrupted", "terminated"}
            or not isinstance(proof.get("source"), str) or not proof["source"].strip()
            or not isinstance(proof.get("evidence"), str) or not proof["evidence"].strip()):
        raise ValueError("Native recovery requires a source-grounded supervisor observation that this owner has terminated; expiry is insufficient")
    try:
        observed = datetime.fromisoformat(proof["observed_at"].replace("Z", "+00:00"))
        if observed.tzinfo is None or observed > datetime.now(timezone.utc):
            raise ValueError("Observation must have a timezone and not be in the future")
    except (KeyError, TypeError, AttributeError, ValueError) as exc:
        raise ValueError("Termination proof requires a valid observed_at timestamp") from exc
    with c.store._transaction() as conn:
        _native_controls(conn)
        row = conn.execute("SELECT * FROM native_task_control WHERE task_id=?", (task_id,)).fetchone()
        if not row or row["owner"] != owner or row["token"] != lease_token:
            raise ValueError("Recovery proof does not match the current native owner/token")
        # last_served is the latest reservation/renewal. A termination receipt
        # from an older incarnation cannot release a subsequently resumed worker.
        if observed.timestamp() < row["last_served"]:
            raise ValueError("Termination observation predates the latest reservation or renewal")
        now = time.time()
        conn.execute("UPDATE native_task_control SET owner=NULL,token=token+1,lease_until=NULL,available_at=?,last_served=?,reason=?,binding=NULL WHERE task_id=? AND owner=? AND token=?",
                     (now, now, reason, task_id, owner, lease_token))
        c.store._event(conn, "native_task_recovered", {"task_id": task_id, "owner": owner,
            "old_token": lease_token, "new_token": lease_token + 1, "actor": actor, "reason": reason, "proof": proof})
    return {"task_id": task_id, "status": "released-after-observed-termination", "fenced_token": lease_token,
            "reason": "The old worker cannot submit; the unchanged native obligation is available for reassignment"}


def _source_proof(c, paper, payload):
    if not _packet_is_current(paper):
        raise ValueError("Native full-text decisions need a verified packet for the current source generation")
    if type(payload.get("source_generation")) is not int or payload["source_generation"] != paper.get("source_generation", 1):
        raise ValueError("Native submission source_generation does not match the current verified packet")
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
    if not isinstance(payload, dict) or not isinstance(actor, str) or not actor.strip():
        raise ValueError("Native submission requires a payload and named actor")
    with c.store._transaction() as conn:
        _native_controls(conn)
        view = _native_transaction_view(c, conn)
        candidates = {task["task_id"]: task for task in _native_candidates(view, hydrate=False)}
        binding = _native_binding(view, candidates[paper_id]) if paper_id in candidates else None
        row = conn.execute("SELECT * FROM native_task_control WHERE task_id=?", (paper_id,)).fetchone()
        lease = payload.get("native_lease") or {}
        if row and row["owner"]:
            if lease.get("owner") != row["owner"] or lease.get("token") != row["token"] or actor != row["owner"]:
                raise ValueError("Native submission requires the current owner and reservation token")
            if row["binding"] != binding:
                raise ValueError("Native task source changed since reservation; release and re-read the new evidence")
            token = row["token"]
        elif lease:
            raise ValueError("Native reservation was released or superseded")
        else:
            token = (row["token"] if row else 0) + 1
            now = time.time()
            conn.execute("INSERT OR REPLACE INTO native_task_control VALUES(?,?,?,?,?,?,?,?)",
                         (paper_id, actor, token, now + 900, 0, now, "Atomic submission reservation", binding))
            c.store._event(conn, "native_task_reserved", {"task_id": paper_id, "owner": actor,
                "token": token, "lease_until": now + 900, "reason": "Legacy direct submission atomically reserves its execution unit"})
        result = _submit_native(view, paper_id, payload, actor)
        changed = conn.execute("UPDATE native_task_control SET owner=NULL,lease_until=NULL,last_served=? WHERE task_id=? AND owner=? AND token=?",
                               (time.time(), paper_id, actor, token))
        if changed.rowcount != 1:
            raise ValueError("Native reservation changed during submission; no changes committed")
        c.store._event(conn, "native_task_submission_finished", {"task_id": paper_id, "actor": actor,
            "lease": {"owner": actor, "token": token}, "source_binding": binding})
    if paper_id.startswith("calibration:"):
        c._calibration_dirty = True
        c.reconcile_calibration()
    return result


def _submit_native(c, paper_id, payload, actor):
    task_id = paper_id
    if not str(actor).strip() or not str(payload.get("reason", "")).strip():
        raise ValueError("Native submission requires actor and reason")
    from .workflow import submit_operational
    handled = submit_operational(c, paper_id, payload, actor)
    if handled is not None:
        return handled
    if paper_id.startswith("calibration:"):
        from .calibration import record_adjudication
        return record_adjudication(c, paper_id[len("calibration:"):],
                                   {k: v for k, v in payload.items() if k != "native_lease"})
    if paper_id.startswith("source:") or paper_id.startswith("citation-source:"):
        return _submit_source_resolution(c, paper_id, payload, actor)
    if paper_id.startswith("process:"):
        paper_id = paper_id[len("process:"):]
        saved = c.store.get_state("native-assessment:" + paper_id)
        if not saved:
            raise ValueError("Process audit requires an existing source-bound native assessment")
        paper = c.store.paper(paper_id)
        if _saved_native_is_current(c, paper, saved):
            payload = dict(saved, **payload)
        elif not all(key in payload for key in ("groups", "paper_state", "source_locations", "source_generation")):
            raise ValueError("A changed source generation requires a fresh full native assessment before process-only continuation")
    if paper_id == "wave-audit":
        from .workflow import enabled
        if enabled(c) and payload.get("coverage_scope") != "focused-v1":
            raise ValueError("Focused wave audit must explicitly name its selective coverage_scope")
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
        if hasattr(c, "reconcile_metadata"):
            c.reconcile_metadata(value[0])
        _schedule_new(c, [value], "resolved:" + key + ":")
        saved = c.store.get_state("native-assessment:" + value[0])
        if saved:
            paper = c.store.paper(value[0])
            if _saved_native_is_current(c, paper, saved):
                _change(c, lambda s: frontiers.record_node(s, _native_paper(paper, saved["paper_state"]), saved["groups"],
                    encounter_depth=min(paper.get("discovery_bridge_depths") or [0]),
                    reason="Resolved rediscovery restores independently eligible bridge lineage"), "Resolved identity lineage reconciled")
        c.store.set_state("identity-resolution:" + key, dict(task, resolved=True), "Bibliographic identity resolved by " + actor)
    else:
        paper = c.store.paper(paper_id)
        if not paper:
            raise ValueError("Unknown paper")
        if _native_source_wait(paper):
            raise ValueError("Native judgment deferred: the current source generation has no verified packet")
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
        native_paper = _native_paper(paper, payload["paper_state"])
        if native_paper["paper_id"] != paper_id:
            raise ValueError("Cannot replace native focal paper identity")
        activations = payload.get("process_activations", [])
        c.store.require_native_ids(paper_id, payload["groups"],
                                  comparisons=[a["comparison"] for a in activations])
        if process["status"] != "unresolved" and (process["status"] == "eligible-comparisons-recorded") != bool(activations):
            raise ValueError("Process audit and activation records disagree")
        def apply(state):
            result = frontiers.record_node(state, native_paper, payload["groups"],
                                           encounter_depth=min(paper.get("discovery_bridge_depths") or [0]), reason=payload["reason"])
            for activation in activations:
                if activation["comparison"]["paper_id"] != paper_id:
                    raise ValueError("Process trigger belongs to another paper")
                result = frontiers.activate_process(result, activation["comparison"], activation["variants"], normalization_reason=activation["normalization_reason"])
            pending = result.setdefault("process_assessment_pending", {})
            if process["status"] == "unresolved":
                pending[paper_id] = {"task": "process-search-audit", "task_id": "process:" + paper_id,
                                     "paper_id": paper_id, "reason": process["reason"]}
            else:
                pending.pop(paper_id, None)
            return result
        _change(c, apply, "Source-bound native discovery assessment submitted by " + actor)
        c.store.set_state("native-assessment:" + paper_id, dict(payload, packet_sha256=packet_hash, actor=actor), "Native route judgment and source identity retained for lineage reuse")
        from .workflow import enabled, move_native_pending
        if enabled(c) and process["status"] == "unresolved":
            move_native_pending(c, [paper_id], "Single source reading leaves process inference unresolved; retain the gap without an automatic reread")
    event = {"task_id": task_id, "actor": actor, "payload_sha256": digest(payload), "reason": payload["reason"]}
    if task_id.startswith("identity:"):
        event["paper_id"] = value[0]
    elif task_id == "wave-audit":
        event["wave_id"] = payload["wave_id"]
    else:
        event["paper_id"] = paper_id
    c.store.event("native_discovery_submission", event)
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
        if obligation.get("coverage_generation"):
            request["coverage_generation"] = obligation["coverage_generation"]
    from .search_holds import require_unheld
    require_unheld(c, request)
    if _citation_block(c, request):
        raise ValueError("Operational citation depth boundary blocks source-resolution retrieval; the obligation remains pending")
    generation_key = "source-resolution-generation:" + task_id
    generation = c.store.get_state(generation_key, 0) + 1
    action = payload.get("action")
    if action not in {"retry-same-request", "restart-citation-window", "resolve-parent-identity", "extracted-reference-list"}:
        raise ValueError("Unsupported source-resolution action")
    if action in {"restart-citation-window", "resolve-parent-identity"}:
        if not obligation_id:
            raise ValueError("Only citation windows support coverage generations and parent identities")
        if action == "resolve-parent-identity":
            identity = payload.get("identity") or {}
            source = payload.get("source")
            if not str(payload.get("source_location", "")).strip() or not str(payload.get("identity_reason", "")).strip():
                raise ValueError("Parent identity requires source_location and a title/author/year matching reason")
            if source == "OpenAlex":
                if set(identity) != {"openalex_id"} or not re.fullmatch(r"(?:https://openalex.org/)?W\d+", str(identity.get("openalex_id", ""))):
                    raise ValueError("OpenAlex identity must contain one verified W identifier")
                identity = {"openalex_id": "https://openalex.org/" + identity["openalex_id"].rsplit("/", 1)[-1]}
            elif source == "Europe PMC":
                if set(identity) != {"epmc_id", "epmc_source"} or not all(re.fullmatch(r"[A-Za-z0-9._-]+", str(identity.get(k, ""))) for k in identity):
                    raise ValueError("Europe PMC identity requires verified epmc_id and epmc_source")
            else:
                raise ValueError("Parent identity may resolve OpenAlex or Europe PMC only")
            pid = obligation["parent"]["paper_id"]
            c.store.set_state("citation-identity:" + pid + ":" + source,
                {"identity": identity, "source": source, "source_location": payload["source_location"],
                 "identity_reason": payload["identity_reason"], "actor": actor},
                "Agent independently corroborated citation service identity without changing the logical work")
            c.store.update_paper(pid, identity, "Verified citation-service identity: " + payload["identity_reason"], actor=actor)
            def resolve(s):
                for direction in ("backward", "forward"):
                    key = pid + ":" + direction
                    if key in s["citation_obligations"] and s["citation_obligations"][key]["status"] != "complete":
                        s = frontiers.restart_citation(s, key, reason=payload["reason"], identity=identity, source=source)
                return s
            _change(c, resolve, "Source identity resolution reopens only unfinished citation directions")
        else:
            _change(c, lambda s: frontiers.restart_citation(s, obligation_id, reason=payload["reason"]),
                    "Explicit new citation coverage generation retains earlier pages and encounters")
        c.store.event("source_resolution_submitted", {"task_id": task_id, "actor": actor, "action": action, "reason": payload["reason"]})
        return discovery_tick(c)
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
    pending_semantic = _pending_semantic(c)
    checked = frontiers.readiness(state, pending_semantic_jobs=pending_semantic, missing_texts_current=False, durable_validation_passed=False)
    # These two assumptions deliberately ask only whether the operational
    # frontiers are exhausted. They do not assert that final scientific
    # validation or missing-text reconciliation has actually happened.
    frontier_check = frontiers.readiness(state, pending_semantic_jobs=pending_semantic,
                                        missing_texts_current=True, durable_validation_passed=True)
    operational = c.store.status()
    pending_native = _native_candidates(c, hydrate=False)
    from .workflow import enabled, active_jobs
    if enabled(c):
        operational = dict(operational, **active_jobs(c))
    from .search_holds import records
    with c.store._connection() as conn:
        search_holds = records(conn)
    exhausted = (not search_holds and frontier_check["ready"] and not pending_native and not operational["unfinished"]
                 and not operational["failed"] and not c.store.unprojected_results(limit=1))
    task = next_native_task(c)
    task_summary = {key: task.get(key) for key in ("task", "task_id", "paper_id", "reason") if task.get(key) is not None} if task else None
    windows = {**state["blind_windows"], **state["process_windows"]}
    completed_windows = [w for w in windows.values() if w["status"] == "complete"]
    ranked_coverage = {"required_windows": len(windows), "completed_windows": len(completed_windows),
        "returned_encounters": sum(w.get("returned_count", 0) for w in completed_windows),
        "reported_hits_across_windows": sum(w.get("reported_total", 0) for w in completed_windows),
        "truncated_windows": sum(w.get("truncated") is True for w in completed_windows),
        "truncated_window_ids": sorted(w["window_key"] for w in completed_windows if w.get("truncated") is True),
        "source_exhausted_windows": sum(w.get("source_exhausted") is True for w in completed_windows),
        "meaning": "Completing a ranked window covers its authorized return only; truncated windows do not establish source exhaustion. Totals count cross-window overlap."}
    return {"initialized": True, "phase": state["phase"], "pending_agent_task": task_summary,
            "operational_frontiers_exhausted": exhausted,
            "held_search_windows": search_holds,
            "checkpoint": "operational-frontiers-exhausted-final-review" if exhausted else "frontier-work-pending",
            "pending_native_tasks": len(pending_native),
            "latest_citation_wave": state["citation_wave_audits"][-1] if state["citation_wave_audits"] else None,
            "final_review_required": ["Reconcile missing texts and unresolved readings", "Resolve any remaining scientific uncertainties", "Complete frozen native records, derived exports and native validation"],
            "ranked_query_coverage": ranked_coverage,
            "max_citation_depth": state.get("max_citation_depth"),
            "depth_limited_obligations": sum(o["status"] == "depth-limited" for o in state["citation_obligations"].values()),
            "depth_unresolved_obligations": sum(o["status"] == "depth-unresolved" for o in state["citation_obligations"].values()),
            "deepest_discovered_citation_depth": citation_depth.summary(c.store),
            "hop_depth_convention": "Ordinary citation hops from frozen seeds/anchors or separately labelled independent process/blind query roots at depth 0; CORE resets only bridge lineage",
            "frontier_checks": checked, "native_scientific_completion": False,
            "reason": "Portable discovery orchestrates prospects; certification still requires the frozen native ledger and validator"}
