#!/usr/bin/env python3
"""End-to-end host-mode scenarios for gabbaboy-runner (Phase 18, HOST-01).

    python3 -I test_host_mode.py --runner PATH --work DIR --scenario NAME

Each scenario starts from an empty directory under --work, drives the real runner process, and prints
`host-mode scenario=<name> pass` or `FAIL <name>: <why>` (exit 1). Assertions are explicit checks, never
`assert`, so the harness behaves identically under any interpreter flags; python -O is refused.
"""
from __future__ import annotations

import argparse
import importlib.util
import os
import re
import shutil
import stat
import sys
import tempfile
from pathlib import Path

if not __debug__:
    raise SystemExit("test_host_mode refuses to run under python -O")

_spec = importlib.util.spec_from_file_location(
    "host_fixture", Path(__file__).resolve().with_name("host_fixture.py"))
host_fixture = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(host_fixture)

RUN_TIMEOUT = 50.0  # below the 60 s CTest bound so a hang fails here with a reason
MBC1_RAM_BATTERY = 0x03
MBC5_RAM_BATTERY = 0x1B
RAM_8K = 0x02


class Failure(Exception):
    pass


def require(condition: bool, why: str) -> None:
    if not condition:
        raise Failure(why)


def fresh_dir(path: Path) -> Path:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True)
    return path


def run(runner: str, rom: Path, save_dir: Path, frames: int, cwd: Path) -> tuple[int, str, str]:
    return host_fixture.run_runner(
        runner, ["--rom", str(rom), "--save-dir", str(save_dir), "--frames", str(frames)],
        str(cwd), RUN_TIMEOUT)


def forbid_work_path(work: Path, *streams: str) -> None:
    """Privacy prohibition (T-18-05): no diagnostic may echo the caller's absolute path."""
    for needle in {str(work), str(work.resolve())}:
        for stream in streams:
            require(needle not in stream, "diagnostic leaked the absolute work directory path")


def listing(save_dir: Path) -> list[str]:
    return sorted(entry.name for entry in save_dir.iterdir())


def expect_clean_exit(code: int, stderr: str, frames: int) -> None:
    require(code == 0, f"exit {code}, expected 0: {stderr.strip()!r}")
    ready = stderr.find("gbb-host: ready")
    exit_line = re.search(
        rf"gbb-host: exit status=clean reason=frames stopped_at_frame={frames} "
        r"flush=(written|unchanged)\b", stderr)
    require(ready >= 0, "missing 'gbb-host: ready'")
    require(exit_line is not None, "missing the clean exit line with flush=(written|unchanged)")
    require(ready < exit_line.start(), "'gbb-host: ready' must precede the exit line")


def scenario_continuation(runner: str, work: Path) -> None:
    """XFER-002: a second process imports the first run's raw .sav, so the guest counter advances."""
    base = fresh_dir(work)
    rom = base / "counter.gb"
    rom.write_bytes(host_fixture.build_rom("counter", MBC1_RAM_BATTERY, RAM_8K))
    saves = fresh_dir(base / "saves")
    sav = saves / "counter.sav"

    code, out, err = run(runner, rom, saves, 60, base)
    expect_clean_exit(code, err, 60)
    require(sav.is_file(), "first run did not publish counter.sav")
    first = sav.read_bytes()
    require(len(first) == 8192, f"first image is {len(first)} bytes, expected 8192")
    require(first[0] == 0x01, f"first run counter is {first[0]:#04x}, expected 0x01")
    require(listing(saves) == ["counter.sav"], f"unexpected directory entries {listing(saves)}")
    forbid_work_path(base, out, err)

    # An import-ignoring runner would start from fresh RAM and write 0x01 again; only an import of the
    # first run's bytes gives exactly 0x02 here.
    code, out, err = run(runner, rom, saves, 60, base)
    expect_clean_exit(code, err, 60)
    second = sav.read_bytes()
    require(len(second) == 8192, f"second image is {len(second)} bytes")
    require(second[0] == 0x02, f"second run counter is {second[0]:#04x}, expected 0x02 (import lost)")
    require(second[1:] == first[1:], "second run altered bytes the guest never touched")
    require(listing(saves) == ["counter.sav"], f"temp file left behind: {listing(saves)}")
    forbid_work_path(base, out, err)

    preload_dir = fresh_dir(base / "preload")
    preload = bytearray((i * 7 + 3) & 0xFF for i in range(8192))
    preload[0] = 0x41
    (preload_dir / "counter.sav").write_bytes(bytes(preload))
    code, out, err = run(runner, rom, preload_dir, 60, base)
    expect_clean_exit(code, err, 60)
    result = (preload_dir / "counter.sav").read_bytes()
    require(len(result) == 8192, f"preloaded image became {len(result)} bytes")
    require(result[0] == 0x42, f"preloaded counter is {result[0]:#04x}, expected 0x42")
    require(result[1:] == bytes(preload[1:]), "preloaded bytes were not preserved")
    require(listing(preload_dir) == ["counter.sav"], f"temp file left behind: {listing(preload_dir)}")
    forbid_work_path(base, out, err)


