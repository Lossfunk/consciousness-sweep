# Consciousness X → Y Literature Sweep Protocol

**Version:** 0.9.14
**Registration status:** frozen

Release authorization is determined by `RELEASE_READINESS.json`; freezing these authorities alone does not authorize launch.

This protocol operationalizes the user-designated Lossfunk-3 manuscript and the user’s explicit clarifications. Those are the reference for preparation; no older pipeline convention adds a scientific requirement. During a registered run this frozen file is the scientific and procedural source of truth for the sweep. It is written for human and AI screeners. `AGENTS.md` governs execution mechanics. Neither file may change during a registered run.

## 1. Aim and scope

The sweep asks:

> For a particular content X, whether external or internally generated, and mental process Y, does awareness of X change whether, or how well, Y can use X?

For this sweep, Y may be any mental function, including affective, motivational, experiential, social, perceptual, or conventionally cognitive functions. These examples are not a whitelist. Behavioral and physiological measures may support Y when their functional interpretation is justified. The supplementary query families do not define eligibility, and function-triggered searches are not restricted to their domains.

Apply no publication-date exclusion. Preprints and other available full-text versions are eligible under the same scientific criteria; record publication status, the version used, and retrieval time. `publication_date_policy = unrestricted` with `publication_cutoff = null` is an explicit no-cutoff decision. It does not mean the date policy is unfinished, and it does not promise exhaustive literature coverage. Completed search snapshots remain immutable even if the literature later changes.

The practical deliverable is a source-grounded prospect queue for the author to vet: papers that may add to the empirical profile of how awareness of X relates to its use in Y. State the proposed contribution, decisive evidence and remaining alternative before assigning a tentative primary/support role. A plausible prospect need not already satisfy the strongest scientific route. Uncertain awareness evidence, signal control, functional interpretation or statistics remain explicit questions; they do not become evidence of irrelevance. Conversely, unconscious processing alone, generic cognitive relevance or a nonzero effect does not establish a contribution to this profile. Distinguish a plausible same-X→same-Y awareness comparison from a study known not to contain one. The scientific classifications below retain their existing meaning; prospect selection does not weaken them.

The empirical target is a well-supported co-occurrence between awareness of X and a change in its downstream use, after the relevant simple explanations, including first-order signal strength, have been addressed under the criteria below. Establishing awareness as an independent cause of the functional change is not an inclusion requirement. These associations, together with capacities supported without awareness, constrain the subsequent abductive construction of process architectures. An architecture in which awareness and the functional change accompany a common processing transition remains compatible with this aim; identifying that architecture is the next theoretical task. Strength of support is assessed through the existing awareness, evidence-control, functional, and statistical requirements, not an additional unspecified effect-size or causal-identification threshold.

The search is result-neutral. A useful experiment may show that Y operates while X is unaware, that awareness changes Y, that no awareness-linked difference was detected, that equivalence is positively supported, or that one or both questions remain unresolved. A study is not a hit because awareness helps; it is useful because its design can inform the X → Y question.

The atomic scientific unit is a **paper × experiment × X→Y comparison**, not a paper or experiment as a whole. The physical experiment group is nevertheless a first-class representation unit: enumerate every physical experiment before atomization, including support-only experiments and experiments yielding no qualifying comparison. Such groups receive no placeholder comparison. One experiment may contain multiple comparison records. Y may be a scalar function or a coherent factorial functional relation. Multiple component simple effects may remain in one comparison when they jointly operationalize the same conservative functional mapping and the critical inference is an interaction or structured pattern over them. Genuinely different downstream functions receive separate comparisons. Assign A and F for each comparison from the methods/design. Assess design-based E next; when evidence is not matched, inspect the result pattern only for the frozen `E-diagnostic` test and then finalize E. Classify unaware capacity and the effect of awareness independently after A, F, and final E are established.

## 2. Design classification

### 2.1 A — awareness of X

Code awareness independently of E and F. The empirical target is human consciousness, including directly informative human patient studies. Record `population_scope` and its reason: `human-target`, `linked-other-system` (explicit direct human relevance, supplementary only), `out-of-scope`, or `unclear`.

Record `awareness_contrast_type` as `aware-unaware`, `graded`, `probability-regime`, `none`, or `unclear`, and independently record `unaware_condition_tested`. Degrees of awareness and supported differences in awareness probability qualify without an unaware arm or arbitrary binning. Factorial components may use `higher-awareness` and `lower-awareness`, with actual levels/rates specified in their descriptions; lower does not mean unaware. Comparison-wide strong A must support the actual levels or regimes compared, including the higher-awareness condition. Separately code A for each inventoried regime under the same criteria. Ordinary unaware capacity requires strong exact-X unawareness only in the explicitly selected regime(s) carrying its positive whole-Y result; uncertainty in another arm remains uncertainty and does not erase that capacity. It does not certify the awareness contrast. Above-chance objective performance alone cannot establish higher awareness. Awareness evidence must address the exact feature, relation, or other content X used by Y; mere awareness of stimulus presence does not automatically validate awareness of that content.

For every focal comparison, inventory each contrasted arm or graded/probability regime separately. Name the exact X used by Y, the focal-task awareness procedure and critical result for that regime, its source location, and any result transferred from another task, block, experiment, sample, supplement, or article with its transfer limitations. Evidence for unawareness in one arm does not establish awareness in another. Labels such as “visible” or “unmasked,” above-chance discrimination, and a separate detection task do not silently certify the higher-awareness focal arm. Missing regime-level evidence remains uncertain under the A rules below; a paper can still be retained for supportive reading. Retain comparison `A_code` as the contrast-wide judgment and record each regime's `A_code` and reason separately. `unaware_capacity_regime_keys` identifies the inventoried regime(s) to which the assessed capacity result and statistics apply. Assess the whole named Y within that scope; do not combine positives from unrelated regimes or components to manufacture it. Per-regime evidence type and objective-invisibility informativeness are necessary because one arm's measurement or sensitivity cannot validate another. Existing regime measure, result, origin and source fields supply the descriptions without duplicating procedures.

Before either E route, assess `comparison_validity` with a concrete reason. Conditions whose opposing instructions, scoring, deadlines or measurement differences trivially produce the target contrast are `not-comparable` unless the design or analysis addresses that explanation. Fully crossed instructions × awareness may support a valid factorial question. An endogenous processing transition under comparable task requirements is not its own disqualifying confound: the aim does not require isolating awareness as an independent cause. Apply this check to matched and diagnostic evidence alike. `unclear` preserves the unresolved comparison.

Subjective awareness does not require a separate feature-identification response. A content-relevant seen/unseen judgment, visibility report or PAS-like rating can directly assess the subjective percept that contains X. Judge its actual instruction, reported percept and claim scope: a report about the relevant colored shape, direction, relation or other content can bear on awareness of that content even when it does not ask the participant to identify the feature. Retain partial-awareness limitations when a report could concern only a different part of the stimulus. A generic presence judgment, objective accuracy, or an unmasked/visible condition label does not automatically certify every feature used by Y. Requiring feature identification for all subjective reports would impose an additional threshold absent from these rules.

Unawareness of X may be supported by subjective awareness evidence, sufficiently informative objective invisibility evidence, or both. Record the orthogonal `awareness_evidence_type` as `subjective`, `objective-invisibility`, `mixed`, or `none`.

Judge the joint, content-relevant awareness evidence at the scope of the claim. Convergence may include participant reports, informative calibration or validation results, and an explicitly justified higher-regime perceptibility contrast. A source-located qualitative result can contribute; a formal instrument in every arm, trialwise reports, exact procedural identity and 100% higher-regime seeing are not universal requirements. Distinguish an actual observation or justified converging premise from a bare condition label, and do not invent missing participant reports. State which results jointly establish each regime and why material task, timing, sample or sensitivity differences do or do not defeat transfer. A functional pattern may strengthen convergence but cannot supply absent awareness evidence by itself. Reasonable transfer can be sufficient even when imperfect; strong A still requires the actual result-bearing support and explicit links specified below.

A described awareness procedure is not itself an awareness result. Record critical-result availability in `awareness_result_reporting` and its evidential bearing in the separate `awareness_result_support` field. A focal reported result supports strong A only when reporting is `reported`, support is `supports-strong-A`, the actual procedure/test type matches, the result bears on the focal X/regime, and an exact source location is present. A Methods-only statement that participants completed a test is `not-reported` for the critical result and cannot support strong A. `A-direct` always requires this focal result. `A-validated` requires it unless a separate complete premise-specific transferred-`awareness-A` bundle supplies the critical result and explicit transfer assessment; do not copy a result from another experiment into the focal result fields.

- `A-direct`: qualifying subjective or objective-invisibility evidence is obtained in the relevant experiment, trial, block, condition, or stimulus regime. Subjective examples include seen/unseen judgments, graded visibility, and PAS-like ratings; the response need not be verbal.
- `A-validated`: qualifying subjective or objective-invisibility evidence is obtained in a separate validation procedure whose conditions plausibly transfer to the main experiment. Assess transfer using at least stimulus parameters, masking or suppression, timing, attentional allocation, task demands, and participant population. A validation regime must not plausibly make awareness lower than in the main experiment while being used to establish unawareness there.
- `A-transfer-risk`: a separate subjective or objective-invisibility validation exists, but its sensitivity or transfer to the main experiment is materially uncertain.
- `A-absent`: no qualifying subjective or objective-invisibility evidence supports the awareness classification. Masking, stimulus condition, neural activity, or an insensitive visibility test alone does not qualify.

