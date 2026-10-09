#!/usr/bin/env python3
"""Create a sorted tar.gz archive with stable ownership and timestamps."""

from __future__ import annotations

import gzip
import hashlib
import os
import pathlib
import tempfile
import tarfile
import sys


def create_archive(stage: pathlib.Path, archive: pathlib.Path, epoch: int) -> None:
    stage = stage.resolve(strict=True)
    archive.parent.mkdir(parents=True, exist_ok=True)
    with archive.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=epoch, compresslevel=9) as compressed:
            with tarfile.open(fileobj=compressed, mode="w", format=tarfile.PAX_FORMAT) as bundle:
                for top in ("bin", "include", "lib", "share"):
                    root = stage / top
                    if not root.exists():
                        raise ValueError(f"archive input is missing required directory: {top}")
                    paths = [root]
                    for current, directories, files in os.walk(root, followlinks=False):
                        current_path = pathlib.Path(current)
                        directories.sort()
                        files.sort()
                        paths.extend(current_path / name for name in directories)
                        paths.extend(current_path / name for name in files)
                    for path in sorted(paths, key=lambda item: item.relative_to(stage).as_posix()):
                        relative = path.relative_to(stage).as_posix()
                        info = bundle.gettarinfo(str(path), arcname=relative)
                        info.uid = 0
                        info.gid = 0
                        info.uname = ""
                        info.gname = ""
                        info.mtime = epoch
                        if info.isfile():
                            with path.open("rb") as source:
                                bundle.addfile(info, source)
                        else:
                            bundle.addfile(info)


def self_test() -> None:
    epoch = 1_700_000_000
    with tempfile.TemporaryDirectory(prefix="gabbaboy-deterministic-archive-") as temporary:
        root = pathlib.Path(temporary)
        stage = root / "stage"
        archive_a, archive_b = root / "a.tar.gz", root / "b.tar.gz"
        for directory in ("include", "lib", "bin", "share"):
            (stage / directory).mkdir(parents=True)
        executable = stage / "bin/gabbaboy-runner"
        executable.write_bytes(b"stable executable bytes\n")
        executable.chmod(0o755)
        (stage / "include/gabbaboy.h").write_bytes(b"header bytes\n")
        (stage / "lib/libgabbaboy.a").write_bytes(b"library bytes\n")
        (stage / "share/notice.txt").write_bytes(b"notice bytes\n")
        (stage / "bin/runner-link").symlink_to("gabbaboy-runner")
        create_archive(stage, archive_a, epoch)
        create_archive(stage, archive_b, epoch)
        if hashlib.sha256(archive_a.read_bytes()).digest() != hashlib.sha256(archive_b.read_bytes()).digest():
            raise SystemExit("deterministic archive self-test produced different bytes for the same input")
        with tarfile.open(archive_a, "r:gz") as bundle:
            members = bundle.getmembers()
            names = [member.name for member in members]
            if names != sorted(names):
                raise SystemExit("archive self-test found entries outside sorted order")
            for member in members:
                if (member.uid, member.gid, member.uname, member.gname, member.mtime) != (0, 0, "", "", epoch):
                    raise SystemExit(f"archive self-test found non-normalized metadata: {member.name}")
            runner = bundle.getmember("bin/gabbaboy-runner")
            link = bundle.getmember("bin/runner-link")
            if runner.mode & 0o777 != 0o755 or link.issym() is False or link.linkname != "gabbaboy-runner":
                raise SystemExit("archive self-test failed to preserve file mode or symlink metadata")
            if bundle.extractfile("include/gabbaboy.h").read() != b"header bytes\n":
                raise SystemExit("archive self-test failed to preserve file contents")


def main(arguments: list[str]) -> int:
    if arguments == ["--self-test"]:
        self_test()
        print("PASS: deterministic archive bytes, normalized metadata, modes, symlinks, and content")
        return 0
    if len(arguments) != 2:
        raise SystemExit("usage: create-deterministic-archive.py STAGE_DIR OUTPUT.tar.gz | --self-test")
    epoch_text = os.environ.get("SOURCE_DATE_EPOCH", "")
    if not epoch_text.isdigit():
        raise SystemExit("SOURCE_DATE_EPOCH must be a non-negative integer")
    create_archive(pathlib.Path(arguments[0]), pathlib.Path(arguments[1]), int(epoch_text))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
