"""Ledger loading and validation. Python 3 stdlib only.

The ledger file is YAML 1.2 written in its JSON-compatible subset, so `json`
parses it. Full-line comments (first non-space char '#') are stripped first;
a raw newline cannot occur inside a JSON string, so this never touches data.
"""
import datetime as _dt
import json
import re

STATES = ["MEASURED", "BUILT", "IN-PROGRESS", "DESIGN-ONLY", "BLOCKED",
          "NOT-DONE", "KILLED", "NEGATIVE-RESULT"]
VERIFICATIONS = ["LINKED", "AUTHOR-REPORTED"]
PROJECTS = ["gin", "sear", "receipts", "latch", "offscreen"]
VISIBILITIES = ["public", "hidden"]
MEASUREMENT_FIELDS = ["metric", "value", "denominator", "dataset", "synthetic",
                      "system", "date"]
ALLOWED_FIELDS = {"id", "project", "claim", "state", "verification", "as_of",
                  "evidence", "does_not_show", "measurements", "results",
                  "reported_result", "kill_criterion", "blocked_by",
                  "disagreement", "visibility", "notes"}
REQUIRED = ["id", "project", "claim", "state", "verification", "as_of",
            "evidence", "does_not_show", "visibility"]
ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SHA_RE = re.compile(r"^[0-9a-f]{7,40}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}(?:-\d{2})?$")
STALE_DAYS = 90


class LedgerError(Exception):
    def __init__(self, errors):
        self.errors = list(errors)
        super().__init__("\n".join(self.errors))


def load_ledger_text(text):
    lines = [ln for ln in text.splitlines() if not ln.lstrip().startswith("#")]
    try:
        data = json.loads("\n".join(lines))
    except json.JSONDecodeError as exc:
        raise LedgerError([f"ledger: not parseable as JSON-subset YAML: {exc}"])
    if not isinstance(data, list):
        raise LedgerError(["ledger: top level must be a list of entries"])
    return data


def load_ledger(path):
    with open(path, encoding="utf-8") as fh:
        return load_ledger_text(fh.read())


def is_unknown(v):
    return isinstance(v, str) and v.strip().upper().startswith("UNKNOWN")


def _blank(v):
    return v is None or (isinstance(v, str) and not v.strip())


def parse_as_of(value):
    """Return a date. Month precision maps to the first day (conservative)."""
    if not isinstance(value, str) or not DATE_RE.match(value):
        raise ValueError(f"bad date {value!r}")
    parts = [int(p) for p in value.split("-")]
    if len(parts) == 2:
        parts.append(1)
    return _dt.date(*parts)


def is_stale(as_of, build_date):
    b = build_date if isinstance(build_date, _dt.date) else parse_as_of(build_date)
    return (b - parse_as_of(as_of)).days > STALE_DAYS


def _evidence_items(ev):
    return ev if isinstance(ev, list) else []


def _linked_item_ok(item):
    if not isinstance(item, dict):
        return False
    path, branch, sha = item.get("path"), item.get("branch"), item.get("sha")
    if any(_blank(x) or is_unknown(x) for x in (path, branch, sha)):
        return False
    if not SHA_RE.match(str(sha)):
        return False
    return item.get("tier") == 1


def validate_entry(e, idx):
    errs = []
    eid = e.get("id", f"<entry {idx}>") if isinstance(e, dict) else f"<entry {idx}>"
    p = f"{eid}:"
    if not isinstance(e, dict):
        return [f"{p} entry must be an object"]
    for k in sorted(set(e) - ALLOWED_FIELDS):
        errs.append(f"{p} unknown field {k!r}")
    for k in REQUIRED:
        if k not in e or _blank(e[k]):
            errs.append(f"{p} missing required field {k}")
    if "id" in e and not (isinstance(e["id"], str) and ID_RE.match(e["id"])):
        errs.append(f"{p} malformed id (want lowercase-kebab)")
    if e.get("state") not in STATES and "state" in e:
        errs.append(f"{p} invalid state {e.get('state')!r} (STALE is computed, never stored)")
    if e.get("verification") not in VERIFICATIONS and "verification" in e:
        errs.append(f"{p} invalid verification {e.get('verification')!r}")
    if e.get("project") not in PROJECTS and "project" in e:
        errs.append(f"{p} invalid project {e.get('project')!r}")
    if e.get("visibility") not in VISIBILITIES and "visibility" in e:
        errs.append(f"{p} invalid visibility {e.get('visibility')!r}")
    if "as_of" in e and not _blank(e["as_of"]):
        try:
            parse_as_of(e["as_of"])
        except (ValueError, TypeError):
            errs.append(f"{p} as_of must be YYYY-MM-DD or YYYY-MM, got {e['as_of']!r}")

    ev = e.get("evidence")
    if ev is not None and not (is_unknown(ev) or isinstance(ev, list)):
        errs.append(f"{p} evidence must be 'UNKNOWN' or a list of items")
    for item in _evidence_items(ev):
        if not isinstance(item, dict) or _blank(item.get("path")) or _blank(item.get("repo")):
            errs.append(f"{p} each evidence item needs repo and path")

    state = e.get("state")
    if state == "MEASURED":
        ms = e.get("measurements")
        if not isinstance(ms, list) or not ms:
            errs.append(f"{p} MEASURED requires a non-empty measurements list")
        else:
            for i, m in enumerate(ms):
                for f in MEASUREMENT_FIELDS:
                    if not isinstance(m, dict) or f not in m or _blank(m[f]) or is_unknown(m[f]):
                        errs.append(f"{p} MEASURED measurement[{i}] lacks {f}")
        if is_unknown(ev) or not _evidence_items(ev):
            errs.append(f"{p} MEASURED requires an evidence pointer")
    if state == "KILLED":
        kc = e.get("kill_criterion")
        if _blank(kc) or is_unknown(kc):
            errs.append(f"{p} KILLED requires kill_criterion")
    if state == "BLOCKED":
        bb = e.get("blocked_by")
        if _blank(bb) or is_unknown(bb):
            errs.append(f"{p} BLOCKED requires blocked_by")
    if e.get("verification") == "LINKED":
        if not any(_linked_item_ok(it) for it in _evidence_items(ev)):
            errs.append(f"{p} LINKED requires a tier-1 evidence item with path + branch + SHA")
    for key in ("measurements", "results"):
        if key in e and not isinstance(e[key], list):
            errs.append(f"{p} {key} must be a list")
    return errs


def validate_entries(entries):
    errs = []
    seen = set()
    for i, e in enumerate(entries):
        entry_errs = validate_entry(e, i)
        if isinstance(e, dict) and isinstance(e.get("id"), str):
            if e["id"] in seen:
                entry_errs.append(f"{e['id']}: duplicate id")
            seen.add(e["id"])
        if entry_errs:
            errs.append("; ".join(entry_errs))
    if errs:
        raise LedgerError(errs)
    return entries
