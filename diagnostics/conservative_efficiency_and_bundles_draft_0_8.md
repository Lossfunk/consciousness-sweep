# Conservative execution and strict evidence bundles — draft-0.8 implementation report

**Status:** pre-freeze implementation diagnostic; not a registered run, calibration, literature search, or clean-room sufficiency test  
**Previous package:** draft-0.7.1 / `prefreeze-package-0.7.1` / `prefreeze-schema-0.7.1`  
**Current package:** draft-0.8 / `prefreeze-package-0.8` / `prefreeze-schema-0.8`

## 1. Scope and prohibited operations

This revision implements only the conservative execution-efficiency changes supported by `diagnostics/efficiency_audit_draft_0_7_1.md` and the strict evidence-bundle/cache architecture requested for the next pre-freeze package. It does not change A/E/F meaning, the draft-0.7.1 capacity/effect/equivalence derivations, or Meyen logic. `tools/derive_outputs.py`, seeds, `README.md`, and any future `METHODS.md` were not changed.

No literature search, HTTP/API call, new paper retrieval, new CALIB, registered run, freeze/registration, completed-run mutation, or clean-room/minimal-prompt test was performed. No commit was created.

## 2. Files changed

Scientific/execution authorities and query configuration:

- `PROTOCOL.md`
- `AGENTS.md`
- `config.yaml`
- `queries.md`

Schemas:

- updated: `auxiliary_sources.schema.json`, `decision_log.schema.json`, `discoveries.schema.json`, `evidence_links.schema.json`, `experiments.schema.json`, `run_state.schema.json`, `search_log.schema.json`
- added: `evidence_bundles.schema.json`, `evidence_assessments.schema.json`, `fulltext_assets.schema.json`

Execution utilities:

- updated: `init_run.py`, `preflight.py`, `query_instruments.py`, `structured_write.py`, `validate_run.py`
- added: `execution_contract.py`

Tests and report:

- updated: `tests/test_pipeline.py`
- added: this report

The prior retrospective efficiency audit remains an input, not registered scientific evidence. No file under `runs/` was written or modified by this task.

## 3. Conservative search configuration

### Mandatory supplementary blind lane

The active families are exactly:

1. `QCAL4-ATTN` — attention/control
2. `QCAL4-META` — metacognition/monitoring
3. `QCAL4-BIND` — binding/integration
4. `QCAL4-MEM` — memory operations
5. `QCAL4-DEC` — action/rule-guided use

Both OpenAlex and Europe PMC are required. Each source/family pair has one relevance-ranked window, maximum N=40, with every return screened, no second page/cursor, and no quota reallocation. The exact maximum is 10 windows and 400 encounters.

`QCAL4-LEARN` is retained verbatim as historical provenance but is disabled/retired from the active candidate instrument because CALIB004 diagnosed the rendering as pathological. Learning/adaptation remains scientifically eligible through seeds, reviews, citations, and independently earned process searches. The visible pre-freeze TODO is to redesign the generic block or explicitly decide that v1 omits it; this revision does neither.

### Process-trigger search

Each independently earned normalized Y uses both OpenAlex and Europe PMC, one window per source, N=50/source/Y, the unchanged controlled lexical universe, no second page/cursor, no quota reallocation, and no same-Y/source retrigger. Recursion is permitted only for a genuinely new normalized Y that independently earns the route under the unchanged A/E/F activation rule.

## 4. Principal-first, blind-last state machine

`AGENTS.md` now states all 16 requested steps explicitly. Durable state adds `workflow_phase`, blind-lane status, citation/process frontier status, activated normalized Ys, and completed immutable search-window keys.

The executable sequence is:

- initialize empirical seeds and review/discovery anchors;
- screen/index principal inputs, expand citations in frozen waves, retrieve/evaluate full texts, and activate earned process searches;
- reach and log provisional satisfaction of every principal frontier;
- only then execute all ten mandatory QCAL source/family windows;
- deduplicate first, record rediscovery provenance for known logical works without semantic rescreening, and individually screen only genuinely new works;
- reopen citation expansion for new eligible nodes and process search for genuinely new earned Ys;
- complete only after every reopened frontier is satisfied again.

The validator rejects a blind search that precedes a durable `principal-provisionally-satisfied` transition. Completion helpers reject a skipped blind lane or an open/reopened frontier. The validator also requires exactly the ten active family/source windows before `blind_lane_status=complete`.

