# Consciousness X → Y Literature Sweep Protocol

**Version:** draft-0.8.6
**Registration status:** pre-freeze; not preregistered

This file is the scientific and procedural source of truth for the sweep. It is written for human and AI screeners. `AGENTS.md` governs execution mechanics. Neither file may change during a registered run.

## 1. Aim and scope

The sweep asks:

> For a particular entity or content X and cognitive process Y, does awareness of X change whether, or how well, Y can use X?

The search is result-neutral. A useful experiment may show that Y operates while X is unaware, that awareness changes Y, that no awareness-linked difference was detected, that equivalence is positively supported, or that one or both questions remain unresolved. A study is not a hit because awareness helps; it is useful because its design can inform the X → Y question.

The atomic scientific unit is a **paper × experiment × X→Y comparison**, not a paper or experiment as a whole. The physical experiment group is nevertheless a first-class representation unit: enumerate every physical experiment before atomization, including support-only experiments and experiments yielding no qualifying comparison. Such groups receive no placeholder comparison. One experiment may contain multiple comparison records. Y may be a scalar function or a coherent factorial functional relation. Multiple component simple effects may remain in one comparison when they jointly operationalize the same conservative functional mapping and the critical inference is an interaction or structured pattern over them. Genuinely different downstream functions receive separate comparisons. Assign A and F for each comparison from the methods/design. Assess design-based E next; when evidence is not matched, inspect the result pattern only for the frozen `E-diagnostic` test and then finalize E. Classify unaware capacity and the effect of awareness independently after A, F, and final E are established.

## 2. Design classification

### 2.1 A — awareness of X

Code awareness independently of E and F.

Unawareness of X may be supported by subjective awareness evidence, sufficiently informative objective invisibility evidence, or both. Record the orthogonal `awareness_evidence_type` as `subjective`, `objective-invisibility`, `mixed`, or `none`.

A described awareness procedure is not itself an awareness result. Record critical-result availability in `awareness_result_reporting` and its evidential bearing in the separate `awareness_result_support` field. A focal reported result supports strong A only when reporting is `reported`, support is `supports-strong-A`, the actual procedure/test type matches, the result bears on the focal X/regime, and an exact source location is present. A Methods-only statement that participants completed a test is `not-reported` for the critical result and cannot support strong A. `A-direct` always requires this focal result. `A-validated` requires it unless a separate complete premise-specific transferred-`awareness-A` bundle supplies the critical result and explicit transfer assessment; do not copy a result from another experiment into the focal result fields.

- `A-direct`: qualifying subjective or objective-invisibility evidence is obtained in the relevant experiment, trial, block, condition, or stimulus regime. Subjective examples include seen/unseen judgments, graded visibility, and PAS-like ratings; the response need not be verbal.
- `A-validated`: qualifying subjective or objective-invisibility evidence is obtained in a separate validation procedure whose conditions plausibly transfer to the main experiment. Assess transfer using at least stimulus parameters, masking or suppression, timing, attentional allocation, task demands, and participant population. A validation regime must not plausibly make awareness lower than in the main experiment while being used to establish unawareness there.
- `A-transfer-risk`: a separate subjective or objective-invisibility validation exists, but its sensitivity or transfer to the main experiment is materially uncertain.
- `A-absent`: no qualifying subjective or objective-invisibility evidence supports the awareness classification. Masking, stimulus condition, neural activity, or an insensitive visibility test alone does not qualify.

When strong A uses a result from another block, experiment, supplement, or external source, `A-validated` requires a complete premise-specific `awareness-A` evidence bundle. Every required result-bearing member must identify the supporting experiment/source, critical result, exact location, transfer reason, transfer limitations, relevant regime differences, and decision use. A procedure-only member cannot complete the bundle. A result from a similar stimulus or another participant sample is never inherited automatically; sample, stimulus, suppression, timing, attention, task, environment, awareness procedure, and first-order-evidence regime remain explicit transfer dimensions. If the critical result is unavailable, the required member is unavailable and the bundle remains incomplete unless a distinct, explicitly justified transferable result independently supports A.

Objective invisibility evidence may support `A-direct` or `A-validated` only when all of the following are true:

1. the task directly tests perceptual access to the relevant X;
2. it has a meaningful objective chance or no-access baseline;
3. the design and amount of evidence are sufficiently sensitive for the invisibility inference being made; and
4. the observed result supports performance being at or sufficiently near that baseline.

Do not impose a universal modern equivalence-test or Bayes-factor requirement on legacy awareness-validation studies. However, a merely nonsignificant comparison against chance from an obviously underpowered or insensitive test is not sufficient. Every `A-direct` or `A-validated` classification using objective invisibility must record why the visibility test is sufficiently informative in `objective_visibility_test_reason` and set `objective_visibility_test_informative = yes`.

