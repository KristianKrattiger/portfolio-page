"""The single stylesheet: concrete wall, punched tags, label tape.

Palette tokens are also read by verify/verify.py for WCAG contrast checks, so the
CSS is generated from PALETTE. Colour encodes epistemic family only:
done = black tape on a white tag, failed = red tape on a white tag,
unfinished = yellow tape on a manila tag. Every state also has a word and a shape.
"""

PALETTE = {
    "light": {
        "wall": "#C9C8C3",       # concrete
        "wall-ink": "#141414",   # text on the wall
        "wall-ink-2": "#34332F",
        "wall-rule": "#141414",
        "tag": "#FFFFFF",        # white tag
        "manila": "#E6DAB8",     # unfinished work sits on manila
        "ink": "#141414",        # text on tags
        "ink-2": "#46443E",
        "rule": "#141414",
        "rule-soft": "#77746C",
        "signal": "#A3191E",     # AUTHOR-REPORTED / UNKNOWN / disagreement (on tags only)
        "tape-done": "#141414", "tape-done-ink": "#F4F4F0",
        "tape-failed": "#A3191E", "tape-failed-ink": "#FFFFFF",
        "tape-unf": "#F2C500", "tape-unf-ink": "#141414",
        "tape-edge": "#141414",
    },
    "dark": {
        "wall": "#1C1C1B",       # asphalt
        "wall-ink": "#ECEAE4",
        "wall-ink-2": "#B3B0A8",
        "wall-rule": "#8A877F",
        "tag": "#E9E7E1",        # tags stay light, as if under a streetlight
        "manila": "#D6C9A4",
        "ink": "#141414",
        "ink-2": "#403E39",
        "rule": "#141414",
        "rule-soft": "#6E6B64",
        "signal": "#8E1519",
        "tape-done": "#141414", "tape-done-ink": "#F4F4F0",
        "tape-failed": "#A3191E", "tape-failed-ink": "#FFFFFF",
        "tape-unf": "#F2C500", "tape-unf-ink": "#141414",
        "tape-edge": "#ECEAE4",
    },
}

# Pairs checked by verify.py: (foreground, background, minimum ratio, what)
CONTRAST_PAIRS = [
    ("wall-ink", "wall", 4.5, "text on the wall"),
    ("wall-ink-2", "wall", 4.5, "secondary text on the wall"),
    ("wall-rule", "wall", 3.0, "hairlines on the wall (non-text)"),
    ("ink", "tag", 4.5, "text on a white tag"),
    ("ink", "manila", 4.5, "text on a manila tag"),
    ("ink-2", "tag", 4.5, "secondary text on a white tag"),
    ("ink-2", "manila", 4.5, "secondary text on a manila tag"),
    ("signal", "tag", 4.5, "signal text on a white tag"),
    ("signal", "manila", 4.5, "signal text on a manila tag"),
    ("rule-soft", "tag", 3.0, "soft hairline on a white tag (non-text)"),
    ("rule-soft", "manila", 3.0, "soft hairline on a manila tag (non-text)"),
    ("tape-done-ink", "tape-done", 4.5, "DONE tape text"),
    ("tape-failed-ink", "tape-failed", 4.5, "FAILED tape text"),
    ("tape-unf-ink", "tape-unf", 4.5, "UNFINISHED tape text"),
    ("tape-edge", "wall", 3.0, "tape edge on the wall (non-text)"),
    ("rule", "tag", 3.0, "tag border and punch hole (non-text)"),
]


def _vars(p):
    return "".join(f"--{k}:{v};" for k, v in p.items())


