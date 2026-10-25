---
phase: GB-14-cgb-e-model-qualification-and-corpus
reviewed: 2026-10-16T02:59:35Z
depth: standard
files_reviewed: 11
files_reviewed_list:
  - .gitattributes
  - .github/scripts/verify-cmake-floor.sh
  - cmake/VerifyMooneyeCgb.cmake
  - tests/CMakeLists.txt
  - tests/expected-tests.txt
  - tests/scripts/test-cgb-apu-source-eol.py
  - tests/scripts/test-cgb-corpus-report.py
  - tests/scripts/verify-cgb-apu-dispositions.py
  - tests/scripts/verify-cgb-corpus-report.py
  - tests/test_age.c
  - tests/test_samesuite_apu_membership.py
findings:
  critical: 1
  warning: 0
  info: 0
  total: 1
status: issues_found
---

# Phase 14: CI Fix Review Recheck

**Reviewed:** 2026-10-16T02:59:35Z
**Depth:** standard
**Files Reviewed:** 11
**Status:** issues_found

## Summary

The specified 11-file exact-head scope confirms CR-03 through CR-06 are fixed as reported. One integration defect remains: build-stamp creation fingerprints the ctest found on PATH, while configured-build consumers can fingerprint CMAKE_CTEST_COMMAND; the stored identity then fails verification when the executables differ. The fixer-reported 9 focused controls and 13 corpus-report tests were not rerun here. The exact hosted Windows and CMake 3.25.3 checks remain pending.

This pass directly reviewed the 11 listed paths. Nine were already included in the original 68-file review scope; the two new unique paths bring cumulative coverage to 70. This recheck does not claim that all 70 files were reread in this pass.

## Narrative Findings (AI reviewer)

### Original Finding Dispositions

- **CR-03 [BLOCKER] — FIXED.** The original cmake-floor-3.25.3 job in Actions run 116778422523 failed five adapters because they looked under the default ROOT/build while CMake configured a separate binary directory. The adapters now receive the configured build directory and CTest executable (tests/CMakeLists.txt:1003-1011, 1349-1354; tests/scripts/test-cgb-corpus-report.py:19-22, 31-67; tests/scripts/verify-cgb-apu-dispositions.py:354-368). Commit 2bd8c1c13a8ac3e4ed303b82993824f68d95fb3f records the fix; its report says the five pre-fix failures reproduced and the same selection passed 5/5 after the fix. Exact hosted floor execution remains pending.
- **CR-04 [BLOCKER] — FIXED.** The Windows job in Actions run 116778422560 failed two APU membership/control digest checks after checkout line-ending conversion changed raw-hashed source bytes. .gitattributes now pins the two raw-digested C sources to LF, and the new temporary-repository control checks index bytes, checkout bytes, and an unpinned CRLF negative control (.gitattributes:79-81; tests/scripts/test-cgb-apu-source-eol.py:41-92; digest consumers in tests/scripts/verify-cgb-apu-dispositions.py:47-48, 136-141). Commit 740fcd0a70c33d1bdb46b310c150cbe507b60461 records the fix; the Windows-hosted rerun remains pending.
- **CR-05 [BLOCKER] — FIXED.** The Windows job in Actions run 116778422560 reported an AGE row identity mismatch for spsw-ch2-lc-delay-cgbBCE because the identity parser only split on /. The shared bounded age_case_name() helper now handles both slash types, and controls cover POSIX, Windows, mixed, basename, invalid, and buffer-boundary inputs (tests/test_age.c:295-310, 428-455, 477-493, 741-754). Commit 75451727cd25822336fe44d8d4c50b2c1d3915a5 records the fix; pinned row values/signatures remain unchanged. The Windows-hosted rerun remains pending.
- **CR-06 [BLOCKER] — FIXED.** The Windows job in Actions run 116778422560 expected exit 3 / missing-fixture from the missing-ROM control but got exit 2 / invalid-manifest: file(WRITE) had reserialized the pinned manifest. The control now byte-copies the original and compares source/copy SHA-256 before invoking the runner (cmake/VerifyMooneyeCgb.cmake:139-153). Commit 5d2ca71a8edce03a118ec53f0b7d70220a5432d0 records the fix, preserving the expected reason and the other manifest controls. The Windows-hosted rerun remains pending.

### CR-07: Build stamp fingerprints a different CTest than its consumers

**Severity:** BLOCKER
**File:** tests/CMakeLists.txt:1005-1009, 1349-1354, 1701-1705; tests/scripts/verify-cgb-corpus-report.py:27, 478-485, 550-573, 577-583
**Issue:** CTest adapter tests receive GBB_CTEST_COMMAND=${CMAKE_CTEST_COMMAND}, but the cgb_corpus_build_stamp target invokes the report script without that environment or an explicit CTest executable. The script defaults to "ctest" and resolves it through PATH. full_build_identity() hashes that executable and version into identity_sha256; later configured-build consumers resolve CMAKE_CTEST_COMMAND, then verify_build_stamp() rejects the stamp if the tools differ. The floor script downloads CMake/CTest into a temporary directory without adding that directory to PATH, so the pinned floor CTest and PATH CTest can differ even though the adapter tests use the pinned executable.
**Reproduction:** Configure with one CTest executable while PATH resolves another, build cgb_corpus_build_stamp, then invoke verify-cgb-corpus-report.py --begin-run --build-dir <build-dir> --receipt <receipt> with GBB_CTEST_COMMAND set to the configured executable. Stamp creation records the PATH tool; begin_corpus_run() recomputes identity with the configured tool and returns build-input-stamp-mismatch.
**Fix:** Pass GBB_CTEST_COMMAND=${CMAKE_CTEST_COMMAND} into the build-stamp command (or accept an explicit CTest CLI argument) so the stamp and consumers bind the same executable. Add a positive control for configured-tool selection and a mutation control proving that a mismatched CTest identity is rejected.

The identity checks remain fail-closed, and the reviewed changes preserve bounded path parsing, exact source digests, and byte-equality checks for the missing-ROM manifest. No additional security-impact or bounds issue was confirmed in this scope. No hardware or actual hosted Windows/floor execution is claimed.

---

_Reviewed: 2026-10-16T02:59:35Z_
_Reviewer: the agent (gsd-code-reviewer)_
_Depth: standard_
