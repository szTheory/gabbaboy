---
phase: GB-05-dmg-audio-and-stable-playback
reviewed: 2026-10-10T11:56:15Z
depth: standard
files_reviewed: 7
files_reviewed_list:
  - src/player/session.c
  - tests/player/test_session.c
  - tests/player/CMakeLists.txt
  - tests/player/expected-tests.txt
  - tests/scripts/verified_player_output_dir.py
  - tests/scripts/test_verified_player_output_dir.py
  - tests/scripts/verify-phase3-player.sh
findings:
  critical: 0
  warning: 0
  info: 1
  total: 1
status: issues_found
---

# Phase 5: Code Review Report (verification-freshness refresh)

**Reviewed:** 2026-10-10
**Depth:** standard (delta since 7b1c491)
**Files Reviewed:** 7
**Status:** issues_found (1 info)

## Summary

Reviewed the delta `7b1c491..HEAD` from Phase 5's perspective. No new critical or warning findings were verified.

- **O_NONBLOCK in `read_rom_file` (src/player/session.c:104):** It is harmless for regular files. On POSIX, O_NONBLOCK has no effect on read(2) of regular files, so ROM loading is unchanged. The flag prevents `open()` from blocking forever on a FIFO with no writer. `fstat` + `S_ISREG` + size bound (lines 109-115) run on the open descriptor before any `read()`, so a FIFO or device is rejected before it is read. The read loop retries on EINTR and treats other errors as failure. The new FIFO regression in `test_session.c` checks that replacement is rejected with the "bounded regular file" error, that the live machine and path are unchanged, and that the FIFO is left in place. `read_save_file` already used the same flag with the same fstat-before-read order.
- **Helper publication (verified_player_output_dir.py):** Archive and receipt are still published under the two fixed names. The receipt carries the same field set as the old inline writer, plus the digest check. The `package_sha256` is recomputed while copying and compared to the candidate build receipt's `package_sha256`. The shell passes arguments in the order `main()` unpacks them (checked by hand). Failures withdraw already-published artifacts, and the archive is never left without its receipt. Phase 5 audio and receipt claims ride in the packaged archive and the unchanged receipt fields, and the delta neither adds nor drops any of them. `python3 tests/scripts/test_verified_player_output_dir.py` ran 20 tests, all OK.
- **CMake and inventory:** `player_verified_output_directory` is registered in both `expected-tests.txt` and `CMakeLists.txt`. `Python3` is a REQUIRED find, so the inventory check cannot silently skip the test.
- **Phase 3 findings:** CR-01, WR-01, WR-01-followon and IN-04 stay fixed. WR-02 stays skipped as intentional. IN-01, IN-02 and IN-03 remain deferred info items. Nothing here duplicates them.

## Info

### IN-01: Default verified output directory moved out of the build root

**File:** `tests/scripts/verify-phase3-player.sh:15-16`
**Issue:** When `GBB_VERIFIED_OUTPUT_DIR` is unset, the verified output now goes to `${RUNNER_TEMP:-${TMPDIR:-/tmp}}/gabbaboy-preview-verified-artifact`. That is a fixed, shared, predictable location. The helper's no-follow directory opening and fixed-name unlink keep this safe, but local runs on a shared `/tmp` could collide with each other or with another user's directory. CI sets the variable explicitly in preview.yml:216 and release.yml:620, so this affects only local runs. Any Phase 5 doc that points at `build/.../preview-verified-artifact` would also be stale.
**Fix:** Optional. Document the new default, or use `mktemp -d` for the fallback.

---

_Reviewed: 2026-10-10_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
