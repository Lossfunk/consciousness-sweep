from __future__ import annotations

import argparse
import csv
import json
import sys
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUN_ID = "PREFREEZE_DIAG_004"
RUN_DIR = ROOT / "runs" / RUN_ID
sys.path.insert(0, str(ROOT / "tools"))

from structured_write import (  # noqa: E402
    allocate_identifier,
    append_jsonl_record,
    load_schema,
    validate_record,
    write_csv_record,
)


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


SCHEMAS = {
    "decision": load_schema(ROOT, "decision_log.schema.json"),
    "experiment": load_schema(ROOT, "experiments.schema.json"),
    "bundle": load_schema(ROOT, "evidence_bundles.schema.json"),
    "link": load_schema(ROOT, "evidence_links.schema.json"),
    "paper": load_schema(ROOT, "papers.schema.json"),
}


EXPERIMENTS = [
    ("P000001", "P000001_E01", "Experiment 1 - human spatial cueing", "factorial-functional-required", "Cue visibility and incongruent-versus-baseline cue structure jointly define one cue-guided target-selection mapping.", "P000001 main PDF pp. 2-5, Fig. 1"),
    ("P000001", "P000001_E02", "Experiment 2 - rhesus spatial cueing", "factorial-functional-required", "The same visibility-by-cue-structure mapping is tested in rhesus monkeys.", "P000001 main PDF pp. 4-5, Fig. 2"),
    ("P000001", "P000001_E03", "Experiment 3 - human forced guessing", "factorial-functional-required", "Visible and subliminal cue regimes produce opposite choice mappings relative to chance.", "P000001 main PDF pp. 5-6, Fig. 3"),
    ("P000001", "P000001_E04", "Experiment 4 - rhesus forced guessing", "factorial-functional-required", "Visible and subliminal cue regimes form one forced-choice rule-use mapping.", "P000001 main PDF p. 6, Fig. 3"),
    ("P000001", "P000001_E05", "Experiment 5 - sparse supraliminal control", "not-applicable", "This control tests whether sparse visible trials suffice for rule learning; it supports another comparison but lacks an unaware-X condition of its own.", "P000001 main PDF p. 7, Fig. 4A"),
    ("P000001", "P000001_E06", "Experiment 6 - instruction manipulation", "factorial-functional-required", "Pre/post instruction phases with the same brief cue jointly define the forced-choice mapping, though instruction is a confounded task-state change.", "P000001 main PDF p. 7, Fig. 4B-C"),
    ("P000001", "P000001_E07", "Experiment 7 - trialwise visibility", "factorial-functional-required", "Trialwise visibility ratings and opposite-choice performance define one awareness-conditioned rule-use mapping under fixed instructions.", "P000001 main PDF pp. 7-8, Fig. 4D"),
    ("P000002", "P000002_E01", "Single experiment - mask configuration, binding, and evaluation", "factorial-functional-required", "Orientation-by-location repetition is the binding function and masking tests that whole interaction; simple cells are components, not separate Ys.", "P000002 main PDF pp. 2-5, Figs. 1-3"),
    ("P000003", "P000003_E01", "Experiment 1 - CFS spatial cueing", "factorial-functional-required", "Cue relevance and cue-target location jointly define a single spatial-target-selection mapping whose awareness modulation is the critical three-way interaction.", "P000003 main PDF pp. 2-4, Fig. 2"),
    ("P000003", "P000003_E02", "Experiment 2 - CFS with localization validation", "factorial-functional-required", "The same cue-relevance-by-location mapping is tested with an added objective visibility check.", "P000003 main PDF pp. 5-6, Figs. 2 and 4"),
    ("P000003", "P000003_E03", "Experiment 3 - brief exposure spatial cueing", "factorial-functional-required", "Cue-target color relation and location jointly define the focal target-selection mapping.", "P000003 main PDF pp. 7-8, Fig. 2"),
    ("P000004", "P000004_E01", "Experiment 1 - repeated cuing", "factorial-functional-required", "Fixed-cue, no-cue, and random-cue phases jointly operationalize temporal allocation of spatial priority; their awareness interaction is the focal mapping.", "P000004 main PDF pp. 2-5, Fig. 2"),
    ("P000004", "P000004_E02", "Experiment 2 - matched visibility validation", "factorial-functional-required", "Fixed, no-cue, and random phases jointly operationalize the same temporal spatial-priority mapping in an objectively invisible regime.", "P000004 main PDF pp. 6-7"),
    ("P000004", "P000004_E03", "Experiment 3 - visible 100-ms SOA control", "not-applicable", "This visible-only control supports robustness of Experiment 1 but contains no aware/unaware contrast and no unaware-capacity test.", "P000004 main PDF p. 7"),
    ("P000005", "P000005_E01", "Single blindsight fMRI experiment", "scalar-justified", "Metacognitive calibration and regional BOLD activation are distinct downstream outputs and therefore receive separate scalar comparisons.", "P000005 main PDF pp. 2-5, Figs. 2-5"),
    ("P000006", "P000006_E01", "Experiment 1 - translating dots", "factorial-functional-required", "Motion-coherence levels jointly define the threshold-linked distractor-interference function.", "P000006 main PDF pp. 2-3, Fig. 2A; supplement pp. 2-4"),
    ("P000006", "P000006_E02", "Experiment 2 - low-contrast dots", "factorial-functional-required", "Motion-coherence levels jointly define the shifted threshold-linked interference function.", "P000006 main PDF p. 3, Fig. 2B; supplement p. 4"),
    ("P000006", "P000006_E03", "Experiment 3 - eye-movement control", "factorial-functional-required", "The coherence-level pattern is one distractor-interference mapping with eye movements monitored.", "P000006 main PDF p. 3; supplement pp. 4-5"),
    ("P000006", "P000006_E04", "Experiment 4 - contracting dots", "factorial-functional-required", "Contracting-motion coherence levels jointly define the threshold-linked distractor-interference function.", "P000006 main PDF p. 3; supplement pp. 5-6, Fig. S2"),
    ("P000006", "P000006_E05", "Experiment 5 - fMRI contracting dots", "factorial-functional-required", "Coherence levels jointly define the behavioral interference function; MT+ and LPFC BOLD are treated as mechanistic support rather than separate qualifying Ys.", "P000006 main PDF pp. 3-4, Figs. 3-4; supplement pp. 6-9"),
]


def comp_effect(component_id: str, relation: str, awareness: str, effect: str, stat: str | None, location: str) -> dict:
    return {
        "component_id": component_id,
        "X_task_relation": relation,
        "awareness_condition": awareness,
        "effect_description": effect,
        "statistical_result": stat,
        "source_location": location,
    }


