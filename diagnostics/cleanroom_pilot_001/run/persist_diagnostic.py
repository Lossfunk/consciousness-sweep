from __future__ import annotations

import hashlib
import json
import shutil
import sys
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUN_ID = "PREFREEZE_DIAG_20260819"
RUN_DIR = ROOT / "runs" / RUN_ID
sys.path.insert(0, str(ROOT / "tools"))

from structured_write import (  # noqa: E402
    allocate_identifier,
    append_jsonl_record,
    doi_resolver_url,
    load_schema,
    write_csv_record,
)

SCHEMAS = {
    "papers_master.csv": load_schema(ROOT, "papers.schema.json"),
    "search_log.csv": load_schema(ROOT, "search_log.schema.json"),
    "discoveries.csv": load_schema(ROOT, "discoveries.schema.json"),
    "auxiliary_sources.csv": load_schema(ROOT, "auxiliary_sources.schema.json"),
    "fulltext_assets.csv": load_schema(ROOT, "fulltext_assets.schema.json"),
    "experiments_master.csv": load_schema(ROOT, "experiments.schema.json"),
    "evidence_bundles.csv": load_schema(ROOT, "evidence_bundles.schema.json"),
    "evidence_links.csv": load_schema(ROOT, "evidence_links.schema.json"),
}
DECISION_SCHEMA = load_schema(ROOT, "decision_log.schema.json")


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def append(table: str, row: dict) -> None:
    write_csv_record(RUN_DIR / table, SCHEMAS[table], row)


def upsert(table: str, row: dict, key: str) -> None:
    write_csv_record(RUN_DIR / table, SCHEMAS[table], row, key_field=key)


def log(entity_type: str, entity_id: str, decision_type: str, field: str | None,
        old_value, new_value, reason: str, source_location: str = "") -> None:
    decision_id = allocate_identifier(RUN_DIR, "decision")
    append_jsonl_record(
        RUN_DIR / "decision_log.jsonl",
        DECISION_SCHEMA,
        {
            "decision_id": decision_id,
            "run_id": RUN_ID,
            "timestamp": now(),
            "entity_type": entity_type,
            "entity_id": entity_id,
            "decision_type": decision_type,
            "field": field,
            "old_value": old_value,
            "new_value": new_value,
            "reason": reason,
            "source_location": source_location,
            "agent": "codex-desktop/gpt-5",
        },
    )


PAPERS = [
    {
        "key": "ben", "source": "ben_haim_2021", "year": 2021,
        "title": "Disentangling perceptual awareness from nonconscious processing in rhesus monkeys (Macaca mulatta)",
        "authors": "Moshe Shay Ben-Haim; Olga Dal Monte; Nicholas A. Fagan; Yarrow Dunham; Ran R. Hassin; Steve W. C. Chang; Laurie R. Santos",
        "doi": "10.1073/pnas.2017543118", "pages": 9, "experiments": 7,
        "abstract": "The abstract explicitly describes conscious/subliminal double dissociations in humans and rhesus monkeys with downstream spatial choice and cue use.",
    },
    {
        "key": "keizer", "source": "keizer_2015", "year": 2015,
        "title": "Consciousness is not necessary for visual feature binding",
        "authors": "André W. Keizer; Bernhard Hommel; Victor A. F. Lamme",
        "doi": "10.3758/s13423-014-0706-2", "pages": 8, "experiments": 1,
        "abstract": "The abstract describes masked versus visible Gabor processing and downstream orientation-location binding costs.",
    },
    {
        "key": "lamy", "source": "lamy_2015", "year": 2015,
        "title": "The Role of Conscious Perception in Attentional Capture and Object-File Updating",
        "authors": "Dominique Lamy; Limor Alon; Tomer Carmel; Nir Shalev",
        "doi": "10.1177/0956797614556777", "pages": 10, "experiments": 3,
        "abstract": "The abstract reports trialwise cue awareness, attentional capture, and object-file-updating-related spatial costs.",
    },
    {
        "key": "lin", "source": "lin_murray_2015", "year": 2015,
        "title": "More Power to the Unconscious: Conscious, but Not Unconscious, Exogenous Attention Requires Location Variation",
        "authors": "Zhicheng Lin; Scott O. Murray",
        "doi": "10.1177/0956797614560770", "pages": 10, "experiments": 3,
        "abstract": "The abstract describes visible/invisible repeated spatial cues, immediate cuing, and a later negative attentional aftereffect.",
    },
    {
        "key": "persaud", "source": "persaud_2011", "year": 2011,
        "title": "Awareness-related activity in prefrontal and parietal cortices in blindsight reflects more than superior visual performance",
        "authors": "Navindra Persaud; Matthew Davidson; Brian Maniscalco; Dean Mobbs; Richard E. Passingham; Alan Cowey; Hakwan Lau",
        "doi": "10.1016/j.neuroimage.2011.06.081", "pages": 7, "experiments": 1,
        "abstract": "The abstract reports performance-matched normal/blind-field stimulation, metacognitive monitoring, and frontoparietal BOLD contrasts.",
    },
    {
        "key": "tsushima", "source": "tsushima_2006", "year": 2006,
        "title": "Greater Disruption Due to Failure of Inhibitory Control on an Ambiguous Distractor",
        "authors": "Yoshiaki Tsushima; Yuka Sasaki; Takeo Watanabe",
        "doi": "10.1126/science.1133197", "pages": 4, "experiments": 5,
        "abstract": "The report summary describes subthreshold versus suprathreshold motion distractors, RSVP disruption, and inhibitory-control-related activity.",
    },
]


def component(cid: str, relation: str, awareness: str, effect: str, stat: str | None, location: str) -> dict:
    return {
        "component_id": cid,
        "X_task_relation": relation,
        "awareness_condition": awareness,
        "effect_description": effect,
        "statistical_result": stat,
        "source_location": location,
    }


def comparison(**overrides) -> dict:
    row = {
        "experiment_label": "Experiment",
        "X_label": "visual stimulus X",
        "X_description": "The experiment manipulates or stratifies awareness of the visual information used in the downstream task.",
        "awareness_measure": "Awareness measure described in the article.",
        "awareness_evidence_type": "subjective",
        "objective_visibility_test_informative": "not-applicable",
        "objective_visibility_test_reason": "No objective invisibility test is used for the operative A classification.",
        "A_code": "A-direct",
        "A_reason": "A qualifying awareness report is collected in the relevant experiment or condition.",
        "critical_dependency_status": "checked-none",
        "critical_dependency_reason": "The supplied article was checked for classification-critical dependencies; none is required for the conservative coding used here.",
        "evidence_bundle_ids": [],
        "structural_audit_status": "complete",
        "awareness_effect_route_status": "not-viable",
        "awareness_effect_route_reason": "The route lacks strong E or another required design gate.",
        "unaware_capacity_route_status": "viable",
        "unaware_capacity_route_reason": "Strong A and F-meaningful permit the unaware-capacity audit; E is not a gate.",
        "null_equivalence_route_status": "not-required",
        "null_equivalence_route_reason": "The comparison does not provide positive equivalence evidence and is not coded as an invariance claim.",
        "result_inspection_status": "completed-viable-routes",
        "result_inspection_reason": "Results were inspected for every structurally viable route and for the limited E-diagnostic test.",
        "first_order_measure": "Direct discrimination or visibility evidence concerning X.",
        "E_code": "E-physical-only",
        "E_reason": "Physical X is held nominally constant within the awareness split, but first-order evidence is neither actively matched nor shown equivalent.",
        "E_matching_basis": "none",
        "E_equivalence_margin": None,
        "E_equivalence_result": "not-applicable",
        "E_competing_account": None,
        "E_competing_prediction": None,
        "E_violating_pattern": None,
        "E_same_Y_reason": None,
        "E_diagnostic_source_locations": [],
        "Y_label": "downstream use of X",
        "Y_description": "A conservative downstream function operationalized by the task-dependent behavioral measure.",
        "Y_structure": "scalar",
        "factorial_Y_reason": None,
        "factorial_component_effects": [],
        "Y_evidence_role": "downstream-functional-measure",
        "F_code": "F-meaningful",
        "F_reason": "The dependent measure identifies a distinct downstream functional use rather than direct registration of X.",
        "Y_interpretation_clarity": "clear",
        "mechanistic_interpretation": "A finer mechanism is possible but is not required for the conservative function-level Y.",
        "mechanism_clarity": "ambiguous",
        "critical_comparison": "The critical behavioral contrast specified in the article.",
        "unaware_capacity_claim": "the named downstream function operates on X in the unaware condition",
        "unaware_capacity": "unclear",
        "unaware_capacity_reason": "The unaware condition is relevant, but the supplied reporting does not establish or refute the exact function with adequate evidence.",
        "unaware_capacity_critical_effect": "Unaware-condition effect reported in the article.",
        "unaware_capacity_stats_status": "unclear",
        "unaware_capacity_stats_reason": "The available statistics do not fully resolve the exact capacity claim.",
        "awareness_effect": "unresolved",
        "awareness_effect_reason": "The relevant awareness contrast is reported but does not satisfy another result category under the protocol.",
        "direction": None,
        "awareness_effect_critical_effect": "Reported awareness-by-Y contrast.",
        "awareness_effect_estimate": "Reported condition estimates; precision is limited.",
        "awareness_effect_estimate_interpretable": "unclear",
        "awareness_effect_stats_status": "concern",
        "awareness_effect_stats_reason": "The critical difference or its precision is insufficiently established for a stronger category.",
        "difference_tested": "unclear",
        "null_evidence_strength": "not-applicable",
        "null_evidence_adequacy": "not-applicable",
        "null_equivalence_margin": None,
        "null_equivalence_result": "not-applicable",
        "null_BF01": None,
        "null_CI_region": None,
        "null_CI_entirely_within_region": "not-applicable",
        "Meyen_role": "not-applicable",
        "Meyen_applicable": "no",
        "Meyen_status": None,
        "Meyen_reason": "The inference is not the direct-chance-plus-indirect-effect pattern governed by the Meyen diagnostic.",
        "stats_status": "concern",
        "stats_flags": ["other"],
        "stats_reason": "The critical inference has a reporting, robustness, or generalizability limitation recorded in the route-specific fields.",
        "constraint_summary": "The comparison is informative only to the extent stated by the separate unaware-capacity and awareness-effect fields.",
        "source_pages": "Supplied PDF",
        "source_figures_tables": None,
        "current_status": "fully-evaluated",
        "notes": "Bounded pre-freeze diagnostic; no outside literature or supplement retrieval was performed.",
    }
    row.update(overrides)
    return row


