# Clean-room pilot 003 provenance

- Source repository commit: `bdb762240b9df98b921e8813b566fc9bb1be5100`. The clean-room package was copied from the then-current uncommitted pre-freeze draft files identified by the versions and immutable hashes in `run/run_state.json`; the commit identifies the repository base and does not imply those draft files were committed.
- Protocol: `draft-0.8.3`.
- Package: `prefreeze-package-0.8.3`.
- Schema: `prefreeze-schema-0.8.2`.
- Execution: fresh stripped clean-room Codex execution over the bounded source fixture.
- Fixture: six main articles and the supplied same-article supplement for one article.
- Excluded context: no external auxiliary literature was supplied; diagnostics, tests, gold corrections, and manuscript material were not visible.
- Network: no network use or external retrieval.
- Harness/model: `codex-desktop`; model field `gpt-5`; model-version field unavailable.
- Started: `2026-08-19T15:25:54.324525Z`.
- Last checkpoint: `2026-08-19T15:44:18.395984Z`.
- Original run ID: `CALIB003`.
- Namespace note: this run ID was an accidental naming collision with the historical `CALIB_*` namespace. It does not make this source-bounded clean-room diagnostic a historical calibration run.
- Clean-room manifests at source: none were present at the workspace root; the archive manifest below was created after byte-preserving copy and verification.

## Exact minimal prompt

> Perform a bounded pre-freeze diagnostic run of the supplied consciousness-sweep protocol.
> Work only from the files present in this workspace.
> Follow the supplied protocol, agent instructions, configuration, schemas, and execution tooling exactly as written. Treat the supplied scientific articles as the complete closed-world source set for this run.
> Do not use the network. Do not search for or retrieve external literature. Do not infer missing evidence from outside knowledge.
> Execute the protocol on the supplied source set from start to finish, producing the normal run artifacts and derived outputs required by the package.
> Preserve uncertainty where the supplied evidence does not justify a stronger classification. Do not optimize toward any expected scientific answer.
> This is a diagnostic pre-freeze run, not a registered run.
> When finished, report the run status, number of papers / physical experiment groups / scientifically relevant X→Y comparisons, counts entering each derived output route, unresolved items, validation results, and paths to the principal generated artifacts.
> Do not modify the protocol, schemas, package rules, source fixture, or historical runs. Do not commit changes.
