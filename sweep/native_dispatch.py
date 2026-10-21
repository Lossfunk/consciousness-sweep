"""Operational dispatch blocks retain obligations; none are scientific decisions."""
import json

from .common import digest

PREFIX = 'native-dispatch-hold:'


def binding(c, task):
    from .discovery import _native_binding
    pid = task.get('paper_id') or task.get('parent', {}).get('paper_id')
    paper = c.store.paper(pid) if pid else {}
    return digest({'task': _native_binding(c, task),
        'parent_source': {key: (paper or {}).get(key) for key in
            ('source_generation', 'packet_source_generation', 'packet_path')},
        'resolution_generation': c.store.get_state('source-resolution-generation:' + task['task_id'], 0)})


def annotate(c, tasks):
    """Pure derived readiness, including historical queued source resolutions."""
    if not tasks:
        return tasks
    with c.store._connection() as conn:
        holds = {row[0][len('state:' + PREFIX):]: json.loads(row[1]) for row in conn.execute(
            "SELECT key,value FROM meta WHERE key LIKE 'state:native-dispatch-hold:%'")}
        pending = [dict(row) for row in conn.execute(
            "SELECT id,payload FROM jobs j WHERE stage='search' AND NOT EXISTS(SELECT 1 FROM job_supersessions s WHERE s.job_id=j.id) AND (state IN ('pending','running') OR (state='complete' AND projected=0))")]
    source_jobs, citation_jobs = {}, {}
    for row in pending:
        payload = json.loads(row['payload'])
        source_jobs[digest(payload)] = row['id']
        if payload.get('obligation_id'):
            key = (payload['obligation_id'], payload.get('source'), payload.get('cursor'), payload.get('coverage_generation', 0))
            citation_jobs[key] = row['id']
    for task in tasks:
        job = None
        if task['task_id'].startswith('citation-source:'):
            key = (task['obligation_id'], task.get('source'), task.get('cursor'), task.get('coverage_generation', 0))
            job = citation_jobs.get(key)
        elif task['task_id'].startswith('source:'):
            job = source_jobs.get(digest(task['request']))
        if job:
            task['dispatch_block'] = {'code': 'source-resolution-job-pending', 'job_id': job,
                'reason': 'An existing source job must execute/project its recorded request before another resolution dispatch.'}
        held = holds.get(task['task_id'])
        if held and held.get('active') and held['binding'] == binding(c, task):
            task['dispatch_block'] = {'code': 'awaiting-changed-evidence', 'reason': held['reason']}
    from .index_limit import annotate as annotate_index_limit
    return annotate_index_limit(c, tasks)
