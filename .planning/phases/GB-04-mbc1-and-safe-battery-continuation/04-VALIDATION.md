---
phase: "GB-04"
slug: "mbc1-and-safe-battery-continuation"
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-10-08"
---

# Phase GB-04 — Validation Strategy

This is the planning-stage validation contract. Every result below remains pending until the named task creates its test and the command runs against that revision. A prior phase's green result is not Phase 4 evidence.

## Test Infrastructure

| Property | Value |
|---|---|
| Framework | Existing C17 CTest binaries, strict `tests/expected-tests.txt` and optional `tests/player/expected-tests.txt` inventories |
| Core configure/build | `cmake --preset phase1 && cmake --build --preset phase1` |
| Core full suite | `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error` |
| Optional macOS player and extracted package | `bash tests/scripts/verify-phase3-player.sh` |
| Relocated installed consumers | `bash tests/scripts/verify-phase2-installed.sh` |
| Original fixture reproduction | `bash tests/scripts/reproduce-mbc1-continuation.sh` after Task 04-05-01 creates it; RGBDS 1.0.1 is required only for this separate reproduction path |
| Sanitizer lane | `cmake --preset phase1-asan && cmake --build --preset phase1-asan && ctest --preset phase1-asan --output-on-failure --no-tests=error` on existing Linux ASan/UBSan CI |
| Runtime | Measure focused and full elapsed time on first execution; no unmeasured estimate is treated as a gate |

## Sampling Rate and Failure Direction

- **After every task:** Run its exact `<verify><automated>` command below before its task commit; `--no-tests=error` and explicit inventory make empty selection, missing required cases, failed cases, timeouts and unexpected skips fail.
- **After each wave:** Run the full offline core suite. Run the optional player verifier after any player, fixture, or package wave (01, 03–06) on macOS; preserve the exact source revision in its receipt.
- **Before phase verification:** Run full core, optional macOS player/package, relocated installed C/C++, fixture reproduction and Linux ASan/UBSan inventories, then inspect exact-head hosted CI and preview artifact receipts for that tested revision. Do not promote a local pass, old SHA, skipped job or unavailable credential to a hosted green claim.
- **Fast feedback target:** Keep focused core selections under 60 seconds where practical; the SDL download/package, RGBDS reproduction and relocated install lanes are separate slower gates. Record actual wall times and investigate regressions instead of assuming a fixed duration.
- **Failure direction:** Stop the task on any red command, preserve minimized failure inputs, keep the failed save/ROM and previous good state where relevant, fix the source or expectation from independent evidence, then rerun the same command. Never update a golden to match a defect or remove a named case to make the inventory pass.

## Per-Task Verification Map

| Task | Wave | Requirement | Threat Ref | Secure behavior and failure signal | Automated command | Test file / gate | Status |
|---|---:|---|---|---|---|---|---|
| 04-01-01 tracer | 1 | SAVE-01/02/03 | T-04-01/02 | Fails when configure/build or selected loader/bus/lifecycle exits nonzero, the selection is empty, or player smoke child cannot reload the guest byte | `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error -R '^(loader_|bus_|instance_lifecycle$)' && bash tests/scripts/verify-phase3-player.sh` | existing loader/bus tests; player `--smoke` extension planned | pending |
| 04-01-02 cartridge tracer | 1 | SAVE-01/02 | T-04-01/04 | Fails when `cartridge_tracer` is absent/nonzero or guest byte, disabled read or transfer differs | `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error -R '^cartridge_tracer$'` | `tests/test_cartridge.c` planned and required inventory | pending |
| 04-02-01 matrix | 2 | SAVE-01 | T-04-03 | Fails when selection is empty/nonzero, bank/mode mismatches, excluded header passes, or replacement mutates prior state | `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error -R '^(cartridge_|loader_|bus_)'` | `tests/test_cartridge.c`, `tests/test_loader.c` | pending |
| 04-02-02 battery API | 2 | SAVE-02 | T-04-04 | Fails when battery case is absent/nonzero or 8/32 KiB, canary, no-battery, reset/replacement or instance result differs | `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error -R '^(battery_|instance_lifecycle$|independent_instances$|reset_)'` | `tests/test_battery.c` planned and required inventory | pending |
| 04-03-01 envelope | 3 | SAVE-03 | T-04-05/07 | Fails when player verifier is nonzero or identity/version/checksum/length/special-file reject and recovery preservation differ | `bash tests/scripts/verify-phase3-player.sh` | `tests/player/test_session.c` and optional inventory | pending |
| 04-03-02 atomic write | 3 | SAVE-03 | T-04-06 | Fails when player verifier is nonzero or injected write/sync/rename/recovery/interruption exposes changed old target or partial target | `bash tests/scripts/verify-phase3-player.sh` | `tests/player/test_session.c` fault-stage cases | pending |
| 04-04-01 lock | 4 | SAVE-03 | T-04-08 | Fails when player verifier is nonzero, second writer succeeds under lock, post-release writer fails or no-battery save appears | `bash tests/scripts/verify-phase3-player.sh` | `tests/player/test_session.c` two-process and injected lock cases | pending |
| 04-04-02 cadence/UX | 4 | SAVE-03 | T-04-09 | Fails when player verifier is nonzero, unchanged store saves, dirty age exceeds 10s, or final transition silently loses progress | `bash tests/scripts/verify-phase3-player.sh` | `tests/player/test_session.c` and player smoke | pending |
| 04-05-01 authored fixture | 5 | SAVE-04 | T-04-11 | Fails when RGBDS tool/notice/source is missing or wrong, digest changes or reproduced bytes differ | `bash tests/scripts/reproduce-mbc1-continuation.sh` | fixture manifest and reproduction script planned | pending |
| 04-05-02 continuation | 5 | SAVE-04 | T-04-10 | Fails when player case is missing/nonzero, fresh-process success absent, distinct MISSING_SAVE_EMPTY/WRONG_ROM_IDENTITY_REJECTED markers collapse, or corruption reaches success | `bash tests/scripts/verify-phase3-player.sh` | `tests/player/test_continuation.c`, player inventory, core fixture digest | pending |
| 04-06-01 consumers/fuzz | 6 | SAVE-02/03 | T-04-12/13 | Fails when battery selection is empty/nonzero, fuzz/sanitizer assertion fires or relocated C/C++ consumer cannot compile/link/run | `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error -R '^battery_' && bash tests/scripts/verify-phase2-installed.sh` | `tests/test_battery_fuzz.c`, installed consumers | pending |
| 04-06-02 CI/package | 6 | SAVE-03/04 | T-04-12/13 | Fails when full inventory is missing/skipped/nonzero, player/package source receipt fails, or reproduction digest differs | `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error && bash tests/scripts/verify-phase3-player.sh && bash tests/scripts/reproduce-mbc1-continuation.sh` | three workflows, package verifier and inventory | pending |
| 04-07-01 public contract | 7 | SAVE-01/02/03/04 | T-04-14/15 | Fails when suite nonzero, tracked whitespace bad, new guide missing/empty, or no-index whitespace status is not clean-diff 1 | `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error && git diff HEAD --check -- README.md docs/preview.md docs/cartridge-and-saves.md && test -s docs/cartridge-and-saves.md && sh -c 'git diff --no-index --check /dev/null "$1"; rc=$?; test "$rc" -eq 1' _ docs/cartridge-and-saves.md` | public docs planned; staged-free pre-commit check | pending |
| 04-07-02 evidence | 7 | SAVE-01/02/03/04 | T-04-14/15 | Fails when core/installed/player nonzero, new ledger missing/empty, tracked whitespace bad, or either no-index whitespace status is not clean-diff 1 | `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error && bash tests/scripts/verify-phase2-installed.sh && bash tests/scripts/verify-phase3-player.sh && git diff HEAD --check -- docs/mbc1-evidence.md .planning/phases/GB-04-mbc1-and-safe-battery-continuation/04-VALIDATION.md && test -s docs/mbc1-evidence.md && sh -c 'git diff --no-index --check /dev/null "$1"; rc=$?; test "$rc" -eq 1' _ docs/mbc1-evidence.md && sh -c 'git diff --no-index --check /dev/null "$1"; rc=$?; test "$rc" -eq 1' _ .planning/phases/GB-04-mbc1-and-safe-battery-continuation/04-VALIDATION.md` | evidence ledger planned; this matrix updated with executed results | pending |

