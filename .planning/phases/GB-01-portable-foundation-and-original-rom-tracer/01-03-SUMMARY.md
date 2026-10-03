---
phase: 01-portable-foundation-and-original-rom-tracer
plan: 03
subsystem: packaging
tags: [c17, cmake, install-export, cmake-package, c-consumer, cpp-consumer]
requires:
  - phase: 01
    provides: "Portable C17 DMG tracer core, bounded API, runner, and licensed original fixture"
provides:
  - "Relocatable GNUInstallDirs package exporting GabbaBoy::core and the public header"
  - "Installed headless runner and licensed tracer fixture files"
  - "Automated relocated runner, C consumer, and C++ consumer smoke tests"
  - "Documented offline build/install/embedding commands and evidence limits"
affects: [01-04, 01-05, api-consumers, ci, cmake-packaging]
actuals:
  tokens: 5203
  tasks: 3
  commits: 2
commits: 2
plan_head_before: 84bc83ce862df66bcf9aa9b6d93c5dd5ef237ab2
plan_head_after: 98a15c4a7ef9abbbe8699e80444b922be2d5baac
tech-stack:
  added: []
  patterns: ["GNUInstallDirs with install-tree target exports", "Downstream C/C++ projects consume only the relocated package"]
key-files:
  created: [cmake/GabbaBoyConfig.cmake.in, cmake/RunInstalledConsumer.cmake, tests/CMakeLists.txt, tests/consumers/c/CMakeLists.txt, tests/consumers/c/main.c, tests/consumers/cpp/CMakeLists.txt, tests/consumers/cpp/main.cpp]
  modified: [CMakeLists.txt, cmake/VerifyInstalledPackage.cmake, README.md]
key-decisions:
  - "Export the installed target as GabbaBoy::core and keep the source include path build-only."
  - "Register installed-package CTests only when the configured relocated prefix exists, preserving ordinary offline CTest runs."
  - "Document only the local macOS toolchain and consumer evidence; CMake 3.25.3 and other native platform floors remain unverified."
requirements-completed: [BASE-01, BASE-06]
coverage:
  - id: D1
    description: "Offline CMake installation exports a relocatable core package, public header, headless runner, and licensed tracer fixture."
    requirement: BASE-01
    verification:
      - kind: integration
        ref: "cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error (21/21 passed)"
        status: pass
      - kind: integration
        ref: "cmake --install build --prefix build/package-prefix; relocate prefix; VerifyInstalledPackage.cmake private-path and required-file scan"
        status: pass
    human_judgment: false
  - id: D2
    description: "The relocated runner and independent C and C++ projects execute the guest tracer using only installed package files."
    requirement: BASE-06
    verification:
      - kind: integration
        ref: "ctest --test-dir build --output-on-failure --no-tests=error -R 'installed_(runner|consumer_(c|cpp))' (3/3 passed on macOS arm64)"
        status: pass
    human_judgment: false
duration: 94min
completed: 2026-10-03
status: complete
---

# Phase 1 Plan 3: Relocatable Package and Installed Consumers Summary

**CMake now installs a relocatable `GabbaBoy::core` package, and downstream C and C++ consumers run the original tracer from a relocated prefix.**

## Performance

- **Duration:** 94 min
- **Started:** 2026-10-03T11:39:53Z
- **Completed:** 2026-10-03T13:13:21Z
- **Tasks:** 3
- **Files modified:** 10

## Accomplishments

- Added a GNUInstallDirs package containing the public C header and `GabbaBoy::core` export, standalone runner, and tracer ROM, manifest, and license.
- Added relocated-install integrity checks and CTest coverage for the installed runner plus independent C and C++ CMake consumers.
- Documented dependency preparation, local build/install commands, API ownership and bounded-run rules, tested local tool versions, and unsupported evidence claims.

## Task Commits

1. **Task 1: Prepare the ignored package staging prefix** — no commit; it created only the ignored `build/package-prefix` directory.
2. **Task 2: Export and install a relocatable `GabbaBoy::core` package** — `a48f254` (`feat(GB-01-03): install relocatable core package`).
3. **Task 3: Execute the original tracer from relocated C and C++ consumers** — `98a15c4` (`feat(GB-01-03): verify relocated C and C++ consumers`).

## Files Created/Modified

