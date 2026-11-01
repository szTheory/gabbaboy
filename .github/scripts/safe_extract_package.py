#!/usr/bin/env python3
"""Validate and extract the regular-file installed-prefix from a package tarball."""

import gzip
import io
import os
from contextlib import contextmanager
from pathlib import Path, PurePosixPath
import stat
import sys
import tarfile
from types import SimpleNamespace


# Preview archives are currently only a few MiB. These documented ceilings
# leave substantial headroom while bounding parsing, disk use, and copy work.
MAX_COMPRESSED_BYTES = 64 * 1024 * 1024
MAX_MEMBERS = 4096
# Preview prefixes are shallow; this cap bounds ancestry validation for hostile paths.
MAX_PATH_COMPONENTS = 64
MAX_EXPANDED_BYTES = 512 * 1024 * 1024
MAX_ARCHIVE_STREAM_BYTES = 576 * 1024 * 1024
MAX_EXTENSION_HEADERS = 8192
MAX_EXTENSION_BYTES = 64 * 1024
MAX_TOTAL_EXTENSION_BYTES = 8 * 1024 * 1024
MAX_TAR_READ_BYTES = 64 * 1024
COPY_CHUNK_BYTES = 1024 * 1024


class BoundedReader:
    """Limit bytes exposed from a decompressor to the tar parser."""

    def __init__(self, source, limit=MAX_ARCHIVE_STREAM_BYTES, max_request=MAX_TAR_READ_BYTES):
        self.source = source
        self.limit = limit
        self.max_request = max_request
        self.bytes_read = 0

    def read(self, size=-1):
        if size is None or size < 0:
            raise ValueError("unbounded reads are not allowed from the archive stream")
        if size == 0:
            return b""
        remaining = self.limit - self.bytes_read
        request_size = min(size, self.max_request, remaining + 1)
        data = self.source.read(request_size)
        if len(data) > remaining:
            raise ArchiveLimitError("stream", f"tar stream exceeds {self.limit}-byte decompressed-archive limit")
        self.bytes_read += len(data)
        return data


class ArchiveLimitError(ValueError):
    def __init__(self, reason, detail):
        super().__init__(detail)
        self.reason = reason


def bounded_tarinfo_class(*, extension_headers=MAX_EXTENSION_HEADERS,
                          extension_bytes=MAX_EXTENSION_BYTES,
                          total_extension_bytes=MAX_TOTAL_EXTENSION_BYTES):
    """Reject excessive hidden PAX/GNU metadata before tarfile reads it."""
    stats = {"headers": 0, "bytes": 0}
    extension_types = (
        tarfile.GNUTYPE_LONGNAME,
        tarfile.GNUTYPE_LONGLINK,
        tarfile.GNUTYPE_SPARSE,
        tarfile.XHDTYPE,
        tarfile.XGLTYPE,
        tarfile.SOLARIS_XHDTYPE,
    )

    class BoundedTarInfo(tarfile.TarInfo):
        def _proc_member(self, archive):
            if self.type in extension_types:
                if self.size < 0 or self.size > extension_bytes:
                    raise ArchiveLimitError("extension-header", f"extended tar header exceeds {extension_bytes}-byte limit")
                if stats["headers"] + 1 > extension_headers:
                    raise ArchiveLimitError("extension-count", f"archive exceeds {extension_headers} extended-header limit")
                if stats["bytes"] + self.size > total_extension_bytes:
                    raise ArchiveLimitError("extension-total", f"archive exceeds {total_extension_bytes} aggregate extended-header limit")
                stats["headers"] += 1
                stats["bytes"] += self.size
            return super()._proc_member(archive)

    return BoundedTarInfo


