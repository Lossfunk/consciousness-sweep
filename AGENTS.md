# Agent Execution Contract

**Status:** draft-0.8, pre-freeze

## 1. Authority split

> `PROTOCOL.md` is the sole authority on scientific eligibility, A/E/F, result classification, statistics, Meyen, screening, discovery and stopping rules.

> `AGENTS.md` is the authority on loading, immutable inputs, filesystem paths, state recording, validation and completion.

Scientific conflict → `PROTOCOL.md`. Execution conflict → `AGENTS.md`. Neither may change during a registered run. If either authority is silent, record the case as unresolved with a why; do not invent a rule.

## 2. Repository contract

```text
consciousness-sweep/
├── README.md
├── AGENTS.md
├── PROTOCOL.md
├── seeds_empirical.csv
├── seeds_reviews.csv
├── queries.md
├── config.yaml
├── requirements.txt
├── schemas/
│   ├── papers.schema.json
│   ├── experiments.schema.json
│   ├── search_log.schema.json
│   ├── discoveries.schema.json
│   ├── missing_texts.schema.json
│   ├── auxiliary_sources.schema.json
│   ├── fulltext_assets.schema.json
│   ├── evidence_assessments.schema.json
│   ├── evidence_bundles.schema.json
│   ├── evidence_links.schema.json
│   ├── decision_log.schema.json
│   └── run_state.schema.json
├── tools/
│   ├── preflight.py
│   ├── init_run.py
│   ├── validate_run.py
│   ├── derive_outputs.py
│   ├── structured_write.py
│   ├── query_instruments.py
│   ├── calibration_sampling.py
│   └── bootstrap_env.py
├── tests/
├── runs/
└── outputs/
    └── consolidated/
```

Each independent run writes only to `runs/<RUN_ID>/` and contains:

```text
runs/<RUN_ID>/
├── papers_master.csv
├── experiments_master.csv
├── search_log.csv
├── discoveries.csv
├── missing_texts.csv
├── auxiliary_sources.csv
├── fulltext_assets.csv
├── evidence_assessments.csv
├── evidence_bundles.csv
├── evidence_links.csv
├── decision_log.jsonl
├── run_state.json
├── design_eligible_experiments.csv
├── constraint_ready_experiments.csv
├── awareness_linked_differences.csv
├── unaware_capacities.csv
├── no_detectable_awareness_differences.csv
├── equivalence_supported_no_difference.csv
├── unresolved_comparisons.csv
├── run_summary.md
└── fulltexts/
```

The experiment-named CSV filenames are retained to avoid unnecessary churn, but every row in `experiments_master.csv` and its derived views is one paper × experiment × X→Y comparison. `comparison_id` is the unique scientific row identifier; `experiment_id` may therefore repeat across rows.

Agents must not inspect another run or write to `outputs/consolidated/`. Paths stored in run files are repository-relative unless a schema states otherwise.

## 3. Immutable registered-run inputs

During a registered run, treat these as read-only:

- `AGENTS.md`
- `PROTOCOL.md`
- `seeds_empirical.csv`
- `seeds_reviews.csv`
- `queries.md`
- `config.yaml`
- `requirements.txt`
- `schemas/*`
- `tools/*`

## 4. Invocation, preflight, start, and resume

Every execution invocation supplies `RUN_ID`, `RUN_MODE = start|resume`, and agent-harness/model metadata where available. `RUN_ID` must be non-empty and filesystem-safe.

Use `requirements.txt` as the canonical dependency specification. The canonical setup is `python3 tools/bootstrap_env.py --venv .venv`, followed by `.venv/bin/python tools/preflight.py --mode ...` (Windows: `.venv\Scripts\python`). The bootstrap utility creates an isolated environment when absent and installs the repository requirements without editing them. Do not improvise or mutate dependency specifications during a run.

Run `.venv/bin/python tools/preflight.py --mode registered` before scientific work. It parses and validates every immutable input, verifies frozen configuration and package/schema versions, and fails on null/TODO freeze fields. If dependencies are missing, preflight must exit with the canonical bootstrap command rather than a raw import traceback. This draft intentionally fails registered preflight; `--mode pre-freeze` audits it without authorizing a run.

