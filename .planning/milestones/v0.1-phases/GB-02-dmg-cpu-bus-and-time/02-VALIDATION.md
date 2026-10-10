---
phase: "GB-02"
slug: "dmg-cpu-bus-and-time"
status: validated
nyquist_compliant: true
wave_0_complete: true
created: "2026-10-06"
---

# Phase 2 — Validation Strategy

This records the validation contract and final execution audit. Research is in [02-RESEARCH.md](02-RESEARCH.md); [02-PLAN-CHECK.md](02-PLAN-CHECK.md) records independent plan review. The earlier seven-gap audit and the later D-01 semantic gap are closed by Plans 02-10 through 02-18 and the passed independent verification. Current audit: 8 gaps found, 8 resolved, 0 escalated; Nyquist compliant and Wave 0 complete.

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
| CPU-01 | All legal base/CB semantics, flags, addresses, timed accesses, illegal lockup | Owned unit/regression plus admitted source-qualified CPU fixture | `ctest --preset phase1 --output-on-failure --no-tests=error -R '^(cpu_|mooneye_required_suite$)'` | Verified; focused base semantic cases 5/5, full inventory 104/104, exact hosted gates pass |
| CPU-02 | Interrupt entry, delayed EI, HALT/bug, STOP/wake, reset/post-boot | Owned timed sequence tests and applicable source-qualified cases | `ctest --preset phase1 --output-on-failure --no-tests=error -R '^(interrupt_|halt_|stop_|reset_|event_(stop_wake|boundary)$)'` | Verified; EI/interrupt ordering, HALT, STOP and reset cases included in full inventory |
| CPU-03 | Supported memory map, timer falling edges/reload races, disconnected serial | Owned bus/device cases and admitted Mooneye timer cases | `ctest --preset phase1 --output-on-failure --no-tests=error -R '^(bus_|timer_|serial_|event_external_serial_edges$|mooneye_required_suite$)'`; `cmake -DGBB_MOONEYE_DIR=fixtures/mooneye -P cmake/VerifyMooneye.cmake` | Verified; fixed corpus has one CPU and two timer cases |
| CPU-04 | Equal actual elapsed time/input partitions, no overshoot, bounded stopped/output outcomes | Metamorphic and API boundary tests | `ctest --preset phase1 --output-on-failure --no-tests=error -R '^(bus_preflight$|cpu_(call_stack|conditional_budget)$|interrupt_|halt_|stop_|reset_|timer_|serial_|event_|run_output_capacity$|diagnostics_)'`; `bash tests/scripts/verify-phase2-installed.sh` | Verified; relocated inventory passed 109/109 including C/C++ consumers |
| CPU-05 | Pinned offline fixtures, explicit statuses, denominator and bounded replay receipts | Runner integration, manifest/digest checks and fail-closed controls | `ctest --preset phase1 --output-on-failure --no-tests=error -R '^(mooneye_|fixture_|runner_)'`; `bash tests/scripts/verify-phase2-hosted.sh` | Verified; exact-SHA hosted CI and fixture reproduction pass |

## Per-Task Verification Map

