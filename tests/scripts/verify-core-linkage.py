#!/usr/bin/env python3
"""Prove that every acceptance-linked test executable links exactly its intended core.

SCAN-LINK: several normal targets named the core twice (once directly and once through the
acceptance library), and mutant targets inherited the acceptance library's normal core next to the
mutant core. Static archives hide that: the first archive that defines gabbaboy.c's symbols wins, so
a wrong or duplicated core can still link, run, and silently test the wrong implementation.

Three independent layers, none of which accepts a generic nonzero exit as the intended failure:

1. Link lines. `ninja -t commands` gives the real link command of every executable. An executable that
   links the acceptance helpers must name exactly one core archive exactly once, the normal core for
   normal targets and a mutant core for mutant targets, never both.
2. Linked bytes. The debug records of the finished executable name the core translation unit that was
   actually pulled in. They must agree with the link line. Where an executable carries no such record
   the platform cannot answer, and that is reported as unsupported, never as a pass.
3. Behaviour. A mutant target must run its mutated core (its defect trips the intended assertion) and
   the normal target must not (the same case passes).

Usage:
  verify-core-linkage.py --check --build-dir BUILD [--commands-file FILE]
  verify-core-linkage.py --self-test --build-dir BUILD
Exit codes: 0 pass, 1 linkage defect, 2 usage or environment error, 3 platform unsupported.
"""

from __future__ import annotations

import argparse
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

NORMAL_CORE = "libgabbaboy_core.a"
MUTANT_CORE = re.compile(r"^libgabbaboy_core_[A-Za-z0-9_]+\.a$")
ACCEPT_LIB = re.compile(r"^libgabbaboy_accept(_bare)?\.a$")
# A target name that announces a mutant core. Only enforced for executables that link the acceptance
# helpers, because some standalone drivers carry a mutant in their own driver code and use the normal core.
MUTANT_NAME = re.compile(r"(mutant|_p12$)")
LINK_LINE = re.compile(r"^: && (?P<command>.*) && :$")

MUTANT_SOURCE = re.compile(rb"gabbaboy_[A-Za-z0-9_]*mutant[A-Za-z0-9_]*\.c")
NORMAL_SOURCE = re.compile(rb"src/core/(?:\x00)?|libgabbaboy_core\.a\(gabbaboy\.c\.o\)")

# One behavioural pair: a mutant colour-core target that must fail one case, and the same cases on the
# normal target. The mutant disables the palette reserved-bit rejection (see tests/CMakeLists.txt).
BEHAVIOUR_MUTANT = "tests/test_cgb_colour_mutant_palette_mask_bit15"
BEHAVIOUR_NORMAL = "tests/test_cgb_colour"
BEHAVIOUR_FAIL_CASE = "palette_compat_api_reject"
BEHAVIOUR_FAIL_TEXT = "not ok"
BEHAVIOUR_CONTROL_CASE = "palette_compat_api_default"


class Unsupported(Exception):
    """The platform or build cannot answer this question."""


class Defect(Exception):
    """A linkage defect with a stable reason code."""

    def __init__(self, reason: str, detail: str) -> None:
        super().__init__(f"{reason}: {detail}")
        self.reason = reason


def find_ninja(build_dir: Path) -> str:
    found = shutil.which("ninja")
    if found:
        return found
    cache = build_dir / "CMakeCache.txt"
    if cache.is_file():
        match = re.search(r"^CMAKE_MAKE_PROGRAM:[A-Z]+=(.+)$", cache.read_text(encoding="utf-8"), re.M)
        if match and Path(match.group(1)).is_file():
            return match.group(1)
    raise Unsupported("ninja is not available; link-line inspection needs the Ninja generator")


def read_commands(build_dir: Path, commands_file: Path | None) -> str:
    if commands_file is not None:
        return commands_file.read_text(encoding="utf-8")
    if not (build_dir / "build.ninja").is_file():
        raise Unsupported(f"{build_dir} has no build.ninja; only the Ninja generator is inspected")
    result = subprocess.run([find_ninja(build_dir), "-C", str(build_dir), "-t", "commands"],
                            capture_output=True, text=True, check=False, timeout=120)
    if result.returncode != 0:
        raise RuntimeError(f"ninja -t commands failed: {result.stderr.strip()}")
    return result.stdout


def link_lines(commands: str) -> dict[str, list[str]]:
    """Map each linked executable to its archive basenames in link order."""
    lines: dict[str, list[str]] = {}
    for raw in commands.splitlines():
        matched = LINK_LINE.match(raw.strip())
        if not matched:
            continue
        tokens = shlex.split(matched.group("command"))
        if "-o" not in tokens:
            continue
        if any(token.lower().endswith(".lib") or Path(token).name.lower() == "link.exe" for token in tokens):
            raise Unsupported("a link.exe style link line was found; archive inspection is not implemented")
        output = tokens[tokens.index("-o") + 1]
        if output.endswith((".a", ".so", ".dylib")):
            continue
        lines[output] = [Path(token).name for token in tokens if token.endswith(".a")]
    return lines


