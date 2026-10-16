---
phase: GB-14-cgb-e-model-qualification-and-corpus
reviewed: 2026-10-16T01:49:17Z
depth: standard
files_reviewed: 68
files_reviewed_list:
  - .gitattributes
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
  critical: 2
  warning: 0
  info: 0
  total: 2
status: issues_found
---

# Phase 14: Code Review Report

**Reviewed:** 2026-10-16T01:49:17Z  
**Depth:** standard  
**Files Reviewed:** 68  
**Status:** issues_found

## Summary

The review covered the Phase 14 runtime, corpus validators, CMake wiring, manifests, and CI paths. The CGB report build-stamp target has two independent Windows portability defects that prevent the native Windows build from completing. The existing CI workflow runs this target as part of the default build.

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

---

_Reviewed: 2026-10-16T01:49:17Z_  
_Reviewer: the agent (gsd-code-reviewer)_  
_Depth: standard_
