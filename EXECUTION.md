# Portable execution reference

This document describes implemented command interfaces and their limits. The
scientific package under `science/` remains frozen and separate.

## Files and identities

Each new run receives a unique filesystem-safe `RUN_ID`. `init` refuses to
overwrite an existing directory. The run contains `execution_plan.json`, a
transactional `state.sqlite3` ledger, immutable job/source artifacts, deliveries
and optional exports. The executable/scientific fingerprint is checked when the
run is reopened. Preserve the release used to create a run; upgrading installed
code is not a silent migration of its evidence.

`doctor` performs no inference. Its resource inventory is a best-effort snapshot.
It distinguishes CPU allocation and container limits where observable, reports
RAM/disk and supported GPU inventory, and lists known CLI tools. It does not
infer remote GPU availability, probe a model by sending a request, or treat an
installed binary/model listing as proof of usable access.

`DISTRIBUTION_MANIFEST.json` checks static-file integrity. It is not a signature.
`verify` checks the distribution; native scientific release verification and
preflight remain separate operations under `science/AGENTS.md`.
Put mutable user configuration, intake files and their source documents under
`workspace/` or outside the repository. Verification permits `workspace/`,
`runs/`, `.venv/` and `.git/` as explicit mutable roots, and `science/runs/` and
`science/outputs/consolidated/` for the separate native workflow. Native agents
must still obey their own write-scope restrictions. Verification checks every
static scientific input and rejects unexpected files elsewhere in the package.

## Plans and resources

Use a preset for ordinary startup or pass JSON to `plan --config FILE`. The
configuration has `profiles`, `resources`, optional `workload` and `mode`:

```json
{
  "mode": "corpus",
  "profiles": {
    "title": {"adapter":"manual","model":"agent-selected"},
    "abstract": {"adapter":"manual","model":"agent-selected"},
    "rescue": {"adapter":"manual","model":"agent-selected"},
    "reader": {"adapter":"manual","model":"agent-selected"}
  },
  "resources": {
    "authorized": false,
    "cpu_workers": 1,
    "model_workers": 2,
    "retrieval_workers": 2,
    "memory_limit_bytes": null,
    "gpu_memory_limit_bytes": null,
    "max_calls": 20,
    "max_tokens": null,
    "max_spend_usd": 0,
    "max_wall_seconds": 3600,
    "max_citation_depth": null
  },
  "workload": {"logical_papers": 2000}
}
```

This is an unapproved example. Set authorizations only after the user grants
them. Automatic profiles each require `authorized: true`; resource authorization
alone does not authorize a different provider. `--config` uses the file's values,
not the convenience preset's command-line defaults. The explicitly supplied
`--mode` and `--max-citation-depth` flags override those two configuration fields.
Authorized plans require positive finite `max_calls` and `max_wall_seconds`.
Call, token and spending caps belong in `resources`; per-profile versions of
those caps are rejected because the coordinator budgets the entire run.

For discovery runs, `resources.max_citation_depth` accepts `null` (no depth cap)
or a nonnegative integer. The equivalent startup flag is
`plan --mode discovery --max-citation-depth 2 ...`. Seeds are depth 0, their
references/citers depth 1, and their eligible neighbours' references/citers
depth 2. Papers at the limit still receive normal screening and reading;
their outgoing citation obligations remain explicitly `depth-limited`.
Depth 0 therefore reads the seed candidates without fetching citation neighbours.
This operational limit does not change scientific eligibility or establish
saturation. Other work already within the allowed scope continues. Pending
depth-limited obligations prevent the normal principal-completion/mandatory
blind-lane transition; the cap does not authorize skipping a discovery route.

Process and blind queries retain their independent frozen query bounds. A work
encountered through one of those queries starts a separately labeled citation
root at depth 0; it is not claimed to be zero hops from the manuscript seeds.
Ordinary hop depth never resets when a CORE paper resets the bridge counter.
A shorter independently observed citation path can lower a paper's depth and
unlock its expansion; cached descendant links propagate that improvement without
repeating retrieval or semantic screening. The chosen limit is saved in the
immutable run plan and reused on resume. A different limit requires a separately
commissioned plan/run under the current immutable-plan contract.

