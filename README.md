# Consciousness literature sweep

A portable, resumable literature pipeline for finding studies that help explain
how awareness of an entity X relates to its use by a downstream function Y.
Its deliverable is a source-grounded prospect queue for scientific review.

Download this repository, open it in your coding agent, and say:

> Follow AGENTS.md. Inspect the available system and model access, recommend one
> configuration, agree a resource allowance with me, and start a bounded run.

The agent handles configuration and evaluation work. You do not need to compare
every model in the candidate catalog or label a new benchmark.

## Start

Python 3.9 or newer is required. From this directory:

```sh
python3 bootstrap.py
.venv/bin/python -B -m sweep doctor --output workspace/inventory.json
```

On Windows, use `.venv\Scripts\python.exe` instead of `.venv/bin/python`.
Bootstrap creates an isolated environment and installs the pinned dependencies.
It does not call a model, purchase credits, or start a literature run. The
inventory records hardware, installed tools and observable access facts without
printing credentials. Unknown model access or quotas stay unknown.

The default plan uses agent work exchange, which works with Codex, Claude Code,
OpenClaw or another agent able to read files and run these commands:

```sh
.venv/bin/python -B -m sweep plan --preset manual --output workspace/plan.json
```

Review the recommendation and resource allowance with the user. Choose manual
exchange or one of the automatic options below. After authorization, record the
agreement in the chosen plan. For manual exchange:

```sh
.venv/bin/python -B -m sweep plan --preset manual --authorize --output workspace/plan.json
```

`--authorize` records permission already given; it is not a substitute for it.
Plans default to a small commissioning allowance, not a budget for a full sweep.
The supervising agent should use that allowance to check actual source-reading
trails against the scientific gates, inspect failures and measure throughput.
The default is 20 admitted calls. Before expanding, the agent reports what those
checks establish and proposes a larger allowance; the user need not label a
benchmark or evaluate the model catalog.

## Automatic model workers

Codex and Claude have separate subscription adapters. The selected model and
reasoning settings are recorded explicitly; the pipeline does not switch to API
billing when subscription access fails.

For Claude Code, first confirm that **Usage credits / extra usage are disabled**
in the account's Usage settings if the run is subscription-only. The adapter
cannot establish that account setting from the CLI. After authorizing the plan:

```sh
.venv/bin/python -B -m sweep plan --preset claude --authorize \
  --claude-extra-usage-disabled --workers 2 --max-calls 20 \
  --max-seconds 3600 --output workspace/plan.json
```

This preset requests Haiku 5.5 at medium effort for screening and Opus 5.5 at high
effort for reading and independent checks. It is a commissioning configuration,
not a scientific qualification claim. Claude Code 2.1.293 or newer is required.
The Claude adapter has automated simulated-CLI tests; live account behavior and
scientific quality must be checked on the recipient's available installation.

The analogous Codex preset is `--preset codex`. It requests Luna/medium for
titles, Sol/medium for abstracts and Sol/xhigh for reading and checks, with the
tested `source-only-v1` context to reduce repeated harness instructions. These
are the final configurations exercised in bounded development checks, not a
general ranking of model ability. Custom profiles remain supported and can
explicitly select `codex_context: standard`. Model availability is account-dependent.
See [EXECUTION.md](EXECUTION.md) for custom profiles, local endpoints, budget
semantics and the task-specific qualification workflow. Official integration
references are in [sweep/provider_docs.json](sweep/provider_docs.json).
The candidate catalog nominates configurations using scientific fidelity,
source grounding, rescue behavior, null interpretation, reliable structured
completion and measured resource use. It does not rank every model on a claimed
universal quality score. The agent recommends the least costly available
configuration that passes the checks for its role.

Once the selected plan is ready, initialize a fresh run:

```sh
.venv/bin/python -B -m sweep init --plan workspace/plan.json --run-id first-sweep
```

The plan becomes immutable for that run. To change models or execution settings,
create a separately configured run with a new ID; overwriting the external plan
file does not change an existing run.

## Work from a corpus

Supply UTF-8 JSONL or CSV, one logical work per row. Each row needs a title;
include DOI, authors, year, abstract and full-text locations where available.
JSONL supports nested fields directly. Keep local configuration, corpora and
source inputs under `workspace/` or outside the downloaded repository. Relative
source paths are relative to the corpus file. CSV arrays use JSON strings.

```json
{"title":"Study title","doi":"10.1234/example","authors":["A. Researcher"],"year":2020,"abstract":"Article abstract","provided_paths":[{"path":"papers/article.pdf","role":"main"},{"path":"papers/supplement.pdf","role":"supplement","association_reason":"Publisher-provided supplement for this article"}]}
```

This is a format example, not a paper or expected scientific decision. A missing
abstract does not exclude a work. Duplicate encounters retain their provenance.
Supplied source bytes are copied into the run and bound by hash before reading.

```sh
.venv/bin/python -B -m sweep ingest --run-id first-sweep --input workspace/corpus.jsonl
.venv/bin/python -B -m sweep close-intake --run-id first-sweep
.venv/bin/python -B -m sweep run --run-id first-sweep
.venv/bin/python -B -m sweep status --run-id first-sweep
.venv/bin/python -B -m sweep estimate --run-id first-sweep
```

With manual profiles, the agent repeatedly requests a task, reads its complete
prompt and source packet, writes a JSON response matching its schema, and submits
it. The returned task directory contains the exact instructions and identifiers:

