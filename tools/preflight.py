#!/usr/bin/env python3
"""Audit immutable sweep inputs without modifying them."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

from leakage_guard import registered_leakage_errors

try:
    import yaml
    from jsonschema import Draft202012Validator
except ModuleNotFoundError as exc:
    print(
        "ERROR: missing repository dependency "
        f"{exc.name!r}. Run: python3 tools/bootstrap_env.py --venv .venv\n"
        "Then use: .venv/bin/python tools/preflight.py --mode pre-freeze",
        file=sys.stderr,
    )
    raise SystemExit(3) from None


ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = (
    "papers.schema.json",
    "experiments.schema.json",
    "search_log.schema.json",
    "discoveries.schema.json",
    "missing_texts.schema.json",
    "auxiliary_sources.schema.json",
    "evidence_bundles.schema.json",
    "evidence_links.schema.json",
    "evidence_assessments.schema.json",
    "fulltext_assets.schema.json",
    "decision_log.schema.json",
    "run_state.schema.json",
)


def enum_values(node: object) -> set[str]:
    values: set[str] = set()
    if isinstance(node, dict):
        enum = node.get("enum")
        if isinstance(enum, list):
            values.update(value for value in enum if isinstance(value, str))
        for value in node.values():
            values.update(enum_values(value))
    elif isinstance(node, list):
        for value in node:
            values.update(enum_values(value))
    return values


def read_csv(path: Path, expected_headers: list[str], errors: list[str]) -> None:
    try:
        with path.open(newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames != expected_headers:
                errors.append(f"{path.name}: headers differ from contract")
            ids: set[str] = set()
            for line_number, row in enumerate(reader, start=2):
                if None in row:
                    errors.append(f"{path.name}:{line_number}: inconsistent column count")
                seed_id = (row.get("seed_id") or "").strip()
                if not seed_id:
                    errors.append(f"{path.name}:{line_number}: missing seed_id")
                elif seed_id in ids:
                    errors.append(f"{path.name}:{line_number}: duplicate seed_id {seed_id}")
                ids.add(seed_id)
                if not (row.get("seed_reason") or "").strip():
                    errors.append(f"{path.name}:{line_number}: missing seed_reason")
    except (OSError, csv.Error) as exc:
        errors.append(f"{path.name}: {exc}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("pre-freeze", "registered"), default="registered")
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    root = args.root.resolve()
    errors: list[str] = []
    blockers: list[str] = []

    required_paths = [
        "AGENTS.md", "PROTOCOL.md", "seeds_empirical.csv", "seeds_reviews.csv",
        "queries.md", "config.yaml", "requirements.txt", "schemas", "tools", "runs",
        "outputs/consolidated",
    ]
    for relative in required_paths:
        if not (root / relative).exists():
            errors.append(f"missing required path: {relative}")

    try:
        config = yaml.safe_load((root / "config.yaml").read_text(encoding="utf-8"))
        if not isinstance(config, dict):
            raise ValueError("top-level YAML value is not an object")
    except (OSError, yaml.YAMLError, ValueError) as exc:
        errors.append(f"config.yaml: {exc}")
        config = {}

    schemas: dict[str, dict] = {}
    for name in SCHEMAS:
        path = root / "schemas" / name
        try:
            schema = json.loads(path.read_text(encoding="utf-8"))
            Draft202012Validator.check_schema(schema)
            schemas[name] = schema
        except Exception as exc:
            errors.append(f"schemas/{name}: {exc}")

    read_csv(
        root / "seeds_empirical.csv",
        ["seed_id", "title", "authors", "year", "doi", "url", "seed_reason", "notes"],
        errors,
    )
    read_csv(
        root / "seeds_reviews.csv",
        ["seed_id", "title", "authors", "year", "doi", "url", "coverage_area", "seed_reason", "notes"],
        errors,
    )
    errors.extend(registered_leakage_errors(root))

    protocol_version = config.get("protocol_version")
    for name in ("AGENTS.md", "PROTOCOL.md"):
        try:
            text = (root / name).read_text(encoding="utf-8")
            if not protocol_version or str(protocol_version) not in text:
                errors.append(f"{name}: does not declare config protocol_version {protocol_version!r}")
        except OSError as exc:
            errors.append(f"{name}: {exc}")

    for version_field in ("protocol_version", "package_version", "schema_version"):
        value = config.get(version_field)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"config.yaml: missing non-empty {version_field}")

    expected_categories = {
        "A-direct", "A-validated", "A-transfer-risk", "A-absent",
        "subjective", "objective-invisibility", "mixed", "none",
        "E-matched", "E-diagnostic", "E-physical-only", "E-uncontrolled",
        "F-meaningful", "F-ambiguous", "F-not-meaningful",
        "supported", "not-supported", "unclear", "not-tested",
        "difference-supported", "no-detectable-difference", "equivalence-supported", "unresolved",
        "scalar", "factorial-functional",
        "not-assessed", "scalar-justified", "factorial-functional-required",
        "Meyen-satisfied", "Meyen-failed", "Meyen-unassessable",
        "inference-critical", "supplementary", "not-applicable",
        "active-matching-or-titration", "equivalence-procedure",
        "supports-equivalence", "does-not-support-equivalence",
        "region-not-stated",
    }
    experiment_categories = enum_values(schemas.get("experiments.schema.json", {}))
    missing = sorted(expected_categories - experiment_categories)
    if missing:
        errors.append(f"experiments schema lacks protocol categories: {', '.join(missing)}")

    experiment_properties = schemas.get("experiments.schema.json", {}).get("properties", {})
    for field in (
        "comparison_id", "evidence_bundle_ids", "structural_audit_status",
        "awareness_effect_route_status", "unaware_capacity_route_status",
        "null_equivalence_route_status", "result_inspection_status",
        "awareness_evidence_type", "objective_visibility_test_informative",
        "critical_dependency_status", "E_matching_basis", "E_equivalence_margin", "E_equivalence_result",
        "E_competing_account", "E_competing_prediction", "E_violating_pattern", "E_same_Y_reason",
        "E_diagnostic_source_locations", "functional_structure_assessment",
        "functional_structure_reason", "factorial_focal_comparison_id",
        "Y_structure", "factorial_component_effects",
        "unaware_capacity_claim", "unaware_capacity", "unaware_capacity_stats_status", "awareness_effect",
        "awareness_effect_stats_status", "awareness_effect_critical_effect",
        "Y_evidence_role", "mechanistic_interpretation", "mechanism_clarity",
        "null_equivalence_margin", "null_equivalence_result", "null_BF01",
        "null_CI_region", "null_CI_entirely_within_region", "Meyen_role",
    ):
        if field not in experiment_properties:
            errors.append(f"experiments schema lacks required comparison/audit field: {field}")
    search_properties = schemas.get("search_log.schema.json", {}).get("properties", {})
    if "trigger_comparison_id" not in search_properties:
        errors.append("search-log schema lacks trigger_comparison_id")
    state_properties = schemas.get("run_state.schema.json", {}).get("properties", {})
    if "next_comparison_counters" not in state_properties:
        errors.append("run-state schema lacks next_comparison_counters")
    for field in (
        "package_version", "schema_version", "next_auxiliary_counter",
        "next_evidence_link_counter", "next_evidence_bundle_counter",
        "next_evidence_assessment_counter", "next_fulltext_asset_counter",
        "workflow_phase", "blind_lane_status", "citation_frontier_status",
        "process_frontier_status", "activated_normalized_y_labels",
        "completed_search_window_keys",
    ):
        if field not in state_properties:
            errors.append(f"run-state schema lacks {field}")
    paper_properties = schemas.get("papers.schema.json", {}).get("properties", {})
    for field in (
        "abstract_status", "title_screen_method", "title_screen_rule_id",
        "abstract_screen_method", "abstract_screen_rule_id",
    ):
        if field not in paper_properties:
            errors.append(f"papers schema lacks {field}")
    missing_properties = schemas.get("missing_texts.schema.json", {}).get("properties", {})
    for field in ("obtained_at", "obtained_wave", "obtained_by", "acquisition_route"):
        if field not in missing_properties:
            errors.append(f"missing-text schema lacks source-neutral field {field}")
    auxiliary_properties = schemas.get("auxiliary_sources.schema.json", {}).get("properties", {})
    for field in ("auxiliary_id", "citation", "identity_reason", "article_version", "retrieval_status"):
        if field not in auxiliary_properties:
            errors.append(f"auxiliary-source schema lacks {field}")
    bundle_properties = schemas.get("evidence_bundles.schema.json", {}).get("properties", {})
    for field in (
        "evidence_bundle_id", "focal_comparison_id", "supported_premise",
        "premise_description", "required_member_keys", "bundle_status", "bundle_reason",
    ):
        if field not in bundle_properties:
            errors.append(f"evidence-bundle schema lacks {field}")
    evidence_properties = schemas.get("evidence_links.schema.json", {}).get("properties", {})
    for field in (
        "evidence_link_id", "evidence_bundle_id", "focal_comparison_id",
        "member_key", "supporting_experiment_id", "supporting_auxiliary_id", "evidence_assessment_id",
        "support_role", "dependency_role", "member_status",
        "supported_claim", "transfer_reason", "transfer_limitation", "source_location",
    ):
        if field not in evidence_properties:
            errors.append(f"evidence-link schema lacks {field}")
    if (config.get("identifiers") or {}).get("comparison_separator") != "_C":
        errors.append("config identifiers.comparison_separator must be '_C'")
    if (config.get("identifiers") or {}).get("auxiliary_separator") != "_AUX":
        errors.append("config identifiers.auxiliary_separator must be '_AUX'")
    if (config.get("identifiers") or {}).get("evidence_link_separator") != "_EL":
        errors.append("config identifiers.evidence_link_separator must be '_EL'")
    if (config.get("identifiers") or {}).get("evidence_bundle_separator") != "_EB":
        errors.append("config identifiers.evidence_bundle_separator must be '_EB'")
    if (config.get("identifiers") or {}).get("evidence_assessment_separator") != "_EA":
        errors.append("config identifiers.evidence_assessment_separator must be '_EA'")
    if (config.get("identifiers") or {}).get("fulltext_asset_separator") != "_FT":
        errors.append("config identifiers.fulltext_asset_separator must be '_FT'")

    conservative = ((config.get("search") or {}).get("conservative_execution") or {})
    blind = conservative.get("supplementary_blind_lane") or {}
    expected_families = ["QCAL4-ATTN", "QCAL4-META", "QCAL4-BIND", "QCAL4-MEM", "QCAL4-DEC"]
    if blind.get("active_families") != expected_families:
        errors.append("conservative blind lane must activate exactly ATTN/META/BIND/MEM/DEC")
    if blind.get("sources") != ["OpenAlex", "Europe PMC"]:
        errors.append("conservative blind lane must retain OpenAlex and Europe PMC")
    if blind.get("max_results_per_source_family") != 40 or blind.get("max_windows_per_source_family") != 1:
        errors.append("conservative blind lane must use one N=40 window per source/family")
    if "QCAL4-LEARN" not in blind.get("disabled_families", []):
        errors.append("pathological QCAL4-LEARN rendering must remain disabled")
    process = conservative.get("process_trigger") or {}
    if process.get("sources") != ["OpenAlex", "Europe PMC"] or process.get("max_results_per_source_y") != 50:
        errors.append("process trigger must use OpenAlex and Europe PMC at N=50/source/Y")

    for key, relative in (config.get("paths") or {}).items():
        if not (root / str(relative)).exists():
            errors.append(f"config paths.{key} does not exist: {relative}")

    registration_status = config.get("registration_status")
    if registration_status not in {"frozen", "preregistered", "registered"}:
        blockers.append(f"registration_status is {registration_status!r}, not frozen/registered")
    if config.get("publication_cutoff") is None:
        blockers.append("publication_cutoff is null")
    search = config.get("search") or {}
    if not search.get("preferred_sources"):
        blockers.append("search.preferred_sources is empty")
    if not search.get("fallback_order"):
        blockers.append("search.fallback_order is empty")
    try:
        query_text = (root / "queries.md").read_text(encoding="utf-8")
        if "DRAFT" in query_text or "TO FREEZE" in query_text or "{{" in query_text:
            blockers.append("queries.md still contains draft/template markers")
    except OSError as exc:
        errors.append(f"queries.md: {exc}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(f"PASS: immutable inputs parse; {len(schemas)} schemas pass Draft 2020-12 meta-validation.")
    print("PASS: seed CSV headers/rows and protocol categorical consistency validate.")
    if blockers:
        label = "BLOCKER" if args.mode == "registered" else "PRE-FREEZE TODO"
        for blocker in blockers:
            print(f"{label}: {blocker}")
    if args.mode == "registered" and blockers:
        return 2
    print("PASS: preflight mode completed without modifying inputs.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
