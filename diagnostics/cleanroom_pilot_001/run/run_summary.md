# Pre-freeze diagnostic PREFREEZE_DIAG_20260819

## Scope and status

This is a bounded, source-only diagnostic under package `draft-0.8.1`, not a registered literature sweep. Exactly six preexisting PDFs from `sources/` were ingested; no literature search, citation expansion, supplement retrieval, or outside-paper lookup was performed. The diagnostic is paused after successful canonical derivation and validation. It is not marked `complete`, because the package is pre-freeze and the registered discovery/stopping conditions remain intentionally open.

The master contains 24 fully evaluated paper × experiment × X→Y comparisons plus two explicitly excluded support-only bookkeeping rows. All source PDFs and page-delimited text extractions have verified hashes in `fulltext_assets.csv`. One unavailable auxiliary dependency (Andersen et al. 2014, invoked for monkey awareness) is recorded without adding it to the candidate pool.

## Deterministic output counts

- Awareness-effect design eligible: 5
- Constraint-ready union: 8
- Constraint-ready awareness-linked differences: 4
- Constraint-ready unaware capacities: 5
- Descriptive no-detectable awareness differences: 4
- Equivalence-supported no difference: 0
- Unresolved comparisons: 12

The union count is lower than the sum of route counts because `P000004_E01_C01` qualifies through both a supported unaware capacity and an awareness-linked difference.

## Comparison-level findings

### P000001 — Ben-Haim et al. (2021)

- `P000001_E01_C01` (human spatial cueing): `A-direct / E-diagnostic / F-meaningful`. Self-report plus chance cue localization support unawareness. Masked cues slowed opposite-side target localization while visible cues facilitated it, a same-Y sign reversal inconsistent with simple monotonic evidence strength. Adaptive opposite-location rule use is `not-supported` under unawareness; the directly tested awareness effect is `difference-supported`.
- `P000001_E02_C01` (monkey spatial cueing): `A-transfer-risk / E-diagnostic / F-meaningful`. The same sign reversal is reported, but the monkeys provide no focal subjective report; the cited monkey validation is unavailable and human-to-monkey transfer cannot be audited. Both inferential routes therefore fail the strong-A gate despite the reported behavioral difference.
- `P000001_E03_C01` (human forced guessing): `A-direct / E-diagnostic / F-meaningful`. Masked-cue choices show below-chance influence while visible-cue choices are above chance. The named adaptive opposite-location rule is `not-supported` under unawareness. The awareness effect remains `unresolved` because the article reports separate condition results rather than a direct focal between-condition test.
- `P000001_E04_C01` (monkey forced guessing): `A-transfer-risk / E-diagnostic / F-meaningful`. Monkeys show 43.5% masked-cue accuracy and strong visible performance, but monkey awareness remains an unresolved auxiliary-transfer dependency; the direct awareness difference is not reported as a focal test.
- `P000001_E06_C01` (informed masked cues): `A-direct / E-physical-only / F-meaningful`. Pre-information unseen-cue performance is below chance, so adaptive opposite-location rule use is `not-supported`. Awareness and explicit task instruction change together, leaving the awareness effect `unresolved`.
- `P000001_E07_C01` (trialwise awareness): `A-direct / E-diagnostic / F-meaningful`. Rating-0 trials are below chance and rating-2/3 trials above chance for the same instructed rule (`χ²(3)=24.8, p<.0001`). This supports a qualitative awareness-linked difference but not adaptive rule use under unawareness.
- Experiment 5 is support-only: it tests whether sparse visible trials suffice for learning, but does not independently answer a qualifying aware/unaware X→Y question.

### P000002 — Keizer et al. (2015)

- `P000002_E01_C01`: `A-validated / E-physical-only / F-meaningful`. Individual staircasing plus post-task presence discrimination supports masked S1 unawareness. A 5.8-ms partial-repetition binding cost indicates short-term orientation-location binding/retrieval under unawareness, but the one-tailed effect is weak and the more inclusive robustness analysis loses the planned effects. The masking × binding interaction is nonsignificant, so the awareness result is only `no-detectable-difference`, never equivalence. Overall and capacity statistics remain `concern`.

### P000003 — Lamy et al. (2015)

- `P000003_E01_C01`, `P000003_E02_C01`, `P000003_E03_C01` (attentional capture): all are `A-direct / E-physical-only / F-meaningful`; Experiment 2 adds objective localization validation. Unseen attention-matching/same-color cues produce significant 36-, 40-, and 104-ms spatial capture, respectively, so the exact capture capacity is `supported`. Direct awareness modulations are not detected, but no equivalence evidence is supplied.
- `P000003_E01_C02` and `P000003_E02_C02` (feature-change cost): `A-direct / E-physical-only / F-meaningful`. The irrelevant-color same-location cost occurs for aware cues (33 and 35 ms) but not as a positive updating cost for unaware cues (1 and 2 ms); direct awareness modulations are significant (`p<.04`). Unaware updating capacity remains `unclear` because near-zero effects are not positive evidence.
- `P000003_E03_C02`: the conservative different-color feature-change cost is `F-meaningful`, but the focal visible/unseen modulation is `p=.055`; both the awareness effect and unaware updating capacity remain `unresolved/unclear`.
- The cited object-file literature is treated as mechanistic context only. The conservative Y is the observed location-specific feature-change cost, so no unavailable external premise was used to pass F.

