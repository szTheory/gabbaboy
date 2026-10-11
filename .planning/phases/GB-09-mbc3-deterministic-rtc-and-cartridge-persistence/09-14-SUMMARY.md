---
phase: 09-mbc3-deterministic-rtc-and-cartridge-persistence
plan: 14
subsystem: testing
tags: [installed-consumer, rtc, mbc3, c, cpp, docs]
requires:
  - phase: 09-mbc3-deterministic-rtc-and-cartridge-persistence
    provides: "Plan 09-11 gbb_rtc_catch_up, GBB_NO_RTC, GBB_RTC_BLOCK_SIZE and battery block"
provides:
  - "rtc_api_smoke in the installed C and C++ consumers"
  - "RTC host integration guidance in docs/native-integration.md"
affects: [09-17, SHIP-10]
actuals:
  tokens: 6500
  tasks: 2
  commits: 2
plan_head_before: 0c4e05523d59b158f21a655cb091239e79e805f2
plan_head_after: 1b5cadd3eac1d760d16cd07c6c88dfe5287f2cc9
commits: 2
tech-stack:
  added: []
  patterns: ["Consumer smokes synthesise an original ROM and use only the installed header and library"]
key-files:
  created: []
  modified:
    - tests/consumers/c/main.c
    - tests/consumers/cpp/main.cpp
    - docs/native-integration.md
key-decisions:
  - "Consumers assert structure only (size, GBRT magic, S/M/H = 1/1/1, byte-identical round trip, error codes); no emulator digest is pinned"
requirements-completed: [RTC-02, RTC-03]
coverage:
  - id: D1
    description: "Installed C consumer proves catch-up, block layout, import round trip, GBB_NO_RTC and negative-argument error"
    requirement: RTC-02
    verification:
      - kind: integration
        ref: "ctest installed_consumer_c"
        status: pass
    human_judgment: false
  - id: D2
    description: "Installed C++ consumer mirrors the same RTC assertions"
    requirement: RTC-03
    verification:
      - kind: integration
        ref: "ctest installed_consumer_cpp"
        status: pass
    human_judgment: false
  - id: D3
    description: "Integration guide tells hosts how to apply catch-up and persist the battery image"
    requirement: RTC-02
    verification: []
    human_judgment: true
    rationale: "Documentation wording adequacy is a reading judgment; presence of gbb_rtc_catch_up is grep-checked"
duration: 12min
completed: 2026-10-11
status: complete
---

# Phase 9 Plan 14: Installed RTC consumers and host guide Summary

**Installed C and C++ consumers prove gbb_rtc_catch_up, the GBRT battery block and a byte-identical import round trip on a synthetic $10 ROM, and the integration guide documents host catch-up.**

## Accomplishments
- `rtc_api_smoke` in both consumers: battery size 8192 + GBB_RTC_BLOCK_SIZE, catch-up of 3661 s gives live S/M/H 1/1/1 at block offsets 9-11 with GBRT at 0-3, import into a fresh instance re-exports identical bytes, `GBB_INVALID_ARGUMENT` for -1 and NULL, `GBB_NO_RTC` on an MBC1 $03 ROM.
- `docs/native-integration.md` documents non-negative elapsed seconds from the host clock, recording as an input event, import never catching up, and persisting RAM plus block through the battery calls.

## Task Commits
1. **Task 1: C consumer tracer** - `6e32f6e` (test)
2. **Task 2: C++ mirror and guide** - `1b5cadd` (test)

## Files Created/Modified
- `tests/consumers/c/main.c` - rtc_api_smoke
- `tests/consumers/cpp/main.cpp` - mirrored rtc_api_smoke
- `docs/native-integration.md` - RTC bullet in API and errors

## Decisions Made
None - followed plan as specified.

## Deviations from Plan

**1. [Rule 3 - Blocking] Stale install prefix**
- **Found during:** Task 1
- **Issue:** build/package-prefix held a pre-Phase-9 install, so the installed header lacked the RTC API.
- **Fix:** `cmake --install build --prefix build/package-prefix` (ignored build output) before running the consumers.
- **Files modified:** none tracked.
- **Verification:** installed_consumer_c/_cpp pass.

**2. [Rule 1 - Bug] C++ goto over initialisation**
- **Found during:** Task 2
- **Fix:** hoisted `size` declaration above the gotos in the C++ smoke. Folded into the Task 2 commit.

**Total deviations:** 2 auto-fixed. **Impact:** none on scope.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
Evidence ledger and capability text remain for Plan 09-17. Full ctest 385/385 passed and test inventory verified with --installed. The player was not touched, so verify-phase3-player.sh was not run.

## Self-Check: PASSED
Files present; commits 6e32f6e and 1b5cadd are ancestors of HEAD.

---
*Phase: 09-mbc3-deterministic-rtc-and-cartridge-persistence*
*Completed: 2026-10-11*
