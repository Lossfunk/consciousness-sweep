# Canonical package decontamination — draft-0.8.1

**Status:** completed narrow pre-freeze revision; not committed, frozen, registered, or preregistered  
**Starting commit:** `3ddcc6e643bd9deee60917ca39a1c16da2ebc1bf`  
**Starting package:** draft-0.8 / `prefreeze-package-0.8` / `prefreeze-schema-0.8`

This pass removes paper-specific answers from registered-facing inputs while retaining the general calibrated method. It is decontamination, not de-calibration. No literature search, network/API call, paper retrieval, new CALIB, registered run, clean-room build, clean-room scientific test, or completed-run mutation occurred.

## 1. Exact starting commit

`git rev-parse HEAD` returned `3ddcc6e643bd9deee60917ca39a1c16da2ebc1bf`. The working tree was clean before this task.

## 2. Files changed

Registered-facing package:

- `AGENTS.md`
- `PROTOCOL.md`
- `config.yaml`
- `queries.md`
- `seeds_empirical.csv`
- `tools/execution_contract.py`
- `tools/preflight.py`
- `tools/query_instruments.py`
- new `tools/leakage_guard.py`

Diagnostic/test material outside registered inputs:

- new `diagnostics/calibration_provenance_draft_0_8_1.md`
- new `diagnostics/canonical_decontamination_draft_0_8_1.md`
- `tests/test_pipeline.py`
- new `tests/test_anchor_non_regression.py`

No schema, review-seed row, derived-output implementation, run, output, README, or METHODS file changed.

## 3. Version changes

- Protocol: `draft-0.8` → `draft-0.8.1`
- Package: `prefreeze-package-0.8` → `prefreeze-package-0.8.1`
- Schema: remains `prefreeze-schema-0.8`; no schema semantics changed
- Registration status: remains `pre-freeze`

The package version changes because immutable registered-facing inputs changed. The schema version remains unchanged because no schema or category semantics changed.

## 4–5. Leakage inventory and classification

| Location in draft-0.8 | Finding | Classification | Disposition |
|---|---|---|---|
| `seeds_empirical.csv` title/author/year/DOI/URL for all six seeds | Bibliographic identities | Necessary bibliographic identity | Retained unchanged |
| `PROTOCOL.md` named Tsushima paragraph beside `E-diagnostic` and its expected result structure | Particular seed's expected E interpretation | Scientific answer-key leakage | Replaced with a synthetic Experiment A/B example; original archived |
| `queries.md` historical Tsushima QDYN table, canonical Y, source terms, pointers, and rendered queries | Particular seed's expected Y and process-query answer | Scientific answer-key leakage | Replaced with a synthetic runtime example; original archived |
| `tools/query_instruments.py` `TSUSHIMA_DIAGNOSTIC_VARIANTS` | Anchor-specific runtime constant and lexical answer | Scientific answer-key leakage | Removed; generic runtime builder and plan added; original archived |
| ESEED001 reason | Paper-specific attentional-control interpretation | Scientific answer-key/potential focal-interpretation leakage | Neutralized; original archived |
| ESEED002 reason | Paper-specific attentional-effects/control interpretation | Scientific answer-key/potential focal-interpretation leakage | Neutralized; original archived |
| ESEED003 reason | Paper-specific attentional-capture/conflict interpretation | Scientific answer-key/potential focal-interpretation leakage | Neutralized; original archived |
| ESEED004 reason | Paper-specific strategic-cue-use interpretation | Scientific answer-key leakage | Neutralized; original archived |
| ESEED005 reason | Paper-specific metacognitive-calibration interpretation | Scientific answer-key leakage | Neutralized; original archived |
| ESEED006 reason | Explicit preserved-capacity/binding interpretation | Scientific answer-key leakage | Neutralized; original archived |
| `queries.md` named CALIB003/CALIB004 sentinel list and recovery instructions | Named target bookkeeping without scientific codes | Calibration/history that should move out | Removed and archived |
| `queries.md` generic blind-sentinel paragraph | Calibration-only bookkeeping | Calibration/history that should move out | Removed and archived |
| `config.yaml` `calibration_004.blind_sentinel_set` | Calibration-only named-set pointer | Calibration/history that should move out | Removed and archived |
| `PROTOCOL.md` generic sentinel rules | Result-neutral calibration methodology | Harmless generic/method content | Retained |
| `config.yaml` generic null `sentinel_recovery_threshold` | Non-identifying pre-freeze calibration field | Harmless generic/method content | Retained |
| `queries.md` generic CALIB history and source/query bounds | Instrument provenance without a paper-specific scientific answer | Harmless generic/method content | Retained |
| `AGENTS.md` CALIB003 bounded sampling rule | Historical execution rule explicitly excluding expected outcomes | Harmless generic/method content | Retained |
| `seeds_reviews.csv` | Neutral scholarly scope and discovery-anchor metadata | Necessary bibliographic identity / harmless method scope | Retained unchanged |

