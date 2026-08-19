"""Diagnostic-only six-anchor derived-view regression; excluded from registered fixtures."""

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
    no_detectable_awareness_difference,
)


def comparison(**updates: object) -> dict[str, object]:
    row: dict[str, object] = {
        "A_code": "A-direct",
        "E_code": "E-diagnostic",
        "F_code": "F-meaningful",
        "experiment_id": "P000001_E01",
        "Y_functional_status": "downstream-function",
        "Y_label": "named synthetic capacity",
        "unaware_capacity_claim": "named synthetic capacity",
        "unaware_capacity_evidence_scope": "whole-focal-Y",
        "unaware_capacity": "supported",
        "unaware_capacity_stats_status": "adequate",
        "awareness_effect": "difference-supported",
        "awareness_effect_stats_status": "adequate",
        "difference_tested": "yes",
        "difference_source_experiment_id": "P000001_E01",
        "difference_source_location": "Synthetic Results",
        "difference_statistic_or_test": "Synthetic direct contrast",
        "null_evidence_adequacy": "inadequate",
        "Meyen_role": "not-applicable",
        "Meyen_status": "not-applicable",
        "current_status": "fully-evaluated",
    }
    row.update(updates)
    return row


class AdjudicatedAnchorDerivedViewNonRegressionTests(unittest.TestCase):
    def test_draft_0_8_3_preserves_settled_diagnostic_route_tuples(self) -> None:
        cases = {
            "Tsushima": comparison(
                A_code="A-validated", unaware_capacity="not-supported",
                Meyen_role="supplementary", Meyen_status="Meyen-failed",
            ),
            "Persaud": comparison(E_code="E-matched", unaware_capacity="unclear"),
            "Keizer": comparison(
                A_code="A-validated", E_code="E-physical-only",
                awareness_effect="no-detectable-difference",
                awareness_effect_stats_status="adequate",
                Meyen_role="supplementary", Meyen_status="Meyen-failed",
            ),
        }
        expected = {
            "Tsushima": (True, False, False, False),
            "Persaud": (True, False, False, False),
            "Keizer": (False, True, False, True),
        }
        for name, row in cases.items():
            with self.subTest(anchor=name):
                actual = (
                    constraint_awareness_difference(row),
                    constraint_unaware_capacity(row),
                    constraint_equivalence_supported(row),
                    no_detectable_awareness_difference(row),
                )
                self.assertEqual(actual, expected[name])


if __name__ == "__main__":
    unittest.main()
