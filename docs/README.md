# Run and review guide

Use this guide to understand the usual path and what to inspect at each step.
The coding agent performs the commands and handles ordinary retrieval and submission.
[AGENTS.md](../AGENTS.md) is its operating contract; [EXECUTION.md](../EXECUTION.md)
is the detailed reference.

## Choose the work

Agree on the harness, exact role models and reasoning, authorized billing, available
worker capacity and optional citation-depth or indexed-paper limits. A finite
allowance and unbounded subscription work are both supported. Installed tools do
not establish model access; the agent must retain unknowns rather than silently
switch a model or payment route.

An indexed-paper allowance counts logical papers, including seeds, anchors,
exclusions and deferred entries. It does not count encounters or completed readings.
Started search responses finish intact, so the count can overshoot slightly.

## Execute and inspect

| Step | What the agent does | What you can assess |
|---|---|---|
| Verify | Bootstrap pinned dependencies, verify the distribution and run `doctor` | Release integrity, selected local storage and observed access |
| Plan | Write the agreed configuration, build a plan and initialize one unique run | Exact profiles, allowance, depth and coverage choices |
| Discover | Search the recorded citation/process windows and deduplicate encounters | Indexed papers, citation depths and remaining frontiers |
| Screen | Record title and abstract decisions with reasons | Unique-paper retain, uncertain and exclude counts |
| Acquire and read | Retrieve main/textual supplementary sources and dispatch fresh readers | Verified sources, completed assessments, gaps and blocked work |
| Publish | Hold admissions, settle writers, validate and deliver a quiet snapshot | Findings, coverage and evidence available for review |

The agent writes the configuration before running this ordinary command sequence:

```sh
.venv/bin/python -B -m sweep plan --config workspace/config.json --output workspace/plan.json
.venv/bin/python -B -m sweep init --plan workspace/plan.json --run-id RUN_ID
```

`RUN_ID` is a new unique name. Do not reuse another run's directory or judgments.
For execution, the supervisor uses the [managed exchange](../EXECUTION.md#managed-worker-exchange)
and [source runner](../EXECUTION.md#managed-source-execution); those helpers fill
authorized slots, publish completed answers and retain their actual process handles.

While work runs, `status --run-id RUN_ID` reports the funnel and holds. `sanity`
checks bounded bookkeeping. Full `validate` and `deliver` belong at quiet
checkpoints, rather than after every worker. Use each command's `--help` for its
required arguments; the [command table](../EXECUTION.md#command-summary) links the
broader interfaces.

## Read the counts correctly

- **Indexed** means a durable logical-paper entry, not a completed reading.
- **Screened** means that stage recorded an individual decision. Legacy revisions
  and rescues mean the totals need not form a perfectly consecutive funnel.
- **Assessed** means a saved scientific reading; incomplete assessments remain explicit.
- **Prospect** means a contribution worth human review, not an accepted primary or support.
- **Deferred, source-missing, held and unknown** are different from scientific exclusion.

Ask for current unique-paper counts, depth, ready work, owned workers, blocked work
and source gaps. Adapter usage omits unobserved supervisor/external-worker usage;
zero recorded dollars does not establish zero credits.

## Deliver a researcher reading list

The optional advisory steps run only when requested under an authorized allowance,
usually at a pause or published checkpoint:

1. `advisory prepare` creates prospect-only Sol/medium ranking jobs against all eleven
   fixed references. Run each job once with the managed advisory launcher.
2. `advisory prepare-final` selects firm new candidates for independent Astra/xhigh
   review. It withholds earlier grades and includes a concrete procedure summary
   in that same requested response.
3. `advisory report` produces the explained researcher delivery from accepted answers.
   It requires no further model or retrieval call.

```sh
.venv/bin/python -B -m sweep advisory report \
  --suggestions workspace/ranking-RUN_ID \
  --final-review workspace/final-RUN_ID \
  --workspace workspace/report-RUN_ID
```

Open `workspace/report-RUN_ID/README.md` for GitHub-friendly Markdown, or
`index.html` for the local HTML version. Follow the linked primary/support lists,
study explanations and catalogue of other assessed papers. The report preserves
original scientific claims, separate advisory recommendations, source gaps and
disagreements. It does not silently disqualify prospects outside final review.

Always use a new report directory. The command checks original bound requests,
answers and execution audits, rather than trusting edited HTML or review summaries.
It accepts repeated final-workspace arguments for independently authorized
replacement jobs, without erasing interrupted tickets or unknown charges.
Existing legacy editorial summaries can be supplied through the documented
`--narratives` binding; no rewrite or replacement inference starts automatically.

Only published assessments belong in that report. Newer ledger work needs its own
quiet validated delivery before a new report includes it. Publishing run-specific
results to a public repository is a separate choice from exporting Markdown or
publishing the portable code. Review the generated report and its provenance first.

## Pause or continue

Ask the agent to pause gracefully, stop admissions and settle admitted work.
Do not kill a worker and infer that its remote call was free or never happened.
When a published checkpoint is needed, drain writers and perform the documented
validation/delivery sequence while preserving holds.

Resume uses the same active release and resource agreement. Changing a runtime,
title profile or indexed-paper allowance requires the supported backed-up
continuation. External advisory/reporting code can read a paused run's published
export without changing that runtime.

## When something is blocked

| Observation | Expected response |
|---|---|
| Source unavailable after bounded acquisition | Record the gap and move on; do not repeat the hunt |
| Packet exceeds capacity | Keep the undispatched job blocked; continue fitting work; use explicit capacity recovery only when authorized |
| Access or budget hold | Preserve its scope and accounting; use explicit recovery, never silent fallback |
| Lost reply or expired lease | Inspect actual execution and durable completion before recovery; never blindly rerun |
| Integrity failure | Stop the affected admission scope, preserve evidence and diagnose; never edit the ledger to pass a check |
| Deferred queue remains | Report selective coverage honestly; do not call it saturation |

See the [reference](../EXECUTION.md) for the exact recovery commands. Keep the
latest restore point; archive older backups only through verified storage commands.
Do not manually delete live SQLite files, sources, first readings or worker evidence.

## Find the implementation

- [Portable modules](../sweep/README.md): orchestration, persistence, sources, checks and advisory output.
- [Source reader](../runtime/README.md): the frozen reading contract and output schema.
- [Scientific authority](../science/PROTOCOL.md): interpretation and citation/process rules.
- [Full command reference](../EXECUTION.md): configuration and operational procedures.
