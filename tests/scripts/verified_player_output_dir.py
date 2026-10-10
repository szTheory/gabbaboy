#!/usr/bin/env python3
"""Prepare a verified player artifact directory without deleting caller data."""

from pathlib import Path
import hashlib
import json
import os
import secrets
import stat
import sys


OUTPUT_NAMES = (
    "gabbaboy-preview-macos-arm64.tar.gz",
    "verified-receipt.json",
)
_HAS_DIRFD_OPEN = os.open in os.supports_dir_fd
_HAS_DIRFD_UNLINK = os.unlink in os.supports_dir_fd
_HAS_DIRFD_LINK = os.link in os.supports_dir_fd
_HAS_LINK_NOFOLLOW = os.link in os.supports_follow_symlinks


def _paths_overlap(left: Path, right: Path) -> bool:
    return left == right or left in right.parents or right in left.parents


def _is_within(path: Path, parent: Path) -> bool:
    return path == parent or parent in path.parents


def _open_directory(path: Path) -> int:
    directory_flag = getattr(os, "O_DIRECTORY", 0)
    nofollow_flag = getattr(os, "O_NOFOLLOW", 0)
    if (
        not directory_flag
        or not nofollow_flag
        or not _HAS_DIRFD_OPEN
        or not _HAS_DIRFD_UNLINK
    ):
        raise OSError("safe directory-relative cleanup is unavailable on this platform")

    flags = os.O_RDONLY | directory_flag
    descriptor = os.open(path.anchor, flags)
    try:
        for component in path.parts[1:]:
            next_descriptor = os.open(
                component,
                flags | nofollow_flag,
                dir_fd=descriptor,
            )
            os.close(descriptor)
            descriptor = next_descriptor
        return descriptor
    except BaseException:
        os.close(descriptor)
        raise


def _path_matches_directory(path: Path, descriptor: int) -> bool:
    try:
        path_info = os.stat(path, follow_symlinks=False)
    except FileNotFoundError:
        return False
    descriptor_info = os.fstat(descriptor)
    return stat.S_ISDIR(path_info.st_mode) and os.path.samestat(
        path_info, descriptor_info
    )


def _prepare_output_dir(
    repository_root: str, candidate_dir: str, requested_dir: str
):
    root = Path(repository_root).resolve()
    candidate = Path(candidate_dir).resolve()
    output_dir = Path(requested_dir).resolve()
    if _paths_overlap(output_dir, candidate):
        raise ValueError("output directory must be separate from the candidate directory")
    if output_dir == Path(output_dir.anchor) or _is_within(output_dir, root):
        raise ValueError("output directory must be outside the filesystem and repository roots")

    output_dir.mkdir(parents=True, exist_ok=True)
    output_dir = output_dir.resolve()
    if _paths_overlap(output_dir, candidate):
        raise ValueError("output directory must be separate from the candidate directory")
    if output_dir == Path(output_dir.anchor) or _is_within(output_dir, root):
        raise ValueError("output directory must be outside the filesystem and repository roots")

    descriptor = _open_directory(output_dir)
    try:
        if not _path_matches_directory(output_dir, descriptor):
            raise ValueError("output directory changed during validation")

        for name in OUTPUT_NAMES:
            try:
                target_info = os.stat(
                    name, dir_fd=descriptor, follow_symlinks=False
                )
            except FileNotFoundError:
                continue
            if stat.S_ISDIR(target_info.st_mode):
                raise ValueError(f"artifact destination is a directory: {name}")

        for name in OUTPUT_NAMES:
            try:
                os.unlink(name, dir_fd=descriptor)
            except FileNotFoundError:
                pass

        if not _path_matches_directory(output_dir, descriptor):
            raise ValueError("output directory changed during cleanup")
        return output_dir, descriptor
    except BaseException:
        os.close(descriptor)
        raise


def prepare_output_dir(
    repository_root: str, candidate_dir: str, requested_dir: str
) -> Path:
    output_dir, descriptor = _prepare_output_dir(
        repository_root, candidate_dir, requested_dir
    )
    os.close(descriptor)
    return output_dir


