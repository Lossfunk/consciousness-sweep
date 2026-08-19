# Draft-0.8.3 pilot-002 revision report

## 1. Starting state

- Starting commit: `bdb762240b9df98b921e8813b566fc9bb1be5100`.
- Starting worktree: clean (`git status --short` produced no entries).
- Starting versions: protocol `draft-0.8.2`, package `prefreeze-package-0.8.2`, schema `prefreeze-schema-0.8.1`.
- The work was performed in the real repository. No unrelated changes were present.
- No network/API call, literature search, paper retrieval, CALIB, pilot 003, registered run, freeze, tag, preregistration, or commit was performed.

## 2. Pilot-002 archive and hashes

The complete run and clean-room fixture provenance were copied to `diagnostics/cleanroom_pilot_002/`. The archive contains the unchanged run, its empty lock file and empty `fulltexts/` directory, fixture manifest, original source-file hash manifest, provenance README, and a SHA-256 manifest. After source/archive byte comparison and hash verification, the archive was made read-only.

Key hashes:

- `SHA256SUMS`: `1709304d67692f1137385aaf59c7d0b3225874cacd63db28ad996834e4d3fae3`
- archive `README.md`: `b354a5ac7e8879790bd13bcde10d48d9d53c92a4d73d6344c326c007139c7d63`
- `run/experiments_master.csv`: `fad93ef452c2cf43c521f0e93f1f032e78e9b5dd7f4e2a07cc2d83a2585d6e22`
- `run/decision_log.jsonl`: `7716cd560f228b5169f618675cd295c9d65173c044ae312b16c1ab14c16c8c27`
- `run/run_state.json`: `87d9f0376464ccb86b06b10b67f63f4a5e47702ac6d28a7d9fe388ecf763eecb`
- `run/run_summary.md`: `07f80157123abb79a54e4afc34ff8af42c3d1616203293728d21e98b35a667e9`

The complete per-file hashes are in the archive manifest. The README records the exact minimal prompt, source commit and versions, fresh Codex session, six-main-article plus same-article-supplement source policy, absence of external auxiliary literature, hidden diagnostic/gold/test/manuscript material, no network retrieval, and run-state model/harness/times. It explicitly prohibits use as registered-facing input.

## 3. Complete pilot-002 adjudication

The full dimension-by-dimension adjudication is in `diagnostics/cleanroom_pilot_002_adjudication.md`. The compact result is:

| Anchor | Focal/structure | A/E/F and bundles | Results/capacity | Diagnostic class |
|---|---|---|---|---|
| Ben-Haim | Relevant early/late and human/monkey relations found; reversals represented factorial-functionally | Human A clean, monkey A source-limited; early E bundle demonstrates reversal but does not resolve design-motivated contingency/policy knowledge | Direct human differences recorded; strategic capacity correctly refused, but early regulation row changes its capacity target to automatic orienting | **A/B/F** |
| Keizer | Coherent binding/retrieval mapping found | A-validated, E-physical-only, F-meaningful are clean | Positive focal capacity retained, but a reported direct mask × binding comparison was incorrectly marked not tested; no equivalence inflation | **A/E** |
| Lamy | Component rows found, focal operational mapping omitted | Component A/F coding restrained; focal E and bundle never assessed | Component results are useful, but scalarization rests on capture/update labels rather than positive functional separation | **A/E** |
| Lin and Murray | Immediate and later effects combined, unlike pilot 001's temporal separation | A/F clean; E potentially valid conditional on the chosen mapping | Direct effect audited, but a broader parent capacity was supported by only an orienting component | **A/D/E/F** |
| Persaud | Functional metacognition separated from BOLD | A-direct, E-matched, meaningful-Y/BOLD distinction clean | Awareness-linked difference survives; blind-field positive capacity remains unclear | **A/C** |
| Tsushima | Behavioral threshold mappings and fMRI registration found | Supplement correctly strengthens behavioral A while leaving fMRI transfer weaker; threshold-shift E and F separation clean | Direct differences retained, but interference/failure of control was incorrectly used as positive regulation capacity | **A/F** |

Class summary:

- **A — clean pass:** source-complete behavioral A use, most conservative X/Y coding, meaningful-versus-registration F separation, explicit evidence provenance, statistical restraint, and refusal to infer equivalence.
- **B — source-fixture limitation:** unavailable external monkey awareness validation in Ben-Haim.
- **C — gold-standard correction:** Persaud blind-field capacity remains `unclear`; pilot 002 correctly reproduces the accepted correction.
- **D — ordinary model variance:** Lin's combined spatiotemporal mapping versus separate temporal-stage functions, now requiring explicit positive justification.
- **E — generic method underspecification:** Lamy focal-structure omission, Keizer descriptive-audit omission, and the previously implicit functional-identity basis.
- **F — method over-permissiveness:** early Ben-Haim E without task-policy contrast integrity and parent capacities supported by different component consequences.

