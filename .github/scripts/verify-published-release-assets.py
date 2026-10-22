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
# The workflow whose runs can write to a release. Runs of any other workflow (CI, for one) never block recovery.
RELEASE_WORKFLOW = ".github/workflows/release-please.yml"


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
        raise ValueError("published-assets-not-json: published release API response is not valid JSON") from error
    if not isinstance(after_rows, list):
        raise ValueError("published-assets-not-json: published release API response is not a JSON array")
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


def check_runs(runs: Any, run_id: int, run_attempt: int, workflow: str, source_sha: str) -> None:
    """Reject a stale attempt, an absent own run, or another unfinished run that could still write this release.

    Only runs of the release workflow count, so unrelated active CI never blocks recovery. Another run is an
    eligible writer when it is unfinished and either built the same source commit or is a manual retry dispatch
    (a retry runs from the current main commit, not the release commit). The list API reports each run's latest attempt.
    """
    if not isinstance(runs, list):
        raise ValueError("live workflow run list must be a JSON array")
    seen_own = False
    for run in runs:
        if (not isinstance(run, dict) or type(run.get("id")) is not int or type(run.get("run_attempt")) is not int
                or not isinstance(run.get("status"), str) or not isinstance(run.get("path"), str)
                or not isinstance(run.get("head_sha"), str) or not isinstance(run.get("event"), str)):
            raise ValueError("live workflow run list has a malformed row")
        if run["path"].split("@", 1)[0] != workflow:
            continue
        if run["id"] == run_id:
            if run["run_attempt"] > run_attempt:
                raise ValueError("this attempt is stale: a later attempt of the same run exists")
            if run["run_attempt"] < run_attempt:
                raise ValueError("this attempt is not the latest attempt the live run list reports")
            seen_own = True
        elif run["status"] != "completed" and (run["head_sha"] == source_sha or run["event"] == "workflow_dispatch"):
            raise ValueError(f"concurrent publication attempt: run {run['id']} ({run['status']}) could still write this release")
    if not seen_own:
        raise ValueError("this run is not in the live release workflow run list")


def decide(release: Any, assets: Any, expected_rows: Any, runs: Any, run_id: int, run_attempt: int,
           workflow: str = RELEASE_WORKFLOW, source_sha: str = "", scope: str = "full") -> str:
    """Choose the only safe next step from LIVE state: never overwrite, never re-draft a published release.

    Returns published-verified, draft-reuse, or draft-upload-missing:<names>; anything else rejects.
    scope=full judges the whole release inventory. scope=subset judges only the named assets an early job attaches
    (other jobs' assets are not this job's to judge) and refuses any published release.
    """
    if scope not in ("full", "subset"):
        raise ValueError("recovery scope must be full or subset")
    if not isinstance(release, dict) or not isinstance(release.get("draft"), bool):
        raise ValueError("live release state is missing or malformed")
    expected = expected_inventory(expected_rows)
    live = live_inventory(assets)
    check_runs(runs, run_id, run_attempt, workflow, source_sha)
    if release["draft"] is False:
        if scope == "subset":
            raise ValueError("a published release never receives further attachments")
        additions = {name for name in live if name not in expected}
        if additions != EXPECTED_ADDITIONS or any(live.get(name) != value for name, value in expected.items()):
            raise ValueError("published release does not carry exactly the qualified bytes plus final receipts")
        return "published-verified"
    extra = sorted(set(live) - set(expected))
    if extra and scope == "full":
        raise ValueError(f"draft carries unexpected assets: {extra}")
    changed = sorted(name for name, value in live.items() if name in expected and value != expected[name])
    if changed:
        raise ValueError(f"draft attachment differs from the qualified bytes and is never overwritten: {changed}")
    missing = sorted(set(expected) - set(live))
    return "draft-upload-missing:" + ",".join(missing) if missing else "draft-reuse"


