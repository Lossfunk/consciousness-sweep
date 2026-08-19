# Draft-0.8.2 main-repository transplant

**Status:** controlled pre-freeze transplant complete; not a registered run, freeze, or new scientific revision

## Starting state

- Real repository: `/Users/sushrutthorat/Documents/GitHub/consciousness-sweep`
- Starting commit: `0be0cc2d0a18dfbec320f8a2ace0b16573914f8c`
- Starting worktree: clean (`git status --short` returned no entries)
- Starting versions: protocol `draft-0.8.1`, package `prefreeze-package-0.8.1`, schema `prefreeze-schema-0.8`
- Validated source workspace: `/private/tmp/consciousness-sweep-cleanroom-draft-0.8.1/`
- Source pilot package commit: `0be0cc2d0a18dfbec320f8a2ace0b16573914f8c`

The source revision report, adjudication, Ben-Haim issue report, gold correction, changed canonical files, and synthetic tests were inspected before transplant. No literature search, retrieval, citation traversal, screening, scientific run, second pilot, freeze, registration, or commit occurred.

## Transplanted generic revision

The repository now identifies protocol `draft-0.8.2`, package `prefreeze-package-0.8.2`, and schema `prefreeze-schema-0.8.1`.

The validated revision adds:

- the mandatory pre-atomization functional-structure check before comparison decomposition;
- focal-first instantiation when factors or cells jointly operationalize one coherent functional mapping;
- continued permission for scalar decomposition when genuinely distinct downstream functions are justified;
- durable `functional_structure_assessment`, `functional_structure_reason`, and `factorial_focal_comparison_id` fields;
- schema, preflight, and run-validator enforcement of those decisions and focal linkage;
- the validated factorial `E-diagnostic` clarification requiring a complete bundle with a required, decision-used `alternative-explanation-control` member; and
- the clean-room A–G generic structural tests and synthetic execution-lifecycle tests.

The Ben-Haim Experiment 1 process-enablement issue remains open diagnostic work. No additional E-diagnostic change was made.

## Files changed

Validated source files transplanted byte-for-byte:

- `AGENTS.md`
- `PROTOCOL.md`
- `config.yaml`
- `schemas/experiments.schema.json`
- `tools/execution_contract.py`
- `tools/preflight.py`
- `tools/validate_run.py`
- `tests/test_factorial_structure.py`
- `tests/test_execution_lifecycle.py`

Small main-repository adaptations:

- `tests/test_pipeline.py`: added the three required structure fields to the existing broad synthetic experiment fixture.
- `tests/test_anchor_non_regression.py`: changed only Persaud's diagnostic capacity gold to `unclear` and its expected capacity-derived result to false.
- `diagnostics/anchor_regression_draft_0_7.md`: recorded the same diagnostic-only Persaud correction and preserved the awareness-linked result.

Diagnostic provenance added:

- `diagnostics/cleanroom_pilot_001/` (sealed 47-file archive)
- `diagnostics/cleanroom_pilot_001_revision_report.md`
- `diagnostics/cleanroom_pilot_001_adjudication.md`
- `diagnostics/ben_haim_exp1_e_diagnostic_pilot_issue.md`
- `diagnostics/cleanroom_pilot_001_gold_corrections.json`
- this report

`tools/derive_outputs.py`, `queries.md`, both seed CSVs, `requirements.txt`, and all completed run contents are unchanged.

## Pilot archive and report verification

`shasum -a 256 -c diagnostics/cleanroom_pilot_001/SHA256SUMS` passed for every listed archive member. A separate source-to-target comparison verified all 47 archive files byte-for-byte. The sealed directory and its archived files preserve their read-only modes.

The copied report hashes are:

| File | SHA-256 |
|---|---|
| `cleanroom_pilot_001_revision_report.md` | `5c67839a8ced445a026dd6c1f0b60af59c135f03cbe7a186309bac7485273553` |
| `cleanroom_pilot_001_adjudication.md` | `40bf7f56730a085f28841bd14c9f59da33dd4c6934473e1541d2ad670abb1e7a` |
| `ben_haim_exp1_e_diagnostic_pilot_issue.md` | `f5502c6dfc383bf9e73c1f786f3f1270c69857f58fd0d6d495f9501fa54aa336` |
| `cleanroom_pilot_001_gold_corrections.json` | `444c6df1545ee823594bd563c842554b08635f4b5bb537337e544cda94956d96` |

