#!/usr/bin/env python3
"""Run the original native-CGB input/progress control through gabbaboy-runner.

The 32 KiB ROM is assembled from documented SM83 instruction bytes at runtime.
It is temporary harness data, not a game fixture or installable product input.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import os
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
CGB_TAIL_HALF_DOTS = 8388608
RGB555_HEADER = b"GBB-RGB555LE-v1 160x144\n"
PPM_HEADER = b"P6\n160 144\n255\n"
FRAME_PIXELS = 160 * 144
MAX_OBSERVATIONS = 64
DEFAULT_RUNNER_TIMEOUT_SECONDS = 30
MAX_RUNNER_TIMEOUT_SECONDS = 120
CHECKPOINT_COLORS = {"title": 0x001F, "play_start": 0x001F, "mid": 0x001F, "hit": 0x03E0}
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


def parse_runner_timeout(raw: str) -> int:
    try:
        timeout = int(raw)
    except ValueError as error:
        raise argparse.ArgumentTypeError("runner timeout must be an integer") from error
    if not 1 <= timeout <= MAX_RUNNER_TIMEOUT_SECONDS:
        raise argparse.ArgumentTypeError(
            f"runner timeout must be between 1 and {MAX_RUNNER_TIMEOUT_SECONDS} seconds")
    return timeout


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


def input_script(with_right: bool, button: str = "RIGHT") -> bytes:
    lines = ["gbinput 1", "wait 1f", "mark title", "wait 1f", "mark play_start",
             "wait 1f", "mark mid"]
    if with_right:
        lines.extend((f"tap {button} 1f", "wait 116f"))
    else:
        lines.append("wait 117f")
    return ("\n".join(lines) + "\n").encode("ascii")


def case_line(identifier: str, predicate: str, script_name: str, rom: bytes, script: bytes,
              model_fail: bool = False) -> str:
    model_field = "model_fail" if model_fail else "model_pass"
    expected_failure = " expect_fail_reason=predicate-not-reached" if model_fail else ""
    return (f"id={identifier} rom=control.gb rom_sha256={hashlib.sha256(rom).hexdigest()} "
            f"rom_size={len(rom)} oracle=progress-predicate predicate={predicate} "
            f"expect_hw_capability=0 input_script={script_name} "
            f"input_sha256={hashlib.sha256(script).hexdigest()} "
            f"budget_half_dots={BUDGET_HALF_DOTS} {model_field}=cgb-cpu-e{expected_failure}\n")


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


def token_fields(line: str, prefix: str) -> dict[str, str]:
    if not line.startswith(prefix + " "):
        raise CheckError("observation-record-missing")
    fields: dict[str, str] = {}
    for token in line.split()[1:]:
        if "=" not in token:
            continue
        key, value = token.split("=", 1)
        if key in fields:
            raise CheckError(f"duplicate-field:{key}")
        fields[key] = value
    return fields


def parse_observation(output: str) -> dict[str, str]:
    rows: list[tuple[str, str]] = []
    prefix = "acceptance.cgb-control-progress."
    for line in output.splitlines():
        if not line.startswith(prefix):
            continue
        if "\t" not in line:
            raise CheckError("observation-record-malformed")
        key, value = line[len(prefix):].split("\t", 1)
        rows.append((key, value))
    if not rows or len(rows) > MAX_OBSERVATIONS or rows != sorted(rows):
        raise CheckError("observation-record-order-or-count-invalid")
    fields: dict[str, str] = {}
    for key, value in rows:
        if key in fields:
            raise CheckError(f"duplicate-observation:{key}")
        fields[key] = value
    return fields


def expected_mark_times(script: bytes) -> dict[str, int]:
    try:
        lines = script.decode("ascii").splitlines()
    except UnicodeDecodeError as error:
        raise CheckError("script-format-invalid") from error
    elapsed_frames = 0
    marks: dict[str, int] = {}
    for line in lines[1:]:
        wait = re.fullmatch(r"wait ([0-9]+)f", line)
        mark = re.fullmatch(r"mark ([a-z_]+)", line)
        if wait:
            elapsed_frames += int(wait.group(1))
        elif mark:
            if mark.group(1) in marks:
                raise CheckError("script-duplicate-mark")
            marks[mark.group(1)] = elapsed_frames * HALF_DOTS_PER_FRAME
        elif not re.fullmatch(r"tap (LEFT|RIGHT|UP|DOWN) [0-9]+f", line):
            raise CheckError("script-format-invalid")
    if set(marks) != {"title", "play_start", "mid"}:
        raise CheckError("script-checkpoint-marks-invalid")
    return marks


def expected_solid_rgb555_digest(color: int) -> str:
    pixels = color.to_bytes(2, "little") * FRAME_PIXELS
    return hashlib.sha256(RGB555_HEADER + pixels).hexdigest()


def expand5(channel: int) -> int:
    return (channel << 3) | (channel >> 2)


def solid_rgb555_ppm(color: int) -> bytes:
    red = expand5(color & 0x1F)
    green = expand5((color >> 5) & 0x1F)
    blue = expand5((color >> 10) & 0x1F)
    return PPM_HEADER + bytes((red, green, blue)) * FRAME_PIXELS


def validate_checkpoint_dump(path: Path, label: str, expected_digest: str) -> None:
    try:
        data = path.read_bytes()
    except OSError as error:
        raise CheckError(f"checkpoint-dump-missing:{label}") from error
    expected_color = CHECKPOINT_COLORS[label]
    expected_ppm = solid_rgb555_ppm(expected_color)
    if len(data) != len(expected_ppm):
        raise CheckError(f"checkpoint-dump-size-invalid:{label}")
    if not data.startswith(PPM_HEADER):
        raise CheckError(f"checkpoint-dump-format-invalid:{label}")
    if data != expected_ppm:
        raise CheckError(f"checkpoint-dump-color-invalid:{label}")
    if expected_solid_rgb555_digest(expected_color) != expected_digest:
        raise CheckError(f"checkpoint-dump-digest-mismatch:{label}")


def normalized_host_path(path: str) -> str:
    return os.path.normcase(os.path.normpath(path.replace("\\", "/"))).replace("\\", "/")


def validate_progress_fields(fields: dict[str, str], *, observation: bool, rom: bytes,
                             script: bytes, source_commit: str,
                             require_predicate_state: bool = False) -> None:
    key = (lambda name: name) if observation else (lambda name: name)
    expected_identity = {
        key("profile"): "CGB-CPU-E",
        key("execution_mode"): "cgb",
        key("frame_format"): "GBB-RGB555LE-v1",
        key("evidence_class"): "original-harness-only",
        key("rom_sha256"): hashlib.sha256(rom).hexdigest(),
        key("rom_size"): str(len(rom)),
        key("input_sha256"): hashlib.sha256(script).hexdigest(),
        key("predicate_name" if observation else "predicate"): "cgb-control-progress",
        key("budget_half_dots"): str(BUDGET_HALF_DOTS),
        key("core_revision"): source_commit,
        key("build_qualified"): "true",
    }
    if observation:
        expected_identity[key("class")] = "regression"
    for name, expected in expected_identity.items():
        if fields.get(name) != expected:
            raise CheckError(f"progress-field-mismatch:{name}")
    try:
        hit = int(fields.get("t_hit_half_dots", ""))
        end = int(fields.get("end_half_dots", ""))
    except ValueError as error:
        raise CheckError("progress-time-invalid") from error
    if hit <= 0 or hit > BUDGET_HALF_DOTS or end != hit + CGB_TAIL_HALF_DOTS:
        raise CheckError("progress-time-out-of-bounds")
    marks = expected_mark_times(script)
    expected_digests = {label: expected_solid_rgb555_digest(color)
                        for label, color in CHECKPOINT_COLORS.items()}
    for label in CHECKPOINT_COLORS:
        requested_name = (f"checkpoint.{label}.requested_half_dots" if observation else
                          f"checkpoint_{label}_requested_half_dots")
        completion_name = (f"checkpoint.{label}.completion_half_dots" if observation else
                           f"checkpoint_{label}_completion_half_dots")
        frame_name = (f"checkpoint.{label}.frame555" if observation else f"checkpoint_{label}_frame")
        try:
            requested = int(fields.get(requested_name, ""))
            completion = int(fields.get(completion_name, ""))
        except ValueError as error:
            raise CheckError(f"checkpoint-time-invalid:{label}") from error
        expected_requested = hit if label == "hit" else marks[label]
        if requested != expected_requested or completion < requested or completion > end:
            raise CheckError(f"checkpoint-time-mismatch:{label}")
        if fields.get(frame_name) != expected_digests[label]:
            raise CheckError(f"checkpoint-digest-mismatch:{label}")
    rolling_name = "frame.rolling555" if observation else "frame_rolling555"
    pcm_name = "pcm_sha256"
    if not re.fullmatch(r"[0-9a-f]{64}", fields.get(rolling_name, "")):
        raise CheckError("rolling-frame-digest-invalid")
    if not re.fullmatch(r"[0-9a-f]{64}", fields.get(pcm_name, "")):
        raise CheckError("pcm-digest-invalid")
    samples_name = "pcm_samples"
    audible_name = "pcm_audible"
    try:
        samples = int(fields.get(samples_name, ""))
    except ValueError as error:
        raise CheckError("pcm-samples-invalid") from error
    if samples <= 0 or fields.get(audible_name) != "false":
        raise CheckError("pcm-contract-invalid")
    pcm_keys = ("pcm.window.left.peak_to_peak", "pcm.window.left.changes",
                "pcm.window.right.peak_to_peak", "pcm.window.right.changes") if observation else (
                "pcm_left_peak_to_peak", "pcm_left_changes", "pcm_right_peak_to_peak", "pcm_right_changes")
    if any(fields.get(name) != "0" for name in pcm_keys):
        raise CheckError("pcm-window-not-silent")
    if require_predicate_state:
        if fields.get("predicate.ready") != "a5" or fields.get("predicate.progress") != "01":
            raise CheckError("predicate-final-state-mismatch")


def receipt_to_observation_fields(receipt: dict[str, str]) -> dict[str, str]:
    fields = dict(receipt)
    fields.pop("id", None)
    fields["class"] = "regression"
    fields["predicate_name"] = fields.pop("predicate", "")
    for label in CHECKPOINT_COLORS:
        fields[f"checkpoint.{label}.requested_half_dots"] = fields.pop(
            f"checkpoint_{label}_requested_half_dots", "")
        fields[f"checkpoint.{label}.completion_half_dots"] = fields.pop(
            f"checkpoint_{label}_completion_half_dots", "")
        fields[f"checkpoint.{label}.frame555"] = fields.pop(f"checkpoint_{label}_frame", "")
    fields["frame.rolling555"] = fields.pop("frame_rolling555", "")
    fields["pcm.window.left.peak_to_peak"] = fields.pop("pcm_left_peak_to_peak", "")
    fields["pcm.window.left.changes"] = fields.pop("pcm_left_changes", "")
    fields["pcm.window.right.peak_to_peak"] = fields.pop("pcm_right_peak_to_peak", "")
    fields["pcm.window.right.changes"] = fields.pop("pcm_right_changes", "")
    return fields


def validate_native_receipt(receipt: str, rom: bytes, script: bytes, source_commit: str) -> dict[str, str]:
    fields = token_fields(receipt, "receipt")
    validate_progress_fields(receipt_to_observation_fields(fields), observation=True,
                             rom=rom, script=script, source_commit=source_commit)
    return fields


def validate_observation(output: str, rom: bytes, script: bytes, source_commit: str) -> dict[str, str]:
    fields = parse_observation(output)
    validate_progress_fields(fields, observation=True, rom=rom, script=script,
                             source_commit=source_commit, require_predicate_state=True)
    return fields


def compare_observation_receipt(observation: dict[str, str], receipt: dict[str, str]) -> None:
    normalized_receipt = receipt_to_observation_fields(receipt)
    if any(observation.get(key) != value for key, value in normalized_receipt.items()):
        raise CheckError("observation-receipt-mismatch")


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
        "checkpoint_%s_requested_half_dots=%llu checkpoint_%s_completion_half_dots=%llu",
        "pcm_audible=%s", "rom_sha256", "predicate_name", "build_qualified",
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
    committed_sources = {
        path: git_text_bytes(repo_root, ["show", f"{commit}:{path}"]).decode("utf-8", errors="strict")
        for path in SOURCE_FACTS
    }
    validate_source_snapshot(committed_checker, current_checker, committed_sources)
    return commit, hashlib.sha256(current_checker).hexdigest()


def validate_source_snapshot(committed_checker: bytes, current_checker: bytes,
                             committed_sources: dict[str, str],
                             facts_by_path: dict[str, tuple[str, ...]] | None = None) -> None:
    if committed_checker != current_checker:
        raise CheckError("checker-source-mismatch")
    facts_map = SOURCE_FACTS if facts_by_path is None else facts_by_path
    for path, facts in facts_map.items():
        source = committed_sources.get(path)
        if source is None:
            raise CheckError(f"source-evidence-missing:{path}")
        if any(fact not in source for fact in facts):
            raise CheckError(f"source-fact-missing:{path}")


def git_text_bytes(repo_root: Path, args: list[str]) -> bytes:
    result = subprocess.run(["git", "-C", str(repo_root), *args], stdin=subprocess.DEVNULL,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if result.returncode != 0:
        raise CheckError("source-revision-invalid")
    return result.stdout


def committed_path_bytes(repo_root: Path, revision: str, relative: str) -> bytes | None:
    """Read a committed file, returning None when that revision predates the file."""
    tree = subprocess.run(
        ["git", "-C", str(repo_root), "ls-tree", "-r", "--name-only", revision, "--", relative],
        stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    if tree.returncode != 0:
        raise CheckError("source-revision-invalid")
    if not tree.stdout.strip():
        return None
    return git_text_bytes(repo_root, ["show", f"{revision}:{relative}"])


def find_stale_source_revision(repo_root: Path, revisions: list[str], relative: str,
                               current_source: bytes) -> str | None:
    for revision in revisions:
        committed_source = committed_path_bytes(repo_root, revision, relative)
        if committed_source is not None and committed_source != current_source:
            return revision
    return None


def source_history_controls() -> None:
    """Verify stale-source scans skip commits predating the checker file."""
    relative = "tests/scripts/verify-cgb-progress.py"
    with tempfile.TemporaryDirectory(prefix="gbb-cgb-source-history-") as temporary:
        root = Path(temporary)
        empty_hooks = root / "empty-hooks"
        empty_hooks.mkdir()
        global_hooks = root / "global-hooks"
        global_hooks.mkdir()
        hook_marker = root / "global-hook-ran"
        global_hook = global_hooks / "pre-commit"
        global_hook.write_text(
            "#!/bin/sh\nprintf '%s\\n' ran > \"$SYNTHETIC_HOOK_MARKER\"\n", encoding="utf-8")
        global_hook.chmod(0o700)
        global_config = root / "global.gitconfig"
        global_config.write_text(
            f"[core]\n\thooksPath = {global_hooks}\n[commit]\n\tgpgsign = true\n",
            encoding="utf-8")
        git_environment = os.environ.copy()
        git_environment["GIT_CONFIG_GLOBAL"] = str(global_config)
        git_environment["GIT_CONFIG_NOSYSTEM"] = "1"
        git_environment["SYNTHETIC_HOOK_MARKER"] = str(hook_marker)

        def run_fixture_git(args: list[str]):
            return subprocess.run(
                ["git", "-C", str(root), *args], stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
                env=git_environment,
            )

        initialized = subprocess.run(
            ["git", "-C", str(root), "init", "--quiet"], stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, env=git_environment,
        )
        if initialized.returncode != 0:
            raise CheckError("self-test-source-history-git-init-failed")
        checker = root / relative
        checker.parent.mkdir(parents=True)
        checker.write_bytes(b"committed checker version\n")
        for source_path in SOURCE_FACTS:
            source_file = root / source_path
            source_file.parent.mkdir(parents=True, exist_ok=True)
            source_file.write_bytes(b"synthetic committed source\n")
        staged = run_fixture_git(["add", relative, *SOURCE_FACTS.keys()])
        if staged.returncode != 0:
            raise CheckError("self-test-source-history-stage-failed")
        first_commit = run_fixture_git(
            ["-c", f"core.hooksPath={empty_hooks}", "-c", "user.name=OpenGSD Test", "-c",
             "user.email=opengsd-test@example.invalid", "commit", "--no-gpg-sign", "--quiet",
             "-m", "synthetic checker source"])
        if first_commit.returncode != 0:
            raise CheckError("self-test-source-history-commit-failed")
        if hook_marker.exists():
            raise CheckError("self-test-source-history-global-hook-ran")
        stale_revision = git_text(root, ["rev-parse", "HEAD"])

        checker.unlink()
        removed = run_fixture_git(["rm", "--quiet", relative])
        if removed.returncode != 0:
            raise CheckError("self-test-source-history-remove-failed")
        second_commit = run_fixture_git(
            ["-c", f"core.hooksPath={empty_hooks}", "-c", "user.name=OpenGSD Test", "-c",
             "user.email=opengsd-test@example.invalid", "commit", "--no-gpg-sign", "--quiet",
             "-m", "synthetic checker predates file"])
        if second_commit.returncode != 0:
            raise CheckError("self-test-source-history-commit-failed")
        if hook_marker.exists():
            raise CheckError("self-test-source-history-global-hook-ran")
        missing_revision = git_text(root, ["rev-parse", "HEAD"])
        checker.parent.mkdir(parents=True, exist_ok=True)
        checker.write_bytes(b"mutable checker version\n")

        if committed_path_bytes(root, missing_revision, relative) is not None:
            raise CheckError("self-test-source-history-missing-path-not-skipped")
        selected = find_stale_source_revision(
            root, [missing_revision, stale_revision], relative, checker.read_bytes())
        if selected != stale_revision:
            raise CheckError("self-test-source-history-stale-revision-not-found")
        expect_rejected(
            lambda: verify_source_identity(root, selected, checker),
            "checker-source-mismatch", "source-history-stale-checker")


def expect_rejected(action, reason_prefix: str, control: str) -> None:
    try:
        action()
    except CheckError as error:
        if not error.reason.startswith(reason_prefix):
            raise
    else:
        raise CheckError(f"self-test-{control}-control-failed")


def synthetic_progress_fields(rom: bytes, script: bytes, source_commit: str) -> dict[str, str]:
    hit = 4 * HALF_DOTS_PER_FRAME
    fields = {
        "class": "regression",
        "t_hit_half_dots": str(hit),
        "profile": "CGB-CPU-E",
        "execution_mode": "cgb",
        "frame_format": "GBB-RGB555LE-v1",
        "evidence_class": "original-harness-only",
        "rom_sha256": hashlib.sha256(rom).hexdigest(),
        "rom_size": str(len(rom)),
        "input_sha256": hashlib.sha256(script).hexdigest(),
        "predicate_name": "cgb-control-progress",
        "budget_half_dots": str(BUDGET_HALF_DOTS),
        "end_half_dots": str(hit + CGB_TAIL_HALF_DOTS),
        "core_revision": source_commit,
        "build_qualified": "true",
        "predicate.ready": "a5",
        "predicate.progress": "01",
        "frame.rolling555": "c" * 64,
        "pcm_sha256": "d" * 64,
        "pcm_samples": "1",
        "pcm_audible": "false",
        "pcm.window.left.peak_to_peak": "0",
        "pcm.window.left.changes": "0",
        "pcm.window.right.peak_to_peak": "0",
        "pcm.window.right.changes": "0",
    }
    marks = expected_mark_times(script)
    for label, color in CHECKPOINT_COLORS.items():
        requested = hit if label == "hit" else marks[label]
        fields[f"checkpoint.{label}.requested_half_dots"] = str(requested)
        fields[f"checkpoint.{label}.completion_half_dots"] = str(requested + 100)
        fields[f"checkpoint.{label}.frame555"] = expected_solid_rgb555_digest(color)
    return fields


def synthetic_receipt(fields: dict[str, str]) -> str:
    receipt = {
        "profile": fields["profile"], "execution_mode": fields["execution_mode"],
        "frame_format": fields["frame_format"], "evidence_class": fields["evidence_class"],
        "rom_sha256": fields["rom_sha256"], "rom_size": fields["rom_size"],
        "input_sha256": fields["input_sha256"], "predicate": fields["predicate_name"],
        "budget_half_dots": fields["budget_half_dots"], "end_half_dots": fields["end_half_dots"],
        "t_hit_half_dots": fields["t_hit_half_dots"], "core_revision": fields["core_revision"],
        "build_qualified": fields["build_qualified"], "frame_rolling555": fields["frame.rolling555"],
        "pcm_sha256": fields["pcm_sha256"], "pcm_samples": fields["pcm_samples"],
        "pcm_audible": fields["pcm_audible"],
        "pcm_left_peak_to_peak": fields["pcm.window.left.peak_to_peak"],
        "pcm_left_changes": fields["pcm.window.left.changes"],
        "pcm_right_peak_to_peak": fields["pcm.window.right.peak_to_peak"],
        "pcm_right_changes": fields["pcm.window.right.changes"],
    }
    for label in CHECKPOINT_COLORS:
        receipt[f"checkpoint_{label}_requested_half_dots"] = fields[
            f"checkpoint.{label}.requested_half_dots"]
        receipt[f"checkpoint_{label}_completion_half_dots"] = fields[
            f"checkpoint.{label}.completion_half_dots"]
        receipt[f"checkpoint_{label}_frame"] = fields[f"checkpoint.{label}.frame555"]
    return "receipt id=cgb-control-progress " + " ".join(
        f"{name}={value}" for name, value in receipt.items())


def self_test(repo_root: Path) -> None:
    if parse_runner_timeout(str(DEFAULT_RUNNER_TIMEOUT_SECONDS)) != DEFAULT_RUNNER_TIMEOUT_SECONDS or \
            parse_runner_timeout("90") != 90:
        raise CheckError("self-test-runner-timeout-policy-failed")
    for invalid_timeout in ("0", "-1", "121", "30.5", "invalid"):
        try:
            parse_runner_timeout(invalid_timeout)
        except argparse.ArgumentTypeError:
            continue
        raise CheckError("self-test-runner-timeout-control-failed")
    if normalized_host_path(r"C:\Runner\Temp\failure-dumps\control.ppm") != \
            normalized_host_path(r"C:\Runner\Temp\failure-dumps/control.ppm"):
        raise CheckError("self-test-host-path-normalization-failed")
    expected_path = r"C:\Users\Jane Doe\Temp\failure-dumps\control.ppm"
    mixed_path = "acceptance id=control ppm=C:\\Users\\Jane Doe\\Temp\\failure-dumps/control.ppm\n"
    parsed_path = re.search(r"(?:^|\s)ppm=([^\r\n]+)", mixed_path)
    if parsed_path is None or normalized_host_path(parsed_path.group(1).rstrip()) != \
            normalized_host_path(expected_path):
        raise CheckError("self-test-host-path-with-spaces-failed")
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
    source_commit = "a" * 40
    complete = synthetic_progress_fields(rom, positive, source_commit)
    validate_progress_fields(complete, observation=True, rom=rom, script=positive,
                             source_commit=source_commit, require_predicate_state=True)
    receipt = synthetic_receipt(complete)
    validate_native_receipt(receipt, rom, positive, source_commit)
    compare_observation_receipt(complete, token_fields(receipt, "receipt"))

    fields_to_mutate = (
        "profile", "execution_mode", "frame_format", "evidence_class", "rom_sha256", "rom_size",
        "input_sha256", "predicate_name", "budget_half_dots", "core_revision", "build_qualified",
        "t_hit_half_dots", "end_half_dots", "frame.rolling555",
        "pcm_sha256", "pcm_samples", "pcm_audible", "pcm.window.left.peak_to_peak",
        "pcm.window.left.changes", "pcm.window.right.peak_to_peak", "pcm.window.right.changes",
        "predicate.ready", "predicate.progress",
    ) + tuple(f"checkpoint.{label}.{field}" for label in CHECKPOINT_COLORS
              for field in ("requested_half_dots", "completion_half_dots", "frame555"))
    for field in fields_to_mutate:
        mutated = dict(complete)
        mutated[field] = "1" if mutated[field] != "1" else "0"
        expect_rejected(lambda: validate_progress_fields(
            mutated, observation=True, rom=rom, script=positive, source_commit=source_commit,
            require_predicate_state=True), "", f"observation-{field}")

    receipt_fields = token_fields(receipt, "receipt")
    receipt_fields_to_mutate = (
        "profile", "execution_mode", "frame_format", "evidence_class", "rom_sha256", "rom_size",
        "input_sha256", "predicate", "budget_half_dots", "core_revision", "build_qualified",
        "t_hit_half_dots", "end_half_dots", "frame_rolling555", "pcm_sha256", "pcm_samples", "pcm_audible",
        "pcm_left_peak_to_peak", "pcm_left_changes", "pcm_right_peak_to_peak", "pcm_right_changes",
    ) + tuple(f"checkpoint_{label}_{field}" for label in CHECKPOINT_COLORS
              for field in ("requested_half_dots", "completion_half_dots", "frame"))
    for field in receipt_fields_to_mutate:
        mutated = dict(receipt_fields)
        mutated[field] = "1" if mutated[field] != "1" else "0"
        line = "receipt id=cgb-control-progress " + " ".join(
            f"{name}={value}" for name, value in mutated.items())
        expect_rejected(lambda: validate_native_receipt(line, rom, positive, source_commit),
                        "", f"receipt-{field}")

    with tempfile.TemporaryDirectory(prefix="gbb-cgb-observation-self-test-") as temp:
        ppm = Path(temp) / "checkpoint.ppm"
        expected_blue = solid_rgb555_ppm(CHECKPOINT_COLORS["title"])
        ppm.write_bytes(expected_blue)
        validate_checkpoint_dump(ppm, "title", complete["checkpoint.title.frame555"])
        ppm.write_bytes(solid_rgb555_ppm(0x001E))
        expect_rejected(lambda: validate_checkpoint_dump(
            ppm, "title", complete["checkpoint.title.frame555"]),
            "checkpoint-dump-color-invalid", "dump-stale")
        source_color = CHECKPOINT_COLORS["title"]
        CHECKPOINT_COLORS["title"] = 0x001E
        try:
            ppm.write_bytes(expected_blue)
            expect_rejected(lambda: validate_checkpoint_dump(
                ppm, "title", complete["checkpoint.title.frame555"]),
                "checkpoint-dump-color-invalid", "expected-color")
        finally:
            CHECKPOINT_COLORS["title"] = source_color
        wrong_format = bytearray(expected_blue)
        wrong_format[:len(PPM_HEADER)] = b"P5\n160 144\n255\n"
        ppm.write_bytes(wrong_format)
        expect_rejected(lambda: validate_checkpoint_dump(
            ppm, "title", complete["checkpoint.title.frame555"]),
            "checkpoint-dump-format-invalid", "dump-format")
        ppm.write_bytes(expected_blue[:-1])
        expect_rejected(lambda: validate_checkpoint_dump(
            ppm, "title", complete["checkpoint.title.frame555"]),
            "checkpoint-dump-size-invalid", "dump-truncated")
        ppm.unlink()
        expect_rejected(lambda: validate_checkpoint_dump(
            ppm, "title", complete["checkpoint.title.frame555"]),
            "checkpoint-dump-missing", "dump-missing")

    expect_rejected(lambda: validate_source_snapshot(b"committed", b"changed", {}),
                    "checker-source-mismatch", "source-mismatch")
    expect_rejected(lambda: validate_source_snapshot(b"committed", b"committed", {},
                    {"src/runner/acceptance.c": ("missing-source-evidence",)}),
                    "source-evidence-missing", "missing-committed-evidence")
    checker_path = Path(__file__).resolve()
    checker_relative = checker_path.relative_to(repo_root).as_posix()
    current_commit_checker = git_text_bytes(
        repo_root, ["show", f"HEAD:{checker_relative}"])
    if current_commit_checker == checker_path.read_bytes():
        stale_revision = find_stale_source_revision(
            repo_root, git_text(repo_root, ["rev-list", "--max-count=64", "HEAD"]).splitlines(),
            checker_relative, current_commit_checker)
        if stale_revision is not None:
            expect_rejected(lambda: verify_source_identity(repo_root, stale_revision, checker_path),
                            "checker-source-mismatch", "source-revision-mismatch")
        original_runner_facts = SOURCE_FACTS["src/runner/acceptance.c"]
        SOURCE_FACTS["src/runner/acceptance.c"] = (*original_runner_facts, "missing-evidence-control")
        try:
            expect_rejected(lambda: verify_source_identity(repo_root, "HEAD", checker_path),
                            "source-fact-missing", "missing-committed-source-fact")
        finally:
            SOURCE_FACTS["src/runner/acceptance.c"] = original_runner_facts
    source_history_controls()
    expect_rejected(lambda: resolve_source_commit(repo_root, "gsd-invalid-cgb-progress-source-revision"),
                    "source-revision-invalid", "source-revision")
    print("observation-contract=pass observation-controls=pass")


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


def run_tracer(runner: Path, repo_root: Path, source_revision: str, checker_path: Path,
               runner_timeout: int) -> int:
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
            str(runner), [*args, "--case", "cgb-control-progress"], str(work), runner_timeout)
        no_input_code, no_input_out, no_input_err = helper.run_runner(
            str(runner), [*args, "--case", "cgb-control-no-input"], str(work), runner_timeout)
        impossible_code, impossible_out, impossible_err = helper.run_runner(
            str(runner), [*args, "--case", "cgb-control-impossible"], str(work), runner_timeout)
        receipt_lines = [line for line in positive_out.splitlines() if line.startswith("receipt id=")]
        if positive_code != 0 or "status=pass" not in positive_out or positive_err or len(receipt_lines) != 1:
            raise CheckError("positive-native-cgb-route-failed:" +
                             positive_out.replace(str(work), "<temp>").strip() + ":" +
                             positive_err.replace(str(work), "<temp>").strip())
        validate_native_receipt(receipt_lines[0], rom, positive, source_commit)
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


def validate_progress_negative(name: str, code: int, stdout: str, stderr: str,
                               expected_state: str) -> None:
    if (code != 1 or status_reason(stdout) != "predicate-not-reached" or
            expected_state not in stdout or "status=pass" in stdout or stderr):
        safe_out = stdout.strip()
        safe_err = stderr.strip()
        raise CheckError(f"{name}-negative-control-failed:exit={code}:{safe_out}:{safe_err}")


def run_discrimination(runner: Path, repo_root: Path, source_revision: str,
                       checker_path: Path, runner_timeout: int) -> int:
    self_test(repo_root)
    source_commit, checker_sha = verify_source_identity(repo_root, source_revision, checker_path)
    if not runner.is_file():
        raise CheckError("runner-unavailable")
    runner_sha = hashlib.sha256(runner.read_bytes()).hexdigest()
    rom, _ = build_rom()
    positive = input_script(True)
    no_input = input_script(False)
    wrong_input = input_script(True, "LEFT")
    validate_source_anchors(rom)
    if hashlib.sha256(rom).hexdigest() != CONTROL_SHA256:
        raise CheckError("rom-source-identity-mismatch")

    with tempfile.TemporaryDirectory(prefix="gbb-cgb-discrimination-") as temp:
        work = Path(temp)
        work.chmod(0o700)
        (work / "control.gb").write_bytes(rom)
        (work / "positive.input").write_bytes(positive)
        (work / "no-input.input").write_bytes(no_input)
        (work / "wrong-input.input").write_bytes(wrong_input)
        raw_lines = (
            case_line("cgb-discrimination-positive", "cgb-control-progress", "positive.input", rom, positive) +
            case_line("cgb-discrimination-no-input", "cgb-control-progress", "no-input.input", rom, no_input) +
            case_line("cgb-discrimination-wrong-input", "cgb-control-progress", "wrong-input.input", rom, wrong_input) +
            case_line("cgb-discrimination-impossible", "cgb-control-impossible", "positive.input", rom, positive)
        )
        strict_lines = (
            case_line("cgb-discrimination-strict-fail", "cgb-control-progress", "no-input.input",
                      rom, no_input, model_fail=True) +
            case_line("cgb-discrimination-strict-pass", "cgb-control-progress", "positive.input",
                      rom, positive, model_fail=True)
        )
        helper = load_host_fixture(repo_root)
        base = ["--acceptance", "cases.txt", "--model", "cgb-cpu-e", "--receipt"]

        (work / "cases.txt").write_text(raw_lines, encoding="ascii")
        for line, script in ((raw_lines.splitlines()[0], positive),
                             (raw_lines.splitlines()[1], no_input),
                             (raw_lines.splitlines()[2], wrong_input),
                             (raw_lines.splitlines()[3], positive)):
            validate_case_identity(line, rom, script)

        positive_code, positive_out, positive_err = helper.run_runner(
            str(runner), [*base, "--case", "cgb-discrimination-positive"], str(work), runner_timeout)
        positive_receipts = [line for line in positive_out.splitlines() if line.startswith("receipt id=")]
        if (positive_code != 0 or "status=pass" not in positive_out or positive_err or
                len(positive_receipts) != 1):
            raise CheckError("positive-native-cgb-route-failed:" +
                             positive_out.strip() + ":" + positive_err.strip())
        validate_native_receipt(positive_receipts[0], rom, positive, source_commit)

        negative_specs = (
            ("no-input", "cgb-discrimination-no-input", "final_ready=a5 final_progress=00"),
            ("wrong-input", "cgb-discrimination-wrong-input", "final_ready=a5 final_progress=00"),
            ("impossible", "cgb-discrimination-impossible", "final_ready=a5 final_progress=01"),
        )
        for name, identifier, final_state in negative_specs:
            code, stdout, stderr = helper.run_runner(
                str(runner), [*base, "--case", identifier, "--raw-verdict"], str(work), runner_timeout)
            validate_progress_negative(name, code, stdout, stderr, final_state)

        (work / "cases.txt").write_text(raw_lines + strict_lines, encoding="ascii")
        for index, script in enumerate((no_input, positive)):
            validate_case_identity(strict_lines.splitlines()[index], rom, script)
        strict_code, strict_out, strict_err = helper.run_runner(
            str(runner), [*base, "--case", "cgb-discrimination-strict-fail"], str(work), runner_timeout)
        if (strict_code != 0 or "status=xfail" not in strict_out or
                "reason=predicate-not-reached" not in strict_out or
                "final_ready=a5 final_progress=00" not in strict_out or strict_err):
            raise CheckError(f"strict-xfail-control-failed:exit={strict_code}:{strict_out.strip()}:{strict_err.strip()}")
        unexpected_code, unexpected_out, unexpected_err = helper.run_runner(
            str(runner), [*base, "--case", "cgb-discrimination-strict-pass"], str(work), runner_timeout)
        if (unexpected_code != 1 or "status=unexpected-pass" not in unexpected_out or
                "status=pass" in unexpected_out or unexpected_err):
            raise CheckError(f"unexpected-pass-control-failed:exit={unexpected_code}:"+
                             f"{unexpected_out.strip()}:{unexpected_err.strip()}")

    print("cgb-discrimination status=pass controls=positive,no-input,wrong-input,impossible,strict-xfail,unexpected-pass "
          f"source_revision={source_commit} checker_sha256={checker_sha} runner_sha256={runner_sha} "
          f"rom_sha256={hashlib.sha256(rom).hexdigest()} positive_input_sha256={hashlib.sha256(positive).hexdigest()} "
          f"no_input_sha256={hashlib.sha256(no_input).hexdigest()} wrong_input_sha256={hashlib.sha256(wrong_input).hexdigest()}")
    return 0


def run_observations(runner: Path, repo_root: Path, source_revision: str,
                     checker_path: Path, runner_timeout: int) -> int:
    self_test(repo_root)
    source_commit, checker_sha = verify_source_identity(repo_root, source_revision, checker_path)
    if not runner.is_file():
        raise CheckError("runner-unavailable")
    runner_sha = hashlib.sha256(runner.read_bytes()).hexdigest()
    rom, _ = build_rom()
    script = input_script(True)
    no_input = input_script(False)
    if hashlib.sha256(rom).hexdigest() != CONTROL_SHA256:
        raise CheckError("rom-source-identity-mismatch")
    with tempfile.TemporaryDirectory(prefix="gbb-cgb-observations-") as temp:
        work = Path(temp)
        work.chmod(0o700)
        (work / "control.gb").write_bytes(rom)
        (work / "positive.input").write_bytes(script)
        (work / "no-input.input").write_bytes(no_input)
        cases = (
            case_line("cgb-control-progress", "cgb-control-progress", "positive.input", rom, script) +
            case_line("cgb-control-no-input", "cgb-control-progress", "no-input.input", rom, no_input)
        )
        (work / "cases.txt").write_text(cases, encoding="ascii")
        helper = load_host_fixture(repo_root)
        base = ["--acceptance", "cases.txt", "--case", "cgb-control-progress", "--model", "cgb-cpu-e"]
        observed_runs: list[dict[str, str]] = []
        receipt_runs: list[dict[str, str]] = []
        dump_runs: list[Path] = []
        for run_name in ("first", "repeat"):
            dump_dir = work / f"dumps-{run_name}"
            dump_dir.mkdir(mode=0o700)
            code, stdout, stderr = helper.run_runner(
                str(runner), [*base, "--observe", "--receipt", "--dump-checkpoints", str(dump_dir)],
                str(work), runner_timeout)
            if code != 0 or stderr:
                raise CheckError(f"observation-run-failed:{run_name}:{code}:{stdout.strip()}:{stderr.strip()}")
            observed_runs.append(validate_observation(stdout, rom, script, source_commit))
            receipt_lines = [line for line in stdout.splitlines() if line.startswith("receipt id=")]
            if len(receipt_lines) != 1:
                raise CheckError(f"observation-receipt-missing:{run_name}")
            receipt_runs.append(validate_native_receipt(receipt_lines[0], rom, script, source_commit))
            dump_runs.append(dump_dir)

        first, repeat = observed_runs
        if first != repeat:
            raise CheckError("observation-repeat-mismatch")
        if receipt_runs[0] != receipt_runs[1]:
            raise CheckError("receipt-repeat-mismatch")
        compare_observation_receipt(first, receipt_runs[0])
        for label, expected_color in CHECKPOINT_COLORS.items():
            expected_digest = expected_solid_rgb555_digest(expected_color)
            for dump_dir in dump_runs:
                validate_checkpoint_dump(dump_dir / f"cgb-control-progress.{label}.ppm",
                                         label, expected_digest)
                if (dump_dir / f"cgb-control-progress.{label}.ppm").read_bytes() != (
                        dump_runs[0] / f"cgb-control-progress.{label}.ppm").read_bytes():
                    raise CheckError(f"observation-repeat-dump-mismatch:{label}")

        failure_dir = work / "failure-dumps"
        failure_dir.mkdir(mode=0o700)
        failure_ppm = failure_dir / "cgb-control-no-input.ppm"
        stale_failure = solid_rgb555_ppm(CHECKPOINT_COLORS["hit"])
        failure_ppm.write_bytes(stale_failure)
        failure_code, failure_out, failure_err = helper.run_runner(
            str(runner), ["--acceptance", "cases.txt", "--case", "cgb-control-no-input",
                          "--model", "cgb-cpu-e", "--failure-dir", str(failure_dir)], str(work), runner_timeout)
        reported_ppm = re.search(r"(?:^|\s)ppm=([^\r\n]+)", failure_out)
        if (failure_code != 1 or status_reason(failure_out) != "predicate-not-reached" or failure_err or
                "final_ready=a5 final_progress=00" not in failure_out or
                reported_ppm is None or
                normalized_host_path(reported_ppm.group(1).rstrip()) != normalized_host_path(str(failure_ppm))):
            raise CheckError("cgb-failure-dump-control-failed:" + failure_out.strip() + ":" + failure_err.strip())
        validate_checkpoint_dump(failure_ppm, "title", expected_solid_rgb555_digest(CHECKPOINT_COLORS["title"]))
        if failure_ppm.read_bytes() == stale_failure:
            raise CheckError("cgb-failure-dump-stale")

    print("cgb-observations status=pass controls=same-run-identity,receipt,repeat,pixel-colors,fresh-failure-dump "
          f"source_revision={source_commit} checker_sha256={checker_sha} runner_sha256={runner_sha} "
          f"rom_sha256={hashlib.sha256(rom).hexdigest()} input_sha256={hashlib.sha256(script).hexdigest()}")
    return 0


def run_compatibility(runner: Path, repo_root: Path, source_revision: str,
                      checker_path: Path, runner_timeout: int) -> int:
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
                          "--model", "cgb-cpu-e", "--receipt"], str(work), runner_timeout)
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
    parser.add_argument("--runner-timeout", type=parse_runner_timeout,
                        default=DEFAULT_RUNNER_TIMEOUT_SECONDS)
    parser.add_argument("--tracer", action="store_true")
    parser.add_argument("--discrimination", action="store_true")
    parser.add_argument("--compatibility", action="store_true")
    parser.add_argument("--observations", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    try:
        if args.repo_root is None:
            raise CheckError("repo-root-required")
        repo_root = args.repo_root.resolve()
        if args.self_test:
            self_test(repo_root)
            print("verify-cgb-progress self-test pass "
                  "controls=observation-identity,time,digest,pcm,dumps,source-history,git-hooks")
            return 0
        if args.tracer:
            if args.runner is None or args.source_revision is None:
                raise CheckError("runner-and-source-revision-required")
            return run_tracer(args.runner.resolve(), repo_root, args.source_revision,
                              Path(__file__).resolve(), args.runner_timeout)
        if args.discrimination:
            if args.runner is None or args.source_revision is None:
                raise CheckError("runner-and-source-revision-required")
            return run_discrimination(args.runner.resolve(), repo_root, args.source_revision,
                                      Path(__file__).resolve(), args.runner_timeout)
        if args.compatibility:
            if args.runner is None or args.source_revision is None:
                raise CheckError("runner-and-source-revision-required")
            return run_compatibility(args.runner.resolve(), repo_root, args.source_revision,
                                     Path(__file__).resolve(), args.runner_timeout)
        if args.observations:
            if args.runner is None or args.source_revision is None:
                raise CheckError("runner-and-source-revision-required")
            return run_observations(args.runner.resolve(), repo_root, args.source_revision,
                                    Path(__file__).resolve(), args.runner_timeout)
        raise CheckError("select-self-test-or-tracer")
    except (CheckError, OSError, TimeoutError, ValueError) as error:
        reason = error.reason if isinstance(error, CheckError) else str(error)
        print(f"verify-cgb-progress: {reason}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
