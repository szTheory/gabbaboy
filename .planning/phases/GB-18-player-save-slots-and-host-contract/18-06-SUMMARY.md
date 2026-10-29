---
phase: GB-18-player-save-slots-and-host-contract
plan: "06"
subsystem: player-slot-wiring
tags: [player, sdl, macos, input, ui, save-state, slots]
requires:
  - phase: GB-18-player-save-slots-and-host-contract
    provides: "18-05 slot engine (player_slot_save/load, key decoder, re-anchor plan, D-25 formatters); 18-03 gbb_get_input_clock; 18-01 dir-fd writer"
provides:
  - "SDL player slot keys: digits 1-9 select, Command-S saves, Command-L loads, Command-Z undoes, decoded before the bare R and S branches, which carry a !command guard"
  - "player_input_rebase: cursor and anchor set to the restored clock, pending mirror seeded, every key and button let go and all eight marked for release"
  - "apply_slot_load: rebase, release queueing, audio clear, redraw and .gbb cadence restart after a load or undo, pause kept"
  - "D-25 status line: slot message through set_status, shown beside an active battery-save failure, with one stderr log line per operation"
  - "Help dialog slot keys and sentence, two new limitation sentences, and an automated Cocoa menu-shortcut scan with a seeded control (A2)"
  - "9 player CTests: player_slot_keys, _reanchor, _status_line, _help_text, _mutant_no_rebase, _mutant_command_guard, _menu_shortcuts, _menu_shortcuts_control (plus the updated player_limitations)"
affects: [18-07, 18-09]
actuals:
  tokens: 18400
  tasks: 3
  commits: 8
commits: 8
plan_head_before: 85e4f37d11def85cc731e51594095170f31383e9
plan_head_after: 67bb2bdc9e2b36d6b143e46e40ef6a24504bfa40
tech-stack:
  added: []
  patterns:
    - "A player mutant is a copy of main.c with one anchored edit embedded into the shared test through a GBB_PLAYER_MAIN_C include macro; the executable is named variant so verify-core-linkage.py keeps its mutant-core rule."
    - "Keys are driven through the real SDL event queue (push_key_mod, pump_events) with the player's own main.c embedded, and the guest outcome is read back from battery RAM on a generated joypad-mirror ROM."
    - "The expected state after a load is built independently in a scratch instance (slot bytes plus the eight releases at max(now, last queued)) instead of being copied from the player's output."
key-files:
  created:
    - tests/player/test_slots.c
    - tests/player/test_menu_shortcuts.c
  modified:
    - src/player/main.c
    - src/player/input.c
    - src/player/input.h
    - src/player/limitations.h
    - tests/player/test_limitations.c
    - tests/player/CMakeLists.txt
    - tests/player/expected-tests.txt
key-decisions:
  - "The slot message is kept in its own player field and combined with save_status when the title is formatted, because the title shows save_status instead of status while a battery-save failure is active; composing into app->status alone would never reach the title."
  - "player_input_rebase has no machine argument, so it marks all eight buttons for release (release_pending_buttons, held_buttons 0xFF) and apply_slot_load queues them through the existing player_input_retry_focus_releases at the same host time, which lands them at max(now, last queued) and lets the main loop retry a release the queue cannot take yet."
  - "The ROM bytes the store needs are re-read with host_save_io_read_bounded (no-follow, regular file, 8 MiB + 1 cap) and accepted only when their SHA-256 equals the digest the session computed, so a ROM replaced on disk after loading turns slots off instead of binding states to the wrong game."
  - "A2 is resolved by an automated scan of the Cocoa main menu that forces the cocoa video driver, because the package lane exports SDL_VIDEO_DRIVER=dummy and that driver has no menu."
  - "A load keeps the slot message on screen: update_battery_save no longer replaces it with the Battery RAM changed hint (a load always leaves the battery different from the last .gbb save)."
