"""Completion-first exchange with a durable handoff to the active agent harness.

No subprocess model execution or implicit worker recovery. A lost dispatch reply
is an unacknowledged ticket, never permission to spawn a second reader.
"""
import json
from pathlib import Path
import time
import uuid

from .common import canonical, digest, inside, save_json
from .publication import PublicationLane, Hold, Reconcile, immutable
from .transactions import transaction_view
from .validation import require_integrity


def control(c, mode, actor, reason):
    if mode not in {'OPEN', 'HOLD'} or not actor.strip() or not reason.strip():
        raise ValueError('Publication control requires OPEN/HOLD, actor and reason')
    lane = PublicationLane(c)
    with lane.lock():
        value = {'mode': mode, 'actor': actor, 'reason': reason, 'at': time.time()}
        # Database first: either side being held/mismatched fails closed.
        c.store.set_state('publication-control', value, reason)
        previous = json.loads(lane.gate.read_bytes()) if lane.gate.exists() else {}
        save_json(lane.gate, dict(previous, **value))
        return value


def _tables(conn):
    conn.execute('''CREATE TABLE IF NOT EXISTS dispatch_tickets (
        id TEXT PRIMARY KEY, kind TEXT NOT NULL, entity_id TEXT NOT NULL,
        owner TEXT NOT NULL, token INTEGER NOT NULL, task_sha256 TEXT NOT NULL,
        state TEXT NOT NULL, worker_context_id TEXT, created_at REAL NOT NULL,
        updated_at REAL NOT NULL)''')
    conn.execute('CREATE INDEX IF NOT EXISTS dispatch_state ON dispatch_tickets(state)')
    continued = conn.execute("SELECT value FROM meta WHERE key='state:runtime_continuation'").fetchone()
    if continued:
        expected = json.loads(continued[0])['target_runtime']['sha256']
        if len(expected) != 64 or any(ch not in '0123456789abcdef' for ch in expected):
            raise ValueError('Invalid continued runtime fingerprint')
        # This table may be created after continuation installed the other fences.
        for operation in ('INSERT', 'UPDATE', 'DELETE'):
            conn.execute('CREATE TRIGGER IF NOT EXISTS runtime_fence_dispatch_tickets_' + operation +
                ' BEFORE ' + operation + " ON dispatch_tickets BEGIN SELECT CASE WHEN sweep_runtime_sha() != '" +
                expected + "' THEN RAISE(ABORT,'Inactive runtime cannot write this continued run') END; END")


def _lease(c, row):
    if row['kind'] == 'model':
        job = c.store.job(row['entity_id'])
        if job and job['state'] == 'complete' and (job['owner'], job['token']) == (row['owner'], row['token']): return 'settled'
        if job and job['state'] == 'running' and (job['owner'], job['token']) == (row['owner'], row['token']):
            return 'owned'
    else:
        with c.store._connection() as conn:
            current = conn.execute('SELECT * FROM native_task_control WHERE task_id=?', (row['entity_id'],)).fetchone()
        # A cleared native lease alone cannot distinguish completion from defer
        # or recovery. The existing terminal event binds the exact lease; this
        # settles a ticket, never authorizes replay of its scientific answer.
        with c.store._connection() as conn:
            ack = conn.execute("SELECT 1 FROM events WHERE kind='native_task_submission_finished' AND json_extract(payload,'$.task_id')=? AND json_extract(payload,'$.lease.owner')=? AND json_extract(payload,'$.lease.token')=? LIMIT 1", (row['entity_id'], row['owner'], row['token'])).fetchone()
        if ack: return 'settled'
        if current and (current['owner'], current['token']) == (row['owner'], row['token']): return 'owned'
    return 'needs-reconciliation'


def check_worker(c, kind, entity_id, owner, token, context):
    with c.store._connection() as conn:
        if not conn.execute("SELECT 1 FROM sqlite_master WHERE name='dispatch_tickets'").fetchone(): return
        row = conn.execute('SELECT worker_context_id,state FROM dispatch_tickets WHERE kind=? AND entity_id=? AND owner=? AND token=?',
                           (kind, entity_id, owner, token)).fetchone()
    if row and (row['state'] != 'dispatched' or row['worker_context_id'] != context):
        raise Reconcile('Dispatch acknowledgement missing or bound to another worker; reconcile before publication')


