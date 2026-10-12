---
phase: 10-cgb-profile-banking-and-register-visibility
plan: 04
subsystem: core
tags: [post-boot, provenance-table, dmg-pin, model-gates, cgb]
requires: ["10-03"]
provides:
  - "tests/test_cgb_postboot.c: public-API DMG post-boot pin (CPU snapshot + guest-read I/O bytes) with --flip control"
  - "const post_boot[] provenance table (DMG column) and post_boot_apply() consumed by reset_state"
affects: [10-06]
tech-stack:
  added: []
  patterns: ["pin test committed before the refactor it protects", "const provenance table walked by a switch with no default"]
key-files:
  created:
    - tests/test_cgb_postboot.c
  modified:
    - src/core/gabbaboy.c
    - docs/model-gates.md
    - tests/CMakeLists.txt
    - tests/expected-tests.txt
key-decisions:
  - "DMG column records the implemented value: IF, STAT, NR50, NR51, NR52(power), OBP0, OBP1, PPU mode and P1 select are POLICY with a diverges-from-pandocs reason; none was corrected toward Pan Docs"
  - "F cell is HEADER_DERIVED: the cell holds the $80 base and the consumer ORs $30 when header byte $14D is non-zero"
  - "Gate tags G03-G11 moved with their literals into post_boot_apply; the doc Site column was updated"
requirements-completed: [CGB-01]
duration: 40 min
completed: 2026-10-12
status: complete
commits: 2
plan_head_before: 9b041041f2219bf9de95d9f87bff66b7ecef3fb3
plan_head_after: bae094a6ea33231fa960589b75f00ca1b0c4ccc0
actuals:
  tokens: 14000
  tasks: 2
  commits: 2
coverage:
  - deliverable: "DMG post-boot state (10 CPU fields, 43 I/O reads, both F branches) pinned through the public API against typed literals, with negative controls"
    human_judgment: false
    verification:
      - kind: ctest
        ref: "cgb_postboot_dmg_pin, cgb_postboot_dmg_pin_checksum_zero, cgb_postboot_dmg_pin_flipped, cgb_postboot_dmg_pin_flipped_io"
        status: pass
  - deliverable: "reset_state takes DMG post-boot values from post_boot[] with provenance; DMG output byte-identical"
    human_judgment: false
    verification:
      - kind: command
        ref: "bash tests/scripts/verify-dmg-baseline.sh (baseline status=pass)"
        status: pass
      - kind: ctest
        ref: "full phase1 suite 430/430 including model_gates*"
        status: pass
---

# Phase 10 Plan 04: DMG Post-Boot Pin and Provenance Table Summary

A public-API pin test fixes the DMG post-boot state, then the literals move into a `const post_boot[]` table with per-field provenance consumed by `reset_state`, with the DMG baseline unchanged.

## Accomplishments

- `tests/test_cgb_postboot.c` snapshots A, F, B, C, D, E, H, L, SP, PC with `gbb_test_cpu_snapshot`, then runs a guest that LDH-loads 43 I/O registers into HRAM and compares each to a literal typed in the test. Time-sensitive registers (STAT, LY, DIV, IF) are read first, so STAT $86, LY 0, DIV $AB are exact. Both F branches ($B0 non-zero checksum, $80 zero) are pinned.
- `--flip N` XORs expected entry N; failure exits 1 with `post-boot mismatch: <field>`. Controls registered for F (CPU) and NR12 (I/O). Sampled flips over CPU and I/O indexes all exited 1 naming the right field.
- `post_boot[]` (provenance enum, source-id list matching the future docs/cgb-profile.md list, field enum, `{value, prov, src_id, reason}` cell, row) with a `_Static_assert` on row count. `post_boot_apply` walks it through a switch with no default; `reset_state` keeps its non-table clears in the original relative order.
- Gate rows G03-G11 now point at `post_boot_apply`; the model-gate scanner stays green.

## Task Commits

1. Task 1 (tracer): `40a9133` test(10-04) DMG pin, committed against unchanged `src/core/gabbaboy.c`.
2. Task 2: `bae094a` refactor(10-04) provenance table and consumer (single bisectable commit).

## Verification

- Targeted ctest (cgb_postboot_dmg_, model_gates, bus_, dma_, cpu_, ppu_, acceptance_, mooneye_): 139/139 pass; full phase1 suite after the final edit: 430/430.
- `bash tests/scripts/verify-dmg-baseline.sh`: `baseline status=pass`; `git diff --quiet main -- tests/baseline` exits 0.
- Acceptance: `PROV_HEADER_DERIVED` count 2, `diverges-from-pandocs` count 10, two separate commits, `src/core/gabbaboy.c` identical to HEAD at the Task 1 commit.

## Deviations from Plan

**1. [Rule 3 - Blocker] Guest placement**
- The 90-byte guest overlaps the header at 0x134, so the test ROM jumps from 0x100 to 0x150. Test-only; no effect on pinned values.

**2. Register read order**
- DIV, STAT, LY, IF are read first so their pinned values stay near power-on rather than reflecting 700 dots of guest time. IE reads $E0 (existing GATE-21 mask), pinned as implemented.

**3. Amend**
- `diverges-from-pandocs` was initially produced by macro concatenation (count 2); the literal was spelled out per row to satisfy the count-4 criterion and the refactor commit was amended before any further commit.

**Total deviations:** 1 Rule 3, 2 notes. **Impact:** none on behaviour.

## Known Stubs

None. CGB and compat columns are intentionally absent until Plan 10-06.

## Self-Check: PASSED

- tests/test_cgb_postboot.c: FOUND
- Commits 40a9133 and bae094a: in HEAD history (bae094a replaced the pre-amend refactor hash)
