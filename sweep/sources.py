"""Public bibliographic adapters and source-preserving full-text acquisition.

Every search returns one immutable page/window, never a relevance decision.
Citation callers enqueue ``next_cursor`` until ``exhausted``. Transient service
failures remain deferred; neither a failed request nor missing text is a zero
result or scientific exclusion. Network transport is injectable for offline QA.
"""
from __future__ import annotations

import datetime as dt
import contextlib
import contextvars
import email.utils
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import re
import shutil
import signal
import socket
import subprocess
import tempfile
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from typing import Any


OPENALEX = "https://api.openalex.org"
EPMC = "https://www.ebi.ac.uk/europepmc/webservices/rest"
CROSSREF = "https://api.crossref.org"
_SEARCH_RESPONSES = contextvars.ContextVar("sweep_source_responses", default=None)


def canonical_bytes(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=False,
                       separators=(",", ":"), allow_nan=False) + "\n").encode()


def digest(value):
    return hashlib.sha256(value if isinstance(value, bytes) else canonical_bytes(value)).hexdigest()


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def normalize_doi(value):
    value = urllib.parse.unquote(str(value or "")).strip().lower()
    return re.sub(r"^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)", "", value)


def normalize_title(value):
    return " ".join(re.sub(r"[^\w\s]", " ", unicodedata.normalize("NFKC", str(value or "")).casefold()).split())


def safe_url(url, *, resolve=True):
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("Only public HTTP(S) URLs without embedded credentials are allowed")
    if parsed.port not in {None, 80, 443}:
        raise ValueError("Nonstandard network ports require an explicit separate adapter")
    if parsed.hostname.casefold() == "localhost" or parsed.hostname.casefold().endswith(".localhost"):
        raise ValueError("Loopback source URL is not public")
    try:
        addresses = [ipaddress.ip_address(parsed.hostname)]
    except ValueError:
        addresses = [ipaddress.ip_address(x[4][0]) for x in socket.getaddrinfo(parsed.hostname, parsed.port or 443)] if resolve else []
    if any(not address.is_global for address in addresses):
        raise ValueError("Private, reserved or local source URL is not public")
    return url


class SourceError(RuntimeError):
    def __init__(self, status, reason, *, attempts=(), retry_after=None):
        super().__init__(reason)
        self.status, self.reason = status, reason
        self.attempts, self.retry_after = list(attempts), retry_after


class _Redirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        safe_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def public_transport(url, *, timeout, headers, max_bytes=64 * 1024 * 1024):
    safe_url(url)
    request = urllib.request.Request(url, headers=headers)
    opener = urllib.request.build_opener(_Redirect())
    try:
        with opener.open(request, timeout=timeout) as response:
            length = response.headers.get("Content-Length")
            if length and length.isdigit() and int(length) > max_bytes:
                raise SourceError("deferred", "Source exceeds operational download byte limit; increase authorized resources or supply a local file")
            body = response.read(max_bytes + 1)
            if len(body) > max_bytes:
                raise SourceError("deferred", "Source exceeds operational download byte limit; no truncated source accepted")
            return {"status": response.status, "headers": dict(response.headers),
                    "body": body, "url": response.url}
    except urllib.error.HTTPError as exc:
        return {"status": exc.code, "headers": dict(exc.headers), "body": exc.read(max_bytes + 1), "url": url}


def _retry_after(headers):
    value = next((v for k, v in headers.items() if k.lower() == "retry-after"), None)
    if value is None:
        return None
    try:
        return max(0, float(value))
    except ValueError:
        try:
            return max(0, (email.utils.parsedate_to_datetime(value) - dt.datetime.now(dt.timezone.utc)).total_seconds())
        except (ValueError, TypeError):
            return None


