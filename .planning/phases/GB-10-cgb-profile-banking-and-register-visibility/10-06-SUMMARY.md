---
phase: 10-cgb-profile-banking-and-register-visibility
plan: 06
subsystem: core-postboot
tags: [cgb, post-boot, provenance, create, copy-frame, apu, div]
requires: ["10-04", "10-05"]
provides:
  - "post_boot[] with dmg, cgb and compat columns; reset_state picks the column by profile and exec_mode (no ROM on the CGB profile is compat, D-04)"
  - "gbb_create accepts GBB_PROFILE_CGB_CPU_E through a switch that rejects every other value"
  - "gbb_copy_frame returns GBB_UNSUPPORTED_PROFILE on the CGB profile after argument validation (D-05, GATE-57 DMG_ONLY)"
  - "compat B/HL licensee title-sum derivation (GATE-68, CGB_ONLY)"
  - "channel 1 enabled-but-silent post-boot state on both CGB columns (NR52 $F1, volume 0)"
affects: [10-07]
tech-stack:
  added: []
  patterns: ["three-column provenance table", "white-box sweep with a hardware-equivalent guest"]
key-files:
  created:
    - tests/test_cgb_postboot_internal.c
  modified:
    - src/core/gabbaboy.c
    - include/gabbaboy/gabbaboy.h
    - docs/model-gates.md
    - tests/test_cgb_postboot.c
    - tests/test_cgb_profile.c
    - tests/CMakeLists.txt
    - tests/expected-tests.txt
key-decisions:
  - "Only compat cells pinned by a named Mooneye test carry HW_TEST (boot_regs-cgb, boot_hwio-C, boot_div-cgbABCDE); every CGB-mode cell is PANDOCS, POLICY or ORACLE_SAMEBOY"
  - "New post_boot fields PB_NR11, PB_NR12, PB_CH1_ENABLED; APU channel memsets moved ahead of post_boot_apply in reset_state so the table can set channel 1 (DMG result identical)"
  - "GATE-03 is DMG_ONLY model_is_dmg, GATE-04..08 are BOTH with basis post_boot[] column per profile, GATE-57 is DMG_ONLY, new GATE-68 is CGB_ONLY"
  - "model_is_dmg/model_is_cgb moved above the post-boot table so the table code can use them"
requirements-completed: []
duration: 55 min
completed: 2026-10-12
status: complete
commits: 2
plan_head_before: 7bb2d6f
plan_head_after: 02434f28b3c373a61afa7588f2aaf43bd2b5a0a5
actuals:
  tokens: 60000
  tasks: 3
  commits: 2
coverage:
  - deliverable: "Creatable CGB profile, column selection by mode, CPU rows, copy_frame gate"
    human_judgment: false
    verification:
      - {kind: ctest, ref: "cgb_postboot_cgb_cpu_tracer, cgb_postboot_compat_cpu, cgb_postboot_compat_no_rom, cgb_profile_create, cgb_copy_frame_cgb, cgb_probe_parity", status: pass}
  - deliverable: "Compat title-sum B/HL and I/O literals with flip controls"
    human_judgment: false
    verification:
      - {kind: ctest, ref: "cgb_postboot_compat_title_sum, cgb_postboot_compat_io, cgb_postboot_cgb_io, cgb_postboot_compat_io_flipped, cgb_postboot_cgb_io_flipped", status: pass}
  - deliverable: "Channel 1 silent at hand-off with an audible retrigger control"
    human_judgment: false
    verification:
      - {kind: ctest, ref: "cgb_postboot_ch1_silent (mutation with post-boot volume 15 made it fail)", status: pass}
  - deliverable: "Compat DIV phase frozen at 0x2678 with a sweep"
    human_judgment: false
    verification:
      - {kind: ctest, ref: "cgb_postboot_div_phase_sweep, cgb_postboot_div_compat_default", status: pass}
---

# Phase 10 Plan 06: CGB post-boot columns and creatable CGB profile Summary

CGB-CPU-E instances can now be created; their post-boot state comes from per-profile, per-mode table columns with recorded provenance, channel 1 is enabled but provably silent, and the compat DIV phase is pinned by a sweep.

## Task commits

