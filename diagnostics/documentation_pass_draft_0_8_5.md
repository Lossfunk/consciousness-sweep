# Human-readable documentation pass for draft 0.8.5

## 1. Starting commit

- Commit: `6e36f0196f6c78e19bbc72b3d74f357f323d8173`.
- Starting worktree: clean.
- Starting versions: protocol `draft-0.8.5`; package `prefreeze-package-0.8.5`; schema `prefreeze-schema-0.8.4`; registration `pre-freeze`.
- Scope: documentation and structural/semantic coverage audit only. No network access, literature search, scientific run, clean-room diagnostic, CALIB, freeze, registration, or commit was performed.

## 2. Files created or changed

Created:

- `METHODS.md`
- `docs/methods_crosswalk.yaml`
- `docs/documentation_issues.md`
- `docs/manual_methods_review.md`
- `tools/validate_documentation.py`
- `tests/test_documentation_coverage.py`
- this report

Changed:

- `README.md` — replaced the scaffold with a human orientation/mini-methods.
- `tools/leakage_guard.py` — added the derived documentation and its structural validator to the registered-facing leakage allowlist.

No normative authority, configuration, query, seed, schema, historical run, pilot archive, or scientific output was modified.

## 3. README word count and outline

Word count: 1,658.

Outline:

1. project question and pre-freeze warning;
2. scientific records and granularity;
3. discovery and screening;
4. A, E, and F;
5. evidence spanning experiments;
6. independent inference axes and overlapping outputs;
7. independent runs and adjudication;
8. repository and outputs; and
9. setup and lifecycle.

The README identifies the authorities and points to `METHODS.md` as the complete human-readable description. It is intentionally an orientation, not a third protocol.

## 4. METHODS word count and full outline

Word count: 6,590.

The 33 major sections are:

1. Aim and scope
2. Units of representation
3. Overview of the workflow
4. Literature discovery
5. Search-source execution and immutable snapshots
6. Bibliographic identity and logical-paper deduplication
7. Paper screening
8. Full-text acquisition
9. Physical experiment enumeration
10. Pre-atomization functional-structure assessment
11. Defining X and Y
12. Awareness evidence (A)
13. First-order evidence (E)
14. E-diagnostic inference
15. Meaningful downstream use (F)
16. Scientific evidence bundles
17. Route-aware comparison evaluation
18. Unaware-capacity inference
19. Awareness-linked-difference inference
20. Direct descriptive awareness comparisons
21. No-detectable awareness differences
22. Equivalence-supported no difference
23. Statistical audit
24. Meyen diagnostic
25. Classification-critical auxiliary evidence
26. Derived scientific evidence sets
27. Missing information and uncertainty
28. Multi-agent execution
29. Audit trail
30. Start, resume, checkpoints, and completion
31. Cross-run consolidation and adjudication
32. Planned outputs and reporting
33. Pre-freeze versus registered status

Every major section ends with a compact authority line.

## 5. PROTOCOL substantive sections mapped

Mapped: **32/32** level-2/level-3 substantive headings. Some headings have additional reverse rows where their rules support more than one METHODS section.

## 6. AGENTS substantive sections mapped

Mapped: **24/24** level-2/level-3 substantive headings, including the unnumbered Start/Resume and derived-filter subsections.

## 7. Intentionally implementation-only entries

Count: **0**. Execution details that can affect encounter, screening, classification, stopping, provenance, reproducibility, or independence are described in METHODS rather than hidden as implementation-only.

## 8. Unresolved crosswalk entries

Count: **0**. The unresolved scientific/execution freeze decisions are fully documented, so their structural coverage status is `covered`; their substantive unresolved status is recorded in `docs/documentation_issues.md` and METHODS §33.

## 9. METHODS claims lacking authority

Count after reverse and manual audit: **0**. Every major METHODS section has at least one incoming crosswalk row and an authority line. Implementation references are used only to explain enforcement of an authorized PROTOCOL/AGENTS rule. This is a structural and human review finding, not a machine proof of semantic equivalence.

