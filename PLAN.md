# PLAN.md

1. Walk the context read-only; log every file in SOURCES.md. (done before code)
2. STYLE.md, SPEC.md, this plan, ASSUMPTIONS.md.
3. Tests first: `tests/test_validate.py` covers every must-fail case and a
   passing minimal ledger. Run them red (no validator yet).
4. `portfolio/validate.py` until tests are green.
5. `content/ledger.yaml` from the walk (seed entries reconciled; new entries
   cite paths). `content/site.json` for name/line/contact (contact UNKNOWN).
6. `build.py`: validate → render pages → dist/. Deterministic (sorted keys,
   fixed build date, no timestamps besides the build date).
7. `verify/verify.py`: determinism (two builds, hash compare), LINKED-at-SHA
   check via `git cat-file`, external-host / secret / IP / tailnet scan,
   internal link check, WCAG contrast for every palette pair in both schemes,
   banned-phrase scan, no-JS sanity (content present in HTML without script),
   keyboard basics (skip link, focus styles, no positive tabindex).
8. `run.sh` + Windows user-level persistence (Startup-folder launcher; no admin).
9. Whole-branch review of my own work; fix findings.
10. Live check: start service, curl every route, record output in the colophon.
11. Final report in the site's vocabulary.
