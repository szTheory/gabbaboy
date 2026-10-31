---
phase: GB-18-player-save-slots-and-host-contract
plan: "09"
subsystem: host-contract
tags: [install, docs, contract, qualification, asan, phase-tail]
requires:
  - phase: GB-18-player-save-slots-and-host-contract
    provides: "18-01 host runner and host_fixture ROMs; 18-02 gbb_get_input_clock; 18-05/18-06 player slots; 18-08 docs/host-contract.json, --print-save-format and verify-host-contract.py"
provides:
  - "share/gabbaboy/host-contract.json: the contract JSON installed beside the runner"
  - "installed_host_smoke: the installed runner from an unrelated cwd, a two-process continuation (01 then 02), a preload (41 to 42) and a byte-identity plus --print-save-format agreement check with a seeded drift control"
  - "docs: README Host mode (headless), native guide Host process contract, cartridge guide Host raw saves and player state slots, unreleased ledger entries for destination v0.3.0"
  - "verify-host-contract.py --docs (exit-code and save-format tables against the JSON) and verify-no-interop-claims.py (six published files, seeded control)"
  - "12 doc contract CTests, 1 installed smoke, GBB_SCOPE_SECTION in VerifyDocContract.cmake, five DECISIONS rows D-115..D-119"
affects: []
actuals:
  tokens: 11000
  tasks: 3
  commits: 7
commits: 7
plan_head_before: 936e0bfc959e3288365e6af3e164b2c2e095c969
plan_head_after: 3c148865e2cecf4b07801215e441100941f8965e
tech-stack:
  added: []
  patterns:
    - "A published table is checked cell by cell against the machine-readable contract it restates; a seeded copy with one changed cell and another with a renamed header each fail for their own REJECT code."
    - "A phrase-removed control copies the tracked document at configure time and fails the configure if its anchor is missing, so a control cannot pass vacuously; CMake wraps long error text, so its expected regex tolerates any non-alphanumeric run between words."
    - "A scan that reads .planning/ lives in its own script and its test carries the planning label, so a script that merely mentions .planning/ does not turn unrelated tests into planning readers."
key-files:
  created:
    - tests/scripts/test_installed_host.py
    - tests/cmake/host-contract.cmake
    - tests/scripts/verify-no-interop-claims.py
  modified:
    - CMakeLists.txt
    - tests/cmake/areas.cmake
    - tests/expected-tests.txt
    - cmake/ExpectedTests.cmake
    - cmake/VerifyDocContract.cmake
    - .github/scripts/verify-test-inventory.sh
    - tests/scripts/verify-host-contract.py
    - README.md
    - docs/native-integration.md
    - docs/cartridge-and-saves.md
    - docs/support/unreleased.md
    - .planning/research/v0.3/PLAYSTEAD-CONTRACT.md
    - .planning/context/DECISIONS.md
    - tests/cmake/input-clock.cmake
    - tests/cmake/slots.cmake
key-decisions:
  - "D-115..D-119 record the five Phase 18 planner discretion choices at the phase tail: the 56-event restored-queue bound, the 16-frame retry back-off, the save_format=none sentinel, the undo-backup-failed message and scratch-instance validation before the preload write."
  - "installed_host_smoke is a stdlib Python harness, not a cmake -P script, because the counter ROM and the 41 preload image contain NUL bytes that CMake strings cannot hold."
  - "The interop-claim scan is its own script with the planning label, not a mode of verify-host-contract.py."
patterns-established:
  - "Phase-tail ASan qualification in the project's Linux verifier container, run as a non-root user, with the failures classified as phase defect, image gap or emulation artifact."
