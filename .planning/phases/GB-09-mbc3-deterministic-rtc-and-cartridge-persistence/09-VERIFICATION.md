---
phase: GB-09-mbc3-deterministic-rtc-and-cartridge-persistence
verified: 2026-10-11T00:00:00Z
status: passed
score: 5/5 must-haves verified
covered_files:
  - .planning/phases/GB-09-mbc3-deterministic-rtc-and-cartridge-persistence/09-01-PLAN.md
  - .planning/phases/GB-09-mbc3-deterministic-rtc-and-cartridge-persistence/09-01-SUMMARY.md
  - .planning/phases/GB-09-mbc3-deterministic-rtc-and-cartridge-persistence/09-02-PLAN.md
  - .planning/phases/GB-09-mbc3-deterministic-rtc-and-cartridge-persistence/09-02-SUMMARY.md
  - .planning/phases/GB-09-mbc3-deterministic-rtc-and-cartridge-persistence/09-03-PLAN.md
  - .planning/phases/GB-09-mbc3-deterministic-rtc-and-cartridge-persistence/09-03-SUMMARY.md
  - .planning/phases/GB-09-mbc3-deterministic-rtc-and-cartridge-persistence/09-04-PLAN.md
  - .planning/phases/GB-09-mbc3-deterministic-rtc-and-cartridge-persistence/09-04-SUMMARY.md
  - .planning/phases/GB-09-mbc3-deterministic-rtc-and-cartridge-persistence/09-05-PLAN.md
  - .planning/phases/GB-09-mbc3-deterministic-rtc-and-cartridge-persistence/09-05-SUMMARY.md
  - .planning/phases/GB-09-mbc3-deterministic-rtc-and-cartridge-persistence/09-06-PLAN.md
  - .planning/phases/GB-09-mbc3-deterministic-rtc-and-cartridge-persistence/09-06-SUMMARY.md
  - .planning/phases/GB-09-mbc3-deterministic-rtc-and-cartridge-persistence/09-07-PLAN.md
  - .planning/phases/GB-09-mbc3-deterministic-rtc-and-cartridge-persistence/09-07-SUMMARY.md
  - .planning/phases/GB-09-mbc3-deterministic-rtc-and-cartridge-persistence/09-08-PLAN.md
  - .planning/phases/GB-09-mbc3-deterministic-rtc-and-cartridge-persistence/09-08-SUMMARY.md
  - .planning/phases/GB-09-mbc3-deterministic-rtc-and-cartridge-persistence/09-09-PLAN.md
  - .planning/phases/GB-09-mbc3-deterministic-rtc-and-cartridge-persistence/09-09-SUMMARY.md
  - .planning/phases/GB-09-mbc3-deterministic-rtc-and-cartridge-persistence/09-10-PLAN.md
  - .planning/phases/GB-09-mbc3-deterministic-rtc-and-cartridge-persistence/09-10-SUMMARY.md
  - .planning/phases/GB-09-mbc3-deterministic-rtc-and-cartridge-persistence/09-11-PLAN.md
  - .planning/phases/GB-09-mbc3-deterministic-rtc-and-cartridge-persistence/09-11-SUMMARY.md
  - .planning/phases/GB-09-mbc3-deterministic-rtc-and-cartridge-persistence/09-12-PLAN.md
  - .planning/phases/GB-09-mbc3-deterministic-rtc-and-cartridge-persistence/09-12-SUMMARY.md
  - .planning/phases/GB-09-mbc3-deterministic-rtc-and-cartridge-persistence/09-13-PLAN.md
  - .planning/phases/GB-09-mbc3-deterministic-rtc-and-cartridge-persistence/09-13-SUMMARY.md
  - .planning/phases/GB-09-mbc3-deterministic-rtc-and-cartridge-persistence/09-14-PLAN.md
  - .planning/phases/GB-09-mbc3-deterministic-rtc-and-cartridge-persistence/09-14-SUMMARY.md
  - .planning/phases/GB-09-mbc3-deterministic-rtc-and-cartridge-persistence/09-15-PLAN.md
  - .planning/phases/GB-09-mbc3-deterministic-rtc-and-cartridge-persistence/09-15-SUMMARY.md
  - .planning/phases/GB-09-mbc3-deterministic-rtc-and-cartridge-persistence/09-16-PLAN.md
  - .planning/phases/GB-09-mbc3-deterministic-rtc-and-cartridge-persistence/09-16-SUMMARY.md
  - .planning/phases/GB-09-mbc3-deterministic-rtc-and-cartridge-persistence/09-17-PLAN.md
  - .planning/phases/GB-09-mbc3-deterministic-rtc-and-cartridge-persistence/09-17-SUMMARY.md
  - .planning/phases/GB-09-mbc3-deterministic-rtc-and-cartridge-persistence/09-18-PLAN.md
  - .planning/phases/GB-09-mbc3-deterministic-rtc-and-cartridge-persistence/09-18-SUMMARY.md
  - cmake/CheckCoreNoHostClock.cmake
  - include/gabbaboy/gabbaboy.h
  - src/core/gabbaboy.c
  - src/player/catch_up_policy.c
  - src/player/session.c
  - tests/expected-tests.txt
  - tests/player/expected-tests.txt