```sh
.venv/bin/python -B -m sweep work --run-id first-sweep
.venv/bin/python -B -m sweep submit --run-id first-sweep \
  --job-id JOB_ID --input RESPONSE_PATH --actor AGENT_AND_MODEL
.venv/bin/python -B -m sweep run --run-id first-sweep --local-only
```

Replace the uppercase placeholders with returned values. `--local-only` prevents
automatic model dispatch; retrieval may still access public scholarly sources.
The agent's own subscription/API consumption is external to that command and
must follow the user's allowance.

Repeat the work/submit/run cycle until the available tasks are handled. At a
quiet checkpoint after workers finish, validate the saved run and regenerate the
review pages:

```sh
.venv/bin/python -B -m sweep validate --run-id first-sweep
.venv/bin/python -B -m sweep deliver --run-id first-sweep
.venv/bin/python -B -m sweep status --run-id first-sweep
```

Inspect the validation result; a valid partial run can still have unresolved
work. Validation checks integrity and provenance, not scientific correctness.

## Discover literature

A plan with `"mode": "discovery"` initializes the frozen empirical seeds and
review anchors. For a separate discovery run, have the agent prepare an
authorized configuration using the profile/resource fields in `EXECUTION.md`:

```sh
.venv/bin/python -B -m sweep plan --config workspace/discovery-configuration.json \
  --output workspace/discovery-plan.json
.venv/bin/python -B -m sweep init --plan workspace/discovery-plan.json --run-id discovery-sweep
.venv/bin/python -B -m sweep discovery-init --run-id discovery-sweep
.venv/bin/python -B -m sweep run --run-id discovery-sweep
.venv/bin/python -B -m sweep native-work --run-id discovery-sweep
```

Native work units ask the agent for source-located experiment-group, citation,
earned-function or wave-audit evidence. Submit the requested JSON with
`native-submit --paper-id TASK_ID --input RESPONSE_PATH --actor AGENT_AND_MODEL`.
Here `TASK_ID` may be a paper ID or a returned source/wave task identifier.
These handoffs are agent work, not an assignment for the user to evaluate models.
The supervising agent must keep servicing them. Automatic headless reader
workers do not independently complete every native discovery judgment.

Discovery follows the frozen principal-first, blind-last rules. Retrieval
failures, unresolved identities and resource exhaustion leave obligations open.
A prospect label does not establish citation eligibility or an earned process Y.

## Review and resume

Results accumulate under `runs/RUN_ID/`. Open `delivery/index.html` in a browser
for the reading queue, searchable titles and per-paper decision trails. “Show
all” also displays context and human-declined records. The machine-readable
delivery is `delivery/prospects.jsonl`; `delivery/status.json` records current
limitations, and `delivery/validation.json` records the latest integrity check.
`export` creates auditable snapshots of the operational records. Human decisions
are separate from model judgments:

```sh
.venv/bin/python -B -m sweep human-decision --run-id first-sweep \
  --paper-id PAPER_ID --decision accepted-support --reason "Scientific review reason"
.venv/bin/python -B -m sweep validate --run-id first-sweep
.venv/bin/python -B -m sweep deliver --run-id first-sweep
```

`pause` requests a graceful stop after already-admitted bounded work is saved.
`resume` clears that stop request; invoke `run` again to do more work. Completed
requests and unchanged source assets are reused. A dead-worker recovery requires
explicit process-death evidence; elapsed time alone never permits duplicate
model dispatch.

For a failed model request with a verified terminal receipt, the supervising
agent can explicitly commission one fresh attempt within the remaining run
allowance:

```sh
.venv/bin/python -B -m sweep retry --run-id first-sweep --job-id FAILED_JOB_ID \
  --actor SUPERVISING_AGENT --reason "Why a fresh attempt is warranted"
.venv/bin/python -B -m sweep run --run-id first-sweep
```

The retry keeps the same source, model and settings in a new job. The old failure,
receipt and charged allowance remain intact; a timeout does not prove zero
provider cost. Repeating this command for the same failed job returns the same
successor. Unknown token or cost accounting can still block further dispatch.
An ambiguous live request cannot be retried this way.

Use `run --run-id first-sweep --watch --max-seconds 3600` to wait for deferred
work to become eligible again within a bounded wall-time allowance. Without
`--watch`, an idle runner returns control to the supervising agent. Waiting does
not resolve missing texts, uncertain admissions or required native judgments.

The command-line worker runs while its process and host are available. It does
not install a background service, keep a sleeping laptop awake, or buy remote
compute. A long run needs an operator-managed persistent terminal or supervisor.

## Scope and integrity

[science/PROTOCOL.md](science/PROTOCOL.md) defines the science. The portable
coordinator maintains a separate operational prospect ledger. Its completion
status does **not** certify the frozen native comparison ledger, native CSV
exports, or comprehensive literature coverage. Native certification requires the
unchanged scientific package's registered-run workflow and validators.

The distribution contains static code, instructions, schemas, seed identities
and a model candidate catalog. It excludes historical runs, paper PDFs, private
paths, credentials and evaluation answer keys. Verify it with:

```sh
python3 bootstrap.py --verify-only
```

See [AGENTS.md](AGENTS.md) for the agent contract and [EXECUTION.md](EXECUTION.md)
for operational details and current limitations.
