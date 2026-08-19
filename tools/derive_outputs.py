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


def awareness_design_eligible(row: dict[str, str]) -> bool:
    return (
        row["A_code"] in {"A-direct", "A-validated"}
        and row["E_code"] in {"E-matched", "E-diagnostic"}
        and row["F_code"] == "F-meaningful"
    )


def meyen_passes(row: dict[str, str]) -> bool:
    return row["Meyen_role"] != "inference-critical" or row["Meyen_status"] == "Meyen-satisfied"


def audited_functional_y(row: dict[str, str]) -> bool:
    return row.get("Y_functional_status") in {
        "downstream-function", "coherent-functional-mapping",
    }


def focal_difference_provenance(row: dict[str, str]) -> bool:
    return (
        row.get("difference_source_experiment_id") == row.get("experiment_id")
        and bool(row.get("difference_source_location", "").strip())
        and bool(row.get("difference_statistic_or_test", "").strip())
    )


def constraint_awareness_difference(row: dict[str, str]) -> bool:
    return (
        awareness_design_eligible(row)
        and row["awareness_effect"] == "difference-supported"
        and row["awareness_effect_stats_status"] == "adequate"
        and row["difference_tested"] == "yes"
        and focal_difference_provenance(row)
        and meyen_passes(row)
    )


def constraint_unaware_capacity(row: dict[str, str]) -> bool:
    return (
        row["A_code"] in {"A-direct", "A-validated"}
        and row["F_code"] == "F-meaningful"
        and audited_functional_y(row)
        and bool(row.get("unaware_capacity_claim", "").strip())
        and row.get("unaware_capacity_claim") == row.get("Y_label")
        and row.get("unaware_capacity_evidence_scope") == "whole-focal-Y"
        and row["unaware_capacity"] == "supported"
        and row["unaware_capacity_stats_status"] == "adequate"
        and meyen_passes(row)
    )


def constraint_equivalence_supported(row: dict[str, str]) -> bool:
    return (
        awareness_design_eligible(row)
        and audited_functional_y(row)
        and bool(row.get("unaware_capacity_claim", "").strip())
        and row.get("unaware_capacity_claim") == row.get("Y_label")
        and row.get("unaware_capacity_evidence_scope") == "whole-focal-Y"
        and row["unaware_capacity"] == "supported"
        and row["unaware_capacity_stats_status"] == "adequate"
        and row["awareness_effect"] == "equivalence-supported"
        and row["awareness_effect_stats_status"] == "adequate"
        and row["difference_tested"] == "yes"
        and focal_difference_provenance(row)
        and row["null_evidence_adequacy"] == "adequate"
        and meyen_passes(row)
    )


def no_detectable_awareness_difference(row: dict[str, str]) -> bool:
    return (
        row.get("current_status") == "fully-evaluated"
        and row["awareness_effect"] == "no-detectable-difference"
    )


def unresolved_comparison(row: dict[str, str]) -> bool:
    return row.get("current_status") == "fully-evaluated" and (
        row["unaware_capacity"] == "unclear" or row["awareness_effect"] == "unresolved"
    )


# Compatibility alias for callers that used the old name for the E-dependent route.
design_eligible = awareness_design_eligible


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

    design = [row for row in rows if awareness_design_eligible(row)]
    awareness = [row for row in rows if constraint_awareness_difference(row)]
    capacity = [row for row in rows if constraint_unaware_capacity(row)]
    no_detectable = [row for row in rows if no_detectable_awareness_difference(row)]
    equivalence = [row for row in rows if constraint_equivalence_supported(row)]
    unresolved = [row for row in rows if unresolved_comparison(row)]
    constraint = [
        row for row in rows
        if constraint_awareness_difference(row)
        or constraint_unaware_capacity(row)
        or constraint_equivalence_supported(row)
    ]
    outputs = {
        "design_eligible_experiments.csv": design,
        "constraint_ready_experiments.csv": constraint,
        "awareness_linked_differences.csv": awareness,
        "unaware_capacities.csv": capacity,
        "no_detectable_awareness_differences.csv": no_detectable,
        "equivalence_supported_no_difference.csv": equivalence,
        "unresolved_comparisons.csv": unresolved,
    }
    for filename, selected in outputs.items():
        write_rows(run_dir / filename, headers, selected)
    print(
        "PASS: comparison-level derived outputs regenerated "
        f"(design={len(design)}, constraint={len(constraint)}, awareness={len(awareness)}, "
        f"capacity={len(capacity)}, no-detectable={len(no_detectable)}, "
        f"equivalence={len(equivalence)}, unresolved={len(unresolved)})."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
