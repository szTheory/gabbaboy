---
phase: 13-cgb-hdma
plan: "09"
subsystem: testing
tags: [cgb-hdma, samesuite, magentests, cgb-e, cgb-c, provenance, ctest]
requires:
  - phase: Phase 13 plans 13-05 through 13-08
    provides: runtime mutation controls, pinned fixture admission, public HDMA guest oracle, Magen differential fixture
provides:
  - Four executed SameSuite CGB-E software-model HDMA dispositions with guest, register, and VRAM predicates
  - Magen hblank_vram_dma differential disposition with named no-transfer, wrong-bank, and wrong-HALT controls
  - Closed-model disposition verifier that rejects result, provenance, denominator, and hardware-claim mutations
affects: [Phase 13 plan 13-10, CGB HDMA evidence, CGB-07]
actuals:
  tokens: 16050
  tasks: 2
  commits: 4
commits: 4
plan_head_before: e37f5b38ec7db0bcc58b24b0b597d61b0a4b3a57
plan_head_after: 12a5a63eb1f4884eb742c12c20b66018c4e968ae
tech-stack:
  added: []
  patterns: [source-derived guest predicates, mutation-tested evidence ledger, bounded CGB fixture execution]
key-files:
  created:
    - tests/test_samesuite_hdma.c
    - tests/external/cgb-hdma-dispositions.json
    - tests/scripts/verify-cgb-hdma-dispositions.py
    - .planning/phases/GB-13-cgb-hdma/13-09-RED-evidence.json
    - .planning/phases/GB-13-cgb-hdma/13-09-TASK2-RED-evidence.json
  modified:
    - tests/CMakeLists.txt
    - tests/expected-tests.txt
    - docs/cgb-profile.md
    - .planning/research/INDEX.md
key-decisions:
  - "Preserve D-06's selected software-model sequence and the Pan Docs discrepancy; physical CGB-E behavior remains UNKNOWN/POLICY."
  - "Keep optional Mealybug CGB-C rows not-run:rights-gate-G1 and outside the CGB-E denominator."
patterns-established:
  - "A fixture disposition records guest results, data/readback, register outcomes, source pins, model, and exact test binding rather than relying on a digest alone."
  - "Metadata controls reject CGB-C hardware claims and denominator inflation."
requirements-completed: []
coverage:
  - id: D1
    description: "Four unmodified, pinned SameSuite ROMs execute to their guest pass result and source-derived HDMA data and register predicates."
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest --test-dir build -R '^(samesuite_hdma_gbc_dma_cont|samesuite_hdma_gdma_addr_mask|samesuite_hdma_hdma_lcd_off|samesuite_hdma_hdma_mode0)$' --output-on-failure --no-tests=error"
        status: pass
      - kind: integration
        ref: "ctest --test-dir build --output-on-failure --parallel 4"
        status: pass
  - id: D2
    description: "The no-copy and corrupted-result twins fail the guest predicate, while Magen's no-transfer, wrong-bank, and wrong-HALT controls reject their named defects."
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest --test-dir build -R '^(samesuite_hdma_|magentests_hblank_vram_dma$|cgb_hdma_(magen_controls|dispositions|original_fixture)|cgb_speed_dispositions|model_gates)' --output-on-failure --no-tests=error"
        status: pass
  - id: D3
    description: "The provenance ledger, model labels, result observations, denominator, Phase 12 boundary, and CGB-C hardware-claim boundary are enforced with mutation controls."
    human_judgment: false
    verification:
      - kind: unit
        ref: "python3 -I tests/scripts/verify-cgb-hdma-dispositions.py --self-test"
        status: pass
      - kind: other
        ref: "python3 -I tests/scripts/verify-cgb-hdma-dispositions.py --complete"
        status: pass
  - id: D4
    description: "The research index navigates to current admission and result evidence while recording the G1 gate and partial Phase 13 execution."
    human_judgment: false
    verification:
      - kind: other
        ref: "python3 -I -c 'from pathlib import Path; text=Path(\".planning/research/INDEX.md\").read_text(); section=text.split(\"<!-- phase13-evidence-begin -->\",1)[1].split(\"<!-- phase13-evidence-end -->\",1)[0]; required=[\"tests/external/cgb-hdma-dispositions.json\",\"fixtures/samesuite/ELIGIBILITY.md\",\"fixtures/magentests/ELIGIBILITY.md\",\"not-run:rights-gate-G1\",\"CGB-C informational\",\"execution partial\"]; valid=lambda value: all(token in value for token in required); assert valid(section), \"phase13-memory-contract\"; assert all(not valid(section.replace(token,\"\")) for token in required), \"phase13-memory-negative-control\"'"
        status: pass
  - id: D5
    description: "The frozen DMG behavior and the previous CGB HDMA, visibility, model, and speed controls remain green."
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest --test-dir build -R '^(cgb_hdma_|cgb_visibility_|model_gates|cgb_speed_)' --output-on-failure --no-tests=error --parallel 4"
        status: pass
      - kind: other
        ref: "bash tests/scripts/verify-dmg-baseline.sh"
        status: pass
