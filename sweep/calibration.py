"""Coordinator-only seed checks against a versioned, source-reviewed baseline.

Normal seed work is the calibration work. This module never modifies a scientific
decision, changes a model, or sends reference answers to a source reader. A matching
paper label is only a disposition check; semantic fidelity requires an explicit,
source-located comparison of the represented claims and their limits.
"""
from __future__ import annotations

from copy import copy, deepcopy
from contextlib import contextmanager
import json
from pathlib import Path

from .common import digest, inside, save_json
from .profiles import profile_fingerprint, validate_profile
from .store import normalize_doi

REFERENCE_PATH = Path(__file__).with_name("calibration_reference.json")
DIMENSIONS = ("same_x", "awareness_alignment", "downstream_use", "actual_contrast",
              "informativeness", "source_integration", "statistical_scope")
STATUSES = {"consistent", "material-difference", "unresolved"}
# These are code-owned blanket extraction notices, not reports that a particular
# comparison needs an unavailable source. Other acquisition notes require review.
ROUTINE_ACQUISITION_NOTICES = frozenset({
    "Graphical source pixels have not been supplied; extracted text may omit figure-only evidence.",
    "Supplement inventory has not been independently verified; absence of attached supplements is not evidence none exist.",
})


def source_coverage(paper):
    """Expose explicit coverage facts; never classify scientific gap prose."""
    assessment = paper.get("assessment") or {}
    retrieval = paper.get("retrieval") or {}
    packet = retrieval.get("packet") or {}
    gaps = packet.get("acquisition_gaps", retrieval.get("gaps", [])) or []
    specific_gaps = [gap for gap in gaps if not isinstance(gap, str) or gap not in ROUTINE_ACQUISITION_NOTICES]
    unresolved_assets = retrieval.get("unresolved_assets") or []
    # Supplied unread units establish unfinished reader work, not unavailable
    # evidence. Separate free-text reading gaps can still report missing support;
    # never discard or classify those notes based on the presence of unread units.
    supplied_unread = bool(assessment.get("unread_source_units"))
    reading_gaps = assessment.get("reading_gaps") or []
    inspect_reading_gaps = bool(reading_gaps)
    needs_check = bool(specific_gaps or unresolved_assets or inspect_reading_gaps)
    return {"status": "needs-source-check" if needs_check else "no-specific-acquisition-gap-recorded",
            "acquisition_notes": specific_gaps, "unresolved_asset_count": len(unresolved_assets),
            "reader_gap_notes": reading_gaps if inspect_reading_gaps else [],
            "supplied_unread_units": supplied_unread,
            "reason": "Inspect the reported coverage gap before buying another read of the same packet; the gap text has not been classified as a scientific failure."
            if needs_check else "No specific acquisition gap requires a separate prerequisite; this does not certify completeness of all evidence needed for the comparison."}


def second_read_identity(value):
    """Keep a requested configuration distinct from an agent's self-report."""
    profile = value.get("profile") or {}
    provenance = value.get("execution_provenance") or {}
    verification = value.get("execution_verification") or {}
    status = verification.get("status", "unverified")
    return {"requested_model": profile.get("model"), "requested_effort": profile.get("effort"),
            "reported_harness": provenance.get("harness"), "reported_model": provenance.get("model"),
            "reported_effort": provenance.get("effort"), "worker_context_id": provenance.get("worker_context_id"),
            "verification_status": status, "provider_identity_verified": False,
            "reason": ("The isolated worker self-reports this configuration and source-only context. This is not provider-verified identity."
                       if status == "self-reported-matching-profile" else
                       "The selected execution arguments are bound to the adapter receipt; this does not by itself verify the provider's backend model identity."
                       if status == "adapter-bound-profile" else
                       "Actual worker/model identity is unknown or unverified; the requested profile is not evidence that this model performed the reading.")}


