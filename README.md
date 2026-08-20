# consciousness-sweep

`consciousness-sweep` is an auditable literature-review package for a specific question: for a content or entity **X** and a downstream cognitive process **Y**, does awareness of X change whether, or how well, Y can use X? The search is deliberately result-neutral. A useful experiment may support processing without awareness, an awareness-linked difference, no detectable difference, equivalence within a stated region, or an unresolved conclusion.

> **Current status: pre-freeze.** This package is not preregistered and does not yet authorize a registered sweep. Its publication cutoff, preferred search-source order, fallback order, and final query status still require human decisions. The active protocol is `draft-0.8.6`, the package is `prefreeze-package-0.8.6`, and the schema is `prefreeze-schema-0.8.5`.

`PROTOCOL.md` is the normative scientific and procedural authority. `AGENTS.md` is the normative execution authority. [METHODS.md](METHODS.md) is the complete, derived human-readable description; this README is only an orientation.

## Scientific records and why they are granular

The atomic scientific record is a **paper × physical experiment × X→Y comparison**, not a whole paper. A paper can contain several physical experiments, and one experiment can test several genuinely different downstream functions. Conversely, multiple component effects can jointly express one coherent factorial functional relation. Treating either the paper or every reported effect as the unit would therefore merge distinct questions or split one question destructively.

The package separates four objects:

- A **logical paper** is the deduplicated bibliographic work. Preprints and published versions are linked only when their relationship is sufficiently clear.
- A **physical experiment group** is one experiment as conducted and reported. Every physical experiment considered at full text receives a durable group record before any comparison is formed.
- A **comparison** is one conservative mapping from X to Y within a physical experiment. It is the unit that receives the scientific codes and inference results.
- A **support-only experiment** supplies evidence for another comparison but does not independently answer an eligible X→Y question. It remains represented as an experiment group and may be linked through an evidence bundle; it does not receive a placeholder comparison.

Stable identifiers distinguish papers, experiment groups, comparisons, searches, result encounters, decisions, evidence objects, and full-text assets. Identifiers are allocated once and never recycled, so revisions do not erase provenance.

## Discovery and screening

Discovery is broad but bounded and auditable. The principal route starts with fixed empirical seeds and review/discovery anchors. Eligible nodes are expanded backward through references and forward through citing papers in waves. A comparison that independently earns a qualifying downstream Y can activate a bounded process-specific search using a closed, provenance-recorded lexical set for that Y. These routes are complemented—not replaced—by a mandatory supplementary blind-spot lane.

One-hop empirical bridges improve citation recall without generic graph crawling: an adequately evaluated, non-CORE empirical paper may receive one citation hop only when one physical experiment clearly contains exactly two CORE ingredients, explicitly fails the third, and is a justified near-neighbor. Bridge-to-bridge continuation on the same lineage is prohibited; CORE resets depth, and bridge status affects discovery only.

The workflow is **principal-first, blind-last**. The seed, anchor, citation, and activated process frontiers must first be provisionally satisfied. Only then are all frozen blind windows run. The current conservative pre-freeze candidate has five active families—attention/control, metacognition/monitoring, binding/integration, memory operations, and action/rule-guided use—on OpenAlex and Europe PMC, with one initial window of at most 40 records per family and source. The generic learning/adaptation block is disabled because its current rendering was pathological; learning remains eligible through every other route. Whether to redesign or omit that generic block is still a pre-freeze decision.

Every returned record inside a completed window is recorded and screened. Rediscoveries remain in the discovery history even when they resolve to an existing logical paper. A genuinely new blind-lane node can reopen citation expansion, and a genuinely new qualifying Y can reopen process search. The sweep cannot finish until those reopened frontiers again satisfy their stopping rules.

Screening is semantic and paper-specific. Titles are reviewed in batches of at most 25 and abstracts in batches of at most 10, solely to amortize context; every paper receives its own decision and reason. Regexes, keywords, embeddings, citation counts, numerical relevance scores, and hidden lexical heuristics cannot independently exclude a record. A retained paper with no obtainable abstract is marked abstract-unavailable, prioritized from its title and provenance, and may proceed to full-text retrieval. Final comparison classification requires full text.

## A, E, and F

Each comparison is characterized along three design dimensions before its scientific outcomes are classified:

- **A: awareness evidence for X.** `A-direct` uses qualifying evidence in the focal experiment; `A-validated` uses a sufficiently transferable validation procedure; `A-transfer-risk` marks material transfer or sensitivity uncertainty; and `A-absent` means qualifying evidence is absent. Subjective evidence, informative objective invisibility evidence, or both may qualify. A described awareness procedure is not the same as a reported result. Strong A requires a supportive, located critical result in the focal experiment or, for transferred validation, a complete result-bearing awareness bundle.
- **E: first-order evidence about X.** `E-matched` requires active matching/titration on the relevant direct measure or successful equivalence under a stated margin. `E-diagnostic` is an alternative strong route for unmatched evidence when a prespecified structured same-Y pattern rules out the relevant simple evidence-strength account. `E-physical-only` and `E-uncontrolled` retain cases where stimulus identity or control is insufficient. Nominal physical identity is not internal-evidence matching.
- **F: meaningful downstream use Y.** `F-meaningful` requires an auditable downstream function or coherent mapping; `F-ambiguous` retains plausible downstream use whose function cannot be assigned conservatively; `F-not-meaningful` covers direct registration, generic neural response, or an effect that does not establish a downstream function. Mechanistic uncertainty does not by itself make F ambiguous.