metrics:
  duration: "about 30 minutes; exact plan start was not captured"
  completed: "2026-10-14"
duration: "about 30 minutes; exact plan start was not captured"
completed: "2026-10-14"
status: complete
---

# Phase 13 Plan 09: Executed SameSuite Dispositions and Optional CGB-C Boundary Summary

**All four admitted SameSuite HDMA ROMs now pass guest-level data and register checks; Magen remains differential evidence, while optional CGB-C stays outside the denominator.**

## Performance

- **Duration:** About 30 minutes; exact plan start was not captured. The first captured Task 1 RED run began at 2026-10-14T22:40:50Z.
- **Completed:** 2026-10-14T22:59Z.
- **Tasks:** 2.
- **Files changed by the plan:** 9.

## Accomplishments

- Executed the four unmodified SameSuite ROMs at revision `f15645fb049a47ea235f6d2c9a033e72d8087901`. Each reaches its author-encoded `P` result and Fibonacci sentinel. The harness checks VRAM bytes, FF55 outcomes, effective addresses, and continuation cursors.
- Recorded the CGB-E selected software-model denominator as 5/5: four SameSuite cases plus Magen `hblank_vram_dma`. Magen's exact 1,024-byte map, FF55 busy/completion, 64-block HALT behavior, green RGB555 viewport, stable frame generations, and structural digest precede its pass.
- Kept Mealybug `hdma_timing-C` and `hdma_during_halt-C` at `not-run:rights-gate-G1`. Both CGB-C rows remain informational and outside the CGB-E denominator. No owner-authorized local Mealybug ROM was present in the repository inventory.
- Extended the closed-model verifier to bind exact observed results, enforce the CGB-C evidence boundary, and reject source, hash, denominator, result, data, control, and Phase 12 boundary mutations. The self-test passes 16 mutations.
- Updated the CGB profile mirror and the bounded Phase 13 section in the research index. The D-06/Pan Docs conflict and the physical CGB-E UNKNOWN/POLICY limit remain explicit.

## Task Commits

1. **Task 1: RED:** `4c075f4` — `test(13-09): add SameSuite DMA tracer oracle`
2. **Task 1: GREEN:** `293621b` — `feat(13-09): verify CGB HDMA tracer disposition`
3. **Task 2: RED:** `4164c64` — `test(13-09): reject CGB-C hardware evidence claims`
4. **Task 2: GREEN:** `12a5a63` — `feat(13-09): execute all CGB HDMA disposition cases`

Task 1's no-copy control fails at the guest pass sentinel and its corrupted-result twin fails at the first changed VRAM byte. Task 2's self-test initially accepted a mutated CGB-C `hardware-backed CGB-E measurement` claim; the targeted CTest failed for that named semantic reason. Both RED records were classified `RED_EVIDENCE_OK` before their GREEN commits. Task 2's GREEN verifier now rejects that claim and the other 15 named metadata/result mutations.

## Verification Results

- SameSuite outcomes: `gbc_dma_cont` copied 32 bytes across two GDMA starts and ended at C020/8820; `gdma_addr_mask` checked its initial 16-byte block and 16-byte untouched region, then verified all four blocks through C040/8840; `hdma_lcd_off` and `hdma_mode0` each checked `$83 -> $02 -> $00 -> $80`, one block, the final `$80` status, and their author-encoded data. Each case passed its exact CTest.
- Magen passed with digest `7a137aaa9e15d61c56d78c0c02b507099f29b1ab7bff6cadd5df6980c0c510e0` and generations 16/17. Its no-transfer, wrong-bank, and wrong-HALT controls each reported the intended diagnosis.
- The exact expanded CGB evidence group passed 26/26. The combined CGB HDMA, visibility, model, and speed regression filter passed 257/257.
- Fresh full CTest passed 984/984 with `--parallel 4` in 66.09 seconds. The frozen DMG baseline passed with 313 inventory keys, 15 Mooneye keys, 20 acceptance keys, 2 benchmark keys, and zero changed rows.
- The required-test-name guard found every required target. The research-index marker contract passed and each required-token deletion was rejected.

