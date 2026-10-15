"""Receipt-backed public source downloads inside one run; identity is not inferred."""
from pathlib import Path
import re
import time
import urllib.parse
import uuid

from .common import canonical, digest, inside
from .sources import SourceClient, SourceError, _publish_immutable, now, safe_url


def _public_location(url):
    parsed = urllib.parse.urlsplit(url)
    private_keys = {'api_key', 'apikey', 'token', 'key', 'access_token', 'signature'}
    query = urllib.parse.urlencode([(k, '[redacted]' if k.lower() in private_keys else v)
                                   for k, v in urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)])
    return urllib.parse.urlunsplit(parsed._replace(query=query, fragment=''))


def fetch(coordinator, paper_id, url, *, role='main', association_reason=None,
          reason, actor='supervising-agent', client=None):
    """Acquisition is authorized by the run; source attachment still verifies identity.

    A receipt before dispatch preserves interrupted/unknown attempts. A unique
    completion receipt records HTTP outcomes without cookies or response bodies.
    File bytes are immutable and no paper/source generation is changed here.
    """
    if not re.fullmatch(r'P[0-9]+', paper_id) or not coordinator.store.paper(paper_id):
        raise ValueError('Download requires an existing paper ID')
    if not isinstance(reason, str) or not reason.strip() or not isinstance(actor, str) or not actor.strip():
        raise ValueError('Download requires a reason and actor')
    if role not in {'main', 'supplement'} or role == 'supplement' and not (association_reason or '').strip():
        raise ValueError('Supplement download requires its source-grounded association reason')
    safe_url(url, resolve=False)
    from .workflow import admit_download
    remaining = admit_download(coordinator, paper_id, role)
    run_dir = coordinator.run_dir.resolve()
    directory = inside(run_dir / 'intake' / 'downloads' / paper_id, run_dir)
    attempt_id = uuid.uuid4().hex
    prefix = inside(directory / attempt_id, run_dir)
    requested = {'download_id': attempt_id, 'paper_id': paper_id, 'url': _public_location(url),
                 'role': role, 'association_reason': association_reason, 'reason': reason.strip(),
                 'actor': actor.strip(), 'requested_at': now(), 'status': 'requested-outcome-unknown'}
    request_path = prefix.with_suffix('.request.json')
    _publish_immutable(request_path, (canonical(requested) + '\n').encode(), conflict_reason='Download request changed')
    coordinator.store.event('source_download_requested', dict(requested,
        receipt_path=str(request_path.relative_to(run_dir))))
    client = client or SourceClient(max_attempts=1, deadline=time.monotonic() + min(60, remaining if remaining is not None else 60))
    entry = None
    try:
        body, response = client.get(url)
        content_type = next((str(v).split(';')[0].strip().lower() for k, v in response.get('headers', {}).items()
                             if k.lower() == 'content-type'), '')
        suffix = '.pdf' if body.lstrip().startswith(b'%PDF-') else '.xml' if content_type in {'application/xml', 'text/xml'} else '.txt' if content_type == 'text/plain' else '.bin'
        target = inside(directory / (digest(body) + suffix), run_dir)
        _publish_immutable(target, body, conflict_reason='Downloaded source bytes changed')
        outcome = {'status': 'downloaded-unverified', 'final_url': _public_location(response['url']),
                   'path': str(target.relative_to(run_dir)), 'sha256': digest(body),
                   'bytes': len(body), 'content_type': content_type, 'attempts': response.get('attempts', [])}
        entry = {'path': str(target), 'role': role, 'expected_sha256': digest(body)}
        if association_reason:
            entry['association_reason'] = association_reason
    except SourceError as exc:
        outcome = {'status': exc.status, 'failure_reason': exc.reason,
                   'attempts': exc.attempts, 'retry_after': exc.retry_after}
    except ValueError:
        # Redirect/transport safety rejection: do not persist a potentially
        # credential-bearing exception message or misrepresent source identity.
        outcome = {'status': 'blocked', 'failure_reason': 'Source URL or immutable download safety check failed', 'attempts': []}
    for attempt in outcome['attempts']:
        if attempt.get('url'):
            attempt['url'] = _public_location(attempt['url'])
    receipt = dict(requested, **outcome, completed_at=now())
    receipt_path = prefix.with_suffix('.receipt.json')
    _publish_immutable(receipt_path, (canonical(receipt) + '\n').encode(), conflict_reason='Download receipt changed')
    coordinator.store.event('source_download_completed', dict(receipt,
        receipt_path=str(receipt_path.relative_to(run_dir))))
    return {'status': receipt['status'], 'receipt_path': str(receipt_path.relative_to(run_dir)),
            'source_entry': entry, 'reason': 'Verify article/version identity, then attach the complete main/SI manifest with source; download alone is not verified evidence.'}
