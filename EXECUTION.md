# Portable execution reference

This document describes implemented command interfaces and their limits. The
scientific package under `science/` remains frozen and separate. Fresh portable
plans use `focused-v1`, an explicit selective-coverage and single-reading workflow.
Its coverage/review choices supersede the native registered workflow only in the
portable runner; scientific eligibility and interpretation stay unchanged.

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

## Managed worker exchange

The coordinator can publish completed answers through a managed local process
while the active harness runs fresh workers. No model session is launched by this
process; it does not change profiles, billing, coverage, resource limits or holds.
Use one supervisor and one publisher per run.

After initialization, or a quiet supported continuation, explicitly open the
publication gate and start the publisher in a managed terminal session:

```sh
.venv/bin/python -B -m sweep publication-control --run-id RUN_ID --mode OPEN --actor SUPERVISOR --reason "Begin managed publication after verified setup"
.venv/bin/python -B -m sweep publication-watch --run-id RUN_ID
```

Keep the returned process/session managed until its actual exit. The optional
`--max-seconds` bounds this helper session only; omission adds no total duration
limit. `--poll-seconds` defaults to one second. A second publisher is refused.
STOP prevents new work but lets admitted answers settle; the publisher exits when
no workers remain owned. `publication-control --mode HOLD` stops publication and
new admissions. It does not cancel already admitted bounded network calls. A
missing or inconsistent publication gate fails closed. Ordinary runs that have
never configured this gate retain their existing supervision controls.

Observe the actual number **N** of free harness worker slots, excluding the
supervisor and workers already running elsewhere in that harness. Then call:

```sh
.venv/bin/python -B -m sweep exchange --run-id RUN_ID --slots N
```

This first commits ready answers, then offers up to N eligible tasks within the
run's shared recorded cap. `--slots 0` only drains and reconciles; it creates no
workers. Offers keep the existing model/native scheduling order and source/lease
bindings. They are stored under `intake/dispatch-v1/<TICKET_ID>/task.json`, with
compact ledger tickets. The returned packet is coordinator material: supply only
its designated source-only files, bindings and intended profile to each reader.

For each **new** ticket, create exactly one fresh worker in the active harness,
using the intended model and effort with no inherited coordinator conversation.
After observing its actual context identifier, record the handoff:

```sh
.venv/bin/python -B -m sweep dispatch-ack --run-id RUN_ID --ticket-id TICKET_ID --worker-context-id CONTEXT_ID --actor SUPERVISOR --reason "Observed worker creation for this exact ticket"
```

An offered ticket is not evidence of dispatch. If the supervisor or command dies,
`exchange` reports the existing unacknowledged ticket rather than offering that
lease again. Inspect the exact ticket against actual harness workers and their
history. A matching worker can be acknowledged; uncertain worker existence needs
reconciliation. Expiry or a missing reply does not authorize a second reader.
Record absence/termination evidence through the existing recovery workflow when
appropriate. Changed leases cannot be acknowledged as if they were original ones.

When a worker finishes, retain its original bound answer unchanged. Obtain a local
settings observation and exact worker pointer from the harness, keeping unavailable
facts unknown. The settings file has `settings_match: true` and a nonempty
`actual_local_turn_settings` list of `{model, effort}` observations. The pointer
has `session_id` and `agent_path`. These are coordinator attestations, not provider
identity verification; do not manufacture them from the intended profile or solely
from worker self-report. When settings cannot be observed, retain that unknown and
use the existing supervised submission route for the saved answer; do not rerun
inference merely to use this optional queue. A model envelope must include its source/prompt/schema/
profile hashes, lease, result and source-only `execution_provenance`.

```sh
.venv/bin/python -B -m sweep publication-stage --run-id RUN_ID --kind model --entity-id JOB_ID --input runs/RUN_ID/intake/answer.json --settings runs/RUN_ID/intake/settings.json --pointer runs/RUN_ID/intake/worker.json --actor WORKER_OWNER
```

