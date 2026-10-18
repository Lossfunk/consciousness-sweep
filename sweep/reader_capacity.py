"""Explicit byte-capacity successors, preserving every original reader request."""
import copy
import hashlib
import json
from .common import digest, file_hash, inside
from .transactions import atomic_operation

KEY = 'reader-input-capacity:'


def effective(base, payload):
    request = payload.get('input_capacity')
    if request is None:
        return base
    if (not isinstance(request,dict) or set(request) not in ({'original_job_id','max_input_bytes','authorization_sha256'}, {'original_job_id','max_input_bytes','authorization_sha256','context_accounting'})
            or type(request['max_input_bytes']) is not int or request['max_input_bytes'] < base['max_input_bytes']
            or request['max_input_bytes']==base['max_input_bytes'] and not request.get('context_accounting')):
        raise ValueError('Malformed explicit reader input capacity')
    from .profiles import validate_profile
    value=dict(base,max_input_bytes=request['max_input_bytes'])
    if request.get('context_accounting'):value['context_accounting']=request['context_accounting']
    return validate_profile(value)


def inspect(c, jid, maximum, actor, reason, access_evidence, context_accounting=None, accounting_evidence=None):
    if not all(isinstance(v,str) and v.strip() for v in (actor,reason,access_evidence)):
        raise ValueError('Capacity requires actor, reason and actual harness/context access evidence')
    if context_accounting is not None or accounting_evidence is not None:
        from .token_counting import METHOD
        if context_accounting != METHOD or not isinstance(accounting_evidence,str) or not accounting_evidence.strip():
            raise ValueError('Explicit context strategy and its operator evidence must be supplied together')
    job=c.store.job(jid)
    if not job or job['stage']!='reader' or job['payload'].get('calibration_review'):
        raise ValueError('Capacity recovery requires an ordinary reader job')
    prior=c.store.get_state(KEY+jid)
    if prior:
        if (prior['max_input_bytes'],prior['actor'],prior['reason'],prior['access_evidence'],prior.get('context_accounting'),prior.get('accounting_evidence')) != (maximum,actor,reason,access_evidence,context_accounting,accounting_evidence):
            raise ValueError('A different capacity successor already exists')
        with c.store._connection() as conn:
            validate(c, conn)
        return prior
    if job['payload'].get('input_capacity'):
        raise ValueError('An existing explicit capacity successor requires separate review before another allowance')
    base=c.profile_for_job(job)
    if (type(maximum) is not int or maximum<base['max_input_bytes'] or maximum==base['max_input_bytes'] and not context_accounting
            or base['adapter'] not in {'manual','codex','claude'}):
        raise ValueError('Capacity must explicitly increase input bytes on the existing harness; API fallback is unsupported')
    paper=c.store.paper(job['payload']['paper_id'])
    if (job['state']!='pending' or job['owner'] is not None or job['attempts']
            or paper.get('assessment') or paper.get('packet_path')!=job['payload'].get('packet_path')
            or paper.get('source_generation',1)!=job['payload'].get('source_generation',1)):
        raise ValueError('Reader must be current, unassessed, pending, unowned and never admitted')
    with c.store._connection() as conn:
        if conn.execute('SELECT 1 FROM reservations WHERE job_id=? AND (admitted=1 OR state!=\'released\')',(jid,)).fetchone():
            raise ValueError('Admitted or uncertain accounting prohibits capacity recovery')
        if conn.execute('SELECT 1 FROM dependencies WHERE dependency_id=?',(jid,)).fetchone():
            raise ValueError('Dependent work requires separate reconciliation')
        if conn.execute('SELECT 1 FROM job_supersessions WHERE job_id=?',(jid,)).fetchone():
            raise ValueError('Source reader is already superseded')
        if conn.execute("SELECT 1 FROM sqlite_master WHERE name='dispatch_tickets'").fetchone():
            if conn.execute("SELECT 1 FROM dispatch_tickets WHERE kind='model' AND entity_id=? AND state IN ('offered','dispatched')",(jid,)).fetchone():
                raise ValueError('Unreconciled worker ticket prohibits capacity recovery')
    block=c.store.get_state('access-block:job:'+jid)
    from .profiles import profile_fingerprint
    if block and block.get('profile_sha256')!=profile_fingerprint(base):
        raise ValueError('Capacity denial profile differs from the current requested profile')
    if not block or not block.get('active') or block.get('failure_category') not in {'source-byte-limit','context-limit'} or block.get('admission')!='not-admitted':
        raise ValueError('Exact active source-byte-limit/nonadmission proof required')
    # Preparation is intentionally absent: preview must not write job artifacts.
    packet_path=inside(c.run_dir/job['payload']['packet_path'],c.run_dir)
    source=json.loads(packet_path.read_bytes())
    from .workflow import prepare_reader
    prompt,schema=prepare_reader(source,job['payload'])
    if digest(source)!=job['payload']['packet_sha256']:
        raise ValueError('Reader packet changed')
    prompt_hash=hashlib.sha256(prompt.encode()).hexdigest()
    if any(block.get(k) is not None and block[k]!=v for k,v in (
        ('prompt_sha256',prompt_hash),('schema_sha256',digest(schema)),('source_sha256',digest(source)))):
        raise ValueError('Capacity block differs from its current request')
    directory=c.run_dir/'jobs'/jid/'execution';receipt=directory/'receipt.json'
    if receipt.exists():
        saved=json.loads(receipt.read_bytes())
        binding=json.loads((directory/'binding.json').read_bytes())
        if (binding.get('profile') != base or binding.get('prompt_sha256') != prompt_hash
                or binding.get('schema_sha256') != file_hash(directory/'schema.json')
                or file_hash(directory/'prompt.txt') != prompt_hash
                or digest(json.loads((directory/'schema.json').read_bytes())) != digest(schema)):
            raise ValueError('Original nonadmission binding differs from this source/profile request')
        if (saved.get('admission')!='not-admitted' or not saved.get('completed_at')
                or saved.get('binding_sha256')!=file_hash(directory/'binding.json')):
            raise ValueError('Original receipt does not prove terminal nonadmission')
    elif (directory/'dispatch.json').exists():
        raise ValueError('Dispatch without terminal nonadmission receipt')
    from .adapters import request_capacity
    from .profiles import validate_profile
    effective_profile=dict(base,max_input_bytes=maximum)
    if context_accounting:effective_profile['context_accounting']=context_accounting
    effective_profile=validate_profile(effective_profile)
    capacity=request_capacity(effective_profile,prompt,schema)
    if capacity['reason']:
        raise ValueError('Requested allowance still fails capacity: '+capacity['reason'])
    proof={'original_job_id':jid,'paper_id':paper['paper_id'],'original_payload_sha256':digest(job['payload']),
            'original_result':job['result'],'original_profile':base,'effective_profile':effective_profile,
            'max_input_bytes':maximum,'prompt_sha256':prompt_hash,'schema_sha256':digest(schema),
            'source_sha256':digest(source),'packet_sha256':job['payload']['packet_sha256'],
            'original_profile_sha256':profile_fingerprint(base),
            'effective_profile_sha256':profile_fingerprint(effective_profile),
            'actor':actor,'reason':reason,'access_evidence':access_evidence,
            'provider_capacity_verified':False,'scope':'input-byte-allowance-only',
            'model_effort_billing_output_and_total_allowance_unchanged':True}
    if context_accounting:
        proof.update(context_accounting=context_accounting,accounting_evidence=accounting_evidence,
            context_measurement=capacity['context_measurement'],scope='input-bytes-and-explicit-local-context-estimate')
    return proof


