"""Observed stage measurements and transparent, provisional scaling estimates."""
import json
import math
import statistics
from .common import save_json


def estimate(coordinator, logical_papers=None):
    n = logical_papers if logical_papers is not None else coordinator.plan.get("workload", {}).get("logical_papers")
    if n is not None and (isinstance(n, bool) or not isinstance(n, int) or n < 0):
        raise ValueError("logical_papers must be a nonnegative integer")
    stages = {}
    # These are commissioning observations, never presented as a random sample
    # of literature or as an estimate of how many eligible studies exist.
    for stage in ("title", "abstract", "rescue", "audit", "reader"):
        stats = {"completed_calls": 0, "source_records": 0, "retained_records": 0,
                 "observed_total_tokens": 0, "metered_calls": 0, "seconds": []}
        cursor = None
        while True:
            jobs = coordinator.store.list_jobs(stage=stage, state="complete", limit=100, after_id=cursor)
            if not jobs:
                break
            for job in jobs:
                receipt_path = coordinator.run_dir / "jobs" / job["id"] / "execution" / "receipt.json"
                if not receipt_path.is_file():
                    continue  # External-agent latency/usage was not observed.
                receipt = json.loads(receipt_path.read_text())
                if receipt.get("status") != "completed":
                    continue
                stats["completed_calls"] += 1
                stats["seconds"].append(receipt["elapsed_seconds"])
                usage = receipt.get("usage") or {}
                if isinstance(usage, dict) and usage.get("total_tokens") is not None:
                    stats["observed_total_tokens"] += usage["total_tokens"]
                    stats["metered_calls"] += 1
                decisions = (job.get("result") or {}).get("assessment", {}).get("decisions", [])
                stats["source_records"] += len(decisions) if stage != "reader" else 1
                stats["retained_records"] += sum(d["decision"] != "exclude" for d in decisions)
            cursor = jobs[-1]["id"]
        seconds = stats.pop("seconds")
        stats["median_seconds_per_call"] = statistics.median(seconds) if seconds else None
        stats["max_observed_seconds_per_call"] = max(seconds) if seconds else None
        stats["mean_batch_records"] = stats["source_records"] / stats["completed_calls"] if stats["completed_calls"] else None
        stats["observed_retain_fraction"] = stats["retained_records"] / stats["source_records"] if stats["source_records"] and stage != "reader" else None
        stages[stage] = stats
    forecasts = []
    title, abstract, reader = (stages[k] for k in ("title", "abstract", "reader"))
    measured = all(s["completed_calls"] for s in (title, abstract, reader))
    if measured and n is not None:
        for factor in (0.5, 1.0, 2.0):
            title_retained = n * min(1, title["observed_retain_fraction"] * factor)
            readers = title_retained * min(1, abstract["observed_retain_fraction"] * factor)
            calls = {"title": math.ceil(n / 25), "abstract": math.ceil(title_retained / 10), "reader": math.ceil(readers)}
            worker_seconds = sum(calls[k] * stages[k]["median_seconds_per_call"] for k in calls)
            forecasts.append({"retention_multiplier": factor, "base_stage_calls": calls,
                              "base_model_worker_hours": worker_seconds / 3600,
                              "base_model_wall_hours_at_authorized_workers": worker_seconds / 3600 / coordinator.plan["resources"]["model_workers"]})
    result = {"logical_papers": n, "stage_observations": stages,
              "estimate_status": "provisional-scenarios" if forecasts else "insufficient-measurements",
              "scenarios": forecasts, "current_budget_accounting": coordinator.store.budget(),
              "excluded_from_scenarios": ["rescue and cumulative audit calls", "new citation/process discoveries",
                  "native discovery judgments", "retrieval/access delays", "quota resets and failures"],
              "limitations": ["Operational observations may be selected and are not a recall study.",
                  "Scenarios assume future batch filling, comparable source lengths and the same profiles.",
                  "These are base-stage workloads, not a promised full-sweep ETA or a statistical confidence interval.",
                  "A synthetic 450,000-record database benchmark says nothing about model throughput."],
              "minimum_title_calls": math.ceil(n / 25) if n is not None else None}
    save_json(coordinator.run_dir / "delivery" / "estimate.json", result)
    coordinator.store.event("throughput_estimate", {"status": result["estimate_status"], "logical_papers": n,
                                                   "reason": "Measured role-specific latency and retention; unmeasured costs remain explicit"})
    return result