All three files must be inside this run. `staged` means queued, not committed.
The publisher commits through the existing validators and fenced submission API,
with its acknowledgement in the same transaction. It retains immutable envelopes
and receipts under `intake/publication-inbox-v1/`. A lost acknowledgement is
recovered from the ledger without resubmission or inference. Original answers,
first readings, history and charges are retained. An orphan file receipt is a
reconciliation issue, never proof of a database commit.

React to each `published`/`refill-needed` notification immediately: observe free
harness capacity, run `exchange`, create and acknowledge the next fresh worker.
Do not wait for all readers, the next heartbeat, a full status report or full
validation. This is a harness handoff, not autonomous Python spawning. The same
loop applies with scripted workers in tests and with the observed active harness
in execution. If the publisher exits with an error, preserve its output and inspect
the exact records before restarting; never infer that its pending answer committed.

Bounded acquisition answers can use `--kind native --entity-id TASK_ID` with their
existing `native_lease` and observed settings/pointer. Other native scientific
reviews, identity resolutions and calibration adjudication retain their normal
supervised `native-submit`/review commands. Completed native submissions are
recognized from their exact terminal lease event; ambiguous legacy completion
does not authorize replay. One invalid queued answer is retained with a
`needs-reconciliation` receipt while other eligible answers can proceed. A global
integrity failure holds publication globally instead of condemning every draft.
After resolving a specific blocker, use `publication-reconcile --run-id RUN_ID
--request-id REQUEST_ID --actor SUPERVISOR --reason "Evidence of the resolved
condition"`. It rechecks the exact saved envelope through the same fences and
preserves the original blocker receipt; it does not clear holds or rerun inference.

Normal polling and repeated CLI handoffs use the pending index and a ledger-bound
index checkpoint, without scanning all settled envelopes each time. An older
restored ledger invalidates that checkpoint and triggers reconstruction. Restore
only while all processes are stopped; keep original envelopes/receipts together
with their run and do not manually prune the pending index.

Ordinary local CLI mutations share a short coordination lock. `run` and
`fetch-source` retain their short store transactions and execute network requests
outside that extra lock. Do not add a command-wide wrapper around them. At a
checkpoint, use `supervise --mode checkpoint`, drain the source runner and workers,
then hold the publisher and validate/deliver the quiet snapshot. Reopen the
publication gate and return supervision to active mode only when those checks pass
and the run is authorized to continue. Existing STOP, access, budget and scoped
search holds must remain intact.

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
      "retrieval_max_rounds": 1,
      "workflow": "focused-v1",
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
not the convenience preset's command-line defaults. `plan` defaults to
`operational_policy.workflow="focused-v1"`; it requires exactly one acquisition
round. `legacy` is supported only for explicit historical-workflow compatibility. The explicitly supplied
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
coalescing also respects the selected profile's request capacity. Fitting batches
stay separate when their combined packet would exceed it. There is no requirement
to wait for a full batch before processing the final tail.
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
Native paper tasks expose current sources and explicit dispatch fields only.
Saved process-audit explanations, prior verdicts and deferral notes remain in the
supervisor's ledger. Dispatch the newly emitted task, without appending those notes
or reusing a worker context that has seen them.

With focused retained-first scheduling, unfinished native assessments following
complete legacy contextual readings form a background queue. Ready model work
and other native tasks take precedence. Background tasks remain claimable when
preferred work is unavailable, retain lease fencing, and still prevent final
completion. They are counted separately as `background_contextual_native` in
queue pressure and do not occupy the active discovery buffer. New sources,
incomplete readings and combined-reader jobs do not receive this lower priority.

Eligible source windows rotate among principal citations, deeper citations and
earned query windows. The saved turn survives resume. Existing depth limits,
source windows, queue size, concurrency and backpressure still apply. This changes
admission order only; no new scientific eligibility or stopping rule is introduced.

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
code, and use focused status summaries. Newly commissioned papers receive one combined substantive reading, including
the rubric output and native citation/process decisions. Existing completed
initial readings retain their results and finish only their outstanding native
assessment. Never turn a prospect/context label into a citation decision or
truncate source coverage to fit a worker.

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