The relationship between A and E is asymmetric. Above-chance objective detection or discrimination does not by itself imply awareness and does not invalidate an independent subjective-unawareness classification; it primarily informs first-order evidence E. Conversely, sufficiently informative chance-level or no-access performance on an appropriate objective visibility task can support unawareness for A. Objective performance is therefore not a universally theory-neutral awareness measure, but neither is it categorically excluded from A.

### 2.2 E — first-order evidence about X

Physical identity of X does not guarantee matched internal evidence.

- `E-matched`: aware and unaware conditions are matched on the relevant direct first-order measure of X. This requires either (1) active matching or titration by experimental design on that measure, or (2) a successful explicit equivalence procedure using a stated equivalence margin. A merely nonsignificant aware/unaware comparison (`p > .05`) does not establish matching. An apparently narrow confidence interval without a predefined or explicitly stated equivalence criterion also does not establish matching.
- `E-diagnostic`: first-order evidence is not matched, but the structured result pattern rules out the relevant simple scalar explanation in which more first-order evidence about X merely strengthens the same downstream functional relation Y. Valid structures include threshold-linked nonmonotonicity, an experimentally shifted threshold accompanied by a shifted downstream effect, crossover/sign reversal, and a coherent factorial/process-selective interaction that changes the mapping from X/task relation to Y. It is not enough that unrelated Y1 and Y2 have different effects.
- `E-physical-only`: the physical stimulus or event is nominally matched, but direct first-order evidence is unequal or inadequately assessed.
- `E-uncontrolled`: outside the nominally identical-physical-X case, first-order evidence differs or is inadequately controlled or known, so a simple first-order-evidence account of Y remains viable.

`E-matched` and `E-diagnostic` are alternative strong routes, not rank-ordered tiers.

### 2.3 E assessment sequence and outcome neutrality

First assess E from the methods. Assign `E-matched` only when its positive matching requirements are met. Otherwise record the provisional non-diagnostic status—`E-physical-only` when physical X is nominally identical, and `E-uncontrolled` otherwise. Then inspect the full result pattern specifically to decide whether the frozen `E-diagnostic` criterion is satisfied. If it is, finalize E as `E-diagnostic`; if not, retain the provisional status.

This limited use of results does not make study selection depend on whether a result is theoretically attractive. The `E-diagnostic` criterion is frozen in advance, is applied to every eligible unmatched case, and is evaluated before unaware-capacity or awareness-effect classification.

Every `E-diagnostic` decision must record all of:

1. the competing simple evidence-strength account;
2. that account's prediction for the same focal Y;
3. the observed pattern that violates the prediction;
4. every experiment or analysis required for the inference, through source pointers and evidence links; and
5. why the evidence concerns one coherent focal Y rather than an opportunistic cross-Y dissociation.

Before assigning `E-diagnostic`, also perform a bounded **contrast-integrity** check. Ask whether the awareness/evidence contrast systematically differs in a separate task-state variable that can independently change the focal Y: instruction, learned contingency, explicit task-relation knowledge, response mapping, policy, attentional/control set, task relevance, feedback/training, or block-specific strategy. Sensory strength, masking, and unequal internal evidence are the ordinary first-order-E problem and do not by themselves fail contrast integrity.

Audit only alternatives that are finite, explicitly named, independently motivated by the design or task, capable of changing the same focal Y, and associated with an observable prediction or control. A classification-gating alternative must also have an independent evidential or design anchor: a design-imposed difference, a directly measured difference, reported behavioral evidence, an explicit manipulation check/control, or comparably direct design-based evidence. A merely possible unmeasured endogenous covariate—such as attention, arousal, motivation, stronger-evidence process engagement, or executive control—may be recorded as a limitation but cannot veto `E-diagnostic` without such an anchor. A hidden process invented after seeing the result is inadmissible. Conversely, an anchored difference in learned contingency, policy, instruction, mapping, or another task state remains classification-critical even when Y reverses sign.

For every admissible task-state alternative, the E-diagnostic bundle must record the variable, why it is viable, its prediction, the required direct control member, and whether it is `ruled-out` or `unresolved`. Use a separate E-diagnostic bundle for each admissible alternative when more than one exists. If any viable alternative remains unresolved, `E-diagnostic` is prohibited and the applicable weaker E category is retained. When the task instructions, response mapping, contingency knowledge, policy, and physical task configuration are held fixed and no separate design-motivated task state is identified, record `not-applicable`; unequal trialwise sensory evidence alone does not block the ordinary E-diagnostic test.

