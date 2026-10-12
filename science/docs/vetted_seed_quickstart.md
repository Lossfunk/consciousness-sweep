# Prepare a future sweep from author-vetted papers

This is preparation guidance under `PROTOCOL.md` §§9.2 and 10. It starts no
sweep and changes no existing registered run. `AGENTS.md` supplies the actual
start/resume and completion contract. The default package includes the complete
manuscript bibliography. A targeted continuation requires its own frozen seed
identities, protocol/package revision, validation and explicit launch.

## Inputs and preparation

Use the current explicit human primary/support decision log maintained by
`tools/postrun_human_decisions.py`. The author must actually have made those
decisions; agent recommendations are not accepted choices. Manuscript
initialization records the author's already chosen examples. The preparation
tool schema-validates those events, takes the latest event per work, and selects
only current primary/support acceptance. Pending and declined works are omitted
from this seed selection; they remain in their historical recommendation pool.

Prepare a bibliographic CSV with these headers:

```text
work_key,title,authors,year,doi,url,article_version
```

Use the exact work keys and article versions in the human decisions, with
verified bibliographic identities. Resolve confirmed duplicates before
preparation; retain genuinely uncertain versions separately until identity is
resolved. No expected A/E/F, favored result, function label or editorial tier
belongs in the distributed seed metadata.

From a verified source package, prepare a **new, absent** directory. Replace
`NEW_REVISION` with the newly commissioned revision identifier; it must differ
from the source and the active development candidate. The placeholder does not
name or authorize another active revision:

```sh
.venv/bin/python tools/prepare_vetted_seeds.py \
  --human-decisions /absolute/path/to/explicit-human-decisions.jsonl \
  --bibliography /absolute/path/to/verified-bibliography.csv \
  --destination /absolute/path/to/new-seed-revision \
  --revision-version NEW_REVISION-candidate \
  --authorization 'Explicit author instruction to prepare the selected identity scope'
```

`--original-graph-reference` may identify the prior graph's provenance when one
exists. It does not assign an unproven graph depth. The tool copies only the
registered-facing allowlist, preserves the source bytes, normalizes bibliographic
DOIs/URLs before persistence, replaces only empirical seeds, and keeps the broad
review anchors and all other discovery obligations. It writes the declared basis,
ordered identity hash and neutral human-event attestation. Actual prior roles and
scientific judgments are not supplied to the new independent reviewer. Historical
run files, outputs, tests and answer keys are not copied.

The generated revision is **prepared, not frozen or launched**. Its temporary
blocked readiness is an unfinished validation state, not a permanent limitation
of the instrument. Complete the prospective revision validation and freeze under
the package's release process; never change readiness merely to bypass a gate.
Preflight and initialization require the declared seed identities and attestation
to agree. Recorded user provenance is auditable evidence, not cryptographic proof
of a human decision; the coordinator must not fabricate it.

## Freeze, launch and report

After the commissioned revision is validated and frozen, build/verify a clean
release with `tools/package_release.py`. The receiving agent bootstraps the
canonical environment, runs registered preflight, and initializes a fresh run
using the exact start command in `AGENTS.md`. A prior run cannot be resumed with
changed seed identities or scientific inputs.

Use the frozen criteria independently on the seed papers and new discoveries.
Previous author acceptance makes an identity a discovery start point; it neither
certifies a scientific result nor overrides contrary source evidence. Every
encounter, duplicate and classification remains recorded under the usual rules.
Follow principal routes, then every blind window, then all reopened citation and
process obligations until the unchanged stopping conditions hold. Missing texts
stay in the bounded request queue while independent work continues.

Report backward/forward parent/source coverage and completed wave obligations.
Fresh seeds have seed-relative distance zero. A one-hop neighbor of a previously
depth-two paper may be at original depth one, two or three after deduplication;
only the prior graph provenance establishes that label. Describe a targeted
continuation from the selected seeds, not complete global depth-three coverage.
Do not launch that continuation automatically when the author accepts a reading
recommendation.
