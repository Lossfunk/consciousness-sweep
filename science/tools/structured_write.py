#!/usr/bin/env python3
"""Validate typed records before atomically writing run CSV or JSONL files."""

from __future__ import annotations

import argparse
import csv
import fcntl
import hashlib
import shutil
import threading
import uuid
import json
import os
import re
import tempfile
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import quote, unquote, urlsplit, urlunsplit

try:
    from jsonschema import Draft202012Validator, FormatChecker
except ModuleNotFoundError as exc:
    print(
        f"ERROR: missing repository dependency {exc.name!r}. "
        "Run: python3 tools/bootstrap_env.py --venv .venv",
        file=sys.stderr,
    )
    raise SystemExit(3) from None

from validate_run import load_csv_rows, load_jsonl_rows, allows_null
from execution_contract import group_record_lifecycle_errors


ROOT = Path(__file__).resolve().parents[1]
TABLE_SCHEMAS = {
    "papers_master.csv": "papers.schema.json",
    "experiment_groups.csv": "experiment_groups.schema.json",
    "experiments_master.csv": "experiments.schema.json",
    "search_log.csv": "search_log.schema.json",
    "discoveries.csv": "discoveries.schema.json",
    "missing_texts.csv": "missing_texts.schema.json",
    "auxiliary_sources.csv": "auxiliary_sources.schema.json",
    "evidence_bundles.csv": "evidence_bundles.schema.json",
    "evidence_links.csv": "evidence_links.schema.json",
    "evidence_assessments.csv": "evidence_assessments.schema.json",
    "fulltext_assets.csv": "fulltext_assets.schema.json",
}
PRIMARY_KEYS = {
    "papers_master.csv": "paper_id",
    "experiment_groups.csv": "experiment_id",
    "experiments_master.csv": "comparison_id",
    "search_log.csv": "search_id",
    "discoveries.csv": "discovery_id",
    "missing_texts.csv": "paper_id",
    "auxiliary_sources.csv": "auxiliary_id",
    "evidence_bundles.csv": "evidence_bundle_id",
    "evidence_links.csv": "evidence_link_id",
    "evidence_assessments.csv": "evidence_assessment_id",
    "fulltext_assets.csv": "fulltext_asset_id",
}
ARRAY_FIELDS = {
    "stats_flags", "attempted_sources", "E_diagnostic_source_locations",
    "factorial_component_effects", "evidence_bundle_ids", "required_member_keys",
    "awareness_regime_evidence", "unaware_capacity_regime_keys", "awareness_regime_keys",
    "linked_comparison_ids", "support_roles", "difference_joint_experiment_ids",
    "bridge_depth0_eligible_paper_ids", "pending_bridge_expansion_paper_ids",
    "completed_bridge_expansion_paper_ids",
}
OBJECT_FIELDS = {"source_parameters", "promotion_challenge"}
DOI_PREFIX = re.compile(
    r"^(?:https?://(?:dx\.)?doi\.org/|doi:\s*|doi\.org/)", re.IGNORECASE
)


MAX_BATCH_MUTATIONS = 100
MAX_BATCH_EVENTS = 1000
MAX_ID_RESERVATIONS = 1000
JOURNAL_NAME = ".structured-write.transaction.json"
_LOCKS: dict[tuple[int, str], threading.RLock] = {}
_LOCKS_GUARD = threading.Lock()
_LOCK_DEPTH = threading.local()