When strong A uses a result from another block, experiment, supplement, or external source, `A-validated` requires a complete premise-specific `awareness-A` evidence bundle. Every required result-bearing member must identify the supporting experiment/source, critical result, exact location, transfer reason, transfer limitations, relevant regime differences, and decision use. A procedure-only member cannot complete the bundle. Each regime using transferred A names its `transfer_bundle_id`. An awareness-A bundle declares its `awareness_regime_keys` manifest; multiple regimes may point to it only when each key is in that scope and each has its own located critical result and explicit transfer assessment. Every declared regime must be supported by the required source-critical evidence. Other premises have an empty regime manifest. Independently complete alternative awareness bundles may retain the same truthful regime scope; the regime selects one active `transfer_bundle_id`, which must resolve to its own complete scoped support. Changing that selection requires a logged revision and fresh bound review. An unrelated complete bundle cannot repair this regime's incomplete or conflicted selected support. A result from a similar stimulus or another participant sample is never inherited automatically; sample, stimulus, suppression, timing, attention, task, environment, awareness procedure, and first-order-evidence regime remain explicit transfer dimensions. If the critical result is unavailable, the required member is unavailable and the bundle remains incomplete unless a distinct, explicitly justified transferable result independently supports A.

Objective invisibility evidence may support `A-direct` or `A-validated` only when all of the following are true:

1. the task directly tests perceptual access to the relevant X;
2. it has a meaningful objective chance or no-access baseline;
3. the design and amount of evidence are sufficiently sensitive for the invisibility inference being made; and
4. the observed result supports performance being at or sufficiently near that baseline.

Do not impose a universal modern equivalence-test or Bayes-factor requirement on legacy awareness-validation studies. However, a merely nonsignificant comparison against chance from an obviously underpowered or insensitive test is not sufficient. Every `A-direct` or `A-validated` classification using objective invisibility must record why the visibility test is sufficiently informative in `objective_visibility_test_reason` and set `objective_visibility_test_informative = yes`.

The relationship between A and E is asymmetric. Above-chance objective detection or discrimination does not by itself imply awareness and does not invalidate an independent subjective-unawareness classification; it primarily informs first-order evidence E. Conversely, sufficiently informative chance-level or no-access performance on an appropriate objective visibility task can support unawareness for A. Objective performance is therefore not a universally theory-neutral awareness measure, but neither is it categorically excluded from A.

### 2.2 E — first-order evidence about X

A quantitative signal-account test can qualify diagnostically when it explicitly tests the relevant same-Y prediction and its measurement, overlap and model assumptions are defensible. A generic regression adjustment is insufficient; retain reconstruction and model limitations in evidence ordering.

Physical identity of X does not guarantee matched internal evidence. Relevant objective first-order performance is a more direct internal-signal check than subjective reports or physical identity alone. This does not turn objective performance into a universal awareness criterion, nor guarantee that equal means match every task-relevant distribution.

- `E-matched`: aware and unaware conditions are matched on the relevant direct first-order measure of X. This requires achieved matching supported by (1) active matching or titration on that measure, (2) a successful explicit equivalence procedure using a stated margin, or (3) defensible post-hoc performance matching with adequate overlap, relevant distributions, and selection/measurement assumptions assessed. Record `post-hoc-performance-matching` and its limitations where applicable. Intended titration or similar means alone do not establish achieved matching. A merely nonsignificant aware/unaware comparison (`p > .05`) does not establish matching. An apparently narrow confidence interval without a predefined or explicitly stated equivalence criterion also does not establish matching.
- `E-diagnostic`: first-order evidence is not matched, but the structured result pattern rules out the relevant simple scalar explanation in which more first-order evidence about X merely strengthens the same downstream functional relation Y. Structures that may satisfy this criterion include threshold-linked nonmonotonicity, an experimentally shifted threshold accompanied by a shifted downstream effect, crossover/sign reversal, and a coherent factorial/process-selective interaction that changes the mapping from X/task relation to Y. No structure qualifies by its label alone: it must violate the justified same-Y prediction. It is not enough that unrelated Y1 and Y2 have different effects.
- `E-physical-only`: the physical stimulus or event is nominally matched, but direct first-order evidence is unequal or inadequately assessed.
- `E-uncontrolled`: outside the nominally identical-physical-X case, first-order evidence differs or is inadequately controlled or known, so a simple first-order-evidence account of Y remains viable.

`E-matched` and `E-diagnostic` are alternative strong routes, not rank-ordered tiers.

Their conclusions remain specific to the control supplied: matching addresses the measured first-order performance difference; a diagnostic pattern addresses the explicitly stated simple same-Y evidence-strength account. Neither code requires eliminating every possible evidence-dependent process architecture. The possibility that stronger evidence recruits a process accompanying both awareness and changed use does not, by itself, defeat a qualifying association. The bounded, independently anchored alternative checks in Section 2.3 still apply.

### 2.3 E assessment sequence and outcome neutrality

First assess E from the methods. Assign `E-matched` only when its positive matching requirements are met. Otherwise record the provisional non-diagnostic status—`E-physical-only` when physical X is nominally identical, and `E-uncontrolled` otherwise. Then inspect the full result pattern specifically to decide whether the frozen `E-diagnostic` criterion is satisfied. If it is, finalize E as `E-diagnostic`; if not, retain the provisional status.

This limited use of results does not make study selection depend on whether a result is theoretically attractive. The `E-diagnostic` criterion is frozen in advance, is applied to every eligible unmatched case, and is evaluated before unaware-capacity or awareness-effect classification.

Every `E-diagnostic` decision must record all of:

1. the competing simple evidence-strength account;
2. that account's prediction for the same focal Y;
3. the observed pattern that violates the prediction;
4. every experiment or analysis required for the inference, through source pointers and evidence links; and
5. why the evidence concerns one coherent focal Y rather than an opportunistic cross-Y dissociation.

Justify the competing prediction from the task, design, or independent evidence; do not select a prediction merely because the observed pattern contradicts it. Crossing chance or another reference baseline is not necessarily a reversal of the focal function: rule accuracy rising from below chance to above chance may remain a monotonic improvement with stronger information about X. Such a crossing alone does not defeat that simple signal account. A diagnostic pattern must instead challenge the relevant prediction for the operationally defined Y; independent manipulations or controls can strengthen that test without becoming a universal requirement for every diagnostic design.

Apply the prediction to signed effects as well as their magnitudes. A positive benefit growing while a negative cost becomes more negative can both be ordinary amplification of the same mapping by stronger information, even when their interaction is significant. Such a pattern alone is not diagnostic. Conversely, a planned reduction of a positive net functional effect with stronger evidence can challenge the independently justified simple strengthening account. Assess its actual critical comparison, precision and controls; a pattern label or omnibus statistic cannot repair a missing or incompatible premise. When a later control supplies the diagnostic test, bind the claim to that control or an explicit compatible joint premise, rather than silently assigning its E conclusion to an earlier experiment.

Before assigning `E-diagnostic`, also perform a bounded **contrast-integrity** check, in addition to the comparison-validity assessment required for both E routes. Ask whether the awareness/evidence contrast systematically differs in a separate task-state variable that can independently change the focal Y: instruction, learned contingency, explicit task-relation knowledge, response mapping, policy, attentional/control set, task relevance, feedback/training, or block-specific strategy. Sensory strength, masking, and unequal internal evidence are the ordinary first-order-E problem and do not by themselves fail contrast integrity.

Audit only alternatives that are finite, explicitly named, independently motivated by the design or task, capable of changing the same focal Y, and associated with an observable prediction or control. A classification-gating alternative must also have an independent evidential or design anchor: a design-imposed difference, a directly measured difference, reported behavioral evidence, an explicit manipulation check/control, or comparably direct design-based evidence. An anchor is necessary but not sufficient: a measured change in the very control or processing function under investigation is not automatically an extraneous alternative. Distinguish an independently changing task requirement or measurement explanation from a candidate common processing transition accompanying awareness and Y. The latter remains compatible with this review even when directly measured. A merely possible unmeasured endogenous covariate—such as attention, arousal, motivation, stronger-evidence process engagement, or executive control—may be recorded as a limitation but cannot veto `E-diagnostic` without such an anchor. A hidden process invented after seeing the result is inadmissible. An anchored extraneous difference in learned contingency, instruction, response requirement, scoring or task state remains classification-critical when it independently accounts for the target contrast; a sign reversal does not remove that explanation.

For every admissible task-state alternative, the E-diagnostic bundle must record the variable, why it is viable, its prediction, the required direct control member, and whether it is `ruled-out` or `unresolved`. Use a separate E-diagnostic bundle for each admissible alternative when more than one exists. If any viable alternative remains unresolved, `E-diagnostic` is prohibited and the applicable weaker E category is retained. When the task instructions, response mapping, contingency knowledge, policy, and physical task configuration are held fixed and no separate design-motivated task state is identified, record `not-applicable`; unequal trialwise sensory evidence alone does not block the ordinary E-diagnostic test.

