"""Tests for the ledger validator. Written before portfolio/validate.py.

Run: python -m unittest discover -s tests -v
"""
import copy
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from portfolio.validate import (  # noqa: E402
    LedgerError,
    is_stale,
    load_ledger_text,
    validate_entries,
)

LINKED_EVIDENCE = [
    {"repo": "GIN", "path": "README.md", "branch": "main", "sha": "84abb9a",
     "tier": 1, "dirty": False}
]

MEASUREMENT = {
    "metric": "fabrication rate", "value": "0.000", "denominator": "0/21 claims",
    "dataset": "synthetic news corpus", "synthetic": True,
    "system": "SEAR NC arm, Mistral-7B", "date": "2026-07-02",
}


def base(**over):
    e = {
        "id": "x-1", "project": "gin", "claim": "A claim.", "state": "BUILT",
        "verification": "AUTHOR-REPORTED", "as_of": "2026-10-01",
        "evidence": "UNKNOWN", "does_not_show": "Nothing beyond the claim.",
        "visibility": "public",
    }
    e.update(over)
    return e


def errors_for(entries):
    try:
        validate_entries(entries)
    except LedgerError as exc:
        return exc.errors
    return []


class PassingCases(unittest.TestCase):
    def test_minimal_entry_passes(self):
        self.assertEqual(errors_for([base()]), [])

    def test_unknown_does_not_show_allowed(self):
        self.assertEqual(errors_for([base(does_not_show="UNKNOWN — author to supply")]), [])

    def test_measured_complete_passes(self):
        e = base(state="MEASURED", verification="LINKED", evidence=LINKED_EVIDENCE,
                 measurements=[MEASUREMENT])
        self.assertEqual(errors_for([e]), [])

    def test_killed_with_criterion_passes(self):
        self.assertEqual(errors_for([base(state="KILLED", kill_criterion="Arm 2 loses to Arm 0")]), [])

    def test_blocked_with_blocker_passes(self):
        self.assertEqual(errors_for([base(state="BLOCKED", blocked_by="labeled data")]), [])

    def test_month_precision_as_of_passes(self):
        self.assertEqual(errors_for([base(as_of="2026-08")]), [])

    def test_vault_evidence_without_sha_ok_for_author_reported(self):
        ev = [{"repo": "vault", "path": "CALICHE/x.md", "branch": "n/a", "sha": "n/a", "tier": 3}]
        self.assertEqual(errors_for([base(evidence=ev)]), [])


