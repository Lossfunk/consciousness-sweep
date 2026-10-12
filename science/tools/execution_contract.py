#!/usr/bin/env python3
"""Pure, network-free enforcement helpers retained for the 0.9.2 candidate."""

from __future__ import annotations

import copy
import hashlib
import json
from datetime import date, datetime
from typing import Any, Iterable


def publication_policy_errors(config: dict[str, Any]) -> list[str]:
    """Distinguish an explicit unrestricted search from an unfinished date policy."""
    policy = config.get("publication_date_policy")
    cutoff = config.get("publication_cutoff")
    if policy == "unrestricted":
        return [] if cutoff is None else ["unrestricted publication policy requires a null cutoff"]
    if policy == "fixed-cutoff":
        try:
            if not isinstance(cutoff, str) or date.fromisoformat(cutoff).isoformat() != cutoff:
                raise ValueError
        except ValueError:
            return ["fixed-cutoff publication policy requires an ISO YYYY-MM-DD date"]
        return []
    return ["publication_date_policy must explicitly be unrestricted or fixed-cutoff"]


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
BRIDGE_INGREDIENT_FIELDS = (
    "citation_specific_x", "citation_awareness_attempt", "citation_functional_y",
)


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


def scientific_regime_fingerprint(state: dict[str, Any]) -> str:
    """Bind reusable scientific evidence to this exact frozen run package.

    Excludes changing counters, timestamps and harness fields. Hashes are already
    recorded at initialization and independently compared with files on disk.
    """
    return _canonical_hash({key: state.get(key) for key in (
        "protocol_version", "package_version", "schema_version", "immutable_inputs_sha256",
    )})


def scientific_promotion_routes(row: dict[str, Any]) -> dict[str, bool]:
    """Select source-review obligations using the unchanged scientific predicates."""
    from derived_views import (constraint_awareness_difference, constraint_equivalence_supported,
                               constraint_null_supported, constraint_unaware_capacity)
    # The CSV predicate's empty claim is a blank string; schema-loaded rows use
    # None. Preserve that representation equivalence without changing its gate.
    row = dict(row, unaware_capacity_claim=row.get("unaware_capacity_claim") or "")
    return {
        "awareness_constraint": any(predicate(row) for predicate in (
            constraint_awareness_difference, constraint_equivalence_supported, constraint_null_supported)),
        "unaware_capacity": constraint_unaware_capacity(row),
    }


