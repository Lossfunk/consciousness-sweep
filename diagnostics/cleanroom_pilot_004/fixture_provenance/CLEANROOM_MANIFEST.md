# Final pre-freeze clean-room fixture manifest

## Purpose

Standalone, stripped fixture for a fresh-agent pre-freeze diagnostic of the committed generic package. The fixture construction performs no scientific run, paper classification, literature search, retrieval, freeze, or registration.

## Package identity

- HEAD commit: `742bf0b7d62d73853913da2ef1e932f7afc10996`
- Protocol: `draft-0.8.4`
- Package: `prefreeze-package-0.8.4`
- Schema: `prefreeze-schema-0.8.3`

## Canonical included files

- `AGENTS.md`
- `PROTOCOL.md`
- `config.yaml`
- `queries.md`
- `requirements.txt`
- `seeds_empirical.csv`
- `seeds_reviews.csv`
- `schemas/auxiliary_sources.schema.json`
- `schemas/decision_log.schema.json`
- `schemas/discoveries.schema.json`
- `schemas/evidence_assessments.schema.json`
- `schemas/evidence_bundles.schema.json`
- `schemas/evidence_links.schema.json`
- `schemas/experiments.schema.json`
- `schemas/fulltext_assets.schema.json`
- `schemas/missing_texts.schema.json`
- `schemas/papers.schema.json`
- `schemas/run_state.schema.json`
- `schemas/search_log.schema.json`
- `tools/bootstrap_env.py`
- `tools/preflight.py`
- `tools/init_run.py`
- `tools/structured_write.py`
- `tools/derive_outputs.py`
- `tools/validate_run.py`
- `tools/execution_contract.py`
- `tools/query_instruments.py`
- `tools/leakage_guard.py`
- `tools/calibration_sampling.py`

`tools/calibration_sampling.py` is included because exact-HEAD preflight/leakage validation requires it in the registered-facing tool allowlist. It is a generic deterministic sampling helper and contains no paper-specific answer material. No other additional static helper is required.

## Supplied scientific source assets

| Fixture path | Article identity | Status | SHA-256 |
|---|---|---|---|
| `sources/ben_haim_2021_main.pdf` | Ben-Haim et al. (2021), DOI `10.1073/pnas.2017543118` | Main article | `990f512970e66ae1887a89d9825bff41b3d155666892c6326e41e21c3cc222b5` |
| `sources/keizer_2015_main.pdf` | Keizer et al. (2015), DOI `10.3758/s13423-014-0706-2` | Main article | `b0d11f89da53b97cc336b1a5445c6e224c957e286aaecf30cb7fcd670aa7f051` |
| `sources/lamy_2015_main.pdf` | Lamy et al. (2015), DOI `10.1177/0956797614556777` | Main article | `65f58da90cc42ce43888561fd05314f3b1d8086216ba89810dc475f9a94564f2` |
| `sources/lin_murray_2015_main.pdf` | Lin and Murray (2015), DOI `10.1177/0956797614560770` | Main article | `650e67516453234b752c60e1087c39e58c65946565345d283608b1a9c669830e` |
| `sources/persaud_2011_main.pdf` | Persaud et al. (2011), DOI `10.1016/j.neuroimage.2011.06.081` | Main article | `e9e811cc2ff73fa730c7c369298050bb5183f3e2d8fe5bdeb77a82ef37284afa` |
| `sources/tsushima_2006_main.pdf` | Tsushima et al. (2006), DOI `10.1126/science.1133197` | Main article | `0b85d69e06753780e0f4b104ee1433f38ec71103f833e28a34924bb15a5b450b` |
| `sources/tsushima_2006_supplement.pdf` | Tsushima et al. (2006), DOI `10.1126/science.1133197` | Same-article Supporting Online Material | `da60bf2662debfea258e63dbbf2645dcdcb7b3d6f4cfe1510c8632e40f696819` |

## Excluded categories

Excluded completely: Git metadata and history; diagnostics; tests; calibration runs and material; prior clean-room archives, prompts, adjudications, reports, corrections, and model outputs; manuscript material; historical runs and outputs; external auxiliary literature; additional supplements; annotations and sidecars; caches; temporary artifacts; prior scientific state; and expected paper classifications, focal experiments, X/Y labels, A/E/F codes, evidence bundles, contrast-integrity judgments, capacity/effect/null/equivalence codes, or constraint-ready results.

`runs/` and `outputs/consolidated/` are intentionally empty. No expected scientific answers are present in this fixture.

The complete fixture hash manifest is `cleanroom_sha256.txt`; it hashes every fixture file except itself.
