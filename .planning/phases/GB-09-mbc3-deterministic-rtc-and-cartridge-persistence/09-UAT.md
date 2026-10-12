---
status: complete
phase: GB-09-mbc3-deterministic-rtc-and-cartridge-persistence
source: 09-01-SUMMARY.md, 09-02-SUMMARY.md, 09-03-SUMMARY.md, 09-04-SUMMARY.md, 09-05-SUMMARY.md, 09-06-SUMMARY.md, 09-07-SUMMARY.md, 09-08-SUMMARY.md, 09-09-SUMMARY.md, 09-10-SUMMARY.md, 09-11-SUMMARY.md, 09-12-SUMMARY.md, 09-13-SUMMARY.md, 09-14-SUMMARY.md, 09-15-SUMMARY.md, 09-16-SUMMARY.md, 09-17-SUMMARY.md, 09-18-SUMMARY.md
started: 2026-10-12T12:48:46Z
updated: 2026-10-12T13:00:32.933Z
---

## Current Test

[testing complete]

## Tests

Automated evidence for tests 1-13 was gathered at a3dae02 (local macOS arm64 Debug: CTest 404/404, inventory --installed 404 executed none skipped, player gate with package build passed, package SHA-256 5501d50e…; hosted CI at the same head: ci PR run 38197216902 all eight required jobs success, fixture-repro pull_request and push success).

### 1. MBC3 banking, RAM gate and MBC30 rejection (CART-04)
expected: MBC3 $0F-$13 load with 7-bit ROM banking, RAM banks 0-3, the 0x0A gate and a 4 MiB ceiling; MBC30 headers are rejected after the checksum and the player names "MBC1 multicart wiring or MBC30".
result: pass
source: automated
evidence: "ctest -R '^(mbc3_|loader_mbc30_variant$)' (09-01, WR-01 fix fc85d8c)"

### 2. MagenTests out-of-bounds SRAM oracle for MBC1, MBC3, MBC5 (CART-04)
expected: Each ROM shows all 23040 pixels at shade 0 after 16 frames; the $149=$03 negative control shows shade 3; manifest rejects a tampered ROM and an empty fixtures array; ROMs never install.
result: pass
source: automated
evidence: "ctest -R '^magentests_' (09-02 D1-D2, 09-07)"

### 3. Loader contradiction matrix with no partial mutation (CART-05)
expected: gbb_load_rom agrees with the written precedence on every MBC2/MBC3/MBC5 combination and a rejected load leaves the previous ROM intact.
result: pass
source: automated
evidence: "ctest -R '^loader_' (09-15)"

### 4. 8 MiB ROM bound under fuzzing (CART-05)
expected: Ten header-only length classes up to SIZE_MAX give a bounded result set, GBB_ROM_TOO_LARGE above 8 MiB, and the prior ROM survives.
result: pass
source: automated
evidence: "ctest -R '^fuzz_core_regressions$' (09-03)"

### 5. Deterministic RTC rate, latch, halt, carry and 9-bit day (RTC-01)
expected: The clock advances only from emulated time (2^23 half-dots per second), latches on 00 then 01, halts, and keeps a sticky day carry; rtc3test Basic, Range and Sub-second pass with exact counts (36, 28, 57) and transcripts; the negative control never finishes; five RTC mutants are each killed.
result: pass
source: automated
evidence: "ctest -R '^(rtc3test_|rtc_)' (09-09, 09-12 D1-D5, 09-15)"

