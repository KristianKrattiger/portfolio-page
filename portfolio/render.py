"""Render the ledger into static pages. Pure functions; returns {path: text}.

Visual system: every entry is a punched tag; its state is a strip of label tape
whose colour encodes the family (done / failed / unfinished) and whose word and
shape name the state. See docs/superpowers/specs/2026-11-22-restyle-design.md.
"""
import html
import json
from collections import Counter, OrderedDict

from .validate import STATES, VERIFICATIONS, is_stale, is_unknown

DONE_STATES = ["MEASURED", "BUILT"]
FAILED_STATES = ["KILLED", "NEGATIVE-RESULT"]
UNFINISHED_STATES = ["IN-PROGRESS", "DESIGN-ONLY", "BLOCKED", "NOT-DONE"]
NOT_DONE_STATES = FAILED_STATES + UNFINISHED_STATES
FAMILIES = [("done", "Done", DONE_STATES), ("failed", "Failed", FAILED_STATES),
            ("unfinished", "Unfinished", UNFINISHED_STATES)]
FAMILY_SHAPE = {"done": "measured", "failed": "killed", "unfinished": "not-done"}
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
UNKNOWN_TEXT = "UNKNOWN — author to supply"

e = html.escape


def slug(s):
    return s.lower().replace(" ", "-")


def family(state):
    for key, _label, states in FAMILIES:
        if state in states:
            return key
    raise ValueError(state)


# ---------------------------------------------------------------- primitives

SVG_DEFS = """<svg class="defs" aria-hidden="true" focusable="false" width="0" height="0"><defs>
<symbol id="s-measured" viewBox="0 0 12 12"><rect x="1.5" y="1.5" width="9" height="9" fill="currentColor"/></symbol>
<symbol id="s-built" viewBox="0 0 12 12"><rect x="2" y="2" width="8" height="8" fill="none" stroke="currentColor" stroke-width="1.6"/></symbol>
<symbol id="s-in-progress" viewBox="0 0 12 12"><rect x="2" y="2" width="8" height="8" fill="none" stroke="currentColor" stroke-width="1.6"/><rect x="2" y="2" width="4" height="8" fill="currentColor"/></symbol>
<symbol id="s-design-only" viewBox="0 0 12 12"><polygon points="6,1 11,6 6,11 1,6" fill="none" stroke="currentColor" stroke-width="1.6"/></symbol>
<symbol id="s-blocked" viewBox="0 0 12 12"><rect x="2" y="2" width="8" height="8" fill="none" stroke="currentColor" stroke-width="1.6"/><rect x="2" y="5" width="8" height="2" fill="currentColor"/></symbol>
<symbol id="s-not-done" viewBox="0 0 12 12"><circle cx="6" cy="6" r="4.2" fill="none" stroke="currentColor" stroke-width="1.8"/></symbol>
<symbol id="s-killed" viewBox="0 0 12 12"><path d="M2 2 L10 10 M10 2 L2 10" stroke="currentColor" stroke-width="2.2" fill="none"/></symbol>
<symbol id="s-negative-result" viewBox="0 0 12 12"><polygon points="1.5,2.5 10.5,2.5 6,10.5" fill="currentColor"/></symbol>
</defs></svg>"""


def shape(name):
    return f'<svg class="shape" aria-hidden="true" focusable="false"><use href="#s-{name}"/></svg>'


def state_tag(state):
    """Label tape: family colour, state shape, state word."""
    return f'<span class="tape {family(state)}">{shape(slug(state))}{e(state)}</span>'


def verif_tag(v):
    cls = "stk-linked" if v == "LINKED" else "stk-author"
    return f'<span class="stk {cls}">{e(v)}</span>'


def stale_tag():
    return '<span class="stk stk-stale" title="as_of older than 90 days at build time">STALE</span>'


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
    target = "ledger/index.html"
    if page == target:
        return "#" + entry_id
    return rel(page, target) + "#" + entry_id


