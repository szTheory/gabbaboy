#!/usr/bin/env python3
"""Run the privacy unittest with a repository-relative traceback filename."""
from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
TEST_FILE = "tests/scripts/test-cgb-red-evidence-privacy.py"
source = (ROOT / TEST_FILE).read_text(encoding="utf-8")
scope = sys.modules["__main__"].__dict__
scope["__file__"] = TEST_FILE
exec(compile(source, TEST_FILE, "exec"), scope)
