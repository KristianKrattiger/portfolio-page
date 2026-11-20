"""Render the ledger into static pages. Pure functions; returns {path: text}."""
import html
import json
from collections import Counter, OrderedDict

from .validate import STATES, VERIFICATIONS, is_stale, is_unknown

NOT_DONE_STATES = ["IN-PROGRESS", "DESIGN-ONLY", "BLOCKED", "NOT-DONE", "KILLED", "NEGATIVE-RESULT"]
DONE_STATES = ["MEASURED", "BUILT"]
SHAPE_NAMES = {
    "MEASURED": "filled square", "BUILT": "open square", "IN-PROGRESS": "half-filled square",
    "DESIGN-ONLY": "open diamond", "BLOCKED": "barred square", "NOT-DONE": "open circle",
    "KILLED": "cross", "NEGATIVE-RESULT": "down triangle",
}
STATE_GLOSS = {
    "MEASURED": "a number with denominator, dataset, system and date",
    "BUILT": "exists; no qualifying measurement",
    "IN-PROGRESS": "being worked on",
    "DESIGN-ONLY": "on paper only",
    "BLOCKED": "stopped by a named blocker",
    "NOT-DONE": "not built or not run",
    "KILLED": "stopped by a stated criterion",
    "NEGATIVE-RESULT": "tested; did not hold",
}
FACETS = [("project", None), ("state", STATES), ("verification", VERIFICATIONS)]
UNKNOWN_TEXT = "UNKNOWN — author to supply"

e = html.escape


def slug(s):
    return s.lower().replace(" ", "-")


# ---------------------------------------------------------------- primitives

SVG_DEFS = """<svg class="defs" aria-hidden="true" focusable="false" width="0" height="0"><defs>
<symbol id="s-measured" viewBox="0 0 12 12"><rect x="1.5" y="1.5" width="9" height="9" fill="currentColor"/></symbol>
<symbol id="s-built" viewBox="0 0 12 12"><rect x="2" y="2" width="8" height="8" fill="none" stroke="currentColor" stroke-width="1.5"/></symbol>
<symbol id="s-in-progress" viewBox="0 0 12 12"><rect x="2" y="2" width="8" height="8" fill="none" stroke="currentColor" stroke-width="1.5"/><rect x="2" y="2" width="4" height="8" fill="currentColor"/></symbol>
<symbol id="s-design-only" viewBox="0 0 12 12"><polygon points="6,1 11,6 6,11 1,6" fill="none" stroke="currentColor" stroke-width="1.5"/></symbol>
<symbol id="s-blocked" viewBox="0 0 12 12"><rect x="2" y="2" width="8" height="8" fill="none" stroke="currentColor" stroke-width="1.5"/><rect x="2" y="5" width="8" height="2" fill="currentColor"/></symbol>
<symbol id="s-not-done" viewBox="0 0 12 12"><circle cx="6" cy="6" r="4.2" fill="none" stroke="currentColor" stroke-width="1.5"/></symbol>
<symbol id="s-killed" viewBox="0 0 12 12"><path d="M2 2 L10 10 M10 2 L2 10" stroke="currentColor" stroke-width="2" fill="none"/></symbol>
<symbol id="s-negative-result" viewBox="0 0 12 12"><polygon points="1.5,2.5 10.5,2.5 6,10.5" fill="currentColor"/></symbol>
</defs></svg>"""


def state_tag(state):
    s = slug(state)
    return (f'<span class="st st-{s}"><svg class="shape" aria-hidden="true" focusable="false">'
            f'<use href="#s-{s}"/></svg>{e(state)}</span>')


def verif_tag(v):
    cls = "vf-linked" if v == "LINKED" else "vf-author"
    return f'<span class="vf {cls}">{e(v)}</span>'


def stale_tag():
    return '<span class="flag flag-stale" title="as_of older than 90 days at build time">STALE</span>'


def text(v):
    """Render a scalar; UNKNOWN values get the visible signal marker."""
    if v is True:
        return "yes"
    if v is False:
        return "no"
    s = str(v).strip()
    if is_unknown(s):
        label = UNKNOWN_TEXT if s.upper() == "UNKNOWN" else s
        return f'<span class="unknown">{e(label)}</span>'
    return e(s)


class Ctx:
    def __init__(self, site, build_date, entries_by_id):
        self.site = site
        self.build_date = build_date
        self.by_id = entries_by_id

    def stale(self, entry):
        return is_stale(entry["as_of"], self.build_date)


