"""Indexed execution-only citation distance, independent of bridge lineage.

An ordinary hop is one citation edge from a frozen seed/anchor or a labelled
independent query root. These tables contain no scientific eligibility claims.
They commit alongside source encounters and never duplicate those encounters.
"""
from __future__ import annotations

from collections import deque
import json
import time

from .common import canonical

ROOT_ROUTES = {"empirical-seed", "review-anchor", "process-triggered", "supplementary-blind"}


def ensure_tables(conn):
    # Do not use executescript: it implicitly commits an existing transaction.
    conn.execute("CREATE TABLE IF NOT EXISTS citation_paths(paper_id TEXT PRIMARY KEY,depth INTEGER NOT NULL,origin TEXT NOT NULL)")
    conn.execute("CREATE INDEX IF NOT EXISTS citation_path_depth ON citation_paths(depth)")
    conn.execute("CREATE TABLE IF NOT EXISTS citation_edges(parent_id TEXT NOT NULL,child_id TEXT NOT NULL,PRIMARY KEY(parent_id,child_id))")
    conn.execute("CREATE INDEX IF NOT EXISTS citation_edges_child ON citation_edges(child_id,parent_id)")
    conn.execute("CREATE TABLE IF NOT EXISTS citation_depth_sync(paper_id TEXT PRIMARY KEY)")


def _path(conn, paper_id):
    row = conn.execute("SELECT depth,origin FROM citation_paths WHERE paper_id=?", (paper_id,)).fetchone()
    return {"depth": row[0], "origin": json.loads(row[1])} if row else None


def record(conn, store, paper_id, provenance):
    """Record an edge/root and lower only affected paths inside the transaction."""
    ensure_tables(conn)
    route = provenance.get("route")
    parent = provenance.get("parent_paper_id")
    if not parent and provenance.get("parent_obligation"):
        parent = provenance["parent_obligation"].rsplit(":", 1)[0]
    candidate = None
    if route in ROOT_ROUTES:
        origin = {"route": route, "root_paper_id": paper_id}
        if provenance.get("window_key"):
            origin["window_key"] = provenance["window_key"]
        candidate = {"depth": 0, "origin": origin}
    elif parent:
        conn.execute("INSERT OR IGNORE INTO citation_edges VALUES(?,?)", (parent, paper_id))
        path = _path(conn, parent)
        if path:
            candidate = {"depth": path["depth"] + 1, "origin": path["origin"]}
    queue = deque([(paper_id, candidate)]) if candidate else deque()
    while queue:
        current, path = queue.popleft()
        previous = _path(conn, current)
        if previous and previous["depth"] <= path["depth"]:
            continue
        conn.execute("INSERT OR REPLACE INTO citation_paths VALUES(?,?,?)", (current, path["depth"], canonical(path["origin"])))
        conn.execute("INSERT OR IGNORE INTO citation_depth_sync VALUES(?)", (current,))
        row = conn.execute("SELECT record FROM papers WHERE id=?", (current,)).fetchone()
        if row:
            paper = json.loads(row[0])
            paper.update(citation_depth=path["depth"], citation_origin=path["origin"])
            store._event(conn, "citation_distance_lowered", {"paper_id": current, "previous": previous, "path": path,
                "reason": "A source encounter establishes a shorter ordinary citation path; bridge lineage is unchanged"})
            conn.execute("UPDATE papers SET record=?,updated_at=? WHERE id=?", (canonical(paper), time.time(), current))
        for child in conn.execute("SELECT child_id FROM citation_edges WHERE parent_id=?", (current,)):
            queue.append((child[0], {"depth": path["depth"] + 1, "origin": path["origin"]}))


def summary(store):
    with store._connection() as conn:
        exists = conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='citation_paths'").fetchone()
        return conn.execute("SELECT max(depth) FROM citation_paths").fetchone()[0] if exists else None