def write_inventory(output: str, paths: list[str]) -> int:
    """Write name/size/sha256 rows for the bytes about to be attached; a directory contributes its regular files."""
    files: list[pathlib.Path] = []
    for item in paths:
        path = pathlib.Path(item)
        if path.is_dir():
            files.extend(child for child in sorted(path.iterdir()) if child.is_file() and child.name != "api-assets.json")
        elif path.is_file():
            files.append(path)
        else:
            raise ValueError(f"inventory input is not a file or directory: {item}")
    rows = [{"name": f.name, "size": f.stat().st_size, "sha256": hashlib.sha256(f.read_bytes()).hexdigest()} for f in files]
    expected_inventory(rows)
    pathlib.Path(output).write_text(json.dumps(rows, sort_keys=True) + "\n")
    return len(rows)


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
    # Executable direct-JSON control: the first argument is response TEXT. A path naming a file that holds a valid
    # response must be rejected, never read, so a caller cannot satisfy the verifier by saving the response first.
    import tempfile

    with tempfile.TemporaryDirectory(prefix="gbb-published-assets.") as directory:
        response_file = pathlib.Path(directory) / "api-assets.json"
        response_file.write_text(after)
        verify(response_file.read_text(), before)
        try:
            verify(str(response_file), before)
        except ValueError as error:
            if "published-assets-not-json" not in str(error):
                raise SystemExit(f"published asset verifier rejected a path for the wrong reason: {error}")
            print("rejected: path-instead-of-json: a file path in place of API response text")
        else:
            raise SystemExit("published asset verifier accepted a file path in place of API response JSON")
    print("PASS: published asset verifier parses JSON responses directly and rejects changed/malformed inventory")
    recovery_self_test()


def inventory_self_test() -> None:
    import tempfile

    with tempfile.TemporaryDirectory(prefix="gbb-inventory.") as directory:
        root = pathlib.Path(directory)
        (root / "one").mkdir()
        (root / "two").mkdir()
        (root / "one" / "a.json").write_bytes(b"alpha")
        (root / "one" / "api-assets.json").write_bytes(b"[]")
        (root / "two" / "b.json").write_bytes(b"beta")
        out = root / "inventory.json"
        if main(["--inventory", str(out), str(root / "one"), str(root / "two" / "b.json")]) != 0:
            raise SystemExit("inventory of real files was rejected")
        rows = json.loads(out.read_text())
        want = [{"name": "a.json", "size": 5, "sha256": hashlib.sha256(b"alpha").hexdigest()},
                {"name": "b.json", "size": 4, "sha256": hashlib.sha256(b"beta").hexdigest()}]
        if rows != want:
            raise SystemExit(f"inventory rows differ from the real bytes: {rows}")
        (root / "two" / "a.json").write_bytes(b"other")
        out.unlink()
        if main(["--inventory", str(out), str(root / "one"), str(root / "two" / "a.json")]) != 1 or out.exists():
            raise SystemExit("a duplicate asset name was inventoried")
        if main(["--inventory", str(out), str(root / "missing")]) != 1:
            raise SystemExit("a missing inventory input was accepted")


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
    src = "c" * 40
    other = "d" * 40

    def run(index: int, status: str = "completed", attempt: int = 1, *, path: str = RELEASE_WORKFLOW,
            sha: str = src, event: str = "push") -> dict[str, Any]:
        return {"id": index, "run_attempt": attempt, "status": status, "path": path, "head_sha": sha, "event": event}

    quiet = [run(7)]
    controls = 0
    positives = 0

    def call(release: Any, assets: Any, rows: Any, runs: Any, attempt: int = 1, scope: str = "full") -> str:
        return decide(release, assets, rows, runs, 7, attempt, RELEASE_WORKFLOW, src, scope)

    # Identical unpublished bytes validate repeatedly and identically.
    first = call(draft, live_rows, expected, quiet)
    again = call(json.loads(json.dumps(draft)), json.loads(json.dumps(live_rows)), expected, quiet)
    if first != again or first != "draft-reuse":
        raise SystemExit("identical draft bytes were not idempotently reused")
    positives += 1
    if call(draft, live_rows[:1], expected, quiet) != "draft-upload-missing:b.json,c.json":
        raise SystemExit("a partial upload was not reduced to uploading only the missing assets")
    positives += 1
    if call(published, published_rows, expected, quiet) != "published-verified":
        raise SystemExit("an already-published release was not verified as published")
    positives += 1
    # Unrelated active CI on the same commit, an active release-workflow run for another commit, and a finished
    # sibling attempt are not release writers and must never block recovery.
    unrelated = quiet + [run(8, "in_progress", path=".github/workflows/ci.yml"),
                         run(9, "queued", path=".github/workflows/ci.yml@refs/heads/main"),
                         run(10, "in_progress", sha=other), run(11, "completed")]
    if call(draft, live_rows, expected, unrelated) != "draft-reuse":
        raise SystemExit("unrelated active runs blocked an otherwise safe recovery")
    positives += 1

    # An early job that attaches only its own assets judges just those; other jobs' assets are not its to judge.
    if call(draft, live_rows, expected[:2], quiet, scope="subset") != "draft-reuse":
        raise SystemExit("a subset attachment was blocked by another job's asset")
    positives += 1
    inventory_self_test()

    def must_reject(label: str, reason: str, *args: Any, **kwargs: Any) -> None:
        nonlocal controls
        try:
            call(*args, **kwargs)
        except ValueError as error:
            if reason not in str(error):
                raise SystemExit(f"recovery self-test rejected {label} for the wrong reason: {error}")
            controls += 1
            return
        raise SystemExit(f"recovery self-test accepted {label}")

    changed = json.loads(json.dumps(live_rows))
    changed[1]["digest"] = "sha256:" + "0" * 64
    must_reject("a changed attachment", "never overwritten", draft, changed, expected, quiet)
    resized = json.loads(json.dumps(live_rows))
    resized[0]["size"] += 1
    must_reject("a resized attachment", "never overwritten", draft, resized, expected, quiet)
    must_reject("a duplicate asset name", "duplicate asset name", draft, live_rows + [dict(live_rows[0], id=99)], expected, quiet)
    must_reject("an unexpected asset", "unexpected assets", draft, live_rows + [row(98, "x.bin", "x")], expected, quiet)
    must_reject("a missing digest", "no SHA-256 digest", draft, [{"id": 1, "name": "a.tar.gz", "size": 1}], expected, quiet)
    must_reject("a concurrent eligible push release", "concurrent publication", draft, live_rows, expected, quiet + [run(8, "in_progress")])
    must_reject("a concurrent queued release", "concurrent publication", draft, live_rows, expected, quiet + [run(8, "queued")])
    must_reject("a concurrent retry dispatch for another commit", "concurrent publication", draft, live_rows, expected,
                quiet + [run(8, "waiting", sha=other, event="workflow_dispatch")])
    must_reject("a stale run attempt", "stale", draft, live_rows, expected, [run(7, attempt=2)])
    must_reject("a run absent from the live listing", "not in the live", draft, live_rows, expected, [run(8)])
    must_reject("a rerun that is not the latest attempt", "not the latest", draft, live_rows, expected, [run(7, attempt=1)], 2)
    must_reject("a malformed run row", "malformed", draft, live_rows, expected, quiet + [{"id": "x"}])
    must_reject("a subset attachment over a changed asset", "never overwritten", draft, changed, expected, quiet, scope="subset")
    must_reject("a subset attachment on a published release", "never receives further", published, published_rows, expected, quiet, scope="subset")
    must_reject("a published release with a changed asset", "published release does not carry",
                published, [dict(published_rows[0], digest="sha256:" + "1" * 64)] + published_rows[1:], expected, quiet)
    must_reject("a published release missing final receipts", "published release does not carry", published, live_rows, expected, quiet)
    must_reject("a published release with no readback inventory", "non-empty", published, published_rows, [], quiet)
    must_reject("a forged expected inventory", "duplicate names", draft, live_rows, expected + [expected[0]], quiet)
    if positives != 5 or controls != 18:
        raise SystemExit("recovery self-test inventory changed unexpectedly")
    print(f"PASS: recovery decisions positives={positives} rejected_controls={controls}")


