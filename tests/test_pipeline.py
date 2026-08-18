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

from jsonschema import Draft202012Validator, FormatChecker, ValidationError


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from derive_outputs import (  # noqa: E402
    constraint_awareness_difference,
    constraint_preserved_capacity,
    design_eligible,
)
from calibration_sampling import select_calibration_fulltexts  # noqa: E402
from structured_write import (  # noqa: E402
    allocate_identifier,
    append_jsonl_record,
    doi_resolver_url,
    normalize_doi,
    write_csv_record,
)
from validate_run import dependency_errors, load_jsonl_rows  # noqa: E402


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
        "first_order_measure": None,
        "E_code": None,
        "E_reason": None,
        "E_matching_basis": None,
        "E_equivalence_margin": None,
        "E_equivalence_result": None,
        "Y_label": None,
        "Y_description": None,
        "Y_evidence_role": None,
        "F_code": None,
        "F_reason": None,
        "Y_interpretation_clarity": None,
        "mechanistic_interpretation": None,
        "mechanism_clarity": None,
        "critical_comparison": None,
        "outcome": None,
        "outcome_reason": None,
        "direction": None,
        "critical_effect": None,
        "unaware_Y_evidence": None,
        "difference_tested": None,
        "null_evidence_strength": None,
        "null_evidence_adequacy": None,
        "null_equivalence_margin": None,
        "null_equivalence_result": None,
        "null_BF01": None,
        "null_CI_region": None,
        "null_CI_entirely_within_region": None,
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
        auxiliary = {
            "target_comparison_id": row["comparison_id"],
            "used_for_decision": True,
            "retrieval_status": "retrieved",
        }
        self.assertEqual(dependency_errors([row], [auxiliary]), [])

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
            "auxiliary_id": "TEST_AUX000001", "target_paper_id": "P000001",
            "target_comparison_id": "P000001_E01_C01", "purpose": "awareness-validation",
            "citation": "Validation source", "doi": "10.1/auxiliary", "url": None,
            "retrieval_status": "unavailable", "local_fulltext_path": None, "file_sha256": None,
            "obtained_at": None, "obtained_by": None, "acquisition_route": None,
            "source_location": "candidate p. 2", "transfer_assessment": "unresolved",
            "transfer_reason": "The source could not be obtained.", "used_for_decision": False,
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

    def test_existing_derived_output_rules_are_unchanged(self) -> None:
        awareness = {
            "A_code": "A-direct", "E_code": "E-diagnostic", "F_code": "F-meaningful",
            "outcome": "awareness-linked-difference", "stats_status": "adequate",
            "difference_tested": "yes", "Meyen_applicable": "no", "Meyen_status": None,
            "unaware_Y_evidence": "not-applicable", "null_evidence_adequacy": "not-applicable",
        }
        preserved = dict(
            awareness,
            outcome="preserved-capacity",
            unaware_Y_evidence="positive",
            null_evidence_adequacy="adequate",
        )
        self.assertTrue(design_eligible(awareness))
        self.assertTrue(constraint_awareness_difference(awareness))
        self.assertFalse(constraint_preserved_capacity(awareness))
        self.assertTrue(constraint_preserved_capacity(preserved))


if __name__ == "__main__":
    unittest.main()
