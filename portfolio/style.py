"""The single stylesheet. Palette tokens are also read by verify/verify.py for
WCAG contrast checks, so keep the PALETTE dicts and CSS in sync (CSS is built
from them)."""

PALETTE = {
    "light": {
        "paper": "#EEE7D7",    # sun-bleached warm paper
        "paper-2": "#E3D9C4",  # table heads, flat
        "ink": "#1D1A16",      # warm charcoal
        "ink-2": "#4D463C",    # secondary text
        "rule": "#1D1A16",     # hairlines (strong)
        "rule-soft": "#877C67",  # hairlines (soft)
        "signal": "#933815",   # oxidized rust: NOT re-verified / UNKNOWN / STALE / disagreement
    },
    "dark": {
        "paper": "#161412",
        "paper-2": "#221F1B",
        "ink": "#E9E1D0",
        "ink-2": "#B5AA96",
        "rule": "#E9E1D0",
        "rule-soft": "#7A7062",
        "signal": "#E8895A",
    },
}

# Pairs checked by verify.py: (foreground, background, minimum ratio, what)
CONTRAST_PAIRS = [
    ("ink", "paper", 4.5, "body text"),
    ("ink", "paper-2", 4.5, "table head text"),
    ("ink-2", "paper", 4.5, "secondary text"),
    ("ink-2", "paper-2", 4.5, "secondary text on table head"),
    ("signal", "paper", 4.5, "signal text (AUTHOR-REPORTED, UNKNOWN, STALE)"),
    ("signal", "paper-2", 4.5, "signal text on table head"),
    ("rule-soft", "paper", 3.0, "soft hairline (non-text, WCAG 1.4.11)"),
    ("rule", "paper", 3.0, "strong hairline (non-text)"),
]


def _vars(p):
    return "".join(f"--{k}:{v};" for k, v in p.items())


GRAIN = ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='160' height='160'%3E"
         "%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='2' "
         "stitchTiles='stitch'/%3E%3CfeColorMatrix values='0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 .55 0'/%3E"
         "%3C/filter%3E%3Crect width='160' height='160' filter='url(%23n)'/%3E%3C/svg%3E")

