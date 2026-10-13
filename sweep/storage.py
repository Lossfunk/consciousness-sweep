"""Inspect run storage and probe new-run SQLite I/O without moving any run.

Location checks identify a few explicit synchronized-directory conventions, not
the cause of a past I/O error or a certificate for every other filesystem.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import platform
import shutil
import sqlite3
import subprocess
import sys
import tempfile


PROBE_TIMEOUT_SECONDS = 10


class StorageError(ValueError):
    def __init__(self, reason, report):
        self.report = report
        super().__init__(reason + " Choose ordinary local storage and put the global --root option before the command: "
                         "python -m sweep --root <local-directory> doctor. No existing run was relocated.")


def _known_sync_roots():
    """Explicit host conventions/configuration; no broad substring matching."""
    roots = []
    if platform.system() == "Darwin":
        home = Path.home()
        roots.extend((
            ("macOS File Provider storage", "macos-conventional-path", home / "Library" / "CloudStorage"),
            ("iCloud documents", "macos-conventional-path", home / "Library" / "Mobile Documents"),
        ))
    for name in ("OneDrive", "OneDriveCommercial", "OneDriveConsumer"):
        value = os.environ.get(name)
        if value:
            roots.append(("OneDrive", "configured-environment:" + name, Path(value).expanduser()))
    return roots


def _suggested_local_root():
    if platform.system() == "Darwin":
        return Path.home() / "Library" / "Application Support" / "consciousness-sweep"
    if platform.system() == "Windows":
        base = Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local")
    else:
        base = Path(os.environ.get("XDG_STATE_HOME") or Path.home() / ".local" / "state")
    return base / "consciousness-sweep"


def inspect_storage(root):
    """Read-only observations about the exact prospective run-parent directory.

    Missing directories are assessed through their closest existing ancestor;
    this function never creates that path or opens a SQLite database.
    """
    report = {
        "version": "portable-storage-inspection-v1", "requested_path": str(root),
        "resolved_path": None, "closest_existing_parent": None, "path_exists": None,
        "path_is_directory": None, "parent_is_directory": None,
        "writable_by_access_check": None, "free_bytes": None, "total_bytes": None,
        "python_version": platform.python_version(), "sqlite_version": sqlite3.sqlite_version,
        "recognized_sync_locations": [], "errors": [], "probe_performed": False,
        "suggested_local_root": str(_suggested_local_root()),
        "limitations": [
            "Path conventions and environment configuration identify known sync locations; they do not establish the cause of an I/O incident.",
            "No recognized sync location is not proof that storage is local, unsynchronized or reliable.",
            "Permission and free-space observations can change; no SQLite write probe was performed by this inspection.",
        ],
    }
    try:
        supplied = Path(root).expanduser()
        # Normalize lexical '..' without losing the independently resolved
        # symlink target. A path spelling is not itself a filesystem boundary.
        requested = Path(os.path.abspath(supplied))
        resolved = supplied.resolve()
        report.update(requested_path=str(requested), resolved_path=str(resolved))
        report["path_exists"] = resolved.exists()
        report["path_is_directory"] = resolved.is_dir() if report["path_exists"] else None
        ancestor = resolved
        while not ancestor.exists() and ancestor.parent != ancestor:
            ancestor = ancestor.parent
        report["closest_existing_parent"] = str(ancestor)
        report["parent_is_directory"] = ancestor.is_dir()
        report["writable_by_access_check"] = bool(report["parent_is_directory"] and os.access(ancestor, os.W_OK | os.X_OK))
        try:
            disk = shutil.disk_usage(ancestor)
            report.update(free_bytes=disk.free, total_bytes=disk.total)
        except OSError as exc:
            report["errors"].append({"operation": "disk-usage", "error": type(exc).__name__, "reason": str(exc)})
        for provider, evidence, path in _known_sync_roots():
            configured = Path(os.path.abspath(path))
            for matched_path in (requested, resolved):
                if any(matched_path.is_relative_to(boundary) for boundary in (configured, path.resolve())):
                    report["recognized_sync_locations"].append({
                        "provider": provider, "evidence": evidence, "root": str(configured),
                        "matched_path": str(matched_path),
                    })
                    break
    except (OSError, ValueError, RuntimeError) as exc:
        report["errors"].append({"operation": "inspect-path", "error": type(exc).__name__, "reason": str(exc)})
    if report["errors"] or not report["parent_is_directory"] or report["path_is_directory"] is False:
        report["assessment"] = "invalid-or-unavailable-path"
    elif report["recognized_sync_locations"]:
        report["assessment"] = "recognized-sync-managed-location"
    elif report["writable_by_access_check"] is False:
        report["assessment"] = "not-writable-by-access-check"
    else:
        report["assessment"] = "no-recognized-storage-hazard"
    return report


_PROBE_SCRIPT = r'''
import json, sqlite3, sys
connections = []
operation = "connect"
try:
    writer = sqlite3.connect(sys.argv[1], timeout=2)
    connections.append(writer)
    operation = "enable-wal"
    mode = writer.execute("PRAGMA journal_mode=WAL").fetchone()[0]
    if mode.lower() != "wal":
        raise RuntimeError("Selected storage did not enable SQLite WAL mode")
    writer.execute("PRAGMA synchronous=FULL")
    operation = "transaction-write"
    with writer:
        writer.execute("CREATE TABLE probe(value TEXT NOT NULL)")
        writer.execute("INSERT INTO probe VALUES ('durable-local-fixture')")
    operation = "second-connection-read"
    reader = sqlite3.connect(sys.argv[1], timeout=2)
    connections.append(reader)
    if reader.execute("SELECT value FROM probe").fetchall() != [("durable-local-fixture",)]:
        raise RuntimeError("Committed SQLite scratch value was not visible to another connection")
    reader.close()
    connections.remove(reader)
    operation = "reopen-read"
    reader = sqlite3.connect(sys.argv[1], timeout=2)
    connections.append(reader)
    if reader.execute("SELECT value FROM probe").fetchall() != [("durable-local-fixture",)]:
        raise RuntimeError("Committed SQLite scratch value changed after reopening")
    operation = "wal-checkpoint"
    checkpoint = writer.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()
    if checkpoint[0] != 0:
        raise RuntimeError("SQLite scratch checkpoint remained busy")
    operation = "integrity-check"
    if writer.execute("PRAGMA integrity_check").fetchall() != [("ok",)]:
        raise RuntimeError("SQLite scratch integrity check failed")
    result = {"ok": True, "journal_mode": mode, "sqlite_version": sqlite3.sqlite_version,
              "checks": ["transaction-write", "second-connection-read", "reopen-read", "wal-checkpoint", "integrity-check"]}
except Exception as exc:
    result = {"ok": False, "operation": operation, "error": type(exc).__name__, "reason": str(exc),
              "sqlite_errorcode": getattr(exc, "sqlite_errorcode", None),
              "sqlite_errorname": getattr(exc, "sqlite_errorname", None)}
finally:
    for connection in reversed(connections):
        try:
            connection.close()
        except Exception as exc:
            detail = {"operation": "close", "error": type(exc).__name__, "reason": str(exc),
                      "sqlite_errorcode": getattr(exc, "sqlite_errorcode", None),
                      "sqlite_errorname": getattr(exc, "sqlite_errorname", None)}
            if result["ok"]:
                result = {"ok": False, **detail}
            else:
                result.setdefault("cleanup_errors", []).append(detail)
print(json.dumps(result))
sys.exit(0 if result["ok"] else 2)
'''


def _probe_sqlite(directory):
    # Reuse the bounded posix_spawn runner already used by source extraction;
    # do not fork an interpreter containing active native-library threads.
    from .sources import _run_extraction_process
    done = _run_extraction_process([sys.executable, "-B", "-c", _PROBE_SCRIPT,
                                    str(Path(directory) / "probe.sqlite3")],
                                   timeout=PROBE_TIMEOUT_SECONDS, max_output_bytes=16384)
    try:
        result = json.loads(done.stdout)
    except (ValueError, TypeError) as exc:
        raise ValueError("SQLite scratch probe did not return a valid diagnostic") from exc
    if not isinstance(result, dict) or type(result.get("ok")) is not bool or (done.returncode == 0) != result["ok"]:
        raise ValueError("SQLite scratch probe returned an inconsistent result")
    return result


def require_new_run_storage(root):
    """Check/probe a new run's parent before the coordinator creates RUN_ID.

    This never relocates an existing run or edits its files. Only the unique
    scratch directory created here is removed, even when the probe fails.
    """
    report = inspect_storage(root)
    assessment = report["assessment"]
    if assessment == "recognized-sync-managed-location":
        raise StorageError("New SQLite run storage is inside a recognized synchronized location: " + report["resolved_path"] + ".", report)
    if assessment != "no-recognized-storage-hazard":
        raise StorageError("New run storage is unavailable or not a writable directory: " + report["requested_path"] + ".", report)
    scratch = None
    try:
        scratch = Path(tempfile.mkdtemp(prefix=".sweep-storage-probe-", dir=report["closest_existing_parent"]))
        report["probe_performed"] = True
        report["probe"] = _probe_sqlite(scratch)
        report["probe"]["timeout_seconds"] = PROBE_TIMEOUT_SECONDS
        report["probe"]["storage_parent"] = report["closest_existing_parent"]
        if not report["probe"]["ok"]:
            raise StorageError("New-run SQLite storage probe failed: " + report["probe"].get("reason", "unknown failure") + ".", report)
    except StorageError:
        raise
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        report["probe"] = {"ok": False, "error": type(exc).__name__, "reason": str(exc),
                           "timeout_seconds": PROBE_TIMEOUT_SECONDS}
        raise StorageError("New-run SQLite storage probe failed: " + str(exc) + ".", report) from exc
    finally:
        primary_error = sys.exc_info()[1]
        if scratch is not None:
            try:
                shutil.rmtree(scratch)
                report["scratch_removed"] = True
            except OSError as exc:
                report["scratch_removed"] = False
                report["scratch_path"] = str(scratch)
                report["cleanup_error"] = {"error": type(exc).__name__, "reason": str(exc)}
                if primary_error is None:
                    raise StorageError("Could not remove the owned storage probe directory: " + str(scratch) + ".", report) from exc
    report["limitations"][-1] = "A bounded scratch SQLite check succeeded at the existing parent; future permissions, space, synchronization and filesystem reliability remain unproven by this check."
    return report
