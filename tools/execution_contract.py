#!/usr/bin/env python3
"""Pure, network-free enforcement helpers for the draft-0.8.4 execution contract."""

from __future__ import annotations

import copy
import hashlib
import json
from typing import Any, Iterable


TITLE_BATCH_MAX = 25
ABSTRACT_BATCH_MAX = 10
SCIENTIFIC_CODE_FIELDS = {
    "A_code", "E_code", "F_code", "unaware_capacity", "awareness_effect",
    "Meyen_role", "Meyen_status", "stats_status",
}

CONTRAST_INTEGRITY_ANCHORS = {
    "design-imposed-difference", "directly-measured-difference",
    "reported-behavioral-evidence", "manipulation-check-or-control",
    "other-direct-design-evidence",
}
UNMATCHED_E_CODES = {"E-diagnostic", "E-physical-only", "E-uncontrolled"}
COMPLETED_ALTERNATIVE_CONTROL_SCANS = {
    "completed-none-found", "completed-candidate-evaluated",
}
PREFREEZE_DIAGNOSTIC_PREFIX = "PREFREEZE_DIAG_"


def validate_run_id_namespace(run_id: str, *, pre_freeze_diagnostic: bool = False) -> None:
    """Keep future source-bounded diagnostics out of the historical CALIB namespace."""
    if pre_freeze_diagnostic and not run_id.startswith(PREFREEZE_DIAGNOSTIC_PREFIX):
        raise ValueError(
            f"pre-freeze diagnostic RUN_ID must begin {PREFREEZE_DIAGNOSTIC_PREFIX}; "
            "CALIB_* is reserved for historical calibration runs"
        )


def _canonical_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def search_window_key(
    *, execution_phase: str, source: str, query_id: str | None,
    normalized_y_label: str | None, canonical_query: str,
    source_parameters: dict[str, Any], publication_cutoff: str | None,
    requested_max_n: int,
) -> str:
    """Fingerprint one immutable bounded query window before it is executed."""
    if not execution_phase or not source or not canonical_query or requested_max_n < 1:
        raise ValueError("search window requires phase, source, canonical query, and positive maximum N")
    return _canonical_hash({
        "execution_phase": execution_phase,
        "source": source,
        "query_id": query_id,
        "normalized_y_label": normalized_y_label,
        "canonical_query": canonical_query,
        "source_parameters": source_parameters,
        "publication_cutoff": publication_cutoff,
        "requested_max_n": requested_max_n,
    })


def ordered_result_set_sha256(results: Iterable[dict[str, Any]]) -> str:
    """Hash the immutable ordered result identity/rank snapshot."""
    ordered = list(results)
    ranks = [item.get("result_rank") for item in ordered]
    if ranks != list(range(1, len(ordered) + 1)):
        raise ValueError("result snapshot ranks must be contiguous and ordered from one")
    normalized = [
        {
            "result_rank": item["result_rank"],
            "source_stable_id": item.get("source_stable_id"),
            "raw_doi": item.get("raw_doi"),
            "raw_title": item.get("raw_title"),
            "raw_url": item.get("raw_url"),
        }
        for item in ordered
    ]
    return _canonical_hash(normalized)


def reusable_completed_window(search_rows: Iterable[dict[str, Any]], window_key: str) -> dict[str, Any] | None:
    """Return one completed snapshot; reject contradictory completed snapshots."""
    matches = [
        row for row in search_rows
        if row.get("window_key") == window_key and row.get("window_status") in {"complete", "reused"}
    ]
    if not matches:
        return None
    hashes = {row.get("result_set_sha256") for row in matches}
    if None in hashes or len(hashes) != 1:
        raise ValueError("completed search window has missing or contradictory result-set hashes")
    return matches[0]