def reference_document():
    value = json.loads(REFERENCE_PATH.read_text(encoding="utf-8"))
    if value.get("schema") != "seed-calibration-reference-v1":
        raise ValueError("Unknown seed calibration reference schema")
    dois = [normalize_doi(case["doi"]) for case in value["cases"]]
    if len(dois) != len(set(dois)) or any(not doi for doi in dois):
        raise ValueError("Calibration reference requires unique DOI identities")
    return value


def reference_for(paper, reference=None):
    if paper.get("seed_role") != "empirical-seed":
        return None
    doi = normalize_doi(paper.get("doi"))
    for case in (reference or reference_document())["cases"]:
        if normalize_doi(case["doi"]) == doi:
            return deepcopy(case)
    return None


def assess(paper, stage=None, result=None, *, reference=None):
    """Compare observable outcomes without classifying scientific prose.

    Passing title/abstract screening is not a scientific pass. Missing or partial
    sources are untested, not a failed experiment or a proven reader-quality error.
    """
    expected = reference_for(paper, reference)
    if expected is None:
        return None
    actual = deepcopy(result if result is not None else paper.get("assessment"))
    stage = stage or ("reader" if actual else "retrieval")
    value = {"paper_id": paper["paper_id"], "seed_id": expected["seed_id"],
             "stage": stage, "reference_sha256": digest(expected),
             "expected": expected, "observed": actual, "needs_review": False,
             "requires_fulltext": False, "flags": [], "semantic_status": "not-compared"}
    if stage in {"title", "abstract", "rescue", "audit"}:
        decision = (actual or {}).get("decision")
        if decision == "exclude":
            value.update(status="screening-disagreement", needs_review=True, requires_fulltext=True,
                         reason="A known relevant empirical seed was excluded before full-text assessment. Preserve that decision and inspect its full text as a separate calibration check.",
                         flags=["seed-screening-exclusion"])
        elif decision in {"retain", "uncertain"}:
            value.update(status="screening-retained", reason="This seed proceeds under ordinary high-recall screening; this is not full-text eligibility.")
        else:
            value.update(status="untested", reason="No usable screening decision is recorded for this seed.")
    elif actual is None:
        missing = paper.get("status", "").startswith("source-")
        value.update(status="untested", reason="Full text is unavailable; reader calibration remains untested, not failed." if missing else "Ordinary seed retrieval or reading has not yet produced an assessment.")
    elif paper.get("assessment_source_generation", paper.get("source_generation", 1)) != paper.get("source_generation", 1):
        value.update(status="untested", needs_review=True, flags=["source-generation-pending"],
                     reason="New source evidence is pending; the earlier seed assessment cannot calibrate the current source generation.")
    elif actual.get("assessment_status") != "complete" or actual.get("source_identity", {}).get("status") != "match" or not actual.get("claims"):
        value.update(status="untested", needs_review=True, flags=["incomplete-source-assessment"],
                     reason="The seed reading is incomplete or its source identity is unresolved. Resolve that execution/source gap before judging scientific agreement.")
    elif expected["expected_paper_decision"] is None:
        value.update(status="no-fixed-outcome", reason="This is an empirical discovery seed without an approved expected disposition. Its source-grounded assessment remains visible without an imposed pass label.")
    elif actual.get("paper_decision") != expected["expected_paper_decision"]:
        value.update(status="disposition-disagreement", needs_review=True, flags=["seed-disposition-disagreement"],
                     reason="The completed reader disposition differs from the approved source-reviewed reference. Review the claims and evidence; neither outcome automatically overrides the other.")
    else:
        value.update(status="disposition-matched", semantic_status="comparison-pending",
                     reason="The paper-level disposition agrees. Claim identity, gate reasoning, source integration and statistical scope still require explicit comparison; label agreement alone is not a semantic pass.")
    return value


