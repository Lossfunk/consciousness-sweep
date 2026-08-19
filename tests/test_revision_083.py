from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from derive_outputs import (  # noqa: E402
    constraint_awareness_difference,
    constraint_equivalence_supported,
    constraint_unaware_capacity,
)
from execution_contract import (  # noqa: E402
    capacity_identity_errors,
    contrast_integrity_bundle_errors,
    functional_structure_errors,
    operational_functional_identity_requires_factorial,
    route_audit_errors,
)


def structure_row(
    comparison_id: str,
    *,
    structure: str,
    assessment: str,
    basis: str,
    focal_id: str | None = None,
) -> dict[str, object]:
    return {
        "comparison_id": comparison_id,
        "experiment_id": comparison_id.rsplit("_C", 1)[0],
        "current_status": "fully-evaluated",
        "Y_structure": structure,
        "functional_structure_assessment": assessment,
        "functional_identity_basis": basis,
        "functional_structure_reason": "Synthetic operational identity rationale.",
        "factorial_focal_comparison_id": focal_id,
    }


def capacity_row(**updates: object) -> dict[str, object]:
    row: dict[str, object] = {
        "A_code": "A-direct",
        "E_code": "E-physical-only",
        "F_code": "F-meaningful",
        "Y_label": "synthetic focal function",
        "Y_structure": "scalar",
        "unaware_capacity_claim": "synthetic focal function",
        "unaware_capacity_evidence_scope": "whole-focal-Y",
        "unaware_capacity": "supported",
        "unaware_capacity_stats_status": "adequate",
        "awareness_effect": "not-tested",
        "awareness_effect_stats_status": "not-applicable",
        "difference_tested": "not-applicable",
        "null_evidence_adequacy": "not-applicable",
        "Meyen_role": "not-applicable",
        "Meyen_status": None,
        "current_status": "fully-evaluated",
    }
    row.update(updates)
    return row


def audit_row(**updates: object) -> dict[str, object]:
    row: dict[str, object] = {
        "A_code": "A-validated",
        "E_code": "E-physical-only",
        "F_code": "F-meaningful",
        "structural_audit_status": "complete",
        "awareness_effect_route_status": "not-viable",
        "unaware_capacity_route_status": "viable",
        "null_equivalence_route_status": "not-required",
        "unaware_capacity": "supported",
        "awareness_effect": "unresolved",
        "difference_tested": "yes",
        "result_inspection_status": "completed-viable-routes",
        "awareness_effect_critical_effect": "Synthetic direct aware/unaware interaction.",
        "awareness_effect_estimate": "interaction estimate = 1 synthetic unit",
        "awareness_effect_estimate_interpretable": "yes",
        "awareness_effect_stats_status": "adequate",
        "awareness_effect_stats_reason": "The direct interaction and estimate were reported.",
        "Meyen_role": "not-applicable",
        "Meyen_status": None,
        "current_status": "fully-evaluated",
    }
    row.update(updates)
    return row


def e_bundle(*, resolution: str, alternative: str | None = None) -> dict[str, object]:
    return {
        "evidence_bundle_id": "SYN_EB000001",
        "focal_comparison_id": "P000001_E01_C01",
        "supported_premise": "E-diagnostic",
        "required_member_keys": ["pattern-control"],
        "bundle_status": "complete",
        "contrast_integrity_alternative": alternative,
        "contrast_integrity_anchor_type": (
            "design-imposed-difference" if alternative else "none"
        ),
        "contrast_integrity_anchor_source_location": (
            "synthetic design" if alternative else None
        ),
        "contrast_integrity_viability_reason": (
            "The task design independently motivates this finite state and it can change Y."
            if alternative else None
        ),
        "contrast_integrity_prediction": (
            "Holding this state fixed removes the policy-based prediction." if alternative else None
        ),
        "contrast_integrity_control_member_key": (
            "pattern-control" if resolution in {"ruled-out", "unresolved"} else None
        ),
        "contrast_integrity_resolution": resolution,
        "contrast_integrity_resolution_reason": "Synthetic bounded contrast-integrity disposition.",
    }