def make_row(*, cid: str, eid: str, label: str, x: str, xdesc: str, awareness_measure: str,
             proc: str, evtype: str, obj: str, obj_reason: str | None, A: str, A_reason: str,
             A_result: str, A_location: str, E: str, E_reason: str, Y: str, Ydesc: str,
             components: list[dict], F: str, F_reason: str, cap: str, cap_effect: str | None,
             cap_stats: str, aw: str, aw_effect: str | None, aw_est: str | None,
             aw_stats: str, diff: str, pages: str, figs: str, constraint: str,
             structure: str = "factorial-functional-required", identity: str = "common-operational-mapping",
             Y_structure: str = "factorial-functional", critical_dependency: str = "checked-none",
             dependency_reason: str = "The supplied article record was checked and no unresolved external classification-critical dependency was needed.",
             alt_scan: str = "completed-none-found", alt_reason: str = "The entire supplied article record was scanned for a same-Y control; no additional classification-changing control was required.",
             E_competing: str | None = None, E_prediction: str | None = None,
             E_violation: str | None = None, E_same_y: str | None = None,
             Meyen_role: str = "not-applicable", Meyen_status: str | None = None,
             Meyen_reason: str = "The inference does not take the direct-chance plus positive-indirect-effect form requiring the Meyen diagnostic.",
             stats: str = "adequate", flags: list[str] | None = None, stats_reason: str = "The critical same-Y effect or interaction was directly tested and reported with an interpretable estimate.",
             null_strength: str = "not-applicable", null_adequacy: str = "not-applicable",
             notes: str | None = None, mech: str = "The paper proposes a mechanism, but the comparison is coded at the conservative behavioral function level.",
             mechanism_clarity: str = "ambiguous", a_bundle: bool = False,
             e_control: tuple[str, str, str] | None = None) -> dict:
    paper_id = cid[:7]
    strong_A = A in {"A-direct", "A-validated"}
    strong_E = E in {"E-matched", "E-diagnostic"}
    meaningful = F == "F-meaningful"
    awareness_route = "viable" if strong_A and strong_E and meaningful else "not-viable"
    capacity_route = "viable" if strong_A and meaningful else "not-viable"
    if cap == "not-tested":
        cap_scope, cap_stat_reason = "not-applicable", "No unaware-X test of this focal Y was reported."
    else:
        cap_scope, cap_stat_reason = ("whole-focal-Y" if cap == "supported" else "unclear"), cap_stats
    if aw == "not-tested":
        aw_est_interp, aw_stat_reason = "not-applicable", "No direct same-Y aware/unaware comparison was performed."
    else:
        aw_est_interp, aw_stat_reason = ("yes" if diff == "yes" else "unclear"), aw_stats
    null_required = aw == "no-detectable-difference"
    row = {
        "comparison_id": cid, "experiment_id": eid, "paper_id": paper_id, "experiment_label": label,
        "X_label": x, "X_description": xdesc, "awareness_measure": awareness_measure,
        "awareness_procedure_type": proc, "awareness_evidence_type": evtype,
        "objective_visibility_test_informative": obj, "objective_visibility_test_reason": obj_reason,
        "A_code": A, "A_reason": A_reason,
        "awareness_result_status": "supportive-result-reported" if strong_A else ("result-unavailable" if A == "A-transfer-risk" else "not-applicable"),
        "awareness_result_procedure_type": proc if A != "A-absent" else "not-applicable",
        "awareness_result_description": A_result,
        "awareness_result_source_location": A_location if A != "A-absent" else None,
        "awareness_result_source_experiment_id": eid if strong_A else None,
        "critical_dependency_status": critical_dependency, "critical_dependency_reason": dependency_reason,
        "evidence_bundle_ids": [], "structural_audit_status": "complete",
        "awareness_effect_route_status": awareness_route,
        "awareness_effect_route_reason": "Strong A, strong E, and F-meaningful are all present." if awareness_route == "viable" else "At least one of strong A, strong E, or F-meaningful is absent.",
        "unaware_capacity_route_status": capacity_route,
        "unaware_capacity_route_reason": "Strong A and F-meaningful permit the unaware-capacity route; E is not a gate." if capacity_route == "viable" else "Strong A and F-meaningful are not both established.",
        "null_equivalence_route_status": "required" if null_required else "not-required",
        "null_equivalence_route_reason": "A direct null-oriented same-Y test requires a descriptive null audit." if null_required else "The focal result is not a null-oriented invariance claim requiring equivalence assessment.",
        "result_inspection_status": "completed-viable-routes" if meaningful else "not-required",
        "result_inspection_reason": "Results were inspected for every viable route and for the direct same-Y comparison." if meaningful else "F is not meaningful, so no strong functional route is available; the descriptive direct result was still audited.",
        "first_order_measure": awareness_measure,
        "E_code": E, "E_reason": E_reason,
        "E_matching_basis": "active-matching-or-titration" if E == "E-matched" else "none",
        "E_equivalence_margin": None, "E_equivalence_result": "not-applicable",
        "E_competing_account": E_competing, "E_competing_prediction": E_prediction,
        "E_violating_pattern": E_violation, "E_same_Y_reason": E_same_y,
        "E_diagnostic_source_locations": [figs] if E == "E-diagnostic" else [],
        "alternative_control_scan_status": "not-required" if E == "E-matched" else alt_scan,
        "alternative_control_scan_reason": "Positive active matching establishes E without an unmatched-case control scan." if E == "E-matched" else alt_reason,
        "Y_label": Y, "Y_description": Ydesc,
        "functional_structure_assessment": structure, "functional_identity_basis": identity,
        "functional_structure_reason": "The recorded component cells jointly test one conservative input-to-output mapping." if structure == "factorial-functional-required" else "The two rows use distinct downstream outputs and are scientifically separable.",
        "factorial_focal_comparison_id": None, "Y_structure": Y_structure,
        "factorial_Y_reason": "The interaction or structured cell pattern is the scientific question and would be lost by scalar-only decomposition." if Y_structure == "factorial-functional" else None,
        "factorial_component_effects": components if Y_structure == "factorial-functional" else [],
        "Y_evidence_role": "downstream-functional-measure" if meaningful else "mechanistic-support-only",
        "F_code": F, "F_reason": F_reason,
        "Y_interpretation_clarity": "clear" if meaningful else "unclear",
        "mechanistic_interpretation": mech, "mechanism_clarity": mechanism_clarity,
        "critical_comparison": "The awareness-conditioned same-Y interaction or contrast reported in the cited source.",
        "unaware_capacity_claim": Y, "unaware_capacity_evidence_scope": cap_scope,
        "unaware_capacity": cap, "unaware_capacity_reason": "The reported unaware-condition effect was evaluated for the whole named focal Y." if cap != "not-tested" else "No unaware-condition test of this focal Y was available.",
        "unaware_capacity_critical_effect": cap_effect, "unaware_capacity_stats_status": ("not-applicable" if cap == "not-tested" else cap_stats),
        "unaware_capacity_stats_reason": cap_stat_reason,
        "awareness_effect": aw, "awareness_effect_reason": "The direct same-Y comparison was classified under the route gates and reported statistics.",
        "direction": ("no-detectable-difference" if aw == "no-detectable-difference" else ("qualitative-change" if aw != "not-tested" else "other")),
        "awareness_effect_critical_effect": aw_effect, "awareness_effect_estimate": aw_est,
        "awareness_effect_estimate_interpretable": aw_est_interp,
        "awareness_effect_stats_status": ("not-applicable" if aw == "not-tested" else aw_stats),
        "awareness_effect_stats_reason": aw_stat_reason, "difference_tested": ("not-applicable" if aw == "not-tested" else diff),
        "null_evidence_strength": null_strength, "null_evidence_adequacy": null_adequacy,
        "null_equivalence_margin": None, "null_equivalence_result": "not-applicable", "null_BF01": None,
        "null_CI_region": None, "null_CI_entirely_within_region": "not-applicable",
        "Meyen_role": Meyen_role, "Meyen_applicable": "yes" if Meyen_role != "not-applicable" else "no",
        "Meyen_status": Meyen_status, "Meyen_reason": Meyen_reason,
        "stats_status": stats, "stats_flags": flags or ["none"], "stats_reason": stats_reason,
        "constraint_summary": constraint, "source_pages": pages, "source_figures_tables": figs,
        "current_status": "fully-evaluated", "notes": notes,
        "_a_bundle": a_bundle, "_e_control": e_control,
    }
    return row


ROWS: list[dict] = []


def add(**kwargs) -> None:
    ROWS.append(make_row(**kwargs))


def fc(cid, eid, label, location, unaware_effect, aware_effect):
    return [
        comp_effect("unaware", "focal mapping under unawareness", "unaware", unaware_effect, None, location),
        comp_effect("aware", "focal mapping under awareness", "aware", aware_effect, None, location),
    ]


