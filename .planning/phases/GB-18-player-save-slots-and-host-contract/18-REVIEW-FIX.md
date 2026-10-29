---
phase: GB-18-player-save-slots-and-host-contract
fixed_at: 2026-10-29T00:00:00Z
review_path: .planning/phases/GB-18-player-save-slots-and-host-contract/18-REVIEW.md
iteration: 1
findings_in_scope: 6
fixed: 6
skipped: 0
status: all_fixed
---

# Phase 18: Code Review Fix Report

**Fixed at:** 2026-10-29
**Source review:** .planning/phases/GB-18-player-save-slots-and-host-contract/18-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 6 (WR-01..WR-06; Info findings were out of scope for this pass)
- Fixed: 6
- Skipped: 0

Each fix is one commit on the phase branch. Every behaviour change has an automated check with a negative control
wired into CTest, and every new test name is in `tests/expected-tests.txt`, `cmake/ExpectedTests.cmake` and
`.github/scripts/verify-test-inventory.sh`.

## Fixed Issues

### WR-01: Rollback and post-load clock results are ignored, so "nothing changed" can be false

**Status:** fixed: requires human verification (error-handling logic)
**Files modified:** `src/player/slots.c`, `src/player/slots.h`, `src/player/main.c`, `tests/test_slots.c`,
`tests/test_slots_pure.c`, `tests/cmake/slots.cmake`, `tests/expected-tests.txt`, `cmake/ExpectedTests.cmake`,
`.github/scripts/verify-test-inventory.sh`
**Commit:** 95294c32
**Applied fix:** Added `PLAYER_SLOT_RESTORE_FAILED` (appended to the outcome enum). A refused rollback after a failed
undo write, and an unreadable input clock after a successful load, now return it with the `gbb_error`, instead of
`BACKUP_FAILED` / `LOADED`. The clock is zeroed in that case. The message is "<subject> could not be fully applied;
the game state may have changed" and the log token is `restore-failed`. The player pauses the game and its input on this
outcome (`handle_slot_key`), because its input mirror no longer matches the machine. The reviewer's suggestion of
returning `REFUSED` for an unreadable clock was not used: the load and the undo file had already been applied, so
`REFUSED` ("nothing changed") would have been false again.
**Tests:** the shipped engine cannot be made to refuse a snapshot it just produced, so `slot_fault_rollback_refused`
and `slot_fault_clock_unreadable` build the engine with the one call forced to fail and require `RESTORE_FAILED`, the
live state and the absence of "nothing changed". `slot_mutant_rollback_ignored` and `slot_mutant_clock_ignored` keep
the same fault and restore the old ignore-the-result handling; both must fail. `slot_mutant_no_rollback` was
re-anchored to the new rollback line. `gbb_slots_mutant` gained a `PASS` keyword for fault variants. The pure message
and log tables cover the new outcome.
**Reviewer should confirm:** the choice to pause the player on `RESTORE_FAILED` (an owner-facing behaviour).

### WR-02: Slot, undo and preload temp files are never swept after a crash

**Files modified:** `src/player/slots.c`, `src/player/slots.h`, `tests/test_slots.c`, `tests/cmake/slots.cmake`,
`tests/expected-tests.txt`, `cmake/ExpectedTests.cmake`, `.github/scripts/verify-test-inventory.sh`
**Commit:** 8014d1a8
**Applied fix:** `player_slot_store_init` now sweeps `.<rom digest>-<profile>-*.tmp-*` from the pref directory on
attach, before any slot key can be accepted. I put it inside init rather than in `main.c` so it cannot be forgotten
by a caller and is testable. The scan uses a duplicated descriptor and collects at most 32 names before `closedir`
(also avoiding the unlink-while-iterating hazard of IN-01), then `unlinkat`s them, so work is bounded and a symlink is
removed itself. It assumes one player per ROM and profile, as host mode does for its stem; this is documented at the
function. `host_save_io_sweep` was left alone (stem-scoped, and part of the checked host API surface).
**Tests:** `slot_stale_temp_sweep` covers swept names (slot, undo, preload, a high pid/seq, a symlink) and kept names
(other profile, other ROM, the player's `.gbb` temp, the real slot, a dot file without a temp marker, the symlink's
target). `slot_mutant_sweep_noop` and `slot_mutant_sweep_unscoped` must fail.

### WR-03: The battery preload backup is clobbered by the first load of every new session

**Status:** fixed: requires human verification (state-handling logic)
**Files modified:** `src/player/slots.c`, `src/player/slots.h`, `docs/cartridge-and-saves.md`, `tests/test_slots.c`,
`tests/cmake/slots.cmake`, `tests/expected-tests.txt`, `cmake/ExpectedTests.cmake`,
`.github/scripts/verify-test-inventory.sh`
**Commit:** cfc474a8
**Applied fix:** Reviewer option (b). The guard (the battery the engine last left in the machine) is persisted after
each load as `<prefix>-battery-guard.bin` through the atomic writer, and is read back with `host_save_io_read_exact`
on the first load of a session when no guard is held in memory (a missing or wrong-sized file just leaves the guard
invalid). The guard file is the full battery image (at most 128 KiB), so no digest code was added. A failed guard
write is ignored and only costs one extra preload write later; this is the one residual path to the old clobber and
is recorded in the code comment. The guide has one new sentence.
**Tests:** `slot_battery_guard_sessions` spans three `player_slot_store_init` calls: session 2's first load leaves the
preload at the real in-game save X, and a genuine in-game save W in session 3 is still backed up.
`slot_mutant_guard_not_persisted` and `slot_mutant_guard_not_seeded` must fail.
**Reviewer should confirm:** that persisting the guard in a third pref-dir file per ROM and profile is acceptable.

