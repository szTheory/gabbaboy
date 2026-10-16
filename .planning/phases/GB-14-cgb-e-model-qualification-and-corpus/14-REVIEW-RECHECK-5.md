---
phase: GB-14-cgb-e-model-qualification-and-corpus
reviewed: 2026-10-16T03:16:33Z
depth: standard
files_reviewed: 3
files_reviewed_list:
  - tests/CMakeLists.txt
  - tests/expected-tests.txt
  - .github/scripts/verify-cmake-floor.sh
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
status: clean
---

# Phase 14: Platform-Control Wiring Recheck

**Reviewed:** 2026-10-16T03:16:33Z
**Depth:** standard
**Files Reviewed:** 3
**Status:** clean

## Summary

The platform-control unittest classes are now registered as a required CTest, included in the expected test inventory, and selected by the CMake-floor job's early adapter gate. The change is test wiring only; it does not alter source behavior. No defect was found in the three-file delta.

## Narrative Findings (AI reviewer)

### Platform-Control Wiring Disposition

`tests/scripts/test-cgb-corpus-report.py` defines four tests in `CorpusReportNativeExecutableTests` and four in `CorpusReportBoundedProcessTests` (lines 143-289). The CTest entry at `tests/CMakeLists.txt:1338-1340` passes both class names to the unittest runner, which selects their eight methods. The CTest also receives the same 45-second timeout and `GBB_TEST_BUILD_DIR=${PROJECT_BINARY_DIR};GBB_CTEST_COMMAND=${CMAKE_CTEST_COMMAND}` environment as the neighboring corpus-report controls at lines 1352-1358.

The test name is present once in `tests/expected-tests.txt:1058`, so full-run inventory validation requires it. `.github/scripts/verify-cmake-floor.sh:46-49` adds the same test to the existing anchored `ctest -R` selection, preserving the floor job's configured CTest binary, `--test-dir`, `--no-tests=error`, and output-on-failure arguments. The change adds no job or dependency and remains compatible with the existing CTest invocation.

The supplied verbose CTest result reports all eight methods passing. I did not rerun the test during this review. The previous 1,137-case stream was stopped before this wiring change; a fresh 1,138-case stream remains pending, so this report makes no full-stream claim.

---

_Reviewed: 2026-10-16T03:16:33Z_
_Reviewer: the agent (gsd-code-reviewer)_
_Depth: standard_
