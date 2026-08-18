# Draft Query Specification

**Status of every exact string below: DRAFT — TO FREEZE BEFORE REGISTERED RUN**

These query families are recall checks and discovery tools, not eligibility definitions. The principal recall instrument is empirical-seed citation expansion plus review/discovery anchors plus activated process-trigger searches. Independent database blocks are a supplementary blind-spot check, not a claim of complete enumeration; every record returned inside a frozen window must nevertheless be screened and audited. Interpret eligibility only under `PROTOCOL.md`. Before registration, adapt and freeze each exact string for every named search source, recording source-specific syntax, fields, limits, date handling, and fallback behavior. Do not execute these drafts during repository construction.

## Proposed CALIB004 compact independent-query lane (prepared, not executed)

These six blocks replace broad standalone process words with diagnostic phrases. Each crosses the same explicit awareness vocabulary with a small process-specific vocabulary. Neither source uses unqualified `task`, `performance`, `experiment`, `memory`, or `decision` as a process term. The canonical renderers are in `tools/query_instruments.py`.

Shared draft syntax-only instrumentation: OpenAlex `/works` with `filter=title_and_abstract.search`, `sort=relevance_score:desc`, `per_page=40`, page 1 only; Europe PMC `/search` with `TITLE_ABS`, default relevance, `pageSize=40`, initial cursor only, and `synonym=false`. Screen and audit all returned records. Across six families and two sources, the hard ceiling is 480 encounters.

### QCAL4-ATTN — attention/control

- OpenAlex: `filter=title_and_abstract.search:(awareness OR unaware OR conscious OR unconscious OR visibility OR visible OR invisible OR unseen OR subliminal OR nonconscious) AND ("attentional control" OR "inhibitory control" OR "distractor interference" OR "attentional capture")`
- Europe PMC: `(TITLE_ABS:awareness OR TITLE_ABS:unaware OR TITLE_ABS:conscious OR TITLE_ABS:unconscious OR TITLE_ABS:visibility OR TITLE_ABS:visible OR TITLE_ABS:invisible OR TITLE_ABS:unseen OR TITLE_ABS:subliminal OR TITLE_ABS:nonconscious) AND (TITLE_ABS:"attentional control" OR TITLE_ABS:"inhibitory control" OR TITLE_ABS:"distractor interference" OR TITLE_ABS:"attentional capture")`

### QCAL4-META — metacognition/monitoring

- OpenAlex: `filter=title_and_abstract.search:(awareness OR unaware OR conscious OR unconscious OR visibility OR visible OR invisible OR unseen OR subliminal OR nonconscious) AND ("metacognitive sensitivity" OR "confidence accuracy" OR "error monitoring" OR "metacognitive control")`
- Europe PMC: `(TITLE_ABS:awareness OR TITLE_ABS:unaware OR TITLE_ABS:conscious OR TITLE_ABS:unconscious OR TITLE_ABS:visibility OR TITLE_ABS:visible OR TITLE_ABS:invisible OR TITLE_ABS:unseen OR TITLE_ABS:subliminal OR TITLE_ABS:nonconscious) AND (TITLE_ABS:"metacognitive sensitivity" OR TITLE_ABS:"confidence accuracy" OR TITLE_ABS:"error monitoring" OR TITLE_ABS:"metacognitive control")`

### QCAL4-BIND — binding/integration

- OpenAlex: `filter=title_and_abstract.search:(awareness OR unaware OR conscious OR unconscious OR visibility OR visible OR invisible OR unseen OR subliminal OR nonconscious) AND ("feature binding" OR "object integration" OR "event integration" OR "object updating")`
- Europe PMC: `(TITLE_ABS:awareness OR TITLE_ABS:unaware OR TITLE_ABS:conscious OR TITLE_ABS:unconscious OR TITLE_ABS:visibility OR TITLE_ABS:visible OR TITLE_ABS:invisible OR TITLE_ABS:unseen OR TITLE_ABS:subliminal OR TITLE_ABS:nonconscious) AND (TITLE_ABS:"feature binding" OR TITLE_ABS:"object integration" OR TITLE_ABS:"event integration" OR TITLE_ABS:"object updating")`

