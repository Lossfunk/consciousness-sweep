# Retrospective efficiency audit under draft-0.7.1

**Status:** methodological, pre-freeze, retrospective only  
**Inputs:** durable records from `CALIB_CODEX_001`–`CALIB_CODEX_004` and `diagnostics/anchor_regression_draft_0_7.md`  
**Prohibited operations confirmed:** no literature search, HTTP/API call, new retrieval, registered run, freeze, or scientific/package change was performed.

## Executive conclusion

The largest defensible savings come from execution order and reuse, not from narrowing the evidence instrument. Run principal discovery first, run the supplementary blind-query lane last, deduplicate before semantic screening, reuse paper-level and within-paper evidence decisions, batch model contexts while preserving individual decisions, cache verified texts, and make full-text work route-aware. These changes preserve the current scientific obligations if reopening rules cover both citation expansion and newly activated process searches.

The calibration does **not** support treating Europe PMC topic search as mere enrichment. At the full non-LEARN QCAL4 window it added 42 source-exclusive title-retained works and 13 source-exclusive abstract screen-ins. Nor does it support dropping any retained family: each family contributed a distinct plausible set after cross-family deduplication. The current LEARN rendering remains a separate, already diagnosed pathological instrument and should not be frozen as-is.

My recommendation is the **Conservative** configuration in Section 17. It achieves lossless calibrated query signal and reduces duplicated reasoning through route order, reuse, batching, caching, and route-aware analysis. The Balanced configuration is a credible efficiency frontier but has measured losses. No configuration is implemented here.

## 1. Scope, definitions, and method

All counts below were reconstructed from stored `search_log.csv`, `discoveries.csv`, `papers_master.csv`, `experiments_master.csv`, `missing_texts.csv`, run summaries, and the current six-anchor regression diagnostic. Existing paper-level decisions were reused as recorded; no paper was scientifically rescreened.

- A **raw encounter** is one stored result occurrence.
- A **unique work** is one CALIB004 logical `paper_id` after its recorded deduplication.
- **Plausible** means abstract `screen-in` + `screen-uncertain` + title-retained/abstract-unavailable, except where a table explicitly reports `screen-in + uncertain` only.
- Source-exclusive counts mean a retained or screen-in work encountered from that source but absent from the other source within the same rank cutoff.
- Sentinel recovery is diagnostic only. The six empirical anchors are required to enter through frozen seeds, not through QCAL.
- LEARN's 80-result pathological return set is excluded from the five-family calculations and addressed separately.

The calibration scopes were not replicas of a full registered run. Cross-run bibliographic overlap and workload projections are therefore estimates, not population parameters.

## 2. QCAL4 source × window ablation

The five retained non-LEARN families are ATTN, META, BIND, MEM, and DEC. Each source contributes `5 × N` maximum encounters.

| N/source | Raw | Unique | Duplicates | Title retained | Abstract in | Uncertain | Abstract unavailable | Sentinels |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| 5 OA | 25 | 24 | 1 | 14 | 5 | 3 | 2 | 0 |
| 5 EPMC | 25 | 25 | 0 | 13 | 3 | 6 | 0 | 0 |
| 5 union | 50 | 49 | 1 | 27 | 8 | 9 | 2 | 0 |
| 10 OA | 50 | 49 | 1 | 29 | 12 | 6 | 5 | 0 |
| 10 EPMC | 50 | 47 | 3 | 17 | 5 | 8 | 0 | 0 |
| 10 union | 100 | 96 | 4 | 46 | 17 | 14 | 5 | 0 |
| 15 OA | 75 | 73 | 2 | 39 | 15 | 7 | 9 | 2: Keizer, Lamy |
| 15 EPMC | 75 | 71 | 4 | 24 | 7 | 11 | 0 | 0 |
| 15 union | 150 | 143 | 7 | 62 | 22 | 18 | 9 | 2: Keizer, Lamy |
| 20 OA | 100 | 97 | 3 | 50 | 20 | 7 | 10 | 3: Keizer, Lamy, Tsushima |
| 20 EPMC | 100 | 93 | 7 | 31 | 12 | 11 | 0 | 1: Keizer |
| 20 union | 200 | 187 | 13 | 78 | 30 | 18 | 10 | 3: Keizer, Lamy, Tsushima |
| 25 OA | 125 | 121 | 4 | 58 | 21 | 10 | 14 | 3: Keizer, Lamy, Tsushima |
| 25 EPMC | 125 | 114 | 11 | 38 | 14 | 15 | 0 | 1: Keizer |
| 25 union | 250 | 227 | 23 | 90 | 32 | 23 | 14 | 3: Keizer, Lamy, Tsushima |
| 30 OA | 150 | 146 | 4 | 69 | 23 | 12 | 18 | 3: Keizer, Lamy, Tsushima |
| 30 EPMC | 150 | 133 | 17 | 46 | 16 | 18 | 0 | 1: Keizer |
| 30 union | 300 | 267 | 33 | 106 | 36 | 25 | 18 | 3: Keizer, Lamy, Tsushima |
| 35 OA | 175 | 171 | 4 | 79 | 26 | 12 | 20 | 3: Keizer, Lamy, Tsushima |
| 35 EPMC | 175 | 155 | 20 | 51 | 18 | 19 | 0 | 1: Keizer |
| 35 union | 350 | 307 | 43 | 118 | 39 | 25 | 20 | 3: Keizer, Lamy, Tsushima |
| 40 OA | 200 | 196 | 4 | 89 | 29 | 13 | 21 | 3: Keizer, Lamy, Tsushima |
| 40 EPMC | 200 | 177 | 23 | 60 | 21 | 21 | 0 | 1: Keizer |
| 40 union | 400 | 345 | 55 | 131 | 42 | 27 | 21 | 3: Keizer, Lamy, Tsushima |

### Source-exclusive contribution

The four exclusive columns apply to the OA/EPMC pair and therefore are the same whichever row of a given N is being interpreted.

| N | OA-only retained | EPMC-only retained | OA-only abstract in | EPMC-only abstract in |
|---:|---:|---:|---:|---:|
| 5 | 14 | 13 | 5 | 3 |
| 10 | 29 | 17 | 12 | 5 |
| 15 | 38 | 23 | 15 | 7 |
| 20 | 47 | 28 | 18 | 10 |
| 25 | 52 | 32 | 18 | 11 |
| 30 | 60 | 37 | 20 | 13 |
| 35 | 67 | 39 | 21 | 13 |
| 40 | 71 | 42 | 21 | 13 |

At N=40, Europe PMC contributed 42 title-retained works not encountered by OpenAlex and 13 source-exclusive abstract screen-ins. This is 32.1% of the union's 131 title-retained works and 31.0% of its 42 screen-ins, although those percentages should not be treated as source sensitivities because screening states and ranking pools are correlated. Europe PMC also increased uncertain candidates. Its contribution is therefore materially more than metadata enrichment. **Removing Europe PMC topic querying is scientifically risky on this evidence.** A conditional fallback role is defensible only in a deliberately Minimal configuration that is explicitly understood to sacrifice calibrated blind-spot yield.

OpenAlex remains the stronger single QCAL source: at N=40 it recovered all three QCAL sentinels, 29 screen-ins, and 89 retained titles versus Europe PMC's one sentinel, 21 screen-ins, and 60 retained titles. That does not erase Europe PMC's unique contribution.

