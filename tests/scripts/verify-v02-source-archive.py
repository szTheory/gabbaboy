#!/usr/bin/env python3
"""Verify GitHub-generated source archives separately from product packages.

Two contracts are checked here and they are deliberately not interchangeable:

* A *source archive* (`--archive`) is the exact-tag snapshot GitHub generates.
  It must retain every admitted licensed fixture together with its notice and
  must match the notice digest table byte for byte.
* A *product package* (`--check-product-archive`) is the installed core archive.
  It must stay fixture-free except for the three original project fixtures.

Both inspect archive bytes by streaming; nothing is ever extracted.  The Python
standard library is the only dependency.

Usage:
  verify-v02-source-archive.py --archive PATH --tag TAG --source-sha SHA
      --output PATH [--repo GIT_DIR]
  verify-v02-source-archive.py --check-receipt RECEIPT --archive PATH
      --tag TAG --source-sha SHA
  verify-v02-source-archive.py --check-product-archive PATH [--repo-root DIR]
  verify-v02-source-archive.py --self-test

Failures print `REJECT <code>: <reason>` on stderr and exit 1.
"""
import argparse
import gzip
import hashlib
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

SCHEMA_VERSION = 1
RECEIPT_KIND = "gabbaboy-source-archive-receipt"
MAX_ENTRIES = 100000
MAX_TOTAL_BYTES = 1 << 30
MAX_MEMBER_BYTES = 64 << 20
MAX_PATH_BYTES = 4096
KEEP_LIMIT = 4 << 20
CHUNK = 1 << 20
ROM_SUFFIXES = (".gb", ".gbc", ".sgb", ".rom", ".bin")
DIGEST_DOCS = ("manifest.json", "SOURCES.md", "candidate-digests.json")
NOTICE_NAME = "THIRD_PARTY_NOTICES.md"
# The only fixtures a binary product package may carry (THIRD_PARTY_NOTICES.md).
PRODUCT_FIXTURES = ("tracer", "visible-demo", "mbc1-continuation")
PRODUCT_REQUIRED = (
    "include/gabbaboy/gabbaboy.h",
    "share/gabbaboy/fixtures/tracer/manifest.json",
    "share/gabbaboy/fixtures/mbc1-continuation/manifest.json",
)
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
        depth = len(parts) - 2
        for step in target.split("/"):
            depth += -1 if step == ".." else (0 if step in ("", ".") else 1)
            if depth < 0:
                break
        if target.startswith("/") or "\x00" in target or depth < 0:
            raise Reject("link-not-allowed", f"symbolic link {raw!r} points outside the archive root")
        oid = hashlib.sha1(b"blob %d\x00" % len(target.encode()) + target.encode()).hexdigest()
        inspection.entries.append(Entry(rel, "symlink", size, target, None, oid, mode))
        return
    sha256, oid, kept = stream_hash(reader, size, want_git)
    inspection.entries.append(Entry(rel, "file", size, None, sha256, oid, mode))
    if kept is not None and (rel == NOTICE_NAME or pathlib.PurePosixPath(rel).name in ("LICENSE.txt",) + DIGEST_DOCS):
        inspection.kept[rel] = kept


def inspect_tar(path, limits, want_git, unwrapped=False):
    inspection, seen = Inspection(unwrapped), set()
    try:
        with tarfile.open(path, "r:gz") as bundle:
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
            inspection.commit = bundle.pax_headers.get("comment")
    except Reject:
        raise
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
        if (mode == "120000") != (entry.kind == "symlink") or entry.git_oid != oid:
            raise Reject("tree-mismatch", f"{name} differs from the tagged tree blob")


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
    lines = []
    for entry in sorted(inspection.entries, key=lambda e: e.path):
        lines.append(f"{entry.path}\t{entry.sha256}\n" if entry.kind == "file" else f"{entry.path}\t->{entry.target}\n")
    return hashlib.sha256("".join(lines).encode("utf-8", "surrogateescape")).hexdigest()


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


