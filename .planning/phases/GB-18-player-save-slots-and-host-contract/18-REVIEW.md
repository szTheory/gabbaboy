---
phase: GB-18-player-save-slots-and-host-contract
reviewed: 2026-10-29T00:00:00Z
depth: standard
files_reviewed: 38
files_reviewed_list:
  - src/host/gbb_host.h
  - src/host/host_run.c
  - src/host/host_save_io.c
  - src/host/host_basename.c
  - src/host/host_cadence.c
  - src/host/host_signal.c
  - src/host/host_exit.h
  - src/host/host_save_format.c
  - src/player/slots.c
  - src/player/slots.h
  - src/player/main.c
  - src/player/input.c
  - src/player/input.h
  - src/player/limitations.h
  - src/runner/main.c
  - include/gabbaboy/gabbaboy.h
  - src/core/gabbaboy.c
  - tests/scripts/host_fixture.py
  - tests/scripts/test_host_mode.py
  - tests/scripts/test_host_signals.py
  - tests/scripts/test_installed_host.py
  - tests/scripts/verify-host-contract.py
  - tests/scripts/verify-no-interop-claims.py
  - tests/scripts/verify-save-formats.py
  - cmake/CheckCoreNoHostClock.cmake
  - cmake/CheckHostApiSymbols.cmake
  - cmake/CheckRunnerSourcesQualified.cmake
  - cmake/VerifyDocContract.cmake
  - CMakeLists.txt
  - tests/cmake/host.cmake
  - tests/cmake/slots.cmake
  - tests/cmake/save-formats.cmake
  - tests/cmake/host-contract.cmake
  - tests/cmake/input-clock.cmake
  - tests/test_save_format_completeness.c
  - tests/test_host_save_io.c
  - tests/test_slots.c
  - tests/player/test_menu_shortcuts.c
findings:
  critical: 0
  warning: 6
  info: 9
  total: 15
status: issues_found
---

# Phase 18: Code Review Report

**Reviewed:** 2026-10-29
**Depth:** standard
**Files Reviewed:** 38
**Status:** issues_found

## Summary

The atomic writer (`host_save_io_replace`), bounded readers, signal path, stem validator, cadence state machine,
slot load and input re-anchor were traced line by line. No exploitable defect was found in the shipped C code:

- Writer ordering is correct (temp O_EXCL|O_NOFOLLOW, write, fsync once and never retried, close checked, target
  lstat, `renameat`, dir fsync), and every failure before the rename unlinks the temp and preserves `errno`.
- Bounded reads never size an allocation from `st_size`. `want + 1` and `state_size + 1` cannot overflow for the
  callers' bounded inputs.
- The signal handler touches only a `volatile sig_atomic_t`. `SA_RESETHAND` plus the polled flag is sound, and the
  non-retried `nanosleep` is correct.
- `player_slot_load` really is validate-in-scratch, then preload, then live load, then undo, with a rollback.
- `player_input_rebase` plus `retry_focus_releases` schedules releases at `max(now, last_queued)`, which the core
  admits.

The findings below are robustness and data-safety weaknesses (ignored rollback and clock results, an unswept temp
class, a clobbered backup, file-mode loss) and test-infrastructure checks that can pass when they should not. There
are no BLOCKERs.

## Warnings

### WR-01: Rollback and post-load clock results are ignored, so "nothing changed" can be false

**File:** `src/player/slots.c:239` and `src/player/slots.c:250`
**Issue:** When the undo write fails (step 5) the live machine has already been replaced by the slot (step 4). The
code rolls back with `(void)gbb_load_state(instance, snapshot, state_size);` and then reports `BACKUP_FAILED` with the
message "nothing changed". If that rollback load ever fails, the machine is left in the loaded state while the user
and the log are told it was not touched. This breaks the all-or-nothing claim exactly on the path that exists to
guarantee it.

Separately, `(void)gbb_get_input_clock(instance, &result.clock);` discards the result. On failure `result.clock`
keeps `struct_size` set and everything else zero. `apply_slot_load` then calls `player_input_rebase` with
`now_half_dots == 0`, which places the cursor and anchor at time 0 on a machine that is far past it. Every queued
release is then older than the core's clock and is rejected, `release_pending_buttons` stays `0xFF`, and
`player_input_key` silently swallows all input until the main loop's recovery pauses the player.

