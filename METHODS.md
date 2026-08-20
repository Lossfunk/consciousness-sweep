# Planned methods for the consciousness X→Y literature sweep

**Document status:** derived human-readable description of protocol `draft-0.8.6`, package `prefreeze-package-0.8.6`, schema `prefreeze-schema-0.8.5`. The package is pre-freeze and not preregistered. `PROTOCOL.md` remains the scientific/procedural authority and `AGENTS.md` the execution authority; this document creates no rule.

<a id="methods-01"></a>
## 1. Aim and scope

The review asks, for a particular content or entity X and a cognitive process Y, whether awareness of X changes whether, or how well, Y can use X. The review is result-neutral. It can retain evidence that Y operates when X is unaware, that awareness changes Y, that a direct difference was not detected, that equivalence is positively supported, or that the available evidence does not resolve one or both questions. A study is informative because its design bears on X→Y, not because it favors an awareness benefit.

The scientific analysis is deliberately comparison-specific. Awareness evidence, first-order evidence, the meaning of Y, capacity under unawareness, and the effect of awareness can differ across experiments or across distinct functions within one experiment. These judgments are therefore not assigned as paper-wide labels.

**Authority:** PROTOCOL §1 “Aim and scope”; AGENTS §1 “Authority split”.

<a id="methods-02"></a>
## 2. Units of representation

### 2.1 Logical papers

A logical paper is the deduplicated bibliographic work represented in `papers_master.csv`. Every encounter with it remains separately recorded in `discoveries.csv`; first-discovery fields in the master record never replace that history. A preprint and a published article are treated as one logical work only when authorship, title/content, and an explicit version relationship make that link sufficiently clear.

### 2.2 Physical experiment groups

A physical experiment is a first-class object in `experiment_groups.csv`. Every enumerated experiment receives an experiment identifier before comparisons are allocated, including experiments that become support-only or yield no qualifying comparison. Its record describes the physical experiment, source location, pre-atomization assessment, disposition, linked comparisons, and any support roles.

### 2.3 Paper × experiment × X→Y comparisons

The atomic scientific unit is one paper × physical experiment × X→Y comparison, stored in `experiments_master.csv`. A comparison represents one conservative functional mapping from X to Y and has a unique comparison identifier. An experiment identifier may repeat across multiple comparison rows. The retained filename reflects historical continuity; its rows are comparisons, not whole experiments.

### 2.4 Support-only experiments

A support-only experiment can provide awareness validation, first-order-evidence control, statistical support, or another premise for a focal comparison. It retains a physical-experiment record and may be a direct evidence-link source, but it receives no placeholder comparison unless it independently answers an eligible X→Y question. The same zero-comparison rule applies to an experiment with no qualifying comparison.

### 2.5 Identifiers and provenance

Stable identifiers are assigned as `P000001` (paper), `P000001_E01` (physical experiment), `P000001_E01_C01` (comparison), and `<RUN_ID>_D/S/R/AUX/EL/EB/EA/FT` plus six digits for decisions, searches, encounters, auxiliary sources, evidence links, evidence bundles, factual assessments, and full-text assets. Allocation is locked and durably advances state before returning an identifier. A crash may retire an unused identifier, but no identifier is recycled or renumbered. Parent records are written before their identifiers are referenced.

**Authority:** PROTOCOL §1; PROTOCOL §2.5–2.6; AGENTS §2, §5–7.

<a id="methods-03"></a>
## 3. Overview of the workflow

Each independent run initializes the fixed empirical seeds and review/discovery anchors, screens the principal candidate literature, expands eligible citation nodes in bounded waves, retrieves and evaluates full texts, and activates process searches only for independently earned downstream functions. Once every principal frontier is provisionally satisfied, the run executes every mandatory supplementary blind window. New eligible nodes from that lane reopen the relevant citation or process frontier. The run ends only after all reopened work, missing-text state, scientific dependencies, derived outputs, and validation conditions are complete.

At full text, physical experiments are enumerated first. Each experiment undergoes a pre-atomization functional-structure assessment; comparison rows are then formed and audited in the scientific order A, F, provisional E, the bounded E-diagnostic test when applicable, and final E. Route viability is assessed before results are interpreted. Capacity and awareness-effect conclusions are kept independent, with null/equivalence and Meyen audits applied where appropriate.

Records are written continuously rather than reconstructed at the end. Every checkpoint regenerates deterministic views, validates the full run, updates state and summary information, and prepares a bounded missing-text request batch.

**Authority:** PROTOCOL §8–10; AGENTS §4, §6–8, §11–12.

<a id="methods-04"></a>
## 4. Literature discovery

### 4.1 Empirical seeds

The fixed empirical seed list supplies guaranteed candidate-lot entries and the initial citation graph. Seeds are not presumed eligible or assigned expected outcomes. Eligible empirical seeds are expanded both backward and forward.

### 4.2 Review and discovery anchors

The fixed review list supplies broad discovery anchors rather than presumed X→Y experiments. It spans at least unconscious processing, functions of consciousness, theory criteria and landscapes, attention/control, metacognition, and visual consciousness. Relevant candidate works named in these sources enter ordinary screening with their provenance recorded.

### 4.3–4.4 Backward and forward citation expansion

