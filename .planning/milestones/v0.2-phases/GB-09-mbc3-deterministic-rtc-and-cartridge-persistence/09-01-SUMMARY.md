---
phase: 09-mbc3-deterministic-rtc-and-cartridge-persistence
plan: 01
subsystem: cartridge-mapper
tags: [mbc3, cartridge, loader, ctest]
requires: []
provides:
  - "MBC3 types $0F-$13 in the cartridge seam (7-bit ROM banking, RAM banks 0-3, RAM gate)"
  - "MBC30 rejection as GBB_UNSUPPORTED_CARTRIDGE_VARIANT after the checksum"
  - "cart_state.has_timer and cartridge_info.has_timer filled from the type row"
affects: [09-02, 09-07, 09-09, 09-11]
tech-stack:
  added: []
  patterns: ["translate-then-mask ROM bank at write time (MBC2 idiom)", "RAM-rule variant marker answered after checksum"]
key-files:
  created: [tests/test_mbc3.c]
  modified: [src/core/gabbaboy.c, include/gabbaboy/gabbaboy.h, tests/CMakeLists.txt, tests/expected-tests.txt, tests/test_mbc5.c]
key-decisions:
  - "Selections $04-$07 and $0D-$FF map nothing; labelled a software-model decision in source, not hardware-qualified"
  - "RAM code $05 on $10/$12/$13 is accepted by the RAM rule only as an MBC30 marker, so it reaches the variant slot after length and checksum"
requirements-completed: [CART-04]
coverage:
  - id: D1
    description: "MBC3 cartridge types, banking, RAM gate, reset, and battery generation behavior pass the focused mapper suite"
    verification:
      - kind: integration
        ref: "Fresh Phase 15.1-11 run: ctest --test-dir build --output-on-failure -R '^mbc3_(tracer|header_matrix|rom_banking|ram_banking|ram_gate|unmapped_select|absent_ram|reset|battery_generation)$' (9/9 passed)"
        status: pass
    human_judgment: false
status: complete
commits: 2
plan_head_before: f26d3ad320c3690d8f41c2da5834ab83527ee720
plan_head_after: 0aed690f372f508b6f425d69ab825d8f0a4ff658
actuals:
  tokens: 30000
  tasks: 2
  commits: 2
duration: 25 min
completed: 2026-10-11
---

# Phase 9 Plan 01: MBC3 mapper and header matrix Summary

MBC3 cartridges `$0F-$13` load through the Phase 8 seam with 7-bit ROM banking, RAM banks 0-3, the `(v & 0x0F) == 0x0A` gate, 4 MiB early ceiling and MBC30 (ROM `$07` / RAM `$05`) rejection after the checksum; nine synthetic-image `mbc3_*` CTests pin it.

## Accomplishments

- Five type rows, `CART_MBC3`, `CART_RAM_MBC3`, `GBB_MBC3_MAX_ROM_SIZE`, `has_timer` carried into `cart_state`; read8/write8 cases follow the MBC5 shape with translate-before-mask ROM banking.
- Tracer (`mbc3_tracer`) proves synthetic ROM -> loader -> mapper -> guest-visible bytes -> CTest.
- `mbc3_header_matrix`, `rom_banking`, `ram_banking`, `ram_gate`, `unmapped_select`, `absent_ram`, `reset`, `battery_generation` pin D-01 to D-03 and the CART-05 adjacency edge (2 MiB loads, 4 MiB variant, 4 MiB + 1 too large).
- Public header comments updated (4 MiB ceiling, MBC3 types, MBC30 variant, battery text).
- Verification: full `ctest --preset phase1` 329/329 passed; `tests/baseline` untouched versus main.

## Task Commits

1. Task 1 (tracer): 3f3ac79
2. Task 2 (matrix and header text): 0aed690

## Deviations from Plan

**1. [Rule 1 - Plan inconsistency] `$AA` enables the RAM gate**
- **Found during:** Task 2 (ram_gate)
- **Issue:** The plan lists `$AA` among disabling values, but D-03 (and the plan's own must_haves) decode the gate as `(v & 0x0F) == 0x0A`, under which `$AA` enables.
- **Fix:** The test asserts `$AA` enables, matching D-03 and the implementation.
- **Files modified:** tests/test_mbc3.c

**2. `battery_api_fuzz` needed no change.** The `$13` header cases still pass with the new rows, so no expectation was altered.

**3.** `$08-$0C` selection on timer types is tested only for `$11/$12/$13`; timer types ($0F/$10) behave as unmapped until Plan 09-09 and are deliberately not pinned here.

**Total deviations:** 1 plan-text correction. **Impact:** none on behavior.

## Known Stubs

None. The `$6000-$7FFF` latch write is ignored and `$08-$0C` on timer types reads `$FF` by design until Plan 09-09 supplies the RTC.

## Threat Flags

None.

## Self-Check: PASSED

- tests/test_mbc3.c present; commits 3f3ac79 and 0aed690 on HEAD; acceptance greps pass; full CTest 329/329.

## Current Verification — 15.1-11

The focused nine-test MBC3 mapper batch passed on the current checkout. This is current local regression evidence; it does not upgrade the historical software-model choices to hardware-backed claims.
