---
phase: 09-mbc3-deterministic-rtc-and-cartridge-persistence
plan: 09
subsystem: cartridge-rtc
tags: [mbc3, rtc, determinism, ctest, ci, no-host-clock]
requires:
  - phase: 09-01
    provides: MBC3 mapper, has_timer in cart_state
  - phase: 09-07
    provides: MagenTests screen oracle that passed on the mapper before the $08-$0C decode was extended
provides:
  - "Lazy MBC3 RTC anchored on emulated time_half_dots (D-07..D-10)"
  - "17 rtc_* CTests: guest tracer, black-box gate/fresh-load, 14 single-TU white-box cases with a GBB_CORE_SOURCE_PATH hook"
  - "cmake/CheckCoreNoHostClock.cmake and the no_host_clock / no_host_clock_selftest / no_host_clock_symbol_selftest CTests"
  - "Draft PR #65 with an exact-head green CI read on all eight required check runs"
affects: [09-10, 09-11, 09-12, 09-15, 09-18]
requirements-completed: [RTC-01]
key-decisions:
  - "Latching on exactly $00 then $01 and the $04-$07 / $0D-$FF unmapped selections are project decisions, labelled as such in source, not hardware-confirmed"
  - "rtc_step_field splits n before adding so a 64-bit second count can never wrap"
  - "CI prints the no_host_clock result on each build leg (extra ctest -V step) so the tool name is in the job log"
status: complete
commits: 4
plan_head_before: 5ea612fec75d2e3719e18cf42cd36202421e5f99
plan_head_after: 2b4c22004e801272ebc1cff12b85312debb444b9
actuals:
  tokens: 14900
  tasks: 3
  commits: 4
duration: 85 min
completed: 2026-10-11
---

# Phase 9 Plan 09: Deterministic MBC3 RTC and no-host-clock proof Summary

A lazy MBC3 RTC that advances only from emulated `time_half_dots` (2^23 half-dots per second, 00-then-01 latch, sticky 9-bit day carry, stored-as-written out-of-range fields), proved by 17 original `rtc_*` CTests and a two-layer `no_host_clock` scan, with the draft PR #65 head green on every required check.

## Accomplishments

- `cart_state` gained `rtc_s/m/h/dl/dh`, `rtc_l[5]`, `rtc_sub`, `rtc_synced_at`, `rtc_latch_prev`. `rtc_add_seconds` is an O(1) closed form; `rtc_sync` splits the elapsed half-dots so nothing overflows and treats `now < synced_at` as zero elapsed. `advance_devices_to` and the STOP fast-forward are untouched (`git diff main` shows no change on them).
- Register read/write masks, the D-10 generation rule (snapshot compare after sync), the `gbb_reset` rebase (sync, `reset_state`, `synced_at = 0`) and fresh-load defaults are in `src/core/gabbaboy.c`. `read8` stays const.
- `rtc_tracer`: a `$10` guest sets 23:59:58 on day 511, waits 150 VBlanks (about 2.51 s), latches and reads 00:00:00 day 0 with DH = `$80`. The frozen tracer digest `4c7a57ff3d50d228` is unchanged.
- `rtc_closed_form_differential` compares the closed form with a naive per-second stepper on 100000 seeded states (including out-of-range fields) and 2000 long-count states (via the 512-day period); `rtc_add_composes` includes a pair whose sum exceeds `INT64_MAX`; metamorphic tests cover slice invariance and busy-loop / HALT / STOP independence.
- `cmake/CheckCoreNoHostClock.cmake`: source layer (include allow-list, comment and literal stripping, left-context call regex) and object layer (`nm -u`, with `llvm-nm` and `dumpbin /SYMBOLS` fallbacks; a missing tool fails). Two negative controls prove it can fail.

## Mutation anchors for Plan 09-15 (each occurs exactly once in `src/core/gabbaboy.c`)

| Tag comment | Statement |
|---|---|
| `rtc: a seconds write restarts the sub-second prescaler` | `c->rtc_sub = 0u;` in `rtc_write_register` case 0 |
| `rtc: other register writes keep the prescaler` | `if (reg >= 1u && reg <= 3u) c->rtc_sub = sub_before;` |
| `rtc: a halt toggle keeps the prescaler` | `if (reg == 4u) c->rtc_sub = sub_before;` |
| `rtc: out-of-range fields are stored as written` | `c->rtc_s = (uint8_t)(value & 0x3Fu);` |
| `rtc: latch only on 00 then 01` | `const int latch_now = c->rtc_latch_prev == 0x00u && value == 0x01u;` in `rtc_latch_write` |

I applied one mutant per tag with the include hook (`-DGBB_CORE_SOURCE_PATH`) as a smoke check: each was killed by at least one white-box case (prescaler tags by `rtc_prescaler_rules`, the out-of-range tag by `rtc_write_masks` and `rtc_out_of_range_rollover`, the latch tag by `rtc_latch_edges`). Plan 09-15 owns the formal controls.

## Exact-head CI (RTC-01 evidence)

- Draft PR: https://github.com/szTheory/gabbaboy/pull/65 (draft, base `main`, not merged, not marked ready).
- Head SHA: `2b4c22004e801272ebc1cff12b85312debb444b9`. Pull-request `ci` run: https://github.com/szTheory/gabbaboy/actions/runs/38180044966 (attempt 1). `wait-exact-head-ci.py` printed `PASS`.

| Required check run | Conclusion |
|---|---|
| native-linux-x64 | success |
| native-macos-arm64 | success |
| native-windows-x64 | success |
| linux-asan-ubsan | success |
| cmake-floor-3.25.3 | success |
| player-gate | success |
| macos-player-package | success |
| required-native | success |