Backward reference and forward-citation events are separately logged with their parent paper and source. A full-text empirical paper becomes a citation node when at least one experiment has a specific X, a genuine awareness contrast or substantive attempt to establish one, and a distinct plausible Y coded `F-meaningful` or `F-ambiguous`. For discovery only, a substantive attempt can be an intended awareness manipulation, grouping, or subjective measurement even when A is ultimately weak. `F-not-meaningful` registration/priming papers do not automatically seed recursion. An `ask-text-high` paper without full text may act provisionally as a node only when its abstract explicitly supports the same X + awareness contrast + distinct plausible Y structure. Eligible nodes are expanded in waves, with weak A or E not preventing expansion.

Full-text empirical papers that narrowly miss CORE eligibility may receive one citation hop when a single physical experiment clearly contains exactly two of the three CORE ingredients and explicitly fails the third. The experiment must be a genuine near-neighbor with a positive rationale; unclear ingredients, cross-experiment aggregation, missing text, and review/theory/methods-only hubs do not qualify. CORE takes precedence at paper level. Consecutive bridge traversal is not allowed: a bridge reached from a bridge is screened but cannot continue that lineage, while encountering CORE resets bridge depth. A later independent depth-0 encounter can enable a bridge that was first found at depth 1, and identical completed citation windows are reused. Bridge status changes citation discovery only; it does not alter comparison eligibility, A/E/F, results, evidence requirements, or QDYN activation.

### 4.5 Process-triggered expansion

A process search is activated only after a comparison independently earns the protocol’s qualifying A/E/F conditions for a normalized Y. It searches that observed process, not a broad neighboring topic. The closed lexical universe comprises the canonical Y, its direct morphology/grammar/spelling variants, same-function terminology explicitly used in the source paper, and at most one frozen immediate-parent functional term. Every term carries a provenance category and rationale. Unrestricted model-generated synonyms are prohibited.

For each activated normalized Y, the current conservative contract uses OpenAlex and Europe PMC, one initial title/abstract window per source, and at most 50 records per source. The same normalized Y/source window is not retriggered, unused quota is not reallocated, and recursion occurs only when a genuinely new Y independently qualifies. In this lane, only `screen-in` proceeds automatically; `screen-uncertain` remains auditable unless independently rediscovered or manually promoted.

### 4.6–4.7 Supplementary blind-spot lane and active QCAL windows

Independent database queries form a mandatory supplementary recall check, not the primary recall engine or a universal enumeration of Y. The current conservative candidate activates five QCAL4 families: ATTN (attention/control), META (metacognition/monitoring), BIND (binding/integration), MEM (memory operations), and DEC (action/rule-guided use). Each is rendered separately for OpenAlex and Europe PMC in title/abstract fields, with one initial window of at most 40 records for each source/family pair. No second page or cursor is requested, unused quota is not redistributed, and every returned record is screened.

### 4.8 Learning/adaptation query status

Learning and adaptation remain scientifically eligible through seeds, anchors, citation expansion, and earned process searches. The generic QCAL4-LEARN blind block is disabled/retired pre-freeze because its tested rendering was pathological. Before registration, humans must either redesign that generic block or explicitly decide that the registered blind lane will omit it. It must not be silently reactivated or deleted.

### 4.9 Principal-first, blind-last ordering

Seeds, anchors, citation expansion, full-text work, and activated process searches form the principal route. The blind lane begins only after all principal frontiers are durably marked provisionally satisfied. Its late position does not make it optional.

### 4.10 Frontier reopening

A blind-discovered CORE node or strict bridge at eligible depth 0 reopens the citation frontier. A genuinely new, independently qualifying normalized Y activates or reopens its process frontier. The unchanged bounded rules then apply recursively.

### 4.11–4.13 Stopping and mandatory completion

Citation expansion stops only when a complete backward-and-forward wave yields zero new potentially relevant papers after deduplication and title/abstract screening and no required one-hop bridge expansion remains pending. A process search stops after both frozen source windows for that Y are complete and its resulting eligible nodes and consequences have been handled. The blind lane is complete only when every frozen source/family window exists as a hash-consistent durable snapshot. The overall search cannot complete while any principal, bridge, blind-triggered citation, or process frontier remains open or reopened. K=1 and the strict parent rule are the prospective resource control; runtime or yield does not create an extra stopping rule.

**Authority:** PROTOCOL §9.1–9.4; AGENTS §8 and §12; `config.yaml` `search.conservative_execution`; `queries.md` active QCAL4 and QDYN001 specifications.

<a id="methods-05"></a>
## 5. Search-source execution and immutable snapshots

Each query is rendered for its source-specific interface and field syntax. Its frozen specification must state sort/ranking, page size, whether every return is screened, exact page/record maximum when nonexhaustive, and behavior for ties, source reordering, cursor failure/API truncation, and cross-block deduplication. A query window is identified by execution phase, source, query family or normalized Y, canonical query, source parameters, publication cutoff, requested maximum N, and a deterministic key. Its logged record also stores ranking/order assumptions, actual return count, retrieval time, ordered result-set hash, status, and any reused search identifier.

A completed query or backward/forward citation window is an immutable retrieval snapshot. Citation windows additionally identify their parent, direction, node basis, and bridge-lineage depth, and bridge windows inherit whatever ordinary citation source/fallback policy is later frozen. Resume may reuse a window only when the entire key and the ordered hash agree with durable discovery records. It may not silently rerun, extend, rerank, or substitute a completed window. Failed, partial, missing, or internally inconsistent windows remain incomplete and require explicit resolution. Every encountered result receives a discovery row, including duplicates and rediscoveries; a reused completed window does not create a second set of encounters.