requirements-completed: [PLAY-01]
coverage:
  - id: D1
    description: "In the running SDL player, digit keys 1-9 select a slot (Shift allowed; Ctrl, Alt and Command veto), Command-S saves it without saving the battery, Command-L restores exactly the slot plus the eight queued button releases, and Command-Z swaps back, with the later Z key-up harmless."
    requirement: PLAY-01
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest -R ^player_slot_keys$ (tests/player/test_slots.c, case keys, through push_key_mod and pump_events)"
        status: pass
  - id: D2
    description: "Command-R does not reset and Command-S does not save the battery, while a bare R still resets and a bare S still saves the battery; a key repeat, a pending transition and a pending dialog change no slot file and no status; slot keys work while paused and a load keeps the pause."
    requirement: PLAY-01
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest -R ^player_slot_keys$ (guards, repeat, transition, dialog, pause and bare-key controls)"
        status: pass
      - kind: integration
        ref: "ctest -R ^player_slot_mutant_command_guard$ (main.c without !command on the R branch fails case keys with exit 1)"
        status: pass
  - id: D3
    description: "After loading an earlier-time state and a later-time state, the player cursor and anchor sit at the restored clock, no key is held, the eight releases are queued, a no-key control frame keeps A released, and a fresh Z keydown is accepted and reaches the guest within one frame of its scheduled time (SRAM byte 0 bit 0 clears), even when Z was held across the load."
    requirement: PLAY-01
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest -R ^player_slot_reanchor$ (generated joypad-mirror ROM)"
        status: pass
      - kind: integration
        ref: "ctest -R ^player_slot_mutant_no_rebase$ (main.c without the player_input_rebase call fails case reanchor with exit 1; also fails on the guest-visible check alone, press 84,264,008 half-dots ahead)"
        status: pass
  - id: D4
    description: "The slot message is shown through set_status; while a battery-save failure is active the title status reads the save status, a middle dot and the slot message; every operation prints one stderr line with the gbb_error; a load clears the audio backlog once, forces a redraw, restarts the .gbb cadence, keeps user_paused, and the next update_battery_save does not wipe the message."
    requirement: PLAY-01
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest -R ^player_slot_status_line$"
        status: pass
  - id: D5
    description: "The help dialog lists Select state slot: 1-9, Save state to slot: Command-S, Load state from slot: Command-L and Undo last load: Command-Z and contains the exact sentence once; the formatted message fits its 4096-byte buffer."
    requirement: PLAY-01
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest -R ^player_slot_help_text$"
        status: pass
  - id: D6
    description: "GBB_PLAYER_LIMITATIONS_TEXT keeps every prior sentence and appends the release-bound-slots sentence and the window-title, fullscreen and VoiceOver sentence; the literal in test_limitations.c is updated in step and the claims checkers that read the text still pass."
    requirement: PLAY-01
    human_judgment: false
    verification:
      - kind: unit
        ref: "ctest -R ^player_limitations$"
        status: pass
      - kind: integration
        ref: "ctest -R ^(cgb_speed_docs_no_stale_claims.*|phase8_player_contract.*|cgb_corpus_claims.*|cgb_hdma_claims_contract.*)$ (main suite, 10 of 10)"
        status: pass
      - kind: integration
        ref: "ctest -R ^player_claims_agree.*$"
        status: pass
  - id: D7
    description: "Research assumption A2 is resolved by a scan, not a manual step: the Cocoa main menu SDL creates (19 items) binds none of Command-S, Command-L or Command-Z, and a seeded Command-S item is detected with exit 1."
    requirement: PLAY-01
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest -R ^player_slot_menu_shortcuts$ (prints menu-shortcuts pass items=19)"
        status: pass
      - kind: integration
        ref: "ctest -R ^player_slot_menu_shortcuts_control$ (prints menu-shortcut-conflict s, exit 1)"
        status: pass
  - id: D8
    description: "The player suite is green end to end through the package gate and matches its inventory, and the main suite is green at the plan head after reconfiguring the revision-pinned tests."
    requirement: PLAY-01
    human_judgment: false
    verification:
      - kind: e2e
        ref: "bash tests/scripts/verify-phase3-player.sh --build-package (106 of 106 player_ tests, JUnit checked against tests/player/expected-tests.txt)"
        status: pass
      - kind: integration
        ref: "ctest --preset phase1 -j6 at 67bb2bdc: 1610 of 1610 after reconfiguring the pinned tests (1607 first pass, the three revision-pinned tests pass on rerun)"
        status: pass
duration: 26min
completed: 2026-10-29
status: complete
---

# Phase 18 Plan 06: Player Slot Wiring Summary

**The SDL player now saves, loads and undoes numbered state slots from the keyboard (digits, Command-S, Command-L, Command-Z) through the real event pump: input is re-anchored at the restored clock so a key pressed after loading an earlier- or later-time state reaches the guest within a frame, Command-S and Command-R no longer hit the battery save and reset, and the macOS menu is machine-checked not to steal the chords.**