def _publish_new_artifact(descriptor: int, name: str, write_content):
    """Publish a new artifact name; return the writer result and published inode."""
    if not _HAS_DIRFD_LINK or not _HAS_LINK_NOFOLLOW:
        raise OSError("safe directory-relative artifact publication is unavailable")

    temporary_name = None
    temporary_fd = None
    for _ in range(8):
        temporary_name = f".{name}.{secrets.token_hex(12)}.tmp"
        try:
            temporary_fd = os.open(
                temporary_name,
                os.O_WRONLY
                | os.O_CREAT
                | os.O_EXCL
                | getattr(os, "O_NOFOLLOW", 0),
                0o600,
                dir_fd=descriptor,
            )
            break
        except FileExistsError:
            continue
    if temporary_fd is None or temporary_name is None:
        raise FileExistsError("could not allocate a unique artifact temporary file")

    published_info = None
    try:
        with os.fdopen(temporary_fd, "wb") as stream:
            result = write_content(stream)
            stream.flush()
            os.fsync(stream.fileno())
            temporary_info = os.fstat(stream.fileno())
        os.link(
            temporary_name,
            name,
            src_dir_fd=descriptor,
            dst_dir_fd=descriptor,
            follow_symlinks=False,
        )
        current_info = os.stat(name, dir_fd=descriptor, follow_symlinks=False)
        if not stat.S_ISREG(current_info.st_mode) or not os.path.samestat(
            temporary_info, current_info
        ):
            # The name no longer refers to our file, so it is not ours to remove.
            raise OSError("published artifact does not match its verified temporary file")
        published_info = current_info
        os.unlink(temporary_name, dir_fd=descriptor)
        os.fsync(descriptor)
        return result, published_info
    except BaseException:
        # Cleanup is best effort; the original failure is what the caller sees.
        if published_info is not None:
            try:
                _withdraw_artifact(descriptor, name, published_info)
            except OSError as error:
                _report_withdrawal_failure(name, error)
        try:
            os.unlink(temporary_name, dir_fd=descriptor)
        except OSError:
            pass
        raise


def _report_withdrawal_failure(name: str, error: OSError) -> None:
    """Name an artifact that may remain published after a failed publication.

    The caller re-raises the original failure, so this must not replace it;
    it only tells the operator that the output set may be incomplete.
    """
    try:
        print(
            f"warning: could not withdraw published {name}: {error}; "
            "the output directory may hold an incomplete artifact set",
            file=sys.stderr,
        )
    except (OSError, ValueError):
        # A closed or broken stderr must not replace the publication error.
        pass


def _withdraw_artifact(descriptor: int, name: str, published_info) -> None:
    """Remove a published name if it still names this operation's inode.

    A failed publication must not leave an archive without its receipt. A file
    that replaced ours before the identity check is kept; POSIX has no
    unlink-by-inode, so a replacement between the check and the unlink can
    still be removed. Publication only targets the two fixed artifact names.
    """
    try:
        current_info = os.stat(name, dir_fd=descriptor, follow_symlinks=False)
    except FileNotFoundError:
        return
    if os.path.samestat(current_info, published_info):
        os.unlink(name, dir_fd=descriptor)
        os.fsync(descriptor)