def strong_routes(row: dict) -> dict:
    strong_a = row["A_code"] in {"A-direct", "A-validated"}
    strong_e = row["E_code"] in {"E-matched", "E-diagnostic"}
    strong_f = row["F_code"] == "F-meaningful"
    row["awareness_effect_route_status"] = "viable" if strong_a and strong_e and strong_f else "not-viable"
    row["awareness_effect_route_reason"] = (
        "Strong A, strong E, and F-meaningful satisfy the awareness-effect design gates."
        if strong_a and strong_e and strong_f else
        "One or more required gates (strong A, strong E, F-meaningful) is absent."
    )
    row["unaware_capacity_route_status"] = "viable" if strong_a and strong_f else "not-viable"
    row["unaware_capacity_route_reason"] = (
        "Strong A and F-meaningful satisfy the unaware-capacity design gates; E is not a gate."
        if strong_a and strong_f else "Strong A or F-meaningful is absent."
    )
    row["result_inspection_status"] = "completed-viable-routes" if (strong_a and strong_f) else "not-required"
    row["result_inspection_reason"] = (
        "Results were inspected for the viable route(s), including the exact unaware function and critical awareness contrast where applicable."
        if (strong_a and strong_f) else "No inferential route is structurally viable; results were inspected only for coding and uncertainty."
    )
    return row


COMPARISONS: list[dict] = []


def add(paper: str, exp: int, label: str, row: dict, bundles: list[dict] | None = None) -> None:
    COMPARISONS.append({"paper": paper, "exp": exp, "label": label, "row": strong_routes(row), "bundles": bundles or []})


def diagnostic_e(locations: list[str], account: str, prediction: str, pattern: str, same_y: str) -> dict:
    return {
        "E_code": "E-diagnostic", "E_matching_basis": "none", "E_equivalence_result": "not-applicable",
        "E_reason": "First-order evidence is not matched, but the prespecified structured same-Y pattern violates the simple evidence-strength account.",
        "E_competing_account": account, "E_competing_prediction": prediction,
        "E_violating_pattern": pattern, "E_same_Y_reason": same_y,
        "E_diagnostic_source_locations": locations,
    }


def diff(effect: str, estimate: str, direction: str = "qualitative-change") -> dict:
    return {
        "awareness_effect": "difference-supported", "awareness_effect_reason": "The aware-versus-unaware difference or interaction was directly tested and supports a change in Y.",
        "direction": direction, "awareness_effect_critical_effect": effect,
        "awareness_effect_estimate": estimate, "awareness_effect_estimate_interpretable": "yes",
        "awareness_effect_stats_status": "adequate", "awareness_effect_stats_reason": "The critical difference/interaction is directly reported with an interpretable estimate and inferential test.",
        "difference_tested": "yes",
    }


def no_diff(effect: str, estimate: str) -> dict:
    return {
        "awareness_effect": "no-detectable-difference", "awareness_effect_reason": "The critical modulation was directly tested and not detected; this is not equivalence.",
        "direction": "no-detectable-difference", "awareness_effect_critical_effect": effect,
        "awareness_effect_estimate": estimate, "awareness_effect_estimate_interpretable": "yes",
        "awareness_effect_stats_status": "concern", "awareness_effect_stats_reason": "Condition estimates are interpretable, but no equivalence margin, Bayes factor, or informative confidence region was supplied.",
        "difference_tested": "yes", "null_evidence_strength": "nonsignificant-only", "null_evidence_adequacy": "weak",
    }


def meyen(role: str) -> dict:
    if role == "not-applicable":
        return {"Meyen_role": role, "Meyen_applicable": "no", "Meyen_status": None,
                "Meyen_reason": "The claim does not rest on a chance direct test plus a positive indirect effect."}
    return {"Meyen_role": role, "Meyen_applicable": "yes", "Meyen_status": "Meyen-unassessable",
            "Meyen_reason": "The article does not demonstrate an indirect-task sensitivity advantage over the direct awareness measure on a comparable scale; the role determines whether this gates the result."}


# Ben-Haim et al. Experiments 1, 2, 3, 4, 6, and 7. Experiment 5 is support-only.
for exp, species, paradigm, pages in [
    (1, "humans", "spatial cueing", "pp. 2-5, Figs. 1-2"),
    (2, "rhesus monkeys", "spatial cueing", "pp. 4-6, Fig. 2"),
    (3, "humans", "forced guessing", "pp. 5-6, Fig. 3"),
    (4, "rhesus monkeys", "forced guessing", "p. 6, Fig. 3"),
]:
    monkey = "monkeys" in species
    x = "masked versus supraliminal spatial cue location"
    y = "adaptive rule-guided use of an incongruent spatial cue"
    e = diagnostic_e(
        [pages],
        "More first-order cue evidence merely strengthens the same cue-driven target-selection mapping.",
        "The more visible/salient cue should yield a larger effect in the same direction as the masked cue.",
        "The masked cue produces congruent capture/interference or below-chance choice, whereas the visible cue supports faster or above-chance selection at the opposite location.",
        "Both signs concern the same mapping from cue location to selection of the contralateral target/reward.",
    )
    base = comparison(
        experiment_label=f"Experiment {exp}: {species}, {paradigm}", X_label=x,
        X_description="A star cue indicates a location while the rewarded/target location is opposite; cue duration/masking produces subliminal and supraliminal regimes.",
        awareness_measure=("Human self-report plus end-of-condition forced-choice cue localization; monkey awareness is inferred from human homologous patterns and a cited prior monkey report." if monkey else "Self-report of cue visibility/predictive awareness plus end-of-condition forced-choice cue localization."),
        awareness_evidence_type="mixed",
        objective_visibility_test_informative="unclear" if monkey else "yes",
        objective_visibility_test_reason=("The cited monkey validation source is not supplied, so sensitivity and transfer cannot be verified." if monkey else "The location task directly tests access to cue location and is reported at chance individually and at group level; exact trial details are in the unavailable supplement."),
        A_code="A-transfer-risk" if monkey else "A-direct",
        A_reason=("No qualifying awareness report is collected from the monkeys in the focal experiment; cross-species pattern matching and the unavailable cited monkey validation leave material transfer risk." if monkey else "Participants report the masked cues unseen and perform at chance in the direct cue-location test within the experimental regime."),
        critical_dependency_status="unresolved" if monkey else "resolved",
        critical_dependency_reason=("The monkey A classification depends on Andersen et al. (2014) and human-to-monkey transfer; that auxiliary paper and the supplement were not supplied." if monkey else "The main article reports the operative subjective and objective results, but supplement-only procedural detail is noted as a limitation rather than silently assumed."),
        first_order_measure="Cue-location forced choice and visibility report.",
        Y_label=y, Y_description="Using or resisting the cue's dominant spatial pull to select the opposite target/reward location.",
        Y_structure="factorial-functional", factorial_Y_reason="Visible and masked cue effects relative to the same baseline jointly define one rule-guided spatial-selection mapping.",
        factorial_component_effects=[
            component("masked", "incongruent cue versus baseline/chance", "unaware", "Interference or below-chance choice toward the cued location.", None, pages),
            component("visible", "incongruent cue versus baseline/chance", "aware", "Facilitation or above-chance choice at the opposite location.", None, pages),
        ],
        mechanistic_interpretation="Awareness may permit disengagement from cue capture and flexible use of the opposite-location rule.",
        critical_comparison="Masked versus supraliminal cue effects on opposite-location target/reward selection.",
        unaware_capacity_claim="adaptive rule-guided selection of the location opposite an incongruent cue",
        unaware_capacity="not-supported",
        unaware_capacity_reason="Masked-cue performance shows capture/interference or below-chance choice, not positive operation of the named opposite-location rule.",
        unaware_capacity_critical_effect=("Masked cue slowed target localization versus baseline." if exp in {1, 2} else "Masked cue produced below-chance reward-location choice."),
        unaware_capacity_stats_status="adequate" if exp in {1, 2, 4} else "concern",
        unaware_capacity_stats_reason="The unaware condition is directly tested; Experiment 3 uses an unusual participant-level quartile aggregation, while the other reported effects have direct tests.",
        source_pages=pages, source_figures_tables=pages,
        stats_status="concern" if exp in {3, 4} else "adequate",
        stats_flags=["other"] if exp in {3, 4} else ["none"],
        stats_reason="Mixed-model/binomial tests are reported; forced-guessing aggregation and missing supplement details are retained as concerns where applicable.",
        constraint_summary="The structured sign reversal supports an awareness-linked qualitative change only when A is strong; the masked condition does not demonstrate adaptive opposite-location rule use.",
        **e, **meyen("inference-critical" if monkey else "supplementary"),
    )
    if exp in {1, 2}:
        base.update(diff("Direct masked-versus-visible cue comparison", "Experiment 1 F(1,3585)=315.66; Experiment 2 F(1,4066)=7.66."))
    else:
        base.update({"difference_tested": "no", "awareness_effect_stats_status": "concern", "awareness_effect_estimate_interpretable": "unclear",
                     "awareness_effect_stats_reason": "Visible and masked conditions are each characterized, but the focal between-condition difference is not reported as a direct test.",
                     "awareness_effect_reason": "Separate condition results do not by themselves establish the critical aware-unaware difference.",
                     "awareness_effect_critical_effect": "Supraliminal above-chance versus masked below-chance choice.",
                     "awareness_effect_estimate": "Visible approximately 94.6% in humans; masked participant-level distribution below chance; monkey masked mean 43.5%.",
                     "awareness_effect": "unresolved", "direction": None})
    bundles = ([{"kind": "monkey-A", "status": "incomplete"}] if monkey else [])
    add("ben", exp, f"Experiment {exp}", base, bundles)

