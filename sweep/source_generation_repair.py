"""Evidence-bound correction of metadata counters on retained, deferred readings."""
import json
import time
from .common import canonical, digest

REPAIR = 'retained-packet-metadata-generation-v1'
OLD_REASON = 'Current assessment belongs to a superseded source generation'
LOCAL = {'provided_paths', 'fulltext_path', 'pdf_path', 'local_path'}
BOUND = {'packet_path', 'packet_source_generation', 'assessment_source_generation',
         'assessment_packet_sha256', 'current_source_generation', 'current_source_manifest_sha256',
         'reader_job', 'retrieval_job', 'assessment', 'retrieval'}


def prove(conn, pid):
    def require(value, reason):
        if not value:
            raise ValueError('Retained-packet repair refused: ' + reason)
    row = conn.execute('SELECT record FROM papers WHERE id=?', (pid,)).fetchone()
    require(row is not None, 'unknown paper')
    paper = json.loads(row[0]); base = paper.get('packet_source_generation'); current = paper.get('source_generation')
    held = paper.get('workflow_defer', {})
    require(type(base) is int and type(current) is int and current > base,
            'no stale generation to reconcile')
    require(held.get('active') is True and held.get('workflow') == 'focused-v1'
            and held.get('source_generation') == base and not paper.get('retrieval_revision_pending'),
            'no unchanged reconciled focused deferral')
    require(paper.get('assessment') is not None and paper.get('assessment_source_generation') == base
            and paper.get('current_source_generation') == base, 'original source bindings disagree')
    reader = conn.execute('SELECT * FROM jobs WHERE id=?', (paper.get('reader_job'),)).fetchone()
    retrieval = conn.execute('SELECT * FROM jobs WHERE id=?', (paper.get('retrieval_job'),)).fetchone()
    require(reader and reader['stage'] == 'reader' and reader['state'] == 'complete'
            and retrieval and retrieval['stage'] == 'retrieval' and retrieval['state'] == 'complete',
            'original completed source jobs are absent')
    rp, ap = json.loads(reader['payload']), json.loads(retrieval['payload'])
    require(rp.get('paper_id') == ap.get('paper_id') == pid
            and rp.get('source_generation') == ap.get('source_generation') == base
            and rp.get('packet_path') == paper.get('packet_path')
            and rp.get('packet_sha256') == paper.get('assessment_packet_sha256')
            and ap.get('source_manifest_sha256') == digest(ap.get('source_manifest'))
            and ap.get('source_manifest_sha256') == paper.get('current_source_manifest_sha256'),
            'packet or acquisition manifest changed')
    require(all(paper.get(k) == ap['source_manifest'].get(k) for k in LOCAL),
            'supplied local sources differ from the original manifest')
    generation, events, started = base, [], False
    for event in conn.execute("SELECT id,kind,payload FROM events WHERE kind IN ('paper_metadata_enriched','paper_updated') "
            "AND json_extract(payload,'$.paper_id')=? ORDER BY id", (pid,)):
        value = json.loads(event['payload']); changes = value.get('changes', {})
        new = changes.get('source_generation')
        if not started and (type(new) is not int or new <= base):
            continue
        started = True
        require(not (BOUND | LOCAL).intersection(changes), 'source bindings changed after metadata increment')
        if new is not None:
            fields = changes.get('metadata_changed_fields', [])
            require(event['kind'] == 'paper_metadata_enriched' and fields and not LOCAL.intersection(fields)
                    and value.get('previous', {}).get('source_generation') == generation
                    and new == generation + 1, 'generation lacks uninterrupted metadata-only history')
            generation = new; events.append(event['id'])
    require(events and generation == current, 'metadata counter differs from history')
    require(not conn.execute("SELECT 1 FROM jobs WHERE stage IN ('reader','retrieval') "
            "AND json_extract(payload,'$.paper_id')=? AND json_extract(payload,'$.source_generation')>? LIMIT 1",
            (pid,base)).fetchone(), 'a newer source job was actually admitted')
    require(not conn.execute("SELECT 1 FROM meta WHERE key IN (?,?) AND json_extract(value,'$.source_generation')>? LIMIT 1",
            ('state:native-assessment:'+pid,'state:bounded-acquisition:'+pid,base)).fetchone(),
            'newer native source work exists')
    changes = {'source_generation':base, 'retired_source_generation':max(current,paper.get('retired_source_generation',0))}
    return {'paper_id':pid,'before_sha256':digest(paper),'changes':changes,
            'metadata_event_ids':events,'reader_job_id':reader['id'],'retrieval_job_id':retrieval['id'],
            'packet_sha256':rp['packet_sha256']}, dict(paper,**changes)


def inspect(run, predecessor_report, snapshot):
    from . import validation, sanity
    from .validator_repair import readonly_coordinator
    c = readonly_coordinator(run)
    report = json.loads((c.run_dir/'delivery/validation.json').read_text())
    if (report.get('ok') is not False or report.get('incomplete') or not report.get('errors')
            or report.get('error_count') != len(report['errors'])
            or any(report.get(k) != predecessor_report.get(k) for k in
                ('scope','snapshot_event_id','error_count','validation_event_id'))
            or any(e.get('code') != 'paper_binding' or e.get('reason') != OLD_REASON for e in report['errors'])):
        raise ValueError('Predecessor validation contains unsupported or unbound failures')
    affected, overrides = [], {}
    with c.store._connection() as conn:
        conn.execute('BEGIN')
        for error in report['errors']:
            proof, paper = prove(conn, error['entity'])
            affected.append(proof); overrides[paper['paper_id']] = paper
    # TEMP view overlays only proven current counters. Main database stays mode=ro;
    # sources, jobs, results, hashes and historic events are validated unchanged.
    projected = readonly_coordinator(run, record_overrides=overrides)
    projected._source_generation_repair_preview = {p['paper_id']:p['changes'] for p in affected}
    checked = validation.validate(projected, persist=False)
    if not checked['ok'] or checked['snapshot_event_id'] != snapshot:
        raise ValueError('Replacement full validation failed or snapshot changed: ' + str(checked['errors']))
    light = sanity.check(projected, persist=False)
    if not light['ok'] or light['snapshot_event_id'] != snapshot:
        raise ValueError('Replacement sanity failed or snapshot changed: ' + str(light['errors']))
    return {'repair':REPAIR,'affected':affected,'snapshot_event_id':snapshot,
            'predecessor_report_sha256':digest(report),'predecessor_validation_event_id':report['validation_event_id'],
            'target_validation':{'ok':True,'checks':checked['checks'],'persisted':False},
            'target_sanity':{'ok':True,'persisted':False},
            'scope':'Append-first counter correction only; original source/reader records and deferral stay unchanged'}


def apply(conn, repair, actor, reason):
    for expected in repair['affected']:
        proof, paper = prove(conn, expected['paper_id'])
        if proof != expected:
            raise ValueError('Source-generation repair proof changed after preview')
        previous = json.loads(conn.execute('SELECT record FROM papers WHERE id=?',(proof['paper_id'],)).fetchone()[0])
        event = {'paper_id':proof['paper_id'],'changes':proof['changes'],
                 'previous':{k:previous.get(k) for k in proof['changes']},'actor':actor,'reason':reason,
                 'source_generation_repair':proof,'repair':REPAIR}
        conn.execute("INSERT INTO events(at,kind,payload) VALUES(?,'paper_updated',?)",(time.time(),canonical(event)))
        conn.execute('UPDATE papers SET record=?,updated_at=? WHERE id=?',(canonical(paper),time.time(),proof['paper_id']))
