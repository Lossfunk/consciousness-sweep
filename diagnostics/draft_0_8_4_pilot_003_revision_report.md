# Draft-0.8.4 pilot-003 revision report

## 1. Starting state

- Starting commit: `bdb762240b9df98b921e8813b566fc9bb1be5100`.
- Starting versions: protocol `draft-0.8.3`; package `prefreeze-package-0.8.3`; schema `prefreeze-schema-0.8.2`.
- Starting worktree: only the expected, related draft-0.8.3 pilot-002 revision changes and diagnostic artifacts were present. No unrelated work was found, so the pass continued without overwriting or reverting them.

Starting `git status --short` was:

```text
 M AGENTS.md
 M PROTOCOL.md
 M config.yaml
 M schemas/evidence_bundles.schema.json
 M schemas/experiments.schema.json
 M tests/test_anchor_non_regression.py
 M tests/test_factorial_structure.py
 M tests/test_pipeline.py
 M tools/derive_outputs.py
 M tools/execution_contract.py
 M tools/preflight.py
 M tools/validate_run.py
?? diagnostics/cleanroom_pilot_002/
?? diagnostics/cleanroom_pilot_002_adjudication.md
?? diagnostics/cleanroom_pilot_002_gold_corrections.json
?? diagnostics/draft_0_8_3_pilot_002_revision_report.md
?? tests/test_revision_083.py
```

## 2. Pilot-003 archive and verification

- Archive: `diagnostics/cleanroom_pilot_003/`.
- Complete scientific run preserved at `diagnostics/cleanroom_pilot_003/run/` with original run ID `CALIB003`.
- Provenance README includes the exact minimal prompt, source base commit, versions, fixture boundary, no-network statement, harness/model fields, and timestamps.
- Forty-three files are listed in `SHA256SUMS`; every entry verifies.
- Manifest SHA-256: `312568c2b64208599cc438306ebe9749a0cf76f7ef9c3d5c231ab3e7e5e3ad8d`.
- Recursive `diff -qr` against the source run returned no differences before the archive was made read-only. Zero archived files remain owner-writable.
- No source-level clean-room manifest existed; this absence is recorded rather than reinterpreted.
- The accidental `CALIB003` name is preserved and explicitly documented as a diagnostic/historical-calibration namespace collision, not as a historical calibration.

## 3. Complete adjudication

The full six-anchor, 17-dimension adjudication is in `diagnostics/cleanroom_pilot_003_adjudication.md`. Pilot 003 cleanly fixed focal factorial structure, focal-capacity identity, and descriptive direct-comparison auditing. It exposed:

1. method over-permissiveness when an unmeasured endogenous attention possibility vetoed E without an evidential/design anchor;
2. method underspecification when an explicit same-article quantitative-alternative control was not scanned/evaluated; and
3. provenance failure when awareness procedures or another experiment's figures were treated as experiment/sample-specific awareness results.

## 4. Files changed in this pass

Canonical package:

- `AGENTS.md`
- `PROTOCOL.md`
- `config.yaml`
- `schemas/experiments.schema.json`
- `schemas/evidence_bundles.schema.json`
- `schemas/evidence_links.schema.json`
- `tools/execution_contract.py`
- `tools/init_run.py`
- `tools/preflight.py`
- `tools/validate_run.py`

Synthetic/non-registered tests:

- `tests/test_pipeline.py`
- `tests/test_factorial_structure.py`
- `tests/test_revision_083.py`
- `tests/test_revision_084.py`

Diagnostic-only artifacts:

- `diagnostics/cleanroom_pilot_003/`
- `diagnostics/cleanroom_pilot_003_adjudication.md`
- this report

Pre-existing related draft-0.8.3 work was preserved. `README.md`, `METHODS.md`, queries, seeds, F rules, search bounds, and completed historical runs were not modified.

## 5. Version changes

- Protocol: `draft-0.8.3` → `draft-0.8.4`.
- Package: `prefreeze-package-0.8.3` → `prefreeze-package-0.8.4`.
- Schema: `prefreeze-schema-0.8.2` → `prefreeze-schema-0.8.3`, because required fields and link/bundle semantics changed.
- Registration remains `pre-freeze`; no tag, freeze, preregistration, or commit was created.

## 6–10. Refined E rule and mandatory article scan

