---
status: complete
phase: GB-17-native-save-state-core
source: 17-01-SUMMARY.md, 17-02-SUMMARY.md, 17-03-SUMMARY.md, 17-04-SUMMARY.md, 17-05-SUMMARY.md, 17-06-SUMMARY.md, 17-07-SUMMARY.md, 17-08-SUMMARY.md, 17-09-SUMMARY.md, 17-10-SUMMARY.md, 17-11-SUMMARY.md
started: 2026-10-31T18:45:29.072409+00:00
updated: 2026-10-31T18:45:29.072409+00:00
---

## Automated Evidence

Reconciled during the v0.3 milestone audit on 2026-10-31, without replaying Phase 17 execution or changing its SUMMARYs or boundary verification. The 11 original SUMMARYs contain 57 fully automated coverage entries; all retain their criterion and original immutable evidence below. The missing closure record was an audit bookkeeping gap, not an unimplemented state API.

Final-head configure/build/install and the full CTest stream at 18a487a3c88097dfb53d0c39e3b4200aaf4bd7ae passed 1707/1707, with zero failures or skips (build/milestone-audit-v03/commands.json and ctest.xml). This includes state continuation, refusal, horizon, canonical/platform pin, inventory/global, fuzz, installed consumer and inherited release/performance controls. A stale configure-time state-fuzz revision from the earlier boundary was rejected first; reconfiguration fixed metadata without changing a source or weakening a test. The approval self-test passed with its temporary Git worktree capability enabled.

The source paths src/include/tests/.github/docs are unchanged from the qualified Phase 19 boundary B=9a25eb92d842fc49d6cc554dabcd19d8a9ae0605 through the audited HEAD. Fresh read-only GitHub observation confirms main CI at B completed successfully, including native Linux/macOS/Windows and Linux sanitizer lanes. The historical Phase 17 pending-CI note is superseded by its continuation's exact-head green PR130 observation and later source-qualified gates; no old VERIFICATION digest was rewritten. D-103 preserves boundary reports and uses one final-head suite.

No hardware, perceptual output, cross-version state migration, live Playstead or new release claim is added. No human checkpoint, retry renewal, new phase or milestone is authorized. The agent completes the audit and stops before owner-selected milestone closeout.

## Current Test

[testing complete]

## Tests

### 1. The installed C and C++ clients compile against all three state APIs, freeze error values 0 through 27, and exercise size, save and load behavior.
expected: "The installed C and C++ clients compile against all three state APIs, freeze error values 0 through 27, and exercise size, save and load behavior."
result: pass
source: automated
summary_file: 17-01-SUMMARY.md
coverage_id: D1
evidence: ["ctest --test-dir build -R '^(installed_consumer_(c|cpp)|preview_package_smoke)$' --output-on-failure --no-tests=error at 04e37bcc0786893f26d26ee78a71673b87546e64"]

### 2. Malformed and mismatched states return typed errors without mutating the destination or writing poisoned outputs; size and tail bounds are preserved.
expected: "Malformed and mismatched states return typed errors without mutating the destination or writing poisoned outputs; size and tail bounds are preserved."
result: pass
source: automated
summary_file: 17-01-SUMMARY.md
coverage_id: D2
evidence: ["installed_consumer_c and installed_consumer_cpp refusal/no-write controls at 04e37bcc0786893f26d26ee78a71673b87546e64", "state_size_bound, state_audio_bound and state_format_contract at immutable source 04e37bcc0786893f26d26ee78a71673b87546e64"]

### 3. A running non-default DMG instance saves, resets and loads through the installed package, then matches uninterrupted future run results, PCM and canonical bytes.
expected: "A running non-default DMG instance saves, resets and loads through the installed package, then matches uninterrupted future run results, PCM and canonical bytes."
result: pass
source: automated
summary_file: 17-01-SUMMARY.md
coverage_id: D3
evidence: ["state_tracer --rev e9a13af264f02ca9a0e8c4a1e75a5e568ee1ee14; state_bytes=189176, prefix_audio=572, future_audio=1144"]

### 4. The qualified instance inventory and writable-global scan reject seeded missing-treatment, nested-field and global mutants.
expected: "The qualified instance inventory and writable-global scan reject seeded missing-treatment, nested-field and global mutants."
result: pass
source: automated
summary_file: 17-01-SUMMARY.md
coverage_id: D4
evidence: ["state_inventory, state_inventory_controls, state_globals, state_globals_controls and state_precodec_gate at 04e37bcc0786893f26d26ee78a71673b87546e64"]

### 5. The documented GBBS header, CRC, descriptor size and caller ownership contract match the implementation; an altered magic claim is rejected.
expected: "The documented GBBS header, CRC, descriptor size and caller ownership contract match the implementation; an altered magic claim is rejected."
result: pass
source: automated
summary_file: 17-01-SUMMARY.md
coverage_id: D5
evidence: ["state_format_contract at immutable source 04e37bcc0786893f26d26ee78a71673b87546e64; docs_control=pass, version_controls=8, CRC=CBF43926"]

### 6. Git-less source archives configure and build as unqualified while state evidence rejects absent or unresolved immutable revisions; a selected tracer regenerates its receipt before use.
expected: "Git-less source archives configure and build as unqualified while state evidence rejects absent or unresolved immutable revisions; a selected tracer regenerates its receipt before use."
result: pass
source: automated
summary_file: 17-01-SUMMARY.md
coverage_id: D6
evidence: ["At immutable source 6b69a3579fd0f6e89b47ca4942954a1596e24dfb, state_revision_controls and acceptance_dense_input_controls passed; the archive core compiled with GBB_BUILD_REVISION=unknown and GBB_BUILD_QUALIFIED=0.", "After deleting state-precodec-proof.json, ctest --test-dir build -R '^state_tracer$' -j8 --output-on-failure --no-tests=error ran state_precodec_gate first and passed 2/2 at 6b69a3579fd0f6e89b47ca4942954a1596e24dfb."]

### 7. Every core function has an accurate model gate; the full CGB probe/load matrix still covers accepted and rejected headers, while the parity harness fits its test budget.
expected: "Every core function has an accurate model gate; the full CGB probe/load matrix still covers accepted and rejected headers, while the parity harness fits its test budget."
result: pass
source: automated
summary_file: 17-01-SUMMARY.md
coverage_id: D7
evidence: ["At immutable source e9a13af264f02ca9a0e8c4a1e75a5e568ee1ee14, the model-gate suite and all real-file negative controls passed 12/12; model_gates_selftest counted 235 functions with no upper cap.", "At immutable source e9a13af264f02ca9a0e8c4a1e75a5e568ee1ee14, test_budget and test_budget_controls passed 2/2; state CTests use 30s normal limits, except the installed tracer at 60s.", "Parallel CTest selection passed 26/26 at e9a13af264f02ca9a0e8c4a1e75a5e568ee1ee14, including cgb_probe_parity in 9.46s; it asserts >100,000 entries and calls the real loader for every entry."]

