#!/usr/bin/env python3
"""Check and summarize the privacy-safe CGB corpus CI artifact allowlist."""

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCHEMA = "gabbaboy-cgb-corpus-public-artifacts-v1"
MAX_FILE_BYTES = 16 * 1024 * 1024
PUBLIC_FILES = (
    "cgb-corpus-receipt.json",
    "cgb-corpus-build-stamp.json",
    "cgb-corpus-run.json",
)
FILE_SCHEMAS = {
    "cgb-corpus-receipt.json": "gabbaboy-cgb-corpus-receipt-v1",
    "cgb-corpus-build-stamp.json": "gabbaboy-cgb-corpus-build-stamp-v1",
    "cgb-corpus-run.json": "gabbaboy-cgb-corpus-run-v1",
}
PRIVATE_PATTERNS = (
    re.compile(r"(?i)(?<![A-Za-z0-9])/(?:Users|home|private/var|var/folders)/[^\s\"'<>]+"),
    re.compile(r"(?i)(?<![A-Za-z0-9])[A-Z]:\\(?:Users|home)\\[^\s\"'<>]+"),
    re.compile(r"(?i)\b[A-Za-z0-9][A-Za-z0-9-]*\.(?:local|lan|internal)\b"),
)


class ArtifactError(Exception):
    pass


def bounded_read(path: Path) -> bytes:
    try:
        size = path.stat().st_size
    except OSError as exc:
        raise ArtifactError("artifact-file-unavailable") from exc
    if size > MAX_FILE_BYTES:
        raise ArtifactError("artifact-file-too-large")
    try:
        return path.read_bytes()
    except OSError as exc:
        raise ArtifactError("artifact-file-unavailable") from exc


def check_public_text(data: bytes, label: str) -> None:
    try:
        text = data.decode("utf-8", "strict")
    except UnicodeDecodeError as exc:
        raise ArtifactError(f"artifact-json-invalid:{label}") from exc
    for pattern in PRIVATE_PATTERNS:
        if pattern.search(text):
            raise ArtifactError(f"artifact-private-data:{label}")


def check_relative_paths(value, label: str) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if (key.endswith("_path") or key == "path") and isinstance(child, str) and child:
                normalized = child.replace("\\", "/")
                if normalized.startswith("/") or re.match(r"^[A-Za-z]:/", normalized):
                    raise ArtifactError(f"artifact-absolute-path:{label}")
            check_relative_paths(child, label)
    elif isinstance(value, list):
        for child in value:
            check_relative_paths(child, label)


def check_build_dir(build_dir: Path) -> tuple[list[dict], dict]:
    root = ROOT.resolve()
    resolved = build_dir.resolve()
    if resolved != root and root not in resolved.parents:
        raise ArtifactError("artifact-build-dir-outside-repository")
    rows = []
    for name in PUBLIC_FILES:
        path = resolved / name
        if path.is_symlink():
            raise ArtifactError(f"artifact-file-symlink:{name}")
        data = bounded_read(path)
        check_public_text(data, name)
        try:
            parsed = json.loads(data)
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise ArtifactError(f"artifact-json-invalid:{name}") from exc
        if type(parsed) is not dict:
            raise ArtifactError(f"artifact-json-invalid:{name}")
        if parsed.get("schema") != FILE_SCHEMAS[name]:
            raise ArtifactError(f"artifact-schema-invalid:{name}")
        check_relative_paths(parsed, name)
        rows.append({
            "path": path.relative_to(root).as_posix(),
            "size_bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
        })
    manifest = {"schema": SCHEMA, "artifacts": rows}
    manifest_bytes = (json.dumps(manifest, sort_keys=True, indent=2) + "\n").encode("utf-8")
    check_public_text(manifest_bytes, "manifest")
    return rows, manifest


def write_manifest(build_dir: Path, manifest: dict) -> Path:
    path = build_dir.resolve() / "cgb-corpus-public-artifacts.json"
    data = (json.dumps(manifest, sort_keys=True, indent=2) + "\n").encode("utf-8")
    check_public_text(data, "manifest")
    path.write_bytes(data)
    return path


def self_test() -> None:
    safe = b'{"path":"build/tests/runner","hostname":"redacted"}'
    check_public_text(safe, "safe-control")
    try:
        check_relative_paths({"junit_path": "/home/agent/work/cgb.xml"}, "absolute-path")
    except ArtifactError as exc:
        if str(exc) != "artifact-absolute-path:absolute-path":
            raise ArtifactError(f"self-test-wrong-diagnostic:{exc}") from exc
    else:
        raise ArtifactError("self-test-accepted-absolute-path")

    raw_reports = (
        b'<Site Hostname="runner-host.local"><FullCommandLine>/home/agent/work/build/runner</FullCommandLine></Site>',
        b'<testsuite hostname="runner-host.local"><system-out>/Users/example/work/src.c</system-out></testsuite>',
    )
    for index, report in enumerate(raw_reports):
        try:
            check_public_text(report, f"raw-report-{index}")
        except ArtifactError as exc:
            if str(exc) != f"artifact-private-data:raw-report-{index}":
                raise ArtifactError(f"self-test-wrong-diagnostic:{exc}") from exc
        else:
            raise ArtifactError(f"self-test-accepted-host-report:{index}")
    print("cgb-corpus-artifact-privacy self-test pass controls=absolute-path,raw-test-xml,raw-junit")


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true")
    group.add_argument("--self-test", action="store_true")
    parser.add_argument("--build-dir", type=Path, default=Path("build"))
    args = parser.parse_args()
    try:
        if args.self_test:
            self_test()
            return 0
        rows, manifest = check_build_dir(args.build_dir)
        manifest_path = write_manifest(args.build_dir, manifest)
        print("cgb-corpus-artifact-privacy pass files={} bytes={} manifest={}".format(
            len(rows), sum(row["size_bytes"] for row in rows),
            manifest_path.relative_to(ROOT.resolve()).as_posix()))
    except (ArtifactError, OSError) as exc:
        print(f"cgb-corpus-artifact-privacy mismatch: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
