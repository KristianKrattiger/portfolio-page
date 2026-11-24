#!/usr/bin/env python3
"""Verification for the portfolio build. Python 3 stdlib only.

python verify/verify.py            run all offline checks, write content/site_checks.json
python verify/verify.py --live URL also curl every route on a running server
Exit code 1 if any check FAILs.
"""
import argparse
import datetime as dt
import hashlib
import html.parser
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from portfolio.validate import load_ledger  # noqa: E402
from portfolio.style import PALETTE, CONTRAST_PAIRS, CSS  # noqa: E402

PY = sys.executable
DIST = os.path.join(ROOT, "dist")
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
RESULTS = []
NOT_RUN = []


def record(name, command, ok, detail):
    res = "PASS" if ok else "FAIL"
    RESULTS.append({"name": name, "command": command, "result": res, "detail": detail})
    print(f"[{res}] {name}: {detail}")
    return ok


def not_run(name, reason):
    NOT_RUN.append({"name": name, "reason": reason})
    print(f"[NOT RUN] {name}: {reason}")


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", **kw)


def dist_files(base=DIST, assets=False):
    """Every file in dist/. assets=False leaves out fonts/ (the bundled font binaries and
    their licence text, copied byte for byte from assets/fonts and never generated), so
    text scans only see what the build writes."""
    out = []
    for d, _, fs in os.walk(base):
        for f in fs:
            r = os.path.relpath(os.path.join(d, f), base).replace(os.sep, "/")
            if assets or not r.startswith("fonts/"):
                out.append(r)
    return sorted(out)


def read(rel, base=DIST):
    with open(os.path.join(base, rel), encoding="utf-8") as fh:
        return fh.read()


# ------------------------------------------------------------------ checks

def check_tests():
    p = run([PY, "-m", "unittest", "discover", "-s", "tests"], cwd=ROOT)
    tail = (p.stderr.strip().splitlines() or ["?"])
    summary = " / ".join(l for l in tail[-3:] if l.strip())
    record("Validator test suite (incl. must-fail cases)", "python -m unittest discover -s tests",
           p.returncode == 0, summary)


BAD_LEDGERS = {
    "MEASURED without denominator": [{"id": "bad", "project": "gin", "claim": "c", "state": "MEASURED",
        "verification": "AUTHOR-REPORTED", "as_of": "2026-11-01", "does_not_show": "x", "visibility": "public",
        "evidence": [{"repo": "GIN", "path": "p", "branch": "main", "sha": "84abb9a", "tier": 2}],
        "measurements": [{"metric": "m", "value": "1", "dataset": "d", "synthetic": True, "system": "s", "date": "2026-11-01"}]}],
    "KILLED without criterion": [{"id": "bad", "project": "gin", "claim": "c", "state": "KILLED",
        "verification": "AUTHOR-REPORTED", "as_of": "2026-11-01", "does_not_show": "x", "visibility": "public",
        "evidence": "UNKNOWN"}],
    "LINKED without SHA": [{"id": "bad", "project": "gin", "claim": "c", "state": "BUILT",
        "verification": "LINKED", "as_of": "2026-11-01", "does_not_show": "x", "visibility": "public",
        "evidence": [{"repo": "GIN", "path": "p", "branch": "main", "tier": 1}]}],
    "missing does_not_show": [{"id": "bad", "project": "gin", "claim": "c", "state": "BUILT",
        "verification": "AUTHOR-REPORTED", "as_of": "2026-11-01", "visibility": "public", "evidence": "UNKNOWN"}],
}


def check_build_fails_on_bad_ledger():
    details, ok = [], True
    for name, ledger in BAD_LEDGERS.items():
        with tempfile.TemporaryDirectory() as td:
            lp = os.path.join(td, "ledger.yaml")
            with open(lp, "w", encoding="utf-8") as fh:
                json.dump(ledger, fh)
            out = os.path.join(td, "out")
            p = run([PY, "build.py", "--ledger", lp, "--out", out, "--date", "2026-11-20"], cwd=ROOT)
            failed = p.returncode == 1 and not os.path.exists(out)
            ok &= failed
            details.append(f"{name}: exit {p.returncode}{', no output' if not os.path.exists(out) else ', OUTPUT WRITTEN'}")
    record("Build fails on invalid ledgers", "python build.py --ledger <bad> (4 cases)", ok, "; ".join(details))


