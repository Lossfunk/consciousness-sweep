# Clean-room pilot 002 provenance

This directory is a diagnostic-calibration archive. It **MUST NOT** enter registered-facing inputs, independent-run inputs, clean-room fixtures, seeds, queries, schemas, or scientific-run outputs.

## Package identity

- Source package commit: `bdb762240b9df98b921e8813b566fc9bb1be5100`
- Protocol version: `draft-0.8.2`
- Package version: `prefreeze-package-0.8.2`
- Schema version: `prefreeze-schema-0.8.1`
- Registration status: `pre-freeze`

## Session and source policy

- Fresh Codex session: yes
- Harness: `codex-desktop`
- Model: `gpt-5.6-sol`
- Model version recorded in run state: `2026-08-19`
- Run start: `2026-08-19T12:44:11.040818Z`
- Final checkpoint: `2026-08-19T13:06:36.671280Z`
- Source policy: six supplied main articles plus the same-article Tsushima Supporting Online Material
- External auxiliary literature supplied: none
- Diagnostics, tests, gold material, and manuscript material visible to the fresh session: none
- Network search or retrieval: none

## Exact minimal prompt

```text
This is a bounded pre-freeze diagnostic, not a literature sweep.
Read PROTOCOL.md and AGENTS.md fully and follow the method they specify.
Using only the papers supplied in `sources/`, evaluate the scientifically\
relevant X→Y comparisons under the current package.
Produce structured, auditable classifications using the package's terminology\
and schemas, together with a concise final report explaining the evidence for\
each decision.
Do not search for or retrieve additional literature.\
Do not access files outside this workspace.\
Do not assume that every experiment in a paper qualifies.\
Report uncertainty rather than filling gaps by guesswork.
Validate the resulting diagnostic outputs with the canonical package tools\
where applicable.
```

## Contents

- `run/`: byte-preserving copy of the complete `PREFREEZE-DIAG-002` run, including its empty lock file and empty `fulltexts/` directory.
- `fixture_provenance/`: byte-preserving copies of the clean-room manifest and its original source-fixture hash manifest.
- `SHA256SUMS`: hashes of every archived file other than `SHA256SUMS` itself.

The run remains exactly as classified by the fresh agent. Scientific adjudication is separate from this archive.
