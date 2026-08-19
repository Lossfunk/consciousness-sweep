from __future__ import annotations

import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUN_ID = "PREFREEZE_DIAG_20260819"
RUN_DIR = ROOT / "runs" / RUN_ID
sys.path.insert(0, str(ROOT / "tools"))

from structured_write import allocate_identifier, append_jsonl_record, load_schema, write_csv_record  # noqa: E402

DECISION_SCHEMA = load_schema(ROOT, "decision_log.schema.json")
SCHEMAS = {
    "experiments_master.csv": load_schema(ROOT, "experiments.schema.json"),
    "evidence_bundles.csv": load_schema(ROOT, "evidence_bundles.schema.json"),
    "evidence_links.csv": load_schema(ROOT, "evidence_links.schema.json"),
}


def now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def log(entity_type, entity_id, decision_type, field, old, new, reason, source=""):
    did = allocate_identifier(RUN_DIR, "decision")
    append_jsonl_record(RUN_DIR / "decision_log.jsonl", DECISION_SCHEMA, {
        "decision_id": did, "run_id": RUN_ID, "timestamp": now(), "entity_type": entity_type,
        "entity_id": entity_id, "decision_type": decision_type, "field": field,
        "old_value": old, "new_value": new, "reason": reason, "source_location": source,
        "agent": "codex-desktop/gpt-5",
    })


def write(table, row, key=None):
    write_csv_record(RUN_DIR / table, SCHEMAS[table], row, key_field=key)


def load_rows():
    with (RUN_DIR / "experiments_master.csv").open(newline="", encoding="utf-8") as f:
        raw = list(csv.DictReader(f))
    schema = SCHEMAS["experiments_master.csv"]
    array_fields = {"evidence_bundle_ids", "E_diagnostic_source_locations", "factorial_component_effects", "stats_flags"}
    number_fields = {"null_BF01"}
    rows = {}
    for r in raw:
        out = {}
        for k, v in r.items():
            if k in array_fields:
                out[k] = json.loads(v) if v else []
            elif k in number_fields:
                out[k] = float(v) if v else None
            else:
                prop = schema["properties"][k]
                if v == "":
                    out[k] = None
                elif v == "true":
                    out[k] = True
                elif v == "false":
                    out[k] = False
                else:
                    out[k] = v
        rows[out["comparison_id"]] = out
    return rows


def add_bundle(row, premise, status, source_type, role, member_status, claim, source_location,
               supporting_paper_id=None, supporting_experiment_id=None, transfer_reason="Same experiment and regime.",
               limitation=None):
    bid = allocate_identifier(RUN_DIR, "evidence_bundle")
    bundle = {
        "evidence_bundle_id": bid, "focal_comparison_id": row["comparison_id"],
        "supported_premise": premise,
        "premise_description": claim,
        "route_label": "E-diagnostic" if premise == "E-diagnostic" else "unresolved dependency audit",
        "required_member_keys": ["required-source"], "bundle_status": "incomplete",
        "bundle_reason": "Initialized before required direct link.", "notes": "Validation repair recorded append-first.",
    }
    log("evidence_bundle", bid, "evidence-bundle-created", "required_member_keys", None, ["required-source"],
        "Validator requires explicit scientific linkage for this premise.", source_location)
    write("evidence_bundles.csv", bundle)
    lid = allocate_identifier(RUN_DIR, "evidence_link")
    link = {
        "evidence_link_id": lid, "evidence_bundle_id": bid, "member_key": "required-source",
        "focal_comparison_id": row["comparison_id"], "supporting_paper_id": supporting_paper_id,
        "supporting_experiment_id": supporting_experiment_id, "supporting_auxiliary_id": None,
        "evidence_assessment_id": None, "supporting_source_type": source_type, "support_role": role,
        "dependency_role": "required", "member_status": member_status, "supported_claim": claim,
        "transfer_reason": transfer_reason, "transfer_limitation": limitation,
        "source_location": source_location, "used_for_decision": status == "complete",
        "notes": "Direct premise-specific link.",
    }
    log("evidence_link", lid, "evidence-link-created", "member_status", None, member_status, claim, source_location)
    write("evidence_links.csv", link)
    final_reason = ("The required same-experiment analysis is available, evaluated, and directly supports the premise."
                    if status == "complete" else "The required supplement content is unavailable in the supplied source set.")
    log("evidence_bundle", bid, "evidence-bundle-status-derived", "bundle_status", "incomplete", status,
        final_reason, source_location)
    bundle["bundle_status"] = status
    bundle["bundle_reason"] = final_reason
    write("evidence_bundles.csv", bundle, "evidence_bundle_id")
    old = list(row["evidence_bundle_ids"])
    row["evidence_bundle_ids"].append(bid)
    log("comparison", row["comparison_id"], "evidence-bundle-linkage", "evidence_bundle_ids", old,
        row["evidence_bundle_ids"], "The comparison now names every bundle used or required by its dependency status.", source_location)
    write("experiments_master.csv", row, "comparison_id")