The current source-specific QCAL and process renderers are locally validated for balanced syntax, supported fields, prohibited generic bare terms, and lexical provenance before any source call. The final preferred source order, fallback order, and publication-cutoff handling are not yet frozen; see §33.

**Authority:** PROTOCOL §9.3–9.4; AGENTS §8; `queries.md`; `config.yaml`; `tools/query_instruments.py`; `tools/execution_contract.py` search-window helpers.

<a id="methods-06"></a>
## 6. Bibliographic identity and logical-paper deduplication

DOIs are percent-decoded, stripped of resolver or `doi:` prefixes, trimmed, and lowercased. Identical nonempty normalized DOIs identify the same work unless clear contrary evidence is recorded. Without a DOI, normalized title, year, and consistently normalized author strings are compared without guessing identities. Uncertain matches remain separate and are marked possible duplicates. Confirmed duplicates point to the retained paper, while their discovery and decision history is preserved.

Before a proposed bibliographic batch is persisted, its DOI and URL fields undergo a nonmutating normalization dry run. Rejected or unsafe values are resolved before IDs are allocated. Resolver URLs are constructed from safely encoded normalized DOIs. Every merge or duplicate judgment requires a reason and decision-log event.

**Authority:** AGENTS §8; `tools/structured_write.py` normalization and write contract.

<a id="methods-07"></a>
## 7. Paper screening

### 7.1 Title screening

Title screening is biased toward recall. It retains records that could plausibly contain an eligible awareness-of-X by downstream-use-Y design and excludes only when irrelevance is clear. Every decision receives a paper-specific reason.

### 7.2 Abstract screening

Abstract screening assigns `screen-in`, `screen-uncertain`, or `screen-out` under the protocol’s scientific scope. `screen-in` means that X, an awareness contrast concerning X, and a distinct downstream Y are plausible; unknown A or E details do not justify exclusion. An abstract can prioritize retrieval but cannot support final comparison classification, which requires full text. `screen-out` leaves full-text priority unassigned.

### 7.3 Unavailable abstracts

When an abstract cannot reasonably be obtained for a title-retained paper, its status is recorded as unavailable and its abstract screen remains not-screened with a reason. It is not converted to screen-out. Full-text priority is assigned from title, provenance, and metadata.

### 7.4 Full-text priority

Screen-in, uncertain, and abstract-unavailable records receive a reasoned high, medium, or low priority. Missing texts are later queued by protocol priority and stable paper ID.

### 7.5–7.6 Semantic batching and prohibited exclusions

Title batches contain at most 25 logical papers and abstract batches at most 10. Smaller batches are allowed. Batching provides context efficiency only: each work is screened individually and receives its own decision and reason. Existing decisions may be reused only for the same logical work, unchanged decision-relevant evidence, and the same scientific-regime fingerprint. Genuinely new evidence permits revision only through append-first history. No regex, keyword, embedding, citation count, numeric relevance score, or hidden lexical heuristic may independently produce exclusion; the current draft registers no deterministic scientific exclusion rule.

**Authority:** PROTOCOL §6.1–6.2; AGENTS §8, §9.1–9.2; `config.yaml` `execution`.

<a id="methods-08"></a>
## 8. Full-text acquisition

The retrieval cascade seeks a published full text, then an accepted/repository version, and then a preprint when permitted. Final comparison classification requires full text. Each verified article version receives a full-text asset record containing source identity, local path, immutable file hash, verification reason, acquisition route, and—when extraction is created—tool/version, extracted-text hash, and page-map hash.

The same verified version and compatible extraction are reused across comparisons within a paper. A materially different article version receives a new immutable asset rather than overwriting the old one; at most one version is current for the paper. Retrieval state and hashes are validated against the filesystem.

If text remains unavailable, the request enters `missing_texts.csv` with attempted sources, priority, reason, current status, and request wave. At checkpoints, unresolved requests are ordered by protocol priority and stable paper ID, and no more than the configured batch of ten is surfaced. A user-supplied text is recorded with its actual acquisition time, wave, route, and `obtained_by=user`; availability is never backdated. Newly obtained text may reopen citation or process work that it activates.

**Authority:** PROTOCOL §7; AGENTS §9 and §9.6; `config.yaml` `fulltext` and `fulltext_cache`.

<a id="methods-09"></a>
## 9. Physical experiment enumeration

Full-text evaluation begins by enumerating every physical experiment group in the article. Each group is persisted before any child comparison is allocated. It is described and assigned one of three final dispositions after its structural audit: comparison-bearing, support-only, or no qualifying comparison. Comparison-bearing groups list exactly their scientific comparison rows. The other two dispositions list none, preventing dummy comparisons while retaining the experiment as auditable evidence or a documented negative structural decision.

Physical experiments and comparison rows answer different questions. The group establishes what was physically conducted; the comparison establishes which X→Y scientific question is being evaluated. A group may support many premises or contain several comparisons without being reducible to any single one of them.

**Authority:** PROTOCOL §1 and §2.5; AGENTS §2, §5, §7; `schemas/experiment_groups.schema.json`.

<a id="methods-10"></a>
## 10. Pre-atomization functional-structure assessment

Before final comparison decomposition, the reviewer asks whether multiple cells, factors, or simple effects implement the same operational input→output mapping. The assessment considers whether they use the same information X, target the same downstream output and task stage, vary X’s relation to that output, form a meaningful higher-order mapping, and admit one conservative common function. Conventional effect names, signs, neural mechanisms, or authors’ labels do not settle functional identity.