def rel(from_path, to_path):
    depth = from_path.count("/")
    return "../" * depth + to_path


def entry_href(page, entry_id):
    return rel(page, "ledger/index.html") + "#" + entry_id


def entry_home_href(page, entry):
    """Link to the entry's full block on its own project page (same page -> bare #id)."""
    target = f"projects/{entry['project']}/index.html"
    if target == page:
        return "#" + entry["id"]
    return rel(page, target) + "#" + entry["id"]


def project_name(site, key):
    for p in site["projects"]:
        if p["slug"] == key:
            return p["name"]
    return key


# ---------------------------------------------------------------- layout

def nav(page, site):
    items = [("index.html", "Ledger summary"), ("ledger/index.html", "Full ledger"),
             ("not-done/index.html", "Not done, failed, untested")]
    items += [(f"projects/{p['slug']}/index.html", p["name"]) for p in site["projects"]]
    items += [("about/index.html", "About"), ("colophon/index.html", "Colophon")]
    lis = []
    for target, label in items:
        cur = ' aria-current="page"' if target == page else ""
        lis.append(f'<li><a href="{rel(page, target)}"{cur}>{e(label)}</a></li>')
    return "<nav aria-label=\"Site\"><ul>" + "".join(lis) + "</ul></nav>"


def layout(page, title, body, ctx, script=""):
    site = ctx.site
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="referrer" content="no-referrer">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'self'; script-src 'unsafe-inline'; img-src 'self' data:; base-uri 'none'; form-action 'none'">
<title>{e(title)} — {e(site['name'])}</title>
<link rel="stylesheet" href="{rel(page, 'style.css')}">
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
{SVG_DEFS}
<header class="masthead">
<p class="who"><a href="{rel(page, 'index.html')}">{e(site['name'])}</a></p>
{nav(page, site)}
</header>
<main id="main" tabindex="-1">
{body}
</main>
<footer class="foot">
<p class="mono">Built {e(ctx.build_date.isoformat())} from content/ledger.yaml. STALE = as_of older than 90 days at build time.
Machine-readable: <a href="{rel(page, 'ledger.json')}">ledger.json</a>.</p>
</footer>
{script}
</body>
</html>
"""


# ---------------------------------------------------------------- entry blocks

def evidence_html(ev, site):
    if is_unknown(ev):
        return f"<p>{text(ev)} No primary artifact found in the context walked.</p>"
    lis = []
    for it in ev:
        repo = it["repo"]
        sha = str(it.get("sha", ""))
        branch = str(it.get("branch", ""))
        loc = f"{repo} @ {branch} {sha}" if repo not in ("vault", "seed") else (
            "author's notes (vault)" if repo == "vault" else "seed ledger (prior only)")
        path_html = e(it["path"])
        if sha in site.get("linkable_shas", {}).get(repo, []) and repo in site.get("public_repos", {}):
            url = f"{site['public_repos'][repo]}/blob/{sha}/{it['path']}"
            if "(untracked)" not in branch:
                path_html = f'<a href="{e(url)}" rel="noreferrer">{path_html}</a>'
        dirty = ' <span class="flag">worktree dirty</span>' if it.get("dirty") else ""
        note = f' — {e(it["note"])}' if it.get("note") else ""
        lis.append(f'<li><span class="mono">{e(loc)} : {path_html}</span> '
                   f'<span class="tier">tier {e(str(it.get("tier", "?")))}</span>{dirty}{note}</li>')
    return "<ul class=\"ev\">" + "".join(lis) + "</ul>"


def numbers_table(rows, caption):
    head = "".join(f"<th scope=\"col\">{h}</th>" for h in
                   ["Metric", "Value", "n / denominator", "Dataset", "Synthetic", "System", "Date"])
    body = []
    for m in rows:
        cells = [m.get(k, "UNKNOWN") for k in
                 ["metric", "value", "denominator", "dataset", "synthetic", "system", "date"]]
        body.append("<tr>" + "".join(f"<td>{text(c)}</td>" for c in cells) + "</tr>")
    return (f'<div class="scroll" role="region" aria-label="{e(caption)}" tabindex="0">'
            f'<table class="nums"><caption>{e(caption)}</caption><thead><tr>{head}</tr></thead>'
            f'<tbody>{"".join(body)}</tbody></table></div>')


def entry_block(entry, ctx, page, heading="h3"):
    eid = entry["id"]
    tags = [state_tag(entry["state"]), verif_tag(entry["verification"]),
            f'<span class="mono asof">as of {e(entry["as_of"])}</span>']
    if ctx.stale(entry):
        tags.append(stale_tag())
    parts = [f'<article class="entry" id="{e(eid)}">',
             f'<p class="meta"><a class="eid mono" href="{entry_href(page, eid)}">#{e(eid)}</a> '
             f'{" ".join(tags)}</p>',
             f'<{heading} class="claim">{e(entry["claim"])}</{heading}>', "<dl>"]
    if entry.get("verification") == "AUTHOR-REPORTED":
        parts.append('<dt>Verification</dt><dd class="sig">Author-reported, not re-verified. '
                     'No tier-1 artifact containing this claim was opened for this site.</dd>')
    if entry.get("measurements"):
        parts.append("<dt>Measured</dt><dd>" + numbers_table(entry["measurements"], f"Measurements for {eid}") + "</dd>")
    if entry.get("results"):
        parts.append("<dt>Reported numbers</dt><dd>" + numbers_table(entry["results"], f"Numbers for {eid}") + "</dd>")
    if entry.get("reported_result"):
        parts.append(f'<dt>Reported result</dt><dd>{e(entry["reported_result"])} '
                     f'<span class="flag">details not supplied</span></dd>')
    if entry.get("kill_criterion"):
        parts.append(f'<dt>Kill criterion</dt><dd>{e(entry["kill_criterion"])}</dd>')
    if entry.get("blocked_by"):
        parts.append(f'<dt>Blocked by</dt><dd>{e(entry["blocked_by"])}</dd>')
    parts.append(f'<dt>Does not show</dt><dd>{text(entry["does_not_show"])}</dd>')
    if entry.get("disagreement"):
        parts.append(f'<dt>Sources disagree</dt><dd class="sig">{e(entry["disagreement"])}</dd>')
    parts.append(f'<dt>Evidence</dt><dd>{evidence_html(entry["evidence"], ctx.site)}</dd>')
    if entry.get("notes"):
        parts.append(f'<dt>Notes</dt><dd>{e(entry["notes"])}</dd>')
    parts.append("</dl></article>")
    return "\n".join(parts)


# ---------------------------------------------------------------- tables

def ledger_rows(entries, ctx, page, anchors=True):
    rows = []
    for en in entries:
        stale = stale_tag() if ctx.stale(en) else ""
        idattr = f' id="{e(en["id"])}"' if anchors else ""
        rows.append(
            f'<tr{idattr} data-project="{e(en["project"])}" data-state="{e(en["state"])}" '
            f'data-verification="{e(en["verification"])}">'
            f'<td class="mono"><a href="{entry_href(page, en["id"]) if not anchors else "#" + e(en["id"])}">{e(en["id"])}</a></td>'
            f'<td>{e(project_name(ctx.site, en["project"]))}</td>'
            f'<td>{state_tag(en["state"])}</td><td>{verif_tag(en["verification"])} {stale}</td>'
            f'<td class="mono date">{e(en["as_of"])}</td><td>{e(en["claim"])}</td>'
            f'<td>{text(en["does_not_show"])}</td></tr>')
    return "".join(rows)


def ledger_table(entries, ctx, page, caption, anchors=True, table_id=None):
    tid = f' id="{table_id}"' if table_id else ""
    head = "".join(f'<th scope="col">{h}</th>' for h in
                   ["id", "Project", "State", "Verification", "As of", "Claim", "Does not show"])
    return (f'<div class="scroll" role="region" aria-label="{e(caption)}" tabindex="0">'
            f'<table class="ledger"{tid}><caption>{e(caption)}</caption><thead><tr>{head}</tr></thead>'
            f'<tbody>{ledger_rows(entries, ctx, page, anchors)}</tbody></table></div>')


def counts_table(counter, keys, caption, kind):
    rows = []
    for k in keys:
        tag = state_tag(k) if kind == "state" else verif_tag(k)
        gloss = STATE_GLOSS.get(k, "") if kind == "state" else (
            "tier-1 artifact opened at a recorded commit" if k == "LINKED" else "not re-verified")
        rows.append(f'<tr><td>{tag}</td><td class="num mono">{counter.get(k, 0)}</td>'
                    f'<td class="gloss">{e(gloss)}</td></tr>')
    return (f'<table class="counts"><caption>{e(caption)}</caption>'
            f'<thead><tr><th scope="col">Label</th><th scope="col">Entries</th><th scope="col">Means</th></tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table>')


def sort_entries(entries, site):
    order = {p["slug"]: i for i, p in enumerate(site["projects"])}
    sidx = {s: i for i, s in enumerate(STATES)}
    return sorted(entries, key=lambda x: (order.get(x["project"], 99), sidx[x["state"]], x["id"]))


# ---------------------------------------------------------------- pages

def page_home(entries, ctx):
    page = "index.html"
    site = ctx.site
    sc = Counter(x["state"] for x in entries)
    vc = Counter(x["verification"] for x in entries)
    stale_n = sum(1 for x in entries if ctx.stale(x))
    unknown_n = sum(1 for x in entries if is_unknown(x["evidence"]) or is_unknown(x["does_not_show"]))
    disagree_n = sum(1 for x in entries if x.get("disagreement"))
    done_n = sum(sc[s] for s in DONE_STATES)
    nd_n = sum(sc[s] for s in NOT_DONE_STATES)
    paras = "".join(f"<p>{e(p)}</p>" for p in site["work_paragraph"])
    body = f"""
