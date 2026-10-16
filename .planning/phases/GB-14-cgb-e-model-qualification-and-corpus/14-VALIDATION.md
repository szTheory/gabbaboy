---
phase: "14"
slug: "cgb-e-model-qualification-and-corpus"
status: validated
nyquist_compliant: true
wave_0_complete: true
created: "2026-10-15"
validated_on: "2026-10-15"
evidence_revision: "f8260549009f3150dc82de801373f40de3a02aa0"
---

# Phase 14 — Validation Strategy and Audit

The 31-task map below is reconciled to registered CTests, actual negative controls, the Wave 11 JUnit report and its nonce-bound corpus receipt. Every task has an executed positive behavior check and an executed negative discriminator. No new tests were needed: existing tests make the disputed behaviors observable, and the source-identical Wave 11 stream passed every registered CTest. COVERED means the behavior and its rejection control have automated evidence; it does not mean every oracle observation matched. Expected failures and unresolved hardware/model questions remain separately identified.

## Test Infrastructure

| Property | Value |
|---|---|
| Framework | C17 native tests, CTest and Python standard-library scripts |
| Configure/build | cmake --preset phase1 && cmake --build --preset phase1 |
| Registered inventory | tests/expected-tests.txt; summary_coverage validates plan SUMMARY records |
| Fresh full-stream command | python3 -I tests/scripts/verify-cgb-corpus-report.py --begin-run --build-dir build --receipt build/cgb-corpus-receipt.json && ctest --test-dir build -T Test --no-compress-output --test-output-size-passed 16777216 --parallel 2 --output-on-failure --no-tests=error --output-junit cgb-corpus-ctest-82996a6a7c9cdd2d438af465fec592d1.xml && python3 -I tests/scripts/verify-cgb-corpus-report.py --from-ctest --build-dir build --receipt build/cgb-corpus-receipt.json |
| Regression in the full stream | CTest dmg_baseline; Wave 11 also checked required-test inventory and allowlisted artifact privacy |
| Focused audit rerun | ctest --test-dir build -R '^(cgb_pcm_channels|cgb_ir_modes|cgb_apu_wave_latch|cgb_apu_transition_controls|cgb_apu_lifecycle_controls|cgb_apu_hostile_seeds|cgb_apu_partition_controls|cgb_samesuite_apu_controls|cgb_corpus_inventory_controls|cgb_corpus_report_controls|cgb_corpus_artifact_privacy_controls|cgb_corpus_claims_controls|cgb_age_m3_pixel_controls|cgb_age_assertion_controls|cgb_research14_dispositions_controls|summary_coverage_selftest|preview_package_smoke|cgb_corpus_ci_contract)$' --output-on-failure --no-tests=error |

The explicit --test-dir build -T Test form is required for the dashboard stream. Do not combine the test preset with dashboard submission: an earlier attempt wrote stale dashboard XML outside the build tree and was correctly rejected. Wave 11 used a fresh begin-run nonce and JUnit name, then rebuilt the receipt from that run. The accepted receipt is tied to source f8260549009f3150dc82de801373f40de3a02aa0; later metadata commits do not change that evidence identity.

Wave 11 actually ran 1,136 CTests: 1,136 passed, zero failures, errors or skips. JUnit SHA-256: ab6b02a9b515499bcd406c9dd1311757c48143e24bf7dca7c16e5a8dbd5496b0. The receipt SHA-256 is 2be80587e04fb7a1eb19568a4415a28e2df8d51fe49966c6aaa952d77d5f307a, with run ID 53a7b4be86a2bee9500a2ef55479bbef7a0794f17255663824451a01c16239ca, model CGB-CPU-E selected software model, and hardware_qualified=false. Actual counters: 107/107 required cases admitted, applicable, attempted and completed; 25 observed passes and 82 exact matched expected failures; 2,845/4,959 passing assertion rows; 18,208/138,240 mismatching image pixels. The CTest log contains 108 selected CTests (107 inventory-bound case tests plus the SameSuite aggregate); that is distinct from the 107 corpus-case denominator. The audit parsed the receipt, JUnit and inventory bytes directly and confirmed the receipt core revision and inventory digest.

