---
phase: GB-01-portable-foundation-and-original-rom-tracer
reviewed: 2026-10-09T12:07:32Z
depth: standard
files_reviewed: 6
files_reviewed_list:
  - src/runner/main.c
  - tests/CMakeLists.txt
  - tests/expected-tests.txt
  - tests/test_api.c
  - tests/test_instance_concurrency.c
  - tests/verify_runner_help.cmake
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
status: clean
---

# Phase 1: Code Review Report

**Reviewed:** 2026-10-09T12:07:32Z
**Depth:** standard
**Files Reviewed:** 6 (recheck of the incremental Phase 1 runner and test changes)
**Status:** clean

## Summary

This recheck covers the six listed source and test files and does not replace the earlier full Phase 1 review. The two newest findings are resolved: the Windows partial thread-creation path releases and joins the worker before destroying its instances, and `runner_help` checks the ROM, manifest-case, and manifest-suite invocation forms. The reset test asserts each post-reset run's outcome, budget, trace bound, and RAM write; the concurrency test exercises distinct ROM immediates and expected RAM values; and the CTest watchdog includes the concurrent test with a 30-second timeout. No current findings remain. This was a source review; no tests were run as part of this recheck. Earlier review records are preserved below.

## Narrative Findings (AI reviewer)

No current findings.

## Recheck Outcome

- **Latest WR-01 — Resolved.** `tests/test_instance_concurrency.c:91-98` releases the start gate, waits for `threads[0]`, closes its handle, and only then destroys either instance when creation of the second Windows thread fails. The first-thread creation failure has no worker to join.
- **Latest WR-02 — Resolved.** `tests/verify_runner_help.cmake:14-24` checks `Usage:`, the ROM invocation, the manifest `--case` invocation, and the manifest `--suite` invocation. `tests/CMakeLists.txt:248-251` registers this check as `runner_help`, and `tests/expected-tests.txt:170` includes it in the expected inventory.
- **Earlier WR-01 — Resolved.** `tests/test_api.c:49-63` asserts stop reason and consumed budget and checks RAM immediately after each run, including the run after two consecutive resets. It bounds both trace counts to the arrays' 32-record capacity before comparing trace bytes.
- **Earlier WR-02 — Resolved.** `tests/test_instance_concurrency.c:64-81` gives the two workers distinct ROM programs by changing the second program's write and compare immediates, and assigns distinct expected RAM values. Each worker checks its own run result and RAM value on every iteration (`:29-38`); the main thread checks both outcomes after joining (`:114-127`).
- **Earlier WR-03 — Resolved.** `tests/CMakeLists.txt:299-307` applies CTest's 30-second `TIMEOUT` to `concurrent_independent_instances`, bounding the test process if either readiness/start spin wait or worker execution stalls.

### Resolved findings from the 2026-10-09 rechecks (preserved)

#### WR-01: Partial Windows thread creation can free an instance still in use

**Classification:** WARNING — resolved in the current recheck.
**File:** `tests/test_instance_concurrency.c:87-98`
**Issue:** If creation of the second Windows worker failed, the failure path released the start gate and closed the first worker's handle without waiting for it to finish, then destroyed both instances while the worker could still be using one.
**Fix:** Join each successfully created worker before destroying its instance. The current second-thread failure path waits for the first worker and closes its handle before destruction.

#### WR-02: Help-output test accepts missing invocation forms

**Classification:** WARNING — resolved in the current recheck.
**File:** `tests/CMakeLists.txt:248-251`
**Issue:** The earlier `runner_help` check only searched for the word `Usage:`, so it passed if invocation examples were removed.
**Fix:** Check every documented invocation form. The current CMake script asserts the ROM, manifest-case, and manifest-suite forms and remains registered in the expected test inventory.

The earlier review records below are retained for traceability; their findings are resolved.

## Historical Supplemental Findings (initial review; preserved)

### WR-01: Double-reset run side effects are not asserted