base = comparison(
    experiment_label="Experiment 6: informed versus uninformed subliminal cues", X_label="33-ms masked spatial cue location",
    X_description="The same brief cue is used before and after participants are explicitly informed that cues occur.",
    awareness_measure="Post-phase subjective reports of seeing the flashes and using them.", awareness_evidence_type="subjective",
    objective_visibility_test_informative="not-applicable", objective_visibility_test_reason="No objective invisibility test supports this comparison's A code.",
    A_code="A-direct", A_reason="Participants directly report cue awareness before and after the information manipulation.",
    E_code="E-physical-only", E_reason="The physical cue is unchanged, but first-order evidence is not matched and explicit instruction changes task knowledge.",
    first_order_measure="Subjective cue visibility/use report.", Y_label="learning and use of the opposite-location reward rule",
    Y_description="Selecting the reward location opposite the cue after learning its predictive relation.",
    critical_comparison="Pre-information versus post-information masked-cue choice.",
    unaware_capacity_claim="adaptive use of the opposite-location reward rule", unaware_capacity="not-supported",
    unaware_capacity_reason="Before information, unseen-cue choices were below chance rather than positive rule use.",
    unaware_capacity_critical_effect="Pre-information performance below chance, χ²(1)=4.85, p=.028.", unaware_capacity_stats_status="adequate",
    unaware_capacity_stats_reason="The pre-information departure from chance is directly tested, but it is in the opposite direction from the named capacity.",
    awareness_effect="unresolved", awareness_effect_reason="The instruction intervention is inseparable from the awareness change and no clean awareness difference is reported.",
    direction=None, awareness_effect_critical_effect="Pre/post information change among participants reporting cue visibility.",
    awareness_effect_estimate="67% of reporters reached criterion after information; no clean matched effect estimate.", awareness_effect_estimate_interpretable="no",
    awareness_effect_stats_status="concern", awareness_effect_stats_reason="Instruction and awareness are confounded.", difference_tested="no",
    source_pages="p. 7, Fig. 4B-C", source_figures_tables="Fig. 4B-C", stats_status="concern", stats_flags=["other"],
    stats_reason="The intervention changes both explicit task knowledge and awareness, preventing a clean critical contrast.",
    constraint_summary="Unseen cues do not support adaptive opposite-location rule use; the apparent post-information benefit cannot be attributed uniquely to awareness.",
    **meyen("not-applicable"),
)
add("ben", 6, "Experiment 6", base)

base = comparison(
    experiment_label="Experiment 7: trialwise cue awareness", X_label="17-ms masked spatial cue location",
    X_description="Participants are instructed to choose opposite the cue and report cue-location awareness on every trial.",
    awareness_measure="Trialwise 0-to-3 subjective awareness rating.", awareness_evidence_type="subjective",
    objective_visibility_test_informative="not-applicable", objective_visibility_test_reason="A is based on the direct trialwise subjective report.",
    A_code="A-direct", A_reason="The relevant cue-location awareness state is reported on each trial.", first_order_measure="Trialwise graded cue-location awareness.",
    Y_label="adaptive rule-guided selection opposite the cue", Y_description="Executing the explicitly instructed opposite-location choice rule.",
    Y_structure="factorial-functional", factorial_Y_reason="Unseen and clearly seen trials are component states of the same instructed spatial rule.",
    factorial_component_effects=[
        component("rating0", "choose opposite cue", "unaware", "Performance significantly below chance.", "Reported below chance", "p. 8, Fig. 4D"),
        component("rating2to3", "choose opposite cue", "aware", "Performance significantly above chance.", "χ²(3)=24.8, p<.0001 across ratings", "p. 8, Fig. 4D"),
    ],
    critical_comparison="Choice accuracy across trialwise cue-awareness ratings.",
    unaware_capacity_claim="adaptive execution of the instructed opposite-location rule", unaware_capacity="not-supported",
    unaware_capacity_reason="Rating-0 trials are below chance, affirmatively opposing positive operation of the rule.",
    unaware_capacity_critical_effect="Rating-0 choices significantly below chance.", unaware_capacity_stats_status="adequate",
    unaware_capacity_stats_reason="The unaware condition is directly compared with chance and the awareness-rating pattern is tested.",
    source_pages="pp. 7-8, Fig. 4D", source_figures_tables="Fig. 4D", stats_status="adequate", stats_flags=["none"],
    stats_reason="The awareness-by-choice pattern is directly tested, though the main article omits some supplement-only detail.",
    constraint_summary="Trialwise awareness changes the sign of rule-guided choice; unseen cues do not support adaptive execution of the instructed rule.",
    **diagnostic_e(["pp. 7-8, Fig. 4D"], "Greater cue evidence simply increases the same instructed opposite-choice mapping.",
                   "Performance should rise monotonically from chance toward correct opposite choice without reversing below chance.",
                   "Rating-0 trials are below chance whereas higher-awareness trials are above chance.",
                   "Both components are accuracy for the same instructed opposite-location rule."),
    **diff("Awareness rating by choice accuracy", "χ²(3)=24.8, p<.0001", "qualitative-change"),
    **meyen("not-applicable"),
)
add("ben", 7, "Experiment 7", base)

# Keizer et al.: one binding comparison; three tasks form one experiment group.
base = comparison(
    experiment_label="Experiment 1: mask configuration, binding, and mask evaluation", X_label="S1 Gabor orientation-location conjunction",
    X_description="A masked or visible first Gabor carries an arbitrary orientation-location conjunction later partially repeated by S2.",
    awareness_measure="Individualized pre-task staircase and post-task present/absent discrimination under the effective mask.",
    awareness_evidence_type="objective-invisibility", objective_visibility_test_informative="yes",
    objective_visibility_test_reason="The direct target-presence task has a 50% baseline, individualized staircasing, a post-test, and split-binomial exclusion; the large number of trials supports sensitivity despite no equivalence test.",
    A_code="A-validated", A_reason="Separate pre/post validation under the same stimulus and mask regime supports transfer to the binding task; the binding task mask was strengthened by 10%.",
    first_order_measure="Present/absent Gabor discrimination.", E_code="E-physical-only",
    E_reason="Effective and ineffective masking deliberately produce unequal evidence; no matching or diagnostic sign reversal is provided.",
    Y_label="short-term binding and retrieval of orientation-location conjunctions",
    Y_description="Partial-repetition reaction-time costs index integration of S1 orientation and location and retrieval on S2.",
    Y_structure="factorial-functional", factorial_Y_reason="Orientation repetition/alternation and location repetition/alternation jointly operationalize one binding relation.",
    factorial_component_effects=[
        component("effective", "orientation × location partial repetition", "unaware", "Binding cost 5.8 ms in primary analysis.", "t(27)=1.8, one-tailed p=.04", "pp. 4-5, Fig. 2, Table 1"),
        component("ineffective", "orientation × location partial repetition", "aware", "Binding cost 8.6 ms in primary analysis.", "t(27)=2.3, one-tailed p=.02", "pp. 4-5, Fig. 2, Table 1"),
    ],
    critical_comparison="Masking × orientation repetition × location repetition interaction.",
    unaware_capacity_claim="short-term integration and retrieval of arbitrary orientation-location conjunctions", unaware_capacity="supported",
    unaware_capacity_reason="The effective-mask condition shows the specified partial-repetition binding cost.",
    unaware_capacity_critical_effect="5.8-ms binding cost under effective masking, t(27)=1.8, one-tailed p=.04.",
    unaware_capacity_stats_status="concern", unaware_capacity_stats_reason="The one-tailed primary effect is weak and the inclusive robustness analysis did not yield significant planned binding costs.",
    source_pages="pp. 2-7, Figs. 1-3, Tables 1-2", source_figures_tables="Figs. 2-3; Tables 1-2",
    stats_status="concern", stats_flags=["selective-exclusions"],
    stats_reason="Ten of 41 participants were excluded for task performance in the primary analysis; including more participants made planned binding costs nonsignificant.",
    constraint_summary="Orientation-location binding is positively indicated under validated masking, but robustness/exclusion concerns prevent constraint-ready status; no awareness-linked invariance is established.",
    **no_diff("Masking × orientation × location interaction", "Primary F(1,27)=0.25, p>.6; costs 8.6 versus 5.8 ms."),
    **meyen("supplementary"),
)
add("keizer", 1, "Experiment 1", base)

