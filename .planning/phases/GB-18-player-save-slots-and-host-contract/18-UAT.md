---
status: complete
phase: GB-18-player-save-slots-and-host-contract
source: 18-01-SUMMARY.md, 18-02-SUMMARY.md, 18-03-SUMMARY.md, 18-04-SUMMARY.md, 18-05-SUMMARY.md, 18-06-SUMMARY.md, 18-07-SUMMARY.md, 18-08-SUMMARY.md, 18-09-SUMMARY.md
started: 2026-10-29T11:29:03.677298+00:00
updated: 2026-10-29T11:29:03.677298+00:00
---

## Automated Evidence

Phase 18 verification closed with no human checkpoint (DECISIONS D-069). Every deliverable below is copied from the coverage blocks of plan SUMMARYs 18-01..18-09, and every verification item is automated and passing. `tests/scripts/verify-uat-closure.py --write` wrote this closure, and its `--self-test` rejects weakened copies.

- Regression gate: at `70a29b29`, after a fresh configure, rebuild and refreshed install prefix, the full suite passed 1676/1676 (`build/18-gate-ctest-70a29b29.log`). The player build (`build-player`, `^player_|^test_budget`) passed 110/110.
- Phase verifier: `18-VERIFICATION.md` is a re-verification with status passed, score 4/4. Requirements PLAY-01 and HOST-01..03 are traced to plans and are Complete. The verifier read the round-2 diff `3b196457..70a29b29` and found no defect introduced.
- Code review: `18-REVIEW.md` found 0 critical, 6 warning and 9 info findings. All 15 are `fixed` in `18-REVIEW-DISPOSITION.md`: WR-01..06 in round 1 and IN-01..09 in round 2, which is the D-102 cap. Each behavioural fix has a test with a negative control.
- Found and fixed at verification: `test_budget` rejected six `player_slot_*` tests at TIMEOUT 120 (`135c6cc5`), and `planning_labels` rejected `host_signal_term` after IN-07 (`70a29b29`). See LESSONS GB-GSD-030.
- API coverage: `COVERAGE.md` passes the `api-coverage` verify-pre gate.
- Hosted evidence: exact-head CI for PR #132 is reconciled at the boundary and recorded in STATE.md and the continuation note, outside the verifier's covered files.
- Superseded wording: the criteria below are copied verbatim from the plan SUMMARYs, and round 2 later changed three of them. Test 51's 2.0 s kill-to-wait ceiling was removed by IN-07 (`3eeec7da`), because a clock is not evidence. The stop is now proven by exit 0 and a byte-equal `--frames K` replay. Test 40: a non-regular slot entry now reads `unreadable` (IN-05, `a312201a`), and the stat-failure row stays `saved` per D-25. Test 53: exit row 1 now also covers a failed pacing clock (IN-06, `c125cc80`). The current tests, `host_signal_term`, `slot_select_message` and `host_exit_pacing_unavailable`, pass in the 1676/1676 run.

Not passes: the player-build `core_linkage_links` and `core_linkage_controls` failures predate Phase 18 (present at the Phase 17 boundary `f4082a6`). No CI lane runs them. They are tracked as FUTURE-MILESTONES RM-031 and are not counted as Phase 18 evidence.

## Current Test

[testing complete]

## Tests

### 1. A real runner process imports an exact-size raw .sav, runs N fixed frames and atomically publishes the battery image; a second process continues from it (fresh 01, then 02, preloaded 41 then 42) with no temp left and no absolute path in diagnostics.
expected: "A real runner process imports an exact-size raw .sav, runs N fixed frames and atomically publishes the battery image; a second process continues from it (fresh 01, then 02, preloaded 41 then 42) with no temp left and no absolute path in diagnostics."
result: pass
source: automated
summary_file: 18-01-SUMMARY.md
coverage_id: D1
evidence: ["ctest -R ^host_continuation$ (tests/scripts/test_host_mode.py --scenario continuation)"]

### 2. The host ROM bound is the core's 8 MiB at both edges: an 8,388,608 B MBC5 ROM runs, 8,388,609 B is refused with rom-size (not rom-unsupported), and a missing ROM is refused with rom-unreadable.
expected: "The host ROM bound is the core's 8 MiB at both edges: an 8,388,608 B MBC5 ROM runs, 8,388,609 B is refused with rom-size (not rom-unsupported), and a missing ROM is refused with rom-unreadable."
result: pass
source: automated
summary_file: 18-01-SUMMARY.md
coverage_id: D2
evidence: ["ctest -R ^host_rom_max_size$", "ctest -R ^host_rom_oversize$", "ctest -R ^host_rom_unreadable$"]

### 3. The inventory bookkeeping keeps the POSIX-only host names out of the Windows expectation in both lists and the self-test proves it.
expected: "The inventory bookkeeping keeps the POSIX-only host names out of the Windows expectation in both lists and the self-test proves it."
result: pass
source: automated
summary_file: 18-01-SUMMARY.md
coverage_id: D3
evidence: ["bash .github/scripts/verify-test-inventory.sh --self-test"]

### 4. The runner dispatch did not disturb existing runner behaviour or core linkage.
expected: "The runner dispatch did not disturb existing runner behaviour or core linkage."
result: pass
source: automated
summary_file: 18-01-SUMMARY.md
coverage_id: D4
evidence: ["ctest -R ^(runner_|core_linkage_|acceptance_core_mutant|instance_lifecycle|tracer_smoke)"]

### 5. Every D-02 grammar defect (unknown flag, duplicate, empty value, missing value, equals form, acceptance flag, positional, missing rom, missing save dir, bad profile, bad frames) exits 2 with its own invalid-arguments reason token and never prints gbb-host: ready.
expected: "Every D-02 grammar defect (unknown flag, duplicate, empty value, missing value, equals form, acceptance flag, positional, missing rom, missing save dir, bad profile, bad frames) exits 2 with its own invalid-arguments reason token and never prints gbb-host: ready."
result: pass
source: automated
summary_file: 18-02-SUMMARY.md
coverage_id: D1
evidence: ["ctest -R ^host_grammar_ (ten expect_exit tests plus host_grammar_empty_value harness scenario)"]

### 6. Every D-07 stem class is its own CTest with its own status and reason token, a refused stem never writes the output buffer, and a transform-instead-of-refuse mutant is killed with the FAIL refuse_backslash line at exit 1.
expected: "Every D-07 stem class is its own CTest with its own status and reason token, a refused stem never writes the output buffer, and a transform-instead-of-refuse mutant is killed with the FAIL refuse_backslash line at exit 1."
result: pass
source: automated
summary_file: 18-02-SUMMARY.md
coverage_id: D2
evidence: ["ctest -R ^host_stem_ (accepts, seven refuse_* classes)", "ctest -R ^host_stem_mutant_transform$"]

### 7. A hostile --rom basename is refused end to end with its own stem token before any filesystem access, and the save directory listing, mtimes and bytes are unchanged.
expected: "A hostile --rom basename is refused end to end with its own stem token before any filesystem access, and the save directory listing, mtimes and bytes are unchanged."
result: pass
source: automated
summary_file: 18-02-SUMMARY.md
coverage_id: D3
evidence: ["ctest -R ^host_cli_stem_refusal$ (tests/scripts/test_host_mode.py --scenario stem-refusal)"]