`no_host_clock` observations (from the job logs of that run):

| Leg | Line |
|---|---|
| native-linux-x64 | `no-host-clock pass files=2 symbols=8 tool=nm` |
| native-macos-arm64 | `no-host-clock pass files=2 symbols=11 tool=nm` |
| native-windows-x64 | `no-host-clock pass files=2 symbols=7 tool=nm` |
| linux-asan-ubsan | `no-host-clock pass files=2 symbols=42 tool=nm` |
| cmake-floor-3.25.3 | `no-host-clock pass files=2 symbols=8 tool=nm` |

Research A2 resolved: the native-windows-x64 Ninja leg configures GNU 14.2.0 from `C:/mingw64` (MinGW), so binutils `nm` reads the COFF archive and the `dumpbin` fallback was not needed. The dumpbin path is therefore untested in CI (it is implemented but unexercised).

Other workflows on the same head: `fixture-repro` (pull_request) success including `magentests-repro` and `rtc3test-repro`; `preview-package-smoke` success. Push-event `ci` run 38180042576 also succeeded.

The first push (`9d905b7`) was red on `macos-player-package` only (see deviation 3); one fix-and-push cycle of the allowed three. A docs-only SUMMARY commit follows the CI-verified head; its own CI was not awaited by this plan.

## Deviations from Plan

**1. [Rule 1 - Bug] 64-bit second count overflow in the field stepper**
- **Found during:** Task 2 design (add_composes requires a pair summing past `INT64_MAX`)
- **Issue:** `(f + n) / limit` could wrap for n near 2^64.
- **Fix:** `rtc_step_field` computes `n / limit + (f + n % limit) / limit`.
- **Files modified:** `src/core/gabbaboy.c`. **Commit:** 3b80276.

**2. [Rule 3 - Blocker] Ninth-bit mutant anchor collision**
- **Found during:** Task 1 configure
- **Issue:** `tests/CMakeLists.txt` requires the text `& 1u) << 8` to occur exactly once in the core (MBC5 mutant); my day-bit expression matched it.
- **Fix:** wrote the day high bit as `(c->rtc_dh & 0x01u) * 256u`.
- **Commit:** 14caf9d.

**3. [Rule 1 - Bug, regression from Plan 09-01] player test used MBC3 as its unsupported cartridge**
- **Found during:** exact-head CI of the first push
- **Issue:** `tests/player/test_session.c` set type `$13` as "unsupported"; MBC3 is supported since 09-01, so `player_session_replacement_failure` failed on `macos-player-package` (the only leg that builds the player tests).
- **Fix:** use `$20` (MBC6), which stays unsupported; checked with the core that it returns `GBB_UNSUPPORTED_CARTRIDGE`.
- **Files modified:** `tests/player/test_session.c`. **Commit:** 2b4c220.

**4. [Rule 2 - Missing] CI log evidence for the tool name**
- **Found during:** Task 3
- **Issue:** `ctest --output-on-failure` hides a passing test's output, so the `no-host-clock pass ... tool=` line would never reach a job log.
- **Fix:** added a `ctest -R '^no_host_clock$' -V` step to the three native legs and the sanitizer leg in `.github/workflows/ci.yml`, and one `ctest -V` line in `.github/scripts/verify-cmake-floor.sh`. Neither file was in the plan's `files_modified`.
- **Commit:** 9d905b7.

**5. [Rule 3] Test registration placement:** the no-host-clock block sits before `gabbaboy_verify_registered_tests()` in `tests/CMakeLists.txt`, not at the end of the file, because the inventory check runs at that call.

**Total deviations:** 5 (2 Rule 1, 1 Rule 2, 2 Rule 3). **Impact:** no change to behaviour or scope; the extra CI steps only add log lines.

## Notes on test construction

- `gbb_run` returns `HALTED_IDLE` after one eligible idle stretch (about one frame), so the guest-driven tests count consumed half-dots rather than calls. A final `HALT` with no wake source ends in a bus-level stop, which the helper treats as the guest having finished; RAM results are asserted by the caller.
- `rtc_slice_invariance` and `rtc_cpu_independence` sync both machines to a common timestamp before comparing, since whole instructions never straddle a budget and the machines stop within a few half-dots of the target.
- The `dumpbin` branch and the `ASAN` symbol list (42 symbols, includes sanitizer runtime references) are covered only by the deny-list; no denied name appeared.

## Known Stubs

None.

## Threat Flags

None. Mitigations T-09-09 (overflow-safe split, `rtc_time_near_max`, differential), T-09-10 (masks, `rtc_out_of_range_rollover`) and T-09-11 (`no_host_clock` with two negative controls, exact-head CI on every leg) are implemented; T-09-12 accepted (RTC work only at RTC accesses, tracer digest unchanged).

## Self-Check: PASSED

- `src/core/gabbaboy.c`, `tests/test_mbc3_rtc.c`, `tests/test_mbc3_rtc_internal.c`, `cmake/CheckCoreNoHostClock.cmake` exist; commits 14caf9d, 3b80276, 9d905b7, 2b4c220 are ancestors of HEAD.
- Local: full CTest 356/356 and `verify-test-inventory.sh` reported 356 executed, none skipped; all five mutation tags occur once; acceptance greps (17 `rtc_` names, 3 `no_host_clock` names, no `GabbaBoy::core` on the white-box target, `no-host-clock-tool-missing` present, PR is a draft) pass.
