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
import sys
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


SCENARIOS = {
    "periodic-flush": scenario_periodic_flush,
    "first-write": scenario_first_write,
    "idempotent-rerun": scenario_idempotent_rerun,
    "sweep": scenario_sweep,
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
