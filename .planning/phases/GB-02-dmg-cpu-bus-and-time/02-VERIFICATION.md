---
phase: GB-02-dmg-cpu-bus-and-time
verified: 2026-10-09T12:43:21Z
status: passed
score: 5/5 roadmap truths verified
covered_files:
  - .planning/phases/GB-02-dmg-cpu-bus-and-time/02-01-PLAN.md
  - .planning/phases/GB-02-dmg-cpu-bus-and-time/02-01-SUMMARY.md
  - .planning/phases/GB-02-dmg-cpu-bus-and-time/02-02-PLAN.md
  - .planning/phases/GB-02-dmg-cpu-bus-and-time/02-02-SUMMARY.md
  - .planning/phases/GB-02-dmg-cpu-bus-and-time/02-03-PLAN.md
  - .planning/phases/GB-02-dmg-cpu-bus-and-time/02-03-SUMMARY.md
  - .planning/phases/GB-02-dmg-cpu-bus-and-time/02-04-PLAN.md
  - .planning/phases/GB-02-dmg-cpu-bus-and-time/02-04-SUMMARY.md
  - .planning/phases/GB-02-dmg-cpu-bus-and-time/02-05-PLAN.md
  - .planning/phases/GB-02-dmg-cpu-bus-and-time/02-05-SUMMARY.md
  - .planning/phases/GB-02-dmg-cpu-bus-and-time/02-06-PLAN.md
  - .planning/phases/GB-02-dmg-cpu-bus-and-time/02-06-SUMMARY.md
  - .planning/phases/GB-02-dmg-cpu-bus-and-time/02-07-PLAN.md
  - .planning/phases/GB-02-dmg-cpu-bus-and-time/02-07-SUMMARY.md
  - .planning/phases/GB-02-dmg-cpu-bus-and-time/02-08-PLAN.md
  - .planning/phases/GB-02-dmg-cpu-bus-and-time/02-08-SUMMARY.md
  - .planning/phases/GB-02-dmg-cpu-bus-and-time/02-09-PLAN.md
  - .planning/phases/GB-02-dmg-cpu-bus-and-time/02-09-SUMMARY.md
  - .planning/phases/GB-02-dmg-cpu-bus-and-time/02-10-PLAN.md
  - .planning/phases/GB-02-dmg-cpu-bus-and-time/02-10-SUMMARY.md
  - .planning/phases/GB-02-dmg-cpu-bus-and-time/02-11-PLAN.md
  - .planning/phases/GB-02-dmg-cpu-bus-and-time/02-11-SUMMARY.md
  - .planning/phases/GB-02-dmg-cpu-bus-and-time/02-12-PLAN.md
  - .planning/phases/GB-02-dmg-cpu-bus-and-time/02-12-SUMMARY.md
  - .planning/phases/GB-02-dmg-cpu-bus-and-time/02-13-PLAN.md
  - .planning/phases/GB-02-dmg-cpu-bus-and-time/02-13-SUMMARY.md
  - .planning/phases/GB-02-dmg-cpu-bus-and-time/02-14-PLAN.md
  - .planning/phases/GB-02-dmg-cpu-bus-and-time/02-14-SUMMARY.md
  - .planning/phases/GB-02-dmg-cpu-bus-and-time/02-15-PLAN.md
  - .planning/phases/GB-02-dmg-cpu-bus-and-time/02-15-SUMMARY.md
  - .planning/phases/GB-02-dmg-cpu-bus-and-time/02-16-PLAN.md
  - .planning/phases/GB-02-dmg-cpu-bus-and-time/02-16-SUMMARY.md
  - .planning/phases/GB-02-dmg-cpu-bus-and-time/02-17-PLAN.md
  - .planning/phases/GB-02-dmg-cpu-bus-and-time/02-17-SUMMARY.md
  - .planning/phases/GB-02-dmg-cpu-bus-and-time/02-18-PLAN.md
  - .planning/phases/GB-02-dmg-cpu-bus-and-time/02-18-SUMMARY.md
  - README.md
  - fixtures/mooneye/ELIGIBILITY.md
  - fixtures/mooneye/SOURCES.md
  - fixtures/mooneye/headless-report.patch
  - fixtures/mooneye/manifest.json
  - include/gabbaboy/gabbaboy.h
  - src/core/gabbaboy.c
  - src/runner/main.c
  - tests/CMakeLists.txt
  - tests/expected-tests.txt
  - tests/scripts/probe-mooneye-candidate.sh
  - tests/scripts/reproduce-mooneye.sh
  - tests/scripts/verify-mooneye-hosted-candidate.sh
  - tests/scripts/verify-mooneye-unadmitted.sh
  - tests/scripts/verify-phase2-hosted.sh
  - tests/scripts/verify-phase2-installed.sh
  - tests/test_bus.c
  - tests/test_control.c
  - tests/test_cpu.c
  - tests/test_diagnostics.c
  - tests/test_events.c
  - tests/test_runner.c
  - tests/test_serial.c
  - tests/test_timer.c
