# Draft 0.8.5 execution-invariants report

## 1. Starting state

- Starting commit: `742bf0b7d62d73853913da2ef1e932f7afc10996` (`Checkpoint pre-freeze draft-0.8.4`).
- Starting worktree: clean.
- Starting versions: protocol `draft-0.8.4`, package `prefreeze-package-0.8.4`, schema `prefreeze-schema-0.8.3`.
- Scope: final pre-documentation execution/representation revision only. No search, retrieval, new diagnostic run, registered sweep, freeze, tag, or commit was performed.

## 2. Pilot 004 archive and verification

- Archive: `diagnostics/cleanroom_pilot_004/`.
- Complete archived run: `diagnostics/cleanroom_pilot_004/run/`.
- Preserved source manifests: `diagnostics/cleanroom_pilot_004/fixture_provenance/`.
- Provenance README contains the recovered exact minimal prompt, exact package commit/versions, fixed seven-file fixture, no-network/hidden-context statement, run/model/harness metadata, timestamps, and registered-input prohibition.
- Recursive `diff -qr` against the source run passed; both source clean-room manifests passed `cmp`.
- All 58 manifest-listed archive files passed `shasum -a 256 -c`; the archive contains 59 files including `SHA256SUMS` itself.
- `SHA256SUMS` hash: `2c9e2fe08673ad52be9e40dbbe7287a790c3de5945247efd3c8e216d0c540854`.
- Archive permissions were made read-only after verification.
- Archived classifications were not edited.

## 3. Pilot adjudication

The detailed adjudication is `diagnostics/cleanroom_pilot_004_adjudication.md`. All four proposed lessons were confirmed from actual records:

1. Two valid support-only physical-experiment decisions (`P000001_E05`, `P000004_E03`) caused the only final validator errors because experiment targets were inferred from comparison rows.
2. The old combined A-result field allowed `supportive-result-reported` while the description itself said exact critical values were not reported.
3. Direct-difference rows lacked structured focal experiment/location/test ownership, so cross-experiment E support could not be mechanically distinguished from a focal statistic.
4. Exact capacity-label identity could be satisfied with a broad effect description, allowing interference/performance modulation to masquerade as a downstream functional capacity.

The adjudication applies the requested A–G categories and audits comparison discovery, physical groups, support-only disposition, X/Y, functional identity, A, E, F, bundles, difference provenance, capacity, null/equivalence, statistics, and constraint-ready outputs across all six anchors.

## 4. Files changed

Registered-facing package:

- `AGENTS.md`, `PROTOCOL.md`, `config.yaml`.
- New `schemas/experiment_groups.schema.json`; revised `schemas/experiments.schema.json`.
- `tools/derive_outputs.py`, `tools/execution_contract.py`, `tools/init_run.py`, `tools/leakage_guard.py`, `tools/preflight.py`, `tools/structured_write.py`, `tools/validate_run.py`.
- `tests/test_pipeline.py`, `tests/test_anchor_non_regression.py`, `tests/test_revision_083.py`, `tests/test_revision_084.py`; new `tests/test_revision_085.py`.

Diagnostic-only additions:

- `diagnostics/cleanroom_pilot_004/`.
- `diagnostics/cleanroom_pilot_004_adjudication.md`.
- This report.

No seed, query, requirement, historical run, prior diagnostic archive, manuscript, or output-consolidation file was modified.

## 5. Version changes

- Protocol: `draft-0.8.4` → `draft-0.8.5`.
- Package: `prefreeze-package-0.8.4` → `prefreeze-package-0.8.5`.
- Schema: `prefreeze-schema-0.8.3` → `prefreeze-schema-0.8.4`.
- Registration status remains `pre-freeze`.
- Historical runs are not migrated; compatibility refusal remains mandatory.

## 6. Experiment-group architecture

`experiment_groups.csv` is initialized for every new run and validated by the strict new schema. It records one physical experiment's identity, source, description, pre-atomization state, functional-structure audit, disposition/reason, linked comparison IDs, and optional support roles/notes.

`experiments_master.csv` remains the scientific paper × experiment × X→Y comparison table. The atomic scientific unit is unchanged.

