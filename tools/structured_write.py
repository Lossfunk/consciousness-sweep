#!/usr/bin/env python3
"""Validate typed records before atomically writing run CSV or JSONL files."""

from __future__ import annotations

import argparse
import csv
import fcntl
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

from validate_run import load_csv_rows, load_jsonl_rows


ROOT = Path(__file__).resolve().parents[1]
TABLE_SCHEMAS = {
    "papers_master.csv": "papers.schema.json",
    "experiments_master.csv": "experiments.schema.json",
    "search_log.csv": "search_log.schema.json",
    "discoveries.csv": "discoveries.schema.json",
    "missing_texts.csv": "missing_texts.schema.json",
    "auxiliary_sources.csv": "auxiliary_sources.schema.json",
    "evidence_links.csv": "evidence_links.schema.json",
}
PRIMARY_KEYS = {
    "papers_master.csv": "paper_id",
    "experiments_master.csv": "comparison_id",
    "search_log.csv": "search_id",
    "discoveries.csv": "discovery_id",
    "missing_texts.csv": "paper_id",
    "auxiliary_sources.csv": "auxiliary_id",
    "evidence_links.csv": "evidence_link_id",
}
ARRAY_FIELDS = {
    "stats_flags", "attempted_sources", "E_diagnostic_source_locations",
    "factorial_component_effects",
}
DOI_PREFIX = re.compile(
    r"^(?:https?://(?:dx\.)?doi\.org/|doi:\s*|doi\.org/)", re.IGNORECASE
)


@contextmanager
def run_write_lock(directory: Path):
    """Serialize every counter allocation and run-file read-modify-write."""
    directory.mkdir(parents=True, exist_ok=True)
    lock_path = directory / ".structured-write.lock"
    with lock_path.open("a+b") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
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


def encode_cell(field: str, value: Any) -> str:
    if value is None:
        return ""
    if field in ARRAY_FIELDS:
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
    validate_record(record, schema)
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


def append_jsonl_record(path: Path, schema: dict[str, Any], record: dict[str, Any]) -> None:
    validate_record(record, schema)
    with run_write_lock(path.parent):
        errors: list[str] = []
        existing = load_jsonl_rows(path, schema, errors) if path.exists() else []
        if errors:
            raise ValueError("existing JSONL is invalid; refusing mutation: " + "; ".join(errors))
        decision_ids = {row["decision_id"] for row in existing}
        if record["decision_id"] in decision_ids:
            raise ValueError(f"duplicate decision_id {record['decision_id']!r}; refusing append")
        _atomic_write_jsonl(path, [*existing, record])


def allocate_identifier(run_dir: Path, kind: str, parent_id: str | None = None) -> str:
    """Atomically reserve one never-recycled identifier from run_state.json."""
    scalar_kinds = {
        "paper": ("next_paper_counter", "P", 6),
        "decision": ("next_decision_counter", "_D", 6),
        "search": ("next_search_counter", "_S", 6),
        "discovery": ("next_discovery_counter", "_R", 6),
        "auxiliary": ("next_auxiliary_counter", "_AUX", 6),
        "evidence_link": ("next_evidence_link_counter", "_EL", 6),
        "evidence_bundle": ("next_evidence_bundle_counter", "_EB", 6),
    }
    with run_write_lock(run_dir):
        state_path = run_dir / "run_state.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        run_id = state["run_id"]
        if kind in scalar_kinds:
            field, marker, width = scalar_kinds[kind]
            counter = state[field]
            if counter > (10 ** width) - 1:
                raise ValueError(f"{kind} counter exhausted for run {run_id}")
            prefix = "" if kind == "paper" else run_id
            identifier = f"{prefix}{marker}{counter:0{width}d}"
            state[field] = counter + 1
        elif kind == "experiment":
            if parent_id is None or not re.fullmatch(r"P[0-9]{6}", parent_id):
                raise ValueError("experiment allocation requires --parent-id P######")
            counters = state["next_experiment_counters"]
            counter = counters.get(parent_id, 1)
            if counter > 99:
                raise ValueError(f"experiment counter exhausted for {parent_id}")
            identifier = f"{parent_id}_E{counter:02d}"
            counters[parent_id] = counter + 1
        elif kind == "comparison":
            if parent_id is None or not re.fullmatch(r"P[0-9]{6}_E[0-9]{2}", parent_id):
                raise ValueError("comparison allocation requires --parent-id P######_E##")
            paper_id, experiment_suffix = parent_id.split("_E", 1)
            next_experiment = state["next_experiment_counters"].get(paper_id, 1)
            if int(experiment_suffix) >= next_experiment:
                raise ValueError(
                    "comparison allocation requires the experiment group to be allocated first"
                )
            counters = state["next_comparison_counters"]
            counter = counters.get(parent_id, 1)
            if counter > 99:
                raise ValueError(f"comparison counter exhausted for {parent_id}")
            identifier = f"{parent_id}_C{counter:02d}"
            counters[parent_id] = counter + 1
        else:
            raise ValueError(f"unknown identifier kind {kind!r}")
        _atomic_write_json(state_path, state)
    return identifier


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "operation",
        choices=(
            "append-csv", "upsert-csv", "append-decision", "allocate-id",
            "dry-run-bibliographic-normalization",
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
            "auxiliary", "evidence_link", "evidence_bundle",
        ),
    )
    parser.add_argument("--parent-id")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--runs-root", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    runs_root = args.runs_root.resolve() if args.runs_root else root / "runs"
    run_dir = runs_root / args.run_id
    if args.operation == "allocate-id":
        if not args.id_kind:
            raise SystemExit("--id-kind is required for allocate-id")
        print(allocate_identifier(run_dir, args.id_kind, args.parent_id))
        return 0
    if not args.row_file:
        raise SystemExit("--row-file is required for record writes")
    record = json.loads(args.row_file.read_text(encoding="utf-8"))
    if args.operation == "dry-run-bibliographic-normalization":
        if not isinstance(record, list):
            raise SystemExit("normalization dry run row file must contain a JSON array")
        normalized = dry_run_bibliographic_normalization(record)
        print(f"PASS: {len(normalized)} bibliographic records normalize without persistence")
        return 0
    if not isinstance(record, dict):
        raise SystemExit("row file must contain one JSON object")
    if args.operation == "append-decision":
        append_jsonl_record(
            run_dir / "decision_log.jsonl",
            load_schema(root, "decision_log.schema.json"),
            record,
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
