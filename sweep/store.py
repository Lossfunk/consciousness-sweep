"""Durable operational state for commissioned prospect sweeps (not native records).

Every mutation has a WAL-backed transaction. Scientific reasons and outputs are
opaque JSON here: this store cannot establish scientific eligibility/completion.
Connections are short-lived, making a Store safe to use across worker threads.
Job dependencies are job IDs. Expiration never steals a worker's lease; recovery
requires evidence that its registered local process has exited.
"""
from contextlib import contextmanager
import csv
import hashlib
from itertools import islice
import json
import math
import os
from pathlib import Path
import re
import socket
import sqlite3
import tempfile
import time
import unicodedata
from urllib.parse import unquote


class StoreError(RuntimeError):
    pass


class StaleLease(StoreError):
    pass


class BudgetExceeded(StoreError):
    pass


def _annotate_storage_error(exc, path, phase):
    """Preserve SQLite's original exception/type/code with operational context."""
    if isinstance(exc, sqlite3.Error):
        try:
            if not hasattr(exc, "sweep_storage_phase"):
                exc.sweep_storage_phase = phase
            if not hasattr(exc, "sweep_db_path"):
                exc.sweep_db_path = str(Path(path).absolute())
        except (AttributeError, TypeError, OSError, ValueError):
            pass  # An exception implementation may not allow extra attributes.


def _record_cleanup_error(primary, cleanup, path, phase):
    """A cleanup failure is secondary evidence, never a replacement diagnosis."""
    _annotate_storage_error(cleanup, path, phase)
    try:
        details = list(getattr(primary, "sweep_cleanup_errors", []))
        details.append({"phase": phase, "type": type(cleanup).__name__, "reason": str(cleanup),
                        "sqlite_errorcode": getattr(cleanup, "sqlite_errorcode", None),
                        "sqlite_errorname": getattr(cleanup, "sqlite_errorname", None)})
        primary.sweep_cleanup_errors = details
    except (AttributeError, TypeError):
        pass


def _close_connection(conn, path, primary):
    try:
        conn.close()
    except BaseException as exc:
        if primary is None:
            _annotate_storage_error(exc, path, "connection-close")
            raise
        _record_cleanup_error(primary, exc, path, "connection-close")


def _json(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True,
                      separators=(",", ":"), allow_nan=False)


def _state_delta(previous, value, path=()):
    """Lossless structural changes; unchanged frontier branches are not logged."""
    if previous == value:
        return []
    if isinstance(previous, dict) and isinstance(value, dict):
        changes = []
        for key in sorted(previous.keys() | value.keys()):
            here = path + (key,)
            if key not in value:
                changes.append({"op": "remove", "path": list(here), "previous": previous[key]})
            elif key not in previous:
                changes.append({"op": "add", "path": list(here), "value": value[key]})
            else:
                changes.extend(_state_delta(previous[key], value[key], here))
        return changes
    if isinstance(previous, list) and isinstance(value, list) and len(value) >= len(previous) and value[:len(previous)] == previous:
        return [{"op": "append", "path": list(path), "previous_length": len(previous), "values": value[len(previous):]}]
    return [{"op": "replace", "path": list(path), "previous": previous, "value": value}]


def apply_state_delta(previous, changes):
    """Reconstruct an audited control state, refusing inconsistent prior values."""
    value = json.loads(_json(previous))
    for change in changes:
        change = json.loads(_json(change))
        path, operation = change["path"], change["op"]
        parent = value
        for key in path[:-1]:
            parent = parent[key]
        if not path:
            if operation == "append" and isinstance(value, list) and len(value) == change["previous_length"]:
                value.extend(change["values"])
            elif operation == "replace" and value == change["previous"]:
                value = change["value"]
            else:
                raise ValueError("Control delta root does not match previous state")
            continue
        key = path[-1]
        if operation == "add":
            if key in parent:
                raise ValueError("Control delta adds an existing field")
            parent[key] = change["value"]
        elif operation == "remove":
            if parent[key] != change["previous"]:
                raise ValueError("Control delta removes a different prior value")
            del parent[key]
        elif operation == "replace":
            if parent[key] != change["previous"]:
                raise ValueError("Control delta replaces a different prior value")
            parent[key] = change["value"]
        elif operation == "append":
            if not isinstance(parent[key], list) or len(parent[key]) != change["previous_length"]:
                raise ValueError("Control delta appends to a different prior list")
            parent[key].extend(change["values"])
        else:
            raise ValueError("Unknown control delta operation")
    return value


def normalize_doi(value):
    value = unquote(str(value or "")).strip().lower()
    for prefix in ("https://doi.org/", "http://doi.org/", "http://dx.doi.org/",
                   "https://dx.doi.org/", "doi:"):
        if value.startswith(prefix):
            return value[len(prefix):].strip()
    return value


def _normal(value):
    return " ".join(unicodedata.normalize("NFKC", str(value or "")).casefold().split())


def _bibliographic_key(record):
    title = _normal(record.get("title"))
    while title and unicodedata.category(title[0]).startswith("P"):
        title = title[1:].lstrip()
    while title and unicodedata.category(title[-1]).startswith("P"):
        title = title[:-1].rstrip()
    authors = record.get("authors") or record.get("author")
    if isinstance(authors, list):
        authors = [_normal(a.get("name") or a.get("display_name") or _json(a))
                   if isinstance(a, dict) else _normal(a) for a in authors]
    else:
        authors = _normal(authors)
    year = _normal(record.get("year") or record.get("publication_year"))
    if not title or not authors or not year:
        return None  # Incomplete identities are never silently collapsed.
    return hashlib.sha256(_json([title, year, authors]).encode()).hexdigest()


def _amounts(value, default_calls=0):
    value = value or {}
    result = {
        "calls": value.get("calls", default_calls),
        "tokens": value.get("tokens", value.get("total_tokens",
                            value.get("input_tokens", 0) + value.get("output_tokens", 0))),
        "cost_usd": value.get("cost_usd", 0),
    }
    for key, amount in result.items():
        if isinstance(amount, bool) or not isinstance(amount, (int, float)) or not math.isfinite(amount) or amount < 0:
            raise ValueError("Invalid nonnegative budget amount: " + key)
    return result


_SCHEMA = """
CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY,value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS counters(kind TEXT PRIMARY KEY,next_value INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY AUTOINCREMENT,at REAL NOT NULL,
 kind TEXT NOT NULL,payload TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS papers(id TEXT PRIMARY KEY,doi TEXT,biblio TEXT,status TEXT NOT NULL,
 record TEXT NOT NULL,created_at REAL NOT NULL,updated_at REAL NOT NULL);
CREATE UNIQUE INDEX IF NOT EXISTS paper_doi ON papers(doi) WHERE doi IS NOT NULL;
CREATE INDEX IF NOT EXISTS paper_biblio ON papers(biblio);
CREATE INDEX IF NOT EXISTS paper_status ON papers(status,id);
CREATE TABLE IF NOT EXISTS identity_aliases(alias TEXT NOT NULL,paper_id TEXT NOT NULL REFERENCES papers(id),PRIMARY KEY(alias,paper_id));
CREATE TABLE IF NOT EXISTS identity_links(left_id TEXT NOT NULL REFERENCES papers(id),right_id TEXT NOT NULL REFERENCES papers(id),
 relation TEXT NOT NULL,reason TEXT NOT NULL,PRIMARY KEY(left_id,right_id,relation));
CREATE TABLE IF NOT EXISTS encounters(id INTEGER PRIMARY KEY AUTOINCREMENT,
 paper_id TEXT NOT NULL REFERENCES papers(id),at REAL NOT NULL,provenance TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS encounter_paper ON encounters(paper_id,id);
CREATE TABLE IF NOT EXISTS owners(owner TEXT PRIMARY KEY,pid INTEGER NOT NULL,
 host TEXT NOT NULL,registered_at REAL NOT NULL);
CREATE TABLE IF NOT EXISTS jobs(id TEXT PRIMARY KEY,stage TEXT NOT NULL,key TEXT NOT NULL,
 payload TEXT NOT NULL,priority INTEGER NOT NULL,state TEXT NOT NULL,available_at REAL NOT NULL,
 owner TEXT,token INTEGER NOT NULL DEFAULT 0,lease_until REAL,attempts INTEGER NOT NULL DEFAULT 0,
 result TEXT,error TEXT,projected INTEGER NOT NULL DEFAULT 0,created_at REAL NOT NULL,updated_at REAL NOT NULL,UNIQUE(stage,key));
CREATE INDEX IF NOT EXISTS job_ready ON jobs(state,stage,available_at,priority DESC,id);
CREATE INDEX IF NOT EXISTS job_priority ON jobs(state,priority DESC,id,available_at,stage);
CREATE INDEX IF NOT EXISTS job_owner ON jobs(owner,state);
CREATE INDEX IF NOT EXISTS job_projection ON jobs(state,projected,id);
CREATE INDEX IF NOT EXISTS job_source_paper ON jobs(json_extract(payload,'$.paper_id'),stage);
CREATE TABLE IF NOT EXISTS retrieval_service(job_id TEXT PRIMARY KEY REFERENCES jobs(id),
 last_sequence INTEGER NOT NULL,claims INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS retrieval_attempts(id INTEGER PRIMARY KEY AUTOINCREMENT,
 job_id TEXT NOT NULL REFERENCES jobs(id),owner TEXT NOT NULL,token INTEGER NOT NULL,
 number INTEGER NOT NULL,started_at REAL NOT NULL,result TEXT,completed_at REAL,
 UNIQUE(job_id,token),UNIQUE(job_id,number));
CREATE INDEX IF NOT EXISTS retrieval_attempt_job ON retrieval_attempts(job_id,number);
CREATE TABLE IF NOT EXISTS job_supersessions(job_id TEXT PRIMARY KEY REFERENCES jobs(id),
 replacement_job_id TEXT REFERENCES jobs(id),reason TEXT NOT NULL,created_at REAL NOT NULL,
 CHECK(job_id != replacement_job_id));
CREATE TABLE IF NOT EXISTS dependencies(job_id TEXT NOT NULL REFERENCES jobs(id),
 dependency_id TEXT NOT NULL REFERENCES jobs(id),PRIMARY KEY(job_id,dependency_id),
 CHECK(job_id != dependency_id));
CREATE TABLE IF NOT EXISTS retry_links(parent_id TEXT PRIMARY KEY REFERENCES jobs(id),
 child_id TEXT NOT NULL UNIQUE REFERENCES jobs(id),reason TEXT NOT NULL,actor TEXT NOT NULL,
 evidence TEXT NOT NULL,created_at REAL NOT NULL,CHECK(parent_id != child_id));
CREATE TABLE IF NOT EXISTS reservations(id TEXT PRIMARY KEY,job_id TEXT NOT NULL REFERENCES jobs(id),
 attempt_key TEXT NOT NULL,owner TEXT NOT NULL,token INTEGER NOT NULL,estimate TEXT NOT NULL,
 usage TEXT,state TEXT NOT NULL,admitted INTEGER NOT NULL DEFAULT 0,created_at REAL NOT NULL,
 updated_at REAL NOT NULL,UNIQUE(job_id,attempt_key));
CREATE INDEX IF NOT EXISTS reservation_state ON reservations(state);
CREATE INDEX IF NOT EXISTS reservation_job ON reservations(job_id,created_at DESC,id DESC);
CREATE TABLE IF NOT EXISTS budget_totals(id INTEGER PRIMARY KEY CHECK(id=1),
 calls REAL NOT NULL,tokens REAL NOT NULL,cost_usd REAL NOT NULL,unknown_outcomes INTEGER NOT NULL);
INSERT OR IGNORE INTO budget_totals VALUES(1,0,0,0,0);
CREATE TABLE IF NOT EXISTS native_scientific_ids(
 id TEXT PRIMARY KEY,kind TEXT NOT NULL CHECK(kind IN ('experiment','comparison')),
 paper_id TEXT NOT NULL REFERENCES papers(id),experiment_key TEXT NOT NULL,
 comparison_key TEXT NOT NULL,experiment_id TEXT NOT NULL,
 actor TEXT NOT NULL,reason TEXT NOT NULL,created_at REAL NOT NULL,
 UNIQUE(paper_id,experiment_key,comparison_key));
CREATE INDEX IF NOT EXISTS native_ids_paper ON native_scientific_ids(paper_id,kind);
"""