A contrast-integrity alternative may gate `E-diagnostic` only if it is finite, task/design motivated, capable of changing the same focal Y, prospectively distinguishable, and anchored by one of:

- design-imposed difference;
- directly measured difference;
- reported behavioral evidence;
- explicit manipulation check/control; or
- comparably direct design evidence.

Unmeasured attention, arousal, motivation, stronger-evidence process engagement, or executive-control possibilities can be recorded as limitations but cannot veto E merely because they could covary with awareness and Y. Unequal first-order sensory evidence remains the ordinary E problem; this repair does not turn E-diagnostic into a matching requirement. Conversely, actual instruction, mapping, learning/contingency, policy, feedback, or block-state differences remain gating when design or behavior anchors them.

Every unmatched E row now durably records:

- `alternative_control_scan_status`: `completed-none-found`, `completed-candidate-evaluated`, or `incomplete-source-missing` (`not-required` for E-matched); and
- `alternative_control_scan_reason`.

A fully evaluated row cannot finalize unmatched E with `incomplete-source-missing`. An E-diagnostic support link must be decision-used, required, and explicitly `same_focal_Y_status = yes`. A different-Y control cannot complete the focal E argument. Classification-critical same-article support must enter an explicit bundle/link; author claims alone are not accepted automatically.

At bundle level, every gating contrast-integrity alternative now records `contrast_integrity_anchor_type` and `contrast_integrity_anchor_source_location`. `ruled-out` or `unresolved` is schema-invalid without an anchor; `not-applicable` requires `none`/null.

## 11–15. Strong-A critical-result provenance

Strong A now separates procedure from result. `A-direct` and `A-validated` require:

- `awareness_measure` and `awareness_procedure_type`;
- `awareness_result_status = supportive-result-reported`;
- `awareness_result_procedure_type` matching the actual procedure;
- a nonempty critical result description;
- an exact result source location; and
- for direct A, a result source experiment equal to the focal experiment.

Where evidence comes from another block, experiment, supplement, or external source, `A-validated` additionally requires a complete `awareness-A` bundle with a required, decision-used `critical-result` member. The link must carry exact source identity/location, explicit transfer reason, explicit transfer limitation, and regime comparison. A `procedure-description` member cannot complete strong A. A reported method with an unavailable result produces an unavailable member/incomplete bundle; similar stimuli or “same method” do not propagate another sample's result.

The schema records evidence-link `evidence_content_type` (`critical-result`, `procedure-description`, `transfer-context`, `other`) so the validator can distinguish a behavioral result from Methods prose.

## 16. Diagnostic A provenance by anchor experiment

This table applies the new rule diagnostically; it is not registered-facing answer material.

| Anchor/experiment | Procedure/result provenance in pilot fixture | Diagnostic disposition |
|---|---|---|
| Tsushima E1 | Four-alternative direction threshold; supportive 5% result in main Fig. 2A, method supplement pp. 3–4 | Result-bearing separate-block bundle can support `A-validated` |
| Tsushima E2 | Experiment-specific direction threshold under low luminance; shifted supportive result in main Fig. 2B | Result-bearing bundle can support `A-validated` |
| Tsushima E3 | Direction-threshold procedure said to match E1; no E3/sample-specific threshold result; Fig. S1 is eye movement | Strong A fails absent an explicit transferable-result bundle; `A-transfer-risk` |
| Tsushima E4 | Presence/absence contraction detection; 5% below chance threshold in supplement Fig. S2 | Result-bearing bundle can support `A-validated`; procedure type must not be copied from E1 |
| Tsushima E5 | In-scanner presence/absence procedure described; no scanner-sample critical visibility result reported | Strong A fails absent explicit transfer; `A-transfer-risk` |
| Lin E1 | Post-task cue-location discrimination; analyzed participants' chance result at main pp. 3–4 | Result-bearing `A-validated` support present |
| Lin E2 | Matched-sequence 420-trial cue localization; chance result at main p. 7 | Result-bearing `A-validated` support present |
| Lamy E1 | Trialwise 0–3 visibility result, main pp. 3–4 | Direct result present |
| Lamy E2 | Trialwise rating plus rating-0 localization result, main pp. 5–6/Fig. 4 | Direct result present |
| Lamy E3 | Trialwise yes/no visibility result, main pp. 7–8 | Direct result present |
| Ben-Haim E1 | Human report plus end-test localization, main pp. 2–3 | Direct result present; exact result fields now required |
| Ben-Haim E2 | Monkey result depends on human transfer plus unavailable cited monkey validation | Strong A remains transfer-risk/incomplete |
| Ben-Haim E3 | Human report/localization, main pp. 5–6 | Direct result present |
| Ben-Haim E4 | Monkey result depends on human transfer plus unavailable cited monkey validation | Strong A remains transfer-risk/incomplete |
| Ben-Haim E5 | Human subjective/rule-awareness results, main pp. 7–8 | Direct result present; subgroup/statistical concern remains separate |
| Ben-Haim E6 | Human subjective/rule-awareness results, main pp. 7–8 | Direct result present |
| Ben-Haim E7 | Trialwise visibility and objective-performance result under fixed instruction, main p. 8/Fig. 4D | Direct result present |
| Persaud E1 | Trialwise Guess/Seen responses with reported normal/blind proportions, main pp. 2–6 | Direct result present |
| Keizer E1 | Separate same-strength post-task present/absent evaluation with retained-participant result, main pp. 2–3 | Explicit result-bearing transfer bundle can support `A-validated`; exclusions remain visible |