### QCAL4-MEM — memory operations

- OpenAlex: `filter=title_and_abstract.search:(awareness OR unaware OR conscious OR unconscious OR visibility OR visible OR invisible OR unseen OR subliminal OR nonconscious) AND ("working memory maintenance" OR "working memory updating" OR "episodic encoding" OR "memory retrieval")`
- Europe PMC: `(TITLE_ABS:awareness OR TITLE_ABS:unaware OR TITLE_ABS:conscious OR TITLE_ABS:unconscious OR TITLE_ABS:visibility OR TITLE_ABS:visible OR TITLE_ABS:invisible OR TITLE_ABS:unseen OR TITLE_ABS:subliminal OR TITLE_ABS:nonconscious) AND (TITLE_ABS:"working memory maintenance" OR TITLE_ABS:"working memory updating" OR TITLE_ABS:"episodic encoding" OR TITLE_ABS:"memory retrieval")`

### QCAL4-DEC — action/rule-guided use

- OpenAlex: `filter=title_and_abstract.search:(awareness OR unaware OR conscious OR unconscious OR visibility OR visible OR invisible OR unseen OR subliminal OR nonconscious) AND ("action selection" OR "response selection" OR "rule-guided behavior" OR "rule-guided behaviour" OR "flexible control")`
- Europe PMC: `(TITLE_ABS:awareness OR TITLE_ABS:unaware OR TITLE_ABS:conscious OR TITLE_ABS:unconscious OR TITLE_ABS:visibility OR TITLE_ABS:visible OR TITLE_ABS:invisible OR TITLE_ABS:unseen OR TITLE_ABS:subliminal OR TITLE_ABS:nonconscious) AND (TITLE_ABS:"action selection" OR TITLE_ABS:"response selection" OR TITLE_ABS:"rule-guided behavior" OR TITLE_ABS:"rule-guided behaviour" OR TITLE_ABS:"flexible control")`

### QCAL4-LEARN — learning/adaptation

- OpenAlex: `filter=title_and_abstract.search:(awareness OR unaware OR conscious OR unconscious OR visibility OR visible OR invisible OR unseen OR subliminal OR nonconscious) AND ("error-based learning" OR "reinforcement learning" OR "evaluative conditioning" OR "adaptive updating")`
- Europe PMC: `(TITLE_ABS:awareness OR TITLE_ABS:unaware OR TITLE_ABS:conscious OR TITLE_ABS:unconscious OR TITLE_ABS:visibility OR TITLE_ABS:visible OR TITLE_ABS:invisible OR TITLE_ABS:unseen OR TITLE_ABS:subliminal OR TITLE_ABS:nonconscious) AND (TITLE_ABS:"error-based learning" OR TITLE_ABS:"reinforcement learning" OR TITLE_ABS:"evaluative conditioning" OR TITLE_ABS:"adaptive updating")`

### Blind sentinel check

Use the six existing CALIB003 sentinels unchanged and without embedding titles, authors, or identifiers in any query. Count only natural recovery inside the 480-record windows. This is a syntax/recall diagnostic, not an inclusion test or registered stopping rule.

## CALIB003 independent-query instrument — executed historical provenance

CALIB002's Q001/Q002 instruments each returned 300 screened records from all eight source blocks but recovered none of the six calibration sentinels. They are retained below as failed historical calibration instruments, not as the proposed CALIB003 lane. The redesign uses six separate process families. Their union is a supplementary recall check alongside the empirical-seed citation graph, review/discovery anchors, and process-triggered searches; it is not a universal enumeration of Y.

Shared draft CALIB003 instrumentation for every block below: title/abstract fields; relevance order; page size 100; screen every returned record; stop after source exhaustion or 2 pages/200 encountered records, whichever comes first. Persist exact parameters and the stable IDs from each completed page before continuing. These bounds are calibration instruments, not registered stopping rules.