# Ben-Haim et al. (2021)
add(cid="P000001_E01_C01", eid="P000001_E01", label=EXPERIMENTS[0][2], x="incongruent spatial cue", xdesc="A masked 17/33-ms or 250-ms star cue predicts the target at the opposite location.", awareness_measure="Postcondition self-report plus forced-choice cue localization", proc="mixed", evtype="mixed", obj="yes", obj_reason="The end-of-experiment localization test had a chance baseline and the main article reports chance at individual and group levels.", A="A-direct", A_reason="Same-experiment subjective and objective results support unawareness of subliminal cues and awareness of supraliminal predictive cues.", A_result="No subliminal cues were reported and localization did not differ from chance; supraliminal predictive cues were consciously used.", A_location="P000001 main PDF pp. 2-5", E="E-physical-only", E_reason="Cue duration and internal evidence differ; the sign reversal is confounded with explicitly learned cue predictiveness, an anchored task-state difference.", Y="cue-guided regulation of spatial target selection", Ydesc="How an incongruent predictive cue changes saccadic target-selection speed and pretarget gaze relative to a nonpredictive baseline.", components=fc("", "", "", "P000001 main PDF pp. 3-5", "Subliminal cue slowed target selection and gaze remained at the cue.", "Aware supraliminal cue sped selection and gaze shifted to the target."), F="F-meaningful", F_reason="Target-selection regulation is a distinct downstream use of cue location and contingency.", cap="supported", cap_effect="Subliminal incongruent cue slowed responses versus baseline, F(1,2989)=13.36, p<.0001.", cap_stats="adequate", aw="unresolved", aw_effect="Subliminal versus supraliminal response-time contrast F(1,3585)=315.66, p<.0001.", aw_est="Opposite slowing versus facilitation relative to matched-duration baselines.", aw_stats="adequate", diff="yes", pages="P000001 main PDF pp. 2-5", figs="P000001 main PDF Fig. 1", constraint="Humans showed unconscious cue-driven interference, but the awareness-effect attribution is unresolved because first-order evidence and learned contingency knowledge were not independently controlled.", critical_dependency="unresolved", dependency_reason="The main article reports the critical results, but the unsupplied SI Appendix contains detailed procedures and exclusions.", alt_scan="completed-candidate-evaluated", alt_reason="Experiments 5-7 address rule learning in forced guessing, but not this same spatial-cueing Y; the learned-contingency alternative remains.", Meyen_role="supplementary", Meyen_status="Meyen-unassessable", Meyen_reason="Dedicated self-report and localization evidence independently support A, but no comparable-scale indirect-task advantage analysis is reported.", a_bundle=True)
add(cid="P000001_E02_C01", eid="P000001_E02", label=EXPERIMENTS[1][2], x="incongruent spatial cue", xdesc="Rhesus monkeys received 17/33-ms or 250-ms predictive cues before target selection.", awareness_measure="No monkey-specific qualifying awareness result; durations were transferred from humans and prior literature", proc="other", evtype="objective-invisibility", obj="unclear", obj_reason="No supplied monkey-specific objective visibility result establishes unawareness for the focal regimes.", A="A-transfer-risk", A_reason="Behavioral analogy and transferred durations do not provide a qualifying monkey-specific awareness result.", A_result="The main article explicitly states that subjective reports were not collected from monkeys.", A_location="P000001 main PDF p. 8", E="E-physical-only", E_reason="First-order evidence differs with duration and the monkey awareness regimes are not independently established.", Y="cue-guided regulation of spatial target selection", Ydesc="How predictive cue location changes saccadic target-selection speed and gaze relative to baseline.", components=fc("", "", "", "P000001 main PDF pp. 4-5", "Short cue slowed target selection versus baseline.", "Long cue sped target selection versus baseline."), F="F-meaningful", F_reason="Saccadic target-selection regulation is a defensible downstream function.", cap="unclear", cap_effect="Short-cue slowdown versus baseline F(1,1737)=7.14, p=.007, but unawareness is not established.", cap_stats="adequate", aw="unresolved", aw_effect="Short- versus long-cue response-time contrast F(1,4066)=7.66, p=.006.", aw_est="Opposite baseline-relative effects.", aw_stats="concern", diff="yes", pages="P000001 main PDF pp. 4-5 and 8", figs="P000001 main PDF Fig. 2", constraint="The monkeys show a behavioral crossover, but the supplied record does not establish the required monkey-specific awareness contrast.", critical_dependency="unresolved", dependency_reason="The article relies on an external monkey study and human thresholds; neither a monkey-specific critical result nor the external full text is supplied.", alt_scan="completed-candidate-evaluated", alt_reason="Human control experiments do not repair monkey-specific A or the learned-contingency contrast.", stats="concern", flags=["other"], stats_reason="The critical models use thousands of trials from four monkeys; the supplied main text does not expose enough random-effects detail to rule out trial-level pseudoreplication.")
add(cid="P000001_E03_C01", eid="P000001_E03", label=EXPERIMENTS[2][2], x="incongruent reward-location cue", xdesc="A visible or 17/33-ms masked cue marks the unrewarded target, so correct choice requires choosing opposite.", awareness_measure="Postexperiment self-report plus forced-choice cue localization", proc="mixed", evtype="mixed", obj="yes", obj_reason="The main article reports individual- and group-level chance localization for subliminal cues.", A="A-direct", A_reason="Same-experiment subjective and objective results support the subliminal/visible awareness contrast.", A_result="Participants denied cue influence and localized subliminal cues at chance; visible cues supported about 94.6% correct rule use.", A_location="P000001 main PDF pp. 5-6", E="E-diagnostic", E_reason="With a later same-Y control holding explicit instructions fixed, opposite choice relative to chance violates simple evidence-strength scaling.", Y="rule-guided selection of the target opposite an incongruent cue", Ydesc="Use of cue location to choose the opposite reward target.", components=fc("", "", "", "P000001 main PDF pp. 5-6", "Subliminal performance was systematically below chance.", "Supraliminal performance was about 94.6% correct."), F="F-meaningful", F_reason="Choosing by an instructed/learned spatial rule is a distinct downstream use of cue location.", cap="supported", cap_effect="Subliminal choices were nonrandom and systematically cue-congruent; lowest-binomial-p quartile 42% versus 25%, chi-square p=.021.", cap_stats="concern", aw="difference-supported", aw_effect="Visible performance about 94.6% versus systematic below-chance subliminal performance.", aw_est="Qualitative reversal around 50% chance.", aw_stats="adequate", diff="yes", pages="P000001 main PDF pp. 5-8", figs="P000001 main PDF Figs. 3-4", constraint="Human forced-choice rule use changes qualitatively with cue awareness; unaware cues still systematically govern choices in the opposite direction.", critical_dependency="unresolved", dependency_reason="Critical results are in the main article, but exact preregistered analyses and awareness-test details are in an unsupplied SI Appendix.", alt_scan="completed-candidate-evaluated", alt_reason="Experiment 7 is a same-Y control with fixed instructions and trialwise awareness and is linked in the E bundle.", E_competing="More first-order cue evidence merely strengthens the same cue-guided choice mapping.", E_prediction="Visible and less-visible cues should bias choices in the same direction, with a larger effect when visible.", E_violation="Performance reverses from below chance when unseen to strongly above chance when seen; Experiment 7 reproduces reversal with fixed instructions.", E_same_y="All cells measure choosing the reward target opposite the cue.", Meyen_role="supplementary", Meyen_status="Meyen-unassessable", Meyen_reason="Dedicated subjective and localization validation independently support A, but no comparable-scale sensitivity advantage is reported.", a_bundle=True, e_control=("P000001_E07", "P000001 main PDF pp. 7-8, Fig. 4D", "Fixed instructions with trialwise visibility reproduce the same forced-choice reversal."), stats="concern", flags=["other"], stats_reason="The group subliminal result is expressed through a distribution of individual binomial p-values rather than a direct group effect estimate, although the aware/unaware reversal is clear.")
add(cid="P000001_E04_C01", eid="P000001_E04", label=EXPERIMENTS[3][2], x="incongruent reward-location cue", xdesc="Rhesus monkeys choose between two targets after visible or masked cueing.", awareness_measure="No monkey-specific qualifying awareness result", proc="other", evtype="objective-invisibility", obj="unclear", obj_reason="The supplied paper contains no focal monkey visibility test.", A="A-transfer-risk", A_reason="Human transfer and behavioral analogy cannot establish monkey awareness under the protocol.", A_result="No monkey subjective report or focal objective visibility result is supplied.", A_location="P000001 main PDF p. 8", E="E-physical-only", E_reason="Cue evidence differs and A is transfer-risk.", Y="rule-guided selection of the target opposite an incongruent cue", Ydesc="Use of cue location to choose the opposite rewarded target.", components=fc("", "", "", "P000001 main PDF p. 6", "Masked-cue performance was 43.5%, below chance.", "Visible-cue performance reached the 80% learning criterion."), F="F-meaningful", F_reason="Reward-location rule use is a distinct downstream function.", cap="unclear", cap_effect="Masked-cue mean 43.5%, combined binomial p=.00018, but monkey unawareness is not established.", cap_stats="adequate", aw="unresolved", aw_effect="Visible success versus masked below-chance choice.", aw_est="Qualitative reversal around chance.", aw_stats="concern", diff="yes", pages="P000001 main PDF pp. 6 and 8", figs="P000001 main PDF Fig. 3D-E", constraint="Monkeys show a cue-dependent behavioral reversal, but awareness-specific interpretation remains unresolved.", critical_dependency="unresolved", dependency_reason="Monkey awareness validation is borrowed from human regimes and an external source not supplied.", alt_scan="completed-candidate-evaluated", alt_reason="Human controls do not resolve monkey-specific awareness or first-order evidence.", stats="concern", flags=["other"], stats_reason="Combined binomial evidence is reported across four monkeys, but no direct monkey-level aware/unaware interaction estimate is supplied.")
add(cid="P000001_E06_C01", eid="P000001_E06", label=EXPERIMENTS[5][2], x="33-ms incongruent reward-location cue", xdesc="The same brief cue is presented before and after participants are informed that cues may occur.", awareness_measure="Self-report of seeing and using cues before and after instruction", proc="subjective-visibility", evtype="subjective", obj="not-applicable", obj_reason="A subjective awareness classification is used; no objective invisibility claim is required for the seen subgroup.", A="A-direct", A_reason="Same-experiment reports distinguish preinstruction unseen from postinstruction seen trials/participants.", A_result="None reported seeing cues before information; afterward 50% reported seeing cues and most seers reported using them.", A_location="P000001 main PDF p. 7", E="E-uncontrolled", E_reason="Instruction and explicit task-relation knowledge change at the same time as awareness, an anchored unresolved task-state alternative.", Y="rule-guided selection of the target opposite an incongruent cue", Ydesc="Use of the brief cue to implement the opposite-target reward rule.", components=fc("", "", "", "P000001 main PDF p. 7", "Before information, performance was below chance.", "After information, aware participants approached supraliminal performance."), F="F-meaningful", F_reason="Spatial rule-guided choice is a distinct downstream function.", cap="supported", cap_effect="Preinstruction below-chance performance chi-square p=.028.", cap_stats="concern", aw="unresolved", aw_effect="Postinstruction aware participants improved to at least 95% peak accuracy while preinstruction performance was below chance.", aw_est="Large qualitative pre/post change without a clean same-state contrast.", aw_stats="concern", diff="yes", pages="P000001 main PDF p. 7", figs="P000001 main PDF Fig. 4B-C", constraint="The brief cue affects choices before reported awareness, but the pre/post awareness effect is confounded with instruction and explicit rule knowledge.", critical_dependency="unresolved", dependency_reason="Exact subgroup counts and analyses depend on the unsupplied SI Appendix.", alt_scan="completed-candidate-evaluated", alt_reason="Experiment 7 controls instruction under the same general Y, but cannot erase the direct pre/post instruction confound in Experiment 6.", stats="concern", flags=["other"], stats_reason="The key postinstruction result is conditional on self-reported seers and a peak-25-trial criterion; a direct pre/post same-Y interaction is not reported.")
add(cid="P000001_E07_C01", eid="P000001_E07", label=EXPERIMENTS[6][2], x="17-ms incongruent reward-location cue", xdesc="Participants are instructed from the outset to choose opposite the cue and rate visibility on each trial.", awareness_measure="Trialwise 0-3 subjective cue-location visibility rating", proc="subjective-visibility", evtype="subjective", obj="not-applicable", obj_reason="A direct trialwise subjective classification is used.", A="A-direct", A_reason="The awareness report is obtained on every focal trial under fixed instructions.", A_result="Choices were below chance at rating 0 and above chance at ratings 2-3; the awareness-by-performance association was significant.", A_location="P000001 main PDF pp. 7-8", E="E-diagnostic", E_reason="Physical cues and instructions are fixed; the sign reversal across trialwise visibility violates simple scalar evidence strengthening.", Y="rule-guided selection of the target opposite an incongruent cue", Ydesc="Use of cue location to implement the instructed opposite-target rule.", components=fc("", "", "", "P000001 main PDF pp. 7-8", "Rating-0 choices were significantly below chance.", "Rating-2/3 choices were significantly above chance."), F="F-meaningful", F_reason="Rule-guided spatial choice is a distinct downstream use of cue location.", cap="supported", cap_effect="Rating-0 performance was significantly below chance, showing nonrandom cue-driven choices.", cap_stats="adequate", aw="difference-supported", aw_effect="Awareness-level performance association chi-square(3)=24.8, p<.0001 with reversal around chance.", aw_est="Below chance at rating 0; above chance at ratings 2-3.", aw_stats="adequate", diff="yes", pages="P000001 main PDF pp. 7-8", figs="P000001 main PDF Fig. 4D", constraint="With instructions and cue duration fixed, cue awareness qualitatively changes rule-guided choice, while unseen cues still drive systematic opposite-to-goal responses.", critical_dependency="unresolved", dependency_reason="The main article reports the critical pattern, but exact cell counts are in the unsupplied SI Appendix.", alt_scan="completed-candidate-evaluated", alt_reason="The full supplied article was scanned; fixed instructions directly address the learned-rule alternative.", E_competing="More first-order cue evidence merely strengthens a single cue-driven choice tendency.", E_prediction="All visibility levels should bias choices in the same direction with magnitude scaling.", E_violation="Choice bias reverses from below chance at visibility 0 to above chance at visibility 2-3.", E_same_y="Every cell measures implementation of the same opposite-target rule.", Meyen_role="not-applicable", stats="adequate", flags=["none"], stats_reason="The awareness-by-choice association was directly tested and the direction of each visibility regime is reported.")