### 8. The Windows gate (D-05) refuses with windows-unsupported on _WIN32 and does not fire on POSIX, where the identical command exits 0 and writes the .sav.
expected: "The Windows gate (D-05) refuses with windows-unsupported on _WIN32 and does not fire on POSIX, where the identical command exits 0 and writes the .sav."
result: pass
source: automated
summary_file: 18-02-SUMMARY.md
coverage_id: D4
evidence: ["ctest -R ^host_windows_refusal$ (tests/scripts/test_host_mode.py --scenario platform-gate)"]

### 9. gabbaboy_host reaches the core only through the public header: every undefined gbb_ symbol is declared there and no source includes a test-seam or acceptance header; the seeded seam-calling archive and seeded include are each rejected for their own reason.
expected: "gabbaboy_host reaches the core only through the public header: every undefined gbb_ symbol is declared there and no source includes a test-seam or acceptance header; the seeded seam-calling archive and seeded include are each rejected for their own reason."
result: pass
source: automated
summary_file: 18-02-SUMMARY.md
coverage_id: D5
evidence: ["ctest -R ^host_api_surface$", "ctest -R ^host_api_surface_controls$"]

### 10. Every runner and host library source is in the GBB_BUILD_QUALIFIED dirty list; a seeded unlisted source is rejected with runner-source-unqualified.
expected: "Every runner and host library source is in the GBB_BUILD_QUALIFIED dirty list; a seeded unlisted source is rejected with runner-source-unqualified."
result: pass
source: automated
summary_file: 18-02-SUMMARY.md
coverage_id: D6
evidence: ["ctest -R ^host_qualified_sources$", "ctest -R ^host_qualified_sources_control$"]

### 11. Inventory bookkeeping keeps the three POSIX-only names out of the Windows expectation in both lists, runner_help sees the new host usage line, and existing runner and core linkage behaviour is unchanged.
expected: "Inventory bookkeeping keeps the three POSIX-only names out of the Windows expectation in both lists, runner_help sees the new host usage line, and existing runner and core linkage behaviour is unchanged."
result: pass
source: automated
summary_file: 18-02-SUMMARY.md
coverage_id: D7
evidence: ["bash .github/scripts/verify-test-inventory.sh --self-test", "ctest -R ^(runner_help|core_linkage_links|no_host_clock)$"]

### 12. gbb_get_input_clock is public, static-asserted to 24 bytes and MODEL-tagged; sizes 0, 1 and 23, a NULL instance and a NULL output are refused with every byte unchanged, the exact size succeeds with struct_size 24, and a larger caller struct keeps its trailing bytes.
expected: "gbb_get_input_clock is public, static-asserted to 24 bytes and MODEL-tagged; sizes 0, 1 and 23, a NULL instance and a NULL output are refused with every byte unchanged, the exact size succeeds with struct_size 24, and a larger caller struct keeps its trailing bytes."
result: pass
source: automated
summary_file: 18-03-SUMMARY.md
coverage_id: D1
evidence: ["ctest -R ^input_clock_handshake$ (tests/test_input_clock.c case handshake)", "ctest -R ^model_gates (verify-model-gates.py sees the tagged function)"]

### 13. A fresh instance reports no queue and last equal to now; three queued events give count 3 and last equal to the third time without moving now; the getter leaves the saved state byte-identical; consumed events return last to now.
expected: "A fresh instance reports no queue and last equal to now; three queued events give count 3 and last equal to the third time without moving now; the getter leaves the saved state byte-identical; consumed events return last to now."
result: pass
source: automated
summary_file: 18-03-SUMMARY.md
coverage_id: D2
evidence: ["ctest -R ^input_clock_queue$ (tests/test_input_clock.c case queue)"]

### 14. After gbb_load_state of a later-time and of an earlier-time state the getter reports the restored time and queue; an event at the stale pre-load cursor is refused with GBB_INVALID_EVENT and an event at max(now, last) is accepted.
expected: "After gbb_load_state of a later-time and of an earlier-time state the getter reports the restored time and queue; an event at the stale pre-load cursor is refused with GBB_INVALID_EVENT and an event at max(now, last) is accepted."
result: pass
source: automated
summary_file: 18-03-SUMMARY.md
coverage_id: D3
evidence: ["ctest -R ^input_clock_after_load$ (tests/test_input_clock.c case after_load)"]

### 15. Removing the struct_size guard makes the handshake case fail with FAIL handshake at exit 1, and storing now in place of the last queued time makes the queue case fail with FAIL queue at exit 1; each mutant has a control that runs the unmutated case and exits 0.
expected: "Removing the struct_size guard makes the handshake case fail with FAIL handshake at exit 1, and storing now in place of the last queued time makes the queue case fail with FAIL queue at exit 1; each mutant has a control that runs the unmutated case and exits 0."
result: pass
source: automated
summary_file: 18-03-SUMMARY.md
coverage_id: D4
evidence: ["ctest -R ^input_clock_mutant_short_size_writes(_control)?$", "ctest -R ^input_clock_mutant_last_is_now(_control)?$"]

### 16. Both installed C and C++ consumers call gbb_get_input_clock and name gbb_input_clock and GBB_INPUT_CLOCK_SIZE_V1, and link and run against the installed prefix; a consumer copy with the call renamed fails with consumer-symbol-missing gbb_get_input_clock.
expected: "Both installed C and C++ consumers call gbb_get_input_clock and name gbb_input_clock and GBB_INPUT_CLOCK_SIZE_V1, and link and run against the installed prefix; a consumer copy with the call renamed fails with consumer-symbol-missing gbb_get_input_clock."
result: pass
source: automated
summary_file: 18-03-SUMMARY.md
coverage_id: D5
evidence: ["ctest -R ^input_clock_consumer_symbols(_selftest)?$", "ctest -R ^installed_consumer_(c|cpp)$ against build/state-prefix"]

### 17. The native integration guide documents the getter without naming any identifier the header does not declare, and the only core diff is the getter, its MODEL tag and its static assert; state bytes, pins, inventory and tracer checkers pass at the committed revision.
expected: "The native integration guide documents the getter without naming any identifier the header does not declare, and the only core diff is the getter, its MODEL tag and its static assert; state bytes, pins, inventory and tracer checkers pass at the committed revision."
result: pass
source: automated
summary_file: 18-03-SUMMARY.md
coverage_id: D6
evidence: ["ctest -R ^(native_guide_.*|doc_contract_.*)$", "ctest -R ^state_(format_contract|portable_pins|inventory|tracer|globals|identity|codec_matrix)$"]

### 18. The cadence is a pure function: a generation change flushes after exactly 16 quiet frames (116 for a change at 100) or when the first unflushed change is 300 frames old, a clean image is compared every 3,600 frames, a decrease counts as a change, and a failed flush is retried 16 frames later with flushed advancing only after success; the != to > mutant and the quiet off-by-one mutant each fail their own case at exit 1.
expected: "The cadence is a pure function: a generation change flushes after exactly 16 quiet frames (116 for a change at 100) or when the first unflushed change is 300 frames old, a clean image is compared every 3,600 frames, a decrease counts as a change, and a failed flush is retried 16 frames later with flushed advancing only after success; the != to > mutant and the quiet off-by-one mutant each fail their own case at exit 1."
result: pass
source: automated
summary_file: 18-04-SUMMARY.md
coverage_id: D1
evidence: ["ctest -R ^host_cadence_(quiet|age|rtc_compare|generation_compare|retry)$ (tests/test_host_cadence.c)", "ctest -R ^host_cadence_mutant_(gt|quiet_off_by_one)$"]

