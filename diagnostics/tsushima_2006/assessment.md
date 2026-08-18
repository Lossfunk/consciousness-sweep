# Tsushima 2006 post-calibration awareness diagnostic

**Status:** diagnostic only under draft-0.4. This is not a run, does not alter `runs/CALIB_CODEX_001/`, and does not screen or add Watanabe et al. (2001) to the X→Y candidate pipeline.

## Classification-critical dependency followed

Tsushima et al. state that their 5% motion condition produced chance-level performance and attach citation 2 to the conclusion that it was subthreshold (main article p. 1787). Citation 2 is Watanabe, Náñez, and Sasaki (2001), *Perceptual learning without perception*, DOI `10.1038/35101601`. No other external citation is attached to that specific 5%-subthreshold inference; citation 16 points to Tsushima's own supporting materials.

The publisher PDF endpoint returned an access page, but a complete author-laboratory copy was obtained from Boston University and stored at `diagnostics/tsushima_2006/fulltexts/Watanabe_2001.pdf` (SHA-256 `3bafc515a7fa5187e06da330862a0cc10bb0a2bde3355e7cd399eb20470d8ea6`). The retrieval and comparison-level transfer assessments are in `auxiliary_sources.csv`.

## What was tested

Tsushima et al. (2006) performed no subjective awareness report. For Experiments 1–3, the same participants completed a post-main-task four-alternative motion-direction threshold procedure: seven coherence levels, 36 trials per level (252 trials), 915-ms displays, no feedback. Experiment 2 repeated the procedure under the deliberately reduced luminance. Experiment 4 used a post-task present/absent contraction-detection threshold including the exact 5% condition and random-motion trials. The paper reports the critical coherence as below the group chance-level threshold. Experiment 5 reports no new threshold test; it uses the Experiment 4 contracting stimulus in an fMRI sample.

Watanabe et al. (2001) supplied converging objective tests at 5% coherence. Across five experiments it used eight-direction identification (12.5% chance), coherent-motion detection against 0% random motion, fine same/different direction discrimination (50% chance), and direction/detection judgments during exposure. The main experiments used eight participants each for Experiments 1–3 and six each for Experiments 4–5; the preliminary threshold study used six, followed by eight new observers tested for 20 trials at each of 4–8% coherence. Test stages included 20 trials per direction. At 5%, performance was reported at or near the relevant baseline before, during, and after exposure; 10% conditions produced the expected above-baseline sensitivity. The design therefore provides substantially more than one small nonsignificant test, despite using legacy null-hypothesis statistics rather than equivalence tests or Bayes factors.

## Informativeness and transfer

The objective evidence is sufficiently informative for a legacy invisibility inference because the tasks directly query the relevant motion, have explicit chance/no-signal baselines, include many repeated observations, converge across identification/detection/discrimination tasks and time points, and show sensitivity at higher coherence. Tsushima's own post-task measurements are conservative with respect to divided attention: removing the central RSVP task should make motion more, not less, available.

Transfer from Watanabe (2001) is strong for Tsushima Experiments 1 and 3: both use task-irrelevant peripheral translating DRD, 5% coherence, 1.27 dots/deg², approximately 14.2°/s, no masking, a central RSVP task, and normal-vision adults. Watanabe used 500-ms displays and different RSVP timing, whereas Tsushima used 915-ms displays. Transfer is weaker for Experiment 2 (lower luminance), Experiments 4–5 (contracting rather than translating motion), and Experiment 5's scanner context. Those limitations do not defeat Experiments 1–4 because Tsushima directly tested their own regimes. For Experiment 5, Tsushima Experiment 4 is the closer separate validation: the contracting stimulus and task structure match, but the participant sample and scanner context differ.

## Revised draft-0.4 A assessment

All five comparisons have `awareness_evidence_type = objective-invisibility`.

- Experiments 1–4: `A-direct`. Each relevant experiment included a same-participant objective threshold/detection procedure that directly tested the motion regime, used a meaningful baseline, and was sufficiently informative under the legacy-evidence rule. Watanabe (2001) corroborates the method but is not needed to convert these cases to `A-validated`.
- Experiment 5: `A-validated`. It lacks its own threshold procedure, but the same contracting stimulus was directly validated in Tsushima Experiment 4. Stimulus parameters, lack of masking, timing/task structure, attention allocation, and normal-vision population are sufficiently close; the separate sample and fMRI setting are recorded transfer limitations. Watanabe (2001) is corroborative but would carry transfer risk if used alone.

This changes the post-calibration A assessment, not the frozen historical records. E, F, outcome, statistics, and Meyen codes were not revisited.