<section class="lead grid">
<h1 class="title">Ledger</h1>
<div class="id-block mono">
<p>{e(site['name'])}</p>
<p>{e(site['line'])}</p>
<p>Contact: {text(site['contact'])}</p>
</div>
</section>
<section class="split grid" aria-label="Counts by state, computed from the ledger">
<div class="half">
<h2>Done side <span class="mono n">{done_n}</span></h2>
{counts_table(sc, DONE_STATES, "Built and measured", "state")}
</div>
<div class="half">
<h2>Not-done side <span class="mono n">{nd_n}</span></h2>
{counts_table(sc, NOT_DONE_STATES, "Not done, blocked, killed, negative", "state")}
<p><a href="{rel(page, 'not-done/index.html')}">Read the not-done side in full</a></p>
</div>
</section>
<section class="grid strip" aria-label="Counts by verification, computed from the ledger">
<div class="half">
{counts_table(vc, VERIFICATIONS, "By verification", "verification")}
</div>
<div class="half mono small">
<p>{stale_tag()} {stale_n} of {len(entries)} entries are older than 90 days.</p>
<p><span class="unknown">UNKNOWN</span> {unknown_n} entries have no evidence pointer or an unknown "does not show".</p>
<p><span class="flag sigflag">Sources disagree</span> on {disagree_n} entries; the site shows the higher tier and the disagreement.</p>
<p>Counts are computed from content/ledger.yaml at build time. Hidden entries are not counted.</p>
</div>
</section>
<section class="prose grid">
<h2>What I work on</h2>
<div class="col">{paras}<p class="mono small">Source: {e(site['work_paragraph_source'])}.</p></div>
</section>
<section>
<h2>Every claim</h2>
{ledger_table(sort_entries(entries, site), ctx, page, "All public ledger entries", anchors=False)}
</section>
"""
    return layout(page, "Ledger", body, ctx)


def untested_built(entries):
    return [x for x in entries if x["state"] == "BUILT" and not x.get("measurements")]


def page_not_done(entries, ctx):
    page = "not-done/index.html"
    site = ctx.site
    blocks = []
    for st in ["NEGATIVE-RESULT", "KILLED", "BLOCKED", "NOT-DONE", "DESIGN-ONLY", "IN-PROGRESS"]:
        group = sort_entries([x for x in entries if x["state"] == st], site)
        inner = "\n".join(entry_block(x, ctx, page) for x in group) or "<p>None.</p>"
        blocks.append(f'<section class="group" id="state-{slug(st)}"><h2>{state_tag(st)} '
                      f'<span class="mono n">{len(group)}</span></h2>'
                      f'<p class="gloss">{e(STATE_GLOSS[st])}</p>{inner}</section>')
    ut = sort_entries(untested_built(entries), site)
    ut_rows = "".join(
        f'<li><a class="mono" href="{entry_href(page, x["id"])}">#{e(x["id"])}</a> {e(x["claim"])}'
        f' <span class="dns">Does not show: {text(x["does_not_show"])}</span></li>' for x in ut)
    body = f"""
