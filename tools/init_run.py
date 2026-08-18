#!/usr/bin/env python3
"""Initialize a new run or safely resume an existing run."""

from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator, FormatChecker

from validate_run import immutable_hashes


ROOT = Path(__file__).resolve().parents[1]
RUN_ID_RE = re.compile(r"^[A-Za-z0-9._-]+$")
CSV_TO_SCHEMA = {
    "papers_master.csv": "papers.schema.json",
    "experiments_master.csv": "experiments.schema.json",
    "search_log.csv": "search_log.schema.json",
    "discoveries.csv": "discoveries.schema.json",
    "missing_texts.csv": "missing_texts.schema.json",
    "design_eligible_experiments.csv": "experiments.schema.json",
    "constraint_ready_experiments.csv": "experiments.schema.json",
    "awareness_linked_differences.csv": "experiments.schema.json",
    "preserved_capacities.csv": "experiments.schema.json",
    "inconclusive_experiments.csv": "experiments.schema.json",
}


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def write_json(path: Path, value: Any) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def append_event(path: Path, event: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n")
        handle.flush()


def repository_commit(root: Path) -> str | None:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=root, text=True, capture_output=True, check=False
    )
    return result.stdout.strip() or None if result.returncode == 0 else None


def schema_headers(root: Path, schema_name: str) -> list[str]:
    schema = json.loads((root / "schemas" / schema_name).read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return list(schema["properties"].keys())


def read_ids(path: Path, field: str) -> list[str]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return [row[field] for row in csv.DictReader(handle) if row.get(field)]


def suffix_max(values: list[str], marker: str, width: int = 6) -> int:
    pattern = re.compile(re.escape(marker) + rf"([0-9]{{{width}}})$")
    matches = [int(match.group(1)) for value in values if (match := pattern.search(value))]
    return max(matches, default=0)


def run_preflight(root: Path, allow_pre_freeze: bool) -> None:
    mode = "pre-freeze" if allow_pre_freeze else "registered"
    result = subprocess.run([sys.executable, str(root / "tools" / "preflight.py"), "--mode", mode, "--root", str(root)])
    if result.returncode:
        raise SystemExit(result.returncode)


def start(args: argparse.Namespace, root: Path, run_dir: Path, config: dict[str, Any]) -> None:
    if run_dir.exists():
        raise SystemExit(f"refusing overwrite: {run_dir} already exists")
    run_dir.mkdir(parents=True)
    (run_dir / "manual_fulltexts").mkdir()
    for filename, schema_name in CSV_TO_SCHEMA.items():
        with (run_dir / filename).open("x", newline="", encoding="utf-8") as handle:
            csv.writer(handle, lineterminator="\n").writerow(schema_headers(root, schema_name))
    (run_dir / "decision_log.jsonl").touch(exist_ok=False)
    (run_dir / "run_summary.md").write_text(
        f"# Run {args.run_id}\n\nInitialized in `{args.run_mode}` mode; scientific execution not yet summarized.\n",
        encoding="utf-8",
    )
    timestamp = now()
    state = {
        "run_id": args.run_id,
        "run_mode": "start",
        "status": "running",
        "status_reason": "Run infrastructure initialized after successful preflight.",
        "protocol_version": config["protocol_version"],
        "registration_status": config["registration_status"],
        "repository_commit": repository_commit(root),
        "immutable_inputs_sha256": immutable_hashes(root),
        "current_wave": 0,
        "next_paper_counter": 1,
        "next_experiment_counters": {},
        "next_comparison_counters": {},
        "next_decision_counter": 2,
        "next_search_counter": 1,
        "next_discovery_counter": 1,
        "started_at": timestamp,
        "last_checkpoint_at": timestamp,
        "model": args.model,
        "model_version": args.model_version,
        "agent_harness": args.agent_harness,
    }
    event = {
        "decision_id": f"{args.run_id}_D000001",
        "run_id": args.run_id,
        "timestamp": timestamp,
        "entity_type": "run",
        "entity_id": args.run_id,
        "decision_type": "run-start",
        "field": "status",
        "old_value": None,
        "new_value": "running",
        "reason": state["status_reason"],
        "source_location": "run_state.json",
        "agent": args.agent_harness,
    }
    append_event(run_dir / "decision_log.jsonl", event)
    write_json(run_dir / "run_state.json", state)
    validator = Draft202012Validator(
        json.loads((root / "schemas" / "run_state.schema.json").read_text(encoding="utf-8")),
        format_checker=FormatChecker(),
    )
    validator.validate(state)
    print(f"PASS: initialized {run_dir} without overwrite.")


def resume(args: argparse.Namespace, root: Path, runs_root: Path, run_dir: Path, config: dict[str, Any]) -> None:
    if not run_dir.is_dir():
        raise SystemExit(f"cannot resume missing run: {run_dir}")
    validation = subprocess.run([
        sys.executable, str(root / "tools" / "validate_run.py"), "--run-id", args.run_id,
        "--root", str(root), "--runs-root", str(runs_root), "--allow-stale-counters",
    ])
    if validation.returncode:
        raise SystemExit(validation.returncode)
    state_path = run_dir / "run_state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    if state["protocol_version"] != config["protocol_version"] or state["registration_status"] != config["registration_status"]:
        raise SystemExit("refusing resume: frozen version/status differs")
    if state["immutable_inputs_sha256"] != immutable_hashes(root):
        raise SystemExit("refusing resume: immutable inputs changed")
    old_status = state["status"]
    if old_status == "complete" and not args.reopen_reason:
        raise SystemExit("completed run requires --reopen-reason")

    paper_ids = read_ids(run_dir / "papers_master.csv", "paper_id")
    experiment_ids = sorted(set(read_ids(run_dir / "experiments_master.csv", "experiment_id")))
    comparison_ids = read_ids(run_dir / "experiments_master.csv", "comparison_id")
    search_ids = read_ids(run_dir / "search_log.csv", "search_id")
    discovery_ids = read_ids(run_dir / "discoveries.csv", "discovery_id")
    decision_ids = []
    for line in (run_dir / "decision_log.jsonl").read_text(encoding="utf-8").splitlines():
        if line.strip():
            decision_ids.append(json.loads(line)["decision_id"])
    next_decision = suffix_max(decision_ids, "_D") + 1
    experiment_counters = {
        paper_id: max(
            [int(value.split("_E")[1]) for value in experiment_ids if value.startswith(f"{paper_id}_E")],
            default=0,
        ) + 1
        for paper_id in paper_ids
    }
    comparison_counters = {
        experiment_id: max(
            [int(value.rsplit("_C", 1)[1]) for value in comparison_ids if value.startswith(f"{experiment_id}_C")],
            default=0,
        ) + 1
        for experiment_id in experiment_ids
    }
    timestamp = now()
    reason = args.reopen_reason or "Resumed an existing validated run without resetting prior state."
    event = {
        "decision_id": f"{args.run_id}_D{next_decision:06d}",
        "run_id": args.run_id,
        "timestamp": timestamp,
        "entity_type": "run",
        "entity_id": args.run_id,
        "decision_type": "run-reopen" if old_status == "complete" else "run-resume",
        "field": "status",
        "old_value": old_status,
        "new_value": "running",
        "reason": reason,
        "source_location": "run_state.json",
        "agent": args.agent_harness,
    }
    append_event(run_dir / "decision_log.jsonl", event)
    state.update({
        "run_mode": "resume",
        "status": "running",
        "status_reason": reason,
        "next_paper_counter": max([int(value[1:]) for value in paper_ids], default=0) + 1,
        "next_experiment_counters": experiment_counters,
        "next_comparison_counters": comparison_counters,
        "next_decision_counter": next_decision + 1,
        "next_search_counter": suffix_max(search_ids, "_S") + 1,
        "next_discovery_counter": suffix_max(discovery_ids, "_R") + 1,
        "last_checkpoint_at": timestamp,
        "model": args.model if args.model is not None else state.get("model"),
        "model_version": args.model_version if args.model_version is not None else state.get("model_version"),
        "agent_harness": args.agent_harness,
    })
    write_json(state_path, state)
    final_validation = subprocess.run([
        sys.executable, str(root / "tools" / "validate_run.py"), "--run-id", args.run_id,
        "--root", str(root), "--runs-root", str(runs_root),
    ])
    if final_validation.returncode:
        raise SystemExit(final_validation.returncode)
    print(f"PASS: resumed {run_dir}; prior files/history were not reset.")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--run-mode", choices=("start", "resume"), required=True)
    parser.add_argument("--agent-harness", required=True)
    parser.add_argument("--model")
    parser.add_argument("--model-version")
    parser.add_argument("--reopen-reason")
    parser.add_argument("--allow-pre-freeze", action="store_true", help="Synthetic/calibration use only")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--runs-root", type=Path)
    args = parser.parse_args()
    if not RUN_ID_RE.fullmatch(args.run_id):
        raise SystemExit("RUN_ID must match ^[A-Za-z0-9._-]+$")
    root = args.root.resolve()
    config = yaml.safe_load((root / "config.yaml").read_text(encoding="utf-8"))
    runs_root = args.runs_root.resolve() if args.runs_root else (root / config["paths"]["runs"])
    run_dir = runs_root / args.run_id
    run_preflight(root, args.allow_pre_freeze)
    if args.run_mode == "start":
        start(args, root, run_dir, config)
    else:
        resume(args, root, runs_root, run_dir, config)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