class SourceClient:
    def __init__(self, transport=None, *, timeout=30, max_attempts=3, sleep=time.sleep,
                 openalex_key_env="OPENALEX_API_KEY", max_download_bytes=64 * 1024 * 1024):
        if timeout <= 0 or not 1 <= max_attempts <= 3:
            raise ValueError("Positive timeout and one to three attempts required")
        self.transport = transport or public_transport
        self.timeout, self.max_attempts, self.sleep = timeout, max_attempts, sleep
        # Store only the environment variable name. Never persist credentials.
        self.openalex_key_env = openalex_key_env
        if not isinstance(max_download_bytes, int) or max_download_bytes < 1:
            raise ValueError("Positive operational download byte limit required")
        self.max_download_bytes = max_download_bytes

    def get(self, url, *, json_response=False):
        safe_url(url, resolve=False)
        attempts = []
        for number in range(self.max_attempts):
            retry = None
            try:
                request_url = url
                if urllib.parse.urlsplit(url).hostname == "api.openalex.org" and self.openalex_key_env:
                    key = os.environ.get(self.openalex_key_env)
                    if key:
                        request_url += ("&" if "?" in url else "?") + urllib.parse.urlencode({"api_key": key})
                response = self.transport(request_url, timeout=self.timeout, max_bytes=self.max_download_bytes, headers={
                    "User-Agent": "consciousness-sweep/1.0 (public scholarly metadata)",
                    "Accept": "application/json" if json_response else "application/xml,application/pdf,text/plain;q=0.8,*/*;q=0.1"})
                code = response["status"]
                body = response["body"]
                if isinstance(body, str):
                    body = body.encode()
                if len(body) > self.max_download_bytes:
                    raise SourceError("deferred", "Source exceeds operational byte allowance; no truncated evidence accepted", attempts=attempts)
                attempts.append({"url": url, "at": now(), "attempt": number + 1,
                                 "http_status": code, "body_sha256": digest(body)})
                if 200 <= code < 300:
                    if json_response:
                        try:
                            data = json.loads(body)
                        except (ValueError, UnicodeDecodeError) as exc:
                            raise SourceError("incomplete", "Malformed JSON response", attempts=attempts) from exc
                    else:
                        data = body
                    resolved = urllib.parse.urlsplit(response.get("url", url))
                    clean_query = urllib.parse.urlencode([(k, v) for k, v in urllib.parse.parse_qsl(resolved.query)
                                                         if k.lower() not in {"api_key", "apikey", "token", "key"}])
                    clean_url = urllib.parse.urlunsplit(resolved._replace(query=clean_query))
                    return data, {"url": clean_url, "headers": response.get("headers", {}),
                                  "body_sha256": digest(body), "attempts": attempts, "raw_body": body}
                if code not in {408, 425, 429, 500, 502, 503, 504}:
                    status = "unavailable" if code in {404, 410} else "blocked"
                    raise SourceError(status, "HTTP {} requires access/query/coverage resolution".format(code), attempts=attempts)
                retry = _retry_after(response.get("headers", {}))
            except (urllib.error.URLError, TimeoutError, OSError) as exc:
                attempts.append({"url": url, "at": now(), "attempt": number + 1,
                                 "error": type(exc).__name__, "reason": "Network/timeout failure; credentials omitted"})
            delay = retry if retry is not None else (5 if number == 0 else 20)
            if number + 1 == self.max_attempts or delay > 20:
                raise SourceError("deferred", "Transient source failure; retain obligation for continuation",
                                  attempts=attempts, retry_after=delay)
            self.sleep(delay)
        raise AssertionError("unreachable")

    def search(self, source, query="", limit=40, cursor=None, *, kind="query", parent=None):
        """Return one ordered page. Query windows never acquire a second page.

        Citation source exhaustion is independent of resource budgets. A cursor
        is an opaque service cursor (or offset for deposited reference lists).
        """
        if not isinstance(limit, int) or limit < 1 or limit > 100:
            raise ValueError("Page/window size must be between 1 and 100")
        if kind == "query" and cursor is not None:
            raise ValueError("Frozen bounded query windows have no second page")
        request = {"source": source, "query": query, "limit": limit, "cursor": cursor,
                   "kind": kind, "parent": parent, "publication_cutoff": None}
        captured = []
        token = _SEARCH_RESPONSES.set(captured)
        try:
            if source == "OpenAlex":
                records, nxt, exhausted, raw = self._openalex(query, limit, cursor, kind, parent)
            elif source in {"Europe PMC", "EuropePMC"}:
                records, nxt, exhausted, raw = self._epmc(query, limit, cursor, kind, parent)
            elif source == "Crossref":
                records, nxt, exhausted, raw = self._crossref(query, limit, cursor, kind, parent)
            else:
                raise ValueError("Unsupported source " + source)
            result = {"status": "complete", "request": request, "retrieved_at": now(),
                      "results": records, "next_cursor": nxt, "exhausted": exhausted,
                      "raw_responses": raw, "reason": "Completed source page/window in returned order"}
            if kind in {"forward", "backward"}:
                if source == "OpenAlex" and kind == "backward":
                    result["reported_total"] = len(raw[0]["response"]["referenced_works"])
                elif source == "OpenAlex":
                    result["reported_total"] = raw[-1]["response"]["meta"]["count"]
                elif source in {"Europe PMC", "EuropePMC"}:
                    result["reported_total"] = raw[-1]["response"]["hitCount"]
                elif source == "Crossref":
                    result["reported_total"] = len(raw[0]["response"]["message"]["reference"])
            result["result_set_sha256"] = digest(records)
            result["request_sha256"] = digest(request)
            return result
        except SourceError as exc:
            return {"status": exc.status, "request": request, "retrieved_at": now(),
                    "results": [], "next_cursor": cursor, "exhausted": False,
                    "attempts": exc.attempts, "raw_responses": captured,
                    "retry_after": exc.retry_after, "reason": exc.reason}
        finally:
            _SEARCH_RESPONSES.reset(token)

    def _json(self, url):
        data, receipt = self.get(url, json_response=True)
        clean = {k: v for k, v in receipt.items() if k != "raw_body"} | {"response": data, "response_json_sha256": digest(data)}
        captured = _SEARCH_RESPONSES.get()
        if captured is not None:
            captured.append(clean)
        return data, clean

    def _openalex_parent(self, parent):
        if not parent:
            raise SourceError("unavailable", "Citation parent identity is missing")
        identifier = parent.get("openalex_id") or parent.get("source_stable_id")
        if not identifier or not re.search(r"(?:^|/)W\d+$", identifier):
            doi = normalize_doi(parent.get("doi"))
            if not doi:
                raise SourceError("unavailable", "OpenAlex citation parent needs a known work ID or DOI")
            identifier = "https://doi.org/" + doi
        data, raw = self._json(OPENALEX + "/works/" + urllib.parse.quote(identifier, safe=""))
        if not isinstance(data, dict) or not data.get("id"):
            raise SourceError("incomplete", "OpenAlex parent response lacks identity")
        expected = normalize_doi(parent.get("doi"))
        if expected and normalize_doi(data.get("doi")) != expected:
            raise SourceError("unavailable", "OpenAlex parent DOI identity is not corroborated")
        return data, raw

    def _openalex(self, query, limit, cursor, kind, parent):
        raw = []
        if kind in {"backward", "forward"}:
            data, receipt = self._openalex_parent(parent)
            raw.append(receipt)
            if kind == "backward":
                if "referenced_works" not in data or not isinstance(data["referenced_works"], list):
                    raise SourceError("incomplete", "OpenAlex reference coverage absent")
                offset = int(cursor or 0)
                ids = data["referenced_works"]
                wanted = ids[offset:offset + limit]
                records = []
                # Preserve source reference-list order even if API list order differs.
                for start in range(0, len(wanted), 50):
                    chunk = wanted[start:start + 50]
                    params = {"filter": "openalex_id:" + "|".join(i.rsplit("/", 1)[-1] for i in chunk), "per_page": len(chunk)}
                    found, receipt = self._json(OPENALEX + "/works?" + urllib.parse.urlencode(params))
                    raw.append(receipt)
                    if not isinstance(found.get("results"), list):
                        raise SourceError("incomplete", "OpenAlex reference identities unresolved")
                    by_id = {r.get("id"): r for r in found["results"]}
                    if any(identifier not in by_id for identifier in chunk):
                        raise SourceError("incomplete", "OpenAlex omitted a referenced work; retain page for identity resolution")
                    records.extend(normalize_openalex(by_id[identifier]) for identifier in chunk)
                nxt = str(offset + len(wanted)) if offset + len(wanted) < len(ids) else None
                return records, nxt, nxt is None, raw
            params = {"filter": "cites:" + data["id"].rsplit("/", 1)[-1], "per_page": limit, "cursor": cursor or "*"}
        elif kind == "query":
            if not query.startswith("filter="):
                raise ValueError("OpenAlex frozen query must preserve the filter= form")
            params = {"filter": query[len("filter="):], "sort": "relevance_score:desc", "per_page": limit, "page": 1}
        elif kind == "identity":
            data, receipt = self._openalex_parent(parent or {"doi": query})
            return [normalize_openalex(data)], None, True, [receipt]
        else:
            raise ValueError("Unsupported OpenAlex operation")
        data, receipt = self._json(OPENALEX + "/works?" + urllib.parse.urlencode(params))
        raw.append(receipt)
        if not isinstance(data.get("results"), list) or not isinstance(data.get("meta", {}).get("count"), int):
            raise SourceError("incomplete", "OpenAlex response is missing results/count")
        records = [normalize_openalex(r) for r in data["results"]]
        nxt = data["meta"].get("next_cursor") if kind != "query" else None
        if kind != "query" and nxt == (cursor or "*"):
            raise SourceError("incomplete", "OpenAlex cursor did not advance")
        if kind != "query" and not records and nxt:
            raise SourceError("incomplete", "OpenAlex empty page advertises continuation")
        return records, nxt, nxt is None, raw

    def _epmc_parent(self, parent):
        if not parent:
            raise SourceError("unavailable", "Europe PMC citation parent is missing")
        if parent.get("epmc_id") and parent.get("epmc_source"):
            return parent["epmc_source"], parent["epmc_id"], []
        doi = normalize_doi(parent.get("doi"))
        pmcid = parent.get("pmcid")
        query = 'DOI:"{}"'.format(doi) if doi else "EXT_ID:" + str(pmcid) if pmcid else None
        if not query:
            raise SourceError("unavailable", "Europe PMC citation parent has no resolvable identity")
        data, raw = self._json(EPMC + "/search?" + urllib.parse.urlencode({"query": query, "format": "json", "resultType": "core"}))
        rows = data.get("resultList", {}).get("result", [])
        matching = [r for r in rows if (doi and normalize_doi(r.get("doi")) == doi) or (pmcid and r.get("pmcid") == pmcid)]
        if len(matching) != 1:
            raise SourceError("unavailable", "Europe PMC parent identity/coverage unavailable")
        return matching[0]["source"], matching[0]["id"], [raw]

    def _epmc(self, query, limit, cursor, kind, parent):
        if kind in {"forward", "backward"}:
            source, identifier, raw = self._epmc_parent(parent)
            page = int(cursor or 1)
            route, list_key, item_key = (("references", "referenceList", "reference") if kind == "backward" else ("citations", "citationList", "citation"))
            url = EPMC + "/{}/{}/{}?".format(urllib.parse.quote(source, safe=""), urllib.parse.quote(identifier, safe=""), route)
            data, receipt = self._json(url + urllib.parse.urlencode({"format": "json", "page": page, "pageSize": limit}))
            raw.append(receipt)
            count = data.get("hitCount")
            rows = data.get(list_key, {}).get(item_key)
            if not isinstance(count, int) or (rows is None and count):
                raise SourceError("incomplete", "Europe PMC citation response lacks count/records")
            rows = rows or []
            if not isinstance(rows, list) or (not rows and (page - 1) * limit < count):
                raise SourceError("incomplete", "Europe PMC citation pagination is inconsistent")
            nxt = str(page + 1) if page * limit < count else None
            return [normalize_epmc(r) for r in rows], nxt, nxt is None, raw
        if kind not in {"query", "identity"}:
            raise ValueError("Unsupported Europe PMC operation")
        if kind == "identity":
            query = 'DOI:"{}"'.format(normalize_doi(query))
        params = {"query": query, "format": "json", "resultType": "core", "pageSize": limit,
                  "cursorMark": "*", "synonym": "false"}
        data, raw = self._json(EPMC + "/search?" + urllib.parse.urlencode(params))
        if not isinstance(data.get("hitCount"), int) or not isinstance(data.get("resultList", {}).get("result"), list):
            raise SourceError("incomplete", "Europe PMC response lacks results/count")
        return [normalize_epmc(r) for r in data["resultList"]["result"]], None, True, [raw]

    def _crossref(self, query, limit, cursor, kind, parent):
        if kind not in {"identity", "backward"}:
            raise ValueError("Crossref is an identity/backward-reference fallback only")
        doi = normalize_doi((parent or {}).get("doi") or query)
        if not doi:
            raise SourceError("unavailable", "Crossref needs a known parent DOI")
        data, raw = self._json(CROSSREF + "/works/" + urllib.parse.quote(doi, safe=""))
        record = data.get("message", {})
        if normalize_doi(record.get("DOI")) != doi:
            raise SourceError("unavailable", "Crossref parent DOI mismatch")
        if kind == "identity":
            return [normalize_crossref(record)], None, True, [raw]
        if not isinstance(record.get("reference"), list):
            raise SourceError("unavailable", "Publisher has not deposited a Crossref reference list")
        offset = int(cursor or 0)
        rows = record["reference"][offset:offset + limit]
        records = [normalize_crossref(r, reference=True) for r in rows]
        nxt = str(offset + len(rows)) if offset + len(rows) < len(record["reference"]) else None
        return records, nxt, nxt is None, [raw]