def entry_home_href(page, entry):
    """Link to the entry's tag on its own project page (same page -> bare #id)."""
    target = f"projects/{entry['project']}/index.html"
    if target == page:
        return "#" + entry["id"]
    return rel(page, target) + "#" + entry["id"]


def project_name(site, key):
    for p in site["projects"]:
        if p["slug"] == key:
            return p["name"]
    return key


def sort_entries(entries, site):
    order = {p["slug"]: i for i, p in enumerate(site["projects"])}
    sidx = {s: i for i, s in enumerate(STATES)}
    return sorted(entries, key=lambda x: (order.get(x["project"], 99), sidx[x["state"]], x["id"]))


def family_counts(entries):
    c = Counter(family(x["state"]) for x in entries)
    return {k: c.get(k, 0) for k, _l, _s in FAMILIES}


def strip(entries):
    """Small family-count chips; zero counts are shown dashed, never hidden."""
    fc = family_counts(entries)
    chips = []
    for key, label, _s in FAMILIES:
        n = fc[key]
        cls = f"chip {key}" + (" zero" if n == 0 else "")
        chips.append(f'<span class="{cls}">{shape(FAMILY_SHAPE[key])}{e(label)} {n}</span>')
    return '<span class="strip">' + "".join(chips) + "</span>"


# ---------------------------------------------------------------- layout