def semantic_screen_action(paper: dict[str, Any], *, genuinely_new_evidence: bool = False) -> str:
    """Choose screen/reuse/revise; rediscovery alone never requests a rescreen."""
    decided = paper.get("title_screen") in {"retain", "exclude"}
    abstract_decided = paper.get("abstract_screen") in {"screen-in", "screen-uncertain", "screen-out"}
    if genuinely_new_evidence and (decided or abstract_decided):
        return "revise-with-decision-log"
    if decided or abstract_decided:
        return "reuse-existing-decision"
    return "screen-new-logical-paper"


def validate_semantic_batch(kind: str, rows: Iterable[dict[str, Any]]) -> None:
    """Validate context amortization without allowing a batch-level decision."""
    values = list(rows)
    maximum = TITLE_BATCH_MAX if kind == "title" else ABSTRACT_BATCH_MAX if kind == "abstract" else None
    if maximum is None:
        raise ValueError("batch kind must be title or abstract")
    if not values or len(values) > maximum:
        raise ValueError(f"{kind} batch must contain 1..{maximum} logical papers")
    paper_ids = [row.get("paper_id") for row in values]
    if len(set(paper_ids)) != len(paper_ids) or any(not value for value in paper_ids):
        raise ValueError("each batch member requires one unique logical paper_id")
    decision_field = "title_screen" if kind == "title" else "abstract_screen"
    reason_field = f"{decision_field}_reason"
    method_field = f"{decision_field}_method"
    for row in values:
        if not row.get(decision_field) or not str(row.get(reason_field) or "").strip():
            raise ValueError("each batch member requires its own decision and why")
        if row.get(method_field) not in {"agent-semantic", "human-semantic"}:
            raise ValueError("batch screening must remain individual semantic screening")
        if any(field in row for field in ("relevance_score", "embedding_score", "citation_threshold")):
            raise ValueError("numeric/heuristic exclusion fields are prohibited")


def derived_bundle_status(
    links: Iterable[dict[str, Any]], required_member_keys: Iterable[str],
) -> str:
    """Derive complete/incomplete/conflicted from explicit member/dependency states."""
    values = list(links)
    required_keys = set(required_member_keys)
    by_key: dict[str, list[dict[str, Any]]] = {}
    for link in values:
        by_key.setdefault(str(link.get("member_key") or ""), []).append(link)
    if any(link.get("member_status") in {"contradicts", "conflicted"} for link in values):
        return "conflicted"
    if not required_keys:
        return "incomplete"
    if any(len(by_key.get(key, [])) != 1 for key in required_keys):
        return "incomplete"
    required = [by_key[key][0] for key in required_keys]
    if any(
        link.get("dependency_role") != "required"
        or link.get("member_status") != "supports"
        or link.get("used_for_decision") is not True
        for link in required
    ):
        return "incomplete"
    return "complete"


def validate_declared_bundle_status(bundle: dict[str, Any], links: Iterable[dict[str, Any]]) -> None:
    relevant = [link for link in links if link.get("evidence_bundle_id") == bundle.get("evidence_bundle_id")]
    observed = derived_bundle_status(relevant, bundle.get("required_member_keys", []))
    if bundle.get("bundle_status") != observed:
        raise ValueError(
            f"bundle {bundle.get('evidence_bundle_id')} declares {bundle.get('bundle_status')} "
            f"but explicit members derive {observed}"
        )


def route_viability(row: dict[str, Any]) -> dict[str, bool]:
    strong_a = row.get("A_code") in {"A-direct", "A-validated"}
    meaningful_f = row.get("F_code") == "F-meaningful"
    strong_e = row.get("E_code") in {"E-matched", "E-diagnostic"}
    return {
        "awareness_effect": strong_a and meaningful_f and strong_e,
        "unaware_capacity": strong_a and meaningful_f,
    }