### LEARN

LEARN is not silently dropped from a scientific Y universe. Its CALIB004 rendering was already diagnosed as pathological. Retiring that exact query string before freeze is **SAFE as an instrument-quality decision only if the resulting learning/adaptation coverage gap is documented or the family is redesigned**; declaring learning/adaptation scientifically ineligible would be scientifically risky.

## 3. QCAL4 family ablation

Full five-family union at N=40: 400 encounters, 345 unique works, 131 retained titles, 42 screen-ins, 27 uncertain, 21 abstract-unavailable, and three sentinels.

| Removed family | Family unique | Marginal unique after cross-family dedup | Lost title retained | Lost screen-in | Lost uncertain | Lost unavailable | Lost sentinels | Remaining unique / retained / in |
|---|---:|---:|---:|---:|---:|---:|---|---|
| ATTN | 71 | 71 | 38 | 19 | 4 | 5 | Lamy, Tsushima | 274 / 93 / 23 |
| META | 76 | 75 | 22 | 6 | 5 | 2 | none | 270 / 109 / 36 |
| BIND | 59 | 59 | 30 | 8 | 11 | 2 | Keizer | 286 / 101 / 34 |
| MEM | 73 | 73 | 19 | 1 | 4 | 7 | none | 272 / 112 / 41 |
| DEC | 67 | 66 | 22 | 8 | 3 | 5 | none | 279 / 109 / 34 |

Only one logical work crossed retained-family boundaries in these compact top windows. Consequently, dropping a family removes almost its entire calibrated candidate set. ATTN and BIND are plainly high-value. META and DEC add meaningful distinct candidates. MEM has the lowest screen-in yield, but its 12 unique plausible records include four uncertain and seven without an abstract; its low observed confirmation yield is not evidence that those unresolved candidates are irrelevant. Dropping MEM is at best **CONDITIONALLY SAFE** as a blind-lane economy and is not recommended. Dropping ATTN, META, BIND, or DEC is **SCIENTIFICALLY RISKY** on the observed marginal signal.

### Exact unique plausible material lost

For this manifest, “candidate material” means a family-exclusive title-retained work that was `screen-in`, `screen-uncertain`, or could not be abstract-screened. Title-retained works already recorded as `screen-out` are counted in the ablation table but are not candidate material after the durable abstract decision. Their additional counts are ATTN 10, META 9, BIND 9, MEM 7, and DEC 6. The identifiers and titles below are copied from CALIB004.

**ATTN (28)**

- `P000008` — screen-in — Attention capture by eye of origin singletons even without awareness—A hallmark of a bottom-up saliency map in the primary visual cortex
- `P000035` — abstract unavailable — Attention Capture, Orienting, and Awareness
- `P000002` — abstract unavailable — Attentional capture and inattentional blindness
- `P000051` — screen-uncertain — Attentional capture by fearful faces requires consciousness and is modulated by task-relevancy: A dot-probe EEG study.
- `P000030` — abstract unavailable — Complete unconscious control: Using (in)action primes to demonstrate completely unconscious activation of inhibitory control mechanisms
- `P000038` — screen-in — Degraded stimulus visibility and the effects of perceptual load on distractor interference
- `P000006` — screen-in — Dissociable Brain Mechanisms Underlying the Conscious and Unconscious Control of Behavior
- `P000007` — screen-in — Dissociating consciousness from inhibitory control: Evidence for unconsciously triggered response inhibition in the stop-signal task.
- `P000003` — screen-in — Frontal Cortex Mediates Unconsciously Triggered Inhibitory Control
- `P000011` — abstract unavailable — Goal-driven attentional capture by invisible colors: Evidence from event-related potentials
- `P000017` — screen-in — Greater Disruption Due to Failure of Inhibitory Control on an Ambiguous Distractor
- `P000040` — screen-in — Inhibition of subliminally primed responses is mediated by the caudate and thalamus: evidence from functional MRI and Huntington's disease
- `P000063` — screen-in — Neural Correlates of the Attentional Bias Towards Subliminal Pornographic Cues in Individuals with Tendencies Toward Problematic Pornography Use: An ERP Study Using a Dot-Probe Task.
- `P000043` — screen-in — No Selective Attentional Shift despite Prefrontal Activation during a Working-Memory Task with Unconscious Stimuli.
- `P000026` — screen-in — Orienting of attention without awareness is affected by measurement-induced attentional control settings
- `P000005` — screen-uncertain — Statistical regularities modulate attentional capture.
- `P000024` — abstract unavailable — Stimulus-driven attentional capture by subliminal onset cues
- `P000053` — screen-in — Subliminal meaning-contingent attentional orienting: The role of attentional control setting based on displaywide features.
- `P000041` — screen-in — The Impact of Temporal Expectation on Unconscious Inhibitory Processing: A Computational Analysis Using Hierarchical Drift Diffusion Modeling.
- `P000013` — screen-in — The Role of Conscious Perception in Attentional Capture and Object-File Updating
- `P000010` — screen-in — Unconscious Activation of the Prefrontal No-Go Network
- `P000060` — screen-in — Unseen food images capture the attention of hungry viewers: Evidence from event-related potentials.
- `P000001` — screen-in — Value-driven attentional capture
- `P000045` — screen-uncertain — Value-Modulated Attentional Capture Arises Entirely Unconsciously (in Those Who Ultimately Become Aware of the Stimulus-Value Association Responsible For it)
- `P000044` — screen-in — Value-modulated attentional capture depends on awareness.
- `P000068` — screen-in — Value-modulated attentional capture depends on explicit awareness
- `P000055` — screen-in — Value-Modulated Attentional Capture is Found Only in Individuals That Show Awareness of the Repeatedly Presented Stimulus-Value Association and Sustains With Belief in the Association Alone
- `P000027` — screen-uncertain — What You See Is What You Set: Sustained Inattentional Blindness and the Capture of Awareness.

**META (13)**

- `P000096` — abstract unavailable — Alzheimer's disease can spare local metacognition despite global anosognosia: Revisiting the confidence–accuracy relationship in episodic memory
- `P000103` — abstract unavailable — Can a failure in the error-monitoring system explain unawareness of memory deficits in Alzheimer’s disease?
- `P000079` — screen-in — Does subliminal visual perception have an error‐monitoring system?
- `P000112` — screen-uncertain — Early changes in corticospinal excitability for subliminally presented fearful body postures.
- `P000116` — screen-uncertain — Error Awareness Can Occur in the Absence of an Error-Related Negativity.
- `P000089` — screen-in — Error Awareness in a Saccade Countermanding Task
- `P000082` — screen-in — Error-Monitoring and Post-Error Compensations: Dissociation between Perceptual Failures and Motor Errors with and without Awareness
- `P000138` — screen-in — Error-related negativity and error awareness in a Go/No-go task.
- `P000074` — screen-in — Error‐related brain potentials are differentially related to awareness of response errors: Evidence from an antisaccade task
- `P000123` — screen-uncertain — Metacognitive Sensitivity on the Iowa Gambling Task Reveals Awareness as a Necessary Condition for Advantageous Performance.
- `P000104` — screen-in — On the independence of visual awareness and metacognition: A signal detection theoretic analysis.
- `P000145` — screen-uncertain — The role of metacognition in recognition of the content of statistical learning.
- `P000078` — screen-uncertain — Theta-burst transcranial magnetic stimulation to the prefrontal cortex impairs metacognitive visual awareness

