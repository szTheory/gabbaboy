---
phase: 11-cgb-colour-rendering-and-player-colour
plan: 06
subsystem: cgb-colour-public-abi
tags: [rgb555, compat-palette, public-api, d-15, d-16, d-17a, d-18, d-19, d-32, d-42, gate-83]
requires:
  - phase: 11-cgb-colour-rendering-and-player-colour
    provides: "11-03 RGB stores, 11-04 compat palette storage and renderer, 11-05 priority truth table"
provides:
  - "gbb_copy_frame_rgb555: validated RGB555 frame copy, CGB profile only (GATE-83)"
  - "gbb_compat_palette, GBB_COMPAT_PALETTE_SIZE_V1, gbb_set_compat_palette, gbb_get_compat_palette"
  - "docs/cgb-profile.md compat palette block pinned against code and the ramp rule"
  - "host guide colour section, support ledger entry and installed C and C++ consumer coverage"
affects: [11-07]
requirements-completed: []
actuals:
  tokens: 60000
  tasks: 3
  commits: 3
coverage:
  - id: C1
    description: "gbb_copy_frame_rgb555 rejects every invalid argument before the profile check, writes nothing on any error and serves both CGB mode and compat mode"
    human_judgment: false
    verification:
      - kind: unit
        ref: "cgb_rgb555_args"
        status: pass
      - kind: unit
        ref: "cgb_rgb555_dmg_profile"
        status: pass
      - kind: unit
        ref: "cgb_rgb555_not_ready"
        status: pass
      - kind: unit
        ref: "cgb_rgb555_both_modes"
        status: pass
  - id: C2
    description: "While the LCD is off the last completed frame stays readable and the generation does not advance"
    human_judgment: false
    verification:
      - kind: unit
        ref: "cgb_rgb555_lcd_off"
        status: pass
  - id: C3
    description: "Moving the profile check ahead of the argument checks is detected, with a passing control on the same mutated core"
    human_judgment: false
    verification:
      - kind: unit
        ref: "cgb_rgb555_mutant_skewed_validator"
        status: pass
      - kind: unit
        ref: "cgb_rgb555_mutant_skewed_validator_control"
        status: pass
  - id: C4
    description: "The compat palette set and get follow the struct_size handshake, reject bit 15 without partial mutation, survive reset and load, and a set never recolours a completed frame"
    human_judgment: false
    verification:
      - kind: unit
        ref: "palette_compat_api_default"
        status: pass
      - kind: unit
        ref: "palette_compat_api_roundtrip"
        status: pass
      - kind: unit
        ref: "palette_compat_api_reject"
        status: pass
      - kind: unit
        ref: "palette_compat_api_get_reject"
        status: pass
      - kind: unit
        ref: "palette_compat_api_larger"
        status: pass
      - kind: unit
        ref: "palette_compat_api_survives"
        status: pass
      - kind: unit
        ref: "palette_compat_effect_next_frame"
        status: pass
  - id: C5
    description: "Masking bit 15 instead of rejecting it is detected, with a passing control"
    human_judgment: false
    verification:
      - kind: unit
        ref: "palette_compat_mutant_mask_bit15"
        status: pass
      - kind: unit
        ref: "palette_compat_mutant_mask_bit15_control"
        status: pass
  - id: C6
    description: "The documented default palette equals the code table and the recomputed rule, and an altered doc copy is rejected"
    human_judgment: false
    verification:
      - kind: unit
        ref: "cgb_tables_compat_palette"
        status: pass
      - kind: unit
        ref: "cgb_tables_compat_palette_mutated_doc"
        status: pass
  - id: C7
    description: "The host guide keeps the new colour promises and the installed C and C++ consumers call every new symbol, each check proven able to fail"
    human_judgment: false
    verification:
      - kind: integration
        ref: "cgb_native_guide_contract"
        status: pass
      - kind: integration
        ref: "cgb_native_guide_contract_missing_selftest"
        status: pass
      - kind: integration
        ref: "installed_consumer_c"
        status: pass
      - kind: integration
        ref: "installed_consumer_cpp"
        status: pass
      - kind: integration
        ref: "cgb_consumer_symbol_coverage"
        status: pass
      - kind: integration
        ref: "cgb_consumer_symbol_coverage_selftest"
        status: pass
  - id: C8
    description: "Every new function and branch carries a MODEL tag with a docs row and DMG output stays byte-identical"
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
plan_head_before: 6c3197618ef2c101eca4096f08760c147b1b6dd3
plan_head_after: 12511ff3c3c437f5df441246bd6d78197e205e05
duration: 55 min
completed: 2026-10-12
---

