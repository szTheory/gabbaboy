#!/usr/bin/env python3
"""Check README.md and docs/*.md links at an immutable revision."""
from __future__ import annotations

import argparse
import json
from pathlib import Path, PurePosixPath
import posixpath
import re
import subprocess
import sys
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[2]
MAX_FILE = 8 * 1024 * 1024
MAX_LISTING = 2 * 1024 * 1024
REVISION = re.compile(r"[0-9a-f]{40}\Z")
PROJECT_VERSION = re.compile(r"^project\(\s*\w+\s+VERSION\s+(\d+)\.(\d+)\.(\d+)[\s)]", re.M)
LEDGER = re.compile(r"v(\d+)\.(\d+)\.(\d+)\.md\Z")
LINK = re.compile(r"!?\[([^\]]*)\]\(\s*(?:<([^>]+)>|([^\s)]+))(?:\s+[^)]*)?\)")
REFERENCE = re.compile(r"(?m)^\s*\[[^\]]+\]:\s*(?:<([^>]+)>|(\S+))")
PREFIX = re.compile(r"\bgabbaboy-v(\d+\.\d+\.\d+)\b", re.IGNORECASE)
HISTORICAL = re.compile(
    r"\b(?:earlier|previous|historical|remains? the record|that release|unchanged|fixes-only|records both versions)\b",
    re.IGNORECASE)
if not __debug__:
    raise SystemExit("verify-doc-links refuses to run under python -O (checks must stay on)")


class Reject(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code, self.message = code, message


def git(repo: Path, args: list[str], limit: int) -> bytes:
    result = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, check=False)
    if result.returncode:
        raise Reject("revision-invalid", f"git {' '.join(args[:2])} failed")
    if len(result.stdout) > limit:
        raise Reject("tree-too-large", f"git output exceeds {limit} bytes")
    return result.stdout


def read_at(repo: Path, rev: str, path: str) -> str:
    try:
        return git(repo, ["show", f"{rev}:{path}"], MAX_FILE).decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise Reject("doc-invalid-utf8", f"{path} is not UTF-8: {error}") from error


def tree(repo: Path, rev: str) -> tuple[str, str, set[str], list[str]]:
    if REVISION.fullmatch(rev) is None:
        raise Reject("revision-invalid", "--rev must be a full 40-character commit id")
    git(repo, ["cat-file", "-e", f"{rev}^{{commit}}"], MAX_LISTING)
    cmake = read_at(repo, rev, "CMakeLists.txt")
    manifest_text = read_at(repo, rev, ".release-please-manifest.json")
    match = PROJECT_VERSION.search(cmake)
    if match is None:
        raise Reject("version-missing", "CMakeLists.txt has no project VERSION")
    version = ".".join(match.groups())
    try:
        manifest = json.loads(manifest_text)
    except json.JSONDecodeError as error:
        raise Reject("version-missing", f"manifest JSON is invalid: {error}") from error
    if not isinstance(manifest, dict) or manifest.get(".") != version:
        raise Reject("version-mismatch", f"release manifest does not match {version}")
    numbers = tuple(int(part) for part in match.groups())
    raw = git(repo, ["ls-tree", "-r", "--name-only", "-z", rev], MAX_LISTING)
    paths = [part.decode("utf-8", errors="strict") for part in raw.split(b"\0") if part]
    if "README.md" not in paths:
        raise Reject("file-missing", "README.md is absent at the requested revision")
    files = ["README.md"] + [p for p in paths if p.startswith("docs/") and "/" not in p[5:] and p.endswith(".md")]
    raw = git(repo, ["ls-tree", "-r", "--name-only", "-z", rev, "--", "docs/support"], MAX_LISTING)
    candidates = []
    for part in raw.split(b"\0"):
        if not part:
            continue
        path = part.decode("utf-8", errors="strict")
        found = LEDGER.fullmatch(PurePosixPath(path).name)
        if found:
            ver = tuple(int(value) for value in found.groups())
            if ver[:2] == numbers[:2] and ver <= numbers:
                candidates.append((ver, path))
    if not candidates:
        raise Reject("support-ledger-missing", f"no ledger is current for v{version}")
    existing = set(paths)
    for path in paths:
        parent = PurePosixPath(path).parent
        while str(parent) != ".":
            existing.add(str(parent))
            parent = parent.parent
    return version, max(candidates)[1], existing, files


