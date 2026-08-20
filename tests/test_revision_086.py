from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker, ValidationError


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tests"))

from execution_contract import (  # noqa: E402
    bridge_expansion_allowed,
    bridge_experiment_errors,
    citation_child_bridge_depth,
    citation_window_key,
    completion_errors,
    derive_paper_citation_node_status,
    experiment_citation_node_status,
    mark_bridge_expansion_complete,
    reconcile_bridge_frontier,
    reusable_completed_window,
)
from test_pipeline import experiment_group, paper  # noqa: E402


def bridge_group(failed: str = "functional-y", **updates: object) -> dict[str, object]:
    ingredients = {
        "specific-x": ("failed", "present", "present"),
        "awareness-attempt": ("present", "failed", "present"),
        "functional-y": ("present", "present", "failed"),
    }[failed]
    row = experiment_group(
        disposition="no-qualifying-comparison",
        disposition_reason="A discovery-only near-miss creates no comparison row.",
        linked_comparison_ids=[],
        citation_specific_x=ingredients[0],
        citation_awareness_attempt=ingredients[1],
        citation_functional_y=ingredients[2],
        bridge_near_neighbor="yes",
        bridge_disposition="eligible",
        bridge_failed_ingredient=failed,
        bridge_rationale=(
            "Two named CORE ingredients co-occur, the recorded third ingredient explicitly "
            "fails, and the experiment remains a meaningful empirical near-neighbor."
        ),
    )
    row.update(updates)
    return row


def core_group(**updates: object) -> dict[str, object]:
    row = experiment_group(
        citation_specific_x="present",
        citation_awareness_attempt="present",
        citation_functional_y="present",
        bridge_near_neighbor="yes",
        bridge_disposition="not-eligible",
        bridge_failed_ingredient="not-applicable",
        bridge_rationale="All three CORE ingredients occur in this experiment, so bridge is inapplicable.",
    )
    row.update(updates)
    return row


def evaluated_paper(**updates: object) -> dict[str, object]:
    row = paper(
        fulltext_status="retrieved-published",
        fulltext_source="synthetic verified fixture",
        current_status="fulltext-evaluated",
        bridge_empirical_status="empirical",
        citation_node_status="bridge",
        citation_node_reason="Full-text physical-experiment audit derives strict bridge status.",
    )
    row.update(updates)
    return row


def state(**updates: object) -> dict[str, object]:
    row: dict[str, object] = {
        "workflow_phase": "principal-discovery",
        "citation_frontier_status": "satisfied",
        "process_frontier_status": "satisfied",
        "blind_lane_status": "complete",
        "activated_normalized_y_labels": [],
        "bridge_depth0_eligible_paper_ids": [],
        "pending_bridge_expansion_paper_ids": [],
        "completed_bridge_expansion_paper_ids": [],
    }
    row.update(updates)
    return row


class StrictBridgeEligibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.group_schema = json.loads(
            (ROOT / "schemas" / "experiment_groups.schema.json").read_text(encoding="utf-8")
        )

    def test_each_possible_explicit_failure_can_form_an_exact_two_bridge(self) -> None:
        for failed in ("specific-x", "awareness-attempt", "functional-y"):
            with self.subTest(failed=failed):
                group = bridge_group(failed)
                Draft202012Validator(self.group_schema).validate(group)
                self.assertEqual(bridge_experiment_errors(group), [])
                self.assertEqual(experiment_citation_node_status(group), "bridge")

    def test_one_present_two_failed_is_not_bridge(self) -> None:
        group = experiment_group(
            citation_specific_x="present", citation_awareness_attempt="failed",
            citation_functional_y="failed", bridge_near_neighbor="yes",
            bridge_disposition="not-eligible", bridge_failed_ingredient="not-applicable",
            bridge_rationale="Only one ingredient is present, so the strict exact-two rule fails.",
        )
        self.assertEqual(experiment_citation_node_status(group), "not-node")

    def test_unclear_third_ingredient_is_not_bridge(self) -> None:
        group = experiment_group(
            citation_specific_x="present", citation_awareness_attempt="present",
            citation_functional_y="unclear", bridge_near_neighbor="yes",
            bridge_disposition="not-eligible", bridge_failed_ingredient="not-applicable",
            bridge_rationale="The third ingredient is unclear rather than explicitly failed.",
        )
        self.assertEqual(experiment_citation_node_status(group), "not-node")
        invalid = dict(group, bridge_disposition="eligible", bridge_failed_ingredient="functional-y")
        with self.assertRaises(ValidationError):
            Draft202012Validator(self.group_schema).validate(invalid)

    def test_all_three_present_is_core_not_bridge(self) -> None:
        self.assertEqual(experiment_citation_node_status(core_group()), "core")

    def test_nonempirical_review_with_apparent_exact_two_is_not_bridge(self) -> None:
        candidate = evaluated_paper(
            bridge_empirical_status="nonempirical", citation_node_status="not-node",
            citation_node_reason="The full-text work is a review and cannot be a dynamic bridge.",
        )
        self.assertEqual(derive_paper_citation_node_status(candidate, [bridge_group()]), "not-node")

    def test_missing_full_text_is_not_bridge_and_does_not_create_a_failure(self) -> None:
        candidate = paper(
            fulltext_status="missing", missing_text_priority="ask-text-high",
            current_status="awaiting-fulltext", citation_node_status="not-assessable-missing-fulltext",
            citation_node_reason="Adequate full text is missing, so bridge status is not assessable.",
        )
        self.assertEqual(
            derive_paper_citation_node_status(candidate, [bridge_group()]),
            "not-assessable-missing-fulltext",
        )

    def test_generic_interest_without_positive_exact_two_disposition_is_not_bridge(self) -> None:
        group = experiment_group(
            citation_specific_x="present", citation_awareness_attempt="present",
            citation_functional_y="unclear", bridge_near_neighbor="not-assessed",
            bridge_disposition="not-eligible", bridge_failed_ingredient="not-applicable",
            bridge_rationale="Interesting consciousness paper.",
        )
        self.assertEqual(experiment_citation_node_status(group), "not-node")

    def test_ingredients_do_not_aggregate_across_physical_experiments(self) -> None:
        groups = [
            experiment_group(
                experiment_id="P000001_E01", citation_specific_x="present",
                citation_awareness_attempt="failed", citation_functional_y="failed",
                bridge_near_neighbor="no", bridge_disposition="not-eligible",
                bridge_failed_ingredient="not-applicable", bridge_rationale="Only X is present."
            ),
            experiment_group(
                experiment_id="P000001_E02", citation_specific_x="failed",
                citation_awareness_attempt="present", citation_functional_y="present",
                bridge_near_neighbor="no", bridge_disposition="not-eligible",
                bridge_failed_ingredient="not-applicable",
                bridge_rationale="The ingredients cannot be borrowed from the other experiment."
            ),
        ]
        candidate = evaluated_paper(citation_node_status="not-node")
        self.assertEqual(derive_paper_citation_node_status(candidate, groups), "not-node")

    def test_core_precedes_a_separate_bridge_experiment(self) -> None:
        candidate = evaluated_paper(citation_node_status="core")
        self.assertEqual(
            derive_paper_citation_node_status(candidate, [bridge_group(), core_group()]), "core"
        )

    def test_bridge_near_miss_needs_no_dummy_comparison(self) -> None:
        group = bridge_group()
        self.assertEqual(group["linked_comparison_ids"], [])
        self.assertEqual(group["disposition"], "no-qualifying-comparison")

    def test_ingredient_vocabulary_failed_ingredient_and_rationale_are_enforced(self) -> None:
        invalid_vocab = bridge_group(citation_specific_x="maybe")
        with self.assertRaises(ValidationError):
            Draft202012Validator(self.group_schema).validate(invalid_vocab)
        for invalid in (
            bridge_group(bridge_failed_ingredient="specific-x"),
            bridge_group(bridge_rationale="too vague"),
        ):
            with self.assertRaises(ValidationError):
                Draft202012Validator(self.group_schema).validate(invalid)


