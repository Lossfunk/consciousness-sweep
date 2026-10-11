# Running one independent sweep

**Current status:** 0.9.13, frozen.
Release readiness is controlled by `RELEASE_READINESS.json` and its hash-bound acceptance receipts. The commands below apply to a verified isolated release. Starting a scientific
sweep remains a separate explicit action; verification alone does not launch one.

Use this guide inside a verified isolated release with Python >=3.9 on macOS or
another POSIX Unix environment. Git is optional. Package-index access is needed
for the canonical bootstrap; discovery and retrieval require the sources named
in `queries.md`. Scientific rules remain in `PROTOCOL.md`; execution rules remain
in `AGENTS.md`.

## Canonical invocation

From the release directory:

```sh
python3 tools/bootstrap_env.py --venv .venv
.venv/bin/python tools/package_release.py verify --root .
.venv/bin/python tools/preflight.py --mode registered
.venv/bin/python tools/init_run.py --run-id RUN001 --run-mode start --agent-harness YOUR_HARNESS --model YOUR_MODEL --model-version YOUR_VERSION
```

Supply the real model/harness metadata and a new filesystem-safe run ID. The
initializer refuses an existing run directory. The release creator uses
`package_release.py verify --distribution` before handing over a pristine
package. Runtime verification permits only the explicitly documented local
environment, bytecode and recipient records in addition to the operative files.

To resume after an interruption:

```sh
.venv/bin/python tools/package_release.py verify --root .
.venv/bin/python tools/init_run.py --run-id RUN001 --run-mode resume --agent-harness YOUR_HARNESS --model YOUR_MODEL --model-version YOUR_VERSION
```

Resume validates the durable state, preserves retired identifiers and recovers
committed transactions. A completed run additionally needs a substantive
`--reopen-reason` under the unchanged frozen authorities.

## Coordinator and source-bound workers

Give each worker the same release and a non-overlapping, already reserved unit
within this run. Workers receive source identity/version, verified text or
retrieval task, relevant authority sections and the stable entity IDs. They
return individual located reasons and typed records. They do not infer new IDs,
inspect another run or bypass the shared writer.

Initialize every frozen empirical seed and review anchor, then maintain the
principal citation and earned-function frontiers before the mandatory blind
lane. `query_instruments.py` renders source-specific queries; `execution_contract.py`
provides deterministic window keys and ordered result hashes. Follow every
citation page to exhaustion, retain each encountered result, and handle retries
and missing coverage exactly as `queries.md` requires. A local empty fixture is
an execution test, never evidence that a live scientific search was exhausted.

Screen each logical work with its own semantic reason. Preserve the exact
abstract/hash or explicit unavailable state. Verify and cache each full-text
version once. Inventory physical experiments before comparison decomposition.
New group rows include `record_status: active`, null `reconciled_into_experiment_id`
and null `record_status_reason` unless a source-backed reason applies. If an allocated row is later established
as nonphysical bookkeeping, follow AGENTS §2: preserve its ID/history, retire it
with the located reason, and reconcile current references atomically. A real
support-only experiment remains active. Count active physical groups separately
from retained retired records; never silently migrate a historical run.
For local JATS XML, `tools/source_identity.py ARTICLE.xml` extracts source-encoded
front-matter authors, title, article identifiers and abstract with the exact
source hash. It handles authors encoded on a parent contributor group and
excludes explicitly nonauthor roles. Verify the actual paper/version, preserve
missing metadata honestly, and run the bibliography normalization dry run before
persistence; this factual helper never screens or classifies a work.
The primary reader assesses each focal X→Y question from located evidence.
In the normal full-text work unit, keep information X, awareness-measured
content, conservative function Y, measured outcome and mechanism proposal
distinct. Locate the actual functional test and its experiment, sample, timing
and report order; explain why the readout supports the proposed function.
Before consequential export, a separate source checker records source facts
without proposed labels, tiers or expected human decisions, then checks the
proposed claim against those passages. Use the existing reasons and the source,
disclosure, assessment and review events required by `AGENTS.md` §7; no parallel
review form or scientific table is needed. Register actual actors; model labels
alone do not establish independence. Revise unresolved premises explicitly and
retain useful support. These same current records feed the required checkpoint prospect queue. A prospect can carry an unresolved scientific premise; independent promotion checks are required when the underlying scientific record makes a strong claim, not merely because a paper is worth human reading.
The source-only receipt also contains `critical_statistics` before label disclosure: measured outcome, source analysis, sample and unit, inferential convention and numerical consistency. In its existing statistics check, the checker retains those observations, uses `statistical_review_scope(comparison)` for the exact focal analysis, and explains whether uncertainty is nonfatal or critical. For an applicable ordinary reference probability, run `.venv/bin/python tools/statistical_consistency.py PARAMETERS.json`. Its JSON inputs explicitly name `distribution` (`student-t`, `normal-z`, or `F`), `statistic` and `tail`; Student-t additionally requires `df`, and F requires `df_numerator`, `df_denominator` and upper (`greater`) tail. Parameter basis and assumptions belong in the source receipt; no N-to-df inference or automatic scientific decision occurs. Record other inferential conventions or missing parameters with a specific noncomputation reason. See AGENTS §7 for the payload contract.