### QCAL3-ATTN — attention, control, inhibition, and distractor control

- OpenAlex (`/works`, `sort=relevance_score:desc`, `per_page=100`): `filter=title_and_abstract.search:(awareness OR unaware OR conscious OR unconscious OR visibility OR visible OR invisible OR unseen OR subliminal OR nonconscious) AND (attention OR "attentional control" OR inhibition OR suppression OR distractor OR "attentional capture")`
- Europe PMC (`/search`, default relevance, `pageSize=100`, cursor pagination, `synonym=false`): `(TITLE_ABS:awareness OR TITLE_ABS:unaware OR TITLE_ABS:conscious OR TITLE_ABS:unconscious OR TITLE_ABS:visibility OR TITLE_ABS:visible OR TITLE_ABS:invisible OR TITLE_ABS:unseen OR TITLE_ABS:subliminal OR TITLE_ABS:nonconscious) AND (TITLE_ABS:attention OR TITLE_ABS:"attentional control" OR TITLE_ABS:inhibition OR TITLE_ABS:suppression OR TITLE_ABS:distractor OR TITLE_ABS:"attentional capture")`

### QCAL3-META — metacognition, confidence, monitoring, and error evaluation

- OpenAlex: `filter=title_and_abstract.search:(awareness OR unaware OR conscious OR unconscious OR visibility OR visible OR invisible OR unseen OR subliminal OR nonconscious) AND (metacognition OR metacognitive OR confidence OR monitoring OR "error evaluation" OR "error detection")`
- Europe PMC: `(TITLE_ABS:awareness OR TITLE_ABS:unaware OR TITLE_ABS:conscious OR TITLE_ABS:unconscious OR TITLE_ABS:visibility OR TITLE_ABS:visible OR TITLE_ABS:invisible OR TITLE_ABS:unseen OR TITLE_ABS:subliminal OR TITLE_ABS:nonconscious) AND (TITLE_ABS:metacognition OR TITLE_ABS:metacognitive OR TITLE_ABS:confidence OR TITLE_ABS:monitoring OR TITLE_ABS:"error evaluation" OR TITLE_ABS:"error detection")`

### QCAL3-BIND — binding, integration, and object/event updating

- OpenAlex: `filter=title_and_abstract.search:(awareness OR unaware OR conscious OR unconscious OR visibility OR visible OR invisible OR unseen OR subliminal OR nonconscious) AND (binding OR integration OR "feature integration" OR "object updating" OR "event updating" OR "object file")`
- Europe PMC: `(TITLE_ABS:awareness OR TITLE_ABS:unaware OR TITLE_ABS:conscious OR TITLE_ABS:unconscious OR TITLE_ABS:visibility OR TITLE_ABS:visible OR TITLE_ABS:invisible OR TITLE_ABS:unseen OR TITLE_ABS:subliminal OR TITLE_ABS:nonconscious) AND (TITLE_ABS:binding OR TITLE_ABS:integration OR TITLE_ABS:"feature integration" OR TITLE_ABS:"object updating" OR TITLE_ABS:"event updating" OR TITLE_ABS:"object file")`

### QCAL3-MEM — memory, maintenance, and working memory

- OpenAlex: `filter=title_and_abstract.search:(awareness OR unaware OR conscious OR unconscious OR visibility OR visible OR invisible OR unseen OR subliminal OR nonconscious) AND (memory OR maintenance OR "working memory" OR retention OR retrieval)`
- Europe PMC: `(TITLE_ABS:awareness OR TITLE_ABS:unaware OR TITLE_ABS:conscious OR TITLE_ABS:unconscious OR TITLE_ABS:visibility OR TITLE_ABS:visible OR TITLE_ABS:invisible OR TITLE_ABS:unseen OR TITLE_ABS:subliminal OR TITLE_ABS:nonconscious) AND (TITLE_ABS:memory OR TITLE_ABS:maintenance OR TITLE_ABS:"working memory" OR TITLE_ABS:retention OR TITLE_ABS:retrieval)`

