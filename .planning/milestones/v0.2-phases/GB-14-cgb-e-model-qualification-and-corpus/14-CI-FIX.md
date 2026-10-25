---
phase: 14
finding: CR-03
fixed_at: 2026-10-16T02:42:50Z
commit: 2bd8c1c13a8ac3e4ed303b82993824f68d95fb3f
status: fixed
---

# Phase 14 CI Fix: Configured Build Directory

CTest now supplies the configured binary directory to the APU and corpus-report adapters. The APU validator accepts explicit `--build-dir` and `--ctest-command` arguments; corpus-report tests pass the configured path to tracer self-tests and use it for temporary controls. Direct CLI defaults remain `ROOT/build`. The tracer test also checks that the receipt identifies the executable from the configured directory.

The fix was committed atomically as `2bd8c1c13a8ac3e4ed303b82993824f68d95fb3f` by GabbaBoy Automation.

**RED:** Before editing, a real `cmake-3.25.3` preset build in the isolated worktree reproduced all five reported failures: APU membership and controls queried the missing default build directory; the report tracer could not find its runner there; tracer controls and report controls attempted to create temporary directories under it. The isolated worktree had no `ROOT/build` directory.

**GREEN:** After the fix and again after the commit, the same nondefault-build CTest selection passed 5/5. The complete corpus-report unittest suite passed 13/13 with `GBB_TEST_BUILD_DIR` set to that nondefault directory, and the APU self-test passed as part of the five-test selection. Python syntax and `git diff --check` passed. Verification ran in the isolated worktree, not the main checkout.

The local host used CMake 4.4.3 and Python 3.14.4 on macOS. The exact CMake 3.25.3 hosted job remains the platform integration check for the parent to rerun after publishing the fix.