## 4. Files changed

Canonical registered-facing or execution files:

- `PROTOCOL.md`
- `AGENTS.md`
- `config.yaml`
- `schemas/experiments.schema.json`
- `schemas/evidence_bundles.schema.json`
- `tools/execution_contract.py`
- `tools/derive_outputs.py`
- `tools/validate_run.py`
- `tools/preflight.py`

Tests:

- `tests/test_revision_083.py` (new)
- `tests/test_factorial_structure.py`
- `tests/test_pipeline.py`
- `tests/test_anchor_non_regression.py`

Diagnostic-only additions:

- `diagnostics/cleanroom_pilot_002/` (complete read-only archive)
- `diagnostics/cleanroom_pilot_002_adjudication.md`
- `diagnostics/cleanroom_pilot_002_gold_corrections.json`
- `diagnostics/draft_0_8_3_pilot_002_revision_report.md`

Root `README.md`, `METHODS.md`, seeds, queries, requirements, QCAL/QDYN settings, and completed runs were not changed.

## 5. Version changes

- Protocol: `draft-0.8.2` → `draft-0.8.3`.
- Package: `prefreeze-package-0.8.2` → `prefreeze-package-0.8.3`.
- Schema: `prefreeze-schema-0.8.1` → `prefreeze-schema-0.8.2`, because required experiment and evidence-bundle fields changed.
- `registration_status` remains `pre-freeze`.

## 6. Operational functional-identity rule

Before scalar atomization, the evaluator now records whether components use the same information-bearing X, same downstream output, same task and relevant temporal/computational stage, a factor that changes a relation/property of X, a higher-order statistic about one input→output mapping, and a defensible conservative common function. When the relevant combination establishes one mapping, the factorial-functional focal comparison must be instantiated first and audited before optional component rows.

The schema adds `functional_identity_basis`. Finalized rows must use `common-operational-mapping` for factorial structure, a positive separation basis for scalar structure, or `not-applicable-single-effect` for a true single-effect case. Runtime validation also enforces focal-before-component linkage.

## 7. Effect/mechanism labels do not define Y

Facilitation, interference, benefit, cost, capture, suppression, and sign are observed effect descriptions. Updating, inhibition, filtering, and disengagement are mechanism interpretations. Neither category independently establishes a distinct downstream function. Functional identity is determined at the conservative operational input→output level, preserving the existing F distinction between function and mechanism.

## 8. Scalar-separation rule

Scalar separation remains available when outputs operationalize different functions, effects occupy substantively different temporal/computational stages, input→output relations differ, or no conservative common function exists. The validator accepts only the corresponding positive bases: `distinct-downstream-outputs`, `distinct-computational-stages`, `distinct-input-output-relations`, or `no-conservative-common-function`. “Different effect names” and “different mechanism labels” are rejected as insufficient.

## 9. Capacity-identity invariant

The invariant is now:

> one comparison = one focal `Y_label` = one possible unaware-capacity target.

`unaware_capacity_claim` must exactly equal `Y_label`. Supported capacity additionally requires `unaware_capacity_evidence_scope = whole-focal-Y`. A component result cannot support its parent focal function; an independently meaningful component requires its own linked comparison and must independently satisfy F, positive unaware evidence, route-specific statistics, and applicable Meyen requirements.

## 10. Capacity schema and validation

`experiments.schema.json` adds required `unaware_capacity_evidence_scope` with `whole-focal-Y`, `component-only`, `unclear`, and `not-applicable`. Supported capacity is schema-limited to `whole-focal-Y`; `not-tested` requires `not-applicable`. Because JSON Schema cannot compare two field values, `capacity_identity_errors()` and `validate_run.py` enforce exact `unaware_capacity_claim == Y_label`. Derived capacity and equivalence views independently repeat exact identity and whole-focal-scope gates, preventing a malformed row from entering outputs even before a full validation checkpoint.

## 11. Descriptive same-Y comparison audit

`difference_tested` now records the existence of a direct same-Y aware/unaware difference or interaction independently of E. If it is `yes`, result inspection is required and the schema requires a named critical effect, estimate, interpretable-estimate status, route-specific statistical status, and reason. `not-tested` is allowed only when no relevant direct comparison was actually tested/reported.