When the experiment requires a coherent factorial-functional relation, its focal comparison is instantiated before optional scalar components. The focal row records the joint structured mapping and at least two component effects with source locations. Any retained component row links back to that focal comparison. A component may be a separate comparison only when it independently answers a distinct X→Y question.

Scalar separation requires a positive reason such as distinct downstream outputs, computational stages, input–output relations, or the absence of a conservative common function. Conversely, distinct mechanism proposals do not force separation when the measured function is common. This prevents both destructive atomization of a critical interaction and forced merging of genuinely different functions.

**Authority:** PROTOCOL §2.5–2.6; AGENTS §7; `tools/execution_contract.py` functional-structure checks.

<a id="methods-11"></a>
## 11. Defining X and Y

X is the specific content/entity whose awareness varies. Y is assigned at the most specific downstream functional level justified by the dependent measure, while remaining conservative. It names an operation, use, or coherent mapping from X to an output—for example regulation of distractor influence—not merely an interference score, response-time change, priming effect, correlation, or neural amplitude.

Each comparison separately records the Y label and description, the evidence role of the dependent measure, functional status, interpretation clarity, proposed mechanism, and mechanism clarity. A behavioral measure may establish a clear function while leaving its neural or cognitive mechanism ambiguous. Generic neural activity can support a proposed mechanism but is not itself a qualifying Y unless it operationalizes a downstream function.

The `Y_functional_status` audit distinguishes a downstream function, coherent functional mapping, effect-only description, unclear function, and not-assessed state. `F-meaningful` requires one of the first two. Functional ambiguity concerns what Y does; mechanism ambiguity concerns how Y is implemented.

**Authority:** PROTOCOL §2.4–2.6; AGENTS §7 and §10; `schemas/experiments.schema.json`.

<a id="methods-12"></a>
## 12. Awareness evidence (A)

Awareness is coded independently from E and F. `A-direct` requires qualifying subjective or objective-invisibility evidence in the focal experiment, trial, block, condition, or stimulus regime. `A-validated` uses qualifying evidence from a separate validation whose stimulus, suppression/masking, timing, attention, task demands, and population plausibly transfer. `A-transfer-risk` records a materially uncertain validation or sensitivity transfer. `A-absent` records that no qualifying awareness evidence supports the classification; masking, condition labels, neural activity, or an insensitive test alone do not qualify.

The evidence type is recorded orthogonally as subjective, objective-invisibility, mixed, or none. An objective invisibility result can support strong A only when the task directly tests perceptual access to focal X, has a meaningful chance/no-access baseline, is sufficiently sensitive, and the result supports performance at or sufficiently near that baseline. Legacy work is not required to use a modern equivalence test or Bayes factor, but an obviously underpowered nonsignificant chance comparison is insufficient. The informativeness judgment and reason are explicit. Above-chance objective performance does not automatically negate an independent subjective-unawareness measure; it primarily informs E.

A procedure is not a result. The focal row separately records whether the critical awareness result was reported and whether it supports strong A, along with procedure type, description, exact location, and source experiment. `A-direct` always requires a reported supportive focal result. `A-validated` also requires such a focal result unless a separate complete `awareness-A` bundle supplies a required, result-bearing validation member. A Methods-only procedure, missing critical values, missing source location, or procedure/result mismatch cannot support strong A.

Transferred A never masquerades as focal reporting. Its bundle must identify the actual experiment or source, result, location, transfer reason, limitations, regime differences, and use in the decision. Sample, stimulus, timing, suppression, attention, task, environment, awareness procedure, and first-order-evidence regime are assessed rather than inherited automatically. If a required result cannot be obtained, the bundle remains incomplete unless distinct adequate support independently completes the premise.

**Authority:** PROTOCOL §2.1; AGENTS §6–7 and §9.4; `schemas/experiments.schema.json`; `tools/execution_contract.py` awareness-result checks.

<a id="methods-13"></a>
## 13. First-order evidence (E)

E concerns internal first-order evidence about X, not physical stimulus identity alone. `E-matched` requires either active design matching/titration on the relevant direct first-order measure or a successful explicit equivalence procedure with a stated margin. A nonsignificant difference or narrow-looking interval without a stated criterion does not establish matching.

`E-diagnostic` is an alternative strong route for unmatched designs when a structured same-Y result rules out the relevant simple scalar account in which more evidence about X merely strengthens the same downstream relation. `E-physical-only` applies when physical X is nominally identical but relevant internal evidence is unequal or inadequately assessed. `E-uncontrolled` applies otherwise when evidence differs, is unknown, or is inadequately controlled.

E is assessed design-first. Reviewers first decide whether positive matching requirements are met. If not, they record the applicable provisional weaker category and then apply the bounded E-diagnostic analysis to every eligible unmatched case before finalizing E. Only that frozen diagnostic use of results is permitted before capacity and awareness-effect outcomes are classified.

**Authority:** PROTOCOL §2.2–2.3; AGENTS §7.

<a id="methods-14"></a>
## 14. E-diagnostic inference

An E-diagnostic claim states the competing simple evidence-strength account, its prediction for the same focal Y, the observed pattern that violates that prediction, every required experiment/analysis and source pointer, and why the evidence concerns one coherent Y rather than an opportunistic cross-Y dissociation. Potential structures include threshold-linked nonmonotonicity, an experimentally shifted threshold with a shifted downstream effect, crossover/sign reversal, or a coherent factorial/process-selective interaction. An interaction by itself is insufficient.