### 19. A real runner flushes a guest write once, mid-run, between frames 16 and 24 of a 120-frame run, creates the first image at the final flush for an untouched battery cart, and leaves the .sav inode and mtime unchanged on an identical rerun.
expected: "A real runner flushes a guest write once, mid-run, between frames 16 and 24 of a 120-frame run, creates the first image at the final flush for an untouched battery cart, and leaves the .sav inode and mtime unchanged on an identical rerun."
result: pass
source: automated
summary_file: 18-04-SUMMARY.md
coverage_id: D2
evidence: ["ctest -R ^host_(periodic_flush|first_write|idempotent_rerun)$ (tests/scripts/test_host_mode.py)"]

### 20. The stale-temp sweep removes only entries with the exact prefix .<stem>.sav.tmp- without following a symlink, keeps near-miss names and the symlink target, runs once after every refusal check and before ready, and a refused start leaves all pre-existing temps in place.
expected: "The stale-temp sweep removes only entries with the exact prefix .<stem>.sav.tmp- without following a symlink, keeps near-miss names and the symlink target, runs once after every refusal check and before ready, and a refused start leaves all pre-existing temps in place."
result: pass
source: automated
summary_file: 18-04-SUMMARY.md
coverage_id: D3
evidence: ["ctest -R ^host_sweep_after_checks$ (tests/scripts/test_host_mode.py scenario sweep)", "ctest -R ^host_sweep_exact_prefix$ (tests/test_host_save_io.c)"]

### 21. Each writer stage failure (temp, write, sync, close, target, rename) returns that stage's code and leaves the previous .sav byte- and inode-identical with no temp entry; a dir-sync failure reports failure with the new bytes already in place; EIO from sync is attempted exactly once; 16 EEXIST collisions fail with the temp stage and one collision moves to the next sequence; a directory or symlink target is refused.
expected: "Each writer stage failure (temp, write, sync, close, target, rename) returns that stage's code and leaves the previous .sav byte- and inode-identical with no temp entry; a dir-sync failure reports failure with the new bytes already in place; EIO from sync is attempted exactly once; 16 EEXIST collisions fail with the temp stage and one collision moves to the next sequence; a directory or symlink target is refused."
result: pass
source: automated
summary_file: 18-04-SUMMARY.md
coverage_id: D4
evidence: ["ctest -R ^host_writer_(fault_(temp|write|sync|close|target|rename|dirsync)|eio_no_retry|eexist|target_not_regular)$ (tests/test_host_save_io.c)"]

### 22. Host mode applies no wall-clock RTC catch-up: an MBC3+RTC run persists RTC-only drift at the final flush as a 32,789-byte image, and a second run on a file aged by a day continues from the persisted clock with unchanged SRAM and a different 21-byte RTC block.
expected: "Host mode applies no wall-clock RTC catch-up: an MBC3+RTC run persists RTC-only drift at the final flush as a 32,789-byte image, and a second run on a file aged by a day continues from the persisted clock with unchanged SRAM and a different 21-byte RTC block."
result: pass
source: automated
summary_file: 18-04-SUMMARY.md
coverage_id: D5
evidence: ["ctest -R ^host_rtc_final_compare$ (tests/scripts/test_host_mode.py scenario rtc-final-compare)"]

### 23. The save directory is never created: a missing path exits 2 save-dir-missing and still does not exist, a regular file exits 2 save-dir-not-directory and is unchanged, a symlinked path (explicit link and /tmp) is accepted and the image lands in the real directory; a runner that creates the directory fails savedir-missing.
expected: "The save directory is never created: a missing path exits 2 save-dir-missing and still does not exist, a regular file exits 2 save-dir-not-directory and is unchanged, a symlinked path (explicit link and /tmp) is accepted and the image lands in the real directory; a runner that creates the directory fails savedir-missing."
result: pass
source: automated
summary_file: 18-04-SUMMARY.md
coverage_id: D6
evidence: ["ctest -R ^host_savedir_(missing|not_directory|symlink_path)$", "ctest -R ^host_savedir_mutant_mkdir$"]

### 24. A hostile .sav is refused before the first frame with its own token and no mutation: sizes 0, N-1, N+1, the mGBA 32,816-byte footer file and 8 MiB+1 give save-size, a corrupted RTC magic gives save-rtc-block, a live or dangling symlink gives save-symlink, a FIFO (within 10 s) and a directory give save-not-regular, and a device at the .sav path is not-regular at the reader; an exact valid image imports; a symlink-following runner fails import-symlink.
expected: "A hostile .sav is refused before the first frame with its own token and no mutation: sizes 0, N-1, N+1, the mGBA 32,816-byte footer file and 8 MiB+1 give save-size, a corrupted RTC magic gives save-rtc-block, a live or dangling symlink gives save-symlink, a FIFO (within 10 s) and a directory give save-not-regular, and a device at the .sav path is not-regular at the reader; an exact valid image imports; a symlink-following runner fails import-symlink."
result: pass
source: automated
summary_file: 18-04-SUMMARY.md
coverage_id: D7
evidence: ["ctest -R ^host_import_(exact|zero|short|long|mgba_footer|oversize|bad_rtc|symlink|dangling_symlink|fifo|directory)$", "ctest -R ^host_import_device$ (tests/test_host_save_io.c)", "ctest -R ^host_import_mutant_follow$"]

### 25. A stray .sav (regular file, FIFO or symlink) next to a no-battery cartridge is never opened: the run exits 0 with flush=none inside 10 s and the entry, its link target and the listing are unchanged; a FIFO or directory passed as --rom exits 2 with rom-not-regular inside 10 s, never rom-unreadable or rom-size, with the save directory untouched.
expected: "A stray .sav (regular file, FIFO or symlink) next to a no-battery cartridge is never opened: the run exits 0 with flush=none inside 10 s and the entry, its link target and the listing are unchanged; a FIFO or directory passed as --rom exits 2 with rom-not-regular inside 10 s, never rom-unreadable or rom-size, with the save directory untouched."
result: pass
source: automated
summary_file: 18-04-SUMMARY.md
coverage_id: D8
evidence: ["ctest -R ^host_import_stray_nobattery$", "ctest -R ^host_rom_(fifo|directory)$"]

### 26. An import-ignoring runner (the single gbb_import_battery call short-circuited to GBB_OK) fails the two-process continuation scenario with FAIL continuation because the second run restarts the counter at 01.
expected: "An import-ignoring runner (the single gbb_import_battery call short-circuited to GBB_OK) fails the two-process continuation scenario with FAIL continuation because the second run restarts the counter at 01."
result: pass
source: automated
summary_file: 18-04-SUMMARY.md
coverage_id: D9
evidence: ["ctest -R ^host_continuation_mutant_ignore_import$"]

### 27. No fault seam ships: the shipped gabbaboy_host archive and the gabbaboy-runner executable define no host_save_io_test_ symbol, while the same check on gabbaboy_host_testing is rejected with host-test-seam-shipped naming host_save_io_test_fail_next.
expected: "No fault seam ships: the shipped gabbaboy_host archive and the gabbaboy-runner executable define no host_save_io_test_ symbol, while the same check on gabbaboy_host_testing is rejected with host-test-seam-shipped naming host_save_io_test_fail_next."
result: pass
source: automated
summary_file: 18-04-SUMMARY.md
coverage_id: D10
evidence: ["ctest -R ^host_no_test_seams_shipped(_control)?$"]

