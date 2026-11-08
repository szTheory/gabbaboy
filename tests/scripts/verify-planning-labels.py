#!/usr/bin/env python3
"""Planning-label lint over the real ctest json-v1 inventory (Phase 16 plan 04, D-22).

The planning-only CI lane configures without building and runs `ctest -L planning`. That is only sound when

* every test that reads `.planning/` or `AGENTS.md` carries the `planning` label (else a planning change would
  skip a test that depends on it), and
* no `planning`-labelled test needs a built artifact (else the unbuilt lane fails with "Could not find executable").
  A narrowly classified CTest-inventory reader may name its configured build directory because `ctest --show-only`
  reads the configured test list without requiring compiled artifacts.

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
import os
import re
import shutil
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
    normalized = path.replace("\\", "/")
    # Windows paths are case-insensitive on the hosted runner. Normalize them
    # with the host path rules before comparing the fixed build-tree exception.
    if os.name == "nt":
        normalized = os.path.normcase(normalized).replace("\\", "/")
    return normalized


def _same_file(left: str, right: str) -> bool:
    try:
        return os.path.samefile(left, right)
    except (OSError, RuntimeError):
        return False


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


def is_phase22_inventory_reader(name: str, command: list[str], labels: list[str],
                                source: str, build: str) -> bool:
    """Allow the Phase 22 contract to inspect CTest's configured inventory, not compiled artifacts."""
    if name != "phase22_evidence_contract" or "planning" not in labels or "ctest-inventory-only" not in labels:
        return False
    expected_script = _norm(str(Path(source) / "tests/scripts/verify-diagnostic-evidence.py"))
    normalized = [_norm(token) for token in command]
    if normalized.count(expected_script) != 1:
        return False
    script_index = normalized.index(expected_script)
    if script_index != 2 or command[1] != "-I":
        return False
    interpreter = _norm(command[0])
    if not (interpreter.startswith("/") or re.match(r"^[A-Za-z]:/", interpreter)):
        return False
    try:
        if Path(command[0]).resolve(strict=True) != Path(sys.executable).resolve(strict=True):
            return False
    except (OSError, RuntimeError):
        return False
    expected_tail = ["--check", "--repo-root", _norm(source), "--source-revision"]
    tail = normalized[script_index + 1:]
    if len(tail) != 7 or tail[:4] != expected_tail or tail[5] != "--build-dir":
        return False
    source_revision = tail[4]
    build_value = tail[6]
    if not re.fullmatch(r"[0-9a-f]{40}", source_revision):
        return False
    if _norm(build_value) != _norm(build):
        return False
    build_tokens = [_norm(token) for token in _tokens(command) if _under(token, build)]
    return build_tokens == [_norm(build_value)]


def is_release_notes_v04_output_only(name: str, command: list[str], labels: list[str],
                                    source: str, build: str, cmake_executable: str,
                                    source_revision: str) -> bool:
    """Allow the v0.4 planning check to write its one fixed output under build/."""
    if name != "release_notes_v04" or "planning" not in labels or "v02" not in labels:
        return False
    if len(command) != 6:
        return False
    if not _same_file(command[0], cmake_executable):
        return False
    expected_regex = "-DGBB_EXPECT_REGEX=release-notes-preface pass version=0.4.0 candidates=2 diagnostics=513/7/0/0 ledger=docs/support/v0.4.0.md rev=[0-9a-f]+"
    if command[2] != "-DGBB_EXPECT_CODE=0" or command[3] != expected_regex:
        return False
    expected_exit = _norm(str(Path(source) / "tests/expect_exit.cmake"))
    if command[4] != "-P" or _norm(command[5]) != expected_exit or not command[1].startswith("-DGBB_CMD="):
        return False
    wrapped = command[1][len("-DGBB_CMD="):].split(";")
    expected_script = _norm(str(Path(source) / "tests/scripts/verify-support-ledger.py"))
    expected_output = _norm(str(Path(build) / "release-notes-v0.4.0-preface.md"))
    if len(wrapped) != 12 or wrapped[1] != "-I" or _norm(wrapped[2]) != expected_script:
        return False
    try:
        if Path(wrapped[0]).resolve(strict=True) != Path(sys.executable).resolve(strict=True):
            return False
    except (OSError, RuntimeError):
        return False
    if wrapped[3:7] != ["--render-release-notes-preface", "--claims-version", "0.4.0", "--rev"]:
        return False
    if wrapped[7] != source_revision \
            or wrapped[8:] != ["--repo", _norm(source), "--output", expected_output]:
        return False
    build_tokens = [_norm(token) for token in _tokens(command) if _under(token, build)]
    return build_tokens == [expected_output]