**BIND (21)**

- `P000190` — screen-uncertain — Automatic binding of basic sensory features requires consciousness
- `P000206` — screen-uncertain — Change detection on a hunch: pre-attentive vision allows "sensing" of unique feature changes.
- `P000169` — screen-in — Color-motion feature binding occurs unconsciously
- `P000162` — screen-in — Consciousness is not necessary for visual feature binding
- `P000177` — screen-uncertain — ERP evidence for temporal independence of set size and object updating in object substitution masking
- `P000196` — screen-in — Integrating events across levels of consciousness.
- `P000159` — abstract unavailable — Integrating unseen events over time
- `P000199` — screen-in — Moderate sedation induced by general anaesthetics disrupts audio-spatial feature binding with sustained P3 components in healthy humans.
- `P000149` — screen-uncertain — Negative Compatibility or Object Updating? A Cautionary Tale of Mask-Dependent Priming.
- `P000200` — screen-uncertain — Negative congruency effects: a test of the inhibition account.
- `P000172` — screen-uncertain — Object-substitution masking degrades the quality of conscious object representations
- `P000152` — screen-uncertain — On the role of mask structure in subliminal priming
- `P000168` — screen-uncertain — Perceptual asynchrony: Modularity of consciousness or object updating?
- `P000175` — abstract unavailable — Relationship between visual binding, reentry and awareness
- `P000155` — screen-in — Seeing properties of an invisible object: Feature inheritance and shine-through
- `P000165` — screen-in — The Fate of Visible Features of Invisible Elements
- `P000189` — screen-uncertain — The Mechanisms of the Masked Priming That Do Not Work Jointly.
- `P000157` — screen-uncertain — The relationship between feature binding and consciousness: Evidence from asynchronous multi-modal stimuli
- `P000185` — screen-uncertain — Unconscious analyses of visual scenes based on feature conjunctions.
- `P000178` — screen-in — Unconscious Familiarity-based Color–Form Binding: Evidence from Visual Extinction
- `P000163` — screen-in — Unconscious symmetrical inferences: A role of consciousness in event integration

**MEM (12)**

- `P000218` — screen-uncertain — Accurate forced-choice recognition without awareness of memory retrieval
- `P000220` — abstract unavailable — An electrophysiological signature of unconscious recognition memory
- `P000229` — abstract unavailable — Does opposition logic provide evidence for conscious and unconscious processes in artificial grammar learning?
- `P000228` — abstract unavailable — Event-related potentials during conscious and automatic memory retrieval
- `P000227` — screen-uncertain — Hippocampus Is Place of Interaction between Unconscious and Conscious Memories
- `P000214` — abstract unavailable — Impaired recruitment of the hippocampus during conscious recollection in schizophrenia
- `P000258` — screen-in — Inverse forgetting in unconscious episodic memory.
- `P000231` — abstract unavailable — On the Relations among Priming, Conscious Recollection, and Intentional Retrieval: Evidence from Neuroimaging Research
- `P000245` — screen-uncertain — Passive or subliminal re-exposure is sufficient for fear modulation in eye-movement intervention.
- `P000217` — abstract unavailable — The Functional Impact of Mental Imagery on Conscious Perception
- `P000213` — abstract unavailable — Theta synchronization during episodic retrieval: neural correlates of conscious awareness
- `P000270` — screen-uncertain — Unconscious memory suppression.

**DEC (16)**

- `P000304` — screen-in — ADHD patients fail to maintain task goals in face of subliminally and consciously induced cognitive conflicts
- `P000303` — abstract unavailable — Are situation awareness and decision-making in driving totally conscious processes? Results of a hazard prediction task
- `P000314` — abstract unavailable — Dissociable correlates of response conflict and error awareness in error-related brain activity
- `P000309` — screen-in — Evidence for a causal role of superior frontal cortex theta oscillations during the processing of joint subliminal and conscious conflicts
- `P000336` — screen-uncertain — How Implicit Sequence Learning and Explicit Sequence Knowledge Are Expressed in a Serial Response Time Task.
- `P000315` — screen-in — Metacognitive Awareness of Difficulty in Action Selection: The Role of the Cingulo-opercular Network
- `P000297` — screen-in — Neuronal networks underlying the conjoint modulation of response selection by subliminal and consciously induced cognitive conflicts
- `P000286` — screen-uncertain — Nonconscious Influence of Masked Stimuli on Response Selection Is Limited to Concrete Stimulus-Response Associations.
- `P000282` — screen-in — Pre-SMA Gray-matter Density Predicts Individual Differences in Action Selection in the Face of Conscious and Unconscious Response Conflict
- `P000320` — screen-uncertain — Subliminal priming modulates motor sequence learning.
- `P000288` — abstract unavailable — Subliminal priming of actions influences sense of control over effects of action
- `P000295` — abstract unavailable — Subliminally and consciously induced cognitive conflicts interact at several processing levels
- `P000285` — screen-in — The basal ganglia and inhibitory mechanisms in response selection: evidence from subliminal priming of motor responses in Parkinson’s disease
- `P000344` — screen-in — The Basal Ganglia Striosomes Affect the Modulation of Conflicts by Subliminal Information-Evidence from X-Linked Dystonia Parkinsonism.
- `P000281` — screen-in — The negative compatibility effect: Unconscious inhibition influences reaction time and response selection.
- `P000280` — abstract unavailable — The neural basis of one's own conscious and unconscious emotional states

## 4. Rank and marginal-yield curves

Each cell is an eight-element vector for ranks `[5,10,15,20,25,30,35,40]`. `C` is cumulative and `M` is the contribution of the successive five-record band. Values are ordered `unique/title/in/(in+uncertain)/sentinel`.

