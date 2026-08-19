# Clean-room pilot 004 adjudication

## Scope and standard

This diagnostic adjudication compares the archived `PREFREEZE_DIAG_004` records against the current hand-audited six-anchor standard and the accepted generic lessons from pilots 001–003. It does not change the archived run, create a scientific run, or place named answers in registered-facing inputs.

Categories: **A** clean pass; **B** source-fixture limitation; **C** gold-standard correction; **D** ordinary model variance; **E** generic method underspecification; **F** method over-permissiveness; **G** provenance/execution failure.

## Run-level findings

- **Comparison discovery — A/D.** The run enumerated six papers, 20 physical experiment groups, and 19 comparison rows. It found the principal comparison structures for all six anchors. Some comparison boundaries and labels vary from the hand audit but are ordinary model variance except where the functional-Y correction below applies.
- **Physical experiment enumeration — A.** Twenty experiment-level audit events cover the physical groups, including Ben-Haim Experiment 5 (`P000001_E05`) and Lin/Murray Experiment 3 (`P000004_E03`).
- **Support-only disposition — G/E.** Those two groups were correctly treated as support-only and were not given dummy comparison rows. Canonical validation nevertheless produced exactly two errors because experiment decision targets were resolved only through `experiments_master.csv`. This is a real execution-contract representation bug, not a scientific error.
- **X/Y and functional identity — A/C/F.** Persaud separates the behavioral metacognitive comparison from a nonfunctional neural comparison; Lamy preserves the repeated-cue functional relation; Ben-Haim and Lin/Murray generally use function-level labels. Tsushima's five rows instead use “modulation of RSVP digit identification by task-irrelevant motion,” an effect-level formulation that cannot by itself establish the hand-audited regulation/control capacity. This is a gold correction exposing method over-permissiveness.
- **A result provenance — A/B/C/E.** Most rows name a result, procedure, and location. Tsushima Experiment 3 nevertheless records `supportive-result-reported` while its own description says exact values were not reported. Experiment 5 similarly treats a described task/regime as the focal critical result. These internally contradictory strong-A states confirm that result availability and result support were underspecified as one field. Source limitations may keep A unresolved, but they do not justify encoding an unreported result as reported.
- **E — A/D.** The run uses explicit premise bundles and generally respects matched, diagnostic, physical-only, and uncontrolled distinctions. Cross-experiment evidence can legitimately support E, including threshold-shift or control logic, but it must remain evidence-bundle provenance rather than a focal direct-difference record.
- **Evidence bundles — A.** The run contains 23 bundles and 24 direct links; required support is explicit and no incomplete/conflicted bundle is used for a final premise. The bundle architecture itself does not require revision.
- **Difference provenance — C/E.** All 18 rows with `difference_tested=yes` have result prose but no structured source-experiment/location/test fields. Several diagnostic arguments borrow a later or separate experiment while the focal row still asserts a direct difference. The records cannot mechanically distinguish legitimate cross-experiment E support from a focal aware/unaware statistic. This confirms a generic provenance gap; focal direct classifications must identify a statistic in the same physical experiment.
- **Capacity identity — A/C/F.** Exact textual identity between `unaware_capacity_claim` and `Y_label` is present, but Tsushima demonstrates that exact identity can be evaded by making both fields the same broad effect label. The unaware interference pattern does not establish the hand-audited regulation/control capacity. A semantic functional-Y guardrail is therefore required in addition to string identity.
- **Descriptive null/equivalence — A.** Keizer's direct null remains descriptive `no-detectable-difference`; no row is upgraded to equivalence without positive null evidence.
- **Statistics — A/D.** Route-specific statistics and reasons are usually recorded. Remaining disagreements concern scientific interpretation or source sufficiency, not a missing generic statistical category.
- **Constraint-ready results — C/F.** The pilot derived 12 constraint-ready rows, including Tsushima rows inflated by effect-only Y/capacity coding and rows whose focal difference provenance is not auditable. Those rows are diagnostic corrections, not targets to preserve. Persaud's awareness-linked result and the previously accepted factorial/E/null structures remain supported by the generic rules.

## Anchor-by-anchor disposition

- **Ben-Haim — A/D.** Physical groups and the support-only fifth experiment were found. The early reversal/contrast-integrity structure is represented; comparison-specific A/E strength varies ordinarily. The support-only validator failure is G, not a reason to invent a comparison.
- **Keizer — A.** The direct comparison is audited despite weak E, with a descriptive null and no equivalence upgrade. This preserves the accepted hand-audited lesson.
- **Lamy — A.** The downstream spatial-selection relation is retained and the within-experiment comparisons are explicit. No new generic correction is driven by this anchor.
- **Lin/Murray — A/G.** Operational identity is assessed, and Experiment 3 is correctly support-only. Its decision-log failure is the same first-class-experiment bug.
- **Persaud — A.** The metacognitive Y is separated from regional cortical activation; the latter remains `F-not-meaningful`. Capacity stays unclear while the direct awareness-linked difference remains available.
- **Tsushima — B/C/E/F.** The threshold/nonmonotonic evidence may support E through explicit same-Y bundles, but Experiments 3 and 5 do not report the focal critical awareness results claimed by the old combined field. The broad performance-modulation Y is effect-descriptive and cannot establish regulation capacity. Direct awareness-effect claims also require same-experiment statistic provenance rather than imported threshold/control logic.

## Confirmed generic lessons

All four proposed lessons are real in the archived records:

1. Physical experiments need first-class rows so valid support-only audit targets resolve without dummy comparisons (**G/E**).
2. Strong-A result reporting must be separate from whether the result supports A (**C/E/F**, with some **B** source limitations).
3. Cross-experiment E support must not fabricate a focal direct awareness-difference statistic (**C/E**).
4. A Y label must name a defensible downstream function or coherent mapping, not merely restate an observed effect (**C/F**).

These are execution-invariant and representation corrections. They do not reopen the settled search, E-diagnostic, evidence-bundle, null/equivalence, Meyen, or workflow rules.