class Exchange(PublicationLane):
    def _refresh(self, c):
        with c.store._connection() as conn:
            _tables(conn)
            rows = conn.execute("SELECT * FROM dispatch_tickets WHERE state IN ('offered','dispatched')").fetchall()
            for row in rows:
                state = _lease(c, row)
                if state != 'owned':
                    conn.execute('UPDATE dispatch_tickets SET state=?,updated_at=? WHERE id=?', (state, time.time(), row['id']))
                    c.store._event(conn, 'dispatch_settled', {'ticket_id': row['id'], 'state': state})

    def step(self, slots, fault=None):
        if type(slots) is not int or slots < 0:
            raise ValueError('Supply the observed number of free harness slots, including zero')
        with self.lock():
            publications = self.drain()
            with self.c.store._transaction() as conn:
                c = transaction_view(self.c, conn)
                self._refresh(c)
                unresolved = [dict(r) for r in conn.execute("SELECT id,kind,entity_id,owner,token,state,worker_context_id FROM dispatch_tickets WHERE state IN ('offered','needs-reconciliation') ORDER BY created_at")]
            offered = sum(r['state'] == 'offered' for r in unresolved)
            dispatches, status = [], 'no-free-harness-slot'
            for _ in range(max(0, slots - offered)):
                # Claim and ticket commit together. Prepared source artifacts are
                # immutable; interrupted uncommitted claims leave no active lease.
                identifier = uuid.uuid4().hex
                with self.c.store._transaction() as conn:
                    c = transaction_view(self.c, conn)
                    task = c.next_task(owner='dispatch-' + identifier)
                    status = task['status']
                    if status not in {'agent-task', 'agent-native-task'}:
                        break
                    if status == 'agent-task':
                        prepared = json.loads((Path(task['task_dir']) / 'task.json').read_bytes())
                        kind, entity = 'model', task['job_id']
                        owner, token = prepared['owner'], prepared['token']
                    else:
                        prepared = task['native_task']
                        kind, entity = 'native', prepared['task_id']
                        owner, token = prepared['native_lease']['owner'], prepared['native_lease']['token']
                    path = self.root / 'intake' / 'dispatch-v1' / identifier / 'task.json'
                    immutable(path, (canonical(task) + '\n').encode())
                    now = time.time()
                    conn.execute('INSERT INTO dispatch_tickets VALUES(?,?,?,?,?,?,?,?,?,?)',
                        (identifier, kind, entity, owner, token, digest(task), 'offered', None, now, now))
                    c.store._event(conn, 'dispatch_offered', {'ticket_id': identifier, 'kind': kind,
                        'entity_id': entity, 'owner': owner, 'token': token, 'task_sha256': digest(task),
                        'reason': 'Reserved for one fresh harness worker; awaiting explicit dispatch acknowledgement'})
                    if fault: fault('before-dispatch-commit')
                if fault: fault('after-dispatch-commit')
                dispatches.append({'ticket_id': identifier, 'kind': kind, 'entity_id': entity,
                    'task_path': str(path), 'task': task})
            return {'status': status, 'publications': publications, 'dispatches': dispatches,
                'unacknowledged_or_unresolved': unresolved,
                'instruction': 'Spawn each NEW ticket once in the active harness with its intended profile and fresh source-only context, then dispatch-ack. Inspect existing unacknowledged tickets against actual harness workers; never respawn blindly.'}

    def acknowledge(self, identifier, context, actor, reason):
        if not all(isinstance(v, str) and v.strip() for v in (context, actor, reason)):
            raise ValueError('Dispatch acknowledgement requires observed worker context, actor and reason')
        with self.lock(), self.c.store._transaction() as conn:
            c = transaction_view(self.c, conn)
            _tables(conn)
            row = conn.execute('SELECT * FROM dispatch_tickets WHERE id=?', (identifier,)).fetchone()
            if not row: raise ValueError('Unknown dispatch ticket')
            path = inside(self.root / 'intake' / 'dispatch-v1' / row['id'] / 'task.json', self.root)
            if digest(json.loads(path.read_bytes())) != row['task_sha256']:
                raise Reconcile('Dispatch task changed')
            if row['state'] == 'dispatched' and row['worker_context_id'] == context:
                return {'status': 'dispatched', 'ticket_id': identifier, 'replayed': True}
            if row['state'] != 'offered' or _lease(c, row) != 'owned':
                raise Reconcile('Dispatch lease/state changed; do not spawn or replace a worker')
            conn.execute("UPDATE dispatch_tickets SET state='dispatched',worker_context_id=?,updated_at=? WHERE id=?", (context, time.time(), identifier))
            c.store._event(conn, 'dispatch_acknowledged', {'ticket_id': identifier,
                'worker_context_id': context, 'actor': actor, 'reason': reason, 'provider_verification': 'unknown'})
            return {'status': 'dispatched', 'ticket_id': identifier, 'provider_verification': 'unknown'}


def watch(c, *, poll_seconds=1, max_seconds=None, progress=print):
    from .coordination import publisher_session
    with publisher_session(c.run_dir):
        return _watch(c, poll_seconds=poll_seconds, max_seconds=max_seconds, progress=progress)


def _watch(c, *, poll_seconds, max_seconds, progress):
    if poll_seconds <= 0 or max_seconds is not None and max_seconds <= 0:
        raise ValueError('Positive polling interval and optional managed-session duration required')
    lane, start, count = PublicationLane(c), time.monotonic(), 0
    while max_seconds is None or time.monotonic() - start < max_seconds:
        try:
            records = lane.drain()
        except Hold:
            return {'status': 'writer-held', 'new_publications': count}
        for record in records:
            progress(record)
            new = not record.get('replayed') and record.get('status') in {'published', 'reconciled-existing-completion'}
            count += new
            if new:
                progress({'status': 'refill-needed', 'entity_id': record['entity_id'],
                    'instruction': 'Observe free harness capacity and call exchange immediately; do not wait for the other workers.'})
        if (lane.root / 'STOP').exists() and not lane.owned_work():
            return {'status': 'paused-after-drain', 'new_publications': count}
        time.sleep(poll_seconds)
    return {'status': 'managed-session-ended', 'new_publications': count}
