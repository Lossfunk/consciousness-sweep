# Portable code map

This map explains where to inspect each responsibility. It is not a second
scientific protocol or an alternative execution path.

```text
CLI → coordinator → durable ledger and managed workers
discovery → screening → sources → combined reading → validated delivery
published delivery → optional ranking → optional final review → Markdown + HTML report
```

The [scientific protocol](../science/PROTOCOL.md) and [source reader](../runtime/README.md)
govern interpretation. Operational scheduling, coverage, persistence and recovery
must preserve those judgments. Advisory modules recommend readings; they do not
change scientific eligibility, citation expansion or stopping.

## Entry and orchestration

| Module | Responsibility |
|---|---|
| [\_\_init\_\_.py](__init__.py) | Package marker; scientific authority is bundled separately. |
| [\_\_main\_\_.py](__main__.py) | CLI entry point: validates arguments and routes commands to the responsible modules. |
| [coordinator.py](coordinator.py) | Durable stage loop shared by automatic workers and agent work exchange. |
| [discovery.py](discovery.py) | Connect public discovery to the durable prospect coordinator. |
| [frontiers.py](frontiers.py) | Tracks citation and process searches still owed under the scientific protocol. |
| [workflow.py](workflow.py) | Defines selective focused-v1 coverage and combined reading without changing the scientific rubric. |
| [execution\_policy.py](execution_policy.py) | Applies agreed priorities, coverage deferrals and acquisition effort. |
| [scheduling.py](scheduling.py) | Bounds discovery buffers and coalesces compatible untouched screening batches. |
| [supervision.py](supervision.py) | Operational supervision and dispatch health; never a scientific stopping rule. |
| [exchange.py](exchange.py) | Completion-first exchange with a durable handoff to the active agent harness. |
| [publication.py](publication.py) | Durable publication of prepared answers; no inference, recovery or adjudication. |
| [coordination.py](coordination.py) | A local mutation lock. Never hold it across provider or network execution. |
| [transactions.py](transactions.py) | Serialize a bounded local decision and its writes on one SQLite snapshot. |

## Durable state and agreements

| Module | Responsibility |
|---|---|
| [store.py](store.py) | Stores paper records, jobs, leases, events and budget accounting in SQLite. |
| [common.py](common.py) | Small shared primitives; no scientific decisions live here. |
| [profiles.py](profiles.py) | Explicit, portable execution profiles and resource planning. |
| [source\_intake.py](source_intake.py) | Attach a complete main/SI set as immutable, hash-bound source evidence. |
| [native\_records.py](native_records.py) | Validates the transport of experiment/comparison records without deciding eligibility. |
| [citation\_depth.py](citation_depth.py) | Records ordinary citation distance separately from bridge lineage. |
| [index\_limit.py](index_limit.py) | Stops new discovery at an agreed indexed-paper allowance, then tracks draining. |

## Sources and worker execution

| Module | Responsibility |
|---|---|
| [capabilities.py](capabilities.py) | Read-only, best-effort host inventory; no inference, credentials or installs. |
| [adapters.py](adapters.py) | Source-only model calls with immutable inputs and explicit billing identity. |
| [sources.py](sources.py) | Public bibliographic adapters and source-preserving full-text acquisition. |
| [downloads.py](downloads.py) | Receipt-backed public source downloads inside one run; identity is not inferred. |
| [source\_scope.py](source_scope.py) | Operational acquisition scope; never a paper-level scientific exclusion. |
| [source\_work.py](source_work.py) | Source execution controls shared by dispatch, the runner and supervision. |
| [search\_holds.py](search_holds.py) | Audited operational holds on exact frozen query windows, never exclusions. |
| [screening.py](screening.py) | Source-specific semantic screening and the unchanged rescue instrument. |
| [reading.py](reading.py) | Bind the source reader and derived, premise-specific reading clarifications. |
| [native\_dispatch.py](native_dispatch.py) | Marks blocked native work without dropping its scientific obligations. |
| [host\_access.py](host_access.py) | Execution-environment holds; no scientific decisions or provider inference. |
| [access\_control.py](access_control.py) | Explicit recovery of operational access blocks, never scientific decisions. |
| [title\_profiles.py](title_profiles.py) | Records approved title-model changes and preserves each older job’s original profile. |
| [reader\_capacity.py](reader_capacity.py) | Explicit byte-capacity successors, preserving every original reader request. |
| [token\_counting.py](token_counting.py) | Estimates input size offline and records uncertainty about provider capacity. |

## Checks and supported recovery