### Managed publication and capacity blocks

Workers return their bound answer file and execution receipt; the coordinator
publishes the answer unchanged with `submit` or `native-submit`. Keep the actual
submission command attached to a managed execution handle until it exits, then
check durable job/task completion. Do not launch an unawaited `Popen`, shell
background child or other detached submission. A launcher exit or returned PID
does not establish success. If the terminal outcome is lost, first inspect the
bound job and stored result: a committed result is reconciled without another
submission; an uncommitted draft stays preserved until supported recovery permits
a normally leased, exact-input publication. Do not repeat model inference, alter
the judgment or attribute the coordinator's identity to the original reader.

`work` uses the automatic adapter's packet-byte, conservative context and
per-request cost checks before returning an agent task. A rejected model packet
creates `status.action_required` under `access-block:job:JOB_ID` and atomically
releases its lease; no worker is launched and accounting is unchanged. The
dispatcher continues to independent fitting work. Resume preserves this block.
The bound prompt, source, schema and profile hashes remain in its history. An
explicit resolution rechecks the same limits; if nothing has changed the block
returns without dispatch. Source replacement supersedes the old request rather
than clearing profile/budget holds or overwriting its evidence. The conservative
context estimate is not an exact tokenizer or proof of provider capacity.

Keep complete main articles and relevant textual supplements. Raising limits or
changing a reading strategy is a separate recorded configuration decision, not an
automatic response to a block. Oversized work remains visible and incomplete
without preventing other eligible work from being dispatched.

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

The focused workflow retains the semantic title/abstract rubric and existing
25-title/10-abstract batch bounds. Every paper has a source-specific decision and
reason. Scientific exclusions are terminal for unchanged evidence; no automatic
rescue or sampled audit is commissioned. Abstract-uncertain papers remain indexed
in deferred coverage. The scheduler does not silently drain that queue when
preferred work ends. Title-retained papers without abstracts receive one bounded
OpenAlex → Europe PMC → Crossref lookup, then remain unassessed if unavailable.
Identity must match by DOI or complete title/year/authors; ambiguity is preserved.

Source-ready reading and outstanding native assessments take precedence over
admitting more papers. Discovery backpressure counts that downstream work along
with screening and retrieval; deferred papers and parked acquisitions do not fill
the active buffer. Every encountered paper remains in global deduplication.
Eligible nodes may expand to deeper levels while earlier uncertain papers wait.
CORE/strict BRIDGE criteria, bridge lineage and bounded process/blind query windows
remain unchanged. A prospect label alone does not authorize expansion.

Compatible untouched partial screening batches coalesce without changing paper
bindings or reasons. Prepared inputs and previous job IDs remain immutable. No
batch waits for its slowest neighbor before another free worker can start.
Inference workers share the recorded cap across model and native leases; retrieval
and abstract metadata requests use the network-worker pool.

One acquisition pass uses known locations with a 180-second deadline and one
transport attempt per request. It collects associated supplements encountered
with the main article. If no readable verified article is found, a single bounded
native acquisition task may inspect the publisher page and make one public-copy
search, inspecting at most two candidate copies within 120 seconds. Missing text
is recorded as deferred coverage. The native worker must use the intended
metadata profile, save receipts, and return; it must not repeat the hunt.

Acquisition claims, actual starts and terminal receipts remain distinct from model
billing. Interrupted attempts without receipts require ordinary recovery.
Historical attempts count toward the one-round limit on continuation. Already
parked work remains parked. Server Retry-After evidence is retained; it does not
commission another acquisition round. Mandatory citation/query source windows
retain their own completeness and fallback rules, rather than being mistaken for
paper-download hunts.

