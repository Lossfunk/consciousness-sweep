"""Explicit, portable execution profiles and resource planning.

Availability, authorization and scientific qualification are independent facts.
No planning function makes a model call or grants spending permission.
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
import re
from urllib.parse import urlsplit


ADAPTERS = {"codex", "claude", "command", "openai-compatible", "manual"}
ROLES = ("title", "abstract", "rescue", "reader")
RESOURCE_KEYS = {"authorized", "cpu_workers", "model_workers", "retrieval_workers",
                 "discovery_buffer_papers", "sanity_interval_seconds", "memory_limit_bytes",
                 "gpu_memory_limit_bytes", "max_calls", "max_tokens", "max_spend_usd",
                 "max_wall_seconds", "max_citation_depth", "max_indexed_papers", "operational_policy"}
PROFILE_KEYS = {"adapter", "model", "effort", "billing_route", "authorized", "timeout_seconds",
                "max_attempts", "cli_path", "endpoint_url", "credential_env", "argv", "environment_names",
                "max_input_bytes", "max_output_tokens", "context_window_tokens", "qualification_status",
                "parameters", "effort_parameter", "response_format", "max_request_usd",
                "input_price_per_million", "output_price_per_million", "max_calls", "max_tokens",
                "max_spend_usd", "profile_id", "qualification_record", "notes", "max_turns",
                "subscription_extra_usage_disabled", "codex_context", "context_accounting"}


def _number(value, name, minimum=0, integer=False, nullable=True):
    if value is None and nullable:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(name + " must be a finite number")
    if value < minimum or integer and int(value) != value:
        raise ValueError(name + " is outside its allowed range")
    return int(value) if integer else value


def profile_fingerprint(profile: dict) -> str:
    return hashlib.sha256(json.dumps(profile, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def validate_profile(profile: dict) -> dict:
    if not isinstance(profile, dict):
        raise ValueError("Profile must be an object")
    unknown = set(profile) - PROFILE_KEYS
    if unknown:
        raise ValueError("Unknown profile keys: " + ", ".join(sorted(unknown)))
    if set(profile) & {"max_calls", "max_tokens", "max_spend_usd"}:
        raise ValueError("Call/token/spending budgets belong in plan resources; per-profile budgets are not enforced")
    p = copy.deepcopy(profile)
    adapter = p.get("adapter", "manual")
    if adapter not in ADAPTERS:
        raise ValueError("Unsupported adapter. OpenClaw may use an explicitly reviewed command wrapper or manual exchange.")
    p["adapter"] = adapter
    p.setdefault("model", "human-selected-agent" if adapter == "manual" else "")
    if not isinstance(p["model"], str) or not p["model"].strip() or any(c in p["model"] for c in "\r\n\0"):
        raise ValueError("An explicit single model identity is required")
    if adapter != "manual" and p["model"].strip().lower() in {"auto", "default", "latest", "sonnet", "opus", "haiku"}:
        raise ValueError("Use an explicit model ID; automatic/default model routing is not reproducible")
    p.setdefault("effort", None)
    if p["effort"] is not None and (not isinstance(p["effort"], str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,40}", p["effort"])):
        raise ValueError("Effort must be an explicit provider-native setting")
    if adapter in {"codex", "claude"} and not p["effort"]:
        raise ValueError("CLI reader effort must be explicit")
    if adapter == "codex":
        p.setdefault("codex_context", "standard")
        if p["codex_context"] not in {"standard", "source-only-v1"}:
            raise ValueError("codex_context must be standard or source-only-v1")
    elif "codex_context" in p:
        raise ValueError("codex_context is supported only by the Codex adapter")
    if adapter == "claude":
        if p["effort"] not in {"low", "medium", "high", "xhigh", "max"}:
            raise ValueError("Select a Claude reasoning level, not an automatic workflow mode")
        if any(old in p["model"] for old in ("opus-4-6", "sonnet-4-6")) and p["effort"] == "xhigh":
            raise ValueError("Claude 4.6 silently lowers xhigh to high; choose the actual supported level")
        if "fable" in p["model"].lower():
            raise ValueError("Fable may silently bill usage credits in headless mode; it is outside this subscription-only adapter")
        p.setdefault("max_turns", 3)
        _number(p["max_turns"], "max_turns", minimum=1, integer=True, nullable=False)
        p.setdefault("subscription_extra_usage_disabled", False)
        if not isinstance(p["subscription_extra_usage_disabled"], bool):
            raise ValueError("subscription_extra_usage_disabled must be a boolean operator attestation")
    p.setdefault("billing_route", "manual" if adapter == "manual" else "subscription" if adapter in {"codex", "claude"} else "local")
    if p["billing_route"] not in {"subscription", "api", "local", "manual"}:
        raise ValueError("Unknown billing_route")
    if adapter == "codex" and p["billing_route"] != "subscription":
        raise ValueError("Codex adapter is signed-in subscription only; no API fallback")
    if adapter == "claude" and p["billing_route"] != "subscription":
        raise ValueError("Claude adapter currently supports verified subscription auth only; use an explicit API endpoint separately")
    if adapter == "manual" and p["billing_route"] != "manual":
        raise ValueError("Manual exchange does not authorize a billed route")
    if adapter == "openai-compatible" and p["billing_route"] not in {"local", "api"}:
        raise ValueError("Compatible endpoints require an explicit local or API billing route")
    p.setdefault("authorized", False)
    if not isinstance(p["authorized"], bool):
        raise ValueError("authorized must be a boolean")
    p.setdefault("timeout_seconds", 900)
    _number(p["timeout_seconds"], "timeout_seconds", minimum=0.01, nullable=False)
    p.setdefault("max_attempts", 1)
    if isinstance(p["max_attempts"], bool) or p["max_attempts"] != 1:
        raise ValueError("One admitted attempt per binding; retries require explicit coordinator disposition")
    p.setdefault("max_input_bytes", 400000)
    p.setdefault("max_output_tokens", 8000)
    for key in ("max_input_bytes", "max_output_tokens"):
        _number(p[key], key, minimum=1, integer=True, nullable=False)
    for key in ("max_calls", "max_tokens"):
        if key in p:
            _number(p[key], key, minimum=1, integer=True)
    for key in ("max_spend_usd", "max_request_usd", "input_price_per_million", "output_price_per_million"):
        if key in p:
            _number(p[key], key, minimum=0)
    if "context_window_tokens" in p:
        _number(p["context_window_tokens"], "context_window_tokens", minimum=1, integer=True, nullable=False)
    if "context_accounting" in p:
        from .token_counting import METHOD
        if (p['context_accounting'] != METHOD or p['adapter'] not in {'codex','manual'}
                or p['adapter']=='codex' and p.get('codex_context')!='source-only-v1'
                or not p.get('context_window_tokens')):
            raise ValueError('Explicit local context accounting requires a bounded source-only Codex/manual text request')
    p.setdefault("qualification_status", "unqualified")
    if p["qualification_status"] not in {"unqualified", "commissioning", "provisional-prospects", "qualified"}:
        raise ValueError("Unknown qualification_status")
    if p["qualification_status"] == "qualified" and not p.get("qualification_record"):
        raise ValueError("Qualified profiles need a qualification record, not just a label")
    if p.get("credential_env") and not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", p["credential_env"]):
        raise ValueError("credential_env must name an environment variable, never contain a credential")
    if not isinstance(p.get("environment_names", []), list):
        raise ValueError("environment_names must be a list of names")
    for name in p.get("environment_names", []):
        if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
            raise ValueError("environment_names must contain names only")
    if adapter == "command":
        argv = p.get("argv")
        if not isinstance(argv, list) or not argv or any(not isinstance(x, str) or "\0" in x for x in argv):
            raise ValueError("Command adapter requires a nonempty argv array; shell strings are unsupported")
        allowed = {"prompt_path", "schema_path", "result_path", "model", "effort"}
        from string import Formatter
        for arg in argv:
            for _, key, fmt, conversion in Formatter().parse(arg):
                if key is not None and (key not in allowed or fmt or conversion):
                    raise ValueError("Unsupported command placeholder: " + str(key))
    if adapter == "openai-compatible":
        address = p.get("endpoint_url", "")
        url = urlsplit(address)
        if url.scheme not in {"http", "https"} or not url.hostname or url.username or url.password or url.query or url.fragment:
            raise ValueError("Endpoint must be an HTTP(S) URL without credentials, query or fragment")
        local = url.hostname in {"localhost", "127.0.0.1", "::1"}
        if p["billing_route"] == "local" and not local:
            raise ValueError("Local route requires a loopback endpoint; remote hosts require explicit API authorization")
        if not local and url.scheme != "https":
            raise ValueError("Remote API endpoints require HTTPS")
        p.setdefault("response_format", "json_schema")
        if p["response_format"] not in {"json_schema", "json_object"}:
            raise ValueError("Select a supported JSON response format explicitly; no silent fallback")
        params = p.setdefault("parameters", {})
        if not isinstance(params, dict):
            raise ValueError("parameters must be an object")
        # Narrow native options only; callers cannot override identity, tools,
        # messages, output limits, credential headers or redirect requests.
        if set(params) - {"temperature", "top_p", "seed", "reasoning_effort", "thinking", "chat_template_kwargs"}:
            raise ValueError("Unsupported provider-native parameter")
        for key in ("thinking", "chat_template_kwargs"):
            if key in params and not isinstance(params[key], dict):
                raise ValueError(key + " must be an object")
        if p["effort"]:
            if p.get("effort_parameter") != "reasoning_effort":
                raise ValueError("Compatible endpoint effort needs an explicitly supported effort_parameter=reasoning_effort; native thinking can instead be declared in parameters")
            if "reasoning_effort" in params and params["reasoning_effort"] != p["effort"]:
                raise ValueError("Effort declarations disagree")
            params["reasoning_effort"] = p["effort"]
        if p["billing_route"] == "api" and p["authorized"]:
            if not p.get("max_request_usd") or any(p.get(k) is None for k in ("input_price_per_million", "output_price_per_million")):
                raise ValueError("Authorized hosted endpoint requires max_request_usd and declared input/output prices for conservative admission")
    return p


def recommend(inventory: dict) -> dict:
    """One unapproved starting point; detecting a CLI does not authorize use."""
    context = inventory.get("active_context", {})
    harness, model, effort = (context.get(key) for key in ("harness", "model", "effort"))
    installed = inventory.get("harnesses", {}).get(harness, {})
    if harness in {"codex", "claude"} and installed.get("installed") and model and effort:
        base = {"adapter": harness, "model": model, "effort": effort, "billing_route": "subscription",
                "cli_path": installed.get("path"), "authorized": False, "qualification_status": "unqualified"}
        if harness == "codex":
            base["codex_context"] = "source-only-v1"
        note = "Prefer the active harness and exact host-supplied model/effort. Choose cheaper stage-specific profiles only from verified available models; startup does not infer access or scientific qualification."
    else:
        base = {"adapter": "manual", "model": model or "human-selected-agent", "effort": effort,
                "authorized": False}
        note = "Use the current agent through work exchange until its exact automatic model, effort and CLI route are supplied. An installed CLI alone does not establish the active harness or usable models."
    cores = inventory.get("cpu", {}).get("usable_cores") or 1
    memory = inventory.get("memory", {}).get("usable_limit_bytes")
    profiles = {role: validate_profile(base) for role in ROLES}
    # These are tested candidates, selected only when the current host explicitly
    # reports their availability. An installed Codex binary is insufficient.
    known = set(context.get("available_models", []))
    if base["adapter"] == "codex":
        if "gpt-6-luna" in known:
            profiles["title"].update(model="gpt-6-luna", effort="medium")
        if "gpt-6.1-sol" in known:
            profiles["abstract"].update(model="gpt-6.1-sol", effort="medium")
    return {"mode": "discovery", "profiles": profiles,
            "resources": {"authorized": False, "cpu_workers": max(1, min(2, int(cores))), "model_workers": 2,
                          "retrieval_workers": 4, "memory_limit_bytes": int(memory * 0.5) if memory else None,
                          "gpu_memory_limit_bytes": None, "max_calls": None, "max_tokens": None,
                          "max_spend_usd": 0, "max_wall_seconds": None, "max_citation_depth": None, "max_indexed_papers": None},
            "reason": note, "remote_resources": "Ask only for additional hosts/quotas and permitted use; no inference performed."}


def build_plan(inventory: dict, profiles: dict, resources: dict, workload: dict = None,
               calibration_review_profile: dict = None) -> dict:
    if not isinstance(profiles, dict) or not profiles:
        raise ValueError("At least one stage profile is required")
    if not isinstance(resources, dict):
        raise ValueError("Resources must be an object")
    unknown = set(resources) - RESOURCE_KEYS
    if unknown:
        raise ValueError("Unknown resource keys: " + ", ".join(sorted(unknown)))
    selected = {stage: validate_profile(value) for stage, value in profiles.items()}
    review_profile = validate_profile(calibration_review_profile) if calibration_review_profile is not None else None
    all_profiles = list(selected.values()) + ([review_profile] if review_profile else [])
    r = copy.deepcopy(resources)
    if "operational_policy" in r:
        from .execution_policy import validate as validate_policy
        r["operational_policy"] = validate_policy(r["operational_policy"])
    r.setdefault("authorized", False)
    if not isinstance(r["authorized"], bool):
        raise ValueError("Resource authorization must be boolean")
    for key, default in (("cpu_workers", 1), ("model_workers", 1), ("retrieval_workers", 2)):
        r.setdefault(key, default)
        _number(r[key], key, minimum=1, integer=True, nullable=False)
    for key, default in (("discovery_buffer_papers", max(250, 100 * r["model_workers"])),
                         ("sanity_interval_seconds", 60)):
        r.setdefault(key, default)
        _number(r[key], key, minimum=1, integer=key == "discovery_buffer_papers", nullable=False)
    for key in ("memory_limit_bytes", "gpu_memory_limit_bytes", "max_calls", "max_tokens"):
        r.setdefault(key, None)
        _number(r[key], key, minimum=1, integer=True)
    for key in ("max_spend_usd", "max_wall_seconds"):
        r.setdefault(key, None)
        _number(r[key], key, minimum=0)
    r.setdefault("max_indexed_papers", None)
    if r["max_indexed_papers"] is not None and (type(r["max_indexed_papers"]) is not int or r["max_indexed_papers"] < 1):
        raise ValueError("max_indexed_papers must be null or a positive integer")
    r.setdefault("max_citation_depth", None)
    depth = r["max_citation_depth"]
    if depth is not None and (type(depth) is not int or depth < 0):
        raise ValueError("max_citation_depth must be null or a nonnegative integer; seeds are depth 0")
    if r["max_wall_seconds"] is not None and r["max_wall_seconds"] <= 0:
        raise ValueError("max_wall_seconds must be positive when supplied")
    cores = inventory.get("cpu", {}).get("usable_cores")
    memory = inventory.get("memory", {}).get("usable_limit_bytes")
    warnings = []
    if r["max_indexed_papers"] is not None:
        warnings.append("Indexed-paper threshold stops new search requests, finishes admitted responses (possible overshoot), and drains existing papers; it is not scientific saturation.")
    if depth is not None:
        warnings.append("Citation expansion is bounded at depth %d from each seed or independent query root. Papers at the boundary remain screenable; deferred expansion is not scientific saturation." % depth)
    if cores and r["cpu_workers"] > max(1, math.ceil(cores)):
        warnings.append("CPU workers exceed observed usable cores; use only if calibration establishes a benefit.")
    if memory and r["memory_limit_bytes"] and r["memory_limit_bytes"] > memory:
        raise ValueError("Requested local memory exceeds observed usable memory")
    if r["authorized"]:
        if any(not p["authorized"] and p["adapter"] != "manual" for p in all_profiles):
            raise ValueError("Every automated stage profile requires explicit authorization")
        if any(p["billing_route"] == "api" for p in all_profiles) and not r["max_spend_usd"]:
            raise ValueError("Hosted API work requires a positive overall spending cap")
        if r["max_tokens"] is not None and any(p["adapter"] in {"codex", "claude"} for p in all_profiles):
            raise ValueError("CLI output-token allowances are not hard provider limits: use observed token telemetry and optional call/time limits, or an endpoint with an enforced output limit for a strict token budget")
    if any(p["adapter"] in {"codex", "claude"} for p in selected.values()):
        warnings.append("CLI max_output_tokens is a planning allowance, not an enforced generation bound. Per-call timeouts and any user-selected call budget are enforced; actual tokens remain provider telemetry.")
    if inventory.get("cloud_quota") is None:
        warnings.append("Cloud/subscription quota unknown; no inferred entitlement or paid fallback. User-selected limits are enforceable; provider quota exhaustion requires a checkpoint.")
    if any(p["qualification_status"] == "unqualified" for p in selected.values()):
        warnings.append("Model reading quality is unqualified. Check initial real seed decisions against the gates and flag discrepancies; no separate commissioning run is required.")
    estimates = {"status": "unmeasured", "wall_seconds": None, "cost_usd": None,
                 "reason": "Measure real stage throughput, retention and provider usage before estimating the whole sweep."}
    workload = workload or {}
    n = workload.get("logical_papers")
    if n is not None:
        _number(n, "logical_papers", minimum=0, integer=True, nullable=False)
        estimates["minimum_title_calls"] = math.ceil(n / 25)
        if r["max_calls"] is not None and estimates["minimum_title_calls"] > r["max_calls"]:
            warnings.append("The call allowance cannot cover even one title pass at the permitted maximum batch size; this is a bounded partial run.")
    result = {"version": "portable-plan-v1", "authorized": r["authorized"], "profiles": selected, "resources": r,
            "budgets": {"max_calls": r["max_calls"], "max_tokens": r["max_tokens"], "max_cost_usd": r["max_spend_usd"]},
            "estimates": estimates, "warnings": warnings, "workload": workload,
            "inventory_observed_at": inventory.get("observed_at")}
    if review_profile is not None:
        result["calibration_review_profile"] = review_profile
    return result
