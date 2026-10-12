# consciousness-sweep

For information X and a downstream function Y, does awareness of X change whether, or how well, Y can use X?

The pipeline discovers scientifically relevant prospects for the author to vet. Each prospect explains what it might add to the awareness–use profile, the decisive evidence, the remaining alternative and a concrete reading question. Primary/support is a tentative annotation after that argument, not the admission test for the queue.

The scientific reference is the user-designated Lossfunk-3 manuscript and the user's explicit clarifications. Strong scientific conclusions retain the awareness, signal-control, functional and statistical criteria. Prospect delivery does not claim final adjudication or exhaustive recall.

**Status:** 0.9.13, frozen

**Package:** package-0.9.14 (bibliographic update only; scientific authorities unchanged)

Release authorization is determined by `RELEASE_READINESS.json`; freezing these authorities alone does not authorize launch.

Development validation records remain outside the reviewer package. Readiness requires separate software, scientific-route, native-lifecycle, persistence-scale, distribution and portability receipts. The earlier sources remain historical provenance.

## Start here

Read [the short workflow](PROTOCOL_BRIEF.md) first, then use [the run quickstart](docs/run_quickstart.md) for the complete workflow: setup, discovery, source assessment, validated checkpoint prospect delivery and explicit human decisions. The same current comparison records and review reasons feed the handoff; there is no second paper-classification pipeline. For a supplied article, use the [standalone full-text guide](FULLTEXT_REVIEW.md), generated from exact authority sections and verified by `tools/render_fulltext_review.py`. [PROTOCOL.md](PROTOCOL.md) is the scientific authority; [AGENTS.md](AGENTS.md) covers execution. [METHODS.md](METHODS.md) is the detailed derived account, with structural coverage tracked in `docs/methods_crosswalk.yaml`.

The internal letter codes are storage labels for awareness evidence, signal-strength control and functional interpretation. They add no criterion beyond those substantive judgments.

The default seed scope covers all 60 logical works in the user-designated manuscript v2 bibliography: 18 empirical seeds and 42 review/discovery anchors. Seed identity conveys no expected eligibility or evidence tier. The Meyen preprint and journal publication are represented by the existing journal seed as one logical work. A newly commissioned revision can instead freeze author-vetted primary/support seed identities using the [vetted-seed quickstart](docs/vetted_seed_quickstart.md); model recommendations never establish that acceptance. Both scopes retain ordinary citation expansion, broad review anchors, earned function-specific searches and all eleven supplementary blind-search families. Any mental function can qualify; the family list is not an eligibility boundary. Preprints and directly relevant human patient studies are eligible, graded awareness is allowed, and there is no date cutoff. Default prospects need a source-grounded argument and valid native records; unfinished scientific interpretation or tentative role does not require certified primary/support agreement. Optional certified primary/support claims retain their independent checks. Existing explicit human decisions stay visible outside the first-read queue. This package requires Python >=3.9 on macOS/Unix; its POSIX writer does not support native Windows. Git is optional; preflight checks exact dependency pins.

Positive use without awareness is distinct from unchanged use across awareness conditions. Capacity-only evidence stays supplementary; suggestive and complementary results remain visible. Meyen is recorded separately. Evidence ordering is qualitative, with source-based reasons.

The default handoff is `profile-prospect`. The coordinator updates it at every validated checkpoint, accounts for newly assessed candidates and preserves earlier entries or records why their disposition changed. Its claim, decisive evidence, remaining alternative and human question come before a tentative primary/support/undetermined role. A located or specifically unresolved same-X→same-Y awareness comparison can justify reading even with weak control or incomplete statistics. Known absence of that comparison or a downstream function belongs in context. Scientific unaware capacities keep their exports and earned searches. See [the handoff reference](docs/postrun_handoff.md).

A provisional guide permits open frontiers and unfinished prospect judgments under native validation. A final guide still requires all frozen search and completion obligations. Human acceptance remains pending; existing explicit acceptances/rejections remain visible and are not silently put back in the first-read queue. If an error appears, first distinguish source, claim-scope and state errors from a genuine policy ambiguity before changing instructions.

## Verify the package before use

```sh
python3 tools/bootstrap_env.py --venv .venv
.venv/bin/python tools/preflight.py --mode registered
.venv/bin/python tools/validate_documentation.py
```

Preflight verifies the frozen inputs and release readiness; documentation validation verifies structural coverage. The bounded source checks retain unresolved interpretations and do not certify future paper-level correctness. Future pre-freeze diagnostics use the explicit diagnostic mode/namespace in `AGENTS.md`; none of these commands starts a sweep.

After readiness and freeze, `tools/package_release.py build` prepares an isolated allowlisted release and `verify --distribution` checks it before handover. The builder creates a hash manifest and refuses an existing destination. Tests, diagnostics, historical runs, dynamic search results and this preparation conversation are excluded. The receiving reviewer bootstraps its own environment and verifies the release before using the future start/resume commands in the run quickstart. Preflight checks the manifest when present; initialization records the immutable-input hashes.

The manifest identifies the actual distributed files even when source changes are uncommitted. It is not a cryptographic signature. Independent reviewers receive the same verified package and separate run directories. Neither verification nor packaging authorizes or starts a sweep.

## Files and responsibilities

| Files | Purpose |
|---|---|
| `PROTOCOL_BRIEF.md` | Short workflow and conditional checks |
| `FULLTEXT_REVIEW.md`, `tools/render_fulltext_review.py` | Exact, hash-bound standalone rendering for a PDF reviewer |
| `docs/vetted_seed_quickstart.md`, `tools/prepare_vetted_seeds.py`, `seed_authorization.json` | Prepare a newly versioned identity-only seed scope from explicit author decisions |
| `PROTOCOL.md`, `AGENTS.md` | Scientific and execution authorities |
| `tools/statistical_consistency.py` | Ordinary reference probabilities under explicit parameters; source/statistics receipt checks, never scientific classification |
| `tools/semantic_rescue.py` | Non-excluding, source-bound rescue signatures and demotion-audit manifests |
| `tools/postrun_handoff.py`, `schemas/postrun_handoff.schema.json` | Default prospect queue at validated checkpoints; optional certified claims and final completed-run handoff |
| `tools/postrun_human_decisions.py`, `schemas/postrun_human_decision.schema.json` | Final explicit human primary/support decisions and current accepted view; never inferred from recommendations |
| `METHODS.md`, `docs/` | Detailed explanation and documentation coverage |
| `config.yaml`, `queries.md`, `seeds_*.csv` | Active search configuration and seeds |
| `schemas/`, `tools/` | Record validation, writing, query rendering and output derivation |
| `runs/<RUN_ID>/` | One independent run's evidence and complete history |
| `outputs/consolidated/` | Post-run union and source-based adjudication |

The supplementary queries have bounded vocabulary-quality evidence, not a measured recall guarantee or verified empirical calibration of every final rendering. Completed run snapshots retain their exact request and results. The fixed search limits and stopping rules are in `PROTOCOL.md` and `queries.md`.