def route_audit_errors(row: dict[str, Any]) -> list[str]:
    """Enforce structural route state without changing any scientific category."""
    errors: list[str] = []
    viability = route_viability(row)
    expected_awareness = "viable" if viability["awareness_effect"] else "not-viable"
    expected_capacity = "viable" if viability["unaware_capacity"] else "not-viable"
    if row.get("structural_audit_status") == "complete":
        if row.get("awareness_effect_route_status") != expected_awareness:
            errors.append(f"awareness-effect route must be {expected_awareness} from A/E/F")
        if row.get("unaware_capacity_route_status") != expected_capacity:
            errors.append(f"unaware-capacity route must be {expected_capacity} from A/F; E is not a gate")
        null_status = row.get("null_equivalence_route_status")
        awareness_result = row.get("awareness_effect")
        if awareness_result in {"no-detectable-difference", "equivalence-supported"}:
            if null_status != "required":
                errors.append("no-detectable/equivalence result requires the null/equivalence audit")
        elif not viability["awareness_effect"] and null_status != "not-required":
            errors.append("null/equivalence route must be not-required when no null-oriented result is at issue")
        elif awareness_result == "difference-supported" and null_status != "not-required":
            errors.append("difference-supported result does not require a null/equivalence audit")
    if viability["unaware_capacity"] and row.get("unaware_capacity") == "not-tested":
        errors.append("capacity-viable comparison cannot skip capacity result inspection")
    difference_tested = row.get("difference_tested")
    awareness_result = row.get("awareness_effect")
    if difference_tested == "yes":
        if awareness_result == "not-tested":
            errors.append("a direct same-Y awareness comparison cannot be recorded as not-tested")
        if row.get("result_inspection_status") == "not-required":
            errors.append("a direct same-Y awareness comparison requires descriptive result inspection")
        for field in ("awareness_effect_critical_effect", "awareness_effect_estimate", "awareness_effect_stats_reason"):
            if not str(row.get(field) or "").strip():
                errors.append(f"a direct same-Y awareness comparison requires {field}")
        if row.get("awareness_effect_estimate_interpretable") != "yes":
            errors.append("a direct same-Y awareness comparison requires an interpretable estimate")
        if row.get("awareness_effect_stats_status") not in {"adequate", "concern", "unclear"}:
            errors.append("a direct same-Y awareness comparison requires a nonempty statistical audit")
        if awareness_result == "difference-supported" and not viability["awareness_effect"]:
            errors.append(
                "a significant direct comparison with weak A/E/F must remain awareness-effect unresolved"
            )
    if difference_tested in {"no", "unclear"} and awareness_result in {
        "difference-supported", "no-detectable-difference", "equivalence-supported",
    }:
        errors.append("a conclusive awareness-comparison result requires a direct same-Y test")
    if difference_tested == "not-applicable" and awareness_result not in {None, "not-tested"}:
        errors.append("no direct same-Y comparison permits only not-tested on the awareness-effect axis")
    if any(viability.values()) and row.get("result_inspection_status") == "not-required":
        errors.append("a viable route requires result inspection")
    if not any(viability.values()) and row.get("null_equivalence_route_status") == "not-required":
        if row.get("result_inspection_status") not in {"not-required", "completed-viable-routes"}:
            errors.append("dead routes require an explicit result-inspection disposition")
    return errors


def operational_functional_identity_requires_factorial(
    *, same_information_x: bool, same_downstream_output: bool, same_task_stage: bool,
    factor_changes_x_relation: bool, higher_order_shared_mapping: bool,
    conservative_common_function: bool,
) -> bool:
    """Apply the bounded operational identity questions without using labels or mechanisms."""
    return all((
        same_information_x,
        same_downstream_output,
        same_task_stage,
        factor_changes_x_relation,
        higher_order_shared_mapping,
        conservative_common_function,
    ))


