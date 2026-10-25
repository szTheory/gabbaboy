---
phase: 11-cgb-colour-rendering-and-player-colour
plan: 10
subsystem: third-party-cgb-ppu-evidence
tags: [magentests, rgb555, d-21, d-20, mutants, reproduction]
requires:
  - phase: 11-cgb-colour-rendering-and-player-colour
    provides: "11-07/11-09 gbb_accept_rgb555_digest, colour mutant harness, CGB colour path"
provides:
  - "Three MagenTests 0.5.0 CGB ROMs vendored with digests, MIT notice, labels and rights records"
  - "magentests_cgb_* drivers with literal RGB555 predicates and three colour mutants with controls"
  - "Table-driven reproduce-magentests.sh covering all six ROMs"
affects: [11-11]
requirements-completed: []
actuals:
  tokens: 45000
  tasks: 3
  commits: 3
coverage:
  - id: C1
    description: "ppu_disabled_state runs on the CGB profile for 20 frames, the last two LCD-on frames are identical and every pixel is 0x03E0, matching the pinned digest; the same ROM in compatibility mode yields one uniform default BG value"
    requirement: CGB-04
    human_judgment: false
    verification:
      - kind: integration
        ref: "magentests_cgb_ppu_disabled_state"
        status: pass
      - kind: integration
        ref: "magentests_cgb_ppu_disabled_state_compat"
        status: pass
  - id: C2
    description: "oam_internal_priority matches the 84-pixel mask derived from the pinned source and bg_oam_priority matches the eight-cell layout with no 0x001F pixel, both before their digests are accepted"
    requirement: CGB-04
    human_judgment: false
    verification:
      - kind: integration
        ref: "magentests_cgb_oam_internal_priority"
        status: pass
      - kind: integration
        ref: "magentests_cgb_bg_oam_priority"
        status: pass
  - id: C3
    description: "Each predicate can fail: skipping the LCD-off mode-0 transition, resolving object colours from BG CRAM and inverting the LCDC.0 composer each fail their ROM, and the controls pass on the same mutant binary"
    requirement: CGB-04
    human_judgment: false
    verification:
      - kind: integration
        ref: "magentests_cgb_mutant_lcd_off_no_mode0"
        status: pass
      - kind: integration
        ref: "magentests_cgb_mutant_lcd_off_no_mode0_control"
        status: pass
      - kind: integration
        ref: "magentests_cgb_mutant_obj_from_bg_cram"
        status: pass
      - kind: integration
        ref: "magentests_cgb_mutant_obj_from_bg_cram_control"
        status: pass
      - kind: integration
        ref: "magentests_cgb_mutant_lcdc0_inverted"
        status: pass
      - kind: integration
        ref: "magentests_cgb_mutant_lcdc0_inverted_control"
        status: pass
  - id: C4
    description: "Vendored bytes match the manifest, stay out of installs, and the rebuild table agrees with the manifest rows; the DMG baseline and existing mbc_oob_sram cases are unchanged"
    requirement: CGB-04
    human_judgment: false
    verification:
      - kind: unit
        ref: "magentests_fixture_digest"
        status: pass
      - kind: integration
        ref: "magentests_not_installed"
        status: pass
      - kind: other
        ref: "bash tests/scripts/reproduce-magentests.sh --self-check"
        status: pass
      - kind: other
        ref: "bash tests/scripts/verify-dmg-baseline.sh"
        status: pass
status: complete
commits: 3
plan_head_before: 361256dfa04256a2e185071929686a14398c1755
plan_head_after: a52953b2716c9106f412e71383f211053d96cbbe
duration: 30 min
completed: 2026-10-12
---

# Phase 11 Plan 10: MagenTests CGB PPU ROMs Summary

Three MagenTests 0.5.0 CGB ROMs (`ppu_disabled_state`, `bg_oam_priority`, `oam_internal_priority`) are admitted with rights and digest records, each checked against a literal RGB555 predicate typed from the pinned upstream source, with a mutant control per ROM and a table-driven rebuild script.