<section class="lead grid">
<h1 class="title">Not done</h1>
<p class="dek">Negative results, killed experiments, blockers, things I have not built, designs that are only designs, and built things nobody has measured. Same weight as the done side.</p>
</section>
<nav class="jump mono" aria-label="Jump to group"><ul>
{"".join(f'<li><a href="#state-{slug(s)}">{e(s)}</a></li>' for s in ["NEGATIVE-RESULT", "KILLED", "BLOCKED", "NOT-DONE", "DESIGN-ONLY", "IN-PROGRESS"])}
<li><a href="#untested">BUILT, NOT MEASURED</a></li></ul></nav>
{"".join(blocks)}
<section class="group" id="untested"><h2>{state_tag("BUILT")} but not measured <span class="mono n">{len(ut)}</span></h2>
<p class="gloss">Built entries with no qualifying measurement in the evidence. Full entries are in the <a href="{rel(page, 'ledger/index.html')}">ledger</a> and on project pages.</p>
<ul class="plain">{ut_rows}</ul></section>
"""
    return layout(page, "Not done", body, ctx)


FILTER_SCRIPT = """<script>
(function () {
  var form = document.getElementById('filters');
  var table = document.getElementById('ledger-table');
  if (!form || !table) return;
  form.hidden = false;
  var rows = table.tBodies[0].rows;
  var out = document.getElementById('filter-count');
  function apply() {
    var p = form.project.value, s = form.state.value, v = form.verification.value, n = 0;
    for (var i = 0; i < rows.length; i++) {
      var r = rows[i];
      var show = (!p || r.getAttribute('data-project') === p) &&
                 (!s || r.getAttribute('data-state') === s) &&
                 (!v || r.getAttribute('data-verification') === v);
      r.hidden = !show; if (show) n++;
    }
    out.textContent = n + ' of ' + rows.length + ' entries shown';
  }
  form.addEventListener('change', apply);
  form.addEventListener('reset', function () { setTimeout(apply, 0); });
  apply();
})();
</script>"""


def facet_values(entries, site):
    used = {k: sorted({x[k] for x in entries}) for k in ("project", "state", "verification")}
    out = OrderedDict()
    out["project"] = [p["slug"] for p in site["projects"] if p["slug"] in used["project"]]
    out["state"] = [s for s in STATES if s in used["state"]]
    out["verification"] = [v for v in VERIFICATIONS if v in used["verification"]]
    return out


def facet_label(site, facet, value):
    return project_name(site, value) if facet == "project" else value


def facet_links(page, entries, site):
    out = []
    for facet, values in facet_values(entries, site).items():
        links = " ".join(
            f'<a href="{rel(page, f"ledger/{facet}/{slug(v)}/index.html")}">{e(facet_label(site, facet, v))}</a>'
            for v in values)
        out.append(f"<li><span class=\"mono\">{facet}:</span> {links}</li>")
    return "<ul class=\"facets\">" + "".join(out) + "</ul>"


def page_ledger(entries, ctx):
    page = "ledger/index.html"
    site = ctx.site
    fv = facet_values(entries, site)

    def select(name, values):
        opts = "".join(f'<option value="{e(v)}">{e(facet_label(site, name, v))}</option>' for v in values)
        return (f'<label>{name} <select name="{name}"><option value="">all</option>{opts}</select></label>')

    body = f"""
