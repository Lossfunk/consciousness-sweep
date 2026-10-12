# Consciousness literature sweep

A portable, resumable literature pipeline for finding studies that help explain
how awareness of an entity X relates to its use by a downstream function Y.
Its deliverable is a source-grounded prospect queue for scientific review.

This repository accompanies **Sushrut Thorat and Paras Chopra,
[Towards a full-stack functionalist theory of consciousness: Identifying its
functional profile](https://arxiv.org/abs/2609.33366)** (2026). The manuscript
sets out the scientific motivation; this repository supplies an agent-assisted
way to extend the literature search and keep an auditable trail of its decisions.

Start with [Quick start](#quick-start-with-a-coding-agent), or read about
[the scientific workflow](#how-the-search-and-screening-work),
[running discovery](#discover-literature), and [reviewing results](#review-and-resume).

## Why this repository exists

A functional account of consciousness needs empirical constraints: what changes
when a system is aware of some information, and what remains possible without
that awareness? The paper approaches this through a specific question:

> For an information-bearing content **X**, does awareness of X change whether,
> or how well, X is used by a mental or bodily process **Y**?

For example, X might be the location of a distracting stimulus and Y the control
of its influence on a later task. The relevant evidence concerns how that
information is used. Simply showing better detection of a more visible stimulus
does not, by itself, answer the functional question. Stronger information can
also improve performance, so awareness, signal strength and the measured use
need to be distinguished.
X can also be internally generated or concern affective or bodily information.
A physiological outcome needs a justified interpretation as a functional use of
X; a bodily change alone is not sufficient.

Manual citation searches identified an initial empirical profile. This pipeline
is intended to find additional studies that those searches may have missed,
including informative differences, preserved capacities and carefully scoped
negative results. Those findings can constrain proposals about the processes
associated with consciousness. They do not, on their own, determine a complete
theory or a unique mechanism.

## What the pipeline produces

The main output is a reviewable collection of **prospects**. Each reading states
what X is, how awareness is assessed, how Y uses X, the decisive source evidence,
the remaining alternative and why the study deserves attention. It also records
which source material was unavailable or left a question unresolved.

The compact reader uses three dispositions:

| Disposition | Meaning |
|---|---|
| **Prospect** | A located, potentially useful contribution warrants scientific review, with its limitations stated. |
| **Context** | The work supplies background or related evidence without an adequate awareness–use comparison for this prospect queue. It can still matter to discovery. |
| **Unresolved** | Missing, ambiguous or conflicting evidence prevents a settled judgment. |

Primary/support/undetermined roles are tentative. A human reviewer decides what
to include in an empirical profile; those decisions are stored separately from
the model's original judgment. A paper can contain several claims with different
dispositions. The queue preserves the actual contribution and its scope rather
than assigning one undifferentiated quality score to a paper.

The software handles retrieval, queues, identifiers, source hashes, budgets,
parallel workers, checkpointing and exports. A supervising coding agent reads
the protocol, manages execution and resolves the scientific discovery tasks.
It is an agent-operated research workflow, not an unattended command that
automatically certifies a finished systematic review.

## How the search and screening work

1. **Start from the frozen bibliography.** Index the empirical seeds and
   review/discovery anchors without treating prior inclusion as an answer key.
2. **Find related literature.** Search references and citing papers. Eligible
   empirical nodes continue citation expansion; strict near-neighbors have a
   bounded one-hop bridge route. Independently established functions can activate
   function-specific searches.
3. **Screen titles, then abstracts.** Titles exclude only clear irrelevance.
   Abstracts retain plausible comparisons, supporting evidence and useful
   discovery connections. Missing detail is not treated as demonstrated absence;
   uncertainty advances to full text. Scientific abstract exclusions receive a
   fresh source-only review, and current exclusions are audited under the protocol.
4. **Acquire and read full texts.** Retrieve accessible sources, verify their
   identity, extract source-located text, include available relevant supplements,
   and assess the concrete experimental claim.
5. **Check wider coverage.** Once the principal frontiers provisionally finish,
   execute the mandatory supplementary search families on OpenAlex and Europe
   PMC. New eligible papers or functions reopen the relevant searches.
6. **Deliver and continue.** Save provisional prospects and their decision trails
   at validated checkpoints. Stop only at the agreed resource/depth boundary or
   when the applicable search obligations are satisfied; these are distinct states.

The fourteen supplementary coverage families are defined in
[science/queries.md](science/queries.md). They include affective and bodily
domains and are coverage checks, not an exhaustive taxonomy of consciousness or
a whitelist of acceptable functions. Full discovery and stopping rules live in
[science/PROTOCOL.md](science/PROTOCOL.md).

At full text, the reader aligns the content X with the actual awareness measure
and a defensible downstream function Y. It checks the reported awareness result,
the comparability of the conditions, the possible explanation by differences in
information strength, and the actual outcome. Physical stimulus matching alone
does not guarantee equal internal evidence. A useful support can have incomplete
control, but naming a confound does not turn an otherwise uninformative contrast
into a contribution. Supporting experiments and supplements must be integrated
with an explicit reason that their evidence applies.

Graded awareness and informative null results are allowed. Bayesian analyses are
not mandatory. A nonsignificant result is not automatically equivalence, and
successful processing without awareness does not automatically show equal
performance with awareness. The reader states the supported claim before its
tentative role; [science/PROTOCOL_BRIEF.md](science/PROTOCOL_BRIEF.md) gives a
short guide to the detailed scientific rules.

## Starting literature

The frozen seed scope covers the 60 logical works in the manuscript v2
bibliography: 18 empirical seeds and 42 review/discovery anchors. This includes
McCormick (1997), Klein et al. (2007), Dali and Hester (2022), Dali et al. (2023),
Murphy and Bloom (2015), and the contextual Shapiro et al. (1997) reference.
Seeds supply identities for independent reading, without expected evidence tiers.
The seed files freeze the supplied manuscript v2 bibliography; the arXiv version
may lag that manuscript. See [science/seeds_empirical.csv](science/seeds_empirical.csv)
and [science/seeds_reviews.csv](science/seeds_reviews.csv) for the actual identities.

## Quick start with a coding agent

Download the `main` branch using GitHub's **Code → Download ZIP**, or clone it:

```sh
git clone https://github.com/Lossfunk/consciousness-sweep.git
cd consciousness-sweep
```

If repository access is restricted, the operator must first have access through
GitHub. Open the downloaded directory as the coding agent's workspace and say:

> Follow AGENTS.md and README.md. I want a discovery sweep from the supplied
> seeds. Inspect the available system and model access, recommend a configuration
> and a bounded commissioning allowance, and confirm my resource and citation
> depth limits before starting. Manage the screening, native discovery tasks,
> retrieval, checkpoints and prospect delivery yourself. Keep decisions grounded
> in the supplied sources and report anything that needs my scientific judgment.

The agent handles configuration and evaluation work. You do not need to compare
every model in the candidate catalog or label a new benchmark.
At startup you can also specify a citation depth limit, such as “go two citation
hops from the seeds.” The agent expands eligible links automatically within that
limit. Seeds are depth 0; papers reached at the limit are still screened and read.
The run reports further expansion as depth-limited, without claiming saturation.

## Install and choose resources

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

You also need network access for scholarly retrieval and usable access to the
selected model harness. A GPU is not required for subscription-based cloud
workers. Local model endpoints require their own sufficient memory and compute;
the agent inspects what is available instead of assuming it. Check the actual
account allowance before a long run. The pipeline cannot infer unlimited quota
from an installed CLI or silently purchase additional capacity.

Choose **discovery mode** to search outward from the bibliography, or **corpus
mode** to screen a list you already have. `plan` defaults to corpus mode; use
`--mode discovery` explicitly for the literature sweep described above. The
commands below are for the supervising agent to operate; you do not need to
write JSON responses or coordinate workers yourself.

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
review anchors. After agreeing the allowance, this example creates a bounded
Codex commissioning run with two workers, twenty admitted calls, a one-hour
execution-session limit and two citation hops:

```sh
.venv/bin/python -B -m sweep plan --preset codex --mode discovery --authorize \
  --workers 2 --max-calls 20 --max-seconds 3600 --max-citation-depth 2 \
  --output workspace/discovery-plan.json
.venv/bin/python -B -m sweep init --plan workspace/discovery-plan.json --run-id discovery-sweep
.venv/bin/python -B -m sweep run --run-id discovery-sweep
.venv/bin/python -B -m sweep native-work --run-id discovery-sweep --owner AGENT_AND_MODEL
```

These numbers illustrate a small commissioning allowance, not the estimated cost
of a complete sweep. Use `--preset manual` for agent work exchange, or the Claude
preset and account attestation described above. For a custom configuration,
use `plan --config workspace/discovery-configuration.json --mode discovery`
with the profile/resource fields in [EXECUTION.md](EXECUTION.md). Initialization
already creates the seed obligations; `discovery-init` is an idempotent explicit
initialization command when needed.

To commission a depth-bounded run, add `--max-citation-depth 2` to `plan`, or
set `resources.max_citation_depth` in the configuration. Omit it or use JSON
`null` for no depth cap; `0` limits citation discovery to the initial roots.
Independent process/blind-query results start their own labeled citation roots,
so query-origin depth is kept distinct from distance to the manuscript seeds.
The status output and review page show any deferred expansion. Those obligations
remain open and prevent a false saturation or completion claim. The selected
depth limit is part of the saved plan; resume uses the same limit.

Native work units ask the agent for source-located experiment-group, citation,
earned-function or wave-audit evidence. Submit the requested JSON with:

```sh
.venv/bin/python -B -m sweep native-submit --run-id discovery-sweep \
  --paper-id TASK_ID --input RESPONSE_PATH --actor AGENT_AND_MODEL
```

Here `TASK_ID` may be a paper ID or a returned source/wave task identifier.
These handoffs are agent work, not an assignment for the user to evaluate models.
The supervising agent must keep servicing them. Automatic headless reader
workers do not independently complete every native discovery judgment.
The agent must follow the returned task's owner/lease-token submission contract;
preserve the returned `native_lease` in the response JSON and use the same owner
as `--actor`. It must not invent identifiers or submit another worker's leased task.

Discovery follows the frozen principal-first, blind-last rules. Retrieval
failures, unresolved identities and resource exhaustion leave obligations open.
A prospect label does not establish citation eligibility or an earned process Y.

## Full texts, missing sources and article versions

Acquisition uses supplied local files, Europe PMC full-text XML, available PDF
or open-access locations, and OpenAlex fallback information. Available linked
or explicitly supplied supplements are associated with their main article.
The pipeline verifies source identity and stores immutable source hashes so
later judgments can be traced to the version actually read.

Some papers will remain inaccessible, unreadable, or incomplete. Paywalls,
missing supplements and figure-only evidence can require agent investigation or
a user-supplied copy. These are recorded gaps, not automatic scientific
exclusions. To supply a main article and supplement, create a JSON array such as
`workspace/source-set.json` with paths relative to that file:

```json
[
  {"path":"papers/article.pdf","role":"main"},
  {"path":"papers/supplement.pdf","role":"supplement","association_reason":"Publisher-linked supplement for this article"}
]
```

Then have the agent attach the complete main/supplement set to the existing ID:

```sh
.venv/bin/python -B -m sweep source --run-id discovery-sweep --paper-id PAPER_ID \
  --manifest workspace/source-set.json --reason "Previously missing full text supplied"
.venv/bin/python -B -m sweep run --run-id discovery-sweep
```

Clear duplicate identities are deduplicated while all discovery encounters are
preserved. Different DOIs, preprints and revised versions can remain separate
with possible-version or duplicate links. The pipeline surfaces those
relationships for adjudication; it does not automatically decide that every
preprint is interchangeable with its published version. Unresolved versions
must not count as independent corroborating studies.

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

The code and reader were checked before handoff with 302 software tests,
23 live full-text readings and four boundary-case repeats. A separate three-call
check passed all 13 expected useful papers through the deployed title and
abstract stages into the retrieval queue. Complete-cycle and recovery tests use
controlled fixtures; earlier live commissioning exercised discovery through
depth two. These checks establish bounded execution and known-paper retention.
They do not measure exhaustive recall, establish live Claude equivalence, or
substitute for reviewing new prospects. Evaluation papers and answer keys are
kept out of this downloadable package.

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

Read the prepared commissioning procedure in [EXECUTION.md](EXECUTION.md) before
launching a large sweep. Setup and verification do not start a search or model
call. A time limit or exhausted allowance creates a resumable checkpoint, not a
claim that the literature has been exhausted.

## Repository guide

| Path | Purpose |
|---|---|
| [AGENTS.md](AGENTS.md) | Startup, execution, evidence and handoff responsibilities for the supervising agent. |
| [CLAUDE.md](CLAUDE.md) | Claude Code entry instructions, referring to the same scientific and execution contracts. |
| [EXECUTION.md](EXECUTION.md) | Configuration, model adapters, resource accounting, discovery tasks and recovery details. |
| [science/PROTOCOL.md](science/PROTOCOL.md) | Authority on scientific eligibility, evidence interpretation, discovery and stopping. |
| [science/PROTOCOL_BRIEF.md](science/PROTOCOL_BRIEF.md) | Short scientific reading and discovery guide. |
| [science/queries.md](science/queries.md) | Frozen query families and search windows. |
| [sweep/](sweep/) | Portable coordinator, adapters, acquisition, storage and delivery code. |
| [runtime/source_reader/](runtime/source_reader/) | Compact reader contract; deployed clarification also lives in `sweep/reading.py`. |
| `workspace/` | Local plans, optional corpus inputs and supplied files; ignored by Git. |
| `runs/RUN_ID/` | One run's ledger, jobs, sources, receipts and review outputs; ignored by Git. |
| [DISTRIBUTION_MANIFEST.json](DISTRIBUTION_MANIFEST.json) | Hashes of the distributed static files. |

Keep each independent sweep's data and judgments separate. Changing a frozen
scientific input or model configuration requires a separately configured run;
do not edit a running experiment into a different one. For the scientific
motivation and manuscript citation, use the
[arXiv paper](https://arxiv.org/abs/2609.33366).
