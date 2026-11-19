#!/usr/bin/env python3
"""Exercise dense acceptance input against the frozen DMG ledger and a source mutant."""

from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
import re
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
FULL_COMMIT = re.compile(r"^[0-9a-f]{40}$")
FULL_COMMIT_BYTES = re.compile(rb"[0-9a-f]{40}")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def run(command: list[str], *, cwd: Path, timeout: int = 300) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, text=True, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT, timeout=timeout, check=False)


def _git_environment() -> dict[str, str]:
    """Give disposable Git commands a small, predictable environment."""
    env = {key: value for key, value in os.environ.items()
           if key in {"PATH", "SYSTEMROOT", "TMPDIR", "TEMP", "TMP"}}
    env.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_SYSTEM=os.devnull,
               GIT_CONFIG_NOSYSTEM="1", GIT_TERMINAL_PROMPT="0")
    return env


def git_bytes(repo: Path, *args: str, input_bytes: bytes | None = None,
              timeout: int = 60) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(["git", "--no-replace-objects", "-C", str(repo), *args], cwd=repo, input=input_bytes,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
                          env=_git_environment(), timeout=timeout)


def _git_detail(result: subprocess.CompletedProcess[bytes]) -> str:
    return (result.stdout + result.stderr).decode("utf-8", "replace").strip()


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
    listed = git_bytes(ROOT, "ls-files", "-z")
    require(listed.returncode == 0, f"cannot enumerate tracked source: {_git_detail(listed)}")
    tracked = listed.stdout.split(b"\0")
    for raw_path in tracked:
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
    initialized = git(ROOT, "init", "--bare", str(destination))
    require(initialized.returncode == 0, f"baseline object store init failed:\n{initialized.stdout}")
    fetched = git(ROOT, "--git-dir", str(destination), "fetch", "--no-tags", str(ROOT), BASELINE_COMMIT)
    require(fetched.returncode == 0, f"fixed baseline object copy failed:\n{fetched.stdout}")
    verified = git(ROOT, "--git-dir", str(destination), "cat-file", "-e", f"{BASELINE_COMMIT}^{{commit}}")
    require(verified.returncode == 0, "copied baseline object did not verify at its full commit identity")