The comparison also undergoes a bounded contrast-integrity check. A task-state alternative may gate E only when it is finite, explicitly named, capable of changing the same Y, associated with an observable prediction/control, independently motivated by the design, and anchored by a design-imposed or directly measured difference, reported behavior, manipulation check/control, or similarly direct evidence. Instructions, learned contingency, explicit task-relation knowledge, response mapping, policy, attention/control set, task relevance, feedback/training, and block strategy are candidate variables when so anchored. Merely possible endogenous attention, arousal, motivation, stronger-evidence engagement, or executive-control differences may be limitations but cannot veto E-diagnostic without an anchor.

Each admissible alternative receives its own E bundle when necessary, including the anchor, prediction, required direct control member, and resolution. Any viable unresolved alternative prohibits E-diagnostic. When no separate design-motivated task state exists and task configuration, mappings, instructions, and policy are held fixed, the contrast-integrity disposition is not-applicable; unequal sensory evidence alone is the ordinary E problem.

Before any unmatched E category is finalized, the whole supplied article record is semantically scanned for another experiment, analysis, supplement, or explicit control aimed at the focal first-order-evidence alternative. The scan status and reason are recorded. Candidate controls must address the same conservative Y, undergo transfer assessment, and be linked through a required bundle when classification-critical. An unavailable critical control leaves the dependency incomplete and prevents final E. Cross-experiment E support is permitted, but cannot create a focal aware/unaware difference statistic.

For factorial-functional Y, the inference applies to the whole mapping. A complete bundle must contain a required, decision-used member that directly addresses the first-order alternative and is verified as same-Y; component strength differences or a cross-Y dissociation do not suffice.

**Authority:** PROTOCOL §2.3 and §2.6; AGENTS §7 and §9.4; `schemas/evidence_bundles.schema.json`; `tools/execution_contract.py` E-diagnostic and contrast-integrity checks.

<a id="methods-15"></a>
## 15. Meaningful downstream use (F)

`F-meaningful` is an eligibility gate for a defensible distinct downstream function or coherent mapping, such as regulation/control, metacognitive evaluation, updating, binding, maintenance/memory, action selection, rule-guided use, or adaptation. It does not require identification of the exact mechanism. `F-ambiguous` retains plausible downstream transformation for which no conservative function can be chosen without selecting among substantively different uses. `F-not-meaningful` covers direct detection/discrimination, generic registration, a generic neural response, or generic priming whose principal implication is merely that information survived.

The judgment follows the operational input→output relation, not lexical labels. An observed nonzero effect does not automatically establish a capacity. Mechanism ambiguity is recorded separately and never gates F. `F-ambiguous` helps preserve discovery recall but does not pass the strongest derived design or constraint-ready routes.

**Authority:** PROTOCOL §2.4; AGENTS §7 and §10; `schemas/experiments.schema.json`.

<a id="methods-16"></a>
## 16. Scientific evidence bundles

A scientific bundle is an explicit argument for one named premise of one focal comparison; it is not an execution cache. The bundle declares every logically required member before the result is relied upon. Each direct link has a unique bundle-local key and names its source, supported claim, source location, evidence type, role, dependency role, status, transfer reason, limitation, same-Y status where relevant, and whether it was used for the decision.

Required members establish the premise. Strengthening, robustness, generalization, mechanistic, and other nonrequired members retain their distinct roles and cannot substitute for a missing required member. Support may come from the same experiment, another experiment in the paper, a supplement, or a reusable auxiliary source. A support-only experiment can therefore contribute directly without receiving a comparison row.

Bundle status is derived. It is `conflicted` if any direct member contradicts or is conflicted; otherwise `incomplete` if any required member is missing, duplicated, unavailable, unevaluated, transfer-invalid, not required in role, not supportive, or not decision-used; otherwise `complete` when at least one decision-used member supports the premise and every required member supports it. No scientific conclusion may depend on an incomplete or conflicted bundle.

Transfer is premise-specific and addresses population, manipulation, measure, analysis, and version compatibility as relevant. Links are direct and non-transitive: sharing a paper, assessment, or bundle does not transmit a conclusion to another premise or comparison. Reusing a verified factual assessment or full-text extraction saves execution work only; the target comparison still requires its own scientific judgment and links.

**Authority:** PROTOCOL §7.1–7.2; AGENTS §9.3–9.6; `schemas/evidence_bundles.schema.json`; `schemas/evidence_links.schema.json`.

<a id="methods-17"></a>
## 17. Route-aware comparison evaluation

After structural auditing and final A/E/F coding, the reviewer records viability separately for the awareness-effect, unaware-capacity, and null/equivalence routes. Strong A plus meaningful F makes the capacity route viable regardless of E. Strong A, strong E, and meaningful F make the constraint-ready awareness-effect route viable. A null/equivalence audit is required when a direct null-oriented result is at issue.

Dead-route short-circuiting avoids scientifically meaningless result interpretation; it does not exclude the paper or erase observations. Any viable route must be inspected. In addition, whenever the focal experiment directly tests aware versus unaware performance on the same Y, the direct result is descriptively audited even if weak E prevents a strong awareness interpretation. This separates design eligibility from factual reporting. Every completed comparison ends with a concise empirical-constraint statement that keeps capacity and awareness-effect conclusions distinct and points to the supporting pages, figures/tables, analyses, bundles, links, or assets.

**Authority:** PROTOCOL §8; AGENTS §7 and §10; `tools/execution_contract.py` route audit.

