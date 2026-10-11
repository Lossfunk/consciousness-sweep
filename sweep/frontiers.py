"""Durable discovery obligations using the frozen scientific predicates.

Functions return new JSON-serializable state; the coordinator persists that state
and its reason atomically. Queue exhaustion and budget exhaustion are never
scientific stopping evidence. Reader prospects cannot create CORE or earned-Y
obligations: callers supply independently audited native records instead.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

from .common import scientific_module, science_root as default_science_root
from .sources import digest, now


def _root(science_root=None):
    root = Path(science_root) if science_root else default_science_root()
    if root.resolve() != default_science_root().resolve():
        raise ValueError("Frontier helper must use the same frozen scientific package as the coordinator")
    return root


def _validate(table, row, root):
    schema = json.loads((root / "schemas" / (table + ".schema.json")).read_text())
    Draft202012Validator(schema).validate(row)


def _event(state, action, reason, **data):
    if not isinstance(reason, str) or not reason.strip():
        raise ValueError("Every frontier transition requires a reason")
    state.setdefault("history", []).append({"at": now(), "action": action, "reason": reason, **data})


def blind_windows(science_root=None):
    root = _root(science_root)
    config = yaml.safe_load((root / "config.yaml").read_text())
    frozen = config["search"]["conservative_execution"]["supplementary_blind_lane"]
    queries = scientific_module("query_instruments")
    contract = scientific_module("execution_contract")
    windows = []
    for source in frozen["sources"]:
        for family in frozen["active_families"]:
            query = queries.render_blind_query(source, family)
            params = {"page": 1, "sort": "relevance_score:desc"} if source == "OpenAlex" else {"cursorMark": "*", "synonym": False, "resultType": "core"}
            limit = frozen["max_results_per_source_family"]
            key = contract.search_window_key(execution_phase="supplementary-blind", source=source,
                    query_id=family, normalized_y_label=None, canonical_query=query,
                    source_parameters=params, publication_cutoff=config["publication_cutoff"], requested_max_n=limit)
            windows.append({"window_key": key, "source": source, "query": query, "family": family,
                            "kind": "query", "phase": "supplementary-blind", "limit": limit,
                            "cursor": None, "source_parameters": params, "status": "pending"})
    return windows


def initial_state(science_root=None):
    root = _root(science_root)
    return {"version": "portable-discovery-frontiers-v1", "science_config_sha256": digest((root / "config.yaml").read_bytes()),
            "phase": "principal", "principal_provisionally_satisfied": False,
            "seed_initialization_complete": False, "anchor_initialization_complete": False,
            "blind_windows": {w["window_key"]: w for w in blind_windows(root)},
            "process_windows": {}, "citation_obligations": {}, "nodes": {},
            "activated_y": {}, "native_assessment_pending": {}, "history": [],
            "lineage_replay_pending": {}, "citation_wave_audits": [], "validation": None}


def _invalidate(state):
    state["validation"] = None
    if state["phase"] in {"complete", "final-validation", "supplementary-blind"}:
        state["phase"] = "reopened-frontiers"


def initialize_principal(state, *, seeds_complete, anchors_complete, reason):
    result = copy.deepcopy(state)
    result["seed_initialization_complete"] = bool(seeds_complete)
    result["anchor_initialization_complete"] = bool(anchors_complete)
    _event(result, "principal-initialization", reason)
    return result


def require_native_assessment(state, paper_id, reason, *, source_asset_ids=()):
    result = copy.deepcopy(state)
    result["native_assessment_pending"][paper_id] = {
        "paper_id": paper_id, "task": "native-discovery-audit", "source_asset_ids": list(source_asset_ids),
        "required": ["enumerate physical experiments", "source-located X / awareness-attempt / functional-Y ingredients",
                     "CORE or strict same-experiment bridge derivation", "independently earned Y audit under PROTOCOL §9.4"],
        "reason": reason, "policy": "Raw prospect/context labels do not establish citation or process eligibility"}
    _invalidate(result)
    _event(result, "native-assessment-required", reason, paper_id=paper_id)
    return result


def _citation_obligations(state, paper, status, depths, reason):
    contract = scientific_module("execution_contract")
    if status == "bridge" and 0 not in depths:
        return
    if status not in {"core", "bridge", "review-anchor", "empirical-seed", "provisional-core"}:
        return
    for direction in ("backward", "forward"):
        key = paper["paper_id"] + ":" + direction
        if key in state["citation_obligations"]:
            existing = state["citation_obligations"][key]
            if existing["parent_node_status"] == "bridge" and status == "core":
                existing["parent_node_status"] = "core"
                existing["child_bridge_depth"] = 0
                if existing["pages"]:
                    state.setdefault("lineage_replay_pending", {})[key] = {
                        "task": "replay-citation-provenance", "obligation_id": key,
                        "pages": copy.deepcopy(existing["pages"]), "child_bridge_depth": 0,
                        "reason": "Parent is now CORE; reuse completed snapshots and record depth-zero rediscoveries without refetching"}
                _invalidate(state)
            continue
        # A source request needs bibliographic identity, not the parent's full
        # article, assessment or screening history. Keep lineage/status in the
        # explicit obligation fields and avoid copying full texts into every
        # frontier snapshot and pagination job.
        identity = {name: copy.deepcopy(paper[name]) for name in (
            "paper_id", "title", "doi", "year", "publication_year", "authors", "author",
            "openalex_id", "source_stable_id", "epmc_id", "epmc_source", "pmcid", "pmid",
            "url", "urls", "source", "publication_date", "arxiv_id") if name in paper}
        state["citation_obligations"][key] = {
            "obligation_id": key, "parent": identity, "parent_node_status": status,
            "direction": direction, "status": "pending", "source": "OpenAlex", "cursor": None,
            "parent_bridge_depth": 0, "child_bridge_depth": contract.citation_child_bridge_depth(status, 0),
            "pages": [], "source_failures": [], "seen_cursors": [], "reason": reason}
        _invalidate(state)


def add_anchor(state, paper, *, role, reason):
    if role not in {"review-anchor", "empirical-seed"}:
        raise ValueError("Only frozen seed/anchor roles enter this route")
    if not paper.get("paper_id"):
        raise ValueError("Anchor requires its allocated logical paper ID")
    result = copy.deepcopy(state)
    _citation_obligations(result, paper, role, [0], reason)
    _event(result, "principal-anchor", reason, paper_id=paper["paper_id"], role=role)
    return result


def record_missing_source(state, paper, audit, *, reason):
    """A high-priority abstract can provisionally earn CORE, never BRIDGE."""
    decision = audit.get("decision")
    if decision not in {"provisional-core", "not-established", "unresolved"} or not str(audit.get("reason", "")).strip():
        raise ValueError("Missing-source audit needs explicit provisional decision and reason")
    result = copy.deepcopy(state)
    if decision == "unresolved":
        _event(result, "missing-source-unresolved", reason, paper_id=paper["paper_id"], audit=audit)
        return result
    if decision == "provisional-core":
        if not paper.get("abstract") or audit.get("priority") != "high":
            raise ValueError("Provisional CORE requires available abstract and explicit high full-text priority")
        ingredients = audit.get("ingredients") or {}
        for key in ("specific_x", "awareness_attempt", "functional_y"):
            if ingredients.get(key, {}).get("status") != "present" or not str(ingredients[key].get("source_observation", "")).strip():
                raise ValueError("Provisional CORE requires all three ingredients explicitly supported in the abstract")
        _citation_obligations(result, paper, "provisional-core", [0], reason)
    result["nodes"][paper["paper_id"]] = {"status": "provisional-core" if decision == "provisional-core" else "not-assessable-missing-fulltext",
        "abstract_sha256": digest(paper.get("abstract") or ""), "reason": reason, "missing_source_audit": copy.deepcopy(audit)}
    result["native_assessment_pending"].pop(paper["paper_id"], None)
    _event(result, "missing-source-audited", reason, paper_id=paper["paper_id"], audit=audit)
    return result


def record_node(state, paper, groups, *, encounter_depth=0, reason, science_root=None):
    """Derive node status from typed physical experiment records, never a label."""
    root = _root(science_root)
    contract = scientific_module("execution_contract")
    if encounter_depth not in {0, 1}:
        raise ValueError("Encounter bridge depth must be zero or one")
    groups = list(groups)
    for group in groups:
        _validate("experiment_groups", group, root)
        if group["paper_id"] != paper["paper_id"]:
            raise ValueError("Physical group belongs to another paper")
        errors = contract.bridge_experiment_errors(group)
        if errors:
            raise ValueError("; ".join(errors))
    status = contract.derive_paper_citation_node_status(paper, groups)
    if status == "not-assessed":
        raise ValueError("Native record is not adequately assessed; keep audit work pending")
    result = copy.deepcopy(state)
    existing = result["nodes"].get(paper["paper_id"], {})
    depths = sorted(set(existing.get("encounter_depths", []) + [encounter_depth]))
    result["nodes"][paper["paper_id"]] = {"status": status, "encounter_depths": depths,
                                        "groups_sha256": digest(groups), "reason": reason}
    result["native_assessment_pending"].pop(paper["paper_id"], None)
    _citation_obligations(result, paper, status, depths, reason)
    _event(result, "node-derived", reason, paper_id=paper["paper_id"], status=status, encounter_depth=encounter_depth)
    return result


def activate_process(state, comparison, variants, *, normalization_reason, science_root=None):
    root = _root(science_root)
    _validate("experiments", comparison, root)
    contract = scientific_module("execution_contract")
    query_tools = scientific_module("query_instruments")
    checked = query_tools.validate_process_variants(variants)
    label = next(v["term"] for v in checked if v["provenance_category"] == "canonical-y")
    payload = contract.process_activation_payload(comparison, label, normalization_reason=normalization_reason,
                                                   prior_normalized_y_labels=state["activated_y"])
    result = copy.deepcopy(state)
    if label not in result["activated_y"]:
        result["activated_y"][label] = payload
        config = yaml.safe_load((root / "config.yaml").read_text())
        frozen = config["search"]["conservative_execution"]["process_trigger"]
        for source in frozen["sources"]:
            plan = query_tools.process_query_plan(source, checked)
            params = {"page": 1, "sort": "relevance_score:desc"} if source == "OpenAlex" else {"cursorMark": "*", "synonym": False, "resultType": "core"}
            key = contract.search_window_key(execution_phase="process-triggered", source=source,
                query_id="QDYN001", normalized_y_label=label, canonical_query=plan["query"], source_parameters=params,
                publication_cutoff=config["publication_cutoff"], requested_max_n=plan["max_results"])
            result["process_windows"][key] = {"window_key": key, "source": source, "query": plan["query"],
                "kind": "query", "phase": "process-triggered", "normalized_y_label": label,
                "limit": plan["max_results"], "cursor": None, "source_parameters": params,
                "trigger_comparison_id": comparison["comparison_id"], "lexical_provenance": list(checked), "status": "pending"}
        _invalidate(result)
    _event(result, "earned-y-activation", normalization_reason, payload=payload)
    return result


def due_obligations(state):
    """Return source tasks and native work units without closing any frontier."""
    result = []
    for obligation in state["citation_obligations"].values():
        if obligation["status"] != "complete":
            task = copy.deepcopy(obligation)
            task.update(kind=obligation["direction"], limit=100, phase="citation", query="")
            if obligation["source"] == "publisher-or-repository-reference-list":
                task["task"] = "source-located-reference-list-acquisition"
            elif obligation["status"] in {"coverage-unresolved", "source-unresolved"}:
                task["task"] = "resolve-citation-source"
            result.append(task)
    result.extend(copy.deepcopy(w) for w in state["process_windows"].values() if w["status"] != "complete")
    if state["principal_provisionally_satisfied"]:
        result.extend(copy.deepcopy(w) for w in state["blind_windows"].values() if w["status"] != "complete")
    result.extend(copy.deepcopy(w) for w in state["native_assessment_pending"].values())
    result.extend(copy.deepcopy(w) for w in state.get("lineage_replay_pending", {}).values())
    return result


def complete_lineage_replay(state, obligation_id, *, reason):
    result = copy.deepcopy(state)
    if obligation_id not in result.get("lineage_replay_pending", {}):
        raise ValueError("No pending lineage replay")
    result["lineage_replay_pending"].pop(obligation_id)
    _event(result, "lineage-replay-completed", reason, obligation_id=obligation_id)
    return result


def complete_window(state, key, snapshot, *, snapshot_path, reason):
    result = copy.deepcopy(state)
    if snapshot.get("status") != "complete" or snapshot.get("result_set_sha256") != digest(snapshot.get("results")):
        raise ValueError("Incomplete retrieval cannot complete a scientific window")
    window = result["blind_windows"].get(key) or result["process_windows"].get(key)
    if window is None:
        raise ValueError("Unknown window")
    if window["phase"] == "supplementary-blind" and not result["principal_provisionally_satisfied"]:
        raise ValueError("Principal frontier must be provisionally satisfied before blind lane")
    request = snapshot["request"]
    if any(request.get(k) != window.get(k) for k in ("source", "query", "limit", "cursor", "kind")):
        raise ValueError("Snapshot request does not match frozen window")
    if snapshot.get("next_cursor") is not None:
        raise ValueError("Bounded query window must not schedule another page")
    if window["status"] == "complete" and window.get("result_set_sha256") != snapshot["result_set_sha256"]:
        raise ValueError("Completed window results are immutable")
    window.update(status="complete", result_set_sha256=snapshot["result_set_sha256"],
                  snapshot_path=str(snapshot_path), retrieved_at=snapshot["retrieved_at"])
    _event(result, "window-completed", reason, window_key=key, result_set_sha256=snapshot["result_set_sha256"])
    return result


def citation_page(state, obligation_id, snapshot, *, snapshot_path, reason):
    result = copy.deepcopy(state)
    obligation = result["citation_obligations"][obligation_id]
    if snapshot.get("status") != "complete" or snapshot.get("result_set_sha256") != digest(snapshot.get("results")):
        raise ValueError("Failed citation page cannot advance/close an obligation")
    if obligation["status"] == "complete":
        raise ValueError("Citation direction is already complete; reuse stored snapshots")
    request = snapshot["request"]
    if request.get("source") != obligation["source"] or request.get("kind") != obligation["direction"] or request.get("cursor") != obligation["cursor"]:
        raise ValueError("Citation snapshot differs from pending request")
    if request.get("parent", {}).get("paper_id") != obligation["parent"]["paper_id"]:
        raise ValueError("Citation snapshot has wrong parent")
    nxt = snapshot.get("next_cursor")
    if not snapshot.get("exhausted") and (nxt is None or nxt == obligation["cursor"] or nxt in obligation["seen_cursors"]):
        raise ValueError("Citation cursor does not demonstrate progress")
    if snapshot.get("exhausted") and nxt is not None:
        raise ValueError("Exhausted citation snapshot still advertises a cursor")
    total = snapshot.get("reported_total")
    if not isinstance(total, int) or total < 0:
        raise ValueError("Citation snapshot requires the source's reported coverage count")
    same_source_pages = [p for p in obligation["pages"] if p["source"] == obligation["source"]]
    if same_source_pages and any(p.get("reported_total") != total for p in same_source_pages):
        raise ValueError("Citation count changed during pagination; snapshot is inconsistent and needs explicit resolution")
    encountered = sum(p["result_count"] for p in same_source_pages) + len(snapshot["results"])
    if encountered > total or (snapshot["exhausted"] and encountered != total):
        raise ValueError("Citation result count does not match demonstrated source exhaustion")
    obligation["pages"].append({"path": str(snapshot_path), "result_set_sha256": snapshot["result_set_sha256"],
                                "request_sha256": snapshot["request_sha256"], "source": obligation["source"],
                                "result_count": len(snapshot["results"]), "reported_total": total,
                                "cursor": obligation["cursor"], "retrieved_at": snapshot["retrieved_at"]})
    obligation["seen_cursors"].append(obligation["cursor"])
    obligation["cursor"] = nxt
    obligation["status"] = "complete" if snapshot["exhausted"] else "pending"
    _event(result, "citation-page", reason, obligation_id=obligation_id, exhausted=snapshot["exhausted"])
    return result


def citation_failure(state, obligation_id, failure, *, reason):
    """Transient failure stays on the same source; missing coverage uses fallback."""
    result = copy.deepcopy(state)
    obligation = result["citation_obligations"][obligation_id]
    obligation["source_failures"].append({"source": obligation["source"], "cursor": obligation["cursor"],
                                         "failure": copy.deepcopy(failure), "at": now(), "reason": reason})
    if failure.get("status") == "unavailable":
        sources = ["OpenAlex", "Europe PMC"] + (["Crossref", "publisher-or-repository-reference-list"] if obligation["direction"] == "backward" else [])
        index = sources.index(obligation["source"])
        if index + 1 < len(sources):
            obligation["source"] = sources[index + 1]
            obligation["cursor"] = None
            obligation["seen_cursors"] = []
            obligation["status"] = "pending"
        else:
            obligation["status"] = "coverage-unresolved"
    else:
        obligation["status"] = "deferred" if failure.get("status") == "deferred" else "source-unresolved"
    _event(result, "citation-source-failure", reason, obligation_id=obligation_id)
    return result


def audit_wave(state, *, wave_id, obligation_ids, new_potentially_relevant, screening_complete, reason):
    """Record a complete wave's screened yield, not unscreened retrieval counts."""
    result = copy.deepcopy(state)
    if not wave_id or not isinstance(new_potentially_relevant, int) or new_potentially_relevant < 0:
        raise ValueError("Wave ID and nonnegative post-screening count required")
    if not screening_complete:
        raise ValueError("A citation wave cannot be audited before all encountered works are screened")
    if not obligation_ids:
        raise ValueError("An empty audit cannot supply evidence of a completed backward/forward citation wave")
    if any(key not in result["citation_obligations"] or result["citation_obligations"][key]["status"] != "complete" for key in obligation_ids):
        raise ValueError("Wave has incomplete backward/forward source obligations")
    for key in obligation_ids:
        other = key.rsplit(":", 1)[0] + (":forward" if key.endswith(":backward") else ":backward")
        if other not in obligation_ids:
            raise ValueError("Wave must contain both citation directions for every parent")
    audit = {"wave_id": wave_id, "obligation_ids": list(obligation_ids), "new_potentially_relevant": new_potentially_relevant,
             "screening_complete": True, "at": now(), "reason": reason,
             "obligations_sha256": digest(result["citation_obligations"])}
    result["citation_wave_audits"].append(audit)
    _event(result, "citation-wave-audited", reason, wave_id=wave_id)
    return result


