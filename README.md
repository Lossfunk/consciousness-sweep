# Consciousness literature sweep

Find source-grounded studies of how awareness relates to the use of information.
This portable workflow discovers papers, screens abstracts, retrieves accessible
sources and produces a prospect queue for human review. A durable ledger preserves
sources, decisions, limitations and execution history across pauses and resumes.

It accompanies Sushrut Thorat and Paras Chopra,
[*Towards a full-stack functionalist theory of consciousness: Identifying its
functional profile*](https://arxiv.org/abs/2609.33366) (2026).

[Get started](#get-started) · [How papers move through the sweep](#how-papers-move-through-the-sweep) ·
[Review results](#review-results) · [Execution reference](EXECUTION.md)

## Scientific scope

> For a content **X**, does awareness of that same X change whether, or how well,
> a distinct mental or bodily process **Y** uses X?

Each substantive reading identifies X, evidence about awareness of X, the distinct
use by Y, the actual comparison, and remaining alternatives. Readings retain
signal-strength confounds, transferred evidence, null findings and statistical
limitations. Bayesian analysis is optional; supports need not independently meet
primary-grade controls. Primary and support roles remain provisional.

The scientific rubric and source-reader instructions are frozen. The portable
**focused-v1** workflow uses selective coverage: uncertain abstracts, unavailable
sources and unresolved identities can remain deferred. Exclusions receive one
source-specific decision, and each newly read paper receives one combined
scientific and discovery assessment. This workflow does not claim the exhaustive
coverage or review requirements of a registered run under `science/AGENTS.md`.

## How papers move through the sweep

1. **Discover and deduplicate.** Retain every encounter, including rediscoveries
   of deferred and excluded papers. Uncertain identity matches remain separate.
2. **Screen titles, then abstracts.** Batches contain at most 25 titles or 10
   abstracts, with a reason for every paper. Missing abstracts get one bounded
   lookup through OpenAlex, Europe PMC and Crossref. If unavailable, defer the
   paper. Retain, uncertain and exclude are semantic judgments, without quotas.
3. **Prioritize retained abstracts.** Uncertain abstracts remain in a deferred
   queue for optional later coverage. Unchanged evidence is not repeatedly screened.
4. **Acquire sources once.** Try known locations with per-request timeouts and a
   bounded publisher/public-copy check. Collect the main article and visible supplementary text, including methods,
   results, tables and figures within those documents. Do not download code,
   datasets, simulation outputs or software archives. Record unavailable material
   and move on; do not repeat the hunt.
5. **Read once, substantially.** One fresh source-only worker applies the complete
   rubric and records experiment-level citation eligibility and earned process
   searches. Missing evidence stays unresolved. No automatic second reader is
   commissioned for the same evidence.
6. **Expand eligible nodes.** Full-text CORE and strict BRIDGE decisions govern
   recursion, with the existing bridge lineage, source windows and depth agreement.
   A prospect label alone never authorizes expansion. Deferred papers remain in
   the global deduplication index at every depth.

Discovery pauses admission when active downstream work fills the buffer, including
papers awaiting scientific assessment. When continuing earlier work, native
follow-ups for completed contextual readings use a separate background queue;
outstanding prospects and ready new work take priority. Eligible seed citations,
deeper citations and earned query windows share bounded search admission.
Workers refill available slots as results arrive. A [managed source runner](EXECUTION.md#managed-source-execution)
processes downloaded documents alongside acquisition helpers; exact source holds
leave unrelated work available. Lightweight checks run
incrementally; full validation and delivery occur at coordinated quiet checkpoints.

## Get started

Clone or extract the repository into a **local folder outside cloud-sync services**:

```sh
git clone https://github.com/Lossfunk/consciousness-sweep.git
cd consciousness-sweep
```

Open the folder in Codex, Claude Code or another coding agent and ask:

> Run the focused sweep with unbounded citation depth. Use my existing subscription
> without extra charges. Download accessible papers and supplementary text into this
> run's repository folder, and use available workers within the agreed allowance.

Choose finite resource, citation-depth or indexed-paper limits if preferred. The agent reads
[AGENTS.md](AGENTS.md), verifies the package and establishes actual model access.
It asks only for choices not already supplied. There is no compulsory pilot,
hidden total-call/time allowance or paid-provider fallback.

Ordinary public scholarly downloads are authorized by this request, including
links supplied by OpenAlex, Europe PMC, Crossref, publishers and repositories.
The agent saves them under `runs/<RUN_ID>/intake/downloads/` and verifies article
identity before use. Source acquisition covers article and supplementary text;
software repositories and raw datasets are outside scope. A trustworthy link does not make document instructions
trusted. Host security controls, credentials and purchase permissions still apply.

### Indexed-paper limit

To commission a finite amount of discovery, add:

> Stop new discovery at 10,000 indexed papers, finish search requests already
> underway, then process the admitted papers and deliver the results.

Use any positive count, such as 20,000, or leave it unbounded. The count includes
seeds, review anchors and all indexed papers, including screened-out and deferred
papers. Rediscoveries and source versions do not count again. Already admitted
search responses are preserved whole, so the final count can slightly exceed the
threshold. Screening, acquisition and reading then continue under the chosen
workflow; exclusions, deferred coverage, missing text and held work stay visible.
An indexed-paper limit is an operational endpoint, not scientific saturation.
The same run can later continue with an additional paper allowance, such as
5,000 more. Completed work and the original count remain; an explicit backed-up
agreement raises the threshold. Ordinary resume keeps the existing allowance.
See [stopping thresholds](EXECUTION.md#indexed-paper-stopping-threshold).

### Model configuration

For an authorized Codex setup, use Standard speed and establish access to these
exact role configurations before initialization:

| Role | Model | Reasoning |
|---|---|---|
| Supervisor | GPT-6.1 Sol | Medium |
| Title screening; bounded identity and acquisition work | GPT-6 Luna | Medium |
| Abstract screening | GPT-6.1 Sol | Medium |
| Combined scientific and discovery reading | GPT-6.1 Sol | High |

Other harnesses use their accessible, authorized configurations. Settings must be
explicit; readers do not inherit the supervisor's conversation or calibration
expectations. The retained seed reference is evaluator material. Disagreements
remain visible without compulsory rereads or repeated calibration of fresh workers.

Use the actual harness capacity, not an assumed worker count. Adapter counters do
not include all supervisor or external-worker consumption; report unknown usage
honestly. Concurrency improves throughput when work is ready, but does not make
each reading cheaper.

Title access recovery keeps the preferred model when it works, uses bounded
retries for transient failures, and periodically rechecks availability while an
authorized fallback is in use. Model changes are recorded at quiet checkpoints;
completed work and accounting are preserved. See
[bounded title access recovery](EXECUTION.md#bounded-title-access-recovery).

An unresolved dependency can hold its exact search windows while unrelated
retrieval, reading and citation work continues. Holds remain visible and pending
until explicitly resolved; see [scoped search holds](EXECUTION.md#scoped-search-window-holds).

### Commands

Python 3.9 or newer is required. The agent can run:

```sh
python3 bootstrap.py
.venv/bin/python -B -m sweep verify
.venv/bin/python -B -m sweep doctor --output workspace/inventory.json
```

Record exact stage profiles and the authorized resource agreement in a config,
then initialize a unique run:

```sh
.venv/bin/python -B -m sweep plan --config workspace/config.json --output workspace/plan.json
.venv/bin/python -B -m sweep init --plan workspace/plan.json --run-id first-sweep
.venv/bin/python -B -m sweep run --run-id first-sweep --defer-checkpoint
.venv/bin/python -B -m sweep work --run-id first-sweep
```

On Windows, use `.venv\Scripts\python.exe`. `manual` profiles mean work exchange
with fresh agent workers, not forms for the user. The supervisor services tasks
through a [managed publication and worker exchange](EXECUTION.md#managed-worker-exchange).
Completed answers are committed before new tasks are offered. Durable dispatch
tickets prevent an interrupted supervisor from silently spawning a second reader;
the active harness supplies each fresh worker and its observed execution identity. Oversized requests stay blocked
without occupying slots; [explicit input capacity recovery](EXECUTION.md#explicit-reader-input-capacity)
retains the original request and records any authorized larger allowance. Combined reading uses this exchange because it reserves
scientific identifiers and submits both outputs together; automatic adapters
remain available for screening. See the [execution reference](EXECUTION.md) for
configuration, leases, recovery and supervision.

**Keep release directories immutable.** This is **portable 1.0.0-r72**. A paused
existing run can adopt the workflow through the explicit, backed-up
[continuation procedure](EXECUTION.md#versioned-operational-continuation).
Completed work and accounting remain intact; pending work follows the recorded
coverage agreement. Do not copy patched files over an active release.

## Review results

Open `runs/<RUN_ID>/delivery/index.html` for the latest published checkpoint.
The JSONL/CSV outputs retain original readings, source pointers, acquisition and
reading gaps, and separate human dispositions. **Prospect**, **context** and
**unresolved** describe supported contributions; they do not settle final inclusion.

### Advisory ranking and factor notes

A prospect is a paper with a source-grounded contribution worth reviewing, not an
accepted primary or support at the strength of the reference papers. A paper can
contain useful, contextual and unresolved claims together.

When requested, run the [advisory review exchange](EXECUTION.md#on-demand-advisory-review)
after a quiet delivery checkpoint: at a pause, after an indexed-paper allowance
has drained, or at another agreed review milestone. It uses completed extractions;
it does not commission another full-text reading. Scoring targets only papers whose
existing full-text assessment has `paper_decision: prospect`. Context, unresolved
and unassessed papers receive no scoring jobs. Available fixed references remain
comparison inputs, even if their current paper decision differs; they do not become
extra scoring targets. Nothing runs automatically at
10,000 papers or on every worker completion. Indexed papers without full-text
assessments do not acquire invented scores.

Every ranking request includes the complete frozen evaluator baseline: Tsushima
(2006), Persaud (2011) and Keizer (2015), plus the eight current supports. These
are explicit comparison subjects even when the sweep has not obtained their texts.
The reference facts and coverage come from the approved calibration snapshots;
they never become scientific records or inputs to source-only readers.

One scoring pass produces independent primary/support reference indices and
paper-specific comparability recommendations. Every supplied ID must have an
entry or an explicit unresolved result. The [suggested reading list](EXECUTION.md#reading-list-and-score-interpretation)
separates comparable candidates, qualified leads and unresolved cases, with the
closest reference, focal claim, source pointers and remaining limitations. Known
reference works remain visible but are not presented as new discoveries. A
comparable label unsupported by any at-or-above reference placement is flagged
as borderline; the original model judgment and score remain preserved.

An index counts the fraction of references ranked below a paper, with half-credit
for ties. It is not a percentage of scientific strength or a probability. Even
complete-reference indices are coarse and cohort-dependent; different batches do
not resolve a fine global order. A comparability recommendation considers the
coherent contribution and its credibility, rather than applying a score cutoff.
Explicitly unrankable references leave honest ranges. Original assessments and
reading gaps remain available per entry; factor grades require a separate optional
pass and are never invented. No additional interpretation model is commissioned.

The managed Codex launcher uses a fresh process and supplied inputs, disables
unnecessary capabilities and audits the complete execution log. Acceptance requires
no observed tool calls and a matching final answer; it does not certify an empty
tool registry. Missing or incomplete audit evidence leaves the result unverified.

These outputs never change scientific decisions, discovery eligibility, queues or
stopping. The retained ranking policy is `rank-calibrated-v2`; experimental rubric
revisions are not silently substituted. See [rubric selection and calibration](EXECUTION.md#rubric-selection-and-calibration)
for the reference set, independent judge comparison, held-out results and limits.
Completed unchanged work can be reused at
later checkpoints. Pending or failed scoring leaves papers unscored and does not
block the sweep. Use the existing authorized allowance and shared worker capacity;
no extra billing or provider fallback is implied.

The review command can read an older run's published export from a separate new
release. This does not migrate that run or authorize resuming it under new code.
Keep its active release and ledger untouched.

`status` reports active work, deferred coverage, source and access blocks, and
execution limits. An exhausted active queue with deferred papers is a selective
coverage checkpoint, not scientific saturation or native-ledger certification.
Sources supplied later may reopen work through a new immutable source generation.

## Storage management

Routine checkpoints validate and publish progress without copying the entire
database. Versioned continuation makes one consistent backup. Keep the newest
restore point and the latest continuation backup directly available; they may be
the same file. Use [backup archiving](EXECUTION.md#backup-storage) for older
snapshots. The supported tool verifies lossless compression before
removing an uncompressed backup, preserves its original receipt, and can restore
its exact bytes and path. Sources, readings, charges and the live database remain
unchanged. Never delete run evidence or rewrite the ledger to reduce disk use.