### Start

For `RUN_MODE=start`:

1. `runs/<RUN_ID>/` must not exist.
2. Run `python tools/init_run.py --run-id <RUN_ID> --run-mode start --agent-harness <HARNESS>`.
3. The initializer creates schema-derived CSV headers, empty history and derived files, `fulltexts/`, summary, and `run_state.json`.
4. Refuse any accidental overwrite.

### Resume

For `RUN_MODE=resume`:

1. `runs/<RUN_ID>/` must exist; do not recreate, truncate, or reset any file.
2. Run `python tools/init_run.py --run-id <RUN_ID> --run-mode resume --agent-harness <HARNESS>`.
3. The utility first verifies exact package/schema compatibility, then validates the existing run, verifies unchanged protocol/config/schema state, recovers counters from durable records, appends a resume event, and updates run state.
4. Continue from the recorded audit state, not memory.

A completed run may reopen only when newly supplied requested full texts are ready for ingestion or an explicitly logged continuation is requested under the same frozen protocol. Supply a non-empty reopening reason. Reopening may reactivate citation or process-search stopping conditions but may not alter frozen inputs.

## 5. Run state and stable identifiers

`run_state.json` is the durable checkpoint for run status, versions, provenance, wave, counters, timestamps, harness, and model metadata. Update it at every validation checkpoint and status transition. Never use in-memory counters without reconciling them against durable files.

Every new run records `protocol_version`, `package_version`, `schema_version`, the repository commit, and immutable input hashes. A validator must refuse—before applying current schemas—to validate or resume a historical run whose package/schema version differs. Historical runs remain valid provenance under their original commit/package and are never silently migrated.

- Paper: `P000001`.
- Experiment: `P000001_E01`.
- Comparison: `P000001_E01_C01`.
- Decision: `<RUN_ID>_D000001`.
- Search: `<RUN_ID>_S000001`.
- Discovery result: `<RUN_ID>_R000001`.
- Auxiliary source: `<RUN_ID>_AUX000001`.
- Evidence link: `<RUN_ID>_EL000001`.
- Evidence bundle: `<RUN_ID>_EB000001`.
- Evidence assessment: `<RUN_ID>_EA000001`.
- Full-text asset: `<RUN_ID>_FT000001`.

Assign each ID once; never recycle or renumber it. Allocate every post-initialization ID through the locked allocator in `tools/structured_write.py`; workers must not infer a next identifier by reading a table or `run_state.json`. Allocation atomically advances durable state before returning the reserved ID, so a crash may retire an unused ID but may never permit reuse. On resume, each next counter must exceed the greatest durable identifier already present. Per-paper experiment counters and per-experiment comparison counters are stored as mappings or recovered equivalently from durable IDs. Multiple rows may share an `experiment_id`, but `comparison_id` must be unique.

## 6. Current state, complete provenance, and continuous writes

Master CSVs hold current state. `decision_log.jsonl` is append-only history. `discoveries.csv` is complete search-result provenance: one row for every paper result actually encountered through a logged search or citation event, including every rediscovery.

Write continuously:

- Newly encountered logical paper → `papers_master.csv`.
- Search, query, retrieval, or citation event → `search_log.csv`.
- Every result encountered in that event → `discoveries.csv`.
- Missing-text or manual-ingestion state → `missing_texts.csv`.
- Classification-critical external evidence → `auxiliary_sources.csv`.
- Every verified paper/version and extraction → `fulltext_assets.csv`.
- Every reusable execution-only factual assessment → `evidence_assessments.csv`.
- Every scientific premise assembled from borrowed support → `evidence_bundles.csv`.
- Every explicit scientific use of within-paper, supplementary, same-experiment, or external support → `evidence_links.csv`.
- Full-text X→Y comparison → `experiments_master.csv`.
- Every decision, revision, merge, status transition, and uncertainty → `decision_log.jsonl`.
- Wave/counter/status checkpoint → `run_state.json`.

Do not reconstruct records from memory at the end. Write a parent record before using its ID elsewhere. `papers_master.csv` fields prefixed `first_` record only the first discovery; they never substitute for `discoveries.csv`.

