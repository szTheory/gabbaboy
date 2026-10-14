---
phase: 13-cgb-hdma
plan: "10"
subsystem: testing
tags: [CGB, HDMA, CMake, installed-consumers]
requires:
  - phase: 13-05
    provides: Bounded public HDMA behavior and partition checks
  - phase: 13-09
    provides: SameSuite and Magen fixture dispositions and package constraints
provides:
  - Relocated installed C and C++ consumers that execute inline CGB DMA guests at both speeds
  - Closed package scans for SameSuite and Magen ROM bytes and forbidden directory labels
affects: [13-11, CGB-07, installed-package-verification]
actuals:
  tokens: 7954
  tasks: 2
  commits: 4
commits: 4
plan_head_before: 49de9e5d8787d3a30450f0d81a83abef52024a87
plan_head_after: d33d967ff6267201fef0033427a29514c5199c45
tech-stack:
  added: []
  patterns:
    - Reconfigure relocated package consumers with an explicit installed GabbaBoy_DIR
    - Validate closed fixture contents by digest and path label using renamed-byte controls
key-files:
  created: []
  modified:
    - tests/consumers/c/main.c
    - tests/consumers/cpp/main.cpp
    - cmake/PreviewPackageSmoke.cmake
    - cmake/RunInstalledConsumer.cmake
    - cmake/ScanForbiddenFixtures.cmake
    - tests/CMakeLists.txt
    - tests/expected-tests.txt
key-decisions:
  - Pin every relocated consumer configure to the package config under the current install prefix.
  - Check positive FF55 completion, ROM-derived readback, and DIV timing; the disabled twin diagnoses missing data and CPU-steal timing because FF55 reads FF both before and after completion.
  - Preserve the exact installed fixture child allow-list and reject SameSuite/Magen bytes under neutral filenames.
patterns-established:
  - Installed consumer evidence must link against the exact package prefix produced by the current build.
  - Package boundary scans combine byte digests with path-component labels and negative controls.
requirements-completed: []
coverage:
  - id: D1
    description: Relocated C and C++ installed consumers execute bounded inline CGB DMA guests at normal and double speed and diagnose a disabled-transfer twin.
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest --test-dir build -R '^(installed_consumer_(c|cpp)$|cgb_consumer_symbol_coverage|preview_package_smoke$)' --output-on-failure --no-tests=error --parallel 4"
        status: pass
  - id: D2
    description: The relocated package preserves its exact fixture child set and rejects forbidden SameSuite and Magen ROM bytes even when renamed.
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest --test-dir build -R '^(cgb_hdma_not_installed|magentests_not_installed|age_not_installed|preview_package_smoke$|installed_consumer_(c|cpp)$)' --output-on-failure --no-tests=error --parallel 4"
        status: pass
duration: 20min
completed: 2026-10-14
status: complete
---

# Phase 13 Plan 13-10: Installed C/C++ DMA Consumers and Closed Package Contents Summary

Installed C and C++ callers now execute bounded original CGB DMA guests from the relocated package, while package checks reject admitted-test ROM bytes under renamed filenames.

## Performance

- **Duration:** 20 minutes
- **Started:** 2026-10-14T23:06:31Z
- **Completed:** 2026-10-14T23:26:55Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments

- Both relocated consumers run a 128-byte source-derived GDMA transfer from an inline CGB ROM at normal and double speed using bounded 257-half-dot public run slices. They check speed state, positive FF55 completion, VRAM-to-WRAM readback, DIV timing, partition limits, and a disabled-transfer twin.
- The preview-package smoke test runs both consumers against the installed artifact and enforces the unchanged exact fixture child set.
- The package scanner rejects SameSuite and Magen ROM digests when renamed, and rejects forbidden fixture path labels. The Mealybug rights-gated fixture remains absent; no bytes were fetched and no allow-list entry was added.
- Final verification configured, built, installed, reconfigured with the relative relocated prefix, and enumerated required targets with no omissions. Installed consumer, symbol-coverage, and preview smoke checks passed 5/5; the focused scanner/package group passed 13/13.

## Task Commits

1. **Task 1 RED: installed guest behavior checks** - `6be24e1` (`test`)
2. **Task 1 GREEN: pin relocated package resolution** - `0cbac03` (`feat`)
3. **Task 2 RED: renamed forbidden-byte controls** - `22193e3` (`test`)
4. **Task 2 GREEN: scan package digest and path boundaries** - `d33d967` (`feat`)

