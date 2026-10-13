---
phase: GB-12-cgb-double-speed
plan: 10
subsystem: core-validation
tags: [cgb, double-speed, rgbds, public-api, fixture, sha256]
requires:
  - phase: GB-12 plans 12-01 through 12-09
    provides: KEY1/STOP speed switching, the bounded CPU stall, public mutant core, and the measured AGE stall window
provides:
  - Original MIT CGB speed fixture with four-phase timer, DIV, serial, NR52, DMA, KEY1, and STOP probes
  - Independent 53-row first-principles expectation table with tampered-table and wrong-speed-ratio controls
  - Clean-core PCM and RGB555 digest pins with M17/M1 mutant sensitivity and zero-mask controls
affects: [GB-12, CGB-06, Phase 12 verification]
actuals:
  tokens: 10135
  tasks: 3
  commits: 4
plan_head_before: 34ba2284b81cf1c48a52463ef988a85b4a40b774
plan_head_after: 6fcd930610049452fb83e5aa7981fc194fd340c6
tech-stack:
  added: [RGBDS 1.0.1 pinned fixture build, Python standard-library derivation]
  patterns: [independently derived integer bounds, public-API digest assertions, build-tree-only mutant core]
key-files:
  created:
    - fixtures/cgb-speed/LICENSE.txt
    - fixtures/cgb-speed/common.inc
    - fixtures/cgb-speed/manifest.json
    - fixtures/cgb-speed/speed.asm
    - fixtures/cgb-speed/speed.gb
    - tests/scripts/derive-cgb-speed-expectations.py
    - tests/data/cgb-speed-expectations.txt
    - tests/test_cgb_speed_fixture.c
  modified:
    - .gitignore
    - tests/CMakeLists.txt
    - tests/expected-tests.txt
key-decisions:
  - "Keep the speed fixture as project-authored, MIT-licensed software evidence; it is not a physical-hardware observation."
  - "Derive timing bounds from the clock units and the guest polling-loop resolution, including at most seven M-cycles of LY-read phase jitter."
  - "Run the DMA straddle in VBlank and sample bus phases at M+159 and M+161 to isolate DMA completion from PPU OAM arbitration."
  - "Pin audio and frame identities from the clean core at revision b326599; retain the measured stall constant 0x20004 T from the 12-09 window."
requirements-completed: [CGB-06]
coverage:
  - id: D1
    description: Original four-phase speed fixture and independent expectation controls validate the timer, DIV, serial, NR52, DMA, KEY1, and STOP observations.
    requirement: CGB-06
    human_judgment: false
    verification:
      - kind: integration
        ref: cgb_speed_fixture_digest
        status: pass
      - kind: integration
        ref: cgb_speed_fixture_probes
        status: pass
      - kind: unit
        ref: cgb_speed_expectations_derive
        status: pass
      - kind: integration
        ref: cgb_speed_expectations_tampered
        status: pass
      - kind: integration
        ref: cgb_speed_expectations_factor3
        status: pass
  - id: D2
    description: The clean-core 60-frame PCM digest is pinned and detects the APU-2x mutation.
    requirement: CGB-06
    human_judgment: false
    verification:
      - kind: integration
        ref: cgb_speed_fixture_audio_digest
        status: pass
      - kind: integration
        ref: cgb_speed_fixture_audio_digest_mutant_m17
        status: pass
      - kind: integration
        ref: cgb_speed_fixture_audio_digest_mutant_m17_control
        status: pass
  - id: D3
    description: The clean-core 60-frame RGB555 digest is pinned and detects the PPU-follows-CPU mutation.
    requirement: CGB-06
    human_judgment: false
    verification:
      - kind: integration
        ref: cgb_speed_fixture_frame_digest
        status: pass
      - kind: integration
        ref: cgb_speed_fixture_frame_digest_mutant_m1
        status: pass
      - kind: integration
        ref: cgb_speed_fixture_frame_digest_mutant_m1_control
        status: pass
duration: "13m+ lower bound from first task commit; earlier execution time was not captured"
completed: 2026-10-13
status: complete
---

# Phase GB-12 Plan 10: CGB Double Speed Summary

**An original CGB speed guest now checks CPU-side timing against independent bounds and pins its PCM and RGB555 output against targeted speed regressions.**

## Performance

- **Duration:** At least 13 minutes from the first task commit; earlier execution time was not captured.
- **Started:** Not captured before the first committed tracer at 2026-10-13T18:17:37-04:00.
- **Completed:** 2026-10-13.
- **Tasks:** 3/3.
- **Files modified:** 11.

## Accomplishments

- Added the original project-authored, MIT-licensed `speed.gb` fixture using the digest-pinned RGBDS 1.0.1 archive. Its four phases cover TIMA and DIV per scanline, internal-clock serial completion and flags, NR52 length expiry, the OAM DMA completion boundary, KEY1 readbacks, and LY movement across STOP.
- Added a standard-library derivation script and 53-row committed table. The host checks each raw WRAM observation through the public API; a tampered table and a speed-factor-3 table both reject the clean core.
- Pinned the 60-frame PCM digest as `126c6ddf5cf8f0e2fb394e8978c1ad018b633e0bd8e1a0785ecb6cca72d4db82` and the RGB555 frame digest as `1f550c49fa9c6c3e99fbb3cc2982198125a89eb0c2ef6ca95e3c935bcbb7a100`. The audio test catches M17 and the frame test catches M1; each zero-mask mutant control passes.
- Kept all emulator core and public API semantics unchanged. Mutant code is generated only in the build tree and is linked only into the dedicated test executable.

