---
phase: GB-02-dmg-cpu-bus-and-time
verified: 2026-10-10T12:53:55Z
status: passed
score: 5/5 roadmap truths verified
covered_files:
  - .github/workflows/ci.yml
  - .gitignore
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
covered_digest: "v3:sha256:0d86347cf460d35f4492a5d24ea3c0d7209e2ea9d887bcce315c901a2450327f"
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
**Verified:** 2026-10-10T12:53:55Z
**Status:** passed
**Re-verification:** Yes. Freshness regeneration of a previously passing report. It was stale because (a) quick task 261010-bz3 (a2411da) reconciled SUMMARY `requirements-completed` metadata, and (b) later-phase commits changed `.github/workflows/ci.yml` and `.gitignore`. Verified at HEAD `a9050df07f72678055bdbdab097d5300297ebfd6` on `gsd/phase-02-verification-refresh-2` (clean tree).

## User Flow Coverage

User story: "As a core integrator, I want to run the declared DMG instruction and timing behavior deterministically, so that I can reproduce diagnostic failures."

| Step | Expected | Evidence | Status |
|------|----------|----------|--------|
| Run diagnostics | The headless runner accepts the pinned manifest and executes the eligible CPU/timer cases under the declared bootless model. | `build/gabbaboy-runner --manifest fixtures/mooneye/manifest.json --suite --receipt` re-run this session: all three cases `status=pass`, `profile=DMG-CPU-B`, `boot=skipped`, final line `suite eligible=3 executed=3 status=pass`. | ✓ VERIFIED |
| Reproduce a result | Each receipt identifies fixture/source/digest, callback and `LD B,B` result PC, bounded budget, stop reason and recent trace. | Receipts carry `manifest_sha256`, `source_revision`, `report_patch_sha256`, `builder_revision`, `fixture_sha256`, `core_revision=a9050df`, `protocol_stage=callback-then-ld-b-b`, `protocol_reason=none`, finite `budget`, `stop=protocol-result`, `recent=128`. | ✓ VERIFIED |
| Outcome | Failures are reproducible within the declared scope. | `tests/test_runner.c` and `tests/test_diagnostics.c` cover pass, guest fail, timeout, unsupported, malformed/missing fixture and wrong breakpoint; the 88-case focused selection passed. | ✓ VERIFIED |

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|---|---|---|
| 1 | The declared DMG profile produces expected base/CB instruction, flag, arithmetic, address and bus-timing results, with explicit illegal-opcode behavior (CPU-01). | ✓ VERIFIED | `tests/test_cpu.c` asserts independent post-state for the legal base and CB encodings, branch outcomes, arithmetic edges, memory effects and timed observer events; the 11 unused opcodes are lockup cases. `cpu_*` cases passed in the 88/88 focused run and the 179/179 full run. |
| 2 | Model-applicable cases observe expected interrupt entry, EI delay, HALT/HALT-bug, STOP, reset and deterministic post-boot results (CPU-02). | ✓ VERIFIED | `tests/test_control.c` and `tests/test_bus.c` cover interrupt priority/entry, EI delay and chaining, HALT idle/timer/bug fetch, STOP wake, reset and persistent-lockup reset. The `interrupt_`, `halt_`, `stop_`, `reset_` and `bus_` cases passed. |
| 3 | Guests observe declared mapping, divider/timer edges and reload races, and disconnected serial at timed boundaries (CPU-03). | ✓ VERIFIED | `tests/test_bus.c`, `tests/test_timer.c`, `tests/test_serial.c` assert guest-visible reads/writes and timed edges; the `bus_`, `timer_` and `serial_` cases passed. The manifest holds exactly one CPU and two timer entries. |
| 4 | Equal timestamped inputs/time yield equal supported state/output across partitions; LCD-off, HALT/STOP, lockup and full output capacity stay bounded (CPU-04). | ✓ VERIFIED | `tests/test_events.c` and `tests/test_control.c` compare whole and partitioned runs, event order and STOP wake; deadline, overflow and output-capacity cases assert bounded return and canaries. `event_*` and related cases passed. |
| 5 | Headless runs report pass/fail/timeout/unsupported for a pinned eligible CPU/timer corpus with model/protocol identity and replay evidence (CPU-05). | ✓ VERIFIED | Live suite: `eligible=3 executed=3 status=pass`. `probe-mooneye-candidate.sh` re-run: `probe=pass ... ppu_access=0` and induced `probe=fail ... callback=1 breakpoint=1 ppu_access=0`, exit 0. Runner and mooneye CTests passed. |

**Score:** 5/5 roadmap truths verified; behavior-unverified: 0.

### Required Artifacts

