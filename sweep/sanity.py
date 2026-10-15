"""Bounded operational sanity checks, safe while independent workers run.

This is a metadata/decision-trail check, not scientific approval or a replacement
for validation.validate. Each pass checks new audit events and their referenced
records, plus a rotating sample of older papers/jobs. It does not rehash sources,
load PDF/text contents, scan the entire event history, or infer missing metadata.
All reads share one WAL snapshot. Changes committed afterwards are considered by
the next pass, rather than incorrectly invalidating the snapshot just checked.
"""
from __future__ import annotations
from . import workflow

import json
from pathlib import Path
import re
import sqlite3
import time

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError
from runtime.source_reader.schema import output_schema, validate_assessment

from .common import canonical, digest, save_json
from . import execution_policy, screening
from .store import normalize_doi

SCOPE = "incremental-operational-sanity"
STATE_KEY = "state:sanity-checkpoint"
SCREEN_STAGES = {"title", "abstract", "rescue", "audit"}
REASON_EVENTS = {"paper_added", "paper_updated", "paper_metadata_enriched", "discovery_encounter",
                 "control_updated", "control_delta", "job_failed", "job_deferred", "job_superseded",
                 "native_scientific_id_reserved", "retrieval_parked"}
_SHA = re.compile(r"[0-9a-f]{64}\Z")