<section class="lead grid">
<h1 class="title">Full ledger</h1>
<p class="dek">Every public claim, one row each. Each row has a stable anchor: ledger/#id. Full detail for each entry follows the table.</p>
</section>
<section aria-label="Filters">
<form id="filters" class="filters mono" hidden>
{select("project", fv["project"])} {select("state", fv["state"])} {select("verification", fv["verification"])}
<button type="reset">clear</button> <output id="filter-count" aria-live="polite"></output>
</form>
<div class="mono small"><p>Filter pages (work without JavaScript):</p>{facet_links(page, entries, site)}</div>
</section>
{ledger_table(sort_entries(entries, site), ctx, page, "Ledger", anchors=True, table_id="ledger-table")}
<section class="details">
<h2>Entries in full</h2>
{"".join(entry_block(x, ctx, page).replace(f'id="{x["id"]}"', f'id="full-{x["id"]}"', 1) for x in sort_entries(entries, site))}
</section>
"""
    return layout(page, "Full ledger", body, ctx, script=FILTER_SCRIPT)


def page_facet(entries, ctx, facet, value):
    page = f"ledger/{facet}/{slug(value)}/index.html"
    site = ctx.site
    sub = sort_entries([x for x in entries if x[facet] == value], site)
    label = facet_label(site, facet, value)
    body = f"""
