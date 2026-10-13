# Consciousness literature sweep

A portable, resumable literature pipeline for finding studies that help explain
how awareness of an entity X relates to its use by a downstream function Y.
Its deliverable is a source-grounded prospect queue for scientific review.

**Current release: portable 1.0.0-r21**, for supervised use. This revision repairs
retrieval starvation observed in a paused run: fresh work and supplied local
sources receive reserved turns, and repeated failures retain endpoint history
with increasing retry delays. Scientific files and reader instructions are
unchanged. See [Scope and integrity](#scope-and-integrity) for the engineering
checks and source-reading evidence.

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

> Run the sweep.

Keep that release directory for the lifetime of its runs. Download updates into
a new directory; do not pull changed code or instructions into an active run.
Existing runs retain their original package, sources and recorded configuration.
This release does not migrate existing runs. A run paused under an earlier
runtime needs an explicit, reviewed continuation mechanism before it can use
the scheduler repair; replacing its files and resuming is unsupported.

The agent reads the repository instructions, inspects the machine and its active
harness/model access, recommends workers and stage profiles, and asks once about
missing resource and citation-depth choices. You can give those choices up front:

> Run the sweep with unbounded citation depth. Use my existing subscription until
> completion, without extra charges. Use available local resources sensibly.

There is **no mandatory test sweep or hidden 20-call/one-hour allowance**. The
first real retrievals and model calls verify operational access while doing
useful work. Empirical seed papers are read through the deployed gates and their
results checked for source-grounded discrepancies as part of the actual run.
The agent reports meaningful problems and work needing scientific judgment.

A citation limit such as “two hops” is also supported. Seeds are depth 0; papers
at the limit are still screened and read. Further expansion remains visibly
deferred. **Unbounded** means no hop cutoff: continue until the protocol's search
frontiers satisfy their stopping rules, including required supplementary routes.
It does not mean that provider quotas or the protocol's query windows disappear.

## Install and choose resources

Python 3.9 or newer is required. From this directory:

```sh
python3 bootstrap.py
.venv/bin/python -B -m sweep doctor --output workspace/inventory.json
```

On Windows, use `.venv\Scripts\python.exe` instead of `.venv/bin/python`.
Bootstrap creates an isolated environment and installs pinned dependencies.
Doctor inventories CPU/RAM, disk, supported GPUs, tools and observable access
without inference or printing credentials. The supervising agent can supply
known session facts with `--harness codex` or `--harness claude`, `--model ID`,
`--effort LEVEL`, and repeated `--available-model ID` flags. Availability and
scientific qualification remain separate; unknown quota is recorded as unknown.
An installed Codex CLI never takes precedence over a known active Claude session.

Network access is needed for literature retrieval. A GPU is not required for
subscription cloud workers. If local models are selected, the agent checks their
actual memory/compute requirements. The agent recommends concurrency and obtains
any missing resource authorization; it does not rent hardware or purchase quota.

`plan` defaults to **discovery mode**, searching from the supplied bibliography.
Use `--mode corpus` for a supplied list. The commands are for the supervising
agent; the user need not manage JSON responses or worker queues.

For work exchange through the current agent (Codex, Claude Code, OpenClaw or
another agent that can operate these commands):

```sh
.venv/bin/python -B -m sweep plan --preset manual --authorize \
  --max-citation-depth unbounded --output workspace/plan.json
```

`--authorize` records permission already given. Omitted call/time limits mean
no operator-imposed total cap; finite `--max-calls N` and `--max-seconds N` remain
available. `--max-calls unbounded` and `--max-seconds unbounded` explicitly clear
those limits in a configuration. Subscription/provider exhaustion creates a
checkpoint; it never silently enables paid fallback or claims the search finished.
Hosted APIs still require explicit spending ceilings.

## Automatic model workers

Codex and Claude have separate subscription adapters. The selected model and
reasoning settings are recorded explicitly; the pipeline does not switch to API
billing when subscription access fails.

For Claude Code, confirm that **Usage credits / extra usage are disabled** for
subscription-only runs. The adapter cannot discover that account setting.
After permission is established, the agent substitutes the exact observed model
ID and supported effort into this example:

```sh
.venv/bin/python -B -m sweep plan --preset claude --model EXACT_MODEL_ID \
  --effort SUPPORTED_EFFORT --authorize --claude-extra-usage-disabled \
  --max-citation-depth unbounded --output workspace/plan.json
```

For Codex, use `--preset codex --model EXACT_MODEL_ID --effort SUPPORTED_EFFORT`.
Automatic presets pin the supplied model for every stage; a configuration file
can choose different available models for title, abstract, rescue and reading.
`--preset auto` (the default) uses the active host context when sufficient facts
are known, otherwise current-agent work exchange. It never invents access to a
model from a provider catalog. `doctor` can recommend the tested Luna/medium
and Sol/medium screening split when the host reports those exact models available.
The Codex adapter retains `source-only-v1` context; custom profiles may explicitly
select `codex_context: standard`.

The Claude adapter requires a supported CLI version (currently 2.1.293 or newer).
Its transport has simulated-CLI coverage; this does not establish live Claude
scientific equivalence. Check real seed decisions against their source evidence
and flag discrepancies, rather than requiring a preliminary benchmark on every
machine. An optional preauthorized `calibration_review_profile` in a custom plan
allows a stronger independent source-only reread when such a flag needs review.
The original reader result remains unchanged; agreement with an expected tier is
not enough to clear the scientific issue.

See [EXECUTION.md](EXECUTION.md) for custom profiles, local endpoints, accounting,
seed checks and recovery. Official integration references are in
[sweep/provider_docs.json](sweep/provider_docs.json). Candidate catalogs nominate
models; they do not establish account access or universal scientific quality.

Once the selected plan is ready, initialize a fresh run:

```sh
.venv/bin/python -B -m sweep init --plan workspace/plan.json --run-id first-sweep
```

The plan becomes immutable for that run. To change models or execution settings,
create a separately configured run with a new ID; overwriting the external plan
file does not change an existing run. A predeclared calibration review profile
is a separate adjudication route, not a silent replacement of the reader.

## Work from a corpus

Initialize a plan with `--mode corpus` for this workflow. Supply UTF-8 JSONL or
CSV, one logical work per row. Each row needs a title;
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

With manual profiles, the agent repeatedly requests a task. An `agent-task`
response supplies its full prompt, source packet, schema and identifiers; the
agent writes and submits the requested JSON. In discovery mode, `work` also
returns `agent-native-task` responses with a native contract and lease, which
use `native-submit` instead. Check the returned status before dispatching:

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
work. Validation checks integrity and provenance, not scientific correctness. During
execution, `sanity --run-id first-sweep` performs a smaller incremental check;
`calibration-report --run-id first-sweep` shows the seed-reading comparison and
any review flags. Neither a matching label nor valid metadata proves scientific
correctness.

## Discover literature

A discovery plan initializes the frozen empirical seeds and review anchors.
After confirming resources and depth once, this example starts the actual sweep
through the current agent, without a total call/time or citation-depth cap:

```sh
.venv/bin/python -B -m sweep plan --preset manual --mode discovery --authorize \
  --max-citation-depth unbounded --output workspace/discovery-plan.json
.venv/bin/python -B -m sweep init --plan workspace/discovery-plan.json --run-id discovery-sweep
.venv/bin/python -B -m sweep run --run-id discovery-sweep
.venv/bin/python -B -m sweep work --run-id discovery-sweep
```

Choose an automatic adapter with the exact model/effort options above when useful,
or use `plan --config workspace/discovery-configuration.json` for stage-specific
profiles. Initialization already creates seed obligations; `discovery-init` is an
idempotent explicit initialization command when needed. Automatic workers and the
supervising agent's native discovery work should proceed concurrently within the
agreed resource allowance. The agent must keep servicing both kinds of work;
the runner cannot invent source-based native scientific judgments. Search fetching
slows temporarily when the pending paper buffer is full, while screening/reading
continues; this is queue management, not a cap on papers discovered. Small pending
screening jobs are combined up to their stage limits, and unfinished batch tails
still proceed. Agent work exchange alternates native and model work when both are
ready. Periodic incremental sanity checks flag bookkeeping problems early.

To limit depth, use `--max-citation-depth 2` or set `resources.max_citation_depth`
in the configuration. `unbounded` on the CLI or JSON `null` means no cap;
`0` limits citation expansion to the roots while still reading them.
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

Acquisition reserves turns for priority work, supplied local sources, fresh
retrievals, retries and other ready acquisition-worker tasks. Repeated seed
failures cannot monopolize service across priorities. Retrieval attempts and
receipts are counted separately from model calls. Transient failures use
increasing delays from one minute to one hour, honoring longer valid server
retry instructions. While retrying transient endpoints, unchanged blocked or
unreadable endpoint outcomes are reused for up to 24 hours. A new source
generation starts fresh endpoint history; prior attempts remain recorded.
These delays do not discard missing-source obligations or impose an attempt cap.

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
`resume` clears that stop request; invoke `run` again to do more work. Authentication/configuration failures require an explicit
resolution after the problem is fixed: `resume --run-id first-sweep
--resolve-access-blocks --reason "Describe the fix"`. Confirmed nonadmission
can then be checked again under the same settings; uncertain charged failures
still use the separate retry workflow. Completed
requests and unchanged source assets are reused. A dead-worker recovery requires
explicit process-death evidence; elapsed time alone never permits duplicate
model dispatch.

To pause and later continue the same run:

```sh
.venv/bin/python -B -m sweep pause --run-id first-sweep
# Later, from the same release directory:
.venv/bin/python -B -m sweep resume --run-id first-sweep
.venv/bin/python -B -m sweep run --run-id first-sweep
.venv/bin/python -B -m sweep status --run-id first-sweep
```

Resume preserves the saved plan, remaining allowance and original finite total
deadline; it does not renew the allowance. With manual profiles, the supervising
agent continues the work/submit/native-submit cycle described above.

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

Use `run --run-id first-sweep --watch` to wait for deferred work. An optional
`--max-seconds N` creates an operational checkpoint; it is not required. Without
`--watch`, an idle runner returns control to the supervising agent. Waiting does
not resolve missing texts, uncertain admissions or required native judgments.

The command-line worker runs while its process and host are available. It does
not install a background service, keep a sleeping laptop awake, or buy remote
compute. A long run needs an operator-managed persistent terminal or supervisor.

## Scope and integrity

The **13 October 2026 maintainer audit** supports supervised handoff without
requiring a full scientific sweep as a commissioning step. Its evidence separates
engineering behavior from scientific reading quality:

- **Packaged software:** 480 tests passed against r21 with zero skips,
  errors or failures. They cover startup, finite and unbounded settings, durable
  access/budget blocks, crashes, competing and stale workers, source revisions,
  calibration review, stopping and reopening. The earlier r19/r20 suites had
  431 tests; the 49 added regressions cover the reported retrieval starvation,
  endpoint cooldown/history, acquisition accounting, and refusal of incompatible
  resumes before database mutation. The incident was reproduced with controlled
  failures plus actual extraction of a synthetic local PDF. No additional live
  model readings were needed for this operational repair.
- **Offline scale:** 2,500 logical papers and 5,000 encounters exercise concurrent
  persistence, 100 screening batches, 2,500 retrieval obligations and backpressure
  over 1,000 citation obligations. Downstream drain is a synthetic fixture, not
  a claim that those papers were retrieved or read. A separate complete finite
  workflow exercises actual coordinator/extraction/delivery code using controlled
  source and model responses, including new work after exhaustion and restart.
  These tests overlap the packaged suite and must not be added to its count.
- **Real sources and fresh readers:** the initial diagnostic used seven of eight
  authorized calls (four screening and three full-text readings). The extension
  used nine of fourteen further authorized calls, all fresh full-text readings.
  Public retrieval, source-version changes, missing texts and manual extraction
  were exercised. Eleven of the thirteen positive-baseline papers have fresh
  readings and retain a qualified prospect; source-integration gaps and
  claim-level disagreements remain explicit. Missing mains/supplements are
  untested evidence, not reader failures or an instruction to force agreement.

The latest reader calls used fresh source-only workers in the active Codex
harness, with no paid API fallback. Exact backend identity was unverified, and
manual calls were counted separately from automatic budget telemetry. Live
Claude/custom-provider paths, clean-machine installation, Windows and network
filesystems were not exercised. These boundaries do not create a compulsory
test sweep; the supervising agent still establishes actual access and follows
the user's resource choices on each new run.

No full sweep was launched during this audit. Scientific gates, reader prompts,
seeds and calibration expectations remain unchanged. Earlier reading and
screening checks remain historical evidence; their counts are not added to the
latest diagnostics or treated as an exhaustive recall estimate. Development
runs and paper PDFs are excluded from the distribution. The versioned
seed-calibration reference is coordinator-only and never supplied to readers.

[science/PROTOCOL.md](science/PROTOCOL.md) defines the science. The portable
coordinator maintains a separate operational prospect ledger. Its completion
status does **not** certify the frozen native comparison ledger, native CSV
exports, or comprehensive literature coverage. Native certification requires the
unchanged scientific package's registered-run workflow and validators.

The distribution contains static code, instructions, schemas, seed identities
and a model candidate catalog. It excludes historical runs, paper PDFs, private
paths and credentials. Its coordinator-only seed-calibration reference records
expected contributions and limitations; reader prompts never include it. Verify it with:

```sh
python3 bootstrap.py --verify-only
```

See [AGENTS.md](AGENTS.md) for the agent contract and [EXECUTION.md](EXECUTION.md)
for operational details and current limitations.

Use the startup and ongoing checking procedures in [EXECUTION.md](EXECUTION.md).
A separate diagnostic is optional and requires its own purpose and allowance;
ordinary startup immediately proceeds to real seed/discovery work. Setup and
verification do not start a search or model call. A time limit or exhausted allowance creates a resumable checkpoint, not a
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
