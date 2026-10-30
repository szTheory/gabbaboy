---
phase: GB-19-qualified-v0-3-0-release
reviewed: 2026-10-30T07:33:13Z
depth: standard
files_reviewed: 56
files_reviewed_list:
  - .github/ci-timeouts.json
  - .github/scripts/release-evidence-lifecycle.sh
  - .github/scripts/verify-published-release-assets.py
  - .github/scripts/verify-release-source-proof.py
  - .github/scripts/verify-test-inventory.sh
  - .github/scripts/verify-workflow-policy.py
  - .github/workflows/ci.yml
  - .github/workflows/libbet-repro.yml
  - .github/workflows/release-rehearsal.yml
  - .github/workflows/release.yml
  - .github/workflows/version-pr-gate.yml
  - CHANGELOG.md
  - cmake/CheckContractRevWiring.cmake
  - cmake/ExpectedTests.cmake
  - cmake/ResolveContractRevision.cmake
  - docs/native-integration.md
  - docs/release.md
  - docs/state-format.md
  - docs/support/unreleased.md
  - src/core/gabbaboy.c
  - tests/CMakeLists.txt
  - tests/baseline/perf-attribution-v1.json
  - tests/cmake/ci-lanes.cmake
  - tests/cmake/host-contract.cmake
  - tests/cmake/hygiene.cmake
  - tests/cmake/perf.cmake
  - tests/cmake/save-formats.cmake
  - tests/data/release-api/SOURCES.md
  - tests/data/release-api/captured.json
  - tests/data/state-forks.json
  - tests/data/support-claims-v0.3.json
  - tests/expected-tests.txt
  - tests/player/CMakeLists.txt
  - tests/scripts/run-perf-gate.sh
  - tests/scripts/test_installed_host.py
  - tests/scripts/verify-changelog-heading.py
  - tests/scripts/verify-doc-links.py
  - tests/scripts/verify-judge-outcome.py
  - tests/scripts/verify-no-interop-claims.py
  - tests/scripts/verify-perf-gate.py
  - tests/scripts/verify-phase3-player.sh
  - tests/scripts/verify-planning-hygiene.py
  - tests/scripts/verify-release-lifecycle.py
  - tests/scripts/verify-state-contract.py
  - tests/scripts/verify-state-forks.py
  - tests/scripts/verify-state-mutants.py
  - tests/scripts/verify-state-pins.py
  - tests/scripts/verify-support-ledger.py
  - tests/scripts/verify-v02-adoption.py
  - tests/scripts/verify-v02-consumers.py
  - tests/scripts/verify-v02-delivery.py
  - tests/scripts/verify-v02-fuzz.py
  - tests/scripts/verify-v03-dispositions.py
  - tests/scripts/verify-version-window.py
  - tests/test_state_codec.c
  - tests/test_state_fork.c
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
status: clean
review_base: f80bdf54c6c7d81e8e21f0275b43cda6edf6c8c4
review_head: b0beb4fd8d1c2290d89b707860bf23c899e12fac
fix_round_delta: 29f6ae2b818fdc4dac8b73b3107b5a9722e10578..b0beb4fd8d1c2290d89b707860bf23c899e12fac
---

# Phase 19: Code Review Report — Review-Fix Round 1

**Reviewed:** 2026-10-30T07:33:13Z  
**Depth:** standard  
**Files Reviewed:** 56  
**Status:** clean

## Summary

Rechecked the six-file fix-round diff `29f6ae2b818fdc4dac8b73b3107b5a9722e10578..b0beb4fd8d1c2290d89b707860bf23c899e12fac` in the context of the original 55-file Phase 19 scope. The new verifier adds the 56th unique source file. All three findings in the premerge report and the judge-CLI integration mismatch are resolved at this head; no new correctness or security finding was verified.

## Prior Findings and Dispositions

### CR-01: Production release readback is incompatible with the publisher's final-asset inventory — RESOLVED (BLOCKER)

