"""Small shared primitives; no scientific decisions live here."""
from __future__ import annotations
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]

def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False)

def digest(value):
    return hashlib.sha256((value if isinstance(value, bytes) else canonical(value).encode())).hexdigest()

def file_hash(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def save_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".write-", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as out:
            out.write(canonical(value) + "\n")
            out.flush()
            os.fsync(out.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)

def science_root():
    for candidate in (ROOT / "science", ROOT / "development" / "current"):
        if (candidate / "PROTOCOL.md").is_file():
            return candidate
    raise RuntimeError("Frozen scientific package is missing; use a complete release.")

def scientific_module(name):
    directory = science_root() / "tools"
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))
    # Native modules depend on one another using their existing import names.
    import importlib
    module = importlib.import_module(name)
    if Path(module.__file__).resolve().parent != directory.resolve():
        raise RuntimeError("Conflicting scientific module loaded: " + name)
    return module

def regime():
    root = science_root()
    return {name: file_hash(root / name) for name in
            ("PROTOCOL.md", "AGENTS.md", "config.yaml", "queries.md", "PROTOCOL_BRIEF.md")}

def safe_run(root, run_id):
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,99}", run_id) or run_id in {".", ".."}:
        raise ValueError("Run ID must be filesystem-safe, nonempty and <=100 characters")
    base = (Path(root) / "runs").resolve()
    path = base / run_id
    if path.is_symlink():
        raise ValueError("Run directory cannot be a symlink")
    return path

def inside(path, root):
    path, root = Path(path).resolve(), Path(root).resolve()
    try:
        path.relative_to(root)
    except ValueError:
        raise ValueError("Artifact must remain within its own run")
    return path