def functional_structure_errors(rows: Iterable[dict[str, Any]]) -> list[str]:
    """Enforce the durable pre-atomization decision without inferring scientific coherence."""
    errors: list[str] = []
    by_experiment: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        by_experiment.setdefault(str(row.get("experiment_id") or ""), []).append(row)

    for experiment_id, experiment_rows in by_experiment.items():
        finalized = [
            row for row in experiment_rows
            if row.get("current_status") == "fully-evaluated"
        ]
        focals = {
            row.get("comparison_id"): row
            for row in finalized
            if row.get("functional_structure_assessment") == "factorial-functional-required"
            and row.get("Y_structure") == "factorial-functional"
        }
        requires_focal = any(
            row.get("functional_structure_assessment") == "factorial-functional-required"
            for row in finalized
        )
        if requires_focal and not focals:
            errors.append(
                f"{experiment_id}: factorial-functional-required assessment lacks a focal comparison"
            )

        for row in finalized:
            comparison_id = str(row.get("comparison_id") or "")
            assessment = row.get("functional_structure_assessment")
            basis = row.get("functional_identity_basis")
            allowed_scalar_bases = {
                "distinct-downstream-outputs", "distinct-computational-stages",
                "distinct-input-output-relations", "no-conservative-common-function",
            }
            if assessment == "factorial-functional-required" and basis != "common-operational-mapping":
                errors.append(
                    f"{comparison_id}: factorial focal/component requires common-operational-mapping basis"
                )
            elif assessment == "scalar-justified" and basis not in allowed_scalar_bases:
                errors.append(
                    f"{comparison_id}: scalar separation requires a positive operational identity basis; "
                    "effect or mechanism labels are insufficient"
                )
            elif assessment == "not-applicable" and basis != "not-applicable-single-effect":
                errors.append(
                    f"{comparison_id}: not-applicable structure requires not-applicable-single-effect basis"
                )
            focal_id = row.get("factorial_focal_comparison_id")
            if focal_id is None:
                continue
            focal = focals.get(focal_id)
            if focal is None:
                errors.append(
                    f"{comparison_id}: linked factorial focal {focal_id} is missing from the same experiment"
                )
                continue
            try:
                focal_order = int(str(focal_id).rsplit("_C", 1)[1])
                component_order = int(comparison_id.rsplit("_C", 1)[1])
            except (IndexError, ValueError):
                continue
            if focal_order >= component_order:
                errors.append(
                    f"{comparison_id}: factorial focal must be instantiated before linked scalar components"
                )

        scalar_rows = [row for row in finalized if row.get("Y_structure") == "scalar"]
        if len(finalized) > 1 and not focals:
            for row in scalar_rows:
                if row.get("functional_structure_assessment") != "scalar-justified":
                    errors.append(
                        f"{row.get('comparison_id')}: multi-row scalar decomposition requires "
                        "a scalar-justified pre-atomization assessment"
                    )
    return errors


def capacity_identity_errors(row: dict[str, Any]) -> list[str]:
    """Enforce one comparison = one focal Y = one possible unaware-capacity target."""
    errors: list[str] = []
    claim = row.get("unaware_capacity_claim")
    focal_y = row.get("Y_label")
    capacity = row.get("unaware_capacity")
    if capacity is not None or claim is not None:
        if not isinstance(claim, str) or not claim.strip():
            errors.append("unaware-capacity assessment requires the focal Y label as its claim")
        elif not isinstance(focal_y, str) or claim != focal_y:
            errors.append("unaware_capacity_claim must exactly equal Y_label; components require their own comparison")
    if capacity == "supported" and row.get("unaware_capacity_evidence_scope") != "whole-focal-Y":
        errors.append("supported unaware capacity requires evidence for the whole focal Y")
    if capacity == "not-tested" and row.get("unaware_capacity_evidence_scope") != "not-applicable":
        errors.append("not-tested unaware capacity requires not-applicable evidence scope")
    return errors


