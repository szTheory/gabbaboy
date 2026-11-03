---
status: complete
phase: GB-21-cgb-game-progress-and-scene-regressions
source: 21-01-SUMMARY.md, 21-02-SUMMARY.md, 21-03-SUMMARY.md, 21-04-SUMMARY.md, 21-05-SUMMARY.md, 21-06-SUMMARY.md, 21-07-SUMMARY.md, 21-08-SUMMARY.md
started: 2026-11-03T01:27:21.179476+00:00
updated: 2026-11-03T01:27:21.179476+00:00
---

## Automated Evidence

# Phase 21 automated verification evidence

## Local implementation boundary

The final implementation and rescope source is `e0845db5841a1d56d8a297cbfaa3e0811af6ad67`. Configure and build passed. The full serial Phase 1 CTest run completed 1,717 of 1,718 registered tests successfully; `v02_source_archive_controls` hit its existing 90-second timeout. Its isolated same-head retest passed in 77.17 seconds without changing test membership, timeout, or budget. Thus all 1,718 registered tests have passing evidence across the full run and that focused retest, but no single full-suite invocation was all-green. The full run took 1,910.62 seconds.

The 18 candidate compile-command unit tests passed. The focused `phase21_fixture_admission_controls` test passed in 34.59 seconds. Configure/build, Phase 21 game-evidence, game-evidence controls, scene controls, and scene contract checks passed at the same source. The final game-evidence record says `game=not-admitted`, model `CGB-CPU-E`, mode `cgb`. No candidate game source or ROM was executed.

Potion Panic remains a source and rights-scope no-go because exact component grants and repository/public-CI scope were not established. µCity 1.3 remains a no-go because required `source/engine/hardware.inc` has no identified grant or notice. These are evidence-scope decisions, not claims that either license prohibits use. `FIXT-01` remains pending further owner-selected source evidence.

## Review and security boundary

The final scoped source review and independent security audit both checked `e0845db5841a1d56d8a297cbfaa3e0811af6ad67`; neither found a remaining issue in the approved qualification-parser and diagnostic-escaping scope. The security audit reports zero open threats. See [21-REVIEW.md](21-REVIEW.md), [21-SECURITY.md](21-SECURITY.md), and [21-RESCOPE.md](21-RESCOPE.md).

## Hosted qualification boundary

PR #140's exact-head checks all passed at `e0845db5841a1d56d8a297cbfaa3e0811af6ad67`. Pull-request CI run [41554959166](https://github.com/szTheory/gabbaboy/actions/runs/41554959166) passed native Windows/Linux/macOS, CMake 3.25.3, the complete ASan/UBSan shards, fixture/native acceptance gates, and performance/player gates. Fixture reproduction [41554959121](https://github.com/szTheory/gabbaboy/actions/runs/41554959121) and the preview package run [41554959116](https://github.com/szTheory/gabbaboy/actions/runs/41554959116) passed, including both installed-package consumers and the macOS player-package smoke. The `planning-checks` lane was skipped for this product-code change; the version pre-tag gate was skipped because no tag was being prepared. Neither skip substituted for a required check.