### 8. Hosted native builds inspect writable storage by object section across Mach-O, GNU/LLVM ELF and COFF, accept const relocation tables, retain external/static/TLS global controls, and compile perf probes with per-revision validated release components.
expected: "Hosted native builds inspect writable storage by object section across Mach-O, GNU/LLVM ELF and COFF, accept const relocation tables, retain external/static/TLS global controls, and compile perf probes with per-revision validated release components."
result: pass
source: automated
summary_file: 17-01-SUMMARY.md
coverage_id: D8
evidence: ["At immutable commit 38a86f212093033a9541f1fb0fb681c21f6986c7, state_globals_controls passed synthetic Mach-O/GNU-ELF/LLVM-ELF/COFF cases, including const relocations, TLS globals, ASan metadata and an ordinary ASan-name lookalike; the compiler-generated Mach-O ASan fixture retained real writable globals.", "The focused CTest selection passed 7/7 at 38a86f212093033a9541f1fb0fb681c21f6986c7; state_precodec_gate wrote a receipt bound to that commit with negative_controls=pass, and its fixture ran before state_tracer.", "run-perf-gate.sh --attribution-dry-run passed for immutable source 38a86f212093033a9541f1fb0fb681c21f6986c7 and historical v0.2.0 ab301aa69b1f085050fd66bf7b1378863a0821f2; each CMake project version matched its immutable CMakeLists.txt and passed cmake/StateVersion.cmake validation."]

### 9. State evidence locates Windows executables and multi-config artifacts, and the installed tracer carries sanitizer runtime link flags when its core was instrumented.
expected: "State evidence locates Windows executables and multi-config artifacts, and the installed tracer carries sanitizer runtime link flags when its core was instrumented."
result: pass
source: automated
summary_file: 17-01-SUMMARY.md
coverage_id: D9
evidence: ["At checker commit dbff3baca61aaa1b9ce4d3fee40a5486b4b2648f, Windows .exe, single/multi-config selection, ambiguity refusal, missing-artifact refusal, and sanitizer-option positive/negative controls pass; state_precodec_gate and state_tracer pass directly in an independent normal Ninja build with a receipt bound to that commit.", "The checker read GABBABOY_ENABLE_SANITIZERS=ON from build/17-03-followup-asan/CMakeCache.txt and returned -fsanitize=address,undefined. In the existing x86-64 Linux tool image, a client linked and ran against that actual instrumented archive (state_bytes=189176); omitting the flags failed on __ubsan_handle_shift_out_of_bounds."]

### 10. Strong cached ROM identity refuses same-title, same-size content changes and keeps failed replacement transactional; mapper/profile/mode state loads continue deterministically.
expected: "Strong cached ROM identity refuses same-title, same-size content changes and keeps failed replacement transactional; mapper/profile/mode state loads continue deterministically."
result: pass
source: automated
summary_file: 17-02-SUMMARY.md
coverage_id: D1
evidence: ["state_identity and state_codec_matrix at immutable revision 7fb9587fed2edca14db3dbb4c66a6ff87fadffb5; SHA-256 empty/abc/multi-block vectors, generated CRC32 collision pair, hash-count controls, and all 15 mapper/profile/mode categories."]

### 11. Accepted states resave byte-identically across canonical queue, audio, palette, mapper, and in-flight device boundaries, and keep the fixed state size.
expected: "Accepted states resave byte-identically across canonical queue, audio, palette, mapper, and in-flight device boundaries, and keep the fixed state size."
result: pass
source: automated
summary_file: 17-02-SUMMARY.md
coverage_id: D2
evidence: ["state_canonical, state_codec_matrix, state_audio_bound, and state_size_bound at immutable revision 7fb9587fed2edca14db3dbb4c66a6ff87fadffb5."]

### 12. CRC-recomputed semantic-invalid state values are rejected without mutating the destination; field relationships and hardware-domain bounds are checked before apply.
expected: "CRC-recomputed semantic-invalid state values are rejected without mutating the destination; field relationships and hardware-domain bounds are checked before apply."
result: pass
source: automated
summary_file: 17-02-SUMMARY.md
coverage_id: D3
evidence: ["state_semantic_bounds and state_override_isolation at immutable revision 7fb9587fed2edca14db3dbb4c66a6ff87fadffb5.", "verify-state-mutants.py --rev 7fb9587fed2edca14db3dbb4c66a6ff87fadffb5 killed normalization-on-load, skipped-cross-field-check, big-endian wire encoding, and test-override-leakage mutants at their named semantic guards."]

### 13. All 198 serialized fields are independently censused against the format ledger, with omitted-row and width mutation controls.
expected: "All 198 serialized fields are independently censused against the format ledger, with omitted-row and width mutation controls."
result: pass
source: automated
summary_file: 17-02-SUMMARY.md
coverage_id: D4
evidence: ["state_field_census and state_field_census_controls at immutable revision 7fb9587fed2edca14db3dbb4c66a6ff87fadffb5; direct immutable census reports 198 rows."]

### 14. The documented wire bounds and state test registration are checked alongside the production tracer and immutable revision gates.
expected: "The documented wire bounds and state test registration are checked alongside the production tracer and immutable revision gates."
result: pass
source: automated
summary_file: 17-02-SUMMARY.md
coverage_id: D5
evidence: ["state_format_contract, state_inventory, state_inventory_controls, state_globals, state_globals_controls, state_revision_controls, state_precodec_gate, and state_tracer at immutable revision 7fb9587fed2edca14db3dbb4c66a6ff87fadffb5."]

### 15. A fresh compatibility-mode target resumes the saved RAM, raw RTC representation, palette, future audio, frame output, and canonical state bytes.
expected: "A fresh compatibility-mode target resumes the saved RAM, raw RTC representation, palette, future audio, frame output, and canonical state bytes."
result: pass
source: automated
summary_file: 17-03-SUMMARY.md
coverage_id: GB17-03-01
evidence: ["state_rtc_palette and state_tracer at immutable implementation revision 30f2151769a770f13853bf4a292c196e3ee85c23; the tracer's precodec receipt was generated before execution."]

### 16. Battery generation changes only for changed projected battery bytes, rumble observers track line transitions, and both counters saturate without entering the wire state.
expected: "Battery generation changes only for changed projected battery bytes, rumble observers track line transitions, and both counters saturate without entering the wire state."
result: pass
source: automated
summary_file: 17-03-SUMMARY.md
coverage_id: GB17-03-02
evidence: ["state_observers at immutable implementation revision 30f2151769a770f13853bf4a292c196e3ee85c23 checks equal lazy RTC projections, changed and repeated RAM/RTC loads, separate receivers, rumble transitions, serialized-counter immunity, and saturation.", "The 11 state observer mutants and their unrelated passing controls all passed at immutable implementation revision 30f2151769a770f13853bf4a292c196e3ee85c23."]

### 17. Every refused load preserves the complete destination and owned buffers; error precedence, every truncated prefix, short-save atomicity, and exact output extent are checked.
expected: "Every refused load preserves the complete destination and owned buffers; error precedence, every truncated prefix, short-save atomicity, and exact output extent are checked."
result: pass
source: automated
summary_file: 17-03-SUMMARY.md
coverage_id: GB17-03-03
evidence: ["state_refusal, state_refusal_controls, and state_semantic_bounds at immutable implementation revision 30f2151769a770f13853bf4a292c196e3ee85c23; the refusal case checks all 197,368 truncated lengths for its fixture.", "Apply-before-validation, invalid-content counter mutation, short-save prefix write, and trailing save write mutants were each rejected by the intended whole-state or output assertion; all four unrelated controls passed at revision 30f2151769a770f13853bf4a292c196e3ee85c23."]

