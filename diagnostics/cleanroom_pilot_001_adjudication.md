# Clean-room pilot 001 adjudication

## Scope and evidence base

This is diagnostic/gold material. It is excluded from registered-facing inputs and future clean-room fixtures. The archived pilot is at `diagnostics/cleanroom_pilot_001/`; its source package commit is `0be0cc2d0a18dfbec320f8a2ace0b16573914f8c`.

The adjudication uses only the archived durable run records, the six locally supplied main articles, and the hand-audited hypotheses in the pilot-revision request. This clean-room workspace intentionally contains no earlier anchor-regression, calibration-provenance, test, or decontamination diagnostic files and is not a Git worktree. Consequently, no absent historical fixture was reconstructed or silently treated as evidence. The Persaud correction and Lamy structural expectation are also recorded in `cleanroom_pilot_001_gold_corrections.json`.

Disagreement classes:

- **A — CLEAN PASS**
- **B — SOURCE-FIXTURE LIMITATION**
- **C — GOLD-STANDARD CORRECTION**
- **D — ORDINARY MODEL / EXECUTION VARIANCE**
- **E — GENERIC METHOD UNDERSPECIFICATION**
- **F — POSSIBLE METHOD OVER-PERMISSIVENESS — NEEDS ANALYSIS**

## Pilot-wide conclusion

The pilot demonstrates that the draft-0.8.1 package can independently recover many comparison-level distinctions, preserve uncertainty, construct premise-specific bundles, and avoid false equivalence. Its one generic structural failure is destructive scalar atomization before asking whether an experiment's critical interaction defines one coherent factorial-functional X→Y relation. The early sign-reversal E-diagnostic decision exposes a separate possible over-permissiveness issue, but one clean Codex run shows only that the ambiguity *can* occur; it does not establish that every such decision requires a protocol rewrite.

The factorial-pre-atomization repair is warranted now because it operationalizes an already intended generic guardrail. The E-diagnostic issue remains open because changing that scientific standard may affect several paradigm classes and requires additional independent pilots/agents.

## Ben-Haim et al. (2021)

| Dimension | Pilot | Hand adjudication | Class and evidence |
|---|---|---|---|
| Focal comparison discovery | Human Exp. 1 and Exp. 7, monkey analogues, and forced-guessing variants were separately found; support-only Exp. 5 was not promoted | Exp. 7 is a clean focal comparison; Exp. 1 is scientifically relevant but its E strength is open | **A** for discovery; **F** only for the Exp. 1 E decision |
| X | Masked/supraliminal cue location or trialwise masked-cue awareness | Correct | **A** |
| Y | Adaptive rule-guided use of an incongruent cue | Correct conservative function | **A** |
| Scalar versus factorial-functional | Crossovers were represented as factorial-functional; the informed-only variant was scalar | Correct | **A** |
| A | Human experiments direct; monkey experiments transfer-risk because the cited validation was unavailable | Correct under supplied sources | **A** for humans; **B** for monkey strong-A limitation |
| E | Exp. 1, 3, 7 and monkey analogues coded E-diagnostic from sign reversal; Exp. 6 physical-only | Exp. 7 trialwise within-regime comparison is potentially clean. Exp. 1 may admit an evidence-strength/process-enablement account and cannot yet be treated as securely diagnostic | **F** for Exp. 1; **A** for recording the late comparison separately |
| Evidence bundles | Explicit same-experiment E bundles; incomplete external-A bundles for monkeys | The Exp. 1 E bundle captures the observed crossover but does not address the more flexible evidence-only process-enablement alternative | **F** for adequacy of the Exp. 1 E premise; **B** for monkey A source completeness |
| Awareness effect | Exp. 1 and Exp. 7 difference-supported; Exp. 3/4 unresolved where no direct focal difference test was reported | Correct conditional on final E | **A** for result/statistical coding; Exp. 1 constraint interpretation inherits **F** |
| Unaware-capacity claim | Exact opposite-location adaptive rule use; not-supported under unawareness | Correct: below-chance/default cue-following is not positive adaptive opposite-rule use | **A** |
| No-detectable/equivalence | None inferred | Correct | **A** |
| Meyen | Human objective cases supplementary/unassessable; monkey cases inference-critical/unassessable | Conservative and explicit | **A/B**; missing auxiliary source explains monkey uncertainty |
| Statistics | Direct Exp. 1 and Exp. 7 effects treated adequate; separate-condition cases flagged | Correctly distinguishes direct from separate tests | **A** |
| Constraint-ready output | Exp. 1 and Exp. 7 enter awareness-linked output | Exp. 7 survives; Exp. 1 is an open possible over-permissive entry pending E adjudication | **F** for Exp. 1 only |

## Keizer et al. (2015)