<section class="lead grid">
<h1 class="title">{e(label)}</h1>
<p class="dek mono">Ledger filtered by {e(facet)} = {e(value)}: {len(sub)} of {len(entries)} entries. <a href="{rel(page, 'ledger/index.html')}">All entries</a>.</p>
</section>
<div class="mono small">{facet_links(page, entries, site)}</div>
{ledger_table(sub, ctx, page, f"Ledger: {facet} {value}", anchors=False)}
"""
    return layout(page, f"Ledger: {label}", body, ctx)


def page_project(proj, entries, ctx):
    page = f"projects/{proj['slug']}/index.html"
    site = ctx.site
    mine = sort_entries([x for x in entries if x["project"] == proj["slug"]], site)
    by = {x["id"]: x for x in mine}
    what = "".join(
        f'<li>{e(by[i]["claim"])} <a class="mono" href="#{e(i)}">#{e(i)}</a></li>'
        for i in proj["what_it_is_ids"] if i in by)

    def section(title, sid, items, empty):
        inner = "\n".join(entry_block(x, ctx, page) for x in items) or f"<p>{empty}</p>"
        return f'<section class="group" id="{sid}"><h2>{e(title)}</h2>{inner}</section>'

    exists = [x for x in mine if x["state"] in ("BUILT", "IN-PROGRESS")]
    measured = [x for x in mine if x["state"] == "MEASURED"]
    not_built = [x for x in mine if x["state"] in ("NOT-DONE", "DESIGN-ONLY", "BLOCKED")]
    weak = [x for x in mine if x["state"] in ("NEGATIVE-RESULT", "KILLED")]
    dns = "".join(
        f'<li><a class="mono" href="#{e(x["id"])}">#{e(x["id"])}</a> {text(x["does_not_show"])}</li>'
        for x in mine)
    disagree = [x for x in mine if x.get("disagreement")]
    dis_html = "".join(
        f'<li><a class="mono" href="#{e(x["id"])}">#{e(x["id"])}</a> <span class="sig">{e(x["disagreement"])}</span></li>'
        for x in disagree)
    oq = "".join(
        "<li>" + e(q["q"]) + " <span class=\"mono small\">from " +
        ", ".join(f'<a href="{e(entry_home_href(page, ctx.by_id[i]))}">#{e(i)}</a>' for i in q["ids"]) +
        "</span><br><span class=\"small\">Would resolve it: " + e(q["resolves"]) + "</span></li>"
        for q in proj["open_questions"])
    ev_index = OrderedDict()
    for x in mine:
        if is_unknown(x["evidence"]):
            ev_index.setdefault(("—", "—", "—", "no primary artifact found in the context walked"), []).append(x["id"])
            continue
        for it in x["evidence"]:
            key = (it["repo"], str(it.get("branch")), str(it.get("sha")), it["path"])
            ev_index.setdefault(key, []).append(x["id"])
    ev_rows = "".join(
        f'<tr><td class="mono">{e(k[0])}</td><td class="mono">{e(k[1])}</td><td class="mono">{e(k[2])}</td>'
        f'<td class="mono">{e(k[3])}</td><td class="mono">{" ".join(f"<a href=\"#{e(i)}\">#{e(i)}</a>" for i in ids)}</td></tr>'
        for k, ids in ev_index.items())
    repo_links = ""
    pub = [r for r in site.get("public_repos", {}) if any(k[0] == r for k in ev_index)]
    links = [f'<li><a href="{e(site["public_repos"][r])}" rel="noreferrer">{e(site["public_repos"][r])}</a></li>' for r in pub]
    links += [f'<li><a href="{e(l["url"])}" rel="noreferrer">{e(l["label"])}</a></li>'
              for l in site.get("extra_links", {}).get(proj["slug"], [])]
    if links:
        repo_links = "<p>Public locations named in the evidence:</p><ul>" + "".join(links) + "</ul>"
    other = sorted({k[0] for k in ev_index} - set(pub) - {"vault", "seed", "—"})
    if other:
        repo_links += ("<p>Repos with no public URL on this site (visibility not confirmed): "
                       + ", ".join(f'<span class="mono">{e(r)}</span>' for r in other) + ". "
                       + text("UNKNOWN — author to supply") + "</p>")

    body = f"""
