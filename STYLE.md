# STYLE.md

Derived from the FORM and VOICE sections of the brief. Checked against the output
before finishing (`python verify/verify.py --banned` enforces the mechanical part).

## Form (restyled 2026-11-22; design: docs/superpowers/specs/2026-11-22-restyle-design.md)

- Concrete wall, punched tags, label tape. Reference: the secondhand, layered side
  of Shimokitazawa. Cohesive, imposing (the facts are hard to avoid), minimal (a
  hiring manager gets it in one pass).
- **Wall**: concrete grey (light) / asphalt (dark). Page chrome sits on the wall.
- **Tags**: every ledger entry is a white tag with a hard ink border and a square
  punch hole. Tags stay light in dark mode. Prose and tables sit on white sheets.
- **Type**: Barlow Condensed (bundled, OFL) for headings, claims, tape and counts;
  the platform serif for prose; the platform monospace for data, ids and dates.
- No rounded corners, no shadows, no gradients, no grain. The only tilt is a
  1-degree rotation on label tape.
- **Colour encodes epistemic family and nothing else.**
  - Done (MEASURED, BUILT): black tape, white tag.
  - Failed (KILLED, NEGATIVE-RESULT): red tape, white tag.
  - Unfinished (IN-PROGRESS, DESIGN-ONLY, BLOCKED, NOT-DONE): yellow tape, manila tag.
  - Verification stickers: LINKED = solid outline; AUTHOR-REPORTED = dashed red;
    STALE = black sticker. UNKNOWN = red dashed underline.
- **Colour is never the only carrier.** Every state has its word and a shape:

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

- The not-done side carries the same weight as the done side: same tag, same
  type size, same placement. Failed and unfinished counts are as large as done.
- All palette pairs must pass WCAG AA (4.5:1 text, 3:1 non-text) in both schemes.

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
