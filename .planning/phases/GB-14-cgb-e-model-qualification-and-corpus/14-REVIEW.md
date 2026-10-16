---
phase: GB-14-cgb-e-model-qualification-and-corpus
reviewed: 2026-10-16T03:08:57Z
depth: standard
files_reviewed: 70
files_reviewed_list:
  - .gitattributes
  - .github/scripts/verify-cmake-floor.sh
  - .github/workflows/ci.yml
  - .github/workflows/fixture-repro.yml
  - .gitignore
  - README.md
  - cmake/AgeFixtureProtocol.cmake
  - cmake/ScanForbiddenFixtures.cmake
  - cmake/VerifyMooneyeCgb.cmake
  - docs/audio-and-playback.md
  - docs/cgb-corpus.md
  - docs/cgb-profile.md
  - docs/model-gates.md
  - docs/native-integration.md
  - docs/preview.md
  - docs/support/unreleased.md
  - fixtures/age/ELIGIBILITY.md
  - fixtures/age/SOURCES.md
  - fixtures/age/manifest.json
  - fixtures/magentests/ELIGIBILITY.md
  - fixtures/mooneye-cgb/ELIGIBILITY.md
  - fixtures/mooneye-cgb/SOURCES.md
  - fixtures/mooneye-cgb/manifest.json
  - fixtures/samesuite/ELIGIBILITY.md
  - fixtures/samesuite/manifest.json
  - src/core/gabbaboy.c
  - src/player/limitations.h
  - src/runner/main.c
  - tests/CMakeLists.txt
  - tests/CheckCgbCorpusPackageControls.cmake
  - tests/expected-tests.txt
  - tests/external/cgb-apu-dispositions.json
  - tests/external/cgb-corpus-inventory.json
  - tests/external/cgb-ppu-dispositions.json
  - tests/external/cgb-speed-dispositions.json
  - tests/fuzz_core.c
  - tests/player/test_limitations.c
  - tests/scripts/check-age-fixture-protocol.cmake
  - tests/scripts/reproduce-age.sh
  - tests/scripts/reproduce-mooneye-cgb.sh
  - tests/scripts/reproduce-samesuite.sh
  - tests/scripts/run-cgb-red-evidence-privacy-test.py
  - tests/scripts/test-cgb-apu-source-eol.py
  - tests/scripts/test-cgb-corpus-report.py
  - tests/scripts/test-cgb-red-evidence-privacy.py
  - tests/scripts/test-reproduce-age.sh
  - tests/scripts/test_age_phase14_contract.py
  - tests/scripts/test_age_phase14_inherited_contract.py
  - tests/scripts/verify-age-m3-pixels.py
  - tests/scripts/verify-age-phase14-contract.py
  - tests/scripts/verify-cgb-apu-dispositions.py
  - tests/scripts/verify-cgb-corpus-artifacts.py
  - tests/scripts/verify-cgb-corpus-claims.py
  - tests/scripts/verify-cgb-corpus-inventory.py
  - tests/scripts/verify-cgb-corpus-report.py
  - tests/scripts/verify-cgb-hdma-claims.py
  - tests/scripts/verify-cgb-hdma-dispositions.py
  - tests/scripts/verify-cgb-speed-dispositions.py
  - tests/scripts/verify-external-dispositions.py
  - tests/test_age.c
  - tests/test_age_m3.c
  - tests/test_cgb_apu.c
  - tests/test_cgb_partition.c
  - tests/test_cgb_tables.c
  - tests/test_cgb_visibility.c
  - tests/test_magentests.c
  - tests/test_runner.c
  - tests/test_samesuite_apu.c
  - tests/test_samesuite_apu_membership.py
  - tests/test_samesuite_hdma.c
findings:
  critical: 8
  warning: 0
  info: 0
  total: 8
status: issues_found
---

# Phase 14: Code Review Report

**Reviewed:** 2026-10-16T03:08:57Z
**Depth:** standard
**Files Reviewed:** 70 cumulative unique paths
**Status:** issues_found

