#!/usr/bin/env python3
"""Contract checks for the repository's OpenGSD closeout scan wrapper."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
REVIEW_SOURCE = (
    ROOT
    / ".planning/phases/GB-14-cgb-e-model-qualification-and-corpus/14-UAT-REVIEW.md"
)
DEFAULT_TOOLS = Path.home() / ".codex/gsd-core/bin/gsd-tools.cjs"


def installed_tools() -> Path:
    configured = os.environ.get("GSD_TOOLS")
    return Path(configured).expanduser() if configured else DEFAULT_TOOLS


def make_fixture(root: Path) -> None:
    phase = root / ".planning/phases/GB-14-cgb-e-model-qualification-and-corpus"
    phase.mkdir(parents=True)
    (phase / "14-UAT-REVIEW.md").write_text(REVIEW_SOURCE.read_text(encoding="utf-8"), encoding="utf-8")
    (phase / "14-UAT.md").write_text(
        "---\n"
        "status: pending\n"
        "phase: GB-14-cgb-e-model-qualification-and-corpus\n"
        "---\n\n"
        "## Current Test\n"
        "[testing pending]\n\n"
        "### Incomplete scenario\n"
        "result: pending\n",
        encoding="utf-8",
    )


class CloseoutScanTests(unittest.TestCase):
    def test_clean_review_is_not_reported_as_canonical_uat_debt(self) -> None:
        with tempfile.TemporaryDirectory(prefix="gabbaboy-closeout-red-") as temp_dir:
            fixture = Path(temp_dir)
            make_fixture(fixture)
            command = ["node", str(installed_tools()), "audit-open", "--json"]
            result = subprocess.run(command, cwd=fixture, text=True, capture_output=True, check=False)
            self.assertEqual(result.returncode, 0, f"installed audit-open failed: {result.stderr}")
            payload = json.loads(result.stdout)
            uat_files = [item["file"] for item in payload["items"]["uat_gaps"]]
            self.assertIn("14-UAT.md", uat_files, "the incomplete canonical UAT must remain visible")
            self.assertNotIn(
                "14-UAT-REVIEW.md",
                uat_files,
                "clean review was misclassified as canonical UAT debt; raw audit-open payload="
                + json.dumps(payload, sort_keys=True),
            )


def run_self_test() -> int:
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(CloseoutScanTests)
    result = unittest.TextTestRunner(stream=sys.stdout, verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    if sys.argv[1:] == ["--self-test"]:
        raise SystemExit(run_self_test())
    raise SystemExit("usage: verify-closeout-scan.py --self-test")