After cleanup, the six anchor names occur in registered-facing material only as bibliographic identity in `seeds_empirical.csv`. Existing answer-rich diagnostics and diagnostic-only tests remain outside the registered-facing allowlist.

## 6. PROTOCOL genericization

The named anchor paragraph was replaced by a synthetic two-experiment structure: Experiment A identifies a downstream extremum around detectability; Experiment B manipulates detectability and the downstream extremum shifts correspondingly; a complete premise-specific same-Y bundle may support `E-diagnostic` only when the joint pattern violates the stated scalar signal-strength prediction. The extremum alone remains insufficient.

An exact normalized comparison against HEAD passed: aside from the version line, this named-to-generic paragraph is the only protocol change.

## 7. Generic E-diagnostic rules

Preserved:

- all four E categories;
- positive matching/titration or explicit equivalence requirements for `E-matched`;
- rejection of bare nonsignificance as matching;
- design-first E assessment and limited result inspection for the diagnostic route;
- threshold-linked non-monotonicity;
- manipulated detectability with a corresponding downstream shift;
- crossover/sign reversal;
- coherent factorial/process-selective mappings;
- the same-Y requirement;
- competing account, prediction, violating pattern, required evidence, and source-location requirements;
- multi-experiment premise-specific evidence bundles;
- the prohibition on treating mere complexity, significance, or non-monotonicity as diagnostic.

The only change is semantically equivalent generic wording for the named empirical illustration.

## 8. Factorial-functional rules

Preserved verbatim: scalar versus factorial-functional Y, coherent component-cell mappings, interaction/structured-mapping inference, retention of meaningful component effects, prohibition on destructive atomization, and prohibition on merging genuinely distinct functions.

## 9. Capacity, effect, null, and equivalence rules

Preserved verbatim:

- orthogonality of unaware capacity and awareness effect;
- a comparison may support both capacity and a difference;
- E gates the awareness-effect route but not the unaware-capacity route;
- exact named capacity and positive evidence requirements;
- component-capacity identity requirements;
- `no-detectable-difference` versus `equivalence-supported`;
- rejection of bare/uninformative `p > .05`;
- positive equivalence evidence requirements and prohibition on invented margins.

## 10. Evidence-bundle guardrails

Preserved verbatim: scientific bundle versus execution cache; one premise per bundle; direct links; required-member manifest; complete/incomplete/conflicted status; no optional-member substitution; support versus dependency role; exact claim/location/transfer rationale/limitation; no transitivity; no same-paper automatic transfer; explicit reuse; support-only experiments; multi-experiment focal inference; and prohibition on cache propagation of scientific codes.

`schemas/`, `tools/derive_outputs.py`, bundle validation, and derived scientific filters have no diff.

## 11. `queries.md` cleanup

- Removed the named six-sentinel list and registered-facing recovery instructions.
- Removed the historical Tsushima QDYN canonical Y, lexical variants, source pointers, and rendered queries.
- Added a synthetic context-dependent response-selection rendering solely to demonstrate the unchanged generic contract.
- Preserved the closed lexical universe, provenance requirements, OA/EPMC renderings, N=50/source/Y, one-window bound, no quota redistribution, no same-Y retrigger, and genuinely-new-Y recursion rule.
- Preserved all five active QCAL families, OA + EPMC, N=40/source/family, blind-last ordering, and disabled/retired LEARN status.

## 12. `query_instruments.py` genericization

Removed the anchor-specific constant. Added:

- `build_process_variants(...)`, which consumes runtime canonical Y, approved grammatical variants, source-derived same-function terms with explicit source pointers, and an optional immediate parent;
- enforcement of exactly one canonical Y and at most one immediate parent;
- `process_query_plan(...)`, which returns a deterministic log-ready query, full lexical provenance, source, canonical Y, N=50, one window, and no quota redistribution.

The existing OpenAlex and Europe PMC renderers remain unchanged. Unrestricted/unknown provenance, provenance-free source terms, duplicates, missing rationales, invalid grammatical derivations, unsupported sources, and multiple parent labels are rejected.