CSS = f"""@font-face{{font-family:"Barlow Condensed";font-weight:600;font-style:normal;font-display:swap;src:url("fonts/BarlowCondensed-SemiBold.ttf") format("truetype")}}
@font-face{{font-family:"Barlow Condensed";font-weight:800;font-style:normal;font-display:swap;src:url("fonts/BarlowCondensed-ExtraBold.ttf") format("truetype")}}
:root{{{_vars(PALETTE['light'])}
--cond:"Barlow Condensed","Arial Narrow","Roboto Condensed",Arial,sans-serif;
--serif:Charter,"Iowan Old Style","Bitstream Charter",Georgia,"Times New Roman",serif;
--mono:ui-monospace,"Cascadia Mono","SF Mono",Menlo,Consolas,"Liberation Mono",monospace;
color-scheme:light dark}}
@media (prefers-color-scheme:dark){{:root{{{_vars(PALETTE['dark'])}}}}}
*,*::before,*::after{{box-sizing:border-box;border-radius:0}}
html{{background:var(--wall);color:var(--wall-ink)}}
body{{margin:0 auto;max-width:1180px;padding:0 clamp(16px,3vw,40px) 56px;font:17px/1.5 var(--serif);background:var(--wall);color:var(--wall-ink)}}
a{{color:inherit;text-decoration-thickness:1px;text-underline-offset:.18em}}
a:hover{{text-decoration-thickness:2px}}
:focus-visible{{outline:3px solid var(--tape-unf);outline-offset:2px;box-shadow:0 0 0 5px var(--ink)}}
.skip{{position:absolute;left:-9999px;top:0;background:var(--ink);color:var(--tag);padding:8px 12px;z-index:2}}
.skip:focus{{left:12px}}
.defs{{position:absolute;width:0;height:0;overflow:hidden}}
.mono,code{{font-family:var(--mono);font-size:.84em;letter-spacing:0}}
.small{{font-size:.86rem}}
h1,h2,h3,h4{{font-family:var(--cond);font-weight:800;margin:0;line-height:1;text-transform:uppercase;letter-spacing:.01em}}
/* masthead */
.masthead{{display:flex;flex-wrap:wrap;align-items:baseline;justify-content:space-between;gap:8px 24px;padding:18px 0 12px;border-bottom:3px solid var(--wall-rule)}}
.masthead .who{{margin:0;font-family:var(--cond);font-weight:800;font-size:1.6rem;text-transform:uppercase;letter-spacing:.02em}}
.masthead .who a{{text-decoration:none}}
.masthead ul{{list-style:none;margin:0;padding:0;display:flex;flex-wrap:wrap;gap:4px 20px;font-family:var(--cond);font-weight:600;font-size:1.1rem;text-transform:uppercase;letter-spacing:.04em}}
.masthead a{{text-decoration:none}}
.masthead a:hover,.masthead a[aria-current]{{text-decoration:underline;text-decoration-thickness:3px;text-underline-offset:.22em}}
/* page head */
.lead{{padding:clamp(28px,6vw,64px) 0 20px}}
.title{{font-size:clamp(3rem,10vw,7.5rem);line-height:.86;letter-spacing:-.01em;color:var(--wall-ink)}}
.tagline{{font-family:var(--cond);font-weight:600;font-size:clamp(1.35rem,3.2vw,2.2rem);line-height:1.12;margin:14px 0 0;max-width:30ch}}
.dek{{font-size:1.1rem;margin:16px 0 0;max-width:62ch;color:var(--wall-ink)}}
.wallnote{{color:var(--wall-ink-2);font-family:var(--mono);font-size:.82rem;margin:8px 0 0}}
h2.band{{font-size:clamp(1.8rem,4.4vw,3rem);padding:12px 0 10px;margin:40px 0 16px;border-top:3px solid var(--wall-rule);display:flex;flex-wrap:wrap;align-items:baseline;justify-content:space-between;gap:6px 18px}}
h2.band .strip{{font-size:1rem}}
h3.fam{{font-size:1.25rem;margin:22px 0 10px;display:flex;align-items:center;gap:10px;letter-spacing:.06em}}
h3.fam .n{{font-family:var(--mono);font-weight:400;font-size:.9rem}}
/* tape (state) */
.tape{{display:inline-flex;align-items:center;gap:7px;font-family:var(--mono);font-weight:700;font-size:.8rem;letter-spacing:.16em;text-transform:uppercase;padding:4px 10px 4px 9px;white-space:nowrap;transform:rotate(-1.2deg);border:1px solid var(--tape-edge)}}
.tape .shape{{width:12px;height:12px;flex:none}}
.tape.done{{background:var(--tape-done);color:var(--tape-done-ink)}}
.tape.failed{{background:var(--tape-failed);color:var(--tape-failed-ink)}}
.tape.unfinished{{background:var(--tape-unf);color:var(--tape-unf-ink)}}
.tag .tape{{border-color:var(--rule)}}
/* stickers (verification, stale) */
.stk{{display:inline-block;font-family:var(--mono);font-size:.74rem;letter-spacing:.06em;padding:2px 6px;white-space:nowrap}}
.stk-linked{{border:1.5px solid var(--ink);color:var(--ink)}}
.stk-author{{border:1.5px dashed var(--signal);color:var(--signal)}}
.stk-stale{{background:var(--ink);color:var(--tag);border:1.5px solid var(--ink)}}
.stk-flag{{border:1.5px dotted var(--ink-2);color:var(--ink-2)}}
.unknown{{color:var(--signal);font-family:var(--mono);font-size:.86em;border-bottom:1.5px dashed var(--signal)}}
.sig{{color:var(--signal)}}
/* tags */
.tag{{position:relative;background:var(--tag);color:var(--ink);border:1.5px solid var(--rule);margin:0 0 14px;padding:16px 20px 16px 52px;scroll-margin-top:16px}}
.tag.unfinished{{background:var(--manila)}}
.tag::before{{content:"";position:absolute;left:18px;top:21px;width:13px;height:13px;border:1.5px solid var(--rule);background:var(--wall)}}
.tag:target{{outline:4px solid var(--tape-unf);outline-offset:3px}}
.tag .meta{{display:flex;flex-wrap:wrap;align-items:center;gap:8px 10px;margin:0}}
.tag .eid{{font-family:var(--mono);font-size:.8rem;font-weight:700;color:var(--ink)}}
.tag .asof{{font-family:var(--mono);font-size:.78rem;color:var(--ink-2)}}
.tag .proj{{font-family:var(--cond);font-weight:800;font-size:.95rem;text-transform:uppercase;letter-spacing:.06em}}
.tag .claim{{font-family:var(--cond);font-weight:600;font-size:1.42rem;line-height:1.22;margin:10px 0 10px;max-width:60ch;text-transform:none;letter-spacing:0}}
.tag .dns{{margin:0;padding-top:8px;border-top:1px solid var(--rule-soft);max-width:72ch}}
.lbl{{display:inline-block;font-family:var(--mono);font-weight:700;font-size:.72rem;letter-spacing:.1em;text-transform:uppercase;margin-right:8px;color:var(--ink)}}
.tag dl{{margin:8px 0 0;display:grid;grid-template-columns:minmax(0,9rem) minmax(0,1fr);gap:0 14px}}
.tag dt{{font-family:var(--mono);font-weight:700;font-size:.72rem;letter-spacing:.1em;text-transform:uppercase;padding:8px 0;border-top:1px solid var(--rule-soft)}}
.tag dd{{margin:0;padding:7px 0;border-top:1px solid var(--rule-soft);min-width:0;max-width:78ch}}
.tag details{{margin-top:10px;border-top:1px solid var(--rule-soft);padding-top:6px}}
.tag summary{{cursor:pointer;font-family:var(--mono);font-size:.78rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase;padding:4px 0}}
.ev{{margin:4px 0 0;padding-left:1.1em;font-size:.92rem}}
.ev li{{margin:0 0 4px}}
.tier{{font-family:var(--mono);font-size:.72rem;color:var(--ink-2);margin-left:4px}}
.mono,.ev,.eid,td{{overflow-wrap:anywhere}}
.tape,.stk{{overflow-wrap:normal}}
/* home: big tape counts */
.counts{{display:flex;flex-wrap:wrap;gap:18px 22px;margin:26px 0 10px;padding:0;list-style:none}}
.counts li{{margin:0}}
.counts a{{text-decoration:none;display:block}}
.bigtape{{display:inline-flex;align-items:baseline;gap:14px;font-family:var(--cond);font-weight:800;text-transform:uppercase;letter-spacing:.04em;font-size:clamp(1.3rem,3vw,1.9rem);padding:10px 18px 8px 16px;border:1.5px solid var(--tape-edge);transform:rotate(-1deg)}}
.bigtape .num{{font-size:clamp(2.6rem,7vw,4.6rem);line-height:.9}}
.bigtape .shape{{width:22px;height:22px;align-self:center}}
.bigtape.done{{background:var(--tape-done);color:var(--tape-done-ink)}}
.bigtape.failed{{background:var(--tape-failed);color:var(--tape-failed-ink)}}
.bigtape.unfinished{{background:var(--tape-unf);color:var(--tape-unf-ink)}}
/* project rows */
.projrows{{list-style:none;margin:0;padding:0}}
.projrow{{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:4px 20px;align-items:baseline;padding:12px 0;border-top:1.5px solid var(--wall-rule)}}
.projrow:last-child{{border-bottom:1.5px solid var(--wall-rule)}}
.projrow .pname{{font-family:var(--cond);font-weight:800;font-size:clamp(1.6rem,4vw,2.4rem);text-transform:uppercase;line-height:1;text-decoration:none}}
.projrow .pname:hover{{text-decoration:underline;text-decoration-thickness:3px}}
.projrow .psub{{display:block;font-size:.95rem;color:var(--wall-ink-2);margin-top:4px;font-family:var(--serif);text-transform:none;font-weight:400}}
.strip{{display:inline-flex;flex-wrap:wrap;gap:6px;font-family:var(--mono);font-size:.85rem;font-weight:700;align-items:center}}
.chip{{display:inline-flex;align-items:center;gap:5px;padding:2px 7px;border:1px solid var(--tape-edge)}}
.chip .shape{{width:10px;height:10px}}
.chip.done{{background:var(--tape-done);color:var(--tape-done-ink)}}
.chip.failed{{background:var(--tape-failed);color:var(--tape-failed-ink)}}
.chip.unfinished{{background:var(--tape-unf);color:var(--tape-unf-ink)}}
.chip.zero{{opacity:1;background:transparent;color:var(--wall-ink-2);border-style:dashed;border-color:var(--wall-ink-2)}}
/* sheets: white paper pinned to the wall, for prose and tables */
.sheet{{background:var(--tag);color:var(--ink);border:1.5px solid var(--rule);padding:18px 22px;margin:0 0 16px;overflow-wrap:anywhere}}
.sheet h3{{font-size:1.2rem;margin:18px 0 8px;letter-spacing:.05em}}
.sheet h3:first-child{{margin-top:0}}
.sheet p{{max-width:72ch}}
.sheet a{{color:var(--ink)}}
.about{{margin:0;display:grid;grid-template-columns:minmax(0,9rem) minmax(0,1fr);gap:0 18px}}
.about dt{{font-family:var(--mono);font-weight:700;font-size:.74rem;letter-spacing:.1em;text-transform:uppercase;padding:10px 0;border-top:1px solid var(--rule-soft)}}
.about dd{{margin:0;padding:9px 0;border-top:1px solid var(--rule-soft);min-width:0}}
.about ul{{margin:0;padding:0;list-style:none}}
.about li{{margin:0 0 5px}}
.seen{{font-family:var(--mono);font-size:.74rem;color:var(--ink-2)}}
ul.plain{{list-style:none;padding:0;margin:0}}
ul.plain>li{{border-top:1px solid var(--rule-soft);padding:8px 0}}
.jump ul,.jump ol{{list-style:none;padding:0;margin:0 0 6px;display:flex;flex-wrap:wrap;gap:6px 18px;font-family:var(--cond);font-weight:600;font-size:1.05rem;text-transform:uppercase;letter-spacing:.04em}}
/* tables */
.scroll{{overflow-x:auto;margin:6px 0 4px}}
table{{border-collapse:collapse;width:100%;font-size:.9rem}}
caption{{text-align:left;font-family:var(--mono);font-size:.76rem;text-transform:uppercase;letter-spacing:.08em;padding:6px 0 8px;color:var(--ink-2)}}
th{{text-align:left;font-family:var(--mono);font-weight:700;font-size:.74rem;text-transform:uppercase;letter-spacing:.06em;border-bottom:1.5px solid var(--rule)}}
th,td{{padding:7px 10px 7px 0;vertical-align:top;border-bottom:1px solid var(--rule-soft)}}
table.nums{{min-width:720px}}
td.date,td.nowrap{{white-space:nowrap;overflow-wrap:normal}}
/* filters */
.filters{{display:flex;flex-wrap:wrap;gap:10px 18px;align-items:center;padding:12px 16px;background:var(--tag);color:var(--ink);border:1.5px solid var(--rule);font-family:var(--mono);font-size:.85rem}}
.filters select,.filters button{{font:inherit;background:var(--tag);color:var(--ink);border:1.5px solid var(--ink);padding:4px 6px}}
.facets{{list-style:none;padding:0;margin:10px 0 0;font-family:var(--mono);font-size:.82rem;color:var(--wall-ink)}}
.facets li{{margin:0 0 5px}}
.facets a{{margin-right:10px}}
.foot{{margin-top:56px;border-top:3px solid var(--wall-rule);padding-top:10px;color:var(--wall-ink-2);font-family:var(--mono);font-size:.8rem}}
.foot p{{margin:0}}
@media (max-width:640px){{
body{{font-size:16px}}
.tag{{padding:14px 14px 14px 40px}}
.tag::before{{left:13px;top:19px;width:11px;height:11px}}
.tag .claim{{font-size:1.25rem}}
.tag dl,.about{{display:block}}
.tag dd,.about dd{{border-top:0;padding-top:0}}
.projrow{{grid-template-columns:minmax(0,1fr)}}
.sheet{{padding:14px}}
}}
@media print{{.masthead nav,.filters{{display:none}}.tape,.bigtape{{transform:none}}}}
"""
