"""Explicit execution priorities and acquisition effort; never eligibility rules."""
import json
import time

from .common import canonical, digest
from .transactions import atomic_operation

DEFAULT = {"retained_first": False, "retrieval_max_rounds": None,
           "inference_workers": None, "supervised_checkpoints": False, "workflow": "legacy"}


def validate(value):
    if not isinstance(value, dict) or set(value) - set(DEFAULT):
        raise ValueError("Unknown operational policy fields")
    result = dict(DEFAULT, **value)
    for key in ("retained_first", "supervised_checkpoints"):
        if type(result[key]) is not bool:
            raise ValueError(key + " must be boolean")
    for key in ("retrieval_max_rounds", "inference_workers"):
        if result[key] is not None and (type(result[key]) is not int or result[key] < 1):
            raise ValueError(key + " must be a positive integer or null")
    if result["workflow"] not in {"legacy", "focused-v1"}:
        raise ValueError("Unknown workflow contract")
    if result["workflow"] == "focused-v1" and result["retrieval_max_rounds"] != 1:
        raise ValueError("focused-v1 requires exactly one acquisition pass")
    if "workflow" not in value:
        result.pop("workflow")
    return result


def load(conn):
    row = conn.execute("SELECT value FROM meta WHERE key='state:runtime_continuation'").fetchone()
    if row:
        return validate(json.loads(row[0])["policy"])
    row = conn.execute("SELECT value FROM meta WHERE key='plan'").fetchone()
    return validate(json.loads(row[0]).get("resources", {}).get("operational_policy", {}) if row else {})


def for_coordinator(c):
    with c.store._connection() as conn:
        return load(conn)


def uncertain_sql(alias="p"):
    return ("(coalesce(json_extract(" + alias + ".record,'$.screening_current.decision'),'')='uncertain' "
            "AND coalesce(json_extract(" + alias + ".record,'$.assessment.paper_decision'),'')!='prospect')")


def uncertain_job_sql():
    return ("(j.stage IN ('reader','retrieval') AND coalesce(json_extract(j.payload,'$.calibration_review'),0)=0 "
            "AND EXISTS(SELECT 1 FROM papers p WHERE p.id=json_extract(j.payload,'$.paper_id') AND " + uncertain_sql() + "))")


def contextual_followup_sql(alias="p"):
    """Scheduling only: a completed ordinary reading of these same sources.

    A stale, incomplete or combined reading never acquires this lower priority.
    Native eligibility remains unassessed and its obligation remains pending.
    """
    record = alias + ".record"
    return ("(" + alias + ".status='assessed'"
        " AND json_extract(" + record + ",'$.assessment.assessment_status')='complete'"
        " AND json_extract(" + record + ",'$.assessment.paper_decision')='context'"
        " AND json_extract(" + record + ",'$.assessment_source_generation')=coalesce(json_extract(" + record + ",'$.source_generation'),1)"
        " AND json_extract(" + record + ",'$.packet_source_generation')=coalesce(json_extract(" + record + ",'$.source_generation'),1)"
        " AND json_extract(" + record + ",'$.packet_path') IS NOT NULL"
        " AND EXISTS(SELECT 1 FROM jobs old_reader WHERE old_reader.id=json_extract(" + record + ",'$.reader_job')"
        " AND old_reader.stage='reader' AND old_reader.state='complete'"
        " AND json_extract(old_reader.payload,'$.unified_reader') IS NULL"
        " AND coalesce(json_extract(old_reader.payload,'$.calibration_review'),0)=0))")


