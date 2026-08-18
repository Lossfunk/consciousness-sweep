# Consciousness X → Y Literature Sweep Protocol

**Version:** draft-0.5
**Registration status:** pre-freeze; not preregistered

This file is the scientific and procedural source of truth for the sweep. It is written for human and AI screeners. `AGENTS.md` governs execution mechanics. Neither file may change during a registered run.

## 1. Aim and scope

The sweep asks:

> For a particular entity or content X and cognitive process Y, does awareness of X change whether, or how well, Y can use X?

The search is outcome-neutral. A useful experiment may report an awareness-linked difference, a capacity preserved without awareness, or an inconclusive result. A study is not a hit because awareness helps; it is useful because its design can inform the X → Y question.

The atomic scientific unit is a **paper × experiment × X→Y comparison**, not a paper or experiment as a whole. One experiment may contain multiple comparison records. Multiple dependent measures that jointly operationalize the same Y and support the same critical inference may remain in one comparison. Genuinely different Y processes receive separate comparisons, as do distinct critical awareness contrasts that support different inferences. Assign A and F for each comparison from the methods/design. Assess design-based E next; when evidence is not matched, inspect the result pattern only for the frozen `E-diagnostic` test and then finalize E. Classify the empirical outcome only after A, F, and final E are established.

## 2. Design classification

### 2.1 A — awareness of X

Code awareness independently of E and F.

Unawareness of X may be supported by subjective awareness evidence, sufficiently informative objective invisibility evidence, or both. Record the orthogonal `awareness_evidence_type` as `subjective`, `objective-invisibility`, `mixed`, or `none`.

- `A-direct`: qualifying subjective or objective-invisibility evidence is obtained in the relevant experiment, trial, block, condition, or stimulus regime. Subjective examples include seen/unseen judgments, graded visibility, and PAS-like ratings; the response need not be verbal.
- `A-validated`: qualifying subjective or objective-invisibility evidence is obtained in a separate validation procedure whose conditions plausibly transfer to the main experiment. Assess transfer using at least stimulus parameters, masking or suppression, timing, attentional allocation, task demands, and participant population. A validation regime must not plausibly make awareness lower than in the main experiment while being used to establish unawareness there.
- `A-transfer-risk`: a separate subjective or objective-invisibility validation exists, but its sensitivity or transfer to the main experiment is materially uncertain.
- `A-absent`: no qualifying subjective or objective-invisibility evidence supports the awareness classification. Masking, stimulus condition, neural activity, or an insensitive visibility test alone does not qualify.

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
- `E-diagnostic`: first-order evidence is not matched, but the whole result pattern rules out the relevant simple explanation in which more first-order evidence about X monotonically produces more or stronger Y. Always state the diagnostic reason explicitly.
- `E-physical-only`: the physical stimulus or event is nominally matched, but direct first-order evidence is unequal or inadequately assessed.
- `E-uncontrolled`: outside the nominally identical-physical-X case, first-order evidence differs or is inadequately controlled or known, so a simple first-order-evidence account of Y remains viable.

`E-matched` and `E-diagnostic` are alternative strong routes, not rank-ordered tiers.

### 2.3 E assessment sequence and outcome neutrality

First assess E from the methods. Assign `E-matched` only when its positive matching requirements are met. Otherwise record the provisional non-diagnostic status—`E-physical-only` when physical X is nominally identical, and `E-uncontrolled` otherwise. Then inspect the full result pattern specifically to decide whether the frozen `E-diagnostic` criterion is satisfied. If it is, finalize E as `E-diagnostic`; if not, retain the provisional status.

This limited use of results does not make study selection depend on whether an outcome is theoretically attractive. The `E-diagnostic` criterion is frozen in advance, is applied to every eligible unmatched case, and is evaluated before outcome classification.

Tsushima, Sasaki, and Watanabe (2006) motivate `E-diagnostic`: interference is non-monotonic with motion coherence, is maximal around the awareness threshold, and the interference dip shifts when the perceptual threshold is experimentally shifted. The diagnostic value comes from the whole pattern, not from non-monotonicity alone. Charles et al. (2013) motivate the distinction between identical physical stimuli and identical internal evidence.

### 2.4 F — meaningful downstream use Y

F is primarily an eligibility gate, not an ordinal score.

- `F-meaningful`: the dependent measure identifies a defensible distinct downstream functional relation or use of X at an appropriately conservative level, such as regulation/control of distractor interference, metacognitive evaluation, updating, binding, maintenance or memory, action selection, rule-guided use, or adaptive use. The exact cognitive or neural mechanism implementing that function need not be identified.
- `F-ambiguous`: the dependent measure plausibly reflects downstream use or transformation beyond direct registration or report, but even a conservative function-level Y cannot be assigned without choosing among substantively different downstream uses.
- `F-not-meaningful`: the dependent variable establishes only direct detection or discrimination of X, generic registration, a generic neural response, or generic priming whose principal implication is merely that some information about X survived.

