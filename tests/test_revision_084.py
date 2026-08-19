from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from execution_contract import (  # noqa: E402
    alternative_control_scan_errors,
    awareness_result_provenance_errors,
    contrast_integrity_alternative_is_gating,
    contrast_integrity_bundle_errors,
    e_diagnostic_same_y_bundle_errors,
    validate_run_id_namespace,
)


FOCAL = "P000001_E01_C01"


def e_row(**updates: object) -> dict[str, object]:
    row: dict[str, object] = {
        "comparison_id": FOCAL,
        "experiment_id": "P000001_E01",
        "E_code": "E-diagnostic",
        "current_status": "fully-evaluated",
        "alternative_control_scan_status": "completed-none-found",
        "alternative_control_scan_reason": "The entire synthetic article was semantically scanned.",
    }
    row.update(updates)
    return row


def e_bundle(
    *, anchor: str = "none", resolution: str = "not-applicable", status: str = "complete",
) -> dict[str, object]:
    return {
        "evidence_bundle_id": "TEST_EB000001",
        "focal_comparison_id": FOCAL,
        "supported_premise": "E-diagnostic",
        "required_member_keys": ["control"],
        "bundle_status": status,
        "contrast_integrity_alternative": None if resolution == "not-applicable" else "finite policy state",
        "contrast_integrity_anchor_type": anchor,
        "contrast_integrity_anchor_source_location": None if anchor == "none" else "synthetic design/result",
        "contrast_integrity_viability_reason": None if resolution == "not-applicable" else "The state can determine the focal Y.",
        "contrast_integrity_prediction": None if resolution == "not-applicable" else "The policy predicts the focal mapping.",
        "contrast_integrity_control_member_key": None if resolution == "not-applicable" else "control",
        "contrast_integrity_resolution": resolution,
    }


def e_link(*, same_y: str = "yes", status: str = "supports") -> dict[str, object]:
    return {
        "evidence_bundle_id": "TEST_EB000001",
        "member_key": "control",
        "support_role": "alternative-explanation-control",
        "dependency_role": "required",
        "member_status": status,
        "used_for_decision": status == "supports",
        "same_focal_Y_status": same_y,
        "supported_claim": "The control directly tests the quantitative account for the focal mapping.",
    }


def a_row(**updates: object) -> dict[str, object]:
    row: dict[str, object] = {
        "comparison_id": FOCAL,
        "experiment_id": "P000001_E01",
        "A_code": "A-direct",
        "awareness_measure": "two-alternative direction identification",
        "awareness_procedure_type": "direction-identification",
        "awareness_result_reporting": "reported",
        "awareness_result_support": "supports-strong-A",
        "awareness_result_procedure_type": "direction-identification",
        "awareness_result_description": "Performance at the focal regime met the stated objective-invisibility criterion.",
        "awareness_result_source_location": "Results, synthetic Figure 1",
        "awareness_result_source_experiment_id": "P000001_E01",
    }
    row.update(updates)
    return row


def a_bundle(*, status: str = "complete") -> dict[str, object]:
    return {
        "evidence_bundle_id": "TEST_EB000002",
        "focal_comparison_id": FOCAL,
        "supported_premise": "awareness-A",
        "bundle_status": status,
    }


def a_link(
    *, content: str = "critical-result", member_status: str = "supports",
    source_type: str = "within-paper-experiment",
) -> dict[str, object]:
    return {
        "evidence_bundle_id": "TEST_EB000002",
        "support_role": "awareness-validation",
        "supporting_experiment_id": "P000001_E02",
        "supporting_auxiliary_id": None,
        "evidence_content_type": content,
        "dependency_role": "required",
        "member_status": member_status,
        "used_for_decision": member_status == "supports",
        "source_location": "Supplement, synthetic Figure S1",
        "transfer_reason": "Population, stimulus, suppression, timing, task, environment, procedure, and evidence regime were compared.",
        "transfer_limitation": "The validation occurred in a separate block; this difference was assessed and does not lower awareness relative to the focal task.",
        "supporting_source_type": source_type,
    }


class EvidentialAnchorTests(unittest.TestCase):
    def test_measured_policy_difference_is_gating(self) -> None:
        self.assertTrue(contrast_integrity_alternative_is_gating("directly-measured-difference"))

    def test_instruction_or_mapping_difference_is_gating(self) -> None:
        self.assertTrue(contrast_integrity_alternative_is_gating("design-imposed-difference"))

    def test_behavioral_contingency_evidence_is_gating(self) -> None:
        self.assertTrue(contrast_integrity_alternative_is_gating("reported-behavioral-evidence"))

    def test_unmeasured_attention_cannot_veto(self) -> None:
        self.assertFalse(contrast_integrity_alternative_is_gating("none"))
        self.assertEqual(contrast_integrity_bundle_errors(e_row(), [e_bundle()], [e_link()]), [])

    def test_post_hoc_latent_process_cannot_veto(self) -> None:
        self.assertFalse(contrast_integrity_alternative_is_gating(None))

    def test_unequal_first_order_evidence_alone_does_not_block(self) -> None:
        self.assertEqual(contrast_integrity_bundle_errors(e_row(), [e_bundle()], [e_link()]), [])

    def test_anchored_unresolved_policy_state_blocks(self) -> None:
        bundle = e_bundle(anchor="design-imposed-difference", resolution="unresolved")
        self.assertTrue(contrast_integrity_bundle_errors(e_row(), [bundle], [e_link()]))