Registered agents must not construct CSV rows by shell concatenation or raw delimiter joining. Use `tools/structured_write.py` (or its imported schema-aware writer functions) for ID allocation, master-row append/upsert, and decision-log append. One per-run lock serializes counter allocation and all read-modify-write operations. The tool derives field order from the schema, performs typed JSON Schema validation before mutation, applies CSV quoting automatically, and atomically replaces CSV/JSONL files. Its JSONL writer ASCII-escapes embedded Unicode separators and writes exactly one physical LF-terminated record per event. A decision event must still be appended before a current-state upsert.

Every title, abstract/abstract-unavailable state, retrieval, auxiliary dependency, full-text asset, factual assessment, evidence bundle/link, citation-expansion, deduplication, comparison structure, A/evidence-type/F/provisional-E/final-E, specifically named unaware-capacity claim, awareness-effect, statistics, Meyen, exclusion, revision, uncertainty, and run-state decision requires a short why. Comparison-level scientific decisions use `entity_type = comparison` and the stable `comparison_id`. Auxiliary evidence, full-text assets, factual assessments, evidence bundles, and evidence links use their corresponding entity types. Experiment-level bookkeeping may use `entity_type = experiment`. Full-text decisions should include page, figure, table, analysis, auxiliary, bundle, link, or asset pointers where possible. Validate every decision event against `schemas/decision_log.schema.json`.

`source_location` may be empty only when no source pointer exists; when that matters, explain the absence in `reason`.

## 7. Full-text sequence and revisions

Follow the scientific order in `PROTOCOL.md`. Operationally, enumerate physical experiment groups first and reserve each experiment ID before reserving any comparison IDs. Then enumerate scalar or coherent factorial X→Y comparisons. For each comparison: complete the structural audit; record A and F; log provisional E and the full E-diagnostic rationale where applicable; create one evidence-bundle row per borrowed premise; create every direct member link before relying on the bundle; derive and record each bundle status; name the exact focal or component function in `unaware_capacity_claim`; assess the unaware-capacity route whenever A/F permit it; assess the awareness-effect route only when strong A/E/F permit it; assess null/equivalence only when the awareness-effect route and its statistics permit it; and record the result-inspection disposition. A supporting experiment receives an experiment pointer in a link but no comparison row unless it independently answers an X→Y question. Weak or unusable E closes the awareness-effect and null/equivalence routes but does not by itself close the unaware-capacity route. The allocator must reject a comparison whose experiment group has not already been reserved. Do not duplicate or reinterpret the scientific definitions here.

Before changing current state:

1. append an event containing field, old value, new value, reason, and source location to `decision_log.jsonl`;
2. update the current-state row.

Never silently overwrite, including clerical corrections.

## 8. Search-result provenance and deduplication

Each `search_log.csv` row identifies an event. A process-triggered event links to its activating `comparison_id` through `trigger_comparison_id`. Each encountered result receives a separate `discoveries.csv` row linked by `search_id`, even when it resolves to an existing paper.

Execute the workflow as this durable principal-first, blind-last state machine:

1. initialize frozen empirical seeds;
2. initialize frozen review/discovery anchors;
3. screen and index candidate literature from those principal inputs;
4. perform backward/forward citation expansion in frozen waves;
5. obtain and evaluate full texts as appropriate;
6. activate process searches only when qualifying Ys are independently earned;
7. citation-expand relevant newly discovered nodes;
8. continue until every principal frontier is provisionally satisfied;
9. only then enter the mandatory supplementary blind lane and execute every frozen source/family window;
10. deduplicate blind results against the complete logical-paper index before semantic screening;
11. add rediscovery provenance for known works without repeating their current paper-level semantic decisions;
12. individually screen genuinely new logical works, using bounded batches only for context amortization;
13. reopen citation expansion for every blind-discovered independently citation-eligible node;
14. reopen or activate the process frontier for every genuinely new Y that independently qualifies;
15. recursively handle new nodes under the unchanged bounded rules; and
16. finish only after every reopened citation and process frontier again satisfies its frozen stopping criterion.