def nav(page, site):
    items = [("ledger/index.html", "Ledger"), ("not-done/index.html", "Not done"),
             ("projects/index.html", "Projects"), ("about/index.html", "About"),
             ("ai/index.html", "AI disclosure")]
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
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'self'; font-src 'self'; script-src 'unsafe-inline'; img-src 'self' data:; base-uri 'none'; form-action 'none'">
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
<p>Built {e(ctx.build_date.isoformat())} from content/ledger.yaml. STALE = as_of older than 90 days at build time.
Machine-readable: <a href="{rel(page, 'ledger.json')}">ledger.json</a>.</p>
</footer>
{script}
</body>
</html>
"""


# ---------------------------------------------------------------- tags

def evidence_html(ev, site):
    if is_unknown(ev):
        return f"<p>{text(ev)} No primary artifact found in the context walked.</p>"
    lis = []
    for it in ev:
        repo = it["repo"]
        sha = str(it.get("sha", ""))
        branch = str(it.get("branch", ""))
        if repo == "vault":
            loc = "author's notes (vault)"
        elif repo == "seed":
            loc = "seed ledger (prior only)"
        elif repo == "author":
            loc = "author's statement"
        elif sha == "n/a":
            loc = f"{repo} ({branch})"
        else:
            loc = f"{repo} @ {branch} {sha}"
        path_html = e(it["path"])
        if sha in site.get("linkable_shas", {}).get(repo, []) and repo in site.get("public_repos", {}):
            url = f"{site['public_repos'][repo]}/blob/{sha}/{it['path']}"
            if "(untracked)" not in branch:
                path_html = f'<a href="{e(url)}" rel="noreferrer">{path_html}</a>'
        dirty = ' <span class="stk stk-flag">worktree dirty</span>' if it.get("dirty") else ""
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
        body.append("<tr>" + "".join(
            f'<td{" class=\"nowrap\"" if i in (1, 6) else ""}>{text(c)}</td>' for i, c in enumerate(cells)) + "</tr>")
    return (f'<div class="scroll" role="region" aria-label="{e(caption)}" tabindex="0">'
            f'<table class="nums"><caption>{e(caption)}</caption><thead><tr>{head}</tr></thead>'
            f'<tbody>{"".join(body)}</tbody></table></div>')


def tag(entry, ctx, page, anchor=True, show_project=True, details=True):
    """One entry as a punched tag. anchor=True puts the entry id on the tag."""
    eid = entry["id"]
    fam = family(entry["state"])
    meta = [state_tag(entry["state"]), verif_tag(entry["verification"])]
    if ctx.stale(entry):
        meta.append(stale_tag())
    meta.append(f'<a class="eid" href="{entry_href(page, eid)}">#{e(eid)}</a>')
    if show_project:
        meta.append(f'<span class="proj">{e(project_name(ctx.site, entry["project"]))}</span>')
    meta.append(f'<span class="asof">as of {e(entry["as_of"])}</span>')
    idattr = f' id="{e(eid)}"' if anchor else ""
    parts = [f'<article class="tag {fam}"{idattr} data-project="{e(entry["project"])}" '
             f'data-state="{e(entry["state"])}" data-verification="{e(entry["verification"])}">',
             f'<p class="meta">{" ".join(meta)}</p>',
             f'<p class="claim">{e(entry["claim"])}</p>',
             f'<p class="dns"><span class="lbl">Does not show</span>{text(entry["does_not_show"])}</p>']
    facts = []
    if entry.get("verification") == "AUTHOR-REPORTED":
        facts.append('<dt>Verification</dt><dd class="sig">Author-reported, not re-verified. '
                     'No tier-1 artifact containing this claim was opened for this site.</dd>')
    if entry.get("measurements"):
        facts.append("<dt>Measured</dt><dd>" + numbers_table(entry["measurements"], f"Measurements for {eid}") + "</dd>")
    if entry.get("results"):
        facts.append("<dt>Reported numbers</dt><dd>" + numbers_table(entry["results"], f"Numbers for {eid}") + "</dd>")
    if entry.get("reported_result"):
        facts.append(f'<dt>Reported result</dt><dd>{e(entry["reported_result"])} '
                     f'<span class="stk stk-flag">details not supplied</span></dd>')
    if entry.get("kill_criterion"):
        facts.append(f'<dt>Kill criterion</dt><dd>{e(entry["kill_criterion"])}</dd>')
    if entry.get("blocked_by"):
        facts.append(f'<dt>Blocked by</dt><dd>{e(entry["blocked_by"])}</dd>')
    if entry.get("disagreement"):
        facts.append(f'<dt>Sources disagree</dt><dd class="sig">{e(entry["disagreement"])}</dd>')
    more = [f'<dt>Evidence</dt><dd>{evidence_html(entry["evidence"], ctx.site)}</dd>']
    if entry.get("notes"):
        more.append(f'<dt>Notes</dt><dd>{e(entry["notes"])}</dd>')
    if details:
        # Compact tag: short, decisive facts stay visible; numbers, the verification
        # note and evidence fold under one summary that names what is inside.
        visible, folded, inside = [], [], []
        for f in facts:
            if f.startswith(("<dt>Kill criterion", "<dt>Blocked by")):
                visible.append(f)
            else:
                folded.append(f)
        if entry.get("measurements"):
            inside.append(f'{len(entry["measurements"])} measured number' + ("s" if len(entry["measurements"]) != 1 else ""))
        if entry.get("results"):
            inside.append(f'{len(entry["results"])} reported number' + ("s" if len(entry["results"]) != 1 else ""))
        if entry.get("disagreement"):
            inside.append("where sources disagree")
        inside.append("evidence")
        if visible:
            parts.append("<dl>" + "".join(visible) + "</dl>")
        flag = ' <span class="stk stk-author">SOURCES DISAGREE</span>' if entry.get("disagreement") else ""
        parts.append(f'<details><summary>{e(", ".join(inside).capitalize())}</summary><dl>'
                     + "".join(folded + more) + "</dl></details>")
        if flag:
            parts[1] = parts[1].replace("</p>", flag + "</p>", 1)
    else:
        parts.append("<dl>" + "".join(facts + more) + "</dl>")
    parts.append("</article>")
    return "\n".join(parts)


def family_groups(entries, ctx, page, anchor=True, show_project=False, details=True, level="h3"):
    """Done / Failed / Unfinished groups; a family with no entries renders nothing."""
    out = []
    sidx = {s: i for i, s in enumerate(STATES)}
    for key, label, states in FAMILIES:
        group = sorted([x for x in entries if x["state"] in states], key=lambda x: (sidx[x["state"]], x["id"]))
        if not group:
            continue
        tags = "\n".join(tag(x, ctx, page, anchor=anchor, show_project=show_project, details=details) for x in group)
        out.append(f'<div class="famgroup" data-family="{key}"><{level} class="fam">'
                   f'<span class="tape {key}">{shape(FAMILY_SHAPE[key])}{e(label)}</span>'
                   f'<span class="n">{len(group)}</span></{level}>{tags}</div>')
    return "".join(out)


# ---------------------------------------------------------------- about

def skills_html(site, page, ctx):
    lis = []
    for sk in site.get("skills", []):
        ids = [i for i in sk.get("backed_by", []) if i in ctx.by_id]
        if ids:
            seen = "seen in " + ", ".join(
                f'<a href="{e(entry_home_href(page, ctx.by_id[i]))}">#{e(i)}</a>' for i in ids)
        else:
            seen = '<span class="stk stk-author">AUTHOR-REPORTED</span>'
        note = f' <span class="seen">({e(sk["note"])})</span>' if sk.get("note") else ""
        lis.append(f'<li>{e(sk["name"])} <span class="seen">{seen}</span>{note}</li>')
    return "<ul>" + "".join(lis) + "</ul>"


def contact_html(contact):
    if isinstance(contact, dict):
        parts = []
        if contact.get("email"):
            em = contact["email"].strip()
            parts.append(f'<a href="mailto:{e(em)}">{e(em)}</a>')
        if contact.get("github"):
            gh = contact["github"].strip()
            label = gh.replace("https://", "").replace("http://", "").rstrip("/")
            parts.append(f'<a href="{e(gh)}" rel="noreferrer">{e(label)}</a>')
        if contact.get("linkedin"):
            li = contact["linkedin"].strip()
            label = li.replace("https://www.", "").replace("https://", "").replace("http://www.", "").replace("http://", "").rstrip("/")
            parts.append(f'<a href="{e(li)}" rel="noreferrer">{e(label)}</a>')
        if parts:
            return " · ".join(parts)
    return text(contact)


def about_dl(site, page, ctx):
    projs = ", ".join(f'<a href="{rel(page, "projects/" + p["slug"] + "/index.html")}">{e(p["name"])}</a>'
                      for p in site["projects"])
    return f"""<dl class="about">