## Performance

- **Duration:** about 26 min
- **Started:** 2026-10-29T04:11Z
- **Completed:** 2026-10-29T04:38Z
- **Tasks:** 3 (tracer, two auto), each with a RED commit and a GREEN commit
- **Files modified:** 9 (2 created, 7 modified, excluding planning files)

## Accomplishments

- **Slot keys in the event loop.** `handle_key` fills a `player_slot_key_input` (digit from the scancode, letter from the keycode, modifiers, `blocked = dialog_pending`) and calls `player_slot_key_decode` before the bare R and S branches; both bare branches gained `!command`. The transition early-return already covers the save-failure prompt, so the decoder never sees one. `handle_slot_key` selects, saves, loads and undoes, shows the D-25 message and prints the stderr line. Nothing on the slot path touches `user_paused`.
- **Slot store attachment.** `slots_attach` runs after every successful ROM load (startup and replacement): pref-directory descriptor, the digest the session already computed, the created profile, and a bounded no-follow re-read of the ROM bytes that must hash to that digest. Failure leaves slots off with a stderr line and a status message instead of binding states to the wrong game.
- **Input re-anchor (D-24).** `player_input_rebase` sets cursor and anchor to the restored clock directly (reconcile refuses to move the cursor back), seeds the pending mirror from the restored queue at `last_queued`, lets go of every key and gamepad button, keeps the pause flag and the gamepad table, and marks all eight buttons for release. If a clock ever arrived with more than 56 queued events it resets instead of queuing past 64.
- **`apply_slot_load`.** Rebase, queue the eight releases at the same host time (landing at `max(now, last queued)`), clear audio, force a redraw, restart the `.gbb` cadence. No RTC catch-up, no `user_paused` assignment.
- **Guest-visible proof.** On a generated joypad-mirror ROM, loading an earlier-time and then a later-time slot is followed by a no-key control frame (A stays released) and a Z keydown timed 8 half-dots after the cursor; the press is scheduled within one frame and SRAM byte 0 bit 0 clears. Z is held across the second load to prove the load lets go of it. The expected state after a load is built independently (slot bytes plus the eight releases).
- **Status line and log.** The title reads `<save_status> · <slot message>` while a battery-save failure is active; `Battery RAM changed` no longer wipes the message a load just produced.
- **Help and limitations.** Four slot key lines and the exact battery-replacement sentence in the help; two appended limitation sentences (release-bound slots; title status hidden in fullscreen and not announced by VoiceOver), pinned byte-for-byte by `player_limitations`.
- **A2 resolved by a check.** The SDL Cocoa main menu has 19 items and none binds Command-S, -L or -Z; the seeded control is caught.

## Task Commits

1. **Task 1 (tracer): Command-S then Command-L through the real SDL event pump, with Command guards on R and S** - `905cbd9b` (test, RED: `FAIL keys ... slots_ready`) then `22905c93` (feat, GREEN)
2. **Task 2: post-load input rebase, status combination, stderr line, two mutants** - `a7d4b076` (test, RED: reanchor fails at the cursor assertion, status_line at the combined title, keys at the post-load state) then `dd0cfd43` (feat, GREEN, five tests pass)
3. **Task 3: help text, limitations, menu-shortcut scan** - `20e4a0d2` (test, RED: help_text and player_limitations fail) then `71fb4e3e` (feat, GREEN) then `c92d1163` (test: the A2 scan and its control, which passed on arrival because they test SDL, not the player) then `67bb2bdc` (test: force the cocoa driver, see deviation 5)

**Plan metadata:** recorded in the following docs commit.

## Decisions Made