def expect_refusal(code: int, stdout: str, stderr: str, reason: str, *forbidden: str) -> None:
    """A start-up refusal: exit 2, its own `gbb-host: refused reason=` token, no frame ever ran."""
    require(code == 2, f"exit {code}, expected 2: {stderr.strip()!r}")
    require(f"gbb-host: refused reason={reason}\n" in stderr,
            f"missing 'gbb-host: refused reason={reason}': {stderr.strip()!r}")
    require("gbb-host: ready" not in stderr, "a refused run must not print 'gbb-host: ready'")
    for token in forbidden:
        require(token not in stderr, f"unexpected {token!r} in a {reason} refusal")


def scenario_rom_max(runner: str, work: Path) -> None:
    """D-04: the host ROM bound is the core's 8 MiB, not the 32 KiB acceptance cap."""
    base = fresh_dir(work)
    rom = base / "maxrom.gb"
    saves = fresh_dir(base / "saves")
    try:
        data = host_fixture.build_rom("write5a", MBC5_RAM_BATTERY, RAM_8K, rom_code=8)
        require(len(data) == 8 * 1024 * 1024, "fixture is not exactly 8 MiB")
        rom.write_bytes(data)
        code, out, err = run(runner, rom, saves, 2, base)
        expect_clean_exit(code, err, 2)
        image = (saves / "maxrom.sav").read_bytes()
        require(len(image) == 8192, f"image is {len(image)} bytes, expected 8192")
        require(image[0] == 0x5A, f"byte 0 is {image[0]:#04x}, expected 0x5a")
        require(listing(saves) == ["maxrom.sav"], f"unexpected directory entries {listing(saves)}")
        forbid_work_path(base, out, err)
    finally:
        rom.unlink(missing_ok=True)  # an 8 MiB image has no business surviving the scenario


def scenario_rom_oversize(runner: str, work: Path) -> None:
    """D-04: one byte over 8 MiB is refused by the host (rom-size) before the core ever sees it."""
    base = fresh_dir(work)
    rom = base / "oversize.gb"
    saves = fresh_dir(base / "saves")
    try:
        rom.write_bytes(host_fixture.build_rom("write5a", MBC5_RAM_BATTERY, RAM_8K, rom_code=8) + b"\x00")
        require(rom.stat().st_size == 8 * 1024 * 1024 + 1, "fixture is not exactly 8 MiB + 1")
        code, out, err = run(runner, rom, saves, 2, base)
        # rom-unsupported would mean the core, not the host cap, refused the image.
        expect_refusal(code, out, err, "rom-size", "reason=rom-unsupported")
        require(listing(saves) == [], f"refused run changed the save directory: {listing(saves)}")
        forbid_work_path(base, out, err)
    finally:
        rom.unlink(missing_ok=True)


def scenario_rom_unreadable(runner: str, work: Path) -> None:
    """A missing ROM is rom-unreadable, never a crash and never a created save."""
    base = fresh_dir(work)
    saves = fresh_dir(base / "saves")
    code, out, err = run(runner, base / "absent.gb", saves, 2, base)
    expect_refusal(code, out, err, "rom-unreadable", "reason=rom-size", "reason=rom-unsupported")
    require(listing(saves) == [], f"refused run changed the save directory: {listing(saves)}")
    forbid_work_path(base, out, err)

STEM_TOKENS = ("stem-empty", "stem-leading-dot", "stem-control", "stem-del", "stem-backslash",
               "stem-bad-utf8", "stem-too-long")


def snapshot(save_dir: Path) -> dict[str, tuple[int, bytes]]:
    """Every entry's name, mtime and bytes, plus the directory's own mtime under the key ''."""
    state: dict[str, tuple[int, bytes]] = {"": (save_dir.stat().st_mtime_ns, b"")}
    for entry in sorted(save_dir.iterdir()):
        state[entry.name] = (entry.stat().st_mtime_ns, entry.read_bytes())
    return state