# Lamy et al.: two distinct Ys in each of three experiments.
for exp, a_type, a_code, obj, pages, cap_u, cap_a, cap_test, cost_u, cost_a, cost_test in [
    (1, "subjective", "A-direct", "not-applicable", "pp. 2-5, Figs. 1-3, Table 1", 36, 50, "F(1,52)=1.76, p>.19", 1, 33, "F(1,52)=4.54, p<.04"),
    (2, "mixed", "A-direct", "yes", "pp. 5-7, Figs. 2-4, Table 1", 40, 55, "F<1", 2, 35, "F(1,44)=4.50, p<.04"),
    (3, "subjective", "A-direct", "not-applicable", "pp. 7-9, Figs. 2-3, Table 1", 104, 104, "F<1", 43, 8, "F(1,45)=3.92, p=.055"),
]:
    awareness = "Trialwise 0-to-3 cue visibility rating" if exp < 3 else "Trialwise yes/no cue visibility report"
    obj_reason = ("Experiment 2's separate forced-choice localization block is at chance (25.07%) for rating-0 trials and directly tests the cue property relevant to capture."
                  if exp == 2 else "A is based on the direct trialwise subjective report; no objective invisibility result is required for that code.")
    cap = comparison(
        experiment_label=f"Experiment {exp}: attentional capture", X_label="color-singleton cue location and target-set match",
        X_description="A spatially nonpredictive singleton cue either matches the target-defining color or has the same task status in Experiment 3.",
        awareness_measure=awareness, awareness_evidence_type=a_type, objective_visibility_test_informative=obj,
        objective_visibility_test_reason=obj_reason, A_code=a_code,
        A_reason="Awareness is reported on every trial; Experiment 2 also validates rating-0 cue localization in a separate block.",
        first_order_measure="Trialwise cue visibility, with forced-choice cue localization in Experiment 2.",
        Y_label="attentional-set-contingent spatial capture", Y_description="Cue-induced facilitation of target discrimination at the cued location.",
        Y_structure="scalar", critical_comparison="Awareness × cue-target location effect for the attention-capturing cue condition.",
        unaware_capacity_claim="attentional-set-contingent spatial capture by the cue", unaware_capacity="supported",
        unaware_capacity_reason="A significant same-location benefit occurs on trials reported wholly unseen.",
        unaware_capacity_critical_effect=f"Unaware same-location benefit {cap_u} ms.", unaware_capacity_stats_status="adequate",
        unaware_capacity_stats_reason="The unaware-condition location effect is directly tested and large in each experiment.",
        source_pages=pages, source_figures_tables="Fig. 2; Table 1", stats_status="adequate", stats_flags=["none"],
        stats_reason="The factorial mixed model directly estimates the within-condition capture and awareness modulation.",
        constraint_summary="Attentional-set-contingent spatial capture is supported under direct subjective unawareness, but E is only physical and the null awareness modulation is not equivalence.",
        **no_diff("Awareness × target-location effect for capture", f"Unaware {cap_u} ms versus aware {cap_a} ms; {cap_test}."),
        **meyen("supplementary" if exp == 2 else "not-applicable"),
    )
    add("lamy", exp, f"Experiment {exp} attentional capture", cap)
    objrow = comparison(
        experiment_label=f"Experiment {exp}: cue-target feature-change cost", X_label="color-singleton cue state before the target",
        X_description="An irrelevant/different-color cue and subsequent target occupy the same or different location, operationalizing a feature-change cost.",
        awareness_measure=awareness, awareness_evidence_type=a_type, objective_visibility_test_informative=obj,
        objective_visibility_test_reason=obj_reason, A_code=a_code,
        A_reason="Awareness is reported on every trial; Experiment 2 also validates rating-0 cue localization in a separate block.",
        critical_dependency_status="resolved", critical_dependency_reason="The paper cites prior object-file work for the mechanism, but the conservative Y here is the observed feature-change cost, so no unavailable external premise is used to pass F.",
        first_order_measure="Trialwise cue visibility, with forced-choice cue localization in Experiment 2.",
        Y_label="location-specific cost of updating a cue-target feature change",
        Y_description="The downstream cost/benefit change when a cue-defined object at a location is replaced by a target with a different task feature.",
        Y_structure="scalar", critical_comparison="Awareness × target location for the irrelevant/different-color cue condition.",
        mechanistic_interpretation="The authors interpret the location-specific cost as object-file updating; that finer mechanism remains separable from the conservative functional cost.",
        unaware_capacity_claim="location-specific updating cost for a cue-target feature change", unaware_capacity="unclear",
        unaware_capacity_reason="The unseen-cue estimate does not positively demonstrate the named updating cost with adequate dedicated statistics.",
        unaware_capacity_critical_effect=f"Unaware irrelevant/different-color location effect {cost_u} ms.", unaware_capacity_stats_status="unclear",
        unaware_capacity_stats_reason="A near-zero or differently signed location effect does not provide positive evidence for the named updating cost.",
        source_pages=pages, source_figures_tables="Fig. 2; Table 1", stats_status="adequate" if exp < 3 else "concern",
        stats_flags=["none"] if exp < 3 else ["weak-null-evidence"],
        stats_reason="The focal awareness modulation is directly tested in Experiments 1-2; Experiment 3's focal contrast is p=.055 and remains unresolved.",
        constraint_summary="The location-specific feature-change cost is awareness-linked in Experiments 1-2 but E is only physical; Experiment 3 is unresolved and no unaware updating capacity is positively shown.",
        **meyen("supplementary" if exp == 2 else "not-applicable"),
    )
    if exp < 3:
        objrow.update(diff("Awareness × target-location effect for the feature-change cue", f"Unaware {cost_u} ms versus aware cost {cost_a} ms; {cost_test}."))
    else:
        objrow.update({"awareness_effect": "unresolved", "awareness_effect_reason": "The focal aware-unaware location-effect difference narrowly misses the reported threshold and is not positive null evidence.",
                       "direction": None, "awareness_effect_critical_effect": "Awareness × location effect for different-color cues",
                       "awareness_effect_estimate": f"Unaware {cost_u} ms versus aware {cost_a} ms; {cost_test}.",
                       "awareness_effect_estimate_interpretable": "yes", "awareness_effect_stats_status": "concern",
                       "awareness_effect_stats_reason": "The focal contrast is p=.055 with no equivalence analysis.", "difference_tested": "yes"})
    add("lamy", exp, f"Experiment {exp} feature-change cost", objrow)

# Lin & Murray: Experiment 3 is a visible-only control and receives no comparison row.
lin_a = {
    "awareness_measure": "Post-task forced-choice cue-location discrimination; fixed-location validation is supplied by Experiment 2.",
    "awareness_evidence_type": "objective-invisibility", "objective_visibility_test_informative": "yes",
    "objective_visibility_test_reason": "The task directly tests cue location with a 50% baseline and 80-420 trials; Experiment 2 validates the fixed and random regimes with matched sequences.",
    "A_code": "A-validated", "A_reason": "Experiment 2's matched-sequence location test supports transfer to Experiment 1 fixed/random regimes; visible performance is near ceiling.",
    "critical_dependency_status": "resolved", "critical_dependency_reason": "The cross-experiment validation is contained in the supplied paper and is represented by a direct evidence bundle/link.",
    "first_order_measure": "Forced-choice cue-location discrimination.",
}
base = comparison(
    experiment_label="Experiment 1: immediate repeated-cue orienting", X_label="fixed or randomly located exogenous annulus cue",
    X_description="Visible red and masked black cues precede target detection in fixed-location and random-location blocks.",
    Y_label="exogenous spatial orienting across cue-location regularity",
    Y_description="The invalid-minus-valid target-detection latency effect across fixed and random cue-location regimes.",
    Y_structure="factorial-functional", factorial_Y_reason="Fixed and random regimes jointly test how the same spatial-orienting function changes with awareness and location variation.",
    factorial_component_effects=[
        component("fixed-unaware", "fixed cue", "unaware", "15.7-ms cuing benefit.", "t(23)=5.96, p<.001", "pp. 4-5, Fig. 2"),
        component("fixed-aware", "fixed cue", "aware", "2.1-ms no-detectable cuing effect.", "t(19)=0.85, p=.407", "pp. 4-5, Fig. 2"),
        component("random-unaware", "random cue", "unaware", "14.9-ms cuing benefit.", "t(23)=8.49, p<.001", "pp. 4-5, Fig. 2"),
        component("random-aware", "random cue", "aware", "14.2-ms cuing benefit.", "t(19)=4.57, p<.001", "pp. 4-5, Fig. 2"),
    ],
    critical_comparison="Cue visibility × validity in fixed blocks, contextualized by random-cue blocks.",
    unaware_capacity_claim="exogenous spatial orienting of target detection by a repeatedly fixed cue", unaware_capacity="supported",
    unaware_capacity_reason="The objectively validated invisible fixed cue produces a direct positive cuing benefit.",
    unaware_capacity_critical_effect="15.7-ms invalid-minus-valid effect, t(23)=5.96, p<.001.", unaware_capacity_stats_status="adequate",
    unaware_capacity_stats_reason="The within-unaware fixed-cue effect is directly tested and replicated in Experiment 2.",
    source_pages="pp. 2-6, Figs. 1-2, Table 2", source_figures_tables="Fig. 2; Table 2",
    stats_status="adequate", stats_flags=["none"], stats_reason="The key visibility × validity interaction is directly tested, with effect sizes and condition estimates.",
    constraint_summary="Validated invisible fixed cues orient target detection, whereas visible fixed cues do not; the same cues orient under random location, supporting a qualitative awareness-by-location-regime change.",
    **lin_a,
    **diagnostic_e(["pp. 4-5, Fig. 2"], "Greater first-order cue evidence simply strengthens the same exogenous orienting effect.",
                   "Visible cues should produce at least as much same-direction cuing as invisible cues in each location regime.",
                   "In fixed blocks invisible cues yield robust cuing while visible cues yield essentially none, yet both yield similar cuing in random blocks.",
                   "Fixed and random blocks manipulate the context of the same cue-to-target spatial-orienting function."),
    **diff("Cue visibility × validity in fixed blocks", "F(1,42)=14.00, p=.001, ηp²=.25; fixed effects 15.7 versus 2.1 ms.", "unaware>aware"),
    **meyen("supplementary"),
)
add("lin", 1, "Experiment 1 immediate orienting", base, [{"kind": "lin-A", "status": "complete"}])