### QCAL3-DEC — decision, action, rule-guided, and flexible use

- OpenAlex: `filter=title_and_abstract.search:(awareness OR unaware OR conscious OR unconscious OR visibility OR visible OR invisible OR unseen OR subliminal OR nonconscious) AND (decision OR "action selection" OR "response selection" OR "rule guided" OR "rule-guided" OR flexibility OR "flexible behavior" OR "flexible behaviour")`
- Europe PMC: `(TITLE_ABS:awareness OR TITLE_ABS:unaware OR TITLE_ABS:conscious OR TITLE_ABS:unconscious OR TITLE_ABS:visibility OR TITLE_ABS:visible OR TITLE_ABS:invisible OR TITLE_ABS:unseen OR TITLE_ABS:subliminal OR TITLE_ABS:nonconscious) AND (TITLE_ABS:decision OR TITLE_ABS:"action selection" OR TITLE_ABS:"response selection" OR TITLE_ABS:"rule guided" OR TITLE_ABS:"rule-guided" OR TITLE_ABS:flexibility OR TITLE_ABS:"flexible behavior" OR TITLE_ABS:"flexible behaviour")`

### QCAL3-LEARN — learning and adaptation

- OpenAlex: `filter=title_and_abstract.search:(awareness OR unaware OR conscious OR unconscious OR visibility OR visible OR invisible OR unseen OR subliminal OR nonconscious) AND (learning OR adaptation OR adaptive OR conditioning OR "error driven" OR "error-driven")`
- Europe PMC: `(TITLE_ABS:awareness OR TITLE_ABS:unaware OR TITLE_ABS:conscious OR TITLE_ABS:unconscious OR TITLE_ABS:visibility OR TITLE_ABS:visible OR TITLE_ABS:invisible OR TITLE_ABS:unseen OR TITLE_ABS:subliminal OR TITLE_ABS:nonconscious) AND (TITLE_ABS:learning OR TITLE_ABS:adaptation OR TITLE_ABS:adaptive OR TITLE_ABS:conditioning OR TITLE_ABS:"error driven" OR TITLE_ABS:"error-driven")`

For the OpenAlex blocks after QCAL3-ATTN, endpoint, field, sort, and page size are the same as QCAL3-ATTN. For Europe PMC, endpoint, field restriction, relevance order, page size, cursor behavior, and `synonym=false` are likewise shared. The exact rendered query and source parameters must still be logged for every executed block.

### Query-calibration sentinels

The calibration-only sentinels are Tsushima et al. (2006), Lin and Murray (2015), Lamy et al. (2015), Ben-Haim et al. (2021), Persaud et al. (2011), and Keizer et al. (2015). They are not scientific inclusion labels. The union of the CALIB003 family windows should recover a substantial fraction of them; report the observed recovery without imposing a final numeric threshold in this draft. Do not embed their titles/DOIs in queries, do not count title lookups, and do not reveal expected A/E/F/outcome codes to registered agents.

### Draft source roles

OpenAlex is the proposed primary broad discovery/identity/citation source. Europe PMC is the parallel metadata/full-text source and conditional biomedical citation fallback. Crossref is the DOI/bibliographic identity and publisher-deposited backward-reference fallback. Semantic Scholar is optional, not required. This is a calibration conclusion and does not populate the still-unfrozen registered source fields in `config.yaml`.

## CALIB002 Q001/Q002 instruments — failed and retired from the main lane

## Q001 — Generic awareness × downstream use

**Purpose:** Broad coverage of awareness of X combined with a distinct downstream use Y.

The universal monolithic draft used in CALIB001 was retired because it returned approximately 12.2 million OpenAlex and 40,000 Europe PMC records. CALIB002 tested the source-specific blocks below; they are preserved verbatim for provenance and are not proposed for CALIB003.

### Q001-OA-BR1 — OpenAlex broad recall