# Keizer et al. (2015)
add(cid="P000002_E01_C01", eid="P000002_E01", label=EXPERIMENTS[7][2], x="S1 Gabor orientation-location conjunction", xdesc="The first Gabor's orientation and location can repeat or alternate at S2 under effective or ineffective masking.", awareness_measure="Individualized presence/absence staircase and post-binding mask-evaluation detection task", proc="presence-absence-detection", evtype="objective-invisibility", obj="yes", obj_reason="The task has a 50% chance baseline, individualized staircasing, and a posttest at the binding-task mask strength with confirmatory split binomial exclusion.", A="A-validated", A_reason="A separate same-participant validation block used the same stimulus and masking strength; attentive detection makes transfer conservative.", A_result="Only two participants confirmed above chance on the split test and were excluded; retained participants supplied the binding analysis.", A_location="P000002 main PDF pp. 2-3", E="E-physical-only", E_reason="S1 is physically the same but masking efficacy produces deliberately unequal first-order evidence without matching or a diagnostic pattern.", Y="orientation-location feature binding and retrieval", Ydesc="The orientation-by-location repetition interaction in S2 response time indexes integration and later retrieval of S1 features.", components=[comp_effect("masked-binding", "orientation by location repetition under effective masking", "unaware", "Binding cost 5.8 ms.", "t(27)=1.8, one-tailed p=.04", "P000002 main PDF p. 4, Fig. 2"), comp_effect("visible-binding", "orientation by location repetition under ineffective masking", "aware", "Binding cost 8.6 ms.", "t(27)=2.3, one-tailed p=.02", "P000002 main PDF p. 4, Fig. 2")], F="F-meaningful", F_reason="The crossed partial-repetition cost operationalizes integration and retrieval of a specific feature conjunction, not mere detection.", cap="supported", cap_effect="Effective-mask RT binding cost 5.8 ms, t(27)=1.8, one-tailed p=.04.", cap_stats="concern", aw="no-detectable-difference", aw_effect="Masking by orientation by location interaction F(1,27)=0.25, p>.6.", aw_est="Binding costs 8.6 ms visible versus 5.8 ms masked.", aw_stats="concern", diff="yes", pages="P000002 main PDF pp. 2-6", figs="P000002 main PDF Figs. 1-3 and Tables 1-2", constraint="Masked S1 produced a binding/retrieval cost, but selective exclusions and a nonsignificant masking interaction do not establish equivalence across awareness.", alt_scan="completed-candidate-evaluated", alt_reason="A robustness reanalysis retained a nonsignificant three-way interaction, but planned masked binding was no longer significant; this weakens rather than repairs inference.", Meyen_role="supplementary", Meyen_status="Meyen-unassessable", Meyen_reason="Dedicated individualized pre/post visibility validation independently supports A, but no indirect-task advantage comparison on a common scale is reported.", stats="concern", flags=["selective-exclusions", "weak-null-evidence"], stats_reason="Ten of 38 awareness-qualified participants were excluded for task performance; including them removed RT significance, and the masked planned test is one-tailed.", null_strength="nonsignificant-only", null_adequacy="weak", a_bundle=True, mech="Binding is inferred from the orientation-by-location partial-repetition interaction; the exact integration/retrieval mechanism remains ambiguous.")

