---
phase: 12-cgb-double-speed
plan: 13
subsystem: testing
tags: [cgb, double-speed, fixture-reproduction, rgbds, workflow]
requires:
  - phase: GB-12
    provides: Original CGB speed and hostile STOP ROMs, manifest recipes, and RGBDS 1.0.1 pins
provides:
  - Manifest-driven byte-identical rebuilds for both CGB speed ROMs
  - Offline negative controls for RGBDS failures, missing build pins, and workflow pin mismatches
  - Linux fixture-repro workflow coverage and exact CTest inventory for CGB speed reproduction
affects: [CGB-06, fixture-repro, RGBDS, GB-12]
actuals:
  tokens: 3993
  tasks: 2
  commits: 2
plan_head_before: 7dd9c63fcf91194dbd9634b5d2dac091f08f8607
plan_head_after: 631be0b9d4c46a7c1e9a3dee9cec1ae50bf713f9
tech-stack:
  added: []
  patterns:
    - Manifest recipe fields pass allow-lists and become tool argument arrays, never shell text.
    - Offline stubs prove harness failures remain distinct from fixture byte differences.
key-files:
  created:
    - tests/scripts/reproduce-cgb-speed.sh
    - tests/scripts/test-reproduce-cgb-speed.sh
  modified:
    - .github/workflows/fixture-repro.yml
    - cmake/ExpectedTests.cmake
    - tests/CMakeLists.txt
    - tests/expected-tests.txt
key-decisions:
  - Compare the RGBDS build pins against the established CGB banking fixture and the workflow's reviewed Linux release pin.
  - Keep tool failures and missing pins as result=error with exit 2, separate from byte mismatches with exit 1.
  - Exercise the workflow's embedded CGB speed pin comparison and a tampered digest through the existing two offline control tests.
requirements-completed: [CGB-06]
coverage:
  - id: GB-12-13-REPRODUCER
    description: The manifest-driven script rebuilds speed.gb and speed-hostile.gb with RGBDS 1.0.1 and requires exact equality with their committed bytes and SHA-256 pins.
    requirement: CGB-06
    human_judgment: false
    verification:
      - kind: integration
        ref: bash tests/scripts/reproduce-cgb-speed.sh
        status: pass
      - kind: integration
        ref: cgb_speed_repro_tool_failure
        status: pass
      - kind: integration
        ref: cgb_speed_repro_missing_pin
        status: pass
  - id: GB-12-13-WORKFLOW
    description: The Linux fixture-repro job cross-checks all CGB speed RGBDS pins and runs the byte-exact rebuild; the actual embedded check rejects a tampered archive digest.
    requirement: CGB-06
    human_judgment: false
    verification:
      - kind: integration
        ref: cgb_speed_repro_missing_pin workflow pin positive and archive_sha256 mismatch control
        status: pass
      - kind: other
        ref: actionlint .github/workflows/fixture-repro.yml
        status: pass
  - id: GB-12-13-INVENTORY
    description: Both bash-only controls are registered under their exact expected names and removed from the Windows inventory.
    requirement: CGB-06
    human_judgment: false
    verification:
      - kind: unit
        ref: cmake --preset phase1
        status: pass
      - kind: integration
        ref: ctest --test-dir build -R '^cgb_speed_repro_' --output-on-failure --no-tests=error
        status: pass
metrics:
  duration: "not captured"
  completed: 2026-10-13
status: complete
---

# Phase GB-12 Plan 13: Reproducible CGB Speed Fixture Summary

**Both original CGB speed ROMs rebuild from their manifest byte-for-byte, with offline controls for build errors and the Linux workflow's RGBDS pin comparison.**

## Performance

- **Duration:** Not captured; no duration estimate is recorded.
- **Started:** Not captured.
- **Completed:** 2026-10-13.
- **Tasks:** 2.
- **Files modified:** 6.

## Accomplishments

- Added `reproduce-cgb-speed.sh`, which validates the recipe allow-lists, source digests, license notice, RGBDS version, and manifest build pins, builds in a temporary directory, and compares both outputs against their committed bytes.
- Rebuilt `speed.gb` as SHA-256 `3c6e88de1e28d47566f7486dd13813c8fb1baf48ee336509e3902bd9ff8e2f3f` and `speed-hostile.gb` as SHA-256 `c03dc826d8da5fcb7adba5fcd9d5c231686519d8fa3ab23cefa57e2e5c027471` with the verified RGBDS 1.0.1 tools. The fixture sources and ROM bytes remain unchanged.
- Added offline controls that require a failing assembler and an absent build pin to report `result=error` with exit 2, never `result=differs`. The existing missing-pin CTest also executes the fixture-repro workflow's real embedded pin block and proves that a tampered CGB speed archive digest is rejected.
- Added the CGB speed manifest to the workflow's cross-check, added the Linux rebuild step, registered exactly two bash-only CTests, and added both to the Windows removal list.
- Kept all evidence scoped to the pinned, author-attested software fixture; this plan makes no physical-hardware claim.