Before finalizing any unmatched case as `E-diagnostic`, `E-physical-only`, or `E-uncontrolled`, perform and record a bounded semantic scan of the entire supplied article record for another experiment, analysis, supplement, or explicit control designed to test the focal first-order-evidence alternative. Record `alternative_control_scan_status` and a reason. A candidate is not automatically accepted: establish that it addresses the same conservative focal Y/factorial mapping, assess cross-experiment transfer, name the alternative, and classify its role as required, strengthening, robustness, or irrelevant. Classification-critical support requires an explicit E bundle/link. If an apparently classification-critical within-paper control is unavailable or unevaluated, keep its bundle/dependency incomplete and do not finalize E. A control concerning a different downstream function cannot repair focal E.

For a factorial-functional comparison, apply `E-diagnostic` to the **whole focal functional relation**, not opportunistically to one component. Component simple effects may differ in strength while their joint structured mapping rules out the specified same-Y scalar account. When required support spans experiments, analyses, or sources, a strict evidence bundle must identify the member that addresses the first-order-evidence alternative. An interaction or cross-Y dissociation alone is never sufficient: the same-Y/coherent-functional-relation requirement and every ordinary `E-diagnostic` requirement above remain mandatory.

For example, Experiment A may find a downstream extremum around a detectability threshold, while Experiment B experimentally shifts detectability and the downstream extremum shifts correspondingly. If the complete, premise-specific evidence bundle shows that this joint same-Y pattern violates the stated simple signal-strength prediction, it may support `E-diagnostic`; the extremum alone does not.

### 2.4 F — meaningful downstream use Y

F is primarily an eligibility gate, not an ordinal score.

- `F-meaningful`: the dependent measure identifies a defensible distinct downstream functional relation or use of X at an appropriately conservative level, such as regulation/control of distractor interference, metacognitive evaluation, updating, binding, maintenance or memory, action selection, rule-guided use, or adaptive use. The exact cognitive or neural mechanism implementing that function need not be identified.
- `F-ambiguous`: the dependent measure plausibly reflects downstream use or transformation beyond direct registration or report, but even a conservative function-level Y cannot be assigned without choosing among substantively different downstream uses.
- `F-not-meaningful`: the dependent variable establishes only direct detection or discrimination of X, generic registration, a generic neural response, or generic priming whose principal implication is merely that some information about X survived.

Assign Y at the most specific functional level justified by the dependent measure. Do not make Y artificially fine-grained, and do not require the experiment to identify the mechanism implementing Y in order for Y to be meaningful. For example, a behavioral measure may justify `Y = regulation/control of the behavioral influence of a task-irrelevant distractor` while leaving active spatial suppression, inhibitory control in LPFC, attentional filtering, altered capture, and other implementations unresolved. That is `F-meaningful` with ambiguous mechanism, not `F-ambiguous`.

For every comparison, record `Y_label`, `Y_description`, `Y_evidence_role`, and `Y_interpretation_clarity` separately from `mechanistic_interpretation` and `mechanism_clarity`. `mechanism_clarity` is never part of the F gate. Neural evidence may support a proposed mechanism for a behavioral Y, but a generic neural difference is not itself a qualifying Y merely because it is compatible with that mechanism. `F-ambiguous` supports discovery recall but does not pass the strongest empirical-lot filter, which continues to require `F-meaningful`.

Use the existing description, comparison, reason, and notes fields to identify the measured outcome and explain how it supports Y. State the information-bearing X separately from the experimenter's parameter or relation code, and state awareness of that information separately from recognizing or reporting it. The same measured outcome does not establish the same mental function when substantively different downstream uses can produce it. A significant profile or crossover strengthens the observed relation but does not identify its function by its shape alone. Interference with a task requiring control is not automatically use of X to accomplish that control. Preserve material population, task, temporal, and awareness-report limitations in the constraint statement or notes; record missing information explicitly rather than inventing it. A delayed probe effect does not alone establish continuous active maintenance, and a brief-trial capacity does not by itself establish sustained functioning. These are applications of the existing F rule, not an additional measurement taxonomy or settled-mechanism requirement.

Also record `Y_functional_status` and a semantic reason. `F-meaningful` requires Y to be an audited `downstream-function` or `coherent-functional-mapping`; `F-ambiguous` uses `function-unclear`; an observed modulation, interference score, priming effect, or other effect label without a defensible downstream function is `effect-only` and cannot become `F-meaningful` merely because it is nonzero. Evidence that X causes an effect on Y is not automatically evidence that the effect itself is a capacity. This is a semantic audit, not a lexical rule: use the operational input→output relation and explain the judgment.

Before finalizing a strong claim, record a source-linked `promotion_challenge` for the applicable premise. For `F-meaningful`, challenge whether the named Y is a distinct downstream function rather than direct detection, discrimination, or registration of X. For `E-diagnostic`, challenge whether the independently justified scalar prediction and its violation concern that same focal Y or coherent functional mapping; a different Y may supply context but cannot carry the focal inference. For `unaware_capacity = supported`, challenge whether positive evidence covers the whole exact named `Y_label`; keep a positive component or partial-X residual at its own scope. For comparison-wide `A-direct` or `A-validated`, challenge whether each contrasted arm/regime has an actual source-located critical awareness result for the exact X and whether any transferred result has a justified scope. For supported unaware capacity, separately challenge whether each explicitly selected capacity regime has adequately supported exact-X unawareness (`unaware_regime_awareness`), including its direct result or complete regime-specific transfer. Record the verdict, reason, and article locations for each applicable challenge. An unresolved or contradicted premise remains at the applicable weaker classification until resolved; this challenge adds no numerical threshold.

### 2.5 Mandatory pre-atomization functional-structure check

Perform this check after enumerating the physical experiment and **before** final comparison decomposition or scalar-row finalization. Persist one physical-experiment-group record even when its final disposition is `support-only` or `no-qualifying-comparison`; those dispositions must not generate placeholder X→Y rows. For every experiment containing multiple relevant factors, cells, or simple effects, ask:

1. Is the critical scientific hypothesis or inferential statistic testing whether X changes one coherent downstream functional mapping across conditions?
2. Do the component cells or simple effects jointly operationalize that same conservative function-level Y?
3. Is the critical evidence an interaction, crossover, conditional mapping, or structured pattern whose scientific meaning would be lost if the cells were evaluated only as separate scalar Ys?

If yes, instantiate the factorial-functional focal X→Y comparison first, record its component effects, and assess A/E/F and any evidence bundles for that whole relation. Scalar/component comparisons may additionally coexist when they independently answer meaningful X→Y questions, but they must link to and never replace or suppress the focal comparison.

If no, scalar decomposition is allowed. Record why the cells represent genuinely distinct downstream functions or why no coherent common Y is defensible.

Determine functional identity from the operational/computational input→output relation, not from conventional effect names, effect signs, or proposed mechanisms. Before declaring multiple components to be different Ys, explicitly consider:

1. whether the same information-bearing X variables are used;
2. whether the same downstream task/output variable is measured;
3. whether the cells occupy the same relevant task and temporal/computational stage;
4. whether the factor changes a relation or property of X rather than replacing the downstream operation;
5. whether the critical higher-order statistic asks how one input→output mapping changes across factor levels; and
6. whether a conservative common function can be stated without committing to distinct mechanisms.

When the relevant answers establish one operational mapping, instantiate the factorial-functional focal comparison first. Labels such as facilitation, interference, benefit, cost, capture, or suppression ordinarily describe component effects. Labels such as updating, inhibition, filtering, or disengagement ordinarily describe proposed mechanisms. Neither kind of label establishes a separate Y without independent function-level evidence.

Scalar separation remains appropriate when dependent variables operationalize different downstream functions, effects occur at substantively different temporal/computational stages, the scientific questions concern different input→output relations, or no conservative common function exists. Record a positive `functional_identity_basis` for that separation; “different effect names” or “different mechanism labels” is not a valid basis.

Use `functional_structure_assessment` as follows:

- `not-applicable`: the experiment has no multiple relevant factors/cells/simple effects requiring the check;
- `scalar-justified`: the check was performed and separate scalar Ys are scientifically warranted;
- `factorial-functional-required`: the check was performed and a focal factorial-functional comparison is required; or
- `not-assessed`: temporary state only, never permitted for a fully evaluated row.

Record the durable rationale in `functional_structure_reason`. A scalar component that coexists with a focal factorial comparison records its focal ID in `factorial_focal_comparison_id`.

### 2.6 Scalar and factorial-functional Y

Record `Y_structure = scalar` when the downstream function is operationalized by one simple effect or a set of interchangeable measures. Record `Y_structure = factorial-functional` when the focal Y is a functional mapping across experimentally defined relations or task states.

A factorial functional relation remains one comparison only when:

1. a conservative common function-level Y can be stated;
2. the design treats the component conditions as parts of one functional question and the critical hypothesis/statistic genuinely concerns that mapping;
3. the simple effects jointly operationalize how the same downstream system uses X under different task relations or states;
4. grouping does not conflate substantively distinct downstream processes; and
5. the relation is empirically operationalized rather than imposed post hoc merely to obtain a preferred E code or result.

Record each component simple effect in `factorial_component_effects`. Do not split a coherent relation merely because its interaction has multiple cells. Conversely, `interaction exists` does not imply one factorial Y: do not merge genuinely different downstream functions or construct a grouping merely to rescue E.

## 3. Independent scientific inferences

Determine A, E, and F before assigning either inference below. The two fields are independent rather than mutually exclusive.

### 3.1 Unaware capacity

An unaware-capacity judgment asks whether the comparison's one **focal downstream function** demonstrably operates on X while X is unaware. It does not ask merely whether unaware X has any measurable downstream consequence. Record `unaware_capacity_claim` as the exact `Y_label` for that comparison and record `unaware_capacity_reason` separately. One comparison therefore has one focal Y and one possible unaware-capacity target.

