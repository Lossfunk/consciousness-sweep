"""Concise decision-trail transport; scientific certification remains separate.

Only shape, source identity status, asset/unit references and unread exceptions
are validated here. Text and dispositions are never classified by keywords,
scores or tests that duplicate PROTOCOL's scientific judgment.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any

from jsonschema import Draft202012Validator

SCHEMA_VERSION = "concise-decision-trail-v1"


def _object(properties: dict[str, Any]) -> dict[str, Any]:
    return {"type": "object", "additionalProperties": False,
            "properties": properties, "required": list(properties)}


def _array(items: dict[str, Any], *, minimum: int = 0) -> dict[str, Any]:
    result = {"type": "array", "items": items}
    if minimum:
        result["minItems"] = minimum
    return result


def _enum(*values: str) -> dict[str, Any]:
    return {"type": "string", "enum": list(values)}


def _ref(name: str) -> dict[str, str]:
    return {"$ref": f"#/$defs/{name}"}


_TEXT = {"type": "string", "minLength": 1}
_DECISION = _enum("prospect", "context", "unresolved")
_SCHEMA = _object({
    "source_identity": _object({
        "status": _enum("match", "mismatch", "unclear"), "reason": _TEXT,
    }),
    "assessment_status": _enum("complete", "partial", "source-identity-unresolved"),
    "unread_source_units": _array(_object({
        "asset_id": _ref("source_asset_id"),
        "unit_ids": _array(_ref("source_unit_id"), minimum=1), "reason": _TEXT,
    })),
    "paper_decision": _DECISION,
    "paper_reason": _TEXT,
    "claims": _array(_object({
        "comparison": _TEXT,
        "x_and_existence": _TEXT,
        "awareness_evidence": _TEXT,
        "downstream_use": _TEXT,
        "decisive_evidence": _array(_object({
            "asset_id": _ref("source_asset_id"),
            "unit_ids": _array(_ref("source_unit_id"), minimum=1),
            "location_detail": _TEXT, "observation": _TEXT,
        }), minimum=1),
        "supported_claim": _TEXT,
        "remaining_alternative": _TEXT,
        "contribution_reasoning": _TEXT,
        "decision": _DECISION,
        "reason_and_vetting_question": _TEXT,
    })),
    "reading_gaps": _array(_TEXT),
})
_SCHEMA["$defs"] = {"source_asset_id": _TEXT, "source_unit_id": _TEXT}


def _source_units(packet: dict[str, Any]) -> dict[str, set[str]]:
    """Read source-scoped units, refusing malformed packets before binding IDs."""
    supplied: dict[str, set[str]] = {}
    sources = packet.get("sources", [])
    if not isinstance(sources, list) or not sources:
        raise ValueError("packet requires supplied source assets and units")
    for source in sources:
        if not isinstance(source, dict):
            raise ValueError("packet source must be an object")
        asset_id = source.get("asset_id")
        if not isinstance(asset_id, str) or not asset_id.strip():
            raise ValueError("packet source requires a nonempty asset_id")
        if asset_id in supplied:
            raise ValueError(f"packet repeats asset_id {asset_id}")
        units = source.get("units", [])
        if not isinstance(units, list) or not units:
            raise ValueError(f"packet source {asset_id}: nonempty unit IDs required")
        keys = [unit.get("unit_id") if isinstance(unit, dict) else unit for unit in units]
        if any(not isinstance(key, str) or not key.strip() for key in keys):
            raise ValueError(f"packet source {asset_id}: nonempty string unit IDs required")
        if len(keys) != len(set(keys)):
            raise ValueError(f"packet source {asset_id}: repeated unit IDs")
        supplied[asset_id] = set(keys)
    return supplied


def output_schema(packet: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return the strict model shape, optionally enum-bound to supplied units.

    No paper identifiers, hashes, schema versions or source prose are echoed by
    the model. The code envelope binds those values. Asset/unit combinations are
    validated separately: page:1 in two assets does not denote the same source.
    """
    schema = deepcopy(_SCHEMA)
    if packet is not None:
        supplied = _source_units(packet)
        schema["$defs"]["source_asset_id"] = _enum(*supplied)
        schema["$defs"]["source_unit_id"] = _enum(*sorted(set().union(*supplied.values())))
    return schema


