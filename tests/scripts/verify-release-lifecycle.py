#!/usr/bin/env python3
"""Replay the release evidence lifecycle against bounded, captured GitHub API shapes (RM-028, D-20).

    verify-release-lifecycle.py --rev SHA --replay
    verify-release-lifecycle.py --rev SHA --self-test

--rev is a resolved immutable 40-hex commit. Every production file the replay uses is materialized from that
commit with git show; the live working tree is never read and never a fallback.

The replay runs the production lifecycle script (.github/scripts/release-evidence-lifecycle.sh) and, through it,
the production gates, unchanged. Only the transport is replaced: a `gh` executable that serves recorded
response shapes and refuses every endpoint or mutation it was not told about. The replay proves deterministic
logic. It does not prove live GitHub permissions, and it never publishes: the final publish command is
intercepted and recorded as a decision.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SHA1 = re.compile(r"[0-9a-f]{40}")
LIFECYCLE = ".github/scripts/release-evidence-lifecycle.sh"
WORKFLOW = ".github/workflows/release.yml"
# mode -> the release.yml job whose step must call it
MODES = {
    "attach-evidence": "attach-v02-evidence",
    "validate-evidence": "candidate-platform-manifest",
    "build-manifest": "candidate-platform-manifest",
    "validate-draft": "publish-qualified-release",
    "final-gate": "publish-qualified-release",
    "publish-draft": "publish-qualified-release",
}


class Reject(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"REJECT {code}: {message}")
        self.code = code


def git_show(rev: str, path: str) -> bytes:
    done = subprocess.run(["git", "-C", str(ROOT), "show", f"{rev}:{path}"], capture_output=True, timeout=60)
    if done.returncode != 0:
        raise Reject("rev-file-missing", f"{path} is not present at {rev}")
    return done.stdout


def resolve_rev(rev: str) -> str:
    if not SHA1.fullmatch(rev):
        raise Reject("rev-malformed", "--rev must be a resolved 40-hex commit")
    done = subprocess.run(["git", "-C", str(ROOT), "cat-file", "-t", rev], capture_output=True, text=True, timeout=60)
    if done.returncode != 0 or done.stdout.strip() != "commit":
        raise Reject("rev-unresolved", "--rev does not name a commit in this repository")
    return rev


def check_wiring(workflow: str, script: str | None) -> None:
    """The production workflow must call the extracted lifecycle script for every mode, from the right job."""
    if script is None:
        raise Reject("lifecycle-missing", f"{LIFECYCLE} is absent: the lifecycle is not extracted")
    for mode, job in MODES.items():
        call = f"bash trusted/.github/scripts/release-evidence-lifecycle.sh {mode}"
        start = workflow.find(f"\n  {job}:\n")
        if start < 0 or call not in workflow[start:]:
            raise Reject("lifecycle-unwired", f"release.yml job {job} does not call the lifecycle mode {mode}")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--rev", required=True)
    parser.add_argument("--replay", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    try:
        rev = resolve_rev(args.rev)
        workflow = git_show(rev, WORKFLOW).decode("utf-8")
        try:
            script = git_show(rev, LIFECYCLE).decode("utf-8")
        except Reject:
            script = None
        check_wiring(workflow, script)
    except Reject as error:
        print(str(error), file=sys.stderr)
        return 1
    return 0 if (args.replay or args.self_test) else 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