### 18. State size, save, and load make no heap calls or ROM hashes, size/save remain observationally pure, and independent receiving instances keep separate state.
expected: "State size, save, and load make no heap calls or ROM hashes, size/save remain observationally pure, and independent receiving instances keep separate state."
result: pass
source: automated
summary_file: 17-03-SUMMARY.md
coverage_id: GB17-03-04
evidence: ["The immutable state_purity probe at revision 30f2151769a770f13853bf4a292c196e3ee85c23 reports heap_calls=0 and hashes=0 for success and error paths; its allocator/hash hooks pass the sensitivity control.", "Allocation-in-save, hash-in-save, and save-tail-overwrite mutants were rejected by state_purity while all three state_purity_controls passed at revision 30f2151769a770f13853bf4a292c196e3ee85c23.", "state_globals and state_globals_controls pass at immutable implementation revision 30f2151769a770f13853bf4a292c196e3ee85c23."]

### 19. Every native run wrapper and independently advancing branch respects the shared 2^62 horizon while retaining transactional refusal and valid timer sentinel behavior.
expected: "Every native run wrapper and independently advancing branch respects the shared 2^62 horizon while retaining transactional refusal and valid timer sentinel behavior."
result: pass
source: automated
summary_file: 17-04-SUMMARY.md
coverage_id: D1
evidence: ["state_horizon, state_horizon_wrappers, and state_horizon_sentinels at immutable revision f64a798539b517604db3c522e689f56416e7df5c.", "Affected CGB speed-switch, HDMA, partition, model-gate, and test-budget selection passed 126/126 at immutable revision f64a798539b517604db3c522e689f56416e7df5c."]

### 20. Ordinary event and borrowed-span admission is capped without partial mutation, equal-time ordering changes, or loss of save/load closure.
expected: "Ordinary event and borrowed-span admission is capped without partial mutation, equal-time ordering changes, or loss of save/load closure."
result: pass
source: automated
summary_file: 17-04-SUMMARY.md
coverage_id: D2
evidence: ["state_horizon_events, state_horizon_closure, state_canonical, and state_audio_bound at immutable revision f64a798539b517604db3c522e689f56416e7df5c; the fixture-linked closure gate covered all 5,644 audio-phase/ring-head combinations."]

### 21. Every independent horizon/admission guard has a witnessed immutable semantic mutation and unrelated codec control, including under the project sanitizer configuration.
expected: "Every independent horizon/admission guard has a witnessed immutable semantic mutation and unrelated codec control, including under the project sanitizer configuration."
result: pass
source: automated
summary_file: 17-04-SUMMARY.md
coverage_id: D3
evidence: ["verify-state-horizon.py at immutable revision 95302423da0aa4bd7ce060621c4b262e28675b2a: all 14 semantic mutants exit 1 and controls exit 0 in normal and sanitizer=true runs; sanitizer self-test passes with control leak detection enabled."]

### 22. All admitted corpus cases fork through public save/load calls into fresh poisoned targets and compare future outputs, metadata, observer projections, and final canonical bytes.
expected: "All admitted corpus cases fork through public save/load calls into fresh poisoned targets and compare future outputs, metadata, observer projections, and final canonical bytes."
result: pass
source: automated
summary_file: 17-05-SUMMARY.md
coverage_id: D1
evidence: ["CTest state_fork_matrix, all 16 matrix shards, and state_slice_invariance at immutable revision a8bcce6018d5a5a404381c6095b9d1456ccc4554; included in the named fork/census/mutation selection (38/38 passed)."]

### 23. Every save-boundary category and every serialized field has a discriminating witness or exact tested treatment, with model applicability and missing-category controls.
expected: "Every save-boundary category and every serialized field has a discriminating witness or exact tested treatment, with model applicability and missing-category controls."
result: pass
source: automated
summary_file: 17-05-SUMMARY.md
coverage_id: D2
evidence: ["CTest state_fork_census and state_fork_census_controls at immutable revision a8bcce6018d5a5a404381c6095b9d1456ccc4554; 14/14 categories and 198/198 fields, including negative controls, passed."]

### 24. Every declared serialized-field omission is exercised on the designated poisoned target restore and rejected by its named canonical or continuation discrepancy; absent/unexercised manifest controls fail.
expected: "Every declared serialized-field omission is exercised on the designated poisoned target restore and rejected by its named canonical or continuation discrepancy; absent/unexercised manifest controls fail."
result: pass
source: automated
summary_file: 17-05-SUMMARY.md
coverage_id: D3
evidence: ["CTest state_fork_mutants, all 16 omission shards, state_fork_mutant_controls, and summary gate at immutable revision a8bcce6018d5a5a404381c6095b9d1456ccc4554; included in the 38/38 passing selection."]

### 25. Reachable pulse/noise timer values round-trip with equal continuation; CRC-valid above-bound values are rejected without receiver mutation.
expected: "Reachable pulse/noise timer values round-trip with equal continuation; CRC-valid above-bound values are rejected without receiver mutation."
result: pass
source: automated
summary_file: 17-05-SUMMARY.md
coverage_id: D4
evidence: ["CTest state_apu_pulse_timer, state_apu_noise_timer, state_semantic_bounds, state_refusal, and state_audio_bound at immutable revision a8bcce6018d5a5a404381c6095b9d1456ccc4554; targeted state/APU/audio selection passed 13/13.", "cmake --preset phase1 && cmake --build --preset phase1 at immutable revision a8bcce6018d5a5a404381c6095b9d1456ccc4554; build passed."]

### 26. The compiled codec emits exact canonical bytes for all pinned hardware-mode fixtures, and an altered output or undisposed compatibility change is rejected.
expected: "The compiled codec emits exact canonical bytes for all pinned hardware-mode fixtures, and an altered output or undisposed compatibility change is rejected."
result: pass
source: automated
summary_file: 17-06-SUMMARY.md
coverage_id: D1
evidence: ["CTest state_portable_pins and state_pin_controls at source fdf7b2ac91d5db24f77725cc87588d3c57e26eb7, checked against immutable mainline base 5ca03b394f2a3e0640f69d94e5eda5622753b36c and Phase 17 entry base f192100c4cc89427575f32785a4221bfca7337d7; both selections passed 2/2.", "verify-state-pins.py --self-test at immutable source fdf7b2ac91d5db24f77725cc87588d3c57e26eb7; 14 compatibility, altered-pin, receipt, and immutable-revision controls passed."]

