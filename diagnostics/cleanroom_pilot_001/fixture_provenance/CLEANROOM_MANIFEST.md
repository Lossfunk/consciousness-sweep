# Clean-room manifest

## Purpose

Standalone fixture for a future fresh-agent sufficiency test of the committed pre-freeze method package. This fixture does not contain a scientific run or expected scientific classifications.

## Source checkpoint

- Git commit: `0be0cc2d0a18dfbec320f8a2ace0b16573914f8c`
- Protocol: `draft-0.8.1`
- Package: `prefreeze-package-0.8.1`
- Schema: `prefreeze-schema-0.8`
- Registration status: `pre-freeze`

## Included canonical content

- `AGENTS.md`
- `PROTOCOL.md`
- `config.yaml`
- `queries.md`
- `requirements.txt`
- `seeds_empirical.csv`
- `seeds_reviews.csv`
- `schemas/` containing the 12 canonical schemas
- `tools/bootstrap_env.py`
- `tools/preflight.py`
- `tools/init_run.py`
- `tools/structured_write.py`
- `tools/validate_run.py`
- `tools/derive_outputs.py`
- `tools/query_instruments.py`
- `tools/execution_contract.py`
- `tools/leakage_guard.py`
- `tools/calibration_sampling.py`
- empty `runs/`
- empty `outputs/consolidated/`

`tools/leakage_guard.py` is included because canonical preflight imports it. `tools/calibration_sampling.py` is included only because the committed leakage guard's explicit registered-facing allowlist requires that canonical file to exist; it is answer-neutral and does not authorize or contain a CALIB run. The other included tools are the minimum canonical subset for environment setup, package preflight, initialization, structured writes, output derivation, run validation, query rendering, and execution-state logic.

## Supplied source papers

- `sources/tsushima_2006.pdf`
- `sources/lin_murray_2015.pdf`
- `sources/lamy_2015.pdf`
- `sources/ben_haim_2021.pdf`
- `sources/persaud_2011.pdf`
- `sources/keizer_2015.pdf`

## Intentionally excluded

- Git metadata and repository history
- diagnostics and calibration provenance
- tests and diagnostic fixtures
- prior runs and outputs
- calibration, regression, audit, implementation, and decontamination reports
- manuscripts, previous prompts, and previous model outputs
- annotations, sidecars, assessments, prior scientific classifications, and answer keys
- caches, bytecode, and temporary files

No expected focal experiments, X/Y assignments, A/E/F classifications, capacity/effect/equivalence outcomes, Meyen judgments, evidence-bundle answers, or paper-specific process-query vocabularies were added to this fixture.

SHA-256 hashes for every included file except the hash manifest itself are recorded in `cleanroom_sha256.txt`.