def scenario_stem_refusal(runner: str, work: Path) -> None:
    """D-07 end to end: a hostile ROM name is refused with its own stem token before any filesystem
    access, the save directory is byte-for-byte unchanged, and the stem is never rewritten into a
    different accepted name (a rewrite of `a\\b` would create `a_b.sav`)."""
    base = fresh_dir(work)
    roms = fresh_dir(base / "roms")
    saves = fresh_dir(base / "saves")
    (saves / "keep.sav").write_bytes(bytes(range(256)) * 32)
    rom_bytes = host_fixture.build_rom("counter", MBC1_RAM_BATTERY, RAM_8K)
    (roms / "dir").mkdir()

    # name is raw bytes; os.fsdecode keeps it byte-exact on POSIX (surrogateescape) for argv.
    cases = [
        ("stem-empty", b"dir/"),
        ("stem-leading-dot", b".gb"),
        ("stem-leading-dot", b"..gb"),
        ("stem-control", b"a\x01b.gb"),
        ("stem-control", b"a\x1fb.gb"),
        ("stem-del", b"a\x7fb.gb"),
        ("stem-backslash", b"a\\b.gb"),
        ("stem-bad-utf8", b"a\xc0\x80b.gb"),
        ("stem-bad-utf8", b"a\xed\xa0\x80b.gb"),
        ("stem-bad-utf8", b"a\xf4\x90\x80\x80b.gb"),
        ("stem-bad-utf8", b"a\xe2\x82.gb"),
        ("stem-too-long", b"a" * 201 + b".gb"),
    ]
    created = 0
    for token, name in cases:
        rom_path = os.path.join(os.fsencode(str(roms)), name)
        if not name.endswith(b"/"):
            try:
                with open(rom_path, "wb") as handle:
                    handle.write(rom_bytes)
                created += 1
            except OSError:
                # macOS APFS refuses non-UTF-8 names. Stem validation precedes any filesystem
                # access, so the refusal must not depend on the file existing.
                pass
        before = snapshot(saves)
        code, out, err = host_fixture.run_runner(
            runner, ["--rom", os.fsdecode(rom_path), "--save-dir", str(saves), "--frames", "1"],
            str(base), RUN_TIMEOUT)
        label = f"{token} for {name!r}"
        expect_refusal(code, out, err, token, *(f"reason={other}" for other in STEM_TOKENS if other != token))
        require(snapshot(saves) == before, f"{label}: the save directory changed")
        forbid_work_path(base, out, err)
    require(created >= 7, f"only {created} hostile ROM files could be created; the scenario lost its teeth")


def scenario_platform_gate(runner: str, work: Path) -> None:
    """D-05: `--save-dir` mode is refused on Windows before any filesystem access, and the gate does
    not fire on POSIX."""
    base = fresh_dir(work)
    saves = fresh_dir(base / "saves")
    rom = Path(__file__).resolve().parents[2] / "fixtures" / "mbc1-continuation" / "continuation.gb"
    require(rom.is_file(), "fixtures/mbc1-continuation/continuation.gb is missing")
    code, out, err = run(runner, rom, saves, 2, base)
    if os.name == "nt":
        expect_refusal(code, out, err, "windows-unsupported")
        require(listing(saves) == [], f"refused run changed the save directory: {listing(saves)}")
    else:
        expect_clean_exit(code, err, 2)
        require("windows-unsupported" not in err, "the Windows gate fired on POSIX")
        require(listing(saves) == ["continuation.sav"], f"unexpected directory entries {listing(saves)}")
    forbid_work_path(base, out, err)


def scenario_grammar_empty_value(runner: str, work: Path) -> None:
    """D-02 empty-value: an empty `--rom` or `--save-dir` operand is its own token. CMake cannot pass an
    empty list element, so this one grammar case runs here instead of in a CTest command."""
    base = fresh_dir(work)
    for args in (["--rom", "", "--save-dir", "d"], ["--rom", "r", "--save-dir", ""],
                 ["--rom", "r", "--save-dir", "d", "--frames", ""]):
        code, out, err = host_fixture.run_runner(runner, args, str(base), RUN_TIMEOUT)
        require(code == 2, f"exit {code}, expected 2 for {args}: {err.strip()!r}")
        require("invalid-arguments: reason=empty-value\n" in err,
                f"missing 'invalid-arguments: reason=empty-value' for {args}: {err.strip()!r}")
        require("gbb-host: ready" not in err, "a refused run must not print 'gbb-host: ready'")
    require(listing(base) == [], "a grammar refusal touched the filesystem")


