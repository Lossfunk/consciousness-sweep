from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker, ValidationError


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from derive_outputs import (  # noqa: E402
    constraint_awareness_difference,
    constraint_preserved_capacity,
    design_eligible,
)
from structured_write import write_csv_record  # noqa: E402
from validate_run import dependency_errors  # noqa: E402


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
        "F_code": None,
        "F_reason": None,
        "Y_interpretation_clarity": None,
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
            "abstract_status": "unavailable", "abstract_screen": "not-screened",
            "abstract_screen_reason": "No abstract was returned or found.",
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
