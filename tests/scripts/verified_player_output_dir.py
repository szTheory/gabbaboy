#!/usr/bin/env python3
"""Prepare a verified player artifact directory without deleting caller data."""

from pathlib import Path
import sys


OUTPUT_NAMES = (
    "gabbaboy-preview-macos-arm64.tar.gz",
    "verified-receipt.json",
)


def prepare_output_dir(repository_root: str, requested_dir: str) -> Path:
    root = Path(repository_root).resolve()
    output_dir = Path(requested_dir).resolve()
    if output_dir == Path(output_dir.anchor) or output_dir == root:
        raise ValueError("output directory must not be a filesystem or repository root")

    output_dir.mkdir(parents=True, exist_ok=True)
    output_dir = output_dir.resolve()
    if output_dir == Path(output_dir.anchor) or output_dir == root:
        raise ValueError("output directory must not be a filesystem or repository root")

    targets = tuple(output_dir / name for name in OUTPUT_NAMES)
    for target in targets:
        if target.is_dir() and not target.is_symlink():
            raise ValueError(f"artifact destination is a directory: {target.name}")

    for target in targets:
        try:
            target.unlink()
        except FileNotFoundError:
            pass

    return output_dir


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: verified_player_output_dir.py REPOSITORY_ROOT OUTPUT_DIR", file=sys.stderr)
        return 2
    try:
        print(prepare_output_dir(sys.argv[1], sys.argv[2]))
    except (OSError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
