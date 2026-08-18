# Tsushima 2006 pre-freeze diagnostics

**Status:** diagnostic only, updated under draft-0.6. This is not a scientific run and does not alter any CALIB001/002/003 run. The earlier draft-0.4 Experiment 5 A diagnostic is superseded by the explicit same-participant report-results check below. The original F/A sections are preserved; the final section adds the requested post-CALIB003 Meyen-role and derivation diagnostic.

## Revised F/Y-granularity diagnostic

The most conservative behavioral Y supported in all five comparisons is:

> **Y label:** regulation/control of task-irrelevant distractor interference<br>
> **Y description:** regulation of how task-irrelevant coherent motion influences performance on the central RSVP task.

This functional description is supported by the behavioral dependent variable: RSVP performance changes with the coherence of motion that participants are instructed to ignore. It does not assert that the experiment uniquely identifies active spatial suppression, LPFC inhibitory control, attentional filtering, altered capture, resource competition, or another implementation. Those are finer mechanistic interpretations.

| Experiment | Behavioral functional constraint | Authors' finer interpretation | Neural/artifact support | Diagnostic F |
|---|---|---|---|---|
| 1 | RSVP d-prime was lower with 5% task-irrelevant motion than with 0% or 20%, showing that the distractor's influence on the central task was regulated differently across the critical conditions. | Failure of effective inhibitory control/filtering for threshold-region motion. | No neural measure; the behavioral effect alone identifies the conservative Y. | `F-meaningful`; Y is clear at the function level, mechanism ambiguous. |
| 2 | Lowering dot contrast shifted both the perceptual threshold and the RSVP interference dip to 30%, again constraining regulation of distractor influence. | Threshold-linked failure of inhibitory control/filtering. | The threshold-shift manipulation supports the functional pattern but does not isolate an implementation. | `F-meaningful`; Y clear, mechanism ambiguous. |
| 3 | The same RSVP interference pattern was reported while eye position was monitored. | The effect is not explained by systematic eye movements; inhibitory-control account retained. | Eye tracking is artifact-control evidence, not a separate qualifying Y or a neural mechanism. | `F-meaningful`; F concerns the measured function even though outcome/statistical reporting remains limited. |
| 4 | Contracting motion reproduced the threshold-region RSVP disruption, showing regulation of distractor interference beyond translating-motion eye-movement accounts. | Failure of inhibitory control/filtering generalized to contraction. | Stimulus-form and eye-movement arguments narrow artifacts, not the precise mechanism. | `F-meaningful`; Y clear, mechanism ambiguous. |
| 5 | In the task-irrelevant scans, RSVP performance showed the same threshold-region dip, so the behavioral Y remains regulation/control of distractor interference. | LPFC fails to inhibit MT+ responses to threshold-region motion. | Lower LPFC BOLD, higher MT+ BOLD, complementary behavioral variation, and their across-coherence correlation are correlational mechanistic support. A generic regional BOLD difference is not recoded as Y. | `F-meaningful`; behavioral Y clear, neural/cognitive mechanism ambiguous. |

Thus all five CALIB002 comparisons would change diagnostically from `F-ambiguous` to `F-meaningful` under draft-0.5. This conclusion follows from the behavioral dependent measure, not from the article's phrase “inhibitory control.” CALIB002 itself remains unchanged.

Sources: article pp. 1786-1788 (PDF pp. 2-4), especially Figs. 2-4; supplement Experiments 1-5 and Figs. S1-S2 (PDF pp. 2-9).

## Experiment 5 A report-results check

The supplement confirms that the same six fMRI participants completed task-relevant and task-irrelevant conditions on different, order-counterbalanced days. In the task-relevant condition, trials contained 0%, 5%, 10%, or 20% contracting motion. Participants pressed one of two buttons to report whether they perceived any coherent motion, and the responses were recorded so that mean performance could be calculated (supplement PDF pp. 7-8).

Neither the article nor the supplement reports those behavioral visibility results: there is no 5% detection proportion, participant-level result, confidence interval, test against the 0%/chance baseline, or plotted psychometric function for the Experiment 5 sample. Article Fig. 3 reports task-relevant BOLD responses, not task-relevant detection accuracy. The existence of a sensitive task therefore does not establish what the participants actually reported at 5%.

**Diagnostic A result: `A-transfer-risk` remains warranted.** The same-participant task is highly relevant, but its unreported results cannot establish the critical 5% awareness status. Transfer from Experiment 4 uses different participants and occurs outside the scanner; it remains materially uncertain. This supersedes the earlier post-CALIB001 diagnostic suggestion of `A-validated` and agrees with CALIB002 without rewriting that run.

## Auxiliary-source scope

The existing Watanabe et al. (2001) auxiliary-source records remain useful for the general informativeness of legacy motion-visibility tests. They do not supply the missing Experiment 5 same-participant 5% report results and were not changed in this correction pass.

## Post-CALIB003 Meyen-role and constraint-ready diagnostic

This section diagnoses the five CALIB003 Tsushima rows without rewriting them. CALIB003 recorded all five as `A-validated`, `E-diagnostic`, `F-meaningful`, awareness-linked differences with the critical difference tested, and `Meyen-failed`; Experiments 1, 2, and 4 had adequate statistics, while Experiments 3 and 5 were statistically unclear.

The Meyen result remains **`Meyen-failed`**: the paper combines threshold-region direct performance with an indirect RSVP interference effect but does not demonstrate that the indirect measure has greater sensitivity to X than the direct measure on a comparable scale. Under draft-0.6, however, its role is **`supplementary`**, not `inference-critical`, for each CALIB003 row. The critical inference does not rest only on direct-chance plus indirect-effect residual-sensitivity logic. It has the separately coded A evidence and the full `E-diagnostic` pattern:

1. the threshold procedure supplies evidence locating the near-threshold regime;
2. interference is nonmonotonic across motion coherence, rather than increasing with stronger first-order motion evidence;
3. the interference disappears at stronger, more visible coherence; and
4. when reduced contrast moves the perceptual threshold from about 5% to about 30% coherence, the interference dip moves with that threshold.

The diagnostic force comes from all four features together, especially the stronger-evidence disappearance and threshold-shift movement; threshold-level chance evidence or nonmonotonicity alone would not support `E-diagnostic`. Meyen failure therefore remains visible as a supplementary caveat but does not duplicate or veto that independent A + E route.

Applying the revised generic derivation mechanically, **three** CALIB003 comparisons would become constraint-ready: `P004229_E01_C01`, `P004229_E02_C01`, and `P004229_E04_C01`. They satisfy design eligibility, awareness-linked difference, adequate statistics, and direct difference testing, and supplementary Meyen failure is non-blocking. `P004229_E03_C01` and `P004229_E05_C01` remain outside constraint-ready output because their statistics are unclear, independently of Meyen.

This result is not seed-specific. Any comparison with the same field values receives the same derivation. The earlier Experiment 5 A-transfer diagnostic above remains a pre-freeze disagreement to adjudicate before freeze; it does not alter the mechanical conclusion about which three CALIB003 rows pass under their recorded current-state values.
