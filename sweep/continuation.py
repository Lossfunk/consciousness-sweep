"""Explicit, backed-up operational continuation; the original plan is immutable."""
from functools import lru_cache
from contextlib import closing, contextmanager
import ast
import json
from pathlib import Path
import re
import sqlite3
import time
import uuid

from .common import ROOT, canonical, digest, file_hash, save_json
from .distribution import runtime_fingerprint, verify
from .execution_policy import validate as validate_policy


@lru_cache(maxsize=1)
def runtime_sha():
    return runtime_fingerprint()["sha256"]


@contextmanager
def _readonly(run):
    conn = sqlite3.connect((Path(run).resolve() / "state.sqlite3").as_uri() + "?mode=ro", uri=True)
    try:
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA query_only=ON")
        yield conn
    finally:
        conn.close()


def require_compatible(run, plan, target):
    with _readonly(run) as conn:
        row = conn.execute("SELECT value FROM meta WHERE key='state:runtime_continuation'").fetchone()
        if row:
            receipt = json.loads(row[0])
            previous, active = None, plan['runtime_fingerprint']
            for event in conn.execute("SELECT id,payload FROM events WHERE kind='runtime_continued' ORDER BY id"):
                current = dict(json.loads(event['payload']), event_id=event['id'])
                if (current['source_runtime'] != active or current['original_plan_sha256'] != digest(plan)
                        or current['previous_continuation_sha256'] != (digest(previous) if previous else None)):
                    raise ValueError("Continuation history mismatch; execution refused")
                validate_policy(current['policy'])
                active, previous = current['target_runtime'], current
            if receipt != previous or receipt["target_runtime"] != target:
                raise ValueError("Continuation binding/history mismatch; execution refused")
            validate_policy(receipt["policy"])
            return receipt
    if plan.get("runtime_fingerprint") != target:
        raise ValueError("Executable inputs changed; restore the run's bound release or use explicit continue-run")
    return None


def protected(name):
    return (name.startswith(("science/", "runtime/")) or name in {
        "development/prospect_contract_v1.md", "sweep/reading.py", "sweep/screening.py",
        "sweep/calibration.py", "sweep/calibration_reference.json", "sweep/frontiers.py"})


def _quiet(conn, run):
    if not (Path(run) / "STOP").is_file():
        raise ValueError("Pause admissions before continuation")
    if conn.execute("SELECT 1 FROM jobs WHERE state='running' LIMIT 1").fetchone():
        raise ValueError("Automatic jobs must drain or be recovered with termination proof")
    if conn.execute("SELECT 1 FROM sqlite_master WHERE name='native_task_control'").fetchone():
        if conn.execute("SELECT 1 FROM native_task_control WHERE owner IS NOT NULL LIMIT 1").fetchone():
            raise ValueError("Native leases must be released or recovered with observed termination proof")
    if conn.execute("SELECT 1 FROM retrieval_attempts WHERE completed_at IS NULL LIMIT 1").fetchone():
        raise ValueError("An interrupted acquisition lacks its terminal receipt; reconcile before continuation")
    latest = conn.execute("SELECT payload FROM events WHERE kind='operational_validation' ORDER BY id DESC LIMIT 1").fetchone()
    if not latest or json.loads(latest[0]).get("ok") is not True:
        raise ValueError("A successful quiet validation under the predecessor runtime is required")
    from .validation import NONMATERIAL_EVENTS
    event = json.loads(latest[0])
    row = conn.execute("SELECT max(id) FROM events WHERE kind NOT IN (" + ",".join("?" for _ in NONMATERIAL_EVENTS) + ")", NONMATERIAL_EVENTS).fetchone()
    if (row[0] or 0) > event["snapshot_event_id"]:
        raise ValueError("Predecessor validation is stale; validate after all workers and recovery writes are quiet")