def factorial_e_diagnostic_bundle_errors(
    row: dict[str, Any], bundles: Iterable[dict[str, Any]], links: Iterable[dict[str, Any]],
) -> list[str]:
    """Require a factorial E bundle member that directly addresses the stated alternative."""
    if row.get("Y_structure") != "factorial-functional" or row.get("E_code") != "E-diagnostic":
        return []
    focal_id = row.get("comparison_id")
    complete_bundle_ids = {
        bundle.get("evidence_bundle_id")
        for bundle in bundles
        if bundle.get("focal_comparison_id") == focal_id
        and bundle.get("supported_premise") == "E-diagnostic"
        and bundle.get("bundle_status") == "complete"
    }
    direct_controls = [
        link for link in links
        if link.get("evidence_bundle_id") in complete_bundle_ids
        and link.get("support_role") == "alternative-explanation-control"
        and link.get("dependency_role") == "required"
        and link.get("member_status") == "supports"
        and link.get("used_for_decision") is True
        and link.get("same_focal_Y_status") == "yes"
        and str(link.get("supported_claim") or "").strip()
    ]
    if direct_controls:
        return []
    return [
        f"{focal_id}: factorial E-diagnostic requires a complete bundle with a required, "
        "decision-used alternative-explanation-control member identifying the result that "
        "addresses the first-order-evidence alternative"
    ]


def e_diagnostic_same_y_bundle_errors(
    row: dict[str, Any], bundles: Iterable[dict[str, Any]], links: Iterable[dict[str, Any]],
) -> list[str]:
    """Require decision-used E support to address the same conservative focal Y."""
    if row.get("E_code") != "E-diagnostic":
        return []
    focal_id = row.get("comparison_id")
    complete_ids = {
        bundle.get("evidence_bundle_id")
        for bundle in bundles
        if bundle.get("focal_comparison_id") == focal_id
        and bundle.get("supported_premise") == "E-diagnostic"
        and bundle.get("bundle_status") == "complete"
    }
    if any(
        link.get("evidence_bundle_id") in complete_ids
        and link.get("support_role") in {
            "first-order-evidence-control", "E-diagnostic-support",
            "alternative-explanation-control",
        }
        and link.get("dependency_role") == "required"
        and link.get("member_status") == "supports"
        and link.get("used_for_decision") is True
        and link.get("same_focal_Y_status") == "yes"
        for link in links
    ):
        return []
    return [
        f"{focal_id}: E-diagnostic requires a complete bundle with required, "
        "decision-used support explicitly verified as addressing the same focal Y"
    ]


def contrast_integrity_alternative_is_gating(anchor_type: str | None) -> bool:
    """Only a finite alternative with a direct design/evidential anchor may gate E."""
    return anchor_type in CONTRAST_INTEGRITY_ANCHORS


def alternative_control_scan_errors(row: dict[str, Any]) -> list[str]:
    """Require a durable within-paper scan before unmatched E is finalized."""
    e_code = row.get("E_code")
    status = row.get("alternative_control_scan_status")
    reason = str(row.get("alternative_control_scan_reason") or "").strip()
    errors: list[str] = []
    if e_code in UNMATCHED_E_CODES:
        if status not in COMPLETED_ALTERNATIVE_CONTROL_SCANS | {"incomplete-source-missing"}:
            errors.append("unmatched E requires a bounded within-paper alternative-control scan")
        if not reason:
            errors.append("within-paper alternative-control scan requires a reason")
        if status == "incomplete-source-missing" and row.get("current_status") == "fully-evaluated":
            errors.append("final E is prohibited while a classification-critical within-paper control is unavailable")
    elif e_code == "E-matched" and status != "not-required":
        errors.append("E-matched requires alternative-control scan status not-required")
    return errors