# Lamy et al. (2015)
for i, vals in enumerate([
    ("P000003_E01_C01", "P000003_E01", "Experiment 1 - CFS spatial cueing", "Trialwise 0-3 subjective visibility", "subjective-visibility", "subjective", "not-applicable", "A direct trialwise subjective measure defines awareness.", "Ratings of 0 defined unaware trials; ratings 1-3 defined aware trials.", "P000003 main PDF pp. 3-4", "Relevant benefit 36 ms; irrelevant effect 1 ms.", "Relevant benefit 50 ms; irrelevant cost 33 ms.", "F(4,52)=14.99, p<.0001", "P000003 main PDF p. 4, Fig. 2"),
    ("P000003_E02_C01", "P000003_E02", "Experiment 2 - CFS with localization validation", "Trialwise 0-3 visibility plus postphase cue localization", "mixed", "mixed", "yes", "Trialwise subjective A is corroborated by chance localization at rating 0 in a dedicated 100-trial block.", "At rating 0, localization was 25.07%, t<1; the main phase used the same subjective categories.", "P000003 main PDF pp. 5-6", "Relevant benefit 40 ms; irrelevant effect 2 ms.", "Relevant benefit 55 ms; irrelevant cost 35 ms.", "F(4,44)=12.30, p<.0001", "P000003 main PDF pp. 5-6, Figs. 2 and 4"),
    ("P000003_E03_C01", "P000003_E03", "Experiment 3 - brief exposure spatial cueing", "Trialwise yes/no subjective cue visibility", "subjective-visibility", "subjective", "not-applicable", "A direct trialwise subjective measure defines awareness, with acknowledged coarse-measure residual-awareness risk.", "Participants reported cue present or absent on every trial.", "P000003 main PDF pp. 7-8", "Same-color benefit 104 ms; different-color benefit 43 ms.", "Same-color benefit 104 ms; different-color effect 8 ms.", "F(4,45)=13.74, p<.0001", "P000003 main PDF pp. 7-8, Fig. 2"),
], start=1):
    cid,eid,label,measure,proc,evtype,obj,Areason,Aresult,Aloc,ue,ae,awtest,loc=vals
    add(cid=cid, eid=eid, label=label, x="color-singleton cue location and cue-target color relation", xdesc="Cue location and whether cue color matches the target define the spatial-cuing relation.", awareness_measure=measure, proc=proc, evtype=evtype, obj=obj, obj_reason=("The objective localization task has a 25% chance baseline and directly tests cue location." if obj=="yes" else "A subjective awareness classification is used."), A="A-direct", A_reason=Areason, A_result=Aresult, A_location=Aloc, E="E-diagnostic", E_reason="The awareness-by-color-relation-by-location pattern changes the same focal mapping rather than uniformly scaling it.", Y="feature-contingent modulation of spatial target selection", Ydesc="How cue-target color relation and cue location jointly change target-orientation response time.", components=[comp_effect("unaware", "relevant/same and irrelevant/different cue-color relations", "unaware", ue, None, loc), comp_effect("aware", "relevant/same and irrelevant/different cue-color relations", "aware", ae, None, loc)], F="F-meaningful", F_reason="The mapping specifies how task set and cue location regulate downstream target selection.", cap="supported", cap_effect=ue, cap_stats="adequate", aw="difference-supported", aw_effect=awtest, aw_est=f"Unaware: {ue} Aware: {ae}", aw_stats="adequate", diff="yes", pages=Aloc, figs=loc, constraint="The spatial-target-selection mapping is present without reported cue awareness and changes qualitatively with awareness across cue-target color relations.", alt_scan="completed-none-found", alt_reason="The supplied article was scanned; instructions, mappings, and task set were held fixed within experiment, and no anchored separate task-state alternative was identified.", E_competing="More first-order cue evidence uniformly strengthens the same spatial-cuing mapping.", E_prediction="Aware cue effects should preserve the unaware pattern and differ mainly in magnitude.", E_violation=f"The color-relation mapping changes across awareness: {ue} versus {ae}", E_same_y="All cells measure target-selection RT as a function of cue-target location and color relation.", Meyen_role="not-applicable")