def normalize_openalex(row):
    inverse = row.get("abstract_inverted_index")
    abstract = None
    if isinstance(inverse, dict):
        words = [(position, word) for word, positions in inverse.items() for position in positions]
        abstract = " ".join(word for _, word in sorted(words))
    locations = [row.get("best_oa_location") or {}] + list(row.get("locations") or [])
    urls = list(dict.fromkeys(loc.get("pdf_url") or loc.get("landing_page_url") for loc in locations if loc.get("pdf_url") or loc.get("landing_page_url")))
    return {"source": "OpenAlex", "source_stable_id": row.get("id"), "openalex_id": row.get("id"),
            "doi": normalize_doi(row.get("doi")), "title": row.get("title") or row.get("display_name") or "",
            "authors": [a.get("author", {}).get("display_name", "") for a in row.get("authorships", [])],
            "year": row.get("publication_year"), "abstract": abstract, "fulltext_urls": urls,
            "url": row.get("id"), "referenced_works": row.get("referenced_works")}


def normalize_epmc(row):
    authors = row.get("authorList", {}).get("author", [])
    fulltexts = row.get("fullTextUrlList", {}).get("fullTextUrl", [])
    return {"source": "Europe PMC", "source_stable_id": str(row.get("source", "")) + ":" + str(row.get("id", "")),
            "epmc_source": row.get("source"), "epmc_id": row.get("id"), "pmcid": row.get("pmcid"),
            "doi": normalize_doi(row.get("doi")), "title": row.get("title") or "",
            "authors": [a.get("fullName", "") for a in authors] or row.get("authorString", ""),
            "year": row.get("pubYear"), "abstract": row.get("abstractText"),
            "fulltext_urls": [u["url"] for u in fulltexts if u.get("url") and u.get("availability") in {"Open access", "Free"}],
            "url": "https://europepmc.org/article/{}/{}".format(row.get("source", "MED"), row.get("id", ""))}