The initializer creates both tables. The writer exposes the group table through the same locked schema-aware path. Resume recovers experiment counters from `experiment_groups.csv`, not comparison rows. The comparison allocator requires a durable group row and rejects a finalized `support-only` or `no-qualifying-comparison` group. Validation reconciles each group's declared linked IDs with actual comparison rows.

## 7. Support-only representation

A support-only physical experiment now has:

- a durable group row;
- a structural/pre-atomization decision and source location;
- a valid experiment-level decision-log target;
- permission to appear as an evidence-link source; and
- zero comparison rows unless it independently answers a qualifying X→Y question.

No dummy comparison is required or allowed. The same zero-comparison behavior applies to `no-qualifying-comparison` groups.

## 8. Decision-log and evidence target resolution

Physical experiment IDs are now resolved from `experiment_groups.csv`; comparison IDs remain resolved from `experiments_master.csv`; all other entity types continue to resolve to their corresponding tables. Evidence links whose `supporting_experiment_id` is absent from the group table are rejected. This resolves pilot 004's two support-only errors without deleting history or weakening support-only semantics.

## 9. A reporting/support split

The old `awareness_result_status` field is replaced for new runs by:

- `awareness_result_reporting`: `reported`, `not-reported`, `unclear`, or `not-applicable`;
- `awareness_result_support`: `supports-strong-A`, `does-not-support-strong-A`, `unclear`, or `not-applicable`.

Procedure type, result description, source location, source experiment, and transfer bundles remain explicit. `not-reported` requires support `not-applicable` and null focal result provenance. `reported` requires a result description, result procedure, source location, and source experiment.

## 10. Strong-A invariant

`A-direct` requires a reported focal critical result that supports strong A, with matching procedure type and the focal experiment as source. Methods-only descriptions and missing locations fail.

`A-validated` follows the same focal-result route when the focal result exists. If it does not, the only strong route is a complete `awareness-A` bundle containing a required, decision-used `critical-result` member with explicit source, transfer reason, limitation, and location.

Invalid reporting/support combinations are rejected by schema and/or cross-file execution validation.

## 11. Transferred-A behavior

A transferred result remains in its evidence link/bundle. It is not copied into the focal row as though reported there. A focal row with `reported` must name its own experiment as the result source; otherwise it fails. An `A-validated` row with `not-reported` may pass only through the complete result-bearing transfer bundle.

## 12. Focal difference provenance

Every `difference_tested = yes` row now requires:

- `difference_source_experiment_id` equal to its own `experiment_id`;
- nonempty `difference_source_location`; and
- nonempty `difference_statistic_or_test`.

The schema requires these fields whenever a direct test is claimed and nulls them for `no`, `unclear`, or `not-applicable`. The validator checks same-experiment identity. Derived difference and equivalence routes also require complete focal provenance.

## 13. Cross-experiment E versus focal difference

Cross-experiment controls remain permitted through E bundles for diagnostic evidence, alternative control, robustness, or transfer. They cannot set `difference_tested=yes` in another experiment. Strong E with no focal direct test cannot become `difference-supported`; direct null auditing remains available in the focal experiment even when E is weak.

## 14. Functional-Y guardrail

Every coded F now requires `Y_functional_status` and a semantic reason:

- `downstream-function` or `coherent-functional-mapping` for `F-meaningful`;
- `function-unclear` for `F-ambiguous`;
- `effect-only` or `not-assessed` for `F-not-meaningful`.

This is an explicit human/agent semantic audit of the operational input→output relation, not a keyword ontology. RT, accuracy, interference, facilitation, correlation, or neural amplitude are evidence about Y and cannot alone serve as a functional Y.

## 15. Effect-only F behavior

When only generic performance modulation is supported, the row must remain `F-ambiguous` if a meaningful downstream function is plausible but unresolved, or `F-not-meaningful` if only generic registration/effect remains. A justified factorial functional mapping remains eligible; the guardrail does not prohibit coherent factorial Y.

## 16. Capacity-identity non-regression

The existing exact `unaware_capacity_claim == Y_label` and whole-focal-Y rules remain. They are now supplemented by the requirement that supported capacity use an audited downstream function/coherent mapping. Derived capacity and equivalence views enforce the same semantic gate. Component/factorial, statistics, Meyen, and evidence-scope rules are unchanged.