The blind lane may not be skipped because the principal routes appear productive or saturated, known anchors were recovered, or available time/token budget seems sufficient. A blind-lane discovery that is independently citation-eligible reopens the citation frontier; a genuinely new independently qualifying Y activates or reopens its bounded process search. Record every transition and do not mark the run complete while any reopened frontier remains open.

Every independent or process query window is an immutable retrieval snapshot identified by its execution phase, source, family or normalized Y label, canonical query, source parameters, publication cutoff, requested N, and deterministic window key. A completed window records the ordered result-set hash and retrieval time. Resume reuses a completed snapshot only when the entire key and ordered hash still match durable discoveries; it never silently reruns, extends, reranks, or substitutes a window. A missing, partial, or inconsistent snapshot remains incomplete and must be explicitly resolved.

The blind lane uses the five active QCAL families `ATTN`, `META`, `BIND`, `MEM`, and `DEC`, on both OpenAlex and Europe PMC, with one window of at most 40 results for every source/family pair. It requests no second page and never reallocates unused quota. `LEARN` is disabled/retired as a generic blind-query family but remains scientifically eligible through every other route. Each activated QDYN search uses both sources, one window of at most 50 results per source for that normalized Y, the frozen lexical rendering rules, no retrigger for the same normalized Y/source window, and only bounded recursion from a genuinely new independently qualifying Y.

Apply bibliographic deduplication deterministically:

1. Normalize DOI by trimming whitespace, lowercasing, and removing a leading `https://doi.org/`, `http://doi.org/`, `http://dx.doi.org/`, `https://dx.doi.org/`, or `doi:` prefix.
2. Identical non-empty normalized DOI means the same work unless clear contrary evidence is recorded.
3. Without DOI, compare normalized title plus year plus authors. Normalize title for case, Unicode, surrounding punctuation, and repeated whitespace; normalize author strings consistently without guessing identities.
4. Do not automatically collapse uncertain matches. Mark them `possible-duplicate` and keep separate paper records until resolved.
5. Link preprint and published versions as one logical work only when authorship, title/content, and explicit version relationship make the link sufficiently clear.

Use `normalize_doi` and `doi_resolver_url` from `tools/structured_write.py` for stored DOI comparisons and resolver URLs. Percent-decode before canonical normalization, then percent-encode unsafe DOI path characters when constructing `https://doi.org/` links; never interpolate a raw DOI into a URI field.

Before any bulk bibliographic persistence, run the non-mutating DOI/URL normalization dry run over the complete proposed batch. Resolve every rejected or unsafe record before allocating paper/discovery IDs or writing parent rows. A passing dry run does not replace row-level schema validation.

Every deduplication or merge requires `dedup_reason`/`duplicate_reason` and a decision-log event. A confirmed duplicate points `duplicate_of` to the retained paper ID; history and discovery rows are never deleted.

## 9. Missing texts and manual full-text ingestion

Follow priority and batching rules in `PROTOCOL.md`. At each checkpoint, order unresolved requests by protocol priority and stable paper ID, and surface at most `ask_text_batch_size` records. Mark the request and wave in `missing_texts.csv`; continue independent work.

For any obtained full text:

1. store or reference it under `runs/<RUN_ID>/fulltexts/` using a filename associated with `paper_id`;
2. record the repository-relative path and, where practical, SHA-256 hash;
3. record the actual `obtained_at`, `obtained_wave`, `obtained_by`, and `acquisition_route`;
4. append the missing-text status transition before updating current state;
5. evaluate it on `resume`;
6. reopen any citation-expansion or process-search stopping condition activated by the text.

Never backdate availability or imply that the file was available in an earlier wave. `obtained_by=user` is used for user-supplied text; `agent` for retrieval during execution; and `preexisting` only when the file genuinely existed before the run invocation.

### 9.1 Abstract-unavailable records

For every title-retained paper whose abstract cannot reasonably be obtained, set `abstract_status = unavailable`, retain `abstract_screen = not-screened` with a reason, and assign full-text priority from title, discovery provenance, and metadata. This state may proceed to retrieval; it is never converted to `screen-out` merely because the abstract is missing.

