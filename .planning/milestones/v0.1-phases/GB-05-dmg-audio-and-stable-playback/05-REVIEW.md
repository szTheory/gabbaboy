---
phase: GB-05-dmg-audio-and-stable-playback
reviewed: 2026-10-10T16:13:25Z
depth: standard
files_reviewed: 5
files_reviewed_list:
  - src/player/session.c
  - tests/player/test_session.c
  - tests/scripts/test_verified_player_output_dir.py
  - tests/scripts/verify-phase3-player.sh
  - .github/workflows/preview.yml
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
status: clean
---

# Phase 5: Code Review Report (Phase 06.1 delta refresh)

**Reviewed:** 2026-10-10T16:13:25Z
**Depth:** standard (delta `f39faac..HEAD`; Phase 06.1 PR #54, merged at ab76d09; HEAD differs from ab76d09 only under `.planning/`)
**Files Reviewed:** 5
**Status:** clean

## Summary

Reviewed the delta from Phase 5's perspective (DMG audio and stable playback, AUDIO-01..03, HOST-01/02; session transitions must leave the active session unchanged on rejection). No critical, warning, or info findings were verified.

- **`src/player/session.c` `read_rom_file` (lines 104-155):**
  - `O_NOCTTY` was added next to `O_NONBLOCK`. The new comment is accurate: the two flags solve different problems, and both are POSIX `open` flags with no effect on regular-file reads. The `fstat`, `S_ISREG` and size-bound check still runs on the open descriptor before any `read()`.
  - The close/bound split is correct. A ROM of exactly 2 MiB + 1 byte passes the `fstat` bound (`<= MAX + 1`) and fills the `MAX + 1` read buffer. `total > MAX` then yields the "2 MiB read bound" message. A `close()` failure now reports its own message instead of being misreported as an oversize ROM. Both paths free `bytes` and leave `*out_rom` and `*out_size` unwritten. The caller therefore sees a rejection with no partial output.
  - The Phase 5 transition invariant holds. The function is read-only on the session, and each rejection happens before any replacement is committed.
- **`tests/player/test_session.c`:** The new `write_sized_file` helper checks every allocation and write/close result and frees on every path. The two new replacement cases pin the exact boundary: +1 byte gives the read-bound message and +2 bytes gives the "bounded regular file" message. Each one asserts `require_unchanged`, which confirms that the machine, path and identity are intact after rejection. This is a meaningful regression test for the stated invariant.
- **`tests/scripts/test_verified_player_output_dir.py`:** `_receipt_fields()` returns a fresh dict on each call, so the three call sites do not share mutable state. The field set is identical to the three inlined copies it replaced. The new `test_failed_withdrawal_after_link_is_reported_without_masking_sync_error` asserts the original error is raised, the withdrawal failure is reported on stderr, and no `.tmp` file is left. I ran `python3 tests/scripts/test_verified_player_output_dir.py`: **Ran 21 tests ... OK**.
- **`.github/workflows/preview.yml`:**
  - The inline polling shell was replaced by `.github/scripts/wait-exact-head-ci.py`. Checkout now precedes the gate in all three jobs, which the script needs.
  - The script is read-only (GET through `gh api` with an argv list, no shell or jq built from input). It validates the SHA and repo with strict regexes and filters on head SHA, event and workflow path. The newest `run_number` decides. A failing conclusion needs two consecutive agreeing polls, and the gate fails closed at the deadline. I ran `python3 .github/scripts/wait-exact-head-ci.py --self-test`: 26 cases passed.
  - The player aggregate check no longer treats `skipped` as acceptable. This is consistent because the workflow triggers only on `pull_request`. The removed `PLAYER_REQUESTED` was therefore always true, and the behaviour is unchanged.
  - The job-level `run_attempt` for the player artifact is preserved through `--attempt-job`.
- **`tests/scripts/verify-phase3-player.sh`:** Only a comment was added (see below). Behaviour is unchanged.

## Previously reported

#### IN-01 (prior review): local-only `GBB_VERIFIED_OUTPUT_DIR` default in `verify-phase3-player.sh` (addressed in PR #54, commit ecb0db7; documentation only)

**Status:** Resolved as a documentation-only change. I confirmed the comment is present at `tests/scripts/verify-phase3-player.sh:15-20`, directly above the `FINAL_ARTIFACT_TEMP_ROOT` / `FINAL_ARTIFACT_DIR` defaults, and that it is accurate:

- The comment says CI sets `GBB_VERIFIED_OUTPUT_DIR` for every `--verify-package` call. That is true: `.github/workflows/preview.yml:145` sets it for the player job and `.github/workflows/release.yml:620` sets it for the release consumer.
- The comment says `--build-package` never publishes to this directory. That is true: the only `verified_player_output_dir.py --publish` call (line 301) sits in the `--verify-package` path (`verify_package ... true`, line 342).
- The comment says the fallback only matters for local `--verify-package` runs. It says that with `TMPDIR` unset the default lands in the shared `/tmp`, and advises a private directory. Both statements match the default expression on lines 20-21, and the advice is sound.
- The line "The helper's no-follow open and fixed-name unlink contain the risk" restates a property already accepted in earlier reviews. I did not re-audit `verified_player_output_dir.py`, which is outside this delta's file list.

The default expression itself is unchanged, so the local shared-`/tmp` exposure remains as documented. This is acceptable as an informational, documented limitation and is not re-raised.

---

_Reviewed: 2026-10-10T16:13:25Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
