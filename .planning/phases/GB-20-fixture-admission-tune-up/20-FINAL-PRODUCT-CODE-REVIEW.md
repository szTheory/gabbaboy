---
phase: GB-20-fixture-admission-tune-up
reviewed: 2026-11-01T12:56:34Z
depth: standard
files_reviewed: 5
files_reviewed_list:
  - tests/scripts/verify-fixture-admission.py
  - tests/scripts/verify-v02-source-archive.py
  - tests/scripts/verify-workflow-policy-coverage.py
  - tests/data/workflow-policy-controls.json
  - .github/scripts/verify-workflow-policy.py
findings:
  critical: 1
  warning: 0
  info: 0
  total: 1
status: issues_found
---

# Phase 20: Final Product Code Review

**Reviewed:** 2026-11-01T12:56:34Z  
**Depth:** standard  
**Files Reviewed:** 5  
**Status:** issues_found

## Summary

The core/player product controls reject forbidden fixture bytes at generated required and `one_of` paths, and the reviewed source digest/AST controls pass. The source/core TAR parser enforces per-header, aggregate-byte, and decompressed-stream limits before metadata payload parsing, but its extension-header count is reset for every ordinary member, allowing archives to exceed the configured count limit.

## Critical Issues

### CR-01: [BLOCKER] Per-member reset bypasses the extension-header count limit

**File:** `tests/scripts/verify-v02-source-archive.py:132-135`
**Issue:** Resetting `stats["headers"]` on every non-extension member makes the 128-header limit apply only to consecutive metadata headers. A PAX header before each ordinary member evades the configured count limit. I reproduced this with the limit lowered to 1: three ordinary members, each with one PAX header, were accepted by `inspect_tar()`. This leaves the source/core archive path without the archive-wide metadata-header bound its other stream and aggregate-byte caps are intended to complement.
**Fix:** Keep a cumulative extension-header counter for the entire archive and reject once it exceeds `extension_headers`. If a separate chained-header limit is needed, track it independently. Add a negative control with extension headers interleaved with ordinary members.

---

_Reviewed: 2026-11-01T12:56:34Z_  
_Reviewer: the agent (gsd-code-reviewer)_  
_Depth: standard_
