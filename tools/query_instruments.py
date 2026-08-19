#!/usr/bin/env python3
"""Render and locally validate frozen-candidate search instruments without network calls."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any


AWARENESS_TERMS = (
    "awareness", "unaware", "conscious", "unconscious", "visibility",
    "visible", "invisible", "unseen", "subliminal", "nonconscious",
)

COMPACT_PROCESS_TERMS = {
    "QCAL4-ATTN": (
        "attentional control", "inhibitory control", "distractor interference",
        "attentional capture",
    ),
    "QCAL4-META": (
        "metacognitive sensitivity", "confidence accuracy", "error monitoring",
        "metacognitive control",
    ),
    "QCAL4-BIND": (
        "feature binding", "object integration", "event integration", "object updating",
    ),
    "QCAL4-MEM": (
        "working memory maintenance", "working memory updating", "episodic encoding",
        "memory retrieval",
    ),
    "QCAL4-DEC": (
        "action selection", "response selection", "rule-guided behavior",
        "rule-guided behaviour", "flexible control",
    ),
}

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
    "canonical-y", "morphology-grammar", "source-paper-terminology",
    "frozen-immediate-parent",
}

TSUSHIMA_DIAGNOSTIC_VARIANTS = (
    {
        "term": "regulation of task-irrelevant distractor interference",
        "provenance_category": "canonical-y",
        "rationale": "Conservative Y assigned from the behavioral dependent measure.",
    },
    {
        "term": "task-irrelevant distractor-interference regulation",
        "provenance_category": "morphology-grammar",
        "derived_from": "regulation of task-irrelevant distractor interference",
        "rationale": "Nominal reordering and hyphenation only; the function is unchanged.",
    },
    {
        "term": "regulating task-irrelevant distractor interference",
        "provenance_category": "morphology-grammar",
        "derived_from": "regulation of task-irrelevant distractor interference",
        "rationale": "Gerund form of the canonical label only.",
    },
    {
        "term": "inhibitory control",
        "provenance_category": "source-paper-terminology",
        "source_pointer": "Tsushima et al. (2006) title and article pp. 1786-1788",
        "rationale": "Terminology explicitly used by the qualifying source paper.",
    },
    {
        "term": "attention filtering",
        "provenance_category": "source-paper-terminology",
        "source_pointer": "Tsushima et al. (2006) article pp. 1786-1788",
        "rationale": "Filtering terminology explicitly used for the observed interference effect.",
    },
    {
        "term": "distractor interference control",
        "provenance_category": "frozen-immediate-parent",
        "frozen_parent_id": "Y-PARENT-DISTRACTOR-INTERFERENCE-CONTROL",
        "rationale": "Single immediate parent frozen for this diagnostic; no neighboring function is added.",
    },
)


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


def render_title_abstract_query(source: str, process_terms: Iterable[str]) -> str:
    """Render one awareness-by-process title/abstract query for a supported source."""
    terms = validate_compact_process_terms(process_terms)
    if source == "OpenAlex":
        return (
            "filter=title_and_abstract.search:("
            + _openalex_clause(AWARENESS_TERMS)
            + ") AND ("
            + _openalex_clause(terms)
            + ")"
        )
    if source == "Europe PMC":
        return (
            "("
            + _europe_pmc_clause(AWARENESS_TERMS)
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
    canonical = [item.get("term") for item in values if item.get("provenance_category") == "canonical-y"]
    if len(canonical) != 1:
        raise ValueError("exactly one canonical-y variant is required")
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
        if category == "source-paper-terminology" and not item.get("source_pointer"):
            raise ValueError(f"source-paper term {term!r} lacks a source pointer")
        if category == "frozen-immediate-parent" and not item.get("frozen_parent_id"):
            raise ValueError(f"immediate-parent term {term!r} lacks a frozen parent identifier")
    return values


def render_process_query(source: str, variants: Iterable[dict[str, Any]]) -> str:
    checked = validate_process_variants(variants)
    query = render_title_abstract_query(source, [item["term"] for item in checked])
    validate_rendered_query(source, query)
    return query


def conservative_instrument_contract() -> dict[str, Any]:
    """Return the locally enforceable, network-free conservative bounds."""
    return {
        "active_families": tuple(COMPACT_PROCESS_TERMS),
        "retired_families": tuple(RETIRED_COMPACT_PROCESS_TERMS),
        "sources": ACTIVE_QCAL_SOURCES,
        "qcal_max_results_per_source_family": QCAL_MAX_RESULTS_PER_SOURCE_FAMILY,
        "qcal_max_windows_per_source_family": 1,
        "process_max_results_per_source_y": PROCESS_MAX_RESULTS_PER_SOURCE_Y,
        "process_max_windows_per_source_y": 1,
        "redistribute_unused_quota": False,
        "blind_lane_mandatory": True,
    }
