---
phase: GB-03-visible-interactive-dmg
reviewed: 2026-10-10T01:50:24Z
depth: standard
files_reviewed: 7
files_reviewed_list:
  - tests/scripts/verified_player_output_dir.py
  - tests/scripts/test_verified_player_output_dir.py
  - tests/scripts/verify-phase3-player.sh
  - tests/player/CMakeLists.txt
  - tests/player/expected-tests.txt
  - src/player/session.c
  - tests/player/test_session.c
findings:
  critical: 1
  warning: 2
  info: 2
  total: 5
status: issues_found
---

# Phase 3: Code Review Report

**Reviewed:** 2026-10-09
**Depth:** standard
**Files Reviewed:** 7
**Status:** issues_found

Historical note: the prior review's CR-01 was fixed; its full text remains in git history.

## Summary

The all-or-nothing archive+receipt publication in `verified_player_output_dir.py` is sound. Publication uses directory-relative hardlinks with an inode identity check. On failure it withdraws only inodes it published. It keeps concurrently replaced files and re-raises the original error. The `finally` block closes both descriptors on every path. The first `_publish_new_artifact` failure path cleans up its own artifact. Any later failure, including a `KeyError` from `receipt_fields`, withdraws the archive. The `O_NONBLOCK` change in `session.c` is correct: the FIFO opens without blocking, `fstat` rejects it as non-regular, and the new test asserts the error text and that the FIFO is unchanged.

The main concern is a cross-file contract break. The helper now rejects any output directory inside the repository, but the release workflow still passes repository-relative output directories. I traced this statically and did not execute the workflow.

## Critical Issues

### CR-01: Release workflow passes in-repo output directories that the helper now rejects

**File:** `.github/workflows/release.yml:621` (also `:494`); rejection at `tests/scripts/verified_player_output_dir.py:78-79,85-86`

**Issue:** The "Download and smoke the attached player archive" step runs `GBB_VERIFIED_OUTPUT_DIR=build/release-player-downloaded bash tests/scripts/verify-phase3-player.sh --verify-package build/downloaded-player`. `--verify-package` calls `verify_package ... true`, which now publishes through the helper (`verify-phase3-player.sh:296`). The helper resolves the relative path against the workspace, which is the repository root. It then raises `ValueError("output directory must be outside the filesystem and repository roots")`. The script turns that into `fail 'could not safely publish the verified package and receipt'`. If the job reaches this step as written, the published-release verification fails deterministically. The job-level `GBB_VERIFIED_OUTPUT_DIR: build/release-player-verified` at line 494 has the same defect. It is overridden at line 621, but it would break any other use. `preview.yml:216` correctly uses `${{ runner.temp }}`, which suggests this was missed when the helper tightened its rules. The `.github` directory is outside this review's file list, and the Phase 6 review did not flag it.

**Fix:** Point both variables outside the checkout, as `preview.yml` does:
```yaml
GBB_VERIFIED_OUTPUT_DIR: ${{ runner.temp }}/release-player-verified
...
GBB_VERIFIED_OUTPUT_DIR="$RUNNER_TEMP/release-player-downloaded" bash tests/scripts/verify-phase3-player.sh --verify-package build/downloaded-player
```
Alternatively, drop the override and use the script default. Add a CI or test check that every workflow value of `GBB_VERIFIED_OUTPUT_DIR` is outside the workspace.

## Warnings

### WR-01: Failed withdrawal is swallowed silently, so a partial artifact set can remain with no signal

**File:** `tests/scripts/verified_player_output_dir.py:178-186,311-316`

**Issue:** Withdrawal is best effort, and any `OSError` is discarded. If the receipt publication fails and then the archive unlink or `fsync` also fails, the archive is left on disk with no receipt. The CLI prints only the original error and exits 1. An operator or downstream upload step that globs the output directory could still pick up an unreceipted archive, which defeats the all-or-nothing guarantee. This path is untested: the tests only inject failures into `link` and directory `fsync`, never into the withdrawal itself.

**Fix:** Keep the original exception as the one that propagates, but report each failed withdrawal to stderr, for example `print(f"WARNING: could not withdraw {name}: {e}", file=sys.stderr)`. Add a test that makes `os.unlink` fail during withdrawal and asserts the warning is emitted.

### WR-02: `prepare` deletes the previous verified set before the replacement is known to succeed

**File:** `tests/scripts/verified_player_output_dir.py:103-107,225-227`

**Issue:** `publish_verified_artifacts` runs `_prepare_output_dir`, which unlinks any existing archive and receipt, before the new archive is copied and digest-checked. If the digest check, copy, or publication then fails, the output directory is left empty. The previously verified pair is lost. A failed run therefore destroys the last good artifact, which contradicts the all-or-nothing intent of this change. This only matters when the output directory is reused. The default path and the CI paths are fresh, so it is minor in practice.

**Fix:** Skip pre-deletion for the publish path. Publish to temporaries, then replace each name atomically with `os.rename(temp, name, src_dir_fd=..., dst_dir_fd=...)`. The archive and receipt would still be two renames, so a window remains. Alternatively, document that republishing into a populated directory is destructive on failure.

## Info

### IN-01: Misleading error message when `close()` fails in `read_rom_file`

**File:** `src/player/session.c:152-156`

**Issue:** A failed `close()` and an oversized ROM (`total > PLAYER_SESSION_MAX_ROM_SIZE`) share one branch. Both report "The selected ROM exceeds the 2 MiB read bound." A `close` error on a ROM of valid size gets the wrong diagnosis. This predates the `O_NONBLOCK` change. Separately, `open` has no `O_NOCTTY`. Opening a terminal device node as a ROM by a session leader could acquire it as the controlling terminal before the `S_ISREG` rejection. This is a very small risk.

**Fix:** Split the branches, using the same "Could not read the selected ROM completely." message for the close failure. Add `O_NOCTTY` to the open flags.

### IN-02: Duplicated receipt-field fixture in tests

**File:** `tests/scripts/test_verified_player_output_dir.py:112-125,154-167,215-228`

**Issue:** The 12-key `receipt_fields` dict is copy-pasted in three places, and `_publish_sample` already builds the same data. Drift between the copies is likely when the receipt schema changes.

**Fix:** Hoist it to a module-level `SAMPLE_RECEIPT_FIELDS` constant or a helper method.

---

_Reviewed: 2026-10-09_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