# Lin and Murray (2015)
add(cid="P000004_E01_C01", eid="P000004_E01", label=EXPERIMENTS[11][2], x="repeated exogenous cue location", xdesc="Visible or masked cues appear at fixed, absent-after-fixed, or random locations across blocks.", awareness_measure="Posttask cue-location discrimination", proc="localization", evtype="objective-invisibility", obj="yes", obj_reason="The localization task has a 50% baseline, 80/120 trials, and reports group 49.30%, t(23)=-.75, p=.46 after individual classification.", A="A-validated", A_reason="A separate posttask localization block tests the focal cue property in the same participants and random-cue regime; transfer to fixed cues is checked in Experiment 2.", A_result="Visible group 97.8%; retained invisible groups 49.30%, t(23)=-.75, p=.46.", A_location="P000004 main PDF pp. 3-4", E="E-diagnostic", E_reason="The fixed/no-cue/random phase mapping violates monotonic sensory-strength scaling despite cue color differences.", Y="temporal allocation of spatial priority from repeated exogenous cues", Ydesc="Immediate cue validity and persistent old-location bias across fixed, no-cue, and random phases.", components=[comp_effect("fixed", "fixed cue location", "mixed", "Invisible cue: 15.7-ms benefit; visible cue: 2.1 ms.", "visibility by validity F(1,42)=14.00, p=.001", "P000004 main PDF p. 4"), comp_effect("no-cue", "previously cued versus new location", "mixed", "Visible: -12.2-ms aftereffect; invisible: 1.6 ms.", "visibility by location F(1,42)=9.17, p=.004", "P000004 main PDF p. 4"), comp_effect("random", "random cue location", "mixed", "Visible 14.2 ms; invisible 14.9 ms.", None, "P000004 main PDF p. 4")], F="F-meaningful", F_reason="The phase-specific allocation and persistence of spatial priority is a distinct downstream function.", cap="supported", cap_effect="Invisible fixed-cue 15.7 ms, t(23)=5.96, p<.001; invisible random-cue 14.9 ms, t(23)=8.49, p<.001.", cap_stats="adequate", aw="difference-supported", aw_effect="Fixed visibility-by-validity F(1,42)=14.00,p=.001 and no-cue visibility-by-location F(1,42)=9.17,p=.004.", aw_est="Invisible-only fixed facilitation and visible-only negative aftereffect; random effects similar.", aw_stats="adequate", diff="yes", pages="P000004 main PDF pp. 2-5", figs="P000004 main PDF Figs. 1-2", constraint="Repeated-cue spatial priority operates under objective invisibility and changes qualitatively across awareness and temporal phase.", alt_scan="completed-candidate-evaluated", alt_reason="Experiments 2 and 3 test fixed-cue visibility transfer and visible SOA robustness; no separate task-state alternative remains.", E_competing="More sensory evidence produces a uniformly stronger version of the same spatial-priority mapping.", E_prediction="Visible cues should have effects at least as large and in the same phase-specific directions as invisible cues.", E_violation="Fixed-cue facilitation occurs only for invisible cues, whereas the later negative aftereffect occurs only for visible cues; random-cue facilitation is similar.", E_same_y="All phases measure allocation of target-detection priority to cued or previously cued locations.", Meyen_role="supplementary", Meyen_status="Meyen-unassessable", Meyen_reason="A dedicated localization validation independently supports A, but no indirect-task advantage analysis on a common sensitivity scale is reported.", a_bundle=True)
add(cid="P000004_E02_C01", eid="P000004_E02", label=EXPERIMENTS[12][2], x="16.7-ms repeated exogenous cue location", xdesc="The same trial sequence is used in cuing and later location-discrimination tasks across fixed, no-cue, and random phases.", awareness_measure="420-trial cue-location discrimination matched in trial count and sequence", proc="localization", evtype="objective-invisibility", obj="yes", obj_reason="The 50% baseline, 420 matched trials, and phase-specific tests provide an informative objective validation.", A="A-validated", A_reason="A separate but exactly trial-sequence-matched validation tests fixed and random cue regimes in the same participants.", A_result="Thirteen fixed-cue participants averaged 49.39%, t(12)=-.61,p=.55; fourteen random-cue participants averaged 50.48%,t(13)=.33,p=.74.", A_location="P000004 main PDF p. 7", E="E-uncontrolled", E_reason="This experiment contains only an invisible cue regime and therefore provides no aware/unaware first-order-evidence contrast.", Y="temporal allocation of spatial priority from repeated exogenous cues", Ydesc="Immediate cuing and persistent location bias across fixed, no-cue, and random phases.", components=[comp_effect("fixed", "fixed cue", "unaware", "15.6-ms cuing effect.", "t(12)=4.13,p=.001", "P000004 main PDF p. 7"), comp_effect("no-cue", "old versus new location", "unaware", "-2.1-ms nonsignificant aftereffect.", "t(12)=-.41,p=.692", "P000004 main PDF p. 7"), comp_effect("random", "random cue", "unaware", "20.5-ms cuing effect.", "t(13)=5.10,p<.001", "P000004 main PDF p. 7")], F="F-meaningful", F_reason="Phase-specific spatial-priority allocation is a distinct downstream function.", cap="supported", cap_effect="Fixed 15.6 ms, p=.001 and random 20.5 ms, p<.001 under validated invisibility.", cap_stats="adequate", aw="not-tested", aw_effect=None, aw_est=None, aw_stats="not-applicable", diff="not-applicable", pages="P000004 main PDF pp. 6-7", figs="P000004 main PDF Table 2", constraint="Objectively invisible repeated cues allocate spatial priority in fixed and random phases, but this experiment alone does not test awareness effects.", alt_scan="completed-candidate-evaluated", alt_reason="Experiment 1 supplies the aware comparator, but cross-experiment evidence is not imported into this row's E classification.", Meyen_role="supplementary", Meyen_status="Meyen-unassessable", Meyen_reason="The large matched validation independently supports A; indirect versus direct sensitivity was not compared on a common scale.", a_bundle=True)

# Persaud et al. (2011)
common_persaud = dict(eid="P000005_E01", label=EXPERIMENTS[14][2], x="vertical-grating location in normal versus blind hemifield", xdesc="Low-contrast normal-field and high-contrast blind-field gratings were titrated to similar discrimination accuracy.", awareness_measure="Guess/Seen report by hemifield", proc="subjective-visibility", evtype="subjective", obj="not-applicable", obj_reason="A direct subjective blindsight report is used.", A="A-direct", A_reason="Same-experiment Guess/Seen results show a marked normal/blind phenomenology difference.", A_result="Seen on 43% of normal-field and 3% of blind-field trials, chi-square p<1e-7.", A_location="P000005 main PDF p. 3, Fig. 2B", E="E-matched", E_reason="Separate staircases actively titrated location-discrimination accuracy to about 75%; observed 76% versus 79%, p=.34.", structure="scalar-justified", identity="distinct-downstream-outputs", Y_structure="scalar", critical_dependency="checked-none", alt_scan="not-required", alt_reason="Active matching establishes E.", a_bundle=True)
add(cid="P000005_E01_C01", **common_persaud, Y="metacognitive calibration of visual discrimination", Ydesc="Correlation between wagering choice and discrimination accuracy within each hemifield.", components=[], F="F-meaningful", F_reason="Trialwise calibration of confidence/wagering to correctness is a distinct metacognitive function beyond direct discrimination.", cap="unclear", cap_effect="Blind-field wagering-accuracy correlation r=.30; its separate significance is not reported.", cap_stats="unclear", aw="difference-supported", aw_effect="Normal r=.52 versus blind r=.30, Fisher r-to-z p<.001.", aw_est="Calibration correlation difference .22.", aw_stats="adequate", diff="yes", pages="P000005 main PDF pp. 2-4", figs="P000005 main PDF Figs. 1-2", constraint="With first-order accuracy titrated, metacognitive calibration is higher for normally seen than blind-field stimuli; blind-field capacity remains statistically unclear.", Meyen_role="not-applicable")
add(cid="P000005_E01_C02", **common_persaud, Y="regional cortical activation to visual stimulation", Ydesc="Normal-minus-blind BOLD activation in parietal, temporal, and prefrontal regions.", components=[], F="F-not-meaningful", F_reason="Regional BOLD differences are generic neural responses/mechanistic support and do not themselves identify a distinct downstream cognitive use of X.", cap="not-tested", cap_effect=None, cap_stats="not-applicable", aw="unresolved", aw_effect="Normal-field stimulation produced multiple cluster-corrected activations over blind-field stimulation.", aw_est="Regional cluster contrasts reported in Table 1.", aw_stats="adequate", diff="yes", pages="P000005 main PDF pp. 3-6", figs="P000005 main PDF Figs. 3-5 and Table 1", constraint="Performance-matched awareness regimes differ in regional BOLD, but generic activation is F-not-meaningful and cannot enter a strong functional route.", Meyen_role="not-applicable", mech="The activations may reflect awareness, metacognitive capacity, preparatory flexibility, or other associated processes; the article cannot disambiguate them.", mechanism_clarity="ambiguous")