def _fsync_directory(directory: Path) -> None:
    descriptor = os.open(directory, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _sha256(path: Path) -> str | None:
    if path.is_symlink():
        raise ValueError(f"refusing symlinked transaction path: {path}")
    if not path.exists():
        return None
    if not path.is_file():
        raise ValueError(f"refusing non-regular transaction path: {path}")
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


@contextmanager
def run_write_lock(directory: Path):
    """Serialize writers and stable readers; recover committed work on entry.

    The process/thread lock makes nested native validate/derive calls reentrant.
    The filesystem flock also serializes independent worker processes.
    """
    directory = directory.resolve()
    directory.mkdir(parents=True, exist_ok=True)
    key = (os.getpid(), str(directory))
    with _LOCKS_GUARD:
        process_lock = _LOCKS.setdefault(key, threading.RLock())
    with process_lock:
        depths = getattr(_LOCK_DEPTH, "depths", {})
        _LOCK_DEPTH.depths = depths
        if depths.get(key, 0):
            depths[key] += 1
            try:
                yield
            finally:
                depths[key] -= 1
            return
        lock_path = directory / ".structured-write.lock"
        with lock_path.open("a+b") as handle:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            depths[key] = 1
            try:
                _recover_transaction(directory)
                yield
            finally:
                depths.pop(key, None)
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def normalize_doi(value: str | None) -> str | None:
    """Return the canonical lower-case DOI without a resolver/prefix wrapper."""
    if value is None:
        return None
    normalized = unquote(value.strip())
    normalized = DOI_PREFIX.sub("", normalized, count=1).strip().lower()
    return normalized or None


def doi_resolver_url(value: str | None) -> str | None:
    """Build an RFC 3986-safe doi.org URL from a raw or normalized DOI."""
    normalized = normalize_doi(value)
    if normalized is None:
        return None
    encoded = quote(normalized, safe="/:@!$&'()*+,;=-._~")
    return f"https://doi.org/{encoded}"


def normalize_url(value: str | None) -> str | None:
    """Return a trimmed, safely encoded HTTP(S) URL or reject it before persistence."""
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError("bibliographic URL must be a string or null")
    stripped = value.strip()
    if not stripped:
        return None
    parts = urlsplit(stripped)
    if parts.scheme.lower() not in {"http", "https"} or not parts.netloc:
        raise ValueError("bibliographic URL must be an absolute HTTP(S) URL")
    path = quote(parts.path, safe="/%:@!$&'()*+,;=-._~")
    query = quote(parts.query, safe="=&?/%:@!$'()*+,;=-._~")
    fragment = quote(parts.fragment, safe="=&?/%:@!$'()*+,;=-._~")
    return urlunsplit((parts.scheme.lower(), parts.netloc, path, query, fragment))


def dry_run_bibliographic_normalization(
    records: Iterable[dict[str, Any]],
) -> list[dict[str, str | None]]:
    """Normalize DOI/URL fields without allocating IDs or mutating run files."""
    normalized: list[dict[str, str | None]] = []
    for index, record in enumerate(records, start=1):
        if not isinstance(record, dict):
            raise ValueError(f"bibliographic record {index} is not an object")
        doi = normalize_doi(record.get("doi"))
        url = normalize_url(record.get("url"))
        normalized.append({"doi": doi, "url": url, "doi_resolver_url": doi_resolver_url(doi)})
    return normalized


def load_schema(root: Path, name: str) -> dict[str, Any]:
    schema = json.loads((root / "schemas" / name).read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return schema


def validate_record(record: dict[str, Any], schema: dict[str, Any]) -> None:
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(record)


def canonical_csv_record(record: dict[str, Any], schema: dict[str, Any]) -> dict[str, Any]:
    """Represent schema-valid optional omissions in the complete CSV header.

    Absence of an optional inventory is an empty inventory, never a fabricated
    assessment. Required fields and conditional scientific requirements are
    validated before canonicalization. Nonrepresentable omissions fail clearly.
    """
    validate_record(record, schema)
    result = dict(record)
    for field, prop in schema["properties"].items():
        if field in result:
            continue
        if allows_null(prop, schema):
            result[field] = None
        elif prop.get("type") == "object":
            result[field] = {}
        elif prop.get("type") == "array":
            result[field] = []
        else:
            raise ValueError(f"optional CSV field {field!r} needs an explicit schema-valid value")
    validate_record(result, schema)
    return result


def encode_cell(field: str, value: Any) -> str:
    if value is None:
        return ""
    if field in ARRAY_FIELDS or field in OBJECT_FIELDS:
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _atomic_write_csv(path: Path, headers: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=headers, lineterminator="\n")
            writer.writeheader()
            for row in rows:
                writer.writerow({field: encode_cell(field, row[field]) for field in headers})
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(path)
        _fsync_directory(path.parent)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def _atomic_write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=True, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(path)
        _fsync_directory(path.parent)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def _atomic_write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            for row in rows:
                handle.write(json.dumps(row, ensure_ascii=True, separators=(",", ":")) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(path)
        _fsync_directory(path.parent)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def write_csv_record(
    path: Path,
    schema: dict[str, Any],
    record: dict[str, Any],
    *,
    key_field: str | None = None,
) -> None:
    """Append, or key-upsert, only after the existing table and new row validate."""
    record = canonical_csv_record(record, schema)
    with run_write_lock(path.parent):
        errors: list[str] = []
        existing = load_csv_rows(path, schema, errors)
        if errors:
            raise ValueError("existing table is invalid; refusing mutation: " + "; ".join(errors))
        if key_field is None:
            primary_key = PRIMARY_KEYS.get(path.name)
            if primary_key and any(row[primary_key] == record[primary_key] for row in existing):
                raise ValueError(f"duplicate {primary_key} {record[primary_key]!r}; refusing append")
            existing.append(record)
        else:
            if key_field not in schema["properties"]:
                raise ValueError(f"unknown key field {key_field!r}")
            matches = [index for index, row in enumerate(existing) if row[key_field] == record[key_field]]
            if len(matches) > 1:
                raise ValueError(f"multiple existing rows have {key_field}={record[key_field]!r}")
            if matches:
                existing[matches[0]] = record
            else:
                existing.append(record)
        _atomic_write_csv(path, list(schema["properties"].keys()), existing)


def append_jsonl_record(path: Path, schema: dict[str, Any], record: dict[str, Any], *, root: Path = ROOT) -> None:
    validate_record(record, schema)
    if record.get("field") == "process_search_activation":
        if path.name != "decision_log.jsonl":
            raise ValueError("process activations belong in the native decision_log.jsonl")
        # These events create durable discovery obligations. Use the same
        # precommit guard as batch writes rather than the generic JSONL path.
        write_batch(path.parent, [], [record], root=root)
        return
    with run_write_lock(path.parent):
        errors: list[str] = []
        existing = load_jsonl_rows(path, schema, errors) if path.exists() else []
        if errors:
            raise ValueError("existing JSONL is invalid; refusing mutation: " + "; ".join(errors))
        decision_ids = {row["decision_id"] for row in existing}
        if record["decision_id"] in decision_ids:
            raise ValueError(f"duplicate decision_id {record['decision_id']!r}; refusing append")
        raw = path.read_bytes() if path.exists() else b""
        if raw and not raw.endswith(b"\n"):
            raise ValueError("existing JSONL lacks final physical LF; refusing mutation")
        contents = raw + (json.dumps(record, ensure_ascii=True, separators=(",", ":")) + "\n").encode("utf-8")
        descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
        temporary = Path(temporary_name)
        try:
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(contents)
                handle.flush()
                os.fsync(handle.fileno())
            temporary.replace(path)
            _fsync_directory(path.parent)
        except Exception:
            temporary.unlink(missing_ok=True)
            raise


ENTITY_TYPES = {
    "papers_master.csv": "paper", "experiment_groups.csv": "experiment",
    "experiments_master.csv": "comparison", "search_log.csv": "search",
    "discoveries.csv": "discovery", "missing_texts.csv": "missing_text",
    "auxiliary_sources.csv": "auxiliary_source", "evidence_bundles.csv": "evidence_bundle",
    "evidence_links.csv": "evidence_link", "evidence_assessments.csv": "evidence_assessment",
    "fulltext_assets.csv": "fulltext_asset",
}
ID_KINDS = {
    "papers_master.csv": "paper", "experiment_groups.csv": "experiment",
    "experiments_master.csv": "comparison", "search_log.csv": "search",
    "discoveries.csv": "discovery", "auxiliary_sources.csv": "auxiliary",
    "evidence_bundles.csv": "evidence_bundle", "evidence_links.csv": "evidence_link",
    "evidence_assessments.csv": "evidence_assessment", "fulltext_assets.csv": "fulltext_asset",
}
SCALAR_KINDS = {
    "paper": ("next_paper_counter", "P", 6),
    "decision": ("next_decision_counter", "_D", 6),
    "search": ("next_search_counter", "_S", 6),
    "discovery": ("next_discovery_counter", "_R", 6),
    "auxiliary": ("next_auxiliary_counter", "_AUX", 6),
    "evidence_link": ("next_evidence_link_counter", "_EL", 6),
    "evidence_bundle": ("next_evidence_bundle_counter", "_EB", 6),
    "evidence_assessment": ("next_evidence_assessment_counter", "_EA", 6),
    "fulltext_asset": ("next_fulltext_asset_counter", "_FT", 6),
}


def _recover_transaction(run_dir: Path) -> None:
    """Roll forward a published transaction, refusing an inconsistent journal.

    Called only while holding the run lock. All paths and hashes are checked
    before any further replacement. Journal publication is the commit point;
    failures after it are recovered, never rolled back or silently discarded.
    """
    journal_path = run_dir / JOURNAL_NAME
    if not journal_path.exists():
        return
    if journal_path.is_symlink():
        raise ValueError("transaction journal must not be a symlink")
    try:
        journal = json.loads(journal_path.read_text(encoding="utf-8"))
        if set(journal) != {"version", "stage", "files"} or journal["version"] != 1:
            raise ValueError("unsupported transaction journal")
        stage_name = journal["stage"]
        if not isinstance(stage_name, str) or not re.fullmatch(r"\.structured-write\.stage\.[0-9a-f]{32}", stage_name):
            raise ValueError("unsafe transaction staging path")
        stage = run_dir / stage_name
        if stage.is_symlink():
            raise ValueError("transaction staging directory must not be a symlink")
        files = journal["files"]
        if not isinstance(files, list) or not files:
            raise ValueError("transaction journal lacks files")
        targets: set[str] = set()
        allowed = {*TABLE_SCHEMAS, "decision_log.jsonl", "run_state.json"}
        if len(files) > len(TABLE_SCHEMAS) + 2 or not isinstance(files[0], dict) or files[0].get("target") != "decision_log.jsonl":
            raise ValueError("transaction must publish decision history first")
        for index, entry in enumerate(files):
            if not isinstance(entry, dict) or set(entry) != {"target", "payload", "before", "after"}:
                raise ValueError("malformed transaction file entry")
            target = entry["target"]
            if target not in allowed or target in targets or entry["payload"] != f"{index:02d}.payload":
                raise ValueError("unsafe or duplicate transaction target")
            if not isinstance(entry["after"], str) or not re.fullmatch(r"[0-9a-f]{64}", entry["after"]):
                raise ValueError("invalid transaction payload hash")
            if entry["before"] is not None and (not isinstance(entry["before"], str) or not re.fullmatch(r"[0-9a-f]{64}", entry["before"])):
                raise ValueError("invalid transaction prior hash")
            targets.add(target)
            current_hash = _sha256(run_dir / target)
            if current_hash not in {entry["before"], entry["after"]}:
                raise ValueError(f"transaction target changed unexpectedly: {target}")
            payload = stage / entry["payload"]
            if current_hash != entry["after"] and _sha256(payload) != entry["after"]:
                raise ValueError(f"transaction payload missing or changed: {target}")
        for entry in files:
            target_path = run_dir / entry["target"]
            if _sha256(target_path) != entry["after"]:
                os.replace(stage / entry["payload"], target_path)
                _fsync_directory(run_dir)
        journal_path.unlink()
        _fsync_directory(run_dir)
        if stage.exists():
            shutil.rmtree(stage, ignore_errors=False)
        _fsync_directory(run_dir)
    except (OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
        raise ValueError(f"committed transaction needs recovery; refusing mutation: {exc}") from exc


def _publish_transaction(run_dir: Path, replacements: list[tuple[str, bytes]]) -> None:
    """Stage, commit, and publish files; history is always the first replacement."""
    stage = run_dir / f".structured-write.stage.{uuid.uuid4().hex}"
    stage.mkdir()
    committed = False
    try:
        entries = []
        for index, (target, contents) in enumerate(replacements):
            payload_name = f"{index:02d}.payload"
            with (stage / payload_name).open("xb") as handle:
                handle.write(contents)
                handle.flush()
                os.fsync(handle.fileno())
            entries.append({
                "target": target, "payload": payload_name,
                "before": _sha256(run_dir / target),
                "after": hashlib.sha256(contents).hexdigest(),
            })
        _fsync_directory(stage)
        _fsync_directory(run_dir)
        _atomic_write_json(run_dir / JOURNAL_NAME, {
            "version": 1, "stage": stage.name, "files": entries,
        })
        committed = True
        _recover_transaction(run_dir)
    finally:
        if not committed and not (run_dir / JOURNAL_NAME).exists():
            shutil.rmtree(stage, ignore_errors=True)


def _reserved_identifier(state: dict[str, Any], kind: str, identifier: str) -> bool:
    if kind in SCALAR_KINDS:
        field, marker, width = SCALAR_KINDS[kind]
        prefix = "" if kind == "paper" else state["run_id"]
        match = re.fullmatch(re.escape(prefix + marker) + rf"([0-9]{{{width}}})", identifier)
        return bool(match and 0 < int(match.group(1)) < state[field])
    marker, field, pattern = (
        ("_E", "next_experiment_counters", r"P[0-9]{6}") if kind == "experiment"
        else ("_C", "next_comparison_counters", r"P[0-9]{6}_E[0-9]{2}")
    )
    match = re.fullmatch(rf"({pattern}){marker}([0-9]{{2}})", identifier)
    return bool(match and 0 < int(match.group(2)) < state[field].get(match.group(1), 1))


def _event_coverage(
    before: dict[str, Any] | None, after: dict[str, Any], events: list[dict[str, Any]],
    schema: dict[str, Any] | None = None,
) -> None:
    for event in events:
        if event["field"] != "record":
            continue
        old, new = event["old_value"], event["new_value"]
        if schema is not None:
            old = canonical_csv_record(old, schema) if isinstance(old, dict) else old
            new = canonical_csv_record(new, schema) if isinstance(new, dict) else new
        if old == before and new == after:
            return
    changed = {field for field, value in after.items() if before is None or before.get(field) != value}
    for field in changed:
        old = before.get(field) if before is not None else None
        if not any(event["field"] == field and event["old_value"] == old
                   and event["new_value"] == after[field] for event in events):
            raise ValueError(f"mutation lacks append-first decision coverage for field {field!r}")


def write_batch(
    run_dir: Path, mutations: list[dict[str, Any]], decisions: list[dict[str, Any]], *,
    root: Path = ROOT, state_updates: dict[str, Any] | None = None,
    state_decision_ids: list[str] | None = None, expected_state: dict[str, Any] | None = None,
) -> dict[str, int]:
    """Commit a bounded typed batch, with CAS and explicit decision coverage.

    A mutation contains table, mode (append/upsert), record, expected_current
    (full current typed row, or null for creation), and decision_ids. IDs are
    reserved separately. Full-row `record` events can document initialization;
    scientific revisions normally use one source-linked event per changed field.
    This is a storage transaction, not scientific validation or completion.
    """
    if not isinstance(mutations, list) or not isinstance(decisions, list):
        raise ValueError("batch mutations and decisions must be arrays")
    if len(mutations) > MAX_BATCH_MUTATIONS or not 1 <= len(decisions) <= MAX_BATCH_EVENTS:
        raise ValueError("batch permits at most 100 mutations and 1..1000 decision events")
    schemas = {name: load_schema(root, TABLE_SCHEMAS[name]) for name in {
        item.get("table") for item in mutations if isinstance(item, dict)
    } if name in TABLE_SCHEMAS}
    decision_schema = load_schema(root, "decision_log.schema.json")
    for event in decisions:
        validate_record(event, decision_schema)
    for mutation in mutations:
        required = {"table", "mode", "record", "expected_current", "decision_ids"}
        if not isinstance(mutation, dict) or set(mutation) != required:
            raise ValueError("mutation requires exactly table, mode, record, expected_current, decision_ids")
        table = mutation["table"]
        if table not in TABLE_SCHEMAS or mutation["mode"] not in {"append", "upsert"}:
            raise ValueError("unknown batch table or mutation mode")
        validate_record(mutation["record"], schemas[table])
        if mutation["expected_current"] is not None:
            validate_record(mutation["expected_current"], schemas[table])
        ids = mutation["decision_ids"]
        if not isinstance(ids, list) or not ids or any(not isinstance(value, str) for value in ids) or len(set(ids)) != len(ids):
            raise ValueError("mutation decision_ids must be a nonempty unique string array")
    mutations = [{**item,
                  "record": canonical_csv_record(item["record"], schemas[item["table"]]),
                  "expected_current": canonical_csv_record(item["expected_current"], schemas[item["table"]])
                  if item["expected_current"] is not None else None}
                 for item in mutations]
    bibliographic = [item["record"] for item in mutations if item["table"] in {"papers_master.csv", "auxiliary_sources.csv"}]
    normalized = dry_run_bibliographic_normalization(bibliographic)
    for record, canonical in zip(bibliographic, normalized):
        if record.get("doi") != canonical["doi"] or record.get("url") != canonical["url"]:
            raise ValueError("batch DOI/URL must be normalized before reserving identifiers")
    with run_write_lock(run_dir):
        run_dir = run_dir.resolve()
        state = json.loads((run_dir / "run_state.json").read_text(encoding="utf-8"))
        if expected_state is not None and state != expected_state:
            raise ValueError("stale run_state compare-and-swap")
        errors: list[str] = []
        existing_events = load_jsonl_rows(run_dir / "decision_log.jsonl", decision_schema, errors)
        if errors:
            raise ValueError("existing decision history invalid: " + "; ".join(errors))
        existing_ids = {event["decision_id"] for event in existing_events}
        if len(existing_ids) != len(existing_events):
            raise ValueError("duplicate existing decision identifiers")
        event_map: dict[str, dict[str, Any]] = {}
        for event in decisions:
            identifier = event["decision_id"]
            if identifier in existing_ids or identifier in event_map:
                raise ValueError(f"duplicate decision_id {identifier}")
            if event["run_id"] != state["run_id"] or not _reserved_identifier(state, "decision", identifier):
                raise ValueError(f"decision identifier is not reserved in this run: {identifier}")
            event_map[identifier] = event
        tables: dict[str, list[dict[str, Any]]] = {}
        indices: dict[str, dict[str, int]] = {}

        def table_index(table: str) -> dict[str, int]:
            if table not in tables:
                schema = schemas.setdefault(table, load_schema(root, TABLE_SCHEMAS[table]))
                table_errors: list[str] = []
                rows = load_csv_rows(run_dir / table, schema, table_errors)
                if table_errors:
                    raise ValueError("existing table invalid: " + "; ".join(table_errors))
                key = PRIMARY_KEYS[table]
                index = {row[key]: position for position, row in enumerate(rows)}
                if len(index) != len(rows):
                    raise ValueError(f"duplicate existing primary keys in {table}")
                tables[table], indices[table] = rows, index
            return indices[table]

        def parent_exists(table: str, identifier: str | None) -> None:
            if identifier is not None and identifier not in table_index(table):
                raise ValueError(f"parent must precede child: {table} {identifier}")

        changed_tables: list[str] = []
        seen: set[tuple[str, str]] = set()
        for mutation in mutations:
            table, record = mutation["table"], mutation["record"]
            key = PRIMARY_KEYS[table]
            identifier = record[key]
            pair = (table, identifier)
            if pair in seen:
                raise ValueError("a batch may mutate each table/key only once")
            seen.add(pair)
            index = table_index(table)
            before = tables[table][index[identifier]] if identifier in index else None
            if before != mutation["expected_current"]:
                raise ValueError(f"stale row compare-and-swap: {table} {identifier}")
            if mutation["mode"] == "append" and before is not None:
                raise ValueError(f"duplicate append key: {table} {identifier}")
            if table in ID_KINDS and not _reserved_identifier(state, ID_KINDS[table], identifier):
                raise ValueError(f"row identifier is not reserved: {identifier}")
            linked_events = []
            for decision_id in mutation["decision_ids"]:
                if decision_id not in event_map:
                    raise ValueError(f"mutation decision is absent from batch: {decision_id}")
                event = event_map[decision_id]
                if event["entity_type"] != ENTITY_TYPES[table] or event["entity_id"] != identifier:
                    raise ValueError("mutation decision entity does not match row")
                linked_events.append(event)
            _event_coverage(before, record, linked_events, schemas[table])
            if table in {"experiment_groups.csv", "experiments_master.csv", "discoveries.csv", "missing_texts.csv", "fulltext_assets.csv"}:
                parent_exists("papers_master.csv", record["paper_id"])
            if table == "experiments_master.csv":
                parent_exists("experiment_groups.csv", record["experiment_id"])
                group = tables["experiment_groups.csv"][indices["experiment_groups.csv"][record["experiment_id"]]]
                if group["disposition"] in {"support-only", "no-qualifying-comparison"}:
                    raise ValueError("comparison prohibited for support-only/no-qualifying group")
                if group["paper_id"] != record["paper_id"] or not identifier.startswith(record["experiment_id"] + "_C"):
                    raise ValueError("comparison parent identity mismatch")
            if table == "experiment_groups.csv" and not identifier.startswith(record["paper_id"] + "_E"):
                raise ValueError("experiment parent identity mismatch")
            if table == "experiment_groups.csv":
                if before is None and record["record_status"] != "active":
                    raise ValueError("a new experiment inventory record must be active; unused reserved IDs need no placeholder")
                parent_exists("experiment_groups.csv", record.get("reconciled_into_experiment_id"))
            if table == "discoveries.csv":
                parent_exists("search_log.csv", record["search_id"])
            if table == "search_log.csv":
                parent_exists("papers_master.csv", record.get("parent_paper_id"))
                parent_exists("experiments_master.csv", record.get("trigger_comparison_id"))
                parent_exists("search_log.csv", record.get("reused_search_id"))
            if table == "evidence_bundles.csv":
                parent_exists("experiments_master.csv", record["focal_comparison_id"])
            if table == "evidence_links.csv":
                parent_exists("evidence_bundles.csv", record["evidence_bundle_id"])
                parent_exists("experiments_master.csv", record["focal_comparison_id"])
                parent_exists("papers_master.csv", record.get("supporting_paper_id"))
                parent_exists("auxiliary_sources.csv", record.get("supporting_auxiliary_id"))
                parent_exists("evidence_assessments.csv", record.get("evidence_assessment_id"))
            if table == "evidence_assessments.csv":
                parent_exists("papers_master.csv", record.get("source_paper_id"))
                parent_exists("auxiliary_sources.csv", record.get("source_auxiliary_id"))
            if before is None:
                index[identifier] = len(tables[table])
                tables[table].append(record)
            else:
                tables[table][index[identifier]] = record
            if table not in changed_tables:
                changed_tables.append(table)
        lifecycle_tables = {
            "experiment_groups.csv", "experiments_master.csv",
            "evidence_links.csv", "evidence_assessments.csv",
        }
        if lifecycle_tables.intersection(changed_tables):
            for table in lifecycle_tables:
                table_index(table)
            lifecycle_errors = group_record_lifecycle_errors(tables)
            if lifecycle_errors:
                raise ValueError("invalid experiment-record reconciliation: " + "; ".join(lifecycle_errors))
        new_state = None
        if state_updates is not None:
            protected = {field for field in state if field.startswith("next_")} | {
                "run_id", "protocol_version", "package_version", "schema_version",
                "registration_status", "repository_commit", "immutable_inputs_sha256", "started_at",
            }
            if not isinstance(state_updates, dict) or set(state_updates) & protected:
                raise ValueError("batch checkpoint may not overwrite counters or immutable run identity")
            new_state = {**state, **state_updates}
            validate_record(new_state, load_schema(root, "run_state.schema.json"))
            ids = state_decision_ids or []
            linked = []
            for identifier in ids:
                event = event_map.get(identifier)
                if not event or event["entity_type"] != "run" or event["entity_id"] != state["run_id"]:
                    raise ValueError("checkpoint requires matching run decision events")
                linked.append(event)
            _event_coverage(state, new_state, linked)
        activation_ids = {event["decision_id"] for event in decisions
                          if event.get("field") == "process_search_activation"}
        if activation_ids:
            from execution_contract import process_obligation_errors
            comparison_schema = load_schema(root, "experiments.schema.json")
            for event in decisions:
                if event["decision_id"] in activation_ids:
                    payload = event.get("new_value")
                    validate_record(payload.get("eligible_comparison") if isinstance(payload, dict) else None,
                                    comparison_schema)
            for table in ("experiments_master.csv", "search_log.csv"):
                table_index(table)
            # Eligibility uses the shared predicate; native premise validation
            # must also pass before an activation can durably earn a window.
            # Schema-valid pointers alone cannot certify an incomplete bundle.
            from validate_run import awareness_regime_errors, evidence_bundle_errors
            for table in ("papers_master.csv", "experiment_groups.csv", "auxiliary_sources.csv",
                          "evidence_assessments.csv", "evidence_bundles.csv", "evidence_links.csv"):
                table_index(table)
            for event in decisions:
                if event["decision_id"] not in activation_ids:
                    continue
                snapshot = event["new_value"]["eligible_comparison"]
                cid = snapshot["comparison_id"]
                scoped_bundles = [item for item in tables["evidence_bundles.csv"] if item["focal_comparison_id"] == cid]
                scoped_links = [item for item in tables["evidence_links.csv"] if item["focal_comparison_id"] == cid]
                premise_errors = awareness_regime_errors(snapshot) + evidence_bundle_errors(
                    [snapshot], scoped_bundles, scoped_links,
                    {item["paper_id"] for item in tables["papers_master.csv"]},
                    {item["auxiliary_id"] for item in tables["auxiliary_sources.csv"]},
                    {item["experiment_id"] for item in tables["experiment_groups.csv"]},
                    {item["evidence_assessment_id"] for item in tables["evidence_assessments.csv"]})
                if premise_errors:
                    raise ValueError("invalid process activation premises before persistence: " + "; ".join(premise_errors))
            errors = process_obligation_errors(tables["experiments_master.csv"], new_state or state,
                                               tables["search_log.csv"], existing_events + decisions)
            prefixes = tuple(f"process activation {identifier}:" for identifier in activation_ids)
            write_errors = [error for error in errors if error.startswith(prefixes)]
            if write_errors:
                raise ValueError("invalid process obligation before persistence: " + "; ".join(write_errors))
        raw_history = (run_dir / "decision_log.jsonl").read_bytes()
        if raw_history and not raw_history.endswith(b"\n"):
            raise ValueError("existing decision history lacks final physical LF")
        history = raw_history + b"".join(
            (json.dumps(event, ensure_ascii=True, separators=(",", ":")) + "\n").encode("utf-8")
            for event in decisions
        )
        replacements = [("decision_log.jsonl", history)]
        import io
        for table in changed_tables:
            stream = io.StringIO(newline="")
            headers = list(schemas[table]["properties"])
            writer = csv.DictWriter(stream, fieldnames=headers, lineterminator="\n")
            writer.writeheader()
            for row in tables[table]:
                writer.writerow({field: encode_cell(field, row[field]) for field in headers})
            replacements.append((table, stream.getvalue().encode("utf-8")))
        if new_state is not None:
            replacements.append(("run_state.json", (json.dumps(new_state, ensure_ascii=True, indent=2) + "\n").encode("utf-8")))
        _publish_transaction(run_dir, replacements)
        return {"mutations": len(mutations), "decisions": len(decisions), "tables": len(changed_tables)}


def reserve_identifiers(
    run_dir: Path, requests: list[dict[str, Any]], *, root: Path = ROOT,
) -> list[list[str]]:
    """Reserve multiple kinds/parents with one durable state write.

    Each request is {kind, count, parent_id}; returned ranges follow request
    order. Qualifying comparison parents must already exist durably. A failed
    request publishes no counter changes, and committed ranges are never reused.
    """
    if not isinstance(requests, list) or not requests or len(requests) > MAX_ID_RESERVATIONS:
        raise ValueError("identifier requests must be a nonempty bounded array")
    total = 0
    for request in requests:
        if not isinstance(request, dict) or set(request) != {"kind", "count", "parent_id"}:
            raise ValueError("reservation requires exactly kind, count, parent_id")
        count = request['count']
        if not isinstance(count, int) or isinstance(count, bool) or not 1 <= count <= MAX_ID_RESERVATIONS:
            raise ValueError("identifier reservation count must be 1..1000")
        if request['kind'] not in {*SCALAR_KINDS, 'experiment', 'comparison'}:
            raise ValueError(f"unknown identifier kind {request['kind']!r}")
        total += count
    if total > MAX_ID_RESERVATIONS:
        raise ValueError("total identifier reservation count must be <=1000")
    with run_write_lock(run_dir):
        state_path = run_dir / 'run_state.json'
        state = json.loads(state_path.read_text(encoding='utf-8'))
        groups = {}
        if any(request['kind'] == 'comparison' for request in requests):
            errors: list[str] = []
            schema = load_schema(root, 'experiment_groups.schema.json')
            group_path = run_dir / 'experiment_groups.csv'
            rows = load_csv_rows(group_path, schema, errors) if group_path.exists() else []
            if errors:
                raise ValueError('experiment_groups.csv is invalid; refusing allocation: ' + '; '.join(errors))
            groups = {row['experiment_id']: row for row in rows}
            if len(groups) != len(rows):
                raise ValueError('comparison allocation requires unique durable experiment-group rows')
        ranges = []
        for request in requests:
            kind, count, parent_id = request['kind'], request['count'], request['parent_id']
            if kind in SCALAR_KINDS:
                field, marker, width = SCALAR_KINDS[kind]
                counter = state[field]
                if not isinstance(counter, int) or isinstance(counter, bool) or counter < 1:
                    raise ValueError(f'invalid allocator counter {field}')
                if counter + count - 1 > (10 ** width) - 1:
                    raise ValueError(f'{kind} counter exhausted for run {state["run_id"]}')
                prefix = '' if kind == 'paper' else state['run_id']
                values = [f'{prefix}{marker}{value:0{width}d}' for value in range(counter, counter + count)]
                state[field] = counter + count
            else:
                pattern = r'P[0-9]{6}' if kind == 'experiment' else r'P[0-9]{6}_E[0-9]{2}'
                if parent_id is None or not isinstance(parent_id, str) or not re.fullmatch(pattern, parent_id):
                    raise ValueError(f'{kind} allocation requires a valid --parent-id')
                if kind == 'comparison':
                    group = groups.get(parent_id)
                    if not group:
                        raise ValueError('comparison allocation requires one durable experiment-group row first')
                    if group['disposition'] in {'support-only', 'no-qualifying-comparison'}:
                        raise ValueError('comparison allocation prohibited for an experiment group whose final disposition has no qualifying comparison')
                field, marker = (('next_experiment_counters', '_E') if kind == 'experiment'
                                 else ('next_comparison_counters', '_C'))
                counters = state[field]
                counter = counters.get(parent_id, 1)
                if not isinstance(counter, int) or isinstance(counter, bool) or counter < 1:
                    raise ValueError(f'invalid allocator counter for {parent_id}')
                if counter + count - 1 > 99:
                    raise ValueError(f'{kind} counter exhausted for {parent_id}')
                values = [f'{parent_id}{marker}{value:02d}' for value in range(counter, counter + count)]
                counters[parent_id] = counter + count
            ranges.append(values)
        _atomic_write_json(state_path, state)
    return ranges


def allocate_identifiers(
    run_dir: Path, kind: str, count: int = 1, parent_id: str | None = None, *, root: Path = ROOT,
) -> list[str]:
    """Reserve one bounded same-kind range through the transaction allocator."""
    return reserve_identifiers(run_dir, [{'kind': kind, 'count': count, 'parent_id': parent_id}], root=root)[0]


def allocate_identifier(run_dir: Path, kind: str, parent_id: str | None = None) -> str:
    """Backward-compatible singleton reservation through the locked range allocator."""
    return allocate_identifiers(run_dir, kind, 1, parent_id)[0]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "operation",
        choices=(
            "append-csv", "upsert-csv", "append-decision", "allocate-id",
            "dry-run-bibliographic-normalization", "batch", "allocate-ids", "reserve-ids",
        ),
    )
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--row-file", type=Path, help="JSON object containing typed values")
    parser.add_argument("--table", choices=tuple(TABLE_SCHEMAS))
    parser.add_argument("--key-field")
    parser.add_argument(
        "--id-kind",
        choices=(
            "paper", "experiment", "comparison", "decision", "search", "discovery",
            "auxiliary", "evidence_link", "evidence_bundle", "evidence_assessment",
            "fulltext_asset",
        ),
    )
    parser.add_argument("--parent-id")
    parser.add_argument("--count", type=int, default=1)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--runs-root", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    runs_root = args.runs_root.resolve() if args.runs_root else root / "runs"
    run_dir = runs_root / args.run_id
    if args.operation in {"allocate-id", "allocate-ids"}:
        if not args.id_kind:
            raise SystemExit("--id-kind is required for allocate-id")
        if args.operation == "allocate-id" and args.count != 1:
            raise SystemExit("allocate-id requires --count 1; use allocate-ids for a range")
        identifiers = allocate_identifiers(run_dir, args.id_kind, args.count, args.parent_id, root=root)
        print(identifiers[0] if args.operation == "allocate-id" else json.dumps(identifiers))
        return 0
    if not args.row_file:
        raise SystemExit("--row-file is required for record writes")
    record = json.loads(args.row_file.read_text(encoding="utf-8"))
    if args.operation == "reserve-ids":
        print(json.dumps(reserve_identifiers(run_dir, record, root=root)))
        return 0
    if args.operation == "dry-run-bibliographic-normalization":
        if not isinstance(record, list):
            raise SystemExit("normalization dry run row file must contain a JSON array")
        normalized = dry_run_bibliographic_normalization(record)
        print(f"PASS: {len(normalized)} bibliographic records normalize without persistence")
        return 0
    if not isinstance(record, dict):
        raise SystemExit("row file must contain one JSON object")
    if args.operation == "batch":
        print(json.dumps(write_batch(run_dir, root=root, **record)))
        return 0
    if args.operation == "append-decision":
        append_jsonl_record(
            run_dir / "decision_log.jsonl",
            load_schema(root, "decision_log.schema.json"),
            record,
            root=root,
        )
    else:
        if not args.table:
            raise SystemExit("--table is required for CSV operations")
        if args.operation == "upsert-csv" and not args.key_field:
            raise SystemExit("--key-field is required for upsert-csv")
        write_csv_record(
            run_dir / args.table,
            load_schema(root, TABLE_SCHEMAS[args.table]),
            record,
            key_field=args.key_field if args.operation == "upsert-csv" else None,
        )
    print("PASS: validated structured record written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
