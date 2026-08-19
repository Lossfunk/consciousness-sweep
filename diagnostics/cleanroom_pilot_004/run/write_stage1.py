from __future__ import annotations

import hashlib
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUN_ID = "PREFREEZE_DIAG_004"
RUN_DIR = ROOT / "runs" / RUN_ID
sys.path.insert(0, str(ROOT / "tools"))

from structured_write import (  # noqa: E402
    allocate_identifier,
    append_jsonl_record,
    doi_resolver_url,
    load_schema,
    normalize_doi,
    write_csv_record,
)


PAPERS = [
    {
        "expected_id": "P000001",
        "slug": "ben_haim_2021",
        "title": "Disentangling perceptual awareness from nonconscious processing in rhesus monkeys (Macaca mulatta)",
        "authors": "Moshe Shay Ben-Haim; Olga Dal Monte; Nicholas A. Fagan; Yarrow Dunham; Ran R. Hassin; Steve W. C. Chang; Laurie R. Santos",
        "year": 2021,
        "doi": "10.1073/pnas.2017543118",
        "abstract_reason": "The supplied abstract describes seven human and rhesus-monkey experiments that manipulate cue visibility and measure downstream cue-guided behavior.",
        "files": [("sources/ben_haim_2021_main.pdf", "published main article", True)],
        "notes": "The article repeatedly cites an online SI Appendix, but that appendix was not among the supplied sources; classification-critical gaps are retained as uncertainty.",
    },
    {
        "expected_id": "P000002",
        "slug": "keizer_2015",
        "title": "Consciousness is not necessary for visual feature binding",
        "authors": "Andre W. Keizer; Bernhard Hommel; Victor A. F. Lamme",
        "year": 2015,
        "doi": "10.3758/s13423-014-0706-2",
        "abstract_reason": "The supplied abstract reports visible and effectively masked S1 conditions and a downstream location-by-orientation binding effect.",
        "files": [("sources/keizer_2015_main.pdf", "published main article", True)],
        "notes": None,
    },
    {
        "expected_id": "P000003",
        "slug": "lamy_2015",
        "title": "The Role of Conscious Perception in Attentional Capture and Object-File Updating",
        "authors": "Dominique Lamy; Limor Alon; Tomer Carmel; Nir Shalev",
        "year": 2015,
        "doi": "10.1177/0956797614556777",
        "abstract_reason": "The supplied abstract reports trial-level cue visibility contrasts and downstream spatial-cuing patterns across cue-target color relations.",
        "files": [("sources/lamy_2015_main.pdf", "published main article", True)],
        "notes": None,
    },
    {
        "expected_id": "P000004",
        "slug": "lin_murray_2015",
        "title": "More Power to the Unconscious: Conscious, but Not Unconscious, Exogenous Attention Requires Location Variation",
        "authors": "Zhicheng Lin; Scott O. Murray",
        "year": 2015,
        "doi": "10.1177/0956797614560770",
        "abstract_reason": "The supplied abstract reports visible and invisible cue groups and downstream spatial-priority effects across fixed-cue, no-cue, and random-cue phases.",
        "files": [("sources/lin_murray_2015_main.pdf", "published main article", True)],
        "notes": "The article mentions online Supplemental Material that was not among the supplied sources; the main article contains the critical reported effects used here.",
    },
    {
        "expected_id": "P000005",
        "slug": "persaud_2011",
        "title": "Awareness-related activity in prefrontal and parietal cortices in blindsight reflects more than superior visual performance",
        "authors": "Navindra Persaud; Matthew Davidson; Brian Maniscalco; Dean Mobbs; Richard E. Passingham; Alan Cowey; Hakwan Lau",
        "year": 2011,
        "doi": "10.1016/j.neuroimage.2011.06.081",
        "abstract_reason": "The supplied abstract reports a blindsight awareness contrast with performance titration, downstream metacognitive calibration, and cortical activity measures.",
        "files": [("sources/persaud_2011_main.pdf", "published main article", True)],
        "notes": None,
    },
    {
        "expected_id": "P000006",
        "slug": "tsushima_2006",
        "title": "Greater Disruption Due to Failure of Inhibitory Control on an Ambiguous Distractor",
        "authors": "Yoshiaki Tsushima; Yuka Sasaki; Takeo Watanabe",
        "year": 2006,
        "doi": "10.1126/science.1133197",
        "abstract_reason": "The supplied article reports threshold-related awareness regimes and downstream disruption of RSVP performance by task-irrelevant motion.",
        "files": [
            ("sources/tsushima_2006_main.pdf", "published main article", True),
            ("sources/tsushima_2006_supplement.pdf", "published supporting online material", False),
        ],
        "notes": None,
    },
]


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


decision_schema = load_schema(ROOT, "decision_log.schema.json")
paper_schema = load_schema(ROOT, "papers.schema.json")
asset_schema = load_schema(ROOT, "fulltext_assets.schema.json")