def normalize_crossref(row, reference=False):
    title = row.get("article-title") if reference else row.get("title")
    if isinstance(title, list):
        title = title[0] if title else ""
    issued = row.get("issued", {}).get("date-parts", [[]])[0]
    doi = normalize_doi(row.get("DOI"))
    return {"source": "Crossref", "source_stable_id": doi or row.get("key"), "doi": doi,
            "title": title or "", "authors": row.get("author") or [],
            "year": row.get("year") if reference else issued[0] if issued else None,
            "abstract": row.get("abstract"), "fulltext_urls": [], "unstructured_reference": row.get("unstructured"),
            "identity_resolution_required": reference and not bool(doi or title),
            "url": "https://doi.org/" + urllib.parse.quote(doi, safe="/") if doi else None}


def save_snapshot(path, snapshot):
    """Exclusive creation: a completed retrieval snapshot cannot be overwritten."""
    if snapshot.get("status") != "complete" or snapshot.get("result_set_sha256") != digest(snapshot.get("results")):
        raise ValueError("Only internally consistent complete snapshots may be frozen")
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    value = canonical_bytes(snapshot)
    if path.exists():
        old = load_snapshot(path)
        if old != snapshot:
            raise ValueError("Immutable completed snapshot differs; do not rerun/replace it")
        return old
    with path.open("xb") as handle:
        handle.write(value)
        handle.flush()
        os.fsync(handle.fileno())
    return snapshot