Assign Y at the most specific functional level justified by the dependent measure. Do not make Y artificially fine-grained, and do not require the experiment to identify the mechanism implementing Y in order for Y to be meaningful. For example, a behavioral measure may justify `Y = regulation/control of the behavioral influence of a task-irrelevant distractor` while leaving active spatial suppression, inhibitory control in LPFC, attentional filtering, altered capture, and other implementations unresolved. That is `F-meaningful` with ambiguous mechanism, not `F-ambiguous`.

For every comparison, record `Y_label`, `Y_description`, `Y_evidence_role`, and `Y_interpretation_clarity` separately from `mechanistic_interpretation` and `mechanism_clarity`. `mechanism_clarity` is never part of the F gate. Neural evidence may support a proposed mechanism for a behavioral Y, but a generic neural difference is not itself a qualifying Y merely because it is compatible with that mechanism. `F-ambiguous` supports discovery recall but does not pass the strongest empirical-lot filter, which continues to require `F-meaningful`.

## 3. Result classification

Determine A, E, and F before classifying results.

- `awareness-linked-difference`: Y uses X differently between aware and unaware conditions.
- `preserved-capacity`: requires both (1) positive evidence that Y uses X in the X-unaware condition and (2) an analysis that does not support a meaningful awareness-linked difference in that use under the tested conditions.
- `inconclusive`: the comparison is relevant, but the result or analysis does not cleanly support either conclusion.

> Evidence that Y operates without awareness and evidence that awareness does not materially change Y are evaluated separately. A null aware–unaware difference alone does not establish preserved capacity.

Use one direction label where applicable: `aware>unaware`, `unaware>aware`, `qualitative-change`, `no-detectable-difference`, or `other`.

Record the two preserved-capacity components separately:

- `unaware_Y_evidence = positive` means the comparison provides positive statistical evidence that Y actually uses X in the unaware condition. Other values are `absent`, `unclear`, and `not-applicable`.
- `null_evidence_adequacy = adequate` means the comparison satisfies at least one of the three criteria in Section 4.2. Other values are `weak`, `unclear`, and `not-applicable`.

These fields remain separate from `null_evidence_strength`, which records the form of the null evidence.

## 4. Statistical audit

Every full-text comparison receives a separate audit with overall status `adequate`, `concern`, or `unclear`.

### 4.1 Critical difference

When awareness is claimed to change Y, determine whether the aware-versus-unaware difference or interaction was itself tested. Do not accept “significant in aware + nonsignificant in unaware” as evidence that the two conditions differ.

### 4.2 Null and preserved-capacity evidence

Assign `null_evidence_adequacy = adequate` only when the study provides at least one of:

1. a successful equivalence test using an explicitly stated or justified equivalence margin;
2. `BF01 >= 3` in favour of the null; or
3. a confidence interval entirely contained within an explicitly stated smallest-effect or equivalence region.

A merely nonsignificant aware/unaware difference or interaction receives `weak`. Insufficient reporting to assess the strength of the null receives `unclear`. Do not invent an equivalence margin for a study that did not state or justify one. Retain `null_evidence_strength` to describe whether the evidence came from equivalence testing, Bayes factors, confidence intervals, nonsignificance alone, mixed evidence, or unclear reporting.

### 4.3 General concerns

Where relevant, flag multiple-comparison problems, inappropriate statistical models, pseudoreplication, materially selective exclusions, critical exploratory or unconfirmed analyses, and other obvious problems. State why each flag matters to the critical inference.

## 5. Meyen diagnostic

Apply this diagnostic only when a study reasons that (1) a direct measure of X is at or near chance or nonsignificant, (2) an indirect measure shows an effect, and therefore (3) X was processed unconsciously.

Meyen et al. require evidence for an **indirect task advantage**: the indirect measure must be shown to be more sensitive to X than the direct measure on a comparable scale.

Record `Meyen_applicable` as `yes` or `no`. When applicable, use `Meyen-satisfied`, `Meyen-failed`, or `Meyen-unassessable`, and explain why. Passing does not by itself prove unconscious processing and does not replace the A requirement.

## 6. Screening funnel

Every encountered paper remains in the master audit record. Every decision includes a brief why.

Title and abstract screens are semantic decisions under this protocol. Agents may process records in batches, but each paper receives its own decision, method, and reason. Keyword, regex, or similar lexical heuristics may assist prioritization; they may not independently produce a scientific exclusion unless that exact deterministic exclusion rule was preregistered and its rule identifier is recorded. In the absence of such a frozen rule, the registered default is agent semantic screening.

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

