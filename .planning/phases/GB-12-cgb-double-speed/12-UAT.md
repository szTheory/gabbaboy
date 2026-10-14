---
status: complete
phase: GB-12-cgb-double-speed
source: 12-01-SUMMARY.md, 12-02-SUMMARY.md, 12-03-SUMMARY.md, 12-04-SUMMARY.md, 12-05-SUMMARY.md, 12-06-SUMMARY.md, 12-07-SUMMARY.md, 12-08-SUMMARY.md, 12-09-SUMMARY.md, 12-10-SUMMARY.md, 12-11-SUMMARY.md, 12-12-SUMMARY.md, 12-13-SUMMARY.md, 12-14-SUMMARY.md, 12-15-SUMMARY.md, 12-16-SUMMARY.md, 12-17-SUMMARY.md, 12-18-SUMMARY.md, 12-19-SUMMARY.md
started: 2026-10-14T14:33:09.590009+00:00
updated: 2026-10-14T14:49:29.224Z
---

## Current Test

[testing complete]

## Tests

All 73 structured SUMMARY coverage entries across 19 plans auto-pass in OpenGSD 1.16.0 (`uat.classify-coverage`): zero `present` entries and zero errors. D-069 and the renewed owner directive authorize automated closure with zero human checkpoints; no confirmation-only checkpoint is added.

Fresh evidence at execution head `da98d56ef8fadadf34ae951b337dcdecce495936`: configure and build succeeded; `CTEST_PARALLEL_LEVEL=8 ctest --preset phase1 --output-on-failure --no-tests=error` passed 898/898 in 107.00 seconds. The existing negative controls ran with that inventory. The only subsequent SUMMARY change corrects plan 12-04’s full `plan_head_after` to the actual `ec5dc8a28daf54a722f4da9b036c5fa48690bc6e`; its two task commits remain ancestors. All 19 bounded commit windows now match their measured claims.

