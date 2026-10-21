"""Optional operational discovery threshold; no scientific stopping claim.

Count durable paper rows, never encounters, source versions or reserved IDs.
Owned requests and their complete responses survive the boundary. Unstarted
searches stay pending; ordinary work on already indexed papers still drains.
"""
import json
import re
import time

from .common import canonical

KEY = 'state:indexed-paper-limit'
READY = 'state:index-limit-saved-search:'


def history(receipt):
    return (receipt or {}).get('indexed_paper_history', [])


def positive(value):
    return type(value) is int and value > 0


def validate_history(plan, receipt, previous=None):
    changes, before = history(receipt), plan.get('resources', {}).get('max_indexed_papers')
    prior = history(previous)
    if (not isinstance(changes, list) or changes[:len(prior)] != prior
            or len(changes) not in {len(prior), len(prior) + 1}):
        raise ValueError('Indexed-paper agreement history changed during continuation')
    seen = set()
    for change in changes:
        if not isinstance(change, dict) or set(change) != {
                'agreement_id', 'mode', 'requested', 'previous_limit', 'indexed_papers', 'limit', 'actor', 'reason'}:
            raise ValueError('Malformed indexed-paper agreement history')
        key = change['agreement_id']
        if not isinstance(key, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,127}', key) or key in seen:
            raise ValueError('Indexed-paper agreement ID must be unique and filesystem-safe')
        seen.add(key)
        count, request = change['indexed_papers'], change['requested']
        if type(count) is not int or count < 0 or change['previous_limit'] != before:
            raise ValueError('Indexed-paper agreement has an invalid count or predecessor')
        if change['mode'] == 'additional':
            if not positive(before) or not positive(request):
                raise ValueError('An additional indexed-paper allowance requires positive counts and a previous finite limit')
            expected = max(count, before) + request
        elif change['mode'] == 'total' and (request is None or positive(request)):
            expected = request
        else:
            raise ValueError('Indexed-paper allowance must be a positive integer or an explicit unbounded total')
        if change['limit'] != expected or (expected is not None and not positive(change['limit'])):
            raise ValueError('Indexed-paper agreement total differs from the authorized allowance')
        for field in ('actor', 'reason'):
            if not isinstance(change[field], str) or not change[field].strip():
                raise ValueError('Indexed-paper agreement requires ' + field)
        before = expected
    if len(changes) > len(prior) and any(changes[-1][k] != receipt[k] for k in ('actor', 'reason')):
        raise ValueError('Indexed-paper authorization differs from its continuation')
    return changes


def preview(conn, plan, prior, total, additional, agreement_id, actor, reason):
    changes = list(history(prior))
    if total is ... and additional is None:
        if agreement_id is not None:
            raise ValueError('An indexed-paper agreement ID requires an explicit total or additional allowance')
        return changes
    if total is not ... and additional is not None:
        raise ValueError('Choose a total or an additional indexed-paper allowance, not both')
    before = changes[-1]['limit'] if changes else plan.get('resources', {}).get('max_indexed_papers')
    if any(change['agreement_id'] == agreement_id for change in changes):
        raise ValueError('Indexed-paper agreement ID was already applied; inspect its receipt, do not grant it again')
    count = conn.execute('SELECT count(*) FROM papers').fetchone()[0]
    if additional is not None and (not positive(before) or not positive(additional)):
        raise ValueError('An additional indexed-paper allowance requires positive counts and a previous finite limit')
    limit = max(count, before) + additional if additional is not None else total
    if limit == before:
        raise ValueError('Indexed-paper limit is unchanged; ordinary resume preserves the agreement')
    changes.append({'agreement_id': agreement_id, 'mode': 'additional' if additional is not None else 'total',
        'requested': additional if additional is not None else total, 'previous_limit': before,
        'indexed_papers': count, 'limit': limit, 'actor': actor.strip(), 'reason': reason.strip()})
    validate_history(plan, {'indexed_paper_history': changes, 'actor': actor.strip(), 'reason': reason.strip()}, prior)
    return changes


def agreement_id(conn):
    row = conn.execute("SELECT json_extract(value,'$.indexed_paper_history[#-1].agreement_id') FROM meta WHERE key='state:runtime_continuation'").fetchone()
    return row[0] if row else None


def configured(conn):
    row = conn.execute("SELECT json_extract(value,'$.indexed_paper_history[#-1].limit') FROM meta "
        "WHERE key='state:runtime_continuation' AND coalesce(json_array_length(value,'$.indexed_paper_history'),0)>0").fetchone()
    if row:
        return row[0]
    row = conn.execute("SELECT json_extract(value,'$.resources.max_indexed_papers') FROM meta WHERE key='plan'").fetchone()
    return row[0] if row else None


def reached(conn):
    limit = configured(conn)
    return limit is not None and conn.execute('SELECT count(*) FROM papers').fetchone()[0] >= limit