# Tsushima et al. (2006)
tsu = [
    ("P000006_E01_C01","P000006_E01",EXPERIMENTS[15][2],"5% coherence was below the measured threshold; 20% was suprathreshold.","5% reduced RSVP d-prime versus 0% and 20%, both Bonferroni p<.001.","P000006 main PDF pp. 2-3, Fig. 2A","adequate",["none"]),
    ("P000006_E02_C01","P000006_E02",EXPERIMENTS[16][2],"The lower-luminance threshold and performance dip shifted toward 30% coherence.","30% reduced RSVP d-prime versus 20% and 40%, both p<.01.","P000006 main PDF p. 3, Fig. 2B","adequate",["none"]),
    ("P000006_E03_C01","P000006_E03",EXPERIMENTS[17][2],"A posttask threshold test used the Experiment-1 method; exact values are not reported in the supplied text.","The same 5% dip pattern occurred while eye movements showed no systematic coherence difference.","P000006 main PDF p. 3; supplement pp. 4-5","unclear",["other"]),
    ("P000006_E04_C01","P000006_E04",EXPERIMENTS[18][2],"A contraction-detection threshold test placed 5% below the chance-level threshold.","5% reduced RSVP d-prime versus 0% p<.01, 10% p<.05, and 20% p<.001.","P000006 supplement pp. 5-6, Fig. S2","adequate",["none"]),
    ("P000006_E05_C01","P000006_E05",EXPERIMENTS[19][2],"The same contracting stimuli were tested in a task-relevant motion-detection condition; the main article places 5% around chance threshold.","At 5%, RSVP performance dipped while MT+ peaked and LPFC remained at 0%-level activity.","P000006 main PDF pp. 3-4, Fig. 3; supplement pp. 6-9","concern",["multiple-comparisons"]),
]
for cid,eid,label,Aresult,effect,loc,stat,flags in tsu:
    add(cid=cid, eid=eid, label=label, x="task-irrelevant coherent background motion", xdesc="Motion coherence varies across below-threshold, threshold-near, and suprathreshold levels while participants identify RSVP digits.", awareness_measure="Post-main motion direction/detection threshold measurement", proc="direction-identification", evtype="objective-invisibility", obj="yes", obj_reason="The objective task has a meaningful chance baseline, many trials, and tests the relevant motion information under attention; transfer to the task-irrelevant main task is conservative.", A="A-validated", A_reason="A separate same-participant threshold procedure tests the same motion regime with attention directed to motion, so below-threshold status plausibly transfers to the less-attended main task.", A_result=Aresult, A_location=loc, E="E-diagnostic", E_reason="Threshold-linked nonmonotonicity, and in Experiment 2 a shifted threshold with shifted dip, violate monotonic evidence-strength scaling for the same RSVP-interference Y.", Y="modulation of RSVP digit identification by task-irrelevant motion", Ydesc="How irrelevant motion coherence changes the accuracy/sensitivity of reporting central RSVP digits.", components=[comp_effect("threshold-near", "threshold-near coherence", "unaware", effect, None, loc), comp_effect("suprathreshold", "suprathreshold coherence", "aware", "Higher coherence produced less disruption than the threshold-near level.", None, loc)], F="F-meaningful", F_reason="The distractor-induced modulation of central digit selection is a distinct downstream control/interference relation, not motion detection itself.", cap="supported", cap_effect=effect, cap_stats=stat, aw=("difference-supported" if stat=="adequate" else "unresolved"), aw_effect=effect, aw_est="Threshold-near coherence disrupts more than both lower/no-coherence and suprathreshold coherence.", aw_stats=stat, diff="yes", pages=loc, figs=loc, constraint="Task-irrelevant motion influences RSVP selection below objective threshold, and the threshold-linked nonmonotonic pattern is diagnostic against simple sensory-strength scaling.", critical_dependency="resolved", dependency_reason="The classification-critical Supporting Online Material was supplied and inspected with the main article.", alt_scan="completed-candidate-evaluated", alt_reason="Experiments 2-5 provide shifted-threshold, eye-movement, contraction, and neural controls; same-Y support is reflected in the bounded scan.", E_competing="Stronger first-order motion evidence monotonically produces more distraction of the same RSVP function.", E_prediction="RSVP disruption should increase monotonically with motion coherence/evidence.", E_violation=effect, E_same_y="Every coherence cell measures central RSVP digit-identification performance under task-irrelevant motion.", Meyen_role="supplementary", Meyen_status="Meyen-unassessable", Meyen_reason="A dedicated high-trial threshold validation independently supports A, but direct and indirect tasks are not compared for sensitivity on a common scale.", stats=stat, flags=flags, stats_reason=("The critical threshold-linked contrasts are reported with corrected tests." if stat=="adequate" else "The qualitative pattern is reported, but small samples and/or incomplete exact contrast reporting limit statistical certainty."), a_bundle=True, mech="The paper proposes that threshold-near motion escapes LPFC inhibitory control and remains strong in MT+; this mechanism is supporting, not the F gate.")


def decision(entity_type: str, entity_id: str, decision_type: str, field: str | None, old_value, new_value, reason: str, source_location: str) -> None:
    record = {
        "decision_id": allocate_identifier(RUN_DIR, "decision"), "run_id": RUN_ID,
        "timestamp": now(), "entity_type": entity_type, "entity_id": entity_id,
        "decision_type": decision_type, "field": field, "old_value": old_value,
        "new_value": new_value, "reason": reason, "source_location": source_location,
        "agent": "Codex/GPT-5",
    }
    append_jsonl_record(RUN_DIR / "decision_log.jsonl", SCHEMAS["decision"], record)