def review_route(observation, current_profile, authorized_profiles):
    """Suggest an authorized independent read, never assume a model ranking."""
    if not observation or not observation["needs_review"]:
        return {"action": "none", "reason": "No automatic disagreement flag requires another reader."}
    if observation.get("source_coverage", {}).get("status") in {"needs-source-check", "additional-source-needed", "unresolved"}:
        return {"action": "source-coverage-review", "reason": "Resolve the explicit source-coverage uncertainty first. Another model cannot inspect unavailable evidence in the unchanged packet; a supervisor may clear this prerequisite with a located coverage judgment."}
    for candidate in authorized_profiles:
        profile = validate_profile(candidate)
        if profile.get("authorized") and profile_fingerprint(profile) != profile_fingerprint(validate_profile(current_profile)):
            return {"action": "independent-source-review", "profile": profile,
                    "reason": "Use the explicitly preauthorized alternative on the original sources, without reference answers or prior judgments. Its result remains separate from the first read."}
    return {"action": "flag-for-supervisor", "reason": "No distinct, preauthorized alternative reader is available. Preserve the discrepancy for source-grounded supervisor or user review; do not silently change models or force a label."}


def _seed_papers(c, reference):
    # Eighteen indexed lookups remain cheap when the discovery corpus is large.
    with c.store._connection() as conn:
        papers = []
        for case in reference["cases"]:
            row = conn.execute("SELECT record FROM papers WHERE doi=?", (normalize_doi(case["doi"]),)).fetchone()
            if row:
                paper = json.loads(row[0])
                if paper.get("seed_role") == "empirical-seed":
                    papers.append(paper)
        return papers


def _bindings(c, paper, reference):
    job_id = paper.get("reader_job")
    job = c.store.job(job_id) if job_id else None
    return {"paper_id": paper["paper_id"], "reader_job": job_id,
            "assessment_sha256": digest(paper.get("assessment")),
            "packet_sha256": paper.get("assessment_packet_sha256"),
            "source_generation": paper.get("assessment_source_generation", paper.get("source_generation", 1)),
            "current_source_generation": paper.get("source_generation", 1),
            "profile_sha256": digest(job.get("payload", {}).get("profile", c.plan["profiles"]["reader"])) if job else None,
            "runtime_fingerprint": c.plan.get("runtime_fingerprint"),
            "second_read_sha256": digest(c.store.get_state("seed_calibration_second_read:" + paper["paper_id"])),
            "reference_sha256": digest(reference)}


def _persist_if_changed(store, key, value, reason):
    if store.get_state(key) != value:
        store.set_state(key, value, reason)


