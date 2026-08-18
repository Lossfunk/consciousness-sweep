# Draft Query Specification

**Status of every exact string below: DRAFT — TO FREEZE BEFORE REGISTERED RUN**

These query families are recall checks and discovery tools, not eligibility definitions. Interpret eligibility only under `PROTOCOL.md`. Before registration, adapt and freeze each exact string for every named search source, recording source-specific syntax, fields, limits, date handling, and fallback behavior. Do not execute these drafts during repository construction.

## Q001 — Generic awareness × downstream use

**Purpose:** Broad coverage of awareness of X combined with a distinct downstream use Y.

```text
(awareness OR aware OR unaware OR conscious OR unconscious OR visibility OR seen OR unseen)
AND
("cognitive function" OR "cognitive control" OR use OR utilization OR evaluation OR monitoring OR updating OR binding OR maintenance OR memory OR "action selection" OR "rule guided" OR adaptation)
AND
(experiment OR task OR performance)
```

## Q002 — Performance-matched awareness

**Purpose:** Find designs that match or diagnose first-order evidence while contrasting awareness.

```text
(awareness OR conscious OR unconscious OR visibility OR seen OR unseen)
AND
("performance matched" OR "matched performance" OR "objective performance" OR discrimination OR d-prime OR d' OR titrat* OR threshold* OR "signal strength" OR evidence)
AND
(control OR evaluation OR monitoring OR updating OR binding OR memory OR decision OR action)
```

## Q003 — Blindsight and metacognition

**Purpose:** Connect blindsight, subjective awareness, and downstream metacognitive use.

```text
(blindsight OR "cortical blindness" OR "visual field defect")
AND
(awareness OR conscious OR confidence OR wagering OR metacognition OR calibration)
AND
(discrimination OR decision OR monitoring OR control OR strategy OR use)
```

## Q004 — Attention and control

**Purpose:** Cover awareness-dependent or awareness-independent control, selection, conflict, capture, and suppression.

```text
(awareness OR conscious OR unconscious OR visible OR invisible OR seen OR unseen)
AND
(attention OR "attentional capture" OR control OR inhibition OR suppression OR conflict OR distractor OR cue*)
AND
(mask* OR threshold* OR visibility OR discrimination OR "continuous flash suppression" OR CFS)
```

## Q005 — Preserved capacity and unconscious function

**Purpose:** Find positive downstream-use effects without awareness plus explicit aware/unaware comparisons.

```text
(unconscious OR unaware OR invisible OR unseen OR subliminal OR nonconscious)
AND
(preserved OR intact OR capacity OR function OR use OR control OR evaluation OR updating OR binding OR maintenance OR memory OR action)
AND
(aware OR conscious OR visible OR seen OR awareness OR visibility OR comparison OR interaction OR equivalence OR Bayes*)
```

## Q006 — Masking, CFS, thresholds, and visibility fluctuations

**Purpose:** Cover methods that generate or exploit awareness contrasts for nominally similar X.

```text
(mask* OR "continuous flash suppression" OR CFS OR threshold* OR "near threshold" OR "subjective visibility" OR "visibility fluctuation*" OR "spontaneous visibility" OR "binocular rivalry")
AND
(aware OR unaware OR conscious OR unconscious OR seen OR unseen OR visible OR invisible)
AND
(control OR evaluation OR monitoring OR updating OR binding OR maintenance OR memory OR selection OR strategy OR adaptation)
```

## QDYN001 — Process-triggered expansion template

**Activation:** Use once for a newly normalized `Y_label` only after an experiment provisionally meets the A/E/F activation conditions in `PROTOCOL.md`. Search only the observed process. Log the rendered query verbatim, its trigger experiment, source, and normalization decision.

```text
(awareness OR aware OR unaware OR conscious OR unconscious OR visibility OR seen OR unseen)
AND
("{{Y_LABEL}}" OR {{FROZEN_Y_SYNONYMS_IF_ANY}})
AND
(experiment OR task OR performance)
AND
(mask* OR threshold* OR discrimination OR "continuous flash suppression" OR CFS OR blindsight)
```

`{{FROZEN_Y_SYNONYMS_IF_ANY}}` must be restricted to synonyms frozen for the observed Y at activation time. Do not add neighbouring cognitive processes. The rendered source-specific string is the auditable query; the template alone is not sufficient.

## Freeze checklist for queries

- Select exact databases and interfaces.
- Translate each draft into source-specific syntax.
- Freeze field restrictions, language/document-type limits, and publication cutoff behavior.
- Decide whether spelling, hyphenation, and controlled-vocabulary variants are explicit or source-generated.
- Define deduplication and pagination/export behavior.
- Pilot for syntax only before registration; preserve pilot changes in version history.