def _focused_model_ready(conn):
    """Only dispatchable model work holds background native follow-ups.

    Use the ordinary claim predicate so held, superseded, blocked, dependency-
    waiting and delayed jobs cannot indefinitely starve the background lane.
    Source retrieval/search use separate capacity and can run alongside it.
    """
    from .store import Store
    from .profiles import profile_fingerprint
    from .host_access import profile_blocked
    blocks = {row[0][6:]: json.loads(row[1]) for row in conn.execute(
        "SELECT key,value FROM meta WHERE key LIKE 'state:access-block:%'") if json.loads(row[1]).get("active")}
    if "access-block:budget" in blocks:
        return False
    plan = json.loads(conn.execute("SELECT value FROM meta WHERE key='plan'").fetchone()[0])
    host_row = conn.execute("SELECT value FROM meta WHERE key='state:host-access'").fetchone()
    host = json.loads(host_row[0]) if host_row else {}
    predicate, args = Store.claimable_sql(conn, ['title','abstract','rescue','audit','reader'], now=time.time())
    for row in conn.execute("SELECT j.stage,coalesce(json_extract(j.payload,'$.calibration_review'),0) review FROM jobs j WHERE " + predicate, args):
        profile = (plan.get('calibration_review_profile') if row['review'] else
            plan['profiles']['rescue' if row['stage'] in {'rescue','audit'} else row['stage']])
        if profile and 'access-block:profile:' + profile_fingerprint(profile) not in blocks and not profile_blocked(host, profile):
            return True
    return False


def primary_pending(conn):
    if load(conn).get("workflow") == "focused-v1":
        return _focused_model_ready(conn)
    # Ready or running work, not blocked inputs/cooldowns, holds the preferred lane.
    blocks = {row[0][6:]: json.loads(row[1]) for row in conn.execute(
        "SELECT key,value FROM meta WHERE key LIKE 'state:access-block:%'") if json.loads(row[1]).get("active")}
    plan = json.loads(conn.execute("SELECT value FROM meta WHERE key='plan'").fetchone()[0])
    host_row = conn.execute("SELECT value FROM meta WHERE key='state:host-access'").fetchone()
    host = json.loads(host_row[0]) if host_row else {}
    from .profiles import profile_fingerprint
    from .host_access import profile_blocked
    from .store import Store
    for row in conn.execute("SELECT j.state,j.stage," + Store.local_retrieval_sql(untried_during_hold=True) + " local_source,coalesce(json_extract(j.payload,'$.calibration_review'),0) review FROM jobs j WHERE (j.state='running' OR (j.state='pending' AND j.available_at<=?)) "
            "AND NOT EXISTS(SELECT 1 FROM job_supersessions s WHERE s.job_id=j.id) "
            "AND NOT EXISTS(SELECT 1 FROM meta b WHERE b.key='state:access-block:job:'||j.id AND json_extract(b.value,'$.active')=1) "
            "AND NOT EXISTS(SELECT 1 FROM dependencies d JOIN jobs q ON q.id=d.dependency_id WHERE d.job_id=j.id AND q.state!='complete') "
            "AND NOT " + uncertain_job_sql(), (time.time(),)):
        role = {'reader':'reader','title':'title','abstract':'abstract','rescue':'rescue','audit':'rescue'}.get(row['stage'])
        if role and row['state'] != 'running':
            profile = plan.get('calibration_review_profile') if row['review'] else plan['profiles'][role]
            if ('access-block:budget' in blocks or (profile and
                    ('access-block:profile:' + profile_fingerprint(profile) in blocks or profile_blocked(host, profile)))):
                continue
        if row['state'] != 'running' and host.get('network') and (row['stage'] in {'search', 'abstract-lookup'} or row['stage'] == 'retrieval' and not row['local_source']):
            continue
        return True
    has_controls = conn.execute("SELECT 1 FROM sqlite_master WHERE name='native_task_control'").fetchone()
    control_filter = (" AND NOT EXISTS(SELECT 1 FROM native_task_control t WHERE t.task_id=p.id AND t.available_at>?)"
                      if has_controls else "")
    rows = conn.execute("SELECT p.record FROM meta m,json_each(m.value,'$.native_assessment_pending') n "
        "JOIN papers p ON p.id=n.key WHERE m.key='state:discovery_frontiers' AND NOT " + uncertain_sql() +
        " AND p.status NOT IN ('retrieval-pending','reader-pending')" + control_filter,
        (time.time(),) if has_controls else ())
    from .discovery import _native_source_wait
    return any(_native_source_wait(json.loads(row[0])) is None for row in rows)