Before finalizing any unmatched case as `E-diagnostic`, `E-physical-only`, or `E-uncontrolled`, perform and record a bounded semantic scan of the entire supplied article record for another experiment, analysis, supplement, or explicit control designed to test the focal first-order-evidence alternative. Record `alternative_control_scan_status` and a reason. A candidate is not automatically accepted: establish that it addresses the same conservative focal Y/factorial mapping, assess cross-experiment transfer, name the alternative, and classify its role as required, strengthening, robustness, or irrelevant. Classification-critical support requires an explicit E bundle/link. If an apparently classification-critical within-paper control is unavailable or unevaluated, keep its bundle/dependency incomplete and do not finalize E. A control concerning a different downstream function cannot repair focal E.

For a factorial-functional comparison, apply `E-diagnostic` to the **whole focal functional relation**, not opportunistically to one component. Component simple effects may differ in strength while their joint structured mapping rules out the specified same-Y scalar account. When required support spans experiments, analyses, or sources, a strict evidence bundle must identify the member that addresses the first-order-evidence alternative. An interaction or cross-Y dissociation alone is never sufficient: the same-Y/coherent-functional-relation requirement and every ordinary `E-diagnostic` requirement above remain mandatory.

For example, Experiment A may find a downstream extremum around a detectability threshold, while Experiment B experimentally shifts detectability and the downstream extremum shifts correspondingly. If the complete, premise-specific evidence bundle shows that this joint same-Y pattern violates the stated simple signal-strength prediction, it may support `E-diagnostic`; the extremum alone does not. Charles et al. (2013) motivate the distinction between identical physical stimuli and identical internal evidence.

### 2.4 F — meaningful downstream use Y

F is primarily an eligibility gate, not an ordinal score.

- `F-meaningful`: the dependent measure identifies a defensible distinct downstream functional relation or use of X at an appropriately conservative level, such as regulation/control of distractor interference, metacognitive evaluation, updating, binding, maintenance or memory, action selection, rule-guided use, or adaptive use. The exact cognitive or neural mechanism implementing that function need not be identified.
- `F-ambiguous`: the dependent measure plausibly reflects downstream use or transformation beyond direct registration or report, but even a conservative function-level Y cannot be assigned without choosing among substantively different downstream uses.
- `F-not-meaningful`: the dependent variable establishes only direct detection or discrimination of X, generic registration, a generic neural response, or generic priming whose principal implication is merely that some information about X survived.

Assign Y at the most specific functional level justified by the dependent measure. Do not make Y artificially fine-grained, and do not require the experiment to identify the mechanism implementing Y in order for Y to be meaningful. For example, a behavioral measure may justify `Y = regulation/control of the behavioral influence of a task-irrelevant distractor` while leaving active spatial suppression, inhibitory control in LPFC, attentional filtering, altered capture, and other implementations unresolved. That is `F-meaningful` with ambiguous mechanism, not `F-ambiguous`.

For every comparison, record `Y_label`, `Y_description`, `Y_evidence_role`, and `Y_interpretation_clarity` separately from `mechanistic_interpretation` and `mechanism_clarity`. `mechanism_clarity` is never part of the F gate. Neural evidence may support a proposed mechanism for a behavioral Y, but a generic neural difference is not itself a qualifying Y merely because it is compatible with that mechanism. `F-ambiguous` supports discovery recall but does not pass the strongest empirical-lot filter, which continues to require `F-meaningful`.

Also record `Y_functional_status` and a semantic reason. `F-meaningful` requires Y to be an audited `downstream-function` or `coherent-functional-mapping`; `F-ambiguous` uses `function-unclear`; an observed modulation, interference score, priming effect, or other effect label without a defensible downstream function is `effect-only` and cannot become `F-meaningful` merely because it is nonzero. Evidence that X causes an effect on Y is not automatically evidence that the effect itself is a capacity. This is a semantic audit, not a lexical rule: use the operational input→output relation and explain the judgment.

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

For a factorial-functional comparison, do not infer unaware capacity for the focal function merely because one component is nonzero under unawareness. `unaware_capacity = supported` requires positive evidence for the whole focal mapping and `unaware_capacity_evidence_scope = whole-focal-Y`. If a component function is independently meaningful and scientifically useful, instantiate a linked component comparison whose own `Y_label` names that component. Only that component row may assess its capacity, and it must independently satisfy F, positive unaware evidence, route-specific statistics, and applicable Meyen requirements. A component result cannot be coded as a different capacity inside its parent focal row.

The strong unaware-capacity route requires:

1. `A_code` in `{A-direct, A-validated}` for unawareness of X;
2. `F_code = F-meaningful`;
3. a non-empty `unaware_capacity_claim` naming the function positively demonstrated under unawareness;
4. exact identity between `unaware_capacity_claim` and `Y_label`, with `unaware_capacity_evidence_scope = whole-focal-Y`;
5. `unaware_capacity = supported` for that same named function;
6. `unaware_capacity_stats_status = adequate`; and
7. if `Meyen_role = inference-critical`, `Meyen_status = Meyen-satisfied`.