Before comparisons are finalized, each physical experiment undergoes a pre-atomization functional-structure assessment. Components remain together when they jointly instantiate one conservative factorial mapping and the inference depends on their interaction or structured pattern. They are separated when they represent distinct outputs, stages, or input–output relations. Effect names and mechanism labels do not decide this question.

## Evidence spanning experiments

Some classifications depend on another experiment, analysis, supplement, or external work. Such support is never pooled informally. One **evidence bundle** represents one named premise for one focal comparison. Its required members are declared before the result is used; every member is directly linked with a source location, status, role, transfer reason, and limitation. A bundle is complete only when every required member supports the premise and is decision-used, incomplete when required support is absent, unavailable, unevaluated, or transfer-invalid, and conflicted when a member contradicts or is conflicted. Evidence links are non-transitive.

External support is stored separately as auxiliary evidence and does not enter the candidate pool merely because it was consulted. An execution-only evidence assessment may cache a verified fact for an exact source/version/regime, but it cannot propagate A/E/F or outcome classifications.

## Independent inference axes and overlapping outputs

The package keeps two principal scientific questions independent. **Unaware capacity** asks whether the exact focal Y is supported under the unaware condition. Strong E is not a gate: strong A, meaningful F, whole-Y evidence, adequate statistics, and any inference-critical Meyen requirement govern this route. **Awareness-linked difference** asks whether a direct aware/unaware test on the same focal Y supports a difference; its strongest route requires strong A, strong E, meaningful F, a focal same-experiment statistic, adequate statistics, and the applicable Meyen gate.

Direct comparisons are also recorded descriptively even when weak E prevents a constraint-ready awareness interpretation. A nonsignificant direct test may be classified as **no detectable awareness difference**, but this is not equivalence. **Equivalence-supported no difference** requires positive null evidence from a stated equivalence procedure, sufficiently strong Bayes factor, or an interval entirely within a stated equivalence region; margins are never invented retrospectively.

These are not mutually exclusive paper labels. A comparison may support unaware capacity while also showing an awareness-linked difference, or unaware capacity plus equivalence-supported invariance. Derived files therefore overlap where the scientific claims are compatible. An unresolved view preserves fully evaluated comparisons whose capacity or awareness-effect conclusion remains unclear.

## Independent runs and adjudication

Independent agents receive the same static frozen package but use separate run directories. They do not share dynamic search results, screening decisions, comparison structures, A/E/F codes, evidence assessments, statistical judgments, stopping judgments, or full-text annotations. Within-run workers may divide already reserved non-overlapping work, but all writes use the same locked, schema-aware writer.

Only after compatible independent runs finish may their discovery sets and comparison-level judgments be consolidated. Disagreement is resolved by returning to the source evidence under the frozen protocol, preserving each original judgment and the adjudication trail. Adjudication is not majority voting and cannot change the frozen protocol.

## Repository and outputs

The main package contains:

```text
PROTOCOL.md                 normative scientific/procedural rules
AGENTS.md                   normative execution contract
METHODS.md                  complete derived human-readable methods
config.yaml, queries.md     versioned execution and search instruments
seeds_*.csv                 empirical seeds and review/discovery anchors
schemas/                    strict run-record schemas
tools/                      initialization, writing, derivation, and validation
tests/                      synthetic and regression tests
docs/                       crosswalk, issues, and manual-review guide
runs/<RUN_ID>/              one isolated run (ignored by Git)
outputs/consolidated/       post-run consolidation target
```

Within a run, `papers_master.csv` holds logical-paper state; `experiment_groups.csv` records physical experiments; `experiments_master.csv` holds comparison rows; `search_log.csv` and `discoveries.csv` preserve search events and every encounter; evidence, missing-text, and full-text tables preserve their own provenance; `decision_log.jsonl` is append-only history; and `run_state.json` is the durable checkpoint. Deterministic derived files include design-eligible comparisons, awareness-linked differences, unaware capacities, no-detectable differences, equivalence-supported invariance, unresolved comparisons, and their constraint-ready union.

## Setup and lifecycle

Create the canonical isolated environment and audit this draft:

```sh
python3 tools/bootstrap_env.py --venv .venv
.venv/bin/python tools/preflight.py --mode pre-freeze
```

Registered start and resume commands are documented now but must not be used until the package is frozen:

```sh
.venv/bin/python tools/init_run.py --run-id <RUN_ID> --run-mode start --agent-harness <HARNESS>
.venv/bin/python tools/init_run.py --run-id <RUN_ID> --run-mode resume --agent-harness <HARNESS>
```

A start refuses an existing run directory. A resume requires exact package/schema compatibility, unchanged immutable-input hashes, and validated durable state; it neither recreates nor truncates prior records. At every search-wave checkpoint, outputs are regenerated and the run is validated:

```sh
.venv/bin/python tools/derive_outputs.py --run-id <RUN_ID>
.venv/bin/python tools/validate_run.py --run-id <RUN_ID>
```

The run remains incomplete until every principal route, mandatory blind window, reopened citation/process frontier, required full-text evaluation, evidence dependency, audit, and validation condition is satisfied. For the present draft, use only pre-freeze audit commands. Resolve the documented freeze items and complete human review before any registration or scientific execution.