Every source job binds a manifest and generation. Identical attachment is
idempotent. New explicitly supplied files can reopen deferred work through a new
generation, preserving earlier results and receipts. Rediscovering another URL
alone does not restart a parked hunt. `source-retry --run-id RUN_ID --paper-id ID
--reason REASON` is an explicit new acquisition authorization; use it only when
access/evidence actually changed, not to evade the bounded pass.

Changed abstract evidence can receive a new append-first decision. Clerical
metadata updates and repeated discovery do not justify repeated semantic screening.
Older results cannot replace a newer source generation or richer current reading.
Source verification establishes article identity and extraction integrity, not
complete reading, figure inspection or absence of unprovided supplements.

The original plan or append-only continuation receipt records this workflow.
Operational `status.coverage` reports deferred papers and held jobs separately.
Holds preserve old job IDs, sources, outputs, failures and charges. An active-scope
checkpoint with deferred coverage is not scientific saturation or native
registered-run certification.

## Startup and ongoing checks

Startup verifies the release, storage, immutable inputs and the user's actual
resource/depth agreement. A separate pilot, rerunning the calibration set for each
fresh worker, or trying every available provider is not required.

The 18 empirical seeds remain unchanged: 13 expected useful prospects, three
contextual controls and two without a fixed outcome. They pass through the same
screening and source workflow. Expectations remain with the evaluator.
`calibration-report --run-id RUN_ID` retains observed claims, gaps and disagreements;
these flags do not automatically commission a reread, force agreement or create a
recurring adjudication task in focused-v1. Missing text is untested. Explicit
source-grounded adjudication can be recorded with `calibration-review`; original
and alternative readings remain separate. Additional model work needs an actual
agreed scope/profile and does not silently inherit a stronger model.

Incremental `sanity` checks metadata, identifiers, references and state transitions
against a consistent snapshot. Its default interval is 60 seconds. It does not
rehash every source or judge scientific claims. Full `validate` checks the complete
ledger, source bytes and immutable bindings at a quiet checkpoint. Neither proves
scientific reading quality. A failed check blocks further admission until resolved.

Use supervised checkpoints to stop admission and drain workers before validation
and delivery. Retain previous publications while preparing the next snapshot.
Known access/budget blocks are durable; resolve them only after actual repair.
Unknown/admitted calls retain their accounting, and lease expiry alone is never
proof of termination. Session or budget exhaustion leaves incomplete work visible.

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


## Source scope and oversized packets

The focused workflow acquires the main article and supplementary text only:
methods, results, appendices, tables and figures in those documents. Do not download
code, repositories, raw datasets, simulation traces or saved software outputs. Do
not convert them into reader text or image collections. A document containing
code examples or equations remains an intact article/supplement. Record excluded
artifact links as outside acquisition scope, not as scientific exclusions. A claim
that depends on unexamined material must retain that limitation.

Known code/data extensions and repository/archive links are rejected before
fetching. The public transport also checks redirects and response headers before
reading the body. An opaque response discovered to be an archive after receipt
is not saved as a source. Ambiguous text files still require source-grounded
inspection; extensions alone do not establish document type. A mixed archive is
not a reason to download an entire repository: locate a direct textual supplement
within the existing acquisition allowance, otherwise record the gap. Publisher
metadata requests and article identity verification remain authorized.

Manifest entries may declare `material_kind`: `article-text` or
`supplementary-text`. `code`, `dataset`, `software-output` and `other` explicitly
identify out-of-scope artifacts and are rejected by focused acquisition/intake.
A CSV/TSV supplementary results table needs an explicit `supplementary-text`
identification; this does not imply raw observations were analyzed. Unsupported
document extraction remains a recorded gap, never a fabricated reading.

For an authorized one-time cleanup of size-blocked, unassessed packets, inspect
source inventories and classify attachments before changing any current manifest.
Keep all downloaded originals, old packets, hashes, failures and accounting.
Exclude only identified non-text artifacts from a replacement main/textual-SI
manifest, recording each omission and its reason. Use `source --manifest` to
create an immutable source generation and supersede stale pending work. Never edit
an existing packet or hash. Completed scientific readings are not automatically
rerun by this cleanup. Do not clear profile/budget/unknown-outcome holds.

