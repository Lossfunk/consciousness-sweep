"""A local mutation lock. Never hold it across provider or network execution."""
from contextlib import contextmanager
import os
import json
from pathlib import Path
import threading

_guard = threading.Lock()
_locks = {}
_held = threading.local()


def writer_hold(conn, run):
    """An optional existing writer gate also holds ordinary runner admissions."""
    path = Path(run) / 'intake' / 'writer-gate.json'
    row = conn.execute("SELECT value FROM meta WHERE key='state:publication-control'").fetchone()
    control = json.loads(row[0]) if row else None
    if not path.exists():
        return 'writer-held' if control else None
    try:
        value = json.loads(path.read_bytes())
    except (ValueError, OSError):
        return 'writer-held'
    if not isinstance(value, dict) or value.get('mode') != 'OPEN': return 'writer-held'
    if control and any(value.get(key) != item for key, item in control.items()): return 'writer-held'
    return None


@contextmanager
def lock(run):
    path = Path(run).resolve() / 'intake' / 'publication-lane.lock'
    path.parent.mkdir(parents=True, exist_ok=True)
    key = str(path)
    with _guard:
        local = _locks.setdefault(key, threading.RLock())
    with local:
        held = getattr(_held, 'paths', set())
        if key in held:
            yield
            return
        with path.open('a+b') as handle:
            if os.name == 'nt':
                import msvcrt
                handle.seek(0)
                if not handle.read(1): handle.write(b'0'); handle.flush()
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
            else:
                import fcntl
                fcntl.flock(handle, fcntl.LOCK_EX)
            _held.paths = held | {key}
            try:
                yield
            finally:
                _held.paths = held
                if os.name == 'nt':
                    handle.seek(0); msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    fcntl.flock(handle, fcntl.LOCK_UN)


# Long-running automatic execution already uses fenced short store transactions.
# Its network/model calls must never acquire an extra command-wide lock.
LOCAL_COMMANDS = {'work', 'submit', 'native-work', 'native-submit', 'source',
    'source-retry', 'native-allocate', 'native-defer', 'native-recover', 'recover',
    'retry', 'ingest', 'close-intake', 'reopen-intake', 'supervise', 'sanity',
    'validate', 'calibration-review', 'calibration-report', 'audit', 'deliver',
    'export', 'pause', 'resume', 'human-decision', 'search-hold', 'search-release',
    'discovery-init', 'native-list', 'host-check'}


@contextmanager
def command_scope(run, command):
    if command in LOCAL_COMMANDS:
        with lock(run):
            yield
    else:
        yield


@contextmanager
def publisher_session(run):
    path = Path(run) / 'intake' / 'publication-session.lock'
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a+b') as handle:
        try:
            if os.name == 'nt':
                import msvcrt
                handle.seek(0); handle.write(b'0'); handle.flush(); handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as error:
            raise ValueError('A managed publisher already owns this run; inspect that session') from error
        try:
            yield
        finally:
            if os.name == 'nt':
                handle.seek(0); msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle, fcntl.LOCK_UN)
