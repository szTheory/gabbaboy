---
phase: 13-cgb-hdma
plan: "01"
subsystem: core
tags: [CGB, HDMA, HBlank, timing-policy]
requires:
  - phase: 12-cgb-double-speed
    provides: Double-speed run-loop timing and bounded run accounting
provides:
  - One bounded, policy-qualified CGB HBlank DMA block on an ordinary visible mode-3-to-0 edge
  - Guest-visible FF51-FF55 latches, masks, and active/completed readback for the implemented path
  - Automated seam, mode, output, disposition, model-gate, and frozen DMG regression coverage
affects: [13-02, CGB HDMA, CGB model claims]
actuals:
  tokens: 14584
  tasks: 2
  commits: 3
plan_head_before: a52bd84014e1bafb6e84f5b4d7d9910d9a33d16d
plan_head_after: aab4a865c325f21a86f0b989ee527eb202ce7e00
tech-stack:
  added: []
  patterns:
    - Persisted one-half-dot service state with preflight checks before each mutation
    - Model-tagged CGB-only behavior mirrored by profile and gate contracts
key-files:
  created:
    - tests/test_cgb_hdma_internal.c
  modified:
    - src/core/gabbaboy.c
    - tests/CMakeLists.txt
    - tests/expected-tests.txt
    - docs/cgb-profile.md
    - tests/test_cgb_visibility.c
    - docs/model-gates.md
    - tests/test_cgb_speed_internal.c
    - tests/external/cgb-speed-dispositions.json
key-decisions:
  - "Treat the post-instruction service boundary, four-half-dot byte cadence, and 64-half-dot block as software policy; no physical CGB-E timing claim is made."
  - "FF51-FF54 CPU reads remain FF under policy while writes apply the documented source and destination masks."
requirements-completed: []
coverage:
  - id: D1
    description: Both late instruction seams complete before a bounded 16-byte HBlank transfer at normal and double speed.
    human_judgment: false
    verification:
      - kind: integration
        ref: ctest:cgb_hdma_tracer_ld_sp,cgb_hdma_tracer_cb
        status: pass
      - kind: integration
        ref: ctest:cgb_hdma_tracer_partition,cgb_hdma_tracer_outputs
        status: pass
  - id: D2
    description: CGB guest-visible FF51-FF55 reads, masks, active/completed status, and DMG/compatibility distinctions are checked through guest execution.
    human_judgment: false
    verification:
      - kind: integration
        ref: ctest:cgb_hdma_visibility
        status: pass
      - kind: integration
        ref: ctest:cgb_hdma_visibility_controls
        status: pass
      - kind: integration
        ref: ctest:cgb_visibility_matrix_cgb,cgb_visibility_matrix_dmg,cgb_visibility_matrix_compat
        status: pass
  - id: D3
    description: CGB support and timing claims match the executable model-gate, I/O-table, speed-disposition, and frozen DMG contracts.
    human_judgment: false
    verification:
      - kind: other
        ref: ctest:model_gates,cgb_tables_io,cgb_speed_dispositions
        status: pass
      - kind: other
        ref: bash tests/scripts/verify-dmg-baseline.sh
        status: pass
duration: 26m
completed: 2026-10-14
status: complete
---

# Phase 13 Plan 01: CGB HDMA Summary

**A policy-qualified HBlank HDMA path transfers one 16-byte block after the retiring instruction and passes guest-visible mask and model-mode checks.**

## Performance

- **Duration:** 26 minutes.
- **Started:** 2026-10-14T18:16:19.973Z (Phase 13 execution start recorded in STATE.md).
- **Completed:** 2026-10-14T18:42:51Z.
- **Tasks:** 2
- **Files modified:** 9 plan-owned files.

## Accomplishments

- Added a private real-run tracer for `LD (a16),SP` and `CB RLC(HL)` seams at normal and double speed. Each transfers 16 distinct bytes with per-call budget and time conservation, no-edge/unarmed controls, split-run equivalence, and trace/audio/diagnostic boundary checks.
- Implemented one ordinary visible HBlank block using private FF51-FF55 latches, masked source/destination programming, admission-time VBK sampling, and one-half-dot persisted service steps with preflight checks.
- Added guest-visible CGB mask/status tests and explicit controls for source/destination mask errors, exposed cursors, and wrong-mode expectations; updated profile, model-gate, and speed-disposition mirrors.