FLUSH_LINE = re.compile(
    r"gbb-host: flush reason=(generation|rtc-drift|final) frame=(\d+) result=(written|unchanged|failed)"
    r"(?: stage=(\S+))?")


def flush_lines(stderr: str) -> list[tuple[str, int, str]]:
    return [(m.group(1), int(m.group(2)), m.group(3)) for m in FLUSH_LINE.finditer(stderr)]


def scenario_periodic_flush(runner: str, work: Path) -> None:
    """D-11 end to end: a guest write is flushed by the generation trigger long before the final
    flush, the image is not rewritten when nothing changed, and the final flush is identical."""
    base = fresh_dir(work)
    rom = base / "write5a.gb"
    rom.write_bytes(host_fixture.build_rom("write5a", MBC1_RAM_BATTERY, RAM_8K))
    saves = fresh_dir(base / "saves")
    code, out, err = run(runner, rom, saves, 120, base)
    expect_clean_exit(code, err, 120)
    flushes = flush_lines(err)
    generation = [f for f in flushes if f[0] == "generation"]
    require(len(generation) == 1, f"expected one generation flush, got {flushes}")
    reason, frame, result = generation[0]
    require(16 <= frame <= 24, f"generation flush at frame {frame}, expected 16..24")
    require(result == "written", f"generation flush result {result}, expected written")
    final = [f for f in flushes if f[0] == "final"]
    require(final == [("final", 120, "unchanged")], f"final flush {final}, expected unchanged at 120")
    require("flush=unchanged" in err, "exit line must report flush=unchanged")
    image = (saves / "write5a.sav").read_bytes()
    require(len(image) == 8192 and image[0] == 0x5A, f"image is {len(image)} bytes, byte0 {image[:1]!r}")
    require(listing(saves) == ["write5a.sav"], f"unexpected directory entries {listing(saves)}")
    forbid_work_path(base, out, err)


def scenario_first_write(runner: str, work: Path) -> None:
    """D-11 first write: a battery cart with an absent .sav creates it at the latest at the final
    flush, even when the guest never touched cartridge RAM."""
    base = fresh_dir(work)
    rom = base / "idle.gb"
    rom.write_bytes(host_fixture.build_rom("idle", MBC1_RAM_BATTERY, RAM_8K))
    saves = fresh_dir(base / "saves")
    code, out, err = run(runner, rom, saves, 2, base)
    expect_clean_exit(code, err, 2)
    require(flush_lines(err) == [("final", 2, "written")], f"flushes {flush_lines(err)}")
    require("flush=written" in err, "exit line must report flush=written")
    size = (saves / "idle.sav").stat().st_size
    require(size == 8192, f".sav is {size} bytes, expected 8192")
    forbid_work_path(base, out, err)


def scenario_idempotent_rerun(runner: str, work: Path) -> None:
    """HOST-01: a second run that changes nothing leaves the .sav inode and mtime alone."""
    base = fresh_dir(work)
    rom = base / "idle.gb"
    rom.write_bytes(host_fixture.build_rom("idle", MBC1_RAM_BATTERY, RAM_8K))
    saves = fresh_dir(base / "saves")
    code, out, err = run(runner, rom, saves, 4, base)
    expect_clean_exit(code, err, 4)
    require("flush=written" in err, "first run must report flush=written")
    first = (saves / "idle.sav").stat()
    code, out, err = run(runner, rom, saves, 4, base)
    expect_clean_exit(code, err, 4)
    require("flush=unchanged" in err, f"second run must report flush=unchanged: {err.strip()!r}")
    second = (saves / "idle.sav").stat()
    require(second.st_ino == first.st_ino, "the .sav inode changed on an unchanged rerun")
    require(second.st_mtime_ns == first.st_mtime_ns, "the .sav mtime changed on an unchanged rerun")
    require(listing(saves) == ["idle.sav"], f"unexpected directory entries {listing(saves)}")
    forbid_work_path(base, out, err)


