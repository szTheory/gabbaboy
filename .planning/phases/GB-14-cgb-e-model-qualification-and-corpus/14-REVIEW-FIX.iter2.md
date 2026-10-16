---
phase: 14
findings: [CR-03, CR-04, CR-05, CR-06]
fixed_at: 2026-10-16T02:52:39Z
commits:
  CR-03: 2bd8c1c13a8ac3e4ed303b82993824f68d95fb3f
  CR-04: 740fcd0a70c33d1bdb46b310c150cbe507b60461
  CR-05: 75451727cd25822336fe44d8d4c50b2c1d3915a5
  CR-06: 5d2ca71a8edce03a118ec53f0b7d70220a5432d0
  floor_failfast: 4c87879e4957b6f23e4376a561d8daec63ce75ae
findings_in_scope: 4
fixed: 4
skipped: 0
status: all_fixed
---

# Phase 14 Review Fix Report 2

## Changes

- **CR-03:** CTest now passes the configured binary directory and CTest executable through the APU and corpus-report adapter paths. Direct CLI defaults remain `ROOT/build`, and the tracer receipt test asserts that its reported runner comes from the configured build directory.
- **CR-04:** `.gitattributes` pins the two raw-digested APU source files to LF. A new CTest creates an isolated Git repository with local `core.autocrlf=true`, checks that their staged and checked-out bytes stay LF, and confirms an unpinned negative control checks out as CRLF.
- **CR-05:** The AGE runner now uses its shared bounded path-name helper for assertion-row IDs and the Phase 14 control. Its controls cover forward, backslash, mixed, and basename spellings; invalid inputs; and output-buffer boundaries. Expected row IDs, signatures, and emulator outcomes are unchanged.
- **CR-06:** The missing-ROM control copies the original manifest byte-for-byte and verifies source/copy SHA-256 equality before invoking the runner. Model, mode, and expected-signature controls remain unchanged.
- **CMake-floor early gate:** The pinned floor script runs the original five Phase 14 adapter tests immediately after the build and before the full suite.

Each fix and the floor-gate change was committed separately by GabbaBoy Automation with normal hooks.

## Fixed Issues

### CR-03: Configured builds fall back to the default build directory

CTest now passes the configured binary directory and CTest executable through the APU and corpus-report adapter paths. Direct CLI defaults remain `ROOT/build`, and the tracer receipt test asserts that its reported runner comes from the configured build directory.

### CR-04: Windows checkout rewrites raw-digested source bytes

`.gitattributes` pins the two raw-digested APU source files to LF. A new CTest creates an isolated Git repository with local `core.autocrlf=true`, checks that their staged and checked-out bytes stay LF, and confirms an unpinned negative control checks out as CRLF.

### CR-05: AGE row identity uses a slash-only basename

The AGE runner now uses its shared bounded path-name helper for assertion-row IDs and the Phase 14 control. Its controls cover forward, backslash, mixed, and basename spellings; invalid inputs; and output-buffer boundaries. Expected row IDs, signatures, and emulator outcomes are unchanged.

### CR-06: Missing-ROM control rewrites the pinned manifest

The missing-ROM control copies the original manifest byte-for-byte and verifies source/copy SHA-256 equality before invoking the runner. Model, mode, and expected-signature controls remain unchanged.

## Verification

- Before CR-03, the five alternate-build CTests reproduced the reported failures in an isolated checkout without `ROOT/build`; after the fix they passed 5/5.
- After all fixes, the original five adapter tests plus APU LF controls, AGE identity and path controls, and Mooneye controls passed 9/9 in the real `build-cmake-3.25.3` preset directory.
- The complete corpus-report unittest suite passed 13/13.
- The autocrlf control failed before the LF attributes with `pinned-source-eol-attribute-missing`, then passed with the positive LF checks and negative CRLF check.
- The AGE Phase 14 control printed `spellings=4 invalid=7 bounds=2` and passed with the pinned signature and row values unchanged.
- The Mooneye control passed with `missing-fixture` for the missing-ROM case, `invalid-manifest` for model and mode mutations, and the existing changed-signature diagnostics.
- CMake configure and required target builds passed; the floor script passed `bash -n`; Python syntax and `git diff --check` passed.

Verification ran in an isolated worktree on macOS with CMake 4.4.3 and Python 3.14.4. Windows autocrlf behavior was exercised in a temporary Git repository, but the actual Windows-hosted job has not yet rerun on these commits. The exact CMake 3.25.3 hosted integration check also remains pending.