Commands below use `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error -R '<selection>'` unless a complete command is printed. All named cases are registered; the final inventory and exact-revision hosted evidence are current. Plans 02-13 and 02-15 document diagnosis/halt decisions whose reproduction precondition was later closed by 02-17; their intermediate failed comparison is not represented as a pass.

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
| 02-07-T1 | 07 | 7 | CPU-01,05 | T-02-14,15,SC | Pinned WLA CPU ROM, digest, real guest | `cmake -DGBB_MOONEYE_DIR=fixtures/mooneye -P cmake/VerifyMooneye.cmake` and finite runner outcome | `fixtures/mooneye/daa.gb` and verifier created T1 | pass; final source-qualified DAA runner case passes |
| 02-07-T2 | 07 | 7 | CPU-03,05 | T-02-14,15,SC | Nonzero CPU/timer eligible set and digests | `cmake -DGBB_MOONEYE_DIR=fixtures/mooneye -P cmake/VerifyMooneye.cmake` | timer ROMs created T2 | pass; final verifier confirms one CPU and two timer cases |
| 02-07-T3 | 07 | 7 | CPU-05 | T-02-14,15 | Offline corpus inventory CTest registration | `^mooneye_(fixture_digest\|eligible_inventory)$` | CTest/inventory created T3 | pass |
| 02-08-T1 | 08 | 8 | CPU-04,05 | T-02-17,18 | Direct diagnostic zero/exact/short/null/canary and repeatable ROM receipt | `^diagnostics_(zero\|exact\|short\|null\|canary)$` plus two-run Python receipt command in plan | `tests/test_diagnostics.c` created and registered T1; runner controls T2 | pass; diagnostics and deterministic final receipts pass |
| 02-08-T2 | 08 | 8 | CPU-05 | T-02-16,17 | Four status controls; fail-closed suite | `^(runner_(pass\|fail\|timeout\|unsupported\|missing_fixture\|bad_manifest\|zero_eligible)\|mooneye_required_suite)$` | runner tests extended T2 | pass; required corpus and negative controls pass |
| 02-09-T1 | 09 | 9 | CPU-04,05 | T-02-19 | Fresh prefix-present/absent inventory and relocated C/C++ API contract | `bash tests/scripts/verify-phase2-installed.sh` | helper, consumers, CTest registration and `cmake/ExpectedTests.cmake` revised T1 | pass; relocated installed inventory 109/109 |
| 02-09-T2 | 09 | 9 | CPU-01..05 | T-02-20 | Full noninstalled JUnit at `build/phase2-ctest.xml`, exact core-only and relocated inventories | full command in 02-09-T2 | CI/inventory revised T2; helper from T1 | pass; final core inventory 104/104, exact inventory has no skips |
| 02-10-T1 | 10 | 10 | CPU-01,02,04 | — | Checksum-selected bootless F on load/reset and failed-load atomicity | `ctest --preset phase1 --output-on-failure --no-tests=error -R '^(reset_(profile\|header_flags)$\|loader_non_destructive$)'` | `tests/test_control.c`, CTest and expected inventory | pass; in final 104-case run |
| 02-10-T2 | 10 | 10 | CPU-01,02,04 | — | RET/RETI and conditional RET timed stack phases | `ctest --preset phase1 --output-on-failure --no-tests=error -R '^cpu_(return_phases\|call_stack\|conditional_budget)$'` | `tests/test_cpu.c`, CTest and expected inventory | pass; in final 104-case run |
| 02-11-T1 | 11 | 11 | CPU-02,03,04 | — | Consecutive EI, EI/DI and split-call vector behavior | `ctest --preset phase1 --output-on-failure --no-tests=error -R '^interrupt_(ei_chain\|ei_delay\|entry)$'` | `tests/test_control.c`, CTest and expected inventory | pass; in final 104-case run |
| 02-11-T2 | 11 | 11 | CPU-02,03,04 | — | Device deadline versus interrupt IF/stack diagnostic ordering | `ctest --preset phase1 --output-on-failure --no-tests=error -R '^(interrupt_(diagnostic_order\|entry\|budget)$\|timer_mid_instruction$)'` | `tests/test_control.c`, CTest and expected inventory | pass; in final 104-case run |
| 02-12-T1 | 12 | 12 | CPU-05 | T-02-23 | Exact Windows checkout/copy bytes versus Git manifest blob | `bash tests/scripts/inspect-windows-manifest.sh` | workflow capture and inspection script | pass; exact-head Windows capture confirms byte identity |
| 02-12-T2 | 12 | 12 | CPU-05 | T-02-23 | Strict manifest policy and distinct missing/digest/metadata failure outcomes | `ctest --preset phase1 --output-on-failure --no-tests=error -R '^runner_(missing_fixture\|bad_digest\|bad_manifest\|bad_metadata)$'` | runner negative controls and hosted Windows lane | pass; all four controls pass in hosted evidence |
| 02-13-T1 | 13 | 13 | CPU-05 | T-02-14 | Diagnose per-byte fixture reproduction mismatch | `bash tests/scripts/reproduce-mooneye.sh --diagnose fixtures/mooneye` | reproduction script and retained mismatch evidence | pass as diagnostic; identified linker tie ordering |
| 02-13-T2 | 13 | 13 | CPU-05 | T-02-14 | Compare reproduced fixture bytes and report divergence | `bash tests/scripts/reproduce-mooneye.sh --compare fixtures/mooneye` | initial difference retained; deterministic recipe closed by 02-17 | superseded; final candidate identity passes 02-17 and 02-18 evidence |
| 02-14-T1 | 14 | 14 | CPU-01,03,05 | T-02-24 | Audit immutable source, rights, and assertion/reporting path | `test -s fixtures/mooneye/ELIGIBILITY.md` plus source/protocol checks | eligibility, source and rights records | pass; source and rights closure verified for admitted derivatives |
| 02-14-T2 | 14 | 14 | CPU-01,03,05 | T-02-24 | Probe candidate callback, result PC, and PPU independence | `bash tests/scripts/probe-mooneye-candidate.sh` | candidate probe and unchanged upstream assertions | pass; positive and negative protocol probes pass |
| 02-15-T1 | 15 | 15 | CPU-01,03,05 | T-02-25 | Rebuild and compare qualified fixture bytes | `bash tests/scripts/reproduce-mooneye.sh --compare fixtures/mooneye` | plan halted at deterministic-byte precondition | superseded; 02-17 qualifies all three candidate byte streams |
| 02-15-T2 | 15 | 15 | CPU-01,03,05 | T-02-25 | Verify strict manifest and reproduced bytes | verifier plus reproduction compare | final fixture admission completed through isolated 02-17 gate | superseded; strict verifier and hosted fixture run pass |
| 02-16-T1 | 16 | 16 | CPU-01..05 | T-02-26 | Strict callback/result-PC runner protocol and induced guest failure | `ctest --preset phase1 --output-on-failure --no-tests=error -R '^(mooneye_|runner_)'` | runner implementation, tests and exact inventory | pass; all corpus and negative-control tests pass |
| 02-16-T2 | 16 | 16 | CPU-01..05 | T-02-26 | Exact-PR-SHA CI and fixture-reproduction gate | `bash tests/scripts/verify-phase2-hosted.sh` | hosted gate and explicit phase contexts | pass at final implementation SHA `cf28e90270be24d9528bfa8a1e4055a2b8485989` |
| 02-17-T1 | 17 | 17 | CPU-05 | — | Capture original baseline and repeat deterministic WLA-DX candidates | `bash tests/scripts/reproduce-mooneye.sh --capture-baseline fixtures/mooneye` and `--candidate-repeat-check` | candidate digest lock and immutable baseline | pass; repeated candidate byte arrays identical |
| 02-17-T2 | 17 | 17 | CPU-05 | — | Compare candidate bytes across local and hosted Linux | hosted candidate verifier in verify-only mode | exact push artifact and candidate digest lock | pass; run 37561292904 matched all three candidate digests |
| 02-17-T3 | 17 | 17 | CPU-01,03,05 | — | Gate admission, rollback, rights and strict denominator | candidate admission/rollback scripts plus `cmake -DGBB_MOONEYE_DIR=fixtures/mooneye -P cmake/VerifyMooneye.cmake` | final manifest and source/rights records | pass; one CPU and two timer fixtures admitted |
| 02-18-T1 | 18 | 18 | CPU-01 | T-02-31 | Independent arithmetic state/flag/PC/time semantic tracer | `ctest --preset phase1 --output-on-failure --no-tests=error -R '^cpu_base_semantic_tracer$'` | `tests/test_cpu.c`, CTest and expected inventory | pass; focused and full inventory executed |
| 02-18-T2 | 18 | 18 | CPU-01 | T-02-31..33 | Legal base opcodes, branch/address variants and timed bus effects | `ctest --preset phase1 --output-on-failure --no-tests=error -R '^cpu_base_(matrix\|conditional_paths\|arithmetic_edges\|address_effects\|semantic_tracer)$'` plus full, installed and hosted gates | `tests/test_cpu.c`, `tests/CMakeLists.txt`, `tests/expected-tests.txt` | pass; focused 5/5, local 104/104, installed 109/109, exact hosted gates pass |