| Family/source | C unique | C title | C in | C in+unc | C sentinel | M title | M in | M in+unc | M sentinel |
|---|---|---|---|---|---|---|---|---|---|
| ATTN OA | 5,10,15,20,25,30,35,40 | 4,8,10,14,15,19,23,25 | 2,6,7,8,8,9,9,11 | 3,7,8,9,9,11,11,13 | 0,0,1,2,2,2,2,2 | 4,4,2,4,1,4,4,2 | 2,4,1,1,0,1,0,2 | 3,4,1,1,0,2,0,2 | 0,0,1,1,0,0,0,0 |
| ATTN EPMC | 5,8,12,16,20,23,28,32 | 4,4,5,8,9,10,12,14 | 3,3,3,5,6,7,8,8 | 4,4,5,7,8,9,10,10 | 0,0,0,0,0,0,0,0 | 4,0,1,3,1,1,2,2 | 3,0,0,2,1,1,1,0 | 4,0,1,2,1,1,1,0 | 0,0,0,0,0,0,0,0 |
| META OA | 5,10,15,19,24,29,34,39 | 2,4,5,6,6,7,9,10 | 1,2,3,4,4,4,5,5 | 1,3,4,5,5,5,6,6 | 0,0,0,0,0,0,0,0 | 2,2,1,1,0,1,2,1 | 1,1,1,1,0,0,1,0 | 1,2,1,1,0,0,1,0 | 0,0,0,0,0,0,0,0 |
| META EPMC | 5,10,15,20,25,29,34,37 | 4,5,7,8,8,11,11,12 | 0,0,0,0,0,1,1,1 | 1,2,3,3,3,4,4,5 | 0,0,0,0,0,0,0,0 | 4,1,2,1,0,3,0,1 | 0,0,0,0,0,1,0,0 | 1,1,1,0,0,1,0,1 | 0,0,0,0,0,0,0,0 |
| BIND OA | 5,10,15,20,25,30,35,40 | 3,5,8,11,14,16,19,22 | 0,1,2,4,5,5,6,6 | 2,4,5,7,10,11,12,13 | 0,0,1,1,1,1,1,1 | 3,2,3,3,3,2,3,3 | 0,1,1,2,1,0,1,0 | 2,2,1,2,3,1,1,1 | 0,0,1,0,0,0,0,0 |
| BIND EPMC | 5,10,15,20,25,30,35,40 | 3,5,8,11,14,17,18,21 | 0,1,2,5,5,5,6,7 | 2,4,6,9,12,14,15,17 | 0,0,0,1,1,1,1,1 | 3,2,3,3,3,3,1,3 | 0,1,1,3,0,0,1,1 | 2,2,2,3,3,2,1,2 | 0,0,0,1,0,0,0,0 |
| MEM OA | 5,10,14,19,23,28,33,38 | 2,6,9,9,12,13,13,14 | 0,0,0,0,0,0,0,0 | 0,0,1,1,2,2,2,2 | 0,0,0,0,0,0,0,0 | 2,4,3,0,3,1,0,1 | 0,0,0,0,0,0,0,0 | 0,0,1,0,1,0,0,0 | 0,0,0,0,0,0,0,0 |
| MEM EPMC | 5,9,14,18,23,27,31,36 | 1,1,2,2,3,4,6,6 | 0,0,1,1,1,1,1,1 | 1,1,2,2,2,3,4,4 | 0,0,0,0,0,0,0,0 | 1,0,1,0,1,1,2,0 | 0,0,1,0,0,0,0,0 | 1,0,1,0,0,1,1,0 | 0,0,0,0,0,0,0,0 |
| DEC OA | 4,9,14,19,24,29,34,39 | 3,6,7,10,11,14,15,18 | 2,3,3,4,4,5,6,7 | 2,4,4,5,5,6,7,8 | 0,0,0,0,0,0,0,0 | 3,3,1,3,1,3,1,3 | 2,1,0,1,0,1,1,1 | 2,2,0,1,0,1,1,1 | 0,0,0,0,0,0,0,0 |
| DEC EPMC | 5,10,15,19,21,24,28,33 | 1,2,2,2,4,4,4,7 | 0,1,1,1,2,2,2,4 | 1,2,2,2,4,4,4,6 | 0,0,0,0,0,0,0,0 | 1,1,0,0,2,0,0,3 | 0,1,0,0,1,0,0,2 | 1,1,0,0,2,0,0,2 | 0,0,0,0,0,0,0,0 |

Marginal unique vectors, omitted from the table only to keep it readable, are: ATTN OA `5,5,5,5,5,5,5,5`, ATTN EPMC `5,3,4,4,4,3,5,4`; META OA `5,5,5,4,5,5,5,5`, META EPMC `5,5,5,5,5,4,5,3`; BIND OA and EPMC both `5,5,5,5,5,5,5,5`; MEM OA `5,5,4,5,4,5,5,5`, MEM EPMC `5,4,5,4,5,4,4,5`; DEC OA `4,5,5,5,5,5,5,5`, DEC EPMC `5,5,5,4,2,3,4,5`.

Practical interpretation:

- ATTN remains intermittent through rank 40 in both sources; later bands resume yield after zero bands.
- META is sparse but still produces isolated gains at ranks 30–40.
- BIND has sustained plausible yield across the entire tested range, especially in Europe PMC.
- MEM is low-yield, not demonstrated saturated: it contains isolated uncertain gains and substantial abstract-unavailable material.
- DEC is intermittent; Europe PMC has zero bands at 15–20 and 30–35 but yield returns at 36–40.

No family/source has a defensible saturation point from this one ranked sample. A zero band is not treated as saturation.

## 5. Process-trigger query window ablation

This section uses only the stored Tsushima QDYN returns. `Plausible` includes screen-in, uncertain, and abstract-unavailable.

| N/source | Raw | Unique | Title retained | In | Uncertain | Unavailable | Plausible | Tsushima recovered |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 5 OA | 5 | 5 | 4 | 4 | 0 | 0 | 4 | no |
| 5 EPMC | 5 | 5 | 1 | 1 | 0 | 0 | 1 | no |
| 5 union | 10 | 10 | 5 | 5 | 0 | 0 | 5 | no |
| 10 OA | 10 | 10 | 5 | 5 | 0 | 0 | 5 | yes |
| 10 EPMC | 10 | 10 | 2 | 1 | 1 | 0 | 2 | no |
| 10 union | 20 | 20 | 7 | 6 | 1 | 0 | 7 | yes |
| 15 OA | 15 | 15 | 7 | 6 | 0 | 1 | 7 | yes |
| 15 EPMC | 15 | 13 | 2 | 1 | 1 | 0 | 2 | no |
| 15 union | 30 | 28 | 9 | 7 | 1 | 1 | 9 | yes |
| 20 OA | 20 | 20 | 10 | 7 | 2 | 1 | 10 | yes |
| 20 EPMC | 20 | 18 | 2 | 1 | 1 | 0 | 2 | no |
| 20 union | 40 | 38 | 12 | 8 | 3 | 1 | 12 | yes |
| 25 OA | 25 | 25 | 11 | 7 | 3 | 1 | 11 | yes |
| 25 EPMC | 25 | 23 | 2 | 1 | 1 | 0 | 2 | no |
| 25 union | 50 | 48 | 13 | 8 | 4 | 1 | 13 | yes |
| 30 OA | 30 | 30 | 13 | 9 | 3 | 1 | 13 | yes |
| 30 EPMC | 30 | 28 | 2 | 1 | 1 | 0 | 2 | no |
| 30 union | 60 | 58 | 15 | 10 | 4 | 1 | 15 | yes |
| 40 OA | 40 | 40 | 15 | 9 | 4 | 2 | 15 | yes |
| 40 EPMC | 40 | 37 | 2 | 1 | 1 | 0 | 2 | no |
| 40 union | 80 | 77 | 17 | 10 | 5 | 2 | 17 | yes |
| 50 OA | 50 | 50 | 15 | 9 | 4 | 2 | 15 | yes |
| 50 EPMC | 50 | 47 | 6 | 3 | 3 | 0 | 6 | no |
| 50 union | 100 | 95 | 19 | 11 | 6 | 2 | 19 | yes |

### Source-exclusive and marginal plausible yield

