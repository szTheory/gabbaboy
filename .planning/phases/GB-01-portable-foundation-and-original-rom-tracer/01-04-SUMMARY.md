---
phase: 01-portable-foundation-and-original-rom-tracer
plan: 04
subsystem: infra
tags: [github-actions, ctest, cmake, asan, ubsan, rgbds]
requires:
  - phase: GB-01 Plans 01-03
    provides: "Portable tracer, named CTest cases, checked fixture, relocatable package, and C/C++ consumers"
provides:
  - "Pinned native Linux x64, macOS arm64, and Windows x64 CI jobs with a fail-closed required-native aggregate"
  - "An explicit CTest case inventory that rejects missing, skipped, failed, empty, and extra-case evidence"
  - "Linux AddressSanitizer/UndefinedBehaviorSanitizer and a digest-verified CMake 3.25.3 configure-to-relocation lane"
  - "A separate RGBDS v1.0.1 fixture-repro workflow and locally byte-verified original ROM recipe"
affects: [GB-01-05, required-checks, preview-packages]
actuals:
  tokens: 5697
  tasks: 2
  commits: 3
commits: 3
plan_head_before: db9f7b98adbac11c608500be1f94bba72240787b
plan_head_after: 585ff3aeb5f78bddf85c2753ffcd683795432f82
tech-stack:
  added: []
  patterns:
    - "Every native test report is compared with a checked-in required inventory; installed consumer cases are conditional but explicit"
    - "Tool floor qualification uses the official archive digest and a relocated installed-consumer run"
key-files:
  created:
    - .github/workflows/ci.yml
    - .github/workflows/fixture-repro.yml
    - .github/scripts/verify-cmake-floor.sh
    - .github/scripts/verify-test-inventory.sh
    - cmake/ExpectedTests.cmake
    - tests/expected-tests.txt
  modified:
    - CMakeLists.txt
    - CMakePresets.json
    - tests/CMakeLists.txt
    - .gitignore
    - README.md
    - .planning/context/LESSONS.md
key-decisions:
  - "Use explicit ubuntu-22.04, macos-14, and windows-2022 runner labels; do not infer product OS support from those labels."
  - "Keep hosted CI and branch-protection evidence pending until the project has a remote and an exact-revision run."
  - "Treat the RGBDS regeneration check as an independent fixture-repro status context, separate from required-native."
requirements-completed: [BASE-05]
coverage:
  - id: D1
    description: "The required native workflow checks all configured lanes and fails closed on missing or skipped test evidence."
    verification:
      - kind: integration
        ref: "actionlint .github/workflows/ci.yml .github/workflows/fixture-repro.yml; local CTest report inventory checks; skipped and incomplete report controls"
        status: pass
    human_judgment: false
  - id: D2
    description: "The CMake 3.25.3 Linux x64 floor script verifies the official digest and relocated installed consumers."
    verification:
      - kind: integration
        ref: "bash .github/scripts/verify-cmake-floor.sh in an Ubuntu 22.04 x86_64 container; 21 initial and 24 relocated cases passed"
        status: pass
    human_judgment: false
  - id: D3
    description: "RGBDS v1.0.1 regenerates the original tracer ROM byte-for-byte and matches its manifest SHA-256."
    requirement: BASE-05
    verification:
      - kind: integration
        ref: "Pinned RGBDS v1.0.1 release regeneration in an Ubuntu x86_64 container; cmp and manifest digest passed"
        status: pass
      - kind: unit
        ref: "ctest --test-dir build --output-on-failure --no-tests=error -R fixture_digest"
        status: pass
    human_judgment: false
  - id: D4
    description: "Exact-revision hosted CI results and configured branch-protection contexts are not yet observed."
    verification:
      - kind: other
        ref: "No Git remote is configured; no hosted workflow run or branch-protection inspection is available."
        status: unknown
    human_judgment: true
    rationale: "This evidence depends on repository hosting and an exact-revision remote run. Local workflow checks cannot establish it."
duration: 31min
completed: 2026-10-03
status: complete
---

# Phase 1 Plan 4: Native CI and Fixture Reproducibility Summary

**Pinned native CI lanes now enforce an explicit executed-test inventory, Linux sanitizers, the CMake 3.25.3 floor, and a separate byte-identical RGBDS fixture check.**

## Performance

