#!/usr/bin/env python3
"""Validate new fixture records against immutable Git identities and product byte policy."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path, PurePosixPath


BASELINE_COMMIT = "7cc6495e64f3645caa120e7458f754585b788985"
MAX_MANIFEST_BYTES = 2 * 1024 * 1024
MAX_FILE_BYTES = 32 * 1024 * 1024
MAX_FILES = 4096
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
COMPONENTS = ("code", "art", "audio_driver", "build_inputs", "notices")


class Reject(Exception):
    def __init__(self, code: str, detail: str):
        super().__init__(f"REJECT {code}: {detail}")
        self.code = code


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise Reject("json-duplicate-key", key)
        result[key] = value
    return result


def reject_constant(value: str):
    raise Reject("json-non-finite", value)


def parse_json(raw: bytes, where: str) -> dict:
    if len(raw) > MAX_MANIFEST_BYTES:
        raise Reject("json-size-limit", where)
    try:
        text = raw.decode("utf-8", errors="strict")
        value = json.loads(text, object_pairs_hook=unique_pairs, parse_constant=reject_constant)
    except (UnicodeDecodeError, json.JSONDecodeError, Reject) as error:
        if isinstance(error, Reject):
            raise
        raise Reject("json-invalid", f"{where}: {error}") from None
    if not isinstance(value, dict):
        raise Reject("json-invalid", f"{where} must be an object")
    return value


def relative_path(value: object, where: str) -> str:
    if not isinstance(value, str) or not value or "\\" in value or "\x00" in value:
        raise Reject("path-invalid", where)
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in ("", ".", "..") for part in path.parts) or str(path) != value:
        raise Reject("path-invalid", f"{where}: {value!r}")
    return value


def git(root: Path, *args: str, input_bytes: bytes | None = None) -> bytes:
    result = subprocess.run(["git", *args], cwd=root, input=input_bytes, capture_output=True,
                            check=False, timeout=30)
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", errors="replace").strip()[:240]
        raise Reject("git-object-unavailable", detail or "git command failed")
    return result.stdout


def check_commit(root: Path, revision: object, token: str) -> str:
    if not isinstance(revision, str) or not HEX40.fullmatch(revision):
        raise Reject(token, "expected one full lowercase commit id")
    git(root, "cat-file", "-e", f"{revision}^{{commit}}")
    return revision


def blob(root: Path, revision: str, path: str) -> bytes:
    path = relative_path(path, "Git blob path")
    result = subprocess.run(["git", "show", f"{revision}:{path}"], cwd=root,
                            capture_output=True, check=False, timeout=30)
    if result.returncode != 0:
        raise Reject("git-blob-missing", path)
    if len(result.stdout) > MAX_FILE_BYTES:
        raise Reject("file-size-limit", path)
    return result.stdout


def read_regular(root: Path, path: str) -> bytes:
    relative_path(path, "file path")
    target = root.joinpath(*PurePosixPath(path).parts)
    current = root
    for part in PurePosixPath(path).parts:
        current = current / part
        try:
            if current.is_symlink():
                raise Reject("path-link", path)
        except OSError:
            raise Reject("file-unavailable", path) from None
    try:
        if not target.is_file():
            raise Reject("file-unavailable", path)
        size = target.stat().st_size
        if size > MAX_FILE_BYTES:
            raise Reject("file-size-limit", path)
        return target.read_bytes()
    except OSError as error:
        raise Reject("file-unavailable", f"{path}: {error.strerror}") from None


def require_keys(value: dict, required: set[str], where: str, optional: set[str] | None = None) -> None:
    optional = optional or set()
    missing = sorted(required - set(value))
    extra = sorted(set(value) - required - optional)
    if missing:
        raise Reject("record-field-missing", f"{where}: {','.join(missing)}")
    if extra:
        raise Reject("record-field-unknown", f"{where}: {','.join(extra)}")


def nonempty(value: object, where: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise Reject("record-field-invalid", where)
    return value.strip()


def file_records(value: object, where: str) -> dict[str, tuple[int, str]]:
    if not isinstance(value, list) or not value or len(value) > MAX_FILES:
        raise Reject("record-files-invalid", where)
    result: dict[str, tuple[int, str]] = {}
    for index, item in enumerate(value):
        label = f"{where}[{index}]"
        if not isinstance(item, dict):
            raise Reject("record-files-invalid", label)
        require_keys(item, {"path", "size_bytes", "sha256"}, label)
        path = relative_path(item["path"], label)
        size, digest = item["size_bytes"], item["sha256"]
        if not isinstance(size, int) or isinstance(size, bool) or size < 0 or size > MAX_FILE_BYTES:
            raise Reject("record-files-invalid", f"{label}.size_bytes")
        if not isinstance(digest, str) or not HEX64.fullmatch(digest):
            raise Reject("record-files-invalid", f"{label}.sha256")
        if path in result:
            raise Reject("record-files-duplicate", path)
        result[path] = (size, digest)
    return result


def _require_file_bytes(root: Path, revision: str, path: str, size: int, digest: str,
                        current: bool = True) -> bytes:
    pinned = blob(root, revision, path)
    if len(pinned) != size or sha256(pinned) != digest:
        raise Reject("record-identity-mismatch", path)
    if current:
        actual = read_regular(root, path)
        if actual != pinned:
            raise Reject("admission-pin-mismatch", path)
    return pinned


def tree_files(root: Path, revision: str, prefix: str) -> set[str]:
    raw = git(root, "ls-tree", "-r", "-z", revision, "--", prefix)
    result: set[str] = set()
    for record in raw.split(b"\0"):
        if not record:
            continue
        try:
            metadata, path_raw = record.split(b"\t", 1)
            mode, kind, _oid = metadata.decode("ascii").split(" ", 2)
            path = path_raw.decode("utf-8", errors="strict")
        except (ValueError, UnicodeDecodeError):
            raise Reject("git-tree-invalid", prefix) from None
        if kind != "blob" or mode not in ("100644", "100755"):
            raise Reject("fixture-link-or-special-file", path)
        result.add(path)
    return result


def check_manifest(root: Path, manifest_path: str) -> dict:
    """Check one candidate manifest. The admission commit is independent of mutable record fields."""
    manifest_path = relative_path(manifest_path, "manifest path")
    if not manifest_path.startswith("fixtures/") or not manifest_path.endswith("/manifest.json"):
        raise Reject("manifest-path-invalid", manifest_path)
    fixture_dir = manifest_path.rsplit("/", 1)[0]
    manifest_raw = read_regular(root, manifest_path)
    manifest = parse_json(manifest_raw, manifest_path)
    require_keys(manifest, {"schema_version", "fixture_kind", "decision", "permissions", "source",
                            "inputs", "files", "build", "components", "notices"}, "manifest")
    if manifest["schema_version"] != 1 or isinstance(manifest["schema_version"], bool):
        raise Reject("record-schema-unsupported", "schema_version must be 1")
    nonempty(manifest["fixture_kind"], "fixture_kind")

    decision = manifest["decision"]
    if not isinstance(decision, dict):
        raise Reject("record-decision-invalid", "decision must be an object")
    require_keys(decision, {"status", "reviewer_role", "rationale"}, "decision")
    if decision["status"] != "approved":
        raise Reject("fixture-no-go", "only a reviewed approved record can be admitted")
    nonempty(decision["reviewer_role"], "decision.reviewer_role")
    nonempty(decision["rationale"], "decision.rationale")

    permissions = manifest["permissions"]
    if not isinstance(permissions, dict):
        raise Reject("record-permissions-invalid", "permissions must be an object")
    require_keys(permissions, {"repository", "public_ci"}, "permissions")
    if permissions != {"repository": True, "public_ci": True}:
        raise Reject("permission-scope-incomplete", "repository and public_ci must both be true")

    source = manifest["source"]
    if not isinstance(source, dict):
        raise Reject("record-source-invalid", "source must be an object")
    require_keys(source, {"repository", "revision"}, "source")
    nonempty(source["repository"], "source.repository")
    if not isinstance(source["revision"], str) or not HEX40.fullmatch(source["revision"]):
        raise Reject("source-revision-invalid", "source.revision must be a full commit id")

    inputs = file_records(manifest["inputs"], "inputs")
    files = file_records(manifest["files"], "files")
    if set(inputs) - set(files):
        raise Reject("input-not-fixture-file", sorted(set(inputs) - set(files))[0])

    build = manifest["build"]
    if not isinstance(build, dict):
        raise Reject("build-invalid", "build must be an object")
    require_keys(build, {"recipe", "tools"}, "build")
    nonempty(build["recipe"], "build.recipe")
    tools = build["tools"]
    if not isinstance(tools, list) or not tools or len(tools) > 64:
        raise Reject("build-tools-invalid", "build.tools must be a non-empty bounded list")
    for index, tool in enumerate(tools):
        label = f"build.tools[{index}]"
        if not isinstance(tool, dict):
            raise Reject("build-tools-invalid", label)
        require_keys(tool, {"name", "version", "terms", "source_repository", "revision", "disposition"}, label)
        for key in ("name", "version", "terms", "source_repository"):
            nonempty(tool[key], f"{label}.{key}")
        if not isinstance(tool["revision"], str) or not HEX40.fullmatch(tool["revision"]):
            raise Reject("build-tool-revision-invalid", label)
        if tool["disposition"] not in ("build_only", "copied", "linked", "shipped"):
            raise Reject("build-tool-disposition-invalid", label)

    components = manifest["components"]
    if not isinstance(components, dict):
        raise Reject("component-record-invalid", "components must be an object")
    require_keys(components, set(COMPONENTS), "components")
    covered: set[str] = set()
    any_present = False
    for component_name in COMPONENTS:
        component = components[component_name]
        label = f"components.{component_name}"
        if not isinstance(component, dict):
            raise Reject("component-record-invalid", label)
        if component.get("presence") == "absent":
            require_keys(component, {"presence", "reason"}, label)
            nonempty(component["reason"], f"{label}.reason")
            continue
        require_keys(component, {"presence", "terms", "evidence", "covered_paths", "scope"}, label)
        if component["presence"] != "present":
            raise Reject("component-presence-invalid", label)
        any_present = True
        nonempty(component["terms"], f"{label}.terms")
        evidence = component["evidence"]
        if not isinstance(evidence, dict):
            raise Reject("component-evidence-invalid", label)
        require_keys(evidence, {"path", "sha256"}, f"{label}.evidence")
        evidence_path = relative_path(evidence["path"], f"{label}.evidence.path")
        if not isinstance(evidence["sha256"], str) or not HEX64.fullmatch(evidence["sha256"]):
            raise Reject("component-evidence-invalid", f"{label}.evidence.sha256")
        if evidence_path not in files or files[evidence_path][1] != evidence["sha256"]:
            raise Reject("component-evidence-not-pinned", evidence_path)
        paths = component["covered_paths"]
        if not isinstance(paths, list) or not paths:
            raise Reject("component-scope-incomplete", label)
        for path in paths:
            path = relative_path(path, f"{label}.covered_paths")
            if path not in files:
                raise Reject("component-scope-incomplete", f"{label}: {path}")
            covered.add(path)
        scope = component["scope"]
        if not isinstance(scope, dict):
            raise Reject("component-scope-incomplete", label)
        require_keys(scope, {"repository", "public_ci"}, f"{label}.scope")
        if scope != {"repository": True, "public_ci": True}:
            raise Reject("component-scope-incomplete", label)
    if not any_present:
        raise Reject("component-record-invalid", "at least one component must be present")
    if set(files) != covered:
        raise Reject("component-scope-incomplete", "every fixture file must be covered exactly by a present component")

    notices = manifest["notices"]
    if not isinstance(notices, dict):
        raise Reject("notice-record-invalid", "notices must be an object")
    require_keys(notices, {"local_path", "sha256", "index_path"}, "notices")
    local_notice = relative_path(notices["local_path"], "notices.local_path")
    index_path = relative_path(notices["index_path"], "notices.index_path")
    if local_notice not in files or not isinstance(notices["sha256"], str) \
            or not HEX64.fullmatch(notices["sha256"]) or files[local_notice][1] != notices["sha256"]:
        raise Reject("notice-record-invalid", "local notice identity differs from files")
    if local_notice.rsplit("/", 1)[0] != fixture_dir:
        raise Reject("notice-record-invalid", "local notice must be in the fixture directory")
    notice_component = components["notices"]
    if notice_component.get("presence") != "present" or local_notice not in notice_component.get("covered_paths", []):
        raise Reject("notice-record-invalid", "the notices component must cover the local notice")

    pin_path = f"{fixture_dir}/admission.commit"
    pin_raw = read_regular(root, pin_path)
    try:
        pin_text = pin_raw.decode("ascii")
    except UnicodeDecodeError:
        raise Reject("admission-pin-invalid", pin_path) from None
    if not re.fullmatch(r"[0-9a-f]{40}\n?", pin_text):
        raise Reject("admission-pin-invalid", "must contain exactly one full commit id")
    pin_text = pin_text.rstrip("\n")
    pin = check_commit(root, pin_text, "admission-pin-invalid")
    current_head = git(root, "rev-parse", "--verify", "HEAD^{commit}").decode("ascii").strip()
    ancestry = subprocess.run(["git", "merge-base", "--is-ancestor", pin, current_head], cwd=root,
                              capture_output=True, check=False, timeout=30)
    if ancestry.returncode != 0:
        raise Reject("admission-pin-not-in-history", pin)

    pinned_manifest = blob(root, pin, manifest_path)
    if pinned_manifest != manifest_raw:
        raise Reject("admission-pin-mismatch", manifest_path)
    expected_files = {manifest_path, *files}
    pinned_files = tree_files(root, pin, fixture_dir)
    if pinned_files != expected_files:
        extra = sorted(pinned_files ^ expected_files)
        raise Reject("fixture-file-inventory-mismatch", extra[0] if extra else fixture_dir)
    current_files: set[str] = set()
    for path in root.joinpath(*PurePosixPath(fixture_dir).parts).rglob("*"):
        if path.is_symlink():
            raise Reject("path-link", path.relative_to(root).as_posix())
        if path.is_file():
            current_files.add(path.relative_to(root).as_posix())
    if current_files != expected_files | {pin_path}:
        extra = sorted(current_files ^ (expected_files | {pin_path}))
        raise Reject("fixture-file-inventory-mismatch", extra[0] if extra else fixture_dir)
    for path, (size, digest) in files.items():
        if not path.startswith(fixture_dir + "/") or path in (manifest_path, pin_path):
            raise Reject("record-files-invalid", f"files must stay inside {fixture_dir}: {path}")
        _require_file_bytes(root, pin, path, size, digest)
    for path, (size, digest) in inputs.items():
        if not path.startswith(fixture_dir + "/") or path not in files:
            raise Reject("input-not-fixture-file", path)
        pinned = blob(root, pin, path)
        if len(pinned) != size or sha256(pinned) != digest:
            raise Reject("input-identity-mismatch", path)
    current_notice_index = read_regular(root, index_path)
    notice_index = blob(root, pin, index_path)
    if current_notice_index != notice_index:
        raise Reject("admission-pin-mismatch", index_path)
    manifest_digest = sha256(manifest_raw).encode("ascii")
    license_digest = notices["sha256"].encode("ascii")
    if manifest_digest not in notice_index or license_digest not in notice_index or local_notice.encode() not in notice_index:
        raise Reject("notice-index-mismatch", index_path)
    return {"fixture": fixture_dir, "pin": pin, "files": len(files)}


def _write_synthetic(root: Path) -> str:
    """Create one complete synthetic fixture and commit the reviewed source bytes."""
    git(root, "init", "-q")
    git(root, "config", "user.name", "GabbaBoy Fixture Test")
    git(root, "config", "user.email", "fixture-test@example.invalid")
    (root / "cmake").mkdir(parents=True, exist_ok=True)
    (root / "cmake/FixtureAdmissionPolicy.json").write_bytes(
        (Path(__file__).resolve().parents[2] / "cmake/FixtureAdmissionPolicy.json").read_bytes())
    (root / "fixtures/synthetic/evidence").mkdir(parents=True)
    payload = b"synthetic fixture bytes; not a game ROM\n"
    source = b"synthetic source input\n"
    license_bytes = b"Synthetic test fixture terms\n"
    grant = b"Synthetic test grant snapshot\n"
    content = {
        "fixtures/synthetic/demo.gb": payload,
        "fixtures/synthetic/demo.asm": source,
        "fixtures/synthetic/LICENSE.txt": license_bytes,
        "fixtures/synthetic/evidence/grant.txt": grant,
    }
    for path, data in content.items():
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    files = [{"path": path, "size_bytes": len(data), "sha256": sha256(data)}
             for path, data in sorted(content.items())]
    input_record = next(item for item in files if item["path"].endswith("demo.asm"))
    components = {
        "code": {"presence": "present", "terms": "MIT", "evidence": {"path": "fixtures/synthetic/evidence/grant.txt", "sha256": sha256(grant)},
                 "covered_paths": ["fixtures/synthetic/demo.gb", "fixtures/synthetic/demo.asm"],
                 "scope": {"repository": True, "public_ci": True}},
        "art": {"presence": "absent", "reason": "Synthetic fixture has no separate art component."},
        "audio_driver": {"presence": "absent", "reason": "Synthetic fixture has no audio driver."},
        "build_inputs": {"presence": "present", "terms": "MIT", "evidence": {"path": "fixtures/synthetic/evidence/grant.txt", "sha256": sha256(grant)},
                         "covered_paths": ["fixtures/synthetic/demo.asm"],
                         "scope": {"repository": True, "public_ci": True}},
        "notices": {"presence": "present", "terms": "Synthetic terms", "evidence": {"path": "fixtures/synthetic/evidence/grant.txt", "sha256": sha256(grant)},
                    "covered_paths": ["fixtures/synthetic/LICENSE.txt", "fixtures/synthetic/evidence/grant.txt"],
                    "scope": {"repository": True, "public_ci": True}},
    }
    record = {
        "schema_version": 1,
        "fixture_kind": "synthetic-game",
        "decision": {"status": "approved", "reviewer_role": "synthetic-test", "rationale": "Synthetic control only."},
        "permissions": {"repository": True, "public_ci": True},
        "source": {"repository": "https://example.invalid/fixture", "revision": BASELINE_COMMIT},
        "inputs": [input_record],
        "files": files,
        "build": {"recipe": "synthetic build", "tools": [{"name": "test-tool", "version": "1.0",
                   "terms": "MIT", "source_repository": "https://example.invalid/tool", "revision": BASELINE_COMMIT,
                   "disposition": "build_only"}]},
        "components": components,
        "notices": {"local_path": "fixtures/synthetic/LICENSE.txt", "sha256": sha256(license_bytes),
                    "index_path": "THIRD_PARTY_NOTICES.md"},
    }
    manifest_path = root / "fixtures/synthetic/manifest.json"
    manifest_path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    manifest_digest = sha256(manifest_path.read_bytes())
    (root / "THIRD_PARTY_NOTICES.md").write_text(
        f"| synthetic | fixtures/synthetic/manifest.json {manifest_digest} | "
        f"fixtures/synthetic/LICENSE.txt {sha256(license_bytes)} |\n", encoding="utf-8")
    git(root, "add", "fixtures/synthetic", "THIRD_PARTY_NOTICES.md", "cmake/FixtureAdmissionPolicy.json")
    git(root, "commit", "-qm", "fixture: synthetic reviewed baseline")
    commit = git(root, "rev-parse", "HEAD").decode("ascii").strip()
    (root / "fixtures/synthetic/admission.commit").write_text(commit + "\n", encoding="ascii")
    return commit


def _run_manifest_cli(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, "-I", str(Path(__file__).resolve()), "--check-manifest",
                           "fixtures/synthetic/manifest.json", "--repo-root", str(root)],
                          capture_output=True, text=True, check=False, timeout=30)


def self_test() -> None:
    with tempfile.TemporaryDirectory(prefix="gbb-fixture-admission-") as directory:
        root = Path(directory)
        (root / ".git/objects/info").mkdir(parents=True, exist_ok=True)
        object_dir = subprocess.run(["git", "rev-parse", "--absolute-git-dir"], cwd=Path(__file__).resolve().parents[2],
                                    capture_output=True, check=True, text=True).stdout.strip() + "/objects"
        (root / ".git/objects/info/alternates").write_text(object_dir + "\n", encoding="utf-8")
        _write_synthetic(root)
        positive = _run_manifest_cli(root)
        if positive.returncode != 0 or "PASS: fixture admission" not in positive.stdout:
            raise Reject("self-test-positive", positive.stderr.strip() or positive.stdout.strip())

        manifest_path = root / "fixtures/synthetic/manifest.json"
        record = parse_json(manifest_path.read_bytes(), "synthetic manifest")
        payload_path = root / "fixtures/synthetic/demo.gb"
        payload = b"coordinated replacement bytes\n"
        payload_path.write_bytes(payload)
        for entry in record["files"]:
            if entry["path"] == "fixtures/synthetic/demo.gb":
                entry["size_bytes"] = len(payload)
                entry["sha256"] = sha256(payload)
        manifest_path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        notice = root / "fixtures/synthetic/LICENSE.txt"
        notice_bytes = notice.read_bytes()
        manifest_hash = sha256(manifest_path.read_bytes())
        notice_row = root / "THIRD_PARTY_NOTICES.md"
        notice_row.write_text(
            f"| synthetic | fixtures/synthetic/manifest.json {manifest_hash} | "
            f"fixtures/synthetic/LICENSE.txt {sha256(notice_bytes)} |\n", encoding="utf-8")
        negative = _run_manifest_cli(root)
        if negative.returncode == 0:
            raise Reject("self-test-baseline-bypass", "coordinated fixture, manifest and notice rewrite was accepted")
        if "REJECT admission-pin-mismatch:" not in negative.stderr:
            raise Reject("self-test-negative-reason", negative.stderr.strip())
    print("PASS: fixture admission self-test positives=1 negative_controls=1")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--self-test", action="store_true")
    modes.add_argument("--check-manifest")
    modes.add_argument("--check-repository", action="store_true")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args(argv)
    try:
        root = args.repo_root.resolve(strict=True)
        policy = parse_json((root / "cmake/FixtureAdmissionPolicy.json").read_bytes(), "FixtureAdmissionPolicy.json")
        if policy.get("schema_version") != 1 or policy.get("baseline_commit") != BASELINE_COMMIT:
            raise Reject("policy-invalid", "baseline commit differs from the reviewed full identity")
        if args.self_test:
            self_test()
        elif args.check_manifest:
            result = check_manifest(root, args.check_manifest)
            print(f"PASS: fixture admission fixture={result['fixture']} pinned={result['pin']} files={result['files']}")
        else:
            raise Reject("repository-check-unimplemented", "repository mode is implemented in the next task")
        return 0
    except (Reject, OSError, subprocess.SubprocessError) as error:
        print(str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
