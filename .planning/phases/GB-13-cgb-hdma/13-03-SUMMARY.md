---
phase: 13-cgb-hdma
plan: "03"
subsystem: core-timing
tags: [cgb, hdma, halt, interrupts, timer, speed-switch, stop, oam-dma, ctest]

requires:
  - phase: "13-02"
    provides: "HDMA scheduler, register behavior and admitted-block progress"
provides:
  - "Public guest HALT wake and natural interrupt dispatch across HBlank DMA"
  - "Independent speed-pause and HDMA residuals with boundary-sampled wake"
  - "Selected STOP freeze and OAM/HDMA/PPU ordering policies with automated controls"
affects: [phase-13-remaining-plans, phase-14-model-qualification]

actuals:
  tokens: 12496
  tasks: 2
  commits: 4
commits: 4
plan_head_before: a6b115bc41fb6ec0d890ee20f9a36d5bcf6e2740
plan_head_after: 22a35bade8550d8978fa67f154313cc965e96874

tech-stack:
  added: []
  patterns:
    - "Bounded public-API guest programs assert guest-visible interrupt and DMA outcomes"
    - "Paired negative controls distinguish selected timing policies from matching final data"

key-files:
  created:
    - tests/test_cgb_hdma.c
  modified:
    - src/core/gabbaboy.c
    - tests/CMakeLists.txt
    - tests/expected-tests.txt
    - tests/test_cgb_hdma_internal.c
    - tests/external/cgb-speed-dispositions.json
    - docs/cgb-profile.md

key-decisions:
  - "HALT wake uses real timer IF/IE and normal IME interrupt dispatch; admitted DMA completes, and later HBlank admission waits for a new visible edge."
  - "During a speed-switch pause, DMA and the pause keep independent residuals; timer wake is sampled at the existing M-cycle boundary, with admitted DMA finishing before IRQ dispatch."
  - "STOP freezes DMA and device remainders until wake; shared-tick ordering is OAM DMA, HDMA, then PPU."
  - "These are selected software policies; physical CGB-E collision and speed-pause timing remain UNKNOWN."

task_commits:
  - task: 1
    stage: RED
    hash: 08f0aef867883977b1b4a12689062483e8f713ca
  - task: 1
    stage: GREEN
    hash: 8aee46acfdaaa30e0ccc08facc8b2a308678fc2b
  - task: 2
    stage: RED
    hash: ac135181e9e7387af4f3186b3a67492319c4b47d
  - task: 2
    stage: GREEN
    hash: 22a35bade8550d8978fa67f154313cc965e96874

requirements-completed: []

coverage:
  - id: D1
    description: "A public guest remains halted across an ineligible HBlank, wakes on a timer IRQ, dispatches naturally, and admits work only at a later genuine edge."
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest --test-dir build -R '^cgb_hdma_guest_(halt|controls|banks)$'"
        status: pass
  - id: D2
    description: "A public guest timing discriminator detects omitted CPU stealing while preserving identical final-data controls."
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest --test-dir build -R '^cgb_hdma_guest_steal(_no_steal_mutant|_no_steal_control)?$'"
        status: pass
  - id: D3
    description: "HDMA and both speed-pause directions advance independently, with boundary-sampled timer wake and DMA retirement before interrupt dispatch."
    human_judgment: false
    verification:
      - kind: unit
        ref: "ctest --test-dir build -R '^cgb_hdma_competing_stalls(_controls)?$'"
        status: pass
  - id: D4
    description: "STOP preserves pending DMA and device remainders without inventing a missed HBlank edge."
    human_judgment: false
    verification:
      - kind: unit
        ref: "ctest --test-dir build -R '^cgb_hdma_stop_policy(_controls)?$'"
        status: pass
  - id: D5
    description: "OAM sampling precedes same-tick HDMA commit, which precedes PPU HBlank publication."
    human_judgment: false
    verification:
      - kind: unit
        ref: "ctest --test-dir build -R '^cgb_hdma_oam_order(_controls)?$'"
        status: pass
  - id: D6
    description: "Model claims and inherited speed anchors retain automated provenance and negative controls."
    human_judgment: false
    verification:
      - kind: other
        ref: "cmake --preset phase1 && cmake --build --preset phase1 && ctest --test-dir build --output-on-failure --no-tests=error --parallel 4"
        status: pass
      - kind: other
        ref: "python3 -I tests/scripts/verify-speed-domains.py src/core/gabbaboy.c"
        status: pass
      - kind: other
        ref: "bash tests/scripts/verify-dmg-baseline.sh"
        status: pass

duration: 43min
completed: 2026-10-14
status: complete
---

# Phase 13 Plan 03: Real HALT Wake and Independent Competing Stalls Summary

**Public guest HALT/IRQ wake now composes with admitted HDMA, while speed pauses, STOP sleep, OAM DMA, and PPU ordering retain independent, tested policies.**

## Performance

- **Duration:** 43 minutes
- **Started:** 2026-10-14T19:57:49Z
- **Completed:** 2026-10-14T20:40:44Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments

