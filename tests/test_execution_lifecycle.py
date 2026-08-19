from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PYTHON = ROOT / ".venv" / "bin" / "python"
sys.path.insert(0, str(ROOT / "tools"))

from execution_contract import (  # noqa: E402
    ordered_result_set_sha256,
    reopen_for_blind_discovery,
    search_window_key,
)
from structured_write import allocate_identifier  # noqa: E402


class ContractStateTests(unittest.TestCase):
    def test_route_reopening_is_specific_and_idempotent(self) -> None:
        state = {
            "workflow_phase": "blind-lane",
            "citation_frontier_status": "provisionally-satisfied",
            "process_frontier_status": "provisionally-satisfied",
            "activated_normalized_y_labels": [],
        }
        updated = reopen_for_blind_discovery(state, citation_node=True, genuinely_new_y="synthetic-y")
        self.assertEqual(updated["workflow_phase"], "reopened-frontiers")
        self.assertEqual(updated["citation_frontier_status"], "reopened")
        self.assertEqual(updated["process_frontier_status"], "reopened")
        repeated = reopen_for_blind_discovery(updated, genuinely_new_y="synthetic-y")
        self.assertEqual(repeated["activated_normalized_y_labels"], ["synthetic-y"])

    def test_immutable_search_snapshot_hashes_ordered_results(self) -> None:
        key = search_window_key(
            execution_phase="blind-lane",
            source="SyntheticSource",
            query_id="SYN",
            normalized_y_label=None,
            canonical_query="synthetic query",
            source_parameters={"sort": "synthetic"},
            publication_cutoff=None,
            requested_max_n=2,
        )
        self.assertEqual(len(key), 64)
        results = [
            {"result_rank": 1, "source_stable_id": "a", "raw_doi": None, "raw_title": "A", "raw_url": None},
            {"result_rank": 2, "source_stable_id": "b", "raw_doi": None, "raw_title": "B", "raw_url": None},
        ]
        digest = ordered_result_set_sha256(results)
        self.assertEqual(len(digest), 64)
        self.assertNotEqual(digest, hashlib.sha256(b"").hexdigest())


class SyntheticLifecycleTests(unittest.TestCase):
    def run_command(self, *args: str, expected: int = 0) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False)
        if result.returncode != expected:
            self.fail(
                f"command returned {result.returncode}, expected {expected}: {' '.join(args)}\n"
                f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
            )
        return result

    def test_clean_lifecycle_derive_validate_resume_and_id_retirement(self) -> None:
        with tempfile.TemporaryDirectory(prefix="sweep-lifecycle-") as temporary:
            runs_root = Path(temporary) / "runs"
            run_id = "SYNTHETIC_LIFECYCLE"
            self.run_command(
                str(PYTHON), "tools/init_run.py", "--run-id", run_id,
                "--run-mode", "start", "--agent-harness", "unittest",
                "--allow-pre-freeze", "--runs-root", str(runs_root),
            )
            run_dir = runs_root / run_id
            retired = allocate_identifier(run_dir, "paper")
            next_identifier = allocate_identifier(run_dir, "paper")
            self.assertEqual(retired, "P000001")
            self.assertEqual(next_identifier, "P000002")
            state = json.loads((run_dir / "run_state.json").read_text())
            self.assertEqual(state["next_paper_counter"], 3)

            self.run_command(
                str(PYTHON), "tools/derive_outputs.py", "--run-id", run_id,
                "--runs-root", str(runs_root),
            )
            self.run_command(
                str(PYTHON), "tools/validate_run.py", "--run-id", run_id,
                "--runs-root", str(runs_root),
            )
            self.run_command(
                str(PYTHON), "tools/init_run.py", "--run-id", run_id,
                "--run-mode", "resume", "--agent-harness", "unittest",
                "--allow-pre-freeze", "--runs-root", str(runs_root),
            )

    def test_historical_package_mismatch_is_refused_before_current_schema(self) -> None:
        with tempfile.TemporaryDirectory(prefix="sweep-compat-") as temporary:
            runs_root = Path(temporary) / "runs"
            run_id = "HISTORICAL_SYNTHETIC"
            self.run_command(
                str(PYTHON), "tools/init_run.py", "--run-id", run_id,
                "--run-mode", "start", "--agent-harness", "unittest",
                "--allow-pre-freeze", "--runs-root", str(runs_root),
            )
            state_path = runs_root / run_id / "run_state.json"
            state = json.loads(state_path.read_text())
            state["protocol_version"] = "draft-0.8.1"
            state["package_version"] = "prefreeze-package-0.8.1"
            state["schema_version"] = "prefreeze-schema-0.8"
            state_path.write_text(json.dumps(state, indent=2) + "\n")
            result = self.run_command(
                str(PYTHON), "tools/validate_run.py", "--run-id", run_id,
                "--runs-root", str(runs_root), expected=3,
            )
            self.assertIn("incompatible run package/schema", result.stderr)


if __name__ == "__main__":
    unittest.main()
