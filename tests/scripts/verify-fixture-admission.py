#!/usr/bin/env python3
"""Validate new fixture records against immutable Git identities and product byte policy."""

from __future__ import annotations

import argparse
import copy
import hashlib
import io
import json
import os
import queue
import re
import stat
import subprocess
import sys
import tempfile
import tarfile
import shutil
import threading
import time
from collections.abc import Iterable, Mapping
from pathlib import Path, PurePosixPath


BASELINE_COMMIT = "7cc6495e64f3645caa120e7458f754585b788985"
# Independent trust anchor for the complete product policy bytes. Updating the
# JSON requires a reviewed digest change here; candidate policy cannot authorize itself.
PRODUCT_POLICY_SHA256 = "4c54582f1c1145474f3da620c086bdfc4457bcbff1831b0398fa1ff7247a2b6f"
NOTICE_BASELINE_PRODUCT_CLAIM = (
    b"The installed and downloaded product packages\n"
    b"remain fixture-free: they carry only the original project-authored tracer,\n"
    b"visible demo and MBC1 continuation fixtures."
)
NOTICE_APPROVED_PRODUCT_CLAIM = (
    b"Installed core packages carry exactly the\n"
    b"original project-authored tracer, visible demo, and MBC1 continuation fixtures\n"
    b"with their pinned notices. The optional player carries only its listed demo and\n"
    b"continuation fixtures with their notices. Controlled game and diagnostic bytes\n"
    b"remain repository-test inputs and are excluded from binary products. Automated\n"
    b"package checks compare recorded byte identities; they do not decide whether a\n"
    b"grant's author had authority."
)
MAX_MANIFEST_BYTES = 2 * 1024 * 1024
MAX_FILE_BYTES = 32 * 1024 * 1024
MAX_TOTAL_FIXTURE_BYTES = 256 * 1024 * 1024
MAX_FILES = 4096
MAX_FIXTURE_ENTRIES = 16384
MAX_GIT_TREE_RECORDS = 16384
MAX_GIT_TREE_OUTPUT_BYTES = 32 * 1024 * 1024
MAX_GIT_TREE_STDERR_BYTES = 4096
GIT_TREE_READ_CHUNK_BYTES = 64 * 1024
GIT_TREE_TIMEOUT_SECONDS = 30
GIT_BLOB_READ_CHUNK_BYTES = 64 * 1024
GIT_BLOB_TIMEOUT_SECONDS = 30
MAX_PRODUCT_FILE_BYTES = 512 * 1024 * 1024
MAX_PRODUCT_TOTAL_BYTES = 1024 * 1024 * 1024
MAX_PRODUCT_ENTRIES = 16384
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


def _terminate_and_reap(process, label: str) -> None:
    try:
        if process.poll() is None:
            process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            if process.poll() is None:
                process.kill()
            process.wait()
    except OSError as error:
        raise Reject("git-child-cleanup-failed", f"{label}: {error}") from None


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
    try:
        process = subprocess.Popen(["git", "show", f"{revision}:{path}"], cwd=root,
                                   stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=0)
    except OSError as error:
        raise Reject("git-object-unavailable", str(error)[:240]) from None
    stream = process.stdout
    data = bytearray()
    failures: queue.Queue[Reject] = queue.Queue(maxsize=1)

    def record_failure(error: Reject) -> None:
        try:
            failures.put_nowait(error)
        except queue.Full:
            pass

    def read_stdout() -> None:
        try:
            while len(data) <= MAX_FILE_BYTES:
                chunk = stream.read(min(GIT_BLOB_READ_CHUNK_BYTES, MAX_FILE_BYTES + 1 - len(data)))
                if not chunk:
                    break
                data.extend(chunk)
            if len(data) > MAX_FILE_BYTES:
                record_failure(Reject("file-size-limit", path))
        except OSError as error:
            record_failure(Reject("git-blob-unavailable", f"{path}: {error.strerror}"))
        except BaseException as error:
            record_failure(Reject("git-blob-read-failed", f"{path}: {type(error).__name__}"))
        finally:
            try:
                stream.close()
            except OSError as error:
                record_failure(Reject("git-blob-read-failed", f"{path}: {str(error)[:240]}"))

    reader = threading.Thread(target=read_stdout, name="fixture-git-blob-stdout", daemon=True)
    waited = False
    try:
        if stream is None:
            raise Reject("git-blob-reader-unavailable", path)
        reader.start()
        deadline = time.monotonic() + GIT_BLOB_TIMEOUT_SECONDS
        returncode = None
        failure = None
        while True:
            try:
                failure = failures.get_nowait()
                break
            except queue.Empty:
                pass
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                failure = Reject("git-blob-timeout", path)
                break
            try:
                returncode = process.wait(timeout=min(0.05, remaining))
                waited = True
                break
            except subprocess.TimeoutExpired:
                continue
            except OSError as error:
                failure = Reject("git-blob-read-failed", f"{path}: {error}")
                break

        if failure is None:
            reader.join(max(0, deadline - time.monotonic()))
            if reader.is_alive():
                failure = Reject("git-blob-timeout", path)
            else:
                try:
                    failure = failures.get_nowait()
                except queue.Empty:
                    pass
        if failure is not None:
            raise failure
        if returncode != 0:
            raise Reject("git-blob-missing", path)
        return bytes(data)
    finally:
        if not waited:
            _terminate_and_reap(process, "git show")
        if stream is not None and not stream.closed:
            stream.close()
        if reader.ident is not None:
            reader.join()


def _strip_html_comments(line: str, in_comment: bool) -> tuple[str, bool]:
    visible: list[str] = []
    offset = 0
    while offset < len(line):
        if in_comment:
            close = line.find("-->", offset)
            if close < 0:
                return "".join(visible), True
            offset = close + 3
            in_comment = False
            continue
        start = line.find("<!--", offset)
        if start < 0:
            visible.append(line[offset:])
            break
        visible.append(line[offset:start])
        offset = start + 4
        in_comment = True
    return "".join(visible), in_comment


def _active_notice_lines(lines: list[str]):
    """Yield Markdown lines outside fenced code blocks and HTML comments."""
    fence_char: str | None = None
    fence_length = 0
    in_comment = False
    for line in lines:
        if fence_char is not None:
            close = re.match(r"^ {0,3}(`+|~+)[ \t]*$", line)
            if close and close.group(1)[0] == fence_char and len(close.group(1)) >= fence_length:
                fence_char = None
                fence_length = 0
            continue

        visible, in_comment = _strip_html_comments(line, in_comment)
        fence = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", visible)
        if fence and (fence.group(1)[0] != "`" or "`" not in fence.group(2)):
            fence_char = fence.group(1)[0]
            fence_length = len(fence.group(1))
            continue
        yield visible


def _notice_digest_table_matches(index: bytes, fixture_id: str, manifest_digest: str,
                                 notice_digest: str) -> bool:
    try:
        lines = list(_active_notice_lines(index.decode("utf-8", errors="strict").splitlines()))
    except UnicodeDecodeError:
        return False

    def cells(line: str) -> list[str] | None:
        stripped = line.strip()
        if not (stripped.startswith("|") and stripped.endswith("|")):
            return None
        return [cell.strip() for cell in stripped[1:-1].split("|")]

    expected_header = ["Fixture directory", "`manifest.json` SHA-256", "`LICENSE.txt` SHA-256"]
    matches = 0
    in_digest_table = False
    header_seen = False
    separator_seen = False
    for line in lines:
        row = cells(line)
        if row == expected_header:
            if header_seen:
                return False
            header_seen = True
            in_digest_table = True
            continue
        if not in_digest_table:
            continue
        if not separator_seen:
            if row is None or len(row) != 3 or not all(re.fullmatch(r":?-{3,}:?", cell) for cell in row):
                return False
            separator_seen = True
            continue
        if row is None:
            in_digest_table = False
            continue
        if len(row) != 3:
            return False
        if row == [f"`{fixture_id}`", f"`{manifest_digest}`", f"`{notice_digest}`"]:
            matches += 1
    return header_seen and separator_seen and matches == 1


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


def _retain_stderr_tail(target: bytearray, chunk: bytes) -> None:
    if len(chunk) >= MAX_GIT_TREE_STDERR_BYTES:
        target[:] = chunk[-MAX_GIT_TREE_STDERR_BYTES:]
        return
    excess = len(target) + len(chunk) - MAX_GIT_TREE_STDERR_BYTES
    if excess > 0:
        del target[:excess]
    target.extend(chunk)