- **Duration:** 31 min
- **Started:** 2026-10-03T13:20:18Z
- **Completed:** 2026-10-03T13:50:49Z
- **Tasks:** 2
- **Files modified:** 12

## Accomplishments

- Added explicit Ubuntu 22.04 x64, macOS 14 arm64, and Windows Server 2022 x64 jobs, with a `required-native` gate that rejects any non-success dependency result.
- Added the 24-case inventory, CMake registration checks, JUnit inventory validation, skipped-case rejection, and Linux ASan/UBSan compiler and linker flag checks.
- Added the official-digest-verified CMake 3.25.3 configure/build/test/install/relocate/consumer script and separate RGBDS v1.0.1 byte-reproduction workflow.
- Documented current CI evidence limits and recorded the CTest inventory/report-path lesson.

## Task Commits

1. **Task 1: Require native matrix, executed-case inventory, and Linux sanitizers** — `63c305e` (`feat`)
2. **Task 2: Rebuild the fixture with pinned RGBDS in isolated CI** — `ae737bf` (`feat`)

3. **Plan closeout correction: document local CMake 3.25.3 evidence** — `585ff3a` (`docs`)

**Measured plan commits:** 3, from `db9f7b98adbac11c608500be1f94bba72240787b` through `585ff3aeb5f78bddf85c2753ffcd683795432f82`.

## Files Created/Modified

- `.github/workflows/ci.yml` — native lanes, sanitizer and floor jobs, and required aggregate.
- `.github/workflows/fixture-repro.yml` — separately named pinned RGBDS byte and digest check.
- `.github/scripts/verify-cmake-floor.sh` — official digest, exact CMake version, package relocation, and installed consumer verification.
- `.github/scripts/verify-test-inventory.sh`, `cmake/ExpectedTests.cmake`, and `tests/expected-tests.txt` — configured and executed case inventory enforcement.
- `CMakeLists.txt` and `CMakePresets.json` — Linux sanitizer option and dedicated sanitizer/floor presets.
- `tests/CMakeLists.txt` — verify registered cases against the checked-in inventory.
- `.gitignore` — ignore generated `build-*` preset output directories.
- `README.md` — CI jobs, fixture preparation, evidence limits, and platform-claim boundaries.
- `.planning/context/LESSONS.md` — records the CTest report-path and conditional-inventory finding.

## Decisions Made

- CI uses explicit runner image labels and does not treat them as product minimum OS claims.
- The RGBDS fixture check has its own `fixture-repro` status context, independent from `required-native`.
- Local passing runs are reported as local evidence; hosted status and branch-protection evidence remain pending without a remote.

## Verification Evidence

- macOS local configure/build and installed-package CTest: 24/24 cases passed; the JUnit inventory matched all 24 names.
- Ubuntu 22.04 x86_64 sanitizer preset with CMake 3.25.3: cache option was ON, compiler and linker commands contained `-fsanitize=address,undefined`, and all 21 core cases passed.
- The CMake 3.25.3 floor script verified the official SHA-256, then passed configure/build/test/install and relocated runner plus C/C++ consumer checks: 21/21 before install and 24/24 after relocation.
- The CTest inventory helper rejected both a skipped case and an incomplete report. `actionlint` and shell syntax checks passed.
- The pinned RGBDS v1.0.1 Linux x64 release regenerated identical fixture bytes and matched manifest SHA-256 `85d84babe64e852babc55fe355919f9d2f8013f90dc56550d58e972470321f77`; local `fixture_digest` passed 1/1.
- No hosted CI run, Windows native result, configured required-check context, or branch-protection inspection exists because no Git remote is configured.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Added the sanitizer option and configure-time CTest inventory guard**
- **Found during:** Task 1
- **Issue:** The plan required an ASan/UBSan preset and a required case inventory, but the project did not yet expose a sanitizer cache option or reject a mismatch between registered and required cases.
- **Fix:** Added a Linux-only GCC/Clang sanitizer option and a CMake inventory check; the workflow compares executed JUnit cases, rejects skips, and gates all five evidence jobs.
- **Files modified:** `CMakeLists.txt`, `CMakePresets.json`, `tests/CMakeLists.txt`, `cmake/ExpectedTests.cmake`, `tests/expected-tests.txt`, `.github/scripts/verify-test-inventory.sh`, `.github/workflows/ci.yml`
- **Verification:** 21 sanitizer cases and 24 installed cases passed; deliberate skipped and incomplete reports were rejected.
- **Committed in:** `63c305e`