For a statistically supported direct difference with weak A/E/F, the observed test remains recorded but `awareness_effect` is `unresolved`; it cannot enter the constraint-ready awareness-difference route. A no-difference result can receive the descriptive `no-detectable-difference` label when existing standards are met. Equivalence still requires positive null evidence and the strongest invariance route still requires strong A/E/F.

## 12. Generic weak-E/null behavior exposed by Keizer

A direct mask × binding-like interaction can no longer be erased because E is physical-only. The test must receive a descriptive audit. A nonsignificant interaction may be classified as no detectable difference only under the unchanged descriptive statistical rules; it cannot become equivalence without positive equivalence/Bayesian/informative-interval evidence. Weak E prevents a constraint-ready awareness inference but does not affect an independently supported focal capacity route.

## 13. E-diagnostic contrast integrity

Every `E-diagnostic` evidence bundle now records a bounded task-state contrast-integrity disposition. It identifies any admissible alternative, why it is viable, its observable prediction, the direct evidence/control member, and a resolution of `ruled-out`, `unresolved`, or `not-applicable`. An unresolved viable alternative prohibits `E-diagnostic`. A `ruled-out` disposition must point to a required, supporting, decision-used `alternative-explanation-control` link. An unresolved disposition must still identify the evidence/control member showing why resolution failed. Non-E bundles use `not-applicable` and null alternative fields.

## 14. Exact bounded alternative class

An admissible contrast-integrity alternative must be:

1. finite and explicitly named;
2. independently motivated by the design/task;
3. capable of changing focal Y;
4. supported or reasonably implied as changing across the contrast; and
5. associated with an observable prediction or control.

The intended class includes instruction, learned contingency, explicit task-relation knowledge, response mapping, policy, attentional/control set, task relevance, feedback/training, block-specific strategy, and knowledge needed to execute the focal mapping.

## 15. Exclusion of unlimited threshold-process skepticism

Stimulus strength, masking, sensory evidence, and internal-evidence differences are the ordinary first-order-E problem; they are not automatically contrast-integrity failures. An arbitrary hidden process proposed only after the result, or the generic suggestion that stronger evidence enables something, is inadmissible. This keeps the new guard finite and prevents it from becoming a demand to rule out every imaginable threshold process.

## 16. Why within-regime comparisons remain possible

When instructions, response mapping, contingency knowledge, policy, and physical task configuration are fixed and only trialwise first-order evidence differs, the contrast-integrity disposition can be `not-applicable`. The ordinary strict E-diagnostic test then proceeds. Thus a within-regime structured contrast is not rejected merely because sensory evidence varies.

## 17. Diagnostic effect on early sign reversals

The early Ben-Haim-like reversal is not rejected merely because it is a reversal. It is re-audited because acquiring/recognizing the predictive contingency and adopting the corresponding response/control policy are independently task-motivated, differ with the contrast, can determine Y, and make observable predictions. The archived pilot bundle did not address that alternative. Under the new generic rule an unresolved alternative prohibits `E-diagnostic`; the final paper-specific E code is deliberately not hard-coded into registered-facing files.

## 18. Preservation of threshold-shift and factorial E logic

Factorial structure still does not imply `E-diagnostic`. The focal common Y, competing first-order account, its predicted mapping, observed violating mapping, required members, and a direct first-order-alternative-control remain mandatory. Threshold-linked nonmonotonicity plus an experimentally shifted threshold remains representable when the complete same-Y bundle defeats the specified evidence account and no separate task-state cochange remains. Optional component rows cannot substitute for the focal factorial row.

## 19. Persaud diagnostic gold

The diagnostic-only gold remains: the awareness-linked metacognitive difference survives, while positive metacognitive capacity in the blind field remains `unclear`. This is recorded in `cleanroom_pilot_002_gold_corrections.json`. No named Persaud result appears in protocol, agent instructions, schemas, runtime tools, seeds, or queries.

## 20. Decontamination and leakage

All canonical rules and synthetic tests are generic. Named anchor adjudication is confined to `diagnostics/` and the already diagnostic-only anchor regression test. The leakage guard passed with no non-neutral seed rationale, named anchor answer context, or anchor-specific runtime identifier. The archived pilot README states that the archive must not enter registered-facing or independent-run inputs.

## 21. New tests

`tests/test_revision_083.py` adds the requested synthetic matrix:

- Functional identity (5): common mapping despite effect labels; mechanism-label irrelevance; genuinely distinct functions; rejection of label-only scalarization; focal plus linked components.
- Capacity identity (5): interference is not regulation; automatic bias is not strategic rule use; own component comparison can qualify; novel capacity target rejected; one positive factorial component does not support parent capacity.
- Descriptive comparison (4): weak-E nonsignificant direct test remains descriptive/non-equivalent; weak-E significant direct test remains unresolved; absent direct test permits not-tested; strong-E difference route remains unchanged.
- Contrast integrity (6): task-policy cochange blocks unresolved E; fixed policy does not independently block; blockwise strategy must be audited; arbitrary hidden process does not block; threshold shift remains possible; explicit control can rule out a design-motivated alternative.

