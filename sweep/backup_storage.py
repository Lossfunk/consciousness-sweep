"""Lossless storage maintenance for closed operational backups, never run records.

This command deliberately bypasses Coordinator: it may archive an older runtime's
closed backups without migrating that runtime or writing to its live database.
Original receipts remain immutable; archive records map their paths and hashes
back to exactly restorable bytes. No source, job or delivery files are removed.
"""
from contextlib import contextmanager, closing
import gzip
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import sqlite3
import stat
import tempfile
import time
import uuid

from .common import canonical, digest, file_hash

FORMAT = 'portable-backup-archive-v1'
CHUNK = 1024 * 1024
RESERVE = 16 * CHUNK


def _path(run, relative):
    value = str(relative)
    parts = PurePosixPath(value)
    if (not value or parts.is_absolute() or '\\' in value or
            any(part in {'.', '..'} for part in value.split('/'))):
        raise ValueError('Unsafe backup storage path')
    current = Path(run)
    for part in parts.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError('Symlinked backup storage path refused')
    return current


def _backup(run, relative):
    path = _path(run, relative)
    parts = PurePosixPath(relative).parts
    if (len(parts) != 3 or parts[0] not in {'intake', 'continuations'} or
            not re.fullmatch(r'state-before(?:-reconciliation)?\.sqlite3', parts[-1])):
        raise ValueError('Only recognized historical backup paths are eligible')
    return path


def _signature(path):
    s = path.lstat()
    if not stat.S_ISREG(s.st_mode) or s.st_nlink != 1:
        raise ValueError('Backup must be a regular file with no hard-link aliases')
    return (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)


def _sidecars(path):
    # WAL/journal may contain durable changes and always block archiving. SHM is
    # an index, not source data. A leftover SHM without WAL is preserved in place.
    if any(Path(str(path) + suffix).exists() or Path(str(path) + suffix).is_symlink()
           for suffix in ('-wal', '-journal')):
        raise ValueError('Backup has SQLite WAL/journal sidecars; reconcile before archiving')
    shm = Path(str(path) + '-shm')
    if shm.exists() or shm.is_symlink():
        _signature(shm)
        return {'shm_sha256': file_hash(shm), 'shm_bytes': shm.stat().st_size}
    return {}


def _standalone(path):
    _signature(path)
    sidecars = _sidecars(path)
    # SQLite backup() may retain a WAL header in a complete standalone image.
    # Preserve it exactly; immutable reads never create or consume WAL sidecars.
    with path.open('rb') as stream:
        header = stream.read(100)
    if len(header) != 100 or header[:16] != b'SQLite format 3\x00' or header[18:20] not in (b'\x01\x01', b'\x02\x02'):
        raise ValueError('Backup is not a recognized SQLite file')
    return sidecars


def require_space(directory, required):
    free = shutil.disk_usage(directory).free
    if free < required + RESERVE:
        raise ValueError(f'Insufficient storage headroom: need {required + RESERVE} free bytes, have {free}; no source removed')


def _sync_dir(path):
    if os.name != 'nt':
        fd = os.open(path, os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)


def _publish(temp, destination):
    # No clobber, including interrupted/repeated invocations.
    os.link(temp, destination)
    _sync_dir(destination.parent)


def _write_new(path, value):
    data = (canonical(value) + '\n').encode()
    fd, name = tempfile.mkstemp(prefix='.record-', dir=path.parent)
    temp = Path(name)
    try:
        with os.fdopen(fd, 'wb') as out:
            out.write(data); out.flush(); os.fsync(out.fileno())
        _publish(temp, path)
    finally:
        temp.unlink(missing_ok=True)


@contextmanager
def _lock(run):
    directory = _path(run, 'storage/backups')
    directory.mkdir(parents=True, exist_ok=True)
    lock = _path(run, 'storage/backups/maintenance.lock')
    with lock.open('a+b') as handle:
        if os.name == 'nt':
            import msvcrt
            handle.seek(0); handle.write(b'0'); handle.flush(); handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            yield
        finally:
            if os.name == 'nt':
                handle.seek(0); msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle, fcntl.LOCK_UN)


