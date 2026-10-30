from __future__ import annotations

import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
PATH = ROOT / "tests/scripts/verify-changelog-heading.py"
SPEC = importlib.util.spec_from_file_location("verify_changelog_heading", PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC is not None and SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class ChangelogHeadingContract(unittest.TestCase):
    def test_unreleased_first_heading_is_rejected(self) -> None:
        text = "## Unreleased\n\n## [0.3.0](https://example.invalid)\n"
        with self.assertRaises(MODULE.Reject) as raised:
            MODULE.check_heading(text)
        self.assertEqual(raised.exception.code, "changelog-first-heading-not-version")


if __name__ == "__main__":
    unittest.main()
