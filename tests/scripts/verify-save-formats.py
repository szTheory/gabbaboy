#!/usr/bin/env python3
"""Hold docs/host-contract.json's save_formats table to the runner that publishes it (Phase 18, HOST-03, D-19/D-20).

The contract JSON and the revision under test are read with `git show REV:<path>`, never from the working tree,
so a check sees the point-in-time facts of one commit. The compiled runner is a separate input.

  --check              for every row, on both the dmg and the cgb profile: `--print-save-format` prints the row's
                       id and byte count; a `--frames 2` batch run produces a .sav of exactly that size whose
                       SRAM byte 0 is $5A ($FA with every byte >= $F0 for MBC2); RTC rows end with a structurally
                       valid GBRT version-1 block (the RTC-only $0F row is that block alone); both profiles agree;
                       a no-battery cartridge prints `save_format=none bytes=0` and creates no file
  --check-print        the print leg only (no file is produced), which is what every platform can run

  --check-completeness every admitted battery (type, RAM code, ROM code) combination reported by the core's
                       gbb_probe_rom / gbb_battery_size (the test_save_format_completeness enumerator, run with
                       --enumerator or read from --completeness FILE) has exactly one row with equal bytes and RTC
                       presence, every row is admitted, and the admitted no-battery types equal no_battery_types
  --freeze             the table is append-only against the latest strict-semver v* tag: every baseline row must
                       survive unchanged; a tag whose tree lacks the file is baseline=none (pass); no strict tag fails

A row's bytes, ram_bytes and rtc_bytes, its id grammar, its order and the "same id means same bytes" rule are
checked structurally before any runner is started. Every failure is `REJECT <code>: <message>` on stderr, exit 1.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import pathlib
import re
import shutil
import subprocess
import sys
from typing import NamedTuple

if not __debug__:
    raise SystemExit("verify-save-formats refuses to run under python -O (its checks must stay on)")

ROOT = pathlib.Path(__file__).resolve().parents[2]
CONTRACT = "docs/host-contract.json"
MAX_BYTES = 8 * 1024 * 1024
TAG = re.compile(r"^v[0-9]+\.[0-9]+\.[0-9]+$")
ADMITTED_LINE = re.compile(
    r"^admitted type=0x([0-9A-F]{2}) ram=0x([0-9A-F]{2}) rom=0x([0-9A-F]{2}) battery=([01]) bytes=([0-9]+) rtc=([01])$")
DONE_LINE = re.compile(r"^admitted-done count=([0-9]+)$")
ID_GRAMMAR = re.compile(r"^gabbaboy-[a-z0-9-]{1,48}-v[1-9][0-9]*$")
HEX_BYTE = re.compile(r"^0x[0-9A-F]{2}$")
PRINT_LINE = re.compile(r"^save_format=([^\s]+) bytes=([0-9]+)\n$")
PROFILES = ("dmg", "cgb")
FRAMES = "2"
RUN_TIMEOUT = 60.0
SECTIONS = ("exit_codes", "cadence", "rtc_wall_clock", "save_formats")
ROW_FIELDS = ("type", "ram_code", "rom_code_max", "id", "bytes", "ram_bytes", "rtc_bytes")
RTC_BLOCK = 21
# Cartridges without a battery, probed to prove the runner prints the sentinel and creates nothing.
NO_BATTERY_PROBES = ((0x1A, 0x03), (0x01, 0x00))
NONE_LINE = "save_format=none bytes=0\n"


class Reject(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


def reject(code: str, message: str) -> None:
    raise Reject(code, message)


class Row(NamedTuple):
    type: int
    ram_code: int
    rom_code_max: int | None
    id: str
    bytes: int
    ram_bytes: int
    rtc_bytes: int

    def label(self) -> str:
        return f"${self.type:02X}/${self.ram_code:02X}"

    def admits(self, rom_code: int) -> bool:
        return self.rom_code_max is None or rom_code <= self.rom_code_max

    def order_key(self) -> tuple[int, int, int]:
        return (self.type, self.ram_code, 255 if self.rom_code_max is None else self.rom_code_max)


class Source:
    """Reads one repository path from a commit with `git show REV:<path>`."""

    def __init__(self, repo: pathlib.Path, rev: str) -> None:
        self.repo = repo
        self.rev = rev

    def read(self, path: str, code: str = "section-missing") -> bytes:
        done = subprocess.run(["git", "-C", str(self.repo), "show", f"{self.rev}:{path}"],
                              capture_output=True, check=False)
        if done.returncode != 0:
            reject(code, f"{path} is not present at {self.rev}")
        if len(done.stdout) > MAX_BYTES:
            reject("path-invalid", f"{path} exceeds {MAX_BYTES} bytes")
        return done.stdout


def parse_canonical(raw: bytes, what: str) -> dict:
    """Parses raw as the hand-written canonical form: ASCII, two-space indent, key order as written, one final
    newline. The text must equal json.dumps(json.loads(text), indent=2, ensure_ascii=True) + newline; keys are
    never sorted, so a sorted or tab-indented copy is a different text."""

    def pairs(items):
        seen: dict = {}
        for key, value in items:
            if key in seen:
                reject("non-canonical", f"{what} repeats the key {key!r}")
            seen[key] = value
        return seen

    try:
        text = raw.decode("ascii")
        document = json.loads(text, object_pairs_hook=pairs)
    except (UnicodeDecodeError, ValueError) as error:
        reject("non-canonical", f"{what} is not ASCII JSON: {error}")
    if json.dumps(document, indent=2, ensure_ascii=True) + "\n" != text:
        reject("non-canonical", f"{what} is not in canonical form (indent=2, ensure_ascii, key order kept, one final newline)")
    if not isinstance(document, dict):
        reject("section-missing", f"{what} is not a JSON object")
    return document


def hex_byte(value, label: str) -> int:
    if not isinstance(value, str) or not HEX_BYTE.match(value):
        reject("row-malformed", f"{label} must be a string like \"0x1B\", got {value!r}")
    return int(value, 16)


def integer(value, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        reject("row-malformed", f"{label} must be a non-negative integer, got {value!r}")
    return value


def parse_rows(document: dict) -> tuple[list[Row], list[int]]:
    """The save_formats rows and no_battery_types, after the structural rules (malformed, id grammar, byte sum,
    same id same bytes, row order). Completeness against the core is a separate leg."""
    section = document.get("save_formats")
    if not isinstance(section, dict) or not isinstance(section.get("rows"), list) \
            or not isinstance(section.get("no_battery_types"), list):
        reject("section-missing", "save_formats needs a rows list and a no_battery_types list")
    rows: list[Row] = []
    for position, entry in enumerate(section["rows"]):
        where = f"save_formats.rows[{position}]"
        if not isinstance(entry, dict):
            reject("row-malformed", f"{where} is not an object")
        if tuple(entry.keys()) != ROW_FIELDS:
            if sorted(entry.keys()) == sorted(ROW_FIELDS):  # a re-sorted copy of the hand-written file
                reject("non-canonical", f"{where} keys are {list(entry.keys())}; the written order is {list(ROW_FIELDS)}")
            reject("row-malformed", f"{where} must have exactly the fields {', '.join(ROW_FIELDS)}")
        limit = entry["rom_code_max"]
        rows.append(Row(
            hex_byte(entry["type"], f"{where}.type"), hex_byte(entry["ram_code"], f"{where}.ram_code"),
            None if limit is None else hex_byte(limit, f"{where}.rom_code_max"),
            entry["id"] if isinstance(entry["id"], str) else reject("row-malformed", f"{where}.id is not a string"),
            integer(entry["bytes"], f"{where}.bytes"), integer(entry["ram_bytes"], f"{where}.ram_bytes"),
            integer(entry["rtc_bytes"], f"{where}.rtc_bytes")))
    for row in rows:
        if not ID_GRAMMAR.fullmatch(row.id):
            reject("id-grammar", f"{row.label()} id {row.id!r} does not match {ID_GRAMMAR.pattern}")
    for row in rows:
        if row.bytes != row.ram_bytes + row.rtc_bytes:
            reject("sum-mismatch", f"{row.label()} {row.id}: bytes {row.bytes} != ram_bytes {row.ram_bytes} + rtc_bytes {row.rtc_bytes}")
    sizes: dict[str, Row] = {}
    for row in rows:
        first = sizes.setdefault(row.id, row)
        if (first.bytes, first.ram_bytes, first.rtc_bytes) != (row.bytes, row.ram_bytes, row.rtc_bytes):
            reject("id-size-conflict", f"id {row.id} names {first.bytes} bytes at {first.label()} but {row.bytes} at {row.label()}")
    for earlier, later in zip(rows, rows[1:]):
        if not earlier.order_key() < later.order_key():
            reject("row-order", f"{later.label()} {later.id} is not after {earlier.label()} in (type, ram_code) order")
    types = [hex_byte(item, f"save_formats.no_battery_types[{i}]") for i, item in enumerate(section["no_battery_types"])]
    if types != sorted(set(types)):
        reject("row-order", "no_battery_types must be ascending without duplicates")
    return rows, types


def load_rows(source: Source) -> tuple[list[Row], list[int]]:
    return parse_rows(parse_canonical(source.read(CONTRACT), CONTRACT))


def load_fixture(repo_root: pathlib.Path):
    path = repo_root / "tests" / "scripts" / "host_fixture.py"
    spec = importlib.util.spec_from_file_location("host_fixture", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# ---- running the runner -------------------------------------------------------------------------------------

def run_runner(command: list[str], args: list[str], cwd: pathlib.Path) -> tuple[int, str, str]:
    try:
        done = subprocess.run([*command, *args], cwd=str(cwd), stdin=subprocess.DEVNULL, capture_output=True,
                              text=True, encoding="utf-8", errors="replace", timeout=RUN_TIMEOUT, check=False)
    except subprocess.TimeoutExpired:
        reject("runner-failed", f"the runner exceeded {RUN_TIMEOUT} s")
    except OSError as error:
        reject("runner-failed", f"the runner could not be started: {error}")
    return done.returncode, done.stdout, done.stderr


def snapshot(directory: pathlib.Path) -> list[tuple[str, str]]:
    return sorted((entry.name, hashlib.sha256(entry.read_bytes()).hexdigest() if entry.is_file() else "dir")
                  for entry in directory.iterdir())


def print_format(command: list[str], rom: pathlib.Path, profile: str, cwd: pathlib.Path) -> tuple[str, int]:
    """Runs `--print-save-format` and returns (id, bytes). It must exit 0 and leave the cwd and the ROM
    directory byte-identical."""
    before = (snapshot(cwd), snapshot(rom.parent))
    code, out, err = run_runner(command, ["--print-save-format", "--rom", str(rom), "--profile", profile], cwd)
    if code != 0:
        reject("runner-failed", f"--print-save-format exited {code} on {profile}: {err.strip()[:200]}")
    if (snapshot(cwd), snapshot(rom.parent)) != before:
        reject("print-side-effect", f"--print-save-format changed the working or ROM directory on {profile}")
    match = PRINT_LINE.match(out)
    if match is None:
        reject("runner-failed", f"--print-save-format printed {out[:120]!r}, not one save_format= line")
    return match.group(1), int(match.group(2))


def valid_rtc_block(block: bytes) -> str | None:
    """None when the 21-byte block is a structurally valid GBRT version-1 block, else the reason. Structure only:
    RTC bytes vary with emulated time, so no fixed digest is possible."""
    if len(block) != RTC_BLOCK:
        return f"block is {len(block)} bytes"
    if block[0:4] != b"GBRT":
        return "bad magic"
    if block[4] != 1:
        return f"version {block[4]}"
    if int.from_bytes(block[5:9], "little") >= 1 << 23:
        return "sub-second count out of range"
    for base in (9, 14):
        seconds, minutes, hours, _day_low, day_high = block[base:base + 5]
        if seconds > 0x3F or minutes > 0x3F or hours > 0x1F or (day_high & 0x3E) != 0:
            return f"clock field out of range at {base}"
    if block[20] != 0:
        return "reserved byte not zero"
    return None


def check_image(row: Row, image: bytes, profile: str) -> None:
    where = f"{row.label()} {row.id} ({profile})"
    if len(image) != row.bytes:
        reject("file-size", f"{where}: the .sav is {len(image)} bytes, the contract says {row.bytes}")
    if row.ram_bytes > 0:
        if row.type in (0x05, 0x06):  # MBC2: 4-bit cells read back with the upper nibble set
            if image[0] != 0xFA or any(byte < 0xF0 for byte in image[:row.ram_bytes]):
                reject("file-content", f"{where}: MBC2 image must start $FA with every byte >= $F0")
        elif image[0] != 0x5A:
            reject("file-content", f"{where}: SRAM byte 0 is ${image[0]:02X}, expected $5A")
    if row.rtc_bytes > 0:
        bad = valid_rtc_block(image[row.ram_bytes:])
        if bad is not None:
            reject("file-content", f"{where}: the trailing GBRT block is invalid ({bad})")


def fresh(directory: pathlib.Path) -> pathlib.Path:
    if directory.exists():
        shutil.rmtree(directory)
    directory.mkdir(parents=True)
    return directory


def make_case(fixture, base: pathlib.Path, name: str, cart_type: int, ram_code: int, rom_code: int):
    """A fresh per-row, per-profile directory: rom.gb, an empty save/ and an empty cwd/."""
    case = fresh(base / name)
    (case / "save").mkdir()
    (case / "cwd").mkdir()
    rom = case / "rom.gb"
    rom.write_bytes(fixture.build_rom("write5a", cart_type, ram_code, rom_code))
    return case, rom


def check_rows(command: list[str], rows: list[Row], fixture, work: pathlib.Path, produce: bool) -> int:
    """The shared print and produced-file leg. Returns the number of .sav files verified."""
    files = 0
    base = work / ("files" if produce else "print")
    shutil.rmtree(base, ignore_errors=True)
    for index, row in enumerate(rows):
        rom_code = 0
        variants = [(rom_code, row)]
        if row.rom_code_max not in (None, 0):
            variants.append((row.rom_code_max, row))  # the constraint boundary is admitted too
        for rom_code, _ in variants:
            printed: dict[str, tuple[str, int]] = {}
            cases = {}
            for profile in PROFILES:
                case, rom = make_case(fixture, base, f"{index:02d}-{row.type:02X}-{row.ram_code:02X}-r{rom_code}-{profile}",
                                      row.type, row.ram_code, rom_code)
                cases[profile] = (case, rom)
                printed[profile] = print_format(command, rom, profile, case / "cwd")
            if printed["dmg"] != printed["cgb"]:
                reject("profile-id-mismatch", f"{row.label()}: dmg printed {printed['dmg']}, cgb printed {printed['cgb']}")
            got_id, got_bytes = printed["dmg"]
            if got_id != row.id:
                reject("id-changed", f"{row.label()}: the runner prints id {got_id!r}, the contract says {row.id!r}")
            if got_bytes != row.bytes:
                reject("size-mismatch", f"{row.label()} {row.id}: the runner prints {got_bytes} bytes, the contract says {row.bytes}")
            if not produce:
                continue
            for profile in PROFILES:
                case, rom = cases[profile]
                code, _out, err = run_runner(command, ["--rom", str(rom), "--save-dir", str(case / "save"),
                                                       "--profile", profile, "--frames", FRAMES], case / "cwd")
                if code != 0:
                    reject("runner-failed", f"{row.label()} ({profile}) --frames {FRAMES} exited {code}: {err.strip()[:200]}")
                names = sorted(entry.name for entry in (case / "save").iterdir())
                if names != ["rom.sav"]:
                    reject("file-size", f"{row.label()} ({profile}): the save directory holds {names}, expected exactly rom.sav")
                check_image(row, (case / "save" / "rom.sav").read_bytes(), profile)
                if rom_code == 0:
                    files += 1
    for cart_type, ram_code in NO_BATTERY_PROBES:
        for profile in PROFILES:
            case, rom = make_case(fixture, base, f"none-{cart_type:02X}-{profile}", cart_type, ram_code, 0)
            got = print_format(command, rom, profile, case / "cwd")
            if got != ("none", 0):
                reject("id-changed", f"${cart_type:02X} has no battery but printed save_format={got[0]} bytes={got[1]}")
            if not produce:
                continue
            code, _out, err = run_runner(command, ["--rom", str(rom), "--save-dir", str(case / "save"),
                                                   "--profile", profile, "--frames", FRAMES], case / "cwd")
            if code != 0:
                reject("runner-failed", f"${cart_type:02X} ({profile}) --frames {FRAMES} exited {code}: {err.strip()[:200]}")
            created = sorted(entry.name for entry in (case / "save").iterdir())
            if created:
                reject("no-battery-file", f"${cart_type:02X} has no battery but the runner created {created}")
    return files


# ---- completeness against the core (D-20) -------------------------------------------------------------------

class Combo(NamedTuple):
    type: int
    ram_code: int
    rom_code: int
    battery: bool
    bytes: int
    rtc: bool


def parse_enumeration(text: str) -> list[Combo]:
    combos: list[Combo] = []
    done: int | None = None
    for line in text.splitlines():
        match = ADMITTED_LINE.match(line)
        if match is not None and done is None:
            combos.append(Combo(int(match.group(1), 16), int(match.group(2), 16), int(match.group(3), 16),
                                match.group(4) == "1", int(match.group(5)), match.group(6) == "1"))
            continue
        finish = DONE_LINE.match(line)
        if finish is not None and done is None:
            done = int(finish.group(1))
            continue
        reject("enumerator-output", f"unexpected enumerator line {line[:120]!r}")
    if done is None or done != len(combos):
        reject("enumerator-output", f"admitted-done count={done} does not match the {len(combos)} admitted lines")
    return combos


def check_completeness(rows: list[Row], no_battery: list[int], combos: list[Combo]) -> int:
    """Both directions: every admitted battery combination maps to exactly one row, every row is admitted."""
    if not rows:
        reject("row-missing", "save_formats.rows is empty, so no admitted battery cartridge has a row")
    used = [False] * len(rows)
    boundary = [False] * len(rows)
    for combo in combos:
        if not combo.battery:
            continue
        matches = [index for index, row in enumerate(rows)
                   if row.type == combo.type and row.ram_code == combo.ram_code and row.admits(combo.rom_code)]
        where = f"${combo.type:02X}/${combo.ram_code:02X} ROM code ${combo.rom_code:02X}"
        if not matches:
            reject("row-missing", f"the core admits {where} ({combo.bytes} bytes) but the contract has no row for it")
        if len(matches) > 1:
            reject("row-overlap", f"{where} matches {len(matches)} rows")
        index = matches[0]
        row = rows[index]
        if combo.bytes != row.bytes or combo.rtc != (row.rtc_bytes > 0):
            reject("size-mismatch", f"{where} {row.id}: the core makes {combo.bytes} bytes (rtc={int(combo.rtc)}), "
                                    f"the contract says {row.bytes} (rtc_bytes={row.rtc_bytes})")
        used[index] = True
        boundary[index] |= row.rom_code_max is not None and combo.rom_code == row.rom_code_max
    for index, row in enumerate(rows):
        if not used[index]:
            reject("row-not-admitted", f"{row.label()} {row.id}: the core admits no battery cartridge with this type and RAM code")
        if row.rom_code_max is not None and not boundary[index]:
            reject("row-not-admitted", f"{row.label()} {row.id}: the core does not admit ROM code ${row.rom_code_max:02X}")
    admitted_plain = sorted({combo.type for combo in combos if not combo.battery})
    for cart_type in admitted_plain:
        if cart_type not in no_battery:
            reject("row-missing", f"${cart_type:02X} is admitted without a battery but is not in no_battery_types")
    for cart_type in no_battery:
        if cart_type not in admitted_plain:
            reject("row-not-admitted", f"no_battery_types lists ${cart_type:02X} but the core admits no such cartridge without a battery")
    battery_types = {row.type for row in rows}
    if battery_types & set(no_battery):
        reject("row-not-admitted", f"types {sorted(battery_types & set(no_battery))} are both battery rows and no_battery_types")
    return len(admitted_plain)


def command_completeness(args) -> int:
    if args.rev is None or (args.enumerator is None and args.completeness is None):
        reject("usage", "--rev and --enumerator (or --completeness FILE) are required")
    rows, no_battery = load_rows(Source(args.repo, args.rev))
    if args.completeness is not None:
        text = args.completeness.read_text(encoding="utf-8", errors="strict")
    else:
        done = subprocess.run([args.enumerator], capture_output=True, text=True, encoding="utf-8", errors="replace",
                              timeout=RUN_TIMEOUT, check=False)
        if done.returncode != 0:
            reject("enumerator-output", f"the enumerator exited {done.returncode}: {done.stdout.strip()[:200]}")
        text = done.stdout
    combos = parse_enumeration(text)
    plain = check_completeness(rows, no_battery, combos)
    battery = sum(1 for combo in combos if combo.battery)
    print(f"save-formats completeness pass rows={len(rows)} battery_combinations={battery} no_battery_types={plain}")
    return 0


# ---- the freeze against the latest release tag (D-19, one-way) -------------------------------------------------

def strict_tags(repo: pathlib.Path) -> list[str]:
    done = subprocess.run(["git", "-C", str(repo), "tag", "--list", "v*"], capture_output=True, text=True, check=False)
    tags = [tag for tag in done.stdout.split() if TAG.fullmatch(tag)]
    return sorted(tags, key=lambda tag: tuple(int(part) for part in tag[1:].split(".")))


def command_freeze(args) -> int:
    if args.rev is None:
        reject("usage", "--rev is required")
    current_rows, current_types = load_rows(Source(args.repo, args.rev))
    tags = strict_tags(args.repo)
    if not tags:
        reject("no-tags", "no strict-semver v* tag exists, so there is no release to freeze against (fetch tags)")
    tag = tags[-1]
    exists = subprocess.run(["git", "-C", str(args.repo), "cat-file", "-e", f"{tag}:{CONTRACT}"],
                            capture_output=True, check=False).returncode == 0
    if not exists:
        print("save-formats freeze pass baseline=none")
        return 0
    baseline_rows, baseline_types = parse_rows(parse_canonical(Source(args.repo, tag).read(CONTRACT), f"{tag}:{CONTRACT}"))
    current = {(row.type, row.ram_code, row.rom_code_max): row for row in current_rows}
    for old in baseline_rows:
        now = current.get((old.type, old.ram_code, old.rom_code_max))
        if now is None:
            reject("freeze-mismatch", f"{tag} published {old.label()} {old.id} and the row is gone")
        if now != old:
            reject("freeze-mismatch", f"{tag} published {old}, now {now}")
    for cart_type in baseline_types:
        if cart_type not in current_types:
            reject("freeze-mismatch", f"{tag} listed ${cart_type:02X} in no_battery_types and it is gone")
    print(f"save-formats freeze pass baseline={tag}")
    return 0


def command_check(args, produce: bool) -> int:
    if args.rev is None or args.work is None or (args.runner is None and args.runner_cmd is None):
        reject("usage", "--rev, --work and --runner (or --runner-cmd) are required")
    command = json.loads(args.runner_cmd) if args.runner_cmd is not None else [args.runner]
    if not (isinstance(command, list) and command and all(isinstance(item, str) for item in command)):
        reject("usage", "--runner-cmd must be a JSON list of strings")
    rows, _types = load_rows(Source(args.repo, args.rev))
    if not rows:
        reject("row-missing", "save_formats.rows is empty")
    fixture = load_fixture(ROOT)
    files = check_rows(command, rows, fixture, args.work, produce)
    ids = len({row.id for row in rows})
    if produce:
        print(f"save-formats pass rows={len(rows)} ids={ids} profiles={len(PROFILES)} files={files}")
    else:
        print(f"save-formats print pass rows={len(rows)} ids={ids} profiles={len(PROFILES)}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="print and produced-file legs on both profiles")
    mode.add_argument("--check-print", action="store_true", help="the print leg only (every platform)")
    mode.add_argument("--check-completeness", action="store_true", help="the contract against the core's admitted set")
    mode.add_argument("--freeze", action="store_true", help="append-only against the latest strict v* tag")
    parser.add_argument("--rev", help="the commit to read docs/host-contract.json from")
    parser.add_argument("--repo", type=pathlib.Path, default=ROOT, help="the repository root")
    parser.add_argument("--runner", help="path of gabbaboy-runner")
    parser.add_argument("--runner-cmd", help="the runner as a JSON list (a shim interpreter and script)")
    parser.add_argument("--enumerator", help="path of test_save_format_completeness (run to list admitted cartridges)")
    parser.add_argument("--completeness", type=pathlib.Path, help="a file holding captured enumerator output")
    parser.add_argument("--work", type=pathlib.Path, help="a build-tree directory for the generated ROMs and saves")
    args = parser.parse_args()
    try:
        if args.check_completeness:
            return command_completeness(args)
        if args.freeze:
            return command_freeze(args)
        return command_check(args, produce=args.check)
    except Reject as error:
        print(f"REJECT {error.code}: {error.message}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