<dt>Education</dt><dd>{e(site['education'])} <span class="seen">Source: {e(site['education_source'])}.</span></dd>
<dt>Focus</dt><dd>{e(site['focus'])}</dd>
<dt>Skills</dt><dd>{skills_html(site, page, ctx)}<span class="seen">{e(site.get('skills_source', ''))}.</span></dd>
<dt>Projects</dt><dd>{projs}</dd>
<dt>Contact</dt><dd>{contact_html(site['contact'])}</dd>
</dl>"""


def project_rows(entries, site, page, group):
    rows = []
    for p in site["projects"]:
        if p.get("group") != group:
            continue
        mine = [x for x in entries if x["project"] == p["slug"]]
        rows.append(f'<li class="projrow"><div><a class="pname" href="{rel(page, "projects/" + p["slug"] + "/index.html")}">'
                    f'{e(p["name"])}</a><span class="psub">{e(p["subtitle"])}</span></div>{strip(mine)}</li>')
    return '<ul class="projrows">' + "".join(rows) + "</ul>"


# ---------------------------------------------------------------- pages

def page_home(entries, ctx):
    page = "index.html"
    site = ctx.site
    fc = family_counts(entries)
    vc = Counter(x["verification"] for x in entries)
    stale_n = sum(1 for x in entries if ctx.stale(x))
    disagree_n = sum(1 for x in entries if x.get("disagreement"))
    targets = {"done": "ledger/index.html", "failed": "not-done/index.html",
               "unfinished": "not-done/index.html#unfinished"}
    counts = "".join(
        f'<li><a href="{rel(page, targets[k])}"><span class="bigtape {k}">{shape(FAMILY_SHAPE[k])}'
        f'{e(label)}<span class="num">{fc[k]}</span></span></a></li>' for k, label, _s in FAMILIES)
    newest = sorted(entries, key=lambda x: (x["as_of"], x["id"]), reverse=True)[:3]
    body = f"""