covered_digest: "v3:sha256:a4d559a66924b04d4b5bf1ad5bff1fdbaae3cbd0b97095535364cfbb8144277a"
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: passed
  previous_score: 5/5
  gaps_closed: []
  gaps_remaining: []
  regressions: []
---

# Phase 2: DMG CPU, Bus, and Time Verification Report

**Phase Goal:** As a core integrator, I want to run the declared DMG instruction and timing behavior deterministically, so that I can reproduce diagnostic failures.
**Verified:** 2026-10-09T12:43:21Z
**Status:** passed
**Re-verification:** Yes — fresh verification of the previously passing phase report against the current checkout.

## User Flow Coverage

User story: «As a core integrator, I want to run the declared DMG instruction and timing behavior deterministically, so that I can reproduce diagnostic failures.»

| Step | Expected | Evidence | Status |
|------|----------|----------|--------|
| Run diagnostics | The headless runner accepts the pinned manifest and executes the eligible CPU/timer cases under the declared bootless model. | `build/gabbaboy-runner --manifest fixtures/mooneye/manifest.json --suite --receipt` ran the guest bytes; all three returned `status=pass`, `profile=DMG-CPU-B`, `boot=skipped`. | ✓ VERIFIED |
| Reproduce a result | Each receipt identifies the fixture/source/digest, callback and `LD B,B` result PC, bounded budget, stop reason, and recent trace events. | The three live receipts report `protocol_stage=callback-then-ld-b-b`, `protocol_reason=none`, finite budgets, `recent=128`, and ordered diagnostic records. | ✓ VERIFIED |
| Outcome | The integrator can reproduce failures within this declared diagnostic scope. | `tests/test_runner.c` and the runner distinguish pass, guest fail, timeout, unsupported, malformed/missing fixture, and wrong breakpoint; the 88-test focused Phase 2 selection passed, including negative controls. | ✓ VERIFIED |

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|---|---|---|
| 1 | The declared DMG profile produces expected base/CB instruction, flag, arithmetic, address and bus-timing results, with explicit illegal-opcode behavior (CPU-01). | ✓ VERIFIED | `tests/test_cpu.c` contains independent full architectural post-state checks for every legal unprefixed encoding, branch outcomes, arithmetic boundaries, memory effects and timed observer assertions; all 11 unused opcodes remain lockup cases. Focused CTest cases `cpu_base_matrix`, `cpu_base_conditional_paths`, `cpu_base_arithmetic_edges`, `cpu_base_address_effects`, `cpu_cb_matrix`, and `cpu_illegal_lockup` passed. |
| 2 | Model-applicable cases observe expected interrupt entry, EI delay, HALT/HALT-bug, STOP, reset and deterministic post-boot results (CPU-02). | ✓ VERIFIED | `tests/test_control.c` exercises interrupt priority/entry, EI delay and chaining, HALT idle/timer/bug, STOP wake, reset profile/header flags and persistent lockup reset; corresponding current CTest cases passed. `tests/test_bus.c` verifies HALT-bug fetch behavior. |
| 3 | Guests observe declared mapping, divider/timer edges and reload races, and disconnected serial at timed boundaries (CPU-03). | ✓ VERIFIED | `tests/test_bus.c`, `tests/test_timer.c` and `tests/test_serial.c` assert guest-visible reads/writes and timed bus/edge results. Current bus, timer and serial focused cases passed. Strict manifest validation confirms the fixed one-CPU/two-timer set. |
| 4 | Equal timestamped inputs/time yield equal supported state/output across partitions; LCD-off, HALT/STOP, lockup and full output capacity remain bounded (CPU-04). | ✓ VERIFIED | `tests/test_events.c` and `tests/test_control.c` compare whole/partitioned runs, event order and STOP wake; deadline, overflow and output-capacity cases assert bounded return and preserved canaries. All selected event/control/bounds tests passed. |
| 5 | Headless runs report pass/fail/timeout/unsupported for a pinned eligible CPU/timer corpus with model/protocol identity and replay evidence (CPU-05). | ✓ VERIFIED | The live runner receipt command executed all three admitted cases with `eligible=3 executed=3 status=pass`; receipts identify source, patch, builder and fixture digests, model, callback/result protocol and bounded recent diagnostics. `probe-mooneye-candidate.sh` passed positive and induced-negative callbacks with zero PPU accesses; all runner and corpus CTests passed. |

**Score:** 5/5 roadmap truths verified; behavior-unverified: 0.

### Required Artifacts