def tree_files(root: Path, revision: str, prefix: str) -> set[str]:
    result: set[str] = set()
    record_count = 0
    pending = bytearray()
    failures: queue.Queue[BaseException] = queue.Queue(maxsize=1)
    stderr_tail = bytearray()

    def record_failure(error: BaseException) -> None:
        try:
            failures.put_nowait(error)
        except queue.Full:
            pass

    def add_record(record: bytes) -> None:
        nonlocal record_count
        if not record:
            return
        record_count += 1
        if record_count > MAX_GIT_TREE_RECORDS:
            raise Reject("git-tree-entry-count-limit", f"more than {MAX_GIT_TREE_RECORDS} records")
        try:
            metadata, path_raw = record.split(b"\t", 1)
            mode, kind, _oid = metadata.decode("ascii").split(" ", 2)
            path = path_raw.decode("utf-8", errors="strict")
        except (ValueError, UnicodeDecodeError):
            raise Reject("git-tree-invalid", prefix) from None
        if kind != "blob" or mode not in ("100644", "100755"):
            raise Reject("fixture-link-or-special-file", path)
        result.add(path)

    command = ["git", "ls-tree", "-r", "-z", revision, "--", prefix]
    try:
        process = subprocess.Popen(command, cwd=root, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   bufsize=0)
    except OSError as error:
        raise Reject("git-object-unavailable", str(error)[:240]) from None
    if process.stdout is None or process.stderr is None:
        raise Reject("git-tree-reader-unavailable", prefix)

    def read_stdout() -> None:
        bytes_read = 0
        try:
            while True:
                read_size = min(GIT_TREE_READ_CHUNK_BYTES,
                                max(1, MAX_GIT_TREE_OUTPUT_BYTES - bytes_read + 1))
                chunk = process.stdout.read(read_size)
                if not chunk:
                    break
                bytes_read += len(chunk)
                if bytes_read > MAX_GIT_TREE_OUTPUT_BYTES:
                    raise Reject("git-tree-output-limit", f"more than {MAX_GIT_TREE_OUTPUT_BYTES} bytes")
                start = 0
                while True:
                    separator = chunk.find(b"\0", start)
                    if separator < 0:
                        pending.extend(chunk[start:])
                        break
                    pending.extend(chunk[start:separator])
                    add_record(bytes(pending))
                    pending.clear()
                    start = separator + 1
        except BaseException as error:
            if isinstance(error, Reject):
                record_failure(error)
            else:
                record_failure(Reject("git-tree-read-failed", type(error).__name__))
        finally:
            try:
                process.stdout.close()
            except OSError as error:
                record_failure(Reject("git-tree-read-failed", str(error)[:240]))

    def read_stderr() -> None:
        try:
            while True:
                chunk = process.stderr.read(MAX_GIT_TREE_STDERR_BYTES)
                if not chunk:
                    break
                _retain_stderr_tail(stderr_tail, chunk)
        except BaseException as error:
            record_failure(Reject("git-tree-read-failed", f"stderr: {type(error).__name__}"))
        finally:
            try:
                process.stderr.close()
            except OSError as error:
                record_failure(Reject("git-tree-read-failed", f"stderr: {str(error)[:240]}"))

    readers = [threading.Thread(target=read_stdout, name="fixture-git-tree-stdout", daemon=True),
               threading.Thread(target=read_stderr, name="fixture-git-tree-stderr", daemon=True)]
    waited = False
    try:
        for reader in readers:
            reader.start()
        deadline = time.monotonic() + GIT_TREE_TIMEOUT_SECONDS
        returncode = None
        failure = None
        while True:
            try:
                failure = failures.get_nowait()
                break
            except queue.Empty:
                pass
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                failure = Reject("git-tree-timeout", prefix)
                break
            try:
                returncode = process.wait(timeout=min(0.05, remaining))
                waited = True
                break
            except subprocess.TimeoutExpired:
                continue
            except OSError as error:
                failure = Reject("git-tree-read-failed", str(error)[:240])
                break

        if failure is None:
            for reader in readers:
                reader.join(max(0, deadline - time.monotonic()))
            if any(reader.is_alive() for reader in readers):
                failure = Reject("git-tree-timeout", f"reader did not finish for {prefix}")
            else:
                try:
                    failure = failures.get_nowait()
                except queue.Empty:
                    pass

        if failure is not None:
            raise failure
        if pending:
            raise Reject("git-tree-invalid", f"unterminated record in {prefix}")
        if returncode != 0:
            detail = bytes(stderr_tail).decode("utf-8", errors="replace").strip()[:240]
            raise Reject("git-object-unavailable", detail or "git ls-tree failed")
    finally:
        if not waited:
            try:
                if process.poll() is None:
                    process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
            except OSError:
                pass
        for stream in (process.stdout, process.stderr):
            try:
                stream.close()
            except OSError:
                pass
        for reader in readers:
            if reader.ident is not None:
                reader.join()
    return result


def current_fixture_files(root: Path, fixture_dir: str | None = None) -> set[str]:
    relative_root = "fixtures" if fixture_dir is None else relative_path(fixture_dir, "fixture directory")
    if relative_root != "fixtures" and not relative_root.startswith("fixtures/"):
        raise Reject("fixture-tree-unavailable", relative_root)
    fixture_root = root.joinpath(*PurePosixPath(relative_root).parts)
    try:
        root_mode = fixture_root.lstat().st_mode
    except OSError:
        raise Reject("fixture-tree-unavailable", f"{relative_root} is missing") from None
    if stat.S_ISLNK(root_mode):
        raise Reject("path-link", relative_root)
    if not stat.S_ISDIR(root_mode):
        raise Reject("fixture-tree-unavailable", relative_root)
    found: set[str] = set()
    pending = [(fixture_root, relative_root)]
    entry_count = 0
    while pending:
        directory, directory_relative = pending.pop()
        try:
            with os.scandir(directory) as entries:
                for entry in entries:
                    relative = f"{directory_relative}/{entry.name}"
                    entry_count += 1
                    if entry_count > MAX_FIXTURE_ENTRIES:
                        raise Reject("fixture-entry-count-limit",
                                     f"more than {MAX_FIXTURE_ENTRIES} entries under {relative_root}")
                    try:
                        mode = entry.stat(follow_symlinks=False).st_mode
                    except OSError:
                        raise Reject("fixture-tree-unavailable", relative) from None
                    if stat.S_ISLNK(mode):
                        raise Reject("path-link", relative)
                    if stat.S_ISDIR(mode):
                        pending.append((Path(entry.path), relative))
                    elif stat.S_ISREG(mode):
                        found.add(relative)
                    else:
                        raise Reject("fixture-special-file", relative)
        except OSError as error:
            raise Reject("fixture-tree-unavailable", f"{directory_relative}: {error.strerror}") from None
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
    if index_path != "THIRD_PARTY_NOTICES.md":
        raise Reject("notice-index-path-invalid", "notices.index_path must be THIRD_PARTY_NOTICES.md")
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
    current_files = current_fixture_files(root, fixture_dir)
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
    fixture_id = PurePosixPath(fixture_dir).name
    if not _notice_digest_table_matches(notice_index, fixture_id, manifest_digest, license_digest):
        raise Reject("notice-index-mismatch", index_path)
    return {"fixture": fixture_dir, "pin": pin, "files": len(files)}


def check_repository(root: Path, baseline: str, baseline_root: Path | None = None) -> dict:
    # The subject supplies current bytes and policy; only immutable baseline objects may
    # come from a separate trusted object store used by source-only mutant harnesses.
    evidence_root = root if baseline_root is None else baseline_root.resolve(strict=True)
    baseline = check_commit(evidence_root, baseline, "baseline-object-unavailable")
    baseline_files = tree_files(evidence_root, baseline, "fixtures")
    current_files = current_fixture_files(root)
    loose_paths = {path for path in baseline_files | current_files
                   if path.startswith("fixtures/") and len(PurePosixPath(path).parts) < 3}
    for path in sorted(loose_paths):
        if (path in baseline_files and path in current_files
                and read_regular(root, path) == blob(evidence_root, baseline, path)):
            continue
        raise Reject("fixture-admission-required", f"changed fixture path {path} has no fixture-directory manifest")
    all_ids = {path.split("/", 2)[1] for path in baseline_files | current_files if path.startswith("fixtures/")}
    changed = 0
    for fixture_id in sorted(all_ids):
        prefix = f"fixtures/{fixture_id}/"
        old = {path for path in baseline_files if path.startswith(prefix)}
        new = {path for path in current_files if path.startswith(prefix)}
        identical = old == new
        if identical:
            for path in sorted(old):
                if read_regular(root, path) != blob(evidence_root, baseline, path):
                    identical = False
                    break
        if identical:
            continue
        manifest_path = prefix + "manifest.json"
        if manifest_path not in new:
            raise Reject("fixture-admission-required", f"changed fixture {fixture_id} has no manifest")
        changed += 1
        check_manifest(root, manifest_path)

    baseline_license = blob(evidence_root, baseline, "LICENSE")
    if read_regular(root, "LICENSE") != baseline_license:
        raise Reject("root-license-mismatch", "LICENSE differs from the immutable project baseline")
    if not baseline_files:
        raise Reject("baseline-fixtures-empty", "the fixed baseline contains no fixture files")
    return {"legacy_files": len(baseline_files), "admitted_changes": changed, "baseline": baseline}


