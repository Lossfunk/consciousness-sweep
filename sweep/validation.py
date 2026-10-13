"""Read-only operational audit, apart from its explicit report and audit event.

This checks storage, immutable evidence and recorded decisions. It neither judges
scientific eligibility nor certifies a frozen native registered run. Run at a
quiet checkpoint; concurrent changes make the resulting report stale.
"""
import hashlib
from datetime import datetime
import json
import math
from pathlib import Path
import re
import sqlite3
import time
from jsonschema.exceptions import ValidationError, SchemaError

from . import reading, screening, sources
from .common import canonical, digest, file_hash, save_json
from .store import StoreError

MODEL_STAGES = {"title", "abstract", "rescue", "audit", "reader"}
SCREEN_FIELDS = {"paper_id", "title", "year", "authors", "doi", "abstract"}
NONMATERIAL_EVENTS = ("operational_validation", "delivery_checkpoint", "throughput_estimate", "execution_session_finished", "operational_sanity")


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
            placeholders = ",".join("?" for _ in NONMATERIAL_EVENTS)
            row = conn.execute("SELECT id FROM events WHERE kind NOT IN (" + placeholders + ") ORDER BY id DESC LIMIT 1", NONMATERIAL_EVENTS).fetchone()
        return (row[0] if row else 0) <= snapshot
    except (OSError, ValueError, TypeError, AttributeError, sqlite3.Error):
        return False


def require_integrity(coordinator):
    """A failed check stays binding until a successful explicit quiet audit."""
    with coordinator.store._connection() as conn:
        row = conn.execute("SELECT payload FROM events WHERE kind='operational_validation' ORDER BY id DESC LIMIT 1").fetchone()
    failed = row is not None and json.loads(row[0]).get("ok") is False
    path = Path(coordinator.run_dir) / "delivery" / "validation.json"
    if path.exists():
        report = json.loads(path.read_text())
        failed = failed or (report.get("ok") is False and not report.get("incomplete"))
    if failed:
        raise ValueError("Operational integrity check failed. Repair the recorded errors and run validate before execution or delivery; previous delivery is preserved.")
    with coordinator.store._connection() as conn:
        latest_sanity = conn.execute("SELECT payload FROM events WHERE kind='operational_sanity' ORDER BY id DESC LIMIT 1").fetchone()
    if latest_sanity and json.loads(latest_sanity[0]).get("ok") is False:
        raise ValueError("Lightweight record check failed. Repair delivery/sanity.json findings and rerun sanity before admitting work or delivering results.")


