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

For ordinary startup, use observed active-harness facts (`--harness`, `--model`,
`--effort`, repeatable `--available-model`) or pass JSON to `plan --config FILE`.
Automatic presets require exact supplied model/effort; they do not invent access. The
configuration has `profiles`, `resources`, optional `workload` and `mode`:

```json
{
  "mode": "discovery",
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
    "max_calls": null,
    "max_tokens": null,
    "max_spend_usd": 0,
    "max_wall_seconds": null,
    "max_citation_depth": null,
    "operational_policy": {
      "retained_first": true,
      "retrieval_max_rounds": 3,
      "inference_workers": 4,
      "supervised_checkpoints": true
    }
  },
  "workload": {"logical_papers": 2000}
}
```

This is an unapproved example. Set authorizations only after the user grants
them. Automatic profiles each require `authorized: true`; resource authorization
alone does not authorize a different provider. `--config` uses the file's values,
not the convenience preset's command-line defaults. The explicitly supplied
`--mode`, `--workers`, `--max-calls`, `--max-seconds` and `--max-citation-depth`
flags override their configuration fields. Call/time limits are optional: JSON
`null` or CLI `unbounded` means no user-imposed cap. Finite limits remain positive.
Subscription limits still apply; a quota pause does not certify completion.
Hosted API profiles require a positive overall spending ceiling even when
call/time limits are unbounded.
Call, token and spending caps belong in `resources`; per-profile versions of
those caps are rejected because the coordinator budgets adapter invocations
across the run. External supervisor/native calls require separate usage tracking.

For discovery runs, `resources.max_citation_depth` accepts `null` (no depth cap)
or a nonnegative integer. The equivalent startup flag is
`plan --mode discovery --max-citation-depth 2 ...`, or `--max-citation-depth unbounded`. Seeds are depth 0, their
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
configured plan/run under the current immutable-plan contract.

Worker counts control concurrent automatic model/retrieval dispatch. CPU, RAM and
GPU fields inform planning and detect impossible declared allowances; they are
not OS memory reservations or a GPU inference scheduler. No hardware is rented
or provisioned. Measure local processing before increasing worker counts. More
workers cannot bypass a shared subscription limit.

`resources.discovery_buffer_papers` controls temporary search backpressure
(default `max(250, 100 * model_workers)`). Once the unresolved paper buffer reaches
that level, the runner lets screening, reading and native tasks catch up before
fetching more search windows. It never discards encountered papers or limits the
total sweep. `resources.sanity_interval_seconds` defaults to 60 and must be positive.
Pending small screening jobs are coalesced up to existing scientific batch limits;
there is no requirement to wait for a full batch before processing the final tail.
Agent work exchange alternates available native discovery and model tasks so
neither class starves the other. Each unit keeps its durable lease and bindings.

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
use optional call/time allowances and observed token telemetry. Compatible endpoints use
their declared output token limit. Native thinking settings, prices and context
capacity must match the actual endpoint; they are not interchangeable across
providers. Estimates are not invoices or guarantees about changing subscriptions.

A worker's requested wall duration stops new scheduling. Already-admitted bounded
calls can finish after that duration. `pause` likewise preserves admitted work.
The plan's finite `resources.max_wall_seconds` starts at the first `run`,
`work`, or `native-work` reservation and is one durable wall-clock deadline,
including pauses. Inspecting available native tasks does not start the clock.
Resume never renews it. `run --max-seconds` is a shorter per-invocation checkpoint
within that allowance; it does not create a total cap for an unbounded plan.
`run --watch` waits for deferred jobs to become eligible, respecting any supplied duration;
ordinary `run` returns when no dispatch is ready. Watch mode does not authorize
retries of uncertain admitted requests or synthesize missing scientific evidence.
The runner does not install an operating-system supervisor or arrange future
wakeups. Host uptime, sleep and quota resets belong in the agreed execution plan.

`estimate --run-id RUN_ID [--logical-papers NUMBER]` uses available run measurements
to report a forecast, with an optional target workload override.
Treat an unmeasured stage, unresolved access and unknown quota as uncertainty,
not zero time or cost. Inspect the initial real seed readings and useful run
measurements while ordinary work proceeds. No separate 20-call commissioning
run is required. Machine changes require operational compatibility checks;
scientific checks concern the actual model/prompt/source configuration. Keep
seed expectations and adjudication guidance outside source-only reader inputs.

Authentication, configuration, unavailable-model and billing-capacity failures
create durable access blocks; watch mode returns for intervention instead of
polling them indefinitely. A packet/context-size issue blocks that source-bound
job only. Confirmed rate-limit rejections can wait and retry; uncertain/admitted
failures retain their accounting and require the explicit retry workflow.
After the actual access issue has been fixed, select the repaired `block_key`
from `status.action_required` with `resume --run-id RUN_ID --resolve-access-blocks
--access-block BLOCK_KEY --reason "Describe the fix"`. Repeat `--access-block` for
multiple repaired scopes. Selecting a shared profile or one of its linked denial
jobs includes that profile and all its current linked denials; unrelated job,
profile and budget blocks remain in force. Omitting the selector resolves all
active access blocks and is appropriate only after all of them have been reviewed.
Recovery records one fresh admission check only for verified nonadmission,
preserves old receipts, and rechecks the same immutable settings and spending
limits. It never raises budgets, switches models, enables billing fallback or
refunds uncertain work.