Existing schema, factorial, pipeline, lifecycle, and diagnostic non-regression fixtures were updated only for the new required fields and settled route expectations.

## 22. Complete validation results

All checks passed:

- Draft 2020-12 schema meta-validation: **12/12 schemas pass**.
- Pre-freeze preflight: **pass**, with only the intentional pre-freeze TODOs (`registration_status`, publication cutoff, preferred/fallback sources, and query draft markers).
- Leakage guard: **pass**.
- Entire repository test suite: **119 tests pass**.
- Requested functional-identity, capacity-identity, descriptive-comparison, and contrast-integrity synthetic tests: **20/20 pass** within the suite.
- Strict evidence-bundle completeness/conflict/direct-link tests: **pass**.
- Clean synthetic init → structured write → derive → validate → resume: **pass** in both lifecycle suites.
- Identifier retirement/non-reuse: **pass**.
- Concurrent allocation and CSV writes: **pass**.
- Route reopening/idempotence and completion blocking: **pass**.
- Immutable search snapshot hashing/reuse/conflict rejection: **pass**.
- Historical package/schema compatibility refusal before current-schema validation: **pass**.
- QCAL/QDYN executable bounds and retired-family checks: **pass**.
- Python compilation/import: **pass** with an external bytecode cache.
- Pilot archive SHA-256 verification: **all files pass**.
- `git diff --check`: **pass**.

No clean scientific run was created for validation; lifecycle tests used temporary directories.

## 23. Historical CALIB immutability

Before editing, complete per-file SHA-256 manifests were captured for CALIB_CODEX_001 through CALIB_CODEX_004. After the revision, every file revalidated byte-for-byte:

| Run | Files | Bytes | Baseline manifest SHA-256 | Result |
|---|---:|---:|---|---|
| CALIB_CODEX_001 | 18 | 6,580,530 | `3774cd957b66aeb766d5e4ded4aea42f293d76caa0738dd2cc32f12aca5bf507` | unchanged |
| CALIB_CODEX_002 | 16 | 6,769,627 | `3e0ee4bb47237157f7531675fc81b65e4fc702edb61da9939ff803b1d9d4e80a` | unchanged |
| CALIB_CODEX_003 | 25 | 15,942,522 | `7dcc39299b56c329e8be5ac304c4ab596937684b03af1f06cbd41dc6016e071b` | unchanged |
| CALIB_CODEX_004 | 15 | 1,374,547 | `877b4d7b8acfa5e09081a40831601193ef533d333813f79df0bc9523a0902492` | unchanged |

No historical run was migrated. Compatibility-refusal tests confirm that old package/schema runs are rejected before applying current schemas.

## 24. Remaining scientific and pre-freeze issues

- The final E code for the early task-policy sign-reversal paradigm remains a paper-specific adjudication question; draft-0.8.3 supplies the missing finite audit rather than an answer key.
- The final focal E/outcome for the omitted common spatial-handling mapping remains to be established by an independent run.
- The combined-versus-separated temporal mapping remains legitimate model variance that must be resolved with the new positive operational basis.
- Exact claim/Y identity is intentionally strict and may cause wording friction, but it is auditable and avoids introducing a new ontology before freeze.
- The package remains intentionally non-registerable: cutoff/source choices and query draft markers are still unfrozen.
- Objective invisibility, A transfer, E-matched, generic E-diagnostic structures, F categories, bundles, Meyen, statistics, no-detectable/equivalence distinction, discovery/search architecture, QCAL/QDYN bounds, principal-first/blind-last order, reopening, snapshots/resume, and independent-run isolation were not scientifically weakened or redefined.

## 25. Recommendation

Run **one final fresh Codex clean-room pilot** after reviewing this patch, using the same bounded closed-world source policy and a newly stripped workspace containing only draft-0.8.3 registered-facing package files plus the six main articles and same-article supplement. It should test whether a fresh agent independently: (1) instantiates the focal operational mapping before scalar components, (2) keeps every capacity target identical to focal Y, (3) audits direct same-Y comparisons despite weak E, and (4) applies contrast integrity to the early task-policy reversal without rejecting clean fixed-policy or threshold-shift cases. Do not expose this report, prior pilots, gold files, diagnostics, or anchor-specific tests to that agent.

The recommendation is for a future bounded pilot only. Pilot 003 was not run in this revision.
