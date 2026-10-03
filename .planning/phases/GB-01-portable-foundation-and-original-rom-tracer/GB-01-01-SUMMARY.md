---
phase: 01-portable-foundation-and-original-rom-tracer
plan: 01
subsystem: core
tags: [c17, cmake, dmg-cpu-b, rgbds, tracer]
requires: []
provides:
  - Bounded opaque C API and minimal DMG-CPU-B CPU/RAM bus path for the original tracer
  - Checked-in project-authored tracer ROM with source, license, build identity, protocol, and digest
  - Offline CTest digest verification and local build/run documentation
affects: [01-02, 01-03, 01-04, 01-05]
actuals:
  tokens: 5352
  tasks: 2
  commits: 2
commits: 2
plan_head_before: ae2dbed7359938354b5005fdc41085d7d32ab0eb
tech-stack:
  added: [C17, CMake 3.25+, RGBDS 1.0.1 fixture tool]
  patterns: [instance-owned state, instruction-atomic half-dot budgeting, caller-owned fixed trace]
key-files:
  created: [CMakeLists.txt, CMakePresets.json, include/gabbaboy/gabbaboy.h, src/core/gabbaboy.c, src/runner/main.c, fixtures/tracer/tracer.asm, fixtures/tracer/tracer.gb, fixtures/tracer/manifest.json, fixtures/tracer/LICENSE.txt, cmake/VerifyFixture.cmake]
  modified: [README.md]
key-decisions:
  - "Keep the DMG-CPU-B profile bootless and explicitly distinguish its deterministic RAM fill from hardware startup state."
  - "Keep RGBDS out of normal build/test; verify the checked ROM with built-in CMake SHA-256 and use pinned RGBDS only for explicit regeneration."
patterns-established:
  - "Run each instruction only after its full half-dot cost fits the remaining caller budget."
  - "Capture fixed-size instruction-boundary records in caller storage and stop explicitly at capacity."
requirements-completed: []
coverage:
  - id: D1
    description: "Original guest stores and reads RAM through the CPU/bus path and reaches the success marker."
    requirement: BASE-04
    verification:
      - kind: integration
        ref: "ctest --preset phase1 --output-on-failure --no-tests=error -R '^tracer_smoke$'"
        status: pass
    human_judgment: false
  - id: D2
    description: "Checked ROM identity matches its authored-source provenance manifest."
    requirement: BASE-05
    verification:
      - kind: unit
        ref: "ctest --preset phase1 --output-on-failure --no-tests=error -R '^fixture_digest$'"
        status: pass
      - kind: integration
        ref: "RGBDS v1.0.1 regeneration and byte comparison; corrupted manifest digest rejection"
        status: pass
    human_judgment: false
duration: 8min
completed: 2026-10-03
status: complete
---

# Phase 1 Plan 1: Portable Foundation and Original ROM Tracer Summary

**A C17 headless core runs an original RAM round-trip ROM through a bounded DMG-CPU-B CPU/bus path and verifies fixture identity offline.**

## Performance

- **Duration:** 8 min
- **Started:** 2026-10-03T11:09:13Z (phase executor start recorded in STATE.md)
- **Completed:** 2026-10-03T11:17:08Z
- **Tasks:** 2
- **Files modified:** 11

## Accomplishments

- Added schema-6 CMake presets and a standard-library-only C17 core/runner build; CTest invokes the runner against the checked-in fixture.
- Implemented the DMG-CPU-B bootless handoff profile, ROM-only cartridge validation, real ROM/RAM bus instructions, strict half-dot budget preflight, and bounded caller-owned trace records.
- Authored and assembled a ROM that writes 0x5A to guest RAM, reads and compares it, then writes distinct success/failure markers. The runner reports guest-derived outcome, stop reason, elapsed half-dots, and trace records.
- Recorded the source/license, RGBDS v1.0.1 recipe, digest, model applicability, protocol, timeout, and reachable byte/opcode inventory; added offline digest validation and precise scope limits.

## Task Commits

1. **Task 1: Run the original guest RAM tracer through the public core** - `48cab4a` (`feat`)
2. **Task 2: Record fixture provenance and deterministic profile evidence** - `c75a470` (`docs`)

**Measured plan commits:** 2 from `ae2dbed7359938354b5005fdc41085d7d32ab0eb` to `HEAD` before metadata close-out.

## Files Created/Modified

