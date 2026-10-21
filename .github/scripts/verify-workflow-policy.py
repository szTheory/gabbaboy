#!/usr/bin/env python3
"""Judge the privilege and trust wiring of the release workflows.

This is deliberately not a general YAML or shell parser. It reads the one block
shape these workflows use (mappings, sequences, literal and folded block scalars,
simple flow lists), refuses everything else (anchors, aliases, tags, tabs, flow
maps, duplicate keys, multi-line plain scalars) and then classifies every job by
role: unprivileged producer, trusted reader, minimal attacher, or a named
residual. Roles are enforced from jobs, permissions, needs, checkout inputs and
artifact steps, never from substrings of the file.

The judge never imports or executes anything from the tree it judges. Run it from
a trusted checkout and pass the subject tree as --root (data only).
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import tempfile
from pathlib import Path


class Reject(Exception):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"REJECT {code}: {message}")


# --------------------------------------------------------------------------- reader
_KEY = re.compile(r"""^([A-Za-z0-9_][A-Za-z0-9_.-]*):(?:\s+(.*))?$""")
_BLOCK = {"|", "|-", "|+", ">", ">-", ">+"}


def _unsupported(name: str, what: str) -> Reject:
    return Reject("workflow-unsupported-yaml", f"{name}: {what}")


def _scalar(raw: str, name: str) -> str:
    value = raw.strip()
    if not value:
        return ""
    if value[0] in "&*!@`%{" or value.startswith("<<"):
        raise _unsupported(name, f"unsupported value {value[:30]!r}")
    if value[0] in "'\"":
        end = value.find(value[0], 1)
        if end < 0 or value[end + 1 :].strip() not in ("",) and not value[end + 1 :].strip().startswith("#"):
            raise _unsupported(name, f"unsupported quoted value {value[:30]!r}")
        return value[1:end]
    cut = value.find(" #")
    return value[:cut].rstrip() if cut >= 0 else value


def _flow_list(raw: str, name: str) -> list[str]:
    inner = raw.strip()[1:-1]
    if any(ch in inner for ch in "[]{}"):
        raise _unsupported(name, f"unsupported flow list {raw[:40]!r}")
    return [_scalar(part, name) for part in inner.split(",") if part.strip()]


class _Reader:
    def __init__(self, text: str, name: str) -> None:
        if "\t" in text or "\r" in text:
            raise _unsupported(name, "tabs and carriage returns are unsupported")
        self.name = name
        self.lines = text.split("\n")
        self.i = 0

    def peek(self) -> tuple[int, str] | None:
        while self.i < len(self.lines):
            line = self.lines[self.i]
            body = line.strip()
            if not body or body.startswith("#"):
                self.i += 1
                continue
            return len(line) - len(line.lstrip(" ")), body
        return None

    def block_scalar(self, indent: int) -> str:
        collected: list[str] = []
        block_indent = None
        while self.i < len(self.lines):
            line = self.lines[self.i]
            if line.strip():
                width = len(line) - len(line.lstrip(" "))
                if width <= indent:
                    break
                block_indent = width if block_indent is None else min(block_indent, width)
            collected.append(line)
            self.i += 1
        width = block_indent or 0
        return "\n".join(line[width:] if line.strip() else "" for line in collected).rstrip("\n")

    def mapping(self, indent: int) -> dict:
        result: dict = {}
        while True:
            head = self.peek()
            if head is None or head[0] < indent:
                return result
            if head[0] > indent:
                raise _unsupported(self.name, f"unexpected indentation near {head[1][:50]!r}")
            body = head[1]
            if body.startswith("- "):
                raise _unsupported(self.name, f"unexpected sequence item near {body[:50]!r}")
            match = _KEY.match(body)
            if not match:
                raise _unsupported(self.name, f"unsupported mapping row {body[:50]!r}")
            key, raw = match.group(1), match.group(2) or ""
            if key in result:
                raise Reject("workflow-duplicate-key", f"{self.name}: duplicate key {key}")
            self.i += 1
            stripped = raw.strip()
            if stripped in _BLOCK:
                result[key] = self.block_scalar(indent)
            elif stripped.startswith("["):
                if not stripped.endswith("]"):
                    raise _unsupported(self.name, f"unterminated flow list for {key}")
                result[key] = _flow_list(stripped, self.name)
            elif stripped == "" or stripped.startswith("#"):
                nxt = self.peek()
                if nxt is not None and (nxt[0] > indent or (nxt[0] == indent and nxt[1].startswith("- "))):
                    result[key] = self.sequence(nxt[0]) if nxt[1].startswith("- ") else self.mapping(nxt[0])
                else:
                    result[key] = ""
            else:
                result[key] = _scalar(raw, self.name)

    def sequence(self, indent: int) -> list:
        result: list = []
        while True:
            head = self.peek()
            if head is None or head[0] != indent or not head[1].startswith("- "):
                if head is not None and head[0] > indent:
                    raise _unsupported(self.name, f"unexpected indentation near {head[1][:50]!r}")
                return result
            rest = head[1][2:]
            if _KEY.match(rest):
                self.lines[self.i] = " " * (indent + 2) + rest
                result.append(self.mapping(indent + 2))
            else:
                if rest.strip()[:1] in "[{":
                    raise _unsupported(self.name, "nested flow collections are unsupported")
                result.append(_scalar(rest, self.name))
                self.i += 1


def read_workflow(path: Path) -> dict:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise Reject("workflow-unavailable", f"cannot read {path.name}: {exc.strerror}") from exc
    reader = _Reader(text, path.name)
    tree = reader.mapping(0)
    if reader.peek() is not None:
        raise _unsupported(path.name, "content after the root mapping")
    jobs = tree.get("jobs")
    if not isinstance(jobs, dict) or not jobs:
        raise _unsupported(path.name, "missing jobs mapping")
    for job_id, job in jobs.items():
        if not isinstance(job, dict):
            raise _unsupported(path.name, f"job {job_id} is not a mapping")
        steps = job.get("steps", [])
        if not isinstance(steps, list) or not all(isinstance(step, dict) for step in steps):
            raise _unsupported(path.name, f"job {job_id} steps are not a list of mappings")
    return tree


# --------------------------------------------------------------------------- helpers
def _needs(job: dict) -> set[str]:
    needs = job.get("needs", [])
    return set(needs) if isinstance(needs, list) else ({needs} if needs else set())


def _permissions(job: dict, top: dict) -> dict[str, str]:
    """GitHub grants only what a job lists once it lists any; an omitted block inherits the top level."""
    declared = job["permissions"] if "permissions" in job else top.get("permissions", {})
    if isinstance(declared, str):
        # read-all/write-all or an empty block: treat the broad forms as writable, fail closed.
        return {"*": "write"} if declared == "write-all" else ({"*": "read"} if declared == "read-all" else {})
    return dict(declared)


def _writes(perms: dict[str, str]) -> bool:
    return any(value == "write" for value in perms.values())


def _checkouts(job: dict) -> list[dict]:
    return [step for step in job.get("steps", []) if str(step.get("uses", "")).startswith("actions/checkout@")]


def _artifact_steps(job: dict, kind: str) -> list[dict]:
    return [step for step in job.get("steps", []) if str(step.get("uses", "")).startswith(f"actions/{kind}-artifact@")]


_TOKEN = re.compile(r"github\.token|secrets\.|GH_TOKEN|GITHUB_TOKEN")
_WRITE_COMMAND = re.compile(r"(?m)(?:^|[\s;&|(])(?:gh\s+(?:release|api|pr|issue|run|workflow)|git\s+(?:push|remote|credential))\b")


def _strings(value) -> list[str]:
    if isinstance(value, dict):
        return [text for item in value.values() for text in _strings(item)]
    if isinstance(value, list):
        return [text for item in value for text in _strings(item)]
    return [str(value)]


def _where(workflow: str, job_id: str) -> str:
    return f"{workflow}.{job_id}"


def _check_actions(workflow: str, tree: dict) -> None:
    for job_id, job in tree["jobs"].items():
        for step in job.get("steps", []):
            uses = str(step.get("uses", ""))
            if uses and not uses.startswith("./") and not re.fullmatch(r"[\w.-]+/[\w./-]+@[0-9a-f]{40}", uses):
                raise Reject("workflow-unpinned-action", f"{_where(workflow, job_id)} uses an action not pinned to a full commit: {uses}")
        if "uses" in job and not str(job["uses"]).startswith("./"):
            raise Reject("workflow-unpinned-action", f"{_where(workflow, job_id)} calls an unpinned reusable workflow")


def _check_checkout_credentials(workflow: str, tree: dict, job_ids) -> None:
    for job_id in job_ids:
        for step in _checkouts(tree["jobs"][job_id]):
            if str(step.get("with", {}).get("persist-credentials", "")).lower() != "false":
                raise Reject("checkout-credentials", f"{_where(workflow, job_id)} checkout must set persist-credentials: false")


def _upload(job: dict, workflow: str, job_id: str, name: str, must_contain: tuple[str, ...]) -> None:
    uploads = _artifact_steps(job, "upload")
    matching = [step for step in uploads if step.get("with", {}).get("name") == name]
    if len(matching) != 1:
        raise Reject("artifact-flow", f"{_where(workflow, job_id)} must retain exactly one artifact named {name}")
    inputs = matching[0]["with"]
    if inputs.get("if-no-files-found") != "error" or any(item not in str(inputs.get("path", "")) for item in must_contain):
        raise Reject("artifact-flow", f"{_where(workflow, job_id)} artifact {name} must fail on a missing file and carry {must_contain}")
    if str(matching[0].get("if", "")).strip() not in ("", "${{ success() }}"):
        raise Reject("artifact-flow", f"{_where(workflow, job_id)} artifact upload must not be conditional")


def _download(job: dict, workflow: str, job_id: str, name: str) -> None:
    if not any(step.get("with", {}).get("name") == name for step in _artifact_steps(job, "download")):
        raise Reject("artifact-flow", f"{_where(workflow, job_id)} must download retained artifact {name}")


def _check_unprivileged(workflow: str, tree: dict, job_id: str) -> None:
    """A producer runs subject code with a read-only job token and no token it could use or leak."""
    job = tree["jobs"][job_id]
    perms = _permissions(job, tree.get("permissions", {}))
    if _writes(perms):
        raise Reject("producer-write-authority", f"{_where(workflow, job_id)} runs producer work with write authority")
    if "permissions" in job and perms != {"contents": "read"}:
        raise Reject("producer-permissions", f"{_where(workflow, job_id)} must hold only contents: read")
    if any(_TOKEN.search(text) for text in _strings({k: v for k, v in job.items() if k != "name"})):
        raise Reject("producer-token", f"{_where(workflow, job_id)} references the job token or a secret")
    if any(_WRITE_COMMAND.search(step.get("run", "")) for step in job.get("steps", [])):
        raise Reject("producer-write-command", f"{_where(workflow, job_id)} runs a repository-write or API command")


def _check_trusted_checkout(workflow: str, job_id: str, job: dict, expected_ref: str, expected_path: str) -> None:
    """A judge, reader or attacher checks out only the trusted workflow revision, never the subject ref."""
    steps = _checkouts(job)
    if len(steps) != 1:
        raise Reject("judge-trust", f"{_where(workflow, job_id)} needs exactly one trusted checkout")
    inputs = steps[0].get("with", {})
    if inputs.get("ref") != expected_ref or inputs.get("path") != expected_path:
        raise Reject("judge-trust", f"{_where(workflow, job_id)} trusted checkout must be ref {expected_ref} at path {expected_path}")


def _require_needs(workflow: str, job_id: str, job: dict, needed: set[str], code: str) -> None:
    missing = needed - _needs(job)
    if missing:
        raise Reject(code, f"{_where(workflow, job_id)} must depend on {sorted(missing)}")


def _require_job(workflow: str, tree: dict, job_id: str) -> dict:
    job = tree["jobs"].get(job_id)
    if job is None:
        raise Reject("workflow-job-missing", f"{workflow} is missing job {job_id}")
    return job


# --------------------------------------------------------------------------- policy
REHEARSAL_PRODUCERS = ("corpus", "fuzz", "performance", "package", "aggregate")
REHEARSAL_FUZZ_ARTIFACT = "rehearsal-fuzz-${{ github.run_id }}-${{ github.run_attempt }}"
DEFAULT_BRANCH_REF = "${{ github.event.repository.default_branch }}"
TRUSTED_SHA_REF = "${{ github.sha }}"

RELEASE_ROLES = {
    "release": "release-please",
    "candidate": "residual",
    "candidate-macos": "residual",
    "candidate-windows": "residual",
    "candidate-platform-manifest": "residual",
    "publish-qualified-release": "residual",
    "candidate-corpus": "producer",
    "candidate-performance": "producer",
    "candidate-fuzz": "trusted-reader",
    "attach-v02-evidence": "attacher",
}
RELEASE_ARTIFACTS = {
    "candidate-corpus": ("release-evidence-corpus", ("build/cgb-corpus-receipt.json", "build/support-ledger.json")),
    "candidate-performance": ("release-evidence-performance", ("build/v02-performance-receipt.json",)),
    "candidate-fuzz": ("release-evidence-fuzz", ("build/ci-fuzz/v02-fuzz-receipt.json",)),
}
SUBJECT_REF = "${{ env.SOURCE_SHA }}"


def check_rehearsal(root: Path) -> None:
    name = "release-rehearsal"
    tree = read_workflow(root / ".github/workflows/release-rehearsal.yml")
    if tree.get("permissions") != {"contents": "read"}:
        raise Reject("workflow-permissions", f"{name} must declare only top-level contents: read")
    _check_actions(name, tree)
    _check_checkout_credentials(name, tree, tree["jobs"])
    for job_id, job in tree["jobs"].items():
        if _writes(_permissions(job, tree["permissions"])):
            raise Reject("producer-write-authority", f"{_where(name, job_id)} holds write authority in a non-publishing rehearsal")
    for job_id in REHEARSAL_PRODUCERS:
        _require_job(name, tree, job_id)
        _check_unprivileged(name, tree, job_id)
    _upload(tree["jobs"]["fuzz"], name, "fuzz", REHEARSAL_FUZZ_ARTIFACT, ("build-asan/v02-fuzz-receipt.json",))

    judge = _require_job(name, tree, "judge")
    _require_needs(name, "judge", judge, set(REHEARSAL_PRODUCERS), "workflow-dependency")
    if "if" in judge:
        raise Reject("workflow-dependency", f"{_where(name, 'judge')} must run unconditionally after every producer")
    _check_unprivileged(name, tree, "judge")
    checkouts = {step.get("with", {}).get("path"): step.get("with", {}) for step in _checkouts(judge)}
    if set(checkouts) != {"trusted-judge", "subject"}:
        raise Reject("judge-trust", f"{_where(name, 'judge')} needs one trusted-judge checkout and one subject-data checkout")
    if checkouts["trusted-judge"].get("ref") != DEFAULT_BRANCH_REF:
        raise Reject("judge-trust", f"{_where(name, 'judge')} judge code must come from the default branch, not the rehearsed subject")
    if checkouts["subject"].get("ref", TRUSTED_SHA_REF) != TRUSTED_SHA_REF:
        raise Reject("judge-trust", f"{_where(name, 'judge')} subject data must be the rehearsed commit")
    _download(judge, name, "judge", REHEARSAL_FUZZ_ARTIFACT)
    for step in judge.get("steps", []):
        if re.search(r"(?:^|[\s=\"'])\.?/?subject/", step.get("run", "")):
            raise Reject("judge-subject-execution", f"{_where(name, 'judge')} names a path inside the subject tree; subject files are data only")


def check_ci(root: Path) -> None:
    name = "ci"
    tree = read_workflow(root / ".github/workflows/ci.yml")
    if tree.get("permissions") != {"contents": "read"}:
        raise Reject("workflow-permissions", "ci must declare only top-level contents: read")
    _check_actions(name, tree)
    job = _require_job(name, tree, "linux-sanitizers")
    perms = _permissions(job, tree["permissions"])
    if perms != {"actions": "read", "contents": "read"}:
        raise Reject("fuzz-producer-permissions", "ci.linux-sanitizers must hold only actions: read and contents: read")
    _check_checkout_credentials(name, tree, ("linux-sanitizers",))
    _upload(job, name, "linux-sanitizers", "v02-fuzz-${{ github.run_id }}-${{ github.run_attempt }}",
            ("build-asan/v02-fuzz-receipt.json", "build-asan/fuzz-artifacts/"))
    if any(_writes(_permissions(item, tree["permissions"])) for item in tree["jobs"].values()):
        raise Reject("producer-write-authority", "ci must not grant write authority to any job")


def check_release(root: Path) -> None:
    name = "release"
    tree = read_workflow(root / ".github/workflows/release.yml")
    if tree.get("permissions") != {"contents": "read"}:
        raise Reject("workflow-permissions", "release must declare only top-level contents: read")
    _check_actions(name, tree)
    jobs = tree["jobs"]
    for job_id in jobs:
        if job_id not in RELEASE_ROLES:
            raise Reject("job-unclassified", f"{_where(name, job_id)} has no declared trust role; classify it in the policy")
    for job_id, role in RELEASE_ROLES.items():
        job = _require_job(name, tree, job_id)
        perms = _permissions(job, tree["permissions"])
        if role in ("producer", "trusted-reader") and _writes(perms):
            raise Reject("producer-write-authority", f"{_where(name, job_id)} runs {role} work with write authority")
        if role == "producer":
            _check_unprivileged(name, tree, job_id)
            _check_checkout_credentials(name, tree, (job_id,))
            _require_needs(name, job_id, job, {"release", "candidate"}, "workflow-dependency")
            checkouts = _checkouts(job)
            if len(checkouts) != 1 or checkouts[0].get("with", {}).get("ref") != SUBJECT_REF:
                raise Reject("producer-checkout", f"{_where(name, job_id)} must check out exactly the tagged source")
            artifact, files = RELEASE_ARTIFACTS[job_id]
            _upload(job, name, job_id, artifact, files)
        elif role == "trusted-reader":
            if perms != {"actions": "read", "contents": "read"}:
                raise Reject("reader-permissions", f"{_where(name, job_id)} needs only actions: read and contents: read")
            _check_checkout_credentials(name, tree, (job_id,))
            _check_trusted_checkout(name, job_id, job, TRUSTED_SHA_REF, "trusted")
            _require_needs(name, job_id, job, {"release", "candidate"}, "workflow-dependency")
            artifact, files = RELEASE_ARTIFACTS[job_id]
            _upload(job, name, job_id, artifact, files)
        elif role == "attacher":
            if perms != {"contents": "write"}:
                raise Reject("attacher-permissions", f"{_where(name, job_id)} must hold exactly contents: write")
            _check_checkout_credentials(name, tree, (job_id,))
            _check_trusted_checkout(name, job_id, job, TRUSTED_SHA_REF, "trusted")
            _require_needs(name, job_id, job, {"release", "candidate", "candidate-corpus", "candidate-fuzz", "candidate-performance"}, "attacher-dependencies")
            for producer in ("candidate-corpus", "candidate-fuzz", "candidate-performance"):
                _download(job, name, job_id, RELEASE_ARTIFACTS[producer][0])
                if f"needs.{producer}.result == 'success'" not in str(job.get("if", "")):
                    raise Reject("attacher-dependencies", f"{_where(name, job_id)} must run only after {producer} succeeded")
            if any(re.search(r"(?m)(?:^|[\s;&|(])(?:cmake|ctest|make|ninja)\s|(?:^|[\s\"'=])(?:\./)?tests/scripts/", step.get("run", "")) for step in job.get("steps", [])):
                raise Reject("attacher-subject-execution", f"{_where(name, job_id)} must execute trusted code only")
    _require_needs(name, "candidate-platform-manifest", jobs["candidate-platform-manifest"], {"attach-v02-evidence"}, "workflow-dependency")


def check_all(root: Path) -> dict[str, int]:
    check_rehearsal(root)
    check_ci(root)
    check_release(root)
    residual = sorted(job_id for job_id, role in RELEASE_ROLES.items() if role == "residual")
    return {"residual": len(residual)}


# --------------------------------------------------------------------------- self-test
WORKFLOWS = ("release-rehearsal.yml", "release.yml", "ci.yml")


def _copy_fixture(root: Path, target: Path) -> None:
    for item in WORKFLOWS:
        destination = target / ".github/workflows" / item
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes((root / ".github/workflows" / item).read_bytes())


def _run_cli(fixture: Path, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-I", str(Path(__file__).resolve()), "--check", "--root", str(fixture)],
        capture_output=True, text=True, check=False, cwd=cwd, timeout=60,
    )


def _mutations(root: Path) -> list[tuple[str, str, str, str, str]]:
    """(label, workflow, old, new, expected diagnostic code). Each anchor must exist in the production file."""
    return [
        ("rehearsal fuzz producer gains contents: write", "release-rehearsal.yml",
         "  fuzz:\n    name: rehearse-clang-libfuzzer-campaign\n    runs-on: ubuntu-24.04\n",
         "  fuzz:\n    name: rehearse-clang-libfuzzer-campaign\n    runs-on: ubuntu-24.04\n    permissions:\n      contents: write\n",
         "producer-write-authority"),
        ("rehearsal top-level write", "release-rehearsal.yml", "permissions:\n  contents: read\n",
         "permissions:\n  contents: write\n", "workflow-permissions"),
        ("rehearsal judge reads judge code from the subject", "release-rehearsal.yml",
         f"ref: {DEFAULT_BRANCH_REF}", f"ref: {TRUSTED_SHA_REF}", "judge-trust"),
        ("rehearsal judge runs a path inside the subject tree", "release-rehearsal.yml",
         "python3 -I trusted-judge/.github/scripts/verify-workflow-policy.py --check --root subject",
         "python3 -I subject/.github/scripts/verify-workflow-policy.py --check --root subject", "judge-subject-execution"),
        ("rehearsal judge stops waiting for the fuzz producer", "release-rehearsal.yml",
         "needs: [corpus, fuzz, performance, package, aggregate]", "needs: [corpus, performance, package, aggregate]",
         "workflow-dependency"),
        ("rehearsal fuzz artifact no longer retained", "release-rehearsal.yml",
         "name: " + REHEARSAL_FUZZ_ARTIFACT, "name: renamed-" + REHEARSAL_FUZZ_ARTIFACT, "artifact-flow"),
        ("rehearsal checkout persists credentials", "release-rehearsal.yml",
         "          fetch-depth: 0\n      - name: Create the local-only rehearsal tag\n",
         "          fetch-depth: 0\n          persist-credentials: true\n      - name: Create the local-only rehearsal tag\n",
         "checkout-credentials"),
        ("unpinned action", "release-rehearsal.yml", "actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02",
         "actions/upload-artifact@v4", "workflow-unpinned-action"),
        ("YAML anchor", "release-rehearsal.yml", "env:\n  REHEARSAL_TAG: v0.2.0\n", "env:\n  REHEARSAL_TAG: &tag v0.2.0\n",
         "workflow-unsupported-yaml"),
        ("release corpus producer gains contents: write", "release.yml",
         "  candidate-corpus:\n    name: exact-tag-corpus-and-support-sidecar\n    needs: [release, candidate]\n    if: ${{ always() && needs.candidate.result == 'success' }}\n    runs-on: ubuntu-22.04\n    timeout-minutes: 60\n    permissions:\n      contents: read\n",
         "  candidate-corpus:\n    name: exact-tag-corpus-and-support-sidecar\n    needs: [release, candidate]\n    if: ${{ always() && needs.candidate.result == 'success' }}\n    runs-on: ubuntu-22.04\n    timeout-minutes: 60\n    permissions:\n      contents: write\n",
         "producer-write-authority"),
        ("release corpus producer receives the job token", "release.yml",
         "  candidate-corpus:\n    name: exact-tag-corpus-and-support-sidecar\n",
         "  candidate-corpus:\n    env:\n      GH_TOKEN: ${{ github.token }}\n    name: exact-tag-corpus-and-support-sidecar\n",
         "producer-token"),
        ("release performance checkout persists credentials", "release.yml",
         "          ref: ${{ env.SOURCE_SHA }}\n          fetch-depth: 0\n          persist-credentials: false\n      - name: Measure",
         "          ref: ${{ env.SOURCE_SHA }}\n          fetch-depth: 0\n          persist-credentials: true\n      - name: Measure",
         "checkout-credentials"),
        ("release fuzz reader checks out the tagged subject", "release.yml",
         "          ref: ${{ github.sha }}\n          path: trusted\n          persist-credentials: false\n      - name: Require trusted main and read the exact CI campaign",
         "          ref: ${{ env.SOURCE_SHA }}\n          path: trusted\n          persist-credentials: false\n      - name: Require trusted main and read the exact CI campaign",
         "judge-trust"),
        ("release attacher checks out the tagged subject", "release.yml",
         "          ref: ${{ github.sha }}\n          path: trusted\n          persist-credentials: false\n      - name: Require the draft and attach",
         "          ref: ${{ env.SOURCE_SHA }}\n          path: trusted\n          persist-credentials: false\n      - name: Require the draft and attach",
         "judge-trust"),
        ("release attacher stops waiting for the corpus producer", "release.yml",
         "needs: [release, candidate, candidate-corpus, candidate-fuzz, candidate-performance]",
         "needs: [release, candidate, candidate-fuzz, candidate-performance]", "attacher-dependencies"),
        ("release manifest no longer waits for the attacher", "release.yml",
         "needs: [release, candidate, candidate-macos, candidate-windows, attach-v02-evidence]",
         "needs: [release, candidate, candidate-macos, candidate-windows]", "workflow-dependency"),
        ("new unclassified release job", "release.yml", "\njobs:\n", "\njobs:\n  surprise:\n    runs-on: ubuntu-22.04\n    steps:\n      - run: true\n",
         "job-unclassified"),
    ]


def self_test(root: Path) -> None:
    rejected = 0
    with tempfile.TemporaryDirectory(prefix="gbb-workflow-policy.") as directory:
        fixture = Path(directory) / "subject"
        work = Path(directory) / "work"
        work.mkdir()
        _copy_fixture(root, fixture)
        positive = _run_cli(fixture, work)
        if positive.returncode != 0 or "PASS: workflow privilege and trust wiring" not in positive.stdout:
            raise SystemExit(f"self-test positive control failed: exit={positive.returncode} stderr={positive.stderr.strip()!r}")
        baselines = {item: (fixture / ".github/workflows" / item).read_text(encoding="utf-8") for item in WORKFLOWS}
        for label, workflow, old, new, expected in _mutations(root):
            if old not in baselines[workflow]:
                raise SystemExit(f"self-test anchor missing for {label!r} in {workflow}")
            path = fixture / ".github/workflows" / workflow
            path.write_text(baselines[workflow].replace(old, new, 1), encoding="utf-8")
            result = _run_cli(fixture, work)
            diagnostic = result.stderr.strip()
            if result.returncode != 1 or f"REJECT {expected}:" not in diagnostic or "PASS:" in result.stdout:
                raise SystemExit(f"self-test negative {label!r} failed: want REJECT {expected}, exit={result.returncode}, "
                                 f"stdout={result.stdout!r}, stderr={diagnostic!r}")
            rejected += 1
            print(f"rejected: {label}: {diagnostic}")
            path.write_text(baselines[workflow], encoding="utf-8")
        # A subject that ships its own judge, and shadows standard-library modules, cannot change the verdict:
        # the trusted script ignores the subject tree except as workflow text.
        bad = baselines["release-rehearsal.yml"].replace("permissions:\n  contents: read\n", "permissions:\n  contents: write\n", 1)
        (fixture / ".github/workflows/release-rehearsal.yml").write_text(bad, encoding="utf-8")
        hostile = fixture / ".github/scripts/verify-workflow-policy.py"
        hostile.parent.mkdir(parents=True, exist_ok=True)
        hostile.write_text("print('PASS: workflow privilege and trust wiring')\nraise SystemExit(0)\n", encoding="utf-8")
        (fixture / "re.py").write_text("raise SystemExit('subject re.py executed')\n", encoding="utf-8")
        (fixture / "pathlib.py").write_text("raise SystemExit('subject pathlib.py executed')\n", encoding="utf-8")
        result = _run_cli(fixture, fixture)
        if result.returncode != 1 or "REJECT workflow-permissions:" not in result.stderr or "PASS:" in result.stdout:
            raise SystemExit(f"self-test hostile subject judge was not ignored: exit={result.returncode} stderr={result.stderr.strip()!r}")
        rejected += 1
        print("rejected: subject-supplied judge and shadowed modules cannot approve a mutated workflow")
    print(f"PASS: workflow policy self-test negative_controls={rejected} positive_controls=1")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--check", action="store_true", help="judge the workflow files under --root")
    modes.add_argument("--self-test", action="store_true", help="run positive and intended-defect controls through the CLI")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2],
                        help="tree whose .github/workflows files are judged as data")
    args = parser.parse_args()
    root = args.root.resolve()
    try:
        if args.self_test:
            self_test(root)
            return 0
        facts = check_all(root)
        print(f"PASS: workflow privilege and trust wiring residual_write_jobs={facts['residual']}")
        return 0
    except Reject as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