## Task Commits

1. **Task 1: Speed probe tracer and independent bounds** — `a9456fa` (`feat`).
2. **Task 2: Device probes and negative expectation controls** — `b326599` (`feat`).
3. **Task 3 RED: Failing digest assertions** — `a800bef` (`test`).
4. **Task 3 GREEN: Clean-core pins and mutant controls** — `6fcd930` (`feat`).

The documentation and tracking changes are committed separately after this summary is verified.

## Evidence and provenance

The age window used by the independent STOP-line derivation is the committed-core AGE result recorded by plan 12-09: inclusive `[0x20004, 0x20007]` T at source revision `2e78a48`, with `GBB_SPEED_SWITCH_STALL_T` still `0x20004` T. The measured AGE run reached its verdict at 22,702,928 half-dots under the recorded 46,000,000-half-dot budget. Plan 12-10 did not remeasure or change that window.

The digest observations came from the clean core at committed revision `b326599`; no `src/core` or public-header changes were made in this plan. The fixture manifest records the source and ROM SHA-256 values and labels the corpus as attested software evidence. No physical-hardware result is claimed.

## TDD Gate Compliance

- **RED, audio:** `build/tdd-red-audio.xml`; the named CTest failed only at the zero-sentinel PCM digest assertion and printed observed digest `126c6ddf5cf8f0e2fb394e8978c1ad018b633e0bd8e1a0785ecb6cca72d4db82`. `gsd-tools check tdd-red-evidence` returned `RED_EVIDENCE_OK`; semantic inspection confirmed the target executed and no build or fixture fault occurred.
- **RED, frame:** `build/tdd-red-frame.xml`; the named CTest failed only at the zero-sentinel RGB555 digest assertion and printed observed digest `1f550c49fa9c6c3e99fbb3cc2982198125a89eb0c2ef6ca95e3c935bcbb7a100`. The evidence classifier returned `RED_EVIDENCE_OK`, and semantic inspection confirmed the planned assertion failure.
- **GREEN:** Both clean digest cases pass after pinning those observed values. M17 and M1 fail their corresponding digests; mask-zero controls pass. No refactor commit was needed.

## Deviations from Plan

**1. [Rule 3 - Blocking issue] Narrow fixture ignore exception.** The repository-wide `*.gb` ignore rule hid the new owned fixture from Git. Added a path-specific allowlist for `fixtures/cgb-speed/speed.gb`; the file remains the only newly admitted ROM in this plan.

**2. [Rule 1 - Fixture correctness] Explicit VBlank timing for the DMA straddle.** The first probe schedule could overlap PPU mode-2/3 OAM arbitration, obscuring the DMA result. The guest now starts the two HRAM routines on the LY 143-to-144 transition, keeps the timed bus reads at M+159/M+161, and records the blocked then available OAM values without changing core behavior.

**3. [Rule 1 - Independent-oracle correction] Derive SC readback and timer resolution from their contracts.** CGB SC reads force bits 1-6 high, so the completion value derives as `$7F` from `$7E | serial_control`; `$7D` was an incorrect initial derivation. The TIMA interval includes the known maximum seven-M-cycle LY polling phase jitter, yielding normal-speed `[26,31]` and double-speed `[55,59]` bounds. These are derived from the register mask, polling loop, TAC period, and clock units; they are not fitted to emulator samples.

**4. [Rule 3 - Negative-control anchor] Track the derived TIMA interval.** After deriving the jitter bound, the configure-time tamper control's exact source anchor was updated from the obsolete nominal row to `tima 0 26 31`; the control still replaces that row with `[200,201]` and the host rejects it.

**Total deviations:** 4 resolved adjustments. No core/API changes, skipped checks, or deferred plan requirements.

## Verification

- Pinned RGBDS 1.0.1 assembled and fixed the final 32 KiB ROM; manifest verification passed for both source hashes and the binary digest.
- `python3 -I tests/scripts/derive-cgb-speed-expectations.py --check tests/data/cgb-speed-expectations.txt` passed with 53 rows.
- The probe, derivation, manifest, tampered-table, and speed-factor-3 CTests passed 5/5.
- Clean audio/frame digest tests, M17/M1 mutants, and mask-zero controls passed 6/6.
- `cmake --preset phase1 && cmake --build --preset phase1 -j8 && ctest --test-dir build --output-on-failure --no-tests=error -j8` passed the complete configured inventory: 831/831.
- Acceptance counts matched: six core-digest CTest names, two expectation negative controls, 36 DIV/serial/NR52/DMA table rows, and ten test-target mentions for `test_cgb_speed_fixture_p12`.

## Next Phase Readiness

Plan 12-10 is complete; Phase 12 remains in progress. The next plan is **GB-12 plan 12-11 — hostile pre-switch entry points (selector byte) with rule-derived outcomes**. The next phase after Phase 12 is **Phase 13 — CGB HDMA**, not started. Resume with **`/gsd-execute-phase 12`**, which starts from plan 12-11. Auto-advance and auto-chain remain false.

---
*Phase: GB-12-cgb-double-speed*
*Plan: 10, completed 2026-10-13*

## Self-Check: PASSED

The SUMMARY exists, and all four task commits are ancestors of the current plan branch head.
