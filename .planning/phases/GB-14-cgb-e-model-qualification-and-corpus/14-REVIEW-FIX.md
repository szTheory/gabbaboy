---
phase: 14
fixed_at: 2026-10-16T01:58:59Z
review_path: .planning/phases/GB-14-cgb-e-model-qualification-and-corpus/14-REVIEW.md
iteration: 1
findings_in_scope: 2
fixed: 2
skipped: 0
status: all_fixed
---

# Phase 14: Code Review Fix Report

**Fixed at:** 2026-10-16T01:58:59Z  
**Source review:** `.planning/phases/GB-14-cgb-e-model-qualification-and-corpus/14-REVIEW.md`  
**Iteration:** 1

**Summary:**
- Findings in scope: 2
- Fixed: 2
- Skipped: 0

## Fixed Issues

### CR-01: Build stamp looks up extensionless executable names on Windows

**Files modified:** `tests/scripts/verify-cgb-corpus-report.py`, `tests/scripts/test-cgb-corpus-report.py`  
**Commit:** `e1deb42`  
**Applied fix:** Added a shared executable-path helper using Python's native `EXE` suffix and applied it to tracer build identity, full build identity, and tracer execution. Added POSIX and simulated Windows positive, missing-path, and wrong-path controls.

### CR-02: Bounded subprocess reader cannot register Windows pipes

**Files modified:** `tests/scripts/verify-cgb-corpus-report.py`, `tests/scripts/test-cgb-corpus-report.py`  
**Commit:** `bfd6f09`  
**Applied fix:** Added a Windows reader thread with a bounded event queue, strict byte cap, deadline, merged output, bounded process-tree cleanup, and reader cancellation fallback. Retained POSIX selector reads and process-group termination, with strict cap checks before retaining a chunk. Added simulated Windows tests for pipe output, nonzero exit, overflow, timeout, and read failure.

## Verification

- Python AST parsing passed for both modified scripts.
- Focused executable-suffix and bounded-subprocess controls passed: 8 tests in the isolated worktree.
- After fast-forwarding, `cmake --preset phase1` and `cmake --build --preset phase1 --target cgb_corpus_build_stamp --parallel 4` passed in the main checkout. The build stamp reported input identity `fb52cac037fe5081d554b9c874a8ceed063c1a4315bec4bbed73c219dc919d18`.
- The existing report-contract suite passed in the main checkout: 13 tests.
- Windows suffix and pipe behavior was simulated on macOS; no actual Windows execution is claimed. Native Windows integration remains for the hosted exact-head job.

## Skipped Issues

None.

---

_Fixed: 2026-10-16T01:58:59Z_  
_Fixer: the agent (gsd-code-fixer)_  
_Iteration: 1_
