---
phase: GB-03-visible-interactive-dmg
plan: "03"
subsystem: video-memory
tags: [DMG, OAM-DMA, VRAM, OAM, PPU, CTest]
requires:
  - phase: GB-03-visible-interactive-dmg/03-02
    provides: Dot-timed PPU modes, frame output, and source-qualified timing cases
provides:
  - Guest-visible bounded OAM DMA progress and selected DMG source mapping
  - Guest VRAM/OAM accesses evaluated against PPU mode at the timed bus phase
  - Explicit source/model evidence limits for DMA and simultaneous PPU contention
affects: [GB-03-04, GB-03-05, VIDEO-02, VIDEO-05]
actuals:
  tokens: 11985
  tasks: 2
  commits: 5
tech-stack:
  added: []
  patterns: [private DMA observer, original guest-authored bus probes, mode-specific evidence matrix]
key-files:
  created: []
  modified: [src/core/gabbaboy.c, tests/test_dma.c, tests/test_bus.c, tests/CMakeLists.txt, tests/expected-tests.txt, docs/dmg-video-evidence.md]
key-decisions:
  - "Adopt the narrower Nintendo manual DMG DMA source envelope `$8000–$DFFF`; record its conflict with pinned Pan Docs as an evidence gap."
  - "Expose VRAM and OAM through guest preflight while enforcing mode lockouts at each actual CPU bus timestamp."
  - "Do not assert disputed simultaneous PPU/DMA collision or CPU-B electrical behavior without model-applicable evidence."
patterns-established:
  - "Separate CPU bus availability from the PPU/DMA device memory paths and qualify each initiator independently."
  - "Keep guest test scratch outside copied HRAM code and bound the generated routine against that region."
requirements-completed: []
coverage:
  - id: D1
    description: "Guest OAM DMA progress, selected source mapping, HRAM execution, and CPU read/write blocking are observable."
    requirement: VIDEO-02
    verification:
      - kind: unit
        ref: "ctest --preset phase1 --output-on-failure --no-tests=error -R '^dma_.*$'"
        status: pass
    human_judgment: false
  - id: D2
    description: "Guest VRAM/OAM reads and writes observe LCD-off and mode 0/1/2/3 access rules around mode transitions."
    requirement: VIDEO-02
    verification:
      - kind: unit
        ref: "dma_vram_lock, dma_oam_lock in tests/test_dma.c"
        status: pass
    human_judgment: false
  - id: D3
    description: "Exact simultaneous PPU/DMA collision effects are qualified for DMG-CPU-B."
    requirement: VIDEO-02
    verification: []
    human_judgment: true
    rationale: "No CPU-B board observation or model-specific primary rule is available for the disputed collision effects; tests deliberately do not invent a pass/fail hardware result."
  - id: D4
    description: "Image composition, PPU timing, and scripted gameplay remain separately checked from DMA/access behavior."
    requirement: VIDEO-05
    verification:
      - kind: integration
        ref: "ctest --preset phase1 --output-on-failure --no-tests=error -R '^(dma_.*|ppu_timing_.*|frame_composition_.*|joypad_gameplay_tracer|bus_(preflight|unsupported_stack|unsupported_fetch))$'"
        status: pass
    human_judgment: false
duration: 79min
completed: 2026-10-07
status: complete
---

# Phase 3 Plan 03 Summary

**Guest-visible OAM DMA and mode-timed VRAM/OAM lockouts now have bounded tests, with CPU-B collision claims kept open.**

## Performance

- **Duration:** 79 min
- **Started:** 2026-10-07T18:13:15Z
- **Completed:** 2026-10-07T19:31:54Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments

- Added guest probes for bounded 160-byte DMA progress, source-page mapping, HRAM execution, blocked CPU accesses, reset cancellation, instance isolation, and adjacent-budget determinism.
- Exposed mapped VRAM `$8000–$9FFF` and OAM `$FE00–$FE9F` to bus preflight so existing timed PPU lock rules can be observed by guest code; kept cartridge RAM and unusable addresses unsupported.
- Added mode-straddling guest reads/writes and documented each assertion's source, profile, and evidence class in the DMA/access matrix.

