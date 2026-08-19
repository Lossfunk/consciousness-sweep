from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator, FormatChecker, ValidationError


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from derive_outputs import (  # noqa: E402
    awareness_design_eligible,
    constraint_awareness_difference,
    constraint_equivalence_supported,
    constraint_unaware_capacity,
    no_detectable_awareness_difference,
    unresolved_comparison,
)
from calibration_sampling import select_calibration_fulltexts  # noqa: E402
from structured_write import (  # noqa: E402
    allocate_identifier,
    append_jsonl_record,
    doi_resolver_url,
    dry_run_bibliographic_normalization,
    normalize_doi,
    write_csv_record,
)
from query_instruments import (  # noqa: E402
    COMPACT_PROCESS_TERMS,
    RETIRED_COMPACT_PROCESS_TERMS,
    QCAL_MAX_RESULTS_PER_SOURCE_FAMILY,
    PROCESS_MAX_RESULTS_PER_SOURCE_Y,
    ACTIVE_QCAL_SOURCES,
    build_process_variants,
    conservative_instrument_contract,
    process_query_plan,
    render_process_query,
    render_title_abstract_query,
    validate_process_variants,
    validate_rendered_query,
)
from leakage_guard import (  # noqa: E402
    NEUTRAL_EMPIRICAL_SEED_REASON,
    anchor_specific_tool_identifier_errors,
    empirical_seed_errors,
    named_answer_context_errors,
    registered_leakage_errors,
)
from execution_contract import (  # noqa: E402
    completion_errors,
    derived_bundle_status,
    ordered_result_set_sha256,
    reopen_for_blind_discovery,
    reusable_completed_window,
    reusable_evidence_assessment,
    reusable_fulltext_asset,
    route_audit_errors,
    search_window_key,
    semantic_screen_action,
    validate_declared_bundle_status,
    validate_semantic_batch,
)
from validate_run import dependency_errors, evidence_bundle_errors, load_jsonl_rows  # noqa: E402


def schema(name: str) -> dict:
    return json.loads((ROOT / "schemas" / name).read_text(encoding="utf-8"))


def experiment(**updates: object) -> dict:
    row = {
        "comparison_id": "P000001_E01_C01",
        "experiment_id": "P000001_E01",
        "paper_id": "P000001",
        "experiment_label": "Synthetic experiment",
        "X_label": None,
        "X_description": None,
        "awareness_measure": None,
        "awareness_evidence_type": None,
        "objective_visibility_test_informative": None,
        "objective_visibility_test_reason": None,
        "A_code": None,
        "A_reason": None,
        "critical_dependency_status": None,
        "critical_dependency_reason": None,
        "evidence_bundle_ids": [],
        "structural_audit_status": "not-started",
        "awareness_effect_route_status": "not-assessed",
        "awareness_effect_route_reason": None,
        "unaware_capacity_route_status": "not-assessed",
        "unaware_capacity_route_reason": None,
        "null_equivalence_route_status": "not-assessed",
        "null_equivalence_route_reason": None,
        "result_inspection_status": "not-started",
        "result_inspection_reason": None,
        "first_order_measure": None,
        "E_code": None,
        "E_reason": None,
        "E_matching_basis": None,
        "E_equivalence_margin": None,
        "E_equivalence_result": None,
        "E_competing_account": None,
        "E_competing_prediction": None,
        "E_violating_pattern": None,
        "E_same_Y_reason": None,
        "E_diagnostic_source_locations": [],
        "Y_label": None,
        "Y_description": None,
        "Y_structure": None,
        "factorial_Y_reason": None,
        "factorial_component_effects": [],
        "Y_evidence_role": None,
        "F_code": None,
        "F_reason": None,
        "Y_interpretation_clarity": None,
        "mechanistic_interpretation": None,
        "mechanism_clarity": None,
        "critical_comparison": None,
        "unaware_capacity_claim": None,
        "unaware_capacity": None,
        "unaware_capacity_reason": None,
        "unaware_capacity_critical_effect": None,
        "unaware_capacity_stats_status": None,
        "unaware_capacity_stats_reason": None,
        "awareness_effect": None,
        "awareness_effect_reason": None,
        "direction": None,
        "awareness_effect_critical_effect": None,
        "awareness_effect_estimate": None,
        "awareness_effect_estimate_interpretable": None,
        "awareness_effect_stats_status": None,
        "awareness_effect_stats_reason": None,
        "difference_tested": None,
        "null_evidence_strength": None,
        "null_evidence_adequacy": None,
        "null_equivalence_margin": None,
        "null_equivalence_result": None,
        "null_BF01": None,
        "null_CI_region": None,
        "null_CI_entirely_within_region": None,
        "Meyen_role": None,
        "Meyen_applicable": None,
        "Meyen_status": None,
        "Meyen_reason": None,
        "stats_status": None,
        "stats_flags": [],
        "stats_reason": None,
        "constraint_summary": None,
        "source_pages": None,
        "source_figures_tables": None,
        "current_status": "design-coded",
        "notes": None,
    }
    row.update(updates)
    return row


def route_row(**updates: object) -> dict:
    row = {
        "A_code": "A-direct", "E_code": "E-diagnostic", "F_code": "F-meaningful",
        "unaware_capacity_claim": "synthetic downstream use of X",
        "unaware_capacity": "supported", "unaware_capacity_stats_status": "adequate",
        "awareness_effect": "difference-supported", "awareness_effect_stats_status": "adequate",
        "difference_tested": "yes", "null_evidence_adequacy": "not-applicable",
        "Meyen_role": "not-applicable", "Meyen_applicable": "no", "Meyen_status": None,
        "current_status": "fully-evaluated",
    }
    row.update(updates)
    return row


def diagnostic_e(**updates: object) -> dict:
    values = {
        "E_code": "E-diagnostic",
        "E_reason": "A prespecified pattern contradicts the named first-order evidence account.",
        "E_matching_basis": "none",
        "E_competing_account": "Uniform degradation of first-order evidence.",
        "E_competing_prediction": "All components of the same Y weaken monotonically.",
        "E_violating_pattern": "The focal component reverses or dissociates instead of weakening uniformly.",
        "E_same_Y_reason": "All components instantiate the same downstream functional relation.",
        "E_diagnostic_source_locations": ["synthetic factorial result"],
    }
    values.update(updates)
    return values


def validate(name: str, row: dict) -> None:
    Draft202012Validator(schema(name), format_checker=FormatChecker()).validate(row)


