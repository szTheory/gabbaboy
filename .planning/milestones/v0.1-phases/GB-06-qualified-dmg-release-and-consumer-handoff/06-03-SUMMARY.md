---
phase: GB-06-qualified-dmg-release-and-consumer-handoff
plan: 03
subsystem: package-adoption
tags: [C17, CMake, relocated-package, battery-saves, DMG]
requires:
  - phase: GB-06-01
    provides: Relocatable GabbaBoy::core package and legally licensed installed fixtures.
  - phase: GB-06-02
    provides: Bounded half-dot execution, timestamped input, frame/audio output, and explicit battery API.
  - phase: GB-06-04
    provides: Versioned support-ledger and source-bound release-sidecar contract.
provides:
  - Runnable relocated C consumer covering bounded stepping, timestamped input, caller-owned frame/audio, and host battery continuation.
  - Adopter documentation for API ownership, support limits, upgrade, troubleshooting, and the Playstead boundary.
affects: [release-package, native-consumers, Playstead-adoption]
actuals:
  tokens: 6171
  tasks: 2
  commits: 4
tech-stack:
  added: []
  patterns: [Relocated CMake consumer using only GabbaBoy::core, Host-owned bounded save I/O with exclusive temporary file and atomic replacement]
key-files:
  created: [examples/relocated-c/CMakeLists.txt, examples/relocated-c/main.c, docs/native-integration.md]
  modified: [CMakeLists.txt, cmake/PreviewPackageSmoke.cmake, README.md, docs/preview.md, docs/cartridge-and-saves.md]
key-decisions:
  - "Use one opaque instance, load the visible legal fixture for frame/audio output, then load the MBC1 continuation fixture for raw battery import/export."
  - "Install the existing visible-demo ROM with its manifest and license because the package previously omitted a fixture capable of producing a completed frame."
  - "Use a PID-suffixed exclusive sibling temporary file and atomic replacement so a failed example write preserves the prior complete save."
patterns-established:
  - "Native package examples configure against the relocated prefix and exercise only the installed public target, headers, and fixtures."
  - "Core battery APIs transfer raw bytes; filesystem path, bounded reads, recovery, and replacement belong to the host."
requirements-completed: [SHIP-01, SHIP-04]
coverage:
  - id: D1
    description: "An external C17 consumer builds from the relocated package and demonstrates bounded execution, timestamped input, frame/audio buffers, and fresh/resumed battery continuation."
    requirement: SHIP-01
    verification:
      - kind: integration
        ref: "ctest --preset phase1 --output-on-failure --no-tests=error -R '^preview_package_smoke$' (pass; package example runs twice from the extracted prefix)"
    human_judgment: false
  - id: D2
    description: "Adopter docs match the public API and link to the versioned support ledger, exact-source sidecar contract, and current Playstead boundary."
    requirement: SHIP-04
    verification:
      - kind: other
        ref: "Local Markdown link check and example public API declaration check (pass)"
      - kind: integration
        ref: "Relocated package smoke after documentation updates (pass)"
    human_judgment: false
duration: 6 min
completed: 2026-10-08
status: complete
plan_head_before: ee730be93f412f2617db7a061c355698bcd20a2c
plan_head_after: 8e6735c4dece426de1ab93202701e04e691f64a8
---

# Phase 6 Plan 3: Relocated Native C Consumer Summary

**A relocated C17 example now exercises bounded DMG stepping, timestamped input, caller-owned video/audio buffers, and repeatable host battery continuation against the installed core package.**

## Performance

- **Duration:** 6 min
- **Started:** 2026-10-08T23:24:36Z
- **Completed:** 2026-10-08T23:31:10Z
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments

