#!/usr/bin/env python3
"""Validate and extract the regular-file installed-prefix from a package tarball."""

import io
import os
from pathlib import Path, PurePosixPath
import stat
import sys
import tarfile


def checked_name(member):
    raw = member.name
    if not raw or raw.startswith("/") or "\\" in raw:
        raise ValueError(f"unsafe archive path: {raw!r}")
    parts = raw.split("/")
    if parts[-1] == "":
        parts.pop()
    if not parts or any(part in ("", ".", "..") for part in parts):
        raise ValueError(f"unsafe archive path: {raw!r}")
    if parts[0].endswith(":") or parts[0] != "installed-prefix":
        raise ValueError(f"archive path is outside installed-prefix: {raw!r}")
    if member.type not in (tarfile.REGTYPE, tarfile.AREGTYPE, tarfile.DIRTYPE):
        raise ValueError(f"unsupported archive entry type: {raw!r}")
    return PurePosixPath(*parts)


def validate_members(members):
    paths = {}
    for member in members:
        path = checked_name(member)
        key = path.as_posix()
        if key in paths:
            raise ValueError(f"duplicate archive path: {key!r}")
        paths[key] = member

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
    root = Path(destination)
    if root.is_symlink():
        raise ValueError("destination must not be a symbolic link")
    if root.exists() and any(root.iterdir()):
        raise ValueError("destination must be an empty directory")
    root.mkdir(parents=True, exist_ok=True)

    with tarfile.open(archive_path, mode="r:gz") as archive:
        paths = validate_members(archive.getmembers())

        for key, member in paths.items():
            target = root.joinpath(*PurePosixPath(key).parts)
            parent = target.parent
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
                while True:
                    chunk = source.read(1024 * 1024)
                    if not chunk:
                        break
                    output.write(chunk)


def self_test():
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
    ]
    for entries in cases:
        try:
            with tarfile.open(fileobj=io.BytesIO(archive_bytes(entries)), mode="r:gz") as archive:
                validate_members(archive.getmembers())
        except ValueError:
            continue
        raise AssertionError(f"unsafe archive accepted: {entries!r}")
    print("PASS safe package extraction adversarial validation")


if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "--self-test":
        self_test()
    elif len(sys.argv) == 3:
        extract(sys.argv[1], sys.argv[2])
    else:
        raise SystemExit("usage: safe_extract_package.py ARCHIVE DESTINATION | --self-test")