def aggregate_hash(directory: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(item for item in directory.rglob("*") if item.is_file()):
        digest.update(path.relative_to(directory).as_posix().encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def paper(**updates: object) -> dict:
    row = {
        "paper_id": "P000001", "title": "Synthetic title", "authors": None,
        "year": 2020, "doi": None, "url": None, "publication_status": "published",
        "first_discovery_route": "independent-query", "first_discovery_parent": None,
        "first_discovery_query_id": "QTEST", "first_search_id": "TEST_S000001",
        "first_seen_wave": 1, "title_screen": "not-screened", "title_screen_reason": None,
        "title_screen_method": "not-screened", "title_screen_rule_id": None,
        "abstract_status": "not-sought", "abstract_screen": "not-screened",
        "abstract_screen_reason": None, "abstract_screen_method": "not-screened",
        "abstract_screen_rule_id": None, "fulltext_priority": "not-assigned",
        "fulltext_priority_reason": None, "fulltext_status": "not-attempted",
        "fulltext_source": None, "missing_text_priority": "none",
        "citation_expansion_status": "not-assessed", "citation_expansion_reason": None,
        "duplicate_of": None, "duplicate_reason": None, "current_status": "encountered",
        "notes": None,
    }
    row.update(updates)
    return row


def decision(decision_id: str, reason: str) -> dict:
    return {
        "decision_id": decision_id, "run_id": "TEST", "timestamp": "2026-08-18T12:00:00Z",
        "entity_type": "run", "entity_id": "TEST", "decision_type": "synthetic",
        "field": "status", "old_value": None, "new_value": "running",
        "reason": reason, "source_location": "synthetic", "agent": "test",
    }


def bundle(**updates: object) -> dict:
    row = {
        "evidence_bundle_id": "TEST_EB000001",
        "focal_comparison_id": "P000001_E01_C01",
        "supported_premise": "awareness-A",
        "premise_description": "The focal masking regime supports the stated A premise.",
        "route_label": "awareness-effect",
        "required_member_keys": ["validation"],
        "bundle_status": "complete",
        "bundle_reason": "Every required direct member supports the premise.",
        "notes": None,
    }
    row.update(updates)
    return row


def evidence_link(**updates: object) -> dict:
    row = {
        "evidence_link_id": "TEST_EL000001",
        "evidence_bundle_id": "TEST_EB000001",
        "member_key": "validation",
        "focal_comparison_id": "P000001_E01_C01",
        "supporting_paper_id": "P000001",
        "supporting_experiment_id": "P000001_E02",
        "supporting_auxiliary_id": None,
        "evidence_assessment_id": None,
        "supporting_source_type": "within-paper-experiment",
        "support_role": "awareness-validation",
        "dependency_role": "required",
        "member_status": "supports",
        "supported_claim": "The masking regime supports the focal A decision.",
        "transfer_reason": "Same population, manipulation, measure, analysis, and article version.",
        "transfer_limitation": None,
        "source_location": "Experiment 2",
        "used_for_decision": True,
        "notes": None,
    }
    row.update(updates)
    return row


class AwarenessRulesTests(unittest.TestCase):
    def test_objective_invisibility_supports_a_direct(self) -> None:
        row = experiment(
            awareness_measure="four-alternative forced-choice direction test",
            awareness_evidence_type="objective-invisibility",
            objective_visibility_test_informative="yes",
            objective_visibility_test_reason="Meaningful 25% chance baseline and repeated trials at the critical regime.",
            A_code="A-direct",
            A_reason="The relevant participants and regime were tested directly.",
            critical_dependency_status="checked-none",
            critical_dependency_reason="No external premise is required.",
        )
        validate("experiments.schema.json", row)

    def test_transferred_objective_invisibility_supports_a_validated(self) -> None:
        row = experiment(
            awareness_measure="separate forced-choice validation",
            awareness_evidence_type="objective-invisibility",
            objective_visibility_test_informative="yes",
            objective_visibility_test_reason="Sensitive chance-baseline test with adequate repeated observations.",
            A_code="A-validated",
            A_reason="Stimulus, timing, task, attention, masking, and population transfer were supported.",
            critical_dependency_status="resolved",
            critical_dependency_reason="A cited validation source was retrieved and assessed.",
        )
        validate("experiments.schema.json", row)
        self.assertTrue(dependency_errors([row], []))
        resolved_bundle = bundle(focal_comparison_id=row["comparison_id"])
        self.assertEqual(dependency_errors([row], [resolved_bundle]), [])

    def test_above_chance_objective_performance_does_not_force_awareness(self) -> None:
        row = experiment(
            awareness_measure="subjective report plus objective discrimination",
            awareness_evidence_type="mixed",
            objective_visibility_test_informative="no",
            objective_visibility_test_reason="Above-chance discrimination informs E, while subjective unawareness independently supports A.",
            A_code="A-direct",
            A_reason="Trialwise subjective unseen reports supply the qualifying direct evidence.",
            critical_dependency_status="checked-none",
            critical_dependency_reason="No critical external premise.",
        )
        validate("experiments.schema.json", row)

    def test_insensitive_objective_test_does_not_support_strong_a(self) -> None:
        for code in ("A-transfer-risk", "A-absent"):
            row = experiment(
                awareness_measure="small underpowered forced-choice test",
                awareness_evidence_type="objective-invisibility",
                objective_visibility_test_informative="no",
                objective_visibility_test_reason="A nonsignificant result from too few trials is insensitive.",
                A_code=code,
                A_reason="The invisibility inference is not sufficiently supported.",
                critical_dependency_status="checked-none",
                critical_dependency_reason="No external premise changes the sensitivity problem.",
            )
            validate("experiments.schema.json", row)
            invalid = dict(row, A_code="A-direct")
            with self.assertRaises(ValidationError):
                validate("experiments.schema.json", invalid)


class FGranularityTests(unittest.TestCase):
    def test_coarse_functional_y_can_have_ambiguous_mechanism(self) -> None:
        row = experiment(
            Y_label="regulation of distractor interference",
            Y_description="Behavioral control of how an irrelevant distractor affects the focal task.",
            Y_evidence_role="downstream-functional-measure",
            F_code="F-meaningful",
            F_reason="The behavioral dependent measure identifies a conservative downstream function.",
            Y_interpretation_clarity="clear",
            mechanistic_interpretation="Active suppression, filtering, or altered capture may implement the function.",
            mechanism_clarity="ambiguous",
            critical_dependency_status="checked-none",
            critical_dependency_reason="No external premise is needed for the synthetic F decision.",
        )
        validate("experiments.schema.json", row)

    def test_true_function_level_ambiguity_is_f_ambiguous(self) -> None:
        row = experiment(
            Y_label="downstream use unresolved",
            Y_description="The measure cannot distinguish updating from action selection.",
            Y_evidence_role="function-level-unresolved",
            F_code="F-ambiguous",
            F_reason="Even a conservative Y requires choosing between substantively different uses.",
            Y_interpretation_clarity="ambiguous",
            mechanistic_interpretation="Not identifiable until the function is resolved.",
            mechanism_clarity="not-assessed",
            critical_dependency_status="checked-none",
            critical_dependency_reason="No external premise is needed for the synthetic F decision.",
        )
        validate("experiments.schema.json", row)

    def test_mechanistic_neural_support_is_not_automatically_y(self) -> None:
        row = experiment(
            Y_label="regional neural difference",
            Y_description="A generic BOLD contrast compatible with a proposed mechanism.",
            Y_evidence_role="mechanistic-support-only",
            F_code="F-meaningful",
            F_reason="Synthetic invalid classification.",
            Y_interpretation_clarity="clear",
            mechanistic_interpretation="The region may participate in inhibitory control.",
            mechanism_clarity="ambiguous",
        )
        with self.assertRaises(ValidationError):
            validate("experiments.schema.json", row)


class ProvenanceSchemaTests(unittest.TestCase):
    def test_auxiliary_source_does_not_create_candidate_paper(self) -> None:
        candidates = [{"paper_id": "P000001", "doi": "10.1/candidate"}]
        auxiliary = {
            "auxiliary_id": "TEST_AUX000001",
            "citation": "Validation source", "doi": "10.1/auxiliary", "url": None,
            "identity_reason": "DOI and citation identify one logical published work.",
            "article_version": "version-of-record",
            "retrieval_status": "unavailable", "local_fulltext_path": None, "file_sha256": None,
            "obtained_at": None, "obtained_by": None, "acquisition_route": None,
            "verification_reason": "Identity verified from the cited DOI; full text unavailable.",
            "notes": None,
        }
        validate("auxiliary_sources.schema.json", auxiliary)
        with self.assertRaises(ValidationError):
            validate("papers.schema.json", auxiliary)
        self.assertEqual(candidates, [{"paper_id": "P000001", "doi": "10.1/candidate"}])

    def test_abstract_unavailable_can_receive_retrieval_priority(self) -> None:
        row = {
            "paper_id": "P000001", "title": "Potentially relevant paper", "authors": None,
            "year": 2001, "doi": None, "url": None, "publication_status": "published",
            "first_discovery_route": "independent-query", "first_discovery_parent": None,
            "first_discovery_query_id": "Q001-OA-PR1", "first_search_id": "TEST_S000001",
            "first_seen_wave": 1, "title_screen": "retain",
            "title_screen_reason": "Title names an awareness contrast and downstream process.",
            "title_screen_method": "agent-semantic", "title_screen_rule_id": None,
            "abstract_status": "unavailable", "abstract_screen": "not-screened",
            "abstract_screen_reason": "No abstract was returned or found.",
            "abstract_screen_method": "not-screened", "abstract_screen_rule_id": None,
            "fulltext_priority": "high",
            "fulltext_priority_reason": "Seed-adjacent title and direct terminology warrant retrieval.",
            "fulltext_status": "not-attempted", "fulltext_source": None,
            "missing_text_priority": "none", "citation_expansion_status": "not-assessed",
            "citation_expansion_reason": None, "duplicate_of": None, "duplicate_reason": None,
            "current_status": "abstract-unavailable", "notes": None,
        }
        validate("papers.schema.json", row)

    def test_obtained_fields_support_agent_and_user_routes(self) -> None:
        for obtained_by, route in (("agent", "publisher-open-access"), ("user", "manual-upload")):
            row = {
                "paper_id": "P000001", "priority": "ask-text-high", "reason": "Needed for classification.",
                "attempted_sources": ["publisher"], "last_attempt_date": "2026-08-18",
                "status": "obtained", "manually_requested": obtained_by == "user",
                "manual_request_wave": 1 if obtained_by == "user" else None,
                "local_fulltext_path": "runs/TEST/fulltexts/P000001.pdf",
                "file_sha256": "a" * 64, "obtained_at": "2026-08-18T12:00:00Z",
                "obtained_wave": 1, "obtained_by": obtained_by, "acquisition_route": route,
                "notes": None,
            }
            validate("missing_texts.schema.json", row)


class StructuredWriteTests(unittest.TestCase):
    def test_malformed_row_fails_before_csv_mutation(self) -> None:
        papers_schema = schema("papers.schema.json")
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "papers_master.csv"
            headers = list(papers_schema["properties"])
            with path.open("w", newline="", encoding="utf-8") as handle:
                csv.writer(handle, lineterminator="\n").writerow(headers)
            before = path.read_bytes()
            with self.assertRaises(ValidationError):
                write_csv_record(path, papers_schema, {"paper_id": "P000001"})
            self.assertEqual(path.read_bytes(), before)

    def test_concurrent_csv_writes_do_not_lose_rows(self) -> None:
        simple_schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object", "additionalProperties": False,
            "required": ["id"], "properties": {"id": {"type": "string"}},
        }
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "items.csv"
            with path.open("w", newline="", encoding="utf-8") as handle:
                csv.writer(handle, lineterminator="\n").writerow(["id"])
            with ThreadPoolExecutor(max_workers=8) as pool:
                list(pool.map(lambda value: write_csv_record(path, simple_schema, {"id": str(value)}), range(40)))
            with path.open(newline="", encoding="utf-8") as handle:
                self.assertEqual(sorted(int(row["id"]) for row in csv.DictReader(handle)), list(range(40)))

    def test_atomic_identifier_allocation_is_unique_under_concurrency(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = Path(temporary)
            (run_dir / "run_state.json").write_text(json.dumps({
                "run_id": "TEST", "next_paper_counter": 1,
                "next_experiment_counters": {}, "next_comparison_counters": {},
                "next_decision_counter": 1, "next_search_counter": 1,
                "next_discovery_counter": 1, "next_auxiliary_counter": 1,
                "next_evidence_link_counter": 1, "next_evidence_bundle_counter": 1,
                "next_evidence_assessment_counter": 1, "next_fulltext_asset_counter": 1,
            }), encoding="utf-8")
            with ThreadPoolExecutor(max_workers=12) as pool:
                identifiers = list(pool.map(lambda _: allocate_identifier(run_dir, "paper"), range(60)))
            self.assertEqual(len(set(identifiers)), 60)
            self.assertEqual(sorted(identifiers), [f"P{value:06d}" for value in range(1, 61)])
            with ThreadPoolExecutor(max_workers=8) as pool:
                experiments = list(pool.map(
                    lambda _: allocate_identifier(run_dir, "experiment", "P000001"), range(20)
                ))
            self.assertEqual(sorted(experiments), [f"P000001_E{value:02d}" for value in range(1, 21)])
            with ThreadPoolExecutor(max_workers=8) as pool:
                comparisons = list(pool.map(
                    lambda _: allocate_identifier(run_dir, "comparison", "P000001_E01"), range(20)
                ))
            self.assertEqual(sorted(comparisons), [f"P000001_E01_C{value:02d}" for value in range(1, 21)])
            state = json.loads((run_dir / "run_state.json").read_text(encoding="utf-8"))
            self.assertEqual(state["next_paper_counter"], 61)
            self.assertEqual(state["next_experiment_counters"]["P000001"], 21)
            self.assertEqual(state["next_comparison_counters"]["P000001_E01"], 21)

    def test_jsonl_escapes_unicode_line_separator_and_uses_physical_records(self) -> None:
        decision_schema = schema("decision_log.schema.json")
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "decision_log.jsonl"
            append_jsonl_record(path, decision_schema, decision("TEST_D000001", "alpha\u2028beta"))
            append_jsonl_record(path, decision_schema, decision("TEST_D000002", "gamma"))
            raw = path.read_bytes()
            self.assertIn(b"\\u2028", raw)
            self.assertEqual(raw.count(b"\n"), 2)
            errors: list[str] = []
            rows = load_jsonl_rows(path, decision_schema, errors)
            self.assertEqual(errors, [])
            self.assertEqual([row["decision_id"] for row in rows], ["TEST_D000001", "TEST_D000002"])

    def test_doi_normalization_and_resolver_encoding(self) -> None:
        raw = " HTTPS://DX.DOI.ORG/10.1002/(SICI)1099-0844(199912)17:4<290::AID-CBF849>3.0.CO;2-P "
        normalized = "10.1002/(sici)1099-0844(199912)17:4<290::aid-cbf849>3.0.co;2-p"
        self.assertEqual(normalize_doi(raw), normalized)
        url = doi_resolver_url(raw)
        self.assertIn("%3C290", url)
        self.assertIn("%3E3.0", url)
        self.assertNotIn("<", url)
        FormatChecker().check(url, "uri")

    def test_doi_url_normalization_dry_run_is_non_mutating(self) -> None:
        records = [{
            "doi": " https://doi.org/10.1002/A<B> ",
            "url": " https://example.org/article path?q=a b ",
        }]
        before = json.loads(json.dumps(records))
        normalized = dry_run_bibliographic_normalization(records)
        self.assertEqual(records, before)
        self.assertEqual(normalized[0]["doi"], "10.1002/a<b>")
        self.assertNotIn("<", normalized[0]["doi_resolver_url"])
        self.assertIn("%20", normalized[0]["url"])

    def test_comparison_requires_preallocated_experiment_group(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = Path(temporary)
            (run_dir / "run_state.json").write_text(json.dumps({
                "run_id": "TEST", "next_paper_counter": 1,
                "next_experiment_counters": {}, "next_comparison_counters": {},
                "next_decision_counter": 1, "next_search_counter": 1,
                "next_discovery_counter": 1, "next_auxiliary_counter": 1,
                "next_evidence_link_counter": 1, "next_evidence_bundle_counter": 1,
                "next_evidence_assessment_counter": 1, "next_fulltext_asset_counter": 1,
            }), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "experiment group"):
                allocate_identifier(run_dir, "comparison", "P000001_E01")
            experiment_id = allocate_identifier(run_dir, "experiment", "P000001")
            self.assertEqual(
                allocate_identifier(run_dir, "comparison", experiment_id),
                "P000001_E01_C01",
            )


class ScreeningContractTests(unittest.TestCase):
    def test_agent_semantic_title_and_abstract_screening(self) -> None:
        row = paper(
            title_screen="retain", title_screen_reason="Semantically plausible X-to-Y design.",
            title_screen_method="agent-semantic", abstract_status="available",
            abstract_screen="screen-out", abstract_screen_reason="The abstract has no awareness contrast.",
            abstract_screen_method="agent-semantic", fulltext_priority="not-assigned",
            current_status="abstract-out",
        )
        validate("papers.schema.json", row)
        with self.assertRaises(ValidationError):
            validate("papers.schema.json", dict(row, abstract_screen_method="lexical-heuristic"))

    def test_deterministic_exclusion_requires_preregistered_rule_id(self) -> None:
        row = paper(
            title_screen="exclude", title_screen_reason="Exact frozen document-type exclusion.",
            title_screen_method="preregistered-deterministic", title_screen_rule_id=None,
            current_status="title-excluded",
        )
        with self.assertRaises(ValidationError):
            validate("papers.schema.json", row)
        validate("papers.schema.json", dict(row, title_screen_rule_id="TITLE-RULE-01"))


class CalibrationSamplingTests(unittest.TestCase):
    def test_calib003_sample_is_priority_then_discovery_then_paper(self) -> None:
        candidates = []
        for value in range(1, 17):
            candidates.append({
                "paper_id": f"P{value:06d}", "newly_discovered": True,
                "abstract_screen": "screen-in",
                "fulltext_priority": "high" if value % 3 else "medium",
                "first_discovery_id": f"CALIB003_R{17 - value:06d}",
                "expected_outcome": "must-not-affect-order" if value % 2 else "different",
            })
        candidates.append({
            "paper_id": "P999999", "newly_discovered": False,
            "abstract_screen": "screen-in", "fulltext_priority": "high",
            "first_discovery_id": "CALIB003_R000001",
        })
        selected = select_calibration_fulltexts(candidates)
        self.assertEqual(len(selected), 12)
        expected = sorted(
            candidates[:16],
            key=lambda row: (
                {"high": 0, "medium": 1, "low": 2}[row["fulltext_priority"]],
                int(row["first_discovery_id"].rsplit("R", 1)[1]), row["paper_id"],
            ),
        )[:12]
        self.assertEqual([row["paper_id"] for row in selected], [row["paper_id"] for row in expected])


class CompatibilityAndDerivedTests(unittest.TestCase):
    def test_historical_calibration_is_refused_without_mutation(self) -> None:
        old_run = ROOT / "runs" / "CALIB_CODEX_001"
        if not old_run.is_dir():
            self.skipTest("historical calibration fixture is not present")
        before = aggregate_hash(old_run)
        result = subprocess.run(
            [
                sys.executable, str(ROOT / "tools" / "validate_run.py"),
                "--run-id", "CALIB_CODEX_001", "--root", str(ROOT),
            ],
            text=True, capture_output=True, check=False,
        )
        self.assertEqual(result.returncode, 3)
        self.assertIn("incompatible run package/schema", result.stderr)
        self.assertEqual(aggregate_hash(old_run), before)

    def test_meyen_role_and_applicability_are_schema_consistent(self) -> None:
        row = experiment(
            Meyen_role="supplementary", Meyen_applicable="yes",
            Meyen_status="Meyen-failed",
            Meyen_reason="Independent A plus E support exists, but indirect-task advantage fails.",
        )
        validate("experiments.schema.json", row)
        with self.assertRaises(ValidationError):
            validate("experiments.schema.json", dict(row, Meyen_applicable="no"))

class ScientificRevisionSyntheticTests(unittest.TestCase):
    """The 18 bounded regression cases required for the draft-0.7 revision."""

    def test_01_capacity_supported_effect_unresolved(self) -> None:
        row = route_row(awareness_effect="unresolved", awareness_effect_stats_status="unclear")
        self.assertTrue(constraint_unaware_capacity(row))
        self.assertFalse(constraint_awareness_difference(row))
        self.assertTrue(unresolved_comparison(row))

    def test_02_capacity_and_difference_overlap(self) -> None:
        row = route_row()
        self.assertTrue(constraint_unaware_capacity(row))
        self.assertTrue(constraint_awareness_difference(row))

    def test_03_capacity_and_no_detectable_difference_overlap(self) -> None:
        row = route_row(
            awareness_effect="no-detectable-difference",
            awareness_effect_stats_status="adequate",
        )
        self.assertTrue(constraint_unaware_capacity(row))
        self.assertTrue(no_detectable_awareness_difference(row))
        self.assertFalse(constraint_equivalence_supported(row))

    def test_04_equivalence_requires_positive_null_evidence(self) -> None:
        row = route_row(
            awareness_effect="equivalence-supported", null_evidence_adequacy="adequate"
        )
        self.assertTrue(constraint_equivalence_supported(row))
        self.assertFalse(constraint_equivalence_supported(dict(row, null_evidence_adequacy="weak")))

    def test_05_bare_nonsignificant_p_cannot_be_equivalence(self) -> None:
        row = experiment(
            awareness_effect="equivalence-supported",
            awareness_effect_reason="No practically important difference is supported.",
            awareness_effect_critical_effect="awareness by function interaction",
            awareness_effect_estimate="interaction p=.60",
            awareness_effect_estimate_interpretable="yes",
            awareness_effect_stats_status="adequate",
            awareness_effect_stats_reason="Synthetic claim.", difference_tested="yes",
            null_evidence_strength="nonsignificant-only", null_evidence_adequacy="weak",
            null_equivalence_result="not-applicable", null_CI_entirely_within_region="not-applicable",
        )
        with self.assertRaises(ValidationError):
            validate("experiments.schema.json", row)

    def test_06_e_not_required_for_capacity_route(self) -> None:
        row = route_row(E_code="E-physical-only", awareness_effect="not-tested")
        self.assertTrue(constraint_unaware_capacity(row))

    def test_07_e_required_for_awareness_difference_route(self) -> None:
        row = route_row(E_code="E-physical-only")
        self.assertFalse(awareness_design_eligible(row))
        self.assertFalse(constraint_awareness_difference(row))

    def test_08_factorial_y_is_one_coherent_comparison(self) -> None:
        components = [
            {"component_id": "relevant-unaware", "X_task_relation": "relevant", "awareness_condition": "unaware", "effect_description": "capture", "statistical_result": "positive", "source_location": "cell 1"},
            {"component_id": "irrelevant-unaware", "X_task_relation": "irrelevant", "awareness_condition": "unaware", "effect_description": "no cost", "statistical_result": "near zero", "source_location": "cell 2"},
        ]
        row = experiment(
            Y_structure="factorial-functional",
            factorial_Y_reason="Task relation changes components of one spatial-control mapping.",
            factorial_component_effects=components,
        )
        validate("experiments.schema.json", row)
        self.assertEqual(row["comparison_id"], "P000001_E01_C01")

    def test_09_distinct_y_relations_require_separate_scalar_rows(self) -> None:
        invalid = experiment(
            Y_structure="scalar",
            factorial_component_effects=[
                {"component_id": "other-y", "X_task_relation": "none", "awareness_condition": "unaware", "effect_description": "different function", "statistical_result": None, "source_location": "cell"}
            ],
        )
        with self.assertRaises(ValidationError):
            validate("experiments.schema.json", invalid)
        first = experiment(Y_structure="scalar", Y_label="response priming")
        second = experiment(
            comparison_id="P000001_E01_C02", Y_structure="scalar", Y_label="memory updating"
        )
        validate("experiments.schema.json", first)
        validate("experiments.schema.json", second)
        self.assertNotEqual(first["comparison_id"], second["comparison_id"])

    def test_10_threshold_relation_can_document_e_diagnostic(self) -> None:
        row = experiment(**diagnostic_e(
            E_competing_account="A monotonic evidence-strength account.",
            E_competing_prediction="The downstream effect shrinks with weaker visibility.",
            E_violating_pattern="The effect appears below the awareness threshold and disappears above it.",
        ))
        validate("experiments.schema.json", row)

    def test_11_sign_reversal_can_document_e_diagnostic(self) -> None:
        row = experiment(**diagnostic_e(
            E_violating_pattern="The same cue relation reverses sign across awareness states."
        ))
        validate("experiments.schema.json", row)

    def test_12_factorial_pattern_can_document_e_diagnostic(self) -> None:
        row = experiment(**diagnostic_e(
            E_violating_pattern="Relevant and irrelevant components cross over across awareness states."
        ))
        validate("experiments.schema.json", row)

    def test_13_unrelated_cross_y_pattern_is_not_documented_e_diagnostic(self) -> None:
        row = experiment(**diagnostic_e(E_same_Y_reason=None))
        with self.assertRaises(ValidationError):
            validate("experiments.schema.json", row)

    def test_14_evidence_bundle_supports_focal_comparison(self) -> None:
        focal = experiment(evidence_bundle_ids=["TEST_EB000001"])
        scientific_bundle = bundle()
        link = evidence_link()
        validate("evidence_bundles.schema.json", scientific_bundle)
        validate("evidence_links.schema.json", link)
        self.assertEqual(
            evidence_bundle_errors([focal], [scientific_bundle], [link], {"P000001"}, set()),
            [],
        )

    def test_15_support_only_experiment_does_not_become_candidate(self) -> None:
        focal = experiment(evidence_bundle_ids=["TEST_EB000001"])
        scientific_bundle = bundle()
        link = evidence_link(
            supporting_experiment_id="P000001_E99",
            support_role="robustness-support",
            supported_claim="A support-only manipulation checks robustness.",
            transfer_reason="Same operational relation and article version.",
            transfer_limitation="Not a candidate X-to-Y comparison.",
        )
        self.assertEqual(
            evidence_bundle_errors([focal], [scientific_bundle], [link], {"P000001"}, set()),
            [],
        )
        self.assertEqual({row["experiment_id"] for row in [focal]}, {"P000001_E01"})

    def test_16_inference_critical_meyen_failure_gates_both_routes(self) -> None:
        row = route_row(Meyen_role="inference-critical", Meyen_applicable="yes", Meyen_status="Meyen-failed")
        self.assertFalse(constraint_unaware_capacity(row))
        self.assertFalse(constraint_awareness_difference(row))

    def test_17_supplementary_meyen_failure_does_not_gate_routes(self) -> None:
        row = route_row(Meyen_role="supplementary", Meyen_applicable="yes", Meyen_status="Meyen-failed")
        self.assertTrue(constraint_unaware_capacity(row))
        self.assertTrue(constraint_awareness_difference(row))

    def test_18_no_detectable_and_equivalence_are_distinct_outputs(self) -> None:
        no_detect = route_row(awareness_effect="no-detectable-difference")
        equivalent = route_row(
            awareness_effect="equivalence-supported", null_evidence_adequacy="adequate"
        )
        self.assertTrue(no_detectable_awareness_difference(no_detect))
        self.assertFalse(constraint_equivalence_supported(no_detect))
        self.assertFalse(no_detectable_awareness_difference(equivalent))
        self.assertTrue(constraint_equivalence_supported(equivalent))


class CapacityIdentityCorrectionTests(unittest.TestCase):
    def test_a_unaware_behavioral_effect_does_not_establish_focal_control(self) -> None:
        row = route_row(
            unaware_capacity_claim="regulation of task-irrelevant distractor interference",
            unaware_capacity="not-supported",
            unaware_capacity_stats_status="adequate",
        )
        self.assertFalse(constraint_unaware_capacity(row))
        self.assertTrue(constraint_awareness_difference(row))

    def test_b_factorial_component_capacity_does_not_transfer_to_awareness_component(self) -> None:
        automatic = route_row(
            unaware_capacity_claim="automatic cue-guided behavioral bias",
            unaware_capacity="supported",
        )
        strategic = dict(
            automatic,
            unaware_capacity_claim="strategic use of the instructed opposite-location rule",
            unaware_capacity="not-supported",
        )
        self.assertTrue(constraint_unaware_capacity(automatic))
        self.assertFalse(constraint_unaware_capacity(strategic))

    def test_c_identical_focal_y_under_unawareness_supports_capacity(self) -> None:
        row = route_row(
            unaware_capacity_claim="orientation-location binding and retrieval"
        )
        self.assertTrue(constraint_unaware_capacity(row))

    def test_d_nonzero_effect_without_named_capacity_is_insufficient(self) -> None:
        row = route_row(unaware_capacity_claim="")
        self.assertFalse(constraint_unaware_capacity(row))
        invalid = experiment(
            unaware_capacity_claim=None,
            unaware_capacity="supported",
            unaware_capacity_reason="A nonzero dependent variable was observed.",
            unaware_capacity_critical_effect="nonzero downstream effect",
            unaware_capacity_stats_status="adequate",
            unaware_capacity_stats_reason="The effect differs from zero.",
        )
        with self.assertRaises(ValidationError):
            validate("experiments.schema.json", invalid)


class QueryInstrumentTests(unittest.TestCase):
    @staticmethod
    def synthetic_variants() -> tuple[dict[str, object], ...]:
        return build_process_variants(
            "context-dependent response selection",
            canonical_rationale="Synthetic conservative Y from the dependent measure.",
            morphology_variants=[{
                "term": "selection of responses depending on context",
                "rationale": "Direct grammatical reordering of the canonical label.",
            }],
            source_terms=[{
                "term": "context-guided response selection",
                "source_pointer": "Synthetic qualifying source, Methods p. 4",
                "rationale": "Same-function terminology used by the qualifying source.",
            }],
            immediate_parent={
                "term": "response selection",
                "frozen_parent_id": "Y-PARENT-RESPONSE-SELECTION",
                "rationale": "One frozen immediate parent, with no neighboring function.",
            },
        )

    def test_compact_queries_parse_on_both_source_renderers(self) -> None:
        documented = (ROOT / "queries.md").read_text(encoding="utf-8")
        for terms in COMPACT_PROCESS_TERMS.values():
            for source in ("OpenAlex", "Europe PMC"):
                rendered = render_title_abstract_query(source, terms)
                validate_rendered_query(source, rendered)
                self.assertNotIn("{{", rendered)
                self.assertIn(rendered, documented)

    def test_runtime_lexical_expansion_is_provenance_backed_and_documented(self) -> None:
        checked = validate_process_variants(self.synthetic_variants())
        self.assertEqual(len(checked), 4)
        documented = (ROOT / "queries.md").read_text(encoding="utf-8")
        for source in ("OpenAlex", "Europe PMC"):
            rendered = render_process_query(source, checked)
            validate_rendered_query(source, rendered)
            self.assertIn(rendered, documented)
            plan = process_query_plan(source, checked)
            self.assertEqual(plan, process_query_plan(source, checked))
            self.assertEqual(plan["canonical_y"], "context-dependent response selection")
            self.assertEqual(plan["max_results"], 50)
            self.assertEqual(plan["max_windows"], 1)
            self.assertEqual(plan["lexical_provenance"], checked)

    def test_unrestricted_semantic_synonym_is_rejected(self) -> None:
        variants = [*self.synthetic_variants(), {
            "term": "executive attention",
            "provenance_category": "llm-semantic-synonym",
            "rationale": "Unrestricted neighboring term.",
        }]
        with self.assertRaisesRegex(ValueError, "unrestricted"):
            validate_process_variants(variants)

    def test_source_term_requires_explicit_pointer(self) -> None:
        with self.assertRaisesRegex(ValueError, "source pointer"):
            build_process_variants(
                "context-dependent response selection",
                canonical_rationale="Synthetic conservative Y.",
                source_terms=[{
                    "term": "context-guided response selection",
                    "rationale": "Purported source term without provenance pointer.",
                }],
            )

    def test_multiple_immediate_parents_are_rejected(self) -> None:
        variants = [*self.synthetic_variants(), {
            "term": "cognitive control",
            "provenance_category": "frozen-immediate-parent",
            "frozen_parent_id": "Y-PARENT-SECOND",
            "rationale": "A prohibited second parent.",
        }]
        with self.assertRaisesRegex(ValueError, "at most one"):
            validate_process_variants(variants)


class RegisteredLeakageGuardTests(unittest.TestCase):
    def test_current_registered_facing_allowlist_passes(self) -> None:
        self.assertEqual(registered_leakage_errors(ROOT), [])

    def test_seed_answer_reason_is_flagged_but_bibliography_is_allowed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "seeds_empirical.csv"
            path.write_text(
                "seed_id,title,authors,year,doi,url,seed_reason,notes\n"
                f"ESEED001,Synthetic title,Sampleanchor A,2020,10.1/example,https://doi.org/10.1/example,{NEUTRAL_EMPIRICAL_SEED_REASON},Bibliographic identity only\n",
                encoding="utf-8",
            )
            self.assertEqual(empirical_seed_errors(path), [])
            path.write_text(
                "seed_id,title,authors,year,doi,url,seed_reason,notes\n"
                "ESEED001,Synthetic title,Sampleanchor A,2020,10.1/example,https://doi.org/10.1/example,Preserved-capacity example,Bibliographic identity only\n",
                encoding="utf-8",
            )
            self.assertTrue(empirical_seed_errors(path))

    def test_anchor_name_alone_is_allowed_but_named_answer_context_is_flagged(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "method.md"
            path.write_text("Sampleanchor et al. (2020) is a frozen bibliographic seed.\n", encoding="utf-8")
            self.assertEqual(named_answer_context_errors(path, ("sampleanchor",)), [])
            path.write_text("Sampleanchor et al. (2020) is expected to be E-diagnostic.\n", encoding="utf-8")
            self.assertTrue(named_answer_context_errors(path, ("sampleanchor",)))

    def test_anchor_specific_runtime_identifier_is_flagged(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "runtime.py"
            path.write_text("SAMPLEANCHOR_VARIANTS = ()\n", encoding="utf-8")
            self.assertTrue(anchor_specific_tool_identifier_errors(path, ("sampleanchor",)))


class ConservativeExecutionTests(unittest.TestCase):
    def test_exact_qcal_and_process_bounds(self) -> None:
        contract = conservative_instrument_contract()
        self.assertEqual(
            contract["active_families"],
            ("QCAL4-ATTN", "QCAL4-META", "QCAL4-BIND", "QCAL4-MEM", "QCAL4-DEC"),
        )
        self.assertEqual(contract["sources"], ("OpenAlex", "Europe PMC"))
        self.assertEqual(ACTIVE_QCAL_SOURCES, ("OpenAlex", "Europe PMC"))
        self.assertEqual(QCAL_MAX_RESULTS_PER_SOURCE_FAMILY, 40)
        self.assertEqual(PROCESS_MAX_RESULTS_PER_SOURCE_Y, 50)
        self.assertEqual(contract["qcal_max_windows_per_source_family"], 1)
        self.assertEqual(contract["process_max_windows_per_source_y"], 1)
        self.assertFalse(contract["redistribute_unused_quota"])
        self.assertTrue(contract["blind_lane_mandatory"])

    def test_pathological_learning_family_is_retired_not_silently_deleted(self) -> None:
        self.assertNotIn("QCAL4-LEARN", COMPACT_PROCESS_TERMS)
        self.assertIn("QCAL4-LEARN", RETIRED_COMPACT_PROCESS_TERMS)
        documented = (ROOT / "queries.md").read_text(encoding="utf-8")
        self.assertIn("QCAL4-LEARN", documented)
        self.assertIn("PRE-FREEZE TODO", documented)

    def test_config_matches_executable_contract(self) -> None:
        config = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))
        blind = config["search"]["conservative_execution"]["supplementary_blind_lane"]
        process = config["search"]["conservative_execution"]["process_trigger"]
        self.assertEqual(blind["active_families"], list(COMPACT_PROCESS_TERMS))
        self.assertEqual(blind["sources"], list(ACTIVE_QCAL_SOURCES))
        self.assertEqual(blind["max_results_per_source_family"], 40)
        self.assertEqual(blind["disabled_families"], ["QCAL4-LEARN"])
        self.assertEqual(process["sources"], list(ACTIVE_QCAL_SOURCES))
        self.assertEqual(process["max_results_per_source_y"], 50)
        self.assertFalse(process["same_normalized_y_retrigger"])
        self.assertTrue(process["genuinely_new_y_recursion_only"])


class WorkflowStateTests(unittest.TestCase):
    @staticmethod
    def state(**updates: object) -> dict:
        value = {
            "workflow_phase": "blind-lane",
            "blind_lane_status": "in-progress",
            "citation_frontier_status": "satisfied",
            "process_frontier_status": "satisfied",
            "activated_normalized_y_labels": [],
        }
        value.update(updates)
        return value

    def test_blind_lane_cannot_be_skipped(self) -> None:
        errors = completion_errors(self.state(workflow_phase="final-validation"))
        self.assertIn("mandatory supplementary blind lane is incomplete", errors)

    def test_blind_new_node_reopens_citation_frontier(self) -> None:
        updated = reopen_for_blind_discovery(self.state(), citation_node=True)
        self.assertEqual(updated["workflow_phase"], "reopened-frontiers")
        self.assertEqual(updated["citation_frontier_status"], "reopened")

    def test_blind_new_y_reopens_process_once(self) -> None:
        updated = reopen_for_blind_discovery(self.state(), genuinely_new_y="distractor control")
        self.assertEqual(updated["process_frontier_status"], "reopened")
        self.assertEqual(updated["activated_normalized_y_labels"], ["distractor control"])
        unchanged = reopen_for_blind_discovery(
            self.state(activated_normalized_y_labels=["distractor control"]),
            genuinely_new_y="distractor control",
        )
        self.assertEqual(unchanged["workflow_phase"], "blind-lane")

    def test_completion_is_blocked_while_a_reopened_frontier_is_open(self) -> None:
        errors = completion_errors(self.state(
            workflow_phase="final-validation", blind_lane_status="complete",
            citation_frontier_status="reopened",
        ))
        self.assertIn("citation frontier is not satisfied", errors)

    def test_complete_state_passes(self) -> None:
        self.assertEqual(completion_errors(self.state(
            workflow_phase="final-validation", blind_lane_status="complete",
        )), [])


class SearchSnapshotTests(unittest.TestCase):
    def test_completed_window_is_reused_by_exact_immutable_key(self) -> None:
        key = search_window_key(
            execution_phase="blind-lane", source="OpenAlex", query_id="QCAL4-ATTN",
            normalized_y_label=None, canonical_query="filter=synthetic",
            source_parameters={"sort": "relevance", "page": 1},
            publication_cutoff="2026-08-19", requested_max_n=40,
        )
        results = [
            {"result_rank": 1, "source_stable_id": "W1", "raw_doi": None,
             "raw_title": "One", "raw_url": "https://example.test/1"},
            {"result_rank": 2, "source_stable_id": "W2", "raw_doi": "10.1/two",
             "raw_title": "Two", "raw_url": "https://example.test/2"},
        ]
        digest = ordered_result_set_sha256(results)
        completed = {"window_key": key, "window_status": "complete", "result_set_sha256": digest}
        self.assertIs(reusable_completed_window([completed], key), completed)
        changed = search_window_key(
            execution_phase="blind-lane", source="OpenAlex", query_id="QCAL4-ATTN",
            normalized_y_label=None, canonical_query="filter=synthetic",
            source_parameters={"sort": "relevance", "page": 1},
            publication_cutoff="2026-08-19", requested_max_n=39,
        )
        self.assertIsNone(reusable_completed_window([completed], changed))

    def test_contradictory_completed_snapshot_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "contradictory"):
            reusable_completed_window([
                {"window_key": "k", "window_status": "complete", "result_set_sha256": "a" * 64},
                {"window_key": "k", "window_status": "complete", "result_set_sha256": "b" * 64},
            ], "k")


class SemanticReuseAndBatchTests(unittest.TestCase):
    def test_rediscovery_reuses_paper_decision_without_rescreen(self) -> None:
        decided = paper(
            title_screen="retain", title_screen_reason="Semantically plausible.",
            title_screen_method="agent-semantic",
        )
        self.assertEqual(semantic_screen_action(decided), "reuse-existing-decision")
        self.assertEqual(
            semantic_screen_action(decided, genuinely_new_evidence=True),
            "revise-with-decision-log",
        )

    def test_title_and_abstract_batches_preserve_individual_decisions_and_whys(self) -> None:
        titles = [paper(
            paper_id=f"P{index:06d}", title_screen="retain",
            title_screen_reason=f"Individual title reason {index}.",
            title_screen_method="agent-semantic",
        ) for index in range(1, 26)]
        validate_semantic_batch("title", titles)
        abstracts = [paper(
            paper_id=f"P{index:06d}", abstract_status="available",
            abstract_screen="screen-in", abstract_screen_reason=f"Individual abstract reason {index}.",
            abstract_screen_method="agent-semantic",
        ) for index in range(1, 11)]
        validate_semantic_batch("abstract", abstracts)
        with self.assertRaisesRegex(ValueError, "1..25"):
            validate_semantic_batch("title", [*titles, paper(paper_id="P000026")])
        with self.assertRaisesRegex(ValueError, "own decision and why"):
            validate_semantic_batch("abstract", [dict(abstracts[0], abstract_screen_reason=None)])

    def test_genuine_revision_remains_append_only_and_logged(self) -> None:
        event = decision("TEST_D000001", "New full-text evidence changes the paper-level screen.")
        event.update({
            "entity_type": "paper", "entity_id": "P000001", "decision_type": "revision",
            "field": "abstract_screen", "old_value": "screen-uncertain", "new_value": "screen-in",
            "source_location": "new full text p. 3",
        })
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "decision_log.jsonl"
            append_jsonl_record(path, schema("decision_log.schema.json"), event)
            self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["old_value"], "screen-uncertain")


class StrictEvidenceBundleTests(unittest.TestCase):
    def test_a_complete_bundle_has_every_required_direct_member(self) -> None:
        links = [evidence_link()]
        self.assertEqual(derived_bundle_status(links, ["validation"]), "complete")
        validate_declared_bundle_status(bundle(), links)

    def test_b_missing_required_manifest_member_is_incomplete(self) -> None:
        links = [evidence_link(member_key="threshold-effect")]
        self.assertEqual(
            derived_bundle_status(links, ["threshold-effect", "threshold-shift"]),
            "incomplete",
        )

    def test_c_unresolved_contradiction_is_conflicted_not_averaged(self) -> None:
        links = [
            evidence_link(member_key="threshold-effect"),
            evidence_link(
                evidence_link_id="TEST_EL000002", member_key="threshold-shift",
                member_status="contradicts",
            ),
        ]
        self.assertEqual(
            derived_bundle_status(links, ["threshold-effect", "threshold-shift"]),
            "conflicted",
        )

    def test_d_e_nonrequired_roles_may_be_absent_or_unavailable(self) -> None:
        required = evidence_link()
        self.assertEqual(derived_bundle_status([required], ["validation"]), "complete")
        for role in ("strengthening", "robustness", "generalization", "mechanistic"):
            optional = evidence_link(
                evidence_link_id=f"TEST_EL{len(role):06d}", member_key=role,
                dependency_role=role, member_status="unavailable", used_for_decision=False,
            )
            self.assertEqual(derived_bundle_status([required, optional], ["validation"]), "complete")

    def test_f_no_transitive_propagation_substitutes_for_a_missing_direct_member(self) -> None:
        direct_first = evidence_link(member_key="exp2-direct")
        chain_only = evidence_link(
            evidence_link_id="TEST_EL000002", member_key="exp3-supports-exp2",
            supporting_experiment_id="P000001_E03", dependency_role="strengthening",
        )
        self.assertEqual(
            derived_bundle_status([direct_first, chain_only], ["exp2-direct", "exp3-direct"]),
            "incomplete",
        )

    def test_g_same_source_two_premises_requires_two_bundles_and_links(self) -> None:
        focal = experiment(evidence_bundle_ids=["TEST_EB000001", "TEST_EB000002"])
        bundles = [bundle(), bundle(
            evidence_bundle_id="TEST_EB000002", supported_premise="meaningful-Y/F",
            premise_description="The same source supports a distinct F premise.",
            required_member_keys=["meaningful-y"],
        )]
        links = [evidence_link(), evidence_link(
            evidence_link_id="TEST_EL000002", evidence_bundle_id="TEST_EB000002",
            member_key="meaningful-y", support_role="other",
            supported_claim="The measure is a downstream functional outcome.",
        )]
        self.assertEqual(
            evidence_bundle_errors([focal], bundles, links, {"P000001"}, set()),
            [],
        )

    def test_i_within_paper_transfer_requires_an_explicit_rationale(self) -> None:
        with self.assertRaises(ValidationError):
            validate("evidence_links.schema.json", evidence_link(transfer_reason=""))

    def test_k_threshold_shift_joint_argument_and_typed_optional_members(self) -> None:
        strongest = bundle(
            supported_premise="E-diagnostic", route_label="awareness-effect",
            required_member_keys=["threshold-linked-effect", "manipulated-threshold-shift"],
            premise_description="A non-monotonic effect follows a manipulated detectability threshold.",
        )
        threshold = evidence_link(
            member_key="threshold-linked-effect", support_role="E-diagnostic-support",
            supported_claim="The interference extremum occurs near the detectability threshold.",
        )
        self.assertEqual(
            derived_bundle_status([threshold], strongest["required_member_keys"]), "incomplete"
        )
        shift = evidence_link(
            evidence_link_id="TEST_EL000002", member_key="manipulated-threshold-shift",
            supporting_experiment_id="P000001_E03", support_role="E-diagnostic-support",
            supported_claim="Changing the visibility regime shifts both threshold and interference extremum.",
        )
        optional = [
            evidence_link(evidence_link_id="TEST_EL000003", member_key="eye-control",
                          supporting_experiment_id="P000001_E04", dependency_role="robustness",
                          support_role="alternative-explanation-control"),
            evidence_link(evidence_link_id="TEST_EL000004", member_key="motion-replication",
                          supporting_experiment_id="P000001_E05", dependency_role="generalization",
                          support_role="generalization-support"),
            evidence_link(evidence_link_id="TEST_EL000005", member_key="neural-mechanism",
                          supporting_experiment_id="P000001_E06", dependency_role="mechanistic",
                          support_role="mechanistic-support"),
        ]
        all_links = [threshold, shift, *optional]
        self.assertEqual(derived_bundle_status(all_links, strongest["required_member_keys"]), "complete")
        validate_declared_bundle_status(strongest, all_links)


class EvidenceAndRetrievalCacheTests(unittest.TestCase):
    def test_j_cached_fact_does_not_propagate_scientific_codes(self) -> None:
        assessment = {
            "evidence_assessment_id": "TEST_EA000001", "source_paper_id": "P000001",
            "source_auxiliary_id": None, "supporting_experiment_id": "P000001_E02",
            "factual_premise": "The visibility test used a four-alternative response.",
            "assessment": "The method reports four response alternatives.",
            "regime_fingerprint": "a" * 64, "source_asset_sha256": "b" * 64,
            "source_location": "Methods p. 2", "assessed_at": "2026-08-19T12:00:00Z",
            "assessor": "test", "notes": None,
        }
        validate("evidence_assessments.schema.json", assessment)
        found = reusable_evidence_assessment(
            [assessment], source_paper_id="P000001", source_auxiliary_id=None,
            factual_premise=assessment["factual_premise"], regime_fingerprint="a" * 64,
            source_asset_sha256="b" * 64, source_location="Methods p. 2",
        )
        self.assertEqual(found, assessment)
        self.assertIsNone(reusable_evidence_assessment(
            [assessment], source_paper_id="P000001", source_auxiliary_id=None,
            factual_premise=assessment["factual_premise"], regime_fingerprint="c" * 64,
            source_asset_sha256="b" * 64, source_location="Methods p. 2",
        ))
        with self.assertRaisesRegex(ValueError, "scientific classifications"):
            reusable_evidence_assessment(
                [dict(assessment, E_code="E-diagnostic")], source_paper_id="P000001",
                source_auxiliary_id=None, factual_premise=assessment["factual_premise"],
                regime_fingerprint="a" * 64, source_asset_sha256="b" * 64,
                source_location="Methods p. 2",
            )

    def test_one_verified_text_and_extraction_serves_multiple_comparisons(self) -> None:
        asset = {
            "fulltext_asset_id": "TEST_FT000001", "paper_id": "P000001",
            "article_version": "version-of-record", "source_identity": "doi:10.1/example",
            "local_fulltext_path": "runs/TEST/fulltexts/P000001.pdf", "file_sha256": "a" * 64,
            "verified_at": "2026-08-19T12:00:00Z", "verification_reason": "Title, DOI, and pagination match.",
            "acquisition_route": "publisher-open-access", "extraction_tool": "pdftotext",
            "extraction_version": "24.02", "extracted_text_path": "runs/TEST/fulltexts/P000001.txt",
            "extracted_text_sha256": "b" * 64, "page_map_path": "runs/TEST/fulltexts/P000001-pages.json",
            "page_map_sha256": "c" * 64, "current_for_paper": True, "notes": None,
        }
        validate("fulltext_assets.schema.json", asset)
        first = reusable_fulltext_asset(
            [asset], paper_id="P000001", article_version="version-of-record",
            extraction_tool="pdftotext", extraction_version="24.02",
        )
        second = reusable_fulltext_asset(
            [asset], paper_id="P000001", article_version="version-of-record",
            extraction_tool="pdftotext", extraction_version="24.02",
        )
        self.assertEqual(first["fulltext_asset_id"], second["fulltext_asset_id"])
        self.assertTrue(first["reuse_extraction"])
        self.assertIsNone(reusable_fulltext_asset(
            [asset], paper_id="P000001", article_version="accepted-manuscript",
        ))

    def test_auxiliary_acquisition_is_reused_but_scientific_links_remain_separate(self) -> None:
        auxiliary = {
            "auxiliary_id": "TEST_AUX000001", "citation": "Reusable source",
            "doi": "10.1/aux", "url": None, "identity_reason": "DOI identity.",
            "article_version": "version-of-record", "retrieval_status": "retrieved",
            "local_fulltext_path": "runs/TEST/fulltexts/AUX.pdf", "file_sha256": "d" * 64,
            "obtained_at": "2026-08-19T12:00:00Z", "obtained_by": "agent",
            "acquisition_route": "repository", "verification_reason": "DOI and title match.",
            "notes": None,
        }
        validate("auxiliary_sources.schema.json", auxiliary)
        links = [evidence_link(
            supporting_paper_id=None, supporting_experiment_id=None,
            supporting_auxiliary_id="TEST_AUX000001", supporting_source_type="external-auxiliary-source",
        ), evidence_link(
            evidence_link_id="TEST_EL000002", evidence_bundle_id="TEST_EB000002",
            member_key="validation-2", focal_comparison_id="P000001_E01_C02",
            supporting_paper_id=None, supporting_experiment_id=None,
            supporting_auxiliary_id="TEST_AUX000001", supporting_source_type="external-auxiliary-source",
        )]
        for link in links:
            validate("evidence_links.schema.json", link)
        self.assertEqual({link["supporting_auxiliary_id"] for link in links}, {"TEST_AUX000001"})
        self.assertEqual(len(links), 2)


class RouteAwareExecutionTests(unittest.TestCase):
    def test_weak_e_closes_effect_route_but_preserves_capacity_inspection(self) -> None:
        row = {
            "A_code": "A-direct", "E_code": "E-physical-only", "F_code": "F-meaningful",
            "structural_audit_status": "complete", "awareness_effect_route_status": "not-viable",
            "unaware_capacity_route_status": "viable", "null_equivalence_route_status": "not-required",
            "unaware_capacity": "supported", "awareness_effect": "not-tested",
            "result_inspection_status": "completed-viable-routes",
        }
        self.assertEqual(route_audit_errors(row), [])

    def test_weak_a_or_f_closes_both_routes_with_explicit_disposition(self) -> None:
        for field, value in (("A_code", "A-absent"), ("F_code", "F-not-meaningful")):
            row = {
                "A_code": "A-direct", "E_code": "E-matched", "F_code": "F-meaningful",
                "structural_audit_status": "complete", "awareness_effect_route_status": "not-viable",
                "unaware_capacity_route_status": "not-viable", "null_equivalence_route_status": "not-required",
                "unaware_capacity": "not-tested", "awareness_effect": "not-tested",
                "result_inspection_status": "not-required",
            }
            row[field] = value
            self.assertEqual(route_audit_errors(row), [])

    def test_irrelevant_null_audit_is_not_required(self) -> None:
        row = {
            "A_code": "A-direct", "E_code": "E-physical-only", "F_code": "F-meaningful",
            "structural_audit_status": "complete", "awareness_effect_route_status": "not-viable",
            "unaware_capacity_route_status": "viable", "null_equivalence_route_status": "not-required",
            "unaware_capacity": "not-supported", "awareness_effect": "not-tested",
            "result_inspection_status": "completed-viable-routes",
        }
        self.assertEqual(route_audit_errors(row), [])

    def test_weak_e_descriptive_no_detectable_result_still_gets_null_audit(self) -> None:
        row = {
            "A_code": "A-validated", "E_code": "E-physical-only", "F_code": "F-meaningful",
            "structural_audit_status": "complete", "awareness_effect_route_status": "not-viable",
            "unaware_capacity_route_status": "viable", "null_equivalence_route_status": "required",
            "unaware_capacity": "supported", "awareness_effect": "no-detectable-difference",
            "result_inspection_status": "completed-viable-routes",
        }
        self.assertEqual(route_audit_errors(row), [])

    def test_route_metadata_does_not_change_derived_output_for_viable_comparison(self) -> None:
        original = route_row()
        audited = dict(original, structural_audit_status="complete",
                       awareness_effect_route_status="viable", unaware_capacity_route_status="viable",
                       null_equivalence_route_status="not-required",
                       result_inspection_status="completed-viable-routes")
        self.assertEqual(constraint_awareness_difference(original), constraint_awareness_difference(audited))
        self.assertEqual(constraint_unaware_capacity(original), constraint_unaware_capacity(audited))
        self.assertEqual(constraint_equivalence_supported(original), constraint_equivalence_supported(audited))


class SyntheticLifecycleTests(unittest.TestCase):
    def test_clean_init_write_derive_validate_resume_and_retired_id_recovery(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            runs_root = Path(temporary) / "runs"
            run_id = "SYNTH_DRAFT08"
            common = ["--root", str(ROOT), "--runs-root", str(runs_root)]
            start = subprocess.run([
                sys.executable, str(ROOT / "tools" / "init_run.py"), "--run-id", run_id,
                "--run-mode", "start", "--agent-harness", "unit-test", "--allow-pre-freeze", *common,
            ], text=True, capture_output=True, check=False)
            self.assertEqual(start.returncode, 0, start.stderr)
            run_dir = runs_root / run_id
            allocated = allocate_identifier(run_dir, "paper")
            self.assertEqual(allocated, "P000001")
            write_csv_record(
                run_dir / "papers_master.csv", schema("papers.schema.json"),
                paper(paper_id=allocated, first_discovery_route="empirical-seed",
                      first_discovery_query_id=None, first_search_id=None),
                key_field="paper_id",
            )
            retired = allocate_identifier(run_dir, "paper")
            self.assertEqual(retired, "P000002")
            derive = subprocess.run([
                sys.executable, str(ROOT / "tools" / "derive_outputs.py"), "--run-id", run_id, *common,
            ], text=True, capture_output=True, check=False)
            self.assertEqual(derive.returncode, 0, derive.stderr)
            checked = subprocess.run([
                sys.executable, str(ROOT / "tools" / "validate_run.py"), "--run-id", run_id, *common,
            ], text=True, capture_output=True, check=False)
            self.assertEqual(checked.returncode, 0, checked.stderr)
            resume = subprocess.run([
                sys.executable, str(ROOT / "tools" / "init_run.py"), "--run-id", run_id,
                "--run-mode", "resume", "--agent-harness", "unit-test", "--allow-pre-freeze", *common,
            ], text=True, capture_output=True, check=False)
            self.assertEqual(resume.returncode, 0, resume.stderr)
            self.assertEqual(allocate_identifier(run_dir, "paper"), "P000003")


if __name__ == "__main__":
    unittest.main()