def validate_assessment(result: dict[str, Any], packet: dict[str, Any]) -> list[str]:
    """Return provenance/structure errors, never scientific approval.

    A complete assessment attests to reading every supplied extracted unit.
    Partial reading names exceptions rather than repeating the entire page map.
    A source-unit location is mandatory for each represented decisive item;
    citing an unread unit or a page from another asset is an integrity error.
    """
    errors: list[str] = []
    for error in sorted(Draft202012Validator(_SCHEMA).iter_errors(result),
                        key=lambda item: tuple(str(part) for part in item.path)):
        path = "/".join(str(part) for part in error.path) or "<root>"
        errors.append(f"{path}: {error.message}")
    if errors:
        return errors
    try:
        supplied = _source_units(packet)
    except ValueError as exc:
        return [str(exc)]

    def nonblank(value: Any, path: str = "") -> None:
        if isinstance(value, str) and not value.strip():
            errors.append(f"{path}: text must not be blank")
        elif isinstance(value, dict):
            for key, child in value.items():
                nonblank(child, f"{path}/{key}")
        elif isinstance(value, list):
            for index, child in enumerate(value):
                nonblank(child, f"{path}/{index}")
    nonblank(result)

    def checked_pairs(location: dict[str, Any], path: str) -> set[tuple[str, str]]:
        asset_id, unit_ids = location["asset_id"], location["unit_ids"]
        if asset_id not in supplied:
            errors.append(f"{path}: unknown asset {asset_id}")
        elif set(unit_ids) - supplied[asset_id]:
            errors.append(f"{path}: unknown source units for asset {asset_id}")
        if len(unit_ids) != len(set(unit_ids)):
            errors.append(f"{path}: repeated source units")
        return {(asset_id, unit_id) for unit_id in unit_ids}

    unread: set[tuple[str, str]] = set()
    for index, location in enumerate(result["unread_source_units"]):
        path = f"unread_source_units/{index}"
        pairs = checked_pairs(location, path)
        if unread & pairs:
            errors.append(f"{path}: source unit listed unread more than once")
        unread.update(pairs)
    for claim_index, claim in enumerate(result["claims"]):
        for item_index, location in enumerate(claim["decisive_evidence"]):
            path = f"claims/{claim_index}/decisive_evidence/{item_index}"
            if checked_pairs(location, path) & unread:
                errors.append(f"{path}: cites unread source units")

    status = result["assessment_status"]
    identity = result["source_identity"]["status"]
    if status == "complete" and not result["claims"]:
        errors.append("complete assessment requires at least one source-located claim/decision trail")
    if status == "complete" and unread:
        errors.append("complete assessment contains unread source units")
    if identity != "match" and status != "source-identity-unresolved":
        errors.append("unresolved source identity requires source-identity-unresolved assessment status")
    if identity == "match" and status == "source-identity-unresolved":
        errors.append("source-identity-unresolved assessment contradicts matched source identity")
    return errors


def assessment_warnings(result: dict[str, Any], packet: dict[str, Any]) -> list[str]:
    """Surface staging limitations without changing claims or their decisions."""
    errors = validate_assessment(result, packet)
    if errors:
        return ["Assessment has structural/provenance errors; validation must be resolved."]
    warnings = []
    if result["assessment_status"] != "complete":
        warnings.append(f"Assessment is {result['assessment_status']}; full source reading is not complete.")
    if not result["claims"]:
        warnings.append("No source-located claim trail was produced.")
    if result["reading_gaps"]:
        warnings.append("Reading limitations are reported; inspect reading_gaps before using the claims.")
    return warnings
