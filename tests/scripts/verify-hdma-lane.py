#!/usr/bin/env python3
"""CGB-HDMA recurring lane contract and remote-check receipt validator.

Extracted from the archived Phase 13 closure checker (Phase 16 D-09) so the recurring CTests no longer read
a phase directory. Only the lane contract, its self-test and the remote-evidence loader and validator live
here; the closure, prohibition and handoff modes stay with the archived Phase 13 record.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LANE_TESTS = (
    "cgb_hdma_claims_contract",
    "cgb_hdma_claims_contract_native",
    "cgb_hdma_claims_contract_selftest",
    "cgb_hdma_lane_contract",
    "cgb_hdma_lane_contract_selftest",
    "cgb_hdma_remote_evidence_selftest",
)
REMOTE_REQUIRED_CONTEXTS = {
    "required-native": "ci",
    "fixture-repro": "fixture-repro",
    "preview-package-smoke": "preview-package-smoke",
}
REMOTE_RECEIPT_FIELDS = frozenset(("headSha", "requiredJobs", "results"))
REMOTE_RESULT_FIELDS = frozenset((
    "name", "workflowName", "databaseId", "attempt", "event", "headSha", "status", "conclusion",
))
MAX_REMOTE_RECEIPT_BYTES = 16 * 1024
MAX_REMOTE_DATABASE_ID = (1 << 63) - 1
MAX_REMOTE_ATTEMPT = 1000
FIXTURE_REPRO_NEEDLES = (
    "reproduce-cgb-hdma.sh --self-check",
    "reproduce-cgb-hdma.sh --self-test",
    "reproduce-cgb-hdma.sh --compare-pinned",
)


class ContractError(Exception):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ContractError(message)


def read(root: Path, relative: str) -> str:
    try:
        return (root / relative).read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise ContractError(f"missing or unreadable {relative}: {error}") from error


def lane_contract(root: Path) -> None:
    cmake = read(root, "tests/CMakeLists.txt")
    expected = read(root, "tests/expected-tests.txt").splitlines()
    player_expected = read(root, "tests/player/expected-tests.txt").splitlines()
    claims = read(root, "tests/scripts/verify-cgb-hdma-claims.py")
    fixture = read(root, ".github/workflows/fixture-repro.yml")
    package_smoke = read(root, "cmake/PreviewPackageSmoke.cmake")
    player_claims = read(root, "tests/player/claims_agree.cmake")
    direct_registrations = re.findall(r"(?m)^\s*add_test\(NAME ([A-Za-z0-9_]+)", cmake)

    for name in LANE_TESTS:
        require(expected.count(name) == 1,
                f"exact core inventory must contain {name} once")
        require(direct_registrations.count(name) == 1,
                f"CTest must register {name} exactly once")
    require("--native-player" in cmake,
            "native claim target must use the explicit --native-player selector")
    require(f'"${{GBB_HDMA_LANE_CHECKER}}" --lane' in cmake,
            "lane target must invoke the Python standard-library --lane selector")
    require(f'"${{GBB_HDMA_LANE_CHECKER}}" --lane-self-test' in cmake,
            "lane control must invoke the Python standard-library --lane-self-test selector")
    require("--prohibitions" not in cmake and "--handoff" not in cmake,
            "local OpenGSD and handoff gates must stay outside recurring CTest")
    require("node " not in cmake and "gsd-tools" not in cmake,
            "recurring lane and claim CTests must not depend on Node or OpenGSD")

    core_hdma = [name for name in expected if name.startswith("cgb_hdma_") or name.startswith("samesuite_hdma_")]
    require(len(core_hdma) >= 90,
            "core HDMA inventory is unexpectedly incomplete")
    player_hdma = [name for name in player_expected if "hdma" in name.lower()]
    require(player_hdma,
            "player HDMA inventory is missing its existing smoke coverage")
    require("claims_agree" in player_claims and
            "GDMA and HBlank DMA run on the selected bootless CGB-CPU-E software model" in player_claims and
            "physical CGB-E remains UNKNOWN/POLICY" in player_claims,
            "player claims contract must retain delivered HDMA scope and its physical qualification limit")

    for needle in FIXTURE_REPRO_NEEDLES:
        require(needle in fixture,
                f"fixture-repro workflow is missing source-pinned check: {needle}")
    require("check_cgb_hdma_fixture_bytes" in fixture or "GBB_RGBDS_ARCHIVE_SHA256" in fixture,
            "fixture-repro must retain its digest-verified tool/source checks")
    require("ScanForbiddenFixtures.cmake" in package_smoke and "CGB-HDMA" in package_smoke,
            "installed package smoke must keep the active CGB-HDMA exclusion scan")
    require("--self-test" in claims and "--subject" in claims and "ALL_SURFACES" in claims,
            "claim checker must retain its complete-surface, subject and mutation controls")
    require("gabbaboy_verify_registered_tests()" in cmake,
            "complete configure-time expected-test enumeration guard is missing")
    print("hdma-lane-contract pass targets=%d core_hdma=%d player_hdma=%d" %
          (len(LANE_TESTS), len(core_hdma), len(player_hdma)))


def lane_self_test(root: Path) -> None:
    lane_contract(root)
    required = (
        "tests/CMakeLists.txt",
        "tests/expected-tests.txt",
        "tests/player/expected-tests.txt",
        "tests/scripts/verify-cgb-hdma-claims.py",
        ".github/workflows/fixture-repro.yml",
        "cmake/PreviewPackageSmoke.cmake",
        "tests/player/claims_agree.cmake",
    )
    with tempfile.TemporaryDirectory(prefix="gabbaboy-hdma-lane-") as temporary:
        scratch = Path(temporary)
        for relative in required:
            target = scratch / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(root / relative, target)
        # (label, file, anchor of the line to delete, substring the rejection must contain). Every anchor names one whole
        # registration or entry, and a rejection for any other reason fails the control: "something failed" proves nothing.
        controls = (
            ("missing-case", "tests/expected-tests.txt", r"(?m)^cgb_hdma_claims_contract_native$",
             "exact core inventory must contain cgb_hdma_claims_contract_native once"),
            ("skipped-lane", "tests/CMakeLists.txt", r"(?m)^[ \t]*add_test\(NAME cgb_hdma_lane_contract(?![A-Za-z0-9_]).*$",
             "CTest must register cgb_hdma_lane_contract exactly once"),
            ("skipped-lane-selftest", "tests/CMakeLists.txt", r"(?m)^[ \t]*add_test\(NAME cgb_hdma_lane_contract_selftest(?![A-Za-z0-9_]).*$",
             "CTest must register cgb_hdma_lane_contract_selftest exactly once"),
            ("missing-fixture-repro-needle", ".github/workflows/fixture-repro.yml", re.escape(FIXTURE_REPRO_NEEDLES[0]),
             "fixture-repro workflow is missing source-pinned check"),
        )
        for label, relative, anchor, reason in controls:
            source = scratch / relative
            original = source.read_text(encoding="utf-8")
            found = re.search(anchor, original)
            require(found is not None, f"{label} mutation anchor did not occur")
            line_start = original.rfind("\n", 0, found.start()) + 1
            line_end = original.find("\n", found.end())
            mutated = original[:line_start] + original[line_end + 1:]
            require(mutated != original, f"{label} mutation changed nothing")
            source.write_text(mutated, encoding="utf-8")
            try:
                lane_contract(scratch)
            except ContractError as error:
                require(reason in str(error), f"{label} failed for the wrong reason: {error}")
            else:
                raise ContractError(f"lane self-test did not reject {label}")
            finally:
                source.write_text(original, encoding="utf-8")
        # An edit that touches none of the lane's registrations must still pass, so the rejections above are the mutations' doing.
        unrelated = scratch / "tests/CMakeLists.txt"
        original = unrelated.read_text(encoding="utf-8")
        unrelated.write_text(original + "\n# unrelated trailing comment\n", encoding="utf-8")
        try:
            lane_contract(scratch)
        finally:
            unrelated.write_text(original, encoding="utf-8")
        controls = controls + (("unrelated-edit-still-passes",),)
    print("hdma-lane self-test pass controls=%d" % len(controls))


def load_remote_evidence(path: Path) -> object:
    try:
        with path.open("rb") as stream:
            payload = stream.read(MAX_REMOTE_RECEIPT_BYTES + 1)
    except OSError as error:
        raise ContractError(f"remote check evidence is unreadable: {error}") from error
    require(len(payload) <= MAX_REMOTE_RECEIPT_BYTES,
            f"remote check evidence exceeds {MAX_REMOTE_RECEIPT_BYTES} bytes")

    def reject_duplicate_fields(pairs: list[tuple[str, object]]) -> dict[str, object]:
        value: dict[str, object] = {}
        for key, field in pairs:
            require(key not in value, f"remote check evidence contains duplicate JSON field: {key}")
            value[key] = field
        return value

    try:
        return json.loads(payload.decode("utf-8"), object_pairs_hook=reject_duplicate_fields)
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError, ValueError) as error:
        raise ContractError(f"remote check evidence is malformed: {error}") from error


def validate_remote_evidence(data: object, expected_head: str) -> None:
    require(isinstance(expected_head, str) and re.fullmatch(r"[0-9a-f]{40}", expected_head) is not None,
            "expected remote result head must be a 40-character lowercase commit SHA")
    require(isinstance(data, dict), "remote evidence must be a JSON object")
    require(set(data) == REMOTE_RECEIPT_FIELDS,
            "remote evidence must contain only headSha, requiredJobs, and results")
    require(data.get("headSha") == expected_head,
            f"remote result head is stale: {data.get('headSha')} != {expected_head}")

    expected_contexts = set(REMOTE_REQUIRED_CONTEXTS)
    required = data.get("requiredJobs")
    require(isinstance(required, list) and len(required) == len(expected_contexts) and
            all(isinstance(name, str) for name in required),
            "remote evidence requiredJobs must name the three authoritative PR contexts")
    require(len(set(required)) == len(required), "remote evidence requiredJobs contains duplicates")
    require(set(required) == expected_contexts,
            f"remote evidence requiredJobs must equal {sorted(expected_contexts)}")

    results = data.get("results")
    require(isinstance(results, list) and len(results) == len(expected_contexts),
            "remote evidence must contain exactly the three authoritative PR context results")
    seen: set[str] = set()
    run_ids: set[int] = set()
    for row in results:
        require(isinstance(row, dict), "remote evidence result rows must be objects")
        require(set(row) == REMOTE_RESULT_FIELDS,
                "remote evidence result has missing or unrecognized fields")
        name = row.get("name")
        require(isinstance(name, str) and name in expected_contexts,
                f"remote evidence has an unrecognized PR context: {name!r}")
        require(name not in seen, f"remote evidence contains duplicate PR context: {name}")
        seen.add(name)
        require(row.get("workflowName") == REMOTE_REQUIRED_CONTEXTS[name],
                f"remote context {name} has the wrong workflow provenance")
        database_id = row.get("databaseId")
        require(type(database_id) is int and 1 <= database_id <= MAX_REMOTE_DATABASE_ID,
                f"remote context {name} has an invalid GitHub run databaseId")
        require(database_id not in run_ids, "remote evidence reuses a GitHub run databaseId")
        run_ids.add(database_id)
        attempt = row.get("attempt")
        require(type(attempt) is int and 1 <= attempt <= MAX_REMOTE_ATTEMPT,
                f"remote context {name} has an invalid GitHub run attempt")
        require(row.get("event") == "pull_request",
                f"remote context {name} is not from a pull_request event")
        require(row.get("headSha") == expected_head,
                f"remote context {name} is stale: {row.get('headSha')} != {expected_head}")
        require(row.get("status") == "completed" and row.get("conclusion") == "success",
                f"remote context {name} is skipped, pending, or failed")
    require(seen == expected_contexts,
            f"remote evidence is missing required results: {sorted(expected_contexts - seen)}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--lane", action="store_true")
    modes.add_argument("--lane-self-test", action="store_true")
    args = parser.parse_args()
    try:
        if args.lane:
            lane_contract(ROOT)
        else:
            lane_self_test(ROOT)
    except ContractError as error:
        print(f"hdma-closure-invalid: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