| Artifact | Expected | Status | Details |
|---|---|---|---|
| `src/core/gabbaboy.c`, `include/gabbaboy/gabbaboy.h` | Substantive CPU, bus, timer, serial, interrupt, time and bounded public API | ✓ VERIFIED | Public `gbb_run` path reaches opcode execution, timed bus/device helpers and explicit stop reasons; direct guest-facing regressions exercise the path. |
| `tests/test_cpu.c`, `tests/test_control.c`, `tests/test_bus.c`, `tests/test_timer.c`, `tests/test_serial.c`, `tests/test_events.c` | Value-level and timed behavior regressions | ✓ VERIFIED | Registered named CTest programs dispatch to substantive tests; the current 88-case phase-focused selection passed. |
| `src/runner/main.c`, `tests/test_runner.c`, `tests/test_diagnostics.c` | Bounded diagnostic classification and replay receipts | ✓ VERIFIED | The runner loads digest-pinned files, checks callback then exact result PC, records bounded diagnostics and returns distinct statuses; current live suite and negative-control tests passed. |
| `fixtures/mooneye/manifest.json`, source/eligibility records, candidate patch and reproduction scripts | Fixed eligible set with rights, derivation, exact build and protocol provenance | ✓ VERIFIED | Manifest has exactly 3 eligible entries (one CPU, two timer); source records preserve original assertion paths and describe the derived headless reporting closure and its boundary. |
| `tests/CMakeLists.txt`, `tests/expected-tests.txt`, `.github/workflows/ci.yml`, installed consumers | Required inventory and wired public consumption | ✓ VERIFIED | Relevant cases are registered and included in the expected inventory; CI invokes CTest and verifies inventory; the relocated C/C++ consumer helper and prior exact hosted evidence remain available. |
| `tests/scripts/verify-phase2-open-gate.sh` | Conditional helper for the corpus-unqualified branch of Plan 02-16 | N/A (conditional path) | This file is absent. The current manifest and Plan 02-17 record the candidates as admitted/qualified, so Plan 02-16's open-gate branch is not active; the admitted runner/hosted path is present and passes. |

### Key Link Verification

| From | To | Via | Status | Details |
|---|---|---|---|---|
| `gbb_run` | CPU/bus/device execution | Timed phases and common execution path | ✓ WIRED | Direct public-API tests execute actual guest programs and observe bus/timer/trace results. |
| Base and CB opcode vectors | Core execution | `gbb_load_rom` and `gbb_run` | ✓ WIRED | Test-owned ROM bytes run through the public API; expected states are separately authored and asserted after execution. |
| Timestamped event queue | STOP wake and run partitioning | Instance queue plus emulated timeline | ✓ WIRED | `event_stop_wake`, `event_partition`, queue order/atomicity and deadline cases pass. |
| Manifest and fixture bytes | Strict runner receipt | Digest validation, callback, exact `LD B,B` result breakpoint | ✓ WIRED | Current live suite emits three passing receipts with matching eligible/executed totals and bounded traces. |
| CTest inventory | CI enforcement | Registered test names and `verify-test-inventory.sh` | ✓ WIRED | The workflow runs CTest and the required inventory validator; the orchestrator's current full local inventory passed 179/179. |
| Installed target | External C/C++ consumers | Relocated install, configure, link and execute | ✓ WIRED | The Phase 2 install verifier and C/C++ consumer tests are present; prior exact-revision installed inventory recorded 109/109. |

Plan 02-18's `verify.key-links` query does not accept its legacy prose in `from` as a file path, so it returned malformed-link diagnostics. The links above were traced manually through source, registration, dispatch and executed tests. Earlier plans also use legacy scalar `key_links` rather than the current structured `from`/`to`/`via` schema; those links were manually checked against the implementation and tests.

### Data-Flow Trace (Level 4)

| Artifact | Data | Source | Produces real data | Status |
|---|---|---|---|---|
| Test vectors → core | Opcode, operands and initial state | Fixed test-owned ROM/program bytes | Yes; loaded into an instance and executed | ✓ FLOWING |
| Core → assertions | Registers, flags, PC/SP, bus events and timing | Public trace records and timed observer | Yes; compared to independently authored expected values | ✓ FLOWING |
| Fixture bytes → runner | CPU/timer guest behavior | Checked-in digest-verified derived ROMs from manifest | Yes; actual core execution | ✓ FLOWING |
| Runner → receipt | Status, callback/result PC, elapsed half-dots and recent trace | Guest execution plus bounded caller-owned diagnostics | Yes; live suite produced three receipts | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|---|---|---|---|
| Phase 2 CPU, control, bus, timer, serial, event, diagnostic and runner cases | `ctest --test-dir build --output-on-failure --no-tests=error -R '^(cpu_|interrupt_|halt_|stop_|reset_|event_|joypad_|bus_|timer_|serial_|diagnostics_|runner_|mooneye_)'` | 88/88 passed in 0.43 s | ✓ PASS |
| Diagnostic reproduction receipt | `build/gabbaboy-runner --manifest fixtures/mooneye/manifest.json --suite --receipt` | Three cases passed; final receipt `eligible=3 executed=3 status=pass`; bounded trace receipts emitted | ✓ PASS |
| Candidate result-protocol probe | `bash tests/scripts/probe-mooneye-candidate.sh` | Three positive callbacks and one induced failure reached callback and result breakpoint; zero PPU access | ✓ PASS |
| Current full local suite | Orchestrator command: `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error` | 179/179 passed (provided current-session evidence) | ✓ PASS |