- Added a standalone `find_package(GabbaBoy CONFIG REQUIRED)` C17 example that uses the public installed target only and a bounded 2 MiB ROM read.
- The example queues timestamped A press/release events, runs within a 200,000 half-dot budget, copies a completed 160x144 frame and emits 48 kHz stereo into caller-owned arrays.
- The same instance loads the MBC1 continuation fixture, imports exact-size host battery bytes when present, verifies fresh/resumed guest markers, and exports through a flushed exclusive temporary file followed by atomic replacement.
- Extended the package smoke to require the visible-demo ROM, manifest, and license, then configure/build/run the external example twice from the extracted prefix and unrelated working directory.
- Added the native integration guide and linked it from the README, preview guide, and cartridge/save contract. Docs state the current model and mapper limits, sidecar identity, upgrade path, troubleshooting, and that Playstead remains GBA/mGBA-only with no live GabbaBoy integration.

## Task Commits

1. **Task 1: Run a relocated native C example** - `04acbab` (feat)
2. **Task 1 correction: Reuse one instance across packaged fixtures** - `cda6387` (fix)
3. **Task 1 correction: Preserve single-instance execution** - `3dfb7b1` (fix)
4. **Task 2: Publish adopter and Playstead seam guide** - `8e6735c` (docs)

Plan metadata will be committed after state/roadmap bookkeeping.

## Files Created/Modified

- `examples/relocated-c/CMakeLists.txt` - Finds the installed package and validates the two installed fixture inputs.
- `examples/relocated-c/main.c` - Runs the visible and continuation fixture paths with explicit host-owned buffers and file persistence.
- `cmake/PreviewPackageSmoke.cmake` - Checks installed fixture assets and builds/runs the relocated example twice.
- `CMakeLists.txt` - Installs the visible-demo ROM and its manifest/license alongside existing fixtures.
- `docs/native-integration.md` - Documents the relocated invocation, ownership, time/input/output, persistence, support, upgrade, and troubleshooting.
- `README.md`, `docs/preview.md`, `docs/cartridge-and-saves.md` - Link to the example and keep public package/save claims aligned.

## Decisions Made

- The visible fixture supplies successful frame output; the MBC1 continuation fixture supplies meaningful save import/export. The example reuses one instance sequentially to satisfy both needs.
- The installed package includes the existing visible fixture's manifest and license so consumers can use it without source-tree access.
- The example keeps persistence host-owned and raw. It does not present the raw core buffer as the SDL player's checksummed save envelope.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Install the legal visible fixture for completed-frame output**
- **Found during:** Task 1
- **Issue:** The installed package contained the tracer and MBC1 continuation fixtures but not the visible demo; both packaged fixtures are headless and could not produce the successful caller-owned frame required by this plan.
- **Fix:** Installed `fixtures/visible-demo/demo.gb` with its manifest and MIT license, and made the package smoke require those files.
- **Files modified:** `CMakeLists.txt`, `cmake/PreviewPackageSmoke.cmake`
- **Verification:** Relocated package configure/build and two successful example runs via `preview_package_smoke`.
- **Committed in:** `04acbab`

**Total deviations:** 1 auto-fixed (Rule 2). **Impact:** Required package data was added without a dependency or a wider package redesign.

## Issues Encountered

- Initial package smoke confirmed the missing visible fixture; after installing it, the package smoke passed on the available macOS host.
- The available environment did not provide a matching Clang libFuzzer runtime; the configure reported that deterministic sanitizer regressions remain enabled. This plan did not add or run fuzzing.

## User Setup Required

None - no external service configuration is needed.

## Next Phase Readiness

- Plan 06-03 is complete. Plans 06-06 and 06-07 remain; hosted exact-source checks and release publication are not performed here.
- No release was published. The example establishes software-path behavior only; it does not qualify physical DMG behavior, perceptual output, broader compatibility, or a live Playstead adapter.

---
*Phase: GB-06-qualified-dmg-release-and-consumer-handoff*
*Completed: 2026-10-08*

## Self-Check: PASSED

Summary file exists, all four task commits are ancestors of the current HEAD, and `git diff --check` reports no whitespace errors.