**Classification:** WARNING
**File:** tests/test_api.c:49-57
**Issue:** The run after two consecutive resets is compared with the later single-reset run, but its expected stop/budget result and RAM write are never checked directly. The RAM assertion occurs only after the second run at line 57, so a regression that affects only the first run after a double reset while preserving its trace can be erased by the next reset and pass this test.
**Fix:** Immediately after the first run, assert its expected reason and consumed half-dots and check gbb_peek_ram(a, 0xC000) == 0x5A before resetting again. Also assert trace_count does not exceed the 32-record array before using it as the memcmp length.

### WR-02: Identical workloads can mask cross-instance interference

**Classification:** WARNING
**File:** tests/test_instance_concurrency.c:59-63
**Issue:** Both instances load the same ROM and each worker performs the same reset/run sequence, expecting the same RAM value. Shared mutable CPU or emulator state can therefore produce matching results and evade this concurrency test, even though the API contract promises independent instances with no shared mutable state.
**Fix:** Give each worker a distinct observable workload (for example, separate small fixtures that write different values or produce different traces), then assert each instance retains its own expected result throughout concurrent execution.

### WR-03: Concurrent-instance test has no host watchdog

**Classification:** WARNING
**File:** tests/CMakeLists.txt:20-21
**Issue:** The new test contains unbounded spin waits for worker readiness and start in tests/test_instance_concurrency.c:26,81. The CTest TIMEOUT list at lines 295-302 omits concurrent_independent_instances, so a worker or core regression that stops making progress can leave CI waiting indefinitely.
**Fix:** Add concurrent_independent_instances to the existing CTest TIMEOUT property (or make the test's synchronization waits bounded and fail with a diagnostic).

---

## Prior Review Record (preserved)

The earlier standard-depth review remains recorded as clean at 2026-10-03T17:28:47Z: 35 files reviewed, with zero critical, warning, or info findings. Its scope included AGENTS.md plus 34 changed non-planning paths. This earlier review predates the four-file incremental scope above.

Original full-review summary: “Re-reviewed the Phase 1 source scope, including the atomic evidence-staging change and the archive, cartridge, and RGBDS fixes. The temporary evidence directory is created atomically with `mktemp -d` under the restrictive umask. The ROM-only loader rejects unsupported size codes; the package extractor rejects links and unsafe paths, bounds compressed and expanded data, member and extension counts, extension sizes, and path depth, and verifies streamed member lengths. The fixture workflow verifies the RGBDS archive SHA-256 before extracting or running it. No actionable findings remain. All reviewed files meet quality standards. No issues found.”

Original full-review metadata: reviewed 2026-10-03T17:28:47Z; standard depth; 35 files; critical 0, warning 0, info 0, total 0; clean.

Earlier review scope:

- AGENTS.md
- .github/scripts/safe_extract_package.py
- .github/scripts/verify-cmake-floor.sh
- .github/scripts/verify-pr-evidence.sh
- .github/scripts/verify-test-inventory.sh
- .github/workflows/ci.yml
- .github/workflows/fixture-repro.yml
- .github/workflows/preview.yml
- .gitignore
- CMakeLists.txt
- CMakePresets.json
- README.md
- cmake/ExpectedTests.cmake
- cmake/GabbaBoyConfig.cmake.in
- cmake/PreviewPackageSmoke.cmake
- cmake/RunInstalledConsumer.cmake
- cmake/VerifyArtifactSidecar.cmake
- cmake/VerifyFixture.cmake
- cmake/VerifyInstalledPackage.cmake
- fixtures/tracer/LICENSE.txt
- fixtures/tracer/manifest.json
- fixtures/tracer/tracer.asm
- fixtures/tracer/tracer.gb
- include/gabbaboy/gabbaboy.h
- src/core/gabbaboy.c
- src/runner/main.c
- tests/CMakeLists.txt
- tests/consumers/c/CMakeLists.txt
- tests/consumers/c/main.c
- tests/consumers/cpp/CMakeLists.txt
- tests/consumers/cpp/main.cpp
- tests/expected-tests.txt
- tests/test_api.c
- tests/test_loader.c
- tests/test_tracer.c

---

_Initial supplemental review: 2026-10-09T11:58:12Z_
_Reviewer: the agent (gsd-code-reviewer)_  
_Depth: standard_
