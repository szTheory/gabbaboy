---
status: complete
phase: GB-14-cgb-e-model-qualification-and-corpus
source: 14-01-SUMMARY.md, 14-02-SUMMARY.md, 14-03-SUMMARY.md, 14-04-SUMMARY.md, 14-05-SUMMARY.md, 14-06-SUMMARY.md, 14-07-SUMMARY.md, 14-08-SUMMARY.md, 14-09-SUMMARY.md, 14-10-SUMMARY.md, 14-11-SUMMARY.md, 14-12-SUMMARY.md, 14-13-SUMMARY.md
started: 2026-10-16T12:17:25.662739+00:00
updated: 2026-10-16T12:23:07.844Z
---

## Automated Evidence

OpenGSD 1.16.0 classifies every one of the 49 structured SUMMARY deliverables across 13 plans as automated: zero present entries or errors. D-069 and the owner instruction authorize automated closure without a confirmation-only checkpoint. Both auto-advance flags remain false.

All 13 bounded commit windows reconcile against reachable ancestors. Four SUMMARY files (14-05, 14-09, 14-10, 14-11) use the legacy `actuals.commits` location; these produce a top-level-field warning, and their exact base/after counts were independently checked. History-redaction mappings remain preserved; no lost task commit is inferred from an unbounded base-to-current-HEAD count.

| Plan | Base | After | Claimed / measured |
|---|---|---|---|
| 14-01 | `e463512aae7ce03e2b429973b4baf2b40d67297d` | `1ddacb60962d32e23133ef72de4bc4d105037d60` | 12 / 12 |
| 14-02 | `6c5b7040a40a25ca1f21aae11f97a8268d05c80b` | `01e1797a4720926a7ef843935fabb562360a4913` | 4 / 4 |
| 14-03 | `72dd987ab214a888c5605d7a2e015ff8f7d82c3c` | `e6e89a8f1730c004df9c90829b583c4853d07003` | 4 / 4 |
| 14-04 | `b7044289ccae28d48a02f70a51ef7ec791357c21` | `7635b3886664fb5f08e93bfb3aa842fc9dc10fc7` | 4 / 4 |
| 14-05 | `f019f755f66f6b41fc00b39807df4bd32b19bf69` | `3cacf9822f2a36ce787920adaae56e996cf4ccc8` | 3 / 3 |
| 14-06 | `74bad9a53867584190e7be66c32d6c387b9f03b3` | `4c927c4bf87dbabc41042c6757340d4e04f757ea` | 4 / 4 |
| 14-07 | `e566a7fcd149ac7b6e801a61c0ed2ce15ca7044f` | `cb54cc62c2985eaef63d4f6f2d820d21ddde1c09` | 5 / 5 |
| 14-08 | `b04f2378d8a4f931006d90b7415262a432baaf22` | `bc33b8941c3a4381681ff80921d1619fb815eaa7` | 6 / 6 |
| 14-09 | `ff3367ca22eac6f87cf8bbcb542264dd0c50bafe` | `f3827cc56b9198edc38d8f3c6215697ccbe9c662` | 4 / 4 |
| 14-10 | `affaa4f28665e2e5a4c655cf67b199bf8088c37a` | `7721a5cefe05eaf4ce43188441ac82f8c42c61c3` | 5 / 5 |
| 14-11 | `b78ba07c2f36d1fa837a90cbcd7d1d13742805d2` | `8b1f120fa296ae1212bdf68e6147e0da3c5db47f` | 7 / 7 |
| 14-12 | `30fcb3a9bb6b8ed36f3f4e29225807c298d3e993` | `e21112c259a10d1d6c6a049eddb852435104facc` | 12 / 12 |
| 14-13 | `b1ff601e665a45816a9606f1af5c5035e5ee8668` | `a29f8c92c84e072cb23775bdfecd88a8a839bc39` | 6 / 6 |

