"""Execution-environment holds; no scientific decisions or provider inference.

Repeated multi-host DNS failures corroborated against metadata hosts suspend
remote transport. Local sources and local workers remain serviceable. Holds are
durable, require explicit repair, and never consume or refund model allowance.
"""
import contextlib
import contextvars
import json
import os
from pathlib import Path
import socket
import tempfile
import time
from urllib.parse import urlsplit

from .common import canonical

_STORE = contextvars.ContextVar("sweep_host_access_store", default=None)
KEY = "host-access"
DNS_CONTROLS = ("api.openalex.org", "www.ebi.ac.uk")
DNS_WINDOW_SECONDS = 120


def status(store):
    return store.get_state(KEY) or {"network": None, "codex_state": None, "dns_hosts": []}


def _update(store, mutate, reason):
    with store._transaction() as conn:
        row = conn.execute("SELECT value FROM meta WHERE key=?", ("state:" + KEY,)).fetchone()
        old = json.loads(row[0]) if row else {"network": None, "codex_state": None, "dns_hosts": []}
        value = mutate(dict(old, dns_hosts=list(old.get("dns_hosts", []))))
        if value != old:
            store._event(conn, "control_updated", {"key": KEY, "previous": old, "value": value, "reason": reason})
            conn.execute("INSERT OR REPLACE INTO meta VALUES(?,?)", ("state:" + KEY, canonical(value)))
        return value


def inspect_launch(profiles=(), *, timeout=10):
    """Bounded launch checks, with DNS corroboration of a reported restriction.

    Enclosing-host environment markers can survive an approved host launch.
    DNS resolution disproves a blanket DNS restriction, not every HTTP/model block.
    Only a disposable write is attempted in an existing selected Codex state dir.
    """
    network = "unobserved"
    if timeout > 0 and os.environ.get("CODEX_SANDBOX_NETWORK_DISABLED") == "1":
        network = "dns-resolvable" if _dns_probe(DNS_CONTROLS, timeout=timeout) else "restricted"
    state = "not-selected"
    if any(p.get("adapter") == "codex" for p in profiles):
        directory = Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex")
        state = "unobserved"
        if directory.is_dir():
            try:
                with tempfile.TemporaryFile(prefix="sweep-access-", dir=directory):
                    pass
                state = "writable"
            except OSError:
                state = "unwritable"
    return {"network": network, "codex_state": state, "inference_performed": False,
            "limitation": "No restriction observed is not proof of network, provider access or writable existing CLI databases."}


def record_launch(store, profiles, *, timeout=10):
    probe = inspect_launch(profiles, timeout=timeout)
    store.event("host_launch_check", dict(probe, observed_at=time.time()))
    def mutate(value):
        if probe["network"] == "restricted" and not value.get("network"):
            value["network"] = {"reason": "The launch reports disabled network access and the metadata-host DNS check failed", "at": time.time()}
        if probe["codex_state"] == "unwritable" and not value.get("codex_state"):
            value["codex_state"] = {"reason": "Selected Codex state directory is not writable in this launch environment", "at": time.time()}
        return value
    return _update(store, mutate, "Record local launch restrictions; retain existing holds until explicit repair")


def remote_profile(profile):
    return profile.get("adapter") in {"codex", "claude"} or (
        profile.get("adapter") in {"command", "openai-compatible"} and profile.get("billing_route") != "local")


def profile_blocked(value, profile):
    return bool(value.get("network") and remote_profile(profile) or
                value.get("codex_state") and profile.get("adapter") == "codex")


@contextlib.contextmanager
def transport_scope(store):
    token = _STORE.set(store)
    try:
        yield
    finally:
        _STORE.reset(token)


def network_hold():
    store = _STORE.get()
    return status(store).get("network") if store is not None else None


def network_error(exc):
    reason = getattr(exc, "reason", exc)
    return "dns" if isinstance(reason, socket.gaierror) else None


def observe(url, *, http_status=None, error=None, check_timeout=10):
    """Observe only real transport outcomes, never cached receipts or source text."""
    store = _STORE.get()
    if store is None or http_status is None and error != "dns":
        return
    host = urlsplit(url).hostname
    if not host:
        return
    def mutate(value):
        if value.get("network"):
            return value
        if http_status is not None:
            value["dns_hosts"] = []  # Even a 403/429 proves an HTTP connection.
            value.pop("dns_started", None)
        else:
            if time.time() - value.get("dns_started", 0) > DNS_WINDOW_SECONDS:
                value["dns_hosts"] = []
                value["dns_started"] = time.time()
            if host not in value["dns_hosts"] and len(value["dns_hosts"]) < 3:
                value["dns_hosts"].append(host)
        return value
    observed = _update(store, mutate, "Record transport connectivity only; scientific obligations remain pending")
    if observed.get("network") or len(observed["dns_hosts"]) < 3:
        return
    # Stale/dead article domains alone must not block a functioning network.
    # No credentials, HTTP request or model call is involved in this check.
    reachable = _dns_probe(DNS_CONTROLS, timeout=check_timeout)
    def corroborate(value):
        if value != observed:  # Another response/recovery won the race.
            return value
        if reachable:
            value["dns_hosts"] = []
            value.pop("dns_started", None)
        else:
            value["network"] = {"reason": "DNS failed across three hosts and the metadata-host DNS recheck failed",
                                "at": time.time(), "hosts": list(value["dns_hosts"])}
        return value
    _update(store, corroborate, "Corroborate multi-host DNS failure against metadata hosts")


def _dns_probe(hosts, *, timeout=10):
    # DNS calls themselves can hang. Use the existing bounded subprocess helper.
    from .capabilities import _capture
    import sys
    code = "import socket,sys\nfor h in sys.argv[1:]:\n try: socket.getaddrinfo(h,443,type=socket.SOCK_STREAM)\n except OSError: continue\n sys.exit(0)\nsys.exit(1)"
    result, _ = _capture([sys.executable, "-c", code, *hosts], timeout=timeout)
    return result == 0


def resolve(store, profiles, reason, scopes):
    if not isinstance(reason, str) or not reason.strip():
        raise ValueError("Host recovery requires the actual repair reason")
    if not scopes or set(scopes) - {"network", "codex_state"}:
        raise ValueError("Select network and/or codex_state for host recovery")
    before = status(store)
    if any(not before.get(scope) for scope in scopes):
        raise ValueError("Selected host hold is not active; inspect current status")
    probe = inspect_launch(profiles)
    if "network" in scopes:
        if probe["network"] == "restricted":
            raise ValueError("Network remains disabled in this launch environment")
        if not _dns_probe(DNS_CONTROLS):
            raise ValueError("Bounded DNS recheck failed; keep the network hold")
    if "codex_state" in scopes and probe["codex_state"] != "writable":
        raise ValueError("Codex state writability was not established in this launch environment")
    def mutate(value):
        if value != before:
            raise ValueError("Host state changed during recovery; inspect it again")
        for scope in scopes:
            value[scope] = None
        if "network" in scopes:
            value["dns_hosts"] = []
            value.pop("dns_started", None)
        return value
    value = _update(store, mutate, "Explicit host recovery: " + reason.strip())
    return {"host_access": value, "checks": probe, "inference_performed": False,
            "limitation": "DNS resolution does not establish successful HTTP transport or model access; verify ordinary work after resume."}
