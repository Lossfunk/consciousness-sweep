#!/usr/bin/env python3
"""Render and locally validate prepared search instruments without network calls."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any


AWARENESS_TERMS = (
    "awareness", "unaware", "conscious", "unconscious", "visibility",
    "visible", "invisible", "unseen", "subliminal", "nonconscious",
)

# Discovery inventory, not an eligibility taxonomy. Distinct windows keep pain,
# hedonic experience and motivation from competing for a single affect quota.
# Broader awareness vocabulary is deliberately tested prospectively; no historical
# calibration is claimed for these revised exact strings.
CALIBRATED_AWARENESS_TERMS = AWARENESS_TERMS + (
    "conscious awareness", "without awareness", "outside awareness", "below awareness",
    "non-conscious", "unconscious processing", "unconscious perception", "awareness threshold",
    "perceptual awareness",
)
COMPACT_PROCESS_TERMS = {
    "QREV6-ATTN": ("attentional control", "inhibitory control", "distractor interference", "attentional capture"),
    "QREV6-META": ("metacognitive sensitivity", "confidence accuracy", "error monitoring", "metacognitive control"),
    "QREV6-BIND": ("feature binding", "object integration", "event integration", "object updating", "perceptual organization", "perceptual adaptation"),
    "QREV6-MEM": ("working memory maintenance", "working memory updating", "episodic encoding", "memory retrieval"),
    "QREV6-DEC": ("action selection", "response selection", "rule-guided behavior", "rule-guided behaviour", "flexible control", "motor control"),
    "QREV6-AFFECT": ("affective appraisal", "emotion regulation", "emotional processing", "affective priming", "emotional evaluation"),
    "QREV6-EXPERIENCE": ("interoception", "body ownership", "bodily self", "sense of agency", "homeostatic regulation", "autonomic regulation"),
    "QREV6-SOCIAL": ("social inference", "theory of mind", "social learning", "empathy", "social evaluation"),
    "QREV6-LEARN": ("perceptual learning", "implicit learning", "sequence learning", "statistical learning", "conditioning", "reinforcement learning"),
    "QREV6-LANGUAGE": ("semantic integration", "semantic priming", "sentence comprehension", "language comprehension", "language production"),
    "QREV6-PAIN": ("pain", "nociception", "unpleasantness", "aversive", "analgesia"),
    "QREV6-HEDONIC": ("pleasure", "hedonic", "liking", "pleasantness", "enjoyment"),
    "QREV6-MOTIVATION": ("motivation", "wanting", "reward", "incentive", "effort allocation"),
}
BLIND_QUERY_FAMILIES = tuple(COMPACT_PROCESS_TERMS) + ("QREV6-OPEN",)


def render_blind_query(source: str, family: str) -> str:
    """Render an independently budgeted coverage cell or unrestricted window."""
    if family in COMPACT_PROCESS_TERMS:
        return render_title_abstract_query(source, COMPACT_PROCESS_TERMS[family], awareness_terms=CALIBRATED_AWARENESS_TERMS)
    if family != "QREV6-OPEN":
        raise ValueError(f"unknown blind family: {family}")
    if source == "OpenAlex":
        return "filter=title_and_abstract.search:(" + _openalex_clause(CALIBRATED_AWARENESS_TERMS) + ")"
    if source == "Europe PMC":
        return "(" + _europe_pmc_clause(CALIBRATED_AWARENESS_TERMS) + ")"
    raise ValueError(f"unsupported source renderer: {source}")


# Retained only as explicit historical/pre-freeze provenance. This pathological
# rendering is not part of the active conservative blind-spot instrument.
RETIRED_COMPACT_PROCESS_TERMS = {
    "QCAL4-LEARN": (
        "error-based learning", "reinforcement learning", "evaluative conditioning",
        "adaptive updating",
    ),
}

ACTIVE_QCAL_SOURCES = ("OpenAlex", "Europe PMC")
QCAL_MAX_RESULTS_PER_SOURCE_FAMILY = 40
PROCESS_MAX_RESULTS_PER_SOURCE_Y = 50

PROHIBITED_BARE_PROCESS_TERMS = {"task", "performance", "experiment", "memory", "decision"}
ALLOWED_VARIANT_PROVENANCE = {
    "canonical-y", "morphology-grammar", "source-paper-terminology", "documented-same-function",
}


def _term(term: str) -> str:
    return f'"{term}"' if any(character.isspace() for character in term) else term


def _openalex_clause(terms: Iterable[str]) -> str:
    return " OR ".join(_term(term) for term in terms)


def _europe_pmc_clause(terms: Iterable[str]) -> str:
    return " OR ".join(f"TITLE_ABS:{_term(term)}" for term in terms)


def validate_compact_process_terms(terms: Iterable[str]) -> tuple[str, ...]:
    values = tuple(terms)
    if not values or any(not isinstance(term, str) or not term.strip() for term in values):
        raise ValueError("compact query requires non-empty process terms")
    prohibited = sorted(term.casefold() for term in values if term.casefold() in PROHIBITED_BARE_PROCESS_TERMS)
    if prohibited:
        raise ValueError(f"generic bare process terms are prohibited: {', '.join(prohibited)}")
    return values


def render_title_abstract_query(
    source: str, process_terms: Iterable[str], *, awareness_terms: Iterable[str] = AWARENESS_TERMS,
) -> str:
    """Render one awareness-by-process title/abstract query for a supported source."""
    terms = validate_compact_process_terms(process_terms)
    if source == "OpenAlex":
        return (
            "filter=title_and_abstract.search:("
            + _openalex_clause(awareness_terms)
            + ") AND ("
            + _openalex_clause(terms)
            + ")"
        )
    if source == "Europe PMC":
        return (
            "("
            + _europe_pmc_clause(awareness_terms)
            + ") AND ("
            + _europe_pmc_clause(terms)
            + ")"
        )
    raise ValueError(f"unsupported source renderer: {source}")


def validate_rendered_query(source: str, query: str) -> None:
    """Perform the local syntax checks possible without calling a source API."""
    if "{{" in query or "}}" in query or query.count("(") != query.count(")"):
        raise ValueError("query contains a template marker or unbalanced parentheses")
    if source == "OpenAlex" and not query.startswith("filter=title_and_abstract.search:("):
        raise ValueError("OpenAlex query is not rendered for title_and_abstract.search")
    if source == "Europe PMC" and "TITLE_ABS:" not in query:
        raise ValueError("Europe PMC query is not rendered for TITLE_ABS")
    if source not in {"OpenAlex", "Europe PMC"}:
        raise ValueError(f"unsupported source renderer: {source}")


def validate_process_variants(variants: Iterable[dict[str, Any]]) -> tuple[dict[str, Any], ...]:
    """Reject unprovenanced or semantically unrestricted dynamic-query variants."""
    values = tuple(variants)
    if any(not isinstance(item, dict) for item in values):
        raise ValueError("each dynamic-query variant must be a provenance record")
    canonical = [item.get("term") for item in values if item.get("provenance_category") == "canonical-y"]
    if len(canonical) != 1:
        raise ValueError("exactly one canonical-y variant is required")
    parents = [item for item in values if item.get("provenance_category") == "frozen-immediate-parent"]
    if parents:
        raise ValueError("no immediate-parent vocabulary is registered for this version")
    seen: set[str] = set()
    for item in values:
        term = item.get("term")
        category = item.get("provenance_category")
        rationale = item.get("rationale")
        if not isinstance(term, str) or not term.strip() or term.casefold() in seen:
            raise ValueError("each dynamic-query term must be non-empty and unique")
        seen.add(term.casefold())
        if category not in ALLOWED_VARIANT_PROVENANCE:
            raise ValueError(f"unrestricted or unknown lexical provenance: {category!r}")
        if not isinstance(rationale, str) or not rationale.strip():
            raise ValueError(f"dynamic-query term {term!r} lacks a rationale")
        if category == "morphology-grammar" and item.get("derived_from") != canonical[0]:
            raise ValueError(f"morphology/grammar term {term!r} must derive from the canonical Y")
        if category in {"source-paper-terminology", "documented-same-function"} and not item.get("source_pointer"):
            raise ValueError(f"source-paper term {term!r} lacks a source pointer")
    return values


def build_process_variants(
    canonical_y: str,
    *,
    canonical_rationale: str,
    morphology_variants: Iterable[dict[str, str]] = (),
    source_terms: Iterable[dict[str, str]] = (),
    equivalent_terms: Iterable[dict[str, str]] = (),
    immediate_parent: dict[str, str] | None = None,
) -> tuple[dict[str, Any], ...]:
    """Build a provenance-complete lexical set from comparison-derived runtime inputs."""
    values: list[dict[str, Any]] = [{
        "term": canonical_y,
        "provenance_category": "canonical-y",
        "rationale": canonical_rationale,
    }]
    for item in morphology_variants:
        values.append({
            "term": item.get("term"),
            "provenance_category": "morphology-grammar",
            "derived_from": canonical_y,
            "rationale": item.get("rationale"),
        })
    for item in source_terms:
        values.append({
            "term": item.get("term"),
            "provenance_category": "source-paper-terminology",
            "source_pointer": item.get("source_pointer"),
            "rationale": item.get("rationale"),
        })
    for item in equivalent_terms:
        values.append({"term": item.get("term"), "provenance_category": "documented-same-function",
                       "source_pointer": item.get("source_pointer"), "rationale": item.get("rationale")})
    if immediate_parent is not None:
        values.append({
            "term": immediate_parent.get("term"),
            "provenance_category": "frozen-immediate-parent",
            "frozen_parent_id": immediate_parent.get("frozen_parent_id"),
            "rationale": immediate_parent.get("rationale"),
        })
    return validate_process_variants(values)


def render_process_query(source: str, variants: Iterable[dict[str, Any]]) -> str:
    checked = validate_process_variants(variants)
    query = render_title_abstract_query(source, [item["term"] for item in checked])
    validate_rendered_query(source, query)
    return query


def process_query_plan(source: str, variants: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Return a deterministic, log-ready bounded query plan for one earned Y."""
    checked = validate_process_variants(variants)
    query = render_process_query(source, checked)
    canonical_y = next(item["term"] for item in checked if item["provenance_category"] == "canonical-y")
    return {
        "source": source,
        "canonical_y": canonical_y,
        "query": query,
        "lexical_provenance": tuple(dict(item) for item in checked),
        "max_results": PROCESS_MAX_RESULTS_PER_SOURCE_Y,
        "max_windows": 1,
        "redistribute_unused_quota": False,
    }


def conservative_instrument_contract() -> dict[str, Any]:
    """Return the locally enforceable, network-free conservative bounds."""
    return {
        "active_families": BLIND_QUERY_FAMILIES,
        "retired_families": tuple(RETIRED_COMPACT_PROCESS_TERMS),
        "sources": ACTIVE_QCAL_SOURCES,
        "qcal_max_results_per_source_family": QCAL_MAX_RESULTS_PER_SOURCE_FAMILY,
        "qcal_max_windows_per_source_family": 1,
        "process_max_results_per_source_y": PROCESS_MAX_RESULTS_PER_SOURCE_Y,
        "process_max_windows_per_source_y": 1,
        "redistribute_unused_quota": False,
        "blind_lane_mandatory": True,
    }