def reconcile(c):
    """Cheap idempotent checkpoint; return report and unscheduled review requests.

    The coordinator may retain an excluded seed for *calibration-only* retrieval
    and enqueue a source-only alternative using review_requests. This function
    never enqueues jobs, overwrites screening, or declares scientific completion.
    """
    reference = reference_document()
    cases, requests = [], []
    for paper in _seed_papers(c, reference):
        ref = reference_for(paper, reference)
        observation = assess(paper, reference=reference)
        observation["bindings"] = _bindings(c, paper, ref)
        observation["source_coverage"] = source_coverage(paper)
        current_screen = paper.get("screening_current")
        screens = c.store.get_state("seed_calibration_screening:" + paper["paper_id"], {})
        if current_screen:
            screen = assess(paper, current_screen.get("stage", "title"), current_screen, reference=reference)
            screens = dict(screens, **{current_screen.get("stage", "title"): screen})
            _persist_if_changed(c.store, "seed_calibration_screening:" + paper["paper_id"], screens,
                                "Retain seed screening calibration history separately from current scientific decisions")
        observation["screening"] = screens
        excluded = [item for item in screens.values() if item and item["status"] == "screening-disagreement"]
        if excluded:
            observation["flags"] = sorted(set(observation["flags"] + ["seed-screening-exclusion"]))
            observation["requires_fulltext"] = not bool(paper.get("packet_path"))
            observation["needs_review"] = True
        second = c.store.get_state("seed_calibration_second_read:" + paper["paper_id"])
        if second:
            observation["second_read"] = second
            observation["second_read_identity"] = second_read_identity(second)
            if second.get("packet_sha256") == observation["bindings"]["packet_sha256"] and second.get("assessment"):
                observation["second_read_check"] = assess(paper, "reader", second["assessment"], reference=reference)
        adjudication = c.store.get_state("seed_calibration_adjudication:" + paper["paper_id"])
        if adjudication:
            if adjudication["bindings"] == observation["bindings"]:
                observation["adjudication"] = adjudication
                observation["semantic_status"] = adjudication["resolution"]
                observation["needs_review"] = adjudication["resolution"] == "unresolved"
                coverage = adjudication.get("source_coverage")
                if coverage:
                    observation["source_coverage"] = dict(observation["source_coverage"], status=coverage["status"],
                                                           reviewer_reason=coverage["reason"])
            else:
                observation["stale_adjudication"] = True
                observation["flags"].append("adjudication-binding-changed")
                observation["needs_review"] = True
        alternatives = [c.plan["calibration_review_profile"]] if c.plan.get("calibration_review_profile") else []
        route = review_route(observation, c.plan["profiles"]["reader"], alternatives)
        observation["review_route"] = route
        if observation["needs_review"]:
            requests.append({"request_id": digest([paper["paper_id"], observation["flags"], observation["bindings"]]),
                             "paper_id": paper["paper_id"], "flags": observation["flags"],
                             "requires_fulltext": observation["requires_fulltext"], "bindings": observation["bindings"],
                             "review_route": route})
        _persist_if_changed(c.store, "seed_calibration:" + paper["paper_id"], observation,
                            "Compare ordinary seed results with the versioned reference without changing judgments")
        cases.append(observation)
    missing = sorted(set(case["seed_id"] for case in reference["cases"]) - {case["seed_id"] for case in cases})
    report = {"schema": "seed-calibration-report-v1", "reference_version": reference["version"],
              "reference_sha256": digest(reference), "reference_scope": reference["scope"],
              "counts": {"expected_seeds": len(reference["cases"]), "indexed_seeds": len(cases),
                         "needs_review": sum(case["needs_review"] for case in cases),
                         "untested": sum(case["status"] == "untested" for case in cases),
                         "disposition_matched": sum(case["status"] == "disposition-matched" for case in cases),
                         "semantic_comparison_pending": sum(case["semantic_status"] == "comparison-pending" for case in cases),
                         "semantic_reviewed": sum(case["semantic_status"] in {"consistent-with-reference", "source-supported-departure"} for case in cases)},
              "unindexed_seed_ids": missing, "cases": cases, "review_requests": requests,
              "attention_required": bool(requests), "attention_required_count": len(requests),
              "scientific_certification": False}
    directory = c.run_dir / "calibration"
    path = directory / "seed_report.json"
    if not path.exists() or json.loads(path.read_text()) != report:
        save_json(path, report)
        _write_report(directory / "seed_report.md", report)
    return report