- `CMakeLists.txt`, `CMakePresets.json` - Minimal C17 core/runner targets, schema-6 presets, tracer smoke, and digest case.
- `include/gabbaboy/gabbaboy.h`, `src/core/gabbaboy.c` - Opaque instance API, supported profile, ROM-only load, CPU/bus subset, budget and trace contract.
- `src/runner/main.c` - Bounded fixture-file loading, guest-marker protocol, outcome reporting, and host trace formatting.
- `fixtures/tracer/tracer.asm`, `fixtures/tracer/tracer.gb`, `fixtures/tracer/manifest.json`, `fixtures/tracer/LICENSE.txt` - Original source and exact fixture provenance.
- `cmake/VerifyFixture.cmake` - Built-in CMake JSON/SHA-256 identity check.
- `README.md` - Build/run commands and explicit evidence boundaries.

## Decisions Made

- Kept the supported profile limited to DMG-CPU-B at cartridge entry, with no boot ROM and no claim of boot or broad compatibility.
- Treated zero-filled work RAM as emulator policy; documented DIV/STAT handoff values without claiming I/O emulation.
- Kept RGBDS as an explicit fixture-regeneration tool. Normal build and digest verification use only checked-in bytes and CMake.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Corrected the entry jump half-dot cost**
- **Found during:** Task 1
- **Issue:** The initial implementation assigned 16 half-dots to `JP a16`, below its four M-cycle cost.
- **Fix:** Set the instruction cost to 32 half-dots and verified trace time advances from the 0x0100 jump boundary by 32.
- **Files modified:** `src/core/gabbaboy.c`
- **Verification:** Tracer smoke passed and emitted entry at time 0 followed by target instruction at time 32.
- **Committed in:** `48cab4a`

**2. [Rule 2 - Missing Critical] Bound supported declared ROM-size codes before shifting**
- **Found during:** Task 1
- **Issue:** An unchecked header ROM-size code could make size arithmetic unsafe for untrusted ROM input.
- **Fix:** Reject codes above the maximum supported 8 MiB ROM-only image before calculating the declared length; exact declared/actual size matching is required.
- **Files modified:** `src/core/gabbaboy.c`
- **Verification:** Valid 32 KiB fixture loaded and ran; loader code rejects out-of-range codes before allocation or instance mutation.
- **Committed in:** `48cab4a`

**Total deviations:** 2 auto-fixed (1 bug, 1 critical input-bound check).

## Verification Evidence

- `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error -R '^tracer_smoke$'` — passed; CTest ran one tracer case.
- `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error -R '^fixture_digest$'` — passed; CTest ran one digest case.
- Regenerated the ROM with RGBDS v1.0.1 and compared bytes — identical to `fixtures/tracer/tracer.gb`.
- Replaced manifest SHA-256 in a temporary copy with zeroes — digest verifier failed with a mismatch as required.
- Fixture SHA-256: `85d84babe64e852babc55fe355919f9d2f8013f90dc56550d58e972470321f77`.

## Deferred Requirements and Limitations

No requirement IDs are marked complete at this plan boundary. BASE-01 still needs install/consumer/CI proof; BASE-02 needs reset, repeated-load, independent-instance tests, and full API ownership/thread documentation; BASE-03 needs malformed-input non-destructive regression cases; BASE-04 needs the planned failure/unsupported/timeout controls; BASE-05 needs the isolated CI regeneration check. Phase-level requirement checkboxes remain pending until their complete evidence exists.

The implementation intentionally supports only this fixture's reachable instruction subset and one DMG profile. The code has no CGB, boot ROM, I/O devices, display, audio, mapper, save, or general gameplay behavior. The fixture identity/digest is verified locally; no remote or hosted CI evidence exists in this repository.

## Next Plan Readiness

Plan 01-02 owns lifecycle/repeated-instance contracts, malformed loader controls, and explicit negative tracer outcomes. Continue with `$gsd-execute-phase 1`; the executor should select Plan 01-02 after this summary is recognized. Do not mark Phase 1 complete or begin another phase.

---
*Phase: 01-portable-foundation-and-original-rom-tracer*
*Plan: 01*
*Completed: 2026-10-03*

## Self-Check: PASSED

- Summary file exists at the plan-declared output path.
- Task commits `48cab4a` and `c75a470` exist in git history.
- OpenGSD detects `GB-01-01-SUMMARY.md` in the phase directory.