def scenario_sweep(runner: str, work: Path) -> None:
    """D-10: only entries with the exact prefix `.<stem>.sav.tmp-` are swept, links are never
    followed, the sweep runs after every refusal check and before the first frame."""
    base = fresh_dir(work)
    rom = base / "game.gb"
    rom.write_bytes(host_fixture.build_rom("idle", MBC1_RAM_BATTERY, RAM_8K))
    saves = fresh_dir(base / "saves")
    outside = base / "outside.txt"
    outside.write_bytes(b"keep me")
    stale = [".game.sav.tmp-1-0", ".game.sav.tmp-99-3"]
    near = [".game.sav.tmp", "game.sav.tmp-1", ".other.sav.tmp-1"]
    (saves / stale[0]).write_bytes(b"stale")
    os.symlink(str(outside), str(saves / stale[1]))
    for name in near:
        (saves / name).write_bytes(b"near")

    # A refused start (short .sav) must leave every pre-existing temp in place.
    (saves / "game.sav").write_bytes(b"\x00" * 8191)
    before = snapshot(saves)
    code, out, err = run(runner, rom, saves, 1, base)
    expect_refusal(code, out, err, "save-size")
    require("sweep removed" not in err, "a refused start must not sweep")
    require(snapshot(saves) == before, "a refused run changed the save directory")
    require(os.path.islink(saves / stale[1]), "the symlink temp was removed by a refused run")
    (saves / "game.sav").unlink()

    code, out, err = run(runner, rom, saves, 1, base)
    expect_clean_exit(code, err, 1)
    require("gbb-host: sweep removed=2\n" in err, f"missing 'sweep removed=2': {err.strip()!r}")
    require(err.find("gbb-host: sweep") < err.find("gbb-host: ready"), "the sweep must precede ready")
    for name in stale:
        require(not os.path.lexists(saves / name), f"stale temp {name} survived the sweep")
    require(outside.read_bytes() == b"keep me", "the sweep followed a symlink and touched its target")
    for name in near:
        require((saves / name).is_file(), f"near-miss {name} was removed")
    require(listing(saves) == sorted(near + ["game.sav"]), f"unexpected entries {listing(saves)}")
    forbid_work_path(base, out, err)


MBC3_TIMER_RAM_BATTERY = 0x10
RAM_32K = 0x03


def scenario_rtc_final_compare(runner: str, work: Path) -> None:
    """D-12: the RTC ticks only while the runner runs. An MBC3+RTC cart that writes nothing still gets
    its drifted clock persisted by the final export-and-compare, and a second run continues from the
    persisted clock, never from the file's mtime or the wall clock."""
    base = fresh_dir(work)
    rom = base / "clock.gb"
    rom.write_bytes(host_fixture.build_rom("idle", MBC3_TIMER_RAM_BATTERY, RAM_32K))
    saves = fresh_dir(base / "saves")
    sav = saves / "clock.sav"

    code, out, err = run(runner, rom, saves, 120, base)
    expect_clean_exit(code, err, 120)
    require(flush_lines(err) == [("final", 120, "written")], f"first run flushes {flush_lines(err)}")
    first = sav.read_bytes()
    require(len(first) == 32789, f"first image is {len(first)} bytes, expected 32789")
    forbid_work_path(base, out, err)

    # Age the file by a day: a runner that caught the clock up from mtime would jump far ahead.
    old = sav.stat().st_mtime - 86400
    os.utime(sav, (old, old))
    code, out, err = run(runner, rom, saves, 120, base)
    expect_clean_exit(code, err, 120)
    require(flush_lines(err) == [("final", 120, "written")],
            f"second run must rewrite an RTC-only change: {flush_lines(err)}")
    second = sav.read_bytes()
    require(len(second) == 32789, f"second image is {len(second)} bytes")
    require(second[:32768] == first[:32768], "SRAM bytes changed although the guest never wrote")
    require(second[32768:] != first[32768:], "the 21-byte RTC block did not change between the runs")
    require(listing(saves) == ["clock.sav"], f"unexpected directory entries {listing(saves)}")
    forbid_work_path(base, out, err)


# ---- Hostile save directory, import and --rom shapes (D-06, D-08, D-30) --------------------------------------
BOUND = 10.0  # a FIFO or special file must be refused well inside this; a blocked open is killed here
IMPORT_TOKENS = ("save-size", "save-rtc-block", "save-symlink", "save-not-regular")
CLOCK_WANT = 32768 + 21  # MBC3+TIMER+RAM+BATTERY with 32 KiB of RAM: SRAM plus the RTC block


def run_bounded(runner: str, rom: Path, save_dir: Path, frames: int, cwd: Path) -> tuple[int, str, str]:
    try:
        return host_fixture.run_runner(
            runner, ["--rom", str(rom), "--save-dir", str(save_dir), "--frames", str(frames)],
            str(cwd), BOUND)
    except TimeoutError as error:
        raise Failure(f"blocked: the runner did not return within {BOUND} s ({error})") from error


