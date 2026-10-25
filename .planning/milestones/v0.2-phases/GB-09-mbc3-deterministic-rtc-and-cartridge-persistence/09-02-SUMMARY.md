---
phase: 09-mbc3-deterministic-rtc-and-cartridge-persistence
plan: 02
subsystem: testing
tags: [fixtures, magentests, mbc, sha256, cmake, provenance]
requires:
  - phase: 08
    provides: fixture manifest and provenance conventions (fixtures/mooneye-mbc)
provides:
  - three MagenTests OOB SRAM ROMs admitted with MIT rights and digests
  - cmake/VerifyFixtureManifest.cmake shared manifest digest check
  - RGBDS 0.6.1 CI archive SHA-256 pin for Plan 09-08
affects: [09-07, 09-08, 09-12, 09-18]
actuals:
  tokens: 4500
  tasks: 2
  commits: 2
plan_head_before: dabd564f71a5a3985903f720233598a9e1de044d
plan_head_after: 6fb0289ed39759567b15c1004532aaf55dbfbda2
tech-stack:
  added: []
  patterns: ["manifest fixtures[] array verified by cmake -P script with explicit failure tokens"]
key-files:
  created:
    - fixtures/magentests/mbc_oob_sram_mbc1.gbc
    - fixtures/magentests/mbc_oob_sram_mbc3.gbc
    - fixtures/magentests/mbc_oob_sram_mbc5.gbc
    - fixtures/magentests/manifest.json
    - fixtures/magentests/LICENSE.txt
    - fixtures/magentests/SOURCES.md
    - fixtures/magentests/ELIGIBILITY.md
    - cmake/VerifyFixtureManifest.cmake
  modified:
    - THIRD_PARTY_NOTICES.md
    - .gitignore
key-decisions:
  - "Admit ROMs by explicit .gitignore exceptions, matching the existing per-file admission convention"
requirements-completed: [CART-04]
coverage:
  - id: D1
    description: "MagenTests ROMs admitted with MIT licence, pinned commit and verified SHA-256"
    requirement: CART-04
    verification:
      - kind: other
        ref: "Fresh Phase 15.1-11 run: magentests_fixture_digest, magentests_manifest_self_check and manifest verification (three fixture-ok entries)"
        status: pass
    human_judgment: false
  - id: D2
    description: "Manifest check fails on a tampered ROM and on an empty fixtures array"
    verification:
      - kind: other
        ref: "Fresh Phase 15.1-11 scratch controls: tampered ROM rejected with fixture-digest-mismatch; empty fixtures array rejected with fixture-manifest-empty; focused CTest negative controls passed"
        status: pass
    human_judgment: false
duration: 15min
completed: 2026-10-11
status: complete
---

# Phase 9 Plan 02: MagenTests Fixture Admission Summary

**Three MagenTests 0.5.0 out-of-bounds SRAM ROMs (MBC1/MBC3/MBC5) admitted with MIT licence, pinned commit and verified SHA-256, plus a shared cmake manifest digest check and the RGBDS 0.6.1 CI archive pin.**

## Performance

- **Duration:** about 15 min
- **Tasks:** 2
- **Files modified:** 10

## Accomplishments
- Downloaded the release ROMs into an empty scratch directory; sizes (32768), header byte $147 ($02/$12/$1A) and all three SHA-256 values matched the plan before copy.
- `VerifyFixtureManifest.cmake` prints `fixture-ok <file> <sha256>` per entry; fails with `fixture-digest-mismatch: <file>` or `fixture-manifest-empty`.
- Negative self-test: a copy with one byte changed (offset 20000) produced `fixture-digest-mismatch: mbc_oob_sram_mbc3.gbc` and exit 1; `{"fixtures":[]}` produced `fixture-manifest-empty`.
- SOURCES.md pins upstream commit, RGBDS v0.6.1, hardware.inc 21ef22d and `rgbds-0.6.1-linux-x86_64.tar.xz sha256 cfaff18e0db0006863de921d6f5a10eb5fb04dba453f967955a8b0f30bc7ba5b` (hashed unextracted).
- ELIGIBILITY.md records evidence class, screen oracle, volatile-only scope; notices entry added.

## Task Commits

1. **Task 1: tracer, ROMs, manifest, check script** - `8205991` (feat)
2. **Task 2: provenance, eligibility, notices** - `6fb0289` (docs)

## Decisions Made
- Added three explicit `.gitignore` negations for the .gbc files (the repository ignores `*.gbc` and admits fixtures one by one).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] .gitignore ignored *.gbc**
- **Found during:** Task 1
- **Issue:** `git add` refused the ROMs because `*.gbc` is ignored.
- **Fix:** Added `!/fixtures/magentests/mbc_oob_sram_mbc{1,3,5}.gbc` exceptions, following the existing admission list.
- **Files modified:** .gitignore
- **Committed in:** 8205991

**2. First negative self-test was a no-op:** the byte I overwrote (offset 100) was already 0xff, so the digest still matched. Re-ran with a differing byte; it failed as designed. Not a code defect.

---

**Total deviations:** 1 auto-fixed (Rule 3). **Impact:** none beyond the ignore list.

## Issues Encountered
None. Full phase1 build and ctest: 100% passed (329 tests). `verify-test-inventory.sh` needs a JUnit report argument and was not run standalone; no tests were added or registered by this plan, so tests/expected-tests.txt is unchanged.

## Known Stubs
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
Plan 09-07 can build the screen oracle on these ROMs once 09-01 (done) is in place; Plan 09-08 reads the RGBDS archive pin from SOURCES.md.

## Self-Check: PASSED
All created files exist; commits 8205991 and 6fb0289 are ancestors of HEAD.

## Current Verification — 15.1-11

The current focused CTest batch passed fixture-digest, manifest self-check, screen-oracle, negative-control, and install-exclusion checks. Separate scratch controls rejected a tampered ROM with `fixture-digest-mismatch` and an empty fixtures array with `fixture-manifest-empty`; the original MIT licence, upstream pin, and digest provenance remain unchanged.