def _product_rules(root: Path, override: dict | None = None) -> tuple[dict, bytes]:
    policy_bytes = read_regular(root, "cmake/FixtureAdmissionPolicy.json")
    _check_product_policy_identity(policy_bytes)
    policy = parse_json(policy_bytes, "FixtureAdmissionPolicy.json")
    require_keys(policy, {"schema_version", "baseline_commit", "products"}, "FixtureAdmissionPolicy.json")
    if policy["schema_version"] != 1 or policy["baseline_commit"] != BASELINE_COMMIT:
        raise Reject("policy-invalid", "baseline commit differs from the reviewed full identity")
    rules = override if override is not None else policy.get("products")
    if not isinstance(rules, dict):
        raise Reject("product-policy-invalid", "products must be an object")
    require_keys(rules, {"files", "external_notices", "release_notice_sidecar", "generated"}, "products")
    files = rules["files"]
    if not isinstance(files, dict) or not files:
        raise Reject("product-policy-invalid", "products.files must be a non-empty object")
    for source_path, record in files.items():
        relative_path(source_path, "product source path")
        if not isinstance(record, dict):
            raise Reject("product-policy-invalid", source_path)
        require_keys(record, {"sha256", "destinations"}, f"products.files.{source_path}")
        if not isinstance(record["sha256"], str) or not HEX64.fullmatch(record["sha256"]):
            raise Reject("product-policy-invalid", f"products.files.{source_path}.sha256")
        destinations = record["destinations"]
        if not isinstance(destinations, dict) or set(destinations) - {"core", "player"}:
            raise Reject("product-policy-invalid", f"products.files.{source_path}.destinations")
        for layout, paths in destinations.items():
            if not isinstance(paths, list) or not paths:
                raise Reject("product-policy-invalid", f"products.files.{source_path}.{layout}")
            for path in paths:
                relative_path(path, f"products.files.{source_path}.{layout}")
    notices = rules["external_notices"]
    if not isinstance(notices, dict) or set(notices) != {"sdl3"}:
        raise Reject("product-policy-invalid", "external_notices must define the pinned SDL3 license")
    for name, record in notices.items():
        if not isinstance(record, dict):
            raise Reject("product-policy-invalid", f"external_notices.{name}")
        require_keys(record, {"path", "size_bytes", "sha256"}, f"external_notices.{name}")
        relative_path(record["path"], f"external_notices.{name}.path")
        if (not isinstance(record["size_bytes"], int) or isinstance(record["size_bytes"], bool)
                or record["size_bytes"] <= 0 or record["size_bytes"] > MAX_PRODUCT_FILE_BYTES
                or not isinstance(record["sha256"], str) or not HEX64.fullmatch(record["sha256"])):
            raise Reject("product-policy-invalid", f"external_notices.{name} identity")
    sidecar = rules["release_notice_sidecar"]
    if not isinstance(sidecar, dict):
        raise Reject("product-policy-invalid", "release_notice_sidecar must be an object")
    require_keys(sidecar, {"path", "sha256"}, "release_notice_sidecar")
    relative_path(sidecar["path"], "release_notice_sidecar.path")
    if not isinstance(sidecar["sha256"], str) or not HEX64.fullmatch(sidecar["sha256"]):
        raise Reject("product-policy-invalid", "release_notice_sidecar.sha256")
    generated = rules["generated"]
    if not isinstance(generated, dict) or set(generated) != {"core", "player"}:
        raise Reject("product-policy-invalid", "generated must define core and player layouts")
    for layout, record in generated.items():
        if not isinstance(record, dict):
            raise Reject("product-policy-invalid", f"generated.{layout}")
        require_keys(record, {"required", "one_of"}, f"generated.{layout}")
        if not isinstance(record["required"], list) or not isinstance(record["one_of"], list):
            raise Reject("product-policy-invalid", f"generated.{layout} path groups")
        for path in record["required"]:
            relative_path(path, f"generated.{layout}.required")
        for alternatives in record["one_of"]:
            if not isinstance(alternatives, list) or not alternatives:
                raise Reject("product-policy-invalid", f"generated.{layout}.one_of")
            for path in alternatives:
                relative_path(path, f"generated.{layout}.one_of")
    return rules, policy_bytes


def _check_product_policy_identity(policy_bytes: bytes) -> None:
    if sha256(policy_bytes) != PRODUCT_POLICY_SHA256:
        raise Reject("product-policy-identity", "complete policy bytes do not match the trusted checker pin")


def _check_product_notice_index(baseline_index: bytes, current_index: bytes) -> None:
    """Allow the reviewed product-policy paragraph while pinning every other notice byte."""
    if baseline_index.count(NOTICE_BASELINE_PRODUCT_CLAIM) != 1:
        raise Reject("product-source-mismatch", "baseline product-policy paragraph is not uniquely identifiable")
    approved_index = baseline_index.replace(NOTICE_BASELINE_PRODUCT_CLAIM, NOTICE_APPROVED_PRODUCT_CLAIM, 1)
    if current_index not in (baseline_index, approved_index):
        raise Reject("product-source-mismatch", "THIRD_PARTY_NOTICES.md differs outside the approved product-policy paragraph")


def _product_source_expectations(root: Path, rules: dict, layout: str) -> tuple[dict[str, dict], set[str], bytes]:
    baseline = check_commit(root, BASELINE_COMMIT, "baseline-object-unavailable")
    # Source artifacts and the notice index are still checked against the immutable baseline
    # when a caller validates bytes extracted from an archive.
    check_repository(root, baseline)
    pinned_index = blob(root, baseline, "THIRD_PARTY_NOTICES.md")
    _check_product_notice_index(pinned_index, read_regular(root, "THIRD_PARTY_NOTICES.md"))
    expected: dict[str, dict] = {}
    allowed_fixture_sources: set[str] = set()
    for source_path, record in rules["files"].items():
        pinned = blob(root, baseline, source_path)
        digest = sha256(pinned)
        if digest != record["sha256"]:
            raise Reject("product-policy-invalid", f"{source_path} digest is not the pinned baseline digest")
        if read_regular(root, source_path) != pinned:
            raise Reject("product-source-mismatch", source_path)
        if source_path.startswith("fixtures/"):
            allowed_fixture_sources.add(source_path)
        for destination in record["destinations"].get(layout, []):
            if destination in expected:
                raise Reject("product-policy-invalid", f"duplicate product destination: {destination}")
            expected[destination] = {"kind": "file", "size_bytes": len(pinned), "sha256": digest}

    if layout == "player":
        sdl = rules["external_notices"]["sdl3"]
        expected[sdl["path"]] = {"kind": "file", "size_bytes": sdl["size_bytes"], "sha256": sdl["sha256"]}
    generated = rules["generated"][layout]
    for path in generated["required"]:
        if path in expected:
            raise Reject("product-policy-invalid", f"generated path overlaps protected source: {path}")
        expected[path] = {"kind": "generated"}
    alternative_groups: list[list[str]] = []
    for alternatives in generated["one_of"]:
        if len(set(alternatives)) != len(alternatives) or any(path in expected for path in alternatives):
            raise Reject("product-policy-invalid", f"duplicate generated alternative: {alternatives}")
        alternative_groups.append(alternatives)
    allowed = set(expected)
    for alternatives in alternative_groups:
        allowed.update(alternatives)

    # Any fixture blob outside the exact source set for this layout is forbidden everywhere in
    # the product, even if renamed or stripped of its usual ROM/file suffix.
    forbidden: set[str] = set()
    baseline_fixture_paths = tree_files(root, baseline, "fixtures")
    total_fixture_bytes = 0
    for path in baseline_fixture_paths:
        if path in allowed_fixture_sources:
            continue
        data = blob(root, baseline, path)
        total_fixture_bytes += len(data)
        if total_fixture_bytes > MAX_TOTAL_FIXTURE_BYTES:
            raise Reject("product-source-size-limit", "fixture digest scan exceeds the bounded total")
        forbidden.add(sha256(data))
    for path in current_fixture_files(root):
        if path in allowed_fixture_sources:
            continue
        data = read_regular(root, path)
        total_fixture_bytes += len(data)
        if total_fixture_bytes > 2 * MAX_TOTAL_FIXTURE_BYTES:
            raise Reject("product-source-size-limit", "current fixture digest scan exceeds the bounded total")
        forbidden.add(sha256(data))
    return expected, forbidden, pinned_index


def _normalize_product_entries(entries: Mapping | Iterable) -> dict[str, dict]:
    if isinstance(entries, Mapping):
        pairs = entries.items()
    else:
        pairs = entries
    normalized: dict[str, dict] = {}
    folded: set[str] = set()
    count = 0
    for item in pairs:
        try:
            path_value, record = item
        except (TypeError, ValueError):
            raise Reject("product-entry-invalid", "each product entry must be a path and record") from None
        path = relative_path(path_value, "product entry path")
        count += 1
        if count > MAX_PRODUCT_ENTRIES:
            raise Reject("product-entry-count-limit", "too many product entries")
        if path in normalized:
            raise Reject("product-path-duplicate", path)
        folded_path = path.casefold()
        if folded_path in folded:
            raise Reject("product-path-duplicate", f"case-fold collision at {path}")
        folded.add(folded_path)
        if not isinstance(record, dict) or "kind" not in record:
            raise Reject("product-entry-invalid", path)
        kind = record["kind"]
        if kind in ("symlink", "link", "hardlink"):
            raise Reject("path-link", path)
        if kind == "directory":
            if set(record) - {"kind", "size_bytes", "sha256"}:
                raise Reject("product-entry-invalid", path)
            normalized[path] = {"kind": "directory"}
            continue
        if kind != "file" or set(record) != {"kind", "size_bytes", "sha256"}:
            raise Reject("product-entry-invalid", path)
        size, digest = record["size_bytes"], record["sha256"]
        if (not isinstance(size, int) or isinstance(size, bool) or size < 0
                or size > MAX_PRODUCT_FILE_BYTES or not isinstance(digest, str) or not HEX64.fullmatch(digest)):
            raise Reject("product-entry-invalid", path)
        normalized[path] = {"kind": "file", "size_bytes": size, "sha256": digest}
    if sum(record.get("size_bytes", 0) for record in normalized.values()) > MAX_PRODUCT_TOTAL_BYTES:
        raise Reject("product-total-size-limit", "product is too large")
    return normalized