def entry_state(path: Path) -> tuple[int, int, int, int, object]:
    """lstat identity (type, inode, mtime, size) plus bytes or link target. A FIFO or directory is
    never opened, so inspecting one cannot block."""
    info = os.lstat(path)
    content: object = None
    if stat.S_ISREG(info.st_mode):
        content = path.read_bytes()
    elif stat.S_ISLNK(info.st_mode):
        content = os.readlink(path)
    return (stat.S_IFMT(info.st_mode), info.st_ino, info.st_mtime_ns, info.st_size, content)


def clock_rom(base: Path) -> Path:
    rom = base / "clock.gb"
    rom.write_bytes(host_fixture.build_rom("idle", MBC3_TIMER_RAM_BATTERY, RAM_32K))
    return rom


def valid_clock_image(runner: str, base: Path, rom: Path) -> bytes:
    """A real exact-size image taken from a prior run, so the RTC block is one the core wrote."""
    seed = fresh_dir(base / "seed")
    code, out, err = run_bounded(runner, rom, seed, 4, base)
    expect_clean_exit(code, err, 4)
    image = (seed / "clock.sav").read_bytes()
    require(len(image) == CLOCK_WANT, f"seed image is {len(image)} bytes, expected {CLOCK_WANT}")
    return image


def import_refusal(runner: str, work: Path, token: str, prepare) -> None:
    """Shared body of the D-08 refusals: the hostile entry is refused with its own token before the
    first frame, and its lstat identity, content and the directory listing are unchanged."""
    base = fresh_dir(work)
    rom = clock_rom(base)
    image = valid_clock_image(runner, base, rom)
    saves = fresh_dir(base / "saves")
    sav = saves / "clock.sav"
    prepare(base, saves, sav, image)
    before_entry, before_listing = entry_state(sav), listing(saves)
    side = [entry_state(p) for p in sorted(base.glob("outside*"))]
    code, out, err = run_bounded(runner, rom, saves, 1, base)
    expect_refusal(code, out, err, token,
                   *(f"reason={other}" for other in IMPORT_TOKENS if other != token))
    require("sweep removed" not in err, "a refused start must not sweep")
    require(entry_state(sav) == before_entry, f"{token}: the .sav entry changed")
    require(listing(saves) == before_listing, f"{token}: the directory listing changed")
    require([entry_state(p) for p in sorted(base.glob("outside*"))] == side,
            f"{token}: a file outside the save directory changed")
    forbid_work_path(base, out, err)


def size_scenario(token: str, size: int):
    def scenario(runner: str, work: Path) -> None:
        def prepare(base: Path, saves: Path, sav: Path, image: bytes) -> None:
            if size > 1024 * 1024:
                with open(sav, "wb") as handle:
                    handle.truncate(size)  # sparse: the runner must refuse on size alone
            else:
                sav.write_bytes((image * 2)[:size])
        import_refusal(runner, work, token, prepare)
    return scenario


def prepare_bad_rtc(base: Path, saves: Path, sav: Path, image: bytes) -> None:
    broken = bytearray(image)
    require(bytes(broken[32768:32772]) == b"GBRT", "the seed image has no GBRT block to corrupt")
    broken[32768] ^= 0xFF  # the exact size is right; only the RTC magic is wrong
    sav.write_bytes(bytes(broken))


def prepare_symlink(base: Path, saves: Path, sav: Path, image: bytes) -> None:
    (base / "outside.bin").write_bytes(image)  # a valid-size file a following reader would accept
    os.symlink(str(base / "outside.bin"), str(sav))


def prepare_dangling(base: Path, saves: Path, sav: Path, image: bytes) -> None:
    os.symlink(str(base / "outside-absent.bin"), str(sav))


def scenario_import_exact(runner: str, work: Path) -> None:
    """The positive control for the size rows: an exact-size image from a prior run is imported."""
    base = fresh_dir(work)
    rom = clock_rom(base)
    image = valid_clock_image(runner, base, rom)
    saves = fresh_dir(base / "saves")
    (saves / "clock.sav").write_bytes(image)
    code, out, err = run_bounded(runner, rom, saves, 4, base)
    expect_clean_exit(code, err, 4)
    require("sweep removed=0" in err, "the sweep line is missing")
    result = (saves / "clock.sav").read_bytes()
    require(len(result) == CLOCK_WANT, f"result is {len(result)} bytes")
    require(result[:32768] == image[:32768], "SRAM bytes changed although the guest never wrote")
    require(listing(saves) == ["clock.sav"], f"unexpected directory entries {listing(saves)}")
    forbid_work_path(base, out, err)