def _run_identity(run, quiet=False):
    run = Path(run).absolute()
    if run.is_symlink() or not run.is_dir():
        raise ValueError('Run must be an existing nonsymlink directory')
    path = _path(run, 'state.sqlite3')
    if quiet and not _path(run, 'STOP').is_file():
        raise ValueError('Pause admissions and drain writers before backup maintenance')
    with closing(sqlite3.connect(path.as_uri() + '?mode=ro', uri=True)) as conn:
        conn.execute('PRAGMA query_only=ON')
        conn.execute('BEGIN')
        plan = json.loads(conn.execute("SELECT value FROM meta WHERE key='plan'").fetchone()[0])
        if quiet:
            if conn.execute("SELECT 1 FROM jobs WHERE state='running' LIMIT 1").fetchone():
                raise ValueError('Automatic workers must drain before backup maintenance')
            if conn.execute("SELECT 1 FROM sqlite_master WHERE name='native_task_control'").fetchone():
                if conn.execute('SELECT 1 FROM native_task_control WHERE owner IS NOT NULL LIMIT 1').fetchone():
                    raise ValueError('Native leases must drain before backup maintenance')
            if conn.execute('SELECT 1 FROM retrieval_attempts WHERE completed_at IS NULL LIMIT 1').fetchone():
                raise ValueError('Interrupted acquisitions need terminal receipts before backup maintenance')
        return {'plan_sha256': digest(plan), 'event_id': conn.execute('SELECT coalesce(max(id),0) FROM events').fetchone()[0]}


def _matching_backup(path, identity):
    _standalone(path)
    with closing(sqlite3.connect(path.as_uri() + '?mode=ro&immutable=1', uri=True)) as conn:
        plan = json.loads(conn.execute("SELECT value FROM meta WHERE key='plan'").fetchone()[0])
    if digest(plan) != identity['plan_sha256']:
        raise ValueError('Backup belongs to a different original run plan')


def _records(run):
    directory = _path(run, 'storage/backups/records')
    if not directory.exists():
        return []
    result = []
    for path in sorted(directory.glob('*.json')):
        _path(run, path.relative_to(run).as_posix())
        record = json.loads(path.read_text())
        if record.get('format') != FORMAT:
            raise ValueError('Unsupported backup archive record')
        _backup(run, record['original_path'])
        if path.name != digest(record['original_path']) + '.json':
            raise ValueError('Backup archive record path mismatch')
        if not re.fullmatch(r'[a-f0-9]{64}', record['original_sha256']):
            raise ValueError('Invalid original backup hash')
        if record['archive_path'] != 'storage/backups/blobs/' + record['original_sha256'] + '.sqlite3.gz':
            raise ValueError('Invalid backup archive blob path')
        _path(run, record['archive_path'])
        result.append(record)
    return result


def inventory(run, keep_latest=2):
    """Read-only plan. Always retain the latest continuation plus recent backups."""
    run = Path(run).absolute()
    if type(keep_latest) is not int or keep_latest < 1:
        raise ValueError('Keep at least one recent uncompressed restore point')
    identity = _run_identity(run)
    found = {}
    for parent in ('intake', 'continuations'):
        directory = _path(run, parent)
        if not directory.exists():
            continue
        for folder in directory.iterdir():
            if folder.is_symlink() or not folder.is_dir():
                continue
            for path in folder.glob('state-before*.sqlite3'):
                relative = path.relative_to(run).as_posix()
                try:
                    _backup(run, relative)
                except ValueError:
                    continue
                s = path.lstat()
                found[relative] = {'original_path': relative, 'original_bytes': s.st_size,
                    'mtime_ns': s.st_mtime_ns, 'original_present': True}
    records = _records(run)
    for record in records:
        found.setdefault(record['original_path'], {k: record[k] for k in ('original_path','original_bytes','mtime_ns')})['archived'] = True
    ordered = sorted(found.values(), key=lambda x: (-x['mtime_ns'], x['original_path']))
    # Select across archived and unarchived files so a rerun doesn't retain two
    # more old files each time. The latest successful continuation is protected.
    keep = {x['original_path'] for x in ordered[:keep_latest]}
    continuations = [x for x in ordered if x['original_path'].startswith('continuations/')]
    if continuations:
        keep.add(continuations[0]['original_path'])
    for item in ordered:
        if item['original_path'] in keep and not item.get('original_present'):
            raise ValueError('Required recent restore point is archived; restore it first: ' + item['original_path'])
        item['action'] = 'keep' if item['original_path'] in keep else ('archive' if item.get('original_present') else 'already-archived')
    return {'format': FORMAT, 'run_directory': str(run), 'identity': identity,
        'keep_latest': keep_latest, 'backups': ordered,
        'uncompressed_backup_bytes': sum(x['original_bytes'] for x in ordered if x.get('original_present')),
        'candidate_bytes': sum(x['original_bytes'] for x in ordered if x['action']=='archive'),
        'archive_bytes': sum(_path(run, x).stat().st_size for x in {r['archive_path'] for r in records}),
        'scope': 'Historical SQLite backups only; sources, live database, records and deliveries untouched'}


