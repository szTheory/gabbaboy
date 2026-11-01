---
phase: GB-20-fixture-admission-tune-up
reviewed: 2026-11-01T11:24:04Z
depth: standard
files_reviewed: 12
files_reviewed_list:
  - .github/scripts/release-evidence-lifecycle.sh
  - .github/scripts/verify-workflow-policy.py
  - .github/workflows/release.yml
  - CMakeLists.txt
  - cmake/FixtureAdmissionPolicy.json
  - docs/fixture-admission.md
  - tests/ci/test-budget-allowlist
  - tests/data/workflow-policy-controls.json
  - tests/scripts/verify-dense-input.py
  - tests/scripts/verify-fixture-admission.py
  - tests/scripts/verify-v02-adoption.py
  - tests/scripts/verify-workflow-policy-coverage.py
findings:
  critical: 1
  warning: 1
  info: 0
  total: 2
status: issues_found
---

# Phase 20: Code Review Report

**Reviewed:** 2026-11-01T11:24:04Z  
**Depth:** standard  
**Files Reviewed:** 12  
**Status:** issues_found

## Narrative Findings (AI reviewer)

## Summary

Reviewed the 12 changed source files covering fixture admission, product policy, and release archive validation. The trusted publisher archive reader still permits decompressed PAX metadata to bypass its stated size limits and exhaust the runner. A secondary failure path leaves extracted data behind when the trusted checker is unavailable. This was a static review; tests were not run.

## Critical Issues

### CR-01 [BLOCKER]: Tar metadata bypasses the decompressed archive limits

**File:** `.github/scripts/verify-workflow-policy.py:79-83`
**Issue:** `tarfile.open(..., mode="r:gz")` parses PAX/GNU extension headers while iterating members, before this code checks regular-file sizes or the accumulated expanded size. The compressed-file cap does not bound decompressed extension-header data, and the expanded-size counter only includes regular members. A highly compressed archive with a huge extension header can make the privileged release publisher allocate excessive memory or spend excessive CPU before any policy rejection.
**Fix:** Parse through a bounded decompression stream that caps total uncompressed tar bytes, and reject PAX/GNU extension headers above per-header, aggregate-byte, and count limits before `tarfile` reads their payloads. The existing bounded approach in `.github/scripts/safe_extract_package.py` can be reused.

## Warnings

### WR-01 [WARNING]: Missing trusted checker leaves a stale extraction tree

**File:** `.github/scripts/verify-workflow-policy.py:130-133`
**Issue:** The archive is fully extracted before the checker path is validated. If the trusted checker is absent, this branch raises before entering the `try/finally` cleanup, leaving the extracted tree behind. A retry with the same destination then fails at the pre-existing-destination check even after the checker is restored.
**Fix:** Validate that the trusted checker exists before extraction, or place extraction and checker validation under one cleanup `try/finally` so every failure removes the destination.

---

_Reviewed: 2026-11-01T11:24:04Z_  
_Reviewer: the agent (gsd-code-reviewer)_  
_Depth: standard_