The neutral checker packet includes the complete identity inventory and the
raw outcome/analysis mapped to each reserved comparison ID. Supporting groups
and reanalyses remain visible without proposed function labels or tiers.

## Structured records and function activation

Write JSON with typed values, then use the schema-aware writer; never construct
CSV rows through delimiter joining. Reserve identifiers through its locked
allocator. Parent records must exist before referenced records, and a physical
experiment group must exist before comparison allocation.

```sh
.venv/bin/python tools/structured_write.py allocate-id --run-id RUN001 --id-kind paper
.venv/bin/python tools/structured_write.py append-decision --run-id RUN001 --row-file runs/RUN001/work/decision.json
.venv/bin/python tools/structured_write.py append-csv --run-id RUN001 --table papers_master.csv --row-file runs/RUN001/work/paper.json
```

The decision JSON contains its reserved decision ID, entity type/ID, timestamp,
field, old/new typed values, source location, reason and real actor. Append the
decision before the corresponding current-state write. Current-state revisions
use `upsert-csv --key-field` with the table's stable primary key.

Use bounded transactions for ingestion and revisions: at most 100 CSV mutations
and 1,000 decision events per batch. The batch validates typed records and
references before publication, serializes writers under the run lock, publishes
decision history before current state, and recovers a committed journal by
deterministic roll-forward after interruption. Identifiers are reserved first
with `allocate_identifiers`; at most 1,000 IDs can be reserved in one call.
Uncommitted rejected batches change no records. Reserved IDs remain retired.

For several identifier kinds or comparison parents, use
`reserve_identifiers(run_dir, requests, root=root)`. Each request contains exactly
`kind`, `count`, and `parent_id` (null for a scalar identifier kind); the summed
count is at most 1,000. Returned identifier lists follow request order. This
reserves all ranges with one state write and validates durable comparison
parents once. The CLI equivalent is `reserve-ids --run-id RUN001 --row-file
runs/RUN001/work/id_requests.json`, where the JSON file is the request array.

This complete API example revises one actual typed current paper using an
explicit full-record decision and compare-and-swap protection. Run Python from
the release directory; replace the title and source pointer with verified facts.

```python
import copy
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

root = Path.cwd()
sys.path.insert(0, str(root / "tools"))
from structured_write import allocate_identifiers, load_schema, write_batch
from validate_run import load_csv_rows

run_dir = root / "runs" / "RUN001"
errors = []
rows = load_csv_rows(run_dir / "papers_master.csv",
                     load_schema(root, "papers.schema.json"), errors)
if errors:
    raise ValueError(errors)
old = next(row for row in rows if row["paper_id"] == "P000001")
new = copy.deepcopy(old)
new["title"] = "Actual title verified against the article front matter"
decision_id = allocate_identifiers(run_dir, "decision", count=1, root=root)[0]
event = {
    "decision_id": decision_id, "run_id": "RUN001",
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "entity_type": "paper", "entity_id": old["paper_id"],
    "decision_type": "bibliographic-correction", "field": "record",
    "old_value": old, "new_value": new,
    "reason": "The verified article front matter supplies the corrected title.",
    "source_location": "Verified article, title page", "agent": "YOUR_REAL_ACTOR",
}
write_batch(run_dir, [{
    "table": "papers_master.csv", "mode": "upsert", "record": new,
    "expected_current": old, "decision_ids": [decision_id],
}], [event], root=root)
```

