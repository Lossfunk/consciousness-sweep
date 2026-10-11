"""Shared, explicit predicates for the frozen 0.9.0 scientific contract.

Reasons and source-based judgments remain the reviewer's responsibility. These
helpers enforce representation and route boundaries; they do not score science.
"""

from __future__ import annotations

from typing import Any

CONTRASTS = {"aware-unaware", "graded", "probability-regime"}
EMPIRICAL_SCOPES = {"human-target", "linked-other-system"}
SUPPORTED_STATS = {"adequate", "concern"}


def comparable_contrast(row: dict[str, Any]) -> bool:
    return row.get("awareness_contrast_type") in CONTRASTS and row.get("comparison_validity") == "comparable"


def human_profile_comparison(row: dict[str, Any]) -> bool:
    return row.get("population_scope") == "human-target" and comparable_contrast(row)


def array_cell(value: Any) -> list[Any]:
    """One representation for schema-loaded records and quoted CSV arrays."""
    if isinstance(value, str):
        import json
        try:
            value = json.loads(value)
        except (TypeError, ValueError):
            return []
    return value if isinstance(value, list) else []


def strong_contrast_awareness(row: dict[str, Any]) -> bool:
    return row.get("A_code") in {"A-direct", "A-validated"}


def selected_unaware_regimes(row: dict[str, Any]) -> list[dict[str, Any]]:
    keys = array_cell(row.get("unaware_capacity_regime_keys"))
    regimes = array_cell(row.get("awareness_regime_evidence"))
    if (not keys or any(not isinstance(key, str) or not key for key in keys)
            or len(keys) != len(set(keys)) or any(not isinstance(item, dict) for item in regimes)):
        return []
    index = {item.get("regime_key"): item for item in regimes}
    if len(index) != len(regimes) or any(key not in index for key in keys):
        return []
    return [index[key] for key in keys]


def strong_unaware_awareness(row: dict[str, Any]) -> bool:
    regimes = selected_unaware_regimes(row)
    if not regimes:
        return False
    for item in regimes:
        if (item.get("A_code") not in {"A-direct", "A-validated"}
                or item.get("X_content") != row.get("X_label")
                or item.get("critical_result_status") != "reported-supports-unawareness"
                or item.get("awareness_evidence_type") not in {"subjective", "objective-invisibility", "mixed"}
                or any(not str(item.get(key) or "").strip() for key in (
                    "A_reason", "awareness_measure", "critical_result", "source_location"))):
            return False
        origin = item.get("evidence_origin")
        if item["A_code"] == "A-direct" and origin != "focal-task":
            return False
        if origin in {"same-article-transferred", "external-transferred"}:
            if (item["A_code"] != "A-validated" or not item.get("transfer_bundle_id")
                    or item["transfer_bundle_id"] not in array_cell(row.get("evidence_bundle_ids"))
                    or not item.get("transfer_reason") or not item.get("transfer_limitation")):
                return False
        elif origin != "focal-task":
            return False
        if (item.get("awareness_evidence_type") == "objective-invisibility"
                and (item.get("objective_visibility_test_informative") != "yes"
                     or not str(item.get("objective_visibility_test_reason") or "").strip())):
            return False
    return True


def decisive_awareness_regime_keys(row: dict[str, Any], *, contrast_required: bool) -> set[str]:
    if contrast_required:
        return {item["regime_key"] for item in array_cell(row.get("awareness_regime_evidence"))
                if isinstance(item, dict) and isinstance(item.get("regime_key"), str)}
    return {item["regime_key"] for item in selected_unaware_regimes(row)}


def route_viability(row: dict[str, Any]) -> dict[str, bool]:
    base = (
        row.get("population_scope") in EMPIRICAL_SCOPES
        and row.get("F_code") == "F-meaningful"
    )
    return {
        "awareness_effect": base and strong_contrast_awareness(row) and comparable_contrast(row)
        and row.get("E_code") in {"E-matched", "E-diagnostic"},
        "unaware_capacity": base and strong_unaware_awareness(row) and row.get("unaware_condition_tested") == "yes",
    }


def difference_provenance_errors(row: dict[str, Any]) -> list[str]:
    if row.get("difference_tested") != "yes":
        return []
    errors = []
    scope = row.get("difference_analysis_scope")
    members = row.get("difference_joint_experiment_ids") or []
    # CSV views retain array cells as JSON text; validate_run uses typed arrays.
    if isinstance(members, str):
        import json
        try:
            members = json.loads(members)
        except (TypeError, ValueError):
            members = []
    if scope == "focal-experiment":
        if row.get("difference_source_experiment_id") != row.get("experiment_id") or members:
            errors.append("a focal difference must name its own focal experiment and no joint members")
    elif scope == "joint-analysis":
        if (not isinstance(members, list) or len(members) < 2 or len(set(members)) != len(members)
                or row.get("experiment_id") not in members
                or row.get("difference_source_experiment_id") not in members):
            errors.append("joint analysis requires distinct contributing experiments including the focal and source anchor")
    else:
        errors.append("a performed difference requires focal-experiment or joint-analysis scope")
    for field in ("difference_source_location", "difference_statistic_or_test"):
        if not str(row.get(field) or "").strip():
            errors.append(f"a direct same-Y difference requires {field}")
    origin = row.get("difference_analysis_origin")
    if origin not in {"author-reported", "reviewer-derived"}:
        errors.append("a performed difference requires its author-reported or reviewer-derived origin")
    if origin == "reviewer-derived" and not str(row.get("difference_derivation") or "").strip():
        errors.append("reviewer-derived analysis requires located inputs, calculation and assumptions")
    return errors


def fulltext_attempt_required(paper: dict[str, Any]) -> bool:
    return paper.get("abstract_screen") in {"screen-in", "screen-uncertain"} or (
        paper.get("abstract_status") == "unavailable" and paper.get("title_screen") == "retain"
    )


def joint_analysis_bundle_errors(row, bundles, links):
    """A joint result needs direct, premise-specific transfer for every contributor."""
    if row.get("difference_analysis_scope") != "joint-analysis":
        return []
    members = set(row.get("difference_joint_experiment_ids") or [])
    for bundle in bundles:
        if (bundle.get("focal_comparison_id") != row.get("comparison_id")
                or bundle.get("supported_premise") != "awareness-effect"
                or bundle.get("bundle_status") != "complete"):
            continue
        direct = [link for link in links
                  if link.get("evidence_bundle_id") == bundle.get("evidence_bundle_id")
                  and link.get("dependency_role") == "required"
                  and link.get("member_status") == "supports"
                  and link.get("used_for_decision") is True
                  and link.get("same_focal_Y_status") == "yes"]
        if (members and members <= {link.get("supporting_experiment_id") for link in direct}
                and any(link.get("evidence_content_type") == "critical-result" for link in direct)):
            return []
    return ["joint analysis requires a complete awareness-effect transfer bundle with direct required contributors and the critical joint result"]