E remains recorded but is not a gate for this route. E addresses whether an aware–unaware difference can be attributed to awareness rather than first-order evidence; it is not logically required to show that Y operates in a validated unaware condition.

### 3.2 Effect of awareness

Use `awareness_effect`:

- `difference-supported`: a directly tested aware–unaware difference or interaction supports a change in Y;
- `no-detectable-difference`: the relevant difference or interaction was directly tested, effect estimates are interpretable, no credible awareness-linked difference was detected, the conclusion is not based on separate significance tests, and robustness/sensitivity limitations are recorded;
- `equivalence-supported`: positive null evidence rules out a scientifically meaningful difference under Section 4.2;
- `unresolved`: the awareness comparison is relevant but does not meet another category; or
- `not-tested`: no aware–unaware comparison relevant to Y was tested.

`no-detectable-difference` does not mean equivalence. A bare, uninformative `p > .05` normally remains `unresolved`.

Record whether a direct aware/unaware difference or interaction on the same focal Y was actually performed in `difference_tested` independently of E. `difference_tested = yes` requires the focal `difference_source_experiment_id`, exact `difference_source_location`, and reported `difference_statistic_or_test`; the source experiment must equal the comparison's own `experiment_id`. A cross-experiment pattern may support E through an explicit bundle but cannot be represented as a direct focal awareness difference. Every direct comparison requires a descriptive result audit. Weak E blocks a constraint-ready awareness interpretation but cannot convert a performed test into `not-tested`.

When a direct difference is statistically supported but A/E/F do not make the strong awareness-effect route viable, record the observed test and statistics but use `awareness_effect = unresolved`. When a direct test detects no credible difference and the descriptive requirements in Section 4.2 are met, `no-detectable-difference` remains available even with weak E. Positive equivalence evidence may likewise be recorded under Section 4.2, but the strongest constraint-ready invariance route still requires strong A, strong E, and meaningful F. Use `not-tested` only when no relevant direct same-Y comparison was tested or reported.

The strong awareness-linked-difference route requires:

1. `A_code` in `{A-direct, A-validated}`;
2. `E_code` in `{E-matched, E-diagnostic}`;
3. `F_code = F-meaningful`;
4. `awareness_effect = difference-supported`;
5. `difference_tested = yes` and `awareness_effect_stats_status = adequate`; and
6. if `Meyen_role = inference-critical`, `Meyen_status = Meyen-satisfied`.

The stronger invariance/equivalence route requires strong A, strong E, `F-meaningful`, `awareness_effect = equivalence-supported`, adequate awareness-effect statistics, adequate positive null evidence, positive Y evidence where the stated invariance claim requires it, and the same inference-critical Meyen gate. Any required positive Y evidence must instantiate the function named in `unaware_capacity_claim`, not a different downstream consequence.

Use one direction label where applicable: `aware>unaware`, `unaware>aware`, `qualitative-change`, `no-detectable-difference`, `equivalent-within-region`, or `other`.

## 4. Statistical audit

Every full-text comparison receives a separate audit with overall status `adequate`, `concern`, or `unclear`.

### 4.1 Critical difference

For every relevant direct same-Y aware/unaware comparison, determine whether the difference or interaction was itself tested and audit its estimate and statistics regardless of E strength. Do not accept “significant in aware + nonsignificant in unaware” as evidence that the two conditions differ. A statistically supported direct contrast with weak E is descriptive evidence that regimes differ, not a constraint-ready awareness effect, and remains `unresolved` on the awareness-effect axis.

### 4.2 No detectable difference and equivalence

`no-detectable-difference` may be assigned without modern equivalence evidence only when the critical interaction/difference was directly tested, the estimates are scientifically interpretable, no credible modulation was detected, and sensitivity/robustness limitations are explicit. Separate within-condition significance tests are insufficient. A bare uninformative nonsignificant result remains `unresolved`.

`equivalence-supported` requires positive null evidence. Assign `null_evidence_adequacy = adequate` only when the study provides at least one of:

1. a successful equivalence test using an explicitly stated or justified equivalence margin;
2. `BF01 >= 3` in favour of the null; or
3. a confidence interval entirely contained within an explicitly stated smallest-effect or equivalence region.

A merely nonsignificant aware/unaware difference or interaction receives `weak` null evidence even when the more modest `no-detectable-difference` category is warranted. Insufficient reporting receives `unclear`. Do not invent an equivalence margin for a legacy study. Retain `null_evidence_strength` to describe the evidence form.

### 4.3 General concerns

Where relevant, flag multiple-comparison problems, inappropriate statistical models, pseudoreplication, materially selective exclusions, critical exploratory or unconfirmed analyses, and other obvious problems. State why each flag matters to the critical inference.

