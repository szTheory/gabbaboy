---
phase: GB-08-cartridge-seam-mbc5-and-mbc2
reviewed: 2026-10-11T00:00:00Z
depth: standard
files_reviewed: 27
files_reviewed_list:
  - .gitattributes
  - .github/workflows/fixture-repro.yml
  - .github/workflows/preview.yml
  - .gitignore
  - cmake/PreviewPackageSmoke.cmake
  - cmake/ScanForbiddenFixtures.cmake
  - cmake/VerifyMooneyeMbc.cmake
  - fixtures/mbc5-banking/banking.asm
  - include/gabbaboy/gabbaboy.h
  - src/core/gabbaboy.c
  - src/player/limitations.h
  - src/player/main.c
  - src/player/session.c
  - src/player/session.h
  - src/runner/main.c
  - tests/CMakeLists.txt
  - tests/consumers/c/main.c
  - tests/consumers/cpp/main.cpp
  - tests/player/test_limitations.c
  - tests/player/test_session.c
  - tests/scripts/reproduce-mbc5-banking.sh
  - tests/scripts/reproduce-mooneye-mbc.sh
  - tests/scripts/verify-phase3-player.sh
  - tests/test_mbc2.c
  - tests/test_mbc5.c
  - tests/test_mbc5_internal.c
  - tests/test_runner.c
findings:
  critical: 0
  warning: 2
  info: 3
  total: 5
status: issues_found
---

# Phase 8: Code Review Report

**Reviewed:** 2026-10-11
**Depth:** standard
**Files Reviewed:** 27
**Status:** issues_found

## Summary

I read the full `5673bed...HEAD` diff of `src/core/gabbaboy.c`, the public header, the runner, the player session changes, the scan and verifier scripts, the reproduction scripts, the workflows and the MBC5 guest. I checked them against the locked decisions D-01 to D-34. I also ran the `mbc|rumble|loader|limitations|session` CTest subset, and all 74 tests pass.

I found no correctness or security defect in the core. These are the specific items I checked:

- **Shift order:** `validate_header` rejects `rom_size_code > row->max_rom_code` before `32768u << code`, so the shift is bounded by 8 and never undefined.
- **Error precedence:** ceiling, then unsupported cartridge, then ROM size, then RAM size, then truncated or mismatch, then checksum, then variant. This matches D-05. Non-MBC5 type bytes keep the 2 MiB `ROM_TOO_LARGE` ceiling (D-14).
- **MBC2 decode:** writes decode by address bit 8, and zero is translated to bank 1 before masking.
- **MBC2 RAM:** it is indexed by `address & 0x1FF`, stored as `0xF0|nibble`, and the generation bumps only when the canonical byte changes.
- **MBC2 import:** the image is normalised and compared before any mutation.
- **MBC5 ROM bank:** the 9-bit bank is masked by `rom_banks - 1`, which is at least 1 because the smallest image is 32 KiB.
- **MBC5 RAM bank:** it is masked by `banks - 1`, where `banks` is at least 1 whenever `cartridge_ram_size` is nonzero.
- **Rumble:** the line is excluded from the RAM index (3 bits on rumble types). The change counter saturates. `gbb_reset` counts a change only if the line was on. A load zeroes the counters through the `cart` memset, and that memset happens after validation and allocation, so a failed load does not mutate state.
- **Battery:** the `battery_unsupported` path in the player never touches a save, lock or temp file, and the new test asserts an empty save directory.

The findings below are fail-open or drift risks in the verification and player layers, plus minor quality items.

## Warnings

### WR-01: Installed-tree scan silently skips symlinks

**File:** `cmake/ScanForbiddenFixtures.cmake:68-70`
**Issue:** `if(IS_SYMLINK "${candidate}") continue()` runs before the size and digest comparison. A symlink to a sibling ROM, for example one created by a future `install(CODE ...)` or a staging script, gets only the path-name check. If the link is named without "mooneye", the 4 MiB or 8 MiB derivative is reachable from the package and the scan reports a clean tree. This is the same fail-open class the scan exists to prevent (D-32). `GLOB_RECURSE` lists symlinked files but does not follow symlinked directories, so a symlinked directory is also never inspected.
**Fix:** Fail closed on any symlink in the scanned tree, or resolve it and scan the target.
```cmake
if(IS_SYMLINK "${candidate}")
  message(FATAL_ERROR "symlink-in-scanned-tree: ${relative}")
endif()
```

### WR-02: Player battery classification duplicates the core type table with no drift guard

**File:** `src/player/session.c:169-171`
**Issue:** `battery_unsupported` is a hard-coded list of type bytes (`$06`, `$1B`, `$1E`). The core's `cart_type_table.has_battery` is the real source of truth. Phase 9 adds MBC3 battery types (`$0F`, `$10`, `$13`) to the table. If that edit forgets this list, a cartridge that the core now accepts and exports battery RAM for gets `battery_backed=false` and `battery_unsupported=false`. The player then runs it with no save and no warning, which is exactly the silent progress loss D-22 was written to prevent. The new test pins only the three current types and `$03`. Nothing enumerates the core's battery-capable types against the player flags.
**Fix:** Add a test that loads a minimal ROM for every byte `0..255` into the core. It should assert that whenever `gbb_battery_size` returns `GBB_OK`, `player_session_identify_rom` yields exactly one of `battery_backed` or `battery_unsupported`. Alternatively, derive the flag at load time from `gbb_battery_size(machine, ...) == GBB_OK && !battery_backed`.

## Info

### IN-01: Scan digest comparison is case-sensitive

**File:** `cmake/ScanForbiddenFixtures.cmake:43-49,75-76`
**Issue:** `forbidden_digests` holds the manifest hex verbatim, and `file(SHA256)` returns lowercase. An uppercase manifest digest would never match, so the scan would pass a copied ROM that has the same size. `VerifyMooneyeMbc.cmake:~262` accepts `[0-9a-fA-F]` digests but compares with `STREQUAL`. That one fails closed on its own check, but the scan does not.
**Fix:** `string(TOLOWER "${rom_digest}" rom_digest)` when building the list.

### IN-02: Unused table columns and duplicated status block

**File:** `src/core/gabbaboy.c:73-92`; `src/player/main.c:517-520,965-969`
**Issue:**
- `has_timer` is carried in the table but never read. This is intended until Phase 9.
- `ram32_max_rom_code` is meaningful for the MBC1 rows only.
- The "Battery saving is not supported..." status and stderr warning is duplicated verbatim in two call sites.

**Fix:** Factor the text into one `static void announce_battery_unsupported(player *)` helper so the two strings cannot drift.

### IN-03: Banking guest's ninth-bit write-order checks are inert on the 64 KiB image

**File:** `fixtures/mbc5-banking/banking.asm:61-80`
**Issue:** On the committed 64 KiB image the ninth bit is masked away by `rom_banks - 1`. The C003 checks therefore prove only that a high-bit write does not clear the low byte, not that bank `$102` composes correctly. The comment says as much, and D-33/D-29 route the real ninth-bit proof through `mbc5_bank_1ff`. The result is not wrong, but C003's pass byte should not be read as ninth-bit evidence.
**Fix:** Keep the comment explicit, and keep the manifest's `scope_limits` stating that bank 256 and above is exercised only by the C005 check on the inflated image.

---

_Reviewed: 2026-10-11_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
