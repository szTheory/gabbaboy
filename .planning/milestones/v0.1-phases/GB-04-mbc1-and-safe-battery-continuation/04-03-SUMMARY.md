---
phase: GB-04-mbc1-and-safe-battery-continuation
plan: 03
subsystem: player-persistence
tags: [c17, battery-save, recovery, atomic-write, fault-injection]
requires:
  - phase: GB-04-mbc1-and-safe-battery-continuation
    provides: MBC1 battery API and versioned player save envelope
provides:
  - Exact-ROM and cartridge-keyed save identity with strict bounded envelope reads
  - Unique preservation of rejected regular saves and fail-closed unsafe-file handling
  - Fault-tested same-directory save replacement and interruption behavior
affects: [player-session, battery-persistence, save-recovery]

actuals:
  tasks: 2
  commits: 1
key-files:
  created: []
  modified:
    - src/player/session.c
    - src/player/session.h
    - tests/player/test_session.c
    - tests/player/CMakeLists.txt
    - tests/player/expected-tests.txt
requirements-completed: [SAVE-03]
---

# Plan 04-03 Summary

## Outcome

Player saves now follow exact ROM bytes plus explicit MBC1/type/RAM identity, reject invalid or unsafe files before import, preserve rejected regular files under unique recovery names, and replace valid saves through a bounded same-directory write protocol.

## Commit

1. `1c6e80c feat(04-03): recover rejected saves and preserve atomic writes`
2. This summary commit.

## Implementation

- Save filenames use lowercase SHA-256 of the exact ROM bytes and an explicit `mbc1`/cartridge-type/RAM-size suffix. Moving identical ROM bytes retains identity; different ROM bytes with the same basename get a different key.
- Reads reject symlinks and non-regular files without blocking on FIFOs. Regular-file reads are bounded to 32,820 bytes; the largest accepted envelope is 32,819 bytes. Header, version, digest, type, length, exact total size, and CRC are validated before core import.
- Invalid regular files are moved with exclusive no-overwrite recovery naming. Recovery-directory sync failure attempts to restore the original name; if preservation cannot be established, the original remains and persistence is disabled. Successful recovery activates fresh `$FF` RAM and leaves persistence available for later guest changes.
- Save replacement checks the target is a regular file, creates an exclusive same-directory temporary, writes the complete envelope, syncs it, renames it, and syncs the directory where supported. Pre-rename failures preserve the old target and keep the generation dirty. A directory-sync failure reports uncertain durability while the target remains a complete new envelope.
- Added a test-only, one-shot fault seam in a separately compiled adapter target. Production continues to use direct OS calls; no dependency or general filesystem abstraction was added.

## Test Evidence

- Plan command: bash tests/scripts/verify-phase3-player.sh — passed; 30/30 optional player CTests, including 17 session cases, and the extracted-package two-process smoke.
- Candidate package SHA-256: `3589e7927e36553f693689679585de456cd1f353a20e9fc7eaaf066d1928a335`.
- Coverage includes moved-ROM identity, same-basename collisions, wrong digest/type/length, wrong version, bad CRC, truncation, trailing bytes, oversized files, symlink/FIFO rejection, recovery collision and failure, 8 KiB and maximum 32 KiB envelopes, temp-create/short-write/file-sync/rename/directory-sync faults, and child interruption before and after rename.
- Rejected-save tests assert exact recovery bytes or an untouched original and unchanged core RAM. Write-fault tests inspect the complete target and dirty generation, not only return codes.
- `git diff --check` passed. The exact player verifier needed scoped permission for its unique synthetic save under SDL's per-user application directory; the final run passed and removed the test save.

## Plan Deviations

- The two tasks share the same adapter and test harness, so recovery and atomic-write behavior were committed together in one implementation commit. The named regression cases were run against the integrated implementation; the plan's red-before-green sequence was not split into separate commits.
- The existing failed-replacement test had used cartridge type `$01` as an unsupported example. Since Plan 04-02 correctly added MBC1 `$01`, the fixture now declares valid unsupported MBC3 type `$13` and has its header checksum recalculated.

## Evidence Limits

The interruption tests kill a child at controlled pre- and post-rename points and verify the target is the old or new complete envelope. They do not establish physical power-loss durability. Directory-sync failures remain reported as durability-uncertain.

## Next

Continue with Plan 04-04, which owns player-session lifecycle, save cadence, status, and writer-lock behavior.
---
*Phase: GB-04-mbc1-and-safe-battery-continuation*
*Completed: 2026-10-07*

## Self-Check: PASSED

- All five modified key files exist, and implementation commit `1c6e80c` is an ancestor of the current branch.
- The exact plan verification command passed with all 30 optional player tests and packaged smoke green.