def excluded_support_row(paper_id, experiment_id, label, source):
    cid = allocate_identifier(RUN_DIR, "comparison", experiment_id)
    # Required fields are retained, but scientific fields remain null because this is explicitly not an X→Y comparison.
    row = {
        "comparison_id": cid, "experiment_id": experiment_id, "paper_id": paper_id,
        "experiment_label": label, "X_label": None, "X_description": None, "awareness_measure": None,
        "awareness_evidence_type": None, "objective_visibility_test_informative": None,
        "objective_visibility_test_reason": None, "A_code": None, "A_reason": None,
        "critical_dependency_status": None, "critical_dependency_reason": None, "evidence_bundle_ids": [],
        "structural_audit_status": "incomplete", "awareness_effect_route_status": "not-assessed",
        "awareness_effect_route_reason": None, "unaware_capacity_route_status": "not-assessed",
        "unaware_capacity_route_reason": None, "null_equivalence_route_status": "not-assessed",
        "null_equivalence_route_reason": None, "result_inspection_status": "not-required",
        "result_inspection_reason": "The physical experiment is support-only and does not independently answer an X→Y question.",
        "first_order_measure": None, "E_code": None, "E_reason": None, "E_matching_basis": None,
        "E_equivalence_margin": None, "E_equivalence_result": None, "E_competing_account": None,
        "E_competing_prediction": None, "E_violating_pattern": None, "E_same_Y_reason": None,
        "E_diagnostic_source_locations": [], "Y_label": None, "Y_description": None, "Y_structure": None,
        "factorial_Y_reason": None, "factorial_component_effects": [], "Y_evidence_role": "not-assessed",
        "F_code": "F-not-meaningful", "F_reason": "This experiment is used only as a control/support and has no independent qualifying X→Y question.",
        "Y_interpretation_clarity": "unclear", "mechanistic_interpretation": None, "mechanism_clarity": "not-assessed",
        "critical_comparison": None, "unaware_capacity_claim": None, "unaware_capacity": None,
        "unaware_capacity_reason": None, "unaware_capacity_critical_effect": None,
        "unaware_capacity_stats_status": None, "unaware_capacity_stats_reason": None,
        "awareness_effect": None, "awareness_effect_reason": None, "direction": None,
        "awareness_effect_critical_effect": None, "awareness_effect_estimate": None,
        "awareness_effect_estimate_interpretable": None, "awareness_effect_stats_status": None,
        "awareness_effect_stats_reason": None, "difference_tested": None, "null_evidence_strength": None,
        "null_evidence_adequacy": None, "null_equivalence_margin": None, "null_equivalence_result": None,
        "null_BF01": None, "null_CI_region": None, "null_CI_entirely_within_region": None,
        "Meyen_role": None, "Meyen_applicable": None, "Meyen_status": None, "Meyen_reason": None,
        "stats_status": None, "stats_flags": [], "stats_reason": None, "constraint_summary": None,
        "source_pages": source, "source_figures_tables": None, "current_status": "excluded",
        "notes": "Execution-only excluded row added because the validator requires a durable table reference for a reserved support-only experiment ID already present in append-only history.",
    }
    log("comparison", cid, "support-only-exclusion", "current_status", None, "excluded",
        "The experiment is retained only to resolve the validator's experiment-reference check; it is not promoted to a scientific X→Y comparison.", source)
    write("experiments_master.csv", row)


