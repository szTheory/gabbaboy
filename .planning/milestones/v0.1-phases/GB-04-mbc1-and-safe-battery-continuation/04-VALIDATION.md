---
phase: "GB-04"
slug: "mbc1-and-safe-battery-continuation"
status: validated
nyquist_compliant: true
wave_0_complete: true
created: "2026-10-08"
---

# Phase GB-04 — Validation Strategy

This validation contract began as a plan. Its task rows now record executed local evidence, and the final exact-head hosted checks and package receipts are recorded below. A prior phase's green result is not Phase 4 evidence.

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
| 04-01-01 tracer | 1 | SAVE-01/02/03 | T-04-01/02 | Fails when configure/build or selected loader/bus/lifecycle exits nonzero, the selection is empty, or player smoke child cannot reload the guest byte | `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error -R '^(loader_|bus_|instance_lifecycle$)' && bash tests/scripts/verify-phase3-player.sh` | existing loader/bus tests; player `--smoke` extension planned | pass |
| 04-01-02 cartridge tracer | 1 | SAVE-01/02 | T-04-01/04 | Fails when `cartridge_tracer` is absent/nonzero or guest byte, disabled read or transfer differs | `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error -R '^cartridge_tracer$'` | `tests/test_cartridge.c` planned and required inventory | pass |
| 04-02-01 matrix | 2 | SAVE-01 | T-04-03 | Fails when selection is empty/nonzero, bank/mode mismatches, excluded header passes, or replacement mutates prior state | `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error -R '^(cartridge_|loader_|bus_)'` | `tests/test_cartridge.c`, `tests/test_loader.c` | pass |
| 04-02-02 battery API | 2 | SAVE-02 | T-04-04 | Fails when battery case is absent/nonzero or 8/32 KiB, canary, no-battery, reset/replacement or instance result differs | `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error -R '^(battery_|instance_lifecycle$|independent_instances$|reset_)'` | `tests/test_battery.c` planned and required inventory | pass |
| 04-03-01 envelope | 3 | SAVE-03 | T-04-05/07 | Fails when player verifier is nonzero or identity/version/checksum/length/special-file reject and recovery preservation differ | `bash tests/scripts/verify-phase3-player.sh` | `tests/player/test_session.c` and optional inventory | pass |
| 04-03-02 atomic write | 3 | SAVE-03 | T-04-06 | Fails when player verifier is nonzero or injected write/sync/rename/recovery/interruption exposes changed old target or partial target | `bash tests/scripts/verify-phase3-player.sh` | `tests/player/test_session.c` fault-stage cases | pass |
| 04-04-01 lock | 4 | SAVE-03 | T-04-08 | Fails when player verifier is nonzero, second writer succeeds under lock, post-release writer fails or no-battery save appears | `bash tests/scripts/verify-phase3-player.sh` | `tests/player/test_session.c` two-process and injected lock cases | pass |
| 04-04-02 cadence/UX | 4 | SAVE-03 | T-04-09 | Fails when player verifier is nonzero, unchanged store saves, dirty age exceeds 10s, or final transition silently loses progress | `bash tests/scripts/verify-phase3-player.sh` | `tests/player/test_session.c` and player smoke | pass |
| 04-05-01 authored fixture | 5 | SAVE-04 | T-04-11 | Fails when RGBDS tool/notice/source is missing or wrong, digest changes or reproduced bytes differ | `bash tests/scripts/reproduce-mbc1-continuation.sh` | fixture manifest, path-specific Windows text/binary attributes, and reproduction script | pass |
| 04-05-02 continuation | 5 | SAVE-04 | T-04-10 | Fails when player case is missing/nonzero, fresh-process success absent, distinct MISSING_SAVE_EMPTY/WRONG_ROM_IDENTITY_REJECTED markers collapse, or corruption reaches success | `bash tests/scripts/verify-phase3-player.sh` | `tests/player/test_continuation.c`, player inventory, core fixture digest | pass |
| 04-06-01 consumers/fuzz | 6 | SAVE-02/03 | T-04-12/13 | Fails when battery selection is empty/nonzero, fuzz/sanitizer assertion fires or relocated C/C++ consumer cannot compile/link/run | `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error -R '^battery_' && bash tests/scripts/verify-phase2-installed.sh` | `tests/test_battery_fuzz.c`, installed consumers | pass |
| 04-06-02 CI/package | 6 | SAVE-03/04 | T-04-12/13 | Fails when full inventory is missing/skipped/nonzero, player/package source receipt fails, or reproduction digest differs | `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error && bash tests/scripts/verify-phase3-player.sh && bash tests/scripts/reproduce-mbc1-continuation.sh` | three workflows, package verifier and inventory | pass |
| 04-07-01 public contract | 7 | SAVE-01/02/03/04 | T-04-14/15 | Fails when suite nonzero, tracked whitespace bad, new guide missing/empty, or no-index whitespace status is not clean-diff 1 | `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error && git diff HEAD --check -- README.md docs/preview.md docs/cartridge-and-saves.md && test -s docs/cartridge-and-saves.md && sh -c 'git diff --no-index --check /dev/null "$1"; rc=$?; test "$rc" -eq 1' _ docs/cartridge-and-saves.md` | public docs planned; staged-free pre-commit check | pass |
| 04-07-02 evidence | 7 | SAVE-01/02/03/04 | T-04-14/15 | Fails when core/installed/player nonzero, new ledger missing/empty, tracked whitespace bad, or either no-index whitespace status is not clean-diff 1 | `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error && bash tests/scripts/verify-phase2-installed.sh && bash tests/scripts/verify-phase3-player.sh && git diff HEAD --check -- docs/mbc1-evidence.md .planning/phases/GB-04-mbc1-and-safe-battery-continuation/04-VALIDATION.md && test -s docs/mbc1-evidence.md && sh -c 'git diff --no-index --check /dev/null "$1"; rc=$?; test "$rc" -eq 1' _ docs/mbc1-evidence.md && sh -c 'git diff --no-index --check /dev/null "$1"; rc=$?; test "$rc" -eq 1' _ .planning/phases/GB-04-mbc1-and-safe-battery-continuation/04-VALIDATION.md` | evidence ledger planned; this matrix updated with executed results | pass |