- Parent: Q001
- Source/endpoint: OpenAlex `/works`
- Fields: `default.search` (OpenAlex text search over its indexed work text)
- Exact parameter: `search=(awareness OR aware OR unaware OR conscious OR unconscious OR visibility OR seen OR unseen) AND ("cognitive control" OR evaluation OR monitoring OR updating OR binding OR maintenance OR memory OR "action selection" OR adaptation) AND (experiment OR task OR performance)`
- Sort/ranking: `sort=relevance_score:desc`
- Page size: `per_page=100`
- Draft CALIB002 bound: at most 3 pages / 300 encountered records; screen all records actually returned within the bound
- Role: broad recall
- Translation: removes the unqualified terms `use`, `utilization`, and `cognitive function`, which dominated unrelated domains in CALIB001; OpenAlex Boolean text-search syntax is used without wildcard pseudo-syntax.

### Q001-OA-PR1 — OpenAlex title/abstract precision

- Parent: Q001
- Source/endpoint: OpenAlex `/works`
- Fields: `title_and_abstract.search`
- Exact parameter: `filter=title_and_abstract.search:(awareness OR unaware OR conscious OR unconscious OR visibility OR unseen) AND ("cognitive control" OR evaluation OR monitoring OR updating OR binding OR maintenance OR "action selection" OR adaptation)`
- Sort/ranking: `sort=relevance_score:desc`
- Page size: `per_page=100`
- Draft CALIB002 bound: at most 3 pages / 300 encountered records; screen all records actually returned within the bound
- Role: field-constrained precision and a coverage comparison with Q001-OA-BR1
- Translation: excludes generic `memory` unless paired through the separate maintenance term; title/abstract restriction deliberately trades recall for precision.

### Q001-EPMC-BR1 — Europe PMC broad recall

- Parent: Q001
- Source/endpoint: Europe PMC `/search`
- Fields: unfielded indexed text
- Exact query: `(awareness OR aware OR unaware OR conscious OR unconscious OR visibility OR seen OR unseen) AND ("cognitive control" OR evaluation OR monitoring OR updating OR binding OR maintenance OR memory OR "action selection" OR adaptation) AND (experiment OR task OR performance)`
- Sort/ranking: default relevance (`sort` omitted; score descending)
- Page size: `pageSize=100`, `cursorMark=*` then returned `nextCursorMark`
- Draft CALIB002 bound: at most 3 pages / 300 encountered records; screen all records actually returned within the bound
- Role: Europe PMC broad-recall comparator
- Translation: no synonym expansion (`synonym=false`); generic `use`/`utilization` are removed for the same calibrated noise reason as OpenAlex.

### Q001-EPMC-PR1 — Europe PMC title/abstract precision

- Parent: Q001
- Source/endpoint: Europe PMC `/search`
- Fields: `TITLE_ABS`
- Exact query: `(TITLE_ABS:awareness OR TITLE_ABS:unaware OR TITLE_ABS:conscious OR TITLE_ABS:unconscious OR TITLE_ABS:visibility OR TITLE_ABS:unseen) AND (TITLE_ABS:"cognitive control" OR TITLE_ABS:evaluation OR TITLE_ABS:monitoring OR TITLE_ABS:updating OR TITLE_ABS:binding OR TITLE_ABS:maintenance OR TITLE_ABS:"action selection" OR TITLE_ABS:adaptation)`
- Sort/ranking: default relevance (`sort` omitted; score descending)
- Page size: `pageSize=100`, `cursorMark=*` then returned `nextCursorMark`
- Draft CALIB002 bound: at most 3 pages / 300 encountered records; screen all records actually returned within the bound
- Role: field-constrained precision and coverage comparison with Q001-EPMC-BR1
- Translation: uses Europe PMC's supported `TITLE_ABS` field and exact phrase syntax; `synonym=false`.

## Q002 — Performance-matched awareness

**Purpose:** Find designs that match or diagnose first-order evidence while contrasting awareness.

The universal Q002 draft is retired. Its apostrophe/wildcard pseudo-syntax failed in OpenAlex and its generic `evidence`/`decision`/`action` terms produced approximately 10.2 million OpenAlex and 62,000 Europe PMC records.