def job_filter(conn):
    from .workflow import enabled_conn, job_hold_sql
    held = job_hold_sql() if enabled_conn(conn) else ""
    if enabled_conn(conn):
        return held
    if not load(conn)["retained_first"]:
        return held
    return held + (" AND NOT " + uncertain_job_sql() if primary_pending(conn) else "")


def job_order(conn=None):
    if conn is not None and load(conn).get("workflow") == "focused-v1":
        # Finish source-ready work before admitting more papers. Bounded discovery
        # buffers ensure earlier stages still drain when this finite queue clears.
        return "j.priority DESC,coalesce((SELECT json_extract(p.record,'$.citation_depth') FROM papers p WHERE p.id=json_extract(j.payload,'$.paper_id')),2147483647),j.id"
    return ("coalesce((SELECT json_extract(p.record,'$.citation_depth') FROM papers p "
            "WHERE p.id=json_extract(j.payload,'$.paper_id')),2147483647),j.id")


def native_rank(conn, task, policy=None):
    policy = policy or load(conn)
    if policy.get("workflow") == "focused-v1":
        category = task.get("task", "")
        background = False
        if policy["retained_first"] and category == "native-discovery-audit" and task.get("paper_id"):
            row = conn.execute("SELECT " + contextual_followup_sql() + " FROM papers p WHERE p.id=?", (task['paper_id'],)).fetchone()
            background = bool(row and row[0])
        return (int(background), 2 if category == "bounded-public-source-acquisition" else 1 if category == "bibliographic-identity-resolution" else 0, task.get("paper_id", ""))
    if not (policy or load(conn))["retained_first"] or not task.get("paper_id") or str(task.get("task_id", "")).startswith("calibration:"):
        return (0, 0, "")
    row = conn.execute("SELECT " + uncertain_sql() + ",json_extract(p.record,'$.citation_depth') "
                       "FROM papers p WHERE p.id=?", (task["paper_id"],)).fetchone()
    return (1, row[1] if type(row[1]) is int else 2147483647, task["paper_id"]) if row and row[0] else (0, 0, "")


def free_slots(conn):
    cap = load(conn)["inference_workers"]
    if cap is None:
        return None
    used = conn.execute("SELECT count(*) FROM jobs WHERE state='running' AND stage IN ('title','abstract','rescue','audit','reader')").fetchone()[0]
    if conn.execute("SELECT 1 FROM sqlite_master WHERE name='native_task_control'").fetchone():
        used += conn.execute("SELECT count(*) FROM native_task_control WHERE owner IS NOT NULL").fetchone()[0]
    return max(0, cap - used)