The same-SHA push CI and fixture runs also passed ([41554953994](https://github.com/szTheory/gabbaboy/actions/runs/41554953994), [41554954013](https://github.com/szTheory/gabbaboy/actions/runs/41554954013)); they are diagnostic only and are not counted as PR qualification. The documentation closeout commit will change the PR head, so phase closure still requires a fresh successful check set for that final exact SHA.

The push and pull-request events each started overlapping CI and fixture-reproduction work for the same SHA. This duplicates hosted work without adding distinct coverage. Track a bounded CI-trigger efficiency follow-up; preserve required checks and verify GitHub event/token behavior before changing workflow triggers.

## Outcome limits

The original CGB result remains harness-only. RGB555/PCM digests establish repeatability, not accuracy, physical hardware behavior, perceptual behavior, or general compatibility. The scene workflow is synthetic-only; no live defect or real-game scene regression is claimed.

## Current Test

[testing complete]

## Tests

### 1. The actual runner accepts source-bound native-CGB guest progress and emits CGB RGB555 and PCM observations; no-input and impossible-predicate controls fail.
expected: "The actual runner accepts source-bound native-CGB guest progress and emits CGB RGB555 and PCM observations; no-input and impossible-predicate controls fail."
result: pass
source: automated
summary_file: 21-01-SUMMARY.md
coverage_id: D1
evidence: ["ctest --preset phase1 --output-on-failure --no-tests=error -R '^(acceptance_cgb_progress_tracer|cgb_runner_profile_dmg_identity_acceptance|dmg_baseline)$'"]

### 2. Loaded compatibility mode is refused explicitly, and the exact ROM, script, predicate, profile, execution mode, and observations are bound in source-qualified evidence.
expected: "Loaded compatibility mode is refused explicitly, and the exact ROM, script, predicate, profile, execution mode, and observations are bound in source-qualified evidence."
result: pass
source: automated
summary_file: 21-01-SUMMARY.md
coverage_id: D2
evidence: ["ctest --preset phase1 --output-on-failure --no-tests=error -R '^(acceptance_cgb_progress_tracer|acceptance_cgb_progress_compat_rejected|cgb_runner_profile_dmg_identity_acceptance|dmg_baseline)$'", "python3 -I tests/scripts/verify-cgb-progress.py --self-test --repo-root ."]

### 3. Native CGB progress requires the intended RIGHT input and predicate; no-input, LEFT input, and impossible-predicate cases fail for predicate-not-reached.
expected: "Native CGB progress requires the intended RIGHT input and predicate; no-input, LEFT input, and impossible-predicate cases fail for predicate-not-reached."
result: pass
source: automated
summary_file: 21-02-SUMMARY.md
coverage_id: D1
evidence: ["ctest --preset phase1 --output-on-failure --no-tests=error -R '^acceptance_predicate_cgb_(truth_table|anchors)$'", "ctest --preset phase1 --output-on-failure --no-tests=error -R '^acceptance_cgb_progress_discrimination$'"]

### 4. Native CGB receipts and sorted observations bind the same run's identities, times, RGB555 digests, PCM results, and independently checked checkpoint/failure PPM pixels.
expected: "Native CGB receipts and sorted observations bind the same run's identities, times, RGB555 digests, PCM results, and independently checked checkpoint/failure PPM pixels."
result: pass
source: automated
summary_file: 21-02-SUMMARY.md
coverage_id: D2
evidence: ["ctest --preset phase1 --output-on-failure --no-tests=error -R '^acceptance_cgb_progress_observations$'", "python3 -I tests/scripts/verify-cgb-progress.py --self-test --repo-root .", "ctest --preset phase1 --output-on-failure --no-tests=error -R '^(acceptance_digest_rgb555_vectors|cgb_runner_profile_dmg_identity_acceptance|dmg_baseline)$'"]

### 5. Fixed candidate order, final-state rules, missing-record rejection and explicit cutoff accounting.
expected: "Fixed candidate order, final-state rules, missing-record rejection and explicit cutoff accounting."
result: pass
source: automated
summary_file: 21-03-SUMMARY.md
coverage_id: D1
evidence: ["python3 -I tests/scripts/test_cgb_candidate_order.py", "ctest --preset phase1 --output-on-failure --no-tests=error -R '^phase21_fixture_admission_contract$'"]

### 6. Admitted evidence delegates to Phase 20, binds native-CGB progress and receipt identities, and requires confined build and probe evidence.
expected: "Admitted evidence delegates to Phase 20, binds native-CGB progress and receipt identities, and requires confined build and probe evidence."
result: pass
source: automated
summary_file: 21-03-SUMMARY.md
coverage_id: D2
evidence: ["ctest --preset phase1 --output-on-failure --no-tests=error -R '^phase21_fixture_admission_controls$'", "cmake --preset phase1 && cmake --build --preset phase1"]

### 7. The primary candidate has a final source-grounded rights no-go; exact source and all downstream candidate facts remain explicitly not observed.
expected: "The primary candidate has a final source-grounded rights no-go; exact source and all downstream candidate facts remain explicitly not observed."
result: pass
source: automated
summary_file: 21-04-SUMMARY.md
coverage_id: D1
evidence: ["python3 -I tests/scripts/verify-cgb-candidates.py --check-record tests/data/cgb-candidates/potion-panic.json --require-final --repo-root . --source-revision 1ab7180e9f35c70246e62c252d3dd4851fa77473"]

### 8. The no-go branch adds no candidate fixture or acceptance input and preserves the Phase 20 repository/package boundary.
expected: "The no-go branch adds no candidate fixture or acceptance input and preserves the Phase 20 repository/package boundary."
result: pass
source: automated
summary_file: 21-04-SUMMARY.md
coverage_id: D2
evidence: ["python3 -I tests/scripts/verify-fixture-admission.py --check-repository --repo-root . && ctest --preset phase1 --output-on-failure --no-tests=error -R '^(fixture_product_core_controls|fixture_product_player_controls|phase21_fixture_admission_(contract|controls))$'"]

### 9. The sole fallback is tied to the author-linked v1.3 source and has a concrete component-scope no-go with later facts explicitly not observed.
expected: "The sole fallback is tied to the author-linked v1.3 source and has a concrete component-scope no-go with later facts explicitly not observed."
result: pass
source: automated
summary_file: 21-05-SUMMARY.md
coverage_id: D1
evidence: ["python3 -I tests/scripts/verify-cgb-candidates.py --check-all --require-final --repo-root . --source-revision c0fa267be2f14c632ef2208354a4267ef2edd6e0"]

### 10. The no-go branch creates no fallback ROM, fixture, notice row, acceptance case, input, or predicate and leaves Phase 20 admission unchanged.
expected: "The no-go branch creates no fallback ROM, fixture, notice row, acceptance case, input, or predicate and leaves Phase 20 admission unchanged."
result: pass
source: automated
summary_file: 21-05-SUMMARY.md
coverage_id: D2
evidence: ["Automated path assertions for fixtures/ucity-1.3, the ucity acceptance case/input, predicate registry, and THIRD_PARTY_NOTICES.md", "python3 -I tests/scripts/verify-fixture-admission.py --check-repository --repo-root ."]

### 11. Existing native-CGB harness progress, input/predicate controls, mode refusal, and fixture/product boundary tests pass; the result remains harness evidence only.
expected: "Existing native-CGB harness progress, input/predicate controls, mode refusal, and fixture/product boundary tests pass; the result remains harness evidence only."
result: pass
source: automated
summary_file: 21-05-SUMMARY.md
coverage_id: D3
evidence: ["ctest --preset phase1 --output-on-failure --no-tests=error -R '^(fixture_product_core_controls|fixture_product_player_controls|acceptance_cgb_progress_.*|phase21_fixture_admission_(contract|controls))$'"]

### 12. Minimal text intake creates bounded unresolved triage and rejects malformed, oversized and unsafe inputs.
expected: "Minimal text intake creates bounded unresolved triage and rejects malformed, oversized and unsafe inputs."
result: pass
source: automated
summary_file: 21-06-SUMMARY.md
coverage_id: D1
evidence: ["ctest --preset phase1 --output-on-failure --no-tests=error -R '^phase21_scene_report_tracer$'"]

### 13. Synthetic promotion evidence rejects missing, self-derived, unpermitted or irrelevant evidence and requires the causal negative control.
expected: "Synthetic promotion evidence rejects missing, self-derived, unpermitted or irrelevant evidence and requires the causal negative control."
result: pass
source: automated
summary_file: 21-06-SUMMARY.md
coverage_id: D2
evidence: ["ctest --preset phase1 --output-on-failure --no-tests=error -R '^phase21_scene_report_controls$'"]

### 14. The committed agent procedure documents recovery, reproduction boundaries, classification, privacy, and promotion obligations.
expected: "The committed agent procedure documents recovery, reproduction boundaries, classification, privacy, and promotion obligations."
result: pass
source: automated
summary_file: 21-06-SUMMARY.md
coverage_id: D3
evidence: ["ctest --preset phase1 --output-on-failure --no-tests=error -R '^phase21_scene_report_contract$'"]

### 15. Source-bound CGB outcome composes current candidate facts and the original harness result, rejecting missing evidence and unsupported game, accuracy, or hardware claims.
expected: "Source-bound CGB outcome composes current candidate facts and the original harness result, rejecting missing evidence and unsupported game, accuracy, or hardware claims."
result: pass
source: automated
summary_file: 21-07-SUMMARY.md
coverage_id: D1
evidence: ["ctest --preset phase1 --output-on-failure --no-tests=error -R '^phase21_game_evidence(_controls)?$'", "verify-cgb-game-evidence.py --check at source fdd3454a0ee6c2aa37dcd56666e1699c59cb55bf; build/phase21-evidence/result.json"]

### 16. Ordered candidate records retain the bounded two-candidate no-go outcome and reject identity, rights-claim, and source-pin mutations.
expected: "Ordered candidate records retain the bounded two-candidate no-go outcome and reject identity, rights-claim, and source-pin mutations."
result: pass
source: automated
summary_file: 21-07-SUMMARY.md
coverage_id: D2
evidence: ["ctest --preset phase1 --output-on-failure --no-tests=error -R '^phase21_fixture_admission(_contract|_controls)?$'"]

### 17. Scene-report documentation preserves independent regression expectations, owner agency, and private-media boundaries.
expected: "Scene-report documentation preserves independent regression expectations, owner agency, and private-media boundaries."
result: pass
source: automated
summary_file: 21-07-SUMMARY.md
coverage_id: D3
evidence: ["ctest --preset phase1 --output-on-failure --no-tests=error -R '^phase21_scene_report_.*$'"]

### 18. The final configured implementation passes the complete registered CTest suite and the fixed test-budget gate.
expected: "The final configured implementation passes the complete registered CTest suite and the fixed test-budget gate."
result: pass
source: automated
summary_file: 21-07-SUMMARY.md
coverage_id: D4
evidence: ["cmake -S . -B build && cmake --build build && ctest --test-dir build --output-on-failure --timeout 60 --parallel 1 \u2014 source fdd3454a0ee6c2aa37dcd56666e1699c59cb55bf; 1724/1724 in 1220.71s"]

### 19. The canonical CMake-built runner qualification binds the exact 24 build inputs, including state-version parsing and the borrowed acceptance-input header; dirty changes to either are rejected before candidate execution, and BUILD_TESTING=OFF remains Python-free.
expected: "The canonical CMake-built runner qualification binds the exact 24 build inputs, including state-version parsing and the borrowed acceptance-input header; dirty changes to either are rejected before candidate execution, and BUILD_TESTING=OFF remains Python-free."
result: pass
source: automated
summary_file: 21-08-SUMMARY.md
coverage_id: D1
evidence: ["ctest --preset phase1 --output-on-failure --no-tests=error -R '^phase21_fixture_admission_(contract|controls)$' at source 5335ae5c41609bc84a3842385fd2b75ec61dcdc4; 24-input receipt and per-path dirty-source/qualification controls passed", "cmake -S . -B build/phase21-no-tests -G Ninja -DBUILD_TESTING=OFF -DCMAKE_BUILD_TYPE=Debug -DCMAKE_DISABLE_FIND_PACKAGE_Python3=TRUE && cmake --build build/phase21-no-tests --target gabbaboy-runner; both passed at source 5335ae5c41609bc84a3842385fd2b75ec61dcdc4"]

### 20. Fresh admitted replay must reproduce the immutable aggregate end time, rolling RGB555, PCM digest, sample count, audibility, and channel statistics; valid changed values fail with the intended observation mismatch.
expected: "Fresh admitted replay must reproduce the immutable aggregate end time, rolling RGB555, PCM digest, sample count, audibility, and channel statistics; valid changed values fail with the intended observation mismatch."
result: pass
source: automated
summary_file: 21-08-SUMMARY.md
coverage_id: D2
evidence: ["ctest --preset phase1 --output-on-failure --no-tests=error -R '^phase21_fixture_admission_(contract|controls)$' at source 5335ae5c41609bc84a3842385fd2b75ec61dcdc4; 69 synthetic negative controls passed, fixture controls 45.32 seconds", "ctest --preset phase1 --output-on-failure --no-tests=error -R '^phase21_game_evidence$' at source 5335ae5c41609bc84a3842385fd2b75ec61dcdc4; passed in 9.00 seconds"]

## Summary

total: 20
passed: 20
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps

[none]