- Added the public test_cgb_hdma target and bounded guest fixtures for HALT wake, timer interrupt dispatch, CPU stealing, bank selection, and matching-data controls.
- Preserved independent DMA and speed-pause residuals; wake obeys the persisted M-cycle boundary and cannot erase admitted work before dispatch.
- Added STOP and shared-tick OAM/HDMA/PPU ordering policies with paired controls and explicit physical-model qualifications.

## Task Commit Ledger

| Task | Stage | Commit | Purpose |
| --- | --- | --- | --- |
| 1 | RED | 08f0aef867883977b1b4a12689062483e8f713ca | Public HALT-wake guest fails on missing wake behavior |
| 1 | GREEN | 8aee46acfdaaa30e0ccc08facc8b2a308678fc2b | Guest tracer, target, controls, and profile contract |
| 2 | RED | ac135181e9e7387af4f3186b3a67492319c4b47d | Competing-stall and policy controls expose missing bounded progress |
| 2 | GREEN | 22a35bade8550d8978fa67f154313cc965e96874 | Independent stall progress, STOP/OAM policies, and qualifications |

**Plan metadata:** b7a6f63 (SUMMARY, STATE, ROADMAP, and continuation route).
**Route correction:** 452ef99 (Operator Next Steps aligned with Phase 13 wave 4).

## Files Created/Modified

- tests/test_cgb_hdma.c — bounded public-API guest emitter and guest-visible HALT, IRQ, steal, and bank checks.
- src/core/gabbaboy.c — independent speed and DMA progression with safe admission, output headroom, and M-boundary wake.
- tests/test_cgb_hdma_internal.c — timer, device, STOP, speed-direction, and OAM ordering controls.
- tests/CMakeLists.txt and tests/expected-tests.txt — explicit CTest registrations and negative-control inventory.
- docs/cgb-profile.md and tests/external/cgb-speed-dispositions.json — software policy, physical UNKNOWN boundary, and matching model-claim pin.

## Decisions Made

Selected guest-visible wake and arbitration behavior is documented above and in the CGB profile. The public header is unchanged. CGB-07 remains open until Phase 13’s final plan and phase-level verification.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical Functionality] Kept the external speed-disposition claim mirror aligned with the new policy test.**
- **Found during:** Task 2 verification
- **Issue:** The profile disposition table was updated to pin the new competing-stall test, but its machine-readable mirror still named the old post-switch-only test and described armed-across-pause coverage as absent.
- **Fix:** Updated the external disposition row, policy description, and flip rule to identify the selected software policy while preserving the physical CGB-E UNKNOWN boundary.
- **Files modified:** docs/cgb-profile.md, tests/external/cgb-speed-dispositions.json
- **Verification:** The exact task gate, disposition mutation controls, and full CTest suite pass.
- **Committed in:** 22a35ba

**Total deviations:** 1 auto-fixed (Rule 2)
**Impact on plan:** The synchronized claim and test pin are necessary for the documented model boundary; scope and public API remain unchanged.

## TDD Gate Compliance

- Task 1 RED commit 08f0aef867883977b1b4a12689062483e8f713ca produced a semantic guest failure at HALT wake status. The later GREEN commit 8aee46acfdaaa30e0ccc08facc8b2a308678fc2b passed the guest, mutant, control, tracer, and model-gate suite.
- Task 2 RED commit ac135181e9e7387af4f3186b3a67492319c4b47d was accepted only after the evidence classifier returned RED_EVIDENCE_OK for the semantic one-half-dot progress failure. The GREEN commit 22a35bade8550d8978fa67f154313cc965e96874 passed all task and full-suite checks.
- Harness or build-discovery failures were not accepted as RED evidence.

## Verification

- Task 1 exact plan gate: required names present; 27/27 public guest, tracer, HALT/interrupt, and model-gate tests passed.
- Task 2 exact plan gate: six required task test names present; 45/45 task, guest, tracer, inherited Phase 12 mutant/control, and model-gate tests passed.
- Full regression: 928/928 CTests passed in 103.48 seconds using four workers.
- Speed-domain check: python3 -I tests/scripts/verify-speed-domains.py src/core/gabbaboy.c passed with 39 functions checked.
- Frozen DMG baseline: inventory 313, Mooneye 15, acceptance 20, benchmark 2, changed rows 0; passed.
- Plan commit ledger: four task commits from a6b115bc41fb6ec0d890ee20f9a36d5bcf6e2740 through 22a35bade8550d8978fa67f154313cc965e96874.

## Issues Encountered

The first full-suite run exposed one stale machine-readable disposition pin (927/928). Updating the matching claim mirror resolved the mismatch; a fresh full run passed 928/928.

## Known Stubs

None found in files created or modified by this plan. The planned public fixture reader is bounded and connected to the guest tests.

## Next Phase Readiness

Phase 13 plan 13-03 execution is complete; Phase 13 remains active. Wave 4 contains plans 13-04 and 13-08. Continue with /gsd-execute-phase 13 after reusing the 13-01, 13-02, 13-03, and 13-06 summaries. CGB-07 remains open until Phase 13 closeout; Phase 14 remains unstarted.

---
*Phase: 13-cgb-hdma*
*Completed: 2026-10-14*

## Self-Check: PASSED

- Summary file exists.
- All four task commits are ancestors of the current HEAD.
- The strict summary coverage checker accepts all six entries.
