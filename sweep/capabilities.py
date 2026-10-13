"""Read-only, best-effort host inventory; no inference, credentials or installs."""
from __future__ import annotations

import datetime as dt
import json
import os
from pathlib import Path
import platform
import re
import shutil
import signal
import subprocess
import tempfile
import time


CODEX_APP_CLI = "/Applications/ChatGPT.app/Contents/Resources/codex-cli/CodexCLI.app/Contents/MacOS/codex"


def _capture(argv, timeout=5):
    # Explicit posix_spawn also for read-only probes: do not revive the macOS
    # fork-with-active-native-threads failure during periodic capacity checks.
    try:
        if os.name == "posix" and hasattr(os, "posix_spawn"):
            with tempfile.TemporaryFile() as out, open(os.devnull, "rb") as inp, open(os.devnull, "wb") as err:
                executable = shutil.which(argv[0]) or argv[0]
                pid = os.posix_spawn(executable, argv, dict(os.environ), setpgroup=0, file_actions=[
                    (os.POSIX_SPAWN_DUP2, inp.fileno(), 0), (os.POSIX_SPAWN_DUP2, out.fileno(), 1),
                    (os.POSIX_SPAWN_DUP2, err.fileno(), 2)])
                started = time.monotonic()
                while True:
                    finished, status = os.waitpid(pid, os.WNOHANG)
                    if finished:
                        out.seek(0)
                        return os.waitstatus_to_exitcode(status), out.read(256 * 1024).decode(errors="replace")
                    if time.monotonic() - started >= timeout:
                        try:
                            os.killpg(pid, signal.SIGKILL)
                        except ProcessLookupError:
                            pass
                        os.waitpid(pid, 0)
                        return None, ""
                    time.sleep(0.05)
        done = subprocess.run(argv, capture_output=True, text=True, timeout=timeout,
                              stdin=subprocess.DEVNULL, check=False)
        return done.returncode, done.stdout
    except (OSError, subprocess.TimeoutExpired):
        return None, ""


def _integer(path):
    try:
        value = Path(path).read_text().strip()
        return int(value) if value != "max" else None
    except (OSError, ValueError):
        return None


def _memory():
    total = available = limit = None
    try:
        total = os.sysconf("SC_PHYS_PAGES") * os.sysconf("SC_PAGE_SIZE")
    except (ValueError, OSError, AttributeError):
        pass
    if Path("/proc/meminfo").is_file():
        try:
            info = {line.split(":")[0]: int(line.split()[1]) * 1024
                    for line in Path("/proc/meminfo").read_text().splitlines()}
            total, available = info.get("MemTotal", total), info.get("MemAvailable")
        except (ValueError, OSError):
            pass
        limit = (_integer("/sys/fs/cgroup/memory.max") or
                 _integer("/sys/fs/cgroup/memory/memory.limit_in_bytes"))
        used = (_integer("/sys/fs/cgroup/memory.current") or
                _integer("/sys/fs/cgroup/memory/memory.usage_in_bytes"))
        if limit is not None and total is not None and limit > total:
            limit = None
        if limit is not None and used is not None:
            available = min(available, max(0, limit - used)) if available is not None else max(0, limit - used)
    elif platform.system() == "Darwin":
        code, value = _capture(["/usr/sbin/sysctl", "-n", "hw.memsize"])
        if code == 0 and value.strip().isdigit():
            total = int(value)
        # Free pages alone would substantially understate reclaimable memory.
        # Report unknown available memory rather than pretending it is total RAM.
    return {"physical_bytes": total, "container_limit_bytes": limit,
            "usable_limit_bytes": min(total, limit) if total and limit else total or limit,
            "available_bytes": available}


def _cpu():
    host = os.cpu_count()
    try:
        affinity = len(os.sched_getaffinity(0))
    except (AttributeError, OSError):
        affinity = None
    quota = None
    try:
        values = Path("/sys/fs/cgroup/cpu.max").read_text().split()
        if values[0] != "max":
            quota = int(values[0]) / int(values[1])
    except (OSError, ValueError, IndexError, ZeroDivisionError):
        q = _integer("/sys/fs/cgroup/cpu/cpu.cfs_quota_us")
        p = _integer("/sys/fs/cgroup/cpu/cpu.cfs_period_us")
        if q and q > 0 and p and p > 0:
            quota = q / p
    candidates = [x for x in (host, affinity, quota) if x is not None]
    usable = min(candidates) if candidates else None
    try:
        load = list(os.getloadavg())
    except (AttributeError, OSError):
        load = None
    return {"logical_count": host, "affinity_count": affinity, "quota_cores": quota,
            "usable_cores": usable, "load_average": load}