base = comparison(
    experiment_label="Experiment 1: negative attentional aftereffect", X_label="previously repeated fixed cue location",
    X_description="After visible or invisible repeated fixed cues, the cue is removed and target detection is compared at old versus new locations.",
    Y_label="persistent location-based inhibition after repeated cueing",
    Y_description="A lasting priority cost at the formerly cued location in subsequent no-cue blocks.",
    Y_structure="scalar", E_code="E-uncontrolled", E_reason="Visible and invisible cue groups differ physically and in evidence; the larger visible aftereffect is compatible with a scalar evidence-strength account.",
    critical_comparison="Cue visibility × old/new target location during no-cue blocks.",
    unaware_capacity_claim="persistent inhibition of the previously cued location", unaware_capacity="unclear",
    unaware_capacity_reason="The invisible-cue aftereffect estimate is near zero and nonsignificant, without positive equivalence evidence.",
    unaware_capacity_critical_effect="1.6-ms old/new difference, t(23)=0.50, p=.621.", unaware_capacity_stats_status="unclear",
    unaware_capacity_stats_reason="Nonsignificance alone does not affirm absence or operation of persistent inhibition.",
    source_pages="pp. 4-6, Fig. 2, Table 2", source_figures_tables="Fig. 2; Table 2",
    stats_status="adequate", stats_flags=["none"], stats_reason="The awareness × old/new-location interaction is directly tested with estimates and effect size.",
    constraint_summary="A persistent negative attentional aftereffect is awareness-linked, but unmatched evidence prevents attribution solely to awareness and the unaware capacity remains unclear.",
    **lin_a, **diff("Cue visibility × old/new location", "F(1,42)=9.17, p=.004, ηp²=.18; visible -12.2 ms versus invisible 1.6 ms.", "aware>unaware"),
    **meyen("supplementary"),
)
add("lin", 1, "Experiment 1 attentional aftereffect", base, [{"kind": "lin-A", "status": "complete"}])

for kind, y, claim, effect, stats, pages in [
    ("immediate", "exogenous spatial orienting across fixed and random cue regimes", "exogenous spatial orienting of target detection by an invisible cue", "Fixed 15.6 ms, t(12)=4.13, p=.001; random 20.5 ms, t(13)=5.10, p<.001.", "adequate", "pp. 6-7, Table 2"),
    ("aftereffect", "persistent location-based inhibition after repeated cueing", "persistent inhibition of the previously cued location", "No-cue old/new difference -2.1 ms, t(12)=-0.41, p=.692.", "unclear", "pp. 6-7, Table 2"),
]:
    supported = kind == "immediate"
    base = comparison(
        experiment_label=f"Experiment 2: {kind}", X_label="16.7-ms masked fixed/random annulus cue",
        X_description="The cuing and direct location-discrimination tasks use identical trial counts and sequences.",
        awareness_measure="Matched-sequence forced-choice cue-location discrimination in fixed and random blocks.", awareness_evidence_type="objective-invisibility",
        objective_visibility_test_informative="yes", objective_visibility_test_reason="The direct task tests cue location over 420 trials with a 50% baseline; selected and group performance are reported at chance in each regime.",
        A_code="A-validated", A_reason="A separate but sequence-matched direct task validates invisibility in the same fixed/random regimes.",
        first_order_measure="Forced-choice cue-location discrimination.", E_code="E-uncontrolled",
        E_reason="Experiment 2 contains only an invisible main-task regime, so no matched aware-unaware evidence comparison is available.",
        Y_label=y, Y_description="Target-detection latency indexed by validity or former cue location.", Y_structure="factorial-functional" if supported else "scalar",
        factorial_Y_reason="Fixed and random cue regimes are components of the same spatial-orienting function." if supported else None,
        factorial_component_effects=([
            component("fixed", "fixed cue", "unaware", "15.6-ms cuing benefit.", "t(12)=4.13, p=.001", pages),
            component("random", "random cue", "unaware", "20.5-ms cuing benefit.", "t(13)=5.10, p<.001", pages),
        ] if supported else []),
        critical_comparison="Validity/old-new target-location effect in objectively unaware participants.",
        unaware_capacity_claim=claim, unaware_capacity="supported" if supported else "unclear",
        unaware_capacity_reason="Direct positive spatial-orienting effects occur in both fixed and random regimes." if supported else "The near-zero nonsignificant aftereffect is not positive evidence for the named function or equivalence.",
        unaware_capacity_critical_effect=effect, unaware_capacity_stats_status=stats,
        unaware_capacity_stats_reason="Direct within-unaware effects are well reported." if supported else "A bare nonsignificant old/new difference remains unclear.",
        awareness_effect="not-tested", awareness_effect_reason="Experiment 2 contains no aware main-task comparison.", direction=None,
        awareness_effect_critical_effect=None, awareness_effect_estimate=None, awareness_effect_estimate_interpretable="not-applicable",
        awareness_effect_stats_status="not-applicable", awareness_effect_stats_reason="No aware main-task condition is present.", difference_tested="not-applicable",
        source_pages=pages, source_figures_tables="Table 2", stats_status="adequate" if supported else "concern",
        stats_flags=["none"] if supported else ["weak-null-evidence"],
        stats_reason="The positive cuing effects are direct and replicated; the null aftereffect lacks positive null evidence.",
        constraint_summary=("Objectively validated unseen cues support exogenous spatial orienting in fixed and random regimes; awareness modulation is not tested."
                            if supported else "Persistent inhibition after unseen repeated cueing remains unresolved; awareness modulation is not tested."),
        **meyen("supplementary"),
    )
    add("lin", 2, f"Experiment 2 {kind}", base)

# Persaud et al.: one functional metacognition comparison and one F-not-meaningful neural contrast.
base = comparison(
    experiment_label="GY experiment: metacognitive monitoring", X_label="vertical-grating location in normal versus blind visual field",
    X_description="Low-contrast normal-field and high-contrast blind-field stimuli are titrated to comparable first-order discrimination accuracy.",
    awareness_measure="Trialwise Guess/Seen commentary report.", awareness_evidence_type="subjective",
    objective_visibility_test_informative="not-applicable", objective_visibility_test_reason="A is based on GY's direct subjective report; objective discrimination is used for E and is above chance in the blind field.",
    A_code="A-direct", A_reason="GY directly reports seeing on 43% of normal-field and 3% of blind-field trials.",
    first_order_measure="Up/down vertical-grating discrimination accuracy.", E_code="E-matched", E_matching_basis="active-matching-or-titration",
    E_reason="Separate staircases target 71% and 79% accuracy in each hemifield; observed accuracy 76% versus 79% did not differ (p=.34).",
    Y_label="metacognitive monitoring of first-order discrimination accuracy",
    Y_description="Trialwise wagering appropriately discriminates correct from incorrect visual decisions.", Y_structure="scalar",
    mechanistic_interpretation="Metacognitive sensitivity may relate to frontopolar/prefrontal function, but the behavioral monitoring function is independently defined.",
    critical_comparison="Difference between normal- and blind-field wagering-accuracy correlations.",
    unaware_capacity_claim="metacognitive monitoring of correct versus incorrect blind-field discriminations", unaware_capacity="unclear",
    unaware_capacity_reason="The blind-field correlation is r=.30, but no within-field significance or precision is reported for the exact positive capacity claim.",
    unaware_capacity_critical_effect="Blind-field wagering-accuracy correlation r=.30.", unaware_capacity_stats_status="unclear",
    unaware_capacity_stats_reason="The paper directly tests the between-field difference, not whether blind-field metacognitive sensitivity itself is reliably above zero.",
    source_pages="pp. 2-6, Figs. 1-2 and 5", source_figures_tables="Fig. 2; behavioral metacognition analysis on p. 4",
    stats_status="concern", stats_flags=["pseudoreplication"], stats_reason="The within-case comparison is statistically clear for GY but cannot establish population generalizability; trial independence and single-case inference limit scope.",
    constraint_summary="With first-order accuracy titrated, GY shows greater metacognitive monitoring in the normally seen field; positive metacognitive capacity in the blind field remains statistically unclear.",
    **diff("Fisher r-to-z difference in wagering-accuracy correlation", "Normal r=.52 versus blind r=.30, p<.001.", "aware>unaware"),
    **meyen("not-applicable"),
)
add("persaud", 1, "GY metacognitive monitoring", base)

