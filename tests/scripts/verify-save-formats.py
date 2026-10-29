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
  --self-test          drives this CLI over private fixture repositories and generated runner shims, one seeded drift per
                       control, each of which must fail with its own REJECT code
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
    raw = source.read(CONTRACT)
    # T-18-28: the table names GabbaBoy's own ids and sizes; it never claims byte interoperability with another
    # emulator (an mGBA save carries a 48-byte footer and a different MBC2 size), so the word has no place in it.
    if b"mgba" in raw.lower():
        reject("interop-claim", f"{CONTRACT} mentions mGBA; the save-format table claims no interoperability with another emulator")
    return parse_rows(parse_canonical(raw, CONTRACT))


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


# ---- self-test: one seeded drift per control (D-20) -------------------------------------------------------------

# A runner shim emulates `--print-save-format` and `--frames` from the contract rows with at most one seeded defect.
# It is a generated Python script started as [sys.executable, "-I", shim] through --runner-cmd.
SHIM = r'''
import json, pathlib, sys
ROWS = json.loads(%(rows)r)
DEFECT = %(defect)r
args = sys.argv[1:]
def opt(name):
    return args[args.index(name) + 1] if name in args else None
rom = pathlib.Path(opt("--rom")).read_bytes()
cart_type, rom_code, ram_code = rom[0x147], rom[0x148], rom[0x149]
profile = opt("--profile") or "dmg"
row = None
for candidate in ROWS:
    limit = candidate["rom_code_max"]
    if (int(candidate["type"], 16) == cart_type and int(candidate["ram_code"], 16) == ram_code
            and (limit is None or rom_code <= int(limit, 16))):
        row = candidate
        break
if "--print-save-format" in args:
    if row is None:
        print("save_format=none bytes=0")
    else:
        identity = row["id"] + ("x" if DEFECT == "cgb-id" and profile == "cgb" else "")
        print("save_format=%%s bytes=%%d" %% (identity, row["bytes"]))
    sys.exit(0)
save_dir = pathlib.Path(opt("--save-dir"))
if row is None:
    if DEFECT == "no-battery-file":
        (save_dir / "rom.sav").write_bytes(bytes(8192))
    sys.exit(0)
image = bytearray(row["bytes"])
if row["ram_bytes"] > 0:
    if cart_type in (5, 6):
        image[:row["ram_bytes"]] = bytes([0xF0]) * row["ram_bytes"]
        image[0] = 0xFA
    else:
        image[0] = 0x5A
if row["rtc_bytes"] > 0:
    image[row["ram_bytes"]:row["ram_bytes"] + 5] = b"GBRT" + bytes([1])
if DEFECT == "short":
    del image[-1]
(save_dir / "rom.sav").write_bytes(bytes(image))
'''


def fabricate_enumeration(rows: list[Row], no_battery: list[int]) -> str:
    """What the in-process enumerator would print for exactly this table: the admitted battery combinations the
    rows describe, plus the no-battery types. A seeded edit of the JSON then disagrees with this output."""
    lines = []
    for row in rows:
        for rom_code in range(0, (0 if row.rom_code_max is None else row.rom_code_max) + 1):
            lines.append(f"admitted type=0x{row.type:02X} ram=0x{row.ram_code:02X} rom=0x{rom_code:02X} battery=1 "
                         f"bytes={row.bytes} rtc={int(row.rtc_bytes > 0)}")
    for cart_type in no_battery:
        lines.append(f"admitted type=0x{cart_type:02X} ram=0x00 rom=0x00 battery=0 bytes=0 rtc=0")
    lines.sort()
    lines.append(f"admitted-done count={len(lines)}")
    return "\n".join(lines) + "\n"


def git(repo: pathlib.Path, *args: str) -> str:
    done = subprocess.run(["git", "-C", str(repo), "-c", "user.name=fixture", "-c", "user.email=fixture@example.invalid",
                           "-c", "commit.gpgsign=false", "-c", "core.hooksPath=/dev/null", *args],
                          capture_output=True, text=True, check=True)
    return done.stdout.strip()