| Artifact | Expected | Status | Details |
|---|---|---|---|
| `src/core/gabbaboy.c`, `include/gabbaboy/gabbaboy.h` | CPU, bus, timer, serial, interrupt, time and bounded public API | ✓ VERIFIED | Public `gbb_run` path is exercised by guest-program tests; the full tree builds and passes. |
| `tests/test_cpu.c`, `test_control.c`, `test_bus.c`, `test_timer.c`, `test_serial.c`, `test_events.c` | Value-level and timed regressions | ✓ VERIFIED | Registered CTest programs; focused selection 88/88. |
| `src/runner/main.c`, `tests/test_runner.c`, `tests/test_diagnostics.c` | Bounded classification and replay receipts | ✓ VERIFIED | Live receipts produced; negative-control tests pass. |
| `fixtures/mooneye/manifest.json`, `SOURCES.md`, `ELIGIBILITY.md`, `headless-report.patch`, reproduction scripts | Fixed eligible set with rights, derivation, build and protocol provenance | ✓ VERIFIED | Exactly 3 eligible entries; receipts echo manifest, patch, builder and fixture digests. |
| `tests/CMakeLists.txt`, `tests/expected-tests.txt`, `.github/workflows/ci.yml` | Required inventory enforced in CI | ✓ VERIFIED | `ci.yml` runs `ctest --no-tests=error` followed by `.github/scripts/verify-test-inventory.sh ... tests/expected-tests.txt` in native, ASan/UBSan and installed jobs (lines 29-30, 47-50, 78-82, 102-105). The later macOS player job (`macos-player-package`) is additive and does not change the Phase 2 inventory path. |
| `tests/scripts/verify-phase2-open-gate.sh` | Conditional open-gate helper for Plan 02-16 | N/A (conditional path) | Absent by design: Plan 02-17 admitted the candidates, so the open-gate branch is inactive. |

### Key Link Verification

| From | To | Via | Status | Details |
|---|---|---|---|---|
| `gbb_run` | CPU/bus/device execution | Timed phases, common execution path | ✓ WIRED | Public-API tests run guest programs and observe bus, timer and trace results. |
| Base and CB opcode vectors | Core execution | `gbb_load_rom` and `gbb_run` | ✓ WIRED | Test-owned ROM bytes run through the public API; expected states are authored separately. |
| Timestamped event queue | STOP wake and partitioning | Instance queue and emulated timeline | ✓ WIRED | `event_stop_wake`, `event_partition` and ordering cases pass. |
| Manifest and fixture bytes | Strict runner receipt | Digest validation, callback, exact `LD B,B` result breakpoint | ✓ WIRED | Live suite emits three passing receipts with matching eligible/executed totals. |
| CTest inventory | CI enforcement | Registered names and `verify-test-inventory.sh` | ✓ WIRED | Workflow lines above; local inventory 179 tests. |

Plan 02-18 and earlier plans use legacy or prose `key_links` that `verify.key-links` cannot parse; links were traced manually as above.

### Data-Flow Trace (Level 4)

| Artifact | Data | Source | Produces real data | Status |
|---|---|---|---|---|
| Test vectors to core | Opcode, operands, initial state | Test-owned ROM bytes | Yes | ✓ FLOWING |
| Core to assertions | Registers, flags, PC/SP, bus events, timing | Public trace and timed observer | Yes | ✓ FLOWING |
| Fixture bytes to runner | CPU/timer guest behavior | Digest-checked derived ROMs | Yes | ✓ FLOWING |
| Runner to receipt | Status, callback/result PC, ticks, recent trace | Guest execution | Yes (three live receipts) | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|---|---|---|---|
| Full local suite | `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error` | 179/179 passed (re-run by this verifier; `ctest -N` lists 179) | ✓ PASS |
| Phase 2 focused selection | `ctest --test-dir build --no-tests=error -R '^(cpu_\|interrupt_\|halt_\|stop_\|reset_\|event_\|joypad_\|bus_\|timer_\|serial_\|diagnostics_\|runner_\|mooneye_)'` | 88/88 passed | ✓ PASS |
| Diagnostic reproduction | `build/gabbaboy-runner --manifest fixtures/mooneye/manifest.json --suite --receipt` | `suite eligible=3 executed=3 status=pass` | ✓ PASS |

### Probe Execution

| Probe | Command | Result | Status |
|---|---|---|---|
| Candidate callback/result protocol and PPU independence | `bash tests/scripts/probe-mooneye-candidate.sh` | exit 0; positive `ppu_access=0`; induced failure reached callback and breakpoint with `ppu_access=0` | PASS |

### Historical Hosted Evidence