<section class="lead">
<h1 class="title">{e(site['name'])}</h1>
<p class="tagline">{e(site['line'])}</p>
<ul class="counts" aria-label="Entries by family, computed from the ledger">{counts}</ul>
<p class="wallnote">{len(entries)} public entries: {vc.get('LINKED', 0)} linked to a commit, {vc.get('AUTHOR-REPORTED', 0)} author-reported, {stale_n} stale, {disagree_n} where sources disagree. Counts are computed at build time.</p>
</section>
<section aria-labelledby="h-research"><h2 class="band" id="h-research">Research</h2>
{project_rows(entries, site, page, "research")}</section>
<section aria-labelledby="h-other"><h2 class="band" id="h-other">Other work</h2>
{project_rows(entries, site, page, "other")}</section>
<section aria-labelledby="h-about"><h2 class="band" id="h-about">About</h2>
<div class="sheet">{about_dl(site, page, ctx)}
<p><a href="{rel(page, 'about/index.html')}">More: what I am looking at next, and open threads</a></p></div></section>
<section aria-labelledby="h-new"><h2 class="band" id="h-new">Newest entries <a class="small" href="{rel(page, 'ledger/index.html')}">all {len(entries)}</a></h2>
{"".join(tag(x, ctx, page, anchor=False) for x in newest)}</section>
"""
    return layout(page, "Ledger summary", body, ctx)


def untested_built(entries):
    return [x for x in entries if x["state"] == "BUILT" and not x.get("measurements")]


def page_not_done(entries, ctx):
    page = "not-done/index.html"
    site = ctx.site
    order = FAILED_STATES[::-1] + ["BLOCKED", "NOT-DONE", "DESIGN-ONLY", "IN-PROGRESS"]
    blocks = []
    for st in order:
        group = sort_entries([x for x in entries if x["state"] == st], site)
        inner = "\n".join(tag(x, ctx, page) for x in group) or "<p>None.</p>"
        first = ' id="unfinished"' if st == "BLOCKED" else ""
        blocks.append(f'<section{first}><h2 class="band" id="state-{slug(st)}">{state_tag(st)}'
                      f'<span class="strip">{len(group)} · {e(STATE_GLOSS[st])}</span></h2>{inner}</section>')
    ut = sort_entries(untested_built(entries), site)
    ut_rows = "".join(
        f'<li><a class="mono" href="{entry_href(page, x["id"])}">#{e(x["id"])}</a> {e(x["claim"])}'
        f'<br><span class="lbl">Does not show</span>{text(x["does_not_show"])}</li>' for x in ut)
    body = f"""