base = comparison(
    experiment_label="GY experiment: frontoparietal BOLD contrast", X_label="vertical-grating stimulation in normal versus blind visual field",
    X_description="Performance-matched hemifield stimulation is contrasted in whole-brain BOLD activity.",
    awareness_measure="Trialwise Guess/Seen commentary report.", awareness_evidence_type="subjective",
    objective_visibility_test_informative="not-applicable", objective_visibility_test_reason="A is based on the direct subjective report.",
    A_code="A-direct", A_reason="GY reports markedly different visual phenomenology across fields.",
    first_order_measure="Up/down discrimination accuracy.", E_code="E-matched", E_matching_basis="active-matching-or-titration",
    E_reason="Observed discrimination accuracy is matched after hemifield-specific contrast titration.",
    Y_label="frontoparietal BOLD response", Y_description="Whole-brain activity difference associated with hemifield stimulation.",
    Y_structure="scalar", Y_evidence_role="mechanistic-support-only", F_code="F-not-meaningful",
    F_reason="A generic neural response does not itself identify a distinct downstream cognitive use of X.", Y_interpretation_clarity="unclear",
    mechanistic_interpretation="The activations may reflect awareness, metacognition, preparatory flexibility, or amplification; the paper explicitly leaves these alternatives unresolved.",
    mechanism_clarity="ambiguous", critical_comparison="Normal-field versus blind-field BOLD contrast.",
    unaware_capacity_claim="a distinct downstream function indexed by frontoparietal BOLD", unaware_capacity="not-tested",
    unaware_capacity_reason="The neural contrast does not operationalize a qualifying downstream function.", unaware_capacity_critical_effect=None,
    unaware_capacity_stats_status="not-applicable", unaware_capacity_stats_reason="No qualifying capacity route exists because F is not meaningful.",
    awareness_effect="not-tested", awareness_effect_reason="The F gate is structurally dead; the neural difference is retained only as mechanistic support.", direction=None,
    awareness_effect_critical_effect=None, awareness_effect_estimate=None, awareness_effect_estimate_interpretable="not-applicable",
    awareness_effect_stats_status="not-applicable", awareness_effect_stats_reason="No qualifying awareness-effect route exists.", difference_tested="not-applicable",
    source_pages="pp. 4-7, Figs. 3-6, Table 1", source_figures_tables="Figs. 3-6; Table 1",
    stats_status="concern", stats_flags=["pseudoreplication"], stats_reason="Whole-brain corrected clusters are reported for one neurological participant; functional interpretation and generalization are unresolved.",
    constraint_summary="The BOLD contrast is mechanistic support only and is excluded by F-not-meaningful from both scientific routes.",
    **meyen("not-applicable"),
)
add("persaud", 1, "GY frontoparietal BOLD", base)

# Tsushima et al.: five behavioral experiment groups; supplement-only details remain unresolved.
for exp, ystruct, pages, ecode, aware_effect, stats in [
    (1, "factorial-functional", "pp. 2-3, Figs. 1-2A", "E-diagnostic", "difference", "adequate"),
    (2, "factorial-functional", "p. 3, Fig. 2B", "E-diagnostic", "difference", "adequate"),
    (3, "factorial-functional", "p. 3 and unavailable supporting material", "E-uncontrolled", "unresolved", "unclear"),
    (4, "factorial-functional", "p. 3 and unavailable supporting material", "E-uncontrolled", "unresolved", "unclear"),
    (5, "factorial-functional", "pp. 3-4, Figs. 3-4", "E-uncontrolled", "unresolved", "concern"),
]:
    extras = {}
    if ecode == "E-diagnostic":
        extras.update(diagnostic_e(
            ["pp. 2-3, Fig. 2A", "p. 3, Fig. 2B"],
            "Increasing motion evidence merely increases the same distractor interference monotonically.",
            "Stronger coherent motion should produce equal or greater RSVP disruption than weaker motion, with no threshold-linked shift.",
            "Disruption peaks near the chance-level motion threshold, recovers at suprathreshold coherence, and both threshold and dip shift together when dot luminance is reduced.",
            "All components measure the same downstream RSVP disruption by the task-irrelevant motion field.",
        ))
    else:
        extras.update({"E_code": "E-uncontrolled", "E_reason": "Motion coherence and direct evidence vary without matching; the main article does not report enough experiment-specific structure to establish E-diagnostic independently.", "E_matching_basis": "none"})
    base = comparison(
        experiment_label=f"Experiment {exp}: motion-distractor regulation", X_label="task-irrelevant coherent background motion",
        X_description="Motion coherence varies around a separately estimated direction-discrimination threshold while participants perform central RSVP.",
        awareness_measure="Post-main four-alternative motion-direction discrimination threshold; experiment-specific detail is partly confined to unavailable supporting material.",
        awareness_evidence_type="objective-invisibility", objective_visibility_test_informative="unclear",
        objective_visibility_test_reason="The main article states chance-level performance at the critical coherence but omits trial counts, sensitivity, and full statistics in the unavailable supplement.",
        A_code="A-transfer-risk", A_reason="A separate objective validation exists, but the supplied main article is insufficient to establish its sensitivity and transfer for each experiment.",
        critical_dependency_status="unresolved", critical_dependency_reason="Classification-critical methods and results are explicitly delegated to supporting material that was not supplied and was not retrieved.",
        first_order_measure="Four-alternative coherent-motion direction discrimination.",
        Y_label="regulation/control of interference from a task-irrelevant motion distractor",
        Y_description="Maintaining central RSVP letter/digit performance despite irrelevant coherent background motion.",
        Y_structure=ystruct, factorial_Y_reason="Coherence levels jointly operationalize the same distractor-regulation function around perceptual threshold.",
        factorial_component_effects=[
            component("near-threshold", "near-threshold irrelevant motion", "unaware", "RSVP performance dip at/near chance-level motion threshold.", None, pages),
            component("suprathreshold", "suprathreshold irrelevant motion", "aware", "RSVP performance recovers relative to the near-threshold dip.", None, pages),
        ],
        critical_comparison="RSVP performance across near-threshold and suprathreshold motion coherence.",
        unaware_capacity_claim="effective regulation of interference from the task-irrelevant motion distractor", unaware_capacity="not-supported",
        unaware_capacity_reason="Near-threshold motion disrupts RSVP; this is a failure of the named regulation function, not positive unconscious control.",
        unaware_capacity_critical_effect="Threshold-linked RSVP disruption in the putatively unaware condition.", unaware_capacity_stats_status=stats,
        unaware_capacity_stats_reason="The disruption is directly tested in Experiments 1-2; experiment-specific statistics are incomplete for Experiments 3-5.",
        source_pages=pages, source_figures_tables=pages,
        stats_status=stats, stats_flags=["none"] if stats == "adequate" else ["other"],
        stats_reason="Main-text tests are adequate for Experiments 1-2; missing supplement detail limits the remaining experiments.",
        constraint_summary="The threshold-linked pattern is compatible with failed control of an unaware distractor, but A remains transfer-risk because validation sensitivity cannot be audited from the supplied file.",
        **extras, **meyen("inference-critical"),
    )
    if aware_effect == "difference":
        estimate = ("5% coherence RSVP d' lower than 0% and 20%, both p<.001." if exp == 1 else "30% coherence RSVP d' lower than 20% and 40%, both p<.01.")
        base.update(diff("Near-threshold versus suprathreshold RSVP performance", estimate, "qualitative-change"))
    else:
        base.update({"awareness_effect": "unresolved", "awareness_effect_reason": "The same qualitative pattern is stated, but the supplied article lacks a complete experiment-specific critical difference test.",
                     "direction": None, "awareness_effect_critical_effect": "Near-threshold versus suprathreshold RSVP pattern.",
                     "awareness_effect_estimate": "Qualitative same-pattern report; supplement details unavailable.",
                     "awareness_effect_estimate_interpretable": "unclear", "awareness_effect_stats_status": "unclear",
                     "awareness_effect_stats_reason": "Incomplete reporting in the supplied main article.", "difference_tested": "unclear"})
    bundles = ([{"kind": "tsushima-E", "status": "complete"}] if exp in {1, 2} else [])
    add("tsushima", exp, f"Experiment {exp}", base, bundles)