## Wave 0 Requirements

- [x] Close CPU timing/startup coverage: RET/RETI phases and ROM-dependent post-boot flags are asserted.
- [x] Close interrupt coverage: consecutive EI and device deadlines inside interrupt diagnostics are asserted.
- [x] Register bus/timer/serial cases and guard output/event bounds, including corrected unsupported-read and wrap regressions.
- [x] Review and prepare individually eligible Mooneye fixture bytes, include/asset rights including font, WLA-DX builder pin, digests, boot/profile/protocol and finite tick budgets. The fixed set has one CPU and two timer cases independent of emulator result.
- [x] Register diagnostics zero/exact/short/null/canary and runner protocol, receipt, missing-fixture and malformed-manifest controls.
- [x] Extend the required inventory and absent-prefix filter, reject failed/error reports, and preserve relocated C/C++ checks.

No remaining Nyquist gaps. Independent verification is recorded in [02-VERIFICATION.md](02-VERIFICATION.md). Ordinary build/tests remain offline and use checked-in bytes; fixture reproduction is an explicit maintainer/CI action.

## Manual-Only Verifications

No routine manual UAT is required. Automated cases qualify the declared corpus and deterministic bootless profile. Fresh physical DMG-CPU-B observation is unavailable here; upstream hardware-author evidence and owned regression/metamorphic checks must be labeled separately. Cartridge reads without a responding device are documented as undefined (Gekkio revision 192 §12.1); a fixed-byte electrical model is not qualified. Deferred PPU, DMA, JOYP, audio and CGB behavior are excluded.

