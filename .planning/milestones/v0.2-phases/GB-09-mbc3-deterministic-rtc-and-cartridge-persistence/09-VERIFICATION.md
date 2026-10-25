---
phase: GB-09-mbc3-deterministic-rtc-and-cartridge-persistence
verified: 2026-10-20T21:05:56.351Z
status: passed
score: 115/115 must-haves verified
covered_files:
  - .github/workflows/fixture-repro.yml
  - .github/workflows/preview.yml
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
  - .planning/phases/GB-09-mbc3-deterministic-rtc-and-cartridge-persistence/09-REFRESH-GATES.md
  - CHANGELOG.md
  - CMakeLists.txt
  - README.md
  - THIRD_PARTY_NOTICES.md
  - cmake/CheckCoreNoHostClock.cmake
  - cmake/ScanForbiddenFixtures.cmake
  - cmake/VerifyDocContract.cmake
  - cmake/VerifyFixtureManifest.cmake
  - docs/cartridge-and-saves.md
  - docs/mbc2-mbc5-evidence.md
  - docs/mbc3-rtc-evidence.md
  - docs/native-integration.md
  - docs/preview.md
  - docs/support/unreleased.md
  - fixtures/magentests/ELIGIBILITY.md
  - fixtures/magentests/LICENSE.txt
  - fixtures/magentests/SOURCES.md
  - fixtures/magentests/manifest.json
  - fixtures/magentests/mbc_oob_sram_mbc1.gbc
  - fixtures/magentests/mbc_oob_sram_mbc3.gbc
  - fixtures/magentests/mbc_oob_sram_mbc5.gbc
  - fixtures/mbc2-continuation/LICENSE.txt
  - fixtures/mbc2-continuation/continuation.asm
  - fixtures/mbc2-continuation/continuation.gb
  - fixtures/mbc2-continuation/manifest.json
  - fixtures/mbc3-rtc-continuation/LICENSE.txt
  - fixtures/mbc3-rtc-continuation/continuation.asm
  - fixtures/mbc3-rtc-continuation/continuation.gb
  - fixtures/mbc3-rtc-continuation/manifest.json
  - fixtures/mbc5-continuation/LICENSE.txt
  - fixtures/mbc5-continuation/continuation.asm
  - fixtures/mbc5-continuation/continuation.gb
  - fixtures/mbc5-continuation/manifest.json
  - fixtures/rtc3test/ELIGIBILITY.md
  - fixtures/rtc3test/LICENSE.txt
  - fixtures/rtc3test/SOURCES.md
  - fixtures/rtc3test/manifest.json
  - fixtures/rtc3test/rtc3test.gb
  - fixtures/rtc3test/tests.md
  - fixtures/save-envelope-v1/LICENSE.txt
  - fixtures/save-envelope-v1/manifest.json
  - fixtures/save-envelope-v1/mbc1-32k.gbb
  - fixtures/save-envelope-v1/mbc1-8k.gbb
  - include/gabbaboy/gabbaboy.h
  - src/core/gabbaboy.c
  - src/player/catch_up_policy.c
  - src/player/catch_up_policy.h
  - src/player/limitations.h
  - src/player/main.c
  - src/player/session.c
  - src/player/session.h
  - tests/CMakeLists.txt
  - tests/consumers/c/main.c
  - tests/consumers/cpp/main.cpp
  - tests/expected-tests.txt
  - tests/fuzz_core.c
  - tests/player/CMakeLists.txt
  - tests/player/expected-tests.txt
  - tests/player/test_continuation.c
  - tests/player/test_limitations.c
  - tests/player/test_session.c
  - tests/rtc3test/basic.input
  - tests/rtc3test/expected-basic.txt
  - tests/rtc3test/expected-range.txt
  - tests/rtc3test/expected-subsecond.txt
  - tests/rtc3test/range.input
  - tests/rtc3test/subsecond.input
  - tests/scripts/generate-save-envelope-v1.sh
  - tests/scripts/reproduce-magentests.sh
  - tests/scripts/reproduce-mbc2-continuation.sh
  - tests/scripts/reproduce-mbc3-rtc-continuation.sh
  - tests/scripts/reproduce-mbc5-continuation.sh
  - tests/scripts/reproduce-rtc3test.sh
  - tests/test_battery_fuzz.c
  - tests/test_catch_up_policy.c
  - tests/test_continuation_guests.c
  - tests/test_fuzz_core.c
  - tests/test_instance_concurrency.c
  - tests/test_loader_matrix.c
  - tests/test_magentests.c
  - tests/test_mbc3.c
  - tests/test_mbc3_rtc.c
  - tests/test_mbc3_rtc_internal.c
  - tests/test_mbc5.c
  - tests/test_rtc3test.c
  - tests/test_rtc_battery.c
