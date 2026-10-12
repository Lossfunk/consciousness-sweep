#!/usr/bin/env python3
"""Validate one run's schemas, CSV encodings, identifiers, and references."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
import unicodedata
from datetime import datetime
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
    e_diagnostic_same_y_bundle_errors, experiment_group_errors, group_record_lifecycle_errors,
    factorial_e_diagnostic_bundle_errors, functional_structure_errors,
    ordered_result_set_sha256, paper_citation_node_errors, process_obligation_errors, route_audit_errors, search_window_key,
    validate_declared_bundle_status, scientific_regime_fingerprint, scientific_promotion_review_errors,
)
from derived_views import DERIVED_PREDICATES, derived_view_errors
from scientific_policy import (fulltext_attempt_required, joint_analysis_bundle_errors,
                               selected_unaware_regimes, strong_unaware_awareness)
from semantic_rescue import global_audit_json_payload, route_json_payload
from execution_contract import publication_policy_errors
ROOT = Path(__file__).resolve().parents[1]
DOI_PREFIX = re.compile(
    r"^(?:https?://(?:dx\.)?doi\.org/|doi:\s*|doi\.org/)", re.IGNORECASE
)


def normalized_doi(value: Any) -> str:
    return DOI_PREFIX.sub("", unquote(str(value or "")).strip()).strip().casefold()


def bibliographic_identity_matches(seed, paper):
    """The registered DOI, then normalized title/year/authors identity rule."""
    left, right = normalized_doi(seed.get("doi")), normalized_doi(paper.get("doi"))
    if left and right:
        return left == right

    def norm(value):
        return " ".join(re.findall(r"\w+", unicodedata.normalize("NFKC", str(value or "")).casefold()))

    return all(norm(seed.get(key)) == norm(paper.get(key)) for key in ("title", "year", "authors"))


def fixed_empirical_seed_traversal_errors(root, search, papers, searches, discoveries):
    """Fixed inputs can seed discovery without claiming dynamically earned CORE."""
    if search.get("citation_traversal_basis") != "fixed-empirical-seed":
        return []
    errors = []
    if (search.get("citation_parent_node_status") != "fixed-empirical-seed"
            or search.get("citation_parent_bridge_depth") != 0
            or search.get("discovery_route") not in {"backward-citation", "forward-citation"}):
        errors.append("fixed empirical seed traversal requires its explicit citation basis and depth zero")
    by_paper = {row["paper_id"]: row for row in papers}

    def canonical(pid):
        seen = set()
        while pid in by_paper and by_paper[pid].get("duplicate_of"):
            if pid in seen:
                return None
            seen.add(pid)
            pid = by_paper[pid]["duplicate_of"]
        return pid if pid in by_paper else None

    parent = canonical(search.get("parent_paper_id"))
    with (root / "seeds_empirical.csv").open(newline="", encoding="utf-8-sig") as stream:
        seeds = list(csv.DictReader(stream))
    fixed_ids = {canonical(paper["paper_id"]) for paper in papers
                 if any(bibliographic_identity_matches(seed, paper) for seed in seeds)} - {None}
    if parent is None or parent not in fixed_ids:
        errors.append("fixed empirical seed parent does not resolve to a frozen empirical seed identity")
    by_search = {row["search_id"]: row for row in searches}

    def prior_encounter(discovery):
        try:
            encountered = datetime.fromisoformat(discovery["discovered_at"].replace("Z", "+00:00"))
            started = datetime.fromisoformat(search["started_at"].replace("Z", "+00:00"))
            return encountered <= started
        except (KeyError, TypeError, ValueError):
            return False

    if parent is None or not any(
            canonical(row["paper_id"]) == parent
            and row.get("bridge_lineage_depth") == 0
            and by_search.get(row["search_id"], {}).get("discovery_route") == "empirical-seed"
            and prior_encounter(row)
            for row in discoveries):
        errors.append("fixed empirical seed traversal lacks a prior depth-zero empirical-seed encounter")
    return errors


def principal_completion_errors(root, state, papers, searches, discoveries, decisions):
    """Reconcile principal obligations and an explicit at-wave stopping snapshot.

    Scientific screening is supplied by the agent in ordinary paper decisions.
    This checks those frozen decisions, never a later paper classification.
    """
    errors = []
    by_paper = {row["paper_id"]: row for row in papers}
    by_search = {row["search_id"]: row for row in searches}
    event_index = {row["decision_id"]: index for index, row in enumerate(decisions)}
    by_event = {row["decision_id"]: row for row in decisions}

    def canonical(pid):
        seen = set()
        while pid in by_paper and by_paper[pid].get("duplicate_of"):
            if pid in seen:
                errors.append(f"{pid}: duplicate cycle prevents completion reconciliation")
                break
            seen.add(pid)
            pid = by_paper[pid]["duplicate_of"]
        return pid

    required = set()
    anchor_papers = set()
    for filename, route in (("seeds_empirical.csv", "empirical-seed"), ("seeds_reviews.csv", "review-anchor")):
        with (root / filename).open(newline="", encoding="utf-8-sig") as stream:
            for seed in csv.DictReader(stream):
                matched = {canonical(row["paper_id"]) for row in papers if bibliographic_identity_matches(seed, row)}
                if len(matched) != 1:
                    errors.append(f"completion: frozen seed {seed['seed_id']} lacks one resolved logical-paper identity")
                    continue
                pid = next(iter(matched))
                if route == "review-anchor":
                    anchor_papers.add(pid)
                required.add(pid)
                if not any(canonical(row["paper_id"]) == pid and by_search.get(row["search_id"], {}).get("discovery_route") == route for row in discoveries):
                    errors.append(f"completion: frozen seed {seed['seed_id']} lacks {route} encounter provenance")

    for paper in papers:
        pid = paper["paper_id"]
        if paper.get("duplicate_of"):
            continue
        if paper.get("citation_node_status") == "core" or paper.get("first_discovery_route") == "review-anchor":
            required.add(pid)
        if paper.get("citation_expansion_status") in {"pending", "in-progress"}:
            errors.append(f"completion: {pid} citation expansion is still pending")
        if paper.get("title_screen") == "not-screened" and pid not in anchor_papers:
            errors.append(f"completion: {pid} title screening is still pending")
        if paper.get("title_screen") == "retain" and (paper.get("abstract_status") == "not-sought" or (paper.get("abstract_status") == "available" and paper.get("abstract_screen") == "not-screened")):
            errors.append(f"completion: {pid} abstract screening is still pending")
        if paper.get("citation_node_status") == "bridge" and any(canonical(row["paper_id"]) == pid and row.get("bridge_lineage_depth") == 0 for row in discoveries):
            required.add(pid)
            if pid not in state.get("bridge_depth0_eligible_paper_ids", []):
                errors.append(f"completion: {pid} depth-zero bridge encounter is absent from durable obligations")
    # A provisional decision already acted upon creates an ordinary obligation.
    required.update(row["parent_paper_id"] for row in searches if row.get("citation_traversal_basis") == "provisional-core")
    citation = [row for row in searches if row.get("discovery_route") in {"backward-citation", "forward-citation"}]
    completed = [row for row in citation if row.get("window_status") in {"complete", "reused"}]
    for pid in sorted(required):
        directions = {row.get("index_direction") for row in completed if canonical(row.get("parent_paper_id")) == pid}
        if directions != {"backward", "forward"}:
            errors.append(f"completion: {pid} lacks completed backward/forward citation obligations")

    snapshots = [event for event in decisions if event.get("entity_type") == "run" and event.get("field") == "citation_saturation"]
    if not snapshots:
        return errors + ["completion: missing source-bound citation_saturation snapshot"]
    event = snapshots[-1]
    payload = event.get("new_value")
    if not isinstance(payload, dict) or set(payload) != {"wave", "search_ids", "new_paper_screening_decisions"}:
        return errors + ["completion: citation_saturation needs wave, search_ids and new_paper_screening_decisions"]
    if not citation or payload.get("wave") != max(row["wave"] for row in citation):
        return errors + ["completion: citation_saturation does not cover the latest citation wave"]
    wave = payload["wave"]
    wave_rows = [row for row in completed if row["wave"] == wave]
    ids = sorted(row["search_id"] for row in wave_rows)
    if payload.get("search_ids") != ids or {row["index_direction"] for row in wave_rows} != {"backward", "forward"}:
        errors.append("completion: citation_saturation must freeze every completed window in a backward/forward wave")
    if any(row.get("completed_at", "") > event["timestamp"] for row in wave_rows):
        errors.append("completion: citation_saturation precedes a window it claims to close")
    # Determine genuinely new logical works from ordered durable encounters.
    seen = set()
    newly_encountered = set()
    for discovery in sorted(discoveries, key=lambda row: row["discovery_id"]):
        pid = canonical(discovery["paper_id"])
        if pid not in seen and discovery["search_id"] in ids:
            newly_encountered.add(pid)
        seen.add(pid)
    screening = payload.get("new_paper_screening_decisions")
    if not isinstance(screening, dict) or set(screening) != newly_encountered:
        errors.append("completion: citation_saturation screening frame differs from newly encountered works")
        return errors
    for pid, decision_id in screening.items():
        prior = by_event.get(decision_id, {}) if isinstance(decision_id, str) else {}
        valid = (prior.get("entity_type") == "paper" and canonical(prior.get("entity_id")) == pid
                 and ((prior.get("field") == "title_screen" and prior.get("new_value") == "exclude")
                      or (prior.get("field") == "abstract_screen" and prior.get("new_value") == "screen-out"))
                 and event_index.get(decision_id, len(decisions)) < event_index[event["decision_id"]]
                 and bool(prior.get("source_location")))
        if not valid:
            errors.append(f"completion: {pid} lacks an at-wave source-bound exclusion; zero-yield citation stopping is unproved")
        elif any(later.get("entity_type") == "paper" and canonical(later.get("entity_id")) == pid
                 and later.get("field") == prior["field"]
                 for later in decisions[event_index[decision_id] + 1:event_index[event["decision_id"]]]):
            errors.append(f"completion: {pid} saturation cites a superseded screening decision")
    # A later revision can reopen a previously zero-yield wave; preserve its history.
    for later in decisions[event_index[event["decision_id"]] + 1:]:
        if later.get("entity_type") == "paper" and canonical(later.get("entity_id")) in newly_encountered and ((later.get("field") == "title_screen" and later.get("new_value") == "retain") or (later.get("field") == "abstract_screen" and later.get("new_value") in {"screen-in", "screen-uncertain"})):
            errors.append("completion: paper screening reopened after citation_saturation; record a fresh completed wave")
            break
    return errors


def abstract_evidence_errors(row: dict[str, Any]) -> list[str]:
    """Verify that available abstract decisions bind to their exact stored text."""
    if row.get("abstract_status") != "available":
        return []
    abstract = row.get("abstract_text")
    if not isinstance(abstract, str) or not abstract:
        return ["available abstract lacks stored text"]
    expected_hash = hashlib.sha256(abstract.encode("utf-8")).hexdigest()
    if row.get("abstract_sha256") != expected_hash:
        return ["abstract SHA-256 differs from stored text"]
    return []


def _screen_digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=True,
                                    separators=(",", ":")).encode()).hexdigest()


def _screen_events(decisions):
    return [event for event in decisions if event.get("entity_type") == "paper"
            and event.get("field") == "semantic_screen"]


def semantic_screen_event_errors(papers, decisions, *, run_complete=False,
                                 expected_scientific_regime=None):
    """Validate minimal, source-bound screening without a feature inventory."""
    errors, latest, by_id = [], {}, {}
    for event in _screen_events(decisions):
        pid, event_id, data = event.get("entity_id"), event.get("decision_id"), event.get("new_value")
        if not isinstance(data, dict):
            errors.append(f"{pid}: semantic_screen must contain a source-bound object")
            continue
        required_text = ("reason", "reviewer", "source_location", "discovery_route")
        if any(not isinstance(data.get(key), str) or not data[key].strip() for key in required_text):
            errors.append(f"{pid}: minimal screening needs reason, reviewer, source and discovery route")
        for key in ("title_sha256", "scientific_regime_fingerprint", "review_regime_fingerprint"):
            if not isinstance(data.get(key), str) or not re.fullmatch(r"[a-f0-9]{64}", data[key]):
                errors.append(f"{pid}: invalid minimal screening {key}")
        if data.get("abstract_sha256") is not None and not re.fullmatch(r"[a-f0-9]{64}", str(data["abstract_sha256"])):
            errors.append(f"{pid}: invalid minimal screening abstract hash")
        if expected_scientific_regime is not None and data.get("scientific_regime_fingerprint") != expected_scientific_regime:
            errors.append(f"{pid}: minimal screening regime differs from frozen inputs")
        stage, decision = data.get("stage"), data.get("decision")
        if stage not in {"title", "abstract", "rescue", "audit"} or decision not in {"retain", "uncertain", "exclude"}:
            errors.append(f"{pid}: invalid minimal screening stage or decision")
        if data.get("origin_stage") not in {"title", "abstract"}:
            errors.append(f"{pid}: minimal screening requires title/abstract origin")
        if stage in {"title", "abstract"} and data.get("origin_stage") != stage:
            errors.append(f"{pid}: initial screening origin must match its stage")
        if stage == "abstract" and data.get("abstract_sha256") is None:
            errors.append(f"{pid}: abstract screening requires the supplied abstract hash")
        if data.get("exclusion_basis") not in ({"outside-scope", "scientific"} if decision == "exclude" else {"not-applicable"}):
            errors.append(f"{pid}: exclusion basis disagrees with decision")
        if stage == "title" and (data.get("abstract_sha256") is not None or data.get("exclusion_basis") == "scientific"):
            errors.append(f"{pid}: title screening cannot claim abstract evidence or a scientific exclusion")
        prior = latest.get(pid)
        target = data.get("supersedes_decision_id")
        if (prior is None and target is not None) or (prior is not None and target != prior.get("decision_id")):
            errors.append(f"{pid}: minimal screening must explicitly supersede the current decision")
        if prior and prior["new_value"].get("abstract_sha256") is not None and data.get("abstract_sha256") is None:
            errors.append(f"{pid}: lower-information screening cannot supersede an abstract decision")
        if stage in {"rescue", "audit"}:
            if not prior or data.get("source_only") is not True:
                errors.append(f"{pid}: independent review needs a current source-only target")
            elif prior["new_value"].get("decision") != "exclude":
                errors.append(f"{pid}: independent review target is not a current exclusion")
            elif data.get("origin_stage") != prior["new_value"].get("origin_stage") or data.get("discovery_route") != prior["new_value"].get("discovery_route"):
                errors.append(f"{pid}: independent review changed its source cohort")
        latest[pid], by_id[event_id] = event, event
    for paper in papers:
        pid = paper["paper_id"]
        event = latest.get(pid)
        if event is None:
            continue
        data = event["new_value"]
        if data.get("title_sha256") != hashlib.sha256(paper["title"].encode()).hexdigest():
            errors.append(f"{pid}: minimal screening title hash is stale")
        if data.get("abstract_sha256") is not None and data["abstract_sha256"] != paper.get("abstract_sha256"):
            errors.append(f"{pid}: minimal screening abstract hash is stale")
        if data.get("discovery_route") != paper.get("first_discovery_route"):
            errors.append(f"{pid}: minimal screening discovery cohort differs from first-discovery route")
        pending_rescue = (data.get("stage") == "abstract" and data.get("decision") == "exclude"
                          and data.get("exclusion_basis") == "scientific")
        if pending_rescue:
            if run_complete or paper.get("abstract_screen") == "screen-out":
                errors.append(f"{pid}: scientific exclusion lacks fresh source-only rescue")
            continue
        if data.get("stage") == "title" or data.get("abstract_sha256") is None:
            expected = "exclude" if data.get("decision") == "exclude" else "retain"
            if paper.get("title_screen") != expected:
                errors.append(f"{pid}: current title state differs from minimal source decision")
        else:
            expected = {"retain": "screen-in", "uncertain": "screen-uncertain", "exclude": "screen-out"}.get(data.get("decision"))
            if paper.get("abstract_screen") != expected:
                errors.append(f"{pid}: current abstract state differs from minimal source decision")
    return errors


def semantic_screen_audit_payload(decisions, *, audit_seed, sample_size=10):
    """Recomputable current-exclusion frame with stable pre-audit rank anchors."""
    latest, anchors, misses = {}, {}, set()
    for event in _screen_events(decisions):
        data = event.get("new_value")
        if not isinstance(data, dict):
            continue
        pid = event.get("entity_id")
        cohort = (str(data.get("origin_stage")), str(data.get("discovery_route")))
        prior = latest.get(pid)
        if data.get("stage") == "audit" and prior:
            if data.get("decision") != "exclude":
                misses.add(cohort)
        else:
            anchors[pid] = _screen_digest({key: data.get(key) for key in
                ("title_sha256", "abstract_sha256", "scientific_regime_fingerprint", "review_regime_fingerprint")})
        latest[pid] = event
    groups = {}
    for pid, event in sorted(latest.items()):
        data = event["new_value"]
        if data.get("decision") != "exclude" or data.get("stage") == "rescue" or data.get("exclusion_basis") != "outside-scope":
            continue
        cohort = (str(data.get("origin_stage")), str(data.get("discovery_route")))
        rank = _screen_digest([audit_seed, list(cohort), pid, anchors.get(pid)])
        groups.setdefault(cohort, []).append((rank, pid, event["decision_id"]))
    cohorts = []
    for cohort, rows in sorted(groups.items()):
        selected = sorted(rows) if cohort in misses else sorted(rows)[:sample_size]
        cohorts.append({"origin_stage": cohort[0], "discovery_route": cohort[1],
                        "current_decision_ids": [row[2] for row in sorted(rows, key=lambda row: row[1])],
                        "sampled_decision_ids": [row[2] for row in selected], "reopened": cohort in misses})
    return {"audit_seed": audit_seed, "sample_size": sample_size, "cohorts": cohorts}


def semantic_screen_audit_errors(decisions, *, run_complete=False, execution_config=None):
    errors, seen, snapshots = [], [], []
    for event in decisions:
        if event.get("field") == "semantic_screen" and event.get("entity_type") == "paper":
            seen.append(event)
        if event.get("field") != "semantic_screen_audit_manifest" or event.get("entity_type") != "run":
            continue
        payload = event.get("new_value")
        snapshots.append((event, len(seen)))
        if not isinstance(payload, dict) or not isinstance(payload.get("audit_seed"), str) or not payload["audit_seed"].strip():
            errors.append("minimal screening audit requires a nonempty fixed audit seed")
            continue
        size = (execution_config or {}).get("demotion_audit_sample_per_stratum", 10)
        if payload.get("sample_size") != size:
            errors.append("minimal screening sample size differs from frozen configuration")
        if len(snapshots) > 1 and payload.get("audit_seed") != snapshots[0][0].get("new_value", {}).get("audit_seed"):
            errors.append("minimal screening audit seed changed across checkpoints")
        expected = semantic_screen_audit_payload(seen, audit_seed=payload["audit_seed"], sample_size=size)
        if payload != expected:
            errors.append("minimal screening audit differs from current source-bound exclusion frame")
    if not seen:
        return errors
    # Even an empty current frame has a checkpoint proving that superseded
    # exclusions were considered; no historical decision is silently resurrected.
    if not snapshots or snapshots[-1][1] != len(seen):
        errors.append("minimal screening decisions lack a current cumulative audit manifest")
        return errors
    if run_complete:
        payload = snapshots[-1][0].get("new_value", {})
        by_id = {event.get("decision_id"): event for event in seen}
        if not isinstance(payload, dict) or not isinstance(payload.get("audit_seed"), str):
            return errors
        current = semantic_screen_audit_payload(seen, audit_seed=payload["audit_seed"],
            sample_size=(execution_config or {}).get("demotion_audit_sample_per_stratum", 10))
        for cohort in current["cohorts"]:
            for event_id in cohort["sampled_decision_ids"]:
                data = by_id.get(event_id, {}).get("new_value", {})
                if data.get("stage") != "audit" or data.get("source_only") is not True:
                    errors.append(f"{event_id}: current sampled exclusion lacks independent source-only audit")
    return errors


def semantic_route_event_errors(
    papers: list[dict[str, Any]], decisions: list[dict[str, Any]],
    fulltext_assets: list[dict[str, Any]], *, run_complete: bool = False,
    expected_scientific_regime: str | None = None,
) -> list[str]:
    """Verify current route evidence and require reviewed rescues before screen-out."""
    errors = semantic_screen_event_errors(papers, decisions, run_complete=run_complete,
        expected_scientific_regime=expected_scientific_regime)
    minimal_papers = {event.get("entity_id") for event in _screen_events(decisions)}
    routes: dict[str, dict[str, Any]] = {}
    reviews: dict[str, dict[str, Any]] = {}
    for event in decisions:
        if event.get("entity_type") != "paper":
            continue
        if event.get("field") == "semantic_route":
            routes[event.get("entity_id", "")] = event
        elif event.get("field") == "semantic_rescue_review":
            reviews[event.get("entity_id", "")] = event
    assets_by_paper: dict[str, set[str]] = {}
    for asset in fulltext_assets:
        assets_by_paper.setdefault(asset["paper_id"], set()).add(asset["file_sha256"])
    for paper in papers:
        pid = paper["paper_id"]
        needs_route = (paper.get("title_screen") in {"retain", "exclude"}
                       or paper.get("abstract_screen") in {"screen-in", "screen-uncertain", "screen-out"})
        event = routes.get(pid)
        if needs_route and event is None and pid not in minimal_papers:
            errors.append(f"{pid}: retained abstract stage lacks source-bound semantic_screen or semantic_route event")
            continue
        if event is None:
            continue
        payload = event.get("new_value")
        if not isinstance(payload, dict) or set(payload) != {"source_bound_input", "decision"}:
            errors.append(f"{pid}: semantic_route event needs source_bound_input and decision")
            continue
        source = payload["source_bound_input"]
        stored = payload["decision"]
        if expected_scientific_regime is not None and (not isinstance(source, dict) or source.get("scientific_regime_fingerprint") != expected_scientific_regime):
            errors.append(f"{pid}: semantic_route scientific regime differs from the frozen run inputs")
        try:
            recomputed = route_json_payload({"records": [source], "audit_seed": "validation"})["decisions"][0]
        except (ValueError, TypeError, KeyError) as exc:
            errors.append(f"{pid}: invalid semantic_route evidence: {exc}")
            continue
        # JSON normalization changes tuples to arrays exactly as decision_log does.
        recomputed = json.loads(json.dumps(recomputed, sort_keys=True))
        if recomputed != stored:
            errors.append(f"{pid}: semantic_route decision differs from instrument output")
        if source.get("paper_id") != pid:
            errors.append(f"{pid}: semantic_route paper identity mismatch")
        title_hash = hashlib.sha256(paper["title"].encode("utf-8")).hexdigest()
        if source.get("title_sha256") != title_hash:
            errors.append(f"{pid}: semantic_route title hash is stale")
        abstract_hash = paper.get("abstract_sha256") if paper.get("abstract_status") == "available" else None
        if source.get("abstract_sha256") != abstract_hash:
            errors.append(f"{pid}: semantic_route abstract hash is stale")
        asset_hash = source.get("fulltext_sha256")
        if asset_hash and asset_hash not in assets_by_paper.get(pid, set()):
            errors.append(f"{pid}: semantic_route full-text hash has no verified asset")
        if (recomputed.get("strongest_agent_review_required")
                and (paper.get("abstract_screen") == "screen-out" or run_complete)):
            review = reviews.get(pid)
            details = review.get("new_value") if review else None
            if (not isinstance(details, dict)
                    or details.get("evidence_binding_sha256") != recomputed.get("evidence_binding_sha256")
                    or details.get("disposition") not in {"retain", "unresolved", "screen-out"}
                    or not details.get("reviewer") or not details.get("reason")):
                errors.append(f"{pid}: rescue route lacks matching strongest-agent review")
            elif (paper.get("abstract_screen") == "screen-out"
                  and details.get("disposition") != "screen-out"):
                errors.append(f"{pid}: rescue review does not support current screen-out")
    return errors


def semantic_route_manifest_errors(
    decisions: list[dict[str, Any]], *, run_complete: bool = False,
) -> list[str]:
    """Recompute every frozen routing batch from its immutable decision IDs."""
    errors: list[str] = []
    route_events = {event["decision_id"]: event for event in decisions
                    if event.get("entity_type") == "paper"
                    and event.get("field") == "semantic_route"}
    event_index = {event["decision_id"]: index for index, event in enumerate(decisions)}
    covered: set[str] = set()
    for event in decisions:
        if event.get("entity_type") != "run" or event.get("field") != "semantic_route_manifest":
            continue
        name = event.get("decision_id") or "unnamed-manifest"
        payload = event.get("new_value")
        if not isinstance(payload, dict):
            errors.append(f"{name}: manifest payload must be an object")
            continue
        ids = payload.get("route_decision_ids")
        if (not isinstance(ids, list) or not ids
                or any(not isinstance(item, str) for item in ids)
                or len(set(ids)) != len(ids)):
            errors.append(f"{name}: manifest needs unique route_decision_ids")
            continue
        if any(route_id not in route_events for route_id in ids):
            errors.append(f"{name}: manifest references absent route decision")
            continue
        if any(event_index[route_id] >= event_index[name] for route_id in ids):
            errors.append(f"{name}: manifest precedes a route decision it claims to freeze")
        if any(route_id in covered for route_id in ids):
            errors.append(f"{name}: route decision appears in multiple frozen manifests")
        covered.update(ids)
        records = []
        for route_id in ids:
            route_event = route_events[route_id]
            source = route_event.get("new_value")
            if not isinstance(source, dict) or not isinstance(source.get("source_bound_input"), dict):
                errors.append(f"{name}: {route_id} lacks source-bound input")
                break
            records.append(source["source_bound_input"])
        else:
            try:
                computed = route_json_payload({
                    "records": records,
                    "audit_seed": payload["audit_seed"],
                    "min_stratum_size": payload["min_stratum_size"],
                    "per_stratum": payload["per_stratum"],
                    "reopen_signatures": payload.get("reopen_signatures", []),
                })
            except (KeyError, ValueError, TypeError) as exc:
                errors.append(f"{name}: cannot recompute route manifest: {exc}")
                continue
            for key in ("route_manifest", "demotion_samples", "affected_signature_manifests"):
                if json.loads(json.dumps(computed[key])) != payload.get(key):
                    errors.append(f"{name}: {key} differs from recomputed frame")
    missing = set(route_events) - covered
    if missing:
        errors.append(f"{len(missing)} semantic route decisions lack a frozen manifest")
    return errors


def semantic_global_audit_errors(
    decisions: list[dict[str, Any]], *, run_complete: bool = False,
    execution_config: dict[str, Any] | None = None,
) -> list[str]:
    """Require a cumulative, hash-bound demotion audit across routing batches."""
    errors = semantic_screen_audit_errors(decisions, run_complete=run_complete,
                                          execution_config=execution_config)
    latest: dict[str, dict[str, Any]] = {}
    snapshots: list[dict[str, Any]] = []
    computed: dict[str, Any] = {}
    inputs: list[dict[str, Any]] = []
    event_index = {event.get("decision_id"): index for index, event in enumerate(decisions)}
    for event in decisions:
        if event.get("entity_type") == "paper" and event.get("field") == "semantic_route":
            latest[event.get("entity_id", "")] = event
        if event.get("entity_type") != "run" or event.get("field") != "semantic_global_audit_manifest":
            continue
        snapshots.append(event)
        computed = {}
        payload = event.get("new_value")
        name = event.get("decision_id") or "unnamed-global-audit"
        if not isinstance(payload, dict):
            errors.append(f"{name}: cumulative global audit manifest must be an object")
            continue
        if execution_config is not None:
            for field, configured in (("min_stratum_size", "demotion_audit_min_stratum_size"),
                                      ("per_stratum", "demotion_audit_sample_per_stratum")):
                if payload.get(field) != execution_config.get(configured):
                    errors.append(f"{name}: {field} differs from frozen config {configured}")
        inputs = []
        for pid, route_event in sorted(latest.items()):
            route = route_event.get("new_value")
            if not isinstance(route, dict) or not isinstance(route.get("decision"), dict):
                errors.append(f"{name}: {pid} current route is missing its decision")
                continue
            inputs.append({"decision_id": route_event.get("decision_id"),
                           "decision": route["decision"]})
        if not inputs:
            errors.append(f"{name}: cumulative global audit has no route decisions")
            continue
        try:
            computed = global_audit_json_payload({
                "route_events": inputs,
                "audit_seed": payload["audit_seed"],
                "min_stratum_size": payload["min_stratum_size"],
                "per_stratum": payload["per_stratum"],
                "reopen_signatures": payload.get("reopen_signatures", []),
            })
        except (KeyError, TypeError, ValueError) as exc:
            errors.append(f"{name}: cannot recompute cumulative global audit: {exc}")
            continue
        if json.loads(json.dumps(computed, sort_keys=True)) != json.loads(json.dumps(payload, sort_keys=True)):
            errors.append(f"{name}: cumulative global audit differs from current routing frame")
    if not latest:
        return errors
    if not snapshots:
        errors.append("current routing decisions lack a cumulative global audit manifest")
        return errors
    snapshot = snapshots[-1]
    if not computed:
        return errors
    frozen_at = event_index.get(snapshot.get("decision_id"), -1)
    if any(event_index.get(event.get("decision_id"), -1) >= frozen_at
           for event in latest.values()):
        errors.append("cumulative global audit precedes a current route decision")
    if not run_complete:
        return errors
    by_paper = {item["decision"]["paper_id"]: item["decision"] for item in inputs}
    sample_audits = [event for event in decisions if event.get("entity_type") == "paper"
                     and event.get("field") == "semantic_demotion_audit"
                     and isinstance(event.get("new_value"), dict)]
    confirmed_misses: set[str] = set()
    for sample in computed["demotion_samples"]:
        for pid in sample["sampled_paper_ids"]:
            binding = by_paper[pid]["evidence_binding_sha256"]
            matching = [event for event in sample_audits
                        if event.get("entity_id") == pid
                        and event["new_value"].get("evidence_binding_sha256") == binding
                        and event["new_value"].get("stratum") == sample["stratum"]]
            if not matching:
                errors.append(f"sampled demotion {pid} lacks source-bound audit")
                continue
            outcome = matching[-1]["new_value"]
            if (outcome.get("disposition") not in {"retained", "unresolved", "screen-out", "false-negative"}
                    or not outcome.get("reviewer") or not outcome.get("reason")
                    or not outcome.get("source_location")):
                errors.append(f"sampled demotion {pid} has incomplete audit result")
    # Purposive and boundary-neighbor audits can reveal a miss too; do not
    # require it to have been selected by the random sample.
    for audit in sample_audits:
        outcome = audit["new_value"]
        if outcome.get("disposition") != "false-negative":
            continue
        pid = audit.get("entity_id")
        binding = by_paper.get(pid, {}).get("evidence_binding_sha256")
        if not binding or outcome.get("evidence_binding_sha256") != binding:
            continue  # Historical/stale audit; current evidence must be reviewed anew.
        signature = outcome.get("false_negative_signature")
        if not isinstance(signature, str) or not signature:
            errors.append(f"false-negative {pid} lacks affected signature")
        else:
            confirmed_misses.add(signature)
    frames = {item["signature"]: item for item in computed["affected_signature_manifests"]}
    for signature in sorted(confirmed_misses):
        frame = frames.get(signature)
        if not frame or not frame["affected_paper_ids"]:
            errors.append(f"false-negative signature {signature} lacks a nonempty frozen affected frame")
            continue
        affected = [event for event in decisions if event.get("entity_type") == "paper"
                    and event.get("field") == "semantic_affected_review"
                    and isinstance(event.get("new_value"), dict)]
        for pid in frame["affected_paper_ids"]:
            binding = by_paper[pid]["evidence_binding_sha256"]
            matching = [event for event in affected
                        if event.get("entity_id") == pid
                        and event_index.get(event.get("decision_id"), -1) > frozen_at
                        and event["new_value"].get("signature") == signature
                        and event["new_value"].get("evidence_binding_sha256") == binding]
            if not matching:
                errors.append(f"affected signature {signature}: {pid} lacks source-bound review")
                continue
            review = matching[-1]["new_value"]
            if (review.get("disposition") not in {"retained", "unresolved", "screen-out", "false-negative"}
                    or not review.get("reviewer") or not review.get("reason")
                    or not review.get("source_location")):
                errors.append(f"affected signature {signature}: {pid} has incomplete review")
        completions = [event for event in decisions if event.get("entity_type") == "run"
                       and event.get("field") == "affected_signature_review_complete"
                       and isinstance(event.get("new_value"), dict)
                       and event["new_value"].get("signature") == signature]
        completion = completions[-1]["new_value"] if completions else {}
        if (not completions or event_index.get(completions[-1].get("decision_id"), -1) <= frozen_at
                or completion.get("ordered_affected_sha256") != frame["ordered_affected_sha256"]
                or completion.get("reviewed_paper_ids") != list(frame["affected_paper_ids"])):
            errors.append(f"affected signature {signature} lacks complete frozen-stratum closure")
    return errors


def awareness_regime_errors(row: dict[str, Any]) -> list[str]:
    """Check exact-X awareness evidence for each claimed contrast regime.

    This is a provenance check. The scientific meaning of a result remains in
    PROTOCOL.md and is never inferred from an arm label or objective accuracy.
    """
    errors: list[str] = []
    regimes = row.get("awareness_regime_evidence") or []
    if not isinstance(regimes, list):
        return ["awareness regime evidence must be a list"]
    keys = [item.get("regime_key") for item in regimes if isinstance(item, dict)]
    if len(keys) != len(regimes):
        errors.append("awareness regime entries must be objects")
    if len(keys) != len(set(keys)):
        errors.append("awareness regime keys must be unique")
    strong_a = row.get("A_code") in {"A-direct", "A-validated"}
    contrast = row.get("awareness_contrast_type")
    selected = row.get("unaware_capacity_regime_keys") or []
    if selected and len(selected_unaware_regimes(row)) != len(selected):
        errors.append("capacity regime selection must identify unique current regime keys")
    if row.get("unaware_capacity") == "supported" and not strong_unaware_awareness(row):
        errors.append("supported capacity lacks strong exact-X unawareness in every selected claim regime")
    if row.get("unaware_condition_tested") == "no" and selected:
        errors.append("a comparison without an unaware condition cannot select capacity regimes")
    if strong_a or (row.get("current_status") == "fully-evaluated" and contrast in {"aware-unaware", "graded", "probability-regime"}):
        if not regimes:
            errors.append("strong or completed awareness comparison lacks arm/regime evidence")
        if contrast == "aware-unaware" and len(regimes) < 2:
            errors.append("aware-unaware comparison requires distinct arm records")
    for item in regimes:
        if not isinstance(item, dict):
            continue
        key = item.get("regime_key") or "unnamed-regime"
        status = item.get("critical_result_status") or "not-reported"
        origin = item.get("evidence_origin") or "missing"
        if status.startswith("reported-") and status != "not-reported":
            if not item.get("critical_result") or not item.get("source_location"):
                errors.append(f"{key}: reported awareness result needs result and source location")
        if origin in {"same-article-transferred", "external-transferred"}:
            if not item.get("transfer_reason") or not item.get("transfer_limitation"):
                errors.append(f"{key}: transferred result needs reason and limitation")
            bundle = item.get("transfer_bundle_id")
            if not bundle or bundle not in row.get("evidence_bundle_ids", []):
                errors.append(f"{key}: transferred result needs a linked evidence bundle")
        local_strong = item.get("A_code") in {"A-direct", "A-validated"}
        if local_strong and item.get("X_content") != row.get("X_label"):
            errors.append(f"{key}: strong regime A must address the exact focal X")
        if strong_a and not local_strong:
            errors.append(f"{key}: comparison-wide strong A requires strong local A in every contrast regime")
        if strong_a or local_strong:
            if status not in {"reported-supports-awareness", "reported-supports-unawareness", "reported-supports-graded-difference"}:
                errors.append(f"{key}: strong A lacks a supporting critical awareness result")
            if (row.get("A_code") == "A-direct" or item.get("A_code") == "A-direct") and origin != "focal-task":
                errors.append(f"{key}: A-direct requires focal-task evidence")
    if row.get("partial_x_residual_status") == "supported" and not row.get("partial_x_residual_source_location"):
        errors.append("supported partial-X residual effect needs a source location")
    return errors
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
    "bayesian_null_supported.csv": "experiments.schema.json",
    "supplementary_evidence.csv": "experiments.schema.json",
}
ARRAY_FIELDS = {
    "stats_flags", "attempted_sources", "E_diagnostic_source_locations",
    "factorial_component_effects", "evidence_bundle_ids", "required_member_keys",
    "awareness_regime_evidence", "unaware_capacity_regime_keys", "awareness_regime_keys",
    "linked_comparison_ids", "support_roles", "difference_joint_experiment_ids",
    "activated_normalized_y_labels", "completed_search_window_keys",
    "bridge_depth0_eligible_paper_ids", "pending_bridge_expansion_paper_ids",
    "completed_bridge_expansion_paper_ids",
}
OBJECT_FIELDS = {"source_parameters", "promotion_challenge"}
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
    if node.get("type") == "null" or (isinstance(node.get("type"), list) and "null" in node["type"]) or ("enum" in node and None in node["enum"]) or (node.get("const") is None and "const" in node):
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
    # String source evidence must retain its exact UTF-8 content (abstract hashes).
    return "" if value is None else value


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
        return row.get("awareness_effect") in {"difference-supported", "no-detectable-difference", "equivalence-supported", "null-supported"}
    if premise == "null/no-detectable-difference":
        return row.get("awareness_effect") in {"no-detectable-difference", "null-supported"}
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
        if bundle.get("supported_premise") == "awareness-A":
            scope = bundle.get("awareness_regime_keys") or []
            regimes = {item.get("regime_key"): item for item in focal.get("awareness_regime_evidence", [])}
            if not scope or any(key not in regimes for key in scope):
                errors.append(f"evidence_bundles.csv: {bundle_id} awareness scope must name current focal regimes")
            for key in scope:
                item = regimes.get(key, {})
                # A regime selects one active premise, but independent complete
                # alternatives may truthfully retain the same declared scope.
                # The active pointer is resolved by awareness_result_provenance_errors.
                if bundle.get("bundle_status") == "complete" and (
                    item.get("evidence_origin") not in {"same-article-transferred", "external-transferred"}
                    or item.get("critical_result_status") not in {"reported-supports-awareness", "reported-supports-unawareness", "reported-supports-graded-difference"}
                    or item.get("X_content") != focal.get("X_label")
                    or any(not str(item.get(field) or "").strip() for field in
                           ("critical_result", "source_location", "transfer_reason", "transfer_limitation"))
                ):
                    errors.append(f"evidence_bundles.csv: {bundle_id}/{key} complete awareness premise lacks explicit exact-X critical-result coverage and transfer")
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
        for error in joint_analysis_bundle_errors(row, evidence_bundles, evidence_links):
            errors.append(f"experiments_master.csv: {focal_id}: {error}")
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


def _main_locked(argv: list[str] | None = None, *, check_derived: bool = True, report_success: bool = True) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--runs-root", type=Path)
    parser.add_argument("--allow-stale-counters", action="store_true")
    args = parser.parse_args(argv)
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

    errors.extend(publication_policy_errors(config))

    csv_schemas = {name: schema for name, schema in CSV_SCHEMAS.items()
                   if check_derived or name not in DERIVED_PREDICATES}
    required = [*csv_schemas, "decision_log.jsonl", "run_state.json", "run_summary.md", "fulltexts"]
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
        for filename, schema_name in csv_schemas.items():
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
    errors.extend(scientific_promotion_review_errors(experiments, state, tables, decisions))
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
    for error in semantic_route_event_errors(
            papers, decisions, fulltext_assets,
            run_complete=state.get("status") == "complete",
            expected_scientific_regime=scientific_regime_fingerprint(compatibility_state)):
        errors.append(f"decision_log.jsonl: {error}")
    for error in semantic_route_manifest_errors(
            decisions, run_complete=state.get("status") == "complete"):
        errors.append(f"decision_log.jsonl: {error}")
    for error in semantic_global_audit_errors(
            decisions, run_complete=state.get("status") == "complete",
            execution_config=config.get("execution", {})):
        errors.append(f"decision_log.jsonl: {error}")
    for row in papers:
        for error in abstract_evidence_errors(row):
            errors.append(f"papers_master.csv: {row['paper_id']} {error}")
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
    for error in group_record_lifecycle_errors(tables):
        errors.append(f"experiment record lifecycle: {error}")
    for row in experiments:
        for member in row.get("difference_joint_experiment_ids", []):
            if member not in experiment_ids:
                errors.append(f"{row['comparison_id']}: joint analysis references missing experiment {member}")
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
        for error in awareness_regime_errors(row):
            errors.append(f"experiments_master.csv: {row['comparison_id']}: {error}")
    for error in functional_structure_errors(experiments):
        errors.append(f"experiments_master.csv: {error}")
    for row in searches:
        for error in fixed_empirical_seed_traversal_errors(root, row, papers, searches, discoveries):
            errors.append(f"search_log.csv: {row['search_id']} {error}")
        if row.get("publication_cutoff") != config.get("publication_cutoff"):
            errors.append(f"search_log.csv: {row['search_id']} publication cutoff differs from the frozen policy")
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
                "fixed-empirical-seed": "fixed-empirical-seed",
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
            errors.extend(principal_completion_errors(root, state, papers, searches, discoveries, decisions))
            for paper in papers:
                if fulltext_attempt_required(paper) and paper.get("fulltext_status") in {"not-attempted", "not-required"} and paper.get("duplicate_of") is None:
                    errors.append(f"{paper['paper_id']}: retained candidate requires a full-text attempt before completion")
                if (paper.get("fulltext_status", "").startswith("retrieved-")
                        and fulltext_attempt_required(paper) and paper.get("duplicate_of") is None
                        and paper.get("current_status") != "fulltext-evaluated"):
                    errors.append(f"{paper['paper_id']}: obtained retained full text must be evaluated before completion")
            for error in completion_errors(state):
                errors.append(f"run_state.json: {error}")
        if state.get("blind_lane_status") == "complete" and complete_blind_pairs != expected_blind_pairs:
            missing_pairs = sorted(expected_blind_pairs - complete_blind_pairs)
            extra_pairs = sorted(complete_blind_pairs - expected_blind_pairs)
            errors.append(
                "run_state.json: blind lane marked complete without exactly the mandatory windows; "
                f"missing={missing_pairs}, extra={extra_pairs}"
            )
        activation_validator = Draft202012Validator(
            json.loads((root / "schemas" / "experiments.schema.json").read_text(encoding="utf-8")),
            format_checker=FormatChecker(),
        )
        for event in decisions:
            if event.get("field") == "process_search_activation" and isinstance(event.get("new_value"), dict):
                snapshot = event["new_value"].get("eligible_comparison")
                for error in activation_validator.iter_errors(snapshot):
                    errors.append(f"decision_log.jsonl: {event['decision_id']} process trigger snapshot: {error.message}")
        errors.extend(process_obligation_errors(experiments, state, searches, decisions))
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

    if check_derived and not errors:
        errors.extend(derived_view_errors(experiments, tables))

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    if report_success:
        print(f"PASS: {args.run_id} schemas, CSV encodings, JSONL, IDs, references, hashes, counters, and derived views validate.")
    return 0


def main(argv: list[str] | None = None, *, check_derived: bool = True, report_success: bool = True) -> int:
    """Validate one stable snapshot, recovering committed writes before reading."""
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--runs-root", type=Path)
    args, _ = parser.parse_known_args(argv)
    root = args.root.resolve()
    runs_root = args.runs_root.resolve() if args.runs_root else root / "runs"
    run_dir = runs_root / args.run_id
    if not run_dir.is_dir():
        print(f"ERROR: run directory does not exist: {run_dir}", file=sys.stderr)
        return 1
    from structured_write import run_write_lock
    try:
        with run_write_lock(run_dir):
            return _main_locked(argv, check_derived=check_derived, report_success=report_success)
    except (OSError, ValueError) as exc:
        print(f"ERROR: run snapshot/recovery: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