requirements-completed: [PLAY-01, HOST-01, HOST-02, HOST-03]
coverage:
  - id: D1
    description: "docs/host-contract.json is installed as share/gabbaboy/host-contract.json, and the installed runner, started from a working directory unrelated to the prefix against a fresh save directory, reads back a game-visible counter of 01 then 02 across two processes and 42 from a 41 preload, prints a save-format id and byte count that name a row of the installed JSON, and finds the installed JSON byte-identical to the source; a copy with one digit of the 0x03/0x02 row's byte count changed is rejected with installed-contract-drift in the same run."
    requirement: HOST-01
    human_judgment: false
    verification:
      - kind: e2e
        ref: "ctest -R ^installed_host_smoke$ (installed-host pass continuation=01,02 preload=42 controls=1)"
        status: pass
      - kind: integration
        ref: "ctest -R ^(installed_runner_smoke|installed_consumer_(c|cpp)|preview_package_smoke)$"
        status: pass
  - id: D2
    description: "README, the native guide, the cartridge guide and the unreleased ledger carry the host-mode, host process contract, raw save and state slot text; each document has a phrase contract scoped to its own section and a copy with one pinned phrase removed fails with doc-contract-missing and that phrase."
    requirement: HOST-02
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest -R ^(native_guide_host_contract|cartridge_guide_slots_contract|readme_host_mode_contract|unreleased_host_entries)$"
        status: pass
      - kind: integration
        ref: "ctest -R ^doc_contract_(host|readme_host|cartridge_slots|unreleased_host)_missing_selftest$"
        status: pass
  - id: D3
    description: "The exit-code table (4 rows) and the save-format table (16 rows) of the Host process contract section equal docs/host-contract.json cell by cell; a copy whose 32,789 cell reads 32,816 is rejected as doc-table-drift and a copy whose save-format header row is renamed is rejected as doc-table-missing."
    requirement: HOST-03
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest -R ^host_contract_docs$ (host-contract docs pass exit_rows=4 format_rows=16)"
        status: pass
      - kind: integration
        ref: "ctest -R ^(host_contract_docs_control|host_contract_docs_missing_control)$"
        status: pass
  - id: D4
    description: "No line of README.md, the native guide, the cartridge guide, the unreleased ledger, docs/host-contract.json or the Playstead research note matches the byte-identical, compatible or interoperab ... mGBA pattern; the note's non-RTC SRAM sentence is replaced by the no-interoperability sentence and the MBC2 512 B versus 256 B difference, and a seeded copy holding the original sentence is rejected inside the same run."
    requirement: HOST-03
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest -R ^doc_no_interop_claims$ (no-interop-claims pass files=6 controls=1)"
        status: pass
      - kind: other
        ref: "grep -c 'byte-identical to mGBA' .planning/research/v0.3/PLAYSTEAD-CONTRACT.md prints 0"
        status: pass
  - id: D5
    description: "The phase tail is qualified at its final head: the full phase1 suite passes 1650 of 1650 with 1650 JUnit cases equal to the 1650 lines of tests/expected-tests.txt, the inventory, test-budget, summary-coverage, no-phase-paths and planning-label checks pass, no Phase 18 test exceeds 10 s locally, no workflow file differs from f4082a6, and the project version line is still 0.2.1."
    requirement: PLAY-01
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest --test-dir build -j8 --output-junit phase18-tail.xml at 3c148865: 1650 of 1650 passed"
        status: pass
      - kind: other
        ref: "bash .github/scripts/verify-test-inventory.sh --self-test"
        status: pass
      - kind: other
        ref: "git diff --quiet f4082a6 -- .github/workflows/ and grep -c 'project(GabbaBoy VERSION 0.2.1' CMakeLists.txt prints 1"
        status: pass
  - id: D6
    description: "The five planner discretion choices are recorded as D-115..D-119 in DECISIONS.md, each citing the owning plan SUMMARY, the CTest that pins it and a revisit trigger."
    requirement: PLAY-01
    human_judgment: false
    verification:
      - kind: other
        ref: "git diff -U0 on .planning/context/DECISIONS.md holds exactly 5 added rows naming 56, frame + 16, save_format=none, Undo not applied: undo backup failed; nothing changed and scratch instance"
        status: pass
duration: 50min
completed: 2026-10-29
status: complete
---

# Phase 18 Plan 09: Installed Host Contract, Published Documentation and Phase-Tail Qualification Summary

**The installed `gabbaboy-runner` now ships `share/gabbaboy/host-contract.json` and continues a raw save across two processes from an unrelated working directory, the host process contract and slot behaviour are documented with phrase contracts and tables held cell by cell to the JSON, no document claims emulator interoperability, and the full suite passes 1650 of 1650 at the final head.**

## Performance

- **Duration:** about 50 min (a quarter of it waiting on the Linux ASan container)
- **Tasks:** 3 (Task 1 tracer, Task 2 docs, Task 3 read-only qualification)
- **Files:** 16 changed outside `.planning/` (3 created), plus `DECISIONS.md` and the Playstead note

