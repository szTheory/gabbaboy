# Phase 3: Visible Interactive DMG - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in `03-CONTEXT.md`; this log preserves the alternatives considered.

**Date:** 2026-10-07
**Phase:** 3-Visible Interactive DMG
**Areas discussed:** interactive fixture and legal evidence; PPU/DMA correctness; API and joypad timing; macOS player UX; dependencies, CI, and claim boundaries

---

## Interactive fixture and legal evidence

| Option | Description | Selected |
|--------|-------------|----------|
| One demo ROM doubles as all rendering/timing evidence | Fastest path, but a playable result or screenshot can hide raster, bus, or fixture-applicability errors. | |
| Original demo plus separate focused test oracles | A small owned bootless ROM demonstrates interaction; authored composition images and timing/DMA cases establish their own behavior. Its bytes and applicability remain reproducible and reviewable. | ✓ |
| Make an upstream ROM suite the product demo | Could provide richer gameplay, but introduces rights, boot/model applicability, maintenance, and unrelated test-scope risks. | |

**User's choice:** The user locked the recommendation package: one original, project-owned 32 KiB ROM-only DMG-CPU-B demo, with reproducibility and applicability evidence, and separate rendering/timing/gameplay checks.

**Notes:** The fixture specialist and adversarial pass emphasized that matching bytes, a valid suite license, or a successful game path does not independently prove model applicability. The recommendation reuses the already pinned RGBDS fixture-generation route rather than adding an assembler dependency. Pan Docs rendering and DMA references informed separate composition/timing/access cases: [Rendering](https://eldred.fr/pandocs/Rendering.html), [OAM DMA](https://eldred.fr/pandocs/OAM_DMA_Transfer.html), and [VRAM/OAM access](https://eldred.fr/pandocs/Accessing_VRAM_and_OAM.html).

## PPU, DMA, and output boundary

| Option | Description | Selected |
|--------|-------------|----------|
| Render a whole scanline/frame as a single operation | Simple output path, but cannot establish dot-sensitive fetch stalls, STAT timing, or contention. | |
| Dot-driven PPU with separate oracles and copied completed frames | Keep internal timing dot-based; test expected pixels independently from raster/access behavior; copy a 160×144 shade-index image into caller-owned memory. | ✓ |
| Expose an internal framebuffer pointer | Avoids a copy, but creates lifetime/ownership coupling and can expose partially rendered internal state. | |

**User's choice:** Lock the dot-driven model, separate image/timing/contention evidence, and caller-owned completed-frame output with explicit pitch/format.

**Notes:** Pan Docs describes variable mode-3 behavior tied to scroll/window/object fetches, so a screenshot cannot serve as timing evidence. The model remains DMG-CPU-B; no physical-hardware qualification is claimed unless hardware evidence is actually obtained.

## Joypad API and deterministic input

| Option | Description | Selected |
|--------|-------------|----------|
| Poll a keyboard snapshot and infer button state | Straightforward, but short press/release pairs can happen between snapshots and timestamps are lost. | |
| Timestamp button-down/up transitions through the existing bounded queue | Preserves deterministic order and emulated-time behavior for both public API and SDL adapter; requires explicit overflow and equal-time rules. | ✓ |
| Let SDL own joypad/interrupt behavior | Smaller core change, but splits guest semantics from headless tests and makes event replay host-dependent. | |

**User's choice:** Extend the existing fixed-capacity event boundary for button transitions; the core owns active-low JOYP selection/interrupts, while SDL translates physical scancodes and event times. Source-qualify the exact interrupt edge before implementation.

**Notes:** SDL documents the repeat flag and timestamp on keyboard events, while its keyboard-state API is a snapshot; focus-loss handling must release held keys. The API tests and SDL path must use the same core boundary. References: [SDL keyboard events](https://wiki.libsdl.org/SDL3/SDL_KeyboardEvent), [keyboard state](https://wiki.libsdl.org/SDL3/SDL_GetKeyboardState), and [Pan Docs joypad input](https://eldred.fr/pandocs/Joypad_Input.html).

## macOS player and usability

| Option | Description | Selected |
|--------|-------------|----------|
| Empty window that requires a ROM before showing anything | Direct file-open model, but weak first-run experience for a preview whose goal is to demonstrate a legal playable fixture. | |
| Start with the owned demo and offer Open ROM | Gives an immediate playable path while preserving user choice and the required supported-ROM open flow. Failed replacement keeps the current session. | ✓ |
| Native Swift/AppKit wrapper | Could offer deeper native menus/dialog behavior, but introduces another language/runtime boundary and lifecycle without a Phase 3 need. | |

| Option | Description | Selected |
|--------|-------------|----------|
| Fractional stretch or crop to fill | Maximizes window fill, but distorts or removes pixels from the 160×144 image. | |
| Integer nearest-neighbor scale with letterboxing | Preserves the 10:9 image and crisp pixels; uses a minimum size and high-DPI drawable dimensions. | ✓ |

**User's choice:** Use one optional SDL3 window, original demo ready at launch, discoverable Open/Pause/Reset/Quit actions, clear keyboard map, actionable errors, integer scaling/letterboxing, and visible audio/persistence limitations.

**Notes:** Keep standard Command-O/Command-Q behavior. Handle SDL's asynchronous file-dialog result on the UI/main thread and always validate the selected file through the core loader because platform filters may be ignored. Apple HIG shortcut and macOS window guidance informed this choice: [Designing for macOS](https://developer.apple.com/design/human-interface-guidelines/designing-for-macos/) and [Keyboards](https://developer.apple.com/design/human-interface-guidelines/keyboards/). SDL references: [logical presentation](https://wiki.libsdl.org/SDL3/SDL_SetRenderLogicalPresentation), [high DPI](https://wiki.libsdl.org/SDL3/README-highdpi), and [file dialog](https://wiki.libsdl.org/SDL3/SDL_ShowOpenFileDialog).

## Dependencies, CI, and delivery claims

| Option | Description | Selected |
|--------|-------------|----------|
| Add a native wrapper, UI framework, or font library | May reduce some UI implementation work but expands the dependency/build surface for a small preview. | |
| SDL3 as the sole player dependency; opt-in build; exact-revision run-scoped preview | Keeps core/headless builds independent and gives macOS users a verifiable preview without implying a release. No network fetch in ordinary tests. | ✓ |
| Sign/notarize and distribute as a public release in this phase | Better end-user installation, but requires release identity, credentials, policy, and artifact verification outside the Phase 3 goal. | |

**User's choice:** Follow the minimal-dependency recommendation: SDL3 is justified by the player; add no second UI dependency. Keep the core offline and SDL-free; any preview artifact is run-scoped and tied to its source digest, with notices. Do not claim signing/notarization or public release status.

**Notes:** The delivery specialist separated build/package smoke from visual usability evidence and signing from preview artifacts. Official sources: [SDL3 CMake](https://wiki.libsdl.org/SDL3/README-cmake), [GitHub Actions artifacts](https://docs.github.com/en/actions/concepts/workflows-and-actions/workflow-artifacts), and [Apple notarization](https://developer.apple.com/documentation/security/notarizing-macos-software-before-distribution).

## Cross-specialty synthesis and adversarial findings

The fan-out covered emulator hardware and timing, original-fixture/legal evidence, core/API and deterministic input, macOS UI/accessibility, dependency and CI delivery, QA, and a separate adversarial assumptions pass. The recurring failure modes were: treating a plausible screenshot as PPU timing proof; conflating a playable fixture with hardware qualification; assuming a test ROM is applicable because it passes; polling snapshots and missing short key transitions; leaving guest buttons stuck after focus loss; exposing a borrowed framebuffer with unclear lifetime; fractional image scaling; trusting file-dialog filters; and adding UI/build dependencies whose cost exceeds their value.

The selected package addresses those risks while preserving the current profile and explicit evidence limits. The exact JOYP edge source, SDL3 patch/minimum version, fixture mechanics, and automated macOS package smoke details remain research/planning decisions, constrained by the selected contract.

## the agent's Discretion

- Internal PPU/DMA architecture and test organization within the bounded, instance-owned C17 core.
- Exact original fixture gameplay, provided it is small, reproducible, legally owned, interactive, and has an unambiguous scripted outcome.
- SDL3 patch pin, CMake discovery, window/event-loop organization, small text drawing method, and preview artifact retention.
- Any upstream test admission, but only after an explicit gap, rights, exact bytes, DMG-CPU-B/boot applicability, and protocol are reviewed.

## Deferred Ideas

- CGB/boot-ROM support, additional mappers, audio, battery persistence, and public signed distribution remain later phases.
- Physical-controller support remains in the later host-input scope.
- No third-party ROM corpus is added by default; revisit only to close a named Phase 3 evidence gap.