### Probe Execution

| Probe | Command | Result | Status |
|---|---|---|---|
| Candidate callback/result protocol and PPU independence | `bash tests/scripts/probe-mooneye-candidate.sh` | Positive cases and induced failing assertion reached expected callback then exact breakpoint; zero PPU accesses | PASS |

### Test Quality Audit

| Test area | Requirement | Active | Assertion/oracle review | Verdict |
|---|---|---:|---|---|
| Base and CB opcode tests | CPU-01 | Yes | Expected values are authored from setup and instruction behavior, not copied from core output; legal states, flags and costs plus illegal lockup are asserted. | Adequate |
| Control, timer, bus, serial and event tests | CPU-02/03/04 | Yes | Tests assert concrete guest-visible states, timed events, partition equality, bounded outcomes and reset/wake transitions. No disabled-test markers were found in linked files. | Adequate |
| Runner and diagnostic tests | CPU-05 | Yes | Tests exercise pass/fail/timeout/unsupported, invalid fixtures, protocol sequencing and bounded diagnostic capacity. Live receipts flow from actual checked-in fixture bytes. | Adequate |

No linked requirement tests were disabled. The tested paths do not generate their own expected values from the system under test. The three admitted fixtures retain their source/rights record and unchanged upstream assertions, but they are **derived headless reporting closures**, not the original PPU-dependent Mooneye reporting paths.

### Requirements Coverage

| Requirement | Source plans | Description | Status | Evidence |
|---|---|---|---|---|
| CPU-01 | 02-02, 02-03, 02-07, 02-09, 02-10, 02-14, 02-16, 02-17, 02-18 | Base/CB semantics, flags, addresses, timing and explicit illegal behavior | SATISFIED | Independent semantic tests and current focused CTest cases pass. |
| CPU-02 | 02-04, 02-06, 02-09, 02-10, 02-11, 02-16 | Interrupts, EI delay, HALT/STOP, reset and bootless profile | SATISFIED | Named current control and bus regressions pass. |
| CPU-03 | 02-01, 02-05, 02-06, 02-07, 02-09, 02-11, 02-14, 02-16 | Mapping, timer races and disconnected serial | SATISFIED | Bus, timer, serial and eligible diagnostic tests pass with guest-visible assertions. |
| CPU-04 | 02-01, 02-02, 02-04, 02-06, 02-08, 02-09, 02-10, 02-11, 02-16 | Partition equivalence and bounded outcomes | SATISFIED | Event/control partition and output/deadline bounds pass. |
| CPU-05 | 02-07, 02-08, 02-09, 02-14, 02-16, 02-17 | Fixed eligible corpus, honest statuses and replay evidence | SATISFIED | Live runner outputs three receipts against the fixed one-CPU/two-timer denominator; protocol probe and fixture identity checks pass. |

No orphaned Phase 2 requirements were found: ROADMAP.md maps CPU-01 through CPU-05, and all five are declared in phase plans and covered above. Plan 02-15 is explicitly superseded/non-runnable; it remains historical evidence and is not treated as an active plan requirement.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|---|---:|---|---|---|
| None | — | No unreferenced debt markers, placeholder behavior, empty core implementation or disabled linked tests found. The phrase `not available` in the hosted-evidence formatter is an explicit missing-link display value, not a stub. | — | No anti-pattern gap. |

### Human Verification Required

None. This is a core/diagnostic foundation phase, and its behavior is exercised through deterministic tests and the headless runner. There was no physical DMG-CPU-B observation. That limitation is recorded and is not asserted as phase evidence or as a compatibility claim.

### Gaps Summary

No remaining gaps. Current implementation and focused tests establish the five roadmap truths, and the current-session full local suite passed 179/179. The corpus is exactly three source-qualified derived headless reporting closures (one CPU, two timer); the upstream original Mooneye result paths remain PPU/LY-dependent and excluded. No physical DMG-CPU-B observation or broad compatibility claim is made.

---

_Verified: 2026-10-09T12:43:21Z_
_Verifier: the agent (gsd-verifier)_