@atomic_operation
def grant(c, jid, maximum, actor, reason, access_evidence, *, apply=False, context_accounting=None, accounting_evidence=None):
    from .validation import require_integrity
    require_integrity(c)
    proof=inspect(c,jid,maximum,actor,reason,access_evidence,context_accounting,accounting_evidence)
    if not apply or proof.get('successor_job_id'):
        return dict(proof,status='already-applied' if proof.get('successor_job_id') else 'preview')
    job=c.store.job(jid);payload=copy.deepcopy(job['payload'])
    payload['input_capacity']={'original_job_id':jid,'max_input_bytes':maximum,'authorization_sha256':digest(proof)}
    if context_accounting:payload['input_capacity']['context_accounting']=context_accounting
    new=c.store.enqueue('reader','input-capacity:'+jid+':'+digest(proof),payload,priority=job['priority'])
    proof=dict(proof,successor_job_id=new)
    c.store.set_state(KEY+jid,proof,'Explicit reader input allowance; original job, source, block and accounting retained')
    c.store.supersede_job(jid,new,'Explicit input capacity successor; no original reading or charge is replaced')
    return dict(proof,status='applied')


def validate(c, conn):
    from .profiles import profile_fingerprint
    for row in conn.execute("SELECT key,value FROM meta WHERE key LIKE 'state:"+KEY+"%'"):
        proof=json.loads(row['value']);old=c.store.job(proof['original_job_id']);new=c.store.job(proof['successor_job_id'])
        unsigned={k:v for k,v in proof.items() if k!='successor_job_id'}
        expected=dict(old['payload'],input_capacity={'original_job_id':old['id'],
            'max_input_bytes':proof['max_input_bytes'],'authorization_sha256':digest(unsigned)})
        if proof.get('context_accounting'):expected['input_capacity']['context_accounting']=proof['context_accounting']
        if (row['key']!='state:'+KEY+old['id'] or new['payload']!=expected
                or proof['original_payload_sha256']!=digest(old['payload'])
                or proof['original_result']!=old['result']
                or proof['original_profile']!=c.profile_for_job(old)
                or proof['original_profile_sha256']!=profile_fingerprint(proof['original_profile'])
                or proof['effective_profile_sha256']!=profile_fingerprint(proof['effective_profile'])
                or effective(proof['original_profile'],new['payload'])!=proof['effective_profile']):
            raise ValueError('Reader capacity successor differs from its recorded authorization')
        event=conn.execute("SELECT payload FROM events WHERE kind='control_updated' AND json_extract(payload,'$.key')=? ORDER BY id DESC LIMIT 1",(KEY+old['id'],)).fetchone()
        link=conn.execute('SELECT replacement_job_id FROM job_supersessions WHERE job_id=?',(old['id'],)).fetchone()
        if not event or json.loads(event[0])['value']!=proof or not link or link[0]!=new['id']:
            raise ValueError('Reader capacity history or supersession differs')
    for row in conn.execute("SELECT id,payload FROM jobs WHERE stage='reader' AND json_type(payload,'$.input_capacity')='object'"):
        request=json.loads(row['payload'])['input_capacity']
        saved=conn.execute('SELECT value FROM meta WHERE key=?',('state:'+KEY+request['original_job_id'],)).fetchone()
        if not saved or not _authorized_job(c,c.store.job(row['id']),json.loads(saved[0]),conn):
            raise ValueError('Reader capacity payload has no exact authorization')