Exact hosted CI run 37620710587 and fixture reproduction run 37620710600 qualified implementation SHA `cf28e90270be24d9528bfa8a1e4055a2b8485989`. This is historical source-revision evidence retained from the prior report; it does not refer to the current refresh branch, and no hosted run is claimed for HEAD `a9050df`. The same-revision local evidence above is what supports this refresh.

### Summary-Metadata Credit Reconciliation (quick task 261010-bz3)

Summaries now credit: CPU-01 to 02-02 and 02-18; CPU-02 to 02-16; CPU-03 to 02-01; CPU-04 to 02-01 and 02-02; CPU-05 to 02-16 and 02-17. 02-10 lists `[]` with a contributory-evidence comment. Checked against the evidence:

- CPU-01: `02-02-SUMMARY` `[CPU-01, CPU-04]` and `02-18-SUMMARY` `[CPU-01]` match the base-instruction and independent post-state tests (truth 1).
- CPU-02: `02-16-SUMMARY` `[CPU-02, CPU-05]` matches the final control/reset semantic closure; truth 2 evidence is in `test_control.c` and `test_bus.c`, which Plan 02-16 covers.
- CPU-03: `02-01-SUMMARY` `[CPU-03, CPU-04]` covers the bus mapping tracer; timer and serial evidence (truth 3) is contributed by 02-05, 02-06 and 02-11, whose summaries intentionally list `[]`. Credit is attributed to the earliest plan owning the requirement, and every CPU-03 test is current and passing.
- CPU-04: 02-01 and 02-02 credits are consistent with partition/bounds tests (truth 4).
- CPU-05: `02-16-SUMMARY` and `02-17-SUMMARY` match the admitted corpus and runner closure (truth 5).

Every requirement ID has at least one crediting summary and passing current tests; none is orphaned. The credit is sparse for CPU-03, with timer/serial evidence only contributory in the other summaries, but it does not contradict the evidence. This is an informational observation, not a gap.

### Requirements Coverage

Plan frontmatter declares `requirements:` drawn only from CPU-01 through CPU-05, and REQUIREMENTS.md maps exactly those five to Phase 2 (lines 24-28 and 103-107). Plan 02-15 is superseded and non-runnable.

| Requirement | Source plans | Description | Status | Evidence |
|---|---|---|---|---|
| CPU-01 | 02-02, 02-03, 02-07, 02-09, 02-10, 02-14, 02-16, 02-17, 02-18 | Base/CB semantics, flags, addresses, timing, illegal behavior | SATISFIED | Truth 1; summary credit 02-02/02-18. |
| CPU-02 | 02-04, 02-06, 02-09, 02-10, 02-11, 02-16 | Interrupts, EI delay, HALT/STOP, reset, bootless profile | SATISFIED | Truth 2; summary credit 02-16. |
| CPU-03 | 02-01, 02-05, 02-06, 02-07, 02-09, 02-11, 02-14, 02-16 | Mapping, timer races, disconnected serial | SATISFIED | Truth 3; summary credit 02-01. |
| CPU-04 | 02-01, 02-02, 02-04, 02-06, 02-08, 02-09, 02-10, 02-11, 02-16 | Partition equivalence and bounded outcomes | SATISFIED | Truth 4; summary credit 02-01/02-02. |
| CPU-05 | 02-07, 02-08, 02-09, 02-14, 02-16, 02-17 | Fixed eligible corpus, honest statuses, replay evidence | SATISFIED | Truth 5; summary credit 02-16/02-17. |

No orphaned requirements.

### Supporting Audits

| Audit | Result |
|---|---|
| `02-VALIDATION.md` | `nyquist_compliant: true`; 8 gaps found, 8 resolved, 0 current. |
| `02-SECURITY.md` | `threats_open: 0`; all registered threats closed. |
| `02-REVIEW.md` / `02-REVIEW-DISPOSITION.md` | Review of `ci.yml` and `.gitignore`; no critical or warning findings; IN-01 info finding deferred with rationale and no open findings. |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|---|---:|---|---|---|
| None | n/a | No unreferenced debt markers in core, include, test sources or fixture records. The `XXXXXX` strings in `src/player/` are `mkstemp` templates in later-phase code, not debt markers. | n/a | None |

### Human Verification Required

None. This is a core/diagnostic phase exercised through deterministic tests and the headless runner. No physical DMG-CPU-B observation was made, and none is claimed.

### Gaps Summary

No gaps. The three admitted fixtures are source-qualified derived headless reporting closures (one CPU, two timer), not the original PPU-dependent Mooneye reporting paths, which remain excluded. No physical hardware or broad compatibility claim is made.

---

_Verified: 2026-10-10T12:53:55Z_
_Verifier: the agent (gsd-verifier)_
