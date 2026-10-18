"""Build a clean downloadable agent repository from an explicit static allowlist.

This module never copies development history, run data, raw evaluations, source PDFs,
credentials or machine configuration. A manifest is an integrity check, not a
signature. The source scientific release remains byte-for-byte unchanged.
"""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import tempfile
import zipfile

MANIFEST = "DISTRIBUTION_MANIFEST.json"
SCIENCE_VERSION = "consciousness-sweep-0.9.14"
DOCS = ("README.md", "AGENTS.md", "CLAUDE.md", "EXECUTION.md")
READER_FILES = ("__init__.py", "schema.py", "reading_instructions.txt", "policy.json", "policy_crosswalk.txt")
MUTABLE_ROOTS = {"runs", "workspace", ".venv", ".git"}
NESTED_MUTABLE_PATHS = {"science/runs", "science/outputs/consolidated"}


class DistributionError(ValueError):
    pass


def _canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True, indent=2, allow_nan=False) + "\n"


def _sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _relative(value):
    if not isinstance(value, str):
        raise DistributionError("Unsafe manifest path")
    path = PurePosixPath(value)
    if path.is_absolute() or not path.parts or any(part in ("", ".", "..") for part in path.parts) or "\\" in value:
        raise DistributionError("Unsafe manifest path")
    return path


def _read_static(path, source_root):
    path = Path(path)
    if not path.is_file() or path.is_symlink():
        raise DistributionError("Missing or symlinked static file: " + path.name)
    try:
        path.resolve().relative_to(source_root.resolve())
    except ValueError:
        raise DistributionError("Static file escapes source repository")
    data = path.read_bytes()
    text = data.decode("utf-8", errors="ignore")
    if re.search(r"/(?:Users|home)/[A-Za-z0-9_.@+-]+/", text):
        raise DistributionError("Personal machine path in distributed file: " + path.name)
    if re.search(r"sk-[A-Za-z0-9_-]{24,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----", text):
        raise DistributionError("Possible credential in distributed file: " + path.name)
    return data


def _catalog(source):
    """Publish identities/evidence links; never distribute local qualification labels."""
    allowed = {"id", "provider", "model_id", "weights_id", "weights_license", "candidate_roles", "source_urls"}
    candidates = []
    for item in source.get("candidates", []):
        candidate = {key: value for key, value in item.items() if key in allowed}
        if item.get("evidence_status") == "candidate_not_task_qualified":
            for field in ("motivation", "limits"):
                if isinstance(item.get(field), str):
                    candidate[field] = item[field]
        if item.get("id") == "openai-sol-reference":
            candidate["motivation"] = "Public documentation positions Sol for complex work at lower cost than Astra; compare exact role configurations using source-grounded behavior and measured resource use."
            candidate["limits"] = "General capability does not qualify this literature-reading task, another role or native scientific certification. Pin model, effort, harness and context; backend identity may not be observable."
        elif item.get("id") == "qwen-local-screening":
            candidate["limits"] = "35B total is not 3B resident memory. Pin quantization, weight revision and backend; measure full-context and concurrent memory on the actual host. Not claimed to be the latest or strongest Qwen. Reader use requires additional qualification."
        candidate["evidence_status"] = "candidate_not_task_qualified"
        candidates.append(candidate)
    return {"registry_version": "portable-candidates-1", "verified_on": source.get("verified_on"),
            "status": "candidate_catalog_not_runtime_allowlist",
            "qualification_rule": "Availability, authorization and task-specific qualification are separate. Exact configurations need source-grounded evidence before approved use; users are not required to evaluate the entire catalog.",
            "selection_policy": "Recommend one accessible configuration within the user's resource limits. Compare seed results during the sweep and use only authorized alternatives when a source-grounded review warrants one; a separate pilot is optional.",
            "evaluation_dimensions": ["same-X, awareness and downstream-Y fidelity", "source grounding and evidence locations",
                "false exclusions and independent rescue", "restraint about null results and equivalence",
                "structured-output validity", "completed-call rate", "measured tokens, latency and spend"],
            "selection_order": ["Establish accessible, authorized exact role configurations and explicit resource limits.",
                "Check source-grounded behavior for that role; keep unknown performance and costs explicit.",
                "Recommend the least costly suitable accessible configuration; compare selected seed results with the coordinator-only baseline during ordinary work. A separate pilot is optional."],
            "ranking_scope": "No global model-quality ranking; qualification applies to the exact model, effort, adapter, context and scientific role.",
            "candidates": candidates, "harness_sources": source.get("harness_sources", {})}


