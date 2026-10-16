#!/usr/bin/env python3
"""Prove APU source pins survive autocrlf check-in and checkout."""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PINNED_SOURCES = (
    "tests/test_samesuite_apu.c",
    "src/core/gabbaboy.c",
)
UNPINNED_CONTROL = "tests/unpinned-control.c"


class EolControlError(Exception):
    pass


def git_bytes(repo: Path, *args: str) -> bytes:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise EolControlError("git-command-failed")
    return result.stdout


def git_text(repo: Path, *args: str) -> str:
    try:
        return git_bytes(repo, *args).decode("utf-8", "strict")
    except UnicodeDecodeError as exc:
        raise EolControlError("git-output-invalid") from exc


def verify_eol_behavior() -> None:
    with tempfile.TemporaryDirectory(prefix="cgb-apu-eol-") as temp:
        repo = Path(temp)
        git_bytes(repo, "init", "--quiet")
        # Keep this control hermetic and avoid touching the user's Git config.
        empty_attributes = repo / "empty-attributes"
        empty_attributes.write_bytes(b"")
        git_bytes(repo, "config", "core.attributesFile", str(empty_attributes))
        git_bytes(repo, "config", "core.autocrlf", "true")
        git_bytes(repo, "config", "core.safecrlf", "false")

        (repo / ".gitattributes").write_bytes((ROOT / ".gitattributes").read_bytes())
        git_bytes(repo, "add", ".gitattributes")

        source_bytes = {}
        for relative in PINNED_SOURCES:
            source_bytes[relative] = (ROOT / relative).read_bytes()
            destination = repo / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(source_bytes[relative])
        negative = repo / UNPINNED_CONTROL
        negative.parent.mkdir(parents=True, exist_ok=True)
        negative.write_bytes(source_bytes[PINNED_SOURCES[0]])

        git_bytes(repo, "add", *PINNED_SOURCES, UNPINNED_CONTROL)
        attributes = git_text(repo, "check-attr", "text", "eol", "--",
                              *PINNED_SOURCES, UNPINNED_CONTROL)
        for relative in PINNED_SOURCES:
            expected = f"{relative}: text: set\n{relative}: eol: lf"
            if expected not in attributes:
                raise EolControlError("pinned-source-eol-attribute-missing")
            if git_bytes(repo, "show", f":{relative}") != source_bytes[relative]:
                raise EolControlError("pinned-source-index-bytes-changed")

        negative_attributes = (
            f"{UNPINNED_CONTROL}: text: unspecified\n"
            f"{UNPINNED_CONTROL}: eol: unspecified"
        )
        if negative_attributes not in attributes:
            raise EolControlError("negative-control-attribute-unexpected")
        if git_bytes(repo, "show", f":{UNPINNED_CONTROL}") != source_bytes[PINNED_SOURCES[0]]:
            raise EolControlError("negative-control-index-bytes-changed")

        for relative in (*PINNED_SOURCES, UNPINNED_CONTROL):
            (repo / relative).unlink()
        git_bytes(repo, "checkout-index", "--force", "--", *PINNED_SOURCES, UNPINNED_CONTROL)

        for relative in PINNED_SOURCES:
            if (repo / relative).read_bytes() != source_bytes[relative]:
                raise EolControlError("pinned-source-checkout-bytes-changed")
        if b"\r\n" not in (repo / UNPINNED_CONTROL).read_bytes():
            raise EolControlError("negative-control-did-not-convert-to-crlf")


def main() -> int:
    try:
        verify_eol_behavior()
    except (EolControlError, OSError) as exc:
        code = str(exc) if isinstance(exc, EolControlError) else "filesystem-error"
        print(f"cgb-apu-source-eol controls failed: {code}", file=sys.stderr)
        return 1
    print("cgb-apu-source-eol controls pass pinned=2 checkout=lf autocrlf-negative=crlf")
    return 0


if __name__ == "__main__":
    sys.exit(main())