## 5. Meyen diagnostic

Apply this diagnostic when a study reasons that (1) a direct measure of X is at or near chance or nonsignificant, (2) an indirect measure shows an effect, and therefore (3) X was processed unconsciously. Meyen et al. require evidence for an **indirect task advantage**: the indirect measure must be shown to be more sensitive to X than the direct measure on a comparable scale.

Record `Meyen_role` before recording status:

- `inference-critical`: the unconscious-processing claim materially rests on a direct task being at/near chance or nonsignificant plus a positive indirect Y effect, with the indirect effect serving as the evidence that X-information survived, and without an independently adequate protocol-approved basis for the awareness classification. `Meyen-failed` or `Meyen-unassessable` blocks constraint-ready status.
- `supplementary`: residual-information concerns remain relevant, but unawareness is already established through a dedicated, sufficiently informative validation whose adequacy and transfer are independently justified. Relevant support may include participant/regime-specific staircasing, dedicated validation blocks, post-task revalidation, sensitivity controls, and appropriate transfer. Preserve failure or unassessability prominently, but it does not gate an otherwise valid constraint.
- `not-applicable`: the study does not make the direct-chance plus indirect-effect inference described above.

`Meyen_applicable` remains as a consistency field: it is `yes` for `inference-critical` and `supplementary`, and `no` for `not-applicable`. When applicable, use `Meyen-satisfied`, `Meyen-failed`, or `Meyen-unassessable`, and explain why. Do not automatically make objective-invisibility cases supplementary; state what dedicated validation independently establishes awareness status. Passing does not itself prove unconscious processing and does not replace A.

## 6. Screening funnel

Every encountered paper remains in the master audit record. Every decision includes a brief why.

Title and abstract screens are semantic decisions under this protocol. Agents may process records in batches only as context amortization, but each paper receives its own decision, method, reason, and durable write. Batch membership is never evidence. Regex/keyword rejection, embedding thresholds, citation-count thresholds, numerical LLM relevance scores, and hidden lexical heuristics may not independently produce an exclusion. The registered default is agent semantic screening; this draft defines no deterministic scientific exclusion rule.

### 6.1 Title screening

Bias toward recall. Exclude only when irrelevance is clear. Record the decision and reason.

### 6.2 Abstract screening

Use `screen-in`, `screen-uncertain`, or `screen-out`. `screen-in` means the abstract plausibly contains X, an awareness contrast concerning X, and a distinct downstream Y. Unknown A or E details are not grounds for exclusion.

For `screen-in` and `screen-uncertain`, assign full-text priority `high`, `medium`, or `low`, with a reason. For `screen-out`, leave full-text priority `not-assigned`. Never make a final A, E, or F classification from an abstract alone.

Record `abstract_status` separately as `not-sought`, `available`, `unavailable`, or `not-applicable`. Failure to obtain an abstract is not a screen-out decision. A title-retained paper with `abstract_status = unavailable` remains in the audit and receives a reasoned full-text priority from its title, discovery provenance, and available metadata. It may proceed to retrieval when that priority warrants.

## 7. Full-text retrieval and missing texts

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

An incomplete or conflicted bundle cannot silently establish its premise. Conflicting evidence is not averaged into completeness. A separate complete independent route may establish the premise only through its own bundle.

Each `evidence_links.csv` row is one explicit scientific use. `support_role` records what support is provided: awareness validation, first-order-evidence control, E-diagnostic support, alternative-explanation control, replication, statistical support, robustness, generalization, mechanistic support, or other. Orthogonal `dependency_role` records whether it is `required`, `strengthening`, `robustness`, `generalization`, or `mechanistic`. A missing non-required member does not by itself make the premise incomplete. Every link records its member status, exact supported claim, source/experiment/analysis, source location, transfer reason, and transfer limitation.

For cross-experiment/regime evidence, assess the relevant transfer dimensions—stimulus parameters, masking/suppression, timing, attentional allocation, task demands, participant population, awareness measurement, and first-order-evidence regime—without mechanically discussing irrelevant dimensions. Same-paper location never supplies transfer by itself.

Evidence support is not transitive. If Exp. 2 supports Exp. 1 and Exp. 3 supports Exp. 2, Exp. 3 supports Exp. 1 only through a separate explicit link with its own rationale and caveats. Paper-level statements, awareness validations, E-diagnostic arguments, and auxiliary evidence likewise do not automatically propagate across experiments, regimes, Ys, premises, or comparisons.

A supporting experiment does not become a candidate X→Y comparison merely because it supports a focal inference. Give it a comparison row only when it independently answers an X→Y question. Evidence links never substitute for comparison-specific A/E/F/statistical coding.

## 8. Full-text comparison evaluation order and route-aware analysis

