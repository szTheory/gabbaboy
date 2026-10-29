#!/usr/bin/env python3
"""Real-signal scenarios for gabbaboy-runner host mode (Phase 18, HOST-02, D-17).

    python3 -I test_host_signals.py --runner PATH --work DIR --scenario NAME [--sanitized]

Each scenario starts a real runner process, waits for `gbb-host: ready` under a watchdog, sends exactly
one real signal per row, and prints `host-signals scenario=<name> pass` or `FAIL <name>: <why>` (exit 1).
POSIX only: Windows never generates SIGTERM and has no host mode (D-05). Assertions are explicit checks,
never `assert`, and python -O is refused.

Time is evidence in exactly one place: the documented 2.0 s kill()-to-wait() contract ceiling of the
`term` row, and only without --sanitized. Every other wait is a watchdog that fails with a reason.
"""
from __future__ import annotations

import argparse
import importlib.util
import os
import random
import re
import resource
import shutil
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

if not __debug__:
    raise SystemExit("test_host_signals refuses to run under python -O")
if os.name == "nt":
    raise SystemExit("test_host_signals is POSIX-only (D-05)")

_spec = importlib.util.spec_from_file_location(
    "host_fixture", Path(__file__).resolve().with_name("host_fixture.py"))
host_fixture = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(host_fixture)

READY_TIMEOUT = 20.0   # a loaded hosted runner may need seconds to load; far below the 60 s CTest bound
EXIT_TIMEOUT = 15.0    # after one signal the runner must be gone long before this
BATCH_TIMEOUT = 40.0
CEILING_SECONDS = 2.0  # D-17: Playstead sends SIGKILL about 2 s after SIGTERM
MBC1_RAM_BATTERY = 0x03
MBC3_TIMER_RAM_BATTERY = 0x10
RAM_8K = 0x02
RAM_32K = 0x03
RTC_SAV_BYTES = 32768 + 21


class Failure(Exception):
    pass


def require(condition: bool, why: str) -> None:
    if not condition:
        raise Failure(why)


def fresh_dir(path: Path) -> Path:
    if path.exists():
        # A previous failed row may have left a 0500 directory behind.
        try:
            os.chmod(path, 0o700)
        except OSError:
            pass
        for root, dirs, _files in os.walk(path):
            for name in dirs:
                try:
                    os.chmod(os.path.join(root, name), 0o700)
                except OSError:
                    pass
        shutil.rmtree(path)
    path.mkdir(parents=True)
    return path


def listing(directory: Path) -> list[str]:
    return sorted(entry.name for entry in directory.iterdir())


class Child:
    """A runner process whose stderr is read by a thread, so waiting can never block unboundedly."""

    def __init__(self, runner: str, args: list[str], cwd: Path, *, ignore_int: bool = False,
                 preexec=None) -> None:
        saved = {s: signal.getsignal(s) for s in (signal.SIGINT, signal.SIGHUP)}
        try:
            # The harness itself may have been started as a background job with SIGINT ignored; the child
            # must see default dispositions unless the row is exactly the inherited-ignore one.
            signal.signal(signal.SIGHUP, signal.SIG_DFL)
            signal.signal(signal.SIGINT, signal.SIG_IGN if ignore_int else signal.SIG_DFL)
            self.process = subprocess.Popen(
                [runner, *args], cwd=str(cwd), stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE, start_new_session=True, preexec_fn=preexec)
        finally:
            for number, handler in saved.items():
                signal.signal(number, handler)
        self.lines: list[str] = []
        self.eof = False
        self.cond = threading.Condition()
        self.sent_at: float | None = None
        self.reaped_at: float | None = None
        self.thread = threading.Thread(target=self._read, daemon=True)
        self.thread.start()

    def _read(self) -> None:
        stream = self.process.stderr
        while True:
            raw = stream.readline()
            with self.cond:
                if not raw:
                    self.eof = True
                else:
                    self.lines.append(raw.decode("utf-8", errors="replace"))
                self.cond.notify_all()
            if not raw:
                return

    def text(self) -> str:
        with self.cond:
            return "".join(self.lines)

    def wait_for(self, pattern: str, timeout: float, *, after: int = 0) -> re.Match | None:
        """First match of `pattern` in the lines from index `after`, or None on exit or timeout."""
        compiled = re.compile(pattern)
        deadline = time.monotonic() + timeout
        with self.cond:
            while True:
                found = compiled.search("".join(self.lines[after:]))
                if found:
                    return found
                remaining = deadline - time.monotonic()
                if self.eof or remaining <= 0:
                    return None
                self.cond.wait(min(remaining, 0.25))

    def line_count(self) -> int:
        with self.cond:
            return len(self.lines)

    def wait_ready(self) -> None:
        if self.wait_for(r"gbb-host: ready", READY_TIMEOUT) is None:
            self.kill()
            raise Failure(f"no 'gbb-host: ready' within {READY_TIMEOUT} s: {self.text().strip()!r}")

    def send(self, number: int) -> None:
        self.sent_at = time.monotonic()
        os.kill(self.process.pid, number)  # the child pid directly, never a process group

    def alive(self) -> bool:
        return self.process.poll() is None

    def wait_exit(self, timeout: float = EXIT_TIMEOUT) -> int:
        try:
            code = self.process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            self.kill()
            raise Failure(f"runner still running {timeout} s after the signal: {self.text().strip()!r}")
        self.reaped_at = time.monotonic()
        self.thread.join(timeout=5.0)
        return code

    def kill(self) -> None:
        try:
            os.killpg(self.process.pid, signal.SIGKILL)
        except OSError:
            pass
        try:
            self.process.wait(timeout=10.0)
        except subprocess.TimeoutExpired:
            pass
        self.thread.join(timeout=5.0)

    def close(self) -> None:
        if self.alive():
            self.kill()
        if self.process.stderr:
            self.process.stderr.close()