def _inventory_record(layout: str, entries: dict[str, dict], policy_bytes: bytes) -> dict:
    files = {path: record for path, record in sorted(entries.items()) if record["kind"] == "file"}
    return {"schema_version": 1, "layout": layout, "policy_sha256": sha256(policy_bytes), "files": files}


def _validate_product_entries(entries: Mapping | Iterable, layout: str, repo_root: Path,
                              inventory: object = None, sidecar: object = None,
                              rules_override: dict | None = None,
                              source_contract: tuple[dict[str, dict], set[str], bytes] | None = None) -> dict:
    if layout not in ("core", "player"):
        raise Reject("product-layout-invalid", layout)
    rules, policy_bytes = _product_rules(repo_root, rules_override)
    expected, forbidden, _pinned_index = source_contract or _product_source_expectations(repo_root, rules, layout)
    actual = _normalize_product_entries(entries)
    generated = rules["generated"][layout]
    allowed_files = set(expected)
    alternative_groups = [set(group) for group in generated["one_of"]]
    allowed_files.update(path for group in alternative_groups for path in group)
    required_paths = set(expected)
    allowed_directories: set[str] = set()
    for path in allowed_files:
        parts = PurePosixPath(path).parts
        for index in range(1, len(parts)):
            allowed_directories.add("/".join(parts[:index]))
    for path, record in actual.items():
        if record["kind"] == "directory":
            if path not in allowed_directories:
                raise Reject("product-path-unknown", path)
            continue
        if record["sha256"] in forbidden:
            expected_record = expected.get(path)
            exact_pinned_file = (
                expected_record is not None
                and expected_record["kind"] == "file"
                and record["size_bytes"] == expected_record["size_bytes"]
                and record["sha256"] == expected_record["sha256"]
            )
            if not exact_pinned_file:
                raise Reject("product-fixture-leak", path)
        if path not in allowed_files:
            raise Reject("product-path-unknown", path)
        if path in expected:
            expected_record = expected[path]
            if expected_record["kind"] == "file":
                if (record["size_bytes"] != expected_record["size_bytes"]
                        or record["sha256"] != expected_record["sha256"]):
                    raise Reject("product-identity-mismatch", path)
            elif record["size_bytes"] == 0:
                raise Reject("product-generated-file-empty", path)
    missing = sorted(required_paths - set(actual))
    if missing:
        raise Reject("product-path-missing", missing[0])
    for group in alternative_groups:
        present = group & set(actual)
        if len(present) != 1:
            raise Reject("product-path-variant-invalid", ",".join(sorted(group)))
    if sidecar is not None:
        expected_sidecar = rules["release_notice_sidecar"]
        if isinstance(sidecar, bytes):
            sidecar_bytes = sidecar
        else:
            sidecar_path = Path(sidecar)
            if not sidecar_path.is_absolute():
                sidecar_path = repo_root / sidecar_path
            try:
                if sidecar_path.is_symlink() or not sidecar_path.is_file():
                    raise Reject("product-notice-sidecar-invalid", expected_sidecar["path"])
                if sidecar_path.stat().st_size > MAX_PRODUCT_FILE_BYTES:
                    raise Reject("product-notice-sidecar-invalid", "sidecar exceeds size limit")
                sidecar_bytes = sidecar_path.read_bytes()
            except OSError:
                raise Reject("product-notice-sidecar-invalid", expected_sidecar["path"]) from None
        if sha256(sidecar_bytes) != expected_sidecar["sha256"]:
            raise Reject("product-notice-sidecar-mismatch", expected_sidecar["path"])

    candidate_inventory = _inventory_record(layout, actual, policy_bytes)
    if inventory is not None:
        if inventory != candidate_inventory:
            raise Reject("product-inventory-mismatch", "validated paths, sizes, bytes, layout, or policy identity differ")
    return candidate_inventory


def check_product_entries(entries: Mapping | Iterable, layout: str, repo_root: Path,
                          inventory: object = None, sidecar: object = None) -> dict:
    """Validate normalized product entries against pinned fixture and notice paths."""
    return _validate_product_entries(entries, layout, repo_root, inventory=inventory, sidecar=sidecar)


def _hash_product_file(path: Path, relative: str) -> dict:
    try:
        if path.is_symlink():
            raise Reject("path-link", relative)
        info = path.lstat()
    except OSError:
        raise Reject("product-tree-unavailable", relative) from None
    if not stat.S_ISREG(info.st_mode):
        raise Reject("product-special-file", relative)
    if info.st_size > MAX_PRODUCT_FILE_BYTES:
        raise Reject("product-file-size-limit", relative)
    data = path.read_bytes()
    if len(data) != info.st_size:
        raise Reject("product-tree-changed", relative)
    return {"kind": "file", "size_bytes": len(data), "sha256": sha256(data)}


def product_tree_entries(tree: Path) -> dict[str, dict]:
    try:
        root = tree.resolve(strict=True)
    except OSError:
        raise Reject("product-tree-unavailable", str(tree)) from None
    if not root.is_dir() or tree.is_symlink():
        raise Reject("product-tree-unavailable", str(tree))
    entries: dict[str, dict] = {}
    folded: set[str] = set()
    pending = [root]
    entry_count = 0
    while pending:
        current_path = pending.pop()
        try:
            with os.scandir(current_path) as children:
                for child in children:
                    entry_count += 1
                    if entry_count > MAX_PRODUCT_ENTRIES:
                        raise Reject("product-entry-count-limit", "too many product entries")
                    path = Path(child.path)
                    relative = relative_path(path.relative_to(root).as_posix(), "product entry")
                    if relative.casefold() in folded:
                        raise Reject("product-path-duplicate", relative)
                    folded.add(relative.casefold())
                    try:
                        mode = child.stat(follow_symlinks=False).st_mode
                    except OSError:
                        raise Reject("product-tree-unavailable", relative) from None
                    if stat.S_ISLNK(mode):
                        raise Reject("path-link", relative)
                    if stat.S_ISDIR(mode):
                        entries[relative] = {"kind": "directory"}
                        pending.append(path)
                    elif stat.S_ISREG(mode):
                        entries[relative] = _hash_product_file(path, relative)
                    else:
                        raise Reject("product-special-file", relative)
        except Reject:
            raise
        except OSError as error:
            directory = current_path.relative_to(root).as_posix() if current_path != root else "."
            raise Reject("product-tree-unavailable", f"{directory}: {error.strerror}") from None
    return entries


def _read_inventory(path: Path) -> dict:
    try:
        if path.is_symlink() or not path.is_file():
            raise Reject("product-inventory-invalid", str(path))
        return parse_json(path.read_bytes(), "product inventory")
    except OSError:
        raise Reject("product-inventory-invalid", str(path)) from None


def _write_inventory(path: Path, inventory: dict, repo_root: Path) -> None:
    if not path.is_absolute():
        path = repo_root / path
    parent = path.parent.resolve(strict=True)
    if path.exists() or path.is_symlink():
        raise Reject("product-inventory-exists", str(path))
    temporary = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=parent,
                                         prefix=f".{path.name}.", suffix=".tmp", delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(inventory, stream, indent=2, sort_keys=True)
            stream.write("\n")
        os.replace(temporary, path)
    except OSError as error:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
        raise Reject("product-inventory-write-failed", error.strerror or "write failed") from None


def _read_sidecar_argument(root: Path, value: str | None) -> object:
    return Path(value) if value is not None else None


def check_product_documentation(root: Path, rules: dict, content: bytes | None = None) -> None:
    if content is None:
        content = read_regular(root, "docs/fixture-admission.md")
    try:
        text = content.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        raise Reject("product-doc-contract", "documentation is not UTF-8") from None
    required_text = (
        "--check-product-tree", "--layout core", "--layout player", "--write-inventory",
        "--inventory", "--notice-sidecar", "check_product_entries", "THIRD_PARTY_NOTICES.md",
        "does not decide whether a grant's author had authority",
        "A source archive is not a core or player product",
    )
    missing = [item for item in required_text if item not in text]
    if missing:
        raise Reject("product-doc-contract", f"missing contract text: {missing[0]}")
    product_paths = {rules["release_notice_sidecar"]["path"]}
    product_paths.update(record["path"] for record in rules["external_notices"].values())
    for record in rules["files"].values():
        for paths in record["destinations"].values():
            product_paths.update(paths)
    for layout in ("core", "player"):
        product_paths.update(rules["generated"][layout]["required"])
        for group in rules["generated"][layout]["one_of"]:
            product_paths.update(group)
    absent = sorted(path for path in product_paths if path not in text)
    if absent:
        raise Reject("product-doc-contract", f"missing policy path: {absent[0]}")


