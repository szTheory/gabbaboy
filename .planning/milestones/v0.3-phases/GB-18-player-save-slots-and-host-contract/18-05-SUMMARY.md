---
phase: GB-18-player-save-slots-and-host-contract
plan: "05"
subsystem: player-slot-engine
tags: [player, save-state, slots, posix, all-or-nothing, mutants]
requires:
  - phase: GB-18-player-save-slots-and-host-contract
    provides: "18-01 dir-fd atomic writer; 18-02 mutant-library pattern and the API-surface checker (GBB_SOURCE_FILES); 18-03 gbb_get_input_clock; 18-04 writer fault seams and the test twin of the host library"
provides:
  - "gabbaboy_player_slots: SDL-free slot engine (src/player/slots.c, slots.h) linked by gabbaboy-player-adapter and the tests"
  - "player_slot_load: scratch-instance validation, then battery preload, live load, undo write with rollback, in the D-23 order"
  - "host_save_io_read_bounded: no-follow, regular-file, caller-bounded reader shared with the exact reader through one open helper"
  - "player_slot_plan_reanchor, player_slot_key_decode, player_slot_format_message/selection/log: pure D-24, D-21 and D-25 tables"
  - "test_slots (POSIX) and test_slots_pure (portable) with 29 slot_ CTests, six of them mutants that each fail their own case"
affects: [18-06, 18-07, 18-09]
actuals:
  tokens: 26500
  tasks: 3
  commits: 7
commits: 7
plan_head_before: 3c24bdbaa3a771b907e3c10efc2ffeb8e4b55de6
plan_head_after: 4c9962b2b041fbd5b6d23b7064241de19be9d3fe
tech-stack:
  added: []
  patterns:
    - "A refusal is detected in a scratch instance built from the store's own ROM copy before the first write, so the D-23 order (preload before the live load) and the no-file-touched rule hold together."
    - "A mutant that moves a write earlier is an insertion at a unique comment anchor; the executable is named variant so verify-core-linkage.py keeps its mutant-core rule."
    - "Expected strings in the portable test are written out independently of the engine and the glyph is a UTF-8 byte escape."
key-files:
  created:
    - src/player/slots.c
    - src/player/slots.h
    - tests/test_slots.c
    - tests/test_slots_pure.c
    - tests/cmake/slots.cmake
  modified:
    - src/host/gbb_host.h
    - src/host/host_save_io.c
    - CMakeLists.txt
    - tests/cmake/areas.cmake
    - tests/cmake/host.cmake
    - tests/expected-tests.txt
    - cmake/ExpectedTests.cmake
    - .github/scripts/verify-test-inventory.sh
key-decisions:
  - "Checker W-5: a load validates the slot in a scratch instance (gbb_create, gbb_load_rom of the store's heap copy, gbb_load_state, gbb_get_input_clock) before any write, so the preload file is on disk before the live gbb_load_state and a refused slot still touches no file."
  - "Checker W-6 (recorded discretion): a restored queue holding more than 56 events is UNSAFE_INPUT, so the eight releases the player queues after a load always fit the core's 64-event queue; the time window is 140,448 x 64 half-dots."
  - "Deviation 4 (recorded discretion): the undo-source backup failure reads `Undo not applied: undo backup failed; nothing changed`, the one string not in the D-25 table."
  - "A failed live gbb_load_state after a successful scratch validation (not expected, same ROM and profile) returns REFUSED with the live machine unchanged by gbb_load_state's all-or-nothing contract; the preload file then holds the current battery, which is a correct backup."
  - "tests/test_slots.c (this plan: SDL-free engine, main inventory, POSIX) and tests/player/test_slots.c (18-06: macOS player suite) are deliberately separate files with the same base name."