Worker counts control concurrent automatic model/retrieval dispatch. CPU, RAM and
GPU fields inform planning and detect impossible declared allowances; they are
not OS memory reservations or a GPU inference scheduler. No hardware is rented
or provisioned. Measure local processing before increasing worker counts. More
workers cannot bypass a shared subscription limit.

The coordinator reserves budget before dispatch. Confirmed pre-admission denials
can release a reservation; ambiguous timeouts retain it. A completed result with
missing telemetry is recorded as completed but unmetered, with its planning
allowance retained. Missing usage is never reported as a measured zero.

`max_calls` counts admitted adapter invocations, not internal provider retries or
Claude's individual agentic turns. `max_attempts` is one per potentially admitted
logical request. Provider internal behavior is not a promise of one network
request. Claude `max_turns` defaults to three for bounded structured completion.

CLI `max_output_tokens` is an estimate/context allowance, **not** an enforced
generation cap. Authorized CLI plans reject a finite strict `max_tokens` budget;
use call/time allowances and observed token telemetry. Compatible endpoints use
their declared output token limit. Native thinking settings, prices and context
capacity must match the actual endpoint; they are not interchangeable across
providers. Estimates are not invoices or guarantees about changing subscriptions.

A worker's requested wall duration stops new scheduling. Already-admitted bounded
calls can finish after that duration. `pause` likewise preserves admitted work.
`run --watch` waits for deferred jobs to become eligible within that duration;
ordinary `run` returns when no dispatch is ready. Watch mode does not authorize
retries of uncertain admitted requests or synthesize missing scientific evidence.
The runner does not install an operating-system supervisor or arrange future
wakeups. Host uptime, sleep and quota resets belong in the agreed execution plan.

`estimate --run-id RUN_ID [--logical-papers NUMBER]` uses available run measurements
to report a forecast, with an optional target workload override.
Treat an unmeasured stage, unresolved access and unknown quota as uncertainty,
not zero time or cost. Before scaling, the supervising agent should inspect the
default 20-call commissioning run's source-grounded decision trails, compare
them with the gates, and report quality and execution findings. This is agent
work; it does not require the user to construct an evaluation set. Any available
maintainer qualification evidence must remain outside reader inputs.

## Adapter profiles

Every automatic profile pins `adapter`, `model`, provider-native `effort` where
applicable, billing route and authorization. Optional fields include
`timeout_seconds` (default 900), `max_input_bytes`, `max_output_tokens`,
`context_window_tokens`, and `qualification_status`. Oversized packets are
deferred without truncation. A model or effort mismatch observed in provider
metadata invalidates the result; unknown effective settings remain unknown.

- `manual`: immutable file exchange with the supervising agent. No additional
  model process is started. The external agent's resource use is not metered by
  this adapter; its operator must respect the agreed allowance.
- `codex`: native signed-in ChatGPT CLI with explicit model/reasoning effort,
  isolated working directory, disabled shell/web context, schema output and no
  ambient OpenAI API-key fallback. `codex_context: standard` retains the CLI's
  ordinary base instructions. Explicit `source-only-v1` replaces them with a
  short, immutable operational instruction file and disables documented optional
  tool features. The scientific task instructions remain in the complete prompt.
  The selected context and file hash are recorded; qualify the exact context.
  The recommended Codex preset selects `source-only-v1`; the profile default
  remains `standard` when no context is explicitly supplied.
- `claude`: native signed-in Claude CLI. Requires supported version, an observed
  subscription auth route and `subscription_extra_usage_disabled: true` after
  operator confirmation. Uses `--safe-mode`, `--restricted`, disabled tool/MCP
  access and explicit no-fallback settings. `--bare` is not used because it
  disables subscription authentication. Fable is excluded from this
  subscription-only adapter because headless calls may automatically bill credits.
- `command`: an explicitly selected command wrapper as an argv array, never a
  constructed shell command. Supported placeholders are `{prompt_path}`,
  `{schema_path}`, `{result_path}`, `{model}`, and `{effort}`. The wrapper receives
  the prompt on stdin and must write the JSON result to the requested path or
  stdout. Its isolation, access and billing behavior require qualification.
- `openai-compatible`: an explicitly configured JSON Chat Completions endpoint.
  Loopback may use `billing_route: local`; remote endpoints require HTTPS,
  `billing_route: api`, explicit authorization, an overall positive spending cap,
  a per-request ceiling and declared input/output token prices. Set credentials
  through `credential_env`, which contains an environment variable **name** only.
  No model, format, endpoint, redirect or billing fallback occurs automatically.

