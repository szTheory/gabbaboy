---
phase: GB-02-dmg-cpu-bus-and-time
reviewed: 2026-10-07T03:23:32Z
depth: standard
files_reviewed: 47
files_reviewed_list:
  - .gitattributes
  - .github/scripts/verify-test-inventory.sh
  - .github/workflows/ci.yml
  - .github/workflows/fixture-repro.yml
  - .gitignore
  - CMakeLists.txt
  - README.md
  - cmake/ExpectedTests.cmake
  - cmake/VerifyMooneye.cmake
  - fixtures/mooneye/ELIGIBILITY.md
  - fixtures/mooneye/FONT-LICENSE.txt
  - fixtures/mooneye/LICENSE.txt
  - fixtures/mooneye/SOURCES.md
  - fixtures/mooneye/candidate-digests.json
  - fixtures/mooneye/font-source.c
  - fixtures/mooneye/headless-report.patch
  - fixtures/mooneye/manifest.json
  - fixtures/mooneye/pre-admission-baseline.json
  - fixtures/tracer/manifest.json
  - fixtures/tracer/tracer.asm
  - include/gabbaboy/gabbaboy.h
  - src/core/gabbaboy.c
  - src/runner/main.c
  - tests/CMakeLists.txt
  - tests/consumers/c/main.c
  - tests/consumers/cpp/main.cpp
  - tests/expect_runner_failure.cmake
  - tests/expected-tests.txt
  - tests/scripts/inspect-windows-manifest.sh
  - tests/scripts/probe-mooneye-candidate.sh
  - tests/scripts/reproduce-mooneye.sh
  - tests/scripts/verify-mooneye-hosted-candidate.sh
  - tests/scripts/verify-mooneye-unadmitted.sh
  - tests/scripts/verify-phase2-hosted.sh
  - tests/scripts/verify-phase2-installed.sh
  - tests/test_api.c
  - tests/test_bus.c
  - tests/test_control.c
  - tests/test_cpu.c
  - tests/test_diagnostics.c
  - tests/test_events.c
  - tests/test_loader.c
  - tests/test_runner.c
  - tests/test_serial.c
  - tests/test_timer.c
  - tests/test_tracer.c
findings:
  critical: 1
  warning: 1
  info: 0
  total: 2
status: issues_found
---

# Phase GB-02: Code Review Report

**Reviewed:** 2026-10-07T03:23:32Z
**Depth:** standard
**Files Reviewed:** 47
**Status:** issues_found

## Summary

Reviewed all 47 nonbinary source, configuration, script, and documentation files in the resolved Phase 02 scope, including both `.changedFiles` and `.outsideUnion`. The current CPU and timer paths and their regression coverage were read in context. Fixture byte provenance was treated as supported by the phase verification evidence. Two confirmed defects remain in the candidate qualification and promotion gates: promotion does not verify its candidate lock against the exact hosted artifact, and the protocol probe can accept a callback observed after the result breakpoint.

## Narrative Findings (AI reviewer)

### CR-01: BLOCKER — Promotion trusts mutable candidate digests as hosted evidence

**File:** `tests/scripts/verify-mooneye-unadmitted.sh:162-173`

**Issue:** The promotion path checks that qualification flags and hosted-comparison booleans say “qualified,” then attempts to validate the lock with `sha(lock_path.read_bytes()) == ''`. Since `sha` returns a nonempty SHA-256 hex digest for every input, this check never validates anything. Later, lines 186-208 compare the local ROM bytes only with the digest values from that same mutable lock. The script never proves that those values still match the committed lock digest or the exact retained hosted artifact. A changed candidate digest and matching local output can therefore be staged for admission while stale `hosted_comparison.byte_identical` fields continue to pass the gate.

**Fix:** Before staging, bind the candidate list and every ROM’s size and digest to the exact retained hosted artifact for the recorded head/run (reusing the checks in `verify-mooneye-hosted-candidate.sh` is suitable). Reject any mismatch; do not treat nonempty SHA output or mutable status fields as hosted-byte evidence.

### WR-01: WARNING — Protocol probe accepts callback records after the result breakpoint

**File:** `tests/scripts/probe-mooneye-candidate.sh:47-60, 74-77`

**Issue:** The trace loop records `saw_breakpoint` when it encounters the result instruction but continues scanning the remainder of that same `gbb_run_ex` batch. If a later record in the batch has the callback PC, `saw_callback` becomes true and the final return condition succeeds. That allows a candidate whose result precedes its protocol callback to pass this probe. The production runner checks protocol ordering, and current derived fixtures have separate verification evidence, but this probe is intended to qualify the ordering property for candidates.

**Fix:** Process each returned trace in order and stop at the first result breakpoint. Require that the expected callback was already observed at that point; reject a breakpoint reached first.

---

_Reviewed: 2026-10-07T03:23:32Z_
_Reviewer: the agent (gsd-code-reviewer)_
_Depth: standard_
