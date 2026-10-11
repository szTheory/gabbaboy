---
phase: GB-07-dmg-game-acceptance-and-regression-baseline
reviewed: 2026-10-10T00:00:00Z
depth: standard
files_reviewed: 35
files_reviewed_list:
  - .github/workflows/ci.yml
  - .github/workflows/libbet-repro.yml
  - CMakeLists.txt
  - cmake/VerifyDmgBaseline.cmake
  - src/accept/digest.c
  - src/accept/gbb_accept.h
  - src/accept/input_script.c
  - src/accept/predicate.c
  - src/accept/sha256.c
  - src/accept/stepper.c
  - src/core/gabbaboy.c
  - src/player/main.c
  - src/player/script_smoke.c
  - src/player/script_smoke.h
  - src/runner/acceptance.c
  - src/runner/acceptance.h
  - src/runner/cases.c
  - src/runner/main.c
  - tests/CMakeLists.txt
  - tests/acceptance/CMakeLists.txt
  - tests/expect_exit.cmake
  - tests/player/CMakeLists.txt
  - tests/player/test_session.c
  - tests/player/verify_script_smoke_surface.cmake
  - tests/scripts/reproduce-libbet.sh
  - tests/scripts/rgb-digest-vector.py
  - tests/scripts/verify-dmg-baseline.sh
  - tests/scripts/verify-libbet-admission.py
  - tests/scripts/verify-phase3-player.sh
  - tests/test_acceptance_cases.c
  - tests/test_acceptance_digest.c
  - tests/test_acceptance_lib.c
  - tests/test_audio.c
  - tests/test_runner.c
  - tests/verify_runner_help.cmake
findings:
  critical: 0
  warning: 5
  info: 5
  total: 10
status: issues_found
---

# Phase 7: Code Review Report

**Reviewed:** 2026-10-10
**Depth:** standard
**Files Reviewed:** 35 (large pre-existing files reviewed as Phase 7 diffs only)
**Status:** issues_found

## Summary

The shared acceptance library, case parser, digest code and CMake/Python gates are carefully bounded. I found no memory-safety, integer-overflow or endianness defects in the C code. The script parser, case parser, SHA-256, PPM and PCM serialisation, the predicate anchor bounds checks and the stall-report size accounting all hold up under tracing. The CMake baseline comparator and the Libbet admission verifier fail closed on every path I traced.

The real defects are a driver/core capacity mismatch that makes some parser-valid scripts unrunnable, a save-suppression ordering gap in the player smoke, a guard that does not cover the code it claims to guard, a silently ignored control flag, and one vacuous test loop. No finding blocks shipping the current fixtures. Several would bite as soon as scripts or ROMs change.

## Warnings

### WR-01: Driver batch size equals the core's total event queue capacity, so valid dense scripts fail with an opaque `drive-error`

**File:** `src/accept/stepper.c:97-118` (also `src/runner/acceptance.c:21`, `src/player/script_smoke.h:21`, `src/accept/gbb_accept.h:169`)
**Issue:** `gbb_accept_drive` accepts `max_batch` up to 64 and the runner uses 64. The core queue holds 64 events in total, counting events still pending (`src/core/gabbaboy.c:6`, `:1554`, which returns `GBB_EVENT_QUEUE_FULL` when `count > 64 - pending`). When a full batch ends the window, the deadline is shortened to the last batched event's time. The stepper may stop up to 47 half-dots short of a deadline, so events inside that slack stay pending. The next batch of up to 64 then overflows the queue.

The script parser accepts such scripts: up to 16384 events and 4096 lines, and `tap X 1hd` lines produce two events per half-dot. I reproduced this with 80 consecutive `tap A 1hd` lines:
`gabbaboy-runner --acceptance tests/acceptance/cases.txt --case libbet --observe --input-script dense.input` printed `status=unsupported ... reason=drive-error status_code=4`. A 20-tap variant ran normally.

