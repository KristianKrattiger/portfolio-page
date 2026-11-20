# SPEC.md — portfolio ledger site

## Purpose
A skeptical reader learns in under a minute what Kristian Krattiger has built,
measured, not built, not tested, and what failed. The NOT-DONE side is a
first-class feature.

## Single source of truth
`content/ledger.yaml`. Format: YAML 1.2, written in its JSON-compatible flow
subset so the stdlib `json` module parses it (zero dependencies). Full-line
`#` comments are allowed and stripped before parsing.

### Entry schema
| field | required | notes |
|---|---|---|
| id | yes | `[a-z0-9-]+`, unique, stable; becomes the `#id` anchor |
| project | yes | one of `gin`, `sear`, `receipts`, `latch`, `offscreen` |
| claim | yes | one plain sentence |
| state | yes | MEASURED, BUILT, IN-PROGRESS, DESIGN-ONLY, BLOCKED, NOT-DONE, KILLED, NEGATIVE-RESULT |
| verification | yes | LINKED or AUTHOR-REPORTED |
| as_of | yes | `YYYY-MM-DD` or `YYYY-MM` |
| evidence | yes | `"UNKNOWN"` or a list of items `{repo, path, branch, sha, tier, dirty, note}`; `repo` may be `vault` or `seed` for non-git sources (then branch/sha may be `"n/a"`) |
| does_not_show | yes | non-empty; `"UNKNOWN — author to supply"` allowed and rendered visibly |
| measurements | MEASURED only | list of `{metric, value, denominator, dataset, synthetic, system, date}`, none UNKNOWN |
| results | optional | same shape as measurements, for non-MEASURED entries (e.g. a NEGATIVE-RESULT with numbers); fields may be UNKNOWN and render visibly |
| reported_result | optional | an author-reported figure whose details are not supplied; renders with a "details not supplied" tag |
| kill_criterion | KILLED only | non-empty, not UNKNOWN |
| blocked_by | BLOCKED only | non-empty, not UNKNOWN |
| disagreement | optional | where evidence tiers disagree; rendered on the site |
| visibility | yes | `public` or `hidden`; hidden entries are excluded from dist/ |
| notes | optional | |

STALE is computed at build time: `as_of` older than 90 days before the build date.

### Build fails (exit non-zero) when
- MEASURED lacks metric, value, denominator, dataset, synthetic flag, system, date, or an evidence pointer
- KILLED lacks kill_criterion; BLOCKED lacks blocked_by
- LINKED lacks an evidence item with path + branch + SHA and tier 1
- any entry lacks as_of or does_not_show
- unknown state/verification/project/visibility, duplicate or malformed id

## Pages (dist/)
`/` ledger-first home with computed counts · `/not-done/` · `/ledger/` with
JS filter plus pre-rendered no-JS filter pages under `/ledger/<facet>/<value>/` ·
`/projects/<slug>/` for gin, sear, receipts, latch in the fixed section order ·
`/about/` · `/colophon/` · `/ledger.json`.

## Constraints
Python 3 stdlib only. No third-party requests. Every page works without JS.
Deterministic output given the same ledger and build date
(`PORTFOLIO_BUILD_DATE`, default today). Served by `python -m http.server`
bound to 127.0.0.1.
