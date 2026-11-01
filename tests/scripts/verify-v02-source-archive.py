#!/usr/bin/env python3
"""Verify GitHub-generated source archives separately from product packages.

Two contracts are checked here and they are deliberately not interchangeable:

* A *source archive* (`--archive`) is the exact-tag snapshot GitHub generates.
  It must retain every admitted licensed fixture together with its notice and
  must match the notice digest table byte for byte.
* A *product package* (`--check-product-archive`) is the installed core archive.
  It must match the shared exact core path and byte policy.

Both inspect archive bytes by streaming; nothing is ever extracted.  The Python
standard library is the only dependency.

Usage:
  verify-v02-source-archive.py --archive PATH --tag TAG --source-sha SHA
      --output PATH [--repo GIT_DIR]
  verify-v02-source-archive.py --check-receipt RECEIPT --archive PATH
      --tag TAG --source-sha SHA
  verify-v02-source-archive.py --check-product-archive PATH [--repo-root DIR]
      [--inventory PATH] [--notice-sidecar PATH] [--fixture-checker PATH]
  verify-v02-source-archive.py --self-test-product-tree DIR --repo-root DIR
  verify-v02-source-archive.py --self-test

Failures print `REJECT <code>: <reason>` on stderr and exit 1.
"""
import argparse
import gzip
import hashlib
import importlib.util
import io
import json
import os
import pathlib
import re
import stat
import subprocess
import sys
import tarfile
import tempfile
import zipfile
import zlib
import shutil

SCHEMA_VERSION = 1
RECEIPT_KIND = "gabbaboy-source-archive-receipt"
MAX_ENTRIES = 100000
MAX_TOTAL_BYTES = 1 << 30
MAX_MEMBER_BYTES = 64 << 20
MAX_PATH_BYTES = 4096
MAX_TAR_STREAM_BYTES = MAX_TOTAL_BYTES + (128 << 20)
MAX_TAR_EXTENSION_BYTES = 64 << 10
MAX_TAR_TOTAL_EXTENSION_BYTES = 4 << 20
MAX_TAR_EXTENSION_HEADERS = 128
MAX_TAR_TOTAL_EXTENSION_HEADERS = 32_768
MAX_TAR_READ_BYTES = 64 << 10
KEEP_LIMIT = 4 << 20
CHUNK = 1 << 20
ROM_SUFFIXES = (".gb", ".gbc", ".sgb", ".rom", ".bin")
DIGEST_DOCS = ("manifest.json", "SOURCES.md", "candidate-digests.json")
NOTICE_NAME = "THIRD_PARTY_NOTICES.md"
# Product paths and protected source bytes are governed by verify-fixture-admission.py.
TAG_RE = re.compile(r"^v([0-9]+\.[0-9]+\.[0-9]+)$")
SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
HEX64_RE = re.compile(r"(?<![0-9a-fA-F])[0-9a-f]{64}(?![0-9a-fA-F])")
TABLE_ROW_RE = re.compile(
    r"^\|\s*`([A-Za-z0-9._-]+)`\s*\|\s*`([0-9a-f]{64})`\s*\|\s*`([0-9a-f]{64})`\s*\|\s*$"
)