## Summary

This cumulative review combines the original 68-file Phase 14 source review with focused rechecks of the first Windows fixes and exact-head CI scopes. The earlier recheck added two previously unlisted paths, bringing cumulative unique coverage to 70; this review did not reread all 70 files. CR-01 through CR-06 are confirmed historical blockers with fixes independently rechecked. CR-07 was fixed in commit `f3b7ed4e3b03fa04d4e74dd9609705a530e676e9` and independently rechecked in `14-REVIEW-RECHECK-3.md`. CR-08 was fixed in commit `e373b3f2b32292035531ba0aad1d05e5a4a009d9` and independently rechecked in `14-REVIEW-RECHECK-4.md`.

## Narrative Findings (AI reviewer)

## Critical Issues

### CR-01: Build stamp looks up extensionless executable names on Windows

**Severity:** BLOCKER
**File:** `tests/scripts/verify-cgb-corpus-report.py:390-405`
**Issue:** `full_build_identity()` constructs artifact paths using extensionless names such as `build/gabbaboy-runner` and `build/tests/test_age`. Windows CMake builds these targets as `.exe` files, so the first `bounded_read()` fails with `input-unavailable`. The function is called by `--write-build-stamp`, which is an `ALL` custom target in `tests/CMakeLists.txt:1691-1699` and depends on these executables at `tests/CMakeLists.txt:4458-4461`; consequently the default `cmake --build --preset phase1` fails on the `native-windows` CI job.
**Reproduction:** On Windows, configure and build the Phase 1 preset; `cgb_corpus_build_stamp` invokes `verify-cgb-corpus-report.py --write-build-stamp`, then fails while reading the first executable because only `gabbaboy-runner.exe` exists.
**Fix:** Pass executable paths from CMake using `$<TARGET_FILE:...>` to the stamp command, or append `sysconfig.get_config_var("EXE")`/the platform executable suffix when constructing each path. Keep the recorded paths relative to the repository after resolving them.

### CR-02: Bounded subprocess reader cannot register Windows pipes

**Severity:** BLOCKER
**File:** `tests/scripts/verify-cgb-corpus-report.py:1433-1443`
**Issue:** `run_bounded()` registers `proc.stdout`, an anonymous pipe, with `selectors.DefaultSelector`. On Windows, `DefaultSelector` uses `SelectSelector`, which only supports sockets and rejects pipe handles. `full_build_identity()` calls this helper for `ctest --version` at line 470 while producing the same default build stamp, so even after correcting the executable suffixes, the Windows build still fails during stamp generation with a selector registration error.
**Reproduction:** Invoke `run_bounded(["ctest", "--version"])` on Windows or build the Phase 1 preset after fixing CR-01; the `selector.register(proc.stdout, ...)` call fails before the report can be generated.
**Fix:** Use a Windows-compatible bounded pipe reader (for example, a dedicated reader thread with a byte cap and timeout/kill handling) or use a bounded `subprocess.run(capture_output=True, timeout=...)` path for the short version query. Preserve the output limit and process cleanup guarantees on both platforms.

### CR-03: Configured builds fall back to the default build directory

**Severity:** BLOCKER
**File:** `tests/CMakeLists.txt:1003-1011, 1349-1354`; `tests/scripts/test-cgb-corpus-report.py:19-22`; `tests/scripts/verify-cgb-apu-dispositions.py:354-368`
**Issue:** The CMake floor job originally configured a nondefault build tree while the APU membership/controls and corpus-report adapters fell back to `ROOT/build`. GitHub Actions job `116778422523` in run `38840242246` (`cmake-floor-3.25.3`) failed five Phase 14 adapter tests because the configured executables and CTest files were not in that default directory.
**Reproduction:** Configure and build with `-B <nondefault-build-dir>`, leave `<repo>/build` absent, then run the five listed adapter CTests; before the fix, APU validation and report tracer/control paths query or create files under `<repo>/build`.
**Fix:** CTest now passes `PROJECT_BINARY_DIR` and `CMAKE_CTEST_COMMAND` to the adapters (environment or explicit CLI arguments). The tracer receipt control asserts that its executable identity uses the configured build directory. Commit `2bd8c1c13a8ac3e4ed303b82993824f68d95fb3f` reproduced the five failures in RED and passed the same selection 5/5 in GREEN. The exact hosted CMake 3.25.3 run remains pending.