def load_snapshot(path):
    value = json.loads(Path(path).read_text())
    if value.get("status") != "complete" or value.get("result_set_sha256") != digest(value.get("results")) or value.get("request_sha256") != digest(value.get("request")):
        raise ValueError("Snapshot identity/result hash mismatch")
    if any(r.get("response_json_sha256") != digest(r.get("response")) for r in value.get("raw_responses", [])):
        raise ValueError("Snapshot raw response hash mismatch")
    return value


def _local_tag(element):
    return element.tag.rsplit("}", 1)[-1]


def _text(element):
    return " ".join(" ".join(element.itertext()).split())


def _run_extraction_process(argv, timeout, max_output_bytes=64 * 1024 * 1024):
    """Bound extraction without forking a process containing worker threads.

    Python 3.9's subprocess fast path is conditional: capture_output plus its
    default close_fds can otherwise fork on macOS. Use posix_spawn explicitly.
    Output goes to temporary files to avoid pipe deadlocks; oversized output is
    rejected in full, never returned as a silently shortened source.
    """
    executable = str(Path(shutil.which(argv[0]) or argv[0]).resolve())
    argv = [executable] + list(argv[1:])
    with tempfile.TemporaryFile() as out, tempfile.TemporaryFile() as err, open(os.devnull, "rb") as inp:
        if os.name == "posix":
            if not hasattr(os, "posix_spawn"):
                raise ValueError("Safe PDF extraction requires posix_spawn on this host")
            pid = os.posix_spawn(executable, argv, dict(os.environ), setpgroup=0, file_actions=[
                (os.POSIX_SPAWN_DUP2, inp.fileno(), 0),
                (os.POSIX_SPAWN_DUP2, out.fileno(), 1),
                (os.POSIX_SPAWN_DUP2, err.fileno(), 2)])
            child = None
        else:
            child = subprocess.Popen(argv, stdin=inp, stdout=out, stderr=err)
            pid = child.pid
        started = time.monotonic()
        reaped = False
        try:
            while True:
                if child is None:
                    finished, status = os.waitpid(pid, os.WNOHANG)
                    code = os.waitstatus_to_exitcode(status) if finished else None
                else:
                    code = child.poll()
                    finished = code is not None
                reaped = bool(finished)
                if os.fstat(out.fileno()).st_size + os.fstat(err.fileno()).st_size > max_output_bytes:
                    raise ValueError("Extraction output exceeds the operational byte limit; no truncated source was accepted")
                if finished:
                    out.seek(0)
                    err.seek(0)
                    return subprocess.CompletedProcess(argv, code, out.read(), err.read())
                if time.monotonic() - started >= timeout:
                    raise subprocess.TimeoutExpired(argv, timeout)
                time.sleep(min(0.05, timeout / 10))
        finally:
            if not reaped:
                if child is None:
                    with contextlib.suppress(ProcessLookupError):
                        os.killpg(pid, signal.SIGKILL)
                    with contextlib.suppress(ChildProcessError):
                        os.waitpid(pid, 0)
                else:
                    child.kill()
                    child.wait()