### 28. The 39 new POSIX-only names are in tests/expected-tests.txt and removed from the Windows expectation in both cmake/ExpectedTests.cmake and the inventory script; the inventory self-test passes, the registered set matches the expected set, and the full suite is green at the plan head.
expected: "The 39 new POSIX-only names are in tests/expected-tests.txt and removed from the Windows expectation in both cmake/ExpectedTests.cmake and the inventory script; the inventory self-test passes, the registered set matches the expected set, and the full suite is green at the plan head."
result: pass
source: automated
summary_file: 18-04-SUMMARY.md
coverage_id: D11
evidence: ["bash .github/scripts/verify-test-inventory.sh --self-test", "ctest -j8 over the full phase1 build at 8335fbaf: 1581 of 1581 passed"]

### 29. A slot saved through the dir-fd writer holds exactly the gbb_save_state bytes, loading it after 60 more frames returns those bytes, and an empty slot returns EMPTY and writes nothing.
expected: "A slot saved through the dir-fd writer holds exactly the gbb_save_state bytes, loading it after 60 more frames returns those bytes, and an empty slot returns EMPTY and writes nothing."
result: pass
source: automated
summary_file: 18-05-SUMMARY.md
coverage_id: D1
evidence: ["ctest -R ^slot_(roundtrip|empty)$ (tests/test_slots.c)"]

### 30. host_save_io_read_bounded opens without following symlinks or blocking, requires a regular file, reads at most the caller's bound and never sizes anything from st_size: a symlinked slot reads as READ_FAILED and a state plus 4096 bytes reads as one byte too many (SIZE_MISMATCH).
expected: "host_save_io_read_bounded opens without following symlinks or blocking, requires a regular file, reads at most the caller's bound and never sizes anything from st_size: a symlinked slot reads as READ_FAILED and a state plus 4096 bytes reads as one byte too many (SIZE_MISMATCH)."
result: pass
source: automated
summary_file: 18-05-SUMMARY.md
coverage_id: D2
evidence: ["ctest -R ^slot_refusal_(symlink|oversize)$ (tests/test_slots.c)", "ctest -R ^host_import_mutant_follow$ (the shared open helper keeps the one anchor the follow mutant edits)"]

### 31. Eight refusals (a state of another game, a DMG state in a CGB store, a patched release token with a recomputed CRC, a text file, a flipped body byte, a 100-byte truncation, size plus 4096 bytes, a symlinked slot) each return their exact outcome and gbb_error and leave gbb_save_state, gbb_copy_battery, the battery generation and the SHA-256 of the slot, undo, preload and .gbb files byte-identical, missing files staying missing.
expected: "Eight refusals (a state of another game, a DMG state in a CGB store, a patched release token with a recomputed CRC, a text file, a flipped body byte, a 100-byte truncation, size plus 4096 bytes, a symlinked slot) each return their exact outcome and gbb_error and leave gbb_save_state, gbb_copy_battery, the battery generation and the SHA-256 of the slot, undo, preload and .gbb files byte-identical, missing files staying missing."
result: pass
source: automated
summary_file: 18-05-SUMMARY.md
coverage_id: D3
evidence: ["ctest -R ^slot_(wrong_rom_untouched|refusal_.*)$ (tests/test_slots.c)"]

### 32. The order is enforced by killed mutants: writing the undo snapshot or the battery preload before the slot is validated fails refusal_flipped_byte at exit 1.
expected: "The order is enforced by killed mutants: writing the undo snapshot or the battery preload before the slot is validated fails refusal_flipped_byte at exit 1."
result: pass
source: automated
summary_file: 18-05-SUMMARY.md
coverage_id: D4
evidence: ["ctest -R ^slot_mutant_(undo_before_load|preload_before_validate)$"]

### 33. A forced preload write failure on the first load returns BACKUP_FAILED with the machine, generation and files identical and no undo or preload file; a forced undo write failure rolls the machine back to byte-identical state and battery with no file changed; a failed slot save keeps the old file's inode and bytes with no temp left, and the seam is one-shot. The rollback-removing mutant fails undo_write_failure.
expected: "A forced preload write failure on the first load returns BACKUP_FAILED with the machine, generation and files identical and no undo or preload file; a forced undo write failure rolls the machine back to byte-identical state and battery with no file changed; a failed slot save keeps the old file's inode and bytes with no temp left, and the seam is one-shot. The rollback-removing mutant fails undo_write_failure."
result: pass
source: automated
summary_file: 18-05-SUMMARY.md
coverage_id: D5
evidence: ["ctest -R ^slot_(backup_write_failure|undo_write_failure|save_failure_keeps_old)$", "ctest -R ^slot_mutant_no_rollback$"]

### 34. Undo swaps: load slot 1, undo returns the starting state, undo again returns slot 1; undo with no undo file returns NO_UNDO and writes nothing.
expected: "Undo swaps: load slot 1, undo returns the starting state, undo again returns slot 1; undo with no undo file returns NO_UNDO and writes nothing."
result: pass
source: automated
summary_file: 18-05-SUMMARY.md
coverage_id: D6
evidence: ["ctest -R ^slot_(undo_swap|no_undo)$"]

### 35. The battery guard keeps the pre-A in-game save: loading A backs up battery X, loading B (live battery equals the guard) leaves the preload file at X, and an in-game change before the next load is backed up. The guard-removing mutant fails battery_guard.
expected: "The battery guard keeps the pre-A in-game save: loading A backs up battery X, loading B (live battery equals the guard) leaves the preload file at X, and an in-game change before the next load is backed up. The guard-removing mutant fails battery_guard."
result: pass
source: automated
summary_file: 18-05-SUMMARY.md
coverage_id: D7
evidence: ["ctest -R ^slot_battery_guard$", "ctest -R ^slot_mutant_no_guard$"]

### 36. A restored queue with an event 65 frames ahead, 60 events or 57 events is UNSAFE_INPUT with the machine and files untouched (no undo or preload written on the session's first load); 56 events load and report queued_count 56.
expected: "A restored queue with an event 65 frames ahead, 60 events or 57 events is UNSAFE_INPUT with the machine and files untouched (no undo or preload written on the session's first load); 56 events load and report queued_count 56."
result: pass
source: automated
summary_file: 18-05-SUMMARY.md
coverage_id: D8
evidence: ["ctest -R ^slot_unsafe_queued_input$"]

### 37. Every outcome and every gbb_error from GBB_OK through GBB_STATE_INVALID_CONTENT maps to the exact D-25 string for both subjects (Slot N and The undo backup), buffers are always NUL-terminated and never overrun, and the log line carries operation, slot, outcome token and gbb_error. A mapping of UNSUPPORTED_VERSION to the damaged text fails message_table.
expected: "Every outcome and every gbb_error from GBB_OK through GBB_STATE_INVALID_CONTENT maps to the exact D-25 string for both subjects (Slot N and The undo backup), buffers are always NUL-terminated and never overrun, and the log line carries operation, slot, outcome token and gbb_error. A mapping of UNSUPPORTED_VERSION to the damaged text fails message_table."
result: pass
source: automated
summary_file: 18-05-SUMMARY.md
coverage_id: D9
evidence: ["ctest -R ^slot_message_table$ (tests/test_slots_pure.c, portable)", "ctest -R ^slot_mutant_message_map$"]

