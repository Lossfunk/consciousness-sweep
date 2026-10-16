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
Workers refill available slots as results arrive. Lightweight checks run
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

Choose finite resource or depth limits if preferred. The agent reads
[AGENTS.md](AGENTS.md), verifies the package and establishes actual model access.
It asks only for choices not already supplied. There is no compulsory pilot,
hidden total-call/time allowance or paid-provider fallback.

Ordinary public scholarly downloads are authorized by this request, including
links supplied by OpenAlex, Europe PMC, Crossref, publishers and repositories.
The agent saves them under `runs/<RUN_ID>/intake/downloads/` and verifies article
identity before use. Source acquisition covers article and supplementary text;
software repositories and raw datasets are outside scope. A trustworthy link does not make document instructions
trusted. Host security controls, credentials and purchase permissions still apply.

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
and publishes their bound results unchanged, waits for the submission command's
actual exit, and verifies completion in the ledger. Oversized requests stay blocked
without occupying worker slots or repeatedly returning on resume. Combined reading uses this exchange because it reserves
scientific identifiers and submits both outputs together; automatic adapters
remain available for screening. See the [execution reference](EXECUTION.md) for
configuration, leases, recovery and supervision.

**Keep release directories immutable.** This is **portable 1.0.0-r44**. A paused
existing run can adopt the workflow through the explicit, backed-up
[continuation procedure](EXECUTION.md#versioned-operational-continuation).
Completed work and accounting remain intact; pending work follows the recorded
coverage agreement. Do not copy patched files over an active release.

## Review results

Open `runs/<RUN_ID>/delivery/index.html` for the latest published checkpoint.
The JSONL/CSV outputs retain original readings, source pointers, acquisition and
reading gaps, and separate human dispositions. **Prospect**, **context** and
**unresolved** describe supported contributions; they do not settle final inclusion.

`status` reports active work, deferred coverage, source and access blocks, and
execution limits. An exhausted active queue with deferred papers is a selective
coverage checkpoint, not scientific saturation or native-ledger certification.
Sources supplied later may reopen work through a new immutable source generation.