def _authorized_job(c,job,proof,conn):
    """A capacity authorization also covers proved same-payload adapter rebinds."""
    anchor=proof['successor_job_id'];current=job['id'];seen=set()
    while current!=anchor:
        if current in seen:return False
        seen.add(current)
        parents=conn.execute('SELECT * FROM job_supersessions WHERE replacement_job_id=?',(current,)).fetchall()
        if len(parents)!=1:return False
        row=parents[0]
        from .continuation import valid_runtime_successor,runtime_rebound_event
        event=runtime_rebound_event(conn,row['job_id'],current)
        if not event or not valid_runtime_successor(c,conn,row,job['payload'],event,expected_profile=proof['effective_profile']):
            return False
        current=row['job_id']
    return True


def profile(c,job,base):
    request=job['payload'].get('input_capacity')
    if request is None:return base
    proof=c.store.get_state(KEY+request.get('original_job_id',''))
    with c.store._connection() as conn:
        if not proof or not _authorized_job(c,job,proof,conn):
            raise ValueError('Reader input capacity has no recorded authorization')
    unsigned={k:v for k,v in proof.items() if k!='successor_job_id'}
    if request.get('authorization_sha256')!=digest(unsigned) or proof['original_profile']!=base:
        raise ValueError('Reader input capacity authorization changed')
    return effective(base,job['payload'])


def successor(c,jid):
    seen=set()
    while True:
        if jid in seen:raise ValueError('Reader capacity successor cycle')
        seen.add(jid);proof=c.store.get_state(KEY+jid)
        if not proof:return jid
        jid=proof['successor_job_id']


def job_filter(alias='j'):
    # Changing a request's byte allowance cannot bypass access restrictions on
    # either the original harness profile or the effective successor settings.
    return (" AND NOT EXISTS(SELECT 1 FROM meta capacity WHERE capacity.key='state:" + KEY + "' || "
            "json_extract(" + alias + ".payload,'$.input_capacity.original_job_id') AND EXISTS("
            "SELECT 1 FROM meta blocked WHERE blocked.key IN ("
            "'state:access-block:profile:'||json_extract(capacity.value,'$.original_profile_sha256'),"
            "'state:access-block:profile:'||json_extract(capacity.value,'$.effective_profile_sha256'))"
            " AND json_extract(blocked.value,'$.active')=1))")


def profile_block_keys(c, job):
    request=job['payload'].get('input_capacity')
    if not request:
        return ()
    proof=c.store.get_state(KEY+request['original_job_id'])
    with c.store._connection() as conn:
        if not proof or not _authorized_job(c,job,proof,conn):
            raise ValueError('Reader capacity has no bound access-control inheritance')
    return tuple('access-block:profile:'+proof[name] for name in
                 ('original_profile_sha256','effective_profile_sha256'))