- **Own field for the slot message.** The title shows `save_status` instead of `status` while `save_status_active`, so a message composed into `app->status` would be invisible exactly when D-25 wants it combined. `slot_message` is set by `set_slot_status` and cleared by any later `set_status`.
- **Releases through the existing path.** `player_input_rebase` has the plan's three-argument signature and so cannot queue; it sets `release_pending_buttons = 0xFF` and `apply_slot_load` calls `player_input_retry_focus_releases`. A queue that cannot take them yet is retried by the main loop every frame, and a paused player retries on resume, exactly as for focus loss.
- **ROM bytes re-read, digest-checked.** The session keeps no ROM bytes; `host_save_io_read_bounded(AT_FDCWD, ...)` reads them again and `player_session_identify_rom` must reproduce the session's digest.
- **A2 by scan, not by limitation (plan deviation 5).** RESEARCH recommended documenting the possible menu clash; this plan instead proves the menu binds none of the chords and carries a control that proves the scanner can see a clash. The limitation sentence is for the title status only.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] A load's status was wiped on the next frame**
- **Found during:** Task 2 design (reading `update_battery_save`)
- **Issue:** a load leaves the battery different from the last `.gbb` save, so the next `update_battery_save` replaced the slot message with `Battery RAM changed; progress is in memory until saved` about a millisecond later, defeating D-25.
- **Fix:** that hint is skipped while a slot message is displayed; the autosave or any other event still replaces the message.
- **Files modified:** `src/player/main.c`
- **Verification:** `player_slot_status_line` calls `update_battery_save` after a load and asserts the title still reads `Loaded slot 2`.
- **Commit:** `dd0cfd43`

**2. [Rule 3 - Blocking] Other main.c embedders and the build need the slot and host libraries**
- **Found during:** Task 1 RED build
- **Issue:** `main.c` now includes `slots.h` and `gbb_host.h`; `test_player_reset_transition` embeds `main.c` and failed to find the host header.
- **Fix:** it links `gabbaboy_player_slots` and `gabbaboy_host`.
- **Files modified:** `tests/player/CMakeLists.txt`
- **Verification:** `player_reset_transition` passes; the 106-test player suite passes.
- **Commit:** `905cbd9b`

**3. [Rule 1 - Bug] The package lane's dummy video driver hid the Cocoa menu**
- **Found during:** tail gate, first `--build-package` run (104 of 106 passed)
- **Issue:** `verify-phase3-player.sh` exports `SDL_VIDEO_DRIVER=dummy`; with it the scan found no main menu and exited 3 (my local run had used the default driver).
- **Fix:** the scan overrides the driver with `SDL_SetHintWithPriority(... SDL_HINT_OVERRIDE)` and exits 3 with a `menu-shortcuts blocked` line when the driver is not cocoa. This is the plan's stop-and-report path made explicit, and it did not trigger here.
- **Files modified:** `tests/player/test_menu_shortcuts.c`
- **Verification:** both menu tests pass with `SDL_VIDEO_DRIVER=dummy` exported; the second `--build-package` run passed 106 of 106.
- **Commit:** `67bb2bdc`

### Plan wordings that met in practice (recorded discretion)

**4. `player_input_rebase` cannot queue releases itself.** See Decisions Made; the observable behaviour (eight releases at `max(now, last queued)`, queued in the core) is asserted by comparing the live state with slot bytes plus those eight events.

**5. A2 resolved by an automated scan instead of RESEARCH's limitation recommendation** (the plan's recorded deviation 5). Result: the SDL main menu has 19 items, no Command-S, -L or -Z key equivalent; the seeded control prints `menu-shortcut-conflict s` and exits 1.

**6. Unavailable-slots message.** When the pref directory or ROM cannot back a store, a slot key shows `State slots are unavailable for this ROM`, the one string not in the D-25 table (like 18-05 deviation 4), and a stderr line names the reason. It is unreachable in the tests.

**7. Reanchor uses one player instance.** The plan loads a later-time state saved by a second instance; here slot 4 is saved at T2 by the same player, and the earlier load (to T1) is followed by a load of slot 4 (T1 plus a few frames to T2), which is a later-time load of the same shape. Z is held across it, which a second instance would not have added.

**8. Cosmetic.** The RED commit `a7d4b076` message shows a literal `\xc2\xb7` for the middle dot; the code uses the byte escape correctly.

---

**Total deviations:** 3 auto-fixed (1 bug, 1 blocking, 1 bug in a new test), 5 recorded wording and discretion notes
**Impact on plan:** no scope change. Files outside `files_modified`: none.

## Evidence Recorded for the Acceptance Criteria