covered_digest: "v3:sha256:082e41b3478e3d2f948fa4513ada1b433b85889478f3fed5d79bfe33ce563bb8"
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: passed
  previous_score: 5/5
  gaps_closed:
    - "Expanded plan truth 09-03 T8 is now covered by the registered independent MBC3 load concurrency test and contamination control."
    - "Expanded plan truth 09-11 T11 is now covered by concurrent independent MBC3 catch-up, battery assertions and contamination control."
  gaps_remaining: []
  regressions: []
---

# Phase 9: MBC3, Deterministic RTC and Cartridge Persistence Verification

**Phase Goal:** Callers can run MBC3 cartridges whose RTC advances only from emulated time, hosts apply wall-clock catch-up explicitly, and battery data for every new mapper survives fresh-process continuation.

**Verified:** 2026-10-20T21:05:56.351Z
**Status:** passed
**Evidence revision:** 28b3c109422f5da82580b370d769ed0242f6be9a, plus the current test-only change in tests/test_instance_concurrency.c.
**Score:** 115/115 observable truths verified.

This refresh expands the earlier five-truth roadmap report to all 110 plan-level truths plus the five roadmap success criteria. Existing UAT, validation, security and review evidence is reused where applicable. The full core suite passed before the latest test-only harness addition; the focused concurrency and source-ledger checks below passed afterward. No new full code review or hosted CI query is claimed.

## Goal Achievement

### Roadmap Success Criteria

| # | Observable truth | Status | Evidence |
|---|---|---|---|
| 1 | MBC3 $0F-$13 uses 7-bit ROM banking and RAM banks 00-03; unsupported MBC30 variants are rejected explicitly; MagenTests OOB SRAM works for MBC1/3/5. | VERIFIED | Mapper/header validation in src/core/gabbaboy.c; loader and MagenTests cases pass in the full regression receipt. |
| 2 | RTC advances only from emulated half-dots at 2^23 per second, independent of CPU speed; latch, halt, sticky carry and 9-bit day behavior match contract; the core has no host clock. | VERIFIED | Per-instance time_half_dots feeds RTC state; rtc3test, RTC boundary/mutation tests and source/object no-host-clock checks pass. |
| 3 | Hosts explicitly call gbb_rtc_catch_up; negative, overflow and rollback behavior are defined; importing battery data never advances the clock. | VERIFIED | Core catch-up/import cases and host policy table pass; the player applies adapter-provided wall time on reopen. |
| 4 | RTC persists through a versioned little-endian block; the player stores saved_at and explicitly catches up on reopen; RTC and MBC2/3/5 battery state continue across fresh processes; v0.1 saves remain unchanged. | VERIFIED | RTC block, v1/v2 envelope, continuation, rollback, halt, no-clock and wrong-ROM tests pass in the existing receipts. |
| 5 | MBC2/3/5 loader contradictions at exact, one-under and one-over sizes reject without partial mutation; fuzz covers the 8 MiB bound. | VERIFIED | Loader matrix, fuzz boundary seeds and mutation/retention checks pass in the full regression receipt. |

### Plan-Level Truths and Plan-ID Trace

All 110 plan truths were checked against their source, tests and wiring. All pass, including the two concurrency backstops newly covered by the current test-only change.

| Plan | Truths verified | Status | Requirement IDs |
|---|---:|---|---|
| 09-01 | 5/5 | VERIFIED | CART-04 |
| 09-02 | 6/6 | VERIFIED | CART-04 |
| 09-03 | 8/8 | VERIFIED | CART-05 |
| 09-04 | 4/4 | VERIFIED | CART-06 |
| 09-05 | 3/3 | VERIFIED | CART-06 |
| 09-06 | 3/3 | VERIFIED | CART-06 |
| 09-07 | 5/5 | VERIFIED | CART-04 |
| 09-08 | 6/6 | VERIFIED | CART-04, RTC-01 |
| 09-09 | 8/8 | VERIFIED | RTC-01 |
| 09-10 | 4/4 | VERIFIED | CART-06, RTC-03 |
| 09-11 | 12/12 | VERIFIED | RTC-02, RTC-03 |
| 09-12 | 6/6 | VERIFIED | RTC-01, RTC-03 |
| 09-13 | 10/10 | VERIFIED | CART-06, RTC-03 |
| 09-14 | 2/2 | VERIFIED | RTC-02 |
| 09-15 | 10/10 | VERIFIED | CART-04, CART-05, RTC-01 |
| 09-16 | 6/6 | VERIFIED | CART-06, RTC-02, RTC-03 |
| 09-17 | 4/4 | VERIFIED | CART-04, CART-05, CART-06, RTC-01, RTC-02, RTC-03 |
| 09-18 | 8/8 | VERIFIED | CART-04, CART-05, CART-06, RTC-01, RTC-02, RTC-03 |

### Required Artifacts and Key Links

