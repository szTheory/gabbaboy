#!/usr/bin/env python3
"""Create and validate bounded local scene reports; test subjects are synthetic only."""

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path


class Reject(Exception):
    pass


def intake_smoke(repo_root):
    """Exercise the public CLI with only the three owner-supplied text fields."""
    with tempfile.TemporaryDirectory(prefix="gbb-scene-intake-") as directory:
        root = Path(directory)
        output = root / "build" / "scene-reports"
        output.mkdir(parents=True)
        result = subprocess.run(
            [sys.executable, "-I", str(Path(__file__).resolve()), "--new",
             "--title", "Synthetic title", "--scene", "Synthetic scene",
             "--symptom", "Synthetic symptom", "--output", str(output),
             "--repo-root", str(root)],
            capture_output=True, text=True, timeout=5, check=False)
        if result.returncode != 0:
            raise Reject("scene-report-intake-rejected: minimal title/scene/symptom input was not accepted")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--new", action="store_true")
    modes.add_argument("--self-test", nargs="?", const="all",
                       choices=("all", "intake", "controls", "contract"))
    parser.add_argument("--title")
    parser.add_argument("--scene")
    parser.add_argument("--symptom")
    parser.add_argument("--output")
    parser.add_argument("--repo-root")
    parser.add_argument("--validate")
    parser.add_argument("--promotion-check")
    parser.add_argument("--source-revision")
    args = parser.parse_args(argv)
    try:
        if args.self_test:
            if args.self_test in ("all", "intake"):
                intake_smoke(args.repo_root)
            print(f"scene-report self-test pass mode={args.self_test}")
            return 0
        if args.new:
            raise Reject("scene-report-intake-not-implemented")
        raise Reject("scene-report-mode-required")
    except (Reject, OSError, ValueError) as error:
        reason = str(error)
        print(f"verify-scene-report: {reason}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