def main():
    rows = load_rows()

    # No-detectable-difference is itself a required null audit, even when evidence is weak.
    for cid in ["P000002_E01_C01", "P000003_E01_C01", "P000003_E02_C01", "P000003_E03_C01"]:
        row = rows[cid]
        old = row["null_equivalence_route_status"]
        row["null_equivalence_route_status"] = "required"
        row["null_equivalence_route_reason"] = "The no-detectable-difference category requires an explicit null audit; evidence is nonsignificant-only and therefore weak, not equivalent."
        log("comparison", cid, "null-route-correction", "null_equivalence_route_status", old, "required",
            row["null_equivalence_route_reason"], row["source_pages"] or "Supplied PDF")
        write("experiments_master.csv", row, "comparison_id")

    # These Lamy rows use a conservative observed cost and therefore have no classification-critical external dependency.
    for cid in ["P000003_E01_C02", "P000003_E02_C02", "P000003_E03_C02"]:
        row = rows[cid]
        old = row["critical_dependency_status"]
        row["critical_dependency_status"] = "checked-none"
        row["critical_dependency_reason"] = "The cited object-file literature informs mechanism only; the conservative feature-change-cost Y is defined by the supplied experiment and does not borrow that premise for A/E/F or outcome coding."
        log("comparison", cid, "dependency-status-correction", "critical_dependency_status", old, "checked-none",
            row["critical_dependency_reason"], row["source_pages"] or "Supplied PDF")
        write("experiments_master.csv", row, "comparison_id")

    # Same-experiment E-diagnostic analyses need explicit complete bundles.
    for cid in ["P000001_E01_C01", "P000001_E02_C01", "P000001_E03_C01", "P000001_E04_C01", "P000001_E07_C01", "P000004_E01_C01"]:
        row = rows[cid]
        claim = row["E_violating_pattern"]
        add_bundle(row, "E-diagnostic", "complete", "same-experiment-analysis", "E-diagnostic-support",
                   "supports", claim, row["source_pages"] or "Supplied PDF",
                   supporting_paper_id=row["paper_id"], supporting_experiment_id=row["experiment_id"],
                   transfer_reason="The linked analysis is in the focal experiment and addresses the same X/task relation and conservative Y.",
                   limitation="The main article omits some supplement-only procedural detail, which is recorded separately and does not alter the observed sign/interaction used for E-diagnostic.")

    # Every unresolved Tsushima dependency receives an explicit incomplete bundle.
    for cid in ["P000006_E01_C01", "P000006_E02_C01", "P000006_E03_C01", "P000006_E04_C01", "P000006_E05_C01"]:
        row = rows[cid]
        add_bundle(row, "awareness-A", "incomplete", "supplementary-analysis", "awareness-validation",
                   "unavailable", "The direct motion-discrimination validation is sensitive and transferable to this focal experiment.",
                   "Tsushima supporting material (not supplied)", supporting_paper_id=row["paper_id"],
                   supporting_experiment_id=row["experiment_id"],
                   transfer_reason="The main article states that the supplement contains the experiment-specific methods and awareness validation.",
                   limitation="Trial counts, sensitivity, participant/regime matching, and experiment-specific transfer cannot be audited without the supplied supplement.")

    # Resolve append-only experiment decision references without treating the controls as qualifying comparisons.
    excluded_support_row("P000001", "P000001_E05", "Experiment 5: sparse visible-trial awareness control (support-only)", "Ben-Haim p. 7, Fig. 4A")
    excluded_support_row("P000004", "P000004_E03", "Experiment 3: visible-only SOA control (support-only)", "Lin & Murray p. 7")

    log("run", RUN_ID, "validation-repair-checkpoint", "validation_repairs", None,
        {"null_audits": 4, "dependency_corrections": 3, "E_bundles": 6, "incomplete_dependency_bundles": 5, "support_only_exclusions": 2},
        "All first-pass validator findings were addressed with append-first, schema-aware writes; no scientific category was strengthened to make validation pass.",
        "runs/PREFREEZE_DIAG_20260819/")


if __name__ == "__main__":
    main()