## 17–21. Diagnostic scientific implications

- **Focal factorial E case:** the unmeasured attention hypothesis lacks an anchor and cannot veto E. The mandatory scan identifies the article's explicit later experiment designed to test the merely quantitative explanation. It addresses the same conservative factorial selection-priority mapping and supplies the expected violating higher-order pattern. With a strict cross-experiment bundle, the diagnostic E implication is `E-diagnostic`, not physical-only. The higher-order mapping—not a marginal p=.055 simple contrast—is the focal evidence.
- **Early task-state-confounded reversal:** remains cautious. Learning/contingency knowledge, instruction, block context, and resulting policy are design-/behavior-grounded and can determine the same action-selection Y. The new anchor requirement preserves this veto. The late fixed-instruction/trialwise comparison remains potentially diagnostic; generic unmeasured attention does not automatically defeat it.
- **Threshold-shift E:** remains viable. Manipulated sensory thresholds and downstream extrema can jointly defeat the specified same-Y scalar account without inventing a separate task-state confound.
- **Keizer:** unaware-capacity evidence remains separately audited with statistical concern; the direct same-Y mask interaction remains a descriptive `no-detectable-difference`; weak null evidence is not equivalence.
- **Persaud:** the awareness-linked metacognitive difference survives; positive blind-field metacognitive capacity remains `unclear`.

## 22. Run-ID namespace repair

`tools/init_run.py` adds `--pre-freeze-diagnostic`. When supplied, it requires `--allow-pre-freeze` and a `PREFREEZE_DIAG_*` ID. `CALIB_*` is rejected for a future diagnostic. Without the flag, historical `CALIB_*` compatibility and ordinary registered naming are unchanged. No historical directory was renamed.

CLI verification:

- `PREFREEZE_DIAG_SYN084` initialized, derived, validated, and resumed successfully in a temporary runs root.
- `CALIB_005` with `--pre-freeze-diagnostic` was rejected before initialization with the reserved-prefix message.

## 23. Registered-facing leakage status

The leakage guard passed. Newly added canonical rules use only generic/synthetic terminology. No named paper, expected experiment, or expected A/E/F/result code was added to protocol, schemas, config, or runtime tools. Named adjudication remains under `diagnostics/`; synthetic tests use generic identifiers.

## 24. New tests

`tests/test_revision_084.py` adds 25 focused tests covering:

- measured policy, design-imposed mapping, and behavioral-contingency anchors;
- unanchored attention and arbitrary post-hoc latent states;
- first-order evidence inequality without a separate task-state veto;
- anchored unresolved policy alternatives;
- completed, candidate-evaluated, missing-source, same-Y, and different-Y within-paper scans;
- same-experiment A results, procedure-only failure, result/source-location failure, procedure/result-type mismatch;
- transferred/supplement result bundles and procedure-only bundle failure;
- no cross-experiment A propagation; and
- diagnostic versus historical/registered run-ID namespaces.

Existing tests were updated only to supply the new generic fields. The full suite also retains schema, bundle, functional identity, capacity identity, descriptive comparison, lifecycle, ID retirement, concurrency, reopening, immutable snapshot, historical compatibility, and route tests.

