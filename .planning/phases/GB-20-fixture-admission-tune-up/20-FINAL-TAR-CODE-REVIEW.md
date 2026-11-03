---
phase: GB-20-fixture-admission-tune-up
reviewed: 2026-11-01T14:12:14Z
depth: standard
files_reviewed: 1
files_reviewed_list:
  - tests/scripts/verify-v02-source-archive.py
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
status: clean
---

# Phase GB-20: Final TAR Code Review Report

**Reviewed:** 2026-11-01T14:12:14Z (follow-up closure)  
**Depth:** standard  
**Files Reviewed:** 1  
**Status:** clean after the follow-up closure below

## Summary

The parser keeps the archive-wide extension count separate from the consecutive-chain cap, checks it before invoking the base extension parser, and constructs fresh counters for each `inspect_tar` call. Source receipt creation/rechecking and core product inspection route through this parser. The changed self-test does not, however, prove that the archive-wide counter resets between inspections.

## Narrative Findings (AI reviewer)

### WR-01: [WARNING, closed] Repeated long-path positive did not test archive-wide counter lifetime

**File:** `tests/scripts/verify-v02-source-archive.py:1061-1067`
**Issue:** The test inspects the 256-long-path archive twice with the default total cap of 32,768. Each pass uses only about 257 extension headers, so a regression that stores `total_headers` across inspections would still accept both passes. The assertion that each pass processes more than 128 headers only exercises the chain-cap compatibility case; it does not establish that the cumulative total is private to one inspection, despite the message at line 1066.
**Fix:** Run both inspections with `MAX_TAR_TOTAL_EXTENSION_HEADERS` scoped to the archive's exact extension-header count (assert that count first), keeping the limit active across both calls. Each independent parse should pass; a counter shared across inspections would reject the second. A smaller two-header fixture with the cap scoped to two would also cover this property.

---

_Reviewed: 2026-11-01T13:12:54Z_  
_Reviewer: the agent (gsd-code-reviewer)_  
_Depth: standard_

## Follow-up Closure

**Resolved at:** `7293eb47a6c799b6455dd854533aca932f4529ad`  
**Result:** PASS — no open findings.

The self-test now counts the 256-long-path archive's extension headers, asserts the count, and scopes `MAX_TAR_TOTAL_EXTENSION_HEADERS` to that exact count for both `inspect_tar` calls. Each parse succeeds independently; a counter accidentally shared across inspections would exceed the cap on the second parse. The `v02_source_archive_controls` CTest and final release-candidate replay pass at this source head. The follow-up TAR review confirmed WR-01 closed.