### 38. The key decoder selects on digits 1-9 (Shift allowed, GUI, Ctrl or Alt vetoes, 0 reserved), maps GUI+S, GUI+L and GUI+Z to save, load and undo, and returns nothing for bare letters, GUI+R, a repeat or a blocked state.
expected: "The key decoder selects on digits 1-9 (Shift allowed, GUI, Ctrl or Alt vetoes, 0 reserved), maps GUI+S, GUI+L and GUI+Z to save, load and undo, and returns nothing for bare letters, GUI+R, a repeat or a blocked state."
result: pass
source: automated
summary_file: 18-05-SUMMARY.md
coverage_id: D10
evidence: ["ctest -R ^slot_key_decoder$ (tests/test_slots_pure.c, portable)"]

### 39. The re-anchor plan releases at max(now, last queued) and flags a window above 140,448 x 64 half-dots or more than 56 queued events; against the core, after loading a later-time state and an earlier-time state with two restored events, a stale-cursor event is refused, the plan's press is admitted, the guest sees A released before it and pressed within one frame after it, and a no-press control keeps A released. A plan that ignores the restored queue fails reanchor_earlier.
expected: "The re-anchor plan releases at max(now, last queued) and flags a window above 140,448 x 64 half-dots or more than 56 queued events; against the core, after loading a later-time state and an earlier-time state with two restored events, a stale-cursor event is refused, the plan's press is admitted, the guest sees A released before it and pressed within one frame after it, and a no-press control keeps A released. A plan that ignores the restored queue fails reanchor_earlier."
result: pass
source: automated
summary_file: 18-05-SUMMARY.md
coverage_id: D11
evidence: ["ctest -R ^slot_reanchor_plan$ (tests/test_slots_pure.c, portable)", "ctest -R ^slot_reanchor_(later|earlier)$ (generated joypad-mirror ROM, SRAM byte 0 bit 0)", "ctest -R ^slot_mutant_plan_ignores_last$"]

### 40. Selection text reads `Slot N selected: empty` for a missing file, `saved YYYY-MM-DD HH:MM` in local time from the mtime (TZ=UTC, utimensat), and a bare `saved` when stat fails for another reason.
expected: "Selection text reads `Slot N selected: empty` for a missing file, `saved YYYY-MM-DD HH:MM` in local time from the mtime (TZ=UTC, utimensat), and a bare `saved` when stat fails for another reason."
result: pass
source: automated
summary_file: 18-05-SUMMARY.md
coverage_id: D12
evidence: ["ctest -R ^slot_select_message$"]

### 41. The slot engine includes only the public header, the host header and libc/POSIX: host_api_surface scans the slots archive and sources and reports archives=2; the Windows-build proxy (-D_WIN32 -fsyntax-only) passes for src/host/*.c and slots.c; the 29 slot_ names, 25 of them POSIX-only, are in the expected inventory and both Windows lists.
expected: "The slot engine includes only the public header, the host header and libc/POSIX: host_api_surface scans the slots archive and sources and reports archives=2; the Windows-build proxy (-D_WIN32 -fsyntax-only) passes for src/host/*.c and slots.c; the 29 slot_ names, 25 of them POSIX-only, are in the expected inventory and both Windows lists."
result: pass
source: automated
summary_file: 18-05-SUMMARY.md
coverage_id: D13
evidence: ["ctest -R ^host_api_surface$", "bash .github/scripts/verify-test-inventory.sh --self-test"]

### 42. The whole suite is green at the plan head after reconfiguring the revision-pinned tests.
expected: "The whole suite is green at the plan head after reconfiguring the revision-pinned tests."
result: pass
source: automated
summary_file: 18-05-SUMMARY.md
coverage_id: D14
evidence: ["ctest -j6 over the full phase1 build at 233a1fed: 1610 of 1610 passed"]

### 43. In the running SDL player, digit keys 1-9 select a slot (Shift allowed; Ctrl, Alt and Command veto), Command-S saves it without saving the battery, Command-L restores exactly the slot plus the eight queued button releases, and Command-Z swaps back, with the later Z key-up harmless.
expected: "In the running SDL player, digit keys 1-9 select a slot (Shift allowed; Ctrl, Alt and Command veto), Command-S saves it without saving the battery, Command-L restores exactly the slot plus the eight queued button releases, and Command-Z swaps back, with the later Z key-up harmless."
result: pass
source: automated
summary_file: 18-06-SUMMARY.md
coverage_id: D1
evidence: ["ctest -R ^player_slot_keys$ (tests/player/test_slots.c, case keys, through push_key_mod and pump_events)"]

### 44. Command-R does not reset and Command-S does not save the battery, while a bare R still resets and a bare S still saves the battery; a key repeat, a pending transition and a pending dialog change no slot file and no status; slot keys work while paused and a load keeps the pause.
expected: "Command-R does not reset and Command-S does not save the battery, while a bare R still resets and a bare S still saves the battery; a key repeat, a pending transition and a pending dialog change no slot file and no status; slot keys work while paused and a load keeps the pause."
result: pass
source: automated
summary_file: 18-06-SUMMARY.md
coverage_id: D2
evidence: ["ctest -R ^player_slot_keys$ (guards, repeat, transition, dialog, pause and bare-key controls)", "ctest -R ^player_slot_mutant_command_guard$ (main.c without !command on the R branch fails case keys with exit 1)"]

### 45. After loading an earlier-time state and a later-time state, the player cursor and anchor sit at the restored clock, no key is held, the eight releases are queued, a no-key control frame keeps A released, and a fresh Z keydown is accepted and reaches the guest within one frame of its scheduled time (SRAM byte 0 bit 0 clears), even when Z was held across the load.
expected: "After loading an earlier-time state and a later-time state, the player cursor and anchor sit at the restored clock, no key is held, the eight releases are queued, a no-key control frame keeps A released, and a fresh Z keydown is accepted and reaches the guest within one frame of its scheduled time (SRAM byte 0 bit 0 clears), even when Z was held across the load."
result: pass
source: automated
summary_file: 18-06-SUMMARY.md
coverage_id: D3
evidence: ["ctest -R ^player_slot_reanchor$ (generated joypad-mirror ROM)", "ctest -R ^player_slot_mutant_no_rebase$ (main.c without the player_input_rebase call fails case reanchor with exit 1; also fails on the guest-visible check alone, press 84,264,008 half-dots ahead)"]

### 46. The slot message is shown through set_status; while a battery-save failure is active the title status reads the save status, a middle dot and the slot message; every operation prints one stderr line with the gbb_error; a load clears the audio backlog once, forces a redraw, restarts the .gbb cadence, keeps user_paused, and the next update_battery_save does not wipe the message.
expected: "The slot message is shown through set_status; while a battery-save failure is active the title status reads the save status, a middle dot and the slot message; every operation prints one stderr line with the gbb_error; a load clears the audio backlog once, forces a redraw, restarts the .gbb cadence, keeps user_paused, and the next update_battery_save does not wipe the message."
result: pass
source: automated
summary_file: 18-06-SUMMARY.md
coverage_id: D4
evidence: ["ctest -R ^player_slot_status_line$"]

### 47. The help dialog lists Select state slot: 1-9, Save state to slot: Command-S, Load state from slot: Command-L and Undo last load: Command-Z and contains the exact sentence once; the formatted message fits its 4096-byte buffer.
expected: "The help dialog lists Select state slot: 1-9, Save state to slot: Command-S, Load state from slot: Command-L and Undo last load: Command-Z and contains the exact sentence once; the formatted message fits its 4096-byte buffer."
result: pass
source: automated
summary_file: 18-06-SUMMARY.md
coverage_id: D5
evidence: ["ctest -R ^player_slot_help_text$"]

