---
phase: 11-cgb-colour-rendering-and-player-colour
plan: 14
subsystem: engineering-closeout
tags: [model-gates, fuzz, palette, benchmark, d-04, d-25, d-32, d-33, d-34, cgb]
status: complete
requires:
  - phase: 11-cgb-colour-rendering-and-player-colour
    provides: "11-11 external dispositions and 11-13 player claims"
provides:
  - "no research:11 owner tag remains: ten PPU timing gates are research:14 with a Phase 11 dispositions table, and model_gates_no_phase11_rows guards it"
  - "palette RAM and compat-palette fuzzing with bit-15, rejected-set and DMG-store invariants, plus a mask-removed core mutant that trips the invariant"
  - "measure_core --profile cgb, 11-BENCH.md and 11-BENCH.json with the D-22 evaluation and the D-04 decision"
affects: [11-15]
requirements-completed: []
plan_head_before: 6ca9f1f3a0e0c96d1492b98becf77d42776843e7
plan_head_after: 2c4ac09cd84f0f4613eb9f54118a445937db554a
actuals:
  tokens: 14000
  tasks: 3
  commits: 4
coverage:
  - id: C1
    description: "Every research:11 gate is resolved or re-assigned to Phase 14 with a reason, docs and code tags agree, and a reverted row is rejected with phase-11-row-open"
    requirement: CGB-04
    human_judgment: false
    verification:
      - kind: unit
        ref: "model_gates"
        status: pass
      - kind: unit
        ref: "model_gates_no_phase11_rows"
        status: pass
      - kind: unit
        ref: "model_gates_no_phase11_rows_mutated_doc"
        status: pass
  - id: C2
    description: "Palette RAM traffic, LCD toggles, run slices and compat-palette sets (struct_size around 28, bit 15, NULL) keep every RGB555 pixel at or below 0x7FFF, leave the palette unchanged on a rejected set and keep the DMG profile's RGB store empty"
    requirement: CGB-05
    human_judgment: false
    verification:
      - kind: unit
        ref: "cgb_fuzz_palette_regressions"
        status: pass
      - kind: unit
        ref: "fuzz_core_regressions"
        status: pass
  - id: C3
    description: "A core with the 0x7FFF resolve mask removed breaks the bit-15 invariant on a guest CRAM word of 0xFFFF, and the same binary stays quiet on seeds without such a word"
    requirement: CGB-05
    human_judgment: false
    verification:
      - kind: unit
        ref: "cgb_fuzz_palette_mutant_no_mask"
        status: pass
      - kind: unit
        ref: "cgb_fuzz_palette_mutant_no_mask_control"
        status: pass
  - id: C4
    description: "measure_core creates the CGB profile for the colour workload, rejects an unknown profile name, and leaves the DMG output and tracer digest unchanged"
    requirement: CGB-04
    human_judgment: false
    verification:
      - kind: unit
        ref: "cgb_measure_core_cgb_profile"
        status: pass
      - kind: unit
        ref: "cgb_measure_core_unknown_profile"
        status: pass
      - kind: integration
        ref: "banking_tracer_digest_unchanged"
        status: pass
  - id: C5
    description: "The advisory interleaved A/B of the DMG profile against the Phase 10 head keeps the tracer digest 4c7a57ff3d50d228 on both builds, the D-22 trigger does not fire, and the harness receipt shape is enforced"
    requirement: CGB-04
    human_judgment: false
    verification:
      - kind: integration
        ref: "cgb_bench_ab_selftest"
        status: pass
      - kind: integration
        ref: "cgb_bench_ab_wrong_digest"
        status: pass
  - id: C6
    description: "DMG byte-identity holds at the plan head and the packaged player smoke, including its pinned CGB colour digest, passes against the final core"
    requirement: CGB-04
    human_judgment: false
    verification:
      - kind: integration
        ref: "bash tests/scripts/verify-dmg-baseline.sh"
        status: pass
      - kind: unit
        ref: "cgb_dmg_identity_shade_pin"
        status: pass
      - kind: unit
        ref: "banking_dmg_flat_reference"
        status: pass
      - kind: integration
        ref: "bash tests/scripts/verify-phase3-player.sh --build-package"
        status: pass
---

# Phase 11 Plan 14: Engineering close-out Summary

Ten PPU timing gates are re-assigned to Phase 14 with reasons and a scan that stops any research:11 row from returning, palette RAM and the compat palette API are fuzzed with a bit-15 invariant that a mask-removed core visibly breaks, and the advisory A/B shows no DMG cost (median 98.5 to 100.2 percent of the Phase 10 head), so the per-dot branch stays.