An append mutation uses `mode="append"`, `expected_current=None`, a fully typed
new record and a reserved ID. A `field="record"` decision binds the complete
old/new row; individual field decisions may instead cover every changed
property. Stale current state rejects the transaction. The same payload can be
saved as JSON and submitted through:

```sh
.venv/bin/python tools/structured_write.py batch --run-id RUN001 --row-file runs/RUN001/work/batch.json
```

An omitted optional inventory is stored as an empty inventory; it creates no
scientific assessment or successful source check. Required and conditionally
required scientific fields still need explicit valid values. The writer uses
the same canonical representation when checking an expected current row.

Run-state updates use the same batch with `state_updates`, matching run decisions
named in `state_decision_ids`, and an optional complete `expected_state` snapshot.
Immutable identity and allocator counters cannot be edited through this path.
Use it for checkpoints and workflow transitions; never replace run state from a
worker's stale snapshot. Keep parent creation and dependent records in order
within a batch. Reserve comparison IDs only after their physical group is durable.

For every earned function, create the comparison's `process_search_activation`
decision value with this imported helper:

```python
from execution_contract import process_activation_payload

payload = process_activation_payload(
    current_typed_comparison,
    normalized_y_label,
    normalization_reason="Located source terms denote the same conservative function.",
    prior_normalized_y_labels=current_state["activated_normalized_y_labels"],
)
```

Append the event before updating run state or starting a window. The payload
binds the original eligible comparison and records `new-y` or `same-y-reuse`.
Each eligible comparison receives an explicit normalization decision; a shared
function reuses existing windows. Historical activations remain obligations
after later scientific revisions. The validator rejects missing earned
functions, invented activation snapshots and searches lacking a prior trigger.

## Checkpoints and completion

Flush writes at each wave, reconcile state counters against durable records,
then run:

```sh
.venv/bin/python tools/derive_outputs.py --run-id RUN001
.venv/bin/python tools/validate_run.py --run-id RUN001
```

Resolve failures before continuing. Record the checkpoint, bounded prioritized
text-request batch, stopping evidence and remaining obligations in run state and
`run_summary.md`. Complete all 22 mandatory blind windows with ordered hashes;
new eligible nodes/functions reopen their frontiers. Completion requires the
source-bound citation saturation record, earned-function windows, bridge
obligations, text dispositions, completed route audits, current exports and
successful final validation. An audited scientific premise may remain unresolved.

## Prospect delivery and explicit decisions

1. **At each validated checkpoint, update the prospect queue.** Author the
   argument for every newly assessed candidate using its existing source-linked
   reasons. State why it merits reading, remains a specific unresolved question,
   or belongs in context/outside this brief. Carry prior queue entries forward
   against current evidence and human decisions, or record the reason for their
   changed disposition. Do not regenerate a list from only the latest subset.
   Full native validation is required; settled primary/support judgment is not.
   Continue all frozen searches, text retrieval and scientific assessments.
2. **Write the argument before the tentative role.** Use the default
   `tier = profile-prospect` and `claim_review = unresolved`. Select the existing
   comparison and source assets,
   `claim_basis`, `claim_comparison_id` and `measured_outcome`. Explain the
   potential contribution, `decisive_evidence`, limitation and `human_question`,
   then set `tentative_role` to `primary`, `support` or `undetermined`.
   `prospect_relation` is `comparison-located` for located same-X→same-Y awareness
   arms/regimes or `comparison-unresolved` for a specifically plausible relation
   whose scope needs checking. Neither asserts a tested difference or adequate
   control. Missing direct testing can remain the question; known absence of
   the relevant comparison or function belongs in context. Generic unconscious
   processing cannot supply the requested awareness–use contribution.