## Validation Sign-Off

- [x] All tasks have automated verification or an earlier test-creation dependency.
- [x] No three consecutive tasks lack automated verification.
- [x] All missing files/test registrations have explicit ownership and ordering.
- [x] No watch-mode flags or zero-case successful selections.
- [x] Per-task map and security threat references match final plans.
- [x] `nyquist_compliant` and `wave_0_complete` are true after automated correctness/applicability gates passed.

Planning review passed on 2026-10-06: nine plans, 19 tasks, five requirements and 12 context decisions. The earlier independent execution result was `gaps_found`; final re-verification is passed 5/5. For 02-09 reports, pass a basename to CTest's preset/test-dir invocation and verify it beneath the selected test directory; clear the installed prefix for core-only inventory. A temporary one-test CTest probe reproduced this report-path behavior; it is tooling evidence, not emulator validation.

## Historical fallback assumptions — superseded by later plans

At the time of the earlier validation audit, the specless CPU-01 adjacency, empty-budget and ordering probes mapped to `cpu_conditional_budget`, `event_boundary` and `event_queue_order`; CPU-02 control-state probes mapped to `interrupt_ei_delay`, `halt_idle`, `stop_wait` and `event_stop_wake`; CPU-03 bus/timer probes mapped to `bus_absent_cart`, `timer_tima_collision` and `timer_tma_collision`; CPU-04 partition/output probes mapped to `event_partition`, `run_output_capacity` and direct diagnostic bounds; CPU-05 corpus/rights/protocol probes mapped to source/asset closure and `mooneye_required_suite`. The initial review also found missing consecutive-EI and timed return/interrupt ordering coverage. Those historical gaps were subsequently closed by Plans 02-10 through 02-18 and are resolved in the final audit below.

## Historical execution audit — 2026-10-06 (superseded)

At source revision `c583e33`, fresh offline Linux normal and ASan/UBSan builds each executed 94 cases: 90 passed and four failed, with no skips. Failures are `mooneye_required_suite`, `mooneye_case_daa`, `mooneye_case_tim00`, and `mooneye_case_tim00-div-trigger`. No sanitizer finding was reported; the sanitizer suite is nevertheless failing. The exact inventory checker rejects failed reports rather than presenting execution counts as success.

At that historical revision the three fixed required ROMs reached LY (`FF44`) through their common reporting path before the declared `LD B,B` completion protocol. PPU/LY is outside this phase. Earlier 3/3 pass claims depended on fabricated unsupported-address reads and were superseded. Fixture digests and source reproduction remained valid while runtime qualification did not; CPU-05 was then PARTIAL with an automated failing gate. Later source-qualified derived reporting closures and exact reproduction resolve the declared headless corpus requirement while the original ROM reporting paths remain excluded.

Corrective regressions later covered all read addressing families, CB/stack/fetch rejection without mutation, 16-bit address/stack wrap, and timer-driven HALT wake under partitions. CMake script-mode policy setup and failed/error JUnit rejection were corrected and verified with negative controls. These checks were subsequently included in the completed phase inventories.

No routine human UAT is required. At that revision the corpus issue was a source/implementation qualification gap; later source and protocol evidence resolved the admitted derived corpus. Hosted exact-SHA qualification was pending then and passed in the final audit. Physical hardware remains unavailable, so Phase 3 stayed paused at this handoff.

## Historical validation audit — 2026-10-06 (superseded)