def awareness_result_provenance_errors(
    row: dict[str, Any], bundles: Iterable[dict[str, Any]], links: Iterable[dict[str, Any]],
) -> list[str]:
    """Require strong A to point to an actual procedure-matched supportive result."""
    if row.get("A_code") not in {"A-direct", "A-validated"}:
        return []
    focal_id = row.get("comparison_id")
    errors: list[str] = []
    if row.get("awareness_result_status") != "supportive-result-reported":
        errors.append(f"{focal_id}: strong A requires a supportive critical awareness result")
    for field in (
        "awareness_measure", "awareness_procedure_type", "awareness_result_procedure_type",
        "awareness_result_description", "awareness_result_source_location",
    ):
        if not str(row.get(field) or "").strip() or row.get(field) == "not-applicable":
            errors.append(f"{focal_id}: strong A lacks {field}")
    if (
        row.get("awareness_procedure_type")
        and row.get("awareness_result_procedure_type")
        and row.get("awareness_procedure_type") != row.get("awareness_result_procedure_type")
    ):
        errors.append(f"{focal_id}: awareness result type does not match the recorded procedure")
    if row.get("A_code") == "A-direct":
        if row.get("awareness_result_source_experiment_id") != row.get("experiment_id"):
            errors.append(f"{focal_id}: A-direct result must come from the focal experiment")
        return errors

    complete_bundle_ids = {
        bundle.get("evidence_bundle_id")
        for bundle in bundles
        if bundle.get("focal_comparison_id") == focal_id
        and bundle.get("supported_premise") == "awareness-A"
        and bundle.get("bundle_status") == "complete"
    }
    result_links = [
        link for link in links
        if link.get("evidence_bundle_id") in complete_bundle_ids
        and link.get("support_role") == "awareness-validation"
        and link.get("evidence_content_type") == "critical-result"
        and link.get("dependency_role") == "required"
        and link.get("member_status") == "supports"
        and link.get("used_for_decision") is True
        and str(link.get("source_location") or "").strip()
        and str(link.get("transfer_reason") or "").strip()
        and str(link.get("transfer_limitation") or "").strip()
        and (
            (
                row.get("awareness_result_source_experiment_id") is not None
                and link.get("supporting_experiment_id")
                == row.get("awareness_result_source_experiment_id")
            )
            or (
                row.get("awareness_result_source_experiment_id") is None
                and link.get("supporting_auxiliary_id") is not None
            )
        )
    ]
    if not result_links:
        errors.append(
            f"{focal_id}: A-validated requires a complete awareness-A bundle with a required, "
            "decision-used, result-bearing member and explicit transfer assessment"
        )
    return errors


def contrast_integrity_bundle_errors(
    row: dict[str, Any], bundles: Iterable[dict[str, Any]], links: Iterable[dict[str, Any]],
) -> list[str]:
    """Reject E-diagnostic only for finite, directly anchored unresolved alternatives."""
    if row.get("E_code") != "E-diagnostic":
        return []
    focal_id = row.get("comparison_id")
    relevant = [
        bundle for bundle in bundles
        if bundle.get("focal_comparison_id") == focal_id
        and bundle.get("supported_premise") == "E-diagnostic"
    ]
    errors: list[str] = []
    for bundle in relevant:
        bundle_id = bundle.get("evidence_bundle_id")
        resolution = bundle.get("contrast_integrity_resolution")
        anchor_type = bundle.get("contrast_integrity_anchor_type")
        anchor_location = str(bundle.get("contrast_integrity_anchor_source_location") or "").strip()
        member_key = bundle.get("contrast_integrity_control_member_key")
        if resolution in {"ruled-out", "unresolved"} and (
            not contrast_integrity_alternative_is_gating(anchor_type) or not anchor_location
        ):
            errors.append(
                f"{focal_id}: contrast-integrity alternative in {bundle_id} lacks an "
                "independent design/evidential anchor and cannot gate E"
            )
            continue
        if resolution in {"ruled-out", "unresolved"} and member_key not in bundle.get(
            "required_member_keys", []
        ):
            errors.append(
                f"{focal_id}: contrast-integrity control member for {bundle_id} must be declared required"
            )
        if resolution == "unresolved":
            errors.append(
                f"{focal_id}: E-diagnostic prohibited because bundle {bundle_id} has an unresolved "
                "design-motivated task-state/policy alternative"
            )
            if not any(
                link.get("evidence_bundle_id") == bundle_id
                and link.get("member_key") == member_key
                for link in links
            ):
                errors.append(
                    f"{focal_id}: unresolved contrast-integrity alternative in {bundle_id} lacks "
                    "its explicitly identified evidence/control member"
                )
        elif resolution == "ruled-out":
            controls = [
                link for link in links
                if link.get("evidence_bundle_id") == bundle_id
                and link.get("member_key") == member_key
                and link.get("support_role") == "alternative-explanation-control"
                and link.get("dependency_role") == "required"
                and link.get("member_status") == "supports"
                and link.get("used_for_decision") is True
                and link.get("same_focal_Y_status") == "yes"
            ]
            if not controls:
                errors.append(
                    f"{focal_id}: ruled-out contrast-integrity alternative in {bundle_id} lacks "
                    "its required, decision-used control member"
                )
        elif resolution != "not-applicable":
            errors.append(f"{focal_id}: E-diagnostic bundle {bundle_id} lacks contrast-integrity resolution")
    return errors


