#!/usr/bin/env python3
"""Exercise dense acceptance input against the frozen DMG ledger and a source mutant."""

from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[2]
BASELINE = ROOT / "tests/baseline/dmg-cpu-b-v1.txt"
BASE_CASES = ROOT / "tests/acceptance/cases.txt"
BASE_SCRIPT = ROOT / "tests/acceptance/inputs/libbet-tutorial.input"
MUTANT_ANCHOR = "        *cursor += applied;\n"
MUTANT_REPLACEMENT = (
    MUTANT_ANCHOR
    + "        if (applied != 0u) {\n"
    + "            while (*cursor < m->accept_input_span->count &&\n"
    + "                   m->accept_input_span->events[*cursor].at_half_dots == m->time_half_dots) ++*cursor;\n"
    + "        }\n"
)
BASELINE_COMMIT = "7cc6495e64f3645caa120e7458f754585b788985"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def run(command: list[str], *, cwd: Path, timeout: int = 300) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, text=True, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT, timeout=timeout, check=False)


def expect_run(command: list[str], *, cwd: Path, status: int, reason: str | None = None) -> str:
    result = run(command, cwd=cwd)
    require(result.returncode == status,
            f"command exit {result.returncode}, expected {status}: {' '.join(command)}\n{result.stdout}")
    if reason is not None:
        require(reason in result.stdout, f"missing {reason!r} from command output:\n{result.stdout}")
    return result.stdout


def read_baseline() -> dict[str, str]:
    values: dict[str, str] = {}
    for line in BASELINE.read_text(encoding="utf-8").splitlines():
        if "\t" in line:
            key, value = line.split("\t", 1)
            values[key] = value
    return values


def receipt_fields(output: str) -> dict[str, str]:
    line = next((line for line in output.splitlines() if line.startswith("receipt id=")), None)
    require(line is not None, f"successful runner output has no receipt:\n{output}")
    return dict(part.split("=", 1) for part in line.split() if "=" in part)


def acceptance_fields(output: str) -> dict[str, str]:
    line = next((line for line in output.splitlines()
                 if line.startswith("acceptance id=libbet-dense status=pass ")), None)
    require(line is not None, f"successful runner output has no acceptance result:\n{output}")
    return dict(part.split("=", 1) for part in line.split() if "=" in part)


def dense_fixture(directory: Path, repo_root: Path = ROOT) -> tuple[Path, Path]:
    script_text = BASE_SCRIPT.read_text(encoding="utf-8")
    original = "tap START 3f"
    require(script_text.count(original) == 1, "Libbet script no longer has one START tap to densify")
    burst = "\n".join(["tap A 0hd"] * 33 + [original])
    script_text = script_text.replace(original, burst, 1)
    script_path = directory / "dense.input"
    script_path.write_text(script_text, encoding="utf-8", newline="\n")
    digest = hashlib.sha256(script_text.encode("utf-8")).hexdigest()

    row = next((line for line in BASE_CASES.read_text(encoding="utf-8").splitlines()
                if line.startswith("id=libbet ")), None)
    require(row is not None, "frozen acceptance case libbet is missing")
    fields = dict(part.split("=", 1) for part in row.split())
    relative_script = script_path.relative_to(repo_root).as_posix()
    fields["id"] = "libbet-dense"
    fields["input_script"] = relative_script
    fields["input_sha256"] = digest
    fields["budget_half_dots"] = "150000000"
    case_path = directory / "dense-cases.txt"
    case_path.write_text(" ".join(f"{key}={value}" for key, value in fields.items()) + "\n",
                         encoding="utf-8", newline="\n")
    return script_path, case_path


