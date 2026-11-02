---
status: complete
phase: GB-21-cgb-game-progress-and-scene-regressions
source: 21-01-SUMMARY.md, 21-02-SUMMARY.md, 21-03-SUMMARY.md, 21-04-SUMMARY.md, 21-05-SUMMARY.md, 21-06-SUMMARY.md, 21-07-SUMMARY.md
started: 2026-11-02T16:23:15.439825+00:00
updated: 2026-11-02T16:23:18.231Z
---

## Automated Evidence

# Phase 21 automated verification evidence

## Boundary

This record was prepared against PR #140 head `a05a0b12e9b1e4bf4b1901b7c81b6160df3688b4`, based on `main` at `9d3dbb3a02e9fc17b5870b45276a4d4833d18d02`. GitHub reported the PR open and mergeable. The evidence below is tied to that point-in-time head; this file records phase closure and does not claim a later live route or ancestry.

## Automated tests

- Plan summaries 21-01 through 21-07 each classify all coverage entries as automated, with passing verification references and no human-judgment entries.
- The full local suite passed 1,724/1,724 at implementation source `fdd3454a0ee6c2aa37dcd56666e1699c59cb55bf`. After merging current `main`, 1,718 tests registered on this host; 1,712 passed in the full run and the remaining six passed in focused retests. No timeout or test budget changed. Six fuzz-runtime-dependent tests were not registered on this host.
- The independent source-bound game-evidence check passed at the merged head and recorded `game=not-admitted`, model `CGB-CPU-E`, mode `cgb`.
- Pull-request checks at this exact head passed: CI run [41474032142](https://github.com/szTheory/gabbaboy/actions/runs/41474032142), fixture reproduction run [41474032137](https://github.com/szTheory/gabbaboy/actions/runs/41474032137), and installed-package smoke run [41474032193](https://github.com/szTheory/gabbaboy/actions/runs/41474032193). These include the required native platform matrix, Linux sanitizers, CMake floor, fixture reproductions, and Linux/macOS installed consumers. The version PR gate was skipped because this change does not create a version PR.
- The verify-work API-coverage pre-check initially matched the phrase “connect to a controlled local network endpoint” in the sandbox-denial test instructions. The phase implements no external API, SDK, or service. `COVERAGE.md` records this reasoned no-integration decision, and the gate passes while surfacing the overridden signal.

## Outcome limits

Neither candidate game was admitted or run. Potion Panic remains a source and rights-scope no-go because exact component grants and repository/public-CI scope could not be established. µCity 1.3 remains a no-go because required `source/engine/hardware.inc` has no identified grant or notice. These are evidence-scope decisions, not claims that either license prohibits use. The original CGB result remains harness-only; RGB555/PCM digests establish repeatability, not accuracy, physical hardware behavior, or general compatibility. `FIXT-01` remains pending further owner-selected source evidence.

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

## Summary

total: 18
passed: 18
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps

[none]
