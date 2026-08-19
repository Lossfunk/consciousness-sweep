# Clean-room pilot 002 manifest

## Purpose

This standalone, stripped workspace is prepared for a fresh-agent source-only sufficiency pilot. It contains the generic committed method and six supplied target articles, plus verified same-article supplementary material that was already locally available. It contains no scientific expected answers and no initialized scientific run.

## Exact package identity

- Source repository commit: `bdb762240b9df98b921e8813b566fc9bb1be5100`
- Protocol version: `draft-0.8.2`
- Package version: `prefreeze-package-0.8.2`
- Schema version: `prefreeze-schema-0.8.1`
- Registration status: `pre-freeze`

## Included canonical files

- `AGENTS.md`
- `PROTOCOL.md`
- `config.yaml`
- `queries.md`
- `requirements.txt`
- `seeds_empirical.csv`
- `seeds_reviews.csv`
- all 12 committed files under `schemas/`
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

The tool subset is the minimum committed set required for environment setup, preflight, run initialization, structured state writes, query rendering, execution-state enforcement, deterministic derivation, validation, and registered-facing leakage checks. `tools/calibration_sampling.py` is included because the canonical leakage guard's registered-facing allowlist requires that generic helper to be present; it is not invoked by this fixture audit.

## Target paper identities and supplied source assets

| Target paper | DOI | Asset | Type | Local source path used | Identity/boundary evidence | SHA-256 |
|---|---|---|---|---|---|---|
| Tsushima, Sasaki, and Watanabe (2006), *Greater Disruption Due to Failure of Inhibitory Control on an Ambiguous Distractor* | `10.1126/science.1133197` | `sources/tsushima_2006_main.pdf` | main article | `/private/tmp/consciousness-sweep-pilot-002-local-sources/tsushima_2006_main.pdf` | First page identifies the Science article, authors, year, and DOI; the local source byte-matches the verified article blob at the exact package commit. | `0b85d69e06753780e0f4b104ee1433f38ec71103f833e28a34924bb15a5b450b` |
| Tsushima, Sasaki, and Watanabe (2006) | `10.1126/science.1133197` | `sources/tsushima_2006_supplement.pdf` | official supplement | `/Users/sushrutthorat/Downloads/tsushima-som.pdf` | First page states “Supporting Online Material,” gives the full article title and authors, cites Science 314 (2006), and gives the same DOI. | `da60bf2662debfea258e63dbbf2645dcdcb7b3d6f4cfe1510c8632e40f696819` |
| Lin and Murray (2015), *More Power to the Unconscious: Conscious, but Not Unconscious, Exogenous Attention Requires Location Variation* | `10.1177/0956797614560770` | `sources/lin_murray_2015_main.pdf` | main article | `/Users/sushrutthorat/Documents/deep-consciousness/papers/emp_starts/bin/lin 2015.pdf` | Article first page gives the journal DOI and bibliographic identity. | `650e67516453234b752c60e1087c39e58c65946565345d283608b1a9c669830e` |
| Lamy, Alon, Carmel, and Shalev (2015), *The Role of Conscious Perception in Attentional Capture and Object-File Updating* | `10.1177/0956797614556777` | `sources/lamy_2015_main.pdf` | main article | `/Users/sushrutthorat/Documents/deep-consciousness/papers/emp_starts/lamy 2014.pdf` | Article first page gives the journal DOI and bibliographic identity; the online-first copyright year precedes the issue year. | `65f58da90cc42ce43888561fd05314f3b1d8086216ba89810dc475f9a94564f2` |
| Ben-Haim et al. (2021), *Disentangling Perceptual Awareness from Nonconscious Processing in Rhesus Monkeys (Macaca mulatta)* | `10.1073/pnas.2017543118` | `sources/ben_haim_2021_main.pdf` | main article | `/Users/sushrutthorat/Documents/deep-consciousness/papers/emp_starts/bin/ben-haim 2021.pdf` | PDF metadata and first page identify the PNAS article and authors. | `990f512970e66ae1887a89d9825bff41b3d155666892c6326e41e21c3cc222b5` |
| Persaud et al. (2011), *Awareness-Related Activity in Prefrontal and Parietal Cortices in Blindsight Reflects More Than Superior Visual Performance* | `10.1016/j.neuroimage.2011.06.081` | `sources/persaud_2011_main.pdf` | main article | `/Users/sushrutthorat/Documents/deep-consciousness/papers/emp_starts/persaud 2011.pdf` | PDF metadata and first page identify the NeuroImage article, authors, year, and DOI. | `e9e811cc2ff73fa730c7c369298050bb5183f3e2d8fe5bdeb77a82ef37284afa` |
| Keizer, Hommel, and Lamme (2015), *Consciousness Is Not Necessary for Visual Feature Binding* | `10.3758/s13423-014-0706-2` | `sources/keizer_2015_main.pdf` | main article | `/Users/sushrutthorat/Documents/deep-consciousness/papers/emp_starts/keizer 2015.pdf` | First page identifies the article, authors, and publication identity. | `b0d11f89da53b97cc336b1a5445c6e224c957e286aaecf30cb7fcd670aa7f051` |

No verified local supplement was available for Lin and Murray (2015), Lamy et al. (2015), Ben-Haim et al. (2021), Persaud et al. (2011), or Keizer et al. (2015). No external auxiliary work is supplied for any target paper.

## Empty output areas

- `runs/` exists and is empty.
- `outputs/consolidated/` exists and is empty.

## Explicit exclusions

The fixture excludes Git metadata; diagnostics; tests; prior runs and outputs; calibration and prior-pilot artifacts; adjudications and gold material; efficiency, provenance, decontamination, implementation, and transplant reports; manuscripts and manuscript claims; previous prompts and model outputs; annotations and assessment sidecars; cached or temporary files; extracted classifications; expected focal experiments; expected X/Y, A/E/F, capacity/effect/equivalence, Meyen, bundle, process-search, or constraint-ready answers; and all external auxiliary literature.

The six empirical seed identities remain intact as neutral committed inputs. No scientific expected answers are included.

## Hash manifest

SHA-256 hashes for every included file other than the hash manifest itself are in `cleanroom_sha256.txt`.
