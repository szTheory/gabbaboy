---
phase: GB-07-dmg-game-acceptance-and-regression-baseline
fixed_at: 2026-10-11T00:00:00Z
review_path: .planning/phases/GB-07-dmg-game-acceptance-and-regression-baseline/07-REVIEW.md
iteration: 1
findings_in_scope: 10
fixed: 8
skipped: 2
status: partial
---

# Phase 7: Code Review Fix Report

**Fixed at:** 2026-10-11
**Source review:** 07-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 10 (WR-01..WR-05 and IN-01..IN-05; IN-03 and IN-05 were skipped)
- Fixed: 8
- Skipped: 2 (IN-03, IN-05)

**Verification:** ran in the main checkout (no worktree). `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1`: 261 tests, 259 passed on the first full run. The two timeouts (`acceptance_unexpected_pass`, `acceptance_core_mutant`) occurred while `verify-phase3-player.sh` ran concurrently; both passed when rerun alone. `verify-phase3-player.sh --build-package`: 56/56 player tests passed and the package smoke passed. No frozen digest, `tests/baseline/dmg-cpu-b-v1.txt`, or Libbet acceptance digest was changed.

## Fixed Issues

### WR-01: Dense scripts fail with an opaque `drive-error`

**Files modified:** `src/runner/acceptance.c`, `tests/acceptance/CMakeLists.txt`, `tests/acceptance/inputs/dense-taps.input`, `tests/expected-tests.txt`
**Commit:** 79c9876
**Applied fix:** `GBB_ACCEPT_DRIVE_DELIVER_FAILED` now prints `reason=event-delivery-failed detail=core-queue-full-or-invalid`. New test `acceptance_dense_script_delivery_failed` runs an 80-tap one-half-dot script. A batch cap (tried at 32) was prototyped and did not make the dense script run, because the core only drains events at about 47 half-dot granularity. It was reverted. Real back-pressure in the driver is a design change and was not attempted. Status: fixed (named reason); the underlying capacity limit remains.

### WR-02: `skip_final_save` set too late in `run_script_smoke`

**Files modified:** `src/player/main.c`
**Commit:** fe1fb68
**Applied fix:** `app->skip_final_save = true` now runs before `gbb_create` and the ROM load. The WR-03 guard enforces the ordering.

### WR-03: Surface guard did not cover `run_script_smoke`

**Files modified:** `tests/player/verify_script_smoke_surface.cmake`, `tests/player/CMakeLists.txt`, `tests/player/expected-tests.txt`
**Commit:** d146902
**Applied fix:** The guard extracts `script_scancode` through `destroy_player` from `main.c` and scans it for the forbidden tokens (allowing `player_session_replace_rom`) and any `fopen`. It requires `skip_final_save = true` before the ROM load. New `player_script_smoke_surface_main_selftest` injects `attempt_battery_save` into the slice and expects failure. The pre-WR-02 `main.c` is also rejected by the guard.

### WR-04: `--mutate` ignored for frame-digest cases

**Files modified:** `src/runner/acceptance.c`, `tests/acceptance/CMakeLists.txt`, `tests/expected-tests.txt`
**Commit:** 3609111
**Applied fix:** `run_frame_case` returns `invalid reason=mutate-not-applicable` (exit 2) for `--mutate` or `--raw-verdict`. New tests: `acceptance_ldbb_mutate_rejected`, `acceptance_ldbb_raw_verdict_rejected`. A `--suite --mutate` run now fails on frame cases rather than skipping them silently.

### WR-05: Vacuous title-garbage loop

**Files modified:** `tests/test_acceptance_lib.c`
**Commit:** 97d3225
**Applied fix:** Rounds 0..6 of every eight start from random WRAM, force all seven predicate bytes to the play-hit values, then break one clause. Round 7 is fully random. Deleting a clause from `predicate.c` makes the test fail.

### IN-01: Truncated PPM left behind on write or close failure

**Files modified:** `src/accept/digest.c`, `src/accept/gbb_accept.h`
**Commit:** 7aec1ed
**Applied fix:** `remove(path)` on failure; the header comment is updated. No automated test: the failure needs a full disk or `/dev/full`, which is not portable.

### IN-02: NUL-byte fixture count

**Files modified:** `tests/player/test_session.c`
**Commit:** 8eebe9d
**Applied fix:** The length is `sizeof(literal) - 1`.

### IN-04: Unchecked NULL `err` in `player_script_smoke_prepare`

**Files modified:** `src/player/script_smoke.c`
**Commit:** 7caac52
**Applied fix:** The two direct `snprintf` calls are guarded like `set_message`.

## Skipped Issues

### IN-03: CI observation steps assert nothing

**File:** `.github/workflows/ci.yml`
**Reason:** Needs a decision on whether to compare against the ledger or reword the comment. It is a CI policy choice and cannot be checked locally, so it was not changed.
**Original issue:** The step comment claims cross-OS equality, but the step only prints lines. `libbet-no-input` is never compared.

### IN-05: Install-tree scan does not descend into directory symlinks

**File:** `tests/scripts/verify-libbet-admission.py:343-360`
**Reason:** The fix changes admission-verifier behavior and needs its own negative fixture. It was kept out of this pass.
**Original issue:** A directory symlink to outside the tree could hide a ROM from the redistribution guard.

---

_Fixed: 2026-10-11_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