Measure the new complete reader prompt once. A now-fitting successor can proceed
through normal leased admission; a still-oversized source stays deferred without
repeat retries. Do not delete genuine text, appendix sections, references, tables
or figures to fit a cap. Long theses need a separately verified context strategy.
`max_input_bytes` is a coarse operational guard, not the model context window;
the adapter's current context/cost bound also conservatively uses UTF-8 bytes as
a token upper bound. Raising only the byte cap may still fail that bound. Do not
change plan-bound limits, use unverified token estimates, truncate sources or
silently split scientific readings. Preserve all resource and isolation controls.

## Routine source acquisition and recovery

The run request authorizes public metadata, article and supplementary-text downloads in scope.
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
  --url 'https://publisher.example/supplement.pdf' --role supplement --material-kind supplementary-text \
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
`path`, `role`, `expected_sha256`, optional `material_kind` and, for supplements, `association_reason`.
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

## Scoped search-window holds

When an unresolved dependency affects identified process or blind query windows,
hold those exact windows and continue independent work. Do not stop all source
execution or use a paper-count threshold as a substitute for a scoped hold.
Global integrity failures, STOP, and access/budget blocks retain their existing
scope and must still be respected.

Use the `window_key` values recorded in `discovery_frontiers`:

```sh
.venv/bin/python -B -m sweep search-hold --run-id RUN_ID \
  --window-key WINDOW_KEY --actor supervising-agent \
  --reason 'This window depends on an unresolved recorded comparison; see intake/review.json'
```

Repeat `--window-key` to hold several windows atomically. The command refuses
unknown or completed windows, owned workers and completed results awaiting
projection. Reconcile those workers/results before holding the window; a hold
does not cancel a request already dispatched. Holds survive restart and cover
both queued automatic searches and native source-resolution tasks. Held jobs
do not consume the active search-queue buffer. Unrelated citation expansion,
abstract lookup, acquisition and reading continue under their existing rules.

`status` and `supervise` list active holds with their exact request identity and
reason. These windows remain incomplete. An empty runnable queue is neither
frontier exhaustion nor scientific saturation. Resolving the underlying evidence
question remains separate from the operational hold:

```sh
.venv/bin/python -B -m sweep search-release --run-id RUN_ID \
  --window-key WINDOW_KEY --actor supervising-agent \
  --reason 'The recorded dependency has been resolved' \
  --evidence 'intake/review-resolution.json: source-grounded resolution and validation'
```

Release preserves the original request, queued job and prior history. It does
not alter eligibility, grant resources or repair scientific records. Do not
release a hold merely to obtain an empty queue or finish the run. `run --local-only`
disables automatic model calls; it still permits network retrieval and searches.

An acquisition's parked receipt remains bound to its original manifest and
attempt generation. Later bibliographic locations can advance metadata without
reopening that acquisition. The validator requires the unchanged acquisition
binding and the intervening metadata-only history. Explicitly supplied local
text, including through `ingest`, reopens source processing; a rediscovered URL
alone does not authorize another hunt.


## Versioned operational continuation

`continue-run` operates on a paused portable run using a separate verified release.
It preserves the original plan, completed work, source artifacts, IDs, charges,
depth and billing. Profiles remain unchanged unless the explicit title-only option
below is supplied. Protected scientific files, accepted reader rubric,
calibration reference and frontier criteria must match. A receipt explicitly records
whether the coverage/review workflow changed; this is not silent native-run migration.

1. Keep both releases and the run. Pause admission and drain all workers. Submit
   completed valid work. Recover abandoned leases only with observed termination
   evidence. Reconcile interrupted acquisition receipts.
2. Under the old active runtime, run quiet sanity and full validation. Full validation
   must pass against the latest material snapshot, except for the narrowly scoped
   validator-only procedure below. Preserve unexplained failures;
   do not edit code, source hashes, the ledger or the fingerprint to force passage.
