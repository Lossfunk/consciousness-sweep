#!/usr/bin/env python3
"""Extract source-encoded JATS bibliographic facts, never scientific judgments.

Names are taken from article front matter, including author-designated parent
contributor groups. Explicit nonauthor contributors are excluded. The returned
source hash identifies the exact XML bytes; callers still verify article/version
identity and use the normal bibliography normalization dry run before writing.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def local_tag(element: ET.Element) -> str:
    return element.tag.rsplit("}", 1)[-1]


def clean_text(element: ET.Element | None) -> str:
    return " ".join("".join(element.itertext()).split()) if element is not None else ""


def extract_jats_identity(path: Path) -> dict[str, Any]:
    """Read authors encoded individually or in author-designated JATS groups.

    Only article front matter is used. Explicit nonauthor contributor roles are
    excluded even inside author groups. Collaborative authors remain explicit;
    no author identity, initials or unencoded author is guessed.
    """
    root = ET.parse(path).getroot()
    front = next((x for x in root if local_tag(x) == "front"), None)
    meta = next((x for x in front or [] if local_tag(x) == "article-meta"), None)
    if meta is None:
        raise ValueError(f"{path}: article front matter is unavailable")
    parents = {child: parent for parent in meta.iter() for child in parent}
    authors = []
    for element in meta.iter():
        if local_tag(element) != "contrib":
            continue
        explicit_role = (element.get("contrib-type") or "").casefold().strip()
        parent = parents.get(element)
        author_group = False
        while parent is not None and parent is not meta:
            if local_tag(parent) == "contrib-group" and any(
                (parent.get(attribute) or "").casefold().strip() in {"author", "authors"}
                for attribute in ("content-type", "contrib-type")
            ):
                author_group = True
            parent = parents.get(parent)
        if explicit_role != "author" and (explicit_role or not author_group):
            continue
        names = [x for x in element if local_tag(x) in {"name", "string-name", "collab"}]
        if not names:
            raise ValueError(f"{path}: source author contributor has no readable name")
        name = names[0]
        if local_tag(name) == "name":
            pieces = {local_tag(x): clean_text(x) for x in name}
            label = " ".join(pieces.get(key, "") for key in ("given-names", "surname", "suffix")).strip()
        else:
            pieces = None
            label = clean_text(name)
        if not label:
            raise ValueError(f"{path}: source author contributor has an empty name")
        authors.append({"name": label, "kind": local_tag(name), "components_as_encoded": pieces})
    titles = [x for x in meta.iter() if local_tag(x) == "article-title"]
    article_ids = {x.get("pub-id-type", "unknown"): clean_text(x)
                   for x in meta if local_tag(x) == "article-id"}
    abstracts = [x for x in meta if local_tag(x) == "abstract"]
    if not titles or not clean_text(titles[0]):
        raise ValueError(f"{path}: source article title is missing")
    return {"title": clean_text(titles[0]), "authors": [x["name"] for x in authors],
            "authors_as_encoded": authors, "article_ids": article_ids,
            "abstract": "\n\n".join(clean_text(x) for x in abstracts) or None,
            "source_sha256": sha256(path),
            "identity_extraction": "article-front-matter; author contributor or author-designated parent group; namespace aware"}


def assert_source_authors(identity: dict[str, Any], authored_authors: str | list[str] | None) -> None:
    """Refuse the former silent empty-author result when names exist in source."""
    actual = identity.get("authors") or []
    if actual and not authored_authors:
        raise ValueError("source-present authors omitted from verified bibliographic identity")
    if isinstance(authored_authors, list) and authored_authors != actual:
        raise ValueError("verified author array must preserve every source-encoded author in order")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="local article JATS XML")
    args = parser.parse_args()
    try:
        value = extract_jats_identity(args.source)
    except (OSError, ValueError, ET.ParseError) as exc:
        parser.exit(1, f"FAIL: source identity unavailable: {exc}\n")
    print(json.dumps(value, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
