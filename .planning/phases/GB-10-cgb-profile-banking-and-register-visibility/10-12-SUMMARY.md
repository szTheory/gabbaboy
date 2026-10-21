---
phase: 10-cgb-profile-banking-and-register-visibility
plan: 12
subsystem: core-bus-tests
tags: [cgb, wram-bank, vram-bank, echo-ram, oam-dma, mutant]
requires: [10-11]
provides: [cart_read helper, CGB OAM DMA source map, public banking tests, echo and DMA-bank core mutants]
affects: [13, 17, 18, 19, 20]
key-files:
  created: [tests/test_banking.c]
  modified: [src/core/gabbaboy.c, docs/model-gates.md, docs/cgb-profile.md, tests/CMakeLists.txt, tests/expected-tests.txt]
requirements-completed: []
status: complete
commits: 2
plan_head_before: 17c2978bc7d8fe50917006853fbe679c20250d06
plan_head_after: 8b419a0f51b4274685732bbf5286a86aeefbfb7c
actuals:
  tokens: 40000
  tasks: 3
  commits: 2
duration: 40 min
completed: 2026-10-12
coverage:
  - id: 10-12-cgb-dma-map
    description: "CGB OAM DMA source map (ROM/cart RAM via shared cart_read, banked VRAM, banked WRAM, E0-FF=$FF); DMG envelope frozen"
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest --test-dir build/phase15_1_14 --output-on-failure -R '^banking_dma_wram_bank$'"
        status: pass
      - kind: integration
        ref: "ctest --test-dir build/phase15_1_14 --output-on-failure -R '^banking_dma_vram_bank$'"
        status: pass
      - kind: integration
        ref: "ctest --test-dir build/phase15_1_14 --output-on-failure -R '^banking_dma_rom_page$'"
        status: pass
      - kind: integration
        ref: "ctest --test-dir build/phase15_1_14 --output-on-failure -R '^banking_dma_cart_ram$'"
        status: pass
      - kind: integration
        ref: "ctest --test-dir build/phase15_1_14 --output-on-failure -R '^banking_dma_high_pages$'"
        status: pass
      - kind: integration
        ref: "ctest --test-dir build/phase15_1_14 --output-on-failure -R '^dma_source_mapping$'"
        status: pass
  - id: 10-12-banking-echo
    description: "VBK/SVBK independence, read-back, and echo RAM following the selected WRAM bank, through guest code"
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest --test-dir build/phase15_1_14 --output-on-failure -R '^banking_vbk_independence$'"
        status: pass
      - kind: integration
        ref: "ctest --test-dir build/phase15_1_14 --output-on-failure -R '^banking_svbk_readback$'"
        status: pass
      - kind: integration
        ref: "ctest --test-dir build/phase15_1_14 --output-on-failure -R '^banking_echo_follows_bank$'"
        status: pass
      - kind: integration
        ref: "ctest --test-dir build/phase15_1_14 --output-on-failure -R '^banking_dmg_banks_frozen$'"
        status: pass
  - id: 10-12-dmg-conflict
    description: "D-17 DMG bus-conflict rule kept on CGB, pinned and documented as expected-failure:cgb-separate-buses"
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest --test-dir build/phase15_1_14 --output-on-failure -R '^banking_bus_conflict_cgb_pin$'"
        status: pass
  - id: 10-12-mutant-controls
    description: "Core-mutant controls for echo bank and DMA bank"
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest --test-dir build/phase15_1_14 --output-on-failure -R '^banking_mutant_echo_ignores_bank$'"
        status: pass
      - kind: integration
        ref: "ctest --test-dir build/phase15_1_14 --output-on-failure -R '^banking_mutant_echo_control$'"
        status: pass
      - kind: integration
        ref: "ctest --test-dir build/phase15_1_14 --output-on-failure -R '^banking_mutant_dma_wrong_bank$'"
        status: pass
      - kind: integration
        ref: "ctest --test-dir build/phase15_1_14 --output-on-failure -R '^banking_mutant_dma_control$'"
        status: pass
---

# Phase 10 Plan 12: CGB OAM DMA sources, echo and banking proofs Summary

The cartridge read switch is now a shared `cart_read`, the CGB profile (both modes) has its own OAM DMA source map (ROM and cartridge RAM through the mapper, `vram[vram_bank]`, banked WRAM, `$FF` for E0-FF) while the DMG envelope is untouched, and ten public-API guest cases plus two core mutants prove banks, echo and DMA sources.

## Accomplishments