### 6. No host clock in the core (RTC-01)
expected: The two-layer scan passes on src/core and fails on its three negative controls, including a /* inside a // comment and an empty symbol listing.
result: pass
source: automated
evidence: "ctest -R '^no_host_clock' (09-09, WR-02 fix 8896725)"

### 7. gbb_rtc_catch_up semantics (RTC-02)
expected: Zero and halted are no-ops, negative returns GBB_INVALID_ARGUMENT with no change, INT64_MAX and carry follow exact modular rules, non-timer carts return GBB_NO_RTC, and import never advances the clock.
result: pass
source: automated
evidence: "ctest -R '^rtc_(catch_up_|import_)' (09-11)"

### 8. 21-byte RTC block round trip and corruption matrix (RTC-03)
expected: The battery image is RAM followed by the GBRT block (block alone for $0F); every corrupt length, magic, version or field is rejected leaving RAM, clock and generation unchanged.
result: pass
source: automated
evidence: "ctest -R '^rtc_block_|^rtc_battery_size_types$' (09-11)"

### 9. Installed C and C++ consumers exercise the RTC API (RTC-02)
expected: Consumers built against the installed package prove catch-up, block layout, import round trip, GBB_NO_RTC and the negative-argument error.
result: pass
source: automated
evidence: "installed consumer CTests in the 404-case run (09-14 D1-D2)"

### 10. Player envelope v2 and v0.1 save compatibility (CART-06)
expected: MBC2, MBC3+RAM+clock and MBC5 up to 128 KiB save in a validated v2 envelope; v0.1.2-written MBC1 saves load and re-encode byte-identically; the player classifies from the core; 8 MiB ROM cap.
result: pass
source: automated
evidence: "player_session_v2_*, player_session_v1_*, generate-save-envelope-v1.sh --check = check=pass (09-04, 09-13)"

### 11. Catch-up on reopen in a fresh process (RTC-03)
expected: A reopened MBC3 save advances once by the time since saved_at, shows the status text, never moves backwards on rollback, respects halt, reports no clock, and MBC2/MBC5 originals resume; --clock-unix only works in battery smoke modes and accepts only [-]digits.
result: pass
source: automated
evidence: "player_continuation_*, player_session_clock_flag_scope, catch_up_policy_table (09-16, IN-01 fix 19deb6b)"

### 12. Original continuation guests rebuild byte-identically (CART-06)
expected: The MBC3+RTC, MBC2 and MBC5 guest ROMs and the MagenTests and rtc3test fixtures rebuild to their pinned digests in hosted CI.
result: pass
source: automated
evidence: "fixture-repro at a3dae02: magentests-repro, rtc3test-repro, fixture-repro all success on push and pull_request (09-05, 09-06, 09-08 D1-D3, 09-10)"

### 13. Evidence ledger and capability text stay registered
expected: Every test name cited in docs/mbc3-rtc-evidence.md is a registered CTest; public capability text names MBC3 and four-mapper player persistence.
result: pass
source: automated
evidence: "ctest -R '^mbc3_rtc_evidence_ledger' (09-17, T-09-34 9bc23db)"

### 14. Integration guide explains RTC catch-up and battery persistence
expected: docs/native-integration.md gives a host author correct, sufficient instructions for gbb_rtc_catch_up and battery persistence: every gbb_*/GBB_* name it uses is declared, and it states all twelve RTC behaviors the header promises.
result: pass
source: automated
evidence: "ctest -R '^(native_guide_rtc_contract|doc_contract_)' (cmake/VerifyDocContract.cmake; plan 09-14 D3 had marked this a human reading, replaced per owner directive DECISIONS D-069; mutants dropping 'two calls add twice' or renaming gbb_rtc_catch_up both fail)"

## Summary

total: 14
passed: 14
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps

[none yet]

## Notes

- Coverage blocks in 09-04, 09-11, 09-13 and 09-16 use a `deliverable:` key and `ctest`/`command` kinds that the coverage classifier rejects; their deliverables were mapped by hand to tests 3-11 above and verified by running the cited tests.
- 09-02, 09-08 and 09-12 SUMMARYs omit `commits:`; their plan windows measure 2, 4 and 3 commits. All other SUMMARYs reconcile exactly.
- Owner directive 2026-10-12: zero human UAT by default (DECISIONS D-069, LESSONS GB-GSD-014); test 14 became an automated contract check instead of a reading.
- verify:pre api-coverage gate fired on mentions of GabbaBoy's own public C API; COVERAGE.md declares no external API integration (Phase 7 precedent).
