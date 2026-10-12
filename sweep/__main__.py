"""Start with `python -m sweep doctor`; all work is explicit and resumable."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys

from .common import ROOT, canonical, safe_run, save_json

def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=ROOT, help="Location of recipient run directories")
    sub = p.add_subparsers(dest="command", required=True)
    doctor = sub.add_parser("doctor", help="Read-only host/access inventory; no inference")
    doctor.add_argument("--output", type=Path)
    plan = sub.add_parser("plan", help="Build an explicit resource/model plan")
    plan.add_argument("--config", type=Path, help="JSON {profiles,resources,workload,mode}")
    plan.add_argument("--preset", choices=["manual", "codex", "claude"], default="manual")
    plan.add_argument("--authorize", action="store_true", help="Record resources already authorized by the user")
    plan.add_argument("--workers", type=int, default=2)
    plan.add_argument("--max-calls", type=int, default=20)
    plan.add_argument("--max-seconds", type=int, default=3600)
    plan.add_argument("--max-citation-depth", type=int, default=argparse.SUPPRESS,
                      help="Maximum citation hops from each seed/query root (0 = roots only); overrides this field in --config")
    plan.add_argument("--mode", choices=["corpus", "discovery"],
                      help="Explicit run mode; overrides mode in --config")
    plan.add_argument("--logical-papers", type=int)
    plan.add_argument("--claude-extra-usage-disabled", action="store_true")
    plan.add_argument("--output", type=Path, required=True)
    init = sub.add_parser("init", help="Initialize new durable state; never overwrite")
    init.add_argument("--plan", type=Path, required=True)
    init.add_argument("--run-id", required=True)
    for name in ("ingest", "close-intake", "reopen-intake", "run", "work", "submit", "status", "estimate", "validate", "audit", "deliver", "export", "pause", "resume", "recover", "retry", "human-decision", "source", "discovery-init", "native-work", "native-submit", "native-list", "native-defer", "native-allocate", "source-retry"):
        cmd = sub.add_parser(name)
        cmd.add_argument("--run-id", required=True)
        if name in {"ingest", "submit", "native-submit"}:
            cmd.add_argument("--input", type=Path, required=True)
        if name == "submit":
            cmd.add_argument("--job-id", required=True)
            cmd.add_argument("--actor", required=True)
        if name == "run":
            cmd.add_argument("--max-seconds", type=int)
            cmd.add_argument("--local-only", action="store_true")
            cmd.add_argument("--watch", action="store_true", help="Wait for deferred automatic work inside the authorized session duration")
        if name == "estimate":
            cmd.add_argument("--logical-papers", type=int)
        if name == "recover":
            cmd.add_argument("--owner", required=True)
            cmd.add_argument("--pid", type=int, required=True)
            cmd.add_argument("--host", required=True)
            cmd.add_argument("--reason", required=True)
        if name == "retry":
            cmd.add_argument("--job-id", required=True, help="Failed model job with a verified terminal receipt")
            cmd.add_argument("--reason", required=True, help="Why a fresh charged attempt is warranted")
            cmd.add_argument("--actor", required=True, help="Supervising agent/operator authorizing this retry")
        if name in {"human-decision", "source", "native-submit", "native-allocate"}:
            cmd.add_argument("--paper-id", required=True)
        if name == "native-work":
            cmd.add_argument("--owner")
            cmd.add_argument("--lease-seconds", type=int, default=900)
        if name == "native-list":
            cmd.add_argument("--limit", type=int, default=100)
            cmd.add_argument("--include-deferred", action="store_true")
        if name == "native-defer":
            cmd.add_argument("--task-id", required=True)
            cmd.add_argument("--actor", required=True)
            cmd.add_argument("--reason", required=True)
            cmd.add_argument("--delay-seconds", type=int, default=300)
            cmd.add_argument("--lease-token", type=int)
        if name == "source-retry":
            cmd.add_argument("--paper-id", required=True)
            cmd.add_argument("--reason", required=True)
        if name == "native-submit":
            cmd.add_argument("--actor", required=True)
        if name == "native-allocate":
            cmd.add_argument("--experiment-key", required=True, help="Stable source-defined physical experiment identity")
            cmd.add_argument("--comparison-key", help="Optional stable focal X-to-Y comparison identity within that experiment")
            cmd.add_argument("--actor", required=True)
            cmd.add_argument("--reason", required=True)
        if name == "human-decision":
            cmd.add_argument("--decision", required=True, choices=["accepted-support", "accepted-primary", "declined", "pending"])
            cmd.add_argument("--reason", required=True)
        if name == "source":
            supplied = cmd.add_mutually_exclusive_group(required=True)
            supplied.add_argument("--path", type=Path, action="append")
            supplied.add_argument("--manifest", type=Path, help="JSON array of {path,role,association_reason} entries; supplies the complete main/SI set")
            cmd.add_argument("--reason", required=True)
    package = sub.add_parser("package", help="Build a clean answer-key-free downloadable release")
    package.add_argument("--destination", type=Path, required=True)
    verify = sub.add_parser("verify", help="Verify all distributed inputs")
    verify.add_argument("--directory", type=Path, default=ROOT)
    args = p.parse_args(argv)
    try:
        if args.command == "doctor":
            from .capabilities import discover
            from .profiles import recommend
            inventory = discover(args.root)
            result = {"inventory": inventory, "recommendation": recommend(inventory)}
            if args.output:
                save_json(args.output, result)
        elif args.command == "plan":
            from .capabilities import discover
            from .profiles import build_plan, recommend
            inventory = discover(args.root)
            draft = json.loads(args.config.read_text()) if args.config else recommend(inventory)
            if not args.config:
                for role in ("title", "abstract", "rescue", "reader"):
                    model = "agent-selected" if args.preset == "manual" else "gpt-6-luna" if args.preset == "codex" and role == "title" else "gpt-6.1-sol" if args.preset == "codex" else "claude-haiku-5-5" if role in {"title", "abstract"} else "claude-opus-5-5"
                    profile = {"adapter": args.preset, "model": model, "authorized": args.authorize,
                               "qualification_status": "commissioning", "max_output_tokens": 16000}
                    if args.preset != "manual":
                        profile["effort"] = "medium" if role in {"title", "abstract"} else "xhigh" if args.preset == "codex" else "high"
                    if args.preset == "codex":
                        profile["codex_context"] = "source-only-v1"
                    if args.preset == "claude":
                        profile["subscription_extra_usage_disabled"] = args.claude_extra_usage_disabled
                    draft["profiles"][role] = profile
                draft["resources"].update(authorized=args.authorize, model_workers=args.workers,
                  max_calls=args.max_calls, max_wall_seconds=args.max_seconds)
                draft["workload"] = {"logical_papers": args.logical_papers} if args.logical_papers is not None else {}
            if hasattr(args, "max_citation_depth"):
                draft["resources"]["max_citation_depth"] = args.max_citation_depth
            result = build_plan(inventory, draft["profiles"], draft["resources"], draft.get("workload"))
            result["mode"] = args.mode or draft.get("mode", "corpus")
            save_json(args.output, result)
        elif args.command == "package":
            from .distribution import build
            result = build(args.destination)
        elif args.command == "verify":
            from .distribution import verify
            result = verify(args.directory)
        else:
            from .coordinator import Coordinator
            run_dir = safe_run(args.root, args.run_id)
            if args.command == "init":
                coordinator = Coordinator.initialize(run_dir, json.loads(args.plan.read_text()))
                result = coordinator.status()
            else:
                coordinator = Coordinator(run_dir)
                if args.command == "ingest":
                    result = coordinator.import_corpus(args.input)
                elif args.command == "close-intake":
                    coordinator.close_intake()
                    result = coordinator.status()
                elif args.command == "reopen-intake":
                    coordinator.store.set_state("intake_closed", False, "Explicit continuation requested by operator")
                    result = coordinator.status()
                elif args.command == "run":
                    result = coordinator.run(max_seconds=args.max_seconds, automatic_models=not args.local_only,
                          watch=args.watch,
                          progress=lambda event: print(canonical({"progress": event}), flush=True))
                elif args.command == "work":
                    result = coordinator.next_task()
                elif args.command == "submit":
                    result = coordinator.submit(args.job_id, args.input, args.actor)
                elif args.command == "status":
                    result = coordinator.status()
                elif args.command == "estimate":
                    from .metrics import estimate
                    result = estimate(coordinator, args.logical_papers)
                elif args.command == "validate":
                    from .validation import validate
                    result = validate(coordinator)
                elif args.command == "audit":
                    result = {"scheduled": coordinator.audit(), "status": coordinator.status()}
                elif args.command == "deliver":
                    result = coordinator.deliver()
                elif args.command == "export":
                    result = coordinator.store.export()
                elif args.command == "pause":
                    (run_dir / "STOP").write_text("User requested graceful pause.\n")
                    result = {"status": "pause-requested", "reason": "Already admitted bounded requests will finish and persist."}
                elif args.command == "resume":
                    (run_dir / "STOP").unlink(missing_ok=True)
                    coordinator.project_results()
                    result = coordinator.status()
                elif args.command == "recover":
                    result = coordinator.store.recover_owner(args.owner, args.reason,
                               {"kind": "process-dead", "pid": args.pid, "host": args.host})
                elif args.command == "retry":
                    from .recovery import retry
                    result = retry(coordinator, args.job_id, args.reason, args.actor)
                elif args.command == "human-decision":
                    result = coordinator.store.update_paper(args.paper_id, {"human_decision": args.decision}, args.reason, "human-explicit")
                    coordinator.deliver()
                elif args.command == "source-retry":
                    from .source_intake import queue_retrieval
                    result = {"job_id": queue_retrieval(coordinator, args.paper_id, args.reason, force_retry=True)}
                elif args.command == "native-allocate":
                    result = coordinator.store.allocate_native_ids(args.paper_id, args.experiment_key,
                        comparison_key=args.comparison_key, actor=args.actor, reason=args.reason)
                elif args.command == "source":
                    from .source_intake import attach
                    paths = json.loads(args.manifest.read_text()) if args.manifest else [str(p.resolve()) for p in args.path]
                    result = attach(coordinator, args.paper_id, paths, args.reason,
                                    base=args.manifest.resolve().parent if args.manifest else Path.cwd())
                else:
                    from . import discovery
                    if args.command == "discovery-init":
                        result = discovery.initialize_discovery(coordinator)
                    elif args.command == "native-work":
                        result = discovery.next_native_task(coordinator, owner=args.owner, lease_seconds=args.lease_seconds)
                    elif args.command == "native-list":
                        result = discovery.list_native_tasks(coordinator, limit=args.limit, include_deferred=args.include_deferred)
                    elif args.command == "native-defer":
                        result = discovery.defer_native_task(coordinator, args.task_id, actor=args.actor, reason=args.reason, delay_seconds=args.delay_seconds, lease_token=args.lease_token)
                    elif args.command == "native-submit":
                        result = discovery.submit_native(coordinator, args.paper_id, json.loads(args.input.read_text()), args.actor)
                    else:
                        raise ValueError("Unsupported command")
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
        if args.command == "validate" and not result.get("ok"):
            return 2
        return 0
    except (ValueError, RuntimeError, FileNotFoundError, KeyError) as exc:
        print(json.dumps({"error": type(exc).__name__, "reason": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
