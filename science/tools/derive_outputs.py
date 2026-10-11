#!/usr/bin/env python3
"""Mechanically derive comparison-level views from experiments_master.csv."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

from derived_views import (
    awareness_design_eligible, constraint_awareness_difference,
    constraint_equivalence_supported, constraint_unaware_capacity, derive_views,
    design_eligible, no_detectable_awareness_difference, unresolved_comparison,
)
from structured_write import run_write_lock
from validate_run import main as validate_run


ROOT = Path(__file__).resolve().parents[1]


def write_rows(path: Path, headers: list[str], rows: list[dict[str, str]]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers, lineterminator="\n", extrasaction="raise")
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--runs-root", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    runs_root = args.runs_root.resolve() if args.runs_root else root / "runs"
    run_dir = runs_root / args.run_id
    if not run_dir.is_dir():
        print(f"ERROR: run directory does not exist: {run_dir}", file=sys.stderr)
        return 1
    # Validate and export one stable master snapshot under the writer's run lock.
    with run_write_lock(run_dir):
        result = validate_run(
            ["--run-id", args.run_id, "--root", str(root), "--runs-root", str(runs_root)],
            check_derived=False, report_success=False,
        )
        if result:
            return result
        schema = json.loads((root / "schemas" / "experiments.schema.json").read_text(encoding="utf-8"))
        headers = list(schema["properties"].keys())
        with (run_dir / "experiments_master.csv").open(newline="", encoding="utf-8-sig") as handle:
            rows = list(csv.DictReader(handle))
        outputs = derive_views(rows)
        for filename, selected in outputs.items():
            write_rows(run_dir / filename, headers, selected)
    print("PASS: validated master snapshot exported: " + ", ".join(
        f"{filename}={len(selected)}" for filename, selected in outputs.items()
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
