"""Read-only operational audit, apart from its explicit report and audit event.

This checks storage, immutable evidence and recorded decisions. It neither judges
scientific eligibility nor certifies a frozen native registered run. Run at a
quiet checkpoint; concurrent changes make the resulting report stale.
"""
import hashlib
import json
import math
from pathlib import Path
import re
import sqlite3
import time
from jsonschema.exceptions import ValidationError, SchemaError

from . import reading, screening, sources
from .common import canonical, digest, file_hash, save_json

MODEL_STAGES = {"title", "abstract", "rescue", "audit", "reader"}
SCREEN_FIELDS = {"paper_id", "title", "year", "authors", "doi", "abstract"}
NONMATERIAL_EVENTS = ("operational_validation", "delivery_checkpoint", "throughput_estimate", "execution_session_finished")


def current(coordinator):
    """Cheap checkpoint freshness check; does not reread source file contents.

    An explicit fresh validate() is still required to detect external file
    tampering. This predicate only certifies that durable run state has not
    changed since the successful report's read snapshot.
    """
    try:
        report = json.loads((Path(coordinator.run_dir) / "delivery" / "validation.json").read_text())
        if report.get("ok") is not True or report.get("scope") != "operational-not-native-scientific":
            return False
        snapshot = report.get("snapshot_event_id")
        if not isinstance(snapshot, int) or isinstance(snapshot, bool):
            return False
        with coordinator.store._connection() as conn:
            recorded = conn.execute("SELECT kind,payload FROM events WHERE id=?", (report.get("validation_event_id"),)).fetchone()
            if not recorded or recorded["kind"] != "operational_validation":
                return False
            event = json.loads(recorded["payload"])
            if event.get("ok") is not True or event.get("snapshot_event_id") != snapshot:
                return False
            row = conn.execute("SELECT id FROM events WHERE kind NOT IN (?,?,?,?) ORDER BY id DESC LIMIT 1", NONMATERIAL_EVENTS).fetchone()
        return (row[0] if row else 0) <= snapshot
    except (OSError, ValueError, TypeError, AttributeError, sqlite3.Error):
        return False