<section class="lead grid">
<h1 class="title">{e(proj['name'])}</h1>
<p class="dek">{e(proj['subtitle'])}</p>
</section>
<nav class="jump mono" aria-label="Sections"><ol>
<li><a href="#what">What it is</a></li><li><a href="#exists">What exists</a></li>
<li><a href="#measured">What was measured</a></li><li><a href="#not-measured">What was not measured or built</a></li>
<li><a href="#weak">Known weaknesses and negative results</a></li><li><a href="#open">Open questions</a></li>
<li><a href="#evidence">Evidence</a></li></ol></nav>
<section class="group" id="what"><h2>What it is</h2><ul class="plain">{what}</ul></section>
{section("What exists", "exists", exists, "No BUILT or IN-PROGRESS entries.")}
{section("What was measured", "measured", measured, "No entry meets MEASURED: number, denominator, dataset, synthetic flag, system and date all known. Numbers that fall short are shown with their entries below.")}
<section class="group" id="not-measured"><h2>What was not measured or built</h2>
{"".join(entry_block(x, ctx, page) for x in not_built) or "<p>No NOT-DONE, DESIGN-ONLY or BLOCKED entries.</p>"}
<h3>What each entry's evidence does not show</h3><ul class="plain dnslist">{dns}</ul></section>
<section class="group" id="weak"><h2>Known weaknesses and negative results</h2>
{"".join(entry_block(x, ctx, page) for x in weak) or "<p>No NEGATIVE-RESULT or KILLED entries.</p>"}
{"<h3>Where sources disagree</h3><ul class='plain'>" + dis_html + "</ul>" if dis_html else ""}</section>
<section class="group" id="open"><h2>Open questions</h2><ul class="plain">{oq}</ul></section>
<section class="group" id="evidence"><h2>Evidence</h2>
{repo_links}
<div class="scroll" role="region" aria-label="Evidence index" tabindex="0"><table class="nums">
<caption>Every evidence pointer used on this page</caption>
<thead><tr><th scope="col">Repo / source</th><th scope="col">Branch</th><th scope="col">SHA</th><th scope="col">Path</th><th scope="col">Used by</th></tr></thead>
<tbody>{ev_rows}</tbody></table></div></section>
"""
    return layout(page, proj["name"], body, ctx)


def page_about(entries, ctx):
    page = "about/index.html"
    site = ctx.site
    threads = []
    for p in site["projects"]:
        for q in p["open_questions"]:
            threads.append(f'<li>{e(q["q"])} <span class="mono small">'
                           + ", ".join(f'<a href="{e(entry_home_href(page, ctx.by_id[i]))}">#{e(i)}</a>' for i in q["ids"])
                           + "</span></li>")
    body = f"""
<section class="lead grid">
<h1 class="title">About</h1>
</section>
<section class="prose grid"><h2>Education</h2><div class="col"><p>{e(site['education'])}</p>
<p class="mono small">Source: {e(site['education_source'])}.</p></div></section>
<section class="prose grid"><h2>What I am looking at next</h2><div class="col"><p>{text(site['next'])}</p>
<p>Open threads recorded in the evidence, not a plan:</p><ul class="plain">{"".join(threads)}</ul></div></section>
<section class="prose grid"><h2>Contact</h2><div class="col"><p>{text(site['contact'])}</p></div></section>
"""
    return layout(page, "About", body, ctx)


def page_colophon(entries, ctx, walk, checks, n_hidden):
    page = "colophon/index.html"
    walked = "".join(f"<li><strong>{e(w['what'])}.</strong> {e(w['detail'])}</li>" for w in walk["walked"])
    not_walked = "".join(f"<li>{e(x)}</li>" for x in walk["not_walked"])
    if checks:
        rows = []
        for c in checks["checks"]:
            res = c["result"]
            cls = "ok" if res == "PASS" else "sig"
            rows.append(f'<tr><td>{e(c["name"])}</td><td class="mono">{e(c["command"])}</td>'
                        f'<td class="mono {cls}">{e(res)}</td><td>{e(c["detail"])}</td></tr>')
        checks_html = (f'<p class="mono small">Recorded by verify/verify.py on {e(checks["date"])} against the build '
                       f'immediately before this one; the same script was re-run on this build (see the final report).</p>'
                       f'<div class="scroll" role="region" aria-label="Site checks" tabindex="0"><table class="nums">'
                       f'<caption>The site\'s own ledger: what was checked</caption><thead><tr><th scope="col">Check</th>'
                       f'<th scope="col">Command</th><th scope="col">Result</th><th scope="col">Detail</th></tr></thead>'
                       f'<tbody>{"".join(rows)}</tbody></table></div>')
        nr = "".join(f"<li><strong>{e(x['name'])}:</strong> NOT RUN. {e(x['reason'])}</li>" for x in checks.get("not_run", []))
        checks_html += f"<h3>Not checked</h3><ul class='plain'>{nr}</ul>"
    else:
        checks_html = f"<p>{text('UNKNOWN — checks not yet recorded for this build')}</p>"
    lv = Counter(x["verification"] for x in entries)
    body = f"""