OpenClaw users can supervise manual exchange directly or provide an explicitly
reviewed command wrapper. The repository does not claim a generic OpenClaw alias
has verified source-only isolation, exact model routing or subscription billing.
Local model serving is external to this repository; discoverable GPUs do not
automatically install or start a model.

The candidate catalog is dated and advisory. Scientific qualification belongs to
an exact configuration and evidence record. `commissioning` and
`provisional-prospects` do not mean formally qualified. Have the supervising agent
run bounded source-grounded checks of selected configurations; do not require the
user to evaluate every provider. Mechanical schema success and independent judge
agreement alone do not establish reading quality or population recall.
Its evaluation dimensions concern same-X/awareness/Y fidelity, source grounding,
false exclusions and rescue, restrained null interpretation, structured validity,
completion rate and measured token, latency and spending demands. Use these as
role-specific checks, not a universal model ranking. Nominate only configurations
with an observable access route, then recommend the least costly configuration
that passes the relevant checks within the user's allowance. Unknown quality or
cost remains unknown; do not make the user benchmark the entire catalog.

The deployed reader prompt contains the unchanged accepted instruction text and
the versioned portable alignment clarification in `sweep/reading.py`. The latter
reiterates the same-X awareness requirement after a development reading failure;
it is not a new scientific eligibility rule. Qualification must cover this exact
combined prompt, schema, adapter context, model and effort. Changing a harness
base context preserves the task prompt but still requires configuration-specific
checks.

CLI input estimates bound the submitted packet, not hidden harness instructions.
Receipts mark that scope and leave unobserved harness overhead unknown. Compare
actual provider token telemetry before claiming a context optimization saved
tokens. Repeated fixed context is material across thousands of batches, but
neither input counts nor subscription usage alone establishes a dollar cost.

## Source and discovery work

Corpus intake accepts JSONL or CSV. Complete the nonmutating identity/URL
validation before allocating IDs. Preserve all rediscoveries. Full-text reading
requires a verified main article and a source-unit map. PDF text extraction does
not establish that figure pixels were examined. Record supplementary acquisition
gaps and source-identity uncertainty explicitly.

`source --paper-id ID --path FILE --reason REASON` supplies a later main source;
it creates new retrieval work with current provenance. Do not backdate it or
delete the earlier missing-text record. Use `reopen-intake` before adding a new
corpus after intake was closed.

For a main article and supplementary material, use `source --paper-id ID
--manifest FILE --reason REASON`. The JSON file contains an array such as:

```json
[
  {"path":"papers/article.pdf","role":"main"},
  {"path":"papers/supplement.pdf","role":"supplement",
   "association_reason":"Publisher-provided supplement for this article"}
]
```

Corpus `provided_paths` accepts the same entries. Preserve the explicit
association reason for each supplement. The coordinator copies supplied bytes
into immutable intake assets and retrieval checks their expected hash; changing
the original local file does not change an already imported source version.

With `mode: discovery`, `discovery-init` creates the frozen principal inputs.
The source adapters use OpenAlex and Europe PMC with the frozen source fallback
policy; citation coverage errors are not empty citation lists. Set
`OPENALEX_API_KEY` through the environment when required by that provider. The
key is not part of run records. Search results are immutable ordered snapshots;
resume must reuse the same request and hash, never silently rerank or extend it.

The source workflow separately tracks native eligibility tasks. `native-work`
returns the next required task and submission contract. `native-submit` records
typed, source-located judgments and derives route decisions using the frozen
scientific predicates. Source, bibliography and citation-wave resolution tasks
also use this channel. Reader prospects alone cannot activate citation recursion
or independently earned process searches.
The supervising agent must service these tasks through the native handoff
commands. Automatic reader workers do not complete all native scientific
judgments on their own.

Mandatory blind windows remain required after principal satisfaction. Eligible
one-hop bridges and new independently earned functions create obligations under
the unchanged rules. Resource limits checkpoint execution; they do not change
window sizes, source families, inclusion criteria or scientific stopping rules.

## Command summary

