---
phase: GB-22-composition-and-microtest-evidence
plan: "01"
subsystem: testing
tags: [python, cmake, ctest, diagnostics, synthetic]
requires:
  - phase: GB-20-fixture-admission-tune-up
    provides: Real fixture-admission CLI and product scanner used with temporary synthetic records.
provides:
  - Original synthetic DMG composition exercised through the compiled runner and exact source-cell comparison.
  - Source-anchored mask and independent receipt identity controls for altered synthetic evidence.
affects: [GB-22 remaining plans, diagnostic fixture admission]
actuals:
  tokens: 14431
  tasks: 2
  commits: 4
tech-stack:
  added: []
  patterns:
    - Fixed source-cell allowlists are checked independently from candidate mask digests.
    - Receipt asset identities are compared against separately computed expected identities.
key-files:
  created:
    - tests/acid2/control.asm
    - tests/scripts/verify-acid2-masks.py
    - tests/scripts/verify-diagnostic-admission.py
  modified:
    - tests/scripts/run-acid2-local.py
    - tests/CMakeLists.txt
    - tests/expected-tests.txt
key-decisions:
  - Keep the tracer synthetic-only and bind its one visible tile cell to a fixed allowlist.
  - Assert specific refusal reasons for identity, mask, image, path, and admission-pin mutants.
patterns-established:
  - A synthetic runner receipt hashes source, ROM, reference, layout, glyph, allowlist, mask, and overlay independently.
  - Phase 22 controls invoke the real Phase 20 admission CLI with disposable original synthetic data.
requirements-completed: []
coverage:
  - id: D1
    description: Original synthetic composition traverses admission, compiled runner, exact unmasked comparison, receipt binding, and product exclusion.
    verification:
      - kind: e2e
        ref: "ctest --preset phase1 --output-on-failure --no-tests=error -R '^phase22_(acid2_(tracer|contract|controls)|fixture_admission_(contract|controls))$'"
        status: pass
    human_judgment: false
  - id: D2
    description: Changed identities, broadened masks, malformed images and admission pins are refused with specific controls.
    verification:
      - kind: integration
        ref: "phase22_acid2_contract, phase22_acid2_controls, phase22_fixture_admission_contract, phase22_fixture_admission_controls"
        status: pass
    human_judgment: false
commits: 4
plan_head_before: 4159b889d1f6b911102e41b68efbeba35ef35e28
plan_head_after: e0cf205d576fb43461eb546026035f6d3b5e8167
duration: 19min
completed: 2026-11-03
started_at: "2026-11-03T09:45:56Z"
completed_at: "2026-11-03T10:04:01Z"
status: complete
---

# Phase GB-22 Plan 22-01: Synthetic Composition and Identity Controls Summary

**An original synthetic DMG tile composition now runs through the compiled runner with source-anchored masks and independently checked receipt identities.**

## Performance

- **Duration:** 19 minutes
- **Started:** 2026-11-03T09:45:56Z
- **Completed:** 2026-11-03T10:04:01Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments

- Added a project-authored synthetic control ROM whose expected frame is specified analytically, then exercised it through the real compiled runner and Phase 20 fixture-admission CLI.
- Added a bounded 160×144 mask derived from the source tile-map write and a fixed `(2, 3)` allowlist; only unmasked pixels participate in exact RGB888 comparison.
- Bound the receipt to ROM, reference, source, layout, glyph, allowlist, mask, and overlay hashes. Changed identities, broader masks, malformed images, unsafe paths, and changed admission or notice pins fail with specific reasons.
- Registered the tracer and four contract/control CTests and synchronized the expected-test inventory.

## Task Commits

1. **Task 1 RED:** `694f7b5a` — add source-cell mask contract.
2. **Task 1 GREEN:** `59fce7ac` — exercise the synthetic composition tracer.
3. **Task 2 RED:** `ce2b2140` — add identity corruption controls.
4. **Task 2 GREEN:** `e0cf205d` — reject altered composition identities.

**Plan metadata:** `351ce5b9` (summary, state, and roadmap update).
**Roadmap correction:** `29649e3a` (mark Wave 2 ready and clarify Phase 22 progress).

The two RED checks failed on their intended assertions: the mask control first observed no marked source pixels, and the identity control accepted all eight changed identity candidates. The GSD RED-evidence checker accepted both records before their GREEN implementations.

## Files Created/Modified

- `tests/acid2/control.asm` — original synthetic source for the one-cell DMG control.
- `tests/scripts/run-acid2-local.py` — bounded input handling retained for the image byte controls and connected to the compiled tracer path.
- `tests/scripts/verify-acid2-masks.py` — mask generation, conversion vectors, exact comparator, overlay generation, and corruption controls.
- `tests/scripts/verify-diagnostic-admission.py` — temporary synthetic admission repository, fail-closed runner gate, identity receipt, and admission controls.
- `tests/CMakeLists.txt` — five Phase 22 CTest registrations.
- `tests/expected-tests.txt` — matching inventory entries.

## Decisions Made

- The tracer remains synthetic-only. It makes no game, hardware, mode-3 timing, glyph-accuracy, or general-compatibility claim.
- The expected cell set is a fixed allowlist checked separately from the candidate mask bytes and their digest.

## Deviations from Plan

None. No package was installed, no third-party fixture bytes were used, and no game ROM was run.

## Issues Encountered

Two new negative controls initially expected a different refusal token than the implementation correctly returned. The controls were corrected to assert the specific fully-masked and incomplete-PNG refusal reasons; the complete CTest selection then passed.

## Requirements Traceability

This plan adds synthetic diagnostic infrastructure only. **DIAG-01 and RIGHTS-01 remain pending** until the Phase 22 plans produce and verify the full admitted diagnostic derivative and rights evidence. This summary therefore does not mark either phase-level requirement complete.

## Verification

- `cmake --preset phase1` — passed.
- `cmake --build --preset phase1` — passed.
- `ctest --preset phase1 --output-on-failure --no-tests=error -R '^phase22_(acid2_(tracer|contract|controls)|fixture_admission_(contract|controls))$'` — passed all five selected tests in 2.05 seconds.
- The T1 tracer-only verification also passed after its GREEN commit and again as part of the five-test selection.
- Stub scan across all six changed files found no placeholder, TODO, FIXME, or unwired empty data source.
- Threat-surface review found no new public endpoint, authentication path, or persistent trust boundary; filesystem, Git, subprocess, image, and admission inputs stay bounded within the plan's threat model.

## Self-Check: PASSED

The summary exists, all four task commits and both metadata commits are ancestors of the current plan branch, and the summary coverage checker accepts both deliverables.

## Next Phase Readiness

Plan 22-02 can build on the source-anchored mask and identity controls. The synthetic pass does not clear game or diagnostic rights review, and no user action is needed for this plan.

---
*Phase: GB-22-composition-and-microtest-evidence*
*Plan: 01*
*Completed: 2026-11-03*
