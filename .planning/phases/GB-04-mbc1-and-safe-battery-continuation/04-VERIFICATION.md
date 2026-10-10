---
phase: GB-04-mbc1-and-safe-battery-continuation
verified: 2026-10-10T16:07:17Z
status: passed
score: 7/7 must-haves verified
covered_files:
  - .planning/phases/GB-04-mbc1-and-safe-battery-continuation/04-01-PLAN.md
  - .planning/phases/GB-04-mbc1-and-safe-battery-continuation/04-01-SUMMARY.md
  - .planning/phases/GB-04-mbc1-and-safe-battery-continuation/04-02-PLAN.md
  - .planning/phases/GB-04-mbc1-and-safe-battery-continuation/04-02-SUMMARY.md
  - .planning/phases/GB-04-mbc1-and-safe-battery-continuation/04-03-PLAN.md
  - .planning/phases/GB-04-mbc1-and-safe-battery-continuation/04-03-SUMMARY.md
  - .planning/phases/GB-04-mbc1-and-safe-battery-continuation/04-04-PLAN.md
  - .planning/phases/GB-04-mbc1-and-safe-battery-continuation/04-04-SUMMARY.md
  - .planning/phases/GB-04-mbc1-and-safe-battery-continuation/04-05-PLAN.md
  - .planning/phases/GB-04-mbc1-and-safe-battery-continuation/04-05-SUMMARY.md
  - .planning/phases/GB-04-mbc1-and-safe-battery-continuation/04-06-PLAN.md
  - .planning/phases/GB-04-mbc1-and-safe-battery-continuation/04-06-SUMMARY.md
  - .planning/phases/GB-04-mbc1-and-safe-battery-continuation/04-07-PLAN.md
  - .planning/phases/GB-04-mbc1-and-safe-battery-continuation/04-07-SUMMARY.md
  - src/player/session.c
  - tests/player/test_session.c
covered_digest: "v3:sha256:630564dc243ccaed6af666c486a585ebb5f767e61f5f0030f919ec532b5eff5e"
behavior_unverified: 0
overrides_applied: 0
decision_coverage:
  honored: 16
  total: 16
  not_honored: []
re_verification:
  previous_status: passed
  previous_score: "7/7 truths verified"
  gaps_closed: []
  gaps_remaining: []
  regressions: []
---

# Phase 4: MBC1 and Safe Battery Continuation Verification

**Phase Goal:** As a player, I want to resume supported MBC1 games from battery saves, so that failures preserve my last good progress.
**Verified:** 2026-10-10T16:07:17Z
**Status:** passed
**Re-verification:** Yes, freshness refresh. The prior report (2026-10-09T17:10:35Z, passed, 7/7, no gaps) had no unresolved gaps.

## Stale Cause (measured)

Phase 06.1 PR #54 (squash merge `ab76d09c2ee27ba09fc5f3c2510af016aebfdecb`, exact tested head `2a8fd1c357262d4b69707b553c603fd441a0f3fa`) changed two covered files, which invalidated the previous fingerprint:

- `src/player/session.c`: `read_rom_file` now opens with `O_NOCTTY` in addition to `O_NONBLOCK | O_NOFOLLOW | O_CLOEXEC`; the size-bound overrun and the `close()` failure are now separate branches. `read_save_file` is unchanged.
- `tests/player/test_session.c`: new `write_sized_file` helper and 2097153/2097154-byte replacement-failure assertions; the existing `mkfifo` assertions are unchanged.

The covered-file list is unchanged from the prior report; no new dependency was found.

## SAVE-03 Re-check After the Change

Inspected in `src/player/session.c`:

- ROM open: `open(path, O_RDONLY | O_CLOEXEC | O_NOFOLLOW | O_NONBLOCK | O_NOCTTY)` (line 107). A FIFO therefore cannot block the open.
- `fstat` followed by `S_ISREG` and a size bound of `PLAYER_SESSION_MAX_ROM_SIZE + 1` rejects non-regular and oversized files and closes the fd before returning an error (lines 113-117).
- The read loop is capped at the bound plus one byte. An overrun frees the buffer and returns an error (lines 143-146).
- The `close()` failure branch frees the buffer and returns an error (lines 149-152).
- The save-side reader (`read_save_file`, lines 323-362) is unchanged: it opens with `O_NONBLOCK | O_NOFOLLOW`, checks `S_ISREG`, bounds the size, and re-`fstat`s for stability.
- `tests/player/test_session.c` keeps the `mkfifo` replacement-failure assertion (line 151) and adds the 2 MiB+1 and 2 MiB+2 byte cases (lines 133, 138). Failures leave the selected path and machine RAM unchanged.