def _synthetic_product_rules(rules: dict, layout: str) -> tuple[dict, bytes]:
    test_rules = copy.deepcopy(rules)
    sdl_bytes = b"Synthetic SDL notice for package-policy controls only.\n"
    if layout == "player":
        test_rules["external_notices"]["sdl3"]["size_bytes"] = len(sdl_bytes)
        test_rules["external_notices"]["sdl3"]["sha256"] = sha256(sdl_bytes)
        # The reviewed player policy currently has no alternatives. Exercise the validator's
        # generic one_of behavior with a self-test-only group without changing the pinned policy.
        test_rules["generated"]["player"]["one_of"].append([
            "share/gabbaboy/generated/player-control-a.bin",
            "share/gabbaboy/generated/player-control-b.bin",
        ])
    return test_rules, sdl_bytes


def _write_synthetic_product_tree(tree: Path, repo_root: Path, layout: str, rules: dict,
                                  sdl_bytes: bytes,
                                  source_contract: tuple[dict[str, dict], set[str], bytes] | None = None) -> None:
    expected, _forbidden, _notice_index = source_contract or _product_source_expectations(repo_root, rules, layout)
    payloads: dict[str, bytes] = {}
    baseline = check_commit(repo_root, BASELINE_COMMIT, "baseline-object-unavailable")
    for source_path, record in rules["files"].items():
        data = blob(repo_root, baseline, source_path)
        if sha256(data) != record["sha256"]:
            raise Reject("self-test-product-policy", source_path)
        for destination in record["destinations"].get(layout, []):
            payloads[destination] = data
    if layout == "player":
        sdl_path = rules["external_notices"]["sdl3"]["path"]
        payloads[sdl_path] = sdl_bytes
    generated = rules["generated"][layout]
    for path in generated["required"]:
        payloads[path] = f"synthetic generated output: {path}\n".encode("utf-8")
    for alternatives in generated["one_of"]:
        path = alternatives[0]
        payloads[path] = f"synthetic generated output: {path}\n".encode("utf-8")
    if set(expected) - set(payloads):
        raise Reject("self-test-product-policy", "synthetic product is missing an expected path")
    for relative, data in payloads.items():
        target = tree.joinpath(*PurePosixPath(relative).parts)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)


def _expect_product_reject(label: str, operation, code: str) -> None:
    try:
        operation()
    except Reject as error:
        if error.code != code:
            raise Reject(f"self-test-product-{label}", f"expected {code}, received {error}") from None
        return
    raise Reject(f"self-test-product-{label}", f"mutation was accepted; expected {code}")


def _self_test_product_notice_index(repo_root: Path) -> int:
    baseline = check_commit(repo_root, BASELINE_COMMIT, "baseline-object-unavailable")
    pinned = blob(repo_root, baseline, "THIRD_PARTY_NOTICES.md")
    current = read_regular(repo_root, "THIRD_PARTY_NOTICES.md")
    _check_product_notice_index(pinned, current)
    approved = pinned.replace(NOTICE_BASELINE_PRODUCT_CLAIM, NOTICE_APPROVED_PRODUCT_CLAIM, 1)
    _check_product_notice_index(pinned, approved)

    controls = [
        ("arbitrary-paragraph-edit", approved.replace(b"No fixture below", b"Every fixture below", 1)),
        ("removed-product-claim", approved.replace(NOTICE_APPROVED_PRODUCT_CLAIM, b"", 1)),
        ("altered-product-claim", approved.replace(NOTICE_APPROVED_PRODUCT_CLAIM,
                                                    NOTICE_APPROVED_PRODUCT_CLAIM + b" altered", 1)),
        ("historical-digest-row-change",
         approved.replace(b"59284b6087dc6cb3bf08169b0c3e58444197494521750fac11839632c652cf5c",
                          b"09284b6087dc6cb3bf08169b0c3e58444197494521750fac11839632c652cf5c", 1)),
    ]
    for label, candidate in controls:
        if candidate == approved:
            raise Reject("self-test-product-notice-index", f"{label} did not alter its target")
        try:
            _check_product_notice_index(pinned, candidate)
        except Reject as error:
            if error.code != "product-source-mismatch":
                raise Reject("self-test-product-notice-index", f"{label} failed for an unrelated reason") from None
        else:
            raise Reject("self-test-product-notice-index", f"{label} was accepted")
        print(f"rejected: notice index {label}")
    return len(controls)