def prepare_fifo(base: Path, saves: Path, sav: Path, image: bytes) -> None:
    os.mkfifo(sav)


def prepare_directory(base: Path, saves: Path, sav: Path, image: bytes) -> None:
    sav.mkdir()


def scenario_import_stray_nobattery(runner: str, work: Path) -> None:
    """D-08: a no-battery cart never opens, reads, writes or counts a stray `{stem}.sav`, whatever its
    shape. A FIFO would block an opener, and an importing runner would refuse the 100-byte file."""
    base = fresh_dir(work)
    rom = base / "stray.gb"
    rom.write_bytes(host_fixture.build_rom("write5a", 0x1A, RAM_8K))  # MBC5+RAM, no battery
    outside = base / "outside.bin"
    outside.write_bytes(b"outside bytes")
    for shape in ("regular", "fifo", "symlink"):
        saves = fresh_dir(base / f"saves-{shape}")
        sav = saves / "stray.sav"
        if shape == "regular":
            sav.write_bytes(bytes(range(100)))
        elif shape == "fifo":
            os.mkfifo(sav)
        else:
            os.symlink(str(outside), str(sav))
        before, before_listing, before_outside = entry_state(sav), listing(saves), entry_state(outside)
        code, out, err = run_bounded(runner, rom, saves, 20, base)
        label = f"{shape} stray"
        require(code == 0, f"{label}: exit {code}, expected 0: {err.strip()!r}")
        require("gbb-host: ready" in err, f"{label}: missing 'gbb-host: ready'")
        require("gbb-host: exit status=clean reason=frames stopped_at_frame=20 flush=none" in err,
                f"{label}: missing the clean exit line with flush=none: {err.strip()!r}")
        for token in IMPORT_TOKENS:
            require(f"reason={token}" not in err, f"{label}: the stray was imported ({token})")
        require(entry_state(sav) == before, f"{label}: the stray entry changed")
        require(entry_state(outside) == before_outside, f"{label}: the symlink target changed")
        require(listing(saves) == before_listing, f"{label}: the directory listing changed")
        forbid_work_path(base, out, err)


def scenario_savedir_missing(runner: str, work: Path) -> None:
    """D-06: the save directory is never created."""
    base = fresh_dir(work)
    rom = base / "idle.gb"
    rom.write_bytes(host_fixture.build_rom("idle", MBC1_RAM_BATTERY, RAM_8K))
    missing = base / "absent"
    before = listing(base)
    code, out, err = run_bounded(runner, rom, missing, 1, base)
    expect_refusal(code, out, err, "save-dir-missing", "reason=save-dir-not-directory")
    require(not os.path.lexists(missing), "the runner created the missing save directory")
    require(listing(base) == before, "a refused run changed the work directory")
    forbid_work_path(base, out, err)


def scenario_savedir_not_directory(runner: str, work: Path) -> None:
    """D-06: a regular file passed as the save directory is its own refusal and is left alone."""
    base = fresh_dir(work)
    rom = base / "idle.gb"
    rom.write_bytes(host_fixture.build_rom("idle", MBC1_RAM_BATTERY, RAM_8K))
    not_dir = base / "notadir"
    not_dir.write_bytes(b"not a directory")
    before, before_listing = entry_state(not_dir), listing(base)
    code, out, err = run_bounded(runner, rom, not_dir, 1, base)
    expect_refusal(code, out, err, "save-dir-not-directory", "reason=save-dir-missing")
    require(entry_state(not_dir) == before, "the file passed as --save-dir changed")
    require(listing(base) == before_listing, "a refused run changed the work directory")
    forbid_work_path(base, out, err)