### 48. GBB_PLAYER_LIMITATIONS_TEXT keeps every prior sentence and appends the release-bound-slots sentence and the window-title, fullscreen and VoiceOver sentence; the literal in test_limitations.c is updated in step and the claims checkers that read the text still pass.
expected: "GBB_PLAYER_LIMITATIONS_TEXT keeps every prior sentence and appends the release-bound-slots sentence and the window-title, fullscreen and VoiceOver sentence; the literal in test_limitations.c is updated in step and the claims checkers that read the text still pass."
result: pass
source: automated
summary_file: 18-06-SUMMARY.md
coverage_id: D6
evidence: ["ctest -R ^player_limitations$", "ctest -R ^(cgb_speed_docs_no_stale_claims.*|phase8_player_contract.*|cgb_corpus_claims.*|cgb_hdma_claims_contract.*)$ (main suite, 10 of 10)", "ctest -R ^player_claims_agree.*$"]

### 49. Research assumption A2 is resolved by a scan, not a manual step: the Cocoa main menu SDL creates (19 items) binds none of Command-S, Command-L or Command-Z, and a seeded Command-S item is detected with exit 1.
expected: "Research assumption A2 is resolved by a scan, not a manual step: the Cocoa main menu SDL creates (19 items) binds none of Command-S, Command-L or Command-Z, and a seeded Command-S item is detected with exit 1."
result: pass
source: automated
summary_file: 18-06-SUMMARY.md
coverage_id: D7
evidence: ["ctest -R ^player_slot_menu_shortcuts$ (prints menu-shortcuts pass items=19)", "ctest -R ^player_slot_menu_shortcuts_control$ (prints menu-shortcut-conflict s, exit 1)"]

### 50. The player suite is green end to end through the package gate and matches its inventory, and the main suite is green at the plan head after reconfiguring the revision-pinned tests.
expected: "The player suite is green end to end through the package gate and matches its inventory, and the main suite is green at the plan head after reconfiguring the revision-pinned tests."
result: pass
source: automated
summary_file: 18-06-SUMMARY.md
coverage_id: D8
evidence: ["bash tests/scripts/verify-phase3-player.sh --build-package (106 of 106 player_ tests, JUnit checked against tests/player/expected-tests.txt)", "ctest --preset phase1 -j6 at 67bb2bdc: 1610 of 1610 after reconfiguring the pinned tests (1607 first pass, the three revision-pinned tests pass on rerun)"]

### 51. A real SIGTERM to a paced runner exits 0 with status=clean reason=SIGTERM, flushes the save, and a fresh --frames K batch run reproduces the signalled .sav byte for byte, so the stop landed on a whole frame; in non-sanitizer lanes kill-to-wait is under 2.0 s.
expected: "A real SIGTERM to a paced runner exits 0 with status=clean reason=SIGTERM, flushes the save, and a fresh --frames K batch run reproduces the signalled .sav byte for byte, so the stop landed on a whole frame; in non-sanitizer lanes kill-to-wait is under 2.0 s."
result: pass
source: automated
summary_file: 18-07-SUMMARY.md
coverage_id: D1
evidence: ["ctest -R ^host_signal_term$ (tests/scripts/test_host_signals.py --scenario term)"]

### 52. SIGINT stops the runner cleanly with reason=SIGINT and a flushed save, and a SIGINT inherited as SIG_IGN is ignored for 0.5 s until a SIGTERM ends the run with exit 0.
expected: "SIGINT stops the runner cleanly with reason=SIGINT and a flushed save, and a SIGINT inherited as SIG_IGN is ignored for 0.5 s until a SIGTERM ends the run with exit 0."
result: pass
source: automated
summary_file: 18-07-SUMMARY.md
coverage_id: D2
evidence: ["ctest -R ^host_signal_(int|inherited_ign)$"]

### 53. The host exit table has exactly the rows 0 clean, 1 failure and 2 refusal, declared once in host_exit.h; host_exit_name is NULL for 3, 4, 77, -1 and 256, and the --frames end, the failed final flush on a read-only save dir, a core stop and a refusal each exit with their own code and token.
expected: "The host exit table has exactly the rows 0 clean, 1 failure and 2 refusal, declared once in host_exit.h; host_exit_name is NULL for 3, 4, 77, -1 and 256, and the --frames end, the failed final flush on a read-only save dir, a core stop and a refusal each exit with their own code and token."
result: pass
source: automated
summary_file: 18-07-SUMMARY.md
coverage_id: D3
evidence: ["ctest -R ^host_exit_table_codes$ (tests/test_host_run.c exit_table)", "ctest -R ^host_exit_(frames_clean|failure_readonly|core_stop|refusal)$"]

### 54. After host_signal_install TERM, INT and HUP carry a non-default handler with SA_RESTART and an empty mask, the first delivery stores the signal and restores the default action, SIGPIPE is ignored, an inherited SIG_IGN on INT and HUP stays ignored, and TERM, INT and HUP are unblocked even if they were blocked before.
expected: "After host_signal_install TERM, INT and HUP carry a non-default handler with SA_RESTART and an empty mask, the first delivery stores the signal and restores the default action, SIGPIPE is ignored, an inherited SIG_IGN on INT and HUP stays ignored, and TERM, INT and HUP are unblocked even if they were blocked before."
result: pass
source: automated
summary_file: 18-07-SUMMARY.md
coverage_id: D4
evidence: ["ctest -R ^host_signal_disposition$ (tests/test_host_run.c disposition)"]

### 55. A signal pending at the first boundary stops the run with stopped_at_frame=0 flush=none, exit 0, and a battery cartridge gets no .sav.
expected: "A signal pending at the first boundary stops the run with stopped_at_frame=0 flush=none, exit 0, and a battery cartridge gets no .sav."
result: pass
source: automated
summary_file: 18-07-SUMMARY.md
coverage_id: D5
evidence: ["ctest -R ^host_run_stop_before_first_frame$ (tests/test_host_run.c)"]

### 56. Six SIGKILLs at pseudo-random moments against an MBC3+RTC cartridge always leave an exact 32,789-byte .sav with a structurally valid GBRT version-1 block, every completed flush replaces the inode, and a final normal start sweeps the temps.
expected: "Six SIGKILLs at pseudo-random moments against an MBC3+RTC cartridge always leave an exact 32,789-byte .sav with a structurally valid GBRT version-1 block, every completed flush replaces the inode, and a final normal start sweeps the temps."
result: pass
source: automated
summary_file: 18-07-SUMMARY.md
coverage_id: D6
evidence: ["ctest -R ^host_exit_crash_storm$ (tests/scripts/test_host_signals.py --scenario crash-storm)"]

### 57. Four build-tree decoy runners fail the harness for their own reason: no final flush fails term with 'SIGTERM left no .sav', a partial-frame stop fails term with a replay mismatch, exit 0 after a failed final flush fails failure-readonly with 'exit 0, expected 1', and an in-place writer fails crash-storm on a kept inode.
expected: "Four build-tree decoy runners fail the harness for their own reason: no final flush fails term with 'SIGTERM left no .sav', a partial-frame stop fails term with a replay mismatch, exit 0 after a failed final flush fails failure-readonly with 'exit 0, expected 1', and an in-place writer fails crash-storm on a kept inode."
result: pass
source: automated
summary_file: 18-07-SUMMARY.md
coverage_id: D7
evidence: ["ctest -R ^host_signal_decoy_(no_flush|partial_frame|exit0_after_failed_flush|in_place_write)$"]

