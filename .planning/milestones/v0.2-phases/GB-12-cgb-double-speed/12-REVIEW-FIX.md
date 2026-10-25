---
phase: GB-12-cgb-double-speed
fixed_at: 2026-10-14T12:12:06Z
review_path: .planning/phases/GB-12-cgb-double-speed/12-REVIEW.md
iteration: 1
findings_in_scope: 2
fixed: 2
skipped: 0
status: all_fixed
---

# Phase GB-12: Code Review Fix Report

**Fixed at:** 2026-10-14T12:12:06Z  
**Source review:** `.planning/phases/GB-12-cgb-double-speed/12-REVIEW.md`  
**Iteration:** 1

**Summary:**
- Findings in scope: 2
- Fixed: 2
- Skipped: 0

## Fixed Issues

### CR-01: [BLOCKER] TMPDIR can inject commands through the cleanup trap

**Files modified:** `.github/scripts/verify-test-inventory.sh`, `.github/scripts/test-inventory-cleanup.sh`  
**Commits:** `be53c43`; root regression-confinement follow-up `d979ba5`  
**Applied fix:** Replaced the interpolated trap with a literal EXIT body that reads a script-scope cleanup path after the self-test function returns. The self-test uses an explicit TMPDIR-based `mktemp` template. Added a regression that verifies the fixed script removes scratch files without running a quote/metacharacter payload, and that a temporary copy with the original trap triggers the harmless marker as a negative control. The deliberately unsafe copy runs only under a fixture-owned `/tmp` prefix; inherited TMPDIR cannot contribute extra shell source to that negative-control harness.

### WR-01: [WARNING] Late Phase 12 CTest timeouts bypass sanitizer scaling

**Files modified:** `tests/CMakeLists.txt`, `tests/expected-tests.txt`, `cmake/ScaleSanitizerTimeouts.cmake`, `tests/check_sanitizer_timeout_policy.cmake`, `tests/cmake/timeout-policy/CMakeLists.txt`  
**Commit:** `fe61e2f`  
**Applied fix:** Moved sanitizer timeout scaling into one helper called after the final test registration and removed the manual AGE multipliers. Added configure-time checks for actual late Phase 12 tests, and a configure-only CTest regression that verifies normal values remain unchanged and sanitizer limits scale once, while early-scaler and double-scaler controls are detected.

## Verification

All checks ran in the canonical main checkout under the negotiated `ISOLATION=none` dispatch. The configure-only sanitizer probe exercised timeout properties with the sanitizer flag enabled on Darwin; no ASan/UBSan runtime was run or claimed on this host.

- `bash -n .github/scripts/verify-test-inventory.sh .github/scripts/test-inventory-cleanup.sh` passed.
- `bash .github/scripts/verify-test-inventory.sh --self-test` passed. The fixed TMPDIR case cleaned its scratch path without creating the marker; the original-trap mutant created the marker and left its temporary child for the regression to detect.
- `cmake -DGBB_SOURCE_DIR="$PWD" -DGBB_BINARY_DIR="$PWD/build" -P tests/check_sanitizer_timeout_policy.cmake` passed. Normal values stayed 120/240/60; sanitizer values were 360/720/180; early-scaler and double-scaler negative controls were detected.
- `cmake -S . -B build` passed, and `ctest --test-dir build -R '^sanitizer_timeout_policy_selftest$' --output-on-failure` passed 1/1. Generated normal-build CTest properties were 120, 30, 240, 240, 60, 60, and 30 seconds for the checked AGE, partition, and policy cases.
- `cmake --build build` passed. A fresh full run, `ctest --test-dir build --output-on-failure`, passed 898/898 in 230.77 seconds.
- An earlier full run had one failure (`cgb_speed_mutant_m7_xfail_ppu`); its isolated rerun passed, and it did not recur in the fresh 898/898 run. The cause of that one-off failure was not established.

---

_Fixed: 2026-10-14T12:12:06Z_  
_Fixer: the agent (gsd-code-fixer)_  
_Iteration: 1_

## Root Verification Follow-up

- Fresh inventory self-test passed its exact platform-filter checks and cleanup trap regression. A nested hostile caller TMPDIR left its parent marker absent; the old inherited-prefix helper mutation triggered that benign marker. This closes the regression-harness data-flow gap as part of CR-01.
- Fresh `ctest --test-dir build -R '^(sanitizer_timeout_policy_selftest|cgb_speed_xfail_pause_ppu_output|cgb_speed_mutant_m7_xfail_ppu)' --output-on-failure --no-tests=error` passed 4/4, including both PPU controls and the timeout policy.
- `cgb_speed_mutant_m7_xfail_ppu` passed 100 consecutive executions under CTest `--repeat until-fail:100`. The prior isolated failure's detailed output was not preserved and its cause remains unknown; no assertion or fixture was changed to absorb it. Final regression and hosted CI checks remain required.

## Independent Follow-up WR-02

The follow-up review found a child-directory gap in the timeout policy, recorded in `12-REVIEW-FOLLOWUP.md`. The optional player now calls the shared helper after its own final registration. A child-directory policy probe verifies normal 120/240/300 and sanitizer 360/720/900 limits, and detects the parent-only omission. A configure-only wrapper around the actual player test directory agrees; omitting its call fails the real configure assertion. CMake configure/build and full CTest passed 898/898 in 52.66 seconds after this fix. The original two-finding report above remains historical; the additional follow-up finding is fixed with zero open follow-up dispositions.