def _write_report(path, report):
    lines = ["# Seed calibration comparison", "", "Expected claims come from the approved source-reviewed baseline. They are withheld from source readers. Differences are review flags, not forced corrections. Paper-level agreement alone does not establish semantic fidelity.", ""]
    for case in report["cases"]:
        expected = case["expected"]
        lines += ["## " + expected["title"], "", "Status: **" + case["status"] + "**; semantic comparison: **" + case["semantic_status"] + "**.", "", case["reason"], ""]
        for n, claim in enumerate(expected["expected_claims"], 1):
            lines += [f"Expected claim {n} ({claim['decision']}): {claim['supported_claim']}", ""]
            lines += [f"- {gate.replace('_', ' ')}: {reason}" for gate, reason in claim["gates"].items()]
            lines += ["", "Scope: " + claim["limitations_and_scope"], ""]
        actual = case.get("observed") or {}
        lines += ["Observed disposition: " + str(actual.get("paper_decision", "not yet read")), ""]
        for n, claim in enumerate(actual.get("claims", []), 1):
            lines += [f"Observed claim {n} ({claim.get('decision')}): {claim.get('supported_claim', '')}", "",
                      "Remaining alternative: " + claim.get("remaining_alternative", ""), ""]
            lines += [f"- {key.replace('_', ' ')}: {claim.get(key, '')}" for key in
                      ("x_and_existence", "awareness_evidence", "downstream_use", "comparison", "contribution_reasoning")]
            lines += [""]
        if case.get("second_read"):
            second = case["second_read"].get("assessment") or {}
            lines += ["Second read: " + str(second.get("paper_decision", "pending")), "",
                      second.get("paper_reason", ""), ""]
            identity = case["second_read_identity"]
            lines += ["Requested model: " + str(identity["requested_model"]) + "; reported model: " + str(identity["reported_model"] or "unknown") +
                      "; execution identity: " + identity["verification_status"] + ".", "", identity["reason"], ""]
        if case.get("adjudication"):
            review = case["adjudication"]
            lines += ["Source-grounded comparison: " + review["resolution"], "", review["reason"], ""]
            lines += [f"- {key.replace('_', ' ')}: {check['status']} — {check['reason']}"
                      for key, check in review["dimensions"].items()]
            lines += [""]
        if case["flags"]:
            lines += ["Review flags: " + ", ".join(case["flags"]), ""]
        if case["source_coverage"]["status"] != "no-specific-acquisition-gap-recorded":
            coverage = case["source_coverage"]
            lines += ["Source coverage: " + coverage["status"], "", coverage.get("reviewer_reason", coverage["reason"]), ""]
    path.write_text("\n".join(lines), encoding="utf-8")


def adjudication_template(c, paper_id):
    return _adjudication_template(c, c.store.paper(paper_id))


def _adjudication_template(c, paper):
    reference = reference_for(paper or {})
    if not reference or not paper.get("assessment"):
        raise ValueError("Seed adjudication requires an ordinary source-reader assessment")
    check = lambda: {"status": "unresolved", "reason": "", "source_locations": []}
    return {"schema": "seed-calibration-adjudication-v1", "bindings": _bindings(c, paper, reference),
            "reviewer": "", "resolution": "unresolved", "reason": "",
            "source_coverage": {"status": "unresolved", "reason": "", "source_locations": []},
            "dimensions": {name: check() for name in DIMENSIONS},
            "expected_claim_checks": [dict(check(), expected_claim_index=i, observed_claim_indices=[])
                                      for i in range(len(reference["expected_claims"]))],
            "additional_claim_checks": []}


def pending_tasks(c):
    """Offer explicit semantic comparisons through the existing agent work lane.

    The task deliberately uses focal_paper_id rather than paper_id: generic
    native leasing then binds the entire comparison, including the expected
    reference and both readings, instead of only the article source identity.
    """
    report = reconcile(c)
    tasks = []
    for case in report["cases"]:
        if not case["expected"]["expected_claims"] or case["semantic_status"] in {"consistent-with-reference", "source-supported-departure"}:
            continue
        first = case.get("observed") or {}
        second = (case.get("second_read") or {}).get("assessment") or {}
        if not first or (not any(read.get("assessment_status") == "complete" and read.get("source_identity", {}).get("status") == "match"
                                for read in (first, second)) and case["source_coverage"]["status"] != "needs-source-check"):
            continue
        paper = c.store.paper(case["paper_id"])
        if not paper.get("packet_path") or paper.get("assessment_source_generation", 1) != paper.get("source_generation", 1):
            continue
        tasks.append({"task": "seed-calibration-comparison", "task_id": "calibration:" + case["paper_id"],
                      "focal_paper_id": case["paper_id"], "bindings": case["bindings"],
                      "expected": case["expected"], "observed": first, "second_read": case.get("second_read"),
                      "source_coverage": case["source_coverage"],
                      "packet_path": paper["packet_path"], "template": adjudication_template(c, case["paper_id"]),
                      "instructions": "First check source coverage: distinguish unavailable main/supplementary/borrowed premise evidence from a reader's failure to use supplied text. Do not infer a weak model from missing evidence. Record source_coverage as sufficient-for-reassessment, additional-source-needed or unresolved with a reason and current source pointers where available; sufficient-for-reassessment clears the prerequisite for an explicitly authorized independent read even when the overall comparison remains unresolved. Then compare each represented claim, all seven semantic dimensions and the approved reference. Expected claims are a comparison baseline, not answers to force. Inspect the original source packet at packet_path within this run; baseline page pointers belong to the baseline version. Supply current asset/unit locations. Preserve a defensible source-supported departure or unresolved gap. A paper-level prospect match alone is insufficient. The optional independent read remains separate from the ordinary assessment; an incomplete ordinary reading cannot become complete just because the independent read matches. Submit the completed template through native-submit for this task, preserving its native lease, or defer with a specific unresolved reason."})
    return tasks