CSS = f""":root{{{_vars(PALETTE['light'])}
--sans:"Helvetica Neue",Helvetica,Arial,"Nimbus Sans","Liberation Sans",sans-serif;
--mono:ui-monospace,"Cascadia Mono","SF Mono",Menlo,Consolas,"Liberation Mono",monospace;
color-scheme:light dark}}
@media (prefers-color-scheme:dark){{:root{{{_vars(PALETTE['dark'])}}}}}
*,*::before,*::after{{box-sizing:border-box;border-radius:0}}
html{{background:var(--paper);color:var(--ink)}}
body{{margin:0;font:16px/1.5 var(--sans);background:var(--paper);color:var(--ink);
max-width:1280px;margin-inline:auto;padding:0 clamp(12px,3vw,40px) 48px;
border-left:1px solid var(--rule-soft);border-right:1px solid var(--rule-soft);position:relative}}
body::after{{content:"";position:fixed;inset:0;pointer-events:none;background-image:url("{GRAIN}");
opacity:.07;mix-blend-mode:multiply}}
@media (prefers-color-scheme:dark){{body::after{{mix-blend-mode:screen;opacity:.035}}}}
a{{color:inherit;text-decoration-thickness:1px;text-underline-offset:.18em}}
a:hover{{text-decoration-thickness:2px}}
:focus-visible{{outline:2px solid var(--ink);outline-offset:2px}}
.skip{{position:absolute;left:-9999px;top:0;background:var(--ink);color:var(--paper);padding:8px 12px;z-index:2}}
.skip:focus{{left:12px}}
.defs{{position:absolute;width:0;height:0;overflow:hidden}}
.mono,code,table.ledger td.mono{{font-family:var(--mono);font-size:.86em;letter-spacing:0}}
.small{{font-size:.84rem}}
h1,h2,h3{{font-weight:700;letter-spacing:-.01em;margin:0}}
h2{{font-size:1.35rem;padding:14px 0 10px;border-top:1px solid var(--rule);margin-top:28px}}
h3{{font-size:1.05rem;margin:18px 0 6px}}
/* masthead */
.masthead{{display:grid;grid-template-columns:repeat(12,minmax(0,1fr));border-bottom:1px solid var(--rule);padding:14px 0 10px;gap:0 16px}}
.masthead .who{{grid-column:1/span 3;margin:0;font-family:var(--mono);font-size:.9rem;text-transform:uppercase;letter-spacing:.06em}}
.masthead .who a{{text-decoration:none}}
.masthead nav{{grid-column:4/span 9}}
.masthead ul{{list-style:none;margin:0;padding:0;display:flex;flex-wrap:wrap;gap:4px 18px;font-family:var(--mono);font-size:.82rem}}
.masthead a[aria-current]{{text-decoration-thickness:2px;font-weight:700}}
@media (max-width:760px){{.masthead .who,.masthead nav{{grid-column:1/-1}}.masthead nav{{margin-top:8px}}}}
/* grid */
.grid{{display:grid;grid-template-columns:repeat(12,minmax(0,1fr));gap:0 16px}}
.lead{{border-bottom:1px solid var(--rule);padding:clamp(28px,6vw,72px) 0 18px;align-items:end}}
.title{{grid-column:1/span 9;font-size:clamp(3.2rem,11vw,9rem);line-height:.86;letter-spacing:-.045em;font-weight:800;margin-left:-.04em}}
.id-block{{grid-column:10/span 3;border-left:1px solid var(--rule);padding-left:12px;font-size:.82rem}}
.id-block p{{margin:0 0 4px}}
.dek{{grid-column:1/span 8;font-size:1.15rem;margin:18px 0 0;max-width:62ch}}
.split{{border-bottom:1px solid var(--rule)}}
.split .half,.strip .half{{grid-column:span 6;padding:0 0 18px}}
.split .half+.half,.strip .half+.half{{border-left:1px solid var(--rule);padding-left:16px}}
.strip{{border-bottom:1px solid var(--rule);padding-top:14px}}
.strip .half p{{margin:0 0 8px}}
.prose h2{{grid-column:1/span 4;border-top:1px solid var(--rule)}}
.prose .col{{grid-column:5/span 8;border-top:1px solid var(--rule);margin-top:28px;padding-top:14px;max-width:70ch}}
.prose .col p:first-child{{margin-top:0}}
@media (max-width:760px){{
.title,.id-block,.dek,.split .half,.strip .half,.prose h2,.prose .col{{grid-column:1/-1}}
.id-block{{border-left:0;padding-left:0;border-top:1px solid var(--rule);padding-top:8px;margin-top:16px}}
.split .half+.half,.strip .half+.half{{border-left:0;padding-left:0;border-top:1px solid var(--rule)}}
.prose .col{{margin-top:0;border-top:0}}}}
h2 .n{{font-weight:400;margin-left:.4em}}
/* tables */
.scroll{{overflow-x:auto;margin:6px 0 10px;border-top:1px solid var(--rule)}}
table{{border-collapse:collapse;width:100%;font-size:.88rem}}
caption{{text-align:left;font-family:var(--mono);font-size:.78rem;text-transform:uppercase;letter-spacing:.06em;padding:8px 0;color:var(--ink-2)}}
th{{text-align:left;font-family:var(--mono);font-weight:700;font-size:.76rem;text-transform:uppercase;letter-spacing:.05em;background:var(--paper-2);border-bottom:1px solid var(--rule)}}
th,td{{padding:7px 10px 7px 0;vertical-align:top;border-bottom:1px solid var(--rule-soft)}}
th:first-child,td:first-child{{padding-left:6px}}
table.ledger{{min-width:1000px}}
table.ledger td:nth-child(6){{min-width:22rem}}
table.nums{{min-width:760px}}
table.counts{{width:auto;min-width:min(100%,420px)}}
table.counts td.num{{text-align:right;font-size:1.6rem;font-weight:700;padding-right:18px}}
.gloss{{color:var(--ink-2);font-size:.86rem}}
/* status */
.st{{display:inline-flex;align-items:center;gap:6px;font-family:var(--mono);font-size:.76rem;font-weight:700;letter-spacing:.04em;white-space:nowrap}}
.shape{{width:12px;height:12px;flex:none}}
.vf{{display:inline-block;font-family:var(--mono);font-size:.72rem;letter-spacing:.04em;padding:1px 5px;white-space:nowrap}}
.vf-linked{{border:1px solid var(--ink);color:var(--ink)}}
.vf-author{{border:1px dashed var(--signal);color:var(--signal)}}
.flag{{display:inline-block;font-family:var(--mono);font-size:.72rem;padding:1px 5px;border:1px dotted var(--ink-2);color:var(--ink-2);white-space:nowrap}}
.flag-stale,.sigflag{{border:1px dotted var(--signal);color:var(--signal)}}
.unknown{{color:var(--signal);font-family:var(--mono);font-size:.86em;border-bottom:1px dashed var(--signal)}}
.sig{{color:var(--signal)}}
.ok{{color:var(--ink)}}
/* entries */
.group{{margin-top:8px}}
.group>h2 .st{{font-size:1rem}}
.group>h2 .shape{{width:16px;height:16px}}
.entry{{border-top:1px solid var(--rule-soft);padding:14px 0 6px;display:grid;grid-template-columns:repeat(12,minmax(0,1fr));gap:0 16px}}
.entry .meta{{grid-column:1/-1;margin:0 0 6px;display:flex;flex-wrap:wrap;gap:6px 12px;align-items:center}}
.entry .claim{{grid-column:1/span 9;font-size:1.22rem;line-height:1.3;font-weight:600;margin:0 0 10px;max-width:60ch}}
.entry dl{{grid-column:1/-1;display:grid;grid-template-columns:minmax(0,2fr) minmax(0,10fr);gap:0 16px;margin:0;min-width:0}}
.entry dd,.entry dt{{min-width:0}}
.entry dt{{font-family:var(--mono);font-size:.74rem;text-transform:uppercase;letter-spacing:.05em;padding:7px 0;border-top:1px solid var(--rule-soft);color:var(--ink-2)}}
.entry dd{{margin:0;padding:6px 0;border-top:1px solid var(--rule-soft);max-width:80ch}}
.entry dd .scroll{{max-width:none;border-top:0;margin:0}}
@media (max-width:760px){{.entry,.grid,.masthead{{display:block}}.entry dl{{display:block}}.entry dd{{border-top:0;padding-top:0}}.lead{{padding-top:24px}}}}
.eid{{font-weight:700}}
.mono,.ev,.eid,.dns,td{{overflow-wrap:anywhere}}
td.date{{white-space:nowrap;overflow-wrap:normal}}
table.ledger td:first-child{{min-width:10rem}}
.st,.vf,.flag{{overflow-wrap:normal}}
.ev{{margin:0;padding-left:1.1em}}
.ev li{{margin:0 0 4px}}
.tier{{font-family:var(--mono);font-size:.72rem;color:var(--ink-2);margin-left:4px}}
ul.plain{{list-style:none;padding:0;margin:0}}
ul.plain>li{{border-top:1px solid var(--rule-soft);padding:8px 0}}
.dns{{display:block;color:var(--ink-2);font-size:.88rem}}
.jump ul,.jump ol{{list-style:none;padding:10px 0;margin:0;display:flex;flex-wrap:wrap;gap:4px 16px;font-size:.8rem;border-bottom:1px solid var(--rule-soft)}}
.facets{{list-style:none;padding:0;margin:0 0 10px}}
.facets li{{margin:0 0 4px}}
.facets a{{margin-right:10px}}
.filters{{display:flex;flex-wrap:wrap;gap:10px 18px;align-items:center;padding:12px 0;border-top:1px solid var(--rule)}}
.filters select,.filters button{{font:inherit;background:var(--paper);color:var(--ink);border:1px solid var(--ink);padding:3px 6px}}
.foot{{margin-top:48px;border-top:1px solid var(--rule);padding-top:10px;color:var(--ink-2)}}
.foot p{{margin:0}}
@media print{{body::after{{display:none}}.masthead nav,.filters{{display:none}}}}
"""
