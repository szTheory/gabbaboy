---
phase: GB-12-cgb-double-speed
reviewed: 2026-10-14T03:33:17Z
depth: standard
files_reviewed: 75
files_reviewed_list:
  - .github/scripts/verify-test-inventory.sh
  - .github/workflows/ci.yml
  - .github/workflows/fixture-repro.yml
  - .github/workflows/preview.yml
  - .gitignore
  - README.md
  - THIRD_PARTY_NOTICES.md
  - cmake/ExpectedTests.cmake
  - cmake/P12Mutants.cmake
  - docs/cartridge-and-saves.md
  - docs/cgb-profile.md
  - docs/mbc3-rtc-evidence.md
  - docs/model-gates.md
  - docs/native-integration.md
  - docs/preview.md
  - docs/support/unreleased.md
  - fixtures/age/ELIGIBILITY.md
  - fixtures/age/LICENSE.txt
  - fixtures/age/SOURCES.md
  - fixtures/age/WARNING.md
  - fixtures/age/manifest.json
  - fixtures/age/spsw-ch2-lc-delay-cgbBCE.gb
  - fixtures/age/spsw-div-cgbBCE.gb
  - fixtures/age/spsw-interrupts-cgbE.gb
  - fixtures/age/spsw-mode0-cgbBCE.gb
  - fixtures/age/spsw-stop-prefetch-cgbBCE.gb
  - fixtures/age/spsw-tima-cgbBC.gb
  - fixtures/age/spsw-tima-cgbE.gb
  - fixtures/age/stat-mode-cgbE.gb
  - fixtures/age/stat-mode-ds-cgbBCE.gb
  - fixtures/age/stat-mode-sprites-dmgC-cgbBCE.gb
  - fixtures/age/stat-mode-sprites-ds-cgbBCE.gb
  - fixtures/age/stat-mode-window-cgbBCE.gb
  - fixtures/age/stat-mode-window-ds-cgbBCE.gb
  - fixtures/cgb-speed/LICENSE.txt
  - fixtures/cgb-speed/common.inc
  - fixtures/cgb-speed/manifest.json
  - fixtures/cgb-speed/speed-hostile.asm
  - fixtures/cgb-speed/speed-hostile.gb
  - fixtures/cgb-speed/speed.asm
  - fixtures/cgb-speed/speed.gb
  - include/gabbaboy/gabbaboy.h
  - src/core/gabbaboy.c
  - src/core/gabbaboy_test.h
  - src/player/limitations.h
  - src/player/main.c
  - tests/CMakeLists.txt
  - tests/check_no_phase12_rows.cmake
  - tests/check_no_stale_speed_claims.cmake
  - tests/consumers/c/main.c
  - tests/consumers/cpp/main.cpp
  - tests/data/cgb-speed-expectations.txt
  - tests/expected-tests.txt
  - tests/external/cgb-speed-dispositions.json
  - tests/fuzz/fuzz_core.dict
  - tests/fuzz_core.c
  - tests/player/CMakeLists.txt
  - tests/player/cgb_smoke.cmake
  - tests/player/expected-tests.txt
  - tests/player/test_limitations.c
  - tests/scripts/derive-cgb-speed-expectations.py
  - tests/scripts/reproduce-age.sh
  - tests/scripts/reproduce-cgb-speed.sh
  - tests/scripts/run-bounded-fuzz.sh
  - tests/scripts/test-reproduce-age.sh
  - tests/scripts/test-reproduce-cgb-speed.sh
  - tests/scripts/verify-cgb-speed-dispositions.py
  - tests/scripts/verify-speed-domains.py
  - tests/test_age.c
  - tests/test_cgb_partition.c
  - tests/test_cgb_speed_fixture.c
  - tests/test_cgb_speed_internal.c
  - tests/test_cgb_tables.c
  - tests/test_cgb_visibility.c
  - tests/test_fuzz_core.c
findings:
  critical: 1
  warning: 1
  info: 0
  total: 2
status: issues_found
---

# Phase GB-12: Code Review Report

**Reviewed:** 2026-10-14T03:33:17Z  
**Depth:** standard  
**Files Reviewed:** 75  
**Status:** issues_found

## Summary

The Phase GB-12 source scope was reviewed, including the CGB speed-switch paths, fixture and test helpers, workflow changes, documentation, and binary fixture hashes against their manifests. Two issues remain: an environment-to-shell injection in a CI self-test cleanup trap, and sanitizer CTest timeout limits registered after the scaling pass.

## Narrative Findings (AI reviewer)

### CR-01: [BLOCKER] TMPDIR can inject commands through the cleanup trap

**File:** `.github/scripts/verify-test-inventory.sh:31`  
**Issue:** `selftest_dir` comes from `mktemp`, which honors the inherited `TMPDIR`. The double-quoted `trap` expands that path into shell source inside single quotes before registering the EXIT handler. If the path contains a quote and shell metacharacters, the handler executes the injected commands when the CI self-test exits. The workflow invokes this self-test at `.github/workflows/ci.yml:25`.
**Fix:** Keep the directory path in script scope (rather than the function-local variable) and register a literal trap body so the path is expanded as a quoted argument only when the trap runs:

```bash
selftest_dir=$(mktemp -d)
trap 'rm -rf -- "$selftest_dir"' EXIT
```

### WR-01: [WARNING] Late Phase 12 CTest timeouts bypass sanitizer scaling

**File:** `tests/CMakeLists.txt:2589-2598,3163,3493`  
**Issue:** The sanitizer scaler snapshots the directory's current `TESTS` property before the Phase 12 registrations begin, so the explicit limits added later are not tripled. For example, `age_sensitivity_*` remains at 240 seconds and the CGB partition tests remain at 60 seconds under ASan/UBSan. This contradicts the nearby policy comment that every explicit timeout is scaled and can make slow sanitizer runs fail as timeouts instead of exposing test results.
**Fix:** Apply timeout scaling after all test registrations, or use a shared timeout-setting helper for every registration. Keep normal-build timeout values as the source of truth and remove the per-test AGE scaling when centralizing, so those limits are multiplied exactly once.

---

_Reviewed: 2026-10-14T03:33:17Z_  
_Reviewer: the agent (gsd-code-reviewer)_  
_Depth: standard_