@atomic_operation
def park_exhausted(c):
    """Settle unsuccessful rounds without rewriting any acquisition receipt."""
    with c.store._connection() as conn:
        cap = load(conn)["retrieval_max_rounds"]
        if cap is None:
            return []
        rows = conn.execute("SELECT j.*,count(a.id) rounds FROM jobs j JOIN retrieval_attempts a ON a.job_id=j.id "
            "WHERE j.stage='retrieval' AND j.state='pending' "
            "AND NOT EXISTS(SELECT 1 FROM job_supersessions s WHERE s.job_id=j.id) "
            "GROUP BY j.id HAVING count(a.id)>=? AND count(a.completed_at)=count(a.id)", (cap,)).fetchall()
        parked = []
        for row in rows:
            job = c.store._job(row)
            last = conn.execute("SELECT result FROM retrieval_attempts WHERE job_id=? ORDER BY number DESC LIMIT 1", (job["id"],)).fetchone()
            result = json.loads(last[0])
            if result.get("status") != "deferred":
                continue
            proof = {"job_id": job["id"], "rounds": row["rounds"], "limit": cap,
                "source_generation": job["payload"].get("source_generation", 1),
                "last_result_sha256": digest(result),
                "reason": "Authorized acquisition rounds exhausted; awaiting source/access, not scientific exclusion or saturation"}
            c.store._event(conn, "retrieval_parked", proof)
            conn.execute("UPDATE jobs SET state='parked',owner=NULL,lease_until=NULL,error=?,updated_at=? WHERE id=?",
                         (proof["reason"], time.time(), job["id"]))
            pid = job["payload"]["paper_id"]
            paper = c.store.paper(pid)
            if (paper and paper.get("source_generation", 1) == proof["source_generation"]
                    and paper.get("status") == "retrieval-pending"):
                c.store.update_paper(pid, {"status": "source-missing", "acquisition_park": proof,
                    "retrieval": result, "retrieval_job": job["id"]}, proof["reason"])
                if c.plan.get("mode") == "discovery":
                    from .discovery import queue_native_after_missing_source
                    queue_native_after_missing_source(c, pid)
                from .workflow import on_source_missing
                on_source_missing(c, pid)
            parked.append(proof)
        return parked


def parked_receipt(conn, job, proof, paper=None):
    """Validate settled acquisition against its event and original attempt receipt.

    A parked job has no completed job result. Its final unsuccessful attempt is
    retained verbatim, including status=deferred; source-missing is presentation
    of exhausted acquisition effort, not a rewritten retrieval outcome.
    """
    def require(value, message):
        if not value:
            raise ValueError(message)

    require(job["stage"] == "retrieval" and job["state"] == "parked"
            and job["owner"] is None and job["lease_until"] is None
            and job["result"] is None and not job["projected"],
            "Parked acquisition lacks its settled unowned, unprojected state")
    require(isinstance(proof, dict) and proof.get("job_id") == job["id"]
            and isinstance(proof.get("reason"), str) and proof["reason"].strip()
            and job["error"] == proof["reason"], "Acquisition parking evidence is absent or mismatched")
    payload = json.loads(job["payload"])
    require(type(proof.get("source_generation")) is int
            and proof["source_generation"] == payload.get("source_generation", 1),
            "Acquisition parking source generation differs from its job")
    attempts = conn.execute("SELECT count(*),count(completed_at) FROM retrieval_attempts WHERE job_id=?",
                            (job["id"],)).fetchone()
    require(type(proof.get("limit")) is int and proof["limit"] > 0
            and type(proof.get("rounds")) is int
            and proof["rounds"] == attempts[0] == attempts[1] and attempts[0] >= proof["limit"],
            "Acquisition parking lacks its completed round accounting")
    last = conn.execute("SELECT result FROM retrieval_attempts WHERE job_id=? ORDER BY number DESC LIMIT 1",
                        (job["id"],)).fetchone()
    result = json.loads(last[0]) if last and last[0] else None
    require(isinstance(result, dict) and result.get("status") == "deferred"
            and digest(result) == proof.get("last_result_sha256"),
            "Parked source differs from its preserved failed acquisition receipt")
    if paper is not None:
        require(payload.get("paper_id") == paper["paper_id"], "Parked acquisition belongs to another paper")
        require(paper.get("acquisition_park") == proof, "Paper differs from its durable parking evidence")
        require(paper.get("retrieval") == result, "Paper differs from its preserved acquisition receipt")
        if paper["status"].startswith("source-"):
            require(paper["status"] == "source-missing", "Parked acquisition must remain source-missing")
            if not paper.get("retrieval_revision_pending"):
                require(paper.get("source_generation", 1) == proof["source_generation"],
                        "Current parked acquisition belongs to a stale source generation")
    return result
