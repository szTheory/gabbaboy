---
status: complete
phase: GB-10-cgb-profile-banking-and-register-visibility
source: 10-01-SUMMARY.md, 10-02-SUMMARY.md, 10-03-SUMMARY.md, 10-04-SUMMARY.md, 10-05-SUMMARY.md, 10-06-SUMMARY.md, 10-07-SUMMARY.md, 10-08-SUMMARY.md, 10-09-SUMMARY.md, 10-10-SUMMARY.md, 10-11-SUMMARY.md, 10-12-SUMMARY.md, 10-13-SUMMARY.md, 10-14-SUMMARY.md, 10-15-SUMMARY.md, 10-16-SUMMARY.md, 10-17-SUMMARY.md, 10-18-SUMMARY.md, 10-19-SUMMARY.md, 10-20-SUMMARY.md
started: 2026-10-12T23:34:09Z
updated: 2026-10-12T23:34:48.091Z
---

## Current Test

[testing complete]

## Tests

Automated evidence for tests 1-12 was gathered at 3c0d6bc (code head; the only later change is COVERAGE.md). Local macOS arm64 Debug: CTest 541/541, inventory --installed 541 executed none skipped, `verify-dmg-baseline.sh` baseline status=pass, `verify-model-gates.py` pass. Hosted CI at 3c0d6bc: ci run 38318873877 all eight required jobs success (including linux-asan-ubsan and native-windows-x64), fixture-repro 38318873887 success (cgb-banking and mooneye-cgb byte-identical), preview-package-smoke success on attempt 2.

### 1. Select the CGB-CPU-E profile, probe a ROM and read model and execution mode (CGB-01)
expected: gbb_probe_rom and gbb_get_info report model and execution mode from header $143 bit 7 (CGB or DMG-compatibility), reject PGB with GBB_UNSUPPORTED_EXECUTION_MODE, reject an undersized struct_size, allocate nothing on probe and leave mode unchanged on a failed load; CGB-only ROMs load on DMG with an informational flag; unknown profiles fail.
result: pass
source: automated
evidence: "ctest -R '^cgb_(probe_|info_|profile_|cgb_only_on_dmg|copy_frame_cgb)' (10-05, 10-06)"

### 2. Mode-specific post-boot state with per-field provenance; DMG row byte-identical (CGB-01)
expected: DMG, CGB and compat post-boot columns match the table with provenance labels (HW_TEST only in COMPAT), flipped-value controls fail, the DIV phase sweep holds, channel 1 is silent after boot, and the DMG pin survives the post_boot[] refactor.
result: pass
source: automated
evidence: "ctest -R '^cgb_postboot_' (17 cases incl. *_flipped and cgb_postboot_div_real_rom_sweep_shifted negative control; 10-04, 10-06, 10-16)"

### 3. Post-boot and I/O docs mirror the code tables (CGB-01, CGB-02)
expected: docs/cgb-profile.md post-boot and io sections match post_boot[] and io_visibility[]; a mutated doc fails.
result: pass
source: automated
evidence: "ctest -R '^cgb_tables_' (incl. *_mutated_doc and selftest; 10-07, 10-10)"

### 4. Every DMG-specific behaviour is tagged by model in code and docs (CGB-02)
expected: verify-model-gates.py finds every core function and model-differing branch tagged, the docs table is a bijection with the code, and untagged, deleted-tag, doc-mismatch and --release mutants each fail.
result: pass
source: automated
evidence: "ctest -R '^model_gates' (8 cases; 10-01, 10-02); python3 -I tests/scripts/verify-model-gates.py pass"

### 5. Register visibility matrix passes per cell for DMG, CGB and compat (CGB-02)
expected: Every FF00-FF7F cell reads and writes per its column; deferred cells refuse reads and latch the stop address on writes; IE bits 5-7 are stored on CGB only; flip, cross-column and sweep controls fail.
result: pass
source: automated
evidence: "ctest -R '^cgb_visibility_' (13 cases; 10-09, 10-10)"

### 6. KEY0 is locked after boot; STOP with KEY1 armed fails closed (CGB-02)
expected: KEY0 writes after boot have no effect on CGB and compat, a reset is idempotent, a cross-column control fails; STOP with KEY1 armed latches unsupported-bus at FF4D instead of switching speed; unarmed and DMG STOP keep old behaviour.
result: pass
source: automated
evidence: "ctest -R '^cgb_(key0_|stop_)' (8 cases; 10-11)"

