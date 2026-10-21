"""Optional operational discovery threshold; no scientific stopping claim.

Count durable paper rows, never encounters, source versions or reserved IDs.
Owned requests and their complete responses survive the boundary. Unstarted
searches stay pending; ordinary work on already indexed papers still drains.
"""
import json
import time

from .common import canonical

KEY = 'state:indexed-paper-limit'
READY = 'state:index-limit-saved-search:'


def configured(conn):
    row = conn.execute("SELECT json_extract(value,'$.resources.max_indexed_papers') FROM meta WHERE key='plan'").fetchone()
    return row[0] if row else None


def reached(conn):
    limit = configured(conn)
    return limit is not None and conn.execute('SELECT count(*) FROM papers').fetchone()[0] >= limit


def record_boundary(conn, store):
    """Called inside the paper insert's transaction; one append-first receipt."""
    limit = configured(conn)
    if limit is None or conn.execute('SELECT 1 FROM meta WHERE key=?', (KEY,)).fetchone():
        return
    count = conn.execute('SELECT count(*) FROM papers').fetchone()[0]
    if count < limit:
        return
    value = {'limit': limit, 'indexed_papers': count, 'at': time.time(),
             'reason': 'User-selected indexed-paper threshold reached; finish admitted responses and drain existing paper work; no saturation claim'}
    event_id = store._event(conn, 'indexed_paper_limit_reached', value)
    value['event_id'] = event_id
    conn.execute('INSERT INTO meta VALUES(?,?)', (KEY, canonical(value)))


def job_filter(conn, alias='j'):
    if not reached(conn):
        return ''
    # A source-only worker can return an already retrieved reference snapshot
    # after the threshold. Permit its verified local projection, not a new hunt.
    return (" AND (" + alias + ".stage!='search' OR EXISTS(SELECT 1 FROM meta il "
            "WHERE il.key='" + READY + "'||" + alias + ".id))")


def save_ready(c, job_id, snapshot_path, snapshot_sha256):
    """An admitted native source answer has complete, immutable local bytes."""
    if c.plan.get('resources', {}).get('max_indexed_papers') is not None:
        c.store.set_state('index-limit-saved-search:' + job_id,
            {'job_id': job_id, 'snapshot_path': snapshot_path, 'snapshot_sha256': snapshot_sha256},
            'Previously admitted source worker returned a complete local snapshot; no further source request is authorized')


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
        if (value.get('limit') != configured(conn) or not reached(conn)
                or value.get('indexed_papers', 0) < value['limit']
                or not event or json.loads(event[0]) != original):
            raise ValueError('Indexed-paper threshold receipt differs from the plan or append-first history')
    elif reached(conn):
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
            'scope': 'Finish complete admitted responses and all remaining in-scope paper work. Preserve deferred searches and evidence gaps. User limit is not scientific saturation or native certification.'}
