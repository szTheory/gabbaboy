---
phase: 14-cgb-e-model-qualification-and-corpus
plan: "11"
subsystem: testing
tags: [cgb, corpus, receipt, ctest, python]
requires:
  - phase: 14-05
    provides: Phase trust boundaries and threat mitigations.
  - phase: 14-06
    provides: CGB source and fixture qualification contracts.
  - phase: 14-07
    provides: Frozen CGB corpus inventory and case identities.
  - phase: 14-09
    provides: Source coverage and expected disposition contracts.
  - phase: 14-10
    provides: CGB-CPU-E behavior and fixture observations.
provides:
  - Versioned identity-bound receipts for the frozen 107-case CGB corpus.
  - Fresh --run and identity-checked --from-ctest workflows with incomplete failure receipts.
  - Independent hostile-stream, exact-membership, and inventory controls.
affects: [14-12, phase-14-qualification, cgb-corpus-reporting]
actuals:
  tokens: 28451
  tasks: 3
  commits: 5
plan_head_before: e5bd88f9ac63a69fc493d45f510d82ce56e2be6d
plan_head_after: 89c966e629b45531a3359e5f27b84de682e53761
tech-stack:
  added: [Python standard library]
  patterns: [identity-bound run receipts, bounded CTest event parsing, source-derived assertion contracts]
key-files:
  created:
    - tests/scripts/verify-cgb-corpus-report.py
    - tests/scripts/test-cgb-corpus-report.py
    - .planning/phases/GB-14-cgb-e-model-qualification-and-corpus/14-11-red-task1.json
    - .planning/phases/GB-14-cgb-e-model-qualification-and-corpus/14-11-red-task3.json
  modified:
    - src/runner/main.c
    - tests/test_age.c
    - tests/test_magentests.c
    - tests/test_samesuite_hdma.c
    - tests/scripts/verify-cgb-corpus-inventory.py
    - tests/external/cgb-corpus-inventory.json
    - tests/CMakeLists.txt
    - tests/expected-tests.txt
    - docs/cgb-corpus.md
key-decisions:
  - Keep observed guest results, evaluator status, matched expected failures, completion counts, and assertion totals separate.
  - Bind receipts to exact source, build, executable, manifest, ROM, CTest membership, and tool identity.
  - Reuse current full CTest evidence through --from-ctest without executing cases again.
patterns-established:
  - Test adapters emit bounded structured events joined by exact frozen case and assertion IDs.
  - A late or invalid run replaces prior success with a fresh incomplete receipt.
requirements-completed: []
coverage:
  - id: D1
    description: A real Mooneye tracer case produces a fresh identity-bound receipt and terminal summary.
    human_judgment: false
    verification:
      - kind: integration
        ref: ctest --test-dir build -R '^cgb_corpus_report_tracer$' --output-on-failure --no-tests=error
        status: pass
  - id: D2
    description: The full frozen corpus reconciles case outcomes, expected failures, assertion rows, and image comparisons.
    human_judgment: false
    verification:
      - kind: integration
        ref: python3 -I tests/scripts/verify-cgb-corpus-report.py --run --build-dir build --receipt build/cgb-corpus-receipt.json
        status: pass
      - kind: integration
        ref: python3 -I tests/scripts/verify-cgb-corpus-report.py --from-ctest --build-dir build --receipt build/cgb-corpus-from-ctest.json
        status: pass
  - id: D3
    description: Hostile receipt streams and inventory mutations reject with bounded diagnostics while clean controls pass.
    human_judgment: false
    verification:
      - kind: unit
        ref: ctest --test-dir build -R '^(cgb_corpus_report_contract|cgb_corpus_report_controls|cgb_corpus_report_tracer|cgb_corpus_report_tracer_controls)$' --output-on-failure --no-tests=error
        status: pass
      - kind: unit
        ref: python3 -I tests/scripts/verify-cgb-corpus-inventory.py --self-test
        status: pass
duration: 23min
completed: 2026-10-15
status: complete
---

# Phase 14 Plan 11: Bounded CGB Corpus Receipt Summary

**An identity-bound receipt reconciles all 107 frozen CGB cases, separating observed passes, declared expected failures, assertion outcomes, and image mismatches.**

## Performance

- **Duration:** 23 minutes
- **Started:** 2026-10-15T22:36:44Z
- **Completed:** 2026-10-15T22:59:50Z
- **Tasks:** 3
- **Files modified:** 13

## Accomplishments

- Added a bounded Python standard-library reporter with a versioned receipt, identity validation, a fresh incomplete failure state, and concise suite summaries.
- Added exact CTest-to-case membership, source-derived assertion validation, and separate observed-pass, completion, evaluator, and matched-xfail accounting.
- Added hostile stream, stale identity, path-bound, late-failure, and all-xfail cohort controls, with independent inventory self-tests.
- Documented the receipt workflow and its current software-model limitations.

