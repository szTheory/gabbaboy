---
phase: "GB-02"
slug: "dmg-cpu-bus-and-time"
status: validated
nyquist_compliant: false
wave_0_complete: false
created: "2026-10-06"
---

# Phase 2 — Validation Strategy

This records the validation contract and execution audit. Research is in [02-RESEARCH.md](02-RESEARCH.md); [02-PLAN-CHECK.md](02-PLAN-CHECK.md) records independent plan review. The audit is finished, but Nyquist compliance and Wave 0 completion remain false: seven correctness/applicability/hosted gaps remain after independent review and goal verification.

## Test Infrastructure

| Property | Value |
|----------|-------|
| Framework | Project-owned C17 executables and CTest; CMake minimum 3.25 |
| Config files | `CMakeLists.txt`, `tests/CMakeLists.txt`, `CMakePresets.json`, `tests/expected-tests.txt` |
| Quick run command | `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error` |
| Full suite command | Same command, plus relocated C/C++ consumers, required installed inventory and Linux `phase1-asan` lane at phase qualification |
| Runtime | See per-plan evidence; no emulator performance baseline is qualified |

## Sampling Rate

- After every task commit: run its automated verification with a stated observable failing direction; use focused selections only after their named tests are registered.
- After every plan wave: run the full suite and fail on missing mandatory cases, unexpected skips, timeout or failure.
- Before implementation completion: run all eligible pinned CPU/timer cases, sanitizer and installed-consumer checks; inspect required remote checks for the exact reviewed SHA.
- Target focused feedback latency: under 30 seconds; establish actual durations during execution. Longer corpus/reproduction/hosted runs remain separate gates and must report actual duration.

## Requirement Verification Map

| Requirement | Behavior | Test class | Planned command | Exists now |
|-------------|----------|------------|-----------------|------------|
| CPU-01 | All legal base/CB semantics, flags, addresses, timed accesses, illegal lockup | Owned unit/regression plus admitted hardware-verifiable DAA fixture | `ctest --preset phase1 --output-on-failure --no-tests=error -R '^(cpu_|mooneye_required_suite$)'`; run the finite DAA runner check in 02-07-T1 | Tests exist; review/qualification gaps remain |
| CPU-02 | Interrupt entry, delayed EI, HALT/bug, STOP/wake, reset/post-boot | Owned timed sequence tests and applicable upstream cases | `ctest --preset phase1 --output-on-failure --no-tests=error -R '^(interrupt_|halt_|stop_|reset_|event_(stop_wake|boundary)$)'` | Tests exist; review/qualification gaps remain |
| CPU-03 | Supported memory map, timer falling edges/reload races, disconnected serial | Owned bus/device cases and admitted Mooneye timer cases | `ctest --preset phase1 --output-on-failure --no-tests=error -R '^(bus_|timer_|serial_|event_external_serial_edges$|mooneye_required_suite$)'`; run the fixture verifier in 02-07-T2 | Tests exist; review/qualification gaps remain |
| CPU-04 | Equal actual elapsed time/input partitions, no overshoot, bounded stopped/output outcomes | Metamorphic and API boundary tests | `ctest --preset phase1 --output-on-failure --no-tests=error -R '^(bus_preflight$|cpu_(call_stack|conditional_budget)$|interrupt_|halt_|stop_|reset_|timer_|serial_|event_|run_output_capacity$|diagnostics_)'`; run the installed-consumer helper in 02-09-T1 | Tests exist; interrupt diagnostic ordering gap remains |
| CPU-05 | Pinned offline fixtures, explicit statuses, denominator and bounded replay receipts | Runner integration, manifest/digest checks and fail-closed controls | `ctest --preset phase1 --output-on-failure --no-tests=error -R '^(mooneye_|fixture_|runner_)'`; run the fixture verifier, two-run receipt check and installed-consumer helper in 02-07-T1/T2, 02-08-T1 and 02-09-T1 | Tests exist; required corpus qualification fails |

## Per-Task Verification Map