def _validate_retrieval_accounting(conn, error, checked):
    """Reconcile operational retry/cursor state with its append-first history.

    Legacy jobs may have no accounting records. A started acquisition without a
    receipt is an honest interrupted/in-flight attempt, not a fabricated failure.
    The disk-backed index keeps this full audit bounded in Python memory.
    """
    def require(value, message):
        if not value:
            raise ValueError(message)

    def positive(value):
        return type(value) is int and value > 0

    def timestamp(value):
        return type(value) in (int, float) and math.isfinite(value) and value >= 0

    tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('retrieval_service','retrieval_attempts')")}
    conn.execute("CREATE TEMP TABLE audit_retrieval_claims(job_id TEXT,token INTEGER,owner TEXT,event_id INTEGER,sequence INTEGER,lane TEXT,PRIMARY KEY(job_id,token))")
    conn.execute("CREATE TEMP TABLE audit_retrieval_events(kind TEXT,job_id TEXT,number INTEGER,payload TEXT,event_id INTEGER,PRIMARY KEY(kind,job_id,number))")
    conn.execute("CREATE INDEX audit_retrieval_claim_job ON audit_retrieval_claims(job_id,sequence)")
    lanes = ("priority", "local", "fresh", "retry", "other-stage")
    sequence, next_lane = 0, 0
    for row in conn.execute("SELECT id,kind,payload FROM events WHERE kind IN ('job_claimed','retrieval_attempt_started','retrieval_attempt_finished') ORDER BY id"):
        try:
            payload = json.loads(row["payload"])
            jid, token = payload["job_id"], payload["token"]
            require(positive(token) and isinstance(payload.get("owner"), str) and payload["owner"].strip(), "Retrieval history lacks its worker/lease binding")
            job = conn.execute("SELECT stage,token FROM jobs WHERE id=?", (jid,)).fetchone()
            require(job is not None and token <= job["token"], "Retrieval history references an unknown job or future lease")
            if row["kind"] == "job_claimed":
                service = "service_sequence" in payload or "service_lane" in payload
                if service:
                    require(payload.get("service_sequence") == sequence + 1 and positive(payload.get("service_sequence")), "Retrieval service sequence is not contiguous in claim history")
                    lane = payload.get("service_lane")
                    require(lane in lanes, "Unknown retrieval service lane")
                    require(lane == "priority" or (job["stage"] != "retrieval" if lane == "other-stage" else job["stage"] == "retrieval"), "Retrieval service lane does not match job stage")
                    sequence, next_lane = payload["service_sequence"], (lanes.index(lane) + 1) % len(lanes)
                conn.execute("INSERT INTO audit_retrieval_claims VALUES(?,?,?,?,?,?)", (jid, token, payload["owner"], row["id"], payload.get("service_sequence"), payload.get("service_lane")))
            else:
                require(job["stage"] == "retrieval" and positive(payload.get("attempt")), "Acquisition event is not a numbered retrieval attempt")
                conn.execute("INSERT INTO audit_retrieval_events VALUES(?,?,?,?,?)", (row["kind"], jid, payload["attempt"], canonical(payload), row["id"]))
            checked("retrieval_accounting_events")
        except (ValueError, KeyError, TypeError, AttributeError, sqlite3.IntegrityError) as exc:
            error("retrieval_accounting_history", row["id"], exc)

    saved = conn.execute("SELECT value FROM meta WHERE key='retrieval_schedule'").fetchone()
    try:
        cursor = json.loads(saved[0]) if saved is not None else None
        require((cursor is None and sequence == 0) or (isinstance(cursor, dict)
                and type(cursor.get("sequence")) is int and type(cursor.get("next_lane")) is int
                and cursor == {"sequence": sequence, "next_lane": next_lane}), "Retrieval service cursor differs from durable claim history")
        checked("retrieval_service_cursor")
    except (ValueError, TypeError) as exc:
        error("retrieval_service_cursor", "retrieval_schedule", exc)

    expected_services = "SELECT c.job_id,max(c.sequence) AS last_sequence,count(*) AS claims FROM audit_retrieval_claims c JOIN jobs j ON j.id=c.job_id WHERE j.stage='retrieval' AND c.sequence IS NOT NULL GROUP BY c.job_id"
    if "retrieval_service" not in tables:
        if conn.execute("SELECT 1 FROM (" + expected_services + ") LIMIT 1").fetchone():
            error("retrieval_service", "table", "Recorded retrieval service has no durable service table")
    else:
        conn.execute("CREATE TEMP TABLE audit_retrieval_service AS " + expected_services)
        conn.execute("CREATE UNIQUE INDEX audit_retrieval_service_job ON audit_retrieval_service(job_id)")
        for row in conn.execute("SELECT s.*,j.stage,e.last_sequence AS expected_sequence,e.claims AS expected_claims FROM retrieval_service s LEFT JOIN jobs j ON j.id=s.job_id LEFT JOIN audit_retrieval_service e ON e.job_id=s.job_id"):
            try:
                require(row["stage"] == "retrieval" and positive(row["last_sequence"]) and positive(row["claims"]), "Service accounting does not identify a retrieval job and positive counts")
                require(row["last_sequence"] == row["expected_sequence"] and row["claims"] == row["expected_claims"], "Retrieval service counters differ from claim history")
                checked("retrieval_service_records")
            except (ValueError, TypeError) as exc:
                error("retrieval_service", row["job_id"], exc)
        for row in conn.execute("SELECT e.job_id FROM audit_retrieval_service e LEFT JOIN retrieval_service s ON s.job_id=e.job_id WHERE s.job_id IS NULL"):
            error("retrieval_service", row[0], "Recorded retrieval claims are missing their service accounting")

    if "retrieval_attempts" not in tables:
        if conn.execute("SELECT 1 FROM audit_retrieval_events LIMIT 1").fetchone():
            error("retrieval_attempt", "table", "Recorded acquisition attempts have no durable attempt table")
        return

    def event(kind, jid, number):
        row = conn.execute("SELECT payload,event_id FROM audit_retrieval_events WHERE kind=? AND job_id=? AND number=?", (kind, jid, number)).fetchone()
        return (json.loads(row[0]), row[1]) if row else (None, None)

    def retry_state_valid(result, payload):
        state = result.get("retry_state")
        if state is None:
            return  # Historical/fixture receipts did not publish endpoint state.
        require(isinstance(state, dict) and type(state.get("version")) is int and state["version"] == 1, "Unknown retrieval endpoint-state version")
        require(state.get("source_generation") == payload.get("source_generation", 1), "Endpoint history belongs to another source generation")
        if "source_manifest" in payload:
            require(state.get("source_manifest_sha256") == payload.get("source_manifest_sha256")
                    == digest(payload["source_manifest"]), "Endpoint history belongs to another immutable source manifest")
        require(isinstance(state.get("endpoints"), dict), "Endpoint history must be a keyed object")
        for key, entry in state["endpoints"].items():
            require(isinstance(entry, dict) and entry.get("kind") in {"article", "identity-discovery"} and isinstance(entry.get("source"), str) and entry["source"], "Malformed retrieval endpoint identity")
            require(key == sources.digest([entry["kind"], entry["source"]]), "Endpoint key differs from its source identity")
            require(isinstance(entry.get("outcome"), dict) and entry.get("outcome_sha256") == sources.digest(entry["outcome"]), "Retained retrieval endpoint outcome hash mismatch")
            require(entry.get("status") == entry["outcome"].get("status") and isinstance(entry.get("status"), str) and entry["status"], "Endpoint status differs from its outcome")
            require(positive(entry.get("acquisitions")) and type(entry.get("transient_failures")) is int and 0 <= entry["transient_failures"] <= entry["acquisitions"], "Malformed retrieval endpoint acquisition counts")
            require((entry["transient_failures"] > 0) == (entry["status"] == "deferred"), "Endpoint transient-failure count disagrees with current outcome")
            attempted, retry = (datetime.fromisoformat(entry[name]) for name in ("attempted_at", "retry_at"))
            require(attempted.tzinfo is not None and retry.tzinfo is not None and retry >= attempted, "Endpoint cooldown must have ordered timezone-aware timestamps")
            checked("retrieval_endpoint_outcomes")

    previous_job, previous_number = None, 0
    for row in conn.execute("SELECT a.*,j.stage,j.payload AS job_payload,j.attempts AS model_attempts FROM retrieval_attempts a LEFT JOIN jobs j ON j.id=a.job_id ORDER BY a.job_id,a.number"):
        jid, number = row["job_id"], row["number"]
        try:
            if jid != previous_job:
                previous_job, previous_number = jid, 0
            require(positive(number) and number == previous_number + 1, "Retrieval attempt numbers are not contiguous")
            previous_number = number
            require(row["stage"] == "retrieval" and row["model_attempts"] == 0, "Retrieval accounting must not become charged model attempts")
            require(timestamp(row["started_at"]), "Retrieval attempt lacks a valid start time")
            started, start_id = event("retrieval_attempt_started", jid, number)
            finished, finish_id = event("retrieval_attempt_finished", jid, number)
            claim = conn.execute("SELECT owner,event_id FROM audit_retrieval_claims WHERE job_id=? AND token=?", (jid, row["token"])).fetchone()
            require(started is not None and claim is not None and claim["owner"] == row["owner"] and claim["event_id"] < start_id, "Retrieval attempt lacks its earlier matching claim/start event")
            payload = json.loads(row["job_payload"])
            require(all(started.get(key) == expected for key, expected in {"job_id": jid, "owner": row["owner"], "token": row["token"], "attempt": number, "source_generation": payload.get("source_generation"), "source_manifest_sha256": payload.get("source_manifest_sha256")}.items()), "Retrieval attempt start differs from immutable job/lease binding")
            if "source_manifest" in payload:
                require(digest(payload["source_manifest"]) == payload.get("source_manifest_sha256"), "Acquisition manifest differs from immutable job hash")
                require(payload["source_manifest"].get("paper_id") == payload.get("paper_id"), "Acquisition manifest belongs to another paper")
            if row["result"] is None:
                require(row["completed_at"] is None and finished is None, "Receipt-less retrieval attempt has a completion timestamp or finished event")
                checked("retrieval_attempts_without_receipt")
            else:
                result = json.loads(row["result"])
                require(isinstance(result, dict) and isinstance(result.get("status"), str) and result["status"], "Retrieval receipt lacks a status")
                require(timestamp(row["completed_at"]) and finished is not None and finish_id > start_id, "Retrieval receipt lacks a later finish event/time")
                require(all(finished.get(key) == expected for key, expected in {"job_id": jid, "owner": row["owner"], "token": row["token"], "attempt": number, "result": result}.items()), "Retrieval receipt differs from append-first finish history")
                retry_state_valid(result, payload)
                checked("retrieval_attempt_receipts")
            checked("retrieval_attempt_records")
        except (ValueError, KeyError, TypeError, AttributeError, OverflowError) as exc:
            error("retrieval_attempt", jid + ":" + str(number), exc)
    for row in conn.execute("SELECT e.kind,e.job_id,e.number FROM audit_retrieval_events e LEFT JOIN retrieval_attempts a ON a.job_id=e.job_id AND a.number=e.number WHERE a.id IS NULL"):
        error("retrieval_attempt", row["job_id"] + ":" + str(row["number"]), "Acquisition history is missing its durable attempt record: " + row["kind"])