def judge(tests: list[dict], source: str, build: str, cmake_executable: str,
          source_revision: str) -> tuple[int, int]:
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
            if uses_build_tree(command, build) \
                    and not is_phase22_inventory_reader(name, command, labels, source, build) \
                    and not is_release_notes_v04_output_only(name, command, labels, source, build,
                                                              cmake_executable, source_revision):
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


def configured_cmake(build_dir: Path) -> str:
    """Return the CMake executable recorded by the build that generated the CTest inventory."""
    cache = build_dir / "CMakeCache.txt"
    try:
        contents = cache.read_text(encoding="utf-8")
    except OSError as exc:
        raise Reject(f"REJECT inventory-unreadable: cannot read configured CMake identity: {exc}") from exc
    match = re.search(r"(?m)^CMAKE_COMMAND:INTERNAL=(.+)$", contents)
    if match is None:
        raise Reject("REJECT inventory-unreadable: configured CMake identity is missing")
    try:
        return str(Path(match.group(1)).resolve(strict=True))
    except (OSError, RuntimeError) as exc:
        raise Reject(f"REJECT inventory-unreadable: configured CMake executable is unavailable: {exc}") from exc


def configured_source_revision(tests: list[dict], source: str, cmake_executable: str) -> str:
    """Read the configure-time source revision from the immutable review contract's CTest command."""
    contracts = [test for test in tests if test.get("name") == "phase23_review_evidence_contract"]
    if len(contracts) != 1:
        raise Reject("REJECT inventory-unreadable: unique review-evidence contract is missing")
    command = [str(item) for item in contracts[0].get("command", [])]
    if len(command) != 6:
        raise Reject("REJECT inventory-unreadable: review-evidence contract command shape changed")
    if not _same_file(command[0], cmake_executable):
        raise Reject("REJECT inventory-unreadable: review-evidence contract uses another CMake executable")
    if not command[1].startswith("-DGBB_CMD=") or command[2] != "-DGBB_EXPECT_CODE=0" \
            or command[4] != "-P" or _norm(command[5]) != _norm(str(Path(source) / "tests/expect_exit.cmake")):
        raise Reject("REJECT inventory-unreadable: review-evidence contract wrapper changed")
    wrapped = command[1][len("-DGBB_CMD="):].split(";")
    expected_script = _norm(str(Path(source) / "tests/scripts/verify-review-evidence.py"))
    try:
        interpreter_matches = Path(wrapped[0]).resolve(strict=True) == Path(sys.executable).resolve(strict=True)
    except (IndexError, OSError, RuntimeError):
        interpreter_matches = False
    if len(wrapped) != 8 or not interpreter_matches or wrapped[1] != "-I" \
            or _norm(wrapped[2]) != expected_script or wrapped[3:5] != ["--check", "--rev"] \
            or wrapped[6:] != ["--repo", _norm(source)] \
            or not re.fullmatch(r"[0-9a-f]{40}", wrapped[5]):
        raise Reject("REJECT inventory-unreadable: review-evidence source revision is invalid")
    return wrapped[5]


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
        evidence = source / "tests/scripts" / "verify-diagnostic-evidence.py"
        evidence.parent.mkdir(parents=True, exist_ok=True)
        evidence.write_text("open('.planning/STATE.md')\n", encoding="utf-8")
        ledger = source / "tests/scripts" / "verify-support-ledger.py"
        ledger.write_text("open('.planning/STATE.md')\n", encoding="utf-8")
        expect_exit = source / "tests" / "expect_exit.cmake"
        expect_exit.write_text("message(STATUS 'ok')\n", encoding="utf-8")

        def test(name: str, command: list[str], labels: list[str] | None = None) -> dict:
            props = [{"name": "LABELS", "value": labels}] if labels else []
            return {"name": name, "command": command, "properties": props}

        py = sys.executable
        fake_python = source / "python-stub"
        fake_python.write_text("#!/bin/sh\nprintf 'diagnostic evidence pass\\n'\n", encoding="utf-8")
        fake_python.chmod(0o755)
        windows_command = [
            py, "-I", str(evidence).replace("/", "\\"), "--check", "--repo-root",
            str(source).replace("/", "\\"), "--source-revision", "a" * 40,
            "--build-dir", str(build).replace("/", "\\"),
        ]
        mixed_separator_command = [
            py, "-I", str(evidence).replace("/", "\\"), "--check", "--repo-root",
            str(source), "--source-revision", "a" * 40,
            "--build-dir", str(build).replace("/", "\\"),
        ]
        release_notes_regex = "-DGBB_EXPECT_REGEX=release-notes-preface pass version=0.4.0 candidates=2 diagnostics=513/7/0/0 ledger=docs/support/v0.4.0.md rev=[0-9a-f]+"

        cmake_executable = shutil.which("cmake")
        if not cmake_executable:
            raise SystemExit("planning-labels self-test: configured CMake executable is unavailable")

        def release_notes_command(output: Path, revision: str = "a" * 40) -> list[str]:
            wrapped = [py, "-I", str(ledger), "--render-release-notes-preface", "--claims-version", "0.4.0",
                       "--rev", revision, "--repo", str(source), "--output", str(output)]
            return [cmake_executable, "-DGBB_CMD=" + ";".join(wrapped),
                    "-DGBB_EXPECT_CODE=0", release_notes_regex,
                    "-P", str(expect_exit)]

        release_notes_writer = release_notes_command(build / "release-notes-v0.4.0-preface.md")
        release_notes_wrong_output = release_notes_command(build / "unexpected.md")
        release_notes_stale_revision = release_notes_command(build / "release-notes-v0.4.0-preface.md", "b" * 40)
        release_notes_extra_artifact = list(release_notes_writer)
        release_notes_extra_artifact[1] += f";{build}/gabbaboy-runner"
        fake_cmake_dir = source / "untrusted-cmake"
        fake_cmake_dir.mkdir()
        fake_cmake = fake_cmake_dir / "cmake"
        fake_cmake.write_text("#!/bin/sh\nprintf 'release-notes-preface pass\\n'\n", encoding="utf-8")
        fake_cmake.chmod(0o755)
        release_notes_fake_cmake = list(release_notes_writer)
        release_notes_fake_cmake[0] = str(fake_cmake)
        wrong_windows_build = str(build / "unexpected").replace("/", "\\")
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
            ("the exact Phase 22 planning contract may read its configured CTest inventory",
             [test("phase22_evidence_contract",
                   [py, "-I", str(evidence), "--check", "--repo-root", str(source), "--source-revision", "a" * 40,
                    "--build-dir", str(build)], ["planning", "ctest-inventory-only"])], None),
            ("the exact Phase 22 planning contract accepts simulated Windows separators",
             [test("phase22_evidence_contract", windows_command, ["planning", "ctest-inventory-only"])], None),
            ("the exact Phase 22 planning contract accepts mixed path separators",
             [test("phase22_evidence_contract", mixed_separator_command, ["planning", "ctest-inventory-only"])], None),
            ("inventory-only classification rejects a configured build directory with a Windows-spelled substitution",
             [test("phase22_evidence_contract",
                   [*mixed_separator_command[:-1], wrong_windows_build], ["planning", "ctest-inventory-only"])],
             "planning-test-needs-build"),
            ("the inventory-only classification is required for build-tree access",
             [test("phase22_evidence_contract",
                   [py, "-I", str(evidence), "--check", "--repo-root", str(source), "--source-revision", "a" * 40,
                    "--build-dir", str(build)], ["planning"])], "planning-test-needs-build"),
            ("inventory-only cannot smuggle a built executable into the command",
             [test("phase22_evidence_contract",
                   [py, "-I", str(evidence), "--check", "--repo-root", str(source), "--source-revision", "a" * 40,
                    "--build-dir", str(build), str(build / "gabbaboy-runner")],
                   ["planning", "ctest-inventory-only"])], "planning-test-needs-build"),
            ("inventory-only classification cannot be reused by another test",
             [test("other_contract",
                   [py, "-I", str(evidence), "--check", "--repo-root", str(source), "--source-revision", "a" * 40,
                    "--build-dir", str(build)], ["planning", "ctest-inventory-only"])], "planning-test-needs-build"),
            ("inventory-only classification rejects extra output or approval flags",
             [test("phase22_evidence_contract",
                   [py, "-I", str(evidence), "--check", "--repo-root", str(source), "--source-revision", "a" * 40,
                    "--build-dir", str(build), "--write-evidence", "unexpected.json"],
                   ["planning", "ctest-inventory-only"])], "planning-test-needs-build"),
            ("inventory-only classification rejects a Python -c pass-output bypass",
             [test("phase22_evidence_contract",
                   [py, "-c", "print('diagnostic evidence pass')", str(evidence), "--check", "--repo-root",
                    str(source), "--source-revision", "a" * 40, "--build-dir", str(build)],
                   ["planning", "ctest-inventory-only"])], "planning-test-needs-build"),
            ("inventory-only classification rejects an absolute Python stub",
             [test("phase22_evidence_contract",
                   [str(fake_python), "-I", str(evidence), "--check", "--repo-root", str(source),
                    "--source-revision", "a" * 40, "--build-dir", str(build)],
                   ["planning", "ctest-inventory-only"])], "planning-test-needs-build"),
            ("the exact v0.4 notes renderer may write its fixed output under build",
             [test("release_notes_v04", release_notes_writer, ["v02", "planning"])], None),
            ("the release-notes output exception cannot be reused by another test",
             [test("other_release_notes", release_notes_writer, ["v02", "planning"])], "planning-test-needs-build"),
            ("the release-notes output exception rejects an unexpected output path",
             [test("release_notes_v04", release_notes_wrong_output, ["v02", "planning"])], "planning-test-needs-build"),
            ("the release-notes output exception rejects a valid but stale source revision",
             [test("release_notes_v04", release_notes_stale_revision, ["v02", "planning"])], "planning-test-needs-build"),
            ("the release-notes output exception cannot smuggle a built executable",
             [test("release_notes_v04", release_notes_extra_artifact, ["v02", "planning"])], "planning-test-needs-build"),
            ("the release-notes output exception rejects a fake outer CMake executable",
             [test("release_notes_v04", release_notes_fake_cmake, ["v02", "planning"])], "planning-test-needs-build"),
            ("the release-notes output renderer must remain in the planning lane",
             [test("release_notes_v04", release_notes_writer, ["v02"])], "unlabelled-planning-reader"),
        ]
        if os.name == "nt":
            # CMake may preserve a different path casing in its cache than the
            # Python temporary path spelling. Windows resolves these to the same
            # output file; the fixed-output exception must recognize that form.
            output_variant = list(release_notes_writer)
            wrapped = output_variant[1][len("-DGBB_CMD="):].split(";")
            output_index = wrapped.index("--output") + 1
            original_output = wrapped[output_index]
            case_variant = next((index for index, char in enumerate(original_output)
                                 if index > 2 and char.isalpha()), None)
            if case_variant is not None:
                char = original_output[case_variant]
                swapped = char.swapcase()
                if swapped != char:
                    wrapped[output_index] = original_output[:case_variant] + swapped + original_output[case_variant + 1:]
                    output_variant[1] = "-DGBB_CMD=" + ";".join(wrapped)
                    cases.append(("the fixed renderer output accepts Windows path casing", [
                        test("release_notes_v04", output_variant, ["v02", "planning"])], None))

        for label, tests, expected in cases:
            try:
                judge(tests, str(source), str(build), cmake_executable, "a" * 40)
            except Reject as exc:
                if expected is None or f"REJECT {expected}:" not in str(exc):
                    raise SystemExit(f"planning-labels self-test: {label}: unexpected {exc}")
            else:
                if expected is not None:
                    raise SystemExit(f"planning-labels self-test: {label}: accepted, wanted REJECT {expected}")
            controls += 1
        total, planning = judge([test("a", [py, str(reader)], ["planning"]), test("b", [py, str(clean)])],
                                str(source), str(build), cmake_executable, "a" * 40)
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
        tests = load(build)
        cmake_executable = configured_cmake(build)
        source_revision = configured_source_revision(tests, str(ROOT), cmake_executable)
        total, planning = judge(tests, str(ROOT), str(build), cmake_executable, source_revision)
    except Reject as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(f"planning-labels pass tests={total} planning={planning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