**Fix:**
```c
    if (host_save_io_replace(store->dirfd, undo_name, snapshot, state_size) != HOST_IO_OK) {
        const gbb_error rollback = gbb_load_state(instance, snapshot, state_size);
        result.outcome = PLAYER_SLOT_BACKUP_FAILED;
        result.error = rollback == GBB_OK ? GBB_OK : (int)rollback; /* surface a failed rollback */
        goto done;
    }
    ...
    result.error = (int)gbb_get_input_clock(instance, &result.clock);
    if (result.error != GBB_OK) { result.outcome = PLAYER_SLOT_REFUSED; goto done; }
```
Also give a distinct message when the rollback failed, so the text never says "nothing changed" for a machine that did.

### WR-02: Slot, undo and preload temp files are never swept after a crash

**File:** `src/player/slots.c:115`, `:221`, `:238` (writers); the only sweep is `src/host/host_save_io.c:250` and is stem-scoped
**Issue:** `host_save_io_replace` leaves `.<prefix>-slotN.gbbs.tmp-<pid>-<seq>`, `.<prefix>-undo.gbbs.tmp-...` and
`.<prefix>-battery-preload.bin.tmp-...` behind when the process dies between the temp create and the rename (SIGKILL,
power loss, crash). Only host mode calls `host_save_io_sweep`, and it matches only `.<stem>.sav.tmp-`. The player never
sweeps, so a crash-during-save leaves state-sized files in the pref directory permanently. That is unbounded
accumulation of up to roughly 3 files per crash, each a full state or battery image. AGENTS.md asks for bounded work
and no stale partial artefacts.
**Fix:** In `slots_attach`, after the store is initialised, sweep this store's prefix. Generalise
`host_save_io_sweep` to take a literal prefix, or add `player_slot_store_sweep(store)` that unlinks names starting
with `.<store->prefix>-` and containing `.tmp-`. Run it once per ROM attach, before any slot key is accepted.

### WR-03: The battery preload backup is clobbered by the first load of every new session

**File:** `src/player/slots.c:123-125`, `:210-226` (the `guard_valid` logic)
**Issue:** The "have I already backed up the in-game save" guard lives only in memory (`store->guard_valid` starts
false on every `player_slot_store_init`). Scenario: session 1 starts with in-game save X. The user loads a slot, so
`preload = X` and the battery becomes Y, which autosaves to the `.gbb`. Session 2 starts with battery Y. The first
slot load sees `!guard_valid`, treats Y as unbacked, and overwrites `preload` with Y. X, the user's real progress,
is now unrecoverable, replaced by a copy of data that already exists in the slot file. The help text promises
"Loading also replaces the game's battery save"; it does not promise that the only backup is destroyed by a later
session.
**Fix:** Do not overwrite an existing preload with a battery that is not an in-game save. Options: (a) rotate
two generations (`-battery-preload.bin` becomes `-battery-preload.prev.bin` before the write); (b) persist the guard
(a digest of the last battery the slot engine wrote or loaded) beside the preload and seed `store->guard` from it at
attach; (c) skip the write when the battery equals the content of the existing preload or of any slot file. Add a test
case that spans two `player_slot_store_init` calls.

### WR-04: The save-format and contract checkers read the configure-time HEAD, so they can pass against a stale revision

**File:** `tests/cmake/save-formats.cmake:13-24` and the tests built on `GBB_SAVE_FORMATS_REV` (`:61`, `:77`, `:90`, `:96`, `:109`, `:122`)
**Issue:** `GBB_SAVE_FORMATS_REV` is resolved once by `execute_process(git rev-parse HEAD)` during configure. If a
developer or agent edits `docs/host-contract.json` or `host_save_format.c`, commits, and re-runs `ctest` without
reconfiguring (the common loop), the checker keeps reading `git show <old-rev>:docs/host-contract.json` while the
runner under test is built from the new working tree. The result is a false green or false red that reports
`rows=16 ...` for the wrong tree. The file's own comment concedes "a configure from before the commit checks the
previous revision". The gate for the append-only id freeze is exactly the kind of check that must not be stale.
**Fix:** Pass the symbolic revision and let the script resolve it at run time. The scripts already accept any
`git show REV:path` revision, so use `--rev HEAD`. Alternatively add
`set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS "${PROJECT_SOURCE_DIR}/.git/HEAD")` so a new commit
forces reconfigure. Keep the explicit-SHA form only for boundary-commit runs.