def classify(archives: list[str]) -> tuple[list[str], list[str], list[str]]:
    cores = [name for name in archives if name == NORMAL_CORE or MUTANT_CORE.match(name)]
    accepts = [name for name in archives if ACCEPT_LIB.match(name)]
    return cores, accepts, [name for name in cores if name != NORMAL_CORE]


def check_line(target: str, archives: list[str]) -> str | None:
    """Return None for an acceptable line, else a diagnostic. Only acceptance-linked targets are in scope."""
    cores, accepts, mutants = classify(archives)
    if not accepts:
        return None
    if not cores:
        return f"no-core: {target} links the acceptance helpers but names no core archive"
    if len(set(cores)) > 1:
        return f"mixed-core: {target} names several core archives {cores}"
    if len(cores) > 1:
        return f"duplicate-core: {target} names {cores[0]} {len(cores)} times"
    wants_mutant = bool(MUTANT_NAME.search(Path(target).name))
    if wants_mutant and not mutants:
        return f"wrong-core: mutant target {target} links the normal core {cores[0]}"
    if not wants_mutant and mutants:
        return f"wrong-core: normal target {target} links the mutant core {cores[0]}"
    return None


def identity_of(path: Path) -> tuple[str, str] | None:
    """Return (kind, label) from the finished executable's debug records, or None if it has none."""
    data = path.read_bytes()
    mutants = sorted(set(match.decode() for match in MUTANT_SOURCE.findall(data)))
    if mutants:
        return "mutant", ",".join(mutants)
    if NORMAL_SOURCE.search(data):
        return "normal", "gabbaboy.c"
    return None


def check_identities(build_dir: Path, lines: dict[str, list[str]]) -> tuple[int, int, int, list[str]]:
    """Return (normal_checked, mutant_checked, unsupported, problems)."""
    normal = mutant = unsupported = 0
    problems: list[str] = []
    for target, archives in sorted(lines.items()):
        cores, accepts, mutants = classify(archives)
        if not accepts or not cores:
            continue
        path = build_dir / target
        if not path.is_file():
            problems.append(f"missing-binary: {target} was not built")
            continue
        found = identity_of(path)
        if found is None:
            unsupported += 1
            continue
        kind, label = found
        expected = "mutant" if mutants else "normal"
        if kind != expected:
            problems.append(f"identity-mismatch: {target} link line says {expected} but the binary holds the {kind} core ({label})")
        elif kind == "mutant":
            mutant += 1
        else:
            normal += 1
    return normal, mutant, unsupported, problems


def check(build_dir: Path, commands_file: Path | None) -> tuple[dict[str, int], list[str]]:
    lines = link_lines(read_commands(build_dir, commands_file))
    scoped = {target: archives for target, archives in lines.items() if classify(archives)[1]}
    problems = [message for target, archives in sorted(scoped.items())
                if (message := check_line(target, archives))]
    counts = {"targets": len(scoped),
              "mutant_targets": sum(1 for archives in scoped.values() if classify(archives)[2]),
              "identity_normal": 0, "identity_mutant": 0, "unsupported": 0}
    if not scoped:
        problems.append("no-targets: no acceptance-linked executable was found, so nothing was proven")
    if commands_file is None and not problems:
        normal, mutant, unsupported, identity_problems = check_identities(build_dir, scoped)
        counts.update(identity_normal=normal, identity_mutant=mutant, unsupported=unsupported)
        problems.extend(identity_problems)
    return counts, problems


def run_cli(args: argparse.Namespace) -> int:
    try:
        counts, problems = check(args.build_dir, args.commands_file)
    except Unsupported as error:
        print(f"core-linkage unsupported: {error}", file=sys.stderr)
        return 3
    except (RuntimeError, OSError, subprocess.SubprocessError) as error:
        print(f"core-linkage error: {error}", file=sys.stderr)
        return 2
    if problems:
        for problem in problems:
            print(f"core-linkage-invalid: {problem}", file=sys.stderr)
        return 1
    if counts["unsupported"]:
        print(f"core-linkage unsupported: {counts['unsupported']} executables carry no debug identity",
              file=sys.stderr)
        return 3
    print("core-linkage pass targets={targets} mutant_targets={mutant_targets} "
          "identity_normal={identity_normal} identity_mutant={identity_mutant}".format(**counts))
    return 0