Commands below use `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error -R '<selection>'` unless a complete command is printed. Each named selection is registered in the same task before it runs. Every plan task includes the observable failing direction beside its runnable command. Current execution evidence is recorded below; prior summary passes are superseded where the corrected bus guard exposed corpus failures.

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure behavior / test class | Selection or complete command | File exists / creation dependency | Status |
|---|---:|---:|---|---|---|---|---|---|
| 02-01-T1 | 01 | 1 | CPU-03,04 | T-02-01,02 | Guest WRAM/map, preflight, existing API/loader A000 regression | `^bus_(wram_guest\|echo_hram\|absent_cart\|preflight)$` | `tests/test_bus.c` created T1; `tests/test_api.c` and `tests/test_loader.c` revised T1 | pass |
| 02-01-T2 | 01 | 1 | CPU-03 | T-02-01,SC | WRAM tracer bytes/digest and original C/C++ consumer regression | full offline CTest | tracer bytes/manifest, runner, tracer tests and consumers revised T2 | pass |
| 02-02-T1 | 02 | 2 | CPU-01,04 | T-02-03,04 | Timed conditional stack guest | `^cpu_(call_stack\|conditional_budget)$` | `tests/test_cpu.c` created T1 | pass |
| 02-02-T2 | 02 | 2 | CPU-01 | T-02-03,04 | All base encodings, flags, lockup; original D3/short-budget regressions | `^cpu_(base_matrix\|illegal_lockup\|flags_edges\|timed_access)$` | test matrix, `tests/test_tracer.c`, `tests/test_api.c`, runner revised T2 | pass |
| 02-03-T1 | 03 | 3 | CPU-01 | T-02-05 | CB memory guest and short budget | `^cpu_cb_(wram\|budget)$` | CB tests added T1 | pass |
| 02-03-T2 | 03 | 3 | CPU-01 | T-02-05,06 | All CB encodings/flags/timing | `^cpu_cb_(matrix\|flags_edges\|timed_access)$` | CB matrix extended T2 | pass |
| 02-04-T1 | 04 | 4 | CPU-02 | T-02-07,08 | Interrupt vector/stack and no-progress | `^interrupt_(entry\|budget)$` | `tests/test_control.c` created T1 | pass |
| 02-04-T2 | 04 | 4 | CPU-02,04 | T-02-07,08 | EI/HALT/STOP/reset control states | `^(interrupt_(ei_delay\|priority)\|halt_(idle\|bug)\|stop_wait\|reset_(profile\|lockup))$` | control tests extended T2 | pass |
| 02-05-T1 | 05 | 5 | CPU-03 | T-02-09,10 | Overflow/reload inside guest instruction | `^timer_(guest_overflow\|mid_instruction)$` | `tests/test_timer.c` created T1 | pass |
| 02-05-T2 | 05 | 5 | CPU-03,04 | T-02-09,10,11 | Source-qualified selector/reload/race/serial and unsupported overlap | `^(timer_(selectors\|div_write\|tac_write\|tima_collision\|tma_collision)\|serial_(internal_disconnected\|external_pending\|unqualified_overlap))$` | `tests/test_serial.c` created T2; per-instance timed bus observer from 02-02 | pass |
| 02-06-T1 | 06 | 6 | CPU-02,04 | T-02-12 | STOP DIV reset, frozen devices, bounded master-time wait/wake, zero/exact budget | `^event_(stop_wake\|boundary)$` | `tests/test_events.c` created T1 | pass |
| 02-06-T2 | 06 | 6 | CPU-03,04 | T-02-12,13 | Atomic queue/partition/external edges/overflow and existing trace canary | `^(event_(queue_order\|queue_atomic\|partition\|deadline_inside\|external_serial_edges\|time_overflow)\|run_output_capacity)$` | events tests extended T2; diagnostics remain 02-08 | pass |
| 02-07-T1 | 07 | 7 | CPU-01,05 | T-02-14,15,SC | Pinned WLA CPU ROM, digest, real guest | `cmake -DGBB_MOONEYE_DIR=fixtures/mooneye -P cmake/VerifyMooneye.cmake` and finite runner outcome | `fixtures/mooneye/daa.gb` and verifier created T1 | digest pass; hosted reproduction and protocol blocked |
| 02-07-T2 | 07 | 7 | CPU-03,05 | T-02-14,15,SC | Nonzero CPU/timer eligible set and digests | `cmake -DGBB_MOONEYE_DIR=fixtures/mooneye -P cmake/VerifyMooneye.cmake` | timer ROMs created T2 | digest pass; hosted reproduction and protocol blocked |
| 02-07-T3 | 07 | 7 | CPU-05 | T-02-14,15 | Offline corpus inventory CTest registration | `^mooneye_(fixture_digest\|eligible_inventory)$` | CTest/inventory created T3 | pass |
| 02-08-T1 | 08 | 8 | CPU-04,05 | T-02-17,18 | Direct diagnostic zero/exact/short/null/canary and repeatable ROM receipt | `^diagnostics_(zero\|exact\|short\|null\|canary)$` plus two-run Python receipt command in plan | `tests/test_diagnostics.c` created and registered T1; runner controls T2 | partial — required corpus fails |
| 02-08-T2 | 08 | 8 | CPU-05 | T-02-16,17 | Four status controls; fail-closed suite | `^(runner_(pass\|fail\|timeout\|unsupported\|missing_fixture\|bad_manifest\|zero_eligible)\|mooneye_required_suite)$` | runner tests extended T2 | partial — required corpus fails |
| 02-09-T1 | 09 | 9 | CPU-04,05 | T-02-19 | Fresh prefix-present/absent inventory and relocated C/C++ API contract | `bash tests/scripts/verify-phase2-installed.sh` | helper, consumers, CTest registration and `cmake/ExpectedTests.cmake` revised T1 | partial — required corpus fails |
| 02-09-T2 | 09 | 9 | CPU-01..05 | T-02-20 | Full noninstalled JUnit at `build/phase2-ctest.xml`, exact core-only and relocated inventories | full command in 02-09-T2 | CI/inventory revised T2; helper from T1 | partial — required corpus fails |

