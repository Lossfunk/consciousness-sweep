# Agent Execution Contract

**Status:** draft-0.3, pre-freeze

## 1. Authority split

> `PROTOCOL.md` is the sole authority on scientific eligibility, A/E/F, result classification, statistics, Meyen, screening, discovery and stopping rules.

> `AGENTS.md` is the authority on loading, immutable inputs, filesystem paths, state recording, validation and completion.

Scientific conflict → `PROTOCOL.md`. Execution conflict → `AGENTS.md`. Neither may change during a registered run. If either authority is silent, record the case as unresolved with a why; do not invent a rule.

## 2. Repository contract

```text
consciousness-sweep/
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
│   ├── decision_log.schema.json
│   └── run_state.schema.json
├── tools/
│   ├── preflight.py
│   ├── init_run.py
│   ├── validate_run.py
│   └── derive_outputs.py
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
├── decision_log.jsonl
├── run_state.json
├── design_eligible_experiments.csv
├── constraint_ready_experiments.csv
├── awareness_linked_differences.csv
├── preserved_capacities.csv
├── inconclusive_experiments.csv
├── run_summary.md
└── manual_fulltexts/
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

Run `python tools/preflight.py --mode registered` before scientific work. It parses and validates every immutable input, verifies frozen configuration and schema versions, and fails on null/TODO freeze fields. This draft intentionally fails registered preflight; `python tools/preflight.py --mode pre-freeze` audits it without authorizing a run.

### Start

For `RUN_MODE=start`:

1. `runs/<RUN_ID>/` must not exist.
2. Run `python tools/init_run.py --run-id <RUN_ID> --run-mode start --agent-harness <HARNESS>`.
3. The initializer creates schema-derived CSV headers, empty history and derived files, `manual_fulltexts/`, summary, and `run_state.json`.
4. Refuse any accidental overwrite.

### Resume

For `RUN_MODE=resume`:

1. `runs/<RUN_ID>/` must exist; do not recreate, truncate, or reset any file.
2. Run `python tools/init_run.py --run-id <RUN_ID> --run-mode resume --agent-harness <HARNESS>`.
3. The utility validates the existing run, verifies unchanged protocol/config/schema version state, recovers counters from durable records, appends a resume event, and updates run state.
4. Continue from the recorded audit state, not memory.

A completed run may reopen only when newly supplied requested full texts are ready for ingestion or an explicitly logged continuation is requested under the same frozen protocol. Supply a non-empty reopening reason. Reopening may reactivate citation or process-search stopping conditions but may not alter frozen inputs.

## 5. Run state and stable identifiers

`run_state.json` is the durable checkpoint for run status, versions, provenance, wave, counters, timestamps, harness, and model metadata. Update it at every validation checkpoint and status transition. Never use in-memory counters without reconciling them against durable files.

- Paper: `P000001`.
- Experiment: `P000001_E01`.
- Comparison: `P000001_E01_C01`.
- Decision: `<RUN_ID>_D000001`.
- Search: `<RUN_ID>_S000001`.
- Discovery result: `<RUN_ID>_R000001`.

Assign each ID once; never recycle or renumber it. On resume, each next counter must exceed the greatest durable identifier already present. Per-paper experiment counters and per-experiment comparison counters are stored as mappings or recovered equivalently from durable IDs. Multiple rows may share an `experiment_id`, but `comparison_id` must be unique.

## 6. Current state, complete provenance, and continuous writes

Master CSVs hold current state. `decision_log.jsonl` is append-only history. `discoveries.csv` is complete search-result provenance: one row for every paper result actually encountered through a logged search or citation event, including every rediscovery.

Write continuously:

- Newly encountered logical paper → `papers_master.csv`.
- Search, query, retrieval, or citation event → `search_log.csv`.
- Every result encountered in that event → `discoveries.csv`.
- Missing-text or manual-ingestion state → `missing_texts.csv`.
- Full-text X→Y comparison → `experiments_master.csv`.
- Every decision, revision, merge, status transition, and uncertainty → `decision_log.jsonl`.
- Wave/counter/status checkpoint → `run_state.json`.

Do not reconstruct records from memory at the end. Write a parent record before using its ID elsewhere. `papers_master.csv` fields prefixed `first_` record only the first discovery; they never substitute for `discoveries.csv`.

Every title, abstract, retrieval, citation-expansion, deduplication, comparison split, A/F/provisional-E/final-E, result, statistics, preserved-capacity component, Meyen, exclusion, revision, uncertainty, and run-state decision requires a short why. Comparison-level scientific decisions use `entity_type = comparison` and the stable `comparison_id`. Experiment-level bookkeeping may use `entity_type = experiment`. Full-text decisions should include page, figure, table, or analysis pointers where possible. Validate every decision event against `schemas/decision_log.schema.json`.

`source_location` may be empty only when no source pointer exists; when that matters, explain the absence in `reason`.

## 7. Full-text sequence and revisions

Follow the scientific order in `PROTOCOL.md`. Operationally, enumerate and assign stable IDs to the experiment's distinct X→Y comparisons; for each comparison, write design facts and A/F decisions first, log the design-based provisional E decision, apply the protocol's result-pattern diagnostic only where required, and then write final E to `experiments_master.csv`. Do not duplicate or reinterpret the scientific definitions here.

Before changing current state:

1. append an event containing field, old value, new value, reason, and source location to `decision_log.jsonl`;
2. update the current-state row.

Never silently overwrite, including clerical corrections.

## 8. Search-result provenance and deduplication

Each `search_log.csv` row identifies an event. A process-triggered event links to its activating `comparison_id` through `trigger_comparison_id`. Each encountered result receives a separate `discoveries.csv` row linked by `search_id`, even when it resolves to an existing paper.

Apply bibliographic deduplication deterministically:

1. Normalize DOI by trimming whitespace, lowercasing, and removing a leading `https://doi.org/`, `http://doi.org/`, `http://dx.doi.org/`, `https://dx.doi.org/`, or `doi:` prefix.
2. Identical non-empty normalized DOI means the same work unless clear contrary evidence is recorded.
3. Without DOI, compare normalized title plus year plus authors. Normalize title for case, Unicode, surrounding punctuation, and repeated whitespace; normalize author strings consistently without guessing identities.
4. Do not automatically collapse uncertain matches. Mark them `possible-duplicate` and keep separate paper records until resolved.
5. Link preprint and published versions as one logical work only when authorship, title/content, and explicit version relationship make the link sufficiently clear.

