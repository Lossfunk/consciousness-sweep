# Clean-room pilot 001 revision report

## 1. Pilot archive path and hashes

The read-only archive is `diagnostics/cleanroom_pilot_001/`. `SHA256SUMS` contains one hash for every archived file other than itself and passes a complete `shasum -a 256 -c` verification.

Key hashes:

| Artifact | SHA-256 |
|---|---|
| `SHA256SUMS` | `cd84ba81a11b2e4dc3079656974c34d1decad02cead482053e12ea97b80d397e` |
| provenance `README.md` | `f02c774b37ca9e0168cc10722700499b18d2bbdddfeb31ff50d2d607428286be` |
| exact `run/run_summary.md` | `f9fba55ac1d5d58d85005f9774167e792c4b2ebab0bdb59b0005e102cbae4f8e` |
| `run/experiments_master.csv` | `3909235dcb53fefde91557e3edd7284c507e2c4e3264a7f3055215a6a75e97c0` |
| `run/decision_log.jsonl` | `8f910d18390b5de6a85ee70ea24f9f2c02c9e7f3977639ab043443a495f3a09b` |
| `run/run_state.json` | `47e2210f293b749aaf875e7e8d387b8352d937e3fcc526b563c88b554f2dd7cb` |

The archive contains the complete scientific output, source assets and extractions, state, decision history, derived views, input and final-checkpoint manifests, and execution artifacts. Transient Swift/Python bytecode caches and the empty write-lock file were excluded. Every copied run file is byte-identical to the source run. The archive has no user-writable files.

## 2. Source package commit

Pilot 001 used commit `0be0cc2d0a18dfbec320f8a2ace0b16573914f8c`, protocol `draft-0.8.1`, package `prefreeze-package-0.8.1`, and schema `prefreeze-schema-0.8`. The run state could not discover the commit because the clean-room fixture intentionally lacked Git metadata; the clean-room manifest independently records the exact commit.

## 3. Exact minimal prompt

```text
This is a bounded pre-freeze diagnostic, not a literature sweep.
Read PROTOCOL.md and AGENTS.md fully and follow the method they specify.
Using only the papers supplied in `sources/`, evaluate the scientifically\
relevant X→Y comparisons under the current package.
Produce structured, auditable classifications using the package's terminology\
and schemas, together with a concise final report explaining the evidence for\
each decision.
Do not search for or retrieve additional literature.\
Do not access files outside this workspace.\
Do not assume that every experiment in a paper qualifies.\
Report uncertainty rather than filling gaps by guesswork.
Validate the resulting diagnostic outputs with the canonical package tools\
where applicable.
```

## 4. Complete anchor-level pilot adjudication

The full per-anchor, per-dimension audit is in `diagnostics/cleanroom_pilot_001_adjudication.md`. It separately evaluates focal comparison discovery, X, Y, structure, A/E/F, bundles, awareness effect, unaware-capacity identity, null/equivalence, Meyen, statistics, and constraint-ready output for all six anchors.

Summary:

| Anchor | Primary adjudication | Key result |
|---|---|---|
| Ben-Haim | **A** plus **B/F** | Late trialwise comparison is potentially clean; early human E-diagnostic is possible over-permissiveness; monkey A is source-limited |
| Keizer | **A** | Strong validated unawareness, positive binding/retrieval capacity, no detectable difference, no equivalence, statistics concern |
| Lamy | **E** | Scalar component rows replaced the unassessed coherent factorial focal comparison |
| Lin & Murray | **A** | Correct factorial immediate-orienting relation, bundles, exact capacities, and separate aftereffect |
| Persaud | **A/C** | Awareness-linked metacognitive difference survives; blind-field positive capacity is corrected to unclear |
| Tsushima | **A/B** | Joint threshold-linked E structure recovered; strong A/statistics limited by absent supplement |

## 5. Clean passes