### WR-04: The save-format and contract checkers read the configure-time HEAD, so they can pass against a stale revision

**Files modified:** `tests/cmake/save-formats.cmake`, `tests/cmake/host-contract.cmake`,
`cmake/CheckContractRevWiring.cmake` (new), `tests/expected-tests.txt`
**Commit:** 0ea6f507
**Applied fix:** `GBB_SAVE_FORMATS_REV` is now a cache variable defaulting to the symbolic `HEAD`, which git resolves
when each test runs; `GBB_HOST_CONTRACT_REV` reuses it. A full SHA can still be pinned with
`-DGBB_SAVE_FORMATS_REV=<sha>` for a boundary-commit run (the point-in-time rule in AGENTS.md); an unresolvable value
still becomes `unknown` and fails closed. The scripts already accepted any `git show` revision, so they were not
changed. A new script, `cmake/CheckContractRevWiring.cmake`, reads the generated `CTestTestfile.cmake` and
requires each of ten checker tests to carry exactly the expected `--rev`.
**Tests:** `contract_rev_wiring` (ten checker tests wired on POSIX), `contract_rev_wiring_stale_control` (a file
carrying a 40-digit SHA must be rejected for "reads revision <sha>") and `contract_rev_wiring_missing_control`
(a missing test must be rejected). A pinned-SHA configure was also exercised by hand and passed, then reverted.
**Note:** other, unrelated tests in `tests/CMakeLists.txt` (e.g. `state_fuzz_controls`, `cgb_corpus_report_tracer`)
still capture the configure-time HEAD; they failed after the commits until the build directory was reconfigured. That
is the same class of problem but outside this finding.

### WR-05: The writer replaces an existing `.sav` with mode 0600, silently dropping its permissions

**Files modified:** `src/host/host_save_io.c`, `docs/native-integration.md`, `tests/test_host_save_mode.c` (new),
`tests/cmake/host.cmake`, `tests/expected-tests.txt`, `cmake/ExpectedTests.cmake`,
`.github/scripts/verify-test-inventory.sh`
**Commit:** 919fe641
**Applied fix:** Preservation, as preferred. Before the temp is created, `host_save_io_replace` takes the
`st_mode & 0777` of an existing regular target and applies it to the temp with `fchmod` (which ignores the umask).
Best effort and permission bits only: a filesystem that rejects the mode keeps the owner-only default, and owner and
group are not reproduced. I did not move the existing ETARGET `fstatat` (it stays after close so the fault-stage
order tests are unchanged); the new `fstatat` is only for the mode. The guide documents the behaviour.
**Tests:** `host_writer_preserve_mode` checks a fresh write (0600) and existing 0640, 0664, 0644 and 0400 targets. It
is its own small program (`test_host_save_mode`) so the mutant host library links without the fault seams.
`host_writer_mutant_no_preserve_mode` removes the `fchmod` and must fail.

### WR-06: The no-interop-claims scan is easy to evade and can be satisfied vacuously for a rewritten claim

**Files modified:** `tests/scripts/verify-no-interop-claims.py`, `tests/cmake/host-contract.cmake`
**Commit:** aea9eb6b
**Applied fix:** Each file is scanned with whitespace collapsed to single spaces, with keyword and mGBA in either
order within 80 characters and dots allowed. Five exact disclaimer phrases ("no save/byte interoperability with",
"not byte-identical to", "not compatible with", "not interoperable with") are removed first, so honest wording passes
while any other negation ("not only compatible with mGBA") is still a claim. The six published files and the Playstead
note scan clean at HEAD under the stricter rule.
**Tests:** the checker's own controls now run five seeded rejections (the original sentence, a hard-wrapped claim, a
`.sav`-bearing claim, mGBA-first, a partly negated claim) and one acceptance (the disclaimers); the CTest expects
`controls=6`. By hand I confirmed the checker fails with `control-accepted` under the old pattern and with
`control-rejected` when the disclaimer removal is dropped.

## Verification

Run in an isolated worktree on macOS (arm64), `phase1` configuration (`build/`), after the last commit and a
reconfigure:

- Full `ctest -j8` in the main configuration: 1659 tests. The first run showed 2 failures (`state_fuzz_controls`,
  `cgb_corpus_report_tracer`), both caused by a configure from before the commits; after `cmake build` and a rebuild
  both passed, and `-R state_` (248 tests) was 100%.
- All slot, host writer, save-format, host-contract and doc/planning tests passed individually after each fix, and
  `verify-test-inventory.sh --self-test` passed.
- Player configuration (`build-player`, SDL3 from the main checkout's prefix): `src/player/main.c` compiles and the
  slot and player tests pass. The full player ctest had 3 failures (`core_linkage_links`, `core_linkage_controls`,
  `test_budget`: the player mutant core-linkage topology and `player_slot_help_text` TIMEOUT 120 s over the 60 s
  budget). The same three tests fail identically on a worktree of the pre-fix base commit `72a88d97` configured the
  same way, so they are pre-existing and not caused by this pass.
- `phase1-asan` was not run: `GABBABOY_ENABLE_SANITIZERS` is supported only on Linux and this host is macOS.
- The gates ran in the isolated worktree, not the main checkout, and the numbers are not reproducible from the main
  checkout until the commits are fast-forwarded in and it is reconfigured.

---

_Fixed: 2026-10-29_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
