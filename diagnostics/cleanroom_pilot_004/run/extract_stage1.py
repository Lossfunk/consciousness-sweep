from __future__ import annotations

import json
import shutil
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[2]
RUN_ID = "PREFREEZE_DIAG_004"
FILES = [
    ("P000001", "ben_haim_2021", "sources/ben_haim_2021_main.pdf", "main"),
    ("P000002", "keizer_2015", "sources/keizer_2015_main.pdf", "main"),
    ("P000003", "lamy_2015", "sources/lamy_2015_main.pdf", "main"),
    ("P000004", "lin_murray_2015", "sources/lin_murray_2015_main.pdf", "main"),
    ("P000005", "persaud_2011", "sources/persaud_2011_main.pdf", "main"),
    ("P000006", "tsushima_2006", "sources/tsushima_2006_main.pdf", "main"),
    ("P000006", "tsushima_2006", "sources/tsushima_2006_supplement.pdf", "supplement"),
]

for paper_id, slug, source_rel, suffix in FILES:
    target_dir = ROOT / "runs" / RUN_ID / "fulltexts"
    target = target_dir / f"{paper_id}_{slug}_{suffix}.pdf"
    text_path = target_dir / f"{paper_id}_{slug}_{suffix}.txt"
    page_map_path = target_dir / f"{paper_id}_{slug}_{suffix}_page_map.json"
    target_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / source_rel, target)
    reader = PdfReader(target)
    chunks = []
    page_map = []
    offset = 0
    for index, page in enumerate(reader.pages, start=1):
        chunk = f"[[PDF PAGE {index}]]\n{page.extract_text() or ''}\n"
        chunks.append(chunk)
        page_map.append({"pdf_page": index, "start_character": offset, "end_character": offset + len(chunk)})
        offset += len(chunk)
    text_path.write_text("\n".join(chunks), encoding="utf-8")
    page_map_path.write_text(json.dumps(page_map, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")

print("PASS: copied and extracted 7 supplied PDFs inside the diagnostic run")