def target_path(source: str, target: str) -> str | None:
    parsed = urlsplit(target.strip())
    if parsed.scheme or parsed.netloc or not parsed.path:
        return None
    path = unquote(parsed.path)
    resolved = posixpath.normpath(path.lstrip("/") if path.startswith("/")
                                  else posixpath.join(posixpath.dirname(source), path))
    if resolved in ("", "."):
        return None
    if resolved == ".." or resolved.startswith("../"):
        raise Reject("doc-link-missing", f"{source} links outside the repository: {target}")
    return resolved


def check_documents(files: dict[str, str], version: str, ledger: str, existing: set[str]) -> int:
    count = 0
    for source, text in files.items():
        found = PREFIX.search(text)
        if found and found.group(1) != version:
            raise Reject("doc-prefix-stale", f"{source} names gabbaboy-v{found.group(1)}; tree is v{version}")
        targets = [(m.group(1), m.group(2) or m.group(3), m.start(), m.end()) for m in LINK.finditer(text)]
        targets += [("", m.group(1) or m.group(2), m.start(), m.end()) for m in REFERENCE.finditer(text)]
        for label, target, start, end in targets:
            resolved = target_path(source, target)
            if resolved is None:
                continue
            count += 1
            if resolved not in existing:
                raise Reject("doc-link-missing", f"{source} links to absent path {resolved}")
            if resolved.startswith("docs/support/") and LEDGER.fullmatch(PurePosixPath(resolved).name):
                if resolved != ledger:
                    context = text[max(0, start - 140):min(len(text), end + 140)]
                    if not HISTORICAL.search(context):
                        raise Reject("doc-link-stale-ledger", f"{source} links to {resolved}; current is {ledger}")
    return count


def self_test() -> int:
    existing = {"README.md", "docs", "docs/guide.md", "docs/support", "docs/support/v0.1.0.md",
                "docs/support/v0.2.1.md"}
    current = "docs/support/v0.2.1.md"
    base = {"README.md": "[ledger](docs/support/v0.2.1.md) [guide](docs/guide.md)\n",
            "docs/guide.md": "[ledger](support/v0.2.1.md)\n"}
    if check_documents(base, "0.2.1", current, existing) != 3:
        raise Reject("control-wrong-result", "current-ledger positive twin failed")
    controls = 1

    def reject(label: str, files: dict[str, str], expected: str) -> None:
        try:
            check_documents(files, "0.2.1", current, existing)
        except Reject as error:
            if error.code != expected:
                raise Reject("control-wrong-reason", f"{label} returned {error.code}") from error
        else:
            raise Reject("control-accepted", f"{label} was accepted")

    reject("stale support ledger", {"README.md": "[ledger](docs/support/v0.1.0.md)\n"},
           "doc-link-stale-ledger")
    controls += 1
    if check_documents({"README.md": "[guide](docs/guide.md)\n"}, "0.2.1", current, existing) != 1:
        raise Reject("control-wrong-result", "existing-target positive twin failed")
    controls += 1
    reject("missing target", {"README.md": "[missing](docs/missing.md)\n"}, "doc-link-missing")
    controls += 1
    if check_documents({"README.md": "gabbaboy-v0.2.1\n"}, "0.2.1", current, existing) != 0:
        raise Reject("control-wrong-result", "matching-prefix positive twin failed")
    controls += 1
    reject("stale version prefix", {"README.md": "gabbaboy-v0.1.0\n"}, "doc-prefix-stale")
    return controls + 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rev", required=True, help="full commit id to read")
    parser.add_argument("--repo", type=Path, default=ROOT, help="repository root")
    parser.add_argument("--self-test", action="store_true", help="run seeded positive and negative controls")
    args = parser.parse_args()
    try:
        version, ledger, existing, paths = tree(args.repo, args.rev)
        files = {path: read_at(args.repo, args.rev, path) for path in paths}
        links = check_documents(files, version, ledger, existing)
        controls = self_test() if args.self_test else 0
    except Reject as error:
        print(f"REJECT {error.code}: {error.message}", file=sys.stderr)
        return 1
    print(f"doc-links pass files={len(files)} links={links} controls={controls}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
