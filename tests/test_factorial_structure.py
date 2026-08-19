from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from execution_contract import (  # noqa: E402
    capacity_identity_errors,
    contrast_integrity_bundle_errors,
    derived_bundle_status,
    factorial_e_diagnostic_bundle_errors,
    functional_structure_errors,
    operational_functional_identity_requires_factorial,
)


def row(
    comparison_id: str,
    *,
    structure: str,
    assessment: str,
    focal_id: str | None = None,
    e_code: str = "E-physical-only",
    basis: str | None = None,
) -> dict[str, object]:
    if basis is None:
        basis = {
            "factorial-functional-required": "common-operational-mapping",
            "scalar-justified": "distinct-downstream-outputs",
            "not-applicable": "not-applicable-single-effect",
            "not-assessed": "not-assessed",
        }[assessment]
    return {
        "comparison_id": comparison_id,
        "experiment_id": comparison_id.rsplit("_C", 1)[0],
        "current_status": "fully-evaluated",
        "Y_structure": structure,
        "functional_structure_assessment": assessment,
        "functional_identity_basis": basis,
        "functional_structure_reason": "Synthetic Y-agnostic structure rationale.",
        "factorial_focal_comparison_id": focal_id,
        "E_code": e_code,
    }


def bundle(bundle_id: str, focal_id: str, status: str = "complete") -> dict[str, object]:
    return {
        "evidence_bundle_id": bundle_id,
        "focal_comparison_id": focal_id,
        "supported_premise": "E-diagnostic",
        "required_member_keys": ["control"],
        "bundle_status": status,
        "contrast_integrity_alternative": None,
        "contrast_integrity_anchor_type": "none",
        "contrast_integrity_anchor_source_location": None,
        "contrast_integrity_viability_reason": None,
        "contrast_integrity_prediction": None,
        "contrast_integrity_control_member_key": None,
        "contrast_integrity_resolution": "not-applicable",
        "contrast_integrity_resolution_reason": "No separate design-motivated task-state alternative is present.",
    }


def link(
    bundle_id: str,
    focal_id: str,
    *,
    role: str = "alternative-explanation-control",
    status: str = "supports",
) -> dict[str, object]:
    return {
        "evidence_bundle_id": bundle_id,
        "focal_comparison_id": focal_id,
        "member_key": "control",
        "support_role": role,
        "dependency_role": "required",
        "same_focal_Y_status": "yes",
        "member_status": status,
        "used_for_decision": status == "supports",
        "supported_claim": "A synthetic control result addresses the stated evidence-only alternative.",
    }


class FunctionalStructureTests(unittest.TestCase):
    def test_a_coherent_factorial_mapping_requires_and_accepts_focal(self) -> None:
        focal = row(
            "P000001_E01_C01",
            structure="factorial-functional",
            assessment="factorial-functional-required",
        )
        self.assertEqual(functional_structure_errors([focal]), [])

    def test_b_factorial_and_optional_linked_scalar_components_coexist(self) -> None:
        focal = row(
            "P000001_E01_C01",
            structure="factorial-functional",
            assessment="factorial-functional-required",
        )
        component = row(
            "P000001_E01_C02",
            structure="scalar",
            assessment="factorial-functional-required",
            focal_id="P000001_E01_C01",
        )
        self.assertEqual(functional_structure_errors([focal, component]), [])

    def test_c_distinct_downstream_functions_remain_separate(self) -> None:
        first = row("P000001_E01_C01", structure="scalar", assessment="scalar-justified")
        second = row("P000001_E01_C02", structure="scalar", assessment="scalar-justified")
        self.assertEqual(functional_structure_errors([first, second]), [])

    def test_d_atomized_rows_without_assessment_are_rejected(self) -> None:
        first = row("P000001_E01_C01", structure="scalar", assessment="not-applicable")
        second = row("P000001_E01_C02", structure="scalar", assessment="not-applicable")
        errors = functional_structure_errors([first, second])
        self.assertEqual(len(errors), 2)
        self.assertTrue(all("scalar-justified" in error for error in errors))

    def test_focal_must_precede_linked_component(self) -> None:
        component = row(
            "P000001_E01_C01",
            structure="scalar",
            assessment="factorial-functional-required",
            focal_id="P000001_E01_C02",
        )
        focal = row(
            "P000001_E01_C02",
            structure="factorial-functional",
            assessment="factorial-functional-required",
        )
        self.assertTrue(any("instantiated before" in error for error in functional_structure_errors([component, focal])))

    def test_e_external_or_control_support_must_complete_bundle(self) -> None:
        focal_id = "P000001_E01_C01"
        focal = row(
            focal_id,
            structure="factorial-functional",
            assessment="factorial-functional-required",
            e_code="E-diagnostic",
        )
        incomplete_link = link("SYN_EB000001", focal_id, status="unavailable")
        self.assertEqual(derived_bundle_status([incomplete_link], ["control"]), "incomplete")
        self.assertTrue(factorial_e_diagnostic_bundle_errors(focal, [bundle("SYN_EB000001", focal_id, "incomplete")], [incomplete_link]))

        complete_link = link("SYN_EB000001", focal_id)
        self.assertEqual(derived_bundle_status([complete_link], ["control"]), "complete")
        self.assertEqual(
            factorial_e_diagnostic_bundle_errors(
                focal, [bundle("SYN_EB000001", focal_id)], [complete_link]
            ),
            [],
        )

    def test_f_interaction_alone_is_not_factorial_e_diagnostic(self) -> None:
        focal_id = "P000001_E01_C01"
        focal = row(
            focal_id,
            structure="factorial-functional",
            assessment="factorial-functional-required",
            e_code="E-diagnostic",
        )
        interaction_only = link("SYN_EB000001", focal_id, role="E-diagnostic-support")
        errors = factorial_e_diagnostic_bundle_errors(
            focal, [bundle("SYN_EB000001", focal_id)], [interaction_only]
        )
        self.assertEqual(len(errors), 1)
        self.assertIn("alternative-explanation-control", errors[0])

    def test_g_single_scalar_comparison_remains_supported(self) -> None:
        scalar = row("P000001_E01_C01", structure="scalar", assessment="not-applicable")
        self.assertEqual(functional_structure_errors([scalar]), [])


class SchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = json.loads((ROOT / "schemas" / "experiments.schema.json").read_text())
        Draft202012Validator.check_schema(cls.schema)
        cls.validator = Draft202012Validator(cls.schema)

    def base_identified_record(self) -> dict[str, object]:
        record = {field: None for field in self.schema["required"]}
        for field in (
            "evidence_bundle_ids",
            "E_diagnostic_source_locations",
            "factorial_component_effects",
            "stats_flags",
        ):
            record[field] = []
        record.update(
            comparison_id="P000001_E01_C01",
            experiment_id="P000001_E01",
            paper_id="P000001",
            experiment_label="Synthetic experiment",
            structural_audit_status="not-started",
            awareness_effect_route_status="not-assessed",
            unaware_capacity_route_status="not-assessed",
            null_equivalence_route_status="not-assessed",
            result_inspection_status="not-started",
            functional_structure_assessment="not-assessed",
            functional_identity_basis="not-assessed",
            functional_structure_reason=None,
            factorial_focal_comparison_id=None,
            current_status="identified",
        )
        return record

    def test_schema_requires_specific_structure_assessment_field(self) -> None:
        record = self.base_identified_record()
        self.assertEqual(list(self.validator.iter_errors(record)), [])
        del record["functional_structure_assessment"]
        self.assertTrue(any(error.validator == "required" for error in self.validator.iter_errors(record)))

    def test_schema_accepts_y_agnostic_scalar_decision(self) -> None:
        record = self.base_identified_record()
        record.update(
            functional_structure_assessment="scalar-justified",
            functional_identity_basis="distinct-downstream-outputs",
            functional_structure_reason="Two downstream functions are substantively distinct.",
            Y_structure="scalar",
        )
        self.assertEqual(list(self.validator.iter_errors(record)), [])

    def test_schema_accepts_factorial_focal_with_components(self) -> None:
        record = self.base_identified_record()
        record.update(
            functional_structure_assessment="factorial-functional-required",
            functional_identity_basis="common-operational-mapping",
            functional_structure_reason="The critical interaction tests one coherent mapping.",
            Y_structure="factorial-functional",
            factorial_Y_reason="The components jointly operationalize one conservative function.",
            factorial_component_effects=[
                {
                    "component_id": "component-a",
                    "X_task_relation": "state-a",
                    "awareness_condition": "aware",
                    "effect_description": "Synthetic effect A",
                    "statistical_result": None,
                    "source_location": "synthetic fixture",
                },
                {
                    "component_id": "component-b",
                    "X_task_relation": "state-b",
                    "awareness_condition": "unaware",
                    "effect_description": "Synthetic effect B",
                    "statistical_result": None,
                    "source_location": "synthetic fixture",
                },
            ],
        )
        self.assertEqual(list(self.validator.iter_errors(record)), [])


if __name__ == "__main__":
    unittest.main()
