#!/usr/bin/env python3
"""Validate new fixture records against immutable Git identities and product byte policy."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import stat
import subprocess
import sys
import tempfile
import tarfile
from pathlib import Path, PurePosixPath


BASELINE_COMMIT = "7cc6495e64f3645caa120e7458f754585b788985"
MAX_MANIFEST_BYTES = 2 * 1024 * 1024
MAX_FILE_BYTES = 32 * 1024 * 1024
MAX_TOTAL_FIXTURE_BYTES = 256 * 1024 * 1024
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
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError, RecursionError, Reject) as error:
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
    try:
        git(root, "cat-file", "-e", f"{revision}^{{commit}}")
    except Reject:
        raise Reject(token, "commit object is unavailable") from None
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
    if sum(size for size, _digest in result.values()) > MAX_TOTAL_FIXTURE_BYTES:
        raise Reject("record-total-size-limit", where)
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


def current_fixture_files(root: Path) -> set[str]:
    fixture_root = root / "fixtures"
    if not fixture_root.is_dir() or fixture_root.is_symlink():
        raise Reject("fixture-tree-unavailable", "fixtures/ is missing or linked")
    found: set[str] = set()
    for path in fixture_root.rglob("*"):
        relative = path.relative_to(root).as_posix()
        try:
            mode = path.lstat().st_mode
        except OSError:
            raise Reject("fixture-tree-unavailable", relative) from None
        if stat.S_ISLNK(mode):
            raise Reject("path-link", relative)
        if stat.S_ISREG(mode):
            found.add(relative)
        elif not stat.S_ISDIR(mode):
            raise Reject("fixture-special-file", relative)
        if len(found) > MAX_FILES:
            raise Reject("fixture-file-count-limit", "too many files")
    return found


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
    require_keys(decision, {"status", "reviewer_role", "rationale", "component_rationale"}, "decision")
    if decision["status"] != "approved":
        raise Reject("fixture-no-go", "only a reviewed approved record can be admitted")
    nonempty(decision["reviewer_role"], "decision.reviewer_role")
    nonempty(decision["rationale"], "decision.rationale")
    component_rationale = decision["component_rationale"]
    if not isinstance(component_rationale, dict):
        raise Reject("decision-component-rationale-invalid", "must map each present component to its scope rationale")
    for name, rationale in component_rationale.items():
        if name not in COMPONENTS:
            raise Reject("decision-component-rationale-invalid", name)
        nonempty(rationale, f"decision.component_rationale.{name}")

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
    check_commit(root, source["revision"], "source-revision-unavailable")

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
        require_keys(tool, {"name", "version", "terms", "source_repository", "revision", "disposition",
                            "component", "covered_paths"}, label)
        for key in ("name", "version", "terms", "source_repository"):
            nonempty(tool[key], f"{label}.{key}")
        if not isinstance(tool["revision"], str) or not HEX40.fullmatch(tool["revision"]):
            raise Reject("build-tool-revision-invalid", label)
        check_commit(root, tool["revision"], "build-tool-revision-unavailable")
        if tool["disposition"] not in ("build_only", "copied", "linked", "shipped"):
            raise Reject("build-tool-disposition-invalid", label)
        if tool["disposition"] == "build_only":
            if tool["component"] is not None or tool["covered_paths"] != []:
                raise Reject("build-tool-coverage-invalid", label)
        else:
            component_name = tool["component"]
            paths = tool["covered_paths"]
            if component_name not in COMPONENTS or not isinstance(paths, list) or not paths:
                raise Reject("build-tool-coverage-invalid", label)
            for path in paths:
                path = relative_path(path, f"{label}.covered_paths")
                if path not in files:
                    raise Reject("build-tool-coverage-invalid", f"{label}: {path}")

    components = manifest["components"]
    if not isinstance(components, dict):
        raise Reject("component-record-invalid", "components must be an object")
    require_keys(components, set(COMPONENTS), "components")
    covered: set[str] = set()
    component_paths: dict[str, set[str]] = {}
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
        component_paths[component_name] = set(paths)
        scope = component["scope"]
        if not isinstance(scope, dict):
            raise Reject("component-scope-incomplete", label)
        require_keys(scope, {"repository", "public_ci"}, f"{label}.scope")
        if scope != {"repository": True, "public_ci": True}:
            raise Reject("component-scope-incomplete", label)
    if set(component_rationale) != {
            name for name, component in components.items()
            if isinstance(component, dict) and component.get("presence") == "present"}:
        raise Reject("decision-component-rationale-invalid", "each present component needs one scope rationale")
    if not any_present:
        raise Reject("component-record-invalid", "at least one component must be present")
    if set(files) != covered:
        raise Reject("component-scope-incomplete", "every fixture file must be covered exactly by a present component")
    for tool in tools:
        if tool["disposition"] != "build_only" and any(
                path not in component_paths.get(tool["component"], set()) for path in tool["covered_paths"]):
            raise Reject("build-tool-coverage-invalid", f"tool {tool['name']} paths are not covered by its component")

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
    if not (root / pin_path).is_file():
        raise Reject("admission-pin-missing", pin_path)
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
    manifest_digest = sha256(manifest_raw)
    license_digest = notices["sha256"]
    matching_rows = [line for line in notice_index.decode("utf-8", errors="strict").splitlines()
                     if manifest_path.encode("utf-8") in line.encode("utf-8")
                     and manifest_digest.encode("ascii") in line.encode("utf-8")
                     and local_notice.encode("utf-8") in line.encode("utf-8")
                     and license_digest.encode("ascii") in line.encode("utf-8")]
    if len(matching_rows) != 1:
        raise Reject("notice-index-mismatch", index_path)
    return {"fixture": fixture_dir, "pin": pin, "files": len(files)}


def check_repository(root: Path, baseline: str) -> dict:
    baseline = check_commit(root, baseline, "baseline-object-unavailable")
    baseline_files = tree_files(root, baseline, "fixtures")
    current_files = current_fixture_files(root)
    all_ids = {path.split("/", 2)[1] for path in baseline_files | current_files if path.startswith("fixtures/")}
    changed = 0
    for fixture_id in sorted(all_ids):
        prefix = f"fixtures/{fixture_id}/"
        old = {path for path in baseline_files if path.startswith(prefix)}
        new = {path for path in current_files if path.startswith(prefix)}
        identical = old == new
        if identical:
            for path in sorted(old):
                if read_regular(root, path) != blob(root, baseline, path):
                    identical = False
                    break
        if identical:
            continue
        manifest_path = prefix + "manifest.json"
        if manifest_path not in new:
            raise Reject("fixture-admission-required", f"changed fixture {fixture_id} has no manifest")
        changed += 1
        check_manifest(root, manifest_path)

    baseline_license = blob(root, baseline, "LICENSE")
    if read_regular(root, "LICENSE") != baseline_license:
        raise Reject("root-license-mismatch", "LICENSE differs from the immutable project baseline")
    if not baseline_files:
        raise Reject("baseline-fixtures-empty", "the fixed baseline contains no fixture files")
    return {"legacy_files": len(baseline_files), "admitted_changes": changed, "baseline": baseline}


def _write_synthetic(root: Path) -> str:
    """Create one complete synthetic fixture and commit the reviewed source bytes."""
    git(root, "init", "-q")
    git(root, "symbolic-ref", "HEAD", "refs/heads/main")
    git(root, "update-ref", "refs/heads/main", BASELINE_COMMIT)
    git(root, "read-tree", "--empty")
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
        "decision": {"status": "approved", "reviewer_role": "synthetic-test", "rationale": "Synthetic control only.",
                     "component_rationale": {"code": "Synthetic code scope only.",
                                             "build_inputs": "Synthetic input scope only.",
                                             "notices": "Synthetic notice scope only."}},
        "permissions": {"repository": True, "public_ci": True},
        "source": {"repository": "https://example.invalid/fixture", "revision": BASELINE_COMMIT},
        "inputs": [input_record],
        "files": files,
        "build": {"recipe": "synthetic build", "tools": [{"name": "test-tool", "version": "1.0",
                   "terms": "MIT", "source_repository": "https://example.invalid/tool", "revision": BASELINE_COMMIT,
                   "disposition": "build_only", "component": None, "covered_paths": []}]},
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


def _prepare_synthetic(root: Path) -> None:
    (root / ".git/objects/info").mkdir(parents=True, exist_ok=True)
    object_dir = subprocess.run(["git", "rev-parse", "--absolute-git-dir"], cwd=Path(__file__).resolve().parents[2],
                                capture_output=True, check=True, text=True).stdout.strip() + "/objects"
    (root / ".git/objects/info/alternates").write_text(object_dir + "\n", encoding="utf-8")
    _write_synthetic(root)


def _prepare_legacy_tree(root: Path) -> None:
    """Materialize only the immutable baseline fixture tree for repository-gate controls."""
    project = Path(__file__).resolve().parents[2]
    git(root, "init", "-q")
    (root / ".git/objects/info").mkdir(parents=True, exist_ok=True)
    object_dir = subprocess.run(["git", "rev-parse", "--absolute-git-dir"], cwd=project,
                                capture_output=True, check=True, text=True).stdout.strip() + "/objects"
    (root / ".git/objects/info/alternates").write_text(object_dir + "\n", encoding="utf-8")
    archive = subprocess.run(["git", "archive", "--format=tar", BASELINE_COMMIT, "fixtures", "LICENSE"],
                             cwd=project, capture_output=True, check=True, timeout=30).stdout
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:") as stream:
        for member in stream.getmembers():
            if member.isdir():
                continue
            path = relative_path(member.name, "baseline archive path")
            if member.issym() or member.islnk() or not member.isfile():
                raise Reject("self-test-baseline-archive-invalid", path)
            if path != "LICENSE" and not path.startswith("fixtures/"):
                raise Reject("self-test-baseline-archive-invalid", path)
            if member.size > MAX_FILE_BYTES:
                raise Reject("self-test-baseline-archive-invalid", path)
            source = stream.extractfile(member)
            if source is None:
                raise Reject("self-test-baseline-archive-invalid", path)
            target = root.joinpath(*PurePosixPath(path).parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(source.read(MAX_FILE_BYTES + 1))
    policy_path = root / "cmake/FixtureAdmissionPolicy.json"
    policy_path.parent.mkdir(parents=True, exist_ok=True)
    policy_path.write_bytes((project / "cmake/FixtureAdmissionPolicy.json").read_bytes())


def _run_repository_cli(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, "-I", str(Path(__file__).resolve()), "--check-repository",
                           "--repo-root", str(root)], capture_output=True, text=True,
                          check=False, timeout=30)


def _run_manifest_mutations(root: Path) -> int:
    path = root / "fixtures/synthetic/manifest.json"
    original = path.read_bytes()
    record = parse_json(original, "synthetic manifest")
    cases = []

    def changed(label: str, mutate, expected: str) -> None:
        candidate = json.loads(json.dumps(record))
        mutate(candidate)
        path.write_text(json.dumps(candidate, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        result = _run_manifest_cli(root)
        if result.returncode == 0 or expected not in result.stderr:
            raise Reject(f"self-test-{label}", result.stderr.strip() or f"{label} mutation was accepted")
        cases.append(label)
        path.write_bytes(original)

    changed("missing-schema-version", lambda value: value.pop("schema_version"), "REJECT record-field-missing:")
    changed("missing-fixture-kind", lambda value: value.pop("fixture_kind"), "REJECT record-field-missing:")
    changed("missing-permissions", lambda value: value.pop("permissions"), "REJECT record-field-missing:")
    changed("missing-source", lambda value: value.pop("source"), "REJECT record-field-missing:")
    changed("missing-inputs", lambda value: value.pop("inputs"), "REJECT record-field-missing:")
    changed("missing-files", lambda value: value.pop("files"), "REJECT record-field-missing:")
    changed("missing-build", lambda value: value.pop("build"), "REJECT record-field-missing:")
    changed("missing-components", lambda value: value.pop("components"), "REJECT record-field-missing:")
    changed("missing-notices", lambda value: value.pop("notices"), "REJECT record-field-missing:")
    changed("unknown-manifest-field", lambda value: value.update(extra="unexpected"), "REJECT record-field-unknown:")
    changed("unsupported-schema", lambda value: value.update(schema_version=2), "REJECT record-schema-unsupported:")
    changed("no-go-decision", lambda value: value["decision"].update(status="no-go"), "REJECT fixture-no-go:")
    changed("component-rationale-omitted", lambda value: value["decision"]["component_rationale"].pop("code"),
            "REJECT decision-component-rationale-invalid:")
    changed("repository-only-permission", lambda value: value["permissions"].update(public_ci=False),
            "REJECT permission-scope-incomplete:")
    changed("source-revision-malformed", lambda value: value["source"].update(revision="main"),
            "REJECT source-revision-invalid:")
    changed("source-revision-missing-object", lambda value: value["source"].update(revision="0" * 40),
            "REJECT source-revision-unavailable:")
    changed("input-not-in-files", lambda value: value["inputs"][0].update(path="fixtures/synthetic/missing.asm"),
            "REJECT input-not-fixture-file:")
    changed("duplicate-file", lambda value: value["files"].append(dict(value["files"][0])),
            "REJECT record-files-duplicate:")
    changed("unsafe-file-path", lambda value: value["files"][0].update(path="../outside.gb"), "REJECT path-invalid:")
    changed("empty-build-recipe", lambda value: value["build"].update(recipe=" "), "REJECT record-field-invalid:")
    changed("unknown-tool-disposition", lambda value: value["build"]["tools"][0].update(disposition="bundled"),
            "REJECT build-tool-disposition-invalid:")
    changed("copied-tool-without-coverage", lambda value: value["build"]["tools"][0].update(
        disposition="copied", component="code", covered_paths=[]), "REJECT build-tool-coverage-invalid:")
    changed("missing-component", lambda value: value["components"].pop("art"), "REJECT record-field-missing:")
    changed("empty-absence-reason", lambda value: value["components"]["art"].update(reason=" "),
            "REJECT record-field-invalid:")
    changed("repository-only-component", lambda value: value["components"]["code"]["scope"].update(public_ci=False),
            "REJECT component-scope-incomplete:")
    changed("unbound-evidence", lambda value: value["components"]["code"]["evidence"].update(path="fixtures/synthetic/missing.txt"),
            "REJECT component-evidence-not-pinned:")
    changed("audio-driver-without-grant", lambda value: value["components"].update(audio_driver={"presence": "present"}),
            "REJECT record-field-missing:")
    changed("notice-digest-mismatch", lambda value: value["notices"].update(sha256="0" * 64),
            "REJECT notice-record-invalid:")

    path.write_bytes(original.replace(b'{\n', b'{\n  "schema_version": 1,\n', 1))
    result = _run_manifest_cli(root)
    if result.returncode == 0 or "REJECT json-duplicate-key:" not in result.stderr:
        raise Reject("self-test-duplicate-json", result.stderr.strip() or "duplicate JSON key was accepted")
    cases.append("duplicate-json-key")
    path.write_bytes(b"{not JSON\n")
    result = _run_manifest_cli(root)
    if result.returncode == 0 or "REJECT json-invalid:" not in result.stderr:
        raise Reject("self-test-malformed-json", result.stderr.strip() or "malformed JSON was accepted")
    cases.append("malformed-json")
    path.write_bytes(original.replace(b'"approved"', b'NaN', 1))
    result = _run_manifest_cli(root)
    if result.returncode == 0 or "REJECT json-non-finite:" not in result.stderr:
        raise Reject("self-test-non-finite-json", result.stderr.strip() or "non-finite JSON was accepted")
    cases.append("non-finite-json")
    path.write_bytes(original)

    pin_path = root / "fixtures/synthetic/admission.commit"
    pin_path.write_text("refs/heads/main\n", encoding="ascii")
    result = _run_manifest_cli(root)
    if result.returncode == 0 or "REJECT admission-pin-invalid:" not in result.stderr:
        raise Reject("self-test-symbolic-pin", result.stderr.strip() or "symbolic pin was accepted")
    cases.append("symbolic-pin")
    pin_path.write_text(BASELINE_COMMIT + "\n", encoding="ascii")
    result = _run_manifest_cli(root)
    if result.returncode == 0 or "REJECT git-blob-missing:" not in result.stderr:
        raise Reject("self-test-missing-blob", result.stderr.strip() or "missing pinned blob was accepted")
    cases.append("missing-pinned-blob")
    pin_path.write_text(git(root, "rev-parse", "HEAD").decode("ascii").strip() + "\n", encoding="ascii")
    return len(cases)


def _run_live_byte_mutations(root: Path) -> int:
    controls = 0
    paths = (
        "fixtures/synthetic/demo.asm",
        "fixtures/synthetic/LICENSE.txt",
        "THIRD_PARTY_NOTICES.md",
    )
    for path in paths:
        target = root / path
        original = target.read_bytes()
        target.write_bytes(original + b"changed after admission\n")
        result = _run_manifest_cli(root)
        if result.returncode == 0 or "REJECT admission-pin-mismatch:" not in result.stderr:
            raise Reject("self-test-live-byte-mismatch", result.stderr.strip() or f"changed bytes accepted: {path}")
        target.write_bytes(original)
        controls += 1

    fixture_file = root / "fixtures/synthetic/demo.gb"
    saved_file = root / "fixtures/synthetic/demo.gb.saved"
    fixture_file.rename(saved_file)
    try:
        fixture_file.symlink_to(saved_file.name)
    except OSError:
        saved_file.rename(fixture_file)
    else:
        result = _run_manifest_cli(root)
        fixture_file.unlink()
        saved_file.rename(fixture_file)
        if result.returncode == 0 or "REJECT path-link:" not in result.stderr:
            raise Reject("self-test-link-escape", result.stderr.strip() or "fixture symlink was accepted")
        controls += 1
    return controls


def _run_repository_controls() -> int:
    with tempfile.TemporaryDirectory(prefix="gbb-fixture-admission-legacy-") as directory:
        root = Path(directory)
        _prepare_legacy_tree(root)
        positive = _run_repository_cli(root)
        if positive.returncode != 0 or "PASS: fixture admission repository" not in positive.stdout:
            raise Reject("self-test-repository-positive", positive.stderr.strip() or positive.stdout.strip())

        new_fixture = root / "fixtures/new-unadmitted-fixture/payload.bin"
        new_fixture.parent.mkdir(parents=True)
        new_fixture.write_bytes(b"unadmitted synthetic payload\n")
        result = _run_repository_cli(root)
        if result.returncode == 0 or "REJECT fixture-admission-required:" not in result.stderr:
            raise Reject("self-test-new-fixture", result.stderr.strip() or "new fixture without a record was accepted")
        new_fixture.unlink()
        new_fixture.parent.rmdir()

        added_payload = root / "fixtures/tracer/new-payload.bin"
        added_payload.write_bytes(b"unadmitted payload inside a legacy fixture\n")
        result = _run_repository_cli(root)
        if result.returncode == 0 or "REJECT record-field-missing:" not in result.stderr:
            raise Reject("self-test-legacy-addition", result.stderr.strip() or "new legacy-subtree payload was accepted")
        added_payload.unlink()

        existing_payload = "fixtures/tracer/tracer.gb"
        original_payload = blob(root, BASELINE_COMMIT, existing_payload)
        (root / existing_payload).write_bytes(b"changed legacy payload\n")
        result = _run_repository_cli(root)
        if result.returncode == 0 or "REJECT record-field-missing:" not in result.stderr:
            raise Reject("self-test-legacy-replacement", result.stderr.strip() or "replaced legacy payload was accepted")
        (root / existing_payload).write_bytes(original_payload)

        license_path = root / "LICENSE"
        original_license = license_path.read_bytes()
        license_path.write_bytes(original_license + b"changed\n")
        result = _run_repository_cli(root)
        if result.returncode == 0 or "REJECT root-license-mismatch:" not in result.stderr:
            raise Reject("self-test-root-license", result.stderr.strip() or "modified root LICENSE was accepted")
        return 4


def self_test() -> None:
    with tempfile.TemporaryDirectory(prefix="gbb-fixture-admission-positive-") as directory:
        root = Path(directory)
        _prepare_synthetic(root)
        positive = _run_manifest_cli(root)
        if positive.returncode != 0 or "PASS: fixture admission" not in positive.stdout:
            raise Reject("self-test-positive", positive.stderr.strip() or positive.stdout.strip())
        manifest_controls = _run_manifest_mutations(root) + _run_live_byte_mutations(root)

    def reject_case(label: str, mutate, expected: str) -> None:
        with tempfile.TemporaryDirectory(prefix=f"gbb-fixture-admission-{label}-") as directory:
            case_root = Path(directory)
            _prepare_synthetic(case_root)
            mutate(case_root)
            result = _run_manifest_cli(case_root)
            if result.returncode == 0:
                raise Reject(f"self-test-{label}-bypass", f"{label} mutation was accepted")
            if expected not in result.stderr:
                raise Reject(f"self-test-{label}-reason", result.stderr.strip())

    def coordinated_rewrite(case_root: Path) -> None:
        manifest_path = case_root / "fixtures/synthetic/manifest.json"
        record = parse_json(manifest_path.read_bytes(), "synthetic manifest")
        payload = b"coordinated replacement bytes\n"
        (case_root / "fixtures/synthetic/demo.gb").write_bytes(payload)
        for entry in record["files"]:
            if entry["path"] == "fixtures/synthetic/demo.gb":
                entry["size_bytes"] = len(payload)
                entry["sha256"] = sha256(payload)
        manifest_path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        notice = case_root / "fixtures/synthetic/LICENSE.txt"
        (case_root / "THIRD_PARTY_NOTICES.md").write_text(
            f"| synthetic | fixtures/synthetic/manifest.json {sha256(manifest_path.read_bytes())} | "
            f"fixtures/synthetic/LICENSE.txt {sha256(notice.read_bytes())} |\n", encoding="utf-8")

    def missing_component(case_root: Path) -> None:
        path = case_root / "fixtures/synthetic/manifest.json"
        record = parse_json(path.read_bytes(), "synthetic manifest")
        del record["components"]["art"]
        path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def missing_pin(case_root: Path) -> None:
        (case_root / "fixtures/synthetic/admission.commit").unlink()

    def missing_pin_object(case_root: Path) -> None:
        (case_root / "fixtures/synthetic/admission.commit").write_text("0" * 40 + "\n", encoding="ascii")

    cases = (
        ("coordinated-rewrite", coordinated_rewrite, "REJECT admission-pin-mismatch:"),
        ("missing-component", missing_component, "REJECT record-field-missing:"),
        ("missing-pin", missing_pin, "REJECT admission-pin-missing:"),
        ("missing-object", missing_pin_object, "REJECT admission-pin-invalid:"),
    )
    for label, mutate, expected in cases:
        reject_case(label, mutate, expected)
    repository_controls = _run_repository_controls()
    print(f"PASS: fixture admission self-test positives=2 negative_controls="
          f"{manifest_controls + len(cases) + repository_controls}")


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
            baseline = policy.get("baseline_commit")
            if not isinstance(baseline, str) or baseline != BASELINE_COMMIT:
                raise Reject("policy-invalid", "baseline_commit must be the reviewed full commit id")
            result = check_repository(root, baseline)
            print(f"PASS: fixture admission repository legacy_files={result['legacy_files']} "
                  f"admitted_changes={result['admitted_changes']} baseline={result['baseline']}")
        return 0
    except (Reject, OSError, subprocess.SubprocessError) as error:
        print(str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
