# Restyle: "concrete wall, punched tags, label tape" — design

Date: 2026-11-22. Status: approved by the author in conversation ("write then implement").

## Intent and why
The first build read as "made by Claude": cream paper plus a burnt-orange accent is Claude's own
palette, and the 7-column ledger table was hard to track (two prose columns side by side, small
uppercase status labels, no project breaks). The author wants the site to feel **cohesive,
forward-thinking, somewhat abstract, imposing** (you cannot run from the facts) and **minimal** (a
hiring manager gets it in one pass). Reference place: Shimokitazawa, specifically its
secondhand, layered side. Chosen direction, from mockups: mix 1 of A (thrift tags) and C (label
maker on concrete).

## Goals
- A visual system that is not Claude's palette and makes every entry's epistemic state
  impossible to miss.
- A ledger a hiring manager can scan: one tag per entry, grouped by project, then by family.
- A home page that leads with what failed and what is unfinished as loudly as what is done.
- An About section with education, focus, skills and every project.
- Three more projects (PriceRiot, TunedIn, QSR ERP) held to the same ledger rules.

## Non-goals
- No change to the validator's build-fail rules, the evidence tiers, or the truth rules.
- No new runtime dependencies, no third-party requests, no JS requirement.
- No change to hosting (loopback, port 8787, Startup launcher).

## Anti-goals (failure even if it works)
- Looking cluttered or "themed" in a way that slows reading.
- Colour carrying anything other than epistemic family.
- Naming teammates, employers, or anything the original brief excludes.

## Approaches considered
1. **Restyle in place (chosen).** Keep validate/build/verify; rewrite `portfolio/style.py` and the
   markup in `portfolio/render.py`; extend content. The parts that work (build-fail rules,
   SHA-pinned evidence, checks) are not what is wrong.
2. Full rewrite of the generator. Gains nothing; risks the checks.
3. Theme layer over current markup. Cannot produce tags or the new home without markup changes.

## Visual system (decided with the author)
- **Wall**: light = concrete grey; dark = asphalt. Page chrome (masthead, headings, counts) sits on
  the wall.
- **Tags**: every entry is a punched tag (square punch hole, keeping the no-rounded-corners rule)
  with a hard 1.5px ink border. Tags stay light in dark mode ("under a streetlight"), so long text
  keeps contrast.
- **Families** (colour encodes family only):
  - Done (MEASURED, BUILT): black label tape, white tag.
  - Failed (KILLED, NEGATIVE-RESULT): red label tape, white tag.
  - Unfinished (IN-PROGRESS, DESIGN-ONLY, BLOCKED, NOT-DONE): yellow label tape, manila tag.
  - Inside a family the existing square-family SVG shapes plus the word distinguish states.
- **Stickers** (verification): LINKED = solid outline; AUTHOR-REPORTED = dashed red outline;
  STALE = black sticker. UNKNOWN keeps the red dashed underline.
- **Type**: Barlow Condensed (OFL, bundled in dist/, two weights) for headings, claims, tape and
  counts; a system serif for prose ("does not show", About); system monospace for data.
- Light texture: none beyond the wall colour (the grain filter is removed; it read as the old look).

## Pages
- **Masthead**: name (condensed, uppercase) + nav: Ledger · Not done · Projects · About · Colophon.
- **Home**: name, tagline (author picked option 2): "AI verification and grounding: what I built,
  what I measured, and what didn't work." Three large tape counts (Done / Failed / Unfinished),
  one line of verification counts (linked · author-reported · stale), then one row per project
  with its family counts (Research: GIN, SEAR, Receipts + Assay, Latch; Other work: PriceRiot,
  QSR ERP, TunedIn), then an **About** block (Education, Focus, Works in, Skills, Projects,
  Contact), then the three newest tags.
- **Ledger**: grouped by project (heading + family count strip), then Done / Failed / Unfinished
  tags inside. One column of full-width tags. Each tag shows: tape, verification sticker, STALE,
  `#id`, as_of, claim (large), "Does not show" (directly under). Measurements, results, kill
  criterion, blocker and disagreement are shown on the tag; evidence and notes sit in a
  `<details>` (works with JS off). Stable `#id` anchors on the tag itself (the separate table and
  `full-<id>` blocks go away). JS filters (project/state/verification) hide tags and empty groups;
  the pre-rendered facet pages stay as the no-JS fallback.
- **Not done**: same tags, grouped by state as now.
- **Projects index** (new, `projects/`): research and other work, one row each with counts.
- **Project pages**: the fixed section order stays; entries render as tags; the evidence index
  table sits on a white sheet.
- **About**: full version of the home About block; skills list marks what a repo backs versus
  what is author-reported; open threads stay.
- **Colophon**: text updated (bundled font, new palette); checks table on a white sheet.

## Content
- `site.json`: new `line` (tagline above), `about` block, `skills` list with evidence markers,
  `group` per project (research | other), three new projects.
- Skills (author-reported unless a repo backs it): Python analytics stack (pandas, NumPy,
  Matplotlib, seaborn: PriceRiot requirements), Streamlit (PriceRiot dashboard), ETL pipelines
  (PriceRiot POS ingestion), SQL / SQLite (QSR ERP), Excel incl. Analytic Solver and the Data
  Science tabs (author-reported), ERP / SAP (author-reported; QSR ERP backs ERP design), data
  mining techniques from ISDS 474 (author-reported, coursework), plus languages the repos show
  (C++17, C#/.NET, TypeScript).
- New ledger entries (walked read-only, SHAs recorded in SOURCES.md):
  - PriceRiot @ main 2870b22: engine (BUILT/LINKED), POS ETL (BUILT/LINKED), analysis apps
    (BUILT/LINKED), not-built items incl. per-run staff edits and the deferred pricing / sweep /
    optimizer / ML work (NOT-DONE/LINKED: route absent from app.py).
  - QSR ERP @ main 72a912e: database (BUILT/LINKED), app framework (BUILT/LINKED), the author's
    role and team lead (IN-PROGRESS/AUTHOR-REPORTED; teammates unnamed), extensions plan on
    branch extensions-plan 35eec27 (DESIGN-ONLY/AUTHOR-REPORTED).
  - TunedIn (not under git; README mtime 2026-09-15): app (BUILT/AUTHOR-REPORTED), README's own
    known gaps (NOT-DONE/AUTHOR-REPORTED).
- Repo visibility for PriceRiot and QSR ERP is not confirmed: shown as path + SHA, no links
  (consistent with sear-demo, Latch, assay).

## Checks to update
- Contrast pairs for the new tokens (text on tag, manila, wall; tape text on tape; sticker red on
  tag and manila; hairlines), both schemes.
- CSP adds `font-src 'self'`; the host scan must still see no third-party hosts.
- Live route list adds `projects/` and the new project pages.
- Private-term scan adds the teammates' first names as SHA-256 hashes only (so the names never
  enter the repo, yet a leak into dist/ still fails the check).
- Validator `PROJECTS` adds `priceriot`, `qsr-erp`, `tunedin`.

## Builder's calls (marked as mine)
- Barlow Condensed over Archivo Narrow (road-sign origin; Archivo is the fallback if disliked).
- TTF files served as-is (no woff2: converting needs a non-stdlib tool).
- Grain texture removed. Tape tilt is a 1–2 degree rotation on the tape only, not the tag.
- Evidence moves into `<details>` on ledger tags; project pages keep it open.
- TunedIn's solo/group status and the author's part in it are UNKNOWN → NEEDS_AUTHOR.
