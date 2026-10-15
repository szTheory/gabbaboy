#!/usr/bin/env python3
"""Exercise the actual HDMA source gate in isolated, disposable Git histories."""
from __future__ import annotations

import runpy
import subprocess
import tempfile
from pathlib import Path


def git(root: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=root, capture_output=True,
                            text=True, check=True)
    return result.stdout.strip()


def write(root: Path, relative: str, content: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def main() -> int:
    checker = runpy.run_path(str(Path(__file__).with_name("verify-hdma-closure.py")))
    validate = checker["validate_source_revision"]
    contract_error = checker["ContractError"]
    phase = ".planning/phases/GB-13-cgb-hdma/"
    metadata = (
        ".planning/STATE.md", ".planning/PROJECT.md", ".planning/ROADMAP.md",
        ".planning/REQUIREMENTS.md", ".planning/config.json", ".planning/state.json",
        ".planning/milestone.lock", ".planning/context/LESSONS.md",
        ".planning/context/DECISIONS.md", ".planning/research/INDEX.md",
        *(phase + f"13-{number:02d}-SUMMARY.md" for number in range(1, 13)),
        *(phase + name for name in (
            "13-BENCH.md", "13-VALIDATION.md", "13-SECURITY.md", "13-REVIEW.md",
            "13-REVIEW-DISPOSITION.md", "13-VERIFICATION.md", "13-LEARNINGS.md",
            "continue.md", "deferred-items.md", "13-ASAN-ADDED-COST.json")),
    )
    # Paths are independent expectations, not copied from the gate's allowlist.
    cases = (
        ("committed-core-only", "committed", "src/core/gabbaboy.c"),
        ("committed-fixture", "committed", "fixtures/cgb-hdma/hblank.asm"),
        ("committed-harness", "committed", "tests/test_cgb_hdma.c"),
        ("committed-workflow", "committed", ".github/workflows/ci.yml"),
        ("committed-unknown-planning-code", "committed", phase + "new-checker.py"),
        ("committed-closure-checker", "committed", phase + "verify-hdma-closure.py"),
        ("committed-projection-plan", "committed", phase + "13-01-PLAN.md"),
        ("committed-readme", "committed", "README.md"),
        ("committed-claim-doc", "committed", "docs/native-integration.md"),
        ("committed-fixture-provenance", "committed", "fixtures/cgb-hdma/manifest.json"),
        ("committed-unknown-path", "committed", "new-input.data"),
        ("unstaged-core", "unstaged", "src/core/gabbaboy.c"),
        ("staged-core", "staged", "src/core/gabbaboy.c"),
        ("staged-core-worktree-reverted", "staged-reverted", "src/core/gabbaboy.c"),
        ("untracked-source", "untracked", "src/core/new-source.c"),
        ("untracked-unknown-planning-code", "untracked", phase + "untracked-checker.py"),
        ("untracked-path-with-newline", "untracked", "src/core/line\nbreak.c"),
        ("untracked-path-with-shell-syntax", "untracked", "src/core/$(false); spaced.c"),
        ("deleted-core", "deleted", "src/core/gabbaboy.c"),
        ("renamed-core-to-metadata", "renamed", "src/core/gabbaboy.c"),
    )
    failures = []
    passed = 0
    with tempfile.TemporaryDirectory(prefix="gabbaboy-hdma-source-") as temporary:
        root = Path(temporary)
        git(root, "init", "--quiet")
        git(root, "config", "user.name", "GabbaBoy source-gate controls")
        git(root, "config", "user.email", "gabbaboy@users.noreply.github.com")
        git(root, "config", "core.hooksPath", str(root / "no-hooks"))
        write(root, ".gitignore", "build/\n")
        for _, state, path in cases:
            if state not in ("untracked",) and "unknown" not in path:
                write(root, path, "tested source\n")
        git(root, "add", "--all")
        git(root, "commit", "--quiet", "-m", "tested source")
        source = git(root, "rev-parse", "HEAD")
        bench = f"- Source revision: `{source}`\n"

        def check(label: str, reject: bool) -> None:
            nonlocal passed
            try:
                actual = validate(root, bench, git(root, "rev-parse", "HEAD"))
            except contract_error as error:
                if reject:
                    print(f"PASS {label}: rejected ({error})")
                    passed += 1
                else:
                    failures.append(label)
                    print(f"FAIL {label}: rejected permitted source ({error})")
            else:
                if reject:
                    failures.append(label)
                    print(f"FAIL {label}: ACCEPTED_UNTESTED_SOURCE_CHANGE")
                elif actual != source:
                    failures.append(label)
                    print(f"FAIL {label}: returned wrong source revision")
                else:
                    passed += 1
                    print(f"PASS {label}: exact source accepted")

        check("exact-tested-source", reject=False)
        write(root, "build/ignored-scratch.c", "ignored build scratch\n")
        check("ignored-build-scratch", reject=False)
        for path in metadata:
            write(root, path, "closeout metadata\n")
        check("untracked-permitted-metadata", reject=False)
        git(root, "add", "--all")
        check("staged-permitted-metadata", reject=False)
        git(root, "commit", "--quiet", "-m", "metadata closeout")
        check("committed-permitted-metadata", reject=False)
        for path in metadata:
            write(root, path, "updated closeout metadata\n")
        check("unstaged-permitted-metadata", reject=False)
        git(root, "reset", "--hard", "--quiet", source)
        for label, state, path in cases:
            if state == "deleted":
                (root / path).unlink()
            elif state == "renamed":
                target = root / ".planning/STATE.md"
                target.parent.mkdir(parents=True, exist_ok=True)
                (root / path).rename(target)
                git(root, "add", "--all")
                git(root, "commit", "--quiet", "-m", label)
            else:
                write(root, path, "untested mutation\n")
            if state in ("committed", "staged", "staged-reverted"):
                git(root, "add", "--", path)
            if state == "committed":
                git(root, "commit", "--quiet", "-m", label)
            elif state == "staged-reverted":
                write(root, path, "tested source\n")
            check(label, reject=True)
            git(root, "reset", "--hard", "--quiet", source)
            git(root, "clean", "-fd", "--quiet")
    print(f"hdma-source-revision controls: {passed}/{passed + len(failures)} pass")
    if failures:
        print("hdma-source-revision FAILED: " + ", ".join(failures))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