def e_link() -> dict[str, object]:
    return {
        "evidence_bundle_id": "SYN_EB000001",
        "member_key": "pattern-control",
        "support_role": "alternative-explanation-control",
        "dependency_role": "required",
        "same_focal_Y_status": "yes",
        "member_status": "supports",
        "used_for_decision": True,
    }


class FunctionalIdentityTests(unittest.TestCase):
    def test_a_same_operational_mapping_requires_factorial_focal(self) -> None:
        self.assertTrue(operational_functional_identity_requires_factorial(
            same_information_x=True,
            same_downstream_output=True,
            same_task_stage=True,
            factor_changes_x_relation=True,
            higher_order_shared_mapping=True,
            conservative_common_function=True,
        ))

    def test_b_mechanism_labels_do_not_change_operational_identity(self) -> None:
        answers = dict(
            same_information_x=True,
            same_downstream_output=True,
            same_task_stage=True,
            factor_changes_x_relation=True,
            higher_order_shared_mapping=True,
            conservative_common_function=True,
        )
        self.assertTrue(operational_functional_identity_requires_factorial(**answers))

    def test_c_truly_distinct_downstream_function_allows_scalar(self) -> None:
        self.assertFalse(operational_functional_identity_requires_factorial(
            same_information_x=True,
            same_downstream_output=False,
            same_task_stage=False,
            factor_changes_x_relation=False,
            higher_order_shared_mapping=False,
            conservative_common_function=False,
        ))
        first = structure_row(
            "P000001_E01_C01", structure="scalar", assessment="scalar-justified",
            basis="distinct-downstream-outputs",
        )
        second = structure_row(
            "P000001_E01_C02", structure="scalar", assessment="scalar-justified",
            basis="distinct-downstream-outputs",
        )
        self.assertEqual(functional_structure_errors([first, second]), [])

    def test_d_effect_names_only_is_not_a_scalar_basis(self) -> None:
        scalar = structure_row(
            "P000001_E01_C01", structure="scalar", assessment="scalar-justified",
            basis="effect-names-only",
        )
        self.assertTrue(any("labels are insufficient" in error for error in functional_structure_errors([scalar])))

    def test_e_factorial_focal_and_linked_component_may_coexist(self) -> None:
        focal = structure_row(
            "P000001_E01_C01", structure="factorial-functional",
            assessment="factorial-functional-required", basis="common-operational-mapping",
        )
        component = structure_row(
            "P000001_E01_C02", structure="scalar",
            assessment="factorial-functional-required", basis="common-operational-mapping",
            focal_id="P000001_E01_C01",
        )
        self.assertEqual(functional_structure_errors([focal, component]), [])


class CapacityIdentityTests(unittest.TestCase):
    def test_a_interference_does_not_support_regulation_capacity(self) -> None:
        row = capacity_row(
            Y_label="regulation of distractor interference",
            unaware_capacity_claim="distractor interference",
        )
        self.assertTrue(capacity_identity_errors(row))
        self.assertFalse(constraint_unaware_capacity(row))

    def test_b_automatic_bias_does_not_support_strategic_capacity(self) -> None:
        row = capacity_row(
            Y_label="strategic use of an instructed rule",
            unaware_capacity_claim="automatic stimulus bias",
        )
        self.assertTrue(capacity_identity_errors(row))

    def test_c_component_with_own_comparison_may_support_capacity(self) -> None:
        row = capacity_row(
            Y_label="automatic stimulus bias",
            unaware_capacity_claim="automatic stimulus bias",
        )
        self.assertEqual(capacity_identity_errors(row), [])
        self.assertTrue(constraint_unaware_capacity(row))

    def test_d_novel_capacity_identity_is_rejected(self) -> None:
        row = capacity_row(unaware_capacity_claim="novel linked component")
        self.assertTrue(capacity_identity_errors(row))

    def test_e_one_positive_factorial_component_does_not_support_parent(self) -> None:
        row = capacity_row(
            Y_structure="factorial-functional",
            unaware_capacity_evidence_scope="component-only",
        )
        self.assertTrue(any("whole focal Y" in error for error in capacity_identity_errors(row)))
        self.assertFalse(constraint_unaware_capacity(row))