Two problems follow. The parser and driver disagree about what is runnable. The failure is also reported as an anonymous "drive-error", not as a delivery or queue-full cause.
**Fix:** Cap batches below the queue capacity and handle back-pressure explicitly. One option is to reject `max_batch > 32` in `gbb_accept_drive` (`gbb_accept.h:169` and `stepper.c:60`). Another is to treat a queue-full result by shortening the window to the first undelivered event and retrying after the stepper advances. Also map `GBB_ACCEPT_DRIVE_DELIVER_FAILED` to a named reason (for example `reason=event-delivery-failed`) in `acceptance.c:1155`, instead of falling into `default`. Add a runner test with a dense script.

### WR-02: Player script smoke sets `skip_final_save` only after fallible steps, so an early exit can still run the battery-save path

**File:** `src/player/main.c:2128-2144` (consumer at `src/player/main.c:2170-2171`)
**Issue:** `run_script_smoke` loads the ROM with `player_session_replace_rom` (line 2128), which populates `app->save_identity` (including `battery_backed`). It then runs the digest-identity check (line 2139). On a mismatch it prints "The ROM changed between validation and load" and jumps to `done` at line 2142, before `app->skip_final_save = true` on line 2144. `destroy_player` writes the battery save when `machine != NULL && save_identity.battery_backed && !skip_final_save`.

That mismatch branch is exactly the case where a different, possibly battery-backed, ROM was loaded. The diagnostic's stated contract ("never writes player state") is broken on that path. It needs a file swap between validation and load, so it is narrow, but it is the one path the identity check exists to catch.
**Fix:** Set `app->skip_final_save = true;` at the top of `run_script_smoke`, before `gbb_create`. It costs nothing, because the diagnostic never wants a save.

### WR-03: The script-smoke "attack surface" guard scans only `script_smoke.c/.h`, not the `run_script_smoke` code in `main.c`

**File:** `tests/player/verify_script_smoke_surface.cmake:718-741`
**Issue:** The guard exists so a future change cannot widen what a replayed script can reach: environment, network, file writes, battery persistence. It applies the forbidden-token and write-mode `fopen` scan to `script_smoke.c` and `script_smoke.h` only. Nearly all of the diagnostic's risk lives in `src/player/main.c` (`script_deliver`, `script_progress`, `run_script_smoke`, lines 2062-2162): ROM loading, save identity, `skip_final_save`, and the SDL event push. For `main.c` the guard checks one regex, an environment read whose arguments contain `SCRIPT`.

The guard therefore passes if `run_script_smoke` calls `player_session_load_battery`, `attempt_battery_save` or `fopen(..., "wb")`. The injected-`getenv` self-test only proves the guard catches the thing in the file it already scans. WR-02 is an example of a persistence defect in the unscanned region.
**Fix:** Extract the `script_deliver`/`script_progress`/`run_script_smoke` block from `main.c` into the scanned module, or have the guard slice `main.c` between `static bool script_scancode` and `static void destroy_player` and run the same forbidden-token checks on that slice. Add a self-test that injects a forbidden token into the slice.

### WR-04: `--mutate` (and `--raw-verdict`) are silently ignored for frame-digest cases

**File:** `src/runner/acceptance.c:799-897` (flag validation in `src/runner/main.c`, acceptance block)
**Issue:** `run_frame_case` never reads `options->has_drop_button`, `mutate_label` or `raw_verdict`. It rejects only `observe_input_script`, `has_frame_digest_at` and `pcm_only`. A control run such as `--case daa-ldbb --mutate drop:START` therefore executes unmutated and can print `status=pass` with no `mutate=` note, because `run_note` is never called on that path. The same applies to `--suite --mutate`, which applies the mutation to progress-predicate cases only. A control that quietly does not control is a fail-open check for anyone relying on the flag.
**Fix:** In `run_frame_case`, return `input_error(c, "mutate-not-applicable")` when `options->has_drop_button` is set. Do the same for `raw_verdict` with a non-predicate oracle. For `--suite --mutate`, either reject frame cases or print the note.