def self_test_packages(layout: str) -> int:
    if layout not in ("core", "player"):
        raise Reject("product-layout-invalid", layout)
    repo_root = Path(__file__).resolve().parents[2]
    rules, _policy_bytes = _product_rules(repo_root)
    policy_controls = 0
    _check_product_policy_identity(_policy_bytes)
    mutated_policy = _policy_bytes.replace(b"fixtures/tracer/tracer.gb", b"fixtures/tracer/other.gb", 1)
    if mutated_policy == _policy_bytes:
        raise Reject("self-test-product-policy-pin", "policy mutation did not change bytes")
    _expect_product_reject("policy-byte-identity", lambda: _check_product_policy_identity(mutated_policy),
                           "product-policy-identity")
    policy_controls += 1

    coordinated = json.loads(_policy_bytes)
    baseline = check_commit(repo_root, BASELINE_COMMIT, "baseline-object-unavailable")
    forbidden_path = next(path for path in sorted(tree_files(repo_root, baseline, "fixtures"))
                          if path not in coordinated["products"]["files"])
    forbidden_bytes = blob(repo_root, baseline, forbidden_path)
    coordinated["products"]["files"][forbidden_path] = {
        "sha256": sha256(forbidden_bytes),
        "destinations": {"core": ["share/gabbaboy/fixtures/forbidden/" + PurePosixPath(forbidden_path).name]},
    }
    coordinated_bytes = json.dumps(coordinated, sort_keys=True, separators=(",", ":")).encode()
    _expect_product_reject("coordinated-policy-identity", lambda: _check_product_policy_identity(coordinated_bytes),
                           "product-policy-identity")
    policy_controls += 1
    check_product_documentation(repo_root, rules)
    if (rules["external_notices"]["sdl3"]["sha256"]
            != "1c040b8271b37e5076359f8fd54240e371114112924d2df81ef87c7d6a1dfdfd"
            or rules["external_notices"]["sdl3"]["size_bytes"] != 884):
        raise Reject("self-test-product-sdl-pin", "SDL license identity differs from the reviewed source notice")
    test_rules, sdl_bytes = _synthetic_product_rules(rules, layout)
    source_contract = _product_source_expectations(repo_root, test_rules, layout)
    with tempfile.TemporaryDirectory(prefix=f"gbb-product-{layout}-positive-") as directory:
        tree = Path(directory) / "installed-prefix"
        tree.mkdir()
        _write_synthetic_product_tree(tree, repo_root, layout, test_rules, sdl_bytes, source_contract)
        entries = product_tree_entries(tree)
        clean_inventory = _validate_product_entries(entries, layout, repo_root, rules_override=test_rules,
                                                     source_contract=source_contract)
        controls = 1 + _self_test_product_notice_index(repo_root) + policy_controls

        if layout == "core":
            configuration_group = rules["generated"]["core"]["one_of"][2]
            selected = next(path for path in configuration_group if path in entries)
            for alternative in configuration_group:
                variant_entries = dict(entries)
                variant_entries.pop(selected)
                variant_entries[alternative] = entries[selected]
                _validate_product_entries(variant_entries, layout, repo_root, rules_override=test_rules,
                                          source_contract=source_contract)
                controls += 1

        def rejected_tree(label: str, mutate, code: str) -> None:
            nonlocal controls
            with tempfile.TemporaryDirectory(prefix=f"gbb-product-{layout}-{label}-") as case_dir:
                candidate = Path(case_dir) / "installed-prefix"
                shutil.copytree(tree, candidate, symlinks=True)
                mutate(candidate)
                candidate_entries = product_tree_entries(candidate)
                _expect_product_reject(label, lambda: _validate_product_entries(
                    candidate_entries, layout, repo_root, rules_override=test_rules,
                    source_contract=source_contract), code)
                controls += 1

        if layout == "core":
            second_configuration = next(path for path in rules["generated"]["core"]["one_of"][2]
                                        if path not in entries)
            rejected_tree("simultaneous-config-exports",
                          lambda candidate: (candidate / second_configuration).parent.mkdir(parents=True, exist_ok=True)
                          or (candidate / second_configuration).write_bytes(b"extra configuration export"),
                          "product-path-variant-invalid")

        fixture_prefixes = sorted({
            destination.rsplit("/", 1)[0]
            for record in rules["files"].values()
            for destination in record["destinations"].get(layout, [])
            if destination.startswith("share/gabbaboy/fixtures/")
        })
        for index, fixture_dir in enumerate(fixture_prefixes):
            rejected_tree(f"extra-fixture-member-{index}",
                          lambda candidate, fixture_dir=fixture_dir: (candidate / fixture_dir / "extra.bin").write_bytes(b"unregistered"),
                          "product-path-unknown")
        # A different basename or no suffix cannot disguise a known repository-only fixture.
        allowed_source_paths = {path for path, record in rules["files"].items()
                                if record["destinations"].get(layout)}
        baseline = check_commit(repo_root, BASELINE_COMMIT, "baseline-object-unavailable")
        forbidden_path = next(path for path in sorted(tree_files(repo_root, baseline, "fixtures"))
                              if path not in allowed_source_paths)
        forbidden_product_bytes = blob(repo_root, baseline, forbidden_path)
        forbidden_product_digest = sha256(forbidden_product_bytes)
        if forbidden_product_digest not in source_contract[1]:
            raise Reject("self-test-product-forbidden-digest", forbidden_path)
        for name in ("renamed-payload.bin", "suffixless"):
            rejected_tree(name, lambda candidate, name=name: (candidate / "share/gabbaboy" / name).write_bytes(forbidden_product_bytes),
                          "product-fixture-leak")

        required_generated_path = next(path for path in test_rules["generated"][layout]["required"]
                                       if path in clean_inventory["files"])
        rejected_tree(f"forbidden-required-generated-{layout}",
                      lambda candidate: (candidate / required_generated_path).write_bytes(forbidden_product_bytes),
                      "product-fixture-leak")

        if test_rules["generated"][layout]["one_of"]:
            one_of_group = test_rules["generated"][layout]["one_of"][0]
            selected_one_of = next(path for path in one_of_group if path in clean_inventory["files"])
            rejected_tree(f"forbidden-one-of-generated-{layout}",
                          lambda candidate: (candidate / selected_one_of).write_bytes(forbidden_product_bytes),
                          "product-fixture-leak")

        protected_paths = sorted(path for path in clean_inventory["files"]
                                 if "LICENSE" in PurePosixPath(path).name)
        for path in protected_paths:
            rejected_tree(f"missing-notice-{controls}", lambda candidate, path=path: (candidate / path).unlink(),
                          "product-path-missing")
            rejected_tree(f"altered-notice-{controls}", lambda candidate, path=path:
                          (candidate / path).write_bytes((candidate / path).read_bytes() + b"altered\n"),
                          "product-identity-mismatch")

        fixture_product_paths = sorted(path for path in clean_inventory["files"]
                                        if path.startswith("share/gabbaboy/fixtures/")
                                        and "LICENSE" not in PurePosixPath(path).name)
        for index, path in enumerate(fixture_product_paths):
            rejected_tree(f"changed-fixture-identity-{index}", lambda candidate, path=path:
                          (candidate / path).write_bytes((candidate / path).read_bytes() + b"changed\n"),
                          "product-identity-mismatch")
        missing_fixture = fixture_product_paths[0]
        rejected_tree("missing-fixture-member", lambda candidate: (candidate / missing_fixture).unlink(),
                      "product-path-missing")

        if layout == "core":
            sidecar = blob(repo_root, baseline, "LICENSE")
            _validate_product_entries(entries, layout, repo_root, sidecar=sidecar, rules_override=test_rules,
                                      source_contract=source_contract)
            _expect_product_reject("altered-release-sidecar", lambda: _validate_product_entries(
                entries, layout, repo_root, sidecar=sidecar + b"altered", rules_override=test_rules,
                source_contract=source_contract),
                "product-notice-sidecar-mismatch")
            controls += 1

        inventory_changed = {path: dict(record) for path, record in entries.items()}
        generated_path = next(path for path, record in inventory_changed.items()
                              if record["kind"] == "file" and path in rules["generated"][layout]["required"])
        inventory_changed[generated_path]["sha256"] = "0" * 64
        _expect_product_reject("inventory-difference", lambda: _validate_product_entries(
            inventory_changed, layout, repo_root, inventory=clean_inventory, rules_override=test_rules,
            source_contract=source_contract),
            "product-inventory-mismatch")
        controls += 1

        duplicate_entries = list(entries.items()) + [next(iter(entries.items()))]
        _expect_product_reject("duplicate-entry", lambda: _validate_product_entries(
            duplicate_entries, layout, repo_root, rules_override=test_rules,
            source_contract=source_contract), "product-path-duplicate")
        controls += 1

        _expect_product_reject("source-notices-file", lambda: _validate_product_entries(
            {**entries, "THIRD_PARTY_NOTICES.md": {"kind": "file", "size_bytes": 1, "sha256": "0" * 64}},
            layout, repo_root, rules_override=test_rules, source_contract=source_contract), "product-path-unknown")
        controls += 1

        with tempfile.TemporaryDirectory(prefix=f"gbb-product-{layout}-receipt-") as case_dir:
            candidate = Path(case_dir) / "installed-prefix"
            shutil.copytree(tree, candidate, symlinks=True)
            (candidate / "unapproved-output").write_bytes(b"unexpected")
            receipt_path = Path(case_dir) / "rejected-inventory.json"
            result = subprocess.run(
                [sys.executable, "-I", str(Path(__file__).resolve()), "--check-product-tree", str(candidate),
                 "--layout", layout, "--repo-root", str(repo_root), "--write-inventory", str(receipt_path)],
                capture_output=True, text=True, check=False, timeout=30)
            if result.returncode == 0 or "REJECT product-path-unknown:" not in result.stderr:
                raise Reject("self-test-product-rejected-receipt", result.stderr.strip() or
                             "product with an unknown path was accepted")
            if receipt_path.exists() or receipt_path.is_symlink():
                raise Reject("self-test-product-rejected-receipt", "rejected product wrote an inventory receipt")
            controls += 1

        doc = read_regular(repo_root, "docs/fixture-admission.md")
        damaged_doc = doc.replace(b"share/gabbaboy/fixtures/tracer/tracer.gb",
                                  b"share/gabbaboy/fixtures/tracer/renamed.gb")
        _expect_product_reject("documentation-mismatch", lambda: check_product_documentation(
            repo_root, rules, damaged_doc), "product-doc-contract")
        controls += 1

        with tempfile.TemporaryDirectory(prefix=f"gbb-product-{layout}-link-") as link_dir:
            candidate = Path(link_dir) / "installed-prefix"
            shutil.copytree(tree, candidate, symlinks=True)
            link_target = next(path for path in sorted(candidate.rglob("*")) if path.is_file() and not path.is_symlink())
            link_target.unlink()
            try:
                link_target.symlink_to("/etc/passwd")
            except OSError as error:
                raise Reject("self-test-product-link", f"could not create controlled symlink: {error}") from None
            _expect_product_reject("link-escape", lambda: product_tree_entries(candidate), "path-link")
            controls += 1

        print(f"PASS: fixture admission product layout={layout} positive=1 negative_controls={controls}")
        return controls


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
        # External revisions are identifiers in their named repositories. These intentionally
        # do not resolve in the synthetic GabbaBoy Git database.
        "source": {"repository": "https://example.invalid/fixture", "revision": "f" * 40},
        "inputs": [input_record],
        "files": files,
        "build": {"recipe": "synthetic build", "tools": [{"name": "test-tool", "version": "1.0",
                   "terms": "MIT", "source_repository": "https://example.invalid/tool", "revision": "e" * 40,
                   "disposition": "build_only", "component": None, "covered_paths": []}]},
        "components": components,
        "notices": {"local_path": "fixtures/synthetic/LICENSE.txt", "sha256": sha256(license_bytes),
                    "index_path": "THIRD_PARTY_NOTICES.md"},
    }
    manifest_path = root / "fixtures/synthetic/manifest.json"
    manifest_path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    manifest_digest = sha256(manifest_path.read_bytes())
    (root / "THIRD_PARTY_NOTICES.md").write_text(
        "### Manifest and notice digests\n\n"
        "| Fixture directory | `manifest.json` SHA-256 | `LICENSE.txt` SHA-256 |\n"
        "|---|---|---|\n"
        f"| `synthetic` | `{manifest_digest}` | `{sha256(license_bytes)}` |\n", encoding="utf-8")
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
    changed("build-tool-revision-malformed", lambda value: value["build"]["tools"][0].update(revision="main"),
            "REJECT build-tool-revision-invalid:")
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
    changed("notice-index-redirect", lambda value: value["notices"].update(
        index_path="fixtures/synthetic/evidence/grant.txt"), "REJECT notice-index-path-invalid:")

    manifest_digest = sha256(original)
    fixture_id = "synthetic"
    notice_digest = record["notices"]["sha256"]
    prose_with_all_values = (
        f"fixture `{fixture_id}` manifest {manifest_digest} notice {notice_digest}"
    ).encode("ascii")
    if _notice_digest_table_matches(prose_with_all_values, fixture_id, manifest_digest, notice_digest):
        raise Reject("self-test-notice-prose", "a prose line containing all digests was accepted as a table row")
    cases.append("notice-prose-with-matching-digests")
    matching_notice_table = (
        "| Fixture directory | `manifest.json` SHA-256 | `LICENSE.txt` SHA-256 |\n"
        "| --- | --- | --- |\n"
        f"| `{fixture_id}` | `{manifest_digest}` | `{notice_digest}` |\n"
    )
    inactive_notice_tables = (
        ("notice-fenced-table-with-matching-digests", f"```markdown\n{matching_notice_table}```\n"),
        ("notice-html-comment-table-with-matching-digests", f"<!--\n{matching_notice_table}-->\n"),
    )
    for label, inactive in inactive_notice_tables:
        if _notice_digest_table_matches(inactive.encode("ascii"), fixture_id, manifest_digest, notice_digest):
            raise Reject("self-test-notice-inactive-markdown", f"{label} was accepted as an active digest table")
        cases.append(label)

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

        loose_fixture = root / "fixtures/payload.gb"
        loose_fixture.write_bytes(b"unadmitted loose synthetic payload\n")
        result = _run_repository_cli(root)
        if result.returncode == 0 or "REJECT fixture-admission-required:" not in result.stderr:
            raise Reject("self-test-loose-fixture", result.stderr.strip() or "direct child of fixtures/ was accepted")
        loose_fixture.unlink()

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
        return 5


