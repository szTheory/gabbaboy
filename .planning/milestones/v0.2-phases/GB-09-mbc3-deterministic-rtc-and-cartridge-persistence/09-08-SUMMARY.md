---
phase: 09-mbc3-deterministic-rtc-and-cartridge-persistence
plan: 08
subsystem: testing
tags: [fixtures, rtc3test, magentests, rgbds, provenance, ci]
requires:
  - phase: 09-02
    provides: VerifyFixtureManifest.cmake, MagenTests fixtures and RGBDS 0.6.1 archive pin
provides:
  - rtc3test v004 ROM and verbatim tests.md admitted with Unlicense, digests and provenance
  - reproduce-rtc3test.sh and reproduce-magentests.sh (--self-check, --compare)
  - magentests-repro and rtc3test-repro jobs in fixture-repro.yml
affects: [09-09, 09-12, 09-18]
actuals:
  tokens: 14000
  tasks: 3
  commits: 4
plan_head_before: 172b9c0f68953586fe84d66f6fd55d0d57b29b93
plan_head_after: 9701c455d58af950f53af21deadeb250239650cb
tech-stack:
  added: []
  patterns: ["offline --self-check plus networked --compare reproduction scripts that never overwrite committed bytes"]
key-files:
  created:
    - fixtures/rtc3test/rtc3test.gb
    - fixtures/rtc3test/tests.md
    - fixtures/rtc3test/manifest.json
    - fixtures/rtc3test/LICENSE.txt
    - fixtures/rtc3test/SOURCES.md
    - fixtures/rtc3test/ELIGIBILITY.md
    - tests/scripts/reproduce-rtc3test.sh
    - tests/scripts/reproduce-magentests.sh
  modified:
    - .github/workflows/fixture-repro.yml
    - THIRD_PARTY_NOTICES.md
    - .gitignore
key-decisions:
  - "Rebuild equality is not claimed in SOURCES.md; a local amd64 Docker run was byte-identical but only the hosted exact-head job (read in 09-18) supports the claim"
  - "rtc3test version check accepts the tag v0.4.2 or the abbreviated commit ede982b, since a shallow source build reports the hash"
requirements-completed: [CART-04, RTC-01]
coverage:
  - id: D1
    description: "rtc3test v004 ROM and tests.md admitted with Unlicense, pinned commit and verified SHA-256"
    requirement: RTC-01
    verification:
      - kind: other
        ref: "Fresh Phase 15.1-11 manifest verification: rtc3test ROM and tests.md both fixture-ok; header=ok"
        status: pass
    human_judgment: false
  - id: D2
    description: "Offline self-checks for the rtc3test and MagenTests legacy-toolchain reproduction scripts"
    requirement: CART-04
    verification:
      - kind: other
        ref: "Fresh Phase 15.1-11 run: tests/scripts/reproduce-rtc3test.sh --self-check and tests/scripts/reproduce-magentests.sh --self-check (both self-check=pass)"
        status: pass
    human_judgment: false
  - id: D3
    description: "The fixture-repro workflow definitions retain both reproduction jobs and pass local syntax validation"
    verification:
      - kind: other
        ref: "Fresh Phase 15.1-11 run: actionlint .github/workflows/fixture-repro.yml (exit 0)"
        status: pass
    human_judgment: false
duration: 25min
completed: 2026-10-11
status: complete
---

# Phase 9 Plan 08: rtc3test Admission and Legacy Rebuild Legs Summary

**rtc3test v004 (Unlicense, SHA-256 a271013f...) and its verbatim tests.md admitted with provenance, plus RGBDS 0.4.2 and 0.6.1 byte-comparison scripts and fixture-repro jobs for rtc3test and MagenTests.**

## Accomplishments

- Admitted `fixtures/rtc3test/` with the ROM (32768 bytes, header 0F 00 00), verbatim `tests.md` (6877 bytes, digest 1937b614...), Unlicense text, SOURCES.md, ELIGIBILITY.md and a manifest; `VerifyFixtureManifest` prints fixture-ok for both files. Added a THIRD_PARTY_NOTICES row.
- Added `reproduce-rtc3test.sh` and `reproduce-magentests.sh` with `--self-check` (offline) and `--compare` (fetch by exact commit, rebuild with the upstream recipe, compare bytes, never overwrite fixtures).
- Added `magentests-repro` (archive digest read from fixtures/magentests/SOURCES.md) and `rtc3test-repro` (RGBDS built from commit ede982b) to fixture-repro.yml; existing jobs untouched.
- Local Docker (ubuntu:22.04, linux/amd64, same toolchains) `--compare` reported `result=byte-identical` for both. This is not the hosted claim; SOURCES.md still says rebuild equality is not yet claimed.

## Task Commits

1. Task 1 (tracer): edf53be admit rtc3test; 9701c45 track rtc3test.gb past the `*.gb` ignore rule
2. Task 2: 71ba14e reproduction scripts
3. Task 3: 72aa368 fixture-repro jobs

## Verification

- Full build and CTest: 336/336 passed; `verify-test-inventory.sh --installed` verified 336 executed cases, none skipped.
- The tracer verify gate passed before expansion.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] `.gitignore` excluded the ROM**
- **Found during:** Task 1 (after commit, noticed via `git ls-files`)
- **Issue:** `*.gb` ignore rule silently left rtc3test.gb untracked
- **Fix:** Added an explicit per-file exception, matching the MagenTests convention
- **Files modified:** .gitignore
- **Commit:** 9701c45

**2. [Rule 1 - Bug] Script defects found by the Docker run**
- **Found during:** Task 2
- **Issue:** `trap` referenced a function-local `work_dir` (unbound under `set -u`); the source-built RGBDS reports a commit hash, not v0.4.2
- **Fix:** Global `work_dir` guard; version check accepts tag or abbreviated pin commit
- **Commit:** 71ba14e (fixed before commit)

**Total deviations:** 2 auto-fixed. **Impact:** none on scope.

## Known Stubs

None.

## Issues Encountered

The first scratch directory for the rtc3test download already existed from an earlier session, so the ROM was re-downloaded into a fresh empty directory and compared byte for byte before admission. The upstream asset also includes a `.sym` file, which was not admitted.

## Threat Flags

None.

## Next Phase Readiness

Plan 09-09 proves the two jobs on hosted CI; Plan 09-12 consumes `fixtures/rtc3test/tests.md` for the RTC oracle.

## Self-Check: PASSED

Files, commits (edf53be, 71ba14e, 72aa368, 9701c45) and digests verified present.

## Current Verification — 15.1-11

The manifest, both offline script self-checks, and workflow syntax passed locally. Historical Docker byte-comparison and hosted exact-head job results remain in the original summary body; no new hosted workflow run is claimed by this batch.