First enumerate each physical experiment. Before final comparison decomposition, perform the mandatory pre-atomization functional-structure check in Section 2.5 and record its decision and why. When the check requires a factorial-functional relation, instantiate that focal comparison before any optional scalar/component comparison. Assign separate scalar comparisons only when they independently answer meaningful X→Y questions or when the check justifies genuinely distinct downstream functions. Unaware capacity and awareness effect are separate fields and do not require duplicate comparison rows merely because both inferences apply. Then, for each comparison:

1. Identify X and the aware/unaware contrast.
2. Identify the awareness measure or validation.
3. Identify the direct first-order evidence measure.
4. Identify Y at the most specific conservative functional level justified by the dependent measure; carry forward the recorded pre-atomization decision, assign scalar versus factorial-functional structure, record component simple effects and any linked optional scalar comparisons, and record finer mechanistic interpretation separately.
5. Check the article and supplement for classification-critical dependencies or supporting analyses. Resolve external auxiliary sources where reasonably possible, create one scientific bundle per focal premise, and create an explicit link for every scientific use.
6. Assign A from the qualifying awareness evidence, record `awareness_evidence_type`, and explain objective-test informativeness where applicable.
7. Assign F from the downstream-use design and explain why.
8. Record the Y evidence role and function-level interpretation clarity separately from the proposed mechanism and mechanism clarity; do not use mechanism ambiguity as the F gate.
9. Assess design-based E: assign `E-matched` if its positive requirements are met; otherwise record provisional `E-physical-only` or `E-uncontrolled`.
10. If evidence is not matched, inspect the structured pattern only to test the frozen `E-diagnostic` criterion; record the competing account, its prediction, the violating pattern, same-Y justification, source locations, required evidence links, and the bounded contrast-integrity disposition for every design-motivated task-state alternative.
11. Finalize E and explain why.
12. Record route viability and a reason. The awareness-effect route is viable only with strong A, strong E, and `F-meaningful`. The unaware-capacity route is viable with strong A and `F-meaningful`; **E is not a gate**. A null/equivalence audit is required only when the comparison actually supports that scientific question.
13. Set `unaware_capacity_claim` to the exact focal `Y_label`. When its route is viable, inspect the results enough to determine whether that same focal function is positively demonstrated, record whether the evidence covers the whole focal Y, and record its critical statistics and applicable Meyen audit even when E is weak. A component capacity requires its own linked comparison.
14. Independently record whether a direct same-Y aware/unaware comparison was performed. If so, audit its observed result, estimate, interpretability, and statistics even when the strong awareness-effect route is not viable. Reserve `difference-supported` for the strong route; use `unresolved` for a significant descriptive difference under weak A/E/F. Use `not-tested` only when the direct comparison is absent.
15. When a direct null-oriented comparison yields a candidate no-detectable or equivalence conclusion, record the structured null-evidence basis, `null_evidence_strength`, and `null_evidence_adequacy`; never conflate no-detectable-difference with equivalence. Otherwise record why the null audit is not required.
16. Perform the overall statistical audit and record relevant robustness concerns.
17. Assign the Meyen role and apply the diagnostic when relevant, explicitly stating whether dedicated awareness validation makes it supplementary.
18. Write a one- or two-sentence empirical-constraint statement that keeps the two inference axes distinct.
19. Record page, figure, table, analysis, auxiliary-source, bundle, and evidence-link locations.

## 9. Discovery routes and stopping rules

The registered sweep combines all four routes below.

Execute the principal routes first: empirical seeds, review/discovery anchors, citation waves, full-text evaluation, and every activated process search. After their frontier is provisionally satisfied, execute the mandatory supplementary blind lane. A new citation-eligible node reopens citation expansion; a genuinely new independently qualifying Y reopens/activates its process search. Completion requires every reopened frontier to satisfy the same unchanged stopping rule. This ordering changes no discovery obligation.

### 9.1 Empirical-seed citation graph

Begin with the frozen empirical seeds. A newly discovered full-text empirical paper becomes a backward/forward citation-network node when at least one experiment contains all of:

1. a specific X;
2. a genuine aware/unaware contrast concerning X, or a substantive attempt to establish one; and
3. a distinct plausible downstream Y coded `F-meaningful` or `F-ambiguous`.

For discovery expansion only, a **substantive attempt** at an awareness contrast is a manipulation, grouping, or subjective measurement explicitly intended to distinguish awareness versus unawareness of the relevant X, even if the resulting evidence is too weak to satisfy `A-direct` or `A-validated`. This keeps borderline papers available as discovery nodes; it does not weaken the empirical-lot criteria.