class BridgeLineageAndStateTests(unittest.TestCase):
    def test_core_to_bridge_may_expand_one_generation(self) -> None:
        self.assertEqual(citation_child_bridge_depth("core", 0), 0)
        self.assertTrue(bridge_expansion_allowed("bridge", [0]))

    def test_bridge_to_bridge_cannot_continue_same_lineage(self) -> None:
        self.assertEqual(citation_child_bridge_depth("bridge", 0), 1)
        self.assertFalse(bridge_expansion_allowed("bridge", [1]))
        with self.assertRaises(ValueError):
            citation_child_bridge_depth("bridge", 1)

    def test_core_descendant_resets_depth_and_later_bridge_is_allowed(self) -> None:
        self.assertEqual(citation_child_bridge_depth("core", 1), 0)
        self.assertTrue(bridge_expansion_allowed("bridge", [0]))

    def test_later_depth_zero_encounter_removes_first_discovery_order_dependence(self) -> None:
        initial = reconcile_bridge_frontier(
            state(), paper_id="P000001", node_status="bridge", encounter_depth=1
        )
        self.assertEqual(initial["pending_bridge_expansion_paper_ids"], [])
        later = reconcile_bridge_frontier(
            initial, paper_id="P000001", node_status="bridge", encounter_depth=0
        )
        self.assertEqual(later["pending_bridge_expansion_paper_ids"], ["P000001"])
        self.assertEqual(later["citation_frontier_status"], "reopened")

    def test_multiple_depth_zero_routes_create_one_retrieval_obligation(self) -> None:
        once = reconcile_bridge_frontier(
            state(), paper_id="P000001", node_status="bridge", encounter_depth=0
        )
        twice = reconcile_bridge_frontier(
            once, paper_id="P000001", node_status="bridge", encounter_depth=0
        )
        self.assertEqual(twice["pending_bridge_expansion_paper_ids"], ["P000001"])

    def test_blind_depth_zero_bridge_reopens_citation_not_process(self) -> None:
        updated = reconcile_bridge_frontier(
            state(workflow_phase="blind-lane"), paper_id="P000001",
            node_status="bridge", encounter_depth=0,
        )
        self.assertEqual(updated["workflow_phase"], "reopened-frontiers")
        self.assertEqual(updated["activated_normalized_y_labels"], [])
        self.assertEqual(updated["process_frontier_status"], "satisfied")

    def test_pending_bridge_blocks_completion(self) -> None:
        errors = completion_errors(state(
            workflow_phase="final-validation",
            pending_bridge_expansion_paper_ids=["P000001"],
        ))
        self.assertIn("required one-hop bridge expansions remain pending", errors)

    def test_bridge_to_core_revision_reopens_and_removes_bridge_obligation(self) -> None:
        pending = reconcile_bridge_frontier(
            state(), paper_id="P000001", node_status="bridge", encounter_depth=0
        )
        revised = reconcile_bridge_frontier(
            pending, paper_id="P000001", node_status="core", encounter_depth=1
        )
        self.assertEqual(revised["pending_bridge_expansion_paper_ids"], [])
        self.assertEqual(revised["citation_frontier_status"], "reopened")

    def test_missing_text_to_bridge_transition_creates_obligation_after_depth_zero_reassessment(self) -> None:
        missing = reconcile_bridge_frontier(
            state(), paper_id="P000001", node_status="not-assessable-missing-fulltext",
            encounter_depth=0,
        )
        obtained = reconcile_bridge_frontier(
            missing, paper_id="P000001", node_status="bridge", encounter_depth=0
        )
        self.assertEqual(obtained["pending_bridge_expansion_paper_ids"], ["P000001"])

    def test_completed_bridge_is_not_refetched(self) -> None:
        pending = reconcile_bridge_frontier(
            state(), paper_id="P000001", node_status="bridge", encounter_depth=0
        )
        complete = mark_bridge_expansion_complete(pending, "P000001")
        reached_again = reconcile_bridge_frontier(
            complete, paper_id="P000001", node_status="bridge", encounter_depth=0
        )
        self.assertEqual(reached_again["pending_bridge_expansion_paper_ids"], [])
        self.assertFalse(bridge_expansion_allowed("bridge", [0], already_completed=True))