<a id="methods-18"></a>
## 18. Unaware-capacity inference

This axis asks whether X supports the exact focal downstream Y under the unaware condition. The stored capacity claim must exactly equal `Y_label`; one comparison therefore has one capacity target. A component of a factorial parent requires its own comparison if a component-specific capacity claim is to be made.

Supported capacity requires strong A, `F-meaningful`, an audited downstream function/coherent mapping, positive evidence for the entire focal Y, adequate route-specific statistics, and the inference-critical Meyen gate when applicable. For a factorial-functional comparison, one positive component does not establish the whole mapping. E is not a gate: weak or uncontrolled evidence may prevent a strong claim about what awareness changes while leaving a properly supported capacity-under-unawareness claim open.

Capacity, not-supported, unclear, and not-tested states each receive a reason and the critical effect/statistical disposition where applicable. A nonzero modulation of some other consequence is not evidence for the named capacity.

**Authority:** PROTOCOL §3.1; AGENTS §7 and §10 “Constraint-ready unaware capacity”.

<a id="methods-19"></a>
## 19. Awareness-linked-difference inference

The strongest awareness-linked-difference route requires `A-direct` or `A-validated`, `E-matched` or `E-diagnostic`, and `F-meaningful`. It further requires a direct aware/unaware difference or interaction on the same focal Y, an interpretable effect estimate, adequate route-specific statistics, and any inference-critical Meyen condition.

The difference must belong to the focal physical experiment. Its source experiment identifier must equal the comparison’s experiment identifier, and its location and statistic/test must be recorded. Cross-experiment evidence may strengthen or establish an E premise through a bundle, but it cannot fabricate a direct focal difference. Direction is recorded without treating aware superiority as the only informative outcome.

**Authority:** PROTOCOL §3.2 and §4.1; AGENTS §7 and §10 “Constraint-ready awareness-linked difference”.

<a id="methods-20"></a>
## 20. Direct descriptive awareness comparisons

`difference_tested` records whether the focal experiment tested aware versus unaware conditions on the same Y, independently of E strength. A claimed direct test requires its focal experiment, exact source location, test/statistic, critical effect, interpretable estimate, and statistical audit.

When A or F is weak, or E remains physical-only/uncontrolled, a significant direct test is still reported but cannot be promoted to a constraint-ready awareness-effect conclusion. Its awareness interpretation remains unresolved as appropriate. This preserves the empirical comparison while distinguishing descriptive evidence from evidence that isolates awareness.

**Authority:** PROTOCOL §3.2 and §8; AGENTS §7; `schemas/experiments.schema.json`; `tools/execution_contract.py` route checks.

<a id="methods-21"></a>
## 21. No-detectable awareness differences

This descriptive category requires a direct same-Y aware/unaware test and an interpretable estimate. It records that the analysis did not detect a difference; it does not state that the conditions are equivalent. Precision, robustness, design limitations, and any sensitivity concerns remain visible. A bare `p > .05` cannot support a stronger invariance claim.

All fully evaluated comparisons assigned this category enter the deterministic no-detectable view, even when strong E is absent. This preserves the descriptive result without upgrading its causal interpretation.

**Authority:** PROTOCOL §3.2 and §4.2; AGENTS §10.

<a id="methods-22"></a>
## 22. Equivalence-supported no difference

Equivalence is a positive evidential claim and is separate from no detectable difference. Adequate null evidence must come from a successful equivalence test with a stated meaningful margin, a Bayes factor favoring the null with `BF01 ≥ 3`, or a confidence/credible interval lying wholly within a stated equivalence region. A margin or region is never invented retrospectively from the observed interval.

The strongest equivalence-supported invariance set also requires strong A/E/F, a direct focal same-Y test, adequate route statistics, supported capacity for the exact whole focal Y, and any inference-critical Meyen condition. Comparisons lacking those gates may still have their direct null evidence described but do not enter this strongest derived set.

**Authority:** PROTOCOL §4.2; AGENTS §10 “Strongest equivalence-supported invariance”; `schemas/experiments.schema.json`.

<a id="methods-23"></a>
## 23. Statistical audit

The audit identifies the exact critical effect for each route and records the reported statistic, estimate, uncertainty, and whether the inference is adequate, concerning, or unclear. A difference between significant and nonsignificant effects is not accepted as evidence that the effects differ. Reviewers examine exclusions, multiple comparisons, model appropriateness, independence/pseudoreplication, exploratory status of critical analyses, selective reporting, and the robustness of the effect.

Capacity and awareness-effect statistics are recorded separately because one route may be adequate while the other is not. Null-oriented results receive the dedicated evidence-strength and adequacy fields described above. Every concern or unclear judgment carries a reason; absence of reported information remains uncertainty rather than being repaired by assumption.

**Authority:** PROTOCOL §4.1–4.3; AGENTS §6–7 and §10.

<a id="methods-24"></a>
## 24. Meyen diagnostic

The Meyen diagnostic assesses whether a claimed indirect effect is more sensitive to X than the direct awareness task in the relevant regime. Its role is labeled `inference-critical` when the argument depends on the direct/indirect sensitivity relation, `supplementary` when informative but not gating, or `not-applicable` when the diagnostic does not bear on the inference.

When inference-critical, the relevant derived route requires `Meyen-satisfied`; failure or unassessability blocks that constraint-ready inference. A supplementary result remains recorded and visible but does not gate. Objective invisibility does not automatically make the diagnostic supplementary: a dedicated, sufficiently informative validation and its transfer must independently justify that role. Passing the diagnostic does not itself prove unconscious processing or replace A. Every role and status receives a reason.

