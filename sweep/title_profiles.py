"""Explicit title-only model changes, bound to monotonic job-ID epochs.

The original plan and all older jobs retain their exact profiles. A quiet,
backed-up continuation may commission future/unstarted title jobs differently.
It cannot switch adapters, billing, source limits or other scientific roles.
"""
import copy
import json
import re
from .profiles import validate_profile


def history(receipt):
    return (receipt or {}).get('title_profile_history', [])


def replacement(before, model, effort):
    after=dict(before,model=model,effort=effort,qualification_status='unqualified')
    after.pop('qualification_record',None)
    return validate_profile(after)


def validate_history(plan, receipt):
    profile, cutoff = plan['profiles']['title'], ''
    for change in history(receipt):
        if set(change) != {'before','after','first_job_id','access_evidence','actor','reason'}:
            raise ValueError('Malformed title profile history')
        after = validate_profile(change['after'])
        if not after.get('effort'):
            raise ValueError('Title profile effort must be explicit')
        if (change['before'] != profile or change['after'] != after
                or after != replacement(profile,after['model'],after['effort'])
                or profile.get('adapter') not in {'manual','codex'}):
            raise ValueError('Title continuation may change only model and effort on the existing harness')
        if not re.fullmatch(r'J[0-9]{12}', change['first_job_id']) or change['first_job_id'] <= cutoff:
            raise ValueError('Title profile job epochs must advance')
        for key in ('access_evidence','actor','reason'):
            if not isinstance(change[key], str) or not change[key].strip():
                raise ValueError('Title profile change requires '+key)
        profile, cutoff = after, change['first_job_id']
    return history(receipt)


def profiles(plan, receipt):
    result=copy.deepcopy(plan['profiles'])
    if history(receipt): result['title']=copy.deepcopy(history(receipt)[-1]['after'])
    return result


def for_job(plan, receipt, job):
    profile=plan['profiles']['title']
    jid=job.get('id')
    if jid is None and not history(receipt): return copy.deepcopy(profile)
    if jid is None:
        raise ValueError('Title execution needs its durable job ID for profile selection')
    for change in history(receipt):
        if jid >= change['first_job_id']: profile=change['after']
    return copy.deepcopy(profile)


def preview(conn, run, plan, prior, request, actor, reason):
    changes=copy.deepcopy(history(prior))
    if request is None: return changes, []
    if not isinstance(request,dict) or set(request) != {'model','effort','access_evidence'}:
        raise ValueError('Title profile request requires model, effort and access_evidence only')
    before=profiles(plan,prior)['title']
    if (before['model'],before['effort']) == (request['model'],request['effort']):
        raise ValueError('Title profile is unchanged; resolve its scoped access block instead')
    after=replacement(before,request['model'],request['effort'])
    row=conn.execute("SELECT next_value FROM counters WHERE kind='job'").fetchone()
    changes.append({'before':before,'after':after,'first_job_id':'J%012d'%(row[0] if row else 1),
        'access_evidence':request['access_evidence'],'actor':actor,'reason':reason})
    validate_history(plan,{'title_profile_history':changes})
    jobs=[]
    for row in conn.execute("SELECT * FROM jobs j WHERE stage='title' AND state='pending' AND NOT EXISTS(SELECT 1 FROM job_supersessions s WHERE s.job_id=j.id) ORDER BY id"):
        jid=row['id']; directory=run/'jobs'/jid/'execution'
        if row['attempts'] or conn.execute("SELECT 1 FROM reservations WHERE job_id=? AND state!='released'",(jid,)).fetchone():
            raise ValueError('Title job has admitted/uncertain accounting; reconcile explicitly before changing profiles: '+jid)
        if conn.execute('SELECT 1 FROM dependencies WHERE dependency_id=?',(jid,)).fetchone():
            raise ValueError('Title job has dependents; reconcile before changing profiles: '+jid)
        receipt_path=directory/'receipt.json'
        block=conn.execute("SELECT value FROM meta WHERE key=?",('state:access-block:job:'+jid,)).fetchone()
        denied=bool(block and json.loads(block[0]).get('admission')=='not-admitted')
        if receipt_path.exists():
            receipt=json.loads(receipt_path.read_text())
            from .common import file_hash
            if (receipt.get('admission')!='not-admitted' or not receipt.get('completed_at')
                    or receipt.get('binding_sha256')!=file_hash(directory/'binding.json')):
                raise ValueError('Title request lacks verified terminal nonadmission: '+jid)
            denied=True
        if (directory/'dispatch.json').exists() and not denied or row['token'] and not denied:
            raise ValueError('Previously leased title task needs explicit nonadmission evidence: '+jid)
        jobs.append(jid)
    return changes,jobs


def replace_pending(conn, run, receipt):
    """Called inside the continuation transaction; all originals remain intact."""
    if not receipt.get('model_profiles_changed'): return
    from types import SimpleNamespace
    from .store import Store
    from .transactions import transaction_view
    store=object.__new__(Store);store.run_dir=run;store.path=run/'state.sqlite3'
    view=transaction_view(SimpleNamespace(store=store),conn)
    # Reserve the epoch boundary even if no title is pending, so a later
    # settings change cannot reuse the same identifier interval.
    boundary=Store._id(conn,'job','J')
    if boundary != receipt['title_profile_history'][-1]['first_job_id']:
        raise ValueError('Title profile boundary changed during continuation')
    for jid in receipt['title_profile_replacements']:
        job=view.store.job(jid)
        deps=[r[0] for r in conn.execute('SELECT dependency_id FROM dependencies WHERE job_id=?',(jid,))]
        successor=view.store.enqueue('title','title-profile:'+receipt['title_profile_history'][-1]['first_job_id']+':'+jid,
            job['payload'],priority=job['priority'],dependencies=deps)
        view.store.supersede_job(jid,successor,'Explicit title model/effort continuation; prior source, prepared files and accounting retained')