### 27. The real fuzz dispatcher reaches semantic invalid-state checks, whole-instance refusal, and accepted-state resave/closure with named witnesses.
expected: "The real fuzz dispatcher reaches semantic invalid-state checks, whole-instance refusal, and accepted-state resave/closure with named witnesses."
result: pass
source: automated
summary_file: 17-06-SUMMARY.md
coverage_id: D2
evidence: ["CTest state_load_fuzz and state_fuzz_controls at immutable source 0521a33d483211725118f1b117b8e1df371ddb94; 2/2 passed.", "The observer-only mutant command exited 1 with `refused state load changed opaque instance bytes or excluded observers`; its unrelated state_control accepted-state-closure control exited 0.", "run-bounded-fuzz.sh --self-test passed; local Clang libFuzzer runtime was unavailable, so the live campaign remains hosted-required."]

### 28. Existing Linux, macOS, and Windows native jobs require immutable event-base pin checks, retain platform receipts, and keep the installed consumer route.
expected: "Existing Linux, macOS, and Windows native jobs require immutable event-base pin checks, retain platform receipts, and keep the installed consumer route."
result: pass
source: automated
summary_file: 17-06-SUMMARY.md
coverage_id: D3
evidence: ["verify-workflow-policy.py --check passed and --self-test passed at immutable source fdf7b2ac91d5db24f77725cc87588d3c57e26eb7 with 271 negative and 4 positive controls, including missing OS, own-source base, event.before bypass, ignored pin target, and dropped installed inventory gate.", "Local compiled pin checks against both immutable bases passed and wrote three-fixture receipts; these single-host runs do not qualify cross-platform equality."]

### 29. Relocated installed C/C++ consumers and the preview package smoke continue to execute beside the state pin test.
expected: "Relocated installed C/C++ consumers and the preview package smoke continue to execute beside the state pin test."
result: pass
source: automated
summary_file: 17-06-SUMMARY.md
coverage_id: D4
evidence: ["CTest preview_package_smoke, installed_consumer_c, installed_consumer_cpp, and state_portable_pins at immutable source fdf7b2ac91d5db24f77725cc87588d3c57e26eb7; 4/4 passed after install."]

### 30. A valid triggered paired timing receipt succeeds as advisory through the producer, verifier, reuse, and release evidence consumer while source and workload binding remain enforced.
expected: "A valid triggered paired timing receipt succeeds as advisory through the producer, verifier, reuse, and release evidence consumer while source and workload binding remain enforced."
result: pass
source: automated
summary_file: 17-07-SUMMARY.md
coverage_id: RM-026
evidence: ["411889324953d20bb3c88c516d3826bc6dfe98bd: ctest --test-dir build/phase17-07 -R '^perf_' --output-on-failure --no-tests=error (11/11 passed)", "411889324953d20bb3c88c516d3826bc6dfe98bd: python3 -I tests/scripts/verify-v02-delivery.py --self-test (7 positives, 48 rejected controls, 2 real-owner rejections)"]

### 31. Deterministic Ir ratios and native realtime remain blocking, both repeats bind output digest and consumption, and a limit change cannot be approved from live policy or ordinary timing evidence.
expected: "Deterministic Ir ratios and native realtime remain blocking, both repeats bind output digest and consumption, and a limit change cannot be approved from live policy or ordinary timing evidence."
result: pass
source: automated
summary_file: 17-07-SUMMARY.md
coverage_id: RM-029
evidence: ["7be6885: python3 -I tests/scripts/verify-perf-gate.py --self-test-limit-ratchet (6/6 passed, 5 controls)", "7be6885: python3 -I tests/scripts/verify-perf-gate.py --self-test-repeat-controls (4/4 passed, 3 controls)", "411889324953d20bb3c88c516d3826bc6dfe98bd: ctest --test-dir build/phase17-07 -R '^perf_' --output-on-failure --no-tests=error (11/11 passed)"]

### 32. Release workflows consume advisory timing while retaining independent deterministic gates and the existing source-specific evidence checks.
expected: "Release workflows consume advisory timing while retaining independent deterministic gates and the existing source-specific evidence checks."
result: pass
source: automated
summary_file: 17-07-SUMMARY.md
coverage_id: release-advisory-policy
evidence: ["411889324953d20bb3c88c516d3826bc6dfe98bd: python3 -I .github/scripts/verify-workflow-policy.py --check (residual_write_jobs=5)", "411889324953d20bb3c88c516d3826bc6dfe98bd: python3 -I .github/scripts/verify-workflow-policy.py --self-test (266 negative controls, 4 positive controls)", "411889324953d20bb3c88c516d3826bc6dfe98bd: bash .github/scripts/verify-release-gates.sh --self-test (exit 0)"]

### 33. The historical performance disclosure in a generated support ledger is rendered by the actual ledger renderer from source-bound validated input; the tagged ledgers are exact generator output with v0.2.1 equal to its tag blob; and input omission, an altered historical value, unbound sources, a handwritten-success bypass and a tagged-target rewrite are each rejected with their own diagnostic.
expected: "The historical performance disclosure in a generated support ledger is rendered by the actual ledger renderer from source-bound validated input; the tagged ledgers are exact generator output with v0.2.1 equal to its tag blob; and input omission, an altered historical value, unbound sources, a handwritten-success bypass and a tagged-target rewrite are each rejected with their own diagnostic."
result: pass
source: automated
summary_file: 17-08-SUMMARY.md
coverage_id: RM-028-generator
evidence: ["ada8050e430393526d11a74697b667850bec8fa1: ctest --test-dir build -R '^release_disclosure_(generator|controls)$' --output-on-failure --no-tests=error (2/2 passed; generator ledgers=2 tagged=1, controls positives=4 controls=19)", "ada8050e430393526d11a74697b667850bec8fa1: python3 -I tests/scripts/verify-support-ledger.py --self-test (exit 0; includes the synthetic-receipt writer round trip, the generated block and the tagged-target refusal)"]

### 34. An active version-window record is judged from Git objects at a resolved revision; body overwrite, a stale head, a changed source, release-note or generator-input path, a digest not recomputed after regeneration, a moved main and review or rehearsal identity mismatches are rejected, a regenerated and revalidated exact head passes, and the inactive record cannot claim a freeze or readiness.
expected: "An active version-window record is judged from Git objects at a resolved revision; body overwrite, a stale head, a changed source, release-note or generator-input path, a digest not recomputed after regeneration, a moved main and review or rehearsal identity mismatches are rejected, a regenerated and revalidated exact head passes, and the inactive record cannot claim a freeze or readiness."
result: pass
source: automated
summary_file: 17-08-SUMMARY.md
coverage_id: RM-028-window
evidence: ["ada8050e430393526d11a74697b667850bec8fa1: ctest --test-dir build -R '^release_window_(contract|controls)$' --output-on-failure --no-tests=error (2/2 passed; controls positives=8 controls=27)", "ada8050e430393526d11a74697b667850bec8fa1: python3 -I tests/scripts/verify-version-window.py --self-test (exit 0; includes the CLI over the frozen head with an intact and an overwritten body)"]