| Dimension | Pilot | Hand adjudication | Class and evidence |
|---|---|---|---|
| Focal comparison discovery | Short-term orientation-location binding/retrieval | Correct | **A** |
| X | Masked S1 orientation-location conjunction | Correct | **A** |
| Y | Binding and retrieval of the conjunction | Correct exact capacity identity | **A** |
| Scalar versus factorial-functional | Factorial-functional partial-repetition mapping | Correct | **A** |
| A | A-validated from individual staircasing plus post-task discrimination | Strong validated unawareness under the legacy-sensitive rule | **A** |
| E | E-physical-only | Correct; no positive evidence matching/equivalence | **A** |
| Evidence bundles | No borrowed classification-critical premise required | Acceptable from supplied paper record | **A** |
| Awareness effect | No-detectable-difference from the direct masking × binding interaction | Correct descriptive category | **A** |
| Unaware-capacity claim | Binding/retrieval supported | Correct, but statistics retain concern | **A** |
| No-detectable/equivalence | No-detectable; explicitly not equivalence | Correct | **A** |
| Meyen | Supplementary/unassessable | Correctly visible but nongating because dedicated validation establishes A | **A** |
| Statistics | Concern: one-tailed 5.8-ms effect and loss in more inclusive robustness analysis | Correct caveat | **A** |
| Constraint-ready output | Excluded because capacity statistics are `concern`; present in descriptive no-detectable view | Correct | **A** |

This is the strongest clean-room success: the agent reproduced strong validated unawareness, positive unaware binding/retrieval capacity, no detectable awareness difference without equivalence inflation, and the robustness caveat.

## Lamy et al. (2015)

| Dimension | Pilot | Hand adjudication | Class and evidence |
|---|---|---|---|
| Focal comparison discovery | Only scalar attentional-capture and feature-change-cost rows | The critical awareness × cue-feature relation × target-location statistic tests a coherent spatial-cuing mapping and had to be considered first | **E** |
| X | Cue location/state, cue-target feature relation, and trialwise awareness were split across scalar rows | Component descriptions are accurate, but the focal X/task relation was not assembled | **E** |
| Y | Separate contingent capture and location-specific feature-change cost | Those components may coexist, but they do not replace the conservative factorial mapping from cue-target feature relation to location-contingent target performance | **E** |
| Scalar versus factorial-functional | Scalar only | Instantiate the factorial-functional focal comparison first; scalar component comparisons remain optional and meaningful | **E** |
| A | A-direct; Exp. 2 adds objective localization support | Correct for the component evidence | **A** |
| E | Scalar rows remain E-physical-only | Focal E was never assessed. It must be assessed on the whole factorial relation under the unchanged strict E rule, with a bundle identifying the first-order-evidence alternative | **E** for omission; final focal E is not backfilled here |
| Evidence bundles | None for the focal factorial relation | A focal bundle is required if cross-experiment or control evidence is used, and must say which member addresses the first-order alternative | **E** |
| Awareness effect | Capture: no detectable modulation; feature-change component: difference-supported in Exps. 1/2, unresolved in Exp. 3 | Component results are useful, but the critical factorial interaction must also receive one focal awareness-effect audit | **E** for incomplete focal audit |
| Unaware-capacity claim | Exact attentional capture supported; feature-change capacity unclear | Correct component-level identities; a nonzero component does not establish the whole factorial function | **A** for components |
| No-detectable/equivalence | Capture no-detectable; no formal equivalence | Correct component-level restraint | **A** |
| Meyen | Not applicable or supplementary as recorded | No adjudicated disagreement | **A** |
| Statistics | Direct component modulations and concerns were recorded | The significant three-way interactions are the critical focal tests and were not given a focal row | **E** |
| Constraint-ready output | Component capture capacities enter; no focal factorial awareness-effect row exists | Structurally incomplete. The new rule makes this omission a canonical execution violation without forcing a particular final E/outcome | **E** |

The failure is method-level, not a request to hard-code this paper. Under the new generic procedure, component scalar rows without the prior functional-structure assessment and required focal row would be rejected.

## Lin & Murray (2015)

| Dimension | Pilot | Hand adjudication | Class and evidence |
|---|---|---|---|
| Focal comparison discovery | Immediate orienting and later aftereffect were separated | Correct: these are defensibly distinct downstream temporal functions | **A** |
| X | Fixed/random masked or visible annulus cue and old cue location | Correct | **A** |
| Y | Immediate orienting as factorial mapping; persistent inhibition as scalar aftereffect | Correct conservative structures | **A** |
| A | A-validated using sequence-matched Exp. 2 localization | Correct, with explicit complete transfer bundle | **A** |
| E | Immediate Exp. 1 E-diagnostic; aftereffect and invisible-only replication uncontrolled | Correctly route-specific | **A** |
| Evidence bundles | Complete A and E bundles for the focal immediate comparison | Premise-specific, direct, and nontransitive | **A** |
| Awareness effect | Immediate qualitative difference; aftereffect difference but weak E; replication not tested | Correct | **A** |
| Unaware-capacity claim | Immediate exogenous orienting supported; persistent inhibition unclear | Exact function identities are preserved | **A** |
| No-detectable/equivalence | No equivalence claim | Correct | **A** |
| Meyen | Supplementary/unassessable | Correctly visible and nongating | **A** |
| Statistics | Immediate interaction adequate; weak aftereffect null flagged | Correct | **A** |
| Constraint-ready output | Immediate comparison and invisible-only immediate capacity enter; aftereffects do not | Correct | **A** |