def _validate_adjudication(c, paper_id, review, *, paper=None, historical_bindings=None):
    paper = paper if paper is not None else c.store.paper(paper_id)
    template = _adjudication_template(c, paper)
    if historical_bindings is not None:
        template["bindings"] = historical_bindings
    if set(review) != set(template) or review.get("schema") != template["schema"]:
        raise ValueError("Calibration adjudication does not match its explicit schema")
    if review["bindings"] != template["bindings"]:
        raise ValueError("Calibration adjudication does not bind the current source, result, profile and reference")
    for name in ("reviewer", "reason"):
        if not isinstance(review[name], str) or not review[name].strip():
            raise ValueError("Calibration adjudication requires a nonempty " + name)
    if review["resolution"] not in {"consistent-with-reference", "source-supported-departure", "unresolved"}:
        raise ValueError("Unknown calibration resolution")
    if set(review["dimensions"]) != set(DIMENSIONS):
        raise ValueError("Calibration review must cover every semantic dimension")
    coverage = review["source_coverage"]
    if coverage.get("status") not in {"sufficient-for-reassessment", "additional-source-needed", "unresolved"} or not isinstance(coverage.get("reason"), str) or not coverage["reason"].strip():
        raise ValueError("Calibration source coverage requires an explicit status and reason")
    if review["resolution"] != "unresolved" and coverage["status"] != "sufficient-for-reassessment":
        raise ValueError("Unresolved source coverage cannot certify semantic calibration")
    if review["resolution"] != "unresolved" and (paper["assessment"].get("assessment_status") != "complete"
            or paper["assessment"].get("source_identity", {}).get("status") != "match"
            or template["bindings"]["source_generation"] != template["bindings"]["current_source_generation"]):
        raise ValueError("Incomplete or superseded source reading cannot establish semantic calibration")
    packet = json.loads(inside(c.run_dir / paper["packet_path"], c.run_dir).read_text())
    if digest(packet) != template["bindings"]["packet_sha256"]:
        raise ValueError("Current seed source packet no longer matches its assessment")
    units = {source["asset_id"]: {u["unit_id"] if isinstance(u, dict) else u for u in source["units"]}
             for source in packet["sources"]}
    checks = list(review["dimensions"].values())
    checks.append(dict(coverage, status="consistent" if coverage["status"] == "sufficient-for-reassessment" else "unresolved"))
    expected_checks = review["expected_claim_checks"]
    if not isinstance(expected_checks, list) or sorted(item.get("expected_claim_index", -1) for item in expected_checks) != list(range(len(template["expected_claim_checks"]))):
        raise ValueError("Calibration review must compare every expected claim exactly once")
    represented = set()
    claim_count = len(paper["assessment"].get("claims", []))
    for item in expected_checks:
        indices = item.get("observed_claim_indices")
        if not isinstance(indices, list) or len(indices) != len(set(indices)) or any(type(i) is not int or not 0 <= i < claim_count for i in indices):
            raise ValueError("Calibration expected claim maps to invalid observed claims")
        if not indices and item.get("status") == "consistent":
            raise ValueError("An omitted expected claim cannot be marked consistent")
        represented.update(indices)
    extras = review["additional_claim_checks"]
    if not isinstance(extras, list):
        raise ValueError("Additional claim checks must be a list")
    extra_indices = [item.get("observed_claim_index", -1) for item in extras]
    if len(extra_indices) != len(set(extra_indices)) or set(extra_indices) != set(range(claim_count)) - represented:
        raise ValueError("Calibration review must explicitly assess every additional observed claim")
    checks += expected_checks + extras
    for check in checks:
        if check.get("status") not in STATUSES or not isinstance(check.get("reason"), str) or not check["reason"].strip():
            raise ValueError("Calibration check needs an explicit status and reason")
        locations = check.get("source_locations")
        if not isinstance(locations, list) or check["status"] != "unresolved" and not locations:
            raise ValueError("Resolved calibration checks require current source locations")
        for location in locations:
            asset, ids = location.get("asset_id"), location.get("unit_ids")
            if asset not in units or not isinstance(ids, list) or not ids or not set(ids) <= units[asset] or len(ids) != len(set(ids)):
                raise ValueError("Calibration check refers to a source unit not supplied in this reading")
    statuses = {check["status"] for check in checks}
    if review["resolution"] != "unresolved" and "unresolved" in statuses:
        raise ValueError("Unresolved checks cannot certify semantic calibration")
    if review["resolution"] == "consistent-with-reference" and statuses != {"consistent"}:
        raise ValueError("A material difference cannot be called consistent")
    if review["resolution"] == "source-supported-departure" and "material-difference" not in statuses:
        raise ValueError("A source-supported departure must identify its material difference")


