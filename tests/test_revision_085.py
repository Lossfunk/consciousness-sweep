from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, ValidationError


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tests"))

from execution_contract import (  # noqa: E402
    awareness_result_provenance_errors,
    capacity_identity_errors,
    experiment_group_errors,
    route_audit_errors,
)
from test_pipeline import experiment, validate  # noqa: E402


FOCAL = "P000001_E01_C01"


def group(**updates: object) -> dict[str, object]:
    row: dict[str, object] = {
        "experiment_id": "P000001_E01",
        "paper_id": "P000001",
        "experiment_label": "Experiment 1",
        "source_location": "Article, Experiment 1",
        "physical_experiment_description": "One physical experiment group.",
        "pre_atomization_assessed": True,
        "citation_specific_x": "not-assessed",
        "citation_awareness_attempt": "not-assessed",
        "citation_functional_y": "not-assessed",
        "bridge_near_neighbor": "not-assessed",
        "bridge_disposition": "not-assessed",
        "bridge_failed_ingredient": "not-applicable",
        "bridge_rationale": None,
        "functional_structure_assessment": "not-applicable",
        "functional_structure_reason": "No atomization is needed.",
        "disposition": "support-only",
        "disposition_reason": "The experiment supports another comparison but does not answer its own X-to-Y question.",
        "linked_comparison_ids": [],
        "support_roles": ["awareness-validation"],
        "notes": None,
    }
    row.update(updates)
    return row


def awareness_row(**updates: object) -> dict[str, object]:
    row: dict[str, object] = {
        "comparison_id": FOCAL,
        "experiment_id": "P000001_E01",
        "A_code": "A-direct",
        "awareness_measure": "objective discrimination",
        "awareness_procedure_type": "direction-identification",
        "awareness_result_reporting": "reported",
        "awareness_result_support": "supports-strong-A",
        "awareness_result_procedure_type": "direction-identification",
        "awareness_result_description": "The focal sample met the registered awareness criterion.",
        "awareness_result_source_location": "Results, p. 4",
        "awareness_result_source_experiment_id": "P000001_E01",
    }
    row.update(updates)
    return row


def transferred_bundle() -> dict[str, object]:
    return {
        "evidence_bundle_id": "TEST_EB000001",
        "focal_comparison_id": FOCAL,
        "supported_premise": "awareness-A",
        "bundle_status": "complete",
    }


def transferred_link() -> dict[str, object]:
    return {
        "evidence_bundle_id": "TEST_EB000001",
        "support_role": "awareness-validation",
        "evidence_content_type": "critical-result",
        "dependency_role": "required",
        "member_status": "supports",
        "used_for_decision": True,
        "supporting_experiment_id": "P000001_E02",
        "supporting_auxiliary_id": None,
        "source_location": "Results, Experiment 2",
        "transfer_reason": "The focal and validation regimes match on the decision-relevant dimensions.",
        "transfer_limitation": "The result came from a separate physical experiment and is transferred explicitly.",
    }


class PhysicalExperimentGroupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        schema = json.loads((ROOT / "schemas" / "experiment_groups.schema.json").read_text())
        cls.validator = Draft202012Validator(schema)

    def test_support_only_group_is_first_class_without_placeholder_comparison(self) -> None:
        self.assertEqual(list(self.validator.iter_errors(group())), [])

    def test_support_only_group_rejects_placeholder_comparison(self) -> None:
        invalid = group(linked_comparison_ids=[FOCAL])
        self.assertTrue(list(self.validator.iter_errors(invalid)))

    def test_comparison_bearing_group_reconciles_one_or_more_comparisons(self) -> None:
        comparison = {"experiment_id": "P000001_E01", "comparison_id": FOCAL}
        candidate = group(
            disposition="comparison-bearing",
            disposition_reason="The experiment yields a qualifying comparison.",
            linked_comparison_ids=[FOCAL], support_roles=[],
        )
        self.assertEqual(experiment_group_errors([candidate], [comparison], {"P000001"}), [])

    def test_no_qualifying_group_needs_no_dummy_comparison(self) -> None:
        candidate = group(
            disposition="no-qualifying-comparison",
            disposition_reason="The experiment contains no distinct downstream X-to-Y comparison.",
            support_roles=[],
        )
        self.assertEqual(experiment_group_errors([candidate], [], {"P000001"}), [])

    def test_comparison_missing_physical_group_is_rejected(self) -> None:
        comparison = {"experiment_id": "P000001_E01", "comparison_id": FOCAL}
        self.assertTrue(experiment_group_errors([], [comparison], {"P000001"}))


