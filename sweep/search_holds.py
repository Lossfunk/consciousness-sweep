"""Audited operational holds on exact frozen query windows, never exclusions.

Admission and hold publication serialize on the run's existing write lock. A
hold cannot cancel an owned worker or conceal a completed, unprojected result.
The scientific frontier, job history, source requests and charges stay intact.
"""
import json
import time

from .common import canonical, digest

PREFIX = "state:search-window-hold:"
EVENT = "search_window_hold_changed"


def job_filter(alias="j"):
    return (" AND NOT EXISTS (SELECT 1 FROM meta sh WHERE " + alias + ".stage='search'"
            " AND sh.key='" + PREFIX + "'||json_extract(" + alias + ".payload,'$.window_key')"
            " AND json_extract(sh.value,'$.active')=1)")


def records(conn, *, active_only=True):
    result = []
    for row in conn.execute(
        "SELECT key,value FROM meta WHERE key GLOB ?" +
        (" AND json_extract(value,'$.active')=1" if active_only else "") + " ORDER BY key",
        (PREFIX + "*",)):
        value = json.loads(row['value'])
        if row['key'] != PREFIX + value['window_key']:
            raise ValueError("Search window hold key differs from its recorded identity")
        result.append(value)
    return result


def active_keys(coordinator):
    with coordinator.store._connection() as conn:
        return {r["window_key"] for r in records(conn)}


def require_unheld(coordinator, request):
    key = request.get("window_key")
    if key and key in active_keys(coordinator):
        raise ValueError("Search window is held; explicit search-release with resolution evidence is required: " + key)


def _window(conn, key):
    # Read only the requested window, not the entire potentially large frontier.
    if not isinstance(key, str) or not key:
        raise ValueError("Missing query window key")
    row = conn.execute("SELECT coalesce(json_extract(value,?),json_extract(value,?)) FROM meta "
        "WHERE key='state:discovery_frontiers'", ('$.process_windows.' + json.dumps(key),
        '$.blind_windows.' + json.dumps(key))).fetchone()
    window = json.loads(row[0]) if row and row[0] else None
    if not window or window.get("window_key") != key:
        raise ValueError("Unknown frozen query window: " + str(key))
    return window


def _identity(window):
    return {k: window.get(k) for k in ("window_key", "source", "query", "kind", "phase", "limit",
        "cursor", "source_parameters", "family", "normalized_y_label", "trigger_comparison_id", "lexical_provenance")}


def change(coordinator, keys, *, actor, reason, release=False, evidence=None):
    if not isinstance(actor, str) or not actor.strip() or not isinstance(reason, str) or not reason.strip():
        raise ValueError("Search holds require actor and reason")
    if not keys or any(not isinstance(k, str) or not k.strip() for k in keys) or len(set(keys)) != len(keys):
        raise ValueError("Provide distinct exact window keys")
    if release and (not isinstance(evidence, str) or not evidence.strip()):
        raise ValueError("Search release requires resolution evidence")
    store = coordinator.store
    changed = []
    with store._transaction() as conn:
        store._require_initialized(conn)
        for key in keys:
            window = _window(conn, key)
            row = conn.execute("SELECT value FROM meta WHERE key=?", (PREFIX + key,)).fetchone()
            previous = json.loads(row[0]) if row else None
            if previous:
                validate_record(conn, previous)
            identity = _identity(window)
            if release:
                if not previous or not previous["active"]:
                    raise ValueError("Window has no active hold: " + key)
            else:
                if window["status"] == "complete":
                    raise ValueError("A completed window cannot be held: " + key)
                if previous and previous["active"]:
                    raise ValueError("Window already held; retain or explicitly release its existing hold: " + key)
                jobs = conn.execute("SELECT id,state,projected FROM jobs WHERE stage='search' "
                    "AND json_extract(payload,'$.window_key')=?", (key,)).fetchall()
                if any(j["state"] == "running" or (j["state"] == "complete" and not j["projected"]) for j in jobs):
                    raise ValueError("Reconcile owned workers and unprojected results before holding this window: " + key)
                if conn.execute("SELECT 1 FROM sqlite_master WHERE name='native_task_control'").fetchone():
                    for job in jobs:
                        if conn.execute("SELECT 1 FROM native_task_control WHERE task_id=? AND owner IS NOT NULL",
                                        ("source:" + job["id"],)).fetchone():
                            raise ValueError("Reconcile the owned native source worker before holding this window: " + key)
            value = {"window_key": key, "identity": identity, "identity_sha256": digest(identity),
                     "active": not release, "actor": actor, "reason": reason, "evidence": evidence if release else None,
                     "at": time.time(), "previous_event_id": previous["event_id"] if previous else None}
            event_id = store._event(conn, EVENT, value)
            value["event_id"] = event_id
            conn.execute("INSERT OR REPLACE INTO meta(key,value) VALUES(?,?)", (PREFIX + key, canonical(value)))
            changed.append(value)
    return {"ok": True, "windows": changed, "scientific_completion": False}


def validate_record(conn, record):
    def require(condition, why):
        if not condition:
            raise ValueError("Search window hold: " + why)
    require(isinstance(record, dict), "record is not an object")
    key = record.get("window_key")
    window = _window(conn, key)
    require(record.get("identity") == _identity(window) and record.get("identity_sha256") == digest(_identity(window)),
            "frozen window identity changed")
    require(type(record.get("active")) is bool, "active must be boolean")
    require(all(isinstance(record.get(k), str) and record[k].strip() for k in ("actor", "reason")), "actor/reason missing")
    require(record["active"] or isinstance(record.get("evidence"), str) and record["evidence"].strip(), "release evidence missing")
    event = conn.execute("SELECT kind,payload FROM events WHERE id=?", (record.get("event_id"),)).fetchone()
    require(event and event["kind"] == EVENT and json.loads(event["payload"]) == {k: v for k, v in record.items() if k != "event_id"},
            "current state lacks its exact append-first event")
    if record["active"]:
        require(window["status"] != "complete", "held window was marked complete")
        require(not conn.execute("SELECT 1 FROM jobs WHERE stage='search' AND json_extract(payload,'$.window_key')=? "
            "AND (state='running' OR (state='complete' AND projected=0)) LIMIT 1", (key,)).fetchone(), "held request was dispatched")


def validate(conn, *, history=False):
    values = records(conn, active_only=False)
    for record in values:
        validate_record(conn, record)
    if history:
        latest = {}
        for row in conn.execute("SELECT id,payload FROM events WHERE kind=? ORDER BY id", (EVENT,)):
            value = json.loads(row["payload"])
            key = value["window_key"]
            old = latest.get(key)
            if (value["previous_event_id"] != (old["event_id"] if old else None)
                    or value["active"] == (old["active"] if old else False)):
                raise ValueError("Search window hold history is not an alternating append-first chain")
            latest[key] = dict(value, event_id=row["id"])
        if latest != {value["window_key"]: value for value in values}:
            raise ValueError("Search window hold history differs from current state")
    return len(values)