Use `unaware_capacity`:

- `supported`: positive evidence shows that Y actually uses X in the X-unaware condition;
- `not-supported`: the tested unaware condition provides affirmative evidence against the specified capacity or lacks the required positive Y effect under an adequate test;
- `unclear`: the capacity was relevant and tested, but evidence or reporting is insufficient for either conclusion; or
- `not-tested`: the comparison does not test Y in an X-unaware condition.

`supported` does not assert that awareness makes no difference. A comparison may simultaneously have `unaware_capacity = supported` and `awareness_effect = difference-supported`. However, a nonzero downstream effect is insufficient by itself: the positive effect must instantiate the function named in `unaware_capacity_claim`. Evidence for interference, automatic bias, or another consequence cannot establish control, strategic rule use, or a different capacity.

For a factorial-functional comparison, do not infer unaware capacity for the focal function merely because one component is nonzero under unawareness. `unaware_capacity = supported` requires positive evidence for the whole focal mapping and `unaware_capacity_evidence_scope = whole-focal-Y`. If a component function is independently meaningful and scientifically useful, instantiate a linked component comparison whose own `Y_label` names that component. Only that component row may assess its capacity, and it must independently satisfy F, positive unaware evidence, route-specific statistics, and the separately recorded Meyen audit. A component result cannot be coded as a different capacity inside its parent focal row.

The strong unaware-capacity route requires:

1. regime-local `A_code` in `{A-direct, A-validated}` for exact-X unawareness in every explicitly selected capacity regime, with its located critical result and justified transfer where used; comparison-wide A need not be strong for this ordinary route;
2. `F_code = F-meaningful`;
3. a non-empty `unaware_capacity_claim` naming the function positively demonstrated under unawareness;
4. exact identity between `unaware_capacity_claim` and `Y_label`, with `unaware_capacity_evidence_scope = whole-focal-Y`;
5. `unaware_capacity = supported` for that same named function;
6. interpretable route-specific statistics (`adequate`, or `concern` with nonfatal limitations); and
7. an actually tested unaware condition. Meyen is recorded separately and does not gate this route.

A capacity-only study without an awareness contrast is supplementary, never a main awareness finding. A supported supplementary capacity may earn a Y-specific search. If no unaware condition was tested, use `unaware_capacity = not-tested`; do not manufacture a capacity result for graded-only comparisons.

E remains recorded but is not a gate for this route. E addresses whether the awareness-linked contrast survives the relevant simple first-order-evidence explanation under Section 2.2; it is not logically required to show that Y operates in a validated unaware condition.

Keep four conclusions separate: a supported awareness-linked constraint on the same Y, positive use of the **whole focal Y** under demonstrated exact-X unawareness, a residual effect for which only partial X or coarse stimulus presence is established, and other useful support. A partial-X residual effect is visible in the record but is not a formal exact-X unaware capacity. Weak E for an awareness-effect claim does not erase a separately supported exact-X capacity. A positive factorial component does not establish capacity for its parent functional mapping. Positive aware use and positive unaware use are equally eligible for assessment; neither direction is preferred.

### 3.2 Effect of awareness

The field name `awareness_effect` denotes the observed awareness-linked comparison, not an independently established causal effect of awareness. A constraint-ready awareness-linked difference is a supported association available to constrain abductive theory construction, with the scope of its E control retained.

Use `awareness_effect`:

- `difference-supported`: a directly tested difference across awareness conditions/degrees or interaction supports a change in Y;
- `no-detectable-difference`: the relevant difference or interaction was directly tested, effect estimates are interpretable, no credible awareness-linked difference was detected, the conclusion is not based on separate significance tests, and robustness/sensitivity limitations are recorded;
- `equivalence-supported`: region-based evidence rules out differences outside a justified equivalence region under Section 4.2;
- `null-supported`: positive Bayesian support for the specified null relative to its specified alternative, without claiming practical equivalence;
- `unresolved`: the awareness comparison is relevant but does not meet another category; or
- `not-tested`: no awareness comparison relevant to Y was tested.

`no-detectable-difference` does not mean equivalence. A bare, uninformative `p > .05` normally remains `unresolved`.

Record whether a direct comparison across awareness conditions or degrees on the same focal Y was performed in `difference_tested`, independently of E. A performed analysis requires `difference_analysis_scope` (`focal-experiment` or `joint-analysis`), source location, statistic/test, and `difference_analysis_origin` (`author-reported` or `reviewer-derived`). A focal analysis names its own experiment. A joint analysis lists every contributing physical experiment in `difference_joint_experiment_ids`, including the focal experiment and source anchor, and requires a complete `awareness-effect` bundle documenting design, measure, population and analysis compatibility. It must directly test the intended contrast; comparing significance labels from separate experiments is insufficient. Reviewer-derived statistics require sufficient located inputs and a reproducible calculation, assumptions and limitations in `difference_derivation`; do not invent missing covariance or silently choose discretionary analyses. Retain this provenance in qualitative ordering. Every direct comparison receives a descriptive result audit; weak E cannot convert a performed test into `not-tested`.

If the test was performed but its estimate is uninterpretable or inadequately reported, retain `difference_tested = yes`, record `awareness_effect_estimate_interpretable = no` or `unclear`, and use `awareness_effect = unresolved`. Explain the unavailable or uninterpretable estimate in the estimate and statistical-reason fields. Such a record may be fully evaluated: completion of its audit does not imply a conclusive scientific answer. Conclusive difference, no-detectable-difference, and equivalence categories still require interpretable estimates.

When a direct difference is statistically supported but A/E/F do not make the strong awareness-effect route viable, record the observed test and statistics but use `awareness_effect = unresolved`. When a direct test detects no credible difference and the descriptive requirements in Section 4.2 are met, `no-detectable-difference` remains available even with weak E. Positive equivalence evidence may likewise be recorded under Section 4.2, but the strongest constraint-ready invariance route still requires strong A, strong E, and meaningful F. Use `not-tested` only when no relevant direct same-Y comparison was tested or reported.

The strong awareness-linked-difference route requires:

1. `A_code` in `{A-direct, A-validated}`;
2. `E_code` in `{E-matched, E-diagnostic}`;
3. `F_code = F-meaningful`;
4. `awareness_effect = difference-supported`;
5. `difference_tested = yes` with valid focal or joint provenance and interpretable statistics (`adequate` or nonfatal `concern`); and
6. a comparable awareness contrast under the scope and validity checks above. Meyen does not gate.

The strong equivalence and Bayesian-null routes require strong A/E/F, a comparable directly tested awareness contrast, interpretable statistics and the appropriate positive null evidence. They also apply to graded contrasts without an unaware arm. Equivalence of measured outcomes does not establish that Y operates in either regime: a claim of preserved capacity separately requires positive evidence for that exact whole function. Do not infer capacity from two absent effects.

Use one direction label where applicable: `aware>unaware`, `unaware>aware`, `qualitative-change`, `no-detectable-difference`, `equivalent-within-region`, or `other`.

## 4. Statistical audit

Every full-text comparison receives a separate audit with overall status `adequate`, `concern`, or `unclear`.

### 4.1 Critical difference

For every relevant direct same-Y aware/unaware comparison, determine whether the difference or interaction was itself tested and audit its estimate and statistics regardless of E strength. Do not accept “significant in aware + nonsignificant in unaware” as evidence that the two conditions differ. A statistically supported direct contrast with weak E is descriptive evidence that regimes differ, not a constraint-ready awareness effect, and remains `unresolved` on the awareness-effect axis.

### 4.2 No detectable difference and equivalence

`no-detectable-difference` may be assigned without modern equivalence evidence only when the critical interaction/difference was directly tested, the estimates are scientifically interpretable, no credible modulation was detected, and sensitivity/robustness limitations are explicit. Separate within-condition significance tests are insufficient. A bare uninformative nonsignificant result remains `unresolved`.

`equivalence-supported` requires region-based evidence (items 1 or 3 below). `null-supported` requires positive Bayesian evidence (item 2), with the tested models and prior assumptions recorded in the null/statistical reasons. Assign `null_evidence_adequacy = adequate` only when the study provides at least one of:

1. a successful equivalence test using an explicitly stated or justified equivalence margin;
2. `BF01 >= 3` in favour of the null; or
3. a confidence interval entirely contained within an explicitly stated smallest-effect or equivalence region.

A merely nonsignificant aware/unaware difference or interaction receives `weak` null evidence even when the more modest `no-detectable-difference` category is warranted. Insufficient reporting receives `unclear`. Do not invent an equivalence margin for a legacy study. Retain `null_evidence_strength` to describe the evidence form.

### 4.3 General concerns

Where relevant, flag multiple-comparison problems, inappropriate statistical models, pseudoreplication, materially selective exclusions, critical exploratory or unconfirmed analyses, and other obvious problems. State why each flag matters to the critical inference. `concern` denotes an interpretable result with nonfatal qualifications and is retained with those qualifications; a claim-invalidating defect or unavailable critical information leaves the result unresolved. Exploratory status, a single patient, limited precision or a sensitivity analysis crossing .05 is not an automatic exclusion. Record `evidence_strength_reason` for every fully evaluated comparison: awareness support, relevant signal control, functional interpretation, analysis provenance, statistical precision/robustness and independent convergence/conflict. Use qualitative ordering with reasons, not a numerical score. Stronger tests can carry more weight; matching and diagnostic routes are not ordered by name alone.