### 35. The release-please workflow judges the regenerated version PR through a fatal post-regeneration gate, and the workflow policy rejects a missing or reordered gate, a skipped or masked judge, write authority, a PR-supplied checker, shallow history, a path-filtered trigger and any release-please path exclusion beyond the existing workflow and script paths.
expected: "The release-please workflow judges the regenerated version PR through a fatal post-regeneration gate, and the workflow policy rejects a missing or reordered gate, a skipped or masked judge, write authority, a PR-supplied checker, shallow history, a path-filtered trigger and any release-please path exclusion beyond the existing workflow and script paths."
result: pass
source: automated
summary_file: 17-08-SUMMARY.md
coverage_id: RM-028-production-route
evidence: ["ada8050e430393526d11a74697b667850bec8fa1: python3 -I .github/scripts/verify-workflow-policy.py --check (residual_write_jobs=5)", "ada8050e430393526d11a74697b667850bec8fa1: python3 -I .github/scripts/verify-workflow-policy.py --self-test (286 negative controls including 20 new window controls, 4 positive controls)"]

### 36. The new generator, window and policy changes leave every existing test green, including the support-ledger, adoption, freeze, test-budget and summary-coverage checks.
expected: "The new generator, window and policy changes leave every existing test green, including the support-ledger, adoption, freeze, test-budget and summary-coverage checks."
result: pass
source: automated
summary_file: 17-08-SUMMARY.md
coverage_id: phase17-08-no-regression
evidence: ["ada8050e430393526d11a74697b667850bec8fa1: ctest --test-dir build -j14 --output-on-failure --no-tests=error after cmake --preset phase1 (1486/1486 passed)"]

### 37. The production attach, manifest, final-gate, publish-decision and retry steps run from the extracted lifecycle script that release.yml calls, in a non-git attacher workspace with GH_REPO explicit and no repository fallback, against a bounded transport that records the publish command as a decision only. A first attempt uploads exactly the four evidence assets, the manifest and the two final receipts and records one decision; a retry with different regenerated sidecars reuses the identical attached bytes, uploads nothing and records one decision.
expected: "The production attach, manifest, final-gate, publish-decision and retry steps run from the extracted lifecycle script that release.yml calls, in a non-git attacher workspace with GH_REPO explicit and no repository fallback, against a bounded transport that records the publish command as a decision only. A first attempt uploads exactly the four evidence assets, the manifest and the two final receipts and records one decision; a retry with different regenerated sidecars reuses the identical attached bytes, uploads nothing and records one decision."
result: pass
source: automated
summary_file: 17-09-SUMMARY.md
coverage_id: RM-028-lifecycle-replay
evidence: ["32321eda15f05d85608c205ffa0dbe457501f8bc: ctest --test-dir build -R '^release_lifecycle_replay$' --output-on-failure --no-tests=error (passed; modes=7 publish_decisions=2 live_mutations=0 uploads=7 calls=54)", "32321eda15f05d85608c205ffa0dbe457501f8bc: python3 -I tests/scripts/verify-release-lifecycle.py --self-test (controls positives=4 controls=85; wrong GH_REPO, missing GH_REPO fallback, skipped attach, removed final gate, unexpected endpoint and a non-intercepted publish command each refused with the intended diagnostic)"]

### 38. Sanitized, bounded, digest-bound captures of real GitHub run, job, artifact, check-run, pull-request, release and asset responses with documented endpoints, API version and transform drive the production source proof, draft asset-set check, recovery decision and final-receipt gate. Stale head, wrong App id or slug, check-run url or html_url of another repository or lookalike prefix, a missing check_suite, the old repository-only shape, altered and replaced bytes, stale identities, partial, duplicated and unknown assets, a moved tag, concurrent runs and duplicate, malformed, path-like or unterminated SHA256SUMS lines are each refused after the real shapes pass.
expected: "Sanitized, bounded, digest-bound captures of real GitHub run, job, artifact, check-run, pull-request, release and asset responses with documented endpoints, API version and transform drive the production source proof, draft asset-set check, recovery decision and final-receipt gate. Stale head, wrong App id or slug, check-run url or html_url of another repository or lookalike prefix, a missing check_suite, the old repository-only shape, altered and replaced bytes, stale identities, partial, duplicated and unknown assets, a moved tag, concurrent runs and duplicate, malformed, path-like or unterminated SHA256SUMS lines are each refused after the real shapes pass."
result: pass
source: automated
summary_file: 17-09-SUMMARY.md
coverage_id: RM-028-captured-shapes
evidence: ["32321eda15f05d85608c205ffa0dbe457501f8bc: python3 -I tests/scripts/verify-release-lifecycle.py --self-test && python3 -I .github/scripts/verify-release-source-proof.py --self-test (7 captured-shape defects rejected; capture contract and sanitizer controls pass)", "32321eda15f05d85608c205ffa0dbe457501f8bc: bash .github/scripts/verify-release-gates.sh --self-test (exit 0; duplicate, malformed, path-like and unterminated SHA256SUMS and the attached-evidence check controls)"]

### 39. On a retry the attached evidence is downloaded and judged independently of the regenerated copies before any copy is replaced, and only identical qualified bytes are then reused. Nine tampered or stale attachment forms are refused before reuse and before the recovery decision; a removed check lets the altered attachment reach the recovery decision; a check moved after the reuse destroys the regenerated evidence before it refuses; downstream owner, manifest and asset-set refusals precede the publish decision. The workflow policy requires the lifecycle wiring and this order.
expected: "On a retry the attached evidence is downloaded and judged independently of the regenerated copies before any copy is replaced, and only identical qualified bytes are then reused. Nine tampered or stale attachment forms are refused before reuse and before the recovery decision; a removed check lets the altered attachment reach the recovery decision; a check moved after the reuse destroys the regenerated evidence before it refuses; downstream owner, manifest and asset-set refusals precede the publish decision. The workflow policy requires the lifecycle wiring and this order."
result: pass
source: automated
summary_file: 17-09-SUMMARY.md
coverage_id: RM-028-retry-order
evidence: ["32321eda15f05d85608c205ffa0dbe457501f8bc: python3 -I tests/scripts/verify-release-lifecycle.py --self-test (retry tamper, ordering mutant and downstream controls)", "32321eda15f05d85608c205ffa0dbe457501f8bc: python3 -I .github/scripts/verify-workflow-policy.py --check && python3 -I .github/scripts/verify-workflow-policy.py --self-test (300 negative controls including 14 lifecycle mutants, 4 positive controls)"]

### 40. The extraction, the stricter final-receipt parse and the new tests leave every existing test green, including the test inventory, test budget and summary coverage checks.
expected: "The extraction, the stricter final-receipt parse and the new tests leave every existing test green, including the test inventory, test budget and summary coverage checks."
result: pass
source: automated
summary_file: 17-09-SUMMARY.md
coverage_id: phase17-09-no-regression
evidence: ["32321eda15f05d85608c205ffa0dbe457501f8bc: cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 -j8 --output-on-failure --no-tests=error (1488/1488 passed)"]