def scenario_savedir_symlink_path(runner: str, work: Path) -> None:
    """D-06: a symlink anywhere in the save-dir path is allowed and resolved once. macOS `/tmp` is
    one; an explicit symlink covers every other POSIX host."""
    base = fresh_dir(work)
    rom = base / "idle.gb"
    rom.write_bytes(host_fixture.build_rom("idle", MBC1_RAM_BATTERY, RAM_8K))

    real = fresh_dir(base / "real")
    link = base / "link"
    os.symlink(str(real), str(link))
    code, out, err = run_bounded(runner, rom, link, 2, base)
    expect_clean_exit(code, err, 2)
    require((real / "idle.sav").is_file(), "the .sav was not written inside the real directory")
    require(os.path.islink(link), "the save-dir symlink was replaced")
    forbid_work_path(base, out, err)

    tmp = Path(tempfile.mkdtemp(prefix="gbb-host-", dir="/tmp"))
    try:
        code, out, err = run_bounded(runner, rom, tmp, 2, base)
        expect_clean_exit(code, err, 2)
        require((Path(os.path.realpath(tmp)) / "idle.sav").is_file(), "no .sav under the /tmp save dir")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def rom_special_scenario(kind: str):
    def scenario(runner: str, work: Path) -> None:
        """D-30: a FIFO or directory passed as --rom is refused as rom-not-regular, never blocks, and is
        never mistaken for an unreadable or oversize file."""
        base = fresh_dir(work)
        holder = fresh_dir(base / f"rom-{kind}")
        rom = holder / "game.gb"  # no trailing slash, so the stem `game` is valid
        if kind == "fifo":
            os.mkfifo(rom)
        else:
            rom.mkdir()
        saves = fresh_dir(base / "saves")
        before = entry_state(rom)
        code, out, err = run_bounded(runner, rom, saves, 1, base)
        expect_refusal(code, out, err, "rom-not-regular", "reason=rom-unreadable", "reason=rom-size")
        require(entry_state(rom) == before, f"the {kind} ROM entry changed")
        require(stat.S_IFMT(os.lstat(rom).st_mode) == (stat.S_IFIFO if kind == "fifo" else stat.S_IFDIR),
                f"the {kind} ROM entry changed type")
        require(listing(saves) == [], f"refused run changed the save directory: {listing(saves)}")
        forbid_work_path(base, out, err)
    return scenario


SCENARIOS = {
    "periodic-flush": scenario_periodic_flush,
    "first-write": scenario_first_write,
    "idempotent-rerun": scenario_idempotent_rerun,
    "sweep": scenario_sweep,
    "rtc-final-compare": scenario_rtc_final_compare,
    "savedir-missing": scenario_savedir_missing,
    "savedir-not-directory": scenario_savedir_not_directory,
    "savedir-symlink-path": scenario_savedir_symlink_path,
    "import-exact": scenario_import_exact,
    "import-zero": size_scenario("save-size", 0),
    "import-short": size_scenario("save-size", CLOCK_WANT - 1),
    "import-long": size_scenario("save-size", CLOCK_WANT + 1),
    "import-mgba-footer": size_scenario("save-size", 32768 + 48),
    "import-oversize": size_scenario("save-size", 8 * 1024 * 1024 + 1),
    "import-bad-rtc": lambda runner, work: import_refusal(runner, work, "save-rtc-block", prepare_bad_rtc),
    "import-symlink": lambda runner, work: import_refusal(runner, work, "save-symlink", prepare_symlink),
    "import-dangling-symlink": lambda runner, work: import_refusal(runner, work, "save-symlink",
                                                                    prepare_dangling),
    "import-fifo": lambda runner, work: import_refusal(runner, work, "save-not-regular", prepare_fifo),
    "import-directory": lambda runner, work: import_refusal(runner, work, "save-not-regular",
                                                             prepare_directory),
    "import-stray-nobattery": scenario_import_stray_nobattery,
    "rom-fifo": rom_special_scenario("fifo"),
    "rom-directory": rom_special_scenario("directory"),
    "continuation": scenario_continuation,
    "rom-max": scenario_rom_max,
    "rom-oversize": scenario_rom_oversize,
    "rom-unreadable": scenario_rom_unreadable,
    "stem-refusal": scenario_stem_refusal,
    "platform-gate": scenario_platform_gate,
    "grammar-empty-value": scenario_grammar_empty_value,
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--runner", required=True)
    parser.add_argument("--work", required=True)
    parser.add_argument("--scenario", required=True, choices=sorted(SCENARIOS))
    args = parser.parse_args()
    runner = os.path.abspath(args.runner)
    work = Path(os.path.abspath(args.work))
    try:
        SCENARIOS[args.scenario](runner, work)
    except Failure as failure:
        print(f"FAIL {args.scenario}: {failure}")
        return 1
    except (OSError, TimeoutError) as error:
        print(f"FAIL {args.scenario}: {type(error).__name__}: {error}")
        return 1
    print(f"host-mode scenario={args.scenario} pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
