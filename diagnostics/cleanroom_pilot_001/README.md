# Clean-room pilot 001 provenance

- Purpose: bounded pre-freeze source-only sufficiency diagnostic of the scientific and execution package; not a registered result or literature sweep.
- Source package commit: `0be0cc2d0a18dfbec320f8a2ace0b16573914f8c`.
- Source versions: protocol `draft-0.8.1`; package `prefreeze-package-0.8.1`; schema `prefreeze-schema-0.8`; registration status `pre-freeze`.
- Session: fresh Codex session using model `gpt-5`, model version `2026-08-19`, harness `codex-desktop`.
- Run interval: started `2026-08-19T06:54:04.262898Z`; final checkpoint `2026-08-19T07:10:09Z`.
- Fixture isolation: diagnostics, tests, gold material, calibration provenance, prior runs/outputs, and manuscript files were absent.
- Available literature: exactly six supplied main-article PDFs under `sources/`; no supplements or auxiliary literature were supplied.
- Retrieval: no network search, citation expansion, API call, supplement retrieval, or outside-paper retrieval occurred.
- Archive scope: `run/` preserves the complete scientific output, source assets, decision history, exact final report, comparison and evidence tables, state, manifests, and execution artifacts. Transient bytecode/module caches and the empty lock file are excluded because they are not scientific output.
- Fixture provenance: `fixture_provenance/` preserves the clean-room manifest and its original SHA-256 manifest.

Exact minimal prompt:

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

This archive is diagnostic calibration provenance. It MUST NOT enter registered-facing agent inputs, registered runs, or future clean-room fixtures.
