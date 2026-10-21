---
phase: 08-cartridge-seam-mbc5-and-mbc2
plan: 02
subsystem: cartridge
tags: [mbc2, mapper, battery, nibble-ram]
requires: [08-01]
provides:
  - "CART_MBC2 kind with type rows $05/$06 in the Cartridge mapper section"
  - "Address-bit-8 register decode, 512 canonical 0xF0|nibble cells echoed over A000-BFFF"
  - "Normalising all-or-nothing 512-byte MBC2 battery import"
  - "tests/test_mbc2.c with 11 CTests on synthetic in-memory ROMs"
affects: [08-03, 08-05]
tech-stack:
  added: []
  patterns: ["sticky-flag guest sweeps (8-bit counters wrap on 8192)", "canonical stored form so export never changes persisted bytes"]
key-files:
  created:
    - tests/test_mbc2.c
  modified:
    - src/core/gabbaboy.c
    - include/gabbaboy/gabbaboy.h
    - tests/CMakeLists.txt
    - tests/expected-tests.txt
key-decisions:
  - "MBC2 ROM bank is stored already translated (0 to 1) and masked by rom_banks-1 in cart.rom_bank_lo; read8 needs no further masking"
  - "Guest programs run straight from ROM bank 0 (never remapped on MBC2), so no WRAM bootstrap is needed"
requirements-completed: [CART-03]
status: complete
duration: 40 min
completed: 2026-10-11
commits: 3
plan_head_before: 78aedde
plan_head_after: 16f9220716870b44972c85e5b023261fabddf423
actuals:
  tokens: 22000
  tasks: 3
  commits: 3
coverage:
  - id: D1
    description: "MBC2 mapper: bit-8 decode, echoed 512-cell nibble RAM, 512-byte canonical battery image"
    human_judgment: false
    verification:
      - kind: unit
        ref: "tests/test_mbc2.c#mbc2_register_decode"
        status: pass
      - kind: unit
        ref: "tests/test_mbc2.c#mbc2_ram_echo"
        status: pass
      - kind: unit
        ref: "tests/test_mbc2.c#mbc2_battery_idempotent"
        status: pass
      - kind: unit
        ref: "tests/test_mbc2.c#mbc2_two_instance_roundtrip"
        status: pass
---

# Phase 8 Plan 02: MBC2 Summary

MBC2 ($05/$06) is a real mapper in the 08-01 seam: address bit 8 chooses RAM-enable versus ROM-bank register, 512 cells are stored as `0xF0 | nibble` and echoed across all 8192 addresses of A000-BFFF, and the battery image is exactly 512 canonical bytes with normalising, all-or-nothing import.

## Accomplishments

- `CART_MBC2`, rows $05 (no battery) and $06 (battery), max ROM code $03, header RAM code must be $00 (RAM size 512 comes from the row).
- write8 `< $4000`: bit 8 clear sets enable on `(v & 0xF) == 0xA`; bit 8 set stores bank `v & 0xF`, 0 to 1, then masks by `rom_banks-1`. `$4000-$7FFF` writes do nothing. RAM write stores canonical and bumps the generation only when the stored byte changes.
- `gbb_import_battery` for MBC2: size, then normalise-compare without writing, then single commit and one saturating generation bump; the input buffer is never written.
- Header comments describe types $05/$06 and the canonical 512-byte image; packed 256-byte images are documented as unsupported.
- 11 CTests (`mbc2_tracer`, `_header_matrix`, `_register_decode`, `_ram_echo`, `_reset`, `_battery_image`, `_battery_import`, `_battery_idempotent`, `_battery_errors`, `_battery_no_battery`, `_two_instance_roundtrip`); only `+` lines added to `tests/expected-tests.txt`.

## Evidence

- Differential: `bash .../differential/run-differential.sh --exclude-types 05,06` prints `cells=85344 lines=212442 old_sha256=b25b2024...6e8 new_sha256=b25b2024...6e8 differences=0`.
- `verify-dmg-baseline.sh`: `baseline status=pass`.
- Local ctest (phase1 build): full suite 272/272 pass; `expected-tests.txt` has 272 lines and the configure-time inventory check passed. Target subset (mbc2_, battery_, cartridge_, loader_, mbc1_continuation, dmg_baseline) 58/58.
- Sanitizers: the `phase1-asan` preset is Linux-only (CMake refuses on macOS), so I built `src/core/gabbaboy.c` with `tests/test_mbc2.c` and `tests/test_battery.c` using `-fsanitize=address,undefined -fno-sanitize-recover=undefined`; all 17 cases pass. The preset run itself is left to CI.
- Mutation check: changing the MBC2 read mask `0x1FF` to `0x0FF` made `mbc2_ram_echo` fail (it initially did not; see Deviations).
- Not proved here: Mooneye mbc2 7/7 (Plan 08-05).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Echo/silent sweep counters wrapped to zero**
- **Found during:** Task 2 (mutation check of mbc2_ram_echo)
- **Issue:** The first version counted mismatches in an 8-bit WRAM byte. Exactly 8192 or 4096 mismatches wrap to 0, so a broken echo mask passed.
- **Fix:** Sweeps now set a sticky flag instead of counting; re-ran the mutation and confirmed the test fails on a wrong mask.
- **Files modified:** tests/test_mbc2.c
- **Commit:** 60f8349

**2. [Process] Tracer commit amended once**
- Task 1's first commit omitted the test registration because a macOS `sed -i` error aborted the scripted edit; the commit was amended (local, unpushed) before any later work.

**Total deviations:** 1 auto-fixed bug (test-only), 1 process note. **Impact:** none on shipped code.

## Notes for later plans

- `docs/cartridge-and-saves.md` and `docs/native-integration.md` still say "raw RAM bytes" for the battery API; the plan scoped header comments only. Worth updating with the Phase 8 docs pass.

## Known Stubs

None.

## Threat Flags

None. T-08-06..T-08-09 mitigations are in place (row-derived RAM size, masked index and bank, size-first normalise-compare-commit import, saturating generation).

## Self-Check: PASSED

- tests/test_mbc2.c present; commits 689a86e (amended tracer), 60f8349, 16f9220 are ancestors of HEAD (verified below at commit time).
