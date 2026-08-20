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
from urllib.parse import unquote

try:
    import yaml
    from jsonschema import Draft202012Validator, FormatChecker
except ModuleNotFoundError as exc:
    print(
        f"ERROR: missing repository dependency {exc.name!r}. "
        "Run: python3 tools/bootstrap_env.py --venv .venv",
        file=sys.stderr,
    )
    raise SystemExit(3) from None

from execution_contract import (
    alternative_control_scan_errors, awareness_result_provenance_errors,
    capacity_identity_errors, citation_window_key, completion_errors, contrast_integrity_bundle_errors,
    e_diagnostic_same_y_bundle_errors, experiment_group_errors,
    factorial_e_diagnostic_bundle_errors, functional_structure_errors,
    ordered_result_set_sha256, paper_citation_node_errors, route_audit_errors, search_window_key,
    validate_declared_bundle_status,
)
ROOT = Path(__file__).resolve().parents[1]
DOI_PREFIX = re.compile(
    r"^(?:https?://(?:dx\.)?doi\.org/|doi:\s*|doi\.org/)", re.IGNORECASE
)


def normalized_doi(value: Any) -> str:
    return DOI_PREFIX.sub("", unquote(str(value or "")).strip()).strip().casefold()
CSV_SCHEMAS = {
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
    "design_eligible_experiments.csv": "experiments.schema.json",
    "constraint_ready_experiments.csv": "experiments.schema.json",
    "awareness_linked_differences.csv": "experiments.schema.json",
    "unaware_capacities.csv": "experiments.schema.json",
    "no_detectable_awareness_differences.csv": "experiments.schema.json",
    "equivalence_supported_no_difference.csv": "experiments.schema.json",
    "unresolved_comparisons.csv": "experiments.schema.json",
}
ARRAY_FIELDS = {
    "stats_flags", "attempted_sources", "E_diagnostic_source_locations",
    "factorial_component_effects", "evidence_bundle_ids", "required_member_keys",
    "linked_comparison_ids", "support_roles",
    "activated_normalized_y_labels", "completed_search_window_keys",
    "bridge_depth0_eligible_paper_ids", "pending_bridge_expansion_paper_ids",
    "completed_bridge_expansion_paper_ids",
}
OBJECT_FIELDS = {"source_parameters"}
BOOLEAN_FIELDS = {
    "manually_requested", "used_for_decision", "current_for_paper",
    "pre_atomization_assessed",
}
FLOAT_FIELDS = {"null_BF01"}
INTEGER_FIELDS = {
    "year", "first_seen_wave", "wave", "results_returned", "new_unique_papers",
    "result_rank", "manual_request_wave", "obtained_wave", "requested_max_n",
    "actual_returned_n", "title_screen_batch_size", "abstract_screen_batch_size",
    "bridge_lineage_depth", "citation_parent_bridge_depth",
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
    if field in ARRAY_FIELDS or field in OBJECT_FIELDS:
        if not text:
            if allows_null(property_schema, schema):
                return None
            return [] if field in ARRAY_FIELDS else {}
        parsed = json.loads(text)
        expected = list if field in ARRAY_FIELDS else dict
        if not isinstance(parsed, expected):
            raise ValueError(f"must encode a JSON {expected.__name__}")
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


def load_jsonl_rows(
    path: Path, schema: dict[str, Any], errors: list[str]
) -> list[dict[str, Any]]:
    """Parse JSONL using physical LF bytes, never Unicode split-line semantics."""
    rows: list[dict[str, Any]] = []
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    try:
        raw_records = path.read_bytes().split(b"\n")
    except OSError as exc:
        errors.append(f"{path}: {exc}")
        return rows
    if raw_records and raw_records[-1] == b"":
        raw_records.pop()
    for record_number, raw in enumerate(raw_records, start=1):
        if not raw.strip():
            errors.append(f"{path}:{record_number}: blank JSONL record")
            continue
        try:
            event = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            errors.append(f"{path}:{record_number}: {exc}")
            continue
        if not isinstance(event, dict):
            errors.append(f"{path}:{record_number}: JSONL record is not an object")
            continue
        for error in validator.iter_errors(event):
            errors.append(f"{path}:{record_number}: {error.message}")
        rows.append(event)
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


def dependency_errors(
    experiments: list[dict[str, Any]], bundles: list[dict[str, Any]]
) -> list[str]:
    """Return comparison-level errors for explicit classification-critical bundles."""
    errors: list[str] = []
    by_comparison: dict[str, list[dict[str, Any]]] = {}
    for bundle in bundles:
        by_comparison.setdefault(bundle["focal_comparison_id"], []).append(bundle)
    for row in experiments:
        comparison_id = row.get("comparison_id")
        status = row.get("critical_dependency_status")
        linked = by_comparison.get(comparison_id, [])
        if status == "resolved" and not any(bundle.get("bundle_status") == "complete" for bundle in linked):
            errors.append(
                f"experiments_master.csv: {comparison_id} has resolved critical dependency "
                "without a complete scientific evidence bundle"
            )
        if status == "unresolved" and not any(bundle.get("bundle_status") in {"incomplete", "conflicted"} for bundle in linked):
            errors.append(
                f"experiments_master.csv: {comparison_id} has unresolved critical dependency "
                "without an incomplete/conflicted scientific evidence bundle"
            )
    return errors


def _premise_is_established(row: dict[str, Any], premise: str) -> bool:
    if premise == "awareness-A":
        return row.get("A_code") in {"A-direct", "A-validated"}
    if premise in {"first-order-evidence-E", "E-diagnostic"}:
        return row.get("E_code") in {"E-matched", "E-diagnostic"}
    if premise == "meaningful-Y/F":
        return row.get("F_code") == "F-meaningful"
    if premise == "unaware-capacity":
        return row.get("unaware_capacity") == "supported"
    if premise == "awareness-effect":
        return row.get("awareness_effect") in {"difference-supported", "no-detectable-difference", "equivalence-supported"}
    if premise == "null/no-detectable-difference":
        return row.get("awareness_effect") == "no-detectable-difference"
    if premise == "equivalence":
        return row.get("awareness_effect") == "equivalence-supported"
    if premise == "statistical-inference":
        return row.get("stats_status") == "adequate"
    if premise == "Meyen-role":
        return row.get("Meyen_role") in {"inference-critical", "supplementary"}
    return False


def evidence_bundle_errors(
    experiments: list[dict[str, Any]],
    evidence_bundles: list[dict[str, Any]],
    evidence_links: list[dict[str, Any]],
    paper_ids: set[str],
    auxiliary_ids: set[str],
    experiment_ids: set[str],
    assessment_ids: set[str] | None = None,
) -> list[str]:
    """Validate first-class one-premise bundles and explicit non-transitive links."""
    errors: list[str] = []
    assessment_ids = assessment_ids or set()
    comparisons = {row["comparison_id"]: row for row in experiments}
    bundles = {row["evidence_bundle_id"]: row for row in evidence_bundles}
    links_by_bundle: dict[str, list[dict[str, Any]]] = {}
    for link in evidence_links:
        link_id = link["evidence_link_id"]
        focal_id = link["focal_comparison_id"]
        bundle_id = link["evidence_bundle_id"]
        links_by_bundle.setdefault(bundle_id, []).append(link)
        bundle = bundles.get(bundle_id)
        if bundle is None:
            errors.append(f"evidence_links.csv: {link_id} references missing bundle {bundle_id}")
        elif bundle["focal_comparison_id"] != focal_id:
            errors.append(f"evidence_links.csv: {link_id} focal differs from its bundle focal")
        elif (link.get("member_key") in set(bundle.get("required_member_keys", []))) != (
            link.get("dependency_role") == "required"
        ):
            errors.append(
                f"evidence_links.csv: {link_id} required membership disagrees with bundle manifest"
            )
        focal = comparisons.get(focal_id)
        if focal is None:
            errors.append(f"evidence_links.csv: {link_id} references missing focal comparison {focal_id}")
            continue
        if bundle_id not in focal.get("evidence_bundle_ids", []):
            errors.append(
                f"evidence_links.csv: {link_id} bundle does not match focal comparison "
                f"{focal_id}"
            )
        supporting_paper = link.get("supporting_paper_id")
        if supporting_paper is not None and supporting_paper not in paper_ids:
            errors.append(
                f"evidence_links.csv: {link_id} references missing supporting paper "
                f"{supporting_paper}"
            )
        supporting_experiment = link.get("supporting_experiment_id")
        if supporting_experiment is not None and not supporting_experiment.startswith(
            f"{supporting_paper}_E"
        ):
            errors.append(
                f"evidence_links.csv: {link_id} supporting experiment does not belong to "
                "supporting_paper_id"
            )
        elif supporting_experiment is not None and supporting_experiment not in experiment_ids:
            errors.append(
                f"evidence_links.csv: {link_id} references missing supporting experiment "
                f"{supporting_experiment}"
            )
        supporting_auxiliary = link.get("supporting_auxiliary_id")
        if supporting_auxiliary is not None and supporting_auxiliary not in auxiliary_ids:
            errors.append(
                f"evidence_links.csv: {link_id} references missing auxiliary source "
                f"{supporting_auxiliary}"
            )
        assessment_id = link.get("evidence_assessment_id")
        if assessment_id is not None and assessment_id not in assessment_ids:
            errors.append(f"evidence_links.csv: {link_id} references missing assessment {assessment_id}")

    bundles_by_focal_premise: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for bundle in evidence_bundles:
        bundle_id = bundle["evidence_bundle_id"]
        focal_id = bundle["focal_comparison_id"]
        focal = comparisons.get(focal_id)
        if focal is None:
            errors.append(f"evidence_bundles.csv: {bundle_id} references missing focal {focal_id}")
            continue
        if bundle_id not in focal.get("evidence_bundle_ids", []):
            errors.append(f"evidence_bundles.csv: {bundle_id} is not declared by focal {focal_id}")
        member_links = links_by_bundle.get(bundle_id, [])
        member_keys = [link.get("member_key") for link in member_links]
        if len(member_keys) != len(set(member_keys)):
            errors.append(f"evidence_bundles.csv: {bundle_id} has duplicate member_key values")
        if not member_links:
            errors.append(f"evidence_bundles.csv: {bundle_id} has no explicit evidence links")
        else:
            try:
                validate_declared_bundle_status(bundle, member_links)
            except ValueError as exc:
                errors.append(f"evidence_bundles.csv: {exc}")
        bundles_by_focal_premise.setdefault((focal_id, bundle["supported_premise"]), []).append(bundle)

    for row in experiments:
        focal_id = row["comparison_id"]
        for bundle_id in row.get("evidence_bundle_ids", []):
            if bundle_id not in bundles:
                errors.append(f"experiments_master.csv: {focal_id} declares missing bundle {bundle_id}")
        premises = {
            bundle["supported_premise"] for bundle in evidence_bundles
            if bundle["focal_comparison_id"] == focal_id
        }
        for premise in premises:
            if _premise_is_established(row, premise) and not any(
                bundle["bundle_status"] == "complete"
                for bundle in bundles_by_focal_premise[(focal_id, premise)]
            ):
                errors.append(
                    f"experiments_master.csv: {focal_id} treats {premise} as established "
                    "without a complete independent bundle"
                )
        if row.get("E_code") == "E-diagnostic" and not any(
            bundle["bundle_status"] == "complete"
            for bundle in bundles_by_focal_premise.get((focal_id, "E-diagnostic"), [])
        ):
            errors.append(
                f"experiments_master.csv: {focal_id} assigns E-diagnostic without a complete E-diagnostic bundle"
            )
        for error in factorial_e_diagnostic_bundle_errors(row, evidence_bundles, evidence_links):
            errors.append(f"experiments_master.csv: {error}")
        for error in e_diagnostic_same_y_bundle_errors(row, evidence_bundles, evidence_links):
            errors.append(f"experiments_master.csv: {error}")
        for error in contrast_integrity_bundle_errors(row, evidence_bundles, evidence_links):
            errors.append(f"experiments_master.csv: {error}")
        for error in alternative_control_scan_errors(row):
            errors.append(f"experiments_master.csv: {focal_id}: {error}")
        for error in awareness_result_provenance_errors(row, evidence_bundles, evidence_links):
            errors.append(f"experiments_master.csv: {error}")
    return errors


def read_compatibility_state(run_dir: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        value = json.loads((run_dir / "run_state.json").read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            return None, "run_state.json is not an object"
        return value, None
    except (OSError, json.JSONDecodeError) as exc:
        return None, str(exc)


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

    compatibility_state, compatibility_error = read_compatibility_state(run_dir)
    try:
        config = yaml.safe_load((root / "config.yaml").read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"ERROR: config.yaml: {exc}", file=sys.stderr)
        return 1
    if compatibility_error:
        print(f"ERROR: cannot read compatibility state: {compatibility_error}", file=sys.stderr)
        return 1
    expected_versions = {
        field: config.get(field)
        for field in ("protocol_version", "package_version", "schema_version")
    }
    observed_versions = {
        field: compatibility_state.get(field) if compatibility_state else None
        for field in expected_versions
    }
    if observed_versions != expected_versions:
        print(
            "ERROR: incompatible run package/schema; "
            f"run={observed_versions}, current={expected_versions}. "
            "Historical runs require an explicit migration and are not validated under the current schema.",
            file=sys.stderr,
        )
        return 3

    required = [*CSV_SCHEMAS, "decision_log.jsonl", "run_state.json", "run_summary.md", "fulltexts"]
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
        decisions = load_jsonl_rows(
            decision_path, schemas["decision_log.schema.json"], errors
        )

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
    experiment_groups = tables.get("experiment_groups.csv", [])
    experiments = tables.get("experiments_master.csv", [])
    searches = tables.get("search_log.csv", [])
    discoveries = tables.get("discoveries.csv", [])
    missing = tables.get("missing_texts.csv", [])
    auxiliary = tables.get("auxiliary_sources.csv", [])
    evidence_bundles = tables.get("evidence_bundles.csv", [])
    evidence_links = tables.get("evidence_links.csv", [])
    evidence_assessments = tables.get("evidence_assessments.csv", [])
    fulltext_assets = tables.get("fulltext_assets.csv", [])
    for rows, field, label in (
        (papers, "paper_id", "papers_master.csv"),
        (experiment_groups, "experiment_id", "experiment_groups.csv"),
        (experiments, "comparison_id", "experiments_master.csv"),
        (searches, "search_id", "search_log.csv"),
        (discoveries, "discovery_id", "discoveries.csv"),
        (missing, "paper_id", "missing_texts.csv"),
        (auxiliary, "auxiliary_id", "auxiliary_sources.csv"),
        (evidence_bundles, "evidence_bundle_id", "evidence_bundles.csv"),
        (evidence_links, "evidence_link_id", "evidence_links.csv"),
        (evidence_assessments, "evidence_assessment_id", "evidence_assessments.csv"),
        (fulltext_assets, "fulltext_asset_id", "fulltext_assets.csv"),
        (decisions, "decision_id", "decision_log.jsonl"),
    ):
        check_unique(rows, field, label, errors)
    for filename in (
        "design_eligible_experiments.csv", "constraint_ready_experiments.csv",
        "awareness_linked_differences.csv", "unaware_capacities.csv",
        "no_detectable_awareness_differences.csv",
        "equivalence_supported_no_difference.csv", "unresolved_comparisons.csv",
    ):
        check_unique(tables.get(filename, []), "comparison_id", filename, errors)

    paper_ids = {row["paper_id"] for row in papers}
    experiment_ids = {row["experiment_id"] for row in experiment_groups}
    comparison_ids = {row["comparison_id"] for row in experiments}
    search_ids = {row["search_id"] for row in searches}
    discovery_ids = {row["discovery_id"] for row in discoveries}
    auxiliary_ids = {row["auxiliary_id"] for row in auxiliary}
    evidence_bundle_ids = {row["evidence_bundle_id"] for row in evidence_bundles}
    evidence_link_ids = {row["evidence_link_id"] for row in evidence_links}
    evidence_assessment_ids = {row["evidence_assessment_id"] for row in evidence_assessments}
    fulltext_asset_ids = {row["fulltext_asset_id"] for row in fulltext_assets}
    for row in papers:
        for field in ("first_discovery_parent", "duplicate_of"):
            if row.get(field) is not None and row[field] not in paper_ids:
                errors.append(f"papers_master.csv: {row['paper_id']} references missing {field} {row[field]}")
        if row.get("first_search_id") is not None and row["first_search_id"] not in search_ids:
            errors.append(f"papers_master.csv: {row['paper_id']} references missing first_search_id {row['first_search_id']}")
        paper_groups = [group for group in experiment_groups if group.get("paper_id") == row["paper_id"]]
        for error in paper_citation_node_errors(row, paper_groups):
            errors.append(f"papers_master.csv: {row['paper_id']}: {error}")
    for error in experiment_group_errors(experiment_groups, experiments, paper_ids):
        errors.append(f"experiment_groups.csv: {error}")
    for row in experiments:
        if row["paper_id"] not in paper_ids:
            errors.append(f"experiments_master.csv: {row['comparison_id']} references missing paper {row['paper_id']}")
        if not row["experiment_id"].startswith(f"{row['paper_id']}_E"):
            errors.append(f"experiments_master.csv: {row['comparison_id']} experiment_id does not belong to paper_id")
        if row["experiment_id"] not in experiment_ids:
            errors.append(f"experiments_master.csv: {row['comparison_id']} references missing experiment group")
        if not row["comparison_id"].startswith(f"{row['experiment_id']}_C"):
            errors.append(f"experiments_master.csv: {row['comparison_id']} does not belong to experiment_id {row['experiment_id']}")
        for error in route_audit_errors(row):
            errors.append(f"experiments_master.csv: {row['comparison_id']}: {error}")
        for error in capacity_identity_errors(row):
            errors.append(f"experiments_master.csv: {row['comparison_id']}: {error}")
    for error in functional_structure_errors(experiments):
        errors.append(f"experiments_master.csv: {error}")
    for row in searches:
        if row.get("discovery_route") in {"independent-query", "process-triggered-query"}:
            expected_key = search_window_key(
                execution_phase=row["execution_phase"], source=row["source"],
                query_id=row.get("query_id"), normalized_y_label=row.get("normalized_y_label"),
                canonical_query=row["canonical_query"], source_parameters=row["source_parameters"],
                publication_cutoff=row.get("publication_cutoff"), requested_max_n=row["requested_max_n"],
            )
            if row.get("window_key") != expected_key:
                errors.append(f"search_log.csv: {row['search_id']} window_key does not match immutable parameters")
        if row.get("discovery_route") in {"backward-citation", "forward-citation"}:
            expected_key = citation_window_key(
                parent_paper_id=row["parent_paper_id"], direction=row["index_direction"],
                source=row["source"], source_parameters=row["source_parameters"],
                publication_cutoff=row.get("publication_cutoff"),
                requested_max_n=row.get("requested_max_n"),
            )
            if row.get("window_key") != expected_key:
                errors.append(f"search_log.csv: {row['search_id']} citation window_key does not match immutable parameters")
            expected_direction = row["discovery_route"].removesuffix("-citation")
            if row.get("event_type") != row.get("discovery_route") or row.get("index_direction") != expected_direction:
                errors.append(f"search_log.csv: {row['search_id']} citation event/route/direction disagree")
            expected_parent_status = {
                "core": "core", "strict-bridge": "bridge", "review-anchor": "review-anchor",
                "provisional-core": "provisional-core",
            }.get(row.get("citation_traversal_basis"))
            if row.get("citation_parent_node_status") != expected_parent_status:
                errors.append(f"search_log.csv: {row['search_id']} traversal basis disagrees with parent node status")
        if row.get("parent_paper_id") is not None and row["parent_paper_id"] not in paper_ids:
            errors.append(f"search_log.csv: {row['search_id']} references missing parent paper")
        if row.get("trigger_comparison_id") is not None and row["trigger_comparison_id"] not in comparison_ids:
            errors.append(f"search_log.csv: {row['search_id']} references missing trigger comparison")
    for row in discoveries:
        if row["search_id"] not in search_ids:
            errors.append(f"discoveries.csv: {row['discovery_id']} references missing search {row['search_id']}")
        if row["paper_id"] not in paper_ids:
            errors.append(f"discoveries.csv: {row['discovery_id']} references missing paper {row['paper_id']}")
        search = next((item for item in searches if item["search_id"] == row["search_id"]), None)
        if search is not None:
            expected_depth = 1 if search.get("citation_traversal_basis") == "strict-bridge" else 0
            if row.get("bridge_lineage_depth") != expected_depth:
                errors.append(f"discoveries.csv: {row['discovery_id']} bridge lineage depth differs from its search route")
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
    auxiliary_version_keys: set[tuple[str, str]] = set()
    for row in auxiliary:
        normalized_auxiliary_doi = normalized_doi(row.get("doi"))
        if normalized_auxiliary_doi:
            key = (normalized_auxiliary_doi, row["article_version"])
            if key in auxiliary_version_keys:
                errors.append(f"auxiliary_sources.csv: duplicate logical DOI/version {key}")
            auxiliary_version_keys.add(key)
        local_path = row.get("local_fulltext_path")
        if local_path:
            candidate = Path(local_path)
            candidate = candidate if candidate.is_absolute() else root / candidate
            if not candidate.exists():
                errors.append(f"auxiliary_sources.csv: local_fulltext_path does not exist: {local_path}")
            elif row.get("file_sha256"):
                digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
                if digest != row["file_sha256"]:
                    errors.append(f"auxiliary_sources.csv: SHA-256 mismatch for {local_path}")
    for row in evidence_assessments:
        if row.get("source_paper_id") is not None and row["source_paper_id"] not in paper_ids:
            errors.append(f"evidence_assessments.csv: {row['evidence_assessment_id']} references missing paper")
        if row.get("source_auxiliary_id") is not None and row["source_auxiliary_id"] not in auxiliary_ids:
            errors.append(f"evidence_assessments.csv: {row['evidence_assessment_id']} references missing auxiliary source")
        asset_hash = row.get("source_asset_sha256")
        if asset_hash and row.get("source_paper_id") is not None and not any(
            asset["paper_id"] == row["source_paper_id"] and asset["file_sha256"] == asset_hash
            for asset in fulltext_assets
        ):
            errors.append(f"evidence_assessments.csv: {row['evidence_assessment_id']} source asset hash is not verified for its paper")
        if asset_hash and row.get("source_auxiliary_id") is not None and not any(
            source["auxiliary_id"] == row["source_auxiliary_id"] and source.get("file_sha256") == asset_hash
            for source in auxiliary
        ):
            errors.append(f"evidence_assessments.csv: {row['evidence_assessment_id']} source asset hash is not verified for its auxiliary")
    current_asset_keys: set[tuple[str, str]] = set()
    current_asset_papers: set[str] = set()
    for row in fulltext_assets:
        if row["paper_id"] not in paper_ids:
            errors.append(f"fulltext_assets.csv: {row['fulltext_asset_id']} references missing paper")
        key = (row["paper_id"], row["article_version"])
        if key in current_asset_keys:
            errors.append(f"fulltext_assets.csv: duplicate verified paper/version {key}")
        current_asset_keys.add(key)
        if row.get("current_for_paper"):
            if row["paper_id"] in current_asset_papers:
                errors.append(f"fulltext_assets.csv: multiple current article versions for {row['paper_id']}")
            current_asset_papers.add(row["paper_id"])
        for path_field, hash_field in (
            ("local_fulltext_path", "file_sha256"),
            ("extracted_text_path", "extracted_text_sha256"),
            ("page_map_path", "page_map_sha256"),
        ):
            local_path = row.get(path_field)
            if local_path:
                candidate = Path(local_path)
                candidate = candidate if candidate.is_absolute() else root / candidate
                if not candidate.exists():
                    errors.append(f"fulltext_assets.csv: {path_field} does not exist: {local_path}")
                elif row.get(hash_field):
                    digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
                    if digest != row[hash_field]:
                        errors.append(f"fulltext_assets.csv: {hash_field} mismatch for {local_path}")
    for row in papers:
        if row.get("fulltext_status") in {"retrieved-published", "retrieved-repository", "retrieved-preprint"}:
            if not any(asset["paper_id"] == row["paper_id"] and asset["current_for_paper"] for asset in fulltext_assets):
                errors.append(f"papers_master.csv: {row['paper_id']} has retrieved full text without a verified asset")

    searches_by_id = {row["search_id"]: row for row in searches}
    discoveries_by_search: dict[str, list[dict[str, Any]]] = {}
    for row in discoveries:
        discoveries_by_search.setdefault(row["search_id"], []).append(row)
    completed_window_hashes: dict[str, set[str]] = {}
    completed_blind_counts: dict[tuple[str, str], int] = {}
    completed_process_counts: dict[tuple[str, str], int] = {}
    for row in searches:
        if (
            row.get("requested_max_n") is not None
            and row.get("actual_returned_n") is not None
            and row["actual_returned_n"] > row["requested_max_n"]
        ):
            errors.append(f"search_log.csv: {row['search_id']} returned more than its frozen maximum")
        if row.get("window_status") == "complete":
            if row.get("discovery_route") == "independent-query":
                pair = (row.get("query_id"), row.get("source"))
                completed_blind_counts[pair] = completed_blind_counts.get(pair, 0) + 1
            elif row.get("discovery_route") == "process-triggered-query":
                pair = (row.get("normalized_y_label"), row.get("source"))
                completed_process_counts[pair] = completed_process_counts.get(pair, 0) + 1
            results = sorted(discoveries_by_search.get(row["search_id"], []), key=lambda item: item["result_rank"] or 0)
            if row.get("actual_returned_n") != len(results) or row.get("results_returned") != len(results):
                errors.append(f"search_log.csv: {row['search_id']} completed window count differs from discoveries")
            try:
                digest = ordered_result_set_sha256(results)
                if digest != row.get("result_set_sha256"):
                    errors.append(f"search_log.csv: {row['search_id']} result-set hash mismatch")
            except ValueError as exc:
                errors.append(f"search_log.csv: {row['search_id']}: {exc}")
            completed_window_hashes.setdefault(row["window_key"], set()).add(row["result_set_sha256"])
        elif row.get("window_status") == "reused":
            original = searches_by_id.get(row.get("reused_search_id"))
            if original is None or original.get("window_status") != "complete":
                errors.append(f"search_log.csv: {row['search_id']} reuses a missing/incomplete window")
            elif original.get("result_set_sha256") != row.get("result_set_sha256"):
                errors.append(f"search_log.csv: {row['search_id']} reused hash differs from original")
            if discoveries_by_search.get(row["search_id"]):
                errors.append(f"search_log.csv: {row['search_id']} reran a reused completed window")
    for key, hashes in completed_window_hashes.items():
        if len(hashes) > 1:
            errors.append(f"search_log.csv: completed window {key} has contradictory snapshots")
    for pair, count in completed_blind_counts.items():
        if count > 1:
            errors.append(f"search_log.csv: blind source/family window reran instead of reusing snapshot: {pair}")
    for pair, count in completed_process_counts.items():
        if count > 1:
            errors.append(f"search_log.csv: process source/Y window retriggered: {pair}")

    conservative = ((config.get("search") or {}).get("conservative_execution") or {})
    blind_contract = conservative.get("supplementary_blind_lane") or {}
    active_families = set(blind_contract.get("active_families", []))
    blind_sources = set(blind_contract.get("sources", []))
    complete_blind_pairs: set[tuple[str, str]] = set()
    for row in searches:
        if row.get("discovery_route") == "independent-query":
            if row.get("query_id") not in active_families:
                errors.append(f"search_log.csv: {row['search_id']} uses inactive/unknown blind family")
            if row.get("source") not in blind_sources or row.get("requested_max_n") != 40:
                errors.append(f"search_log.csv: {row['search_id']} violates conservative QCAL source/N=40")
            if row.get("window_status") in {"complete", "reused"}:
                complete_blind_pairs.add((row["query_id"], row["source"]))
        if row.get("discovery_route") == "process-triggered-query":
            process_contract = conservative.get("process_trigger") or {}
            if row.get("source") not in set(process_contract.get("sources", [])) or row.get("requested_max_n") != 50:
                errors.append(f"search_log.csv: {row['search_id']} violates conservative process source/N=50")
    expected_blind_pairs = {(family, source) for family in active_families for source in blind_sources}

    errors.extend(dependency_errors(experiments, evidence_bundles))
    errors.extend(evidence_bundle_errors(
        experiments, evidence_bundles, evidence_links, paper_ids, auxiliary_ids,
        experiment_ids, evidence_assessment_ids,
    ))

    valid_entities = {
        "paper": paper_ids,
        "experiment": experiment_ids,
        "comparison": comparison_ids,
        "search": search_ids,
        "discovery": discovery_ids,
        "missing_text": paper_ids,
        "auxiliary_source": auxiliary_ids,
        "evidence_bundle": evidence_bundle_ids,
        "evidence_link": evidence_link_ids,
        "evidence_assessment": evidence_assessment_ids,
        "fulltext_asset": fulltext_asset_ids,
        "run": {args.run_id},
    }
    for event in decisions:
        if event.get("run_id") != args.run_id:
            errors.append(f"decision_log.jsonl: {event.get('decision_id')} has wrong run_id")
        entity_type = event.get("entity_type")
        if entity_type in valid_entities and event.get("entity_id") not in valid_entities[entity_type]:
            errors.append(f"decision_log.jsonl: {event.get('decision_id')} references missing {entity_type} {event.get('entity_id')}")

    blind_searches = [row for row in searches if row.get("discovery_route") == "independent-query"]
    if blind_searches:
        provisional_events = [
            event for event in decisions
            if event.get("entity_type") == "run"
            and event.get("field") == "workflow_phase"
            and event.get("new_value") == "principal-provisionally-satisfied"
        ]
        first_blind_started = min(row["started_at"] for row in blind_searches)
        if not provisional_events or min(event["timestamp"] for event in provisional_events) > first_blind_started:
            errors.append(
                "decision_log.jsonl: blind lane began before a durable principal-provisionally-satisfied transition"
            )

    if state:
        if state.get("run_id") != args.run_id:
            errors.append("run_state.json: run_id does not match directory")
        for field in ("protocol_version", "package_version", "schema_version"):
            if state.get(field) != config.get(field):
                errors.append(f"run_state.json: {field} differs from config")
        if state.get("registration_status") != config.get("registration_status"):
            errors.append("run_state.json: registration_status differs from config")
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
                ("next_auxiliary_counter", max_suffix(list(auxiliary_ids), "_AUX")),
                ("next_evidence_link_counter", max_suffix(list(evidence_link_ids), "_EL")),
                ("next_evidence_bundle_counter", max_suffix(list(evidence_bundle_ids), "_EB")),
                ("next_evidence_assessment_counter", max_suffix(list(evidence_assessment_ids), "_EA")),
                ("next_fulltext_asset_counter", max_suffix(list(fulltext_asset_ids), "_FT")),
            )
            for field, maximum in counter_checks:
                if state.get(field, 0) <= maximum:
                    errors.append(f"run_state.json: {field} is stale")
        if state.get("status") == "complete":
            for error in completion_errors(state):
                errors.append(f"run_state.json: {error}")
        if state.get("blind_lane_status") == "complete" and complete_blind_pairs != expected_blind_pairs:
            missing_pairs = sorted(expected_blind_pairs - complete_blind_pairs)
            extra_pairs = sorted(complete_blind_pairs - expected_blind_pairs)
            errors.append(
                "run_state.json: blind lane marked complete without exactly the mandatory windows; "
                f"missing={missing_pairs}, extra={extra_pairs}"
            )
        process_complete = {
            (row.get("normalized_y_label"), row.get("source"))
            for row in searches
            if row.get("discovery_route") == "process-triggered-query"
            and row.get("window_status") in {"complete", "reused"}
        }
        process_sources = set(((conservative.get("process_trigger") or {}).get("sources", [])))
        if state.get("process_frontier_status") == "satisfied":
            for label in state.get("activated_normalized_y_labels", []):
                missing_sources = process_sources - {source for y, source in process_complete if y == label}
                if missing_sources:
                    errors.append(
                        f"run_state.json: process frontier satisfied but Y {label!r} lacks sources {sorted(missing_sources)}"
                    )
        completed_keys = set(state.get("completed_search_window_keys", []))
        durable_keys = set(completed_window_hashes)
        if not completed_keys.issubset(durable_keys):
            errors.append("run_state.json: completed_search_window_keys includes no durable complete snapshot")
        eligible_bridges = set(state.get("bridge_depth0_eligible_paper_ids", []))
        pending_bridges = set(state.get("pending_bridge_expansion_paper_ids", []))
        completed_bridges = set(state.get("completed_bridge_expansion_paper_ids", []))
        if not pending_bridges.issubset(eligible_bridges):
            errors.append("run_state.json: pending bridge parents lack a depth-zero eligible lineage")
        if pending_bridges & completed_bridges:
            errors.append("run_state.json: a bridge expansion cannot be both pending and complete")
        bridge_paper_ids = {row["paper_id"] for row in papers if row.get("citation_node_status") == "bridge"}
        if not pending_bridges.issubset(bridge_paper_ids):
            errors.append("run_state.json: pending bridge parents are not currently strict bridge nodes")
        for paper_id in completed_bridges:
            directions = {
                row.get("index_direction") for row in searches
                if row.get("parent_paper_id") == paper_id
                and row.get("citation_traversal_basis") == "strict-bridge"
                and row.get("window_status") in {"complete", "reused"}
            }
            if directions != {"backward", "forward"}:
                errors.append(
                    f"run_state.json: completed bridge parent {paper_id} lacks completed/reused backward and forward windows"
                )

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"PASS: {args.run_id} schemas, CSV encodings, JSONL, IDs, references, hashes, and counters validate.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