<section class="lead grid">
<h1 class="title">Colophon</h1>
<p class="dek">How this site was built, what it was built from, and what was and was not checked about it.</p>
</section>
<section class="prose grid"><h2>Build</h2><div class="col">
<p>One ledger file (content/ledger.yaml) is the only source of factual sentences. A Python 3 standard-library script validates it and writes static HTML to dist/. The build fails, and writes nothing, if a MEASURED entry lacks its metric, value, denominator, dataset, synthetic flag, system, date or evidence; if a KILLED entry lacks its criterion; if a BLOCKED entry lacks its blocker; if a LINKED entry lacks a tier-1 path with branch and SHA; or if any entry lacks as_of or "does not show". STALE is computed at build time.</p>
<p>No dependencies, no third-party requests, no fonts, no analytics, no cookies. Type is a system stack: Helvetica Neue / Arial for text, the platform monospace for data. Every page works without JavaScript; the only script filters the ledger table, and the same filters exist as plain pages. Served by Python's http.server bound to the loopback interface only.</p>
<p>Entries: {len(entries)} public ({lv.get('LINKED', 0)} LINKED, {lv.get('AUTHOR-REPORTED', 0)} AUTHOR-REPORTED); {n_hidden} hidden by default and not published.</p>
<p>The site was assembled by an AI coding agent working from my repositories and notes, under rules that forbid inventing or rounding numbers. The ledger is the place to check it.</p>
</div></section>
<section class="prose grid"><h2>Context walked</h2><div class="col"><p class="mono small">{e(walk['method'])} Walk date {e(walk['walk_date'])}.</p><ul class="plain">{walked}</ul></div></section>
<section class="prose grid"><h2>Context not walked</h2><div class="col"><p>Absence from this walk is not evidence of absence.</p><ul class="plain">{not_walked}</ul></div></section>
<section><h2>Checks on the site itself</h2>{checks_html}</section>
"""
    return layout(page, "Colophon", body, ctx)


# ---------------------------------------------------------------- json

def ledger_json(entries, ctx, n_hidden):
    out = []
    for x in sort_entries(entries, ctx.site):
        d = OrderedDict((k, x[k]) for k in sorted(x))
        d["stale"] = ctx.stale(x)
        out.append(d)
    doc = OrderedDict([
        ("generated_from", "content/ledger.yaml"),
        ("build_date", ctx.build_date.isoformat()),
        ("stale_rule", "as_of older than 90 days before build_date; month-precision dates count from the 1st"),
        ("hidden_entries_excluded", n_hidden),
        ("counts", OrderedDict([
            ("by_state", OrderedDict((s, sum(1 for x in entries if x["state"] == s)) for s in STATES)),
            ("by_verification", OrderedDict((v, sum(1 for x in entries if x["verification"] == v)) for v in VERIFICATIONS)),
            ("stale", sum(1 for x in entries if ctx.stale(x))),
        ])),
        ("entries", out),
    ])
    return json.dumps(doc, indent=2, ensure_ascii=False) + "\n"


# ---------------------------------------------------------------- entry point

def build_site(all_entries, site, walk, checks, build_date):
    entries = [x for x in all_entries if x["visibility"] == "public"]
    n_hidden = len(all_entries) - len(entries)
    ctx = Ctx(site, build_date, {x["id"]: x for x in entries})
    for p in site["projects"]:
        for i in p["what_it_is_ids"] + [i for q in p["open_questions"] for i in q["ids"]]:
            if i not in ctx.by_id:
                raise ValueError(f"site.json references unknown or hidden entry {i}")
    pages = OrderedDict()
    pages["index.html"] = page_home(entries, ctx)
    pages["not-done/index.html"] = page_not_done(entries, ctx)
    pages["ledger/index.html"] = page_ledger(entries, ctx)
    for facet, values in facet_values(entries, site).items():
        for v in values:
            pages[f"ledger/{facet}/{slug(v)}/index.html"] = page_facet(entries, ctx, facet, v)
    for p in site["projects"]:
        pages[f"projects/{p['slug']}/index.html"] = page_project(p, entries, ctx)
    pages["about/index.html"] = page_about(entries, ctx)
    pages["colophon/index.html"] = page_colophon(entries, ctx, walk, checks, n_hidden)
    pages["ledger.json"] = ledger_json(entries, ctx, n_hidden)
    from .style import CSS
    pages["style.css"] = CSS
    return pages