### P000004 — Lin & Murray (2015)

- `P000004_E01_C01` (immediate orienting): `A-validated / E-diagnostic / F-meaningful`. Experiment 2 supplies a direct matched-sequence awareness-validation bundle. In fixed blocks, invisible cues yield 15.7-ms cuing while visible cues yield 2.1 ms; in random blocks both yield about 15 ms. The direct fixed-block interaction is `F(1,42)=14.00, p=.001`. Unseen fixed-cue orienting is `supported`, and awareness produces a `difference-supported` qualitative regime change.
- `P000004_E01_C02` (attentional aftereffect): `A-validated / E-uncontrolled / F-meaningful`. A visible repeated cue produces a -12.2-ms later bias against its old location; the invisible aftereffect is 1.6 ms. The visibility × old/new interaction is significant, but unequal cue evidence remains a viable scalar account. Persistent inhibition under unawareness is `unclear`.
- `P000004_E02_C01` (immediate orienting replication): `A-validated / E-uncontrolled / F-meaningful`. The sequence-matched objective test supports invisibility; fixed and random invisible cues yield 15.6- and 20.5-ms cuing effects. Unaware exogenous orienting is `supported`; no aware main-task condition is tested.
- `P000004_E02_C02` (aftereffect replication): the -2.1-ms no-cue old/new result is nonsignificant without positive null evidence, so persistent inhibition under unawareness is `unclear` and awareness modulation is `not-tested`.
- Experiment 3 is a visible-only SOA control and is excluded as support-only.

### P000005 — Persaud et al. (2011)

- `P000005_E01_C01` (metacognitive monitoring): `A-direct / E-matched / F-meaningful`. Hemifield-specific titration yields matched first-order accuracy (76% vs 79%, `p=.34`) while Guess/Seen reports differ sharply. Wagering-accuracy correlation is higher in the normal field (`r=.52`) than blind field (`r=.30`; Fisher difference `p<.001`), supporting an awareness-linked metacognitive difference. Positive blind-field metacognitive capacity is `unclear` because `r=.30` is not itself tested against zero. Generalization remains a single-case concern.
- `P000005_E01_C02` (frontoparietal BOLD): `A-direct / E-matched / F-not-meaningful`. Corrected frontoparietal clusters are retained as mechanistic support, but a generic neural response does not identify a qualifying downstream cognitive use. Both scientific routes are therefore excluded.

### P000006 — Tsushima et al. (2006)

- `P000006_E01_C01` and `P000006_E02_C01`: `A-transfer-risk / E-diagnostic / F-meaningful`. RSVP disruption peaks near the reported chance-level motion threshold, recovers at suprathreshold coherence, and both the threshold and dip shift when dot luminance is reduced. This joint same-Y pattern violates monotonic evidence strength. However, validation sensitivity and transfer details are confined to an unavailable supplement, so strong A is not established and no constraint-ready route opens. The unaware condition shows failed distractor regulation, not positive unconscious control.
- `P000006_E03_C01` and `P000006_E04_C01`: eye-movement and contracting-motion controls reproduce the qualitative performance dip, but experiment-specific statistics and awareness-validation detail are unavailable. They remain `A-transfer-risk / E-uncontrolled / F-meaningful` with unresolved awareness effects and `not-supported` distractor regulation.
- `P000006_E05_C01`: fMRI links the near-threshold dip to high MT+ and low LPFC activity, but the behavioral/A details remain supplement-dependent. The conservative behavioral Y is meaningful; the neural measures are mechanistic support rather than separate qualifying functions. A, E, and the awareness effect remain insufficient for a strong route.

## Uncertainty and stopping evidence

- No result is coded `equivalence-supported`; nonsignificant awareness interactions are explicitly weak null evidence.
- The Ben-Haim monkey A classifications remain `A-transfer-risk` because the cited monkey awareness paper was not supplied.
- Tsushima awareness validation and several control-experiment statistics remain unresolved because the supporting material was not supplied.
- No missing target PDFs remain within the bounded input set. Missing external/supplementary dependencies are recorded as unavailable or incomplete bundles rather than silently accepted.
- Search, citation, blind-lane, and process-search frontiers remain open by design. Their open status is evidence that this diagnostic is not a sweep and must not be interpreted as complete literature coverage.

## Validation

Canonical tools were run after all append-first repairs:

- `tools/derive_outputs.py --run-id PREFREEZE_DIAG_20260819`: pass
- `tools/validate_run.py --run-id PREFREEZE_DIAG_20260819`: pass for schemas, CSV encoding, JSONL, identifiers, cross-file references, file hashes, evidence-bundle status, and durable counters