**Evidence limit:** the `read_rom_file` `close()`-failure branch is inspection-only evidence. There is no fault-injection stage for it, so it is not claimed as test-covered.

## User Flow Coverage

| Step | Expected | Evidence in codebase | Status |
|---|---|---|---|
| Open a supported MBC1 game | Declared standard MBC1 combinations load and select expected ROM/RAM banks; excluded variants return explicit errors. | src/core/gabbaboy.c validates the descriptor before replacing the active cartridge. Cartridge/loader matrix tests cover both banking modes and rejections. | VERIFIED |
| Make progress and save it | Guest RAM writes update instance-owned battery data; the player persists bounded data with identity and integrity checks. | Public battery API in include/gabbaboy/gabbaboy.h; mapper, battery, envelope, cadence, atomic-write tests. | VERIFIED |
| Reopen the same game | A fresh process imports the matching save before guest execution and reaches a path depending on earlier bytes. | tests/player/test_continuation.c; the extracted-package fresh-process continuation smoke passed this run. | VERIFIED |
| Recover safely from failures | A failed write keeps the last complete save, reports the failure, and blocks quit/reset/replacement until retry, continue-without-saving, or cancel. | src/player/session.c synced same-directory temporary plus rename; fault and transition tests; the player smoke passed "save retry, cancel, and continue choices". | VERIFIED |
| See the story outcome | Relaunch preserves progress; empty/wrong-save controls prove the oracle is meaningful. | Authored 32 KiB MBC1 fixture, distinct positive and negative controls, digest-bound manifest. | VERIFIED |

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---:|---|---|---|
| 1 | Declared standard MBC1 configurations behave as specified; excluded variants and other mappers return explicit errors. | VERIFIED | Core suite 184/184 passed in this run, including cartridge and loader matrix cases. |
| 2 | Bounded battery import/export under documented identity/size rules; malformed imports leave live state unchanged. | VERIFIED | Battery error/canary/fuzz tests are in the 184/184 core run; C/C++ consumer tests are in the core inventory. |
| 3 | Documented atomic replacement, recovery, and concurrent-writer rules; failed writes preserve the last good save and visibly report failure. | VERIFIED | session.c inspected above (open flags, fstat/S_ISREG/size bound, atomic write path); package player smoke passed retry/cancel/continue and lock-conflict preservation. Reported player CTest 51/51 from the verify script. |
| 4 | Original fixture saves, exits, reopens in a fresh process, and resumes dependent behavior; controls demonstrate a meaningful oracle. | VERIFIED | "packaged MBC1 continuation fixture resumed in a fresh process" in this run's package lane; test_continuation.c positive and negative controls. |
| 5 | ROM-only behavior and failed ROM replacement remain intact. | VERIFIED | Replacement-failure test covers unsupported headers, absent paths, FIFO, and the new oversize cases; path and RAM preserved. |
| 6 | Relocated C and C++ consumers compile and run the public battery API; required inventories fail closed. | VERIFIED | Consumers and expected-test inventories are in the 184/184 core run (`--no-tests=error`). Hosted jobs below. |
| 7 | Integrators can determine the support boundary, ownership, save rules, and evidence limits. | VERIFIED | docs/cartridge-and-saves.md and docs/mbc1-evidence.md are unchanged by the stale-causing PR. |

**Score:** 7/7 truths verified; all four roadmap success criteria are verified.

### Required Artifacts