| Metric | Count |
|---|---|
| Gaps found | 7 |
| Resolved | 0 |
| Escalated | 7 |

Independent code review added four core gaps: startup F, RET/RETI stack phases, consecutive EI, and interrupt diagnostic ordering. The initial corpus gap plus these four and the subsequent Windows manifest/reproduction failures are the seven distinct entries recorded at that time. Named per-task passes then did not establish the uncovered behaviors; later gap plans closed them, and current CPU requirement status is recorded in the final audit.

Hosted qualification at PR head `a91d8e7` is failing: Linux/macOS native 95/99, ASan/UBSan and CMake floor 90/94, Windows 93/99. Windows reports invalid-manifest for two negative controls; the Mooneye reproduction job reports different DAA bytes. Earlier local reproduction does not establish cross-host reproduction. See [hosted evidence](02-HOSTED-EVIDENCE.md); both causes remain unresolved.

## Final Nyquist audit — 2026-10-07

| Metric | Count |
|---|---:|
| Distinct gaps found across the 2026-10-06 audit and the later D-01 review | 8 |
| Resolved with automated evidence | 8 |
| Escalated | 0 |
| Current gaps | 0 |

The seven gaps in the historical audit closed through Plans 02-10 to 02-17: four CPU/control-state findings (startup flags, return phases, consecutive EI, and interrupt diagnostic ordering), the Windows manifest-byte issue, the fixture applicability/reproduction issue, and exact runner/hosted qualification. The independent verifier then identified D-01 as an eighth gap. Plan 02-18 added fixed expected semantic state for every documented legal base opcode, conditional branch paths, address effects, arithmetic boundaries, and representative timed bus accesses. Eleven unused opcodes remain distinct persistent lockup cases.

Current run evidence: focused base semantic selection passed 5/5; a fresh local CTest run passed 104/104 and the core inventory checker reported no skips. The current phase verification records 109/109 relocated installed checks, exact hosted CI run [37620710587](https://github.com/szTheory/gabbaboy/actions/runs/37620710587), and exact fixture-reproduction run [37620710600](https://github.com/szTheory/gabbaboy/actions/runs/37620710600) for implementation SHA `cf28e90270be24d9528bfa8a1e4055a2b8485989`. Independent phase verification is passed 5/5 with zero behavior unverified in [02-VERIFICATION.md](02-VERIFICATION.md).

No additional test file was needed: the only gap identified in this audit, CPU-01/D-01, is covered by the registered 02-18 tests. No implementation bug is escalated. Physical DMG-CPU-B observation remains unavailable and is recorded as a hardware evidence limitation, not an automated coverage gap or manual UAT requirement. The original upstream Mooneye ROMs remain PPU/LY-limited; the passing fixed corpus uses source-qualified derived reporting closures and does not claim original-ROM PPU behavior or hardware qualification.

## Validation refresh after Phase 06.1 — 2026-10-10

Covered-input drift since the 2026-10-10 report is limited to `.github/workflows/ci.yml`, changed by Phase 06.1 PR #54 (squash `ab76d09c2ee27ba09fc5f3c2510af016aebfdecb`, exact tested head `2a8fd1c357262d4b69707b553c603fd441a0f3fa`). The `pull_request` player-gating condition now lives in one `player-gate` job, and `required-native` checks its `player_required` output through `.github/scripts/check-player-result.sh` (14-case `--self-test`, run in `native-linux-x64`). The Phase 2 test-inventory jobs (`native-linux`, `native-macos`, `native-windows`, `linux-sanitizers`) still run `ctest --no-tests=error` and `verify-test-inventory.sh` against `tests/expected-tests.txt`, so CPU-01..CPU-05 coverage is unchanged.

Evidence on the refresh branch (descends from the merge SHA, no source change since): the phase-1 preset suite, which includes every Phase 2 CPU/timer case, passed 184/184 locally; `check-player-result.sh --self-test` printed `PASS: player result self-test (14 cases)`. Hosted: PR-head ci run [38064419789](https://github.com/szTheory/gabbaboy/actions/runs/38064419789) succeeded on all jobs, and main-push ci run [38064726000](https://github.com/szTheory/gabbaboy/actions/runs/38064726000) on the merge SHA succeeded (`macos-player-package` skipped, as designed for push). No new gaps; no test files were added.

## Validation Audit 2026-10-09

| Metric | Count |
|---|---|
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |
