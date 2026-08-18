#!/usr/bin/env python3
"""Validate typed records before atomically writing run CSV or JSONL files."""

from __future__ import annotations

import argparse
import csv
import json
import os
import tempfile
import sys
from pathlib import Path
from typing import Any

try:
    from jsonschema import Draft202012Validator, FormatChecker
except ModuleNotFoundError as exc:
    print(
        f"ERROR: missing repository dependency {exc.name!r}. "
        "Run: python3 tools/bootstrap_env.py --venv .venv",
        file=sys.stderr,
    )
    raise SystemExit(3) from None

from validate_run import load_csv_rows


ROOT = Path(__file__).resolve().parents[1]
TABLE_SCHEMAS = {
    "papers_master.csv": "papers.schema.json",
    "experiments_master.csv": "experiments.schema.json",
    "search_log.csv": "search_log.schema.json",
    "discoveries.csv": "discoveries.schema.json",
    "missing_texts.csv": "missing_texts.schema.json",
    "auxiliary_sources.csv": "auxiliary_sources.schema.json",
}
PRIMARY_KEYS = {
    "papers_master.csv": "paper_id",
    "experiments_master.csv": "comparison_id",
    "search_log.csv": "search_id",
    "discoveries.csv": "discovery_id",
    "missing_texts.csv": "paper_id",
    "auxiliary_sources.csv": "auxiliary_id",
}
ARRAY_FIELDS = {"stats_flags", "attempted_sources"}


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


def write_csv_record(
    path: Path,
    schema: dict[str, Any],
    record: dict[str, Any],
    *,
    key_field: str | None = None,
) -> None:
    """Append, or key-upsert, only after the existing table and new row validate."""
    validate_record(record, schema)
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
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    decision_ids: set[str] = set()
    if path.exists():
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                raise ValueError(f"existing JSONL has blank line {line_number}; refusing mutation")
            existing = json.loads(line)
            validator.validate(existing)
            decision_ids.add(existing["decision_id"])
    if record["decision_id"] in decision_ids:
        raise ValueError(f"duplicate decision_id {record['decision_id']!r}; refusing append")
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("operation", choices=("append-csv", "upsert-csv", "append-decision"))
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--row-file", type=Path, required=True, help="JSON object containing typed values")
    parser.add_argument("--table", choices=tuple(TABLE_SCHEMAS))
    parser.add_argument("--key-field")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--runs-root", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    runs_root = args.runs_root.resolve() if args.runs_root else root / "runs"
    run_dir = runs_root / args.run_id
    record = json.loads(args.row_file.read_text(encoding="utf-8"))
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