### CR-04: Windows checkout rewrites raw-digested source bytes

**Severity:** BLOCKER
**File:** `.gitattributes:79-81`; `tests/scripts/verify-cgb-apu-dispositions.py:47-48, 136-141`; `tests/scripts/test-cgb-apu-source-eol.py:41-92`
**Issue:** The APU membership verifier hashes the raw bytes of `tests/test_samesuite_apu.c` and `src/core/gabbaboy.c`. Windows `core.autocrlf=true` rewrote their checkout bytes, so Windows job `116778422560` in Actions run `38840242246` failed the APU membership and controls digest checks.
**Reproduction:** Check out the sources with Windows autocrlf conversion and run the APU membership verifier; the source digests no longer match the recorded harness/core hashes.
**Fix:** Pin both hashed files to LF with `.gitattributes`. The new isolated-Git control verifies index and checkout bytes with local `core.autocrlf=true`, and verifies that an unpinned negative control converts to CRLF. Commit `740fcd0a70c33d1bdb46b310c150cbe507b60461` contains this fix. The actual Windows-hosted rerun remains pending.

### CR-05: AGE row identity uses a slash-only basename

**Severity:** BLOCKER
**File:** `tests/test_age.c:295-310, 428-455, 477-493, 741-754`
**Issue:** The AGE observation row ID was derived with slash-only basename handling, so a Windows ROM path containing backslashes produced a row identity that did not match the pinned Phase 14 assertion ID. Windows job `116778422560` in Actions run `38840242246` reported an identity mismatch for `spsw-ch2-lc-delay-cgbBCE`.
**Reproduction:** Run the Phase 14 AGE observation path with a Windows-style ROM path; the prior implementation retained directory components in the row ID.
**Fix:** Reuse the bounded `age_case_name()` helper for row identity and the Phase 14 control. The added control covers forward, backslash, mixed, and basename spellings, invalid inputs, and exact output-buffer boundaries while leaving pinned rows/signatures unchanged. Commit `75451727cd25822336fe44d8d4c50b2c1d3915a5` contains the fix. The actual Windows-hosted rerun remains pending.

### CR-06: Missing-ROM control rewrites the pinned manifest

**Severity:** BLOCKER
**File:** `cmake/VerifyMooneyeCgb.cmake:139-153`
**Issue:** The missing-ROM negative control serialized the parsed manifest with `file(WRITE)`, changing its raw bytes and causing the runner to reject it as `invalid-manifest` (exit 2) before reaching the intended missing-fixture check (exit 3). This failure was observed in Windows job `116778422560` in Actions run `38840242246`.
**Reproduction:** Run the Mooneye controls mode on Windows; the `missing-required-rom` control sees a reserialized manifest whose digest differs from the pinned manifest.
**Fix:** Copy the manifest byte-for-byte with `file(COPY_FILE)`, compare source/copy SHA-256 digests, then invoke the runner on the copy. Preserve the expected `missing-fixture` failure and keep the model/mode/signature controls unchanged. Commit `5d2ca71a8edce03a118ec53f0b7d70220a5432d0` contains the fix. The actual Windows-hosted rerun remains pending.

### CR-07: Build stamp fingerprints a different CTest than its consumers

