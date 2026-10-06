---
phase: GB-02-dmg-cpu-bus-and-time
plan: 08
subsystem: diagnostics-and-runner
tags: [diagnostics, mooneye, bounded-runner, qualification]
requires:
  - phase: GB-02-dmg-cpu-bus-and-time/02-07
    provides: pinned eligible offline CPU/timer fixtures and provenance
provides:
  - Caller-owned bounded core diagnostics with complete-operation reservation
  - Manifest-pinned case and strict suite execution with sanitized receipts
  - Per-case and negative-control runner tests
affects: [GB-02-dmg-cpu-bus-and-time/02-09, phase-verification]
tech-stack:
  added: []
  patterns: [caller-owned linear diagnostics, fixed manifest digest admission, host-owned LD-B-B protocol detection, source-derived finite execution bounds]
key-files:
  created: [tests/test_diagnostics.c, tests/test_runner.c, tests/expect_runner_failure.cmake]
  modified: [include/gabbaboy/gabbaboy.h, src/core/gabbaboy.c, src/runner/main.c, CMakeLists.txt, tests/CMakeLists.txt, tests/expected-tests.txt, fixtures/mooneye/manifest.json, fixtures/mooneye/SOURCES.md]
key-decisions:
  - "LD B,B stays an ordinary CPU instruction; the runner recognizes Mooneye register results at instruction boundaries."
  - "The source-qualified denominator stays one CPU plus two timer cases; every case must execute and pass for the required suite to pass."
  - "DAA's budget is 2000000 half-dots because its pinned source runs 4096 cases with a 1343488-half-dot timing floor before setup and completion."
  - "Receipts pin the Mooneye source and exact core/runner revision, omit local paths, and retain at most 128 recent diagnostic records."
metrics:
  duration: 8 min
  completed: 2026-10-06
  tasks: 2
  files: 10
  commits: 3
  plan_head_before: 96e29af6cad1f91b75bb7aec86f496f110766f5d
  plan_head_after: 4d3115e8944262686e4944575295691ab9df2180
actuals:
  tasks: 2
  commits: 3
requirements-completed: []
coverage:
  - id: D-05
    description: "Mooneye LD B,B remains ordinary CPU execution and only the host runner reads its register-result protocol."
    verification:
      - kind: unit
        ref: "runner_pass and runner_fail controlled instruction-boundary protocol records"
        status: pass
      - kind: integration
        ref: "mooneye_required_suite and three per-case tests"
        status: pass
    human_judgment: false
  - id: D-11
    description: "Runner classifies pass, fail, timeout, and unsupported separately, with bounded sanitized receipts and exact denominators."
    verification:
      - kind: unit
        ref: "runner_pass, runner_fail, runner_timeout, runner_unsupported"
        status: pass
      - kind: integration
        ref: "two byte-identical required-suite receipts; eligible=3 executed=3 status=pass"
        status: pass
    human_judgment: false
  - id: D-10
    description: "Missing or changed fixture bytes and malformed or tampered manifest metadata fail closed."
    verification:
      - kind: integration
        ref: "runner_missing_fixture, runner_bad_digest, runner_bad_manifest, runner_bad_metadata, runner_zero_eligible"
        status: pass
    human_judgment: false
status: complete
---

# Phase 2 Plan 08: Manifest-Driven Mooneye Qualification Summary

**The headless runner now qualifies every pinned CPU/timer fixture through the host-owned register protocol and emits deterministic, bounded receipts backed by caller-owned core diagnostics.**

## Accomplishments

- Added `gbb_diagnostic_record`, `gbb_run_ex`, and `diagnostic_count`. Diagnostics record instruction boundaries, timed bus accesses, and timer changes into caller storage. The core reserves 16 slots before each CPU operation and returns output-full before that operation mutates state when capacity is short. `gbb_run` remains the no-diagnostics wrapper.
- Added the five `diagnostics_zero`, `diagnostics_exact`, `diagnostics_short`, `diagnostics_null`, and `diagnostics_canary` tests. They verify optional output, exact reserved capacity, rejection without operation mutation, invalid pointer/capacity pairing, and intact canaries.
- Added bounded manifest, ROM-size, and SHA-256 validation; `--manifest`, `--case`, `--suite`, and `--receipt`; aliases including `--case daa`; fixed CPU/timer IDs and denominators; and host-side `LD B,B` register-result classification. Pass, fail, timeout, and unsupported are distinct runner outcomes. A required suite fails if any eligible case is missing, skipped, unsupported, timed out, or failed.
- Receipts include the pinned Mooneye source revision, matching core and runner build revisions, build qualification, fixture digest, model and boot profile, protocol, ticks and budget, exact eligible/executed counts, and no local paths. The runner keeps a fixed 128-record recent history and prints at most eight records per case.
- Restored the existing positional tracer invocation after the first full-suite run exposed that installed-package and tracer smoke tests depended on it.
- Added per-case CTest registration and subprocess negative controls for missing fixtures, ROM digest mismatch, malformed manifests, and altered model/boot metadata.

