# Calibration provenance removed from registered-facing draft-0.8.1

**Status:** historical calibration material only — not a registered input  
**Pre-change commit:** `3ddcc6e643bd9deee60917ca39a1c16da2ebc1bf`  
**Source package:** draft-0.8 / `prefreeze-package-0.8` / `prefreeze-schema-0.8`

This file preserves paper-specific calibration instantiations removed while preparing draft-0.8.1. The generic scientific rules learned from these cases remain in `PROTOCOL.md`; this file must not be supplied to independent registered agents or a clean-room sufficiency test.

## Protocol example removed

The following draft-0.8 paragraph was removed from registered-facing normative prose because it names a frozen empirical seed beside its expected `E-diagnostic` interpretation:

> Tsushima, Sasaki, and Watanabe (2006) motivate `E-diagnostic`: interference is non-monotonic with motion coherence, is maximal around the awareness threshold, and the interference dip shifts when the perceptual threshold is experimentally shifted. The diagnostic value comes from the whole pattern, not from non-monotonicity alone. Charles et al. (2013) motivate the distinction between identical physical stimuli and identical internal evidence.

The threshold-linked extremum, manipulated-threshold shift, same-Y requirement, multi-experiment bundle, crossover/sign-reversal, and factorial-functional rules remain in generic form in `PROTOCOL.md`.

## Original empirical-seed rationales

| Seed | Original draft-0.8 `seed_reason` |
|---|---|
| ESEED001 | Central attentional-control example and citation-graph entry point; included for discovery rather than presumed eligibility |
| ESEED002 | Central attentional-effects/control study and citation-graph entry point |
| ESEED003 | Central attentional-capture/conflict-handling study and citation-graph entry point |
| ESEED004 | Central awareness-and-strategic-cue-use study and citation-graph entry point |
| ESEED005 | Central awareness-and-metacognitive-calibration example and citation-graph entry point |
| ESEED006 | Central feature-location-binding/preserved-capacity example and citation-graph entry point |

These rationales were replaced with neutral procedural provenance because several disclose a hand-adjudicated functional interpretation or expected result. Titles, authors, years, DOIs, URLs, and guaranteed empirical-seed entry remain unchanged.

## Historical Tsushima QDYN instantiation

Draft-0.8 embedded this calibration-only lexical set in `queries.md` and `tools/query_instruments.py`:

| Term | Provenance category | Historical source/derivation |
|---|---|---|
| `regulation of task-irrelevant distractor interference` | canonical-y | Conservative Y assigned from the behavioral dependent measure. |
| `task-irrelevant distractor-interference regulation` | morphology-grammar | Derived from the historical canonical Y. |
| `regulating task-irrelevant distractor interference` | morphology-grammar | Derived from the historical canonical Y. |
| `inhibitory control` | source-paper-terminology | Tsushima et al. (2006), title and pp. 1786–1788. |
| `attention filtering` | source-paper-terminology | Tsushima et al. (2006), pp. 1786–1788. |
| `distractor interference control` | frozen-immediate-parent | Historical parent `Y-PARENT-DISTRACTOR-INTERFERENCE-CONTROL`. |

It was used in CALIB004 to exercise one bounded OpenAlex and one bounded Europe PMC process-query window, each capped at 50 records. It was removed from registered-facing query prose and runtime code because it supplies a particular seed's expected canonical Y and process-search answer. The generic runtime now consumes a comparison-derived canonical Y, approved grammatical variants, explicitly source-derived same-function terms with pointers, and at most one frozen immediate-parent label.

## Historical sentinel bookkeeping

The CALIB003/CALIB004 held-out query sentinels were Tsushima et al. (2006), Lin and Murray (2015), Lamy et al. (2015), Ben-Haim et al. (2021), Persaud et al. (2011), and Keizer et al. (2015). CALIB004 reused the unchanged CALIB003 six-sentinel set to assess blind-query recovery without embedding titles, authors, or identifiers in the search strings. Sentinel recovery was a calibration diagnostic, never a scientific inclusion label or registered stopping rule.

The named list, the `calibration_004.blind_sentinel_set` bookkeeping field, and registered-facing recovery instructions were removed. The same six works remain unchanged as frozen empirical seeds; seed membership, not sentinel recovery, guarantees candidate-lot entry.

## Exclusion rationale

Each item above is retained here because it documents how the method was calibrated. It is excluded from registered-facing inputs because it tells an executing agent how a particular frozen seed is expected to instantiate a focal function, diagnostic structure, outcome, or query vocabulary. No generic scientific rule or execution bound was removed for that reason.