**Authority:** PROTOCOL §5; AGENTS §10.

<a id="methods-25"></a>
## 25. Classification-critical auxiliary evidence

An external logical work used only to support a classification is recorded once in `auxiliary_sources.csv`, with bibliographic identity, article version, retrieval status, source, local file/hash when obtained, and verification reason. Each scientific use is then linked from a premise-specific bundle with an explicit transfer judgment and limitation.

Consulting an auxiliary source does not automatically add it to the candidate pool or discovery graph. It enters those tables only if independently encountered through an ordinary discovery event. If required auxiliary text cannot be retrieved, the member remains unavailable and its bundle incomplete; the dependent conclusion cannot be asserted.

**Authority:** PROTOCOL §7.1–7.2; AGENTS §9.3–9.4; `schemas/auxiliary_sources.schema.json`.

<a id="methods-26"></a>
## 26. Derived scientific evidence sets

Derived files are regenerated mechanically from `experiments_master.csv`, sorted by paper, experiment, and comparison identifiers; they are not independently classified. The design-eligible awareness-effect view contains strong A, strong E, and meaningful F. The constraint-ready awareness-linked-difference view adds a supported direct focal difference, adequate statistics, provenance, and the Meyen gate. The unaware-capacity view uses strong A, meaningful/audited F, exact whole-Y identity, supported capacity, adequate statistics, and the Meyen gate, without an E requirement.

The no-detectable view contains every fully evaluated descriptive no-difference comparison. The strongest equivalence-supported view adds positive equivalence evidence, supported exact-Y capacity, the strong A/E/F design gate, focal provenance, statistics, and Meyen. The unresolved view contains fully evaluated comparisons with unclear capacity or unresolved awareness effect. `constraint_ready_experiments.csv` is the deduplicated union of the awareness-difference, unaware-capacity, and equivalence routes.

Membership may overlap because the scientific claims are compatible rather than mutually exclusive. For example, a comparison can support unaware capacity and an awareness-linked difference, or capacity and equivalence-supported invariance.

**Authority:** PROTOCOL §3–5 and §12; AGENTS §10; `tools/derive_outputs.py`.

<a id="methods-27"></a>
## 27. Missing information and uncertainty

Missing target texts are tracked separately from screening decisions and surfaced in bounded priority batches. Missing critical auxiliary sources, unavailable within-paper controls, material A-transfer risk, incomplete or conflicted bundles, unclear statistics, uncertain duplicates, and unresolved comparison judgments retain explicit statuses and reasons. Missing information is never converted into a negative scientific finding.

A conclusion cannot depend on an incomplete or conflicted bundle. An unmatched comparison cannot be finalized when a classification-critical within-paper control is known but unavailable. Uncertainty remains visible in current state and append-only history so that a later obtained text or corrected fact can trigger an auditable revision.

**Authority:** PROTOCOL §2.1–2.3, §4.3, §7–8; AGENTS §6–9 and §12.

<a id="methods-28"></a>
## 28. Multi-agent execution

Independent registered runs share only immutable static package inputs: frozen seed and anchor identity, normalization rules, schemas, queries, protocol, and execution instructions. They do not share dynamic query results, paper-specific screening decisions, comparison decompositions, A/E/F codes, evidence assessments or links, statistical/Meyen judgments, process-Y or saturation judgments, full-text annotations, or run outputs.

Each run writes only within its own `runs/<RUN_ID>/` directory and may not inspect another run or write consolidated outputs. Stored paths are repository-relative unless their schema states otherwise. No dynamic result set is precomputed for distribution. Multiple workers inside one run may divide only already reserved, nonoverlapping units; all identifiers and writes pass through the run’s locked writer, and a coordinator reconciles durable state at checkpoints.

**Authority:** PROTOCOL §11; AGENTS §2, §5–6, §12.

<a id="methods-29"></a>
## 29. Audit trail

Master CSVs represent current state; `decision_log.jsonl` is append-only history. Every search/retrieval/citation event has a search row, and every result encounter has a discovery row. Separate tables preserve missing-text requests, auxiliary sources, verified full-text assets, factual execution assessments, scientific bundles and links, physical groups, and comparison judgments.

Every title, abstract state, retrieval, deduplication, structural choice, A/E/F decision, route result, statistic, Meyen judgment, uncertainty, revision, and state transition receives a short why. Before a current-state value changes, a decision event records field, old value, new value, reason, source location, timestamp, entity, and agent. Source locations may be empty only when none exists and the reason explains why.

Structured writes derive column order from schema, validate typed rows, apply CSV quoting, lock the run, and atomically replace the target. JSONL records are ASCII-safe and one physical LF-delimited object each. Full-text and extraction hashes, immutable input hashes, ordered search-result hashes, and stable IDs allow later reproduction and integrity checks.

**Authority:** PROTOCOL §12; AGENTS §5–8 and §11; `tools/structured_write.py`; `tools/validate_run.py`.

<a id="methods-30"></a>
## 30. Start, resume, checkpoints, and completion

A registered invocation supplies a filesystem-safe nonempty run ID, start/resume mode, and available harness/model metadata. The immutable inputs are `AGENTS.md`, `PROTOCOL.md`, both seed files, `queries.md`, `config.yaml`, `requirements.txt`, every schema, and every canonical tool. The canonical environment is built from `requirements.txt`; registered preflight parses immutable inputs, meta-validates schemas, checks version/category consistency, and refuses null or draft freeze fields.