requirements-completed: [PLAY-01]
coverage:
  - id: D1
    description: "A slot saved through the dir-fd writer holds exactly the gbb_save_state bytes, loading it after 60 more frames returns those bytes, and an empty slot returns EMPTY and writes nothing."
    requirement: PLAY-01
    human_judgment: false
    verification:
      - kind: unit
        ref: "ctest -R ^slot_(roundtrip|empty)$ (tests/test_slots.c)"
        status: pass
  - id: D2
    description: "host_save_io_read_bounded opens without following symlinks or blocking, requires a regular file, reads at most the caller's bound and never sizes anything from st_size: a symlinked slot reads as READ_FAILED and a state plus 4096 bytes reads as one byte too many (SIZE_MISMATCH)."
    requirement: PLAY-01
    human_judgment: false
    verification:
      - kind: unit
        ref: "ctest -R ^slot_refusal_(symlink|oversize)$ (tests/test_slots.c)"
        status: pass
      - kind: integration
        ref: "ctest -R ^host_import_mutant_follow$ (the shared open helper keeps the one anchor the follow mutant edits)"
        status: pass
  - id: D3
    description: "Eight refusals (a state of another game, a DMG state in a CGB store, a patched release token with a recomputed CRC, a text file, a flipped body byte, a 100-byte truncation, size plus 4096 bytes, a symlinked slot) each return their exact outcome and gbb_error and leave gbb_save_state, gbb_copy_battery, the battery generation and the SHA-256 of the slot, undo, preload and .gbb files byte-identical, missing files staying missing."
    requirement: PLAY-01
    human_judgment: false
    verification:
      - kind: unit
        ref: "ctest -R ^slot_(wrong_rom_untouched|refusal_.*)$ (tests/test_slots.c)"
        status: pass
  - id: D4
    description: "The order is enforced by killed mutants: writing the undo snapshot or the battery preload before the slot is validated fails refusal_flipped_byte at exit 1."
    requirement: PLAY-01
    human_judgment: false
    verification:
      - kind: unit
        ref: "ctest -R ^slot_mutant_(undo_before_load|preload_before_validate)$"
        status: pass
  - id: D5
    description: "A forced preload write failure on the first load returns BACKUP_FAILED with the machine, generation and files identical and no undo or preload file; a forced undo write failure rolls the machine back to byte-identical state and battery with no file changed; a failed slot save keeps the old file's inode and bytes with no temp left, and the seam is one-shot. The rollback-removing mutant fails undo_write_failure."
    requirement: PLAY-01
    human_judgment: false
    verification:
      - kind: unit
        ref: "ctest -R ^slot_(backup_write_failure|undo_write_failure|save_failure_keeps_old)$"
        status: pass
      - kind: unit
        ref: "ctest -R ^slot_mutant_no_rollback$"
        status: pass
  - id: D6
    description: "Undo swaps: load slot 1, undo returns the starting state, undo again returns slot 1; undo with no undo file returns NO_UNDO and writes nothing."
    requirement: PLAY-01
    human_judgment: false
    verification:
      - kind: unit
        ref: "ctest -R ^slot_(undo_swap|no_undo)$"
        status: pass
  - id: D7
    description: "The battery guard keeps the pre-A in-game save: loading A backs up battery X, loading B (live battery equals the guard) leaves the preload file at X, and an in-game change before the next load is backed up. The guard-removing mutant fails battery_guard."
    requirement: PLAY-01
    human_judgment: false
    verification:
      - kind: unit
        ref: "ctest -R ^slot_battery_guard$"
        status: pass
      - kind: unit
        ref: "ctest -R ^slot_mutant_no_guard$"
        status: pass
  - id: D8
    description: "A restored queue with an event 65 frames ahead, 60 events or 57 events is UNSAFE_INPUT with the machine and files untouched (no undo or preload written on the session's first load); 56 events load and report queued_count 56."
    requirement: PLAY-01
    human_judgment: false
    verification:
      - kind: unit
        ref: "ctest -R ^slot_unsafe_queued_input$"
        status: pass
  - id: D9
    description: "Every outcome and every gbb_error from GBB_OK through GBB_STATE_INVALID_CONTENT maps to the exact D-25 string for both subjects (Slot N and The undo backup), buffers are always NUL-terminated and never overrun, and the log line carries operation, slot, outcome token and gbb_error. A mapping of UNSUPPORTED_VERSION to the damaged text fails message_table."
    requirement: PLAY-01
    human_judgment: false
    verification:
      - kind: unit
        ref: "ctest -R ^slot_message_table$ (tests/test_slots_pure.c, portable)"
        status: pass
      - kind: unit
        ref: "ctest -R ^slot_mutant_message_map$"
        status: pass
  - id: D10
    description: "The key decoder selects on digits 1-9 (Shift allowed, GUI, Ctrl or Alt vetoes, 0 reserved), maps GUI+S, GUI+L and GUI+Z to save, load and undo, and returns nothing for bare letters, GUI+R, a repeat or a blocked state."
    requirement: PLAY-01
    human_judgment: false
    verification:
      - kind: unit
        ref: "ctest -R ^slot_key_decoder$ (tests/test_slots_pure.c, portable)"
        status: pass
  - id: D11
    description: "The re-anchor plan releases at max(now, last queued) and flags a window above 140,448 x 64 half-dots or more than 56 queued events; against the core, after loading a later-time state and an earlier-time state with two restored events, a stale-cursor event is refused, the plan's press is admitted, the guest sees A released before it and pressed within one frame after it, and a no-press control keeps A released. A plan that ignores the restored queue fails reanchor_earlier."
    requirement: PLAY-01
    human_judgment: false
    verification:
      - kind: unit
        ref: "ctest -R ^slot_reanchor_plan$ (tests/test_slots_pure.c, portable)"
        status: pass
      - kind: integration
        ref: "ctest -R ^slot_reanchor_(later|earlier)$ (generated joypad-mirror ROM, SRAM byte 0 bit 0)"
        status: pass
      - kind: unit
        ref: "ctest -R ^slot_mutant_plan_ignores_last$"
        status: pass
  - id: D12
    description: "Selection text reads `Slot N selected: empty` for a missing file, `saved YYYY-MM-DD HH:MM` in local time from the mtime (TZ=UTC, utimensat), and a bare `saved` when stat fails for another reason."
    requirement: PLAY-01
    human_judgment: false
    verification:
      - kind: unit
        ref: "ctest -R ^slot_select_message$"
        status: pass
  - id: D13
    description: "The slot engine includes only the public header, the host header and libc/POSIX: host_api_surface scans the slots archive and sources and reports archives=2; the Windows-build proxy (-D_WIN32 -fsyntax-only) passes for src/host/*.c and slots.c; the 29 slot_ names, 25 of them POSIX-only, are in the expected inventory and both Windows lists."
    requirement: PLAY-01
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest -R ^host_api_surface$"
        status: pass
      - kind: other
        ref: "bash .github/scripts/verify-test-inventory.sh --self-test"
        status: pass
  - id: D14
    description: "The whole suite is green at the plan head after reconfiguring the revision-pinned tests."
    requirement: PLAY-01
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest -j6 over the full phase1 build at 233a1fed: 1610 of 1610 passed"
        status: pass