def _collect(root):
    collected = {}

    def include(source, destination):
        _relative(destination)
        collected[destination] = _read_static(source, root)

    modules = sorted((root / "sweep").glob("*.py"))
    if not modules or not (root / "sweep" / "__init__.py").is_file():
        raise DistributionError("Portable runtime is missing")
    for path in modules:
        include(path, "sweep/" + path.name)
    if (root / "sweep" / "provider_docs.json").is_file():
        include(root / "sweep" / "provider_docs.json", "sweep/provider_docs.json")
    if (root / "sweep" / "calibration_reference.json").is_file():
        include(root / "sweep" / "calibration_reference.json", "sweep/calibration_reference.json")
    for name in ('o200k_base.tiktoken','cl100k_base.tiktoken','tokenizer_LICENSE.txt'):
        if (root/'sweep'/name).is_file():
            include(root/'sweep'/name, 'sweep/'+name)
    include(root / "runtime" / "__init__.py", "runtime/__init__.py")
    for name in READER_FILES:
        include(root / "runtime" / "source_reader" / name, "runtime/source_reader/" + name)
    include(root / "bootstrap.py", "bootstrap.py")
    documents = root / "packaging" if (root / "packaging" / "README.md").is_file() else root
    for name in DOCS:
        include(documents / name, name)
    include(documents / "requirements.txt", "requirements.txt")
    # The accepted immutable policy cites this static contract by its source path.
    contract = root / "development" / "prospect_contract_v1.md"
    if contract.is_file():
        include(contract, "development/prospect_contract_v1.md")
    catalog_path = root / "development" / "agent_candidates.json"
    if not catalog_path.is_file():
        catalog_path = root / "agent_candidates.json"
    collected["agent_candidates.json"] = _canonical(_catalog(json.loads(_read_static(catalog_path, root)))).encode()
    science = root / "science"
    if not science.is_dir():
        science = root / "releases" / SCIENCE_VERSION
    release = json.loads(_read_static(science / "RELEASE_MANIFEST.json", root))
    files = release.get("files")
    if not isinstance(files, dict) or not files:
        raise DistributionError("Scientific release has no static manifest")
    for name, expected in files.items():
        path = _relative(name)
        if any(part in {"runs", "outputs", "tests", "diagnostics", "pilots", "__pycache__"} for part in path.parts):
            raise DistributionError("Scientific manifest includes forbidden dynamic material")
        content = _read_static(science / name, root)
        if hashlib.sha256(content).hexdigest() != expected:
            raise DistributionError("Scientific release hash mismatch: " + name)
        collected["science/" + name] = content
    include(science / "RELEASE_MANIFEST.json", "science/RELEASE_MANIFEST.json")
    collected[".gitignore"] = b".venv/\nruns/\nworkspace/\nscience/outputs/consolidated/\n__pycache__/\n*.py[cod]\n.DS_Store\n"
    # A clone must preserve manifest-bound bytes even with core.autocrlf=true.
    # Do not normalize frozen CSVs or any other scientific package content.
    collected[".gitattributes"] = b"* -text\n"
    return collected


def runtime_fingerprint(root=None):
    """Bind executable code, reader contract and frozen science, excluding run data."""
    root = Path(root or Path(__file__).resolve().parents[1]).resolve()
    files = {}
    for path in sorted((root / "sweep").glob("*.py")):
        files[path.relative_to(root).as_posix()] = _sha(path)
    for name in ('o200k_base.tiktoken','cl100k_base.tiktoken'):
        if (root/'sweep'/name).is_file():
            files['sweep/'+name] = _sha(root/'sweep'/name)
    if (root / "sweep" / "calibration_reference.json").is_file():
        files["sweep/calibration_reference.json"] = _sha(root / "sweep" / "calibration_reference.json")
    for name in READER_FILES:
        relative = "runtime/source_reader/" + name
        files[relative] = _sha(root / relative)
    files["runtime/__init__.py"] = _sha(root / "runtime" / "__init__.py")
    contract = root / "development" / "prospect_contract_v1.md"
    if contract.is_file():
        files["development/prospect_contract_v1.md"] = _sha(contract)
    science = root / "science"
    if not science.is_dir():
        # The development package and isolated release must agree scientifically;
        # a local developer run binds the actual package it will execute.
        science = root / "development" / "current"
    if not science.is_dir():
        science = root / "releases" / SCIENCE_VERSION
    manifest = science / "RELEASE_MANIFEST.json"
    if manifest.is_file():
        names = sorted(json.loads(manifest.read_text())["files"])
    else:
        names = [path.relative_to(science).as_posix() for path in science.rglob("*")
                 if path.is_file() and (len(path.relative_to(science).parts) == 1
                 or path.relative_to(science).parts[0] in {"tools", "schemas", "docs"})
                 and "__pycache__" not in path.parts and path.suffix not in {".pyc", ".pyo"}]
    for name in names:
        _relative(name)
        files["science/" + name] = _sha(science / name)
    encoded = json.dumps(files, sort_keys=True, separators=(",", ":")).encode()
    return {"format": "portable-runtime-binding-v1", "sha256": hashlib.sha256(encoded).hexdigest(), "files": files}


