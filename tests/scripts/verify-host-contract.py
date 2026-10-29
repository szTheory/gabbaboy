#!/usr/bin/env python3
"""Hold docs/host-contract.json to the C sources that implement it (Phase 18, D-16).

The contract is hand-written canonical JSON with exactly four sections, in this order: exit_codes, cadence,
rtc_wall_clock and save_formats. This checker covers the first three; verify-save-formats.py covers save_formats.

  --check       the JSON text equals json.dumps(json.loads(text), indent=2, ensure_ascii=True) + newline (keys are
                never re-sorted); the exit_codes rows with a number equal the GBB_HOST_EXIT_TABLE rows of
                src/host/host_exit.h (code, name, meaning) and one more row has code null and the name `crash`;
                the cadence values equal the constants in src/host/gbb_host.h
  --self-test   drives this CLI over private fixture repositories, one seeded drift per control
  --docs        the exit-code and save-format tables of the `## Host process contract` section of
                docs/native-integration.md equal docs/host-contract.json cell by cell (backticks are formatting
                only, thousands separators in Bytes are ignored); --docs-file PATH reads a build-tree copy of the
                guide instead of the committed one, which is how the drift control feeds a seeded copy
  --no-interop  no line of the user docs, the contract JSON or the Playstead research note matches
                `(byte-identical|compatible|interoperab)[^.\\n]*mGBA`; a seeded copy of the note that holds its
                original claim must be rejected inside the same run

The JSON and both C files are read with `git show REV:<path>` (never the working tree), so a check sees the
point-in-time facts of one commit. Every failure is `REJECT <code>: <message>` on stderr, exit 1.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import subprocess
import sys
import tempfile

if not __debug__:
    raise SystemExit("verify-host-contract refuses to run under python -O (its checks must stay on)")

ROOT = pathlib.Path(__file__).resolve().parents[2]
SCRIPT = pathlib.Path(__file__).resolve()
CONTRACT = "docs/host-contract.json"
EXIT_HEADER = "src/host/host_exit.h"
HOST_HEADER = "src/host/gbb_host.h"
MAX_BYTES = 8 * 1024 * 1024
SECTIONS = ("exit_codes", "cadence", "rtc_wall_clock", "save_formats")
CADENCE_KEYS = ("frame_half_dots", "quiet_frames", "max_dirty_frames", "rtc_compare_frames",
                "sram_loss_window_frames", "rtc_loss_window_frames")
# JSON key -> the constant in gbb_host.h that fixes it. The two loss windows are derived: a stop loses at most
# the frames since the last flush (the age cap) or the clock-only drift since the last compare.
CADENCE_CONSTANTS = {
    "frame_half_dots": "GBB_HOST_FRAME_HALF_DOTS",
    "quiet_frames": "GBB_HOST_QUIET_FRAMES",
    "max_dirty_frames": "GBB_HOST_MAX_DIRTY_FRAMES",
    "rtc_compare_frames": "GBB_HOST_RTC_COMPARE_FRAMES",
    "sram_loss_window_frames": "GBB_HOST_MAX_DIRTY_FRAMES",
    "rtc_loss_window_frames": "GBB_HOST_RTC_COMPARE_FRAMES",
}
EXIT_ROW = re.compile(r'X\(\s*([0-9]+)\s*,\s*([A-Z][A-Z0-9_]*)\s*,\s*"([^"\\]*)"\s*,\s*"([^"\\]*)"\s*\)')
EXIT_FIELDS = ("code", "name", "meaning")
GUIDE = "docs/native-integration.md"
GUIDE_SECTION = "## Host process contract"
EXIT_TABLE_HEADER = ("Code", "Name", "Meaning")
FORMAT_TABLE_HEADER = ("Type", "RAM code", "Id", "Bytes")
CRASH_CODE_CELL = "none (death by signal)"
NOTE = ".planning/research/v0.3/PLAYSTEAD-CONTRACT.md"
INTEROP_FILES = ("README.md", GUIDE, "docs/cartridge-and-saves.md", "docs/support/unreleased.md", CONTRACT, NOTE)
INTEROP_PATTERN = re.compile(r"(byte-identical|compatible|interoperab)[^.\n]*mGBA", re.IGNORECASE)
# The sentence PLAYSTEAD-CONTRACT.md carried before the D-19 correction: the seeded control re-appends it.
INTEROP_ORIGINAL = "Non-RTC SRAM is byte-identical to mGBA and can be documented as such."


class Reject(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


def reject(code: str, message: str) -> None:
    raise Reject(code, message)


def read_at(repo: pathlib.Path, rev: str, path: str) -> bytes:
    done = subprocess.run(["git", "-C", str(repo), "show", f"{rev}:{path}"], capture_output=True, check=False)
    if done.returncode != 0:
        reject("section-missing", f"{path} is not present at {rev}")
    if len(done.stdout) > MAX_BYTES:
        reject("section-missing", f"{path} exceeds {MAX_BYTES} bytes")
    return done.stdout


def parse_canonical(raw: bytes) -> dict:
    def pairs(items):
        seen: dict = {}
        for key, value in items:
            if key in seen:
                reject("non-canonical", f"{CONTRACT} repeats the key {key!r}")
            seen[key] = value
        return seen

    try:
        text = raw.decode("ascii")
        document = json.loads(text, object_pairs_hook=pairs)
    except (UnicodeDecodeError, ValueError) as error:
        reject("non-canonical", f"{CONTRACT} is not ASCII JSON: {error}")
    if json.dumps(document, indent=2, ensure_ascii=True) + "\n" != text:
        reject("non-canonical", f"{CONTRACT} is not in canonical form (indent=2, ensure_ascii, key order kept, one final newline)")
    if not isinstance(document, dict):
        reject("section-missing", f"{CONTRACT} is not a JSON object")
    return document


def require_keys(found, expected: tuple[str, ...], what: str) -> None:
    """Exactly the expected keys in the written order. The same keys in another order are a re-sorted copy of the
    hand-written file: non-canonical, never silently accepted."""
    keys = tuple(found.keys())
    if keys == expected:
        return
    if sorted(keys) == sorted(expected):
        reject("non-canonical", f"{what} keys are {list(keys)}; the written order is {list(expected)} (never re-sorted)")
    reject("section-missing", f"{what} keys are {list(keys)}, expected exactly {list(expected)}")


def exit_table(header: str) -> list[tuple[int, str, str]]:
    """The GBB_HOST_EXIT_TABLE rows of host_exit.h as (code, name, meaning)."""
    lines = header.splitlines()
    start = next((i for i, line in enumerate(lines) if line.startswith("#define GBB_HOST_EXIT_TABLE(X)")), None)
    if start is None:
        reject("exit-table-drift", f"{EXIT_HEADER} defines no GBB_HOST_EXIT_TABLE")
    body = []
    for line in lines[start:]:
        body.append(line)
        if not line.rstrip().endswith("\\"):
            break
    rows = [(int(code), name, meaning) for code, _ident, name, meaning in EXIT_ROW.findall("\n".join(body))]
    if not rows:
        reject("exit-table-drift", f"{EXIT_HEADER} has no parsable X(code, IDENT, \"name\", \"meaning\") rows")
    return rows


def cadence_constants(header: str) -> dict[str, int]:
    values = {}
    for name in set(CADENCE_CONSTANTS.values()):
        found = re.findall(rf"^#define\s+{name}\s+UINT64_C\(([0-9]+)\)\s*(?:/\*.*)?$", header, re.M)
        if len(found) != 1:
            reject("cadence-drift", f"{HOST_HEADER} must define {name} exactly once as UINT64_C(<n>)")
        values[name] = int(found[0])
    return values


def check(repo: pathlib.Path, rev: str) -> tuple[int, int]:
    document = parse_canonical(read_at(repo, rev, CONTRACT))
    require_keys(document, SECTIONS, "top-level")
    if document["rtc_wall_clock"] != "not-recorded":
        reject("section-missing", f"rtc_wall_clock must be \"not-recorded\", got {document['rtc_wall_clock']!r}")
    if not isinstance(document["save_formats"], dict):
        reject("section-missing", "save_formats must be an object")

    rows = document["exit_codes"]
    if not isinstance(rows, list) or not all(isinstance(row, dict) and tuple(row.keys()) == EXIT_FIELDS for row in rows):
        reject("exit-table-drift", f"exit_codes must be a list of objects with the fields {', '.join(EXIT_FIELDS)}")
    numbered = [(row["code"], row["name"], row["meaning"]) for row in rows if row["code"] is not None]
    crash = [row for row in rows if row["code"] is None]
    expected = exit_table(read_at(repo, rev, EXIT_HEADER).decode("utf-8", errors="strict"))
    if numbered != expected:
        reject("exit-table-drift", f"exit_codes rows {numbered} differ from GBB_HOST_EXIT_TABLE {expected}")
    if len(crash) != 1 or crash[0]["name"] != "crash" or rows[-1] is not crash[0]:
        reject("exit-table-drift", "exit_codes needs exactly one final row with code null and the name crash")

    cadence = document["cadence"]
    if not isinstance(cadence, dict):
        reject("section-missing", "cadence must be an object")
    require_keys(cadence, CADENCE_KEYS, "cadence")
    constants = cadence_constants(read_at(repo, rev, HOST_HEADER).decode("utf-8", errors="strict"))
    for key in CADENCE_KEYS:
        value = cadence[key]
        wanted = constants[CADENCE_CONSTANTS[key]]
        if isinstance(value, bool) or not isinstance(value, int) or value != wanted:
            reject("cadence-drift", f"cadence.{key} is {value!r}, {CADENCE_CONSTANTS[key]} is {wanted}")
    return len(rows), len(cadence)


# ---- --docs: the published tables against the JSON ------------------------------------------------------------

def table_cells(line: str) -> list[str]:
    return [cell.strip().replace("`", "") for cell in line.strip().strip("|").split("|")]


def guide_section(guide: str) -> list[str]:
    lines = guide.splitlines()
    starts = [i for i, line in enumerate(lines) if line.strip() == GUIDE_SECTION]
    if len(starts) != 1:
        reject("doc-table-missing", f"{GUIDE} must hold exactly one {GUIDE_SECTION!r} heading, found {len(starts)}")
    section = []
    for line in lines[starts[0] + 1:]:
        if line.startswith("## "):
            break
        section.append(line)
    return section


def section_table(section: list[str], header: tuple[str, ...]) -> list[list[str]]:
    """The body rows of the one table whose header row is exactly `header`."""
    found = [i for i, line in enumerate(section) if line.lstrip().startswith("|") and tuple(table_cells(line)) == header]
    if len(found) != 1:
        reject("doc-table-missing", f"the section needs exactly one table with the header {' | '.join(header)}, found {len(found)}")
    at = found[0]
    if at + 1 >= len(section) or not all(re.fullmatch(r":?-{3,}:?", cell) for cell in table_cells(section[at + 1])):
        reject("doc-table-missing", f"the {' | '.join(header)} table has no separator row")
    rows = []
    for line in section[at + 2:]:
        if not line.lstrip().startswith("|"):
            break
        rows.append(table_cells(line))
    return rows


def check_docs(guide: str, document: dict) -> tuple[int, int]:
    section = guide_section(guide)
    exit_rows = section_table(section, EXIT_TABLE_HEADER)
    wanted_exit = [[str(row["code"]) if row["code"] is not None else CRASH_CODE_CELL, row["name"], row["meaning"]]
                   for row in document["exit_codes"]]
    if exit_rows != wanted_exit:
        for index in range(max(len(exit_rows), len(wanted_exit))):
            have = exit_rows[index] if index < len(exit_rows) else None
            want = wanted_exit[index] if index < len(wanted_exit) else None
            if have != want:
                reject("doc-table-drift", f"exit-code table row {index + 1} is {have}, host-contract.json says {want}")
    format_rows = section_table(section, FORMAT_TABLE_HEADER)
    json_rows = document["save_formats"]["rows"]
    if len(format_rows) != len(json_rows):
        reject("doc-table-drift", f"the save-format table has {len(format_rows)} rows, host-contract.json has {len(json_rows)}")
    for index, (cells, row) in enumerate(zip(format_rows, json_rows), start=1):
        if len(cells) != 4:
            reject("doc-table-drift", f"save-format table row {index} has {len(cells)} cells, expected 4")
        bytes_cell = cells[3].replace(",", "")
        wanted = [row["type"], row["ram_code"], row["id"], str(row["bytes"])]
        if [cells[0], cells[1], cells[2], bytes_cell] != wanted:
            reject("doc-table-drift", f"save-format table row {index} is {cells}, host-contract.json says {wanted}")
    return len(exit_rows), len(format_rows)


# ---- --no-interop: no emulator-interoperability claim anywhere in the published text ------------------------

def interop_lines(label: str, text: str) -> None:
    for number, line in enumerate(text.splitlines(), start=1):  # one line at a time: a match never spans lines
        if INTEROP_PATTERN.search(line):
            reject("interop-claim", f"{label} line {number} makes an emulator interoperability claim")


def check_no_interop(repo: pathlib.Path, rev: str) -> int:
    texts = {path: read_at(repo, rev, path).decode("utf-8", errors="strict") for path in INTEROP_FILES}
    for path in INTEROP_FILES:
        interop_lines(path, texts[path])
    seeded = texts[NOTE].rstrip("\n") + "\n" + INTEROP_ORIGINAL + "\n"
    try:
        interop_lines("the seeded copy", seeded)
    except Reject:
        return len(INTEROP_FILES)
    reject("control-accepted", "the seeded copy holding the original Playstead sentence was accepted; the scan has lost its teeth")


# ---- self-test ----------------------------------------------------------------------------------------------

def git(repo: pathlib.Path, *args: str) -> str:
    done = subprocess.run(["git", "-C", str(repo), "-c", "user.name=fixture", "-c", "user.email=fixture@example.invalid",
                           "-c", "commit.gpgsign=false", "-c", "core.hooksPath=/dev/null", *args],
                          capture_output=True, text=True, check=True)
    return done.stdout.strip()


def make_repo(parent: pathlib.Path, name: str, files: dict[str, str]) -> pathlib.Path:
    repo = parent / name
    repo.mkdir()
    git(repo, "init", "-q")
    for path, text in files.items():
        target = repo / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(text.encode("utf-8"))  # bytes: no newline translation on any platform
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "fixture")
    return repo


def run_cli(repo: pathlib.Path) -> subprocess.CompletedProcess:
    rev = git(repo, "rev-parse", "HEAD")
    return subprocess.run([sys.executable, "-I", str(SCRIPT), "--check", "--rev", rev, "--repo", str(repo)],
                          capture_output=True, text=True, timeout=120, check=False)


def self_test(repo: pathlib.Path, rev: str | None) -> int:
    """With --rev the seed files are read from that commit (a boundary check never reads the live tree)."""
    paths = (CONTRACT, EXIT_HEADER, HOST_HEADER)
    if rev is not None:
        seed = {path: read_at(repo, rev, path).decode("utf-8", errors="strict") for path in paths}
    else:
        seed = {path: (ROOT / path).read_text(encoding="utf-8") for path in paths}
    document = json.loads(seed[CONTRACT])
    controls = 0

    def dump(value) -> str:
        return json.dumps(value, indent=2, ensure_ascii=True) + "\n"

    def mutated(path: str, old: str, new: str) -> dict[str, str]:
        if seed[path].count(old) != 1:
            raise SystemExit(f"self-test seed anchor {old!r} does not occur exactly once in {path}")
        return {**seed, path: seed[path].replace(old, new)}

    def with_document(edit) -> dict[str, str]:
        copy = json.loads(seed[CONTRACT])
        edit(copy)
        return {**seed, CONTRACT: dump(copy)}

    with tempfile.TemporaryDirectory(prefix="gbb-host-contract-") as temp:
        parent = pathlib.Path(temp)
        count = 0

        def repo_for(files: dict[str, str]) -> pathlib.Path:
            nonlocal count
            count += 1
            return make_repo(parent, f"r{count}", files)

        def expect_pass(label: str, files: dict[str, str]) -> None:
            nonlocal controls
            result = run_cli(repo_for(files))
            if result.returncode != 0 or "host-contract pass exit_codes=4 cadence=6" not in result.stdout:
                raise SystemExit(f"self-test {label}: expected a pass, got {result.stdout.strip()} {result.stderr.strip()[:240]}")
            controls += 1

        def expect_reject(label: str, files: dict[str, str], code: str) -> None:
            nonlocal controls
            result = run_cli(repo_for(files))
            if result.returncode == 0 or "host-contract pass" in result.stdout:
                raise SystemExit(f"self-test accepted {label}")
            if f"REJECT {code}:" not in result.stderr:
                raise SystemExit(f"self-test {label}: expected REJECT {code}, got: {result.stderr.strip()[:240]}")
            controls += 1

        expect_pass("the real contract", seed)
        expect_reject("tab-indented JSON", {**seed, CONTRACT: json.dumps(document, indent="\t") + "\n"}, "non-canonical")
        expect_reject("sorted keys", {**seed, CONTRACT: json.dumps(document, indent=2, sort_keys=True) + "\n"}, "non-canonical")
        expect_reject("a missing cadence section", with_document(lambda d: d.pop("cadence")), "section-missing")
        expect_reject("rtc_wall_clock recorded", with_document(lambda d: d.update(rtc_wall_clock="recorded")), "section-missing")
        expect_reject("a changed host_exit.h meaning",
                      mutated(EXIT_HEADER, "Refused before any save mutation", "Refused sometimes"), "exit-table-drift")
        expect_reject("a missing crash row", with_document(lambda d: d["exit_codes"].pop()), "exit-table-drift")
        expect_reject("a renumbered exit row", with_document(lambda d: d["exit_codes"][1].update(code=3)), "exit-table-drift")
        expect_reject("quiet frames 17 in gbb_host.h",
                      mutated(HOST_HEADER, "#define GBB_HOST_QUIET_FRAMES UINT64_C(16)",
                              "#define GBB_HOST_QUIET_FRAMES UINT64_C(17)"), "cadence-drift")
        expect_reject("a changed loss window",
                      with_document(lambda d: d["cadence"].update(sram_loss_window_frames=301)), "cadence-drift")
    print(f"host-contract self-test pass controls={controls}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="canonical JSON, exit table and cadence")
    mode.add_argument("--self-test", action="store_true", help="seeded drift controls")
    mode.add_argument("--docs", action="store_true", help="the guide's tables against the JSON")
    mode.add_argument("--no-interop", action="store_true", help="no emulator-interoperability claim in the published text")
    parser.add_argument("--docs-file", type=pathlib.Path, help="read the native guide from this file instead of --rev")
    parser.add_argument("--rev", help="the commit to read the contract and C sources from")
    parser.add_argument("--repo", type=pathlib.Path, default=ROOT, help="the repository root")
    args = parser.parse_args()
    try:
        if args.self_test:
            return self_test(args.repo, args.rev)
        if args.rev is None:
            reject("usage", "--rev is required")
        if args.docs:
            document = parse_canonical(read_at(args.repo, args.rev, CONTRACT))
            if args.docs_file is not None:
                guide = args.docs_file.read_text(encoding="utf-8")
            else:
                guide = read_at(args.repo, args.rev, GUIDE).decode("utf-8", errors="strict")
            tables_exit, tables_format = check_docs(guide, document)
            print(f"host-contract docs pass exit_rows={tables_exit} format_rows={tables_format}")
            return 0
        if args.no_interop:
            files = check_no_interop(args.repo, args.rev)
            print(f"no-interop-claims pass files={files} controls=1")
            return 0
        exit_rows, cadence_keys = check(args.repo, args.rev)
        print(f"host-contract pass exit_codes={exit_rows} cadence={cadence_keys}")
        return 0
    except Reject as error:
        print(f"REJECT {error.code}: {error.message}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