3. Save the authorized policy under the existing run's `intake/`. Use the actual
   available shared inference capacity. For example:

   ```json
   {"workflow":"focused-v1","retained_first":true,"retrieval_max_rounds":1,"inference_workers":3,"supervised_checkpoints":true}
   ```

4. From the new release directory, use its Python and the original run root:

   ```sh
   .venv/bin/python -B -m sweep --root /local/run-repository continue-run \
     --run-id RUN_ID --previous-release /local/active-release \
     --policy /local/run-repository/runs/RUN_ID/intake/workflow-policy.json \
     --actor supervising-agent --reason 'User-authorized focused coverage and combined reading'
   ```

   Inspect the preview, including `workflow_contract` and
   `coverage_and_review_changed`. Repeat with `--apply`. The command backs up SQLite
   and the exact original plan, records the runtime transition, fences older
   binaries and reconciles pending work. STOP remains in place.
5. Inspect the reconciliation: completed readings and native assessments are intact;
   unfinished old initial readings receive fresh combined successor jobs; completed
   initial readings finish only their remaining native work. Prepared predecessor
   files remain immutable. Uncertain/unavailable work is held or parked, exclusion
   rereviews are held, and unknown calls retain their receipts and charges. No
   historical judgment is rewritten to satisfy the new workflow.
6. Run new-runtime `sanity`, `validate`, then `deliver` with the original root.
   Confirm counts, source generations, holds, original budget totals and the explicit
   deferred-coverage report. A failure after the transition requires inspection and
   reconciliation under the new runtime; never restore a backup over later work.
7. Only after these checks pass, `resume`, return supervision to active mode if held,
   and refill available leased slots. Use the new executable with the same root/run
   ID on every invocation. Never overlay the old release or restart the run.

A later continuation names the then-active release as `--previous-release`.
Ordinary resume never changes policy or adds an allowance. A different scientific
rubric or frozen input requires separate scientific review and is rejected here.

### Validator-only recovery

When the active release falsely rejects a parked acquisition after bibliographic
rediscovery, a reviewed replacement can perform an explicit validator-only
continuation. Retain the failed predecessor report and its history. Add
`--repair-validation parked-metadata-generation-v1` to both the `continue-run`
preview and its subsequent `--apply` command.

This procedure requires STOP, no owned workers or unfinished acquisition attempts,
and a fresh predecessor full-validation report containing only the recognized
parked-metadata failure. The replacement proves the unchanged acquisition binding
and metadata history, then performs full validation and sanity read-only on that
same snapshot. Any other failure, changed snapshot, model-profile change or
operational-policy change blocks the transition. It is not a general validation
bypass and does not clear access holds or resolve scientific dependencies.

Application preserves the predecessor report and records the repair evidence in
the ordinary backed-up continuation receipt. Keep STOP until new-runtime sanity
and full validation pass explicitly. No counter, parking proof, source file,
scientific judgment or charge is rewritten to make validation succeed.


### Title model access and authorized replacement

Check the current harness's exact worker model/effort capability before dispatch.
A missing entry in an old catalog leaves access unestablished; it is not a provider
rejection. Refresh the observable capability without inferring entitlement from
the installed binary or a worker's self-report. A current tool-schema restriction
must be respected. Actual execution through the requested route is stronger
evidence than a catalog listing, while backend identity may remain unverified.
Keep a working preferred model; an access problem is not a scientific reading
failure or a reason to increase reasoning effort.

### Bounded title access recovery

The supervising agent manages this policy using the existing access-resolution,
lease and continuation commands. The runner does not automatically switch models
or create a polling task. Apply it within the user's recorded allowance and
existing supervision mechanism; it adds no model calls at startup.

Keep one outage record per exact title profile and execution route under
`runs/<RUN_ID>/intake/model-access/`, with a unique outage ID. Save each observation
as a new file: UTC time, catalog/receipt evidence, requested model and effort,
job/lease identity where present, admission state, attempt count, next check time,
authorized fallback and remaining unknowns. Recover this record on resume and
share its count across workers; a new job or supervisor invocation does not reset
it. Never store credentials or overwrite earlier evidence. These notes support
supervision; they do not clear ledger blocks, grant leases or establish billing.

