---
phase: 12-cgb-double-speed
plan: 11
subsystem: emulator-validation
tags: [cgb, stop, hostile-fixture, rgbds, timing]
requires:
  - phase: 12-cgb-double-speed
    provides: The original speed fixture, the pinned RGBDS recipe, and the 12-09 stall gate.
provides:
  - Eight selector-controlled hostile STOP entry points with rule-derived outcomes.
  - A public-API ROM-copy driver, selector marker checks, and a tampered-outcome negative control.
  - Pinned source and ROM identity for the separate hostile guest.
affects: [12-cgb-double-speed/12-12, CGB-06]
actuals:
  tokens: 5749
  tasks: 2
  commits: 2
plan_head_before: c632ad2599c389e6ef1d601cea722440c246b16e
plan_head_after: dbc9bd5f14ab23c244f1b180f1a13e4983741d20
tech-stack:
  added: []
  patterns:
    - In-memory ROM selector patching through the public API.
    - First-principles outcome bounds from D-02, D-08, D-09, and the pinned stall value.
key-files:
  created:
    - fixtures/cgb-speed/speed-hostile.asm
    - fixtures/cgb-speed/speed-hostile.gb
  modified:
    - fixtures/cgb-speed/manifest.json
    - tests/scripts/derive-cgb-speed-expectations.py
    - tests/data/cgb-speed-expectations.txt
    - tests/test_cgb_speed_fixture.c
    - tests/CMakeLists.txt
    - tests/expected-tests.txt
key-decisions:
  - Keep speed.gb, its digest, and the pre-existing identity pins unchanged; hostile entries use a separate original guest.
  - Derive timer and LY intervals from documented clock units and STALL_T=0x20004 without fitting the core observations.
  - Capture pending IF before disarming interrupts for the guest's stable idle loop.
requirements-completed: [CGB-06]
coverage:
  - id: GB-12-11-HOSTILE
    description: Eight original guest entry points exercise pending IRQ, IME-off, in-stall wake, held-button HALT, EI;STOP, LCD-off DIV, active DMA, and four consecutive switches; selectors 0 and 9 retain distinct markers.
    requirement: CGB-06
    human_judgment: false
    verification:
      - kind: e2e
        ref: cgb_speed_fixture_hostile
        status: pass
      - kind: integration
        ref: cgb_speed_fixture_digest
        status: pass
  - id: GB-12-11-EXPECTATIONS
    description: Hostile outcome bounds are derived independently from D-02/D-08 timing rules and checked against the guest observations.
    requirement: CGB-06
    human_judgment: false
    verification:
      - kind: unit
        ref: python3 -I tests/scripts/derive-cgb-speed-expectations.py --check tests/data/cgb-speed-expectations.txt
        status: pass
      - kind: integration
        ref: cgb_speed_fixture_hostile
        status: pass
  - id: GB-12-11-TAMPER
    description: A configure-time copy with selector 4 KEY1-after changed to 0xFE is rejected by the independent host verdict.
    requirement: CGB-06
    human_judgment: false
    verification:
      - kind: integration
        ref: cgb_speed_expectations_hostile_tampered
        status: pass
  - id: GB-12-11-PROVENANCE
    description: The hostile ROM is reproducible with digest-pinned RGBDS 1.0.1 and its manifest source and byte hashes match.
    requirement: CGB-06
    human_judgment: false
    verification:
      - kind: other
        ref: Pinned RGBDS 1.0.1 rebuild followed by cmp against fixtures/cgb-speed/speed-hostile.gb
        status: pass
      - kind: integration
        ref: cgb_speed_fixture_digest
        status: pass
duration: ">=42min lower bound from persisted plan ledger; initial task start was not recorded"
completed: 2026-10-13
status: complete
---

# Phase GB-12 Plan 11: Hostile CGB Double Speed Entry Summary

An original selector guest now exercises all eight hostile STOP decision paths through the public API, with D-02/D-08-derived outcome checks and a tamper-detection control.

## Performance

- **Duration:** At least 42 minutes from the persisted plan ledger; work began before that timestamp.
- **Tasks:** 2.
- **Plan files modified:** 9.
- **Plan task commits:** 2.

## Accomplishments

