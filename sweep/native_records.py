"""Typed comparison transport independent of process-search eligibility."""
import json
from pathlib import Path

from .common import digest, file_hash, inside
from jsonschema.exceptions import ValidationError
from .transactions import atomic_operation


def comparisons(payload):
    """Union explicit and legacy activation records without hiding conflicts."""
    rows = payload.get('comparisons', [])
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        raise ValueError('comparisons must be a list of typed comparison records')
    indexed = {}
    for row in rows:
        cid = row.get('comparison_id')
        if not isinstance(cid, str) or cid in indexed:
            raise ValueError('Standalone comparison IDs must be present and unique')
        indexed[cid] = row
    activated = set()
    for activation in payload.get('process_activations', []):
        row = activation['comparison']; cid = row['comparison_id']
        if cid in activated or (cid in indexed and indexed[cid] != row):
            raise ValueError('Process comparison is repeated or conflicts with its standalone record')
        activated.add(cid)
        indexed[cid] = row
    return list(indexed.values())


def validate(c, pid, payload, *, conn=None):
    from . import frontiers
    rows = comparisons(payload)
    c.store.require_native_ids(pid, payload['groups'], rows, conn=conn)
    # Transport neither earns a search nor certifies a scientific conclusion.
    for row in rows:
        try:
            frontiers._validate('experiments', row, frontiers._root())
        except ValidationError as exc:
            raise ValueError('Invalid typed native comparison: ' + str(exc)) from exc
    return rows


def verify_supplement(c, value):
    """Validate the original completed job binding; older source versions stay historical."""
    from . import frontiers
    job = c.store.job(value['reader_job_id'])
    if not job or job['stage'] != 'reader' or job['state'] != 'complete' or digest(job['result']) != value['original_result_sha256']:
        raise ValueError('Supplement requires the exact original completed reader result')
    payload = value['records']; pid = job['payload']['paper_id']
    if (pid != value['paper_id'] or payload['source_generation'] != job['payload']['source_generation']
            or value['packet_sha256'] != job['payload']['packet_sha256']
            or value['original_reader_actor'] != job['result']['actor']):
        raise ValueError('Supplement differs from its original reader/source binding')
    path = inside(c.run_dir / value['snapshot_path'], c.run_dir)
    if file_hash(path) != value['snapshot_sha256'] or json.loads(path.read_bytes()) != payload:
        raise ValueError('Supplement differs from its immutable input snapshot')
    validate(c, pid, payload)
    for group in payload['groups']:
        frontiers._validate('experiment_groups', group, frontiers._root())
    if not value.get('actor') or not value.get('reason') or value.get('scope') != 'preserved-reader-records-only':
        raise ValueError('Supplement requires explicit provenance and nonactivating scope')


@atomic_operation
def supplement(c, reader_job_id, input_path, expected_result_sha256, actor, reason):
    """Add already-authored own-run records without replacing readings or route decisions."""
    from .discovery import _source_proof
    from .validation import require_integrity
    require_integrity(c)
    if not actor.strip() or not reason.strip():
        raise ValueError('Supplement requires actor and an explanation of original-reader provenance')
    job = c.store.job(reader_job_id)
    if not job or job['stage'] != 'reader' or job['state'] != 'complete' or digest(job['result']) != expected_result_sha256:
        raise ValueError('Supply the exact original completed reader result hash')
    source = inside(Path(input_path), c.run_dir)
    raw = source.read_bytes(); records = json.loads(raw)
    if not isinstance(records, dict) or not records.get('comparisons'):
        raise ValueError('Supplement must contain already-authored comparison records')
    pid = job['payload']['paper_id']; paper = c.store.paper(pid)
    if paper.get('reader_job') != reader_job_id or paper.get('source_generation') != job['payload']['source_generation']:
        raise ValueError('Current reader/source changed; preserve the sidecar for separate review')
    if _source_proof(c, paper, records) != job['payload']['packet_sha256']:
        raise ValueError('Supplement source differs from its original reader packet')
    key = 'native-record-supplement:' + reader_job_id
    old = c.store.get_state(key)
    if old:
        if old['records'] != records or old['original_result_sha256'] != expected_result_sha256:
            raise ValueError('A different supplement already exists; never replace it silently')
        verify_supplement(c, old)
        return {'status': 'already-recorded', 'reader_job_id': reader_job_id}
    # Validate before creating a content-addressed immutable snapshot.
    from . import frontiers
    validate(c, pid, records)
    for group in records['groups']:
        frontiers._validate('experiment_groups', group, frontiers._root())
    path = c.run_dir / 'intake/native-records' / (reader_job_id + '-' + digest(records) + '.json')
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != raw:
            raise ValueError('Supplement snapshot already exists with different bytes')
    else:
        with path.open('xb') as output:
            output.write(raw)
    value = {'paper_id': pid, 'reader_job_id': reader_job_id, 'original_result_sha256': expected_result_sha256,
        'original_reader_actor': job['result']['actor'], 'packet_sha256': job['payload']['packet_sha256'],
        'records': records, 'snapshot_path': str(path.relative_to(c.run_dir)), 'snapshot_sha256': file_hash(path),
        'actor': actor, 'reason': reason, 'scope': 'preserved-reader-records-only'}
    verify_supplement(c, value)
    c.store.set_state(key, value, reason)
    return {'status': 'recorded', 'reader_job_id': reader_job_id, 'scope': value['scope'],
        'route_decisions_changed': False, 'model_calls': 0}