All 14 task rows have runnable automated verification paths, matching task-local `<fails_when>` clauses, and passing local results recorded from the plan summaries and final Phase 4 run. The exact hosted-revision gate is listed separately below. `git diff HEAD --check` sees tracked changes; the staging-free `git diff --no-index --check` wrappers accepted only the clean-diff exit 1 for new documentation.

The repeated `T-04-SC` supply-chain row is accepted because these plans introduce no npm/pip/cargo installation. Existing pinned SDL3 and RGBDS acquisition paths retain their digest and version checks in the player and fixture lanes above; any later new package would require a separate legitimacy audit.

## Executed Local Results

The final local software/package pass used implementation revision
`918ec265d1ab2a94292fe12c52a16563de8926b1`:

- Core CTest: **155/155** passed, including battery fuzz, mapper matrix, and
  continuation-fixture digest checks.
- Relocated install verifier: **160/160** installed tests passed, including
  external C and C++ consumers; its fresh core-only inventory passed
  **155/155** with no skips.
- macOS player and extracted-package verifier: **37/37** passed. The package
  reopened the MBC1 continuation fixture in a fresh process. Candidate package
  SHA-256: `dc2b8ebdeee56fb73a5d14bbfa5c2872ab2cfcbebd2180cd3740814fedded9d2`.
- The phase-boundary regression run rebuilt the core and passed **155/155**;
  the fresh macOS player/package rerun passed **37/37** and produced a verified
  extracted package with SHA-256
  `97af58d5b118c0cf26f45ed3d45401e0bb8a71b02a2c63269b20358f07eab3e4` at
  source `79f83f627ffb3631811b2f39b23081117ebaab8f`. In this sandbox, the
  first player smoke run could not create its synthetic lock file because
  SDL's macOS preference directory
  resolves through Foundation rather than the `HOME` environment variable.
  Redirecting `CFFIXED_USER_HOME` to an isolated `/private/tmp` directory made
  the complete player verifier pass; no product-code change was needed.
- The RGBDS 1.0.1 macOS archive SHA-256
  `2f6f13c6ec984313656c07b08d97dfcd3a471c7d3901d3ff486e5814bb503645`
  reproduced the source and checked-in ROM digests byte-for-byte.
- The public documentation passed tracked and no-index whitespace checks;
  `actionlint` passed for the updated preview workflow; a privacy scan found
  no home paths or personal identifiers in published docs.
- Linux ASan/UBSan was not run on this macOS host. It remains required on the
  hosted PR head. The install build showed the already-known
  unsequenced-access warning in `tests/test_dma.c:702`; this phase did not
  change that file.

After Windows CI exposed CRLF conversion of the authored assembly source,
`95c076d` added path-specific `.gitattributes` rules: text inputs check out
with LF, while the generated ROM remains byte-for-byte binary. A Windows-style
checkout with `core.autocrlf=true` retained the manifest's source and ROM
digests. The fixture/package verifier now reports both expected and actual
digests on mismatch. The corrected implementation passed the local core
inventory (155/155) and relocated package verifier (160/160 plus 155/155
core-only, no skips); exact hosted evidence below repeats these checks on the
current PR head.