class AwarenessReportingSupportTests(unittest.TestCase):
    def test_reported_supportive_focal_result_allows_direct_a(self) -> None:
        self.assertEqual(awareness_result_provenance_errors(awareness_row(), [], []), [])

    def test_methods_only_statement_cannot_support_direct_a(self) -> None:
        row = awareness_row(
            awareness_result_reporting="not-reported",
            awareness_result_support="not-applicable",
            awareness_result_procedure_type="not-applicable",
            awareness_result_description=None,
            awareness_result_source_location=None,
            awareness_result_source_experiment_id=None,
        )
        self.assertTrue(awareness_result_provenance_errors(row, [], []))

    def test_not_reported_cannot_claim_support(self) -> None:
        row = awareness_row(
            awareness_result_reporting="not-reported",
            awareness_result_support="supports-strong-A",
        )
        self.assertTrue(awareness_result_provenance_errors(row, [], []))
        schema_row = experiment(
            A_code="A-direct", A_reason="Synthetic strong-A claim.",
            awareness_measure="objective discrimination",
            awareness_evidence_type="objective-invisibility",
            objective_visibility_test_informative="yes",
            objective_visibility_test_reason="The synthetic test is sensitive.",
            awareness_procedure_type="direction-identification",
            awareness_result_reporting="not-reported",
            awareness_result_support="supports-strong-A",
            awareness_result_procedure_type="not-applicable",
            awareness_result_description=None,
            awareness_result_source_location=None,
            awareness_result_source_experiment_id=None,
        )
        with self.assertRaises(ValidationError):
            validate("experiments.schema.json", schema_row)

    def test_explicit_complete_transfer_allows_validated_a(self) -> None:
        row = awareness_row(
            A_code="A-validated",
            awareness_result_reporting="not-reported",
            awareness_result_support="not-applicable",
            awareness_result_procedure_type="not-applicable",
            awareness_result_description=None,
            awareness_result_source_location=None,
            awareness_result_source_experiment_id=None,
        )
        self.assertEqual(
            awareness_result_provenance_errors(row, [transferred_bundle()], [transferred_link()]),
            [],
        )

    def test_transferred_result_cannot_masquerade_as_focal_reporting(self) -> None:
        row = awareness_row(
            A_code="A-validated",
            awareness_result_source_experiment_id="P000001_E02",
        )
        self.assertTrue(awareness_result_provenance_errors(row, [], []))

    def test_missing_focal_result_location_prohibits_strong_a(self) -> None:
        self.assertTrue(
            awareness_result_provenance_errors(
                awareness_row(awareness_result_source_location=None), [], []
            )
        )


