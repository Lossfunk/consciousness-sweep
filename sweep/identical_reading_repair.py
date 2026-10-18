"""Explicit reconciliation of a proven accidental reread, never adjudication.

Both completed jobs, allocated IDs and charges stay immutable. Only the current
presentation returns to its first reading; the extra reading is separately bound
as an alternative. Conflicting routes or changed sources require separate review.
"""
import copy
import json
import time
from .common import canonical, digest, inside

REPAIR = 'identical-packet-metadata-reread-v1'
BOUND = ('source_generation', 'current_source_generation', 'current_source_manifest_sha256',
         'packet_path', 'packet_source_generation', 'assessment_source_generation',
         'assessment_packet_sha256', 'reader_job', 'retrieval_job', 'assessment', 'retrieval', 'status')
LOCAL = ('provided_paths', 'fulltext_path', 'pdf_path', 'local_path')


def require(ok, reason):
    if not ok:
        raise ValueError('Identical-reading reconciliation refused: ' + reason)


def prove(conn, run, pid):
    """Read one quiet snapshot; recover the original only from its own history."""
    row = conn.execute('SELECT record FROM papers WHERE id=?', (pid,)).fetchone()
    require(row is not None, 'unknown paper')
    current = json.loads(row[0])
    generation = current.get('source_generation')
    require(type(generation) is int and generation > 1 and current.get('status') == 'assessed'
            and not current.get('retrieval_revision_pending') and not current.get('workflow_defer', {}).get('active'),
            'current source work is not a settled complete reading')
    # Recover the state immediately before the automatic acquisition increment.
    previous, metadata, increment, original = None, [], None, None
    for event in conn.execute("SELECT id,kind,payload FROM events WHERE kind IN "
            "('paper_added','paper_updated','paper_metadata_enriched') "
            "AND json_extract(payload,'$.paper_id')=? ORDER BY id", (pid,)):
        value = json.loads(event['payload'])
        if event['kind'] == 'paper_added':
            previous = value['record']; continue
        changes = value.get('changes', {})
        if changes.get('source_generation') == generation:
            require(event['kind'] == 'paper_updated' and set(changes) == {'source_generation'}
                    and value.get('reason') == 'New acquisition locations require a newly bound source attempt'
                    and value.get('previous', {}).get('source_generation') == previous.get('source_generation'),
                    'generation was not advanced by automatic metadata reconciliation')
            original, increment = copy.deepcopy(previous), event['id']
            break
        if event['kind'] == 'paper_metadata_enriched':
            metadata.append(event['id'])
        require(previous is not None, 'paper creation history missing')
        previous.update(changes)
    require(original is not None and original.get('assessment') and original.get('status') == 'assessed'
            and original.get('retrieval_revision_pending') and metadata,
            'no completed original reading before rediscovery')
    base = original['source_generation']
    require(base < generation and not original.get('workflow_defer', {}).get('active'), 'original source is not reusable')

    def job(jid, stage):
        row = conn.execute('SELECT * FROM jobs WHERE id=?', (jid,)).fetchone()
        require(row and row['stage'] == stage and row['state'] == 'complete' and row['projected'],
                'source/reader job is not durably complete and projected')
        return {'id': jid, 'payload': json.loads(row['payload']), 'result': json.loads(row['result'])}
    old = job(original.get('reader_job'), 'reader'); new = job(current.get('reader_job'), 'reader')
    old_source = job(original.get('retrieval_job'), 'retrieval'); new_source = job(current.get('retrieval_job'), 'retrieval')
    packet = old['payload'].get('packet_sha256')
    require(old['id'] != new['id'] and packet and packet == new['payload'].get('packet_sha256')
            and original.get('packet_path') == current.get('packet_path')
            and digest(json.loads(inside(run / original['packet_path'], run).read_bytes())) == packet,
            'reader packets differ or changed on disk')
    for paper, reader, source, gen in [(original,old,old_source,base),(current,new,new_source,generation)]:
        require(reader['payload'].get('unified_reader') == 'focused-v1'
                and not reader['payload'].get('calibration_review')
                and reader['payload'].get('source_generation') == gen
                and reader['payload'].get('packet_path') == paper['packet_path']
                and paper.get('packet_source_generation') == paper.get('assessment_source_generation') == gen
                and paper.get('assessment_packet_sha256') == packet
                and source['payload'].get('paper_id') == reader['payload'].get('paper_id') == pid
                and source['payload'].get('source_generation') == paper.get('current_source_generation') == gen
                and digest(source['payload']['source_manifest']) == source['payload'].get('source_manifest_sha256')
                == paper.get('current_source_manifest_sha256'), 'original/current job bindings disagree')
        from .workflow import assessment
        require(assessment(reader['result']['assessment'],reader['payload']) == paper['assessment'],
                'assessment differs from its immutable reader result')
    require(all(original.get(k) == current.get(k) == old_source['payload']['source_manifest'].get(k)
                == new_source['payload']['source_manifest'].get(k) for k in LOCAL), 'supplied sources changed')
    require(not conn.execute("SELECT 1 FROM jobs WHERE stage IN ('reader','retrieval') "
            "AND json_extract(payload,'$.paper_id')=? AND json_extract(payload,'$.source_generation')>? "
            "AND id NOT IN (?,?) LIMIT 1",(pid,base,new['id'],new_source['id'])).fetchone(),
            'additional source attempts require separate review')
    # Refuse intervening attachment/retry or restoration even if final bytes match.
    for event in conn.execute("SELECT kind,payload FROM events WHERE id>? AND "
            "json_extract(payload,'$.paper_id')=? AND kind IN ('paper_updated','paper_metadata_enriched')", (increment,pid)):
        changes = json.loads(event['payload']).get('changes',{})
        require(not set(LOCAL + ('source_generation',)).intersection(changes), 'intervening source revision')

    def native(reader, before=None):
        expected = dict(reader['result']['assessment']['native_discovery'],
                        packet_sha256=packet, actor=reader['result']['actor'])
        rows = conn.execute("SELECT id,payload FROM events WHERE kind='control_updated' "
            "AND json_extract(payload,'$.key')=? AND id<? ORDER BY id DESC",
            ('native-assessment:'+pid, before or 2**63-1))
        event = rows.fetchone()
        require(event is not None and json.loads(event['payload']).get('value') == expected,
                'latest original/native publication differs from its completed reader')
        return expected, event['id']
    old_native, old_event = native(old,increment); new_native, new_event = native(new)
    saved = conn.execute('SELECT value FROM meta WHERE key=?',('state:native-assessment:'+pid,)).fetchone()
    require(saved and json.loads(saved[0]) == new_native, 'current native assessment has an intervening revision')
    from .native_records import comparisons
    require(not comparisons(old_native) and not comparisons(new_native)
            and not old_native.get('process_activations') and not new_native.get('process_activations')
            and old_native.get('process_audit',{}).get('status') == new_native.get('process_audit',{}).get('status') == 'no-eligible-comparison'
            and original['assessment']['paper_decision'] == current['assessment']['paper_decision'],
            'comparison/process or prospect disagreement requires separate review')
    require(not conn.execute("SELECT 1 FROM meta WHERE key IN (?,?)",('state:native-record-supplement:'+old['id'],
            'state:native-record-supplement:'+new['id'])).fetchone(), 'additional comparison sidecars require separate review')
    state = json.loads(conn.execute("SELECT value FROM meta WHERE key='state:discovery_frontiers'").fetchone()[0])
    node = state['nodes'].get(pid)
    from . import frontiers
    from .discovery import _native_paper
    derived = frontiers.record_node(state,_native_paper(current,old_native['paper_state']),old_native['groups'],
        encounter_depth=min(current.get('discovery_bridge_depths') or [0]),reason=old_native['reason'])['nodes'][pid]
    require(node and node.get('groups_sha256') == frontiers.digest(new_native['groups']) and node.get('status') == derived['status'],
            'citation route disagreement requires separate review')
    require(not any(str(w.get('trigger_comparison_id','')).startswith(pid+'_') for w in state['process_windows'].values()),
            'paper already triggered process obligations')
    require(pid not in state.get('native_assessment_pending',{}) and pid not in state.get('process_assessment_pending',{})
            and pid not in state.get('workflow_deferred_tasks',{}), 'pending native review requires separate resolution')
    changes = {k:original.get(k) for k in BOUND}
    changes.update(retrieval_revision_pending=False,retired_source_generation=max(generation,current.get('retired_source_generation',0)))
    restored_node = dict(node,groups_sha256=frontiers.digest(old_native['groups']),reason=old_native['reason'])
    return {'repair':REPAIR,'paper_id':pid,'before_sha256':digest(current),'changes':changes,
        'metadata_event_ids':metadata,'increment_event_id':increment,
        'original_reader_job':old['id'],'alternative_reader_job':new['id'],
        'original_retrieval_job':old_source['id'],'alternative_retrieval_job':new_source['id'],
        'original_native_event_id':old_event,'alternative_native_event_id':new_event,
        'original_native':old_native,'alternative_native':new_native,
        'packet_sha256':packet,'original_node':restored_node,'previous_node':node,
        'jobs':{j['id']:digest(j) for j in (old,new,old_source,new_source)}}


