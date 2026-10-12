---
phase: GB-09-mbc3-deterministic-rtc-and-cartridge-persistence
reviewed: 2026-10-11T00:00:00Z
depth: standard
files_reviewed: 59
files_reviewed_list:
  - .gitattributes
  - .github/scripts/verify-cmake-floor.sh
  - .github/workflows/ci.yml
  - .github/workflows/fixture-repro.yml
  - .github/workflows/preview.yml
  - CMakeLists.txt
  - cmake/CheckCoreNoHostClock.cmake
  - cmake/ScanForbiddenFixtures.cmake
  - cmake/VerifyFixtureManifest.cmake
  - include/gabbaboy/gabbaboy.h
  - src/core/gabbaboy.c
  - src/player/catch_up_policy.c
  - src/player/catch_up_policy.h
  - src/player/limitations.h
  - src/player/main.c
  - src/player/session.c
  - src/player/session.h
  - tests/player/clock_flag_scope.cmake
  - tests/scripts/reproduce-mbc3-rtc-continuation.sh
  - tests/scripts/reproduce-rtc3test.sh
findings:
  critical: 0
  warning: 2
  info: 3
  total: 5
status: issues_found
---

# Phase 9: Code Review Report

**Reviewed:** 2026-10-11
**Depth:** standard
**Files Reviewed:** 59 in scope; the core, player, no-host-clock cmake, CI workflows and reproduction scripts were read in full or by Phase 9 diff. Fixture manifests, expected-output files and the C test sources were only spot-checked.

## Summary

I traced the MBC3 core against the locked decisions and found no correctness or security defects there. The checks covered:

- **RTC arithmetic.** `rtc_step_field`, `rtc_add_seconds` and `rtc_sync` cannot overflow, even for a 2^64 second count. The 9-bit day wrap and sticky carry are right, and halted clocks re-anchor without crediting the halted time.
- **Catch-up.** `gbb_rtc_catch_up` handles zero (no-op), negative (`GBB_INVALID_ARGUMENT`), `INT64_MAX` and halted (ignored, `GBB_OK`).
- **Battery import.** The RTC block is parsed into a local copy and validated before any RAM or clock mutation. Size is checked first, and the bad-block cases return before anything is written. The generation bump is computed against the clock projected to now.
- **Register select and banking.** Selections `$04-$07` and `$0D-$FF` map nothing. The ROM bank is masked at write time, and zero becomes one before the mask.
- **Loader.** MBC30 markers are rejected only after the length and checksum checks. The 4 MiB MBC3 ceiling is an early bound only.
- **`gbb_reset`.** It banks elapsed time, then re-anchors the clock to the zeroed `time_half_dots`.
- **Player side.** Envelope v2 decode validates each length against an allow-list before any addition, forms the total in `uint64_t`, checks the CRC and copies nothing until all checks pass. `player_catch_up_policy` is correct at the boundaries, including `now - saved_at > INT64_MAX`, which clamps. `--clock-unix` is scoped to the battery smoke modes. Repeated, misplaced and malformed uses all fall to the usage exit.

The findings below are robustness and user-facing correctness issues. There are no blockers.

## Warnings

### WR-01: MBC30 rejection reports the "MBC1 multicart" message

**File:** `src/player/session.c:78-79`
**Issue:** Phase 9 broadened `GBB_UNSUPPORTED_CARTRIDGE_VARIANT` to mean "MBC1M or MBC30" (see `include/gabbaboy/gabbaboy.h`). `rom_error()` still maps it to "This MBC1 multicart wiring is not supported by the current preview." A user loading an MBC30 ROM (ROM code `$07` or RAM code `$05` on types `$0F-$13`) is told it is an MBC1 multicart. The player is the only consumer that turns this status into text, so the wrong cause reaches the screen and the status line.
**Fix:** Use a neutral message, because the status code cannot tell the two variants apart:
```c
case GBB_UNSUPPORTED_CARTRIDGE_VARIANT:
    return "This cartridge uses an unsupported mapper variant (MBC1 multicart or MBC30).";
```
Alternatively, have the player look at the header type byte, but keep it in the adapter.

### WR-02: The no-host-clock proof can pass vacuously or be defeated by comment text

**File:** `cmake/CheckCoreNoHostClock.cmake:84-100, 197-216`
**Issue:** There are two weaknesses in a test whose purpose is to be fail-closed.

1. The object layer takes `rc EQUAL 0` from the first `nm` that runs. It never asserts that it parsed any undefined symbols. If an `nm` variant exits 0 on a library it cannot read, or prints nothing, `gbb_symbol_count` is 0 and the test prints a success line. A real C core always imports at least `memcpy`, `malloc` and `free`, so zero symbols means the tool did not do its job.
2. `gbb_strip_comments` finds `/*` before it removes `//` comments. A line comment containing `/*` (for example `// see /* ...`) opens a block comment that swallows code up to the next `*/`. That can hide a denied call from the source layer. A `//` inside a string literal such as `"http://"` also truncates the rest of the line. Both are unlikely today, but the scan is meant to be a guard against accidental reintroduction.

**Fix:** Fail when the symbol list is empty, so the symbol layer cannot pass without reading a symbol:
```cmake
if(gbb_symbol_count EQUAL 0)
  message(FATAL_ERROR "no-host-clock-no-symbols: ${gbb_tool} listed no undefined symbols")
endif()
```
For comment stripping, scan once character by character. Alternatively, remove `//[^\n]*` first only when no `/*` precedes it on the same line, or document that the scan is best-effort and add the empty-symbol assertion.

## Info

### IN-01: `--clock-unix` accepts leading whitespace and a `+` sign

**File:** `src/player/main.c` (the `strtoll` parse in `main`, around the `clock_flag_ok` block)
**Issue:** The comment and `tests/player/clock_flag_scope.cmake` describe "a complete base-10 int64". `strtoll` also accepts leading whitespace, `+5`, `-0` and `0x...` is rejected only because base is 10. The test does not exercise these. This is harmless for a test-only flag, but the contract wording is slightly broader than the code.
**Fix:** Reject `argv[4][0]` that is not a digit or `-`, or tighten the comment to "as parsed by `strtoll`, base 10".

### IN-02: Battery block accepts any latch-edge byte

**File:** `src/core/gabbaboy.c` (`rtc_block_parse`, the `latch_prev` copy, around line 2196)
**Issue:** Byte 19 is copied without range checking. Only values the core can produce are meaningful (`$FF` after reset, otherwise the last written byte, which may be any value), so rejecting nothing is correct. However, the header text says "out-of-range field" is rejected, and this field is the one unchecked field. This is a documentation nit only.
**Fix:** State in the header comment that the latch-edge byte is stored as any value.

### IN-03: `catch_up_on_open` ignores the machine's own `ram_size` in image-size math

**File:** `src/player/session.c:706-711`
**Issue:** `player_session_apply_catch_up` hard-codes the live DH register at `ram_size + 13`, the block layout offset, instead of sharing a named constant with `rtc_block_write`. If the block layout version changes, the halted and carry reporting would silently read the wrong byte. Nothing fails today, because the core and player are in the same repo and the layout is pinned by the v1 block format.
**Fix:** Add a named constant for the offset in the public header, next to `GBB_RTC_BLOCK_SIZE`, for example `#define GBB_RTC_BLOCK_LIVE_DH_OFFSET 13u`, and use it in both places.

---

_Reviewed: 2026-10-11_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
