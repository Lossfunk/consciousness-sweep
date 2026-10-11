#!/usr/bin/env python3
"""Deterministic bounded full-text sampling for CALIB003 only."""

from __future__ import annotations

import re
from typing import Any, Iterable


PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}
DISCOVERY_ID_RE = re.compile(r"^[A-Za-z0-9._-]+_R([0-9]{6})$")


def _discovery_order(candidate: dict[str, Any]) -> int:
    match = DISCOVERY_ID_RE.fullmatch(str(candidate.get("first_discovery_id", "")))
    if not match:
        raise ValueError("eligible calibration candidates require a durable first_discovery_id")
    return int(match.group(1))


def select_calibration_fulltexts(
    candidates: Iterable[dict[str, Any]], limit: int = 12
) -> list[dict[str, Any]]:
    """Select newly discovered screen-ins by priority, discovery order, then paper ID."""
    if limit < 1:
        raise ValueError("limit must be positive")
    eligible = [
        candidate
        for candidate in candidates
        if candidate.get("newly_discovered") is True
        and candidate.get("abstract_screen") == "screen-in"
    ]
    for candidate in eligible:
        if candidate.get("fulltext_priority") not in PRIORITY_ORDER:
            raise ValueError("eligible calibration candidates require high/medium/low priority")
        if not re.fullmatch(r"P[0-9]{6}", str(candidate.get("paper_id", ""))):
            raise ValueError("eligible calibration candidates require a stable paper_id")
    return sorted(
        eligible,
        key=lambda candidate: (
            PRIORITY_ORDER[candidate["fulltext_priority"]],
            _discovery_order(candidate),
            candidate["paper_id"],
        ),
    )[:limit]