| Observed condition | Supervisory action |
|---|---|
| Catalog missing/stale, route otherwise untested | Refresh capability first. If the exact setting is permitted, dispatch one ordinary leased title batch. If the tool currently disallows it, retain the hold and recheck capability without inference. |
| Transient refusal with confirmed terminal nonadmission | At most three dispatch attempts total in the outage, including the original. Space the second and third at least 60 and 300 seconds after the preceding attempt, with a small additional stagger; honor any longer retry-after. Reconcile the receipt, resolve only the affected access scope with the actual retry rationale, and dispatch just one batch at a time. Continue independent work during the delay. |
| Explicit unsupported model/effort, authentication failure, exhausted quota or billing denial | Do not repeat the unchanged request. Require changed capability, repaired access or a reset before retrying. A different model must not be used to evade an account/budget hold. |
| Timeout, lost worker, admitted failure or unknown admission | Preserve the receipt and charge. Establish worker termination and reconcile the outcome; only the existing explicit charged-retry workflow can authorize another attempt. These calls are not nonadmission retries. |
| Completed response, including malformed output or a disputed screening decision | Save and handle it under the existing result/review workflow. It is not evidence that the model is unavailable; no access retry or model escalation follows from the label or format alone. |

For the economical Codex title configuration, the preferred pair is
`gpt-6-luna` / `medium`; the optional fallback is `gpt-6.1-sol` / `low` on the same
authorized harness and billing route. Both switching to the fallback and returning
to the preferred pair require recorded user authorization, which may be supplied
once for this policy. Existing authorization need not be requested again. Other
roles and harnesses retain their own exact profiles. A fallback is never implied
by the recommendation. Once the bounded transient attempts are exhausted, or an
explicit unavailability is established, use the authorized fallback at a quiet
checkpoint or retain the scoped hold. Do not start a new three-attempt cycle for
each paper.

While on fallback with title work remaining, check the preferred capability at the
first ordinary supervisory checkpoint at least one hour after fallback, then at
least two hours after an unchanged check, then at least four hours between further
unchanged checks. Honor longer provider reset times. These checks use available
catalog/access observations without inference; keep the working fallback busy.
Do not wake the supervisor solely to poll, run repeated model probes, or create a
full validation checkpoint for an unchanged observation. If no non-inference
capability check exists, retain the unknown and wait for new access evidence.

New evidence permitting the preferred model can trigger restoration at the next
quiet checkpoint after at least one hour on fallback. Use the title-profile
continuation below, even when the release itself is unchanged. Resolve any old
preferred-profile block explicitly under the profile to which its original job
was bound; a continuation does not erase that block. Dispatch one ordinary pending
title batch under the restored profile, accept its result if valid, and only then
fill the other title slots. This is useful work, not an extra calibration call.
Do not re-screen completed titles or interrupt admitted fallback workers.

If restoration fails, retain its real admission/accounting state and use the
same bounded recovery rules. A return to the authorized fallback is another
recorded quiet transition, not a hot task rewrite. After a failed restoration,
wait at least four hours and require new evidence before another restoration;
do not bounce between models on each worker handoff. Skip restoration checks when
no title work remains. Record requested and reported settings separately; a
successful task alone is not proof of provider identity.

### Recording a title profile change

If the user authorizes a replacement for title screening, `continue-run` accepts
`--title-profile /absolute/path/title-profile.json` during the same quiet,
backed-up transition. Supply the exact authorized `model`, `effort` and a nonempty
`access_evidence` description of what was observed and what remains unknown.
The option changes only title model/effort on the existing Codex/manual route.
It preserves the original plan, other roles, request limits, billing and budget.
Qualification evidence for the old model is retained in history and is not
transferred to the replacement; this adds no compulsory calibration run.
The option is optional; runtime upgrades never imply a model change.