### 58. No test hook ships: the shipped gabbaboy_host archive and gabbaboy-runner define no host_save_io_test_ or host_run_test_ symbol, while the test twin is rejected naming host_run_test_set_after_ready_hook.
expected: "No test hook ships: the shipped gabbaboy_host archive and gabbaboy-runner define no host_save_io_test_ or host_run_test_ symbol, while the test twin is rejected naming host_run_test_set_after_ready_hook."
result: pass
source: automated
summary_file: 18-07-SUMMARY.md
coverage_id: D8
evidence: ["ctest -R ^host_no_test_seams_shipped(_control|_run_control)?$"]

### 59. The core is mechanically free of signal code: the deny lists add signal, sigaction, raise, kill, sigprocmask, pthread_sigmask, alarm and setitimer at the source and object layers, the real core still passes, a strict-C17 object importing kill fails with no-host-clock-symbol: kill and a source calling sigaction fails with a call token.
expected: "The core is mechanically free of signal code: the deny lists add signal, sigaction, raise, kill, sigprocmask, pthread_sigmask, alarm and setitimer at the source and object layers, the real core still passes, a strict-C17 object importing kill fails with no-host-clock-symbol: kill and a source calling sigaction fails with a call token."
result: pass
source: automated
summary_file: 18-07-SUMMARY.md
coverage_id: D9
evidence: ["ctest -R ^no_host_clock(_selftest|_symbol_selftest|_comment_selftest|_signal_selftest|_signal_call_selftest)?$"]

### 60. The 17 new names are in tests/expected-tests.txt, the 15 POSIX-only ones are removed from the Windows expectation in both cmake/ExpectedTests.cmake and the inventory script, and the full phase1 suite is green at the plan head.
expected: "The 17 new names are in tests/expected-tests.txt, the 15 POSIX-only ones are removed from the Windows expectation in both cmake/ExpectedTests.cmake and the inventory script, and the full phase1 suite is green at the plan head."
result: pass
source: automated
summary_file: 18-07-SUMMARY.md
coverage_id: D10
evidence: ["bash .github/scripts/verify-test-inventory.sh --self-test", "ctest --preset phase1 -j8 at 64c6749b: 1628 of 1628 passed"]

### 61. --print-save-format prints save_format=gabbaboy-mbc1-sram-8k-v1 bytes=8192 for the committed MBC1 fixture, save_format=none bytes=0 for the tracer (no battery; the sentinel is not an id), exits 2 with print-save-format-extra when combined with --save-dir, and prints no ready line.
expected: "--print-save-format prints save_format=gabbaboy-mbc1-sram-8k-v1 bytes=8192 for the committed MBC1 fixture, save_format=none bytes=0 for the tracer (no battery; the sentinel is not an id), exits 2 with print-save-format-extra when combined with --save-dir, and prints no ready line."
result: pass
source: automated
summary_file: 18-08-SUMMARY.md
coverage_id: D1
evidence: ["ctest -R ^(save_format_print|save_format_print_none|host_grammar_print_extra)$"]

### 62. For all 16 rows on both the dmg and cgb profiles the runner prints the JSON id and bytes, a --frames 2 run produces a .sav of exactly that size with SRAM byte 0 equal to $5A ($FA with every byte >= $F0 for MBC2), RTC rows end in a structurally valid GBRT version-1 block (the $0F row is that block alone), both profiles agree, MBC1 ROM code 4 is also admitted, and $1A and $01 cartridges create no file; the checker prints rows=16 ids=12 profiles=2 files=32.
expected: "For all 16 rows on both the dmg and cgb profiles the runner prints the JSON id and bytes, a --frames 2 run produces a .sav of exactly that size with SRAM byte 0 equal to $5A ($FA with every byte >= $F0 for MBC2), RTC rows end in a structurally valid GBRT version-1 block (the $0F row is that block alone), both profiles agree, MBC1 ROM code 4 is also admitted, and $1A and $01 cartridges create no file; the checker prints rows=16 ids=12 profiles=2 files=32."
result: pass
source: automated
summary_file: 18-08-SUMMARY.md
coverage_id: D2
evidence: ["ctest -R ^save_format_files$ (verify-save-formats.py --check)"]

### 63. Every admitted battery (type, RAM code, ROM code) combination reported by the core maps to exactly one JSON row with equal bytes and RTC presence, every row has an admitted combination (including the MBC1 ROM-code-4 boundary), the admitted no-battery types equal no_battery_types, and $10/$05 (MBC30) is never admitted.
expected: "Every admitted battery (type, RAM code, ROM code) combination reported by the core maps to exactly one JSON row with equal bytes and RTC presence, every row has an admitted combination (including the MBC1 ROM-code-4 boundary), the admitted no-battery types equal no_battery_types, and $10/$05 (MBC30) is never admitted."
result: pass
source: automated
summary_file: 18-08-SUMMARY.md
coverage_id: D3
evidence: ["ctest -R ^save_format_completeness$ (test_save_format_completeness + verify-save-formats.py --check-completeness)"]

### 64. The table is append-only against the latest strict-semver v* tag: the current latest tag v0.2.1 carries no docs/host-contract.json, so the freeze passes with baseline=none; no strict tag fails with no-tags; a baseline row that changed or vanished fails with freeze-mismatch.
expected: "The table is append-only against the latest strict-semver v* tag: the current latest tag v0.2.1 carries no docs/host-contract.json, so the freeze passes with baseline=none; no strict tag fails with no-tags; a baseline row that changed or vanished fails with freeze-mismatch."
result: pass
source: automated
summary_file: 18-08-SUMMARY.md
coverage_id: D4
evidence: ["ctest -R ^save_format_freeze$ (verify-save-formats.py --freeze)"]

### 65. docs/host-contract.json is canonical (text equals json.dumps(json.loads(text), indent=2, ensure_ascii=True) plus newline, keys never re-sorted), has exactly the four sections in order, its numbered exit_codes rows equal GBB_HOST_EXIT_TABLE in host_exit.h with one final crash row of code null, and its cadence values equal the constants in gbb_host.h.
expected: "docs/host-contract.json is canonical (text equals json.dumps(json.loads(text), indent=2, ensure_ascii=True) plus newline, keys never re-sorted), has exactly the four sections in order, its numbered exit_codes rows equal GBB_HOST_EXIT_TABLE in host_exit.h with one final crash row of code null, and its cadence values equal the constants in gbb_host.h."
result: pass
source: automated
summary_file: 18-08-SUMMARY.md
coverage_id: D5
evidence: ["ctest -R ^host_contract_json$ (verify-host-contract.py --check)"]

### 66. Twenty-six save-format controls each fail for their own REJECT code (size-mismatch for $10/$03 at 32,816, row-missing, row-not-admitted for a $10/$05 row, id-grammar for a release-versioned and an uppercase id, sum-mismatch, id-size-conflict, row-order, non-canonical for tabs and sorted keys, interop-claim, enumerator-output, file-size, profile-id-mismatch, no-battery-file, no-tags twice, freeze-mismatch twice) beside the positive controls; ten host-contract controls do the same for canonical form, sections, exit table and cadence.
expected: "Twenty-six save-format controls each fail for their own REJECT code (size-mismatch for $10/$03 at 32,816, row-missing, row-not-admitted for a $10/$05 row, id-grammar for a release-versioned and an uppercase id, sum-mismatch, id-size-conflict, row-order, non-canonical for tabs and sorted keys, interop-claim, enumerator-output, file-size, profile-id-mismatch, no-battery-file, no-tags twice, freeze-mismatch twice) beside the positive controls; ten host-contract controls do the same for canonical form, sections, exit table and cadence."
result: pass
source: automated
summary_file: 18-08-SUMMARY.md
coverage_id: D6
evidence: ["ctest -R ^save_format_controls$ (save-formats self-test pass controls=26)", "ctest -R ^host_contract_controls$ (host-contract self-test pass controls=10)"]

