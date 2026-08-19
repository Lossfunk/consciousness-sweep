#!/usr/bin/env python3
"""Conservative semantic guard against anchor answer keys in registered inputs."""

from __future__ import annotations

import argparse
import ast
import csv
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NEUTRAL_EMPIRICAL_SEED_REASON = (
    "Frozen empirical seed identified during pre-registration manual scoping; "
    "retained as a guaranteed candidate-lot entry"
)

# This allowlist deliberately excludes diagnostics, tests, runs, outputs, and prose drafts.
REGISTERED_FACING_FILES = (
    "AGENTS.md",
    "PROTOCOL.md",
    "config.yaml",
    "queries.md",
    "requirements.txt",
    "seeds_empirical.csv",
    "seeds_reviews.csv",
    "schemas/auxiliary_sources.schema.json",
    "schemas/decision_log.schema.json",
    "schemas/discoveries.schema.json",
    "schemas/evidence_assessments.schema.json",
    "schemas/evidence_bundles.schema.json",
    "schemas/evidence_links.schema.json",
    "schemas/experiment_groups.schema.json",
    "schemas/experiments.schema.json",
    "schemas/fulltext_assets.schema.json",
    "schemas/missing_texts.schema.json",
    "schemas/papers.schema.json",
    "schemas/run_state.schema.json",
    "schemas/search_log.schema.json",
    "tools/bootstrap_env.py",
    "tools/calibration_sampling.py",
    "tools/derive_outputs.py",
    "tools/execution_contract.py",
    "tools/init_run.py",
    "tools/leakage_guard.py",
    "tools/preflight.py",
    "tools/query_instruments.py",
    "tools/structured_write.py",
    "tools/validate_run.py",
)

ANSWER_CUE = re.compile(
    r"(?:A-(?:direct|validated|transfer-risk|absent)|"
    r"E-(?:matched|diagnostic|physical-only|uncontrolled)|"
    r"F-(?:meaningful|ambiguous|not-meaningful)|"
    r"Meyen-(?:satisfied|failed|unassessable)|"
    r"canonical[ _-]?y|focal experiment|expected (?:classification|result|outcome)|"
    r"constraint-ready|preserved[ -]capacity|awareness-linked example|"
    r"strategic cue use|metacognitive calibration|binding survives|"
    r"distractor (?:interference )?(?:regulation|control)|"
    r"diagnostic variants?|should (?:qualify|survive)|"
    r"sentinel (?:set|list|identity|identities|recovery))",
    re.IGNORECASE,
)
SEED_ANSWER_CUE = re.compile(
    r"(?:A-(?:direct|validated|transfer-risk|absent)|"
    r"E-(?:matched|diagnostic|physical-only|uncontrolled)|"
    r"F-(?:meaningful|ambiguous|not-meaningful)|"
    r"Meyen-(?:satisfied|failed|unassessable)|"
    r"preserved[ -]capacity|awareness[- ]effect|unaware[- ]capacity|"
    r"constraint-ready|strategic cue use|metacognitive calibration|"
    r"feature[- ]location binding|attentional[- ]control|"
    r"focal experiment|expected (?:classification|result|outcome))",
    re.IGNORECASE,
)


def empirical_anchor_tokens(seed_path: Path) -> tuple[str, ...]:
    """Derive author-family-name tokens from the frozen empirical bibliography."""
    tokens: set[str] = set()
    with seed_path.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            for author in (row.get("authors") or "").split(";"):
                first = author.strip().split(" ", 1)[0]
                if len(first) >= 3:
                    tokens.add(first.casefold())
    return tuple(sorted(tokens))


def _anchor_pattern(tokens: tuple[str, ...]) -> re.Pattern[str]:
    alternatives = "|".join(re.escape(token) for token in sorted(tokens, key=len, reverse=True))
    return re.compile(rf"(?<![\w-])(?:{alternatives})(?![\w-])", re.IGNORECASE)


def empirical_seed_errors(path: Path) -> list[str]:
    errors: list[str] = []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        for line_number, row in enumerate(csv.DictReader(handle), start=2):
            seed_id = row.get("seed_id") or f"line {line_number}"
            reason = (row.get("seed_reason") or "").strip()
            notes = (row.get("notes") or "").strip()
            if reason != NEUTRAL_EMPIRICAL_SEED_REASON:
                errors.append(
                    f"seeds_empirical.csv:{line_number}: {seed_id} seed_reason is not neutral procedural provenance"
                )
            if SEED_ANSWER_CUE.search(reason) or SEED_ANSWER_CUE.search(notes):
                errors.append(
                    f"seeds_empirical.csv:{line_number}: {seed_id} metadata contains a scientific answer cue"
                )
    return errors


def named_answer_context_errors(path: Path, anchor_tokens: tuple[str, ...]) -> list[str]:
    """Flag anchor names coupled to answer cues while allowing names alone."""
    if path.name in {"seeds_empirical.csv", "seeds_reviews.csv"}:
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    anchor = _anchor_pattern(anchor_tokens)
    errors: list[str] = []
    for index, line in enumerate(lines):
        if not anchor.search(line):
            continue
        start = max(0, index - 1)
        end = min(len(lines), index + 2)
        context = " ".join(lines[start:end])
        if ANSWER_CUE.search(context):
            errors.append(
                f"{path.as_posix()}:{index + 1}: empirical anchor is coupled to a classification, focal-Y, or sentinel cue"
            )
    return errors


def anchor_specific_tool_identifier_errors(path: Path, anchor_tokens: tuple[str, ...]) -> list[str]:
    """Flag anchor-named runtime constants/functions without scanning prose surnames blindly."""
    if path.name == "leakage_guard.py":
        return []
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    anchor = _anchor_pattern(anchor_tokens)
    errors: list[str] = []
    for node in ast.walk(tree):
        name = None
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            name = node.name
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            name = node.id
        if name and anchor.search(name.replace("_", " ")):
            errors.append(f"{path.as_posix()}:{getattr(node, 'lineno', 1)}: anchor-specific runtime identifier {name!r}")
    return sorted(set(errors))


def registered_leakage_errors(root: Path) -> list[str]:
    root = root.resolve()
    errors: list[str] = []
    for relative in REGISTERED_FACING_FILES:
        if not (root / relative).is_file():
            errors.append(f"missing registered-facing allowlist file: {relative}")
    seed_path = root / "seeds_empirical.csv"
    if not seed_path.is_file():
        return errors
    tokens = empirical_anchor_tokens(seed_path)
    errors.extend(empirical_seed_errors(seed_path))
    for relative in REGISTERED_FACING_FILES:
        path = root / relative
        if not path.is_file():
            continue
        if relative not in {"seeds_empirical.csv", "seeds_reviews.csv"}:
            # Keep diagnostics readable by reporting repository-relative paths.
            found = named_answer_context_errors(path, tokens)
            errors.extend(error.replace(path.as_posix(), relative, 1) for error in found)
        if relative.startswith("tools/") and path.suffix == ".py":
            found = anchor_specific_tool_identifier_errors(path, tokens)
            errors.extend(error.replace(path.as_posix(), relative, 1) for error in found)
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    errors = registered_leakage_errors(args.root)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(
        "PASS: registered-facing leakage guard found no non-neutral seed rationale, "
        "named anchor answer context, or anchor-specific runtime identifier."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