| N | OA-only plausible | EPMC-only plausible | Union marginal plausible in new band | Union retained vs 50+50 | Union lost vs 50+50 |
|---:|---:|---:|---:|---:|---:|
| 5 | 4 | 1 | +5 | 5/19 (26.3%) | 14 |
| 10 | 5 | 2 | +2 | 7/19 (36.8%) | 12 |
| 15 | 7 | 2 | +2 | 9/19 (47.4%) | 10 |
| 20 | 10 | 2 | +3 | 12/19 (63.2%) | 7 |
| 25 | 11 | 2 | +1 | 13/19 (68.4%) | 6 |
| 30 | 13 | 2 | +2 | 15/19 (78.9%) | 4 |
| 40 | 15 | 2 | +2 | 17/19 (89.5%) | 2 |
| 50 | 13 | 4 | +2 | 19/19 (100%) | 0 |

The last two marginal rows cover ten-rank bands (31–40 and 41–50); earlier rows cover five. The decline is gradual, not a hard saturation. Europe PMC contributes little through rank 40 but adds four source-exclusive plausible works at rank 50; two of the union's final two new plausible works are obtained only in its late band after cross-source deduplication effects. OpenAlex recovered Tsushima naturally at rank 9 and added no new retained title from ranks 41–50.

For ranks `[5,10,15,20,25,30,40,50]`, source-specific cumulative/marginal plausible vectors are: OpenAlex cumulative `4,5,7,10,11,13,15,15`, marginal `4,1,2,3,1,2,2,0`; Europe PMC cumulative `1,2,2,2,2,2,2,6`, marginal `1,1,0,0,0,0,0,4`; union cumulative `5,7,9,12,13,15,17,19`, marginal `5,2,2,3,1,2,2,2`. The final two bands in each vector span ten ranks.

For a reproducible process search, 50+50 is the only tested setting with zero calibrated loss. 40+40 is a reasonable Balanced frontier with 89.5% plausible retention and two measured losses. 30+30 loses four. Windows at 25 or below discard at least six of 19 plausible records and are not a good default merely because they are cheaper.

## 6. Cross-route redundancy

Bibliographic identity was normalized by DOI where present and otherwise by normalized title plus year. The comparison used 345 non-LEARN QCAL works against 574 principal-route paper records represented across CALIB001–003 plus CALIB004 QDYN. Those 574 records produced 837 DOI and title/year keys; this is a key count, not a work count.

| Quantity | Estimate |
|---|---:|
| QCAL works also encountered through represented principal routes | 21 |
| QCAL-only works | 324 |
| Overlap works title-retained in CALIB004 | 9 |
| Overlap works abstract screen-in | 8 |
| QCAL-only title-retained | 122 |
| QCAL-only abstract screen-in | 34 |
| QCAL-only abstract uncertain | 27 |
| QCAL-only abstract unavailable | 20 |
| Observed overlapping sentinel | Tsushima |
| Observed QCAL-only sentinels in this cross-run match | Lamy, Keizer |

The represented principal-route workload included the following durable route volumes: CALIB001 query 25, review 9, backward 4, forward 4, and seed 1 encounters; CALIB002 independent query 2,400, forward 347, backward 129, empirical seed 2, and review anchor 1; CALIB003 query 2,400 and seed 1; CALIB004 QDYN 100 encounters/95 unique works. These routes had different scopes and query instruments, so 21/345 is not a general overlap rate.

If QCAL had run last in these represented data, at least 21 first paper-level semantic screens could have been avoided, including nine title-retained decisions and eight recorded screen-ins. The remaining 324 QCAL-only works show why the blind lane cannot be removed. In an actual registered run, all six frozen empirical seeds must enter before QCAL; therefore all three QCAL-recovered anchors—Tsushima, Lamy, and Keizer—would be rediscoveries even though only Tsushima overlaps in this limited cross-run identity reconstruction. Scientific decisions are not transferred across independent runs; this calculation is solely an execution-order counterfactual within one future run.

## 7. Route-order simulation

The proposed principal-first/blind-last order preserves current discovery obligations **conditionally**. It changes when a bounded route runs, not what it must search or screen. It is safe only under a frozen operational rule with all of these properties:

1. the blind lane is mandatory and cannot be skipped because the principal routes are large or resources are depleted;
2. every blind result is deduplicated against the run's complete logical-paper index before semantic screening;
3. rediscovery adds a discovery record while reusing the current paper-level decision;
4. genuinely new blind results are individually screened;
5. a newly relevant blind result reopens backward/forward citation expansion;
6. a blind result that earns a new qualifying Y also activates or reopens the corresponding process-trigger search;
7. all reopened frontiers must again satisfy their frozen stopping rules before completion; and
8. ranked windows obey the frozen publication cutoff/query snapshot semantics so that running later does not silently change the candidate window.

Step 12 of the proposed ordering mentions citation reopening but not the process-search case. That omission must be corrected operationally before the ordering can be called obligation-preserving. Edge cases are a blind-only work that creates a new citation node, a blind-only full text that earns a previously unseen Y, and long-running searches whose live relevance ranking changes over time. These alter downstream discoverability unless reopening and temporal snapshot rules are explicit.

With those safeguards, the order is **CONDITIONALLY SAFE** and recommended. It does not justify transferring decisions between agents or runs.

## 8. Paper-level decision reuse audit

| Reuse guarantee within one registered run | Current status | Basis and gap | Optimization classification |
|---|---|---|---|
| One title-screen decision per logical paper | Guaranteed already | One current logical-paper row holds the title state; deduplicated discovery rows point to it. Revisions remain logged. | SAFE to exploit |
| One abstract-screen decision per logical paper | Guaranteed already | Same current-state structure at paper level. | SAFE to exploit |
| Rediscovery adds provenance without repeated semantic screening | Partially guaranteed | `discoveries.csv` preserves every encounter and the paper row centralizes state, but no explicit execution guard proves an agent cannot regenerate/revise the same semantic judgment on rediscovery. | SAFE opportunity: frozen reuse rule |
| One verified full-text acquisition per logical paper, reused across comparisons | Partially guaranteed | Retrieval/missing-text state and paths are paper-level, but one-copy/one-extraction reuse is not stated as an invariant for every acquisition route. | SAFE opportunity |
| One auxiliary acquisition reused across evidence links | Partially guaranteed | Evidence links can point repeatedly to support, but canonical auxiliary identity/acquisition reuse is not fully guaranteed. | SAFE opportunity |
| One bibliographic identity resolution reused across all discovery routes | Partially guaranteed | DOI/title/year dedup and retained paper IDs create one logical state, but there is no explicit canonical alias/index cache preventing repeated identity work. | SAFE opportunity |

These are execution guarantees only. Reuse must not collapse uncertain duplicates, suppress discovery provenance, or prevent logged revisions when genuinely new evidence changes a decision.

## 9. Route-aware full-text short-circuit simulation

The simulation combines 13 fully evaluated unfamiliar CALIB003 comparisons with the six focal anchor comparisons in the current regression diagnostic. It does not revise any historical classification.

| Stage/route | Comparisons |
|---|---:|
| Entering Stage 1 structural/design audit | 19 |
| Awareness-effect route structurally viable | 5 |
| Unaware-capacity route structurally viable | 15 |
| Requiring null/no-difference audit | 3 |
| Awareness-effect detailed statistical audits avoidable | 11 |
| Capacity detailed statistical audits avoidable | 4 |
| Meyen audits avoidable | 4 |
| Null/equivalence audits avoidable | 16 |
| Entire detailed outcome-route reasoning avoidable | 4 |