class DescriptiveAwarenessAuditTests(unittest.TestCase):
    def test_a_weak_e_nonsignificant_direct_test_can_be_descriptive_not_equivalent(self) -> None:
        row = audit_row(
            awareness_effect="no-detectable-difference",
            null_equivalence_route_status="required",
            null_evidence_adequacy="weak",
        )
        self.assertEqual(route_audit_errors(row), [])
        self.assertFalse(constraint_equivalence_supported(row))

    def test_b_weak_e_significant_direct_test_is_unresolved(self) -> None:
        row = audit_row(awareness_effect="unresolved")
        self.assertEqual(route_audit_errors(row), [])
        self.assertFalse(constraint_awareness_difference(row))
        invalid = dict(row, awareness_effect="difference-supported")
        self.assertTrue(any("weak A/E/F" in error for error in route_audit_errors(invalid)))

        incomplete = dict(row, awareness_effect_estimate=None)
        self.assertTrue(any("awareness_effect_estimate" in error for error in route_audit_errors(incomplete)))

    def test_c_no_direct_comparison_allows_not_tested(self) -> None:
        row = audit_row(
            awareness_effect="not-tested",
            difference_tested="not-applicable",
            awareness_effect_stats_status="not-applicable",
        )
        self.assertEqual(route_audit_errors(row), [])

    def test_d_strong_e_direct_difference_is_unchanged(self) -> None:
        row = audit_row(
            E_code="E-matched",
            awareness_effect_route_status="viable",
            awareness_effect="difference-supported",
        )
        self.assertEqual(route_audit_errors(row), [])
        self.assertTrue(constraint_awareness_difference(row))


class ContrastIntegrityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.row = {"comparison_id": "P000001_E01_C01", "E_code": "E-diagnostic"}

    def test_a_policy_knowledge_cochange_blocks_diagnostic(self) -> None:
        bundle = e_bundle(resolution="unresolved", alternative="learned task-policy knowledge")
        self.assertTrue(contrast_integrity_bundle_errors(self.row, [bundle], [e_link()]))

    def test_b_fixed_policy_and_only_evidence_difference_does_not_block(self) -> None:
        bundle = e_bundle(resolution="not-applicable")
        self.assertEqual(contrast_integrity_bundle_errors(self.row, [bundle], [e_link()]), [])

    def test_c_blockwise_strategy_cochange_must_be_audited(self) -> None:
        bundle = e_bundle(resolution="unresolved", alternative="block-specific response strategy")
        self.assertTrue(contrast_integrity_bundle_errors(self.row, [bundle], [e_link()]))

    def test_d_unmotivated_hidden_process_does_not_block(self) -> None:
        bundle = e_bundle(resolution="not-applicable")
        self.assertEqual(contrast_integrity_bundle_errors(self.row, [bundle], []), [])

    def test_e_threshold_shift_without_task_state_cochange_remains_possible(self) -> None:
        bundle = e_bundle(resolution="not-applicable")
        self.assertEqual(contrast_integrity_bundle_errors(self.row, [bundle], [e_link()]), [])

    def test_f_explicit_control_can_rule_out_design_motivated_alternative(self) -> None:
        bundle = e_bundle(resolution="ruled-out", alternative="instruction-dependent policy")
        self.assertEqual(contrast_integrity_bundle_errors(self.row, [bundle], [e_link()]), [])
        self.assertTrue(contrast_integrity_bundle_errors(self.row, [bundle], []))


if __name__ == "__main__":
    unittest.main()