### 9.2 Registered screening execution

Title and abstract screening are paper-specific semantic decisions under `PROTOCOL.md`, even when records are presented in batches. Title batches contain at most 25 logical works and abstract batches at most 10. Batch membership is context amortization only: write one durable decision and one paper-specific reason per logical work. A prior decision may be reused only for the same logical work, same scientific regime fingerprint, and unchanged decision-relevant evidence. Genuinely new evidence permits revision only through an append-first decision-log event followed by the current-state update. Regex, keyword, embedding, citation-count, numeric relevance, and hidden lexical heuristics may not independently produce `exclude` or `screen-out`; this draft registers no deterministic scientific exclusion rule.

### 9.3 Auxiliary evidence sources

Record each reusable external logical work/version in `auxiliary_sources.csv`. Store its bibliographic and retrieval identity once; do not duplicate it for each target comparison. Every scientific use, transfer judgment, limitation, and dependency role belongs in the target comparison's evidence bundle and link. Auxiliary rows do not create `papers_master.csv` or `discoveries.csv` records unless the work is independently encountered through an ordinary discovery event, so support-only evidence cannot leak into the candidate pool.

### 9.4 Evidence bundles

Create one `evidence_bundles.csv` row for one named premise of one focal comparison. Its `required_member_keys` manifest names every member logically required before any result is known, so an omitted required link is auditable as incomplete. The same source used for two premises or comparisons requires distinct bundles and explicit direct links. Each `evidence_links.csv` row receives its own stable ID and unique bundle-local `member_key`, and records one member, supported claim, dependency role (`required`, `strengthening`, `robustness`, `generalization`, or `mechanistic`), member status, transfer reason, limitation, and source location. Links to external sources resolve to reusable auxiliary rows; within-paper supporting experiments need no candidate comparison row.

Bundle status is derived, not asserted opportunistically: `conflicted` when any direct member contradicts or is conflicted; otherwise `incomplete` when any required member is absent, unavailable, unevaluated, or transfer-invalid; otherwise `complete` when at least one decision-used member supports the premise and every required member supports it. No scientific conclusion may depend on an incomplete or conflicted bundle. Evidence transfer is premise-specific and must justify population, manipulation, measure, analysis, and version compatibility where relevant. Evidence links are direct only: no transitivity, no inference from sharing a source or bundle, and no propagation of a conclusion from one comparison to another.

### 9.5 Execution-only evidence assessments

`evidence_assessments.csv` is a factual execution cache, never a scientific bundle or classification store. Reuse requires the same logical source/version, source-asset hash, factual premise, source location, and exact scientific-regime fingerprint. It may cache such facts as task structure, measure identity, reported analysis, or quoted result, but it must not contain or propagate A/E/F codes, route outcomes, eligibility, Meyen conclusions, or comparison-level scientific judgments. Every target comparison still requires its own explicit scientific bundle/link and decision.

### 9.6 Verified full-text assets

Record one verified `fulltext_assets.csv` row per logical paper/article version, with stable source identity, immutable file hash, verification reason, and—when created—extraction tool/version, extracted-text hash, and page-map hash. Reuse that verified asset and extraction across comparisons within the same paper/version. Never redownload or re-extract an unchanged verified version merely because another comparison needs it. A materially different article version receives a new immutable asset row; current-version changes are logged, never overwritten silently.

## 10. Deterministic derived files

Run `python tools/derive_outputs.py --run-id <RUN_ID>`; never classify derived files separately. The utility applies only these filters and sorts by `paper_id`, then `experiment_id`, then `comparison_id`.

### Awareness-effect design eligible

`A_code` in `{A-direct, A-validated}` AND `E_code` in `{E-matched, E-diagnostic}` AND `F_code = F-meaningful`.

### Constraint-ready awareness-linked difference

All of: awareness-effect design eligible; `awareness_effect = difference-supported`; `awareness_effect_stats_status = adequate`; `difference_tested = yes`; and, if `Meyen_role = inference-critical`, `Meyen_status = Meyen-satisfied`. A supplementary Meyen result remains visible but does not gate.