For each concern, explain whether it invalidates the scoped inference, weakens confidence or changes precision. Distinguish exclusions based on task quality from selection on the focal effect; neither is resolved by the label alone. Audit the critical effect and direct contrast at their own scope, including available sensitivity estimates, rather than treating a change in significance as a change in whether the function exists. A qualified descriptive preserved-capacity claim can retain nonfatal concerns in both its positive-capacity analysis and its direct nondifference analysis. It must still have positive whole-Y evidence and an interpretable actual test; the concern category cannot fill a missing premise or convert descriptive nondifference into equivalence.

Synthesis must visibly retain suggestive and complementary findings, including supplementary capacities. Contradictory evidence yields a scoped `mixed` synthesis, with reasons based on relevance, quality and independence rather than vote counts; do not delete an original scoped finding unless invalidated. Agreement among review models is not empirical replication.

## 5. Meyen diagnostic

Apply this diagnostic when a study reasons that (1) a direct measure of X is at or near chance or nonsignificant, (2) an indirect measure shows an effect, and therefore (3) X was processed unconsciously. Meyen et al. require evidence for an **indirect task advantage**: the indirect measure must be shown to be more sensitive to X than the direct measure on a comparable scale.

Record `Meyen_role` before recording status:

- `inference-critical`: the unconscious-processing claim materially rests on a direct task being at/near chance or nonsignificant plus a positive indirect Y effect, with the indirect effect serving as the evidence that X-information survived, and without an independently adequate protocol-approved basis for the awareness classification. This label records the role of the diagnostic in the source inference; `Meyen-failed` or `Meyen-unassessable` does not automatically block inclusion or penalize the main ranking.
- `supplementary`: residual-information concerns remain relevant, but unawareness is already established through a dedicated, sufficiently informative validation whose adequacy and transfer are independently justified. Relevant support may include participant/regime-specific staircasing, dedicated validation blocks, post-task revalidation, sensitivity controls, and appropriate transfer. Preserve failure or unassessability prominently, but it does not gate an otherwise valid constraint.
- `not-applicable`: the study does not make the direct-chance plus indirect-effect inference described above.

`Meyen_applicable` remains as a consistency field: it is `yes` for `inference-critical` and `supplementary`, and `no` for `not-applicable`. When applicable, use `Meyen-satisfied`, `Meyen-failed`, or `Meyen-unassessable`, and explain why. Do not automatically make objective-invisibility cases supplementary; state what dedicated validation independently establishes awareness status. Passing does not itself prove unconscious processing and does not replace A.

Meyen application, result and assessability remain visible in a separate diagnostic display. Main eligibility and qualitative ordering use their independently justified A/E/F and statistical judgments, never a relabeled Meyen veto.

## 6. Screening funnel

Every encountered paper remains in the master audit record. Every decision includes a brief why.

Title and abstract screens are semantic decisions under this protocol. Agents may process records in batches only as context amortization, but each paper receives its own decision, method, reason, and durable write. Batch membership is never evidence. Regex/keyword rejection, embedding thresholds, citation-count thresholds, numerical LLM relevance scores, and hidden lexical heuristics may not independently produce an exclusion. The candidate registers no deterministic scientific exclusion rule.

### 6.1 Title screening

Bias toward recall. Exclude only when irrelevance is clear. Record the decision and reason.

### 6.2 Abstract screening

Use `screen-in`, `screen-uncertain`, or `screen-out`. `screen-in` means the abstract plausibly contains X, an awareness contrast concerning X, and a distinct downstream Y. Unknown A or E details are not grounds for exclusion.

For `screen-in` and `screen-uncertain`, assign full-text priority `high`, `medium`, or `low`, with a reason. For `screen-out`, leave full-text priority `not-assigned`. Never make a final A, E, or F classification from an abstract alone.

Record `abstract_status` separately as `not-sought`, `available`, `unavailable`, or `not-applicable`. Failure to obtain an abstract is not a screen-out decision. A title-retained paper with `abstract_status = unavailable` remains in the audit and receives a reasoned full-text priority from its title, discovery provenance, and available metadata. It may proceed to retrieval when that priority warrants.

When available, preserve the exact abstract text, source, acquisition time, and SHA-256 used in the semantic decision. A changed abstract version is new decision-relevant evidence and requires a logged revision before reuse. Unavailable abstracts retain a reasoned state without invented text or a fabricated hash.

The abstract screen asks whether full text could contribute to the X→Y review or a source-linked manuscript reading pool. It does not require abstract-level proof of final A, E, F, statistics, or Meyen. Missing controls or uncertainty about exact X/Y is not negative evidence. If plausible value remains, use `screen-in` or `screen-uncertain`, explain why, and attempt full text under Section 7. A routing priority is not a scientific exclusion.

At screening, identify the plausible contribution and what the full text would need to resolve. Do not demand proof of a final primary/support role. A putative awareness comparison with uncertain controls or a potentially interpretable downstream function remains worth assessment; a known unaware-only finding remains available through the existing scientific and discovery routes without being represented as an awareness-comparison prospect. Unknown detail and established absence are different states.

Title decisions require only a paper-specific decision and reason. An uncertain title advances to the abstract. At abstract screening, distinguish a clear outside-scope exclusion from a consequential scientific exclusion: any exclusion depending on whether an awareness-related experiment could contribute receives a fresh source-only review before finalization. This second reader receives the source and instructions, not the previous verdict, asserted features or expected answer. Unknown controls remain unknown; no rescue route itself confers A/E/F or main status.

Audit clear outside-scope exclusions independently of the first reader's feature assertions. Use cumulative current-exclusion cohorts defined by discovery source/route and original screening stage, freeze a deterministic hash sample of up to ten per cohort (all when fewer than ten), and assess each sampled paper from source alone. Incremental intake updates the cumulative frame; only still-current exclusions are eligible. A reproduced miss reopens the currently excluded cohort for source-bound review. Do not resurrect superseded exclusions, erase prior judgments, or treat this sample as a recall estimate. The recorded source/evidence revision and current stage govern whether a result may update present state. A source-only rescue that already assessed the abstract fulfills that abstract stage.

Structured dissociations, response priming, bodily/interoceptive functions, agency, affect/motivation, patient cases, perceptual history, metacognition, learning, memory, language, social and action uses remain prompts for careful reading, not a feature checklist or eligibility whitelist. A detailed semantic feature instrument may assist an assessor, but is not required in every title/abstract response and does not decide eligibility.

## 7. Full-text retrieval and missing texts

Every `screen-in` and `screen-uncertain` paper receives a full-text attempt, across every discovery route. Title-retained papers with unavailable abstracts also receive an attempt. Priority governs order, not eligibility.

Attempt, in order:

1. Published full text.
2. Open repository or accepted manuscript.
3. A preprint containing the relevant experiment.

If unavailable, assign `ask-text-high`, `ask-text-medium`, or `unavailable-low-priority`. After each search wave, surface only a bounded batch of the highest-priority missing texts. Do not block the rest of the search while waiting for manually supplied papers.

No final A, E, or F classification is allowed without full text. A likely relevant missing paper may provisionally serve as a citation-network node.

When a user supplies requested full text, preserve its later provenance: associate the file with the paper ID, record its repository-relative manual-ingestion path and a SHA-256 hash where practical, update the missing-text state, and evaluate it on resume. Do not represent it as having been available in earlier waves. New citation or process-search obligations activated by the text reopen the corresponding stopping condition under the unchanged frozen protocol.

For every obtained full text, regardless of source, record `obtained_at`, `obtained_wave`, `obtained_by` (`agent`, `user`, or `preexisting`), and `acquisition_route`. Acquisition provenance must describe how the target article was obtained and verified; a nominally free link is not sufficient.

Within one run, the verified article/version is a reusable factual asset for every comparison and evidence bundle concerning that logical paper. Resolve identity, verify the article/version, hash the file, and extract it once per extraction-tool/version. A materially different version receives a separate durable asset record and never silently overwrites the verified source. This reuse changes no scientific classification.

## 7.1 Classification-critical auxiliary evidence

Before finalizing A, E, F, or a statistical classification, inspect the candidate article and supplement for an explicit dependency on an external source for a classification-critical premise. Examples include a cited prior visibility validation, a cited perceptual threshold, matching or titration established elsewhere, or an external statistical method required to interpret the critical analysis.

This dependency check is not ordinary citation-network expansion. When a dependency exists:

1. retrieve and inspect the cited source where reasonably possible;
2. evaluate only the classification-critical claim for which it was cited;
3. record it in `auxiliary_sources.csv` and link it to the target comparison;
4. assess transfer where the purpose is awareness validation, explicitly covering stimulus parameters, masking/suppression, timing, attentional allocation, task demands, and participant population; and
5. only then finalize the affected classification.

If the source cannot be obtained, record an unresolved auxiliary dependency and assign the A/E/F/statistical category warranted by that uncertainty. Do not silently treat the cited evidence as nonexistent and do not silently accept the article's claim.

Auxiliary sources do not need to pass the X→Y title/abstract screen merely to be consulted. Consultation does not add them to the candidate-paper pool, make them citation-network nodes, or trigger expansion. They may enter the ordinary pipeline only if independently encountered under the registered discovery rules.

### 7.2 Structured evidence bundles