<section class="lead">
<h1 class="title">Not done</h1>
<p class="dek">Negative results, killed experiments, blockers, things I have not built, designs that are only designs, and built things nobody has measured. Same weight as the done side.</p>
</section>
<nav class="jump" aria-label="Jump to group"><ul>
{"".join(f'<li><a href="#state-{slug(s)}">{e(s)}</a></li>' for s in order)}
<li><a href="#untested">Built, not measured</a></li></ul></nav>
{"".join(blocks)}
<section><h2 class="band" id="untested">Built, not measured <span class="strip">{len(ut)}</span></h2>
<div class="sheet"><p>Built entries with no qualifying measurement in the evidence. Full tags are in the <a href="{rel(page, 'ledger/index.html')}">ledger</a> and on project pages.</p>
<ul class="plain">{ut_rows}</ul></div></section>
"""
    return layout(page, "Not done", body, ctx)


FILTER_SCRIPT = """<script>
(function () {
  var form = document.getElementById('filters');
  var root = document.getElementById('ledger-tags');
  if (!form || !root) return;
  form.hidden = false;
  var tags = root.querySelectorAll('article.tag');
  var out = document.getElementById('filter-count');
  function apply() {
    var p = form.project.value, s = form.state.value, v = form.verification.value, n = 0, i;
    for (i = 0; i < tags.length; i++) {
      var t = tags[i];
      var show = (!p || t.getAttribute('data-project') === p) &&
                 (!s || t.getAttribute('data-state') === s) &&
                 (!v || t.getAttribute('data-verification') === v);
      t.hidden = !show; if (show) n++;
    }
    var groups = root.querySelectorAll('.famgroup, section.proj');
    for (i = 0; i < groups.length; i++) {
      groups[i].hidden = !groups[i].querySelector('article.tag:not([hidden])');
    }
    out.textContent = n + ' of ' + tags.length + ' entries shown';
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
        out.append(f"<li>{facet}: {links}</li>")
    return "<ul class=\"facets\">" + "".join(out) + "</ul>"


def ledger_sections(entries, ctx, page, anchor):
    site = ctx.site
    out = []
    for p in site["projects"]:
        mine = [x for x in entries if x["project"] == p["slug"]]
        if not mine:
            continue
        out.append(f'<section class="proj" id="p-{e(p["slug"])}" data-project="{e(p["slug"])}">'
                   f'<h2 class="band"><a href="{rel(page, "projects/" + p["slug"] + "/index.html")}">{e(p["name"])}</a>'
                   f'{strip(mine)}</h2>{family_groups(mine, ctx, page, anchor=anchor)}</section>')
    return "".join(out)


def page_ledger(entries, ctx):
    page = "ledger/index.html"
    site = ctx.site
    fv = facet_values(entries, site)

    def select(name, values):
        opts = "".join(f'<option value="{e(v)}">{e(facet_label(site, name, v))}</option>' for v in values)
        return f'<label>{name} <select name="{name}"><option value="">all</option>{opts}</select></label>'

    body = f"""
<section class="lead">
<h1 class="title">Ledger</h1>
<p class="dek">Every public claim, one tag each, grouped by project and then by done, failed and unfinished. Each tag has a stable anchor: ledger/#id. Evidence for each tag opens under it.</p>
</section>
<section aria-label="Filters">
<form id="filters" class="filters" hidden>
{select("project", fv["project"])} {select("state", fv["state"])} {select("verification", fv["verification"])}
<button type="reset">clear</button> <output id="filter-count" aria-live="polite"></output>
</form>
<p class="wallnote">Filter pages (work without JavaScript):</p>{facet_links(page, entries, site)}
</section>
<div id="ledger-tags">
{ledger_sections(entries, ctx, page, anchor=True)}
</div>
"""
    return layout(page, "Ledger", body, ctx, script=FILTER_SCRIPT)


def page_facet(entries, ctx, facet, value):
    page = f"ledger/{facet}/{slug(value)}/index.html"
    site = ctx.site
    sub = [x for x in entries if x[facet] == value]
    label = facet_label(site, facet, value)
    body = f"""
<section class="lead">
<h1 class="title">{e(label)}</h1>
<p class="dek">Ledger filtered by {e(facet)} = {e(value)}: {len(sub)} of {len(entries)} entries. <a href="{rel(page, 'ledger/index.html')}">All entries</a>.</p>
{facet_links(page, entries, site)}
</section>
{ledger_sections(sub, ctx, page, anchor=False)}
"""
    return layout(page, f"Ledger: {label}", body, ctx)


def page_projects(entries, ctx):
    page = "projects/index.html"
    site = ctx.site
    body = f"""
<section class="lead">
<h1 class="title">Projects</h1>
<p class="dek">Research on verifying AI output, and other work. The chips count each project's ledger entries by family.</p>
</section>
<section aria-labelledby="h-research"><h2 class="band" id="h-research">Research</h2>
{project_rows(entries, site, page, "research")}</section>
<section aria-labelledby="h-other"><h2 class="band" id="h-other">Other work</h2>
{project_rows(entries, site, page, "other")}</section>
"""
    return layout(page, "Projects", body, ctx)


def page_project(proj, entries, ctx):
    page = f"projects/{proj['slug']}/index.html"
    site = ctx.site
    mine = sort_entries([x for x in entries if x["project"] == proj["slug"]], site)
    by = {x["id"]: x for x in mine}
    what = "".join(
        f'<li>{e(by[i]["claim"])} <a class="mono" href="#{e(i)}">#{e(i)}</a></li>'
        for i in proj["what_it_is_ids"] if i in by)

    def section(title, sid, items, empty, extra=""):
        inner = "\n".join(tag(x, ctx, page, show_project=False, details=False) for x in items) \
            or f'<div class="sheet"><p>{empty}</p></div>'
        return f'<section><h2 class="band" id="{sid}">{e(title)}<span class="strip">{len(items)} {"entry" if len(items) == 1 else "entries"}</span></h2>{inner}{extra}</section>'

    exists = [x for x in mine if x["state"] in ("BUILT", "IN-PROGRESS")]
    measured = [x for x in mine if x["state"] == "MEASURED"]
    not_built = [x for x in mine if x["state"] in ("NOT-DONE", "DESIGN-ONLY", "BLOCKED")]
    weak = [x for x in mine if x["state"] in ("NEGATIVE-RESULT", "KILLED")]
    dns = "".join(
        f'<li><a class="mono" href="#{e(x["id"])}">#{e(x["id"])}</a> {text(x["does_not_show"])}</li>'
        for x in mine)
    dis_html = "".join(
        f'<li><a class="mono" href="#{e(x["id"])}">#{e(x["id"])}</a> <span class="sig">{e(x["disagreement"])}</span></li>'
        for x in mine if x.get("disagreement"))
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
    other = sorted({k[0] for k in ev_index} - set(pub) - {"vault", "seed", "author", "—"})
    if other:
        repo_links += ("<p>Repos with no public URL on this site (visibility not confirmed): "
                       + ", ".join(f'<span class="mono">{e(r)}</span>' for r in other) + ". "
                       + text("UNKNOWN — author to supply") + "</p>")
    dis_block = f"<div class='sheet'><h3>Where sources disagree</h3><ul class='plain'>{dis_html}</ul></div>" if dis_html else ""

    body = f"""
<section class="lead">
<h1 class="title">{e(proj['name'])}</h1>
<p class="tagline">{e(proj['subtitle'])}</p>
<p class="wallnote">{strip(mine)}</p>
</section>
<nav class="jump" aria-label="Sections"><ol>
<li><a href="#what">What it is</a></li><li><a href="#exists">What exists</a></li>
<li><a href="#measured">What was measured</a></li><li><a href="#not-measured">Not measured or built</a></li>
<li><a href="#weak">Weaknesses and negative results</a></li><li><a href="#open">Open questions</a></li>
<li><a href="#evidence">Evidence</a></li></ol></nav>
<section><h2 class="band" id="what">What it is</h2>{versions_html(proj, page, ctx) or f'<div class="sheet"><ul class="plain">{what}</ul></div>'}</section>
{section("What exists", "exists", exists, "No BUILT or IN-PROGRESS entries.")}
{section("What was measured", "measured", measured, "No entry meets MEASURED: number, denominator, dataset, synthetic flag, system and date all known. Numbers that fall short are shown with their entries.")}
{section("Not measured or built", "not-measured", not_built, "No NOT-DONE, DESIGN-ONLY or BLOCKED entries.",
         extra=f'<div class="sheet"><h3>What each entry does not show</h3><ul class="plain">{dns}</ul></div>')}
{section("Weaknesses and negative results", "weak", weak, "No NEGATIVE-RESULT or KILLED entries.", extra=dis_block)}
<section><h2 class="band" id="open">Open questions</h2><div class="sheet"><ul class="plain">{oq}</ul></div></section>
<section><h2 class="band" id="evidence">Evidence</h2><div class="sheet">
{repo_links}
<div class="scroll" role="region" aria-label="Evidence index" tabindex="0"><table class="nums">
<caption>Every evidence pointer used on this page</caption>
<thead><tr><th scope="col">Repo / source</th><th scope="col">Branch</th><th scope="col">SHA</th><th scope="col">Path</th><th scope="col">Used by</th></tr></thead>
<tbody>{ev_rows}</tbody></table></div></div></section>
"""
    return layout(page, proj["name"], body, ctx)


def versions_html(proj, page, ctx):
    """Projects that exist in more than one version show each version, with its
    entries linked wherever they live."""
    vs = proj.get("versions")
    if not vs:
        return ""
    cards = []
    for i, v in enumerate(vs, 1):
        items = "".join(
            f'<li>{state_tag(ctx.by_id[x]["state"])} {e(ctx.by_id[x]["claim"])} '
            f'<a class="mono" href="{e(entry_home_href(page, ctx.by_id[x]))}">#{e(x)}</a></li>' for x in v["ids"])
        cards.append(f'<div class="sheet version"><h3><span class="vnum">Version {i}</span> {e(v["name"])}</h3>'
                     f'<p>{e(v["how"])}</p><ul class="plain">{items}</ul><p class="seen">{e(v["where"])}</p></div>')
    return '<div class="versions">' + "".join(cards) + "</div>"


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
<section class="lead">
<h1 class="title">About</h1>
<p class="tagline">{e(site['line'])}</p>
</section>
<div class="sheet">{about_dl(site, page, ctx)}</div>
<section><h2 class="band" id="next">What I am looking at next</h2><div class="sheet"><p>{text(site['next'])}</p>
<p>Open threads recorded in the evidence, not a plan:</p><ul class="plain">{"".join(threads)}</ul></div></section>
"""
    return layout(page, "About", body, ctx)


def page_ai(entries, ctx):
    page = "ai/index.html"
    disc = ctx.site["ai_disclosure"]
    sections = []
    for sec in disc["sections"]:
        parts = []
        if sec.get("intro"):
            parts.append(f'<p>{e(sec["intro"])}</p>')
        if sec.get("items"):
            lis = "".join(f"<li>{e(it)}</li>" for it in sec["items"])
            parts.append(f'<ul class="plain">{lis}</ul>')
        for para in sec.get("paragraphs", []):
            parts.append(f"<p>{e(para)}</p>")
        sections.append(
            f'<section aria-labelledby="{e(sec["id"])}">'
            f'<h2 class="band" id="{e(sec["id"])}">{e(sec["heading"])}</h2>'
            f'<div class="sheet">{"".join(parts)}</div></section>'
        )
    body = f"""
<section class="lead">
<h1 class="title">AI disclosure</h1>
<p class="tagline">{e(disc['tagline'])}</p>
</section>
{"".join(sections)}
"""
    return layout(page, "AI disclosure", body, ctx)


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

def build_site(all_entries, site, build_date):
    entries = [x for x in all_entries if x["visibility"] == "public"]
    n_hidden = len(all_entries) - len(entries)
    ctx = Ctx(site, build_date, {x["id"]: x for x in entries})
    refs = [i for sk in site.get("skills", []) for i in sk.get("backed_by", [])]
    for p in site["projects"]:
        refs += p["what_it_is_ids"] + [i for q in p["open_questions"] for i in q["ids"]]
        refs += [i for v in p.get("versions", []) for i in v["ids"]]
    for i in refs:
        if i not in ctx.by_id:
            raise ValueError(f"site.json references unknown or hidden entry {i}")
    pages = OrderedDict()
    pages["index.html"] = page_home(entries, ctx)
    pages["not-done/index.html"] = page_not_done(entries, ctx)
    pages["ledger/index.html"] = page_ledger(entries, ctx)
    for facet, values in facet_values(entries, site).items():
        for v in values:
            pages[f"ledger/{facet}/{slug(v)}/index.html"] = page_facet(entries, ctx, facet, v)
    pages["projects/index.html"] = page_projects(entries, ctx)
    for p in site["projects"]:
        pages[f"projects/{p['slug']}/index.html"] = page_project(p, entries, ctx)
    pages["about/index.html"] = page_about(entries, ctx)
    pages["ai/index.html"] = page_ai(entries, ctx)
    pages["ledger.json"] = ledger_json(entries, ctx, n_hidden)
    from .style import CSS
    pages["style.css"] = CSS
    return pages
