#!/usr/bin/env python3
"""Classify a change as planning-only or full (D-21, TUNE-04).

kind=planning means every changed path sits under .planning/ or is exactly AGENTS.md, so the heavy native,
sanitizer, performance and package jobs may be skipped. Everything else, and anything this script cannot judge
with certainty, is kind=full: the safe answer is always to run the whole matrix.

    classify-changes.py --base SHA --head SHA --ref REF   judge `git diff --raw --no-renames -z BASE HEAD`
    classify-changes.py --from-raw FILE [FILE ...]        judge recorded raw diffs (fixtures), one line per file
    classify-changes.py --self-test                       run every control

The workflow runs the copy of this file stored at the base commit (`git show BASE:.github/scripts/...`), so a
change cannot loosen the rule that judges it. Prints exactly one line: `kind=planning` or `kind=full reason=CODE`.
"""

from __future__ import annotations

import argparse
import itertools
import os
import random
import re
import subprocess
import sys
import tempfile
from pathlib import Path

MAX_FILES = 300
PLANNING_ROOT = ".planning"
PLANNING_FILE = "AGENTS.md"
# git's all-zero object name stands for "no commit": a new branch or tag push has no parent to diff against.
_ZERO = re.compile(r"^0+$")
_META = re.compile(r"^:(\d{6}) (\d{6}) ([0-9a-f]{4,64}) ([0-9a-f]{4,64}) ([A-Z])(\d*)$")
# Entry modes that are never plain files: a symlink or a submodule can point anywhere.
_LINK_MODES = {"120000", "160000"}


