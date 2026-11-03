# Consciousness literature sweep

Find studies of how awareness relates to the use of information, then deliver an
explained reading list for a researcher. The workflow discovers and deduplicates
papers, screens titles and abstracts, retrieves accessible articles and textual
supplements, and records source-grounded assessments.

It accompanies Sushrut Thorat and Paras Chopra,
[*Towards a full-stack functionalist theory of consciousness: Identifying its
functional profile*](https://arxiv.org/abs/2609.33366).

[Run and review guide](docs/README.md) · [Command reference](EXECUTION.md) ·
[Code map](sweep/README.md) · [Reader contract](runtime/README.md)

## Get started

Clone or extract the repository into a **local folder outside cloud-sync services**:

```sh
git clone https://github.com/Lossfunk/consciousness-sweep.git
cd consciousness-sweep
```

Open the folder in Codex, Claude Code or another coding agent and ask:

> Run the focused sweep with unbounded citation depth. Stop new discovery at
> 10,000 indexed papers, finish requests already underway, then process the
> admitted papers. Use my existing subscription without extra charges. Download
> accessible articles and textual supplements into this run's repository folder.
> Use available workers within the agreed allowance and deliver explained results.

Choose another paper count, a citation-depth limit or an unbounded sweep if preferred.
The agent reads [AGENTS.md](AGENTS.md), verifies the release, establishes actual
model access and asks only for missing resource choices. There is no compulsory
pilot, hidden total-call/time limit or paid API fallback.

Python 3.9 or newer is required. The agent handles setup and ordinary operations:

```sh
python3 bootstrap.py
.venv/bin/python -B -m sweep verify
.venv/bin/python -B -m sweep doctor --output workspace/inventory.json
```

On Windows, use `.venv\Scripts\python.exe`. The [guide](docs/README.md) explains
planning, execution, checkpoints and delivery; the [reference](EXECUTION.md)
contains the complete command options.

## What the sweep asks

> For information **X**, does awareness of that same X change whether, or how well,
> a distinct mental or bodily process **Y** uses X?

Each substantive reading identifies X, its awareness evidence, Y, the actual
comparison and remaining alternatives. It retains signal-strength confounds,
transferred evidence, null results and statistical limitations. Supports need not
meet primary-grade controls; Bayesian analysis is optional.

The scientific rubric and source-reader instructions are frozen. The portable
**focused-v1** workflow is selective: uncertain abstracts, unavailable sources and
unresolved identities can remain deferred. Exclusions receive one source-specific
decision; each newly read paper receives one combined scientific and discovery
assessment. This does not certify an exhaustive registered scientific sweep.

## How work moves

1. **Discover and deduplicate** against the entire index, including deferred papers.
2. **Screen titles and abstracts** with individual reasons, without retention quotas.
3. **Acquire accessible sources once**, using bounded requests and terminal routes first.
4. **Read in a fresh source-only context** and preserve all claims, gaps and limitations.
5. **Expand eligible studies** under the frozen citation/process rules and recorded limits.
6. **Validate and publish a quiet checkpoint** for researcher review.

Ordinary public scholarly downloads are authorized by starting the sweep. The agent
saves them under `runs/<RUN_ID>/intake/downloads/` and checks article/version identity.
Acquisition includes main articles and textual supplements, not code, datasets or
software archives. Purchases, login bypass and new credentials are outside that permission.

## Model configuration

For an authorized Codex setup, the recommended configurations are:

| Work | Model | Reasoning |
|---|---|---|
| Supervision | GPT-6.1 Sol | Medium |
| Titles, bounded identity and acquisition | GPT-6 Luna | Medium |
| Abstracts | GPT-6.1 Sol | Medium |
| Combined scientific reading | GPT-6.1 Sol | High |

Other harnesses use their accessible, authorized settings. Requested settings do
not prove provider identity. Keep unavailable access, usage and billing facts unknown.

## Review the results

The ordinary scientific delivery is `runs/<RUN_ID>/delivery/index.html`, with
structured exports and source pointers. **Prospect**, **context** and **unresolved**
describe saved contributions; they do not assign final manuscript roles.

When requested, an advisory Sol/medium pass compares only full-text-assessed
prospects with the fixed three-primary/eight-support reference set. An optional
independent Astra/xhigh final review evaluates the firm suggestions without seeing
Sol's scores or roles. Neither pass changes scientific judgments or discovery gates.

Finish a requested final review with `advisory report`. It produces both formats:

| Output | Contents |
|---|---|
| `README.md` / `index.html` | Overview, scope and qualified leads |
| `primary.md` / `primary.html` | Primary candidates and named reference comparisons |
| `support.md` / `support.html` | Support candidates and what prevents a primary recommendation |
| `other-papers.md` / `other-papers.html` | Brief saved reasons for every other assessed paper |
| `papers/` | Study procedures, findings, evidence and limitations |
| `references.md` / `references.html` | The fixed comparison studies |

Markdown uses relative links for GitHub viewing. HTML adds local navigation and
search. Both use the same saved prose and judgments; exporting adds no model call.
Unreviewed prospects and missing evidence are never relabelled as rejection.
See [researcher delivery](docs/README.md#deliver-a-researcher-reading-list).

## Pause, resume and keep the evidence

Runs preserve sources, first readings, IDs, receipts, holds and accounting. Resume
uses the exact active release. **Do not replace files inside a bound release.**
This distribution is **portable 1.0.0-r76**; adopting new runtime code requires the
documented backed-up continuation. External advisory reports can read a published
older export without migrating or resuming that scientific run.

At an indexed-paper threshold, stop new discovery, preserve complete started
responses and process admitted papers. A small overshoot is retained. The same run
can later receive an explicit additional paper allowance. Deferred work, missing
sources and limits are not scientific saturation.

The agent uses incremental sanity checks during work and full validation at quiet
delivery checkpoints. Unknown calls are not blindly retried or refunded. Routine
status checks do not make database copies. Older continuation backups can be
losslessly archived through the supported storage commands.

Detailed recovery, concurrency, source capacity, calibration, provenance and
storage rules remain in [EXECUTION.md](EXECUTION.md). The downloadable package
excludes historical runs, PDFs, private configuration and development evaluations.