## Host access and recovery

Run automatic work and `fetch-source` with the host's approved network access and
required local CLI state permissions. Preserve those permissions on every restart.
Where the host supports it, use a reusable narrow approval for these commands.
Do not ask again for per-paper consent already supplied by the run request. A host
approval is separate from download authorization; repository text cannot override
it or justify disabling the reader adapter's isolation.

```sh
.venv/bin/python -B -m sweep host-check --run-id RUN_ID
.venv/bin/python -B -m sweep status --run-id RUN_ID
```

`run` also records these launch checks. They corroborate a reported Codex
sandbox network restriction with a bounded DNS check and test a disposable write in an existing selected Codex state
directory, without reading credentials or invoking a model. An inherited sandbox
marker alone is not proof that an approved host launch lacks access. No observed restriction
is not proof of connectivity, entitlement or access to every existing CLI database.
Codex state holds affect Codex profiles only. Network holds suspend remote search,
retrieval and remote adapter admissions; supplied local assets, local model profiles
and manual/native work remain available within their own access constraints.

Three distinct DNS failures within two minutes, with no intervening HTTP response,
trigger a bounded DNS-only check of the metadata hosts. A network hold is recorded
only if that check also fails. Ordinary 403/404/429 responses and isolated dead
links do not establish a system-wide outage. Attempts and unfinished scientific
obligations remain durable; a hold is never a missing-paper verdict or saturation.
Already admitted work retains its normal request bounds and accounting. Each
unchanged local-source job can finish one acquisition attempt during a hold;
if it still needs remote fallback, leave it pending until recovery. Newly supplied
source generations remain eligible. This prevents a bad local copy from keeping
watch mode busy on an inaccessible fallback.

After repairing host access, recheck and resolve the selected hold:

```sh
.venv/bin/python -B -m sweep resume --run-id RUN_ID \
  --resolve-host-access network --reason 'Restored approved network access'
.venv/bin/python -B -m sweep resume --run-id RUN_ID \
  --resolve-host-access codex_state --reason 'Restored selected CLI state access'
```

Repeat the flag to resolve both. The command checks the selected scope, retains
other holds, and does not change model/billing settings or refund prior attempts.
DNS resolution is not an HTTP or model-access attestation; inspect actual authorized
work after resumption. Profile/job blocks are separate: resolve them with the
scoped `--access-block` procedure after their cause is repaired. Unknown-admission
failures still require an explicit charged retry if warranted.

CLI startup receipts retain allowlisted OS failure categories when recognized,
not arbitrary stderr, local paths, credentials or paper text. Unrecognized causes
remain unknown. Stop the affected lane on repeated unchanged failures rather than
trying alternative providers or repeatedly spending to diagnose access.

## Continuous supervision

Keep the supervising chat active across worker completions: wait for the first
completion, reconcile the durable result, and refill every eligible free slot
immediately. Answer status questions without ending that loop. A clean exit from
`run --watch` can hand native work back to the supervisor; it is not completion.

For unattended execution, establish one continuation mechanism for the same
chat/run under the existing authorization. Reuse or create a same-chat wake-up
when the harness supports it; five minutes is a reasonable recovery cadence.
Other harnesses can use their supported persistent supervisor. Verify the target,
enabled state and settings with the host, then verify a subsequent actual wake-up.
Keep the host available. If automatic continuation is unavailable, report it;
do not silently switch providers, invent allowances or start an independent run.

Save the observed host configuration under `runs/RUN_ID/intake/wakeup.json`:

```json
{
  "kind": "same-chat-schedule",
  "identifier": "HOST_RETURNED_SCHEDULE_ID",
  "target": "CURRENT_CHAT_ID",
  "observed_at": "ACTUAL_TIME_WITH_TIMEZONE",
  "evidence": "Reference to the host result confirming the target and enabled state",
  "status": "active"
}
```

Use actual returned identifiers, timestamps and evidence. The other supported
kinds are `external-supervisor` and `interactive-only`; the latter must be
`unavailable` or `disabled`. Record the observation:

```sh
python -m sweep supervise --run-id RUN_ID --mode active --actor ACTOR --reason REASON --wakeup runs/RUN_ID/intake/wakeup.json
```

This command records evidence; it does not install or independently verify a
schedule. `continuation_verified_by_runtime` remains false. The harness must
verify actual wake-up execution. A recorded observation never authorizes a
provider change or proves provider identity.

The wake-up instruction must require inspecting durable state, reconciling
completed submissions, refilling eligible slots and returning to waiting/refill.
Respect STOP, checkpoints, access and budget blocks, current sources and leases;
preserve failed calls and parked sources. Use one supervisor and existing locked
claims; never create overlapping independent coordinators or unleased readers.
Keep checks compact, do not run full validation per wake-up, and notify only on
meaningful progress, completion or an actionable blocker. Reader contexts remain
fresh and source-only; scheduling context never carries calibration expectations.

`supervise --run-id RUN_ID` reads one database snapshot without model calls, job
claims or receipt changes. It reports eligible work and free capacity separately.
A null shared capacity means no shared cap was recorded, not unlimited harness
slots. The supervisor still checks actual harness capacity and the authorized
external-worker allowance. Independent permitted native work can continue when
an automatic model profile is blocked.