covered_digest: "v3:sha256:8daf5227ffaaa894eea292802806abbf809b6a6ec53ec7a2286261eabb287ce7"
behavior_unverified: 0
overrides_applied: 0
---

# Phase 9: MBC3, Deterministic RTC and Cartridge Persistence Verification Report

**Phase Goal:** Callers can run MBC3 cartridges whose RTC advances only from emulated time, hosts apply wall-clock catch-up explicitly, and battery data for every new mapper survives fresh-process continuation.
**Verified at:** HEAD c773c13 on branch gsd/phase-09-mbc3-deterministic-rtc-and-cartridge-persistence
**Status:** passed
**Re-verification:** No, initial verification

## Goal Achievement

### Observable Truths (ROADMAP success criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | MBC3 `$0F-$13` with 7-bit ROM banking and RAM `00-03`; MBC30 and other variants rejected explicitly; MagenTests OOB SRAM pass for MBC1/3/5 | VERIFIED | `GBB_UNSUPPORTED_CARTRIDGE_VARIANT` in `include/gabbaboy/gabbaboy.h` (MBC30 markers ROM code `$07` / RAM code `$05`). `mbc3_*`, `loader_mbc30_variant`, `magentests_*` all in the 404-test run, 0 failures. |
| 2 | rtc3test passes headless; RTC runs from emulated half-dots only; latch, halt, sticky carry, 9-bit day; CI proves no host clock in `src/core` | VERIFIED | `rtc_sync` in `src/core/gabbaboy.c` derives time only from `instance->time_half_dots` (shift constant `RTC_HALF_DOTS_PER_SECOND_SHIFT`). `rtc_add_seconds` gives a 9-bit day and a sticky `0x80` carry. `src/core/gabbaboy.c` has no `time()`, `clock()` or `clock_gettime`. `rtc3test_*` (5 tests incl. `rtc3test_negative_control`) pass. `no_host_clock` reports `files=2 symbols=11 tool=nm`, and its negative controls and `no_host_clock_comment_selftest` pass. |
| 3 | `gbb_rtc_catch_up` applies elapsed seconds with tested negative, overflow and rollback policy; battery import never advances the RTC | VERIFIED | `gbb_rtc_catch_up` rejects negatives with `GBB_INVALID_ARGUMENT`, treats 0 as a no-op, ignores the delta when halted, and sets sticky carry through `rtc_add_seconds`. `src/player/catch_up_policy.c` handles clock-earlier (rollback), unavailable clock, no timestamp, and clamps the delta to `INT64_MAX`. `rtc_catch_up_*`, `rtc_import_*` and `catch_up_policy_table` pass. |
| 4 | RTC round-trips through a versioned LE battery block; player envelope stores `saved_at` and applies catch-up on reopen; RTC continuation fixture passes across fresh processes; MBC2/3/5 continue; v0.1 saves load unchanged | VERIFIED | `GBB_RTC_BLOCK_SIZE 21u` and `rtc_block_*` tests pass. `src/player/session.c` decodes the v2 envelope with `saved_at` and applies catch-up through `player_session_apply_catch_up`. `player_continuation_mbc3_rtc_{resume,delta,rollback,halted,no_clock,wrong_rom}`, `_mbc2_resume`, `_mbc5_resume`, `player_session_v1_{corpus_load,mbc1_write_identical,v2_stickiness}` are registered in `tests/player/expected-tests.txt`. The player gate `verify-phase3-player.sh --build-package` I re-ran and it passed. |
| 5 | Loader rejects every contradictory type/ROM/RAM/length combination for MBC2/3/5 (exact, one-under, one-over) with no partial mutation; fuzz covers the 8 MiB bound | VERIFIED | `loader_*` (20 tests) and `fuzz_core_regressions` pass. |