def run_process(command: list[str], timeout: int = 120) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, capture_output=True, text=True, check=False, timeout=timeout)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def expect_rejection(script: Path, build_dir: Path, commands: str, reason: str, name: str,
                     directory: Path) -> None:
    fixture = directory / f"{name}.commands"
    fixture.write_text(commands, encoding="utf-8", newline="\n")
    result = run_process([sys.executable, "-I", str(script), "--check", "--build-dir", str(build_dir),
                          "--commands-file", str(fixture)])
    require(result.returncode == 1, f"{name}: exit {result.returncode}, expected 1\n{result.stderr}")
    require(f"core-linkage-invalid: {reason}:" in result.stderr,
            f"{name}: missing diagnostic {reason!r}\n{result.stderr}")
    require("core-linkage pass" not in result.stdout, f"{name}: emitted success output")


def mutate_line(commands: str, target: str, edit) -> str:
    out: list[str] = []
    hits = 0
    for raw in commands.splitlines():
        matched = LINK_LINE.match(raw.strip())
        if matched:
            tokens = shlex.split(matched.group("command"))
            if "-o" in tokens and tokens[tokens.index("-o") + 1] == target:
                tokens = edit(tokens)
                raw = ": && " + " ".join(shlex.quote(token) for token in tokens) + " && :"
                hits += 1
        out.append(raw)
    require(hits == 1, f"fixture target {target} must have exactly one link line (found {hits})")
    return "\n".join(out) + "\n"


def archive_path(tokens: list[str], basename: str) -> str:
    for token in tokens:
        if Path(token).name == basename:
            return token
    raise AssertionError(f"link line has no {basename}")