def reopen_for_blind_discovery(
    state: dict[str, Any], *, citation_node: bool = False, genuinely_new_y: str | None = None,
) -> dict[str, Any]:
    """Reopen only the frontiers activated by a genuinely new blind-lane result."""
    updated = copy.deepcopy(state)
    reopened = False
    if citation_node:
        updated["citation_frontier_status"] = "reopened"
        reopened = True
    if genuinely_new_y:
        activated = updated.setdefault("activated_normalized_y_labels", [])
        if genuinely_new_y not in activated:
            activated.append(genuinely_new_y)
            updated["process_frontier_status"] = "reopened"
            reopened = True
    if reopened:
        updated["workflow_phase"] = "reopened-frontiers"
    return updated


def completion_errors(state: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if state.get("blind_lane_status") != "complete":
        errors.append("mandatory supplementary blind lane is incomplete")
    if state.get("citation_frontier_status") != "satisfied":
        errors.append("citation frontier is not satisfied")
    if state.get("process_frontier_status") != "satisfied":
        errors.append("process frontier is not satisfied")
    if state.get("workflow_phase") not in {"final-validation", "complete"}:
        errors.append("workflow has not reached final validation")
    return errors


def reusable_evidence_assessment(
    assessments: Iterable[dict[str, Any]], *, source_paper_id: str | None,
    source_auxiliary_id: str | None, factual_premise: str, regime_fingerprint: str,
    source_asset_sha256: str | None, source_location: str,
) -> dict[str, Any] | None:
    """Reuse facts only for an exact source/premise/regime match; never return codes."""
    for assessment in assessments:
        if any(field in assessment for field in SCIENTIFIC_CODE_FIELDS):
            raise ValueError("execution assessment illegally contains scientific classifications")
        if (
            assessment.get("source_paper_id") == source_paper_id
            and assessment.get("source_auxiliary_id") == source_auxiliary_id
            and assessment.get("factual_premise") == factual_premise
            and assessment.get("regime_fingerprint") == regime_fingerprint
            and assessment.get("source_asset_sha256") == source_asset_sha256
            and assessment.get("source_location") == source_location
        ):
            return assessment
    return None


def reusable_fulltext_asset(
    assets: Iterable[dict[str, Any]], *, paper_id: str, article_version: str,
    extraction_tool: str | None = None, extraction_version: str | None = None,
) -> dict[str, Any] | None:
    """Reuse only the verified logical paper/version; extraction reuse also needs tool/version."""
    for asset in assets:
        if (
            asset.get("paper_id") == paper_id
            and asset.get("article_version") == article_version
            and asset.get("current_for_paper") is True
        ):
            result = copy.deepcopy(asset)
            result["reuse_extraction"] = bool(
                extraction_tool
                and extraction_version
                and asset.get("extraction_tool") == extraction_tool
                and asset.get("extraction_version") == extraction_version
                and asset.get("extracted_text_path")
            )
            return result
    return None