def tree_hash(base):
    h = hashlib.sha256()
    for rel in dist_files(base, assets=True):
        h.update(rel.encode())
        with open(os.path.join(base, rel), "rb") as fh:
            h.update(hashlib.sha256(fh.read()).digest())
    return h.hexdigest()


def check_determinism(date):
    with tempfile.TemporaryDirectory() as td:
        hs = []
        for i in (1, 2):
            out = os.path.join(td, f"b{i}")
            p = run([PY, "build.py", "--out", out, "--date", date], cwd=ROOT)
            if p.returncode != 0:
                return record("Deterministic build", "python build.py x2", False, p.stderr[-300:])
            hs.append(tree_hash(out))
    record("Deterministic build", f"python build.py --date {date} (twice, sha256 over all files)",
           hs[0] == hs[1], f"build 1 {hs[0][:16]}..., build 2 {hs[1][:16]}...")


def check_linked_at_sha():
    entries = load_ledger(os.path.join(ROOT, "content", "ledger.yaml"))
    repos = json.load(open(os.path.join(ROOT, "content", "repos.local.json"), encoding="utf-8"))
    checked, missing, linked = 0, [], 0
    for en in entries:
        if en["verification"] != "LINKED":
            continue
        linked += 1
        tier1 = [it for it in en["evidence"] if it.get("tier") == 1 and "(untracked)" not in str(it.get("branch"))]
        if not tier1:
            missing.append(f"{en['id']}: no tracked tier-1 item")
        for it in en["evidence"]:
            if it["repo"] in ("vault", "seed") or "(untracked)" in str(it.get("branch")):
                continue
            path = repos.get(it["repo"])
            if not path:
                missing.append(f"{en['id']}: no local path for {it['repo']}")
                continue
            p = run(["git", "-C", path, "cat-file", "-e", f"{it['sha']}:{it['path']}"])
            checked += 1
            if p.returncode != 0:
                missing.append(f"{en['id']}: {it['repo']} {it['sha']}:{it['path']} not found")
            if it.get("branch"):
                b = run(["git", "-C", path, "merge-base", "--is-ancestor", it["sha"], it["branch"]])
                if b.returncode != 0:
                    missing.append(f"{en['id']}: {it['sha']} not on branch {it['branch']}")
    record("Every LINKED entry: path exists at SHA, SHA on named branch",
           "git cat-file -e <sha>:<path>; git merge-base --is-ancestor <sha> <branch>",
           not missing, f"{linked} LINKED entries, {checked} evidence items checked" + (f"; problems: {missing}" if missing else ""))


URL_RE = re.compile(r"""(?:https?:)?//[^\s"'<>)]+""")
ALLOWED_URL_PREFIXES = ("https://github.com/KristianKrattiger", "https://kristiankrattiger.github.io/receipts/",
                        "https://www.linkedin.com/in/kristiankratt/", "http://www.w3.org/2000/svg")


def allowed_contact_emails():
    site_path = os.path.join(ROOT, "content", "site.json")
    if not os.path.exists(site_path):
        return set()
    with open(site_path, encoding="utf-8") as fh:
        contact = json.load(fh).get("contact")
    if isinstance(contact, dict) and contact.get("email"):
        return {contact["email"].strip().lower()}
    return set()