## Files Modified

- `tests/consumers/c/main.c` and `tests/consumers/cpp/main.cpp` - inline original transfer guests and explicit disabled-transfer diagnostics using public APIs.
- `cmake/RunInstalledConsumer.cmake` - force every configure to resolve the imported package from the current install prefix.
- `cmake/ScanForbiddenFixtures.cmake` and `cmake/PreviewPackageSmoke.cmake` - scan multiple manifests and path labels, run renamed-byte controls, and preserve exact installed fixture children.
- `tests/CMakeLists.txt` and `tests/expected-tests.txt` - register scanner controls and resolve a relative install prefix from the build root without PATH cache normalization.

## Decisions Made

FF55 reports `FF` after a completed general DMA transfer, and also reads as `FF` before one begins. Therefore the positive guest checks completion status, while the disabled twin must fail the source-derived data and CPU-steal timing predicates. The tests do not claim an impossible status mismatch for that twin.

The package scanner checks exact SameSuite and Magen digests and path labels. Mealybug remains excluded by the unresolved rights gate, so the implementation only checks its forbidden path label and does not claim a Mealybug digest scan.

## TDD Gate Compliance

- **Task 1 RED:** `build/tdd-red-13-10-task1-final.xml` records both installed consumers failing on the stale cached package, which rejected the FF55 write with `GBB_STOP_UNSUPPORTED_BUS`. The unchanged report was machine-classified as semantic stale-package evidence in `build/tdd-red-13-10-task1-final-evidence.json`.
- **Task 1 GREEN:** after pinning `GabbaBoy_DIR` to the current relocated install, both consumers passed with symbol coverage and the preview package smoke test (5/5).
- **Task 2 RED:** `build/tdd-red-13-10-task2.xml` records renamed SameSuite and Magen ROMs accepted by the single-manifest scanner. The unchanged report was machine-classified as the intended missing-digest-set failure in `build/tdd-red-13-10-task2-evidence.json`.
- **Task 2 GREEN:** the multi-manifest and path-label scanner, clean package scan, renamed-byte controls, and preview smoke passed in the focused package group (13/13).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking issue] Prevent stale package-prefix reuse in relocated consumers**
- **Found during:** Task 1
- **Issue:** Existing consumer build caches could keep `GabbaBoy_DIR` pointed at an older phase-12 package prefix, causing the newly added guest to run against a stale library.
- **Fix:** Set `GabbaBoy_DIR` explicitly to the CMake package config under `GBB_INSTALL_PREFIX` on every configure. The relocated library archive matched the current build, and both consumers passed against that prefix.
- **Files modified:** `cmake/RunInstalledConsumer.cmake`
- **Verification:** Final install/reconfigure and installed C/C++ consumer tests passed.
- **Committed in:** `0cbac03`

**2. [Rule 3 - Blocking issue] Preserve relative relocated-prefix input through CMake configuration**
- **Found during:** Task 1 verification
- **Issue:** A `PATH` cache entry normalized the relative install-prefix argument against the process working directory before the test registration logic could resolve it from the build root.
- **Fix:** Store the test prefix as `STRING` and resolve relative values against `CMAKE_BINARY_DIR` before registration.
- **Files modified:** `tests/CMakeLists.txt`
- **Verification:** `cmake --preset phase1 -DGBB_TEST_INSTALL_PREFIX=relocated-prefix` retained the relative value and registered every required target.
- **Committed in:** `d33d967`

**Total deviations:** 2 auto-fixed blocking issues (Rule 3)
**Impact on plan:** Both fixes were needed to make relocated installed-package verification reliable. No public API or installed fixture allow-list changed.

## Issues Encountered

The relocated build initially selected a stale package prefix. The guest failure, cached imported target, and archive identity established the cause; pinning `GabbaBoy_DIR` per configure fixed it. FF55 reset behavior also required checking the twin through data and timing predicates rather than an indistinguishable status value.

## User Setup Required

None - no external service or credentials are required.

## Next Phase Readiness

Phase 13 Wave 8 Plan 13-10 is complete. Continue with Phase 13 Wave 9 Plan 13-11, **Atomic consumer claims and executable documentation contracts**, using `/gsd-execute-phase 13 --wave 9`. CGB-07 remains open pending phase-level closure; physical CGB-E qualification remains unproven and Phase 14 remains unstarted. Both auto-advance flags remain false.

---
*Phase: 13-cgb-hdma*
*Completed: 2026-10-14*