def validate(coordinator, *, deadline=None):
    root, store = Path(coordinator.run_dir).resolve(), coordinator.store
    errors, checks, error_count = [], {}, 0
    started = time.time()

    def deadline_check():
        if deadline is not None and time.monotonic() >= deadline:
            raise TimeoutError("Checkpoint deadline reached; validation remains incomplete")

    def checked(name, amount=1):
        deadline_check()
        checks[name] = checks.get(name, 0) + amount

    def error(code, entity, reason):
        deadline_check()
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
        hasher = hashlib.sha256()
        with local(path).open("rb") as stream:
            while True:
                deadline_check()
                block = stream.read(1024 * 1024)
                if not block:
                    break
                hasher.update(block)
        require(hasher.hexdigest() == expected, "Stored file no longer matches its immutable hash")
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
        require(local(asset["text_path"]).read_bytes().decode("utf-8") == asset["content"], "Extracted text differs from reader asset content")
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
            conn.set_progress_handler(lambda: int(deadline is not None and time.monotonic() >= deadline), 10000)
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
                    if kind in {"job_enqueued", "job_completed", "agent_submission", "model_receipt", "job_superseded"}:
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

            for issue in coordinator.store.native_id_errors(conn):
                error("native_identifier_registry", "native", issue)
            checked("native_identifier_registry")

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
                        if "source_manifest" in payload:
                            require(digest(payload["source_manifest"]) == payload.get("source_manifest_sha256"), "Acquisition manifest differs from immutable job hash")
                            require(payload["source_manifest"].get("paper_id") == payload["paper_id"], "Acquisition manifest belongs to another paper")
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
                            required_provenance = bool(payload.get("calibration_review"))
                            if required_provenance or "execution_provenance" in result or "execution_verification" in result:
                                from .coordinator import execution_task_context, validate_execution_provenance
                                job = {"stage": stage, "payload": payload}
                                profile = coordinator.profile_for_job(job)
                                context = execution_task_context(job, profile)
                                require(all(task.get(key) == value for key, value in context.items()),
                                        "External agent task execution context differs from its intended profile")
                                execution = {key: result.get(key) for key in ("execution_provenance", "execution_verification")}
                                require(load(directory / ("submitted_execution-" + str(row["token"]) + ".json")) == execution,
                                        "External agent execution provenance differs from its saved submission")
                                require(submitted.get("execution_sha256") == digest(execution),
                                        "External agent execution provenance has no matching submission history")
                                expected_verification = validate_execution_provenance(
                                    profile, execution["execution_provenance"], required=required_provenance)
                                require(execution["execution_verification"] == expected_verification,
                                        "External agent verification differs from its reported execution provenance")
                        checked("completed_model_results")
                    checked("jobs")
                except (ValueError, KeyError, TypeError, AttributeError, IndexError, OSError, AssertionError, ValidationError, SchemaError) as exc:
                    error("job_binding", jid, exc)

            has_exclusion_index = conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='screening_exclusions'").fetchone() is not None
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
                        reader_payload = json.loads(saved["payload"])
                        require(reader_payload["paper_id"] == pid, "Assessment reader job belongs to another paper")
                        require(reader_payload.get("packet_path") == paper.get("packet_path"), "Current assessment belongs to a superseded source packet")
                        require(reader_payload.get("source_generation", 0) == paper.get("source_generation", 0), "Current assessment belongs to a superseded source generation")
                        require(paper.get("assessment_packet_sha256") == reader_payload.get("packet_sha256"), "Current assessment packet hash binding is missing or stale")
                        require(paper.get("assessment_source_generation") == paper.get("source_generation", 0), "Current assessment generation binding is missing or stale")
                        require(json.loads(saved["result"])["assessment"] == paper.get("assessment"), "Current assessment differs from its reader result")
                    for stage, decision in paper.get("screening", {}).items():
                        saved = conn.execute("SELECT stage,state,result FROM jobs WHERE id=?", (decision.get("job_id"),)).fetchone()
                        require(saved is not None and saved["state"] == "complete" and saved["stage"] == stage, "Current screening lacks a completed source-specific job")
                        matches = [d for d in json.loads(saved["result"])["assessment"]["decisions"] if d["paper_id"] == pid]
                        require(len(matches) == 1 and matches[0] == decision.get("decision"), "Current screening differs from its durable job result")
                    latest = paper.get("screening_current", {})
                    active_exclusion = (latest.get("decision") == "exclude" and latest.get("stage") != "rescue"
                                        and paper["status"] in {"title-excluded", "abstract-excluded"})
                    cached = conn.execute("SELECT * FROM screening_exclusions WHERE paper_id=?", (pid,)).fetchone() if has_exclusion_index else None
                    require(bool(cached) == active_exclusion, "Current-exclusion audit index omits an exclusion or retains a superseded one")
                    if cached:
                        binding = latest.get("audit_binding_sha256", latest["source_sha256"])
                        require(cached["job_id"] == latest["job_id"] and cached["cohort"] == latest["cohort"] and cached["binding"] == binding,
                                "Current-exclusion cache differs from current source-bound screening")
                        require(cached["rank"] == digest([coordinator.plan.get("audit_seed", "portable-v1"), latest["cohort"], pid, binding]), "Audit sampling rank differs from its deterministic source binding")
                        require(cached["reviewed"] == int(latest["stage"] == "audit"), "Audit completion differs from actual source review")
                        if cached["scheduled_job"]:
                            audit_job = conn.execute("SELECT stage,payload FROM jobs WHERE id=?", (cached["scheduled_job"],)).fetchone()
                            require(audit_job is not None and audit_job["stage"] == "audit" and pid in json.loads(audit_job["payload"])["paper_ids"], "Exclusion audit reservation has no corresponding job")
                    if "human_decision" in paper:
                        require(isinstance(paper["human_decision"], str) and paper["human_decision"] in {"accepted-support", "accepted-primary", "declined", "pending"}, "Human disposition must be a supported CLI decision string")
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
                        coordinator.store.require_native_ids(pid, value["groups"],
                            [a["comparison"] for a in value.get("process_activations", [])], conn=conn)
                        require(conn.execute("SELECT 1 FROM audit_packets WHERE hash=? AND paper_id=?", (value["packet_sha256"], pid)).fetchone() is not None, "Native discovery judgment is not bound to a supplied reader packet")
                        checked("native_source_bindings")
                except (ValueError, KeyError, TypeError, AttributeError, IndexError, OSError, StoreError) as exc:
                    error("control_binding", row["key"], exc)

            from .discovery_validation import validate_discovery
            validate_discovery(coordinator, conn, error, checked)
            from .calibration import validate_records
            for issue in validate_records(coordinator, conn):
                error(issue["code"], issue["entity"], issue["reason"])
            checked("seed_calibration_records")

            for row in conn.execute("SELECT * FROM job_supersessions ORDER BY job_id"):
                try:
                    event = history("job_superseded", row["job_id"])
                    require(event is not None and event.get("replacement_job_id") == row["replacement_job_id"] and event.get("reason") == row["reason"] and str(row["reason"]).strip(), "Job supersession differs from its durable reason/history")
                    require(event.get("scope") == "execution-only; original result, running worker and budget remain unchanged", "Job supersession lacks its execution-only scope")
                    saved = conn.execute("SELECT payload,stage FROM jobs WHERE id=?", (row["job_id"],)).fetchone()
                    require(saved is not None, "Superseded job is missing")
                    if row["replacement_job_id"]:
                        require(row["replacement_job_id"] != row["job_id"] and conn.execute("SELECT 1 FROM jobs WHERE id=?", (row["replacement_job_id"],)).fetchone() is not None, "Supersession replacement is invalid")
                    if saved["stage"] in {"reader", "retrieval"}:
                        payload = json.loads(saved["payload"])
                        current_row = conn.execute("SELECT record FROM papers WHERE id=?", (payload["paper_id"],)).fetchone()
                        require(current_row is not None, "Superseded source job paper is missing")
                        paper = json.loads(current_row[0])
                        changed = payload.get("source_generation", 1) != paper.get("source_generation", 1)
                        changed = changed or (saved["stage"] == "reader" and payload.get("packet_path") != paper.get("packet_path"))
                        changed = changed or (saved["stage"] == "retrieval" and payload.get("source_manifest_sha256") != paper.get("current_source_manifest_sha256"))
                        require(changed, "Superseded source job still has current inputs")
                    checked("job_supersessions")
                except (ValueError, KeyError, TypeError, AttributeError) as exc:
                    error("job_supersession", row["job_id"], exc)

            from .recovery import validate_retries
            validate_retries(coordinator, conn, error, checked, history)
            _validate_retrieval_accounting(conn, error, checked)

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
    except TimeoutError:
        raise
    except (sqlite3.Error, ValueError, KeyError, TypeError, AttributeError, IndexError, OSError) as exc:
        deadline_check()
        error("validation_snapshot", "database", exc)

    deadline_check()
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
