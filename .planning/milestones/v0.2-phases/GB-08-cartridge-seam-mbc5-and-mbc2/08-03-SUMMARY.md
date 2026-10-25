---
phase: 08-cartridge-seam-mbc5-and-mbc2
plan: 03
subsystem: cartridge
tags: [mbc5, mapper, rumble, rom-ceiling, public-api]
requires: [08-01, 08-02]
provides:
  - "CART_MBC5 kind with type rows $19-$1E, 9-bit ROM banking (bank 0 selectable at $4000), RAM to 128 KiB"
  - "Type-aware early ROM ceiling: 8 MiB for MBC5 rows, 2 MiB for every other row and no-row type"
  - "GBB_NO_RUMBLE (18) and gbb_rumble_state() with saturating transition counter"
  - "tests/test_mbc5.c (14 CTests) and tests/test_mbc5_internal.c (single-TU saturation test)"
affects: [08-05, 08-07, 08-08]
tech-stack:
  added: []
  patterns: ["single-TU white-box test including src/core/gabbaboy.c, not linked to the core library", "sticky stamps (low byte plus bank>>8) so banks 2 and $102 are distinguishable"]
key-files:
  created:
    - tests/test_mbc5.c
    - tests/test_mbc5_internal.c
  modified:
    - src/core/gabbaboy.c
    - include/gabbaboy/gabbaboy.h
    - tests/CMakeLists.txt
    - tests/expected-tests.txt
    - tests/consumers/c/main.c
    - tests/consumers/cpp/main.cpp
key-decisions:
  - "GBB_MAX_ROM_SIZE became 8 MiB; the old 2 MiB value is GBB_LEGACY_MAX_ROM_SIZE, used by every non-MBC5 row and the no-row fallback"
  - "MBC5 bank composition lives in one helper whose single line holds the anchor '& 1u) << 8' (once in the file)"
  - "Rumble reset transition is recorded in gbb_reset only, never in reset_state, so loads and gbb_create never count"
requirements-completed: [CART-02]
status: complete
duration: 55 min
completed: 2026-10-11
commits: 3
plan_head_before: 61853e47287f5829f6030baf472e06526a68f982
plan_head_after: 0173f87a360802fd04d4e2ca08a0deef9c03eae6
actuals:
  tokens: 36000
  tasks: 3
  commits: 3
coverage:
  - id: D1
    description: "MBC5 mapper: 9-bit ROM banking, RAM enable/banking to 128 KiB, battery, no-RAM window"
    human_judgment: false
    verification:
      - kind: unit
        ref: "tests/test_mbc5.c#mbc5_rom_banking"
        status: pass
      - kind: unit
        ref: "tests/test_mbc5.c#mbc5_ram_enable"
        status: pass
      - kind: unit
        ref: "tests/test_mbc5.c#mbc5_ram_banking"
        status: pass
      - kind: unit
        ref: "tests/test_mbc5.c#mbc5_battery"
        status: pass
  - id: D2
    description: "Type-aware 8 MiB ceiling that leaves every other type's loader result unchanged"
    human_judgment: false
    verification:
      - kind: unit
        ref: "tests/test_mbc5.c#mbc5_rom_bound"
        status: pass
      - kind: other
        ref: "run-differential.sh --exclude-types 05,06,19,1A,1B,1C,1D,1E"
        status: pass
  - id: D3
    description: "gbb_rumble_state / GBB_NO_RUMBLE with exact reset, load and saturation semantics"
    human_judgment: false
    verification:
      - kind: unit
        ref: "tests/test_mbc5.c#mbc5_rumble_reset_load"
        status: pass
      - kind: unit
        ref: "tests/test_mbc5_internal.c#mbc5_rumble_saturation"
        status: pass
      - kind: unit
        ref: "installed_consumer_c / installed_consumer_cpp"
        status: pass
---

# Phase 8 Plan 03: MBC5 Summary

MBC5 ($19-$1E) is a real mapper in the 08-01 seam: independent low-8 and bit-8 ROM bank registers (bank 0 reachable at $4000-$7FFF, no remap), RAM banking to 128 KiB with the rumble bit masked out of the RAM index, a type-aware 8 MiB ROM ceiling, and a new public `gbb_rumble_state`/`GBB_NO_RUMBLE`.

## Accomplishments

