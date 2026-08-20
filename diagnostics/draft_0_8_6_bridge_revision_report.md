# Draft-0.8.6 one-hop empirical bridge revision report

## 1. Starting commit

- Commit: `dbf83a708999ed9b78c76afb7d64912aae63929f`
- Commit summary: `dbf83a7 Add human-readable methods and documentation crosswalk`
- Starting versions: protocol `draft-0.8.5`; package `prefreeze-package-0.8.5`; schema `prefreeze-schema-0.8.4`; registration `pre-freeze`.
- The only starting worktree changes were the two authorized, untracked bridge diagnostic directories and their reports. They were read and verified but not rewritten.

## 2. Calibration evidence motivating K=1

The depth calibration found 23 confirmed CORE nodes among 647 logical papers reached from two parents. K=2 exceeded 10,000 deduplicated logical records before completing even 17 of 139 queued bridge parents, demonstrating frontier explosion beyond one bridge generation. The retrospective parent audit found five eligible strict empirical near-miss parents among 42 adequately full-text-evaluated works; both original calibration parents qualified. All five met both the “at least two” and “exactly two” formulations in the focal-experiment audit, while 14 nonempirical hubs were explicitly excluded. This supports the selected strict K=1 rule without reopening the completed calibration.

## 3. Files changed

Normative and human-readable files:

- `PROTOCOL.md`
- `AGENTS.md`
- `METHODS.md`
- `README.md`
- `config.yaml`
- `docs/methods_crosswalk.yaml`
- `docs/documentation_issues.md`

Durable schemas:

- `schemas/experiment_groups.schema.json`
- `schemas/papers.schema.json`
- `schemas/discoveries.schema.json`
- `schemas/search_log.schema.json`
- `schemas/run_state.schema.json`

Execution and validation:

- `tools/execution_contract.py`
- `tools/init_run.py`
- `tools/preflight.py`
- `tools/structured_write.py`
- `tools/validate_run.py`

Tests and report:

- `tests/test_pipeline.py`
- `tests/test_revision_085.py`
- `tests/test_revision_086.py`
- `diagnostics/draft_0_8_6_bridge_revision_report.md`

No historical run, pilot, seed, query instrument, comparison schema, A/E/F implementation, or prior bridge diagnostic was modified.

## 4. Version changes

- Protocol: `draft-0.8.5` → `draft-0.8.6`
- Package: `prefreeze-package-0.8.5` → `prefreeze-package-0.8.6`
- Schema: `prefreeze-schema-0.8.4` → `prefreeze-schema-0.8.5`
- Registration remains `pre-freeze`.

## 5. Final strict bridge definition

A BRIDGE is an adequately full-text-evaluated empirical, non-CORE logical paper with at least one genuine near-neighbor physical experiment containing exactly two clearly present CORE ingredients and one explicitly failed ingredient, together with a positive scientific rationale. Bridge status changes citation discovery only.

## 6. Same-experiment exact-two rule

The physical experiment row records specific X, awareness contrast/attempt, and plausible functional Y independently as `present`, `failed`, `unclear`, or pre-assessment `not-assessed`. `bridge_disposition = eligible` is valid only for one of the three exact two-present/one-failed combinations. The failed-ingredient field must identify that same failed ingredient. Paper derivation examines each group independently and never unions ingredients across experiments.

## 7. Empirical/full-text restriction

Paper rows now record empirical status and derived citation-node status. CORE, BRIDGE, and assessed non-node states require a retrieved, evaluated full text. Missing/manually requested/unavailable text derives `not-assessable-missing-fulltext`; it cannot establish a bridge or turn missingness into an ingredient failure.

## 8. Review/theory exclusion

Only `bridge_empirical_status = empirical` can derive BRIDGE. Reviews, theories, perspectives, commentaries, methods-only works, and generic conceptual works are normative nonempirical exclusions from dynamic bridge generation. Dedicated frozen review/discovery anchors remain unchanged.

## 9. Paper-level CORE precedence

`derive_paper_citation_node_status` derives CORE if any single group has all three ingredients, before considering bridge groups. Therefore a paper with one CORE experiment and a separate near-miss is handled as CORE. The near-miss audit can remain durable without downgrading the paper.