def record_adjudication(c, paper_id, review):
    """Record an explicit comparison, preserving the first and alternative reads.

    A reviewer may find a source-supported departure from the reference; the
    reference is a calibration aid, never a scientific ground-truth override.
    """
    _validate_adjudication(c, paper_id, review)
    c.store.set_state("seed_calibration_adjudication:" + paper_id, deepcopy(review),
                      "Explicit source-grounded comparison with the approved reference; scientific judgments remain unchanged")
    return reconcile(c)


def validate_records(c, conn):
    """Read-only seed evidence checks within the full validator's snapshot.

    Legitimately superseded adjudications remain historical; they must still bind
    their original job/source, and may never masquerade as current semantic passes.
    """
    from . import reading
    view, store = copy(c), copy(c.store)

    @contextmanager
    def connection():
        yield conn

    store._connection = connection
    view.store = store
    prefixes = ("seed_calibration_second_read:", "seed_calibration_adjudication:")
    records = {}
    for prefix in prefixes:
        start = "state:" + prefix
        for row in conn.execute("SELECT key,value FROM meta WHERE key>=? AND key<?", (start, start + "~")):
            records[row["key"][6:]] = json.loads(row["value"])
    latest, historical_second_reads = {}, {}
    wanted_second_hashes = {review.get("bindings", {}).get("second_read_sha256")
                            for key, review in records.items() if key.startswith(prefixes[1])}
    # One audit-log pass, never one corpus-sized pass per seed.
    for row in conn.execute("SELECT payload FROM events WHERE kind='control_updated' ORDER BY id"):
        event = json.loads(row["payload"])
        key = event.get("key", "")
        if key in records:
            latest[key] = event.get("value")
        if key.startswith(prefixes[0]) and digest(event.get("value")) in wanted_second_hashes:
            historical_second_reads[(key[len(prefixes[0]):], digest(event.get("value")))] = event["value"]
    issues = []

    def require(value, message):
        if not value:
            raise ValueError(message)

    def check_second(pid, value):
        job = store.job(value["job_id"])
        require(job and job["stage"] == "reader" and job["state"] == "complete", "Second read does not resolve to a completed reader job")
        payload = job["payload"]
        require(payload.get("calibration_review") is True and payload.get("paper_id") == pid, "Second read does not belong to this seed calibration job")
        require(value["assessment"] == job["result"]["assessment"], "Second read differs from its immutable job result")
        profile = view.plan.get("calibration_review_profile")
        require(profile and profile.get("authorized") and value["profile"] == profile, "Second read does not bind the authorized alternative profile")
        require(payload.get("review_profile_sha256") == profile_fingerprint(profile), "Second-read profile fingerprint differs")
        provenance, verification = value.get("execution_provenance"), value.get("execution_verification")
        require(isinstance(verification, dict), "Second read lacks explicit execution verification status")
        if job["result"].get("receipt"):
            require(provenance is None and verification.get("status") == "adapter-bound-profile"
                    and verification.get("receipt") == job["result"]["receipt"], "Automatic second read does not bind its adapter receipt")
        else:
            from .coordinator import validate_execution_provenance
            require(provenance == job["result"].get("execution_provenance")
                    and verification == job["result"].get("execution_verification"), "Manual second-read identity differs from its submitted provenance")
            require(verification == validate_execution_provenance(profile, provenance, required=True), "Manual second-read provenance/verification disagrees")
        require(value["packet_sha256"] == payload.get("packet_sha256") and value["source_generation"] == payload.get("source_generation"), "Second-read source generation or packet differs")
        packet = json.loads(inside(view.run_dir / payload["packet_path"], view.run_dir).read_text())
        require(digest(packet) == value["packet_sha256"], "Second-read source packet hash changed")
        reading.validate(value["assessment"], packet)

    for key, value in records.items():
        pid = key.split(":", 1)[1]
        try:
            require(latest.get(key) == value, "Calibration state differs from its append-only control history")
            paper = store.paper(pid)
            ref = reference_for(paper or {})
            require(ref is not None, "Calibration record does not refer to a known empirical seed")
            if key.startswith(prefixes[0]):
                check_second(pid, value)
                continue
            bindings = value["bindings"]
            current_bindings = _bindings(view, paper, ref)
            if bindings == current_bindings:
                _validate_adjudication(view, pid, value)
                continue
            # Reconstruct the old reading rather than applying current evidence
            # to an earlier, honestly preserved source-bound review.
            require(set(bindings) == set(current_bindings), "Historical adjudication has malformed bindings")
            require(bindings["paper_id"] == pid and bindings["reference_sha256"] == digest(ref), "Historical adjudication identity/reference differs")
            require(bindings["runtime_fingerprint"] == view.plan.get("runtime_fingerprint"), "Historical adjudication runtime differs from this immutable run")
            job = store.job(bindings["reader_job"])
            require(job and job["state"] == "complete" and job["stage"] == "reader" and job["payload"].get("paper_id") == pid, "Historical adjudication has no completed source reader")
            assessment = job["result"]["assessment"]
            require(digest(assessment) == bindings["assessment_sha256"], "Historical adjudication result hash differs")
            require(job["payload"].get("packet_sha256") == bindings["packet_sha256"] and job["payload"].get("source_generation", 1) == bindings["source_generation"], "Historical adjudication packet/generation differs from its original job")
            require(digest(job["payload"].get("profile", view.plan["profiles"]["reader"])) == bindings["profile_sha256"], "Historical adjudication profile differs")
            if bindings["second_read_sha256"] != digest(None):
                second = historical_second_reads.get((pid, bindings["second_read_sha256"]))
                require(second is not None, "Historical adjudication second read has no recorded source-bound history")
                check_second(pid, second)
            historical_paper = dict(paper, assessment=assessment, reader_job=job["id"],
                packet_path=job["payload"]["packet_path"], assessment_packet_sha256=bindings["packet_sha256"],
                assessment_source_generation=bindings["source_generation"], source_generation=bindings["current_source_generation"])
            _validate_adjudication(view, pid, value, paper=historical_paper, historical_bindings=bindings)
            observation = store.get_state("seed_calibration:" + pid)
            require(not observation or observation.get("bindings") != current_bindings or observation.get("semantic_status") not in {"consistent-with-reference", "source-supported-departure"}, "A stale adjudication is incorrectly presented as a current semantic pass")
        except (ValueError, KeyError, TypeError, AttributeError, IndexError, OSError) as exc:
            issues.append({"code": "seed_calibration_evidence", "entity": key, "reason": str(exc)})
    return issues