def build(destination, source_root=None, archive=True):
    """Build into a new directory and optionally its adjacent .zip; refuse overwrite."""
    root = Path(source_root or Path(__file__).resolve().parents[1]).resolve()
    destination = Path(destination).absolute()
    archive_path = destination.parent / (destination.name + ".zip")
    if destination.exists() or destination.is_symlink():
        raise DistributionError("Destination already exists; release builds never overwrite")
    if archive and archive_path.exists():
        raise DistributionError("Release archive already exists")
    files = _collect(root)
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix="." + destination.name + "-build-", dir=str(destination.parent)))
    zip_temp = None
    try:
        for name, data in files.items():
            target = staging / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        # Native preflight requires these empty containers. No historical run
        # or derived output is copied, and Git clones recreate them at setup.
        for name in ("science/runs", "science/outputs/consolidated"):
            (staging / name).mkdir(parents=True, exist_ok=True)
        manifest = {
            "format": "portable-agent-repository-v1",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "identity": "SHA-256 of actual distributed files; not a signature or clean-commit claim",
            "scope": "commissioned prospect discovery and screening; native registered certification remains separate",
            "files": {name: hashlib.sha256(data).hexdigest() for name, data in sorted(files.items())},
            "mutable_roots": sorted(MUTABLE_ROOTS),
            "nested_mutable_paths": sorted(NESTED_MUTABLE_PATHS),
            "excluded": ["source PDFs", "run history", "developer tests", "raw evaluation judgments", "credentials", "machine settings"],
            "calibration": "Versioned compact seed reference is coordinator-only; it is never included in model source packets or ordinary reader prompts.",
        }
        (staging / MANIFEST).write_text(_canonical(manifest), encoding="utf-8")
        verification = verify(staging)
        if archive:
            fd, temporary_name = tempfile.mkstemp(prefix="." + destination.name + "-", suffix=".zip", dir=str(destination.parent))
            os.close(fd)
            zip_temp = Path(temporary_name)
            with zipfile.ZipFile(zip_temp, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
                for path in sorted(staging.rglob("*")):
                    if path.is_file() or (path.is_dir() and not any(path.iterdir())):
                        bundle.write(path, (Path(destination.name) / path.relative_to(staging)).as_posix())
        os.rename(staging, destination)
        if archive:
            # Exclusive linking avoids overwriting an archive created concurrently.
            os.link(zip_temp, archive_path)
            zip_temp.unlink()
            zip_temp = None
        return {"destination": str(destination), "archive": str(archive_path) if archive else None,
                "manifest": manifest, "verification": verification}
    finally:
        if staging.exists():
            shutil.rmtree(staging)
        if zip_temp is not None and zip_temp.exists():
            zip_temp.unlink()


def verify(root):
    """Verify all static bytes and reject extra static files or escaping symlinks."""
    root = Path(root).resolve()
    path = root / MANIFEST
    if not path.is_file() or path.is_symlink():
        raise DistributionError("Distribution manifest is missing or symlinked")
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if manifest.get("format") != "portable-agent-repository-v1" or set(manifest.get("mutable_roots", [])) != MUTABLE_ROOTS:
        raise DistributionError("Unsupported distribution manifest")
    if set(manifest.get("nested_mutable_paths", [])) != NESTED_MUTABLE_PATHS:
        raise DistributionError("Unsupported nested mutable-path manifest")
    files = manifest.get("files")
    if not isinstance(files, dict) or not files:
        raise DistributionError("Distribution manifest contains no files")
    for name, expected in files.items():
        _relative(name)
        target = root / name
        if not target.is_file() or target.is_symlink() or _sha(target) != expected:
            raise DistributionError("Distributed input is missing or changed: " + name)
        try:
            target.resolve().relative_to(root)
        except ValueError:
            raise DistributionError("Distributed input escapes repository")
    for current, directories, names in os.walk(root, followlinks=False):
        relative = Path(current).relative_to(root)
        directories[:] = [name for name in directories if name != "__pycache__"
                          and not (relative == Path(".") and name in MUTABLE_ROOTS)
                          and (relative / name).as_posix() not in NESTED_MUTABLE_PATHS]
        for name in directories:
            if (Path(current) / name).is_symlink():
                raise DistributionError("Unexpected static directory symlink")
        for name in names:
            item = Path(current) / name
            rel = item.relative_to(root).as_posix()
            # Git worktrees use a regular root .git pointer file rather than
            # a directory. Treat it as metadata without opening its contents
            # or following the referenced checkout; symlinks stay rejected.
            if rel == ".git" and item.is_file() and not item.is_symlink():
                continue
            if name.endswith((".pyc", ".pyo")) or name == ".DS_Store":
                continue
            if rel not in files and rel != MANIFEST:
                raise DistributionError("Unexpected static file: " + rel)
    # Check the nested scientific manifest independently as well as outer hashes.
    release = json.loads((root / "science" / "RELEASE_MANIFEST.json").read_text(encoding="utf-8"))
    for name, expected in release.get("files", {}).items():
        _relative(name)
        if files.get("science/" + name) != expected:
            raise DistributionError("Outer and scientific manifests disagree: " + name)
    return {"ok": True, "files_verified": len(files), "manifest_sha256": _sha(path),
            "scientific_files_verified": len(release.get("files", {}))}