def apply(conn, run, proofs, actor, reason):
    from .validator_repair import readonly_coordinator
    from .transactions import transaction_view
    c = transaction_view(readonly_coordinator(run),conn)
    for expected in proofs:
        proof = prove(conn,run,expected['paper_id'])
        require(proof == expected,'proof changed after continuation preview')
        pid = proof['paper_id']; before = c.store.paper(pid)
        # Separately index the extra reading; its immutable job/publication remains.
        c.store.set_state('alternative-reading:'+proof['alternative_reader_job'],
            dict(proof,actor=actor,reason=reason,scope='accidental-identical-source-reading'),reason)
        c.store._event(conn,'paper_updated',{'paper_id':pid,'changes':proof['changes'],
            'previous':{k:before.get(k) for k in proof['changes']},'actor':actor,'reason':reason,
            'repair':REPAIR,'source_generation_repair':proof})
        conn.execute('UPDATE papers SET record=?,status=?,updated_at=? WHERE id=?',
            (canonical(dict(before,**proof['changes'])),proof['changes']['status'],time.time(),pid))
        c.store.set_state('native-assessment:'+pid,proof['original_native'],reason)
        def restore_node(state):
            state['nodes'][pid] = proof['original_node']
            return state
        c.store.mutate_state_compact('discovery_frontiers',restore_node,reason,history_field='history')


def verify_archive(conn, value):
    """Keep the reconciliation auditable even after later genuine source changes."""
    require(value.get('repair') == REPAIR and value.get('scope') == 'accidental-identical-source-reading'
            and value.get('actor') and value.get('reason'),'alternative lacks explicit attribution')
    for jid, checksum in value['jobs'].items():
        row = conn.execute('SELECT payload,result FROM jobs WHERE id=?',(jid,)).fetchone()
        require(row and digest({'id':jid,'payload':json.loads(row['payload']),'result':json.loads(row['result'])}) == checksum,
                'preserved source/reader job changed')
    for label in ('original','alternative'):
        event = conn.execute('SELECT payload FROM events WHERE id=?',(value[label+'_native_event_id'],)).fetchone()
        require(event and json.loads(event[0]).get('value') == value[label+'_native'], 'preserved native history changed')