### Constraint-ready unaware capacity

All of: `A_code` in `{A-direct, A-validated}`; `F_code = F-meaningful`; non-empty `unaware_capacity_claim` names the exact focal or component function positively demonstrated under unawareness; `unaware_capacity = supported` for that same function; `unaware_capacity_stats_status = adequate`; and, if `Meyen_role = inference-critical`, `Meyen_status = Meyen-satisfied`. A nonzero effect of X on some other downstream consequence does not pass. E does not gate this route.

### Strongest equivalence-supported invariance

All of: awareness-effect design eligible; non-empty `unaware_capacity_claim`; `unaware_capacity = supported` for that named function; `unaware_capacity_stats_status = adequate`; `awareness_effect = equivalence-supported`; `awareness_effect_stats_status = adequate`; `difference_tested = yes`; `null_evidence_adequacy = adequate`; and the inference-critical Meyen gate.

`constraint_ready_experiments.csv` is the deduplicated union of the awareness-linked-difference, unaware-capacity, and equivalence-supported routes. `no_detectable_awareness_differences.csv` contains every fully evaluated comparison assigned that descriptive category, without upgrading it to equivalence. `unresolved_comparisons.csv` contains fully evaluated comparisons with `unaware_capacity = unclear` or `awareness_effect = unresolved`. A comparison may appear in multiple compatible views.

## 11. Validation checkpoints

At the end of every search wave:

1. flush all writes;
2. run `python tools/derive_outputs.py --run-id <RUN_ID>`;
3. run `python tools/validate_run.py --run-id <RUN_ID>`;
4. check IDs, counters, cross-file references, schema conditionals, file hashes, and every required why;
5. check every declared bundle against its derived status, every direct member/reference and strict transfer record, every execution-cache fingerprint and source hash, every full-text version/hash, and that no support-only source silently entered the candidate pool;
6. prepare the bounded ask-text batch;
7. update `run_summary.md` with route/wave progress, counts, unresolved cases, missing texts, validation outcome, and remaining stopping conditions;
8. update `run_state.json` checkpoint timestamp, counters, wave, status, and reason.

Resolve validation failures before another wave. Do not add ad hoc categorical values.

For CALIB003 only, after title/abstract screening, select at most 12 newly discovered `screen-in` candidates with `tools/calibration_sampling.py`: sort by full-text priority (`high`, `medium`, `low`), then earliest durable first-discovery ID, then `paper_id`, and take the first 12 (or all if fewer). Expected A/E/F/outcome must not enter selection or tie-breaking. Attempt retrieval for all selected papers, fully evaluate every obtained text, and apply normal missing-text handling to the rest. This bounded sampling rule is not the registered sweep rule; a registered sweep evaluates every retrievable paper passing its full-text threshold.

## 12. Independent-run isolation and completion

Do not inspect another run, use its discovered papers, import its classifications, or consolidate. Consolidation/adjudication occurs only after independent runs finish and is outside an executing agent's write scope.

A run is complete only when: the principal frontier was provisionally satisfied; every mandatory blind window is complete and hash-consistent; every blind-triggered citation or new-Y process frontier has been reopened and subsequently satisfied; all frozen routes and activated process searches are done; stopping rules are met; retrievable and manually supplied texts are evaluated; missing-text state is current; no scientific conclusion depends on an incomplete/conflicted bundle; route audits and result-inspection dispositions are complete; files validate; unresolved cases have reasons; derived files are current; and `run_summary.md` documents stopping evidence and validation. Set `run_state.status = complete` only after all conditions hold.

Across independent registered runs, agents share only immutable static package inputs: frozen seed and review-anchor identity, normalization rules, schemas, queries, protocol, and agent instructions. They do not share semantic screening decisions, dynamic result sets, A/E/F codes, evidence links or assessments, statistical/Meyen judgments, process-Y or saturation judgments, full-text annotations, or run outputs. No dynamic query result is precomputed for distribution across agents. If one harness uses multiple workers inside a single independent run, it may divide already-reserved, non-overlapping execution units only; all writes still pass through that run's locked structured writer and the coordinator reconciles durable state before checkpoints.
