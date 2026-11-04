#!/usr/bin/env python3
"""Check the exact v0.4.0 release version is pinned into its trusted workflows."""
from __future__ import annotations

import argparse
import copy
import importlib.util
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_PATHS = {
    "release-please.yml": ".github/workflows/release-please.yml",
    "version-pr-gate.yml": ".github/workflows/version-pr-gate.yml",
    "release.yml": ".github/workflows/release.yml",
}
WINDOW_STEPS = {
    "release-please.yml": (
        "version-window", "Judge the regenerated version PR against its frozen window", False,
        "trusted/tests/scripts/verify-version-window.py",
    ),
    "version-pr-gate.yml": (
        "pre-tag-gate", "Judge the version window on the exact PR base", False,
        "trusted/tests/scripts/verify-version-window.py",
    ),
    "release.yml": (
        "candidate", "Require an active version window at the exact source SHA", True,
        "$RUNNER_TEMP/verify-version-window.py",
    ),
}
VERSION = "0.4.0"


class Reject(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def git(repo: Path, *args: str, timeout: int = 15, check: bool = True) -> bytes:
    env = os.environ.copy()
    env["GIT_NO_REPLACE_OBJECTS"] = "1"
    env["GIT_NO_LAZY_FETCH"] = "1"
    result = subprocess.run(["git", *args], cwd=repo, env=env, capture_output=True,
                            check=False, timeout=timeout)
    if check and result.returncode != 0:
        raise Reject("release-policy-git", result.stderr.decode("utf-8", "replace")[:1000])
    return result.stdout


def resolve_revision(repo: Path, revision: str) -> str:
    if not re.fullmatch(r"[0-9a-f]{40,64}", revision):
        raise Reject("release-policy-revision", "revision must be a full immutable Git commit ID")
    resolved = git(repo, "rev-parse", "--verify", "--quiet", f"{revision}^{{commit}}").decode().strip()
    if resolved != revision:
        raise Reject("release-policy-revision", "revision did not resolve to the exact commit ID")
    return resolved


def git_blob(repo: Path, revision: str, path: str, maximum: int = 2 * 1024 * 1024) -> bytes:
    result = git(repo, "show", f"{revision}:{path}")
    if len(result) > maximum:
        raise Reject("release-policy-input-too-large", f"{path} exceeds the input limit")
    return result


def load_workflow_policy_parser():
    path = ROOT / ".github/scripts/verify-workflow-policy.py"
    spec = importlib.util.spec_from_file_location("gbb_trusted_workflow_policy", path)
    if spec is None or spec.loader is None:
        raise Reject("release-policy-parser-unavailable", "trusted workflow parser could not be loaded")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_workflows(repo: Path, revision: str, policy) -> dict[str, dict]:
    documents = {}
    with tempfile.TemporaryDirectory(prefix="gbb-v04-release-policy-") as temporary:
        directory = Path(temporary)
        for name, relative in WORKFLOW_PATHS.items():
            target = directory / name
            target.write_bytes(git_blob(repo, revision, relative))
            documents[name] = policy.read_workflow(target)
    return documents


def named_step(document: dict, workflow: str, job_name: str, step_name: str) -> dict:
    job = document.get("jobs", {}).get(job_name)
    if not isinstance(job, dict):
        raise Reject("release-policy-step-missing", f"{workflow} is missing job {job_name}")
    matches = [step for step in job.get("steps", []) if step.get("name") == step_name]
    if len(matches) != 1:
        raise Reject("release-policy-step-missing", f"{workflow} must contain one {step_name!r} step")
    return matches[0]


def shell_events(policy, step: dict, workflow: str) -> list:
    try:
        return policy.shell_events(step.get("run", ""))
    except Exception as error:
        raise Reject("release-policy-shell-invalid", f"{workflow} step has unsupported shell syntax") from error


def checker_invocations(policy, step: dict, workflow: str, script_path: str) -> list[list[str]]:
    events = shell_events(policy, step, workflow)
    return [event.words for event in events
            if event.words[:3] == ["python3", "-I", script_path]]


def has_option(words: list[str], option: str, value: str) -> bool:
    return words.count(option) == 1 and words.index(option) + 1 < len(words) \
        and words[words.index(option) + 1] == value


def validate_pr_window(policy, step: dict, workflow: str, script_path: str) -> None:
    invocations = checker_invocations(policy, step, workflow, script_path)
    if len(invocations) != 2:
        raise Reject("release-policy-version-window-call", f"{workflow} must separately check the active window and tracked output")
    active = [words for words in invocations if "--check" in words and "--check-tracked" not in words]
    tracked = [words for words in invocations if "--check-tracked" in words]
    if len(active) != 1 or len(tracked) != 1:
        raise Reject("release-policy-version-window-call", f"{workflow} must have one active-window check and one tracked-output check")
    if active[0].count("--check") != 1 or "--expect-version" in active[0]:
        raise Reject("release-policy-inactive-window-pin", f"{workflow} active-window check must allow the normal inactive pre-freeze record")
    if (tracked[0].count("--check-tracked") != 1 or "--check" in tracked[0]
            or not has_option(tracked[0], "--expect-version", VERSION)
            or not has_option(tracked[0], "--repo", "version-pr")
            or not has_option(tracked[0], "--rev", "$PR_HEAD")):
        raise Reject("release-policy-version-pin", f"{workflow} tracked version check must pin {VERSION} on the exact PR head")

    adoption_path = "trusted/tests/scripts/verify-v02-adoption.py"
    adoption_calls = [event.words for event in shell_events(policy, step, workflow)
                      if event.words[:3] == ["python3", "-I", adoption_path]]
    if (len(adoption_calls) != 1
            or not has_option(adoption_calls[0], "--release-notes", "$RUNNER_TEMP/version-pr-body.md")
            or not has_option(adoption_calls[0], "--repo", "version-pr")
            or not has_option(adoption_calls[0], "--rev", "$PR_HEAD")):
        raise Reject("release-policy-notes-call", f"{workflow} must validate the exact PR release-notes body")


def validate_release_window(policy, step: dict, workflow: str, script_path: str) -> None:
    invocations = checker_invocations(policy, step, workflow, script_path)
    if len(invocations) != 1:
        raise Reject("release-policy-version-window-call", f"{workflow} must execute one trusted version-window checker")
    words = invocations[0]
    if (words.count("--check-tracked") != 1 or words.count("--check") != 0
            or words.count("--require-active") != 1
            or not has_option(words, "--expect-version", VERSION)):
        raise Reject("release-policy-version-pin", f"{workflow} must require an active exact {VERSION} tracked window")


def validate_version_pin(words: list[str], workflow: str) -> None:
    if words.count("--expect-version") != 1:
        raise Reject("release-policy-version-pin", f"{workflow} must pin exactly one expected release version")
    index = words.index("--expect-version")
    if index + 1 >= len(words) or words[index + 1] != VERSION:
        raise Reject("release-policy-version-pin", f"{workflow} must require version {VERSION}")


def validate_documents(documents: dict[str, dict], policy) -> None:
    for workflow, (job, step_name, require_active, script_path) in WINDOW_STEPS.items():
        step = named_step(documents[workflow], workflow, job, step_name)
        if require_active:
            validate_release_window(policy, step, workflow, script_path)
        else:
            validate_pr_window(policy, step, workflow, script_path)

    release = documents["release.yml"]
    identity = named_step(
        release, "release.yml", "candidate",
        "Require trusted repository, main workflow ref, and exact tag identity",
    )
    guards = [event.words for event in shell_events(policy, identity, "release.yml")
              if event.words == ["[[", "$RELEASE_TAG", "==", "v0.4.0", "]]"]]
    if len(guards) != 1:
        raise Reject("release-policy-tag-pin", "release.yml must accept only the v0.4.0 candidate tag")


def self_test(documents: dict[str, dict], policy) -> tuple[int, int]:
    controls = 0
    positives = 0

    def accepted(label: str, candidate: dict[str, dict]) -> None:
        nonlocal positives
        try:
            validate_documents(candidate, policy)
        except Reject as error:
            raise SystemExit(f"release workflow positive {label} was rejected: {error.code}: {error}") from error
        positives += 1

    def rejected(label: str, candidate: dict[str, dict], expected: str) -> None:
        nonlocal controls
        try:
            validate_documents(candidate, policy)
        except Reject as error:
            if error.code != expected:
                raise SystemExit(f"release workflow control {label} failed for {error.code}, expected {expected}") from error
            controls += 1
            return
        raise SystemExit(f"release workflow control {label} accepted a weakened version gate")

    for workflow, (job, step_name, require_active, _script_path) in WINDOW_STEPS.items():
        accepted("valid " + workflow + " counterpart", copy.deepcopy(documents))
        mutant = copy.deepcopy(documents)
        step = named_step(mutant[workflow], workflow, job, step_name)
        original = step["run"]
        if original.count("--expect-version 0.4.0") != 1:
            raise SystemExit(f"release workflow self-test anchor is absent in {workflow}")
        step["run"] = original.replace("--expect-version 0.4.0", "", 1)
        rejected(workflow + " missing expected version", mutant, "release-policy-version-pin")

        accepted("valid " + workflow + " counterpart", copy.deepcopy(documents))
        mutant = copy.deepcopy(documents)
        step = named_step(mutant[workflow], workflow, job, step_name)
        step["run"] = step["run"].replace("--expect-version 0.4.0", "--expect-version 0.3.0", 1)
        rejected(workflow + " wrong expected version", mutant, "release-policy-version-pin")

        if not require_active:
            accepted("inactive pre-freeze counterpart", copy.deepcopy(documents))
            mutant = copy.deepcopy(documents)
            step = named_step(mutant[workflow], workflow, job, step_name)
            anchor = "--check tests/data/version-window.json"
            if step["run"].count(anchor) != 1:
                raise SystemExit(f"release workflow self-test active-check anchor is absent in {workflow}")
            step["run"] = step["run"].replace(anchor, anchor + " --expect-version 0.4.0", 1)
            rejected(workflow + " pins the inactive pre-freeze window", mutant,
                     "release-policy-inactive-window-pin")

            accepted("release-notes validation counterpart", copy.deepcopy(documents))
            mutant = copy.deepcopy(documents)
            step = named_step(mutant[workflow], workflow, job, step_name)
            anchor = "python3 -I trusted/tests/scripts/verify-v02-adoption.py --release-notes"
            if step["run"].count(anchor) != 1:
                raise SystemExit(f"release workflow self-test notes-validator anchor is absent in {workflow}")
            step["run"] = step["run"].replace(anchor, "python3 -I trusted/tests/scripts/untrusted-notes.py --release-notes", 1)
            rejected(workflow + " omits trusted release-notes validation", mutant, "release-policy-notes-call")

    accepted("valid v0.4.0 tag counterpart", copy.deepcopy(documents))
    mutant = copy.deepcopy(documents)
    identity = named_step(mutant["release.yml"], "release.yml", "candidate",
                          "Require trusted repository, main workflow ref, and exact tag identity")
    if identity["run"].count('[[ "$RELEASE_TAG" == "v0.4.0" ]]') != 1:
        raise SystemExit("release workflow self-test tag-guard anchor is absent")
    identity["run"] = identity["run"].replace('[[ "$RELEASE_TAG" == "v0.4.0" ]]',
                                               '[[ "$RELEASE_TAG" == "v0.4.1" ]]', 1)
    rejected("release tag accepts the wrong version", mutant, "release-policy-tag-pin")
    return positives, controls


def load_source_and_workflows(repo: Path, revision: str):
    revision = resolve_revision(repo, revision)
    current_source = Path(__file__).read_bytes()
    committed_source = git_blob(repo, revision, "tests/scripts/verify-v04-release-policy.py", 256 * 1024)
    if current_source != committed_source:
        raise Reject("release-policy-checker-source-mismatch", "executing checker differs from its immutable Git blob")
    policy = load_workflow_policy_parser()
    return revision, policy, read_workflows(repo, revision, policy)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--self-test", action="store_true")
    parser.add_argument("--repo", type=Path, default=ROOT)
    parser.add_argument("--rev", required=True)
    args = parser.parse_args()
    repo = args.repo.resolve(strict=True)
    try:
        revision, policy, documents = load_source_and_workflows(repo, args.rev)
        if args.self_test:
            positives, controls = self_test(documents, policy)
            print(f"release workflow v0.4.0 controls pass positives={positives} controls={controls} rev={revision}")
        else:
            validate_documents(documents, policy)
            print(f"release workflow v0.4.0 pins pass rev={revision}")
        return 0
    except Reject as error:
        print(f"REJECT {error.code}: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