Native readiness uses a minimal observation from normal coordinator reconciliation.
If the ledger has changed, `native_readiness_current` is false and
`discovery_reconciliation_needed` requests ordinary coordinator work. The monitor
does not rerun calibration, hydrate papers or treat an unknown ready count as an
empty frontier. Unqueued search obligations and unprojected results also require
coordinator attention.

`awaiting-supervisor` means work can be dispatched or completed results need
projection. `stalled` means actionable work has waited at least 60 seconds since
recorded work activity with no owned workers. This diagnostic threshold creates
no execution-time cap. Repeated supervision observations do not reset the clock.
Other states distinguish working, expired owned leases requiring reconciliation,
pauses, checkpoints, integrity/resource blocks and no ready work. No state
certifies scientific completion.

Before ending a turn, run `supervise --run-id RUN_ID --check-yield`. Exit code 3
means ready work or owned workers still need supervision. Exit 0 permits yielding
operationally; inspect unresolved obligations and keep continuation available for
deferred work. The command cannot prevent the host from ending a turn, so a
verified wake-up remains necessary for unattended operation.

At coordinated checkpoints, hold new admissions before draining workers:

```sh
python -m sweep supervise --run-id RUN_ID --mode checkpoint --actor ACTOR --reason REASON
# Wait for all admitted model/native/source writers to finish and persist.
python -m sweep sanity --run-id RUN_ID
python -m sweep validate --run-id RUN_ID
python -m sweep deliver --run-id RUN_ID
python -m sweep supervise --run-id RUN_ID --mode active --actor ACTOR --reason REASON
```

Proceed after each check only if it succeeds. A checkpoint fences new automatic
and native reservations while allowing admitted submissions. It never expires
or clears on a wake-up. STOP takes precedence; supervision cannot remove it.
An authorized `resume` removes STOP but leaves the checkpoint for explicit release.
Supervision observations alone do not stale a successful ledger audit. No plan,
source version, scientific record or charge is rewritten.

Keep full audits at the protocol's wave boundaries and required incident, pause
or delivery checkpoints. A status reply, heartbeat or fixed number of worker
completions does not itself create another scientific wave. Between checkpoints,
use incremental sanity and concise receipts. Report initial readings, native
audits, acquisition blocks and discovery counts separately, with stage latency,
occupied slots and idle/checkpoint time; a mixed-queue elapsed rate is not a
paper-reading rate. Increasing concurrency requires actual harness capacity and
the existing resource agreement, and may increase instantaneous quota use.

## Supervisor and native workers