class Reject(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


class ArchiveLimitError(ValueError):
    def __init__(self, reason, message):
        super().__init__(message)
        self.reason = reason


class BoundedTarReader:
    """Count decompressed TAR bytes and reject unbounded or over-budget reads."""
    def __init__(self, source, limit, max_request):
        self.source = source
        self.limit = limit
        self.max_request = max_request
        self.bytes_read = 0

    def read(self, size=-1):
        if size is None or size < 0:
            raise ValueError("unbounded reads are not allowed from the TAR stream")
        if size == 0:
            return b""
        remaining = self.limit - self.bytes_read
        data = self.source.read(min(size, self.max_request, remaining + 1))
        if len(data) > remaining:
            raise ArchiveLimitError("stream", f"TAR exceeds {self.limit}-byte decompressed-stream limit")
        self.bytes_read += len(data)
        return data


def bounded_tarinfo_class(extension_headers=MAX_TAR_EXTENSION_HEADERS,
                          total_extension_headers=MAX_TAR_TOTAL_EXTENSION_HEADERS,
                          extension_bytes=MAX_TAR_EXTENSION_BYTES,
                          total_extension_bytes=MAX_TAR_TOTAL_EXTENSION_BYTES):
    """Check PAX and GNU extension declarations before tarfile consumes their payloads."""
    stats = {"chain_headers": 0, "total_headers": 0, "bytes": 0}
    extension_types = {
        tarfile.GNUTYPE_LONGNAME,
        tarfile.GNUTYPE_LONGLINK,
        tarfile.GNUTYPE_SPARSE,
        tarfile.XHDTYPE,
        tarfile.XGLTYPE,
        tarfile.SOLARIS_XHDTYPE,
    }

    class BoundedTarInfo(tarfile.TarInfo):
        def _proc_member(self, archive):
            if self.type in extension_types:
                if self.size < 0 or self.size > extension_bytes:
                    raise ArchiveLimitError("extension-header",
                                            f"extended TAR header exceeds {extension_bytes}-byte limit")
                if stats["chain_headers"] + 1 > extension_headers:
                    raise ArchiveLimitError("extension-count",
                                            f"TAR exceeds {extension_headers} extended-header limit")
                if stats["total_headers"] + 1 > total_extension_headers:
                    raise ArchiveLimitError("extension-total-count",
                                            f"TAR exceeds {total_extension_headers} archive-wide extended-header limit")
                if stats["bytes"] + self.size > total_extension_bytes:
                    raise ArchiveLimitError("extension-total",
                                            f"TAR exceeds {total_extension_bytes} aggregate extension-byte limit")
                stats["chain_headers"] += 1
                stats["total_headers"] += 1
                stats["bytes"] += self.size
            else:
                # A source member may legitimately need one PAX path header (for long
                # names); cap a hidden run per member, while keeping a separate archive total.
                stats["chain_headers"] = 0
            return super()._proc_member(archive)

    return BoundedTarInfo


class Limits:
    def __init__(self, entries=MAX_ENTRIES, total=MAX_TOTAL_BYTES, member=MAX_MEMBER_BYTES, path=MAX_PATH_BYTES):
        self.entries, self.total, self.member, self.path = entries, total, member, path


class Entry:
    def __init__(self, path, kind, size, target, sha256, git_oid, mode):
        self.path, self.kind, self.size, self.target = path, kind, size, target
        self.sha256, self.git_oid, self.mode = sha256, git_oid, mode


class Inspection:
    def __init__(self, unwrapped=False):
        # A source archive is wrapped in one <name>-<version>/ directory. The installed core package is
        # not: it is `tar -C <stage> include lib bin share`, so its members sit at the archive top level.
        self.unwrapped = unwrapped
        self.root = None
        self.entries = []
        self.directories = []
        self.kept = {}
        self.commit = None
        self.total = 0

    def files(self):
        return {e.path: e for e in self.entries if e.kind == "file"}


def split_path(raw):
    """Return the normalised component tuple or raise path-unsafe."""
    if "\x00" in raw or "\\" in raw:
        raise Reject("path-unsafe", f"archive path contains a NUL or backslash: {raw!r}")
    if raw.startswith("/") or re.match(r"^[A-Za-z]:", raw):
        raise Reject("path-unsafe", f"archive path is absolute: {raw!r}")
    parts = [p for p in raw.split("/") if p not in ("", ".")]
    if not parts or ".." in parts:
        raise Reject("path-unsafe", f"archive path is empty or traverses: {raw!r}")
    return tuple(parts)


def stream_hash(reader, declared, want_git):
    sha256 = hashlib.sha256()
    sha1 = hashlib.sha1(b"blob %d\x00" % declared) if want_git else None
    keep = io.BytesIO() if declared <= KEEP_LIMIT else None
    remaining = declared
    while remaining:
        chunk = reader.read(min(CHUNK, remaining))
        if not chunk:
            raise Reject("archive-unreadable", "archive member is shorter than its declared size")
        remaining -= len(chunk)
        sha256.update(chunk)
        if sha1:
            sha1.update(chunk)
        if keep is not None:
            keep.write(chunk)
    return sha256.hexdigest(), (sha1.hexdigest() if sha1 else None), (keep.getvalue() if keep is not None else None)


def open_kind(path):
    with open(path, "rb") as handle:
        magic = handle.read(4)
    if magic[:2] == b"\x1f\x8b":
        return "tar.gz"
    if magic[:2] == b"PK":
        return "zip"
    raise Reject("archive-unreadable", "archive is neither a gzip tarball nor a zip file")


def account(inspection, entry_count, size, limits):
    if entry_count > limits.entries:
        raise Reject("too-many-entries", f"archive has more than {limits.entries} entries")
    inspection.total += size
    if inspection.total > limits.total:
        raise Reject("archive-oversize", f"archive declares more than {limits.total} uncompressed bytes")


def register(inspection, seen, raw, kind, size, target, reader, mode, limits, want_git):
    parts = split_path(raw)
    if len(raw.encode("utf-8", "surrogatepass")) > limits.path:
        raise Reject("path-too-long", f"archive path exceeds {limits.path} bytes")
    if size > limits.member:
        raise Reject("member-oversize", f"member {raw!r} declares {size} bytes, over {limits.member}")
    if parts in seen:
        raise Reject("path-duplicate", f"archive contains a duplicate path: {raw!r}")
    seen.add(parts)
    if inspection.unwrapped:
        inspection.root = ""
        account(inspection, len(seen), size, limits)
        rel = "/".join(parts)
        if kind == "dir":
            inspection.directories.append(rel)
            return
    else:
        if inspection.root is None:
            inspection.root = parts[0]
        elif parts[0] != inspection.root:
            raise Reject("root-mismatch", "archive has more than one top-level entry")
        account(inspection, len(seen), size, limits)
        rel = "/".join(parts[1:])
        if kind == "dir":
            return
        if not rel:
            raise Reject("root-mismatch", "archive root is not a directory")
    if kind == "symlink":
        # Without a tagged tree to compare against, only a relative link that stays inside the
        # archive root is tolerated; with --repo the exact tree comparison decides.
        target_bytes = target.encode("utf-8", "surrogateescape")
        if not target_bytes or len(target_bytes) > limits.path:
            raise Reject("path-too-long", f"symbolic link target for {raw!r} is empty or exceeds {limits.path} bytes")
        if target.startswith("/") or "\x00" in target or "\\" in target or re.match(r"^[A-Za-z]:", target):
            raise Reject("link-not-allowed", f"symbolic link {raw!r} has an absolute or non-portable target")
        # `parts` includes the wrapped archive root for source archives, but no synthetic
        # root for product archives. Resolve from the link's parent within that boundary.
        depth = len(parts) - (1 if inspection.unwrapped else 2)
        for step in target.split("/"):
            if step == "..":
                depth -= 1
            elif step not in ("", "."):
                depth += 1
            if depth < 0:
                raise Reject("link-not-allowed", f"symbolic link {raw!r} points outside the archive root")
        inspection.total += len(target_bytes)
        if inspection.total > limits.total:
            raise Reject("archive-oversize", f"archive declares more than {limits.total} uncompressed bytes")
        oid = hashlib.sha1(b"blob %d\x00" % len(target_bytes) + target_bytes).hexdigest()
        inspection.entries.append(Entry(rel, "symlink", size, target, None, oid, mode))
        return
    sha256, oid, kept = stream_hash(reader, size, want_git)
    inspection.entries.append(Entry(rel, "file", size, None, sha256, oid, mode))
    if kept is not None and (rel == NOTICE_NAME or pathlib.PurePosixPath(rel).name in ("LICENSE.txt",) + DIGEST_DOCS):
        inspection.kept[rel] = kept


def inspect_tar(path, limits, want_git, unwrapped=False):
    inspection, seen = Inspection(unwrapped), set()
    try:
        with open(path, "rb") as compressed:
            with gzip.GzipFile(fileobj=compressed, mode="rb") as decompressed:
                bounded = BoundedTarReader(decompressed, MAX_TAR_STREAM_BYTES, MAX_TAR_READ_BYTES)
                with tarfile.open(
                        fileobj=bounded, mode="r|",
                        tarinfo=bounded_tarinfo_class(extension_headers=MAX_TAR_EXTENSION_HEADERS,
                                                      total_extension_headers=MAX_TAR_TOTAL_EXTENSION_HEADERS,
                                                      extension_bytes=MAX_TAR_EXTENSION_BYTES,
                                                      total_extension_bytes=MAX_TAR_TOTAL_EXTENSION_BYTES)) as bundle:
                    for member in bundle:
                        if member.issparse() or member.islnk():
                            raise Reject("link-not-allowed" if member.islnk() else "nonregular-member",
                                         f"archive member is a hard link or sparse file: {member.name!r}")
                        if member.isdir():
                            kind, target, reader = "dir", None, None
                        elif member.issym():
                            kind, target, reader = "symlink", member.linkname, None
                        elif member.isreg():
                            kind, target, reader = "file", None, bundle.extractfile(member)
                        else:
                            raise Reject("nonregular-member", f"archive member is a device, FIFO or special file: {member.name!r}")
                        register(inspection, seen, member.name, kind, member.size if kind == "file" else 0,
                                 target, reader, member.mode, limits, want_git)
                    while bounded.read(MAX_TAR_READ_BYTES):
                        pass
                    inspection.commit = bundle.pax_headers.get("comment")
    except Reject:
        raise
    except ArchiveLimitError as error:
        code = {
            "extension-header": "archive-extension-header-limit",
            "extension-total": "archive-extension-total-limit",
            "extension-count": "archive-extension-count-limit",
            "extension-total-count": "archive-extension-total-count-limit",
            "stream": "archive-stream-limit",
        }[error.reason]
        raise Reject(code, str(error)) from None
    except ValueError as error:
        raise Reject("archive-unreadable", f"archive cannot be read as a bounded gzip tarball: {error}") from None
    except (tarfile.TarError, EOFError, zlib.error, OSError) as error:
        raise Reject("archive-unreadable", f"archive cannot be read as a gzip tarball: {error}")
    return inspection


def inspect_zip(path, limits, want_git, unwrapped=False):
    inspection, seen = Inspection(unwrapped), set()
    try:
        with zipfile.ZipFile(path) as bundle:
            infos = bundle.infolist()
            if len(infos) > limits.entries:
                raise Reject("too-many-entries", f"archive has more than {limits.entries} entries")
            for info in infos:
                mode = info.external_attr >> 16
                if info.is_dir():
                    kind, target, size = "dir", None, 0
                elif stat.S_ISLNK(mode):
                    if info.file_size > limits.member:
                        raise Reject("member-oversize", f"member {info.filename!r} is over {limits.member}")
                    kind, target, size = "symlink", bundle.read(info).decode("utf-8", "replace"), 0
                elif mode and not stat.S_ISREG(mode):
                    raise Reject("nonregular-member", f"archive member is special: {info.filename!r}")
                else:
                    kind, target, size = "file", None, info.file_size
                if kind == "file" and size <= limits.member:
                    with bundle.open(info) as reader:
                        register(inspection, seen, info.filename, kind, size, target, reader, mode & 0o777, limits, want_git)
                        if reader.read(1):
                            raise Reject("member-oversize", f"member {info.filename!r} exceeds its declared size")
                else:
                    register(inspection, seen, info.filename, kind, size, target, None, mode & 0o777, limits, want_git)
            inspection.commit = bundle.comment.decode("ascii", "replace").strip() or None
    except Reject:
        raise
    except (zipfile.BadZipFile, EOFError, zlib.error, OSError, NotImplementedError) as error:
        raise Reject("archive-unreadable", f"archive cannot be read as a zip file: {error}")
    return inspection


def inspect_archive(path, limits, want_git=False, unwrapped=False):
    try:
        if os.path.getsize(path) > limits.total:
            raise Reject("archive-oversize", "archive file is larger than the uncompressed-size limit")
        kind = open_kind(path)
    except OSError as error:
        raise Reject("archive-unreadable", f"archive cannot be opened: {error.strerror or error}")
    inspection = (inspect_tar if kind == "tar.gz" else inspect_zip)(path, limits, want_git, unwrapped)
    if inspection.root is None:
        raise Reject("archive-unreadable", "archive has no entries")
    return inspection


def sha256_path(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(CHUNK), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git(repo, *args):
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    result = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, env=env, check=False)
    if result.returncode != 0:
        raise Reject("tag-source-mismatch", f"git {' '.join(args[:2])} failed: {result.stderr.decode('utf-8', 'replace').strip()}")
    return result.stdout


def check_identity(inspection, tag, source_sha):
    match = TAG_RE.match(tag)
    if not match:
        raise Reject("tag-invalid", f"tag {tag!r} is not v<major>.<minor>.<patch>")
    if not SHA1_RE.match(source_sha):
        raise Reject("tag-source-mismatch", "source SHA must be a lowercase full 40-character commit ID")
    version = match.group(1)
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*-" + re.escape(version), inspection.root):
        raise Reject("root-mismatch", f"archive root {inspection.root!r} is not <name>-{version}")
    if not inspection.commit:
        raise Reject("tag-source-mismatch", "archive carries no embedded commit ID, so it cannot be bound to the tag")
    if inspection.commit != source_sha:
        raise Reject("tag-source-mismatch", f"archive embeds commit {inspection.commit}, expected {source_sha}")


def check_tree(inspection, repo, tag, source_sha):
    resolved = git(repo, "rev-parse", "--verify", "--quiet", f"refs/tags/{tag}^{{commit}}").decode().strip()
    if resolved != source_sha:
        raise Reject("tag-source-mismatch", f"tag {tag} resolves to {resolved}, expected {source_sha}")
    expected = {}
    for record in git(repo, "ls-tree", "-r", "-z", "--full-tree", source_sha).split(b"\x00"):
        if not record:
            continue
        meta, name = record.split(b"\t", 1)
        mode, kind, oid = meta.decode().split(" ")
        if kind == "commit":
            continue  # git archive writes a submodule as an empty directory
        expected[name.decode("utf-8", "surrogateescape")] = (mode, oid)
    actual = {e.path: e for e in inspection.entries}
    missing = sorted(set(expected) - set(actual))
    extra = sorted(set(actual) - set(expected))
    if missing or extra:
        raise Reject("tree-mismatch", f"archive differs from tagged tree: missing {missing[:3]} extra {extra[:3]}")
    for name, (mode, oid) in expected.items():
        entry = actual[name]
        actual_mode = ("120000" if entry.kind == "symlink" else
                       ("100755" if entry.mode & 0o111 else "100644"))
        if mode != actual_mode or entry.git_oid != oid:
            raise Reject("tree-mismatch", f"{name} differs from the tagged tree mode or blob")


def parse_notice_table(text):
    rows = {}
    for line in text.splitlines():
        found = TABLE_ROW_RE.match(line)
        if found:
            if found.group(1) in rows:
                raise Reject("missing-notice", f"notice digest table lists {found.group(1)} twice")
            rows[found.group(1)] = (found.group(2), found.group(3))
    return rows


def check_fixtures(inspection):
    files = inspection.files()
    notices = inspection.kept.get(NOTICE_NAME)
    if notices is None:
        raise Reject("missing-notice", f"{NOTICE_NAME} is missing from the source archive")
    table = parse_notice_table(notices.decode("utf-8", "replace"))
    if not table:
        raise Reject("missing-notice", f"{NOTICE_NAME} carries no manifest and notice digest table")
    present = {}
    for path in files:
        parts = path.split("/")
        if parts[0] == "fixtures":
            if len(parts) < 3:
                raise Reject("fixture-unadmitted", f"loose file directly under fixtures/: {path}")
            present.setdefault(parts[1], []).append(path)
    for name in sorted(table):
        if name not in present:
            raise Reject("fixture-missing", f"admitted fixture {name} is absent from the source archive")
    for name in sorted(table):
        if f"fixtures/{name}/LICENSE.txt" not in files:
            raise Reject("missing-notice", f"fixture {name} has no LICENSE.txt notice")
        manifest = files.get(f"fixtures/{name}/manifest.json")
        if manifest is None:
            raise Reject("fixture-missing", f"fixture {name} has no manifest.json")
        license_entry = files[f"fixtures/{name}/LICENSE.txt"]
        if (manifest.sha256, license_entry.sha256) != table[name]:
            raise Reject("fixture-digest-mismatch", f"fixture {name} manifest or notice differs from the notice digest table")
    for name in sorted(present):
        if name not in table:
            raise Reject("fixture-unadmitted", f"fixture directory {name} is not admitted by {NOTICE_NAME}")
    authorised = {name: set() for name in table}
    for name in table:
        for doc in DIGEST_DOCS:
            data = inspection.kept.get(f"fixtures/{name}/{doc}")
            if data is not None:
                authorised[name].update(HEX64_RE.findall(data.decode("utf-8", "replace")))
    for path, entry in sorted(files.items()):
        if not path.lower().endswith(ROM_SUFFIXES):
            continue
        parts = path.split("/")
        if parts[0] != "fixtures" or parts[1] not in table or entry.sha256 not in authorised[parts[1]]:
            raise Reject("unexpected-rom", f"ROM-like file {path} is not declared by an admitted fixture manifest")
    return table, files, notices


def tree_digest(inspection):
    digest = hashlib.sha256(b"gabbaboy-source-tree-v2\x00")
    entries = sorted(inspection.entries, key=lambda e: e.path.encode("utf-8", "surrogateescape"))
    for entry in entries:
        path = entry.path.encode("utf-8", "surrogateescape")
        if entry.kind == "symlink":
            kind, mode = b"symlink", b"120000"
            payload = entry.target.encode("utf-8", "surrogateescape")
        else:
            kind = b"file"
            mode = b"100755" if entry.mode & 0o111 else b"100644"
            payload = bytes.fromhex(entry.sha256)
        for field in (path, kind, mode, payload):
            digest.update(len(field).to_bytes(8, "big"))
            digest.update(field)
    return digest.hexdigest()


def build_receipt(archive, tag, source_sha, repo, limits):
    inspection = inspect_archive(archive, limits, want_git=repo is not None)
    check_identity(inspection, tag, source_sha)
    if repo is not None:
        check_tree(inspection, repo, tag, source_sha)
    table, files, notices = check_fixtures(inspection)
    identities = []
    for name in sorted(table):
        roms = sorted(p for p in files if p.startswith(f"fixtures/{name}/") and p.lower().endswith(ROM_SUFFIXES))
        identities.append({
            "fixture": name,
            "manifest_sha256": table[name][0],
            "license_sha256": table[name][1],
            "rom_count": len(roms),
        })
    return {
        "schema_version": SCHEMA_VERSION,
        "kind": RECEIPT_KIND,
        "archive_sha256": sha256_path(archive),
        "tag": tag,
        "source_sha": source_sha,
        "archive_root": inspection.root,
        "source_tree_sha256": tree_digest(inspection),
        "tree_bound_to_git": repo is not None,
        "admitted_fixture_identities": identities,
        "notice_sha256": hashlib.sha256(notices).hexdigest(),
        "inspected_members": len(inspection.entries),
    }


def check_receipt(receipt_path, archive, tag, source_sha, repo, limits):
    if not repo:
        raise Reject("receipt-unbound", "receipt qualification requires --repo for an independent Git-tree check")
    try:
        if os.path.getsize(receipt_path) > KEEP_LIMIT:
            raise ValueError("receipt is too large")
        receipt = json.loads(pathlib.Path(receipt_path).read_text())
    except (OSError, ValueError) as error:
        raise Reject("receipt-invalid", f"source archive receipt cannot be read: {error}")
    if not isinstance(receipt, dict) or receipt.get("kind") != RECEIPT_KIND or receipt.get("schema_version") != SCHEMA_VERSION:
        raise Reject("receipt-invalid", "receipt is not a version 1 source archive receipt (a source or build receipt cannot stand in)")
    if receipt.get("tag") != tag or receipt.get("source_sha") != source_sha:
        raise Reject("receipt-invalid", "receipt tag or source SHA differs from the frozen release identity")
    if receipt.get("tree_bound_to_git") is not True:
        raise Reject("receipt-unbound", "receipt was not produced with a Git-tree binding")
    for field in ("archive_sha256", "source_tree_sha256", "notice_sha256"):
        if not isinstance(receipt.get(field), str) or not SHA256_RE.match(receipt[field]):
            raise Reject("receipt-invalid", f"receipt {field} is missing or malformed")
    if not receipt.get("admitted_fixture_identities") or not isinstance(receipt.get("inspected_members"), int) or receipt["inspected_members"] <= 0:
        raise Reject("receipt-invalid", "receipt carries no admitted fixture identities or inspected members")
    # The archive byte digest is retained as download provenance. Re-encoded gzip
    # archives may have different bytes while representing the same qualified tree.
    fresh = build_receipt(archive, tag, source_sha, repo, limits)
    for field in ("source_tree_sha256", "notice_sha256", "archive_root",
                  "admitted_fixture_identities", "inspected_members"):
        if receipt.get(field) != fresh[field]:
            raise Reject("receipt-invalid", f"receipt {field} does not match the independently qualified source tree")
    return receipt


_PRODUCT_POLICY_MODULES = {}


def _shared_policy_checker(checker_path=None):
    path = (pathlib.Path(checker_path).resolve() if checker_path else
            pathlib.Path(__file__).resolve().with_name("verify-fixture-admission.py"))
    key = str(path)
    if key in _PRODUCT_POLICY_MODULES:
        return _PRODUCT_POLICY_MODULES[key]
    spec = importlib.util.spec_from_file_location("gbb_fixture_admission_product", path)
    if spec is None or spec.loader is None:
        raise Reject("product-policy-unavailable", "shared fixture admission checker cannot be loaded")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _PRODUCT_POLICY_MODULES[key] = module
    return module


def check_product(archive, repo_root, limits, inventory_path=None, sidecar_path=None, fixture_checker=None):
    inspection = inspect_archive(archive, limits, unwrapped=True)
    if any(e.kind == "symlink" for e in inspection.entries):
        raise Reject("product-link-not-allowed", "product package contains a link")
    checker = _shared_policy_checker(fixture_checker)
    if repo_root is None:
        repo_root = pathlib.Path(__file__).resolve().parents[2]
    root = pathlib.Path(repo_root).resolve()
    if sidecar_path is not None and pathlib.Path(sidecar_path).name != "gabbaboy-notices.txt":
        raise Reject("product-notice-sidecar-invalid", "sidecar must use the gabbaboy-notices.txt release asset name")
    entries = {
        entry.path: {"kind": "file", "size_bytes": entry.size, "sha256": entry.sha256}
        for entry in inspection.entries
    }
    entries.update({path: {"kind": "directory"} for path in inspection.directories})
    try:
        inventory = checker._read_inventory(pathlib.Path(inventory_path)) if inventory_path else None
        accepted = checker.check_product_entries(entries, "core", root, inventory=inventory, sidecar=sidecar_path)
    except checker.Reject as rejection:
        detail = str(rejection).partition(": ")[2] or str(rejection)
        raise Reject(rejection.code, detail) from None
    return {"inspected_members": len(inspection.entries) + len(inspection.directories),
            "root": inspection.root, "inventory": accepted}


# --------------------------------------------------------------------------- self-test


def tar_bytes(members, commit, root="gabbaboy-0.0.1", fmt=tarfile.PAX_FORMAT, extra_pax=None):
    """Build a gzip tarball from {relative path: bytes | ('symlink', target) | ...} like GitHub does."""
    raw = io.BytesIO()
    headers = {"comment": commit} if commit else {}
    with tarfile.open(fileobj=raw, mode="w", format=fmt, pax_headers=headers) as bundle:
        if root is not None:
            top = tarfile.TarInfo(root)
            top.type = tarfile.DIRTYPE
            top.mode = 0o755
            bundle.addfile(top)
        for name, value in members.items():
            # A leading "@" supplies the raw member name (traversal, absolute and second-root controls).
            # root=None builds the installed product layout, whose members sit at the archive top level.
            info = tarfile.TarInfo(name[1:] if name.startswith("@") else (name if root is None else f"{root}/{name}"))
            if extra_pax and name in extra_pax:
                info.pax_headers = extra_pax[name]
            if isinstance(value, tuple) and value[0] == "file":
                info.size = len(value[1])
                info.mode = value[2]
                bundle.addfile(info, io.BytesIO(value[1]))
            elif isinstance(value, tuple) and value[0] == "dir":
                info.type = tarfile.DIRTYPE
                info.mode = 0o755
                bundle.addfile(info)
            elif isinstance(value, tuple):
                info.type = {"symlink": tarfile.SYMTYPE, "hardlink": tarfile.LNKTYPE, "device": tarfile.CHRTYPE}[value[0]]
                info.linkname = value[1]
                bundle.addfile(info)
            else:
                info.size = len(value)
                info.mode = 0o644
                bundle.addfile(info, io.BytesIO(value))
    compressed = io.BytesIO()
    with gzip.GzipFile(fileobj=compressed, mode="wb", mtime=0) as handle:
        handle.write(raw.getvalue())
    return compressed.getvalue()


def pax_record(key, value):
    body = key.encode("ascii") + b"=" + value + b"\n"
    length = len(body) + 2
    while True:
        record = str(length).encode("ascii") + b" " + body
        if len(record) == length:
            return record
        length = len(record)


def chained_pax_tar_bytes(count, record):
    raw = io.BytesIO()
    with tarfile.open(fileobj=raw, mode="w", format=tarfile.PAX_FORMAT) as bundle:
        top = tarfile.TarInfo("gabbaboy-0.0.1")
        top.type = tarfile.DIRTYPE
        bundle.addfile(top)
        for index in range(count):
            extension = tarfile.TarInfo(f"./PaxHeaders/{index}")
            extension.type = tarfile.XHDTYPE
            extension.size = len(record)
            bundle.addfile(extension, io.BytesIO(record))
        payload = tarfile.TarInfo("gabbaboy-0.0.1/README.md")
        payload.size = 1
        bundle.addfile(payload, io.BytesIO(b"x"))
    return gzip.compress(raw.getvalue(), mtime=0)


def _load_product_policy_module():
    return _shared_policy_checker()


def _private_baseline_repo(scratch, checker):
    """Materialize a private working tree backed by only the immutable product baseline."""
    project_root = pathlib.Path(__file__).resolve().parents[2]
    repo = pathlib.Path(scratch) / "synthetic-policy-repository"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", str(repo)], check=True, capture_output=True)
    object_dir = subprocess.run(
        ["git", "-C", str(project_root), "rev-parse", "--path-format=absolute", "--git-path", "objects"],
        check=True, capture_output=True).stdout.rstrip(b"\r\n")
    object_info = repo / ".git/objects/info"
    object_info.mkdir(parents=True, exist_ok=True)
    (object_info / "alternates").write_bytes(object_dir + b"\n")

    paths = ["LICENSE", "THIRD_PARTY_NOTICES.md", "cmake/FixtureAdmissionPolicy.json"]
    raw_tree = checker.git(repo, "ls-tree", "-r", "-z", "--full-tree", checker.BASELINE_COMMIT, "--", "fixtures")
    for record in raw_tree.split(b"\0"):
        if not record:
            continue
        _metadata, raw_path = record.split(b"\t", 1)
        paths.append(raw_path.decode("utf-8", "surrogateescape"))
    for relative in paths:
        target = repo.joinpath(*relative.split("/"))
        target.parent.mkdir(parents=True, exist_ok=True)
        data = (project_root / relative).read_bytes() if relative == "cmake/FixtureAdmissionPolicy.json" \
            else checker.blob(repo, checker.BASELINE_COMMIT, relative)
        target.write_bytes(data)
    return repo


def _synthetic_core_product(scratch):
    checker = _load_product_policy_module()
    repo = _private_baseline_repo(scratch, checker)
    rules, _policy_bytes = checker._product_rules(repo)
    source_contract = checker._product_source_expectations(repo, rules, "core")
    tree = pathlib.Path(scratch) / "synthetic-core-product"
    tree.mkdir()
    checker._write_synthetic_product_tree(tree, repo, "core", rules, b"", source_contract)
    entries = checker.product_tree_entries(tree)
    product = {}
    for relative, record in entries.items():
        if record["kind"] == "directory":
            product[relative] = ("dir",)
        else:
            product[relative] = tree.joinpath(*relative.split("/")).read_bytes()
    inventory = checker.check_product_entries(entries, "core", repo)
    forbidden_source = "fixtures/mooneye-cgb/boot_regs-cgb.gb"
    forbidden_bytes = checker.blob(repo, checker.BASELINE_COMMIT, forbidden_source)
    return checker, repo, product, inventory, forbidden_bytes, rules, source_contract


def check_product_notice_contract(content):
    try:
        text = content.decode("utf-8", "strict") if isinstance(content, bytes) else content
    except UnicodeDecodeError:
        raise Reject("notice-contract-invalid", "THIRD_PARTY_NOTICES.md is not UTF-8") from None
    paragraphs = [paragraph.strip() for paragraph in text.split("\n\n") if paragraph.strip()]
    claims = [paragraph for paragraph in paragraphs
              if "installed core packages" in paragraph.lower() and "binary products" in paragraph.lower()]
    if len(claims) != 1:
        raise Reject("notice-contract-invalid", "expected one explicit installed-product fixture claim")
    claim = " ".join(claims[0].split()).lower()
    required = ("exactly the original project-authored tracer, visible demo, and mbc1 continuation fixtures",
                "their pinned notices", "controlled game and diagnostic bytes", "excluded from binary products",
                "do not decide whether a grant's author had authority")
    if any(phrase not in claim for phrase in required) or "fixture-free" in claim:
        raise Reject("notice-contract-invalid", "product claim does not describe the exact fixtures, notices, exclusions, and review boundary")


def self_test_product_tree(tree_path, repo_root):
    """Run the shared product-entry checker against private mutations of a real staged tree."""
    checker = _shared_policy_checker()
    root = pathlib.Path(repo_root).resolve()
    tree = pathlib.Path(tree_path).resolve(strict=True)
    rules, _policy_bytes = checker._product_rules(root)
    source_contract = checker._product_source_expectations(root, rules, "core")
    clean_entries = checker.product_tree_entries(tree)
    inventory = checker.check_product_entries(clean_entries, "core", root)

    # Reuse the just-validated immutable baseline expectations across isolated controls. The
    # public API name remains the call under test; only its deterministic baseline setup is held.
    def check_cached(entries, layout, repo_root, inventory=None, sidecar=None):
        return checker._validate_product_entries(
            entries, layout, repo_root, inventory=inventory, sidecar=sidecar,
            rules_override=rules, source_contract=source_contract)

    checker.check_product_entries = check_cached
    positives = 1
    negatives = 0
    print("accepted: actual extracted core product tree")

    def reject_mutation(label, mutate, expected_code):
        nonlocal negatives
        with tempfile.TemporaryDirectory(prefix=f"gbb-real-core-{label}-") as directory:
            candidate = pathlib.Path(directory) / "installed-prefix"
            shutil.copytree(tree, candidate, symlinks=True)
            mutate(candidate)
            entries = checker.product_tree_entries(candidate)
            try:
                checker.check_product_entries(entries, "core", root, inventory=inventory)
            except checker.Reject as error:
                if error.code != expected_code:
                    raise Reject("self-test-real-product", f"{label}: expected {expected_code}, got {error.code}") from None
            else:
                raise Reject("self-test-real-product", f"{label}: mutation was accepted")
        negatives += 1
        print(f"rejected: extracted product {label} ({expected_code})")

    forbidden_bytes = (root / "fixtures/mooneye-cgb/boot_regs-cgb.gb").read_bytes()
    fixture_dirs = ("tracer", "visible-demo", "mbc1-continuation")
    for fixture_dir in fixture_dirs:
        prefix = pathlib.Path("share/gabbaboy/fixtures") / fixture_dir
        reject_mutation(f"extra-{fixture_dir}",
                        lambda candidate, prefix=prefix: (candidate / prefix / "unregistered.bin").write_bytes(b"extra"),
                        "product-path-unknown")
        for disguise in ("renamed-payload.bin", "suffixless"):
            reject_mutation(f"known-forbidden-{fixture_dir}-{disguise}",
                            lambda candidate, prefix=prefix, disguise=disguise:
                            (candidate / prefix / disguise).write_bytes(forbidden_bytes),
                            "product-fixture-leak")
    for disguise in ("renamed-payload.bin", "suffixless"):
        reject_mutation(f"known-forbidden-outside-{disguise}",
                        lambda candidate, disguise=disguise:
                        (candidate / "share/gabbaboy" / disguise).write_bytes(forbidden_bytes),
                        "product-fixture-leak")

    fixture_sources = [(source, record) for source, record in rules["files"].items()
                       if source.startswith("fixtures/") and record["destinations"].get("core")]
    for index, (source, record) in enumerate(fixture_sources):
        for destination in record["destinations"]["core"]:
            if source.endswith("LICENSE.txt"):
                reject_mutation(f"missing-fixture-notice-{index}",
                                lambda candidate, destination=destination: (candidate / destination).unlink(),
                                "product-path-missing")
                reject_mutation(f"changed-fixture-notice-{index}",
                                lambda candidate, destination=destination:
                                (candidate / destination).write_bytes((candidate / destination).read_bytes() + b"changed"),
                                "product-identity-mismatch")
            elif source.endswith((".gb", ".gbc", ".sgb", ".rom", ".bin", ".asm")) or source.endswith("manifest.json"):
                reject_mutation(f"changed-fixture-identity-{index}",
                                lambda candidate, destination=destination:
                                (candidate / destination).write_bytes((candidate / destination).read_bytes() + b"changed"),
                                "product-identity-mismatch")
    root_mit = "share/gabbaboy/LICENSE.txt"
    reject_mutation("missing-root-mit", lambda candidate: (candidate / root_mit).unlink(), "product-path-missing")
    reject_mutation("changed-root-mit", lambda candidate:
                    (candidate / root_mit).write_bytes((candidate / root_mit).read_bytes() + b"changed"),
                    "product-identity-mismatch")
    print(f"PASS: actual extracted core product controls positives={positives} negative_controls={negatives}")
    return negatives


def synthetic_tree():
    files = {
        "README.md": b"synthetic original tree\n",
        "src/a.c": b"int a(void) { return 1; }\n",
        "src/nested/link": ("symlink", "../../README.md"),
    }
    rows = []
    for name, rom in (("alpha", b"\x00ALPHA-ROM\x01"), ("beta", b"\x00BETA-ROM\x02")):
        rom_sha = hashlib.sha256(rom).hexdigest()
        manifest = json.dumps({"id": name, "rom": f"{name}.gb", "sha256": rom_sha}, indent=2).encode() + b"\n"
        notice = f"{name} fixture, original synthetic MIT notice\n".encode()
        files[f"fixtures/{name}/manifest.json"] = manifest
        files[f"fixtures/{name}/LICENSE.txt"] = notice
        files[f"fixtures/{name}/{name}.gb"] = rom
        rows.append((name, hashlib.sha256(manifest).hexdigest(), hashlib.sha256(notice).hexdigest()))
    nested = b"\x00NESTED\x03"
    files["fixtures/beta/sub/nested.gb"] = nested
    files["fixtures/beta/SOURCES.md"] = f"nested ROM {hashlib.sha256(nested).hexdigest()}\n".encode()
    table = "\n".join(f"| `{n}` | `{m}` | `{l}` |" for n, m, l in rows)
    files[NOTICE_NAME] = ("# Third-party notices\n\n### Manifest and notice digests\n\n"
                          "| Fixture directory | `manifest.json` SHA-256 | `LICENSE.txt` SHA-256 |\n|---|---|---|\n" + table + "\n").encode()
    return files


def private_git(*args, cwd, input_bytes=None):
    env = {"PATH": os.environ.get("PATH", ""), "HOME": str(cwd), "GIT_CONFIG_GLOBAL": os.devnull,
           "GIT_CONFIG_SYSTEM": os.devnull, "GIT_AUTHOR_NAME": "selftest", "GIT_AUTHOR_EMAIL": "selftest@example.invalid",
           "GIT_COMMITTER_NAME": "selftest", "GIT_COMMITTER_EMAIL": "selftest@example.invalid"}
    result = subprocess.run(["git", *args], cwd=cwd, capture_output=True, env=env, input=input_bytes, check=False)
    if result.returncode != 0:
        raise SystemExit(f"self-test git {' '.join(args)} failed: {result.stderr.decode()}")
    return result.stdout


def run_cli(script, *args):
    result = subprocess.run([sys.executable, "-I", str(script), *args], capture_output=True, text=True, check=False)
    return result.returncode, result.stderr, result.stdout


# --------------------------------------------------------------------------- notice attribute scope

# Digest-bound notice text must keep LF endings on every checkout, but the rule must name only the paths the
# notice table admits: the root LICENSE, the root notice file and each admitted fixture's LICENSE.txt. A
# basename wildcard such as `LICENSE*` also rewrites unrelated files at any depth, which changes bytes that no
# digest covers.
UNRELATED_PATHS = ("LICENSE.bin", "NOTICE", "docs/NOTICE.bin", "vendor/LICENSE-APACHE", "THIRD_PARTY_blob.bin")
EOL_LINE_RE = re.compile(r"^i/(\S+)\s+w/(\S+)\s+attr/(.*?)\s*\t(.+)$")


def attribute_scope_problems(attributes_text, fixture_names):
    """Add CRLF files to a scratch repository under the given .gitattributes and report what the index did."""
    pinned = ["LICENSE", NOTICE_NAME] + [f"fixtures/{name}/LICENSE.txt" for name in fixture_names]
    env = {**os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}
    problems = []
    with tempfile.TemporaryDirectory(prefix="gabbaboy-attributes-") as name:
        repo = pathlib.Path(name)

        def git(*args):
            return subprocess.run(["git", "-c", "core.autocrlf=false", "-c", "core.safecrlf=false", *args],
                                  cwd=repo, env=env, capture_output=True, text=True, check=False)

        if git("init", "-q").returncode != 0:
            raise SystemExit("self-test: could not create the scratch attribute repository")
        (repo / ".gitattributes").write_bytes(attributes_text.encode("utf-8"))
        for rel in pinned + list(UNRELATED_PATHS):
            target = repo / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(b"line one\r\nline two\r\n")
        if git("add", "--", *pinned, *UNRELATED_PATHS).returncode != 0:
            raise SystemExit("self-test: could not stage the scratch attribute files")
        listing = git("ls-files", "--eol", "--", *pinned, *UNRELATED_PATHS).stdout
        index_eol = {}
        for line in listing.splitlines():
            found = EOL_LINE_RE.match(line)
            if found:
                index_eol[found.group(4)] = found.group(1)
    for rel in pinned:
        if index_eol.get(rel) != "lf":
            problems.append(f"notice-not-pinned: {rel} is stored {index_eol.get(rel)!r}, not lf")
    for rel in UNRELATED_PATHS:
        if index_eol.get(rel) != "crlf":
            problems.append(f"attribute-scope-broad: unrelated {rel} was rewritten to {index_eol.get(rel)!r}")
    return problems


def notice_digest_problems(root, table):
    """Compare each fixture's committed manifest and notice bytes with the notice digest table."""
    problems = []
    for name, (manifest_sha, license_sha) in sorted(table.items()):
        for label, expected in (("manifest.json", manifest_sha), ("LICENSE.txt", license_sha)):
            path = root / "fixtures" / name / label
            if not path.is_file():
                problems.append(f"digest-file-missing: fixtures/{name}/{label}")
            elif hashlib.sha256(path.read_bytes()).hexdigest() != expected:
                problems.append(f"digest-mismatch: fixtures/{name}/{label}")
    return problems


def self_test():
    script = pathlib.Path(__file__).resolve()
    positives = negatives = 0
    with tempfile.TemporaryDirectory(prefix="gabbaboy-source-archive-") as scratch_name:
        scratch = pathlib.Path(scratch_name)
        sha = "a" * 40
        tag = "v0.0.1"

        def write(name, data):
            path = scratch / name
            path.write_bytes(data)
            return path

        def expect_pass(label, archive, *extra, tag_arg=tag, sha_arg=sha):
            nonlocal positives
            out = scratch / f"{label}.receipt.json"
            code, err, _ = run_cli(script, "--archive", str(archive), "--tag", tag_arg, "--source-sha", sha_arg, "--output", str(out), *extra)
            if code != 0:
                raise SystemExit(f"self-test positive {label} failed: {err}")
            receipt = json.loads(out.read_text())
            if receipt["inspected_members"] <= 0 or not receipt["admitted_fixture_identities"]:
                raise SystemExit(f"self-test positive {label} produced an empty receipt")
            positives += 1
            print(f"accepted: {label}")
            return receipt

        def expect_reject(label, code_expected, archive, *extra, tag_arg=tag, sha_arg=sha):
            nonlocal negatives
            out = scratch / f"{label}.receipt.json"
            code, err, stdout = run_cli(script, "--archive", str(archive), "--tag", tag_arg, "--source-sha", sha_arg, "--output", str(out), *extra)
            if code != 1 or not err.startswith(f"REJECT {code_expected}:"):
                raise SystemExit(f"self-test negative {label}: expected REJECT {code_expected}, got exit {code}: {err!r}")
            if stdout:
                raise SystemExit(f"self-test negative {label} printed success output: {stdout!r}")
            if out.exists():
                raise SystemExit(f"self-test negative {label} left a receipt behind")
            negatives += 1
            print(f"rejected: {label} ({code_expected})")

        def expect_inspect_reject(label, code_expected, archive, limits=None):
            nonlocal negatives
            try:
                inspect_tar(archive, limits or Limits(), want_git=False)
            except Reject as rejection:
                if rejection.code != code_expected:
                    raise SystemExit(f"self-test parser negative {label}: expected {code_expected}, got {rejection.code}: {rejection}")
            else:
                raise SystemExit(f"self-test parser negative {label}: archive was accepted")
            negatives += 1
            print(f"rejected: {label} ({code_expected})")

        def with_tar_limit(name, value, operation):
            original = globals()[name]
            globals()[name] = value
            try:
                operation()
            finally:
                globals()[name] = original

        base = synthetic_tree()

        def variant(**changes):
            files = dict(base)
            for key, value in changes.items():
                name = key.replace("__", "/").replace("_dot_", ".")
                if value is None:
                    files.pop(name, None)
                else:
                    files[name] = value
            return files

        # Positive path through real `git archive` bytes, bound to a private tagged tree.
        repo = scratch / "repo"
        repo.mkdir()
        private_git("init", "-q", cwd=repo)
        for name, data in base.items():
            target = repo / name
            target.parent.mkdir(parents=True, exist_ok=True)
            if isinstance(data, tuple):
                target.symlink_to(data[1])
            else:
                target.write_bytes(data)
        private_git("add", "-A", cwd=repo)
        private_git("commit", "-q", "-m", "synthetic tagged tree", cwd=repo)
        real_sha = private_git("rev-parse", "HEAD", cwd=repo).decode().strip()
        private_git("tag", tag, cwd=repo)
        git_tar = scratch / "git.tar"
        git_tar.write_bytes(private_git("archive", "--format=tar", "--prefix=gabbaboy-0.0.1/", tag, cwd=repo))
        git_tgz = write("git-source.tar.gz", gzip.compress(git_tar.read_bytes(), mtime=0))
        git_zip = write("git-source.zip", private_git("archive", "--format=zip", "--prefix=gabbaboy-0.0.1/", tag, cwd=repo))
        tgz_receipt = expect_pass("git-tar-bound-to-tag", git_tgz, "--repo", str(repo), sha_arg=real_sha)
        zip_receipt = expect_pass("git-zip-bound-to-tag", git_zip, "--repo", str(repo), sha_arg=real_sha)
        if tgz_receipt["source_tree_sha256"] != zip_receipt["source_tree_sha256"] or not tgz_receipt["tree_bound_to_git"]:
            raise SystemExit("self-test: tar and zip archives of the same tag disagree on the source tree digest")
        if {i["fixture"] for i in tgz_receipt["admitted_fixture_identities"]} != {"alpha", "beta"} or \
                tgz_receipt["admitted_fixture_identities"][1]["rom_count"] != 2:
            raise SystemExit("self-test: receipt does not record the admitted fixture identities")
        generated = write("generated.tar.gz", tar_bytes(base, real_sha))
        generated_receipt = expect_pass("generated-matches-git-tree", generated, "--repo", str(repo), sha_arg=real_sha)
        if generated_receipt["source_tree_sha256"] != tgz_receipt["source_tree_sha256"]:
            raise SystemExit("self-test: generated and git archives of one tree disagree")
        expect_pass("generated-without-repo", write("plain.tar.gz", tar_bytes(base, sha)))

        long_path_members = dict(base)
        long_path_names = []
        for index in range(256):
            name = f"src/long-paths/{index:03d}-" + ("x" * 105) + ".txt"
            long_path_names.append(name)
            long_path_members[name] = f"long path member {index}\n".encode("ascii")
        long_path_archive = write("many-long-paths.tar.gz", tar_bytes(long_path_members, sha))
        extension_types = {
            tarfile.GNUTYPE_LONGNAME, tarfile.GNUTYPE_LONGLINK, tarfile.GNUTYPE_SPARSE,
            tarfile.XHDTYPE, tarfile.XGLTYPE, tarfile.SOLARIS_XHDTYPE,
        }
        base_proc_member = tarfile.TarInfo._proc_member
        extension_payload_calls = []

        def count_long_path_extensions(info, archive):
            if info.type in extension_types:
                extension_payload_calls.append(info.type)
            return base_proc_member(info, archive)

        tarfile.TarInfo._proc_member = count_long_path_extensions
        try:
            first_inspection = inspect_tar(long_path_archive, Limits(), want_git=False)
            if sum(entry.path in long_path_names for entry in first_inspection.entries) != 256:
                raise SystemExit("self-test 256-long-path positive did not retain all members")
            exact_extension_count = len(extension_payload_calls)
            if exact_extension_count <= 128:
                raise SystemExit("self-test 256-long-path positive did not exercise more than 128 extension headers")
            if exact_extension_count > MAX_TAR_TOTAL_EXTENSION_HEADERS:
                raise SystemExit("self-test 256-long-path positive exceeded the default archive-wide header cap")
            if first_inspection.commit != sha:
                raise SystemExit("self-test 256-long-path positive lost global source identity metadata")
            extension_payload_calls.clear()

            def inspect_again_at_exact_total_cap():
                second_inspection = inspect_tar(long_path_archive, Limits(), want_git=False)
                if sum(entry.path in long_path_names for entry in second_inspection.entries) != 256:
                    raise SystemExit("self-test repeated 256-long-path inspection lost members")
                if len(extension_payload_calls) != exact_extension_count:
                    raise SystemExit("self-test repeated 256-long-path inspection processed a different header count")
                if second_inspection.commit != sha:
                    raise SystemExit("self-test repeated 256-long-path inspection lost global source identity metadata")

            # Requiring an exact-cap parse to succeed twice proves the archive-wide count is
            # fresh for each inspect_tar call; a shared counter would reject the second pass.
            with_tar_limit("MAX_TAR_TOTAL_EXTENSION_HEADERS", exact_extension_count,
                           inspect_again_at_exact_total_cap)
        finally:
            tarfile.TarInfo._proc_member = base_proc_member
        positives += 1
        print("accepted: 256 long-path source members on independent inspections")
        expect_pass("source-cli-256-long-paths", long_path_archive, sha_arg=sha)

        large_source_metadata = write(
            "source-with-large-pax.tar.gz",
            tar_bytes(base, real_sha, extra_pax={"src/a.c": {"GBB.control": "x" * 70_000}}))
        expect_reject("source-cli-oversized-pax", "archive-extension-header-limit", large_source_metadata,
                      "--repo", str(repo), sha_arg=real_sha)

        # Rights and content mutations: each must fail for its own reason.
        expect_reject("missing-fixture-notice", "missing-notice", write("m1.tar.gz", tar_bytes(variant(fixtures__alpha__LICENSE_dot_txt=None), sha)))
        expect_reject("missing-notices-file", "missing-notice", write("m2.tar.gz", tar_bytes(variant(THIRD_PARTY_NOTICES_dot_md=None), sha)))
        expect_reject("licensed-fixture-digest", "fixture-digest-mismatch",
                      write("m3.tar.gz", tar_bytes(variant(fixtures__alpha__manifest_dot_json=base["fixtures/alpha/manifest.json"] + b" "), sha)))
        expect_reject("unauthorized-rom-in-fixture", "unexpected-rom", write("m4.tar.gz", tar_bytes(variant(fixtures__alpha__evil_dot_gb=b"\x00EVIL"), sha)))
        expect_reject("unauthorized-rom-outside-fixtures", "unexpected-rom", write("m5.tar.gz", tar_bytes(variant(src__extra_dot_gb=b"\x00EVIL"), sha)))
        gamma = variant(fixtures__gamma__manifest_dot_json=b"{}\n", fixtures__gamma__LICENSE_dot_txt=b"x\n")
        expect_reject("unlicensed-unadmitted-fixture", "fixture-unadmitted", write("m6.tar.gz", tar_bytes(gamma, sha)))
        expect_reject("admitted-fixture-removed", "fixture-missing", write("m7.tar.gz", tar_bytes(
            {k: v for k, v in base.items() if not k.startswith("fixtures/beta/")}, sha)))
        expect_reject("loose-fixtures-file", "fixture-unadmitted", write("m7b.tar.gz", tar_bytes(variant(fixtures__stray_dot_txt=b"x"), sha)))

        # Source and tag identity.
        expect_reject("wrong-source-sha", "tag-source-mismatch", write("s1.tar.gz", tar_bytes(base, "b" * 40)))
        expect_reject("no-embedded-commit", "tag-source-mismatch", write("s2.tar.gz", tar_bytes(base, None)))
        expect_reject("wrong-root-version", "root-mismatch", write("s3.tar.gz", tar_bytes(base, sha, root="gabbaboy-9.9.9")))
        expect_reject("malformed-tag", "tag-invalid", generated, tag_arg="0.0.1")
        expect_reject("tag-absent-from-repo", "tag-source-mismatch", write("s0.tar.gz", tar_bytes(base, real_sha, root="gabbaboy-0.0.2")),
                      "--repo", str(repo), tag_arg="v0.0.2", sha_arg=real_sha)
        expect_reject("tag-resolves-elsewhere", "tag-source-mismatch", generated, "--repo", str(repo), sha_arg="c" * 40)
        expect_reject("content-differs-from-tagged-tree", "tree-mismatch",
                      write("s4.tar.gz", tar_bytes(variant(src__a_dot_c=b"int a(void) { return 2; }\n"), real_sha)), "--repo", str(repo), sha_arg=real_sha)
        expect_reject("extra-file-versus-tagged-tree", "tree-mismatch",
                      write("s5.tar.gz", tar_bytes(variant(src__b_dot_c=b"int b;\n"), real_sha)), "--repo", str(repo), sha_arg=real_sha)
        expect_reject("two-top-level-roots", "root-mismatch", write("s6.tar.gz", tar_bytes({**base, "@other-root/x": b"x"}, sha, fmt=tarfile.GNU_FORMAT)))

        # Unsafe members and resource limits.
        expect_reject("parent-traversal", "path-unsafe", write("p1.tar.gz", tar_bytes({**base, "@gabbaboy-0.0.1/../evil": b"x"}, sha)))
        expect_reject("absolute-path", "path-unsafe", write("p2.tar.gz", tar_bytes({**base, "@/etc/evil": b"x"}, sha)))
        dup = io.BytesIO()
        with tarfile.open(fileobj=dup, mode="w", format=tarfile.PAX_FORMAT, pax_headers={"comment": sha}) as bundle:
            top = tarfile.TarInfo("gabbaboy-0.0.1")
            top.type = tarfile.DIRTYPE
            bundle.addfile(top)
            for _ in range(2):
                info = tarfile.TarInfo("gabbaboy-0.0.1/README.md")
                info.size = 1
                bundle.addfile(info, io.BytesIO(b"x"))
        expect_reject("duplicate-path", "path-duplicate", write("p3.tar.gz", gzip.compress(dup.getvalue(), mtime=0)))
        long_name = "d/" * 2100 + "f"
        expect_reject("overlong-path", "path-too-long", write("p4.tar.gz", tar_bytes({**base, long_name: b"x"}, sha)))
        top = tarfile.TarInfo("gabbaboy-0.0.1")
        top.type = tarfile.DIRTYPE
        header = tarfile.TarInfo("gabbaboy-0.0.1/huge.bin")
        header.size = MAX_MEMBER_BYTES + 1
        # Metadata only: two headers and no data, so a rejection proves the declared size
        # is refused before any allocation or read.
        bomb = top.tobuf(tarfile.GNU_FORMAT) + header.tobuf(tarfile.GNU_FORMAT)
        expect_reject("oversize-member-metadata", "member-oversize", write("p5.tar.gz", gzip.compress(bomb, mtime=0)))
        oversized_global = write("oversized-global-pax.tar.gz",
                                 tar_bytes({"README.md": b"x"}, "x" * 70_000))
        base_proc_member = tarfile.TarInfo._proc_member
        parser_body_calls = []

        def count_extension_body_parser(info, archive):
            parser_body_calls.append(info.type)
            return base_proc_member(info, archive)

        tarfile.TarInfo._proc_member = count_extension_body_parser
        try:
            inspect_tar(oversized_global, Limits(), want_git=False)
        except Reject as rejection:
            if rejection.code != "archive-extension-header-limit":
                raise SystemExit(f"self-test 70KB PAX control rejected for wrong reason: {rejection}") from None
            if parser_body_calls:
                raise SystemExit("self-test 70KB PAX header reached TarInfo payload parsing before rejection")
            negatives += 1
            print("rejected: 70KB PAX header (archive-extension-header-limit)")
        else:
            raise SystemExit("self-test 70KB PAX header passed inspect_tar without a resource rejection")
        finally:
            tarfile.TarInfo._proc_member = base_proc_member

        aggregate = write("aggregate-pax.tar.gz", tar_bytes(
            {"one": b"1", "two": b"2", "three": b"3"}, None,
            extra_pax={name: {"GBB.control": "x" * 60_000} for name in ("one", "two", "three")}))
        with_tar_limit("MAX_TAR_TOTAL_EXTENSION_BYTES", 128 * 1024,
                       lambda: expect_inspect_reject("aggregate extension payload", "archive-extension-total-limit", aggregate))

        count_archive = write("extension-count.tar.gz", chained_pax_tar_bytes(129, b"5 x=\n"))
        with_tar_limit("MAX_TAR_EXTENSION_HEADERS", 128,
                       lambda: expect_inspect_reject("chained extension header count", "archive-extension-count-limit", count_archive))

        interleaved_count_archive = write(
            "interleaved-extension-count.tar.gz",
            tar_bytes({"one": b"1", "two": b"2", "three": b"3"}, None,
                      extra_pax={name: {"GBB.x": "y"} for name in ("one", "two", "three")}))
        interleaved_record_size = len(pax_record("GBB.x", b"y"))
        if (interleaved_count_archive.stat().st_size >= MAX_TOTAL_BYTES
                or len(gzip.decompress(interleaved_count_archive.read_bytes())) >= MAX_TAR_STREAM_BYTES
                or 3 > Limits().entries
                or interleaved_record_size > MAX_TAR_EXTENSION_BYTES
                or 3 * interleaved_record_size > MAX_TAR_TOTAL_EXTENSION_BYTES):
            raise SystemExit("self-test interleaved count archive exceeded an unrelated archive limit")
        interleaved_payload_calls = []

        def count_interleaved_extension_payload(info, archive):
            if info.type in extension_types:
                interleaved_payload_calls.append(info.type)
            return base_proc_member(info, archive)

        tarfile.TarInfo._proc_member = count_interleaved_extension_payload
        try:
            with_tar_limit("MAX_TAR_TOTAL_EXTENSION_HEADERS", 2,
                           lambda: expect_inspect_reject(
                               "interleaved archive-wide extension header count",
                               "archive-extension-total-count-limit", interleaved_count_archive))
            if len(interleaved_payload_calls) != 2:
                raise SystemExit("self-test archive-wide header cap parsed an over-limit extension payload")
        finally:
            tarfile.TarInfo._proc_member = base_proc_member

        stream_archive = write("decompressed-stream.tar.gz",
                               tar_bytes({"README.md": b"z" * (32 * 1024)}, None))
        if stream_archive.stat().st_size >= 32 * 1024:
            raise SystemExit("self-test decompressed-stream control is not highly compressible")
        with_tar_limit("MAX_TAR_STREAM_BYTES", 4096,
                       lambda: expect_inspect_reject("decompressed TAR stream", "archive-stream-limit", stream_archive))
        expect_reject("symlink-not-in-tree", "link-not-allowed", write("p6.tar.gz", tar_bytes({**base, "link": ("symlink", "/etc/passwd")}, sha)))
        expect_reject("hardlink-member", "link-not-allowed", write("p7.tar.gz", tar_bytes({**base, "hard": ("hardlink", "README.md")}, sha)))
        expect_reject("device-member", "nonregular-member", write("p8.tar.gz", tar_bytes({**base, "dev": ("device", "")}, sha)))
        expect_reject("entry-limit", "too-many-entries", generated, "--max-entries", "3")
        expect_reject("total-size-limit", "archive-oversize", generated, "--max-total-bytes", "64")
        expect_reject("member-size-limit", "member-oversize", generated, "--max-member-bytes", "8")
        expect_reject("path-length-limit", "path-too-long", generated, "--max-path-bytes", "16")
        expect_reject("truncated-gzip", "archive-unreadable", write("t1.tar.gz", generated.read_bytes()[:200]))
        expect_reject("not-an-archive", "archive-unreadable", write("t2.tar.gz", b"plain text, not an archive"))

        # Product package contract: build a complete accepted product from the pinned source baseline,
        # independent of mutable files in the checkout under test.
        product_checker, product_repo, good_product, good_inventory, forbidden_product_bytes, product_rules, source_contract = \
            _synthetic_core_product(scratch)

        # A release retry must use the trusted workflow-commit checker even when the tagged
        # workspace sibling differs. Exercise the CLI with a deliberately unusable sibling.
        tagged_dir = scratch / "tagged-checkout"
        trusted_dir = scratch / "trusted-control-plane"
        tagged_dir.mkdir()
        trusted_dir.mkdir()
        tagged_script = tagged_dir / "verify-v02-source-archive.py"
        shutil.copyfile(script, tagged_script)
        (tagged_dir / "verify-fixture-admission.py").write_text(
            "raise RuntimeError('tagged sibling checker must not be imported')\n", encoding="utf-8")
        trusted_checker = trusted_dir / "verify-fixture-admission.py"
        shutil.copyfile(product_checker.__file__, trusted_checker)
        trusted_archive = write("product-with-explicit-trusted-checker.tar.gz",
                                tar_bytes(good_product, None, root=None))
        code, err, stdout = run_cli(tagged_script, "--check-product-archive", str(trusted_archive),
                                    "--repo-root", str(product_repo), "--fixture-checker", str(trusted_checker))
        if code != 0 or not stdout.startswith("PASS: core product matches exact policy"):
            raise SystemExit(f"self-test trusted fixture checker was not used: {err!r}, {stdout!r}")
        positives += 1
        print("accepted: archive policy uses the explicit trusted fixture checker")

        def expect_product(label, files, expected, root_name=None, inventory=None,
                           notice_sidecar=None, use_cli=False):
            nonlocal positives, negatives
            archive = write(f"{label}.tar.gz", tar_bytes(files, None, root=root_name))
            inventory_path = None
            args = ["--check-product-archive", str(archive), "--repo-root", str(product_repo)]
            if inventory is not None:
                inventory_path = scratch / f"{label}.inventory.json"
                inventory_path.write_text(json.dumps(inventory, sort_keys=True), encoding="utf-8")
                args.extend(("--inventory", str(inventory_path)))
            if notice_sidecar is not None:
                args.extend(("--notice-sidecar", str(notice_sidecar)))
            if use_cli:
                code, err, stdout = run_cli(script, *args)
                if expected is None:
                    if code != 0:
                        raise SystemExit(f"self-test product positive {label} failed: {err}")
                elif stdout or code != 1 or not err.startswith(f"REJECT {expected}:"):
                    raise SystemExit(f"self-test product negative {label}: expected {expected}, got {code}: {err!r}")
            else:
                try:
                    check_product(str(archive), str(product_repo), Limits(), str(inventory_path) if inventory_path else None)
                except Reject as rejection:
                    if expected is None or rejection.code != expected:
                        raise SystemExit(f"self-test product {label}: expected {expected or 'accept'}, got {rejection.code}: {rejection}")
                else:
                    if expected is not None:
                        raise SystemExit(f"self-test product {label}: mutation was accepted; expected {expected}")
            if expected is None:
                positives += 1
                print(f"accepted: {label}")
            else:
                negatives += 1
                print(f"rejected: {label} ({expected})")

        # One CLI positive covers option parsing and inventory loading. Later archive mutations
        # use the same production function with baseline expectations precomputed once, avoiding
        # a full fixture-tree digest scan for every individual negative control.
        expect_product("complete-core-product-from-pinned-baseline", good_product, None,
                       inventory=good_inventory, use_cli=True)

        good_sidecar = scratch / "gabbaboy-notices.txt"
        good_sidecar.write_bytes(product_checker.blob(product_repo, product_checker.BASELINE_COMMIT, "LICENSE"))
        expect_product("complete-core-product-with-release-sidecar", good_product, None,
                       inventory=good_inventory, notice_sidecar=good_sidecar, use_cli=True)
        large_product_member = next(iter(good_product))
        large_product_metadata = write(
            "core-product-with-large-pax.tar.gz",
            tar_bytes(good_product, None, root=None,
                      extra_pax={large_product_member: {"GBB.control": "x" * 70_000}}))
        code, err, stdout = run_cli(script, "--check-product-archive", str(large_product_metadata),
                                    "--repo-root", str(product_repo))
        if code != 1 or stdout or not err.startswith("REJECT archive-extension-header-limit:"):
            raise SystemExit(f"self-test core product PAX negative expected metadata-limit rejection, got {code}: {err!r}, {stdout!r}")
        negatives += 1
        print("rejected: core-product CLI oversized PAX (archive-extension-header-limit)")
        missing_sidecar = scratch / "missing-sidecar" / "gabbaboy-notices.txt"
        expect_product("product-missing-release-sidecar", good_product, "product-notice-sidecar-invalid",
                       notice_sidecar=missing_sidecar, use_cli=True)
        altered_sidecar = scratch / "altered-sidecar" / "gabbaboy-notices.txt"
        altered_sidecar.parent.mkdir()
        altered_sidecar.write_bytes(good_sidecar.read_bytes() + b"altered\n")
        expect_product("product-altered-release-sidecar", good_product, "product-notice-sidecar-mismatch",
                       notice_sidecar=altered_sidecar, use_cli=True)
        wrong_name_sidecar = scratch / "notice.txt"
        wrong_name_sidecar.write_bytes(good_sidecar.read_bytes())
        expect_product("product-wrong-release-sidecar-name", good_product, "product-notice-sidecar-invalid",
                       notice_sidecar=wrong_name_sidecar, use_cli=True)

        def cached_product_entries(entries, layout, repo_root, inventory=None, sidecar=None):
            return product_checker._validate_product_entries(
                entries, layout, repo_root, inventory=inventory, sidecar=sidecar,
                rules_override=product_rules, source_contract=source_contract)

        product_checker.check_product_entries = cached_product_entries
        expect_product("product-wrapped-in-a-source-style-root", good_product, "product-path-unknown", root_name="stage")
        for directory in ("tracer", "visible-demo", "mbc1-continuation"):
            expect_product(f"product-extra-member-{directory}",
                           {**good_product, f"share/gabbaboy/fixtures/{directory}/unregistered.bin": b"extra"},
                           "product-path-unknown", use_cli=(directory == "tracer"))
            for disguise in ("renamed-payload.bin", "suffixless"):
                path = f"share/gabbaboy/fixtures/{directory}/{disguise}"
                expect_product(f"product-known-forbidden-{directory}-{disguise}",
                               {**good_product, path: forbidden_product_bytes}, "product-fixture-leak")

        policy_rules, _ = product_checker._product_rules(product_repo)
        fixture_records = [(source, record) for source, record in policy_rules["files"].items()
                           if source.startswith("fixtures/") and record["destinations"].get("core")]
        for index, (source, record) in enumerate(fixture_records):
            destination = record["destinations"]["core"][0]
            if source.endswith("LICENSE.txt"):
                expect_product(f"product-missing-fixture-license-{index}",
                               {path: value for path, value in good_product.items() if path != destination},
                               "product-path-missing")
                expect_product(f"product-altered-fixture-license-{index}",
                               {**good_product, destination: good_product[destination] + b"altered\n"},
                               "product-identity-mismatch")
            elif source.endswith((".gb", ".gbc", ".sgb", ".rom", ".bin", ".asm")) or source.endswith("manifest.json"):
                expect_product(f"product-altered-fixture-identity-{index}",
                               {**good_product, destination: good_product[destination] + b"changed\n"},
                               "product-identity-mismatch")

        root_license = "share/gabbaboy/LICENSE.txt"
        expect_product("product-missing-root-mit", {path: value for path, value in good_product.items()
                                                      if path != root_license}, "product-path-missing")
        expect_product("product-altered-root-mit", {**good_product, root_license: good_product[root_license] + b"altered\n"},
                       "product-identity-mismatch")
        expect_product("product-with-source-notice-index", {**good_product, NOTICE_NAME: b"x"}, "product-path-unknown")
        expect_product("product-with-changed-inventory", good_product,
                       "product-inventory-mismatch", inventory={**good_inventory, "policy_sha256": "0" * 64})
        expect_product("product-missing-generated-header",
                       {k: v for k, v in good_product.items() if k != "include/gabbaboy/gabbaboy.h"},
                       "product-path-missing")

        notices = (pathlib.Path(__file__).resolve().parents[2] / NOTICE_NAME).read_bytes()
        check_product_notice_contract(notices)
        positives += 1
        altered_claim = notices.replace(
            b"Controlled game and diagnostic bytes",
            b"Approved game and diagnostic bytes")
        if altered_claim == notices:
            raise SystemExit("self-test notice-contract mutation did not alter its target claim")
        try:
            check_product_notice_contract(altered_claim)
        except Reject as error:
            if error.code != "notice-contract-invalid":
                raise SystemExit(f"self-test notice-contract negative returned unrelated rejection: {error}")
            negatives += 1
            print("rejected: altered binary product claim (notice-contract-invalid)")
        else:
            raise SystemExit("self-test notice-contract negative accepted an altered product claim")

        code, err, _ = run_cli(script, "--check-product-archive", str(generated), "--repo-root", str(product_repo))
        if code != 1 or not err.startswith("REJECT product-"):
            raise SystemExit(f"self-test: a licensed source archive was accepted as a product package: {err!r}")
        negatives += 1
        print("rejected: licensed source archive substituted for a product package")
        code, err, _ = run_cli(script, "--archive", str(write("p9.tar.gz", tar_bytes(good_product, sha, root="gabbaboy-0.0.1"))),
                               "--tag", tag, "--source-sha", sha, "--output", str(scratch / "p9.json"))
        if code != 1 or not err.startswith(f"REJECT missing-notice:"):
            raise SystemExit(f"self-test: a fixture-free product archive was accepted as a source archive: {err!r}")
        negatives += 1
        print("rejected: fixture-free product package substituted for a source archive")

        # Receipt consumption: the final release gate reads this receipt, not the build receipt.
        good = scratch / "git-tar-bound-to-tag.receipt.json"
        def expect_receipt_pass(label, receipt, archive, repo_path):
            nonlocal positives
            code, err, stdout = run_cli(script, "--check-receipt", str(receipt), "--archive", str(archive),
                                        "--tag", tag, "--source-sha", real_sha, "--repo", str(repo_path))
            if code != 0 or not stdout.startswith("PASS: source archive receipt"):
                raise SystemExit(f"self-test receipt positive {label} failed: exit {code}, {err!r}, {stdout!r}")
            positives += 1
            print(f"accepted: receipt {label}")

        def expect_receipt_reject(label, code_expected, receipt, archive, repo_path):
            nonlocal negatives
            code, err, stdout = run_cli(script, "--check-receipt", str(receipt), "--archive", str(archive),
                                        "--tag", tag, "--source-sha", real_sha, "--repo", str(repo_path))
            if code != 1 or not err.startswith(f"REJECT {code_expected}:"):
                raise SystemExit(f"self-test receipt negative {label}: expected REJECT {code_expected}, got exit {code}: {err!r}")
            if stdout:
                raise SystemExit(f"self-test receipt negative {label} printed success output: {stdout!r}")
            negatives += 1
            print(f"rejected: receipt {label} ({code_expected})")

        expect_receipt_reject("oversized PAX source recheck", "archive-extension-header-limit", good,
                              large_source_metadata, repo)

        receipt_cases = {
            "wrong-kind": lambda r: r.update(kind="gabbaboy-build-receipt"),
            "wrong-tag": lambda r: r.update(tag="v9.9.9"),
            "wrong-sha": lambda r: r.update(source_sha="d" * 40),
            "malformed-archive-digest": lambda r: r.update(archive_sha256="z" * 64),
            "no-fixture-identities": lambda r: r.update(admitted_fixture_identities=[]),
            "altered-notice-digest": lambda r: r.update(notice_sha256="0" * 64),
        }
        code, err, stdout = run_cli(script, "--check-receipt", str(good), "--archive", str(git_tgz),
                                    "--tag", tag, "--source-sha", real_sha, "--repo", str(repo))
        if code != 0:
            raise SystemExit(f"self-test receipt positive failed: {err!r}")
        if not stdout.startswith("PASS: source archive receipt"):
            raise SystemExit(f"self-test receipt positive omitted success output: {stdout!r}")
        positives += 1
        print("accepted: receipt recomputed against the immutable Git tree")

        # Receipt qualification must consume the real immutable tag tree, not trust a
        # producer's tree_bound_to_git boolean. Each control enters through --check-receipt.
        bound_receipt = scratch / "git-tar-bound-to-tag.receipt.json"
        expect_receipt_pass("bound to immutable Git tree", bound_receipt, git_tgz, repo)
        unbound_source_receipt = scratch / "generated-matches-git-tree-unbound.receipt.json"
        code, err, _ = run_cli(script, "--archive", str(generated), "--tag", tag, "--source-sha", real_sha,
                               "--output", str(unbound_source_receipt))
        if code != 0:
            raise SystemExit(f"self-test: could not create an unbound receipt for the real tagged tree: {err!r}")
        expect_receipt_reject("historical unbound receipt", "receipt-unbound", unbound_source_receipt, generated, repo)

        flipped = json.loads(bound_receipt.read_text())
        flipped["tree_bound_to_git"] = False
        flipped_path = write("receipt-flipped-tree-binding.json", json.dumps(flipped).encode())
        expect_receipt_reject("cleared Git-binding boolean", "receipt-unbound", flipped_path, git_tgz, repo)

        modified_source = write("modified-source-claiming-tag.tar.gz",
                                tar_bytes(variant(src__a_dot_c=b"int a(void) { return 2; }\n"), real_sha))
        modified_receipt = scratch / "modified-source-receipt.json"
        code, err, _ = run_cli(script, "--archive", str(modified_source), "--tag", tag,
                               "--source-sha", real_sha, "--output", str(modified_receipt))
        if code != 0:
            raise SystemExit(f"self-test: could not create an unbound receipt for the modified-tree control: {err!r}")
        modified_data = json.loads(modified_receipt.read_text())
        modified_data["tree_bound_to_git"] = True
        modified_receipt.write_text(json.dumps(modified_data))
        expect_receipt_reject("modified archive claiming tagged commit", "tree-mismatch", modified_receipt,
                              modified_source, repo)

        for label, mutate in receipt_cases.items():
            receipt = json.loads(good.read_text())
            mutate(receipt)
            path = write(f"receipt-{label}.json", json.dumps(receipt).encode())
            code, err, stdout = run_cli(script, "--check-receipt", str(path), "--archive", str(git_tgz),
                                        "--tag", tag, "--source-sha", real_sha, "--repo", str(repo))
            if code != 1 or not err.startswith("REJECT receipt-invalid:"):
                raise SystemExit(f"self-test receipt negative {label}: got {code}: {err!r}")
            if stdout:
                raise SystemExit(f"self-test receipt negative {label} printed success output: {stdout!r}")
            negatives += 1
            print(f"rejected: receipt {label}")

        reencoded = write("git-source-reencoded.tar.gz", gzip.compress(git_tar.read_bytes(), compresslevel=1, mtime=123))
        if sha256_path(reencoded) == sha256_path(git_tgz):
            raise SystemExit("self-test: gzip re-encoding did not change the compressed archive bytes")
        expect_receipt_pass("same Git tree with different gzip bytes", bound_receipt, reencoded, repo)

        mode_changed = write("git-source-executable-mode.tar.gz", tar_bytes(
            variant(src__a_dot_c=("file", base["src/a.c"], 0o755)), real_sha))
        mode_receipt = scratch / "git-source-executable-mode.receipt.json"
        code, err, _ = run_cli(script, "--archive", str(mode_changed), "--tag", tag, "--source-sha", real_sha,
                               "--output", str(mode_receipt))
        if code != 0:
            raise SystemExit(f"self-test: could not create a receipt for the executable-mode control: {err!r}")
        mode_data = json.loads(mode_receipt.read_text())
        mode_data["tree_bound_to_git"] = True
        mode_receipt.write_text(json.dumps(mode_data))
        expect_receipt_reject("executable-mode change under same tag", "tree-mismatch", mode_receipt,
                              mode_changed, repo)

        changed_link_tree = variant(src__nested__link=("symlink", "../README.md"))
        changed_link = write("git-source-symlink-target.tar.gz", tar_bytes(changed_link_tree, real_sha))
        changed_link_receipt = scratch / "git-source-symlink-target.receipt.json"
        code, err, _ = run_cli(script, "--archive", str(changed_link), "--tag", tag, "--source-sha", real_sha,
                               "--output", str(changed_link_receipt))
        if code != 0:
            raise SystemExit(f"self-test: could not create a receipt for the symlink-target control: {err!r}")
        changed_link_data = json.loads(changed_link_receipt.read_text())
        changed_link_data["tree_bound_to_git"] = True
        changed_link_receipt.write_text(json.dumps(changed_link_data))
        expect_receipt_reject("symlink target change under same tag", "tree-mismatch", changed_link_receipt,
                              changed_link, repo)

        nested_link = write("nested-in-root-link.tar.gz", tar_bytes(
            {**base, "src/nested/second-link": ("symlink", "../../README.md")}, sha))
        expect_pass("nested source link resolves within archive root", nested_link)
        nested_escape = write("nested-root-escape.tar.gz", tar_bytes(
            {**base, "src/nested/escape": ("symlink", "../../../outside")}, sha))
        expect_reject("nested source link escapes archive root", "link-not-allowed", nested_escape)
        expect_product("product-nested-in-root-link", {**good_product, "nested/link": ("symlink", "../README.md")},
                       "product-link-not-allowed")
        expect_product("product-nested-root-escape", {**good_product, "nested/link": ("symlink", "../../outside")},
                       "link-not-allowed")

        # Notice attribute scope and digest stability, on the real repository files. Unrelated CRLF bytes must
        # survive staging, pinned notice bytes must be stored as LF, and the committed notice digests must match.
        root_dir = script.parents[2]
        attributes_path = root_dir / ".gitattributes"
        notice_path = root_dir / NOTICE_NAME
        if attributes_path.is_file() and notice_path.is_file():
            real_attributes = attributes_path.read_text(encoding="utf-8")
            real_table = parse_notice_table(notice_path.read_text(encoding="utf-8"))
            names = sorted(real_table)
            if not names:
                raise SystemExit("self-test: the real notice file has no digest table")
            problems = attribute_scope_problems(real_attributes, names)
            if problems:
                raise SystemExit("self-test: the real .gitattributes scope is wrong: " + "; ".join(problems))
            positives += 1
            print("accepted: real-attribute-scope")
            digest_problems = notice_digest_problems(root_dir, real_table)
            if digest_problems:
                raise SystemExit("self-test: real notice digests are not stable: " + "; ".join(digest_problems))
            positives += 1
            print("accepted: real-notice-digests")
            broad = real_attributes + "LICENSE* text eol=lf\nNOTICE* text eol=lf\nTHIRD_PARTY* text eol=lf\n"
            expect_scope = {
                "broad-basename-wildcards": (broad, "attribute-scope-broad:"),
                "root-notice-unpinned": (real_attributes.replace("\n/LICENSE text eol=lf", "\n")
                                         .replace("\n/THIRD_PARTY_NOTICES.md text eol=lf", "\n"), "notice-not-pinned:"),
                "fixture-license-unpinned": (real_attributes.replace("fixtures/*/LICENSE.txt text eol=lf", ""),
                                             "notice-not-pinned:"),
            }
            for label, (attributes, reason) in expect_scope.items():
                if attributes == real_attributes:
                    raise SystemExit(f"self-test: attribute mutant {label} did not change .gitattributes")
                found = attribute_scope_problems(attributes, names)
                if not any(item.startswith(reason) for item in found):
                    raise SystemExit(f"self-test: attribute mutant {label} was not rejected for {reason} (got {found})")
                negatives += 1
                print(f"rejected: {label}")
            altered = dict(real_table)
            first = names[0]
            altered[first] = ("0" * 64, altered[first][1])
            if not notice_digest_problems(root_dir, altered):
                raise SystemExit("self-test: an altered notice digest row was not rejected")
            negatives += 1
            print("rejected: altered-notice-digest-row")
        else:
            raise SystemExit("self-test: .gitattributes and the notice file are required in the source tree")

        # Real tree: archive the committed repository at a private tag in a lightweight clone.
        # The test only reads Git objects, so share the checkout object store and skip
        # materializing a worktree instead of copying the full object database on Windows.
        root = script.parents[2]
        if (root / ".git").exists():
            clone = scratch / "clone"
            subprocess.run(["git", "clone", "-q", "--shared", "--no-checkout", str(root), str(clone)],
                           capture_output=True, check=False)
            if (clone / ".git").exists():
                head = private_git("rev-parse", "HEAD", cwd=clone).decode().strip()
                private_git("tag", tag, cwd=clone)
                real_tar = write("real.tar.gz", gzip.compress(private_git("archive", "--format=tar", "--prefix=gabbaboy-0.0.1/", tag, cwd=clone), mtime=0))
                receipt = expect_pass("real-repository-tag", real_tar, "--repo", str(clone), sha_arg=head)
                if len(receipt["admitted_fixture_identities"]) < 19:
                    raise SystemExit("self-test: the real source archive admits fewer than the 19 recorded fixture directories")
                broken = real_tar.read_bytes()
                # Drop one real fixture notice and re-pack to prove the real checker rejects the real tree.
                source = tarfile.open(fileobj=io.BytesIO(gzip.decompress(broken)))
                members = {}
                for member in source:
                    if member.isreg():
                        members[member.name.split("/", 1)[1]] = source.extractfile(member).read()
                members.pop("fixtures/libbet/LICENSE.txt")
                expect_reject("real-repository-missing-notice", "missing-notice", write("real-broken.tar.gz", tar_bytes(members, head)), sha_arg=head)
            else:
                print("skipped: real-repository-tag (local clone unavailable)")
        else:
            print("skipped: real-repository-tag (no git checkout)")
    if positives == 0 or negatives == 0:
        raise SystemExit("self-test selected no positive or no negative cases")
    print(f"PASS: source archive checker accepted {positives} cases and rejected {negatives} negative controls")


# --------------------------------------------------------------------------- entry point


def main(argv):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--self-test-product-tree")
    parser.add_argument("--archive")
    parser.add_argument("--tag")
    parser.add_argument("--source-sha")
    parser.add_argument("--output")
    parser.add_argument("--repo")
    parser.add_argument("--check-receipt")
    parser.add_argument("--check-product-archive")
    parser.add_argument("--repo-root")
    parser.add_argument("--fixture-checker", help="explicit trusted shared fixture admission checker")
    parser.add_argument("--inventory", help="compare actual archive paths and bytes with a producer stage inventory")
    parser.add_argument("--notice-sidecar", help="validate the actual gabbaboy-notices.txt sidecar bytes")
    # Limits can only be tightened, never raised above the contract values.
    parser.add_argument("--max-entries", type=int, default=MAX_ENTRIES)
    parser.add_argument("--max-total-bytes", type=int, default=MAX_TOTAL_BYTES)
    parser.add_argument("--max-member-bytes", type=int, default=MAX_MEMBER_BYTES)
    parser.add_argument("--max-path-bytes", type=int, default=MAX_PATH_BYTES)
    args = parser.parse_args(argv)
    limits = Limits(min(args.max_entries, MAX_ENTRIES), min(args.max_total_bytes, MAX_TOTAL_BYTES),
                    min(args.max_member_bytes, MAX_MEMBER_BYTES), min(args.max_path_bytes, MAX_PATH_BYTES))
    try:
        if args.self_test:
            self_test()
        elif args.self_test_product_tree:
            if not args.repo_root:
                parser.error("--self-test-product-tree needs --repo-root")
            self_test_product_tree(args.self_test_product_tree, args.repo_root)
        elif args.check_product_archive:
            result = check_product(args.check_product_archive, args.repo_root, limits,
                                   args.inventory, args.notice_sidecar, args.fixture_checker)
            print(f"PASS: core product matches exact policy ({result['inspected_members']} members)")
        elif args.check_receipt:
            if args.inventory or args.notice_sidecar or args.fixture_checker:
                parser.error("--inventory, --notice-sidecar and --fixture-checker are only valid with --check-product-archive")
            if not (args.archive and args.tag and args.source_sha):
                parser.error("--check-receipt needs --archive, --tag and --source-sha")
            check_receipt(args.check_receipt, args.archive, args.tag, args.source_sha, args.repo, limits)
            print("PASS: source archive receipt matches the archive bytes")
        elif args.archive:
            if args.inventory or args.notice_sidecar or args.fixture_checker:
                parser.error("--inventory, --notice-sidecar and --fixture-checker are only valid with --check-product-archive")
            if not (args.tag and args.source_sha and args.output):
                parser.error("--archive needs --tag, --source-sha and --output")
            output = pathlib.Path(args.output)
            output.unlink(missing_ok=True)
            receipt = build_receipt(args.archive, args.tag, args.source_sha, args.repo, limits)
            output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
            print(f"PASS: source archive {receipt['archive_sha256'][:12]} verified ({receipt['inspected_members']} members, "
                  f"{len(receipt['admitted_fixture_identities'])} admitted fixtures)")
        else:
            parser.error("choose --archive, --check-receipt, --check-product-archive or --self-test")
    except Reject as rejection:
        print(f"REJECT {rejection.code}: {rejection}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