def enter_blind_lane(state, *, pending_semantic_jobs=0, reason):
    result = copy.deepcopy(state)
    errors = principal_errors(result, pending_semantic_jobs=pending_semantic_jobs)
    if errors:
        raise ValueError("; ".join(errors))
    result["principal_provisionally_satisfied"] = True
    result["phase"] = "supplementary-blind"
    _event(result, "blind-lane-entered", reason)
    return result


def principal_errors(state, *, pending_semantic_jobs=0):
    errors = []
    if not state["seed_initialization_complete"] or not state["anchor_initialization_complete"]:
        errors.append("Frozen empirical seeds and review anchors have not both been initialized")
    if any(w["status"] != "complete" for w in state["citation_obligations"].values()):
        errors.append("Citation directions/eligible one-hop bridges remain incomplete")
    if any(w["status"] != "complete" for w in state["process_windows"].values()):
        errors.append("Independently earned process windows remain incomplete")
    if state["native_assessment_pending"] or state.get("lineage_replay_pending") or pending_semantic_jobs:
        errors.append("Source reading, screening, or native eligibility audits remain pending")
    audits = state["citation_wave_audits"]
    if not audits or audits[-1]["new_potentially_relevant"] != 0 or audits[-1]["obligations_sha256"] != digest(state["citation_obligations"]):
        errors.append("No current complete backward/forward citation wave with zero newly relevant papers")
    return errors