def copy_tracked_source(destination: Path) -> None:
    listed = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, check=True,
                            stdout=subprocess.PIPE).stdout.split(b"\0")
    for raw_path in listed:
        if not raw_path:
            continue
        relative = Path(os.fsdecode(raw_path))
        if relative.parts[0] in {".planning", ".codex", ".agents", "build"}:
            continue
        source = ROOT / relative
        target = destination / relative
        if not source.is_file():
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        if source.is_symlink():
            resolved = source.resolve()
            require(resolved == ROOT or ROOT in resolved.parents,
                    f"tracked symlink escapes checkout: {relative}")
            shutil.copyfile(resolved, target)
        else:
            shutil.copy2(source, target)


def create_baseline_object_store(destination: Path) -> None:
    destination.mkdir()
    initialized = run(["git", "init", "--bare", str(destination)], cwd=ROOT)
    require(initialized.returncode == 0, f"baseline object store init failed:\n{initialized.stdout}")
    fetched = run(["git", "--git-dir", str(destination), "fetch", "--no-tags",
                  str(ROOT), BASELINE_COMMIT], cwd=ROOT)
    require(fetched.returncode == 0, f"fixed baseline object copy failed:\n{fetched.stdout}")
    verified = run(["git", "--git-dir", str(destination), "cat-file", "-e",
                    f"{BASELINE_COMMIT}^{{commit}}"], cwd=ROOT)
    require(verified.returncode == 0, "copied baseline object did not verify at its full commit identity")


def check_repository(subject: Path, evidence: Path | None, expected: str) -> None:
    command = [sys.executable, "-I", str(subject / "tests/scripts/verify-fixture-admission.py"),
               "--check-repository", "--repo-root", str(subject)]
    if evidence is not None:
        command.extend(("--baseline-object-root", str(evidence)))
    result = run(command, cwd=subject)
    require(result.returncode == 1 and expected in result.stdout,
            f"expected admission rejection {expected!r}, got exit={result.returncode}:\n{result.stdout}")


