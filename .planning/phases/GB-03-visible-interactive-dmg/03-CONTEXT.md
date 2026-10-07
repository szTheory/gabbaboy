# Phase 3: Visible Interactive DMG - Context

**Gathered:** 2026-10-07
**Status:** Ready for planning

<domain>
## Phase Boundary

Deliver the limited DMG preview in which a macOS user can play a legal, interactive 32 KiB ROM-only Game Boy fixture with deterministic input and evidenced DMG video behavior. Implement VIDEO-01 through VIDEO-05: background/window/sprite composition and dot-sensitive timing, model-specific OAM DMA and display access restrictions, timestamped joypad input through the public API and SDL keyboard adapter, an optional macOS player with actionable ROM loading and controls, and automated evidence that keeps image composition, raster timing, and scripted gameplay distinct.

This phase extends the declared bootless DMG-CPU-B core and preserves its bounded C17 API and headless use. It does not add CGB execution, boot-ROM behavior, other cartridge mappers, battery persistence, audio, physical-controller support, general-purpose UI frameworks, or a signed/notarized public release. The preview must clearly disclose that audio and persistence are not implemented.

</domain>

<decisions>
## Implementation Decisions

### Fixture, scope, and evidence
- **D-01:** Use one small, original, project-owned, bootless 32 KiB ROM-only interactive fixture as the immediately playable demo. It must respond to controls and produce a deterministic visible outcome through a short scripted path. Include its readable source, rights notice, exact checked-in bytes, digest, build recipe, DMG-CPU-B/bootless applicability, and pass protocol. Reuse the already pinned RGBDS 1.0.1 fixture-generation path where practical; do not add an assembler dependency just for this fixture.
- **D-02:** Keep the playable demo separate from the hardware-behavior test oracles. Test frame composition with authored expected images; test raster/mode/STAT/fetch behavior with focused timing cases; test OAM DMA, VRAM/OAM restrictions, and CPU/PPU/DMA contention with separate model-applicable cases; and test joypad-driven gameplay through deterministic scripted inputs. A demo pass or plausible screenshot alone does not establish timing correctness.
- **D-03:** Prefer owned, source-reviewed tests. Add a third-party ROM only to close a named evidence gap and only after its immutable source, redistribution rights, digest, model/boot applicability, and protocol are documented. Keep unknown or inapplicable tests out of the eligible denominator. Preserve the Phase 2 lesson that exact fixture bytes and source identity do not by themselves prove fixture applicability.

### PPU, DMA, and public output
- **D-04:** Advance the PPU on the emulated dot timeline. Model the declared DMG background, window, sprites, LCD/STAT transitions, variable fetch behavior, VRAM/OAM access restrictions, and OAM DMA contention from model-qualified evidence. Keep image-composition assertions separate from dot-sensitive timing and access assertions. Pan Docs describes mode-3 duration varying with scrolling, windows, and objects; line-at-once output is not sufficient timing evidence.
- **D-05:** Expose completed video frames as a bounded copy into caller-owned storage: 160×144 pixels, explicit pitch and documented 2-bit DMG shade-index values. Keep SDL, host RGB conversion, and presentation policy in the adapter. Internal PPU progression remains dot-based; copying a completed frame is an output boundary, not a frame-at-a-time execution shortcut.
- **D-06:** Qualify every PPU/DMA assertion to the declared DMG-CPU-B profile and its sources. Use focused controls for composition, timing, and contention so a single passing fixture cannot mask an inapplicable oracle or an inaccurate timing path. Do not claim physical-hardware qualification without physical-hardware evidence.

### Input and deterministic core boundary
- **D-07:** Extend the existing fixed-capacity timestamped event boundary with joypad button press and release transitions. Preserve bounded atomic admission, stable caller ordering for equal timestamps, explicit queue-full behavior, and deterministic behavior across run partitions. The core owns active-low JOYP row selection and interrupt behavior; both the public API tests and SDL adapter must exercise this same boundary.
- **D-08:** Before encoding the exact JOYP interrupt edge/selection interaction, planning/research must record the primary model-applicable source and focused expected cases. Do not infer the electrical edge solely from SDL behavior or from a game fixture. The host adapter translates SDL scancodes and monotonic event timestamps to the emulated half-dot timeline; host clock access remains outside the core.
- **D-09:** Ignore host key-repeat events. On focus loss, pause and enqueue releases for held buttons so the guest cannot retain stuck input. Reset clears pending input/video generation state according to a documented API rule; same-timestamp ordering, event overflow, and reset behavior receive direct tests.