### Q002-OA-BR1 — OpenAlex broad evidence-control recall

- Parent: Q002
- Source/endpoint: OpenAlex `/works`
- Fields: `default.search`
- Exact parameter: `search=(awareness OR conscious OR unconscious OR visibility OR seen OR unseen) AND ("performance matched" OR "matched performance" OR "objective performance" OR discrimination OR "d prime" OR titration OR threshold OR "signal strength") AND ("cognitive control" OR evaluation OR monitoring OR updating OR binding OR maintenance OR memory)`
- Sort/ranking: `sort=relevance_score:desc`
- Page size: `per_page=100`
- Draft CALIB002 bound: at most 3 pages / 300 encountered records; screen all records actually returned within the bound
- Role: broad recall for explicit first-order-evidence control language
- Translation: `d'` becomes `d prime`; unsupported wildcard stems become the literal variants `titration` and `threshold`; generic `evidence`, `decision`, and `action` are removed.

### Q002-OA-PR1 — OpenAlex title/abstract matching precision

- Parent: Q002
- Source/endpoint: OpenAlex `/works`
- Fields: `title_and_abstract.search`
- Exact parameter: `filter=title_and_abstract.search:("performance matched" OR "matched performance" OR titration OR threshold OR "d prime") AND (awareness OR conscious OR unconscious OR visibility OR unseen) AND (control OR monitoring OR updating OR binding OR maintenance OR memory)`
- Sort/ranking: `sort=relevance_score:desc`
- Page size: `per_page=100`
- Draft CALIB002 bound: at most 3 pages / 300 encountered records; screen all records actually returned within the bound
- Role: precision for explicit matching/titration/threshold designs
- Translation: no apostrophe or wildcard pseudo-syntax; title/abstract restriction is intentional.

### Q002-EPMC-BR1 — Europe PMC broad evidence-control recall

- Parent: Q002
- Source/endpoint: Europe PMC `/search`
- Fields: unfielded indexed text
- Exact query: `(awareness OR conscious OR unconscious OR visibility OR seen OR unseen) AND ("performance matched" OR "matched performance" OR "objective performance" OR discrimination OR "d prime" OR "d-prime" OR titrat* OR threshold* OR "signal strength") AND ("cognitive control" OR evaluation OR monitoring OR updating OR binding OR maintenance OR memory)`
- Sort/ranking: default relevance (`sort` omitted; score descending)
- Page size: `pageSize=100`, `cursorMark=*` then returned `nextCursorMark`
- Draft CALIB002 bound: at most 3 pages / 300 encountered records; screen all records actually returned within the bound
- Role: Europe PMC broad-recall comparator
- Translation: uses supported Europe PMC wildcards; omits the syntax-fragile apostrophe form `d'` in favor of explicit hyphen/space variants; `synonym=false`.

### Q002-EPMC-PR1 — Europe PMC title/abstract matching precision

- Parent: Q002
- Source/endpoint: Europe PMC `/search`
- Fields: `TITLE_ABS`
- Exact query: `(TITLE_ABS:awareness OR TITLE_ABS:conscious OR TITLE_ABS:unconscious OR TITLE_ABS:visibility OR TITLE_ABS:unseen) AND (TITLE_ABS:"performance matched" OR TITLE_ABS:"matched performance" OR TITLE_ABS:titrat* OR TITLE_ABS:threshold* OR TITLE_ABS:"d prime" OR TITLE_ABS:"d-prime") AND (TITLE_ABS:control OR TITLE_ABS:monitoring OR TITLE_ABS:updating OR TITLE_ABS:binding OR TITLE_ABS:maintenance OR TITLE_ABS:memory)`
- Sort/ranking: default relevance (`sort` omitted; score descending)
- Page size: `pageSize=100`, `cursorMark=*` then returned `nextCursorMark`
- Draft CALIB002 bound: at most 3 pages / 300 encountered records; screen all records actually returned within the bound
- Role: field-constrained precision and coverage comparison with Q002-EPMC-BR1
- Translation: uses supported `TITLE_ABS` and wildcard syntax; `synonym=false`.