- `src/core/gabbaboy.c`: `cart_read` extracted from `read8` (identical behaviour, one call from `read8`, GATE-22 moved with it). `dma_source_read` now has a `CGB_ONLY GATE-51 GUARD=model_is_cgb` branch and a `DMG_ONLY GATE-75 GUARD=model_is_dmg` branch that keeps D-024 exactly. `dma_advance_half_dot` and the DMA period are unchanged.
- `docs/model-gates.md`: GATE-51 changed from `UNKNOWN research:10` to `CGB_ONLY model_is_cgb`; GATE-75 added; GATE-22 site now `cart_read`. Scanner: functions=147 gates=76.
- `tests/test_banking.c` (new): guests built with a small assembler, run on DMG, CGB and compat views. Expected values come from the ROM image bytes or the guest's own write pattern, never from the core. Cases: `dma_wram_bank` (tracer: D0 page under SVBK 2 gives `$20..`; under 3 gives `$30..`; C0 page ignores SVBK), `vbk_independence`, `svbk_readback` (`$F8|raw`, marker per bank, bank 0 aliases bank 1), `echo_follows_bank` (F000/F001/FDFF under every SVBK; E000/E001/EFFF mirror C000 band), `dma_vram_bank`, `dma_rom_page` (page 00 and switchable page 40 under MBC5 bank 2; DMG `$FF`), `dma_high_pages` (E0, F0, FE, FF on all three views), `dma_cart_ram` (MBC5 RAM; RAM-disabled negative control returns `$FF`), `dmg_banks_frozen` (CPU view and DMA view on DMG and compat), `bus_conflict_cgb_pin` (CGB and compat read `$FF` and drop the write exactly like DMG).
- `tests/CMakeLists.txt`: `gbb_banking_mutant` builds a configure-time copy of the core with an exactly-once anchor (forward and reverse `string(FIND)`), as a test-only static library. Echo mutant: `F000+` always bank 1; DMA mutant: CGB D0-DF page always bank 1. Each fails its named case at a named REQUIRE (`echo_reads_match`, `oam_is_pattern(m, 0x20)`) and passes an unrelated case (`vbk_independence`, `svbk_readback`) in the same mutant.
- `docs/cgb-profile.md`: "Banked memory and OAM DMA sources" with the page table (cartridge and E0-FF cells labelled `PANDOCS [VERIFY]` / `ORACLE_SAMEBOY [VERIFY]`, explicitly not hardware) and the D-17 limitation `expected-failure:cgb-separate-buses`.

## Verification

- Full suite (`ctest --preset phase1`): 499/499 pass, including all 14 new `banking_*` tests, `dma_*`, `bus_*`, `cgb_tables_*` and `model_gates*`.
- `bash tests/scripts/verify-dmg-baseline.sh`: `baseline status=pass`, rows=0. `python3 -I tests/scripts/verify-model-gates.py`: pass.
- Extra negative control (not committed): making the CGB branch return `$FF` for ROM/cart addresses failed exactly `banking_dma_rom_page` and `banking_dma_cart_ram` and nothing else; source restored byte-identical before commit.

## Fresh behavior recheck (2026-10-21)

Configured the isolated `build/phase15_1_14` tree from the current checkout and built the current core, guest-test executables, and configure-time echo/DMA mutant cores. The 15 mapped banking and DMA CTests plus the eight STOP/KEY0 controls passed in the focused 23/23 run. This is current software-model evidence; the original full-suite and producer statements above remain historical.

## Deviations from Plan

**1. Two commits, not three.** Task 1's core change is commit 7736589. Tasks 2 and 3 edit the same `tests/CMakeLists.txt` region and the same `tests/expected-tests.txt` block (test registration and the mutant function sit together) and the tracer case lives in the same test file as the others, so splitting would need a synthetic partial state; they are in commit 8b419a0.

**2. [Rule 3 - Blocker] Image type for non-RAM guests.** The first run failed to load because a 64 KiB image with a ROM-only header type is rejected by the loader. The helper constant `T_ROM_ONLY` is therefore MBC5 without RAM (`$19`), comment in the test. No core change.

**3. Mutant regex naming.** The plan asks for a regex naming the failing REQUIRE in `echo_follows_bank` and `dma_wram_bank`; the echo case aggregates its comparisons into the variable `echo_reads_match` so the REQUIRE text names the discriminating check.

**Total deviations:** 3 (one blocker fix in test harness, two structural notes). **Impact:** none on behaviour or scope.

## Known Stubs

None.

## Threat Flags

None. T-10-18 mitigations: every CGB DMA source page maps to a bounded helper (`cart_read` masks banks, `wram_byte` uses `wram_bank` 1..7, VRAM bank 0..1, E0-FF constant); `banking_dma_*` cover each range and the mutants cover the bank selection.

## Notes for later plans

- CGB-03 is not marked complete: Plans 10-13, 10-17, 10-18, 10-19 still declare it.
- The cart and E0-FF DMA cells remain PANDOCS/ORACLE_SAMEBOY claims; no hardware evidence exists for CGB-E.

## Self-Check: PASSED

- FOUND: tests/test_banking.c, 10-12-SUMMARY.md
- FOUND commits: 7736589, 8b419a0 (ancestors of HEAD)