def check_receipt(receipt_path, archive, tag, source_sha, limits):
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
    for field in ("archive_sha256", "source_tree_sha256", "notice_sha256"):
        if not isinstance(receipt.get(field), str) or not SHA256_RE.match(receipt[field]):
            raise Reject("receipt-invalid", f"receipt {field} is missing or malformed")
    if not receipt.get("admitted_fixture_identities") or not isinstance(receipt.get("inspected_members"), int) or receipt["inspected_members"] <= 0:
        raise Reject("receipt-invalid", "receipt carries no admitted fixture identities or inspected members")
    fresh = build_receipt(archive, tag, source_sha, None, limits)
    for field in ("archive_sha256", "source_tree_sha256", "notice_sha256", "archive_root",
                  "admitted_fixture_identities", "inspected_members"):
        if receipt.get(field) != fresh[field]:
            raise Reject("receipt-invalid", f"receipt {field} does not match the archive bytes")
    return receipt


def collect_third_party_digests(repo_root):
    digests = set()
    fixtures = pathlib.Path(repo_root) / "fixtures"
    for directory in sorted(fixtures.iterdir()) if fixtures.is_dir() else []:
        if directory.name in PRODUCT_FIXTURES or not directory.is_dir():
            continue
        for doc in DIGEST_DOCS:
            candidate = directory / doc
            if candidate.is_file() and candidate.stat().st_size <= KEEP_LIMIT:
                digests.update(HEX64_RE.findall(candidate.read_text(errors="replace")))
        for rom in directory.rglob("*"):
            if rom.is_file() and rom.name.lower().endswith(ROM_SUFFIXES) and rom.stat().st_size <= MAX_MEMBER_BYTES:
                digests.add(sha256_path(rom))
    return digests


def check_product(archive, repo_root, limits):
    inspection = inspect_archive(archive, limits, unwrapped=True)
    if any(e.kind == "symlink" for e in inspection.entries):
        raise Reject("product-link-not-allowed", "product package contains a link")
    files = inspection.files()
    forbidden = collect_third_party_digests(repo_root) if repo_root else set()
    for path, entry in sorted(files.items()):
        parts = path.split("/")
        in_fixtures = len(parts) > 3 and parts[:3] == ["share", "gabbaboy", "fixtures"]
        if in_fixtures and parts[3] not in PRODUCT_FIXTURES:
            raise Reject("product-fixture-leak", f"product package carries non-product fixture content: {path}")
        if path.lower().endswith(ROM_SUFFIXES) and not (in_fixtures and parts[3] in PRODUCT_FIXTURES):
            raise Reject("product-fixture-leak", f"product package carries a ROM-like file outside the original fixtures: {path}")
        if entry.sha256 in forbidden:
            raise Reject("product-fixture-leak", f"product package carries bytes of an admitted third-party fixture: {path}")
        if parts[0] == "fixtures" or path == NOTICE_NAME:
            raise Reject("product-fixture-leak", f"product package carries source-archive content: {path}")
    for required in PRODUCT_REQUIRED:
        if required not in files:
            raise Reject("product-package-incomplete", f"product package lacks {required} (a source archive is not a product package)")
    return {"inspected_members": len(inspection.entries), "root": inspection.root}


# --------------------------------------------------------------------------- self-test


def tar_bytes(members, commit, root="gabbaboy-0.0.1", fmt=tarfile.PAX_FORMAT):
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
            if isinstance(value, tuple):
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