## 5. Search snapshots and resume

Every bounded query row now records execution phase, source, query identity or normalized Y, canonical rendering, source parameters, publication cutoff, requested and actual N, retrieval time, window status, ordered result ranks, source-stable IDs where available, deterministic window key, and ordered result-set SHA-256.

The window key fingerprints phase, source, query identity, normalized Y, exact rendering, source parameters, cutoff, and N. The result hash fingerprints ordered rank plus stable ID/DOI/title/URL. Validation rejects:

- a key inconsistent with its frozen parameters;
- noncontiguous result ranks;
- an actual result count above the frozen maximum;
- a result count/hash inconsistent with durable discovery rows;
- contradictory completed snapshots;
- a second completed source/family or source/Y execution;
- a reused snapshot without a prior completed row or with a changed hash;
- discovery rows attached to a reuse event, which would imply a silent rerun.

Resume therefore reuses the durable snapshot and retries only failed/incomplete windows. Dynamic result sets are never shared across independent runs.

## 6. Paper-level decisions and batching

`papers_master.csv` remains the single current bibliographic/title/abstract state for each logical work; `discoveries.csv` retains every encounter. The execution guard returns one of three actions: screen a new logical paper, reuse the existing decision, or revise because genuinely new evidence exists. Rediscovery alone returns reuse.

Title batches are limited to 25 logical papers and abstract batches to 10; smaller batches are allowed. Each member must have a unique paper ID, individual semantic method, individual decision, and individual reason. Batch membership carries no evidence. Regex/keyword rules, embeddings, citation thresholds, numeric relevance scores, and hidden lexical heuristics are prohibited from independently excluding a work. A genuine revision remains append-first in `decision_log.jsonl`, with old value, new value, reason, and triggering source before current-state mutation.

No paper-level or scientific decision is reusable across independent agent runs.

## 7. First-class scientific evidence bundles

`evidence_bundles.csv` is now the scientific argument table. One row supports one controlled premise of one focal comparison. It includes:

- stable bundle ID and focal comparison ID;
- controlled `supported_premise`;
- premise description and route label;
- a predeclared `required_member_keys` manifest;
- derived `complete`, `incomplete`, or `conflicted` status and reason.

The required-member manifest is essential: a missing link is observable rather than indistinguishable from an intentionally absent member. The same evidence used for two premises or two comparisons requires two bundles and direct links for both uses. An independent route to the same premise is a separate bundle.

`evidence_links.csv` now records a unique bundle-local member key, source/experiment/analysis, exact location, supported claim, support role, dependency role, member status, transfer reason, transfer limitation, decision use, and optional factual-assessment reference.

Support roles cover awareness validation, first-order evidence control, E-diagnostic support, alternative-explanation control, replication, statistics, robustness, generalization, mechanism, and other. Dependency roles are separate:

- `required`: present, evaluated, transfer-valid, supporting, and decision-used before the bundle can complete;
- `strengthening`: materially increases support but is not logically necessary;
- `robustness`: tests an alternative explanation or analytic sensitivity;
- `generalization`: extends population/stimulus/regime scope;
- `mechanistic`: supplies implementation evidence without becoming a functional premise.

Status is derived as follows:

- `conflicted` if any direct evaluated member contradicts or is itself conflicted;
- otherwise `incomplete` if a manifested required member is missing, duplicated, unavailable, unevaluated, transfer-invalid, non-supporting, not marked required, or not used for the decision;
- otherwise `complete`.

Optional unavailable strengthening/robustness/generalization/mechanistic members do not automatically defeat a complete required core. Contradictions are not averaged away. A comparison cannot treat a bundled premise as established without a complete independent bundle.

Evidence is direct and non-transitive. The schema has no bundle-as-source shortcut, and validation requires each direct member to target the same focal comparison and declared bundle. Sharing a paper, experiment, auxiliary source, assessment, or another bundle creates no inferred link.

Support-only experiments remain support-only. A link may reference a within-paper experiment without requiring a candidate comparison row; it enters the candidate pool only if independently represented as an eligible X→Y comparison.

## 8. Scientific bundle versus execution cache