## 13. Empirical-seed reason cleanup

All six empirical seeds and every bibliographic identity remain unchanged. Every `seed_reason` now uses the same neutral procedural statement:

> Frozen empirical seed identified during pre-registration manual scoping; retained as a guaranteed candidate-lot entry

The notes now contain bibliographic verification only. Original rich rationales are archived with the starting commit.

## 14. Review-anchor audit

`seeds_reviews.csv` contains neutral coverage-area, discovery-anchor, and bibliographic metadata. It reveals no expected classification or focal interpretation for the six empirical seeds. No review row required modification.

## 15. Sentinel cleanup

Named sentinel identities, the named-set config pointer, and registered-facing recovery bookkeeping were moved to diagnostics. The six empirical seed rows remain registered inputs. Generic pre-freeze sentinel methodology remains because it is result-neutral and may still be useful for instrument calibration before freeze.

## 16. Historical calibration provenance

`diagnostics/calibration_provenance_draft_0_8_1.md` records the exact pre-change commit, removed protocol paragraph, all original empirical-seed rationales, the complete historical Tsushima lexical set and provenance, CALIB003/CALIB004 sentinel identities/use, and the reason each item is excluded from registered inputs.

Existing gold-standard diagnostics remain untouched and outside registered-facing inputs.

## 17. Remaining registered-facing anchor occurrences

The remaining occurrences are the six rows of `seeds_empirical.csv`:

- Tsushima et al. (2006)
- Lin & Murray (2015)
- Lamy et al. (2015)
- Ben-Haim et al. (2021)
- Persaud et al. (2011)
- Keizer et al. (2015)

Each occurrence is necessary bibliographic identity for a frozen empirical seed: title, authors, year, DOI, URL, neutral procedural seed provenance, and bibliographic verification. No row supplies focal experiment, X/Y adjudication, A/E/F, capacity/effect/equivalence, Meyen, bundle, process vocabulary, or constraint-ready status.

## 18. Leakage guard

New `tools/leakage_guard.py` uses an explicit registered-facing file allowlist. It:

- derives empirical-anchor author tokens from the seed bibliography rather than globally banning surnames;
- permits bibliographic names and neutral citations;
- requires neutral procedural empirical-seed reasons and scans seed metadata for answer cues;
- flags anchor names coupled to classification, focal-Y, expected-result, capacity/effect, diagnostic, or sentinel cues;
- parses canonical Python tools and flags anchor-named constants/functions/classes;
- excludes diagnostics, tests, runs, and outputs from the registered-facing audit by construction.

`tools/preflight.py` invokes the guard. The guard is conservative and explicitly does not replace a human semantic leakage audit.

## 19. Synthetic/Y-agnostic query-renderer tests

The former anchor-specific fixture is replaced with a synthetic context-dependent response-selection fixture. Tests cover:

- runtime canonical Y;
- grammatical variant derivation;
- source terminology with explicit pointer;
- one immediate-parent label;
- deterministic planning and full lexical provenance;
- OpenAlex and Europe PMC rendering;
- N=50/source/Y and one-window bounds;
- rejection of unrestricted synonyms;
- rejection of provenance-free source terminology;
- rejection of multiple parent labels;
- leakage detection for a synthetic anchor-named runtime constant.

Existing execution tests continue to cover no same-Y retrigger and genuinely-new-Y frontier reopening.

## 20. Generic threshold-shift bundle regression

The synthetic regression remains unchanged. Its bundle premise is a structured threshold-linked downstream pattern supporting `E-diagnostic`; required members are the threshold-linked effect and independently manipulated threshold/downstream shift. With only the first member the bundle is `incomplete`; with both it is `complete`. Robustness, generalization, and mechanistic members remain optional typed roles and cannot substitute for either required member.

## 21. Six-anchor scientific non-regression

`tests/test_anchor_non_regression.py` is diagnostic-only and excluded from registered fixtures. It reapplies the existing draft-0.8 route tuples to unchanged derived functions; it does not reread papers or create a scientific run.

| Anchor | Awareness-difference ready | Unaware-capacity ready | Equivalence ready | Descriptive no-detectable | Result |
|---|---:|---:|---:|---:|---|
| Tsushima | yes | no | no | no | unchanged |
| Lin & Murray | yes | no | no | no | unchanged |
| Lamy | yes | yes, named component | no | no | unchanged |
| Ben-Haim | yes | yes, named automatic component | no | no | unchanged |
| Persaud | yes | yes, named metacognitive capacity | no | no | unchanged |
| Keizer | no | yes, named binding capacity | no | yes | unchanged |