- Added selectors 1–8 to the separate `speed-hostile.gb`: pending timer IRQ with IME on and off, timer wake during the stall, held RIGHT with HALT/no speed switch, EI;STOP without an IRQ, LCD-off DIV sampling, OAM DMA across STOP, and four consecutive speed switches. Selector 0 records the no-variant marker; selector 9 records the bad-selector marker.
- The test patches only byte `$0200` in a heap copy, loads each copy with `gbb_load_rom`, and sends the held-button event through `gbb_queue_events`. It checks the outcome record and remains bounded to 60 frames.
- Added 66 hostile expectation rows. The derivation uses D-02/D-08 branches, TAC periods, 912 half-dots per PPU line, D-09 realignment, and the plan 12-09 `STALL_T` value. It reads neither emulator output nor core source.
- Registered a tampered-table control that changes selector 4's expected KEY1-after value from `$7F` to `$FE`; the host verdict rejects it at `hostile-4 hostile-key1-after`.
- Rebuilt with the verified RGBDS 1.0.1 binaries. `speed-hostile.gb` is 32,768 bytes with SHA-256 `c03dc826d8da5fcb7adba5fcd9d5c231686519d8fa3ab23cefa57e2e5c027471`; its source SHA-256 is `e2ed657067d127215ddb329bc97a16057de7ad7330bc6c15c10cd181dd3544d2`. The manifest still pins the original `speed.gb` at `3c6e88de1e28d47566f7486dd13813c8fb1baf48ee336509e3902bd9ff8e2f3f`.
- The fixture remains classified as pinned author-attested software-model evidence. No physical-hardware result is claimed, and the public API and core semantics were unchanged.

## Verification

- `python3 -I tests/scripts/derive-cgb-speed-expectations.py --check tests/data/cgb-speed-expectations.txt` passed with 119 rows total.
- `ctest --test-dir build -R '^(cgb_speed_fixture_|cgb_speed_expectations_)' --output-on-failure --no-tests=error` passed 13/13.
- `ctest --test-dir build --output-on-failure -j8 --no-tests=error` passed 833/833 in 41.73 seconds.
- The RGBDS 1.0.1 rebuild matched the committed ROM byte-for-byte; all manifest source hashes matched. Plan acceptance checks found two fixtures, one registration per hostile test, and no changes to `speed.gb`, `common.inc`, or `speed.asm`.

## Task Commits

1. **Task 1: Selector 1 tracer guest and public-API driver** — `18323e7` (`feat`).
2. **Task 2: Entries 2–8 and tampered-outcome control** — `dbc9bd5` (`feat`).

## Decisions Made

- TMA reloads to zero after the one-shot timer overflow so a pending request does not repeat while IF remains set.
- The guest captures IF as part of its outcome record, then clears IE and IF before the stable idle loop. This keeps later interrupt activity from changing the recorded result.
- LCD-off timing uses the DIV sample because LY remains at zero. DMA verification reads the final OAM byte after the full stall.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Stabilized the guest after recording a pending interrupt outcome**
- **Found during:** Task 2.
- **Issue:** The IME-off selector left its recorded IF request active while the guest continued into the idle loop, allowing later interrupt activity to affect the outcome byte.
- **Fix:** Capture IF first, then clear IE and IF before entering the stable HALT loop.
- **Files modified:** `fixtures/cgb-speed/speed-hostile.asm`.
- **Verification:** `cgb_speed_fixture_hostile` and `cgb_speed_expectations_hostile_tampered` passed.
- **Committed in:** `dbc9bd5`.

**2. [Rule 1 - Bug] Corrected the independently derived timer line bounds**
- **Found during:** Task 2.
- **Issue:** The first draft divided double-speed timer T-cycles by 456 dots instead of 912 master half-dots per line and selected the wrong TAC-period index for `$04`.
- **Fix:** Apply the documented half-dot conversion and use the 1024-T period selected by TAC `$04`; retain bounds derived from the clock model.
- **Files modified:** `tests/scripts/derive-cgb-speed-expectations.py`, `tests/data/cgb-speed-expectations.txt`.
- **Verification:** Derivation `--check`, all 13 focused tests, and the 833-test suite passed.
- **Committed in:** `dbc9bd5`.

## Issues Encountered

The final test result stays tied to the rule-derived table. The initial discrepancies narrowed the unit conversion and guest setup; neither was resolved by widening the locked stall value or fitting expectations to observations.

## Next Phase Readiness

Plan 12-11 is complete. Phase GB-12 remains in progress. The next plan is **12-12**, via **`/gsd-execute-phase 12`**; that command resumes at plan 12-12. Stop there until the owner chooses to continue. Auto-advance remains disabled.

---
*Phase: 12-cgb-double-speed*
*Completed: 2026-10-13*

## Self-Check: PASSED

- Summary file exists.
- Task commits `18323e7` and `dbc9bd5` are ancestors of HEAD.
- `summary_coverage` passed 1/1.