def validate(coordinator):
    root, store = Path(coordinator.run_dir).resolve(), coordinator.store
    errors, checks, error_count = [], {}, 0
    started = time.time()

    def checked(name, amount=1):
        checks[name] = checks.get(name, 0) + amount

    def error(code, entity, reason):
        nonlocal error_count
        error_count += 1
        if len(errors) < 100:
            errors.append({"code": code, "entity": str(entity), "reason": str(reason)[:800]})

    def require(condition, message):
        if not condition:
            raise ValueError(message)

    def local(path):
        value = Path(path)
        value = value.resolve() if value.is_absolute() else (root / value).resolve()
        require(value.is_relative_to(root), "Stored evidence path escapes this run")
        return value

    def load(path):
        return json.loads(local(path).read_text(encoding="utf-8"))

    def hash_file(path, expected):
        require(isinstance(expected, str) and re.fullmatch(r"[0-9a-f]{64}", expected), "Missing/malformed SHA-256 binding")
        require(file_hash(local(path)) == expected, "Stored file no longer matches its immutable hash")
        checked("file_hashes")

    def packet_valid(packet):
        require(isinstance(packet, dict) and not set(packet) - {"paper", "paper_id", "sources", "acquisition_gaps"}, "Reader packet contains non-source fields")
        _, schema = reading.prepare(packet)
        require(isinstance(schema, dict), "Reader packet schema unavailable")
        for asset in packet["sources"]:
            require(asset.get("content_sha256") == hashlib.sha256(asset["content"].encode()).hexdigest(), "Reader source content hash mismatch")
        checked("reader_packets")

    def asset_valid(asset):
        hash_file(asset["original_path"], asset["sha256"])
        hash_file(asset["text_path"], asset["text_sha256"])
        hash_file(asset["map_path"], asset["map_sha256"])
        require(local(asset["text_path"]).read_text(encoding="utf-8") == asset["content"], "Extracted text differs from reader asset content")
        require(load(asset["map_path"]) == asset["units"], "Source unit map differs from recorded asset")
        require(asset["content_sha256"] == hashlib.sha256(asset["content"].encode()).hexdigest(), "Asset content hash mismatch")
        cache = local(asset["original_path"]).parent / (asset["sha256"] + ".extraction.json")
        cached = load(cache)
        require(cached.get("sha256") == sources.digest(cached["payload"]), "Extraction cache integrity mismatch")
        payload = cached["payload"]
        require(payload["source_sha256"] == asset["sha256"], "Extraction refers to another source version")
        reconstructed = "\n\n".join("[{}]\n{}".format(unit["unit_id"], unit["content"]) for unit in payload["units"])
        require(reconstructed == asset["content"], "Extraction units do not reconstruct supplied content")
        checked("verified_assets")

    snapshot_event_id = 0
    try:
        with store._connection() as conn:
            conn.execute("PRAGMA temp_store=FILE")
            conn.execute("BEGIN")
            snapshot_event_id = conn.execute("SELECT coalesce(max(id),0) FROM events").fetchone()[0]
            for row in conn.execute("PRAGMA integrity_check"):
                if row[0] != "ok":
                    error("sqlite_integrity", "database", row[0])
            checked("sqlite_integrity")
            for row in conn.execute("PRAGMA foreign_key_check"):
                error("foreign_key", row[0], tuple(row))
            checked("foreign_keys")
            # Disk-backed indexed audit summaries avoid a corpus-sized Python
            # lookup table and do not modify the run's main database.
            conn.execute("CREATE TEMP TABLE audit_history(kind TEXT,key TEXT,value TEXT,event_id INTEGER,PRIMARY KEY(kind,key))")
            conn.execute("CREATE TEMP TABLE audit_packets(hash TEXT PRIMARY KEY,paper_id TEXT)")

            def history(kind, key):
                row = conn.execute("SELECT value FROM audit_history WHERE kind=? AND key=?", (kind, key)).fetchone()
                return json.loads(row[0]) if row else None

            for row in conn.execute("SELECT * FROM events ORDER BY id"):
                try:
                    payload = json.loads(row["payload"])
                    require(isinstance(payload, dict), "Audit event payload must be an object")
                    kind = row["kind"]
                    key, value = None, None
                    if kind in {"job_enqueued", "job_completed", "agent_submission", "model_receipt"}:
                        key, value = payload["job_id"], payload
                    elif kind == "job_retry_authorized":
                        key, value = payload["parent_id"], payload
                    elif kind == "paper_updated":
                        require(str(payload.get("reason", "")).strip(), "Paper update lacks a reason")
                        if "human_decision" in payload.get("changes", {}):
                            key, value, kind = payload["paper_id"], payload, "human_decision"
                    elif kind == "control_updated" and payload.get("key", "").startswith("native-assessment:"):
                        key, value = payload["key"], payload
                    if key is not None:
                        conn.execute("INSERT OR REPLACE INTO audit_history VALUES(?,?,?,?)", (kind, key, canonical(value), row["id"]))
                    checked("events")
                except (ValueError, KeyError, TypeError, AttributeError, IndexError) as exc:
                    error("event_record", row["id"], exc)

            for kind, table, prefix in (("paper", "papers", "P"), ("job", "jobs", "J"), ("reservation", "reservations", "B")):
                maximum = conn.execute("SELECT coalesce(max(cast(substr(id,2) AS INTEGER)),0) FROM " + table).fetchone()[0]
                counter = conn.execute("SELECT next_value FROM counters WHERE kind=?", (kind,)).fetchone()
                if maximum and (not counter or counter[0] <= maximum):
                    error("identifier_counter", kind, "Next identifier does not exceed all durable IDs")
                for row in conn.execute("SELECT id FROM " + table):
                    if not re.fullmatch(prefix + r"\d{6,}", row[0]):
                        error("identifier_format", row[0], "Unexpected durable identifier format")
                checked("identifier_counters")

            for row in conn.execute("SELECT * FROM jobs ORDER BY id"):
                jid = row["id"]
                try:
                    payload = json.loads(row["payload"])
                    result = json.loads(row["result"]) if row["result"] is not None else None
                    published = history("job_enqueued", jid)
                    require(published is not None and published.get("payload_sha256") == digest(payload), "Job payload no longer matches its publication history")
                    require(published.get("stage") == row["stage"] and published.get("key") == row["key"], "Job stage/key differ from their immutable publication")
                    if row["state"] != "complete":
                        require(result is None, "Uncompleted job cannot publish an assessment result")
                        checked("unassessed_jobs")
                    else:
                        completed = history("job_completed", jid)
                        require(completed is not None and completed.get("result") == result, "Completed result differs from its durable decision event")
                    stage = row["stage"]
                    if stage in {"title", "abstract", "rescue", "audit"}:
                        records = payload["source_records"]
                        require(digest(records) == payload["source_sha256"], "Semantic metadata snapshot hash mismatch")
                        require([paper["paper_id"] for paper in records] == payload["paper_ids"], "Semantic snapshot paper IDs differ from job membership")
                        for paper in records:
                            require(not set(paper) - SCREEN_FIELDS, "Semantic source contains prior decisions or operational fields")
                            require(stage != "title" or "abstract" not in paper, "Title-only stage contains abstract evidence")
                            require(conn.execute("SELECT 1 FROM papers WHERE id=?", (paper["paper_id"],)).fetchone() is not None, "Semantic source references unknown paper")
                        source = {"papers": records}
                        prompt, schema = screening.prepare(stage, records)
                    elif stage == "reader":
                        source = load(payload["packet_path"])
                        expected = payload.get("packet_sha256") or Path(payload["packet_path"]).name.split(".", 1)[0]
                        require(digest(source) == expected, "Reader packet differs from job source binding")
                        packet_valid(source)
                        require(source.get("paper_id", source.get("paper", {}).get("paper_id")) == payload["paper_id"], "Reader packet belongs to another paper")
                        conn.execute("INSERT OR IGNORE INTO audit_packets VALUES(?,?)", (expected, payload["paper_id"]))
                        prompt, schema = reading.prepare(source)
                    elif stage == "retrieval" and row["state"] == "complete":
                        if result["status"] == "verified":
                            packet_valid(result["packet"])
                            for asset in result["assets"]:
                                asset_valid(asset)
                            require([{k: v for k, v in a.items() if k not in {"original_path", "text_path", "map_path"}} for a in result["assets"]] == result["packet"]["sources"], "Retrieval assets differ from packet evidence")
                        else:
                            require(not result.get("packet"), "Unverified retrieval must not supply a ready reader packet")
                    elif stage == "search" and row["state"] == "complete" and result["retrieval_status"] == "complete":
                        hash_file(result["snapshot_path"], result["snapshot_sha256"])
                        snapshot = sources.load_snapshot(local(result["snapshot_path"]))
                        request = snapshot["request"]
                        for key in ("source", "query", "limit", "cursor", "kind", "parent"):
                            expected = payload.get(key)
                            if key == "query":
                                expected = expected or ""
                            elif key == "limit":
                                expected = expected or 100
                            require(request.get(key) == expected, "Search snapshot request differs from queued window: " + key)
                        checked("search_snapshots")
                    if stage in MODEL_STAGES and row["state"] == "complete":
                        directory = root / "jobs" / jid
                        require(load(directory / "source.json") == source, "Captured model source differs from queued evidence")
                        require((directory / "prompt.txt").read_text(encoding="utf-8") == prompt, "Model prompt differs from the deployed scientific instructions and source")
                        require(load(directory / "schema.json") == schema, "Model schema differs from the bound source schema")
                        task = load(directory / "task.json")
                        require(task["job_id"] == jid and task["stage"] == stage, "Prepared task identity mismatch")
                        require(task["source"] == source and task["source_sha256"] == digest(source), "Prepared task source mismatch")
                        require(task["prompt_sha256"] == hashlib.sha256(prompt.encode()).hexdigest() and task["schema_sha256"] == digest(schema), "Prepared task hash mismatch")
                        require(str(result.get("actor", "")).strip(), "Completed model result lacks an actor")
                        assessment = result["assessment"]
                        if stage == "reader":
                            reading.validate(assessment, source)
                        else:
                            screening.validate(assessment, stage, source["papers"])
                        if result.get("receipt"):
                            execution = local(result["receipt"])
                            receipt, binding = load(execution / "receipt.json"), load(execution / "binding.json")
                            require(receipt.get("status") == "completed" and receipt.get("result") == assessment, "Completed job does not match provider receipt")
                            hash_file(execution / "result.json", receipt["result_sha256"])
                            require(load(execution / "result.json") == assessment, "Provider result file differs from scientific assessment")
                            hash_file(execution / "binding.json", receipt["binding_sha256"])
                            require(binding["prompt_sha256"] == hashlib.sha256(prompt.encode()).hexdigest(), "Provider prompt binding mismatch")
                            require(binding["schema_sha256"] == sources.digest(schema), "Provider source-bound schema mismatch")
                            if binding.get("base_instructions_sha256") is not None:
                                require(binding["base_instructions_sha256"] == receipt.get("base_instructions_sha256"), "Provider context binding differs from receipt")
                                hash_file(execution / "base_instructions.txt", binding["base_instructions_sha256"])
                            event = history("model_receipt", jid)
                            recorded_receipt = event.get("receipt") if event is not None else None
                            # Cache recovery adds only an execution annotation;
                            # the completed receipt file remains immutable.
                            require(isinstance(recorded_receipt, dict) and
                                    {k: v for k, v in recorded_receipt.items() if k != "recovered"} ==
                                    {k: v for k, v in receipt.items() if k != "recovered"},
                                    "Provider receipt differs from durable execution history")
                        else:
                            submitted = history("agent_submission", jid)
                            require(submitted is not None and submitted.get("result_sha256") == digest(assessment), "External agent result has no matching submission history")
                            require(submitted.get("actor") == result["actor"], "External agent attribution differs from submission history")
                            saved = directory / ("submitted_result-" + str(row["token"]) + ".json")
                            require(load(saved) == assessment, "External agent result differs from its saved submission")
                        checked("completed_model_results")
                    checked("jobs")
                except (ValueError, KeyError, TypeError, AttributeError, IndexError, OSError, AssertionError, ValidationError, SchemaError) as exc:
                    error("job_binding", jid, exc)

            for row in conn.execute("SELECT id,status,record FROM papers ORDER BY id"):
                pid = row["id"]
                try:
                    paper = json.loads(row["record"])
                    require(paper.get("paper_id") == pid and paper.get("status") == row["status"], "Paper record identity/status differs from indexed state")
                    for entry in paper.get("provided_paths", []):
                        if isinstance(entry, dict) and entry.get("expected_sha256"):
                            hash_file(entry["path"], entry["expected_sha256"])
                    if paper.get("assessment") is not None or paper["status"] in {"assessed", "reading-incomplete"}:
                        saved = conn.execute("SELECT stage,state,payload,result FROM jobs WHERE id=?", (paper.get("reader_job"),)).fetchone()
                        require(saved is not None and saved["stage"] == "reader" and saved["state"] == "complete", "Current assessment lacks a completed reader job")
                        require(json.loads(saved["payload"])["paper_id"] == pid, "Assessment reader job belongs to another paper")
                        require(json.loads(saved["result"])["assessment"] == paper.get("assessment"), "Current assessment differs from its reader result")
                    for stage, decision in paper.get("screening", {}).items():
                        saved = conn.execute("SELECT stage,state,result FROM jobs WHERE id=?", (decision.get("job_id"),)).fetchone()
                        require(saved is not None and saved["state"] == "complete" and saved["stage"] == stage, "Current screening lacks a completed source-specific job")
                        matches = [d for d in json.loads(saved["result"])["assessment"]["decisions"] if d["paper_id"] == pid]
                        require(len(matches) == 1 and matches[0] == decision.get("decision"), "Current screening differs from its durable job result")
                    if "human_decision" in paper:
                        event = history("human_decision", pid)
                        require(event is not None and event.get("actor") == "human-explicit" and event.get("changes", {}).get("human_decision") == paper["human_decision"], "Human disposition lacks an explicit attributed history event")
                    checked("papers")
                except (ValueError, KeyError, TypeError, AttributeError, IndexError, OSError) as exc:
                    error("paper_binding", pid, exc)

            for row in conn.execute("SELECT key,value FROM meta WHERE key LIKE 'state:intake-source:%' OR key LIKE 'state:native-assessment:%' ORDER BY key"):
                try:
                    value = json.loads(row["value"])
                    if row["key"].startswith("state:intake-source:"):
                        hash_file(value["snapshot"], value["normalized_sha256"])
                        checked("intake_snapshots")
                    else:
                        require(str(value.get("actor", "")).strip() and str(value.get("reason", "")).strip(), "Native discovery judgment lacks actor/reason")
                        event = history("control_updated", row["key"][len("state:"):])
                        require(event is not None and event.get("value") == value, "Native discovery judgment differs from its explicit submission history")
                        pid = row["key"].split("state:native-assessment:", 1)[1]
                        require(conn.execute("SELECT 1 FROM audit_packets WHERE hash=? AND paper_id=?", (value["packet_sha256"], pid)).fetchone() is not None, "Native discovery judgment is not bound to a supplied reader packet")
                        checked("native_source_bindings")
                except (ValueError, KeyError, TypeError, AttributeError, IndexError, OSError) as exc:
                    error("control_binding", row["key"], exc)

            from .recovery import validate_retries
            validate_retries(coordinator, conn, error, checked, history)

            totals = {"calls": 0.0, "tokens": 0.0, "cost_usd": 0.0, "unknown_outcomes": 0}
            for row in conn.execute("SELECT * FROM reservations ORDER BY id"):
                try:
                    if row["state"] != "released":
                        usage = json.loads(row["usage"] if row["state"] == "settled" else row["estimate"])
                        for key in ("calls", "tokens", "cost_usd"):
                            require(isinstance(usage[key], (int, float)) and math.isfinite(usage[key]) and usage[key] >= 0, "Budget amount is invalid")
                            totals[key] += usage[key]
                        totals["unknown_outcomes"] += row["state"] == "unknown"
                    checked("budget_reservations")
                except (ValueError, KeyError, TypeError, AttributeError, IndexError) as exc:
                    error("budget_reservation", row["id"], exc)
            aggregate = dict(conn.execute("SELECT calls,tokens,cost_usd,unknown_outcomes FROM budget_totals WHERE id=1").fetchone())
            for key, total in totals.items():
                if not math.isclose(total, aggregate[key], rel_tol=1e-9, abs_tol=1e-9):
                    error("budget_aggregate", key, "Durable aggregate differs from all reservations")
            checked("budget_aggregate")
    except (sqlite3.Error, ValueError, KeyError, TypeError, AttributeError, IndexError, OSError) as exc:
        error("validation_snapshot", "database", exc)

    report = {"ok": error_count == 0, "errors": errors, "error_count": error_count, "checks": checks,
              "scope": "operational-not-native-scientific", "snapshot_event_id": snapshot_event_id,
              "elapsed_seconds": round(time.time() - started, 3), "native_scientific_certification": False,
              "limitations": ["Schema/source integrity does not establish scientific correctness or discovery stopping.",
                              "A valid failed/unstarted job remains scientifically unassessed."]}
    with store._transaction() as conn:
        current = conn.execute("SELECT coalesce(max(id),0) FROM events").fetchone()[0]
        if current != snapshot_event_id:
            error("concurrent_change", "database", "Run changed during validation; repeat at a quiet checkpoint")
            report.update(ok=False, error_count=error_count)
        report["validation_event_id"] = store._event(conn, "operational_validation", {
            "ok": report["ok"], "snapshot_event_id": snapshot_event_id, "error_count": error_count,
            "scope": report["scope"], "reason": "Checked durable state, source hashes and recorded output provenance; no native scientific certification"})
    save_json(root / "delivery" / "validation.json", report)
    return report