## Accomplishments

- Each ROM was downloaded into a fresh scratch directory and its size, SHA-256 and `$143` byte checked against the RESEARCH values before copying. The upstream source was read from a scratch clone at 3f9c090f and not vendored.
- `tests/test_magentests.c` gained a CGB driver: 20 frames on `GBB_PROFILE_CGB_CPU_E`, the last two `gbb_copy_frame_rgb555` captures byte-identical and `frame_info.generation` strictly advancing (so a retained or LCD-off frame cannot pass), then the predicate, then the digest. The DMG `expect_screen` path and the `mbc_oob_sram` cases are unchanged.
- The `oam_internal_priority` mask was derived by hand from `graphics_data.asm` and `main.asm` (recorded in ELIGIBILITY.md under "oam_internal_priority mask derivation"): 42 opaque pixels per box, 84 in total, agreeing with the RESEARCH simulation, so no disagreement exists.
- Digests were cross-checked with an independent Python SHA-256 over the expected image built from the predicates, not just taken from the core: uniform green `7a137aaa...10e0`, oam_internal_priority `edf38b0b...6299`, bg_oam_priority `5a356fe0...895a`.
- `reproduce-magentests.sh` now rebuilds from one table (name, source dir, rgbfix options) and its self-check requires the manifest rows and the table to name the same files with the same `source_dir` and `rgbfix_options` (negative control run by corrupting a table row: self-check fails). `.gitattributes` marks the ROMs binary.

## bg_oam_priority outcome

It passed its literal predicate on the unmodified core, so no expected-unsupported record was needed, no core fix was made, and the digest is pinned. The LCDC.0 mutant therefore applies.

## D-20 deviation: AGE

AGE at 1f5bc10e has no CGB colour, attribute or priority ROM (only m3-bg-lcdc and m3-bg-scx, expected-unsupported for mode-3 pixel timing, D-09). Roadmap success criterion 1 is met by these MagenTests ROMs, the plan 11-07 and 11-08 original fixtures and the plan 11-01/11-05 priority truth table, not by AGE. ELIGIBILITY.md states this. The AGE expected-unsupported records belong to plan 11-11.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] `.gitignore` ignores `*.gbc`**
- **Found during:** Task 1 (`git add` refused the ROM)
- **Fix:** added `!/fixtures/magentests/{ppu_disabled_state,bg_oam_priority,oam_internal_priority}.gbc` beside the existing mbc_oob_sram exceptions
- **Files modified:** `.gitignore`
- **Commit:** 61da394

**2. [Rule 3 - Blocking] Manifest rows for the three mbc_oob_sram ROMs needed `source_dir` and `rgbfix_options`**
- **Why:** the plan requires the self-check to compare manifest and table field by field, which needs the same fields on every row
- **Files modified:** `fixtures/magentests/manifest.json`
- **Commit:** a52953b

### Notes

- The local RGBDS is 1.0.4, so `reproduce-magentests.sh --compare` (which requires v0.6.1) could not be run here. The three new ROMs are admitted by release digest; whether the pinned rebuild is byte-identical is reported only by the hosted `magentests-repro` job, and SOURCES.md says so.
- `.planning/milestone.lock` is untracked runtime state and was not staged.

## Verification

- `ctest --preset phase1 --output-on-failure --no-tests=error`: 673 of 673 passed. `phase1-asan` is Linux-only and runs in CI.
- `bash tests/scripts/verify-dmg-baseline.sh`: `baseline status=pass`.
- `bash tests/scripts/reproduce-magentests.sh --self-check`: `self-check=pass`.

## Known Stubs

None.

## Threat Flags

None.

## Self-Check: PASSED

Created files present: the three `.gbc` ROMs under `fixtures/magentests/`; commits 61da394, 631d5d7 and a52953b are on the branch.