- Keizer is a strong clean-room success, including the statistical/robustness caveat and refusal to infer equivalence.
- Lin & Murray's immediate factorial relation, premise-specific cross-experiment validation, capacity identity, and route outputs are clean.
- Persaud's awareness-linked metacognitive difference is clean, and the pilot already uses the corrected `unaware_capacity = unclear` value.
- Tsushima's joint threshold/dip-shift E reasoning is clean for the supplied main-article evidence.
- Ben-Haim's late same-physical-regime/trialwise comparison was separately found, and adaptive opposite-rule capacity was correctly not inferred from below-chance/default cue-following.
- Across anchors, the pilot did not inflate nonsignificant results into equivalence.

## 6. Source-fixture limitations

- Tsushima's official supplement was absent, so visibility-validation sensitivity, transfer, and several control statistics could not establish strong A.
- The external monkey awareness-validation source cited by Ben-Haim was absent, so monkey A remained transfer-risk.
- These are fixture limitations, not reasons to weaken or change A.

## 7. Gold corrections

Persaud's blind-field metacognitive capacity is corrected from any superseded diagnostic gold of `supported` to `unclear`. The reported blind-field correlation (`r=.30`) is not accompanied by an adequate direct positive test against zero. The direct Fisher comparison still supports an awareness-linked difference. Machine-readable diagnostic provenance is in `diagnostics/cleanroom_pilot_001_gold_corrections.json`.

## 8. Ordinary model-variance candidates

No observed disagreement is confidently classified as ordinary model/execution variance. The clean-room fixture intentionally excluded the earlier anchor-regression and calibration diagnostics, so a missing historical expectation cannot be reconstructed or reclassified by guesswork.

## 9. Generic method underspecification

The Lamy-like failure is the sole repair target: an evaluator could instantiate accurate scalar component rows before asking whether the experiment's critical interaction defined one coherent factorial-functional relation. Draft-0.8.1 allowed factorial Y but did not make the check temporally mandatory or durably auditable.

## 10. Possible method over-permissiveness

Ben-Haim Experiment 1 received `E-diagnostic` because the visible/unseen sign reversal defeats a monotonic same-process strength account. A plausible evidence-only alternative remains: sufficient evidence may enable acquisition/access/application of the opposite-location mapping, producing reversal without awareness as the operative variable. This is analyzed, not repaired, in `diagnostics/ben_haim_exp1_e_diagnostic_pilot_issue.md`.

## 11. Persaud capacity gold correction

The diagnostic standard is now explicit:

- awareness-linked metacognitive difference: `difference-supported`;
- blind-field positive metacognitive capacity: `unclear`;
- constraint-ready awareness-difference route: retained;
- constraint-ready unaware-capacity route: not retained.

No registered-facing scientific rule changed to produce this result.

## 12. Exact generic pre-atomization rule added

Before final comparison decomposition, every experiment with multiple relevant factors/cells/simple effects must answer:

1. Is the critical hypothesis/statistic testing whether X changes one coherent downstream functional mapping?
2. Do the component effects jointly operationalize the same conservative function-level Y?
3. Would scalar-only evaluation lose the meaning of the critical interaction, crossover, conditional mapping, or structured pattern?

If yes, instantiate the factorial focal comparison first, record its components, and assess A/E/F and bundles for that whole relation. Optional scalar comparisons may coexist but must link to and may not replace the focal. If no, record why the components are genuinely distinct functions or why no common Y is defensible.

The complementary guardrail requires a conservative common Y, a genuine common mapping and inferential target, no conflation of substantively distinct processes, and empirical rather than post-hoc grouping. `interaction exists` is explicitly insufficient.

## 13. PROTOCOL changes

- Version advanced to `draft-0.8.2`; status remains pre-freeze.
- Section 2.5 is now the mandatory pre-atomization functional-structure check.
- Scalar/factorial definitions moved to Section 2.6 and now include the no-forced-merger criteria.
- The full-text order performs the check before decomposition and focal-row creation.
- The unchanged strict E rule is clarified for the whole factorial focal relation and its direct alternative-control bundle member.

