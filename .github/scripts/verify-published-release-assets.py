#!/usr/bin/env python3
"""Verify published release assets against the frozen pre-publication inventory."""

from __future__ import annotations

import json
import pathlib
import sys
from typing import Any


EXPECTED_ADDITIONS = {"SHA256SUMS", "release-receipt.json"}


def inventory(rows: list[dict[str, Any]]) -> list[tuple[int, str, str | None]]:
    if not isinstance(rows, list):
        raise ValueError("release asset inventory must be a JSON array")
    result = []
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("id"), int) or not isinstance(row.get("name"), str):
            raise ValueError("release asset inventory has a malformed row")
        result.append((row["id"], row["name"], row.get("digest")))
    if len({row[1] for row in result}) != len(result):
        raise ValueError("release asset inventory contains duplicate names")
    return sorted(result)


def verify(after_json: str, before_rows: list[dict[str, Any]]) -> None:
    try:
        after_rows = json.loads(after_json)
    except json.JSONDecodeError as error:
        raise ValueError("published release API response is not valid JSON") from error
    before = inventory(before_rows)
    after = inventory(after_rows)
    if not set(before).issubset(set(after)):
        raise ValueError("published release readback changed or removed a previously qualified asset")
    expected_names = {row[1] for row in before} | EXPECTED_ADDITIONS
    if {row[1] for row in after} != expected_names:
        raise ValueError("published release readback has an unexpected asset inventory")


def self_test() -> None:
    before = [{"id": 41, "name": "qualified.tar.gz", "digest": "sha256:abc"}]
    # The API response is deliberately a JSON string, not a filesystem path.
    after = json.dumps(before + [
        {"id": 42, "name": "SHA256SUMS", "digest": "sha256:def"},
        {"id": 43, "name": "release-receipt.json", "digest": "sha256:ghi"},
    ])
    verify(after, before)
    for bad_after in (
        json.dumps([
            {"id": 41, "name": "qualified.tar.gz", "digest": "sha256:changed"},
            {"id": 42, "name": "SHA256SUMS"},
            {"id": 43, "name": "release-receipt.json"},
        ]),
        "not-json",
    ):
        try:
            verify(bad_after, before)
        except ValueError:
            continue
        raise SystemExit("published asset verifier self-test accepted invalid API evidence")
    print("PASS: published asset verifier parses JSON responses directly and rejects changed/malformed inventory")


def main(argv: list[str]) -> int:
    if argv == ["--self-test"]:
        self_test()
        return 0
    if len(argv) != 2:
        raise SystemExit("usage: verify-published-release-assets.py API_ASSETS_JSON BASELINE_JSON | --self-test")
    before = json.loads(pathlib.Path(argv[1]).read_text())
    verify(argv[0], before)
    print("PASS: published release asset IDs, names, and digests match the qualified inventory")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
