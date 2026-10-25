#!/usr/bin/env python3
"""Planning-label lint over the real ctest json-v1 inventory (Phase 16 plan 04, D-22).

The planning-only CI lane configures without building and runs `ctest -L planning`. That is only sound when

* every test that reads `.planning/` or `AGENTS.md` carries the `planning` label (else a planning change would
  skip a test that depends on it), and
* no `planning`-labelled test needs a built artifact (else the unbuilt lane fails with "Could not find executable").

`--build-dir DIR` runs `ctest --test-dir DIR --show-only=json-v1`. A test is a planning reader when any command
argument names `.planning` or ends with `AGENTS.md`, or when a repository file the command references (a script,
one level deep; documented limitation: a script that merely calls another script is not followed) mentions
`.planning` or `AGENTS.md`. A labelled test is a build user when any argument (also inside `-DNAME=a;b` options)
names a path under the build directory.

Prints `planning-labels pass tests=N planning=M` once. `--self-test` drives fixture inventories through the same
rules and prints `planning-labels self-test pass controls=N` once.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

if not __debug__ or sys.flags.optimize:
    raise SystemExit("verify-planning-labels must not run with python -O")

ROOT = Path(__file__).resolve().parents[2]
# A path below .planning/ or the AGENTS.md file; a bare ".planning" word (an exclusion list, "needs.planning-checks")
# is not a read.
PLANNING_TEXT = re.compile(r"\.planning/|AGENTS\.md")
SCRIPT_SUFFIXES = {".py", ".sh", ".cmake", ".cjs", ".js", ".txt"}
MAX_SCRIPT_BYTES = 4 * 1024 * 1024


class Reject(Exception):
    pass


def _tokens(command: list[str]) -> list[str]:
    """Arguments plus the pieces of `-DNAME=a;b;c` style options, so a wrapped script path is still seen."""
    pieces: list[str] = []
    for argument in command:
        pieces.append(argument)
        for part in re.split(r"[;=]", argument):
            if part and part != argument:
                pieces.append(part)
    return pieces


def _norm(path: str) -> str:
    return path.replace("\\", "/")


def _under(path: str, directory: str) -> bool:
    path, directory = _norm(path), _norm(directory).rstrip("/")
    return path == directory or path.startswith(directory + "/")


def _reads_planning_text(path: Path) -> bool:
    try:
        if path.suffix not in SCRIPT_SUFFIXES or not path.is_file() or path.stat().st_size > MAX_SCRIPT_BYTES:
            return False
        return bool(PLANNING_TEXT.search(path.read_text(encoding="utf-8", errors="replace")))
    except OSError:
        return False


def is_planning_reader(command: list[str], source: str, build: str) -> bool:
    for token in _tokens(command):
        text = _norm(token)
        if "/.planning/" in text or text.endswith("/.planning") or text == ".planning" or text.endswith("AGENTS.md"):
            return True
        if text.startswith("/") or re.match(r"^[A-Za-z]:/", text):
            if _under(text, source) and not _under(text, build) and _reads_planning_text(Path(token)):
                return True
    return False


def uses_build_tree(command: list[str], build: str) -> bool:
    return any(_under(token, build) for token in _tokens(command))


def judge(tests: list[dict], source: str, build: str) -> tuple[int, int]:
    planning = 0
    for test in tests:
        name = test.get("name", "?")
        command = [str(item) for item in test.get("command", [])]
        labels: list[str] = []
        for prop in test.get("properties", []):
            if prop.get("name") == "LABELS":
                value = prop.get("value")
                labels = [str(v) for v in value] if isinstance(value, list) else [str(value)]
        labelled = "planning" in labels
        if labelled:
            planning += 1
            if uses_build_tree(command, build):
                raise Reject(f"REJECT planning-test-needs-build: {name} is labelled planning but its command references the build directory")
        elif is_planning_reader(command, source, build):
            raise Reject(f"REJECT unlabelled-planning-reader: {name} reads .planning/ or AGENTS.md but lacks the planning label")
    return len(tests), planning


def load(build_dir: Path) -> list[dict]:
    result = subprocess.run(["ctest", "--test-dir", str(build_dir), "--show-only=json-v1"], capture_output=True, text=True,
                            check=False, timeout=300)
    if result.returncode != 0:
        raise Reject(f"REJECT inventory-unreadable: ctest exited {result.returncode}: {result.stderr.strip()[:200]}")
    try:
        tests = json.loads(result.stdout)["tests"]
    except (ValueError, KeyError, TypeError) as exc:
        raise Reject(f"REJECT inventory-unreadable: json-v1 did not parse: {exc}") from exc
    if not tests:
        raise Reject("REJECT vacuous: ctest json-v1 listed no tests")
    return tests


def self_test() -> int:
    controls = 0
    with tempfile.TemporaryDirectory(prefix="gbb-planning-labels.") as directory:
        source = Path(directory).resolve() / "src"
        build = source / "build"
        (source / "tests").mkdir(parents=True)
        build.mkdir()
        reader = source / "tests" / "reads-planning.py"
        reader.write_text("open('.planning/STATE.md')\n", encoding="utf-8")
        agents = source / "tests" / "reads-agents.sh"
        agents.write_text("cat AGENTS.md\n", encoding="utf-8")
        clean = source / "tests" / "clean.py"
        clean.write_text("print('ok')\n", encoding="utf-8")

        def test(name: str, command: list[str], labels: list[str] | None = None) -> dict:
            props = [{"name": "LABELS", "value": labels}] if labels else []
            return {"name": name, "command": command, "properties": props}

        py = "/usr/bin/python3"
        cases = [
            ("unlabelled test reading .planning/ is rejected", [test("a", [py, str(reader)])], "unlabelled-planning-reader"),
            ("unlabelled test passing a .planning path is rejected", [test("a", [py, str(clean), f"{source}/.planning/STATE.md"])],
             "unlabelled-planning-reader"),
            ("unlabelled test reading AGENTS.md through a script is rejected", [test("a", ["bash", str(agents)])], "unlabelled-planning-reader"),
            ("reader hidden inside a -D option is rejected", [test("a", ["cmake", f"-DGBB_CMD={py};{reader}", "-P", "x.cmake"])],
             "unlabelled-planning-reader"),
            ("labelled test running a built binary is rejected", [test("a", [str(build / "tests" / "test_api")], ["planning"])],
             "planning-test-needs-build"),
            ("labelled test with a built binary inside a -D option is rejected",
             [test("a", ["cmake", f"-DGBB_CMD={build}/gabbaboy-runner;--x"], ["planning"])], "planning-test-needs-build"),
            ("labelled test reading planning from sources is accepted", [test("a", [py, str(reader)], ["planning"])], None),
            ("unlabelled test that reads nothing planning is accepted", [test("a", [py, str(clean)])], None),
            ("a sibling directory named like the build dir is not the build dir",
             [test("a", [py, f"{build}-other/x"], ["planning"])], None),
        ]
        for label, tests, expected in cases:
            try:
                judge(tests, str(source), str(build))
            except Reject as exc:
                if expected is None or f"REJECT {expected}:" not in str(exc):
                    raise SystemExit(f"planning-labels self-test: {label}: unexpected {exc}")
            else:
                if expected is not None:
                    raise SystemExit(f"planning-labels self-test: {label}: accepted, wanted REJECT {expected}")
            controls += 1
        total, planning = judge([test("a", [py, str(reader)], ["planning"]), test("b", [py, str(clean)])], str(source), str(build))
        if (total, planning) != (2, 1):
            raise SystemExit("planning-labels self-test: counts are wrong")
        controls += 1
    print(f"planning-labels self-test pass controls={controls}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--build-dir", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    if args.build_dir is None:
        parser.error("--build-dir or --self-test is required")
    build = args.build_dir.resolve()
    try:
        total, planning = judge(load(build), str(ROOT), str(build))
    except Reject as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(f"planning-labels pass tests={total} planning={planning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