def _extract(data, suffix):
    if data.lstrip().startswith(b"%PDF") or suffix.lower() == ".pdf":
        tool = shutil.which("pdftotext")
        if tool:
            with tempfile.TemporaryDirectory(prefix="sweep-extract-") as directory:
                file = Path(directory) / "article.pdf"
                file.write_bytes(data)
                done = _run_extraction_process([tool, "-layout", str(file), "-"], timeout=120)
                if done.returncode:
                    raise ValueError("pdftotext could not extract this source")
                pages = done.stdout.decode("utf-8", errors="replace").split("\f")
                if pages and not pages[-1].strip():
                    pages.pop()
            try:
                probe = _run_extraction_process([tool, "-v"], timeout=10, max_output_bytes=65536)
                lines = (probe.stderr or probe.stdout).decode(errors="replace").strip().splitlines()
                version = lines[0] if lines and probe.returncode == 0 else "version unavailable"
            except (OSError, ValueError, subprocess.SubprocessError):
                version = "version unavailable"
        else:
            try:
                import io
                import pypdf
            except ImportError as exc:
                raise ValueError("PDF extraction requires pdftotext or pypdf; install the declared optional dependency") from exc
            reader = pypdf.PdfReader(io.BytesIO(data))
            pages = [page.extract_text() or "" for page in reader.pages]
            version = "pypdf " + pypdf.__version__
        units = [{"unit_id": "page:{}".format(i + 1), "content": page} for i, page in enumerate(pages)]
        return units, {"tool": "pdftotext" if tool else "pypdf", "version": version}, {}, []
    if suffix.lower() in {".xml", ".nxml"} or data.lstrip().startswith((b"<?xml", b"<article")):
        root = ET.fromstring(data)
        if _local_tag(root) != "article":
            raise ValueError("XML is not an article full text")
        if not any(_local_tag(node) == "body" and _text(node).strip() for node in root):
            raise ValueError("Article XML contains no readable main body; metadata/abstract alone is not full text")
        front = next((node for node in root if _local_tag(node) == "front"), None)
        identity = {}
        if front is not None:
            for node in front.iter():
                if _local_tag(node) == "article-id" and node.get("pub-id-type") == "doi":
                    identity["doi"] = normalize_doi(_text(node))
                if _local_tag(node) == "article-title" and "title" not in identity:
                    identity["title"] = _text(node)
        # Whole direct components preserve every paragraph, table caption,
        # reference and back matter once; IDs remain stable across repeated reads.
        units = [{"unit_id": "section:{}:{}".format(i + 1, _local_tag(node)), "content": _text(node)}
                 for i, node in enumerate(root)]
        supplements = []
        for node in root.iter():
            if _local_tag(node) == "supplementary-material":
                links = [v for child in node.iter() for key, v in child.attrib.items() if key.rsplit("}", 1)[-1] == "href"]
                supplements.extend({"href": href, "description": _text(node)} for href in links)
                if not links:
                    supplements.append({"href": None, "description": _text(node)})
        return units, {"tool": "stdlib ElementTree full-component extraction", "version": "1"}, identity, supplements
    if suffix.lower() in {".txt", ".text"}:
        content = data.decode("utf-8")
        return [{"unit_id": "text:1", "content": content}], {"tool": "UTF-8 text", "version": "1"}, {}, []
    raise ValueError("Source is not a supported PDF, article XML or UTF-8 text; HTML/archives need explicit acquisition")


def _identity(paper, units, extracted):
    expected = normalize_doi(paper.get("doi"))
    encoded = normalize_doi(extracted.get("doi"))
    title = normalize_title(paper.get("title"))
    supplied_title = normalize_title(extracted.get("title"))
    if title and supplied_title and title != supplied_title:
        return "unclear", "Explicit article front-matter title conflicts with the requested title; resolve identity/version before use"
    if expected and encoded:
        return ("match", "Article front-matter DOI matches") if expected == encoded else ("mismatch", "Article front-matter DOI differs from requested work")
    first = "\n".join(u["content"] for u in units[:2])
    text = normalize_title(first)
    title_matches = bool(title) and (title == supplied_title or title in text)
    if title_matches and expected and re.search(r"(?<![\w/])" + re.escape(expected) + r"(?![\w/])", first, re.I):
        return "match", "Requested DOI plus title are present in the first source units"
    authors = paper.get("authors") or []
    if isinstance(authors, str):
        authors = [authors]
    names = [normalize_title(a if isinstance(a, str) else a.get("family", "")) for a in authors]
    surname_match = any(name and name.split()[-1] in text.split() for name in names)
    year_match = bool(paper.get("year")) and str(paper["year"]) in first
    if title_matches and (surname_match or year_match):
        return "match", "Title plus encoded author/year corroborates source identity"
    return "unclear", "Insufficient bibliographic corroboration; source identity requires resolution"