Derivation: none of the 13 unfamiliar comparisons had strong A+F+E for the awareness-effect route; nine retained strong A+F and therefore still required capacity-oriented result inspection despite weak E; two had a stored tested difference/inconclusive pattern requiring null-oriented inspection. Across the six anchors, five had matched/diagnostic E, all six had strong A+F, and Keizer required the no-detectable-difference audit. The four fully dead comparisons were the three P002166 comparisons and P002220_E01_C01, whose structural A/F combination closed both strong inference routes. Those four also account for avoidable Meyen work.

The counts are route-specific, not a license to stop reading when E is weak. For each of the 15 capacity-viable comparisons, results must still be inspected enough to decide whether the *named conservative Y* is positively demonstrated under unawareness, with adequate statistics and the current Meyen logic where applicable. A route can be marked `not-tested`/`not-applicable` only with a durable structural reason. Under those conditions, route-aware short-circuiting is **CONDITIONALLY SAFE** and promises a large reduction in irrelevant statistical prose without changing scientific criteria.

## 10. Within-paper evidence reuse

An internal `experiment_evidence_group`, or equivalent immutable assessed-premise object, is a **SAFE** execution optimization if every comparison retains its own X, Y, A/E/F codes, result, statistics, and why. The shared object may hold participant/stimulus regime, awareness validation, first-order evidence checks, control experiments, and auxiliary sources; comparisons cite it and add only comparison-specific reasoning.

Observed/estimated utility:

- **Tsushima:** five comparison rows share the threshold-validation/E-diagnostic bundle. One assessed bundle referenced five times could avoid about four repeated premise write-ups.
- **Lin:** the main and control experiments share visibility/location premises. The regression diagnostic supports qualitative reuse, but not a durable comparison-row count from which to calculate savings.
- **Lamy:** Exps. 1–2 and the Exp. 3 first-order-evidence control form one diagnostic bundle; the focal comparison can reference one assessed premise rather than regenerating three experiment narratives.
- **Ben-Haim:** Exp. 7 and the Exp. 6/late-control support can be assessed as one bundle while leaving the focal crossover code comparison-specific.
- **CALIB003 unfamiliar sample:** 13 comparisons occurred across six papers. Five multi-comparison papers contained 12 of them in groups of 3, 2, 2, 2, and 3. Paper/experiment premise reuse could avoid about seven duplicate premise assessments versus per-comparison regeneration. This is an upper-bound reasoning-unit estimate, not seven fewer scientific comparisons.

No bundle may propagate an A or E code to a comparison whose participant, stimulus, awareness measure, timing, or first-order evidence differs materially.

## 11. Static precomputation before multi-agent runs

| Precomputed object | Independent screening preserved? | Independent classification preserved? | Auditability preserved? | Candidate-universe bias | Assessment |
|---|---|---|---|---|---|
| Canonical DOI/OpenAlex/PMID identity for empirical seeds | Yes | Yes | Yes, with source/date/hash | None if identity is verified | SAFE |
| Canonical identity for review/discovery anchors | Yes | Yes | Yes | None if identity-only | SAFE |
| Verified seed/anchor bibliographic metadata | Yes | Yes | Yes, if raw/source provenance retained | Low; metadata errors must remain correctable | SAFE |
| Complete static backward-reference lists for frozen empirical seeds | Yes, if agents screen every entry independently | Yes | Yes, with extraction source/date/hash and completeness check | Possible if list extraction is incomplete or stale | CONDITIONALLY SAFE |
| Complete bibliography/reference lists for frozen review anchors | Yes, under the same rule | Yes | Yes | Possible extraction/edition bias | CONDITIONALLY SAFE |

Precomputation must stop before relevance, eligibility, A/E/F, result, or stopping decisions. It must not include dynamically discovered forward-citation results. A static list shared identically across Codex/Claude/GLM is non-scientific input preparation; their screening and classification records must remain independent.

## 12. Batch semantic screening

Recommended default context batches are **25 titles** and **10 abstracts**. For unusually dense/ambiguous sets, reduce to 15–20 titles or 6–8 abstracts. These sizes amortize prompt/schema overhead while leaving enough room for an individual decision and why for every paper. Larger abstract batches raise cross-paper contamination and reason-truncation risk; very small batches sacrifice throughput without scientific benefit.

Batching is **SAFE** only as context amortization. Each logical paper still receives its own durable title decision and why, and, where applicable, its own abstract decision and why. Batch membership is not evidence. Regex exclusion, keyword auto-rejection, embeddings thresholds, citation-count filters, and numeric LLM relevance thresholds remain prohibited.

## 13. Retrieval and full-text efficiency

The registered workflow can safely resolve identity once, apply a frozen publisher/OA/repository cascade, stop after the correct article is verified, store/hash once, extract text once, cache render/page pointers within the run, and reuse the verified copy across comparisons and evidence bundles. Article identity, completeness, and version verification remain mandatory.

CALIB003 recorded 12 sampled retrieval records excluding the Tsushima seed: seven obtained, five pending, and 22 source-route attempts. Thirteen unfamiliar comparison rows came from six papers that yielded comparisons; a naive per-comparison acquisition/extraction would require 13 units, whereas paper-level reuse requires six, an upper-bound avoidance of seven duplicate acquisition/extraction units. The historical data do not show that all seven duplicates were actually incurred; this is a counterfactual saving. Fixed-cascade early stopping should also reduce repeated route attempts after success, but the durable records do not support a precise percentage.

This optimization is **SAFE** and improves auditability when the cascade, verification result, hash, extraction version, and cached page map are logged.

## 14. Multi-agent independence versus shared static work

Scientific independence must remain separate for discovery judgments, title/abstract screening, A/E/F coding, outcome/capacity/effect inference, statistical and Meyen decisions, and judgment-dependent stopping. Agents must not import another run's discoveries or classifications.

The following may be supplied identically: DOI normalization rules; verified seed and anchor identities/metadata; schema validation; frozen query renderings; and complete, hashed static seed/anchor reference lists whose extraction is independently auditable. Sharing those objects does not turn separate agents into one run because they are fixed candidate inputs, not scientific decisions.

Do not share dynamically discovered route results, dedup judgments beyond canonical frozen identities, semantic decisions, full-text annotations, evidence coding, outcomes, or frontier-saturation judgments. This conservative boundary preserves both operational economy and the purpose of independent Codex/Claude/GLM runs.

## 15. Estimated workload and cost

### What was observed

| Calibration | Encounters | Unique papers | Comparison rows | Other directly relevant observation |
|---|---:|---:|---:|---|
| CALIB001 | 43 | 35 | 14 | 21 searches |
| CALIB002 | 2,879 | 2,483 | 5 | 35 searches; bounded query and citation calibration |
| CALIB003 | 2,401 | 2,115 | 20 | 13 unfamiliar fully evaluated comparisons used here; 12 sampled retrieval records excluding Tsushima |
| CALIB004 | 580 | 498 | 1 | 480 QCAL encounters + 100 QDYN; seven OpenAlex calls cost $0.007 |

These are different calibrations, not additive forecasts. In particular, the registered number of seed/review nodes, citation waves, eligible full texts, earned Ys, and process-trigger calls remains unknown.