**2. [Rule 1 - Bug] Matched the RGBDS version output used by the reproducibility job**
- **Found during:** Task 2
- **Issue:** RGBDS prints `rgbasm v1.0.1`; the initial CI check expected a different capitalization and label.
- **Fix:** Checked the tool's actual version string, then verified the official release binary rebuilt identical bytes and manifest digest.
- **Files modified:** `.github/workflows/fixture-repro.yml`
- **Verification:** The pinned RGBDS 1.0.1 reproduction passed in an Ubuntu x86_64 container.
- **Committed in:** `ae737bf`

**3. [Rule 1 - Bug] Wrote CTest JUnit reports to the selected build directory**
- **Found during:** Task 1
- **Issue:** A relative `--output-junit build/ctest.xml` path was resolved from CTest's selected `build` directory, so the inventory helper looked in the wrong location.
- **Fix:** Use a report basename for `--test-dir` and preset runs; use the resulting build-directory path when checking it. The floor script writes its report to an absolute temporary path.
- **Files modified:** `.github/workflows/ci.yml`, `.github/scripts/verify-cmake-floor.sh`
- **Verification:** Local macOS and Linux reports matched the exact expected 24 and 21 test inventories; incomplete and skipped report controls failed.
- **Committed in:** `63c305e`

**4. [Rule 2 - Missing Critical] Ignored generated preset build directories**
- **Found during:** Task 1
- **Issue:** The new `build-asan` and CMake floor presets produce repository-root build directories outside the existing `/build/` ignore rule.
- **Fix:** Added `/build-*/` to `.gitignore` so local verification outputs do not appear as source changes.
- **Verification:** Generated sanitizer and floor directories remained untracked build output; the final working tree contains only pre-existing `.gsd/` and `.planning/milestone.lock` untracked entries.
- **Committed in:** `63c305e`

**5. [Rule 1 - Bug] Updated the CMake floor statement after its local verification passed**
- **Found during:** Plan closeout
- **Issue:** The README still described CMake 3.25.3 as unqualified after the official-digest floor script passed in the Ubuntu x86_64 container.
- **Fix:** Record the local container result while keeping hosted CI and other OS/compiler evidence pending.
- **Files modified:** `README.md`
- **Verification:** The floor script passed official digest, version, configure/build/test/install, relocation, runner, and C/C++ consumer checks.
- **Committed in:** `585ff3a`

**Total deviations:** 5 auto-fixed (Rule 1: 3; Rule 2: 2). **Impact on plan:** These changes supply the missing enforcement, correct workflow reporting, and accurate evidence documentation needed to make the planned CI checks executable and fail closed.

## Issues Encountered

- The sanitizer preset correctly rejected the macOS host. The full sanitizer check then passed in an Ubuntu 22.04 x86_64 container; the first container attempt used arm64 and could not execute the pinned x64 CMake archive, so the container was explicitly run as `linux/amd64`.
- CTest resolves relative JUnit output paths from its selected test directory. The workflow was corrected to write a basename in each build directory, and the floor script uses an absolute temporary report path.
- The first RGBDS version assertion used the wrong display string; it was corrected before commit and the actual pinned release reproduced the fixture.

## User Setup Required

None for local build or fixture regeneration beyond explicitly preparing RGBDS v1.0.1. Hosted PR checks require a repository remote and configured branch protection, which are not present.

## Next Phase Readiness

- Plan 04 is complete. BASE-05 now has a reviewed authored-source license/notice record plus a successful local pinned-tool byte reproduction.
- BASE-07 remains pending until the required jobs run on an exact hosted revision and the repository's required-check configuration is inspected. Windows execution and native Linux hosted evidence are also pending.
- The next stage is **Phase 1 Plan 05: Revision-linked Foundation Preview Packages**. Continue with `$gsd-execute-phase 1`; stop after Phase 1 and do not enter Phase 2.

---
*Phase: 01-portable-foundation-and-original-rom-tracer*
*Completed: 2026-10-03*

## Self-Check: PASSED

- All six created key files exist; task commits `63c305e` and `ae737bf` plus documentation correction `585ff3a` exist.
- The measured plan commit count is 3 from the recorded base through the plan-change head.
- No tracked files were deleted, no stub patterns were found in plan changes, and final local verification passed after the resolved attempts described above.
