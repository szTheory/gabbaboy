---
status: complete
phase: GB-11-cgb-colour-rendering-and-player-colour
source: 11-01-SUMMARY.md, 11-02-SUMMARY.md, 11-03-SUMMARY.md, 11-04-SUMMARY.md, 11-05-SUMMARY.md, 11-06-SUMMARY.md, 11-07-SUMMARY.md, 11-08-SUMMARY.md, 11-09-SUMMARY.md, 11-10-SUMMARY.md, 11-11-SUMMARY.md, 11-12-SUMMARY.md, 11-13-SUMMARY.md, 11-14-SUMMARY.md, 11-15-SUMMARY.md
started: 2026-10-20T22:28:12.432043+00:00
updated: 2026-10-20T22:28:12.432043+00:00
---

## Automated Evidence

## Current verification refresh (2026-10-20)

All 15 plans were already complete. This canonical closure migration replaces 11 grouped rows with one row for each of the 91 unchanged SUMMARY coverage entries. It does not replay the original implementation or turn historical hosted receipts into current-head results.

Current source snapshot: e444dd2320acf0e4e0d83fb89009311edcaa5e13. The configured regression command `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error` passed 1,144/1,144 in 486.68 seconds, zero skips. Rebuilt SDL player suite `ctest --test-dir build-player -R '^player_' --output-on-failure --no-tests=error` passed 98/98 in 21.72 seconds, zero skips. This includes current positive and mutation controls; focused bounded review controls passed another 36/36 as recorded in 11-REFRESH-GATES.md. Local transient logs: /tmp/gabbaboy-phase11-regression.log and /tmp/gabbaboy-phase11-player-all.log.

Historical boundary checks use commit 4811033: STATE and continuation named the execution handoff to /gsd-verify-work 11 and Phase 12: CGB Double Speed; both auto flags were false and no Phase 12 tree existed there. Later live routes and trees are intentionally not asserted as historical facts. No new hosted exact-head, hardware, perceptual, fixture rebuild with the pinned RGBDS tool, or performance qualification is claimed. Benchmark and hosted evidence below remains bound to its original revision. CGB-04, CGB-05 and CGB-09 remain the requirement scope; D-20 AGE exclusion is unchanged.

## Preserved original automated evidence

All 91 SUMMARY coverage entries across 15 plans classify as auto-passed (`uat.classify-coverage`: mode coverage, zero present, zero errors), so per D-069 no human checkpoint is presented. Rows below group them by deliverable with the plan coverage ids they carry.