`evidence_assessments.csv` is an execution-only factual cache. Reuse requires exact source identity, factual premise, source location, scientific-regime fingerprint, and source-asset hash. Its strict schema has no A/E/F, outcome, Meyen, or route-classification fields, and the helper rejects injected scientific fields. A cached fact never creates a scientific link or code; every target comparison still needs its own bundle/link and decision.

This preserves within-paper reuse for visibility tests, stimulus regimes, first-order manipulations, reported analyses, and controls without inheriting scientific classifications through group membership. A changed regime fingerprint, source location, or asset hash blocks reuse.

## 9. Full-text and auxiliary reuse

`fulltext_assets.csv` records one immutable paper/article-version asset with source identity, file hash, verification reason, acquisition route, and optional extraction tool/version, extracted-text hash, and page-map hash. Validation permits only one row per paper/version and one current version per paper; a materially different version is a new row rather than an overwrite. Extraction reuse additionally requires an exact tool/version match. Paths and hashes are verified during run validation.

`auxiliary_sources.csv` now stores one reusable logical external work/version rather than duplicating target-specific uses. Duplicate normalized DOI/version rows are rejected. Multiple evidence links may reference the same acquisition, but every distinct scientific use retains its own target, premise, transfer rationale, caveat, and provenance. Auxiliary-only sources do not enter `papers_master.csv` or `discoveries.csv` unless independently encountered through a normal discovery event.

## 10. Route-aware full-text evaluation

Comparison rows now record structural-audit status and explicit awareness-effect, unaware-capacity, null/equivalence, and result-inspection dispositions with reasons.

- Awareness-effect constraint route: viable only with strong A + strong E + meaningful F.
- Unaware-capacity route: viable with strong A + meaningful F; E is not a gate. Results and critical statistics must still be inspected for the exact named capacity.
- Null/equivalence route: required only when a no-detectable/equivalence question is actually at issue. This includes a descriptive no-detectable result such as Keizer even when weak E prevents constraint-ready awareness-effect inference. A difference result does not require a null audit.
- Dead routes receive explicit not-viable/not-required reasons rather than ambiguous blanks.

No derived scientific filter changed. Route metadata only controls which reasoning is required; it does not redefine outputs.

## 11. Synthetic threshold-shift bundle regression

The canonical synthetic test represents the strongest threshold-shift E-diagnostic argument with two manifested required members:

1. a threshold-linked non-monotonic interference result; and
2. an independently manipulated detectability threshold whose interference extremum shifts correspondingly.

With only member 1, the bundle derives `incomplete`. Adding member 2 derives `complete`. Eye/control, replication/generalization, and mechanistic members remain separately typed optional roles and do not substitute for either required member. This expresses the focal Tsushima structure without embedding its expected registered-run classification in seeds or registered instructions.

## 12. Six-anchor non-regression

The existing bounded draft-0.7.1 diagnostic was reapplied as a non-regression check using `diagnostics/anchor_regression_draft_0_7.md`, the existing Tsushima diagnostic material, unchanged derived-output functions, and the new structural validators/tests. This was not an independent source reread and not the future minimal-instruction test.

| Anchor | Draft-0.7.1 focal result | Draft-0.8 non-regression | Structural check |
|---|---|---|---|
| Tsushima | awareness difference yes; capacity no; equivalence no | unchanged | required threshold-effect + manipulated-threshold-shift bundle completes only jointly; controls retain optional typed roles |
| Lin & Murray | awareness difference yes; capacity no; equivalence no | unchanged | multi-experiment location/visibility support remains explicit and premise-specific |
| Lamy | awareness difference yes; named component capacity yes; equivalence no | unchanged | focal factorial comparison plus the separate first-order-evidence control remains a complete direct E-diagnostic bundle |
| Ben-Haim | awareness difference yes; automatic-bias component capacity yes; strategic component no; equivalence no | unchanged | focal late crossover remains the comparison; earlier/late controls remain support-only links |
| Persaud | awareness difference yes; named metacognitive capacity yes; equivalence no | unchanged | scalar E-matched route and within-paper matching/calibration evidence remain representable without code inheritance |
| Keizer | awareness difference no; named binding capacity yes; descriptive no-detectable difference; equivalence no | unchanged | weak E closes the constraint-ready awareness route but not capacity inspection or the relevant descriptive null audit; equivalence still requires positive evidence |

