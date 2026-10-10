#!/usr/bin/env python3
"""Regression tests for safe verified-player output directory preparation."""

from pathlib import Path
import contextlib
import hashlib
import io
import json
import os
import re
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import verified_player_output_dir as output_dir_module
from verified_player_output_dir import (
    OUTPUT_NAMES,
    prepare_output_dir,
    publish_verified_artifacts,
)


class VerifiedPlayerOutputDirTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory(prefix="gbb-output-dir-test-")
        self.addCleanup(self.temp_dir.cleanup)
        self.workspace = Path(self.temp_dir.name)
        self.repository = self.workspace / "repository"
        self.repository.mkdir()
        self.candidate = self.workspace / "candidate"
        self.candidate.mkdir()
        self.output = self.workspace / "artifacts"
        self.output.mkdir()

    def test_preserves_unrelated_files_and_replaces_only_expected_artifacts(self) -> None:
        unrelated = self.output / "keep-me.txt"
        unrelated.write_text("owner data\n", encoding="utf-8")
        for name in OUTPUT_NAMES:
            (self.output / name).write_text("stale artifact\n", encoding="utf-8")

        prepared = prepare_output_dir(
            str(self.repository), str(self.candidate), str(self.output)
        )

        self.assertEqual(prepared, self.output.resolve())
        self.assertEqual(unrelated.read_text(encoding="utf-8"), "owner data\n")
        for name in OUTPUT_NAMES:
            self.assertFalse((self.output / name).exists())

    def test_removes_expected_symlink_without_touching_its_target(self) -> None:
        external = self.workspace / "external.txt"
        external.write_text("preserve target\n", encoding="utf-8")
        archive_link = self.output / OUTPUT_NAMES[0]
        try:
            archive_link.symlink_to(external)
        except (NotImplementedError, OSError) as error:
            self.skipTest(f"symlinks are unavailable: {error}")

        prepare_output_dir(
            str(self.repository), str(self.candidate), str(self.output)
        )

        self.assertFalse(archive_link.is_symlink())
        self.assertEqual(external.read_text(encoding="utf-8"), "preserve target\n")

    def test_cleanup_stays_in_open_directory_if_output_path_is_replaced(self) -> None:
        hostile = self.workspace / "hostile"
        hostile.mkdir()
        for name in OUTPUT_NAMES:
            (hostile / name).write_text("preserve redirected target\n", encoding="utf-8")

        probe = self.workspace / "symlink-probe"
        try:
            probe.symlink_to(hostile, target_is_directory=True)
        except (NotImplementedError, OSError) as error:
            self.skipTest(f"directory symlinks are unavailable: {error}")
        probe.unlink()

        original_output = self.workspace / "original-artifacts"
        original_stat = os.stat
        swapped = False

        def replace_path_during_relative_stat(
            path, *, dir_fd=None, follow_symlinks=True
        ):
            nonlocal swapped
            if dir_fd is not None and path == OUTPUT_NAMES[0] and not swapped:
                self.output.rename(original_output)
                self.output.symlink_to(hostile, target_is_directory=True)
                swapped = True
            return original_stat(
                path, dir_fd=dir_fd, follow_symlinks=follow_symlinks
            )

        with patch.object(
            output_dir_module.os, "stat", side_effect=replace_path_during_relative_stat
        ):
            with self.assertRaisesRegex(ValueError, "output directory changed during cleanup"):
                prepare_output_dir(
                    str(self.repository), str(self.candidate), str(self.output)
                )

        self.assertTrue(swapped)
        self.assertTrue(self.output.is_symlink())
        for name in OUTPUT_NAMES:
            self.assertEqual(
                (hostile / name).read_text(encoding="utf-8"),
                "preserve redirected target\n",
            )

    def test_publication_stays_in_open_directory_if_output_path_is_replaced(self) -> None:
        archive_bytes = b"verified candidate package\n"
        archive = self.candidate / "candidate.tar.gz"
        archive.write_bytes(archive_bytes)
        hostile = self.workspace / "hostile-publish-target"
        hostile.mkdir()
        for name in OUTPUT_NAMES:
            (hostile / name).write_text("preserve redirected target\n", encoding="utf-8")

        probe = self.workspace / "publish-symlink-probe"
        try:
            probe.symlink_to(hostile, target_is_directory=True)
        except (NotImplementedError, OSError) as error:
            self.skipTest(f"directory symlinks are unavailable: {error}")
        probe.unlink()

        original_output = self.workspace / "original-publish-output"
        original_link = os.link
        swapped = False

        def replace_path_before_relative_link(
            src, dst, *, src_dir_fd=None, dst_dir_fd=None, follow_symlinks=True
        ):
            nonlocal swapped
            if dst == OUTPUT_NAMES[0] and dst_dir_fd is not None and not swapped:
                self.output.rename(original_output)
                self.output.symlink_to(hostile, target_is_directory=True)
                swapped = True
            return original_link(
                src,
                dst,
                src_dir_fd=src_dir_fd,
                dst_dir_fd=dst_dir_fd,
                follow_symlinks=follow_symlinks,
            )

        receipt_fields = {
            "source_revision": "a" * 40,
            "build_run_id": "build-run",
            "build_run_attempt": "1",
            "consumer_run_id": "consumer-run",
            "consumer_run_attempt": "1",
            "sdl_version": "3.4.18",
            "sdl_archive_sha256": "b" * 64,
            "sdl_license_sha256": "c" * 64,
            "demo_rom_sha256": "d" * 64,
            "battery_fixture_sha256": "e" * 64,
            "battery_fixture_source_sha256": "f" * 64,
            "source_tree_state": "clean",
        }
        with patch.object(output_dir_module.os, "link", side_effect=replace_path_before_relative_link):
            with self.assertRaisesRegex(ValueError, "output directory changed during artifact publication"):
                publish_verified_artifacts(
                    str(self.repository),
                    str(self.candidate),
                    str(self.output),
                    str(archive),
                    hashlib.sha256(archive_bytes).hexdigest(),
                    receipt_fields,
                )

        self.assertTrue(swapped)
        self.assertTrue(self.output.is_symlink())
        for name in OUTPUT_NAMES:
            self.assertEqual(
                (hostile / name).read_text(encoding="utf-8"),
                "preserve redirected target\n",
            )

    def test_publication_receipt_binds_copied_archive_digest(self) -> None:
        archive_bytes = b"verified candidate package\n"
        archive = self.candidate / "candidate.tar.gz"
        archive.write_bytes(archive_bytes)
        receipt_fields = {
            "source_revision": "a" * 40,
            "build_run_id": "build-run",
            "build_run_attempt": "1",
            "consumer_run_id": "consumer-run",
            "consumer_run_attempt": "1",
            "sdl_version": "3.4.18",
            "sdl_archive_sha256": "b" * 64,
            "sdl_license_sha256": "c" * 64,
            "demo_rom_sha256": "d" * 64,
            "battery_fixture_sha256": "e" * 64,
            "battery_fixture_source_sha256": "f" * 64,
            "source_tree_state": "clean",
        }

        prepared = publish_verified_artifacts(
            str(self.repository),
            str(self.candidate),
            str(self.output),
            str(archive),
            hashlib.sha256(archive_bytes).hexdigest(),
            receipt_fields,
        )

        copied_archive = prepared / OUTPUT_NAMES[0]
        receipt = json.loads((prepared / OUTPUT_NAMES[1]).read_text(encoding="utf-8"))
        self.assertEqual(copied_archive.read_bytes(), archive_bytes)
        self.assertEqual(
            receipt["package_sha256"], hashlib.sha256(copied_archive.read_bytes()).hexdigest()
        )
        self.assertEqual(receipt["source_revision"], "a" * 40)

    def _publish_with_failing_receipt_link(self, before_failure=None) -> None:
        original_link = os.link

        def fail_receipt_link(source, destination, *args, **kwargs):
            if destination == OUTPUT_NAMES[1]:
                if before_failure is not None:
                    before_failure()
                raise OSError("simulated receipt publication failure")
            return original_link(source, destination, *args, **kwargs)

        with patch.object(output_dir_module.os, "link", side_effect=fail_receipt_link):
            with self.assertRaisesRegex(OSError, "simulated receipt publication failure"):
                self._publish_sample()

    def _publish_sample(self) -> None:
        archive_bytes = b"verified candidate package\n"
        archive = self.candidate / "candidate.tar.gz"
        archive.write_bytes(archive_bytes)
        receipt_fields = {
            "source_revision": "a" * 40,
            "build_run_id": "build-run",
            "build_run_attempt": "1",
            "consumer_run_id": "consumer-run",
            "consumer_run_attempt": "1",
            "sdl_version": "3.4.18",
            "sdl_archive_sha256": "b" * 64,
            "sdl_license_sha256": "c" * 64,
            "demo_rom_sha256": "d" * 64,
            "battery_fixture_sha256": "e" * 64,
            "battery_fixture_source_sha256": "f" * 64,
            "source_tree_state": "clean",
        }
        publish_verified_artifacts(
            str(self.repository),
            str(self.candidate),
            str(self.output),
            str(archive),
            hashlib.sha256(archive_bytes).hexdigest(),
            receipt_fields,
        )

    def test_failed_receipt_publication_withdraws_published_archive(self) -> None:
        self._publish_with_failing_receipt_link()

        self.assertEqual(
            sorted(entry.name for entry in self.output.iterdir()), []
        )

    def test_failure_after_link_withdraws_each_published_artifact(self) -> None:
        for failing_publication in (1, 2):
            with self.subTest(failing_publication=failing_publication):
                for entry in self.output.iterdir():
                    entry.unlink()
                original_fsync = os.fsync
                directory_syncs = 0

                def fail_directory_sync(descriptor):
                    nonlocal directory_syncs
                    if stat.S_ISDIR(os.fstat(descriptor).st_mode):
                        directory_syncs += 1
                        if directory_syncs == failing_publication:
                            raise OSError("simulated directory sync failure")
                    return original_fsync(descriptor)

                with patch.object(output_dir_module.os, "fsync", side_effect=fail_directory_sync):
                    with self.assertRaisesRegex(OSError, "simulated directory sync failure"):
                        self._publish_sample()

                self.assertEqual(sorted(entry.name for entry in self.output.iterdir()), [])

    def test_failed_withdrawal_is_reported_without_masking_original_error(self) -> None:
        def fail_withdrawal(descriptor, name, published_info):
            raise OSError("simulated withdrawal failure")

        stderr = io.StringIO()
        with patch.object(output_dir_module, "_withdraw_artifact", side_effect=fail_withdrawal):
            with contextlib.redirect_stderr(stderr):
                self._publish_with_failing_receipt_link()

        self.assertIn(f"could not withdraw published {OUTPUT_NAMES[0]}", stderr.getvalue())
        self.assertIn("simulated withdrawal failure", stderr.getvalue())
        self.assertEqual(
            sorted(entry.name for entry in self.output.iterdir()), [OUTPUT_NAMES[0]]
        )

    def test_failed_withdrawal_after_link_is_reported_without_masking_sync_error(self) -> None:
        # Exercises the inner withdrawal site in _publish_new_artifact: the first
        # directory fsync fails after the archive was linked, and withdrawing it fails too.
        original_fsync = os.fsync
        directory_sync_failed = False

        def fail_first_directory_sync(descriptor):
            nonlocal directory_sync_failed
            if not directory_sync_failed and stat.S_ISDIR(os.fstat(descriptor).st_mode):
                directory_sync_failed = True
                raise OSError("simulated directory sync failure")
            return original_fsync(descriptor)

        def fail_withdrawal(descriptor, name, published_info):
            raise OSError("simulated withdrawal failure")

        stderr = io.StringIO()
        with patch.object(output_dir_module.os, "fsync", side_effect=fail_first_directory_sync):
            with patch.object(output_dir_module, "_withdraw_artifact", side_effect=fail_withdrawal):
                with contextlib.redirect_stderr(stderr):
                    with self.assertRaisesRegex(OSError, "simulated directory sync failure"):
                        self._publish_sample()

        self.assertTrue(directory_sync_failed)
        self.assertIn(f"could not withdraw published {OUTPUT_NAMES[0]}", stderr.getvalue())
        self.assertIn("simulated withdrawal failure", stderr.getvalue())
        names = sorted(entry.name for entry in self.output.iterdir())
        self.assertEqual(names, [OUTPUT_NAMES[0]])
        self.assertFalse([name for name in names if name.endswith(".tmp")])

    def test_broken_stderr_does_not_replace_original_publication_error(self) -> None:
        def fail_withdrawal(descriptor, name, published_info):
            raise OSError("simulated withdrawal failure")

        stderr = io.StringIO()
        stderr.close()
        with patch.object(output_dir_module, "_withdraw_artifact", side_effect=fail_withdrawal):
            with contextlib.redirect_stderr(stderr):
                self._publish_with_failing_receipt_link()

    def test_mismatched_published_name_is_not_removed(self) -> None:
        original_link = os.link

        def link_then_replace(source, destination, *args, **kwargs):
            original_link(source, destination, *args, **kwargs)
            if destination == OUTPUT_NAMES[0]:
                published = self.output / destination
                published.unlink()
                published.write_text("concurrent owner data\n", encoding="utf-8")

        with patch.object(output_dir_module.os, "link", side_effect=link_then_replace):
            with self.assertRaisesRegex(OSError, "does not match its verified temporary file"):
                self._publish_sample()

        self.assertEqual(
            (self.output / OUTPUT_NAMES[0]).read_text(encoding="utf-8"),
            "concurrent owner data\n",
        )
        self.assertEqual(
            sorted(entry.name for entry in self.output.iterdir()), [OUTPUT_NAMES[0]]
        )

    def test_failed_receipt_publication_keeps_concurrently_replaced_archive(self) -> None:
        published_archive = self.output / OUTPUT_NAMES[0]

        def replace_archive() -> None:
            published_archive.unlink()
            published_archive.write_text("concurrent owner data\n", encoding="utf-8")

        self._publish_with_failing_receipt_link(replace_archive)

        self.assertEqual(
            published_archive.read_text(encoding="utf-8"), "concurrent owner data\n"
        )
        self.assertFalse((self.output / OUTPUT_NAMES[1]).exists())

    def test_publish_cli_binds_and_publishes_verified_archive(self) -> None:
        archive_bytes = b"verified CLI candidate package\n"
        archive = self.candidate / "candidate.tar.gz"
        archive.write_bytes(archive_bytes)
        result = subprocess.run(
            [
                sys.executable,
                str(Path(output_dir_module.__file__).resolve()),
                "--publish",
                str(self.repository),
                str(self.candidate),
                str(self.output),
                str(archive),
                hashlib.sha256(archive_bytes).hexdigest(),
                "a" * 40,
                "build-run",
                "1",
                "consumer-run",
                "1",
                "3.4.18",
                "b" * 64,
                "c" * 64,
                "d" * 64,
                "e" * 64,
                "f" * 64,
                "clean",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        output_dir = Path(result.stdout.strip())
        copied_archive = output_dir / OUTPUT_NAMES[0]
        receipt = json.loads((output_dir / OUTPUT_NAMES[1]).read_text(encoding="utf-8"))
        self.assertEqual(copied_archive.read_bytes(), archive_bytes)
        self.assertEqual(receipt["package_sha256"], hashlib.sha256(archive_bytes).hexdigest())

    def test_rejects_root_destinations_before_removing_files(self) -> None:
        existing = self.repository / OUTPUT_NAMES[1]
        existing.write_text("preserve repository file\n", encoding="utf-8")

        with self.assertRaises(ValueError):
            prepare_output_dir(
                str(self.repository), str(self.candidate), str(self.repository)
            )
        with self.assertRaises(ValueError):
            prepare_output_dir(
                str(self.repository), str(self.candidate), str(Path(self.repository.anchor))
            )

        self.assertEqual(existing.read_text(encoding="utf-8"), "preserve repository file\n")

    def test_rejects_repository_descendant_without_removing_artifacts(self) -> None:
        metadata_dir = self.repository / ".git"
        metadata_dir.mkdir()
        existing = tuple(metadata_dir / name for name in OUTPUT_NAMES)
        for target in existing:
            target.write_text("preserve repository metadata\n", encoding="utf-8")

        missing_dir = self.repository / "build" / "verified-output"
        self.assertFalse(missing_dir.exists())

        with self.assertRaisesRegex(ValueError, "outside the filesystem and repository roots"):
            prepare_output_dir(
                str(self.repository), str(self.candidate), str(metadata_dir)
            )
        with self.assertRaisesRegex(ValueError, "outside the filesystem and repository roots"):
            prepare_output_dir(
                str(self.repository), str(self.candidate), str(missing_dir)
            )

        for target in existing:
            self.assertEqual(target.read_text(encoding="utf-8"), "preserve repository metadata\n")
        self.assertFalse(missing_dir.exists())

    def test_refuses_directory_at_expected_file_name(self) -> None:
        collision = self.output / OUTPUT_NAMES[1]
        collision.mkdir()
        sentinel = collision / "keep-me.txt"
        sentinel.write_text("preserve directory\n", encoding="utf-8")

        with self.assertRaises(ValueError):
            prepare_output_dir(
                str(self.repository), str(self.candidate), str(self.output)
            )

        self.assertEqual(sentinel.read_text(encoding="utf-8"), "preserve directory\n")

    def test_rejects_candidate_and_output_directory_overlap_without_removing_input(self) -> None:
        archive = self.candidate / OUTPUT_NAMES[0]
        receipt = self.candidate / OUTPUT_NAMES[1]
        archive.write_text("candidate archive\n", encoding="utf-8")
        receipt.write_text("candidate receipt\n", encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "separate from the candidate directory"):
            prepare_output_dir(str(self.repository), str(self.candidate), str(self.candidate))

        self.assertEqual(archive.read_text(encoding="utf-8"), "candidate archive\n")
        self.assertEqual(receipt.read_text(encoding="utf-8"), "candidate receipt\n")

    def test_rejects_symlink_alias_of_candidate_directory(self) -> None:
        archive = self.candidate / OUTPUT_NAMES[0]
        archive.write_text("candidate archive\n", encoding="utf-8")
        alias = self.workspace / "candidate-alias"
        try:
            alias.symlink_to(self.candidate, target_is_directory=True)
        except (NotImplementedError, OSError) as error:
            self.skipTest(f"directory symlinks are unavailable: {error}")

        with self.assertRaisesRegex(ValueError, "separate from the candidate directory"):
            prepare_output_dir(str(self.repository), str(self.candidate), str(alias))

        self.assertEqual(archive.read_text(encoding="utf-8"), "candidate archive\n")

    def test_rejects_output_directory_nested_in_candidate_without_removing_input(self) -> None:
        nested_output = self.candidate / "artifacts"
        nested_output.mkdir()
        candidate_archive = nested_output / OUTPUT_NAMES[0]
        candidate_archive.write_text("candidate-owned archive\n", encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "separate from the candidate directory"):
            prepare_output_dir(str(self.repository), str(self.candidate), str(nested_output))

        self.assertEqual(
            candidate_archive.read_text(encoding="utf-8"), "candidate-owned archive\n"
        )

    def test_rejects_candidate_nested_in_output_directory(self) -> None:
        broad_output = self.workspace / "output"
        nested_candidate = broad_output / "candidate"
        nested_candidate.mkdir(parents=True)

        with self.assertRaisesRegex(ValueError, "separate from the candidate directory"):
            prepare_output_dir(str(self.repository), str(nested_candidate), str(broad_output))


class WorkflowOutputDirectoryTests(unittest.TestCase):
    """CI must hand the helper an output directory it accepts.

    The helper rejects every repository descendant, so a workspace-relative
    GBB_VERIFIED_OUTPUT_DIR would fail the downloaded-package smoke at publish
    time, after the expensive package checks have already passed.
    """

    def test_workflows_place_verified_output_outside_the_checkout(self) -> None:
        workflows = Path(__file__).resolve().parents[2] / ".github" / "workflows"
        assignment = re.compile(
            r"GBB_VERIFIED_OUTPUT_DIR\s*[:=]\s*(\$\{\{[^}]*\}\}\S*|\S+)"
        )
        values = []
        for workflow in sorted([*workflows.glob("*.yml"), *workflows.glob("*.yaml")]):
            for line in workflow.read_text(encoding="utf-8").splitlines():
                match = assignment.search(line)
                if match:
                    values.append((workflow.name, match.group(1).strip("'\"")))
        self.assertTrue(values, "no workflow sets GBB_VERIFIED_OUTPUT_DIR")
        for workflow_name, value in values:
            with self.subTest(workflow=workflow_name, value=value):
                self.assertTrue(
                    value.startswith(("${{ runner.temp }}/", "$RUNNER_TEMP/", "${RUNNER_TEMP}/"))
                    and ".." not in value.split("/"),
                    f"{workflow_name} sets GBB_VERIFIED_OUTPUT_DIR outside runner temp: {value}",
                )


if __name__ == "__main__":
    unittest.main()