Execution head `9c5b32dc4c75ad5f9eba44ff1c7b0a15ba0f9c7f` has exact-head hosted receipts: [CI](https://github.com/szTheory/gabbaboy/actions/runs/38845800948) 8/8, [fixture reproduction](https://github.com/szTheory/gabbaboy/actions/runs/38845800952) 7/7, [package smoke](https://github.com/szTheory/gabbaboy/actions/runs/38845800953) 4/4, every job successful and none skipped. Linux passed 1,138/1,138, Windows 1,126/1,126 and Linux ASan/UBSan 1,133/1,133. These receipts belong to that execution revision; the final UAT revision requires its own exact-head checks before merge. GitHub holds the latest published head and merge receipt.

The complete software corpus has 107 cases, 25 actual passes and 82 matched expected failures. Hardware CGB-E remains UNKNOWN/POLICY; analog/perceptual output, IR peers and game acceptance remain unqualified. Rights/model exclusions stay outside the executed denominator. Phase 15 owns acceptance and release, including release PR #70. No Phase 15 work is started here.

The verify-pre API gate initially selected the hardware `14-SOURCE-COVERAGE.md` as an external API matrix. `COVERAGE.md` now records the existing no-external-integration decision; the enabled gate passes without a fake capability or disabled check. UI scope is limitation-copy only, already covered by executable copy contracts; there is no browser or perceptual checkpoint. Existing security has zero open threats, and completed security/Nyquist/UI hooks are reused.

`verify-uat-contract.py --self-test` preserves every SUMMARY/id/criterion/evidence mapping, exact commit windows, and the completed handoff, including the machine-readable state route and Phase 15 pause. It rejects weakened records and stale routes locally. Recurring behavior, mutations, summary schema, consumer, package and corpus checks already run in CI; this boundary-only check adds no dependency or duplicate CI lane. Reopen completed UAT only for a changed covered contract, a concrete regression, or stale/unavailable evidence. The next owner-selected command is `/gsd-discuss-phase 15`.

## Current Test

[testing complete]

## Tests

### 1. Native CGB guests read PCM12 and PCM34 as CH2:CH1 and CH4:CH3 digital nibbles, including channel phase advancement.
expected: "Native CGB guests read PCM12 and PCM34 as CH2:CH1 and CH4:CH3 digital nibbles, including channel phase advancement."
result: pass
source: automated
summary_file: 14-01-SUMMARY.md
coverage_id: D1
evidence: ["ctest --test-dir build -R '^(cgb_pcm_tracer|cgb_pcm_channels)$' --output-on-failure --no-tests=error", "tests/test_cgb_apu.c#cgb_pcm_channels expects PCM12=0xef, PCM34=0xfa, and pulse phase 0x0f then 0x00"]

### 2. PCM reads obey the native CGB, compatibility, and DMG visibility policies, and the frozen DMG baseline remains byte-identical.
expected: "PCM reads obey the native CGB, compatibility, and DMG visibility policies, and the frozen DMG baseline remains byte-identical."
result: pass
source: automated
summary_file: 14-01-SUMMARY.md
coverage_id: D2
evidence: ["ctest --test-dir build -R '^(cgb_visibility_matrix_dmg|cgb_visibility_matrix_compat|cgb_visibility_matrix_cgb|cgb_visibility_boundaries|cgb_visibility_deferred_stop)$' --output-on-failure --no-tests=error", "bash tests/scripts/verify-dmg-baseline.sh"]

### 3. PCM output is read-only and independent of host routing, volume, and sample-buffer availability or draining; named controls detect incorrect implementations.
expected: "PCM output is read-only and independent of host routing, volume, and sample-buffer availability or draining; named controls detect incorrect implementations."
result: pass
source: automated
summary_file: 14-01-SUMMARY.md
coverage_id: D3
evidence: ["ctest --test-dir build -R '^(cgb_pcm_power_dac|cgb_pcm_readonly|cgb_pcm_host_invariance|cgb_pcm_controls)$' --output-on-failure --no-tests=error", "Negative controls: swapped-nibble observed expected=0x0f actual=0xf0; routing-coupled observed expected-muted=0x0f actual=0x00; writable PCM observed expected-readonly=0x0f actual=0xa5."]

### 4. Existing CGB Mooneye author pass assertions remain separate from exact current software-model failure observations; failing guests are never counted as passes.
expected: "Existing CGB Mooneye author pass assertions remain separate from exact current software-model failure observations; failing guests are never counted as passes."
result: pass
source: automated
summary_file: 14-01-SUMMARY.md
coverage_id: D4
evidence: ["ctest --test-dir build -R '^cgb_mooneye_' --output-on-failure --no-tests=error", "Raw protocol verdicts: boot_hwio-C fail callback 0x01F5/result 0x4067; unused_hwio-C fail callback 0x1A31/result 0x4070. Tampered pass disposition, stale unsupported stop, changed fail callback, and false xfail on a passing ROM all remain nonzero controls."]

### 5. PCM helper model tags and independent visibility-table checks agree with the native CGB, compatibility, and DMG policies for FF76/FF77.
expected: "PCM helper model tags and independent visibility-table checks agree with the native CGB, compatibility, and DMG policies for FF76/FF77."
result: pass
source: automated
summary_file: 14-01-SUMMARY.md
coverage_id: D5
evidence: ["ctest --test-dir build -R '^(model_gates.*|cgb_tables_.*)$' --output-on-failure --no-tests=error", "Negative controls: model_gates_real_deleted_tag, model_gates_real_untagged_function, model_gates_real_doc_mismatch; cgb_tables self-test rejected six PCM profile-disposition mutations plus three existing visibility mutations (pass mutants=12 overall)."]

### 6. Native CGB FF56 reads and writes follow the disconnected-receiver policy, with compatibility and DMG access unchanged.
expected: "Native CGB FF56 reads and writes follow the disconnected-receiver policy, with compatibility and DMG access unchanged."
result: pass
source: automated
summary_file: 14-02-SUMMARY.md
coverage_id: D1
evidence: ["ctest --test-dir build -R '^(cgb_ir_tracer|cgb_ir_controls|cgb_ir_modes)$' --output-on-failure --no-tests=error", "Negative guest predicates report mask expected=$3E actual=$1E and compatibility expected=$FF actual=$BE."]

### 7. FF56 creation, successful-load, reset, failed-load preservation, and instance isolation are checked alongside FF72-FF75 mode cells and PCM12/PCM34.
expected: "FF56 creation, successful-load, reset, failed-load preservation, and instance isolation are checked alongside FF72-FF75 mode cells and PCM12/PCM34."
result: pass
source: automated
summary_file: 14-02-SUMMARY.md
coverage_id: D2
evidence: ["ctest --test-dir build -R '^(cgb_ir_controls|cgb_ir_modes|cgb_visibility_matrix_dmg|cgb_visibility_matrix_compat|cgb_visibility_matrix_cgb|cgb_visibility_cross_column_control)$' --output-on-failure --no-tests=error", "ctest --test-dir build -R '^(cgb_tables_io|cgb_tables_io_mutated_doc|cgb_tables_postboot|cgb_tables_postboot_selftest)$' --output-on-failure --no-tests=error", "Negative controls report FF56 reset expected=$00 actual=$01, failed-load expected=$C1 actual=$00, and table mutants reject FF75 mask and compatibility FF74 decode changes; postboot self-test passes mutants=14."]

### 8. Model-gate claims, exact Mooneye observations, and the frozen DMG baseline remain aligned with the implementation.
expected: "Model-gate claims, exact Mooneye observations, and the frozen DMG baseline remain aligned with the implementation."
result: pass
source: automated
summary_file: 14-02-SUMMARY.md
coverage_id: D3
evidence: ["Focused model-gate, CGB Mooneye disposition, CGB speed reset, and HDMA lifecycle selections pass 29/29 tests.", "Mooneye boot_hwio-C and unused_hwio-C retain author_expect=pass, observed=fail, exact callback/result signatures, and status=xfail; the disposition controls pass.", "bash tests/scripts/verify-dmg-baseline.sh reports inventory=313, Mooneye=15, acceptance=20, benchmark=2, changed rows=0, status=pass."]

### 9. CGB CH3 retains the previous sample through trigger until a timed fetch, and PCM and host mix use the same latched sample.
expected: "CGB CH3 retains the previous sample through trigger until a timed fetch, and PCM and host mix use the same latched sample."
result: pass
source: automated
summary_file: 14-03-SUMMARY.md
coverage_id: D1
evidence: ["ctest --test-dir build -R '^(cgb_apu_wave_latch|cgb_apu_wave_fetch|cgb_apu_wave_direct_ram_control)$' --output-on-failure --no-tests=error", "Direct-RAM mutant diagnostic expected=07 actual=0A before fetch; guest observes new sample after fetch."]

### 10. CGB APU power, off-state writes, active wave access, length and sweep ordering, and normal/double-speed DIV transitions have guest assertions and controls.
expected: "CGB APU power, off-state writes, active wave access, length and sweep ordering, and normal/double-speed DIV transitions have guest assertions and controls."
result: pass
source: automated
summary_file: 14-03-SUMMARY.md
coverage_id: D2
evidence: ["ctest --test-dir build -R '^(cgb_apu_power|cgb_apu_off_writes|cgb_apu_wave_access|cgb_apu_trigger_length_sweep|cgb_apu_div_stop|cgb_apu_transition_controls|model_gates)$' --output-on-failure --no-tests=error", "ctest related CGB APU, PCM, DMG APU, table, speed, runner, and disposition cohorts with -j2; 54/54 passed, including omitted-DIV and CH4-frequency controls."]

### 11. Audio and model-gate claims track the implemented CGB behavior while preserving the frozen DMG baseline and precise unresolved DMG limitations.
expected: "Audio and model-gate claims track the implemented CGB behavior while preserving the frozen DMG baseline and precise unresolved DMG limitations."
result: pass
source: automated
summary_file: 14-03-SUMMARY.md
coverage_id: D3
evidence: ["bash tests/scripts/verify-dmg-baseline.sh", "python3 -I tests/scripts/verify-model-gates.py; model-gates pass functions=186 gates=100 unknown=34", "ctest --test-dir build -R '^(model_gates|summary_coverage|cgb_speed_dispositions(_.*)?|cgb_apu_(power|off_writes|wave_access|trigger_length_sweep|div_stop|transition_controls|wave_latch|wave_fetch|wave_direct_ram_control))$' --output-on-failure --no-tests=error -j2; 15/15 passed", "cmake --preset phase1 && cmake --build --preset phase1"]

### 12. CH3 fetch and PCM guest observations remain equal across split runs at normal and double speed.
expected: "CH3 fetch and PCM guest observations remain equal across split runs at normal and double speed."
result: pass
source: automated
summary_file: 14-04-SUMMARY.md
coverage_id: D1
evidence: ["ctest --test-dir build -R '^(cgb_apu_partition_fetch|cgb_apu_partition_speed|cgb_apu_partition_controls|cgb_partition_snapshot_fidelity)$' --output-on-failure --no-tests=error"]

### 13. Reset, successful load, failed-load preservation, and separate-instance isolation cover APU and IR state.
expected: "Reset, successful load, failed-load preservation, and separate-instance isolation cover APU and IR state."
result: pass
source: automated
summary_file: 14-04-SUMMARY.md
coverage_id: D2
evidence: ["ctest --test-dir build -R '^(cgb_apu_lifecycle|cgb_apu_lifecycle_controls)$' --output-on-failure --no-tests=error"]

### 14. Guest PCM and bus observations are invariant under absent, full, and drained host audio output through DIV, speed-switch, and HDMA transitions.
expected: "Guest PCM and bus observations are invariant under absent, full, and drained host audio output through DIV, speed-switch, and HDMA transitions."
result: pass
source: automated
summary_file: 14-04-SUMMARY.md
coverage_id: D3
evidence: ["ctest --test-dir build -R '^cgb_apu_output_pressure$' --output-on-failure --no-tests=error"]

### 15. Deterministic hostile APU seeds exercise truncated and oversized loader inputs with bounded guest operations and terminal observations.
expected: "Deterministic hostile APU seeds exercise truncated and oversized loader inputs with bounded guest operations and terminal observations."
result: pass
source: automated
summary_file: 14-04-SUMMARY.md
coverage_id: D4
evidence: ["ctest --test-dir build -R '^cgb_apu_hostile_seeds$' --output-on-failure --no-tests=error"]

### 16. Shared HDMA and speed identity seams remain green and the frozen DMG baseline stays unchanged.
expected: "Shared HDMA and speed identity seams remain green and the frozen DMG baseline stays unchanged."
result: pass
source: automated
summary_file: 14-04-SUMMARY.md
coverage_id: D5
evidence: ["ctest --test-dir build -R '^(cgb_hdma_partition_midbyte|cgb_hdma_lifecycle|cgb_hdma_competing_stalls|cgb_speed_identity_pin)$' --output-on-failure --no-tests=error", "bash tests/scripts/verify-dmg-baseline.sh"]

### 17. Frozen pinned source closure and selected CGB model/mode case identities
expected: "Frozen pinned source closure and selected CGB model/mode case identities"
result: pass
source: automated
summary_file: 14-05-SUMMARY.md
coverage_id: D1
evidence: ["python3 -I tests/scripts/verify-cgb-corpus-inventory.py --selection-only", "python3 -I tests/scripts/verify-cgb-corpus-inventory.py --self-test; 18 named mutation controls"]

### 18. Admission, rights, model applicability, and MagenTests documentation agree with pinned manifests
expected: "Admission, rights, model applicability, and MagenTests documentation agree with pinned manifests"
result: pass
source: automated
summary_file: 14-05-SUMMARY.md
coverage_id: D2
evidence: ["python3 -I tests/scripts/verify-cgb-corpus-inventory.py --selection-only", "python3 -I tests/scripts/verify-cgb-corpus-inventory.py --self-test; stale Magen claim and false evidence controls"]

### 19. The five added Mooneye CGB outputs reproduce byte-identically from the pinned source and toolchain recipe, and all nine selected guests execute to a terminal protocol result.
expected: "The five added Mooneye CGB outputs reproduce byte-identically from the pinned source and toolchain recipe, and all nine selected guests execute to a terminal protocol result."
result: pass
source: automated
summary_file: 14-06-SUMMARY.md
coverage_id: D1
evidence: ["bash tests/scripts/reproduce-mooneye-cgb.sh --compare fixtures/mooneye-cgb", "ctest --test-dir build -j2 -R '^(cgb_corpus_mooneye_boot_regs_cgb|cgb_corpus_mooneye_boot_div_cgbABCDE|cgb_corpus_mooneye_boot_hwio_C|cgb_corpus_mooneye_unused_hwio_C|cgb_corpus_mooneye_daa|cgb_corpus_mooneye_div_write|cgb_corpus_mooneye_tim00|cgb_corpus_mooneye_tim00_div_trigger|cgb_corpus_mooneye_vblank_stat_intr_C)$' --output-on-failure --no-tests=error"]

### 20. The exact Mooneye identities, model, compatibility mode, header byte, ROM hashes, manifest digest, assertion signatures, and CTest bindings are checked independently.
expected: "The exact Mooneye identities, model, compatibility mode, header byte, ROM hashes, manifest digest, assertion signatures, and CTest bindings are checked independently."
result: pass
source: automated
summary_file: 14-06-SUMMARY.md
coverage_id: D2
evidence: ["ctest --test-dir build -j2 -R '^(cgb_mooneye_fixture_digest|cgb_mooneye_inventory|cgb_mooneye_digest_tamper|cgb_mooneye_inventory_tamper|cgb_mooneye_pc_table|cgb_mooneye_pc_table_tamper|cgb_corpus_inventory_selection|cgb_corpus_inventory_selftest)$' --output-on-failure --no-tests=error", "ctest --test-dir build --show-only=json-v1 plus the required-name check: missing-required-tests: []"]

### 21. Six guests count as passes and three author-pass guests remain exact xfails; missing bytes, wrong model or mode, altered callback/register signatures, and false xfail promotion are rejected.
expected: "Six guests count as passes and three author-pass guests remain exact xfails; missing bytes, wrong model or mode, altered callback/register signatures, and false xfail promotion are rejected."
result: pass
source: automated
summary_file: 14-06-SUMMARY.md
coverage_id: D3
evidence: ["ctest --test-dir build -j2 -R '^(cgb_corpus_mooneye_controls|cgb_mooneye_required_suite)$' --output-on-failure --no-tests=error", "Runner receipt: eligible=9 executed=9; guest pass=6; exact xfail=3; expected-failure=3/3; nine assertion rows, one per case."]

### 22. All 70 pinned APU ROM outputs are admitted with source and output digests, rights records, and byte-identical reproduction.
expected: "All 70 pinned APU ROM outputs are admitted with source and output digests, rights records, and byte-identical reproduction."
result: pass
source: automated
summary_file: 14-07-SUMMARY.md
coverage_id: D1
evidence: ["bash tests/scripts/reproduce-samesuite.sh --self-check && bash tests/scripts/reproduce-samesuite.sh --self-test && GBB_RGBDS_ARCHIVE=/tmp/gabbaboy-rgbds-v1.0.1.zip bash tests/scripts/reproduce-samesuite.sh --compare-pinned"]

### 23. The bounded CGB-CPU-E run records all 70 terminal case outcomes and 4,784 result assertions while preserving pass as each author's expectation.
expected: "The bounded CGB-CPU-E run records all 70 terminal case outcomes and 4,784 result assertions while preserving pass as each author's expectation."
result: pass
source: automated
summary_file: 14-07-SUMMARY.md
coverage_id: D2
evidence: ["build/tests/test_samesuite_apu --suite fixtures/samesuite/manifest.json --dispositions tests/external/cgb-apu-dispositions.json"]

### 24. Exact per-case membership, tracer contracts, and eight named negative controls reject cohort omissions, result-selected filtering, altered expectations, changed receipts, and unexpected passes.
expected: "Exact per-case membership, tracer contracts, and eight named negative controls reject cohort omissions, result-selected filtering, altered expectations, changed receipts, and unexpected passes."
result: pass
source: automated
summary_file: 14-07-SUMMARY.md
coverage_id: D3
evidence: ["ctest --test-dir build --output-on-failure --parallel 2 --no-tests=error -R '^(cgb_samesuite_apu_(membership|controls|tracer|tracer_controls|channel_.*|div_.*)|cgb_corpus_inventory_(selection|selftest)|cgb_external_dispositions.*|cgb_speed_dispositions.*)$'"]

### 25. The frozen inventory reports 109 admitted outputs, no pending output bytes, and 107 required cases while retaining six admitted AGE image cases as not executed.
expected: "The frozen inventory reports 109 admitted outputs, no pending output bytes, and 107 required cases while retaining six admitted AGE image cases as not executed."
result: pass
source: automated
summary_file: 14-07-SUMMARY.md
coverage_id: D4
evidence: ["python3 -I tests/scripts/verify-cgb-corpus-inventory.py --selection-only && python3 -I tests/scripts/verify-cgb-corpus-inventory.py --self-test"]

### 26. Six AGE mode-3 ROMs and reference PNGs are admitted with pinned source, rights, digests, CGB-E expectations, and distinct mode and speed identities.
expected: "Six AGE mode-3 ROMs and reference PNGs are admitted with pinned source, rights, digests, CGB-E expectations, and distinct mode and speed identities."
result: pass
source: automated
summary_file: 14-08-SUMMARY.md
coverage_id: D1
evidence: ["bash tests/scripts/reproduce-age.sh --self-check && bash tests/scripts/reproduce-age.sh --compare"]

### 27. AGE fixture validation rejects altered, missing, cross-paired, misclassified, or stale-provenance inputs with named diagnostics.
expected: "AGE fixture validation rejects altered, missing, cross-paired, misclassified, or stale-provenance inputs with named diagnostics."
result: pass
source: automated
summary_file: 14-08-SUMMARY.md
coverage_id: D2
evidence: ["bash tests/scripts/test-reproduce-age.sh compare-tampered", "bash tests/scripts/test-reproduce-age.sh selfcheck-tampered"]

### 28. CMake and disposition validators route the explicit AGE protocol to 13 row-oracle cases, keep six image fixtures pending, and reject unknown or altered membership.
expected: "CMake and disposition validators route the explicit AGE protocol to 13 row-oracle cases, keep six image fixtures pending, and reject unknown or altered membership."
result: pass
source: automated
summary_file: 14-08-SUMMARY.md
coverage_id: D3
evidence: ["cmake -S . -B /tmp/gabbaboy14-wave2-dispositions-20261015 -G Ninja -DCMAKE_BUILD_TYPE=Debug -DBUILD_TESTING=ON && cmake --build /tmp/gabbaboy14-wave2-dispositions-20261015 --parallel 8 && ctest --test-dir /tmp/gabbaboy14-wave2-dispositions-20261015 --output-on-failure -R '^(age_.*|cgb_tables_.*|model_gates.*|summary_coverage.*|fixture_digest|cgb_mooneye_(inventory|fixture_digest).*|cgb_external_dispositions.*|cgb_speed_dispositions.*)$'", "python3 -I tests/scripts/verify-external-dispositions.py --record tests/external/cgb-ppu-dispositions.json --doc docs/cgb-profile.md --repo-root . && python3 -I tests/scripts/verify-cgb-speed-dispositions.py"]

### 29. Bounded public-API guest capture and source-derived RGB555 PNG oracle reject malformed or altered images.
expected: "Bounded public-API guest capture and source-derived RGB555 PNG oracle reject malformed or altered images."
result: pass
source: automated
summary_file: 14-09-SUMMARY.md
coverage_id: D1
evidence: ["cgb_age_m3_tracer and cgb_age_m3_pixel_controls in the phase1 CTest suite", "python3 -I tests/scripts/verify-age-m3-pixels.py --self-test", "cgb_age_m3_early_frame_control in the phase1 CTest suite"]

### 30. Six exact AGE image identities are executed and compared with preserved author targets and measured dispositions.
expected: "Six exact AGE image identities are executed and compared with preserved author targets and measured dispositions."
result: pass
source: automated
summary_file: 14-09-SUMMARY.md
coverage_id: D2
evidence: ["six cgb_age_m3_m3_bg_* CTest cases and cgb_age_m3_membership", "tests/scripts/verify-age-m3-pixels.py case, signature, model, mode, and speed checks", "cgb_external_dispositions and cgb_speed_dispositions CTest checks"]

### 31. Image receipts remain consistent across AGE manifests, inventory, disposition validators, and reproduction controls.
expected: "Image receipts remain consistent across AGE manifests, inventory, disposition validators, and reproduction controls."
result: pass
source: automated
summary_file: 14-09-SUMMARY.md
coverage_id: D3
evidence: ["22 focused phase1 CTest checks covering AGE pixels, inventory, external dispositions, speed, and reproduction controls", "python3 -I tests/scripts/verify-cgb-corpus-inventory.py --selection-only", "bash tests/scripts/reproduce-age.sh --self-check"]

### 32. Normal-speed STAT and inherited AGE row observations retain source identities, independent expected values, and exact guest dispositions.
expected: "Normal-speed STAT and inherited AGE row observations retain source identities, independent expected values, and exact guest dispositions."
result: pass
source: automated
summary_file: 14-10-SUMMARY.md
coverage_id: CGB-08-AGE-ROWS
evidence: ["ctest --test-dir build --output-on-failure --no-tests=error -R '^(cgb_age_assertion_identity|age_stat_mode_cgbE|age_stat_mode_ds_cgbBCE|age_stat_mode_sprites_dmgC_cgbBCE|age_stat_mode_sprites_ds_cgbBCE|age_stat_mode_window_cgbBCE|age_stat_mode_window_ds_cgbBCE|age_spsw_mode0_cgbBCE|age_spsw_ch2_lc_delay_cgbBCE)$'"]

### 33. Mixed LY and SCX/STAT semantics, row omission and duplication, xpass, signature drift, and hostile fixture bounds are rejected.
expected: "Mixed LY and SCX/STAT semantics, row omission and duplication, xpass, signature drift, and hostile fixture bounds are rejected."
result: pass
source: automated
summary_file: 14-10-SUMMARY.md
coverage_id: CGB-08-AGE-NEGATIVE-CONTROLS
evidence: ["ctest --test-dir build --output-on-failure --no-tests=error -R '^(cgb_age_assertion_controls|cgb_phase14_inherited_contract_unit)$'"]

### 34. All 19 admitted AGE identities bind unique tests while six image cases and their pixel controls remain distinct from row outcomes.
expected: "All 19 admitted AGE identities bind unique tests while six image cases and their pixel controls remain distinct from row outcomes."
result: pass
source: automated
summary_file: 14-10-SUMMARY.md
coverage_id: CGB-10-AGE-CORPUS
evidence: ["ctest --test-dir build --output-on-failure --no-tests=error -R '^(cgb_corpus_inventory_selection|cgb_corpus_inventory_selftest|cgb_age_m3_tracer|cgb_age_m3_m3_bg_lcdc_cgbBCE|cgb_age_m3_m3_bg_lcdc_nocgb_ncmBCE|cgb_age_m3_m3_bg_lcdc_ds_cgbBCE|cgb_age_m3_m3_bg_scx_cgbBCE|cgb_age_m3_m3_bg_scx_nocgb_ncmBCE|cgb_age_m3_m3_bg_scx_ds_cgbBCE|cgb_age_m3_pixel_controls|cgb_age_m3_early_frame_control)$'"]

### 35. Each of the 31 inherited research14 gates has a tested resolution or explicit, owned evidence limitation mirrored in model-gate documentation.
expected: "Each of the 31 inherited research14 gates has a tested resolution or explicit, owned evidence limitation mirrored in model-gate documentation."
result: pass
source: automated
summary_file: 14-10-SUMMARY.md
coverage_id: CGB-08-RESEARCH14-OWNERSHIP
evidence: ["ctest --test-dir build --output-on-failure --no-tests=error -R '^(cgb_research14_dispositions|cgb_research14_dispositions_controls|model_gates|cgb_speed_dispositions|cgb_hdma_dispositions)$'"]

### 36. AGE additions preserve frozen corpus membership, speed-domain rules, and the byte-identical DMG baseline.
expected: "AGE additions preserve frozen corpus membership, speed-domain rules, and the byte-identical DMG baseline."
result: pass
source: automated
summary_file: 14-10-SUMMARY.md
coverage_id: CGB-10-FROZEN-CORPUS-BASELINE
evidence: ["python3 -I tests/scripts/verify-speed-domains.py src/core/gabbaboy.c && bash tests/scripts/verify-dmg-baseline.sh"]

### 37. A real Mooneye tracer case produces a fresh identity-bound receipt and terminal summary.
expected: "A real Mooneye tracer case produces a fresh identity-bound receipt and terminal summary."
result: pass
source: automated
summary_file: 14-11-SUMMARY.md
coverage_id: D1
evidence: ["ctest --test-dir build -R '^cgb_corpus_report_tracer$' --output-on-failure --no-tests=error"]

### 38. The full frozen corpus reconciles case outcomes, expected failures, assertion rows, and image comparisons.
expected: "The full frozen corpus reconciles case outcomes, expected failures, assertion rows, and image comparisons."
result: pass
source: automated
summary_file: 14-11-SUMMARY.md
coverage_id: D2
evidence: ["python3 -I tests/scripts/verify-cgb-corpus-report.py --run --build-dir build --receipt build/cgb-corpus-receipt.json", "python3 -I tests/scripts/verify-cgb-corpus-report.py --from-ctest --build-dir build --receipt build/cgb-corpus-from-ctest.json"]

### 39. Hostile receipt streams and inventory mutations reject with bounded diagnostics while clean controls pass.
expected: "Hostile receipt streams and inventory mutations reject with bounded diagnostics while clean controls pass."
result: pass
source: automated
summary_file: 14-11-SUMMARY.md
coverage_id: D3
evidence: ["ctest --test-dir build -R '^(cgb_corpus_report_contract|cgb_corpus_report_controls|cgb_corpus_report_tracer|cgb_corpus_report_tracer_controls)$' --output-on-failure --no-tests=error", "python3 -I tests/scripts/verify-cgb-corpus-inventory.py --self-test"]

### 40. The Phase 14 live AGE checker accepts exact source-labelled rows and rejects altered row values.
expected: "The Phase 14 live AGE checker accepts exact source-labelled rows and rejects altered row values."
result: pass
source: automated
summary_file: 14-11-SUMMARY.md
coverage_id: D4
evidence: ["ctest --test-dir build -R '^cgb_age_assertion_identity$' --output-on-failure --no-tests=error", "ctest --test-dir build -R '^cgb_age_assertion_controls$' --output-on-failure --no-tests=error"]

### 41. Native CI validates exact corpus bindings and creates a fresh complete receipt from one full CTest execution.
expected: "Native CI validates exact corpus bindings and creates a fresh complete receipt from one full CTest execution."
result: pass
source: automated
summary_file: 14-12-SUMMARY.md
coverage_id: D1
evidence: ["Fresh committed-head receipt: 107/107 cases from the nonce-bound 1,133-test CTest stream; 1133 executed, none skipped", "tests/scripts/test-cgb-corpus-report.py: TestList, captured output, omission, duplication, stale identity controls", "python3 -I tests/scripts/verify-cgb-corpus-inventory.py --ci-contract"]

### 42. Inventory binding checks and pinned reproduction paths preserve exact selection, rights, output digests, and tamper rejection.
expected: "Inventory binding checks and pinned reproduction paths preserve exact selection, rights, output digests, and tamper rejection."
result: pass
source: automated
summary_file: 14-12-SUMMARY.md
coverage_id: D2
evidence: ["python3 -I tests/scripts/verify-cgb-corpus-inventory.py --bindings", "python3 -I tests/scripts/verify-cgb-corpus-inventory.py --self-test; verifies strict --complete rejection for magentests:bg_oam_priority", "AGE, SameSuite, and Mooneye CGB pinned reproduction commands and their tamper controls"]

### 43. Relocated C and C++ consumers and package smoke remain valid, and corpus ROM/reference bytes stay outside installed packages.
expected: "Relocated C and C++ consumers and package smoke remain valid, and corpus ROM/reference bytes stay outside installed packages."
result: pass
source: automated
summary_file: 14-12-SUMMARY.md
coverage_id: D3
evidence: ["Full CTest stream: installed_consumer_c, installed_consumer_cpp, installed_consumer_phase2_c, installed_consumer_phase2_cpp, preview_package_smoke", "cgb_corpus_not_installed_controls: renamed ROM and renamed AGE PNG rejected by digest", "cgb_consumer_symbol_coverage and cgb_hdma_claims_contract_native"]

### 44. Native integration documentation limits audio observations to guest digital registers and states physical and analog exclusions.
expected: "Native integration documentation limits audio observations to guest digital registers and states physical and analog exclusions."
result: pass
source: automated
summary_file: 14-12-SUMMARY.md
coverage_id: D4
evidence: ["cgb_hdma_claims_contract_native scans native-integration.md for FF76/FF77 and explicit analog/physical limits"]

### 45. Native CI uses one nonce-specific JUnit path for receipt, required inventory, and DMG checks, and publishes only privacy-safe corpus evidence.
expected: "Native CI uses one nonce-specific JUnit path for receipt, required inventory, and DMG checks, and publishes only privacy-safe corpus evidence."
result: pass
source: automated
summary_file: 14-12-SUMMARY.md
coverage_id: D5
evidence: ["cgb_corpus_ci_contract and inventory self-tests reject stale JUnit consumers, raw XML uploads, and a missing hashed build target", "python3 -I tests/scripts/verify-cgb-corpus-artifacts.py --check --build-dir build: 3 privacy-safe JSON payloads; raw Test.xml and JUnit excluded", "python3 -I tests/scripts/verify-cgb-corpus-artifacts.py --self-test rejects host paths in Test.xml and JUnit", "Clean Ninja build and covered-input rebuild proved stamp ordering; cgb_corpus_report_tracer rejected a stale runner and passed after fresh configure/build"]

### 46. CGB profile, audio, corpus, and gate claims bind to source expectations, stable identities, exact mode cells, and a fresh complete receipt.
expected: "CGB profile, audio, corpus, and gate claims bind to source expectations, stable identities, exact mode cells, and a fresh complete receipt."
result: pass
source: automated
summary_file: 14-13-SUMMARY.md
coverage_id: D1
evidence: ["cgb_corpus_claims and cgb_corpus_claims_controls; 15 semantic controls cover wrong cells, xfail inflation, oracle swaps, missing gates, hardware claims, and omitted limits.", "python3 -I tests/scripts/verify-cgb-corpus-claims.py --receipt build/cgb-corpus-receipt.json; 107/107 cases, 25 observed passes, 82 matched xfails, 2,845/4,959 assertion rows passed.", "cgb_corpus_report_contract; native CI contract verifies the claims consumer runs after receipt construction."]

### 47. README, preview, unreleased notes, and player limitation claims agree with the qualified software model and explicit exclusions.
expected: "README, preview, unreleased notes, and player limitation claims agree with the qualified software model and explicit exclusions."
result: pass
source: automated
summary_file: 14-13-SUMMARY.md
coverage_id: D2
evidence: ["player_claims_agree, player_claims_agree_mutated, player_limitations, cgb_speed_docs_no_stale_claims, cgb_hdma_claims_contract_native.", "cgb_corpus_claims_controls rejects omitted compatibility policy, removed analog limits, and hardware overclaims."]

### 48. Persisted RED records and public evidence artifacts contain no workstation paths while preserving the original test evidence.
expected: "Persisted RED records and public evidence artifacts contain no workstation paths while preserving the original test evidence."
result: pass
source: automated
summary_file: 14-13-SUMMARY.md
coverage_id: D3
evidence: ["cgb_corpus_red_evidence_privacy; checks five sanitized historical records and detects a synthetic absolute path.", "OpenGSD 1.16.0 check tdd-red-evidence classified all five historical records and the new Task 3 record RED_EVIDENCE_OK.", "verify-cgb-corpus-artifacts.py --check --build-dir build; three allowlisted JSON files passed, raw Test.xml/JUnit stayed local."]

### 49. The registered exact test inventory and durable research, decision, lesson, and plan-history links pass automated contracts.
expected: "The registered exact test inventory and durable research, decision, lesson, and plan-history links pass automated contracts."
result: pass
source: automated
summary_file: 14-13-SUMMARY.md
coverage_id: D4
evidence: ["Full nonce-bound CTest stream: 1,136/1,136 tests passed with none skipped; required-test set was checked before filtering.", "summary_coverage and summary_coverage_selftest validate block-style coverage with no human checkpoints.", "All twelve earlier plan_head_before/after windows are ancestors of the phase branch; 14-03 head fields are top-level and dependency descriptions match their source summaries."]

## Summary

total: 49
passed: 49
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps

[none]