## 10. Lineage-aware K=1 semantics

Every encounter carries bridge-lineage depth 0 or 1. A strict bridge can expand only after at least one depth-0 encounter. Its children receive depth 1. A bridge at depth 1 cannot continue that lineage. K=1 is consequently a bound on consecutive non-CORE bridge generations, not a lifetime count of bridge nodes on a path.

## 11. CORE depth reset

CORE traversal resets the child lineage to depth 0 even when the CORE paper was found under a bridge. The synthetic tests cover CORE → BRIDGE → CORE and CORE → BRIDGE → CORE → BRIDGE behavior.

## 12. Discovery-order independence

Run state separately records depth-0 eligible, pending, and completed bridge-parent IDs. A paper first reached at depth 1 gains a pending expansion if later encountered independently at depth 0. Multiple eligible depth-0 encounters create one retrieval obligation while retaining each encounter's provenance.

## 13. Search-window/reuse behavior

Citation windows now have a deterministic identity over parent paper, direction, source, source parameters, publication cutoff, and optional requested maximum. Citation search rows record parent node status, parent bridge depth, and traversal basis. Validator checks event/route/direction agreement, basis/status agreement, and immutable keys. Completed identical windows reuse their snapshot rather than refetching. No bridge-specific source was hard-coded; bridge windows inherit the unresolved ordinary citation source/fallback policy.

## 14. Missing-text behavior

Title/abstract evidence cannot establish BRIDGE. Existing missing-text retrieval and manual-ingestion machinery remains authoritative. A later full-text reassessment can append a bridge decision and add/reopen the required citation obligation.

## 15. Frontier reopening/completion behavior

An eligible depth-0 bridge adds a pending citation-frontier obligation and reopens the citation frontier. A bridge-to-CORE revision removes the bridge obligation and reopens ordinary CORE recursion. Completion validation rejects any nonempty pending bridge-parent set. No paper-count, title-count, API-cost, runtime, parent-quota, or zero-yield stop was added.

## 16. Bridge versus QDYN distinction

Bridge reconciliation never changes `activated_normalized_y_labels` or process-frontier state. A bridge-discovered Y can activate QDYN only by independently meeting the unchanged §9.4 comparison-level activation rule.

## 17. Durable representation/schema changes

- Physical experiment: three controlled ingredient states, near-neighbor status, bridge disposition, failed ingredient, and rationale.
- Paper: empirical status, derived node status, and node reason.
- Discovery: per-encounter bridge-lineage depth and reason.
- Search: parent node status, parent bridge depth, traversal basis, and immutable citation-window requirements.
- Run state: depth-0 eligible, pending, and completed bridge-parent ID sets.
- Schema version advanced to `prefreeze-schema-0.8.5`; historical runs remain incompatible by design and are not migrated.

## 18. Synthetic tests added

`tests/test_revision_086.py` adds 25 focused tests covering all three possible exact-two failures; one-present/two-failed; unclear third ingredient; all-three CORE; nonempirical hubs; missing full text; vague-interest nonqualification; cross-experiment nonaggregation; CORE precedence; no dummy comparison; controlled vocabulary; K=1 lineage blocking; CORE reset; later depth-0 rediscovery; single obligation across routes; blind reopening; completion blocking; bridge→CORE and missing→bridge transitions; completed-window no-refetch; immutable citation-window reuse; search provenance; discovery lineage; and experiment decision events.

## 19. Non-regression results

The complete 194-test repository suite passed. This includes prior draft-0.8.x scientific regressions for awareness evidence, E-matched/E-diagnostic and anchored contrast integrity, alternative-control scans, F and functional identity, factorial structure, evidence bundles, capacity identity, direct differences, null/equivalence, statistics/Meyen, query instruments, screening, derived outputs, and anchor non-regression. The bridge implementation does not touch `experiments.schema.json`, `derive_outputs.py`, `query_instruments.py`, QCAL/QDYN configuration, seeds, or queries.

## 20. Documentation/crosswalk status

The human-readable layer was changed only where needed for the bridge method. Structural validation reports PROTOCOL 33/33 headings mapped, AGENTS 24/24 headings mapped, 33 METHODS targets, and 64 crosswalk rows, with zero unresolved or implementation-only mappings. The source-policy documentation issue now clarifies that bridge citation retrieval inherits the still-unfrozen ordinary policy.