## 17. Pilot 004 implications

- The two support-only validator errors disappear structurally in new runs without dummy comparisons.
- Pilot strong-A rows whose own descriptions acknowledge unreported critical values would not pass the new focal-result route; explicit complete transfer evidence would be required.
- Pilot rows cannot assert direct focal differences without same-experiment statistic provenance.
- Effect-descriptive performance-modulation labels cannot yield supported unaware capacity merely through exact string identity.
- The archived pilot is retained unchanged as diagnostic provenance; no historical migration was attempted.

## 18. Leakage status

`tools/leakage_guard.py` passed. New canonical prose, schema fields, tools, and generic tests contain no named anchor answer mapping or anchor-specific runtime identifier. Named adjudication remains under `diagnostics/`; diagnostic non-regression tests remain excluded from registered fixtures by the established leakage contract.

## 19. Synthetic and regression tests

`tests/test_revision_085.py` adds 22 targeted tests covering:

- comparison-bearing, support-only, no-qualifying, missing-group, and placeholder-group behavior;
- reported/supportive A, Methods-only A, inconsistent reporting/support, transfer-only A, copied-source rejection, and missing locations;
- focal difference ownership, cross-experiment rejection, required test/statistic provenance, strong-E/no-direct-test behavior, and weak-E descriptive null behavior;
- effect-only RT/performance labels, ambiguous functional Y, generic neural effects, justified factorial mapping, and capacity semantic identity.

The lifecycle regression now writes a support-only group, resolves an experiment-level audit event, rejects comparison allocation for that final disposition, derives, validates, resumes, and confirms ID retirement/non-reuse.

All prior 0.8.x, factorial, evidence-bundle, route, query/snapshot, reopening/state, namespace, concurrency, and anchor non-regression tests remain active.

## 20. Full validation

Final results:

- Draft 2020-12 meta-validation: **PASS**, 13 schemas.
- Pre-freeze preflight: **PASS**; expected freeze TODOs reported separately below.
- Registered-facing leakage guard: **PASS**.
- Python import/compile: **PASS** with bytecode cache directed to `/private/tmp` because the default macOS cache path is outside the sandbox.
- Entire repository suite: **PASS**, 166 tests.
- Clean init → structured write → derive → validate → resume: **PASS** within the suite.
- Experiment group / strong-A / difference provenance / functional-Y targeted tests: **PASS**, 22 tests.
- ID retirement/non-reuse and concurrent allocation/write tests: **PASS**.
- Search snapshot, reopening/state, diagnostic namespace, and historical compatibility refusal tests: **PASS**.
- `git diff --check`: **PASS**.
- Archive SHA-256 verification and byte comparison: **PASS**.

## 21. Historical CALIB immutability

All 74 files under completed `runs/CALIB*` directories were hashed before edits and after final validation. The manifests are byte-identical (`cmp` passed). Both aggregate manifests hash to:

`ddbd3b402c5f082a6bdabc22afe3a31e6e6f87de50712624f68d9d7546b63b44`

No historical CALIB run or archived prior pilot was migrated or rewritten.

## 22. Remaining pre-freeze TODOs

Preflight still intentionally reports:

1. `registration_status` is `pre-freeze`, not frozen/registered;
2. `publication_cutoff` is null;
3. `search.preferred_sources` is empty;
4. `search.fallback_order` is empty; and
5. `queries.md` contains draft/template markers.

These are freeze/documentation decisions, not failures of this revision. No freeze values were invented.

## 23. Final assessment

The package now enforces:

- every physical experiment has a durable first-class record;
- support-only experiments need no fake X→Y comparison;
- strong A requires a genuinely reported and supportive focal result or an explicit complete transferred-A bundle;
- transferred A cannot masquerade as focal reporting;
- focal awareness-effect statistics belong to the focal experiment;
- cross-experiment evidence can support E without creating a focal direct test;
- Y names a downstream function/coherent mapping rather than merely an observed effect; and
- exact capacity identity cannot be evaded by broad effect-label substitution.

The package is ready to **stop Codex-specific calibration and move to human-readable documentation**, while remaining explicitly pre-freeze until the five registered-run TODOs above are resolved. This revision does not itself authorize a freeze or registered sweep.