- Task 1: `player_slot_keys` passes; `grep -c player_slot_key_decode src/player/main.c` prints 1 and the call precedes the bare R branch; both bare branches contain `!command` (lines of `src/player/main.c`: `... && !command && key->scancode == SDL_SCANCODE_R` and `... SDL_SCANCODE_S`). RED log `build/18-06-task1-red.log`.
- Task 2: `ctest -R '^player_slot_(keys|reanchor|status_line|mutant_no_rebase|mutant_command_guard)$'` runs 5 and passes (`build/18-06-task2-mutants.log`). Direct runs of the variants (`build/18-06-task2-mutant-reasons.log`): the no-rebase variant prints `FAIL reanchor ... guest_cursor_half_dots == want_now ...`; with that state check temporarily removed it still fails on the guest-visible check (`the press is scheduled 84264008 half-dots ahead, more than one frame`) and the unmutated player passes the same reduced test; the command-guard variant prints `FAIL keys ... after_reset_key == undone`. `apply_slot_load` contains no assignment to `user_paused`.
- Task 3: `ctest -R '^(player_slot_(help_text|menu_shortcuts|menu_shortcuts_control)|player_limitations)$'` passes; the scan prints `menu-shortcuts pass items=19`, the control prints `menu-shortcut-conflict s` with exit 1; `git diff -U0 src/player/limitations.h` is one changed line and the old line is a strict prefix of the new one (230 bytes appended); the help sentence occurs once in `main.c`. Main-suite claims checkers: `cgb_speed_docs_no_stale_claims*`, `phase8_player_contract*`, `cgb_corpus_claims*`, `cgb_hdma_claims_contract*` pass 10 of 10 (`build/18-06-claims.log`).
- Tail gate: `bash tests/scripts/verify-phase3-player.sh --build-package` ran twice (first run found deviation 3); the second run: 106 of 106 `player_` tests pass, inventory check passes, package smoke passes (`build/18-06-build-package.log`).
- Full main suite `ctest --preset phase1 -j6` at `67bb2bdc` (`build/18-06-full-ctest.txt`): 1607 of 1610 on the first pass; the three failures (`cgb_corpus_report_tracer`, `cgb_corpus_report_controls`, `state_fuzz_controls`) were the known revision-pinned tests on a tree configured at an older HEAD (`state fuzz control revision is not the current immutable HEAD`). After `cmake --preset phase1 -DGBB_STATE_PIN_BASE_REV=7c1f257dd47fec77380f410b93a488bb1a5695cd` they pass with `state_purity`, `state_pin_planning`, `state_portable_pins`, `release_lifecycle_controls` and `summary_coverage*` (13 of 13, `build/18-06-pinned-rerun.txt`). No core test was added or changed: 1610 total as after 18-05.
- Not run locally: the Linux ASan lane (the player is macOS-only) and the hosted CI job `macos-player-package`, which repeats the tail gate at the PR head. The A2 scan needs a Cocoa-capable session on that runner; if it ever reports `menu-shortcuts blocked`, that is the owner decision the plan describes.

## Issues Encountered

- The player inventory file is read with `file(STRINGS)`, which adds no configure dependency: after editing `tests/player/expected-tests.txt` alone the build tree keeps the old test list until `tests/player/CMakeLists.txt` is touched. Not changed (outside this plan); a fresh configure, as in CI, is unaffected.
- `player_reset_transition` runs in about 0.01 s; that is the existing behaviour of the case and unrelated to this plan.

## Known Stubs

None.

## Threat Flags

None. T-18-19 (Command chords reaching the battery save or reset) is mitigated by decode-before-bare-keys, the `!command` guards and the command-guard mutant; T-18-20 (stuck input after a load) by `player_input_rebase`, the no-rebase mutant and the earlier- and later-time cases; T-18-21 (silent failure) by a status message and a stderr line with the `gbb_error` on every operation. The re-read of the ROM is a no-follow, regular-file, size-capped read of the path the user opened and is digest-checked, so it adds no new trust boundary.

## Next Phase Readiness

- Next plan: 18-07 (parallel-safe with this plan: no main inventory, root CMake or workflow file was touched here). Remaining in the phase: 18-07 through 18-09.
- PLAY-01 player surface is complete; the closing traceability lands with 18-09. `.planning/config.json` was left untouched.

## Self-Check: PASSED

- FOUND: tests/player/test_slots.c, tests/player/test_menu_shortcuts.c, src/player/input.c (player_input_rebase), src/player/main.c (apply_slot_load, handle_slot_key, format_help_message)
- FOUND commits: 905cbd9b, 22905c93, a7d4b076, dd0cfd43, 20e4a0d2, 71fb4e3e, c92d1163, 67bb2bdc

---
*Phase: GB-18-player-save-slots-and-host-contract*
*Completed: 2026-10-29*