Tasks 1 and 2 share one commit (`4f8a792`) because both edit the same three-column `post_boot[]` table and the same test file; the CPU-row tracer cannot be separated from the table structure it depends on. Task 3 is `02434f2`.

## What was built

- **Table**: `post_boot_row` has `dmg`, `cgb` and `compat` cells. `post_boot_column()` selects DMG on the DMG profile, CGB when `exec_mode == GBB_MODE_CGB`, otherwise compat.
- **CPU rows**: compat A $11, F $80, C $00, D $00, E $08, H $00, L $7C, SP $FFFE are HW_TEST (Mooneye boot_regs-cgb). CGB mode A $11 F $80 B $00 C $00 D $FF E $56 H $00 L $0D is PANDOCS. F is $80 on the CGB profile regardless of the checksum (header branch tagged GATE-03 DMG_ONLY).
- **Compat B/HL**: derived in `compat_title_registers` from the licensee title sum (old licensee $01, or $33 with new licensee "01"; HL $991A when the sum is $43 or $58, else $007C).
- **I/O**: P1 $FF (compat HW_TEST boot_hwio-C, CGB ORACLE_SAMEBOY); SC $7E compat / $7F CGB; DMA register $00; IF $E1; NR11 $BF, NR12 $F3, NR50 $77, NR51 $F3, NR52 $F1.
- **Channel 1**: enabled with current volume 0 and a valid idle frequency/timer; no chime synthesised.
- **DIV**: compat counter 0x2678, div $26, phase 0, HW_TEST (boot_div-cgbABCDE, applicability CGB A-E); CGB-mode cells are POLICY with the "varies with header and held buttons" reason.
- **API**: `gbb_create` switch; `gbb_copy_frame` D-05 gate; header comments updated (the "only implemented model" sentence is gone).

## Tests (negative controls included)

- `cgb_postboot_*`: cgb_cpu_tracer, compat_cpu, compat_no_rom, compat_title_sum (incl. no-match and CGB-mode-ignores rows), compat_io, cgb_io, ch1_silent, div_phase_sweep, div_compat_default, plus compat_io_flipped and cgb_io_flipped (flipped NR52 expectation must fail naming the field).
- `cgb_profile_create`, `cgb_copy_frame_cgb`; `cgb_probe_parity` now loads on both profiles and cross-checks the oracle on the CGB side; `cgb_profile_unknown` no longer expects CGB create to fail.
- Mutation check: forcing post-boot channel 1 volume to 15 made `cgb_postboot_ch1_silent` fail; restored.
- Full run: `ctest --preset phase1` 455/455 passed; `tests/expected-tests.txt` matches `ctest -N`; `bash tests/scripts/verify-dmg-baseline.sh` prints `baseline status=pass`; model_gates, model_gates_selftest and the mutation tests pass.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Hardware-equivalent DIV guest timing**
- **Found during:** Task 3
- **Issue:** The plan's NOP counts alone (27, 57, 56, 57, 57, 58) with a 4-M-cycle capture did not reproduce the expected DIV sequence 27 28 28 29 2A 2C; the cadence needs 64 M-cycles per read.
- **Fix:** Each capture is LDH, LD r,A and three padding NOPs, and the entry sequence is NOP then JP (usual cartridge entry). With those, the passing set is exactly 0x2678..0x267B for both phases.
- **Files modified:** tests/test_cgb_postboot_internal.c
- **Commit:** 02434f2

**2. [Rule 2 - Missing critical] Extra negative controls and a no-ROM case**
- Added `compat_io_flipped`, `cgb_io_flipped` and `compat_no_rom` (D-04) beyond the plan's names, per the verification-with-negative-control rule.

**3. [Rule 3 - Blocking] Moved APU channel memsets and the model predicates**
- `reset_state` cleared the APU channels after `post_boot_apply`, which would erase channel 1; the clears now precede it (DMG result unchanged, baseline passes). `model_is_dmg/cgb` moved above the table.

## Known Stubs

None.

## Threat Flags

None. T-10-09 and T-10-10 mitigations are in place (volume-0 policy proven by test and mutation; HW_TEST only on compat cells with a named Mooneye source).

## Self-Check: PASSED
