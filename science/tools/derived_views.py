"""Pure comparison-view selection shared by derivation and validation."""

from __future__ import annotations

from typing import Any
from scientific_policy import (route_viability, difference_provenance_errors, human_profile_comparison, SUPPORTED_STATS, EMPIRICAL_SCOPES, strong_contrast_awareness)


def completed_result_audit(row: dict[str, Any]) -> bool:
    return (
        row.get("current_status") == "fully-evaluated"
        and row.get("structural_audit_status") == "complete"
        and row.get("result_inspection_status") == "completed-viable-routes"
    )


def awareness_design_eligible(row: dict[str, Any]) -> bool:
    return (
        row.get("current_status") in {"design-coded", "fully-evaluated"}
        and route_viability(row)["awareness_effect"]
    )


def audited_functional_y(row: dict[str, Any]) -> bool:
    return row.get("Y_functional_status") in {
        "downstream-function", "coherent-functional-mapping",
    }


def focal_difference_provenance(row: dict[str, Any]) -> bool:
    return row.get("difference_tested") == "yes" and not difference_provenance_errors(row)


def constraint_awareness_difference(row: dict[str, Any]) -> bool:
    return (
        completed_result_audit(row)
        and awareness_design_eligible(row)
        and row["awareness_effect"] == "difference-supported"
        and row["awareness_effect_stats_status"] in SUPPORTED_STATS
        and row["difference_tested"] == "yes"
        and focal_difference_provenance(row)
    )


def constraint_unaware_capacity(row: dict[str, Any]) -> bool:
    return (
        completed_result_audit(row)
        and route_viability(row)["unaware_capacity"]
        and audited_functional_y(row)
        and bool(str(row.get("unaware_capacity_claim") or "").strip())
        and row.get("unaware_capacity_claim") == row.get("Y_label")
        and row.get("unaware_capacity_evidence_scope") == "whole-focal-Y"
        and row["unaware_capacity"] == "supported"
        and row["unaware_capacity_stats_status"] in SUPPORTED_STATS
    )


def constraint_equivalence_supported(row: dict[str, Any]) -> bool:
    return (
        completed_result_audit(row)
        and awareness_design_eligible(row)
        and audited_functional_y(row)
        and row["awareness_effect"] == "equivalence-supported"
        and row["awareness_effect_stats_status"] in SUPPORTED_STATS
        and row["difference_tested"] == "yes"
        and focal_difference_provenance(row)
        and row["null_evidence_adequacy"] == "adequate"
    )


def no_detectable_awareness_difference(row: dict[str, Any]) -> bool:
    return (
        row.get("current_status") == "fully-evaluated"
        and row["awareness_effect"] == "no-detectable-difference"
    )


def unresolved_comparison(row: dict[str, Any]) -> bool:
    return row.get("current_status") == "fully-evaluated" and (
        row["unaware_capacity"] == "unclear" or row["awareness_effect"] == "unresolved"
    )


def constraint_null_supported(row: dict[str, Any]) -> bool:
    return (completed_result_audit(row) and awareness_design_eligible(row)
            and audited_functional_y(row) and row.get("awareness_effect") == "null-supported"
            and row.get("awareness_effect_stats_status") in SUPPORTED_STATS
            and focal_difference_provenance(row) and row.get("null_evidence_adequacy") == "adequate")


def main_finding(row: dict[str, Any]) -> bool:
    # An unaware capacity alone does not establish an awareness comparison.
    return human_profile_comparison(row) and (
        constraint_awareness_difference(row) or (strong_contrast_awareness(row) and constraint_unaware_capacity(row))
        or constraint_equivalence_supported(row) or constraint_null_supported(row))


def supplementary_evidence(row: dict[str, Any]) -> bool:
    return (row.get("current_status") == "fully-evaluated"
            and row.get("population_scope") in EMPIRICAL_SCOPES
            and row.get("F_code") in {"F-meaningful", "F-ambiguous"}
            and not main_finding(row))


def process_search_eligible(row: dict[str, Any]) -> bool:
    return awareness_design_eligible(row) or constraint_unaware_capacity(row)


design_eligible = awareness_design_eligible
DERIVED_PREDICATES = {
    "design_eligible_experiments.csv": awareness_design_eligible,
    "constraint_ready_experiments.csv": main_finding,
    "awareness_linked_differences.csv": constraint_awareness_difference,
    "unaware_capacities.csv": constraint_unaware_capacity,
    "no_detectable_awareness_differences.csv": no_detectable_awareness_difference,
    "equivalence_supported_no_difference.csv": constraint_equivalence_supported,
    "bayesian_null_supported.csv": constraint_null_supported,
    "supplementary_evidence.csv": supplementary_evidence,
    "unresolved_comparisons.csv": unresolved_comparison,
}


def derive_views(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    ordered = sorted(rows, key=lambda row: (row["paper_id"], row["experiment_id"], row["comparison_id"]))
    return {name: [row for row in ordered if predicate(row)]
            for name, predicate in DERIVED_PREDICATES.items()}


def derived_view_errors(
    masters: list[dict[str, Any]], tables: dict[str, list[dict[str, Any]]],
) -> list[str]:
    return [f"{name}: derived rows differ from the current master (membership, content, or order); regenerate outputs"
            for name, expected in derive_views(masters).items()
            if tables.get(name) != expected]