## CALIB002 pagination and stopping instrumentation (DRAFT, not frozen)

CALIB002 uses page size 100 and an initial ceiling of 3 pages / 300 encountered records per block. Every record actually returned within that ceiling is screened. These values are calibration instruments, not a proposed universal registered maximum. For each block CALIB002 must report whether the complete result set was exhausted, marginal title-retain yield by page, duplicates across blocks, and the result-count/ranking stability observed on a repeated first-page request.

Persist stable identifiers for each completed page before requesting the next page. If a source reorders results, a cursor expires, a request truncates, or a tied rank crosses a boundary, deduplicate by stable identifier, record the instability, and repeat/continue only within the stated draft record ceiling; do not silently substitute a different ordering. Deduplication across blocks follows `AGENTS.md`, while every rediscovery remains in `discoveries.csv`.

CALIB002 must also compare each seed/anchor citation direction from (A) OpenAlex alone with (B) the union of OpenAlex and Europe PMC where Europe PMC coverage is usable. Record overlap, source-unique records, and source-unique records surviving title screening. Use page size 100 and a draft ceiling of 200 records per direction per source. Crossref may be assessed only as a publisher-deposited backward-reference fallback. Do not infer the final citation-source rule from counts alone.

## Other legacy drafts — not proposed CALIB003 blocks

## Q003 — Blindsight and metacognition

**Purpose:** Connect blindsight, subjective awareness, and downstream metacognitive use.

```text
(blindsight OR "cortical blindness" OR "visual field defect")
AND
(awareness OR conscious OR confidence OR wagering OR metacognition OR calibration)
AND
(discrimination OR decision OR monitoring OR control OR strategy OR use)
```

## Q004 — Attention and control

**Purpose:** Cover awareness-dependent or awareness-independent control, selection, conflict, capture, and suppression.

```text
(awareness OR conscious OR unconscious OR visible OR invisible OR seen OR unseen)
AND
(attention OR "attentional capture" OR control OR inhibition OR suppression OR conflict OR distractor OR cue*)
AND
(mask* OR threshold* OR visibility OR discrimination OR "continuous flash suppression" OR CFS)
```

## Q005 — Preserved capacity and unconscious function

**Purpose:** Find positive downstream-use effects without awareness plus explicit aware/unaware comparisons.

```text
(unconscious OR unaware OR invisible OR unseen OR subliminal OR nonconscious)
AND
(preserved OR intact OR capacity OR function OR use OR control OR evaluation OR updating OR binding OR maintenance OR memory OR action)
AND
(aware OR conscious OR visible OR seen OR awareness OR visibility OR comparison OR interaction OR equivalence OR Bayes*)
```

## Q006 — Masking, CFS, thresholds, and visibility fluctuations

**Purpose:** Cover methods that generate or exploit awareness contrasts for nominally similar X.

```text
(mask* OR "continuous flash suppression" OR CFS OR threshold* OR "near threshold" OR "subjective visibility" OR "visibility fluctuation*" OR "spontaneous visibility" OR "binocular rivalry")
AND
(aware OR unaware OR conscious OR unconscious OR seen OR unseen OR visible OR invisible)
AND
(control OR evaluation OR monitoring OR updating OR binding OR maintenance OR memory OR selection OR strategy OR adaptation)
```

## QDYN001 — Process-triggered expansion template

**Activation:** Use once for a newly normalized `Y_label` only after an experiment provisionally meets the A/E/F activation conditions in `PROTOCOL.md`. Search only the observed process. Log the rendered query verbatim, its trigger experiment, source, and normalization decision.

The permitted lexical universe is closed: canonical Y; morphology/grammar/spelling/hyphenation of canonical Y; terminology explicitly used for Y in the qualifying source paper; and one frozen immediate-parent functional term. Each rendered term must carry its provenance category, source or derivation, and rationale. Unrestricted language-model synonyms and neighboring functions are invalid. The source renderers in `tools/query_instruments.py` enforce these categories locally before any call.

