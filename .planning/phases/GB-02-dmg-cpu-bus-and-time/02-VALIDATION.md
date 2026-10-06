---
phase: "GB-02"
slug: "dmg-cpu-bus-and-time"
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-10-06"
---

# Phase 2 — Validation Strategy

This is the execution validation contract, not a record of passing Phase 2 tests. Research is in [02-RESEARCH.md](02-RESEARCH.md); the planner reconciles the per-task map with the final plans before the checker runs.

## Test Infrastructure

| Property | Value |
|----------|-------|
| Framework | Project-owned C17 executables and CTest; CMake minimum 3.25 |
| Config files | `CMakeLists.txt`, `tests/CMakeLists.txt`, `CMakePresets.json`, `tests/expected-tests.txt` |
| Quick run command | `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error` |
| Full suite command | Same command, plus relocated C/C++ consumers, required installed inventory and Linux `phase1-asan` lane at phase qualification |
| Runtime | Not measured for Phase 2; measure the new focused checks during their first execution |

## Sampling Rate

- After every task commit: run its automated verification with a stated observable failing direction; use focused selections only after their named tests are registered.
- After every plan wave: run the full suite and fail on missing mandatory cases, unexpected skips, timeout or failure.
- Before implementation completion: run all eligible pinned CPU/timer cases, sanitizer and installed-consumer checks; inspect required remote checks for the exact reviewed SHA.
- Target focused feedback latency: under 30 seconds; establish actual durations during execution. Longer corpus/reproduction/hosted runs remain separate gates and must report actual duration.

## Requirement Verification Map

| Requirement | Behavior | Test class | Planned command | Exists now |
|-------------|----------|------------|-----------------|------------|
| CPU-01 | All legal base/CB semantics, flags, addresses, timed accesses, illegal lockup | Owned unit/regression plus admitted hardware-verifiable DAA fixture | `ctest --preset phase1 --output-on-failure --no-tests=error -R 'cpu_'` | New focused tests required |
| CPU-02 | Interrupt entry, delayed EI, HALT/bug, STOP/wake, reset/post-boot | Owned timed sequence tests and applicable upstream cases | `ctest --preset phase1 --output-on-failure --no-tests=error -R 'interrupt_|halt_|stop_|reset_'` | New focused tests required |
| CPU-03 | Supported memory map, timer falling edges/reload races, disconnected serial | Owned bus/device cases and admitted Mooneye timer cases | `ctest --preset phase1 --output-on-failure --no-tests=error -R 'bus_|timer_|serial_'` | New focused tests required |
| CPU-04 | Equal actual elapsed time/input partitions, no overshoot, bounded stopped/output outcomes | Metamorphic and API boundary tests | `ctest --preset phase1 --output-on-failure --no-tests=error -R 'partition_|run_bounds|trace_capacity'` | Bounds/trace tests exist; event/partition coverage is new |
| CPU-05 | Pinned offline fixtures, explicit statuses, denominator and bounded replay receipts | Runner integration, manifest/digest checks and fail-closed controls | `ctest --preset phase1 --output-on-failure --no-tests=error -R 'mooneye_|fixture_'` | New fixtures/runner coverage required |

## Per-Task Verification Map

The final planner must replace this paragraph with one row per executable task: Task ID, Plan, Wave, Requirement, Threat Ref, Secure Behavior, Test Type, Automated Command, File Exists, Status. Every task has a non-watch automated command and a `fails_when` statement; not-yet-existing files are created in that task or an earlier dependency. All execution results remain pending at planning handoff.

## Wave 0 Requirements

- [ ] Register focused CPU semantic/timing cases and independent expected results.
- [ ] Register interrupt/EI/HALT/STOP/reset and event/partition cases.
- [ ] Register bus/timer/serial cases and guard output/event bounds.
- [ ] Review and prepare individually eligible Mooneye fixture bytes, include/asset rights, WLA-DX builder pin, digests, boot/profile/protocol and tick budgets.
- [ ] Register runner protocol, receipt, missing-fixture and malformed-manifest controls.
- [ ] Extend the existing required CTest inventory and preserve relocated C/C++ consumer checks.

These gaps are assigned to implementation tasks before their verification commands run. Ordinary build/tests remain offline and use checked-in bytes; fixture reproduction is an explicit maintainer/CI action.

## Manual-Only Verifications

No routine manual UAT is required. Automated cases qualify the declared corpus and deterministic bootless profile. Fresh physical DMG-CPU-B observation is unavailable here; upstream hardware-author evidence and owned regression/metamorphic checks must be labeled separately. Cartridge reads without a responding device are documented as undefined (Gekkio revision 192 §12.1); a fixed-byte electrical model is not qualified. Deferred PPU, DMA, JOYP, audio and CGB behavior are excluded.

## Validation Sign-Off

- [ ] All tasks have automated verification or an earlier test-creation dependency.
- [ ] No three consecutive tasks lack automated verification.
- [ ] All missing files/test registrations have explicit ownership and ordering.
- [ ] No watch-mode flags or zero-case successful selections.
- [ ] Per-task map and security threat references match final plans.
- [ ] `nyquist_compliant: true` is set only after planning checks pass; `wave_0_complete` remains false until the test gaps are implemented and verified.

Approval: pending plan review. Implementation verification is pending.
