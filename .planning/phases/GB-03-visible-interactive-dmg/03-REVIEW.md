---
phase: GB-03-visible-interactive-dmg
reviewed: 2026-10-10T01:52:47Z
depth: standard
files_reviewed: 8
files_reviewed_list:
  - tests/scripts/verified_player_output_dir.py
  - tests/scripts/test_verified_player_output_dir.py
  - .github/workflows/release.yml
  - tests/scripts/verify-phase3-player.sh
  - tests/player/CMakeLists.txt
  - tests/player/expected-tests.txt
  - src/player/session.c
  - tests/player/test_session.c
findings:
  critical: 0
  warning: 0
  info: 3
  total: 3
status: issues_found
---

# Phase 3: Code Review Report (re-review after 91d11d4 and 8151a75)

**Reviewed:** 2026-10-10
**Depth:** standard
**Files Reviewed:** 8
**Status:** issues_found

## Summary

Fix commits 91d11d4 and 8151a75 resolve CR-01, WR-01, the follow-on WR-01 (reporting can mask errors), and IN-04. The 20 tests in `tests/scripts/test_verified_player_output_dir.py` pass when run from `tests/scripts`. No critical or warning findings remain. WR-02 is accepted as an intentional design choice. Three info items remain open (IN-01, IN-02, IN-03). Status stays `issues_found` only because those info items are open.

## Resolved in this re-review

### CR-01 (was Critical): release workflow in-repo output directory. Fixed in 91d11d4.

Evidence:
- `grep` over `.github` and the script finds only two assignments of `GBB_VERIFIED_OUTPUT_DIR`: `preview.yml:216` (`${{ runner.temp }}/...`) and `release.yml:620` (`"$RUNNER_TEMP/release-player-downloaded"`). The job-level `build/release-player-verified` value is gone.
- Removing the job-level env is safe. `FINAL_ARTIFACT_DIR` is read only at `verify-phase3-player.sh:16` and consumed only at `:296-297`, inside the publish branch of `verify_package ... true`. That branch is reached only via `--verify-package` (`:337-338`).
- `--build-package` calls `verify_package "$ARTIFACT_DIR" false` (`:573`), which skips publication. The `--build-package` calls in `release.yml:589` and `ci.yml:135` therefore never touch the variable.
- The guard test regex `GBB_VERIFIED_OUTPUT_DIR\s*[:=]\s*(\$\{\{[^}]*\}\}\S*|\S+)` matches both forms:
  - `${{ runner.temp }}/x` matches the first alternative.
  - `"$RUNNER_TEMP/x"` matches `\S+`, and the surrounding quotes are stripped by `.strip("'\"")`.
  - The `startswith` allowlist covers `${{ runner.temp }}`, `$RUNNER_TEMP` and `${RUNNER_TEMP}`.
- The test asserts at least one match, so it cannot pass vacuously.

### WR-01 (was Warning): swallowed withdrawal failures. Fixed in 91d11d4.

Evidence:
- Both `except OSError` sites (`verified_player_output_dir.py:181-182`, the inner publish cleanup, and `:327-328`, the outer loop) now call `_report_withdrawal_failure`, which writes to stderr.
- The original exception still propagates through the bare `raise` after the handler.
- The outer loop continues to the remaining withdrawals.
- `test_failed_withdrawal_is_reported_without_masking_original_error` covers the outer site. It asserts the stderr text, that the original `OSError` is raised, and that the unwithdrawn archive remains.

### WR-01 (follow-on, introduced by 91d11d4): reporting could mask the original error. Fixed in 8151a75.

Evidence:
- `_report_withdrawal_failure` now wraps the `print` in `try/except (OSError, ValueError)`. `print` to a closed file raises `ValueError`, and a broken pipe raises `OSError`, so both are covered.
- A new regression test, `test_broken_stderr_does_not_replace_original_publication_error`, redirects a closed `StringIO` to stderr. The shared helper asserts that the original "simulated receipt publication failure" `OSError` still propagates.
- All 20 tests pass.

### IN-04 (was Info): shallow workflow guard. Fixed in 8151a75.

Evidence:
- The guard now globs `*.yml` and `*.yaml`.
- It requires a `${{ runner.temp }}/`, `$RUNNER_TEMP/` or `${RUNNER_TEMP}/` prefix, so `$RUNNER_TEMPX` is rejected.
- It rejects any `..` path segment.
- The current values (`${{ runner.temp }}/verified-player-artifact` and `"$RUNNER_TEMP/release-player-downloaded"`) still pass.
- Still not covered: composite actions under `.github/actions` and multi-line YAML scalars. Neither is used today.

### WR-02 (was Warning): `prepare` clears the previous verified set. Intentional, no longer tracked as a finding.

I agree with the decision. A stale verified pair must not survive a failed verification run, because it could be mistaken for current evidence. That requirement outweighs preserving the last good set. Fresh CI output directories make the destructive case rare.

## Info

### IN-01: Misleading error message when `close()` fails in `read_rom_file`

**File:** `src/player/session.c:152-156`

**Issue:** A failed `close()` and an oversized ROM share one branch, so both report "exceeds the 2 MiB read bound". `open` also lacks `O_NOCTTY`. Both are minor and predate the `O_NONBLOCK` change.

**Fix:** Split the branches and use a "could not read completely" message for the close failure. Add `O_NOCTTY` to the open flags.

### IN-02: Duplicated receipt-field fixture in tests

**File:** `tests/scripts/test_verified_player_output_dir.py:112-125,154-167,215-228`

**Issue:** The 12-key `receipt_fields` dict is copy-pasted in three places, and `_publish_sample` builds the same data. The copies will drift when the receipt schema changes.

**Fix:** Hoist it to a module-level constant or a helper.

### IN-03: New withdrawal-report test covers only the outer call site

**File:** `tests/scripts/test_verified_player_output_dir.py:289-302`

**Issue:** The receipt link fails before any receipt inode is published, so only the outer-loop site at `verified_player_output_dir.py:327` is exercised. The inner site at `:181` (a post-link failure such as a directory `fsync` error, followed by a failed withdrawal) has no report assertion.

**Fix:** Extend the test with a case that fails the directory `fsync` after link and also fails the withdrawal. Assert the stderr text and that the original error is raised.

---

_Reviewed: 2026-10-10_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