def _fixture_entry_count(root: Path, relative: str) -> int:
    """Count a tree's descendant entries without materializing a directory listing."""
    pending = [root / relative]
    count = 0
    while pending:
        directory = pending.pop()
        try:
            with os.scandir(directory) as entries:
                for entry in entries:
                    count += 1
                    if entry.is_dir(follow_symlinks=False):
                        pending.append(Path(entry.path))
        except OSError as error:
            raise Reject("self-test-fixture-count-failed", f"{relative}: {error.strerror}") from None
    return count


class _FakeTreeStream:
    def __init__(self, data: bytes):
        self.data = data
        self.offset = 0
        self.bytes_read = 0
        self.closed = False
        self.eof_reads = 0

    def read(self, size: int = -1) -> bytes:
        if self.closed:
            raise ValueError("read from closed fake stream")
        if self.offset >= len(self.data):
            self.eof_reads += 1
            return b""
        if size < 0:
            size = len(self.data) - self.offset
        chunk = self.data[self.offset:self.offset + size]
        self.offset += len(chunk)
        self.bytes_read += len(chunk)
        return chunk

    def close(self) -> None:
        self.closed = True


class _FakeTreeProcess:
    def __init__(self, stdout_data: bytes, stderr_data: bytes):
        self.stdout = _FakeTreeStream(stdout_data)
        self.stderr = _FakeTreeStream(stderr_data)
        self.returncode = None
        self.terminated = False
        self.wait_calls = 0
        self.wait_after_terminate = 0
        self._finished = threading.Event()

    def poll(self):
        return self.returncode

    def terminate(self) -> None:
        self.terminated = True
        self.returncode = -15
        self._finished.set()

    def kill(self) -> None:
        self.returncode = -9
        self._finished.set()

    def wait(self, timeout: float | None = None) -> int:
        self.wait_calls += 1
        if self.terminated:
            self.wait_after_terminate += 1
        if self.returncode is not None:
            return self.returncode
        if self._finished.wait(timeout):
            return self.returncode
        raise subprocess.TimeoutExpired("git ls-tree", timeout)


def _fake_tree_process_lifecycle_control() -> bool:
    fake = _FakeTreeProcess(b"x" * 8192, b"e" * 8192)
    process_calls = 0
    created_threads = []
    original_popen = subprocess.Popen
    original_thread = threading.Thread
    original_limit = MAX_GIT_TREE_OUTPUT_BYTES

    def fake_popen(*_args, **_kwargs):
        nonlocal process_calls
        if _kwargs.get("bufsize") != 0:
            return original_popen(*_args, **_kwargs)
        process_calls += 1
        return fake

    def tracked_thread(*args, **kwargs):
        thread = original_thread(*args, **kwargs)
        created_threads.append(thread)
        return thread

    subprocess.Popen = fake_popen
    threading.Thread = tracked_thread
    globals()["MAX_GIT_TREE_OUTPUT_BYTES"] = 4
    try:
        try:
            tree_files(Path("."), BASELINE_COMMIT, "fixtures")
        except Reject as error:
            if error.code != "git-tree-output-limit":
                raise Reject("self-test-git-stream-lifecycle-reason", str(error)) from None
        else:
            return False
    finally:
        subprocess.Popen = original_popen
        threading.Thread = original_thread
        globals()["MAX_GIT_TREE_OUTPUT_BYTES"] = original_limit

    if process_calls == 0:
        return False
    if not fake.terminated or fake.wait_after_terminate == 0:
        raise Reject("self-test-git-stream-lifecycle", "overflow did not terminate and reap its child")
    if not fake.stdout.closed or not fake.stderr.closed:
        raise Reject("self-test-git-stream-lifecycle", "overflow did not close both child streams")
    if not created_threads or any(thread.is_alive() for thread in created_threads):
        raise Reject("self-test-git-stream-lifecycle", "overflow returned before its readers completed")
    if fake.stderr.bytes_read != len(fake.stderr.data):
        raise Reject("self-test-git-stream-lifecycle", "stderr reader did not drain the child's output")
    retained = bytearray()
    for offset in range(0, len(fake.stderr.data), 1024):
        _retain_stderr_tail(retained, fake.stderr.data[offset:offset + 1024])
        if len(retained) > MAX_GIT_TREE_STDERR_BYTES:
            raise Reject("self-test-git-stderr-limit", "stderr retention exceeded 4 KiB")
    if len(retained) != MAX_GIT_TREE_STDERR_BYTES or retained != fake.stderr.data[-MAX_GIT_TREE_STDERR_BYTES:]:
        raise Reject("self-test-git-stderr-limit", "stderr reader did not retain the bounded tail")
    return True


def _fake_blob_process_lifecycle_control() -> bool:
    fake = _FakeTreeProcess(b"x" * 8192, b"")
    process_calls = 0
    original_popen = subprocess.Popen
    original_limit = MAX_FILE_BYTES

    def fake_popen(*_args, **kwargs):
        nonlocal process_calls
        if kwargs.get("bufsize") != 0:
            return original_popen(*_args, **kwargs)
        process_calls += 1
        return fake

    subprocess.Popen = fake_popen
    globals()["MAX_FILE_BYTES"] = 4
    try:
        try:
            blob(Path("."), BASELINE_COMMIT, "fixtures/oversized.bin")
        except Reject as error:
            if error.code != "file-size-limit":
                raise Reject("self-test-git-blob-lifecycle-reason", str(error)) from None
        else:
            return False
    finally:
        subprocess.Popen = original_popen
        globals()["MAX_FILE_BYTES"] = original_limit

    if process_calls == 0:
        return False
    if fake.stdout.bytes_read != 5:
        raise Reject("self-test-git-blob-read-bound", f"overflow consumed {fake.stdout.bytes_read} bytes, expected 5")
    if not fake.terminated or fake.wait_after_terminate == 0 or fake.wait_calls == 0:
        raise Reject("self-test-git-blob-lifecycle", "overflow did not terminate and reap the git child")
    if not fake.stdout.closed:
        raise Reject("self-test-git-blob-lifecycle", "overflow did not close the git output stream")
    return True


def _fake_blob_read_deadline_control() -> bool:
    class StalledStream:
        def __init__(self, terminated: threading.Event):
            self.terminated = terminated
            self.read_started = threading.Event()
            self.released_by_termination = False
            self.closed = False

        def read(self, _size: int = -1) -> bytes:
            self.read_started.set()
            self.released_by_termination = self.terminated.wait(1)
            return b""

        def close(self) -> None:
            self.closed = True

    class StalledProcess:
        def __init__(self):
            self.terminated_event = threading.Event()
            self.stdout = StalledStream(self.terminated_event)
            self.returncode = None
            self.terminated = False
            self.wait_calls = 0
            self.wait_after_terminate = 0
            self.finished = threading.Event()

        def poll(self):
            return self.returncode

        def terminate(self) -> None:
            self.terminated = True
            self.returncode = -15
            self.terminated_event.set()
            self.finished.set()

        def kill(self) -> None:
            self.returncode = -9
            self.terminated_event.set()
            self.finished.set()

        def wait(self, timeout: float | None = None) -> int:
            self.wait_calls += 1
            if self.terminated:
                self.wait_after_terminate += 1
            if self.returncode is not None:
                return self.returncode
            if self.finished.wait(min(timeout or 0, 0.02)):
                return self.returncode
            raise subprocess.TimeoutExpired("git show", timeout)

    fake = StalledProcess()
    process_calls = 0
    created_threads = []
    original_popen = subprocess.Popen
    original_thread = threading.Thread
    original_timeout = GIT_BLOB_TIMEOUT_SECONDS

    def fake_popen(*_args, **kwargs):
        nonlocal process_calls
        if kwargs.get("bufsize") != 0:
            return original_popen(*_args, **kwargs)
        process_calls += 1
        return fake

    def tracked_thread(*args, **kwargs):
        thread = original_thread(*args, **kwargs)
        created_threads.append(thread)
        return thread

    subprocess.Popen = fake_popen
    threading.Thread = tracked_thread
    globals()["GIT_BLOB_TIMEOUT_SECONDS"] = 0.05
    started = time.monotonic()
    try:
        try:
            blob(Path("."), BASELINE_COMMIT, "fixtures/stalled.bin")
        except Reject as error:
            if error.code != "git-blob-timeout":
                raise Reject("self-test-git-blob-timeout-reason", str(error)) from None
        else:
            return False
    finally:
        subprocess.Popen = original_popen
        threading.Thread = original_thread
        globals()["GIT_BLOB_TIMEOUT_SECONDS"] = original_timeout

    if process_calls == 0 or time.monotonic() - started >= 0.5:
        raise Reject("self-test-git-blob-timeout", "stalled stream was not bounded by the read deadline")
    if not fake.stdout.read_started.is_set() or not fake.stdout.released_by_termination:
        raise Reject("self-test-git-blob-timeout", "terminating the child did not release its blocked stdout reader")
    if not fake.terminated or fake.wait_after_terminate == 0:
        raise Reject("self-test-git-blob-timeout", "timeout did not terminate and reap the git child")
    if not fake.stdout.closed or not created_threads or any(thread.is_alive() for thread in created_threads):
        raise Reject("self-test-git-blob-timeout", "timeout left the stdout stream or reader thread open")
    return True