def bundle_rows(row: dict, fake_index: int, persist: bool) -> tuple[list[dict], list[dict], list[str]]:
    bundles, links, ids = [], [], []
    specs = []
    if row.pop("_a_bundle"):
        specs.append(("awareness-A", [{"key":"critical-awareness-result", "exp":row["experiment_id"], "location":row["awareness_result_source_location"], "claim":row["awareness_result_description"], "role":"awareness-validation", "same":"not-applicable"}], None))
    control = row.pop("_e_control")
    if row["E_code"] == "E-diagnostic":
        members = [{"key":"same-y-pattern", "exp":row["experiment_id"], "location":row["source_figures_tables"], "claim":row["E_violating_pattern"], "role":"E-diagnostic-support", "same":"yes"}]
        contrast = None
        if control:
            members.append({"key":"contrast-control", "exp":control[0], "location":control[1], "claim":control[2], "role":"alternative-explanation-control", "same":"yes"})
            contrast = control
        specs.append(("E-diagnostic", members, contrast))
    for spec_index, (premise, members, contrast) in enumerate(specs, start=1):
        bundle_id = allocate_identifier(RUN_DIR, "evidence_bundle") if persist else f"{RUN_ID}_EB{fake_index*10+spec_index:06d}"
        ids.append(bundle_id)
        bundle = {
            "evidence_bundle_id": bundle_id, "focal_comparison_id": row["comparison_id"],
            "supported_premise": premise,
            "premise_description": ("The separate validation result supports the focal awareness classification." if premise=="awareness-A" else "The structured same-Y pattern violates the stated scalar first-order-evidence account."),
            "route_label": ("A classification" if premise=="awareness-A" else "E diagnostic"),
            "required_member_keys": [m["key"] for m in members], "bundle_status": "complete",
            "bundle_reason": "Every required direct member is available, evaluated, transfer-valid enough, and supportive.",
            "contrast_integrity_alternative": ("Explicit task-relation knowledge could independently change forced-choice rule use." if contrast else None),
            "contrast_integrity_anchor_type": ("manipulation-check-or-control" if contrast else "none"),
            "contrast_integrity_anchor_source_location": (contrast[1] if contrast else None),
            "contrast_integrity_viability_reason": ("The source experiment learns the rule under visible cues; a fixed-instruction control is therefore required." if contrast else None),
            "contrast_integrity_prediction": ("If explicit rule knowledge alone explains the pattern, fixed instructions should eliminate the visibility-linked reversal." if contrast else None),
            "contrast_integrity_control_member_key": ("contrast-control" if contrast else None),
            "contrast_integrity_resolution": ("ruled-out" if contrast else "not-applicable"),
            "contrast_integrity_resolution_reason": ("Experiment 7 holds the instruction and rule constant and still reports the same visibility-linked reversal." if contrast else "No independently anchored separate task-state alternative was identified for this bundle."),
            "notes": None,
        }
        for member_index, m in enumerate(members, start=1):
            link_id = allocate_identifier(RUN_DIR, "evidence_link") if persist else f"{RUN_ID}_EL{fake_index*100+spec_index*10+member_index:06d}"
            links.append({
                "evidence_link_id": link_id, "evidence_bundle_id": bundle_id, "member_key": m["key"],
                "focal_comparison_id": row["comparison_id"], "supporting_paper_id": row["paper_id"],
                "supporting_experiment_id": m["exp"], "supporting_auxiliary_id": None, "evidence_assessment_id": None,
                "supporting_source_type": ("same-experiment-analysis" if m["exp"]==row["experiment_id"] else "within-paper-experiment"),
                "support_role": m["role"], "dependency_role": "required", "evidence_content_type": "critical-result",
                "same_focal_Y_status": m["same"], "member_status": "supports", "supported_claim": m["claim"],
                "transfer_reason": ("Same participants/regime and focal analysis." if m["exp"]==row["experiment_id"] else "The supporting experiment uses the same forced-choice opposite-target Y and fixes the task-state alternative."),
                "transfer_limitation": (None if m["exp"]==row["experiment_id"] else "The supporting experiment uses trialwise instructed rather than learned rule use."),
                "source_location": m["location"], "used_for_decision": True, "notes": None,
            })
        bundles.append(bundle)
    row["evidence_bundle_ids"] = ids
    return bundles, links, ids


def dry_run() -> None:
    all_bundles, all_links = [], []
    for index, original in enumerate(ROWS, start=1):
        row = deepcopy(original)
        bundles, links, _ = bundle_rows(row, index, False)
        try:
            validate_record(row, SCHEMAS["experiment"])
        except Exception as exc:
            raise RuntimeError(f"comparison schema failure at {row['comparison_id']}: {exc}") from exc
        for bundle in bundles: validate_record(bundle, SCHEMAS["bundle"])
        for link in links: validate_record(link, SCHEMAS["link"])
        all_bundles.extend(bundles); all_links.extend(links)
    print(f"PASS: schema dry run for {len(ROWS)} comparisons, {len(all_bundles)} bundles, and {len(all_links)} links")


def persist() -> None:
    for paper_id, expected_eid, label, assessment, reason, location in EXPERIMENTS:
        eid = allocate_identifier(RUN_DIR, "experiment", paper_id)
        if eid != expected_eid: raise RuntimeError(f"unexpected experiment ID {eid}, expected {expected_eid}")
        decision("experiment", eid, "pre-atomization-functional-structure", "functional_structure_assessment", None, assessment, reason, location)
    for index, original in enumerate(ROWS, start=1):
        row = deepcopy(original)
        cid = allocate_identifier(RUN_DIR, "comparison", row["experiment_id"])
        if cid != row["comparison_id"]: raise RuntimeError(f"unexpected comparison ID {cid}, expected {row['comparison_id']}")
        bundles, links, _ = bundle_rows(row, index, True)
        for bundle in bundles:
            initial = deepcopy(bundle); initial["bundle_status"]="incomplete"; initial["bundle_reason"]="Required direct links are not yet persisted."
            decision("evidence_bundle", bundle["evidence_bundle_id"], "evidence-bundle-initialization", "bundle_status", None, "incomplete", initial["bundle_reason"], row["source_pages"])
            write_csv_record(RUN_DIR/"evidence_bundles.csv", SCHEMAS["bundle"], initial)
            for link in [x for x in links if x["evidence_bundle_id"]==bundle["evidence_bundle_id"]]:
                decision("evidence_link", link["evidence_link_id"], "evidence-link-assessment", "member_status", None, "supports", link["supported_claim"], link["source_location"])
                write_csv_record(RUN_DIR/"evidence_links.csv", SCHEMAS["link"], link)
            decision("evidence_bundle", bundle["evidence_bundle_id"], "evidence-bundle-derivation", "bundle_status", "incomplete", "complete", bundle["bundle_reason"], row["source_pages"])
            write_csv_record(RUN_DIR/"evidence_bundles.csv", SCHEMAS["bundle"], bundle, key_field="evidence_bundle_id")
        events = [
            ("comparison-structure","functional_structure_assessment",row["functional_structure_assessment"],row["functional_structure_reason"]),
            ("awareness-classification","A_code",row["A_code"],row["A_reason"]),
            ("meaningful-function-classification","F_code",row["F_code"],row["F_reason"]),
            ("provisional-first-order-evidence","E_code",("E-physical-only" if row["E_code"]=="E-diagnostic" else row["E_code"]),"Design-based E was assessed before result inspection."),
            ("alternative-control-scan","alternative_control_scan_status",row["alternative_control_scan_status"],row["alternative_control_scan_reason"]),
            ("final-first-order-evidence","E_code",row["E_code"],row["E_reason"]),
            ("unaware-capacity","unaware_capacity",row["unaware_capacity"],row["unaware_capacity_reason"]),
            ("awareness-effect","awareness_effect",row["awareness_effect"],row["awareness_effect_reason"]),
            ("statistical-audit","stats_status",row["stats_status"],row["stats_reason"]),
            ("Meyen-audit","Meyen_role",row["Meyen_role"],row["Meyen_reason"]),
            ("result-inspection","result_inspection_status",row["result_inspection_status"],row["result_inspection_reason"]),
            ("constraint-summary","constraint_summary",row["constraint_summary"],row["constraint_summary"]),
        ]
        for dtype, field, value, reason in events:
            decision("comparison", cid, dtype, field, None, value, reason, row["source_pages"])
        write_csv_record(RUN_DIR/"experiments_master.csv", SCHEMAS["experiment"], row)
    with (RUN_DIR/"papers_master.csv").open(newline="",encoding="utf-8") as handle:
        papers=list(csv.DictReader(handle))
    for raw in papers:
        paper_id=raw["paper_id"]
        # Reload typed rows through the package helper by round-tripping the initialized schema reader.
        from structured_write import load_csv_rows
        errors=[]; typed=load_csv_rows(RUN_DIR/"papers_master.csv",SCHEMAS["paper"],errors)
        if errors: raise RuntimeError(errors)
        paper=next(x for x in typed if x["paper_id"]==paper_id)
        decision("paper",paper_id,"fulltext-evaluation","current_status","fulltext-retrieved","fulltext-evaluated","Every qualifying supplied-paper experiment was mapped and comparison-level classifications were written; support-only experiments were explicitly retained without comparison rows.",paper["fulltext_source"])
        paper["current_status"]="fulltext-evaluated"
        write_csv_record(RUN_DIR/"papers_master.csv",SCHEMAS["paper"],paper,key_field="paper_id")
    print(f"PASS: persisted {len(EXPERIMENTS)} experiment audits and {len(ROWS)} comparison rows")


if __name__ == "__main__":
    parser=argparse.ArgumentParser(); parser.add_argument("--persist",action="store_true"); args=parser.parse_args()
    persist() if args.persist else dry_run()