**Original files:** `.github/scripts/release-evidence-lifecycle.sh:252-276`; `tests/scripts/verify-v03-dispositions.py:386-435` at `29f6ae2b818fdc4dac8b73b3107b5a9722e10578`  
**Verified fix:** The validator now requires both final metadata assets in the full sourced inventory, compares all published API names/IDs/digests against that inventory, and defines checksum and release-receipt coverage as the inventory minus `SHA256SUMS` and `release-receipt.json` (`tests/scripts/verify-v03-dispositions.py:386-444`). The final metadata assets are separately bound by their own API digests and asset IDs. The lifecycle fixture now includes both final assets and their metadata checks. This matches the production publisher, which deliberately excludes the two self-referential final files from payload checksums.

### CR-02: Publisher does not recheck the frozen asset inventory before publishing — RESOLVED (BLOCKER)

**Original files:** `.github/scripts/release-evidence-lifecycle.sh:310-326,362-376`; `.github/workflows/release.yml:1424-1440` at `29f6ae2b818fdc4dac8b73b3107b5a9722e10578`  
**Verified fix:** `publish-draft` now fetches the live asset list and invokes `verify_pre_publish` before the draft-to-published transition (`.github/scripts/release-evidence-lifecycle.sh:365-372`). The verifier binds the inventory to tag, source commit, release ID, run ID and attempt, rejects malformed or duplicate IDs/names, and requires live IDs and SHA-256 digests to exactly equal the frozen inventory (`.github/scripts/verify-published-release-assets.py:52-113`). The lifecycle control exercises a successful final-gate/nightly/publish path and removes a qualified asset after those gates; the changed code refuses publication while the release remains a draft. The retained post-tag evidence is at `build/preflight/runs/4291d7b05419162f3db9a518c5fdcd0e69388b79/review/`.

### WR-01: PR changed-path exclusion can be bypassed with internal traversal components — RESOLVED (WARNING)

**Original file:** `tests/scripts/verify-v03-dispositions.py:481-484` at `29f6ae2b818fdc4dac8b73b3107b5a9722e10578`  
**Verified fix:** Path validation rejects backslashes, absolute and drive-prefixed paths, empty/dot/dot-dot components, and noncanonical POSIX forms before checking the root component (`tests/scripts/verify-v03-dispositions.py:490-498`). The negative control now includes `docs/placeholder/../../src/core/gabbaboy.c` and expects rejection.

### IR-01: Documented local judge CLI invocation disagreed with its parser — RESOLVED (WARNING)

**Original file:** `tests/scripts/verify-judge-outcome.py` at `29f6ae2b818fdc4dac8b73b3107b5a9722e10578`  
**Verified fix:** The parser now accepts the documented `--key STDERR_FILE --exit N` form and requires a nonnegative integer exit code (`tests/scripts/verify-judge-outcome.py:246-281`). Self-tests execute the documented positive form and reject omitted, noninteger, and negative exit values.

## Rechecked Concern — API Pagination (Not a Finding)

The release asset calls request `per_page=100` without `--paginate`, so a multi-page result would be truncated. The production path cannot qualify such a result: `REQUIRED_ASSETS` contains 20 exact payload names, `check_asset_inventory` accepts only those names with at most the two final metadata names, and `check_final_receipt` requires exactly 22 unique assets (`.github/scripts/verify-release-gates.sh:21,226-237,286-295`). A response with more than 100 release assets has 100 rows on its first page and fails these cardinality/name checks before the frozen inventory is produced. If an asset is added after the 22-row snapshot and the list exceeds one page, the prepublish exact-map comparison sees the 100-row response and refuses it. Thus the proposed later-page-hidden asset does not have a reachable successful final-gate/prepublish path under the current qualified inventory.

The earlier shallow subject checkout versus full-history local differential remains a coverage limitation, not a verified defect: the subject path has no ancestry-dependent Git query, and history/object queries use the trusted checkout.

---

_Reviewed: 2026-10-30T07:33:13Z_  
_Reviewer: the agent (gsd-code-reviewer)_  
_Depth: standard_