def check_external_and_secrets():
    hosts, bad = set(), []
    allowed_emails = allowed_contact_emails()
    host_names = [
        h for h in {os.environ.get("COMPUTERNAME", ""), socket.gethostname()}
        if h and len(h) >= 3 and h.lower() != "localhost"
    ]
    machine_rx = re.compile("|".join(re.escape(h) for h in sorted(host_names)), re.I) if host_names else re.compile(r"@@none@@")
    secret_patterns = {
        "IPv4 address": re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
        "tailnet (*.ts.net) name": re.compile(r"[a-z0-9-]+\.ts\.net", re.I),
        "local path": re.compile(r"[A-Za-z]:[\\/]+Users|/c/Users|/mnt/c/|\\\\Users\\\\", re.I),
        "email": re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[a-z]{2,}"),
        "api key": re.compile(r"sk-[A-Za-z0-9]{16,}|ghp_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|BEGIN [A-Z ]*PRIVATE KEY|xox[bp]-"),
        "env assignment": re.compile(r"(?:API_KEY|TOKEN|SECRET|PASSWORD)\s*=\s*\S+", re.I),
        "localhost": re.compile(r"localhost", re.I),
        "machine name": machine_rx,
        "analytics/cookies": re.compile(r"google-analytics|googletagmanager|gtag\(|plausible|umami|document\.cookie|<script[^>]+src=", re.I),
    }
    for rel in dist_files():
        txt = read(rel)
        for m in URL_RE.finditer(txt):
            u = m.group(0)
            if u.startswith("//") and not u.startswith("//www.w3.org"):
                bad.append(f"{rel}: protocol-relative {u}")
                continue
            if u.startswith("http"):
                hosts.add(urllib.parse.urlparse(u).netloc)
                if not u.startswith(ALLOWED_URL_PREFIXES):
                    bad.append(f"{rel}: disallowed URL host")
        for name, rx in secret_patterns.items():
            for m in rx.finditer(txt):
                if name == "email" and m.group(0).lower() in allowed_emails:
                    continue
                bad.append(f"{rel}: {name}")  # never echo the match: it would be republished
    record("No external hosts beyond evidence links; no secrets, IPs, *.ts.net names, hostnames, analytics",
           "regex scan of every file in dist/", not bad,
           f"allowed hosts seen: {sorted(h for h in hosts if any(x.startswith('http') and urllib.parse.urlparse(x).netloc == h for x in ALLOWED_URL_PREFIXES))}; other hosts: {len([h for h in hosts if not any(urllib.parse.urlparse(x).netloc == h for x in ALLOWED_URL_PREFIXES)])} (w3.org is the SVG namespace inside a CSS data URI, never fetched)"
           + (f"; problems: {sorted(set(bad))[:12]}" if bad else ""))


class LinkParser(html.parser.HTMLParser):
    VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr", "use", "rect", "circle", "polygon", "path"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links, self.ids, self.stack, self.errors = [], set(), [], []
        self.tabindex, self.text_chunks, self.in_script = [], [], False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            if a["id"] in self.ids:
                self.errors.append(f"duplicate id {a['id']}")
            self.ids.add(a["id"])
        for k in ("href", "src"):
            if k in a and a[k] and tag not in ("use",):
                self.links.append(a[k])
        if "tabindex" in a:
            self.tabindex.append(a["tabindex"])
        if tag == "script":
            self.in_script = True
        if tag not in self.VOID:
            self.stack.append(tag)

    def handle_startendtag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            self.ids.add(a["id"])

    def handle_endtag(self, tag):
        if tag == "script":
            self.in_script = False
        if tag in self.VOID:
            return
        if not self.stack or self.stack[-1] != tag:
            self.errors.append(f"unexpected </{tag}> (open: {self.stack[-3:]})")
            if tag in self.stack:
                while self.stack and self.stack.pop() != tag:
                    pass
        else:
            self.stack.pop()

    def handle_data(self, data):
        if not self.in_script:
            self.text_chunks.append(data)


def parse(rel):
    p = LinkParser()
    p.feed(read(rel))
    p.close()
    if p.stack:
        p.errors.append(f"unclosed: {p.stack}")
    return p


def check_links_and_html():
    pages = [r for r in dist_files() if r.endswith(".html")]
    parsed = {r: parse(r) for r in pages}
    broken, n = [], 0
    for r, p in parsed.items():
        for href in p.links:
            if href.startswith(("http://", "https://", "mailto:")):
                continue
            n += 1
            path, _, frag = href.partition("#")
            target = r if not path else os.path.normpath(os.path.join(os.path.dirname(r), path)).replace(os.sep, "/")
            if not os.path.exists(os.path.join(DIST, target)):
                broken.append(f"{r} -> {href}")
                continue
            if frag and target.endswith(".html") and frag not in parsed[target].ids:
                broken.append(f"{r} -> {href} (missing #{frag})")
    record("Internal link check (files and #fragments)", "html.parser over dist/*.html",
           not broken, f"{n} internal links in {len(pages)} pages" + (f"; broken: {broken[:10]}" if broken else ""))
    errs = [f"{r}: {e}" for r, p in parsed.items() for e in p.errors]
    record("HTML well-formedness (tag balance, duplicate ids)", "stdlib html.parser structural check",
           not errs, f"{len(pages)} pages" + (f"; errors: {errs[:8]}" if errs else ""))
    return parsed