class WithinPaperScanTests(unittest.TestCase):
    def test_explicit_control_must_be_evaluated_before_final_e(self) -> None:
        row = e_row(alternative_control_scan_status="incomplete-source-missing")
        self.assertTrue(alternative_control_scan_errors(row))

    def test_same_y_control_may_complete_e_bundle(self) -> None:
        row = e_row(alternative_control_scan_status="completed-candidate-evaluated")
        self.assertEqual(e_diagnostic_same_y_bundle_errors(row, [e_bundle()], [e_link()]), [])

    def test_different_y_control_cannot_support_focal_e(self) -> None:
        self.assertTrue(e_diagnostic_same_y_bundle_errors(e_row(), [e_bundle()], [e_link(same_y="no")]))

    def test_unavailable_control_keeps_bundle_incomplete(self) -> None:
        row = e_row(alternative_control_scan_status="incomplete-source-missing")
        self.assertTrue(alternative_control_scan_errors(row))
        self.assertTrue(e_diagnostic_same_y_bundle_errors(row, [e_bundle(status="incomplete")], [e_link(status="unavailable")]))

    def test_no_relevant_control_is_a_completed_scan(self) -> None:
        self.assertEqual(alternative_control_scan_errors(e_row()), [])


class AwarenessResultProvenanceTests(unittest.TestCase):
    def test_same_experiment_procedure_and_result_allow_direct_a(self) -> None:
        self.assertEqual(awareness_result_provenance_errors(a_row(), [], []), [])

    def test_procedure_without_result_prohibits_strong_a(self) -> None:
        row = a_row(
            awareness_result_reporting="not-reported", awareness_result_support="not-applicable",
            awareness_result_procedure_type="not-applicable", awareness_result_description=None,
            awareness_result_source_location=None, awareness_result_source_experiment_id=None,
        )
        self.assertTrue(awareness_result_provenance_errors(row, [], []))

    def test_complete_transferred_result_bundle_allows_validated_a(self) -> None:
        row = a_row(
            A_code="A-validated",
            awareness_result_reporting="not-reported", awareness_result_support="not-applicable",
            awareness_result_procedure_type="not-applicable", awareness_result_description=None,
            awareness_result_source_location=None, awareness_result_source_experiment_id=None,
        )
        self.assertEqual(awareness_result_provenance_errors(row, [a_bundle()], [a_link()]), [])

    def test_similar_stimulus_different_sample_does_not_propagate_a(self) -> None:
        row = a_row(
            A_code="A-validated", awareness_result_reporting="not-reported",
            awareness_result_support="not-applicable", awareness_result_procedure_type="not-applicable",
            awareness_result_description=None, awareness_result_source_location=None,
            awareness_result_source_experiment_id=None,
        )
        self.assertTrue(awareness_result_provenance_errors(row, [], []))

    def test_mismatched_awareness_test_type_is_rejected(self) -> None:
        row = a_row(awareness_result_procedure_type="presence-absence-detection")
        self.assertTrue(awareness_result_provenance_errors(row, [], []))

    def test_missing_result_source_location_is_rejected(self) -> None:
        self.assertTrue(awareness_result_provenance_errors(a_row(awareness_result_source_location=None), [], []))

    def test_supplement_result_is_valid_when_explicitly_linked(self) -> None:
        row = a_row(
            A_code="A-validated", awareness_result_reporting="not-reported",
            awareness_result_support="not-applicable", awareness_result_procedure_type="not-applicable",
            awareness_result_description=None, awareness_result_source_location=None,
            awareness_result_source_experiment_id=None,
        )
        link = a_link(source_type="supplementary-analysis")
        self.assertEqual(awareness_result_provenance_errors(row, [a_bundle()], [link]), [])

    def test_procedure_only_transfer_member_cannot_complete_a(self) -> None:
        row = a_row(
            A_code="A-validated", awareness_result_reporting="not-reported",
            awareness_result_support="not-applicable", awareness_result_procedure_type="not-applicable",
            awareness_result_description=None, awareness_result_source_location=None,
            awareness_result_source_experiment_id=None,
        )
        self.assertTrue(awareness_result_provenance_errors(row, [a_bundle()], [a_link(content="procedure-description")]))

    def test_second_experiment_requires_own_result_or_transfer_bundle(self) -> None:
        first = a_row()
        second = a_row(
            comparison_id="P000001_E02_C01", experiment_id="P000001_E02",
            awareness_result_reporting="not-reported", awareness_result_support="not-applicable",
            awareness_result_procedure_type="not-applicable", awareness_result_description=None,
            awareness_result_source_location=None, awareness_result_source_experiment_id=None,
        )
        self.assertEqual(awareness_result_provenance_errors(first, [], []), [])
        self.assertTrue(awareness_result_provenance_errors(second, [], []))


class RunIdNamespaceTests(unittest.TestCase):
    def test_prefreeze_diagnostic_prefix_is_allowed(self) -> None:
        validate_run_id_namespace("PREFREEZE_DIAG_004", pre_freeze_diagnostic=True)

    def test_calib_prefix_is_rejected_for_future_diagnostic(self) -> None:
        with self.assertRaises(ValueError):
            validate_run_id_namespace("CALIB_005", pre_freeze_diagnostic=True)

    def test_historical_calib_compatibility_is_unchanged(self) -> None:
        validate_run_id_namespace("CALIB_003", pre_freeze_diagnostic=False)

    def test_registered_naming_is_unchanged(self) -> None:
        validate_run_id_namespace("RUN_2026_001", pre_freeze_diagnostic=False)


if __name__ == "__main__":
    unittest.main()