class DirectDifferenceProvenanceTests(unittest.TestCase):
    def row(self, **updates: object) -> dict[str, object]:
        row: dict[str, object] = {
            "experiment_id": "P000001_E01",
            "A_code": "A-direct", "E_code": "E-diagnostic", "F_code": "F-meaningful",
            "structural_audit_status": "complete",
            "awareness_effect_route_status": "viable",
            "unaware_capacity_route_status": "viable",
            "null_equivalence_route_status": "not-required",
            "unaware_capacity": "supported",
            "awareness_effect": "difference-supported",
            "difference_tested": "yes",
            "difference_source_experiment_id": "P000001_E01",
            "difference_source_location": "Results, Experiment 1",
            "difference_statistic_or_test": "awareness-by-X interaction",
            "result_inspection_status": "completed-viable-routes",
            "awareness_effect_critical_effect": "Direct focal interaction.",
            "awareness_effect_estimate": "interaction estimate = 1 synthetic unit",
            "awareness_effect_estimate_interpretable": "yes",
            "awareness_effect_stats_status": "adequate",
            "awareness_effect_stats_reason": "The direct test and estimate were reported.",
        }
        row.update(updates)
        return row

    def test_same_experiment_direct_difference_has_complete_provenance(self) -> None:
        self.assertEqual(route_audit_errors(self.row()), [])

    def test_cross_experiment_difference_cannot_be_marked_direct(self) -> None:
        errors = route_audit_errors(
            self.row(difference_source_experiment_id="P000001_E02")
        )
        self.assertTrue(any("focal experiment" in error for error in errors))

    def test_missing_statistic_or_test_is_rejected(self) -> None:
        errors = route_audit_errors(self.row(difference_statistic_or_test=None))
        self.assertTrue(any("difference_statistic_or_test" in error for error in errors))

    def test_strong_e_without_focal_test_cannot_be_difference_supported(self) -> None:
        errors = route_audit_errors(
            self.row(
                difference_tested="no",
                difference_source_experiment_id=None,
                difference_source_location=None,
                difference_statistic_or_test=None,
            )
        )
        self.assertTrue(any("conclusive awareness-comparison" in error for error in errors))

    def test_focal_descriptive_null_remains_available_with_weak_e(self) -> None:
        row = self.row(
            E_code="E-physical-only",
            awareness_effect_route_status="not-viable",
            awareness_effect="no-detectable-difference",
            null_equivalence_route_status="required",
        )
        self.assertEqual(route_audit_errors(row), [])


class FunctionalYSemanticGuardrailTests(unittest.TestCase):
    def test_effect_on_reaction_time_is_not_meaningful_by_label_alone(self) -> None:
        row = experiment(
            F_code="F-meaningful", F_reason="A nonzero RT effect was observed.",
            Y_label="effect on reaction time", Y_functional_status="effect-only",
            Y_functional_reason="Only the effect metric is named.",
            Y_evidence_role="downstream-functional-measure", Y_interpretation_clarity="clear",
        )
        with self.assertRaises(ValidationError):
            validate("experiments.schema.json", row)

    def test_uncertain_function_remains_f_ambiguous(self) -> None:
        row = experiment(
            F_code="F-ambiguous", F_reason="The downstream consequence is real but its function is unresolved.",
            Y_label="task performance modulation", Y_functional_status="function-unclear",
            Y_functional_reason="Multiple substantively different downstream functions remain viable.",
            Y_evidence_role="function-level-unresolved", Y_interpretation_clarity="ambiguous",
        )
        validate("experiments.schema.json", row)

    def test_generic_neural_difference_is_not_meaningful_y(self) -> None:
        row = experiment(
            F_code="F-not-meaningful", F_reason="Only a generic neural difference is reported.",
            Y_label="neural amplitude difference", Y_functional_status="effect-only",
            Y_functional_reason="No downstream operation is identified.",
            Y_evidence_role="direct-registration-only", Y_interpretation_clarity="unclear",
        )
        validate("experiments.schema.json", row)

    def test_justified_factorial_mapping_can_remain_meaningful(self) -> None:
        row = experiment(
            F_code="F-meaningful", F_reason="The cells jointly operationalize one task-state mapping.",
            Y_label="conditional selection mapping", Y_functional_status="coherent-functional-mapping",
            Y_functional_reason="The preregistered interaction tests one common input-to-output relation.",
            Y_evidence_role="downstream-functional-measure", Y_interpretation_clarity="clear",
        )
        validate("experiments.schema.json", row)

    def test_effect_label_cannot_become_supported_capacity(self) -> None:
        row = {
            "Y_label": "interference effect",
            "Y_functional_status": "effect-only",
            "unaware_capacity_claim": "interference effect",
            "unaware_capacity_evidence_scope": "whole-focal-Y",
            "unaware_capacity": "supported",
        }
        self.assertTrue(capacity_identity_errors(row))

    def test_named_downstream_function_can_be_supported_capacity(self) -> None:
        row = {
            "Y_label": "selection of the task-relevant digit",
            "Y_functional_status": "downstream-function",
            "unaware_capacity_claim": "selection of the task-relevant digit",
            "unaware_capacity_evidence_scope": "whole-focal-Y",
            "unaware_capacity": "supported",
        }
        self.assertEqual(capacity_identity_errors(row), [])


if __name__ == "__main__":
    unittest.main()
