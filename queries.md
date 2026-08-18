# Draft Query Specification

**Status of every exact string below: DRAFT — TO FREEZE BEFORE REGISTERED RUN**

These query families are recall checks and discovery tools, not eligibility definitions. Interpret eligibility only under `PROTOCOL.md`. Before registration, adapt and freeze each exact string for every named search source, recording source-specific syntax, fields, limits, date handling, and fallback behavior. Do not execute these drafts during repository construction.

## Q001 — Generic awareness × downstream use

**Purpose:** Broad coverage of awareness of X combined with a distinct downstream use Y.

The universal monolithic draft used in CALIB001 is retired because it returned approximately 12.2 million OpenAlex and 40,000 Europe PMC records. CALIB002 must test these source-specific blocks without treating their draft bounds as frozen stopping rules.

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

```text
(awareness OR aware OR unaware OR conscious OR unconscious OR visibility OR seen OR unseen)
AND
("{{Y_LABEL}}" OR {{FROZEN_Y_SYNONYMS_IF_ANY}})
AND
(experiment OR task OR performance)
AND
(mask* OR threshold* OR discrimination OR "continuous flash suppression" OR CFS OR blindsight)
```

`{{FROZEN_Y_SYNONYMS_IF_ANY}}` must be restricted to synonyms frozen for the observed Y at activation time. Do not add neighbouring cognitive processes. The rendered source-specific string is the auditable query; the template alone is not sufficient.

## Freeze checklist for queries

- Select exact databases and interfaces.
- Translate each draft into source-specific syntax.
- Freeze field restrictions, language/document-type limits, and publication cutoff behavior.
- Decide whether spelling, hyphenation, and controlled-vocabulary variants are explicit or source-generated.
- Define deduplication and pagination/export behavior.
- Pilot for syntax only before registration; preserve pilot changes in version history.