A **scientific evidence bundle** is a structured argument specifying which experiments, analyses, validations, or auxiliary sources jointly warrant one named premise of one focal X→Y comparison. It is scientifically substantive. An **execution evidence assessment/cache** stores a reusable factual assessment to avoid repeated parsing. It is not scientific evidence linkage and may not propagate A, E, F, outcome, statistics, or Meyen classifications. The two objects must never be conflated.

Every scientific bundle is a first-class `evidence_bundles.csv` row with one `focal_comparison_id`, one controlled `supported_premise`, a premise description, a route label, an explicit manifest of required member keys, status, reason, and notes. The manifest is fixed before evaluating member outcomes so a missing required link remains auditable. One bundle supports one named premise of one comparison. If the same underlying evidence supports two premises or two comparisons, create separate bundles and explicit links for every scientific use. If an independent route establishes the same premise, represent it as a separate bundle.

Use `bundle_status`:

- `complete`: every member marked `required` is available, evaluated, transfer-valid enough, and supportive, with no unresolved contradiction that defeats the premise;
- `incomplete`: a required member is unavailable, unevaluated, or transfer-invalid; or
- `conflicted`: evaluated evidence contains a substantive unresolved contradiction relevant to the premise.

Independent contradictory replications retain their own comparison records and contribute to a mixed synthesis. They do not retroactively become required members of an original scoped premise unless they actually invalidate that premise. Keep a claim about one experiment separate from a claim about cross-study generality.

An incomplete or conflicted bundle cannot silently establish its premise. Conflicting evidence is not averaged into completeness. A separate complete independent route may establish the premise only through its own bundle.

Each `evidence_links.csv` row is one explicit scientific use. `support_role` records what support is provided: awareness validation, first-order-evidence control, E-diagnostic support, alternative-explanation control, replication, statistical support, robustness, generalization, mechanistic support, or other. Orthogonal `dependency_role` records whether it is `required`, `strengthening`, `robustness`, `generalization`, or `mechanistic`. A missing non-required member does not by itself make the premise incomplete. Every link records its member status, exact supported claim, source/experiment/analysis, source location, transfer reason, and transfer limitation.

For cross-experiment/regime evidence, assess the relevant transfer dimensions—stimulus parameters, masking/suppression, timing, attentional allocation, task demands, participant population, awareness measurement, and first-order-evidence regime—without mechanically discussing irrelevant dimensions. Same-paper location never supplies transfer by itself.

Evidence support is not transitive. If Exp. 2 supports Exp. 1 and Exp. 3 supports Exp. 2, Exp. 3 supports Exp. 1 only through a separate explicit link with its own rationale and caveats. Paper-level statements, awareness validations, E-diagnostic arguments, and auxiliary evidence likewise do not automatically propagate across experiments, regimes, Ys, premises, or comparisons.

A supporting experiment does not become a candidate X→Y comparison merely because it supports a focal inference. Give it a comparison row only when it independently answers an X→Y question. Evidence links never substitute for comparison-specific A/E/F/statistical coding.

## 8. Full-text comparison evaluation order and route-aware analysis

Read toward a compact argument: what this could add to the awareness–use profile, which experiment/result supports it, and which alternative or missing premise limits it. Form that argument from sources before proposing a reading role, then record the scientific judgments in the order below. A tentative role cannot supply a missing premise, and a weak or unresolved scientific code does not by itself erase a plausible prospect.

First enumerate each physical experiment. Before final comparison decomposition, perform the mandatory pre-atomization functional-structure check in Section 2.5 and record its decision and why. When the check requires a factorial-functional relation, instantiate that focal comparison before any optional scalar/component comparison. Assign separate scalar comparisons only when they independently answer meaningful X→Y questions or when the check justifies genuinely distinct downstream functions. Unaware capacity and awareness effect are separate fields and do not require duplicate comparison rows merely because both inferences apply. Then, for each comparison:

1. Identify X, population relevance, the awareness contrast (including graded/probability regimes), whether an unaware condition was tested, and comparison validity with reasons.
2. Identify the awareness measure or validation separately for every arm or graded regime, distinguishing focal-task critical results from transferred results and recording why each bears on the exact X.
3. Identify the direct first-order evidence measure.
4. Identify Y at the most specific conservative functional level justified by the dependent measure; carry forward the recorded pre-atomization decision, assign scalar versus factorial-functional structure, record component simple effects and any linked optional scalar comparisons, and record finer mechanistic interpretation separately.
5. Check the article and supplement for classification-critical dependencies or supporting analyses. Resolve external auxiliary sources where reasonably possible, create one scientific bundle per focal premise, and create an explicit link for every scientific use.
6. Assign A from the qualifying awareness evidence, record `awareness_evidence_type`, and explain objective-test informativeness where applicable.
7. Assign F from the downstream-use design and explain why.
8. Record the Y evidence role and function-level interpretation clarity separately from the proposed mechanism and mechanism clarity; do not use mechanism ambiguity as the F gate.
9. Assess design-based E: assign `E-matched` if its positive requirements are met; otherwise record provisional `E-physical-only` or `E-uncontrolled`.
10. If evidence is not matched, inspect the structured pattern only to test the frozen `E-diagnostic` criterion; record the competing account, its prediction, the violating pattern, same-Y justification, source locations, required evidence links, and the bounded contrast-integrity disposition for every design-motivated task-state alternative.
11. Finalize E and explain why.
12. Record route viability and a reason. The awareness-effect route is viable only with a comparable awareness contrast in a relevant population, strong A, strong E, and `F-meaningful`. The unaware-capacity route is viable with strong exact-X A in the explicitly selected unaware capacity regime(s), `F-meaningful`, and an actually tested unaware condition; **E is not a gate**. A null/equivalence audit is required only when the comparison actually supports that scientific question.
13. Set `unaware_capacity_claim` to the exact focal `Y_label`. When its route is viable, inspect the results enough to determine whether that same focal function is positively demonstrated, record whether the evidence covers the whole focal Y, and record its critical statistics and applicable Meyen audit even when E is weak. A component capacity requires its own linked comparison. Independently record any positive partial-X residual effect without promoting it to formal exact-X capacity.
14. Independently record whether a direct same-Y aware/unaware comparison was performed. If so, audit its observed result, estimate, interpretability, and statistics even when the strong awareness-effect route is not viable. Reserve `difference-supported` for the strong route; use `unresolved` for a significant descriptive difference under weak A/E/F. Use `not-tested` only when the direct comparison is absent.
15. When a direct null-oriented comparison yields a candidate no-detectable, Bayesian-null or equivalence conclusion, record the structured null-evidence basis, `null_evidence_strength`, and `null_evidence_adequacy`; never conflate no-detectable-difference with equivalence. Otherwise record why the null audit is not required.
16. Perform the overall statistical audit and record relevant robustness concerns.
17. Assign the Meyen role and apply the diagnostic when relevant, explicitly stating whether dedicated awareness validation makes it supplementary.
18. Write a one- or two-sentence empirical-constraint statement that keeps the two inference axes distinct. For an awareness-linked difference, state the functional co-occurrence and the measured performance difference or specified simple evidence-strength account addressed by E; preserve material scope limitations without requiring independent causal attribution or inventing unanchored alternatives.
19. Record page, figure, table, analysis, auxiliary-source, bundle, and evidence-link locations.

## 9. Discovery routes and stopping rules

The registered sweep combines all four routes below.

Execute the principal routes first: empirical seeds, review/discovery anchors, citation waves, full-text evaluation, and every activated process search. After their frontier is provisionally satisfied, execute the mandatory supplementary blind lane. A new citation-eligible node reopens citation expansion; a genuinely new independently qualifying Y reopens/activates its process search. Completion requires every reopened frontier to satisfy the same unchanged stopping rule. This ordering changes no discovery obligation.

### 9.1 Empirical-seed citation graph

Begin with the frozen empirical seeds. A newly discovered full-text empirical paper becomes a backward/forward citation-network node when at least one experiment contains all of:

1. a specific X;
2. a genuine awareness contrast concerning X (including degrees or probabilistic regimes), or a substantive attempt to establish such a contrast or unaware capacity; and
3. a distinct plausible downstream Y coded `F-meaningful` or `F-ambiguous`.

For discovery expansion only, a **substantive attempt** at an awareness contrast is a manipulation, grouping, or subjective measurement explicitly intended to assess awareness levels/regimes or establish unawareness of the relevant X, even if the resulting evidence is too weak to satisfy `A-direct` or `A-validated`. This keeps borderline papers available as discovery nodes; it does not weaken the empirical-lot criteria.

Weak A or E does not prevent expansion. Papers containing only generic registration or priming coded `F-not-meaningful` do not automatically seed recursive expansion. For unavailable full texts, an `ask-text-high` paper may act provisionally as a node only when its abstract explicitly supports the same X + awareness contrast + distinct plausible Y structure. Review and discovery anchors are expanded separately under their own route. Record every expansion decision and why.

### 9.1.1 Strict one-hop empirical bridge

In addition to CORE nodes above, a logical paper is a strict **BRIDGE** node only after adequate full-text evaluation establishes that it is empirical, is not CORE, and contains at least one single physical experiment that is a genuine near-neighbor of the target design and clearly contains **exactly two** of the three CORE ingredients. The remaining ingredient must explicitly fail; an unclear, unknown, or unassessed ingredient does not qualify. The two present ingredients and the failed ingredient must co-occur in that one experiment and may not be assembled across experiments. The record must identify all three ingredient states, the failed ingredient, and a positive scientific rationale for why the experiment is a meaningful near-miss. Reviews, theories, perspectives, commentaries, methods-only works, and generic conceptual papers cannot become dynamically generated BRIDGE nodes. Title or abstract evidence alone cannot establish BRIDGE status, and missing full text is not evidence that an ingredient failed.