## Task Commits

1. **Task 1: RED:** `e9e3f77` — `test(13-01): add failing CGB HDMA seam tracer`
2. **Task 2: RED:** `e0ecbd6` — `test(13-01): cover CGB HDMA register masks and modes`
3. **Task 1: Shared GREEN implementation (also Task 2):** `aab4a86` — `feat(13-01): implement bounded CGB HBlank HDMA tracer`

The plan ledger measured 3 task commits from `a52bd84014e1bafb6e84f5b4d7d9910d9a33d16d` through `aab4a865c325f21a86f0b989ee527eb202ce7e00`.

## TDD Gate Compliance

- Task 1 RED target `cgb_hdma_tracer_ld_sp` failed on the expected pre-implementation FF55 unsupported stop. The fresh CTest JUnit report passed `check tdd-red-evidence` with `RED_EVIDENCE_OK`; the semantic review found no build, fixture, discovery, or report error.
- Task 2 RED target `cgb_hdma_visibility` was run against a temporary archive of the branch baseline with the new guest test and inventory entries. It failed at the expected baseline FF55 unsupported stop (`reason=4`). Its fresh JUnit report passed the classifier with `RED_EVIDENCE_OK`. The same tests passed against the in-progress implementation before GREEN was committed.
- The shared GREEN commit implemented the transfer and register path used by both tasks. No additional refactor was needed.

## Verification Evidence

- Task 1 required-name guard found all 13 exact names. The complete Task 1 command passed **45/45** selected CTests, including all five `cgb_hdma_tracer_*` cases, visibility and model-gate regressions, the FF54 negative twin, CGB/DMG identity checks, and speed dispositions.
- Task 1's `bash tests/scripts/verify-dmg-baseline.sh` passed: inventory 313 keys, Mooneye 15, acceptance 20, benchmark 2, changes 0.
- Task 2's required-name guard found `cgb_hdma_visibility` and `cgb_hdma_visibility_controls`. Those two tests plus the five seam tracer cases passed **7/7**.
- The complete Task 2 verification command passed **37/37** selected CTests, including `summary_coverage`, and the frozen DMG baseline passed again.
- The Task 2 negative controls reject leaked FF51 cursor values, a missing FF52 source mask, missing FF54 destination-low mask, unmasked FF53 page bits, and CGB/compatibility expectation swaps.
- `docs/model-gates.md`, `docs/cgb-profile.md`, the CGB I/O table, and `tests/external/cgb-speed-dispositions.json` remained synchronized under their automated checks.
- `include/gabbaboy/gabbaboy.h` is unchanged. No physical CGB-E evidence was collected or inferred.

## Decisions Made

- The only implemented trigger in this plan is an ordinary visible-line mode-3-to-mode-0 transition. The pending transfer is serviced after the retiring instruction and before interrupt dispatch or another opcode.
- This software policy advances one master half-dot per DMA service tick and commits bytes at elapsed 4, 8, …, 64 half-dots, with no extra startup or teardown. Those timing choices remain unqualified on physical hardware.
- FF51-FF54 CPU reads return `$FF` as policy. FF52/FF54 low nibbles and FF53 high bits are masked on writes; FF55 exposes the active/completed values exercised by the tests.

## Deviations from Plan

No code scope deviation. Task 2's failing guest-visible test commit was recorded before the shared implementation commit because both tasks use the same core register path and the runtime TDD gate requires RED before the first `feat(13-01)` commit.

## Issues Encountered

The baseline I/O table test accepts only existing I/O policy kinds. The new latches were therefore connected through the existing masked `IO_STORE` abstraction, preserving the plan's nine-file scope and keeping `cgb_tables_io` passing.

## Next Phase Readiness

Plan 13-01 is complete. Phase 13 remains active: this plan does not implement general-purpose DMA, cancellation/restart semantics, LCD-off or VBlank transfers, or HALT interaction, so requirement CGB-07 remains open. The next Phase 13 plan retains responsibility for its remaining behavior.

## Self-Check: PASSED

The summary, core, and tracer test files exist. Commits `e9e3f77`, `e0ecbd6`, and `aab4a86` are ancestors of the current HEAD.

---
*Phase: 13-cgb-hdma*
*Completed: 2026-10-14*