| Command | Purpose |
|---|---|
| `doctor`, `plan`, `init` | Inspect, agree resources, initialize without overwriting |
| `ingest`, `close-intake`, `reopen-intake` | Manage explicit corpus intake |
| `run`, `run --watch`, `run --local-only` | Advance stages, wait within a bounded allowance, or disable automatic model dispatch |
| `work`, `submit` | Lease and publish ordinary agent judgments |
| `discovery-init`, `native-work`, `native-submit` | Initialize discovery and resolve native route tasks |
| `status`, `estimate`, `audit` | Inspect progress, report measured forecasts and schedule required screening audits |
| `validate` | Check run storage, source hashes, recorded outputs and budget consistency at a quiet checkpoint |
| `source`, `human-decision` | Add a later source or record explicit human vetting |
| `deliver`, `export` | Publish prospects and operational provenance snapshots |
| `pause`, `resume`, `recover` | Graceful stop, clear stop request, reconcile a proven dead owner |
| `retry` | Explicit fresh attempt for a verified terminal model failure, retaining its prior receipt and budget charge |
| `verify`, `package` | Verify or build an isolated static distribution |

Use `python -m sweep COMMAND --help` for required arguments. `--root DIRECTORY`
is a global option placed before the command; run directories go beneath it.

`retry --run-id RUN_ID --job-id FAILED_JOB_ID --actor ACTOR --reason REASON`
creates one new immutable work unit with exactly the failed job's evidence,
model, effort and execution settings. It requires a terminal receipt: a CLI child
must have exited or been killed and waited for, or the HTTP request must have
returned locally. The latter does not prove that remote computation stopped.
The original result, failure and reservation remain auditable and charged;
there are no automatic uncertain retries or refunds. Another request must fit
the existing call allowance, and unresolved usage still blocks token/cost-capped
dispatch. The command is idempotent for one parent; if its child fails, that
child needs a separately reasoned explicit retry. Failed ancestors cease to
block completion only because their linked successor now represents the work;
historical failures remain counted and checked. A running request, missing
terminal proof, changed inputs/settings, or a failed job with existing dependent
jobs is refused. Resolve those cases explicitly rather than editing the queue.

## Completion and logs

After manual submissions and their queued follow-up work are handled, run
`validate --run-id RUN_ID`, inspect its `ok` and errors, then `deliver --run-id
RUN_ID` and `status --run-id RUN_ID`. Do this when workers are idle: concurrent
changes invalidate the validation checkpoint. A later scientific or operational
state change makes the checkpoint stale and requires another validation before
reporting operational completion. Files modified outside the coordinator also
require a fresh validation; the lightweight status check does not rehash every
file.

`delivery/index.html` provides a browser-readable queue and links to
versioned paper pages linked from that index. These pages show stored claims, their source
locations, alternatives, reading gaps and the human decision separately. They do
not independently classify papers. `delivery/prospects.jsonl` retains all reader
assessments, including context and human-declined records; the queue indicator
selects items for review. Validation details are in `delivery/validation.json`.

Operational events record discovery provenance, reasons, source identity,
requested/observed settings, hashes, usage when available, failures, reservations
and transitions. Raw credentials and private model reasoning are not intentional
log outputs. Large source packets are immutable files rather than repeatedly
copied bookkeeping in the model's answer.

`commissioned-corpus-assessed` concerns the closed supplied corpus and its current
operational work, with a current successful operational validation. It does not
mean complete literature coverage or native
scientific certification. Partial source readings, unresolved access, failed jobs
and native frontier obligations remain visible. Native scientific completion
requires `science/AGENTS.md`, all its run records and its validator; the portable
ledger intentionally reports native certification as false.

The distributed repository excludes development judgments and evaluation answer
keys. Maintainer tests and the recipient's bounded commissioning can substantiate
mechanical and semantic claims separately. Claude and custom endpoint integrations
must not be described as live-verified where only simulated transports were used.

## Revision 0.9.14 operational contract

Title output is just a decision and a paper-specific reason; uncertainty advances.
Abstract output adds the exclusion basis. Every consequential scientific exclusion
receives a fresh source-only strongest-profile assessment; the first verdict and
feature assertions are withheld. A rescue that read the abstract completes that
stage. Clear outside-scope exclusions are independently audited in cumulative
source/stage cohorts: the ten lowest stable source-bound
hashes, or all papers in a smaller cohort. A miss reopens the remaining current
exclusions in that cohort. This sample does not estimate corpus recall.

