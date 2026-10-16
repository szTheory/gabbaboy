---
phase: 14
iteration: 3
findings_in_scope: 1
fixed: 1
skipped: 0
status: all_fixed
---

# Phase 14 configured CTest identity fix

## Fixed Issues

### CR-07: Build stamp fingerprints a different CTest than its consumers

The CMake stamp command now uses `cmake -E env` to pass the same `GBB_CTEST_COMMAND=${CMAKE_CTEST_COMMAND}` as its consumers. The report controls verify the real build stamp against the configured identity and reject a substituted CTest executable hash with `build-input-stamp-mismatch`.

Before the fix, a failing `ctest` decoy placed first on PATH made the real stamp target fail with `ctest-version-unavailable`. After the fix, the same decoy PATH build succeeded using the configured CTest. Three focused report CTests and all 13 report-contract tests passed. The decoy and its logs remain private temporary test inputs; no new dependency or hosted job was added.

The actual Windows and exact CMake 3.25.3 hosted runs remain pending for the final published revision. No earlier hosted result is relabeled as a pass for this fix.