def main(argv: list[str]) -> int:
    if argv == ["--self-test"]:
        self_test()
        return 0
    if argv and argv[0] == "--inventory":
        if len(argv) < 3:
            raise SystemExit("usage: verify-published-release-assets.py --inventory OUTPUT_JSON FILE_OR_DIR...")
        try:
            print(f"inventory rows={write_inventory(argv[1], argv[2:])}")
        except (ValueError, OSError) as error:
            print(f"REJECT inventory: {error}", file=sys.stderr)
            return 1
        return 0
    if argv and argv[0] == "--decide":
        if len(argv) != 10:
            raise SystemExit("usage: verify-published-release-assets.py --decide RELEASE_JSON ASSETS_JSON EXPECTED_JSON RUNS_JSON RUN_ID RUN_ATTEMPT WORKFLOW_PATH SOURCE_SHA full|subset")
        try:
            documents = [json.loads(pathlib.Path(path).read_text()) for path in argv[1:5]]
            print(decide(*documents, int(argv[5]), int(argv[6]), argv[7], argv[8], argv[9]))
        except (ValueError, OSError) as error:
            print(f"REJECT recovery: {error}", file=sys.stderr)
            return 1
        return 0
    if len(argv) != 2:
        raise SystemExit("usage: verify-published-release-assets.py API_ASSETS_JSON BASELINE_JSON | --inventory ... | --decide ... | --self-test")
    before = json.loads(pathlib.Path(argv[1]).read_text())
    verify(argv[0], before)
    print("PASS: published release asset IDs, names, and digests match the qualified inventory")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
