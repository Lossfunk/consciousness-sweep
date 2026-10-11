# Prospect handoff reference 0.5.0

This is the recommendation contract for **0.9.13, frozen**. Use [the run
quickstart](run_quickstart.md) for discovery, source assessment, checkpoint
prospect delivery and explicit human decisions. The coordinator must update the
prospect queue at each validated checkpoint and deliver it as the default final
output. It reuses current scientific records, never changes scientific codes or
infers human acceptance, and makes no exhaustive-recall claim.

An authored draft names a `handoff_id`, fixed `created_at`, `status` (`final` or
`provisional`), input runs and one item per logical work. Use the default
`tier = profile-prospect`. Retain existing queue entries against current sources
and explicit human decisions, or record why their disposition changed; do not
silently lose earlier entries when authoring the next snapshot. Account for each
newly assessed candidate in its existing source-linked relevance reasons.

Write a compact argument before any tentative role:

- **Contribution:** what the paper might add to the awareness–use profile;
  identify X, conservative plausible Y and measured outcome separately.
- **Decisive evidence:** the actual experiment, comparison or result and source
  location that makes this a prospect; never restate the desired conclusion.
- **Limitation:** the remaining alternative or missing premise, explaining
  whether it narrows the claim, weakens confidence or leaves relevance uncertain.
- **Human question:** the concrete matter the author's reading should resolve.

Reuse `claim`, `manuscript_contribution`, `reason`, `limitation` and source fields.
The prospect adds `decisive_evidence` and `human_question`, then
`tentative_role = primary|support|undetermined`. The role is provisional and does
not gate relevance. `claim_basis`, `claim_comparison_id` and `measured_outcome`
select and describe the existing scientific record; no second classification
pipeline or numerical relevance score is created.

Set `prospect_relation = comparison-located` when the sources locate awareness
arms/regimes concerning the same X and Y. It does not assert that the difference
was tested or the awareness/signal controls are sufficient.
`comparison-unresolved` retains a source-grounded plausible relation whose
awareness, function or analysis scope is the concrete human question. A missing
direct test alone is not exclusion when the relevant arms exist. Do not claim a
difference from separate significance labels, or claim equivalence without its
required evidence. Uncertain awareness transfer, weak signal control, plausible
but unclear function or incomplete critical statistics can remain prospects.
Known absence of the relevant awareness comparison or downstream use belongs in
context. Ordinary unconscious processing alone does not establish relevance to
this queue; scientific capacity exports and searches remain unchanged.

For default prospects and conditional questions, set `claim_review = unresolved`
and supply all four prospect fields. This means the human-vetting claim is
provisional even when its comparison is located. Existing claim bases describe
the proposed contribution, not an established finding. A comparison with
`F-ambiguous`/`function-unclear` or `A-absent` uses `comparison-unresolved`;
uncertain transfer can remain `comparison-located` when the awareness relation
is otherwise located. E strength and missing direct testing do not alone
change that relation. Known nonhuman/out-of-scope population, absent awareness
contrast, incompatible comparison or nonfunctional/effect-only Y cannot be
restated as a prospect. Optional certified primary/support items use their
existing confirmed review fields and omit the four prospect fields. Context
has `first_read = false`.

Every prospect references its current comparison and verified source; the
selected comparison belongs to the paper and its referenced comparison IDs.
Native validation still applies. A default prospect does not require confirmed
scientific-promotion or exact certified-claim reviews merely to be recommended.
If its underlying current record makes a strong scientific claim, that claim's
normal independent checks still apply. Unfinished interpretation is represented
honestly rather than promoted to pass a check.

Optional stronger recommendation paths remain available:

- **Qualified primary prospect:** an awareness-linked change uses the strong
  awareness-constraint route. Preserved capacity needs positive exact-X whole-Y
  unaware functioning plus an actual awareness nondifference/null test. Its
  descriptive branch can retain weak E with strong A/F and interpretable,
  adequately supported or nonfatally qualified evidence, without calling this
  equivalence or established invariance.
- **Valuable support:** a bounded empirical premise from a completed human,
  comparable same-function awareness test, meaningful Y, interpretable direct
  result and adequate/nonfatally qualified statistics. Weak E or awareness
  transfer can remain limitations. These certified paths retain their existing
  independent source and exact-claim reviews.
- **Conditional check/read:** the existing specific-question path remains
  available with the same four prospect fields and unresolved review; it need
  not be used instead of a plausible default prospect.
- **Backup context:** useful narrower findings, unaware-only capacities and
  methods. **Unresolved source request:** the existing missing-text obligation.

All items explain their potential contribution and evidence limitations; no
manuscript example supplies an expected classification. The existing
`evidence_level_comparison` may identify a tentative comparison, or explain
what cannot yet be compared without inventing a baseline. Primary/support
placement can remain undetermined. Context stays separately visible.

For `backup-context` only, an item may cite `experiment_group_ids` instead of comparisons. Each group must belong to that paper, have completed pre-atomization assessment, and have current disposition `support-only` or `no-qualifying-comparison`. A current verified asset and source-located claim review remain required. This preserves narrower findings without inventing comparison rows or presenting group-only evidence as the requested awareness comparison. Default prospects, certified primary/support and conditional items require a selected comparison. The group table remains in the input hash manifest.

