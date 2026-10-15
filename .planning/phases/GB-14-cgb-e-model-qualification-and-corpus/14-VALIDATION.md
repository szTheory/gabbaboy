---
phase: "14"
slug: "cgb-e-model-qualification-and-corpus"
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-10-15"
---

# Phase 14 — Validation Strategy

This is a planning contract, not a verification receipt. New behavior, fixtures and checks remain unimplemented. The planner completes the per-task map against its final plan IDs; execution records results. D-069 and context D-20 require an automated discriminator and a negative control for every deliverable.

## Test Infrastructure

| Property | Value |
|---|---|
| Framework | Existing C17 native tests, CTest and Python standard-library scripts |
| Config | `CMakePresets.json`, `tests/CMakeLists.txt`, `tests/expected-tests.txt` |
| Quick run command | `cmake --preset phase1 && cmake --build --preset phase1 && ctest --test-dir build -R '^(apu_.*|cgb_visibility_.*|summary_coverage)$' --output-on-failure --no-tests=error` |
| Full suite command | `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error` |
| Regression command | `bash tests/scripts/verify-dmg-baseline.sh` |
| Measured planning cost | Research selection: 33 tests in 2.09 s; eight AGE disposition tests in 2.89 s. Phase 13's historical 994-test run was 107 s. These are not future CI guarantees. |

## Sampling Rate

- After every implementation task: build and run its exact named positive/negative tests; assert required CTest membership before filtering.
- After each wave: run affected integration, inventory and shared clock-domain checks; run the frozen DMG baseline after shared core changes.
- At phase verification: full native suite, relevant sanitizer/fixture/consumer/package lanes and complete corpus receipt, reusing existing executions.
- Target focused feedback below 30 seconds excluding build/reproduction; measure new workloads and record a justified budget before increasing timeouts.
- An empty regex result, subset missing required names, stale receipt, changed expected-failure signature, timeout or unexpected pass cannot be green.

## Per-Task Verification Map

Final map for13 plans,31 tasks and11 waves. Each PLAN contains the complete root-relative command, exact required CTest membership, --no-tests=error where CTest runs, observable fails_when, positive twin and intended negative signal. New helpers/tests are created by their first consumer task. Dynamic SameSuite70 membership expands from14-SOURCE-COVERAGE.md using the exact naming rule in14-07-PLAN.md.

