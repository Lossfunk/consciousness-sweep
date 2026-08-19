from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUN_ID = "PREFREEZE_DIAG_004"
RUN_DIR = ROOT / "runs" / RUN_ID
sys.path.insert(0, str(ROOT / "tools"))

from structured_write import _atomic_write_json, allocate_identifier, append_jsonl_record, load_schema, validate_record

timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
reason = (
    "The bounded source-only scientific diagnostic and deterministic derivation are complete. "
    "Final validation is paused on the package's two support-only experiment-reference errors; "
    "no search frontier was entered because additional retrieval was prohibited."
)
event = {
    "decision_id": allocate_identifier(RUN_DIR, "decision"),
    "run_id": RUN_ID,
    "timestamp": timestamp,
    "entity_type": "run",
    "entity_id": RUN_ID,
    "decision_type": "status-transition",
    "field": "status",
    "old_value": "running",
    "new_value": "paused",
    "reason": reason,
    "source_location": "runs/PREFREEZE_DIAG_004/run_summary.md",
    "agent": "Codex/GPT-5",
}
append_jsonl_record(
    RUN_DIR / "decision_log.jsonl",
    load_schema(ROOT, "decision_log.schema.json"),
    event,
)
state_path = RUN_DIR / "run_state.json"
state = json.loads(state_path.read_text(encoding="utf-8"))
state.update({
    "status": "paused",
    "status_reason": reason,
    "current_wave": 1,
    "workflow_phase": "final-validation",
    "last_checkpoint_at": timestamp,
})
validate_record(state, load_schema(ROOT, "run_state.schema.json"))
_atomic_write_json(state_path, state)
print("PASS: diagnostic checkpoint recorded")
