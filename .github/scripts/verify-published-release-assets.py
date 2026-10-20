#!/usr/bin/env python3
"""Verify published release assets against the frozen pre-publication inventory."""

from __future__ import annotations

import hashlib
import json
import pathlib
import re
import sys
from typing import Any

HEX64 = re.compile(r"[0-9a-f]{64}")


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


def expected_inventory(rows: Any) -> dict[str, tuple[int, str]]:
    """Name -> (size, sha256) of the qualified unpublished inventory; duplicates are never tolerated."""
    if not isinstance(rows, list) or not rows:
        raise ValueError("expected asset inventory must be a non-empty JSON array")
    result: dict[str, tuple[int, str]] = {}
    for row in rows:
        if (not isinstance(row, dict) or not isinstance(row.get("name"), str)
                or type(row.get("size")) is not int or row["size"] < 0
                or not isinstance(row.get("sha256"), str) or not HEX64.fullmatch(row["sha256"])):
            raise ValueError("expected asset inventory has a malformed row")
        if row["name"] in result:
            raise ValueError("expected asset inventory contains duplicate names")
        result[row["name"]] = (row["size"], row["sha256"])
    return result


def live_inventory(rows: Any) -> dict[str, tuple[int, str]]:
    if not isinstance(rows, list):
        raise ValueError("live release asset list must be a JSON array")
    result: dict[str, tuple[int, str]] = {}
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("name"), str) or type(row.get("size")) is not int:
            raise ValueError("live release asset list has a malformed row")
        digest = row.get("digest")
        if not isinstance(digest, str) or not digest.startswith("sha256:") or not HEX64.fullmatch(digest[7:]):
            raise ValueError(f"live asset {row['name']} carries no SHA-256 digest")
        if row["name"] in result:
            raise ValueError(f"live release has duplicate asset name {row['name']}")
        result[row["name"]] = (row["size"], digest[7:])
    return result


def decide(release: Any, assets: Any, expected_rows: Any, runs: Any, run_id: int, run_attempt: int) -> str:
    """Choose the only safe next step from LIVE state: never overwrite, never re-draft a published release.

    Returns published-verified, draft-reuse, or draft-upload-missing:<names>; anything else rejects.
    """
    if not isinstance(release, dict) or not isinstance(release.get("draft"), bool):
        raise ValueError("live release state is missing or malformed")
    expected = expected_inventory(expected_rows)
    live = live_inventory(assets)
    if not isinstance(runs, list):
        raise ValueError("live workflow run list must be a JSON array")
    for run in runs:
        if not isinstance(run, dict) or type(run.get("id")) is not int or type(run.get("run_attempt")) is not int:
            raise ValueError("live workflow run list has a malformed row")
        if run["id"] == run_id and run["run_attempt"] > run_attempt:
            raise ValueError("this attempt is stale: a later attempt of the same run exists")
        if run["id"] != run_id and run.get("status") in ("queued", "in_progress", "waiting"):
            raise ValueError(f"concurrent publication attempt: run {run['id']} is still active")
    if release["draft"] is False:
        additions = {name for name in live if name not in expected}
        if additions != EXPECTED_ADDITIONS or any(live.get(name) != value for name, value in expected.items()):
            raise ValueError("published release does not carry exactly the qualified bytes plus final receipts")
        return "published-verified"
    extra = sorted(set(live) - set(expected))
    if extra:
        raise ValueError(f"draft carries unexpected assets: {extra}")
    changed = sorted(name for name, value in live.items() if value != expected[name])
    if changed:
        raise ValueError(f"draft attachment differs from the qualified bytes and is never overwritten: {changed}")
    missing = sorted(set(expected) - set(live))
    return "draft-upload-missing:" + ",".join(missing) if missing else "draft-reuse"


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
    recovery_self_test()