No focal A/E/F, capacity, awareness-effect, equivalence, or Meyen adjudication regressed. `tools/derive_outputs.py` has no diff. No rule was altered to force anchor recovery.

## 13. Test inventory and results

All 47 retained draft-0.7.1 tests passed after schema-fixture migration. In particular, the existing capacity identity, awareness/evidence, F granularity, factorial E-diagnostic, Meyen, derived-output, DOI/provenance, historical-run immutability, query rendering, support-only experiment, concurrency, and structured-write assertions remain green.

Thirty new tests were added; every one passed:

| Area | New tests | Result |
|---|---|---|
| Conservative QCAL/QDYN | exact five active families/two sources/N=40/N=50; LEARN retained but inactive; config/tool contract equality | 3/3 PASS |
| Route state | blind lane cannot be skipped; citation reopening; new-Y reopening/no retrigger; reopened-frontier completion block; valid completion | 5/5 PASS |
| Search snapshots | exact-key/hash reuse; contradictory completed snapshot rejection | 2/2 PASS |
| Semantic reuse/batching | rediscovery reuse versus genuine revision; 25-title/10-abstract individual decisions; append-only revision event | 3/3 PASS |
| Strict bundles | complete required core; missing required member; conflict; optional-role absence; non-transitivity; two-premise explicit reuse; transfer rationale; threshold-shift joint bundle | 8/8 PASS |
| Evidence/retrieval cache | factual-cache non-propagation/regime mismatch; one verified text/extraction reused and version mismatch blocked; one auxiliary acquisition with separate links | 3/3 PASS |
| Route-aware execution | weak E preserves capacity; weak A/F closes both; irrelevant null skip; weak-E descriptive null audit; derived outputs unchanged for viable routes | 5/5 PASS |
| Synthetic lifecycle | pre-freeze init → structured write → derive → validate → resume, with a retired unused ID remaining retired | 1/1 PASS |

Total: **77/77 PASS**.

## 14. Validation results

- Draft 2020-12 schema meta-validation: **12/12 PASS**.
- Pre-freeze input/schema/category audit: **PASS**.
- Entire unit suite: **77/77 PASS**.
- Clean synthetic lifecycle in a temporary runs root: **PASS**; no repository `runs/` write.
- Resume without reset and immutable-input compatibility: **PASS**.
- ID retirement/recovery: **PASS** (`P000002` retired unused; next allocation after resume was `P000003`).
- Historical CALIB package/schema refusal and aggregate-hash immutability: **PASS**.
- Query rendering, lexical provenance, and conservative bounds: **PASS**.
- Route ordering/reopening/completion tests: **PASS**.
- Evidence-bundle and threshold-shift tests: **PASS**.
- Route-aware and retrieval-cache tests: **PASS**.
- Six-anchor derived-view tuple reapplication plus joint threshold-shift bundle check: **PASS**.
- Python compile check with a temporary bytecode cache: **PASS**.
- `git diff --check`: **PASS**.
- Derived scientific implementation diff: **none**.

Expected pre-freeze blockers remain visible rather than being filled by this task: registration status is pre-freeze, publication cutoff is null, preferred/fallback search source fields are not frozen, and query documents still contain draft/TODO markers.

## 15. Remaining pre-freeze TODOs and clean-room concerns

Before freeze:

- decide whether to redesign or deliberately omit the generic LEARN blind block;
- set the publication cutoff and interpretation;
- freeze preferred search/citation sources and deterministic fallbacks;
- resolve remaining query template/tie/failure details and remove draft-only historical ambiguity where appropriate;
- run the separately planned clean-room/minimal-instruction sufficiency test in a fresh session without anchor gold or calibration outputs;
- address any scientific ambiguity revealed by that held-out test before registration.

The future METHODS crosswalk should map three distinct layers one-to-one: scientific premise/bundle rules in `PROTOCOL.md`, operational state/cache/snapshot rules in `AGENTS.md`, and concrete schema/validator fields. The present split is auditable but lengthy; route viability, descriptive null analysis, and constraint-ready derivation will require especially careful separate subsections so readers do not mistake execution short-circuiting for scientific exclusion. This is a documentation-structure concern, not an unresolved execution rule, and was not solved here because README/METHODS work is explicitly deferred.

The clean-room test must not receive this report, the anchor regression diagnostic, expected anchor codes/experiment choices, or calibration outputs that reveal expected answers.