def check(coordinator_or_store, *, max_events=2000, max_papers=100, max_jobs=100,
          persist=True, deadline=None):
    """Check new events and affected records, plus bounded rotating old records.

    max_papers/max_jobs bound the rotating samples; event-referenced records are
    also checked (bounded by max_events and the frozen job batch sizes). Missing
    optional bibliography, absent abstracts, and unresolved source retrieval are
    notices, not errors. Pass ``persist=False`` for a read-only inspection.
    A failed pass keeps its cursor so repairing and rechecking cannot silently
    skip the failing event. A concurrent checker cannot overwrite a newer cursor.
    """
    for name, value in (("max_events", max_events), ("max_papers", max_papers), ("max_jobs", max_jobs)):
        if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 10000:
            raise ValueError(name + " must be an integer in 1..10000")
    store = getattr(coordinator_or_store, "store", coordinator_or_store)
    root = Path(store.run_dir).resolve()
    started = time.monotonic()
    errors, notices, checks = [], [], {}
    error_count = notice_count = 0
    snapshot = cursor = 0
    old_state_text = None
    state = {}
    coverage = {}

    def tick(name, count=1):
        if deadline is not None and time.monotonic() >= deadline:
            raise TimeoutError("Sanity-check deadline reached; cursor is unchanged")
        checks[name] = checks.get(name, 0) + count

    def issue(code, entity, reason, *, notice=False):
        nonlocal error_count, notice_count
        if notice:
            notice_count += 1
            target = notices
        else:
            error_count += 1
            target = errors
        if len(target) < 100:
            target.append({"code": code, "entity": str(entity), "reason": str(reason)[:800]})

    def require(value, reason):
        if not value:
            raise ValueError(reason)

    def nonblank(value):
        return isinstance(value, str) and bool(value.strip())

    def local_file(path):
        require(nonblank(path), "Missing source path")
        value = Path(path)
        value = value.resolve() if value.is_absolute() else (root / value).resolve()
        require(value.is_relative_to(root), "Source path escapes this run")
        require(value.is_file(), "Referenced source file is absent: " + str(path))
        tick("file_presence")

    def sha(value):
        require(isinstance(value, str) and _SHA.fullmatch(value), "Missing or malformed source hash binding")

    def object_json(value):
        result = json.loads(value)
        require(isinstance(result, dict), "Stored JSON must be an object")
        return result

    try:
        with store._connection() as conn:
            conn.set_progress_handler(lambda: int(deadline is not None and time.monotonic() >= deadline), 10000)
            conn.execute("BEGIN")
            snapshot = conn.execute("SELECT coalesce(max(id),0) FROM events").fetchone()[0]
            previous = conn.execute("SELECT value FROM meta WHERE key=?", (STATE_KEY,)).fetchone()
            old_state_text = previous[0] if previous else None
            state = object_json(old_state_text) if old_state_text else {}
            cursor = state.get("event_id", 0)
            require(isinstance(cursor, int) and not isinstance(cursor, bool) and 0 <= cursor <= snapshot,
                    "Sanity event cursor is invalid or points beyond durable history")
            require(conn.execute("SELECT 1 FROM meta WHERE key='plan'").fetchone(), "Run is not initialized")
            try:
                from .search_holds import validate as validate_search_holds
                tick("search_window_holds", validate_search_holds(conn))
            except (ValueError, KeyError, TypeError) as exc:
                issue("search_window_holds", "query-windows", exc)
            affected_papers, affected_jobs = set(), set()
            event_end = cursor

            def provenance(pid, value):
                require(isinstance(value, dict) and value, "Discovery encounter has no provenance")
                require(any(nonblank(value.get(k)) for k in ("route", "source", "search")),
                        "Discovery provenance lacks a route or source")
                if value.get("search_job_id"):
                    row = conn.execute("SELECT stage,state,payload,result FROM jobs WHERE id=?", (value["search_job_id"],)).fetchone()
                    require(row and row["stage"] == "search" and row["state"] == "complete",
                            "Discovery provenance references no completed search job")
                    payload, result = object_json(row["payload"]), object_json(row["result"])
                    require(value.get("snapshot_sha256") == result.get("snapshot_sha256") and value.get("snapshot_sha256"),
                            "Discovery snapshot differs from its completed search result")
                    require(value.get("source") == payload.get("source"), "Discovery source differs from its search job")
                    rank = value.get("result_rank")
                    require(isinstance(rank, int) and not isinstance(rank, bool) and rank > 0,
                            "Search encounter needs a positive result rank")
                tick("encounter_provenance")

            # Extract small event fields inside SQLite: model receipts and frontier
            # snapshots can contain large texts that this checker need not load.
            sql = """SELECT id,kind,json_valid(payload) AS valid,
                CASE WHEN json_valid(payload) THEN json_type(payload) END AS shape,
                CASE WHEN json_valid(payload) THEN json_extract(payload,'$.reason') END AS reason,
                CASE WHEN json_valid(payload) THEN json_extract(payload,'$.paper_id') END AS paper_id,
                CASE WHEN json_valid(payload) THEN json_extract(payload,'$.job_id') END AS job_id,
                CASE WHEN json_valid(payload) THEN json_extract(payload,'$.task_id') END AS task_id,
                CASE WHEN json_valid(payload) THEN json_extract(payload,'$.wave_id') END AS wave_id,
                CASE WHEN kind='discovery_encounter' AND json_valid(payload)
                     THEN json_extract(payload,'$.provenance') END AS provenance
                FROM events WHERE id>? AND id<=? AND kind!='operational_sanity' ORDER BY id LIMIT ?"""
            for row in conn.execute(sql, (cursor, snapshot, max_events)):
                event_end = row["id"]
                try:
                    require(row["valid"] and row["shape"] == "object", "Audit event payload is not a JSON object")
                    if row["kind"] in REASON_EVENTS:
                        require(nonblank(row["reason"]), "Recorded state change lacks a reason")
                    pid = row["paper_id"]
                    if row["kind"] == "native_discovery_submission":
                        # Older releases mislabeled identity/wave task IDs as paper_id.
                        # Interpret only this event type; never skip arbitrary bad IDs.
                        task_id = row["task_id"] if row["task_id"] is not None else pid
                        require(nonblank(task_id), "Native submission has no task identity")
                        if task_id.startswith("identity:"):
                            key = task_id[len("identity:"):]
                            saved = conn.execute("SELECT value FROM meta WHERE key=?",
                                                 ("state:identity-resolution:" + key,)).fetchone()
                            require(saved is not None, "Audit trail references an absent bibliographic identity task")
                            task = object_json(saved[0])
                            require(task.get("task_id") == task_id and task.get("resolved") is True,
                                    "Bibliographic identity task is mismatched or unresolved")
                            encounter = conn.execute("SELECT value FROM meta WHERE key=?",
                                                     ("state:encounter:" + key,)).fetchone()
                            require(encounter is not None, "Resolved identity lacks its durable paper binding")
                            binding = json.loads(encounter[0])
                            require(isinstance(binding, list) and len(binding) == 2 and nonblank(binding[0]),
                                    "Resolved identity paper binding is malformed")
                            require(pid == (binding[0] if row["task_id"] is not None else task_id),
                                    "Native identity submission paper differs from its durable binding")
                            pid = binding[0]
                        elif task_id == "wave-audit":
                            require(pid is None if row["task_id"] is not None else pid == "wave-audit",
                                    "Wave audit must not name a paper")
                            saved = conn.execute("SELECT json_extract(value,'$.citation_wave_audits') FROM meta WHERE key='state:discovery_frontiers'").fetchone()
                            audits = json.loads(saved[0]) if saved and saved[0] else []
                            require(isinstance(audits, list) and all(isinstance(a, dict) for a in audits),
                                    "Frontier wave audit history is malformed")
                            require(any(a.get("reason") == row["reason"] and
                                        (row["task_id"] is None or a.get("wave_id") == row["wave_id"])
                                        for a in audits), "Wave submission lacks its recorded frontier audit")
                            pid = None
                        else:
                            require(pid and task_id in (pid, "process:" + pid),
                                    "Native submission task does not match its paper")
                    if pid:
                        require(isinstance(pid, str), "Audit paper ID must be text")
                        affected_papers.add(pid)
                    if row["job_id"]:
                        require(isinstance(row["job_id"], str), "Audit job ID must be text")
                        affected_jobs.add(row["job_id"])
                    if row["kind"] == "discovery_encounter":
                        provenance(row["paper_id"], json.loads(row["provenance"]))
                    tick("events")
                except (ValueError, TypeError, KeyError) as exc:
                    issue("event_record", row["id"], exc)

            def rotate(table, key, limit):
                after = state.get(key, "")
                require(isinstance(after, str), "Invalid rotating sample cursor")
                rows = [r[0] for r in conn.execute("SELECT id FROM " + table + " WHERE id>? ORDER BY id LIMIT ?", (after, limit))]
                reached_end = len(rows) < limit
                return rows, "" if reached_end else rows[-1]

            paper_sample, paper_after = rotate("papers", "paper_after", max_papers)
            job_sample, job_after = rotate("jobs", "job_after", max_jobs)

            selected_papers = affected_papers | set(paper_sample)
            selected_jobs = affected_jobs | set(job_sample)
            for pid in selected_papers:
                bound = conn.execute("SELECT json_extract(record,'$.retrieval_job') FROM papers WHERE id=?", (pid,)).fetchone()
                if bound and bound[0]:
                    selected_jobs.add(bound[0])
            parked_ids = {jid for jid in selected_jobs if conn.execute(
                "SELECT 1 FROM jobs WHERE id=? AND state='parked'", (jid,)).fetchone()}
            # One history scan, retaining only this bounded batch's parking
            # events; never rescan the entire ledger for each parked paper.
            parking = {}
            if parked_ids:
                for event in conn.execute("SELECT json_extract(payload,'$.job_id') jid,payload FROM events WHERE kind='retrieval_parked' ORDER BY id"):
                    if event["jid"] in parked_ids:
                        parking[event["jid"]] = object_json(event["payload"])

            for pid in sorted(selected_papers):
                try:
                    row = conn.execute("SELECT id,doi,status,record FROM papers WHERE id=?", (pid,)).fetchone()
                    require(row is not None, "Audit trail references an absent paper")
                    paper = object_json(row["record"])
                    require(re.fullmatch(r"P[0-9]{6,}", pid), "Malformed allocated paper identifier")
                    require(paper.get("paper_id") == pid and paper.get("status") == row["status"],
                            "Paper identity/status differs from its indexed state")
                    from .coordinator import validate_record
                    validate_record(paper)
                    require((normalize_doi(paper.get("doi")) or None) == row["doi"], "Indexed DOI differs from paper metadata")
                    for name in ("year", "publication_year"):
                        value = paper.get(name)
                        require(value in (None, "") or not isinstance(value, bool) and
                                isinstance(value, (str, int)) and str(value).isdigit(),
                                name + " must be a supplied numeric year or explicitly absent")
                    for name in ("authors", "author"):
                        value = paper.get(name)
                        require(value is None or isinstance(value, (str, list)), name + " must be a supplied author string/list or explicitly absent")
                        if isinstance(value, list):
                            require(all(isinstance(author, (str, dict)) for author in value), "Author list contains an invalid entry")
                    missing = [k for k in ("doi", "year", "authors") if not paper.get(k)]
                    if missing:
                        issue("incomplete_bibliography", pid, "Not supplied: " + ", ".join(missing) + "; retain without inventing metadata", notice=True)
                    if not paper.get("abstract"):
                        issue("abstract_unavailable", pid, "No abstract stored; retrieval may proceed after title retention", notice=True)
                    first = conn.execute("SELECT provenance FROM encounters WHERE paper_id=? ORDER BY id LIMIT 1", (pid,)).fetchone()
                    require(first is not None, "Paper has no durable discovery encounter")
                    provenance(pid, object_json(first[0]))
                    for stage, value in paper.get("screening", {}).items():
                        require(stage in SCREEN_STAGES, "Unknown screening stage")
                        saved = conn.execute("SELECT stage,state,payload,result FROM jobs WHERE id=?", (value.get("job_id"),)).fetchone()
                        require(saved and saved["stage"] == stage and saved["state"] == "complete", "Screening decision lacks its completed stage job")
                        result = object_json(saved["result"])
                        matches = [d for d in result["assessment"]["decisions"] if d["paper_id"] == pid]
                        require(len(matches) == 1 and matches[0] == value.get("decision"), "Paper screening differs from its durable job decision")
                        require(nonblank(matches[0].get("reason")), "Screening decision lacks a paper-specific reason")
                    current = paper.get("screening_current")
                    if current:
                        saved = paper.get("screening", {}).get(current.get("stage"))
                        require(saved and saved.get("job_id") == current.get("job_id") and saved["decision"]["decision"] == current.get("decision"),
                                "Current screening differs from paper screening history")
                        sha(current.get("source_sha256"))
                    if paper["status"] in {"title-excluded", "abstract-excluded"}:
                        require(current and current.get("decision") == "exclude", "Excluded paper has no current exclusion decision")
                    if paper.get("assessment") is not None or paper["status"] in {"assessed", "reading-incomplete"}:
                        saved = conn.execute("SELECT stage,state,payload,result FROM jobs WHERE id=?", (paper.get("reader_job"),)).fetchone()
                        require(saved and saved["stage"] == "reader" and saved["state"] == "complete", "Assessment lacks its completed reader job")
                        payload, result = object_json(saved["payload"]), object_json(saved["result"])
                        require(payload.get("paper_id") == pid and workflow.assessment(result.get("assessment"), payload) == paper.get("assessment"), "Assessment differs from its source-bound reader result")
                        expected_status = "assessed" if paper["assessment"].get("assessment_status") == "complete" else "reading-incomplete"
                        require(paper["status"] == expected_status, "Paper completion state differs from the reader's completeness report")
                        require(payload.get("packet_path") == paper.get("packet_path"), "Assessment refers to a superseded packet")
                        require(payload.get("packet_sha256") == paper.get("assessment_packet_sha256"), "Assessment packet hash differs from reader binding")
                        generation = paper.get("source_generation", 1)
                        # Rediscovery can briefly mark a new generation before
                        # its reconciliation invalidates the old assessment.
                        if not paper.get("retrieval_revision_pending"):
                            require(payload.get("source_generation", 1) == generation == paper.get("assessment_source_generation"), "Assessment belongs to a stale source generation")
                        affected_jobs.add(paper["reader_job"])
                    parked_retrieval = False
                    if paper.get("retrieval_job"):
                        saved = conn.execute("SELECT * FROM jobs WHERE id=?", (paper["retrieval_job"],)).fetchone()
                        parked_retrieval = saved is not None and saved["state"] == "parked"
                        if parked_retrieval:
                            execution_policy.parked_receipt(conn, saved, parking.get(saved["id"]), paper)
                        else:
                            require(saved and saved["stage"] == "retrieval" and saved["state"] == "complete", "Stored retrieval lacks its completed acquisition job")
                            require(object_json(saved["payload"]).get("paper_id") == pid and object_json(saved["result"]) == paper.get("retrieval"),
                                    "Paper retrieval differs from its acquisition result")
                    if paper["status"] == "reader-pending" or paper.get("assessment") is not None:
                        local_file(paper.get("packet_path"))
                        require(paper.get("retrieval", {}).get("status") == "verified", "Readable paper state lacks verified acquisition metadata")
                    if paper["status"].startswith("source-"):
                        retrieval = paper.get("retrieval")
                        require(isinstance(retrieval, dict) and nonblank(retrieval.get("reason")), "Unresolved retrieval lacks its recorded explanation")
                        require(parked_retrieval or paper["status"] == "source-" + retrieval.get("status", ""), "Missing-source status differs from retrieval record")
                        issue("source_unresolved", pid, retrieval["reason"], notice=True)
                    tick("papers")
                except (ValueError, TypeError, KeyError, AttributeError, OSError) as exc:
                    issue("paper_record", pid, exc)

            for jid in sorted(affected_jobs | set(job_sample)):
                try:
                    row = conn.execute("SELECT * FROM jobs WHERE id=?", (jid,)).fetchone()
                    require(row is not None, "Audit trail references an absent job")
                    require(re.fullmatch(r"J[0-9]{12,}", jid), "Malformed allocated job identifier")
                    payload = object_json(row["payload"])
                    stage, status = row["stage"], row["state"]
                    require(status in {"pending", "running", "complete", "failed", "parked"}, "Unknown job execution state")
                    require(not row["projected"] or status == "complete", "Uncompleted job marked projected")
                    if status == "running":
                        require(nonblank(row["owner"]) and row["lease_until"] is not None and row["token"] > 0, "Running job lacks its lease/owner binding")
                    require((row["result"] is not None) == (status == "complete"), "Job result presence contradicts execution state")
                    result = object_json(row["result"]) if status == "complete" else None
                    if status == "parked":
                        execution_policy.parked_receipt(conn, row, parking.get(jid))
                    if status == "failed":
                        require(nonblank(row["error"]), "Failed job lacks an explanation")
                    if stage in SCREEN_STAGES:
                        records = payload["source_records"]
                        require(digest(records) == payload["source_sha256"], "Screening source binding differs from captured metadata")
                        require([p["paper_id"] for p in records] == payload["paper_ids"], "Screening batch IDs differ from its metadata records")
                        require(1 <= len(records) <= (25 if stage == "title" else 10), "Screening batch exceeds its stage bound")
                        for record in records:
                            require(conn.execute("SELECT 1 FROM papers WHERE id=?", (record["paper_id"],)).fetchone(), "Screening batch references an absent paper")
                            require(stage != "title" or "abstract" not in record, "Title task contains unavailable abstract evidence")
                        if result is not None:
                            require(nonblank(result.get("actor")), "Completed screening lacks an actor")
                            screening.validate(result["assessment"], stage, records)
                    elif stage == "abstract-lookup":
                        from .workflow import validate_lookup
                        validate_lookup(payload, result)
                        require(conn.execute("SELECT 1 FROM papers WHERE id=?", (payload["paper_id"],)).fetchone(), "Abstract lookup references absent paper")
                    elif stage in {"reader", "retrieval"}:
                        require(conn.execute("SELECT 1 FROM papers WHERE id=?", (payload["paper_id"],)).fetchone(), "Source job references an absent paper")
                        if stage == "reader":
                            sha(payload.get("packet_sha256"))
                            local_file(payload.get("packet_path"))
                            if result is not None:
                                require(nonblank(result.get("actor")), "Completed reader lacks an actor")
                                from .workflow import assessment
                                checked_assessment = assessment(result["assessment"], payload)
                                Draft202012Validator(output_schema()).validate(checked_assessment)
                                # Retrieve only source IDs/page maps from the
                                # stored current asset metadata, never its text.
                                assets = conn.execute("""SELECT json_extract(s.value,'$.asset_id') AS asset_id,
                                    json_extract(s.value,'$.units') AS units FROM papers p,
                                    json_each(p.record,'$.retrieval.packet.sources') s WHERE p.id=?""", (payload["paper_id"],)).fetchall()
                                paper_row = conn.execute("SELECT json_extract(record,'$.packet_path') FROM papers WHERE id=?", (payload["paper_id"],)).fetchone()
                                if assets and paper_row[0] == payload.get("packet_path"):
                                    packet = {"sources": [{"asset_id": a["asset_id"], "units": json.loads(a["units"])} for a in assets]}
                                    require(not validate_assessment(checked_assessment, packet), "Reader decision trail contains invalid/unread source-unit references")
                                else:
                                    issue("source_units_deferred", jid, "Historical or external packet: source-unit membership remains the full validator's responsibility", notice=True)
                        elif result is not None:
                            require(nonblank(result.get("reason")), "Retrieval result lacks a reason")
                            if result.get("status") == "verified":
                                require(result.get("packet") and result.get("assets"), "Verified retrieval lacks its source packet/assets")
                                for asset in result["assets"]:
                                    for path_key, hash_key in (("original_path", "sha256"), ("text_path", "text_sha256"), ("map_path", "map_sha256")):
                                        local_file(asset.get(path_key))
                                        sha(asset.get(hash_key))
                            else:
                                require(not result.get("packet"), "Unverified retrieval exposes a ready reader packet")
                    elif stage == "search" and result is not None and result.get("retrieval_status") == "complete":
                        sha(result.get("snapshot_sha256"))
                        local_file(result.get("snapshot_path"))
                    for dependency in conn.execute("SELECT d.dependency_id,j.state FROM dependencies d LEFT JOIN jobs j ON j.id=d.dependency_id WHERE d.job_id=?", (jid,)):
                        require(dependency["state"] is not None, "Job references an absent dependency")
                        require(status not in {"running", "complete"} or dependency["state"] == "complete", "Job ran before a dependency completed")
                    tick("jobs")
                except (ValueError, TypeError, KeyError, AttributeError, OSError, ValidationError) as exc:
                    issue("job_record", jid, exc)

            for kind, table, prefix in (("paper", "papers", "P"), ("job", "jobs", "J"), ("reservation", "reservations", "B")):
                row = conn.execute("SELECT id FROM " + table + " ORDER BY id DESC LIMIT 1").fetchone()
                if row:
                    counter = conn.execute("SELECT next_value FROM counters WHERE kind=?", (kind,)).fetchone()
                    require(row[0].startswith(prefix) and row[0][1:].isdigit(), "Malformed durable identifier")
                    if not counter or counter[0] <= int(row[0][1:]):
                        issue("identifier_counter", kind, "Next identifier does not exceed durable IDs")
            tick("identifier_counters", 3)
            remaining = bool(conn.execute("SELECT 1 FROM events WHERE id>? AND id<=? AND kind!='operational_sanity' LIMIT 1", (event_end, snapshot)).fetchone())
            if not remaining:
                event_end = snapshot
            coverage = {"from_event_id": cursor, "through_event_id": event_end, "snapshot_event_id": snapshot,
                        "event_backlog": remaining, "papers": checks.get("papers", 0), "jobs": checks.get("jobs", 0),
                        "rotating_papers": len(paper_sample), "rotating_jobs": len(job_sample)}
            next_state = {"event_id": event_end, "paper_after": paper_after, "job_after": job_after}
    except TimeoutError:
        raise
    except (sqlite3.Error, ValueError, TypeError, KeyError, AttributeError, OSError) as exc:
        tick("snapshot_failure")
        issue("sanity_snapshot", "database", exc)
        next_state = state

    report = {"ok": error_count == 0, "errors": errors, "error_count": error_count,
              "notices": notices, "notice_count": notice_count, "checks": checks, "coverage": coverage,
              "scope": SCOPE, "snapshot_event_id": snapshot, "native_scientific_certification": False,
              "elapsed_seconds": round(time.monotonic() - started, 3),
              "limitations": ["Bounded metadata and decision-trail checks do not certify scientific judgments or full-corpus integrity.",
                              "Source contents/hashes and complete historical provenance require the full validator.",
                              "Absent optional metadata and legitimately unresolved sources are notices, never exclusions."]}
    if persist:
        with store._transaction() as conn:
            latest = conn.execute("SELECT value FROM meta WHERE key=?", (STATE_KEY,)).fetchone()
            if (latest[0] if latest else None) != old_state_text:
                report["persisted"] = False
                report["superseded_by_concurrent_check"] = True
                return report
            # Advance a revision even for failures so a concurrent older pass
            # cannot overwrite their report while their event cursor stays put.
            durable_state = dict(next_state if report["ok"] else state)
            durable_state["revision"] = state.get("revision", 0) + 1
            conn.execute("INSERT OR REPLACE INTO meta(key,value) VALUES(?,?)", (STATE_KEY, canonical(durable_state)))
            report["sanity_event_id"] = store._event(conn, "operational_sanity", {
                "ok": report["ok"], "snapshot_event_id": snapshot, "error_count": error_count,
                "coverage": coverage, "scope": SCOPE,
                "reason": "Bounded snapshot check of metadata, record bindings, provenance and decision reasons; no scientific certification"})
            report["persisted"] = True
            save_json(root / "delivery" / "sanity.json", report)
    return report