def self_test(build_dir: Path) -> int:
    script = Path(__file__).resolve()
    commands = read_commands(build_dir, None)
    counts, problems = check(build_dir, None)
    require(not problems, "the real build already has linkage defects:\n  " + "\n  ".join(problems))
    require(counts["unsupported"] == 0, f"{counts['unsupported']} executables carry no debug identity")
    require(counts["mutant_targets"] >= 4 and counts["identity_mutant"] >= 4 and counts["identity_normal"] >= 4,
            f"too few targets were proven: {counts}")
    lines = link_lines(commands)
    for needed in ("tests/test_age", "tests/test_cgb_speed_fixture", "tests/test_age_p12",
                   BEHAVIOUR_MUTANT, BEHAVIOUR_NORMAL):
        require(needed in lines, f"expected link line for {needed}")

    rejected = 0
    with tempfile.TemporaryDirectory(prefix="core-linkage-") as temp_name:
        temp = Path(temp_name)
        # Duplicate library: the normal core named a second time on a normal link line.
        def duplicate(tokens: list[str]) -> list[str]:
            return tokens + [archive_path(tokens, NORMAL_CORE)]
        expect_rejection(script, build_dir, mutate_line(commands, "tests/test_age", duplicate),
                         "duplicate-core", "duplicate-core", temp)
        rejected += 1
        # Wrong-core substitution: the normal core slips into a mutant link line.
        def mixed(tokens: list[str]) -> list[str]:
            return tokens + [archive_path(tokens, NORMAL_CORE)]
        expect_rejection(script, build_dir, mutate_line(commands, "tests/test_age_p12", mixed),
                         "mixed-core", "mixed-core", temp)
        rejected += 1
        # Wrong-core substitution: a mutant target whose mutant core is replaced by the normal core.
        def swap_to_normal(tokens: list[str]) -> list[str]:
            return [token if not MUTANT_CORE.match(Path(token).name) else
                    str(Path(token).parent / NORMAL_CORE) for token in tokens]
        expect_rejection(script, build_dir, mutate_line(commands, "tests/test_age_p12", swap_to_normal),
                         "wrong-core", "wrong-core-normal-for-mutant", temp)
        rejected += 1
        # Wrong-core substitution: a normal target handed a mutant core.
        mutant_archive = archive_path(lines_tokens(commands, "tests/test_age_p12"), "libgabbaboy_core_p12_mutants.a")
        def swap_to_mutant(tokens: list[str]) -> list[str]:
            return [mutant_archive if Path(token).name == NORMAL_CORE else token for token in tokens]
        expect_rejection(script, build_dir, mutate_line(commands, "tests/test_age_m3", swap_to_mutant),
                         "wrong-core", "wrong-core-mutant-for-normal", temp)
        rejected += 1
        # A core that is missing altogether.
        def drop_core(tokens: list[str]) -> list[str]:
            return [token for token in tokens if Path(token).name != NORMAL_CORE]
        expect_rejection(script, build_dir, mutate_line(commands, "tests/test_cgb_speed_fixture", drop_core),
                         "no-core", "no-core", temp)
        rejected += 1
        # A commands file that names no acceptance target proves nothing and is not a pass.
        expect_rejection(script, build_dir, "", "no-targets", "no-targets", temp)
        rejected += 1

        # Linked bytes: each real executable's identity must match its link line, and the check must
        # notice a binary that holds the other core (a normal binary relabelled as a mutant and back).
        normal_binary = build_dir / BEHAVIOUR_NORMAL
        mutant_binary = build_dir / BEHAVIOUR_MUTANT
        require(identity_of(normal_binary) is not None and identity_of(normal_binary)[0] == "normal",
                "normal binary does not report the normal core")
        require(identity_of(mutant_binary) is not None and identity_of(mutant_binary)[0] == "mutant",
                "mutant binary does not report a mutant core")
        swapped = temp / "swapped-build"
        (swapped / "tests").mkdir(parents=True)
        shutil.copy2(mutant_binary, swapped / BEHAVIOUR_NORMAL)
        shutil.copy2(normal_binary, swapped / BEHAVIOUR_MUTANT)
        scoped = {key: value for key, value in link_lines(commands).items()
                  if key in (BEHAVIOUR_NORMAL, BEHAVIOUR_MUTANT)}
        _, _, _, swap_problems = check_identities(swapped, scoped)
        require(len(swap_problems) == 2 and all(p.startswith("identity-mismatch:") for p in swap_problems),
                f"swapped binaries were not rejected as identity mismatches: {swap_problems}")
        rejected += 1
        # A binary without debug records cannot answer: unsupported, never a pass.
        bare = temp / "bare-build"
        (bare / "tests").mkdir(parents=True)
        (bare / BEHAVIOUR_NORMAL).write_bytes(b"\x7fELF no debug records here")
        (bare / BEHAVIOUR_MUTANT).write_bytes(b"\x7fELF no debug records here")
        _, _, bare_unsupported, bare_problems = check_identities(bare, scoped)
        require(bare_unsupported == 2 and not bare_problems,
                f"a binary without records must be reported unsupported (got {bare_unsupported}, {bare_problems})")
        rejected += 1

    # Behaviour: the mutant executable runs its mutated core and the normal executable does not.
    mutant_run = run_process([str(mutant_binary), BEHAVIOUR_FAIL_CASE], timeout=60)
    require(mutant_run.returncode == 1 and BEHAVIOUR_FAIL_TEXT in mutant_run.stdout + mutant_run.stderr,
            f"mutant target did not trip its defect (exit {mutant_run.returncode})")
    control_run = run_process([str(mutant_binary), BEHAVIOUR_CONTROL_CASE], timeout=60)
    require(control_run.returncode == 0, f"mutant target failed its control (exit {control_run.returncode})")
    normal_run = run_process([str(normal_binary), BEHAVIOUR_FAIL_CASE], timeout=60)
    require(normal_run.returncode == 0 and BEHAVIOUR_FAIL_TEXT not in normal_run.stdout + normal_run.stderr,
            f"normal target ran the mutant behaviour (exit {normal_run.returncode})")
    # The same expectation applied to the normal target is the wrong-core negative control: it must fail.
    rejected += 1

    print("core-linkage self-test pass targets={targets} mutant_targets={mutant_targets} "
          "identity_normal={identity_normal} identity_mutant={identity_mutant} behavioural=3 "
          "rejected_controls={rejected}".format(rejected=rejected, **counts))
    return 0


def lines_tokens(commands: str, target: str) -> list[str]:
    for raw in commands.splitlines():
        matched = LINK_LINE.match(raw.strip())
        if matched:
            tokens = shlex.split(matched.group("command"))
            if "-o" in tokens and tokens[tokens.index("-o") + 1] == target:
                return tokens
    raise AssertionError(f"no link line for {target}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="inspect the build's link lines and binaries")
    mode.add_argument("--self-test", action="store_true", help="run positive and intended-defect controls")
    parser.add_argument("--build-dir", type=Path, required=True)
    parser.add_argument("--commands-file", type=Path, help="use captured `ninja -t commands` output (link lines only)")
    args = parser.parse_args()
    args.build_dir = args.build_dir.resolve()
    if args.self_test:
        try:
            return self_test(args.build_dir)
        except Unsupported as error:
            print(f"core-linkage unsupported: {error}", file=sys.stderr)
            return 3
        except (AssertionError, RuntimeError, OSError, subprocess.SubprocessError) as error:
            print(f"core-linkage self-test FAIL: {error}", file=sys.stderr)
            return 1
    return run_cli(args)


if __name__ == "__main__":
    sys.exit(main())