def synthetic_tree():
    files = {
        "README.md": b"synthetic original tree\n",
        "src/a.c": b"int a(void) { return 1; }\n",
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
        expect_reject("symlink-not-in-tree", "link-not-allowed", write("p6.tar.gz", tar_bytes({**base, "link": ("symlink", "/etc/passwd")}, sha)))
        expect_reject("hardlink-member", "link-not-allowed", write("p7.tar.gz", tar_bytes({**base, "hard": ("hardlink", "README.md")}, sha)))
        expect_reject("device-member", "nonregular-member", write("p8.tar.gz", tar_bytes({**base, "dev": ("device", "")}, sha)))
        expect_reject("entry-limit", "too-many-entries", generated, "--max-entries", "3")
        expect_reject("total-size-limit", "archive-oversize", generated, "--max-total-bytes", "64")
        expect_reject("member-size-limit", "member-oversize", generated, "--max-member-bytes", "8")
        expect_reject("path-length-limit", "path-too-long", generated, "--max-path-bytes", "16")
        expect_reject("truncated-gzip", "archive-unreadable", write("t1.tar.gz", generated.read_bytes()[:200]))
        expect_reject("not-an-archive", "archive-unreadable", write("t2.tar.gz", b"plain text, not an archive"))

        # Product package contract: separate from the source archive contract.
        good_product = {
            "include/gabbaboy/gabbaboy.h": b"/* header */\n",
            "share/gabbaboy/fixtures/tracer/manifest.json": b"{}\n",
            "share/gabbaboy/fixtures/tracer/tracer.gb": b"\x00T",
            "share/gabbaboy/fixtures/mbc1-continuation/manifest.json": b"{}\n",
        }

        def expect_product(label, files, expected, root_name=None):
            nonlocal positives, negatives
            archive = write(f"{label}.tar.gz", tar_bytes(files, None, root=root_name))
            code, err, _ = run_cli(script, "--check-product-archive", str(archive))
            if expected is None:
                if code != 0:
                    raise SystemExit(f"self-test product positive {label} failed: {err}")
                positives += 1
                print(f"accepted: {label}")
            else:
                if code != 1 or not err.startswith(f"REJECT {expected}:"):
                    raise SystemExit(f"self-test product negative {label}: expected {expected}, got {code}: {err!r}")
                negatives += 1
                print(f"rejected: {label} ({expected})")

        expect_product("product-fixture-free", good_product, None)
        expect_product("product-wrapped-in-a-source-style-root", good_product, "product-fixture-leak", root_name="stage")
        expect_product("product-with-third-party-fixture", {**good_product, "share/gabbaboy/fixtures/libbet/libbet.gb": b"\x00L"}, "product-fixture-leak")
        expect_product("product-with-renamed-rom", {**good_product, "share/gabbaboy/renamed.gb": b"\x00L"}, "product-fixture-leak")
        expect_product("product-with-notice-table", {**good_product, NOTICE_NAME: b"x"}, "product-fixture-leak")
        expect_product("product-missing-header", {k: v for k, v in good_product.items() if "include" not in k}, "product-package-incomplete")
        code, err, _ = run_cli(script, "--check-product-archive", str(generated))
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
        good = scratch / "generated-without-repo.receipt.json"
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

        receipt_cases = {
            "wrong-kind": lambda r: r.update(kind="gabbaboy-build-receipt"),
            "wrong-tag": lambda r: r.update(tag="v9.9.9"),
            "wrong-sha": lambda r: r.update(source_sha="d" * 40),
            "altered-archive-digest": lambda r: r.update(archive_sha256="0" * 64),
            "no-fixture-identities": lambda r: r.update(admitted_fixture_identities=[]),
            "altered-notice-digest": lambda r: r.update(notice_sha256="0" * 64),
        }
        plain = scratch / "plain.tar.gz"
        code, err, _ = run_cli(script, "--check-receipt", str(good), "--archive", str(plain), "--tag", tag, "--source-sha", sha)
        if code != 0:
            raise SystemExit(f"self-test receipt positive failed: {err}")
        positives += 1
        print("accepted: receipt bound to the archive bytes")

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
            code, err, _ = run_cli(script, "--check-receipt", str(path), "--archive", str(plain), "--tag", tag, "--source-sha", sha)
            if code != 1 or not err.startswith("REJECT receipt-invalid:"):
                raise SystemExit(f"self-test receipt negative {label}: got {code}: {err!r}")
            negatives += 1
            print(f"rejected: receipt {label}")

        # Real tree: archive the committed repository at a private tag in a private clone.
        root = script.parents[2]
        if (root / ".git").exists():
            clone = scratch / "clone"
            subprocess.run(["git", "clone", "-q", "--no-hardlinks", str(root), str(clone)], capture_output=True, check=False)
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
    parser.add_argument("--archive")
    parser.add_argument("--tag")
    parser.add_argument("--source-sha")
    parser.add_argument("--output")
    parser.add_argument("--repo")
    parser.add_argument("--check-receipt")
    parser.add_argument("--check-product-archive")
    parser.add_argument("--repo-root")
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
        elif args.check_product_archive:
            result = check_product(args.check_product_archive, args.repo_root, limits)
            print(f"PASS: product package is fixture-free ({result['inspected_members']} members)")
        elif args.check_receipt:
            if not (args.archive and args.tag and args.source_sha):
                parser.error("--check-receipt needs --archive, --tag and --source-sha")
            check_receipt(args.check_receipt, args.archive, args.tag, args.source_sha, limits)
            print("PASS: source archive receipt matches the archive bytes")
        elif args.archive:
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