The [model configuration](README.md#model-configuration) assigns roles for Codex.
Before initialization, inspect and explicitly set the stage profiles in
`plan --config`: convenience presets inherit some settings from the active chat
and do not configure the supervisor or its native subagents. Prefer the active
harness and establish actual access; equivalent Claude/custom settings must be
chosen explicitly rather than inferred from Codex names.

Save a dated operational receipt under `runs/RUN_ID/intake/` recording the
user-authorized supervisor/native agreement, requested harness/model/effort,
speed mode where exposed, concurrency, billing allowance and observed execution
identity or explicit unknowns. Reference the receipt in the run's append-only
event history through `Store.event`. This external agreement is not a new plan
field or an automatically enforced spending cap. Keep historical receipts.

Dispatch `agent-task` with its bound `intended_profile`. Dispatch
`agent-native-task` with the agreed external role settings and its owner/token.
Native scientific readers use fresh source-only contexts; in Codex explicitly
set `model`, `reasoning_effort` and `fork_turns="none"` when spawning. Do not rely
on inherited model settings or send evaluator context to a reader. A requested
model and worker self-report do not independently establish provider identity.

Use distinct leased units concurrently within the authorized harness capacity;
`resources.model_workers` and `retrieval_workers` govern automatic dispatch unless
an explicit `operational_policy.inference_workers` supplies the effective model
worker limit. That limit is shared atomically with all owned native task leases,
including expired leases awaiting recovery. It does not include the supervising
chat or authorize new model settings or spending. Retrieval remains separately
bounded by `retrieval_workers`.
Refill each available native slot promptly when independent work is ready; do not
wait for an entire batch to finish. The observed peak is not evidence of the
harness maximum. Respect the actual authorized capacity and keep blocked lanes
separate from ready work. Return concise results and source references, leave repetitive persistence to
code, and use focused status summaries. An independent native scientific
assessment remains required even when a compact prospect reading is complete;
avoid extra duplicate passes without bypassing that obligation or truncating
sources.

Report adapter calls/tokens, supervisor usage and native-worker usage separately
when telemetry exists. Cached input counts are not new source text. Missing
telemetry remains unmeasured, and `cost_usd=0` is not evidence of free subscription
or credit use. Account balances cover other chats too; credit runway is not a
completion estimate. Estimate remaining work from measured retention, source
availability and completed native tasks as well as automatic throughput.

### Checkpointing an external model change

An explicit user update may change an external supervisor/native-worker setting
that is not bound by a saved job profile. It does not authorize changing the
immutable execution plan or installed release.

1. Use `pause --run-id RUN_ID`, stop new native dispatch and reconcile admitted
   automatic jobs and native leases. Let workers finish where practical; recover
   interrupted workers only with the documented termination evidence. Stopping
   the chat alone does not establish that its background processes stopped.
2. Record the authorized change, previous and new settings, effective checkpoint
   and observed identity in a new operational receipt and append-only event.
   Preserve the earlier execution records and completed work.
3. Change the supervising chat and explicitly configure newly created workers.
   Existing workers retain their original settings. Keep all plan-bound
   automatic/manual job profiles, frozen inputs and source bindings unchanged.
4. Resume the same run with its bound release, then inspect actual settings,
   source coverage, task throughput and usage at the next agreed checkpoint.

This procedure neither migrates a release nor requalifies a scientific reader.
Source-grounded calibration and unresolved limitations remain visible. Changing
a bound job profile, code, scientific rule or resource limit requires a
separately versioned configuration/continuation; ordinary `resume` does not
provide that mechanism.

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
review initial source-grounded seed decisions within the actual run; do not require the
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
| `supervise [--check-yield]` | Inspect dispatch health; record continuation observations or checkpoint holds with `--mode`. |
| `run`, `run --watch`, `run --local-only` | Advance stages, wait within the selected scope, or disable automatic model dispatch |
| `work`, `submit` | Lease and publish ordinary agent judgments |
| `discovery-init`, `native-work`, `native-submit` | Initialize discovery and resolve native route tasks |
| `status`, `estimate`, `audit` | Inspect progress, report measured forecasts and schedule required screening audits |
| `sanity` | Incrementally check metadata, reasons and bookkeeping with explicit coverage |
| `calibration-report`, `calibration-review` | Inspect empirical seed discrepancies and record source-grounded adjudication |
| `validate` | Check run storage, source hashes, recorded outputs and budget consistency at a quiet checkpoint |
| `source`, `human-decision` | Add a later source or record explicit human vetting |
| `deliver`, `export` | Publish prospects and operational provenance snapshots |
| `host-check` | Record local launch restrictions without model inference |
| `pause`, `resume`, `recover` | Graceful stop, clear stop request, reconcile a proven dead owner |
| `retry` | Explicit fresh attempt for a verified terminal model failure, retaining its prior receipt and budget charge |
| `verify`, `package` | Verify or build an isolated static distribution |

Use `python -m sweep COMMAND --help` for required arguments. `--root DIRECTORY`
is a global option placed before the command; run directories go beneath it.

For a new run, use a local, nonsynchronized storage root. The package may remain
elsewhere, but the live SQLite database, WAL and SHM must stay together outside
sync-managed folders. `doctor` reports the actual selected `ROOT/runs` path,
resolved parent, directory/writability observations, disk capacity, versions and
recognized sync-path risks without writing a test file. `init` rejects recognized
sync locations and performs a temporary WAL/write/reopen/checkpoint probe in the
selected filesystem before creating `RUN_ID`. A successful probe is one current
I/O check, not a guarantee against later faults or a scientific commissioning run.
No unknown filesystem is certified by the absence of a recognized path marker.

For example, use `python -m sweep --root "$HOME/consciousness-sweep-work" doctor`,
then the same global option for plan/init/run/work/submit/status/validate/resume.
This selects a new run location explicitly; it does not move historical runs or
change source paths, judgments, resource agreements or executable fingerprints.

SQLite exceptions terminate new admission rather than becoming ordinary failed
paper/model jobs. Already admitted bounded work can finish. CLI stderr retains
the failing storage phase, path and available SQLite extended error code/name;
Python versions without those attributes report null. A cleanup/rollback error
must not replace the original failure, and uncertain commits are never retried
automatically. Preserve the diagnostics and database/WAL/SHM. Resolve the storage
problem and reconcile actual worker termination before recovery, then validate
under the bound release. A reported generic disk I/O error alone cannot establish
which filesystem operation or external process caused it.

For manual `work`/`submit`, `task.json` and the returned task envelope name the
intended profile and execution role. Dispatch each reading to a fresh worker
without inherited supervisor history. Supply only the task prompt/schema/source
and operational bindings; keep seed expectations, calibration comparisons and
prior assessments in the supervisor's context. This applies to ordinary readers
as well as alternative calibration readers. The latter must return an attested
envelope, copying binding values from `task.json`:

```json
{
  "job_id": "COPY_FROM_TASK",
  "owner": "COPY_FROM_TASK",
  "token": 1,
  "prompt_sha256": "COPY_FROM_TASK",
  "schema_sha256": "COPY_FROM_TASK",
  "source_sha256": "COPY_FROM_TASK",
  "intended_profile_sha256": "COPY_FROM_TASK",
  "execution_provenance": {
    "harness": "codex",
    "model": "ACTUAL_MODEL_OR_unknown",
    "effort": "ACTUAL_EFFORT_OR_NULL",
    "worker_context_id": "ACTUAL_FRESH_WORKER_ID",
    "fresh_context": true,
    "source_only": true,
    "calibration_reference_seen": false,
    "prior_assessments_seen": false
  },
  "result": {}
}
```

Replace `result` with the schema-valid judgment and `token` with the exact task
value. Use the string `unknown` for an unobserved harness/model and JSON `null`
for unknown effort; never infer actual identity from the requested profile.
Concrete reported settings must match concrete intended settings. Missing or
contaminated context attestations reject an alternative read; unknown settings
retain it as unverified. An alternative cannot reuse the known original reader's
worker context. Matching identity/isolation attestations are explicitly
**self-reported**, not provider-verified. The requested `profile`, reported
`execution_provenance` and `execution_verification` remain separately logged;
the original reading is never overwritten. Ordinary legacy raw submissions
remain accepted on the first lease but have unverified identity and isolation.
After a task is deferred or recovered and leased again, submit the bound envelope
with the current owner/token; a raw response cannot establish which lease wrote it.

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

Stop new automatic/native admissions and let all admitted workers finish before
a full checkpoint. Include acquisition workers and their pending source attachments,
not just model calls or native leases. Recover interrupted work only with the
required termination evidence. `run --defer-checkpoint` lets the supervisor own
this coordination: the runner persists admitted work and performs lightweight
sanity checks, leaving full validation and delivery for the quiet checkpoint.

After manual submissions and queued follow-up work are handled, run `sanity`,
`validate --run-id RUN_ID`, inspect its `ok` and errors, then `deliver --run-id
RUN_ID` and `status --run-id RUN_ID`. A clean snapshot invalidated solely by
concurrent writes produces `delivery/validation-incomplete.json`; it preserves the
last full report and delivery and does not manufacture an integrity failure.
Repeat validation when writers are quiet. Real validation errors remain blocking,
including a previous failure that a busy audit cannot clear. A later scientific or operational
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

Discovery reports `operational-frontiers-exhausted-final-review` when the current
zero-yield citation audit still matches its obligations, required process and
blind windows are complete, and no queued, failed, unprojected or native review
work remains. Repeated polling does not create another identical wave audit.
New or revised eligible obligations reopen the normal work and require current
stopping evidence. This checkpoint exposes unresolved source/reading states and
remaining final review explicitly; it does not certify missing-text reconciliation,
scientific records, exports or native completion.

The distributed repository excludes historical development runs and paper PDFs.
A versioned coordinator-only seed reference supplies expected contributions and
limits; no seed expectations appear in source-only worker prompts. Maintainer
tests and ongoing source-grounded seed checks can substantiate
mechanical and semantic claims separately. Claude and custom endpoint integrations
must not be described as live-verified where only simulated transports were used.

## Scheduling and source revisions

Title output is just a decision and a paper-specific reason; uncertainty advances.
Abstract output adds the exclusion basis. Every consequential scientific exclusion
receives a fresh source-only strongest-profile assessment; the first verdict and
feature assertions are withheld. A rescue that read the abstract completes that
stage. Clear outside-scope exclusions are independently audited in cumulative
source/stage cohorts: the ten lowest stable source-bound
hashes, or all papers in a smaller cohort. A miss reopens the remaining current
exclusions in that cohort. This sample does not estimate corpus recall.

With `retained_first`, ready retained work and existing prospects take precedence
over uncertain-abstract retrieval, reading and native assessment. Within the
uncertain lane, shallower citation depth and then stable discovery order take
precedence. Calibration reviews remain preferred. Blocked preferred work does not
hold ready lower-priority work unnecessarily. Uncertain papers retain their
scientific state and remain outstanding; an unbounded productive preferred lane
can leave them waiting indefinitely, which must be reported.

The active discovery buffer excludes this deferred uncertain lane and parked
acquisitions; `status` reports them separately. Eligible CORE, provisional CORE
and strict BRIDGE nodes expand under the unchanged scientific and lineage rules,
including deeper eligible work before shallower uncertain work. A prospect label
alone does not authorize expansion. Without retained-first scheduling, ready
reader jobs precede rescue/audit, abstracts and titles. Acquisition workers rotate among nonempty lanes for
priority work, supplied local sources, fresh retrievals, retries and other ready
stages such as search. Each nonempty lane receives service within five admissions;
an individual job's wait also depends on earlier work in its lane. Without retained-first scheduling, fresh work
is oldest-first across priorities and retries rotate by last service. With it,
active-lane jobs are ordered by citation depth then stable job ID. Discovery backpressure still
applies. The durable service cursor survives restart. This ordering changes no
paper's scientific eligibility. Every acquisition job binds an immutable source
manifest and generation. An
identical attachment is idempotent. A changed abstract reopens a screening-only decision; richer metadata does not replace an existing full-paper reading. A changed acquisition identity creates explicit source follow-up work. Older results remain in history but cannot
replace a newer generation or a richer current stage. `source-retry --run-id ID
--paper-id ID --reason REASON` authorizes a new acquisition attempt. It does not
silently retry a model call. Source-verified means bibliographic identity and
extraction were checked; it does not certify complete article text or figure
inspection. Acquisition gaps and individual claim dispositions appear in delivery.

Retrieval claims, actual acquisition starts and finished receipts are separate
from model admission and billing. `status` exposes `retrieval_execution`; an
attempt without a receipt remains visible after interruption. Retrieval receipts
and endpoint history publish under the same fenced lease as job completion or
deferral. They cannot be updated by a stale worker. Transient acquisition retries
use increasing delays from 60 seconds to a maximum ordinary delay of one hour;
longer valid `Retry-After` instructions are honored. Invalid or unrepresentable
server delays fall back to ordinary backoff and retain the response evidence.
Unchanged blocked or unreadable endpoint outcomes can be reused for 24 hours
while other endpoints remain transient. Local files are rechecked against their
bound hashes. A new source generation, including an explicit `source-retry`,
starts fresh endpoint history and preserves the old receipts. When the user selects
`retrieval_max_rounds`, actual acquisition starts count toward that per-generation
allowance; historical rounds count too. After the allowance, terminal unsuccessful
work is parked with its receipts and missing-source state, freeing the active
buffer. No additional model calls or scientific exclusions are created. An
interrupted attempt without a receipt still requires recovery. A new source or
explicit access-repair `source-retry` can reopen acquisition; unchanged failures
must not be recycled through that command to evade the allowance.

The policy is stored in the original plan for fresh runs or in an append-only
continuation receipt for an existing run. Omitting it preserves legacy scheduling:
no acquisition-round limit, the original model-worker limit, and ordinary automatic
checkpoints. `supervised_checkpoints` keeps incremental sanity during execution and
leaves full validation/delivery to the supervising agent at quiet wave checkpoints,
after recovery/source revisions requiring a checkpoint, and before handoff.

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

## Startup and ongoing checks

A request to "run the sweep" starts discovery after one scope/resource agreement.
Verify dependencies, writable run storage, exact adapter settings and observable
authentication. Real first retrieval/model calls supply the remaining operational
checks and count as sweep work. There is no compulsory commissioning run, 20-call
ceiling, one-hour cutoff or obligation to rerun scientific benchmarks on each host.
An optional diagnostic must be requested or justified separately, with its own
explicit scope; it must not silently replace the user's intended sweep.

Use `sanity --run-id RUN_ID` during execution for bounded incremental metadata,
reason, identifier and state checks. The report records which events/papers/jobs
were covered; an incomplete scan is not presented as full validation. The
persistent report is `delivery/sanity.json`. Full `validate` at quiet checkpoints
still checks the complete ledger and immutable source bindings. Neither checks
whether an experimental scientific inference is correct.

The 18 empirical seed papers pass through the actual title, abstract and full-text
gates. The calibration reference distinguishes 13 expected useful prospects,
three contextual controls and two papers without a fixed expected outcome;
review/discovery anchors are not assumed to be positive examples. Expected
contributions are evaluator material, not reader inputs or tier overrides. `calibration-report --run-id RUN_ID` exposes observed judgments, source
gaps and review flags. Missing text, partial reading, disagreement about a claim
and a model execution failure require different responses. An unexpected
exclusion is a flag for source-grounded adjudication, not proof that the seed
must pass or that a stronger model is automatically right.

A plan may declare an authorized `calibration_review_profile` alongside stage
profiles. It follows the same access, no-fallback and resource accounting rules.
This permits independent source-only rereading under an agreed stronger model;
its response does not overwrite the original scientific decision. The supervising
agent records a claim-specific resolution with `calibration-review --run-id RUN_ID
--paper-id PAPER_ID --input REVIEW_JSON`. If no authorized review route is
available, retain the flag and request a focused decision rather than silently
switching models or repeatedly spending until a preferred label appears.

Semantic seed comparisons are ordinary leased native tasks (`calibration:PAPER_ID`),
including when a prospect label agrees. Their template asks the supervisor to
compare each expected and observed claim, gate reasoning, source integration and
statistical scope. Check whether the decisive sources are actually available
before blaming the model or dispatching another read. Missing text is untested;
it cannot become a calibration failure or be filled from the reference. The
comparison report is linked from the delivery page. A valid, source-supported
departure from the reference can be recorded without rewriting either reading.

A reported acquisition or reading gap holds an automatic second read until the
supervisor records a located `source_coverage` judgment. Request missing premise
evidence first. Routine extraction notices do not block, and an interrupted read
with supplied unread units may go to the authorized alternative. Expected claims
guide comparison but never override source evidence or enter ordinary reader
prompts.

Authentication and configuration failures block the affected profile; a source
size problem blocks the affected job. `status` reports these under
`action_required`. The automatic loop continues independent work and returns
when only blocked work remains, instead of repeatedly probing access. After a
real fix, select the repaired block with `resume --run-id RUN_ID
--resolve-access-blocks --access-block BLOCK_KEY --reason "WHAT CHANGED"`.
This authorizes a fresh access check under the same settings. It neither raises
limits nor refunds uncertain admissions; failed admitted calls still use the
documented charged retry procedure. Confirmed rate limits retain backoff.

For an abandoned external-agent native lease, use `native-recover --run-id RUN_ID
--task-id TASK_ID --owner OWNER --lease-token TOKEN --actor SUPERVISOR --reason
"WHY" --proof RECEIPT_JSON`. The receipt must contain `kind` equal to
`supervisor-observed-termination`, the exact `owner`, a terminal `terminal_status`
(`completed`, `failed`, `interrupted` or `terminated`), the harness/task observation
in `source` and `evidence`, and a timezone-bearing `observed_at` after the latest
reservation. Expiry or silence is insufficient. Recovery fences the old token
and makes the unchanged work available again; same-owner resume is also supported.

Unattended execution still requires the supervising agent to service leased
native discovery tasks while automatic workers process retrieval and model jobs.
Use separate leased units and the shared transactional writer, and continue
independent work when one unit is deferred. Watch mode waits under the selected
scope; quota exhaustion, unknown admission, missing sources and native scientific
questions remain honest checkpoints. They are never treated as zero-yield search
results. The host/supervisor must remain available; the package does not install
a background service or arrange future wakeups.

## Native identifiers and source provenance

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

Durable `retrieval_deferred` events retain attempt receipts and the source-manifest
binding before a transient source request is requeued. The supervising agent uses
this evidence to distinguish access failures, source gaps and warranted recovery.

## Negative findings

The source-reader wrapper applies PROTOCOL §3.2 when a negative
comparison has an uninterpretable critical estimate, analysis population or
coverage: retain the performed test as unresolved, rather than call it supporting
negative evidence. This does not demand equivalence, Bayesian analysis or
primary-level control from a prospect. Other informative comparisons in the
same paper remain independently eligible. The scientific package, accepted
reading instructions, output schema and discovery rules are unchanged.

## Human dispositions

Operational validation requires an explicitly attributed human decision to use
one of the CLI's existing values: `accepted-support`, `accepted-primary`,
`declined`, or `pending`. Malformed values fail validation before delivery,
preventing a rendering failure or an ineffective queue exclusion.

## Evidence integration

The reader integrates supporting and contrary premise evidence
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

## Signal control and claim scope

Assess signal control where the focal information is presented, generated or
acquired, even when its use is tested later. Matching later probes cannot match
earlier information retrospectively. A different function's diagnostic pattern
does not automatically justify a separate prospect; a supporting observation may
instead remain context for the accepted mapping. Coherent tested functional
relations remain intact. This clarifies the existing same-X/same-Y contribution
and signal-control rules without changing scientific inputs or the output schema.


### Native task identities and record sanity

Native submissions distinguish `task_id` from the allocated logical `paper_id`.
An identity-resolution submission records both the bibliography task and its
resolved paper; a wave submission records its task and wave, with no paper ID.
Incremental sanity checks reconcile those bindings with durable task/encounter
or frontier records. Historical native-submission events that stored task IDs
under `paper_id` are interpreted without rewriting history; unknown tasks,
unresolved bindings and absent real papers still fail. A failed sanity cursor
is retained until a successful check, so full validation alone does not clear it.


## Routine source acquisition and recovery

The run request authorizes public metadata/paper/supplement downloads in scope.
The supervising agent performs routine acquisition and identity checks without
per-paper user confirmation. Public article and supplement links deposited in
OpenAlex, Europe PMC, DOI/publisher records and recognized repositories may be
followed directly. This is retrieval authorization, not proof of article identity,
source completeness or scientific validity. Host permissions remain independently
enforced; configure them as described in [host access](#host-access-and-recovery).

For an identified paper, use a terminal-first acquisition workflow:

1. Locate article and supplement URLs through metadata APIs, DOI/publisher links,
   repositories, preprint servers and author pages. Available search tools,
   including Google or Scholar where accessible, may locate additional copies.
2. Fetch located public files with `fetch-source` and extract them with terminal
   tools. Batch independent operations within the agreed concurrency and
   per-request limits; reuse unchanged verified files and extraction results.
3. Use browser interaction only for a specific source-access step unavailable
   through direct retrieval. Avoid lengthy navigation and repeated screenshots.
   Inspect images/pages when essential figures, tables or extraction problems
   require visual evidence; terminal-first does not mean text-only reading.
4. Preserve failed-attempt receipts, use another available permitted route, and
   continue independent work when access remains blocked. Retry an unchanged
   blocked route only when new evidence or changed access justifies it. Apply
   the existing missing-text workflow and the recorded acquisition-round allowance.
   At the allowance, park the request and continue; do not conduct repeated manual
   acquisition campaigns outside the recorded allowance.

These are acquisition methods, not changes to frozen discovery queries/windows,
article/version verification, complete source coverage or scientific judgments.
All downloads stay in the selected repository/run root; never scatter them in
Downloads or temporary personal folders. Automatic retrieval writes under
`runs/RUN_ID/sources/`. For a public URL located by the agent:

```sh
.venv/bin/python -B -m sweep fetch-source --run-id RUN_ID --paper-id P000001 \
  --url 'https://publisher.example/article.pdf' --reason 'Located publisher main article'
.venv/bin/python -B -m sweep fetch-source --run-id RUN_ID --paper-id P000001 \
  --url 'https://publisher.example/supplement.pdf' --role supplement \
  --association-reason 'Linked as supplementary information by the article landing page' \
  --reason 'Obtain methods needed for source coverage'
```

Each invocation saves a request receipt before dispatch, then a separate outcome
receipt under `intake/downloads/PAPER_ID/`. File names are content hashes; receipt
identities are unique. The command uses public-URL/redirect checks, a 30-second
request timeout, a 60-second total deadline and the existing 64 MiB per-download
safeguard. It performs one attempt; failures remain explicit. No model allowance
is consumed. Cookies and response headers other than content type are omitted.
A request receipt without an outcome means interruption/unknown, not success.
The result's `source_entry` is a candidate manifest entry, not a verified asset.

Verify title, authors, DOI/article version and supplement association against the
source. Combine all intended current main/SI entries in a JSON array under the
run directory, then use `source --manifest FILE --reason REASON`. Entries include
`path`, `role`, `expected_sha256` and, for supplements, `association_reason`.
Do not replace the main paper with a poster, wrong article, landing page or
unverified version. Source attachment preserves immutable bytes, advances the
source generation and retires only old current projections; prior readings and
costs remain historical. Concurrent publication cannot restore an old reading as
current. Identical bytes alone do not revive an older calibration generation.

| Observed condition | Agent action within the existing agreement |
|---|---|
| Public download unavailable/403/404 | Record the receipt; seek another public copy or a protocol-approved fallback; defer and continue independent work if still missing. |
| Citation response partial or identity unresolved | Preserve the incomplete window and resolve using source metadata/native tasks. Do not turn a failed response into zero results or silently alter frozen queries. |
| Canonical metadata incomplete | `ingest` source-grounded enrichment with provenance; retain rediscovery history. |
| New main/SI evidence | Verify identity and `source --manifest` the complete set; do not overwrite source files or completed reads. |
| Worker exited | Use `recover` or `native-recover` with observed termination evidence, then the newly fenced lease. Expiration alone is insufficient. |
| Confirmed authentication/quota repair | `resume --resolve-access-blocks --access-block BLOCK_KEY --reason REASON` for the repaired scope under unchanged settings. |
| Unknown/admitted model failure | Preserve its charge and receipt; `retry` only when termination is established and another charged attempt fits the existing agreement. |
| Host network or CLI state unavailable | Inspect `host-check` and `status.host_access`; restore the approved launch environment and resolve only the repaired hold. Local work can continue. |
| Input too large or budget exhausted | Surface the exact block. Do not truncate text, raise a bound limit, switch model/billing route or call it completion. |
| Integrity/storage failure | Stop admissions, preserve diagnostics, investigate read-only and validate using the bound release. No in-run code/database repair. |
| Calibration disagreement | Check source coverage, compare claims and reasons, preserve departures and unresolved evidence. Use only an already authorized isolated alternative reader. |

Fresh native source-reading tasks expose bibliographic identity, abstract, source
bindings and lease information, without prior screening, reader or human verdicts.
Evaluator-only calibration tasks remain separate. A retired source-scoped access
block stays in history but is not an action on its replacement; profile and budget
blocks remain in force across source replacement.

## Versioned operational continuation

Ordinary resume verifies the active runtime and never edits its fingerprint.
`continue-run` is an explicit operation for a paused portable run. It rejects
changes to protected scientific inputs, reader instructions, schemas, calibration
references and frontier rules. It changes only the operational runtime binding
and the four declared policy fields; profiles, depth, billing, budgets and the
original execution plan remain unchanged. It is not a native registered-ledger
migration or scientific certification.

1. Keep the old run and release in place. Download and verify the new release in
   a separate local directory. Stop admissions and drain all automatic, native
   and acquisition workers. Submit valid pending results before releasing leases;
   recover abandoned work only with actual observed termination evidence. Lease
   expiration alone is insufficient.
2. Under the old runtime, reconcile interrupted acquisition receipts and run
   quiet `sanity` and `validate`. Full validation must pass against the current
   material snapshot. If sanity fails because of a reproduced checker defect,
   preserve that failure and require a separately verified successor that fixes
   it; do not clear the guard or alter ledger records to pass. The continuation
   can proceed from the successful full validation, but the successor's sanity
   replay, full validation and delivery must pass before resuming. Unexplained
   integrity failures require investigation first. Preserve current deliveries.
3. Save the user-approved policy JSON under the existing run's `intake/`:

   ```json
   {"retained_first":true,"retrieval_max_rounds":3,"inference_workers":4,"supervised_checkpoints":true}
   ```

4. From the **new release directory**, use its Python environment and keep
   `--root` pointing to the **existing run repository** on every invocation:

   ```sh
   .venv/bin/python -B -m sweep --root /local/old-release continue-run \
     --run-id RUN_ID --previous-release /local/old-release \
     --policy /local/old-release/runs/RUN_ID/intake/operational-policy.json \
     --actor supervising-agent --reason 'User-authorized operational continuation'
   ```

   Inspect the read-only preview. Repeat the same command with `--apply`. The
   operation backs up SQLite and the exact original plan under `continuations/`,
   atomically records the runtime transition, and fences stale runtime writes.
   It then parks already-exhausted acquisition jobs idempotently. `STOP` remains.
   A failure after the recorded transition does not undo it: inspect `status`
   under the new runtime and reconcile before resuming; never restore the backup
   over a ledger that has subsequent work.
5. Run `sanity`, `validate`, then `deliver` with the new executable and old root.
   Inspect preserved assessments, source gaps, parked acquisitions, pending queues
   and access/budget blocks. The new runtime can recover a predecessor's verified
   terminal model receipt; unknown/admitted calls retain their charges. Prepared
   confirmed-unadmitted requests receive new successor IDs if the adapter changed;
   original artifacts remain unchanged. Access blocks still require scoped repair.
6. Only after the checkpoint passes, use `resume` and restart coordinated work
   with the new executable and the same root/run ID. Refill authorized shared
   slots without bypassing independent scientific assessment. Do not edit a plan,
   copy patched files into the old release, replay completed readings, reset
   counters or use old-runtime commands after continuation.

For a later continuation, `--previous-release` names the then-active executable
release; `--root` still names the unchanged run repository. The receipt chain
retains every operational agreement. Any scientific conflict requires separate
review and is outside this mechanism.