def _verify_archive(run, record, output=None):
    archive = _path(run, record['archive_path'])
    if file_hash(archive) != record['archive_sha256'] or archive.stat().st_size != record['archive_bytes']:
        raise ValueError('Backup archive hash/size mismatch; preserve original')
    h, size = hashlib.sha256(), 0
    with gzip.open(archive, 'rb') as source:
        while block := source.read(CHUNK):
            size += len(block)
            if size > record['original_bytes']:
                raise ValueError('Archive exceeds recorded original size')
            h.update(block)
            if output is not None:
                output.write(block)
    if size != record['original_bytes'] or h.hexdigest() != record['original_sha256']:
        raise ValueError('Restored backup hash/size mismatch; preserve original')


def _compress(source, destination):
    h, size = hashlib.sha256(), 0
    with source.open('rb') as inp, destination.open('wb') as raw:
        with gzip.GzipFile(fileobj=raw, mode='wb', filename='', mtime=0, compresslevel=1) as out:
            while block := inp.read(CHUNK):
                out.write(block); h.update(block); size += len(block)
        raw.flush(); os.fsync(raw.fileno())
    return h.hexdigest(), size


def _archive_one(run, relative, identity, actor, reason):
    source = _backup(run, relative)
    _matching_backup(source, identity)
    signature = _signature(source)
    sidecars = _sidecars(source)
    record_path = _path(run, 'storage/backups/records/' + digest(relative) + '.json')
    record_path.parent.mkdir(parents=True, exist_ok=True)
    if record_path.exists():
        record = next(r for r in _records(run) if r['original_path'] == relative)
        if record['plan_sha256'] != identity['plan_sha256']:
            raise ValueError('Archive record belongs to another run')
        _verify_archive(run, record)
    else:
        blobs = _path(run, 'storage/backups/blobs'); blobs.mkdir(parents=True, exist_ok=True)
        # Conservative streaming bound: compressed output may be slightly larger.
        require_space(blobs, signature[2] + signature[2] // 1000 + CHUNK)
        fd, name = tempfile.mkstemp(prefix='.compress-', dir=blobs); os.close(fd)
        temp = Path(name)
        try:
            sha, size = _compress(source, temp)
            archive = blobs / (sha + '.sqlite3.gz')
            record = {'format': FORMAT, 'original_path': relative, 'original_sha256': sha,
                'original_bytes': size, 'mtime_ns': signature[3], 'plan_sha256': identity['plan_sha256'],
                'preserved_sidecars': sidecars,
                'archive_path': archive.relative_to(run).as_posix(), 'archive_sha256': file_hash(temp),
                'archive_bytes': temp.stat().st_size, 'actor': actor, 'reason': reason, 'created_at': time.time()}
            if record['archive_bytes'] >= record['original_bytes']:
                return {'original_path': relative, 'status': 'kept-no-space-saving', 'reclaimed_bytes': 0}
            if archive.exists():
                # Compression bytes may differ across zlib versions; verify the
                # existing blob against the same original hash before sharing it.
                record.update(archive_sha256=file_hash(archive), archive_bytes=archive.stat().st_size)
                _verify_archive(run, record)
            else:
                _publish(temp, archive)
        finally:
            temp.unlink(missing_ok=True)
        _verify_archive(run, record)  # Stream-decompress and hash before publication/removal.
        _write_new(record_path, record)
    if _signature(source) != signature or file_hash(source) != record['original_sha256']:
        raise ValueError('Original backup changed during archive; original retained')
    if _standalone(source) != sidecars or sidecars != record.get('preserved_sidecars', {}):
        raise ValueError('Backup sidecars changed; original retained')
    if _run_identity(run, quiet=True) != identity:
        raise ValueError('Run changed during backup maintenance; original retained')
    # Archive + path mapping are already durable. A crash before/after unlink is
    # restartable: the existing record is verified and no history is overwritten.
    source.unlink()
    _sync_dir(source.parent)
    return {'original_path': relative, 'status': 'archived', 'original_bytes': record['original_bytes'],
        'archive_bytes': record['archive_bytes'], 'record': record_path.relative_to(run).as_posix()}


def archive(run, *, keep_latest=2, actor, reason):
    run = Path(run).absolute()
    if not str(actor).strip() or not str(reason).strip():
        raise ValueError('Backup maintenance requires actor and reason')
    identity = _run_identity(run, quiet=True)
    with _lock(run):
        plan = inventory(run, keep_latest)
        if plan['identity'] != identity:
            raise ValueError('Run changed while preparing archive')
        results = []
        for item in plan['backups']:
            if item['action'] == 'archive':
                results.append(_archive_one(run, item['original_path'], identity, actor, reason))
        result = {'format': FORMAT, 'actor': actor, 'reason': reason, 'created_at': time.time(),
            'results': results, 'after': inventory(run, keep_latest)}
        receipts = _path(run, 'storage/backups/operations'); receipts.mkdir(parents=True, exist_ok=True)
        _write_new(receipts / (uuid.uuid4().hex + '.json'), result)
        return result


def restore(run, relative, *, actor, reason):
    """Restore a backup's original bytes/path; never restore over the live ledger."""
    run = Path(run).absolute()
    if not str(actor).strip() or not str(reason).strip():
        raise ValueError('Backup restoration requires actor and reason')
    source = _backup(run, relative)
    identity = _run_identity(run, quiet=True)
    with _lock(run):
        record = next((r for r in _records(run) if r['original_path'] == relative), None)
        if not record or record['plan_sha256'] != identity['plan_sha256']:
            raise ValueError('No matching original backup archive record')
        if _sidecars(source) != record.get('preserved_sidecars', {}):
            raise ValueError('Backup sidecars changed; restore refused')
        if source.exists():
            if file_hash(source) != record['original_sha256']:
                raise ValueError('Restore destination exists with different bytes; refused')
            _standalone(source)
            return {'status': 'already-restored', 'original_path': relative}
        source.parent.mkdir(parents=True, exist_ok=True)
        require_space(source.parent, record['original_bytes'])
        fd, name = tempfile.mkstemp(prefix='.restore-', dir=source.parent); temp = Path(name)
        try:
            with os.fdopen(fd, 'wb') as out:
                _verify_archive(run, record, out); out.flush(); os.fsync(out.fileno())
            _matching_backup(temp, identity)
            if _run_identity(run, quiet=True) != identity:
                raise ValueError('Run changed during restoration')
            if _sidecars(source) != record.get('preserved_sidecars', {}):
                raise ValueError('Backup sidecars changed during restoration')
            os.utime(temp, ns=(record['mtime_ns'], record['mtime_ns']))
            _publish(temp, source)
        finally:
            temp.unlink(missing_ok=True)
        result = {'format': FORMAT, 'status': 'restored', 'original_path': relative,
            'original_sha256': record['original_sha256'], 'actor': actor, 'reason': reason, 'created_at': time.time()}
        receipts = _path(run, 'storage/backups/operations'); receipts.mkdir(parents=True, exist_ok=True)
        _write_new(receipts / (uuid.uuid4().hex + '.json'), result)
        return result