### Player UX, dependencies, and delivery
- **D-10:** Keep the macOS player optional and keep the portable C17 core, public API, and ordinary headless tests SDL-free. SDL3 is the one justified player dependency. Use built-in SDL rendering/dialog facilities and a small project-owned control/status treatment if text is needed; do not add SDL_ttf, ImGui, a Swift/AppKit wrapper, a generic UI framework, or network-fetched build dependencies in this phase.
- **D-11:** Start the preview with the original demo ready to play and provide a discoverable Open ROM action. Use standard macOS Open/Quit shortcuts (Command-O/Command-Q), map arrows to the D-pad, Z/X to A/B, Return to Start, and Right Shift to Select; provide clear Pause and Reset actions and show the key map in the player. Preserve the active session after a failed ROM replacement and show an actionable error. Always validate the selected file through the existing bounded loader; dialog filters are only hints.
- **D-12:** Preserve the DMG image's 10:9 aspect ratio with nearest-neighbor integer scaling and letterboxing. Set an initial/minimum window size that avoids shrinking below native size, and calculate presentation using drawable pixels on high-DPI displays. Use SDL3 logical presentation with integer scaling when supported by the pinned SDL version; do not stretch, crop, or use fractional scaling to fill the window.
- **D-13:** Make the preview visibly state that audio and battery persistence are not implemented. Keep controls, pause/focus state, and current ROM status legible without adding a general-purpose UI dependency. Treat accessibility and keyboard discoverability as product behavior, not only README documentation.
- **D-14:** Add an opt-in macOS player build and exact-revision package/build smoke to CI using an explicit SDL3 version. The ordinary core build stays offline and SDL-free. If a run-scoped preview artifact is produced, bind it to the source revision, include SDL license notices and digests, and qualify the downloaded package bytes. It is a preview artifact, not a signed/notarized public release; make no signing, notarization, or hardware claim without corresponding evidence.

### the agent's Discretion
- Choose internal PPU/DMA data structures, test decomposition, and the smallest implementation organization that preserves portable C17, explicit instance ownership, bounded public operations, deterministic time, and the decisions above.
- Choose concrete owned fixture mechanics and artwork so long as they remain original, small, reproducible, interactive, and suitable for composition and scripted gameplay evidence.
- Select the exact SDL3 patch release, CMake discovery details, artifact retention, and UI drawing approach during research/planning, subject to D-10 and D-14.
- Add a focused upstream oracle only under D-03; no upstream case is presumed eligible by name alone.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Product scope and phase requirements
- `.planning/PROJECT.md` — Game Boy/Game Boy Color identity, limited DMG milestone, project value, and non-goals.
- `.planning/REQUIREMENTS.md` — VIDEO-01 through VIDEO-05; exact acceptance and traceability requirements.
- `.planning/ROADMAP.md` §Phase 3 — phase goal, success criteria, dependencies, and explicit boundaries with Phases 4–6.
- `.planning/context/BRIEF.md` — owner goals and constraints.
- `.planning/context/DECISIONS.md` — adopted architecture, model/evidence claims, validation, delivery, and dependency principles.
- `.planning/context/WORKFLOW.md` — workflow and evidence conventions.