def _fake_product_scandir_limit_control() -> bool:
    class FakeEntry:
        def __init__(self, path: str):
            self.path = path
            self.name = Path(path).name

        def stat(self, *, follow_symlinks: bool = True):
            return type("FakeStat", (), {"st_mode": stat.S_IFDIR | 0o755})()

        def is_dir(self, *, follow_symlinks: bool = True) -> bool:
            return True

        def is_symlink(self) -> bool:
            return False

    class FakeScandir:
        def __init__(self, directory: Path):
            self.directory = directory
            self.index = 0
            self.yielded = 0
            self.closed = False

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            self.closed = True

        def __iter__(self):
            return self

        def __next__(self):
            if self.index >= 100:
                raise StopIteration
            self.index += 1
            self.yielded += 1
            return FakeEntry(str(self.directory / f"child-{self.index}"))

    original_scandir = os.scandir
    original_limit = MAX_PRODUCT_ENTRIES
    scanners: list[FakeScandir] = []

    def fake_scandir(directory):
        scanner = FakeScandir(Path(directory))
        scanners.append(scanner)
        return scanner

    with tempfile.TemporaryDirectory(prefix="gbb-product-entry-limit-") as directory:
        tree = Path(directory) / "product"
        tree.mkdir()
        os.scandir = fake_scandir
        globals()["MAX_PRODUCT_ENTRIES"] = 1
        try:
            try:
                product_tree_entries(tree)
            except Reject as error:
                if error.code != "product-entry-count-limit":
                    raise Reject("self-test-product-entry-limit-reason", str(error)) from None
            else:
                return False
        finally:
            os.scandir = original_scandir
            globals()["MAX_PRODUCT_ENTRIES"] = original_limit

    if len(scanners) != 1 or scanners[0].yielded != 2 or not scanners[0].closed:
        raise Reject("self-test-product-entry-limit", "traversal retained or visited beyond the first over-limit entry")
    return True


def _run_bounded_input_controls() -> int:
    missing: list[str] = []
    project = Path(__file__).resolve().parents[2]

    with tempfile.TemporaryDirectory(prefix="gbb-fixture-entry-manifest-") as directory:
        root = Path(directory)
        _prepare_synthetic(root)
        initial_count = _fixture_entry_count(root, "fixtures/synthetic")
        (root / "fixtures/synthetic/empty-one/nested-empty").mkdir(parents=True)
        original_limit = MAX_FIXTURE_ENTRIES
        globals()["MAX_FIXTURE_ENTRIES"] = initial_count + 1
        try:
            try:
                check_manifest(root, "fixtures/synthetic/manifest.json")
            except Reject as error:
                if error.code != "fixture-entry-count-limit":
                    raise Reject("self-test-fixture-entry-count-reason", str(error)) from None
            else:
                missing.append("fixture-entry-count")
        finally:
            globals()["MAX_FIXTURE_ENTRIES"] = original_limit

    with tempfile.TemporaryDirectory(prefix="gbb-fixture-entry-repository-") as directory:
        root = Path(directory)
        _prepare_legacy_tree(root)
        initial_count = _fixture_entry_count(root, "fixtures")
        (root / "fixtures/tracer/empty-added-directory").mkdir()
        original_limit = MAX_FIXTURE_ENTRIES
        globals()["MAX_FIXTURE_ENTRIES"] = initial_count
        try:
            try:
                check_repository(root, BASELINE_COMMIT)
            except Reject as error:
                if error.code != "fixture-entry-count-limit":
                    raise Reject("self-test-repository-entry-count-reason", str(error)) from None
            else:
                missing.append("repository-entry-count")
        finally:
            globals()["MAX_FIXTURE_ENTRIES"] = original_limit

    original_bytes_limit = MAX_GIT_TREE_OUTPUT_BYTES
    globals()["MAX_GIT_TREE_OUTPUT_BYTES"] = 1
    try:
        try:
            tree_files(project, BASELINE_COMMIT, "fixtures")
        except Reject as error:
            if error.code != "git-tree-output-limit":
                raise Reject("self-test-git-tree-output-reason", str(error)) from None
        else:
            missing.append("git-tree-output")
    finally:
        globals()["MAX_GIT_TREE_OUTPUT_BYTES"] = original_bytes_limit

    original_records_limit = MAX_GIT_TREE_RECORDS
    globals()["MAX_GIT_TREE_RECORDS"] = 1
    try:
        try:
            tree_files(project, BASELINE_COMMIT, "fixtures")
        except Reject as error:
            if error.code != "git-tree-entry-count-limit":
                raise Reject("self-test-git-tree-entry-count-reason", str(error)) from None
        else:
            missing.append("git-tree-entry-count")
    finally:
        globals()["MAX_GIT_TREE_RECORDS"] = original_records_limit

    if not _fake_tree_process_lifecycle_control():
        missing.append("git-stream-lifecycle")
    if not _fake_blob_process_lifecycle_control():
        missing.append("git-blob-stream-lifecycle")
    if not _fake_blob_read_deadline_control():
        missing.append("git-blob-read-deadline")
    if not _fake_product_scandir_limit_control():
        missing.append("product-entry-scandir-limit")

    if missing:
        markers = {
            "fixture-entry-count": "self-test-fixture-entry-count-bypass",
            "repository-entry-count": "self-test-repository-entry-count-bypass",
            "git-tree-output": "self-test-git-tree-output-bypass",
            "git-tree-entry-count": "self-test-git-tree-entry-count-bypass",
            "git-stream-lifecycle": "self-test-git-stream-lifecycle-bypass",
            "git-blob-stream-lifecycle": "self-test-git-blob-stream-lifecycle-bypass",
            "git-blob-read-deadline": "self-test-git-blob-timeout-bypass",
            "product-entry-scandir-limit": "self-test-product-entry-scandir-limit-bypass",
        }
        first = missing[0]
        raise Reject(markers[first], f"over-limit control was accepted or its stream lifecycle was not enforced: {first}")
    return 8


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
    bounded_controls = _run_bounded_input_controls()
    print(f"PASS: fixture admission self-test positives=2 negative_controls="
          f"{manifest_controls + len(cases) + repository_controls + bounded_controls}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--self-test", action="store_true")
    modes.add_argument("--self-test-packages", action="store_true")
    modes.add_argument("--check-manifest")
    modes.add_argument("--check-repository", action="store_true")
    modes.add_argument("--check-product-tree", type=Path)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--baseline-object-root", type=Path,
                        help="optional trusted local Git object store for immutable baseline reads")
    parser.add_argument("--layout", choices=("core", "player"))
    parser.add_argument("--write-inventory", type=Path)
    parser.add_argument("--inventory", type=Path)
    parser.add_argument("--notice-sidecar", type=Path)
    args = parser.parse_args(argv)
    if args.write_inventory and args.inventory:
        parser.error("--write-inventory and --inventory are mutually exclusive")
    if (args.self_test_packages or args.check_product_tree) and not args.layout:
        parser.error("package checks require --layout core|player")
    if not (args.self_test_packages or args.check_product_tree) and any(
            (args.layout, args.write_inventory, args.inventory, args.notice_sidecar)):
        parser.error("--layout, inventory, and sidecar options require a product-tree mode")
    try:
        root = args.repo_root.resolve(strict=True)
        policy = parse_json((root / "cmake/FixtureAdmissionPolicy.json").read_bytes(), "FixtureAdmissionPolicy.json")
        if policy.get("schema_version") != 1 or policy.get("baseline_commit") != BASELINE_COMMIT:
            raise Reject("policy-invalid", "baseline commit differs from the reviewed full identity")
        if args.self_test:
            self_test()
        elif args.self_test_packages:
            self_test_packages(args.layout)
        elif args.check_manifest:
            result = check_manifest(root, args.check_manifest)
            print(f"PASS: fixture admission fixture={result['fixture']} pinned={result['pin']} files={result['files']}")
        elif args.check_product_tree:
            entries = product_tree_entries(args.check_product_tree)
            inventory = _read_inventory(args.inventory) if args.inventory else None
            accepted = check_product_entries(entries, args.layout, root, inventory=inventory,
                                             sidecar=_read_sidecar_argument(root, args.notice_sidecar))
            if args.write_inventory:
                _write_inventory(args.write_inventory, accepted, root)
            print(f"PASS: fixture admission product layout={args.layout} files={len(accepted['files'])} "
                  f"policy={accepted['policy_sha256']}")
        else:
            baseline = policy.get("baseline_commit")
            if not isinstance(baseline, str) or baseline != BASELINE_COMMIT:
                raise Reject("policy-invalid", "baseline_commit must be the reviewed full commit id")
            result = check_repository(root, baseline, args.baseline_object_root)
            print(f"PASS: fixture admission repository legacy_files={result['legacy_files']} "
                  f"admitted_changes={result['admitted_changes']} baseline={result['baseline']}")
        return 0
    except (Reject, OSError, subprocess.SubprocessError) as error:
        print(str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