## TDD Gate Compliance

- Task 1 RED was the named `samesuite_hdma_gbc_dma_cont_control` no-copy mutant, rejected at the source-derived guest pass predicate. Task 1 GREEN delivered the original guest oracle, its negative twins, and provenance-bound pending metadata for the remaining corpus.
- Task 2 RED was `cgb_hdma_dispositions_selftest`, which executed the hardware-claim mutation and failed because the old validator accepted it. Task 2 GREEN added the precise CGB-C evidence-class check, per-case SameSuite execution checks, Magen map/control observations, and the complete-mode CTest registration.
- The `gdma_addr_mask` predicate was corrected after its unmodified ROM showed an initial one-block snapshot followed by three visible-HBlank blocks when the LCD was re-enabled. The final assertion now verifies both temporal observations and all four blocks. The Mode 0 runner also treats `GBB_STOP_HALTED_IDLE` as resumable progress until the guest sentinel; neither observation changes the ROM's expected result.

## Files Created and Modified

- Created `tests/test_samesuite_hdma.c`, the disposition JSON and verifier, and both persisted RED evidence records.
- Modified CTest registration and inventory, the CGB profile disposition mirror, and the research index's Phase 13 evidence section.

## Decisions Made

The plan preserves existing D-06/D-16/D-17/D-18 policy: successful software-model and differential executions do not establish physical CGB-E behavior; the cancellation disagreement with Pan Docs remains unresolved; optional CGB-C evidence remains rights-gated and outside the CGB-E denominator. CGB-07 stays open for later Phase 13 closure work.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Accept resumable HALTED_IDLE progress in the SameSuite runner.**
- **Found during:** Task 2.
- **Issue:** `hdma_mode0` returned the public API's normal resumable `GBB_STOP_HALTED_IDLE` reason, which the runner treated as a fatal stop before the ROM reached its pass sentinel.
- **Fix:** Continue bounded slices for this stop reason and retain the existing budget and sentinel checks.
- **Files modified:** `tests/test_samesuite_hdma.c`.
- **Verification:** Exact four-case CTest and fresh 984-test full suite passed.
- **Committed in:** `12a5a63`.

**2. [Rule 1 - Bug] Match `gdma_addr_mask`'s initial transfer and later visible-HBlank continuation.**
- **Found during:** Task 2.
- **Issue:** An initial harness predicate treated the first block as the final transfer. The unmodified ROM re-enables LCD and drains the remaining three blocks on visible HBlanks; repeated snapshot capture also obscured the first-block state.
- **Fix:** Capture the first FF55 start once, assert the 16 copied bytes and 16 untouched bytes at that point, then assert the full 64-byte final result and C040/8840 cursors.
- **Files modified:** `tests/test_samesuite_hdma.c`.
- **Verification:** The exact ROM test passed and the disposition verifier binds its initial snapshot, final data count, FF55 result, cursor, and elapsed half-dots.
- **Committed in:** `12a5a63`.

**Total deviations:** 2 auto-fixed harness issues. No core behavior, upstream ROM expectation, rights boundary, or hardware qualification was changed.

## User Setup Required

None. No new package, emulator, CI job, or external service was introduced.

## Next Phase Readiness

Phase 13 remains active with 9/12 plans complete. Next is **Phase 13 Wave 8, Plan 13-10: Installed C/C++ DMA consumers and closed package contents**. Continue with `/gsd-execute-phase 13 --wave 8`; stop before Phase 14. CGB-07 remains open.

## Self-Check: PASSED

All five created test, ledger, verifier, and RED-evidence files exist. The four task commits are ancestors of the plan ending SHA, and `summary_coverage` plus its self-test passed.

---
*Phase: 13-cgb-hdma*
*Plan: 09*
*Completed: 2026-10-14*
