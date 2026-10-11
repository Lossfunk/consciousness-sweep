#!/usr/bin/env python3
"""Prepare an isolated identity-only seed revision; never freeze or start a run."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shutil
import unicodedata
from pathlib import Path
from typing import Any

import yaml

from leakage_guard import NEUTRAL_EMPIRICAL_SEED_REASON, REGISTERED_FACING_FILES
from postrun_human_decisions import read_events
from structured_write import dry_run_bibliographic_normalization
from render_fulltext_review import render

ROOT = Path(__file__).resolve().parents[1]
FIELDS = ("seed_id", "title", "authors", "year", "doi", "url", "seed_reason", "notes")
IDENTITY_FIELDS = ("seed_id", "title", "authors", "year", "doi", "url")


def canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":")) + "\n").encode("utf-8")


def identity_manifest(root: Path) -> dict[str, Any]:
    identities = {}
    for name in ("seeds_empirical.csv", "seeds_reviews.csv"):
        with (root / name).open(newline="", encoding="utf-8-sig") as handle:
            identities[name] = [{field: row.get(field, "") for field in IDENTITY_FIELDS}
                                for row in csv.DictReader(handle)]
    return {"format": "neutral-seed-identities-v1", "identities": identities}


def identity_hash(root: Path) -> str:
    return hashlib.sha256(canonical(identity_manifest(root))).hexdigest()


def seed_scope_errors(root: Path, config: dict[str, Any]) -> list[str]:
    errors = []
    scope = config.get("seed_scope")
    if not isinstance(scope, dict):
        return ["config.seed_scope must declare the frozen seed basis"]
    if scope.get("basis") not in {"manuscript-bibliography", "author-vetted-primary-support"}:
        errors.append("seed_scope.basis must be manuscript-bibliography or author-vetted-primary-support")
    if not str(scope.get("authorization") or "").strip():
        errors.append("seed_scope.authorization must identify the explicit commissioning provenance")
    try:
        expected = identity_hash(root)
        if scope.get("identity_manifest_sha256") != expected:
            errors.append("seed_scope identity-manifest hash does not match frozen seed CSVs")
        authorization = json.loads((root / "seed_authorization.json").read_text(encoding="utf-8"))
        if authorization.get("basis") != scope.get("basis") or authorization.get("identity_manifest_sha256") != expected:
            errors.append("seed authorization does not match the declared basis and frozen identities")
        if scope.get("basis") == "author-vetted-primary-support":
            if authorization.get("selection_source") != "validated-explicit-human-decision-log":
                errors.append("author-vetted seeds require explicit human decisions, not model recommendations")
            if not re.fullmatch(r"[a-f0-9]{64}", str(authorization.get("human_decision_log_sha256") or "")):
                errors.append("author-vetted seed authorization needs the human decision log hash")
            accepted = authorization.get("accepted_identity_events")
            if not isinstance(accepted, list) or not accepted:
                errors.append("author-vetted seed authorization has no accepted identity events")
            else:
                manifest_ids = [row["seed_id"] for row in identity_manifest(root)["identities"]["seeds_empirical.csv"]]
                if [item.get("seed_id") for item in accepted if isinstance(item, dict)] != manifest_ids:
                    errors.append("author acceptance identities do not exactly cover the ordered empirical seed manifest")
                for item in accepted:
                    if (not isinstance(item, dict) or not str(item.get("event_id") or "").strip()
                            or item.get("origin") not in {"user", "manuscript"}
                            or item.get("explicit_user_decision") is not (item.get("origin") == "user")):
                        errors.append("seed acceptance lacks an explicit user event or manuscript initialization provenance")
                        break
    except (OSError, ValueError, TypeError, KeyError) as exc:
        errors.append(f"seed-scope authorization cannot be verified: {exc}")
    return errors


def prepare(root: Path, destination: Path, decision_log: Path, bibliography: Path,
            *, revision_version: str, authorization_reason: str,
            original_graph_reference: str | None = None) -> dict[str, Any]:
    """Consume explicit human events; recommendations are never an input type.

    The attestation records execution provenance. It cannot authenticate the
    human independently of the trusted commissioning/decision-record process.
    """
    if destination.exists():
        raise ValueError("refusing an existing destination; registered/frozen inputs are never edited")
    if not re.fullmatch(r"\d+\.\d+\.\d+-candidate", revision_version):
        raise ValueError("a new pre-freeze revision version X.Y.Z-candidate is required")
    config = yaml.safe_load((root / "config.yaml").read_text(encoding="utf-8"))
    if revision_version.removesuffix("-candidate") == str(config["protocol_version"]).removesuffix("-candidate"):
        raise ValueError("the new seed scope must have a distinct protocol/package revision")
    if not authorization_reason.strip():
        raise ValueError("explicit commissioning authorization is required")
    current = {}
    for event in read_events(decision_log):
        current[event["work_key"]] = event
    accepted = {key: event for key, event in current.items() if event["role"] in {"primary", "support"}}
    if not accepted:
        raise ValueError("no current explicit human primary/support acceptance; do not substitute recommendations")
    with bibliography.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        required = {"work_key", "title", "authors", "year", "doi", "url", "article_version"}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError("bibliography CSV requires work_key,title,authors,year,doi,url,article_version")
        indexed = {}
        for row in reader:
            if row["work_key"] in indexed:
                raise ValueError("duplicate bibliographic work_key; resolve before preparation")
            indexed[row["work_key"]] = row
    if set(accepted) - set(indexed):
        raise ValueError("accepted identities missing from bibliography: " + ", ".join(sorted(set(accepted) - set(indexed))))
    records = [indexed[key] for key in sorted(accepted)]
    normalized = dry_run_bibliographic_normalization(records)
    seeds = []
    events = []
    seen = set()
    for index, (record, normalized_identity) in enumerate(zip(records, normalized), 1):
        event = accepted[record["work_key"]]
        if record["article_version"] != event["article_version"]:
            raise ValueError("bibliographic article version differs from explicit author decision")
        if any(not str(record[key]).strip() for key in ("title", "authors", "year")):
            raise ValueError("each accepted identity needs title, authors and year")
        if not re.fullmatch(r"\d{4}", record["year"].strip()):
            raise ValueError("bibliographic year must be four digits")
        doi = normalized_identity["doi"]
        title = " ".join(unicodedata.normalize("NFKC", record["title"]).casefold().split()).strip(" .,:;\"'")
        key = ("doi", doi) if doi else ("bibliographic", title, record["year"].strip(), " ".join(record["authors"].casefold().split()))
        if key in seen:
            raise ValueError("confirmed duplicate accepted identities; resolve explicit human event mapping before preparation")
        seen.add(key)
        seed_id = f"ESEED{index:03d}"
        seeds.append({"seed_id": seed_id, "title": record["title"].strip(), "authors": record["authors"].strip(),
                      "year": record["year"].strip(), "doi": doi or "", "url": normalized_identity["doi_resolver_url"] or normalized_identity["url"] or "",
                      "seed_reason": NEUTRAL_EMPIRICAL_SEED_REASON,
                      "notes": "Identity selected from explicit author decisions before freeze; reassess independently under this revision."})
        # Identity/procedural provenance only. No previous role, A/E/F or expected
        # scientific result is distributed to the new independent reviewer.
        events.append({"seed_id": seed_id, "event_id": event["event_id"], "origin": event["origin"],
                       "explicit_user_decision": event["explicit_user_decision"]})
    source_hashes = {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in REGISTERED_FACING_FILES}
    destination.mkdir(parents=True)
    for name in REGISTERED_FACING_FILES:
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(root / name, target)
    for name in ("runs", "outputs/consolidated"):
        (destination / name).mkdir(parents=True, exist_ok=True)
    with (destination / "seeds_empirical.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(seeds)
    old_version = config["protocol_version"]
    old_package = config["package_version"]
    for name in REGISTERED_FACING_FILES:
        if name.endswith((".md", ".yaml", ".json")) and name not in {"config.yaml", "RELEASE_READINESS.json"}:
            path = destination / name
            path.write_text(path.read_text(encoding="utf-8").replace(old_package, "package-" + revision_version).replace(old_version, revision_version), encoding="utf-8")
    # A verified final source can prepare a future candidate too. Do not carry
    # its frozen/ready front matter into the new, unvalidated seed scope.
    for name in ("PROTOCOL.md", "AGENTS.md", "queries.md"):
        path = destination / name
        text = path.read_text(encoding="utf-8")
        text = re.sub(r"(?m)^\*\*(?:Registration status|Status):\*\*.*$",
                      "**Registration status:** pre-freeze candidate; registered execution prohibited until release validation", text, count=1)
        path.write_text(text, encoding="utf-8")
    readme = destination / "README.md"
    text = readme.read_text(encoding="utf-8")
    text = re.sub(r"(?m)^\*\*Status:\*\*.*$",
                  f"**Status:** protocol `{revision_version}`, package `package-{revision_version}`, schema `{config['schema_version']}`. New pre-freeze seed revision; no run started.", text, count=1)
    readme.write_text(text, encoding="utf-8")
    config.update(protocol_version=revision_version, package_version="package-" + revision_version, registration_status="pre-freeze")
    config["seed_scope"] = {"basis": "author-vetted-primary-support", "authorization": authorization_reason,
        "identity_manifest_sha256": identity_hash(destination), "original_graph_reference": original_graph_reference,
        "distance_convention": "seed-relative; original-graph depth only when independently established"}
    (destination / "config.yaml").write_text(yaml.safe_dump(config, sort_keys=False, allow_unicode=True), encoding="utf-8")
    attestation = {"basis": "author-vetted-primary-support", "selection_source": "validated-explicit-human-decision-log",
        "identity_manifest_sha256": identity_hash(destination),
        "human_decision_log_sha256": hashlib.sha256(decision_log.read_bytes()).hexdigest(),
        "accepted_identity_events": events}
    (destination / "seed_authorization.json").write_bytes(canonical(attestation))
    (destination / "RELEASE_READINESS.json").write_bytes(canonical({"status": "blocked",
        "protocol_version": revision_version, "package_version": "package-" + revision_version,
        "schema_version": config["schema_version"],
        "reason": "New commissioned seed revision prepared; prospective freeze/validation and explicit launch remain separate obligations."}))
    (destination / "FULLTEXT_REVIEW.md").write_text(render(destination), encoding="utf-8")
    if any(hashlib.sha256((root / name).read_bytes()).hexdigest() != value for name, value in source_hashes.items()):
        raise ValueError("source package changed during preparation; do not use incomplete destination")
    errors = seed_scope_errors(destination, config)
    if errors:
        raise ValueError("\n".join(errors))
    return {"status": "prepared-not-frozen-or-launched", "seed_count": len(seeds), "destination": str(destination),
            "identity_manifest_sha256": identity_hash(destination), "source_inputs": source_hashes}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--human-decisions", type=Path, required=True)
    parser.add_argument("--bibliography", type=Path, required=True)
    parser.add_argument("--revision-version", required=True)
    parser.add_argument("--authorization", required=True)
    parser.add_argument("--original-graph-reference")
    args = parser.parse_args()
    try:
        result = prepare(args.root, args.destination, args.human_decisions, args.bibliography,
                         revision_version=args.revision_version, authorization_reason=args.authorization,
                         original_graph_reference=args.original_graph_reference)
    except (OSError, ValueError) as exc:
        print(f"FAIL: {exc}")
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