### 41. Release reuses a rehearsal performance receipt only from the newest successful run that is a push or dispatch of release-rehearsal.yml on rehearsal/<tag> in this repository, whose head is the tagged commit or has the tagged tree proved from git objects, and only through the one artifact that exact run and attempt uploaded. Another workflow, event, conclusion, branch, repository or fork, an unprovable or different tree, a stale newest run behind an older valid run, a repeated or malformed run id, an expired, empty, oversized, renamed, duplicated or foreign-run artifact and a truncated artifact list are each refused with the intended diagnostic after the real captured run and artifact shapes pass. The judge is the trusted revision's copy and the workflow policy pins the selection, the trusted judge, the exact download and refuses write or unlisted API calls in the token step.
expected: "Release reuses a rehearsal performance receipt only from the newest successful run that is a push or dispatch of release-rehearsal.yml on rehearsal/<tag> in this repository, whose head is the tagged commit or has the tagged tree proved from git objects, and only through the one artifact that exact run and attempt uploaded. Another workflow, event, conclusion, branch, repository or fork, an unprovable or different tree, a stale newest run behind an older valid run, a repeated or malformed run id, an expired, empty, oversized, renamed, duplicated or foreign-run artifact and a truncated artifact list are each refused with the intended diagnostic after the real captured run and artifact shapes pass. The judge is the trusted revision's copy and the workflow policy pins the selection, the trusted judge, the exact download and refuses write or unlisted API calls in the token step."
result: pass
source: automated
summary_file: 17-10-SUMMARY.md
coverage_id: RM-030-WR-01-reuse-selection
evidence: ["12e8dbb8e45c7d93b90d14eadd78b042b668b1dc: python3 -I .github/scripts/verify-release-source-proof.py --self-test (54 rehearsal reuse defects rejected on a hand-built shape and again on the captured GitHub run and artifact objects; the CLI proves an equal tree from git objects in a disposable repository)", "12e8dbb8e45c7d93b90d14eadd78b042b668b1dc: python3 -I .github/scripts/verify-workflow-policy.py --check and --self-test (346 negative controls, 4 positive controls including 10 release.yml selection mutants)"]

### 42. The platform manifest is parsed strictly before a name-keyed map is built, so a repeated name, a path-like name, a wrong-length or upper-case digest, a missing key and a non-list asset field are each refused with a named diagnostic. SHA256SUMS wrong-length, upper-case, blank, CRLF and extra-space lines are regression controls beside the earlier duplicate, malformed, path-like and unterminated cases.
expected: "The platform manifest is parsed strictly before a name-keyed map is built, so a repeated name, a path-like name, a wrong-length or upper-case digest, a missing key and a non-list asset field are each refused with a named diagnostic. SHA256SUMS wrong-length, upper-case, blank, CRLF and extra-space lines are regression controls beside the earlier duplicate, malformed, path-like and unterminated cases."
result: pass
source: automated
summary_file: 17-10-SUMMARY.md
coverage_id: RM-030-WR-03-manifest-parse
evidence: ["12e8dbb8e45c7d93b90d14eadd78b042b668b1dc: bash .github/scripts/verify-release-gates.sh --self-test (exit 0; 6 manifest defects and 9 SHA256SUMS defects refused with the intended reason)"]

### 43. Every recorded required context must come from GitHub App id 15368 with slug github-actions at PR time as at release time. A wildcard branch rule still gets the identity check on the run, and a rule that trusts another App or names the id as a string is refused.
expected: "Every recorded required context must come from GitHub App id 15368 with slug github-actions at PR time as at release time. A wildcard branch rule still gets the identity check on the run, and a rule that trusts another App or names the id as a string is refused."
result: pass
source: automated
summary_file: 17-10-SUMMARY.md
coverage_id: RM-030-IN-02-app-identity
evidence: ["12e8dbb8e45c7d93b90d14eadd78b042b668b1dc: bash .github/scripts/verify-release-gates.sh --self-test (4 wildcard-rule run identity defects and 2 branch-rule defects refused; fail-first at 33d157d accepted the wildcard case)"]

### 44. The retry order of 17-09 holds: attached evidence is judged before any regenerated copy is replaced, and the release lifecycle replay still passes with the changed gates and workflow.
expected: "The retry order of 17-09 holds: attached evidence is judged before any regenerated copy is replaced, and the release lifecycle replay still passes with the changed gates and workflow."
result: pass
source: automated
summary_file: 17-10-SUMMARY.md
coverage_id: RM-030-IN-01-retry-recheck
evidence: ["12e8dbb8e45c7d93b90d14eadd78b042b668b1dc: python3 -I tests/scripts/verify-release-lifecycle.py --self-test (positives=4 controls=85) and the release_lifecycle_replay CTest"]

### 45. Both Phase 8 checkers require historical/phase-08-boundary to peel to 96d5eec977bee99a0629499b89c737415e24184c and stop with a retargeted-tag message before any clause is judged. Disposable annotated and lightweight tags retargeted to another commit are refused, a deleted tag is unreadable, an explicit override revision is judged by its clauses alone, and the plain CTests read the literal commit.
expected: "Both Phase 8 checkers require historical/phase-08-boundary to peel to 96d5eec977bee99a0629499b89c737415e24184c and stop with a retargeted-tag message before any clause is judged. Disposable annotated and lightweight tags retargeted to another commit are refused, a deleted tag is unreadable, an explicit override revision is judged by its clauses alone, and the plain CTests read the literal commit."
result: pass
source: automated
summary_file: 17-10-SUMMARY.md
coverage_id: RM-030-WR-02-historical-identity
evidence: ["12e8dbb8e45c7d93b90d14eadd78b042b668b1dc: python3 -I tests/scripts/verify-phase8-closure-contract.py --self-test (rejected_controls=168) and python3 -I tests/scripts/verify-phase8-player-contract.py --self-test (retargeted-tag-x8)", "12e8dbb8e45c7d93b90d14eadd78b042b668b1dc: ctest --preset phase1 -j8 (phase8_closure_contract, phase8_closure_contract_selftest, phase8_closure_contract_wrong_boundary, phase8_player_contract, phase8_player_contract_selftest, phase8_player_contract_wrong_boundary all passed)"]

### 46. Against an immutable base commit, a test-budget allowlist row that is new is refused above 180 s and refused when it cites a reference that already backs a base row, so copying an existing reference cannot grant an unbounded timeout. Existing rows at larger ceilings, a first seeding, two new rows sharing one fresh reference and the shipped allowlist judged against itself stay valid. The base must be a full commit id and is pinned once.
expected: "Against an immutable base commit, a test-budget allowlist row that is new is refused above 180 s and refused when it cites a reference that already backs a base row, so copying an existing reference cannot grant an unbounded timeout. Existing rows at larger ceilings, a first seeding, two new rows sharing one fresh reference and the shipped allowlist judged against itself stay valid. The base must be a full commit id and is pinned once."
result: pass
source: automated
summary_file: 17-10-SUMMARY.md
coverage_id: RM-030-WR-04-budget-new-rows
evidence: ["12e8dbb8e45c7d93b90d14eadd78b042b668b1dc: python3 -I tests/scripts/verify-test-budget.py --self-test (controls=54) and --build-dir build --base main (pass tests=1488 allowlisted=79)"]