def publish_verified_artifacts(
    repository_root: str,
    candidate_dir: str,
    requested_dir: str,
    archive_source: str,
    expected_archive_sha256: str,
    receipt_fields: dict,
) -> Path:
    candidate = Path(candidate_dir).resolve()
    archive = Path(archive_source).resolve(strict=True)
    if archive.parent != candidate or not archive.is_file():
        raise ValueError("candidate archive must be a regular file directly inside the candidate directory")
    if (
        len(expected_archive_sha256) != 64
        or any(character not in "0123456789abcdef" for character in expected_archive_sha256)
    ):
        raise ValueError("expected archive SHA-256 must be 64 lowercase hexadecimal characters")

    output_dir, output_descriptor = _prepare_output_dir(
        repository_root, candidate_dir, requested_dir
    )
    candidate_descriptor = None
    try:
        candidate_descriptor = _open_directory(candidate)
        if not _path_matches_directory(candidate, candidate_descriptor):
            raise ValueError("candidate directory changed during validation")
        source_descriptor = os.open(
            archive.name,
            os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0),
            dir_fd=candidate_descriptor,
        )
        try:
            if not stat.S_ISREG(os.fstat(source_descriptor).st_mode):
                raise ValueError("candidate archive must be a regular file")

            archive_digest = hashlib.sha256()

            def copy_archive(stream) -> str:
                with os.fdopen(os.dup(source_descriptor), "rb") as source:
                    while True:
                        chunk = source.read(1024 * 1024)
                        if not chunk:
                            break
                        archive_digest.update(chunk)
                        stream.write(chunk)
                digest = archive_digest.hexdigest()
                if digest != expected_archive_sha256:
                    raise ValueError("candidate archive changed after package verification")
                return digest

            package_sha256, archive_info = _publish_new_artifact(
                output_descriptor, OUTPUT_NAMES[0], copy_archive
            )
        finally:
            os.close(source_descriptor)
    except BaseException:
        if candidate_descriptor is not None:
            os.close(candidate_descriptor)
        os.close(output_descriptor)
        raise

    # The archive and receipt form one artifact set: any failure from here on
    # withdraws whatever this call already published.
    published = [(OUTPUT_NAMES[0], archive_info)]
    try:
        receipt = {
            "schema_version": 1,
            "result": "passed",
            "source_revision": receipt_fields["source_revision"],
            "build_run_id": receipt_fields["build_run_id"],
            "build_run_attempt": receipt_fields["build_run_attempt"],
            "consumer_run_id": receipt_fields["consumer_run_id"],
            "consumer_run_attempt": receipt_fields["consumer_run_attempt"],
            "build_source_tree_state": receipt_fields["source_tree_state"],
            "package": OUTPUT_NAMES[0],
            "package_sha256": package_sha256,
            "sdl_version": receipt_fields["sdl_version"],
            "sdl_archive_sha256": receipt_fields["sdl_archive_sha256"],
            "sdl_license_sha256": receipt_fields["sdl_license_sha256"],
            "demo_rom_sha256": receipt_fields["demo_rom_sha256"],
            "battery_fixture_sha256": receipt_fields["battery_fixture_sha256"],
            "battery_fixture_source_sha256": receipt_fields[
                "battery_fixture_source_sha256"
            ],
            "smoke": (
                "SDL keyboard events reached the demo guest, extracted package "
                "produced a completed frame, and packaged MBC1 battery progress "
                "resumed in a fresh process"
            ),
            "signed": False,
            "notarized": False,
            "hardware_qualified": False,
        }
        receipt_bytes = (json.dumps(receipt, indent=2, sort_keys=True) + "\n").encode()
        _, receipt_info = _publish_new_artifact(
            output_descriptor,
            OUTPUT_NAMES[1],
            lambda stream: stream.write(receipt_bytes),
        )
        published.append((OUTPUT_NAMES[1], receipt_info))
        if not _path_matches_directory(output_dir, output_descriptor):
            raise ValueError("output directory changed during artifact publication")
        return output_dir
    except BaseException:
        for name, info in reversed(published):
            try:
                _withdraw_artifact(output_descriptor, name, info)
            except OSError as error:
                _report_withdrawal_failure(name, error)
        raise
    finally:
        os.close(candidate_descriptor)
        os.close(output_descriptor)


def main() -> int:
    if len(sys.argv) == 19 and sys.argv[1] == "--publish":
        (
            repository_root,
            candidate_dir,
            output_dir,
            archive_source,
            expected_archive_sha256,
            source_revision,
            build_run_id,
            build_run_attempt,
            consumer_run_id,
            consumer_run_attempt,
            sdl_version,
            sdl_archive_sha256,
            sdl_license_sha256,
            demo_rom_sha256,
            battery_fixture_sha256,
            battery_fixture_source_sha256,
            source_tree_state,
        ) = sys.argv[2:]
        receipt_fields = {
            "source_revision": source_revision,
            "build_run_id": build_run_id,
            "build_run_attempt": build_run_attempt,
            "consumer_run_id": consumer_run_id,
            "consumer_run_attempt": consumer_run_attempt,
            "sdl_version": sdl_version,
            "sdl_archive_sha256": sdl_archive_sha256,
            "sdl_license_sha256": sdl_license_sha256,
            "demo_rom_sha256": demo_rom_sha256,
            "battery_fixture_sha256": battery_fixture_sha256,
            "battery_fixture_source_sha256": battery_fixture_source_sha256,
            "source_tree_state": source_tree_state,
        }
        try:
            print(
                publish_verified_artifacts(
                    repository_root,
                    candidate_dir,
                    output_dir,
                    archive_source,
                    expected_archive_sha256,
                    receipt_fields,
                )
            )
        except (OSError, ValueError, KeyError) as error:
            print(f"ERROR: {error}", file=sys.stderr)
            return 1
        return 0

    if len(sys.argv) != 4:
        print(
            "usage: verified_player_output_dir.py REPOSITORY_ROOT CANDIDATE_DIR OUTPUT_DIR",
            file=sys.stderr,
        )
        return 2
    try:
        print(prepare_output_dir(sys.argv[1], sys.argv[2], sys.argv[3]))
    except (OSError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