class Store:
    @staticmethod
    def read_plan(run_dir):
        """Inspect a bound run before any schema setup or write connection.

        A rejected runtime/science upgrade must not mutate the old ledger merely
        because its coordinator was opened. Ordinary execution still opens the
        writer only after the caller verifies this immutable origin binding.
        """
        path = Path(run_dir).resolve() / "state.sqlite3"
        if not path.is_file():
            raise StoreError("Run is not initialized")
        conn, primary, phase = None, None, "read-plan-connect"
        try:
            conn = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True, timeout=30)
            phase = "read-plan"
            row = conn.execute("SELECT value FROM meta WHERE key='plan'").fetchone()
            if not row:
                raise StoreError("Run is not initialized")
            return json.loads(row[0])
        except BaseException as exc:
            primary = exc
            _annotate_storage_error(exc, path, phase)
            raise
        finally:
            if conn is not None:
                _close_connection(conn, path, primary)

    def __init__(self, run_dir):
        self.run_dir = Path(run_dir)
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.path = self.run_dir / "state.sqlite3"
        with self._connection() as conn:
            phase = "journal-mode-setup"
            try:
                conn.execute("PRAGMA journal_mode=WAL")
                phase = "schema-setup"
                conn.executescript(_SCHEMA)
            except sqlite3.Error as exc:
                _annotate_storage_error(exc, self.path, phase)
                raise

    @contextmanager
    def _connection(self):
        conn, primary, phase = None, None, "connect"
        try:
            conn = sqlite3.connect(str(self.path), timeout=30, isolation_level=None)
            phase = "connection-setup:row-factory"
            conn.row_factory = sqlite3.Row
            from .continuation import runtime_sha
            phase = "connection-setup:runtime-fence"
            conn.create_function("sweep_runtime_sha", 0, runtime_sha)
            for pragma in ("foreign_keys=ON", "synchronous=FULL", "busy_timeout=30000"):
                phase = "connection-setup:" + pragma
                conn.execute("PRAGMA " + pragma)
            phase = "connection-use"
            yield conn
        except BaseException as exc:
            primary = exc
            _annotate_storage_error(exc, self.path, phase)
            raise
        finally:
            if conn is not None:
                _close_connection(conn, self.path, primary)

    @contextmanager
    def _transaction(self):
        with self._connection() as conn:
            phase = "transaction-begin"
            try:
                conn.execute("BEGIN IMMEDIATE")
                phase = "transaction-body"
                yield conn
                phase = "transaction-commit"
                conn.execute("COMMIT")
            except BaseException as exc:
                _annotate_storage_error(exc, self.path, phase)
                try:
                    # SQLite may already roll back after FULL/IOERR. A second
                    # ROLLBACK would replace that error with "no transaction".
                    if conn.in_transaction:
                        conn.execute("ROLLBACK")
                except BaseException as cleanup:
                    _record_cleanup_error(exc, cleanup, self.path, "transaction-rollback")
                raise

    @staticmethod
    def _event(conn, kind, payload):
        return conn.execute("INSERT INTO events(at,kind,payload) VALUES(?,?,?)",
                            (time.time(), kind, _json(payload))).lastrowid

    @staticmethod
    def _id(conn, kind, prefix):
        conn.execute("INSERT OR IGNORE INTO counters(kind,next_value) VALUES(?,1)", (kind,))
        number = conn.execute("SELECT next_value FROM counters WHERE kind=?", (kind,)).fetchone()[0]
        conn.execute("UPDATE counters SET next_value=next_value+1 WHERE kind=?", (kind,))
        return ("%s%06d" if kind == "paper" else "%s%012d") % (prefix, number)

    @staticmethod
    def _require_initialized(conn):
        if not conn.execute("SELECT 1 FROM meta WHERE key='plan'").fetchone():
            raise StoreError("Initialize this run before adding operational state")

    def initialize(self, plan):
        encoded = _json(plan)
        with self._transaction() as conn:
            if conn.execute("SELECT 1 FROM meta WHERE key='plan'").fetchone():
                raise StoreError("Run already initialized; resume without reinitializing")
            conn.execute("INSERT INTO meta VALUES('plan',?)", (encoded,))
            conn.execute("INSERT INTO meta VALUES('schema_version','1')")
            self._event(conn, "initialized", {"plan": plan, "scope": "commissioned-prospect-operations"})

    def plan(self):
        with self._connection() as conn:
            row = conn.execute("SELECT value FROM meta WHERE key='plan'").fetchone()
            if not row:
                raise StoreError("Run is not initialized")
            return json.loads(row[0])

    def event(self, kind, payload):
        with self._transaction() as conn:
            self._require_initialized(conn)
            return self._event(conn, kind, payload)

    @staticmethod
    def _native_key(value, name):
        if (not isinstance(value, str) or not value.strip() or value != value.strip()
                or len(value) > 500 or any(unicodedata.category(c) == "Cc" for c in value)):
            raise ValueError(name + " must be a nonempty stable key without surrounding whitespace or control characters")
        return value

    @staticmethod
    def _native_next(conn, paper_id, experiment_id=None):
        """Reconcile a counter against durable reservations and accepted own-run rows."""
        scope = "native-comparison:" + experiment_id if experiment_id else "native-experiment:" + paper_id
        pattern = (re.escape(experiment_id) + r"_C([0-9]{2})" if experiment_id
                   else re.escape(paper_id) + r"_E([0-9]{2})")
        greatest = 0
        for row in conn.execute("SELECT id,experiment_id FROM native_scientific_ids WHERE paper_id=?", (paper_id,)):
            for value in row:
                match = re.fullmatch(pattern, value)
                if match:
                    greatest = max(greatest, int(match[1]))
        # An older accepted native record may predate the portable reservation
        # interface. Never reuse its identifiers or silently assign them a key.
        saved = conn.execute("SELECT value FROM meta WHERE key=?", ("state:native-assessment:" + paper_id,)).fetchone()
        if saved:
            assessment = json.loads(saved[0])
            values = []
            for group in assessment.get("groups", []):
                values.extend([group.get("experiment_id"), *group.get("linked_comparison_ids", [])])
            for activation in assessment.get("process_activations", []):
                comparison = activation.get("comparison", {})
                values.extend([comparison.get("experiment_id"), comparison.get("comparison_id")])
            for value in values:
                match = re.fullmatch(pattern, value or "")
                if match:
                    greatest = max(greatest, int(match[1]))
        row = conn.execute("SELECT next_value FROM counters WHERE kind=?", (scope,)).fetchone()
        number = max(greatest + 1, row[0] if row else 1)
        if number > 99:
            raise StoreError("Native identifier scope exhausted at 99; keep the unit unresolved under the frozen schema")
        conn.execute("INSERT OR REPLACE INTO counters(kind,next_value) VALUES(?,?)", (scope, number + 1))
        return number

    def allocate_native_ids(self, paper_id, experiment_key, *, comparison_key=None, actor, reason):
        """Reserve scientific identities; this does not create or certify scientific rows.

        Stable source-defined keys are idempotent across processes and restarts.
        The write lock commits IDs, counters and provenance before returning.
        A comparison key optionally reserves a child of the physical experiment.
        """
        if not isinstance(paper_id, str) or not re.fullmatch(r"P[0-9]{6}", paper_id):
            raise ValueError("Native allocation requires an allocated logical paper ID")
        experiment_key = self._native_key(experiment_key, "experiment_key")
        if comparison_key is not None:
            comparison_key = self._native_key(comparison_key, "comparison_key")
        if not isinstance(actor, str) or not actor.strip() or not isinstance(reason, str) or not reason.strip():
            raise ValueError("Native allocation requires actor and reason")
        with self._transaction() as conn:
            self._require_initialized(conn)
            if not conn.execute("SELECT 1 FROM papers WHERE id=?", (paper_id,)).fetchone():
                raise StoreError("Native allocation requires an existing logical paper")
            def reserve(key, kind, parent=None):
                row = conn.execute("SELECT * FROM native_scientific_ids WHERE paper_id=? AND experiment_key=? AND comparison_key=?",
                                   (paper_id, experiment_key, key)).fetchone()
                if row:
                    if row["kind"] != kind or (parent and row["experiment_id"] != parent):
                        raise StoreError("Native reservation key has an incompatible identity")
                    return row["id"]
                number = self._native_next(conn, paper_id, parent)
                identity = "%s_C%02d" % (parent, number) if parent else "%s_E%02d" % (paper_id, number)
                created_at = time.time()
                self._event(conn, "native_scientific_id_reserved", {"id": identity, "kind": kind,
                    "paper_id": paper_id, "experiment_key": experiment_key, "comparison_key": key or None,
                    "experiment_id": parent or identity, "actor": actor, "reason": reason, "created_at": created_at})
                conn.execute("INSERT INTO native_scientific_ids VALUES(?,?,?,?,?,?,?,?,?)",
                    (identity, kind, paper_id, experiment_key, key, parent or identity, actor, reason, created_at))
                return identity
            experiment_id = reserve("", "experiment")
            comparison_id = reserve(comparison_key, "comparison", experiment_id) if comparison_key is not None else None
            return {"paper_id": paper_id, "experiment_key": experiment_key, "experiment_id": experiment_id,
                    "comparison_key": comparison_key, "comparison_id": comparison_id}

    def require_native_ids(self, paper_id, groups, comparisons=(), *, conn=None):
        """Reject invented/foreign/duplicate submitted IDs without judging evidence."""
        groups, comparisons = list(groups), list(comparisons)
        if conn is None:
            with self._connection() as connection:
                return self.require_native_ids(paper_id, groups, comparisons, conn=connection)
        reservations = {row["id"]: dict(row) for row in conn.execute(
            "SELECT * FROM native_scientific_ids WHERE paper_id=?", (paper_id,))}
        seen_groups, seen_links, seen_comparisons = set(), set(), set()
        for group in groups:
            eid = group.get("experiment_id")
            row = reservations.get(eid)
            if group.get("paper_id") != paper_id or not row or row["kind"] != "experiment":
                raise StoreError("Native group requires its reserved focal-paper experiment ID; use native-allocate")
            if eid in seen_groups:
                raise StoreError("Native physical experiment IDs must be unique")
            seen_groups.add(eid)
            for cid in group.get("linked_comparison_ids", []):
                child = reservations.get(cid)
                if not child or child["kind"] != "comparison" or child["experiment_id"] != eid or cid in seen_links:
                    raise StoreError("Native group links require unique reserved comparisons of that physical experiment")
                seen_links.add(cid)
        for comparison in comparisons:
            cid, eid = comparison.get("comparison_id"), comparison.get("experiment_id")
            row = reservations.get(cid)
            if (comparison.get("paper_id") != paper_id or not row or row["kind"] != "comparison"
                    or row["experiment_id"] != eid or eid not in seen_groups or cid not in seen_links):
                raise StoreError("Native comparison requires its reserved focal-paper ID and physical-group link")
            if cid in seen_comparisons:
                raise StoreError("Native comparison IDs must be unique")
            seen_comparisons.add(cid)

    def native_id_errors(self, conn=None):
        """Check reservation identity, parent/counter consistency and event binding."""
        if conn is None:
            with self._connection() as connection:
                return self.native_id_errors(connection)
        errors, maxima = [], {}
        rows = {row["id"]: dict(row) for row in conn.execute("SELECT * FROM native_scientific_ids")}
        events = {}
        for event in conn.execute("SELECT payload FROM events WHERE kind='native_scientific_id_reserved'"):
            try:
                payload = json.loads(event[0])
                if not isinstance(payload, dict) or not isinstance(payload.get("id"), str):
                    raise ValueError("Invalid native reservation event")
                events.setdefault(payload["id"], []).append(payload)
            except (ValueError, TypeError):
                errors.append("Invalid native reservation event")
        for identity, row in rows.items():
            try:
                pid, eid, kind = row["paper_id"], row["experiment_id"], row["kind"]
                self._native_key(row["experiment_key"], "experiment_key")
                if not conn.execute("SELECT 1 FROM papers WHERE id=?", (pid,)).fetchone():
                    raise ValueError("Native reservation references an unknown paper")
                if kind == "experiment":
                    pattern, scope = re.escape(pid) + r"_E([0-9]{2})", "native-experiment:" + pid
                    if eid != identity or row["comparison_key"] != "":
                        raise ValueError("Native experiment reservation has invalid parent/key")
                elif kind == "comparison":
                    self._native_key(row["comparison_key"], "comparison_key")
                    parent = rows.get(eid, {})
                    if (parent.get("kind") != "experiment" or parent.get("paper_id") != pid
                            or parent.get("experiment_key") != row["experiment_key"]):
                        raise ValueError("Native comparison reservation has incompatible experiment parent")
                    pattern, scope = re.escape(eid) + r"_C([0-9]{2})", "native-comparison:" + eid
                else:
                    raise ValueError("Invalid native reservation kind")
                match = re.fullmatch(pattern, identity)
                if not re.fullmatch(r"P[0-9]{6}", pid) or not match or int(match[1]) == 0:
                    raise ValueError("Invalid native identifier format")
                maxima[scope] = max(maxima.get(scope, 0), int(match[1]))
                if not row["actor"].strip() or not row["reason"].strip():
                    raise ValueError("Native reservation lacks actor/reason")
                expected = {key: row[key] for key in ("id", "kind", "paper_id", "experiment_key", "experiment_id", "actor", "reason", "created_at")}
                expected["comparison_key"] = row["comparison_key"] or None
                if events.get(identity) != [expected]:
                    raise ValueError("Native reservation differs from its unique append-first reservation event")
            except (ValueError, TypeError, AttributeError) as exc:
                errors.append(identity + ": " + str(exc))
        for identity in events.keys() - rows.keys():
            errors.append(identity + ": Native reservation event has no durable registry identity")
        for scope, greatest in maxima.items():
            counter = conn.execute("SELECT next_value FROM counters WHERE kind=?", (scope,)).fetchone()
            if not counter or type(counter[0]) is not int or counter[0] <= greatest:
                errors.append(scope + ": Next native identifier does not exceed all durable IDs")
        return errors

    def get_state(self, key, default=None):
        with self._connection() as conn:
            row = conn.execute("SELECT value FROM meta WHERE key=?", ("state:" + key,)).fetchone()
            return json.loads(row[0]) if row else default

    def set_state(self, key, value, reason):
        return self.mutate_state(key, lambda previous: value, reason)

    def mutate_state(self, key, updater, reason, default=None):
        """Atomic control update. updater must be fast, pure and must not call Store."""
        if not key or not str(reason).strip():
            raise ValueError("A control update requires a key and reason")
        with self._transaction() as conn:
            self._require_initialized(conn)
            row = conn.execute("SELECT value FROM meta WHERE key=?", ("state:" + key,)).fetchone()
            previous = json.loads(row[0]) if row else default
            value = updater(previous)
            encoded = _json(value)
            self._event(conn, "control_updated", {"key": key, "previous": previous, "value": value, "reason": reason})
            conn.execute("INSERT OR REPLACE INTO meta(key,value) VALUES(?,?)", ("state:" + key, encoded))
            return value

    def mutate_state_compact(self, key, updater, reason, *, history_field=None):
        """Atomic current state plus reconstructable append-only change history.

        Large frontier transitions use this opt-in form instead of storing two
        full frontier snapshots in every event. An append-only history field is
        moved to that transition's event and cleared from current state. This
        bounds historical duplication; current state is still read/serialized
        as a whole and therefore costs O(current frontier size) per mutation.
        """
        if not key or not str(reason).strip():
            raise ValueError("A control update requires a key and reason")
        with self._transaction() as conn:
            self._require_initialized(conn)
            row = conn.execute("SELECT value FROM meta WHERE key=?", ("state:" + key,)).fetchone()
            if row is None:
                raise ValueError("Initialize compact control state before updating it")
            previous = json.loads(row[0])
            value = updater(json.loads(row[0]))
            archived = []
            if history_field is not None:
                old_history, new_history = previous.get(history_field, []), value.get(history_field, [])
                if not isinstance(old_history, list) or not isinstance(new_history, list) or new_history[:len(old_history)] != old_history:
                    raise ValueError("Frontier history must be append-only")
                archived = new_history
                value[history_field] = []
            encoded = _json(value)
            changes = _state_delta(previous, value)
            self._event(conn, "control_delta", {"key": key, "changes": changes,
                "previous_sha256": hashlib.sha256(_json(previous).encode()).hexdigest(),
                "value_sha256": hashlib.sha256(encoded.encode()).hexdigest(),
                "history_field": history_field, "history_entries": archived, "reason": reason})
            conn.execute("UPDATE meta SET value=? WHERE key=?", (encoded, "state:" + key))
            return value

    def job_by_key(self, stage, key):
        """One indexed immutable job identity; no growing scheduler-side key list."""
        with self._connection() as conn:
            row = conn.execute("SELECT * FROM jobs WHERE stage=? AND key=?", (stage, key)).fetchone()
            return self._job(row) if row is not None else None

    def add_paper(self, record, provenance):
        """Record every encounter; exact DOI or unambiguous complete bibliography dedups.

        New discovery metadata never silently replaces a previous semantic decision.
        DOI-bearing conflicting works are kept distinct even if their titles match.
        """
        with self._transaction() as conn:
            self._require_initialized(conn)
            return self._add_paper(conn, record, provenance)

    def import_many(self, records, provenance=None):
        """Import at most 1000 records in one all-or-nothing transaction.

        With provenance supplied, records is a list of metadata dicts. Otherwise
        pass (record, provenance) pairs, preserving each encounter independently.
        """
        records = list(islice(iter(records), 1001))
        if not 1 <= len(records) <= 1000:
            raise ValueError("Import batches must contain 1..1000 records")
        with self._transaction() as conn:
            self._require_initialized(conn)
            return [self._add_paper(conn, item, provenance) if provenance is not None
                    else self._add_paper(conn, item[0], item[1]) for item in records]

    def _add_paper(self, conn, record, provenance):
        if not str(record.get("title", "")).strip():
            raise ValueError("Paper requires a title")
        doi, biblio = normalize_doi(record.get("doi")) or None, _bibliographic_key(record)
        existing = None
        if doi:
            existing = conn.execute("SELECT id FROM papers WHERE doi=?", (doi,)).fetchone()
        elif biblio:
            matches = conn.execute("SELECT id FROM papers WHERE biblio=? LIMIT 2", (biblio,)).fetchall()
            if len(matches) == 1:
                existing = matches[0]
                prior = json.loads(conn.execute("SELECT record FROM papers WHERE id=?", (existing[0],)).fetchone()[0])
                if record.get("arxiv_id") and prior.get("arxiv_id") and record["arxiv_id"] != prior["arxiv_id"]:
                    existing = None  # Explicitly different versions await adjudication.
        is_new = existing is None
        paper_id = self._id(conn, "paper", "P") if is_new else existing[0]
        if is_new:
            now = time.time()
            value = dict(record, paper_id=paper_id)
            value.update(metadata_revision=1, source_generation=1)
            if doi:
                value["doi"] = doi
            value.setdefault("status", "discovered")
            self._event(conn, "paper_added", {"paper_id": paper_id, "record": value,
                                             "reason": "New logical work by deterministic identity"})
            conn.execute("INSERT INTO papers VALUES(?,?,?,?,?,?,?)",
                         (paper_id, doi, biblio, value["status"], _json(value), now, now))
        else:
            self._enrich_metadata(conn, paper_id, record, provenance)
        self._identity_links(conn, paper_id, record, doi, biblio)
        self._event(conn, "discovery_encounter", {"paper_id": paper_id, "is_new": is_new,
                                                  "reason": "new identity" if is_new else "matching DOI or complete bibliography",
                                                  "provenance": provenance})
        conn.execute("INSERT INTO encounters(paper_id,at,provenance) VALUES(?,?,?)",
                     (paper_id, time.time(), _json(provenance)))
        return paper_id, is_new

    def _enrich_metadata(self, conn, paper_id, incoming, provenance):
        """Retain source revisions without importing another run's decisions."""
        row = conn.execute("SELECT record FROM papers WHERE id=?", (paper_id,)).fetchone()
        current = json.loads(row[0])
        changes = {}
        acquisition = {"url", "urls", "fulltext_url", "fulltext_urls", "pdf_url", "open_access_url",
                       "provided_paths", "fulltext_path", "pdf_path", "local_path", "pmcid", "pmid", "openalex_id", "epmc_id", "epmc_source", "source_locations"}
        scalar = {"abstract", "authors", "author", "year", "publication_year", "arxiv_id", "journal", "venue", "type",
                  "publication_date", "language", "volume", "issue", "pages", "publication_status", "version", "version_of", "relation"} | acquisition
        lists = {"urls", "fulltext_urls", "provided_paths", "version_relations", "source_locations"}
        for key in scalar | lists:
            value = incoming.get(key)
            if value in (None, "", [], {}):
                continue
            old = current.get(key)
            if key in lists:
                old_values = old if isinstance(old, list) else [old] if old else []
                new_values = value if isinstance(value, list) else [value]
                combined = list(old_values)
                for item in new_values:
                    if item not in combined:
                        combined.append(item)
                if combined != old_values:
                    changes[key] = combined
            elif key == "abstract" and value != old:
                changes[key] = value
            elif old in (None, "", [], {}) and value != old:
                changes[key] = value
        if not changes:
            return
        changed = sorted(changes)
        changes.update(metadata_revision=current.get("metadata_revision", 1) + 1,
                       metadata_changed_fields=changed)
        if "abstract" in changed:
            changes["screening_revision_pending"] = True
        if acquisition.intersection(changed):
            changes.update(source_generation=current.get("source_generation", 1) + 1,
                           retrieval_revision_pending=True)
        self._event(conn, "paper_metadata_enriched", {"paper_id": paper_id, "changes": changes,
                    "previous": {key: current.get(key) for key in changes}, "provenance": provenance,
                    "reason": "Rediscovery supplied new metadata or decision-relevant abstract evidence; existing decisions require explicit reconciliation"})
        current.update(changes)
        conn.execute("UPDATE papers SET record=?,biblio=?,updated_at=? WHERE id=?",
                     (_json(current), _bibliographic_key(current), time.time(), paper_id))

    def _identity_links(self, conn, paper_id, record, doi, biblio):
        """Index exact identifiers and flag related records; never fuzzy-merge."""
        aliases = []
        if doi:
            aliases.append("doi:" + doi)
            aliases.append("version-doi:" + doi)
        def relation_dois(value):
            if isinstance(value, dict):
                for item in value.values():
                    yield from relation_dois(item)
            elif isinstance(value, list):
                for item in value:
                    yield from relation_dois(item)
            elif isinstance(value, str) and re.fullmatch(r"10\.\d{4,9}/\S+", normalize_doi(value)):
                yield normalize_doi(value)
        for target in relation_dois([record.get("version_relations"), record.get("relation"), record.get("version_of")]):
            aliases.append("version-doi:" + target)
        arxiv = re.sub(r"^https?://arxiv\.org/(?:abs|pdf)/", "", str(record.get("arxiv_id") or "")).removesuffix(".pdf")
        if arxiv:
            aliases.append("arxiv:" + re.sub(r"v\d+$", "", arxiv))
        candidates = set()
        if biblio:
            candidates.update(row[0] for row in conn.execute("SELECT id FROM papers WHERE biblio=? AND id!=?", (biblio, paper_id)))
        for alias in aliases:
            candidates.update(row[0] for row in conn.execute("SELECT paper_id FROM identity_aliases WHERE alias=? AND paper_id!=?", (alias, paper_id)))
            conn.execute("INSERT OR IGNORE INTO identity_aliases VALUES(?,?)", (alias, paper_id))
        for candidate in candidates:
            left, right = sorted((paper_id, candidate))
            reason = "Exact bibliography, base arXiv identifier, or source-declared version relationship links these records; retain both until adjudication"
            cursor = conn.execute("INSERT OR IGNORE INTO identity_links VALUES(?,?,?,?)", (left, right, "possible-version-or-duplicate", reason))
            if cursor.rowcount:
                self._event(conn, "possible_duplicate_linked", {"paper_ids": [left, right], "reason": reason})
        relations = record.get("version_relations") or record.get("relation")
        if relations:
            self._event(conn, "version_relationship_observed", {"paper_id": paper_id, "relationships": relations,
                         "reason": "Source-supplied relationship retained as metadata, not proof that versions have identical evidence"})

    def identity_relationships(self, paper_id):
        with self._connection() as conn:
            return [dict(row) for row in conn.execute("SELECT * FROM identity_links WHERE left_id=? OR right_id=? ORDER BY left_id,right_id", (paper_id, paper_id))]

    def paper(self, paper_id):
        with self._connection() as conn:
            row = conn.execute("SELECT record FROM papers WHERE id=?", (paper_id,)).fetchone()
            return json.loads(row[0]) if row else None

    def papers(self, status=None, limit=100, after_id=None):
        if limit < 1 or limit > 10000:
            raise ValueError("Bounded page limit must be 1..10000")
        sql, args = "SELECT record FROM papers WHERE id>?", [after_id or ""]
        if status is not None:
            sql += " AND status=?"
            args.append(status)
        with self._connection() as conn:
            return [json.loads(row[0]) for row in conn.execute(sql + " ORDER BY id LIMIT ?", args + [limit])]

    def update_paper(self, paper_id, changes, reason, actor="coordinator"):
        if not str(reason).strip():
            raise ValueError("A state change requires a reason")
        if set(changes) & {"id", "paper_id", "doi", "title", "authors", "author", "year", "publication_year"}:
            raise ValueError("Identity corrections require an explicit deduplication operation")
        with self._transaction() as conn:
            row = conn.execute("SELECT record FROM papers WHERE id=?", (paper_id,)).fetchone()
            if not row:
                raise KeyError(paper_id)
            value = json.loads(row[0])
            self._event(conn, "paper_updated", {"paper_id": paper_id, "changes": changes,
                                                 "previous": {k: value.get(k) for k in changes},
                                                 "reason": reason, "actor": actor})
            value.update(changes)
            conn.execute("UPDATE papers SET record=?,status=?,updated_at=? WHERE id=?",
                         (_json(value), value["status"], time.time(), paper_id))
            return value

    def enqueue(self, stage, key, payload, priority=0, dependencies=()):
        if not stage or not key:
            raise ValueError("Job stage and stable key are required")
        encoded, deps = _json(payload), sorted(set(dependencies))
        with self._transaction() as conn:
            self._require_initialized(conn)
            old = conn.execute("SELECT * FROM jobs WHERE stage=? AND key=?", (stage, key)).fetchone()
            if old:
                old_deps = [r[0] for r in conn.execute("SELECT dependency_id FROM dependencies WHERE job_id=? ORDER BY dependency_id", (old["id"],))]
                if old["payload"] != encoded or old_deps != deps or old["priority"] != priority:
                    raise StoreError("A job key is already bound to different inputs")
                return old["id"]
            job_id, now = self._id(conn, "job", "J"), time.time()
            conn.execute("INSERT INTO jobs(id,stage,key,payload,priority,state,available_at,created_at,updated_at) VALUES(?,?,?,?,?,'pending',?,?,?)",
                         (job_id, stage, key, encoded, priority, now, now, now))
            conn.executemany("INSERT INTO dependencies VALUES(?,?)", [(job_id, dep) for dep in deps])
            self._event(conn, "job_enqueued", {"job_id": job_id, "stage": stage, "key": key,
                                               "payload_sha256": hashlib.sha256(encoded.encode()).hexdigest(), "dependencies": deps})
            return job_id

    @staticmethod
    def _supersede_job(conn, job_id, replacement_job_id, reason):
        if not str(reason).strip() or job_id == replacement_job_id:
            raise ValueError("Execution supersession requires another input/job and a reason")
        original = conn.execute("SELECT state FROM jobs WHERE id=?", (job_id,)).fetchone()
        if original is None or (replacement_job_id is not None and not conn.execute("SELECT 1 FROM jobs WHERE id=?", (replacement_job_id,)).fetchone()):
            raise ValueError("Unknown superseded or replacement job")
        cursor = conn.execute("INSERT OR IGNORE INTO job_supersessions VALUES(?,?,?,?)",
                              (job_id, replacement_job_id, reason, time.time()))
        if cursor.rowcount:
            Store._event(conn, "job_superseded", {"job_id": job_id, "replacement_job_id": replacement_job_id,
                "previous_state": original[0], "reason": reason,
                "scope": "execution-only; original result, running worker and budget remain unchanged"})
        return bool(cursor.rowcount)

    def supersede_job(self, job_id, replacement_job_id, reason):
        """Retire obsolete inputs from admission, preserving every prior record.

        Running work is not cancelled. A caller abandoning a not-yet-dispatched
        claim must release its own lease through defer; admitted work finishes.
        """
        with self._transaction() as conn:
            return self._supersede_job(conn, job_id, replacement_job_id, reason)

    def supersede_source_jobs(self, paper_id, generation, manifest_sha256, replacement_job_id, reason):
        with self._transaction() as conn:
            current = conn.execute("SELECT record FROM papers WHERE id=?", (paper_id,)).fetchone()
            if current is None or json.loads(current[0]).get("source_generation", 1) != generation:
                raise ValueError("Source supersession must target the current paper generation")
            count = 0
            for row in conn.execute("SELECT id,stage,payload FROM jobs WHERE json_extract(payload,'$.paper_id')=? AND stage IN ('reader','retrieval') AND id!=?", (paper_id, replacement_job_id)).fetchall():
                payload = json.loads(row["payload"])
                stale = payload.get("source_generation", 1) < generation
                stale = stale or (row["stage"] == "retrieval" and payload.get("source_generation", 1) == generation
                                  and payload.get("source_manifest_sha256") != manifest_sha256)
                if stale:
                    count += self._supersede_job(conn, row["id"], replacement_job_id, reason)
            return count

    def retry_failed(self, old_id, reason, actor, evidence):
        """Create one explicitly supervised successor without refunding the past.

        The recovery layer verifies receipt files, exact input/profile hashes and
        transport termination before supplying this proof. Here the atomic
        boundary checks its shape, the failed job and dependency graph. Original
        jobs, receipts, attempts and all charged/unknown reservations are kept.
        """
        if not str(reason).strip() or not str(actor).strip():
            raise ValueError("A supervised retry needs an explicit reason and actor")
        if not isinstance(evidence, dict) or evidence.get("kind") != "terminal-model-receipt":
            raise ValueError("Retry requires a verified terminal model receipt")
        for name in ("receipt_sha256", "binding_sha256", "prompt_sha256", "schema_sha256", "source_sha256", "profile_sha256"):
            if not isinstance(evidence.get(name), str) or not re.fullmatch(r"[0-9a-f]{64}", evidence[name]):
                raise ValueError("Retry receipt proof lacks " + name)
        if (evidence.get("terminal_transport") not in {"local-process-exited", "http-request-returned"}
                or evidence.get("receipt_status") not in {"failed", "deferred", "completed"}
                or evidence.get("admission") not in {"admitted", "unknown"}
                or not isinstance(evidence.get("receipt_path"), str) or not evidence["receipt_path"].strip()
                or not isinstance(evidence.get("completed_at"), str) or not evidence["completed_at"].strip()):
            raise ValueError("Retry proof does not establish a terminal transport outcome")
        with self._transaction() as conn:
            self._require_initialized(conn)
            old = conn.execute("SELECT * FROM jobs WHERE id=?", (old_id,)).fetchone()
            if (old is None or old["state"] != "failed" or old["stage"] not in {"title", "abstract", "rescue", "audit", "reader"}
                    or old["owner"] is not None or old["lease_until"] is not None):
                raise StoreError("Only a failed, unowned model job can be explicitly retried")
            if conn.execute("SELECT 1 FROM dependencies WHERE dependency_id=? LIMIT 1", (old_id,)).fetchone():
                raise StoreError("Retry with outgoing dependents needs explicit graph reconciliation and is unsupported")
            prior = conn.execute("SELECT * FROM retry_links WHERE parent_id=?", (old_id,)).fetchone()
            if prior:
                previous = json.loads(prior["evidence"])
                if any(previous.get(key) != evidence.get(key) for key in ("receipt_sha256", "binding_sha256", "profile_sha256")):
                    raise StoreError("Retry is already bound to different terminal evidence")
                return prior["child_id"]
            dependencies = [row[0] for row in conn.execute("SELECT dependency_id FROM dependencies WHERE job_id=? ORDER BY dependency_id", (old_id,))]
            child, now, key = self._id(conn, "job", "J"), time.time(), "supervised-retry:" + old_id
            conn.execute("INSERT INTO jobs(id,stage,key,payload,priority,state,available_at,created_at,updated_at) VALUES(?,?,?,?,?,'pending',?,?,?)",
                         (child, old["stage"], key, old["payload"], old["priority"], now, now, now))
            conn.executemany("INSERT INTO dependencies VALUES(?,?)", [(child, dep) for dep in dependencies])
            self._event(conn, "job_enqueued", {"job_id": child, "stage": old["stage"], "key": key,
                        "payload_sha256": hashlib.sha256(old["payload"].encode()).hexdigest(), "dependencies": dependencies})
            conn.execute("INSERT INTO retry_links VALUES(?,?,?,?,?,?)", (old_id, child, reason, actor, _json(evidence), now))
            self._event(conn, "job_retry_authorized", {"parent_id": old_id, "child_id": child,
                        "reason": reason, "actor": actor, "evidence": evidence,
                        "budget_policy": "Original charged and unknown reservations retained; new call requires fresh admission"})
            return child

    def retries(self, limit=100, after_parent_id=None):
        """Bounded supervisor/validator retry lineage with immutable proof."""
        if not 1 <= limit <= 1000:
            raise ValueError("Retry page limit must be between 1 and 1000")
        with self._connection() as conn:
            rows = conn.execute("SELECT * FROM retry_links WHERE parent_id>? ORDER BY parent_id LIMIT ?", (after_parent_id or "", limit))
            return [dict(row, evidence=json.loads(row["evidence"])) for row in rows]

    @staticmethod
    def _job(row):
        value = dict(row)
        value["job_id"] = value["id"]
        value["payload"] = json.loads(value["payload"])
        value["result"] = json.loads(value["result"]) if value["result"] is not None else None
        return value

    def register_owner(self, owner, pid=None, host=None):
        """Owner names bind one process lifetime; use a random nonce in each name."""
        with self._transaction() as conn:
            self._register_owner(conn, owner, pid or os.getpid(), host or socket.gethostname())

    @staticmethod
    def _register_owner(conn, owner, pid, host):
        row = conn.execute("SELECT * FROM owners WHERE owner=?", (owner,)).fetchone()
        if row and (row["pid"] != pid or row["host"] != host):
            raise StoreError("Owner name is bound to another process; use a fresh owner ID")
        conn.execute("INSERT OR IGNORE INTO owners VALUES(?,?,?,?)", (owner, pid, host, time.time()))

    @staticmethod
    def local_retrieval_sql(alias="j", *, untried_during_hold=False):
        if alias not in {"j", "jobs"}:
            raise ValueError("Unexpected SQL alias")
        source = "CASE WHEN json_type(" + alias + ".payload,'$.source_manifest')='object' THEN json_extract(" + alias + ".payload,'$.source_manifest') ELSE coalesce((SELECT record FROM papers WHERE id=json_extract(" + alias + ".payload,'$.paper_id'))," + alias + ".payload) END"
        local = "(coalesce(json_array_length(" + source + ",'$.provided_paths'),0)>0 OR " + " OR ".join(
            "nullif(json_extract(" + source + ",'$." + key + "'),'') IS NOT NULL"
            for key in ("fulltext_path", "pdf_path", "local_path")) + ")"
        if untried_during_hold:
            # A failed local copy must not poll its remote fallback throughout a
            # network hold. New source generations are distinct jobs; recovery
            # restores ordinary retry admission without removing obligations.
            local += " AND NOT EXISTS (SELECT 1 FROM retrieval_attempts ra, meta hm WHERE ra.job_id=" + alias + ".id AND hm.key='state:host-access' AND json_type(hm.value,'$.network')='object' AND ra.completed_at>=coalesce(json_extract(hm.value,'$.network.at'),0))"
        return local

    @staticmethod
    def claimable_sql(conn, stages, *, now, calibration_reviews=None, local_retrieval_only=False):
        """Shared pending-work predicate for admission and supervision inspection."""
        placeholders = ",".join("?" for _ in stages)
        review_filter = ""
        args = list(stages) + [now]
        if calibration_reviews is not None:
            if type(calibration_reviews) is not bool:
                raise ValueError("calibration_reviews must be boolean or null")
            review_filter = " AND coalesce(json_extract(j.payload,'$.calibration_review'),0)=?"
            args.append(int(calibration_reviews))
        eligible = "j.state='pending' AND NOT EXISTS (SELECT 1 FROM job_supersessions s WHERE s.job_id=j.id) AND NOT EXISTS (SELECT 1 FROM meta m WHERE m.key='state:access-block:job:'||j.id AND json_extract(m.value,'$.active')=1) AND j.stage IN (" + placeholders + ") AND j.available_at<=?" + review_filter + " AND NOT EXISTS (SELECT 1 FROM dependencies d JOIN jobs p ON p.id=d.dependency_id WHERE d.job_id=j.id AND p.state!='complete')"
        if type(local_retrieval_only) is not bool:
            raise ValueError("local_retrieval_only must be boolean")
        if local_retrieval_only:
            eligible += " AND j.stage='retrieval' AND " + Store.local_retrieval_sql(untried_during_hold=True)
        from .execution_policy import job_filter, load
        eligible += job_filter(conn)
        rounds = load(conn)["retrieval_max_rounds"]
        if rounds is not None:
            eligible += " AND (j.stage!='retrieval' OR (SELECT count(*) FROM retrieval_attempts a WHERE a.job_id=j.id)<" + str(rounds) + ")"
        return eligible, args

    def claim(self, stages, owner, lease_seconds=300, limit=1, calibration_reviews=None, local_retrieval_only=False):
        if not stages or not owner or not 1 <= limit <= 1000 or lease_seconds <= 0:
            raise ValueError("Claim requires stages, owner, bounded limit and positive lease")
        now = time.time()
        with self._transaction() as conn:
            self._require_initialized(conn)
            self._register_owner(conn, owner, os.getpid(), socket.gethostname())
            from .supervision import admission_hold
            if admission_hold(conn, self.run_dir):
                return []
            eligible, args = self.claimable_sql(conn, stages, now=now,
                calibration_reviews=calibration_reviews, local_retrieval_only=local_retrieval_only)
            from .execution_policy import free_slots
            slots = free_slots(conn)
            model_stages = {'title', 'abstract', 'rescue', 'audit', 'reader'}
            if slots is not None and set(stages).issubset(model_stages):
                limit = min(limit, slots)
                if limit == 0:
                    return []
            schedule = None
            if "retrieval" in stages:
                saved = conn.execute("SELECT value FROM meta WHERE key='retrieval_schedule'").fetchone()
                schedule = json.loads(saved[0]) if saved else {"next_lane": 0, "sequence": 0}
                rows = None  # Select one slot at a time inside the same claim transaction.
            else:
                from .execution_policy import load, job_order
                order = job_order(conn) if load(conn)["retained_first"] else "j.priority DESC,j.id"
                rows = conn.execute("SELECT j.* FROM jobs j WHERE " + eligible + " ORDER BY " + order + " LIMIT ?", args + [limit]).fetchall()
            result = []
            for index in range(limit if rows is None else len(rows)):
                if schedule is not None:
                    slot_filter = " AND j.stage NOT IN ('title','abstract','rescue','audit','reader')" if slots == 0 else ""
                    row, lane = self._next_retrieval_service(conn, eligible + slot_filter, args, schedule)
                    if row is None:
                        break
                else:
                    row, lane = rows[index], None
                if row["stage"] in model_stages and slots is not None:
                    if slots == 0:
                        continue
                    slots -= 1
                token = row["token"] + 1
                claim = {"job_id": row["id"], "owner": owner, "token": token}
                if schedule is not None:
                    schedule["sequence"] += 1
                    claim.update(service_lane=lane, service_sequence=schedule["sequence"])
                self._event(conn, "job_claimed", claim)
                conn.execute("UPDATE jobs SET state='running',owner=?,token=?,lease_until=?,updated_at=? WHERE id=?",
                             (owner, token, now + lease_seconds, now, row["id"]))
                if row["stage"] == "retrieval":
                    conn.execute("INSERT INTO retrieval_service VALUES(?,?,1) ON CONFLICT(job_id) DO UPDATE SET last_sequence=excluded.last_sequence,claims=claims+1",
                                 (row["id"], schedule["sequence"]))
                value = self._job(row)
                value.update(state="running", owner=owner, token=token, lease_until=now + lease_seconds)
                result.append(value)
            if schedule is not None and result:
                conn.execute("INSERT INTO meta VALUES('retrieval_schedule',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (_json(schedule),))
            return result

    @staticmethod
    def _next_retrieval_service(conn, eligible, args, schedule):
        """Reserve service for priority, local, fresh, retry and other stages.

        Each nonempty lane receives a slot every five admissions at most. The
        fresh lane is oldest-first across priorities; the retry lane rotates by
        last service. Thus new high-priority work, recurring failures and local
        arrivals cannot monopolize acquisition. Empty lanes are skipped. The
        last slot prevents other requested stages such as discovery from being
        starved by a full acquisition queue; retrieval-only claims skip it.
        This affects execution ordering, never scientific eligibility or caps.
        """
        local = Store.local_retrieval_sql()
        lanes = (
            ("priority", "", "j.priority DESC,coalesce(rs.last_sequence,0),j.id"),
            ("local", " AND j.stage='retrieval' AND " + local, "coalesce(rs.last_sequence,0),j.priority DESC,j.id"),
            ("fresh", " AND j.stage='retrieval' AND coalesce(rs.claims,j.token)=0", "j.id"),
            ("retry", " AND j.stage='retrieval' AND coalesce(rs.claims,j.token)>0", "coalesce(rs.last_sequence,0),j.id"),
            ("other-stage", " AND j.stage!='retrieval'", "j.priority DESC,j.id"),
        )
        for _ in lanes:
            lane, predicate, order = lanes[schedule["next_lane"]]
            schedule["next_lane"] = (schedule["next_lane"] + 1) % len(lanes)
            from .execution_policy import load, job_order
            if load(conn)["retained_first"]:
                order = job_order(conn)
            row = conn.execute("SELECT j.* FROM jobs j LEFT JOIN retrieval_service rs ON rs.job_id=j.id WHERE " + eligible + predicate + " ORDER BY " + order + " LIMIT 1", args).fetchone()
            if row is not None:
                return row, lane
        return None, None

    @staticmethod
    def _owned(conn, job_id, owner, token):
        row = conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
        if not row or row["state"] != "running" or row["owner"] != owner or row["token"] != token:
            raise StaleLease("Worker no longer owns job " + job_id)
        return row

    def heartbeat(self, job_id, owner, token, lease_seconds=300):
        if lease_seconds <= 0:
            raise ValueError("Lease must be positive")
        with self._transaction() as conn:
            self._owned(conn, job_id, owner, token)
            conn.execute("UPDATE jobs SET lease_until=?,updated_at=? WHERE id=?",
                         (time.time() + lease_seconds, time.time(), job_id))

    def admit_retrieval_attempt(self, job_id, owner, token):
        """Count actual acquisition starts, separately from claims/model calls."""
        with self._transaction() as conn:
            job = self._owned(conn, job_id, owner, token)
            if job["stage"] != "retrieval":
                raise StoreError("Retrieval execution accounting requires a retrieval job")
            prior = conn.execute("SELECT number FROM retrieval_attempts WHERE job_id=? AND token=?", (job_id, token)).fetchone()
            if prior:
                return prior[0]
            number = conn.execute("SELECT coalesce(max(number),0)+1 FROM retrieval_attempts WHERE job_id=?", (job_id,)).fetchone()[0]
            payload, now = json.loads(job["payload"]), time.time()
            self._event(conn, "retrieval_attempt_started", {"job_id": job_id, "owner": owner,
                "token": token, "attempt": number, "source_generation": payload.get("source_generation"),
                "source_manifest_sha256": payload.get("source_manifest_sha256")})
            conn.execute("INSERT INTO retrieval_attempts(job_id,owner,token,number,started_at) VALUES(?,?,?,?,?)", (job_id, owner, token, number, now))
            return number

    def retrieval_attempt_count(self, job_id):
        with self._connection() as conn:
            return conn.execute("SELECT count(*) FROM retrieval_attempts WHERE job_id=?", (job_id,)).fetchone()[0]

    def retrieval_attempts(self, job_id, limit=100, after_number=0):
        if not 1 <= limit <= 1000 or after_number < 0:
            raise ValueError("Retrieval history requires a bounded page and nonnegative cursor")
        with self._connection() as conn:
            return [dict(row, result=json.loads(row["result"]) if row["result"] is not None else None)
                    for row in conn.execute("SELECT * FROM retrieval_attempts WHERE job_id=? AND number>? ORDER BY number LIMIT ?", (job_id, after_number, limit))]

    def latest_retrieval_result(self, job_id):
        """Only finished receipts for this exact immutable source-bound job."""
        with self._connection() as conn:
            row = conn.execute("SELECT result FROM retrieval_attempts WHERE job_id=? AND result IS NOT NULL ORDER BY number DESC LIMIT 1", (job_id,)).fetchone()
            return json.loads(row[0]) if row else None

    def finish_retrieval_attempt(self, job_id, owner, token, result, delay_seconds=0):
        """Fence receipt/cache publication and defer/completion in one transaction."""
        if (not isinstance(result, dict) or not result.get("status") or isinstance(delay_seconds, bool)
                or not isinstance(delay_seconds, (int, float)) or not math.isfinite(delay_seconds) or delay_seconds < 0):
            raise ValueError("Retrieval completion needs a result and finite nonnegative delay")
        with self._transaction() as conn:
            job = self._owned(conn, job_id, owner, token)
            attempt = conn.execute("SELECT * FROM retrieval_attempts WHERE job_id=? AND token=?", (job_id, token)).fetchone()
            if job["stage"] != "retrieval" or attempt is None or attempt["result"] is not None:
                raise StoreError("Retrieval completion requires this lease's unfinished admitted attempt")
            payload, now = json.loads(job["payload"]), time.time()
            self._event(conn, "retrieval_attempt_finished", {"job_id": job_id, "owner": owner,
                "token": token, "attempt": attempt["number"], "result": result})
            conn.execute("UPDATE retrieval_attempts SET result=?,completed_at=? WHERE id=?", (_json(result), now, attempt["id"]))
            if result["status"] == "deferred":
                reason = result.get("reason") or "Transient retrieval failure"
                self._event(conn, "retrieval_deferred", {"job_id": job_id,
                    "paper_id": payload.get("paper_id"), "source_manifest_sha256": payload.get("source_manifest_sha256"), "result": result})
                self._event(conn, "job_deferred", {"job_id": job_id, "owner": owner, "token": token,
                    "reason": reason, "delay_seconds": delay_seconds})
                conn.execute("UPDATE jobs SET state='pending',owner=NULL,lease_until=NULL,available_at=?,error=?,updated_at=? WHERE id=?", (now + delay_seconds, reason, now, job_id))
            else:
                self._event(conn, "job_completed", {"job_id": job_id, "owner": owner, "token": token, "result": result})
                conn.execute("UPDATE jobs SET state='complete',result=?,lease_until=NULL,updated_at=? WHERE id=?", (_json(result), now, job_id))

    def complete(self, job_id, owner, token, result):
        with self._transaction() as conn:
            self._owned(conn, job_id, owner, token)
            self._event(conn, "job_completed", {"job_id": job_id, "owner": owner, "token": token,
                                                "result": result})
            conn.execute("UPDATE jobs SET state='complete',result=?,lease_until=NULL,updated_at=? WHERE id=?",
                         (_json(result), time.time(), job_id))

    def complete_agent_submission(self, job_id, owner, token, result, submission, publish):
        """Fence manual publication and its append-first history in one lock.

        The callback may only publish this lease's immutable artifacts. A crash
        before commit can leave those bytes for an identical retry, but a losing
        or recovered worker never gets to replace a committed worker's evidence.
        """
        with self._transaction() as conn:
            self._owned(conn, job_id, owner, token)
            automatic = conn.execute(
                "SELECT 1 FROM reservations WHERE job_id=? AND state!='released' LIMIT 1", (job_id,)).fetchone()
            if automatic:
                raise StoreError("Automatic execution already reserved this job; manual submission cannot replace its receipt")
            publish()
            self._event(conn, "agent_submission", submission)
            self._event(conn, "job_completed", {"job_id": job_id, "owner": owner, "token": token,
                                                "result": result})
            conn.execute("UPDATE jobs SET state='complete',result=?,lease_until=NULL,updated_at=? WHERE id=?",
                         (_json(result), time.time(), job_id))

    def defer(self, job_id, owner, token, reason, delay_seconds=0):
        self._finish_attempt(job_id, owner, token, reason, "pending", delay_seconds)

    def fail(self, job_id, owner, token, reason):
        self._finish_attempt(job_id, owner, token, reason, "failed", 0)

    def _finish_attempt(self, job_id, owner, token, reason, state, delay):
        if not str(reason).strip() or delay < 0:
            raise ValueError("A failure/defer requires a reason and nonnegative delay")
        with self._transaction() as conn:
            self._owned(conn, job_id, owner, token)
            self._event(conn, "job_deferred" if state == "pending" else "job_failed",
                        {"job_id": job_id, "owner": owner, "token": token, "reason": reason, "delay_seconds": delay})
            conn.execute("UPDATE jobs SET state=?,owner=NULL,lease_until=NULL,available_at=?,error=?,updated_at=? WHERE id=?",
                         (state, time.time() + delay, reason, time.time(), job_id))

    def reconcile(self):
        """Report expired leases without stealing them or changing attempt budgets."""
        with self._connection() as conn:
            return [dict(row) for row in conn.execute("SELECT id,owner,token,lease_until FROM jobs WHERE state='running' AND lease_until<? ORDER BY id LIMIT 1000", (time.time(),))]

    def recover_owner(self, owner, reason, proof):
        """Recover only a demonstrably exited registered local process.

        proof={'kind':'process-dead','pid':123,'host':socket.gethostname()}.
        Remote recovery must be handled by its supervisor; elapsed time is not
        proof. Admitted unsettled calls become unknown and continue holding funds.
        """
        if not str(reason).strip() or proof.get("kind") != "process-dead":
            raise StoreError("Recovery requires a reason and process-dead proof")
        with self._transaction() as conn:
            registered = conn.execute("SELECT * FROM owners WHERE owner=?", (owner,)).fetchone()
            if not registered or proof.get("pid") != registered["pid"] or proof.get("host") != registered["host"]:
                raise StoreError("Recovery proof does not match registered owner")
            if registered["host"] != socket.gethostname():
                raise StoreError("Cannot verify a remote process locally")
            try:
                os.kill(registered["pid"], 0)
            except ProcessLookupError:
                pass
            except (PermissionError, OSError) as exc:
                raise StoreError("Cannot prove owner has exited") from exc
            else:
                raise StoreError("Owner process remains live; do not steal its work")
            rows = conn.execute("SELECT id FROM jobs WHERE owner=? AND state='running'", (owner,)).fetchall()
            for row in rows:
                self._event(conn, "owner_recovered", {"job_id": row[0], "owner": owner, "reason": reason, "proof": proof})
                conn.execute("UPDATE jobs SET state='pending',owner=NULL,token=token+1,lease_until=NULL,available_at=?,updated_at=? WHERE id=?",
                             (time.time(), time.time(), row[0]))
            for reservation in conn.execute("SELECT * FROM reservations WHERE owner=? AND state IN ('reserved','admitted')", (owner,)).fetchall():
                if reservation["admitted"]:
                    conn.execute("UPDATE budget_totals SET unknown_outcomes=unknown_outcomes+1 WHERE id=1")
                else:
                    self._budget_delta(conn, json.loads(reservation["estimate"]), -1)
                conn.execute("UPDATE reservations SET state=?,updated_at=? WHERE id=?",
                             ("unknown" if reservation["admitted"] else "released", time.time(), reservation["id"]))
            return [row[0] for row in rows]

    @staticmethod
    def _budget_totals(conn):
        row = conn.execute("SELECT calls,tokens,cost_usd,unknown_outcomes FROM budget_totals WHERE id=1").fetchone()
        return dict(row)

    @staticmethod
    def _budget_delta(conn, amounts, sign=1):
        conn.execute("UPDATE budget_totals SET calls=calls+?,tokens=tokens+?,cost_usd=cost_usd+? WHERE id=1",
                     (sign * amounts["calls"], sign * amounts["tokens"], sign * amounts["cost_usd"]))

    def reserve_budget(self, job_id, owner, token, estimate, attempt_key):
        """Reserve bounded call capacity before invocation, without admitting an attempt.

        Estimates must be conservative upper bounds for enforced monetary caps;
        unavailable provider pricing/usage must not be presented as known zero.
        An unresolved billed outcome stops token/spend-capped dispatch until
        reconciled. Calls-only subscription runs retain its one-call reservation
        and may continue independent work; unknown calls never count as zero.
        """
        amounts = _amounts(estimate, default_calls=1)
        if amounts["calls"] != 1 or not attempt_key:
            raise ValueError("Each reservation represents one actual model call")
        with self._transaction() as conn:
            self._owned(conn, job_id, owner, token)
            previous = conn.execute("SELECT * FROM reservations WHERE job_id=? AND attempt_key=?", (job_id, attempt_key)).fetchone()
            if previous:
                if previous["estimate"] != _json(amounts) or previous["owner"] != owner or previous["token"] != token:
                    raise StoreError("Attempt key already bound to different inputs/owner")
                return previous["id"]
            if conn.execute("SELECT 1 FROM reservations WHERE job_id=? AND state IN ('reserved','admitted','unknown')", (job_id,)).fetchone():
                raise StoreError("This job already has an unresolved reservation")
            plan = json.loads(conn.execute("SELECT value FROM meta WHERE key='plan'").fetchone()[0])
            caps = plan.get("budgets", plan.get("budget", {}))
            totals = self._budget_totals(conn)
            token_cap = caps.get("max_tokens", caps.get("tokens"))
            spend_cap = caps.get("max_cost_usd", caps.get("cost_usd"))
            if totals["unknown_outcomes"] and (token_cap is not None or spend_cap is not None and spend_cap > 0):
                raise BudgetExceeded("Resolve unknown billed outcomes before additional dispatch")
            for name in ("calls", "tokens", "cost_usd"):
                cap = caps.get("max_" + name, caps.get(name))
                measured = name in estimate or name == "calls" or name == "tokens" and ("total_tokens" in estimate or {"input_tokens", "output_tokens"} <= set(estimate))
                if cap is not None and not measured:
                    raise BudgetExceeded("A bounded estimate is required for capped " + name)
                if cap is not None and totals[name] + amounts[name] > cap + 1e-12:
                    raise BudgetExceeded("Run budget would exceed " + name)
            reservation_id, now = self._id(conn, "reservation", "B"), time.time()
            self._event(conn, "budget_reserved", {"reservation_id": reservation_id, "job_id": job_id,
                                                   "attempt_key": attempt_key, "estimate": amounts})
            conn.execute("INSERT INTO reservations(id,job_id,attempt_key,owner,token,estimate,state,created_at,updated_at) VALUES(?,?,?,?,?,?,'reserved',?,?)",
                         (reservation_id, job_id, attempt_key, owner, token, _json(amounts), now, now))
            self._budget_delta(conn, amounts)
            return reservation_id

    def admit_attempt(self, reservation_id, owner, token, max_attempts=None):
        with self._transaction() as conn:
            row = conn.execute("SELECT * FROM reservations WHERE id=?", (reservation_id,)).fetchone()
            if not row or row["owner"] != owner or row["token"] != token:
                raise StaleLease("Reservation owner mismatch")
            job = self._owned(conn, row["job_id"], owner, token)
            if row["state"] == "released":
                raise StoreError("A released reservation cannot be readmitted")
            if row["admitted"]:
                return job["attempts"]
            if row["state"] != "reserved":
                raise StoreError("Reservation is no longer available for admission")
            if max_attempts is not None and job["attempts"] >= max_attempts:
                raise BudgetExceeded("Job has exhausted its lifetime attempt budget")
            self._event(conn, "attempt_admitted", {"reservation_id": reservation_id, "job_id": row["job_id"], "attempt": job["attempts"] + 1})
            conn.execute("UPDATE reservations SET admitted=1,state='admitted',updated_at=? WHERE id=?", (time.time(), reservation_id))
            conn.execute("UPDATE jobs SET attempts=attempts+1,updated_at=? WHERE id=?", (time.time(), row["job_id"]))
            return job["attempts"] + 1

    def settle_budget(self, reservation_id, usage=None, outcome="known", reason="provider receipt"):
        """Settle once; an unknown outcome can later be resolved from a receipt.

        not-started is allowed only before admission. There is deliberately no
        automatic refund for an admitted call lacking a transport response.
        """
        if outcome not in ("known", "unknown", "not-started", "completed-unmetered") or not str(reason).strip():
            raise ValueError("Invalid budget settlement")
        with self._transaction() as conn:
            row = conn.execute("SELECT * FROM reservations WHERE id=?", (reservation_id,)).fetchone()
            if not row:
                raise KeyError(reservation_id)
            if outcome == "not-started" and row["admitted"]:
                raise StoreError("Cannot refund an admitted call without a usage receipt")
            if outcome != "not-started" and not row["admitted"]:
                raise StoreError("Call must be admitted before settlement")
            if outcome == "known" and usage is None:
                raise ValueError("Known outcomes require an explicit usage receipt")
            state = {"known": "settled", "unknown": "unknown", "not-started": "released", "completed-unmetered": "unmetered"}[outcome]
            amounts = _amounts(usage, default_calls=1) if outcome == "known" else None
            if amounts is not None and amounts["calls"] != 1:
                raise ValueError("An admitted model invocation always consumes one call")
            encoded = _json(amounts) if amounts is not None else None
            if row["state"] in ("settled", "released"):
                if row["state"] == state and row["usage"] == encoded:
                    return
                raise StoreError("Settled budget history cannot be silently overwritten")
            if row["state"] == "unmetered" and state == "unknown":
                raise StoreError("Known completion cannot become an unknown execution")
            self._event(conn, "budget_settled", {"reservation_id": reservation_id, "state": state,
                                                  "usage": amounts, "reason": reason})
            if state not in ("unknown", "unmetered"):
                self._budget_delta(conn, json.loads(row["estimate"]), -1)
                if amounts is not None:
                    self._budget_delta(conn, amounts)
            if row["state"] == "unknown":
                conn.execute("UPDATE budget_totals SET unknown_outcomes=unknown_outcomes-1 WHERE id=1")
            if state == "unknown":
                conn.execute("UPDATE budget_totals SET unknown_outcomes=unknown_outcomes+1 WHERE id=1")
            conn.execute("UPDATE reservations SET state=?,usage=?,updated_at=? WHERE id=?",
                         (state, encoded, time.time(), reservation_id))

    def reject_admission(self, reservation_id, reason, proof):
        """Refund only an explicit authenticated endpoint pre-admission denial.

        A CLI failure, timeout or absent response is not proof. Local preflight
        should occur before admit_attempt and use not-started settlement instead.
        Confirmed HTTP 401/403/429 rejects the provisional dispatch count too.
        """
        if (not str(reason).strip() or proof.get("admission") != "not-admitted"
                or proof.get("status") not in ("deferred", "failed")
                or proof.get("http_status") not in (401, 403, 429)
                or not isinstance(proof.get("binding_sha256"), str)
                or len(proof["binding_sha256"]) != 64):
            raise StoreError("Explicit bound HTTP pre-admission rejection receipt required")
        with self._transaction() as conn:
            row = conn.execute("SELECT * FROM reservations WHERE id=?", (reservation_id,)).fetchone()
            if not row:
                raise KeyError(reservation_id)
            if row["state"] == "released":
                return
            if row["state"] not in ("reserved", "admitted", "unknown"):
                raise StoreError("Cannot refund an already completed call")
            self._event(conn, "admission_rejected", {"reservation_id": reservation_id, "job_id": row["job_id"],
                                                       "reason": reason, "proof": proof})
            self._budget_delta(conn, json.loads(row["estimate"]), -1)
            if row["state"] == "unknown":
                conn.execute("UPDATE budget_totals SET unknown_outcomes=unknown_outcomes-1 WHERE id=1")
            if row["admitted"]:
                conn.execute("UPDATE jobs SET attempts=attempts-1,updated_at=? WHERE id=? AND attempts>0", (time.time(), row["job_id"]))
            conn.execute("UPDATE reservations SET state='released',updated_at=? WHERE id=?", (time.time(), reservation_id))

    @staticmethod
    def _reservation(row):
        if row is None:
            return None
        value = dict(row)
        for key in ("estimate", "usage"):
            value[key] = json.loads(value[key]) if value[key] is not None else None
        return value

    def reservation(self, reservation_id):
        with self._connection() as conn:
            return self._reservation(conn.execute("SELECT * FROM reservations WHERE id=?", (reservation_id,)).fetchone())

    def reservation_for_job(self, job_id):
        with self._connection() as conn:
            return self._reservation(conn.execute("SELECT * FROM reservations WHERE job_id=? ORDER BY created_at DESC,id DESC LIMIT 1", (job_id,)).fetchone())

    latest_reservation = reservation_for_job

    def budget(self):
        with self._connection() as conn:
            result = self._budget_totals(conn)
            result["completed_unmetered_calls"] = conn.execute("SELECT count(*) FROM reservations WHERE state='unmetered'").fetchone()[0]
            return result

    def list_jobs(self, stage=None, state=None, limit=100, after_id=None):
        if not 1 <= limit <= 10000:
            raise ValueError("Bounded page limit must be 1..10000")
        sql, args = "SELECT * FROM jobs WHERE id>?", [after_id or ""]
        for name, value in (("stage", stage), ("state", state)):
            if value is not None:
                sql += " AND " + name + "=?"
                args.append(value)
        with self._connection() as conn:
            return [self._job(row) for row in conn.execute(sql + " ORDER BY id LIMIT ?", args + [limit])]

    def job(self, job_id):
        with self._connection() as conn:
            row = conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
            return self._job(row) if row else None

    def unprojected_results(self, limit=100):
        if not 1 <= limit <= 10000:
            raise ValueError("Bounded page limit must be 1..10000")
        with self._connection() as conn:
            return [self._job(row) for row in conn.execute("SELECT * FROM jobs WHERE state='complete' AND projected=0 ORDER BY id LIMIT ?", (limit,))]

    def mark_projected(self, job_id):
        """Acknowledge idempotent downstream state/jobs after durable completion."""
        with self._transaction() as conn:
            row = conn.execute("SELECT state,projected FROM jobs WHERE id=?", (job_id,)).fetchone()
            if not row or row["state"] != "complete":
                raise StoreError("Only completed results can be projected")
            if not row["projected"]:
                self._event(conn, "result_projected", {"job_id": job_id})
                conn.execute("UPDATE jobs SET projected=1,updated_at=? WHERE id=?", (time.time(), job_id))

    def count_jobs(self, stage=None, state=None):
        sql, args = "SELECT count(*) FROM jobs WHERE 1=1", []
        for name, value in (("stage", stage), ("state", state)):
            if value is not None:
                sql += " AND " + name + "=?"
                args.append(value)
        with self._connection() as conn:
            return conn.execute(sql, args).fetchone()[0]

    def result(self, job_id):
        with self._connection() as conn:
            row = conn.execute("SELECT result FROM jobs WHERE id=?", (job_id,)).fetchone()
            return json.loads(row[0]) if row and row[0] is not None else None

    def status(self):
        with self._connection() as conn:
            stages = {}
            for row in conn.execute("SELECT stage,state,count(*) AS n FROM jobs WHERE NOT EXISTS (SELECT 1 FROM retry_links r WHERE r.parent_id=jobs.id) AND (state='running' OR NOT EXISTS (SELECT 1 FROM job_supersessions s WHERE s.job_id=jobs.id)) GROUP BY stage,state"):
                stages.setdefault(row["stage"], {})[row["state"]] = row["n"]
            papers = {r[0]: r[1] for r in conn.execute("SELECT status,count(*) FROM papers GROUP BY status")}
            return {"jobs": stages, "papers": papers,
                    "unfinished": conn.execute("SELECT count(*) FROM jobs WHERE state='running' OR (state='pending' AND NOT EXISTS (SELECT 1 FROM job_supersessions s WHERE s.job_id=jobs.id))").fetchone()[0],
                    "failed": conn.execute("SELECT count(*) FROM jobs WHERE state='failed' AND NOT EXISTS (SELECT 1 FROM retry_links r WHERE r.parent_id=jobs.id) AND NOT EXISTS (SELECT 1 FROM job_supersessions s WHERE s.job_id=jobs.id)").fetchone()[0],
                    "superseded_jobs": conn.execute("SELECT count(*) FROM job_supersessions").fetchone()[0],
                    "historical_failed": conn.execute("SELECT count(*) FROM jobs WHERE state='failed'").fetchone()[0],
                    "retried_failed": conn.execute("SELECT count(*) FROM retry_links").fetchone()[0],
                    "retrieval_execution": {
                        "claims": conn.execute("SELECT coalesce(sum(claims),0) FROM retrieval_service").fetchone()[0],
                        "attempts": conn.execute("SELECT count(*) FROM retrieval_attempts").fetchone()[0],
                        "receipts": conn.execute("SELECT count(*) FROM retrieval_attempts WHERE result IS NOT NULL").fetchone()[0],
                        "without_receipt": conn.execute("SELECT count(*) FROM retrieval_attempts WHERE result IS NULL").fetchone()[0]},
                    "encounters": conn.execute("SELECT count(*) FROM encounters").fetchone()[0],
                    "events": conn.execute("SELECT count(*) FROM events").fetchone()[0],
                    "budget": self._budget_totals(conn), "native_scientific_completion": False}

    def events(self, after_id=0, limit=None):
        """Stream a consistent snapshot; close the generator if stopping early."""
        with self._connection() as conn:
            conn.execute("BEGIN")
            sql, args = "SELECT * FROM events WHERE id>? ORDER BY id", [after_id]
            if limit is not None:
                sql += " LIMIT ?"
                args.append(limit)
            for row in conn.execute(sql, args):
                value = dict(row)
                value["payload"] = json.loads(value["payload"])
                yield value

    def export(self, directory=None):
        """Stream one database snapshot to atomic individual JSONL/CSV files.

        An export manifest is published last. Its file hashes allow readers to
        reject a partially replaced multi-file export after interruption.
        """
        directory = Path(directory or self.run_dir / "exports")
        directory.mkdir(parents=True, exist_ok=True)
        temp_paths, manifest = [], {"files": {}, "scope": "commissioned-prospect-operations"}
        try:
            with self._connection() as conn:
                conn.execute("BEGIN")
                manifest["last_event_id"] = conn.execute("SELECT coalesce(max(id),0) FROM events").fetchone()[0]
                for table in ("papers", "jobs", "encounters", "events", "reservations", "retry_links", "job_supersessions", "native_scientific_ids", "retrieval_service", "retrieval_attempts"):
                    destination = directory / (table + ".jsonl")
                    fd, name = tempfile.mkstemp(prefix="." + table + "-", dir=str(directory))
                    temp_paths.append(name)
                    digest, count = hashlib.sha256(), 0
                    with os.fdopen(fd, "wb") as output:
                        for row in conn.execute("SELECT * FROM " + table + " ORDER BY " + ("parent_id" if table == "retry_links" else "job_id" if table in {"job_supersessions", "retrieval_service"} else "id")):
                            item = dict(row)
                            for key in ("record", "payload", "provenance", "result", "estimate", "usage", "evidence"):
                                if key in item and item[key] is not None:
                                    item[key] = json.loads(item[key])
                            line = (_json(item) + "\n").encode()
                            output.write(line)
                            digest.update(line)
                            count += 1
                        output.flush()
                        os.fsync(output.fileno())
                    os.replace(name, destination)
                    manifest["files"][destination.name] = {"sha256": digest.hexdigest(), "rows": count}
                destination = directory / "papers.csv"
                fd, name = tempfile.mkstemp(prefix=".papers-", dir=str(directory))
                temp_paths.append(name)
                with os.fdopen(fd, "w", newline="", encoding="utf-8") as output:
                    writer = csv.DictWriter(output, fieldnames=["paper_id", "title", "doi", "year", "status", "record_json"])
                    writer.writeheader()
                    for row in conn.execute("SELECT id,record FROM papers ORDER BY id"):
                        record = json.loads(row["record"])
                        writer.writerow({"paper_id": row["id"], "title": record.get("title", ""), "doi": record.get("doi", ""),
                                         "year": record.get("year", record.get("publication_year", "")), "status": record["status"], "record_json": row["record"]})
                    output.flush()
                    os.fsync(output.fileno())
                os.replace(name, destination)
                digest = hashlib.sha256()
                with destination.open("rb") as stream:
                    for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                        digest.update(chunk)
                manifest["files"][destination.name] = {"sha256": digest.hexdigest()}
            fd, name = tempfile.mkstemp(prefix=".manifest-", dir=str(directory))
            temp_paths.append(name)
            with os.fdopen(fd, "w", encoding="utf-8") as output:
                output.write(_json(manifest) + "\n")
                output.flush()
                os.fsync(output.fileno())
            os.replace(name, directory / "manifest.json")
            return manifest
        finally:
            for name in temp_paths:
                if os.path.exists(name):
                    os.unlink(name)