Within available worker capacity, ready reader jobs precede rescue/audit, abstracts and titles; ready acquisition precedes more citation fetching. This scheduling order lets the pipeline finish paper assessments while a large title backlog remains, without excluding or changing any paper. Every acquisition job binds an immutable source manifest and generation. An
identical attachment is idempotent. A changed abstract reopens a screening-only decision; richer metadata does not replace an existing full-paper reading. A changed acquisition identity creates explicit source follow-up work. Older results remain in history but cannot
replace a newer generation or a richer current stage. `source-retry --run-id ID
--paper-id ID --reason REASON` authorizes a new acquisition attempt. It does not
silently retry a model call. Source-verified means bibliographic identity and
extraction were checked; it does not certify complete article text or figure
inspection. Acquisition gaps and individual claim dispositions appear in delivery.

Keep uncertain preprint/published matches separate and preserve supplied version
relations/publication status. Use the source text to resolve identity. Never count
unresolved copies as independent corroboration or reuse decisions across changed
versions just because titles are similar.

Use `native-list --run-id ID --include-deferred` to inspect outstanding work, then
`native-work --run-id ID --owner WORKER --lease-seconds 900` to reserve distinct
work. Without an owner, native-work is an inspection only. Carry the returned
owner/token as `native_lease` in submissions. `native-defer --run-id ID --task-id
TASK --actor WORKER --reason REASON --lease-token TOKEN --delay-seconds 300`
releases that reservation and lets other tasks proceed. Lease expiry alone is not
proof that a worker died. Resolve DOI-less parents through the returned identity
lookup task: inspect candidate bibliography and submit a verified service identity
with evidence, or retain ambiguity. A citation CORE judgment can be recorded
while the separate process-search assessment remains unresolved.

Inconsistent source responses are quarantined, never converted to zero yield.
Use the returned source task's `restart-citation-window` action to create a new
recorded coverage generation; prior pages and encounters remain in history.
Report total hits, returned records and ranked truncation independently. A full
40-record blind window or 50-record earned-Y window is not source exhaustion.
The fourteen QREV6 families and their rationale are in science/queries.md.

A failed operational integrity report blocks execution and trusted delivery
until repaired and successfully revalidated. Deadlines propagate to model and
retrieval workers, with a cleanup allowance inside the session budget. A killed
possibly admitted call retains its reservation and unknown cost; no automatic
model retry follows. If time is insufficient for validation/delivery, record a
deferred checkpoint and keep the prior delivery. OS scheduling and durable disk
flushes can add small shutdown latency; the deadline does not allow workers to
drain their full original multi-minute timeout.

## Prepared one-hour commissioning test (not automatically launched)

The prospective test uses this exact verified distribution with the accessible
Codex profiles selected at startup (reader/rescue effort explicitly xhigh), at
most three concurrent model workers, two retrieval workers, 24 model calls, and
3,600 seconds total including setup and checkpointing. Recheck account capacity
before dispatch; reduce concurrency if necessary without changing scientific gates.
No paid-API fallback is implicit. The commissioning record must carry a single
wall-clock deadline across repeated runner/native-work invocations; pass only the
remaining allowance to each runner, stop dispatch by minute 50, and reserve the
last ten minutes for active-call termination, validation and the report. A resumed
session does not reset this test's total clock.

Targets, decided before reading outcomes:

1. Verify the package, inventory host/access, initialize the 60 bibliography
   seeds, and exercise both citation directions and a DOI-less identity task.
2. Reach at least one real two-hop citation path using source-grounded native
   decisions, with a commissioned citation depth of two. Screen/read boundary
   papers normally; retain further expansion as depth-limited.
3. Exercise title, abstract, independent rescue, retrieval, full-paper reading,
   native eligibility and human-readable delivery. Aim for four to six complete
   accessible PDFs chosen by ordinary durable priority/order, not anticipated
   inclusion. Report the exact units actually read, claims, evidence and limits.
4. In separately labeled source diagnostics, inspect at least one revised pain,
   hedonic, motivation and unrestricted query on each source. Do not claim those
   diagnostic windows fulfilled the main run's blind-lane obligations. Retain
   hit counts, truncation, duplicates and obvious off-topic fractions.
