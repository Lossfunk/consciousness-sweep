"""Durable publication of prepared answers; no inference, recovery or adjudication."""
import hashlib
import json
import os
from pathlib import Path
import time

from jsonschema import ValidationError

from sweep import discovery
from sweep.common import canonical, digest, inside, save_json
from sweep.coordinator import validate_execution_provenance
from sweep.sources import _publish_immutable
from sweep.transactions import transaction_view
from sweep.validation import require_integrity


class Hold(ValueError):
    pass


class Reconcile(ValueError):
    pass


def immutable(path, value):
    _publish_immutable(path, value, conflict_reason='Publication inbox bytes changed')


def failure_reason(error):
    # jsonschema's full rendering can repeat an entire paper/answer. The original
    # immutable input remains available; keep the operational receipt compact.
    if isinstance(error, ValidationError):
        location = '/'.join(map(str, error.absolute_path)) or '<result>'
        return ('Result schema validation failed at ' + location + ': ' + error.message)[:2000]
    return str(error)[:2000]


class PublicationLane:
    def __init__(self, coordinator):
        self.c = coordinator
        self.root = coordinator.run_dir.resolve()
        self.inbox = inside(self.root / 'intake' / 'publication-inbox-v1', self.root)
        self.pending = self.inbox / 'pending'
        self.indexed = False
        self.gate = self.root / 'intake' / 'writer-gate.json'
        self.lock_path = self.root / 'intake' / 'publication-lane.lock'

    def lock(self):
        from .coordination import lock
        return lock(self.root)

    def require_open(self):
        # A missing/malformed gate is not permission. STOP holds new admissions,
        # while the OPEN writer gate permits already admitted results to settle.
        if not self.gate.is_file() or json.loads(self.gate.read_text()).get('mode') != 'OPEN':
            raise Hold('Writer gate is not OPEN')
        control = self.c.store.get_state('publication-control')
        if control and (control.get('mode') != 'OPEN' or any(
                json.loads(self.gate.read_bytes()).get(k) != v for k, v in control.items())):
            raise Hold('Publication control and file gate disagree; reconcile explicitly')

    def stage(self, kind, entity_id, answer_path, actor, proof_path, pointer_path):
        if kind not in {'model', 'native'} or not actor.strip():
            raise ValueError('Explicit model/native publication and actor required')
        if entity_id.startswith('calibration:'):
            raise ValueError('Calibration adjudication stays with the supervisor')
        files = {}
        for name, path in [('answer.json', answer_path), ('settings.json', proof_path), ('pointer.json', pointer_path)]:
            path = inside(Path(path).resolve(), self.root)
            files[name] = path.read_bytes()
        values = {name: json.loads(raw) for name, raw in files.items()}
        self.validate_shapes(kind, values)
        data = values['answer.json']
        fence = {k: data.get(k) for k in ('owner', 'token')} if kind == 'model' else data.get('native_lease', {})
        if not isinstance(fence, dict) or not isinstance(fence.get('owner'), str) or type(fence.get('token')) is not int:
            raise ValueError('A bound existing lease is required; no automatic recovery')
        manifest = {'kind': kind, 'entity_id': entity_id, 'actor': actor,
                    'owner': fence['owner'], 'token': fence['token'],
                    'files': {k: hashlib.sha256(v).hexdigest() for k, v in files.items()}}
        identifier = digest(manifest)
        target = self.inbox / identifier
        with self.lock():
            self.require_open()
            if kind == 'model':
                self.validate_prepared_result(entity_id, data)
            for name, value in files.items():
                immutable(target / name, value)
            self.mark_pending(identifier)
            # Publish manifest last, including after the derived queue marker.
            # A crashed staging caller cannot leave a consumable request that
            # the already-running publisher would not notice until restart.
            immutable(target / 'request.json', (canonical(manifest) + '\n').encode())
        return identifier

    @staticmethod
    def validate_shapes(kind, values):
        for name in ('answer.json', 'settings.json', 'pointer.json'):
            if not isinstance(values[name], dict):
                raise Reconcile(name + ' must contain a JSON object')
        answer, proof, pointer = (values[name] for name in
                                 ('answer.json', 'settings.json', 'pointer.json'))
        observations = proof.get('actual_local_turn_settings')
        if not isinstance(observations, list) or not observations or any(
                not isinstance(row, dict) for row in observations):
            raise Reconcile('Observed settings must be a nonempty list of objects')
        if any(not isinstance(pointer.get(k), str) or not pointer[k].strip()
               for k in ('session_id', 'agent_path')):
            raise Reconcile('Missing exact worker identity pointer')
        if kind == 'model':
            if not isinstance(answer.get('result'), dict):
                raise Reconcile('Model envelope requires a result object; retain the original and correct only transport explicitly')
            if not isinstance(answer.get('execution_provenance'), dict):
                raise Reconcile('Model envelope requires source-only execution_provenance')

    def validate_prepared_result(self, entity_id, answer):
        # Reuse the validators for the worker's prepared source. Do not prepare a new task,
        # change its lease, project a result or reinterpret science during staging.
        job = self.c.store.job(entity_id)
        if answer.get('job_id') != entity_id or not job:
            raise Reconcile('Unknown or mismatched existing job')
        path = inside(self.root / 'jobs' / entity_id / 'schema.json', self.root)
        schema = json.loads(path.read_bytes())
        if digest(schema) != answer.get('schema_sha256'):
            raise Reconcile('Prepared answer schema binding changed')
        source = json.loads(path.with_name('source.json').read_bytes())
        if digest(source) != answer.get('source_sha256'):
            raise Reconcile('Prepared answer source binding changed')
        try:
            if job['stage'] == 'reader':
                # Combined readers validate each part through the existing
                # workflow; the nested reader schema has its own local $refs.
                from .workflow import validate_reader
                validate_reader(answer['result'], source, job['payload'])
            else:
                from .screening import validate
                decisions = answer['result'].get('decisions')
                if not isinstance(decisions, list) or any(not isinstance(row, dict) for row in decisions):
                    raise Reconcile('Screening result schema requires a decisions array of objects')
                validate(answer['result'], job['stage'], source['papers'])
        except ValidationError as error:
            raise Reconcile(failure_reason(error)) from error

    def mark_pending(self, identifier):
        immutable(self.pending / (identifier + '.json'), (identifier + '\n').encode())

    def unmark_pending(self, identifier):
        # Only this derived queue index is removable. Original answers,
        # manifests, acknowledgements and reconciliation receipts are retained.
        (self.pending / (identifier + '.json')).unlink(missing_ok=True)

    def ensure_index(self):
        """Rebuild once at startup, never on every poll; caller holds the lock.

        A restart recovers crashes between request/ack installation and index
        maintenance. Offline database restoration requires restarting this helper.
        """
        if self.indexed:
            return
        head = self.inbox / 'index-head.json'
        if head.is_file():
            checkpoint = json.loads(head.read_bytes())
            identifier = checkpoint.get('request_sha256')
            saved = self.c.store.get_state('coordination-publication:' + str(identifier))
            receipt = self.inbox / str(identifier) / 'accepted.json'
            if saved and saved == checkpoint and receipt.is_file() and json.loads(receipt.read_bytes()) == saved:
                # Normal new CLI processes need only this indexed ledger check.
                # An older restored DB lacks/mismatches the head and triggers
                # full reconstruction. Stage installs its pending marker first.
                self.indexed = True
                return
        prefix = 'state:coordination-publication:'
        with self.c.store._connection() as conn:
            acks = {row[0][len(prefix):]: json.loads(row[1]) for row in conn.execute(
                'SELECT key,value FROM meta WHERE key LIKE ?', (prefix + '%',))}
        for path in self.inbox.glob('*/request.json'):
            identifier = path.parent.name
            receipt = path.parent / 'accepted.json'
            settled = (identifier in acks and receipt.is_file()
                       and json.loads(receipt.read_bytes()) == acks[identifier])
            if settled or (path.parent / 'blocked.json').exists():
                self.unmark_pending(identifier)
            else:
                self.mark_pending(identifier)
        self.indexed = True

    def load(self, identifier):
        if len(identifier) != 64 or any(ch not in '0123456789abcdef' for ch in identifier):
            raise ValueError('Invalid queue identity')
        folder = inside(self.inbox / identifier, self.root)
        manifest = json.loads((folder / 'request.json').read_bytes())
        if (not isinstance(manifest, dict) or digest(manifest) != identifier
                or not isinstance(manifest.get('files'), dict)
                or set(manifest['files']) != {'answer.json', 'settings.json', 'pointer.json'}
                or manifest.get('kind') not in ('model', 'native')
                or any(not isinstance(manifest.get(k), str) or not manifest[k].strip()
                       for k in ('actor', 'entity_id', 'owner'))
                or type(manifest.get('token')) is not int):
            raise Reconcile('Publication manifest changed')
        values = {}
        for name, expected in manifest['files'].items():
            raw = inside(folder / name, self.root).read_bytes()
            if hashlib.sha256(raw).hexdigest() != expected:
                raise Reconcile('Prepared answer or attestation changed')
            values[name] = json.loads(raw)
        return manifest, values

    @staticmethod
    def verify_settings(profile, values, provenance=None):
        proof, pointer = values['settings.json'], values['pointer.json']
        observed = proof.get('actual_local_turn_settings')
        if proof.get('settings_match') is not True or not observed:
            raise Reconcile('Missing observed local worker settings')
        if not pointer.get('session_id') or not pointer.get('agent_path'):
            raise Reconcile('Missing exact worker identity pointer')
        if any(x.get('model') != profile.get('model') or x.get('effort') != profile.get('effort') for x in observed):
            raise Reconcile('Observed settings differ from the existing intended profile')
        if provenance is not None:
            validate_execution_provenance(profile, provenance, required=True)
            if provenance['worker_context_id'] != pointer['session_id']:
                raise Reconcile('Worker identity and execution provenance disagree')
        # These are allowlisted local attestations, not proof of provider identity.

    def _model(self, c, manifest, values, path):
        answer = values['answer.json']
        job = c.store.job(manifest['entity_id'])
        if not job or answer.get('job_id') != job['id']:
            raise Reconcile('Unknown or mismatched existing job')
        if (answer.get('owner'), answer.get('token')) != (manifest['owner'], manifest['token']):
            raise Reconcile('Manifest and answer lease mismatch')
        profile = c.profile_for_job(job)
        provenance = answer.get('execution_provenance')
        if not provenance:
            raise Reconcile('Missing source-only execution provenance')
        self.verify_settings(profile, values, provenance)
        task = json.loads((self.root / 'jobs' / job['id'] / 'task.json').read_bytes())
        for key in ('job_id', 'owner', 'token', 'prompt_sha256', 'schema_sha256', 'source_sha256', 'intended_profile_sha256'):
            if key not in answer or answer[key] != task.get(key):
                raise Reconcile('Prepared answer binding changed: ' + key)
        self.validate_prepared_result(job['id'], answer)
        if job['state'] == 'complete':
            # Retrospective handover: reconcile an answer that the old supervisor
            # already committed, without resubmitting or changing its attribution.
            saved = job.get('result') or {}
            if (job['owner'], job['token']) != (manifest['owner'], manifest['token']) or (
                    saved.get('assessment') != answer['result'] or saved.get('actor') != manifest['actor']
                    or saved.get('execution_provenance') != provenance):
                raise Reconcile('Completed result does not exactly match this publication')
            c.project_results()
            return 'reconciled-existing-completion'
        if job['state'] != 'running':
            raise Reconcile('Job needs explicit lease reconciliation')
        from .exchange import check_worker
        check_worker(c, 'model', job['id'], manifest['owner'], manifest['token'], provenance['worker_context_id'])
        c.submit(job['id'], path, manifest['actor'], compact=True)
        return 'published'

    def _native(self, c, manifest, values):
        # Support ordinary leased native tasks, including bounded acquisitions.
        # A legacy native result with no queue receipt cannot be proved identical
        # from its terminal event alone; preserve it and request reconciliation.
        task_id = manifest['entity_id']
        if task_id.startswith('calibration:'):
            raise Reconcile('Calibration adjudication requires supervisor review')
        with c.store._connection() as conn:
            row = conn.execute('SELECT * FROM native_task_control WHERE task_id=?', (task_id,)).fetchone()
        if not row or (row['owner'], row['token']) != (manifest['owner'], manifest['token']):
            raise Reconcile('Native lease no longer owned; do not blindly replay')
        tasks = {t['task_id']: t for t in discovery._native_candidates(c, hydrate=False)}
        if task_id not in tasks:
            raise Reconcile('Native task no longer available')
        task = discovery._hydrate_native_task(c, tasks[task_id])
        if task.get('task') != 'bounded-public-source-acquisition':
            raise Reconcile('Queued native publication supports bounded acquisition outputs; other native reviews stay supervised')
        profile = task.get('intended_profile') or c.plan['profiles']['reader']
        self.verify_settings(profile, values)
        from .exchange import check_worker
        check_worker(c, 'native', task_id, manifest['owner'], manifest['token'], values['pointer.json']['session_id'])
        discovery.submit_native(c, task_id, values['answer.json'], manifest['actor'])
        return 'published'

    def publish(self, identifier, fault=None):
        with self.lock():
            self.require_open()
            require_integrity(self.c)
            self.ensure_index()
            manifest, values = self.load(identifier)
            key = 'coordination-publication:' + identifier
            # The result and the publication acknowledgement commit in the SAME
            # transaction. Lost acknowledgement never calls submit again.
            with self.c.store._transaction() as conn:
                c = transaction_view(self.c, conn)
                saved = c.store.get_state(key)
                if saved:
                    if saved['request_sha256'] != identifier:
                        raise Reconcile('Acknowledgement mismatch')
                    result = dict(saved, replayed=True)
                else:
                    if (self.inbox / identifier / 'accepted.json').exists():
                        raise Reconcile('Unbacked file receipt: inspect restored database and receipt before publication')
                    self.validate_shapes(manifest['kind'], values)
                    path = self.inbox / identifier / 'answer.json'
                    disposition = self._model(c, manifest, values, path) if manifest['kind'] == 'model' else self._native(c, manifest, values)
                    if fault:
                        fault('before-commit')
                    result = {'request_sha256': identifier, 'kind': manifest['kind'],
                              'owner': manifest['owner'], 'token': manifest['token'],
                              'entity_id': manifest['entity_id'], 'status': disposition,
                              'provider_verification': 'unknown', 'completed_at': time.time()}
                    c.store.set_state(key, result, 'Prepared response committed without another model invocation')
            if fault:
                fault('after-commit')
            # File receipt is reproducible from the committed record after a crash.
            durable = {k: v for k, v in result.items() if k != 'replayed'}
            immutable(self.inbox / identifier / 'accepted.json', (canonical(durable) + '\n').encode())
            save_json(self.inbox / 'index-head.json', durable)
            self.unmark_pending(identifier)
            return result

    def drain(self):
        """One bounded pass, suitable for a managed watcher. No hidden retry loop."""
        self.require_open()
        require_integrity(self.c)
        with self.lock():
            self.ensure_index()
            # Stable order within the pending set. Settled history is not polled.
            pending = sorted(self.pending.glob('*.json'), key=lambda p: (p.stat().st_mtime_ns, str(p)))
        results = []
        for marker in pending:
            path = self.inbox / marker.stem / 'request.json'
            if not marker.exists():
                continue
            if not path.is_file():
                # A staging process may have died just before installing its
                # manifest. Preserve its files; report once for reconciliation.
                receipt = path.parent / 'blocked.json'
                with self.lock():
                    if path.is_file():
                        continue
                    if not receipt.exists():
                        immutable(receipt, (canonical({'status': 'needs-reconciliation',
                            'reason': 'Interrupted inbox staging: missing final manifest',
                            'at': time.time()}) + '\n').encode())
                    self.unmark_pending(marker.stem)
                results.append(json.loads(receipt.read_bytes()))
                continue
            if (path.parent / 'blocked.json').exists():
                with self.lock():
                    self.unmark_pending(marker.stem)
                continue
            try:
                results.append(self.publish(path.parent.name))
            except Hold:
                raise
            except (ValueError, ValidationError) as error:
                # A global integrity checkpoint is a temporary global hold,
                # not evidence that every individual draft is defective.
                require_integrity(self.c)
                receipt = {'status': 'needs-reconciliation', 'request_sha256': marker.stem,
                           'reason': failure_reason(error), 'error_type': type(error).__name__, 'at': time.time()}
                try:
                    request = json.loads(path.read_bytes())
                except ValueError:
                    request = None
                if isinstance(request, dict) and digest(request) == marker.stem:
                    receipt.update(entity_id=request.get('entity_id'), kind=request.get('kind'))
                with self.lock():
                    blocked = path.parent / 'blocked.json'
                    if blocked.exists():
                        receipt = json.loads(blocked.read_bytes())
                    else:
                        immutable(blocked, (canonical(receipt) + '\n').encode())
                    self.unmark_pending(marker.stem)
                results.append(receipt)
        return results

    def owned_work(self):
        with self.c.store._connection() as conn:
            count = conn.execute("SELECT count(*) FROM jobs WHERE state='running'").fetchone()[0]
            if conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='native_task_control'").fetchone():
                count += conn.execute('SELECT count(*) FROM native_task_control WHERE owner IS NOT NULL').fetchone()[0]
            return count

    def reconcile(self, identifier, actor, reason):
        if not actor.strip() or not reason.strip():
            raise ValueError('Reconciliation requires actor and evidence-backed reason')
        with self.lock():
            result = self.publish(identifier)
            self.c.store.event('publication_reconciled', {'request_id': identifier,
                'actor': actor, 'reason': reason, 'replayed': result.get('replayed', False)})
            return result

    def next_task(self, owner=None):
        with self.lock():
            self.require_open()
            self.ensure_index()
            # Prioritize queued completions before allocating another unit.
            if any(self.pending.glob('*.json')):
                return {'status': 'publication-pending'}
            return self.c.next_task(owner=owner)
