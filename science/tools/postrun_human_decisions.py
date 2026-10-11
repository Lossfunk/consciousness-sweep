"""Append explicit human role events and derive a current golden view; never called by handoff builder."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

from postrun_handoff import HandoffError, canonical


SCHEMA = json.loads((Path(__file__).resolve().parents[1] / "schemas/postrun_human_decision.schema.json").read_text(encoding="utf-8"))


def check(event: dict[str, Any]) -> None:
    errors = list(Draft202012Validator(SCHEMA, format_checker=FormatChecker()).iter_errors(event))
    if errors:
        raise HandoffError("human decision schema: " + "; ".join(error.message for error in errors))


def read_events(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    events = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line:
            raise HandoffError(f"empty decision-log line {line_number}")
        event = json.loads(line)
        check(event)
        events.append(event)
    ids = [event["event_id"] for event in events]
    if len(ids) != len(set(ids)):
        raise HandoffError("duplicate human decision event ID")
    return events


def append_event(log_path: Path, event: dict[str, Any], *, explicit_user_action: bool = False, manuscript_initialization: bool = False) -> None:
    check(event)
    if event["origin"] == "user" and not explicit_user_action:
        raise HandoffError("user event requires explicit --user-decision action")
    if event["origin"] == "manuscript" and not manuscript_initialization:
        raise HandoffError("manuscript event requires explicit --initialize-manuscript action")
    events = read_events(log_path)
    if any(previous["event_id"] == event["event_id"] for previous in events):
        raise HandoffError("event ID already exists")
    if event["origin"] == "manuscript" and any(previous["work_key"] == event["work_key"] for previous in events):
        raise HandoffError("manuscript initialization cannot overwrite an existing work")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def derive(log_path: Path, out_path: Path) -> dict[str, Any]:
    current: dict[str, dict[str, Any]] = {}
    for event in read_events(log_path):
        current[event["work_key"]] = event
    accepted = [
        {"work_key": key, "role": event["role"], "event_id": event["event_id"], "article_version": event["article_version"], "source_reference": event["source_reference"]}
        for key, event in sorted(current.items()) if event["role"] in {"primary", "support"}
    ]
    view = {"schema_version": "0.1.0", "accepted": accepted}
    out_path.parent.mkdir(parents=True, exist_ok=True)
    temp = out_path.with_suffix(out_path.suffix + ".tmp")
    temp.write_bytes(canonical(view))
    temp.replace(out_path)
    return view


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    append = sub.add_parser("append")
    append.add_argument("--log", type=Path, required=True)
    append.add_argument("--event", type=Path, required=True)
    group = append.add_mutually_exclusive_group(required=True)
    group.add_argument("--user-decision", action="store_true")
    group.add_argument("--initialize-manuscript", action="store_true")
    view = sub.add_parser("derive")
    view.add_argument("--log", type=Path, required=True)
    view.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == "append":
            event = json.loads(args.event.read_text(encoding="utf-8"))
            append_event(args.log, event, explicit_user_action=args.user_decision, manuscript_initialization=args.initialize_manuscript)
        else:
            derive(args.log, args.out)
    except (HandoffError, OSError, json.JSONDecodeError) as exc:
        parser.exit(2, f"human-decision error: {exc}\n")


if __name__ == "__main__":
    main()