A, unaware-capacity, no-detectable/equivalence, Meyen, discovery coverage, QCAL/QDYN bounds, and stopping rules were not changed. F changed only in its existing factorial operationalization; its eligibility categories and gate are unchanged.

## 14. AGENTS changes

- Status advanced to `draft-0.8.2, pre-freeze`.
- The evaluator must log an experiment-level pre-atomization decision before finalizing comparison rows.
- A required focal comparison must be reserved/instantiated before optional linked scalar components.
- Completed rows must carry the specific assessment and reason; the generic structural-audit flag cannot substitute.
- Factorial E-diagnostic bundles must identify the member addressing the first-order alternative.

## 15. Schema and tooling changes

Schema advanced to `prefreeze-schema-0.8.1` because semantics changed. `experiments.schema.json` adds only:

- `functional_structure_assessment`: `not-assessed | not-applicable | scalar-justified | factorial-functional-required`;
- `functional_structure_reason`;
- `factorial_focal_comparison_id` for optional scalar components.

Schema conditionals prohibit a fully evaluated temporary state and enforce consistent scalar/factorial combinations. Validation tooling now:

- requires multi-row scalar decompositions without a focal to record `scalar-justified`;
- requires a focal whenever a row declares `factorial-functional-required`;
- checks linked components point to a same-experiment focal instantiated earlier;
- requires a factorial `E-diagnostic` bundle to contain a required, supportive, decision-used `alternative-explanation-control` member.

Preflight checks the fields/categories. Package version advanced to `prefreeze-package-0.8.2`.

## 16. Why the repair is generic

Registered-facing prose, schemas, tools, and tests use only function-level and synthetic terminology. No anchor surname or expected paper-specific classification was added to registered-facing inputs. The rule applies to any multifactor experiment and preserves scalar comparisons whenever a coherent common Y is not scientifically defensible.

## 17. Factorial E-bundle clarification

`E-diagnostic` applies to the whole focal functional relation. Joint simple effects can rule out the stated same-Y scalar account even when individual effect magnitudes differ, but a cross-Y dissociation or interaction alone is insufficient. Any borrowed support must use a strict bundle, and the direct result controlling the first-order alternative must be explicitly identified.

## 18. Ben-Haim Experiment 1 issue

The full diagnostic is `diagnostics/ben_haim_exp1_e_diagnostic_pilot_issue.md`. It finds the evidence-only process-enablement account genuinely viable, inventories physical/evidence/learning/knowledge confounds, explains why Experiment 7 is cleaner but not automatically decisive, lists observable discriminators, and ranks three future formulations from a modestly broadened alternative to a residual-awareness/intervention requirement.

## 19. Why E-diagnostic was not changed

One Codex run establishes possible ambiguity, not the appropriate breadth of a revised causal standard. Tightening E could unintentionally eliminate intended threshold-shift, late trialwise, or factorial-functional cases. Candidate formulations should first be tested by independent agents against source-complete fixtures. The current E categories and core decision criterion remain unchanged.

## 20. Source-complete future-pilot policy

Future bounded clean-room fixtures should include the exact main article and official/author supplementary material belonging to that article when locally available and part of its evidential record. They should not automatically include external auxiliary papers, validation studies, or broader literature unless the pilot is explicitly testing auxiliary retrieval. Registered retrieval rules are unchanged.

## 21. Decontamination and leakage status

`tools/leakage_guard.py` passes after all registered-facing edits. Anchor-specific archives, adjudication, gold corrections, and E analysis remain under `diagnostics/`; synthetic tests remain under `tests/`. Both directories are outside the registered-facing allowlist. No source paper, supplement, or external literature was retrieved.

## 22. Version changes

| Component | Before | After |
|---|---|---|
| Protocol | `draft-0.8.1` | `draft-0.8.2` |
| Package | `prefreeze-package-0.8.1` | `prefreeze-package-0.8.2` |
| Schema | `prefreeze-schema-0.8` | `prefreeze-schema-0.8.1` |
| Registration | `pre-freeze` | `pre-freeze` |

