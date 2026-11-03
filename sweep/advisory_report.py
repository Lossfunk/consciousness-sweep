"""Researcher-facing delivery from bound saved evidence; no inference or ledger access.

This is a presentation layer, not another classifier. It reads original accepted
answers rather than editable review.json/HTML, and leaves every input unchanged.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import html
import json
import os
from pathlib import Path
import re
import shutil
import tempfile
from urllib.parse import quote

from . import advisory as a
from . import advisory_final as final
from . import advisory_rankings as ranking

FORMAT = "researcher-reading-report-v1"
LABELS = {
    "primary": "Primary reading candidates",
    "support": "Support reading candidates",
    "qualified": "Qualified leads",
    "out": "Not recommended by final review",
    "unresolved": "Final comparison unresolved",
    "review-pending": "Final review incomplete or stale",
    "reference": "Existing reference studies",
    "not-finally-reviewed": "Prospects outside the final review",
    "context": "Context rather than an awareness–use prospect",
    "scientific-unresolved": "Evidence insufficient for a scientific decision",
    "other-assessed": "Other saved assessments",
}
CLAIM_FIELDS = (
    ("comparison", "What the study compared"),
    ("x_and_existence", "What information was available"),
    ("awareness_evidence", "How awareness of that information was assessed"),
    ("downstream_use", "What the person used the information to do"),
    ("supported_claim", "What the results support"),
    ("contribution_reasoning", "Why that finding matters"),
    ("remaining_alternative", "What else could explain it"),
    ("reason_and_vetting_question", "Original reader's vetting note"),
)
STYLE = """
:root{color-scheme:light;--ink:#202b35;--muted:#586875;--line:#d9e1e5;--blue:#155777}
*{box-sizing:border-box}body{margin:0;background:#fafaf7;color:var(--ink);font:17px/1.65 system-ui,sans-serif}
main{max-width:1000px;margin:44px auto;padding:0 28px 60px}h1,h2,h3{line-height:1.25}h1{font-size:2.1rem}
h2{margin-top:2rem}h3{font-size:1.15rem}a{color:var(--blue)}p{max-width:82ch}.meta{font-size:.9rem;color:var(--muted)}
nav{display:flex;flex-wrap:wrap;gap:10px 24px;margin:20px 0}.card,article{border-top:1px solid var(--line);padding:20px 0}
.notice{border-left:3px solid #adbcc7;padding:2px 18px;margin:20px 0;background:#f0f4f4}.evidence{background:#fff;padding:14px 20px}
summary{cursor:pointer;font-weight:600}details{margin:18px 0}li{margin:10px 0}input{font:inherit;padding:9px;width:100%;max-width:600px}
pre{white-space:pre-wrap;overflow-wrap:anywhere;font-size:.8rem}code{overflow-wrap:anywhere}footer{border-top:1px solid var(--line);margin-top:32px;padding-top:16px}
@media(max-width:600px){main{padding:0 18px;margin-top:24px}h1{font-size:1.65rem}}@media print{nav,input,button{display:none}body{background:white}main{margin:0;max-width:none}.card,article{break-inside:avoid}}
"""


def _text(value):
    """Never expose Python/JSON representations as scientific prose."""
    return value.strip() if isinstance(value, str) else ""


def _write(path, text):
    # Explicit LF output also works on the supported Python 3.9 runtime.
    with Path(path).open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(text)


def _names(baseline):
    names = {r["paper_id"]: r["name"] for role in baseline["roles"].values() for r in role.values()}
    names.update({key.removeprefix("REF_"): value for key, value in list(names.items())})
    return names


def _readable(value, names):
    value = _text(value)
    value = re.sub(r"\b(?:REF_)?[DG]\d+(?::C(\d+))?\b",
                   lambda m: names.get(m[0].split(":")[0], m[0].split(":")[0])
                   + (" (claim " + m[1] + ")" if m[1] else ""), value)
    value = re.sub(r"\b(Experiments?|Figures?|Tables?|Appendix|pages?)(?=\d)", r"\1 ", value)
    return value.replace("neither head", "neither the primary nor the support comparison")


def _paragraph(value, names):
    text = _readable(value, names)
    return "<p>" + html.escape(text) + "</p>" if text else ""


def _section(title, text, names):
    return "<h3>" + html.escape(title) + "</h3>" + _paragraph(text, names)


def _list(values, names):
    values = list(dict.fromkeys(_readable(v, names) for v in values if _text(v)))
    return "<ul>" + "".join("<li>" + html.escape(v) + "</li>" for v in values) + "</ul>" if values else ""


def _shell(title, body, *, depth=0):
    base = "../" if depth else ""
    nav = "<nav>" + "".join('<a href="' + base + path + '">' + label + "</a>" for path, label in (
        ("index.html", "Overview"), ("primary.html", "Primary readings"),
        ("support.html", "Support readings"), ("other-papers.html", "Other assessed papers"),
        ("references.html", "Reference studies"))) + "</nav>"
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            + "<title>" + html.escape(title) + "</title><style>" + STYLE + "</style></head><body><main>"
            + nav + body + "</main></body></html>")


def _claim(row, key):
    if not key:
        return None
    prefix = row["paper_id"] + ":C"
    if not key.startswith(prefix) or not key[len(prefix):].isdigit():
        raise ValueError("Focal claim does not belong to its paper")
    index = int(key[len(prefix):]) - 1
    claims = row["assessment"].get("claims", [])
    if index < 0 or index >= len(claims):
        raise ValueError("Focal claim is absent from the saved assessment")
    return claims[index]


def _main_claim(row, judgment):
    if judgment:
        role = "primary" if judgment["recommended_role"] == "primary" else "support"
        found = _claim(row, judgment[role]["supported_claim_key"])
        if found:
            return found
    claims = row["assessment"].get("claims", [])
    return next((c for c in claims if c.get("decision") == "prospect"), claims[0] if claims else {})


def _bibliography(row):
    authors = row.get("authors")
    parts = [authors] if isinstance(authors, str) and authors.strip() else []
    if row.get("year") is not None:
        parts.append(str(row["year"]))
    if row.get("publication_status"):
        parts.append(str(row["publication_status"]))
    body = '<p class="meta">' + html.escape(" · ".join(parts)) + "</p>" if parts else ""
    doi = a._doi(row.get("doi"))
    if doi:
        body += '<p><a href="https://doi.org/' + html.escape(quote(doi, safe="/"), quote=True) + '">Open article</a></p>'
    return body


def _evidence(claim, names, *, expanded=False):
    items = []
    for point in claim.get("decisive_evidence", []):
        if not isinstance(point, dict):
            continue
        observation = _readable(point.get("observation"), names)
        units = ", ".join(str(x).replace("page:", "page ") for x in point.get("unit_ids", []))
        location = " · ".join(x for x in (units, _text(point.get("location_detail"))) if x)
        items.append("<li>" + html.escape(observation) + ('<br><span class="meta">' + html.escape(location) + "</span>" if location else "") + "</li>")
    if not items:
        return "<p>Located result details were not supplied in this saved claim.</p>"
    if expanded:
        return '<div class="evidence"><h3>The reported observations</h3><ul>' + "".join(items) + "</ul></div>"
    return '<details class="evidence"><summary>Reported results and where to find them</summary><ul>' + "".join(items) + "</ul></details>"


def _comparison(head, role, row, baseline, names, title=None):
    refid = head["closest_reference"]
    ref = baseline["papers"].get(refid)
    title = title or ("Why it belongs on the primary reading list" if role == "primary" else "Why it is useful as support")
    body = _section(title, head["reason"], names)
    if ref:
        body += '<p><strong>Compared with <a href="../references.html#' + html.escape(refid, quote=True) + '">' + html.escape(names[refid]) + "</a>.</strong></p>"
        body += '<details><summary>Reference background: separately recorded claims and limits</summary><p>The reviewer’s reason above defines the comparison. The following are the reference paper’s saved claims; no single claim is automatically selected as its exact comparator.</p>'
        for number, reference_claim in enumerate(ref["assessment"].get("claims", []), 1):
            body += "<h3>Reference claim " + str(number) + " (" + html.escape(str(reference_claim.get("decision", "unresolved"))) + ")</h3>"
            body += _paragraph(reference_claim.get("supported_claim"), names)
            body += _paragraph(reference_claim.get("comparison"), names)
            body += _paragraph(reference_claim.get("remaining_alternative"), names)
        body += "</details>"
    else:
        body += "<p>The saved review did not resolve a reference comparator.</p>"
    focal = _claim(row, head["supported_claim_key"])
    if focal and focal.get("decision") != "prospect":
        body += '<div class="notice"><p>The final reviewer treats this claim as useful for the reading list, while the original scientific assessment called it ' + html.escape(str(focal.get("decision"))) + '. Both judgments are retained; this report does not resolve their disagreement.</p></div>'
    return body


def _brief(row, judgment, category):
    reason = _text(row["assessment"].get("paper_reason"))
    if judgment:
        return _text(judgment.get("recommendation_reason"))
    if category == "reference":
        return "This is already part of the comparison reference set, rather than a new discovery. " + reason
    if category == "review-pending":
        return "A final review was selected but has no current accepted answer. This is not a rejection. " + reason
    if category == "not-finally-reviewed":
        return "The scientific reading retained this prospect, but it was outside the accepted final review. It has not been disqualified. " + reason
    return reason or "The saved assessment does not supply a paper-level reason; inspect its claims and evidence gaps."


def _paper_page(row, judgment, category, baseline, names, provenance, procedure=None):
    title = row.get("title") or row["paper_id"]
    body = "<h1>" + html.escape(title) + "</h1>" + _bibliography(row)
    body += "<p><strong>" + html.escape(LABELS[category]) + "</strong></p>"
    body += ('<p class="meta">Study account: the original scientific reading. Reading-list recommendation: the later independent final review. The two judgments remain separate.</p>' if judgment else
             '<p class="meta">Original scientific assessment. This paper has no current accepted final reading-list judgment.</p>')
    if row["assessment"].get("assessment_status") != "complete":
        body += '<div class="notice"><p>This saved scientific assessment is incomplete. Missing evidence is not a demonstrated negative result.</p></div>'
    focal = _main_claim(row, judgment)
    body += "<h2>What participants saw and did</h2>"
    procedure = procedure or (judgment.get("procedure") if judgment else None)
    if procedure:
        body += _paragraph(procedure, names)
    else:
        body += _paragraph(focal.get("x_and_existence"), names)
        body += _paragraph(focal.get("downstream_use"), names)
        if not _text(focal.get("x_and_existence")) and not _text(focal.get("downstream_use")):
            body += "<p>The saved extraction does not reconstruct this procedure; consult the source before interpreting the result.</p>"
    body += _section("How awareness of that information was assessed", focal.get("awareness_evidence"), names)
    body += _section("What was compared", focal.get("comparison"), names)
    body += "<h2>What happened</h2>" + _paragraph(focal.get("supported_claim"), names) + _evidence(focal, names, expanded=True)
    if judgment:
        body += _paragraph(judgment["recommendation_reason"], names)
        if category == "primary":
            body += _comparison(judgment["primary"], "primary", row, baseline, names)
        elif category == "support":
            body += _comparison(judgment["support"], "support", row, baseline, names)
            body += _comparison(judgment["primary"], "primary", row, baseline, names,
                                "What prevents a primary recommendation")
            other = _claim(row, judgment["primary"]["supported_claim_key"])
            if other and other != focal:
                body += '<p>The primary comparison concerns a separate claim:</p>' + _paragraph(other.get("supported_claim"), names)
        else:
            body += _section("Why it is not in the main reading lists", judgment["recommendation_reason"], names)
            for role in ("primary", "support"):
                body += _section(role.title() + " comparison", judgment[role]["reason"], names)
        qualifications = judgment["primary"]["remaining_qualifications"] + judgment["support"]["remaining_qualifications"]
        body += "<h3>Qualifications to keep with this recommendation</h3>" + _paragraph(focal.get("remaining_alternative"), names) + _list(qualifications, names)
    else:
        title = "Why it was not retained as a prospect" if category == "context" else "Why it remains outside the final reading lists"
        body += _section(title, _brief(row, judgment, category), names)
    body += '<h2>Original reader assessment and additional claims</h2><p>The scientific label “prospect” means a contribution retained for review; it is not a primary or support rank.'
    body += (' Original vetting notes below predate the final recommendation and may differ from it.</p>' if judgment else
             ' The notes below are the original scientific reading; no final role was assigned here.</p>')
    for index, claim in enumerate(row["assessment"].get("claims", []), 1):
        # Each original claim stays separate; no cross-experiment construction.
        content = "".join(_section(label, claim.get(key), names) for key, label in CLAIM_FIELDS)
        content += _evidence(claim, names)
        label = "Claim " + str(index) + ": " + str(claim.get("decision", "unresolved"))
        body += '<article id="claim-' + str(index) + '"><details><summary>' + html.escape(label) + "</summary>" + content + "</details></article>"
    body += "<h2>Missing material and remaining reading limitations</h2>"
    gaps = row["assessment"].get("reading_gaps", []) + row.get("acquisition_gaps", [])
    body += _list([g for g in gaps if isinstance(g, str)], names)
    nontext = [g for g in gaps if not isinstance(g, str)]
    if nontext:
        body += '<details><summary>Structured source-gap records</summary><pre>' + html.escape(json.dumps(nontext, ensure_ascii=False, indent=2)) + "</pre></details>"
    if not gaps:
        body += "<p>No additional gaps are recorded here; this does not independently establish source completeness.</p>"
    body += '<details><summary>Evidence and execution audit</summary><p>Paper record: ' + html.escape(row["paper_id"]) + ". Saved assessment: " + html.escape(str(row["assessment"].get("paper_decision"))) + ".</p>"
    body += '<p>The narrative arranges saved extraction and reviewer text; it adds no model call or new scientific decision.</p><pre>' + html.escape(json.dumps(provenance, ensure_ascii=False, indent=2)) + "</pre></details>"
    return _shell(row.get("title") or row["paper_id"], body, depth=1)


def _job_state(root, entry, rows, policy):
    directory, job = a._job(root, entry)
    fresh = a._current(job, rows, policy)
    if (directory / "receipt.json").exists():
        receipt = a._receipt(directory)
        effective = a._effective_receipt(directory, receipt, a._audit_record(directory, receipt), current=fresh)
        state = "current" if effective["accepted"] else effective["status"]
    else:
        receipt = None
        terminal = a._read(directory / "codex-terminal.json") if (directory / "codex-terminal.json").exists() else None
        state = "stale" if not fresh else terminal["status"] if terminal else "dispatched-outcome-pending" if (directory / "dispatch.json").exists() else "prepared"
    evidence = {"workspace": str(root), "job_id": job["job_id"], "state": state, "targets": job["targets"],
                "request_sha256": job["binding_sha256"], "requested_profile": job["profile"],
                "usage": receipt.get("usage") if receipt else None,
                "reported_identity": receipt.get("reported_identity") if receipt else None,
                "identity_verification": receipt.get("identity_verification") if receipt else "unverified"}
    if (directory / "dispatch.json").exists():
        evidence["dispatch_sha256"] = a._bytes_hash((directory / "dispatch.json").read_bytes())
    if receipt:
        evidence.update({k: receipt[k] for k in ("receipt_sha256", "answer_sha256", "execution_sha256")})
    return directory, job, state, evidence


def collect(suggestions, final_reviews):
    """Validate original inputs and partition every assessed paper exactly once."""
    if not final_reviews:
        raise ValueError("Supply the final-review workspace, even if its work is incomplete")
    root, manifest, baseline, policy, eligible, unavailable = final.candidates(suggestions)
    export = Path(manifest["export_path"]).resolve()
    raw = export.read_bytes(); rows = a._parse_rows(raw)
    assessed = {pid: row for pid, row in rows.items() if isinstance(row.get("assessment"), dict)}
    judgments, final_selected, evidence, origins = {}, set(), [], {}
    input_roots = [root]
    seen_jobs = {}
    final_policy_hash = None
    for workspace in final_reviews:
        froot, fm = a._manifest(workspace)
        if froot in input_roots:
            raise ValueError("Supply each distinct final-review workspace only once")
        input_roots.append(froot)
        if (fm.get("final_review_layout") != final.LAYOUT or fm["profile"] != final.PROFILE
                or Path(fm["export_path"]).resolve() != export
                or Path(fm["suggestion_workspace"]).resolve() != root
                or fm["suggestion_manifest_sha256"] != manifest["manifest_sha256"]
                or fm["reference_baseline_sha256"] != manifest["reference_baseline_sha256"]
                or fm["policy_sha256"] != manifest["policy_sha256"]):
            raise ValueError("Report inputs must share the same run/export, suggestion pass, profile and baseline")
        if final_policy_hash is not None and fm["final_policy_sha256"] != final_policy_hash:
            raise ValueError("Cannot combine different final-review policies")
        final_policy_hash = fm["final_policy_sha256"]
        final_selected.update(fm["selected"])
        for entry in fm["jobs"]:
            directory, job, state, proof = _job_state(froot, entry, rows, policy)
            identity = (directory.resolve(), job["binding_sha256"])
            if job["job_id"] in seen_jobs:
                if identity != seen_jobs[job["job_id"]]:
                    raise ValueError("Reused job ID refers to different final-review evidence")
                continue  # Identical reused job, not a second scientific judgment.
            seen_jobs[job["job_id"]] = identity; evidence.append(proof)
            if state != "current":
                continue
            answer = a._read(directory / "answer.json")
            a._validate_answer(job, answer, a._read(directory / "schema.json"))
            for pid, judgment in answer["result"]["papers"].items():
                if pid in judgments:
                    raise ValueError("Overlapping accepted final judgments; preserve both and resolve separately")
                if pid not in eligible or pid not in assessed:
                    raise ValueError("Final recommendation has no current bound prospect evidence")
                judgments[pid] = judgment; origins[pid] = proof
    known = {a._doi(p.get("doi")) for p in baseline["papers"].values()}
    categories = {}
    for pid, row in assessed.items():
        decision = row["assessment"].get("paper_decision")
        if pid in judgments:
            category = judgments[pid]["recommended_role"]
        elif decision == "context":
            category = "context"
        elif decision == "unresolved":
            category = "scientific-unresolved"
        elif pid in final_selected:
            category = "review-pending"
        elif a._doi(row.get("doi")) and a._doi(row.get("doi")) in known:
            category = "reference"
        elif decision == "prospect":
            category = "not-finally-reviewed"
        else:
            category = "other-assessed"
        categories[pid] = category
    if export.read_bytes() != raw:
        raise ValueError("Published export changed during report assembly; use a quiet snapshot")
    sources = [{"workspace": str(p), "manifest_sha256": a._manifest(p)[1]["manifest_sha256"]} for p in input_roots]
    return {"rows": assessed, "judgments": judgments, "categories": categories, "baseline": baseline,
            "origins": origins, "input_roots": input_roots, "export_bytes": raw,
            "provenance": {"format": FORMAT, "export_path": str(export), "export_sha256": a._bytes_hash(raw),
                "suggestion_workspace": str(root), "inputs": sources, "final_jobs": evidence,
                "assessed_papers": len(assessed), "export_rows_without_assessment": len(rows) - len(assessed),
                "accepted_final_papers": len(judgments), "selected_final_papers": len(final_selected),
                "category_counts": dict(Counter(categories.values())), "unavailable_suggestion_jobs": unavailable,
                "new_model_calls": 0, "source_retrievals": 0, "scientific_run_mutations": 0,
                "meaning": "Saved scientific evidence and advisory recommendations for human reading, not accepted scientific roles"}}


def _card(pid, data, names, *, brief=False):
    row = data["rows"][pid]; judgment = data["judgments"].get(pid); category = data["categories"][pid]
    body = '<article class="card" data-search="' + html.escape((row.get("title", "") + " " + pid + " " + (row.get("doi") or "")).lower(), quote=True) + '"><h3><a href="papers/' + pid + '.html">' + html.escape(row.get("title") or pid) + "</a></h3>"
    if not brief:
        procedure = data.get("procedures", {}).get(pid) or (judgment.get("procedure") if judgment else None)
        body += "<p><strong>The task.</strong> " + html.escape(_readable(procedure or _main_claim(row, judgment).get("downstream_use"), names)) + "</p>"
        body += _paragraph(_main_claim(row, judgment).get("supported_claim"), names)
    body += _paragraph(_brief(row, judgment, category), names)
    if judgment and category == "support":
        body += "<p><strong>Short of primary:</strong> " + html.escape(_readable(judgment["primary"]["reason"], names)) + "</p>"
    if judgment:
        role = "primary" if category == "primary" else "support"
        reference = judgment[role]["closest_reference"]
        if reference:
            body += "<p class=\"meta\">Compared with " + html.escape(names[reference]) + ".</p>"
    return body + "</article>"


def _editorial_notes(path, data):
    if path is None:
        return {}, None
    raw = Path(path).read_bytes(); value = a._decode(raw.decode("utf-8"))
    source = a._manifest(data["provenance"]["suggestion_workspace"])[1]
    if (value.get("format") != "researcher-editorial-notes-v1"
            or Path(value["export_path"]).resolve() != Path(data["provenance"]["export_path"])
            or value.get("suggestion_manifest_sha256") != source["manifest_sha256"]):
        raise ValueError("Editorial notes must belong to this exact run/export and suggestion pass")
    result = {}
    for pid, note in value["papers"].items():
        if (pid not in data["judgments"] or note["row_sha256"] != a._hash(data["rows"][pid])
                or note["judgment_sha256"] != a._hash(data["judgments"][pid])):
            raise ValueError("Editorial note is stale or has no accepted bound review")
        if not _text(note.get("procedure")):
            raise ValueError("Editorial procedure is empty")
        result[pid] = note["procedure"]
    return result, {"path": str(Path(path).resolve()), "sha256": a._bytes_hash(raw),
                    "requested_editor_profile": value.get("requested_editor_profile"),
                    "provider_identity": value.get("provider_identity"),
                    "meaning": "Separately preserved editorial wording; no new scientific judgment"}


def write_report(suggestions, final_reviews, workspace, *, narratives=None):
    data = collect(suggestions, final_reviews)
    input_provenance_sha256 = a._hash(data["provenance"])
    data["procedures"], editorial = _editorial_notes(narratives, data)
    data["provenance"]["editorial_notes"] = editorial
    missing = [pid for pid, q in data["judgments"].items() if not _text(q.get("procedure")) and pid not in data["procedures"]]
    data["provenance"]["legacy_recommendations_without_procedure_lead"] = missing
    destination = Path(workspace).absolute()
    resolved = destination.resolve()
    export = Path(data["provenance"]["export_path"]).resolve()
    protected = [p.resolve() for p in data["input_roots"]] + [export]
    if narratives is not None:
        protected.append(Path(narratives).resolve())
    # An external release may read a paused run, but must never publish into it.
    protected += [p for p in export.parents if (p / "execution_plan.json").exists() or (p / "state.sqlite3").exists()]
    if (destination.exists() or destination.is_symlink() or
            any(resolved == p or p in resolved.parents or resolved in p.parents for p in protected)):
        raise ValueError("Use a new report directory separate from inputs and the scientific run")
    names = _names(data["baseline"])
    ordered = sorted(data["rows"], key=lambda pid: ((data["rows"][pid].get("title") or pid).casefold(), pid))
    lists = {cat: [pid for pid in ordered if data["categories"][pid] == cat] for cat in LABELS}
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=".reading-report-", dir=str(destination.parent)))
    try:
        (temporary / "papers").mkdir()
        for pid in ordered:
            row = data["rows"][pid]
            proof = {"export": str(export), "row_sha256": a._hash(row), "source_generation": row.get("source_generation"),
                     "reader_job": row.get("reader_job"), "final_review": data["origins"].get(pid)}
            page = _paper_page(row, data["judgments"].get(pid), data["categories"][pid], data["baseline"], names, proof,
                               procedure=data["procedures"].get(pid))
            _write(temporary / "papers" / (pid + ".html"), page)
        notice = '<div class="notice"><p>These recommendations compare saved study evidence with the three primary and eight support references. A primary candidate is comparable in a particular contribution, not necessarily equal to every primary. Support can be useful without primary-grade controls. The original assessments, limitations and disagreements remain intact.</p></div>'
        intro = "<h1>Studies to read</h1><p>Start with the primary and support candidates. Each study page explains what was tested, what was found, why it belongs in that reading list, and what still limits the interpretation.</p>" + notice
        counts = data["provenance"]["category_counts"]
        intro += "<p><strong>" + str(counts.get("primary", 0)) + " primary candidates · " + str(counts.get("support", 0)) + " support candidates.</strong></p>"
        intro += "<p>This report accounts for all " + str(len(ordered)) + " assessed papers in the bound published export. The independent final review has current accepted answers for " + str(len(data["judgments"])) + " of " + str(data["provenance"]["selected_final_papers"]) + " selected papers. Other prospects remain explicitly outside that review; missing evidence is not rejection.</p>"
        if missing:
            intro += '<div class="notice"><p>' + str(len(missing)) + ' accepted legacy reviews lack a concise procedure opening. Their original analytical study accounts remain available; no additional model work was automatically commissioned to rewrite them.</p></div>'
        intro += '<details><summary>Terms used in the saved study accounts</summary><p>X is the information being studied; Y is the distinct use made of it. Primary and support are reading recommendations. “Prospect” is the earlier scientific screening label. CORE concerns eligibility for citation expansion, a separate decision. Numbered claims remain separate findings from the same paper; their labels do not rank strength.</p></details>'
        for role in ("primary", "support"):
            intro += "<h2>" + LABELS[role] + " (" + str(len(lists[role])) + ")</h2>"
            intro += '<p><a href="' + role + '.html">Full study descriptions, reference comparisons and limitations</a></p><ul>'
            intro += ''.join('<li><a href="papers/' + pid + '.html">' + html.escape(data["rows"][pid].get("title") or pid) + '</a></li>' for pid in lists[role]) + '</ul>'
        intro += '<h2>Other assessed papers and optional follow-ups</h2><p><a href="other-papers.html">Other assessed papers: brief reasons and full evidence</a></p>'
        if lists["qualified"]:
            intro += '<p>Lower-priority optional follow-ups: <a href="other-papers.html#qualified">' + str(len(lists["qualified"])) + ' qualified leads with unresolved evidential or interpretive gaps</a>. These are outside the primary and support reading lists.</p>'
        intro += '<footer><p>Prepared from saved extractions and accepted review answers. This report introduces no new inference or source verification. Alphabetical lists do not imply a strength ranking. <a href="provenance.json">Coverage and execution evidence</a>.</p></footer>'
        _write(temporary / "index.html", _shell("Studies to read", intro))
        for role in ("primary", "support"):
            body = "<h1>" + LABELS[role] + " (" + str(len(lists[role])) + ")</h1>" + notice
            body += "".join(_card(pid, data, names) for pid in lists[role])
            _write(temporary / (role + ".html"), _shell(LABELS[role], body))
        others = "<h1>Other full-text-assessed papers</h1><p>These entries explain the saved decisions. Contextual papers lacked a qualifying awareness–use contribution; unresolved papers lacked evidence for a decision. A prospect outside final review has not been disqualified.</p>"
        others += '<label for="filter">Find a title, DOI or paper ID</label><br><input id="filter" type="search" placeholder="Search assessed papers">'
        for cat in LABELS:
            if cat in ("primary", "support") or not lists[cat]:
                continue
            others += '<section id="' + html.escape(cat, quote=True) + '"><h2>' + html.escape(LABELS[cat]) + " (" + str(len(lists[cat])) + ")</h2>" + "".join(_card(pid, data, names, brief=True) for pid in lists[cat]) + "</section>"
        others += "<script>document.getElementById('filter').addEventListener('input',function(){let q=this.value.toLowerCase();document.querySelectorAll('[data-search]').forEach(el=>el.hidden=!el.dataset.search.includes(q));});</script>"
        _write(temporary / "other-papers.html", _shell("Other assessed papers", others))
        refs = "<h1>The reference studies</h1><p>These are the fixed three-primary and eight-support evaluator snapshots used for the comparisons. They are the comparison standard, rather than additional discoveries or newly reread sources.</p>"
        for role, records in data["baseline"]["roles"].items():
            refs += "<h2>" + role.title() + " references</h2>"
            for ref in records.values():
                row = data["baseline"]["papers"][ref["paper_id"]]
                refs += '<article id="' + html.escape(ref["paper_id"], quote=True) + '"><h2>' + html.escape(ref["name"]) + "</h2>" + _bibliography(row)
                for index, claim in enumerate(row["assessment"].get("claims", []), 1):
                    refs += "<h3>Reference claim " + str(index) + "</h3>" + "".join(_section(label, claim.get(key), names) for key, label in CLAIM_FIELDS) + _evidence(claim, names)
                refs += "</article>"
        _write(temporary / "references.html", _shell("Reference studies", refs))
        from .advisory_markdown import write_markdown
        data["provenance"]["markdown"] = write_markdown(temporary)
        provenance = dict(data["provenance"], created_at=datetime.now(timezone.utc).isoformat(),
                          renderer_sha256=a._bytes_hash(Path(__file__).read_bytes()))
        report = {"format": FORMAT, "reading_lists": lists, "coverage": provenance,
                  "papers": [{"paper_id": pid, "title": data["rows"][pid].get("title"), "category": data["categories"][pid],
                              "summary": _brief(data["rows"][pid], data["judgments"].get(pid), data["categories"][pid]),
                              "row_sha256": a._hash(data["rows"][pid]), "page": "papers/" + pid + ".html", "markdown_page": "papers/" + pid + ".md"} for pid in ordered]}
        a._once(temporary / "report.json", report)
        provenance["files"] = {p.relative_to(temporary).as_posix(): a._bytes_hash(p.read_bytes()) for p in sorted(temporary.rglob("*")) if p.is_file()}
        a._once(temporary / "provenance.json", provenance)
        if (export.read_bytes() != data["export_bytes"] or any(a._manifest(x["workspace"])[1]["manifest_sha256"] != x["manifest_sha256"] for x in provenance["inputs"])
                or (editorial and a._bytes_hash(Path(editorial["path"]).read_bytes()) != editorial["sha256"])):
            raise ValueError("Bound inputs changed before publication; no report published")
        # Receipt/answer/log files are bound separately from their workspace's
        # manifest. Recheck those too, including upstream acceptance and freshness.
        if a._hash(collect(suggestions, final_reviews)["provenance"]) != input_provenance_sha256:
            raise ValueError("Review evidence changed before publication; no report published")
        if destination.exists() or destination.is_symlink():
            raise ValueError("Another writer created the report destination")
        os.rename(temporary, destination)
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)
    return {"report": str(destination / "index.html"), "markdown": str(destination / "README.md"), "assessed_papers": len(ordered),
            "reading_list_counts": {role: len(lists[role]) for role in ("primary", "support", "qualified")},
            "category_counts": counts, "accepted_final_papers": len(data["judgments"]),
            "new_model_calls": 0, "scientific_run_mutations": 0}