## 21. Leakage status

The registered-facing leakage guard passed. No paper-specific bridge classification, diagnostic answer, anchor-specific runtime identifier, or sentinel cue was added to registered-facing files. The two diagnostics remain diagnostic-only evidence summarized generically here.

## 22. Complete validation results

- JSON Schema Draft 2020-12 meta-validation: PASS for all 13 schemas.
- Pre-freeze preflight: PASS with the expected pre-freeze TODOs only.
- Leakage guard: PASS.
- Documentation validator and coverage tests: PASS.
- Entire unit suite: PASS, 194 tests.
- New bridge eligibility/state/search tests: PASS, 25 tests.
- Synthetic init → structured write → derive → validate → resume and ID-retirement recovery: PASS through the repository lifecycle suites.
- Route reopening, concurrency, allocation uniqueness/non-reuse, immutable snapshot reuse, and historical compatibility refusal: PASS through the full suite.
- Python compile/import check: PASS using a temporary bytecode cache.
- `git diff --check`: PASS.
- No network/API call, literature retrieval, citation execution, scientific run, CALIB run, clean-room diagnostic, or commit occurred.

The pre-freeze TODOs remain: registration is pre-freeze; publication cutoff is null; preferred and fallback source order are empty; and `queries.md` retains draft markers.

## 23. Historical-run/pilot immutability

Before/after aggregate SHA-256 values are unchanged:

- Historical `runs/CALIB*`: `ddbd3b402c5f082a6bdabc22afe3a31e6e6f87de50712624f68d9d7546b63b44`
- Archived clean-room pilot trees: `d4a8c88f165dd49320f9d7f1437ee5c3dd96a4c4ec1737ee2baf49acc06b32c4`
- Both bridge diagnostic directories: `e52c61d3513726c8fed10aad153748c0075677feace8bdfc7b003d717d432968`
- Depth diagnostic report: `92625f3d5973cce0ad7b9c75c0ef28ac394412816001f604706856b30952782b`
- Parent-eligibility report: `db1dd5a4f1fc6748ddabf0bb3dd02f895b0b71fa4dbe68b7ed15e1281ac8ab13`

## 24. Remaining pre-freeze TODOs

Human decisions still required before registration are the publication cutoff, preferred/fallback search-source order including ordinary/bridge citation fallback, final query status, and the redesign-or-omit decision for generic LEARN. General METHODS language/flow simplification, `PROTOCOL_BRIEF.md`, freezing, registration, and tagging remain explicitly deferred.

## 25. Readiness for the later documentation pass

Yes. The bridge rule is now normatively specified, durably represented, mechanically validated, documented, crosswalked, and covered by synthetic tests. It is ready to be included in the later human-readable simplification and `PROTOCOL_BRIEF.md` pass after the remaining freeze decisions are resolved. The package itself remains pre-freeze.

## Critical final check

- **A. CORE recursion unchanged:** confirmed; the existing CORE criterion and recursive behavior remain, with only explicit bridge integration added.
- **B. Full-text empirical non-CORE bridge:** enforced by paper derivation and schema/validator gates.
- **C. Exactly two in one physical experiment:** enforced by experiment-group schema and derivation; no aggregation.
- **D. Third explicitly fails:** enforced; `unclear` cannot qualify.
- **E. No review/theory dynamic hubs:** enforced by the empirical gate; anchor route unchanged.
- **F. At most one consecutive bridge generation:** enforced by lineage depth 0/1.
- **G. No bridge-of-bridge continuation on one lineage:** enforced by traversal and expansion helpers/tests.
- **H. CORE resets depth:** enforced and tested.
- **I. Discovery-order independence:** later depth-0 encounters create the obligation; completed retrieval remains single-use/reusable.
- **J. Discovery-only effect:** no A/E/F, comparison, result, derived-output, evidence, statistical, Meyen, QCAL, or QDYN rule changed.
- **K. Missing text is not bridge evidence:** enforced through `not-assessable-missing-fulltext` and full-text gates.
- **L. Required expansions block completion without a resource cap:** enforced by pending bridge state and completion validation; no adaptive zero-yield rule exists.
