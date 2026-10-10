---
phase: GB-03-visible-interactive-dmg
reviewed: 2026-10-10T16:02:18Z
depth: standard
files_reviewed: 6
files_reviewed_list:
  - src/player/session.c
  - tests/player/test_session.c
  - tests/scripts/test_verified_player_output_dir.py
  - tests/scripts/verify-phase3-player.sh
  - .github/workflows/ci.yml
  - .github/workflows/preview.yml
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
status: clean
---

# Phase 3: Code Review Report (re-review after Phase 06.1, PR #54)

**Reviewed:** 2026-10-10T16:02:18Z
**Depth:** standard
**Files Reviewed:** 6
**Status:** clean

## Summary

This re-review covers the code that changed between `9832ba4` and `HEAD` (Phase 06.1 PR #54, merge `ab76d09`) in the six scoped files. The three previously deferred info findings (IN-01, IN-02, IN-03) are now resolved in the code. The drifted code has no new bugs, security issues or quality defects. `python3 -m unittest test_verified_player_output_dir`, run from `tests/scripts`, passes 21 tests, one more than before because of the new IN-03 test. The C tests, the shell script and the workflows were reviewed by reading only. I did not build or run them.

Two scope notes:
- The refactored workflows call `.github/scripts/wait-exact-head-ci.py` and `.github/scripts/check-player-result.sh`. Neither file is in the review scope. I read only `check-player-result.sh` (the `decide` truth table) and did not review the 453-line `wait-exact-head-ci.py`. The workflow call sites are consistent with the arguments they pass.
- Coverage gap that remains: the `close()`-failure branch of `read_rom_file` (`src/player/session.c:149-153`) has no fault-injection test. Only the size-bound message is guarded, by the 2097153-byte case in `player_session_replacement_failure` (`tests/player/test_session.c:131-136`). The close-failure branch is not test-covered. A `close()` failure on a read-only descriptor is rare, and the branch is a simple free-and-fail path. I do not raise this as a finding.

## Resolved / prior findings

Historical items use h4 headings so that parsers reading `### CR-/WR-/IN-` headings see only current open findings. There are none.

#### IN-01 (Info): close() failure message and missing O_NOCTTY in read_rom_file. RESOLVED in Phase 06.1.

- `src/player/session.c:104-107`: `O_NOCTTY` is added to the open flags. A comment explains why both `O_NONBLOCK` and `O_NOCTTY` stay.
- `src/player/session.c:143-153`: the branches are split.
  - An oversized read (`total > PLAYER_SESSION_MAX_ROM_SIZE`) reports "exceeds the 2 MiB read bound".
  - A `close()` failure reports "Could not finish reading the selected ROM." Both paths free the buffer.
- Test coverage covers only the size-bound message: the 2097153-byte case at `tests/player/test_session.c:131-136` asserts "2 MiB read bound". The 2097154-byte case at `:137-141` asserts "bounded regular file", the earlier `fstat` rejection. The close-failure branch has no fault-injection test.

#### IN-02 (Info): duplicated receipt-field fixture in tests. RESOLVED in Phase 06.1.

- `tests/scripts/test_verified_player_output_dir.py:27-42` defines a single `_receipt_fields()` helper. It returns a fresh dict on every call, so tests cannot share mutated state.
- The three former copies now call it, at `:169`, `:193` and `:230` (inside `_publish_sample`). No inline 12-key dict remains.

#### IN-03 (Info): withdrawal-report test covered only the outer call site. RESOLVED in Phase 06.1.

- `tests/scripts/test_verified_player_output_dir.py:284-312`, `test_failed_withdrawal_after_link_is_reported_without_masking_sync_error`:
  - It fails the first directory `fsync` after the archive link, then fails `_withdraw_artifact`. This reaches the inner site at `tests/scripts/verified_player_output_dir.py:180-182`.
  - It asserts that the stderr report is emitted and that the original sync `OSError` still propagates.
  - It asserts that the leftover state is exactly the one published archive with no `.tmp` files.
- The outer site at `:330-332` stays covered by the existing test at `:269`.

#### CR-01 (Critical): release workflow in-repo output directory. Fixed in 91d11d4. Prior history unchanged.

`GBB_VERIFIED_OUTPUT_DIR` is set only under the runner temp directory, and the workflow guard test enforces this. `tests/scripts/verify-phase3-player.sh` still treats `FINAL_ARTIFACT_DIR` as consumed only in the publish branch. The only change there is a new comment block at lines 15-19. The comment is accurate: `--build-package` never publishes, and the `/tmp` fallback applies only to local `--verify-package` runs.

#### WR-01 (Warning): swallowed withdrawal failures. Fixed in 91d11d4, with a follow-on fix in 8151a75. Prior history unchanged.

#### IN-04 (Info): shallow workflow output-directory guard. Fixed in 8151a75. Prior history unchanged.

#### WR-02 (Warning): `prepare` clears the previous verified set. Accepted as intentional, not tracked as a finding.

A stale verified archive and receipt pair must not survive a failed verification run.

## Drift review notes (no findings)

- **`.github/workflows/ci.yml`**
  - The new `player-gate` job is the single place that decides whether player evidence is required.
  - `macos-player-package` is skipped on push events when the gate output is `'false'`.
  - `required-native` now checks out the source, which the self-tests and `check-player-result.sh` need.
  - It requires `player-gate` to be `success` and delegates the decision to `check-player-result.sh`. That script fails closed for a failed, cancelled or skipped gate and for an empty `required` value.
  - The `echo "player_required=${{ github.event_name == 'pull_request' }}"` line interpolates only a boolean expression, so there is no injection surface.
- **`.github/workflows/preview.yml`**
  - The inline polling loops are replaced by `wait-exact-head-ci.py`.
  - The checkout now happens before the wait step, so the script exists in the job. The `ref` is the PR head SHA, which is the version the script runs from.
  - Untrusted-looking values (`EXPECTED_SHA`, `GITHUB_REPOSITORY`) are passed through `env` and quoted.
  - The aggregate gate now requires `player-package-smoke-macos` to be `success` unconditionally. This is consistent because the workflow triggers only on `pull_request`.
- **`tests/player/test_session.c`**
  - `write_sized_file` frees its buffer on every path.
  - The boundary comment is accurate: `st_size` is checked against the 2 MiB bound plus 1.
  - The 2097153-byte case passes `fstat` and reaches the read-bound message. The 2097154-byte case is rejected earlier as "not a bounded regular file".

---

_Reviewed: 2026-10-10T16:02:18Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