@contextmanager
def open_bounded_tar(archive_path, *, stream_limit=MAX_ARCHIVE_STREAM_BYTES,
                     extension_headers=MAX_EXTENSION_HEADERS,
                     extension_bytes=MAX_EXTENSION_BYTES,
                     total_extension_bytes=MAX_TOTAL_EXTENSION_BYTES,
                     max_request=MAX_TAR_READ_BYTES):
    with Path(archive_path).open("rb") as compressed_file:
        with gzip.GzipFile(fileobj=compressed_file, mode="rb") as decompressed_file:
            bounded_file = BoundedReader(decompressed_file, limit=stream_limit, max_request=max_request)
            with tarfile.open(
                fileobj=bounded_file,
                mode="r|",
                tarinfo=bounded_tarinfo_class(extension_headers=extension_headers,
                                              extension_bytes=extension_bytes,
                                              total_extension_bytes=total_extension_bytes),
            ) as archive:
                yield archive, bounded_file


def checked_name(member):
    raw = member.name
    if not raw or raw.startswith("/") or "\\" in raw:
        raise ValueError(f"unsafe archive path: {raw!r}")
    component_count = raw.count("/") + (0 if raw.endswith("/") else 1)
    if component_count > MAX_PATH_COMPONENTS:
        raise ValueError(f"archive path exceeds {MAX_PATH_COMPONENTS}-component limit: {raw!r}")
    parts = raw.split("/")
    if parts[-1] == "":
        parts.pop()
    if not parts or any(part in ("", ".", "..") for part in parts):
        raise ValueError(f"unsafe archive path: {raw!r}")
    if any(":" in part for part in parts):
        raise ValueError(f"unsafe Windows drive or stream syntax in archive path: {raw!r}")
    if parts[0] != "installed-prefix":
        raise ValueError(f"archive path is outside installed-prefix: {raw!r}")
    if member.type not in (tarfile.REGTYPE, tarfile.AREGTYPE, tarfile.DIRTYPE):
        raise ValueError(f"unsupported archive entry type: {raw!r}")
    return PurePosixPath(*parts)


def require_target_inside_root(root, target, name):
    """Reject native path joins that escape the extraction root."""
    try:
        target.relative_to(root)
    except ValueError as error:
        raise ValueError(f"archive target is outside extraction root: {name!r}") from error
    return target


def validate_members(members):
    paths = {}
    declared_total = 0
    for member in members:
        if len(paths) >= MAX_MEMBERS:
            raise ValueError(f"archive has more than {MAX_MEMBERS} members")
        if member.size < 0:
            raise ValueError(f"negative archive member size: {member.name!r}")
        if member.size > MAX_EXPANDED_BYTES:
            raise ValueError(f"archive member exceeds {MAX_EXPANDED_BYTES} expanded-byte limit: {member.name!r}")
        if declared_total > MAX_EXPANDED_BYTES - member.size:
            raise ValueError(f"archive exceeds {MAX_EXPANDED_BYTES} aggregate expanded-byte limit")
        path = checked_name(member)
        key = path.as_posix()
        if key in paths:
            raise ValueError(f"duplicate archive path: {key!r}")
        paths[key] = member
        declared_total += member.size

    prefix = paths.get("installed-prefix")
    if prefix is None or prefix.type != tarfile.DIRTYPE:
        raise ValueError("archive has no installed-prefix directory")
    for key in paths:
        parts = PurePosixPath(key).parts
        for index in range(1, len(parts)):
            parent = PurePosixPath(*parts[:index]).as_posix()
            parent_member = paths.get(parent)
            if parent_member is not None and parent_member.type != tarfile.DIRTYPE:
                raise ValueError(f"archive path descends through non-directory: {parent!r}")
    return paths