Weak A or E does not prevent expansion. Papers containing only generic registration or priming coded `F-not-meaningful` do not automatically seed recursive expansion. For unavailable full texts, an `ask-text-high` paper may act provisionally as a node only when its abstract explicitly supports the same X + awareness contrast + distinct plausible Y structure. Review and discovery anchors are expanded separately under their own route. Record every expansion decision and why.

### 9.1.1 Strict one-hop empirical bridge

In addition to CORE nodes above, a logical paper is a strict **BRIDGE** node only after adequate full-text evaluation establishes that it is empirical, is not CORE, and contains at least one single physical experiment that is a genuine near-neighbor of the target design and clearly contains **exactly two** of the three CORE ingredients. The remaining ingredient must explicitly fail; an unclear, unknown, or unassessed ingredient does not qualify. The two present ingredients and the failed ingredient must co-occur in that one experiment and may not be assembled across experiments. The record must identify all three ingredient states, the failed ingredient, and a positive scientific rationale for why the experiment is a meaningful near-miss. Reviews, theories, perspectives, commentaries, methods-only works, and generic conceptual papers cannot become dynamically generated BRIDGE nodes. Title or abstract evidence alone cannot establish BRIDGE status, and missing full text is not evidence that an ingredient failed.

Paper status is derived from its physical experiments with CORE precedence: any CORE experiment makes the paper CORE; otherwise any strict bridge experiment makes it BRIDGE; otherwise it is not a citation node through this rule. A BRIDGE paper receives backward and forward citation expansion only when it has been encountered on an eligible depth-0 lineage, and it may create at most one consecutive non-CORE bridge generation (`K = 1`). A BRIDGE child reached at depth 1 is retained and screened but cannot continue that bridge lineage. A CORE child resets bridge depth to 0 and resumes ordinary CORE recursion. A later independent depth-0 encounter of a bridge paper enables its one expansion even if its first encounter was at depth 1; completed identical paper/source/window retrievals are reused while every encounter retains provenance. Thus discovery order cannot permanently suppress an otherwise eligible one-hop expansion.

Bridge traversal changes discovery only. It does not create a comparison, alter A/E/F or any outcome/statistical/Meyen/evidence-bundle rule, promote `F-not-meaningful`, or independently activate QDYN. A bridge-discovered Y activates QDYN only if it separately meets §9.4. Bridge citation retrieval inherits the same registered source/fallback policy as ordinary citation expansion and uses the same immutable window identity, ordered-result hash, durable encounter, and resume-reuse rules; no bridge-specific source is fixed here. Bridge obligations are part of the citation frontier. Every eligible required expansion must finish before principal citation saturation or run completion; temporary resource limits require pause/checkpoint, not a paper/API/title budget, post hoc parent quota, or zero-yield stopping rule. Newly obtained text or append-first revision of node status deterministically reopens any newly enabled frontier.

Stop citation expansion when a complete backward-and-forward citation wave yields zero new potentially relevant papers after deduplication and title/abstract screening.

Scientific eligibility and discovery usefulness are distinct. A weak study may remain a useful citation-network node.

### 9.2 Review and discovery anchors

Use a frozen broad set of review, theory, method, and other discovery-anchor papers to index partially disconnected areas, spanning at least unconscious processing, functions of consciousness, theory criteria, attention and control, metacognition, theory landscapes, and visual consciousness. These anchors are discovery sources, not automatically X → Y experiments. Screen cited empirical work through the normal funnel.

### 9.3 Independent query search

The principal recall instrument is the combination of empirical-seed backward/forward citation expansion, review/discovery anchors, and activated process-triggered expansion. Before the registered run, freeze compact source-specific independent query families only as a supplementary blind-spot and recall check. This lane does not claim complete enumeration and does not replace the principal routes. Nevertheless, every record returned inside each frozen window is screened and audited under the normal provenance rules.

The conservative pre-freeze instrument activates five conceptually motivated families: attention/control/inhibition/distractor control; metacognition/confidence/monitoring/error evaluation; binding/integration/object or event updating; memory operations/maintenance/working memory; and decision/action/rule-guided or flexible use. Use both OpenAlex and Europe PMC, one ranked window of at most 40 records per source/family, screen every return, request no second page/cursor, and never redistribute unused quota. The lane is mandatory and runs only after the principal frontier is provisionally satisfied.

Learning/adaptation remains scientifically eligible and discoverable through seeds, reviews, citations, and independently earned process-trigger searches. CALIB004 diagnosed the current generic QCAL4-LEARN rendering as pathological; it is disabled/retired and not an active v1 instrument. **PRE-FREEZE TODO:** redesign it or explicitly decide that v1 omits a generic LEARN blind-query block. No such omission changes scientific eligibility.

Every frozen source-specific query block must state its sort/ranking, page size, whether every returned record is screened, and—if not exhaustive—the exact preregistered record/page maximum. It must also specify behavior for ties, source reordering, cursor failure/API truncation, and deduplication across blocks. A registered instruction to merely “run the query” is insufficient. Pre-freeze calibration may use explicitly labeled draft bounds to determine whether exhaustive screening is feasible; those bounds do not become registered defaults by convenience.