def placeholder(final: dict, paper_id: str, experiment_id: str, comparison_id: str) -> dict:
    row = deepcopy(final)
    row.update({"paper_id": paper_id, "experiment_id": experiment_id, "comparison_id": comparison_id})
    for field in [
        "X_label", "X_description", "awareness_measure", "awareness_evidence_type",
        "objective_visibility_test_informative", "objective_visibility_test_reason", "A_code", "A_reason",
        "critical_dependency_status", "critical_dependency_reason", "first_order_measure", "E_code", "E_reason",
        "E_matching_basis", "E_equivalence_margin", "E_equivalence_result", "E_competing_account",
        "E_competing_prediction", "E_violating_pattern", "E_same_Y_reason", "Y_label", "Y_description",
        "Y_structure", "factorial_Y_reason", "Y_evidence_role", "F_code", "F_reason",
        "Y_interpretation_clarity", "mechanistic_interpretation", "mechanism_clarity", "critical_comparison",
        "unaware_capacity_claim", "unaware_capacity", "unaware_capacity_reason", "unaware_capacity_critical_effect",
        "unaware_capacity_stats_status", "unaware_capacity_stats_reason", "awareness_effect", "awareness_effect_reason",
        "direction", "awareness_effect_critical_effect", "awareness_effect_estimate",
        "awareness_effect_estimate_interpretable", "awareness_effect_stats_status", "awareness_effect_stats_reason",
        "difference_tested", "null_evidence_strength", "null_evidence_adequacy", "null_equivalence_margin",
        "null_equivalence_result", "null_BF01", "null_CI_region", "null_CI_entirely_within_region",
        "Meyen_role", "Meyen_applicable", "Meyen_status", "Meyen_reason", "stats_status", "stats_reason",
        "constraint_summary", "source_pages", "source_figures_tables",
    ]:
        row[field] = None
    row.update({
        "evidence_bundle_ids": [], "structural_audit_status": "not-started",
        "awareness_effect_route_status": "not-assessed", "awareness_effect_route_reason": None,
        "unaware_capacity_route_status": "not-assessed", "unaware_capacity_route_reason": None,
        "null_equivalence_route_status": "not-assessed", "null_equivalence_route_reason": None,
        "result_inspection_status": "not-started", "result_inspection_reason": None,
        "E_diagnostic_source_locations": [], "factorial_component_effects": [], "stats_flags": [],
        "current_status": "identified", "notes": "Comparison structure reserved before scientific coding and evidence linkage.",
    })
    return row