class BridgeSearchProvenanceTests(unittest.TestCase):
    def test_completed_immutable_citation_window_is_reused_on_resume(self) -> None:
        key = citation_window_key(
            parent_paper_id="P000001", direction="backward", source="future-policy-source",
            source_parameters={"cursor": "initial"}, publication_cutoff=None,
        )
        completed = {
            "window_key": key, "window_status": "complete", "result_set_sha256": "a" * 64
        }
        self.assertIs(reusable_completed_window([completed], key), completed)

    def test_strict_bridge_search_schema_records_parent_direction_depth_source_and_basis(self) -> None:
        schema = json.loads(
            (ROOT / "schemas" / "search_log.schema.json").read_text(encoding="utf-8")
        )
        key = citation_window_key(
            parent_paper_id="P000001", direction="forward", source="future-policy-source",
            source_parameters={"page": 1}, publication_cutoff=None,
        )
        row = {
            "search_id": "TEST_S000001", "run_id": "TEST", "wave": 1,
            "execution_phase": "principal-discovery", "event_type": "forward-citation",
            "discovery_route": "forward-citation", "parent_paper_id": "P000001",
            "citation_parent_node_status": "bridge", "citation_parent_bridge_depth": 0,
            "citation_traversal_basis": "strict-bridge", "trigger_comparison_id": None,
            "normalized_y_label": None, "query_id": None, "query_text": None,
            "canonical_query": "citations:P000001:forward", "source_parameters": {"page": 1},
            "publication_cutoff": None, "requested_max_n": None, "actual_returned_n": None,
            "window_key": key, "result_set_sha256": None, "retrieved_at": None,
            "window_status": "incomplete", "reused_search_id": None,
            "source": "future-policy-source", "index_direction": "forward",
            "started_at": "2026-08-20T00:00:00Z", "completed_at": None,
            "results_returned": None, "new_unique_papers": None, "status": "started",
            "reason_or_notes": "Strict bridge status at an eligible depth-zero encounter enabled traversal.",
        }
        Draft202012Validator(schema, format_checker=FormatChecker()).validate(row)
        invalid = dict(row, citation_parent_bridge_depth=1)
        with self.assertRaises(ValidationError):
            Draft202012Validator(schema, format_checker=FormatChecker()).validate(invalid)

    def test_discovery_schema_retains_lineage_depth_and_reason_per_encounter(self) -> None:
        schema = json.loads(
            (ROOT / "schemas" / "discoveries.schema.json").read_text(encoding="utf-8")
        )
        row = {
            "discovery_id": "TEST_R000001", "search_id": "TEST_S000001",
            "paper_id": "P000001", "result_rank": 1, "raw_title": "Synthetic child",
            "raw_doi": None, "raw_url": None, "source_stable_id": "child-1",
            "discovered_at": "2026-08-20T00:00:00Z", "bridge_lineage_depth": 1,
            "bridge_lineage_reason": "Encountered as a child of one strict depth-zero bridge expansion.",
            "dedup_status": "new-paper", "dedup_reason": "No matching logical work exists.",
            "notes": None,
        }
        Draft202012Validator(schema, format_checker=FormatChecker()).validate(row)

    def test_experiment_decision_log_target_is_schema_valid(self) -> None:
        schema = json.loads(
            (ROOT / "schemas" / "decision_log.schema.json").read_text(encoding="utf-8")
        )
        event = {
            "decision_id": "TEST_D000001", "run_id": "TEST",
            "timestamp": "2026-08-20T00:00:00Z", "entity_type": "experiment",
            "entity_id": "P000001_E01", "decision_type": "bridge-assessment",
            "field": "bridge_disposition", "old_value": "not-assessed",
            "new_value": "eligible",
            "reason": "The three located ingredient decisions support the strict exact-two rule.",
            "source_location": "Synthetic article, Experiment 1", "agent": "test",
        }
        Draft202012Validator(schema, format_checker=FormatChecker()).validate(event)


if __name__ == "__main__":
    unittest.main()