3. **Build and inspect the current guide.** `status = provisional` permits open
   frontiers and unfinished prospect assessments; scientific records still pass
   native validation. A final guide requires completed, validated runs and all
   unchanged stopping obligations. Multi-run synthesis requires completed
   external adjudication; independent reviewers never inspect another run.
   Optional certified primary/support claims retain their stronger source and
   exact-claim reviews. Do not require them for a default prospect.

   Save the authored draft at `runs/RUN001/prospect_draft.json`. During an
   independent run, the coordinator may build a snapshot only from that run;
   `outputs/handoffs/HANDOFF_ID/` is the narrow presentation exception in
   AGENTS §2. Scientific files remain run-local.

   ```sh
   .venv/bin/python tools/postrun_handoff.py build --draft runs/RUN001/prospect_draft.json --repo-root . --output-dir outputs/handoffs/HANDOFF_ID
   .venv/bin/python tools/postrun_handoff.py validate --repo-root . --output-dir outputs/handoffs/HANDOFF_ID
   ```

   Use a new handoff ID for each snapshot and retain earlier guides as history.
   Inspect the rendered function, readout, evidence, limitation and human
   question. Source changes require updating the affected argument; unchanged
   source work need not be repeated. The builder verifies references and
   consistency, not the truth of a scientific interpretation.
4. **Deliver prospects with human acceptance pending.** This is the default
   checkpoint and final deliverable. Context is separately visible, and explicit
   previous human acceptances/rejections remain outside the first-read queue.
   Preserve the scope/reason of a rejection; only an explicit human decision
   reopens it. Model agreement or a tentative role does not establish acceptance.
   See [the handoff reference](postrun_handoff.md) for schema fields.
5. **Record only an actual explicit human decision.** Once the user accepts,
   rejects or revises placement, append the authorized event and derive the
   current accepted view. No decision is prepopulated. `--initialize-manuscript`
   is reserved for the user's already existing manuscript choices:

   ```sh
   .venv/bin/python tools/postrun_human_decisions.py append --log outputs/human_review/decision_log.jsonl --event path/to/explicit_event.json --user-decision
   .venv/bin/python tools/postrun_human_decisions.py derive --log outputs/human_review/decision_log.jsonl --out outputs/human_review/golden_primary_support.json
   ```

Before revising a rule in response to an error, check source intake, source
interpretation, claim scope and durable state. Repair those errors under the
existing science; a tentative-tier disagreement alone is not a policy failure.

Human acceptance is independent of scientific run completion. A new source
version or decision-relevant evidence uses the existing logged revision/reopening
and source-binding mechanisms; reassess the affected recommendation and derive
the current view rather than silently carrying an old promotion forward. A
different frozen scientific regime needs a new run. No human decision or reading
recommendation automatically starts a deeper or new-model sweep.

Existing explicit human decisions are displayed separately and hashed in the guide inputs. Rebuild the presentation after a human event; unchanged current source checks may be reused. Canonical handoff/human-review outputs are permitted runtime records, and remain forbidden in pristine distributions.


Scientific awareness scope: comparison-wide A continues to cover every contrasted regime for strong awareness claims and primary preservation. Ordinary unaware capacity instead requires strong exact-X unawareness in its explicit `unaware_capacity_regime_keys`, positive evidence for the whole named Y and its own interpretable statistics, without an E gate. Every regime remains inventoried and bound; local A, evidence type and objective-invisibility informativeness prevent cross-arm borrowing. A transferred regime points through `transfer_bundle_id` to a complete awareness-A bundle whose `awareness_regime_keys` explicitly includes it; shared validation requires source-critical coverage and transfer for every declared regime. Uncertified higher awareness leaves the capacity visible in ordinary capacity/supplementary exports and search activation, while main awareness-profile and certified primary/support claims retain their existing contrast-wide evidence requirements. Default prospects may retain that uncertainty with a concrete human question.
