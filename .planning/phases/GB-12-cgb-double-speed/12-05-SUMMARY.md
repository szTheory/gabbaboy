---
phase: 12-cgb-double-speed
plan: 05
subsystem: timing
tags: [cgb, double-speed, cpu-ticks, timer, serial, dma, apu, rtc]
requires:
  - phase: 12-01
    provides: "CGB KEY1 and STOP speed-switch state"
  - phase: 12-03
    provides: "Runtime-mask speed mutant harness and CPU timing contracts"
provides:
  - "CPU-tick timer reload, serial and OAM DMA countdowns across CGB speed changes"
  - "Speed-specific APU DIV frame-sequencer taps"
  - "Behavioral and structural proof that PPU, APU channel timers, PCM and RTC remain in master time"
affects: [12-06, 12-09, 12-10, 12-16]
actuals:
  tokens: 7911
  tasks: 3
  commits: 7
  plan_head_before: 5480a617c97e4a4e0365b6c833e4456f2086a59c
  plan_head_after: d205aa0da932a546d695909619f1f726f2e974cf
tech-stack:
  added: []
  patterns:
    - "CPU-side countdowns are stored in T ticks and decremented only on cpu_tick"
    - "Speed-domain structural checks lex C function bodies while ignoring comments and literals"
key-files:
  created:
    - tests/scripts/verify-speed-domains.py
  modified:
    - src/core/gabbaboy.c
    - tests/test_cgb_speed_internal.c
    - cmake/P12Mutants.cmake
    - tests/CMakeLists.txt
    - tests/expected-tests.txt
key-decisions:
  - "The frame-sequencer DIV tap is bit 12 at normal speed and bit 13 at double speed, including DIV reset edges."
  - "Timer reload, serial edge and DMA byte progress use integer CPU-tick countdowns so no fractional phase is created by a speed switch."
requirements-completed: [CGB-06]
coverage:
  - id: GB-12-05-01
    description: "Guest timer and DIV samples across two LY transitions show twice the CPU-side rate at double speed, preserve pending reload ticks, and retain normal-speed identity."
    requirement: CGB-06
    human_judgment: false
    verification:
      - kind: unit
        ref: cgb_speed_timer_scaling
        status: pass
      - kind: unit
        ref: cgb_speed_mutant_m3_timer_unscaled and cgb_speed_mutant_m3_timer_unscaled_control
        status: pass
      - kind: unit
        ref: cgb_speed_mutant_m15_timer_reload_half_dot_units and cgb_speed_mutant_m15_timer_reload_half_dot_units_control
        status: pass
      - kind: unit
        ref: cgb_speed_identity_pin and cgb_speed_identity_pin_flipped
        status: pass
      - kind: other
        ref: "bash tests/scripts/verify-dmg-baseline.sh (baseline status=pass)"
        status: pass
  - id: GB-12-05-02
    description: "Serial, DMA and frame-sequencer rates scale with CPU ticks, while switch remainders survive and TIMA reload uses the remaining ticks."
    requirement: CGB-06
    human_judgment: false
    verification:
      - kind: unit
        ref: cgb_speed_serial_scaling and cgb_speed_mutant_m2_serial_unscaled with control
        status: pass
      - kind: unit
        ref: cgb_speed_dma_scaling and cgb_speed_mutant_m14_dma_unscaled with control
        status: pass
      - kind: unit
        ref: cgb_speed_apu_tap and cgb_speed_mutant_m4_apu_tap_unscaled with control
        status: pass
      - kind: unit
        ref: cgb_speed_remainder_across_switch and cgb_speed_mutant_m11_remainder_dropped_at_switch with control
        status: pass
      - kind: other
        ref: "gsd check tdd-red-evidence build/tdd-red-12-05-task2.json (RED_EVIDENCE_OK)"
        status: pass
  - id: GB-12-05-03
    description: "PPU line and frame timing, APU channel and PCM output, and RTC seconds remain equal in master time at both CPU speeds."
    requirement: CGB-06
    human_judgment: false
    verification:
      - kind: unit
        ref: cgb_speed_ppu_apu_rtc_unscaled
        status: pass
      - kind: unit
        ref: cgb_speed_mutant_m1_ppu_scaled and control
        status: pass
      - kind: unit
        ref: cgb_speed_mutant_m12_rtc_scaled and control
        status: pass
      - kind: unit
        ref: cgb_speed_mutant_m17_apu_channels_scaled and control
        status: pass
      - kind: unit
        ref: cgb_speed_domains_scan and cgb_speed_domains_scan_mutated
        status: pass
      - kind: other
        ref: "gsd check tdd-red-evidence build/tdd-red-12-05-task3.json (RED_EVIDENCE_OK)"
        status: pass
  - id: GB-12-05-04
    description: "The complete local regression suite passes with all Phase 12 timing, identity and model-gate checks present."
    requirement: CGB-06
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest --test-dir build --output-on-failure --no-tests=error -j8 (741/741)"
        status: pass
      - kind: unit
        ref: cgb_speed_identity_pin and model_gates
        status: pass
duration: "19m55s lower bound from task commit timestamps; plan start not recorded"
completed: 2026-10-13
status: complete
commits: 7
plan_head_before: 5480a617c97e4a4e0365b6c833e4456f2086a59c
plan_head_after: d205aa0da932a546d695909619f1f726f2e974cf
---

# Phase GB-12 Plan 05: CGB Double Speed Device Domains Summary