def recovery_self_test() -> None:
    def row(index: int, name: str, text: str) -> dict[str, Any]:
        data = text.encode()
        return {"id": index, "name": name, "size": len(data), "digest": "sha256:" + hashlib.sha256(data).hexdigest()}

    names = ("a.tar.gz", "b.json", "c.json")
    live_rows = [row(i, n, n + " bytes") for i, n in enumerate(names, 1)]
    expected = [{"name": r["name"], "size": r["size"], "sha256": r["digest"][7:]} for r in live_rows]
    draft = {"draft": True}
    published = {"draft": False}
    published_rows = live_rows + [row(90, "SHA256SUMS", "sums"), row(91, "release-receipt.json", "final")]
    quiet = [{"id": 7, "run_attempt": 1, "status": "completed"}]
    controls = 0
    positives = 0
    # Identical unpublished bytes validate repeatedly and identically.
    first = decide(draft, live_rows, expected, quiet, 7, 1)
    again = decide(json.loads(json.dumps(draft)), json.loads(json.dumps(live_rows)), expected, quiet, 7, 1)
    if first != again or first != "draft-reuse":
        raise SystemExit("identical draft bytes were not idempotently reused")
    positives += 1
    if decide(draft, live_rows[:1], expected, quiet, 7, 1) != "draft-upload-missing:b.json,c.json":
        raise SystemExit("a partial upload was not reduced to uploading only the missing assets")
    positives += 1
    if decide(published, published_rows, expected, quiet, 7, 1) != "published-verified":
        raise SystemExit("an already-published release was not verified as published")
    positives += 1

    def must_reject(label: str, reason: str, *args: Any) -> None:
        nonlocal controls
        try:
            decide(*args)
        except ValueError as error:
            if reason not in str(error):
                raise SystemExit(f"recovery self-test rejected {label} for the wrong reason: {error}")
            controls += 1
            return
        raise SystemExit(f"recovery self-test accepted {label}")

    changed = json.loads(json.dumps(live_rows))
    changed[1]["digest"] = "sha256:" + "0" * 64
    must_reject("a changed attachment", "never overwritten", draft, changed, expected, quiet, 7, 1)
    resized = json.loads(json.dumps(live_rows))
    resized[0]["size"] += 1
    must_reject("a resized attachment", "never overwritten", draft, resized, expected, quiet, 7, 1)
    must_reject("a duplicate asset name", "duplicate asset name", draft, live_rows + [dict(live_rows[0], id=99)], expected, quiet, 7, 1)
    must_reject("an unexpected asset", "unexpected assets", draft, live_rows + [row(98, "x.bin", "x")], expected, quiet, 7, 1)
    must_reject("a missing digest", "no SHA-256 digest", draft, [{"id": 1, "name": "a.tar.gz", "size": 1}], expected, quiet, 7, 1)
    must_reject("a concurrent active attempt", "concurrent publication", draft, live_rows, expected,
                quiet + [{"id": 8, "run_attempt": 1, "status": "in_progress"}], 7, 1)
    must_reject("a stale run attempt", "stale", draft, live_rows, expected, [{"id": 7, "run_attempt": 2, "status": "completed"}], 7, 1)
    must_reject("a published release with a changed asset", "published release does not carry",
                published, [dict(published_rows[0], digest="sha256:" + "1" * 64)] + published_rows[1:], expected, quiet, 7, 1)
    must_reject("a published release missing final receipts", "published release does not carry", published, live_rows, expected, quiet, 7, 1)
    must_reject("a published release with no readback inventory", "non-empty", published, published_rows, [], quiet, 7, 1)
    must_reject("a forged expected inventory", "duplicate names", draft, live_rows, expected + [expected[0]], quiet, 7, 1)
    if positives != 3 or controls != 11:
        raise SystemExit("recovery self-test inventory changed unexpectedly")
    print(f"PASS: recovery decisions positives={positives} rejected_controls={controls}")


def main(argv: list[str]) -> int:
    if argv == ["--self-test"]:
        self_test()
        return 0
    if argv and argv[0] == "--decide":
        if len(argv) != 7:
            raise SystemExit("usage: verify-published-release-assets.py --decide RELEASE_JSON ASSETS_JSON EXPECTED_JSON RUNS_JSON RUN_ID RUN_ATTEMPT")
        try:
            documents = [json.loads(pathlib.Path(path).read_text()) for path in argv[1:5]]
            print(decide(*documents, int(argv[5]), int(argv[6])))
        except (ValueError, OSError) as error:
            print(f"REJECT recovery: {error}", file=sys.stderr)
            return 1
        return 0
    if len(argv) != 2:
        raise SystemExit("usage: verify-published-release-assets.py API_ASSETS_JSON BASELINE_JSON | --decide ... | --self-test")
    before = json.loads(pathlib.Path(argv[1]).read_text())
    verify(argv[0], before)
    print("PASS: published release asset IDs, names, and digests match the qualified inventory")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