class MustFailCases(unittest.TestCase):
    def assertFails(self, entries, needle):
        errs = errors_for(entries)
        self.assertTrue(errs, "expected validation to fail")
        self.assertTrue(any(needle in m for m in errs), f"{needle!r} not in {errs}")

    # MEASURED completeness
    def test_measured_without_measurements(self):
        self.assertFails([base(state="MEASURED", evidence=LINKED_EVIDENCE)], "measurements")

    def test_measured_missing_each_field(self):
        for field in ["metric", "value", "denominator", "dataset", "synthetic", "system", "date"]:
            m = copy.deepcopy(MEASUREMENT)
            del m[field]
            with self.subTest(field=field):
                self.assertFails([base(state="MEASURED", evidence=LINKED_EVIDENCE,
                                       measurements=[m])], field)

    def test_measured_unknown_field(self):
        for field in ["value", "denominator", "dataset", "system", "date", "synthetic"]:
            m = copy.deepcopy(MEASUREMENT)
            m[field] = "UNKNOWN"
            with self.subTest(field=field):
                self.assertFails([base(state="MEASURED", evidence=LINKED_EVIDENCE,
                                       measurements=[m])], field)

    def test_measured_without_evidence_pointer(self):
        self.assertFails([base(state="MEASURED", measurements=[MEASUREMENT])], "evidence")

    # KILLED / BLOCKED
    def test_killed_without_criterion(self):
        self.assertFails([base(state="KILLED")], "kill_criterion")

    def test_killed_with_unknown_criterion(self):
        self.assertFails([base(state="KILLED", kill_criterion="UNKNOWN")], "kill_criterion")

    def test_blocked_without_blocker(self):
        self.assertFails([base(state="BLOCKED")], "blocked_by")

    def test_blocked_with_empty_blocker(self):
        self.assertFails([base(state="BLOCKED", blocked_by="  ")], "blocked_by")

    # LINKED
    def test_linked_with_unknown_evidence(self):
        self.assertFails([base(verification="LINKED")], "LINKED")

    def test_linked_without_sha(self):
        ev = [dict(LINKED_EVIDENCE[0], sha="")]
        self.assertFails([base(verification="LINKED", evidence=ev)], "LINKED")

    def test_linked_without_branch(self):
        ev = [{k: v for k, v in LINKED_EVIDENCE[0].items() if k != "branch"}]
        self.assertFails([base(verification="LINKED", evidence=ev)], "LINKED")

    def test_linked_without_path(self):
        ev = [dict(LINKED_EVIDENCE[0], path="UNKNOWN")]
        self.assertFails([base(verification="LINKED", evidence=ev)], "LINKED")

    def test_linked_with_only_tier2(self):
        ev = [dict(LINKED_EVIDENCE[0], tier=2)]
        self.assertFails([base(verification="LINKED", evidence=ev)], "LINKED")

    def test_linked_with_bad_sha(self):
        ev = [dict(LINKED_EVIDENCE[0], sha="n/a")]
        self.assertFails([base(verification="LINKED", evidence=ev)], "LINKED")

    # required fields
    def test_missing_as_of(self):
        e = base()
        del e["as_of"]
        self.assertFails([e], "as_of")

    def test_bad_as_of(self):
        self.assertFails([base(as_of="Aug 2026")], "as_of")

    def test_missing_does_not_show(self):
        e = base()
        del e["does_not_show"]
        self.assertFails([e], "does_not_show")

    def test_empty_does_not_show(self):
        self.assertFails([base(does_not_show="")], "does_not_show")

    def test_missing_claim(self):
        e = base()
        del e["claim"]
        self.assertFails([e], "claim")

    # enums and ids
    def test_bad_state(self):
        self.assertFails([base(state="DONE")], "state")

    def test_stale_is_not_storable(self):
        self.assertFails([base(state="STALE")], "state")

    def test_bad_verification(self):
        self.assertFails([base(verification="VERIFIED")], "verification")

    def test_bad_visibility(self):
        self.assertFails([base(visibility="private")], "visibility")

    def test_bad_project(self):
        self.assertFails([base(project="other")], "project")

    def test_duplicate_id(self):
        self.assertFails([base(), base()], "duplicate")

    def test_malformed_id(self):
        self.assertFails([base(id="Bad Id")], "id")

    def test_unknown_field_rejected(self):
        self.assertFails([base(colour="red")], "unknown field")

    def test_all_errors_reported_together(self):
        errs = errors_for([base(state="KILLED"), base(id="y", state="BLOCKED")])
        self.assertEqual(len(errs), 2)


class Parsing(unittest.TestCase):
    def test_comment_lines_stripped(self):
        text = "# a comment\n  # indented comment\n[{\"a\": \"# not a comment\"}]\n"
        self.assertEqual(load_ledger_text(text), [{"a": "# not a comment"}])

    def test_top_level_must_be_list(self):
        with self.assertRaises(LedgerError):
            load_ledger_text("{}")

    def test_invalid_json_raises_ledger_error(self):
        with self.assertRaises(LedgerError):
            load_ledger_text("[{,}]")


class Staleness(unittest.TestCase):
    def test_stale_after_90_days(self):
        self.assertTrue(is_stale("2026-08-01", "2026-11-20"))

    def test_not_stale_within_90_days(self):
        self.assertFalse(is_stale("2026-09-01", "2026-11-20"))

    def test_boundary_exactly_90_days_not_stale(self):
        self.assertFalse(is_stale("2026-08-22", "2026-11-20"))

    def test_month_precision_uses_first_day(self):
        # 2026-08 is treated as 2026-08-01 (conservative: flags more, not fewer)
        self.assertTrue(is_stale("2026-08", "2026-11-20"))


if __name__ == "__main__":
    unittest.main()
