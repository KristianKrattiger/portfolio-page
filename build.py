#!/usr/bin/env python3
"""Build the portfolio into dist/. Python 3 stdlib only.

Usage: python build.py [--out dist] [--date YYYY-MM-DD]
The build date (for STALE) comes from --date, else PORTFOLIO_BUILD_DATE, else today.
Exit code 1 on any ledger validation failure; nothing is written in that case.
"""
import argparse
import datetime as dt
import json
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from portfolio.validate import LedgerError, load_ledger, validate_entries  # noqa: E402
from portfolio import render  # noqa: E402


def load_json(path, default=None):
    if not os.path.exists(path):
        return default
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(ROOT, "dist"))
    ap.add_argument("--date", default=os.environ.get("PORTFOLIO_BUILD_DATE"))
    ap.add_argument("--ledger", default=os.path.join(ROOT, "content", "ledger.yaml"))
    args = ap.parse_args(argv)
    build_date = dt.date.fromisoformat(args.date) if args.date else dt.date.today()

    try:
        entries = validate_entries(load_ledger(args.ledger))
    except LedgerError as exc:
        print("LEDGER VALIDATION FAILED — build aborted, nothing written:", file=sys.stderr)
        for err in exc.errors:
            print("  - " + err, file=sys.stderr)
        return 1

    site = load_json(os.path.join(ROOT, "content", "site.json"))

    pages = render.build_site(entries, site, build_date)

    out = os.path.abspath(args.out)
    if os.path.isdir(out):
        shutil.rmtree(out)
    for rel_path, content in sorted(pages.items()):
        full = os.path.join(out, *rel_path.split("/"))
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(content)
    # Static assets (bundled font + its licence), copied byte for byte.
    fonts_src = os.path.join(ROOT, "assets", "fonts")
    if os.path.isdir(fonts_src):
        fonts_out = os.path.join(out, "fonts")
        os.makedirs(fonts_out, exist_ok=True)
        for name in sorted(os.listdir(fonts_src)):
            shutil.copyfile(os.path.join(fonts_src, name), os.path.join(fonts_out, name))
    print(f"built {len(pages)} files into {out} (build date {build_date.isoformat()})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