def record_boundary(conn, store):
    """Called inside the paper insert's transaction; one append-first receipt."""
    limit = configured(conn)
    if limit is None:
        return
    scope = agreement_id(conn)
    row = conn.execute('SELECT value FROM meta WHERE key=?', (KEY,)).fetchone()
    if row and json.loads(row[0]).get('agreement_id') == scope:
        return
    count = conn.execute('SELECT count(*) FROM papers').fetchone()[0]
    if count < limit:
        return
    value = {'limit': limit, 'indexed_papers': count, 'at': time.time(),
             'reason': 'User-selected indexed-paper threshold reached; finish admitted responses and drain existing paper work; no saturation claim'}
    if scope is not None:
        value['agreement_id'] = scope
    event_id = store._event(conn, 'indexed_paper_limit_reached', value)
    value['event_id'] = event_id
    conn.execute('INSERT OR REPLACE INTO meta VALUES(?,?)', (KEY, canonical(value)))


def job_filter(conn, alias='j'):
    if not reached(conn):
        return ''
    # A source-only worker can return an already retrieved reference snapshot
    # after the threshold. Permit its verified local projection, not a new hunt.
    return (" AND (" + alias + ".stage!='search' OR EXISTS(SELECT 1 FROM meta il "
            "WHERE il.key='" + READY + "'||" + alias + ".id))")


def save_ready(c, job_id, snapshot_path, snapshot_sha256):
    """An admitted native source answer has complete, immutable local bytes."""
    with c.store._connection() as conn:
        finite = configured(conn) is not None
    if finite:
        c.store.set_state('index-limit-saved-search:' + job_id,
            {'job_id': job_id, 'snapshot_path': snapshot_path, 'snapshot_sha256': snapshot_sha256},
            'Previously admitted source worker returned a complete local snapshot; no further source request is authorized')


def saved_searches(conn, run):
    """Carry complete predecessor responses, including unprojected native lists."""
    from .sources import load_snapshot
    from .common import file_hash
    result = []
    for row in conn.execute("SELECT id,payload FROM jobs WHERE stage='search' AND state='pending' ORDER BY id"):
        path = run / 'searches' / (row['id'] + '.json')
        if not path.exists():
            continue
        snapshot = load_snapshot(path)
        payload = json.loads(row['payload'])
        request = {k: payload.get(k) for k in ('source', 'query', 'limit', 'cursor', 'kind', 'parent')}
        if request['source'] != 'publisher-or-repository-reference-list':
            request['query'], request['limit'] = request['query'] or '', request['limit'] or 100
        request['publication_cutoff'] = None
        if snapshot['request'] != request:
            raise ValueError('Saved predecessor response does not match its exact queued search')
        result.append({'job_id': row['id'], 'snapshot_path': str(path.relative_to(run)),
                       'snapshot_sha256': file_hash(path)})
    return result


def carry_saved_searches(conn, run, saved, store):
    from .common import file_hash
    for value in saved:
        if file_hash(run / value['snapshot_path']) != value['snapshot_sha256']:
            raise ValueError('Saved predecessor search changed during continuation')
        key = READY + value['job_id']
        row = conn.execute('SELECT value FROM meta WHERE key=?', (key,)).fetchone()
        if row and json.loads(row[0]) != value:
            raise ValueError('Saved predecessor search binding differs from its existing receipt')
        if not row:
            store._event(conn, 'control_updated', {'key': key[len('state:'):], 'previous': None, 'value': value,
                'reason': 'Continuation preserves a complete already-retrieved predecessor response for local projection only'})
            conn.execute('INSERT INTO meta VALUES(?,?)', (key, canonical(value)))


def require_saved_response(c, job_id):
    from .common import file_hash
    value = c.store.get_state('index-limit-saved-search:' + job_id)
    if value:
        path = c.run_dir / 'searches' / (job_id + '.json')
        if (value.get('job_id') != job_id or value.get('snapshot_path') != str(path.relative_to(c.run_dir))
                or not path.is_file() or file_hash(path) != value.get('snapshot_sha256')):
            raise ValueError('Admitted local search snapshot is missing or changed; no new network request is authorized')


def validate(c, conn):
    row = conn.execute('SELECT value FROM meta WHERE key=?', (KEY,)).fetchone()
    if row:
        value = json.loads(row[0])
        event = conn.execute("SELECT payload FROM events WHERE id=? AND kind='indexed_paper_limit_reached'", (value.get('event_id'),)).fetchone()
        original = {k: v for k, v in value.items() if k != 'event_id'}
        plan = json.loads(conn.execute("SELECT value FROM meta WHERE key='plan'").fetchone()[0])
        continued = conn.execute("SELECT value FROM meta WHERE key='state:runtime_continuation'").fetchone()
        scopes = {None: plan.get('resources', {}).get('max_indexed_papers')}
        scopes.update({v['agreement_id']: v['limit'] for v in history(json.loads(continued[0]) if continued else None)})
        if (value.get('agreement_id') not in scopes or value.get('limit') != scopes[value.get('agreement_id')]
                or not positive(value.get('limit')) or value.get('indexed_papers', 0) < value['limit']
                or value['indexed_papers'] > conn.execute('SELECT count(*) FROM papers').fetchone()[0]
                or not event or json.loads(event[0]) != original):
            raise ValueError('Indexed-paper threshold receipt differs from the agreement or append-first history')
    if reached(conn) and (not row or value.get('agreement_id') != agreement_id(conn)):
        raise ValueError('Reached indexed-paper threshold lacks its durable receipt')
    for row in conn.execute("SELECT key FROM meta WHERE key GLOB ?", (READY + '*',)):
        require_saved_response(c, row[0][len(READY):])


