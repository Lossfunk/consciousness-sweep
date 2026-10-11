#!/usr/bin/env python3
"""Validate structural authority coverage for the derived documentation layer.

This check establishes METHODS/crosswalk coverage and lightweight brief structure.
It cannot establish semantic equivalence with the normative sources or prose quality.
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

try:
    import yaml
except ModuleNotFoundError as exc:
    print(
        f"ERROR: missing repository dependency {exc.name!r}. "
        "Run: python3 tools/bootstrap_env.py --venv .venv",
        file=sys.stderr,
    )
    raise SystemExit(3) from None


ROOT = Path(__file__).resolve().parents[1]
AUTHORITY_FILES = ("PROTOCOL.md", "AGENTS.md")
BRIEF_REQUIRED_HEADINGS = {
    "The scientific question",
    "Core concepts",
    "Scientific algorithm",
    "Four discovery routes",
    "From full text to a comparison",
    "Outcomes and outputs",
    "Independent runs and current status",
}
REQUIRED_FIELDS = {
    "authority_file", "authority_section", "authority_heading", "rule_category",
    "methods_section", "methods_heading", "coverage_status", "notes",
}
ALLOWED_STATUSES = {"covered", "intentionally-implementation-only", "unresolved"}
HEADING_RE = re.compile(r"^(#{2,3})\s+(.+?)\s*$")
METHODS_ANCHOR_RE = re.compile(r'^<a id="([a-z0-9-]+)"></a>$')


def markdown_headings(path: Path) -> list[tuple[int, str]]:
    """Return level-2/3 headings, stripping a leading numeric section label."""
    headings: list[tuple[int, str]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        match = HEADING_RE.match(line)
        if match:
            level = len(match.group(1))
            heading = re.sub(r"^\d+(?:\.\d+)*\.?(?:\s+|$)", "", match.group(2)).strip()
            headings.append((level, heading))
    return headings


def methods_sections(path: Path) -> tuple[dict[str, str], list[str]]:
    sections: dict[str, str] = {}
    errors: list[str] = []
    pending_anchor: str | None = None
    seen_anchors: list[str] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        anchor = METHODS_ANCHOR_RE.match(line)
        if anchor:
            pending_anchor = anchor.group(1)
            seen_anchors.append(pending_anchor)
            continue
        if line.startswith("## "):
            if pending_anchor is None:
                errors.append(f"METHODS.md:{line_number}: major heading lacks a preceding explicit anchor")
            else:
                sections[pending_anchor] = line[3:].strip()
            pending_anchor = None
    for anchor, count in Counter(seen_anchors).items():
        if count > 1:
            errors.append(f"METHODS.md: duplicate anchor {anchor}")
    return sections, errors


def load_crosswalk(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    errors: list[str] = []
    try:
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        return [], [f"{path}: {exc}"]
    if not isinstance(document, dict) or not isinstance(document.get("mappings"), list):
        return [], [f"{path}: top-level mappings must be a list"]
    rows = document["mappings"]
    for index, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            errors.append(f"crosswalk row {index}: must be an object")
            continue
        missing = REQUIRED_FIELDS - set(row)
        extra = set(row) - REQUIRED_FIELDS
        if missing:
            errors.append(f"crosswalk row {index}: missing fields {sorted(missing)}")
        if extra:
            errors.append(f"crosswalk row {index}: unexpected fields {sorted(extra)}")
        if row.get("coverage_status") not in ALLOWED_STATUSES:
            errors.append(f"crosswalk row {index}: invalid coverage_status {row.get('coverage_status')!r}")
        for field in REQUIRED_FIELDS - {"notes"}:
            if not isinstance(row.get(field), str) or not row[field].strip():
                errors.append(f"crosswalk row {index}: {field} must be nonempty text")
    return rows, errors


def _known_numeric_sections(path: Path) -> set[str]:
    known: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        match = re.match(r"^#{2,3}\s+(\d+(?:\.\d+)*)\.?\s+", line)
        if match:
            known.add(match.group(1))
    return known


def validate(root: Path) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    methods_path = root / "METHODS.md"
    crosswalk_path = root / "docs" / "methods_crosswalk.yaml"
    rows, row_errors = load_crosswalk(crosswalk_path)
    errors.extend(row_errors)
    sections, section_errors = methods_sections(methods_path)
    errors.extend(section_errors)

    brief_path = root / "PROTOCOL_BRIEF.md"
    brief_headings: set[str] = set()
    brief_mapped: set[str] = set()
    if not brief_path.is_file():
        errors.append("PROTOCOL_BRIEF.md: required derived overview is missing")
    else:
        brief_text = brief_path.read_text(encoding="utf-8")
        brief_headings = {heading for level, heading in markdown_headings(brief_path) if level == 2}
        for heading in sorted(BRIEF_REQUIRED_HEADINGS - brief_headings):
            errors.append(f"PROTOCOL_BRIEF.md: missing required heading {heading!r}")
        opening = brief_text[:1200].lower()
        if not all(name in opening for name in ("protocol.md", "agents.md", "normative")):
            errors.append("PROTOCOL_BRIEF.md: opening must identify PROTOCOL.md and AGENTS.md as normative")
        if not any(status in brief_text.lower() for status in ("pre-freeze", "frozen")):
            errors.append("PROTOCOL_BRIEF.md: package status is not explicit")
        if "does awareness of x change whether, or how well, y can use x?" not in brief_text.lower():
            errors.append("PROTOCOL_BRIEF.md: core X-to-Y awareness question is missing")
        core_start = brief_text.find("## Core concepts")
        algorithm_start = brief_text.find("## Scientific algorithm")
        if core_start < 0 or algorithm_start <= core_start:
            errors.append("PROTOCOL_BRIEF.md: Core concepts must precede Scientific algorithm")
        else:
            core_block = brief_text[core_start:algorithm_start]
            for label in ("Awareness evidence", "Signal-strength control", "Functional interpretation"):
                if label not in core_block:
                    errors.append(f"PROTOCOL_BRIEF.md: {label} is not defined in Core concepts")

    try:
        crosswalk_document = yaml.safe_load(crosswalk_path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        crosswalk_document = {}
    brief_rows = crosswalk_document.get("brief_mappings") if isinstance(crosswalk_document, dict) else None
    if not isinstance(brief_rows, list):
        errors.append(f"{crosswalk_path}: top-level brief_mappings must be a list")
        brief_rows = []
    brief_keys: list[tuple[Any, ...]] = []
    for index, row in enumerate(brief_rows, start=1):
        required = {"brief_heading", "methods_section", "authority_refs"}
        if not isinstance(row, dict):
            errors.append(f"brief crosswalk row {index}: must be an object")
            continue
        missing = required - set(row)
        extra = set(row) - required
        if missing:
            errors.append(f"brief crosswalk row {index}: missing fields {sorted(missing)}")
        if extra:
            errors.append(f"brief crosswalk row {index}: unexpected fields {sorted(extra)}")
        heading = row.get("brief_heading")
        target = row.get("methods_section")
        refs = row.get("authority_refs")
        brief_keys.append((heading, target, refs))
        if heading not in brief_headings:
            errors.append(f"brief crosswalk row {index}: stale brief heading {heading!r}")
        else:
            brief_mapped.add(heading)
        if target not in sections:
            errors.append(f"brief crosswalk row {index}: orphaned METHODS target {target!r}")
        if not isinstance(refs, str) or not refs.strip() or not any(
            authority in refs for authority in ("PROTOCOL", "AGENTS")
        ):
            errors.append(f"brief crosswalk row {index}: authority_refs must name an authority")
    for key, count in Counter(brief_keys).items():
        if count > 1:
            errors.append(f"duplicate brief crosswalk row: {key}")
    for heading in sorted(brief_headings - brief_mapped):
        errors.append(f"unmapped PROTOCOL_BRIEF heading: {heading}")

    authority_headings = {
        filename: {heading for _level, heading in markdown_headings(root / filename)}
        for filename in AUTHORITY_FILES
    }
    mapped_headings: dict[str, set[str]] = {filename: set() for filename in AUTHORITY_FILES}
    row_keys: list[tuple[Any, ...]] = []
    target_counts: Counter[str] = Counter()
    for index, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            continue
        filename = row.get("authority_file")
        heading = row.get("authority_heading")
        target = row.get("methods_section")
        key = (
            filename, row.get("authority_section"), heading, target,
            row.get("coverage_status"), row.get("rule_category"),
        )
        row_keys.append(key)
        if filename not in AUTHORITY_FILES:
            errors.append(f"crosswalk row {index}: unknown authority_file {filename!r}")
        elif heading not in authority_headings[filename]:
            errors.append(f"crosswalk row {index}: stale authority heading {filename} / {heading!r}")
        else:
            mapped_headings[filename].add(heading)
        if target not in sections:
            errors.append(f"crosswalk row {index}: orphaned METHODS target {target!r}")
        elif row.get("methods_heading") != sections[target]:
            errors.append(
                f"crosswalk row {index}: stale METHODS heading for {target}: "
                f"{row.get('methods_heading')!r} != {sections[target]!r}"
            )
        if isinstance(target, str):
            target_counts[target] += 1
    for key, count in Counter(row_keys).items():
        if count > 1:
            errors.append(f"duplicate crosswalk row identity: {key}")

    for filename in AUTHORITY_FILES:
        missing = authority_headings[filename] - mapped_headings[filename]
        for heading in sorted(missing):
            errors.append(f"unmapped authority heading: {filename} / {heading}")
    for section in sections:
        if target_counts[section] == 0:
            errors.append(f"METHODS section has no reverse authority mapping: {section}")

    methods_text = methods_path.read_text(encoding="utf-8")
    authority_lines = [line for line in methods_text.splitlines() if line.startswith("**Authority:**")]
    if len(authority_lines) != len(sections):
        errors.append(
            f"METHODS.md: expected one Authority line per major section "
            f"({len(sections)}), found {len(authority_lines)}"
        )
    known_sections = {
        "PROTOCOL": _known_numeric_sections(root / "PROTOCOL.md"),
        "AGENTS": _known_numeric_sections(root / "AGENTS.md"),
    }
    for line in authority_lines:
        if "PROTOCOL" not in line and "AGENTS" not in line:
            errors.append(f"METHODS.md: authority line names no normative authority: {line}")
        for authority in ("PROTOCOL", "AGENTS"):
            for segment in re.findall(rf"{authority}\s+([^;]+)", line):
                for number in re.findall(r"§(\d+(?:\.\d+)*)|[–-](\d+(?:\.\d+)*)", segment):
                    section_number = next(value for value in number if value)
                    if section_number not in known_sections[authority]:
                        errors.append(
                            f"METHODS.md: unresolved authority reference {authority} §{section_number}"
                        )

    unresolved = sum(row.get("coverage_status") == "unresolved" for row in rows if isinstance(row, dict))
    implementation_only = sum(
        row.get("coverage_status") == "intentionally-implementation-only"
        for row in rows if isinstance(row, dict)
    )
    stats = {
        "protocol_mapped": len(mapped_headings["PROTOCOL.md"]),
        "protocol_total": len(authority_headings["PROTOCOL.md"]),
        "agents_mapped": len(mapped_headings["AGENTS.md"]),
        "agents_total": len(authority_headings["AGENTS.md"]),
        "methods_sections": len(sections),
        "crosswalk_rows": len(rows),
        "implementation_only": implementation_only,
        "unresolved": unresolved,
        "brief_mapped": len(brief_mapped),
        "brief_total": len(brief_headings),
    }
    return errors, stats


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument(
        "--require-no-unresolved", action="store_true",
        help="Freeze-time mode: fail when a crosswalk row remains unresolved.",
    )
    args = parser.parse_args()
    errors, stats = validate(args.root.resolve())
    if args.require_no_unresolved and stats["unresolved"]:
        errors.append(f"freeze-time crosswalk has {stats['unresolved']} unresolved entries")
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(
        "PASS: structural documentation coverage validates; "
        f"PROTOCOL {stats['protocol_mapped']}/{stats['protocol_total']}, "
        f"AGENTS {stats['agents_mapped']}/{stats['agents_total']}, "
        f"BRIEF {stats['brief_mapped']}/{stats['brief_total']}, "
        f"METHODS targets {stats['methods_sections']}, rows {stats['crosswalk_rows']}."
    )
    print(
        f"REPORT: intentionally-implementation-only={stats['implementation_only']}; "
        f"unresolved={stats['unresolved']}."
    )
    print("NOTE: this validator proves structural coverage, not semantic equivalence.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
