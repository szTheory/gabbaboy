---
phase: "09"
slug: "mbc3-deterministic-rtc-and-cartridge-persistence"
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: true) (#2117)
status: validated
nyquist_compliant: true
wave_0_complete: true
created: "2026-10-11"
---

# Phase 09 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Source: `09-RESEARCH.md` § Validation Architecture.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | CTest (C test executables with REQUIRE macros; CMake `-P` scripts for fixture and scan checks) |
| **Config file** | `tests/CMakeLists.txt`; exact inventories `tests/expected-tests.txt` and `tests/player/expected-tests.txt` |
| **Quick run command** | `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 -R '^(mbc3_\|magentests_\|loader_\|rtc_\|no_host_clock\|catch_up_)'` |
| **Full suite command** | `ctest --test-dir build --output-on-failure --no-tests=error --output-junit ctest.xml && bash .github/scripts/verify-test-inventory.sh build/ctest.xml tests/expected-tests.txt --installed` |
| **Sanitizer leg (Linux)** | `cmake --preset phase1-asan -DGBB_TEST_INSTALL_PREFIX= && cmake --build --preset phase1-asan && ctest --preset phase1-asan` |
| **Player (macOS arm64)** | `bash tests/scripts/verify-phase3-player.sh --build-package` |
| **Estimated runtime** | Quick slice < 30 s; rtc3test slice about 14 s on Debug (TIMEOUT 300 under ASan) |

---

## Sampling Rate

- **After every task commit:** run the plan's own `ctest --preset phase1 -R` slice
- **After every plan wave:** run the full suite command plus the inventory check
- **Before `/gsd-verify-work`:** the full suite, the ASan leg (in CI) and the player gate must all be green at the exact head
- **Max feedback latency:** 30 seconds for the quick slice

---

## Per-Task Verification Map

Filled from the PLAN files once they exist. Requirement-level map:

| Requirement | Behavior | Test Type | Automated Command | File Exists | Status |
|-------------|----------|-----------|-------------------|-------------|--------|
| CART-04 | MBC3 banking, RAM, RTC select; MBC30 variant rejected | unit | `ctest --preset phase1 -R '^(mbc3_\|loader_mbc30_variant$)'` | ✅ 11 tests | ✅ green |
| CART-04 | MagenTests OOB SRAM for MBC1/3/5, negative control, digest, not installed | hardware-derived oracle + scan | `ctest --preset phase1 -R '^magentests_'` | ✅ 8 tests | ✅ green |
| CART-05 | Contradiction matrix, no partial mutation | table-driven oracle | `ctest --preset phase1 -R '^loader_'` | ✅ 20 tests | ✅ green |
| CART-05 | 8 MiB fuzz bound | deterministic seeds + bounded fuzz | `ctest --preset phase1 -R '^fuzz_core_regressions$'` | ✅ `FUZZ_SYNTH_MAX` 8 MiB mode | ✅ green |
| CART-06 | MBC2/MBC3/MBC5 fresh-process continuation; v1 unchanged | player integration | `bash tests/scripts/verify-phase3-player.sh --build-package` | ✅ `player_continuation_*`, `player_session_v1_*` | ✅ green |
| RTC-01 | Rate, latch, halt, carry, 9-bit day | hardware-derived (rtc3test) + metamorphic | `ctest --preset phase1 -R '^(rtc3test_\|rtc_)'` | ✅ 47 tests | ✅ green |
| RTC-01 | No host clock in `src/core` | static scan + negative control | `ctest --preset phase1 -R '^no_host_clock'` | ✅ 4 tests (3 negative controls) | ✅ green |
| RTC-02 | Catch-up: zero, negative, INT64_MAX, halted, carry; import never advances | unit | `ctest --preset phase1 -R '^rtc_(catch_up_\|import_)'` | ✅ 10 tests | ✅ green |
| RTC-03 | RTC block round-trip and corruption matrix | unit | `ctest --preset phase1 -R '^rtc_block_'` | ✅ 4 tests | ✅ green |
| RTC-03 | Player `saved_at`, catch-up on reopen, rollback | player integration + cross-OS policy table | `ctest --preset phase1 -R '^catch_up_policy_table$'` and the player gate | ✅ 1 test + `player_continuation_mbc3_rtc_*` | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `fixtures/magentests/` (manifest, LICENSE, three digest-pinned ROMs) and `tests/test_magentests.c`
- [x] `fixtures/rtc3test/` and `tests/test_rtc3test.c`
- [x] `tests/test_mbc3_rtc.c`, `tests/test_loader_matrix.c`
- [x] `cmake/CheckCoreNoHostClock.cmake` with a negative control
- [x] continuation fixtures for MBC3+RTC, MBC2 and MBC5, plus `fixtures/save-envelope-v1/`
- [x] new names registered in `tests/expected-tests.txt` and `tests/player/expected-tests.txt`

---

## Manual-Only Verifications

All phase behaviors have automated verification.

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 30s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** validated 2026-10-11 at 258a830 (CTest 402/402, inventory `--installed` 402, player gate green)

## Validation Audit 2026-10-12

| Metric | Count |
|---|---|
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |
