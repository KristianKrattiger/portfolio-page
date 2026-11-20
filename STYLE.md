# STYLE.md

Derived from the FORM and VOICE sections of the brief. Checked against the output
before finishing (`python verify/verify.py --banned` enforces the mechanical part).

## Form

- Warm industrial minimalism: Bauhaus grid, brutalist honesty of structure,
  deep-club restraint, faded SoCal / central-coast paper.
- Rigid visible grid. Hairline rules (1px) separate everything. No cards, no
  shadows, no rounded corners (border-radius: 0 everywhere).
- Big asymmetric type for page titles (left-aligned, oversized, off-centre
  against the grid). Body text in a plain sans stack. Data, status, ids, dates,
  counts and evidence in monospace.
- Flat surfaces. One subtle grain/fade texture, CSS only, at very low opacity.
- Palette:
  - Light: sun-bleached warm paper background, warm charcoal ink.
  - Dark (prefers-color-scheme: dark): deep warm charcoal background, paper ink.
  - One oxidized signal accent (rust).
- **Color encodes epistemic status and nothing else.** The accent marks what is
  NOT re-verified: AUTHOR-REPORTED, UNKNOWN, STALE, and disagreements between
  sources. LINKED evidence is plain ink. Links, headings and decoration never
  use the accent.
- **Color is never the only carrier.** Every state has a text label AND a
  distinct shape; every verification level has a text label AND a distinct
  border style (solid = LINKED, dashed = AUTHOR-REPORTED).

  | State | Shape |
  |---|---|
  | MEASURED | filled square |
  | BUILT | open square |
  | IN-PROGRESS | half-filled square |
  | DESIGN-ONLY | open diamond |
  | BLOCKED | square with a bar |
  | NOT-DONE | open circle |
  | KILLED | cross |
  | NEGATIVE-RESULT | downward triangle |

- The "not done" side carries the same typographic weight as the "done" side:
  same type size, same table, same placement rules. Negative results are never
  greyed out, collapsed or footnoted.
- All palette pairs must pass WCAG AA (4.5:1 for text) in both schemes.

## Avoid (hard bans)

Gradient hero; "Hi, I'm..."; "passionate about"; skill bars or percentages of
skill; tech-logo walls; testimonial carousels; stock photos; glassmorphism
(backdrop-filter); bento grids; particles; parallax; scroll-jacking;
typewriter text; neon "hacker terminal" cosplay; rounded-card soup
(border-radius); emoji bullets; AI-sparkle iconography.

## Voice

- First person, plain, declarative. Short sentences.
- No superlatives ("best", "cutting-edge", "world-class", "revolutionary").
- No "novel" or "groundbreaking" (no evidence is linked that would earn them).
- No "passionate", "innovative", "leverage", "seamless", "robust" (as praise),
  "state-of-the-art", "game-changing", "excited to".
- Hedge only where uncertainty is real, and say what would resolve it.
- Every factual sentence comes from a ledger entry. Prose that is not a ledger
  claim is limited to navigation, method, and the one paragraph on what I work on.
- Missing facts render as `UNKNOWN — author to supply`, never as plausible prose.
- Never name or explain the alias. Never mention employers, job search, grades,
  family/partner/collaborator names, the compliance-venture idea, finances,
  health, or location.

## Banned-pattern list (machine-checked in dist/)

Phrases (case-insensitive): `hi, i'm`, `hi i'm`, `passionate`, `groundbreaking`,
`novel`, `cutting-edge`, `cutting edge`, `world-class`, `revolutionary`,
`game-changing`, `state-of-the-art`, `innovative`, `leverage`, `seamless`,
`excited to`, `rockstar`, `ninja`, `10x`, `ex-opere`, `exopere`, `ex opere`.

CSS/markup patterns: `linear-gradient(` used on a hero, `backdrop-filter`,
`border-radius` with a non-zero value, `parallax`, `typewriter`, emoji
characters in the Unicode pictograph ranges, `<marquee`, `@import url(http`.