Evidence: local macOS arm64 Debug at b314686 CTest 689/689 and at 4811033 691/691 (adds `ci_asan_parallel_contract` and its negative control `ci_asan_parallel_serial_selftest`). Hosted CI at b314686: the push ci run 38360819833 passed all jobs, but the pull_request ci run 38360825378 was cancelled when linux-asan-ubsan reached its 30-minute timeout (504/684 passed, none failing, runner about 1.6x slower), and preview-package-smoke 38360825726 failed only waiting on that run. Fixed in eb6f36e (ASan ctest `--parallel 4`, pinned by `ci_asan_parallel_contract` with negative control `ci_asan_parallel_serial_selftest`) and 4811033 (sanitizer builds scale explicit test TIMEOUTs by three, after eb6f36e's parallel run pushed two acceptance cases past 300 s; ci runs 38396258662 and 38396266543 failed on exactly that). LESSONS GB-CI-004. Hosted CI at 4811033 is all green: ci push 38398631736 and pull_request 38398639883 (all jobs; linux-asan-ubsan 686/686 in 1019 s test time, jobs 16.4 and 17.7 min of 30), fixture-repro 38398631778 and 38398639816 (incl. cgb-colour byte-identical rebuild with pinned RGBDS 1.0.1), preview-package-smoke 38398639852. Local scripts at 4811033: `verify-dmg-baseline.sh` baseline status=pass, `rgb-digest-vector.py --rgb555`, `reproduce-magentests.sh --self-check` pass, `verify-phase3-player.sh --build-package` passed (player tests run there; `reproduce-cgb-colour.sh` refuses local RGBDS 1.0.4 by design and is covered by fixture-repro). Every named test cited by a SUMMARY coverage ref is registered in `tests/expected-tests.txt` or `tests/player/expected-tests.txt`.

## Current Test

[testing complete]

## Tests

### 1. DMG shade-identity pin over three ROMs is proven able to fail by a shade-flip core mutant while its control case passes
expected: "DMG shade-identity pin over three ROMs is proven able to fail by a shade-flip core mutant while its control case passes"
result: pass
source: automated
summary_file: 11-01-SUMMARY.md
coverage_id: D1
evidence: ["cgb_dmg_identity_shade_pin", "cgb_dmg_identity_mutant_shade_flip", "cgb_dmg_identity_mutant_shade_flip_control"]

### 2. gbb_copy_frame stays unsupported on the CGB profile in CGB and compat mode and works on DMG
expected: "gbb_copy_frame stays unsupported on the CGB profile in CGB and compat mode and works on DMG"
result: pass
source: automated
summary_file: 11-01-SUMMARY.md
coverage_id: D2
evidence: ["cgb_colour_copy_frame_unsupported"]

### 3. Independent 6144-row priority truth table is regenerable, byte-compared, sensitivity-checked and fails on an altered row
expected: "Independent 6144-row priority truth table is regenerable, byte-compared, sensitivity-checked and fails on an altered row"
result: pass
source: automated
summary_file: 11-01-SUMMARY.md
coverage_id: D3
evidence: ["cgb_priority_truth_regen", "cgb_priority_truth_selftest", "cgb_priority_truth_regen_mutated"]

### 4. Table shape, uniqueness of every input combination and eight hand-written golden rows agree with the oracle
expected: "Table shape, uniqueness of every input combination and eight hand-written golden rows agree with the oracle"
result: pass
source: automated
summary_file: 11-01-SUMMARY.md
coverage_id: D4
evidence: ["cgb_priority_table_shape"]

### 5. No production core change and the DMG baseline is intact
expected: "No production core change and the DMG baseline is intact"
result: pass
source: automated
summary_file: 11-01-SUMMARY.md
coverage_id: D5
evidence: ["bash tests/scripts/verify-dmg-baseline.sh"]

### 6. BCPD auto-increments across all 64 bytes, wraps 63 to 0 keeping bit 7 and bit 6, reads never advance, and all 8 bits of every byte are stored
expected: "BCPD auto-increments across all 64 bytes, wraps 63 to 0 keeping bit 7 and bit 6, reads never advance, and all 8 bits of every byte are stored"
result: pass
source: automated
summary_file: 11-02-SUMMARY.md
coverage_id: C1
evidence: ["palette_cram_bg_autoinc", "palette_cram_bg_readback"]

### 7. A mode-3 blocked write keeps the byte but still advances the index, a blocked read returns FF without advancing, and LCD off lifts the lock
expected: "A mode-3 blocked write keeps the byte but still advances the index, a blocked read returns FF without advancing, and LCD off lifts the lock"
result: pass
source: automated
summary_file: 11-02-SUMMARY.md
coverage_id: C2
evidence: ["palette_cram_bg_blocked_write", "palette_cram_bg_blocked_read", "palette_cram_lockout_lcd_off"]

### 8. OCPD mirrors BCPD independently of the background side, and compat mode reads FF and ignores writes with no increment
expected: "OCPD mirrors BCPD independently of the background side, and compat mode reads FF and ignores writes with no increment"
result: pass
source: automated
summary_file: 11-02-SUMMARY.md
coverage_id: C3
evidence: ["palette_cram_obj_autoinc", "palette_cram_compat_ports"]

### 9. OPRI stores bit 0, reads FE or the bit in CGB mode, changes no other instance state and is inert in compat mode
expected: "OPRI stores bit 0, reads FE or the bit in CGB mode, changes no other instance state and is inert in compat mode"
result: pass
source: automated
summary_file: 11-02-SUMMARY.md
coverage_id: C4
evidence: ["palette_opri_cgb", "palette_opri_compat"]

### 10. Post-boot CRAM is white in CGB and compat mode after load and reset, and VRAM bank 1 is zero after every load and reset
expected: "Post-boot CRAM is white in CGB and compat mode after load and reset, and VRAM bank 1 is zero after every load and reset"
result: pass
source: automated
summary_file: 11-02-SUMMARY.md
coverage_id: C5
evidence: ["cgb_postboot_cram_white", "cgb_postboot_vram1_zero", "cgb_tables_postboot"]

### 11. The three DEFERRED(11) cells flip together in table, decode, docs and independent visibility expectations
expected: "The three DEFERRED(11) cells flip together in table, decode, docs and independent visibility expectations"
result: pass
source: automated
summary_file: 11-02-SUMMARY.md
coverage_id: C6
evidence: ["cgb_tables_io", "cgb_visibility_matrix_cgb", "cgb_visibility_deferred_stop", "cgb_visibility_matrix_compat", "cgb_visibility_matrix_dmg"]

### 12. Each palette port rule has a mutant that makes its test fail while a control case still passes
expected: "Each palette port rule has a mutant that makes its test fail while a control case still passes"
result: pass
source: automated
summary_file: 11-02-SUMMARY.md
coverage_id: C7
evidence: ["palette_mutant_blocked_no_increment", "palette_mutant_read_increments", "palette_mutant_lock_always_allowed", "palette_mutant_lock_ignores_lcd_off", "palette_mutant_blocked_no_increment_control", "palette_mutant_read_increments_control", "palette_mutant_lock_always_allowed_control", "palette_mutant_lock_ignores_lcd_off_control"]

### 13. Every new function and model-differing branch carries a MODEL tag with a docs row, and the DMG baseline is byte-identical
expected: "Every new function and model-differing branch carries a MODEL tag with a docs row, and the DMG baseline is byte-identical"
result: pass
source: automated
summary_file: 11-02-SUMMARY.md
coverage_id: C8
evidence: ["model_gates", "bash tests/scripts/verify-dmg-baseline.sh"]

### 14. A CGB-mode BG pixel is resolved from live CRAM per dot into the RGB store, with bit 15 of the guest word masked
expected: "A CGB-mode BG pixel is resolved from live CRAM per dot into the RGB store, with bit 15 of the guest word masked"
result: pass
source: automated
summary_file: 11-03-SUMMARY.md
coverage_id: C1
evidence: ["cgb_rgb_store_bg_palette", "cgb_rgb_store_bit15_masked"]

### 15. The shade buffers stay zero on the CGB profile and the RGB buffers stay zero on the DMG profile
expected: "The shade buffers stay zero on the CGB profile and the RGB buffers stay zero on the DMG profile"
result: pass
source: automated
summary_file: 11-03-SUMMARY.md
coverage_id: C2
evidence: ["cgb_rgb_store_shade_untouched", "cgb_rgb_store_dmg_untouched"]

### 16. LCD off fills the RGB working frame with white and keeps the completed frame, and reset zero-fills both RGB buffers
expected: "LCD off fills the RGB working frame with white and keeps the completed frame, and reset zero-fills both RGB buffers"
result: pass
source: automated
summary_file: 11-03-SUMMARY.md
coverage_id: C3
evidence: ["cgb_rgb_store_lcd_off", "cgb_rgb_store_reset"]

### 17. BG attribute bits select palette, tile bank, X flip and Y flip, bit 4 is ignored and rendering never reads VBK or OPRI
expected: "BG attribute bits select palette, tile bank, X flip and Y flip, bit 4 is ignored and rendering never reads VBK or OPRI"
result: pass
source: automated
summary_file: 11-03-SUMMARY.md
coverage_id: C4
evidence: ["cgb_attr_palette", "cgb_attr_bank", "cgb_attr_xflip", "cgb_attr_yflip", "cgb_attr_bit4_ignored", "cgb_attr_vbk_not_read"]

### 18. LCDC bit 0 only removes priority in CGB mode, BG and window are still drawn, and the window is gated by LCDC bit 5 alone with the same attribute fetch
expected: "LCDC bit 0 only removes priority in CGB mode, BG and window are still drawn, and the window is gated by LCDC bit 5 alone with the same attribute fetch"
result: pass
source: automated
summary_file: 11-03-SUMMARY.md
coverage_id: C5
evidence: ["cgb_attr_bg_priority", "cgb_attr_lcdc0_bg_drawn", "cgb_attr_window_same_fetch", "cgb_attr_window_lcdc0_clear"]

### 19. Objects take the tile bank from OAM bit 3 and palette from bits 0-2 and order by OAM index, with a transparent winner pixel letting the next object show
expected: "Objects take the tile bank from OAM bit 3 and palette from bits 0-2 and order by OAM index, with a transparent winner pixel letting the next object show"
result: pass
source: automated
summary_file: 11-03-SUMMARY.md
coverage_id: C6
evidence: ["cgb_attr_obj_bank_palette", "cgb_attr_obj_oam_order"]

### 20. A colour path that also writes the shade store is caught while a control case still passes, and the DMG shade output is unchanged
expected: "A colour path that also writes the shade store is caught while a control case still passes, and the DMG shade output is unchanged"
result: pass
source: automated
summary_file: 11-03-SUMMARY.md
coverage_id: C7
evidence: ["cgb_dmg_identity_mutant_colour_writes_shade", "cgb_dmg_identity_mutant_colour_writes_shade_control", "cgb_dmg_identity_shade_pin", "bash tests/scripts/verify-dmg-baseline.sh"]

### 21. Every new function and model-differing branch carries a MODEL tag with a docs row
expected: "Every new function and model-differing branch carries a MODEL tag with a docs row"
result: pass
source: automated
summary_file: 11-03-SUMMARY.md
coverage_id: C8
evidence: ["model_gates"]

### 22. The default compat palette is the documented ramp for BG, OBJ0 and OBJ1 and survives reset and ROM load, including a host change
expected: "The default compat palette is the documented ramp for BG, OBJ0 and OBJ1 and survives reset and ROM load, including a host change"
result: pass
source: automated
summary_file: 11-04-SUMMARY.md
coverage_id: C1
evidence: ["cgb_compat_internal_default"]

### 23. A compat BG pixel is resolved per dot through the compat palette and compat mode never writes the shade store
expected: "A compat BG pixel is resolved per dot through the compat palette and compat mode never writes the shade store"
result: pass
source: automated
summary_file: 11-04-SUMMARY.md
coverage_id: C2
evidence: ["cgb_compat_internal_bg", "cgb_rgb_store_shade_untouched"]

### 24. Objects pick set 1 or 2 by OAM bit 4 through OBP0 or OBP1 and OAM bits 0-3 have no effect
expected: "Objects pick set 1 or 2 by OAM bit 4 through OBP0 or OBP1 and OAM bits 0-3 have no effect"
result: pass
source: automated
summary_file: 11-04-SUMMARY.md
coverage_id: C3
evidence: ["cgb_compat_internal_obj_sets"]

### 25. CGB attributes in vram bank 1, VBK and OPRI do not change the compat frame
expected: "CGB attributes in vram bank 1, VBK and OPRI do not change the compat frame"
result: pass
source: automated
summary_file: 11-04-SUMMARY.md
coverage_id: C4
evidence: ["cgb_compat_internal_attr_ignored"]

### 26. LCDC bit 0 clear renders BG index 0 through BGP while objects still draw, and objects order by smaller X then lower OAM index
expected: "LCDC bit 0 clear renders BG index 0 through BGP while objects still draw, and objects order by smaller X then lower OAM index"
result: pass
source: automated
summary_file: 11-04-SUMMARY.md
coverage_id: C5
evidence: ["cgb_compat_internal_lcdc0", "cgb_compat_internal_x_order"]

### 27. A mid-frame compat palette change affects later pixels and never alters the completed frame until the next completion
expected: "A mid-frame compat palette change affects later pixels and never alters the completed frame until the next completion"
result: pass
source: automated
summary_file: 11-04-SUMMARY.md
coverage_id: C6
evidence: ["cgb_compat_internal_live_config"]

### 28. DMG output is byte-identical and every new function and branch carries a MODEL tag with a docs row
expected: "DMG output is byte-identical and every new function and branch carries a MODEL tag with a docs row"
result: pass
source: automated
summary_file: 11-04-SUMMARY.md
coverage_id: C7
evidence: ["cgb_dmg_identity_shade_pin", "bash tests/scripts/verify-dmg-baseline.sh", "model_gates"]

### 29. Every one of the 6144 oracle rows matches the colour the real CGB-mode and compat-mode pixel functions produce, and the checked count is asserted
expected: "Every one of the 6144 oracle rows matches the colour the real CGB-mode and compat-mode pixel functions produce, and the checked count is asserted"
result: pass
source: automated
summary_file: 11-05-SUMMARY.md
coverage_id: C1
evidence: ["cgb_priority_truth_table"]

### 30. A deterministic sample of 64 rows rendered through whole frames with real OAM matches the oracle
expected: "A deterministic sample of 64 rows rendered through whole frames with real OAM matches the oracle"
result: pass
source: automated
summary_file: 11-05-SUMMARY.md
coverage_id: C2
evidence: ["cgb_priority_truth_frames"]

### 31. Each composer input (BG attribute bit 7, OAM bit 7, LCDC.0, the BG index 0 rule) is shown able to break the table
expected: "Each composer input (BG attribute bit 7, OAM bit 7, LCDC.0, the BG index 0 rule) is shown able to break the table"
result: pass
source: automated
summary_file: 11-05-SUMMARY.md
coverage_id: C3
evidence: ["cgb_priority_mutant_ignore_bg_attr7", "cgb_priority_mutant_ignore_obj_attr7", "cgb_priority_mutant_lcdc0_inverted", "cgb_priority_mutant_no_index0_rule"]

### 32. CGB-mode objects order by OAM index only and OPRI has no effect: an X-order mutant fails the table and an OPRI-live mutant fails the no-effect case
expected: "CGB-mode objects order by OAM index only and OPRI has no effect: an X-order mutant fails the table and an OPRI-live mutant fails the no-effect case"
result: pass
source: automated
summary_file: 11-05-SUMMARY.md
coverage_id: C4
evidence: ["cgb_priority_opri_no_effect", "cgb_priority_mutant_cgb_x_order", "cgb_priority_mutant_opri_live"]

### 33. Compat renderer semantics (LCDC.0 as BG enable, objects through their own palette sets) are mutation-checked on the compat rows
expected: "Compat renderer semantics (LCDC.0 as BG enable, objects through their own palette sets) are mutation-checked on the compat rows"
result: pass
source: automated
summary_file: 11-05-SUMMARY.md
coverage_id: C5
evidence: ["cgb_priority_mutant_compat_lcdc0_ignored", "cgb_priority_mutant_compat_bg_set_for_objects"]

### 34. Attribute bank, flip bits and VBK independence each have a detected mutant
expected: "Attribute bank, flip bits and VBK independence each have a detected mutant"
result: pass
source: automated
summary_file: 11-05-SUMMARY.md
coverage_id: C6
evidence: ["cgb_attr_mutant_ignore_bank", "cgb_attr_mutant_swap_flips", "cgb_attr_mutant_reads_vbk", "cgb_attr_mutant_obj_bank_ignored"]

### 35. No core source was edited and DMG output stays byte-identical
expected: "No core source was edited and DMG output stays byte-identical"
result: pass
source: automated
summary_file: 11-05-SUMMARY.md
coverage_id: C7
evidence: ["bash tests/scripts/verify-dmg-baseline.sh"]

### 36. gbb_copy_frame_rgb555 rejects every invalid argument before the profile check, writes nothing on any error and serves both CGB mode and compat mode
expected: "gbb_copy_frame_rgb555 rejects every invalid argument before the profile check, writes nothing on any error and serves both CGB mode and compat mode"
result: pass
source: automated
summary_file: 11-06-SUMMARY.md
coverage_id: C1
evidence: ["cgb_rgb555_args", "cgb_rgb555_dmg_profile", "cgb_rgb555_not_ready", "cgb_rgb555_both_modes"]

### 37. While the LCD is off the last completed frame stays readable and the generation does not advance
expected: "While the LCD is off the last completed frame stays readable and the generation does not advance"
result: pass
source: automated
summary_file: 11-06-SUMMARY.md
coverage_id: C2
evidence: ["cgb_rgb555_lcd_off"]

### 38. Moving the profile check ahead of the argument checks is detected, with a passing control on the same mutated core
expected: "Moving the profile check ahead of the argument checks is detected, with a passing control on the same mutated core"
result: pass
source: automated
summary_file: 11-06-SUMMARY.md
coverage_id: C3
evidence: ["cgb_rgb555_mutant_skewed_validator", "cgb_rgb555_mutant_skewed_validator_control"]

### 39. The compat palette set and get follow the struct_size handshake, reject bit 15 without partial mutation, survive reset and load, and a set never recolours a completed frame
expected: "The compat palette set and get follow the struct_size handshake, reject bit 15 without partial mutation, survive reset and load, and a set never recolours a completed frame"
result: pass
source: automated
summary_file: 11-06-SUMMARY.md
coverage_id: C4
evidence: ["palette_compat_api_default", "palette_compat_api_roundtrip", "palette_compat_api_reject", "palette_compat_api_get_reject", "palette_compat_api_larger", "palette_compat_api_survives", "palette_compat_effect_next_frame"]

### 40. Masking bit 15 instead of rejecting it is detected, with a passing control
expected: "Masking bit 15 instead of rejecting it is detected, with a passing control"
result: pass
source: automated
summary_file: 11-06-SUMMARY.md
coverage_id: C5
evidence: ["palette_compat_mutant_mask_bit15", "palette_compat_mutant_mask_bit15_control"]

### 41. The documented default palette equals the code table and the recomputed rule, and an altered doc copy is rejected
expected: "The documented default palette equals the code table and the recomputed rule, and an altered doc copy is rejected"
result: pass
source: automated
summary_file: 11-06-SUMMARY.md
coverage_id: C6
evidence: ["cgb_tables_compat_palette", "cgb_tables_compat_palette_mutated_doc"]

### 42. The host guide keeps the new colour promises and the installed C and C++ consumers call every new symbol, each check proven able to fail
expected: "The host guide keeps the new colour promises and the installed C and C++ consumers call every new symbol, each check proven able to fail"
result: pass
source: automated
summary_file: 11-06-SUMMARY.md
coverage_id: C7
evidence: ["cgb_native_guide_contract", "cgb_native_guide_contract_missing_selftest", "installed_consumer_c", "installed_consumer_cpp", "cgb_consumer_symbol_coverage", "cgb_consumer_symbol_coverage_selftest"]

### 43. Every new function and branch carries a MODEL tag with a docs row and DMG output stays byte-identical
expected: "Every new function and branch carries a MODEL tag with a docs row and DMG output stays byte-identical"
result: pass
source: automated
summary_file: 11-06-SUMMARY.md
coverage_id: C8
evidence: ["model_gates", "bash tests/scripts/verify-dmg-baseline.sh"]

### 44. A guest that rewrites BG colour 0 in each HBlank shows its own colour on every one of the 144 rows of the public RGB555 frame, the first completed frame holds no reset-fill zero pixel, and the frame digest is pinned
expected: "A guest that rewrites BG colour 0 in each HBlank shows its own colour on every one of the 144 rows of the public RGB555 frame, the first completed frame holds no reset-fill zero pixel, and the frame digest is pinned"
result: pass
source: automated
summary_file: 11-07-SUMMARY.md
coverage_id: C1
evidence: ["cgb_colour_hblank_rows"]

### 45. Resolving the whole frame against one CRAM snapshot is detected as a wrong row, with a passing control on the same mutated core
expected: "Resolving the whole frame against one CRAM snapshot is detected as a wrong row, with a passing control on the same mutated core"
result: pass
source: automated
summary_file: 11-07-SUMMARY.md
coverage_id: C2
evidence: ["cgb_colour_mutant_frame_resolve", "cgb_colour_mutant_frame_resolve_control"]

### 46. The committed fixture ROM matches the size and SHA-256 recorded in its manifest
expected: "The committed fixture ROM matches the size and SHA-256 recorded in its manifest"
result: pass
source: automated
summary_file: 11-07-SUMMARY.md
coverage_id: C3
evidence: ["cgb_colour_fixture_digest"]

### 47. The RGB555 digest helpers serialise explicit little-endian pairs, the independent Python computation of the pinned frame digest agrees, and the DMG digest vectors are unchanged
expected: "The RGB555 digest helpers serialise explicit little-endian pairs, the independent Python computation of the pinned frame digest agrees, and the DMG digest vectors are unchanged"
result: pass
source: automated
summary_file: 11-07-SUMMARY.md
coverage_id: C4
evidence: ["acceptance_digest_vectors", "python3 -I computation of the GBB-RGB555LE-v1 digest of the table-derived frame equals the pinned abb528b8ffd636f85dcd62b1f13e60ea2f1ef7ac368c84b4767e5b967d2e9546"]

### 48. The manifest-driven script rebuilds every ROM from its recipe with RGBDS 1.0.1 byte for byte, rejects a different tool version and a tampered ROM, and the CI job runs it
expected: "The manifest-driven script rebuilds every ROM from its recipe with RGBDS 1.0.1 byte for byte, rejects a different tool version and a tampered ROM, and the CI job runs it"
result: pass
source: automated
summary_file: 11-07-SUMMARY.md
coverage_id: C5
evidence: ["bash tests/scripts/reproduce-cgb-colour.sh"]

### 49. DMG output stays byte-identical
expected: "DMG output stays byte-identical"
result: pass
source: automated
summary_file: 11-07-SUMMARY.md
coverage_id: C6
evidence: ["bash tests/scripts/verify-dmg-baseline.sh"]

### 50. Every CGB BG attribute rule (palette, tile bank, X and Y flip, unused bit 4, BG priority) and OBJ bank and palette selection is shown on a guest-built frame through the public RGB555 call, with literal per-cell colours checked before the digest pin
expected: "Every CGB BG attribute rule (palette, tile bank, X and Y flip, unused bit 4, BG priority) and OBJ bank and palette selection is shown on a guest-built frame through the public RGB555 call, with literal per-cell colours checked before the digest pin"
result: pass
source: automated
summary_file: 11-08-SUMMARY.md
coverage_id: C1
evidence: ["cgb_colour_attr"]

### 51. With LCDC bit 0 clear the BG is still drawn and the BG-priority cell shows the object, on a guest-built frame
expected: "With LCDC bit 0 clear the BG is still drawn and the BG-priority cell shows the object, on a guest-built frame"
result: pass
source: automated
summary_file: 11-08-SUMMARY.md
coverage_id: C2
evidence: ["cgb_colour_lcdc0"]

### 52. A guest exercises palette RAM auto-increment, wrap, read-back, read without increment, the mode-3 blocked write that still increments, the blocked read and the LCD-off write, reporting through WRAM markers; a core whose blocked write does not increment fails the guest while its control still passes
expected: "A guest exercises palette RAM auto-increment, wrap, read-back, read without increment, the mode-3 blocked write that still increments, the blocked read and the LCD-off write, reporting through WRAM markers; a core whose blocked write does not increment fails the guest while its control still passes"
result: pass
source: automated
summary_file: 11-08-SUMMARY.md
coverage_id: C3
evidence: ["cgb_colour_guest_cram", "cgb_colour_guest_cram_mutant_blocked_no_increment", "cgb_colour_guest_cram_mutant_blocked_no_increment_control"]

### 53. In compatibility mode BGP, OBP0 and OBP1 select shades that map through the default palette set of their own region, and after gbb_set_compat_palette the next completed frame uses the override for BG, OBJ0 and OBJ1 separately
expected: "In compatibility mode BGP, OBP0 and OBP1 select shades that map through the default palette set of their own region, and after gbb_set_compat_palette the next completed frame uses the override for BG, OBJ0 and OBJ1 separately"
result: pass
source: automated
summary_file: 11-08-SUMMARY.md
coverage_id: C4
evidence: ["palette_compat_mapping"]

### 54. While the guest keeps the LCD off the completed frame is retained and the generation is frozen, and the internal working RGB buffer is all 0x7FFF
expected: "While the guest keeps the LCD off the completed frame is retained and the generation is frozen, and the internal working RGB buffer is all 0x7FFF"
result: pass
source: automated
summary_file: 11-08-SUMMARY.md
coverage_id: C5
evidence: ["cgb_colour_lcd_off", "cgb_rgb_store_lcdoff_fixture"]

### 55. The five new committed ROMs match the sizes and SHA-256 digests in their manifest rows and rebuild byte for byte from their recipes with RGBDS 1.0.1 (six ROMs in total)
expected: "The five new committed ROMs match the sizes and SHA-256 digests in their manifest rows and rebuild byte for byte from their recipes with RGBDS 1.0.1 (six ROMs in total)"
result: pass
source: automated
summary_file: 11-08-SUMMARY.md
coverage_id: C6
evidence: ["cgb_colour_fixture_digest", "bash tests/scripts/reproduce-cgb-colour.sh"]

### 56. DMG output stays byte-identical
expected: "DMG output stays byte-identical"
result: pass
source: automated
summary_file: 11-08-SUMMARY.md
coverage_id: C7
evidence: ["bash tests/scripts/verify-dmg-baseline.sh"]

### 57. A CGB frame-digest case runs through the runner on the CGB profile, captures through gbb_copy_frame_rgb555 and prints an RGB555-labelled digest under frame555, identically for --model cgb-cpu-e and --profile cgb
expected: "A CGB frame-digest case runs through the runner on the CGB profile, captures through gbb_copy_frame_rgb555 and prints an RGB555-labelled digest under frame555, identically for --model cgb-cpu-e and --profile cgb"
result: pass
source: automated
summary_file: 11-09-SUMMARY.md
coverage_id: C1
evidence: ["acceptance_cgb_colour_hblank", "acceptance_cgb_colour_hblank_profile_flag"]

### 58. The CGB runner path can fail and refuse: the wrong model is excluded, a flipped reference digest fails with reason frame-mismatch and a fresh 69135-byte RGB555 PPM, and a CGB progress-predicate run reports frame-unsupported-profile
expected: "The CGB runner path can fail and refuse: the wrong model is excluded, a flipped reference digest fails with reason frame-mismatch and a fresh 69135-byte RGB555 PPM, and a CGB progress-predicate run reports frame-unsupported-profile"
result: pass
source: automated
summary_file: 11-09-SUMMARY.md
coverage_id: C2
evidence: ["acceptance_cgb_colour_excluded_dmg", "acceptance_cgb_colour_flipped_ppm", "acceptance_cgb_colour_progress_refused"]

### 59. The RGB555 digest, padding independence, 0x8000 rejection with nothing written, channel expansion and PPM bytes agree with an independent Python implementation
expected: "The RGB555 digest, padding independence, 0x8000 rejection with nothing written, channel expansion and PPM bytes agree with an independent Python implementation"
result: pass
source: automated
summary_file: 11-09-SUMMARY.md
coverage_id: C3
evidence: ["acceptance_digest_rgb555_vectors", "python3 -I tests/scripts/rgb-digest-vector.py --rgb555"]

### 60. DMG digest format, receipts and the frozen baseline are byte-identical
expected: "DMG digest format, receipts and the frozen baseline are byte-identical"
result: pass
source: automated
summary_file: 11-09-SUMMARY.md
coverage_id: C4
evidence: ["bash tests/scripts/verify-dmg-baseline.sh", "acceptance_digest_vectors"]

### 61. ppu_disabled_state runs on the CGB profile for 20 frames, the last two LCD-on frames are identical and every pixel is 0x03E0, matching the pinned digest; the same ROM in compatibility mode yields one uniform default BG value
expected: "ppu_disabled_state runs on the CGB profile for 20 frames, the last two LCD-on frames are identical and every pixel is 0x03E0, matching the pinned digest; the same ROM in compatibility mode yields one uniform default BG value"
result: pass
source: automated
summary_file: 11-10-SUMMARY.md
coverage_id: C1
evidence: ["magentests_cgb_ppu_disabled_state", "magentests_cgb_ppu_disabled_state_compat"]

### 62. oam_internal_priority matches the 84-pixel mask derived from the pinned source and bg_oam_priority matches the eight-cell layout with no 0x001F pixel, both before their digests are accepted
expected: "oam_internal_priority matches the 84-pixel mask derived from the pinned source and bg_oam_priority matches the eight-cell layout with no 0x001F pixel, both before their digests are accepted"
result: pass
source: automated
summary_file: 11-10-SUMMARY.md
coverage_id: C2
evidence: ["magentests_cgb_oam_internal_priority", "magentests_cgb_bg_oam_priority"]

### 63. Each predicate can fail: skipping the LCD-off mode-0 transition, resolving object colours from BG CRAM and inverting the LCDC.0 composer each fail their ROM, and the controls pass on the same mutant binary
expected: "Each predicate can fail: skipping the LCD-off mode-0 transition, resolving object colours from BG CRAM and inverting the LCDC.0 composer each fail their ROM, and the controls pass on the same mutant binary"
result: pass
source: automated
summary_file: 11-10-SUMMARY.md
coverage_id: C3
evidence: ["magentests_cgb_mutant_lcd_off_no_mode0", "magentests_cgb_mutant_lcd_off_no_mode0_control", "magentests_cgb_mutant_obj_from_bg_cram", "magentests_cgb_mutant_obj_from_bg_cram_control", "magentests_cgb_mutant_lcdc0_inverted", "magentests_cgb_mutant_lcdc0_inverted_control"]

### 64. Vendored bytes match the manifest, stay out of installs, and the rebuild table agrees with the manifest rows; the DMG baseline and existing mbc_oob_sram cases are unchanged
expected: "Vendored bytes match the manifest, stay out of installs, and the rebuild table agrees with the manifest rows; the DMG baseline and existing mbc_oob_sram cases are unchanged"
result: pass
source: automated
summary_file: 11-10-SUMMARY.md
coverage_id: C4
evidence: ["magentests_fixture_digest", "magentests_not_installed", "bash tests/scripts/reproduce-magentests.sh --self-check", "bash tests/scripts/verify-dmg-baseline.sh"]

### 65. The six AGE m3-bg-lcdc and m3-bg-scx variants carry expected-unsupported with reason mode-3-pixel-timing, every Mealybug m3_* case at the pinned tree carries unsupported-model, the docs mirror equals the record, and no tracked fixture carries such a ROM or image
expected: "The six AGE m3-bg-lcdc and m3-bg-scx variants carry expected-unsupported with reason mode-3-pixel-timing, every Mealybug m3_* case at the pinned tree carries unsupported-model, the docs mirror equals the record, and no tracked fixture carries such a ROM or image"
result: pass
source: automated
summary_file: 11-11-SUMMARY.md
coverage_id: C1
evidence: ["cgb_external_dispositions"]

### 66. A changed AGE reason is rejected by the verifier with disposition-mismatch
expected: "A changed AGE reason is rejected by the verifier with disposition-mismatch"
result: pass
source: automated
summary_file: 11-11-SUMMARY.md
coverage_id: C2
evidence: ["cgb_external_dispositions_mutated"]

### 67. The local acid2 runner decodes and compares synthetic data correctly: PNG round trip, equal frames, a one-pixel mismatch reported as pixels=1, and a fake ROM refused
expected: "The local acid2 runner decodes and compares synthetic data correctly: PNG round trip, equal frames, a one-pixel mismatch reported as pixels=1, and a fake ROM refused"
result: pass
source: automated
summary_file: 11-11-SUMMARY.md
coverage_id: C3
evidence: ["cgb_acid2_local_selftest"]

### 68. An unpinned ROM is refused with exit 2 before anything is run or decoded
expected: "An unpinned ROM is refused with exit 2 before anything is run or decoded"
result: pass
source: automated
summary_file: 11-11-SUMMARY.md
coverage_id: C4
evidence: ["cgb_acid2_local_refuses_unpinned"]

### 69. The select_profile seam maps every model and $143 value to the right profile, reports the CGB-only note only for a $C0 ROM on the DMG model, rejects a PGB header for every model, and leaves its outputs unchanged for a missing file
expected: "The select_profile seam maps every model and $143 value to the right profile, reports the CGB-only note only for a $C0 ROM on the DMG model, rejects a PGB header for every model, and leaves its outputs unchanged for a missing file"
result: pass
source: automated
summary_file: 11-12-SUMMARY.md
coverage_id: C1
evidence: ["player_session_model_select", "player_session_model_pgb", "player_session_model_missing_file"]

### 70. A session library whose select_profile ignores the model fails player_session_model_select
expected: "A session library whose select_profile ignores the model fails player_session_model_select"
result: pass
source: automated
summary_file: 11-12-SUMMARY.md
coverage_id: C2
evidence: ["player_cgb_model_mutant_ignores_flag"]

### 71. RGB555 to RGBA32 expansion equals the independent formula for all 32768 values at two pitches, alpha is always 255, and a red/blue-swapped colour.c fails the same test
expected: "RGB555 to RGBA32 expansion equals the independent formula for all 32768 values at two pitches, alpha is always 255, and a red/blue-swapped colour.c fails the same test"
result: pass
source: automated
summary_file: 11-12-SUMMARY.md
coverage_id: C3
evidence: ["player_cgb_expand", "player_cgb_expand_mutant_rb_swap"]

### 72. The window title model token is DMG, CGB or CGB (DMG-compat) from the machine mode, and - with no ROM
expected: "The window title model token is DMG, CGB or CGB (DMG-compat) from the machine mode, and - with no ROM"
result: pass
source: automated
summary_file: 11-12-SUMMARY.md
coverage_id: C4
evidence: ["player_cgb_title_token"]

### 73. The real player renders colour-attr.gb in colour: the uploaded RGBA digest is pinned, at least 14 distinct colours appear, 40 rendered-surface spot pixels equal values computed in CMake from the fixture's literal RGB555 palette entries, and the title token is CGB
expected: "The real player renders colour-attr.gb in colour: the uploaded RGBA digest is pinned, at least 14 distinct colours appear, 40 rendered-surface spot pixels equal values computed in CMake from the fixture's literal RGB555 palette entries, and the title token is CGB"
result: pass
source: automated
summary_file: 11-12-SUMMARY.md
coverage_id: C5
evidence: ["player_cgb_smoke"]

### 74. A player built with R and B swapped in colour.c and a player whose update_frame is forced onto the DMG path each make the smoke check fail
expected: "A player built with R and B swapped in colour.c and a player whose update_frame is forced onto the DMG path each make the smoke check fail"
result: pass
source: automated
summary_file: 11-12-SUMMARY.md
coverage_id: C6
evidence: ["player_cgb_smoke_mutant_rb_swap", "player_cgb_smoke_mutant_dmg_path"]

### 75. The --model grammar: an unknown or missing value is a usage error with exit 2, cgb on a DMG-only ROM reports CGB (DMG-compat), auto picks CGB for a CGB ROM, dmg and the default model refuse the colour smoke, and auto picks DMG for a DMG ROM
expected: "The --model grammar: an unknown or missing value is a usage error with exit 2, cgb on a DMG-only ROM reports CGB (DMG-compat), auto picks CGB for a CGB ROM, dmg and the default model refuse the colour smoke, and auto picks DMG for a DMG ROM"
result: pass
source: automated
summary_file: 11-12-SUMMARY.md
coverage_id: C7
evidence: ["player_cgb_cli"]

### 76. The existing DMG player behaviour is unchanged: --model auto --smoke passes exactly like player_smoke, including the invalid-ROM replacement that fails its probe and leaves the session intact, and the whole player suite still passes
expected: "The existing DMG player behaviour is unchanged: --model auto --smoke passes exactly like player_smoke, including the invalid-ROM replacement that fails its probe and leaves the session intact, and the whole player suite still passes"
result: pass
source: automated
summary_file: 11-12-SUMMARY.md
coverage_id: C8
evidence: ["player_cgb_model_auto_smoke", "bash tests/scripts/verify-phase3-player.sh --build-package"]

### 77. The pinned player limitations text states the D-44 claims verbatim: DMG and CGB software with --model auto|dmg|cgb (default dmg), the fixed compatibility palette with no palette flag, no colour correction, the DMG APU model on the CGB profile, and CGB mode-3 timing, double speed and HDMA not claimed
expected: "The pinned player limitations text states the D-44 claims verbatim: DMG and CGB software with --model auto|dmg|cgb (default dmg), the fixed compatibility palette with no palette flag, no colour correction, the DMG APU model on the CGB profile, and CGB mode-3 timing, double speed and HDMA not claimed"
result: pass
source: automated
summary_file: 11-13-SUMMARY.md
coverage_id: C1
evidence: ["player_limitations"]

### 78. Every phrase of one list appears in limitations.h, README.md and the macOS capability_limits string, and the Linux string (which keeps saying it has no SDL player) carries the shorter list
expected: "Every phrase of one list appears in limitations.h, README.md and the macOS capability_limits string, and the Linux string (which keeps saying it has no SDL player) carries the shorter list"
result: pass
source: automated
summary_file: 11-13-SUMMARY.md
coverage_id: C2
evidence: ["player_claims_agree"]

### 79. A README copy with a phrase removed is rejected with exit 1 and claims-disagree naming that phrase
expected: "A README copy with a phrase removed is rejected with exit 1 and claims-disagree naming that phrase"
result: pass
source: automated
summary_file: 11-13-SUMMARY.md
coverage_id: C3
evidence: ["player_claims_agree_mutated"]

### 80. The remaining player tests, the packaged player smoke and the full phase1 suite are unchanged by the text edits
expected: "The remaining player tests, the packaged player smoke and the full phase1 suite are unchanged by the text edits"
result: pass
source: automated
summary_file: 11-13-SUMMARY.md
coverage_id: C4
evidence: ["bash tests/scripts/verify-phase3-player.sh --build-package"]

### 81. Every research:11 gate is resolved or re-assigned to Phase 14 with a reason, docs and code tags agree, and a reverted row is rejected with phase-11-row-open
expected: "Every research:11 gate is resolved or re-assigned to Phase 14 with a reason, docs and code tags agree, and a reverted row is rejected with phase-11-row-open"
result: pass
source: automated
summary_file: 11-14-SUMMARY.md
coverage_id: C1
evidence: ["model_gates", "model_gates_no_phase11_rows", "model_gates_no_phase11_rows_mutated_doc"]

### 82. Palette RAM traffic, LCD toggles, run slices and compat-palette sets (struct_size around 28, bit 15, NULL) keep every RGB555 pixel at or below 0x7FFF, leave the palette unchanged on a rejected set and keep the DMG profile's RGB store empty
expected: "Palette RAM traffic, LCD toggles, run slices and compat-palette sets (struct_size around 28, bit 15, NULL) keep every RGB555 pixel at or below 0x7FFF, leave the palette unchanged on a rejected set and keep the DMG profile's RGB store empty"
result: pass
source: automated
summary_file: 11-14-SUMMARY.md
coverage_id: C2
evidence: ["cgb_fuzz_palette_regressions", "fuzz_core_regressions"]

### 83. A core with the 0x7FFF resolve mask removed breaks the bit-15 invariant on a guest CRAM word of 0xFFFF, and the same binary stays quiet on seeds without such a word
expected: "A core with the 0x7FFF resolve mask removed breaks the bit-15 invariant on a guest CRAM word of 0xFFFF, and the same binary stays quiet on seeds without such a word"
result: pass
source: automated
summary_file: 11-14-SUMMARY.md
coverage_id: C3
evidence: ["cgb_fuzz_palette_mutant_no_mask", "cgb_fuzz_palette_mutant_no_mask_control"]

### 84. measure_core creates the CGB profile for the colour workload, rejects an unknown profile name, and leaves the DMG output and tracer digest unchanged
expected: "measure_core creates the CGB profile for the colour workload, rejects an unknown profile name, and leaves the DMG output and tracer digest unchanged"
result: pass
source: automated
summary_file: 11-14-SUMMARY.md
coverage_id: C4
evidence: ["cgb_measure_core_cgb_profile", "cgb_measure_core_unknown_profile", "banking_tracer_digest_unchanged"]

### 85. The advisory interleaved A/B of the DMG profile against the Phase 10 head keeps the tracer digest 4c7a57ff3d50d228 on both builds, the D-22 trigger does not fire, and the harness receipt shape is enforced
expected: "The advisory interleaved A/B of the DMG profile against the Phase 10 head keeps the tracer digest 4c7a57ff3d50d228 on both builds, the D-22 trigger does not fire, and the harness receipt shape is enforced"
result: pass
source: automated
summary_file: 11-14-SUMMARY.md
coverage_id: C5
evidence: ["cgb_bench_ab_selftest", "cgb_bench_ab_wrong_digest"]

### 86. DMG byte-identity holds at the plan head and the packaged player smoke, including its pinned CGB colour digest, passes against the final core
expected: "DMG byte-identity holds at the plan head and the packaged player smoke, including its pinned CGB colour digest, passes against the final core"
result: pass
source: automated
summary_file: 11-14-SUMMARY.md
coverage_id: C6
evidence: ["bash tests/scripts/verify-dmg-baseline.sh", "cgb_dmg_identity_shade_pin", "banking_dmg_flat_reference", "bash tests/scripts/verify-phase3-player.sh --build-package"]

### 87. DECISIONS holds consecutive rows D-076 to D-083 for the eight adopted Phase 11 choices, each naming Phase 11 D-NN, evidence tests and a revisit trigger
expected: "DECISIONS holds consecutive rows D-076 to D-083 for the eight adopted Phase 11 choices, each naming Phase 11 D-NN, evidence tests and a revisit trigger"
result: pass
source: automated
summary_file: 11-15-SUMMARY.md
coverage_id: C1
evidence: ["python3 -I memory check from 11-15-PLAN Task 1 (prints memory ok)"]

### 88. The research INDEX Phase 11 bullet links resolve and the three memory files contain no home path or email
expected: "The research INDEX Phase 11 bullet links resolve and the three memory files contain no home path or email"
result: pass
source: automated
summary_file: 11-15-SUMMARY.md
coverage_id: C2
evidence: ["python3 -I link check plus grep for /Users/ and @gmail on DECISIONS, INDEX and LESSONS"]

### 89. The phase COVERAGE.md is one declaration line with a reason of at most 200 characters and the api-coverage verify:pre gate passes
expected: "The phase COVERAGE.md is one declaration line with a reason of at most 200 characters and the api-coverage verify:pre gate passes"
result: pass
source: automated
summary_file: 11-15-SUMMARY.md
coverage_id: C3
evidence: ["gsd-tools check api-coverage.verify-pre on the phase directory (passed true, block false)", "test of single line and length in 11-15-PLAN Task 2 verify"]

### 90. The handoff names Phase 11 execution as the completed stage, /gsd-verify-work 11 as the next command, Phase 12: CGB Double Speed as the unstarted following phase, and no Phase 12 directory exists
expected: "The handoff names Phase 11 execution as the completed stage, /gsd-verify-work 11 as the next command, Phase 12: CGB Double Speed as the unstarted following phase, and no Phase 12 directory exists"
result: pass
source: automated
summary_file: 11-15-SUMMARY.md
coverage_id: C4
evidence: ["grep of STATE.md and .continue-here.md for Phase 12: CGB Double Speed and /gsd-verify-work 11, and absence of a GB-12 directory"]

### 91. The full phase1 suite passes at the plan head
expected: "The full phase1 suite passes at the plan head"
result: pass
source: automated
summary_file: 11-15-SUMMARY.md
coverage_id: C5
evidence: ["ctest --preset phase1 --output-on-failure --no-tests=error (684 of 684 passed)"]

## Summary

total: 91
passed: 91
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps

[none]
