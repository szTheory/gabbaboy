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
import re
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
RAM_32K = 0x03


class Failure(Exception):
    pass


def require(condition: bool, why: str) -> None:
    if not condition:
        raise Failure(why)


def fresh_dir(path: Path) -> Path:
    if path.exists():
        # A previous failed row may have left a 0500 directory behind.
        for root, dirs, _files in os.walk(path):
            for name in dirs:
                try:
                    os.chmod(os.path.join(root, name), 0o700)
                except OSError:
                    pass
        try:
            os.chmod(path, 0o700)
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


SCENARIOS = {
    "term": scenario_term,
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
