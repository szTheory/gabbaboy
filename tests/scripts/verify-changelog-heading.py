#!/usr/bin/env python3
"""Require the first CHANGELOG H2 to name a linked release version."""
from __future__ import annotations

import argparse
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
MAX_BYTES = 8 * 1024 * 1024
REVISION = re.compile(r"[0-9a-f]{40}\Z")
VERSION_HEADING = re.compile(r"^## \[(\d+\.\d+\.\d+)\]\(([^)]+)\)(?:\s+.*)?$")

if not __debug__:
    raise SystemExit("verify-changelog-heading refuses to run under python -O (its checks must stay on)")


class Reject(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


def check_heading(text: str) -> str:
    for line in text.splitlines():
        if line.startswith("## "):
            if VERSION_HEADING.fullmatch(line) is None:
                raise Reject("changelog-first-heading-not-version", f"first H2 is not a linked version heading: {line}")
            return line[3:]
    raise Reject("changelog-first-heading-not-version", "CHANGELOG.md has no H2 release heading")


def read_at(repo: Path, rev: str, path: str) -> str:
    done = subprocess.run(["git", "-C", str(repo), "show", f"{rev}:{path}"], capture_output=True, check=False)
    if done.returncode != 0:
        raise Reject("changelog-missing", f"{path} is not present at {rev}")
    if len(done.stdout) > MAX_BYTES:
        raise Reject("changelog-too-large", f"{path} exceeds {MAX_BYTES} bytes")
    try:
        return done.stdout.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise Reject("changelog-invalid-utf8", f"{path} is not UTF-8: {error}") from error


def verify_revision(repo: Path, rev: str) -> None:
    if REVISION.fullmatch(rev) is None:
        raise Reject("revision-invalid", "--rev must be a full 40-character commit id")
    done = subprocess.run(["git", "-C", str(repo), "cat-file", "-e", f"{rev}^{{commit}}"],
                          capture_output=True, check=False)
    if done.returncode != 0:
        raise Reject("revision-invalid", f"{rev} is not an available commit")


def self_test() -> int:
    try:
        check_heading("# Changelog\n\n## Unreleased\n\n## [0.3.0](https://example.invalid)\n")
    except Reject as error:
        if error.code != "changelog-first-heading-not-version":
            raise Reject("control-wrong-reason", error.message) from error
    else:
        raise Reject("control-accepted", "the seeded Unreleased-first changelog was accepted")
    try:
        accepted = check_heading("# Changelog\n\n## [0.3.0](https://example.invalid) (2026-10-29)\n")
    except Reject as error:
        raise Reject("control-rejected", f"the linked version-first twin was rejected: {error.message}") from error
    if accepted != "[0.3.0](https://example.invalid) (2026-10-29)":
        raise Reject("control-wrong-result", "the version-first twin returned a different first heading")
    return 2


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rev", required=True, help="the commit to read the changelog from")
    parser.add_argument("--repo", type=Path, default=ROOT, help="the repository root")
    parser.add_argument("--self-test", action="store_true", help="run seeded rejecting and accepting controls")
    args = parser.parse_args()
    try:
        verify_revision(args.repo, args.rev)
        first = check_heading(read_at(args.repo, args.rev, "CHANGELOG.md"))
        controls = self_test() if args.self_test else 0
    except Reject as error:
        print(f"REJECT {error.code}: {error.message}", file=sys.stderr)
        return 1
    print(f"changelog-heading pass first={first} controls={controls}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