def scientific_promotion_binding(row: dict[str, Any], state: dict[str, Any],
                                 tables: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    """Bind a typed comparison and its direct support to current source versions.

    The full comparison is bound conservatively, including reasons/limitations.
    No dynamic counters or unrelated papers enter the binding. The normal run
    validator independently verifies these source records against files on disk.
    """
    cid = row["comparison_id"]
    bundles = [item for item in tables.get("evidence_bundles.csv", []) if item["focal_comparison_id"] == cid]
    links = [item for item in tables.get("evidence_links.csv", []) if item["focal_comparison_id"] == cid]
    paper_ids = {row["paper_id"]} | {item.get("supporting_paper_id") for item in links}
    auxiliary_ids = {item.get("supporting_auxiliary_id") for item in links}
    assessment_ids = {item.get("evidence_assessment_id") for item in links}
    assessments = [item for item in tables.get("evidence_assessments.csv", [])
                   if item["evidence_assessment_id"] in assessment_ids]
    paper_ids |= {item.get("source_paper_id") for item in assessments}
    auxiliary_ids |= {item.get("source_auxiliary_id") for item in assessments}
    experiment_ids = {row["experiment_id"]} | set(row.get("difference_joint_experiment_ids") or []) | {item.get("supporting_experiment_id") for item in links}
    assets = [item for item in tables.get("fulltext_assets.csv", [])
              if item["paper_id"] in paper_ids and item.get("current_for_paper") is True]
    if not any(item["paper_id"] == row["paper_id"] for item in assets):
        raise ValueError("strong comparison requires its current verified focal source asset")
    auxiliary = [item for item in tables.get("auxiliary_sources.csv", []) if item["auxiliary_id"] in auxiliary_ids]
    payload = {
        "scientific_regime_fingerprint": scientific_regime_fingerprint(state),
        "comparison": row,
        "bundles": sorted(bundles, key=lambda item: item["evidence_bundle_id"]),
        "links": sorted(links, key=lambda item: item["evidence_link_id"]),
        "assets": sorted(assets, key=lambda item: item["fulltext_asset_id"]),
        "auxiliary": sorted(auxiliary, key=lambda item: item["auxiliary_id"]),
        "assessments": sorted(assessments, key=lambda item: item["evidence_assessment_id"]),
        "experiment_groups": sorted((item for item in tables.get("experiment_groups.csv", []) if item["experiment_id"] in experiment_ids), key=lambda item: item["experiment_id"]),
    }
    source_ids = sorted([item["fulltext_asset_id"] for item in assets]
                        + [item["auxiliary_id"] for item in auxiliary if item.get("file_sha256")])
    # A conservative binding may include unused alternatives. Source-first
    # coverage is the focal source plus sources actually used for a decision
    # and all required members of those needed premises, not every inventory ID.
    required_source_ids = {item["fulltext_asset_id"] for item in assets if item["paper_id"] == row["paper_id"]}
    needed_bundles = {item.get("evidence_bundle_id") for item in links if item.get("used_for_decision") is True}
    assessments_by_id = {item["evidence_assessment_id"]: item for item in assessments}

    def require_source(paper_id, auxiliary_id, *, expected_hash=None):
        sources = ([item for item in auxiliary if item["auxiliary_id"] == auxiliary_id]
                   if auxiliary_id else [item for item in assets if item["paper_id"] == paper_id])
        sources = [item for item in sources if item.get("file_sha256")
                   and (expected_hash is None or item["file_sha256"] == expected_hash)]
        if not sources or (not paper_id and not auxiliary_id):
            raise ValueError("decision-used or required premise lacks its current verified source/hash")
        required_source_ids.update(item["auxiliary_id"] if auxiliary_id else item["fulltext_asset_id"] for item in sources)

    for link in links:
        if not (link.get("used_for_decision") is True or
                (link.get("dependency_role") == "required" and link.get("evidence_bundle_id") in needed_bundles)):
            continue
        require_source(link.get("supporting_paper_id"), link.get("supporting_auxiliary_id"))
        if link.get("evidence_assessment_id"):
            assessment = assessments_by_id.get(link["evidence_assessment_id"])
            if not assessment or not assessment.get("source_asset_sha256"):
                raise ValueError("decision-used or required factual assessment lacks its verified source/hash")
            require_source(assessment.get("source_paper_id"), assessment.get("source_auxiliary_id"),
                           expected_hash=assessment["source_asset_sha256"])
    return {"binding_sha256": _canonical_hash(payload),
            "scientific_regime_fingerprint": payload["scientific_regime_fingerprint"],
            "source_ids": source_ids, "required_source_ids": sorted(required_source_ids)}


def scientific_source_reading_binding(source_ids: list[str], state: dict[str, Any],
                                      tables: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    """Bind a neutral source-only reading to identities/versions, without A/E/F.

    This receipt validates recorded chronology and immutable source identity. It
    cannot prove that an actor read independently or interpreted a source well.
    """
    if not source_ids or len(source_ids) != len(set(source_ids)):
        raise ValueError("source-only reading needs nonempty, unique source IDs")
    available = {}
    for item in tables.get("fulltext_assets.csv", []):
        if item.get("current_for_paper") is True:
            available[item["fulltext_asset_id"]] = item
    for item in tables.get("auxiliary_sources.csv", []):
        if item.get("file_sha256"):
            available[item["auxiliary_id"]] = item
    if any(source_id not in available for source_id in source_ids):
        raise ValueError("source-only reading names a missing or noncurrent verified source")
    sources = [available[source_id] for source_id in sorted(source_ids)]
    return {"scientific_regime_fingerprint": scientific_regime_fingerprint(state),
            "source_reading_binding_sha256": _canonical_hash({
                "scientific_regime_fingerprint": scientific_regime_fingerprint(state),
                "sources": sources}),
            "source_ids": sorted(source_ids),
            "source_hashes": {source_id: available[source_id]["file_sha256"]
                              for source_id in sorted(source_ids)}}


def statistical_review_scope(row: dict[str, Any]) -> dict[str, Any]:
    """Identify the actual focal analyses; this never chooses an inference route.

    Kept inside the existing statistics check, not a second classification
    store. The full comparison binding also includes scientific reasons/codes.
    Nulls stay typed so absence is not silently replaced by a reported result.
    """
    fields = (
        "comparison_id", "Y_label", "difference_tested", "difference_analysis_scope",
        "difference_source_experiment_id", "difference_joint_experiment_ids",
        "difference_statistic_or_test", "awareness_effect_estimate",
        "unaware_capacity_critical_effect", "null_evidence_strength",
        "null_evidence_adequacy",
    )
    return {key: copy.deepcopy(row.get(key)) for key in fields}


def scientific_promotion_review_errors(rows: list[dict[str, Any]], state: dict[str, Any],
                                       tables: dict[str, list[dict[str, Any]]],
                                       decisions: list[dict[str, Any]], *,
                                       required_comparison_ids: Iterable[str] = ()) -> list[str]:
    """Require a separate source checker before strong scientific export.

    Role records document actual workers/humans; this validates provenance and
    separation, never a model's identity, capability or truthfulness.
    """
    required = set(required_comparison_ids)
    errors = [f"{cid}: reading recommendation names a missing comparison"
              for cid in sorted(required - {row['comparison_id'] for row in rows})]
    indexed = {event["decision_id"]: (index, event) for index, event in enumerate(decisions)}
    roles = {}
    for index, event in enumerate(decisions):
        if event.get("entity_type") == "run" and event.get("field") == "scientific_review_role":
            value = event.get("new_value")
            if isinstance(value, dict) and value.get("role_id"):
                roles.setdefault(value["role_id"], []).append((index, value))

    def role(role_id, expected, before):
        registrations = roles.get(role_id, []) if isinstance(role_id, str) else []
        if len(registrations) != 1:
            return None
        index, value = registrations[0]
        if (index >= before or value.get("role") != expected
                or value.get("actor_kind") not in {"agent-worker", "human"}
                or not str(value.get("actor_id") or "").strip()
                or not str(value.get("provenance_reference") or "").strip()):
            return None
        return value

    for row in rows:
        routes = scientific_promotion_routes(row)
        if not any(routes.values()) and row['comparison_id'] not in required:
            continue
        cid = row["comparison_id"]
        prefix = f"{cid}: scientific promotion review "
        try:
            binding = scientific_promotion_binding(row, state, tables)
        except ValueError as exc:
            errors.append(prefix + str(exc))
            continue
        matches = [(index, event) for index, event in enumerate(decisions)
                   if event.get("entity_type") == "comparison" and event.get("entity_id") == cid
                   and event.get("field") == "scientific_promotion_review"]
        if not matches:
            errors.append(prefix + "is missing; obtain an independent source check before strong export")
            continue
        review_index, review = matches[-1]
        value = review.get("new_value")
        if not isinstance(value, dict):
            errors.append(prefix + "payload must be an object")
            continue
        if any(value.get(key) != binding[key] for key in ("binding_sha256", "scientific_regime_fingerprint")):
            errors.append(prefix + "has stale or wrong comparison/source/version/regime binding")
        primary_id = value.get("primary_assessment_decision_id")
        primary_index, primary = indexed.get(primary_id, (-1, {})) if isinstance(primary_id, str) else (-1, {})
        assessment = primary.get("new_value")
        assessment = assessment if isinstance(assessment, dict) else {}
        if (primary_index < 0 or primary_index >= review_index
                or primary.get("entity_type") != "comparison" or primary.get("entity_id") != cid
                or primary.get("field") != "scientific_primary_assessment"
                or any(assessment.get(key) != binding[key] for key in ("binding_sha256", "scientific_regime_fingerprint"))):
            errors.append(prefix + "lacks a preceding primary assessment of this exact bound snapshot")
        assessor = role(assessment.get("role_id"), "primary-assessor", primary_index)
        checker = role(value.get("reviewer_role_id"), "source-checker", review_index)
        if (not assessor or not checker or assessor["role_id"] == checker["role_id"]
                or assessor["actor_id"] == checker["actor_id"]
                or primary.get("agent") != assessor["actor_id"] or review.get("agent") != checker["actor_id"]):
            errors.append(prefix + "requires distinct registered assessor/checker actors with matching event provenance")
        # A source-first instruction is an execution obligation, not a new
        # eligibility threshold. Require its durable receipt and recorded label
        # disclosure sequence instead of accepting a free-text claim afterward.
        source_id = value.get("source_interpretation_decision_id")
        source_index, source_event = indexed.get(source_id, (-1, {})) if isinstance(source_id, str) else (-1, {})
        source_reading = source_event.get("new_value")
        source_reading = source_reading if isinstance(source_reading, dict) else {}
        if (source_index < 0 or source_index >= review_index
                or source_event.get("entity_type") != "comparison" or source_event.get("entity_id") != cid
                or source_event.get("field") != "scientific_source_interpretation"
                or not checker or source_event.get("agent") != checker["actor_id"]
                or not role(value.get("reviewer_role_id"), "source-checker", source_index)
                or source_reading.get("proposed_labels_seen") is not False):
            errors.append(prefix + "lacks a preceding checker source-only interpretation receipt")
        else:
            source_ids = source_reading.get("source_ids")
            try:
                if not isinstance(source_ids, list) or any(not isinstance(item, str) for item in source_ids):
                    raise ValueError("source IDs must be a list of strings")
                source_binding = scientific_source_reading_binding(source_ids, state, tables)
                if any(source_reading.get(key) != source_binding[key] for key in source_binding):
                    raise ValueError("source/version/hash/regime receipt is stale or mismatched")
                focal_sources = {item["fulltext_asset_id"] for item in tables.get("fulltext_assets.csv", [])
                                 if item.get("paper_id") == row["paper_id"] and item.get("current_for_paper") is True}
                if not focal_sources.intersection(source_ids):
                    raise ValueError("receipt does not include a verified focal source")
                if not set(binding["required_source_ids"]) <= set(source_ids):
                    raise ValueError("source-only receipt omits current decision-used or required premise sources")
            except ValueError as exc:
                errors.append(prefix + str(exc))
            for key in ("awareness_measured_content", "conservative_task_function"):
                if not str(source_reading.get(key) or "").strip():
                    errors.append(prefix + "source-only receipt must independently state measured awareness content and task function")
            if (not isinstance(source_reading.get("source_locations"), list)
                    or not source_reading["source_locations"]
                    or any(not isinstance(item, str) or not item.strip() for item in source_reading["source_locations"])
                    or not str(source_event.get("source_location") or "").strip()):
                errors.append(prefix + "source-only receipt lacks decisive source locations")
            from statistical_consistency import statistics_observation_errors
            errors.extend(prefix + error for error in statistics_observation_errors(
                source_reading.get("critical_statistics")))
        disclosure_id = value.get("labels_disclosed_decision_id")
        disclosure_index, disclosure = indexed.get(disclosure_id, (-1, {})) if isinstance(disclosure_id, str) else (-1, {})
        disclosed = disclosure.get("new_value")
        disclosed = disclosed if isinstance(disclosed, dict) else {}
        if (not source_index < disclosure_index < review_index or not primary_index < disclosure_index
                or disclosure.get("entity_type") != "comparison" or disclosure.get("entity_id") != cid
                or disclosure.get("field") != "scientific_labels_disclosed"
                or not checker or disclosure.get("agent") != checker["actor_id"]
                or disclosed.get("source_interpretation_decision_id") != source_id
                or disclosed.get("primary_assessment_decision_id") != primary_id
                or any(disclosed.get(key) != binding[key] for key in ("binding_sha256", "scientific_regime_fingerprint"))):
            errors.append(prefix + "lacks recorded source-before-label-disclosure chronology for this snapshot")
        if checker and any(
            index < source_index and event.get("entity_type") == "comparison"
            and event.get("entity_id") == cid and event.get("agent") == checker["actor_id"]
            and event.get("field") in {"scientific_primary_assessment", "scientific_labels_disclosed", "scientific_promotion_review"}
            for index, event in enumerate(decisions)
        ):
            errors.append(prefix + "source-only receipt follows this actor's recorded label exposure; use a new independent actor or retain an unresolved postlabel review")
        if value.get("disposition") not in {"confirmed", "unresolved", "correction-needed"}:
            errors.append(prefix + "disposition must be confirmed, unresolved or correction-needed")
        elif value["disposition"] != "confirmed":
            errors.append(prefix + "is not confirmed; append an explicit scientific revision before strong export")
        checks = value.get("checks")
        if not isinstance(checks, dict):
            errors.append(prefix + "requires source-focused checks")
            continue
        arms = checks.get("exact_x_awareness_by_arm")
        from scientific_policy import decisive_awareness_regime_keys
        expected_arms = decisive_awareness_regime_keys(row,
            contrast_required=routes["awareness_constraint"] or cid in required)
        if (not isinstance(arms, list) or not expected_arms
                or any(not isinstance(item, dict) for item in arms)
                or len({item.get("regime_key") for item in arms}) != len(arms)
                or not expected_arms <= {item.get("regime_key") for item in arms}
                or not {item.get("regime_key") for item in arms} <= {item["regime_key"] for item in row.get("awareness_regime_evidence", [])}):
            errors.append(prefix + "must inspect exact X against awareness test/results in every recorded arm required by the current claim")
            arms = []
        for arm in arms:
            if any(not str(arm.get(key) or "").strip() for key in ("focal_X", "awareness_tested_content", "critical_awareness_result")):
                errors.append(prefix + "arm check must state focal X, tested content and critical result separately")
            if arm.get("focal_X") != row.get("X_label"):
                errors.append(prefix + "arm check names a different focal X from the current comparison")
            regime = next((item for item in row.get("awareness_regime_evidence", [])
                           if item.get("regime_key") == arm.get("regime_key")), {})
            if arm.get("regime_key") in expected_arms and regime.get("evidence_origin") in {"same-article-transferred", "external-transferred"}:
                pointer = regime.get("transfer_bundle_id")
                result_links = [item for item in tables.get("evidence_links.csv", [])
                                if item.get("focal_comparison_id") == cid
                                and item.get("evidence_bundle_id") == pointer
                                and item.get("dependency_role") == "required"
                                and item.get("evidence_content_type") == "critical-result"
                                and item.get("used_for_decision") is True]
                source_covered = bool(result_links)
                for link in result_links:
                    if link.get("supporting_auxiliary_id"):
                        sources = {link["supporting_auxiliary_id"]}
                    else:
                        sources = {asset["fulltext_asset_id"] for asset in tables.get("fulltext_assets.csv", [])
                                   if asset.get("paper_id") == link.get("supporting_paper_id")
                                   and asset.get("current_for_paper") is True}
                    arm_sources = arm.get("source_ids")
                    if (not sources or not isinstance(arm_sources, list)
                            or not sources.intersection(arm_sources)):
                        source_covered = False
                if not source_covered:
                    errors.append(prefix + "transferred arm check must cover its required critical-result sources")
        prior_ids = source_reading.get("source_ids")
        prior_ids = set(prior_ids) if isinstance(prior_ids, list) and all(isinstance(item, str) for item in prior_ids) else set()
        for arm in arms:
            if (arm.get("verdict") not in {"supported", "contradicted", "unresolved"}
                    or not str(arm.get("reason") or "").strip()
                    or not isinstance(arm.get("source_locations"), list) or not arm["source_locations"]
                    or any(not isinstance(pointer, str) or not pointer.strip() for pointer in arm["source_locations"])
                    or not isinstance(arm.get("source_ids"), list) or not arm["source_ids"]
                    or any(source not in binding["source_ids"] or source not in prior_ids for source in arm["source_ids"])):
                errors.append(prefix + "has an unlocated or wrong-source optional/decisive arm check")
        required_checks = [arm for arm in arms if arm.get("regime_key") in expected_arms]
        prior_source_ids = source_reading.get("source_ids")
        prior_source_ids = set(prior_source_ids) if isinstance(prior_source_ids, list) and all(isinstance(item, str) for item in prior_source_ids) else set()
        for key in ("distinct_whole_y", "statistics_limitations"):
            required_checks.append(checks.get(key))
        statistics = checks.get("statistics_limitations")
        if not isinstance(statistics, dict):
            errors.append(prefix + "requires a comparison-specific statistics check")
        else:
            if statistics.get("focal_analysis_scope") != statistical_review_scope(row):
                errors.append(prefix + "statistics check names a different or stale comparison/function/critical analysis")
            source_statistics = statistics.get("source_statistics")
            from statistical_consistency import statistics_observation_errors
            errors.extend(prefix + error for error in statistics_observation_errors(source_statistics))
            if source_statistics != source_reading.get("critical_statistics"):
                errors.append(prefix + "statistics check changes the prior source-only statistical observations after disclosure")
            if not isinstance(statistics.get("materiality"), str) or statistics.get("materiality") not in {"supports-scoped-claim", "nonfatal-qualified", "critical-unresolved"}:
                errors.append(prefix + "statistics check must distinguish nonfatal qualifications from critical uncertainty")
            elif statistics["materiality"] == "critical-unresolved" and value.get("disposition") == "confirmed":
                errors.append(prefix + "cannot confirm a claim whose critical statistics remain unresolved")
        if routes["awareness_constraint"]:
            required_checks.append(checks.get("same_y_e"))
        for check in required_checks:
            if (not isinstance(check, dict) or check.get("verdict") != "supported"
                    or not str(check.get("reason") or "").strip()
                    or not isinstance(check.get("source_locations"), list) or not check["source_locations"]
                    or any(not isinstance(pointer, str) or not pointer.strip() for pointer in check["source_locations"])
                    or not isinstance(check.get("source_ids"), list) or not check["source_ids"]
                    or any(source not in binding["source_ids"] for source in check["source_ids"])):
                errors.append(prefix + "has an unsupported, unlocated or wrong-source decisive check")
                break
            if any(source not in prior_source_ids for source in check["source_ids"]):
                errors.append(prefix + "decisive check uses a source absent from the prior source-only receipt")
                break
        if not str(value.get("reason") or "").strip() or not str(review.get("source_location") or "").strip():
            errors.append(prefix + "requires a source location and reason")
    return errors


READING_CLAIM_FIELDS = (
    "run_id", "paper_id", "tier", "claim_basis", "claim_comparison_id", "asset_id",
    "X", "Y", "measured_outcome", "result_direction", "claim", "source_location",
    "limitation", "manuscript_contribution", "evidence_level_comparison",
    "claim_review", "claim_review_reason", "reviewed_by", "reason", "redundancy_note",
)


def scientific_reading_claim_binding(item: dict[str, Any], row: dict[str, Any],
                                     state: dict[str, Any],
                                     tables: dict[str, list[dict[str, Any]]]) -> dict[str, str]:
    """Bind the exact recommendation to the existing scientific/source snapshot.

    The checker reviews these authored assertions, including their functional
    scope. This hash records what was reviewed; it does not establish truth.
    """
    binding = scientific_promotion_binding(row, state, tables)
    return {key: binding[key] for key in ("binding_sha256", "scientific_regime_fingerprint")} | {
        "claim_sha256": _canonical_hash({key: item.get(key) for key in READING_CLAIM_FIELDS})}


def scientific_reading_claim_review(item: dict[str, Any], row: dict[str, Any],
                                  state: dict[str, Any], tables: dict[str, list[dict[str, Any]]],
                                  decisions: list[dict[str, Any]]) -> dict[str, Any]:
    """Require a current, separately checked primary/support recommendation.

    Weak-E support is a recommendation obligation, not a new scientific route.
    An unresolved check blocks the recommendation while narrower scientific
    exports and earned discovery routes remain unchanged.
    """
    cid = row["comparison_id"]
    errors = scientific_promotion_review_errors([row], state, tables, decisions,
                                               required_comparison_ids=[cid])
    if errors:
        raise ValueError("; ".join(errors))
    science = [(index, event) for index, event in enumerate(decisions)
               if event.get("entity_type") == "comparison" and event.get("entity_id") == cid
               and event.get("field") == "scientific_promotion_review"][-1]
    matches = [(index, event) for index, event in enumerate(decisions)
               if event.get("entity_type") == "comparison" and event.get("entity_id") == cid
               and event.get("field") == "scientific_reading_claim_review"
               and isinstance(event.get("new_value"), dict)
               and event["new_value"].get("claim_sha256") == scientific_reading_claim_binding(item, row, state, tables)["claim_sha256"]]
    if not matches:
        raise ValueError(f"{cid}: exact reading claim lacks an independent source review")
    index, event = matches[-1]
    value = event["new_value"]
    expected = scientific_reading_claim_binding(item, row, state, tables)
    if any(value.get(key) != expected[key] for key in expected):
        raise ValueError(f"{cid}: reading claim/source/comparison/regime review is stale")
    if (index <= science[0] or value.get("scientific_promotion_review_decision_id") != science[1]["decision_id"]
            or event.get("agent") != science[1].get("agent") or item.get("reviewed_by") != event.get("agent")):
        raise ValueError(f"{cid}: reading claim must follow and reference the current independent checker review")
    if value.get("disposition") != "confirmed":
        raise ValueError(f"{cid}: reading claim is unresolved or needs correction")
    check = value.get("checks")
    if not isinstance(check, dict):
        raise ValueError(f"{cid}: reading claim lacks located claim/function/analysis checks")
    source_ids = scientific_promotion_binding(row, state, tables)["source_ids"]
    interpretation_id = science[1]["new_value"]["source_interpretation_decision_id"]
    interpretation = next(event for event in decisions if event["decision_id"] == interpretation_id)
    read_sources = interpretation["new_value"]["source_ids"]
    for key in ("same_function_awareness_comparison", "claim_scope"):
        member = check.get(key)
        if (not isinstance(member, dict) or member.get("verdict") != "supported"
                or not str(member.get("reason") or "").strip()
                or not isinstance(member.get("source_locations"), list) or not member["source_locations"]
                or any(not isinstance(pointer, str) or not pointer.strip() for pointer in member["source_locations"])
                or not isinstance(member.get("source_ids"), list) or not member["source_ids"]
                or any(source not in source_ids or source not in read_sources for source in member["source_ids"])):
            raise ValueError(f"{cid}: reading claim has an unsupported, unlocated or wrong-source {key}")
    actual = check["same_function_awareness_comparison"]
    if actual.get("awareness_comparison_established") is not True:
        raise ValueError(f"{cid}: an actual awareness comparison is not established; discrimination groups alone are insufficient")
    if (actual.get("statistic_or_test") != row.get("difference_statistic_or_test")
            or actual.get("analysis_scope") != row.get("difference_analysis_scope")
            or actual.get("source_experiment_id") != row.get("difference_source_experiment_id")):
        raise ValueError(f"{cid}: reading claim check identifies a different functional analysis")
    scope = check["claim_scope"]
    for key in ("X", "Y", "measured_outcome", "result_direction"):
        if scope.get(key) != item.get(key):
            raise ValueError(f"{cid}: reading claim check identifies a different {key}")
    if item.get("asset_id") not in source_ids or item.get("asset_id") not in read_sources:
        raise ValueError(f"{cid}: reading claim cites a source absent from the scientific check")
    if not str(event.get("source_location") or "").strip() or not str(value.get("reason") or "").strip():
        raise ValueError(f"{cid}: reading claim review lacks a decisive location/reason")
    return {"decision_id": event["decision_id"], "scientific_review_decision_id": science[1]["decision_id"],
            "reviewer": event["agent"], **expected}


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


def citation_window_key(
    *, parent_paper_id: str, direction: str, source: str,
    source_parameters: dict[str, Any], publication_cutoff: str | None,
    requested_max_n: int | None = None,
) -> str:
    """Fingerprint an ordinary or bridge citation window without choosing a source policy."""
    if not parent_paper_id or direction not in {"backward", "forward"} or not source:
        raise ValueError("citation window requires parent, backward/forward direction, and source")
    if requested_max_n is not None and requested_max_n < 1:
        raise ValueError("citation requested maximum must be positive when supplied")
    return _canonical_hash({
        "parent_paper_id": parent_paper_id,
        "direction": direction,
        "source": source,
        "source_parameters": source_parameters,
        "publication_cutoff": publication_cutoff,
        "requested_max_n": requested_max_n,
    })


def experiment_citation_node_status(group: dict[str, Any]) -> str:
    """Derive CORE/strict-bridge status from one physical experiment only."""
    if group.get("record_status", "active") != "active":
        return "not-node"
    values = [group.get(field) for field in BRIDGE_INGREDIENT_FIELDS]
    if all(value == "present" for value in values):
        return "core"
    if group.get("bridge_disposition") == "eligible":
        return "bridge"
    if all(value == "not-assessed" for value in values):
        return "not-assessed"
    return "not-node"


def bridge_experiment_errors(group: dict[str, Any]) -> list[str]:
    """Enforce the strict same-experiment exact-two bridge rule."""
    values = {field: group.get(field) for field in BRIDGE_INGREDIENT_FIELDS}
    errors: list[str] = []
    if group.get("bridge_disposition") != "eligible":
        return errors
    present = [field for field, value in values.items() if value == "present"]
    failed = [field for field, value in values.items() if value == "failed"]
    if len(present) != 2 or len(failed) != 1 or any(value == "unclear" for value in values.values()):
        errors.append("bridge eligibility requires exactly two present ingredients and one explicit failure")
    failed_names = {
        "citation_specific_x": "specific-x",
        "citation_awareness_attempt": "awareness-attempt",
        "citation_functional_y": "functional-y",
    }
    expected_failed = failed_names.get(failed[0]) if len(failed) == 1 else None
    if group.get("bridge_failed_ingredient") != expected_failed:
        errors.append("bridge failed ingredient does not match the single explicitly failed ingredient")
    if group.get("bridge_near_neighbor") != "yes":
        errors.append("bridge eligibility requires a positive empirical near-neighbor judgment")
    rationale = str(group.get("bridge_rationale") or "").strip()
    if len(rationale) < 20:
        errors.append("bridge eligibility requires a substantive positive bridge rationale")
    return errors


def derive_paper_citation_node_status(
    paper: dict[str, Any], groups: Iterable[dict[str, Any]],
) -> str:
    """Derive paper node status with full-text/empirical gates and CORE precedence."""
    fulltext = paper.get("fulltext_status")
    if fulltext in {"missing", "manually-requested", "unavailable"}:
        return "not-assessable-missing-fulltext"
    if (
        fulltext not in {"retrieved-published", "retrieved-repository", "retrieved-preprint"}
        or paper.get("current_status") != "fulltext-evaluated"
    ):
        return "not-assessed"
    if paper.get("bridge_empirical_status") != "empirical":
        return "not-node"
    statuses = [experiment_citation_node_status(group) for group in groups]
    if "core" in statuses:
        return "core"
    if "bridge" in statuses:
        return "bridge"
    return "not-node"


def paper_citation_node_errors(
    paper: dict[str, Any], groups: Iterable[dict[str, Any]],
) -> list[str]:
    expected = derive_paper_citation_node_status(paper, groups)
    observed = paper.get("citation_node_status")
    if observed != expected:
        return [f"citation_node_status must derive as {expected}, not {observed}"]
    if observed != "not-assessed" and not str(paper.get("citation_node_reason") or "").strip():
        return ["assessed citation-node status requires a reason"]
    return []


def citation_child_bridge_depth(parent_node_status: str, parent_bridge_depth: int) -> int:
    """Return child lineage depth; CORE and other depth-zero routes reset it."""
    if parent_bridge_depth not in {0, 1}:
        raise ValueError("bridge depth must be zero or one")
    if parent_node_status == "bridge":
        if parent_bridge_depth == 1:
            raise ValueError("a bridge at depth one cannot continue the same bridge lineage")
        return 1
    return 0


def bridge_expansion_allowed(
    node_status: str, encounter_depths: Iterable[int], *, already_completed: bool = False,
) -> bool:
    """Permit one bridge expansion when any eligible depth-zero encounter exists."""
    return node_status == "bridge" and 0 in set(encounter_depths) and not already_completed


def reconcile_bridge_frontier(
    state: dict[str, Any], *, paper_id: str, node_status: str, encounter_depth: int,
) -> dict[str, Any]:
    """Add/reopen a bridge obligation without making first encounter order authoritative."""
    if encounter_depth not in {0, 1}:
        raise ValueError("bridge encounter depth must be zero or one")
    updated = copy.deepcopy(state)
    eligible = updated.setdefault("bridge_depth0_eligible_paper_ids", [])
    pending = updated.setdefault("pending_bridge_expansion_paper_ids", [])
    completed = updated.setdefault("completed_bridge_expansion_paper_ids", [])
    if node_status == "bridge" and encounter_depth == 0:
        if paper_id not in eligible:
            eligible.append(paper_id)
        if paper_id not in completed and paper_id not in pending:
            pending.append(paper_id)
            updated["citation_frontier_status"] = "reopened"
            updated["workflow_phase"] = "reopened-frontiers"
    elif node_status == "core":
        if paper_id in pending:
            pending.remove(paper_id)
        updated["citation_frontier_status"] = "reopened"
        updated["workflow_phase"] = "reopened-frontiers"
    elif node_status == "not-node" and paper_id in pending:
        pending.remove(paper_id)
    return updated


def mark_bridge_expansion_complete(state: dict[str, Any], paper_id: str) -> dict[str, Any]:
    """Close a bridge-parent obligation after its policy-required citation windows finish."""
    updated = copy.deepcopy(state)
    pending = updated.setdefault("pending_bridge_expansion_paper_ids", [])
    completed = updated.setdefault("completed_bridge_expansion_paper_ids", [])
    if paper_id not in updated.setdefault("bridge_depth0_eligible_paper_ids", []):
        raise ValueError("cannot complete a bridge expansion without a depth-zero eligible lineage")
    if paper_id in pending:
        pending.remove(paper_id)
    if paper_id not in completed:
        completed.append(paper_id)
    return updated


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


from scientific_policy import route_viability, difference_provenance_errors


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
            errors.append(f"unaware-capacity route must be {expected_capacity} from selected exact-X unaware-regime A/F; E is not a gate")
        null_status = row.get("null_equivalence_route_status")
        awareness_result = row.get("awareness_effect")
        if awareness_result in {"no-detectable-difference", "equivalence-supported", "null-supported"}:
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
        errors.extend(difference_provenance_errors(row))
        for field in (
            "difference_source_location", "difference_statistic_or_test",
        ):
            if not str(row.get(field) or "").strip():
                errors.append(f"a direct same-Y difference requires {field}")
        if awareness_result == "not-tested":
            errors.append("a direct same-Y awareness comparison cannot be recorded as not-tested")
        if row.get("result_inspection_status") == "not-required":
            errors.append("a direct same-Y awareness comparison requires descriptive result inspection")
        for field in ("awareness_effect_critical_effect", "awareness_effect_estimate", "awareness_effect_stats_reason"):
            if not str(row.get(field) or "").strip():
                errors.append(f"a direct same-Y awareness comparison requires {field}")
        interpretability = row.get("awareness_effect_estimate_interpretable")
        if interpretability not in {"yes", "no", "unclear"}:
            errors.append("a direct same-Y awareness comparison requires an estimate-interpretability assessment")
        elif interpretability != "yes" and awareness_result != "unresolved":
            errors.append("an uninterpretable or unclear direct estimate must remain awareness-effect unresolved")
        if row.get("awareness_effect_stats_status") not in {"adequate", "concern", "unclear"}:
            errors.append("a direct same-Y awareness comparison requires a nonempty statistical audit")
        if awareness_result == "difference-supported" and not viability["awareness_effect"]:
            errors.append(
                "a significant direct comparison with weak A/E/F must remain awareness-effect unresolved"
            )
    if difference_tested in {"no", "unclear"} and awareness_result in {
        "difference-supported", "no-detectable-difference", "equivalence-supported", "null-supported",
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


def experiment_group_errors(
    groups: Iterable[dict[str, Any]], comparisons: Iterable[dict[str, Any]], paper_ids: set[str],
) -> list[str]:
    """Reconcile first-class physical groups with comparison rows without placeholders."""
    errors: list[str] = []
    group_rows = list(groups)
    comparison_rows = list(comparisons)
    errors.extend(group_record_lifecycle_errors({
        "experiment_groups.csv": group_rows,
        "experiments_master.csv": comparison_rows,
    }))
    group_ids = {row.get("experiment_id") for row in group_rows}
    comparisons_by_experiment: dict[str, set[str]] = {}
    for row in comparison_rows:
        experiment_id = str(row.get("experiment_id") or "")
        comparisons_by_experiment.setdefault(experiment_id, set()).add(
            str(row.get("comparison_id") or "")
        )
        if experiment_id not in group_ids:
            errors.append(f"{row.get('comparison_id')}: references missing experiment group")
    for group in group_rows:
        experiment_id = str(group.get("experiment_id") or "")
        paper_id = str(group.get("paper_id") or "")
        if paper_id not in paper_ids:
            errors.append(f"{experiment_id}: references missing paper {paper_id}")
        if not experiment_id.startswith(f"{paper_id}_E"):
            errors.append(f"{experiment_id}: does not belong to paper_id")
        observed = comparisons_by_experiment.get(experiment_id, set())
        declared = set(group.get("linked_comparison_ids", []))
        if declared != observed:
            errors.append(f"{experiment_id}: linked comparisons differ from experiments_master.csv")
        disposition = group.get("disposition")
        if disposition == "comparison-bearing" and not observed:
            errors.append(f"{experiment_id}: comparison-bearing group has no comparisons")
        if disposition in {"support-only", "no-qualifying-comparison"} and observed:
            errors.append(f"{experiment_id}: {disposition} group has placeholder/comparison rows")
        for error in bridge_experiment_errors(group):
            errors.append(f"{experiment_id}: {error}")
    return errors


def current_physical_experiment_groups(groups: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Current physical inventory; erroneous retained administrative rows are history."""
    return [group for group in groups if group.get("record_status", "active") == "active"]


def group_record_lifecycle_errors(tables: dict[str, list[dict[str, Any]]]) -> list[str]:
    """Validate retained nonphysical records and reject their use as current evidence."""
    groups = {group["experiment_id"]: group for group in tables.get("experiment_groups.csv", [])}
    retired = {key for key, group in groups.items() if group.get("record_status") == "retired-nonphysical"}
    errors: list[str] = []
    for key in sorted(retired):
        group = groups[key]
        target = group.get("reconciled_into_experiment_id")
        if target is not None:
            current = groups.get(target)
            if current is None:
                errors.append(f"{key}: reconciliation target is missing")
            elif target == key or current.get("paper_id") != group.get("paper_id"):
                errors.append(f"{key}: reconciliation target must be a different same-paper group")
            elif current.get("record_status", "active") != "active":
                errors.append(f"{key}: reconciliation target must be active; alias chains are prohibited")
        if group.get("linked_comparison_ids"):
            errors.append(f"{key}: retired nonphysical record retains current comparisons")
    for table, field, identifier in (
        ("experiments_master.csv", "experiment_id", "comparison_id"),
        ("experiments_master.csv", "awareness_result_source_experiment_id", "comparison_id"),
        ("experiments_master.csv", "difference_source_experiment_id", "comparison_id"),
        ("evidence_links.csv", "supporting_experiment_id", "evidence_link_id"),
        ("evidence_assessments.csv", "supporting_experiment_id", "evidence_assessment_id"),
    ):
        for row in tables.get(table, []):
            if row.get(field) in retired:
                errors.append(f"{table} {row.get(identifier)}: current reference to retired nonphysical group {row[field]}")
            if table == "experiments_master.csv" and field == "experiment_id":
                for key in sorted(set(row.get("difference_joint_experiment_ids", [])) & retired):
                    errors.append(f"{table} {row.get(identifier)}: joint analysis references retired nonphysical group {key}")
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
    if capacity == "supported" and row.get("Y_functional_status") not in {
        "downstream-function", "coherent-functional-mapping",
    }:
        errors.append("supported unaware capacity requires Y to be an audited downstream function")
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
    """Separate focal result reporting from support and require explicit transfer evidence."""
    focal_id = row.get("comparison_id")
    errors: list[str] = []
    from scientific_policy import array_cell
    bundles, links = list(bundles), list(links)
    regimes = array_cell(row.get("awareness_regime_evidence"))
    for item in regimes:
        if not isinstance(item, dict) or item.get("A_code") not in {"A-direct", "A-validated"}:
            continue
        if item.get("evidence_origin") not in {"same-article-transferred", "external-transferred"}:
            continue
        pointer = item.get("transfer_bundle_id")
        scoped = [bundle for bundle in bundles
                  if bundle.get("evidence_bundle_id") == pointer
                  and bundle.get("focal_comparison_id") == focal_id
                  and bundle.get("supported_premise") == "awareness-A"
                  and bundle.get("bundle_status") == "complete"
                  and item.get("regime_key") in array_cell(bundle.get("awareness_regime_keys"))]
        result_members = [link for link in links
                          if link.get("evidence_bundle_id") == pointer
                          and link.get("focal_comparison_id") == focal_id
                          and link.get("support_role") == "awareness-validation"
                          and link.get("evidence_content_type") == "critical-result"
                          and link.get("dependency_role") == "required"
                          and link.get("member_status") == "supports"
                          and link.get("used_for_decision") is True
                          and str(link.get("source_location") or "").strip()
                          and str(link.get("transfer_reason") or "").strip()
                          and str(link.get("transfer_limitation") or "").strip()
                          and (link.get("supporting_experiment_id") or link.get("supporting_auxiliary_id"))]
        if not scoped or not result_members or item.get("A_code") != "A-validated":
            errors.append(f"{focal_id}/{item.get('regime_key')}: strong transferred A requires its own complete awareness-A bundle with a required decision-used critical result")
    if row.get("A_code") not in {"A-direct", "A-validated"}:
        return errors
    for field in ("awareness_measure", "awareness_procedure_type"):
        if not str(row.get(field) or "").strip() or row.get(field) == "not-applicable":
            errors.append(f"{focal_id}: strong A lacks {field}")
    focal_result_supports = (
        row.get("awareness_result_reporting") == "reported"
        and row.get("awareness_result_support") == "supports-strong-A"
    )
    if focal_result_supports:
        for field in (
            "awareness_result_procedure_type", "awareness_result_description",
            "awareness_result_source_location",
        ):
            if not str(row.get(field) or "").strip() or row.get(field) == "not-applicable":
                errors.append(f"{focal_id}: reported supportive awareness result lacks {field}")
        if row.get("awareness_result_source_experiment_id") != row.get("experiment_id"):
            errors.append(f"{focal_id}: focal awareness result must come from the focal experiment")
        if (
            row.get("awareness_procedure_type")
            and row.get("awareness_result_procedure_type")
            and row.get("awareness_procedure_type") != row.get("awareness_result_procedure_type")
        ):
            errors.append(f"{focal_id}: awareness result type does not match the recorded procedure")
    if row.get("A_code") == "A-direct":
        if not focal_result_supports:
            errors.append(
                f"{focal_id}: A-direct requires a reported focal critical result that supports strong A"
            )
        return errors

    if focal_result_supports:
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
            link.get("supporting_experiment_id") is not None
            or link.get("supporting_auxiliary_id") is not None
        )
    ]
    if not result_links:
        errors.append(
            f"{focal_id}: A-validated without a supportive focal result requires a complete "
            "transferred awareness-A bundle with a required, decision-used, result-bearing "
            "member and explicit transfer assessment"
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


def process_activation_payload(
    comparison: dict[str, Any], normalized_y_label: str, *, normalization_reason: str,
    prior_normalized_y_labels: Iterable[str] = (),
) -> dict[str, Any]:
    """Freeze a comparison-specific earned function obligation before searching.

    Store this as a comparison decision's ``process_search_activation`` value.
    The complete typed comparison preserves the original trigger after revision;
    the ordinary decision history independently establishes its recorded state.
    """
    from derived_views import process_search_eligible
    row = dict(comparison, unaware_capacity_claim=comparison.get("unaware_capacity_claim") or "")
    if not process_search_eligible(row):
        raise ValueError("process activation requires an independently eligible comparison")
    if not isinstance(normalized_y_label, str) or not normalized_y_label.strip():
        raise ValueError("process activation requires a nonempty normalized Y label")
    if not isinstance(normalization_reason, str) or not normalization_reason.strip():
        raise ValueError("process activation requires a function normalization reason")
    return {
        "normalized_y_label": normalized_y_label,
        "normalization_reason": normalization_reason,
        "activation_kind": "same-y-reuse" if normalized_y_label in prior_normalized_y_labels else "new-y",
        "eligible_comparison": copy.deepcopy(comparison),
    }


def process_obligation_errors(
    comparisons: Iterable[dict[str, Any]], state: dict[str, Any],
    searches: Iterable[dict[str, Any]], decisions: Iterable[dict[str, Any]],
) -> list[str]:
    """Reconcile earned functions, activation history and their retrieval windows.

    This uses the existing scientific predicate; normalization remains an explicit
    semantic decision. Historical valid activations survive later demotions.
    """
    from derived_views import process_search_eligible
    rows = {row["comparison_id"]: row for row in comparisons}
    history = list(decisions)
    errors: list[str] = []
    activations: dict[str, list[dict[str, Any]]] = {}
    labels: set[str] = set()
    for index, event in enumerate(history):
        if event.get("field") != "process_search_activation":
            continue
        cid = event.get("entity_id")
        value = event.get("new_value")
        if (event.get("entity_type") != "comparison" or cid not in rows or not isinstance(value, dict)
                or set(value) != {"normalized_y_label", "normalization_reason", "activation_kind", "eligible_comparison"}):
            errors.append(f"process activation {event.get('decision_id')}: invalid comparison-specific payload")
            continue
        label, snapshot = value.get("normalized_y_label"), value.get("eligible_comparison")
        if (not isinstance(label, str) or not label.strip() or not str(value.get("normalization_reason") or "").strip()
                or not isinstance(snapshot, dict) or snapshot.get("comparison_id") != cid):
            errors.append(f"process activation {event.get('decision_id')}: missing label, reason or trigger snapshot")
            continue
        try:
            eligible = process_search_eligible(dict(snapshot, unaware_capacity_claim=snapshot.get("unaware_capacity_claim") or ""))
        except (KeyError, TypeError, AttributeError):
            eligible = False
        if not eligible:
            errors.append(f"process activation {event.get('decision_id')}: snapshot is not independently eligible")
            continue
        # Undo subsequent recorded scientific/clerical changes to recover the
        # comparison state actually present when this activation was recorded.
        prior = copy.deepcopy(rows[cid])
        for later in reversed(history[index + 1:]):
            if later.get("entity_type") != "comparison" or later.get("entity_id") != cid:
                continue
            field = later.get("field")
            if field == "record" and isinstance(later.get("old_value"), dict):
                prior = copy.deepcopy(later["old_value"])
            elif field in prior:
                prior[field] = copy.deepcopy(later.get("old_value"))
        if snapshot != prior:
            errors.append(f"process activation {event.get('decision_id')}: trigger snapshot differs from recorded comparison history")
            continue
        expected_kind = "same-y-reuse" if label in labels else "new-y"
        if value.get("activation_kind") != expected_kind:
            errors.append(f"process activation {event.get('decision_id')}: activation/reuse kind differs from prior obligations")
            continue
        labels.add(label)
        activations.setdefault(cid, []).append(event)
    declared = set(state.get("activated_normalized_y_labels", []))
    if labels != declared:
        errors.append("process obligations: activated normalized Y labels differ from valid durable activation history")
    def precedes(event: dict[str, Any], search: dict[str, Any]) -> bool:
        try:
            activated = datetime.fromisoformat(event["timestamp"].replace("Z", "+00:00"))
            started = datetime.fromisoformat(search["started_at"].replace("Z", "+00:00"))
            return activated <= started
        except (KeyError, TypeError, ValueError):
            return False

    for search in searches:
        if search.get("discovery_route") != "process-triggered-query":
            continue
        matching = [event for event in activations.get(search.get("trigger_comparison_id"), [])
                    if event["new_value"]["normalized_y_label"] == search.get("normalized_y_label")
                    and precedes(event, search)]
        if not matching:
            errors.append(f"process search {search.get('search_id')}: lacks a prior matching earned comparison activation")
    if state.get("status") == "complete" or state.get("process_frontier_status") == "satisfied":
        for cid, row in rows.items():
            checked = dict(row, unaware_capacity_claim=row.get("unaware_capacity_claim") or "")
            if process_search_eligible(checked) and not any(
                    event["new_value"]["eligible_comparison"].get("Y_label") == row.get("Y_label")
                    for event in activations.get(cid, [])):
                errors.append(f"process obligations: independently eligible comparison {cid} lacks function normalization/activation or same-Y reuse")
    return errors


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
    if state.get("pending_bridge_expansion_paper_ids", []):
        errors.append("required one-hop bridge expansions remain pending")
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