The focused audit rerun passed 18/18 checks in 3.14 seconds. It includes live APU/IR behavior, CGB corpus inventory/report/CI/privacy/claims controls, AGE assertions/pixels, all-31 research-gate controls, summary schema rejection and a package smoke test. The same 18 test names are present and passing in the Wave 11 JUnit.

## Per-Task Verification Map

All rows were found in the Wave 11 JUnit and have no failure, error or skip element. Test names below are registered names from tests/CMakeLists.txt and tests/expected-tests.txt; controls are actual negative tests, not generic task labels.

| Task | Requirement | Positive behavioral evidence | Negative discriminator executed | Audit status |
|---|---|---|---|---|
| 14-01-1 | CGB-08 | cgb_pcm_tracer; cgb_visibility_matrix_dmg, cgb_visibility_matrix_compat, cgb_visibility_matrix_cgb | cgb_pcm_tracer_control swaps PCM nibble result (expected 0x0f, mutant 0xf0); cgb_visibility_cross_column_control rejects cross-profile policy leakage | COVERED |
| 14-01-2 | CGB-08 | cgb_pcm_channels, cgb_pcm_power_dac, cgb_pcm_readonly, cgb_pcm_host_invariance | cgb_pcm_routing_control detects muted output changing from 0x0f to 0x00; cgb_pcm_writable_control detects read-only PCM changing from 0x0f to 0xa5 | COVERED |
| 14-02-1 | CGB-08 | cgb_ir_tracer, cgb_ir_modes | cgb_ir_controls rejects FF56 reset ($00 vs $01) and failed-load state ($C1 vs $00) | COVERED |
| 14-02-2 | CGB-08 | cgb_tables_io, cgb_visibility_matrix_cgb, cgb_visibility_matrix_compat | cgb_tables_io_mutated_doc and cgb_visibility_cross_column_control reject changed register policy, including FF75 mask and compatibility FF74 decode mutations | COVERED |
| 14-03-1 | CGB-08 | cgb_apu_wave_latch, cgb_apu_wave_fetch | cgb_apu_wave_direct_ram_control detects direct Wave RAM reads bypassing fetched-sample latch (expected 0x07, mutant 0x0a) | COVERED |
| 14-03-2 | CGB-08 | cgb_apu_power, cgb_apu_off_writes, cgb_apu_wave_access, cgb_apu_trigger_length_sweep, cgb_apu_div_stop | cgb_apu_transition_controls exercises omitted transition/clock edges; cgb_speed_dispositions_mutated rejects altered model dispositions. DMG length retention remains UNKNOWN, not a pass | COVERED |
| 14-04-1 | CGB-08 | cgb_apu_partition_fetch, cgb_apu_partition_speed, cgb_partition_snapshot_fidelity, cgb_hdma_partition_midbyte | cgb_apu_partition_controls detects lost/duplicated fetch remainder; cgb_partition_mutant_m16 plus its control detects hostile in-stall interrupt mutation | COVERED |
| 14-04-2 | CGB-08 | cgb_apu_lifecycle, cgb_apu_output_pressure, cgb_apu_hostile_seeds, cgb_hdma_lifecycle, cgb_hdma_competing_stalls, cgb_speed_identity_pin | cgb_apu_lifecycle_controls detects reset leakage and failed-load state leakage; bounded hostile seeds and output-pressure cases execute in the full suite | COVERED |
| 14-05-1 | CGB-10 | cgb_corpus_inventory_selection runs selection-only; cgb_corpus_inventory_selftest checks inventory behavior | cgb_corpus_inventory_controls / inventory self-test reject narrowed, empty or altered candidate/output selections | COVERED |
| 14-05-2 | CGB-10 | cgb_corpus_inventory runs the actual --bindings mode and binds exactly 107 required CTests | cgb_corpus_inventory_controls, cgb_mooneye_unknown_manifest and source admission controls reject bad pins, incomplete metadata and unsupported/rights-invalid inputs. Static --complete deliberately rejects non-terminal Magen bg_oam_priority; runtime completion is receipt-based | COVERED |
| 14-06-1 | CGB-08, CGB-10 | cgb_mooneye_fixture_digest, cgb_mooneye_inventory; nine pinned CGB fixtures are used by corpus tests | cgb_corpus_mooneye_controls and cgb_mooneye_unknown_manifest reject digest/manifest tampering and preserve exact failure signatures | COVERED |
| 14-06-2 | CGB-08, CGB-10 | cgb_mooneye_required_suite, cgb_mooneye_observe_not_applicable, exact per-case runner tests | cgb_corpus_mooneye_controls rejects stale unsupported dispositions, altered callbacks and false xfails on a passing guest; author expect=pass remains separate from observed xfails | COVERED |
| 14-06-3 | CGB-08, CGB-10 | cgb_corpus_mooneye_boot_regs_cgb, cgb_corpus_mooneye_boot_div_cgbABCDE, cgb_corpus_mooneye_boot_hwio_C, cgb_corpus_mooneye_unused_hwio_C, cgb_corpus_mooneye_daa, cgb_corpus_mooneye_div_write, cgb_corpus_mooneye_tim00, cgb_corpus_mooneye_tim00_div_trigger and cgb_corpus_mooneye_vblank_stat_intr_C | cgb_corpus_mooneye_controls checks exact callback/result signatures and catches altered or misclassified outcomes | COVERED |
| 14-07-1 | CGB-08, CGB-10 | cgb_samesuite_apu_tracer observes a public-API CH3 guest | cgb_samesuite_apu_tracer_controls detects tracer/signature mutations | COVERED |
| 14-07-2 | CGB-08, CGB-10 | cgb_samesuite_apu_suite emits one bounded suite result for the frozen manifest/disposition set; receipt records 70 SameSuite members | cgb_samesuite_apu_controls rejects all-xfail/empty rosters and altered signatures/counts; samesuite_repro_selfcheck checks reproduction controls | COVERED |
| 14-07-3 | CGB-08, CGB-10 | cgb_samesuite_apu_membership and the following 70 registered case CTests: cgb_samesuite_apu_channel_1_channel_1_align; cgb_samesuite_apu_channel_1_channel_1_align_cpu; cgb_samesuite_apu_channel_1_channel_1_delay; cgb_samesuite_apu_channel_1_channel_1_duty; cgb_samesuite_apu_channel_1_channel_1_duty_delay; cgb_samesuite_apu_channel_1_channel_1_extra_length_clocking_cgb0B; cgb_samesuite_apu_channel_1_channel_1_freq_change; cgb_samesuite_apu_channel_1_channel_1_freq_change_timing_A; cgb_samesuite_apu_channel_1_channel_1_freq_change_timing_cgb0BC; cgb_samesuite_apu_channel_1_channel_1_freq_change_timing_cgbDE; cgb_samesuite_apu_channel_1_channel_1_nrx2_glitch; cgb_samesuite_apu_channel_1_channel_1_nrx2_speed_change; cgb_samesuite_apu_channel_1_channel_1_restart; cgb_samesuite_apu_channel_1_channel_1_restart_nrx2_glitch; cgb_samesuite_apu_channel_1_channel_1_stop_div; cgb_samesuite_apu_channel_1_channel_1_stop_restart; cgb_samesuite_apu_channel_1_channel_1_sweep; cgb_samesuite_apu_channel_1_channel_1_sweep_restart; cgb_samesuite_apu_channel_1_channel_1_sweep_restart_2; cgb_samesuite_apu_channel_1_channel_1_volume; cgb_samesuite_apu_channel_1_channel_1_volume_div; cgb_samesuite_apu_channel_2_channel_2_align; cgb_samesuite_apu_channel_2_channel_2_align_cpu; cgb_samesuite_apu_channel_2_channel_2_delay; cgb_samesuite_apu_channel_2_channel_2_duty; cgb_samesuite_apu_channel_2_channel_2_duty_delay; cgb_samesuite_apu_channel_2_channel_2_extra_length_clocking_cgb0B; cgb_samesuite_apu_channel_2_channel_2_freq_change; cgb_samesuite_apu_channel_2_channel_2_nrx2_glitch; cgb_samesuite_apu_channel_2_channel_2_nrx2_speed_change; cgb_samesuite_apu_channel_2_channel_2_restart; cgb_samesuite_apu_channel_2_channel_2_restart_nrx2_glitch; cgb_samesuite_apu_channel_2_channel_2_stop_div; cgb_samesuite_apu_channel_2_channel_2_stop_restart; cgb_samesuite_apu_channel_2_channel_2_volume; cgb_samesuite_apu_channel_2_channel_2_volume_div; cgb_samesuite_apu_channel_3_channel_3_and_glitch; cgb_samesuite_apu_channel_3_channel_3_delay; cgb_samesuite_apu_channel_3_channel_3_extra_length_clocking_cgb0; cgb_samesuite_apu_channel_3_channel_3_extra_length_clocking_cgbB; cgb_samesuite_apu_channel_3_channel_3_first_sample; cgb_samesuite_apu_channel_3_channel_3_freq_change_delay; cgb_samesuite_apu_channel_3_channel_3_restart_delay; cgb_samesuite_apu_channel_3_channel_3_restart_during_delay; cgb_samesuite_apu_channel_3_channel_3_restart_stop_delay; cgb_samesuite_apu_channel_3_channel_3_shift_delay; cgb_samesuite_apu_channel_3_channel_3_shift_skip_delay; cgb_samesuite_apu_channel_3_channel_3_stop_delay; cgb_samesuite_apu_channel_3_channel_3_stop_div; cgb_samesuite_apu_channel_3_channel_3_wave_ram_dac_on_rw; cgb_samesuite_apu_channel_3_channel_3_wave_ram_locked_write; cgb_samesuite_apu_channel_3_channel_3_wave_ram_sync; cgb_samesuite_apu_channel_4_channel_4_align; cgb_samesuite_apu_channel_4_channel_4_delay; cgb_samesuite_apu_channel_4_channel_4_equivalent_frequencies; cgb_samesuite_apu_channel_4_channel_4_extra_length_clocking_cgb0B; cgb_samesuite_apu_channel_4_channel_4_freq_change; cgb_samesuite_apu_channel_4_channel_4_frequency_alignment; cgb_samesuite_apu_channel_4_channel_4_lfsr; cgb_samesuite_apu_channel_4_channel_4_lfsr15; cgb_samesuite_apu_channel_4_channel_4_lfsr_15_7; cgb_samesuite_apu_channel_4_channel_4_lfsr_7_15; cgb_samesuite_apu_channel_4_channel_4_lfsr_restart; cgb_samesuite_apu_channel_4_channel_4_lfsr_restart_fast; cgb_samesuite_apu_channel_4_channel_4_volume_div; cgb_samesuite_apu_div_trigger_volume_10; cgb_samesuite_apu_div_write_trigger; cgb_samesuite_apu_div_write_trigger_10; cgb_samesuite_apu_div_write_trigger_volume; cgb_samesuite_apu_div_write_trigger_volume_10. Configure-time membership requires exactly 70 rows | cgb_samesuite_apu_controls rejects roster changes, missing cases and xfail inflation; receipt has exact case IDs and a separate 70-case suite denominator | COVERED |
| 14-08-1 | CGB-10 | age_repro_selfcheck, age_repro_compare_tampered and AGE pinned reproduction | age_repro_compare_tampered rejects a changed rebuilt output | COVERED |
| 14-08-2 | CGB-10 | age_fixture_digest, age_repro_selfcheck and same-source/reference AGE rebuild comparison | age_repro_selfcheck_tampered and age_repro_compare_tampered reject altered inputs and outputs | COVERED |
| 14-09-1 | CGB-08, CGB-10 | cgb_age_m3_tracer captures a complete public-API frame against its pinned PNG reference | cgb_age_m3_pixel_controls rejects wrong frame size, blank/unchanged output and changed reference pixels; cgb_age_m3_early_frame_control rejects an incomplete frame | COVERED |
| 14-09-2 | CGB-08, CGB-10 | cgb_age_m3_m3_bg_lcdc_cgbBCE, cgb_age_m3_m3_bg_lcdc_nocgb_ncmBCE, cgb_age_m3_m3_bg_lcdc_ds_cgbBCE, cgb_age_m3_m3_bg_scx_cgbBCE, cgb_age_m3_m3_bg_scx_nocgb_ncmBCE, cgb_age_m3_m3_bg_scx_ds_cgbBCE; cgb_age_m3_membership requires all six | cgb_age_m3_pixel_controls and cgb_age_m3_early_frame_control; all six observations were recorded, with 0/6 exact image matches and 18,208/138,240 pixel mismatches in the receipt | COVERED |
| 14-10-1 | CGB-08, CGB-10 | Eight inherited AGE row tests: CGB-E/DS STAT, sprite, window, mode-0 and CH2 length-delay cases; assertion contract reports 13 cases / 142 rows | age_stat_mode_cgbE_phase14_controls, cgb_age_assertion_controls and cgb_age_assertion_identity detect altered IDs, omitted rows and changed observed values | COVERED |
| 14-10-2 | CGB-08, CGB-10 | cgb_research14_dispositions checks all 31 research gates; model_gates binds source tags/docs; AGE identity binds assertions | cgb_research14_dispositions_controls, cgb_age_assertion_controls and model-gate mutation tests reject omitted/renamed/misclassified rows. Actual gate ledger: 4 resolved, 27 owned UNKNOWN limitations | COVERED |
| 14-11-1 | CGB-10 | cgb_corpus_report_tracer exercises a single case through the report adapter | cgb_corpus_report_tracer_controls rejects altered case/receipt inputs | COVERED |
| 14-11-2 | CGB-10 | Wave 11 --begin-run → explicit CTest dashboard stream → --from-ctest completed a nonce-bound 107-case receipt | cgb_corpus_report_controls rejects missing, duplicate, stale, truncated, mismatched and unbounded receipt inputs; receipt/JUnit hashes and run ID were cross-checked | COVERED |
| 14-11-3 | CGB-10 | cgb_corpus_report_contract, cgb_corpus_ci_contract and cgb_corpus_report_tracer; Wave 11 proves the checked-in CI command and live exact stream | cgb_corpus_report_controls and cgb_corpus_ci_contract reject a changed invocation or invalid report accounting | COVERED |
| 14-12-1 | CGB-08, CGB-10 | cgb_corpus_inventory, cgb_corpus_ci_contract, cgb_corpus_report_contract, summary_coverage | cgb_corpus_inventory_controls, cgb_corpus_report_controls and summary_coverage_selftest reject changed membership, broken accounting and malformed/unverified coverage | COVERED |
| 14-12-2 | CGB-08, CGB-10 | AGE and SameSuite pinned-rebuild checks; age_repro_selfcheck, samesuite_repro_selfcheck | age_repro_selfcheck_tampered, age_repro_compare_tampered and cgb_samesuite_apu_controls reject modified fixture bytes or outputs | COVERED |
| 14-12-3 | CGB-08, CGB-10 | installed_consumer_c, installed_consumer_cpp, preview_package_smoke, cgb_consumer_symbol_coverage | cgb_consumer_symbol_coverage_selftest and cgb_corpus_not_installed_controls reject missing/extra exported surfaces or corpus leakage into packages | COVERED |
| 14-13-1 | CGB-08, CGB-10 | cgb_corpus_claims checks consumer-facing semantic claims against evidence and dispositions | cgb_corpus_claims_controls rejects invented passes, wrong mode cells, xfail-inflated totals and overclaimed hardware/analog behavior | COVERED |
| 14-13-2 | CGB-08, CGB-10 | cgb_corpus_artifact_privacy_controls, cgb_corpus_red_evidence_privacy and allowlisted artifact checks from Wave 11 | Synthetic private-path/secret controls prove rejection. The original private-history RED input was sanitized and is not reproducible from public history; that historical failure is retained as a deviation, not claimed as a current rerun | COVERED |
| 14-13-3 | CGB-08, CGB-10 | cgb_corpus_claims, cgb_corpus_inventory, cgb_corpus_report_contract and summary_coverage verify durable evidence and source links | cgb_corpus_claims_controls, cgb_corpus_inventory_controls, cgb_research14_dispositions_controls and summary_coverage_selftest reject stale claims, missing gate rows and malformed evidence | COVERED |