def extract(archive_path, destination):
    archive_file = Path(archive_path)
    compressed_size = archive_file.stat().st_size
    if compressed_size > MAX_COMPRESSED_BYTES:
        raise ValueError(f"compressed archive exceeds {MAX_COMPRESSED_BYTES}-byte limit")
    root = Path(destination)
    if root.is_symlink():
        raise ValueError("destination must not be a symbolic link")
    if root.exists() and any(root.iterdir()):
        raise ValueError("destination must be an empty directory")
    root.mkdir(parents=True, exist_ok=True)
    root = root.resolve()

    # Validate all visible names/types before writing anything. The tar parser
    # itself is fed through a bounded gzip stream, including hidden metadata and
    # padding that TarInfo.size does not account for.
    with open_bounded_tar(archive_file) as (archive, _bounded_file):
        paths = validate_members(iter(archive))

    # A second bounded pass is needed because streaming tar mode cannot seek back
    # to extract members after full-archive validation.
    with open_bounded_tar(archive_file) as (archive, bounded_file):
        copied_total = 0
        seen = set()
        for member in archive:
            key = checked_name(member).as_posix()
            expected = paths.get(key)
            if expected is None or (member.type, member.size) != (expected.type, expected.size):
                raise ValueError(f"archive changed between validation and extraction: {key!r}")
            seen.add(key)
            parts = PurePosixPath(key).parts
            target = root.joinpath(*parts)
            # Windows can reinterpret a later drive-relative component during a
            # native join. Resolve and prove containment before mkdir/open.
            target = require_target_inside_root(root, target.resolve(strict=False), key)
            parent = target.parent
            current = root
            for part in parts[:-1]:
                current = current / part
                if os.path.lexists(current) and not stat.S_ISDIR(os.lstat(current).st_mode):
                    raise ValueError(f"non-directory extraction parent: {current}")
            parent.mkdir(parents=True, exist_ok=True)
            # The destination is fresh/private. Still check every parent to prevent
            # extraction from following an unexpected link if that assumption fails.
            current = root
            for part in PurePosixPath(key).parts[:-1]:
                current = current / part
                if not stat.S_ISDIR(os.lstat(current).st_mode):
                    raise ValueError(f"non-directory extraction parent: {current}")
            if member.type == tarfile.DIRTYPE:
                target.mkdir(exist_ok=True)
                if not stat.S_ISDIR(os.lstat(target).st_mode):
                    raise ValueError(f"non-directory destination: {target}")
                continue
            source = archive.extractfile(member)
            if source is None:
                raise ValueError(f"could not read regular file: {key!r}")
            flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
            if hasattr(os, "O_NOFOLLOW"):
                flags |= os.O_NOFOLLOW
            fd = os.open(target, flags, 0o755 if member.mode & 0o111 else 0o644)
            with os.fdopen(fd, "wb") as output, source:
                copied_member = 0
                while True:
                    # Read at most one byte beyond the declared length so an
                    # unexpected overlong stream is rejected before writing it.
                    remaining = member.size - copied_member
                    chunk = source.read(min(COPY_CHUNK_BYTES, remaining + 1))
                    if not chunk:
                        break
                    copied_member += len(chunk)
                    copied_total += len(chunk)
                    if copied_member > member.size:
                        raise ValueError(f"archive member exceeds declared size: {key!r}")
                    if copied_total > MAX_EXPANDED_BYTES:
                        raise ValueError(f"archive exceeds {MAX_EXPANDED_BYTES} aggregate expanded-byte limit")
                    output.write(chunk)
                if copied_member != member.size:
                    raise ValueError(
                        f"archive member size mismatch for {key!r}: declared {member.size}, copied {copied_member}"
                    )
        if seen != set(paths):
            raise ValueError("archive changed between validation and extraction")
        if bounded_file.bytes_read > MAX_ARCHIVE_STREAM_BYTES:
            raise ValueError(f"tar stream exceeds {MAX_ARCHIVE_STREAM_BYTES}-byte decompressed-archive limit")