These materials remain under `diagnostics/`; they were not introduced into registered-facing inputs, canonical scientific fixtures, or `runs/`.

## Persaud diagnostic-gold correction

The superseded diagnostic-only `unaware_capacity = supported` value was changed to `unclear`. The reported blind-field correlation (`r=.30`) lacks an adequate direct positive test against zero in the supplied article, while the between-field difference continues to support the awareness-linked metacognitive effect. No registered-facing rule, seed rationale, query, schema category, or runtime answer key encodes this result.

## Validation results

| Check | Result |
|---|---|
| Draft 2020-12 schema meta-validation | PASS, all 12 schemas |
| Pre-freeze preflight | PASS; expected unresolved freeze items remain: registration status, publication cutoff, preferred/fallback source order, and query draft markers |
| Registered-package leakage guard | PASS |
| Entire repository unit suite | PASS, 99/99 tests |
| Pre-atomization/factorial A–G tests | PASS |
| Factorial E-diagnostic and strict evidence-bundle tests | PASS |
| Synthetic init → ID allocation/write → derive → validate → resume | PASS |
| ID retirement/non-reuse and concurrent allocation/write tests | PASS |
| Route reopening/state tests | PASS |
| Immutable search-window key and ordered-result snapshot tests | PASS |
| Python import and in-memory compile | PASS, 14 tool/test modules |
| `git diff --check` | PASS |

The leakage guard found no named anchor-specific answer, focal experiment, expected Y, expected E code, or expected classification in `PROTOCOL.md`, `AGENTS.md`, `config.yaml`, `queries.md`, seeds, schemas, or canonical runtime tools. The new rule remains generic.

The search instrument is unchanged: five active QCAL families (`ATTN`, `META`, `BIND`, `MEM`, `DEC`), OpenAlex plus Europe PMC, one window of at most 40 results per source/family, QDYN at most 50 results per source/Y, and `LEARN` disabled/retired with its pre-freeze TODO retained. `preferred_sources` and `fallback_order` remain intentionally unfrozen.

## Historical CALIB immutability

Before the transplant, byte-manifest baselines were recorded for all four completed calibration directories. The after-audit retained the same file counts, total bytes, and content baselines; no completed file has a modification time later than its original calibration checkpoint.

| Run | Files | Bytes | Baseline/after aggregate SHA-256 |
|---|---:|---:|---|
| `CALIB_CODEX_001` | 18 | 6,580,530 | `baa6a67c461803247c995d308772688c0ff4a8e5440bf3f528c48cfd265ec2d0` |
| `CALIB_CODEX_002` | 16 | 6,769,627 | `095854040ebcc17ce960286c078edcd2361adc1abe71ccfc3474ead9bc461083` |
| `CALIB_CODEX_003` | 25 | 15,942,522 | `648abaf8b3a009f65505d604df8e9d6b37f95137484bad117307f213f82a33d4` |
| `CALIB_CODEX_004` | 15 | 1,374,547 | `c852807587880bdec6a20c4ea5db5d1b692b9e581248f8844215e36a35f529c1` |

Direct validator probes returned exit 3 for every completed CALIB run because its historical package/schema differs from the current package. Each refusal occurred before applying the new schema. No completed run was migrated, rewritten, resumed, derived, or otherwise modified.

## Source-to-target comparison

The nine consequential transplanted files (seven canonical files plus two clean-room test modules), `tools/derive_outputs.py`, and `queries.md` are byte-identical to the validated clean-room workspace. There is no scientific or runtime difference from the validated implementation.

The only additional main-repository changes are the minimum compatible fixture migration, the explicitly requested diagnostic-only Persaud correction, and archival/reporting files described above. No silent improvement or rewrite was introduced.

## Checkpoint readiness

The real main repository is ready for a draft-0.8.2 pre-freeze checkpoint commit. It is not frozen or registered, the listed pre-freeze TODOs remain open, pilot #2 has not been run, and no commit was created by this transplant.