def _asset(paper, data, label, directory, *, role="article", association=None):
    sha = digest(data)
    directory.mkdir(parents=True, exist_ok=True)
    extraction_cache = directory / (sha + ".extraction.json")
    if extraction_cache.exists():
        cached = json.loads(extraction_cache.read_text())
        payload = cached["payload"]
        if cached.get("sha256") != digest(payload) or payload.get("source_sha256") != sha:
            raise ValueError("Cached extraction integrity mismatch")
        units, extraction, identity, supplements = (payload[k] for k in ("units", "extraction", "identity", "supplements"))
    else:
        units, extraction, identity, supplements = _extract(data, Path(urllib.parse.urlsplit(label).path).suffix)
        payload = {"units": units, "extraction": extraction, "identity": identity,
                   "supplements": supplements, "source_sha256": sha}
        extraction_cache.write_bytes(canonical_bytes({"payload": payload, "sha256": digest(payload)}))
    if not units or not any(u["content"].strip() for u in units):
        raise ValueError("Extraction contains no readable source text; OCR/manual source required")
    status, reason = _identity(paper, units, identity)
    if role == "supplement" and association:
        status, reason = "match", association
    asset_id = "asset-" + sha[:20]
    content = "\n\n".join("[{}]\n{}".format(u["unit_id"], u["content"]) for u in units)
    mapping = [{"unit_id": u["unit_id"], "characters": len(u["content"]), "sha256": digest(u["content"].encode())} for u in units]
    directory.mkdir(parents=True, exist_ok=True)
    suffix = ".pdf" if data.lstrip().startswith(b"%PDF") else ".xml" if extraction["tool"].startswith("stdlib") else ".txt"
    paths = {"original_path": directory / (sha + suffix), "text_path": directory / (sha + ".extracted.txt"),
             "map_path": directory / (sha + ".map.json")}
    for key, payload in [("original_path", data), ("text_path", content.encode()), ("map_path", canonical_bytes(mapping))]:
        if paths[key].exists() and paths[key].read_bytes() != payload:
            raise ValueError("Immutable cached source/extraction changed")
        if not paths[key].exists():
            paths[key].write_bytes(payload)
    asset = {"asset_id": asset_id, "source": label, "kind": "main" if role == "article" else "additional",
             "source_role": role, "identity": {"status": status, "reason": reason, **identity},
             "sha256": sha, "text_sha256": digest(content.encode()), "map_sha256": digest(mapping),
             "content_sha256": digest(content.encode()), "units": mapping, "content": content,
             "extraction": extraction, **{k: str(v) for k, v in paths.items()},
             "limits": "Extracted text; graphical pixels and unprovided supplements are not supplied."}
    return asset, supplements