## 8. Full-text comparison evaluation order

First enumerate the distinct X→Y comparisons within each potentially relevant experiment. Assign a separate comparison when Y is genuinely different or when a distinct critical awareness contrast supports a different inference. Measures that jointly operationalize the same Y and critical inference may remain together. Then, for each comparison:

1. Identify X and the aware/unaware contrast.
2. Identify the awareness measure or validation.
3. Identify the direct first-order evidence measure.
4. Identify Y at the most specific conservative functional level justified by its dependent measure; record finer mechanistic interpretation separately.
5. Check the article and supplement for explicit classification-critical external dependencies; resolve and record each auxiliary source where reasonably possible.
6. Assign A from the qualifying awareness evidence, record `awareness_evidence_type`, and explain objective-test informativeness where applicable.
7. Assign F from the downstream-use design and explain why.
8. Record the Y evidence role and function-level interpretation clarity separately from the proposed mechanism and mechanism clarity; do not use mechanism ambiguity as the F gate.
9. Assess design-based E: assign `E-matched` if its positive requirements are met; otherwise record provisional `E-physical-only` or `E-uncontrolled`.
10. If evidence is not matched, inspect the full pattern only to test the frozen `E-diagnostic` criterion.
11. Finalize E and explain why.
12. Only now classify the empirical outcome and explain why.
13. Identify the critical aware/unaware comparison.
14. Record `unaware_Y_evidence` when relevant.
15. Record the structured null-evidence basis, `null_evidence_strength`, and `null_evidence_adequacy` when relevant.
16. Perform the statistical audit, including whether the critical difference was tested.
17. Apply the Meyen diagnostic when relevant.
18. Write a one- or two-sentence empirical-constraint statement.
19. Record page, figure, table, analysis, and auxiliary-source locations.

## 9. Discovery routes and stopping rules

The registered sweep combines all four routes below.

### 9.1 Empirical-seed citation graph

Begin with the frozen empirical seeds. A newly discovered full-text empirical paper becomes a backward/forward citation-network node when at least one experiment contains all of:

1. a specific X;
2. a genuine aware/unaware contrast concerning X, or a substantive attempt to establish one; and
3. a distinct plausible downstream Y coded `F-meaningful` or `F-ambiguous`.

For discovery expansion only, a **substantive attempt** at an awareness contrast is a manipulation, grouping, or subjective measurement explicitly intended to distinguish awareness versus unawareness of the relevant X, even if the resulting evidence is too weak to satisfy `A-direct` or `A-validated`. This keeps borderline papers available as discovery nodes; it does not weaken the empirical-lot criteria.

Weak A or E does not prevent expansion. Papers containing only generic registration or priming coded `F-not-meaningful` do not automatically seed recursive expansion. For unavailable full texts, an `ask-text-high` paper may act provisionally as a node only when its abstract explicitly supports the same X + awareness contrast + distinct plausible Y structure. Review and discovery anchors are expanded separately under their own route. Record every expansion decision and why.

Stop citation expansion when a complete backward-and-forward citation wave yields zero new potentially relevant papers after deduplication and title/abstract screening.

Scientific eligibility and discovery usefulness are distinct. A weak study may remain a useful citation-network node.

### 9.2 Review and discovery anchors

Use a frozen broad set of review, theory, method, and other discovery-anchor papers to index partially disconnected areas, spanning at least unconscious processing, functions of consciousness, theory criteria, attention and control, metacognition, theory landscapes, and visual consciousness. These anchors are discovery sources, not automatically X → Y experiments. Screen cited empirical work through the normal funnel.

### 9.3 Independent query search

Before the registered run, freeze source-specific query families as a supplementary recall check against citation-network blind spots. This lane complements, rather than replaces, the empirical-seed graph, review/discovery anchors, and process-triggered searches. Use several conceptually motivated families that separately cross awareness terminology with broad downstream-use classes, including attention/control/inhibition/distractor control; metacognition/confidence/monitoring/error evaluation; binding/integration/object or event updating; memory/maintenance/working memory; decision/action/rule-guided or flexible use; and learning/adaptation. Unknown Y remains discoverable through review, citation, and process-trigger routes. Do not rely on relevance ranking from one multimillion-record monolithic query as the main instrument.

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

A genuinely new Y found in this lane may trigger another Y-specific search only if it independently satisfies the same activation conditions. Each normalized Y label may activate this route once per run; label normalization decisions and reasons must be logged.

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
- Each `experiments_master.csv` row is one paper × experiment × X→Y comparison, identified by `comparison_id`.
- Clean qualifying files are deterministic comparison-level views of master records, never independently classified datasets.

Operational paths, event-to-file mappings, identifiers, validation checkpoints, and completion requirements are defined in `AGENTS.md`.