def prepare(run, previous_release, policy, actor, reason):
    run, previous_release = Path(run).resolve(), Path(previous_release).resolve()
    if not str(actor).strip() or not str(reason).strip():
        raise ValueError("Continuation requires the authorizing actor and reason")
    verify(previous_release)
    if (ROOT / "DISTRIBUTION_MANIFEST.json").exists():
        verify(ROOT)
    source, target = runtime_fingerprint(previous_release), runtime_fingerprint()
    names = set(source["files"]) | set(target["files"])
    changed = sorted(name for name in names if source["files"].get(name) != target["files"].get(name))
    if any(protected(name) for name in changed):
        raise ValueError("Scientific/reader/calibration changes require separate scientific review")
    def source_instructions(root):
        tree = ast.parse((root / 'sweep/adapters.py').read_text())
        return [ast.literal_eval(node.value) for node in tree.body if isinstance(node, ast.Assign)
                and any(isinstance(target, ast.Name) and target.id == 'CODEX_SOURCE_INSTRUCTIONS' for target in node.targets)]
    if source_instructions(previous_release) != source_instructions(ROOT):
        raise ValueError("Source-only worker instructions changed; separate scientific review required")
    with _readonly(run) as conn:
        conn.execute("BEGIN")
        plan = json.loads(conn.execute("SELECT value FROM meta WHERE key='plan'").fetchone()[0])
        existing = conn.execute("SELECT value FROM meta WHERE key='state:runtime_continuation'").fetchone()
        prior = json.loads(existing[0]) if existing else None
        expected = prior["target_runtime"] if prior else plan["runtime_fingerprint"]
        if source != expected:
            raise ValueError("Previous release does not match this run's exact active runtime")
        require_compatible(run, plan, source)
        if digest(json.loads((run / "execution_plan.json").read_text())) != digest(plan):
            raise ValueError("Original plan file differs from the durable original agreement")
        _quiet(conn, run)
        snapshot = conn.execute("SELECT max(id) FROM events").fetchone()[0]
    return {"format": "operational-continuation-v1", "run_directory": str(run),
        "original_plan_sha256": digest(plan), "source_runtime": source, "target_runtime": target,
        "previous_continuation_sha256": digest(prior) if prior else None,
        "policy": validate_policy(policy), "actor": actor.strip(), "reason": reason.strip(),
        "snapshot_event_id": snapshot, "changed_runtime_files": changed,
        "scientific_inputs_changed": False, "model_profiles_changed": False,
        "status": "ready-for-explicit-apply"}


def apply(run, previous_release, policy, actor, reason):
    receipt = prepare(run, previous_release, policy, actor, reason)
    run = Path(run).resolve()
    folder = run / "continuations" / uuid.uuid4().hex
    folder.mkdir(parents=True)
    # Snapshot first. The write transaction below refuses any intervening event.
    with _readonly(run) as source, closing(sqlite3.connect(folder / "state-before.sqlite3")) as backup:
        source.backup(backup)
        # The backup must be a standalone file, including on hosts whose read-only
        # WAL reader cannot create absent sidecars. This changes only the backup.
        backup.execute("PRAGMA journal_mode=DELETE")
    (folder / "execution_plan.original.json").write_bytes((run / "execution_plan.json").read_bytes())
    receipt.update(backup_path=str((folder / "state-before.sqlite3").relative_to(run)),
        backup_sha256=file_hash(folder / "state-before.sqlite3"), continued_at=time.time(), status="applied-paused")
    conn = sqlite3.connect(run / "state.sqlite3", timeout=30, isolation_level=None)
    conn.row_factory = sqlite3.Row
    # A previous continuation's trigger expects the previously active runtime.
    conn.create_function("sweep_runtime_sha", 0, lambda: receipt["source_runtime"]["sha256"])
    try:
        conn.execute("BEGIN IMMEDIATE")
        _quiet(conn, run)
        if conn.execute("SELECT max(id) FROM events").fetchone()[0] != receipt["snapshot_event_id"]:
            raise ValueError("Run changed during backup; repeat preparation at a quiet checkpoint")
        if digest(json.loads(conn.execute("SELECT value FROM meta WHERE key='plan'").fetchone()[0])) != receipt["original_plan_sha256"]:
            raise ValueError("Original plan changed during continuation")
        event = conn.execute("INSERT INTO events(at,kind,payload) VALUES(?,'runtime_continued',?)", (time.time(), canonical(receipt))).lastrowid
        receipt["event_id"] = event
        conn.execute("INSERT OR REPLACE INTO meta VALUES('state:runtime_continuation',?)", (canonical(receipt),))
        # Fence older binaries, even though the historical plan still names them.
        # Old connections lack this function; older upgraded binaries return a different hash.
        triggers = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='trigger' AND name LIKE 'runtime_fence_%'")]
        for name in triggers:
            conn.execute('DROP TRIGGER "' + name + '"')
        tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
        for table in tables:
            if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", table):
                raise ValueError("Unsupported ledger table name")
            for operation in ("INSERT", "UPDATE", "DELETE"):
                conn.execute('CREATE TRIGGER "runtime_fence_' + table + '_' + operation + '" BEFORE ' + operation +
                    ' ON "' + table + '" BEGIN SELECT CASE WHEN sweep_runtime_sha() != \'' + receipt["target_runtime"]["sha256"] +
                    "' THEN RAISE(ABORT,'Inactive runtime cannot write this continued run') END; END")
        conn.execute("COMMIT")
    except BaseException:
        if conn.in_transaction:
            conn.execute("ROLLBACK")
        raise
    finally:
        conn.close()
    save_json(folder / "receipt.json", receipt)
    return receipt