## Evidence and Interpretation

- Receipt case binding uses the inventory's 107 exact CTest bindings plus the nonce-specific Test.xml/JUnit artifacts. Static --complete is deliberately not a runtime completion check: it rejects Magen bg_oam_priority because that row is non-terminal in the static inventory. Runtime completion is --bindings plus the fresh receipt built from --begin-run / --from-ctest.
- The receipt reports author expectations separately from current observations. Required CGB Mooneye failures and 62 SameSuite xfails remain failures/xfails with named signatures; they were not counted as passes. AGE output remains a measurement: none of six full-frame images matched exactly. This audit proves the measurement and its controls ran, not hardware equivalence or complete visual conformance.
- The 31 research gates are fully owned by the disposition ledger and its controls. Four are resolved; 27 remain explicitly UNKNOWN/limited. In particular, DMG length retention (GATE-15/34), physical CGB-E, analog audio/perceptual quality and a real IR peer are not asserted by software tests. Phase 15 acceptance remains outside Phase 14.
- The Wave 11 test stream is source-bound to f826054, not the later metadata HEAD. The working tree's separate CMake whitespace and owner metadata edits were not staged or included in this audit commit.
- Task 14-12-3 has no pre-implementation RED record. No TDD history was fabricated. Synthetic privacy controls cover current sanitization behavior, while the sanitized historical private-input failure remains explicitly non-reproducible.

## Manual-Only Verifications

None for this phase's automated acceptance. Physical CGB-E measurements, analog/perceptual audio, an external IR peer and Phase 15 game/release acceptance are explicit scope limitations, not manual checkpoints or evidence claimed here.

## Validation Sign-Off

- [x] Final map includes all 13 plans, 31 tasks and 11 waves.
- [x] Every task maps to actual positive behavior evidence and a concrete executed negative control.
- [x] Full Wave 11 JUnit and receipt are fresh, nonce-bound, source-bound and free of test errors/skips.
- [x] Receipt outcomes, exact expected failures and mismatching AGE pixels are reported as observed.
- [x] No implementation files were modified; no new tests were needed; focused follow-up passed 18/18.
- [x] No routine human UAT is required. Out-of-scope hardware/analog/IR/Phase 15 evidence remains excluded.

Approval: Nyquist validation is complete for Phase 14 deliverables. Phase closure and requirement-status updates remain with the parent workflow.

## Validation Audit 2026-10-16

| Metric | Count |
|---|---|
| Gaps found | 31 |
| Resolved | 31 |
| Escalated | 0 |