def self_test(repo: pathlib.Path, rev: str | None) -> int:
    """Drives this very CLI with `python -I`. With --rev the seed contract is read from that commit."""
    seed_text = (Source(repo, rev).read(CONTRACT) if rev is not None else (ROOT / CONTRACT).read_bytes()).decode("ascii")
    seed = json.loads(seed_text)
    seed_rows, seed_types = parse_rows(parse_canonical(seed_text.encode("ascii"), CONTRACT))
    enumeration = fabricate_enumeration(seed_rows, seed_types)
    controls = 0
    import tempfile
    script = pathlib.Path(__file__).resolve()

    def dump(value) -> str:
        return json.dumps(value, indent=2, ensure_ascii=True) + "\n"

    def edited(edit) -> str:
        copy = json.loads(seed_text)
        edit(copy)
        return dump(copy)

    def row_of(document: dict, cart_type: str, ram_code: str) -> dict:
        return next(entry for entry in document["save_formats"]["rows"]
                    if entry["type"] == cart_type and entry["ram_code"] == ram_code)

    with tempfile.TemporaryDirectory(prefix="gbb-save-formats-") as temp:
        parent = pathlib.Path(temp)
        counter = 0

        def make_repo(contract: str | None) -> pathlib.Path:
            nonlocal counter
            counter += 1
            fixture = parent / f"repo{counter}"
            fixture.mkdir()
            git(fixture, "init", "-q")
            (fixture / "README").write_bytes(b"fixture\n")
            if contract is not None:
                (fixture / "docs").mkdir()
                (fixture / CONTRACT).write_bytes(contract.encode("ascii"))
            git(fixture, "add", "-A")
            git(fixture, "commit", "-q", "-m", "fixture")
            return fixture

        def commit_contract(fixture: pathlib.Path, contract: str) -> None:
            (fixture / "docs").mkdir(exist_ok=True)
            (fixture / CONTRACT).write_bytes(contract.encode("ascii"))
            git(fixture, "add", "-A")
            git(fixture, "commit", "-q", "-m", "contract")

        def cli(fixture: pathlib.Path, *extra: str) -> subprocess.CompletedProcess:
            return subprocess.run([sys.executable, "-I", str(script), "--repo", str(fixture),
                                   "--rev", git(fixture, "rev-parse", "HEAD"), *extra],
                                  capture_output=True, text=True, timeout=180, check=False)

        def expect_pass(label: str, result: subprocess.CompletedProcess, line: str) -> None:
            nonlocal controls
            if result.returncode != 0 or line not in result.stdout:
                raise SystemExit(f"self-test {label}: expected {line!r}, got {result.stdout.strip()} {result.stderr.strip()[:240]}")
            controls += 1

        def expect_reject(label: str, result: subprocess.CompletedProcess, code: str) -> None:
            nonlocal controls
            if result.returncode == 0 or "save-formats" in result.stdout and " pass" in result.stdout:
                raise SystemExit(f"self-test accepted {label}")
            if f"REJECT {code}:" not in result.stderr:
                raise SystemExit(f"self-test {label}: expected REJECT {code}, got: {result.stderr.strip()[:240]}")
            controls += 1

        enumerator_file = parent / "enumerator.txt"
        enumerator_file.write_bytes(enumeration.encode("ascii"))

        def completeness(contract: str, output: pathlib.Path = enumerator_file) -> subprocess.CompletedProcess:
            return cli(make_repo(contract), "--check-completeness", "--completeness", str(output))

        # completeness and the structural rules
        expect_pass("the real contract against its own enumeration", completeness(seed_text),
                    f"save-formats completeness pass rows={len(seed_rows)}")

        def mgba_size(document: dict) -> None:  # 32,768 B of RAM and a 48 B footer: internally consistent, wrong
            entry = row_of(document, "0x10", "0x03")
            entry.update({"bytes": 32816, "rtc_bytes": 48})
        expect_reject("$10/$03 at 32,816 bytes", completeness(edited(mgba_size)), "size-mismatch")

        def delete_row(document: dict) -> None:
            document["save_formats"]["rows"].remove(row_of(document, "0x1E", "0x05"))
        expect_reject("a deleted row", completeness(edited(delete_row)), "row-missing")

        def add_mbc30(document: dict) -> None:  # $10/$05 is the MBC30 marker, which the core does not admit
            rows = document["save_formats"]["rows"]
            entry = dict(row_of(document, "0x10", "0x03"))
            entry.update({"ram_code": "0x05", "id": "gabbaboy-mbc30-rtc-sram-64k-v1", "bytes": 65557, "ram_bytes": 65536})
            rows.insert(rows.index(row_of(document, "0x10", "0x03")) + 1, entry)
        expect_reject("an admitted-check failure ($10/$05 row)", completeness(edited(add_mbc30)), "row-not-admitted")

        def versioned(document: dict) -> None:
            row_of(document, "0x03", "0x02")["id"] = "gabbaboy-mbc1-sram-8k-v0.3.0"
        expect_reject("a release-versioned id", completeness(edited(versioned)), "id-grammar")

        def uppercase(document: dict) -> None:
            row_of(document, "0x03", "0x02")["id"] = "GabbaBoy-mbc1-sram-8k-v1"
        expect_reject("an uppercase id", completeness(edited(uppercase)), "id-grammar")

        def bad_sum(document: dict) -> None:
            row_of(document, "0x03", "0x02")["bytes"] = 8193
        expect_reject("bytes != ram + rtc", completeness(edited(bad_sum)), "sum-mismatch")

        def two_sizes(document: dict) -> None:
            row_of(document, "0x13", "0x03")["id"] = row_of(document, "0x13", "0x02")["id"]
        expect_reject("one id with two sizes", completeness(edited(two_sizes)), "id-size-conflict")

        def swapped(document: dict) -> None:
            rows = document["save_formats"]["rows"]
            rows[0], rows[1] = rows[1], rows[0]
        expect_reject("rows out of order", completeness(edited(swapped)), "row-order")

        expect_reject("tab-indented JSON", completeness(json.dumps(seed, indent="\t") + "\n"), "non-canonical")
        expect_reject("sorted keys", completeness(json.dumps(seed, indent=2, sort_keys=True) + "\n"), "non-canonical")
        expect_reject("an interoperability claim",
                      completeness(edited(lambda d: d["exit_codes"][0].update(meaning="Clean exit; saves are mGBA compatible"))),
                      "interop-claim")
        expect_reject("an empty rows list", completeness(edited(lambda d: d["save_formats"].update(rows=[]))), "row-missing")

        broken = parent / "enumerator-broken.txt"
        broken.write_bytes(enumeration.replace("admitted-done count=", "admitted-done count=9").encode("ascii"))
        expect_reject("an enumerator count that does not match", completeness(seed_text, broken), "enumerator-output")

        # produced files, through a runner shim with exactly one seeded defect
        def shim_run(defect: str | None) -> subprocess.CompletedProcess:
            fixture = make_repo(seed_text)
            shim = parent / f"shim-{defect or 'good'}.py"
            shim.write_bytes((SHIM % {"rows": json.dumps(seed["save_formats"]["rows"]), "defect": defect}).encode("ascii"))
            return cli(fixture, "--check", "--runner-cmd", json.dumps([sys.executable, "-I", str(shim)]),
                       "--work", str(parent / f"work-{defect or 'good'}"))

        expect_pass("the shim without a defect", shim_run(None),
                    f"save-formats pass rows={len(seed_rows)} ids={len({row.id for row in seed_rows})} profiles=2 files={2 * len(seed_rows)}")
        expect_reject("a .sav one byte short", shim_run("short"), "file-size")
        expect_reject("a different id under cgb", shim_run("cgb-id"), "profile-id-mismatch")
        expect_reject("a .sav for a no-battery cartridge", shim_run("no-battery-file"), "no-battery-file")

        # the freeze against the latest strict release tag
        def tagged_repo(tags: dict[str, str | None], current: str) -> pathlib.Path:
            fixture = make_repo(None)
            for tag, contract in tags.items():
                if contract is not None:
                    commit_contract(fixture, contract)
                git(fixture, "tag", tag)
                if contract is not None:
                    git(fixture, "rm", "-q", "-r", "docs")
                    git(fixture, "commit", "-q", "-m", "drop")
            commit_contract(fixture, current)
            return fixture

        def renamed(document: dict) -> None:
            row_of(document, "0x03", "0x02")["id"] = "gabbaboy-mbc1-sram-8k-v2"

        def gone(document: dict) -> None:
            document["save_formats"]["rows"].pop()

        def appended(document: dict) -> None:
            document["save_formats"]["rows"].append(
                {"type": "0x1E", "ram_code": "0x06", "rom_code_max": None, "id": "gabbaboy-mbc5-sram-256k-v1",
                 "bytes": 262144, "ram_bytes": 262144, "rtc_bytes": 0})

        expect_reject("a repository with no tag", cli(make_repo(seed_text), "--freeze"), "no-tags")
        stray = make_repo(seed_text)
        git(stray, "tag", "v0.1")
        expect_reject("only a stray non-strict tag", cli(stray, "--freeze"), "no-tags")
        expect_pass("a tag whose tree lacks the file", cli(tagged_repo({"v9.9.9": None}, seed_text), "--freeze"),
                    "save-formats freeze pass baseline=none")
        expect_pass("an unchanged table", cli(tagged_repo({"v9.9.9": seed_text}, seed_text), "--freeze"),
                    "save-formats freeze pass baseline=v9.9.9")
        expect_pass("an appended row", cli(tagged_repo({"v9.9.9": seed_text}, edited(appended)), "--freeze"),
                    "save-formats freeze pass baseline=v9.9.9")
        expect_reject("a changed id against the release", cli(tagged_repo({"v9.9.9": seed_text}, edited(renamed)), "--freeze"),
                      "freeze-mismatch")
        expect_reject("a removed row against the release", cli(tagged_repo({"v9.9.9": seed_text}, edited(gone)), "--freeze"),
                      "freeze-mismatch")
        # v9.10.0 sorts after v9.9.9 numerically (not as text) and its tree lacks the file, so the older tag's
        # baseline must not be consulted even though the current table no longer matches it.
        expect_pass("numeric tag order", cli(tagged_repo({"v9.9.9": seed_text, "v9.10.0": None}, edited(renamed)), "--freeze"),
                    "save-formats freeze pass baseline=none")
    print(f"save-formats self-test pass controls={controls}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="print and produced-file legs on both profiles")
    mode.add_argument("--check-print", action="store_true", help="the print leg only (every platform)")
    mode.add_argument("--check-completeness", action="store_true", help="the contract against the core's admitted set")
    mode.add_argument("--freeze", action="store_true", help="append-only against the latest strict v* tag")
    mode.add_argument("--self-test", action="store_true", help="seeded drift controls (optionally --rev/--repo for the seed)")
    parser.add_argument("--rev", help="the commit to read docs/host-contract.json from")
    parser.add_argument("--repo", type=pathlib.Path, default=ROOT, help="the repository root")
    parser.add_argument("--runner", help="path of gabbaboy-runner")
    parser.add_argument("--runner-cmd", help="the runner as a JSON list (a shim interpreter and script)")
    parser.add_argument("--enumerator", help="path of test_save_format_completeness (run to list admitted cartridges)")
    parser.add_argument("--completeness", type=pathlib.Path, help="a file holding captured enumerator output")
    parser.add_argument("--work", type=pathlib.Path, help="a build-tree directory for the generated ROMs and saves")
    args = parser.parse_args()
    try:
        if args.self_test:
            return self_test(args.repo, args.rev)
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
