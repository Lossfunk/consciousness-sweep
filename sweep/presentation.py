"""Human-readable views of stored claims; never an additional classifier."""
import json
from html import escape
from urllib.parse import quote

STYLE = """body{font:16px/1.55 system-ui,sans-serif;max-width:960px;margin:40px auto;padding:0 24px;color:#18212a;background:#fafaf7}h1{font-size:28px;line-height:1.2}h2{font-size:21px;margin-top:32px}dt{font-weight:650;margin-top:14px}dd{margin:4px 0 14px}a{color:#125578}article{border-top:1px solid #ccc;margin-top:26px;padding-top:16px}.meta{color:#52616b}input{font:inherit;padding:8px;margin:12px 0;width:85%}.tag{font-size:14px;color:#52616b}li{margin:8px 0}pre{white-space:pre-wrap}button{font:inherit;padding:8px}mark{background:#ffedb0}"""


def shell(title, body):
    return '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>' + escape(title) + '</title><style>' + STYLE + '</style><body>' + body + '</body></html>'


def depth_limit_notice(discovery):
    """Show the commissioned search boundary without implying saturation."""
    coverage = discovery.get("ranked_query_coverage", {})
    completed = coverage.get("completed_windows", 0)
    notice = ""
    if completed:
        notice = '<p class="meta" id="ranked-query-scope">' + escape("Ranked search windows: %s complete; %s returned encounters; %s windows truncated by the frozen result cap. A completed ranked window is not a saturation claim; hit totals overlap across windows." % (completed, coverage.get("returned_encounters", 0), coverage.get("truncated_windows", 0))) + '</p>'
    limit = discovery.get("max_citation_depth")
    if limit is None:
        return notice
    count = discovery.get("depth_limited_obligations", 0)
    text = "Citation depth limit: %s hops from each seed or independent query root. " % limit
    text += "Papers at the limit still receive normal screening and reading. "
    if count:
        text += "%s further citation directions are deferred by this limit; the search has not reached scientific saturation. " % count
    else:
        text += "No further citation directions are currently deferred by this limit. "
    if discovery.get("depth_unresolved_obligations"):
        text += "Some citation directions also await verified depth provenance. "
    return notice + '<p class="meta" id="citation-depth-scope">' + escape(text) + '</p>'


def paper_page(paper):
    assessment = paper["assessment"]
    body = '<a href="../index.html">Reading queue</a><h1>' + escape(paper["title"]) + '</h1>'
    body += '<p class="meta">' + escape(paper["paper_id"] + ' · ' + assessment["paper_decision"] + ' · ' + assessment["assessment_status"] + ' · human: ' + paper.get("human_decision", "pending")) + '</p>'
    if paper.get("doi"):
        body += '<p><a href="https://doi.org/' + quote(paper["doi"], safe='/') + '">Open article by DOI</a></p>'
    body += '<p>' + escape(assessment["paper_reason"]) + '</p>'
    packet = paper.get("retrieval", {}).get("packet", {})
    gaps = packet.get("acquisition_gaps", [])
    if gaps:
        body += '<h2>Acquisition limitations</h2><ul>'
        for gap in gaps:
            body += '<li>' + escape(gap if isinstance(gap, str) else json.dumps(gap, ensure_ascii=False, sort_keys=True)) + '</li>'
        body += '</ul>'
    relations = {key: paper[key] for key in ("version_relations", "relation", "version_of", "possible_duplicates") if paper.get(key)}
    if relations:
        body += '<h2>Related versions / possible copies</h2><p>' + escape(json.dumps(relations, ensure_ascii=False, sort_keys=True)) + '</p><p>Resolve these relationships before treating copies as independent evidence.</p>'
    if paper.get("publication_status"):
        body += '<p class="meta">Publication status: ' + escape(str(paper["publication_status"])) + '</p>'
    for claim in assessment["claims"]:
        body += '<article><h2>' + escape(claim["comparison"]) + '</h2><dl>'
        body += '<dt>Claim disposition</dt><dd>' + escape(claim["decision"]) + '</dd>'
        for key, label in (("supported_claim", "Supported claim"), ("x_and_existence", "X and evidence it exists"),
                           ("awareness_evidence", "Awareness evidence"), ("downstream_use", "How Y uses X"),
                           ("contribution_reasoning", "Why this contributes"), ("remaining_alternative", "Remaining alternative"),
                           ("reason_and_vetting_question", "What to vet")):
            body += '<dt>' + label + '</dt><dd>' + escape(claim[key]) + '</dd>'
        body += '<dt>Decisive evidence</dt><dd><ul>'
        for item in claim["decisive_evidence"]:
            body += '<li>' + escape(item["observation"]) + '<br><span class="tag">' + escape(item["asset_id"] + ': ' + ', '.join(item["unit_ids"]) + ' · ' + item["location_detail"]) + '</span></li>'
        body += '</ul></dd></dl></article>'
    if assessment["reading_gaps"] or assessment["unread_source_units"]:
        body += '<h2>Reading limitations</h2><ul>'
        for gap in assessment["reading_gaps"]:
            body += '<li>' + escape(gap) + '</li>'
        for gap in assessment["unread_source_units"]:
            body += '<li>' + escape(gap["asset_id"] + ': ' + ', '.join(gap["unit_ids"]) + ' — ' + gap["reason"]) + '</li>'
        body += '</ul>'
    body += '<p class="meta">These are the stored reader claims. Human decisions remain separate; this view does not certify primary eligibility or scientific stopping.</p>'
    return shell(paper["title"], body)


def index_row(paper, in_queue):
    assessment = paper["assessment"]
    return '<li data-queue="' + ('yes' if in_queue else 'no') + '"><a href="papers/' + escape(paper["paper_id"]) + '.html">' + escape(paper["title"]) + '</a><br><span class="tag">' + escape(paper["paper_id"] + ' · ' + assessment["paper_decision"] + ' · human: ' + paper.get("human_decision", "pending")) + '</span><p>' + escape(assessment["paper_reason"]) + '</p></li>\n'


INDEX_START = '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Prospect reading queue</title><style>' + STYLE + '</style><body><h1>Prospect reading queue</h1><p>Source-grounded decision trails for human vetting. Partial readings and uncertainty remain visible. Context and human-declined records are available under “Show all”.</p><button id="all">Show all</button><br><input id="search" aria-label="Filter titles and reasons" placeholder="Filter titles and reasons"><ul id="papers">\n'
INDEX_END = '''</ul><script>let all=false;const apply=()=>{let q=document.querySelector('#search').value.toLowerCase();for(let e of document.querySelectorAll('#papers>li'))e.hidden=(!all&&e.dataset.queue!=='yes')||!e.textContent.toLowerCase().includes(q)};document.querySelector('#all').onclick=()=>{all=!all;document.querySelector('#all').textContent=all?'Show queue':'Show all';apply()};document.querySelector('#search').oninput=apply;apply();</script></body></html>'''
