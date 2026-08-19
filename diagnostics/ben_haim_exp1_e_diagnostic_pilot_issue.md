# Ben-Haim Experiment 1 E-diagnostic pilot issue

## Status and scope

**OPEN diagnostic issue; no E-diagnostic rule change is made in this revision.** This analysis uses only the locally supplied Ben-Haim et al. main article and archived clean-room pilot 001. The official supplement was not supplied, and no outside literature was searched or retrieved.

A single clean Codex run is evidence that an ambiguity or over-permissive application *can* occur. It is not sufficient evidence that every sign reversal requires a protocol rewrite. The factorial-pre-atomization repair is implemented separately because it operationalizes an already intended generic guardrail. The E issue has broader consequences and remains open pending further pilot, Claude, and GLM evidence.

## What the pilot did

The pilot coded human Experiment 1 (`P000001_E01_C01`) as `A-direct / E-diagnostic / F-meaningful`. It defined one factorial-functional Y—adaptive rule-guided use of an incongruent spatial cue—and treated the sign reversal as violating the account that increasing first-order cue evidence merely produces a stronger version of the same downstream response. The E bundle linked the same-experiment crossover: masked cues slowed responses relative to masked baseline, while visible cues facilitated responses relative to visible baseline. The row entered the constraint-ready awareness-linked-difference output.

This is a faithful application of the literal draft-0.8.1 phrase "simple scalar explanation." The question is whether that phrase is scientifically too weak.

## 1. Viability of an evidence-only threshold/process-enablement account

The alternative is genuinely viable enough that Experiment 1 should not be treated as securely E-diagnostic without further separation:

```text
weak cue evidence
  → automatic orienting/default cue-following
  → interference when the target is opposite

sufficiently strong cue evidence
  → acquisition/access to the predictive opposite-location relation
  → engagement of inhibitory or rule-guided control
  → facilitation at the opposite location
```

This is still a first-order-evidence-only family: awareness need not be the operative cause. Evidence strength can cross a threshold that enables a qualitatively different process. A sign reversal therefore rules out only a *single-process monotonic gain* account, not every scientifically plausible evidence-only account.

The article itself makes process acquisition central. It says visible facilitation was expected only if participants recognized that the target appeared opposite the cue, and visible participants unaware of the cue's predictive value were not facilitated (main article pp. 2–5). That observation is compatible with awareness-dependent access, but it is also compatible with evidence-dependent acquisition/access to the predictive relation.

Experiment 5 shows that a small number of visible cued trials can enable learning; Experiment 6 shows that informing participants about flashes changes both reported visibility and rule use even though the 33-ms cue duration is held constant (p. 7). Those controls weaken some particular stories, but they do not isolate awareness from instruction, rule knowledge, attention to the cue, or evidence-dependent access.

## 2. Confounds in the early experiment

| Dimension | Experiment 1 status | Consequence for E |
|---|---|---|
| Cue visibility | Masked cues were reported unseen; supraliminal cues were visible | Awareness differs, as intended, but is not isolated |
| Physical duration/masking | Subliminal cues were 17/33 ms; supraliminal cues were 250 ms, with blockwise presentation | Large physical/evidence regime difference remains |
| First-order evidence | Objective localization was at chance for masked cues; visible cues were consciously accessible | Evidence is explicitly unequal, so E must be diagnostic rather than matched |
| Acquisition/access to predictive relation | Visible facilitation depended on recognizing the opposite-location contingency | Process availability covaries with cue evidence and awareness |
| Explicit rule knowledge | Participants were not simply given one fixed opposite-location instruction in Experiment 1; they had to acquire/recognize predictability, after congruent training | Knowledge/access is a plausible mediator or confound |
| Block/context | Subliminal and supraliminal trials occurred in counterbalanced blocks | Regime/context can support different learned policies |

Source: main article pp. 2–5 and Fig. 1. Full task and analysis detail was placed in an unsupplied supplement (p. 8).

## 3. Does Experiment 1 fail the intended E-diagnostic standard?

**Provisional diagnostic judgment: likely yes, or at minimum unresolved, under the intended robust standard.** It clearly falsifies the narrow claim that more cue evidence only scales the same automatic orienting response. It does not clearly falsify the broader plausible family in which sufficient evidence enables acquisition, access, or execution of a different task-relevant process.

This is not a retrospective claim that every threshold model is admissible. The alternative is design-motivated and finite: it follows directly from the experiment's learning demands, block structure, physical regimes, and dependence on recognizing cue predictability. It is not an arbitrary curve fitted after seeing the sign reversal.

The current protocol nevertheless permits the pilot's code because it asks explicitly about a "simple scalar" account. That mismatch between literal rule and intended causal protection is the possible over-permissiveness.

## 4. Why later within-regime/trialwise comparisons are cleaner

Experiment 7 holds the masked duration at 17 ms, instructs participants from the start to choose opposite the cue if they see it, measures awareness after every trial, and reports below-chance performance for rating-0 trials versus above-chance performance for rating-2/3 trials with a direct awareness-level effect (`χ²(3)=24.8, p<.0001`; main article p. 8, Fig. 4D).

This removes two major early confounds:

- the physical-duration/block contrast; and
- acquisition of the opposite-location rule.

It is therefore potentially cleaner, not automatically decisive. Trialwise subjective awareness still covaries with trialwise sensory evidence. An evidence-dependent access account can say that stronger cue representations enable execution of the already known rule and also produce higher visibility ratings. A final strong-E judgment would benefit from a direct trialwise evidence measure, matching/modeling, or an intervention that dissociates awareness from usable evidence.

## 5. What alternative class should E-diagnostic rule out?

