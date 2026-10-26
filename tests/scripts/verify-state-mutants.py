#!/usr/bin/env python3
"""Compile disposable state-codec mutants and require the named contract tests to kill them."""

from __future__ import annotations

import argparse
import re
import subprocess
import tempfile
from pathlib import Path


class MutantError(Exception):
    pass


def run(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(command, cwd=cwd, text=True, capture_output=True,
                              check=False, timeout=25)
    except subprocess.TimeoutExpired as error:
        raise MutantError(f"mutant command timed out: {' '.join(command)}") from error


def git_show(repo: Path, rev: str, path: str) -> str:
    if not re.fullmatch(r"[0-9a-f]{40}", rev):
        raise MutantError("--rev must be a resolved immutable 40-hex commit")
    result = run(["git", "show", f"{rev}:{path}"], repo)
    if result.returncode != 0:
        raise MutantError(f"git show {rev}:{path} failed: {result.stderr.strip()}")
    return result.stdout


def replace_once(source: str, original: str, replacement: str, mutant: str) -> str:
    count = source.count(original)
    if count != 1:
        raise MutantError(f"{mutant} seed expected one source anchor, found {count}")
    return source.replace(original, replacement, 1)


def materialize(root: Path, core: str, test: str, headers: dict[str, str]) -> None:
    (root / "src/core").mkdir(parents=True)
    (root / "tests").mkdir(parents=True)
    (root / "include/gabbaboy").mkdir(parents=True)
    (root / "src/core/gabbaboy.c").write_text(core)
    (root / "tests/test_state_codec.c").write_text(test)
    for relative, contents in headers.items():
        (root / relative).write_text(contents)


def build(root: Path, cc: str, version: tuple[int, int, int], *, pcm_override: bool) -> Path:
    exe = root / "state-codec-mutant"
    command = [cc, "-std=c17", "-O0", "-g",
               f"-DGBB_STATE_RELEASE_MAJOR={version[0]}",
               f"-DGBB_STATE_RELEASE_MINOR={version[1]}",
               f"-DGBB_STATE_RELEASE_PATCH={version[2]}",
               "-I", str(root / "include"), "-I", str(root / "src/core")]
    if pcm_override:
        command.append("-DGBB_TEST_CGB_PCM_WRITABLE=1")
    command.extend([str(root / "tests/test_state_codec.c"), "-o", str(exe)])
    result = run(command, root)
    if result.returncode != 0:
        raise MutantError(f"mutant compile failed ({result.returncode}): {result.stdout}{result.stderr}")
    return exe


def check_pass(exe: Path, case: str) -> None:
    result = run([str(exe), case], exe.parent)
    if result.returncode != 0:
        raise MutantError(f"unmutated {case} control failed ({result.returncode}): {result.stdout}{result.stderr}")


def check_killed(exe: Path, case: str, diagnostic: str, label: str) -> str:
    result = run([str(exe), case], exe.parent)
    output = result.stdout + result.stderr
    if result.returncode == 0:
        raise MutantError(f"{label} mutant survived {case}: {output}")
    if diagnostic not in output:
        raise MutantError(f"{label} mutant failed outside its intended assertion; expected {diagnostic!r}: {output}")
    return next(line for line in output.splitlines() if diagnostic in line)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rev", required=True)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--cc", required=True)
    args = parser.parse_args()
    repo = args.repo.resolve()
    try:
        core = git_show(repo, args.rev, "src/core/gabbaboy.c")
        test = git_show(repo, args.rev, "tests/test_state_codec.c")
        cmake = git_show(repo, args.rev, "CMakeLists.txt")
        version_match = re.search(r"project\(GabbaBoy VERSION (\d+)\.(\d+)\.(\d+)", cmake)
        if version_match is None:
            raise MutantError("immutable CMakeLists.txt has no three-part GabbaBoy project version")
        version = tuple(int(part) for part in version_match.groups())
        headers = {
            "include/gabbaboy/gabbaboy.h": git_show(repo, args.rev, "include/gabbaboy/gabbaboy.h"),
            "src/core/gabbaboy_test.h": git_show(repo, args.rev, "src/core/gabbaboy_test.h"),
            "src/core/gbb_accept_input.h": git_show(repo, args.rev, "src/core/gbb_accept_input.h"),
        }
        with tempfile.TemporaryDirectory(prefix="gabbaboy-state-mutants-") as temp:
            scratch = Path(temp)
            baseline_root = scratch / "baseline"
            baseline_root.mkdir()
            materialize(baseline_root, core, test, headers)
            baseline_exe = build(baseline_root, args.cc, version, pcm_override=True)
            for case in ("state_canonical", "state_semantic_bounds", "state_override_isolation"):
                check_pass(baseline_exe, case)

            normalization_anchor = "const uint64_t raw = state_get_u64(body + offset, field->wire_width);"
            normalization_mutant = replace_once(core, normalization_anchor,
                "uint64_t raw = state_get_u64(body + offset, field->wire_width);\n"
                "            if (strcmp(field->path, \"apu_pulse[].envelope\") == 0 && i == 0u) raw &= 0xF8u;",
                "normalize-on-load")

            relation_anchor = "if (div != (divider_counter >> 8) || timer_signal != expected_timer_signal) return 0;"
            relation_mutant = replace_once(core, relation_anchor,
                "if (0 && (div != (divider_counter >> 8) || timer_signal != expected_timer_signal)) return 0;",
                "skipped-cross-field-check")

            endian_anchor = "if (mode == STATE_WALK_ENCODE) state_put_u64(mutable_body + offset, raw, field->wire_width);"
            endian_mutant = replace_once(core, endian_anchor,
                "if (mode == STATE_WALK_ENCODE) {\n"
                "                for (unsigned wire_byte = 0u; wire_byte < field->wire_width; ++wire_byte)\n"
                "                    mutable_body[offset + wire_byte] = (uint8_t)(raw >> ((field->wire_width - 1u - wire_byte) * 8u));\n"
                "            }",
                "big-endian-native-write")

            census_anchor = ('    { 197u, "audio_hpf_output", 4u, 2u, offsetof(gbb_instance, audio_hpf_output), sizeof(int32_t), STATE_VALUE_I32, STATE_STORAGE_INSTANCE },\n};')
            census_mutant = replace_once(core, census_anchor,
                '    { 197u, "audio_hpf_output", 4u, 2u, offsetof(gbb_instance, audio_hpf_output), sizeof(int32_t), STATE_VALUE_I32, STATE_STORAGE_INSTANCE },\n'
                '#if GBB_TEST_CGB_PCM_WRITABLE\n'
                '    { 198u, "apu_pcm_test_override", 1u, 2u, offsetof(gbb_instance, apu_pcm_test_override), sizeof(uint8_t), STATE_VALUE_U8, STATE_STORAGE_INSTANCE },\n'
                '    { 199u, "apu_pcm_test_override_valid", 1u, 1u, offsetof(gbb_instance, apu_pcm_test_override_valid), sizeof(uint8_t), STATE_VALUE_U8, STATE_STORAGE_INSTANCE },\n'
                '#endif\n};', "test-override-wire-leak")

            mutants = (
                ("normalize-on-load", normalization_mutant, False, "state_canonical", "normalization guard:"),
                ("skipped-cross-field-check", relation_mutant, False, "state_semantic_bounds", "div[0]=0x1"),
                ("native-endian-encoding", endian_mutant, False, "state_canonical", "wire endian guard:"),
                ("test-override-leakage", census_mutant, True, "state_override_isolation", "test_state_field_census(source)"),
            )
            for label, mutant_source, pcm_override, case, diagnostic in mutants:
                mutant_root = scratch / label
                mutant_root.mkdir()
                materialize(mutant_root, mutant_source, test, headers)
                exe = build(mutant_root, args.cc, version, pcm_override=pcm_override)
                detail = check_killed(exe, case, diagnostic, label)
                print(f"state mutant killed name={label} target={case} evidence={detail}")
        print(f"state mutation controls pass source={args.rev} controls=4 baseline=3")
        return 0
    except (MutantError, OSError) as error:
        parser.exit(1, f"state mutant control failure: {error}\n")


if __name__ == "__main__":
    raise SystemExit(main())