### 7. VRAM 2x8 KiB and WRAM 8x4 KiB banking with echo RAM (CGB-03)
expected: VBK and SVBK select banks (SVBK 0 maps to 1) in CGB mode only; echo RAM follows the selected WRAM bank; DMG banks are frozen and match a flat-memory reference; the tracer digest is unchanged; echo mutants fail.
result: pass
source: automated
evidence: "ctest -R '^banking_' (incl. banking_mutant_echo_ignores_bank; 10-08, 10-09, 10-12)"

### 8. Model-correct OAM DMA source behaviour (CGB-03)
expected: CGB OAM DMA reads ROM pages, cart RAM, the selected VRAM and WRAM banks and high pages through the bank map; the wrong-bank mutant fails.
result: pass
source: automated
evidence: "ctest -R '^banking_(dma_|mutant_dma_)' (10-12)"

### 9. Original banking fixtures and Mooneye CGB ROMs verify CGB behaviour (CGB-03)
expected: fixtures/cgb-banking guests pass on CGB, compat and DMG with three controls; Mooneye boot_div-cgbABCDE, boot_regs-cgb pass and boot_hwio-C, unused_hwio-C stop as expected-unsupported at FF76; digest, inventory, pc-table, expected-unsupported and unknown-manifest tampering fails; no third-party ROM installs; both fixture sets rebuild byte-identically.
result: pass
source: automated
evidence: "ctest -R '^cgb_(banking_|mooneye_)' (24 cases; 10-13..10-16); fixture-repro 38318873887 cgb-banking-repro and mooneye-cgb-repro success"

### 10. DMG output unchanged and runner labels are profile-correct
expected: The frozen DMG baseline matches; DMG acceptance and Mooneye runs are byte-identical through the new --profile mapping; CGB cases never report DMG-CPU-B; an unknown model or a model/profile conflict exits non-zero.
result: pass
source: automated
evidence: "bash tests/scripts/verify-dmg-baseline.sh baseline status=pass; ctest -R '^(cgb_runner_|acceptance_unknown_model_refused$)' (10-03, WR-01 927ff60)"

### 11. Fuzz, loader and consumer coverage on both profiles with instance isolation
expected: Bounded fuzz with random profile selection keeps bank indices in range after every step; the loader matrix agrees on both profiles; two instances share no state; hosted ASan/UBSan is clean.
result: pass
source: automated
evidence: "ctest -R '^cgb_(fuzz_|loader_|instance_)' (10-18, Nyquist cgb_fuzz_profile_select); ci 38318873877 linux-asan-ubsan success"

### 12. Half-dot timeline decision recorded and banking cost measured (success criterion 4)
expected: DECISIONS.md D-070 records the half-dot unit, static asserts compile it, and the contract fails if a name is undeclared or missing; the native guide states the CGB API correctly; the A/B benchmark receipt records the DMG cost against the Phase 7 baseline and rejects a wrong digest or missing field.
result: pass
source: automated
evidence: "ctest -R '^cgb_(adr_|native_guide_|bench_ab_)' (10-17, 10-19); 10-BENCH.md shows about +6-7% on a loaded host (owner veto item)"

## Summary

total: 12
passed: 12
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps

[none yet]

## Notes

- Coverage blocks in all 20 SUMMARYs use a `deliverable:` key and flow-style `ctest` entries that the coverage classifier rejects (same as Phase 9). Their 118 cited test names were all checked against tests/expected-tests.txt and mapped by hand to tests 1-12 above.
- All 20 SUMMARY commit claims reconcile exactly against their plan_head_before..plan_head_after windows.
- Zero human UAT per DECISIONS D-069. The six owner veto items in PR #66 (gbb_info ABI, PGB rejection, gbb_copy_frame on CGB, DMG FF4C-FF7F fail-closed, the +5% bench trigger, CGB IE bits 5-7) are owner decisions, not UAT checkpoints.
- verify:pre api-coverage gate blocked because the COVERAGE.md opt-out reason was over 200 characters; shortened to the Phase 9 form (no external API integration).
- Live-DOM and Playwright UI verification do not apply: no browser surface in this phase.