## Wave 0 Requirements

- [ ] Close CPU timing/startup coverage: RET/RETI phases and ROM-dependent post-boot flags remain missing.
- [ ] Close interrupt coverage: consecutive EI and device deadlines inside interrupt diagnostics remain missing.
- [x] Register bus/timer/serial cases and guard output/event bounds, including corrected unsupported-read and wrap regressions.
- [ ] Review and prepare individually eligible Mooneye fixture bytes, include/asset rights including font, WLA-DX builder pin, digests, boot/profile/protocol and finite tick budgets. At least one CPU and one timer case are required independent of emulator result.
- [x] Register diagnostics zero/exact/short/null/canary and runner protocol, receipt, missing-fixture and malformed-manifest controls.
- [x] Extend the required inventory and absent-prefix filter, reject failed/error reports, and preserve relocated C/C++ checks.

Remaining gaps are structured in [02-VERIFICATION.md](02-VERIFICATION.md). Next command: `$gsd-plan-phase 2 --gaps`. Ordinary build/tests remain offline and use checked-in bytes; fixture reproduction is an explicit maintainer/CI action.

## Manual-Only Verifications

No routine manual UAT is required. Automated cases qualify the declared corpus and deterministic bootless profile. Fresh physical DMG-CPU-B observation is unavailable here; upstream hardware-author evidence and owned regression/metamorphic checks must be labeled separately. Cartridge reads without a responding device are documented as undefined (Gekkio revision 192 §12.1); a fixed-byte electrical model is not qualified. Deferred PPU, DMA, JOYP, audio and CGB behavior are excluded.

## Validation Sign-Off

- [x] All tasks have automated verification or an earlier test-creation dependency.
- [x] No three consecutive tasks lack automated verification.
- [x] All missing files/test registrations have explicit ownership and ordering.
- [x] No watch-mode flags or zero-case successful selections.
- [x] Per-task map and security threat references match final plans.
- [x] `nyquist_compliant` and `wave_0_complete` remain false while automated correctness/applicability gates fail.