Timer, serial and OAM DMA now advance in CPU T ticks, the APU frame-sequencer tap follows the speed-dependent DIV bit, and automated tests prove the PPU, APU channel timers, PCM and RTC remain on the master timeline.

## Performance

- **Duration:** 19m55s measured from the first task commit to the final task commit; this is a lower bound because the plan start time was not recorded.
- **Tasks:** 3
- **Files modified:** 6
- **Task commits:** 7, measured from the persisted plan ledger.

## Accomplishments

- Converted timer reload and serial edge countdowns to CPU T ticks, with the timer reload converted to half-dots only for the TMA-coincidence comparison.
- Scaled DIV and the OAM DMA byte period at double speed while preserving whole-tick countdown and DMA remainders across STOP.
- Applied the speed-specific DIV tap in normal device advancement and divider reset; added PPU, APU, PCM and RTC behavior checks plus a source scanner and negative control.
- Preserved DMG and CGB single-speed identity pins and passed the full 741-test suite.

## TDD Evidence

- **Task 2 RED:** `build/tdd-red-12-05-task2.json` returned `RED_EVIDENCE_OK`; the serial, DMA and APU assertions failed against their planned scaling behaviors. GREEN passed all corresponding tests and mutant controls.
- **Task 3 RED:** `build/tdd-red-12-05-task3.json` returned `RED_EVIDENCE_OK`; the named contract failed at the APU channel timer assertion with M17 enabled. GREEN passed the clean behavior case, M1/M12/M17 mutants and controls, and the structural scanner’s mutated-core control.
- Task 1’s timer guest configured TAC=$05, polled two LY transitions, then compared TIMA and DIV deltas at both speeds. A pending reload was also checked across a speed change.
- No refactor-only commit was needed.

## Task Commits

- `0b76ed5`: `feat(12-05): scale timer and divider CPU ticks`
- `c361a38`: `test(12-05): add serial DMA and APU scaling contracts` (RED)
- `58a6ad1`: `feat(12-05): scale serial DMA and APU timing` (GREEN)
- `d2dbbf4`: `test(12-05): add master-time device contracts` (RED)
- `ba2e2bf`: `feat(12-05): prove PPU APU and RTC master-time domains` (GREEN)
- `25857b3`: `test(12-05): make RTC speed mutant explicit`
- `d205aa0`: `test(12-05): poll timer scaling through guest LY changes`

## Files Created/Modified

- `src/core/gabbaboy.c` — CPU-tick timing, timer conversion, speed-dependent APU tap and mutation anchors.
- `tests/test_cgb_speed_internal.c` — timer, serial, DMA, APU, switch-remainder and master-time contracts.
- `tests/scripts/verify-speed-domains.py` — lexical scan of PPU/APU/RTC function bodies for speed reads.
- `cmake/P12Mutants.cmake`, `tests/CMakeLists.txt`, `tests/expected-tests.txt` — named mutants, controls and required test inventory.

## Decisions Made

- Countdown state uses CPU ticks so changing speed cannot create fractional countdowns.
- The APU frame-sequencer tap uses DIV bit 12 at normal speed and bit 13 at double speed, including the shared divider-reset edge.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Test mutant equivalence] Strengthened M3’s half-rate mutation.**
- **Found during:** Task 1
- **Issue:** A mutant that reused `divider_phase == 0` was equivalent to the double-speed path because the phase is intentionally held at zero there.
- **Fix:** The mutation now samples every other half-dot when enabled, matching the intended unscaled timer/DIV fault.
- **Files modified:** `cmake/P12Mutants.cmake`
- **Verification:** M3 fails `cgb_speed_timer_scaling`; its zero-mask control passes.
- **Committed in:** `0b76ed5` (the corrected mutant was included in the task commit).

**2. [Rule 1 - Mutation precision] Made the RTC speed fault explicit in the generated mutant.**
- **Found during:** Task 3
- **Issue:** `rtc_sync` receives only cartridge state and master time, so a mutant reading machine speed there would require changing the production RTC interface and would violate the scanner contract.
- **Fix:** The generated M12 mutant introduces a local `double_speed` fault bit and shifts elapsed RTC half-dots by that bit; production RTC code stays speed-independent.
- **Files modified:** `cmake/P12Mutants.cmake`
- **Verification:** M12 fails the RTC-seconds case; its zero-mask control passes; the real-source domain scan passes.
- **Committed in:** `25857b3`.

**Total deviations:** 2 test-harness refinements. No product behavior was added outside the plan.

## Verification

- `cmake --preset phase1 && cmake --build --preset phase1` — passed.
- All 60 scaling, mutant, identity, model-gate and DMG-baseline focused tests passed; `verify-dmg-baseline.sh` reported `baseline status=pass`.
- `python3 -I tests/scripts/verify-speed-domains.py src/core/gabbaboy.c` — `speed-domains pass functions=39`.
- `ctest --test-dir build --output-on-failure --no-tests=error -j8` — 741/741 passed on the final task-code head.

## Known Stubs

None.

## Threat Flags

None. The change adds no public API, network endpoint, file trust boundary or schema.

## Self-Check: PASSED

- Summary artifact and all six declared code/test artifacts exist.
- All seven task commits are ancestors of the plan head recorded above.
- Full suite passed 741/741 on the final task-code head.

## Next Phase Readiness

Phase GB-12 remains in progress. Plan 12-06, **STOP decision cases and KEY1 contract**, is next. Continue only when the owner chooses; keep both auto-advance flags false.

---
*Phase: 12-cgb-double-speed*
*Completed: 2026-10-13*
