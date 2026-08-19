# Documentation issues requiring human resolution

This file records only substantive issues exposed by the documentation pass. No authority text was changed to resolve them.

## 1. Registration state is intentionally unfinished

`config.yaml` sets `registration_status: pre-freeze`, and `PROTOCOL.md` states that the package is not preregistered. Registered preflight therefore refuses execution. Human action is required to complete review, freeze/version the package, and set an authorized registration state; this documentation pass does not determine that state.

## 2. Publication cutoff is absent

`config.yaml` leaves `publication_cutoff` null and requests an inclusive date plus timezone/interpretation. Search-window identity already includes this field, so the missing value affects what literature can be encountered and the reproducibility of each snapshot. A value and interpretation must be chosen before registration.

## 3. Preferred and fallback search-source order is not frozen

`search.preferred_sources` and `search.fallback_order` are empty. The same configuration records a calibration-only proposed strategy, while the conservative blind and process instruments specifically name OpenAlex and Europe PMC. `PROTOCOL.md` §9.3.1 says the citation-source rule remains to be fixed. The current text therefore supports bounded OpenAlex/Europe PMC execution for those two query routes but does not specify the overall registered preferred order, deterministic failure fallbacks, or unavailable-source substitution policy. Humans must resolve and version these fields.

## 4. Query specification still declares draft status

`queries.md` marks its exact strings as draft/to-freeze and retains historical calibration instruments alongside the active conservative candidate. The active QCAL4 families and QDYN rendering rules are identifiable and mechanically implemented, but the file-level draft markers intentionally block registered preflight. Human review must decide which source-specific strings and parameters become frozen and preserve historical material without making it executable.

## 5. Generic learning/adaptation blind-query decision remains open

The QCAL4-LEARN rendering is disabled/retired because it was pathological, while learning/adaptation remains scientifically eligible through all other routes. The authorities require a pre-v1 choice: redesign the generic blind block or explicitly omit such a block. The current five-family conservative lane is clear, but the final registered treatment of a generic LEARN blind window is unresolved.

## 6. Citation-source calibration conclusion and execution contract occupy different scopes

The calibration-only strategy proposes roles for OpenAlex, Europe PMC, Crossref, and optional Semantic Scholar. The active conservative query contract fixes OpenAlex and Europe PMC for blind and process windows, while the final citation-source/fallback order is unset. This is not a direct contradiction, but readers could mistake a route-specific executable source list for the complete source policy. `METHODS.md` therefore presents the fixed route-specific behavior and the unresolved overall policy separately. Human freeze review should confirm that this interpretation is intended.

## Coverage and unbacked-claim result

The structural crosswalk contains no unresolved coverage rows and no intentionally implementation-only rows. The side-by-side semantic review found no additional authority contradiction, missing METHODS coverage, or substantive METHODS claim lacking an authority. Automated structural coverage does not replace the manual review described in `docs/manual_methods_review.md`.
