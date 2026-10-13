---
status: complete
phase: GB-11-cgb-colour-rendering-and-player-colour
source: 11-01-SUMMARY.md, 11-02-SUMMARY.md, 11-03-SUMMARY.md, 11-04-SUMMARY.md, 11-05-SUMMARY.md, 11-06-SUMMARY.md, 11-07-SUMMARY.md, 11-08-SUMMARY.md, 11-09-SUMMARY.md, 11-10-SUMMARY.md, 11-11-SUMMARY.md, 11-12-SUMMARY.md, 11-13-SUMMARY.md, 11-14-SUMMARY.md, 11-15-SUMMARY.md
started: 2026-10-13T08:30:00Z
updated: 2026-10-13T12:56:37.039Z
---

## Current Test

[testing complete]

## Tests

All 91 SUMMARY coverage entries across 15 plans classify as auto-passed (`uat.classify-coverage`: mode coverage, zero present, zero errors), so per D-069 no human checkpoint is presented. Rows below group them by deliverable with the plan coverage ids they carry.

Evidence: local macOS arm64 Debug at b314686 CTest 689/689 and at 4811033 691/691 (adds `ci_asan_parallel_contract` and its negative control `ci_asan_parallel_serial_selftest`). Hosted CI at b314686: the push ci run 38360819833 passed all jobs, but the pull_request ci run 38360825378 was cancelled when linux-asan-ubsan reached its 30-minute timeout (504/684 passed, none failing, runner about 1.6x slower), and preview-package-smoke 38360825726 failed only waiting on that run. Fixed in eb6f36e (ASan ctest `--parallel 4`, pinned by `ci_asan_parallel_contract` with negative control `ci_asan_parallel_serial_selftest`) and 4811033 (sanitizer builds scale explicit test TIMEOUTs by three, after eb6f36e's parallel run pushed two acceptance cases past 300 s; ci runs 38396258662 and 38396266543 failed on exactly that). LESSONS GB-CI-004. Hosted CI at 4811033 is all green: ci push 38398631736 and pull_request 38398639883 (all jobs; linux-asan-ubsan 686/686 in 1019 s test time, jobs 16.4 and 17.7 min of 30), fixture-repro 38398631778 and 38398639816 (incl. cgb-colour byte-identical rebuild with pinned RGBDS 1.0.1), preview-package-smoke 38398639852. Local scripts at 4811033: `verify-dmg-baseline.sh` baseline status=pass, `rgb-digest-vector.py --rgb555`, `reproduce-magentests.sh --self-check` pass, `verify-phase3-player.sh --build-package` passed (player tests run there; `reproduce-cgb-colour.sh` refuses local RGBDS 1.0.4 by design and is covered by fixture-repro). Every named test cited by a SUMMARY coverage ref is registered in `tests/expected-tests.txt` or `tests/player/expected-tests.txt`.

### 1. DMG output is unchanged and gbb_copy_frame keeps its model contract (CGB-04)
expected: The DMG shade pin over three ROMs fails under a shade-flip mutant; gbb_copy_frame stays unsupported on the CGB profile and works on DMG; every plan leaves the DMG baseline byte-identical.
result: pass
source: automated
coverage_id: 11-01 D1 D2 D5; 11-02 C8; 11-03 C7; 11-04 C7; 11-06 C8; 11-07 C6; 11-08 C7; 11-09 C4; 11-14 C6
evidence: "bash tests/scripts/verify-dmg-baseline.sh (baseline status=pass); ctest -R '^(cgb_dmg_|cgb_copy_frame_)'"

### 2. Independent 6144-row priority truth table matches the real composers (CGB-04)
expected: The table regenerates byte-identically, rejects an altered row, covers every input once and agrees with the CGB-mode and compat-mode pixel functions on all rows and a 64-row whole-frame sample; each composer input, ordering and attribute rule has a mutant that fails it.
result: pass
source: automated
coverage_id: 11-01 D3 D4; 11-05 C1-C7
evidence: "ctest -R '^cgb_priority_' (GBB_CGB_PRIORITY_TRUTH_ROWS == 6144 asserted; mutants included)"

### 3. Palette RAM ports BCPS/BCPD, OCPS/OCPD and OPRI (CGB-04)
expected: Auto-increment and wrap, read without advance, mode-3 lockout that still advances the index, LCD-off unlock, compat-mode inertness, OPRI bit 0, white post-boot CRAM and zeroed VRAM bank 1; each rule has a failing mutant; DEFERRED(11) cells flip in table, decode, docs and visibility together.
result: pass
source: automated
coverage_id: 11-02 C1-C7
evidence: "ctest -R '^(palette_cram_|cgb_visibility_|cgb_tables_)'"

### 4. CGB-mode per-dot colour rendering with attributes and priority (CGB-04)
expected: BG, window and objects resolve per dot from live CRAM into the RGB store (bit 15 masked); attribute palette, bank and flips apply; LCDC.0 removes priority only; objects order by OAM index; shade and RGB stores stay separate; LCD off whitens the working frame and keeps the completed one; a mid-frame HBlank CRAM rewrite shows on all 144 rows.
result: pass
source: automated
coverage_id: 11-03 C1-C6 C8; 11-07 C1 C2; 11-08 C1 C2 C3 C5
evidence: "ctest -R '^cgb_colour_' (fixtures/cgb-colour, snapshot and composer mutants with passing controls)"

### 5. Compatibility palette for DMG software on the CGB profile (CGB-05)
expected: A fixed, original, documented ramp for BG, OBJ0 and OBJ1 with no boot-ROM or title-hash source; resolved per dot through BGP/OBP0/OBP1; CGB attributes, VBK and OPRI have no effect; set/get follow struct_size, reject bit 15 without partial mutation, survive reset and load, and never recolour a completed frame; docs equal the code table.
result: pass
source: automated
coverage_id: 11-04 C1-C6; 11-06 C4 C5 C6; 11-08 C4
evidence: "ctest -R '^(palette_compat_|cgb_tables_compat_palette)'"

### 6. Public gbb_copy_frame_rgb555 call and installed consumers (CGB-04, CGB-05)
expected: Invalid arguments are rejected before the profile check with nothing written; CGB and compat modes are served; LCD off freezes the generation; the host guide keeps the colour promises and the installed C and C++ consumers call every new symbol, each check proven able to fail.
result: pass
source: automated
coverage_id: 11-06 C1 C2 C3 C7
evidence: "ctest -R '^(cgb_copy_frame_rgb555|native_guide_cgb|installed_consumer)' (ordering mutant with passing control)"

### 7. Original colour fixtures and external colour oracles (CGB-04)
expected: Six committed RGBDS ROMs match their manifest digests and rebuild byte for byte with RGBDS 1.0.1; MagenTests ppu_disabled_state, oam_internal_priority and bg_oam_priority match their pinned predicates, each able to fail; AGE m3 variants are expected-unsupported (mode-3-pixel-timing, D-20) and a changed reason is rejected; the acid2 runner refuses an unpinned ROM.
result: pass
source: automated
coverage_id: 11-07 C3 C4 C5; 11-08 C6; 11-10 C1-C4; 11-11 C1-C4
evidence: "ctest -R '^(cgb_colour_fixture|magentests_cgb_|age_|acid2_)'; fixture-repro workflow"

### 8. Runner CGB frame digests (CGB-04)
expected: The runner captures CGB frames through gbb_copy_frame_rgb555 with an RGB555-labelled digest that agrees with an independent Python implementation; wrong model, a flipped reference and an over-budget run each fail or refuse; DMG digest format is unchanged.
result: pass
source: automated
coverage_id: 11-09 C1-C4
evidence: "ctest -R '^cgb_runner_'"

### 9. SDL3 player --model auto|dmg|cgb with colour presentation and CI smoke (CGB-09)
expected: The select_profile seam maps every model and $143 value correctly; RGB555 to RGBA32 equals the independent formula for all 32768 values; the title shows DMG, CGB or CGB (DMG-compat); the real player renders colour-attr.gb with a pinned RGBA digest; R/B-swap and forced-DMG-path players fail the smoke; the --model grammar and existing DMG behaviour hold.
result: pass
source: automated
coverage_id: 11-12 C1-C8
evidence: "bash tests/scripts/verify-phase3-player.sh --build-package (player CTests incl. player_cgb_smoke, rb_swap and dmg_path mutants; macos-player-package job in ci)"

### 10. Player limitations text, research gates, robustness and benchmark (CGB-04, CGB-09)
expected: The pinned limitations text matches limitations.h, README and the macOS string, and a README missing a phrase is rejected; every research:11 gate is resolved or reassigned; RGB555 pixels never exceed 0x7FFF under fuzzed traffic and a mask-removed core is caught; measure_core runs the CGB workload with the DMG tracer digest unchanged.
result: pass
source: automated
coverage_id: 11-13 C1-C4; 11-14 C1-C5
evidence: "ctest -R '^(player_limitations_|model_gates|fuzz_core_|bench_)'; 11-BENCH.md"

### 11. Durable records and handoff (all)
expected: DECISIONS D-076 to D-083 name evidence and revisit triggers; INDEX links resolve; memory files are privacy-clean; COVERAGE.md passes the api-coverage gate; the full suite passes at the plan head.
result: pass
source: automated
coverage_id: 11-15 C1-C5
evidence: "ctest -R '^(summary_coverage|decisions_|research_index_)'; api-coverage.verify-pre pass"

## Summary

total: 11
passed: 11
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps

[none]
