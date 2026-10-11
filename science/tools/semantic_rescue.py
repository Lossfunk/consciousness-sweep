"""Frozen prospective, non-excluding semantic rescue instrument.

A reviewer supplies paper-specific assertions after reading the available record;
no text matching, numerical score, or local-model label can make a scientific
screening decision here. The returned manifests are pure data persisted through
the package's locked writer.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass, field
from hashlib import sha256
import json
import sys
from typing import Mapping, Sequence


ROUTING_INSTRUMENT_VERSION = "0.1.0"
ASSERTION_VALUES = frozenset({"present", "plausible", "absent", "unclear"})
POSITIVE = frozenset({"present", "plausible"})
DEMOTION_LABELS = frozenset({"low", "supportive"})
LOCAL_LABELS = frozenset({"unreviewed", "high", "medium", "low", "supportive"})

STRUCTURED_PATTERNS = (
    "crossover_or_sign_reversal",
    "nonmonotonic_or_biphasic",
    "awareness_invariant_y",
    "shifted_threshold_and_effect",
    "trial_or_percept_history_matched_input",
    "explicit_alternative_control",
    "performance_or_confidence_matched",
)
PRIMING_KINDS = (
    "response_priming", "motor_priming", "visuomotor_priming",
    "semantic_priming", "affective_priming", "rapid_chase_priming",
)
DOMAIN_CELLS = (
    "bodily_or_interoceptive", "agency_or_control", "affect_or_motivation",
    "patient_dissociation_or_residual", "perceptual_organization_or_history",
    "metacognitive_confidence_or_information_control",
    "learning", "memory", "language", "social", "action",
)
SCIENTIFIC_AXES = (
    "exact_x_awareness", "distinct_y", "awareness_linked_same_y",
    "matched_or_diagnostic_control", "aware_effect",
    "awareness_linked_constraints", "positive_aware_use", "positive_unaware_use",
    "formal_exact_x_unaware_capacity", "partial_x_residual_capacity",
    "direct_vs_indirect_measure_sensitivity", "time_course_or_trajectory",
    "supportive_role", "null_role", "patient_role", "method_role",
    "review_role", "near_neighbor_role",
)
KNOWN_FEATURES = frozenset(SCIENTIFIC_AXES + STRUCTURED_PATTERNS + PRIMING_KINDS
                           + DOMAIN_CELLS + (
                               "structured_same_y_relation",
                               "substantive_unawareness_attempt",
                               "abstract_unavailable",
                           ))


def _digest(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":"))
    return sha256(payload.encode("utf-8")).hexdigest()


def _valid_hash(value: str | None, name: str) -> None:
    if value is None:
        return
    if len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
        raise ValueError(f"{name} must be a lowercase SHA-256 hex digest")


@dataclass(frozen=True)
class FeatureAssertion:
    """One semantic claim; ``unclear`` is evidence uncertainty, not absence."""

    value: str
    reason: str
    source_location: str | None = None

    def __post_init__(self) -> None:
        if self.value not in ASSERTION_VALUES:
            raise ValueError(f"unsupported assertion value: {self.value}")
        if not self.reason.strip():
            raise ValueError("each assertion requires a paper-specific reason")
        if self.value in POSITIVE and not (self.source_location or "").strip():
            raise ValueError("present/plausible assertions require a source pointer")


@dataclass(frozen=True)
class RegimeEvidence:
    """Separate focal, transferred and objective evidence for one named regime."""

    focal_exact_x_result: FeatureAssertion | None = None
    cross_task_transfer: FeatureAssertion | None = None
    objective_discrimination: FeatureAssertion | None = None


@dataclass(frozen=True)
class PaperEvidence:
    paper_id: str
    work_identity: str
    abstract_sha256: str | None
    fulltext_sha256: str | None
    scientific_regime_fingerprint: str
    review_regime_fingerprint: str
    assertions: Mapping[str, FeatureAssertion]
    title_sha256: str | None = None
    awareness_regimes: Mapping[str, RegimeEvidence] = field(default_factory=dict)
    local_label: str = "unreviewed"
    local_label_reason: str = "No local prioritization was supplied."

    def __post_init__(self) -> None:
        for name in ("paper_id", "work_identity", "local_label_reason"):
            if not getattr(self, name).strip():
                raise ValueError(f"{name} is required")
        if self.local_label not in LOCAL_LABELS:
            raise ValueError(f"unsupported local prioritization label: {self.local_label}")
        for name in ("title_sha256", "abstract_sha256", "fulltext_sha256",
                     "scientific_regime_fingerprint", "review_regime_fingerprint"):
            _valid_hash(getattr(self, name), name)
        if self.abstract_sha256 is None:
            if self.title_sha256 is None:
                raise ValueError("missing-abstract records require an immutable title hash")
            if self.assertions.get("abstract_unavailable", None) is None:
                raise ValueError("missing-abstract records require an abstract_unavailable assertion")
        if not self.scientific_regime_fingerprint or not self.review_regime_fingerprint:
            raise ValueError("both regime fingerprints are required")
        if not isinstance(self.assertions, Mapping):
            raise ValueError("assertions must be a named mapping")
        if any(not key.strip() or not isinstance(value, FeatureAssertion)
               for key, value in self.assertions.items()):
            raise ValueError("assertions need named FeatureAssertion values")
        unknown = set(self.assertions) - KNOWN_FEATURES
        if unknown:
            raise ValueError(f"unknown semantic feature(s): {sorted(unknown)}")
        if any(not name.strip() or not isinstance(value, RegimeEvidence)
               for name, value in self.awareness_regimes.items()):
            raise ValueError("awareness regimes need names and RegimeEvidence values")


@dataclass(frozen=True)
class RoutingDecision:
    instrument_version: str
    paper_id: str
    work_identity: str
    evidence_binding_sha256: str
    lanes: tuple[str, ...]
    risk_signatures: tuple[str, ...]
    axis_statuses: Mapping[str, str]
    awareness_regime_statuses: Mapping[str, Mapping[str, str]]
    strongest_agent_review_required: bool
    priority: str
    scientific_disposition: str
    local_label: str
    reason: str
    source_locations: tuple[str, ...]


def _status(assertions: Mapping[str, FeatureAssertion], key: str) -> str:
    item = assertions.get(key)
    return item.value if item else "unassessed"


def _positive(assertions: Mapping[str, FeatureAssertion], key: str) -> bool:
    return _status(assertions, key) in POSITIVE


def _evidence_binding(record: PaperEvidence) -> str:
    return _digest({
        "paper_id": record.paper_id,
        "work_identity": record.work_identity,
        "title_sha256": record.title_sha256,
        "abstract_sha256": record.abstract_sha256,
        "fulltext_sha256": record.fulltext_sha256,
        "scientific_regime_fingerprint": record.scientific_regime_fingerprint,
        "review_regime_fingerprint": record.review_regime_fingerprint,
        "instrument_version": ROUTING_INSTRUMENT_VERSION,
        "assertions": {key: asdict(value) for key, value in sorted(record.assertions.items())},
        "awareness_regimes": {key: asdict(value)
                              for key, value in sorted(record.awareness_regimes.items())},
        "local_label": record.local_label,
        "local_label_reason": record.local_label_reason,
    })


def route_paper(record: PaperEvidence) -> RoutingDecision:
    """Flag semantic rescue lanes without deciding screen-out, A, E, or F.

    Missing assertions remain ``unassessed``. They never become negative
    evidence. A present/plausible pattern is a reviewer assertion with a source
    pointer, never a keyword hit.
    """

    a = record.assertions
    lanes: list[str] = []
    risks: list[str] = []

    three_gates = (
        _positive(a, "exact_x_awareness") and _positive(a, "distinct_y")
        and (_positive(a, "awareness_linked_same_y")
             or _positive(a, "positive_unaware_use"))
    )
    if three_gates and _status(a, "matched_or_diagnostic_control") != "present":
        lanes.append("three-gate-scalar-unclear")
        risks.append("three-gate-scalar-unclear")

    patterns = [key for key in STRUCTURED_PATTERNS if _positive(a, key)]
    if patterns and _status(a, "structured_same_y_relation") != "absent":
        lanes.append("structured-dissociation")
        risks.extend(f"structured:{key}" for key in patterns)

    priming = [key for key in PRIMING_KINDS if _positive(a, key)]
    if priming and (_positive(a, "exact_x_awareness")
                    or _positive(a, "substantive_unawareness_attempt")):
        lanes.append("response-priming")
        risks.append("response-priming")

    for domain in DOMAIN_CELLS:
        if _positive(a, domain):
            lanes.append(f"domain:{domain}")
            risks.append(f"domain:{domain}")

    if record.abstract_sha256 is None:
        risks.append("missing-abstract")
    if _positive(a, "partial_x_residual_capacity"):
        risks.append("partial-x-residual")

    regimes: dict[str, dict[str, str]] = {}
    for name, evidence in sorted(record.awareness_regimes.items()):
        regimes[name] = {
            "focal_exact_x_result": evidence.focal_exact_x_result.value
            if evidence.focal_exact_x_result else "unassessed",
            "cross_task_transfer": evidence.cross_task_transfer.value
            if evidence.cross_task_transfer else "unassessed",
            "objective_discrimination": evidence.objective_discrimination.value
            if evidence.objective_discrimination else "unassessed",
        }
        if (name in ("aware", "higher-awareness")
                and regimes[name]["focal_exact_x_result"] not in POSITIVE
                and regimes[name]["objective_discrimination"] in POSITIVE):
            risks.append("higher-awareness-arm-unverified")

    if record.local_label in DEMOTION_LABELS:
        risks.append("local-demotion")

    locations = {item.source_location for item in a.values()
                 if item.source_location}
    for evidence in record.awareness_regimes.values():
        for member in (evidence.focal_exact_x_result, evidence.cross_task_transfer,
                       evidence.objective_discrimination):
            if member and member.source_location:
                locations.add(member.source_location)
    evidence_reasons = [f"{key}: {a[key].reason}" for key in sorted(a)]
    if record.abstract_sha256 is None:
        priority = "unresolved-record"
    elif lanes:
        priority = "rescue-review"
    else:
        priority = "ordinary-semantic-review"
    # A local demotion by itself remains in ordinary paper-specific semantic
    # review. Strongest-agent escalation is reserved for rescue lanes and the
    # deterministic audit sample chosen below.
    strongest = bool(lanes)
    reason = (f"{record.paper_id} ({record.work_identity}): "
              + ("; ".join(evidence_reasons) if evidence_reasons
                 else "No supplied semantic assertion activates a rescue lane; review remains open.")
              + f" Local label context: {record.local_label_reason}")
    return RoutingDecision(
        instrument_version=ROUTING_INSTRUMENT_VERSION,
        paper_id=record.paper_id,
        work_identity=record.work_identity,
        evidence_binding_sha256=_evidence_binding(record),
        lanes=tuple(sorted(set(lanes))),
        risk_signatures=tuple(sorted(set(risks))),
        axis_statuses={key: _status(a, key) for key in SCIENTIFIC_AXES},
        awareness_regime_statuses=regimes,
        strongest_agent_review_required=strongest,
        priority=priority,
        scientific_disposition="undetermined",
        local_label=record.local_label,
        reason=reason,
        source_locations=tuple(sorted(locations)),
    )


@dataclass(frozen=True)
class AuditSample:
    """Immutable deterministic sample of one demotion route/risk stratum."""

    stratum: str
    population_size: int
    ordered_population_sha256: str
    sampled_paper_ids: tuple[str, ...]
    ordered_sample_sha256: str
    seed: str


@dataclass(frozen=True)
class RouteManifest:
    """Ordered, content-addressed output for a complete routing batch."""

    instrument_version: str
    ordered_paper_ids: tuple[str, ...]
    ordered_bindings_sha256: str
    ordered_outputs_sha256: str
    manifest_sha256: str


def route_manifest(decisions: Sequence[RoutingDecision]) -> RouteManifest:
    """Fingerprint all paper decisions, including source-bound semantic reasons."""

    ordered = sorted(decisions, key=lambda d: d.paper_id)
    ids = tuple(decision.paper_id for decision in ordered)
    if len(set(ids)) != len(ids):
        raise ValueError("a route manifest requires one decision per paper")
    if any(d.instrument_version != ROUTING_INSTRUMENT_VERSION for d in ordered):
        raise ValueError("mixed routing instrument versions")
    bindings = tuple((d.paper_id, d.evidence_binding_sha256) for d in ordered)
    outputs = tuple(asdict(d) for d in ordered)
    bindings_hash = _digest(bindings)
    outputs_hash = _digest(outputs)
    return RouteManifest(
        instrument_version=ROUTING_INSTRUMENT_VERSION,
        ordered_paper_ids=ids,
        ordered_bindings_sha256=bindings_hash,
        ordered_outputs_sha256=outputs_hash,
        manifest_sha256=_digest([ROUTING_INSTRUMENT_VERSION, ids, bindings_hash,
                                 outputs_hash]),
    )


def _stratum(decision: RoutingDecision) -> str:
    return _digest({"label": decision.local_label, "lanes": decision.lanes,
                    "risks": decision.risk_signatures})


def sample_demotions(
    decisions: Sequence[RoutingDecision], *, seed: str,
    min_stratum_size: int = 20, per_stratum: int = 10,
) -> tuple[AuditSample, ...]:
    """Sample every large local-demotion stratum by stable hash ranking.

    The caller freezes/persists the returned population and sample hashes.
    This does not approve demotion or exclude small strata from semantic review.
    """

    if not seed.strip() or min_stratum_size < 1 or per_stratum < 1:
        raise ValueError("nonempty seed and positive sample parameters are required")
    by_id: dict[str, RoutingDecision] = {}
    for decision in decisions:
        if decision.paper_id in by_id:
            raise ValueError(f"duplicate paper decision: {decision.paper_id}")
        by_id[decision.paper_id] = decision
    groups: dict[str, list[RoutingDecision]] = {}
    for decision in decisions:
        if decision.local_label in DEMOTION_LABELS:
            groups.setdefault(_stratum(decision), []).append(decision)
    samples: list[AuditSample] = []
    for stratum, group in sorted(groups.items()):
        if len(group) < min_stratum_size:
            continue
        population = sorted((d.paper_id, d.evidence_binding_sha256) for d in group)
        ranked = sorted(group, key=lambda d: (
            _digest([seed, stratum, d.paper_id, d.evidence_binding_sha256]), d.paper_id))
        chosen = tuple(d.paper_id for d in ranked[:per_stratum])
        samples.append(AuditSample(
            stratum=stratum, population_size=len(group),
            ordered_population_sha256=_digest(population),
            sampled_paper_ids=chosen, ordered_sample_sha256=_digest(chosen),
            seed=seed,
        ))
    return tuple(samples)


@dataclass(frozen=True)
class AffectedSignatureManifest:
    signature: str
    affected_paper_ids: tuple[str, ...]
    ordered_affected_sha256: str


def reopen_affected_signature(
    decisions: Sequence[RoutingDecision], signature: str,
) -> AffectedSignatureManifest:
    """Return the complete local-demotion stratum bearing a frozen risk signature.

    A false-negative audit can name the exact signature. Unaffected signatures
    are omitted. The caller records the signature and manifest before review.
    """

    if not signature.strip():
        raise ValueError("a frozen risk signature is required")
    seen: set[str] = set()
    affected: list[tuple[str, str]] = []
    for decision in decisions:
        if decision.paper_id in seen:
            raise ValueError(f"duplicate paper decision: {decision.paper_id}")
        seen.add(decision.paper_id)
        if (decision.local_label in DEMOTION_LABELS
                and signature in decision.risk_signatures):
            affected.append((decision.paper_id, decision.evidence_binding_sha256))
    affected.sort()
    return AffectedSignatureManifest(signature, tuple(p for p, _ in affected),
                                     _digest(affected))


def _json_assertion(value: object) -> FeatureAssertion:
    if not isinstance(value, dict):
        raise ValueError("each feature assertion must be a JSON object")
    return FeatureAssertion(**value)


def _json_record(value: object) -> PaperEvidence:
    if not isinstance(value, dict):
        raise ValueError("each record must be a JSON object")
    fields = dict(value)
    raw_assertions = fields.get("assertions")
    if not isinstance(raw_assertions, dict):
        raise ValueError("each record requires an assertions object")
    fields["assertions"] = {
        key: _json_assertion(item) for key, item in raw_assertions.items()
    }
    raw_regimes = fields.get("awareness_regimes", {})
    if not isinstance(raw_regimes, dict):
        raise ValueError("awareness_regimes must be a JSON object")
    regimes: dict[str, RegimeEvidence] = {}
    for name, raw in raw_regimes.items():
        if not isinstance(raw, dict):
            raise ValueError(f"awareness regime {name!r} must be a JSON object")
        regimes[name] = RegimeEvidence(**{
            key: _json_assertion(item) if item is not None else None
            for key, item in raw.items()
        })
    fields["awareness_regimes"] = regimes
    return PaperEvidence(**fields)


def route_json_payload(payload: object) -> dict[str, object]:
    """Validate one input batch and return deterministic, JSON-ready outputs."""

    if not isinstance(payload, dict):
        raise ValueError("input must be a JSON object")
    allowed = {"records", "audit_seed", "min_stratum_size", "per_stratum",
               "reopen_signatures"}
    unknown = set(payload) - allowed
    if unknown:
        raise ValueError(f"unknown input field(s): {sorted(unknown)}")
    raw_records = payload.get("records")
    if not isinstance(raw_records, list):
        raise ValueError("records must be a JSON array")
    seed = payload.get("audit_seed")
    if not isinstance(seed, str) or not seed.strip():
        raise ValueError("audit_seed must be a nonempty string")
    minimum = payload.get("min_stratum_size", 20)
    count = payload.get("per_stratum", 10)
    if (isinstance(minimum, bool) or not isinstance(minimum, int)
            or isinstance(count, bool) or not isinstance(count, int)):
        raise ValueError("audit sample sizes must be integers")
    raw_signatures = payload.get("reopen_signatures", [])
    if (not isinstance(raw_signatures, list)
            or any(not isinstance(item, str) or not item.strip()
                   for item in raw_signatures)):
        raise ValueError("reopen_signatures must be an array of nonempty strings")
    if len(set(raw_signatures)) != len(raw_signatures):
        raise ValueError("reopen_signatures must be unique")

    records = [_json_record(item) for item in raw_records]
    decisions = [route_paper(item) for item in records]
    manifest = route_manifest(decisions)  # Also rejects duplicate paper decisions.
    samples = sample_demotions(decisions, seed=seed,
                               min_stratum_size=minimum, per_stratum=count)
    reopened = [reopen_affected_signature(decisions, signature)
                for signature in sorted(raw_signatures)]
    return {
        "instrument_version": ROUTING_INSTRUMENT_VERSION,
        "source_bound_inputs": [asdict(record)
                                for record in sorted(records, key=lambda item: item.paper_id)],
        "decisions": [asdict(decision)
                      for decision in sorted(decisions, key=lambda d: d.paper_id)],
        "route_manifest": asdict(manifest),
        "demotion_samples": [asdict(sample) for sample in samples],
        "affected_signature_manifests": [asdict(item) for item in reopened],
    }


def global_audit_json_payload(payload: object) -> dict[str, object]:
    """Freeze cumulative demotion strata across all current routing batches.

    Input contains exactly one latest source-validated route event per logical
    paper. The caller preserves older route events as provenance but excludes
    them from this current-state frame. This closes the small-batch audit gap.
    """
    if not isinstance(payload, dict):
        raise ValueError("global audit input must be a JSON object")
    allowed = {"route_events", "audit_seed", "min_stratum_size", "per_stratum",
               "reopen_signatures"}
    if set(payload) - allowed:
        raise ValueError(f"unknown global audit input field(s): {sorted(set(payload) - allowed)}")
    raw = payload.get("route_events")
    if not isinstance(raw, list):
        raise ValueError("route_events must be a JSON array")
    seed = payload.get("audit_seed")
    minimum = payload.get("min_stratum_size", 20)
    count = payload.get("per_stratum", 10)
    signatures = payload.get("reopen_signatures", [])
    if not isinstance(seed, str) or not seed.strip():
        raise ValueError("audit_seed must be a nonempty string")
    if (isinstance(minimum, bool) or not isinstance(minimum, int) or minimum < 1
            or isinstance(count, bool) or not isinstance(count, int) or count < 1):
        raise ValueError("audit sample sizes must be positive integers")
    if (not isinstance(signatures, list)
            or any(not isinstance(item, str) or not item.strip() for item in signatures)
            or len(set(signatures)) != len(signatures)):
        raise ValueError("reopen_signatures must be unique nonempty strings")
    entries: list[tuple[str, RoutingDecision]] = []
    for item in raw:
        if not isinstance(item, dict) or set(item) != {"decision_id", "decision"}:
            raise ValueError("each route event needs decision_id and decision")
        identifier = item["decision_id"]
        if not isinstance(identifier, str) or not identifier:
            raise ValueError("route decision_id is required")
        decision = item["decision"]
        if not isinstance(decision, dict):
            raise ValueError("route decision must be an object")
        try:
            routed = RoutingDecision(**decision)
        except TypeError as exc:
            raise ValueError(f"invalid route decision: {exc}") from exc
        if routed.instrument_version != ROUTING_INSTRUMENT_VERSION:
            raise ValueError("mixed routing instrument versions")
        entries.append((identifier, routed))
    if len({item[0] for item in entries}) != len(entries):
        raise ValueError("duplicate route decision_id")
    if len({item[1].paper_id for item in entries}) != len(entries):
        raise ValueError("global audit needs one current decision per paper")
    entries.sort(key=lambda item: item[1].paper_id)
    decisions = [item[1] for item in entries]
    samples = sample_demotions(decisions, seed=seed,
                               min_stratum_size=minimum, per_stratum=count)
    reopened = [reopen_affected_signature(decisions, signature)
                for signature in sorted(signatures)]
    frame = [(identifier, decision.paper_id, decision.evidence_binding_sha256)
             for identifier, decision in entries]
    return {
        "instrument_version": ROUTING_INSTRUMENT_VERSION,
        "route_decision_ids": [identifier for identifier, _ in entries],
        "ordered_routes_sha256": _digest(frame),
        "audit_seed": seed,
        "min_stratum_size": minimum,
        "per_stratum": count,
        "reopen_signatures": sorted(signatures),
        "demotion_samples": [asdict(item) for item in samples],
        "affected_signature_manifests": [asdict(item) for item in reopened],
    }


def main(argv: Sequence[str] | None = None) -> int:
    """Read a JSON batch and print JSON results; never mutate a run."""

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--input", default="-", metavar="JSON_PATH",
                        help="JSON input path, or '-' for standard input (default)")
    parser.add_argument("--mode", choices=("route", "global-audit"), default="route")
    args = parser.parse_args(argv)
    try:
        if args.input == "-":
            payload = json.load(sys.stdin)
        else:
            with open(args.input, encoding="utf-8") as stream:
                payload = json.load(stream)
        result = (route_json_payload(payload) if args.mode == "route"
                  else global_audit_json_payload(payload))
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    json.dump(result, sys.stdout, sort_keys=True, ensure_ascii=True,
              separators=(",", ":"))
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