Start requires that the run directory not exist and creates schema-derived headers, empty history and derived files, `fulltexts/`, a summary, and durable state. Resume requires the directory to exist, first checks exact protocol/package/schema compatibility, validates the historical run under its own unchanged package, verifies immutable hashes, recovers counters from durable IDs, appends a resume event, and continues from recorded state. It never recreates, truncates, or silently migrates. A completed run can reopen only for newly supplied requested full text or an explicitly logged continuation reason.

At each search-wave checkpoint, writes are flushed; derived outputs and the run validator execute; IDs, counters, references, schema conditions, bundles, assets, fingerprints, and hashes are checked; a bounded text-request batch is prepared; the summary and state are updated. Validation failures are resolved before another wave.

A run is complete only after the principal frontier was provisionally satisfied; every mandatory blind window is complete and hash-consistent; all reopened citation and process frontiers are again satisfied; all frozen routes and activated searches are done; retrievable and supplied texts are evaluated; missing-text state is current; no conclusion depends on an incomplete/conflicted bundle; structural, route, result, statistical, and Meyen audits are complete; derived files are current; validation passes; and the summary records stopping evidence. State is marked complete only then.

**Authority:** PROTOCOL §9–10; AGENTS §3–5, §11–12; `tools/bootstrap_env.py`; `tools/preflight.py`; `tools/init_run.py`; `tools/validate_run.py`.

<a id="methods-31"></a>
## 31. Cross-run consolidation and adjudication

Consolidation occurs only after independent compatible registered runs finish and is outside each executing agent’s write scope. The discovery union is compared while retaining provenance, and judgments are aligned at the comparison level rather than by whole-paper labels. Each original comparison structure, code, reason, and evidence trail remains preserved.

Disagreements are adjudicated by human source-based review under the frozen protocol. Adjudication is not majority voting and cannot retrospectively alter the frozen protocol. If the authorities are silent, the case remains unresolved with a reason rather than generating a new rule.

**Authority:** PROTOCOL §11; AGENTS §1, §2 and §12.

<a id="methods-32"></a>
## 32. Planned outputs and reporting

Every run contains the paper, experiment-group, comparison, search, discovery, missing-text, auxiliary-source, full-text, evidence-assessment, evidence-bundle, and evidence-link tables; append-only decisions; durable state; deterministic comparison views; a run summary; and a full-text directory. The summary reports wave and route progress, counts, unresolved cases, missing texts, validation outcome, and remaining stopping conditions.

The planned derived scientific views are `design_eligible_experiments.csv`, `awareness_linked_differences.csv`, `unaware_capacities.csv`, `no_detectable_awareness_differences.csv`, `equivalence_supported_no_difference.csv`, `unresolved_comparisons.csv`, and their deduplicated constraint-ready union. Output filenames retain “experiments” for continuity even though rows are comparisons. Cross-run consolidated outputs are not written by an executing run.

**Authority:** PROTOCOL §12; AGENTS §2, §10–12.

<a id="methods-33"></a>
## 33. Pre-freeze versus registered status

The scientific representation, A/E/F definitions, evidence-bundle model, route logic, conservative QCAL/QDYN bounds, principal-first/blind-last state machine, run isolation, provenance, and validation machinery described above are determined in the current candidate package. They remain draft rules until the package is frozen and registered, but this documentation does not alter them. The protocol’s pre-freeze process also calls for circulation to consciousness researchers, collection of suggested literatures, pilot coding on known examples, resolution of ambiguities, and joint freezing/versioning of protocol, seeds/anchors, queries, sources/fallbacks, cutoff, text-batch size, schemas, tools, and stopping rules. Query sentinels assess draft-instrument recall only: they are not inclusion judgments, cannot be embedded in query strings, and title lookups do not count as recovery; this draft sets no final recovery threshold.

### Pre-freeze items to finalize before registration

The following values are intentionally unresolved and registered preflight must continue to fail until they are resolved and versioned:

1. registration status remains `pre-freeze`, not frozen or registered;
2. the inclusive publication cutoff and its timezone/interpretation are null;
3. `search.preferred_sources` is empty;
4. `search.fallback_order` is empty;
5. `queries.md` still contains draft/to-freeze markers and historical draft instruments; and
6. the generic QCAL4-LEARN decision remains open: redesign the block or explicitly omit it from the registered blind lane.

The calibration-only source strategy currently describes OpenAlex as proposed primary broad discovery/identity/citation infrastructure, Europe PMC as a parallel metadata/full-text and conditional biomedical citation fallback, Crossref as DOI/bibliographic identity and publisher-deposited backward-reference fallback, and Semantic Scholar as optional. These are calibration conclusions, not frozen preferred/fallback fields. The conservative blind and process contracts presently name OpenAlex and Europe PMC, but that does not resolve the overall registered source order or unavailable-source behavior. `AGENTS.md` also retains a CALIB003-only historical exception: at most 12 newly discovered abstract screen-ins were selected for full text by priority, earliest durable discovery, then paper ID, without expected-outcome tie-breaking. That bounded sampling rule is not the registered sweep rule, under which every retrievable paper passing the full-text threshold is evaluated. No registered run may begin until humans settle the live freeze points, remove draft markers as appropriate, update versions/status, and pass registered preflight.

**Authority:** PROTOCOL §9.3.1 and §10; AGENTS §3–4; `config.yaml`; `queries.md` “Freeze checklist for queries”.