def run_batch(runner: str, rom: Path, save_dir: Path, frames: int, cwd: Path) -> tuple[int, str]:
    code, _out, err = host_fixture.run_runner(
        runner, ["--rom", str(rom), "--save-dir", str(save_dir), "--frames", str(frames)],
        str(cwd), BATCH_TIMEOUT)
    return code, err


EXIT_LINE = re.compile(
    r"gbb-host: exit status=(?P<status>\w+) reason=(?P<reason>[\w-]+)(?: stop=\w+)? "
    r"stopped_at_frame=(?P<frame>\d+) flush=(?P<flush>\w+)")


def exit_line(text: str) -> re.Match:
    found = EXIT_LINE.search(text)
    require(found is not None, f"no exit line in stderr: {text.strip()!r}")
    return found


def paced_spin(runner: str, base: Path, name: str, cart_type: int = MBC1_RAM_BATTERY,
               ram_code: int = RAM_32K, **kwargs) -> tuple[Child, Path, Path]:
    """Starts a paced (no --frames) spin-increment runner in a fresh save dir and waits for ready."""
    rom = base / "spin.gb"
    rom.write_bytes(host_fixture.build_rom("spin-increment", cart_type, ram_code))
    saves = fresh_dir(base / name)
    child = Child(runner, ["--rom", str(rom), "--save-dir", str(saves)], base, **kwargs)
    child.wait_ready()
    return child, rom, saves


def scenario_term(runner: str, work: Path, sanitized: bool) -> None:
    """One SIGTERM ends a paced run at a frame boundary: exit 0, flushed, and a fresh `--frames K`
    batch run reproduces the same .sav byte for byte, so the stop landed on a whole frame."""
    base = fresh_dir(work)
    child, rom, saves = paced_spin(runner, base, "saves")
    try:
        time.sleep(0.5)
        child.send(signal.SIGTERM)
        code = child.wait_exit()
    finally:
        child.close()
    err = child.text()
    require(code == 0, f"exit {code}, expected 0: {err.strip()!r}")
    found = exit_line(err)
    require(found["status"] == "clean" and found["reason"] == "SIGTERM",
            f"exit line is not status=clean reason=SIGTERM: {found.group(0)!r}")
    require(found["flush"] in ("written", "unchanged"), f"flush={found['flush']}, expected written|unchanged")
    frame = int(found["frame"])
    require(frame >= 1, "stopped_at_frame=0: the runner stopped before it ran a frame")
    sav = saves / "spin.sav"
    require(sav.is_file(), "SIGTERM left no .sav: the final flush did not run")
    signalled = sav.read_bytes()
    require(len(signalled) == 32768, f"signalled image is {len(signalled)} bytes, expected 32768")
    require(listing(saves) == ["spin.sav"], f"unexpected directory entries {listing(saves)}")
    if not sanitized:
        elapsed = child.reaped_at - child.sent_at
        require(elapsed < CEILING_SECONDS,
                f"kill-to-wait took {elapsed:.3f} s, over the {CEILING_SECONDS} s ceiling")

    replay_dir = fresh_dir(base / "replay")
    code, err = run_batch(runner, rom, replay_dir, frame, base)
    require(code == 0, f"replay --frames {frame} exit {code}: {err.strip()!r}")
    replayed = (replay_dir / "spin.sav").read_bytes()
    require(replayed == signalled,
            f"replay --frames {frame} differs from the signalled run: the stop did not land on a frame boundary")