def _provided_bytes(entry):
    data = Path(entry["path"]).read_bytes()
    expected = entry.get("expected_sha256")
    if expected is not None and (not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{64}", expected) or digest(data) != expected):
        raise SourceError("identity-unresolved", "Supplied immutable source hash mismatch; repair the input explicitly before reading")
    return data


def retrieve(paper, output_dir, provided_paths=(), *, client=None):
    """Acquire a verified main source plus explicitly associated supplements.

    Supplied entries may be paths or {path, role:'supplement', association_reason}.
    Source claims of complete reading never imply that unavailable graphics or
    unprovided supplements were examined. All extraction content is retained.
    """
    client = client or SourceClient()
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    attempts, assets, gaps, candidates = [], [], [], []
    supplied_supplements = []
    if not provided_paths:
        provided_paths = paper.get("provided_paths") or []
    for item in provided_paths:
        entry = {"path": str(item)} if isinstance(item, (str, Path)) else dict(item)
        (supplied_supplements if entry.get("role") == "supplement" else candidates).append(entry)
    pmcid = paper.get("pmcid")
    # User-supplied sources are attempted without unnecessary remote calls.
    # Metadata discovery is useful only when no explicit local source exists.
    local_available = any(c.get("path") for c in candidates) or any(paper.get(k) for k in ("fulltext_path", "pdf_path", "local_path"))
    if not pmcid and paper.get("doi") and not local_available:
        found = client.search("Europe PMC", normalize_doi(paper["doi"]), 10, kind="identity")
        attempts.append({"kind": "identity-discovery", "status": found["status"], "reason": found["reason"],
                         "attempts": found.get("attempts", []), "raw_responses": found.get("raw_responses", [])})
        matched = [r for r in found.get("results", []) if r.get("doi") == normalize_doi(paper["doi"])]
        if len(matched) == 1:
            pmcid = matched[0].get("pmcid")
            candidates.extend({"url": u} for u in matched[0].get("fulltext_urls", []))
    if pmcid:
        if not re.fullmatch(r"PMC\d+", str(pmcid)):
            raise ValueError("Invalid PMCID")
        candidates.insert(len(provided_paths), {"url": EPMC + "/" + pmcid + "/fullTextXML"})
    candidates.extend({"url": url} for url in paper.get("fulltext_urls", []) if url)
    extra_urls = paper.get("urls") or []
    if isinstance(extra_urls, str):
        extra_urls = [extra_urls]
    candidates.extend({"url": u} for u in extra_urls if isinstance(u, str))
    for key in ("fulltext_path", "pdf_path", "local_path"):
        if paper.get(key):
            candidates.insert(0, {"path": paper[key]})
    if paper.get("fulltext_url"):
        candidates.append({"url": paper["fulltext_url"]})
    if paper.get("pdf_url"):
        candidates.append({"url": paper["pdf_url"]})
    if paper.get("open_access_url"):
        candidates.append({"url": paper["open_access_url"]})
    if not candidates and paper.get("doi"):
        found = client.search("OpenAlex", normalize_doi(paper["doi"]), 1, kind="identity")
        attempts.append({"kind": "identity-discovery", "source": "OpenAlex", "status": found["status"],
                         "reason": found["reason"], "raw_responses": found.get("raw_responses", [])})
        for record in found.get("results", []):
            candidates.extend({"url": u} for u in record.get("fulltext_urls", []))
    unresolved = []
    supplemental_links = []
    seen = set()
    for candidate in candidates:
        label = candidate.get("path") or candidate.get("url")
        if not label or label in seen:
            continue
        seen.add(label)
        try:
            if candidate.get("path"):
                data = _provided_bytes(candidate)
                receipt = {"route": "provided-file", "path": label, "at": now()}
            else:
                data, raw = client.get(label)
                receipt = {k: v for k, v in raw.items() if k != "raw_body"}
            asset, supplemental_links = _asset(paper, data, label, directory)
            attempts.append({"source": label, "status": asset["identity"]["status"], "receipt": receipt,
                             "reason": asset["identity"]["reason"]})
            if asset["identity"]["status"] == "match":
                assets.append(asset)
                break
            unresolved.append(asset)
        except SourceError as exc:
            attempts.append({"source": label, "status": exc.status, "reason": exc.reason,
                             "attempts": exc.attempts, "retry_after": exc.retry_after})
        except (OSError, ValueError, ET.ParseError, subprocess.SubprocessError) as exc:
            attempts.append({"source": label, "status": "unreadable", "reason": str(exc)})
    if not assets:
        status = "identity-unresolved" if unresolved or any(a["status"] == "identity-unresolved" for a in attempts) else "deferred" if any(a["status"] == "deferred" for a in attempts) else "missing"
        return {"status": status, "packet": None, "assets": unresolved, "attempts": attempts,
                "gaps": ["No verified readable main article"], "reason": "No source has yet passed identity and extraction verification"}
    for link in supplemental_links:
        href = link.get("href")
        if href and urllib.parse.urlsplit(href).scheme in {"http", "https"}:
            supplied_supplements.append({"url": href, "association_reason": "Explicit supplementary-material link in verified main article"})
        else:
            gaps.append("Supplement requires acquisition/association: " + str(href or link.get("description") or "unnamed supplement"))
    for supplement in supplied_supplements:
        label = supplement.get("path") or supplement.get("url")
        try:
            if not supplement.get("association_reason"):
                raise ValueError("Supplied supplemental source needs an explicit association reason")
            data = _provided_bytes(supplement) if supplement.get("path") else client.get(label)[0]
            asset, _ = _asset(paper, data, label, directory, role="supplement", association=supplement["association_reason"])
            if asset["asset_id"] not in {a["asset_id"] for a in assets}:
                assets.append(asset)
            attempts.append({"source": label, "status": "match", "reason": asset["identity"]["reason"]})
        except (SourceError, OSError, ValueError, ET.ParseError, subprocess.SubprocessError) as exc:
            gaps.append("Supplement unavailable: {} ({})".format(label, exc))
            attempts.append({"source": label, "status": getattr(exc, "status", "unreadable"), "reason": str(exc)})
    attempted_sources = {a.get("source") for a in attempts}
    for item in provided_paths:
        entry = {"path": str(item)} if isinstance(item, (str, Path)) else item
        if entry.get("path") not in attempted_sources and entry.get("role") != "supplement":
            gaps.append("Additional supplied file was not read; identify its source role/association before use: " + str(entry.get("path")))
    gaps.append("Graphical source pixels have not been supplied; extracted text may omit figure-only evidence.")
    if not supplemental_links and not supplied_supplements:
        gaps.append("Supplement inventory has not been independently verified; absence of attached supplements is not evidence none exist.")
    packet = {"paper": {k: paper.get(k) for k in ("paper_id", "title", "authors", "year", "doi")},
              "sources": [{k: v for k, v in a.items() if k not in {"original_path", "text_path", "map_path"}} for a in assets],
              "acquisition_gaps": gaps}
    return {"status": "verified", "packet": packet, "assets": assets, "attempts": attempts, "gaps": gaps,
            "reason": "Main identity verified; source-located extraction retained with explicit acquisition limits"}