Paper status is derived from its physical experiments with CORE precedence: any CORE experiment makes the paper CORE; otherwise any strict bridge experiment makes it BRIDGE; otherwise it is not a citation node through this rule. A BRIDGE paper receives backward and forward citation expansion only when it has been encountered on an eligible depth-0 lineage, and it may create at most one consecutive non-CORE bridge generation (`K = 1`). A BRIDGE child reached at depth 1 is retained and screened but cannot continue that bridge lineage. A CORE child resets bridge depth to 0 and resumes ordinary CORE recursion. A later independent depth-0 encounter of a bridge paper enables its one expansion even if its first encounter was at depth 1; completed identical paper/source/window retrievals are reused while every encounter retains provenance. Thus discovery order cannot permanently suppress an otherwise eligible one-hop expansion.

Bridge traversal changes discovery only. It does not create a comparison, alter A/E/F or any outcome/statistical/Meyen/evidence-bundle rule, promote `F-not-meaningful`, or independently activate QDYN. A bridge-discovered Y activates QDYN only if it separately meets §9.4. Bridge citation retrieval inherits the same registered source/fallback policy as ordinary citation expansion and uses the same immutable window identity, ordered-result hash, durable encounter, and resume-reuse rules; no bridge-specific source is fixed here. Bridge obligations are part of the citation frontier. Every eligible required expansion must finish before principal citation saturation or run completion; temporary resource limits require pause/checkpoint, not a paper/API/title budget, post hoc parent quota, or zero-yield stopping rule. Newly obtained text or append-first revision of node status deterministically reopens any newly enabled frontier.

Stop citation expansion when a complete backward-and-forward citation wave yields zero new potentially relevant papers after deduplication and title/abstract screening.

Scientific eligibility and discovery usefulness are distinct. A weak study may remain a useful citation-network node.

### 9.2 Review and discovery anchors

Use a frozen broad set of review, theory, method, and other discovery-anchor papers to index partially disconnected areas, spanning at least unconscious processing, functions of consciousness, theory criteria, attention and control, metacognition, theory landscapes, and visual consciousness. These anchors are discovery sources, not automatically X → Y experiments. Screen cited empirical work through the normal funnel.

The frozen `seed_scope.basis` in `config.yaml` declares either `manuscript-bibliography` or `author-vetted-primary-support`. For `manuscript-bibliography`, every reference in the user-designated current manuscript is an initial seed, represented once across the empirical-seed and review/discovery-anchor files after bibliographic deduplication. Empirical candidate papers enter the candidate lot; other references, including books, theoretical, methodological, and computational works, enter as fixed discovery anchors. For `author-vetted-primary-support`, the empirical seeds are the identities explicitly accepted by the author before freeze; freeze their identity manifest and neutral selection provenance, without distributing expected A/E/F or outcome judgments. The separate broad review/discovery anchors remain frozen and receive their ordinary treatment under either basis. Seed role conveys no expected scientific classification. Being a fixed anchor does not permit newly discovered nonempirical works to become recursive CORE or BRIDGE nodes.

### 9.3 Independent query search

The principal recall instrument is the combination of empirical-seed backward/forward citation expansion, review/discovery anchors, and activated process-triggered expansion. Before the registered run, freeze compact source-specific independent query families only as a supplementary blind-spot and recall check. This lane does not claim complete enumeration and does not replace the principal routes. Nevertheless, every record returned inside each frozen window is screened and audited under the normal provenance rules.

The prepared supplementary instrument contains fourteen families: attention/control, metacognition, binding/perceptual organization, memory, action/rule use, affect, bodily/interoceptive uses, social uses, learning, language, pain/unpleasantness, pleasure/liking, motivation/reward, and a function-agnostic awareness window. These are coverage checks, not an exhaustive ontology or an eligibility whitelist. Use both sources, one ranked window of at most 40 records per source/family (28 windows, at most 1,120 encounters), screen every return, request no second page/cursor and never redistribute quota. The lane remains mandatory after provisional satisfaction of the principal frontiers. The QREV6 strings are prospectively specified and locally syntax-checked; their exact live retrieval quality remains to be assessed in a separately identified diagnostic.

Historical QCAL4/QCAL5 windows are not silently reused as QREV6 snapshots. Record total service hits, returned records and ranked-window truncation separately from source exhaustion. A full top-N window never establishes saturation. Any later widening or partitioning requires a prospectively commissioned new package/window specification, after examining source yield, coverage gaps and resources; never change a frozen window mid-run. No domain's scientific eligibility depends on these query families.

Every frozen source-specific query block must state its sort/ranking, page size, whether every returned record is screened, and—if not exhaustive—the exact preregistered record/page maximum. It must also specify behavior for ties, source reordering, cursor failure/API truncation, and deduplication across blocks. A registered instruction to merely “run the query” is insufficient. Pre-freeze calibration may use explicitly labeled draft bounds to determine whether exhaustive screening is feasible; those bounds do not become registered defaults by convenience.

### 9.3.1 Citation-source coverage calibration before freeze

Before fixing the citation-source rule, compare the OpenAlex graph alone with the union of OpenAlex and Europe PMC wherever Europe PMC supplies usable references/citations. Record overlap, source-unique references/citations, and source-unique records surviving title screening. Crossref may be tested as a publisher-deposited backward-reference fallback. Citation counts from different services remain non-interchangeable.

The selected policy is OpenAlex primary for broad discovery/identity/citations; Europe PMC parallel for required query windows and a covered-parent citation fallback; Crossref for DOI identity and backward references; and the identified article/repository reference list as the last backward fallback. No OpenAlex/Europe PMC citation union is required at every node. Follow the explicit direction-specific fallback, pagination, snapshot, and retry rules in `queries.md`. An unavailable citation direction remains incomplete, not a zero-yield result. Revisit coverage calibration only if a new coverage problem appears.

### 9.4 Process-triggered expansion

A newly encountered Y earns a targeted search when a comparable awareness contrast independently has strong A/E/F, or when a fully evaluated unaware capacity has strong exact-X A in its explicitly selected unaware regime(s), meaningful F, positive whole-Y evidence and interpretable adequate/nonfatally qualified statistics. E does not gate the latter. Population relevance and functional identity must be explicit. No search is earned merely by bridge status, an unclear capacity or an effect label.

Search only the observed Y; do not automatically expand to semantic neighbours. Log every dynamic query verbatim. Both `screen-in` and `screen-uncertain` receive full-text attempts in this lane too.

Lexical expansion is controlled and auditable. A rendered dynamic query may contain only: (1) the canonical Y label; (2) morphology, grammatical reorderings, spelling, or hyphenation variants of that label; and (3) terminology explicitly used for the same Y by the qualifying source paper; and (4) documented same-function terminology from another identified source, with a rationale demonstrating identity rather than a neighbouring function (`documented-same-function`). Every term must be logged with one of those provenance categories, its source or derivation, and a rationale. No immediate-parent vocabulary is registered for this version; omit that optional input instead of inventing a parent identifier or an additional taxonomy. Unrestricted language-model synonyms, neighboring functions, and unlogged semantic expansions are prohibited. Any independently qualifying mental function can activate this route, including functions outside the supplementary blind-query families.

A genuinely new Y found in this lane may trigger another Y-specific search only if it independently satisfies the same activation conditions. Each normalized Y label may activate this route once per run; label normalization decisions and reasons must be logged.

Use both OpenAlex and Europe PMC for each activated Y, one bounded ranked window of at most 50 records per source, no second page/cursor, and no quota reallocation. A same-Y rediscovery never retriggers the route.

## 10. Calibration, freeze, and registration

Release authorization is determined by `RELEASE_READINESS.json` and requires named acceptance evidence bound to the operative inputs. Freezing these authorities alone does not authorize launch. For future revisions, lock the scientific authorities and case-selection rules before independent validation readings. An explicit registered launch remains a separate action. For every new revision:

1. Freeze the declared seed basis and exact seed identities. `manuscript-bibliography` includes the complete current manuscript bibliography; `author-vetted-primary-support` includes the author's explicitly accepted primary/support identities for the commissioned targeted scope. Record the source of authorization and the identity-manifest hash in frozen configuration. Recommendations or model classifications alone never count as author acceptance. Changing basis or identities requires a new pre-freeze revision; it cannot modify or reopen an existing frozen run under changed inputs. Starting from new seeds does not establish comprehensive depth-3 coverage of an earlier graph: keep seed-relative wave/distance separate from any proven original-graph depth.
2. Incorporate any further user-supplied papers, reviews, or researcher feedback before freeze; external solicitation is optional and is not authorized by this protocol.
3. Pilot A/E/F coding on known examples.
4. Resolve protocol ambiguities.
5. The protocol, empirical seeds, review and discovery anchors, exact queries, search sources and fallbacks, explicit publication-date policy, missing-text batch size, schemas, execution utilities, and stopping rules are frozen together. Starting a run remains a separate explicit action.