No freeze, registration, new run, CALIB, pilot #2, commit, repository README, or METHODS file was created.

## 23. Tests and validation results

| Validation | Result |
|---|---|
| Draft 2020-12 schema meta-validation | **PASS**, 12 schemas |
| Pre-freeze canonical preflight | **PASS**, with expected pre-freeze TODOs |
| Registered-mode preflight | **EXPECTED BLOCK**, exit 2 for unfrozen status/cutoff/sources/query markers |
| Registered-package leakage guard | **PASS** |
| Python import/compile | **PASS** with `PYTHONPYCACHEPREFIX` confined to `/private/tmp` |
| Full available unit suite | **PASS**, 15/15 |
| A–G pre-atomization/factorial tests | **PASS** |
| Evidence-bundle completeness and factorial alternative-control tests | **PASS** |
| Clean synthetic initialization/derive/validate/resume lifecycle | **PASS** |
| Identifier retirement/non-reuse | **PASS** (`P000001` retired; next allocation `P000002`) |
| Route reopening/state idempotence | **PASS** |
| Immutable search-window/result-set snapshot tests | **PASS** |
| Historical package/schema compatibility refusal | **PASS**, mismatch rejected before current-schema validation |
| Pilot archive full SHA-256 verification | **PASS** |
| Pilot source/archive byte comparison | **PASS** for all copied run files |
| Archive read-only permission check | **PASS** |
| Structural pilot non-regression | **PASS**: old scalar-only omission would now violate procedure |
| Whitespace/conflict-marker scan | **PASS** |
| `git diff --check` | **UNAVAILABLE**: the supplied clean-room workspace intentionally has no `.git` repository |
| Historical CALIB filesystem immutability | **NOT DIRECTLY AUDITABLE**: no CALIB runs or calibration diagnostics exist in this fixture; none were created or modified. Generic historical compatibility is covered above |

The initial unconstrained `compileall` attempt was blocked because macOS tried to write its user bytecode cache outside the workspace. Rerunning with the cache under `/private/tmp` passed; this was an environment write-location issue, not a syntax/import failure.

The archived pilot is historical under draft-0.8.1 and was not migrated or revalidated against the changed schema. Its original canonical derive/validate passes are preserved in its exact final report. Current-package derive/validate/resume behavior was validated through the clean synthetic lifecycle.

## 24. Remaining pre-freeze TODOs

- Resolve the open E-diagnostic alternative-class issue with independent pilots/agents.
- Run a source-complete clean-room pilot under draft-0.8.2; do not expose diagnostics/gold to it.
- Decide the final publication cutoff and timezone interpretation.
- Freeze permitted search sources and fallback order.
- Resolve remaining query template/draft markers and the generic LEARN blind-query decision.
- Restore or inspect historical anchor/calibration/decontamination provenance in the actual main repository; it was intentionally absent from this fixture.
- Circulate and adjudicate remaining scientific ambiguities before freeze.
- Only after those steps, freeze versions and register.

## 25. Recommendation for the next clean-room pilot

Run one fresh, independent, source-complete bounded pilot after this revision is placed in the actual main repository. Use the same minimal source-only prompt, provide each exact main article plus its official supplement where locally available, keep external auxiliary works absent unless retrieval is the test target, and ensure diagnostics/tests/gold/manuscript files are excluded from the fixture.

Primary non-regression question: does the evaluator perform the pre-atomization check, instantiate a coherent factorial focal comparison before any optional scalar components, and preserve genuinely distinct scalar Ys without forced merging?

Secondary diagnostic question: apply Candidate 1 and Candidate 2 from the Ben-Haim issue as blinded audit overlays—not protocol changes—to early sign-reversal, late trialwise, threshold-shift, and factorial-functional cases. Compare independent agent rationales before deciding whether E should change.
