"""Attach a complete main/SI set as immutable, hash-bound source evidence."""
from pathlib import Path
import os
import shutil
import tempfile
from .common import file_hash, digest
from .transactions import atomic_operation

MANIFEST_FIELDS = ("paper_id", "title", "authors", "author", "year", "publication_year", "doi", "arxiv_id",
                   "pmcid", "pmid", "epmc_id", "epmc_source", "openalex_id", "url", "urls", "fulltext_url",
                   "fulltext_urls", "pdf_url", "open_access_url", "provided_paths", "fulltext_path", "pdf_path", "local_path",
                   "publication_status", "version", "version_of", "relation", "version_relations", "source_locations")


def source_manifest(paper):
    return {key: paper[key] for key in MANIFEST_FIELDS if key in paper}


@atomic_operation
def queue_retrieval(coordinator, paper_id, reason, *, force_retry=False):
    """Bind acquisition to immutable inputs; explicit retries preserve old jobs."""
    if not str(reason).strip():
        raise ValueError("Source acquisition requires a reason")
    paper = coordinator.store.paper(paper_id)
    if paper is None:
        raise ValueError("Unknown paper")
    generation = paper.get("source_generation", 1)
    if force_retry:
        generation += 1
        coordinator.store.update_paper(paper_id, {"source_generation": generation}, reason)
    manifest = source_manifest(paper)
    payload = {"paper_id": paper_id, "source_generation": generation,
               "source_manifest": manifest, "source_manifest_sha256": digest(manifest)}
    key = paper_id + ":source:" + str(generation) + ":" + digest(manifest)
    previous = coordinator.store.job_by_key("retrieval", key)
    job_id = coordinator.store.enqueue("retrieval", key, payload,
                                      priority=120 if paper.get("seed_role") == "empirical-seed" else 20)
    # Repeated attachment of completed input must not create a pending paper
    # with no pending work. A fresh source generation retires only current
    # presentation fields; prior results/assets remain in append-only history.
    if previous is None or (previous["state"] != "complete" and
            (paper.get("current_source_manifest_sha256") != digest(manifest) or paper.get("current_source_generation") != generation)):
        coordinator.store.update_paper(paper_id, {"status": "retrieval-pending", "assessment": None,
            "reader_job": None, "packet_path": None, "packet_source_generation": None, "assessment_source_generation": None, "assessment_packet_sha256": None, "retrieval_revision_pending": False, "current_source_manifest_sha256": digest(manifest), "current_source_generation": generation}, reason)
    coordinator.store.supersede_source_jobs(paper_id, generation, digest(manifest), job_id,
        "New immutable acquisition inputs supersede prior source-bound execution; preserve earlier results and costs")
    return job_id


def retry_acquisition(coordinator, paper_id, reason):
    return {"job_id": queue_retrieval(coordinator, paper_id, reason, force_retry=True),
            "status": "retrieval-pending", "reason": "Explicit acquisition retry preserves earlier attempts and their source evidence"}


def attach(coordinator, paper_id, entries, reason, base=None):
    from .coordinator import validate_record
    if not reason or not reason.strip():
        raise ValueError("A source revision needs a reason")
    if coordinator.store.paper(paper_id) is None:
        raise ValueError("Unknown paper")
    validate_record({"title": "source-manifest", "provided_paths": entries})
    if not entries:
        raise ValueError("Supply the complete nonempty main/SI set")
    base = Path(base or Path.cwd())
    assets = coordinator.run_dir / "intake" / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    normalized = []
    for entry in entries:
        item = dict(entry) if isinstance(entry, dict) else {"path": entry, "role": "main"}
        item.setdefault("role", "main")
        source = (base / item["path"]).resolve()
        if not source.is_file():
            raise ValueError("Source does not exist: " + str(source))
        with tempfile.NamedTemporaryFile(dir=assets, delete=False) as tmp:
            temporary = Path(tmp.name)
        try:
            shutil.copyfile(source, temporary)
            sha = file_hash(temporary)
            if item.get("expected_sha256") and item["expected_sha256"] != sha:
                raise ValueError("Supplied source hash does not match manifest")
            target = assets / (sha + source.suffix.lower())
            if target.exists():
                if file_hash(target) != sha:
                    raise ValueError("Immutable source snapshot has been modified")
            else:
                os.replace(temporary, target)
            item.update(path=str(target), expected_sha256=sha)
            normalized.append(item)
        finally:
            temporary.unlink(missing_ok=True)
    return _commit_sources(coordinator, paper_id, normalized, reason)


@atomic_operation
def _commit_sources(coordinator, paper_id, normalized, reason):
    paper = coordinator.store.paper(paper_id)
    if paper.get("provided_paths") != normalized:
        coordinator.store.update_paper(paper_id, {"provided_paths": normalized,
            "source_generation": paper.get("source_generation", 1) + 1}, reason)
    return {"job_id": queue_retrieval(coordinator, paper_id, reason),
            "sources": [{"role": item.get("role", "main"), "sha256": item["expected_sha256"]} for item in normalized]}