Exact-head PR-event hosted evidence (fresh readback): [CI 38569486172](https://github.com/szTheory/gabbaboy/actions/runs/38569486172), [fixture reproduction 38569486169](https://github.com/szTheory/gabbaboy/actions/runs/38569486169), and [package smoke 38569486126](https://github.com/szTheory/gabbaboy/actions/runs/38569486126), all 19 jobs successful at `da98d56ef8fadadf34ae951b337dcdecce495936`. ASan/UBSan: 893/893, 1089.77 seconds. These include real SDL player and installed C/C++ consumer smokes and pinned Linux AGE/speed fixture rebuilds. Historical SUMMARY run ids/counts and RED scratch evidence remain historical; they are not presented as the current hosted receipt. Any later committed revision must have its own eligible green checks before merge.

Qualification: only AGE DIV (5/5) and STOP-prefetch (1/1) pass; eleven admitted ROMs have exact-signature expected-failure dispositions. Passing their disposition tests verifies the published boundaries, not the unsupported hardware behavior. The selected stall is `0x20004` destination-speed CPU T in the measured `[0x20004,0x20007]` window. M28 changes mode-0 but not DIV. No physical hardware or local libFuzzer campaign is claimed. No scope expansion or new owner decision is needed.

Durable closure: `python3 -I .planning/phases/GB-12-cgb-double-speed/verify-uat-contract.py --self-test` checks the exact one-to-one 73-entry mapping and rejects nine weaker-closure mutations. Existing `summary_coverage` and its negative controls enforce the automation schema in CI before verify-work. This session-specific closure check stays local; existing recurring behavior, seam, fixture, install, package and mutation checks already run in CI. Rerunning verify-work on unchanged evidence resumes this completed file and must not create new plans or repeat UAT. Reopen only for changed covered behavior, a new regression, or stale/unavailable evidence; use the canonical verification owner to refresh that evidence.

### 1. Pre-change CGB frame, PCM and inline timer/serial/DMA identity pins detect altered output.
expected: "Pre-change CGB frame, PCM and inline timer/serial/DMA identity pins detect altered output."
result: pass
source: automated
summary_file: 12-01-SUMMARY.md
coverage_id: D1
evidence: ["cgb_speed_identity_pin", "cgb_speed_identity_pin_flipped", "cgb_speed_internal_harness_alive"]

### 2. Armed CGB STOP switches at retirement, exposes KEY1 speed, consumes a resumable stall, and emits only the STOP trace record.
expected: "Armed CGB STOP switches at retirement, exposes KEY1 speed, consumes a resumable stall, and emits only the STOP trace record."
result: pass
source: automated
summary_file: 12-01-SUMMARY.md
coverage_id: D2
evidence: ["cgb_speed_tracer_switch", "cgb_stop_armed_cgb", "cgb_stop_unarmed_cgb", "cgb_stop_compat_ignores_key1", "cgb_stop_dmg_control"]

### 3. KEY1 documentation, model-gate declarations and existing DMG identity remain consistent.
expected: "KEY1 documentation, model-gate declarations and existing DMG identity remain consistent."
result: pass
source: automated
summary_file: 12-01-SUMMARY.md
coverage_id: D3
evidence: ["cgb_tables_io", "model_gates", "bash tests/scripts/verify-dmg-baseline.sh"]

### 4. The rights and manifest pin the first AGE ROM to its source commit, tree, license, source path and RGBDS 1.0.1 archive; local rebuild bytes match.
expected: "The rights and manifest pin the first AGE ROM to its source commit, tree, license, source path and RGBDS 1.0.1 archive; local rebuild bytes match."
result: pass
source: automated
summary_file: 12-02-SUMMARY.md
coverage_id: D1
evidence: ["bash tests/scripts/reproduce-age.sh --compare", "cmake -DMANIFEST=fixtures/age/manifest.json -P cmake/VerifyFixtureManifest.cmake", "shasum -a 256 fixtures/age/LICENSE.txt and fixtures/age/WARNING.md"]

### 5. Offline comparison and manifest validation reject tampered bytes, an escaping source path and a malformed digest.
expected: "Offline comparison and manifest validation reject tampered bytes, an escaping source path and a malformed digest."
result: pass
source: automated
summary_file: 12-02-SUMMARY.md
coverage_id: D2
evidence: ["bash tests/scripts/test-reproduce-age.sh compare-tampered", "bash tests/scripts/test-reproduce-age.sh selfcheck-tampered"]

### 6. The hosted fixture-repro workflow enforces AGE RGBDS pin equality and schedules rebuild and offline controls.
expected: "The hosted fixture-repro workflow enforces AGE RGBDS pin equality and schedules rebuild and offline controls."
result: pass
source: automated
summary_file: 12-02-SUMMARY.md
coverage_id: D3
evidence: ["fixture-repro workflow YAML and required step/pin assertions"]

### 7. M5/M7 runtime mutants, mask-zero controls, duplicate-anchor rejection and the off-M stall static-assert mutant validate the shared mutant harness.
expected: "M5/M7 runtime mutants, mask-zero controls, duplicate-anchor rejection and the off-M stall static-assert mutant validate the shared mutant harness."
result: pass
source: automated
summary_file: 12-03-SUMMARY.md
coverage_id: GB-12-03-01
evidence: ["cgb_speed_tracer_switch", "cgb_speed_mutant_m5_stall_sets_stopped and cgb_speed_mutant_m5_stall_sets_stopped_control", "cgb_speed_mutant_m7_devices_frozen and cgb_speed_mutant_m7_devices_frozen_control", "cgb_speed_mutant_anchor_guard", "cgb_speed_stall_static_assert_mutant"]

### 8. All base and CB opcode costs, bus offsets, 1000-NOP normal/double-speed loops, interrupt costs, and M18 scaling mutation are checked.
expected: "All base and CB opcode costs, bus offsets, 1000-NOP normal/double-speed loops, interrupt costs, and M18 scaling mutation are checked."
result: pass
source: automated
summary_file: 12-03-SUMMARY.md
coverage_id: GB-12-03-02
evidence: ["cgb_speed_cpu_ticks", "cgb_speed_mutant_m18_cost_unscaled and cgb_speed_mutant_m18_cost_unscaled_control", "gsd check tdd-red-evidence build/tdd-red-12-03-task2.json returned RED_EVIDENCE_OK for the unscaled-cost scratch mutant"]

### 9. Reset independently clears double speed, speed-switch stall kind and duration, and KEY1 arming; each mutant is detected and its mask-zero control passes.
expected: "Reset independently clears double speed, speed-switch stall kind and duration, and KEY1 arming; each mutant is detected and its mask-zero control passes."
result: pass
source: automated
summary_file: 12-03-SUMMARY.md
coverage_id: GB-12-03-03
evidence: ["cgb_speed_reset_double_speed", "cgb_speed_reset_stall", "cgb_speed_reset_key1", "cgb_speed_mutant_m24_reset_retains_double_speed and cgb_speed_mutant_m24_reset_retains_double_speed_control", "cgb_speed_mutant_m25_reset_retains_stall and cgb_speed_mutant_m25_reset_retains_stall_control", "cgb_speed_mutant_m26_reset_retains_key1_arm and cgb_speed_mutant_m26_reset_retains_key1_arm_control", "gsd check tdd-red-evidence build/tdd-red-12-03-task3.json returned RED_EVIDENCE_OK for the reset KEY1 scratch mutant"]

### 10. The full suite, CGB identity pins and the DMG baseline remain unchanged.
expected: "The full suite, CGB identity pins and the DMG baseline remain unchanged."
result: pass
source: automated
summary_file: 12-03-SUMMARY.md
coverage_id: GB-12-03-04
evidence: ["ctest --preset phase1 --output-on-failure --no-tests=error -j8 (713/713)", "cgb_speed_identity_pin and cgb_speed_identity_pin_flipped", "cgb_instance_isolation", "bash tests/scripts/verify-dmg-baseline.sh (baseline status=pass)", "summary_coverage"]

### 11. The 13-ROM manifest has complete source, digest, linker-layout, attestation, and expected-role records, with no excluded or private files.
expected: "The 13-ROM manifest has complete source, digest, linker-layout, attestation, and expected-role records, with no excluded or private files."
result: pass
source: automated
summary_file: 12-04-SUMMARY.md
coverage_id: GB-12-04-01
evidence: ["cmake -DMANIFEST=fixtures/age/manifest.json -P cmake/VerifyFixtureManifest.cmake", "Python manifest assertions; ROM-count, D-19 exclusion, and privacy scans"]

### 12. All admitted ROMs reproduce byte-identically with pinned RGBDS 1.0.1, and offline negative controls still detect fixture tampering.
expected: "All admitted ROMs reproduce byte-identically with pinned RGBDS 1.0.1, and offline negative controls still detect fixture tampering."
result: pass
source: automated
summary_file: 12-04-SUMMARY.md
coverage_id: GB-12-04-02
evidence: ["PATH=<digest-pinned RGBDS 1.0.1> GBB_RGBDS_ARCHIVE=<verified macOS archive> GBB_RGBDS_ARCHIVE_SHA256=2f6f13c6ec984313656c07b08d97dfcd3a471c7d3901d3ff486e5814bb503645 bash tests/scripts/reproduce-age.sh --compare", "bash tests/scripts/test-reproduce-age.sh compare-tampered", "bash tests/scripts/test-reproduce-age.sh selfcheck-tampered", "ctest --test-dir build -R '^summary_coverage$' --output-on-failure"]

### 13. Guest timer and DIV samples across two LY transitions show twice the CPU-side rate at double speed, preserve pending reload ticks, and retain normal-speed identity.
expected: "Guest timer and DIV samples across two LY transitions show twice the CPU-side rate at double speed, preserve pending reload ticks, and retain normal-speed identity."
result: pass
source: automated
summary_file: 12-05-SUMMARY.md
coverage_id: GB-12-05-01
evidence: ["cgb_speed_timer_scaling", "cgb_speed_mutant_m3_timer_unscaled and cgb_speed_mutant_m3_timer_unscaled_control", "cgb_speed_mutant_m15_timer_reload_half_dot_units and cgb_speed_mutant_m15_timer_reload_half_dot_units_control", "cgb_speed_identity_pin and cgb_speed_identity_pin_flipped", "bash tests/scripts/verify-dmg-baseline.sh (baseline status=pass)"]

### 14. Serial, DMA and frame-sequencer rates scale with CPU ticks, while switch remainders survive and TIMA reload uses the remaining ticks.
expected: "Serial, DMA and frame-sequencer rates scale with CPU ticks, while switch remainders survive and TIMA reload uses the remaining ticks."
result: pass
source: automated
summary_file: 12-05-SUMMARY.md
coverage_id: GB-12-05-02
evidence: ["cgb_speed_serial_scaling and cgb_speed_mutant_m2_serial_unscaled with control", "cgb_speed_dma_scaling and cgb_speed_mutant_m14_dma_unscaled with control", "cgb_speed_apu_tap and cgb_speed_mutant_m4_apu_tap_unscaled with control", "cgb_speed_remainder_across_switch and cgb_speed_mutant_m11_remainder_dropped_at_switch with control", "gsd check tdd-red-evidence build/tdd-red-12-05-task2.json (RED_EVIDENCE_OK)"]

### 15. PPU line and frame timing, APU channel and PCM output, and RTC seconds remain equal in master time at both CPU speeds.
expected: "PPU line and frame timing, APU channel and PCM output, and RTC seconds remain equal in master time at both CPU speeds."
result: pass
source: automated
summary_file: 12-05-SUMMARY.md
coverage_id: GB-12-05-03
evidence: ["cgb_speed_ppu_apu_rtc_unscaled", "cgb_speed_mutant_m1_ppu_scaled and control", "cgb_speed_mutant_m12_rtc_scaled and control", "cgb_speed_mutant_m17_apu_channels_scaled and control", "cgb_speed_domains_scan and cgb_speed_domains_scan_mutated", "gsd check tdd-red-evidence build/tdd-red-12-05-task3.json (RED_EVIDENCE_OK)"]

### 16. The complete local regression suite passes with all Phase 12 timing, identity and model-gate checks present.
expected: "The complete local regression suite passes with all Phase 12 timing, identity and model-gate checks present."
result: pass
source: automated
summary_file: 12-05-SUMMARY.md
coverage_id: GB-12-05-04
evidence: ["ctest --test-dir build --output-on-failure --no-tests=error -j8 (741/741)", "cgb_speed_identity_pin and model_gates"]

### 17. Armed STOP decision cases, exact byte lengths and effects, public-input held-button wake, and a guest-generated timer IRQ with natural IME dispatch
expected: "Armed STOP decision cases, exact byte lengths and effects, public-input held-button wake, and a guest-generated timer IRQ with natural IME dispatch"
result: pass
source: automated
summary_file: 12-06-SUMMARY.md
coverage_id: GB-12-06-STOP
evidence: ["cgb_speed_stop_cases", "cgb_speed_stop_guest_timer_irq", "cgb_speed_mutant_m20_guest_timer_pending_ignored and cgb_speed_mutant_m20_guest_timer_pending_ignored_control", "cgb_speed_mutant_m34_stop_falls_into_rlca and cgb_speed_mutant_m34_stop_falls_into_rlca_control", "cgb_speed_mutant_m20_pending_ignored and cgb_speed_mutant_m20_pending_ignored_control", "cgb_speed_mutant_m19_held_predicate_ignored and cgb_speed_mutant_m19_held_predicate_ignored_control"]

### 18. STOP operand independence and opcode fetch from FF04 with a wrong-byte negative
expected: "STOP operand independence and opcode fetch from FF04 with a wrong-byte negative"
result: pass
source: automated
summary_file: 12-06-SUMMARY.md
coverage_id: GB-12-06-FETCH
evidence: ["cgb_speed_stop_operand", "cgb_speed_stop_prefetch_ff04 and cgb_speed_stop_prefetch_ff04_negative", "cgb_speed_mutant_m33_operand_changes_switch and cgb_speed_mutant_m33_operand_changes_switch_control"]

### 19. Switch cost, KEY1/KEY0 semantics and DMG/unarmed identity remain enforced
expected: "Switch cost, KEY1/KEY0 semantics and DMG/unarmed identity remain enforced"
result: pass
source: automated
summary_file: 12-06-SUMMARY.md
coverage_id: GB-12-06-SPEED
evidence: ["cgb_speed_stop_cost, cgb_speed_key1_readback, cgb_speed_key0_no_switch", "cgb_speed_dmg_unarmed_unchanged", "cgb_speed_mutant_m8_speed_gate_removed, cgb_speed_mutant_m10_key1_arm_not_cleared, cgb_speed_mutant_m27_divider_reset_omitted, cgb_speed_mutant_m29_switch_cost_one_m, cgb_speed_mutant_m30_dmg_stop_apu_edge, cgb_speed_mutant_m32_key0_toggles_speed and cgb_speed_mutant_m33_operand_changes_switch; each paired _control", "cgb_speed_tracer_switch, cgb_speed_identity_pin, cgb_speed_identity_pin_flipped, cgb_stop_*, cgb_dmg_identity_*, banking_tracer_digest_unchanged, cgb_runner_profile_dmg_identity_*, model_gates*", "bash tests/scripts/verify-dmg-baseline.sh"]

### 20. A timer IRQ ends the speed-switch stall at an M-cycle boundary; IME dispatch, IME-off resume, EI;STOP, and host budget partitioning retain their contracts.
expected: "A timer IRQ ends the speed-switch stall at an M-cycle boundary; IME dispatch, IME-off resume, EI;STOP, and host budget partitioning retain their contracts."
result: pass
source: automated
summary_file: 12-07-SUMMARY.md
coverage_id: GB-12-07-WAKE
evidence: ["cgb_speed_wake_ime_on", "cgb_speed_wake_ime_off", "cgb_speed_ei_stop", "cgb_speed_wake_m_boundary", "cgb_speed_mutant_m13_wake_ime_off_ignored and its mask-zero control", "cgb_speed_mutant_m16_wake_sampled_per_call and its mask-zero control", "cgb_speed_mutant_m34_ei_delay_not_retired and its mask-zero control"]

### 21. Every CGB entry into normal speed applies the D-09 four-half-dot CPU realignment tail only at phase four, and does not cut the tail short on pending IF.
expected: "Every CGB entry into normal speed applies the D-09 four-half-dot CPU realignment tail only at phase four, and does not cut the tail short on pending IF."
result: pass
source: automated
summary_file: 12-07-SUMMARY.md
coverage_id: GB-12-07-REALIGN
evidence: ["cgb_speed_realign", "cgb_speed_mutant_m23_realignment_omitted and its mask-zero control"]

### 22. The named stall duration is exact at both destination speeds, stays M-cycle aligned, and consumes no more than the caller budget.
expected: "The named stall duration is exact at both destination speeds, stays M-cycle aligned, and consumes no more than the caller budget."
result: pass
source: automated
summary_file: 12-07-SUMMARY.md
coverage_id: GB-12-07-LENGTH-BUDGET
evidence: ["cgb_speed_stall_length", "cgb_speed_budget_semantics", "cgb_speed_mutant_m6_stall_one_m_long and its mask-zero control", "cgb_speed_mutant_m21_stall_one_m_short and its mask-zero control", "cgb_speed_mutant_m28_stall_one_half_dot_long and its mask-zero control", "cgb_speed_mutant_m9_stall_budget_unbounded and its mask-zero control", "cgb_speed_mutant_m31_stall_offset_noop"]

### 23. CGB stall time advances PPU, DIV/TIMA, serial, OAM DMA, and audio output without exposing STOPPED, HALTED_IDLE, or NO_PROGRESS to the host.
expected: "CGB stall time advances PPU, DIV/TIMA, serial, OAM DMA, and audio output without exposing STOPPED, HALTED_IDLE, or NO_PROGRESS to the host."
result: pass
source: automated
summary_file: 12-07-SUMMARY.md
coverage_id: GB-12-07-DEVICES
evidence: ["cgb_speed_stall_devices_advance", "cgb_speed_never_stopped", "cgb_speed_mutant_m5_stall_sets_stopped_devices and its mask-zero control", "cgb_speed_mutant_m7_devices_frozen_devices and its mask-zero control", "cgb_speed_mutant_m5_stall_sets_stopped_never and its mask-zero control", "cgb_speed_mutant_m7_devices_frozen_never and its mask-zero control"]

### 24. An armed switching STOP rejects insufficient worst-case time headroom without mutation and proceeds with exactly one more half-dot available.
expected: "An armed switching STOP rejects insufficient worst-case time headroom without mutation and proceeds with exactly one more half-dot available."
result: pass
source: automated
summary_file: 12-07-SUMMARY.md
coverage_id: GB-12-07-HEADROOM
evidence: ["cgb_speed_headroom", "cgb_speed_mutant_m22_switch_headroom_omitted and its mask-zero control"]

### 25. The Phase 12 speed-switch changes preserve STOP, DMG identity, model-gate contracts, and the frozen DMG baseline across the complete CTest inventory.
expected: "The Phase 12 speed-switch changes preserve STOP, DMG identity, model-gate contracts, and the frozen DMG baseline across the complete CTest inventory."
result: pass
source: automated
summary_file: 12-07-SUMMARY.md
coverage_id: GB-12-07-REGRESSION
evidence: ["ctest --test-dir build -j8 --output-on-failure --no-tests=error", "bash tests/scripts/verify-dmg-baseline.sh"]

### 26. Every Phase 12 model-gate row is resolved, reassigned with its reason, or recorded as an expected failure; the code and table remain bijective.
expected: "Every Phase 12 model-gate row is resolved, reassigned with its reason, or recorded as an expected failure; the code and table remain bijective."
result: pass
source: automated
summary_file: 12-08-SUMMARY.md
coverage_id: GB-12-08-GATES
evidence: ["python3 -I tests/scripts/verify-model-gates.py", "model_gates", "model_gates_no_phase12_rows", "model_gates_no_phase12_rows_mutated_doc"]

### 27. The CGB profile describes all four STOP cases, the stall timing derivation, D-070 clock behavior, deferred behaviors, and future state fields.
expected: "The CGB profile describes all four STOP cases, the stall timing derivation, D-070 clock behavior, deferred behaviors, and future state fields."
result: pass
source: automated
summary_file: 12-08-SUMMARY.md
coverage_id: GB-12-08-STOP-DOC
evidence: ["cgb_speed_profile_contract", "cgb_speed_profile_contract_missing_selftest", "cgb_adr_half_dot_contract", "cgb_native_guide_contract", "cgb_tables_postboot", "cgb_tables_io"]

### 28. The updated core metadata and CTest registration configure and build, and the profile contains no stale Phase 12 deferral or verification marker.
expected: "The updated core metadata and CTest registration configure and build, and the profile contains no stale Phase 12 deferral or verification marker."
result: pass
source: automated
summary_file: 12-08-SUMMARY.md
coverage_id: GB-12-08-BUILD
evidence: ["cmake --build --preset phase1", "! rg -n 'DEFERRED\\\\(12\\\\)|\\\\[VERIFY\\\\]' docs/cgb-profile.md", "! rg -n '\\\"(0x20004|131076|262152)\\\"' tests/CMakeLists.txt"]

### 29. The bounded AGE driver validates all five spsw-div rows, emits a stable verdict signature, and uses a measured budget with a distinct timeout result.
expected: "The bounded AGE driver validates all five spsw-div rows, emits a stable verdict signature, and uses a measured budget with a distinct timeout result."
result: pass
source: automated
summary_file: 12-09-SUMMARY.md
coverage_id: GB-12-09-AGE
evidence: ["age_spsw_div_cgbBCE", "age_spsw_div_cgbBCE_timeout"]

### 30. The committed-core stall window is re-measured through the public M31 offset seam, including failing controls just outside both passing edges.
expected: "The committed-core stall window is re-measured through the public M31 offset seam, including failing controls just outside both passing edges."
result: pass
source: automated
summary_file: 12-09-SUMMARY.md
coverage_id: GB-12-09-WINDOW
evidence: ["age_stall_window", "ctest --test-dir build -R '^(age_stall_window|age_spsw_div_cgbBCE|cgb_speed_)' --output-on-failure --no-tests=error"]

### 31. The CGB profile records the measured window and source revision, while numeric phrases derive from the core constant and a missing-phrase control still fails.
expected: "The CGB profile records the measured window and source revision, while numeric phrases derive from the core constant and a missing-phrase control still fails."
result: pass
source: automated
summary_file: 12-09-SUMMARY.md
coverage_id: GB-12-09-DOCS
evidence: ["cgb_speed_profile_contract", "cgb_speed_profile_contract_missing_selftest", "cgb_adr_half_dot_contract"]

### 32. The complete configured test inventory passes after the AGE driver, mutant gate, and measured-window contract are committed.
expected: "The complete configured test inventory passes after the AGE driver, mutant gate, and measured-window contract are committed."
result: pass
source: automated
summary_file: 12-09-SUMMARY.md
coverage_id: GB-12-09-REGRESSION
evidence: ["ctest --test-dir build --output-on-failure --no-tests=error -j8"]

### 33. Original four-phase speed fixture and independent expectation controls validate the timer, DIV, serial, NR52, DMA, KEY1, and STOP observations.
expected: "Original four-phase speed fixture and independent expectation controls validate the timer, DIV, serial, NR52, DMA, KEY1, and STOP observations."
result: pass
source: automated
summary_file: 12-10-SUMMARY.md
coverage_id: D1
evidence: ["cgb_speed_fixture_digest", "cgb_speed_fixture_probes", "cgb_speed_expectations_derive", "cgb_speed_expectations_tampered", "cgb_speed_expectations_factor3"]

### 34. The clean-core 60-frame PCM digest is pinned and detects the APU-2x mutation.
expected: "The clean-core 60-frame PCM digest is pinned and detects the APU-2x mutation."
result: pass
source: automated
summary_file: 12-10-SUMMARY.md
coverage_id: D2
evidence: ["cgb_speed_fixture_audio_digest", "cgb_speed_fixture_audio_digest_mutant_m17", "cgb_speed_fixture_audio_digest_mutant_m17_control"]

### 35. The clean-core 60-frame RGB555 digest is pinned and detects the PPU-follows-CPU mutation.
expected: "The clean-core 60-frame RGB555 digest is pinned and detects the PPU-follows-CPU mutation."
result: pass
source: automated
summary_file: 12-10-SUMMARY.md
coverage_id: D3
evidence: ["cgb_speed_fixture_frame_digest", "cgb_speed_fixture_frame_digest_mutant_m1", "cgb_speed_fixture_frame_digest_mutant_m1_control"]

### 36. Eight original guest entry points exercise pending IRQ, IME-off, in-stall wake, held-button HALT, EI;STOP, LCD-off DIV, active DMA, and four consecutive switches; selectors 0 and 9 retain distinct markers.
expected: "Eight original guest entry points exercise pending IRQ, IME-off, in-stall wake, held-button HALT, EI;STOP, LCD-off DIV, active DMA, and four consecutive switches; selectors 0 and 9 retain distinct markers."
result: pass
source: automated
summary_file: 12-11-SUMMARY.md
coverage_id: GB-12-11-HOSTILE
evidence: ["cgb_speed_fixture_hostile", "cgb_speed_fixture_digest"]

### 37. Hostile outcome bounds are derived independently from D-02/D-08 timing rules and checked against the guest observations.
expected: "Hostile outcome bounds are derived independently from D-02/D-08 timing rules and checked against the guest observations."
result: pass
source: automated
summary_file: 12-11-SUMMARY.md
coverage_id: GB-12-11-EXPECTATIONS
evidence: ["python3 -I tests/scripts/derive-cgb-speed-expectations.py --check tests/data/cgb-speed-expectations.txt", "cgb_speed_fixture_hostile"]

### 38. A configure-time copy with selector 4 KEY1-after changed to 0xFE is rejected by the independent host verdict.
expected: "A configure-time copy with selector 4 KEY1-after changed to 0xFE is rejected by the independent host verdict."
result: pass
source: automated
summary_file: 12-11-SUMMARY.md
coverage_id: GB-12-11-TAMPER
evidence: ["cgb_speed_expectations_hostile_tampered"]

### 39. The hostile ROM is reproducible with digest-pinned RGBDS 1.0.1 and its manifest source and byte hashes match.
expected: "The hostile ROM is reproducible with digest-pinned RGBDS 1.0.1 and its manifest source and byte hashes match."
result: pass
source: automated
summary_file: 12-11-SUMMARY.md
coverage_id: GB-12-11-PROVENANCE
evidence: ["Pinned RGBDS 1.0.1 rebuild followed by cmp against fixtures/cgb-speed/speed-hostile.gb", "cgb_speed_fixture_digest"]

### 40. The real CGB player renders speed.gb to the pinned RGBA digest and title token, while wrong-digest and PPU-follows-CPU controls are detected.
expected: "The real CGB player renders speed.gb to the pinned RGBA digest and title token, while wrong-digest and PPU-follows-CPU controls are detected."
result: pass
source: automated
summary_file: 12-12-SUMMARY.md
coverage_id: GB-12-12-PLAYER-SPEED
evidence: ["player_cgb_speed_smoke", "player_cgb_speed_smoke_wrong_sha", "player_cgb_speed_smoke_mutant_ppu_follows_cpu"]

### 41. Player limitations, README, preview package metadata, help, and their expected text consistently state that CGB double speed is implemented while mode-3 timing and HDMA remain unclaimed.
expected: "Player limitations, README, preview package metadata, help, and their expected text consistently state that CGB double speed is implemented while mode-3 timing and HDMA remain unclaimed."
result: pass
source: automated
summary_file: 12-12-SUMMARY.md
coverage_id: GB-12-12-CLAIMS
evidence: ["player_limitations", "player_claims_agree", "player_claims_agree_mutated"]

### 42. Relocated installed C and C++ consumers exercise an armed switch in bounded gbb_run partitions, reject unarmed twins, and preserve the existing public symbol set.
expected: "Relocated installed C and C++ consumers exercise an armed switch in bounded gbb_run partitions, reject unarmed twins, and preserve the existing public symbol set."
result: pass
source: automated
summary_file: 12-12-SUMMARY.md
coverage_id: GB-12-12-INSTALLED-CONSUMERS
evidence: ["installed_consumer_c", "installed_consumer_cpp", "cgb_consumer_symbol_coverage"]

### 43. The manifest-driven script rebuilds speed.gb and speed-hostile.gb with RGBDS 1.0.1 and requires exact equality with their committed bytes and SHA-256 pins.
expected: "The manifest-driven script rebuilds speed.gb and speed-hostile.gb with RGBDS 1.0.1 and requires exact equality with their committed bytes and SHA-256 pins."
result: pass
source: automated
summary_file: 12-13-SUMMARY.md
coverage_id: GB-12-13-REPRODUCER
evidence: ["bash tests/scripts/reproduce-cgb-speed.sh", "cgb_speed_repro_tool_failure", "cgb_speed_repro_missing_pin"]

### 44. The Linux fixture-repro job cross-checks all CGB speed RGBDS pins and runs the byte-exact rebuild; the actual embedded check rejects a tampered archive digest.
expected: "The Linux fixture-repro job cross-checks all CGB speed RGBDS pins and runs the byte-exact rebuild; the actual embedded check rejects a tampered archive digest."
result: pass
source: automated
summary_file: 12-13-SUMMARY.md
coverage_id: GB-12-13-WORKFLOW
evidence: ["cgb_speed_repro_missing_pin workflow pin positive and archive_sha256 mismatch control", "actionlint .github/workflows/fixture-repro.yml"]

### 45. Both bash-only controls are registered under their exact expected names and removed from the Windows inventory.
expected: "Both bash-only controls are registered under their exact expected names and removed from the Windows inventory."
result: pass
source: automated
summary_file: 12-13-SUMMARY.md
coverage_id: GB-12-13-INVENTORY
evidence: ["cmake --preset phase1", "ctest --test-dir build -R '^cgb_speed_repro_' --output-on-failure --no-tests=error"]

### 46. Full-state run partitioning matches around stall start and at both real-constant stall ends, with a timer wake inside the stall.
expected: "Full-state run partitioning matches around stall start and at both real-constant stall ends, with a timer wake inside the stall."
result: pass
source: automated
summary_file: 12-14-SUMMARY.md
coverage_id: CGB-06-STALL-BOUNDARIES
evidence: ["cgb_partition_stall_start_window", "cgb_partition_hostile_irq_in_stall", "cgb_partition_stall_end_window_to_double", "cgb_partition_stall_end_window_to_normal"]

### 47. Snapshot restore preserves the independent continuation digest and rejects unsupported pointer ownership.
expected: "Snapshot restore preserves the independent continuation digest and rejects unsupported pointer ownership."
result: pass
source: automated
summary_file: 12-14-SUMMARY.md
coverage_id: CGB-06-SNAPSHOT-RESTORE
evidence: ["cgb_partition_snapshot_fidelity", "cgb_partition_stall_end_window_to_double", "cgb_partition_stall_end_window_to_normal"]

### 48. Seeded, fixed interior, and zero/sub-quantum budgets retain the same final digest and make valid progress.
expected: "Seeded, fixed interior, and zero/sub-quantum budgets retain the same final digest and make valid progress."
result: pass
source: automated
summary_file: 12-14-SUMMARY.md
coverage_id: CGB-06-SEEDED-MULTICUT
evidence: ["cgb_partition_stall_end_window_seeded", "cgb_partition_interior_points", "cgb_partition_seeded_multicut", "cgb_partition_zero_and_subquantum"]

### 49. Pending-IRQ, held-button, LCD-off, back-to-back, and chained STOP scenarios are cut around step-measured retirement boundaries.
expected: "Pending-IRQ, held-button, LCD-off, back-to-back, and chained STOP scenarios are cut around step-measured retirement boundaries."
result: pass
source: automated
summary_file: 12-14-SUMMARY.md
coverage_id: CGB-06-STOP-IRQ-SCENARIOS
evidence: ["cgb_partition_pending_at_stop", "cgb_partition_held_button", "cgb_partition_lcd_off", "cgb_partition_back_to_back", "cgb_partition_chained"]

### 50. A one-M joypad timing change and mutation of every digest input group, including ROM and cartridge RAM, change the digest.
expected: "A one-M joypad timing change and mutation of every digest input group, including ROM and cartridge RAM, change the digest."
result: pass
source: automated
summary_file: 12-14-SUMMARY.md
coverage_id: CGB-06-DIGEST-SENSITIVITY
evidence: ["cgb_partition_sensitivity_joypad_shift", "cgb_partition_sensitivity_digest_input"]

### 51. Per-call stall-wake sampling is detected by the M16 mutant while the zero-mask control passes.
expected: "Per-call stall-wake sampling is detected by the M16 mutant while the zero-mask control passes."
result: pass
source: automated
summary_file: 12-14-SUMMARY.md
coverage_id: D-34-M16-NEGATIVE-CONTROL
evidence: ["cgb_partition_mutant_m16", "cgb_partition_mutant_m16_control"]

### 52. Every partition CTest has a half-dot cap and explicit timeout; measured local Debug wall times are recorded in CMake.
expected: "Every partition CTest has a half-dot cap and explicit timeout; measured local Debug wall times are recorded in CMake."
result: pass
source: automated
summary_file: 12-14-SUMMARY.md
coverage_id: D-29-PER-CASE-CAP
evidence: ["ctest --test-dir build -R '^cgb_partition_' -V --no-tests=error -j1", "ctest --test-dir build --output-on-failure --no-tests=error -j8"]

### 53. Eight guest-driven speed seeds prove their intended switch, repeated-switch, pending-interrupt, button, DMA, LCD, compatibility, or DMG control path while checking every run call.
expected: "Eight guest-driven speed seeds prove their intended switch, repeated-switch, pending-interrupt, button, DMA, LCD, compatibility, or DMG control path while checking every run call."
result: pass
source: automated
summary_file: 12-15-SUMMARY.md
coverage_id: CGB-06-SPEED-FUZZ-PATHS
evidence: ["cgb_fuzz_speed_regressions", "fuzz_core_regressions"]

### 54. The inverted KEY1 oracle is detected on speed seeds and does not spuriously fail the non-speed control.
expected: "The inverted KEY1 oracle is detected on speed seeds and does not spuriously fail the non-speed control."
result: pass
source: automated
summary_file: 12-15-SUMMARY.md
coverage_id: CGB-06-SPEED-ORACLE-NEGATIVE
evidence: ["cgb_fuzz_speed_oracle_mutant", "cgb_fuzz_speed_oracle_mutant_control"]

### 55. The bounded-fuzz self-test verifies the speed-switch dictionary and its use by both fuzz invocations.
expected: "The bounded-fuzz self-test verifies the speed-switch dictionary and its use by both fuzz invocations."
result: pass
source: automated
summary_file: 12-15-SUMMARY.md
coverage_id: CGB-06-SPEED-DICTIONARY
evidence: ["bash tests/scripts/run-bounded-fuzz.sh --self-test"]

### 56. Each admitted AGE ROM is pinned to its measured committed-core outcome, with expected failures carrying exact signatures, row masks, flip rules, and bounded budgets.
expected: "Each admitted AGE ROM is pinned to its measured committed-core outcome, with expected failures carrying exact signatures, row masks, flip rules, and bounded budgets."
result: pass
source: automated
summary_file: 12-16-SUMMARY.md
coverage_id: CGB-06-AGE-VERDICTS
evidence: ["age_spsw_div_cgbBCE", "age_spsw_tima_cgbE", "age_spsw_tima_cgbBC", "age_spsw_stop_prefetch_cgbBCE", "age_spsw_interrupts_cgbE", "age_spsw_mode0_cgbBCE", "age_spsw_ch2_lc_delay_cgbBCE", "age_stat_mode_ds_cgbBCE", "age_stat_mode_cgbE", "age_stat_mode_sprites_ds_cgbBCE", "age_stat_mode_sprites_dmgC_cgbBCE", "age_stat_mode_window_ds_cgbBCE", "age_stat_mode_window_cgbBCE"]

### 57. The AGE fixture manifest verifies all vendored digests and rejects a deliberately changed digest pin.
expected: "The AGE fixture manifest verifies all vendored digests and rejects a deliberately changed digest pin."
result: pass
source: automated
summary_file: 12-16-SUMMARY.md
coverage_id: CGB-06-AGE-DIGEST
evidence: ["age_fixture_digest", "age_fixture_digest_tampered"]

### 58. Offline rebuild self-check and tampered-manifest and tampered-ROM negative controls detect changed fixture provenance or bytes.
expected: "Offline rebuild self-check and tampered-manifest and tampered-ROM negative controls detect changed fixture provenance or bytes."
result: pass
source: automated
summary_file: 12-16-SUMMARY.md
coverage_id: CGB-06-AGE-REPRODUCTION
evidence: ["age_repro_selfcheck", "age_repro_selfcheck_tampered", "age_repro_compare_tampered"]

### 59. AGE ROM bytes are absent from the install tree, and the renamed-copy control proves the scan detects them by digest.
expected: "AGE ROM bytes are absent from the install tree, and the renamed-copy control proves the scan detects them by digest."
result: pass
source: automated
summary_file: 12-16-SUMMARY.md
coverage_id: CGB-06-AGE-NOT-INSTALLED
evidence: ["age_not_installed", "age_not_installed_selftest"]

### 60. Four unresolved speed-switch behaviors are pinned to current behavior with mutant or deliberate-input negative controls.
expected: "Four unresolved speed-switch behaviors are pinned to current behavior with mutant or deliberate-input negative controls."
result: pass
source: automated
summary_file: 12-17-SUMMARY.md
coverage_id: CGB-06-SPEED-BEHAVIOR-PINS
evidence: ["cgb_speed_xfail_pause_ppu_output", "cgb_speed_mutant_m7_xfail_ppu", "cgb_speed_mutant_m7_xfail_ppu_control", "cgb_speed_xfail_dma_restart", "cgb_speed_mutant_m14_xfail_dma_restart", "cgb_speed_xfail_hdma_fails_closed_negative", "cgb_speed_xfail_stop_oam_unchanged_negative"]

### 61. All disposition rows are pinned to inventory tests, mirrored in the CGB profile, and protected by edited-reason and missing-pin controls.
expected: "All disposition rows are pinned to inventory tests, mirrored in the CGB profile, and protected by edited-reason and missing-pin controls."
result: pass
source: automated
summary_file: 12-17-SUMMARY.md
coverage_id: CGB-06-SPEED-DISPOSITIONS
evidence: ["cgb_speed_dispositions", "cgb_speed_dispositions_mutated", "cgb_speed_dispositions_pinned_by_missing", "cgb_external_dispositions", "cgb_external_dispositions_mutated"]

### 62. Every admitted AGE ROM is compared against clean behavior for all four stall and DIV mutants, with required DIV discrimination retained for M6, M21, and M27.
expected: "Every admitted AGE ROM is compared against clean behavior for all four stall and DIV mutants, with required DIV discrimination retained for M6, M21, and M27."
result: pass
source: automated
summary_file: 12-17-SUMMARY.md
coverage_id: CGB-06-AGE-SENSITIVITY
evidence: ["age_sensitivity_m6", "age_sensitivity_m21", "age_sensitivity_m28", "age_sensitivity_m27", "age_sensitivity_m28_reference_mutated"]

### 63. The M28 test mutant is limited to double-speed destinations and the normal-speed transition invariant is pinned independently.
expected: "The M28 test mutant is limited to double-speed destinations and the normal-speed transition invariant is pinned independently."
result: pass
source: automated
summary_file: 12-17-SUMMARY.md
coverage_id: CGB-06-M28-SCOPE
evidence: ["cgb_speed_m28_normal_unchanged", "cgb_speed_m28_normal_unchanged_control", "age_sensitivity_m28"]

### 64. The complete configured local CTest inventory passes after the plan changes.
expected: "The complete configured local CTest inventory passes after the plan changes."
result: pass
source: automated
summary_file: 12-17-SUMMARY.md
coverage_id: CGB-06-FULL-SUITE
evidence: ["ctest --test-dir build --output-on-failure --no-tests=error -j8 (895/895)"]

### 65. The native guide and public header comments describe KEY1 speed visibility, master-time budgets, frame duration, and modeled pause stop semantics without changing declarations.
expected: "The native guide and public header comments describe KEY1 speed visibility, master-time budgets, frame duration, and modeled pause stop semantics without changing declarations."
result: pass
source: automated
summary_file: 12-18-SUMMARY.md
coverage_id: CGB-06-HOST-SPEED-CONTRACT
evidence: ["cgb_native_guide_contract", "cgb_native_guide_contract_missing_selftest", "cgb_consumer_symbol_coverage", "cgb_consumer_symbol_coverage_selftest"]

### 66. Release, preview, cartridge, and RTC evidence docs state the implemented double-speed behavior and retain HDMA, mode-3, hardware, and corpus limitations.
expected: "Release, preview, cartridge, and RTC evidence docs state the implemented double-speed behavior and retain HDMA, mode-3, hardware, and corpus limitations."
result: pass
source: automated
summary_file: 12-18-SUMMARY.md
coverage_id: CGB-06-PUBLIC-DOCS-STALE-CLAIMS
evidence: ["cgb_speed_docs_no_stale_claims", "cgb_speed_docs_no_stale_claims_mutated", "mbc3_rtc_evidence_ledger_names", "mbc3_rtc_evidence_ledger_selftest"]

### 67. The published AGE summary distinguishes its two passing cases from eleven expected failures and records the corrected M28 mode-0 versus DIV sensitivity without a hardware claim.
expected: "The published AGE summary distinguishes its two passing cases from eleven expected failures and records the corrected M28 mode-0 versus DIV sensitivity without a hardware claim."
result: pass
source: automated
summary_file: 12-18-SUMMARY.md
coverage_id: CGB-06-AGE-EVIDENCE-SCOPE
evidence: ["cgb_speed_dispositions", "cgb_speed_dispositions_mutated", "cgb_speed_dispositions_pinned_by_missing", "age_sensitivity_m28", "age_sensitivity_m28_reference_mutated"]

### 68. The complete local CTest inventory, including both newly registered scanner tests, passes.
expected: "The complete local CTest inventory, including both newly registered scanner tests, passes."
result: pass
source: automated
summary_file: 12-18-SUMMARY.md
coverage_id: CGB-06-FULL-INVENTORY
evidence: ["ctest --test-dir build --output-on-failure --no-tests=error -j8 (897/897)", "summary_coverage", "summary_coverage_selftest"]

### 69. Adopted decisions D-084 through D-095, lessons GB-CGB-008 through 010, and the Phase 12 evidence index are complete with resolving links and bounded evidence claims.
expected: "Adopted decisions D-084 through D-095, lessons GB-CGB-008 through 010, and the Phase 12 evidence index are complete with resolving links and bounded evidence claims."
result: pass
source: automated
summary_file: 12-19-SUMMARY.md
coverage_id: CGB-06-MEMORY
evidence: ["python3 -I .planning/phases/GB-12-cgb-double-speed/verify-closeout-contract.py --self-test"]

### 70. The advisory CGB measurement, DMG digest, AGE and partition timings, mutant build costs, Phase 12 ASan test-duration sum, and qualified GB-CI-004 comparison are recorded from preserved samples and exact hosted logs.
expected: "The advisory CGB measurement, DMG digest, AGE and partition timings, mutant build costs, Phase 12 ASan test-duration sum, and qualified GB-CI-004 comparison are recorded from preserved samples and exact hosted logs."
result: pass
source: automated
summary_file: 12-19-SUMMARY.md
coverage_id: CGB-06-BENCHMARK
evidence: ["python3 -I .planning/phases/GB-12-cgb-double-speed/verify-closeout-contract.py --self-test", "CI run 38502094649 at 301f1b05577e6d35a4c3a756ded1ec15a4082c8d: required-native and all required PR jobs passed"]

### 71. The pinned Linux rebuild is byte-identical for all 13 AGE ROMs and both CGB-speed ROMs; tampered AGE reproduction controls pass, and no hardware behavior is inferred.
expected: "The pinned Linux rebuild is byte-identical for all 13 AGE ROMs and both CGB-speed ROMs; tampered AGE reproduction controls pass, and no hardware behavior is inferred."
result: pass
source: automated
summary_file: 12-19-SUMMARY.md
coverage_id: CGB-06-FIXTURE-RECEIPTS
evidence: ["CI fixture-reproduction run 38502094682, job 115651190879", "age_repro_compare_tampered", "age_repro_selfcheck_tampered"]

### 72. The Windows required-test filter excludes only the 12 known WIN32 Bash-only tests; it preserves unrelated tests and still rejects a missing required test.
expected: "The Windows required-test filter excludes only the 12 known WIN32 Bash-only tests; it preserves unrelated tests and still rejects a missing required test."
result: pass
source: automated
summary_file: 12-19-SUMMARY.md
coverage_id: CGB-06-WINDOWS-INVENTORY
evidence: ["bash .github/scripts/verify-test-inventory.sh --self-test", "CI run 38502094649: native-windows-x64 and required-native passed"]

### 73. API coverage is explicitly declared, all plan summaries pass the machine-readable coverage schema, and state points to Phase 12 verification before any Phase 13 entry.
expected: "API coverage is explicitly declared, all plan summaries pass the machine-readable coverage schema, and state points to Phase 12 verification before any Phase 13 entry."
result: pass
source: automated
summary_file: 12-19-SUMMARY.md
coverage_id: CGB-06-COVERAGE-AND-HANDOFF
evidence: ["gsd_run check api-coverage.verify-pre .planning/phases/GB-12-cgb-double-speed", "summary_coverage", "summary_coverage_selftest", "python3 -I .planning/phases/GB-12-cgb-double-speed/verify-closeout-contract.py --self-test"]

## Summary

total: 73
passed: 73
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps

[none]