### WR-05: The "title garbage" half of the predicate truth-table test cannot discriminate

**File:** `tests/test_acceptance_lib.c:319-327`
**Issue:** The loop fills WRAM with pseudo-random bytes and then forces `ram[0xC4E8] = 3` (`floor_width`) on every round, before asserting the predicate is false. With `floor_width != 2` the predicate is false regardless of every other term (`predicate.c:100`). The 64 rounds therefore test only the `floor_width == 2` clause. If the `hw_capability`, `attract_mode`, `cur_floor`, `floor_height`, `max_score` or `cur_score` clauses were deleted, this loop would still pass. The single-field negatives below it do cover those clauses one at a time, so the file as a whole still has coverage. The garbage test itself, as labelled, is vacuous.
**Fix:** Instead of pinning width to 3, skip any round where the random bytes happen to satisfy all seven terms (or force exactly one other term to a wrong value per round, cycling through the terms). Then the loop exercises the whole predicate.

## Info

### IN-01: `gbb_accept_write_ppm` can leave a truncated file on write or close failure

**File:** `src/accept/digest.c:62-71`, `src/accept/gbb_accept.h:213-215`
**Issue:** The header documents "nothing is created" only for an invalid shade, which holds. On a later `fwrite` or `fclose` failure (disk full) the function returns 3 but leaves a short `.ppm` behind. Checkpoint dumps (`acceptance.c:131-138`) then set `dump_failed`, so the run is reported, but the stale file remains in the dump directory.
**Fix:** On `failed`, call `remove(path)` before returning 3, and say so in the header comment.

### IN-02: NUL-byte test fixture writes 20 bytes from a 19-byte literal

**File:** `tests/player/test_session.c:1113`
**Issue:** `fwrite("gbinput 1\nwait 1f\0\n", 1, 20, file)` writes the literal's 19 characters plus its terminating NUL. The embedded NUL on line 2 still triggers the intended rejection, so the test is correct, but the count is accidental. The file also ends with an extra NUL after the final LF.
**Fix:** Use `sizeof("gbinput 1\nwait 1f\0\n") - 1u` and assert on that value, so the fixture is exactly what the comment says.

### IN-03: CI "Record acceptance and Mooneye observations" steps assert nothing

**File:** `.github/workflows/ci.yml` (the three added "Record acceptance and Mooneye observations" steps)
**Issue:** The comment says "the same observation lines must come out on every native OS at the same head", but the step only prints the lines. It fails only on a runner crash. Cross-OS equality is enforced indirectly, because each OS compares against the single frozen ledger in `dmg_baseline`. `libbet-no-input` is observed here but never compared anywhere, so a drift in that run's output would go unnoticed.
**Fix:** Reword the comment to "recorded for the log", or pipe the output through the comparator. If the no-input observation matters, add its keys to the ledger.

### IN-04: `player_script_smoke_prepare` formats into `err` without a NULL check

**File:** `src/player/script_smoke.c:48`, `:60`
**Issue:** `set_message` guards `err == NULL`, but the two direct `snprintf(err, err_capacity, ...)` calls do not. The header (`script_smoke.h:34`) does not say `err` must be non-NULL. The one in-tree caller passes a buffer, so this is latent only.
**Fix:** Use `set_message`-style guarding for the prefixed messages, or document `err` as required.

### IN-05: Install-tree scan does not descend into directory symlinks

**File:** `tests/scripts/verify-libbet-admission.py:343-360`
**Issue:** `os.walk(..., followlinks=False)` lists directory symlinks in `dirs`, so their names are checked for "libbet", but their contents are not scanned. For the extracted package tree this is acceptable, since a symlink to an in-tree directory is reached through its real path. A symlink to a directory outside the tree would hide a ROM from the redistribution guard.
**Fix:** Fail the scan if a directory entry is a symlink, as `read_tree` already does for the closure derivation.

---

_Reviewed: 2026-10-10_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