The preview lists `title_profile_history` and `title_profile_replacements`.
Completed/historical jobs retain their original settings. Pending title jobs get
new successor IDs and the same source bindings; their old files, blocks and
records remain. Previously leased work requires recorded nonadmission, and any
admitted/uncertain request or dependent job prevents automatic replacement.
Reconcile those cases explicitly. A reserved job-ID boundary binds future title
jobs to the recorded profile, including after coalescing or another continuation.
The intended task profile, reported worker identity and provider verification
remain distinct. No retrospective rereading or allowance reset is implied.

Completed-result projection is atomic per bounded job: checking its current
state, applying local changes and recording completion share one transaction.
Overlapping coordinator calls reuse committed results; interrupted transactions
replay from the saved source snapshot. Network requests and inference run outside
this transaction. Keep a single supervisor/managed runner for clear ownership;
parallel reader and retrieval workers retain their existing shared limits.

## Backup storage

Routine checkpoints do not require another full SQLite copy. `continue-run` makes
one consistent backup itself and checks available space before copying. A status
update, heartbeat, fixed worker-completion count or ordinary pause/resume does
not justify an additional snapshot. Keep validation at the documented checkpoints.

Use the storage commands to reclaim space occupied by **closed historical SQLite
backups**. Preview is read-only and can run during normal work:

```sh
python -m sweep --root /local/run-repository backup-archive --run-id RUN_ID --keep-latest 1
```

At a paused, drained checkpoint, archive the previewed older backups:

```sh
python -m sweep --root /local/run-repository backup-archive --run-id RUN_ID \
  --keep-latest 1 --apply --actor supervising-agent \
  --reason 'Retain the newest restore point and losslessly archive older backups'
```

The default `--keep-latest 1` retains the newest restore point and the latest
continuation backup (which may be an additional file). A larger value retains
more recent backups uncompressed when explicitly requested. It compresses older
backups one at a time, checks their original run plan, streams decompression to verify original bytes
and SHA-256, and durably records the archive mapping before removing only the
uncompressed historical copy. Identical backups share one compressed blob.
The latest continuation and original receipts remain intact. Reruns verify and
finish interrupted operations; changed files, missing/corrupt archives, active
workers, SQLite WAL/journal sidecars and unsafe paths stop removal. A leftover
SHM index without WAL stays in place with its hash recorded and checked; it is
never removed, reconstructed or treated as missing database content. No model calls occur.

Archives and per-path records live under `runs/RUN_ID/storage/backups/`. Their
original-path mapping supplements existing receipts without rewriting those
receipts or the ledger. Keep this directory with the run. Archives preserve all
backup bytes; they are not a substitute for a separate-device disaster backup.

Restore a historical backup to its original path when needed:

```sh
python -m sweep --root /local/run-repository backup-restore --run-id RUN_ID \
  --backup continuations/CONTINUATION_ID/state-before.sqlite3 \
  --actor supervising-agent --reason 'Restore a historical snapshot for inspection'
```

Restoration requires paused/drained work and enough space. It verifies the
compressed and decompressed hashes and refuses to overwrite different existing
bytes. This restores a **historical file only**; it never rolls back the active
ledger. Never copy that file over later completed work.

These filesystem-maintenance commands open the live ledger read-only and may
maintain backups from an older compatible portable run before runtime adoption.
They do not initialize Coordinator, alter fingerprints, migrate the run, or
authorize execution with a different release. Run ordinary scientific work and
validation under the run's bound runtime until a supported continuation succeeds.
After continuation, apply backup maintenance before resuming; ordinary checkpoints
need no recurring full-backup or archive pass.

Storage commands leave sources, extraction, job files, delivery generations and
all original ledger events unchanged. Their space savings concern historical
backups; they do not certify capacity for an arbitrarily large sweep. Report
actual before/after bytes, retained restore points and archive failures. If disk
space becomes insufficient, keep the run operationally paused with the reason;
never report scientific exhaustion.