The final fresh run on revision 89c966e completed 107/107 cases: 25 observed passes and 82 matched expected failures. Assertions totaled 2,845 passing rows out of 4,959. AGE compared 138,240 image pixels and recorded 18,208 mismatches.

The current run identity is 5e8d91372ac28426562fd97b6826e9319b28a654f94c1050355496068727d755. Its input identity SHA-256 is a7b63102b02240c54e7ad9025f8c5ebfdd578e25f2155b2252d5d6767427bc92.

| Suite | Cases | Observed pass | Matched expected failure | Passing assertion rows |
| --- | ---: | ---: | ---: | ---: |
| AGE | 19 | 2 | 17 | 43/148 |
| Magen tests | 5 | 5 | 0 | 5/5 |
| Mooneye | 9 | 6 | 3 | 6/9 |
| SameSuite | 74 | 12 | 62 | 2,791/4,797 |

The receipt reports software CGB-CPU-E evidence only. It makes no hardware or game-level claim. The current AGE image comparisons include mismatches, and matched expected failures do not increase the observed-pass totals.

## Task Commits

1. **Task 1 RED:** 38c6a5b; **Task 1 GREEN:** 0b03fd5
2. **Task 2:** ef0394d
3. **Task 3 RED:** 95da9af; **Task 3 GREEN:** 89c966e

## Files Created or Modified

- tests/scripts/verify-cgb-corpus-report.py — bounded run orchestration, identity checking, normalization, and receipt output.
- tests/scripts/test-cgb-corpus-report.py — clean and hostile receipt contract controls.
- tests/scripts/verify-cgb-corpus-inventory.py — independent mutation controls for the updated frozen bindings.
- tests/external/cgb-corpus-inventory.json — exact CTest and assertion bindings for the admitted cases.
- src/runner/main.c, tests/test_age.c, tests/test_magentests.c, and tests/test_samesuite_hdma.c — stable structured observations required by the report.
- tests/CMakeLists.txt and tests/expected-tests.txt — corpus labels and required contract/control registrations.
- docs/cgb-corpus.md — receipt commands, output counts, and evidence limits.
- 14-11-red-task1.json and 14-11-red-task3.json — committed TDD RED evidence records.

## Decisions Made

- Preserve the distinction between guest observation, evaluator status, expected-failure matching, completion, and assertion counts.
- Use exact input and executable identity plus the complete CTest case set to bind report reuse.
- Keep static candidate or not-run inventory records separate from runtime results.
- Keep all outputs repository-relative and avoid host path or machine identity data.

## Deviations from Plan

### Auto-fixed Issues

**1. Added direct test-consumer identity fields needed to join DMA observations**
- **Found during:** Task 2
- **Issue:** The HDMA adapter did not report mode, speed, boot policy, or a terminal marker, so its output could not establish the frozen case identity.
- **Fix:** Added those fields to the stable HDMA event and validated them in the reporter; the necessary AGE and Magen consumer events and CTest bindings were also wired to their frozen source contracts.
- **Files modified:** tests/test_samesuite_hdma.c, tests/test_age.c, tests/test_magentests.c, tests/CMakeLists.txt, tests/expected-tests.txt, tests/external/cgb-corpus-inventory.json
- **Verification:** Full 107-case report and all four receipt contract/control CTests passed.
- **Committed in:** ef0394d and 89c966e

**2. Updated an inventory self-test whose old expectation became stale**
- **Found during:** Task 3
- **Issue:** After Magen CTest bindings were populated, the positive inventory could no longer serve as the unbound negative fixture.
- **Fix:** Mutated a deep copy back to a pending binding for that control and asserted the intended rejection. The static not-run row check remains independent.
- **Files modified:** tests/scripts/verify-cgb-corpus-inventory.py
- **Verification:** Inventory self-test passed with the unbound and static not-run controls.
- **Committed in:** 89c966e

**Total deviations:** 2 targeted corrections.
**Impact on plan:** The added consumer fields and adjusted negative fixture were needed for exact identity checks. No public ABI, dependency, hardware claim, or additional emulator behavior was introduced.

## Issues Encountered

The first final run correctly rejected a runner executable built before the Task 3 commit because its embedded source revision did not match the current input identity; it wrote an incomplete receipt. Reconfiguring and rebuilding on 89c966e refreshed the executable identity. The subsequent fresh run, reporter self-test, and --from-ctest run all passed.

The CMake configure step noted that the matching Clang libFuzzer runtime was unavailable; deterministic sanitizer regressions remained enabled and the full build succeeded. Static inventory rows marked not-run-by-inventory remain separate from the 107 runtime case results.

## User Setup Required

None.

## Next Phase Readiness

Plan 14-11 is complete. Phase 14 remains open pending the parent workflow's full-wave gate and remaining phase work. No Phase 15 work was started.

---
*Phase: 14-cgb-e-model-qualification-and-corpus*
*Completed: 2026-10-15*

## Self-Check: PASSED

The summary file exists, all five task commits are ancestors of the plan head, and the summary_coverage CTest passed.
