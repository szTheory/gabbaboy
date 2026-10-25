---
phase: 07-dmg-game-acceptance-and-regression-baseline
plan: 17
subsystem: input
tags: [joypad, libbet, d-19, intro-timing, investigation]

requires:
  - phase: 07-03
    provides: D-19(i) outcome (D-027) and the sibling investigation recording style
provides:
  - D-19(ii) outcome - early repeated Start taps are expected guest behaviour, no emulator defect (D-028)
  - GB-GAME-002 lesson with probe evidence
affects: [07-07, 07-10, 07-15]

status: complete
actuals:
  tokens: 2500
  tasks: 2
  commits: 1
plan_head_before: bf210883c2f69721e118fbdda185b810847db735
plan_head_after: f2443b5

tech-stack:
  added: []
  patterns:
    - "Separate 'game ignored input' from 'emulator dropped input' by logging guest-side new_keys edges per frame"

key-files:
  created: []
  modified:
    - .planning/context/DECISIONS.md
    - .planning/context/LESSONS.md

key-decisions:
  - "D-19(ii) is expected behaviour: intro unskippable window plus skippable window plus a second Start at the title explain every observation; joypad path unchanged (D-028)"

requirements-completed: [GAME-02]

coverage:
  - id: D1
    description: "Early repeated Start taps explained from pinned Libbet intro.z80/pads.z80 with a scratch replay; decision recorded with evidence"
    requirement: GAME-02
    verification:
      - kind: other
        ref: "scratch probe over libbet.gb (not committed); results in DECISIONS.md D-028 and LESSONS.md GB-GAME-002"
        status: pass
      - kind: integration
        ref: "ctest --test-dir build (201/201 pass); git diff --quiet src/core/gabbaboy.c; anchor count 1 in src and main"
        status: pass
    human_judgment: false

duration: 25min
completed: 2026-10-10
---

# Phase 7 Plan 17: Early Start taps investigation (D-19(ii)) Summary

**Early repeated Start taps are expected Libbet behaviour (120-frame unskippable window, then a skippable window, then a second Start at the title); the core reports every press exactly once as read_pad would see it, so the joypad path is unchanged and recorded as D-028.**

## Performance

- **Duration:** about 25 min
- **Tasks:** 2 (Task 1 investigation only, no tracked change; Task 2 one docs commit)
- **Files modified:** 2

## Accomplishments

- Source (pinned `pinobatch/libbet` commit `46a765a2c01701bffb8c0b7dd6e4be3a6b193090`, fetched as a tarball into scratch and only read): `src/intro.z80` roll loop (lines 237-305) never calls `read_pad` and runs until `cursor_x` reaches 192 (+3 per frame, 64 frames); `.vtimeout` (lines 307-322, `ld bc, 180*256+120`) calls `read_pad` each frame, ignores `new_keys` for 120 passes, then tests `new_keys & (PADF_START|PADF_A)` for up to 180 passes. `src/pads.z80` `read_pad` (lines 61-95) polls buttons then d-pad via `rP1`, discards two reads, and derives `new_keys = (cur ^ b) & b`. The title (`src/instructions.z80` lines 131-137) polls once per frame.
- Scratch probe (copy of the core with a write log on `new_keys` at `$C5A2`, address taken from the ROM's `read_pad` bytes; ROM sha256 `3607412031c8287cf878299ce96e581e85b852dde703806343b95576fa3ff1a9`):
  - No input: roll loop f50-f113, unskippable window to f233, intro ends f440, title f447 (matches the D-13 "ready near f444" fact).
  - Repeated START taps every 10f from f100 (3f holds): taps f100-f230 ignored; f240 tap skips the intro (LCD off f270, title f277); f280 tap starts the game (play state f287, `lcdc=$E3`). State change (play) at f287.
  - Single START taps, run separately: f290 -> title f327, no game; f350 -> title f387, no game; f440 -> no effect, title f447, no game; f470 -> game f478. Game start from a single tap: none before f470.
  - Every tap gave exactly one `new_keys=$08` edge in the press frame (PC `$00E2`, inside `read_pad`), with `cur_keys` clear 3 frames later: no held-across-vblank or select-line timing deviation.
- Decision (D-19(ii)): expected, no defect. The research claim that single taps at f290-f440 "do nothing" is explained: they skip the intro and stop at the title; none was followed by a second Start.
- Recorded as D-028 (DECISIONS.md) and GB-GAME-002 (LESSONS.md). No source or test change. Core-mutant anchor `if ((m->joypad_select & 0x20u) == 0)` occurs once in `src/core/gabbaboy.c` and once in `main:src/core/gabbaboy.c`; `tests/expected-tests.txt` unchanged.

## Task Commits

1. **Task 1: explain early taps from pinned source with scratch replay** - no commit (plan states no tracked change; results live in this summary, D-028 and GB-GAME-002)
2. **Task 2: record outcome (no defect, no source change)** - `f2443b5` (docs)

## Decisions Made

- D-028: joypad path unchanged; acceptance scripts tap Start only once the title is up (D-13 uses f500, after f449) or send two taps for an early path.

## Deviations from Plan

None - plan executed exactly as written. The plan's "fix only a demonstrated defect" branch was not taken, so no `tests/test_joypad.c` assertion was added.

## Issues Encountered

- The existing scratch Libbet directory held a different tree (not the pinned source), so the pinned tarball was fetched into a fresh scratch directory (sha256 of tarball `331774dcfa439bba893f88ea5f11e9eb02f8ea30a6094cc73f97e14ea7ed0b54`) and only read; nothing in it was executed or built.
- The probe is single-window per tap and depends on the in-scratch core copy; no regression test could fail pre-fix because there is no fix.

## Verification Run

- After Task 1: `cmake --build --preset phase1 && ctest --test-dir build -R 'joypad|events|tracer' --no-tests=error` 16/16 pass; `git diff --quiet -- src/core/gabbaboy.c` clean.
- After Task 2: full `ctest --test-dir build --no-tests=error` 201/201 pass; `grep -c 'D-19(ii)' DECISIONS.md` = 1; DECISIONS row cites `intro.z80` and `pads.z80` at the pinned commit; anchor count 1 in both revisions; `git diff --quiet tests/expected-tests.txt` clean.

## Known Stubs

None.

## Threat Flags

None.

## Next Phase Readiness

D-19 pre-freeze investigations (i) and (ii) are both closed; digest blessing in Plan 07-07 onward and the Plan 07-10 core mutant (anchor unchanged) are unblocked by this plan.

## Self-Check: PASSED

- Commit f2443b5 is an ancestor of HEAD; DECISIONS.md and LESSONS.md contain D-028 and GB-GAME-002.
