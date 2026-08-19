# Agent Execution Contract

**Status:** draft-0.7.1, pre-freeze

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

Assign each ID once; never recycle or renumber it. Allocate every post-initialization ID through the locked allocator in `tools/structured_write.py`; workers must not infer a next identifier by reading a table or `run_state.json`. Allocation atomically advances durable state before returning the reserved ID, so a crash may retire an unused ID but may never permit reuse. On resume, each next counter must exceed the greatest durable identifier already present. Per-paper experiment counters and per-experiment comparison counters are stored as mappings or recovered equivalently from durable IDs. Multiple rows may share an `experiment_id`, but `comparison_id` must be unique.

## 6. Current state, complete provenance, and continuous writes

Master CSVs hold current state. `decision_log.jsonl` is append-only history. `discoveries.csv` is complete search-result provenance: one row for every paper result actually encountered through a logged search or citation event, including every rediscovery.

Write continuously:

- Newly encountered logical paper → `papers_master.csv`.
- Search, query, retrieval, or citation event → `search_log.csv`.
- Every result encountered in that event → `discoveries.csv`.
- Missing-text or manual-ingestion state → `missing_texts.csv`.
- Classification-critical external evidence → `auxiliary_sources.csv`.
- Every borrowed within-paper, supplementary, same-experiment, or external premise → `evidence_links.csv`.
- Full-text X→Y comparison → `experiments_master.csv`.
- Every decision, revision, merge, status transition, and uncertainty → `decision_log.jsonl`.
- Wave/counter/status checkpoint → `run_state.json`.

Do not reconstruct records from memory at the end. Write a parent record before using its ID elsewhere. `papers_master.csv` fields prefixed `first_` record only the first discovery; they never substitute for `discoveries.csv`.

Registered agents must not construct CSV rows by shell concatenation or raw delimiter joining. Use `tools/structured_write.py` (or its imported schema-aware writer functions) for ID allocation, master-row append/upsert, and decision-log append. One per-run lock serializes counter allocation and all read-modify-write operations. The tool derives field order from the schema, performs typed JSON Schema validation before mutation, applies CSV quoting automatically, and atomically replaces CSV/JSONL files. Its JSONL writer ASCII-escapes embedded Unicode separators and writes exactly one physical LF-terminated record per event. A decision event must still be appended before a current-state upsert.

Every title, abstract/abstract-unavailable state, retrieval, auxiliary dependency, evidence link, citation-expansion, deduplication, comparison structure, A/evidence-type/F/provisional-E/final-E, specifically named unaware-capacity claim, awareness-effect, statistics, Meyen, exclusion, revision, uncertainty, and run-state decision requires a short why. Comparison-level scientific decisions use `entity_type = comparison` and the stable `comparison_id`. Auxiliary evidence uses `entity_type = auxiliary_source`; evidence links use `entity_type = evidence_link`. Experiment-level bookkeeping may use `entity_type = experiment`. Full-text decisions should include page, figure, table, analysis, auxiliary, or evidence-link pointers where possible. Validate every decision event against `schemas/decision_log.schema.json`.

`source_location` may be empty only when no source pointer exists; when that matters, explain the absence in `reason`.

## 7. Full-text sequence and revisions

Follow the scientific order in `PROTOCOL.md`. Operationally, enumerate the physical experiment groups first and reserve each experiment ID before reserving any comparison IDs. Then enumerate scalar or coherent factorial X→Y comparisons. For each comparison, check `critical_dependency_status`, reserve an evidence bundle when support is borrowed, record every evidence link before relying on it, write design facts and A/F decisions, log provisional E, record the complete structured E-diagnostic rationale where applicable, name the exact focal or component function in `unaware_capacity_claim`, and only then write independent unaware-capacity and awareness-effect decisions. A supporting experiment receives an experiment pointer in an evidence link but no comparison row unless it independently answers an X→Y question. The allocator must reject a comparison whose experiment group has not already been reserved. Do not duplicate or reinterpret the scientific definitions here.

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

Title and abstract screening are paper-specific semantic decisions under `PROTOCOL.md`, even when records are presented in batches. Record the screening method and a separate reason for every paper. Keyword or regex signals may order work for efficiency, but may not independently produce `exclude` or `screen-out`. A deterministic exclusion is permitted only when its exact rule is preregistered and the row records that rule identifier; the default method is `agent-semantic`.

### 9.3 Auxiliary evidence sources

Record each explicit classification-critical dependency in `auxiliary_sources.csv` before finalizing the affected comparison. The row must identify its purpose, target paper/comparison, source pointer in the target article, retrieval/acquisition provenance, transfer assessment where applicable, and whether it was used. A resolved dependency requires a retrieved linked auxiliary row used for the decision. An unresolved dependency requires a linked row documenting why it could not be resolved. Auxiliary rows do not create `papers_master.csv` or `discoveries.csv` records unless the work is independently encountered through an ordinary discovery event.

### 9.4 Evidence bundles

Reserve an `evidence_bundle_id` once per focal comparison when it borrows support. Each row in `evidence_links.csv` receives its own stable `evidence_link_id` and records exactly one supported claim, role, transfer reason, limitation, and source location. A link to an external auxiliary source must reference the corresponding `auxiliary_id`. A within-paper supporting experiment may be referenced without creating a comparison row. Validators require every non-null comparison `evidence_bundle_id` to have at least one matching link and every link to target an existing focal comparison.

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
5. check that every resolved/unresolved dependency and non-null evidence bundle has the required linked records, that external links resolve to auxiliary rows, and that no support-only source silently entered the candidate pool;
6. prepare the bounded ask-text batch;
7. update `run_summary.md` with route/wave progress, counts, unresolved cases, missing texts, validation outcome, and remaining stopping conditions;
8. update `run_state.json` checkpoint timestamp, counters, wave, status, and reason.

Resolve validation failures before another wave. Do not add ad hoc categorical values.

For CALIB003 only, after title/abstract screening, select at most 12 newly discovered `screen-in` candidates with `tools/calibration_sampling.py`: sort by full-text priority (`high`, `medium`, `low`), then earliest durable first-discovery ID, then `paper_id`, and take the first 12 (or all if fewer). Expected A/E/F/outcome must not enter selection or tie-breaking. Attempt retrieval for all selected papers, fully evaluate every obtained text, and apply normal missing-text handling to the rest. This bounded sampling rule is not the registered sweep rule; a registered sweep evaluates every retrievable paper passing its full-text threshold.

## 12. Independent-run isolation and completion

Do not inspect another run, use its discovered papers, import its classifications, or consolidate. Consolidation/adjudication occurs only after independent runs finish and is outside an executing agent's write scope.

A run is complete only when all frozen routes and activated process searches are done; stopping rules are met; retrievable and manually supplied texts are evaluated; missing-text state is current; files validate; unresolved cases have reasons; derived files are current; and `run_summary.md` documents stopping evidence and validation. Set `run_state.status = complete` only after all conditions hold.