# Phase 11 Plan 06: Public colour ABI Summary

`gbb_copy_frame_rgb555` and the host-overridable `gbb_compat_palette` (set/get, bit 15 rejected not masked, struct_size handshake) are public, validated before any write, documented, and called by both installed consumers.

## Accomplishments

- `gbb_copy_frame_rgb555(instance, uint16_t *pixels, capacity_bytes, pitch_bytes, out_info)` duplicates the `gbb_copy_frame` validation (no refactor of the DMG call) with byte units, 2-byte alignment, even pitch, minimum pitch 320 and the `(SIZE_MAX - 320) / 143` overflow bound, then the CGB_ONLY profile gate (new GATE-83, docs row added), then not-ready, then a per-row memcpy from the completed RGB store. `gbb_frame_info` is unchanged and shared.
- Stale "no colour output yet" comments in the header (profile enum, instance block, `gbb_copy_frame`) now point to the RGB555 call; `gbb_copy_frame` behaviour and GATE-57 are untouched.
- `gbb_set_compat_palette` validates the whole struct before the first store; `gbb_get_compat_palette` writes nothing on any error and stores field by field, setting struct_size to 28. `_Static_assert` pins the layout beside the `gbb_info` assert.
- `docs/cgb-profile.md` holds the rule and the 12 default values between the `cgb-compat-palette` markers with the G4 provenance statement; `test_cgb_tables compat_palette` compares the block with `compat_default_rgb555` and with the rule recomputed in the test.
- `docs/native-integration.md` gains a colour and compat palette section plus three new contract phrases; `docs/support/unreleased.md` gains a "CGB colour (Phase 11)" entry and the Phase 10 "no colour output" statements are updated.
- Both installed consumers call every new symbol; `cgb_consumer_symbol_coverage` pins that with a selftest that drops one symbol.

## Deviations from Plan

**1. [Rule 3 - Blocking] Extra file `tests/cgb_consumer_symbol_coverage.cmake`.** A `add_test` allows one COMMAND and a `-P` check needs a script file, so the symbol-coverage check lives in a small script instead of inline in `tests/CMakeLists.txt`. It takes comma-separated lists so the values survive nesting in the selftest's command list.

**2. [Interpretation] Skewed-validator mutant anchor.** The anchor is the `row_bytes` declaration at the top of the function (exactly once), with a replacement that inserts the profile test before the NULL checks, rather than the profile gate statement itself. Same effect, simpler exactly-once guarantee.

**3. [Rule 1 - Bug in own test] Effect test guest.** A zero-filled ROM slides through the address space and rewrites BGP after a few frames, so `palette_compat_effect_next_frame` uses a `jp $0150; jr -2` spin guest to keep the blank post-boot screen. After a set it runs two frames (the in-progress frame at the set moment legitimately mixes old and new pixels).

**4. [Interpretation] Contract phrases need a bullet in the scope paragraph.** The doc contract scope is the paragraph after "The CGB-CPU-E profile is selected with", so a one-bullet colour summary carries the three new phrases; the full section follows.

**5. [Environment] Installed-package refresh.** `build/package-prefix` is a stale pre-existing install the consumer tests read; `cmake --install build --prefix build/package-prefix` refreshes it. CI and any clean checkout do this as part of its own flow.

**Total deviations:** 5, none affecting scope or locked decisions.

## Verification

- `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error`: 645/645 passed.
- `bash tests/scripts/verify-dmg-baseline.sh`: baseline status=pass (run after the core edits).
- `python3 -I tests/scripts/verify-support-ledger.py --self-test`: passed.
- `phase1-asan` is Linux-only (CMake refuses sanitizers on this macOS host); it runs in CI on the pushed branch.

## Known Stubs

None.

## Threat Flags

None. T-11-11 to T-11-14 mitigations are implemented as planned and exercised by `cgb_rgb555_args`, `palette_compat_api_reject`, `palette_compat_api_get_reject` and `palette_compat_api_larger`.

## Self-Check: PASSED

Commits de107a1, c1d54cc and 12511ff are ancestors of HEAD; header, core and test files exist.