### Comparable supplementary-instrument workload

This table combines one QCAL execution with one Tsushima-like QDYN trigger using the actual stored returns. It is the only part of a registered workload that can be compared directly across the candidate configurations.

| Execution | QCAL + one QDYN raw | Unique works across both lanes | Title-retained | Abstract in | Uncertain | Abstract unavailable | OA calls / observed-price estimate |
|---|---:|---:|---:|---:|---:|---:|---|
| Current unoptimized calibration instrument: six QCAL families 40+40; QDYN 50+50 | 580 | 498 | 151 | 48 | 34 | 24 | 7 / about $0.007 |
| Conservative: five QCAL families 40+40; QDYN 50+50 | 500 | 419 | 141 | 45 | 33 | 22 | 6 / about $0.006 |
| Balanced: five QCAL families 30+30; QDYN 40+40 | 380 | 328 | 115 | 39 | 30 | 19 | 6 / about $0.006 |
| Minimal: five QCAL families 20+20; QDYN 30+30 | 260 | 235 | 86 | 33 | 22 | 11 | 6 / about $0.006 |

The current-to-Conservative reduction is mostly retirement of the pathological LEARN rendering: 80 encounters and 79 unique first screens in this combined reconstruction. It also removes 10 title-retained, three screen-in, one uncertain, and two abstract-unavailable LEARN records. Those plausible flags are why LEARN retirement must be described as removal of a bad instrument, not proof of zero candidate loss; learning/adaptation remains discoverable through the principal routes and should be redesigned if a blind-lane check is required.

Against the five-family N=40 QCAL baseline alone, Balanced saves 100 encounters and 78 unique screens while losing six of 42 screen-ins; Minimal saves 200 encounters and 158 unique screens while losing 12 of 42 screen-ins. For one process trigger, Balanced saves 20 encounters/18 unique works and loses two of 19 plausible records; Minimal saves 40 encounters/37 unique works and loses four. OpenAlex monetary cost changes little because each source/family still uses one request; page-size reductions save screening, not call count. At the observed $0.001 per OpenAlex call, every additional earned Y adds about $0.001 for its OpenAlex process query; Europe PMC monetary cost was not recorded.

Route-last ordering does not reduce query calls or raw encounters, because the lane remains mandatory. In the represented overlap it avoids at least 21 new semantic decisions by reusing prior paper states. More could be saved in a full seed-rich run, but the calibration does not justify extrapolating an overlap percentage.

### Full-text reasoning burden

The observed CALIB003 retrieval sample had 12 records, 22 route attempts, seven successes, and five pending. The anchor-plus-unfamiliar simulation had 19 Stage 1 comparison audits. A naive uniform workflow exposes up to 19 slots each for awareness-effect, capacity, Meyen, and null/equivalence analysis (76 route-specific slots). Route-aware analysis retains 5 + 15 + 15 + 3 = 38 detailed route slots under the retrospective mapping, while all 19 still receive structural audit. These slots are not equal-cost and are not token counts; they show where reasoning can be removed without changing criteria.

Principal citation workload dominates and remains unknown for a registered run. CALIB002 alone recorded 479 raw seed/review/citation-route encounters (347 forward + 129 backward + 2 empirical-seed + 1 review-anchor) alongside its separate 2,400 query encounters. It would be false precision to multiply that example by the future seed count or to estimate total model tokens from it.

### Qualitative burden by configuration

- **Current unoptimized:** highest title/identity burden; repeated reasoning remains possible; every comparison may receive prose for dead routes.
- **Conservative:** low scientific-loss risk; moderate query reduction from retiring LEARN; large reasoning savings from route-last reuse, batching, evidence groups, retrieval caching, and route-aware audits.
- **Balanced:** meaningfully lower screening burden, but observed QCAL and QDYN candidate losses require explicit acceptance in a frozen rule.
- **Minimal:** roughly halves the current calibration instrument's unique-paper load, but discards substantial calibrated signal and should be considered only a coarse coverage check.

## 16. SAFE versus risky optimization table

| Optimization | Estimated saving | Scientific risk | Auditability impact | Independence impact | Recommendation |
|---|---|---|---|---|---|
| Query lane last | At least 21 reused screens in represented overlap; unknown full-run gain | **CONDITIONALLY SAFE**: blind lane and all reopenings must remain mandatory | Improves if every rediscovery is logged | None within each run | Adopt with frozen citation + process reopening rule |
| Paper decision reuse | Avoids every repeated title/abstract judgment after dedup | **SAFE** | Improves single-state history | None; never reuse across agents/runs | Adopt |
| Smaller OpenAlex QCAL windows | At N=30, 50 fewer OA encounters than N=40 across five families | **CONDITIONALLY SAFE** but measured yield loss; later bands still produce candidates | Neutral if bound is frozen | None | Do not use in Conservative; Balanced candidate only |
| Remove Europe PMC topic querying | 200 QCAL encounters at N=40 | **SCIENTIFICALLY RISKY**: loses 42 exclusive retained and 13 exclusive screen-ins | Candidate-universe contraction remains auditable but incomplete | None | Do not recommend |
| Drop generic QCAL families | 80 encounters per family at N=40 | **SCIENTIFICALLY RISKY** for ATTN/META/BIND/DEC; MEM at best conditional | Makes blind-spot coverage narrower | None | Retain all five; handle LEARN separately |
| Smaller process-trigger windows | 20 encounters at 40+40; 40 at 30+30 | **CONDITIONALLY SAFE** with measured loss of 2/19 or 4/19 plausible records | Good if source/rank bound frozen | None | 50+50 Conservative; 40+40 Balanced |
| Route-aware full-text short-circuit | Avoids 11 awareness, 4 capacity, 4 Meyen, and 16 null detailed audits in 19-comparison simulation | **CONDITIONALLY SAFE**: capacity result inspection must survive weak E | Improves when dead-route why is explicit | None | Adopt after operational decision tree is frozen |
| Batch semantic screening | Amortizes model context across about 25 titles or 10 abstracts | **SAFE** | Neutral if every row/why is durable | None | Adopt |
| Static seed/reference precomputation | Avoids repeated identity and reference extraction in every agent | **SAFE** for identity/metadata; **CONDITIONALLY SAFE** for reference completeness | Improves with hashes/source snapshots | Preserves independence if no relevance decisions shared | Adopt conservative static subset |
| Within-paper evidence reuse | About 4 premise restatements in Tsushima and about 7 in unfamiliar sample | **SAFE** if codes remain comparison-specific | Improves evidence consistency | None | Adopt internal evidence groups |
| Retrieval/text/render cache | Up to 7 duplicate acquisition/extraction units in unfamiliar comparison sample | **SAFE** after article verification | Improves hash/path traceability | None | Adopt within each run |
| Heuristic keyword exclusion | Potentially large | **SCIENTIFICALLY RISKY** | Opaque false negatives | Could correlate agent errors | Reject |
| Embedding-based exclusion | Potentially large | **SCIENTIFICALLY RISKY** | Threshold/model drift harms auditability | Correlates candidate universes | Reject |
| Citation-count prioritization | Little if all records are screened; apparent savings only if low-cited work is deferred past stopping | **SCIENTIFICALLY RISKY** when it affects inclusion or bounded retrieval | Reproducible ordering cannot cure coverage bias | Correlates agents toward canonical literature | Reject as an efficiency filter; harmless only as nonexclusive ordering with complete screening |