### 47. Plan-cap counts canonical and suffixed plan names toward each phase cap, never counts a no-id file such as NN-PLAN-CHECK.md, limits plans that are not gap_closure to the cap minus one reserved slot, rejects a fifth active milestone phase and, with --rev, reads the ROADMAP and plan names from one full commit id with git so a working-tree edit, a later commit and a symbolic name cannot change the verdict.
expected: "Plan-cap counts canonical and suffixed plan names toward each phase cap, never counts a no-id file such as NN-PLAN-CHECK.md, limits plans that are not gap_closure to the cap minus one reserved slot, rejects a fifth active milestone phase and, with --rev, reads the ROADMAP and plan names from one full commit id with git so a working-tree edit, a later commit and a symbolic name cannot change the verdict."
result: pass
source: automated
summary_file: 17-10-SUMMARY.md
coverage_id: RM-030-WR-05-plan-cap
evidence: ["12e8dbb8e45c7d93b90d14eadd78b042b668b1dc: python3 -I tests/scripts/verify-planning-hygiene.py --self-test (controls=77) and --check plan-cap --rev 12e8dbb8e45c7d93b90d14eadd78b042b668b1dc (pass phases=4 plans=18)", "12e8dbb8e45c7d93b90d14eadd78b042b668b1dc: ctest --preset phase1 -j8 (plan_cap, planning_hygiene_controls and no_phase_paths passed)"]

### 48. The nightly red report step has its own 5 minute timeout, reuses an open issue only for the exact title carrying the nightly-red label, creates the label when it is missing, and a dispatch-only dry run skips the replay and records every issue and label write instead of sending it. The production body is executed against a recording gh stand-in over 11 scenarios (an unrelated or prefix title, the exact title under another or no label and a lowest-numbered match among several) and 8 body mutants. This entry does NOT cover the job-level timeout and its ledger row, which wait for a completed report-red run.
expected: "The nightly red report step has its own 5 minute timeout, reuses an open issue only for the exact title carrying the nightly-red label, creates the label when it is missing, and a dispatch-only dry run skips the replay and records every issue and label write instead of sending it. The production body is executed against a recording gh stand-in over 11 scenarios (an unrelated or prefix title, the exact title under another or no label and a lowest-numbered match among several) and 8 body mutants. This entry does NOT cover the job-level timeout and its ledger row, which wait for a completed report-red run."
result: pass
source: automated
summary_file: 17-10-SUMMARY.md
coverage_id: RM-030-IN-03-report-red-body
evidence: ["12e8dbb8e45c7d93b90d14eadd78b042b668b1dc: python3 -I .github/scripts/verify-workflow-policy.py --self-test (19 static nightly mutants plus the 11 scenario and 8 mutant replay)"]

### 49. The HDMA skipped-lane control must be refused for the missing CTest registration of the lane test (and separately of its selftest), a missing inventory case must be refused by name, an unrelated edit still passes, and every remote-evidence control including skipped and reused-run receipts must be refused for its own reason. The perf-gate second repeat digest and consumption controls of 17-07 still pass.
expected: "The HDMA skipped-lane control must be refused for the missing CTest registration of the lane test (and separately of its selftest), a missing inventory case must be refused by name, an unrelated edit still passes, and every remote-evidence control including skipped and reused-run receipts must be refused for its own reason. The perf-gate second repeat digest and consumption controls of 17-07 still pass."
result: pass
source: automated
summary_file: 17-10-SUMMARY.md
coverage_id: RM-030-IN-04-lane-controls
evidence: ["12e8dbb8e45c7d93b90d14eadd78b042b668b1dc: python3 -I tests/scripts/verify-hdma-lane.py --lane-self-test (controls=5) and python3 -I tests/scripts/test_hdma_remote_evidence.py (negative=18)", "12e8dbb8e45c7d93b90d14eadd78b042b668b1dc: python3 -I tests/scripts/verify-perf-gate.py --self-test (controls=33)"]

### 50. The changed checkers, workflow and CTest wiring leave every existing test green, including the test inventory, test budget and summary coverage checks.
expected: "The changed checkers, workflow and CTest wiring leave every existing test green, including the test inventory, test budget and summary coverage checks."
result: pass
source: automated
summary_file: 17-10-SUMMARY.md
coverage_id: phase17-10-no-regression
evidence: ["12e8dbb8e45c7d93b90d14eadd78b042b668b1dc: cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 -j8 --output-on-failure --no-tests=error (1488/1488 passed, 150.5 s)"]

### 51. A deterministic Ir exception is authorized only by a verified OWNER comment on the recorded review issue that is newer than the issue and carries the exact wording derived from the full canonical measurement digest, the accepted cause and its reference, the per-ROM ratio bands and the approved limit. The eight named mutants (non-owner, wrong issue, wrong digest, missing approval text, prefix-only digest, unrecorded issue, comment predating the issue, prefilled owner fields) are each refused for their own reason, further controls refuse an edited cause, limit, band, measurement, revision, association or reference, an unrelated edit still passes, and a refusal writes no file and edits no input.
expected: "A deterministic Ir exception is authorized only by a verified OWNER comment on the recorded review issue that is newer than the issue and carries the exact wording derived from the full canonical measurement digest, the accepted cause and its reference, the per-ROM ratio bands and the approved limit. The eight named mutants (non-owner, wrong issue, wrong digest, missing approval text, prefix-only digest, unrecorded issue, comment predating the issue, prefilled owner fields) are each refused for their own reason, further controls refuse an edited cause, limit, band, measurement, revision, association or reference, an unrelated edit still passes, and a refusal writes no file and edits no input."
result: pass
source: automated
summary_file: 17-11-SUMMARY.md
coverage_id: RM-030-ir-owner-approval
evidence: ["d2d27eba14e50deaba88256e6465a6350448103e: python3 -I tests/scripts/verify-release-gates.py --self-test review-controls --rev d2d27eba14e50deaba88256e6465a6350448103e (controls=38 positives=4)", "d2d27eba14e50deaba88256e6465a6350448103e: ctest release_review_controls (passed in 1.7 s inside the full -j8 run)"]

### 52. The evaluator writes the exact measurement the owner approves, the approved receipt is the only way the widened limit passes the real verify-perf-gate ratchet, the same widening without approval is refused, an approved run still fails on a wrong correctness digest and on a realtime miss, a receipt edited after approval is refused downstream, ordinary advisory timing passes with no approval and an approval offered for it is refused, and the triggered advisory pipeline succeeds without any decision.
expected: "The evaluator writes the exact measurement the owner approves, the approved receipt is the only way the widened limit passes the real verify-perf-gate ratchet, the same widening without approval is refused, an approved run still fails on a wrong correctness digest and on a realtime miss, a receipt edited after approval is refused downstream, ordinary advisory timing passes with no approval and an approval offered for it is refused, and the triggered advisory pipeline succeeds without any decision."
result: pass
source: automated
summary_file: 17-11-SUMMARY.md
coverage_id: RM-030-ir-approval-reaches-ratchet
evidence: ["d2d27eba14e50deaba88256e6465a6350448103e: python3 -I tests/scripts/verify-release-gates.py --self-test review-approval --rev d2d27eba14e50deaba88256e6465a6350448103e (controls=5 positives=10) and ctest release_review_approval", "d2d27eba14e50deaba88256e6465a6350448103e: python3 -I tests/scripts/verify-perf-gate.py --self-test-exception-measurement (controls=2) and ctest perf_exception_measurement"]

