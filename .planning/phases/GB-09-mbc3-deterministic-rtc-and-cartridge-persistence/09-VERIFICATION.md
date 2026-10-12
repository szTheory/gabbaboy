---
phase: GB-09-mbc3-deterministic-rtc-and-cartridge-persistence
verified: 2026-10-12T14:00:00Z
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
  - cmake/VerifyDocContract.cmake
  - docs/native-integration.md
  - include/gabbaboy/gabbaboy.h
  - src/core/gabbaboy.c
  - src/player/catch_up_policy.c
  - src/player/session.c
  - tests/CMakeLists.txt
  - tests/expected-tests.txt
  - tests/player/expected-tests.txt
covered_digest: "v3:sha256:e0451e1d115e547eaffd17b114bbaaee8a3e0fd919045942b8d0feedef2b10b2"
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: passed
  previous_score: 5/5
  gaps_closed: []
  gaps_remaining: []
  regressions: []
---

# Phase 9: MBC3, Deterministic RTC and Cartridge Persistence Verification Report

**Phase Goal:** Callers can run MBC3 cartridges whose RTC advances only from emulated time, hosts apply wall-clock catch-up explicitly, and battery data for every new mapper survives fresh-process continuation.
**Verified at:** HEAD cad42a2 on branch gsd/phase-09-mbc3-deterministic-rtc-and-cartridge-persistence
**Status:** passed
**Re-verification:** Yes, regenerated against the current tree after covered files changed (a9d0d14, c47fc00, docs to cad42a2)

## Goal Achievement

### Observable Truths (ROADMAP success criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | MBC3 `$0F-$13` with 7-bit ROM banking and RAM `00-03`; MBC30 and other variants rejected explicitly; MagenTests OOB SRAM pass for MBC1/3/5 | VERIFIED | `GBB_UNSUPPORTED_CARTRIDGE_VARIANT` in `include/gabbaboy/gabbaboy.h` (MBC30 markers ROM code `$07` / RAM code `$05`). `mbc3_*`, `loader_mbc30_variant`, `magentests_*` all in the 411-test run, 0 failures. |
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
| `ctest --test-dir build` (orchestrator, HEAD cad42a2) | 411/411 passed |
| `verify-test-inventory.sh build/ctest.xml tests/expected-tests.txt --installed` | "verifies 411" (orchestrator-reported, HEAD cad42a2; `ctest -N` lists 411 and `tests/expected-tests.txt` has 411 lines, which I confirmed) |
| `ctest -R rtc3test` | 5/5 passed |
| `ctest -R no_host_clock` | 4/4 passed |
| Targeted slice rerun by me at cad42a2: native_guide_rtc_contract, doc_contract_*, rtc3test_, no_host_clock, rtc_, player_continuation, loader_, magentests_, fuzz_core | 87/87 passed |
| Earlier slice: player_continuation, player_session_v1, loader_mbc30, catch_up, rtc_import, rtc_block, magentests, fuzz_core | 25/25 passed |
| `bash tests/scripts/verify-phase3-player.sh --build-package` | passed (SDL 3.4.18 package smoke; the no-input control failed as expected) |

### Changes since the previous report (re-verified)

`git diff 46ece1a HEAD -- src include cmake tests` touches only `cmake/VerifyDocContract.cmake` (new, 171 lines), `tests/CMakeLists.txt` (+76) and `tests/expected-tests.txt` (+7). Core, player and header code is unchanged, so truths 1-5 rest on the same implementation. The additions:

- `native_guide_rtc_contract` checks `docs/native-integration.md` (RTC section) against `gabbaboy.h` and the relocated example: 12 required contract phrases (once per open, negative returns `GBB_INVALID_ARGUMENT`, `GBB_NO_RTC`, import never advances, block-alone for `$0F`, never reads host clock) must be present within the scoped section, and every `gbb_*` identifier the guide names must be declared. It passes and requires `identifiers>=1 phrases=12`.
- Six `doc_contract_*_selftest` controls each fail the checker on purpose (undeclared identifier, missing phrase, comment-only declaration, word-boundary prefix, empty phrase, out-of-scope phrase) and pass.
- All seven new tests are registered in `tests/expected-tests.txt` (411 entries equals `ctest -N` total), so the inventory gate covers them.
- This strengthens RTC-02/RTC-03 traceability: the host-facing documented catch-up and persistence contract is now machine-checked against the API rather than read by hand.

### Phase artifacts added

09-UAT.md (status complete, 14 automated passes, 0 issues), COVERAGE.md, and a scoped 09-REVIEW.md with 09-REVIEW-DISPOSITION.md (open: 0, total 13). I did not treat these as evidence on their own; the passing tests above are.

### Anti-Patterns and Review

09-REVIEW-DISPOSITION.md lists 13 findings in total (frontmatter `total: 13`, `open: 0`); the five original ones were WR-01, WR-02, IN-01, IN-02 fixed and IN-03 skipped (readability only). 0 are open. 09-SECURITY.md reports threats_open 0 and 09-VALIDATION.md has nyquist_compliant true. No debt markers were found in the changed core files that I read.

### Hosted CI State

Hosted CI at cad42a2 was not queried by me. The UAT record cites ci PR run 38197216902 (all eight required jobs success) at a3dae02, which predates the doc-contract commits. Per AGENTS.md, exact-head CI for the final merge revision must be confirmed green before merging PR #65. This is a merge precondition, not a verification gap.

### Limits (not human_needed)

- Behavior that depends on real wall-clock time or Game Boy hardware (for example RTC drift against a physical cart) is outside automated scope. The phase claims only the emulated-time and explicit-catch-up contracts, which are covered by rtc3test and the original fixtures.
- Mealybug `mbc3_rtc` is gated by G1 and gbclock by G3. The phase does not claim either as evidence.

### Gaps Summary

No gaps. The phase goal is achieved in code and tests at HEAD.

---

_Verified: 2026-10-12_
_Verifier: Claude (gsd-verifier)_
