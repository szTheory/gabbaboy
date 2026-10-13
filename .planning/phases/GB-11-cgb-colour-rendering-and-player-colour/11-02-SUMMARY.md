---
phase: 11-cgb-colour-rendering-and-player-colour
plan: 02
subsystem: cgb-palette-ram-ports
tags: [cram, bcpd, ocpd, opri, d-08, d-10, d-11, d-12, d-13, d-14, d-31, d-40, mutant-controls]
requires:
  - phase: 11-cgb-colour-rendering-and-player-colour
    provides: "11-01 colour mutant harness and DMG identity pin"
provides:
  - "bg_cram[64], obj_cram[64] and opri storage on the instance"
  - "BCPD and OCPD data ports with auto-increment, blocked-write increment and mode-3 lockout"
  - "OPRI stored bit 0 with no priority effect after boot"
  - "post_boot rows for bg_cram_fill, obj_cram_fill (white) and opri, mirrored in docs/cgb-profile.md"
  - "No DEFERRED(11) cell remains in table, docs or tests"
affects: [11-03, 11-04, 11-05]
requirements-completed: [CGB-04]
actuals:
  tokens: 60000
  tasks: 3
  commits: 3
coverage:
  - id: C1
    description: "BCPD auto-increments across all 64 bytes, wraps 63 to 0 keeping bit 7 and bit 6, reads never advance, and all 8 bits of every byte are stored"
    human_judgment: false
    verification:
      - kind: unit
        ref: "palette_cram_bg_autoinc"
        status: pass
      - kind: unit
        ref: "palette_cram_bg_readback"
        status: pass
  - id: C2
    description: "A mode-3 blocked write keeps the byte but still advances the index, a blocked read returns FF without advancing, and LCD off lifts the lock"
    human_judgment: false
    verification:
      - kind: unit
        ref: "palette_cram_bg_blocked_write"
        status: pass
      - kind: unit
        ref: "palette_cram_bg_blocked_read"
        status: pass
      - kind: unit
        ref: "palette_cram_lockout_lcd_off"
        status: pass
  - id: C3
    description: "OCPD mirrors BCPD independently of the background side, and compat mode reads FF and ignores writes with no increment"
    human_judgment: false
    verification:
      - kind: unit
        ref: "palette_cram_obj_autoinc"
        status: pass
      - kind: unit
        ref: "palette_cram_compat_ports"
        status: pass
  - id: C4
    description: "OPRI stores bit 0, reads FE or the bit in CGB mode, changes no other instance state and is inert in compat mode"
    human_judgment: false
    verification:
      - kind: unit
        ref: "palette_opri_cgb"
        status: pass
      - kind: unit
        ref: "palette_opri_compat"
        status: pass
  - id: C5
    description: "Post-boot CRAM is white in CGB and compat mode after load and reset, and VRAM bank 1 is zero after every load and reset"
    human_judgment: false
    verification:
      - kind: unit
        ref: "cgb_postboot_cram_white"
        status: pass
      - kind: unit
        ref: "cgb_postboot_vram1_zero"
        status: pass
      - kind: unit
        ref: "cgb_tables_postboot"
        status: pass
  - id: C6
    description: "The three DEFERRED(11) cells flip together in table, decode, docs and independent visibility expectations"
    human_judgment: false
    verification:
      - kind: unit
        ref: "cgb_tables_io"
        status: pass
      - kind: integration
        ref: "cgb_visibility_matrix_cgb"
        status: pass
      - kind: integration
        ref: "cgb_visibility_deferred_stop"
        status: pass
      - kind: integration
        ref: "cgb_visibility_matrix_compat"
        status: pass
      - kind: integration
        ref: "cgb_visibility_matrix_dmg"
        status: pass
  - id: C7
    description: "Each palette port rule has a mutant that makes its test fail while a control case still passes"
    human_judgment: false
    verification:
      - kind: unit
        ref: "palette_mutant_blocked_no_increment"
        status: pass
      - kind: unit
        ref: "palette_mutant_read_increments"
        status: pass
      - kind: unit
        ref: "palette_mutant_lock_always_allowed"
        status: pass
      - kind: unit
        ref: "palette_mutant_lock_ignores_lcd_off"
        status: pass
      - kind: unit
        ref: "palette_mutant_blocked_no_increment_control"
        status: pass
      - kind: unit
        ref: "palette_mutant_read_increments_control"
        status: pass
      - kind: unit
        ref: "palette_mutant_lock_always_allowed_control"
        status: pass
      - kind: unit
        ref: "palette_mutant_lock_ignores_lcd_off_control"
        status: pass
  - id: C8
    description: "Every new function and model-differing branch carries a MODEL tag with a docs row, and the DMG baseline is byte-identical"
    human_judgment: false
    verification:
      - kind: unit
        ref: "model_gates"
        status: pass
      - kind: other
        ref: "bash tests/scripts/verify-dmg-baseline.sh"
        status: pass
