#!/usr/bin/env python3
"""Validate one run's schemas, CSV encodings, identifiers, and references."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[1]
CSV_SCHEMAS = {
    "papers_master.csv": "papers.schema.json",
    "experiments_master.csv": "experiments.schema.json",
    "search_log.csv": "search_log.schema.json",
    "discoveries.csv": "discoveries.schema.json",
    "missing_texts.csv": "missing_texts.schema.json",
    "design_eligible_experiments.csv": "experiments.schema.json",
    "constraint_ready_experiments.csv": "experiments.schema.json",
    "awareness_linked_differences.csv": "experiments.schema.json",
    "preserved_capacities.csv": "experiments.schema.json",
    "inconclusive_experiments.csv": "experiments.schema.json",
}
ARRAY_FIELDS = {"stats_flags", "attempted_sources"}
BOOLEAN_FIELDS = {"manually_requested"}
FLOAT_FIELDS = {"null_BF01"}
INTEGER_FIELDS = {
    "year", "first_seen_wave", "wave", "results_returned", "new_unique_papers",
    "result_rank", "manual_request_wave", "provided_wave",
}


def immutable_paths(root: Path) -> list[Path]:
    paths = [
        root / "AGENTS.md", root / "PROTOCOL.md", root / "seeds_empirical.csv",
        root / "seeds_reviews.csv", root / "queries.md", root / "config.yaml",
        root / "requirements.txt",
    ]
    paths.extend(sorted((root / "schemas").glob("*.json")))
    paths.extend(sorted((root / "tools").glob("*.py")))
    return paths


def immutable_hashes(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in immutable_paths(root)
    }


def resolve_local_ref(schema: dict[str, Any], ref: str) -> Any:
    node: Any = schema
    for part in ref.removeprefix("#/").split("/"):
        node = node[part.replace("~1", "/").replace("~0", "~")]
    return node


def allows_null(node: Any, schema: dict[str, Any]) -> bool:
    if not isinstance(node, dict):
        return False
    if node.get("type") == "null" or node.get("const") is None and "const" in node:
        return True
    if "$ref" in node and str(node["$ref"]).startswith("#/"):
        return allows_null(resolve_local_ref(schema, node["$ref"]), schema)
    return any(allows_null(item, schema) for key in ("anyOf", "oneOf") for item in node.get(key, []))


def convert_cell(field: str, value: str | None, property_schema: dict[str, Any], schema: dict[str, Any]) -> Any:
    text = "" if value is None else value.strip()
    if field in ARRAY_FIELDS:
        if not text:
            return None if allows_null(property_schema, schema) else []
        parsed = json.loads(text)
        if not isinstance(parsed, list):
            raise ValueError("must encode a JSON array")
        return parsed
    if not text and allows_null(property_schema, schema):
        return None
    if field in BOOLEAN_FIELDS:
        if text.lower() not in {"true", "false"}:
            raise ValueError("must be true or false")
        return text.lower() == "true"
    if field in FLOAT_FIELDS:
        return float(text)
    if field in INTEGER_FIELDS:
        return int(text)
    return text


def load_csv_rows(path: Path, schema: dict[str, Any], errors: list[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    headers = list(schema["properties"].keys())
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    try:
        with path.open(newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames != headers:
                errors.append(f"{path}: headers do not exactly match {headers}")
                return rows
            for line_number, raw in enumerate(reader, start=2):
                if None in raw:
                    errors.append(f"{path}:{line_number}: inconsistent column count")
                    continue
                try:
                    row = {
                        field: convert_cell(field, raw[field], schema["properties"][field], schema)
                        for field in headers
                    }
                except (ValueError, TypeError, json.JSONDecodeError) as exc:
                    errors.append(f"{path}:{line_number}: CSV decoding error: {exc}")
                    continue
                for error in sorted(validator.iter_errors(row), key=lambda item: list(item.path)):
                    location = ".".join(str(part) for part in error.path) or "<row>"
                    errors.append(f"{path}:{line_number}:{location}: {error.message}")
                rows.append(row)
    except (OSError, csv.Error) as exc:
        errors.append(f"{path}: {exc}")
    return rows


def check_unique(rows: list[dict[str, Any]], field: str, label: str, errors: list[str]) -> None:
    seen: set[Any] = set()
    for row in rows:
        value = row.get(field)
        if value in seen:
            errors.append(f"{label}: duplicate {field} {value}")
        seen.add(value)


def max_suffix(values: list[str], marker: str, width: int = 6) -> int:
    found = []
    pattern = re.compile(re.escape(marker) + rf"([0-9]{{{width}}})$")
    for value in values:
        match = pattern.search(value)
        if match:
            found.append(int(match.group(1)))
    return max(found, default=0)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--runs-root", type=Path)
    parser.add_argument("--allow-stale-counters", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    runs_root = args.runs_root.resolve() if args.runs_root else (root / "runs")
    run_dir = runs_root / args.run_id
    errors: list[str] = []

    required = [*CSV_SCHEMAS, "decision_log.jsonl", "run_state.json", "run_summary.md", "manual_fulltexts"]
    for name in required:
        if not (run_dir / name).exists():
            errors.append(f"missing run path: {run_dir / name}")

    schemas: dict[str, dict[str, Any]] = {}
    for name in set(CSV_SCHEMAS.values()) | {"decision_log.schema.json", "run_state.schema.json"}:
        try:
            schema = json.loads((root / "schemas" / name).read_text(encoding="utf-8"))
            Draft202012Validator.check_schema(schema)
            schemas[name] = schema
        except Exception as exc:
            errors.append(f"schemas/{name}: {exc}")

    tables: dict[str, list[dict[str, Any]]] = {}
    if not errors:
        for filename, schema_name in CSV_SCHEMAS.items():
            tables[filename] = load_csv_rows(run_dir / filename, schemas[schema_name], errors)

    decisions: list[dict[str, Any]] = []
    decision_path = run_dir / "decision_log.jsonl"
    if decision_path.exists() and "decision_log.schema.json" in schemas:
        validator = Draft202012Validator(schemas["decision_log.schema.json"], format_checker=FormatChecker())
        for line_number, line in enumerate(decision_path.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                errors.append(f"{decision_path}:{line_number}: blank JSONL line")
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError as exc:
                errors.append(f"{decision_path}:{line_number}: {exc}")
                continue
            for error in validator.iter_errors(event):
                errors.append(f"{decision_path}:{line_number}: {error.message}")
            decisions.append(event)

    state: dict[str, Any] = {}
    state_path = run_dir / "run_state.json"
    if state_path.exists() and "run_state.schema.json" in schemas:
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
            validator = Draft202012Validator(schemas["run_state.schema.json"], format_checker=FormatChecker())
            for error in validator.iter_errors(state):
                errors.append(f"{state_path}: {error.message}")
        except json.JSONDecodeError as exc:
            errors.append(f"{state_path}: {exc}")

    papers = tables.get("papers_master.csv", [])
    experiments = tables.get("experiments_master.csv", [])
    searches = tables.get("search_log.csv", [])
    discoveries = tables.get("discoveries.csv", [])
    missing = tables.get("missing_texts.csv", [])
    for rows, field, label in (
        (papers, "paper_id", "papers_master.csv"),
        (experiments, "comparison_id", "experiments_master.csv"),
        (searches, "search_id", "search_log.csv"),
        (discoveries, "discovery_id", "discoveries.csv"),
        (missing, "paper_id", "missing_texts.csv"),
        (decisions, "decision_id", "decision_log.jsonl"),
    ):
        check_unique(rows, field, label, errors)
    for filename in (
        "design_eligible_experiments.csv", "constraint_ready_experiments.csv",
        "awareness_linked_differences.csv", "preserved_capacities.csv",
        "inconclusive_experiments.csv",
    ):
        check_unique(tables.get(filename, []), "comparison_id", filename, errors)

    paper_ids = {row["paper_id"] for row in papers}
    experiment_ids = {row["experiment_id"] for row in experiments}
    comparison_ids = {row["comparison_id"] for row in experiments}
    search_ids = {row["search_id"] for row in searches}
    discovery_ids = {row["discovery_id"] for row in discoveries}
    for row in papers:
        for field in ("first_discovery_parent", "duplicate_of"):
            if row.get(field) is not None and row[field] not in paper_ids:
                errors.append(f"papers_master.csv: {row['paper_id']} references missing {field} {row[field]}")
        if row.get("first_search_id") is not None and row["first_search_id"] not in search_ids:
            errors.append(f"papers_master.csv: {row['paper_id']} references missing first_search_id {row['first_search_id']}")
    for row in experiments:
        if row["paper_id"] not in paper_ids:
            errors.append(f"experiments_master.csv: {row['comparison_id']} references missing paper {row['paper_id']}")
        if not row["experiment_id"].startswith(f"{row['paper_id']}_E"):
            errors.append(f"experiments_master.csv: {row['comparison_id']} experiment_id does not belong to paper_id")
        if not row["comparison_id"].startswith(f"{row['experiment_id']}_C"):
            errors.append(f"experiments_master.csv: {row['comparison_id']} does not belong to experiment_id {row['experiment_id']}")
    for row in searches:
        if row.get("parent_paper_id") is not None and row["parent_paper_id"] not in paper_ids:
            errors.append(f"search_log.csv: {row['search_id']} references missing parent paper")
        if row.get("trigger_comparison_id") is not None and row["trigger_comparison_id"] not in comparison_ids:
            errors.append(f"search_log.csv: {row['search_id']} references missing trigger comparison")
    for row in discoveries:
        if row["search_id"] not in search_ids:
            errors.append(f"discoveries.csv: {row['discovery_id']} references missing search {row['search_id']}")
        if row["paper_id"] not in paper_ids:
            errors.append(f"discoveries.csv: {row['discovery_id']} references missing paper {row['paper_id']}")
    for row in missing:
        if row["paper_id"] not in paper_ids:
            errors.append(f"missing_texts.csv: references missing paper {row['paper_id']}")
        local_path = row.get("local_fulltext_path")
        if local_path:
            candidate = Path(local_path)
            candidate = candidate if candidate.is_absolute() else root / candidate
            if not candidate.exists():
                errors.append(f"missing_texts.csv: local_fulltext_path does not exist: {local_path}")
            elif row.get("file_sha256"):
                digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
                if digest != row["file_sha256"]:
                    errors.append(f"missing_texts.csv: SHA-256 mismatch for {local_path}")

    valid_entities = {
        "paper": paper_ids,
        "experiment": experiment_ids,
        "comparison": comparison_ids,
        "search": search_ids,
        "discovery": discovery_ids,
        "missing_text": paper_ids,
        "run": {args.run_id},
    }
    for event in decisions:
        if event.get("run_id") != args.run_id:
            errors.append(f"decision_log.jsonl: {event.get('decision_id')} has wrong run_id")
        entity_type = event.get("entity_type")
        if entity_type in valid_entities and event.get("entity_id") not in valid_entities[entity_type]:
            errors.append(f"decision_log.jsonl: {event.get('decision_id')} references missing {entity_type} {event.get('entity_id')}")

    if state:
        if state.get("run_id") != args.run_id:
            errors.append("run_state.json: run_id does not match directory")
        try:
            config = yaml.safe_load((root / "config.yaml").read_text(encoding="utf-8"))
            if state.get("protocol_version") != config.get("protocol_version"):
                errors.append("run_state.json: protocol_version differs from config")
            if state.get("registration_status") != config.get("registration_status"):
                errors.append("run_state.json: registration_status differs from config")
        except Exception as exc:
            errors.append(f"config.yaml: {exc}")
        try:
            if state.get("immutable_inputs_sha256") != immutable_hashes(root):
                errors.append("run_state.json: immutable input hashes have changed")
        except OSError as exc:
            errors.append(f"immutable input hashing failed: {exc}")

        if not args.allow_stale_counters:
            paper_max = max((int(value[1:]) for value in paper_ids), default=0)
            if state.get("next_paper_counter", 0) <= paper_max:
                errors.append("run_state.json: next_paper_counter is stale")
            for paper_id in paper_ids:
                exp_max = max(
                    (int(exp.split("_E")[1]) for exp in experiment_ids if exp.startswith(f"{paper_id}_E")),
                    default=0,
                )
                if state.get("next_experiment_counters", {}).get(paper_id, 1) <= exp_max:
                    errors.append(f"run_state.json: next experiment counter is stale for {paper_id}")
            for experiment_id in experiment_ids:
                comparison_max = max_suffix(list(comparison_ids), f"{experiment_id}_C", width=2)
                if state.get("next_comparison_counters", {}).get(experiment_id, 1) <= comparison_max:
                    errors.append(f"run_state.json: next comparison counter is stale for {experiment_id}")
            counter_checks = (
                ("next_decision_counter", max_suffix([row.get("decision_id", "") for row in decisions], "_D")),
                ("next_search_counter", max_suffix(list(search_ids), "_S")),
                ("next_discovery_counter", max_suffix(list(discovery_ids), "_R")),
            )
            for field, maximum in counter_checks:
                if state.get(field, 0) <= maximum:
                    errors.append(f"run_state.json: {field} is stale")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"PASS: {args.run_id} schemas, CSV encodings, JSONL, IDs, references, hashes, and counters validate.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
