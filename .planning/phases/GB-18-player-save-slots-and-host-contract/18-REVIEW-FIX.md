---
phase: GB-18-player-save-slots-and-host-contract
fixed_at: 2026-10-29T00:00:00Z
review_path: .planning/phases/GB-18-player-save-slots-and-host-contract/18-REVIEW.md
iteration: 1
findings_in_scope: 6
fixed: 6
skipped: 0
status: all_fixed
round_2_iteration: 2
round_2_fixed_at: 2026-10-29T11:13:23Z
round_2_scope: IN-01..IN-09
round_2_findings_in_scope: 9
round_2_fixed: 9
round_2_skipped: 0
round_2_status: all_fixed
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

**Status:** fixed (owner accepted pausing input on RESTORE_FAILED)
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

**Status:** fixed (owner accepted the design)
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
**Owner decision (2026-10-29):** the third pref-dir file per ROM and profile is accepted. The residual path was
closed in a follow-up (e94174e3): a failed guard write no longer passes silently. The load still applies, `guard_unsaved`
is set and the status message warns that the in-game save backup may be replaced next session.
`slot_guard_write_failure` (a directory at the guard's name makes the write fail) and its control
`slot_mutant_guard_failure_silent` cover it.

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

## Round 2 (Info findings)

**Fixed at:** 2026-10-29T11:13:23Z
**Iteration:** 2 (review-fix round 2 of at most 2)
**Scope:** IN-01..IN-09. WR-01..WR-06 were not touched.

**Summary:** 9 in scope, 9 fixed, 0 skipped. Two findings were only partly applied as written: IN-04 part (b) and the
stat-failure row of IN-05. The reasons are in the notes below. One commit per finding on the phase branch. Each
behaviour change has a CTest-wired check with a negative control. Every new name is in `tests/expected-tests.txt`
(or `tests/player/expected-tests.txt`). POSIX-only names are also removed from the Windows expectation in
`cmake/ExpectedTests.cmake` and `.github/scripts/verify-test-inventory.sh`. No new TIMEOUT was added, and the core was
not touched.

| Id | Status | Commit | Test | Negative control |
|---|---|---|---|---|
| IN-01 | fixed | 84e20cdc | `host_sweep_batches`: 150 temps (more than two 64-name batches) are all removed, non-matching names are kept, and 65 unremovable temp-named directories end the sweep | `host_writer_mutant_sweep_single_pass` (stops after the first pass) must fail |
| IN-02 | fixed | 4515a548 | `host_writer_name_cap`: a name at `GBB_HOST_REPLACE_NAME_MAX` (204) is written; cap+1 and 240 are refused with EINVAL and leave the directory empty | `host_writer_mutant_name_cap_240` (old 240-byte cap) must fail |
| IN-03 | fixed | 6c0a3c65 | `player_input_rebase_guard` (player build): safe (56 events) re-anchors; unsafe (60, 200) returns false, pauses input, keeps the mirror counted (clamped to 64) and the releases pending; no key reaches the core queue; resume is refused | `player_input_mutant_rebase_silent` (old silent early return, in a copy of input.c) must fail |
| IN-04 | fixed (part a; part b not changed, see note) | 8332aab1 | `host_import_mbc2_noncanonical`: a `$0N`-style 512-byte MBC2 `.sav` with an idle guest gives `flush=unchanged`; bytes, inode and mtime are kept | `host_import_mutant_raw_baseline` (raw-file baseline) must fail with "a non-canonical MBC2 save was rewritten" |
| IN-05 | fixed (stat-failure row kept per D-25, see note) | a312201a | `slot_select_message` extended: a dangling symlink (slot 6) and a directory (slot 7) read "Slot N selected: unreadable", and loading either gives READ_FAILED | `slot_mutant_selection_any_entry` (no regular-file check) must fail |
| IN-06 | fixed | c125cc80 | `host_exit_pacing_unavailable`: a fault-variant runner whose clock fails from the third pacing wait ends by itself with one `gbb-host: pacing unavailable` line, `exit status=failure reason=pacing`, a written flush, exit 1 and a `--frames K` replay of the same bytes | `host_signal_decoy_pacing_ignored` (same fault, result ignored) must fail the watchdog with "the runner kept running after its pacing clock failed" |
| IN-07 | fixed | 3eeec7da | none new: the 2.0 s kill-to-wait assertion, its constant, the timestamps and the `--sanitized` flag that only toggled it were removed; `host_signal_term` keeps the replay-equality evidence | existing `host_signal_decoy_partial_frame` (stops mid-frame) still fails on the replay comparison |
| IN-08 | fixed | a87cfd37 | the pass patterns of `save_format_files`, `save_format_completeness`, `host_contract_json` and `host_contract_docs` accept any positive count (cadence=6 and profiles=2 stay pinned); `host_contract_controls` requires the derived pass line and gains the control "an appended exit row" (exit_codes=5), now controls=11 | against the old pinned literal the appended-row control fails ("expected exit_codes=4 ... got exit_codes=5"), shown by hand on a scratch copy of the checker; the existing reject controls (missing crash row, renumbered row, empty rows list) still fail |
| IN-09 | fixed | b7589dfa | comment-only (orphaned slots.cmake lines deleted; dir-sync asymmetry documented at the directory fsync) | n/a |

**Notes and decisions:**

- **IN-01:** On the local filesystem (APFS) an unlink during readdir does not cause entries to be skipped, so that
  hazard cannot be reproduced here. The test covers the collect-then-unlink batching the fix introduces. A pass that
  fills the buffer and removes something is followed by another pass. A pass that removes nothing ends the sweep, so
  the work is bounded. The `host_save_io_sweep` signature is unchanged.
- **IN-02:** The cap is derived (`GBB_HOST_STEM_MAX_BYTES + 4`). Two `_Static_assert`s check that the worst-case temp
  name (a 20-byte pid and a two-digit sequence) fits in 255. All current callers are inside the cap: host stems are at
  most 204 bytes and slot names about 88.
- **IN-03:** `player_input_rebase` now returns `bool`. Its only caller, `apply_slot_load`, keeps the game paused when it
  returns false. The anchor of `player_slot_mutant_no_rebase` follows the new call site.
- **IN-04 part (b) was not changed.** The cartridge's battery presence and the exact file size are both checked before
  import, so the only refusal `gbb_import_battery` can return for those bytes is a malformed clock block
  (GBB_INVALID_ARGUMENT from `rtc_block_parse`). Mapping the other `gbb_error` values would add branches that no input
  can reach. I wrote that invariant next to the `save-rtc-block` refusal instead.
- **IN-05:** D-25 (18-CONTEXT.md) adopted the bare "saved" for an entry whose stat fails. The reviewer suggested
  replacing that row too. I kept it to respect the adopted decision and changed only the non-regular-entry case,
  which no decision covered. The cartridge guide now names the "unreadable" state.
- **IN-06:** I used the fail-closed option. Exit code 1's meaning now reads "I/O or flush failure, allocation failure,
  a failed pacing clock, or a core stop mid-run". It is changed together in `src/host/host_exit.h`,
  `docs/host-contract.json` and the guide table, and the checkers compare these cell by cell. The guide's paced-mode
  paragraph describes the stop. A clock that fails at start is caught at the first frame boundary. The fault variant
  and the decoy are build-tree `hostvariant` runners; nothing mutated is installed.
- **IN-07:** No clock remains as evidence in `test_host_signals.py`. `PROCESSORS 2` stays, so the watchdogs are not
  starved on a 4-wide hosted ctest.

**Verification (round 2):**

- **Where it ran:** the gates ran in the isolated review-fix worktree, in its own build directories, which I
  configured like the main checkout's. `build` is phase1 Debug with Ninja. `build-player` adds
  `GABBABOY_BUILD_PLAYER=ON` and the main checkout's SDL3 prefix. I did not rebuild the main checkout's `build` and
  `build-player`, because a full `ctest` was running in `build` when this pass started. After the fast-forward they
  still hold the pre-round-2 binaries and need `cmake --build build -j8` and `cmake --build build-player -j8` before
  the numbers can be reproduced there. The worktree has been removed.
- **phase1 (`build`):** `ctest -R '^host_|^slot_|^save_format|contract|^doc_|test_budget|inventory|summary_coverage|hygiene|no_host_clock|core_linkage|installed_|^unreleased|^readme|^cartridge_guide|^native_guide'`
  gave 243 of 243 passing at b7589dfa. The contract checkers read the committed HEAD, so they were run after each
  commit. One run before the IN-06 commit showed `host_contract_docs_missing_control` failing: it compared the edited
  working tree with the old HEAD (the documented commit-before-run rule), and it passed after the commit.
  `verify-test-inventory.sh --self-test` passed.
- **Player (`build-player`):** `ctest -R '^player_'` gave 108 of 108 passing, including `player_slot_*`,
  `player_input_rebase_guard` and `player_input_mutant_rebase_silent`. `test_budget` passed. `core_linkage_links` and
  `core_linkage_controls` still fail with the pre-existing player mutant-topology findings (RM-031, recorded in
  3b196457). None of the new round-2 targets appears in their output.
- I confirmed that each negative control fails for its own reason (the `FAIL <case>:` line or the named harness
  reason), not by crashing.
- **Not run:** the full 1,600+ test `ctest` at the new head, and `phase1-asan` (sanitizers are Linux-only).

---

_Fixed: 2026-10-29_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
_Round 2 fixed: 2026-10-29T11:13:23Z (iteration 2)_
