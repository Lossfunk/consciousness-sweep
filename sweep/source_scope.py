"""Operational acquisition scope; never a paper-level scientific exclusion."""
from pathlib import PurePosixPath
import re
from urllib.parse import parse_qsl, unquote, urlsplit

NAME = "article-and-supplementary-text-v1"
MATERIAL_KINDS = {"article-text", "supplementary-text", "code", "dataset", "software-output", "other"}
TEXT_KINDS = {"article-text", "supplementary-text"}
INSTRUCTIONS = (
    "Acquire only the main article and supplementary text (methods, results, appendices, "
    "tables and figures within those documents). Do not download code, software repositories, "
    "raw datasets, simulation traces, saved software outputs or mixed repository archives. "
    "Do not convert those artifacts to TXT/PDF to make them reader inputs. A text document "
    "may contain equations or code examples; retain that document intact. Record out-of-scope "
    "links without fetching them. If a claim depends on material outside this scope, record "
    "the unexamined dependency and limit the claim; do not claim reproducibility was checked."
)
_NON_TEXT = {".py", ".pyc", ".r", ".rmd", ".m", ".jl", ".ipynb", ".sh", ".js", ".c", ".cpp", ".h",
             ".java", ".exe", ".dll", ".so", ".rds", ".rdata", ".mat", ".npy", ".npz", ".h5", ".hdf5",
             ".sav", ".dta", ".parquet", ".sqlite", ".sqlite3", ".mp4", ".avi", ".mov", ".wav", ".mp3"}
_ARCHIVES = {".zip", ".gz", ".tgz", ".tar", ".bz2", ".xz", ".7z", ".rar"}
_DOCUMENTS = {".pdf", ".xml", ".txt", ".md", ".html", ".htm", ".doc", ".docx", ".rtf", ".odt"}
_MIMES = {"application/zip", "application/x-zip-compressed", "application/gzip", "application/x-gzip",
          "application/x-tar", "application/x-7z-compressed", "application/x-rar-compressed",
          "text/x-python", "text/x-r-source", "application/x-ipynb+json"}


def exclusion(location, *, material_kind=None, description="", headers=None):
    """Reject known artifact types, not relevance or words inside an article.

    Opaque URLs and text files still require source-grounded supervisor inspection.
    A declaration cannot disguise a known code extension as supplementary text.
    """
    if material_kind is not None:
        if not isinstance(material_kind, str) or material_kind not in MATERIAL_KINDS:
            raise ValueError("Unknown source material_kind")
        if material_kind not in TEXT_KINDS:
            return "Outside text-only acquisition scope: declared " + material_kind
    parsed = urlsplit(str(location or ""))
    path = unquote(parsed.path).lower()
    names = [path] + [unquote(v).lower() for k, v in parse_qsl(parsed.query)
                     if k.lower() in {"filename", "file", "name", "download", "path"}]
    h = {k.lower(): str(v).lower() for k, v in (headers or {}).items()}
    names += re.findall(r'filename\*?=(?:utf-8\x27\x27)?["\x27]?([^"\x27;]+)', h.get("content-disposition", ""))
    for name in names:
        suffix = PurePosixPath(unquote(name).strip()).suffix
        if suffix in _NON_TEXT:
            return "Outside text-only acquisition scope: code, data or media file"
        if suffix in _ARCHIVES:
            return "Outside text-only acquisition scope: archive; locate a direct textual supplement if available"
        if suffix in {".csv", ".tsv"} and material_kind != "supplementary-text":
            return "Tabular download needs explicit supplementary-text identification; raw datasets are outside scope"
    host = (parsed.hostname or "").lower()
    if host in {"github.com", "www.github.com", "api.github.com", "codeload.github.com", "gitlab.com", "bitbucket.org"}:
        if PurePosixPath(path).suffix not in _DOCUMENTS:
            return "Outside text-only acquisition scope: software repository; use only a direct article/text document"
    mime = h.get("content-type", "").split(";", 1)[0].strip()
    if mime in _MIMES or mime.startswith(("audio/", "video/")):
        return "Outside text-only acquisition scope: non-document response type"
    if re.match(r"^(?:supplement(?:ary|al)\s+)?(?:source code|software(?: repository)?|raw data(?:set)?|dataset|simulation (?:code|traces|outputs))(?:\b|:)", description.strip(), re.I):
        return "Outside text-only acquisition scope: link explicitly identifies code/data/software outputs"
    return None


def check(location, **kwargs):
    from .sources import SourceError
    why = exclusion(location, **kwargs)
    if why:
        raise SourceError("out-of-scope", why)


def get(client, url, *, enabled=False, material_kind=None):
    if not enabled:
        return client.get(url)
    from .sources import SourceClient
    check(url, material_kind=material_kind)
    # Native transport checks redirects and response headers before reading bytes.
    result = client.get(url, text_only=True, material_kind=material_kind) if isinstance(client, SourceClient) else client.get(url)
    body, response = result
    check(response.get("url", url), material_kind=material_kind, headers=response.get("headers"))
    final_path = urlsplit(response.get("url", url)).path.lower()
    office_document = PurePosixPath(final_path).suffix in {".docx", ".odt"}
    if not office_document and body.startswith((b"PK\x03\x04", b"\x1f\x8b", b"7z\xbc\xaf\x27\x1c", b"Rar!")):
        from .sources import SourceError
        raise SourceError("out-of-scope", "Archive response is outside text-only acquisition scope; no source file retained")
    return body, response
