#!/usr/bin/env python3
"""Audit immutable sweep inputs without modifying them."""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
from importlib.metadata import PackageNotFoundError, version as installed_version
from pathlib import Path

from leakage_guard import registered_leakage_errors
from execution_contract import publication_policy_errors
from package_release import verify_release, release_readiness_errors

try:
    import yaml
    from jsonschema import Draft202012Validator
except ModuleNotFoundError as exc:
    print(
        "ERROR: missing repository dependency "
        f"{exc.name!r}. Run: python3 tools/bootstrap_env.py --venv .venv\n"
        "Then use: .venv/bin/python tools/preflight.py --mode registered",
        file=sys.stderr,
    )
    raise SystemExit(3) from None


ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = (
    "papers.schema.json",
    "experiment_groups.schema.json",
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
    "postrun_handoff.schema.json",
    "postrun_human_decision.schema.json",
)


def runtime_errors(requirements: Path, *, platform_name: str | None = None,
                   python_version: tuple[int, ...] | None = None, version_lookup=installed_version) -> list[str]:
    """Check the supported interpreter/platform and exact canonical dependency pins."""
    errors: list[str] = []
    if (platform_name or os.name) != "posix":
        errors.append("supported runtime requires a POSIX Unix environment; native Windows is unsupported")
    if (python_version or tuple(sys.version_info[:3])) < (3, 9):
        errors.append("supported runtime requires Python >=3.9")
    try:
        lines = requirements.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        return errors + [f"cannot read canonical dependency pins: {exc}"]
    for line in lines:
        text = line.split("#", 1)[0].strip()
        if not text:
            continue
        match = re.fullmatch(r"([A-Za-z0-9_.-]+)(?:\[[^]]+\])?==([^\s]+)", text)
        if not match:
            errors.append(f"canonical requirement is not an exact supported pin: {text}")
            continue
        package, expected = match.groups()
        try:
            actual = version_lookup(package)
        except PackageNotFoundError:
            errors.append(f"missing dependency {package}; run python3 tools/bootstrap_env.py --venv .venv")
            continue
        if actual != expected:
            errors.append(f"dependency {package} version {actual!r} differs from canonical {expected!r}; rerun canonical bootstrap")
    return errors


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
    errors: list[str] = runtime_errors(root / "requirements.txt")
    blockers: list[str] = []
    if args.mode == "registered":
        errors.extend(release_readiness_errors(root))
    if (root / "RELEASE_MANIFEST.json").exists():
        try:
            diagnostic_manifest = json.loads((root / "RELEASE_MANIFEST.json").read_text(encoding="utf-8")).get("purpose") == "pre-freeze-diagnostic"
        except (OSError, ValueError, AttributeError):
            diagnostic_manifest = False  # verifier supplies the located error
        errors.extend(verify_release(root, pre_freeze_diagnostic=(args.mode == "pre-freeze" and diagnostic_manifest)))

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
    runtime = config.get("runtime") or {}
    if runtime.get("python_minimum") != "3.9" or runtime.get("platforms") != ["posix"]:
        errors.append("config runtime must declare Python >=3.9 and POSIX support")

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
    from prepare_vetted_seeds import seed_scope_errors
    from render_fulltext_review import verify as verify_fulltext_rendering
    errors.extend(seed_scope_errors(root, config))
    errors.extend(verify_fulltext_rendering(root))

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
        "scalar", "factorial-functional", "null-supported", "graded", "probability-regime",
        "human-target", "linked-other-system", "post-hoc-performance-matching",
        "joint-analysis", "reviewer-derived", "not-comparable",
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
        "population_scope", "population_scope_reason", "awareness_contrast_type",
        "awareness_regime_evidence", "partial_x_residual_status",
        "partial_x_residual_reason", "partial_x_residual_source_location",
        "unaware_condition_tested", "comparison_validity", "comparison_validity_reason",
        "difference_analysis_scope", "difference_joint_experiment_ids",
        "difference_analysis_origin", "difference_derivation", "evidence_strength_reason",
        "awareness_effect_route_status", "unaware_capacity_route_status",
        "null_equivalence_route_status", "result_inspection_status",
        "awareness_evidence_type", "awareness_procedure_type", "objective_visibility_test_informative",
        "awareness_result_reporting", "awareness_result_support", "awareness_result_procedure_type",
        "awareness_result_description", "awareness_result_source_location",
        "awareness_result_source_experiment_id",
        "critical_dependency_status", "E_matching_basis", "E_equivalence_margin", "E_equivalence_result",
        "E_competing_account", "E_competing_prediction", "E_violating_pattern", "E_same_Y_reason",
        "E_diagnostic_source_locations", "alternative_control_scan_status",
        "alternative_control_scan_reason", "functional_structure_assessment",
        "functional_identity_basis", "functional_structure_reason", "factorial_focal_comparison_id",
        "Y_structure", "factorial_component_effects", "Y_functional_status", "Y_functional_reason",
        "unaware_capacity_claim", "unaware_capacity_evidence_scope", "unaware_capacity", "unaware_capacity_stats_status", "awareness_effect",
        "awareness_effect_stats_status", "awareness_effect_critical_effect",
        "difference_source_experiment_id", "difference_source_location", "difference_statistic_or_test",
        "Y_evidence_role", "mechanistic_interpretation", "mechanism_clarity",
        "null_equivalence_margin", "null_equivalence_result", "null_BF01",
        "null_CI_region", "null_CI_entirely_within_region", "Meyen_role",
    ):
        if field not in experiment_properties:
            errors.append(f"experiments schema lacks required comparison/audit field: {field}")
    group_properties = schemas.get("experiment_groups.schema.json", {}).get("properties", {})
    for field in (
        "experiment_id", "paper_id", "experiment_label", "source_location",
        "physical_experiment_description", "pre_atomization_assessed",
        "citation_specific_x", "citation_awareness_attempt", "citation_functional_y",
        "bridge_near_neighbor", "bridge_disposition", "bridge_failed_ingredient",
        "bridge_rationale",
        "functional_structure_assessment", "functional_structure_reason",
        "disposition", "disposition_reason", "linked_comparison_ids", "support_roles",
    ):
        if field not in group_properties:
            errors.append(f"experiment-group schema lacks {field}")
    search_properties = schemas.get("search_log.schema.json", {}).get("properties", {})
    if "trigger_comparison_id" not in search_properties:
        errors.append("search-log schema lacks trigger_comparison_id")
    for field in (
        "citation_parent_node_status", "citation_parent_bridge_depth", "citation_traversal_basis",
    ):
        if field not in search_properties:
            errors.append(f"search-log schema lacks {field}")
    for field in ("citation_parent_node_status", "citation_traversal_basis"):
        if "fixed-empirical-seed" not in search_properties.get(field, {}).get("enum", []):
            errors.append(f"search-log schema lacks fixed empirical seed {field}")
    discovery_properties = schemas.get("discoveries.schema.json", {}).get("properties", {})
    for field in ("bridge_lineage_depth", "bridge_lineage_reason"):
        if field not in discovery_properties:
            errors.append(f"discoveries schema lacks {field}")
    state_properties = schemas.get("run_state.schema.json", {}).get("properties", {})
    if "next_comparison_counters" not in state_properties:
        errors.append("run-state schema lacks next_comparison_counters")
    for field in (
        "package_version", "schema_version", "next_auxiliary_counter",
        "next_evidence_link_counter", "next_evidence_bundle_counter",
        "next_evidence_assessment_counter", "next_fulltext_asset_counter",
        "workflow_phase", "blind_lane_status", "citation_frontier_status",
        "process_frontier_status", "activated_normalized_y_labels",
        "bridge_depth0_eligible_paper_ids", "pending_bridge_expansion_paper_ids",
        "completed_bridge_expansion_paper_ids",
        "completed_search_window_keys",
    ):
        if field not in state_properties:
            errors.append(f"run-state schema lacks {field}")
    paper_properties = schemas.get("papers.schema.json", {}).get("properties", {})
    for field in (
        "abstract_status", "abstract_text", "abstract_sha256",
        "abstract_source", "abstract_obtained_at",
        "title_screen_method", "title_screen_rule_id",
        "abstract_screen_method", "abstract_screen_rule_id",
        "bridge_empirical_status", "citation_node_status", "citation_node_reason",
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
        "contrast_integrity_alternative", "contrast_integrity_viability_reason",
        "contrast_integrity_anchor_type", "contrast_integrity_anchor_source_location",
        "contrast_integrity_prediction", "contrast_integrity_control_member_key",
        "contrast_integrity_resolution", "contrast_integrity_resolution_reason",
    ):
        if field not in bundle_properties:
            errors.append(f"evidence-bundle schema lacks {field}")
    evidence_properties = schemas.get("evidence_links.schema.json", {}).get("properties", {})
    for field in (
        "evidence_link_id", "evidence_bundle_id", "focal_comparison_id",
        "member_key", "supporting_experiment_id", "supporting_auxiliary_id", "evidence_assessment_id",
        "support_role", "dependency_role", "evidence_content_type", "same_focal_Y_status", "member_status",
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
    from query_instruments import BLIND_QUERY_FAMILIES
    expected_families = list(BLIND_QUERY_FAMILIES)
    if blind.get("active_families") != expected_families:
        errors.append("conservative blind lane must match the prepared targeted and function-agnostic families")
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
    errors.extend(publication_policy_errors(config))
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