def discovery_task(task):
    return task.get('task_id', '').startswith(('source:', 'citation-source:')) or task.get('task_id') == 'wave-audit'


def annotate(c, tasks):
    with c.store._connection() as conn:
        if not reached(conn):
            return tasks
        has_controls = conn.execute("SELECT 1 FROM sqlite_master WHERE name='native_task_control'").fetchone()
        owned = {r[0] for r in conn.execute('SELECT task_id FROM native_task_control WHERE owner IS NOT NULL')} if has_controls else set()
    for task in tasks:
        if discovery_task(task) and task['task_id'] not in owned:
            task['dispatch_block'] = {'code': 'indexed-paper-limit',
                'reason': 'User-selected discovery threshold reached; retain this unopened frontier and drain already indexed papers'}
    return tasks


def snapshot(c, pending_native=()):
    """Caller supplies its existing native reconciliation; never recurse into it."""
    with c.store._connection() as conn:
        limit = configured(conn)
        if limit is None:
            return {'max_indexed_papers': None, 'reached': False, 'drained': False}
        count = conn.execute('SELECT count(*) FROM papers').fetchone()[0]
        from .workflow import enabled_conn, job_hold_sql
        held = job_hold_sql() if enabled_conn(conn) else ''
        current = " AND NOT EXISTS(SELECT 1 FROM job_supersessions s WHERE s.job_id=j.id) AND NOT EXISTS(SELECT 1 FROM retry_links r WHERE r.parent_id=j.id)"
        jobs = dict(conn.execute("SELECT state,count(*) FROM jobs j WHERE j.stage!='search' AND j.state IN ('pending','running','failed')" + current + held + ' GROUP BY state').fetchall())
        admitted_searches = conn.execute("SELECT count(*) FROM jobs j WHERE j.stage='search' AND (j.state='running' OR (j.state='complete' AND j.projected=0) OR (j.state='pending' AND EXISTS(SELECT 1 FROM meta il WHERE il.key=?||j.id)))" + current, (READY,)).fetchone()[0]
        unprojected = conn.execute("SELECT count(*) FROM jobs WHERE state='complete' AND projected=0").fetchone()[0]
        table = conn.execute("SELECT 1 FROM sqlite_master WHERE name='native_task_control'").fetchone()
        owned = conn.execute('SELECT count(*) FROM native_task_control WHERE owner IS NOT NULL').fetchone()[0] if table else 0
        native = sum(not discovery_task(t) for t in pending_native)
        # A crash between indexing and enqueueing must not manufacture a drained
        # corpus. Inspect paper state as well as execution queues. Explicit
        # workflow deferrals and source gaps remain separately reported gaps.
        unsettled = dict(conn.execute("SELECT status,count(*) FROM papers WHERE status IN "
            "('discovered','title-pending','abstract-pending','abstract-lookup-pending',"
            "'rescue-pending','retrieval-pending','reader-pending') "
            "AND coalesce(json_extract(record,'$.workflow_defer.active'),0)=0 GROUP BY status").fetchall())
        deferred = conn.execute("SELECT count(*) FROM jobs j WHERE j.stage='search' AND j.state IN ('pending','failed')" + current + " AND NOT EXISTS(SELECT 1 FROM meta il WHERE il.key=?||j.id)", (READY,)).fetchone()[0]
        scope_id = agreement_id(conn)
    hit = count >= limit
    drained = hit and not (sum(jobs.values()) or sum(unsettled.values()) or admitted_searches or unprojected or owned or native)
    return {'max_indexed_papers': limit, 'indexed_papers': count, 'reached': hit,
            'overshoot_papers': max(0, count-limit), 'drained': drained,
            'pending_paper_jobs': jobs.get('pending', 0), 'running_paper_jobs': jobs.get('running', 0),
            'failed_paper_jobs': jobs.get('failed', 0), 'admitted_searches_remaining': admitted_searches,
            'unprojected_results': unprojected, 'owned_native_tasks': owned,
            'pending_paper_native_tasks': native, 'deferred_search_jobs': deferred,
            'unsettled_paper_states': unsettled,
            'counting': 'Durable logical paper rows including seeds, anchors, excluded and deferred papers; rediscoveries and source versions do not add rows',
            'agreement_id': scope_id,
            'scope': 'Finish complete admitted responses and all remaining in-scope paper work. Preserve deferred searches and evidence gaps. User limit is not scientific saturation or native certification.'}