| Check | Status | Evidence |
|---|---|---|
| 47 declared artifact references across 44 unique paths | VERIFIED | 45 automatic artifact checks pass. The two remaining references are mutable .planning/STATE.md and .planning/.continue-here.md; their Phase 9 handoff contents were verified with git show at boundary commit 0ca424f89810408101f15d11dd4b0e3601a3882b. Current mutable state was not used for historical claims. |
| 27 plan-declared key links | VERIFIED | 13 pass the automatic link checker. The remaining descriptive endpoints were manually traced from source to their tests/consumers; no disconnected implementation link was found. |
| Runtime-to-persistence data flow | VERIFIED | Per-instance emulated time feeds RTC state; explicit catch-up changes that state; byte-wise battery serialization flows into the player envelope and fresh-process reopen path. |

The 18-plan artifact audit found no stubs or unwired deliverables. The current code and tests contain no unreferenced debt markers or empty implementations; ordinary null error returns in helper functions are not stubs.

### Behavioral Spot-Checks

| Behavior | Command/result | Status |
|---|---|---|
| Full core, fixtures, loader, MBC3, RTC, mutation, no-host-clock, installed consumers and inventory | Configured phase1 CTest receipt at core source 28b3c10: 1,144/1,144 passed in 375.09 seconds; raw log /tmp/gabbaboy-phase9-regression.log. This predates only the test-harness addition below; no emulator source changed afterward. | PASS |
| Independent MBC3 loading and RTC isolation, including contamination negative control, plus source-ledger controls | ctest --test-dir build --output-on-failure --no-tests=error -R '^(concurrent_independent_instances|cgb_instance_isolation|v02_support_ledger|v02_support_ledger_controls)$': 4/4 passed in 16.18 seconds; raw log /tmp/gabbaboy-phase9-gap-tests.log. | PASS |
| Player continuation and focused contracts | Focused SDL player slice: 28/28 passed in 1.03 seconds at /tmp/gabbaboy-phase9-player-tests.log. Player source is unchanged. The temporary two-entry registration experiment was reverted; its 30-test run is not the final inventory receipt. | PASS |
| Existing automated UAT | 09-UAT.md records 14/14 automated rows, zero issues, pending, skipped, blocked or human rows. Reused; workflow and legacy coverage schema were not rewritten. | PASS |
| Decision coverage | OpenGSD check.decision-coverage-verify reports all 28 trackable 09-CONTEXT.md decisions honored. | PASS |

The new concurrency test barrier-starts two independent MBC3 instances. Each repeatedly loads its own ROM, runs its own guest marker and applies distinct RTC catch-up deltas, checking battery state after each step. The negative control imports the other lane's real RTC block after both workers join and requires the same oracle to detect the contamination. Calls on a single instance remain serial and are not required to be thread-safe.

### Requirements Coverage

| Requirement | Source plans | Status | Evidence |
|---|---:|---|---|
| CART-04 | 6 | SATISFIED | MBC3 mapper/banking, MBC30 rejection and MagenTests criteria pass. |
| CART-05 | 4 | SATISFIED | Contradiction matrix, bounded fuzz and independent-instance concurrent loading evidence pass. |
| CART-06 | 9 | SATISFIED | Fresh-process MBC2/3/5 continuation and v0.1 save compatibility pass. |
| RTC-01 | 6 | SATISFIED | RTC rate, latch, halt, carry, day counter, rtc3test and no-host-clock checks pass. |
| RTC-02 | 5 | SATISFIED | Explicit catch-up, negative/overflow policy, import behavior and independent-instance RTC isolation pass. |
| RTC-03 | 9 | SATISFIED | Versioned block and fresh-process reopen continuation pass; RTC isolation is covered by the new test. |

All six IDs are declared by Phase 9 plans and mapped to this phase in REQUIREMENTS.md. No orphaned Phase 9 requirement was found.

### Reused Quality Gates

| Gate | Result |
|---|---|
| Security | 09-SECURITY.md reports 45 threats closed and zero open; the accepted low performance risk remains non-blocking. |
| Code review | 09-REVIEW-DISPOSITION.md records 13 findings and zero open. The latest review is scoped to the guide contract checker; no new full-phase review is claimed. |
| Validation | 09-VALIDATION.md is validated and Nyquist compliant; plans specify automated checks. |
| Probe execution | Not applicable: no Phase 9 plan declares a probe script and this is not a migration/tooling phase. |
| Human verification | None. No physical hardware, visual, credential or perceptual claim is made; software assertions are automated per D-069. |

Historical coverage blocks in plans 09-04, 09-11, 09-13 and 09-16 use a legacy schema. The coverage gate is scoped with --since 11; those historical blocks were not treated as green or rewritten.

### Gaps Summary

No remaining gaps. All five roadmap truths, 110 plan truths, 47 artifact references and 27 key links are verified. The refreshed report supersedes the earlier roadmap-only 5/5 report with broader plan and evidence coverage.

---
_Verified: 2026-10-20T21:05:56.351Z_
_Verifier: Codex (gsd-verifier)_