- Six rows $19-$1E; `CART_RAM_MBC5` maps codes $02/$03/$05/$04 to 8/32/64/128 KiB, rejects every other code; no-RAM rows ($19, $1C) accept only $00. Every MBC5 row maps A000-BFFF, so a no-RAM read returns $FF with no unsupported-bus stop.
- write8: $0000-$1FFF low-nibble `$A` enable, $2000-$2FFF low 8 bank bits, $3000-$3FFF bit 8 from value bit 0, $4000-$5FFF RAM bank (4 bits, or 3 bits plus the motor line on rumble rows), $6000-$7FFF ignored.
- `GBB_MAX_ROM_SIZE` is 8 MiB; `GBB_LEGACY_MAX_ROM_SIZE` (2 MiB) is the early ceiling for all other rows and for type bytes with no row, at the same precedence slot, so earlier error classes are unchanged. `src/player/session.c`, `tests/test_loader.c` and `tests/test_loader_fuzz.c` are untouched.
- Header docs: MBC5 types, ROM codes $00-$08, RAM codes, CGB flag ignored, type-aware ceiling, 8 MiB + 128 KiB allocation bound.
- `gbb_rumble_state`: NULL checks first, `GBB_NO_RUMBLE` with no ROM or non-rumble type, outputs only written on success; reset counts one change only from line-on; successful load zeroes both.
- Installed C and C++ consumers call `gbb_rumble_state` and require `GBB_NO_RUMBLE` with unchanged sentinels.
- 15 new CTests: `mbc5_tracer`, `_header_matrix`, `_rom_banking`, `_ram_enable`, `_ram_banking`, `_no_ram_window`, `_battery`, `_rom_bound`, `_cgb_flag_ignored`, `_cross_mapper_control`, `_rumble_state`, `_rumble_errors`, `_rumble_reset_load`, `_reset_preserves_ram`, `_rumble_saturation`. Only `+` lines in `tests/expected-tests.txt`.

## Evidence

- Local ctest (phase1 build): full suite 287/287 pass; `tests/expected-tests.txt` has 287 lines (inventory check passed at configure); `ctest -N -R '^mbc5_'` lists 15; 15 `mbc5_` names in the inventory. Target subset (mbc5_, mbc2_, installed_consumer_c/cpp, cartridge_, battery_, loader_, dmg_baseline) 74/74. Installed consumers ran against the relocated `build/package-prefix`.
- Differential: `run-differential.sh --exclude-types 05,06,19,1A,1B,1C,1D,1E` prints `cells=83328 lines=210426 old_sha256=15f93a2c...b52b new_sha256=15f93a2c...b52b differences=0`.
- `verify-dmg-baseline.sh`: `baseline status=pass`.
- Anchor: `grep -c '& 1u) << 8' src/core/gabbaboy.c` is 1.
- Sanitizers: `phase1-asan` is Linux-only, so I compiled `tests/test_mbc5.c` with the core, and `tests/test_mbc5_internal.c`, with `-fsanitize=address,undefined -fno-sanitize-recover=undefined`; all 15 cases pass. The preset run itself is left to CI.
- Mutation checks (each failed the named test, then reverted): bank-0 remap (tracer); lo write clearing hi, hi write clearing lo, hi bit taken from value bit 1 (rom_banking/rom_bound); exact-$0A enable (ram_enable); 3-bit RAM mask on non-rumble (ram_banking); unmasked RAM read (ram_banking); 8 MiB ceiling for all rows or for no-row types (rom_bound, loader_boundary_fuzz); banked low window (all); unconditional generation bump (battery); unguarded rumble increment on the write path and on the reset path (rumble_saturation); 4-bit mask on rumble rows (rumble_state, reset_preserves_ram); reset not counting or not clearing the line (rumble_reset_load); `ram_enabled` or `ram_bank` not reset (reset_preserves_ram); line gated on RAM enable (rumble_state). Sweeps use sticky checks or bounded sequences with no wrapping 8-bit counters.
- Not proved here: Mooneye mbc5 (Plan 08-05), the $1FF original fixture (Plan 08-08; `mbc5_rom_bound` does read bank $1FF on a synthetic 8 MiB image).

## Deviations from Plan

None - plan executed exactly as written. (Rumble fields `rumble_on`/`rumble_changes` already existed in `cart_state` from Plan 08-01 and were used as planned.)

## Known Stubs

None.

## Threat Flags

None. The new public entry point `gbb_rumble_state` is covered by T-08-13.

## Self-Check: PASSED

- FOUND: tests/test_mbc5.c, tests/test_mbc5_internal.c
- FOUND commits 628dfe7, 690e6fd, 0173f87 on the branch
- Full local ctest 287/287; inventory agrees with tests/expected-tests.txt