### Project research and prior phase contracts
- `.planning/research/INDEX.md` — research navigation and topic ownership.
- `.planning/research/SUMMARY.md` — synthesized project research and roadmap context.
- `.planning/research/ARCHITECTURE.md` — portable core and host-adapter boundary.
- `.planning/research/HARDWARE-AND-VALIDATION.md` — model applicability, bootless profile, and evidence classes.
- `.planning/research/PITFALLS.md` — emulator correctness and validation failure modes.
- `.planning/research/STACK.md` — C17/CMake stack and dependency constraints.
- `.planning/research/QUALITY-AND-DELIVERY.md` — CI, artifact, and claim qualification practices.
- `.planning/phases/GB-01-portable-foundation-and-original-rom-tracer/01-CONTEXT.md` — public bounded API, ownership, fixture, and dependency contract.
- `.planning/phases/GB-01-portable-foundation-and-original-rom-tracer/01-RESEARCH.md` and `01-VALIDATION.md` — original fixture patterns and prior evidence limits.
- `.planning/phases/GB-02-dmg-cpu-bus-and-time/02-CONTEXT.md` — current DMG-CPU-B, deterministic timeline, event queue, and Phase 3 boundary.
- `.planning/phases/GB-02-dmg-cpu-bus-and-time/02-RESEARCH.md` — source qualification and fixture practices carried forward.
- `.planning/phases/GB-02-dmg-cpu-bus-and-time/02-VALIDATION.md`, `02-VERIFICATION.md`, and `02-SECURITY.md` — exact Phase 2 evidence, limitations, and closed fixture-threat audit; do not generalize its headless corpus to PPU applicability.

### Current implementation and fixture surfaces
- `include/gabbaboy/gabbaboy.h` — opaque instance API, bounded run/event contracts, profile, and existing public types.
- `src/core/gabbaboy.c` — instance-owned CPU/bus and current half-dot/event behavior to extend.
- `CMakeLists.txt`, `tests/CMakeLists.txt`, and `tests/expected-tests.txt` — core-only build and fail-closed test inventory patterns.
- `tests/test_api.c`, `tests/test_events.c`, `tests/test_bus.c`, `tests/test_runner.c`, and `tests/test_tracer.c` — public API, timestamped event, bus, headless runner, and guest fixture patterns.
- `fixtures/tracer/tracer.asm`, `fixtures/tracer/manifest.json`, and `fixtures/tracer/LICENSE.txt` — original source, provenance, reproducibility, and rights-notice precedent.
- `.github/workflows/ci.yml`, `.github/workflows/fixture-repro.yml`, and `.github/workflows/preview.yml` — current offline/hosted checks, pinned fixture reproduction, and run-scoped artifact patterns.