Every deduplication or merge requires `dedup_reason`/`duplicate_reason` and a decision-log event. A confirmed duplicate points `duplicate_of` to the retained paper ID; history and discovery rows are never deleted.

## 9. Missing texts and manual full-text ingestion

Follow priority and batching rules in `PROTOCOL.md`. At each checkpoint, order unresolved requests by protocol priority and stable paper ID, and surface at most `ask_text_batch_size` records. Mark the request and wave in `missing_texts.csv`; continue independent work.

When the user supplies a requested text:

1. store or reference it under `runs/<RUN_ID>/manual_fulltexts/` using a filename associated with `paper_id`;
2. record the repository-relative path and, where practical, SHA-256 hash;
3. record the actual provision timestamp and wave;
4. append the missing-text status transition before updating current state;
5. evaluate it on `resume`;
6. reopen any citation-expansion or process-search stopping condition activated by the text.

Never backdate availability or imply that the file was available in an earlier wave.

## 10. Deterministic derived files

Run `python tools/derive_outputs.py --run-id <RUN_ID>`; never classify derived files separately. The utility applies only these filters and sorts by `paper_id`, then `experiment_id`, then `comparison_id`.

### Design eligible

`A_code` in `{A-direct, A-validated}` AND `E_code` in `{E-matched, E-diagnostic}` AND `F_code = F-meaningful`.

### Constraint-ready awareness-linked difference

All of: design eligible; `outcome = awareness-linked-difference`; `stats_status = adequate`; `difference_tested = yes`; and, if `Meyen_applicable = yes`, `Meyen_status = Meyen-satisfied`.

### Constraint-ready preserved capacity

All of: design eligible; `outcome = preserved-capacity`; `stats_status = adequate`; `unaware_Y_evidence = positive`; `difference_tested = yes`; `null_evidence_adequacy = adequate`; and, if `Meyen_applicable = yes`, `Meyen_status = Meyen-satisfied`.

`constraint_ready_experiments.csv` is the union of exactly those two comparison routes. `awareness_linked_differences.csv` and `preserved_capacities.csv` are the corresponding comparison subsets.

`inconclusive_experiments.csv` contains design-eligible comparisons with `outcome = inconclusive`; it is not a constraint-ready view. Nominal awareness-linked or preserved results with inadequate statistics remain in the master and design-eligible files only.

## 11. Validation checkpoints

At the end of every search wave:

1. flush all writes;
2. run `python tools/derive_outputs.py --run-id <RUN_ID>`;
3. run `python tools/validate_run.py --run-id <RUN_ID>`;
4. check IDs, counters, cross-file references, schema conditionals, file hashes, and every required why;
5. prepare the bounded ask-text batch;
6. update `run_summary.md` with route/wave progress, counts, unresolved cases, missing texts, validation outcome, and remaining stopping conditions;
7. update `run_state.json` checkpoint timestamp, counters, wave, status, and reason.

Resolve validation failures before another wave. Do not add ad hoc categorical values.

## 12. Independent-run isolation and completion

Do not inspect another run, use its discovered papers, import its classifications, or consolidate. Consolidation/adjudication occurs only after independent runs finish and is outside an executing agent's write scope.

A run is complete only when all frozen routes and activated process searches are done; stopping rules are met; retrievable and manually supplied texts are evaluated; missing-text state is current; files validate; unresolved cases have reasons; derived files are current; and `run_summary.md` documents stopping evidence and validation. Set `run_state.status = complete` only after all conditions hold.