- `CMakeLists.txt` — adds relocatable install/export configuration and names the imported target `GabbaBoy::core`.
- `cmake/GabbaBoyConfig.cmake.in` — loads the installed namespaced target export.
- `cmake/VerifyInstalledPackage.cmake` — verifies required install files, private-path-free metadata, and runner execution from an unrelated working directory.
- `cmake/RunInstalledConsumer.cmake` — configures, builds, and runs each independent consumer against the installed prefix.
- `tests/CMakeLists.txt` — retains the existing test inventory and conditionally registers installed-package smokes.
- `tests/consumers/c/` and `tests/consumers/cpp/` — standalone consumers use the installed public header and imported target, read the installed fixture, and assert guest success and bounded trace output.
- `README.md` — documents offline build/install, relocation and consumer smoke commands, API contracts, local tool versions, and remaining limits.

## Decisions Made

- The install export explicitly renames the build target to `core`, yielding the promised `GabbaBoy::core` consumer name.
- Installed consumer tests register only when the configured relocated prefix exists, so an ordinary offline CTest run remains independent from installation state.
- The README reports the locally tested macOS toolchain and consumer evidence and leaves the CMake 3.25.3 floor plus Linux/Windows evidence pending the native CI plans.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Corrected the installed target name and consumer trace bounds**
- **Found during:** Task 3
- **Issue:** CMake aliases are not retained automatically in an install export, and a 64-record trace filled before the fixture reached its guest success marker.
- **Fix:** Set `EXPORT_NAME core`; consumers allocate a bounded 16,384-record trace and use the fixture's 200,000 half-dot budget.
- **Files modified:** `CMakeLists.txt`, `tests/consumers/c/main.c`, `tests/consumers/cpp/main.cpp`
- **Verification:** Both installed CTest consumers pass and assert the guest RAM success marker and nonempty bounded trace.
- **Committed in:** `98a15c4`

**2. [Rule 1 - Bug] Made relocated-runner paths independent of the caller's working directory**
- **Found during:** Task 3
- **Issue:** Relative prefix and working-directory arguments became invalid after the runner changed directories.
- **Fix:** Normalize prefix and runner working directory to absolute paths in the package verification script.
- **Files modified:** `cmake/VerifyInstalledPackage.cmake`
- **Verification:** Installed runner passes with the installed fixture from a separate working directory.
- **Committed in:** `98a15c4`

**3. [Rule 1 - Bug] Kept normal CTest independent of a stale install-prefix cache entry**
- **Found during:** Task 3
- **Issue:** A cached install-prefix setting caused installed tests to run after their prefixes had been intentionally removed for a clean offline suite.
- **Fix:** Register installed-package tests only when the configured relocated prefix currently exists.
- **Files modified:** `tests/CMakeLists.txt`
- **Verification:** Clean ordinary CTest passed 21/21 cases before installation; after relocation, installed runner and consumer CTests passed 3/3.
- **Committed in:** `98a15c4`

**Total deviations:** 3 auto-fixed (Rule 1: 3). **Impact:** Fixes ensure the exported consumer name, relocated runner, and clean offline test flow meet the plan's stated contracts.

## Issues Encountered

- Initial consumer runs found the target export alias omission, trace-capacity/budget mismatch, and a C++ `sizeof` compile error; each was corrected and verified by the installed smoke tests.
- The workspace initially denied Git index writes. The authorized GSD commits succeeded after the Git-writing invocation was run through the approval layer.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plan 03 package, relocation, runner, C consumer, and C++ consumer checks are complete locally on macOS arm64.
- Plan 04 should run the required native matrix, Linux sanitizers, and CMake 3.25.3 floor lane. No Linux/Windows consumer or minimum-OS support claim is made from this local run.

## Self-Check: PASSED

- The installed header, runner, fixture, manifest, license, package config, and target export exist in the relocated prefix.
- Commits `a48f254` and `98a15c4` exist; measured plan commits are 2 from base `84bc83ce862df66bcf9aa9b6d93c5dd5ef237ab2` through `98a15c4a7ef9abbbe8699e80444b922be2d5baac`.
- Clean local suite passed 21/21 tests; installed runner and C/C++ consumer suite passed 3/3 tests.

---
*Phase: 01-portable-foundation-and-original-rom-tracer*
*Completed: 2026-10-03*
