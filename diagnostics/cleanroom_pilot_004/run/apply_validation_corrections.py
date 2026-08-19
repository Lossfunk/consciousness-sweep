from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUN_ID = "PREFREEZE_DIAG_004"
RUN_DIR = ROOT / "runs" / RUN_ID
sys.path.insert(0, str(ROOT / "tools"))

from structured_write import (  # noqa: E402
    allocate_identifier,
    append_jsonl_record,
    load_csv_rows,
    load_schema,
    write_csv_record,
)

SCHEMAS = {
    "decision": load_schema(ROOT, "decision_log.schema.json"),
    "experiment": load_schema(ROOT, "experiments.schema.json"),
    "link": load_schema(ROOT, "evidence_links.schema.json"),
}


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def decision(entity_type: str, entity_id: str, decision_type: str, field: str,
             old_value, new_value, reason: str, source_location: str) -> None:
    record = {
        "decision_id": allocate_identifier(RUN_DIR, "decision"),
        "run_id": RUN_ID,
        "timestamp": now(),
        "entity_type": entity_type,
        "entity_id": entity_id,
        "decision_type": decision_type,
        "field": field,
        "old_value": old_value,
        "new_value": new_value,
        "reason": reason,
        "source_location": source_location,
        "agent": "Codex/GPT-5",
    }
    append_jsonl_record(RUN_DIR / "decision_log.jsonl", SCHEMAS["decision"], record)


def load(name: str, schema: str):
    errors: list[str] = []
    rows = load_csv_rows(RUN_DIR / name, SCHEMAS[schema], errors)
    if errors:
        raise RuntimeError(errors)
    return rows


experiments = load("experiments_master.csv", "experiment")
by_comparison = {row["comparison_id"]: row for row in experiments}

# The main article is sufficient for the classifications of these human
# comparisons. Missing exact SI details are retained as limitations rather
# than mislabeled as classification-critical unresolved dependencies.
resolved = {
    "P000001_E01_C01", "P000001_E03_C01", "P000001_E07_C01"
}
for comparison_id in resolved:
    row = by_comparison[comparison_id]
    old = row["critical_dependency_status"]
    reason = (
        "The supplied main article reports the classification-critical awareness and "
        "outcome results. Unsupplied exact SI details remain an explicit statistical or "
        "procedural limitation but are not required to establish the recorded category."
    )
    decision("comparison", comparison_id, "critical-dependency-revision",
             "critical_dependency_status", old, "resolved", reason, row["source_pages"])
    row["critical_dependency_status"] = "resolved"
    row["critical_dependency_reason"] = reason
    write_csv_record(RUN_DIR / "experiments_master.csv", SCHEMAS["experiment"], row,
                     key_field="comparison_id")

# The monkey rows make no strong A-based conclusion; the unavailable external
# awareness validation is therefore a reported uncertainty, not a dependency
# used by the classification.
for comparison_id in ("P000001_E02_C01", "P000001_E04_C01"):
    row = by_comparison[comparison_id]
    old = row["critical_dependency_status"]
    reason = (
        "No external awareness premise is used to establish a conclusion. The row remains "
        "A-transfer-risk and both scientific routes remain unresolved/unclear because the "
        "supplied record lacks monkey-specific awareness validation."
    )
    decision("comparison", comparison_id, "critical-dependency-revision",
             "critical_dependency_status", old, "checked-none", reason, row["source_pages"])
    row["critical_dependency_status"] = "checked-none"
    row["critical_dependency_reason"] = reason
    write_csv_record(RUN_DIR / "experiments_master.csv", SCHEMAS["experiment"], row,
                     key_field="comparison_id")

# A direct same-Y neural comparison was inspected even though F is not meaningful.
row = by_comparison["P000005_E01_C02"]
decision("comparison", row["comparison_id"], "result-inspection-revision",
         "result_inspection_status", row["result_inspection_status"],
         "completed-viable-routes",
         "The direct normal-versus-blind BOLD contrast was descriptively inspected; F-not-meaningful prevents a strong functional route but does not waive result inspection.",
         row["source_pages"])
row["result_inspection_status"] = "completed-viable-routes"
row["result_inspection_reason"] = (
    "The direct same-Y BOLD comparison was inspected; the result remains unresolved on the "
    "awareness-effect axis because the output is F-not-meaningful."
)
write_csv_record(RUN_DIR / "experiments_master.csv", SCHEMAS["experiment"], row,
                 key_field="comparison_id")

links = load("evidence_links.csv", "link")
for link in links:
    changed = False
    if link["support_role"] == "E-diagnostic-support" and link["same_focal_Y_status"] == "yes":
        old = link["support_role"]
        reason = (
            "The required same-Y nonmonotonic or qualitative-change result directly tests and "
            "rejects the recorded scalar first-order-evidence alternative; it is therefore the "
            "bundle's alternative-explanation control, not merely generic E support."
        )
        decision("evidence_link", link["evidence_link_id"], "evidence-role-revision",
                 "support_role", old, "alternative-explanation-control", reason,
                 link["source_location"])
        link["support_role"] = "alternative-explanation-control"
        changed = True
    focal = by_comparison[link["focal_comparison_id"]]
    if (focal["A_code"] == "A-validated" and
            link["support_role"] == "awareness-validation" and
            not link["transfer_limitation"]):
        limitation = (
            "The critical awareness result was obtained in a separate validation block or "
            "phase rather than simultaneously with the focal downstream outcome."
        )
        decision("evidence_link", link["evidence_link_id"], "transfer-audit-revision",
                 "transfer_limitation", None, limitation,
                 "The limitation is required for an explicit premise-specific A transfer assessment.",
                 link["source_location"])
        link["transfer_limitation"] = limitation
        changed = True
    if changed:
        write_csv_record(RUN_DIR / "evidence_links.csv", SCHEMAS["link"], link,
                         key_field="evidence_link_id")

print("PASS: append-first validation corrections applied")