## 10. Documentation issues found

Six genuine pre-freeze issues are recorded:

1. registration remains pre-freeze;
2. publication cutoff is null;
3. preferred source order is empty;
4. deterministic fallback order is empty;
5. query specifications retain draft/to-freeze markers; and
6. the generic LEARN blind-block redesign/omission decision remains open.

The source-role scope distinction—route-specific OpenAlex/Europe PMC execution versus unresolved overall source/fallback policy—is explicitly documented as a clarification needed at freeze review, not silently resolved.

## 11. README/METHODS consistency and semantic side-by-side audit

README did not distort the supplementary QCAL lane into the primary recall engine; it uses the comparison, not paper, as the classification unit; presents A/E/F as design dimensions; keeps unaware capacity independent from awareness effect; distinguishes no-detectable from equivalence; describes bundles as premise-specific direct support; retains support-only experiments; rejects majority-vote adjudication; and states that weak E closes only the strong awareness-effect route.

The manual METHODS/PROTOCOL/AGENTS side-by-side audit explicitly checked all requested high-risk concepts. Coverage passed for physical groups versus comparisons; support-only representation; pre-atomization; factorial functional relations; effect versus function; A procedure versus reported result; objective invisibility; A transfer; E-matched; E-diagnostic; anchored contrast-integrity alternatives; the whole-article control scan; evidence bundles and non-transitivity; exact capacity identity; descriptive direct differences and focal provenance; no-detectable versus equivalence; statistics; Meyen; auxiliary evidence; route-aware short-circuiting; principal-first/blind-last order; citation/process reopening; immutable snapshots; decision reuse; missing texts; multi-agent independence; completion; and adjudication.

The first draft had described citation stopping too generally. The final document now states the exact rule: a complete backward-and-forward wave must yield zero new potentially relevant papers after deduplication and title/abstract screening. The same correction pass made citation-node eligibility, process-lane promotion, source-failure specification, Meyen caveats, and sentinel rules explicit.

## 12. Validator implementation

`tools/validate_documentation.py` parses all level-2/level-3 authority headings, explicit METHODS anchors, and the YAML crosswalk. It verifies required fields/statuses, complete authority-heading coverage, existing and title-consistent METHODS targets, incoming reverse coverage for every METHODS section, unique row identities and anchors, and resolvable numeric authority references. It reports unresolved and intentionally implementation-only rows and offers `--require-no-unresolved` for freeze-time enforcement.

`tests/test_documentation_coverage.py` checks the live package and regression-tests duplicate-anchor and orphan-target detection. The validator explicitly states that it proves structural coverage only, not semantic equivalence.

## 13. Validation results

- Documentation crosswalk validator: **PASS** — PROTOCOL 32/32, AGENTS 24/24, 33 METHODS targets, 63 rows, 0 implementation-only, 0 unresolved.
- Documentation-specific unit tests: **PASS**, 3 tests (also included in the full suite).
- Draft 2020-12 schema meta-validation: **PASS**, 13 schemas.
- Pre-freeze preflight: **PASS**, with the five expected registered-run TODO messages (status, cutoff, source preference, fallback order, query markers).
- Registered-facing leakage guard: **PASS** after adding documentation files to its allowlist.
- Entire unit suite: **PASS**, 169 tests.
- Python import/compile: **PASS**, with bytecode cache directed to `/private/tmp`.
- `git diff --check`: **PASS**.
- Normative authorities, configuration, queries, seeds, requirements, and schemas unchanged from `HEAD`: **PASS** (`git diff --exit-code` over those paths).
- Freeze-time crosswalk mode (`--require-no-unresolved`): **PASS** for the documentation crosswalk; this does not resolve the separately documented package freeze decisions.

## 14. Readiness for human manual review

**Ready for human manual review.** The documentation layer is structurally complete and the requested semantic audit has been performed. It is not ready for registration: the genuine pre-freeze decisions in `docs/documentation_issues.md` remain for human resolution. No authority was changed to make the documentation easier, and no scientific execution was started.
