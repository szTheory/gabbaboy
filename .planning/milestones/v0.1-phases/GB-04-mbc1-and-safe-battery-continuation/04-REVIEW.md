---
phase: GB-04-mbc1-and-safe-battery-continuation
reviewed: 2026-10-10T16:06:11Z
depth: standard
files_reviewed: 2
files_reviewed_list:
  - src/player/session.c
  - tests/player/test_session.c
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
status: clean
---

# Phase 4: Code Review Report

**Reviewed:** 2026-10-10T16:06:11Z
**Depth:** standard
**Files Reviewed:** 2
**Status:** clean

## Summary

Fresh re-review of drift in `src/player/session.c` and `tests/player/test_session.c`
since diff_base `bce8564`, introduced by Phase 06.1 PR #54 (merge `ab76d09`).
Scope was the `git diff bce8564 HEAD` hunks; `read_save_file` is unchanged and was
not re-raised.

Changes examined:

- `read_rom_file` (`src/player/session.c`): added `O_NOCTTY` to the open flags, and
  split the former combined `close_result != 0 || total > MAX` branch into a
  size-bound branch ("exceeds the 2 MiB read bound") and a separate `close()`
  failure branch ("Could not finish reading the selected ROM.").
- `tests/player/test_session.c`: new `write_sized_file` helper and 2097153- and
  2097154-byte replacement-failure assertions.

Verification of the SAVE-03 hardening and replacement-failure behaviour:

- Open still uses `O_NONBLOCK | O_NOFOLLOW | O_CLOEXEC`, and `O_NOCTTY` is purely
  additive. The `fstat` check still requires `S_ISREG`, non-negative size, and
  `st_size <= MAX + 1`. The FIFO path is still rejected before any `read()`, and
  the existing `mkfifo` assertion is untouched.
- Resource handling on every exit branch of `read_rom_file`: open failure (no fd,
  no buffer); `fstat` rejection (fd closed, no buffer yet); `malloc` failure (fd
  closed); read error (buffer freed, fd closed); over-bound (fd closed before the
  check, buffer freed); `close()` failure (fd already consumed by `close`, buffer
  freed); success (buffer ownership passes to the caller via `*out_rom`). No leak
  or double close was introduced. The split makes the `close()` failure message
  accurate rather than mislabelling it as a size overrun.
- Output parameters `*out_rom` and `*out_size` are written only on the success
  path, so replacement failure still leaves the session unchanged.
- Test arithmetic is correct: with `MAX = 2 MiB`, a file of `MAX + 1` bytes passes
  `fstat`, is read in full (`total == capacity`), and reaches the "2 MiB read bound"
  message. A file of `MAX + 2` bytes fails `fstat` and yields "bounded regular
  file". `write_sized_file` frees its buffer on the `fopen` failure and normal
  paths, and `require_unchanged` follows each failed replacement.

Coverage note: the `close()`-failure branch has no fault-injection test. It was
verified by inspection only and is not test-covered.

No findings in the drifted code.

## Narrative Findings (AI reviewer)

No current findings.

## Prior review (2026-10-09)

History preserved from the earlier Phase 4 review. Headings are h4 so that they
are not parsed as current findings.

#### Prior status

Reviewed 2026-10-09T17:01:28Z, depth standard, 26 files, status clean (0 critical,
0 warning, 0 info).

#### Prior summary

The initial 26-file Phase 4 review found one warning: a user-selected FIFO could
block ROM loading before the regular-file check. The focused follow-up re-reviewed
`src/player/session.c` and `tests/player/test_session.c`. ROM input now opens with
`O_NONBLOCK` and retains the `fstat` regular-file check. The replacement-failure
regression creates a FIFO, confirms replacement is rejected, and verifies that the
prior ROM path and guest RAM remain unchanged. The warning is closed; no findings
remained. The orchestrator reported the then-current player verifier passed all 50
cases.

#### Prior files reviewed (26)

.gitattributes, .github/workflows/fixture-repro.yml, .github/workflows/preview.yml,
CMakeLists.txt, cmake/PreviewPackageSmoke.cmake, cmake/VerifyInstalledPackage.cmake,
fixtures/mbc1-continuation/continuation.asm, include/gabbaboy/gabbaboy.h,
src/core/gabbaboy.c, src/player/limitations.h, src/player/main.c,
src/player/session.c, src/player/session.h, tests/CMakeLists.txt,
tests/consumers/c/main.c, tests/consumers/cpp/main.cpp, tests/player/CMakeLists.txt,
tests/player/test_continuation.c, tests/player/test_limitations.c,
tests/player/test_session.c, tests/scripts/reproduce-mbc1-continuation.sh,
tests/scripts/verify-phase3-player.sh, tests/test_battery.c,
tests/test_battery_fuzz.c, tests/test_cartridge.c, tests/test_loader.c.

#### Prior narrative findings

No unresolved findings. WR-01 (FIFO could block ROM loading before the
regular-file check) was closed by the `O_NONBLOCK` hardening and the `mkfifo`
regression described above.

---

_Reviewed: 2026-10-10T16:06:11Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
