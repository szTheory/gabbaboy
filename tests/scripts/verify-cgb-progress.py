#!/usr/bin/env python3
"""Run the original native-CGB input/progress control through gabbaboy-runner.

The 32 KiB ROM is assembled from documented SM83 instruction bytes at runtime.
It is temporary harness data, not a game fixture or installable product input.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import re
from pathlib import Path
import subprocess
import sys
import tempfile

if not __debug__:
    raise SystemExit("verify-cgb-progress refuses to run under python -O")

NINTENDO_LOGO = bytes.fromhex(
    "ce ed 66 66 cc 0d 00 0b 03 73 00 83 00 0c 00 0d 00 08 11 1f 88 89 00 "
    "0e dc cc 6e e6 dd dd d9 99 bb bb 67 63 6e 0e ec cc dd dc 99 9f bb b9 33 3e"
)
ROM_SIZE = 32768
HALF_DOTS_PER_FRAME = 140448
BUDGET_HALF_DOTS = 120 * HALF_DOTS_PER_FRAME
CONTROL_SHA256 = "17822873ec8641280d9504229d96850414e872bc90de5431469a498e5271db7e"
CONTROL_COMPAT_SHA256 = "6a1d4a1ed58e8a51f3a5be1283a2226775867fc1373b628ecbc798d12d3ca5fc"
SOURCE_ANCHORS = (
    ("ready", 0x15F, bytes.fromhex("3e a5 ea 00 c0 af ea 01")),
    ("right_input", 0x16C, bytes.fromhex("3e 20 e0 00 f0 00 cb 47")),
    ("progress", 0x17C, bytes.fromhex("3e 01 ea 01 c0")),
)


class CheckError(Exception):
    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


class Program:
    def __init__(self) -> None:
        self.code = bytearray()
        self.labels: dict[str, int] = {}
        self.fixups: list[tuple[int, str]] = []

    def emit(self, *values: int) -> None:
        self.code.extend(values)

    def label(self, name: str) -> None:
        if name in self.labels:
            raise ValueError(f"duplicate label {name}")
        self.labels[name] = len(self.code)

    def jr_nz(self, name: str) -> None:
        self.emit(0x20, 0)
        self.fixups.append((len(self.code) - 1, name))

    def jr(self, name: str) -> None:
        self.emit(0x18, 0)
        self.fixups.append((len(self.code) - 1, name))

    def finish(self) -> bytes:
        for offset, name in self.fixups:
            if name not in self.labels:
                raise ValueError(f"missing label {name}")
            relative = self.labels[name] - (offset + 1)
            if not -128 <= relative <= 127:
                raise ValueError(f"relative jump to {name} is out of range")
            self.code[offset] = relative & 0xFF
        return bytes(self.code)


def authored_program() -> tuple[bytes, dict[str, int]]:
    """Build a palette-0 blue-to-green control with source-derived WRAM markers."""
    p = Program()
    p.emit(0xF3)                         # di
    p.emit(0xAF)                         # xor a
    p.emit(0xE0, 0x40)                   # ldh ($ff40),a; disable LCD for palette setup
    p.emit(0x3E, 0x80, 0xE0, 0x68)       # BGPI: palette 0, colour 0, auto-increment
    p.emit(0x3E, 0x1F, 0xE0, 0x69)       # BGPD low: RGB555 blue = $001f
    p.emit(0xAF, 0xE0, 0x69)             # BGPD high
    p.label("ready_anchor")
    p.emit(0x3E, 0xA5, 0xEA, 0x00, 0xC0) # ld a,$a5; ld ($c000),a
    p.emit(0xAF, 0xEA, 0x01, 0xC0)       # xor a; ld ($c001),a
    p.emit(0x3E, 0x91, 0xE0, 0x40)       # LCD on, BG on, unsigned tile data
    p.label("poll_anchor")
    p.emit(0x3E, 0x20, 0xE0, 0x00)       # select direction keys at JOYP
    p.emit(0xF0, 0x00, 0xCB, 0x47)       # read JOYP; bit 0 is RIGHT
    p.jr_nz("poll_anchor")              # released RIGHT: continue polling
    p.emit(0xFA, 0x01, 0xC0, 0xB7)       # read progress byte; OR a
    p.jr_nz("poll_anchor")              # only accept the first press
    p.label("progress_anchor")
    p.emit(0x3E, 0x01, 0xEA, 0x01, 0xC0) # ld a,1; ld ($c001),a exactly once
    p.label("vblank_wait")
    p.emit(0xF0, 0x44, 0xFE, 0x90)       # read LY; compare with 144
    p.jr_nz("vblank_wait")
    p.emit(0x3E, 0x80, 0xE0, 0x68)       # select BG palette 0, colour 0
    p.emit(0x3E, 0xE0, 0xE0, 0x69)       # BGPD low: RGB555 green = $03e0
    p.emit(0x3E, 0x03, 0xE0, 0x69)       # BGPD high
    p.label("spin")
    p.jr("spin")
    return p.finish(), dict(p.labels)


def header_checksum(rom: bytearray) -> int:
    value = 0
    for byte in rom[0x134:0x14D]:
        value = (value - byte - 1) & 0xFF
    return value


def build_rom() -> tuple[bytes, dict[str, int]]:
    program, labels = authored_program()
    rom = bytearray(ROM_SIZE)
    rom[0x100:0x104] = bytes((0x00, 0xC3, 0x50, 0x01))  # nop; jp $0150
    rom[0x104:0x134] = NINTENDO_LOGO
    rom[0x134:0x143] = b"GBB CGB CONTROL"
    rom[0x143] = 0x80                        # CGB capable; native mode on CGB profile
    rom[0x146] = 0x00                        # no SGB features
    rom[0x147] = 0x00                        # ROM-only cartridge
    rom[0x148] = 0x00                        # 32 KiB
    rom[0x149] = 0x00                        # no external RAM
    rom[0x150:0x150 + len(program)] = program
    rom[0x14D] = header_checksum(rom)
    labels = {name: 0x150 + offset for name, offset in labels.items()}
    return bytes(rom), labels


def build_compat_rom() -> tuple[bytes, dict[str, int]]:
    """Derive a header-valid compatibility-mode control from the authored native-CGB image."""
    native, labels = build_rom()
    rom = bytearray(native)
    rom[0x143] = 0x00
    rom[0x14D] = header_checksum(rom)
    return bytes(rom), labels


def input_script(with_right: bool) -> bytes:
    lines = ["gbinput 1", "wait 1f", "mark title", "wait 1f", "mark play_start",
             "wait 1f", "mark mid"]
    if with_right:
        lines.extend(("tap RIGHT 1f", "wait 116f"))
    else:
        lines.append("wait 117f")
    return ("\n".join(lines) + "\n").encode("ascii")


def case_line(identifier: str, predicate: str, script_name: str, rom: bytes, script: bytes) -> str:
    return (f"id={identifier} rom=control.gb rom_sha256={hashlib.sha256(rom).hexdigest()} "
            f"rom_size={len(rom)} oracle=progress-predicate predicate={predicate} "
            f"expect_hw_capability=0 input_script={script_name} "
            f"input_sha256={hashlib.sha256(script).hexdigest()} "
            f"budget_half_dots={BUDGET_HALF_DOTS} model_pass=cgb-cpu-e\n")


def validate_case_identity(line: str, rom: bytes, script: bytes) -> None:
    values = dict(token.split("=", 1) for token in line.split() if "=" in token)
    if values.get("rom_sha256") != hashlib.sha256(rom).hexdigest():
        raise CheckError("rom-identity-mismatch")
    if values.get("input_sha256") != hashlib.sha256(script).hexdigest():
        raise CheckError("script-identity-mismatch")


def validate_source_anchors(rom: bytes) -> None:
    for _, offset, anchor in SOURCE_ANCHORS:
        if rom[offset:offset + len(anchor)] != anchor:
            raise CheckError("predicate-anchor-mismatch")


def validate_native_receipt(receipt: str) -> None:
    fields = dict(re.findall(r"(?:^|\s)([a-zA-Z0-9_]+)=([^\s]+)", receipt))
    required = {
        "profile": "CGB-CPU-E",
        "execution_mode": "cgb",
        "frame_format": "GBB-RGB555LE-v1",
        "evidence_class": "original-harness-only",
    }
    for key, value in required.items():
        if fields.get(key) != value:
            raise CheckError(f"native-mode-receipt-missing:{key}")
    if not re.fullmatch(r"[0-9a-f]{64}", fields.get("rom_sha256", "")):
        raise CheckError("native-mode-receipt-missing:rom_sha256")
    if not re.fullmatch(r"[0-9a-f]{64}", fields.get("input_sha256", "")):
        raise CheckError("native-mode-receipt-missing:input_sha256")
    for label in ("title", "play_start", "mid", "hit"):
        if not re.fullmatch(r"[0-9]+", fields.get(f"checkpoint_{label}_completion_half_dots", "")):
            raise CheckError(f"native-mode-receipt-missing:checkpoint_{label}_completion_half_dots")
        if not re.fullmatch(r"[0-9a-f]{64}", fields.get(f"checkpoint_{label}_frame", "")):
            raise CheckError(f"native-mode-receipt-missing:checkpoint_{label}_frame")
    blue = expected_solid_rgb555_digest(0x001F)
    green = expected_solid_rgb555_digest(0x03E0)
    if any(fields.get(f"checkpoint_{label}_frame") != blue for label in ("title", "play_start", "mid")):
        raise CheckError("native-mode-receipt-unexpected-pre-input-frame")
    if fields.get("checkpoint_hit_frame") != green:
        raise CheckError("native-mode-receipt-unexpected-post-input-frame")
    try:
        pcm_samples = int(fields.get("pcm_samples", ""))
    except ValueError as error:
        raise CheckError("native-mode-receipt-missing:pcm_samples") from error
    if pcm_samples <= 0:
        raise CheckError("native-mode-receipt-missing:pcm_samples")


def expected_solid_rgb555_digest(color: int) -> str:
    pixels = color.to_bytes(2, "little") * (160 * 144)
    return hashlib.sha256(b"GBB-RGB555LE-v1 160x144\n" + pixels).hexdigest()


def git_text(repo_root: Path, args: list[str]) -> str:
    result = subprocess.run(["git", "-C", str(repo_root), *args], stdin=subprocess.DEVNULL,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                            encoding="utf-8", errors="replace", check=False)
    if result.returncode != 0:
        raise CheckError("source-revision-invalid")
    return result.stdout.rstrip("\n")


def resolve_source_commit(repo_root: Path, revision: str) -> str:
    commit = git_text(repo_root, ["rev-parse", "--verify", f"{revision}^{{commit}}"])
    if not re.fullmatch(r"[0-9a-f]{40,64}", commit):
        raise CheckError("source-revision-invalid")
    return commit


SOURCE_FACTS = {
    "src/accept/predicate.c": (
        CONTROL_SHA256, CONTROL_COMPAT_SHA256, '"cgb-control-progress"',
        '"cgb-control-impossible"', '"cgb-control-compatibility"',
        "0x15Fu", "0x16Cu", "0x17Cu",
        "0x3E, 0xA5, 0xEA, 0x00, 0xC0, 0xAF, 0xEA, 0x01",
        "0x3E, 0x01, 0xEA, 0x01, 0xC0",
        "0x3E, 0x20, 0xE0, 0x00, 0xF0, 0x00, 0xCB, 0x47",
    ),
    "src/accept/gbb_accept.h": (
        "GBB_ACCEPT_OBSERVE_PROGRESS_ONLY", "source_rows", "gbb_accept_predicate_eval_fn",
    ),
    "src/runner/acceptance.c": (
        "execution-mode-mismatch", "GBB_MODE_CGB", "GBB_ACCEPT_OBSERVE_PROGRESS_ONLY",
        "gbb_copy_frame_rgb555", "gbb_accept_rgb555_digest_bin", "pcm_samples",
    ),
    "include/gabbaboy/gabbaboy.h": (
        "GBB_MODE_CGB = 2", "GBB_MODE_CGB_DMG_COMPAT = 3", "GBB_INFO_SIZE_V1",
    ),
}


def verify_source_identity(repo_root: Path, revision: str, checker_path: Path) -> tuple[str, str]:
    commit = resolve_source_commit(repo_root, revision)
    try:
        relative = checker_path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError as error:
        raise CheckError("checker-outside-repository") from error
    committed_checker = git_text_bytes(repo_root, ["show", f"{commit}:{relative}"])
    current_checker = checker_path.read_bytes()
    if committed_checker != current_checker:
        raise CheckError("checker-source-mismatch")
    for path, facts in SOURCE_FACTS.items():
        source = git_text_bytes(repo_root, ["show", f"{commit}:{path}"]).decode("utf-8", errors="strict")
        if any(fact not in source for fact in facts):
            raise CheckError(f"source-fact-missing:{path}")
    return commit, hashlib.sha256(current_checker).hexdigest()


def git_text_bytes(repo_root: Path, args: list[str]) -> bytes:
    result = subprocess.run(["git", "-C", str(repo_root), *args], stdin=subprocess.DEVNULL,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if result.returncode != 0:
        raise CheckError("source-revision-invalid")
    return result.stdout


def self_test(repo_root: Path) -> None:
    rom, labels = build_rom()
    if len(NINTENDO_LOGO) != 48 or len(rom) != ROM_SIZE or rom[0x143] != 0x80:
        raise CheckError("header-invalid")
    if rom[0x147:0x14A] != b"\x00\x00\x00" or rom[0x14D] != header_checksum(bytearray(rom)):
        raise CheckError("header-invalid")
    if rom[0x104:0x134] != NINTENDO_LOGO:
        raise CheckError("header-logo-invalid")
    if hashlib.sha256(rom).hexdigest() != CONTROL_SHA256:
        raise CheckError("rom-source-identity-mismatch")
    if labels != {"ready_anchor": 0x15F, "poll_anchor": 0x16C, "progress_anchor": 0x17C,
                  "vblank_wait": 0x181, "spin": 0x193}:
        raise CheckError("rom-anchor-layout-mismatch")
    validate_source_anchors(rom)
    compat_rom, compat_labels = build_compat_rom()
    if (hashlib.sha256(compat_rom).hexdigest() != CONTROL_COMPAT_SHA256 or
            compat_rom[0x143] != 0 or compat_rom[0x14D] != header_checksum(bytearray(compat_rom)) or
            compat_labels != labels):
        raise CheckError("compatibility-rom-identity-mismatch")
    validate_source_anchors(compat_rom)
    positive = input_script(True)
    line = case_line("cgb-control-progress", "cgb-control-progress", "positive.input", rom, positive)
    validate_case_identity(line, rom, positive)
    try:
        validate_case_identity(line.replace(hashlib.sha256(rom).hexdigest(), "0" * 64, 1), rom, positive)
    except CheckError as error:
        if error.reason != "rom-identity-mismatch":
            raise
    else:
        raise CheckError("self-test-rom-identity-control-failed")
    try:
        validate_case_identity(line.replace(hashlib.sha256(positive).hexdigest(), "0" * 64, 1), rom, positive)
    except CheckError as error:
        if error.reason != "script-identity-mismatch":
            raise
    else:
        raise CheckError("self-test-script-identity-control-failed")
    changed = bytearray(rom)
    changed[SOURCE_ANCHORS[0][1]] ^= 1
    try:
        validate_source_anchors(bytes(changed))
    except CheckError as error:
        if error.reason != "predicate-anchor-mismatch":
            raise
    else:
        raise CheckError("self-test-predicate-anchor-control-failed")
    blue = expected_solid_rgb555_digest(0x001F)
    green = expected_solid_rgb555_digest(0x03E0)
    complete = ("profile=CGB-CPU-E execution_mode=cgb frame_format=GBB-RGB555LE-v1 "
                "evidence_class=original-harness-only rom_sha256=" + "a" * 64 + " input_sha256=" + "b" * 64 +
                " checkpoint_title_completion_half_dots=1 checkpoint_title_frame=" + blue +
                " checkpoint_play_start_completion_half_dots=2 checkpoint_play_start_frame=" + blue +
                " checkpoint_mid_completion_half_dots=3 checkpoint_mid_frame=" + blue +
                " checkpoint_hit_completion_half_dots=4 checkpoint_hit_frame=" + green + " pcm_samples=1")
    validate_native_receipt(complete)
    try:
        validate_native_receipt(complete.replace("execution_mode=cgb ", ""))
    except CheckError as error:
        if error.reason != "native-mode-receipt-missing:execution_mode":
            raise
    else:
        raise CheckError("self-test-native-mode-receipt-control-failed")
    try:
        resolve_source_commit(repo_root, "gsd-invalid-cgb-progress-source-revision")
    except CheckError as error:
        if error.reason != "source-revision-invalid":
            raise
    else:
        raise CheckError("self-test-source-revision-control-failed")


def load_host_fixture(repo_root: Path):
    path = repo_root / "tests/scripts/host_fixture.py"
    spec = importlib.util.spec_from_file_location("host_fixture", path)
    if spec is None or spec.loader is None:
        raise CheckError("host-fixture-unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def status_reason(stdout: str) -> str | None:
    match = re.search(r"status=fail\s+model=[^\s]+\s+reason=([^\s]+)", stdout)
    return match.group(1) if match else None


def run_tracer(runner: Path, repo_root: Path, source_revision: str, checker_path: Path) -> int:
    self_test(repo_root)
    source_commit, checker_sha = verify_source_identity(repo_root, source_revision, checker_path)
    if not runner.is_file():
        raise CheckError("runner-unavailable")
    runner_sha = hashlib.sha256(runner.read_bytes()).hexdigest()
    rom, _ = build_rom()
    positive = input_script(True)
    no_input = input_script(False)
    validate_source_anchors(rom)
    if hashlib.sha256(rom).hexdigest() != CONTROL_SHA256:
        raise CheckError("rom-source-identity-mismatch")
    with tempfile.TemporaryDirectory(prefix="gbb-cgb-progress-") as temp:
        work = Path(temp)
        work.chmod(0o700)
        (work / "control.gb").write_bytes(rom)
        (work / "positive.input").write_bytes(positive)
        (work / "no-input.input").write_bytes(no_input)
        cases = (
            case_line("cgb-control-progress", "cgb-control-progress", "positive.input", rom, positive) +
            case_line("cgb-control-no-input", "cgb-control-progress", "no-input.input", rom, no_input) +
            case_line("cgb-control-impossible", "cgb-control-impossible", "positive.input", rom, positive)
        )
        (work / "cases.txt").write_text(cases, encoding="ascii")
        helper = load_host_fixture(repo_root)
        args = ["--acceptance", "cases.txt", "--model", "cgb-cpu-e", "--receipt"]
        positive_code, positive_out, positive_err = helper.run_runner(
            str(runner), [*args, "--case", "cgb-control-progress"], str(work), 30)
        no_input_code, no_input_out, no_input_err = helper.run_runner(
            str(runner), [*args, "--case", "cgb-control-no-input"], str(work), 30)
        impossible_code, impossible_out, impossible_err = helper.run_runner(
            str(runner), [*args, "--case", "cgb-control-impossible"], str(work), 30)
        receipt_lines = [line for line in positive_out.splitlines() if line.startswith("receipt id=")]
        if positive_code != 0 or "status=pass" not in positive_out or positive_err or len(receipt_lines) != 1:
            raise CheckError("positive-native-cgb-route-failed:" +
                             positive_out.replace(str(work), "<temp>").strip() + ":" +
                             positive_err.replace(str(work), "<temp>").strip())
        validate_native_receipt(receipt_lines[0])
        for name, code, stdout, stderr in (
            ("no-input", no_input_code, no_input_out, no_input_err),
            ("impossible", impossible_code, impossible_out, impossible_err),
        ):
            if code != 1 or status_reason(stdout) != "predicate-not-reached" or stderr:
                safe_out = stdout.replace(str(work), "<temp>").strip()
                safe_err = stderr.replace(str(work), "<temp>").strip()
                raise CheckError(f"{name}-negative-control-failed:exit={code}:{safe_out}:{safe_err}")
    print("acceptance id=cgb-control-progress evidence=original-harness-only "
          f"source_revision={source_commit} checker_sha256={checker_sha} "
          f"runner_sha256={runner_sha} rom_sha256={hashlib.sha256(rom).hexdigest()} "
          f"input_sha256={hashlib.sha256(positive).hexdigest()} "
          "positive=pass no_input=predicate-not-reached impossible=predicate-not-reached")
    return 0


def run_compatibility(runner: Path, repo_root: Path, source_revision: str,
                      checker_path: Path) -> int:
    self_test(repo_root)
    source_commit, checker_sha = verify_source_identity(repo_root, source_revision, checker_path)
    if not runner.is_file():
        raise CheckError("runner-unavailable")
    runner_sha = hashlib.sha256(runner.read_bytes()).hexdigest()
    rom, _ = build_compat_rom()
    script = input_script(True)
    if hashlib.sha256(rom).hexdigest() != CONTROL_COMPAT_SHA256:
        raise CheckError("compatibility-rom-identity-mismatch")
    with tempfile.TemporaryDirectory(prefix="gbb-cgb-mode-control-") as temp:
        work = Path(temp)
        work.chmod(0o700)
        (work / "control.gb").write_bytes(rom)
        (work / "positive.input").write_bytes(script)
        case = case_line("cgb-control-compatibility", "cgb-control-compatibility",
                         "positive.input", rom, script)
        (work / "cases.txt").write_text(case, encoding="ascii")
        helper = load_host_fixture(repo_root)
        code, stdout, stderr = helper.run_runner(
            str(runner), ["--acceptance", "cases.txt", "--case", "cgb-control-compatibility",
                          "--model", "cgb-cpu-e", "--receipt"], str(work), 30)
    expected = "reason=execution-mode-mismatch expected=cgb actual=cgb-dmg-compat"
    if code != 3 or expected not in stdout or "status=pass" in stdout or "receipt id=" in stdout or stderr:
        safe_out = stdout.replace(str(work), "<temp>").strip()
        safe_err = stderr.replace(str(work), "<temp>").strip()
        raise CheckError(f"compatibility-mode-control-failed:exit={code}:{safe_out}:{safe_err}")
    print("compatibility-control pass actual=cgb-dmg-compat "
          f"source_revision={source_commit} checker_sha256={checker_sha} runner_sha256={runner_sha} "
          f"rom_sha256={hashlib.sha256(rom).hexdigest()} input_sha256={hashlib.sha256(script).hexdigest()}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runner", type=Path)
    parser.add_argument("--repo-root", type=Path)
    parser.add_argument("--source-revision")
    parser.add_argument("--tracer", action="store_true")
    parser.add_argument("--compatibility", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    try:
        if args.repo_root is None:
            raise CheckError("repo-root-required")
        repo_root = args.repo_root.resolve()
        if args.self_test:
            self_test(repo_root)
            print("verify-cgb-progress self-test pass controls=source-revision,rom-identity,script-identity,anchor,native-mode-receipt")
            return 0
        if args.tracer:
            if args.runner is None or args.source_revision is None:
                raise CheckError("runner-and-source-revision-required")
            return run_tracer(args.runner.resolve(), repo_root, args.source_revision,
                              Path(__file__).resolve())
        if args.compatibility:
            if args.runner is None or args.source_revision is None:
                raise CheckError("runner-and-source-revision-required")
            return run_compatibility(args.runner.resolve(), repo_root, args.source_revision,
                                     Path(__file__).resolve())
        raise CheckError("select-self-test-or-tracer")
    except (CheckError, OSError, TimeoutError, ValueError) as error:
        reason = error.reason if isinstance(error, CheckError) else str(error)
        print(f"verify-cgb-progress: {reason}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