**Severity:** BLOCKER
**File:** `tests/CMakeLists.txt:1005-1009, 1349-1354, 1701-1705`; `tests/scripts/verify-cgb-corpus-report.py:27, 478-485, 550-573, 577-583`
**Issue:** The corpus-report tests receive `GBB_CTEST_COMMAND=${CMAKE_CTEST_COMMAND}`, but the `cgb_corpus_build_stamp` custom target originally invoked `--write-build-stamp` without that environment or an explicit CTest path. `full_build_identity()` therefore fingerprinted the CTest found on `PATH` while later consumers could fingerprint the configured CTest. Since CTest path/version bytes contribute to `identity_sha256`, `verify_build_stamp()` rejected the configured-build receipt with `build-input-stamp-mismatch` whenever those executables differed. The floor verifier downloads CMake/CTest into a temporary directory without adding that directory to `PATH`, making the mismatch reachable for its configured CTest.
**Reproduction:** Configure with a CTest executable that differs from `PATH`'s `ctest`, build `cgb_corpus_build_stamp`, then run `verify-cgb-corpus-report.py --begin-run --build-dir <build-dir> --receipt <receipt>` with `GBB_CTEST_COMMAND` set to the configured CTest. Before the fix, the stamp was created with the PATH tool identity; `begin_corpus_run()` recomputed the configured tool identity and failed at `verify_build_stamp()`.
**Fix:** Commit `f3b7ed4e3b03fa04d4e74dd9609705a530e676e9` passes the configured CTest to the stamp target through `cmake -E env`. The focused control verifies the actual stamp against configured identity and rejects a substituted CTest digest with `build-input-stamp-mismatch`. Three focused report CTests and all 13 report-contract tests passed per the fix report; the hosted Windows and exact CMake 3.25.3 runs remain pending. This identity check protects receipt integrity by failing closed on a different CTest hash (T-14-21); subprocess bounds and cleanup relevant to T-14-22 are unchanged. No separate bypass was found in this focused recheck. See `14-REVIEW-RECHECK-3.md` and `14-REVIEW-FIX.iter3.md`.

### CR-08: AGE child deadline ignores sanitizer slowdown

**Severity:** BLOCKER
**File:** `tests/CMakeLists.txt:1357-1367`; `tests/scripts/verify-age-phase14-contract.py:226-230, 359-379, 597-607`; `tests/scripts/test_age_phase14_inherited_contract.py:25-59`
**Issue:** The `cgb_age_assertion_identity` adapter ran each of 13 AGE guests with a fixed 15-second `subprocess.run()` timeout. The ASan job's CTest timeout was scaled from 60 to 180 seconds, but that scaling did not change this nested Python child deadline. In the original ASan job `116778422483` in Actions run `38840242246`, the adapter's `stat-mode-ds-cgbBCE` child exceeded 15 seconds and failed; the job reported six failures, of which the other five were the configured-build-directory issue already recorded as CR-03.
**Reproduction:** Run the AGE assertion identity adapter under the sanitizer workload with a child taking longer than 15 seconds. The adapter raises `TimeoutExpired` despite the sanitizer-scaled outer CTest allowance.
**Fix:** Commit `e373b3f2b32292035531ba0aad1d05e5a4a009d9` sets the child deadline to 15 seconds normally and 45 seconds with `GABBABOY_ENABLE_SANITIZERS`, matching the existing threefold sanitizer policy. The script accepts only integer limits from 1 through 45 and supplies the selected timeout to every guest call. The new control verifies all 13 calls receive 45 seconds, rejects 0, 46, booleans, and fractional values, and confirms timeout exceptions propagate as failures. The fix report records the pre-fix RED regression, live AGE identity plus inherited-contract CTests passing 2/2, and 13 cases/142 rows passing with the 45-second child limit. The local macOS host rejects the Linux-only sanitizer preset; the actual hosted sanitizer rerun remains pending. This closes a bounded-completion gap relevant to T-14-20; guest budgets and expected outcomes are unchanged.

---

_Reviewed: 2026-10-16T03:08:57Z_
_Reviewer: the agent (gsd-code-reviewer)_
_Depth: standard_