def self_test():
    import tempfile
    from pathlib import PureWindowsPath
    from unittest.mock import patch

    completed_controls = []

    def expect_rejection(label, members):
        try:
            validate_members(members)
        except ValueError:
            return
        raise AssertionError(f"{label} accepted")

    def archive_bytes(entries):
        data = io.BytesIO()
        with tarfile.open(fileobj=data, mode="w:gz") as archive:
            for name, kind, linkname in entries:
                info = tarfile.TarInfo(name)
                if kind == "dir":
                    info.type = tarfile.DIRTYPE
                elif kind == "symlink":
                    info.type = tarfile.SYMTYPE
                    info.linkname = linkname
                elif kind == "hardlink":
                    info.type = tarfile.LNKTYPE
                    info.linkname = linkname
                elif kind == "fifo":
                    info.type = tarfile.FIFOTYPE
                    archive.addfile(info)
                    continue
                else:
                    body = b"x"
                    info.size = len(body)
                    archive.addfile(info, io.BytesIO(body))
                    continue
                archive.addfile(info)
        return data.getvalue()

    cases = [
        [("installed-prefix/", "dir", ""), ("installed-prefix/link", "symlink", "../../outside"),
         ("installed-prefix/link/pwn", "file", "")],
        [("installed-prefix/", "dir", ""), ("installed-prefix/hard", "hardlink", "../../outside")],
        [("installed-prefix/", "dir", ""), ("installed-prefix/special", "fifo", "")],
        [("installed-prefix/", "dir", ""), ("installed-prefix/../outside", "file", "")],
        [("installed-prefix/", "dir", ""), ("/installed-prefix/absolute", "file", "")],
        [("installed-prefix/", "dir", ""), ("other/file", "file", "")],
        [("installed-prefix/", "dir", ""), ("installed-prefix/a", "file", ""),
         ("installed-prefix/a", "file", "")],
        [("installed-prefix/", "dir", ""), ("installed-prefix/a", "file", ""),
         ("installed-prefix/a/b", "file", "")],
        [("installed-prefix/", "dir", ""), ("installed-prefix/D:escape/payload", "file", "")],
        [("installed-prefix/", "dir", ""), ("installed-prefix/share:stream/file", "file", "")],
        [("installed-prefix/", "dir", ""), ("installed-prefix/share/file:stream", "file", "")],
    ]
    for entries in cases:
        try:
            compressed = io.BytesIO(archive_bytes(entries))
            with gzip.GzipFile(fileobj=compressed, mode="rb") as decompressed:
                bounded = BoundedReader(decompressed)
                with tarfile.open(
                    fileobj=bounded,
                    mode="r|",
                    tarinfo=bounded_tarinfo_class(),
                ) as archive:
                    validate_members(iter(archive))
        except ValueError:
            continue
        raise AssertionError(f"unsafe archive accepted: {entries!r}")
    completed_controls.append("reusable extractor drive/ADS path rejection")

    windows_root = PureWindowsPath("C:/temporary/extraction")
    normal_target = windows_root.joinpath("installed-prefix", "share", "notes.txt")
    require_target_inside_root(windows_root, normal_target, "installed-prefix/share/notes.txt")
    escaped_target = windows_root.joinpath("installed-prefix", "D:escape", "payload")
    try:
        require_target_inside_root(windows_root, escaped_target, "installed-prefix/D:escape/payload")
    except ValueError:
        pass
    else:
        raise AssertionError("Windows drive-relative join escaped the extraction root")
    completed_controls.append("reusable extractor cross-drive containment")

    def expect_injected_escape_rejection(member_name, outside_name, member_kind):
        with tempfile.TemporaryDirectory(prefix="safe-extract-self-test-") as temporary:
            base = Path(temporary)
            destination = base / "destination"
            archive_path = base / "input.tar.gz"
            outside_parent = base / "outside"
            outside_parent.mkdir()
            sentinel = outside_parent / "sentinel"
            sentinel.write_bytes(b"unchanged")
            outside_target = outside_parent / outside_name
            archive_path.write_bytes(archive_bytes([
                ("installed-prefix/", "dir", ""),
                (member_name, member_kind, ""),
            ]))
            member_parts = PurePosixPath(member_name).parts
            resolved_destination = destination.resolve()
            path_type = type(destination)
            original_joinpath = path_type.joinpath
            original_mkdir = path_type.mkdir
            original_open = os.open
            attempted = []

            def injected_joinpath(self, *segments):
                if self == resolved_destination and tuple(segments) == member_parts:
                    return outside_target
                return original_joinpath(self, *segments)

            def monitored_mkdir(self, *args, **kwargs):
                if self in (outside_parent, outside_target):
                    attempted.append(f"mkdir:{self}")
                    raise AssertionError(f"outside mkdir attempted: {self}")
                return original_mkdir(self, *args, **kwargs)

            def monitored_open(path, flags, *args, **kwargs):
                if Path(path) == outside_target:
                    attempted.append(f"open:{path}")
                    raise AssertionError(f"outside file open attempted: {path}")
                return original_open(path, flags, *args, **kwargs)

            with patch.object(path_type, "joinpath", new=injected_joinpath), \
                 patch.object(path_type, "mkdir", new=monitored_mkdir), \
                 patch.object(os, "open", new=monitored_open):
                try:
                    extract(archive_path, destination)
                except ValueError as error:
                    if "outside extraction root" not in str(error):
                        raise AssertionError(f"wrong containment rejection: {error}") from error
                else:
                    raise AssertionError(f"injected outside {member_kind} target was accepted")

            if attempted:
                raise AssertionError(f"outside filesystem operation was attempted: {attempted!r}")
            if outside_target.exists() or sentinel.read_bytes() != b"unchanged":
                raise AssertionError("injected containment control changed outside data")
        return True

    expect_injected_escape_rejection("installed-prefix/outside-dir/", "escaped-dir", "dir")
    completed_controls.append("reusable extractor directory containment before create")
    expect_injected_escape_rejection("installed-prefix/outside-file", "escaped-file", "file")
    completed_controls.append("reusable extractor regular-file containment before open")

    root = SimpleNamespace(name="installed-prefix/", type=tarfile.DIRTYPE, size=0)
    too_many = [root] + [
        SimpleNamespace(name=f"installed-prefix/f{i}", type=tarfile.REGTYPE, size=0)
        for i in range(MAX_MEMBERS)
    ]
    expect_rejection("member-count limit", too_many)

    too_deep = [
        root,
        SimpleNamespace(
            name="installed-prefix/" + "/".join(f"d{i}" for i in range(MAX_PATH_COMPONENTS)),
            type=tarfile.REGTYPE,
            size=0,
        ),
    ]
    expect_rejection("path-depth limit", too_deep)

    over_total = [
        root,
        SimpleNamespace(name="installed-prefix/a", type=tarfile.REGTYPE, size=MAX_EXPANDED_BYTES // 2),
        SimpleNamespace(name="installed-prefix/b", type=tarfile.REGTYPE, size=MAX_EXPANDED_BYTES // 2 + 1),
    ]
    expect_rejection("aggregate-size limit", over_total)

    source = io.BytesIO(b"decompressed bytes beyond cap")
    requests = []

    class RequestTracker:
        def read(self, size):
            requests.append(size)
            return source.read(size)

    bounded = BoundedReader(RequestTracker(), limit=16, max_request=8)
    try:
        bounded.read()
    except ValueError:
        if source.tell() != 0:
            raise AssertionError("bounded reader consumed input for an unbounded read")
    else:
        raise AssertionError("bounded reader accepted an unbounded read")
    try:
        while True:
            bounded.read(1024)
    except ValueError:
        if source.tell() != 17:
            raise AssertionError(f"bounded reader consumed {source.tell()} bytes, expected at most 17")
        if max(requests) > 8:
            raise AssertionError(f"bounded reader requested {max(requests)} bytes, expected at most 8")
    else:
        raise AssertionError("decompressed-stream limit accepted excess bytes")
    print(
        "PASS safe package extraction adversarial validation (drive/ADS paths, target containment, member count, "
        "path depth, aggregate size, and decompressed stream bounds)"
    )
    return tuple(completed_controls)


if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "--self-test":
        self_test()
    elif len(sys.argv) == 3:
        extract(sys.argv[1], sys.argv[2])
    else:
        raise SystemExit("usage: safe_extract_package.py ARCHIVE DESTINATION | --self-test")