## Task Commits and TDD Evidence

1. **Run one admitted ROM and emit a bounded receipt:** `060dace` — caller-owned diagnostics, runner case selection, build revision metadata, and diagnostics tests.
2. **Fail closed on negative controls and execute all eligible cases:** `a3b4983` (RED) and `4d3115e` (GREEN).

The RED run of `mooneye_required_suite` executed all three eligible cases and failed because DAA exhausted the inherited 200,000-half-dot preparation budget. Both timer cases already reached the documented pass registers. The pinned `acceptance/instr/daa.s` source sets BC to `$80*16` and runs that 2,048-case loop twice. Its loop executes at least 25 instructions per case, with a timing floor of 328 half-dots per case: 1,343,488 half-dots before setup and the completion protocol. Raising only the finite DAA budget to 2,000,000 allowed the unchanged guest to reach the protocol and pass at 1,805,920 half-dots. This is a budget correction based on the pinned workload, not a core behavior change or fixture exclusion.

## Verification Evidence and Limits

- `cmake --preset phase1` and `cmake --build --preset phase1` passed after the implementation commit. CMake embedded exact revision `4d3115e8944262686e4944575295691ab9df2180` for both core and runner and marked the build qualified.
- Full offline CTest passed **90/90**, including the five diagnostics tests, runner protocol and negative-control tests, all three per-case Mooneye tests, the strict required suite, tracer compatibility, preview package smoke, and installed C/C++ consumers.
- The strict required suite reported `eligible=3 executed=3 status=pass`. DAA passed at 1,805,920/2,000,000 half-dots; `tim00` passed at 36,984/200,000; `tim00_div_trigger` passed at 34,904/200,000.
- Two post-commit suite receipts were byte-identical. The receipt reports the exact Mooneye source revision and matching, qualified core/runner revision; its output contains no local filesystem paths.
- `gsd_run check evaluation-scope --plan 02-08 --commits-only --raw` found all three plan commits and no missing or out-of-scope files. The measured task-commit range is base `96e29af6cad1f91b75bb7aec86f496f110766f5d` through `4d3115e8944262686e4944575295691ab9df2180`.
- No hardware run was performed. The fixtures' pinned source declares DMG hardware results; local results are emulator qualification evidence, not a new hardware claim. CPU requirements remain pending the Phase 2 verifier as directed.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking issue] Raised the DAA runner budget to cover its pinned source workload.**
- **Found during:** Task 2
- **Issue:** The 200,000-half-dot preparation budget was below the source-derived minimum of 1,343,488 half-dots for 4,096 DAA cases, before setup and completion protocol.
- **Fix:** Set the finite manifest and runner budget to 2,000,000 half-dots; kept fixture bytes, source logic, selected IDs, eligibility, and strict pass requirement unchanged.
- **Files modified:** `fixtures/mooneye/manifest.json`, `fixtures/mooneye/SOURCES.md`, `src/runner/main.c`
- **Verification:** The required suite and `mooneye_case_daa` passed at 1,805,920 half-dots; manifest digest and full CTest inventory passed.
- **Commit:** `4d3115e`.

**2. [Rule 1 - Bug] Preserved the positional original-tracer runner interface.**
- **Found during:** Overall verification
- **Issue:** The first full CTest run showed that `tracer_smoke` and preview-package verification still invoke `gabbaboy-runner <tracer.gb>`.
- **Fix:** Kept the new manifest CLI and restored the bounded positional tracer path used by existing consumers.
- **Files modified:** `src/runner/main.c`
- **Verification:** `tracer_smoke`, `preview_package_smoke`, installed runner smoke, and full CTest passed.
- **Commit:** `4d3115e`.

## TDD Gate Compliance

Task 2 carried `tdd="true"`. The strict suite test was committed first as RED (`a3b4983`) and failed on its planned all-eligible-pass assertion because the source workload exceeded the old DAA limit. After the source-based bound correction and negative-control implementation, GREEN commit `4d3115e` passed the required suite and all 90 CTest cases. Project `workflow.tdd_mode` was false, so the runtime RED-evidence classifier gate was not enabled; the target test and semantic failure were inspected directly.

## Deferred Issues

- CPU-04/CPU-05 requirement traceability and all Phase 2 completion claims remain pending Phase 2 verification.
- Hardware-backed execution was not available in this run; no local emulator result is presented as a physical DMG observation.

## Self-Check: PASSED

- Summary and three test artifacts exist at their recorded paths.
- Task commits `060dace`, `a3b4983`, and `4d3115e` are ancestors of the current phase branch head.
- The focused 18-case diagnostics, runner negative-control, per-case, and strict suite inventory passed after summary creation; the full suite passed 90/90 after the implementation commit.
- The task commit range measured three commits from `96e29af6cad1f91b75bb7aec86f496f110766f5d` through `4d3115e8944262686e4944575295691ab9df2180`.