The intended target should be broader than a linear or monotonic gain account but narrower than arbitrary post-hoc models. A defensible class is:

> Plausible first-order-evidence-only accounts, specified from the design and task demands, in which evidence magnitude or quality can continuously scale the same process **or cross a task-relevant threshold that enables acquisition, access, selection, or control of another already motivated process**.

The class should include process-gating alternatives when the design itself supplies a reason for them—learning a contingency, accessing a rule, switching policies, engaging control, or selecting a representation. It should not include unconstrained hidden states invented only after the result, with no independent task rationale or discriminating prediction.

## 6. Is "simple scalar account" too weak?

Yes, potentially. It can be read as only "larger evidence → larger same-direction Y." Crossover, nonmonotonicity, and factorial interactions then pass almost automatically even when unequal evidence plausibly enables a different task process. The phrase protects against monotonic scaling but not evidence-dependent process access.

The weakness is semantic and operational: the current required fields capture one competing account and prediction, but do not say how broadly the competing evidence-only family must be motivated or bounded.

## 7. Avoiding an impossible standard

A strengthened rule should not require ruling out every logically possible threshold/process model. That would make `E-diagnostic` unfalsifiable and unusable. Bound alternatives by three constraints:

1. **Design motivation:** the alternative must arise from known task operations or manipulated dimensions, not merely from the observed curve.
2. **Prospective discrimination:** it must make at least one observable prediction different from the awareness-dependent account.
3. **Finite audit:** the evaluator lists the small set of credible evidence-only alternatives and the result/control that addresses each; arbitrary unmeasured latent processes are not automatically admitted.

Thus, an interaction is not sufficient, but neither is a limitless skeptical model required.

## 8. Discriminating observable evidence

Useful evidence would distinguish awareness-dependent process access from evidence-strength-dependent process access by crossing or conditioning the relevant variables:

- Match or titrate a direct first-order cue measure across aware/unaware trials, then test whether the process difference remains.
- Within one physical cue/mask regime, model Y jointly from objective first-order evidence and trialwise awareness; test whether awareness has a preregistered residual relation with Y.
- Hold rule knowledge constant through prior instruction/training, as Experiment 7 begins to do, and separately measure whether the rule representation is accessible on low- and high-awareness trials.
- Manipulate instruction or contingency knowledge while holding cue evidence fixed; test whether knowledge rather than awareness produces the sign switch.
- Manipulate sensory evidence within each awareness category or awareness within a narrow evidence region, allowing competing threshold predictions to be compared.
- Use an independently motivated intervention expected to alter awareness without altering the direct evidence measure, or vice versa.
- Predefine the evidence-gated process alternative and test a control condition where the proposed additional process is unnecessary or unavailable.

## Candidate generic formulations for a future revision

### Candidate 1 — broaden the named scalar alternative (least restrictive)

> `E-diagnostic` requires the structured same-Y pattern to rule out the design-motivated first-order-evidence account, including ordinary monotonic scaling and any task-obvious evidence threshold that merely enables access to the tested mapping. Arbitrary post-hoc process models need not be excluded.

Implications:

- **Early sign reversal:** downgraded when learning/rule access is an obvious evidence-gated alternative.
- **Late same-regime/trialwise:** often remains potentially diagnostic, especially with fixed instruction, but unequal trialwise evidence must still be addressed.
- **Threshold-shift cases:** can pass when the experimentally shifted threshold and downstream shift contradict the predeclared evidence-only account.
- **Factorial-functional cases:** can pass when the whole same-Y mapping and its bundle address the obvious first-order alternative; interaction alone cannot.

### Candidate 2 — finite design-motivated alternative set (moderately restrictive)

> Before assigning `E-diagnostic`, enumerate the finite set of plausible first-order-evidence-only alternatives motivated by the task—continuous gain, evidence-thresholded acquisition/access, policy selection, and control engagement where applicable. For each, record a distinct prediction and the observed result or required bundle member that defeats it. Do not admit alternatives lacking an independent task rationale or prospective discriminating prediction.

Implications:

- **Early sign reversal:** normally fails without a control that separates awareness from acquiring/accessing the opposite rule.
- **Late same-regime/trialwise:** stronger because physical regime and knowledge can be held constant; still needs evidence-sensitive analysis when the same representation may gate rule execution.
- **Threshold-shift cases:** remain viable if joint experiments were designed to distinguish continuous strength and threshold-gated alternatives.
- **Factorial-functional cases:** require explicit alternative-explanation-control links for the whole relation, as the new bundle clarification now demands.

### Candidate 3 — residual-awareness/intervention requirement (most restrictive)

> In unmatched designs, `E-diagnostic` requires either (a) a preregistered within-regime analysis showing that awareness predicts the focal same-Y mapping after adequate control/matching for direct first-order evidence, or (b) an intervention that differentially changes awareness and the focal mapping without the corresponding change predicted from first-order evidence alone. Structured reversal by itself is insufficient.

Implications:

- **Early sign reversal:** fails.
- **Late same-regime/trialwise:** may pass only with adequate direct evidence measurement/control; subjective strata alone may be insufficient.
- **Threshold-shift cases:** a shifted threshold/dip pattern alone may no longer pass unless paired with residual-evidence or intervention evidence.
- **Factorial-functional cases:** substantially harder to qualify; even coherent interactions require evidence control at the focal mapping level.

## Recommendation

Carry Candidate 1 and Candidate 2 into the next independent source-complete pilot as competing audit instructions. Do not adopt Candidate 3 without evidence that it does not eliminate intended threshold-shift and factorial-functional exemplars. Keep the issue open until independent agents show whether the ambiguity recurs and how each candidate changes late trialwise, threshold-shift, and factorial cases.