def main() -> None:
    # One administrative manual-supply event records the bounded input set.
    search_id = allocate_identifier(RUN_DIR, "search")
    search_row = {
        "search_id": search_id, "run_id": RUN_ID, "wave": 0, "execution_phase": "administrative",
        "event_type": "manual-promotion", "discovery_route": "manual-suggestion", "parent_paper_id": None,
        "trigger_comparison_id": None, "normalized_y_label": None, "query_id": None, "query_text": None,
        "canonical_query": None, "source_parameters": {"scope": "workspace sources only", "count": 6},
        "publication_cutoff": None, "requested_max_n": None, "actual_returned_n": None,
        "window_key": None, "result_set_sha256": None, "retrieved_at": now(), "window_status": "not-applicable",
        "reused_search_id": None, "source": "user-supplied workspace sources/", "index_direction": "not-applicable",
        "started_at": now(), "completed_at": now(), "results_returned": 6, "new_unique_papers": 6,
        "status": "complete", "reason_or_notes": "Bounded pre-freeze diagnostic input registration; no search or retrieval was performed.",
    }
    log("search", search_id, "bounded-input-registration", "status", None, "complete",
        "The user supplied exactly six PDFs and prohibited literature search/retrieval.", "sources/")
    append("search_log.csv", search_row)

    paper_ids: dict[str, str] = {}
    experiment_ids: dict[tuple[str, int], str] = {}
    for rank, p in enumerate(PAPERS, start=1):
        pid = allocate_identifier(RUN_DIR, "paper")
        paper_ids[p["key"]] = pid
        url = doi_resolver_url(p["doi"])
        row = {
            "paper_id": pid, "title": p["title"], "authors": p["authors"], "year": p["year"], "doi": p["doi"], "url": url,
            "publication_status": "published", "first_discovery_route": "manual-suggestion", "first_discovery_parent": None,
            "first_discovery_query_id": None, "first_search_id": search_id, "first_seen_wave": 0,
            "title_screen": "retain", "title_screen_reason": "The supplied title plausibly concerns awareness of X and a distinct downstream cognitive or neural Y.",
            "title_screen_method": "agent-semantic", "title_screen_rule_id": None,
            "abstract_status": "available", "abstract_screen": "screen-in", "abstract_screen_reason": p["abstract"],
            "abstract_screen_method": "agent-semantic", "abstract_screen_rule_id": None,
            "fulltext_priority": "high", "fulltext_priority_reason": "The full text was supplied and the abstract contains the target X-awareness-Y structure.",
            "fulltext_status": "retrieved-published", "fulltext_source": f"sources/{p['source']}.pdf",
            "missing_text_priority": "none", "citation_expansion_status": "not-applicable",
            "citation_expansion_reason": "Citation expansion is intentionally out of scope for this bounded diagnostic.",
            "duplicate_of": None, "duplicate_reason": None, "current_status": "fulltext-evaluated",
            "notes": "Preexisting workspace PDF; no external retrieval or cross-run information used.",
        }
        for field, reason in [
            ("title_screen", row["title_screen_reason"]), ("abstract_screen", row["abstract_screen_reason"]),
            ("fulltext_status", "A published PDF was preexisting in sources/ at invocation."),
            ("citation_expansion_status", row["citation_expansion_reason"]),
        ]:
            log("paper", pid, f"paper-{field}", field, None, row[field], reason, f"sources/{p['source']}.pdf")
        append("papers_master.csv", row)

        did = allocate_identifier(RUN_DIR, "discovery")
        discovery = {
            "discovery_id": did, "search_id": search_id, "paper_id": pid, "result_rank": rank,
            "raw_title": p["title"], "raw_doi": p["doi"], "raw_url": url,
            "source_stable_id": f"sources/{p['source']}.pdf", "discovered_at": now(), "dedup_status": "new-paper",
            "dedup_reason": "Unique normalized DOI within the complete six-record supplied batch.",
            "notes": "Manual supplied-input provenance; no dynamic search result.",
        }
        log("discovery", did, "manual-source-discovery", "dedup_status", None, "new-paper",
            discovery["dedup_reason"], f"sources/{p['source']}.pdf")
        append("discoveries.csv", discovery)

        pdf_src = ROOT / "sources" / f"{p['source']}.pdf"
        txt_src = RUN_DIR / "fulltexts" / f"source_{p['source']}.txt"
        pdf_dst = RUN_DIR / "fulltexts" / f"{pid}_{p['source']}.pdf"
        txt_dst = RUN_DIR / "fulltexts" / f"{pid}_{p['source']}.txt"
        shutil.copyfile(pdf_src, pdf_dst)
        shutil.copyfile(txt_src, txt_dst)
        ftid = allocate_identifier(RUN_DIR, "fulltext_asset")
        asset = {
            "fulltext_asset_id": ftid, "paper_id": pid, "article_version": "publisher PDF as supplied",
            "source_identity": f"doi:{p['doi']}", "local_fulltext_path": str(pdf_dst.relative_to(ROOT)),
            "file_sha256": sha(pdf_dst), "verified_at": now(),
            "verification_reason": f"Title/DOI in the PDF match the supplied bibliographic identity; {p['pages']} PDF pages were extracted with page markers.",
            "acquisition_route": "preexisting user-supplied workspace source; no retrieval performed",
            "extraction_tool": "Swift PDFKit page.string", "extraction_version": "macOS-system-framework",
            "extracted_text_path": str(txt_dst.relative_to(ROOT)), "extracted_text_sha256": sha(txt_dst),
            "page_map_path": None, "page_map_sha256": None, "current_for_paper": True,
            "notes": "Extraction contains explicit 'PDF PAGE n' delimiters; no supplement was inferred when absent.",
        }
        log("fulltext_asset", ftid, "verified-fulltext-asset", "file_sha256", None, asset["file_sha256"],
            asset["verification_reason"], asset["local_fulltext_path"])
        append("fulltext_assets.csv", asset)

        for n in range(1, p["experiments"] + 1):
            eid = allocate_identifier(RUN_DIR, "experiment", pid)
            experiment_ids[(p["key"], n)] = eid
            role = "candidate-or-supporting experiment group reserved before comparison allocation"
            log("experiment", eid, "experiment-group-enumeration", "experiment_id", None, eid,
                role, f"{asset['local_fulltext_path']}; Experiment {n}")

    # One unavailable auxiliary work captures the monkey-awareness dependency.
    aux_id = allocate_identifier(RUN_DIR, "auxiliary")
    aux = {
        "auxiliary_id": aux_id,
        "citation": "Andersen LM, Basile BM, Hampton RR (2014). Dissociation of visual localization and visual detection in rhesus monkeys (Macaca mulatta). Animal Cognition 17:681-687.",
        "doi": None, "url": None,
        "identity_reason": "The complete citation is listed as reference 29 in the supplied Ben-Haim article and is explicitly invoked for monkey subjective 'stimulus not there' reports.",
        "article_version": "published version cited; exact file/version unavailable",
        "retrieval_status": "not-attempted", "local_fulltext_path": None, "file_sha256": None,
        "obtained_at": None, "obtained_by": None, "acquisition_route": None,
        "verification_reason": "Bibliographic identity is limited to the citation in the supplied article; the bounded diagnostic forbids retrieval.",
        "notes": "Unresolved classification-critical awareness-transfer dependency; not added to candidate papers/discoveries.",
    }
    log("auxiliary_source", aux_id, "auxiliary-dependency-recorded", "retrieval_status", None, "not-attempted",
        "The source is classification-critical for monkey awareness but retrieval is prohibited by the bounded diagnostic.", "Ben-Haim p. 8, ref. 29")
    append("auxiliary_sources.csv", aux)

    comp_records = []
    for spec in COMPARISONS:
        eid = experiment_ids[(spec["paper"], spec["exp"])]
        cid = allocate_identifier(RUN_DIR, "comparison", eid)
        spec["comparison_id"] = cid
        final = deepcopy(spec["row"])
        final.update({"paper_id": paper_ids[spec["paper"]], "experiment_id": eid, "comparison_id": cid,
                      "experiment_label": spec["label"]})
        log("comparison", cid, "comparison-structure", "comparison_id", None, cid,
            "This is one scalar or coherent factorial paper × experiment × X→Y comparison; distinct downstream functions are separate rows.", final["source_pages"] or "Supplied PDF")
        append("experiments_master.csv", placeholder(final, paper_ids[spec["paper"]], eid, cid))
        comp_records.append((spec, final))

    # Evidence bundles are created incomplete, populated with direct links, then derived to final status.
    for spec, final in comp_records:
        for bspec in spec["bundles"]:
            bid = allocate_identifier(RUN_DIR, "evidence_bundle")
            member_key = "required-source"
            premise = "awareness-A" if bspec["kind"] in {"monkey-A", "lin-A"} else "E-diagnostic"
            route = "awareness validation" if premise == "awareness-A" else "E-diagnostic"
            bundle = {
                "evidence_bundle_id": bid, "focal_comparison_id": final["comparison_id"], "supported_premise": premise,
                "premise_description": (
                    "Awareness status transfers to the focal comparison." if premise == "awareness-A" else
                    "The threshold-linked dip and its luminance-induced shift jointly violate monotonic evidence strength."
                ),
                "route_label": route, "required_member_keys": [member_key], "bundle_status": "incomplete",
                "bundle_reason": "Initialized before its required direct member link was written.", "notes": None,
            }
            log("evidence_bundle", bid, "evidence-bundle-created", "required_member_keys", None, [member_key],
                "The required-member manifest is fixed before evaluating the member outcome.", final["source_pages"])
            append("evidence_bundles.csv", bundle)
            lid = allocate_identifier(RUN_DIR, "evidence_link")
            if bspec["kind"] == "monkey-A":
                link = {
                    "evidence_link_id": lid, "evidence_bundle_id": bid, "member_key": member_key,
                    "focal_comparison_id": final["comparison_id"], "supporting_paper_id": None,
                    "supporting_experiment_id": None, "supporting_auxiliary_id": aux_id, "evidence_assessment_id": None,
                    "supporting_source_type": "external-auxiliary-source", "support_role": "awareness-validation",
                    "dependency_role": "required", "member_status": "unavailable",
                    "supported_claim": "The 17/33-ms monkey cue regime is subjectively reported as stimulus absent under transferable conditions.",
                    "transfer_reason": "The focal article invokes the same species and nominal masked durations.",
                    "transfer_limitation": "The auxiliary full text is unavailable; stimulus parameters, masking, timing, attention, task demands, and population transfer cannot be audited.",
                    "source_location": "Ben-Haim p. 8, ref. 29", "used_for_decision": False,
                    "notes": "Unavailable required member keeps the bundle incomplete and A at transfer-risk.",
                }
            elif bspec["kind"] == "lin-A":
                supporting_eid = experiment_ids[("lin", 2)]
                link = {
                    "evidence_link_id": lid, "evidence_bundle_id": bid, "member_key": member_key,
                    "focal_comparison_id": final["comparison_id"], "supporting_paper_id": paper_ids["lin"],
                    "supporting_experiment_id": supporting_eid, "supporting_auxiliary_id": None, "evidence_assessment_id": None,
                    "supporting_source_type": "within-paper-experiment", "support_role": "awareness-validation",
                    "dependency_role": "required", "member_status": "supports",
                    "supported_claim": "The fixed/random 16.7-ms cue regime yields chance cue-location discrimination with matched trial sequences.",
                    "transfer_reason": "Experiment 2 uses the same cue duration, masking, task sequence, fixed/random location regimes, participant population, and direct cue-location measure as the invisible conditions being validated.",
                    "transfer_limitation": "Experiment 2 uses an independent participant sample and fewer main-task blocks than Experiment 1.",
                    "source_location": "Lin & Murray pp. 6-7", "used_for_decision": True,
                    "notes": "Direct within-paper cross-experiment validation.",
                }
            else:
                supporting_exp = 2 if spec["exp"] == 1 else 1
                supporting_eid = experiment_ids[("tsushima", supporting_exp)]
                link = {
                    "evidence_link_id": lid, "evidence_bundle_id": bid, "member_key": member_key,
                    "focal_comparison_id": final["comparison_id"], "supporting_paper_id": paper_ids["tsushima"],
                    "supporting_experiment_id": supporting_eid, "supporting_auxiliary_id": None, "evidence_assessment_id": None,
                    "supporting_source_type": "within-paper-experiment", "support_role": "E-diagnostic-support",
                    "dependency_role": "required", "member_status": "supports",
                    "supported_claim": "Lowering dot luminance shifts both motion threshold and the same RSVP performance dip to higher coherence.",
                    "transfer_reason": "Experiments 1 and 2 use the same RSVP function and motion-distractor structure; luminance is deliberately changed to test the threshold-linked prediction.",
                    "transfer_limitation": "Full procedural and inferential detail is in unavailable supporting material, so A remains transfer-risk even though the reported same-Y shift supports E-diagnostic.",
                    "source_location": "Tsushima p. 3, Fig. 2A-B", "used_for_decision": True,
                    "notes": "Premise-specific same-Y E-diagnostic link.",
                }
            log("evidence_link", lid, "evidence-link-created", "member_status", None, link["member_status"],
                link["supported_claim"], link["source_location"])
            append("evidence_links.csv", link)
            final_status = bspec["status"]
            reason = ("All required direct members are evaluated, transfer-valid enough, and supportive."
                      if final_status == "complete" else "The required external awareness-validation member is unavailable.")
            log("evidence_bundle", bid, "evidence-bundle-status-derived", "bundle_status", "incomplete", final_status,
                reason, link["source_location"])
            bundle["bundle_status"] = final_status
            bundle["bundle_reason"] = reason
            upsert("evidence_bundles.csv", bundle, "evidence_bundle_id")
            final["evidence_bundle_ids"].append(bid)

    for spec, final in comp_records:
        cid = final["comparison_id"]
        decisions = [
            ("structural-audit", "structural_audit_status", final["structural_audit_status"], "X, awareness evidence, first-order evidence, conservative Y, scalar/factorial structure, and distinct-function boundaries were audited."),
            ("A-classification", "A_code", final["A_code"], final["A_reason"]),
            ("awareness-evidence-type", "awareness_evidence_type", final["awareness_evidence_type"], final["objective_visibility_test_reason"]),
            ("critical-dependency", "critical_dependency_status", final["critical_dependency_status"], final["critical_dependency_reason"]),
            ("F-classification", "F_code", final["F_code"], final["F_reason"]),
            ("Y-structure", "Y_structure", final["Y_structure"], final["Y_description"]),
            ("provisional-E", "E_code", "E-physical-only" if final["E_code"] == "E-diagnostic" else final["E_code"], "Methods were assessed before results; no positive equivalence route was inferred from nonsignificance."),
            ("final-E", "E_code", final["E_code"], final["E_reason"]),
            ("route-audit", "route_statuses", {"awareness": final["awareness_effect_route_status"], "unaware": final["unaware_capacity_route_status"]}, final["awareness_effect_route_reason"] + " " + final["unaware_capacity_route_reason"]),
            ("unaware-capacity-claim", "unaware_capacity_claim", final["unaware_capacity_claim"], final["unaware_capacity_reason"]),
            ("unaware-capacity", "unaware_capacity", final["unaware_capacity"], final["unaware_capacity_stats_reason"]),
            ("awareness-effect", "awareness_effect", final["awareness_effect"], final["awareness_effect_reason"]),
            ("statistics", "stats_status", final["stats_status"], final["stats_reason"]),
            ("null-equivalence-audit", "null_evidence_adequacy", final["null_evidence_adequacy"], final["null_equivalence_route_reason"]),
            ("Meyen-audit", "Meyen_role", final["Meyen_role"], final["Meyen_reason"]),
            ("constraint", "constraint_summary", final["constraint_summary"], "The statement keeps unaware capacity and awareness effect distinct and does not exceed the reported evidence."),
            ("result-inspection", "result_inspection_status", final["result_inspection_status"], final["result_inspection_reason"]),
        ]
        for dtype, field, value, reason in decisions:
            log("comparison", cid, dtype, field, None, value, reason, final["source_pages"])
        log("comparison", cid, "comparison-finalization", "current_status", "identified", "fully-evaluated",
            "All applicable design, route, result, statistical, Meyen, dependency, and source-location fields were completed; unresolved gaps remain explicit.", final["source_pages"])
        upsert("experiments_master.csv", final, "comparison_id")

    log("run", RUN_ID, "diagnostic-classification-checkpoint", "scope", None,
        {"papers": len(PAPERS), "comparisons": len(COMPARISONS)},
        "All supplied PDFs were evaluated without search/retrieval; the run remains non-complete because discovery and stopping rules are intentionally out of scope.", "runs/PREFREEZE_DIAG_20260819/")
    print(json.dumps({"papers": paper_ids, "comparisons": len(COMPARISONS)}, indent=2))


if __name__ == "__main__":
    main()
