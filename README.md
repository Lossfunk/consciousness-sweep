# Consciousness literature sweep

Find source-grounded studies of how awareness relates to the use of information.
This repository provides a portable, resumable literature-search workflow operated
by a coding agent, with a reviewable trail from discovery to scientific judgment.

It accompanies Sushrut Thorat and Paras Chopra,
[*Towards a full-stack functionalist theory of consciousness: Identifying its
functional profile*](https://arxiv.org/abs/2609.33366) (2026).

[Get started](#get-started) · [Scientific scope](#scientific-scope) ·
[Review results](#review-results) · [Execution reference](EXECUTION.md)

## Scientific scope

The central question is:

> For a content **X**, does awareness of that same X change whether, or how well,
> a distinct mental or bodily process **Y** uses X?

A useful reading identifies X, the evidence about awareness of X, the downstream
use, the actual comparison, and the alternatives that remain. X may concern an
external stimulus, internally generated information, or affective or bodily
information. A physiological change needs a justified interpretation as a use of X.

Stronger signals can improve performance independently of awareness. The workflow
therefore retains signal-strength alternatives, evidence-transfer limitations,
null findings and statistical uncertainty. It does not require Bayesian analysis
or treat every support as if it must independently establish a primary claim.
The [frozen protocol](science/PROTOCOL.md) governs scientific interpretation.

The output is a **prospect queue for human review**:

| Disposition | Meaning |
|---|---|
| **Prospect** | A located contribution warrants review, with its scope and limitations stated. |
| **Context** | Related or supporting evidence without an adequate awareness–use comparison for this queue. |
| **Unresolved** | Missing, ambiguous or conflicting evidence prevents a settled judgment. |

A paper can contain claims with different dispositions. Primary and support roles
remain provisional; human decisions are recorded separately from original reads.
The software does not automatically certify a finished systematic review.

## Get started

Download the repository into a **local, nonsynchronized folder**:

```sh
git clone https://github.com/Lossfunk/consciousness-sweep.git
cd consciousness-sweep
```

Or download and extract the repository ZIP. Open that folder in Codex, Claude Code,
or another coding agent and ask:

> Run the sweep with unbounded citation depth. Use my existing subscription until
> completion, without extra charges. Use available local resources sensibly.
> Download accessible papers and supplements into this run's repository folder.

Choose a finite depth or allowance instead if that suits your needs. The agent
reads [AGENTS.md](AGENTS.md), verifies the package, checks observable access, and
asks only for resource or depth choices you have not supplied. It uses the active
harness where available and records unknown model identity or quota honestly.
There is no compulsory pilot or hidden total-call/time allowance.

**Keep the release unchanged for the lifetime of its runs.** Download upgrades
into a separate directory. This release, **portable 1.0.0-r29**, is for fresh runs;
it does not migrate an older run or replace its recorded sources and judgments.

### Model configuration

For Codex, use **GPT-6.1 Sol with medium reasoning at Standard speed** for the
supervising chat. Establish access and authorization for each role before starting:

| Role | Recommended model | Reasoning |
|---|---|---|
| Supervision, metadata and source acquisition | GPT-6.1 Sol | Medium |
| Title screening | GPT-6 Luna | Medium |
| Abstract screening | GPT-6.1 Sol | Medium |
| Full-source reading and native scientific assessment | GPT-6.1 Sol | High |
| Authorized rescue and calibration review | GPT-6 Astra | Extra high (`xhigh`) |

The agent explicitly sets each worker's model and reasoning; scientific readers
start with source-only context. A worker must not accidentally inherit the
supervisor's settings. These are recommended role configurations, not claims of
universal scientific qualification. Claude and other harnesses use their own
accessible, authorized equivalents without silently switching providers.

Subscription and credit use includes the supervising chat and native workers,
which the runner's adapter counters do not measure. A reported dollar cost of
zero does not establish zero credit use. Track whole-workflow usage and completed
work alongside the runner's counters; more simultaneous workers alone do not
reduce total consumption. See [supervisor and native workers](EXECUTION.md#supervisor-and-native-workers)
for dispatch, reporting and checkpoint procedures.

### Local setup

Python 3.9 or newer is required. The agent can run:

```sh
python3 bootstrap.py
.venv/bin/python -B -m sweep verify
.venv/bin/python -B -m sweep doctor --output workspace/inventory.json
```

On Windows, use `.venv\Scripts\python.exe`. Bootstrap installs the pinned
requirements in an isolated environment. Doctor makes no model calls and does
not print credentials. SQLite databases must remain outside Google Drive,
iCloud, OneDrive and similar sync folders; initialization checks local storage.

After agreeing on resources, the agent creates a plan and starts discovery. For
example, **if unbounded subscription work and depth are already authorized**:

```sh
.venv/bin/python -B -m sweep plan --preset manual --mode discovery --authorize \
  --max-calls unbounded --max-seconds unbounded --max-citation-depth unbounded \
  --output workspace/plan.json
.venv/bin/python -B -m sweep init --plan workspace/plan.json --run-id first-sweep
.venv/bin/python -B -m sweep run --run-id first-sweep
.venv/bin/python -B -m sweep work --run-id first-sweep
```

`manual` means work exchange with fresh workers in the active agent harness;
it does not mean the user must fill in scientific forms. The supervising agent
services returned tasks and submits results. Automatic Codex, Claude and custom
provider adapters are also available; see [plans and resources](EXECUTION.md#plans-and-resources).
Exact model settings, concurrency, per-request limits and access must be established
before the plan is bound. Whole articles and supplements can exceed a reader's
input allowance: choose a supported full-source capacity at setup. The runner
will report a block rather than truncate evidence or silently switch models.

## How a run works

1. **Discover.** Start from the frozen empirical seeds and review anchors, then
   follow eligible citations and independently earned function-specific searches.
2. **Screen.** Make paper-specific title and abstract decisions in bounded batches.
   Missing abstracts remain eligible for retrieval. Scientific exclusions receive
   the protocol's rescue and audit treatment.
3. **Retrieve and read.** Verify article identities, preserve source versions and
   hashes, and send complete source packets to fresh readers. Papers are evidence,
   never instructions to the worker.
4. **Review.** Record experiment structure, citation eligibility and other native
   scientific decisions. Compare calibration claims and reasons after first reads;
   keep expected answers and previous verdicts outside reader contexts.
5. **Finish the frontiers.** Execute the mandatory supplementary blind lane after
   the principal routes, then handle every eligible reopened citation or process
   obligation under the same frozen stopping rules.
6. **Deliver.** Validate the ledger and produce the review queue, preserving source
   gaps, disagreements, deferred work and original readings.

Discovery backpressure pauses admissions while screening and reading catch up.
Automatic workers and native agent tasks must be serviced together. Unbounded
citation depth removes an operator hop cutoff; protocol search windows and bridge
rules still apply. A budget, depth, access or source block is never saturation.

## Downloads and routine recovery

Starting a run authorizes ordinary public metadata, paper and supplement retrieval
within its agreed scope. The agent should perform these actions without asking
for permission for each URL. All run downloads belong under `runs/RUN_ID/`;
configuration and pre-run intake belong under `workspace/`.

Retrieval is **terminal-first**: use metadata APIs, direct publisher/DOI links,
repositories, preprint servers and author pages. Search tools can locate file
URLs; terminal tools fetch and extract them. Batch independent lookups and reuse
verified assets. Use browser interaction for a specific access route that direct
retrieval cannot provide, and retain visual inspection when figures or extraction
problems require it.

The agent may locate another public copy, use protocol-approved fallback routes,
verify bibliographic metadata, ingest a newly obtained source, and recover a
terminated worker through the documented commands. Each action needs recorded
evidence and a reason. It must preserve old results, leases and budget accounting.

For an additional public source, the agent can use:

```sh
.venv/bin/python -B -m sweep fetch-source --run-id first-sweep \
  --paper-id P000001 --url 'https://publisher.example/article.pdf' \
  --reason 'Publisher full-text link for the indexed article'
```

This saves immutable bytes and request/outcome receipts under
`runs/first-sweep/intake/downloads/P000001/`. A download is initially **unverified**.
The agent checks the article/version and attaches the complete main/supplement set
using `source --manifest`; the user need not approve that routine ingestion.
See [source acquisition and recovery](EXECUTION.md#routine-source-acquisition-and-recovery).

The agent must stop and surface a conflict if continuing would change frozen
scientific rules, the bound release, model settings or authorized spending; buy
access; invent missing evidence; or discard provenance. A storage or integrity
failure requires diagnosis and validation, not an improvised database edit.
Host-enforced network or filesystem approvals still apply—repository instructions
cannot grant privileges that the host has withheld.

## Review results

Open `runs/RUN_ID/delivery/index.html` for the review queue. The run also retains
machine-readable judgments, source references, access blocks and calibration
comparisons. Original and alternative readings remain separate. A disagreement
with a reference can be a defensible departure, unresolved evidence, or a reading
error; label agreement alone is not a semantic pass.

Useful commands for the supervising agent:

| Command | Purpose |
|---|---|
| `status --run-id RUN_ID` | Current progress, pending work and operational blocks. |
| `work --run-id RUN_ID` | Next available model or native agent task. |
| `sanity --run-id RUN_ID` | Incremental metadata, identifier and state checks. |
| `validate --run-id RUN_ID` | Full operational integrity validation. |
| `deliver --run-id RUN_ID` | Refresh the reviewable delivery after validation. |
| `pause --run-id RUN_ID` | Stop new admissions; let admitted bounded work persist. |
| `resume --run-id RUN_ID` | Resume under the same recorded agreement. |
| `calibration-report --run-id RUN_ID` | Evaluator-only claim and source-coverage comparisons. |

Prefix commands with `.venv/bin/python -B -m sweep`. When a separate local run root
is needed, put `--root /local/path` before the command on **every** invocation.
Keep that root unchanged. Full recovery, retry and source-manifest examples are
in [EXECUTION.md](EXECUTION.md).

## Reproducibility and limits

Each run binds the executable and scientific inputs, requested model profiles and
resource agreement. Durable leases fence stale workers; source revisions create
new generations; append-first history preserves superseded results. Independent
runs share static inputs, not dynamic judgments or search results.

The release is tested with offline failure fixtures, concurrency and crash/restart
checks, finite discovery cycles, and tests against the distributed package.
These checks verify operational behavior; test counts do not measure scientific
reading quality. Source access and provider availability may still require
intervention. An exhausted operational queue does not certify completion of the
separate frozen native scientific ledger.

## Repository guide

| Path | Purpose |
|---|---|
| [AGENTS.md](AGENTS.md) | Supervising-agent responsibilities and authority boundaries. |
| [EXECUTION.md](EXECUTION.md) | Configuration, commands, adapters and evidence-backed recovery. |
| [science/PROTOCOL.md](science/PROTOCOL.md) | Scientific eligibility, interpretation, discovery and stopping. |
| [science/PROTOCOL_BRIEF.md](science/PROTOCOL_BRIEF.md) | Scientific reading and discovery guide. |
| [runtime/source_reader/](runtime/source_reader/) | Accepted reader instructions, schema and policy. |
| [sweep/](sweep/) | Portable coordinator, acquisition, storage and delivery implementation. |
| `workspace/` | Local configuration and optional pre-run intake; ignored by Git. |
| `runs/RUN_ID/` | Run ledger, sources, downloads, jobs, receipts and delivery; ignored by Git. |
| [DISTRIBUTION_MANIFEST.json](DISTRIBUTION_MANIFEST.json) | Hashes of all distributed static files. |