The source-specific query crosses explicit awareness terms directly with the validated Y variants in title/abstract fields. Generic `experiment`, `task`, and `performance` clauses and an obligatory masking-method clause are removed because CALIB003 showed that they can make an already narrow process phrase pathological.

### Prepared Tsushima diagnostic query (not executed)

Permitted variants, exhaustively:

| Term | Provenance category | Rationale |
|---|---|---|
| `regulation of task-irrelevant distractor interference` | canonical-y | Conservative Y assigned from the behavioral dependent measure. |
| `task-irrelevant distractor-interference regulation` | morphology-grammar | Nominal reordering and hyphenation only; the function is unchanged. |
| `regulating task-irrelevant distractor interference` | morphology-grammar | Gerund form of the canonical label only. |
| `inhibitory control` | source-paper-terminology | Explicitly used in the paper title and article, pp. 1786–1788. |
| `attention filtering` | source-paper-terminology | Filtering terminology explicitly used for the observed interference effect, article pp. 1786–1788. |
| `distractor interference control` | frozen-immediate-parent | Single immediate parent `Y-PARENT-DISTRACTOR-INTERFERENCE-CONTROL`; no neighboring function is added. |

- OpenAlex: `filter=title_and_abstract.search:(awareness OR unaware OR conscious OR unconscious OR visibility OR visible OR invisible OR unseen OR subliminal OR nonconscious) AND ("regulation of task-irrelevant distractor interference" OR "task-irrelevant distractor-interference regulation" OR "regulating task-irrelevant distractor interference" OR "inhibitory control" OR "attention filtering" OR "distractor interference control")`
- Europe PMC: `(TITLE_ABS:awareness OR TITLE_ABS:unaware OR TITLE_ABS:conscious OR TITLE_ABS:unconscious OR TITLE_ABS:visibility OR TITLE_ABS:visible OR TITLE_ABS:invisible OR TITLE_ABS:unseen OR TITLE_ABS:subliminal OR TITLE_ABS:nonconscious) AND (TITLE_ABS:"regulation of task-irrelevant distractor interference" OR TITLE_ABS:"task-irrelevant distractor-interference regulation" OR TITLE_ABS:"regulating task-irrelevant distractor interference" OR TITLE_ABS:"inhibitory control" OR TITLE_ABS:"attention filtering" OR TITLE_ABS:"distractor interference control")`

CALIB004 syntax bound for this diagnostic: one initial result window per source, 50 records each, screen/audit all returned records, maximum 100 encounters. Report source parse success and result-universe size; do not follow results or retrieve full text.

## CALIB004 bounded plan (prepared, not authorized or executed)

1. **A — compact volume and blind sentinel recovery:** syntax-test the six QCAL4 blocks on OpenAlex and Europe PMC, one 40-record window per source/block, screen and audit all returns, maximum 480 encounters. Evaluate the unchanged six sentinels blindly.
2. **B — dynamic-query syntax/universe:** syntax-test the prepared Tsushima query on both sources, one 50-record window each, maximum 100 encounters. Confirm parsing and that the returned universe is non-pathological; do not expand citations or recurse.
3. **C — mechanical Meyen-role verification:** use synthetic rows only to verify inference-critical blocking, supplementary non-blocking, and retention of supplementary status in derived files. This phase has zero literature records.

The total CALIB004 ceiling is 580 encountered literature records. It includes no citation calibration, F/full-text calibration, source-ordering calibration, scientific screening beyond the returned calibration windows, or change to frozen scientific criteria. This plan is preparation only and does not authorize a calibration run.

## Freeze checklist for queries

- Select exact databases and interfaces.
- Translate each draft into source-specific syntax.
- Freeze field restrictions, language/document-type limits, and publication cutoff behavior.
- Decide whether spelling, hyphenation, and controlled-vocabulary variants are explicit or source-generated.
- Define deduplication and pagination/export behavior.
- Pilot for syntax only before registration; preserve pilot changes in version history.