def compatible_adapter_hash(c, observed):
    from . import adapters
    if observed == file_hash(adapters.__file__):
        return True
    receipt = c.store.get_state("runtime_continuation")
    if not receipt:
        return False
    with c.store._connection() as conn:
        return any(observed == json.loads(row[0])["source_runtime"]["files"].get("sweep/adapters.py")
                   for row in conn.execute("SELECT payload FROM events WHERE kind='runtime_continued'"))


def rebind_unadmitted_request(c, job):
    """A prepared predecessor request gets a fresh ID, never overwritten bytes."""
    from . import adapters
    directory = c.run_dir / "jobs" / job["id"] / "execution"
    path = directory / "binding.json"
    if not path.exists():
        return False
    binding = json.loads(path.read_text())
    if binding.get("adapter_source_sha256") == file_hash(adapters.__file__):
        return False
    if not compatible_adapter_hash(c, binding.get("adapter_source_sha256")):
        raise ValueError("Prepared request belongs to an unapproved adapter")
    receipt = json.loads((directory / "receipt.json").read_text())
    if (receipt.get("admission") != "not-admitted" or not receipt.get("completed_at")
            or receipt.get("binding_sha256") != file_hash(path)):
        raise ValueError("Predecessor request lacks verified terminal nonadmission; explicit recovery required")
    from .recovery import _source
    _, (prompt, schema) = _source(c, job)
    from .profiles import validate_profile
    profile = validate_profile(c.profile_for_job(job))
    if (binding.get("version") != adapters.VERSION or binding["profile"] != profile
            or receipt.get("requested_model") != profile["model"]
            or receipt.get("requested_effort") != profile["effort"]
            or binding["prompt_sha256"] != file_hash(directory / "prompt.txt")
            or (directory / "prompt.txt").read_bytes() != prompt.encode()
            or binding["schema_sha256"] != file_hash(directory / "schema.json")
            or json.loads((directory / "schema.json").read_text()) != schema):
        raise ValueError("Prepared predecessor source/profile changed")
    if binding.get("base_instructions_sha256") is not None:
        if file_hash(directory / "base_instructions.txt") != binding["base_instructions_sha256"]:
            raise ValueError("Prepared predecessor context instructions changed")
    from .transactions import transaction_view
    with c.store._transaction() as conn:
        view = transaction_view(c, conn)
        view.store._owned(conn, job["id"], job["owner"], job["token"])
        if conn.execute("SELECT 1 FROM reservations WHERE job_id=? AND state!='released'", (job["id"],)).fetchone():
            raise ValueError("Uncertain/admitted request charges require explicit retry; cannot rebind")
        if conn.execute("SELECT 1 FROM dependencies WHERE dependency_id=?", (job["id"],)).fetchone():
            raise ValueError("Prepared request has dependents; explicit graph recovery required")
        deps = [r[0] for r in conn.execute("SELECT dependency_id FROM dependencies WHERE job_id=?", (job["id"],))]
        successor = view.store.enqueue(job["stage"], "continued-request:" + job["id"] + ":" + runtime_sha(),
            job["payload"], priority=job["priority"], dependencies=deps)
        reason = "Confirmed unadmitted request rebound to explicitly continued adapter; original source/settings/receipt retained"
        view.store.supersede_job(job["id"], successor, reason)
        view.store.defer(job["id"], job["owner"], job["token"], reason)
        view.store._event(conn, "request_runtime_rebound", {"job_id": job["id"], "successor_id": successor,
            "receipt_sha256": file_hash(directory / "receipt.json"), "reason": reason})
    return True