At Phase 4 triage on 2026-10-08, authenticated GitHub queries found no
pre-existing open issues or pull requests. Phase 4 work and closeout are in
PR #8; its current exact-head evidence is recorded below.

## Required Inventory, Fixture and Hosted Gates

1. Register every new core case in `tests/expected-tests.txt` and every optional `player_*` case in `tests/player/expected-tests.txt`; `tests/CMakeLists.txt`, `tests/player/CMakeLists.txt`, and CI enforce exact nonempty registration. No test is counted merely because a source file exists.
2. Keep checked-in original fixture bytes and manifest digest available offline. In the separate RGBDS 1.0.1 reproduction lane, rebuild and byte-compare them; a missing assembler/tool pin, rights notice, digest or byte comparison is red.
3. Linux ASan/UBSan runs the bounded battery/API fuzz and full required core inventory; hosted native lanes execute relocated C/C++ battery consumers. Optional macOS player lane executes fault, lock, continuation and package smoke. Downloaded package verification checks the exact artifact bytes and source revision.
4. The protected required aggregate must reflect current eligible pull-request head and all intended lanes. `workflow_dispatch` or old successful runs cannot substitute for the protected PR result. Record current run IDs, SHA, test counts, package digest and access failures during execution.

## Wave 0 Requirements

Existing CTest, strict inventories, sanitizer preset, SDL player verifier and fixture-reproduction conventions provide the infrastructure. The leading tracer task added its named smoke path and the next task registered `cartridge_tracer`; no separate foundation-only Wave 0 task was needed. The fixture and all required inventories now execute locally.

## Evidence Boundaries and Manual-Only Verification

Mapper expectations from Pan Docs/Gekkio plus source cross-checks are documented or inferred software-model evidence. Synthetic bank patterns, original guest continuation, and process interruption are software evidence; no emulator differential is admitted as a passing Phase 4 result. No identified physical DMG-CPU-B/MBC1 observation exists; this phase must make no physical hardware or storage power-loss qualification claim. All scoped software acceptance is automated. Record any hosted access limitation without converting it to a passing case or inventing manual UAT.

## Hosted Exact-Head Status

PR #8's current exact head `79f83f627ffb3631811b2f39b23081117ebaab8f`
passed all Phase 4 hosted gates. It includes the merge of the already-merged
planning PR from `main`; the source and fixture fix under test are unchanged
from `95c076d`.

- `ci` pull-request run **37728192665** passed: `required-native`
  (113151357960), `native-linux-x64` (113151047504), `native-macos-arm64`
  (113151047562), `native-windows-x64` (113151047530), `linux-asan-ubsan`
  (113151047292), `cmake-floor-3.25.3` (113151047475), and
  `macos-player-package` (113151047510). Windows captured raw manifest bytes
  and passed the required installed inventory; no job was skipped.
- `fixture-repro` pull-request run **37728192634** passed `fixture-repro`
  (113151047353), `mooneye-original-repro` (113151047346), and
  `mooneye-candidate-repro` (113151046938), including byte reproduction of
  the MBC1 continuation fixture with pinned RGBDS 1.0.1.
- `preview-package-smoke` pull-request run **37728192674** passed the aggregate
  (113151467275), Linux installed consumer (113151047069), macOS installed
  consumer (113151047303), and downloaded macOS player consumer
  (113151047564). Each artifact receipt identifies the same source SHA.

Downloaded and locally re-hashed package bytes match the receipts:

| Package | Source SHA | Package SHA-256 | Receipt |
|---|---|---|---|
| Linux core preview | `79f83f627ffb3631811b2f39b23081117ebaab8f` | `74e893cdadd453dd13c981b7324448f824d53baad5388fa2217ed54743491ca2` | `smoke_result: passed` |
| macOS core preview | `79f83f627ffb3631811b2f39b23081117ebaab8f` | `5c5284633295504167ac689a5207fa3debba52e81f7231d18e01e64330efebf2` | `smoke_result: passed` |
| macOS player preview | `79f83f627ffb3631811b2f39b23081117ebaab8f` | `44fbac8b86eee0a1dc1565848a3febee2692e85edc117545a7d8d6d386a26d17` | `result: passed`; fresh-process MBC1 continuation |

The player receipt also records fixture source digest
`ad82e0cd51eeb6d536421d20c4a5b88ee0c019a4e699c2c75de077a20c82ba94`, ROM
digest `f89bf3884ff10a702aa117f2963e6fe9ea8aeac3a9bc003f52b6c5ca6abfbbd2`,
SDL 3.4.18 archive digest, and `hardware_qualified: false`, `signed: false`,
`notarized: false`. The package smoke drove SDL keyboard events into the demo,
produced a completed frame, and resumed battery progress in a fresh process.
No skipped, stale, canceled, unavailable, or manual-dispatch-only result was
used as passing evidence.