## Accomplishments

- `install(FILES docs/host-contract.json DESTINATION share/gabbaboy)` ships the contract. `installed_host_smoke` (stdlib Python, POSIX only, registered only with an install prefix) drives the installed binary from `<work>/cwd`, runs the counter ROM twice (byte 0 is `01` then `02`), a `41` preload (`42`), compares the installed JSON with the source byte for byte, checks that `--print-save-format` names a row of it, and feeds a copy with one digit changed through the same comparison, which must fail with `installed-contract-drift`.
- The native guide gained `## Host process contract` (flags, stem rule with the Playstead `deletingPathExtension` divergence, atomicity scope with `no power-loss guarantee`, cadence and loss windows of 16 quiet frames, 300 frames plus one write and 3,600 frames, exit table, signals, Windows refusal, no wall-clock time, single-writer rule, save-format table, the `save_format=none` sentinel sentence and `gbb_get_input_clock`). The README gained `## Host mode (headless)`; the cartridge guide gained `## Host raw saves and player state slots`; the unreleased ledger has a host-mode and a player-slot entry, each with source, model, execution mode, rights, CTest dispositions and `destination v0.3.0`.
- `verify-host-contract.py --docs` locates the two tables by header row inside the section and compares every cell with the JSON (backticks and thousands separators are formatting only). `verify-no-interop-claims.py` scans six files line by line at one commit and rejects its own seeded copy of the pre-correction Playstead sentence.
- `PLAYSTEAD-CONTRACT.md` no longer says non-RTC SRAM is byte-identical to another emulator; it records the MBC2 difference (512 B against 256 B) and a no-interoperability sentence.
- `DECISIONS.md` records D-115..D-119 (see Decisions Made).

## Task Commits

1. **Task 1 (tracer): installed contract and relocated continuation** - `d71eaa5c` (test, RED: the install rule absent, `installed share/gabbaboy/host-contract.json is missing`) then `12eebba1` (feat, GREEN). Tracer gate: `<verify>` re-run end to end (5 installed and package tests plus the inventory self-test); tracer verified end-to-end, expanding.
2. **Task 2: docs, tables and interop guard** - `d5aea3fe` (test, RED), `6e670406` (docs, GREEN), `323d93e0` (fix, see Deviations).
3. **Task 3: qualification** - two owning-plan fixes found by it (`4780e365` for 18-02, `3c148865` for 18-05), then this SUMMARY and the DECISIONS rows in the next commit.

**Plan metadata:** the SUMMARY and DECISIONS commit, then the STATE and ROADMAP commit.

## Files Created/Modified

- `CMakeLists.txt` - one install rule
- `tests/scripts/test_installed_host.py`, `tests/cmake/host-contract.cmake` - the installed smoke and every registration of this plan (one include line in `tests/cmake/areas.cmake`)
- `tests/expected-tests.txt`, `cmake/ExpectedTests.cmake`, `.github/scripts/verify-test-inventory.sh` - 13 names; `installed_host_smoke` in the no-prefix and Windows removal lists
- `tests/scripts/verify-host-contract.py`, `tests/scripts/verify-no-interop-claims.py`, `cmake/VerifyDocContract.cmake` - `--docs`, the interop scan, `GBB_SCOPE_SECTION`
- `README.md`, `docs/native-integration.md`, `docs/cartridge-and-saves.md`, `docs/support/unreleased.md`, `.planning/research/v0.3/PLAYSTEAD-CONTRACT.md`, `.planning/context/DECISIONS.md`
- `tests/cmake/input-clock.cmake`, `tests/cmake/slots.cmake` - leak detection off for the deliberately failing mutants (owning-plan fixes)

## Decisions Made

