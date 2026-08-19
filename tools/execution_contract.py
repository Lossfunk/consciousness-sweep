#!/usr/bin/env python3
"""Pure, network-free enforcement helpers for the draft-0.8 execution contract."""

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
    if viability["awareness_effect"] and row.get("awareness_effect") == "not-tested":
        errors.append("awareness-effect-viable comparison cannot skip its result audit")
    if any(viability.values()) and row.get("result_inspection_status") == "not-required":
        errors.append("a viable route requires result inspection")
    if not any(viability.values()) and row.get("null_equivalence_route_status") == "not-required":
        if row.get("result_inspection_status") not in {"not-required", "completed-viable-routes"}:
            errors.append("dead routes require an explicit result-inspection disposition")
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
