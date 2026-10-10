---
phase: GB-02-dmg-cpu-bus-and-time
plan: 12
subsystem: fixture-admission
tags: [windows, manifest, line-endings, sha256, negative-controls]
requires:
  - phase: GB-02-08
    provides: Strict Mooneye manifest and runner negative controls
provides:
  - Exact-head Windows checkout and configured-copy byte evidence
  - Byte-preserved Mooneye manifest checkout policy and precise fixture error receipts
affects: [CPU-05, Windows-CI, T-02-23]
actuals:
  tokens: 2309
  tasks: 2
  commits: 3
commits: 3
plan_head_before: e332bfb93bea61d4182528919b8e5abd5d3b7435
plan_head_after: 22a0136dbe5da1a687a231bb1c3982dd07cba43a
tech-stack:
  added: []
  patterns: [Exact Git blob versus checkout byte capture, single-read bounded ROM classification]
key-files:
  created: [.gitattributes, tests/scripts/inspect-windows-manifest.sh]
  modified: [.github/workflows/ci.yml, src/runner/main.c, tests/expect_runner_failure.cmake]
key-decisions:
  - Preserve the Mooneye manifest Git blob bytes at checkout with a path-scoped -text attribute.
  - Keep exact raw-manifest SHA-256 admission; classify absent, wrong-size, unreadable, and wrong-digest ROMs separately.
requirements-completed: []
duration: 9min
completed: 2026-10-07
status: complete
---

# Phase GB-02 Plan 12: Windows Manifest Portability Summary

**Exact Windows bytes proved checkout CRLF conversion caused manifest rejection; the pinned manifest now survives checkout unchanged and all four Windows negative controls pass.**

## Accomplishments

- Added an explicit Windows CI capture before CTest and a maintainer inspection script. The retained artifact contains the exact Git blob, checked-out manifest, both `configure_file(COPYONLY)` control copies, run/head identity, lengths, SHA-256 values, CR/LF counts, and equality results. The hosted capture now fails if any consumed manifest differs from the blob.
- The initial [push run 37550413474](https://github.com/szTheory/gabbaboy/actions/runs/37550413474) at `faafe408897245a485c35381fd4dd0bf7daf5b78` proved the first byte change occurs at checkout: the Git blob was 11,055 bytes, SHA-256 `76204bc792a5a767f3d7430edfe5542698953507fe268de6a0154b7cb02bcc3e`, with 223 LF and 0 CR. Windows checkout was 11,278 bytes, SHA-256 `1621960a33da8b4459b9876f86620233dcf86082bac5d5c61acbb7ece5f7a13e`, with 223 LF and 223 CR. Both configured control copies were byte-identical to that converted checkout.
- Added `fixtures/mooneye/manifest.json -text` to preserve the exact tracked bytes on Windows. The runner still validates the pinned raw digest before fixture admission. It reads each selected ROM once within a 32 KiB limit and reports distinct bounded reasons for missing file, bad size, bad digest, read error, and invalid fixture path. Missing-ROM and changed-ROM controls now require their exact receipts; malformed JSON/metadata continue to return `invalid-manifest`.

## Task Commits

1. Task 1 — Windows raw-byte capture and inspection: `faafe40` (`test`).
2. Task 2 RED — exact negative-control expectations: `c9b0cc4` (`test`).
3. Task 2 GREEN — byte policy and runner classification: `22a0136` (`fix`).

## TDD Gate Compliance

`ctest --preset phase1 --output-on-failure --no-tests=error --output-junit build/02-12-red.xml -R '^runner_(missing_fixture|bad_digest|bad_manifest|bad_metadata)$'` ran all four controls before the runner change. Missing-fixture and bad-digest failed because both received the old `missing-or-invalid-fixture` reason; malformed-manifest and metadata controls passed. The unmodified JUnit report gave `RED_EVIDENCE_OK` for `runner_missing_fixture` (2/4 failed for the intended assertions). Its semantic assessment confirmed target execution and the old combined reason. The ignored local build directory holds the RED record. The GREEN focused selection passed 4/4. No refactor commit was needed.

## Exact Verification

At production commit `22a0136dbe5da1a687a231bb1c3982dd07cba43a`, local configure/build and the four named controls passed. The local full offline inventory ran 98 cases: 94 passed and the four existing Mooneye unsupported-LY cases failed.

The fresh [Windows push run 37550748143](https://github.com/szTheory/gabbaboy/actions/runs/37550748143) used the same head. Its artifact reports the Git blob, checkout, missing-fixture copy, and bad-digest copy all at 11,055 bytes with SHA-256 `76204bc792a5a767f3d7430edfe5542698953507fe268de6a0154b7cb02bcc3e`, 223 LF and 0 CR. `bash tests/scripts/inspect-windows-manifest.sh` verified the run/head/artifact and all four raw-byte comparisons. The hosted Windows CTest log shows `runner_missing_fixture`, `runner_bad_digest`, `runner_bad_manifest`, and `runner_bad_metadata` passing. Its installed inventory ran 103 cases: 99 passed and only the four previously open Mooneye unsupported-LY cases failed. The Windows manifest portability gap and distinct-control portion of T-02-23 are resolved; the overall required-native job remains red because corpus qualification is still open.

## Deviations from Plan

The existing four named CMake controls already exercised the required file and manifest paths, so `tests/test_runner.c` and `tests/CMakeLists.txt` needed no changes or new inventory entries. A single-read ROM loader avoided the earlier duplicate read/hash path while making failure reasons precise. No manifest contents, fixture bytes, digests, or eligible denominator changed.

## Open Issues

The four Mooneye cases still stop at unsupported LY before their reporting protocol. CPU-05 and Phase GB-02 remain open, along with the independent WLA-DX cross-host fixture reproduction gap. Phase 3 — Visible Interactive DMG — remains paused.

## Self-Check: PASSED

All plan-created and modified files exist; commits `faafe40`, `c9b0cc4`, and `22a0136` are ancestors of HEAD. The measured plan interval contains three commits. No owner/runtime file was staged.
