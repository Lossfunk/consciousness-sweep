from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUN_ID = "PREFREEZE_DIAG_004"
RUN_DIR = ROOT / "runs" / RUN_ID
sys.path.insert(0, str(ROOT / "tools"))

from structured_write import allocate_identifier, append_jsonl_record, load_csv_rows, load_schema, write_csv_record

decision_schema = load_schema(ROOT, "decision_log.schema.json")
experiment_schema = load_schema(ROOT, "experiments.schema.json")
errors: list[str] = []
rows = load_csv_rows(RUN_DIR / "experiments_master.csv", experiment_schema, errors)
if errors:
    raise RuntimeError(errors)
row = next(item for item in rows if item["comparison_id"] == "P000001_E06_C01")
reason = (
    "No borrowed premise is used to establish a scientific conclusion. Same-experiment results "
    "are sufficient for A-direct and unaware capacity, while the awareness-effect route remains "
    "unresolved because instruction is an explicit task-state confound."
)
event = {
    "decision_id": allocate_identifier(RUN_DIR, "decision"),
    "run_id": RUN_ID,
    "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    "entity_type": "comparison",
    "entity_id": row["comparison_id"],
    "decision_type": "critical-dependency-revision",
    "field": "critical_dependency_status",
    "old_value": row["critical_dependency_status"],
    "new_value": "checked-none",
    "reason": reason,
    "source_location": row["source_pages"],
    "agent": "Codex/GPT-5",
}
append_jsonl_record(RUN_DIR / "decision_log.jsonl", decision_schema, event)
row["critical_dependency_status"] = "checked-none"
row["critical_dependency_reason"] = reason
write_csv_record(RUN_DIR / "experiments_master.csv", experiment_schema, row, key_field="comparison_id")
print("PASS: final scientific correction applied")