- **D-115** the 56-event restored-queue bound (64 minus the player's 8 post-load releases; 18-05 W-6, 18-06 `player_input_rebase`; `slot_reanchor_plan`).
- **D-116** the 16-frame retry back-off after a failed periodic flush (`frame + 16`; 18-04; `host_cadence_retry`).
- **D-117** `save_format=none bytes=0` is a no-battery sentinel, not an id (18-08; `save_format_print_none`, the native-guide sentence).
- **D-118** the undo-source message `Undo not applied: undo backup failed; nothing changed` (18-05; `slot_message_table`).
- **D-119** scratch-instance validation before the preload write (18-05 W-5; the `slot_refusal_*` byte-identity cases).
- The installed smoke is a Python harness for the NUL-byte reason in the plan's pattern-choice truth.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] The scope option of VerifyDocContract.cmake ends at the next blank line**
- **Found during:** Task 2
- **Issue:** `native_guide_host_contract` must find phrases anywhere in the `## Host process contract` section, but `GBB_SCOPE_START` limits the scope to the paragraph holding the heading (the heading is followed by a blank line).
- **Fix:** an optional `GBB_SCOPE_SECTION` input makes the scope run from the literal to the next level-2 heading; the default behavior and the existing `native_guide_rtc_contract` are unchanged.
- **Files modified:** `cmake/VerifyDocContract.cmake` (not in the plan's list)
- **Commit:** `d5aea3fe`

**2. [Rule 3 - Blocking] The cartridge guide named two core-private macros**
- **Found during:** Task 2
- **Issue:** `cartridge_guide_slots_contract` scans the whole guide for `GBB_*` names declared in the public header and failed on `GBB_MAX_ROM_SIZE` and `GBB_LEGACY_MAX_ROM_SIZE`, which exist only in `src/core/gabbaboy.c`.
- **Fix:** the two parentheticals were dropped; the sizes (8 MiB, 2 MiB) are stated in words, as the plan asks for new text.
- **Files modified:** `docs/cartridge-and-saves.md`
- **Commit:** `6e670406`

**3. [Rule 1 - Bug] A long expected phrase did not match CMake's wrapped error text**
- **Found during:** Task 2 (the README control)
- **Fix:** the phrase-removed controls match any run of non-alphanumeric characters between words, and phrases are pinned in halves where a sentence holds a semicolon (list separator). Both are the same assertions as the plan's `doc-contract-missing: <phrase>`.
- **Files modified:** `tests/cmake/host-contract.cmake`
- **Commit:** `d5aea3fe`

**4. [Rule 1 - Bug] The interop scan made host_contract_json a planning reader**
- **Found during:** Task 3 (the first full run: `REJECT unlabelled-planning-reader: host_contract_json`)
- **Issue:** adding the Playstead note path to `verify-host-contract.py` made every test that runs it a `.planning/` reader without the `planning` label.
- **Fix:** the scan moved to `tests/scripts/verify-no-interop-claims.py` (a file beyond the plan's list, which allowed "a CMake -P scan or a checker mode") and `doc_no_interop_claims` carries the `planning` label; `verify-host-contract.py` keeps only `--docs`.
- **Commit:** `323d93e0`

**5. [Rule 2 - Missing critical] A second table control**
- **Issue:** the plan's one control proves `doc-table-drift`; a table that vanishes is a different failure.
- **Fix:** `host_contract_docs_missing_control` (a copy with the save-format header row renamed, REJECT `doc-table-missing`), one extra inventory name.

**6. [Rule 1 - Bug, routed to the owning plans] Phase 18 mutant controls fail under Linux LeakSanitizer**
- **Found during:** Task 3 item (2), the Linux ASan run
- **Issue:** `input_clock_mutant_*` (18-02) and `slot_mutant_*` (18-05) trip a REQUIRE that returns early; under `phase1-asan` on Linux LeakSanitizer then reports leaks and exits through `_exit`, dropping the buffered `FAIL <case>` line, so seven tests failed with "exit code 1 was right but the output did not match". macOS has no LeakSanitizer, so no earlier run saw it. Earlier mutant tests (`cmake/P12Mutants.cmake`, `tests/CMakeLists.txt`) already set `ASAN_OPTIONS=detect_leaks=0` on exactly these deliberately failing runs.
- **Fix:** the same environment property on the mutant tests only (controls and every other test keep leak checking), committed against the owning plans as D-105 directs: `4780e365` (18-02, `tests/cmake/input-clock.cmake`) and `3c148865` (18-05, `tests/cmake/slots.cmake`). Task 3's checks were then re-run in full.
- **Verification:** the 99 Phase 18 tests of the Linux ASan build pass (`build/18-09-asan-linux-rerun2.log`).

### Planned-form differences

- **Phrase halves.** The single-writer, power-loss and Windows sentences are pinned as halves split at the semicolon; the Task 2 text lists them as whole sentences.
- **Whole-guide RTC test.** `native_guide_rtc_contract` still passes unchanged.
- **UAT closure self-test.** `verify-uat-closure.py --self-test` needs a phase directory with an existing `NN-UAT.md`, which Phase 18 does not have until `/gsd-verify-work 18`. It was run against the latest closed phase and passed (`uat-closure self-test pass automated=51 controls=21`).
- **TDD shape.** Task 1's RED failed on the behavior (`installed share/gabbaboy/host-contract.json is missing`, `build/18-09-task1-red.log`). Task 2's tests are checkers over documents, so its RED ran against the committed revision before the docs were committed: `host_contract_docs` and `doc_no_interop_claims` failed (the second on the original Playstead sentence at line 107), the phrase tests already saw the uncommitted docs (`build/18-09-task2-red-worktree.log`). The RED commit leaves the control anchors absent from the committed docs until the next commit; it was not intended to be bisectable.

---

**Total deviations:** 6 (2 blocking, 3 bugs, 1 missing critical), all handled in-plan; no gap plan 18-10 is opened.
**Impact on plan:** three files beyond the plan's list (`cmake/VerifyDocContract.cmake`, `tests/scripts/verify-no-interop-claims.py`, and the two owning-plan registration files); no scope change.

## Phase-Tail Qualification (Task 3, D-27)

Head SHA for the code evidence: `3c148865e2cecf4b07801215e441100941f8965e` (docs-only commits follow it).

| # | Check | Result |
|---|---|---|
| 1 | `ctest --test-dir build -j8 --output-junit build/phase18-tail.xml` (reconfigured with `-DGBB_STATE_PIN_BASE_REV=7c1f257dd47fec77380f410b93a488bb1a5695cd`, `GBB_TEST_INSTALL_PREFIX=build/state-prefix`, rebuilt and reinstalled at the head) | 1650 of 1650 passed, 132.96 s; JUnit cases 1650 equal `wc -l < tests/expected-tests.txt` 1650. Without an install prefix the registered count is 1644 and the inventory still matches |
| 2 | Linux ASan, `gabbaboy-phase2-verifier` container (x86-64 under emulation on an arm64 host), preset `phase1-asan` | Not a clean lane: see below. Exact-head `linux-asan-ubsan`: **pending post-CI** |
| 3 | `bash .github/scripts/verify-test-inventory.sh --self-test` | passed |
| 4 | `test_budget`, `summary_coverage` (+ `_selftest`, `_live`, fixtures), `no_phase_paths`, `planning_labels` and `_controls` | all passed |
| 5 | `verify-uat-closure.py <phase-dir> --self-test` | passed against the Phase 16 closure (Phase 18 has none until verify-work) |
| 6 | per-test wall time for `^(host_|slot_|save_format_|input_clock_|installed_host_|no_host_clock_signal)` | 145 tests; slowest `host_exit_crash_storm` 9.4 s, `save_format_controls` 8.9 s, `host_signal_decoy_in_place_write` 3.1 s, `input_clock_after_load` 2.7 s; none above 45 s |
| 7 | `git diff --quiet f4082a6 -- .github/workflows/`; `grep -c 'project(GabbaBoy VERSION 0.2.1' CMakeLists.txt` | no workflow differs; prints 1. `.github/scripts/verify-workflow-policy.py` is also unchanged |
| 8 | every Phase 18 SUMMARY `coverage:` block | `summary_coverage` passes (re-run after this file was written) |
| 9 | DECISIONS.md rows | five new rows D-115..D-119 after D-114 |

Local times of this plan's tests: `installed_host_smoke` 0.9 s; the twelve other new tests 0.01 to 0.12 s each. None has a TIMEOUT other than the base 60 s and none has an allowlist row.

**Linux ASan run (item 2).** The first full `ctest --preset phase1-asan` in the container (as root, 1644 tests, 1,060 s) failed 18 tests. Classified, with the logs in `build/18-09-asan-linux.log` and `build/18-09-asan-linux-rerun.log`:

- **Phase 18 defect, fixed (7):** `input_clock_mutant_short_size_writes`, `input_clock_mutant_last_is_now`, `slot_mutant_undo_before_load`, `slot_mutant_preload_before_validate`, `slot_mutant_no_guard`, `slot_mutant_no_rollback`, `slot_mutant_plan_ignores_last` (Deviation 6). After the fix the 99 Phase 18 tests of the ASan build pass (`build/18-09-asan-linux-rerun2.log`).
- **Root-user artifacts (3):** `host_exit_failure_readonly`, `host_signal_decoy_exit0_after_failed_flush` and `v02_fuzz_controls` pass when the container runs as a non-root user; a root user writes into a read-only directory.
- **Emulation artifact (1):** `host_signal_disposition` fails on `after.sa_handler == SIG_DFL`. A 15-line C program with `SA_RESETHAND` shows `after_is_dfl=0` in the x86-64 container with and without sanitizers and `after_is_dfl=1` on a native arm64 Linux container, so the emulation does not implement the flag. Native CI is the real check.
- **Image gaps, not Phase 18 (7):** `cgb_mooneye_repro_requires_manifest`, `release_lifecycle_replay` and `release_lifecycle_controls` need `jq`, which the image lacks (`jq: command not found`, `FileNotFoundError: 'jq'`); `state_format_contract`, `v02_consumer_controls_c` and `v02_consumer_controls_cpp` run a nested CMake that finds no build program for "Unix Makefiles". `workflow_policy_controls` also failed in the image; its script and every workflow are unchanged since `f4082a6`, and it was not root-caused here.

This is local evidence for the Phase 18 tests under Linux ASan and LeakSanitizer, not a clean full lane. Item 2 stays **pending post-CI**.

**Post-CI addendum (open, before `/gsd-verify-work 18`).** After the PR exists, record by run URL and head SHA the green `linux-asan-ubsan`, `native-windows-x64` and `macos-player-package` runs, and confirm that each new test's hosted time from the slowest lane is at most 75% of its 60 s budget (GB-CI-012). `native-windows-x64` is the first run of the Windows removal lists for `installed_host_smoke`.

## Issues Encountered

- The first full run failed `planning_labels` (Deviation 4); after the fix the second run failed three revision-pinned tests only because the build had not been rebuilt at the new HEAD (known environment note); the third full run, after a rebuild, passed.
- `workflow_policy_controls` takes 60 to 95 s under load; it is not a Phase 18 test and has its own budget row.

## Known Stubs

None.

## Threat Flags

None. T-18-30 (installed JSON drift) is mitigated by the byte-identity and print agreement check with its seeded control; T-18-31 (over-claiming) by the phrase contracts, the JSON-checked tables and `doc_no_interop_claims` with its seeded control; T-18-32 by `git grep -e '/Users/' -e '/home/' -- README.md docs/` exiting 1 and by the harness diagnostics printing stems and tokens only. T-18-SC: no package was installed.

## Requirement Traceability

- **PLAY-01** (player numbered slots): 18-05 and 18-06 tests plus this plan's slot documentation (`cartridge_guide_slots_contract`) and D-115, D-118, D-119.
- **HOST-01** (headless runner with atomic raw save): 18-01 and 18-04 tests plus `installed_host_smoke`.
- **HOST-02** (signals, exit table, cadence): 18-04 and 18-07 tests plus `native_guide_host_contract` and `host_contract_docs`.
- **HOST-03** (published save-format contract): 18-08 tests plus the installed JSON, `host_contract_docs` and `doc_no_interop_claims`.

## Next Phase Readiness

Phase 18 execution is complete (plans 18-01 through 18-09 summarised; the gap slot 18-10 is unused). This is not Phase 19. The orchestrator runs code review and verification next.

Next command: `/gsd-verify-work 18`. Phase 19 (the release phase that binds `installed_host_smoke` as a receipt) is not started and must be chosen by the owner after verification and the PR's exact-head CI.

## Self-Check: PASSED

- FOUND: tests/scripts/test_installed_host.py, tests/cmake/host-contract.cmake, tests/scripts/verify-no-interop-claims.py, build/state-prefix/share/gabbaboy/host-contract.json
- FOUND commits: d71eaa5c, 12eebba1, d5aea3fe, 6e670406, 323d93e0, 4780e365, 3c148865

---
*Phase: GB-18-player-save-slots-and-host-contract*
*Completed: 2026-10-29*
