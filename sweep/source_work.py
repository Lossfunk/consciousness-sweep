"""Source execution controls shared by dispatch, the runner and supervision."""
import json
import os
import socket
import sys
import time
from .common import digest
from .transactions import atomic_operation

PREFIX = 'source-work-hold:'


def job_filter(alias='j'):
    # A locator/abstract rediscovery can create a new metadata generation. It
    # does not release a source quarantine. An explicit retry or supplied-file
    # change does; its generation transition has an append-first source event.
    return (" AND NOT EXISTS(SELECT 1 FROM meta sw JOIN jobs held "
            "ON held.id=substr(sw.key," + str(len('state:'+PREFIX)+1) + ") WHERE " + alias + ".stage='retrieval'"
            " AND sw.key GLOB 'state:" + PREFIX + "*'"
            " AND json_extract(sw.value,'$.active')=1 AND (held.id=" + alias + ".id OR ("
            "json_extract(held.payload,'$.paper_id')=json_extract(" + alias + ".payload,'$.paper_id')"
            " AND json_extract(held.payload,'$.source_generation')<=json_extract(" + alias + ".payload,'$.source_generation')"
            " AND NOT EXISTS(SELECT 1 FROM events e WHERE e.kind IN ('paper_updated','paper_metadata_enriched')"
            " AND json_extract(e.payload,'$.paper_id')=json_extract(held.payload,'$.paper_id')"
            " AND json_extract(e.payload,'$.changes.source_generation')>json_extract(held.payload,'$.source_generation')"
            " AND json_extract(e.payload,'$.changes.source_generation')<=json_extract(" + alias + ".payload,'$.source_generation')"
            " AND (e.kind='paper_updated' OR EXISTS(SELECT 1 FROM json_each(e.payload,'$.changes.metadata_changed_fields') f"
            " WHERE f.value IN ('provided_paths','fulltext_path','pdf_path','local_path')))))))")


def held_paper(c, pid):
    # Use the exact dispatch predicate against the current paper generation so
    # acquisition helpers and automatic retrieval cannot disagree about a hold.
    with c.store._connection() as conn:
        row = conn.execute("SELECT record FROM papers WHERE id=?", (pid,)).fetchone()
        if not row:
            return False
        paper = json.loads(row[0])
        payload = json.dumps({'paper_id':pid,'source_generation':paper.get('source_generation',1)})
        return conn.execute("SELECT 1 FROM (SELECT '' id,'retrieval' stage,? payload) j WHERE 1=1" +
                            job_filter(), (payload,)).fetchone() is None


@atomic_operation
def change(c, job_ids, actor, reason, *, release=False, evidence=None):
    if not actor.strip() or not reason.strip() or not job_ids or (release and not str(evidence or '').strip()):
        raise ValueError('Source hold/release requires exact jobs, actor, reason and release evidence')
    values = []
    for jid in dict.fromkeys(job_ids):
        job = c.store.job(jid)
        if not job or job['stage'] != 'retrieval':
            raise ValueError('Source holds require existing immutable retrieval jobs')
        key = PREFIX + jid
        old = c.store.get_state(key)
        if release and (not old or not old['active']):
            raise ValueError('Source hold is absent or already released')
        value = {'job_id':jid, 'paper_id':job['payload']['paper_id'],
                 'payload_sha256':digest(job['payload']), 'active':not release,
                 'actor':actor, 'reason':reason, 'evidence':evidence, 'at':time.time()}
        c.store.set_state(key, value, reason)
        values.append(value)
    return values


def validate(conn):
    for row in conn.execute("SELECT key,value FROM meta WHERE key LIKE 'state:" + PREFIX + "%'"):
        value = json.loads(row['value']); jid = value['job_id']
        job = conn.execute('SELECT stage,payload FROM jobs WHERE id=?',(jid,)).fetchone()
        if (row['key'] != 'state:'+PREFIX+jid or not job or job['stage'] != 'retrieval'
                or value['payload_sha256'] != digest(json.loads(job['payload']))
                or value['paper_id'] != json.loads(job['payload'])['paper_id']
                or type(value['active']) is not bool or not value['actor'] or not value['reason']
                or (not value['active'] and not value.get('evidence'))):
            raise ValueError('Source hold differs from its immutable job binding')
        event = conn.execute("SELECT payload FROM events WHERE kind='control_updated' "
            "AND json_extract(payload,'$.key')=? ORDER BY id DESC LIMIT 1",(PREFIX+jid,)).fetchone()
        if not event or json.loads(event[0])['value'] != value:
            raise ValueError('Source hold differs from its append-first history')


def snapshot(c, now=None):
    now = time.time() if now is None else now
    with c.store._connection() as conn:
        predicate,args = c.store.claimable_sql(conn,['retrieval'],now=now)
        row = conn.execute('SELECT count(*) n,min(j.created_at) oldest,sum(CASE WHEN '+
            c.store.local_retrieval_sql()+' THEN 1 ELSE 0 END) supplied FROM jobs j WHERE '+predicate,args).fetchone()
        local = conn.execute('SELECT min(j.created_at) FROM jobs j WHERE '+predicate+' AND '+c.store.local_retrieval_sql(),args).fetchone()[0]
        last_row = conn.execute("SELECT at FROM events WHERE kind='retrieval_attempt_finished' ORDER BY id DESC LIMIT 1").fetchone()
        last = last_row[0] if last_row else None
        held = conn.execute("SELECT count(*) FROM jobs j WHERE NOT (1=1" + job_filter() +
            ") AND NOT EXISTS (SELECT 1 FROM job_supersessions s WHERE s.job_id=j.id)").fetchone()[0]
    return {'eligible_retrievals':row['n'], 'eligible_supplied_documents':row['supplied'] or 0,
            'oldest_ready_seconds':max(0,now-row['oldest']) if row['oldest'] else 0,
            'oldest_supplied_seconds':max(0,now-local) if local else 0,
            'last_retrieval_completion_at':last, 'held_source_jobs':held,
            'runner_observation':c.store.get_state('source-runner'),
            'attention_required':bool(local and now-local>=60),
            'instruction':'Run one managed source-run alongside acquisition helpers; supplied documents need not wait for helper leases.'}


def run(c, *, mode='all', max_seconds=None, watch=True, progress=None):
    from .coordination import source_session
    if mode not in {'all','supplied'}:
        raise ValueError('Source mode must be all or supplied')
    with source_session(c.run_dir):
        c.store.set_state('source-runner',{'mode':mode,'state':'running','pid':os.getpid(),
            'host':socket.gethostname(),'at':time.time()},'One managed source runner; helper leases are independent')
        previous_mode = getattr(c, 'source_mode', 'all')
        try:
            c.run(max_seconds=max_seconds,watch=watch,automatic_models=False,
                  defer_checkpoint=True,source_mode=mode,progress=progress,_source_session=True)
        finally:
            c.source_mode = previous_mode
            primary = sys.exc_info()[1]
            try:
                c.store.set_state('source-runner',{'mode':mode,'state':'exited','pid':os.getpid(),
                    'host':socket.gethostname(),'at':time.time()},'Managed source session ended; leases and receipts remain authoritative')
            except BaseException as cleanup:
                if primary is None:
                    raise
                from .store import _record_cleanup_error
                _record_cleanup_error(primary, cleanup, c.store.path, 'source-runner-observation')

    return c.status()
