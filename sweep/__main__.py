"""Start with `python -m sweep doctor`; all work is explicit and resumable."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
import sqlite3

from .common import ROOT, canonical, safe_run, save_json
from .storage import StorageError


def optional_limit(value):
    """An explicit unbounded allowance is JSON null, never an arbitrary ceiling."""
    if value.lower() in {"unbounded", "none", "null"}:
        return None
    try:
        return int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Use an integer or 'unbounded'") from exc


def context_arguments(parser):
    parser.add_argument("--harness", choices=["codex", "claude", "openclaw", "other", "manual"],
                        help="Active agent harness, supplied from session context; overrides environment markers")
    parser.add_argument("--model", help="Exact available model ID supplied by the supervising agent")
    parser.add_argument("--effort", help="Exact supported reasoning effort; never guessed from a model alias")
    parser.add_argument("--available-model", action="append", default=[],
                        help="Known accessible model ID from host context (repeatable; does not probe a provider)")


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=ROOT, help="Location of recipient run directories")
    sub = p.add_subparsers(dest="command", required=True)
    doctor = sub.add_parser("doctor", help="Read-only host/access inventory; no inference")
    doctor.add_argument("--output", type=Path)
    context_arguments(doctor)
    plan = sub.add_parser("plan", help="Build an explicit resource/model plan")
    plan.add_argument("--config", type=Path, help="JSON {profiles,resources,workload,mode}")
    plan.add_argument("--preset", choices=["auto", "manual", "codex", "claude"], default="auto")
    context_arguments(plan)
    plan.add_argument("--authorize", action="store_true", help="Record resources already authorized by the user")
    plan.add_argument("--workers", type=int, default=argparse.SUPPRESS)
    plan.add_argument("--max-calls", type=optional_limit, default=argparse.SUPPRESS,
                      help="User-selected total call cap, or unbounded (no default cap)")
    plan.add_argument("--max-seconds", type=optional_limit, default=argparse.SUPPRESS,
                      help="User-selected execution-session cap, or unbounded (no default cap)")
    plan.add_argument("--max-citation-depth", type=optional_limit, default=argparse.SUPPRESS,
                      help="Maximum citation hops (0 = roots only), or unbounded; overrides --config")
    plan.add_argument("--max-indexed-papers", type=optional_limit, default=argparse.SUPPRESS,
                      help="Stop new discovery at this indexed-paper count, finish admitted responses, then drain paper work; or unbounded")
    plan.add_argument("--mode", choices=["corpus", "discovery"],
                      help="Explicit run mode; overrides mode in --config")
    plan.add_argument("--logical-papers", type=int)
    plan.add_argument("--claude-extra-usage-disabled", action="store_true")
    plan.add_argument("--output", type=Path, required=True)
    for name in ("publication-control", "publication-stage", "publication-watch", "publication-reconcile", "exchange", "dispatch-ack"):
        cmd = sub.add_parser(name)
        cmd.add_argument("--run-id", required=True)
        if name == "publication-control":
            cmd.add_argument("--mode", choices=["OPEN", "HOLD"], required=True)
            cmd.add_argument("--actor", required=True)
            cmd.add_argument("--reason", required=True)
        elif name == "publication-stage":
            cmd.add_argument("--kind", choices=["model", "native"], required=True)
            cmd.add_argument("--entity-id", required=True)
            cmd.add_argument("--input", type=Path, required=True)
            cmd.add_argument("--settings", type=Path, required=True)
            cmd.add_argument("--pointer", type=Path, required=True)
            cmd.add_argument("--actor", required=True)
        elif name == "publication-watch":
            cmd.add_argument("--poll-seconds", type=float, default=1)
            cmd.add_argument("--max-seconds", type=float)
        elif name == "publication-reconcile":
            cmd.add_argument("--request-id", required=True)
            cmd.add_argument("--actor", required=True)
            cmd.add_argument("--reason", required=True)
        elif name == "exchange":
            cmd.add_argument("--slots", type=int, required=True, help="Observed free harness slots now; zero only drains prepared answers")
        else:
            cmd.add_argument("--ticket-id", required=True)
            cmd.add_argument("--worker-context-id", required=True)
            cmd.add_argument("--actor", required=True)
            cmd.add_argument("--reason", required=True)
    init = sub.add_parser("init", help="Initialize new durable state; never overwrite")
    init.add_argument("--plan", type=Path, required=True)
    init.add_argument("--run-id", required=True)
    for name in ("ingest", "close-intake", "reopen-intake", "run", "work", "submit", "status", "estimate", "validate", "sanity", "calibration-report", "calibration-review", "audit", "deliver", "export", "pause", "resume", "recover", "retry", "human-decision", "source", "discovery-init", "native-work", "native-submit", "native-list", "native-defer", "native-recover", "native-allocate", "native-records", "source-retry", "fetch-source", "host-check", "continue-run", "supervise", "search-hold", "search-release", "source-hold", "source-release", "source-run", "reader-capacity"):
        cmd = sub.add_parser(name)
        cmd.add_argument("--run-id", required=True)
        if name in {"ingest", "submit", "native-submit", "calibration-review"}:
            cmd.add_argument("--input", type=Path, required=True)
        if name in {"search-hold", "search-release"}:
            cmd.add_argument("--window-key", action="append", required=True, help="Exact frozen query window key; repeat for atomic changes")
            cmd.add_argument("--actor", required=True)
            cmd.add_argument("--reason", required=True)
            if name == "search-release":
                cmd.add_argument("--evidence", required=True, help="Source or repair receipt that resolves this operational hold")
        if name in {"source-hold", "source-release"}:
            cmd.add_argument('--job-id', action='append', required=True)
            cmd.add_argument('--actor', required=True)
            cmd.add_argument('--reason', required=True)
            if name == 'source-release': cmd.add_argument('--evidence', required=True)
        if name == 'source-run':
            cmd.add_argument('--mode', choices=['all','supplied'], default='all')
            cmd.add_argument('--max-seconds', type=optional_limit)
            cmd.add_argument('--watch', action='store_true')
        if name == 'reader-capacity':
            cmd.add_argument('--job-id', required=True)
            cmd.add_argument('--max-input-bytes', required=True, type=int)
            cmd.add_argument('--actor', required=True)
            cmd.add_argument('--reason', required=True)
            cmd.add_argument('--access-evidence', required=True)
            cmd.add_argument('--context-accounting', choices=['local-openai-text-v1'])
            cmd.add_argument('--accounting-evidence', help='Explicit authorization for a local estimate; model mapping/provider framing remain unverified')
            cmd.add_argument('--apply', action='store_true')
        if name == "supervise":
            cmd.add_argument("--mode", choices=["active", "checkpoint"], help="Record active supervision or hold new admissions for a coordinated checkpoint")
            cmd.add_argument("--actor")
            cmd.add_argument("--reason")
            cmd.add_argument("--wakeup", type=Path, help="JSON observation from the host's same-run continuation mechanism; records evidence, does not install a schedule")
            cmd.add_argument("--check-yield", action="store_true", help="Exit 3 if ready work or owned workers still need active supervision")
        if name == "continue-run":
            from .validator_repair import REPAIR
            from .source_generation_repair import REPAIR as SOURCE_REPAIR
            cmd.add_argument("--repair-validation", choices=[REPAIR, SOURCE_REPAIR], help="Explicit known repair; requires proven failure, quiet snapshot and passing replacement checks before backed-up apply")
            cmd.add_argument("--title-profile", type=Path, help="Explicit JSON {model,effort,access_evidence} for future/unadmitted title tasks only")
            cmd.add_argument("--reconcile-identical-reading", action="append", default=[], metavar="PAPER_ID",
                help="Explicitly restore a proven original reading after an identical-packet metadata reread; retain the extra reading separately")
            cmd.add_argument("--previous-release", type=Path, required=True)
            cmd.add_argument("--policy", type=Path, required=True)
            cmd.add_argument("--actor", required=True)
            cmd.add_argument("--reason", required=True)
            cmd.add_argument("--apply", action="store_true", help="Apply the inspected continuation; otherwise read-only preparation")
        if name == "submit":
            cmd.add_argument("--job-id", required=True)
            cmd.add_argument("--actor", required=True)
        if name == "run":
            cmd.add_argument("--max-seconds", type=optional_limit)
            cmd.add_argument("--local-only", action="store_true")
            cmd.add_argument("--watch", action="store_true", help="Wait for deferred automatic work inside the authorized session duration")
            cmd.add_argument("--defer-checkpoint", action="store_true", help="Leave full validation/delivery to the supervisor after all writers are quiet")
        if name == "resume":
            cmd.add_argument("--resolve-access-blocks", action="store_true",
                             help="Record a real access/configuration fix; does not change models, budgets or unknown admission")
            cmd.add_argument("--access-block", action="append", help="Active block_key from status; repeat to select repaired scopes (includes linked profile/job denials)")
            cmd.add_argument("--resolve-host-access", action="append", choices=["network", "codex_state"], help="Recheck and resolve only the selected repaired host hold; no inference")
            cmd.add_argument("--reason", help="What changed to resolve the recorded access failure")
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
        if name in {"human-decision", "source", "native-submit", "native-allocate", "calibration-review"}:
            cmd.add_argument("--paper-id", required=True)
        if name == "native-records":
            cmd.add_argument("--reader-job-id", required=True)
            cmd.add_argument("--expected-result-sha256", required=True)
            cmd.add_argument("--input", type=Path, required=True)
            cmd.add_argument("--actor", required=True)
            cmd.add_argument("--reason", required=True)
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
            cmd.add_argument("--until-changed", action="store_true", help="Hold unchanged source/identity work until evidence changes or explicit release; retain incomplete coverage")
            cmd.add_argument("--lease-token", type=int)
        if name == "fetch-source":
            cmd.add_argument("--paper-id", required=True)
            cmd.add_argument("--url", required=True)
            cmd.add_argument("--role", choices=["main", "supplement"], default="main")
            cmd.add_argument("--association-reason")
            from .source_scope import MATERIAL_KINDS
            cmd.add_argument("--material-kind", choices=sorted(MATERIAL_KINDS))
            cmd.add_argument("--reason", required=True)
            cmd.add_argument("--actor", default="supervising-agent")
        if name == "source-retry":
            cmd.add_argument("--paper-id", required=True)
            cmd.add_argument("--reason", required=True)
        if name == "native-recover":
            cmd.add_argument("--task-id", required=True)
            cmd.add_argument("--owner", required=True)
            cmd.add_argument("--lease-token", required=True, type=int)
            cmd.add_argument("--actor", required=True)
            cmd.add_argument("--reason", required=True)
            cmd.add_argument("--proof", required=True, type=Path,
                             help="JSON receipt of observed worker termination; expiration alone is insufficient")
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
    for name in ("backup-archive", "backup-restore"):
        cmd = sub.add_parser(name, help="Historical backup storage only; never changes the live ledger or sources")
        cmd.add_argument("--run-id", required=True)
        cmd.add_argument("--actor", default="supervising-agent")
        cmd.add_argument("--reason", default="")
        if name == "backup-archive":
            cmd.add_argument("--keep-latest", type=int, default=1,
                             help="Recent backups to retain uncompressed (default: 1); the latest continuation is always retained too")
            cmd.add_argument("--apply", action="store_true", help="Archive closed backups after verified decompression; otherwise read-only inventory")
        else:
            cmd.add_argument("--backup", required=True, help="Original run-relative historical backup path to restore, never the live database")
    package = sub.add_parser("package", help="Build a clean downloadable release with a coordinator-only seed calibration reference")
    package.add_argument("--destination", type=Path, required=True)
    verify = sub.add_parser("verify", help="Verify all distributed inputs")
    verify.add_argument("--directory", type=Path, default=ROOT)
    args = p.parse_args(argv)
    try:
        if args.command == "doctor":
            from .capabilities import discover
            from .profiles import recommend
            inventory = discover(args.root, harness=args.harness, model=args.model,
                                 effort=args.effort, available_models=args.available_model)
            result = {"inventory": inventory, "recommendation": recommend(inventory)}
            if args.output:
                save_json(args.output, result)
        elif args.command == "plan":
            from .capabilities import discover
            from .profiles import build_plan, recommend
            inventory = discover(args.root, harness=args.harness or (args.preset if args.preset != "auto" else None),
                                 model=args.model, effort=args.effort, available_models=args.available_model)
            draft = json.loads(args.config.read_text()) if args.config else recommend(inventory)
            if not args.config:
                if args.preset in {"codex", "claude"}:
                    context = inventory.get("active_context", {})
                    model, effort = args.model or context.get("model"), args.effort or context.get("effort")
                    if not model or not effort:
                        raise ValueError("Automatic presets require exact available --model and --effort from host context, or explicit stage profiles via --config")
                    for role in ("title", "abstract", "rescue", "reader"):
                        draft["profiles"][role] = {"adapter": args.preset, "model": model, "effort": effort,
                            "qualification_status": "unqualified", "max_output_tokens": 16000}
                elif args.preset == "manual":
                    draft["profiles"] = {role: {"adapter": "manual", "model": args.model or "agent-selected", "effort": args.effort}
                                         for role in ("title", "abstract", "rescue", "reader")}
                for profile in draft["profiles"].values():
                    profile["authorized"] = args.authorize
                    if profile["adapter"] == "codex":
                        profile.setdefault("codex_context", "source-only-v1")
                    if profile["adapter"] == "claude":
                        profile["subscription_extra_usage_disabled"] = args.claude_extra_usage_disabled
                draft["resources"]["authorized"] = args.authorize
                draft["workload"] = {"logical_papers": args.logical_papers} if args.logical_papers is not None else {}
            for flag, key in (("workers", "model_workers"), ("max_calls", "max_calls"),
                              ("max_seconds", "max_wall_seconds"), ("max_citation_depth", "max_citation_depth"),
                              ("max_indexed_papers", "max_indexed_papers")):
                if hasattr(args, flag):
                    draft["resources"][key] = getattr(args, flag)
            policy = draft["resources"].setdefault("operational_policy", {})
            policy.setdefault("workflow", "focused-v1")
            if policy["workflow"] == "focused-v1":
                policy.setdefault("retrieval_max_rounds", 1)
                policy.setdefault("retained_first", True)
                policy.setdefault("supervised_checkpoints", True)
            result = build_plan(inventory, draft["profiles"], draft["resources"], draft.get("workload"),
                                draft.get("calibration_review_profile"))
            result["mode"] = args.mode or draft.get("mode", "discovery")
            save_json(args.output, result)
        elif args.command == "package":
            from .distribution import build
            result = build(args.destination)
        elif args.command == "verify":
            from .distribution import verify
            result = verify(args.directory)
        elif args.command in {"backup-archive", "backup-restore"}:
            from . import backup_storage
            run_dir = safe_run(args.root, args.run_id)
            if args.command == "backup-restore":
                result = backup_storage.restore(run_dir, args.backup, actor=args.actor, reason=args.reason)
            elif args.apply:
                result = backup_storage.archive(run_dir, keep_latest=args.keep_latest, actor=args.actor, reason=args.reason)
            else:
                result = backup_storage.inventory(run_dir, args.keep_latest)
        else:
            from .coordinator import Coordinator
            run_dir = safe_run(args.root, args.run_id)
            if args.command == "init":
                coordinator = Coordinator.initialize(run_dir, json.loads(args.plan.read_text()))
                result = coordinator.status()
            elif args.command == "continue-run":
                from . import continuation
                operation = continuation.apply if args.apply else continuation.prepare
                result = operation(run_dir, args.previous_release, json.loads(args.policy.read_text()), args.actor, args.reason,
                    json.loads(args.title_profile.read_text()) if args.title_profile else None,
                    repair_validation=args.repair_validation, reconcile_readings=args.reconcile_identical_reading)
                if args.apply:
                    from .execution_policy import park_exhausted
                    from .workflow import reconcile
                    reconcile(Coordinator(run_dir))
                    result = {"continuation": result, "parked_retrievals": park_exhausted(Coordinator(run_dir)),
                              "status": "paused-awaiting-validation"}
            else:
                coordinator = Coordinator(run_dir)
                from .coordination import command_scope
                with command_scope(run_dir, args.command):
                    if args.command in {"publication-control", "publication-stage", "publication-watch", "publication-reconcile", "exchange", "dispatch-ack"}:
                        from .exchange import Exchange, control, watch
                        lane = Exchange(coordinator)
                        if args.command == "publication-control":
                            result = control(coordinator, args.mode, args.actor, args.reason)
                        elif args.command == "publication-stage":
                            result = {"status": "staged", "request_id": lane.stage(args.kind, args.entity_id,
                                args.input, args.actor, args.settings, args.pointer)}
                        elif args.command == "publication-watch":
                            result = watch(coordinator, poll_seconds=args.poll_seconds, max_seconds=args.max_seconds,
                                progress=lambda value: print(canonical(value), flush=True))
                        elif args.command == "publication-reconcile":
                            result = lane.reconcile(args.request_id, args.actor, args.reason)
                        elif args.command == "exchange":
                            result = lane.step(args.slots)
                        else:
                            result = lane.acknowledge(args.ticket_id, args.worker_context_id, args.actor, args.reason)
                    elif args.command in {"search-hold", "search-release"}:
                        from .search_holds import change
                        result = change(coordinator, args.window_key, actor=args.actor, reason=args.reason,
                            release=args.command == "search-release", evidence=getattr(args, "evidence", None))
                    elif args.command == "ingest":
                        result = coordinator.import_corpus(args.input)
                    elif args.command == "close-intake":
                        coordinator.close_intake()
                        result = coordinator.status()
                    elif args.command == "reopen-intake":
                        coordinator.store.set_state("intake_closed", False, "Explicit continuation requested by operator")
                        result = coordinator.status()
                    elif args.command == "run":
                        result = coordinator.run(max_seconds=args.max_seconds, automatic_models=not args.local_only,
                              watch=args.watch, defer_checkpoint=args.defer_checkpoint,
                              progress=lambda event: print(canonical({"progress": event}), flush=True))
                    elif args.command == "work":
                        result = coordinator.next_task()
                    elif args.command == "submit":
                        result = coordinator.submit(args.job_id, args.input, args.actor)
                    elif args.command == "supervise":
                        from .supervision import record, snapshot
                        if args.mode:
                            record(coordinator, actor=args.actor, reason=args.reason, mode=args.mode,
                                   wakeup=json.loads(args.wakeup.read_text()) if args.wakeup else None)
                        elif args.actor or args.reason or args.wakeup:
                            raise ValueError("Recording supervision requires --mode, --actor and --reason")
                        result = snapshot(coordinator)
                    elif args.command == "status":
                        result = coordinator.status()
                    elif args.command == "estimate":
                        from .metrics import estimate
                        result = estimate(coordinator, args.logical_papers)
                    elif args.command == "validate":
                        from .validation import validate
                        result = validate(coordinator)
                    elif args.command == "sanity":
                        from .sanity import check
                        result = check(coordinator)
                    elif args.command == "calibration-report":
                        from .calibration import reconcile
                        result = reconcile(coordinator)
                    elif args.command == "calibration-review":
                        from .calibration import record_adjudication
                        result = record_adjudication(coordinator, args.paper_id, json.loads(args.input.read_text()))
                        coordinator._calibration_dirty = True
                        coordinator.reconcile_calibration()
                    elif args.command == "audit":
                        result = {"scheduled": coordinator.audit(), "status": coordinator.status()}
                    elif args.command == "deliver":
                        result = coordinator.deliver()
                    elif args.command == "export":
                        result = coordinator.store.export()
                    elif args.command == "pause":
                        (run_dir / "STOP").write_text("User requested graceful pause.\n")
                        result = {"status": "pause-requested", "reason": "Already admitted bounded requests will finish and persist."}
                    elif args.command == "host-check":
                        from .host_access import record_launch
                        result = {"host_access": record_launch(coordinator.store, [*coordinator.execution_profiles.values(),
                            *([coordinator.plan["calibration_review_profile"]] if coordinator.plan.get("calibration_review_profile") else [])]), "inference_performed": False}
                    elif args.command == "resume":
                        if args.access_block and not args.resolve_access_blocks:
                            raise ValueError("--access-block requires --resolve-access-blocks")
                        if args.resolve_host_access:
                            from .host_access import resolve as resolve_host
                            resolve_host(coordinator.store, [*coordinator.execution_profiles.values(),
                                *([coordinator.plan["calibration_review_profile"]] if coordinator.plan.get("calibration_review_profile") else [])],
                                args.reason, args.resolve_host_access)
                        if args.resolve_access_blocks:
                            from .access_control import resolve
                            if not args.reason or not args.reason.strip():
                                raise ValueError("--resolve-access-blocks requires the actual fix in --reason")
                            resolve(coordinator, args.reason, block_keys=args.access_block)
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
                    elif args.command == "fetch-source":
                        from .downloads import fetch
                        from .host_access import transport_scope
                        with transport_scope(coordinator.store):
                            result = fetch(coordinator, args.paper_id, args.url, role=args.role,
                                association_reason=args.association_reason, reason=args.reason, actor=args.actor,
                                material_kind=args.material_kind)
                    elif args.command in {'source-hold','source-release'}:
                        from .source_work import change
                        result = change(coordinator,args.job_id,args.actor,args.reason,
                            release=args.command=='source-release',evidence=getattr(args,'evidence',None))
                    elif args.command == 'source-run':
                        from .source_work import run as source_run
                        result = source_run(coordinator,mode=args.mode,max_seconds=args.max_seconds,watch=args.watch)
                    elif args.command == 'reader-capacity':
                        from .reader_capacity import grant
                        result = grant(coordinator,args.job_id,args.max_input_bytes,args.actor,args.reason,
                            args.access_evidence,apply=args.apply,context_accounting=args.context_accounting,accounting_evidence=args.accounting_evidence)
                    elif args.command == "source-retry":
                        from .source_intake import queue_retrieval
                        result = {"job_id": queue_retrieval(coordinator, args.paper_id, args.reason, force_retry=True)}
                    elif args.command == "native-records":
                        from .native_records import supplement
                        result = supplement(coordinator, args.reader_job_id, args.input,
                            args.expected_result_sha256, args.actor, args.reason)
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
                            from .validation import require_integrity
                            require_integrity(coordinator)
                            result = discovery.next_native_task(coordinator, owner=args.owner, lease_seconds=args.lease_seconds)
                        elif args.command == "native-recover":
                            result = discovery.recover_native_task(coordinator, args.task_id, owner=args.owner,
                                lease_token=args.lease_token, actor=args.actor, reason=args.reason,
                                proof=json.loads(args.proof.read_text()))
                        elif args.command == "native-list":
                            result = discovery.list_native_tasks(coordinator, limit=args.limit, include_deferred=args.include_deferred)
                        elif args.command == "native-defer":
                            result = discovery.defer_native_task(coordinator, args.task_id, actor=args.actor, reason=args.reason, delay_seconds=args.delay_seconds, lease_token=args.lease_token, until_changed=args.until_changed)
                        elif args.command == "native-submit":
                            result = discovery.submit_native(coordinator, args.paper_id, json.loads(args.input.read_text()), args.actor)
                        else:
                            raise ValueError("Unsupported command")
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
        if args.command in {"validate", "sanity"} and not result.get("ok"):
            return 2
        if args.command == "supervise" and args.check_yield and not result["may_end_turn"]:
            return 3
        return 0
    except StorageError as exc:
        print(json.dumps({"error": type(exc).__name__, "reason": str(exc), "storage": exc.report},
                         ensure_ascii=False, default=str), file=sys.stderr)
        return 2
    except sqlite3.Error as exc:
        # The database may be unable to record its own failure. Always retain
        # diagnostics on stderr; do not open it again or retry an uncertain write.
        storage = {"command": args.command,
                   "database": getattr(exc, "sweep_db_path", None),
                   "phase": getattr(exc, "sweep_storage_phase", "unknown"),
                   "sqlite_errorcode": getattr(exc, "sqlite_errorcode", None),
                   "sqlite_errorname": getattr(exc, "sqlite_errorname", None),
                   "python_version": sys.version.split()[0],
                   "sqlite_version": sqlite3.sqlite_version,
                   "cleanup_errors": getattr(exc, "sweep_cleanup_errors", []),
                   "retry_performed": False,
                   "next_action": "Stop execution, preserve database/WAL/SHM and worker receipts, resolve the storage problem, then reconcile leases and validate with the bound release before resuming. Do not replay calls or retry an uncertain commit automatically."}
        print(json.dumps({"error": type(exc).__name__, "reason": str(exc), "storage": storage},
                         ensure_ascii=False, default=str), file=sys.stderr)
        return 2
    except (ValueError, RuntimeError, OSError, EOFError, KeyError) as exc:
        print(json.dumps({"error": type(exc).__name__, "reason": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