## Task Commits

1. **Task 1: Byte-exact manifest-driven reproducer** — `b025cba` (`feat`).
2. **Task 2: Offline controls, CTest inventory, and fixture-repro workflow** — `631be0b` (`test`).

The final summary and tracking commit is recorded in the executor completion report.

## Files Created/Modified

- `tests/scripts/reproduce-cgb-speed.sh` — rebuilds both ROMs from validated manifest recipes and distinguishes build errors from byte differences.
- `tests/scripts/test-reproduce-cgb-speed.sh` — offline tool-failure, missing-pin, and workflow pin-mismatch controls.
- `.github/workflows/fixture-repro.yml` — checks the CGB speed release pins and rebuilds the two ROMs on Linux.
- `tests/CMakeLists.txt`, `tests/expected-tests.txt`, and `cmake/ExpectedTests.cmake` — exact registered test inventory and Windows exclusions.

## Validation Evidence

- `bash tests/scripts/reproduce-cgb-speed.sh` with `/private/tmp/gabbaboy-rgbds-1.0.1` on `PATH` — `result=byte-identical roms=2`; both output hashes matched the manifest.
- `cmake --preset phase1` and `cmake --build --preset phase1` — passed.
- `ctest --test-dir build -R '^cgb_speed_repro_' --output-on-failure --no-tests=error` — 2/2 passed, including the workflow pin mismatch control.
- `ctest --test-dir build -j8 --output-on-failure` — 835/835 passed. After extending the offline control to exercise the embedded workflow check, the focused two-test group was rerun and passed 2/2.
- `actionlint .github/workflows/fixture-repro.yml` and a PyYAML parse — passed.
- `summary_coverage` is checked after this file is written; its result is recorded in the self-check below.

## Decisions Made

- Followed the CGB colour reproduction pattern and compared all required build-pin fields against the established CGB banking manifest. The hosted workflow also compares the CGB speed pins with the reviewed Linux RGBDS 1.0.1 archive digest.
- Kept reproducibility outcomes explicit: source/tool/recipe errors are `result=error` (exit 2), committed-byte differences are `result=differs` (exit 1), and exact matches are `result=byte-identical` (exit 0).
- Put the workflow pin-mismatch negative control inside the planned missing-pin CTest, satisfying D-069 without adding a third inventory name.

## Deviations from Plan

### Auto-added validation

**1. [Rule 2 - Missing critical validation] Added a persistent workflow pin-mismatch control.**
- **Found during:** Task 2 (Offline controls and workflow registration).
- **Issue:** The two requested offline controls tested the reproducer, but did not prove that the workflow's newly added manifest comparison rejects a changed CGB speed pin.
- **Fix:** Extended the existing controls to run the actual embedded workflow Python block against the manifests, then mutate `cgb-speed`'s archive digest and require rejection.
- **Files modified:** `tests/scripts/test-reproduce-cgb-speed.sh`.
- **Verification:** Both `cgb_speed_repro_tool_failure` and `cgb_speed_repro_missing_pin` pass; each exercises the positive workflow pin block and its mismatch control.
- **Committed in:** `631be0b`.

## Issues Encountered

The local `helperci_monitor` command and `scripts/ci_monitor.cjs` are unavailable. This plan requires local fixture and workflow validation only; hosted workflow execution remains assigned to plan 12-19, so no hosted run was started here.

## User Setup Required

None.

## Next Phase Readiness

Plan 12-13 is complete; Phase GB-12 remains in progress. The next plan is **12-14 — CGB speed partition invariance**, via **`/gsd-execute-phase 12`**. Phase 13 — CGB HDMA remains not started and follows only after Phase GB-12 closes; auto-advance remains disabled.

---
*Phase: 12-cgb-double-speed*
*Completed: 2026-10-13*

## Self-Check: PASSED

- All six plan deliverable files and this SUMMARY exist.
- Task commits `b025cba` and `631be0b` are ancestors of HEAD and appear in the `12-13` evaluation scope.
- All plan acceptance checks pass; the registered negative-control tests pass 2/2.
- `summary_coverage` passes 1/1 and classifies all three deliverables as automatically covered.
