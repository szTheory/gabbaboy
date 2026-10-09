#!/usr/bin/env python3
"""Regression tests for safe verified-player output directory preparation."""

from pathlib import Path
import tempfile
import unittest

from verified_player_output_dir import OUTPUT_NAMES, prepare_output_dir


class VerifiedPlayerOutputDirTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory(prefix="gbb-output-dir-test-")
        self.addCleanup(self.temp_dir.cleanup)
        self.workspace = Path(self.temp_dir.name)
        self.repository = self.workspace / "repository"
        self.repository.mkdir()
        self.output = self.workspace / "artifacts"
        self.output.mkdir()

    def test_preserves_unrelated_files_and_replaces_only_expected_artifacts(self) -> None:
        unrelated = self.output / "keep-me.txt"
        unrelated.write_text("owner data\n", encoding="utf-8")
        for name in OUTPUT_NAMES:
            (self.output / name).write_text("stale artifact\n", encoding="utf-8")

        prepared = prepare_output_dir(str(self.repository), str(self.output))

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

        prepare_output_dir(str(self.repository), str(self.output))

        self.assertFalse(archive_link.is_symlink())
        self.assertEqual(external.read_text(encoding="utf-8"), "preserve target\n")

    def test_rejects_root_destinations_before_removing_files(self) -> None:
        existing = self.repository / OUTPUT_NAMES[1]
        existing.write_text("preserve repository file\n", encoding="utf-8")

        with self.assertRaises(ValueError):
            prepare_output_dir(str(self.repository), str(self.repository))
        with self.assertRaises(ValueError):
            prepare_output_dir(str(self.repository), str(Path(self.repository.anchor)))

        self.assertEqual(existing.read_text(encoding="utf-8"), "preserve repository file\n")

    def test_refuses_directory_at_expected_file_name(self) -> None:
        collision = self.output / OUTPUT_NAMES[1]
        collision.mkdir()
        sentinel = collision / "keep-me.txt"
        sentinel.write_text("preserve directory\n", encoding="utf-8")

        with self.assertRaises(ValueError):
            prepare_output_dir(str(self.repository), str(self.output))

        self.assertEqual(sentinel.read_text(encoding="utf-8"), "preserve directory\n")


if __name__ == "__main__":
    unittest.main()