def readiness(state, *, pending_semantic_jobs=0, missing_texts_current=False, durable_validation_passed=False):
    errors = principal_errors(state, pending_semantic_jobs=pending_semantic_jobs)
    if not state["principal_provisionally_satisfied"]:
        errors.append("Principal frontier was never provisionally satisfied")
    if set(state["blind_windows"]) != {w["window_key"] for w in blind_windows()} or any(w["status"] != "complete" for w in state["blind_windows"].values()):
        errors.append("Mandatory blind windows are incomplete")
    if not missing_texts_current:
        errors.append("Missing-text state has not been reconciled")
    if not durable_validation_passed:
        errors.append("Scientific records, snapshot hashes, provenance, and derived outputs require native validation")
    return {"ready": not errors, "errors": errors,
            "scope": "Scientific frontier completion still requires the frozen native validator; queue exhaustion is insufficient"}


def native_work_unit(paper_id, assets, reason):
    return {"task": "native-discovery-audit", "paper_id": paper_id, "assets": list(assets), "reason": reason,
            "instructions": "Read the supplied sources under PROTOCOL §§8–9. Record typed physical experiment groups, citation ingredients and reasons. Derive CORE/strict BRIDGE using execution_contract. For any independently eligible process comparison, provide the complete native comparison and provenance-backed normalized-Y variants. If unsupported or source missing, retain an explicit unresolved reason; a prospect decision cannot substitute for native judgments."}