### 53. The nightly gate selects the newest eligible nightly-asan run at the exact head and requires it completed with success and a successful asan-full-replay job. The six named mutants (failure, wrong head superseded by a newer run, skipped replay, run in progress, no run at the head, older green behind a newer red) and 32 further variants (failed, cancelled, missing or repeated replay job, other workflow, event or branch, another attempt, repeated run id, out-of-order or malformed timestamps, unresolvable head, boundary source of another tree) are each refused for their own reason, the receipt is written exclusively and only on success, and a head and a tagged commit that share a tree are accepted.
expected: "The nightly gate selects the newest eligible nightly-asan run at the exact head and requires it completed with success and a successful asan-full-replay job. The six named mutants (failure, wrong head superseded by a newer run, skipped replay, run in progress, no run at the head, older green behind a newer red) and 32 further variants (failed, cancelled, missing or repeated replay job, other workflow, event or branch, another attempt, repeated run id, out-of-order or malformed timestamps, unresolvable head, boundary source of another tree) are each refused for their own reason, the receipt is written exclusively and only on success, and a head and a tagged commit that share a tree are accepted."
result: pass
source: automated
summary_file: 17-11-SUMMARY.md
coverage_id: RM-030-nightly-exact-head
evidence: ["d2d27eba14e50deaba88256e6465a6350448103e: python3 -I tests/scripts/verify-release-gates.py --self-test nightly-controls --rev d2d27eba14e50deaba88256e6465a6350448103e (controls=38 positives=4) and --self-test nightly-gate (controls=2 positives=7)", "d2d27eba14e50deaba88256e6465a6350448103e: ctest release_nightly_gate and release_nightly_controls"]

### 54. The Phase 17 boundary check reads plans, summaries, requirement ids, route flags, the Phase 16 receipt blobs, nightly receipt timestamps and the six RM-027 rows from one literal commit. A short, named, upper-case, unresolvable or substituted revision, a missing plan or summary, an unreachable plan_head_after, a later phase, an auto flag, a regenerated historic receipt, a seventh or dropped release_bound row, a version past 0.2.1 with rows left and a receipt checked after its commit or before its run completed are each refused, while an uncommitted edit and a later commit do not change an earlier boundary.
expected: "The Phase 17 boundary check reads plans, summaries, requirement ids, route flags, the Phase 16 receipt blobs, nightly receipt timestamps and the six RM-027 rows from one literal commit. A short, named, upper-case, unresolvable or substituted revision, a missing plan or summary, an unreachable plan_head_after, a later phase, an auto flag, a regenerated historic receipt, a seventh or dropped release_bound row, a version past 0.2.1 with rows left and a receipt checked after its commit or before its run completed are each refused, while an uncommitted edit and a later commit do not change an earlier boundary."
result: pass
source: automated
summary_file: 17-11-SUMMARY.md
coverage_id: RM-030-immutable-boundary
evidence: ["d2d27eba14e50deaba88256e6465a6350448103e: python3 -I tests/scripts/verify-state-contract.py --boundary --self-test --rev d53ec9c34e42094e6b468f5ca725afe28cb4e819 (controls=31) and --boundary --rev d53ec9c34e42094e6b468f5ca725afe28cb4e819", "d2d27eba14e50deaba88256e6465a6350448103e: ctest state_boundary_controls (planning label, 13.9 s inside the full -j8 run)"]

### 55. The real release paths call the gates: the publisher runs the nightly-gate lifecycle mode from the trusted checkout after the final byte gate and before the publication transition with actions read only, run-perf-gate.sh hands the ratchet only a receipt that --review-approval wrote and no longer accepts a bare receipt, and ci.yml and the rehearsal run the gate controls beside the perf gate. The workflow policy refuses a removed, echoed, tagged-checkout, failure-swallowing, unbound, reordered or over-permissioned nightly call and each broken link of the approval path with 19 new negative controls, and the lifecycle replay runs the production nightly mode against recorded run shapes in both attempts and refuses twelve hostile run histories.
expected: "The real release paths call the gates: the publisher runs the nightly-gate lifecycle mode from the trusted checkout after the final byte gate and before the publication transition with actions read only, run-perf-gate.sh hands the ratchet only a receipt that --review-approval wrote and no longer accepts a bare receipt, and ci.yml and the rehearsal run the gate controls beside the perf gate. The workflow policy refuses a removed, echoed, tagged-checkout, failure-swallowing, unbound, reordered or over-permissioned nightly call and each broken link of the approval path with 19 new negative controls, and the lifecycle replay runs the production nightly mode against recorded run shapes in both attempts and refuses twelve hostile run histories."
result: pass
source: automated
summary_file: 17-11-SUMMARY.md
coverage_id: RM-030-production-wiring
evidence: ["d2d27eba14e50deaba88256e6465a6350448103e: python3 -I .github/scripts/verify-workflow-policy.py --check and --self-test (negative_controls=366 positive_controls=4)", "d2d27eba14e50deaba88256e6465a6350448103e: python3 -I tests/scripts/verify-release-lifecycle.py --rev d2d27eba14e50deaba88256e6465a6350448103e --replay (modes=8 publish_decisions=2 live_mutations=0) and --self-test (positives=4 controls=97)", "d2d27eba14e50deaba88256e6465a6350448103e: bash .github/scripts/verify-release-gates.sh --self-test (exit 0)"]

### 56. The six release_bound timeout rows stay a named Phase 19 entry blocker: the boundary check requires exactly those rows and the blocker wording at version 0.2.1 and refuses any row left once the version passes 0.2.1. docs/release.md records the approval and nightly contracts and the blocker, and the documentation adoption check passes.
expected: "The six release_bound timeout rows stay a named Phase 19 entry blocker: the boundary check requires exactly those rows and the blocker wording at version 0.2.1 and refuses any row left once the version passes 0.2.1. docs/release.md records the approval and nightly contracts and the blocker, and the documentation adoption check passes."
result: pass
source: automated
summary_file: 17-11-SUMMARY.md
coverage_id: RM-027-blocker-preserved
evidence: ["d2d27eba14e50deaba88256e6465a6350448103e: python3 -I tests/scripts/verify-state-contract.py --boundary --rev d2d27eba14e50deaba88256e6465a6350448103e (release_bound=6 version=0.2.1) and python3 -I tests/scripts/verify-v02-adoption.py --check docs"]

### 57. The full suite passes at the final source head after a fresh configure, including dmg_baseline, the test inventory and budget, the planning labels and the summary coverage checks.
expected: "The full suite passes at the final source head after a fresh configure, including dmg_baseline, the test inventory and budget, the planning labels and the summary coverage checks."
result: pass
source: automated
summary_file: 17-11-SUMMARY.md
coverage_id: phase17-11-no-regression
evidence: ["d2d27eba14e50deaba88256e6465a6350448103e: cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 -j8 --output-on-failure --no-tests=error (1494/1494 passed, 170.9 s)"]

## Summary

total: 57
passed: 57
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps

[none]
