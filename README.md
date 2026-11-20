# portfolio

Ledger-first personal site. Source of truth: `content/ledger.yaml` (schema in SPEC.md).

    python -m unittest discover -s tests     # validator tests
    python build.py                          # validate + build dist/ (fails on bad ledger)
    python verify/verify.py --live http://127.0.0.1:8787   # all checks; writes content/site_checks.json
    ./run.sh                                 # build + serve on 127.0.0.1:8787 (foreground)
    powershell -File service/install-service.ps1     # persistent, user-level (Startup folder)
    powershell -File service/uninstall-service.ps1

After editing the ledger: run verify, then build again so the colophon carries the results.
Docs: STYLE.md, SPEC.md, PLAN.md, ASSUMPTIONS.md, SOURCES.md, NEEDS_AUTHOR.md.