def git(repo: Path, *args: str, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    raw = git_bytes(repo, *args, input_bytes=input_text.encode("utf-8") if input_text is not None else None)
    return subprocess.CompletedProcess(["git", "--no-replace-objects", "-C", str(repo), *args], raw.returncode,
                                       (raw.stdout + raw.stderr).decode("utf-8", "replace"), "")


def git_blob(repo: Path, revision: str, path: str) -> bytes:
    result = git_bytes(repo, "show", f"{revision}:{path}")
    require(result.returncode == 0,
            f"cannot read immutable admission pin {path}: {_git_detail(result)}")
    return result.stdout


def parse_admission_pin(raw: bytes, path: str) -> str:
    if len(raw) == 40:
        value = raw
    elif len(raw) == 41 and raw.endswith(b"\n"):
        value = raw[:-1]
    elif len(raw) == 42 and raw.endswith(b"\r\n"):
        value = raw[:-2]
    else:
        raise RuntimeError(f"admission-pin-invalid: {path}")
    if FULL_COMMIT_BYTES.fullmatch(value) is None:
        raise RuntimeError(f"admission-pin-invalid: {path}")
    return value.decode("ascii")


def admission_pin_controls() -> int:
    body = b"a" * 40
    positives = (body, body + b"\n", body + b"\r\n")
    for raw in positives:
        require(parse_admission_pin(raw, "control") == body.decode("ascii"),
                "valid raw admission-pin form was rejected")
    invalid = (body + b"\r", body + b"\r\n\n", body + b"\n\r\n", body + b" ",
               body.upper(), b"g" + body[1:], body[:-1], body + b"0", b"\xff" + body[1:])
    for raw in invalid:
        try:
            parse_admission_pin(raw, "control")
        except RuntimeError as error:
            require("admission-pin-invalid" in str(error),
                    f"malformed raw admission pin refused for the wrong cause: {error}")
        else:
            raise RuntimeError(f"malformed raw admission pin was accepted: {raw!r}")

    # Commit one malformed blob and send it through the same tree enumeration and
    # object reader as a real candidate. This proves text-mode newline conversion
    # cannot turn a bare-CR pin into an accepted LF pin.
    with tempfile.TemporaryDirectory(prefix="dense-bare-cr-pin-") as name:
        repo = Path(name)
        pin_path = repo / "fixtures/probe/admission.commit"
        pin_path.parent.mkdir(parents=True)
        (repo / "fixtures/probe/manifest.json").write_bytes(b"{}\n")
        pin_path.write_bytes(body + b"\r")
        require(git(repo, "init", "-q").returncode == 0, "bare-CR pin repository init failed")
        added = git(repo, "add", "fixtures/probe/manifest.json", "fixtures/probe/admission.commit")
        require(added.returncode == 0, f"bare-CR pin staging failed: {added.stdout.strip()}")
        committed = git(repo, "-c", "user.name=Fixture Control", "-c",
                        "user.email=fixture-control@example.invalid", "commit", "-qm", "bare-CR pin")
        require(committed.returncode == 0, f"bare-CR pin commit failed: {committed.stdout.strip()}")
        revision = git(repo, "rev-parse", "--verify", "HEAD^{commit}")
        require(revision.returncode == 0, f"bare-CR pin commit identity unavailable: {revision.stdout.strip()}")
        try:
            active_admission_pins(repo, revision.stdout.strip())
        except RuntimeError as error:
            require("admission-pin-invalid" in str(error),
                    f"committed bare-CR pin refused for the wrong cause: {error}")
        else:
            raise RuntimeError("committed bare-CR admission pin was accepted")
    return len(positives) + len(invalid) + 1


def active_admission_pins(source: Path, source_revision: str) -> list[tuple[str, str]]:
    require(FULL_COMMIT.fullmatch(source_revision) is not None,
            "source revision must be one full lowercase commit identity")
    available = git(source, "cat-file", "-e", f"{source_revision}^{{commit}}")
    require(available.returncode == 0,
            f"candidate-object-unavailable: {source_revision}")
    tree = git_bytes(source, "ls-tree", "-rz", "--name-only", source_revision, "--", "fixtures")
    require(tree.returncode == 0, f"cannot enumerate candidate fixture tree: {_git_detail(tree)}")
    paths = {os.fsdecode(path) for path in tree.stdout.split(b"\0") if path}
    manifests = {path for path in paths if re.fullmatch(r"fixtures/[^/]+/manifest\.json", path)}
    pins = sorted(path for path in paths if re.fullmatch(r"fixtures/[^/]+/admission\.commit", path))
    require(pins, "candidate has no active fixture admission pins")
    for pin_path in pins:
        manifest_path = pin_path.removesuffix("admission.commit") + "manifest.json"
        require(manifest_path in manifests,
                f"admission pin has no sibling manifest: {pin_path}")
    result: list[tuple[str, str]] = []
    for pin_path in pins:
        result.append((pin_path, parse_admission_pin(git_blob(source, source_revision, pin_path), pin_path)))
    return result


def validate_candidate_git_context(subject: Path, source_revision: str) -> list[tuple[str, str]]:
    require(FULL_COMMIT.fullmatch(source_revision) is not None,
            "candidate revision is not one full lowercase identity")
    absolute_git_dir = git(subject, "rev-parse", "--absolute-git-dir")
    require(absolute_git_dir.returncode == 0,
            f"candidate-git-dir-unavailable: {absolute_git_dir.stdout.strip()}")
    expected_git_dir = (subject / ".git").resolve()
    actual_git_dir = Path(absolute_git_dir.stdout.strip()).resolve()
    require(actual_git_dir == expected_git_dir,
            f"candidate-git-dir-mismatch: expected={expected_git_dir} actual={actual_git_dir}")
    candidate = git(subject, "cat-file", "-e", f"{source_revision}^{{commit}}")
    require(candidate.returncode == 0, f"candidate-object-unavailable: {source_revision}")
    worktree = git(subject, "rev-parse", "--show-toplevel")
    require(worktree.returncode == 0,
            f"candidate-worktree-unavailable: {worktree.stdout.strip()}")
    expected_worktree = subject.resolve()
    actual_worktree = Path(worktree.stdout.strip()).resolve()
    require(actual_worktree == expected_worktree,
            f"candidate-worktree-mismatch: expected={expected_worktree} actual={actual_worktree}")
    head = git(subject, "rev-parse", "--verify", "HEAD^{commit}")
    require(head.returncode == 0, f"candidate-head-unavailable: {head.stdout.strip()}")
    actual_head = head.stdout.strip()
    require(actual_head == source_revision,
            f"candidate-head-mismatch: expected={source_revision} actual={actual_head}")
    pins = active_admission_pins(subject, source_revision)
    for path, pin in pins:
        present = git(subject, "cat-file", "-e", f"{pin}^{{commit}}")
        require(present.returncode == 0,
                f"admission-pin-object-unavailable: {path} {pin}")
        ancestry = git(subject, "merge-base", "--is-ancestor", pin, source_revision)
        require(ancestry.returncode == 0,
                f"admission-pin-not-in-history: {path} {pin}")
    return pins


def install_candidate_git_context(subject: Path, source_revision: str) -> list[tuple[str, str]]:
    initialized = git(subject, "init", "-q")
    require(initialized.returncode == 0, f"candidate subject init failed: {initialized.stdout.strip()}")
    fetched = git(subject, "fetch", "--no-tags", str(ROOT), source_revision)
    require(fetched.returncode == 0,
            f"candidate object transfer failed: {fetched.stdout.strip()}")
    branch = "refs/heads/phase24-d213-candidate"
    updated = git(subject, "update-ref", branch, source_revision)
    require(updated.returncode == 0, f"candidate HEAD setup failed: {updated.stdout.strip()}")
    symbolic = git(subject, "symbolic-ref", "HEAD", branch)
    require(symbolic.returncode == 0, f"candidate HEAD binding failed: {symbolic.stdout.strip()}")
    read_index = git(subject, "read-tree", source_revision)
    require(read_index.returncode == 0, f"candidate index setup failed: {read_index.stdout.strip()}")
    return validate_candidate_git_context(subject, source_revision)


def candidate_git_context_controls(source_revision: str) -> int:
    pins = active_admission_pins(ROOT, source_revision)
    pin_controls = admission_pin_controls()
    with tempfile.TemporaryDirectory(prefix="dense-git-context-", dir=ROOT) as temp_name:
        temp = Path(temp_name)
        candidate = temp / "candidate"
        candidate.mkdir()
        installed = install_candidate_git_context(candidate, source_revision)
        require(installed == pins, "candidate subject changed the enumerated admission pin set")

        pin_path, _pin_value = pins[0]
        original_pin = git_blob(candidate, source_revision, pin_path)
        mutant_pin = b"0" * 40 + b"\n"
        mutant_blob = git(candidate, "hash-object", "-w", "--stdin", input_text=mutant_pin.decode("ascii"))
        require(mutant_blob.returncode == 0, "replacement-ref mutant pin blob could not be written")
        added_path = "fixtures/d217-replacement/manifest.json"
        added_blob = git(candidate, "hash-object", "-w", "--stdin", input_text="{}\n")
        require(added_blob.returncode == 0, "replacement-ref extra manifest blob could not be written")
        staged = git(candidate, "update-index", "--add", "--cacheinfo",
                     "100644," + mutant_blob.stdout.strip() + "," + pin_path,
                     "--cacheinfo", "100644," + added_blob.stdout.strip() + "," + added_path)
        require(staged.returncode == 0, f"replacement-ref mutant tree could not be staged: {staged.stdout.strip()}")
        mutant_tree = git(candidate, "write-tree")
        require(mutant_tree.returncode == 0, "replacement-ref mutant tree could not be written")
        mutant_commit = git(candidate, "-c", "user.name=Fixture Control", "-c",
                            "user.email=fixture-control@example.invalid", "commit-tree",
                            mutant_tree.stdout.strip(), "-p", source_revision, "-m", "replacement-ref mutant")
        require(mutant_commit.returncode == 0, f"replacement-ref mutant commit failed: {mutant_commit.stdout.strip()}")
        mutant_revision = mutant_commit.stdout.strip()
        require(git(candidate, "replace", source_revision, mutant_revision).returncode == 0,
                "replacement-ref control could not install the synthetic commit replacement")
        ordinary_pin = subprocess.run(["git", "-C", str(candidate), "show",
                                       f"{source_revision}:{pin_path}"], cwd=candidate,
                                      env=_git_environment(), stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE, check=False)
        ordinary_tree = subprocess.run(["git", "-C", str(candidate), "ls-tree", "-rz",
                                        "--name-only", source_revision, "--", "fixtures"],
                                       cwd=candidate, env=_git_environment(), stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE, check=False)
        ordinary_paths = set(ordinary_tree.stdout.split(b"\0"))
        require(ordinary_pin.returncode == 0 and ordinary_pin.stdout == mutant_pin
                and added_path.encode("ascii") in ordinary_paths,
                "ordinary Git did not prove replacement commit changed both pin and fixture tree")
        require(git_blob(candidate, source_revision, pin_path) == original_pin
                and active_admission_pins(candidate, source_revision) == pins,
                "hardened admission reads followed a replacement ref instead of original objects")

        decoy = temp / "decoy"
        decoy.mkdir()
        (decoy / "sentinel.txt").write_text("unchanged decoy repository\n", encoding="utf-8", newline="\n")
        require(git(decoy, "init", "-q").returncode == 0, "decoy repository init failed")
        require(git(decoy, "add", "sentinel.txt").returncode == 0, "decoy sentinel staging failed")
        decoy_commit = git(decoy, "-c", "user.name=Fixture Control", "-c",
                           "user.email=fixture-control@example.invalid", "commit", "-qm", "decoy sentinel")
        require(decoy_commit.returncode == 0, f"decoy commit failed: {decoy_commit.stdout.strip()}")
        decoy_head = git(decoy, "rev-parse", "--verify", "HEAD^{commit}").stdout.strip()
        decoy_refs = git(decoy, "for-each-ref", "--format=%(refname) %(objectname)").stdout
        decoy_index = hashlib.sha256((decoy / ".git/index").read_bytes()).hexdigest()
        hostile_values = {
            "GIT_DIR": str(decoy / ".git"),
            "GIT_WORK_TREE": str(decoy),
            "GIT_COMMON_DIR": str(decoy / ".git"),
            "GIT_INDEX_FILE": str(decoy / ".git/index"),
            "GIT_OBJECT_DIRECTORY": str(decoy / ".git/objects"),
            "GIT_ALTERNATE_OBJECT_DIRECTORIES": str(decoy / ".git/objects"),
            "GIT_CONFIG_GLOBAL": str(decoy / "hostile-global-config"),
            "GIT_CONFIG_SYSTEM": str(decoy / "hostile-system-config"),
            "GIT_CONFIG_COUNT": "1",
            "GIT_CONFIG_KEY_0": "core.bare",
            "GIT_CONFIG_VALUE_0": "true",
            "GIT_NAMESPACE": "redirected",
            "GIT_PREFIX": "redirected/",
        }
        (decoy / "hostile-global-config").write_text("[core]\n\tbare = true\n", encoding="utf-8")
        (decoy / "hostile-system-config").write_text("[core]\n\tbare = true\n", encoding="utf-8")
        previous_values = {key: os.environ.get(key) for key in hostile_values}
        previously_present = {key for key in hostile_values if key in os.environ}
        try:
            os.environ.update(hostile_values)
            hostile_candidate = temp / "hostile-candidate"
            hostile_candidate.mkdir()
            hostile_pins = install_candidate_git_context(hostile_candidate, source_revision)
            require(hostile_pins == pins, "hostile environment changed the selected admission pins")
            require(git(decoy, "rev-parse", "--verify", "HEAD^{commit}").stdout.strip() == decoy_head,
                    "sanitized candidate Git operations changed the decoy HEAD")
            require(git(decoy, "for-each-ref", "--format=%(refname) %(objectname)").stdout == decoy_refs,
                    "sanitized candidate Git operations changed decoy refs")
            require(hashlib.sha256((decoy / ".git/index").read_bytes()).hexdigest() == decoy_index,
                    "sanitized candidate Git operations changed the decoy index")

            safe_environment = _git_environment
            try:
                globals()["_git_environment"] = lambda: os.environ.copy()
                try:
                    validate_candidate_git_context(candidate, source_revision)
                except RuntimeError as error:
                    require("candidate-git-dir-mismatch" in str(error),
                            f"unsanitized Git control refused for the wrong cause: {error}")
                else:
                    raise RuntimeError("unsanitized Git environment redirection was accepted")
            finally:
                globals()["_git_environment"] = safe_environment
        finally:
            for key in hostile_values:
                if key in previously_present:
                    os.environ[key] = previous_values[key] or ""
                else:
                    os.environ.pop(key, None)
        require(git(decoy, "rev-parse", "--verify", "HEAD^{commit}").stdout.strip() == decoy_head,
                "hostile-environment controls changed the decoy HEAD")
        require(git(decoy, "for-each-ref", "--format=%(refname) %(objectname)").stdout == decoy_refs,
                "hostile-environment controls changed decoy refs")
        require(hashlib.sha256((decoy / ".git/index").read_bytes()).hexdigest() == decoy_index,
                "hostile-environment controls changed the decoy index")

        missing = temp / "missing-object"
        missing.mkdir()
        initialized = git(missing, "init", "-q")
        require(initialized.returncode == 0, "missing-object fixture init failed")
        try:
            validate_candidate_git_context(missing, source_revision)
        except RuntimeError as error:
            require("candidate-object-unavailable" in str(error),
                    f"missing-object control refused for wrong cause: {error}")
        else:
            raise RuntimeError("missing candidate object control was accepted")

        wrong_head = temp / "wrong-head"
        wrong_head.mkdir()
        wrong_install = install_candidate_git_context(wrong_head, source_revision)
        require(wrong_install == pins, "wrong-head control lost an admission pin")
        parent = git(wrong_head, "rev-parse", "--verify", f"{source_revision}^{{commit}}^")
        require(parent.returncode == 0, "candidate has no parent for the wrong-head control")
        wrong_ref = git(wrong_head, "update-ref", "refs/heads/wrong", parent.stdout.strip())
        require(wrong_ref.returncode == 0, "wrong-head ref setup failed")
        symbolic = git(wrong_head, "symbolic-ref", "HEAD", "refs/heads/wrong")
        require(symbolic.returncode == 0, "wrong-head binding failed")
        try:
            validate_candidate_git_context(wrong_head, source_revision)
        except RuntimeError as error:
            require("candidate-head-mismatch" in str(error),
                    f"wrong-head control refused for wrong cause: {error}")
        else:
            raise RuntimeError("wrong candidate HEAD control was accepted")

        shallow = temp / "missing-pin-object"
        shallow.mkdir()
        initialized = git(shallow, "init", "-q")
        require(initialized.returncode == 0, "missing-pin fixture init failed")
        fetched = git(shallow, "fetch", "--no-tags", "--depth=1", str(ROOT), source_revision)
        require(fetched.returncode == 0, f"shallow candidate transfer failed: {fetched.stdout.strip()}")
        shallow_ref = git(shallow, "update-ref", "refs/heads/candidate", source_revision)
        require(shallow_ref.returncode == 0, "shallow candidate ref setup failed")
        symbolic = git(shallow, "symbolic-ref", "HEAD", "refs/heads/candidate")
        require(symbolic.returncode == 0, "shallow candidate binding failed")
        try:
            validate_candidate_git_context(shallow, source_revision)
        except RuntimeError as error:
            require("admission-pin-object-unavailable" in str(error),
                    f"missing-pin control refused for wrong cause: {error}")
        else:
            raise RuntimeError("missing admission pin object control was accepted")

        unrelated = temp / "unrelated-ancestry"
        unrelated.mkdir()
        unrelated_install = install_candidate_git_context(unrelated, source_revision)
        require(unrelated_install == pins, "ancestry control lost an admission pin")
        empty_tree = git(unrelated, "mktree", input_text="")
        require(empty_tree.returncode == 0, f"unrelated root tree creation failed: {empty_tree.stdout.strip()}")
        root_commit = git(unrelated, "-c", "user.name=Fixture Control", "-c",
                          "user.email=fixture-control@example.invalid", "commit-tree",
                          empty_tree.stdout.strip(), "-m", "unrelated ancestry control")
        require(root_commit.returncode == 0, f"unrelated root commit creation failed: {root_commit.stdout.strip()}")
        candidate_tree = git(unrelated, "rev-parse", f"{source_revision}^{{tree}}")
        require(candidate_tree.returncode == 0, "candidate tree is unavailable for ancestry control")
        alternate = git(unrelated, "-c", "user.name=Fixture Control", "-c",
                        "user.email=fixture-control@example.invalid", "commit-tree",
                        candidate_tree.stdout.strip(), "-p", root_commit.stdout.strip(),
                        "-m", "same-tree unrelated candidate control")
        require(alternate.returncode == 0, f"unrelated candidate creation failed: {alternate.stdout.strip()}")
        alternate_ref = git(unrelated, "update-ref", "refs/heads/unrelated", alternate.stdout.strip())
        require(alternate_ref.returncode == 0, "unrelated candidate ref setup failed")
        symbolic = git(unrelated, "symbolic-ref", "HEAD", "refs/heads/unrelated")
        require(symbolic.returncode == 0, "unrelated candidate binding failed")
        try:
            validate_candidate_git_context(unrelated, alternate.stdout.strip())
        except RuntimeError as error:
            require("admission-pin-not-in-history" in str(error),
                    f"unrelated ancestry control refused for wrong cause: {error}")
        else:
            raise RuntimeError("unrelated admission ancestry control was accepted")
    return len(pins) + 4 + pin_controls + 2


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
    parser.add_argument("--self-test", action="store_true",
                        help="run the dense-input positive and negative controls")
    parser.add_argument("--build-dir", type=Path,
                        help="isolated build containing gabbaboy-runner")
    parser.add_argument("--check-git-context", action="store_true",
                        help="run candidate identity and admission-pin controls without configure/build/runner")
    parser.add_argument("--source-revision",
                        help="full immutable candidate commit for --check-git-context")
    args = parser.parse_args()
    if args.check_git_context:
        require(not args.self_test and args.build_dir is None,
                "--check-git-context must run alone without a runner/build directory")
        require(args.source_revision is not None,
                "--check-git-context requires --source-revision")
        controls = candidate_git_context_controls(args.source_revision)
        print(f"dense-input git-context=pass rev={args.source_revision} controls={controls} configure=0 build=0 runner=0")
        return 0
    require(args.self_test and args.build_dir is not None,
            "full dense-input verification needs --self-test and --build-dir")
    build_dir = args.build_dir if args.build_dir.is_absolute() else ROOT / args.build_dir
    runner = build_dir / "gabbaboy-runner"
    if not runner.is_file():
        runner = build_dir / "gabbaboy-runner.exe"
    require(runner.is_file(), f"runner not found in {build_dir}; build gabbaboy-runner first")
    runner = runner.resolve()
    revision_result = git(ROOT, "rev-parse", "--verify", "HEAD^{commit}")
    require(revision_result.returncode == 0 and FULL_COMMIT.fullmatch(revision_result.stdout.strip()) is not None,
            f"dense self-test cannot resolve a full candidate HEAD: {revision_result.stdout.strip()}")
    source_revision = revision_result.stdout.strip()
    context_controls = candidate_git_context_controls(source_revision)
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
            initialized = git(ROOT, "init", "--bare", str(empty_evidence))
            require(initialized.returncode == 0, f"empty baseline store init failed:\n{initialized.stdout}")
            check_repository(mutant_root, empty_evidence, "REJECT baseline-object-unavailable:")
            wrong_evidence = Path(mutant_name) / "wrong-baseline.git"
            unrelated_source = Path(mutant_name) / "unrelated-source"
            wrong_evidence.mkdir()
            unrelated_source.mkdir()
            initialized = git(ROOT, "init", "--bare", str(wrong_evidence))
            require(initialized.returncode == 0, f"wrong baseline store init failed:\n{initialized.stdout}")
            initialized = git(ROOT, "init", str(unrelated_source))
            require(initialized.returncode == 0, f"unrelated source repository init failed:\n{initialized.stdout}")
            unrelated_commit = git(unrelated_source, "-c", "user.name=Fixture Control",
                                   "-c", "user.email=fixture-control@example.invalid", "commit", "--allow-empty",
                                   "-m", "unrelated baseline identity")
            require(unrelated_commit.returncode == 0, f"unrelated identity creation failed:\n{unrelated_commit.stdout}")
            unrelated_identity = git(unrelated_source, "rev-parse", "HEAD")
            require(unrelated_identity.returncode == 0, f"unrelated identity lookup failed:\n{unrelated_identity.stdout}")
            fetched_wrong = git(wrong_evidence, "fetch", "--no-tags",
                                str(unrelated_source), unrelated_identity.stdout.strip())
            require(fetched_wrong.returncode == 0, f"wrong identity object copy failed:\n{fetched_wrong.stdout}")
            check_repository(mutant_root, wrong_evidence, "REJECT baseline-object-unavailable:")
            pins = install_candidate_git_context(mutant_root, source_revision)
            require(len(pins) == len(active_admission_pins(ROOT, source_revision)),
                    "candidate-backed mutant has an incomplete admission pin set")
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
            candidate_dirty_core_definitions = [
                line for line in ninja_files.splitlines()
                if f'-DGBB_BUILD_REVISION=\\"{source_revision}\\"' in line and
                "-DGBB_BUILD_QUALIFIED=0" in line
            ]
            require(candidate_dirty_core_definitions,
                    "dirty candidate-backed mutant did not retain its candidate revision as unqualified")
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
            changed_pins = install_candidate_git_context(changed_subject, source_revision)
            require(changed_pins == pins, "changed-fixture control has a different admission pin set")
            changed_fixture = changed_subject / "fixtures/tracer/tracer.gb"
            require(changed_fixture.is_file(), "fixture-byte negative-control input is missing")
            changed_fixture.write_bytes(changed_fixture.read_bytes() + b"\ncontrolled mutation\n")
            check_repository(changed_subject, baseline_object_root, "REJECT record-field-missing:")

            source_archive = Path(mutant_name) / "source-archive"
            source_archive_build = Path(mutant_name) / "source-archive-build"
            source_archive.mkdir()
            copy_tracked_source(source_archive)
            archive_configure = run(["cmake", "-S", str(source_archive), "-B", str(source_archive_build),
                                     "-G", "Ninja", "-DCMAKE_BUILD_TYPE=Debug", "-DBUILD_TESTING=ON"],
                                    cwd=source_archive, timeout=180)
            require(archive_configure.returncode == 0,
                    f"Gitless source-archive configure failed:\n{archive_configure.stdout}")
            archive_ninja = (source_archive_build / "build.ninja").read_text(encoding="utf-8")
            archive_core_definitions = [
                line for line in archive_ninja.splitlines()
                if '-DGBB_BUILD_REVISION=\\"unknown\\"' in line and
                "-DGBB_BUILD_QUALIFIED=0" in line
            ]
            require(archive_core_definitions,
                    "Gitless source archive did not retain the unqualified unknown revision")

        print("dense-input status=pass ordered_events=67 same_timestamp=true")
        print("dense-input baseline=pass fields=" + ",".join(comparisons))
        print("dense-input documentation-contract=pass stale-limit-control=pass")
        print("dense-input failure-diagnostic=pass capped_bytes=" + str(len(stall_bytes)))
        print("dense-input no-refill-mutant=failed-as-expected reason=predicate-not-reached")
        print("dense-input immutable-baseline=separate-object-store full-identity=verified")
        print("dense-input baseline-controls=missing-object,wrong-identity,changed-fixture-rejected")
        print(f"dense-input candidate-context=pass rev={source_revision} controls={context_controls}")
        print("dense-input candidate-mutant=dirty-unqualified source-archive=unknown-unqualified")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, subprocess.TimeoutExpired) as error:
        print(f"verify-dense-input: FAIL: {error}", file=sys.stderr)
        raise SystemExit(1)