Planning review passed on 2026-10-06: nine plans, 19 tasks, five requirements and 12 context decisions. Independent execution verification now returns `gaps_found`. For 02-09 reports, pass a basename to CTest's preset/test-dir invocation and verify it beneath the selected test directory; clear the installed prefix for core-only inventory. A temporary one-test CTest probe reproduced this report-path behavior; it is tooling evidence, not emulator validation.

## Seven Fallback Assumptions

The specless CPU-01 adjacency, empty-budget and ordering probes map to `cpu_conditional_budget`, `event_boundary` and `event_queue_order` respectively; their named cases have executed; the gaps below remain. The unclassified CPU-02 control-state probe maps to `interrupt_ei_delay`, `halt_idle`, `stop_wait` and `event_stop_wake`. The unclassified CPU-03 bus/timer collision probe maps to `bus_absent_cart`, `timer_tima_collision` and `timer_tma_collision`. The unclassified CPU-04 partition/output probe maps to `event_partition`, `run_output_capacity` and the direct 02-08 diagnostic bounds cases. The unclassified CPU-05 corpus/rights/protocol probe maps to source/asset closure in 02-07 and strict `mooneye_required_suite` in 02-08. Owned cases have executed, but review identifies missing consecutive-EI and timed return/interrupt ordering coverage. Corpus applicability remains blocked; no fallback assumption waives it.

## Execution Audit — 2026-10-06

At source revision `c583e33`, fresh offline Linux normal and ASan/UBSan builds each executed 94 cases: 90 passed and four failed, with no skips. Failures are `mooneye_required_suite`, `mooneye_case_daa`, `mooneye_case_tim00`, and `mooneye_case_tim00-div-trigger`. No sanitizer finding was reported; the sanitizer suite is nevertheless failing. The exact inventory checker rejects failed reports rather than presenting execution counts as success.

The three fixed required ROMs reach LY (`FF44`) through their common reporting path before the declared `LD B,B` completion protocol. PPU/LY is outside this phase. Earlier 3/3 pass claims depended on fabricated unsupported-address reads and are superseded. Fixture digests and source reproduction remain valid; runtime qualification does not. CPU-05 is PARTIAL, with an automated failing gate, not a manual-only item. CPU-01..04 have substantial owned coverage, with final correctness assessment delegated to independent review/verification. No CPU requirement is marked complete.

Corrective regressions cover all read addressing families, CB/stack/fetch rejection without mutation, 16-bit address/stack wrap, and timer-driven HALT wake under partitions. Eight focused checks passed, including the adjusted base matrix using implemented DIV addresses. This new evidence does not make the overall phase green. CMake script-mode policy setup and failed/error JUnit rejection were also corrected and verified with negative controls.

No routine human UAT is required. The remaining corpus issue is a source/implementation qualification gap; screenshots or manual acknowledgement cannot close it. Hosted exact-SHA qualification remains pending. Phase 3 is paused.

## Validation Audit 2026-10-06

| Metric | Count |
|---|---|
| Gaps found | 7 |
| Resolved | 0 |
| Escalated | 7 |

Independent code review adds four core gaps: startup F, RET/RETI stack phases, consecutive EI, and interrupt diagnostic ordering. The initial corpus gap plus these four and the subsequent Windows manifest/reproduction failures are the seven distinct entries in the verification report. Named per-task passes above describe the registered cases; they do not establish the uncovered behaviors. All CPU requirements remain pending.

Hosted qualification at PR head `a91d8e7` is failing: Linux/macOS native 95/99, ASan/UBSan and CMake floor 90/94, Windows 93/99. Windows reports invalid-manifest for two negative controls; the Mooneye reproduction job reports different DAA bytes. Earlier local reproduction does not establish cross-host reproduction. See [hosted evidence](02-HOSTED-EVIDENCE.md); both causes remain unresolved.