| Artifact | Expected | Status | Details |
|---|---|---|---|
| include/gabbaboy/gabbaboy.h, src/core/gabbaboy.c | Public battery API and standard MBC1 | VERIFIED | Unchanged; exercised by the 184/184 run. |
| src/player/session.c, src/player/main.c | Bounded load, safe save, lock, status | VERIFIED | Re-inspected after the PR #54 change. |
| tests/test_cartridge.c, tests/test_loader.c, tests/test_battery.c | Mapper, rejection, transfer regressions | VERIFIED | Passed in the core run. |
| tests/player/test_session.c, tests/player/test_continuation.c | Save-failure, FIFO, oversize, fresh-process behavior | VERIFIED | Passed in the player package lane. |
| fixtures/mbc1-continuation/* | Original fixture and manifest | VERIFIED | Unchanged. |
| docs/cartridge-and-saves.md, docs/mbc1-evidence.md | Contract and qualifications | VERIFIED | Unchanged. |

### Key Link Verification

| From | To | Via | Status | Details |
|---|---|---|---|---|
| ROM header | Cartridge descriptor and bank state | Validate before replacement | WIRED | Unchanged. |
| Guest RAM | Battery transfer | Per-instance export/import | WIRED | Unchanged. |
| Battery API | Save envelope | Identity and CRC | WIRED | Unchanged. |
| Save state | Durable target | Same-directory temp, sync, rename | WIRED | Unchanged; `read_save_file` untouched. |
| Player session | Writer coordination | Advisory lock | WIRED | Lock conflict preserved the session in the package smoke. |
| Process A | Process B | Persisted bytes | WIRED | Fresh-process smoke passed. |
| Save outcome | Status and transition gating | Session result drives player | WIRED | Retry/cancel/continue smoke passed. |

### Data-Flow Trace (Level 4)

| Artifact | Data | Source | Produces real data | Status |
|---|---|---|---|---|
| MBC1 mapper | Selected ROM/RAM bytes | ROM bytes plus mapper writes | Yes | FLOWING |
| Battery API | Payload | Live cartridge RAM | Yes | FLOWING |
| Save envelope | Persisted payload | Export plus identity and CRC | Yes | FLOWING |
| Resume path | Guest state | Validated save imported before execution | Yes | FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|---|---|---|---|
| Core suite | `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error` | 100% passed, 184/184 (re-run by this verifier) | PASS |
| Player and extracted package | `bash tests/scripts/verify-phase3-player.sh --build-package` | Re-run by this verifier: dummy-audio smoke, packaged MBC1 continuation resumed in a fresh process, SDL smoke including lock conflict and save choices, SDL 3.4.18, package SHA-256 9e27b705ea913ce29fd8a5f5dd9158366cfaa0bc4da2e508f9890751f19136ee. Player CTest 51/51 is as reported by the script run; this verifier saw only its tail. | PASS |
| Hosted PR head | `gh run view 38064419789` | ci on head 2a8fd1c3: required-native, native-linux-x64, native-macos-arm64, native-windows-x64, linux-asan-ubsan, cmake-floor-3.25.3, player-gate, macos-player-package all success | PASS |
| Hosted main push | `gh run view 38064726000` | conclusion success; macos-player-package skipped by design on push (not counted as passing) | PASS |

Preview run 38064419803 (success) is cited from the handoff, not re-queried here. Code re-review (0 findings) and security (22/22 threats closed) are cited from 04-REVIEW.md and 04-SECURITY.md, which were refreshed by their own gates.

### Probe Execution

Not applicable: no probe-based criteria are declared.

### Requirements Coverage

| Requirement | Source Plans | Description | Status | Evidence |
|---|---|---|---|---|
| SAVE-01 | 04-01, 04-02, 04-07 | Standard MBC1 matrix; explicit rejection of excluded variants | SATISFIED | Cartridge and loader tests in the 184/184 run. |
| SAVE-02 | 04-01, 04-02, 04-06, 04-07 | Bounded battery import/export; non-mutation on malformed input | SATISFIED | Battery tests and consumers. |
| SAVE-03 | 04-01, 04-03, 04-04, 04-05, 04-06, 04-07 | Atomic persistence, recovery, writer policy, visible failed-save preservation | SATISFIED | Session tests; FIFO/oversize replacement-failure behavior re-inspected. |
| SAVE-04 | 04-05, 04-06, 04-07 | Fresh-process continuation with negative controls | SATISFIED | Package fresh-process smoke; continuation tests. |

All four IDs appear in PLAN `requirements:` frontmatter (04-01 through 04-07), in REQUIREMENTS.md (marked complete), and in the Phase 4 mapping. No orphaned requirements.

### Anti-Patterns Found

None. The files changed by PR #54 contain no TBD/FIXME/XXX/TODO markers (mkstemp `XXXXXX` templates are intentional). The code re-review reported 0 findings.

### Human Verification Required

None. No new human-only item exists. The limits below carry forward unchanged and are not reasons to add manual UAT.

### Evidence Limits (carried forward)

- No physical MBC1/DMG hardware result and no storage power-loss qualification is claimed.
- The writer lock guarantee holds only among cooperating processes.
- The `read_rom_file` `close()` failure branch is inspection-only, with no fault-injection test.
- The native SDL presentation audit (13/24, no screenshot) made no visual-polish claim, and none is made here.
- The macos-player-package job is skipped on main-push by design; package evidence comes from the PR-head run and the local package lane.
- Earlier hosted evidence (runs 37728192665/37728192634/37728192674 at 79f83f6; PR #43 runs at 9b9d58a) remains scoped to those revisions.

### Gaps Summary

No gaps. The only change since the prior pass is the PR #54 hardening of `read_rom_file` and its tests. It leaves the SAVE-03 FIFO and replacement-failure behavior intact and adds oversize-ROM rejection coverage.

---

_Verified: 2026-10-10T16:07:17Z_
_Verifier: the agent (gsd-verifier)_