The generic threshold-shift bundle regression also passed. No paper-specific result was written into registered-facing material.

## 22. Calibrated-guardrail before/after audit

| Guardrail family | Before → after status |
|---|---|
| Awareness evidence categories/types, objective invisibility, mixed evidence, legacy adequacy, and transfer dimensions | Preserved verbatim |
| E categories, matching/equivalence requirements, design-first sequence, and diagnostic structures | Preserved verbatim except named illustration replaced by semantically equivalent generic wording |
| F categories, conservative functional Y, mechanism/function separation, and non-qualifying direct/generic responses | Preserved verbatim |
| Scalar and factorial-functional comparison rules | Preserved verbatim |
| Unaware capacity versus awareness effect and component-capacity identity | Preserved verbatim |
| No-detectable versus equivalence and positive-null standards | Preserved verbatim |
| Meyen roles, critical gate, and supplementary limitation | Preserved verbatim |
| Strict evidence bundles, direct links, member manifest/status, transfer, non-transitivity, and cache separation | Preserved verbatim |
| Structural audit, route viability, dead-route short-circuiting, and durable reasons | Preserved verbatim |
| Discovery architecture, principal-first/blind-last, frontier reopening, snapshots/resume, and independence | Preserved verbatim |
| QCAL five-family OA/EPMC N=40 contract | Preserved verbatim |
| QDYN OA/EPMC N=50, closed lexical universe, no retrigger, bounded new-Y recursion | Preserved; anchor-specific instantiation replaced by general runtime inputs |
| Statistical standards and derived scientific filters | Preserved verbatim; implementation has no diff |
| Schema categories and semantics | Preserved verbatim; all 12 schema files have no diff |

No calibrated generic guardrail was intentionally changed for another scientific reason. None was removed because it originated from anchor calibration.

## 23. Test and validation results

- Draft 2020-12 schema meta-validation: **12/12 PASS**.
- Pre-freeze input/config/seed/category audit: **PASS**.
- Registered-package leakage guard: **PASS**.
- Entire unit suite: **84/84 PASS**.
- Synthetic QDYN renderer/provenance/rejection tests: **PASS**.
- Generic threshold-shift evidence-bundle regression: **PASS**.
- Clean temporary init → structured write → derive → validate → resume lifecycle: **PASS**.
- Resume without reset and package/schema compatibility: **PASS**.
- Retired ID recovery (`P000002` remains retired; next is `P000003`): **PASS**.
- Immutable completed search-window key/hash reuse and contradiction rejection: **PASS**.
- Route-state, blind-last completion, citation reopening, and genuinely-new-Y reopening/no-retrigger: **PASS**.
- Historical CALIB package/schema refusal with before/after aggregate-hash immutability: **PASS**.
- Six-anchor derived-view non-regression: **PASS**.
- Python compile and import check: **10/10 canonical tool modules PASS**.
- Exact protocol normalized-diff audit: **PASS**.
- Schemas and `tools/derive_outputs.py` unchanged: **PASS**.
- Semantic anchor-occurrence audit: **PASS**; only empirical-seed bibliographic rows remain.
- `git diff --check`: **PASS**.
- Source `runs/` and completed CALIB artifacts: **not modified**.

No network access or paper retrieval was used.

## 24. Remaining pre-freeze TODOs

- Registration status remains `pre-freeze`.
- Publication cutoff remains null.
- Preferred search sources remain unfrozen/empty.
- Fallback source order remains unfrozen/empty.
- Query strings remain draft/to-freeze.
- Decide whether to redesign the generic LEARN blind-query family or explicitly omit that generic family from v1 while retaining learning eligibility through other routes.
- Build a new clean-room fixture only after review and commit of this revision.
- Run the minimal-instruction sufficiency test later in a fresh session on that newly built fixture.
- README/METHODS and the full authority crosswalk remain deferred until after that test.

## 25. Suitability and critical answer

- Suitable for checkpoint commit: **YES**, subject to human review of this uncommitted diff.
- Suitable for rebuilding a fresh clean-room fixture: **YES, after commit**, from the exact new commit rather than this working tree.
- Suitable for the later minimal-instruction sufficiency test: **YES, after** the replacement fixture is built and independently leakage-audited.

**Critical answer: YES. This task removed paper-specific answers while preserving the general calibrated method.**

The old `/tmp/consciousness-sweep-cleanroom-draft-0.8/` fixture was not modified, and no replacement fixture or clean-room scientific test was created or run.
