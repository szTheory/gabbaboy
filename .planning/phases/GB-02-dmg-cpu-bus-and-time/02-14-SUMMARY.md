---
phase: GB-02-dmg-cpu-bus-and-time
plan: 14
subsystem: testing
tags: [mooneye, cpu, timer, provenance, applicability]
requires:
  - phase: GB-02
    provides: Pinned three-case Mooneye source and builder recipe from Plan 02-13
provides:
  - Audited PPU-independent derived CPU/timer reporting candidate
  - Pinned harness patch and automated positive/negative protocol probe
affects: [GB-02-15, CPU-01, CPU-03, CPU-05]
tech-stack:
  added: []
  patterns: [source-qualified derived oracle, private ROM negative control]
key-files:
  created: [fixtures/mooneye/ELIGIBILITY.md, fixtures/mooneye/headless-report.patch, tests/scripts/probe-mooneye-candidate.sh]
  modified: [tests/scripts/reproduce-mooneye.sh]
key-decisions:
  - Keep all three checked-in ROMs ineligible as built because quit reads LY before callback.
  - Preserve acceptance sources and result registers; redirect only harness printing to WRAM and remove PPU helpers.
  - Defer manifest admission and CPU-05 completion pending final suite and cross-host evidence.
requirements-completed: []
actuals:
  tokens: 5261
  tasks: 2
  commits: 2
commits: 2
plan_head_before: fa3a2d55ec236e85a49e3a37925af896877964d7
plan_head_after: 5a2da504bd1ef307b465e067d639eb828e86dacd
duration: 8min
completed: 2026-10-06
status: complete
---

# Phase GB-02 Plan 14: Mooneye Candidate Qualification Summary

**A pinned harness-only derivative reaches the original DAA/timer callbacks and register verdict without PPU bus access; no fixture has been admitted.**

## Accomplishments

- Audited Mooneye commit `31510e12eea6286d36eea060a6adde755e1067aa`, tree `2b8c52424a49a2a7466cf631fd8992c53d0de2fa`, for all three acceptance roots and their common include closure. Each root declares DMG pass and has a CPU/timer assertion independent of boot ROM and PPU behavior. The existing ROMs are ineligible as built: original `quit` calls `is_ppu_broken`, reading LY `FF44`, before the callback.
- Created `headless-report.patch` (SHA-256 `c3679ab53b59da14a0f6af1fdd552316ba922762c3a91988f7f8ac4440516e5d`). It changes only MIT-covered `common/common.s` and `common/lib/quit.s`: drops seven PPU-only includes and the unused font section, bypasses PPU setup and LY waits, points printing at WRAM `$c000`, and leaves the callback, its D verdict, six register assignments and actual `LD B,B` breakpoint intact. The upstream acceptance sources and assertion constants remain byte-for-byte unchanged. The separately licensed zero font is still pin-verified during preparation but is absent from derived ROMs.
- Extended explicit networked reproduction with `--candidate`, immutable source/tool checks and patch digest recording. The public-core `gbb_run_ex` probe checks callback PCs from linker symbols, the real breakpoint opcode/PC, independent expected registers and diagnostic bus accesses. It mutates only one DAA expected-table byte in a private ROM copy to induce the original failure path.

## Verification

`bash tests/scripts/probe-mooneye-candidate.sh` passed on local Darwin/arm64. The pinned source/tool revisions, trees, WLA-DX archive, WLA tool versions and unchanged acceptance-source digests passed. Candidate ROM SHA-256 values: DAA `0577cd81220ab6afeb5d2fde5d267729df4bd7188a1f0cdc960eb613e3a261fb`; TIM00 `ecf9a3f90c44dcc348bbbf7d50994eb8ef4dfb9b084a0b950e6fcbfd7da66dcb`; TIM00 DIV trigger `9485b29362f72f64f0715acfd4211b08cd2bc9b07a5de6531d4fecebfe32d7a4`.

| Probe | Callback | Real breakpoint | Expected six registers | PPU accesses | Half-dots |
|---|---:|---:|---|---:|---:|
| DAA pass | yes | yes | `03 05 08 0d 15 22` | 0 | 1,807,304 |
| TIM00 pass | yes | yes | `03 05 08 0d 15 22` | 0 | 37,776 |
| TIM00 DIV trigger pass | yes | yes | `03 05 08 0d 15 22` | 0 | 35,648 |
| DAA induced fail | yes | yes | `42 42 42 42 42 42` | 0 | 19,968 |

`bash -n` for both scripts, `git diff --check`, and the Task 1 audit verification passed. No hosted Linux candidate run was performed in this plan. The pre-existing WLA-DX cross-host linker ordering issue remains open; candidate bytes are local evidence only. No `manifest.json`, checked-in ROM, denominator, or requirement completion changed. T-02-25, CR-05 and T-02-15 remain open through final admitted-suite evidence.

## Task Commits

1. `9d4c687` — Task 1, immutable source closure and eligibility audit.
2. `5a2da50` — Task 2, pinned patch, candidate mode and positive/negative probe.

## Deviations from Plan

None. The probe deliberately mutates a temporary ROM table byte for a failure control, without editing upstream acceptance source or the tracked patch.

## Rights and scope

The Mooneye MIT notice is retained in `fixtures/mooneye/LICENSE.txt` and in patched source headers. WLA-DX GPL-2.0-or-later applies to the separate build tool. Font replacement rights are recorded in `FONT-LICENSE.txt`; the derived closure omits the font section. No restricted ROM or unlicensed font bytes were added.

## Self-Check: PASSED

All four plan files and this summary exist; task commits `9d4c687` and `5a2da50` are ancestors of HEAD; the measured task commit count is two; `git diff --check` passed.