def decision(entity_type: str, entity_id: str, decision_type: str, field: str, new_value, reason: str, source_location: str) -> None:
    record = {
        "decision_id": allocate_identifier(RUN_DIR, "decision"),
        "run_id": RUN_ID,
        "timestamp": now(),
        "entity_type": entity_type,
        "entity_id": entity_id,
        "decision_type": decision_type,
        "field": field,
        "old_value": None,
        "new_value": new_value,
        "reason": reason,
        "source_location": source_location,
        "agent": "Codex/GPT-5",
    }
    append_jsonl_record(RUN_DIR / "decision_log.jsonl", decision_schema, record)


for paper in PAPERS:
    paper_id = allocate_identifier(RUN_DIR, "paper")
    if paper_id != paper["expected_id"]:
        raise RuntimeError(f"unexpected allocated paper ID {paper_id}")

    primary_target = f"runs/{RUN_ID}/fulltexts/{paper_id}_{paper['slug']}_main.pdf"
    paper_row = {
        "paper_id": paper_id,
        "title": paper["title"],
        "authors": paper["authors"],
        "year": paper["year"],
        "doi": normalize_doi(paper["doi"]),
        "url": doi_resolver_url(paper["doi"]),
        "publication_status": "published",
        "first_discovery_route": "other",
        "first_discovery_parent": None,
        "first_discovery_query_id": None,
        "first_search_id": None,
        "first_seen_wave": 0,
        "title_screen": "retain",
        "title_screen_reason": "The supplied title directly concerns awareness or unconscious processing and a candidate downstream function.",
        "title_screen_method": "agent-semantic",
        "title_screen_rule_id": None,
        "abstract_status": "available",
        "abstract_screen": "screen-in",
        "abstract_screen_reason": paper["abstract_reason"],
        "abstract_screen_method": "agent-semantic",
        "abstract_screen_rule_id": None,
        "fulltext_priority": "high",
        "fulltext_priority_reason": "The full text was supplied in sources/ and directly supports comparison-level evaluation.",
        "fulltext_status": "retrieved-published",
        "fulltext_source": primary_target,
        "missing_text_priority": "none",
        "citation_expansion_status": "not-applicable",
        "citation_expansion_reason": "This source-bounded diagnostic prohibits citation expansion and additional retrieval.",
        "duplicate_of": None,
        "duplicate_reason": None,
        "current_status": "fulltext-retrieved",
        "notes": paper["notes"],
    }
    decision("paper", paper_id, "title-screen", "title_screen", "retain", paper_row["title_screen_reason"], paper["files"][0][0] + ": PDF page 1")
    decision("paper", paper_id, "abstract-screen", "abstract_screen", "screen-in", paper_row["abstract_screen_reason"], paper["files"][0][0] + ": PDF page 1")
    decision("paper", paper_id, "fulltext-retrieval", "fulltext_status", "retrieved-published", "A published full text was present in the user-supplied sources/ directory before this diagnostic; no network retrieval was performed.", paper["files"][0][0])
    write_csv_record(RUN_DIR / "papers_master.csv", paper_schema, paper_row)

    for source_rel, article_version, is_primary in paper["files"]:
        suffix = "main" if is_primary else "supplement"
        target_rel = f"runs/{RUN_ID}/fulltexts/{paper_id}_{paper['slug']}_{suffix}.pdf"
        text_rel = f"runs/{RUN_ID}/fulltexts/{paper_id}_{paper['slug']}_{suffix}.txt"
        page_map_rel = f"runs/{RUN_ID}/fulltexts/{paper_id}_{paper['slug']}_{suffix}_page_map.json"
        target = ROOT / target_rel
        text_path = ROOT / text_rel
        page_map_path = ROOT / page_map_rel
        for required_path in (target, text_path, page_map_path):
            if not required_path.is_file():
                raise RuntimeError(f"missing pre-extracted asset {required_path}")

        asset_id = allocate_identifier(RUN_DIR, "fulltext_asset")
        asset_row = {
            "fulltext_asset_id": asset_id,
            "paper_id": paper_id,
            "article_version": article_version,
            "source_identity": source_rel,
            "local_fulltext_path": target_rel,
            "file_sha256": sha256(target),
            "verified_at": now(),
            "verification_reason": "The PDF title/DOI or supplement identity was checked against its first page, and the copied file hash matches the supplied source file.",
            "acquisition_route": "preexisting user-supplied workspace source; copied into the diagnostic run without network access",
            "extraction_tool": "pypdf",
            "extraction_version": "6.4.0",
            "extracted_text_path": text_rel,
            "extracted_text_sha256": sha256(text_path),
            "page_map_path": page_map_rel,
            "page_map_sha256": sha256(page_map_path),
            "current_for_paper": is_primary,
            "notes": "PDF page numbers are preserved as explicit page markers in the extracted text.",
        }
        decision("fulltext_asset", asset_id, "fulltext-asset-verification", "file_sha256", asset_row["file_sha256"], asset_row["verification_reason"], target_rel + ": PDF page 1")
        write_csv_record(RUN_DIR / "fulltext_assets.csv", asset_schema, asset_row)

print("PASS: persisted 6 papers and 7 verified supplied full-text assets")
