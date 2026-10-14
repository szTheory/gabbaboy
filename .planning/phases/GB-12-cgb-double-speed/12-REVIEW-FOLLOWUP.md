---
phase: GB-12-cgb-double-speed
reviewed: 2026-10-14
scope_diff: be53c43^..d979ba5
scope_commits:
  - be53c43
  - fe61e2f
  - d979ba5
files_reviewed: 7
findings:
  blocker: 0
  warning: 1
  total: 1
status: issues_found
findings_fixed: 1
findings_open: 0
---

# Phase GB-12 Code Review Fix Follow-up

This independent follow-up reviewed the fixes in `be53c43`, `fe61e2f`, and `d979ba5`, covering `be53c43^..d979ba5`:

- `.github/scripts/test-inventory-cleanup.sh`
- `.github/scripts/verify-test-inventory.sh`
- `cmake/ScaleSanitizerTimeouts.cmake`
- `tests/CMakeLists.txt`
- `tests/check_sanitizer_timeout_policy.cmake`
- `tests/cmake/timeout-policy/CMakeLists.txt`
- `tests/expected-tests.txt`

CR-01's cleanup trap now evaluates a literal command whose path is expanded as a quoted argument. The unsafe-trap negative control confines its marker and injected TMPDIR path beneath its own `mktemp` directory. WR-01's manual AGE multipliers are removed, and the late Phase 12 tests have explicit sanitizer-timeout assertions. One gap remains for tests registered in a child CMake directory.

## Verification

- `bash -n` passed for both inventory scripts. `bash .github/scripts/verify-test-inventory.sh --self-test` passed: the fixed trap cleaned the hostile-TMPDIR test directory without creating the marker, while the unsafe mutant triggered only the fixture's benign marker and was detected by its leftover-directory check.
- `tests/check_sanitizer_timeout_policy.cmake` passed in an isolated scratch directory. Normal limits stayed `120/240/60/120`; sanitizer limits became `360/720/180/360`; the early-scaler and double-scaler negative controls were both detected.
- An isolated sanitizer-enabled project configure, using a Linux target setting with the host AppleClang compiler and the optional player disabled, passed the six actual late-test assertions in `tests/CMakeLists.txt` (including the AGE, sensitivity, and CGB partition cases). This was configure-only evidence; no test binaries were run.
- A separate parent/child CMake probe using the shared helper left the child test at `TIMEOUT 120` with sanitizers enabled. The current normal-build CTest manifest also retains the expected unscaled limits for representative late tests.
- No full CTest suite or ASan/UBSan runtime was run in this follow-up. The parent was using the shared build directory. The optional-player sanitizer configure could not be completed because the available SDL3 version is 3.4.10 while the project requires exactly 3.4.18.

## Remaining Findings

### WR-02: [WARNING] Sanitizer timeout scaling omits child-directory tests

**File:** `cmake/ScaleSanitizerTimeouts.cmake:6-11`; called from `tests/CMakeLists.txt:3517-3518`

**Issue:** The helper reads only the current directory's `TESTS` property. `tests/CMakeLists.txt` adds `tests/player` as a child at lines 1055-1057 before calling the helper, but the helper does not walk child directories. As a result, explicit player limits such as `player_cgb_speed_smoke` at `tests/player/CMakeLists.txt:75` and `player_cgb_cli` at line 119 remain 120 and 240 seconds in sanitizer builds. A slow sanitizer run can therefore time out before the test reports its result.

**Fix:** Invoke the shared scaler at the end of each test directory after that directory's registrations, or make the helper enumerate and scale descendant directories. Add a child-directory case to the timeout-policy regression so this boundary stays covered.

## Material Limits

The earlier `cgb_speed_mutant_m7_xfail_ppu` one-off failure still has no established cause. The recorded later serial run passed 898/898 and the test passed 100 repeated controls; no pin or assertion was weakened. This follow-up did not rerun those tests or claim ASan runtime evidence.

## Root Disposition and Verification

| Finding | Disposition | Evidence |
|---------|-------------|----------|
| WR-02 | fixed | Commit `40e7f08`: `tests/player/CMakeLists.txt` calls the shared scaler once after its final registration. The CMake 3.25 floor requires each test directory to update its own properties. |

The timeout-policy self-test now includes a real child CMake directory with 120/240/300 second limits. Normal values remain unchanged and sanitizer values become 360/720/900. The parent-only negative control leaves the child's limits unchanged and is detected; the existing early and double controls remain effective.

A configure-only wrapper also exercised the actual `tests/player/CMakeLists.txt` with stub link targets, preserving normal 120/240/300 limits and producing sanitizer 360/720/900 limits. A scratch copy omitting the child scaler failed the actual `player_cgb_speed_smoke expected 360` assertion. This is test-property evidence, not an SDL build or sanitizer runtime claim.

After the fix, the configured regression command (CMake configure/build and CTest with `CTEST_PARALLEL_LEVEL=8`) passed 898/898 in 52.66 seconds. No fixture or output pin changed. Hosted sanitizer and optional-player checks remain required on the pushed revision.
