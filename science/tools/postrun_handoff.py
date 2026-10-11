"""Source-linked prospects for human vetting; scientific claims remain separate."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any
from urllib.parse import unquote

from jsonschema import Draft202012Validator, FormatChecker

from derived_views import (
    audited_functional_y,
    completed_result_audit,
    constraint_awareness_difference,
    constraint_equivalence_supported,
    constraint_null_supported,
    constraint_unaware_capacity,
    no_detectable_awareness_difference,
)
from scientific_policy import (
    SUPPORTED_STATS,
    difference_provenance_errors,
    human_profile_comparison,
)
from execution_contract import scientific_reading_claim_review
from validate_run import convert_cell


HERE = Path(__file__).resolve().parent
PACKAGE_ROOT = HERE.parent
VERSION = "0.5.0"
TIERS = (
    "profile-prospect", "qualified-primary-prospect", "valuable-support", "conditional-check-read",
    "backup-context", "unresolved-source-request",
)
DERIVED_ITEM_FIELDS = {"title", "work_key", "source_path", "source_sha256", "article_version", "bound_comparison", "source_review", "human_review"}
INPUT_FILES = ("run_state.json", "papers_master.csv", "experiment_groups.csv", "experiments_master.csv", "fulltext_assets.csv", "missing_texts.csv", "auxiliary_sources.csv", "evidence_assessments.csv", "evidence_bundles.csv", "evidence_links.csv", "decision_log.jsonl")
REVIEW_TABLES = {
    "experiments_master.csv": "experiments.schema.json", "experiment_groups.csv": "experiment_groups.schema.json",
    "fulltext_assets.csv": "fulltext_assets.schema.json", "auxiliary_sources.csv": "auxiliary_sources.schema.json",
    "evidence_assessments.csv": "evidence_assessments.schema.json", "evidence_bundles.csv": "evidence_bundles.schema.json",
    "evidence_links.csv": "evidence_links.schema.json",
}
SIDECAR_FILES = (
    "tools/postrun_handoff.py", "schemas/postrun_handoff.schema.json",
    "tools/postrun_human_decisions.py", "schemas/postrun_human_decision.schema.json",
    "tools/derived_views.py", "tools/scientific_policy.py",
    "tools/execution_contract.py", "tools/validate_run.py",
    "tools/statistical_consistency.py",
)
BOUND_COMPARISON_FIELDS = (
    "comparison_id", "experiment_id", "X_label", "Y_label",
    "difference_tested", "difference_analysis_scope", "difference_source_experiment_id", "difference_joint_experiment_ids",
    "difference_source_location", "difference_statistic_or_test", "difference_analysis_origin",
    "difference_derivation", "awareness_effect", "awareness_effect_estimate",
    "awareness_effect_estimate_interpretable", "awareness_effect_stats_status",
    "awareness_effect_stats_reason", "unaware_capacity", "unaware_capacity_critical_effect",
    "unaware_capacity_stats_status", "unaware_capacity_stats_reason",
    "A_code", "A_reason", "awareness_regime_evidence", "unaware_capacity_regime_keys", "E_code", "E_reason", "F_code", "F_reason",
    "comparison_validity", "comparison_validity_reason", "evidence_strength_reason",
)


class HandoffError(ValueError):
    pass


def canonical(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def schema_check(value: dict[str, Any]) -> None:
    schema = json.loads((PACKAGE_ROOT / "schemas/postrun_handoff.schema.json").read_text(encoding="utf-8"))
    errors = sorted(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(value), key=lambda e: str(e.path))
    if errors:
        raise HandoffError("schema: " + "; ".join(f"{'.'.join(map(str, e.path)) or '<root>'}: {e.message}" for e in errors))


def within(root: Path, name: str) -> Path:
    if not name or Path(name).is_absolute():
        raise HandoffError(f"repository-relative path required: {name!r}")
    target = (root / name).resolve()
    try:
        target.relative_to(root.resolve())
    except ValueError as exc:
        raise HandoffError(f"path escapes repository: {name}") from exc
    return target


def rows(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise HandoffError(f"missing run file: {path}")
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def norm_doi(value: str) -> str:
    value = unquote(value.strip()).lower()
    return re.sub(r"^(https?://(dx\.)?doi\.org/|doi:)", "", value).strip()


def work_key(paper: dict[str, str]) -> str:
    doi = norm_doi(paper.get("doi", ""))
    if doi:
        return "doi:" + doi
    normalize = lambda s: " ".join(re.findall(r"\w+", (s or "").casefold()))
    return "metadata:" + "|".join(normalize(paper.get(k, "")) for k in ("title", "year", "authors"))


def _index(data: list[dict[str, str]], key: str, label: str) -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    for row in data:
        ident = row.get(key, "")
        if not ident or ident in out:
            raise HandoffError(f"duplicate/empty {key} in {label}: {ident!r}")
        out[ident] = row
    return out


def typed_review_tables(run_dir: Path) -> dict[str, list[dict[str, Any]]]:
    """Use the native CSV codec so source bindings equal the run validator's.

    Full schema/reference validation is mandatory in build/validate for both
    handoff statuses. This pure preparation path also checks source receipts.
    """
    tables = {}
    for name, schema_name in REVIEW_TABLES.items():
        schema = json.loads((PACKAGE_ROOT / "schemas" / schema_name).read_text(encoding="utf-8"))
        decoded = []
        for row in rows(run_dir / name):
            try:
                decoded.append({key: convert_cell(key, value, schema["properties"][key], schema)
                                for key, value in row.items()})
            except (KeyError, ValueError, TypeError, json.JSONDecodeError) as exc:
                raise HandoffError(f"invalid source-review table {name}: {exc}") from exc
        tables[name] = decoded
    return tables


def load_runs(draft: dict[str, Any], root: Path) -> tuple[dict[str, Any], dict[str, str], dict[str, str]]:
    root = root.resolve()
    contexts: dict[str, Any] = {}
    hashes: dict[str, str] = {}
    work_map: dict[str, str] = {}
    for run in draft["input_runs"]:
        run_id = run["run_id"]
        if run_id in contexts:
            raise HandoffError(f"duplicate input run: {run_id}")
        run_dir = within(root, run["run_dir"])
        if run_dir.name != run_id:
            raise HandoffError(f"run directory does not match run_id: {run_id}")
        for name in INPUT_FILES:
            path = run_dir / name
            if not path.is_file():
                raise HandoffError(f"missing run file: {path}")
            hashes[path.relative_to(root).as_posix()] = digest(path)
        state = json.loads((run_dir / "run_state.json").read_text(encoding="utf-8"))
        if state.get("run_id") != run_id:
            raise HandoffError(f"run_state ID mismatch: {run_id}")
        if draft["status"] == "final" and state.get("status") != "complete":
            raise HandoffError(f"final handoff requires complete run: {run_id}")
        contexts[run_id] = {
            "state": state,
            "papers": _index(rows(run_dir / "papers_master.csv"), "paper_id", run_id),
            "comparisons": _index(rows(run_dir / "experiments_master.csv"), "comparison_id", run_id),
            "groups": _index(rows(run_dir / "experiment_groups.csv"), "experiment_id", run_id),
            "assets": _index(rows(run_dir / "fulltext_assets.csv"), "fulltext_asset_id", run_id),
            "missing": _index(rows(run_dir / "missing_texts.csv"), "paper_id", run_id),
            "typed_tables": typed_review_tables(run_dir),
            "decisions": [json.loads(line) for line in (run_dir / "decision_log.jsonl").read_text(encoding="utf-8").split("\n") if line.strip()],
        }
    if len(contexts) > 1:
        name = draft["adjudication_manifest"]
        if not name:
            raise HandoffError("multiple runs require an adjudication manifest")
        path = within(root, name)
        if not path.is_file():
            raise HandoffError("adjudication manifest missing")
        adjudication = json.loads(path.read_text(encoding="utf-8"))
        if adjudication.get("status") != "complete" or set(adjudication.get("input_run_ids", [])) != set(contexts):
            raise HandoffError("adjudication manifest does not cover completed input runs")
        work_map = adjudication.get("work_map", {})
        if not isinstance(work_map, dict) or not all(isinstance(key, str) and isinstance(value, str) and value for key, value in work_map.items()):
            raise HandoffError("adjudication work_map must identify canonical logical works")
        hashes[path.relative_to(root).as_posix()] = digest(path)
    elif draft["adjudication_manifest"] is not None:
        raise HandoffError("single-run handoff must not claim multi-run adjudication")
    return contexts, hashes, work_map


def claim_comparison(item: dict[str, Any], ctx: dict[str, Any]) -> dict[str, str] | None:
    """Bind an authored recommendation to one existing scientific comparison.

    Label equality checks identity, not whether either label is scientifically
    justified. That interpretation remains a source-focused semantic review.
    """
    comparison_id = item["claim_comparison_id"]
    if comparison_id is None:
        return None
    if comparison_id not in item["comparison_ids"]:
        raise HandoffError(f"claim comparison must be among comparison_ids: {item['item_id']}")
    comparison = ctx["comparisons"].get(comparison_id)
    if comparison is None or comparison.get("paper_id") != item["paper_id"]:
        raise HandoffError(f"stale or cross-paper claim comparison: {comparison_id}")
    if item["X"] != comparison.get("X_label") or item["Y"] != comparison.get("Y_label"):
        raise HandoffError(f"authored X/Y must match the selected claim comparison labels: {item['item_id']}")
    return comparison


def prospect_comparison_located(comparison: dict[str, str]) -> bool:
    """A located design is not a certified effect, awareness route or inference."""
    return (human_profile_comparison(comparison)
            and comparison.get("F_code") == "F-meaningful"
            and audited_functional_y(comparison)
            and comparison.get("A_code") in {"A-direct", "A-validated", "A-transfer-risk"})


def prospect_admissibility(item: dict[str, Any], comparison: dict[str, str] | None) -> None:
    """Retain argued uncertainty without relabeling known irrelevance as a question.

    These are consistency checks on recorded judgments, not another scientific
    classifier. Weak E, uncertain transfer and unresolved statistics do not
    disqualify a reading prospect. A missing direct test can itself be the
    specific analysis question for a located same-function awareness design.
    """
    if comparison is None:
        raise HandoffError(f"prospect requires a selected comparison: {item['item_id']}")
    outside = {
        "population_scope": {"out-of-scope", "linked-other-system"},
        "awareness_contrast_type": {"none"},
        "comparison_validity": {"not-comparable", "not-applicable"},
        "F_code": {"F-not-meaningful"},
        "Y_functional_status": {"effect-only"},
    }
    for field, values in outside.items():
        if comparison.get(field) in values:
            raise HandoffError(f"known outside-brief comparison cannot be a prospect ({field}): {item['item_id']}")
    expected = "comparison-located" if prospect_comparison_located(comparison) else "comparison-unresolved"
    if item["prospect_relation"] != expected:
        raise HandoffError(f"prospect_relation must be {expected} for the recorded comparison: {item['item_id']}")
    if comparison.get("difference_tested") == "yes":
        errors = difference_provenance_errors(comparison)
        if errors:
            raise HandoffError(f"invalid recorded prospect test for {item['item_id']}: {'; '.join(errors)}")


def recommendation_admissibility(item: dict[str, Any], comparison: dict[str, str] | None) -> None:
    """Enforce the narrow reading tiers without changing scientific exports."""
    tier = item["tier"]
    if tier in {"backup-context", "unresolved-source-request"}:
        return
    if tier in {"profile-prospect", "conditional-check-read"}:
        prospect_admissibility(item, comparison)
        return
    if comparison is None:
        raise HandoffError(f"evidence recommendation requires a selected claim comparison: {item['item_id']}")
    support_audit_without_strong_route = (
        tier == "valuable-support"
        and comparison.get("current_status") == "fully-evaluated"
        and comparison.get("structural_audit_status") == "complete"
        and comparison.get("result_inspection_status") == "not-required"
    )
    if not (completed_result_audit(comparison) or support_audit_without_strong_route) or not human_profile_comparison(comparison):
        raise HandoffError(f"evidence recommendation requires a completed comparable human awareness design: {item['item_id']}")
    if comparison.get("F_code") != "F-meaningful" or not audited_functional_y(comparison):
        raise HandoffError(f"evidence recommendation requires a meaningful same-function Y: {item['item_id']}")
    if comparison.get("difference_tested") != "yes":
        raise HandoffError(f"evidence recommendation requires a direct same-Y awareness test: {item['item_id']}")
    provenance_errors = difference_provenance_errors(comparison)
    if provenance_errors:
        raise HandoffError(f"invalid direct same-Y test for {item['item_id']}: {'; '.join(provenance_errors)}")
    if tier == "valuable-support":
        if comparison.get("A_code") not in {"A-direct", "A-validated", "A-transfer-risk"}:
            raise HandoffError(f"qualified awareness support requires an actual awareness assessment: {item['item_id']}")
        if (comparison.get("awareness_effect_estimate_interpretable") != "yes"
                or comparison.get("awareness_effect_stats_status") not in SUPPORTED_STATS):
            raise HandoffError(f"qualified awareness support requires an interpretable direct test with adequate or nonfatal-concern statistics: {item['item_id']}")
        # Weak E or uncertain transfer can limit useful support. Neither is
        # silently recoded or made a gate for the broad capacity/search routes.
        return
    try:
        if item["claim_basis"] == "awareness-linked-change":
            admissible = constraint_awareness_difference(comparison)
        else:
            positive_capacity = (comparison.get("A_code") in {"A-direct", "A-validated"}
                                 and constraint_unaware_capacity(comparison))
            positive_null = (
                constraint_equivalence_supported(comparison)
                or constraint_null_supported(comparison)
            )
            descriptive_nondifference = (
                no_detectable_awareness_difference(comparison)
                and comparison.get("awareness_effect_estimate_interpretable") == "yes"
                and comparison.get("awareness_effect_stats_status") in SUPPORTED_STATS
            )
            # Descriptive nondifference remains descriptive, including under
            # weak E. Positive equivalence/Bayesian claims retain their existing
            # scientific E requirements through the shared route predicates.
            admissible = positive_capacity and (positive_null or descriptive_nondifference)
    except KeyError as exc:
        raise HandoffError(f"claim comparison lacks a required scientific field: {exc.args[0]}") from exc
    if not admissible:
        raise HandoffError(f"primary claim basis is not supported by the selected comparison: {item['item_id']}")


def bind_comparison(comparison: dict[str, str] | None, asset: dict[str, str]) -> dict[str, str] | None:
    """Generate a receipt from the current comparison and verified source."""
    if comparison is None:
        return None
    receipt = {field: comparison.get(field, "") for field in BOUND_COMPARISON_FIELDS}
    receipt.update(
        comparison_sha256=hashlib.sha256(canonical(comparison)).hexdigest(),
        source_asset_id=asset["fulltext_asset_id"],
        source_sha256=asset["file_sha256"],
    )
    return receipt


def prepare(draft: dict[str, Any], root: Path) -> tuple[dict[str, Any], dict[str, str]]:
    root = root.resolve()
    schema_check(draft)
    if "counts" in draft or any(DERIVED_ITEM_FIELDS.intersection(item) for item in draft["items"]):
        raise HandoffError("authored input cannot contain generated fields")
    contexts, hashes, work_map = load_runs(draft, root)
    # Existing explicit human decisions remain visible. This read-only stage
    # never records acceptance or changes the scientific recommendation.
    from postrun_human_decisions import read_events
    human_path = root / "outputs/human_review/decision_log.jsonl"
    human_events = read_events(human_path)
    human_aliases: dict[str, set[str]] = {}
    for mapped_run, mapped_context in contexts.items():
        for mapped_paper, mapped in mapped_context["papers"].items():
            identity = work_map.get(f"{mapped_run}:{mapped_paper}")
            if identity:
                human_aliases.setdefault(identity, set()).add(work_key(mapped))
    if human_path.exists():
        hashes[human_path.relative_to(root).as_posix()] = digest(human_path)
    seen_items: set[str] = set()
    seen_works: set[str] = set()
    out = dict(draft)
    out["items"] = []
    for item in draft["items"]:
        item_id = item["item_id"]
        if item_id in seen_items:
            raise HandoffError(f"duplicate handoff item: {item_id}")
        seen_items.add(item_id)
        ctx = contexts.get(item["run_id"])
        if ctx is None:
            raise HandoffError(f"item references undeclared run: {item_id}")
        paper = ctx["papers"].get(item["paper_id"])
        if paper is None:
            raise HandoffError(f"stale paper reference: {item_id}")
        if paper.get("duplicate_of") or paper.get("current_status") == "duplicate":
            raise HandoffError(f"item references superseded duplicate paper: {item_id}")
        key = work_key(paper)
        if len(contexts) > 1:
            canonical_identity = work_map.get(f"{item['run_id']}:{item['paper_id']}")
            if not canonical_identity:
                raise HandoffError(f"adjudication work_map omits item: {item_id}")
            key = "adjudicated:" + canonical_identity
        if key in seen_works:
            raise HandoffError(f"duplicate logical work: {key}")
        seen_works.add(key)
        for comparison_id in item["comparison_ids"]:
            comparison = ctx["comparisons"].get(comparison_id)
            if comparison is None or comparison.get("paper_id") != item["paper_id"]:
                raise HandoffError(f"stale or cross-paper comparison: {comparison_id}")
        for group_id in item.get("experiment_group_ids", []):
            group = ctx["groups"].get(group_id)
            if group is None or group.get("paper_id") != item["paper_id"]:
                raise HandoffError(f"stale or cross-paper experiment group: {group_id}")
            if group.get("record_status", "active") != "active":
                raise HandoffError(f"retired nonphysical experiment record cannot support a recommendation: {group_id}")
            if (group.get("pre_atomization_assessed", "").lower() not in {"true", "1"}
                    or group.get("disposition") not in {"support-only", "no-qualifying-comparison"}):
                raise HandoffError(f"experiment group lacks assessed support-only disposition: {group_id}")
        selected_comparison = claim_comparison(item, ctx)
        recommendation_admissibility(item, selected_comparison)
        enriched = dict(item)
        enriched.update(title=paper["title"], work_key=key, source_path=None, source_sha256=None, article_version=None, bound_comparison=None, source_review=None)
        # Adjudication establishes identity across the included records. Reuse
        # decisions under either that canonical key or any mapped native key;
        # append order determines the latest explicit decision across aliases.
        human_keys = {key, work_key(paper)}
        if len(contexts) > 1:
            human_keys.update(human_aliases.get(canonical_identity, set()))
        human = next((event for event in reversed(human_events) if event["work_key"] in human_keys), None)
        enriched["human_review"] = ({"role": human["role"], "event_id": human["event_id"],
                                     "article_version": human["article_version"], "source_reference": human["source_reference"]}
                                    if human else None)
        if human and human["role"] != "pending":
            enriched["first_read"] = False
        if item["tier"] == "unresolved-source-request":
            missing = ctx["missing"].get(item["paper_id"])
            if missing is None or missing.get("status") not in {"pending", "manually-requested", "unavailable"}:
                raise HandoffError(f"unresolved request lacks open missing-text record: {item_id}")
            if missing.get("priority") != item["request_priority"]:
                raise HandoffError(f"request priority differs from missing-text state: {item_id}")
        else:
            asset = ctx["assets"].get(item["asset_id"])
            if asset is None or asset.get("paper_id") != item["paper_id"]:
                raise HandoffError(f"stale or cross-paper asset: {item_id}")
            if asset.get("current_for_paper", "").lower() not in {"true", "1"}:
                raise HandoffError(f"asset is not current for paper: {item_id}")
            source_name = asset.get("local_fulltext_path", "")
            source = within(root, source_name)
            if not source.is_file() or digest(source) != asset.get("file_sha256"):
                raise HandoffError(f"missing or bad asset hash: {item_id}")
            hashes[source_name] = digest(source)
            enriched.update(source_path=source_name, source_sha256=asset["file_sha256"], article_version=asset["article_version"])
            enriched["bound_comparison"] = bind_comparison(selected_comparison, asset)
            if item["tier"] in {"qualified-primary-prospect", "valuable-support"}:
                typed = next(row for row in ctx["typed_tables"]["experiments_master.csv"]
                             if row["comparison_id"] == selected_comparison["comparison_id"])
                try:
                    enriched["source_review"] = scientific_reading_claim_review(
                        item, typed, ctx["state"], ctx["typed_tables"], ctx["decisions"])
                except (ValueError, KeyError, TypeError) as exc:
                    raise HandoffError(f"reading recommendation source check failed: {exc}") from exc
        out["items"].append(enriched)
    by_tier = Counter(item["tier"] for item in out["items"])
    out["counts"] = {"total": len(out["items"]), "first_read": sum(item["first_read"] for item in out["items"]), "by_tier": {tier: by_tier[tier] for tier in TIERS}}
    schema_check(out)
    return out, hashes


def guide(handoff: dict[str, Any]) -> str:
    title = f"# Reading handoff {handoff['handoff_id']} ({handoff['status']})"
    lines = [title, "", f"Source-backed pipeline recommendations. Explicit human decisions are shown separately. Sidecar {VERSION}.", "", f"Total: {handoff['counts']['total']}; first read: {handoff['counts']['first_read']}.", ""]
    decided = lambda item: bool(item.get("human_review") and item["human_review"]["role"] != "pending")
    evidence_tiers = {"profile-prospect", "qualified-primary-prospect", "valuable-support", "conditional-check-read"}
    groups = (
        ("Prospects for human vetting", [item for item in handoff["items"] if item["tier"] in evidence_tiers and not decided(item)]),
        ("Backup Context", [item for item in handoff["items"] if item["tier"] == "backup-context" and not decided(item)]),
        ("Unresolved Source Requests", [item for item in handoff["items"] if item["tier"] == "unresolved-source-request" and not decided(item)]),
        ("Previously decided — outside the prospect queue", [item for item in handoff["items"] if decided(item)]),
    )
    for heading, items in groups:
        lines.extend((f"## {heading} ({len(items)})", ""))
        for item in items:
            lines.append(f"### {item['title']} ({item['item_id']})" + (" — first read" if item["first_read"] else ""))
            lines.append("")
            human = item.get("human_review")
            lines.append(f"Human decision: {human['role']} ({human['event_id']}; {human['article_version']})." if human else "Human decision: pending.")
            lines.append("")
            if human and human["role"] == "declined":
                lines.extend(("Previously declined; retained here as history, outside the first-read queue.", ""))
            lines.append(f"X → Y: {item['X']} → {item['Y']}. {item['manuscript_contribution']}")
            lines.append("")
            if item["measured_outcome"] is not None:
                lines.append(f"Measured outcome: {item['measured_outcome']}.")
                lines.append("")
            prospect = item["tier"] in {"profile-prospect", "conditional-check-read"}
            label = "Tentative inference for vetting" if prospect else "Claim"
            lines.append(f"{label} ({item['claim_basis']}; {item['result_direction']}): {item['claim']}")
            lines.append("")
            if prospect:
                lines.extend((f"Decisive source evidence: {item['decisive_evidence']}", "",
                              f"Limitation: {item['limitation']}", "",
                              f"Human reading question: {item['human_question']}", "",
                              f"Why read: {item['reason']}", "",
                              f"Tentative placement: {item['tentative_role']}; {item['prospect_relation']}. This is a reading prospect; no verified scientific conclusion is claimed.", ""))
            elif item["tier"] in {"qualified-primary-prospect", "valuable-support"}:
                lines.extend((f"Located evidence: {item['source_location']}. {item['claim_review_reason']}", "",
                              f"Limitation: {item['limitation']}", "",
                              f"Checked recommendation: {item['tier']}; human acceptance remains pending unless recorded above.", ""))
            bound = item.get("bound_comparison")
            if bound is not None:
                test = bound["difference_statistic_or_test"] or "no direct test recorded"
                location = bound["difference_source_location"] or "no direct-test source location recorded"
                lines.append(f"Bound comparison {bound['comparison_id']} ({bound['experiment_id']}): direct same-Y test = {bound['difference_tested'] or 'not recorded'}; {test}; {location}.")
                lines.append("")
                if bound["difference_analysis_scope"] == "joint-analysis":
                    lines.append(f"Joint-analysis contributors: {bound['difference_joint_experiment_ids']}; source anchor: {bound['difference_source_experiment_id']}.")
                    lines.append("")
                lines.append(f"Awareness result: {bound['awareness_effect'] or 'not recorded'}; estimate: {bound['awareness_effect_estimate'] or 'not recorded'}; statistics: {bound['awareness_effect_stats_status'] or 'not recorded'}. {bound['awareness_effect_stats_reason']}")
                lines.append("")
                if item["claim_basis"] == "preserved-capacity":
                    lines.append(f"Positive unaware capacity: {bound['unaware_capacity'] or 'not recorded'}; {bound['unaware_capacity_critical_effect'] or 'critical effect not recorded'}. {bound['unaware_capacity_stats_reason']}")
                    lines.append("")
                    if bound["awareness_effect"] == "no-detectable-difference":
                        lines.append("This is a directly tested descriptive nondifference, not established equivalence. Signal-control limitations remain part of the interpretation.")
                        lines.append("")
                lines.append(f"Awareness and interpretation limits: {bound['A_code'] or 'A not recorded'} — {bound['A_reason'] or 'reason not recorded'}; {bound['E_code'] or 'E not recorded'} — {bound['E_reason'] or 'reason not recorded'}; {bound['F_code'] or 'F not recorded'} — {bound['F_reason'] or 'reason not recorded'}.")
                lines.append("")
            if item["tier"] == "conditional-check-read":
                lines.append(f"Unresolved question: {item['claim_review_reason']}")
                lines.append("")
            if not prospect:
                lines.append(f"Why read: {item['reason']} Limitation: {item['limitation']}")
                lines.append("")
            lines.append(f"Evidence level compared with the manuscript: {item['evidence_level_comparison']}")
            lines.append("")
            if item["source_path"]:
                lines.append(f"Source: [article file](<../../../{item['source_path']}>) ({item['article_version']}), {item['source_location']}; comparisons: {', '.join(item['comparison_ids'])}.")
                if item.get("experiment_group_ids"):
                    lines.append(f"Supporting experiment groups: {', '.join(item['experiment_group_ids'])}.")
            else:
                lines.append(f"Source request ({item['request_priority']}): {item['request_reason']}")
            lines.append("")
            lines.append(f"Claim review: {item['claim_review']} by {item['reviewed_by']} — {item['claim_review_reason']} Redundancy: {item['redundancy_note']}")
            if item.get("source_review"):
                checked = item["source_review"]
                lines.append(f"Independent current-source claim review: {checked['decision_id']} by {checked['reviewer']} (scientific review {checked['scientific_review_decision_id']}).")
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def output_dir(root: Path, name: str) -> Path:
    path = within(root, name)
    relative = path.relative_to(root).parts
    if relative[:2] != ("outputs", "handoffs") or len(relative) != 3:
        raise HandoffError("handoff output must be under outputs/handoffs, never run or human-review state")
    if path.exists() and any(path.iterdir()):
        raise HandoffError("output directory must be absent or empty")
    return path


def check_full_run_validation(draft: dict[str, Any], root: Path) -> None:
    validator = root / "tools" / "validate_run.py"
    if not validator.is_file():
        raise HandoffError("handoff requires the package's validate_run.py for final and provisional source checks")
    for run in draft["input_runs"]:
        run_dir = within(root, run["run_dir"])
        result = subprocess.run(
            [sys.executable, str(validator), "--run-id", run["run_id"], "--root", str(root),
             "--runs-root", str(run_dir.parent)],
            cwd=root, capture_output=True, text=True, check=False,
        )
        if result.returncode != 0:
            detail = (result.stderr or result.stdout).strip().splitlines()
            raise HandoffError(f"full run validation failed for {run['run_id']}: {detail[-1] if detail else 'no diagnostic'}")


def build(draft_path: Path, root: Path, out_name: str, *, full_run_validation: bool = True) -> Path:
    root = root.resolve()
    draft = json.loads(draft_path.read_text(encoding="utf-8"))
    if full_run_validation:
        check_full_run_validation(draft, root)
    handoff, input_hashes = prepare(draft, root)
    out = output_dir(root, out_name)
    out.mkdir(parents=True, exist_ok=True)
    files = {
        "authored_input.json": canonical(draft),
        "reading_handoff.json": canonical(handoff),
        "reading_guide.md": guide(handoff).encode("utf-8"),
    }
    manifest = {"sidecar_version": VERSION, "handoff_id": handoff["handoff_id"], "sidecar_sha256": {name: digest(PACKAGE_ROOT / name) for name in SIDECAR_FILES}, "input_sha256": input_hashes, "output_sha256": {name: hashlib.sha256(data).hexdigest() for name, data in files.items()}}
    files["input_manifest.json"] = canonical(manifest)
    for name, data in files.items():
        (out / name).write_bytes(data)
    return out


def validate(root: Path, out_name: str, *, full_run_validation: bool = True) -> None:
    root = root.resolve()
    out = within(root, out_name)
    manifest = json.loads((out / "input_manifest.json").read_text(encoding="utf-8"))
    if manifest.get("sidecar_version") != VERSION:
        raise HandoffError("sidecar version mismatch")
    for name in SIDECAR_FILES:
        if manifest.get("sidecar_sha256", {}).get(name) != digest(PACKAGE_ROOT / name):
            raise HandoffError(f"sidecar file hash drift: {name}")
    for name, expected in manifest.get("input_sha256", {}).items():
        if digest(within(root, name)) != expected:
            raise HandoffError(f"input hash drift: {name}")
    for name, expected in manifest.get("output_sha256", {}).items():
        if digest(out / name) != expected:
            raise HandoffError(f"output hash drift: {name}")
    draft = json.loads((out / "authored_input.json").read_text(encoding="utf-8"))
    if full_run_validation:
        check_full_run_validation(draft, root)
    expected, hashes = prepare(draft, root)
    if hashes != manifest["input_sha256"]:
        raise HandoffError("input manifest does not match current references")
    if canonical(expected) != (out / "reading_handoff.json").read_bytes():
        raise HandoffError("handoff JSON differs from current source records or counts")
    if guide(expected).encode("utf-8") != (out / "reading_guide.md").read_bytes():
        raise HandoffError("reading guide differs from handoff JSON or counts")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    build_parser = sub.add_parser("build")
    build_parser.add_argument("--draft", required=True, type=Path)
    for child in (build_parser, sub.add_parser("validate")):
        child.add_argument("--repo-root", required=True, type=Path)
        child.add_argument("--output-dir", required=True, help="repository-relative handoff directory")
    args = parser.parse_args()
    try:
        if args.command == "build":
            print(build(args.draft, args.repo_root, args.output_dir))
        else:
            validate(args.repo_root, args.output_dir)
            print("reading handoff valid")
    except (HandoffError, OSError, KeyError, json.JSONDecodeError) as exc:
        parser.exit(2, f"handoff error: {exc}\n")


if __name__ == "__main__":
    main()