### 9.3.1 Citation-source coverage calibration before freeze

Before fixing the citation-source rule, compare the OpenAlex graph alone with the union of OpenAlex and Europe PMC wherever Europe PMC supplies usable references/citations. Record overlap, source-unique references/citations, and source-unique records surviving title screening. Crossref may be tested as a publisher-deposited backward-reference fallback. Citation counts from different services remain non-interchangeable.

CALIB002 found no retained Europe-PMC-only citation candidates for the tested nodes. The current calibration conclusion, not yet a registered rule, is OpenAlex primary for broad discovery/identity/citations; Europe PMC parallel for metadata/full text and conditional biomedical citation fallback; Crossref for DOI/bibliographic identity and publisher-deposited backward references; Semantic Scholar optional. Do not require an OpenAlex/Europe PMC citation union at every node, and do not repeat mandatory union calibration unless a new coverage problem appears.

### 9.4 Process-triggered expansion

A newly encountered Y triggers one targeted Y-specific search only when it first appears in a comparison provisionally satisfying all of:

- A is `A-direct` or `A-validated`;
- E is `E-matched` or `E-diagnostic`;
- F is `F-meaningful`.

Search only the observed Y; do not automatically expand to semantic neighbours. Log every dynamic query verbatim. In this lane, only `screen-in` proceeds automatically; `screen-uncertain` remains in the audit unless independently rediscovered or manually promoted later.

Lexical expansion is controlled and auditable. A rendered dynamic query may contain only: (1) the canonical Y label; (2) morphology, grammatical reorderings, spelling, or hyphenation variants of that label; (3) terminology explicitly used for Y by the qualifying source paper; and (4) one frozen immediate-parent functional term. Every term must be logged with one of those provenance categories, its source or derivation, and a rationale. Unrestricted language-model synonyms, neighboring functions, and unlogged semantic expansions are prohibited.

A genuinely new Y found in this lane may trigger another Y-specific search only if it independently satisfies the same activation conditions. Each normalized Y label may activate this route once per run; label normalization decisions and reasons must be logged.

Use both OpenAlex and Europe PMC for each activated Y, one bounded ranked window of at most 50 records per source, no second page/cursor, and no quota reallocation. A same-Y rediscovery never retriggers the route.

## 10. Calibration, freeze, and registration

This repository is currently **draft / pre-freeze**, not preregistered. Before the registered run:

1. Circulate the working paper to consciousness researchers.
2. Collect suggested empirical papers, reviews, and literatures.
3. Pilot A/E/F coding on known examples.
4. Resolve protocol ambiguities.
5. Freeze and version the protocol, empirical seeds, review and discovery anchors, exact queries, search sources and fallbacks, publication cutoff, missing-text batch size, schemas, execution utilities, and stopping rules.

During a registered run, agents are not told what classifications seeds are expected to receive. Criteria are not modified. Unforeseen cases are recorded rather than resolved by inventing rules.

Pre-freeze query sentinels test only whether a draft query instrument has obviously poor recall within its stated calibration window. Sentinel recovery is not scientific inclusion, sentinel titles/DOIs must not be embedded in search strings, and title lookups do not count as query recovery. Do not tell registered agents expected A/E/F/outcome classifications. No final numeric sentinel-recovery threshold is set in this draft.

## 11. Independent multi-agent execution and adjudication

Each agent receives the same frozen scientific package. Independent runs must not inspect one another.

After all runs:

1. Union discovered papers and deduplicate them.
2. Retain which agent found each paper.
3. Compare comparison-level classifications.
4. Manually adjudicate disagreements and uncertain cases against the frozen protocol and source experiment/comparison.

Do not adjudicate by majority vote. Record the final decision, reason, and source location. Adjudication may resolve a case but cannot alter the frozen protocol. Cases genuinely unresolved under the protocol remain unresolved.

## 12. Audit trail and derived outputs

The master record contains every encountered paper, including exclusions. Every decision includes a brief why.

- CSV master tables hold current state.
- JSONL holds the append-only, complete decision history.
- `discoveries.csv` holds one row for every paper result encountered through every logged search or citation event, including rediscoveries.
- `experiment_groups.csv` holds one row for every enumerated physical experiment, including support-only and no-qualifying-comparison groups.
- Each `experiments_master.csv` row is one paper × experiment × X→Y comparison, identified by `comparison_id`.
- Clean qualifying files are deterministic comparison-level views of master records, never independently classified datasets.

Operational paths, event-to-file mappings, identifiers, validation checkpoints, and completion requirements are defined in `AGENTS.md`.