duration: 21min
completed: 2026-10-29
status: complete
---

# Phase 18 Plan 05: Player Slot Engine Summary

**An SDL-free slot engine saves and loads numbered gbb_save_state slots all-or-nothing: a scratch instance rejects a bad, wrong-game, over-queued or symlinked slot before any file or live state is touched, the in-game battery is backed up before the live load, an undo write failure rolls the machine back, and the D-25 messages, D-21 key table and D-24 re-anchor plan are exact, pure and mutant-proven.**

## Performance

- **Duration:** about 21 min
- **Started:** 2026-10-29T03:48:24Z
- **Completed:** 2026-10-29T04:09Z
- **Tasks:** 3
- **Files modified:** 13 (5 created, 8 modified, excluding planning files)

## Accomplishments

- `player_slot_save` writes the `gbb_save_state` bytes with `host_save_io_replace` on the pref-dir descriptor. The file names come only from the ROM digest, the created profile and a digit 1-9, so no user text reaches a name (T-18-17).
- `player_slot_load` runs the D-23 sequence in one function, each step returning before any later one: bounded read, scratch validation (create, load the store's own ROM copy, `gbb_load_state`, `gbb_get_input_clock`, the unsafe-input rule), live snapshot, battery guard preload write, live `gbb_load_state`, undo write with rollback, guard update. Undo is the same function with the undo file as source, so it swaps.
- Eight generated refusals and the wrong-ROM control assert the exact outcome and `gbb_error`, and that `gbb_save_state`, `gbb_copy_battery`, the generation and the SHA-256 of the slot, undo, preload and `.gbb` stand-in files do not change.
- The order is held by mutants: undo-before-validation and preload-before-validation both fail `refusal_flipped_byte` with `snap_equal`; no-guard fails `battery_guard`; no-rollback fails `undo_write_failure`.
- Post-load input admission is observed in the guest. A generated joypad-mirror ROM copies P1 into SRAM byte 0. After a later-time load and an earlier-time load with two restored events, the stale cursor is refused, the press at the plan's release time is admitted, the guest sees A released before and pressed within one frame after, and a no-press copy keeps A released.
- `test_slots_pure` is portable and iterates every outcome and every `gbb_error` 0..27 for both subjects; the glyph is a byte escape in all three files (no raw U+2318 byte).

## Task Commits

1. **Task 1 (tracer): save slot 3 and load it back** - `621a06c3` (test, RED: both cases fail at fixture setup against an inert engine) then `7a768467` (feat, GREEN: engine happy path, `host_save_io_read_bounded`)
2. **Task 2: all-or-nothing load, undo, battery guard, unsafe input, order mutants** - `507f4367` (test: 15 cases) then `38e37344` (feat: scratch validation, guard, rollback, four mutants, `archives=2`)
3. **Task 3: messages, key decoder, plan, selection text** - `58a9bbba` (test: pure table, guest-visible cases, stubs) then `233a1fed` (feat: formatters, decoder, plan, two mutants)
4. **Harness tidy** - `4c9962b2` (test: remove the fixture directory after any case)

**Plan metadata:** recorded in the following docs commit.

## Files Created/Modified

- `src/player/slots.c`, `src/player/slots.h` - the engine, types and constants; POSIX calls under `#ifndef _WIN32` with ISO C stubs, pure tables outside it
- `src/host/host_save_io.c`, `src/host/gbb_host.h` - `host_save_io_read_bounded` and the shared `open_regular_nofollow`
- `CMakeLists.txt` - `gabbaboy_player_slots` (no link libraries) and its link into `gabbaboy-player-adapter`
- `tests/test_slots.c`, `tests/test_slots_pure.c`, `tests/cmake/slots.cmake` - cases, `gbb_slots_mutant`, registrations
- `tests/cmake/host.cmake` - `host_api_surface` scans the second archive and the two slot files
- `tests/cmake/areas.cmake`, `tests/expected-tests.txt`, `cmake/ExpectedTests.cmake`, `.github/scripts/verify-test-inventory.sh` - 29 names, 25 POSIX-only in both Windows lists

## Decisions Made

- **Scratch validation keeps D-23's order (checker W-5).** The preload file is written before the live `gbb_load_state`, so there is no window where the live battery was replaced and not yet backed up, and a refused slot is found in the scratch instance before that write.
- **56-event capacity rule (checker W-6, recorded discretion).** 64 minus the 8 releases the player queues after a load. The time window is 140,448 x 64 half-dots; both are strict (`>`), tested at the boundary.
- **Undo-source backup failure string (deviation 4, recorded discretion):** `Undo not applied: undo backup failed; nothing changed`.
- **Step-4 failure** after a passing scratch validation returns REFUSED; the live machine is unchanged (all-or-nothing) and the preload file holds the current battery, a correct backup.
- **Two files named `test_slots.c` are deliberate:** `tests/test_slots.c` here (SDL-free engine, main inventory) and `tests/player/test_slots.c` in 18-06 (macOS player suite).
- **Result fields:** `error` carries a `gbb_error` only; a failed file operation reports `GBB_OK` (or `GBB_OUT_OF_MEMORY`), so the log's `gbb_error=` is never a host I/O code.
- **EMPTY with the undo source** (unreachable, the engine returns NO_UNDO) prints `The undo backup is empty; nothing changed`, so the subject rule holds for every outcome.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Second `openat` copy broke the follow-mutant anchor**
- **Found during:** Task 1 (configure after adding `host_save_io_read_bounded`)
- **Issue:** `gbb_host_mutant_library(follow ...)` in 18-04 requires its anchor `O_RDONLY | O_NOFOLLOW | O_NONBLOCK` to occur exactly once in host_save_io.c; copying the reader's open flags made configure fail.
- **Fix:** both readers now open through one static `open_regular_nofollow`, which also means a symlink-following defect would hit the slot reader too. `host.cmake` was not edited for this.
- **Files modified:** `src/host/host_save_io.c`
- **Verification:** `host_import_mutant_follow` and the 76 `host_` tests pass; `slot_refusal_symlink` passes.
- **Commit:** `7a768467`

**2. [Rule 3 - Blocking] Variant executables are named `variant`, not `mutant`**
- **Found during:** Task 2 design (same cause as 18-04 deviation 1)
- **Issue:** `verify-core-linkage.py` requires every executable named `*mutant*` that links the acceptance helpers to carry a mutant core; the slot mutants mutate only slots.c.
- **Fix:** `test_slots_variant_<name>`, `test_slots_pure_variant_<name>` and `gabbaboy_player_slots_variant_<name>`; CTest names stay `slot_mutant_*`.
- **Files modified:** `tests/cmake/slots.cmake`
- **Verification:** `core_linkage_links` and `core_linkage_controls` pass in the full suite.
- **Commit:** `38e37344`

**3. [Process] Two plan wordings met in practice**
- The `undo_before_load` mutant inserts the snapshot and undo write at the validation anchor instead of moving the original statements (one anchor cannot span steps 2 and 5 of this layout). The refused slot still leaves an undo file, so the case fails exactly as the plan requires. The `plan_ignores_last` mutant fails `reanchor_earlier` on the release-time equality, which precedes the refused-press check; both name the same defect.
- The refusal cases, `no_undo`, `empty` and `save_failure_keeps_old` passed on arrival against the Task 1 engine (nothing wrote files and `gbb_load_state` is all-or-nothing). Their discriminating evidence is the four order and guard mutants (`build/18-05-task2-mutants.log`); RED for Task 2 is the five cases that failed (`build/18-05-task2-red.log`).

**4. [Observation] Rollback advances the battery generation**
- A failed undo write rolls back with `gbb_load_state(snapshot)`. The generation is receiving-instance observer history (`state_apply_observers`), so it increases with the rollback load when the batteries differ. `undo_write_failure` therefore compares state, battery and the four file digests, not the generation. Refusals, whose first write comes after validation, compare the generation too. The host cadence writes a battery only when the bytes differ, so the extra generation costs no write.

---

**Total deviations:** 2 auto-fixed (both blocking), 1 process note, 1 observation
**Impact on plan:** No scope change. Files outside `files_modified`: none.

## Evidence Recorded for the Acceptance Criteria

- Task 1: `slot_roundtrip`, `slot_empty`, `host_api_surface` pass; `grep -E '#include.*(SDL|input\.h|session\.h|gabbaboy_test\.h|gbb_accept\.h)' src/player/slots.c src/player/slots.h` prints nothing; `gabbaboy_player_slots` has no `target_link_libraries`; `test_slots` is created inside `if(NOT WIN32)`; the `-D_WIN32 -fsyntax-only` proxy exits 0 for `src/host/*.c` and `src/player/slots.c` (also clean with `-Wall -Wextra`).
- Task 2: 20 tests in the verify regex pass. Direct mutant runs (`build/18-05-task2-mutants.log`): `undo_before_load` and `preload_before_validate` print `FAIL refusal_flipped_byte ... snap_equal(&before, &after)`, `no_guard` prints `FAIL battery_guard ... file_equals(... preload, x ...)`, `no_rollback` prints `FAIL undo_write_failure ... snap_machine_equal`; each unmutated case prints `PASS` and exits 0. In `player_slot_load` the scratch `gbb_load_state(` (line 188) and `slot_clock_unsafe(` (199) precede the first `host_save_io_replace(` (220, preload), which precedes the live `gbb_load_state(` (230) and the undo write (237). `host_api_surface` prints `host-api pass archives=2 symbols=13`.
- Task 3: `ctest -N -R '^slot_'` lists 29. `LC_ALL=C grep -c` for the U+2318 and U+00B7 byte sequences prints 0 for slots.c, test_slots_pure.c and test_slots.c; `grep -c 'xe2\\x8c\\x98' src/player/slots.c` prints 3. `slot_mutant_message_map` prints `FAIL message_table: ... message 'Slot 4 is damaged; nothing changed' expected 'Slot 4 is from another GabbaBoy version; nothing changed'`; `slot_mutant_plan_ignores_last` prints `FAIL reanchor_earlier`.
- `ctest -R '^(slot_|host_)'`: 105 of 105 pass. The inventory self-test passes.
- Full suite at `233a1fed` after reconfiguring (pin base `7c1f257`): 1610 of 1610 passed (1581 from 18-04 plus 29 new). Log `build/18-05-full-ctest2.txt`; the first run is `build/18-05-full-ctest.txt`. After the final test-only commit `4c9962b2` the 31 tests matching `^(slot_|host_api_surface)` pass again.
- Linux ASan lane: not run locally (`GABBABOY_ENABLE_SANITIZERS` is Linux-only, this host is macOS); the `linux-asan-ubsan` CI lane runs the slot tests at the PR head. The Windows MSVC build is proven by the `native-windows-x64` exact-head build, with the syntax proxy above as the local check.
- The player target (`GABBABOY_BUILD_PLAYER`, SDL3) was not rebuilt here; the only change to it is the added link of `gabbaboy_player_slots` and `gabbaboy_host` to `gabbaboy-player-adapter`, and nothing calls the engine until 18-06.

## Issues Encountered

- The first full run failed `cgb_corpus_report_tracer`, `cgb_corpus_report_controls`, `state_fuzz_controls` and `state_purity` (revision-pinned tests, build tree configured at an older HEAD) and timed out `release_lifecycle_controls` (36 s alone, slow under `-j8`). After reconfiguring, all five pass; the second full run is recorded above.
- Failing and mutant slot cases left their temp pref directory in the build tree; `4c9962b2` makes `main` remove it (`GBB_SLOTS_KEEP=1` keeps it).

## Known Stubs

None. The RED-only inert formatters in `58a9bbba` were replaced in `233a1fed`.

## Threat Flags

None. T-18-14 through T-18-18 are mitigated as planned: scratch validation, no-follow regular-file bounded read and seven generated refusals plus the wrong-ROM control (T-18-14), the state-size-plus-one read cap and the size+4096 case (T-18-15), the preload-before-live-load guard with the guard and preload-order mutants (T-18-16), names from the digest, profile token and digit only with slots 0 and above 9 rejected (T-18-17), and UNSAFE_INPUT before any write with the 60-, 57- and 65-frame cases and the boundary table (T-18-18).

## Next Phase Readiness

- Next plan: 18-06 (player wiring: SDL keys, status line, help text) consumes `player_slot_key_decode`, `player_slot_load`/`save`, `player_slot_plan_reanchor`, `player_slot_format_message/selection/log`. It must queue the eight releases at `plan.release_at`, seed its pending mirror from `plan.pending_count` and keep pause across a load.
- PLAY-01 is not complete until the player integration and the closing traceability land (18-06 and 18-09).

## Self-Check: PASSED

- FOUND: src/player/slots.c, src/player/slots.h, tests/test_slots.c, tests/test_slots_pure.c, tests/cmake/slots.cmake
- FOUND commits: 621a06c3, 7a768467, 507f4367, 38e37344, 58a9bbba, 233a1fed, 4c9962b2

---
*Phase: GB-18-player-save-slots-and-host-contract*
*Completed: 2026-10-29*