## Task Commits

1. **Task 1 tests:** `af276e2` — failing OAM DMA guest coverage.
2. **Task 1 implementation:** `d34d181` — bounded DMG OAM DMA.
3. **Task 2 tests:** `362f9ba` — display-memory lockout coverage.
4. **Task 2 implementation and evidence:** `6bf7457` — timed VRAM/OAM bus mapping.
5. **Test-fixture bound:** `065ae59` — keep DMA probe scratch beyond copied HRAM code.

The Task 2 red receipt was independently accepted by OpenGSD as `RED_EVIDENCE_OK` for `dma_vram_lock`; the initial failure occurred at the intended unsupported-bus preflight.

## Files Created/Modified

- `src/core/gabbaboy.c` — admits the mapped VRAM/OAM address windows to guest instruction preflight while preserving actual-time lock checks.
- `tests/test_dma.c` — guest DMA, CPU/PPU-mode access, source, reset, isolation, and partition cases.
- `tests/test_bus.c` — keeps unsupported stack/fetch controls at actual unmapped boundaries.
- `tests/CMakeLists.txt`, `tests/expected-tests.txt` — registers the DMA/access cases in the required inventory.
- `docs/dmg-video-evidence.md` — records the source conflict, per-case applicability, measured guest timestamps, and open collision gaps.

## Decisions Made

- Use the narrower Nintendo *Game Boy Programming Manual* `$8000–$DFFF` DMG DMA source range for this ROM-only model. The pinned Pan Docs source allows `$00–$DF`; that conflict remains documented rather than silently widening the implementation.
- Treat `$FF` blocked reads and ignored writes as explicit emulator policy because the cited sources do not provide exact CPU-B electrical values.
- Keep CPU, PPU, and DMA as separate initiators. Tests verify CPU gating and the DMA source/destination path; they do not qualify revision-specific OAM corruption or simultaneous PPU/DMA collision outcomes.

## Automated Results

- Full local offline inventory: **125/125 passed**.
- Focused DMA/PPU/frame/gameplay/bus regression set: **23/23 passed**.
- Linux ASan/UBSan full inventory: **125/125 passed**; the latest DMA/bus subset also passed **13/13** after the HRAM fixture bound.
- `git diff --check` passed.

## Issues Encountered

- The sanitizer preset's ignored local cache pointed at a previous `/work` checkout, and the macOS host correctly rejected the Linux-only sanitizer option. Verification used a clean Linux container build instead of deleting the stale cache.
- Extending the HRAM guest initially let scratch at `$FFA0` overwrite the longer copied routine. Moving scratch to `$FFB0+` and bounding the routine fixed the fixture; `dma_hram` and the DMA suite pass.

## Evidence and Limitations

The mapped access implementation and tests are software evidence for the bootless `GBB_PROFILE_DMG_CPU_B` model. There was no physical CPU-B board observation. The Nintendo manual versus Pan Docs source-range conflict remains open, as do accepted FF46 restart semantics, blocked-bus electrical values, exact coincident CPU/DMA ordering, and revision-specific OAM corruption. `dma_contention` proves per-instance isolation and reset cancellation; its name does not imply qualification of contested PPU collision effects.

Plan tasks are complete, but this summary does not mark VIDEO-02 or VIDEO-05 complete for the phase. VIDEO-02 still requires evidence for simultaneous CPU/PPU/DMA contention; VIDEO-05 spans later UI/package plans. Preserve those gates through Phase 3 verification.

## Next Phase Readiness

Continue with Wave 4 / Plan 03-04, which owns deterministic JOYP polling and the separate D-08 interrupt evidence gate. Keep Phase 3 executing, retain the VIDEO-02 collision limitation, and stop after Phase 3 before Phase 4.

---
*Phase: GB-03-visible-interactive-dmg*
*Completed: 2026-10-07*
