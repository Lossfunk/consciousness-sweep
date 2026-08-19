# Clean-room pilot 004 provenance

- Exact package commit: `742bf0b7d62d73853913da2ef1e932f7afc10996` (`Checkpoint pre-freeze draft-0.8.4`).
- Protocol: `draft-0.8.4`.
- Package: `prefreeze-package-0.8.4`.
- Schema: `prefreeze-schema-0.8.3`.
- Execution: fresh stripped clean-room Codex execution over the fixed seven-file scientific source fixture (six main articles and one permitted same-article supplement).
- External retrieval/search: none.
- Hidden context: no diagnostics, tests, gold corrections, prior-pilot material, or manuscript material was visible in the clean room.
- Run ID: `PREFREEZE_DIAG_004`.
- Harness/model: `codex-desktop`; model `GPT-5`; model version `2026-08-19`.
- Started: `2026-08-19T17:43:54.594296Z`.
- Last checkpoint: `2026-08-19T18:05:27.423024Z`.
- Source clean-room manifests are preserved byte-for-byte under `fixture_provenance/`.
- This archive is diagnostic calibration provenance only and MUST NOT enter registered-facing inputs.

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
Use the pre-freeze diagnostic run ID:
PREFREEZE\_DIAG\_004
Validate the resulting diagnostic outputs with the canonical package tools\
where applicable.
```