|Task|Wave|Requirement|Automated evidence|Negative discriminator|Threat refs|
|---|---|---|---|---|---|
|14-01-1|1|CGB-08|`cgb_pcm_tracer`, `cgb_pcm_tracer_control`, `cgb_visibility_matrix_dmg`, `cgb_visibility_matrix_compat`, `cgb_visibility_matrix_cgb`|Clean twin plus intended mismatch specified in task action|T-14-01, T-14-02|
|14-01-2|1|CGB-08|`cgb_pcm_channels`, `cgb_pcm_power_dac`, `cgb_pcm_readonly`, `cgb_pcm_host_invariance`, `cgb_pcm_controls`|Clean twin plus intended mismatch specified in task action|T-14-01, T-14-02|
|14-02-1|2|CGB-08|`cgb_ir_tracer`, `cgb_ir_controls`, `cgb_ir_modes`|Clean twin plus intended mismatch specified in task action|T-14-03, T-14-04|
|14-02-2|2|CGB-08|`cgb_ir_modes`, `cgb_ir_controls`, `cgb_tables_io`, `cgb_tables_io_mutated_doc`, `cgb_visibility_matrix_cgb`, `cgb_visibility_matrix_compat`, `cgb_visibility_cross_column_control`|Clean twin plus intended mismatch specified in task action|T-14-03, T-14-04|
|14-03-1|3|CGB-08|`cgb_apu_wave_latch`, `cgb_apu_wave_fetch`, `cgb_apu_wave_direct_ram_control`|Clean twin plus intended mismatch specified in task action|T-14-05, T-14-06|
|14-03-2|3|CGB-08|`cgb_apu_power`, `cgb_apu_off_writes`, `cgb_apu_wave_access`, `cgb_apu_trigger_length_sweep`, `cgb_apu_div_stop`, `cgb_apu_transition_controls`, `model_gates`|Clean twin plus intended mismatch specified in task action|T-14-05, T-14-06|
|14-04-1|4|CGB-08|`cgb_apu_partition_fetch`, `cgb_apu_partition_speed`, `cgb_apu_partition_controls`, `cgb_partition_snapshot_fidelity`, `cgb_hdma_partition_midbyte`|Clean twin plus intended mismatch specified in task action|T-14-07, T-14-08|
|14-04-2|4|CGB-08|`cgb_apu_lifecycle`, `cgb_apu_output_pressure`, `cgb_apu_hostile_seeds`, `cgb_apu_lifecycle_controls`, `cgb_hdma_lifecycle`, `cgb_hdma_competing_stalls`, `cgb_speed_identity_pin`|Clean twin plus intended mismatch specified in task action|T-14-07, T-14-08|
|14-05-1|1|CGB-10|`python3 -I tests/scripts/verify-cgb-corpus-inventory.py --selection-only && python3 -I tests/scripts/verify-cgb-corpus-inventory.py --self-test`|Clean twin plus intended mismatch specified in task action|T-14-09, T-14-10|
|14-05-2|1|CGB-10|`python3 -I tests/scripts/verify-cgb-corpus-inventory.py --selection-only && python3 -I tests/scripts/verify-cgb-corpus-inventory.py --self-test`|Clean twin plus intended mismatch specified in task action|T-14-09, T-14-10|
|14-06-1|5|CGB-08, CGB-10|`bash tests/scripts/reproduce-mooneye-cgb.sh --compare fixtures/mooneye-cgb && bash tests/scripts/test-reproduce-mooneye-cgb-guard.sh . && cmake --preset phase1 && cmake --build --preset phase1 && build/gabbaboy-runner --manifest fixtures/mooneye-cgb/manifest.json --case daa --profile cgb --receipt`|Clean twin plus intended mismatch specified in task action|T-14-11, T-14-12|
|14-06-2|5|CGB-08, CGB-10|`bash tests/scripts/reproduce-mooneye-cgb.sh --compare fixtures/mooneye-cgb && bash tests/scripts/test-reproduce-mooneye-cgb-guard.sh . && cmake --preset phase1 && cmake --build --preset phase1 && build/gabbaboy-runner --manifest fixtures/mooneye-cgb/manifest.json --suite --profile cgb --receipt`|Clean twin plus intended mismatch specified in task action|T-14-11, T-14-12|
|14-06-3|5|CGB-08, CGB-10|`cgb_corpus_mooneye_boot_regs_cgb`, `cgb_corpus_mooneye_boot_div_cgbABCDE`, `cgb_corpus_mooneye_boot_hwio_C`, `cgb_corpus_mooneye_unused_hwio_C`, `cgb_corpus_mooneye_daa`, `cgb_corpus_mooneye_div_write`, `cgb_corpus_mooneye_tim00`, `cgb_corpus_mooneye_tim00_div_trigger`, `cgb_corpus_mooneye_vblank_stat_intr_C`, `cgb_corpus_mooneye_controls`|Clean twin plus intended mismatch specified in task action|T-14-11, T-14-12|
|14-07-1|6|CGB-08, CGB-10|`cgb_samesuite_apu_tracer`, `cgb_samesuite_apu_tracer_controls`|Clean twin plus intended mismatch specified in task action|T-14-13, T-14-14|
|14-07-2|6|CGB-08, CGB-10|`cmake --preset phase1 && cmake --build --preset phase1 && build/tests/test_samesuite_apu --suite fixtures/samesuite/manifest.json --dispositions tests/external/cgb-apu-dispositions.json && bash tests/scripts/reproduce-samesuite.sh --self-check && bash tests/scripts/reproduce-samesuite.sh --self-test && bash tests/scripts/reproduce-samesuite.sh --compare-pinned`|Clean twin plus intended mismatch specified in task action|T-14-13, T-14-14|
|14-07-3|6|CGB-08, CGB-10|`cgb_samesuite_apu_membership`, `cgb_samesuite_apu_controls`, `cgb_samesuite_apu_tracer`, `cgb_samesuite_apu_channel_1_channel_1_align`, `cgb_samesuite_apu_channel_1_channel_1_align_cpu`, `cgb_samesuite_apu_channel_1_channel_1_delay`, `cgb_samesuite_apu_channel_1_channel_1_duty`, `cgb_samesuite_apu_channel_1_channel_1_duty_delay`, `cgb_samesuite_apu_channel_1_channel_1_extra_length_clocking_cgb0B`, `cgb_samesuite_apu_channel_1_channel_1_freq_change`, `cgb_samesuite_apu_channel_1_channel_1_freq_change_timing_A`, `cgb_samesuite_apu_channel_1_channel_1_freq_change_timing_cgb0BC`, `cgb_samesuite_apu_channel_1_channel_1_freq_change_timing_cgbDE`, `cgb_samesuite_apu_channel_1_channel_1_nrx2_glitch`, `cgb_samesuite_apu_channel_1_channel_1_nrx2_speed_change`, `cgb_samesuite_apu_channel_1_channel_1_restart`, `cgb_samesuite_apu_channel_1_channel_1_restart_nrx2_glitch`, `cgb_samesuite_apu_channel_1_channel_1_stop_div`, `cgb_samesuite_apu_channel_1_channel_1_stop_restart`, `cgb_samesuite_apu_channel_1_channel_1_sweep`, `cgb_samesuite_apu_channel_1_channel_1_sweep_restart`, `cgb_samesuite_apu_channel_1_channel_1_sweep_restart_2`, `cgb_samesuite_apu_channel_1_channel_1_volume`, `cgb_samesuite_apu_channel_1_channel_1_volume_div`, `cgb_samesuite_apu_channel_2_channel_2_align`, `cgb_samesuite_apu_channel_2_channel_2_align_cpu`, `cgb_samesuite_apu_channel_2_channel_2_delay`, `cgb_samesuite_apu_channel_2_channel_2_duty`, `cgb_samesuite_apu_channel_2_channel_2_duty_delay`, `cgb_samesuite_apu_channel_2_channel_2_extra_length_clocking_cgb0B`, `cgb_samesuite_apu_channel_2_channel_2_freq_change`, `cgb_samesuite_apu_channel_2_channel_2_nrx2_glitch`, `cgb_samesuite_apu_channel_2_channel_2_nrx2_speed_change`, `cgb_samesuite_apu_channel_2_channel_2_restart`, `cgb_samesuite_apu_channel_2_channel_2_restart_nrx2_glitch`, `cgb_samesuite_apu_channel_2_channel_2_stop_div`, `cgb_samesuite_apu_channel_2_channel_2_stop_restart`, `cgb_samesuite_apu_channel_2_channel_2_volume`, `cgb_samesuite_apu_channel_2_channel_2_volume_div`, `cgb_samesuite_apu_channel_3_channel_3_and_glitch`, `cgb_samesuite_apu_channel_3_channel_3_delay`, `cgb_samesuite_apu_channel_3_channel_3_extra_length_clocking_cgb0`, `cgb_samesuite_apu_channel_3_channel_3_extra_length_clocking_cgbB`, `cgb_samesuite_apu_channel_3_channel_3_first_sample`, `cgb_samesuite_apu_channel_3_channel_3_freq_change_delay`, `cgb_samesuite_apu_channel_3_channel_3_restart_delay`, `cgb_samesuite_apu_channel_3_channel_3_restart_during_delay`, `cgb_samesuite_apu_channel_3_channel_3_restart_stop_delay`, `cgb_samesuite_apu_channel_3_channel_3_shift_delay`, `cgb_samesuite_apu_channel_3_channel_3_shift_skip_delay`, `cgb_samesuite_apu_channel_3_channel_3_stop_delay`, `cgb_samesuite_apu_channel_3_channel_3_stop_div`, `cgb_samesuite_apu_channel_3_channel_3_wave_ram_dac_on_rw`, `cgb_samesuite_apu_channel_3_channel_3_wave_ram_locked_write`, `cgb_samesuite_apu_channel_3_channel_3_wave_ram_sync`, `cgb_samesuite_apu_channel_4_channel_4_align`, `cgb_samesuite_apu_channel_4_channel_4_delay`, `cgb_samesuite_apu_channel_4_channel_4_equivalent_frequencies`, `cgb_samesuite_apu_channel_4_channel_4_extra_length_clocking_cgb0B`, `cgb_samesuite_apu_channel_4_channel_4_freq_change`, `cgb_samesuite_apu_channel_4_channel_4_frequency_alignment`, `cgb_samesuite_apu_channel_4_channel_4_lfsr`, `cgb_samesuite_apu_channel_4_channel_4_lfsr15`, `cgb_samesuite_apu_channel_4_channel_4_lfsr_15_7`, `cgb_samesuite_apu_channel_4_channel_4_lfsr_7_15`, `cgb_samesuite_apu_channel_4_channel_4_lfsr_restart`, `cgb_samesuite_apu_channel_4_channel_4_lfsr_restart_fast`, `cgb_samesuite_apu_channel_4_channel_4_volume_div`, `cgb_samesuite_apu_div_trigger_volume_10`, `cgb_samesuite_apu_div_write_trigger`, `cgb_samesuite_apu_div_write_trigger_10`, `cgb_samesuite_apu_div_write_trigger_volume`, `cgb_samesuite_apu_div_write_trigger_volume_10`|Clean twin plus intended mismatch specified in task action|T-14-13, T-14-14|
|14-08-1|2|CGB-10|`bash tests/scripts/reproduce-age.sh --self-check && bash tests/scripts/test-reproduce-age.sh compare-tampered && bash tests/scripts/test-reproduce-age.sh selfcheck-tampered && bash tests/scripts/reproduce-age.sh --compare`|Clean twin plus intended mismatch specified in task action|T-14-15, T-14-16|
|14-08-2|2|CGB-10|`bash tests/scripts/reproduce-age.sh --self-check && bash tests/scripts/test-reproduce-age.sh compare-tampered && bash tests/scripts/test-reproduce-age.sh selfcheck-tampered && bash tests/scripts/reproduce-age.sh --compare`|Clean twin plus intended mismatch specified in task action|T-14-15, T-14-16|
|14-09-1|7|CGB-08, CGB-10|`cgb_age_m3_tracer`, `cgb_age_m3_pixel_controls`|Clean twin plus intended mismatch specified in task action|T-14-17, T-14-18|
|14-09-2|7|CGB-08, CGB-10|`cgb_age_m3_m3_bg_lcdc_cgbBCE`, `cgb_age_m3_m3_bg_lcdc_nocgb_ncmBCE`, `cgb_age_m3_m3_bg_lcdc_ds_cgbBCE`, `cgb_age_m3_m3_bg_scx_cgbBCE`, `cgb_age_m3_m3_bg_scx_nocgb_ncmBCE`, `cgb_age_m3_m3_bg_scx_ds_cgbBCE`, `cgb_age_m3_membership`, `cgb_age_m3_pixel_controls`|Clean twin plus intended mismatch specified in task action|T-14-17, T-14-18|
|14-10-1|8|CGB-08, CGB-10|`age_stat_mode_cgbE`, `age_stat_mode_ds_cgbBCE`, `age_stat_mode_sprites_dmgC_cgbBCE`, `age_stat_mode_sprites_ds_cgbBCE`, `age_stat_mode_window_cgbBCE`, `age_stat_mode_window_ds_cgbBCE`, `age_spsw_mode0_cgbBCE`, `age_spsw_ch2_lc_delay_cgbBCE`, `cgb_age_m3_membership`, `cgb_speed_dispositions`|Clean twin plus intended mismatch specified in task action|T-14-19, T-14-20|
|14-10-2|8|CGB-08, CGB-10|`cgb_age_assertion_identity`, `cgb_age_assertion_controls`, `cgb_research14_dispositions`, `cgb_research14_dispositions_controls`, `model_gates`, `cgb_speed_dispositions`, `cgb_hdma_dispositions`|Clean twin plus intended mismatch specified in task action|T-14-19, T-14-20|
|14-11-1|9|CGB-10|`cgb_corpus_report_tracer`, `cgb_corpus_report_tracer_controls`|Clean twin plus intended mismatch specified in task action|T-14-21, T-14-22|
|14-11-2|9|CGB-10|`cmake --preset phase1 && cmake --build --preset phase1 && python3 -I tests/scripts/verify-cgb-corpus-report.py --run --build-dir build --receipt build/cgb-corpus-receipt.json && python3 -I tests/scripts/verify-cgb-corpus-report.py --self-test`|Clean twin plus intended mismatch specified in task action|T-14-21, T-14-22|
|14-11-3|9|CGB-10|`cgb_corpus_report_contract`, `cgb_corpus_report_controls`, `cgb_corpus_report_tracer`, `cgb_corpus_report_tracer_controls`|Clean twin plus intended mismatch specified in task action|T-14-21, T-14-22|
|14-12-1|10|CGB-08, CGB-10|`cgb_corpus_inventory`, `cgb_corpus_inventory_controls`, `cgb_corpus_ci_contract`, `cgb_corpus_report_contract`, `cgb_corpus_report_controls`, `summary_coverage`|Clean twin plus intended mismatch specified in task action|T-14-23, T-14-24|
|14-12-2|10|CGB-08, CGB-10|`python3 -I tests/scripts/verify-cgb-corpus-inventory.py --ci-contract && python3 -I tests/scripts/verify-cgb-corpus-inventory.py --self-test && bash tests/scripts/reproduce-age.sh --self-check && bash tests/scripts/test-reproduce-age.sh compare-tampered && bash tests/scripts/reproduce-samesuite.sh --self-check && bash tests/scripts/reproduce-samesuite.sh --self-test`|Clean twin plus intended mismatch specified in task action|T-14-23, T-14-24|
|14-12-3|10|CGB-08, CGB-10|`installed_consumer_c`, `installed_consumer_cpp`, `preview_package_smoke`, `cgb_consumer_symbol_coverage`, `cgb_corpus_not_installed`, `cgb_corpus_not_installed_controls`|Clean twin plus intended mismatch specified in task action|T-14-23, T-14-24|
|14-13-1|11|CGB-08, CGB-10|`python3 -I tests/scripts/verify-cgb-corpus-claims.py && python3 -I tests/scripts/verify-cgb-corpus-claims.py --self-test`|Clean twin plus intended mismatch specified in task action|T-14-25, T-14-26|
|14-13-2|11|CGB-08, CGB-10|`python3 -I tests/scripts/verify-cgb-corpus-claims.py && python3 -I tests/scripts/verify-cgb-corpus-claims.py --self-test`|Clean twin plus intended mismatch specified in task action|T-14-25, T-14-26|
|14-13-3|11|CGB-08, CGB-10|`cgb_corpus_claims`, `cgb_corpus_claims_controls`, `summary_coverage`, `summary_coverage_selftest`, `model_gates`, `cgb_corpus_inventory`, `cgb_corpus_report_contract`|Clean twin plus intended mismatch specified in task action|T-14-25, T-14-26|

