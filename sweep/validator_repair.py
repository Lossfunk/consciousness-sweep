"""Narrow, read-only evidence for an explicitly requested validator repair.

This is not an option to ignore failed checks. The predecessor must have only
the recognized false failure, and the replacement must fully validate the same
quiet snapshot before the ordinary backed-up continuation may proceed.
"""
from contextlib import contextmanager
import json
from pathlib import Path
import sqlite3

from .common import digest

REPAIR = "parked-metadata-generation-v1"
OLD_REASON = "Current parked acquisition belongs to a stale source generation"


def readonly_coordinator(run, *, database=None):
    """Inspection-only view: no constructor, migrations, fencing or disk writes.

    SQLite mode=ro protects the main database while full validation may create
    disposable TEMP audit tables. An explicit standalone backup uses immutable=1.
    """
    from .coordinator import Coordinator
    from .store import Store
    c = Coordinator.__new__(Coordinator)
    c.run_dir = Path(run).resolve()
    c.store = Store.__new__(Store)
    c.store.run_dir = c.run_dir
    c.store.path = Path(database).resolve() if database else c.run_dir / "state.sqlite3"

    @contextmanager
    def connection():
        uri = c.store.path.as_uri() + "?mode=ro" + ("&immutable=1" if database else "")
        conn = sqlite3.connect(uri, uri=True, isolation_level=None)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    @contextmanager
    def no_writes():
        raise ValueError("Read-only validator inspection cannot mutate a run")
        yield

    c.store._connection, c.store._transaction = connection, no_writes
    c.plan = c.store.plan()
    return c


def inspect(run, kind, predecessor_report, snapshot):
    if kind != REPAIR:
        raise ValueError("Unknown validator repair")
    from . import execution_policy, validation, sanity
    c = readonly_coordinator(run)
    report = json.loads((c.run_dir / "delivery/validation.json").read_text())
    if (report.get("ok") is not False or report.get("incomplete") or report.get("scope") != predecessor_report.get("scope")
            or report.get("snapshot_event_id") != predecessor_report.get("snapshot_event_id")
            or report.get("error_count") != predecessor_report.get("error_count")
            or report.get("validation_event_id") != predecessor_report.get("validation_event_id")
            or not report.get("errors") or report['error_count'] != len(report['errors'])
            or any(e.get('code') != 'paper_binding' or e.get('reason') != OLD_REASON for e in report['errors'])):
        raise ValueError("Predecessor validation contains unsupported or unbound failures")
    affected = []
    with c.store._connection() as conn:
        conn.execute("BEGIN")
        for error in report['errors']:
            row = conn.execute("SELECT record FROM papers WHERE id=?", (error['entity'],)).fetchone()
            paper = json.loads(row[0]) if row else {}
            job = conn.execute("SELECT * FROM jobs WHERE id=?", (paper.get('retrieval_job'),)).fetchone()
            proof_row = conn.execute("SELECT payload FROM events WHERE kind='retrieval_parked' "
                "AND json_extract(payload,'$.job_id')=? ORDER BY id DESC LIMIT 1", (paper.get('retrieval_job'),)).fetchone()
            if not job or not proof_row or paper.get('retrieval_revision_pending'):
                raise ValueError("Known parked-metadata failure is not reproducible")
            proof = json.loads(proof_row[0])
            execution_policy.parked_receipt(conn, job, proof, paper)
            events = execution_policy.parked_metadata_revision(conn, paper, json.loads(job['payload']), proof)
            affected.append({'paper_id': paper['paper_id'], 'job_id': job['id'], 'metadata_event_ids': events})
    checked = validation.validate(c, persist=False)
    if not checked['ok'] or checked['snapshot_event_id'] != snapshot:
        raise ValueError("Replacement full validation failed or snapshot changed: " + str(checked['errors']))
    light = sanity.check(c, persist=False)
    if not light['ok'] or light['snapshot_event_id'] != snapshot:
        raise ValueError("Replacement sanity failed or snapshot changed: " + str(light['errors']))
    return {'repair': kind, 'affected': affected, 'snapshot_event_id': snapshot,
        'predecessor_report_sha256': digest(report), 'predecessor_validation_event_id': report['validation_event_id'],
        'target_validation': {'ok': True, 'checks': checked['checks'], 'persisted': False},
        'target_sanity': {'ok': True, 'persisted': False},
        'scope': 'Validator correction only; no scientific or operational record is rewritten'}