def stop_and_collect(child: Child, number: int, pause: float = 0.5) -> tuple[int, str]:
    """Sends exactly one signal after `pause`, waits for the exit and returns (exit code, stderr)."""
    try:
        time.sleep(pause)
        child.send(number)
        code = child.wait_exit()
    finally:
        child.close()
    return code, child.text()


def scenario_int(runner: str, work: Path, sanitized: bool) -> None:
    """One SIGINT is a clean stop like SIGTERM, with its own reason, and the save is flushed."""
    base = fresh_dir(work)
    child, rom, saves = paced_spin(runner, base, "saves")
    code, err = stop_and_collect(child, signal.SIGINT)
    require(code == 0, f"exit {code}, expected 0: {err.strip()!r}")
    found = exit_line(err)
    require(found["status"] == "clean" and found["reason"] == "SIGINT",
            f"exit line is not status=clean reason=SIGINT: {found.group(0)!r}")
    require(int(found["frame"]) >= 1, "stopped_at_frame=0")
    require((saves / "spin.sav").is_file(), "SIGINT left no .sav: the final flush did not run")
    require(len((saves / "spin.sav").read_bytes()) == 32768, "the flushed image has the wrong size")


def scenario_inherited_ign(runner: str, work: Path, sanitized: bool) -> None:
    """D-13: SIGINT inherited as SIG_IGN (nohup, background jobs) stays ignored; SIGTERM still stops."""
    base = fresh_dir(work)
    child, rom, saves = paced_spin(runner, base, "saves", ignore_int=True)
    try:
        time.sleep(0.2)
        child.send(signal.SIGINT)
        time.sleep(0.5)
        require(child.alive(), "the runner exited on SIGINT although it was inherited as SIG_IGN")
        child.send(signal.SIGTERM)
        code = child.wait_exit()
    finally:
        child.close()
    err = child.text()
    require(code == 0, f"exit {code}, expected 0 after SIGTERM: {err.strip()!r}")
    found = exit_line(err)
    require(found["reason"] == "SIGTERM", f"exit line reason is {found['reason']}, expected SIGTERM")
    require((saves / "spin.sav").is_file(), "no .sav after the SIGTERM stop")


def scenario_frames_clean(runner: str, work: Path, sanitized: bool) -> None:
    """A fixed-length batch run ends clean with its own reason."""
    base = fresh_dir(work)
    rom = base / "spin.gb"
    rom.write_bytes(host_fixture.build_rom("spin-increment", MBC1_RAM_BATTERY, RAM_32K))
    saves = fresh_dir(base / "saves")
    code, err = run_batch(runner, rom, saves, 30, base)
    require(code == 0, f"exit {code}, expected 0: {err.strip()!r}")
    found = exit_line(err)
    require(found["status"] == "clean" and found["reason"] == "frames" and found["frame"] == "30",
            f"exit line is not status=clean reason=frames stopped_at_frame=30: {found.group(0)!r}")


def scenario_failure_readonly(runner: str, work: Path, sanitized: bool) -> None:
    """A failed final flush exits 1 and keeps the old .sav byte-identical with no temp left behind.

    The image changes every frame (the spin counter and the RTC sub-second count), so under the D-11
    last-persisted rule the final flush must attempt a write and cannot be skipped as `unchanged`."""
    require(os.geteuid() != 0, "this row cannot run as root: root ignores a 0500 directory; run as a non-root user")
    base = fresh_dir(work)
    rom = base / "spin.gb"
    rom.write_bytes(host_fixture.build_rom("spin-increment", MBC3_TIMER_RAM_BATTERY, RAM_32K))
    saves = fresh_dir(base / "saves")
    code, err = run_batch(runner, rom, saves, 30, base)
    require(code == 0, f"seeding run exit {code}: {err.strip()!r}")
    sav = saves / "spin.sav"
    old = sav.read_bytes()
    require(len(old) == RTC_SAV_BYTES, f"seed image is {len(old)} bytes, expected {RTC_SAV_BYTES}")
    child = Child(runner, ["--rom", str(rom), "--save-dir", str(saves)], base)
    try:
        child.wait_ready()
        os.chmod(saves, 0o500)  # after ready: the directory fd is open, but no entry can be created
        code, err = stop_and_collect(child, signal.SIGTERM, pause=0.3)
        require(code == 1, f"exit {code}, expected 1: {err.strip()!r}")
        require(re.search(r"gbb-host: flush reason=final frame=\d+ result=failed stage=temp", err) is not None,
                f"no 'flush reason=final ... result=failed stage=temp' line: {err.strip()!r}")
        found = exit_line(err)
        require(found["status"] == "failure" and found["reason"] == "flush",
                f"exit line is not status=failure reason=flush: {found.group(0)!r}")
        require(sav.read_bytes() == old, "the old .sav changed although the final flush failed")
        stray = [name for name in listing(saves) if name.startswith(".spin.sav.tmp-")]
        require(not stray, f"temp entries left behind: {stray}")
    finally:
        os.chmod(saves, 0o700)
        child.close()


