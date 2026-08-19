# Run CALIB003

## Status

**Paused at the mandatory external blind-lane gate.** Scientific evaluation of the complete user-supplied closed-world fixture is finished, all derived outputs are current, and local validation passes. Protocol-level completion is not declared because the required OpenAlex and Europe PMC blind windows cannot be executed without violating the explicit no-network instruction. No external search result or completed external window was fabricated.

This is a diagnostic pre-freeze run under protocol `draft-0.8.3`, package `prefreeze-package-0.8.3`, and schema `prefreeze-schema-0.8.2`.

## Preflight and execution boundary

- Pre-freeze preflight passed immutable-input parsing, all 12 schema meta-validations, seed validation, and categorical-consistency checks.
- Expected pre-freeze TODOs remain: registration status is pre-freeze, publication cutoff is null, preferred/fallback search sources are not frozen, and `queries.md` contains draft/template markers.
- The canonical offline bootstrap could not install because pinned wheels were not cached. Execution used an already installed environment containing the exact pinned versions `PyYAML 6.0.3` and `jsonschema 4.25.1`; no network access was used.
- Six empirical seed papers were the complete encounter set. All six passed semantic title and abstract screening and were selected under the CALIB003 cap of 12.
- Seven PDF assets (six main articles and one supplement) were copied into the run, hashed, visually checked, and extracted once with page maps.
- No candidate full texts are missing. One classification-critical auxiliary source cited for monkey awareness transfer is unavailable because it is outside the supplied fixture.

## Counts

- Papers: **6**
- Physical experiment groups: **20**
- Scientifically relevant, fully evaluated X-to-Y comparisons: **19**
- Support-only experiment audit units: **1** (`P000002_E03_C02`, excluded; visible-only control with no unaware condition)
- Evidence bundles: **17**
- Direct evidence links: **24**
- Verified full-text assets: **7**

## Derived outputs

| Route/view | Count |
|---|---:|
| Awareness-effect design eligible | 8 |
| Constraint-ready union | 15 |
| Awareness-linked differences | 8 |
| Unaware capacities | 9 |
| No detectable awareness differences | 1 |
| Equivalence-supported no difference | 0 |
| Unresolved comparisons | 10 |

The constraint-ready union deduplicates comparisons that qualify through both awareness-linked-difference and unaware-capacity routes.

## Unresolved scientific items

Ten fully evaluated comparisons remain in `unresolved_comparisons.csv`:

- Lamy Experiments 1-3 (`P000003_E01_C01` to `P000003_E03_C01`): unseen task-set-contingent spatial selection is supported, but the direct awareness differences remain unresolved because first-order evidence was not matched and trialwise attentional state was not controlled.
- Ben-Haim human Experiments 1, 3, and 6 (`P000004_E01_C01`, `P000004_E03_C01`, `P000004_E06_C01`): masked cue-dependent action effects are supported, but awareness-effect classification remains unresolved under weak E.
- Ben-Haim monkey Experiments 2 and 4 (`P000004_E02_C01`, `P000004_E04_C01`): both inference axes remain unresolved because awareness validation transfers from humans and an unavailable cited monkey source; the A evidence bundle is incomplete.
- Ben-Haim Experiment 5 (`P000004_E05_C01`): awareness-effect interpretation is weak-E and unaware capacity is unclear because the unaware subgroup contained only three participants.
- Persaud (`P000005_E01_C01`): the matched-performance metacognitive awareness difference is supported, but positive metacognitive capacity in the blind field remains unclear because the within-field significance of `r=.30` was not reported.

The Keizer comparison is not upgraded to equivalence: it is retained as one descriptive no-detectable-difference result with weak null evidence, and its unaware binding effect is excluded from the constraint-ready route because the statistics are exclusion-sensitive and one-tailed.

## Frontier and stopping audit

- Closed-world empirical fixture ingestion: complete.
- Full-text evaluation: complete for every supplied article.
- Candidate missing-text queue: empty.
- Citation frontier: satisfied only under the user-defined closed-world boundary; no external citation search was attempted.
- Process frontier: satisfied only under the user-defined closed-world boundary; no external dynamic query was attempted.
- Mandatory blind lane: pending. Ten external source/family windows required by the package remain unexecuted because network use is prohibited.
- Run status therefore remains `paused`, not `complete`.

## Validation

`tools/derive_outputs.py --run-id CALIB003` regenerated all comparison views. `tools/validate_run.py --run-id CALIB003` passed schemas, CSV encoding, JSONL integrity, identifiers/counters, cross-file references, evidence bundles/links, local file hashes, and derived-output consistency.