## Accomplishments
- Task 1 (tracer): GATE-02, 10, 13, 14, 20, 44, 47, 48, 49 and 50 re-tagged `research:14` in `src/core/gabbaboy.c` and `docs/model-gates.md` together, notes reworded to name the deferred CGB timing or lock-edge question (D-09/D-12). A "Phase 11 dispositions" table lists all fourteen Phase 11 rows (ten re-assigned, GATE-28 split, GATE-43/45/46 resolved BOTH). The Release status paragraph no longer says Phase 11 owns open rows. `docs/cgb-profile.md` gains a "Colour path scope" paragraph (D-09, D-36, FF55 DEFERRED(13), D-20 AGE). `tests/check_no_phase11_rows.cmake` backs `model_gates_no_phase11_rows`; `model_gates_no_phase11_rows_mutated_doc` reverts one row in a configure-time copy and must exit 1 with `phase-11-row-open`.
- Task 2: `tests/fuzz_core.c` palette path (`data[0] = 0xA0 | ...` on the CGB profile): up to 512 operations of FF68-FF6C guest writes and reads (auto-increment wrap), LCDC toggles (writes with the LCD off and on), run slices of at most 400000 half-dots, and `gbb_set_compat_palette` / `gbb_get_compat_palette` calls with `struct_size` in {0, 27, 28, 29, 64}, bit 15 entries and NULL; CGB mode and compat mode both reachable through `$143`. Invariants: every `gbb_copy_frame_rgb555` pixel at most 0x7FFF, a rejected set leaves the palette unchanged and an accepted one stores exactly what was given, and the DMG profile refuses the colour copy and writes nothing. In the standalone build a violated contract is counted and reported (the libFuzzer build still aborts), which lets `cgb_fuzz_palette_mutant_no_mask` assert a numeric exit 1 with `pixel above 0x7FFF`; its control runs the same executable on seeds without a 0xFFFF word and exits 0.
- Task 3: `measure_core --no-trace --profile cgb <rom>` (DMG form and digest unchanged, the CGB form appends `profile=cgb-cpu-e`), `cgb_measure_core_cgb_profile` and an unknown-profile usage control. `11-BENCH.md`/`11-BENCH.json`: three interleaved A/B runs of the DMG tracer workload (digest 4c7a57ff3d50d228 on every warm-up and sample of both builds, base Phase 10 head 3012e8f built from a temporary worktree outside the repository and removed afterwards), plus a head-only CGB colour record for `colour-attr.gb` with digest 3c5797f6525df9c7.
- D-22 evaluation: medians 99.22, 98.49 and 100.23 percent with 95 percent margins 1.5 to 1.9; the trigger did not fire in any run. D-04 decision: no hoist, so no core change was made for performance and no second receipt is owed.
- Verification at the plan head: full `phase1` suite 684 of 684 passed; `verify-dmg-baseline.sh` printed `baseline status=pass`; `banking_tracer_digest_unchanged`, `banking_dmg_flat_reference` and `cgb_dmg_identity_shade_pin` pass; `verify-phase3-player.sh --build-package` passed with the unchanged `player_cgb_smoke` pin (package SHA-256 3eeb250a...); local ASan/UBSan (clang `-fsanitize=address,undefined`) run of the fuzz regressions and 400 random palette-path inputs was clean. The `phase1-asan` preset is Linux-only (it refuses to configure on macOS), so that leg runs in CI on the pushed branch.

## Deviations from Plan
- [Rule 3 - Blocking] The Phase 10 head cannot run the CGB colour workload (it stops after 131544 half-dots on the first colour register, unsupported-bus), so the CGB colour workload is recorded head-only with its own digest rather than as an A/B, as the plan's "separately recorded" wording allows. `measure_core` keeps printing the legacy workload label for every ROM; 11-BENCH.md names the real fixture.
- [Rule 2 - Missing critical] The standalone fuzz harness used `abort()`, which `expect_exit.cmake` cannot match to a numeric code. It now counts violated contracts in the standalone build only; `test_fuzz_core`'s `main` returns 1 when any were counted, which also makes the pre-existing seeds fail loudly instead of via a signal.
- Added `cgb_measure_core_cgb_profile`, `cgb_measure_core_unknown_profile` and `cgb_fuzz_palette_mutant_no_mask_control` beyond the four names the plan listed; all are inventoried in `tests/expected-tests.txt`.
- The `phase1-asan` preset could not be run locally (Linux-only); equivalent local sanitizer evidence is stated above and CI runs the preset.
- D-20 statement for VERIFICATION: AGE has no CGB colour, attribute or priority ROM at its pinned commit, so it supplies no Phase 11 colour evidence; its mode-3 pixel-timing cases are `expected-unsupported` and owned by Phase 14 (docs/cgb-profile.md, `cgb_external_dispositions`).

**Total deviations:** 4 (1 blocking, 1 missing-critical, 2 informational). **Impact:** none on scope; no core behaviour changed (only gate tag comments).

## Known Stubs
None.

## Threat Flags
None. No new endpoints, auth paths or trust boundaries; the fuzz path only widens untrusted-input coverage (T-11-31), receipts carry a hardware class only (T-11-32) and the gate scan closes stale ownership (T-11-33).

## Self-Check: PASSED
- Files exist: docs/model-gates.md, tests/check_no_phase11_rows.cmake, tests/fuzz_core.c, 11-BENCH.md, 11-BENCH.json.
- Commits 8658dc2, ad0827d, 271faa1 and 2c4ac09 are on the branch.
