#!/usr/bin/env python3
"""Mechanically derive comparison-level views from experiments_master.csv."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

from validate_run import load_csv_rows


ROOT = Path(__file__).resolve().parents[1]


def design_eligible(row: dict[str, str]) -> bool:
    return (
        row["A_code"] in {"A-direct", "A-validated"}
        and row["E_code"] in {"E-matched", "E-diagnostic"}
        and row["F_code"] == "F-meaningful"
    )


def meyen_passes(row: dict[str, str]) -> bool:
    return row["Meyen_applicable"] != "yes" or row["Meyen_status"] == "Meyen-satisfied"


def constraint_awareness_difference(row: dict[str, str]) -> bool:
    return (
        design_eligible(row)
        and row["outcome"] == "awareness-linked-difference"
        and row["stats_status"] == "adequate"
        and row["difference_tested"] == "yes"
        and meyen_passes(row)
    )


def constraint_preserved_capacity(row: dict[str, str]) -> bool:
    return (
        design_eligible(row)
        and row["outcome"] == "preserved-capacity"
        and row["stats_status"] == "adequate"
        and row["unaware_Y_evidence"] == "positive"
        and row["difference_tested"] == "yes"
        and row["null_evidence_adequacy"] == "adequate"
        and meyen_passes(row)
    )


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
    schema = json.loads((root / "schemas" / "experiments.schema.json").read_text(encoding="utf-8"))
    headers = list(schema["properties"].keys())
    errors: list[str] = []
    load_csv_rows(run_dir / "experiments_master.csv", schema, errors)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    with (run_dir / "experiments_master.csv").open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != headers:
            print("ERROR: experiments_master.csv header differs from schema", file=sys.stderr)
            return 1
        rows = sorted(reader, key=lambda row: (row["paper_id"], row["experiment_id"], row["comparison_id"]))

    design = [row for row in rows if design_eligible(row)]
    awareness = [row for row in design if constraint_awareness_difference(row)]
    preserved = [row for row in design if constraint_preserved_capacity(row)]
    constraint = [row for row in design if constraint_awareness_difference(row) or constraint_preserved_capacity(row)]
    inconclusive = [row for row in design if row["outcome"] == "inconclusive"]
    outputs = {
        "design_eligible_experiments.csv": design,
        "constraint_ready_experiments.csv": constraint,
        "awareness_linked_differences.csv": awareness,
        "preserved_capacities.csv": preserved,
        "inconclusive_experiments.csv": inconclusive,
    }
    for filename, selected in outputs.items():
        write_rows(run_dir / filename, headers, selected)
    print(
        "PASS: comparison-level derived outputs regenerated "
        f"(design={len(design)}, constraint={len(constraint)}, awareness={len(awareness)}, "
        f"preserved={len(preserved)}, inconclusive={len(inconclusive)})."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