### 67. The 9 new CTest names are in tests/expected-tests.txt, the 2 POSIX-only ones (save_format_files, save_format_controls) are removed from the Windows expectation in both cmake/ExpectedTests.cmake and the inventory script, and the full phase1 suite is green at the plan's last code commit.
expected: "The 9 new CTest names are in tests/expected-tests.txt, the 2 POSIX-only ones (save_format_files, save_format_controls) are removed from the Windows expectation in both cmake/ExpectedTests.cmake and the inventory script, and the full phase1 suite is green at the plan's last code commit."
result: pass
source: automated
summary_file: 18-08-SUMMARY.md
coverage_id: D7
evidence: ["bash .github/scripts/verify-test-inventory.sh --self-test", "ctest --test-dir build -j8 at befd624c: 1637 of 1637 passed"]

### 68. docs/host-contract.json is installed as share/gabbaboy/host-contract.json, and the installed runner, started from a working directory unrelated to the prefix against a fresh save directory, reads back a game-visible counter of 01 then 02 across two processes and 42 from a 41 preload, prints a save-format id and byte count that name a row of the installed JSON, and finds the installed JSON byte-identical to the source; a copy with one digit of the 0x03/0x02 row's byte count changed is rejected with installed-contract-drift in the same run.
expected: "docs/host-contract.json is installed as share/gabbaboy/host-contract.json, and the installed runner, started from a working directory unrelated to the prefix against a fresh save directory, reads back a game-visible counter of 01 then 02 across two processes and 42 from a 41 preload, prints a save-format id and byte count that name a row of the installed JSON, and finds the installed JSON byte-identical to the source; a copy with one digit of the 0x03/0x02 row's byte count changed is rejected with installed-contract-drift in the same run."
result: pass
source: automated
summary_file: 18-09-SUMMARY.md
coverage_id: D1
evidence: ["ctest -R ^installed_host_smoke$ (installed-host pass continuation=01,02 preload=42 controls=1)", "ctest -R ^(installed_runner_smoke|installed_consumer_(c|cpp)|preview_package_smoke)$"]

### 69. README, the native guide, the cartridge guide and the unreleased ledger carry the host-mode, host process contract, raw save and state slot text; each document has a phrase contract scoped to its own section and a copy with one pinned phrase removed fails with doc-contract-missing and that phrase.
expected: "README, the native guide, the cartridge guide and the unreleased ledger carry the host-mode, host process contract, raw save and state slot text; each document has a phrase contract scoped to its own section and a copy with one pinned phrase removed fails with doc-contract-missing and that phrase."
result: pass
source: automated
summary_file: 18-09-SUMMARY.md
coverage_id: D2
evidence: ["ctest -R ^(native_guide_host_contract|cartridge_guide_slots_contract|readme_host_mode_contract|unreleased_host_entries)$", "ctest -R ^doc_contract_(host|readme_host|cartridge_slots|unreleased_host)_missing_selftest$"]

### 70. The exit-code table (4 rows) and the save-format table (16 rows) of the Host process contract section equal docs/host-contract.json cell by cell; a copy whose 32,789 cell reads 32,816 is rejected as doc-table-drift and a copy whose save-format header row is renamed is rejected as doc-table-missing.
expected: "The exit-code table (4 rows) and the save-format table (16 rows) of the Host process contract section equal docs/host-contract.json cell by cell; a copy whose 32,789 cell reads 32,816 is rejected as doc-table-drift and a copy whose save-format header row is renamed is rejected as doc-table-missing."
result: pass
source: automated
summary_file: 18-09-SUMMARY.md
coverage_id: D3
evidence: ["ctest -R ^host_contract_docs$ (host-contract docs pass exit_rows=4 format_rows=16)", "ctest -R ^(host_contract_docs_control|host_contract_docs_missing_control)$"]

### 71. No line of README.md, the native guide, the cartridge guide, the unreleased ledger, docs/host-contract.json or the Playstead research note matches the byte-identical, compatible or interoperab ... mGBA pattern; the note's non-RTC SRAM sentence is replaced by the no-interoperability sentence and the MBC2 512 B versus 256 B difference, and a seeded copy holding the original sentence is rejected inside the same run.
expected: "No line of README.md, the native guide, the cartridge guide, the unreleased ledger, docs/host-contract.json or the Playstead research note matches the byte-identical, compatible or interoperab ... mGBA pattern; the note's non-RTC SRAM sentence is replaced by the no-interoperability sentence and the MBC2 512 B versus 256 B difference, and a seeded copy holding the original sentence is rejected inside the same run."
result: pass
source: automated
summary_file: 18-09-SUMMARY.md
coverage_id: D4
evidence: ["ctest -R ^doc_no_interop_claims$ (no-interop-claims pass files=6 controls=1)", "grep -c 'byte-identical to mGBA' .planning/research/v0.3/PLAYSTEAD-CONTRACT.md prints 0"]

### 72. The phase tail is qualified at its final head: the full phase1 suite passes 1650 of 1650 with 1650 JUnit cases equal to the 1650 lines of tests/expected-tests.txt, the inventory, test-budget, summary-coverage, no-phase-paths and planning-label checks pass, no Phase 18 test exceeds 10 s locally, no workflow file differs from f4082a6, and the project version line is still 0.2.1.
expected: "The phase tail is qualified at its final head: the full phase1 suite passes 1650 of 1650 with 1650 JUnit cases equal to the 1650 lines of tests/expected-tests.txt, the inventory, test-budget, summary-coverage, no-phase-paths and planning-label checks pass, no Phase 18 test exceeds 10 s locally, no workflow file differs from f4082a6, and the project version line is still 0.2.1."
result: pass
source: automated
summary_file: 18-09-SUMMARY.md
coverage_id: D5
evidence: ["ctest --test-dir build -j8 --output-junit phase18-tail.xml at 3c148865: 1650 of 1650 passed", "bash .github/scripts/verify-test-inventory.sh --self-test", "git diff --quiet f4082a6 -- .github/workflows/ and grep -c 'project(GabbaBoy VERSION 0.2.1' CMakeLists.txt prints 1"]

### 73. The five planner discretion choices are recorded as D-115..D-119 in DECISIONS.md, each citing the owning plan SUMMARY, the CTest that pins it and a revisit trigger.
expected: "The five planner discretion choices are recorded as D-115..D-119 in DECISIONS.md, each citing the owning plan SUMMARY, the CTest that pins it and a revisit trigger."
result: pass
source: automated
summary_file: 18-09-SUMMARY.md
coverage_id: D6
evidence: ["git diff -U0 on .planning/context/DECISIONS.md holds exactly 5 added rows naming 56, frame + 16, save_format=none, Undo not applied: undo backup failed; nothing changed and scratch instance"]

## Summary

total: 73
passed: 73
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps

[none]