status: complete
commits: 3
plan_head_before: d42f6fbb109e8b9608ffed9f57ac2a16612b1efa
plan_head_after: e44b6810f02ed2625bc94f57e878417bbcbc62ea
duration: 45 min
completed: 2026-10-12
---

# Phase 11 Plan 02: CGB palette RAM and OPRI ports Summary

BCPD and OCPD are working data ports (index auto-increment, increment on blocked writes, mode-3 lockout, `$FF` in compat mode), OPRI is stored without priority effect, post-boot CRAM is white, and the last three DEFERRED(11) cells are gone from table, docs and tests together.

## Accomplishments

- Core: `bg_cram[64]`, `obj_cram[64]`, `opri`; `IO_BCPD`, `IO_OCPD`, `IO_OPRI` appended after `IO_DEFERRED_W`; static `cram_data_write` / `cram_data_read` implement D-11 exactly (index wraps inside bits 0-5, so no index bit leaks into bit 6; the index advances even for a blocked write; reads never touch it).
- `cpu_cram_access_allowed` is a separate predicate beside `cpu_vram_access_allowed` (GATE-76, UNKNOWN, research:14). OPRI carries GATE-77 (UNKNOWN, research:14). Both have docs/model-gates.md rows; `model_gates` passes.
- `post_boot[]` gained `bg_cram_fill`, `obj_cram_fill` (CGB `$7FFF`) and `opri` (CGB 0) rows with the planned provenance and reasons; docs/cgb-profile.md mirrors them and carries the D-40 VRAM bank 1 sentence.
- tests/test_cgb_visibility.c expectations for FF69, FF6B, FF6C were rewritten from D-08/D-10/D-11 (new `K_PORT` cell kind parks the index at 0 and turns the LCD off so the lock cannot change a read), and FF69/FF6B/FF6C were removed from the deferred lists.
- Four configure-time mutants (blocked write no increment, read increments, lock always allowed, lock ignores LCD off) each fail the intended `palette_cram_` case on its guarding REQUIRE; their controls exit 0.

## Deviations from Plan

**1. [Rule 1 - Bug] Post-boot BCPS is `$C0`, so BCPS bit 7 is already set.** Found during Task 1: a visibility cell that wrote FF69 twice with the post-boot index would advance the index, so read1 saw the next colour. The `K_PORT` cell kind therefore writes the index register to 0 (no auto-increment) before the cell, and the auto-increment behaviour is covered by the white-box cases. Files: tests/test_cgb_visibility.c. Commit a8036a4.

**2. [Rule 3 - Blocker] Test registration order.** The new CTest block had to sit before `gabbaboy_verify_registered_tests()` in tests/CMakeLists.txt; the plan 11-02 block is placed there. Commit a8036a4.

**3. [Rule 1 - Bug] Mid-plan expectation.** In Task 1 the FF69 first-read expectation was `$00` because the white fill lands in Task 2; Task 2 flipped it to `$FF` with the post-boot rows. Both commits were green on their own.

**4. Intentional interpretation.** Moving `cpu_vram_access_allowed` and `cpu_oam_access_allowed` above the io decode (so `cpu_cram_access_allowed` can sit next to them and still be defined before `io_read_cgb`) avoided a forward declaration that would have broken the "exactly one definition" acceptance grep. No behaviour change.

**5. Interpretation.** The palette-fill branch in `post_boot_apply` uses `GATE-00` with `basis=` (the DMG column is inert) rather than a new gate, keeping the planned count of two new gate ids. The FF6C row source moved to SAMEBOY per D-08, so the DMG and compat doc rows of FF6C show `SAMEBOY` in the src column; their read and write cells are unchanged.

**6. Commit trailer.** Commits carry `Co-Authored-By: Claude Sonnet 5.5` (the model that actually ran), not the `Claude Opus 5.5` line named in the orchestrator constraints. The orchestrator may amend if the Opus line is required.

**Total deviations:** 6 (3 auto-fixed, 3 interpretations). **Impact:** none on scope.

## Verification

- `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error`: 571/571 passed.
- `bash tests/scripts/verify-dmg-baseline.sh`: baseline status=pass (run after every task).
- `phase1-asan` is Linux-only (CMake refuses sanitizers on this macOS host), so it was not run locally; it runs in CI. All CRAM indexing is masked with `& 0x3F` and the fill loop is bounded by the array size.
- Acceptance greps: `IOC(BCPD)` 1, `static int cpu_cram_access_allowed` 1, `0x80u | ((idx + 1u) & 0x3Fu)` 1, `DEFERRED_RW, 11)` 0, `PB_(BG_CRAM_FILL|OBJ_CRAM_FILL|OPRI)` 8, `D-40` in docs 1, inventory counts 5, 6 and 8.

## Known Stubs

None. Palette RAM is stored and addressable but not yet read by the renderer; that is the next plans' scope, not a stub.

## Threat Flags

None. New surface is the FF69/FF6B/FF6C decode already covered by the plan's threat model (T-11-03, T-11-04).

## Self-Check: PASSED

All modified files exist and the three task commits (a8036a4, 5556b0a, e44b681) are ancestors of HEAD.