5. Reuse the offline finite-graph regression for principal saturation, blind-lane
   entry, new CORE/earned-Y reopening and resaturation. A depth-limited hour cannot
   legitimately force those transitions in a live graph.
6. Interrupt/resume once at a safe checkpoint, verify immutable reuse and current
   source bindings, then validate and deliver. A target not reached within budget
   is reported as untested; an empty queue or timeout is not a scientific success.

The maintainer's offline receipts establish software behavior. The one-hour test
will add live transport, retrieval and actual paper-reading evidence. It is a
bounded diagnostic, not a completed registered sweep or automatic authorization
for the multi-day run.

## Portable r7 execution repairs

The scientific package remains 0.9.14. Frozen discovery anchors retain their
citation-source role on metadata rediscovery; new URLs alone do not bypass
semantic screening. Seed titles and metadata updates use bounded batches. A
verified fuller source retires stale lower-stage screening before a model call.
PDF subprocesses preserve the selected virtual-environment interpreter.

Before a native experiment-group submission, allocate its stable identifiers:

```sh
python -m sweep native-allocate --run-id RUN --paper-id P000001 \
  --experiment-key "experiment-1" --comparison-key "focal-x-to-y" \
  --actor WORKER --reason "One physical experiment and its focal comparison"
```

Reuse the returned IDs for the same physical experiment/comparison. Allocation
is transactional and idempotent; it does not supply an assessment, imply a
completed comparison, or activate a process search. Native submission rejects
unreserved IDs. Process eligibility may remain explicitly unresolved while
source-grounded citation eligibility is recorded.

Review/theory narratives about unavailable originals remain contextual leads;
the originals must supply empirical prospect evidence. This applies the existing
paper-by-experiment scope and does not change A/E/F or statistical gates.

The final r8 packaging adds durable `retrieval_deferred` events containing the
attempt receipts and source-manifest binding before a transient source request
is requeued. The reader prompt, profiles, schemas, science and scheduling rules
are unchanged from the live-tested r7 candidate. This preserves the cause of a
failed public-source request for the supervising agent's recovery work.

## Portable r9 negative-finding clarification

The source-reader wrapper now explicitly applies PROTOCOL §3.2 when a negative
comparison has an uninterpretable critical estimate, analysis population or
coverage: retain the performed test as unresolved, rather than call it supporting
negative evidence. This does not demand equivalence, Bayesian analysis or
primary-level control from a prospect. Other informative comparisons in the
same paper remain independently eligible. The scientific package, accepted
reading instructions, output schema and discovery rules are unchanged.

## Portable r10 human-decision validation

Operational validation requires an explicitly attributed human decision to use
one of the CLI's existing values: `accepted-support`, `accepted-primary`,
`declined`, or `pending`. Malformed values fail validation before delivery,
preventing a rendering failure or an ineffective queue exclusion. The reader,
scientific inputs and all model execution settings are byte-identical to r9.

## Reader clarification revision r11

The reader now explicitly integrates supporting and contrary premise evidence
across supplied sources before selecting a claim. It distinguishes evidence that
is insufficient alone from evidence that cannot transfer, and records the joint
awareness judgment. Every reformulated claim must independently locate evidence
for its X, awareness contrast, downstream use and surviving contribution. A
construct mismatch or uninterpretable selected comparison cannot be repaired by
caveats or a low-priority label. These instructions apply existing PROTOCOL
Sections 1, 2.1, 2.4, 4.3 and 12; qualitative evidence, reasonable transfer,
weak-control prospects and genuinely uncertain aligned comparisons remain
admissible.

Qualification must bind the exact prompt, schema, source packet and response.
Source fidelity and correct execution do not establish prospect usefulness;
partial evidence integration or unresolved acceptance judgments must not be
counted as scientific passes. Evaluation material and expected judgments remain
outside the distributed reader inputs. The frozen scientific package and output
schema are unchanged.

## Reader clarification revision r12

Assess signal control where the focal information is presented, generated or
acquired, even when its use is tested later. Matching later probes cannot match
earlier information retrospectively. A different function's diagnostic pattern
does not automatically justify a separate prospect; a supporting observation may
instead remain context for the accepted mapping. Coherent tested functional
relations remain intact. This clarifies the existing same-X/same-Y contribution
and signal-control rules without changing scientific inputs or the output schema.