| Module | Responsibility |
|---|---|
| [sanity.py](sanity.py) | Bounded operational sanity checks, safe while independent workers run. |
| [validation.py](validation.py) | Read-only operational audit, apart from its explicit report and audit event. |
| [discovery\_validation.py](discovery_validation.py) | Operational discovery integrity; no independent scientific classifications. |
| [calibration.py](calibration.py) | Coordinator-only seed checks against a versioned, source-reviewed baseline. |
| [continuation.py](continuation.py) | Explicit, backed-up operational continuation; the original plan is immutable. |
| [recovery.py](recovery.py) | Explicit fresh attempts after terminal model failures, preserving prior costs. |
| [validator\_repair.py](validator_repair.py) | Narrow, read-only evidence for an explicitly requested validator repair. |
| [source\_generation\_repair.py](source_generation_repair.py) | Repairs a proven metadata-only generation mismatch while retaining the source evidence. |
| [identical\_reading\_repair.py](identical_reading_repair.py) | Reconciles an accidental duplicate reading only after identical inputs and provenance are proven. |
| [storage.py](storage.py) | Inspect run storage and probe new-run SQLite I/O without moving any run. |
| [backup\_storage.py](backup_storage.py) | Lossless storage maintenance for closed operational backups, never run records. |

## Scientific delivery and packaging

| Module | Responsibility |
|---|---|
| [presentation.py](presentation.py) | Human-readable views of stored claims; never an additional classifier. |
| [metrics.py](metrics.py) | Observed stage measurements and transparent, provisional scaling estimates. |
| [distribution.py](distribution.py) | Build a clean downloadable agent repository from an explicit static allowlist. |

## Researcher review and delivery

| Module | Responsibility |
|---|---|
| [advisory.py](advisory.py) | Optional post-reading review exchange; never opens or changes a sweep ledger. |
| [advisory\_rankings.py](advisory_rankings.py) | Complete fixed-reference ranking and human-readable advisory reading lists. |
| [advisory\_final.py](advisory_final.py) | Independent, on-demand final advisory review of the firm Sol shortlist. |
| [advisory\_execution.py](advisory_execution.py) | Launches an authorized review once and audits execution, tool use and transport evidence. |
| [advisory\_report.py](advisory_report.py) | Researcher-facing delivery from bound saved evidence; no inference or ledger access. |
| [advisory\_markdown.py](advisory_markdown.py) | Markdown companions for freshly rendered report HTML; never a scientific input. |

## Follow one paper through the code

| Step | Where to look | What must survive |
|---|---|---|
| Plan and initialize | `__main__.py` → `profiles.py` → `coordinator.py` | Exact agreement and a unique run |
| Locate and deduplicate | `discovery.py` → `sources.py` → `store.py` | Every encounter and explicit version relationship |
| Screen | `screening.py` → `coordinator.py` | One reason and binding per paper, even in a batch |
| Attach and extract | `source_intake.py` → `source_work.py` → `sources.py` | Complete source manifests, hashes and earlier versions |
| Dispatch and publish | `exchange.py` → `reading.py` / `workflow.py` → `publication.py` | Fresh contexts, fenced leases and original answers |
| Expand or defer | `native_records.py` → `discovery.py` → `frontiers.py` | Source-grounded routing and pending obligations |
| Check and deliver | `sanity.py` / `validation.py` → `presentation.py` | Honest coverage and a quiet validated snapshot |
| Explain recommendations | `advisory.py` → `advisory_rankings.py` → `advisory_final.py` → `advisory_report.py` | Separate advisory judgments and all limitations |

## Static policy and runtime assets

| Asset | Purpose |
|---|---|
| `calibration_reference.json` | Coordinator-only seed reference; never a source-reader input |
| `advisory_policy.json` | Retained advisory rubric and factor definitions |
| `advisory_references.json` | Fixed three-primary/eight-support evaluator evidence |
| `provider_docs.json` | Recorded provider configuration references |
| `*.tiktoken`, `tokenizer_LICENSE.txt` | Pinned offline tokenizer assets and license |

## Boundaries to preserve

- A scientific reader receives source-only evidence in a fresh context. Evaluator
  expectations, earlier verdicts and advisory grades remain outside it.
- Local write transactions and publication use short locks. Network/model calls
  must not hold a command-wide publication lock.
- A durable submission, not a launcher exit or saved draft, proves completion.
- Source changes create preserved versions. Model/profile changes and resource
  extensions use explicit agreements; unknown outcomes remain charged/unknown.
- Reports read original bound evidence and accepted answers. Markdown is derived
  from freshly generated HTML in the same staging area, not an edited old view.
- Distribution uses an explicit static allowlist. Runs, PDFs, private configuration
  and development evaluations are not copied into the portable package.

Use [verify](../EXECUTION.md#files-and-identities) to check distributed bytes.
The full [command reference](../EXECUTION.md), [agent contract](../AGENTS.md) and
[run/review guide](../docs/README.md) explain execution and recovery.
