---
phase: 09-mbc3-deterministic-rtc-and-cartridge-persistence
plan: 11
subsystem: core-battery-rtc
tags: [mbc3, rtc, battery, catch-up, host-policy]
requires: ["09-09"]
provides:
  - "Battery image for timer carts: RAM plus a 21-byte versioned little-endian GBRT block"
  - "gbb_rtc_catch_up, GBB_NO_RTC, GBB_RTC_BLOCK_SIZE (append-only public API)"
  - "Pure host catch-up policy and status formatter (src/player/catch_up_policy.{c,h})"
affects: ["09-13", "09-14", "09-16", "09-17"]
tech-stack:
  added: []
  patterns: ["parse into locals, then commit RAM and clock together", "project on a local copy to keep exports const"]
key-files:
  created:
    - tests/test_rtc_battery.c
    - src/player/catch_up_policy.c
    - src/player/catch_up_policy.h
    - tests/test_catch_up_policy.c
  modified:
    - src/core/gabbaboy.c
    - include/gabbaboy/gabbaboy.h
    - tests/test_mbc3.c
    - tests/CMakeLists.txt
    - tests/expected-tests.txt
key-decisions:
  - "Import compares against the live clock projected to now, so re-importing an image exported at the same emulated time is not a change and never bumps the generation"
  - "catch_up_policy_table is registered in the core inventory (not tests/player) so it runs on Linux, macOS and Windows"
requirements-completed: [RTC-02, RTC-03]
status: complete
commits: 3
plan_head_before: 6c7835654859f22c1a756c9879ec4d3cf80b291d
plan_head_after: 2803615211f8b3079a9120fdce07ea7023a7b8b6
actuals:
  tokens: 45000
  tasks: 3
  commits: 3
duration: 40 min
completed: 2026-10-11
coverage:
  - id: D1
    description: "Unified battery image with RTC block, validated import, never-advancing import"
    verification:
      - kind: integration
        ref: "ctest --test-dir build --output-on-failure --no-tests=error -R '^(rtc_block_roundtrip|rtc_block_corruption_matrix|rtc_import_never_advances|rtc_block_reset_roundtrip|rtc_block_generation|rtc_battery_size_types)$'"
        status: pass
    human_judgment: false
  - id: D2
    description: "gbb_rtc_catch_up with GBB_NO_RTC and exact modular semantics"
    verification:
      - kind: unit
        ref: "ctest --test-dir build --output-on-failure --no-tests=error -R '^rtc_catch_up_.*$'"
        status: pass
    human_judgment: false
  - id: D3
    description: "Pure host catch-up policy and formatter"
    verification:
      - kind: unit
        ref: "ctest --test-dir build --output-on-failure --no-tests=error -R '^catch_up_policy_table$'"
        status: pass
    human_judgment: false
---

# Phase 9 Plan 11: Battery image with RTC block, catch-up call and host policy Summary

Timer cartridges now persist RAM plus a validated 21-byte GBRT clock block through the existing battery calls, hosts get one exact modular `gbb_rtc_catch_up(instance, int64_t)` call, and a pure cross-OS-tested policy decides when a reopened save should be advanced.

## Accomplishments

- `has_battery_ram` became `has_battery_image`; `$0F` (timer, no RAM) is battery-backed and its image is the block alone. Every other type keeps its v0.1 RAM-sized image (MBC1 `$03` unchanged, existing battery and MBC2 tests pass without edits).
- Export projects the clock on a local copy (instance stays const); import validates length, magic, version, sub (< 2^23), S/M/H bounds, DH masked bits and reserved byte into locals, then commits RAM and clock together with `rtc_synced_at = time_half_dots`. Every rejection leaves RAM, clock and generation unchanged (matrix test).
- `gbb_rtc_catch_up`: NULL, then no timer, then negative, with zero and halted as no-ops, otherwise `rtc_add_seconds` after `rtc_sync`; latched registers, sub and emulated time unchanged; one generation bump when live state changed. `GBB_NO_RTC` is appended after `GBB_NO_RUMBLE`.
- `player_catch_up_policy` (signed comparison, then unsigned subtraction clamped to INT64_MAX) and `player_catch_up_format_status`; the table test covers INT64_MIN/INT64_MAX for both timestamps.

## Task Commits

1. Task 1 (tracer): `d1b3b7d` battery image and RTC block (also carries the public header additions for all three symbols)
2. Task 2: `54132d0` catch-up tests and corruption matrix
3. Task 3: `2803615` pure catch-up policy and table test

## Deviations from Plan

**1. [Rule 1 - Bug] mbc3_absent_ram asserted $0F has no battery**
- **Found during:** Task 1
- **Issue:** The test (added in 09-01) expected `gbb_battery_size` to return GBB_NO_BATTERY for `$0F`, which D-15 now makes battery-backed with a 21-byte image.
- **Fix:** `$0F` now asserts size == GBB_RTC_BLOCK_SIZE; `$11` still asserts GBB_NO_BATTERY.
- **Files modified:** tests/test_mbc3.c
- **Commit:** d1b3b7d

**2. [Ordering] Public header additions landed in Task 1**
- GBB_NO_RTC and the `gbb_rtc_catch_up` declaration were committed with Task 1 because the header comment and the core were edited together; Task 2 added the tests that exercise them.

**3. [Documented plan deviation] catch_up_policy_table lives in the core inventory**
- D-26 listed `player_catch_up_policy` in tests/player/expected-tests.txt, but the player builds only on macOS while D-21 requires the table on all three OSes (research Open Question 1). The test compiles `src/player/catch_up_policy.c` directly and is registered in tests/expected-tests.txt.

**Total deviations:** 1 auto-fixed (bug in a prior test), 1 ordering note, 1 pre-planned placement deviation.

## Known Stubs

None. The policy is intentionally not yet wired into the player or its CMake target; Plans 09-13 and 09-16 own that. docs/cartridge-and-saves.md is updated by 09-17.

## Verification

- Full `cmake --preset phase1` build, `ctest` 372/372 passed, and `verify-test-inventory.sh ... --installed` verified 372 cases, none skipped.
- Task acceptance criteria all re-run and passing (header counts, inventory counts 14 and 1, no host-clock includes in the policy, `has_battery_ram` count 0).

## Threat Flags

None beyond the plan's register (T-09-16..19 mitigated and tested).

## Self-Check: PASSED

Files exist (test_rtc_battery.c, catch_up_policy.c/.h, test_catch_up_policy.c) and commits d1b3b7d, 54132d0, 2803615 are on the branch.

## Fresh Focused Evidence (15.1-12)

- The available focused core CTest invocation passed 27/27 selected RTC, policy, continuation-guest and rtc3test cases. This includes battery image round-trip/corruption cases, catch-up error and boundary cases, the policy table, continuation guests, transcript comparisons and the rtc3test negative control.
- The full historical phase regression count in the original verification section is retained as producer evidence; no full suite was run for this refresh.