All 14 tasks have a runnable automated verification path and matching task-local `<fails_when>`. At the pre-commit point, `git diff HEAD --check` sees staged and unstaged tracked changes. `test -s` requires each new guide/ledger, and the staging-free `git diff --no-index --check` wrapper accepts only the observed clean-diff exit 1 while rejecting whitespace-error exit 3.

The repeated `T-04-SC` supply-chain row is accepted because these plans introduce no npm/pip/cargo installation. Existing pinned SDL3 and RGBDS acquisition paths retain their digest and version checks in the player and fixture lanes above; any later new package would require a separate legitimacy audit.

## Required Inventory, Fixture and Hosted Gates

1. Register every new core case in `tests/expected-tests.txt` and every optional `player_*` case in `tests/player/expected-tests.txt`; `tests/CMakeLists.txt`, `tests/player/CMakeLists.txt`, and CI enforce exact nonempty registration. No test is counted merely because a source file exists.
2. Keep checked-in original fixture bytes and manifest digest available offline. In the separate RGBDS 1.0.1 reproduction lane, rebuild and byte-compare them; a missing assembler/tool pin, rights notice, digest or byte comparison is red.
3. Linux ASan/UBSan runs the bounded battery/API fuzz and full required core inventory; hosted native lanes execute relocated C/C++ battery consumers. Optional macOS player lane executes fault, lock, continuation and package smoke. Downloaded package verification checks the exact artifact bytes and source revision.
4. The protected required aggregate must reflect current eligible pull-request head and all intended lanes. `workflow_dispatch` or old successful runs cannot substitute for the protected PR result. Record current run IDs, SHA, test counts, package digest and access failures during execution.

## Wave 0 Requirements

Existing CTest, strict inventories, sanitizer preset, SDL player verifier and fixture-reproduction conventions provide the infrastructure. The leading tracer task adds its named smoke path and the next task registers `cartridge_tracer`; no separate foundation-only Wave 0 task is needed. `wave_0_complete` remains false until those tests exist and run.

## Evidence Boundaries and Manual-Only Verification

Mapper expectations from Pan Docs/Gekkio plus source cross-checks are documented or inferred software-model evidence. Synthetic bank patterns, original guest continuation, process interruption and emulator differential comparisons are separate classes. No identified physical DMG-CPU-B/MBC1 observation exists; this phase must make no physical hardware or storage power-loss qualification claim. All scoped software acceptance is automated. If hosted credentials or a real desktop/hardware observation are unavailable, record that limitation without converting it to a passing case or inventing manual UAT.

## Validation Sign-Off

- [x] Planning matrix covers all 14 tasks and SAVE-01 through SAVE-04.
- [x] Every task has `<automated>` verify and a named failing direction.
- [x] Required inventory, original fixture reproduction, exact-head CI/consumer and threat validations are mapped.
- [ ] Focused tests and full suites executed at their planned revisions.
- [ ] Hosted exact-head and downloaded artifact evidence inspected.
- [ ] `nyquist_compliant: true` set only after execution supports it.

**Approval:** pending execution evidence.