def scenario_core_stop(runner: str, work: Path, sanitized: bool) -> None:
    """A core stop mid-run still attempts the final flush, then exits 1."""
    base = fresh_dir(work)
    rom = base / "bad.gb"
    rom.write_bytes(host_fixture.build_rom("illegal-opcode", MBC1_RAM_BATTERY, RAM_8K))
    saves = fresh_dir(base / "saves")
    code, err = run_batch(runner, rom, saves, 10, base)
    require(code == 1, f"exit {code}, expected 1: {err.strip()!r}")
    found = exit_line(err)
    require(found["status"] == "failure" and found["reason"] == "core-stop",
            f"exit line is not status=failure reason=core-stop: {found.group(0)!r}")
    require(found["flush"] == "written", f"flush={found['flush']}: the final flush was not attempted")
    image = (saves / "bad.sav").read_bytes()
    require(len(image) == 8192 and image[0] == 0x5A, "the guest's write before the stop was not flushed")


def scenario_pacing_unavailable(runner: str, work: Path, sanitized: bool) -> None:
    """IN-06, against a runner built with a failing monotonic clock (a build-tree fault variant: the shipped
    clock cannot be made to fail). A paced run must stop by itself at the frame boundary where pacing failed,
    print `gbb-host: pacing unavailable` once, still flush, and exit 1 with reason=pacing, instead of running
    on unpaced. A fresh `--frames K` batch run (never paced) reproduces the .sav, so the stop was a whole frame.
    The wait is a watchdog: a runner that keeps going fails with its own reason."""
    base = fresh_dir(work)
    child, rom, saves = paced_spin(runner, base, "saves")
    try:
        try:
            code = child.process.wait(timeout=EXIT_TIMEOUT)
        except subprocess.TimeoutExpired:
            raise Failure("the runner kept running after its pacing clock failed") from None
        child.thread.join(timeout=5.0)
    finally:
        child.close()
    err = child.text()
    require(code == 1, f"exit {code}, expected 1: {err.strip()[-400:]!r}")
    require(err.count("gbb-host: pacing unavailable\n") == 1,
            f"expected exactly one 'gbb-host: pacing unavailable' line: {err.strip()[-400:]!r}")
    found = exit_line(err)
    require(found["status"] == "failure" and found["reason"] == "pacing",
            f"exit line is not status=failure reason=pacing: {found.group(0)!r}")
    require(err.index("gbb-host: pacing unavailable") < found.start(), "the diagnostic must precede the exit line")
    require(found["flush"] == "written", f"flush={found['flush']}: the frames that ran were not flushed")
    frame = int(found["frame"])
    require(frame >= 1, "stopped_at_frame=0: pacing is only checked after a frame")
    sav = saves / "spin.sav"
    require(sav.is_file(), "no .sav: the final flush did not run")
    stopped = sav.read_bytes()
    replay_dir = fresh_dir(base / "replay")
    code, err = run_batch(runner, rom, replay_dir, frame, base)
    require(code == 0, f"replay --frames {frame} exit {code}: {err.strip()!r}")
    require((replay_dir / "spin.sav").read_bytes() == stopped,
            f"replay --frames {frame} differs: the pacing stop did not land on a frame boundary")


def scenario_refusal(runner: str, work: Path, sanitized: bool) -> None:
    """A refusal is exit 2 before any save mutation and before `ready`."""
    base = fresh_dir(work)
    rom = base / "short.gb"
    rom.write_bytes(host_fixture.build_rom("write5a", MBC1_RAM_BATTERY, RAM_8K))
    saves = fresh_dir(base / "saves")
    (saves / "short.sav").write_bytes(bytes(8191))
    code, err = run_batch(runner, rom, saves, 5, base)
    require(code == 2, f"exit {code}, expected 2: {err.strip()!r}")
    require("gbb-host: refused reason=save-size" in err, f"no 'refused reason=save-size': {err.strip()!r}")
    require("gbb-host: ready" not in err, "a refused run printed 'gbb-host: ready'")
    require((saves / "short.sav").read_bytes() == bytes(8191), "a refusal changed the .sav")


def valid_rtc_block(block: bytes) -> str | None:
    """None when the 21-byte block is a structurally valid GBRT version 1 block, else the reason."""
    if len(block) != 21:
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


def scenario_crash_storm(runner: str, work: Path, sanitized: bool) -> None:
    """SIGKILL at pseudo-random moments against an RTC cart: the .sav is always the last completed
    flush (exact size, valid GBRT block), every completed flush replaces the inode (so a torn in-place
    writer is caught), and a final normal start sweeps the temps a kill may have left."""
    base = fresh_dir(work)
    rom = base / "spin.gb"
    rom.write_bytes(host_fixture.build_rom("spin-increment", MBC3_TIMER_RAM_BATTERY, RAM_32K))
    saves = fresh_dir(base / "saves")
    sav = saves / "spin.sav"
    # Children inherit this limit, so a SIGKILLed runner can never write a core file. Setting it on the
    # harness instead of in preexec_fn keeps the fork path free of Python code while threads exist.
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    rng = random.Random(1807)
    inodes: set[int] = set()
    previous_inode: int | None = None
    for round_number in range(6):
        child = Child(runner, ["--rom", str(rom), "--save-dir", str(saves), "--frames", "100000"], base)
        try:
            child.wait_ready()
            found = child.wait_for(r"gbb-host: flush reason=\w[\w-]* frame=\d+ result=written", BATCH_TIMEOUT)
            require(found is not None, f"round {round_number}: no completed flush: {child.text().strip()!r}")
            first = sav.stat()  # right after the first completed flush, long before the next one
            if previous_inode is not None:
                require(first.st_ino != previous_inode,
                        f"round {round_number}: a completed flush kept inode {first.st_ino}: the writer is not atomic")
            inodes.add(first.st_ino)
            time.sleep(rng.uniform(0.0, 0.3))
            child.send(signal.SIGKILL)
            code = child.wait_exit()
        finally:
            child.close()
        require(code == -signal.SIGKILL, f"round {round_number}: exit {code}, expected death by SIGKILL")
        require(sav.is_file(), f"round {round_number}: no .sav after a completed flush and a kill")
        image = sav.read_bytes()
        require(len(image) == RTC_SAV_BYTES,
                f"round {round_number}: .sav is {len(image)} bytes, expected {RTC_SAV_BYTES}")
        bad = valid_rtc_block(image[32768:])
        require(bad is None, f"round {round_number}: the GBRT block is invalid ({bad})")
        previous_inode = sav.stat().st_ino
    require(len(inodes) >= 2, f"only {len(inodes)} inode seen over the storm: flushes replace nothing")
    code, err = run_batch(runner, rom, saves, 5, base)
    require(code == 0, f"the final normal start exit {code}: {err.strip()!r}")
    require(listing(saves) == ["spin.sav"], f"temps survived the sweep: {listing(saves)}")


SCENARIOS = {
    "term": scenario_term,
    "int": scenario_int,
    "inherited-ign": scenario_inherited_ign,
    "frames-clean": scenario_frames_clean,
    "failure-readonly": scenario_failure_readonly,
    "core-stop": scenario_core_stop,
    "pacing-unavailable": scenario_pacing_unavailable,
    "refusal": scenario_refusal,
    "crash-storm": scenario_crash_storm,
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runner", required=True)
    parser.add_argument("--work", required=True)
    parser.add_argument("--scenario", required=True, choices=sorted(SCENARIOS))
    parser.add_argument("--sanitized", action="store_true")
    options = parser.parse_args()
    work = Path(options.work)
    work.parent.mkdir(parents=True, exist_ok=True)
    try:
        SCENARIOS[options.scenario](options.runner, work, options.sanitized)
    except Failure as failure:
        print(f"FAIL {options.scenario}: {failure}")
        return 1
    except Exception as error:  # a harness defect must fail loudly, never pass
        print(f"FAIL {options.scenario}: {type(error).__name__}: {error}")
        return 1
    print(f"host-signals scenario={options.scenario} pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