### WR-05: The writer replaces an existing `.sav` with mode 0600, silently dropping its permissions

**File:** `src/host/host_save_io.c:198`
**Issue:** The temp is created with mode `0600`, and `renameat` then makes it the target. A save that was `0644` or
`0664` (group-shared, or read by a supervisor or backup process under another uid) becomes owner-only after the
first flush. The writer neither preserves the target's mode nor documents the change. A host that deliberately shares
the save directory across users loses read access with no error.
**Fix:** When the target exists, `fstatat` already runs for the type check (`:224`). Capture `target.st_mode & 07777`
there and apply `fchmod(fd, mode)` to the temp before the rename, which needs the fstatat moved before the write; or
document in `docs/host-contract.json` and the guide that published saves are 0600 and add a test. Prefer
preservation.

### WR-06: The no-interop-claims scan is easy to evade and can be satisfied vacuously for a rewritten claim

**File:** `tests/scripts/verify-no-interop-claims.py:36` and `:58-60`
**Issue:** `PATTERN = (byte-identical|compatible|interoperab)[^.\n]*mGBA` cannot cross a period or a newline. Hard-wrapped
Markdown puts "compatible with" and "mGBA" on adjacent lines, and a `.sav` token ("compatible with the .sav format of
mGBA") is a period. Both defeat the scan. The same pattern also rejects legitimate disclaimers ("GabbaBoy saves are not
compatible with mGBA"), which pushes authors toward evasive wording. The seeded control proves only that the exact
original sentence is caught, not that the pattern generalises.
**Fix:** Scan the text with whitespace collapsed (`re.sub(r"\s+", " ", text)`) per file and use a class that allows dots,
for example `(byte-identical|compatible|interoperab)[^\n]{0,80}mGBA`. Pair it with an allow-list of explicit negative
phrases ("no byte interoperability with") so disclaimers pass. Add controls for a wrapped claim and a `.sav`-bearing claim.

## Info

### IN-01: `host_save_io_sweep` unlinks while iterating `readdir`

**File:** `src/host/host_save_io.c:262-265`
**Issue:** POSIX leaves it unspecified whether entries removed after `opendir` or `rewinddir` are skipped or returned,
and some network and FUSE filesystems skip following entries after an unlink. A stale temp can survive a sweep.
**Fix:** Collect matching names into a bounded array first (a cap, for example 64, with a "more remain" count), close the
directory, then `unlinkat` each.

### IN-02: The replace name cap does not guarantee the temp name fits NAME_MAX

**File:** `src/host/host_save_io.c:187`
**Issue:** The name is capped at 240 bytes, but the temp is `.` + name + `.tmp-` + up to 7 pid digits + `-` + seq, up
to about 256 bytes. A 240-byte name would hit `ENAMETOOLONG` and report `temp`. Current callers (stems of 200 bytes or
fewer, fixed slot names) are safe.
**Fix:** Cap at 255 minus the fixed overhead, for example `name_len > 215`, or derive the cap from `GBB_HOST_STEM_MAX_BYTES + 4`.

### IN-03: `player_input_rebase` early return leaves the mirror empty and a press unreleased

**File:** `src/player/input.c:87`
**Issue:** When `queued_count > 56` the function returns after setting only cursor and anchor. `pending_count` stays 0,
`release_pending_buttons` stays 0, and the core's queue still holds up to 64 events. Subsequent key events would overrun
the real queue, and a restored press without a release could stay held. This is unreachable through the slot engine,
which refuses such clocks, but the function is a public header API.
**Fix:** In that branch mark `release_pending_buttons = 0xFF` and `held_buttons = 0xFF`, set `paused = true`, and return a
`bool` (or document that the caller must have validated), so the failure is loud rather than silent.

### IN-04: A non-canonical MBC2 save is rewritten even when the guest never writes, and import failures are mislabelled

**File:** `src/host/host_run.c:327` and `:392-395`
**Issue:** `gbb_import_battery` normalises MBC2 RAM to `0xF0 | nibble`. `flush_battery` compares the exported (canonical)
image against the raw imported bytes, so a `0x0N`-style MBC2 `.sav` differs and is rewritten at the final flush with
`flush=written` although nothing changed semantically. Separately, any `gbb_import_battery` failure is reported as
`save-rtc-block`, even though the function can also fail for reasons other than the clock block.
**Fix:** After a successful import, re-export into `imported` (`gbb_copy_battery`) so the baseline is the canonical image,
or document the one-time normalisation. Choose the refusal token by the returned `gbb_error`.

### IN-05: Slot selection text follows neither the loader's symlink rule nor its regular-file rule

**File:** `src/player/slots.c:434`
**Issue:** `player_slot_format_selection` uses `fstatat(..., AT_SYMLINK_NOFOLLOW)` and prints "saved <time>" for any
existing entry. A symlink or directory in a slot position shows as saved, but `player_slot_load` refuses it with
`READ_FAILED`.
**Fix:** Print "empty" only for `ENOENT`, and print "saved" only when `S_ISREG(info.st_mode)`; for anything else use a
neutral "unreadable" wording.

### IN-06: A failed monotonic clock silently turns paced mode into a full-speed loop

**File:** `src/host/host_run.c:256` and `:274`
**Issue:** If `clock_gettime` fails, `pacer->valid` is cleared and `pacer_wait` returns immediately forever, so a paced
runner burns CPU and the emulated clock runs far ahead of real time. There is no diagnostic.
**Fix:** On clock failure print one `gbb-host: pacing unavailable` line and stop the run with `GBB_HOST_EXIT_FAILURE`, or
fall back to `nanosleep` of `GBB_HOST_FRAME_NS`.

### IN-07: The `term` signal row uses a wall-clock ceiling as evidence, against project policy

**File:** `tests/scripts/test_host_signals.py:235-238`
**Issue:** AGENTS.md says "No quotas, clocks or run counters as evidence". The row asserts `elapsed < 2.0 s` from
`sent_at` to `reaped_at`. The docstring acknowledges the exception, but on a loaded shared runner a scheduler stall
could fail a correct runner, and it can never prove the 2 s bound on other hardware.
**Fix:** Drop the timing assertion and keep the boundary-frame replay equality, which is the real evidence. If the
Playstead 2 s contract matters, assert the structural property instead (a stop is honoured at the next frame boundary,
at most one frame later) using frame counts.

### IN-08: Hard-coded counts in PASS_REGULAR_EXPRESSION fight the append-only table

**File:** `tests/cmake/save-formats.cmake:64`, `:80`, `:99`; `tests/cmake/host-contract.cmake:207`; `tests/scripts/verify-host-contract.py:291`
**Issue:** The contract is append-only by design (D-19), but `rows=16 ids=12 files=32`, `rows=16`, `exit_rows=4
format_rows=16` and `exit_codes=4 cadence=6` are literals. Adding a legitimate row or exit code makes unrelated
checkers fail until each literal is edited.
**Fix:** Derive the expected counts from the JSON in the test (print `rows=N` and compare to the parsed length), or
match `rows=[1-9][0-9]*`, since the structural checks already pin correctness.

### IN-09: Stale and duplicated comment, and directory fsync asymmetry on macOS

**File:** `tests/cmake/slots.cmake:6` and `:69`; `src/host/host_save_io.c:242`
**Issue:** The comment fragment "registers is removed from the Windows expectation in BOTH ..." is duplicated mid-file
(lines 69-72) without its subject, which is a leftover from an edit. Separately, the file sync prefers `F_FULLFSYNC`
on Apple platforms, but the directory sync is a plain `fsync(dirfd)`, so the rename gets a weaker durability guarantee
than the data. This is acceptable under the "process death only" contract, but the asymmetry is undocumented.
**Fix:** Delete the orphaned comment lines. Add one comment at `:242` stating that directory durability is best effort
and power-loss is out of contract, or route the directory through `sync_file`.

---

_Reviewed: 2026-10-29_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