For a **final** handoff, each run must be complete and pass its own frozen `tools/validate_run.py`; the CLI invokes it. A provisional handoff can describe open discovery frontiers and unfinished prospect judgments. Native scientific records and the checks applicable to each recommendation type must validate. The CLI invokes the native validator for both statuses. Multiple runs require a completed external adjudication manifest with `status: "complete"`, matching `input_run_ids`, and a `work_map` from each recommended `RUN_ID:PAPER_ID` to an adjudicated canonical logical-work key. The handoff checks coverage and deduplication; it does not perform adjudication or merge independent records.

Save the authored single-run draft at `runs/RUN001/prospect_draft.json`.
During an independent run, only its coordinator may write the presentation
snapshot under `outputs/handoffs/HANDOFF_ID/`; AGENTS §2 grants this narrow
exception while scientific records stay run-local and other runs and
`outputs/consolidated/` remain inaccessible.

From the released package root, at each validated checkpoint (or after completion and any required multi-run adjudication):

```sh
.venv/bin/python tools/postrun_handoff.py build \
  --draft runs/RUN001/prospect_draft.json \
  --repo-root . \
  --output-dir outputs/handoffs/HANDOFF_ID

.venv/bin/python tools/postrun_handoff.py validate \
  --repo-root . \
  --output-dir outputs/handoffs/HANDOFF_ID
```

The new directory contains `authored_input.json`, `reading_handoff.json`, `reading_guide.md`, and `input_manifest.json`. Validation rechecks current run/source hashes and regenerates both output views to catch count or text drift. Build requires an absent or empty output directory under `outputs/handoffs/`; it cannot write into a run directory or `outputs/human_review/`. Source interpretation remains an authored semantic review: a hash and page pointer establish provenance, but do not prove a scientific claim.

The [human-decision utility](../tools/postrun_human_decisions.py) records the final authorized step using append-only events conforming to [its schema](../schemas/postrun_human_decision.schema.json). An event with `origin=user` requires an actual explicit user decision and `--user-decision`. `--initialize-manuscript` is only for the user's already existing manuscript choices. The handoff builder never imports or invokes this utility. The recommendation can be complete while **human acceptance** remains pending; human acceptance is independent of scientific completion. Record an actual acceptance, rejection or revised placement, then derive the current view rather than importing an old recommendation as a decision.

```sh
.venv/bin/python tools/postrun_human_decisions.py append \
  --log outputs/human_review/decision_log.jsonl \
  --event path/to/explicit_event.json --user-decision

.venv/bin/python tools/postrun_human_decisions.py derive \
  --log outputs/human_review/decision_log.jsonl \
  --out outputs/human_review/golden_primary_support.json
```

No manuscript baseline or user decision is prepopulated in a release. The current view is derived only from explicit events, and handoff validation never writes it.

## Optional certified recommendations and scientific promotions

Every optional certified primary and valuable-support item needs a current separate source check,
including weak-E/transfer-risk support. The same existing scientific review
events are used; the scientific export and search predicates are unchanged.
After those source facts are recorded, the independent checker reviews the
exact proposed claim, outcome, result, scope and limitation and appends a
`scientific_reading_claim_review` event as specified in `AGENTS.md` §7. Use
`scientific_reading_claim_binding` from `tools/execution_contract.py` to bind
that item and current typed evidence. The generated `source_review` receipt
names the actual comparison and claim review events and reviewer. Authored
`verified` or a reviewer name without this bound event cannot promote an item.

The source check distinguishes an actual awareness comparison from a function
test across objective-discrimination groups whose awareness states remain
unestablished. The latter actual result may remain a default unresolved prospect when an awareness interpretation is source-grounded and the question is concrete; otherwise it stays context. This does
not exclude legitimate qualified support merely because awareness transfer or
first-order signal matching is uncertain. A claim change needs a new exact
check; an unchanged verified source requires no redundant full-paper reading.

The guide reads existing explicit human decisions from the canonical
`outputs/human_review/decision_log.jsonl`, shows their recorded role/version,
and leaves accepted or declined works outside the first-read queue. Preserve
the scope and reason of any decline; only an explicit human decision reopens
it, even when a source version changes. It never
appends a human event or infers an acceptance. A human decision changes the
presentation input manifest; rebuild the guide while reusing current science
and source checks. Earlier guides remain immutable history.

The exact claim receipt also binds the authored why-read and redundancy text. For combined runs, human history follows only aliases established by the adjudication manifest and uses the latest append-order event across those keys.

A separately stored decisive supplement is registered and directly linked as an auxiliary source under AGENTS §9.3. Its verified ID belongs in the independent source reading and exact claim checks; a free-form source pathname does not bind its bytes.


Scientific awareness scope: comparison-wide A continues to cover every contrasted regime for strong awareness claims and primary preservation. Ordinary unaware capacity instead requires strong exact-X unawareness in its explicit `unaware_capacity_regime_keys`, positive evidence for the whole named Y and its own interpretable statistics, without an E gate. Every regime remains inventoried and bound; local A, evidence type and objective-invisibility informativeness prevent cross-arm borrowing. A transferred regime points through `transfer_bundle_id` to a complete awareness-A bundle whose `awareness_regime_keys` explicitly includes it; shared validation requires source-critical coverage and transfer for every declared regime. Uncertified higher awareness leaves the capacity visible in ordinary capacity/supplementary exports and search activation, while main awareness-profile and certified primary/support reading claims retain their existing contrast-wide evidence requirements. Default prospects may retain uncertainty with a concrete question.