**Score:** 5/5 truths verified, 0 present-but-behavior-unverified.

All five truths are state-transition or invariant claims. Each is backed by a passing behavioral test that I ran, not only symbol presence.

### Requirements Coverage

| Requirement | Source Plans | Status | Evidence |
|-------------|--------------|--------|----------|
| CART-04 | 6 plans | SATISFIED | Truth 1 |
| CART-05 | 4 plans | SATISFIED | Truth 5 |
| CART-06 | 9 plans | SATISFIED | Truth 4 |
| RTC-01 | 6 plans | SATISFIED | Truth 2 |
| RTC-02 | 5 plans | SATISFIED | Truth 3 |
| RTC-03 | 9 plans | SATISFIED | Truth 4 |

All six IDs appear in PLAN frontmatter and are mapped to Phase 9 in REQUIREMENTS.md, marked Complete. No orphaned requirements.

### Behavioral Spot-Checks and Evidence I Ran

| Check | Result |
|-------|--------|
| `cmake --build --preset phase1` | no work to do (up to date at HEAD) |
| `ctest --test-dir build --no-tests=error --output-junit ctest.xml` | 404/404 passed (173.9 s) |
| `verify-test-inventory.sh build/ctest.xml tests/expected-tests.txt --installed` | "Verified 404 executed CTest cases; none skipped." |
| `ctest -R rtc3test` | 5/5 passed |
| `ctest -R no_host_clock` | 4/4 passed |
| Targeted slice: player_continuation, player_session_v1, loader_mbc30, catch_up, rtc_import, rtc_block, magentests, fuzz_core | 25/25 passed |
| `bash tests/scripts/verify-phase3-player.sh --build-package` | passed (SDL 3.4.18 package smoke; the no-input control failed as expected) |

### Anti-Patterns and Review

09-REVIEW-DISPOSITION.md lists 5 findings: 4 fixed (WR-01, WR-02, IN-01, IN-02) and 1 skipped (IN-03, readability only). 0 are open. 09-SECURITY.md reports threats_open 0 and 09-VALIDATION.md has nyquist_compliant true. No debt markers were found in the changed core files that I read.

### Hosted CI State (reported as observed, not assumed)

- Exact-head CI on **04c7759** (ci run 38191589574, fixture-repro run 38191589599): both completed with conclusion `success`.
- The code diff from 04c7759 to HEAD touches 8 files in `src`, `include`, `tests` and `cmake`: the review fixes, a ledger-name check and `tests/expected-tests.txt` entries. My local 404-test run covers that code.
- At **HEAD c773c13**, hosted runs (ci 38196792878 on the PR, 38196787564 on the push, plus fixture-repro and preview-package-smoke) were still queued or in progress when I queried. `player-gate` had succeeded and no ci check had failed. Exact-head CI for c773c13 is **not yet green**. Per AGENTS.md, merge PR #65 only after those checks finish green. This is a pending merge precondition, not a verification gap.

### Limits (not human_needed)

- Behavior that depends on real wall-clock time or Game Boy hardware (for example RTC drift against a physical cart) is outside automated scope. The phase claims only the emulated-time and explicit-catch-up contracts, which are covered by rtc3test and the original fixtures.
- Mealybug `mbc3_rtc` is gated by G1 and gbclock by G3. The phase does not claim either as evidence.

### Gaps Summary

No gaps. The phase goal is achieved in code and tests at HEAD.

---

_Verified: 2026-10-11_
_Verifier: Claude (gsd-verifier)_
