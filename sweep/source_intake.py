"""Attach a complete main/SI set as immutable, hash-bound source evidence."""
from pathlib import Path
import os
import shutil
import tempfile
from .common import file_hash, digest


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
    coordinator.store.update_paper(paper_id, {"provided_paths": normalized, "status": "retrieval-pending"}, reason)
    return {"job_id": coordinator.store.enqueue("retrieval", paper_id + ":manual:" + digest(normalized), {"paper_id": paper_id}),
            "sources": [{"role": item.get("role", "main"), "sha256": item["expected_sha256"]} for item in normalized]}
