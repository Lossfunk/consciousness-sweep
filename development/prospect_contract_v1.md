# Commissioned prospect delivery contract v1

Contract identifier: `commissioned-prospect-delivery-v1`.

This additive contract implements the author's commissioned prospect-discovery
product. It binds the scientific authority identified by
`runtime/source_reader/policy.json`, currently PROTOCOL 0.9.13. It does not amend
that frozen release, any historical run, or the registered native-certification
mode. Its deliverable is a source-grounded reading recommendation, not a complete
native experiment database or a certified empirical constraint.

## What completion means

A complete commissioned source assessment has a verified article identity, the
entire supplied source packet read with no unread exception, a valid receipt
bound to that packet and the exact reader, and an evidence-grounded decision
trail. A scientifically unresolved relation, a context-only contribution or an
author-declined paper can have a complete assessment. Unknown source identity,
partial reading and failed execution cannot.

For this commissioned product, source/claim-bound compact assessments and their
handoff are sufficient for **prospect-assessment completion**. Exhaustive physical
experiment ledgers, native comparison rows, A/E/F fields, every statistical audit,
and certified primary/support reviews are not prerequisites for delivering that
recommendation. The reading still applies the authority's scientific criteria:
same-X existence and awareness alignment, conservative downstream function,
actual awareness evidence, comparability and signal alternatives, accurate
critical results, contribution and bounded inference. A tier cannot supply a
missing premise. Preserve materially different narrower claims and negative
results when they affect the recommendation.

`prospect-delivery-complete` means all readings in the explicitly identified
commissioned set meet this assessment contract and have been delivered. It is
never an assertion that literature discovery is complete, that corpus recall has
been established, that a paper is human-accepted, or that a native scientific
export is certified. The delivery always records
`literature_sweep_complete = false`, `discovery_frontiers_assessed = false`, and
`native_scientific_exports_certified = false`. Its membership and version are
explicit; changing the commissioned membership requires a new delivery directory.

## Source and claim provenance

Keep the original sources, verified identities and version distinctions, full
extractions, unit maps and hashes. Cite decisive evidence by source asset and
unit; identify the source experiment/analysis in the claim. The execution binding
records source packet, prompt, schema, policy, code, CLI, model, effort and attempt
limits. The raw response and completed attempt receipt remain immutable.
Program-generated claim references identify exact result entries; they are not
registered comparison IDs and do not create native experiment records.

The delivery function revalidates the current binding, original response and
source packet before every reconciliation. Changed source or reader inputs
invalidate reuse of the previous reading. Partial, mismatched, absent, corrupt or
unassessed inputs produce an incomplete current delivery; prior complete snapshots
remain historical records. Delivery history is append-only and hash-chained;
`current.json` is its replaceable latest view. Hashes establish provenance and
integrity, not scientific truth or proof that the reader comprehended every page.
Snapshots are valid for their recorded inputs, not continuously monitored. Every
invocation records a reconciliation revision, including unchanged inputs; history
is intentionally an invocation audit rather than an idempotent single record.

## Human decisions and prospect presentation

Preserve the raw reader argument and disposition. Apply only explicit recorded
user decisions afterward, by canonical work identity. An author-declined paper
stays out of the new-reading queue while its source assessment and any defensible
scientific disagreement remain visible. Existing accepted support/primary roles
remain human decisions, not fresh model acceptance. A changed human ledger
requires a new reconciled delivery revision. Once configured, the prior human
ledger is reused when its argument is omitted; disappearance of a prior decision
blocks completion rather than silently restoring a declined recommendation.
Human acceptance never overrides
incomplete reading or unresolved source identity. No acceptance is inferred from
a model judgment or the act of delivery.

## Discovery and certification boundaries

Prospect selection does not decide discovery eligibility. Context or weak-control
papers may still earn citation traversal under the unchanged rules. CORE/BRIDGE
decisions require their actual experiment-level ingredients and provenance;
process-search activation requires its independently qualifying scientific
premises and the existing checks. Complete those targeted records when the route
is being used. A compact prospect flag cannot activate a process search, close a
citation frontier, discharge a missing-text obligation or satisfy a registered
stopping rule. The current native registered mode retains all its records,
validation and completion requirements.

Title/abstract screening, retrieval, source completeness, citation expansion,
process searches and stopping remain separate responsibilities. This contract
does not authorize a heuristic exclusion shortcut, a resource-based discovery
cap, or a change to scientific eligibility. A completed batch of full-text
readings is not a completed whole-literature sweep.

## Validation and change control

Use impact-based validation rather than automatically rerunning every known
paper after every change. Before deployment, identify the changed behavior and
test the exact final contract with focused positive and negative source sentinels
that exercise it, including accepted useful comparisons and known missing or
incompatible comparisons. Reuse immutable prior outputs only for behavior that
has not changed, and identify that reuse explicitly. Prompt/schema changes need
fresh evidence for affected scientific behavior; deterministic transport-only
changes can be tested against immutable outputs and execution fixtures. Broaden
checks when regressions, interacting rules or uncertainty justify it. Never select
the most agreeable output across versions or claim coverage that was not tested.

Validate delivery binding, changed-source invalidation, narrow-claim preservation,
human-decision reconciliation, incomplete execution, and completion-scope flags.
Record remaining limitations. Deployment acceptance binds the exact reader files,
this contract, scientific authority and validated settings; changing them cannot
silently inherit earlier acceptance. No full-text-only test certifies title or
abstract screening, retrieval recall or corpus-scale speed.