Focused tests target <30seconds excluding build/reproduction; measure new guest/parser workload and timeout headroom during execution. Full native verification remains `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error`. Run frozen DMG baseline after shared core changes. Existing installed/reproduction commands are inherited; no runtime/GSD dependency is added to CI.

Threat references above retain unique T-14-01–26. The shared supply-chain threat T-14-SC is defined once in14-05-PLAN.md and referenced explicitly in every other plan's threat model; it requires existing source/tool pins and hashes and rejects introduced unaudited packages, with no package install planned. All five research questions are RESOLVED for planning in14-RESEARCH.md, with exact task links; their automated implementation/admission checks remain pending execution. Physical CGB-E stays an explicit out-of-scope limitation and adds no human checkpoint.

## Wave 0 Requirements

No new test framework or dependency is required. Each tracer task creates its missing tests before expansion. Plans must order the guest APU tests, new fixture admission and executable oracles, independent source inventory validator, receipt parser and AGE image checks before their consumers. Keep source inventory validation separate from result parsing. Do not insert a horizontal infrastructure-only phase.

## Manual-Only Verifications

All in-scope phase behaviors have automated verification. No routine human UAT is required. Physical CGB-E, analog/perceptual evidence and Phase 15 game/release work remain outside this phase; they are limitations, not invented acceptance checkpoints.

## Evidence and Coverage Format

Every plan SUMMARY uses block-style `coverage` records with `id`, `description`, `human_judgment: false` and block `verification` items containing `kind`, `ref`, `status: pass`. Kinds are `unit`, `integration`, `e2e`, `automated_ui` or `other`. `summary_coverage` must reject malformed or unverified entries. No flow maps, inline comments or `ctest` kind.

## Validation Sign-Off

- [ ] Final task map matches all plans and unique threat IDs.
- [ ] Every task has runnable automated verification and an observable failure signal.
- [ ] Every deliverable has a passing twin and intended negative control.
- [ ] Missing checks are created before first use; no watch-mode commands.
- [ ] Runtime and exact required membership are measured during execution.
- [ ] Phase evidence is fresh; `nyquist_compliant` is set only by validation.

**Approval:** Planning contract pending independent plan check; implementation verification pending.