### Primary external technical references
- [Pan Docs: Rendering](https://eldred.fr/pandocs/Rendering.html) — visible lines, mode timing, pixel fetching, and variable stalls.
- [Pan Docs: OAM DMA Transfer](https://eldred.fr/pandocs/OAM_DMA_Transfer.html) — DMG DMA duration and CPU access constraints.
- [Pan Docs: Accessing VRAM and OAM](https://eldred.fr/pandocs/Accessing_VRAM_and_OAM.html) — mode-dependent memory restrictions and conflicts.
- [Pan Docs: Joypad Input](https://eldred.fr/pandocs/Joypad_Input.html) — active-low matrix and row selection; use another primary source for any finer interrupt-edge detail not established here.
- [SDL3: SDL_SetRenderLogicalPresentation](https://wiki.libsdl.org/SDL3/SDL_SetRenderLogicalPresentation) and [SDL3 high-DPI guidance](https://wiki.libsdl.org/SDL3/README-highdpi) — logical resolution, integer scaling, and drawable-pixel behavior.
- [SDL3: SDL_KeyboardEvent](https://wiki.libsdl.org/SDL3/SDL_KeyboardEvent), [SDL_GetKeyboardState](https://wiki.libsdl.org/SDL3/SDL_GetKeyboardState), and [SDL_ShowOpenFileDialog](https://wiki.libsdl.org/SDL3/SDL_ShowOpenFileDialog) — event timestamps/repeat, snapshot limitations, and asynchronous file-dialog behavior.
- [SDL3 CMake guidance](https://wiki.libsdl.org/SDL3/README-cmake) — optional package discovery and build integration.
- [Apple Human Interface Guidelines: Designing for macOS](https://developer.apple.com/design/human-interface-guidelines/designing-for-macos/), [Keyboards](https://developer.apple.com/design/human-interface-guidelines/keyboards/), and [Writing](https://developer.apple.com/design/human-interface-guidelines/writing/) — window, shortcut, and actionable-message conventions.
- [GitHub Actions workflow artifacts](https://docs.github.com/en/actions/concepts/workflows-and-actions/workflow-artifacts) and [Apple notarization](https://developer.apple.com/documentation/security/notarizing-macos-software-before-distribution) — run-scoped preview evidence and the distinction between preview artifacts and notarized distribution.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- The core already owns each `gbb_instance`, keeps host facilities out of `src/core`, and has bounded caller-owned run output and a fixed-capacity timestamped event queue. Extend those contracts rather than creating a parallel PPU or input framework.
- The current queue admits STOP_WAKE and SERIAL_EDGE events with atomic capacity checks and stable caller order at equal timestamps. Joypad events should follow the same admission and deterministic-time discipline.
- The ROM loader currently accepts exact-size 32 KiB ROM-only images and leaves the active machine intact when replacement input fails. Preserve that non-destructive behavior in the player.
- The fixture-reproduction workflow already pins RGBDS 1.0.1 for the original tracer, while routine tests use checked-in bytes and run offline.
- `preview.yml` already demonstrates run-scoped Linux/macOS artifacts; extend its evidence discipline for the optional player rather than describing a CI artifact as a release.

### Established Patterns
- Portable C17, explicit per-instance ownership, no hidden globals, host I/O in adapters, bounded work, and clear unsupported/error results are existing core constraints.
- Fixture bytes, source/provenance, rights notices, model/boot applicability, and expected protocol are recorded and digest-checked. The Phase 2 three-case headless reporting corpus is not a PPU oracle.
- Core-only CMake and C/C++ consumers do not require SDL. The player must remain opt-in and must not leak SDL into the core package.
- Existing verification distinguishes authored tests, upstream-derived fixtures, model-specific evidence, and unqualified hardware behavior. Continue those distinctions.

### Integration Points
- Extend core bus/device progression with PPU registers, dot-level rendering, LCD/STAT state, OAM DMA, and access arbitration on the existing half-dot timeline.
- Add a bounded completed-frame output and timestamped button transitions to the public API, with API/consumer tests that exercise deterministic partitioning and ownership.
- Implement the SDL adapter as a separate optional target: map keyboard/file/window events into the core API, render copied shade-index frames, and keep dialogs/errors/status on the host side.
- Extend test inventories, owned fixture manifests, fixture reproduction, macOS CI, docs, preview limitations, and installed-package smoke together so claims match the exact deliverable.

</code_context>

<specifics>
## Specific Ideas

- First run opens the original demo ready to play. Suggested keys: arrows for D-pad; Z/X for A/B; Return for Start; Right Shift for Select; Space for Pause; R for Reset; Command-O to open and Command-Q to quit.
- Show native-size pixels at 10:9 with integer enlargement and letterboxing; provide actionable ROM errors and keep the prior loaded game intact after a failed replacement.
- Keep the user-visible notice that audio and battery persistence are not implemented.
- Track rendering composition, raster timing, DMA/access contention, and interactive gameplay as separate evidence outputs.
- Keep fixture source, exact bytes, reproducibility, license, and profile applicability reviewable without adding a dependency for routine builds.
</specifics>

<deferred>
## Deferred Ideas

- CGB execution, boot-ROM support, broader cartridge mappers, and hardware-family claims remain outside the limited DMG phase.
- Audio and battery persistence belong to later phases; the visible preview must label their absence.
- Physical controllers and broader focus/device lifecycle policy belong to the later host-input phase; this phase covers the SDL keyboard path and stuck-key prevention on focus loss.
- Signed/notarized public distribution, stable release support floors, and consumer/release certification remain Phase 6.
- Third-party ROM suites remain deferred unless a specific gap and complete rights/applicability review justify adding one.

</deferred>

---

*Phase: 3-Visible Interactive DMG*
*Context gathered: 2026-10-07*
