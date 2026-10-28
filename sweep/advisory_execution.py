"""Managed advisory Codex execution and conservative audit of its JSONL events.

This audits observed execution, not absence of advertised tools or provider identity.
It never opens a sweep ledger or changes source-reading adapters.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
import shutil
import subprocess
import tempfile

from .adapters import CODEX_CONFIG, CODEX_SOURCE_CONFIG, _environment, _metadata, _run


TRANSPORT_VERSION = "advisory-chatgpt-no-replay-v1"
TRANSPORT_PROFILE = "sweep-chatgpt-no-replay"


def transport_policy(timeout):
    if not isinstance(timeout, (int, float)) or isinstance(timeout, bool) or timeout <= 0:
        raise ValueError("Positive bound advisory timeout required")
    return {"version": TRANSPORT_VERSION, "config_id": TRANSPORT_PROFILE,
            "request_max_retries": 0, "stream_max_retries": 0,
            "unbounded_connection_retries": False, "stream_idle_timeout_ms": max(1, int(timeout * 1000)),
            "supports_websockets": False, "transport": "https-event-stream", "auth": "existing-chatgpt-login", "endpoint_override": None}


def transport_settings(timeout):
    policy = transport_policy(timeout)
    prefix = "model_providers." + TRANSPORT_PROFILE + "."
    provider = {"name": "OpenAI", "wire_api": "responses", "requires_openai_auth": True,
                "supports_websockets": policy["supports_websockets"],
                "request_max_retries": 0, "stream_max_retries": 0,
                "stream_idle_timeout_ms": policy["stream_idle_timeout_ms"]}
    return ["model_provider=" + json.dumps(TRANSPORT_PROFILE), 'forced_login_method="chatgpt"',
            "features.unbounded_connection_retries=false"] + [prefix + k + "=" + json.dumps(v) for k, v in provider.items()]


def retry_observed(raw):
    # CLI diagnostics only; source/model text is not passed to this detector.
    text = raw.decode("utf-8", errors="replace")
    return bool(re.search(r"retrying\s+(?:sampling\s+request|stream|request)|reconnecting\s*\.\.\.|falling back (?:to https?|from websockets)", text, re.I))


def audit_transport(directory, execution):
    """Reproduce new managed-launch evidence without changing legacy audits."""
    from .advisory import _read, _bytes_hash
    if "transport_policy" not in execution:
        return None
    issues = []
    try:
        directory = Path(directory)
        launch = _read(directory / "codex-launch.json")
        job = _read(directory / "request.json")
        expected = transport_policy(job["timeout_seconds"])
        raw = (directory / "codex-stderr.txt").read_bytes()
        if execution["transport_policy"] != expected or launch.get("transport_policy") != expected:
            issues.append("transport-policy-mismatch")
        if _bytes_hash((directory / "codex-launch.json").read_bytes()) != execution.get("launch_sha256"):
            issues.append("launch-hash-mismatch")
        if _bytes_hash(raw) != execution.get("stderr_sha256"):
            issues.append("stderr-hash-mismatch")
        argv = launch["argv"]
        settings = {}
        for index, value in enumerate(argv[:-1]):
            if value == "-c":
                key, separator, setting = argv[index + 1].partition("=")
                if separator: settings[key] = setting
        required = dict(value.split("=", 1) for value in transport_settings(job["timeout_seconds"]))
        if any(settings.get(k) != value for k, value in required.items()):
            issues.append("no-replay-controls-missing-or-overridden")
        prefix = "model_providers." + TRANSPORT_PROFILE + "."
        if any((k.startswith(prefix) and k not in required) or k in {"openai_base_url", "chatgpt_base_url"} for k in settings):
            issues.append("unexpected-provider-endpoint-or-auth-setting")
        observed = retry_observed(raw)
    except (OSError, ValueError, KeyError, TypeError):
        observed = None
        issues.append("transport-evidence-unavailable")
    return {"version": TRANSPORT_VERSION,
            "status": "transport-retry-rejected" if observed else "transport-unverified" if issues else "configured-no-replay",
            "retry_observed": observed, "issues": sorted(set(issues)),
            "scope": "Configured CLI controls and observed stderr; not provider exactly-once execution or backend verification"}


def audit_events(raw, answer):
    from .advisory import _decode, _hash
    issues, events = [], []
    try:
        text = raw.decode("utf-8")
        for line in text.split("\n"):
            if line.strip():
                event = _decode(line)
                if not isinstance(event, dict):
                    raise ValueError("Nonobject event")
                events.append(event)
    except (ValueError, UnicodeError):
        text = raw.decode("utf-8", errors="replace")
        issues.append("malformed-event-stream")
    try:
        metadata, _ = _metadata("codex", text)
    except (ValueError, TypeError, KeyError):
        issues.append("invalid-event-fields")
        metadata = {"tool_use_observed": False, "observed_model": None, "observed_effort": None, "usage": None}
    if not raw.endswith(b"\n"):
        issues.append("unterminated-event-stream")
    threads, turns, completions, phase = [], 0, 0, 0
    final = None
    allowed_items = {"agent_message", "reasoning"}
    for event in events:
        kind = event.get("type")
        if not isinstance(kind, str):
            issues.append("invalid-event-type"); continue
        if phase == 3:
            issues.append("events-after-terminal")
        if kind == "thread.started":
            tid = event.get("thread_id")
            if phase != 0 or not isinstance(tid, str) or not tid.strip():
                issues.append("invalid-thread-start")
            threads.append(tid)
            phase = 1
        elif kind == "turn.started":
            if phase != 1:
                issues.append("invalid-turn-start")
            turns += 1
            phase = 2
        elif kind in {"session.started", "session.configured"}:
            # Advertised tool definitions in metadata are not evidence of tool use.
            pass
        elif kind in {"item.started", "item.updated", "item.completed"}:
            item = event.get("item")
            if phase != 2 or not isinstance(item, dict):
                issues.append("invalid-item-event")
                continue
            if not isinstance(item.get("type"), str) or item["type"] not in allowed_items:
                issues.append("non-annotation-item")
            if kind == "item.completed" and item.get("type") == "agent_message":
                try:
                    final = _decode(item["text"])
                except (ValueError, TypeError, KeyError):
                    final = None
        elif kind == "turn.completed":
            if phase != 2:
                issues.append("invalid-turn-completion")
            completions += 1
            phase = 3
        else:
            issues.append("unsupported-or-failed-event")
    if len(threads) != 1 or turns != 1 or completions != 1 or phase != 3:
        issues.append("incomplete-or-multiple-turns")
    if final != answer:
        issues.append("final-answer-does-not-match-submission")
    tools = metadata["tool_use_observed"]
    status = "tool-use-rejected" if tools else "execution-unverified" if issues else "verified-no-tool-use"
    return {"version": "advisory-codex-events-v1", "status": status,
            "events_sha256": hashlib.sha256(raw).hexdigest(), "answer_canonical_sha256": _hash(answer),
            "tool_use_observed": True if tools else None if issues else False,
            "issues": sorted(set(issues)), "worker_context_id": threads[0] if len(threads) == 1 else None,
            "observed_model": metadata["observed_model"], "observed_effort": metadata["observed_effort"],
            "usage": metadata["usage"], "tool_availability": "not-certified-empty",
            "scope": "Observed JSONL execution only; not enforced tool absence or provider verification"}


def run_job(workspace, job_id, *, owner, executable=None):
    """One managed process per prepared ticket. Never redispatch an existing ticket."""
    from . import advisory as a
    root, manifest = a._manifest(workspace)
    entry = next((e for e in manifest["jobs"] if e["job_id"] == job_id), None)
    if not entry:
        raise ValueError("Unknown advisory job")
    directory, job = a._job(root, entry)
    if job["profile"]["harness"] != "codex":
        raise ValueError("Managed advisory execution supports the requested Codex harness only; no fallback")
    resolved = shutil.which(str(executable or "codex"))
    if not resolved:
        raise ValueError("Requested Codex executable is unavailable; no inference or fallback")
    version = subprocess.run([resolved, "--version"], capture_output=True, timeout=15)
    if version.returncode or not version.stdout.startswith(b"codex-cli "):
        raise ValueError("Executable did not identify as Codex CLI; no inference or fallback")
    claim = a.claim(root, job_id, owner=owner)
    if not claim["new_dispatch"]:
        return claim
    ticket = claim["ticket"]
    events = directory / "codex-events.jsonl"
    stderr = directory / "codex-stderr.txt"
    answer = directory / "codex-answer.json"
    execution = directory / "codex-execution.json"
    for p in (events, stderr, answer, execution, directory / "codex-launch.json"):
        if p.exists() or p.is_symlink():
            raise ValueError("Existing invocation evidence preserved; reconcile rather than relaunch")
    with tempfile.TemporaryDirectory(prefix="sweep-advisory-") as cwd:
        argv = [resolved, "exec", "--ignore-user-config", "--ephemeral", "--skip-git-repo-check",
                "--sandbox", "read-only", "--cd", cwd, "--model", job["profile"]["model"],
                "-c", "model_reasoning_effort=" + json.dumps(job["profile"]["effort"]),
                "--json", "--output-schema", str(directory / "schema.json"), "-o", str(answer)]
        for setting in list(CODEX_CONFIG + CODEX_SOURCE_CONFIG) + transport_settings(job["timeout_seconds"]):
            argv += ["-c", setting]
        argv.append("-")
        a._once(directory / "codex-launch.json", {
            "job_id": job_id, "dispatch_id": ticket["dispatch_id"], "binding_sha256": job["binding_sha256"],
            "requested_profile": job["profile"], "argv": argv,
            "executable_sha256": a._bytes_hash(Path(resolved).read_bytes()),
            "cli_version": version.stdout.decode("utf-8").strip(),
            "prompt_sha256": entry["prompt_sha256"], "schema_sha256": entry["schema_sha256"],
            "transport_policy": transport_policy(job["timeout_seconds"]),
            "fresh_process_and_temporary_cwd": True, "project_documents_disabled": True,
            "tool_availability": "not-certified-empty", "billing": "Existing ChatGPT login; no API fallback"})
        try:
            outcome = _run(argv, directory / "prompt.txt", events, stderr,
                           env=_environment({"adapter": "codex"}), cwd=cwd, timeout=job["timeout_seconds"])
        except OSError as exc:
            outcome = {"exit_code": None, "timed_out": False, "launcher_error": type(exc).__name__}
            for path in (events, stderr):
                if not path.exists():
                    a._stage_bytes(path, b"")
    metadata, _ = _metadata("codex", events.read_bytes().decode("utf-8", errors="replace"))
    a._once(execution, {
        "dispatch_id": ticket["dispatch_id"], "requested_profile": job["profile"],
        "outcome": "completed" if outcome["exit_code"] == 0 and not outcome["timed_out"] else "incomplete",
        "reported": {"harness": "codex", "model": metadata["observed_model"], "effort": metadata["observed_effort"], "provider_identity": None},
        "usage": metadata["usage"], "process": outcome, "transport_policy": transport_policy(job["timeout_seconds"]),
        "usage_scope": "Observed JSONL usage; unreported provider consumption remains unknown",
        "launch_sha256": a._bytes_hash((directory / "codex-launch.json").read_bytes()),
        "events_sha256": a._bytes_hash(events.read_bytes()), "stderr_sha256": a._bytes_hash(stderr.read_bytes())})
    transport = audit_transport(directory, a._read(execution))
    if outcome["exit_code"] == 0 and not outcome["timed_out"] and answer.is_file():
        try:
            result = a.submit(root, job_id, answer, execution, events_path=events)
        except ValueError:
            result = {"accepted": False, "status": "invalid-response", "job_id": job_id,
                      "reason": "Saved invocation/answer was not accepted; inspect exact evidence, no automatic retry"}
    else:
        result = {"accepted": False, "status": "execution-incomplete", "job_id": job_id,
                  "reason": "Saved process failure/timeout; model admission or charges may be unknown, no automatic retry"}
    if transport and transport["status"] != "configured-no-replay" and not (directory / "receipt.json").exists():
        result.update(accepted=False, status=transport["status"], transport_audit=transport)
    a._once(directory / "codex-terminal.json", result)
    return result