def _gpus():
    result = []
    binary = shutil.which("nvidia-smi")
    if binary:
        code, text = _capture([binary, "--query-gpu=index,name,memory.total,memory.free",
                               "--format=csv,noheader,nounits"])
        if code == 0:
            import csv
            for row in csv.reader(text.splitlines()):
                try:
                    result.append({"vendor": "NVIDIA", "index": int(row[0]), "name": row[1].strip()[:120],
                                   "memory_bytes": int(row[2]) * 1024 ** 2,
                                   "free_memory_bytes": int(row[3]) * 1024 ** 2,
                                   "memory_kind": "dedicated"})
                except (ValueError, IndexError):
                    continue
    if platform.system() == "Darwin" and platform.machine() in {"arm64", "aarch64"}:
        result.append({"vendor": "Apple", "name": "Apple Silicon (exact GPU unobserved)",
                       "memory_bytes": None, "free_memory_bytes": None,
                       "memory_kind": "shared with system; do not add to RAM"})
    return result


def _tool(name):
    binary = shutil.which(name)
    if not binary and name == "codex" and Path(CODEX_APP_CLI).is_file():
        binary = CODEX_APP_CLI
    if not binary:
        return {"installed": False, "path": None, "version": None, "access": "unobserved"}
    code, output = _capture([binary, "--version"])
    # Version-only allowlist; do not export arbitrary startup/plugin output.
    versions = re.findall(r"\b\d+\.\d+(?:\.\d+)?(?:[-+][A-Za-z0-9.-]+)?", output)
    value = {"installed": True, "path": str(Path(binary).resolve()),
             "version": versions[0] if code == 0 and versions else None,
             "access": "unobserved", "model_catalog": "unobserved", "quota": None}
    if name == "codex":
        # Codex prints login status to stderr on some versions; _capture leaves
        # it unobserved rather than storing arbitrary diagnostic output.
        code, output = _capture([binary, "login", "status"])
        low = output.lower()
        if code == 0 and "chatgpt" in low:
            value["authentication_route"] = "subscription"
        elif code == 0 and "api key" in low:
            value["authentication_route"] = "api"
        else:
            value["authentication_route"] = "unobserved"
    elif name == "claude":
        code, output = _capture([binary, "auth", "status"])
        try:
            auth = json.loads(output)
            method = auth.get("authMethod")
            value["authentication_route"] = ({"claude.ai": "subscription", "oauth_token": "subscription",
                "api_key": "api", "api_key_helper": "api", "third_party": "third-party", "none": "none"}
                .get(method, "unobserved"))
        except (ValueError, AttributeError):
            value["authentication_route"] = "unobserved"
    return value


def active_context(*, harness=None, model=None, effort=None, available_models=None) -> dict:
    """Accept host-provided facts without guessing a provider's model catalog.

    Environment markers identify the enclosing harness only, never model access.
    Explicit arguments take precedence because nested agent shells can inherit
    another harness's environment.
    """
    source = "operator-supplied" if harness else "unobserved"
    if not harness:
        markers = []
        if os.environ.get("CODEX_THREAD_ID") or os.environ.get("CODEX_CI"):
            markers.append("codex")
        if os.environ.get("CLAUDECODE") == "1" or os.environ.get("CLAUDE_CODE_ENTRYPOINT"):
            markers.append("claude")
        if os.environ.get("OPENCLAW_SESSION_ID"):
            markers.append("openclaw")
        if len(markers) == 1:
            harness, source = markers[0], "environment-marker"
    if harness is not None and harness not in {"codex", "claude", "openclaw", "other", "manual"}:
        raise ValueError("Unknown active harness")
    models = list(dict.fromkeys(available_models or []))
    for value in [model, effort, *models]:
        if value is not None and (not isinstance(value, str) or not value.strip() or any(c in value for c in "\r\n\0")):
            raise ValueError("Host model and effort facts must be nonempty single-line names")
    if model and model not in models:
        models.append(model)
    return {"harness": harness, "harness_source": source, "model": model, "effort": effort,
            "available_models": models,
            "model_evidence": "operator-supplied host context; not independently probed" if models else "unobserved"}


def discover(root: Path, *, harness=None, model=None, effort=None, available_models=None) -> dict:
    """Inspect only the current host. Catalog presence never establishes access."""
    from .storage import inspect_storage
    root = Path(root).expanduser().absolute()
    storage = inspect_storage(root / "runs")
    storage["requested_global_root"] = str(root)
    return {"version": "capability-inventory-v1", "observed_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "system": platform.system(), "architecture": platform.machine(), "python": platform.python_version(),
            "cpu": _cpu(), "memory": _memory(), "disk": {"free_bytes": storage["free_bytes"], "total_bytes": storage["total_bytes"]},
            "storage": storage,
            "gpus": _gpus(), "harnesses": {name: _tool(name) for name in ("codex", "claude", "openclaw")},
            "active_context": active_context(harness=harness, model=model, effort=effort,
                                               available_models=available_models),
            "local_tools": {name: shutil.which(name) for name in ("pdftotext", "pdftoppm", "tesseract", "ollama")},
            "configured_credential_env_names": [name for name in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "ZAI_API_KEY")
                                                if name in os.environ],
            "cloud_quota": None, "remote_resources": "not supplied", "inference_performed": False,
            "limitations": ["Installed/configured is not authorized, qualified, or proof of model access.",
                            "Unobserved quotas are unknown, not unlimited.",
                            "GPU inventory is advisory; inference memory and throughput need measurement."]}
