---
phase: GB-20-fixture-admission-tune-up
reviewed: 2026-11-01T11:57:00Z
depth: standard
files_reviewed: 5
files_reviewed_list:
  - .github/scripts/safe_extract_package.py
  - .github/scripts/verify-workflow-policy.py
  - tests/cmake/ci-lanes.cmake
  - tests/data/workflow-policy-controls.json
  - tests/scripts/verify-workflow-policy-coverage.py
findings:
  critical: 1
  warning: 0
  info: 0
  total: 1
status: issues_found
---

# Phase GB-20: Post-Rescope Code Review Report

**Reviewed:** 2026-11-01T11:57:00Z  
**Depth:** standard  
**Files Reviewed:** 5  
**Status:** issues_found

## Narrative Findings (AI reviewer)

## Summary

The prior oversized tar metadata issue is closed by the bounded decompression stream and pre-payload extension-header checks. The missing-checker path now checks the trusted checker before creating the extraction tree, so that retry failure is also closed. One archive path validation defect remains: on Windows, a drive-qualified directory member can create directories outside the extraction destination.

## Critical Issues

### CR-01 [BLOCKER]: Drive-qualified archive paths escape the extraction root on Windows

**File:** `.github/scripts/verify-workflow-policy.py:74-82, 152-155`
**Issue:** `_archive_member_path` validates names using `PurePosixPath`, which accepts a relative-looking member such as `D:/outside/`. On Windows, `destination.joinpath(*relative.split("/"))` treats `D:` as a drive component. The directory-entry branch then calls `target.mkdir(parents=True, exist_ok=True)` without a containment check, creating attacker-chosen directories on that drive outside `destination`. For regular-file entries, `target.parent.mkdir(...)` also runs before the later containment check, so rejected files can leave directories outside the extraction tree. A downloaded archive therefore still controls filesystem writes outside the private extraction root when this checker runs on Windows.
**Fix:** Reject Windows drive and alternate-stream syntax in every path component before joining (for example, reject `:` in any component), and verify that each computed target is contained under `destination` before any `mkdir` or file creation. Apply the same pre-creation containment check to directory and regular-file entries.

---

_Reviewed: 2026-11-01T11:57:00Z_  
_Reviewer: the agent (gsd-code-reviewer)_  
_Depth: standard_
