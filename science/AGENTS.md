# Agent Execution Contract

**Status:** 0.9.13, frozen

Release authorization is determined by `RELEASE_READINESS.json`; freezing these authorities alone does not authorize launch.

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
│   ├── experiment_groups.schema.json
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
│   ├── run_state.schema.json
│   ├── postrun_handoff.schema.json
│   └── postrun_human_decision.schema.json
├── tools/
│   ├── preflight.py
│   ├── init_run.py
│   ├── validate_run.py
│   ├── derive_outputs.py
│   ├── derived_views.py
│   ├── structured_write.py
│   ├── query_instruments.py
│   ├── leakage_guard.py
│   ├── calibration_sampling.py
│   ├── bootstrap_env.py
│   ├── postrun_handoff.py
│   └── postrun_human_decisions.py
├── tests/
├── runs/
└── outputs/
    └── consolidated/
```

Each independent run keeps its scientific records and working files in `runs/<RUN_ID>/`. The sole during-run presentation exception is the coordinator's single-run snapshot under `outputs/handoffs/<HANDOFF_ID>/`, built from that run's validated records under §12. Save its authored draft at `runs/<RUN_ID>/prospect_draft.json`; the builder reads that draft and writes only the presentation snapshot. This exception does not permit another run to be inspected, scientific records to be moved outside their run, or access to `outputs/consolidated/`. The run contains:

```text
runs/<RUN_ID>/
├── papers_master.csv
├── experiment_groups.csv
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
├── bayesian_null_supported.csv
├── supplementary_evidence.csv
├── unresolved_comparisons.csv
├── run_summary.md
└── fulltexts/
```

`experiment_groups.csv` contains one durable row per enumerated physical experiment, including `support-only` and `no-qualifying-comparison` groups. New records have `record_status = active`. If later source evidence establishes that an allocated record is only a procedure part, reanalysis, duplicate inventory entry or other nonphysical bookkeeping error, retain its ID/history and mark it `retired-nonphysical` with a source-located `record_status_reason`. Use `reconciled_into_experiment_id` for a known current same-paper physical group, or null with an explicit reason when no such group exists. No alias chains, self-reference or cross-paper reconciliation is allowed. A retired record cannot own a current comparison, support a current evidence link/cache/joint analysis, earn citation eligibility or supply a supporting-experiment recommendation. Reconcile all current structured references in the same locked append-first transaction; do not automatically transfer scientific judgments. This operation does not retire a real physical experiment merely because it has no qualifying result. A record with current comparisons requires an explicitly resolved comparison-structure correction before retirement; do not delete or renumber comparisons. Report active physical groups separately from retained administrative rows using `current_physical_experiment_groups`. Reopening an erroneously retired record requires a source-backed append-first correction and current checks, never ID reuse.

The experiment-named comparison CSV filenames are retained to avoid unnecessary churn, but every row in `experiments_master.csv` and its derived views is one paper × experiment × X→Y comparison. `comparison_id` is the unique scientific row identifier; `experiment_id` may therefore repeat across comparison rows. Support-only groups never receive placeholder comparison rows. Historical runs remain under their original schema; never silently add lifecycle fields to them.

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

Future pre-freeze clean-room/source-bounded diagnostics must additionally use `--pre-freeze-diagnostic` and a `PREFREEZE_DIAG_*` run ID. `CALIB_*` remains the historical calibration namespace and may not be used for a new diagnostic. This does not rename or migrate any historical run, and ordinary registered-run naming remains unchanged.

Use Python >=3.9 in a POSIX Unix environment and `requirements.txt` as the canonical dependency specification. The canonical setup is `python3 tools/bootstrap_env.py --venv .venv`, followed by `.venv/bin/python tools/preflight.py --mode registered`. The locked writer uses POSIX `fcntl`; this package supports macOS and Unix-like environments. Native Windows is unsupported; use a suitable Unix environment there. Preflight checks the declared runtime and exact installed dependency pins. The bootstrap utility creates an isolated environment when absent and installs the repository requirements without editing them. Do not improvise or mutate dependency specifications during a run. Git is optional in an isolated release; a missing repository commit remains null, while immutable input hashes and the release manifest identify the actual package. See `docs/run_quickstart.md` for the canonical invocation and persistence examples.

Run `.venv/bin/python tools/preflight.py --mode registered` before scientific work. It parses and validates every immutable input, verifies frozen configuration and package/schema versions, and fails on unresolved freeze fields. An explicit `publication_date_policy = unrestricted` permits `publication_cutoff = null`; it means no date filter and must remain null in search records. If dependencies are missing, preflight must exit with the canonical bootstrap command rather than a raw import traceback. The frozen package must pass registered preflight before initialization. `--mode pre-freeze` remains available only for a future explicitly versioned diagnostic revision and never authorizes a registered run.

### Start

Use an isolated release directory created with `tools/package_release.py build`. The builder verifies a pristine distribution: only the operative allowlist, manifest and empty runtime directories. `verify --distribution` repeats that inventory check before distribution. Before invocation, run `tools/package_release.py verify --root <release-directory>`; this runtime check additionally permits the recipient's local `.venv`, generated tool bytecode and own run/output records, while rejecting other extra inputs and symlinked operative paths. Its `RELEASE_MANIFEST.json` fingerprints every distributed input, including derived guidance. Preflight also verifies this manifest when present, so initialization checks the supplied release before recording per-run hashes. The manifest is an integrity check, not a signature or a claim that a Git commit contains uncommitted changes. Never distribute tests, diagnostics, historical runs, output records or this preparation conversation to independent reviewers.

A future pre-freeze diagnostic may obtain isolated inputs before release acceptance using `tools/package_release.py build --pre-freeze-diagnostic`, then `verify --pre-freeze-diagnostic` and `preflight.py --mode pre-freeze`. Its manifest retains the actual blocked readiness and explicitly marks diagnostic purpose; ordinary verification and registered preflight reject it. Invocation requires both `--allow-pre-freeze --pre-freeze-diagnostic` and a `PREFREEZE_DIAG_*` run ID. It is not a reviewer distribution or registered sweep. Final distribution requires a separately built ready release with ordinary verification; never convert a populated diagnostic in place.

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
- Obtained abstract → exact UTF-8 `abstract_text`, SHA-256, source and actual acquisition time in that paper row; verify its hash before reuse.
- Search, query, retrieval, or citation event → `search_log.csv`.
- Every result encountered in that event → `discoveries.csv`.
- Missing-text or manual-ingestion state → `missing_texts.csv`.
- Classification-critical external evidence → `auxiliary_sources.csv`.
- Every verified paper/version and extraction → `fulltext_assets.csv`.
- Every reusable execution-only factual assessment → `evidence_assessments.csv`.
- Every scientific premise assembled from borrowed support → `evidence_bundles.csv`.
- Every explicit scientific use of within-paper, supplementary, same-experiment, or external support → `evidence_links.csv`.
- Every enumerated physical experiment and its pre-atomization disposition → `experiment_groups.csv`.
- Full-text X→Y comparison → `experiments_master.csv`.
- Every decision, revision, merge, status transition, and uncertainty → `decision_log.jsonl`.
- Wave/counter/status checkpoint → `run_state.json`.

Do not reconstruct records from memory at the end. Write a parent record before using its ID elsewhere. `papers_master.csv` fields prefixed `first_` record only the first discovery; they never substitute for `discoveries.csv`.

Registered agents must not construct CSV rows by shell concatenation or raw delimiter joining. Use `tools/structured_write.py` (or its imported schema-aware writer functions) for ID allocation, master-row append/upsert, and decision-log append. One per-run lock serializes counter allocation and all read-modify-write operations. The tool derives field order from the schema, performs typed JSON Schema validation before mutation, applies CSV quoting automatically, and atomically replaces CSV/JSONL files. Its JSONL writer ASCII-escapes embedded Unicode separators and writes exactly one physical LF-terminated record per event. A decision event must still be appended before a current-state upsert.

For bulk persistence, use the writer's `write_batch` or `batch` CLI, with at most 100 CSV mutations and 1,000 decision events per transaction. Reserve IDs beforehand through `allocate_identifiers` (at most 1,000 per call); all reserved IDs remain retired after failure. Each mutation names its table, append/upsert mode, typed record, full expected current row (null for creation), and covering decision IDs. Cover every changed field with exact old/new values or one `record` event binding the complete old/new row. Parent records precede references. The locked writer validates the whole proposal before publication and rejects stale expected state. A hash-bound fsynced journal marks the commit point; decision history publishes first, and subsequent locked access deterministically rolls forward any committed interruption. Run-state updates use covering run decisions and cannot alter immutable identity or allocator counters. Use the examples in `docs/run_quickstart.md`; never bypass this transaction contract with a raw file replacement.

Every title, abstract/abstract-unavailable state, retrieval, auxiliary dependency, full-text asset, factual assessment, evidence bundle/link, citation-expansion, deduplication, comparison structure, A/evidence-type/critical-awareness-result/F/provisional-E/final-E/alternative-control-scan, specifically named unaware-capacity claim, awareness-effect, statistics, Meyen, exclusion, revision, uncertainty, and run-state decision requires a short why. Comparison-level scientific decisions use `entity_type = comparison` and the stable `comparison_id`. Auxiliary evidence, full-text assets, factual assessments, evidence bundles, and evidence links use their corresponding entity types. Experiment-level bookkeeping may use `entity_type = experiment`. Full-text decisions should include page, figure, table, analysis, auxiliary, bundle, link, or asset pointers where possible. Validate every decision event against `schemas/decision_log.schema.json`.

The versioned semantic rescue instrument records paper-specific assertions, source pointers, all nonexclusive rescue signatures, title/abstract/full-text hashes, scientific and review-regime fingerprints, routing reason and ordered manifest hashes. Run its read-only JSON CLI on a frozen batch; persist each `source_bound_inputs` item paired with its `decisions` item as an append-only `decision_log.jsonl` paper event (`field = semantic_route`, `new_value = {source_bound_input, decision}`) before updating its current screen. Persist a subsequent run event (`field = semantic_route_manifest`) with the ordered `route_decision_ids`, `audit_seed`, `min_stratum_size`, `per_stratum`, `reopen_signatures`, `route_manifest`, `demotion_samples`, and `affected_signature_manifests` from that exact batch. The validator recomputes every frozen batch manifest and rejects route decisions omitted from a manifest. At each validation checkpoint, additionally pass **all current latest route decisions across batches** to the instrument's `--mode global-audit` and persist its entire output as a run event (`field = semantic_global_audit_manifest`). The validator rejects a stale cumulative frame. Batch-level samples are bookkeeping only; the cumulative frame defines required demotion audits. A local model's priority is scheduling evidence only; it cannot independently write `screen-out` or `exclude`. Reuse requires the same logical work, unchanged decision-relevant evidence and both fingerprints. Newly obtained evidence requires append-first revision.

Use the frozen config's `demotion_audit_min_stratum_size` and `demotion_audit_sample_per_stratum` as `min_stratum_size` and `per_stratum` in every cumulative audit. These parameters cannot be changed by a batch payload.

Set each route's `scientific_regime_fingerprint` with `tools.execution_contract.scientific_regime_fingerprint(run_state)`: SHA-256 of canonical JSON (sorted keys, ASCII escaping, compact separators) containing `protocol_version`, `package_version`, `schema_version`, and the complete `immutable_inputs_sha256` mapping. Do not substitute an arbitrary label hash. A new frozen package requires a fresh fingerprint and fresh paper-specific scientific review. The separately recorded review-regime fingerprint identifies the reviewer procedure; it cannot substitute for this package binding.

`source_location` may be empty only when no source pointer exists; when that matters, explain the absence in `reason`.

## 7. Full-text sequence and revisions

Follow `PROTOCOL.md` §8 for scientific judgments and conditional checks. Use the brief's seven-step workflow as a reading aid; the storage codes are not additional scientific requirements.

The default handoff is a prospect for human vetting. Before assigning its tentative role, use the existing source-located descriptions/reasons to state the proposed contribution, decisive evidence, remaining alternative and specific human question. Complete the applicable scientific records honestly; do not promote them to make a recommendation pass. A prospect with unresolved premises can be delivered from a valid current snapshot under §12. Strong scientific export claims still require the independent checks below.

Operational sequence:

1. Reserve each physical experiment ID and create its `experiment_groups.csv` row before reserving comparison IDs. Record the functional-structure decision and final group disposition. Support-only and no-qualifying groups retain no invented comparison rows.
   First inventory the supplied article and available supplements: focal experiments, pilots, validation samples, supportive analyses and reported task variants. Distinguish a separate physical experiment from a reanalysis or subset, and distinguish a supporting experiment in this article from validation merely cited from another work. Locate every available classification-critical result before claiming that it is unavailable. Record support-only groups or auxiliary provenance as appropriate; never manufacture an independent replication or a comparison to make an inventory count look complete. A later source-backed nonphysical inventory correction follows the retained-record procedure in §2.
2. When a coherent factorial mapping is required, instantiate the focal comparison before optional components and link each component to that focal row. Completed comparisons retain the explicit structure, identity basis and reason required by the schema.
3. Record located evidence and the comparison-specific scientific judgments in protocol order. Use factual assessments only for reusable source facts, and direct bundles/links for borrowed scientific premises. The corresponding details are required only when that branch applies; record honest not-applicable/not-tested states elsewhere. In the existing descriptions, reasons and notes, keep the information-bearing X, awareness-measured content, conservative mental function Y, measured outcome, and implementing-mechanism proposal distinct. Explain why the outcome supports use of that X for that Y. Locate the actual functional contrast/statistic and its experiment, sample, timing and report order. An arm elsewhere in the paper or a comparison of later discrimination groups does not establish the focal awareness test; conversely, preserve an actual broader test at its own scope rather than saying the paper has no comparison. Use these same records for eventual recommendations instead of another scientific review form.
   Before assigning A, transcribe short source spans for the critical awareness item or instruction and its critical result into the existing awareness description/reason, regime-evidence reason, decision reason/notes and source-location fields. Separately state the focal X and the content actually measured by that awareness item. Apply `PROTOCOL.md` §2.1 exactly: awareness evidence must address the feature, relation or other content X used by Y, and a described procedure is not itself a result. Stimulus, masking, cue or manipulation detail may identify the focal X, but it cannot silently make the awareness item measure more specific content than its wording and result support. If the match remains unresolved, use the applicable existing A code and unresolved/correction-needed promotion disposition; preserve the paper and any narrower or supportive evidence.
   For each focal contrast, fill `awareness_regime_evidence` with one source-located record per relevant arm or graded regime, including exact X, local A code/reason, evidence type and applicable objective-invisibility informativeness, focal-task result, any transferred result and its own linked bundle, objective first-order result, and why. Record explicit `unaware_capacity_regime_keys` for the capacity result; keep comparison-wide A and any uncertain higher arm unchanged. Do not infer one arm from another. Record a partial-X residual effect in its separate descriptive fields without changing formal exact-X capacity.
   Before upserting a strong A, meaningful F, diagnostic E, or supported unaware-capacity claim, append the source-linked `promotion_challenge` decision for each applicable premise. A contradicted or unresolved challenge keeps that premise unpromoted under `PROTOCOL.md`.
4. Before every current-state change, append the decision event with field, old value, new value, source and reason, then upsert through the structured writer. This includes clerical corrections.
5. Complete the relevant result audits, write the scoped empirical constraint and qualitative strength reason, and derive outputs mechanically. A completed audit can leave an inference unresolved.

Before exporting a comparison selected by `scientific_promotion_routes` in `tools/execution_contract.py`, obtain a separate source-focused check as part of the normal full-text work unit. That helper calls the existing predicates for awareness-linked differences, equivalence, Bayesian null support, and supported unaware capacity (including supplementary capacity); it adds no scientific eligibility rule. Record the independent source reading before comparing labels. The checker first receives neutral article/source identifiers, verified source hashes and experiment/source locations, without the primary assessor's proposed A/F labels, proposed reading tier or expected human decision. From those sources, the checker records what content the located awareness item and result actually measure and the most conservative task-level function justified by the located dependent measure, distinguishing that function from the observed effect and proposed mechanism. Its existing reasons also identify which actual source analysis tests awareness's relation to that function, or explain its absence and any narrower comparison that is present. The checker cannot establish correctness merely by agreeing with the primary assessor or a prior user verdict.

Before label disclosure, the same `scientific_source_interpretation.new_value` includes `critical_statistics`: `measured_outcome`, `reported_analysis`, `sample_and_unit`, `inferential_convention`, and `numerical_consistency`. Transcribe the actual source analysis and its unit; distinguish source-reported df/tail from unavailable conventions and named assumptions. `numerical_consistency` contains `status` (`checked`, `not-computable`, or `not-applicable`), a source-specific `reason`, and `calculations`. A checked observation has at least one calculation; noncomputed observations have an empty array and explain why. Each calculation contains `inputs`, `basis` (`source-reported` or `explicit-assumption`), `basis_reason`, and `computed_p`. Use `tools/statistical_consistency.py` for supported ordinary reference probabilities, or record why that tool is inapplicable. It does not infer df from N, choose a tail, interpret a model, or assign a scientific category. A rounded author p is not a computed probability. Floating-point underflow is not proof of an exact zero probability.

When an ordinary test's convention is missing, inspect plausible source-supported interpretations under explicit assumptions if that can clarify the critical inference. Do not silently supply a directional plan, require paired testing for every design, or apply an ordinary t distribution to a z, bootstrap, multilevel or cluster statistic. State whether the unknown convention is material to the scoped claim under PROTOCOL §4.3. An unavailable critical convention remains unresolved; nonfatal reporting uncertainty can retain a qualified result. Keep the literal author result and descriptive estimate, and do not invent original-data covariance or replace its analysis provenance with a reference-distribution calculation.

Only after that source interpretation is durably appended may the checker view and compare the proposed assessment. A second full-paper read is not mandatory, but the primary assessor's summary alone is insufficient. Distinguish the exact focal X from what the awareness question actually tested. A presence/visibility question does not automatically measure a feature used by Y; neither should it be rejected automatically when the source and its sensitivity justify that scope. Explain the actual scope rather than imposing a categorical transfer rule. Similarly, magnitude or intensity of an experienced state is not automatically a degree of awareness of the same X: transcribe what the question asks, identify its content, and justify whether the measured regimes concern that focal content under `PROTOCOL.md` §2.1. Preserve uncertainty if the relation is unclear.

Apply `PROTOCOL.md` §2.4 to the operational X→Y relation: a meaningful task name or real performance outcome is insufficient unless the located measure supports use of the named X. Direct reporting/estimation of X and integration or use of X in a further task can require different interpretations; inspect temporal/task structure and preserve genuine uncertainty, rather than categorically treating every estimate as direct registration or every long task as downstream use. “The exact cognitive or neural mechanism implementing that function need not be identified,” and `mechanism_clarity` “is never part of the F gate.” This execution check does not add a requirement to prove that awareness is an independent cause or establish a causal mechanism beyond the protocol's operational relation. Check each recorded awareness arm/regime, distinct/whole Y, same-Y E when the awareness-constraint route applies, and statistics and limitations. Capacity-only verification does not add an E gate.

Use the existing append-only decision log for this execution check; create no extra scientific table:

- Register each actual worker or human once with a run event `field = scientific_review_role`, whose `new_value` contains `role_id`, `role` (`primary-assessor` or `source-checker`), `actor_id`, `actor_kind` (`agent-worker` or `human`), and `provenance_reference` (the actual worker/task invocation or human review record). These are provenance identifiers, not assertions of model identity or quality. The two roles must have different role IDs and actual actor IDs; relabeling one actor does not make a separate check.
- Before showing the checker any proposed A/F label, append an ordinary comparison decision event with `field = scientific_source_interpretation` and `agent` equal to the actual registered checker actor ID. Compute `scientific_source_reading_binding(source_ids, run_state, typed_tables)` from the verified sources actually read; put its source/version/hash/regime binding in `new_value`, together with `proposed_labels_seen = false`, nonempty `source_locations`, `awareness_measured_content` and `conservative_task_function`. Retain the decisive pointer in the event's `source_location`. The receipt must cover the current verified focal source and the source-bearing direct links actually used for a scientific decision, including every required member of a needed premise and the exact verified source/hash of any linked factual assessment. Use `scientific_promotion_binding(...)["required_source_ids"]` for that source closure; the wider `source_ids` inventory remains conservatively bound but optional unused sources need not be read. Unavailable critical support remains unresolved. Rebinding a comparison or citing only old sources cannot substitute for this current coverage. This is an execution receipt using the existing decision schema, not a new scientific table or eligibility rule. Its claims of actual independent reading remain auditable actor assertions, not proof of comprehension.
- Compute `scientific_promotion_binding(comparison, run_state, typed_tables)` using schema-loaded records. It returns `binding_sha256`, `scientific_regime_fingerprint` and allowed `source_ids`. The binding covers the full comparison, direct bundles/links, linked factual assessments and groups, current focal/supporting assets and auxiliary versions/hashes. Append a comparison event `field = scientific_primary_assessment` containing that binding hash, regime fingerprint and assessor `role_id`; set the event's `agent` to the registered actor ID.
- When the labels are disclosed, append a comparison event `field = scientific_labels_disclosed` by the actual checker actor, with the current `binding_sha256`, `scientific_regime_fingerprint`, `primary_assessment_decision_id` and the prior `source_interpretation_decision_id`. Then append `field = scientific_promotion_review` by that checker. Its `new_value` contains the same binding/fingerprint, both assessment and source-interpretation IDs, `labels_disclosed_decision_id`, `reviewer_role_id`, `disposition` (`confirmed`, `unresolved` or `correction-needed`), `reason`, and `checks`. The validator requires source interpretation before disclosure before review, current source/version/hash bindings, and receipt coverage of every source used by a decisive check. It checks recorded provenance, not hidden label access or scientific truth. Preserve the decisive source pointer in `source_location`.
- `checks.exact_x_awareness_by_arm` contains one item per decisive claim regime returned by the shared policy: every contrast regime for an awareness constraint or primary/support reading claim; only the explicit `unaware_capacity_regime_keys` for ordinary capacity-only promotion. All other regimes remain in the bound scientific inventory with their honest uncertain evidence. Optional inventoried arm checks may record unresolved/contradicted evidence; only decisive claim arms require supported verdicts, while all supplied checks retain normal source/provenance validation. Transferred decisive checks must cover the required critical-result sources of their exact scoped bundle. A capacity-only confirmation does not certify the unreviewed awareness contrast. Each item states `regime_key`, `focal_X` (the current `X_label`), `awareness_tested_content` (independently read from the source), and `critical_awareness_result` separately. Its existing substantive `reason` briefly transcribes the decisive awareness-item/result wording or states why no short decisive span exists; manipulation details remain separate from measured-content specificity. `checks.distinct_whole_y` records the checker's independently stated conservative task-level function separately from the measured outcome and proposed mechanism; its existing reason explains why the outcome supports that function and whether competing uses leave attribution unresolved. `checks.statistics_limitations` is always required; its reason identifies the critical test, comparison scope, temporal/report order and material limitations, distinguishing a same-outcome comparison from a justified same-function comparison. `checks.same_y_e` is required only for a selected awareness-constraint route and states the relevant signal measure or justified scalar prediction, not merely general specificity controls. Every required arm/check contains a `verdict`, substantive `reason`, nonempty `source_locations` and nonempty `source_ids` from the binding. A confirmed review requires `verdict = supported` for every required check. Uncertainty or contradiction receives an unresolved/correction-needed review and a scientific revision under the applicable existing code rather than a forced supported verdict; narrower and supplementary support remains visible. These are strengthened uses of the existing reasons, not additional review tables or fields.

The normal validator and pre-export validation reject missing, stale, nonseparate or unconfirmed reviews for current strong claims. A changed comparison, support premise, source version/hash or frozen regime requires a fresh bound assessment and check. Do not erase the old review. Log and upsert any scientific correction through the normal append-first writer; retain support, partial-X observations and uncertainties under the existing predicates. Once a logged downgrade no longer makes a strong claim, that historical unresolved check does not prevent ordinary supplementary/support export. No checker changes a scientific code merely to satisfy this execution gate.

Every optional certified primary or valuable-support reading recommendation also requires this separate current scientific source review, including a weak-E or transfer-risk comparison outside the strong export routes. The handoff calls the same helper with `required_comparison_ids`; this adds a recommendation obligation and does not change any scientific export or process-search predicate. Reuse the source-first interpretation and current independent comparison review when unchanged.

The existing `checks.statistics_limitations` also contains `focal_analysis_scope = statistical_review_scope(comparison)` from `tools/execution_contract.py`, `source_statistics` identical to the prior source-only `critical_statistics`, and `materiality` (`supports-scoped-claim`, `nonfatal-qualified`, or `critical-unresolved`). Its ordinary verdict/reason/source pointers still apply. The scope records the focal comparison, Y and actual native critical analyses; it cannot be copied from another comparison. The checker explains the mapping from independent source observations to that analysis and why a qualification is critical or nonfatal. A confirmed review cannot contain `critical-unresolved`. These execution checks verify scope, chronology and recorded arithmetic; they cannot prove source comprehension or the truth of an attribution. Use source-linked revisions for genuinely corrected source facts. A source-first receipt must precede that actual actor's first recorded label/primary-assessment/promotion-review exposure for this comparison. If new critical sources or corrected source facts require a fresh source-only reading after exposure, use a new independent actor; the exposed actor may record an honest unresolved postlabel review but may not assert a new blind receipt and confirm it. A new role name for the same actor does not erase recorded exposure. These receipts document actual source and exposure assertions, not a confidentiality or comprehension guarantee.

For an optional certified primary/support recommendation, after reviewing the exact authored recommendation, that same independent checker appends `field = scientific_reading_claim_review` for its selected comparison. Compute `scientific_reading_claim_binding(item, comparison, run_state, typed_tables)`; its `binding_sha256`, `scientific_regime_fingerprint` and `claim_sha256` bind the full current scientific evidence and exact authored tier, basis, X/Y, outcome, direction, claim, limitation, source location and editorial reasoning. The event's agent and the item's `reviewed_by` name the registered checker actor. Its payload references the current `scientific_promotion_review_decision_id`, gives `disposition` (`confirmed`, `unresolved`, `correction-needed`), a reason, and two located checks. Each contains verdict, reason, source IDs actually covered by the prior source-only reading, and source locations. `checks.same_function_awareness_comparison` records `awareness_comparison_established` as a boolean, the actual `statistic_or_test`, `analysis_scope` and `source_experiment_id` from the current row; it explains why the compared regimes concern awareness rather than objective ability alone. `checks.claim_scope` states X, Y, measured_outcome and result_direction exactly as reviewed and explains the scoped warrant, including why any causal, mechanism, duration or equivalence wording is justified or must be removed. A confirmed recommendation requires both checks supported and an established actual awareness comparison. These records use the existing decision log; no new paper-classification table or truth-by-hash inference is permitted.

Both provisional and final handoffs run full native record validation and the checks applicable to the authored recommendation type. A provisional handoff permits open discovery frontiers; it does not waive scientific validity. Default `profile-prospect` items bind their current comparison/source and explicit evidence/question without requiring confirmed promotion or certified exact-claim reviews. If a current scientific record independently makes a strong export claim, its existing promotion checks still apply. Optional certified primary/support items retain the exact claim checks: changed wording needs a new check, unchanged facts need no second full-paper read, and a newer unresolved/correction-needed check blocks reuse of an older confirmation. Claim review never records human acceptance.

Neutral checker handoffs include the complete source identity inventory: active focal and supporting experiments, task variants, reanalyses and any retained retired administrative entries explicitly distinguished from physical experiments. Map each reserved comparison ID to its raw measured outcome and actual analysis/source location so the checker never infers an ordinal from a generic location. Do not disclose proposed X→Y interpretations, A/E/F, tier or expected verdict in that mapping. An incomplete packet must be corrected before the source-interpretation receipt; existing native records must not be re-enumerated merely because a packet omitted them.

Before proposing a rule change, classify the observed failure: incomplete source intake, source interpretation, claim-scope mismatch, lost/stale state, or genuine policy ambiguity. Correct factual and execution errors under the existing rule; preserve an honest unresolved judgment when needed. Tentative primary/support disagreement is not a failed prospect and does not justify changing the frozen science.

Do not duplicate scientific thresholds here. The schema validates the record; `PROTOCOL.md` determines its scientific interpretation.

## 8. Search-result provenance and deduplication

Each `search_log.csv` row identifies an event. A process-triggered event links to its activating `comparison_id` through `trigger_comparison_id`. Each encountered result receives a separate `discoveries.csv` row linked by `search_id`, even when it resolves to an existing paper.

For every adequately evaluated physical experiment, record the three discovery ingredients (`citation_specific_x`, `citation_awareness_attempt`, and `citation_functional_y`) independently as `present`, `failed`, or `unclear`; use `not-assessed` only before assessment. A strict bridge group requires exactly two `present`, one `failed`, `bridge_near_neighbor = yes`, the matching failed-ingredient value, and a substantive positive rationale. Never aggregate ingredients across experiment groups. Derive the paper's current `citation_node_status` from its groups and empirical/full-text state: CORE has precedence over BRIDGE; missing/insufficient text is `not-assessable-missing-fulltext`; an adequately assessed paper with neither is `not-node`. No bridge requires or permits a dummy comparison.

Every discovery encounter records bridge-lineage depth 0 or 1 and why. Every backward/forward citation search records the parent, direction, source, parent node status, parent bridge depth, and whether a fixed empirical seed, CORE, strict BRIDGE, a review anchor, or a provisional CORE decision enabled traversal. A strict bridge parent may expand only from depth 0. Its children have depth 1 unless a child's eventual CORE status resets subsequent traversal to depth 0. A bridge first reached at depth 1 remains ineligible on that lineage, but any later depth-0 rediscovery adds a durable eligible obligation. Track depth-0 eligible, pending, and completed bridge-parent IDs in `run_state.json`; never base the decision solely on first-discovery fields. Reuse an identical completed paper/source/direction window rather than fetching it again, while retaining each rediscovery row. Bridge windows inherit the ordinary citation-source/fallback policy; do not hard-code a diagnostic source.

`PROTOCOL.md` §9.1 begins citation discovery from the frozen empirical seeds, independently of the rule for newly discovered empirical nodes. For that initial fixed-seed traversal use `citation_traversal_basis = fixed-empirical-seed`, `citation_parent_node_status = fixed-empirical-seed`, and `citation_parent_bridge_depth = 0`. The parent must resolve to an identity in `seeds_empirical.csv` and have a previously recorded depth-zero encounter through an `empirical-seed` search event. This search-record basis does not set the paper's `citation_node_status` to CORE, establish awareness evidence, create comparisons, or activate process searches. Missing abstract/full text does not erase the fixed seed's discovery role. Its children enter ordinary screening at bridge-lineage depth 0; any later recursive eligibility follows the unchanged protocol. Keep the normal citation source, exhaustion, snapshot and fallback policy.

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

At steps 4, 7, 13, and 15, include every pending eligible one-hop bridge expansion in the citation frontier. A bridge-discovered CORE node reopens ordinary CORE recursion. A blind- or process-discovered BRIDGE node at depth 0 creates or reopens its bridge obligation. Bridge status alone never adds an activated normalized Y. Do not add resource-dependent caps, bridge-parent quotas, or a zero-yield bridge-generation stopping rule.

The blind lane may not be skipped because the principal routes appear productive or saturated, known anchors were recovered, or available time/token budget seems sufficient. A blind-lane discovery that is independently citation-eligible reopens the citation frontier; a genuinely new independently qualifying Y activates or reopens its bounded process search. Record every transition and do not mark the run complete while any reopened frontier remains open.

Before durably recording activation, the locked writer validates the triggering comparison and its scientific premises with the same native regime/bundle validators used at checkpoints; an asserted strong local A cannot earn activation from an incomplete required bundle. Before activating a process window, apply `process_search_eligible` from `tools/derived_views.py` to the triggering current comparison and log the route and scientific reason. Append one comparison decision with field `process_search_activation` and the payload returned by `process_activation_payload` in `tools/execution_contract.py`: a normalized Y label, normalization reason, `new-y` or `same-y-reuse` kind, and the complete typed eligible comparison snapshot. Append this event before adding its label to `activated_normalized_y_labels` or starting a window. Both the batch and standalone decision writers check the typed trigger, recorded comparison snapshot and activation/reuse kind before persistence; a rejected transaction leaves all current records and history unchanged, while reserved IDs remain retired. Every independently eligible comparison receives its own normalization/activation or same-Y reuse decision; a previously activated function reuses its existing obligation rather than retriggering a completed window. Completion reconciles current earned comparisons, original trigger snapshots and all historical activations, so omission of a qualifying function cannot silently satisfy the frontier. Preserve the activation decision and its source windows if later evidence revises the comparison; do not falsify prior search provenance.

Every independent or process query window is an immutable retrieval snapshot identified by its execution phase, source, family or normalized Y label, canonical query, source parameters, publication cutoff, requested N, and deterministic window key. A completed window records the ordered result-set hash and retrieval time. Resume reuses a completed snapshot only when the entire key and ordered hash still match durable discoveries; it never silently reruns, extends, reranks, or substitutes a window. A missing, partial, or inconsistent snapshot remains incomplete and must be explicitly resolved.

The blind lane executes every family in the frozen config: eleven prepared families, on OpenAlex and Europe PMC, one N≤40 window per source/family, no second page and no quota redistribution. The historical QCAL4-LEARN rendering stays retired; the redesigned QCAL5-LEARN is distinct. QDYN remains one N≤50 window per source/earned Y, with documented lexical provenance and bounded new-Y recursion.

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

Title and abstract screening are paper-specific semantic decisions under `PROTOCOL.md`, even when records are presented in batches. Title batches contain at most 25 logical works and abstract batches at most 10. Batch membership is context amortization only: write one durable decision and one paper-specific reason per logical work. A prior decision may be reused only for the same logical work, same scientific regime fingerprint, and unchanged decision-relevant evidence. Genuinely new evidence permits revision only through an append-first decision-log event followed by the current-state update. Regex, keyword, embedding, citation-count, numeric relevance, and hidden lexical heuristics may not independently produce `exclude` or `screen-out`; this candidate registers no deterministic scientific exclusion rule.

Before finalizing a semantic screen-out, apply the current versioned rescue instrument to the available paper-specific evidence. Any triggered rescue receives strongest-agent or human-grade semantic review with a paper event (`field = semantic_rescue_review`) naming the route evidence-binding hash, reviewer, `retain|unresolved|screen-out` disposition, source and why; a missing abstract remains unresolved under §9.1. Preserve separate axes for an awareness-linked constraint, exact-X whole-Y unaware capacity, partial-X residual evidence, and other support. For each large **cumulative** demoted route stratum, freeze a deterministic hash-random sample within each risk-defined stratum before review; record optional purposive risk cases separately. Each sampled paper gets a `semantic_demotion_audit` event naming its evidence-binding hash, frozen stratum, reviewer, source, `retained|unresolved|screen-out|false-negative` disposition and why. A reproducible false negative records its signature; rerun `--mode global-audit` with that `reopen_signatures` value over every current route decision, freezing all affected IDs across batches. Give each affected paper a source-bound `semantic_affected_review` event after that freeze; only then append `affected_signature_review_complete` with every reviewed ID and the exact frozen frame hash. An unknown signature requires a versioned routing repair and fresh validation rather than an empty frame. Review a boundary-neighbor sample too. Unaffected strata remain separately documented. Do not describe purposive risk cases as a population recall estimate. An audit sample alone never creates scientific exclusion or a new resource-based stopping rule.

### 9.3 Auxiliary evidence sources

Record each reusable external logical work/version in `auxiliary_sources.csv`. Store its bibliographic and retrieval identity once; do not duplicate it for each target comparison. Every scientific use, transfer judgment, limitation, and dependency role belongs in the target comparison's evidence bundle and link. Auxiliary rows do not create `papers_master.csv` or `discoveries.csv` records unless the work is independently encountered through an ordinary discovery event, so support-only evidence cannot leak into the candidate pool.

Register each separately stored supplement used for a classification-critical premise as a reusable auxiliary source/version with its actual attachment identity, parent-article relation, acquisition provenance and immutable file hash. Directly link it to each focal premise using `supporting_source_type = supplementary-analysis`, its corresponding paper ID and auxiliary ID. Multiple attachments sharing a parent DOI need distinct truthful attachment/version identities. Name an actual experiment only when the analysis belongs to it; do not invent an experiment or candidate paper for an attachment. Include the auxiliary ID in the prior independent source reading and decisive checks. A pathname in `source_location`, or a noncurrent article asset, cannot supply that binding. This representation of separate bytes does not make the scientific result external or establish transfer across populations; the link states its actual scope.

### 9.4 Evidence bundles

Create one `evidence_bundles.csv` row for one named premise of one focal comparison. Its `required_member_keys` manifest names every member logically required before any result is known, so an omitted required link is auditable as incomplete. The same source used for two premises or comparisons requires distinct bundles and explicit direct links. Each `evidence_links.csv` row receives its own stable ID and unique bundle-local `member_key`, and records one member, supported claim, dependency role (`required`, `strengthening`, `robustness`, `generalization`, or `mechanistic`), member status, transfer reason, limitation, and source location. Links to external sources resolve to reusable auxiliary rows; within-paper supporting experiments need no candidate comparison row.

Bundle status is derived, not asserted opportunistically: `conflicted` when any direct member contradicts or is conflicted; otherwise `incomplete` when any required member is absent, unavailable, unevaluated, or transfer-invalid; otherwise `complete` when at least one decision-used member supports the premise and every required member supports it. No scientific conclusion may depend on an incomplete or conflicted bundle. Evidence transfer is premise-specific and must justify population, manipulation, measure, analysis, and version compatibility where relevant. Each regime's `transfer_bundle_id` resolves to a declared awareness-A premise bundle whose `awareness_regime_keys` explicitly includes that regime. A shared bundle may support multiple regimes only with located critical-result coverage and explicit transfer for every declared regime. Independent complete alternatives may name the same regime without being its active pointer; validate each bundle's scope/coverage and resolve the selected pointer separately. A pointer change is logged and stales its bound review; unrelated complete bundles never substitute. A complete `awareness-A` transfer bundle must include at least one required, decision-used `critical-result` member; a `procedure-description` member alone cannot complete strong A. Evidence links are direct only: no transitivity, no inference from sharing a source or bundle, and no propagation of a conclusion from one comparison to another.

### 9.5 Execution-only evidence assessments

`evidence_assessments.csv` is a factual execution cache, never a scientific bundle or classification store. Reuse requires the same logical source/version, source-asset hash, factual premise, source location, and exact scientific-regime fingerprint. It may cache such facts as task structure, measure identity, reported analysis, or quoted result, but it must not contain or propagate A/E/F codes, route outcomes, eligibility, Meyen conclusions, or comparison-level scientific judgments. Every target comparison still requires its own explicit scientific bundle/link and decision.

### 9.6 Verified full-text assets

Record one verified `fulltext_assets.csv` row per logical paper/article version, with stable source identity, immutable file hash, verification reason, and—when created—extraction tool/version, extracted-text hash, and page-map hash. Reuse that verified asset and extraction across comparisons within the same paper/version. Never redownload or re-extract an unchanged verified version merely because another comparison needs it. A materially different article version receives a new immutable asset row; current-version changes are logged, never overwritten silently.

## 10. Deterministic derived files

Run `python tools/derive_outputs.py --run-id <RUN_ID>`; never classify derived files separately. The utility applies only these filters and sorts by `paper_id`, then `experiment_id`, then `comparison_id`.

Before export, the utility validates the compatible master snapshot, including evidence bundles and references, under the per-run write lock. It does not require old derived files to be current in order to regenerate them. Full validation then compares every derived view with the exact expected membership, content, and order from the master, rejecting stale views.

The output predicates are implemented once in `tools/derived_views.py` and follow `PROTOCOL.md` §§3–5 and §12. Do not classify an export independently or apply extra gates in an execution prompt.

The generated views are design-eligible comparisons, main constraint-ready comparisons, awareness-linked differences, unaware capacities, descriptive no-detectable differences, equivalence, Bayesian null support, supplementary evidence, and unresolved comparisons. Compatible views may overlap. In particular, a capacity export is not a claim of equivalence, and supplementary findings remain visible in synthesis.

The validator checks each export against its source records and the same predicates. Use `tools/scientific_policy.py` for shared route/provenance checks rather than maintaining a second implementation.

## 11. Validation checkpoints

At the end of every search wave:

1. flush all writes;
2. run `python tools/derive_outputs.py --run-id <RUN_ID>`;
3. run `python tools/validate_run.py --run-id <RUN_ID>`;
4. check IDs, counters, cross-file references, schema conditionals, file hashes, and every required why;
5. check every declared bundle against its derived status, every direct member/reference and strict transfer record, every execution-cache fingerprint and source hash, every full-text version/hash, and that no support-only source silently entered the candidate pool;
6. prepare the bounded ask-text batch;
7. update `run_summary.md` with route/wave progress, counts, unresolved cases, missing texts, validation outcome, and remaining stopping conditions;
8. update `run_state.json` checkpoint timestamp, counters, wave, status, and reason; and
9. author or update the default prospect handoff from the validated snapshot. Address each newly assessed candidate's relevance in its existing source-linked reasons; add the defensible prospects and specific unresolved questions, and document why known nonmatching evidence remains context or outside the queue. Reconcile every prior queue item against current sources and explicit human decisions: retain it, revise it with a reason, or visibly record its disposition. Never rebuild from only the latest selected subset and silently lose earlier prospects. No settled primary/support judgment is required for this checkpoint delivery.

Also verify that every triggered rescue has a completed or explicitly unresolved paper-specific disposition, every required demotion stratum has a frozen frame and executed audit, and every confirmed false-negative signature has a complete affected-stratum review or an open obligation. Verify arm/regime awareness sources against the comparison's A code and evidence links. Reading recommendations must resolve to current source assets and comparison decisions, but their editorial tiers cannot alter derived scientific predicates.

Every current strong awareness-linked constraint or supported unaware capacity must also have the confirmed, separate, current-source `scientific_promotion_review` described in §7 before export. Preserve unresolved reviewer findings and any resulting source-linked correction in the decision history.

Resolve validation failures before another wave. Do not add ad hoc categorical values.

For CALIB003 only, after title/abstract screening, select at most 12 newly discovered `screen-in` candidates with `tools/calibration_sampling.py`: sort by full-text priority (`high`, `medium`, `low`), then earliest durable first-discovery ID, then `paper_id`, and take the first 12 (or all if fewer). Expected A/E/F/outcome must not enter selection or tie-breaking. Attempt retrieval for all selected papers, fully evaluate every obtained text, and apply normal missing-text handling to the rest. This bounded sampling rule is not the registered sweep rule; a registered sweep evaluates every retrievable paper passing its full-text threshold.

## 12. Independent-run isolation and completion

Do not inspect another run, use its discovered papers, import its classifications, or consolidate. Consolidation/adjudication occurs only after independent runs finish and is outside an executing agent's write scope.

A run is complete only when: the principal frontier was provisionally satisfied; every required eligible one-hop bridge expansion is complete; every mandatory blind window is complete and hash-consistent; every blind-triggered citation or new-Y process frontier has been reopened and subsequently satisfied; all frozen routes and activated process searches are done; stopping rules are met; retrievable and manually supplied texts are evaluated; missing-text state is current; no scientific conclusion depends on an incomplete/conflicted bundle; route audits and result-inspection dispositions are complete; files validate; unresolved cases have reasons; derived files are current; and `run_summary.md` documents stopping evidence and validation. Set `run_state.status = complete` only after all conditions hold.

Record the existing zero-new-potentially-relevant citation-wave stopping condition as an append-only run decision with `field = citation_saturation`. Its `new_value` is an object with exactly `wave` (the completed citation wave), `search_ids` (sorted IDs of every completed/reused backward/forward window in that wave), and `new_paper_screening_decisions` (a mapping from each logical paper first encountered in those windows to its source-bound `title_screen = exclude` or `abstract_screen = screen-out` decision ID). An empty map is valid only when there were no new logical works. Append this snapshot after the windows and screening decisions, with a source pointer and reason. Refer to decisions made at that wave, never infer historical exclusions from later current rows. A later relevant revision or reopened citation wave requires a new snapshot. This record documents the protocol stopping rule; it does not add an exclusion rule. Before completion, the validator also reconciles every frozen seed's logical identity and seed encounter, required fixed-seed/CORE/provisional-CORE/depth-zero-BRIDGE backward/forward windows, and pending paper screening/expansion states.

At each validated checkpoint, the coordinator must author and deliver or refresh the source-linked **prospect queue** from current comparison records. The default `profile-prospect` uses `claim_review = unresolved` and names `claim_basis`, `claim_comparison_id`, `measured_outcome`, `decisive_evidence`, `human_question`, `tentative_role` and `prospect_relation` under `PROTOCOL.md` §12. The contribution, evidence and limitation precede the tentative primary/support/undetermined annotation. Reuse source asset IDs, located reasons and scientific records; do not create another classification table, copy an earlier tier, or require human adjudication before continuing autonomous discovery. Source-grounded uncertainty can remain a prospect; known lack of the relevant comparison or downstream function remains context. Optional certified primary/support recommendations retain the source and exact-claim checks in §7.

`tools/postrun_handoff.py` validates and renders this presentation without choosing scientific codes or changing run files. A provisional guide permits open frontiers and unfinished prospect assessments under native validation. A final guide still requires completed, validated input runs; a delivered guide never closes search or text obligations. Multi-run handoff additionally requires completed external adjudication, and only a post-run coordinator may inspect independent runs together. Source/comparison revisions invalidate affected presentation bindings; preserve old guides as history and reuse unchanged source work. See `docs/run_quickstart.md` and `docs/postrun_handoff.md`.

The user's manuscript choices initialize the human-vetted golden primary/support list. Pipeline recommendations never add to it automatically; only an explicit user post-reading decision does. `tools/postrun_human_decisions.py` records those authorized append-only events and derives the current accepted view; it is never invoked by the handoff builder. Do not prepopulate a human decision event or infer acceptance from an editorial tier. The recommendation can be completed while human acceptance remains pending; human acceptance is independent of scientific run completion. Record rejection or revised placement explicitly and derive the current view without erasing historical judgments. A delivered reading list does not by itself complete an unfinished registered run, change its science, or launch a deeper/new-model sweep.

The handoff reads any existing explicit events at `outputs/human_review/decision_log.jsonl` without appending to them. It displays the latest recorded role and article version separately from the scientific recommendation, removes previously accepted/declined items from the first-read queue, and includes that history in its input manifest. In a combined-run guide, use the latest append-order event under the adjudicated identity or any native work key explicitly mapped to that same identity; do not guess aliases. A new human event invalidates the old presentation view; rebuild the guide using the unchanged source checks where still current. A prior decline remains visible even when a source version changes; its reason and scope must accompany any later discussion. Reopening or acceptance requires a new explicit human decision. Do not turn an explicit rejection into an unqualified conditional prospect or silently restore it to the first-read queue. Runtime package verification permits the documented handoff files under `outputs/handoffs/<ID>/` and canonical human-review outputs, while pristine distribution verification continues to reject all populated runtime records.

Across independent registered runs, agents share only immutable static package inputs: frozen seed and review-anchor identity, normalization rules, schemas, queries, protocol, and agent instructions. They do not share semantic screening decisions, dynamic result sets, A/E/F codes, evidence links or assessments, statistical/Meyen judgments, process-Y or saturation judgments, full-text annotations, or run outputs. No dynamic query result is precomputed for distribution across agents. If one harness uses multiple workers inside a single independent run, it may divide already-reserved, non-overlapping execution units only; all writes still pass through that run's locked structured writer and the coordinator reconciles durable state before checkpoints.