## Persaud et al. (2011)

| Dimension | Pilot | Hand adjudication | Class and evidence |
|---|---|---|---|
| Focal comparison discovery | Metacognitive monitoring separated from mechanistic BOLD | Correct | **A** |
| X | Titrated grating discrimination in normal versus blind field | Correct | **A** |
| Y | Metacognitive monitoring of first-order accuracy | Correct | **A** |
| Scalar versus factorial-functional | Scalar correlation/difference comparison | Correct | **A** |
| A | A-direct | Correct for the subjective/field contrast used | **A** |
| E | E-matched from hemifield-specific titration and comparable first-order accuracy | Correct under the package's active-matching route | **A** |
| Evidence bundles | No borrowed premise required | Acceptable | **A** |
| Awareness effect | Difference-supported from the direct Fisher comparison | Survives strongly | **A** |
| Unaware-capacity claim | `unclear` because blind-field `r=.30` lacks an adequate direct positive test against zero | This is the corrected hand standard | **C** relative to any superseded gold of `supported`; the pilot already matches the correction |
| No-detectable/equivalence | None claimed | Correct | **A** |
| Meyen | Not applicable | Correct | **A** |
| Statistics | Overall concern for single-case/generalization; direct between-field difference adequate | Correct separation | **A** |
| Constraint-ready output | Awareness-linked difference enters; unaware-capacity route does not | Correct after gold correction | **A/C** |

The correction is scientific, not protocol-driven: a significant between-field difference does not itself prove that the blind-field correlation is positive.

## Tsushima et al. (2006)

| Dimension | Pilot | Hand adjudication | Class and evidence |
|---|---|---|---|
| Focal comparison discovery | Threshold-linked distractor-regulation comparisons and controls were found | Correct | **A** |
| X | Task-irrelevant coherent background motion | Correct | **A** |
| Y | Regulation/control of motion-distractor interference | Correct; failed regulation is not positive unconscious control | **A** |
| Scalar versus factorial-functional | Threshold/distractor mapping represented factorial-functionally | Correct | **A** |
| A | A-transfer-risk because validation sensitivity/transfer were supplement-dependent | With only the main article, this is the warranted uncertainty; do not change A | **B** |
| E | Exps. 1/2 E-diagnostic from the joint threshold/dip shift; later controls uncontrolled | Correct joint same-Y structure for supplied evidence | **A** |
| Evidence bundles | Complete cross-experiment E bundles; incomplete supplement-based A bundles | Correctly separates an available E premise from unavailable A support | **A/B** |
| Awareness effect | Reported differences retained but strong route closed by A | Correct | **A/B** |
| Unaware-capacity claim | Distractor regulation not-supported | Correct exact capacity identity | **A** |
| No-detectable/equivalence | None inferred | Correct | **A** |
| Meyen | Inference-critical/unassessable | Correctly gates because strong independent A could not be established from fixture | **B** |
| Statistics | Main threshold shift adequate; supplement-only controls unclear | Correct uncertainty | **B** |
| Constraint-ready output | None | Correct for this source-incomplete fixture, not evidence that the full paper record must fail | **B** |

The principal lesson is fixture construction. A future source-complete bounded test should include the exact main article and official/author supplementary material belonging to it when locally available. It should not automatically include external auxiliary papers, validation studies, or broader literature unless the test is explicitly exercising the auxiliary-source mechanism. Registered retrieval rules are unchanged.

## Disagreement summary

- **A — clean passes:** Keizer; Lin & Murray; Persaud's awareness-linked difference; the pilot's exact component-capacity and no-equivalence restraint; Tsushima's E structure; late trialwise Ben-Haim comparison.
- **B — source-fixture limitations:** Tsushima supplement-dependent A/statistics; monkey awareness validation in Ben-Haim.
- **C — gold-standard correction:** Persaud blind-field positive metacognitive capacity changes from any superseded `supported` fixture to `unclear`; the pilot already has `unclear`.
- **D — ordinary model/execution variance:** no disagreement is confidently assigned here. Because historical fixtures are absent, ordinary variance cannot be distinguished from an old-gold discrepancy by assumption.
- **E — generic method underspecification:** Lamy-like atomization of component scalar effects before considering the critical factorial-functional comparison.
- **F — possible method over-permissiveness:** early Ben-Haim human sign reversal classified E-diagnostic without ruling out a plausible evidence-strength/process-enablement account.

## Structural non-regression effect

Using the archived pilot only, the new generic rule would require the evaluator to perform and record the pre-atomization check before finalizing the Lamy scalar rows. Because the paper reports critical awareness × feature-relation × location interactions bearing on one conservative spatial-cuing mapping, the evaluator would have to instantiate the focal factorial-functional comparison first. The component capture and feature-change comparisons could still coexist. The archived pattern—component scalar rows present, focal coherent factorial relation never assessed—would violate the revised canonical execution procedure.

No other anchor classification changes merely because of this guardrail. A factorial focal relation is warranted only when the actual experimental hypothesis and statistic concern one coherent mapping; an interaction alone is not sufficient.