Prepare source-located development packets for the manuscript's **primary and supportive** empirical examples. Record exact X and conservative Y, awareness evidence for each relevant regime, first-order evidence, the same-Y/E account, direct result and statistics, limitation, and manuscript role. A conflict between article evidence and the rule is unresolved; do not force a code to match the manuscript. Keep named expected outcomes outside registered reviewer instructions. Before release readiness, validate the whole routing stack on development controls, a separately frozen near-neighbor set, and withheld positive, borderline, negative, and residual-capacity works. Report gate-level and paper-level retention, false-primary burden, and source-backed disagreements. Lock the instrument and case-selection rules before withheld identities are revealed to the independent assessors and reference readers. Disclose prior coordinator identity or routing exposure in the separate validation audit; source-and-judgment withholding does not establish identity-clean discovery validation. A small zero-miss panel is a regression gate, not a claim of exhaustive recall.

During a registered run, agents are not told what classifications seeds are expected to receive. Criteria are not modified. Unforeseen cases are recorded rather than resolved by inventing rules.

Query calibration tests vocabulary and retrieval behavior; recovery alone is not scientific inclusion. Never embed sentinel title/DOI answers in query strings or treat metadata inspection as A/E/F classification. Report exact-query coverage and untested applicability honestly; calibration supplies no exhaustive-recall claim or automatic numeric recovery threshold.

## 11. Independent multi-agent execution and adjudication

Each agent receives the same frozen scientific package. Independent runs must not inspect one another.

After all runs:

1. Union discovered papers and deduplicate them.
2. Retain which agent found each paper.
3. Compare comparison-level classifications.
4. Manually adjudicate disagreements and uncertain cases against the frozen protocol and source experiment/comparison.

Do not adjudicate by majority vote. Record the final decision, reason, and source location. Adjudication may resolve a case but cannot alter the frozen protocol. Cases genuinely unresolved under the protocol remain unresolved.

After adjudication, summarize the functional profile in a concise source-linked table and explanatory prose: the conservative function, supporting comparison IDs, result type, principal limitation, and whether support is confined to one study, patient, or paradigm. Several comparisons from one experiment are not independent replications. Preserve these dependencies and scope limits without requiring a new synthesis schema, numerical evidence score, or process-theory commitment.

## 12. Audit trail and derived outputs

The master record contains every encountered paper, including exclusions. Every decision includes a brief why.

- CSV master tables hold current state.
- JSONL holds the append-only, complete decision history.
- `discoveries.csv` holds one row for every paper result encountered through every logged search or citation event, including rediscoveries.
- `experiment_groups.csv` holds one row for every enumerated physical experiment, including support-only and no-qualifying-comparison groups.
- Each `experiments_master.csv` row is one paper × experiment × X→Y comparison, identified by `comparison_id`.
- Clean qualifying files are deterministic comparison-level views of master records, never independently classified datasets.

Operational paths, event-to-file mappings, identifiers, validation checkpoints, and completion requirements are defined in `AGENTS.md`.

The main profile contains findings from comparable human awareness contrasts. Awareness-linked difference and positive invariance claims require strong A/E/F and a directly tested same-Y contrast. Positive unaware capacity within a verified comparable awareness design requires comparison-wide strong A and meaningful F, plus its separately supported regime-local unawareness and its own positive capacity statistics, without an E gate; weak E leaves the awareness-effect claim unresolved. Capacity-only studies lacking an awareness contrast stay supplementary. `constraint_ready_experiments.csv` is this main set; the route-specific views preserve their own scope, and `supplementary_evidence.csv` keeps relevant completed evidence outside the main set visible. Descriptive no-difference is not automatically a positive constraint; state its uncertainty. `bayesian_null_supported.csv` is distinct from region-based equivalence. Every fully evaluated comparison carries `evidence_strength_reason`.

The normal source assessment supplies the same records for the source-linked **prospect queue**; do not reconstruct a second scientific table. The default `profile-prospect` is a reading recommendation for human vetting, not an accepted primary/support finding. Its argument identifies X, a conservative plausible Y, the measured outcome, decisive source evidence, a scoped contribution, the remaining alternative or limitation, and a specific question for the author. Assess that argument holistically before adding `tentative_role = primary|support|undetermined`; the annotation is not a scientific gate.

Each prospect references an existing comparison and verified source. `prospect_relation = comparison-located` identifies located arms or regimes in which awareness of the same X is related to the same Y. It does not assert that the difference was statistically tested or that awareness was perfectly validated. `comparison-unresolved` identifies a source-grounded plausible relation whose precise awareness, functional or analysis scope remains the stated `human_question`. `decisive_evidence` describes the actual design/result and its source location, not the desired conclusion. Unknown or unresolved detail is not an established absence. An absent direct difference test alone does not exclude a prospect when the same-function awareness arms are located; withhold difference/equivalence claims and identify the missing test. Known absence of an awareness comparison, known nonfunctional Y, or an incompatible X→Y relation belongs in context rather than the prospect queue. A conscious condition elsewhere, separate significance labels or a later discrimination subgroup cannot manufacture the focal comparison.

Uncertain awareness transfer, weak signal control, ambiguous but plausible function, incomplete critical analysis or source uncertainty can remain in the prospect queue with the concrete question and honest claim scope. Merely saying “needs more research” is insufficient. Positive unaware-only use remains scientifically visible and can earn its ordinary searches, but is context for this requested awareness–use evidence queue. No prospect label changes scientific codes, derived membership, discovery eligibility or stopping rules. Native record validation still applies; independent promotion checks remain required whenever the underlying scientific record makes a strong claim. An unfinished prospect does not require a confirmed scientific promotion or exact primary/support claim review merely to be recommended.

The optional certified primary/support paths below retain their stronger requirements for an actual same-function awareness comparison. Use them only when making those stronger recommendations; they are not required before delivering prospects.

A functional test across objective-discrimination groups is a real test of the relation to discrimination performance. It is an awareness comparison for this evidence queue only when source evidence also justifies interpreting the grouped dimension as different awareness regimes of the focal X. Above-chance objective performance does not by itself establish the higher-awareness group, and a selected group's nonsignificant departure from chance does not by itself establish unawareness. When the group-awareness premise is unestablished, preserve the actual functional result as a source-grounded unresolved prospect if an awareness interpretation is plausible and the specific question is stated; otherwise retain it as context. Do not describe it as verified awareness support. This differs from a source-grounded awareness comparison whose measurement transfer or signal control is uncertain: such a comparison can retain qualified support at its justified scope. No strong-A or E requirement is added to every support finding, and scientific capacity, discovery and export rules remain unchanged.

Each handoff item states `claim_basis`: `awareness-linked-change`, `preserved-capacity`, `qualified-awareness-support`, `context`, or `unresolved-source`. Its `claim_comparison_id` identifies the existing comparison whose source analysis supports the claim, and `measured_outcome` names the readout separately from X and Y. These are editorial references to existing scientific records, not new scientific classifications. The shared handoff policy applies these optional stronger recommendation meanings:

- A **qualified primary prospect** for awareness-linked change requires the existing strong awareness-constraint route and actual critical same-Y test.
- A **qualified primary prospect** for preserved capacity requires supported exact-X whole-Y unaware functioning and an actual same-Y awareness nondifference/null test. A descriptive branch may combine comparison-wide strong A/F and supported whole-Y capacity with an interpretable adequate or nonfatally qualified `no-detectable-difference` result even when E is weak. Label it descriptive nondifference with the signal limitation; do not call it positive equivalence or established invariance. Strong equivalence or Bayesian-null claims retain their existing route requirements, including E. No E gate is added to scientific unaware capacity or its search activation.
- **Valuable support** contributes a bounded empirical awareness–function premise through an actual comparable same-function test with an interpretable direct result and adequate or nonfatally qualified statistics. A clear function and located awareness comparison can remain qualified support with weak E or materially uncertain awareness transfer; state that limit. An uninterpretable result or unresolved critical statistics belongs in a specific conditional question rather than this evidence tier. General cognitive relevance, a nonzero effect, methods usefulness, or an unaware-only result does not supply this evidence role. This reading-tier requirement does not alter scientific export predicates.
- **Conditional check/read** identifies a specific unresolved question about function, awareness scope, a critical analysis, or a source. It is an optional check pool, not an accepted evidence claim or automatic immediate reading obligation. **Backup/context** preserves useful narrower findings and methods. An **unresolved source request** uses the existing missing-text obligation.

For both default prospects and optional certified recommendations, source versions, comparison decisions and existing review reasons support these judgments; a missing or contradicted core premise cannot be filled by the tier label. Editorial rank cannot change A/E/F, statistics, Meyen, derived scientific membership, discovery or stopping rules. The coordinator must author and update the default prospect queue at each validated checkpoint, retaining prior entries or recording their reasoned disposition against current evidence and explicit human decisions. Deliver provisional prospect guides while discovery remains open; a final guide still requires completed input runs and the unchanged stopping rules. The pipeline completes and delivers recommendations independently. Human acceptance remains pending until the user's own reading and explicit primary/support decision; it is not a scientific completion condition. A later depth-3 or new-model sweep requires a separate launch; neither a recommendation nor a newly vetted paper starts one automatically.

When an error is found, identify whether it concerns source intake or interpretation, claim scope, lost/current state, or an actual ambiguity in the scientific rule. Correct the evidence, claim or state under the existing rule when possible. Disagreement over tentative primary/support placement alone does not justify another rule revision; genuine policy ambiguity remains explicitly unresolved and cannot change frozen inputs during a run.