## 25. Full validation results

- Schema meta-validation: **PASS**, all 12 schemas validate under Draft 2020-12.
- Pre-freeze preflight: **PASS**, with expected unresolved freeze TODOs only.
- Leakage guard: **PASS**.
- Entire repository suite: **PASS**, 144 tests.
- Focused draft-0.8.4 suite: **PASS**, 25 tests.
- Clean lifecycle: **PASS** via the existing full init → structured write → derive → validate → resume/retired-ID test and an additional CLI namespace init/derive/validate/resume check.
- ID retirement/non-reuse, concurrency, bundle, functional/capacity identity, descriptive audit, reopening/state, immutable snapshot, and historical compatibility tests: **PASS** within the suite.
- Python import/compile: **PASS** using a sandbox-writable task-specific bytecode cache. The initial default-cache compile attempt was blocked by macOS cache permissions; rerun with `PYTHONPYCACHEPREFIX=/private/tmp/consciousness-sweep-pycache-084` passed.
- `git diff --check`: **PASS**.

Expected pre-freeze TODOs remain: registration status, publication cutoff, preferred/fallback source freeze fields, and draft/template query markers. Their presence is intentional and did not authorize a run.

## 26. Historical CALIB immutability

Before/after manifests for every historical directory passed with no byte changes:

| Directory | Files | Bytes | Baseline manifest SHA-256 |
|---|---:|---:|---|
| `runs/CALIB_CODEX_001` | 18 | 6,580,530 | `3774cd957b66aeb766d5e4ded4aea42f293d76caa0738dd2cc32f12aca5bf507` |
| `runs/CALIB_CODEX_002` | 16 | 6,769,627 | `3e0ee4bb47237157f7531675fc81b65e4fc702edb61da9939ff803b1d9d4e80a` |
| `runs/CALIB_CODEX_003` | 25 | 15,942,522 | `7dcc39299b56c329e8be5ac304c4ab596937684b03af1f06cbd41dc6016e071b` |
| `runs/CALIB_CODEX_004` | 15 | 1,374,547 | `877b4d7b8acfa5e09081a40831601193ef533d333813f79df0bc9523a0902492` |

Historical runs were neither validated against new schemas nor migrated.

## 27. Remaining scientific/package TODOs

- Run one final fresh-agent, stripped clean-room diagnostic to test whether both repairs are sufficient without visible diagnostics/gold/tests.
- Preserve uncertainty for any experiment/sample whose critical awareness result remains absent; do not repair it by inference.
- Rebuild any classification-critical same-article E support and cross-experiment A support as explicit new-schema bundles in the next diagnostic.
- Keep the unavailable external monkey validation as a source-fixture limitation unless it is explicitly supplied to a future bounded fixture.
- Complete the already-declared freeze fields and separate sufficiency review before registration; do not freeze from this pass.

## 28. Recommendation for one final Codex diagnostic

Run exactly one stripped, no-network, source-bounded Codex diagnostic named `PREFREEZE_DIAG_004` (or the next unused `PREFREEZE_DIAG_*` ID) using draft-0.8.4, the same six main articles and permitted same-article supplement, and no diagnostics/tests/gold/manuscript material. Its primary acceptance checks should be: full-paper E-control scans on every unmatched row; no unanchored latent-state veto; result-bearing A provenance per experiment/sample; explicit transfer bundles; and preservation of all draft-0.8.3 non-regressions. Do not expose the expected paper-specific answers in the fixture prompt.

## Critical final assessment

The package now independently enforces:

- **A.** Functional/factorial structure before decomposition — yes.
- **B.** Unaware capacity cannot change the focal function — yes.
- **C.** Direct aware/unaware comparisons receive descriptive audit even with weak E — yes.
- **D.** Unanchored latent-state speculation cannot defeat E-diagnostic — yes.
- **E.** Classification-critical within-paper controls cannot be ignored — yes.
- **F.** Strong A requires an actual supportive result, not only a procedure — yes.
- **G.** Cross-experiment A requires an explicit result-bearing transfer bundle — yes.
- **H.** Future diagnostic and historical CALIB namespaces cannot be confused — yes, when diagnostics are invoked with the required `--pre-freeze-diagnostic` execution mode; historical/default compatibility is preserved.

No commit was made, no freeze occurred, and no final clean-room diagnostic was started.
