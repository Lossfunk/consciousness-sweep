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
    "max_wall_seconds": 3600
  },
  "workload": {"logical_papers": 2000}
}
```

This is an unapproved example. Set authorizations only after the user grants
them. Automatic profiles each require `authorized: true`; resource authorization
alone does not authorize a different provider. `--config` uses the file's values,
not the convenience preset's command-line defaults.
Authorized plans require positive finite `max_calls` and `max_wall_seconds`.
Call, token and spending caps belong in `resources`; per-profile versions of
those caps are rejected because the coordinator budgets the entire run.

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
`delivery/papers/PAPER_ID.html`. These pages show stored claims, their source
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