## Validation Sign-Off

- [x] Planning matrix covers all 14 tasks and SAVE-01 through SAVE-04.
- [x] Every task has `<automated>` verify and a named failing direction.
- [x] Required inventory, original fixture reproduction, exact-head CI/consumer and threat validations are mapped.
- [x] Focused and full local suites executed; counts are recorded below.
- [x] Prior-phase regression gate executed with the full core and macOS player
      test inventories; both passed with no skipped cases.
- [x] Every scoped software requirement has named automated coverage; no manual-only software acceptance remains.
- [x] Hosted exact-head and downloaded artifact evidence inspected and
      package bytes re-hashed against receipts.
- [x] `nyquist_compliant: true` is supported by the executed per-task coverage map.

**Approval:** local execution, Nyquist coverage, source review, threat gate,
exact-head hosted checks, and downloaded package receipts are validated.

## Validation Audit 2026-10-08

| Metric | Count |
|---|---|
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |

## Canonical Refresh Local Evidence 2026-10-09

The current working tree is based on source revision
`4d52df7aa0594bad2a3b0f0dc91e92e5612a2f4c` and contains a local player
hardening change plus its regression assertion. This is local evidence for the
working tree, not an exact hosted PR-head result:

- Core CTest: **179/179** passed with no skips.
- The macOS player and extracted-package verifier passed **50/50** player
  tests, including a FIFO ROM replacement case that now verifies prompt
  rejection and preservation of the active ROM/session. The package also
  passed dummy-audio, extracted-byte, and fresh-process MBC1 continuation
  checks. Candidate package SHA-256:
  `12cbb579ccd5a2c0f05fd33b7b534f81ff15bac788ef7605136d145d56368232`.
- The local package receipt identifies source revision
  `4d52df7aa0594bad2a3b0f0dc91e92e5612a2f4c` and `source_tree_state: dirty`;
  this is local evidence and is kept separate from the hosted result below.
- Code review identified that opening a user-selected FIFO could block before
  the regular-file check. `read_rom_file()` now uses `O_NONBLOCK` with
  `O_NOFOLLOW`, then retains its existing descriptor-based regular-file and
  size checks. The regression checks rejection, the FIFO's unchanged type, and
  that the active path and guest RAM remain unchanged.

The historical exact-hosted results above remain scoped to PR #8's tested
source revision. The local FIFO patch then passed PR #43's exact code head
`9b9d58a009b175256b09fe074e3f44e1aa0320e7` on 2026-10-09. CI run
37964888409 passed required-native, native Linux/macOS/Windows, Linux
ASan/UBSan, CMake 3.25.3 floor, and the macOS player package. Fixture run
37964888352 passed fixture-repro plus original and candidate Mooneye
reproduction. Preview package run 37964888373 passed Linux/macOS installed
consumer and macOS player-package smoke. All three runs were pull-request runs
for that exact code head; the separate push-event run with a skipped player job
was not used. No hardware or power-loss result is implied.

## Validation Refresh After Phase 06.1 — 2026-10-10

Covered-input drift since the 2026-10-09 report is limited to `src/player/session.c` and `tests/player/test_session.c`, both changed by Phase 06.1 PR #54 (squash `ab76d09c2ee27ba09fc5f3c2510af016aebfdecb`, exact tested head `2a8fd1c357262d4b69707b553c603fd441a0f3fa`):

- `read_rom_file` now also opens with `O_NOCTTY` and reports a size overrun and a `close()` failure in separate branches. `O_NONBLOCK`, `O_NOFOLLOW` and the descriptor-based regular-file and size checks that carry the SAVE-03 FIFO hardening are unchanged. `read_save_file` is unchanged.
- `player_session_replacement_failure` gains 2097153-byte and 2097154-byte replacement-failure assertions, each followed by the unchanged-session check. The existing `mkfifo` ROM-replacement assertion is unchanged.

Evidence on the refresh branch (descends from the merge SHA; no source change since):

- `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error`: 184/184 passed.
- `bash tests/scripts/verify-phase3-player.sh --build-package` at `4bcd27e`: exit 0; the optional player CTest passed 51/51, including `player_session_replacement_failure` (FIFO rejection and preserved session) and the continuation tests, and the extracted-package fresh-process MBC1 continuation smoke passed (SDL 3.4.18).
- Hosted: PR-head ci run [38064419789](https://github.com/szTheory/gabbaboy/actions/runs/38064419789) succeeded on every job, including `macos-player-package`.

SAVE-01..SAVE-04 coverage is unchanged and green. No new gaps were found, no test files were added, and no manual UAT was added. No hardware or power-loss result is implied.