def verify_documentation_contract() -> None:
    text = (ROOT / "docs/game-acceptance.md").read_text(encoding="utf-8")
    for phrase in ("private, immutable event span", "16,384-event limit", "existing 64-event queue",
                   "same-time transition before the next guest tick", "caller-managed batches"):
        require(phrase in text, f"game-acceptance documentation is missing contract phrase: {phrase}")
    require("Input scripts denser than the core's 64-event queue can drain are not supported." not in text,
            "game-acceptance documentation still states the pre-repair dense-input limitation")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true", required=True,
                        help="run the dense-input positive and negative controls")
    parser.add_argument("--build-dir", type=Path, required=True,
                        help="isolated build containing gabbaboy-runner")
    args = parser.parse_args()
    build_dir = args.build_dir if args.build_dir.is_absolute() else ROOT / args.build_dir
    runner = build_dir / "gabbaboy-runner"
    if not runner.is_file():
        runner = build_dir / "gabbaboy-runner.exe"
    require(runner.is_file(), f"runner not found in {build_dir}; build gabbaboy-runner first")
    runner = runner.resolve()
    baseline = read_baseline()
    verify_documentation_contract()

    with tempfile.TemporaryDirectory(prefix="dense-input-", dir=ROOT) as temp_name:
        temp = Path(temp_name)
        _, case_path = dense_fixture(temp)
        positive = expect_run([str(runner), "--acceptance", str(case_path), "--case", "libbet-dense",
                               "--receipt"], cwd=ROOT, status=0)
        require("acceptance id=libbet-dense status=pass" in positive,
                f"dense adopter did not pass:\n{positive}")
        fields = {**acceptance_fields(positive), **receipt_fields(positive)}
        comparisons = {
            "t_hit_half_dots": "acceptance.libbet.t_hit_half_dots",
            "frame_title": "acceptance.libbet.checkpoint.title.frame",
            "frame_play_start": "acceptance.libbet.checkpoint.play_start.frame",
            "frame_mid": "acceptance.libbet.checkpoint.mid.frame",
            "frame_hit": "acceptance.libbet.checkpoint.hit.frame",
            "frame_rolling": "acceptance.libbet.frame.rolling",
            "pcm_sha256": "acceptance.libbet.pcm_sha256",
        }
        for receipt_key, baseline_key in comparisons.items():
            require(fields.get(receipt_key) == baseline.get(baseline_key),
                    f"dense {receipt_key}={fields.get(receipt_key)!r} differs from frozen "
                    f"{baseline_key}={baseline.get(baseline_key)!r}")

        diagnostic_dir = temp / "failure"
        diagnostic_dir.mkdir()
        negative = expect_run([str(runner), "--acceptance", str(case_path), "--case", "libbet-dense",
                              "--mutate", "drop:START", "--raw-verdict", "--failure-dir",
                              str(diagnostic_dir)], cwd=ROOT, status=1,
                             reason="reason=predicate-not-reached")
        require("status=fail" in negative, "START-drop replay did not report an explicit failed status")
        require("status=pass" not in negative, "failed dense replay emitted success output")
        stall = diagnostic_dir / "libbet-dense.stall.txt"
        require(stall.is_file(), "failing dense replay did not produce its stall diagnostic")
        stall_bytes = stall.read_bytes()
        require(len(stall_bytes) <= 65536, f"stall diagnostic exceeded 64 KiB: {len(stall_bytes)}")
        require(b"stall id=libbet-dense reason=predicate-not-reached" in stall_bytes,
                "stall diagnostic lacks the intended predicate failure")

        with tempfile.TemporaryDirectory(prefix="dense-input-mutant-") as mutant_name:
            mutant_root = Path(mutant_name) / "source"
            mutant_build = Path(mutant_name) / "build"
            baseline_object_root = Path(mutant_name) / "trusted-baseline.git"
            mutant_root.mkdir()
            copy_tracked_source(mutant_root)
            create_baseline_object_store(baseline_object_root)
            check_repository(mutant_root, None, "REJECT baseline-object-unavailable:")
            empty_evidence = Path(mutant_name) / "empty-baseline.git"
            empty_evidence.mkdir()
            initialized = run(["git", "init", "--bare", str(empty_evidence)], cwd=ROOT)
            require(initialized.returncode == 0, f"empty baseline store init failed:\n{initialized.stdout}")
            check_repository(mutant_root, empty_evidence, "REJECT baseline-object-unavailable:")
            wrong_evidence = Path(mutant_name) / "wrong-baseline.git"
            unrelated_source = Path(mutant_name) / "unrelated-source"
            wrong_evidence.mkdir()
            unrelated_source.mkdir()
            initialized = run(["git", "init", "--bare", str(wrong_evidence)], cwd=ROOT)
            require(initialized.returncode == 0, f"wrong baseline store init failed:\n{initialized.stdout}")
            initialized = run(["git", "init", str(unrelated_source)], cwd=ROOT)
            require(initialized.returncode == 0, f"unrelated source repository init failed:\n{initialized.stdout}")
            unrelated_commit = run(["git", "-C", str(unrelated_source), "-c", "user.name=Fixture Control",
                                    "-c", "user.email=fixture-control@example.invalid", "commit", "--allow-empty",
                                    "-m", "unrelated baseline identity"], cwd=ROOT)
            require(unrelated_commit.returncode == 0, f"unrelated identity creation failed:\n{unrelated_commit.stdout}")
            unrelated_identity = run(["git", "-C", str(unrelated_source), "rev-parse", "HEAD"], cwd=ROOT)
            require(unrelated_identity.returncode == 0, f"unrelated identity lookup failed:\n{unrelated_identity.stdout}")
            fetched_wrong = run(["git", "--git-dir", str(wrong_evidence), "fetch", "--no-tags",
                                 str(unrelated_source), unrelated_identity.stdout.strip()], cwd=ROOT)
            require(fetched_wrong.returncode == 0, f"wrong identity object copy failed:\n{fetched_wrong.stdout}")
            check_repository(mutant_root, wrong_evidence, "REJECT baseline-object-unavailable:")
            core_path = mutant_root / "src/core/gabbaboy.c"
            core = core_path.read_text(encoding="utf-8")
            require(core.count(MUTANT_ANCHOR) == 1,
                    "no-refill mutant anchor must occur exactly once")
            core_path.write_text(core.replace(MUTANT_ANCHOR, MUTANT_REPLACEMENT, 1),
                                 encoding="utf-8", newline="\n")
            mutant_case_dir = mutant_root / "dense-input-fixture"
            mutant_case_dir.mkdir()
            mutant_script, mutant_case = dense_fixture(mutant_case_dir, mutant_root)
            mutant_configure = run(["cmake", "-S", str(mutant_root), "-B", str(mutant_build),
                                    "-G", "Ninja", "-DCMAKE_BUILD_TYPE=Debug", "-DBUILD_TESTING=ON",
                                    f"-DGABBABOY_FIXTURE_BASELINE_OBJECT_ROOT={baseline_object_root}"],
                                   cwd=mutant_root, timeout=180)
            require(mutant_configure.returncode == 0,
                    f"mutant CMake configure failed:\n{mutant_configure.stdout}")
            ninja_files = (mutant_build / "build.ninja").read_text(encoding="utf-8")
            gitless_core_definitions = [
                line for line in ninja_files.splitlines()
                if '-DGBB_BUILD_REVISION=\\"unknown\\"' in line and
                "-DGBB_BUILD_QUALIFIED=0" in line
            ]
            require(gitless_core_definitions,
                    "gitless source archive did not retain the unqualified unknown revision")
            mutant_compile = run(["cmake", "--build", str(mutant_build), "--target", "gabbaboy-runner"],
                                 cwd=mutant_root, timeout=300)
            require(mutant_compile.returncode == 0,
                    f"mutant runner build failed:\n{mutant_compile.stdout}")
            mutant_runner = mutant_build / "gabbaboy-runner"
            if not mutant_runner.is_file():
                mutant_runner = mutant_build / "gabbaboy-runner.exe"
            require(mutant_runner.is_file(), "mutant build did not produce gabbaboy-runner")
            mutant = expect_run([str(mutant_runner), "--acceptance", str(mutant_case),
                                "--case", "libbet-dense", "--raw-verdict"],
                               cwd=mutant_root, status=1,
                               reason="reason=predicate-not-reached")
            require("status=fail" in mutant, "no-refill mutant did not report an explicit failed status")
            require("status=pass" not in mutant and "receipt id=" not in mutant,
                    "no-refill mutant emitted success or a successful receipt")

            changed_subject = Path(mutant_name) / "changed-subject"
            changed_subject.mkdir()
            copy_tracked_source(changed_subject)
            changed_fixture = changed_subject / "fixtures/tracer/tracer.gb"
            require(changed_fixture.is_file(), "fixture-byte negative-control input is missing")
            changed_fixture.write_bytes(changed_fixture.read_bytes() + b"\ncontrolled mutation\n")
            check_repository(changed_subject, baseline_object_root, "REJECT record-field-missing:")

        print("dense-input status=pass ordered_events=67 same_timestamp=true")
        print("dense-input baseline=pass fields=" + ",".join(comparisons))
        print("dense-input documentation-contract=pass stale-limit-control=pass")
        print("dense-input failure-diagnostic=pass capped_bytes=" + str(len(stall_bytes)))
        print("dense-input no-refill-mutant=failed-as-expected reason=predicate-not-reached")
        print("dense-input immutable-baseline=separate-object-store full-identity=verified")
        print("dense-input baseline-controls=missing-object,wrong-identity,changed-fixture-rejected")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, subprocess.TimeoutExpired) as error:
        print(f"verify-dense-input: FAIL: {error}", file=sys.stderr)
        raise SystemExit(1)
