# Manual review guide for the documentation layer

Automated checks establish structure, not semantic equivalence. Human review proceeds in five passes and records any discrepancy before registration.

## Pass 1: brief comprehension

Read `PROTOCOL_BRIEF.md` alone. Ask whether a researcher new to the package can state the scientific question, define X and Y, explain A/E/F, distinguish unaware capacity from awareness effect, distinguish no-detectable difference from equivalence, name the four discovery routes, and understand why CORE and bridge nodes have different citation permissions. Flag jargon used before definition, unsupported certainty, and any sentence that makes the draft sound registered.

## Pass 2: Methods comprehension

Read `METHODS.md` alone. Ask whether a researcher could reproduce what enters the sweep, how papers become physical experiments and comparisons, how evidence dependencies work, what each outcome means, and when the search stops. Confirm that the main text moves from the scientific question and concepts to the algorithm, units, discovery, evaluation, outputs, and execution detail without requiring repository knowledge.

## Pass 3: scientific fidelity

Read `METHODS.md` beside `PROTOCOL.md`. Check that simplification has not changed eligibility; comparison atomization; A, E, or F; result classification; statistics; Meyen; evidence transfer; screening; CORE or bridge eligibility; K=1 depth; function-targeted or blind search; source/window bounds; recursion; or stopping. Confirm that function-targeted search is clearly cross-referenced to historical process-triggered/QDYN terminology and that all fourteen prepared QREV6 families and the separation from historical QCAL4/QCAL5 snapshots are accurately represented.

## Pass 4: execution and reproducibility fidelity

Read `METHODS.md` beside `AGENTS.md`. Check record ownership, continuous and parent-first writes, append-first revision, locked stable IDs, search-result provenance, immutable snapshots, DOI normalization, missing-text handling, verified assets, start/resume behavior, independent-run isolation, checkpoint validation, and every completion condition.

## Pass 5: open decisions and freeze readiness

Inspect `docs/methods_crosswalk.yaml`, `docs/documentation_issues.md`, `config.yaml`, and `queries.md`. Confirm that only genuine authority/configuration decisions appear as documentation issues. Resolve them in the normative package through a separately authorized revision, rerun documentation validation in freeze-time mode, search every registered-facing document for stale TODO/draft language, and confirm that no unresolved crosswalk entry remains before registration.

## Highest-risk concepts

- [ ] X and Y are neither too broad nor destructively atomized.
- [ ] Factorial structure follows operational functional identity, with a focal comparison before components.
- [ ] A distinguishes procedure, reported result, evidential support, objective-test informativeness, and transfer.
- [ ] E-diagnostic states a same-Y competing account, prediction, and violation, and audits only anchored task-state alternatives.
- [ ] Every borrowed premise uses a direct, non-transitive, status-derived evidence bundle.
- [ ] An unaware-capacity claim exactly matches the whole focal functional Y; E is not its gate.
- [ ] Direct descriptive results remain visible without being upgraded through weak E.
- [ ] No-detectable difference is not described as equivalence; region-based equivalence and Bayesian model-relative null support are distinct.
- [ ] Search stopping includes principal-first/blind-last order, mandatory windows, immutable snapshots, and reopened frontiers.
- [ ] A bridge is empirical, focal-experiment exact-two, K=1, discovery-only, and cannot continue a bridge lineage.
- [ ] Independent runs share only static frozen inputs; adjudication preserves original judgments and is not majority voting.

- [ ] Human patient studies, graded awareness without an unaware arm, and exact-content awareness remain eligible.
- [ ] Capacity-only and suggestive/complementary evidence stay supplementary and visible.
- [ ] Comparability applies to both E routes; an endogenous functional transition is not its own confound.
- [ ] Joint/reviewer-derived analysis provenance is explicit; statistical concerns are distinguished from invalidating defects.
- [ ] Meyen remains separate from main eligibility/ranking; qualitative ordering and mixed synthesis give reasons.
- [ ] The default product is a prospect queue for human vetting; tentative primary/support placement does not determine prospect inclusion.
- [ ] Every prospect gives its specific contribution, decisive evidence, limiting alternative and human question before its tentative role.
- [ ] Unknown awareness/function/comparison details are distinguished from a located absence of the target comparison; generic unaware processing alone does not answer the commissioned question.
- [ ] Checkpoint prospect delivery preserves current evidence and explicit human decisions without claiming scientific promotion, final consensus or search completion.
