"""Operational discovery integrity; no independent scientific classifications."""
from __future__ import annotations
import copy
import json
from pathlib import Path
from jsonschema.exceptions import ValidationError, SchemaError

from . import citation_depth, frontiers, sources
from .common import canonical, digest, inside, file_hash
from .store import apply_state_delta


def validate_discovery(coordinator, conn, error, checked):
    row = conn.execute("SELECT value FROM meta WHERE key='state:discovery_frontiers'").fetchone()
    if row is None:
        return
    state = json.loads(row[0])
    def require(ok, message):
        if not ok:
            raise ValueError(message)
    def report(name, function):
        try:
            function()
            checked(name)
        except (ValueError, KeyError, TypeError, AttributeError, IndexError, OSError, ValidationError, SchemaError) as exc:
            error(name, "discovery", exc)
    def control_history():
        reconstructed = None
        for event in conn.execute("SELECT kind,payload FROM events WHERE kind IN ('control_updated','control_delta') ORDER BY id"):
            payload = json.loads(event[1])
            if payload.get('key') != 'discovery_frontiers':
                continue
            previously_satisfied = bool(reconstructed and reconstructed.get('principal_provisionally_satisfied'))
            if event[0] == 'control_updated':
                require(payload.get('previous') == reconstructed, 'Frontier control history does not join its preceding state')
                reconstructed = payload['value']
            else:
                require(digest(reconstructed) == payload['previous_sha256'], 'Frontier delta previous hash mismatch')
                reconstructed = apply_state_delta(reconstructed, payload['changes'])
                require(digest(reconstructed) == payload['value_sha256'], 'Frontier delta result hash mismatch')
            if reconstructed.get('principal_provisionally_satisfied') and not previously_satisfied:
                require(not frontiers.principal_errors(reconstructed), 'Blind lane opened without a satisfied principal frontier in its recorded transition')
            checked('discovery_history_events')
        require(reconstructed == state, 'Current frontier differs from append-only history')
        require(state.get('max_citation_depth') == coordinator.plan.get('resources', {}).get('max_citation_depth'), 'Depth bound differs from immutable plan')
        limit = state.get('max_citation_depth')
        require(limit is None or type(limit) is int and limit >= 0, 'Invalid citation depth bound')
        frozen = frontiers.initial_state(max_citation_depth=limit)
        require(state.get('science_config_sha256') == frozen['science_config_sha256'], 'Discovery scientific configuration binding changed')
        require(set(state['blind_windows']) == set(frozen['blind_windows']), 'Mandatory frozen blind windows were added or omitted')
        for key, window in frozen['blind_windows'].items():
            require(all(state['blind_windows'][key].get(k) == value for k,value in window.items() if k != 'status'), 'Blind query parameters differ from their frozen window')
        for label, activation in state['activated_y'].items():
            windows = [w for w in state['process_windows'].values() if w.get('normalized_y_label') == label]
            require(bool(windows), 'Earned Y has no process windows')
            require(activation.get('normalized_y_label') == label, 'Earned-Y identity mismatch')
            frozen = frontiers.activate_process(frozen,activation['eligible_comparison'],windows[0]['lexical_provenance'],normalization_reason=activation['normalization_reason'])
            checked('discovery_earned_y_bindings')
        require(set(state['process_windows']) == set(frozen['process_windows']), 'Process windows do not match independently recorded earned Ys')
        for key, window in frozen['process_windows'].items():
            require(all(state['process_windows'][key].get(k) == value for k,value in window.items() if k != 'status'), 'Process query parameters differ from their recorded earned-Y window')
    report('discovery_control_history', control_history)
    def paths():
        names = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        require({'citation_paths','citation_edges','citation_depth_sync'} <= names, 'Indexed citation-distance tables are missing')
        conn.execute('CREATE TEMP TABLE audit_citation_edges(parent_id TEXT,child_id TEXT,PRIMARY KEY(parent_id,child_id))')
        conn.execute('CREATE TEMP TABLE audit_citation_roots(paper_id TEXT,origin TEXT,PRIMARY KEY(paper_id,origin))')
        for encounter in conn.execute('SELECT paper_id,provenance FROM encounters ORDER BY id'):
            provenance = json.loads(encounter[1])
            if provenance.get('route') in citation_depth.ROOT_ROUTES:
                origin = {'route': provenance['route'], 'root_paper_id': encounter[0]}
                if provenance.get('window_key'):
                    origin['window_key'] = provenance['window_key']
                conn.execute('INSERT OR IGNORE INTO audit_citation_roots VALUES(?,?)', (encounter[0],canonical(origin)))
            else:
                parent = provenance.get('parent_paper_id') or (provenance.get('parent_obligation') or '').rsplit(':',1)[0]
                if parent:
                    conn.execute('INSERT OR IGNORE INTO audit_citation_edges VALUES(?,?)', (parent,encounter[0]))
            checked('discovery_path_encounters')
        require(conn.execute('SELECT parent_id,child_id FROM citation_edges EXCEPT SELECT parent_id,child_id FROM audit_citation_edges LIMIT 1').fetchone() is None, 'Citation edge has no encountered source provenance')
        require(conn.execute('SELECT parent_id,child_id FROM audit_citation_edges EXCEPT SELECT parent_id,child_id FROM citation_edges LIMIT 1').fetchone() is None, 'Encountered citation edge is absent from the distance index')
        for path in conn.execute('SELECT p.paper_id,p.depth,p.origin,r.record FROM citation_paths p LEFT JOIN papers r ON r.id=p.paper_id'):
            require(type(path[1]) is int and path[1] >= 0, 'Citation distance must be a nonnegative integer')
            require(path[3] is not None, 'Citation path references unknown paper')
            origin = json.loads(path[2]); paper = json.loads(path[3])
            require(paper.get('citation_depth') == path[1] and paper.get('citation_origin') == origin, 'Paper citation path differs from authoritative index')
            require(conn.execute('SELECT 1 FROM audit_citation_roots WHERE paper_id=? AND origin=?',(origin.get('root_paper_id'),canonical(origin))).fetchone() is not None, 'Citation origin has no independent root encounter')
            if path[1] == 0:
                require(origin.get('root_paper_id') == path[0], 'Depth-zero work is not its recorded root')
            else:
                require(conn.execute('SELECT 1 FROM citation_edges e JOIN citation_paths p ON e.parent_id=p.paper_id WHERE e.child_id=? AND p.depth=? AND p.origin=? LIMIT 1',(path[0],path[1]-1,path[2])).fetchone() is not None, 'Citation depth lacks a supporting shortest predecessor')
            checked('discovery_indexed_paths')
        require(conn.execute('SELECT 1 FROM citation_edges e JOIN citation_paths p ON p.paper_id=e.parent_id LEFT JOIN citation_paths c ON c.paper_id=e.child_id WHERE c.paper_id IS NULL OR c.depth>p.depth+1 LIMIT 1').fetchone() is None, 'Citation shortest-path propagation is incomplete')
        require(conn.execute('SELECT 1 FROM audit_citation_roots r LEFT JOIN citation_paths p ON p.paper_id=r.paper_id WHERE p.paper_id IS NULL OR p.depth<>0 LIMIT 1').fetchone() is None, 'An independent root is missing its zero distance')
        for row in conn.execute('SELECT r.id,r.record FROM papers r LEFT JOIN citation_paths p ON p.paper_id=r.id WHERE p.paper_id IS NULL'):
            paper=json.loads(row[1])
            require(paper.get('citation_depth') is None and paper.get('citation_origin') is None, 'Paper claims citation distance without an authoritative path')
            checked('discovery_unlocated_papers')
        require(conn.execute('SELECT 1 FROM citation_depth_sync LIMIT 1').fetchone() is None, 'Citation depth changes still need frontier reconciliation')
    report('discovery_citation_paths', paths)
    def coverage():
        for key, obligation in state['citation_obligations'].items():
            pid = obligation['parent']['paper_id']
            require(key == pid + ':' + obligation['direction'], 'Citation obligation identity mismatch')
            path = conn.execute('SELECT depth,origin FROM citation_paths WHERE paper_id=?',(pid,)).fetchone()
            if path:
                require(obligation.get('parent_citation_depth') == path[0] and obligation.get('child_citation_depth') == path[0]+1 and obligation.get('citation_origin') == json.loads(path[1]), 'Obligation depth differs from indexed path')
            else:
                require(obligation.get('parent_citation_depth') is None, 'Obligation claims depth without an indexed path')
            generation = obligation.get('coverage_generation',0)
            require(type(generation) is int and generation >= 0, 'Invalid citation coverage generation')
            active = [p for p in obligation['pages'] if p['source']==obligation['source'] and p.get('coverage_generation',0)==generation]
            cursor = None; total = None; count = 0; seen=set(); last=None; manifest=None
            for page in active:
                snap = sources.load_snapshot(inside(coordinator.run_dir / page['path'],coordinator.run_dir))
                require(snap['request_sha256']==page['request_sha256'] and snap['result_set_sha256']==page['result_set_sha256'], 'Citation page differs from immutable response')
                require(snap['request']['source']==obligation['source'] and snap['request']['kind']==obligation['direction'] and snap['request']['parent']['paper_id']==pid, 'Citation page belongs to another obligation')
                require(snap['request']['cursor']==cursor, 'Citation page sequence is discontinuous')
                require(type(snap.get('reported_total')) is int and snap['reported_total']>=0, 'Missing citation source total')
                require(total is None or total==snap['reported_total'], 'Citation source count shifted within a generation')
                total=snap['reported_total']; count+=len(snap['results'])
                keys=frontiers.citation_identity_keys(snap)
                require(len(keys)==len(set(keys)) and not seen.intersection(keys), 'Citation coverage includes repeated source identities')
                require(page.get('source_identity_keys')==keys, 'Citation coverage identity index differs from source')
                seen.update(keys)
                marker=snap.get('reference_list_sha256')
                require(manifest is None or marker in {None,manifest}, 'Reference list shifted within a generation')
                manifest=marker or manifest
                cursor=snap.get('next_cursor'); last=snap
                require(count<=total, 'Citation coverage exceeds reported source total')
                checked('discovery_citation_pages')
            if obligation['status']=='complete':
                require(last is not None and last.get('exhausted') is True and cursor is None and count==total, 'Completed citation obligation lacks complete source coverage')
            else:
                require(obligation['cursor']==cursor, 'Pending citation cursor differs from completed page sequence')
                block=frontiers.citation_fetch_block(state,obligation)
                require(not block or obligation['status']==block, 'Citation obligation bypasses the operational depth boundary')
        for key, window in {**state['blind_windows'],**state['process_windows']}.items():
            if window['status']!='complete':continue
            snap=sources.load_snapshot(inside(coordinator.run_dir / window['snapshot_path'],coordinator.run_dir))
            require(snap['result_set_sha256']==window['result_set_sha256'], 'Completed query window differs from source snapshot')
            validated = frontiers.complete_window(state,key,snap,snapshot_path=window['snapshot_path'],reason='Operational query binding validation')
            expected = validated['blind_windows'].get(key) or validated['process_windows'][key]
            require(all(window.get(k) == expected[k] for k in ('reported_total','returned_count','truncated','source_exhausted')), 'Completed query count/truncation fields differ from source response')
            checked('discovery_query_windows')
        if state.get('principal_provisionally_satisfied'):
            require(bool(state.get('citation_wave_audits')), 'Principal satisfaction has no citation-wave audit')
    report('discovery_coverage',coverage)