class Full(Exception):
    """The change is not provably planning-only; `code` is the reason printed after kind=full."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


def parse_raw(data: bytes) -> list[tuple[str, str]]:
    """Split a `git diff --raw -z` stream into (meta, path) pairs.

    Fixtures store the stream with newlines in place of NUL bytes so they stay ordinary LF text files; a path
    that holds a newline cannot be written that way, and the live stream is always NUL-separated.
    """
    if b"\0" in data:
        fields = data.split(b"\0")
        if fields and fields[-1] == b"":
            fields.pop()
    else:
        fields = data.split(b"\n")
        while fields and fields[-1] == b"":
            fields.pop()
    if len(fields) % 2:
        raise Full("malformed-diff")
    try:
        decoded = [field.decode("utf-8") for field in fields]
    except UnicodeDecodeError:
        raise Full("non-utf8-path") from None
    return [(decoded[i], decoded[i + 1]) for i in range(0, len(decoded), 2)]


def _allowed(path: str) -> bool:
    if not path or path.startswith("/") or "\\" in path or any(ord(char) < 0x20 or ord(char) == 0x7F for char in path):
        return False
    segments = path.split("/")
    if any(segment in ("", ".", "..") for segment in segments):
        return False
    # Case-sensitive on purpose: .Planning/ or agents.md are different paths on Linux and the same path on a
    # case-folding checkout, which is exactly the ambiguity that must not skip the heavy jobs.
    if path == PLANNING_FILE:
        return True
    return segments[0] == PLANNING_ROOT and len(segments) > 1


def classify_pairs(pairs: list[tuple[str, str]]) -> None:
    """Raise Full unless every pair is a planning-only change."""
    if not pairs:
        raise Full("empty-diff")
    if len(pairs) > MAX_FILES:
        raise Full("too-many-files")
    for meta, path in pairs:
        match = _META.match(meta)
        if not match:
            raise Full("malformed-diff")
        old_mode, new_mode, status = match.group(1), match.group(2), match.group(5)
        if status not in "AMDT":
            # With --no-renames a rename or copy never appears; one that does came from a different command.
            raise Full("unexpected-status")
        if old_mode in _LINK_MODES or new_mode in _LINK_MODES:
            raise Full("symlink-or-submodule")
        if not _allowed(path):
            raise Full("path-outside-planning")


def classify_raw(data: bytes) -> str:
    try:
        classify_pairs(parse_raw(data))
    except Full as exc:
        return f"kind=full reason={exc.code}"
    return "kind=planning"


def _git(*args: str, cwd: str | None = None) -> subprocess.CompletedProcess[bytes]:
    env = dict(os.environ)
    env["GIT_OPTIONAL_LOCKS"] = "0"
    return subprocess.run(["git", *args], capture_output=True, check=False, cwd=cwd, env=env, timeout=120)


def classify_range(base: str, head: str, ref: str, cwd: str | None = None) -> str:
    if ref.startswith("refs/tags/") or ref.startswith("tags/"):
        return "kind=full reason=tag-ref"
    if not base or _ZERO.match(base):
        return "kind=full reason=no-base"
    for name, value in (("base", base), ("head", head)):
        if not re.fullmatch(r"[0-9a-fA-F]{7,64}", value or ""):
            return f"kind=full reason=bad-{name}"
        if _git("cat-file", "-e", f"{value}^{{commit}}", cwd=cwd).returncode != 0:
            return f"kind=full reason=unresolvable-{name}"
    result = _git("diff", "--raw", "--no-renames", "--no-ext-diff", "--no-textconv", "--ignore-submodules=none",
                  "--no-abbrev", "-z", base, head, "--", cwd=cwd)
    if result.returncode != 0:
        return "kind=full reason=diff-failed"
    return classify_raw(result.stdout)


# --------------------------------------------------------------------------- self-test
def _raw(*entries: tuple[str, str, str, str], nul: bool = True) -> bytes:
    """(old mode, new mode, status, path) -> a raw diff stream."""
    fields: list[str] = []
    for old_mode, new_mode, status, path in entries:
        fields.append(f":{old_mode} {new_mode} {'0' * 40} {'1' * 40} {status}")
        fields.append(path)
    return ("\0".join(fields) + "\0" if nul else "\n".join(fields) + "\n").encode("utf-8")


def _edit(path: str, status: str = "M", old_mode: str = "100644", new_mode: str = "100644") -> tuple[str, str, str, str]:
    return (old_mode, new_mode, status, path)


def _repo_controls(controls: list[str]) -> None:
    """Drive the real `git diff` path in a throwaway repository: renames, links and unusable bases."""
    git_env = ["-c", "user.name=classify", "-c", "user.email=classify@example.invalid", "-c", "commit.gpgsign=false",
               "-c", "core.autocrlf=false"]

    with tempfile.TemporaryDirectory(prefix="gbb-classify.") as directory:
        def git(*args: str) -> str:
            result = subprocess.run(["git", *git_env, *args], capture_output=True, text=True, check=False, cwd=directory, timeout=60)
            if result.returncode != 0:
                raise SystemExit(f"classify-changes self-test: git {' '.join(args)} failed: {result.stderr.strip()}")
            return result.stdout.strip()

        def write(path: str, text: str) -> None:
            target = Path(directory) / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding="utf-8")

        def commit(message: str) -> str:
            git("add", "-A")
            git("commit", "-q", "--allow-empty", "-m", message)
            return git("rev-parse", "HEAD")

        git("init", "-q")
        write("src/a.c", "int a;\n")
        write("tests/t.txt", "t\n")
        write(".planning/x.md", "x\n")
        write("AGENTS.md", "a\n")
        base = commit("base")

        def verdict(label: str, expected: str, head: str, ref: str = "refs/heads/work", the_base: str | None = None) -> None:
            actual = classify_range(base if the_base is None else the_base, head, ref, cwd=directory)
            if actual != expected:
                raise SystemExit(f"classify-changes self-test: {label}: want {expected!r}, got {actual!r}")
            controls.append(label)

        write(".planning/x.md", "changed\n")
        write("AGENTS.md", "changed\n")
        planning = commit("planning only")
        verdict("repo: planning-only change", "kind=planning", planning)
        verdict("repo: a tag ref is never planning", "kind=full reason=tag-ref", planning, ref="refs/tags/v9")
        verdict("repo: an all-zero base is never planning", "kind=full reason=no-base", planning, the_base="0" * 40)
        verdict("repo: an unresolvable base is never planning", "kind=full reason=unresolvable-base", planning, the_base="1" * 40)
        verdict("repo: an empty diff is never planning", "kind=full reason=empty-diff", planning, the_base=planning)
        git("mv", "src/a.c", ".planning/a.c")
        renamed = commit("rename out of src")
        verdict("repo: a rename out of src/ is a delete under src/", "kind=full reason=path-outside-planning", renamed)
        link_blob = subprocess.run(["git", "hash-object", "-w", "--stdin"], input="../src/a.c", capture_output=True, text=True,
                                   check=True, cwd=directory, timeout=60).stdout.strip()
        git("update-index", "--add", "--cacheinfo", f"120000,{link_blob},.planning/link")
        # `git add -A` would drop an index-only entry, so commit the index as it stands.
        git("commit", "-q", "-m", "symlink under .planning")
        symlinked = git("rev-parse", "HEAD")
        verdict("repo: a symlink entry under .planning/ is full", "kind=full reason=symlink-or-submodule", symlinked, the_base=renamed)


def self_test() -> int:
    controls: list[str] = []

    def expect(label: str, expected: str, data: bytes) -> None:
        actual = classify_raw(data)
        if actual != expected:
            raise SystemExit(f"classify-changes self-test: {label}: want {expected!r}, got {actual!r}")
        controls.append(label)

    planning_only = [_edit(".planning/x.md", "A"), _edit(".planning/a/b.md"), _edit("AGENTS.md")]
    expect("planning and AGENTS.md only", "kind=planning", _raw(*planning_only))
    expect("planning and AGENTS.md only, newline-separated fixture form", "kind=planning", _raw(*planning_only, nul=False))
    expect("nested .planning/a/b.md alone", "kind=planning", _raw(_edit(".planning/a/b.md")))
    expect("a deleted planning file", "kind=planning", _raw(_edit(".planning/old.md", "D")))
    for path in ("src/core/gabbaboy.c", "include/gabbaboy.h", "tests/CMakeLists.txt", "cmake/x.cmake", ".github/workflows/ci.yml",
                 "docs/guide.md", "README.md", "CMakeLists.txt"):
        expect(f"{path} is full", "kind=full reason=path-outside-planning", _raw(_edit(path)))
    expect("planning plus one src change is full", "kind=full reason=path-outside-planning",
           _raw(_edit(".planning/x.md"), _edit("src/a.c")))
    # A rename from src/ into .planning/ shows up as delete plus add under --no-renames.
    expect("rename src/a.c -> .planning/a.c is full", "kind=full reason=path-outside-planning",
           _raw(_edit("src/a.c", "D"), _edit(".planning/a.c", "A")))
    expect("an R status is full", "kind=full reason=unexpected-status", _raw(_edit(".planning/a.c", "R")))
    for label, path in (("dot-dot segment", ".planning/../src/a.c"), ("leading dot-dot", "../x"), ("dot segment", ".planning/./x.md"),
                        ("empty segment", ".planning//x.md"), ("absolute path", "/etc/passwd"), ("backslash", ".planning\\x.md"),
                        ("trailing slash", ".planning/"), ("control character", ".planning/x\x01.md"),
                        ("case variant .Planning/", ".Planning/x.md"), ("case variant .PLANNING/", ".PLANNING/x.md"),
                        ("a file named .planning", ".planning"), ("prefix collision .planningX/", ".planningX/x.md"),
                        ("AGENTS.md.orig", "AGENTS.md.orig"), ("docs/AGENTS.md", "docs/AGENTS.md"), ("agents.md", "agents.md"),
                        ("Agents.md", "Agents.md"), ("nested .planning under src", "src/.planning/x.md")):
        expect(f"{label} is full", "kind=full reason=path-outside-planning", _raw(_edit(path)))
    expect("symlink mode in a planning path is full", "kind=full reason=symlink-or-submodule",
           _raw(_edit(".planning/link", "A", "000000", "120000")))
    expect("submodule mode in a planning path is full", "kind=full reason=symlink-or-submodule",
           _raw(_edit(".planning/mod", "A", "000000", "160000")))
    expect("a file turned into a symlink is full", "kind=full reason=symlink-or-submodule",
           _raw(_edit("AGENTS.md", "T", "100644", "120000")))
    expect("an empty diff is full", "kind=full reason=empty-diff", b"")
    exact = [_edit(f".planning/{n}.md", "A") for n in range(MAX_FILES)]
    expect(f"{MAX_FILES} files stay planning", "kind=planning", _raw(*exact))
    expect(f"{MAX_FILES + 1} files are full", "kind=full reason=too-many-files",
           _raw(*exact, _edit(f".planning/{MAX_FILES}.md", "A")))
    expect("an odd field count is full", "kind=full reason=malformed-diff", _raw(_edit("AGENTS.md")) + b"extra\0")
    expect("a malformed meta line is full", "kind=full reason=malformed-diff", b"not-a-meta\0AGENTS.md\0")
    expect("non-UTF-8 bytes are full", "kind=full reason=non-utf8-path", _raw(_edit(".planning/x.md"))[:-1] + b"\xff\0")
    # The verdict depends on the set of paths, never on their order.
    mixed = [_edit(".planning/x.md"), _edit("AGENTS.md"), _edit("src/a.c"), _edit(".planning/y.md")]
    reference = classify_raw(_raw(*mixed))
    rng = random.Random(16)
    shuffled = list(mixed)
    for _ in range(5):
        rng.shuffle(shuffled)
        if classify_raw(_raw(*shuffled)) != reference:
            raise SystemExit("classify-changes self-test: shuffled order changed the verdict")
    for permutation in itertools.permutations(planning_only):
        if classify_raw(_raw(*permutation)) != "kind=planning":
            raise SystemExit("classify-changes self-test: permuted planning-only order changed the verdict")
    controls.append("verdict independent of path order")
    _repo_controls(controls)
    print(f"classify-changes self-test pass controls={len(controls)}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--self-test", action="store_true")
    modes.add_argument("--from-raw", type=Path, nargs="+", metavar="FILE", help="classify recorded raw diffs")
    parser.add_argument("--base", default="")
    parser.add_argument("--head", default="")
    parser.add_argument("--ref", default="")
    args = parser.parse_args()
    if sys.flags.optimize:
        print("classify-changes: refusing to run under python -O", file=sys.stderr)
        return 2
    if args.self_test:
        return self_test()
    if args.from_raw is not None:
        for path in args.from_raw:
            try:
                data = path.read_bytes()
            except OSError as exc:
                print(f"kind=full reason=unreadable-raw ({exc.strerror})")
                continue
            print(classify_raw(data))
        return 0
    print(classify_range(args.base, args.head, args.ref))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