def lum(hexc):
    hexc = hexc.lstrip("#")
    rgb = [int(hexc[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def ratio(a, b):
    la, lb = sorted([lum(a), lum(b)], reverse=True)
    return (la + 0.05) / (lb + 0.05)


def check_contrast():
    rows, ok = [], True
    for scheme, pal in PALETTE.items():
        for fg, bg, need, what in CONTRAST_PAIRS:
            r = ratio(pal[fg], pal[bg])
            ok &= r >= need
            rows.append(f"{scheme} {fg}/{bg} {r:.2f} (need {need})")
    record("WCAG AA contrast, every palette pair, both schemes", "WCAG 2.x relative-luminance formula",
           ok, "; ".join(rows))


BANNED = ["hi, i'm", "hi i'm", "passionate", "groundbreaking", "novel", "cutting-edge", "cutting edge",
          "world-class", "revolutionary", "game-changing", "state-of-the-art", "innovative", "leverage",
          "seamless", "excited to", "rockstar", "ninja", "10x", "ex-opere", "exopere", "ex opere"]
BANNED_CSS = [r"linear-gradient\(", r"radial-gradient\(", r"backdrop-filter", r"border-radius\s*:\s*(?!0[;}\s])",
              r"parallax", r"typewriter", r"<marquee", r"@import\s+url\(http"]
EMOJI = re.compile("[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F000-\U0001F2FF]")
# Teammates' first names, stored only as SHA-256 of the lowercased word, so the names never
# enter this repo while a leak into dist/ still fails the check.
PRIVATE_NAME_HASHES = {
    "69bfe1e6e44821df7f8a0927bd7e61ef208fdb25deaa4353450bc3fb904abd52",
    "c71758a30a821e220d7f441eec57f6d7347183186cacb7f41f55a33a522dc64e",
    "7f2c7bc80b97eb6fd2b7932826ce72697648c1ac3284316f92aef0102a748c69",
    "d919a100ce6b45524d415d52d088d5817587c6dd8c3691b03b8063c44d043523",
    "cd879f74c6ffe6e4ae973145798ca26489fa2a61f7b29ac5fd816c0ad959511f",
}
PRIVATE_TERMS = ["pinetree internship", "internship", "job search", "employer", "girlfriend", "boyfriend",
                 "wife", "husband", "attest", "claim-record", "business plan", "salary", "gpa"]


def name_hits(txt):
    return any(hashlib.sha256(w.encode()).hexdigest() in PRIVATE_NAME_HASHES
               for w in set(re.findall(r"[a-z]+", txt.lower())))


def check_banned(parsed):
    hits = []
    for r, p in parsed.items():
        txt = " ".join(p.text_chunks).lower()
        for w in BANNED:
            if re.search(r"(?<![a-z])" + re.escape(w) + r"(?![a-z])", txt):
                hits.append(f"{r}: '{w}'")
        for w in PRIVATE_TERMS:
            if re.search(r"(?<![a-z])" + re.escape(w) + r"(?![a-z])", txt):
                hits.append(f"{r}: private term '{w}'")
        if EMOJI.search(read(r)):
            hits.append(f"{r}: emoji")
        if name_hits(txt):
            hits.append(f"{r}: teammate name")
    j = read("ledger.json").lower()
    if name_hits(j):
        hits.append("ledger.json: teammate name")
    for w in BANNED + PRIVATE_TERMS:
        if re.search(r"(?<![a-z])" + re.escape(w) + r"(?![a-z])", j):
            hits.append(f"ledger.json: '{w}'")
    for rx in BANNED_CSS:
        for r in dist_files():
            if re.search(rx, read(r), re.I):
                hits.append(f"{r}: pattern {rx}")
    record("Banned phrases/patterns from STYLE.md and private-topic terms", "regex over visible text, ledger.json, CSS",
           not hits, f"{len(BANNED)} phrases, {len(PRIVATE_TERMS)} private terms, {len(PRIVATE_NAME_HASHES)} hashed names, {len(BANNED_CSS)} CSS patterns, emoji ranges"
           + (f"; hits: {hits[:12]}" if hits else ""))


def check_keyboard_static(parsed):
    problems = []
    for r, p in parsed.items():
        if "#main" not in p.links:
            problems.append(f"{r}: no skip link")
        if any(t.strip().lstrip("-").isdigit() and int(t) > 0 for t in p.tabindex):
            problems.append(f"{r}: positive tabindex")
        src = read(r)
        if re.search(r"onclick=|<div[^>]+role=\"button\"", src):
            problems.append(f"{r}: non-native interactive element")
    if ":focus-visible" not in CSS or re.search(r"outline\s*:\s*(none|0)", CSS):
        problems.append("style.css: focus style missing or removed")
    record("Keyboard basics (static): skip link, native controls, no positive tabindex, visible focus",
           "html.parser + CSS scan", not problems, f"{len(parsed)} pages" + (f"; {problems[:8]}" if problems else ""))


def check_nojs(parsed):
    entries = [e for e in load_ledger(os.path.join(ROOT, "content", "ledger.yaml")) if e["visibility"] == "public"]
    src = read("ledger/index.html")
    rows = src.count('data-verification="')
    form_hidden = re.search(r'<form id="filters"[^>]*\bhidden\b', src) is not None
    ok = rows == len(entries) and form_hidden
    detail = f"ledger has {rows} tags server-rendered for {len(entries)} public entries; JS-only filter form hidden by default: {form_hidden}"
    # This Edge build ignores --blink-settings=scriptEnabled=false / --disable-javascript for
    # --dump-dom (verified: the filter script still ran). So the JS-off render is tested on a
    # copy of dist/ with every <script> block removed, which is what a JS-off browser sees here
    # (the site has no <noscript> content).
    if os.path.exists(EDGE):
        work = tempfile.mkdtemp(prefix="nojs-")
        try:
            stripped = os.path.join(work, "site")
            shutil.copytree(DIST, stripped)
            n_scripts = 0
            for rel in dist_files(stripped):
                if rel.endswith(".html"):
                    s = read(rel, stripped)
                    n_scripts += s.count("<script")
                    s = re.sub(r"<script\b.*?</script>", "", s, flags=re.S)
                    with open(os.path.join(stripped, rel), "w", encoding="utf-8", newline="\n") as fh:
                        fh.write(s)
            prof = os.path.join(work, "profile")
            base = ["--headless", "--disable-gpu", "--no-first-run", "--disable-extensions", "--disable-sync",
                    "--disable-background-networking", f"--user-data-dir={prof}", "--dump-dom"]
            off_url = "file:///" + os.path.join(stripped, "ledger", "index.html").replace(os.sep, "/")
            on_url = "file:///" + os.path.join(DIST, "ledger", "index.html").replace(os.sep, "/")
            off = run([EDGE, *base, off_url], timeout=90)
            on = run([EDGE, *base, on_url], timeout=90)
            off_rows = off.stdout.count('data-verification="')
            off_hidden = re.search(r'<form id="filters"[^>]*\bhidden', off.stdout) is not None
            on_shown = re.search(r'<form id="filters"[^>]*\bhidden', on.stdout) is None and 'id="filters"' in on.stdout
            on_count = re.search(r'<output id="filter-count"[^>]*>([^<]*)<', on.stdout)
            pages_ok = []
            for rel in [r for r in dist_files(stripped) if r.endswith("index.html")]:
                u = "file:///" + os.path.join(stripped, rel).replace(os.sep, "/")
                d = run([EDGE, *base, u], timeout=90).stdout
                pages_ok.append('<main id="main"' in d and "</footer>" in d)
            ok &= off_rows == len(entries) and off_hidden and on_shown and all(pages_ok)
            detail += (f"; headless Edge on a script-stripped copy ({n_scripts} script blocks removed): "
                       f"{sum(pages_ok)}/{len(pages_ok)} pages render main+footer, ledger shows {off_rows} tags, "
                       f"filter form stays hidden={off_hidden}; with scripts: form revealed={on_shown}, "
                       f"counter='{on_count.group(1) if on_count else '?'}'")
        except Exception as exc:  # noqa: BLE001
            detail += f"; headless Edge check errored: {exc}"
            ok = False
        finally:
            shutil.rmtree(work, ignore_errors=True)
    else:
        not_run("Headless JS-off render", "Edge not found")
    record("Pages render with JS off", "static check + msedge --headless --dump-dom on a script-stripped copy", ok, detail)


ROUTES = ["/", "/index.html", "/not-done/", "/ledger/", "/ledger.json", "/about/", "/ai/", "/style.css",
          "/projects/", "/projects/gin/", "/projects/sear/", "/projects/receipts/", "/projects/latch/",
          "/projects/backstop/", "/projects/priceriot/", "/projects/qsr-erp/", "/projects/tunedin/",
          "/fonts/BarlowCondensed-SemiBold.ttf", "/fonts/BarlowCondensed-ExtraBold.ttf", "/fonts/OFL.txt"]


def check_live(base):
    out, ok = [], True
    routes = ROUTES + ["/" + r.replace("index.html", "") for r in dist_files() if r.startswith("ledger/") and r.count("/") > 1]
    for r in sorted(set(routes)):
        try:
            with urllib.request.urlopen(base.rstrip("/") + r, timeout=10) as resp:
                code = resp.status
        except Exception as exc:  # noqa: BLE001
            code = getattr(exc, "code", str(exc))
        ok &= code == 200
        out.append(f"{r} {code}")
    record("Live: every route returns 200 from the loopback server", f"HTTP GET x{len(out)} (URL in the final report, not published)", ok, "; ".join(out))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", help="base URL of a running server")
    ap.add_argument("--date", default=os.environ.get("PORTFOLIO_BUILD_DATE", dt.date.today().isoformat()))
    ap.add_argument("--no-write", action="store_true")
    ap.add_argument("--skip-local-repos", action="store_true",
                    help="skip LINKED-at-SHA checks against local workstation clones (for CI / server deploys)")
    args = ap.parse_args(argv if "argv" in locals() else None)

    check_tests()
    check_build_fails_on_bad_ledger()
    check_determinism(args.date)
    p = run([PY, "build.py", "--date", args.date], cwd=ROOT)
    if p.returncode != 0:
        print(p.stderr)
        sys.exit(1)
    if args.skip_local_repos:
        not_run("Every LINKED entry: path exists at SHA, SHA on named branch",
                "skipped via --skip-local-repos (local source repos unavailable in this environment)")
    else:
        check_linked_at_sha()
    check_external_and_secrets()
    parsed = check_links_and_html()
    check_contrast()
    check_banned(parsed)
    check_keyboard_static(parsed)
    check_nojs(parsed)
    if args.live:
        check_live(args.live)
    else:
        not_run("Live route check", "no --live URL given in this run")
    not_run("Full W3C/Nu HTML validation", "no validator on this machine (no vnu, tidy or java); a stdlib structural check ran instead")
    not_run("Interactive keyboard traversal in a real browser", "no browser automation driver available without installing one; static keyboard checks ran instead")
    not_run("Screen-reader pass", "no screen reader automation available")
    not_run("Automated visual regression test", "none exists; instead the agent looked at headless-Edge screenshots (1280px dark and light, a 375px iframe for phone width) on 2026-11-20 and again after the 2026-11-22 restyle, which found and led to fixing phone-width overflows; the author chose the direction from mockups but has not reviewed the built pages")
    not_run("Re-running the source repos' own test suites", "repos are read-only for this build; running pytest/npm would write caches into them")

    if not args.no_write:
        doc = {"date": args.date, "checks": RESULTS, "not_run": NOT_RUN}
        with open(os.path.join(ROOT, "content", "site_checks.json"), "w", encoding="utf-8", newline="\n") as fh:
            json.dump(doc, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
    fails = [r for r in RESULTS if r["result"] != "PASS"]
    print(f"\n{len(RESULTS) - len(fails)} PASS, {len(fails)} FAIL, {len(NOT_RUN)} NOT RUN")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