## 17. Configuration frontier

All configurations retain ATTN, META, BIND, MEM, and DEC. None treats a dropped query family as a scientific exclusion. LEARN is kept outside the configured maximum because its current rendering is pathological; its six plausible flags and the resulting coverage gap must remain documented.

### Conservative

- **QCAL:** OpenAlex + Europe PMC, N=40 per source/family; maximum 400 encounters.
- **Calibrated QCAL signal:** all three recovered sentinels; 42/42 non-LEARN screen-ins retained, none lost; 131 retained titles, 27 uncertain, 21 unavailable.
- **Process trigger:** OpenAlex + Europe PMC, N=50 each; maximum 100 encounters per earned Y; 19/19 plausible Tsushima-query records retained.
- **Order/reuse:** principal routes first, blind lane last, pre-screen deduplication, paper-decision reuse, mandatory citation and process reopening.
- **Batches:** 25 titles, 10 abstracts, with smaller ambiguity batches.
- **Full text:** Stage 1 for every comparison; detailed analysis only for viable routes; capacity route never gated by E.
- **Static work:** verified identities/metadata shared; hashed complete static reference lists may be shared after completeness validation.
- **Classification:** SAFE execution savings plus conditional route-order/short-circuit rules; essentially no loss in the retained calibrated instrument.

### Balanced

- **QCAL:** both sources, N=30 per source/family; maximum 300 encounters.
- **Calibrated QCAL signal:** all three sentinels; 36/42 screen-ins retained (85.7%), six lost; 106 retained titles, 25 uncertain, 18 unavailable.
- **Process trigger:** both sources, N=40 each; maximum 80 encounters per earned Y; 17/19 plausible records retained (89.5%), two lost.
- **Order/reuse, batches, full text, static work:** same as Conservative.
- **Classification:** CONDITIONALLY SAFE as a frozen bounded instrument, but not calibrated-lossless. It saves 120 raw encounters and 91 unique works relative to Conservative in the one-trigger reconstruction.

### Minimal

- **QCAL:** both sources, N=20 per source/family; maximum 200 encounters. Keeping both sources makes this a genuine two-index coverage check rather than an OpenAlex-only sentinel test.
- **Calibrated QCAL signal:** all three sentinels; 30/42 screen-ins retained (71.4%), 12 lost; 78 retained titles, 18 uncertain, 10 unavailable.
- **Process trigger:** both sources, N=30 each; maximum 60 encounters per earned Y; 15/19 plausible records retained (78.9%), four lost.
- **Order/reuse, batches, full text, static work:** same as Conservative.
- **Classification:** a coarse coverage check with substantial measured loss. It is **CONDITIONALLY SAFE only if the protocol explicitly defines this limited blind-spot obligation**; it is scientifically risky if represented as equivalent to the N=40/N=50 calibrated coverage.

The frontier does not include an OpenAlex-only option because the observed Europe PMC-unique signal is too large to call that an obligation-preserving default.

## 18. Manuscript-anchor invariance

The empirical-seed mechanism, not QCAL or QDYN recovery, must guarantee entry of Tsushima, Lin & Murray, Lamy, Ben-Haim, Persaud, and Keizer. Every configuration above assumes all six are initialized and scientifically evaluated under unchanged draft-0.7.1 criteria.

| Optimization class | Anchor effect |
|---|---|
| Route-last ordering and paper-decision reuse | No effect if all seeds are initialized first; QCAL recovery becomes provenance-only rediscovery. |
| Smaller query/process windows, source/family changes | Cannot remove a seed anchor, but can reduce discovery of unfamiliar corroborating or contrasting work. Any implementation that makes anchor entry depend on QCAL violates the package. |
| Route-aware full-text short-circuit | Preserves all anchors only if weak E does not gate capacity. Keizer must still receive capacity and null-result analysis; Tsushima and Lin retain awareness-effect analysis; Lamy and Ben-Haim retain bundle/component analysis; Persaud retains matched scalar analysis. |
| Evidence-group reuse | Preserves anchors if Lamy's multi-experiment E bundle, Ben-Haim's late controls, Tsushima's threshold/control bundle, and Lin's location/visibility structure are not flattened into generic paper-level codes. |
| Static precomputation, batching, and retrieval cache | No scientific effect if individual screening/classification and article verification remain independent. |
| Keyword, embedding, or citation-count exclusion | Could violate guaranteed evaluation if applied upstream to seeds or support evidence and is rejected. |

No recommended optimization alters the anchor classifications in the current regression diagnostic. Removing Europe PMC or shrinking windows would still pass a seed-entry anchor check, which is precisely why sentinel invariance alone is insufficient evidence of safe discovery coverage.

## 19. Unresolved uncertainties

1. CALIB004 is one ranked snapshot. Live source rankings, index coverage, and abstracts can change; no empirical saturation claim follows.
2. QCAL screen-in is not full-text eligibility. Source/family yields may change materially after retrieval and A/E/F coding.
3. Twenty-one QCAL works lacked abstracts at the full non-LEARN window. Family/source ablations disproportionately remove unresolved evidence, so apparent precision is optimistic.
4. The cross-route overlap joins deliberately different calibration scopes. The 21 avoided-screen estimate is a lower-scope counterfactual, not a registered-run rate.
5. QDYN ablation is based on Tsushima's Y only. Other earned Ys may have very different source and rank curves.
6. The LEARN query was pathological but still produced three screen-ins, one uncertain, and two abstract-unavailable records. Retiring it improves efficiency but does not prove the scientific learning/adaptation blind spot is empty.
7. Full-text and evidence-reuse savings are reasoning-unit estimates from small samples; actual model-token and wall-time savings were not durably recorded.
8. The 19-comparison route simulation maps current structural fields and anchor diagnostics to viable routes retrospectively. It is not a validated execution engine and must not replace protocol decisions.
9. OpenAlex cost extrapolation assumes the observed $0.001/call pricing; future pricing/authentication is outside this retrospective audit. Europe PMC cost and rate-limit burden were not quantified.
10. Static reference-list completeness needs an operational verification rule. A shared incomplete extraction would correlate omissions across agents.
11. Section 3's exact manifest defines candidate material after the durable abstract state and therefore does not enumerate the 41 family-exclusive title-retained records already screened out at abstract stage; their counts remain in the ablation table.

## Recommendation

Adopt the **Conservative execution configuration** at freeze unless a separate scientific decision explicitly accepts the Balanced configuration's measured losses. Its query bounds preserve all calibrated non-LEARN and QDYN signal while the main savings come from lossless execution changes: principal-first/blind-last ordering with citation and process reopening, one semantic decision per logical paper, batch contexts of 25 titles/10 abstracts, reusable evidence groups, one verified text/extraction/render cache per paper, and route-aware detailed analysis.

Do not remove Europe PMC topic search, do not drop the five retained families, and do not use heuristic or embedding exclusions. Do not freeze the current LEARN rendering; document its six plausible flags and either redesign that blind-spot family before freeze or rely explicitly on the unchanged principal discovery obligations rather than pretending the current query is useful.

This is a recommendation only. Nothing was implemented, frozen, registered, or searched.
