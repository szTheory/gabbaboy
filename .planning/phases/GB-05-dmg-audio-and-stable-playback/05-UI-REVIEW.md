# Phase 5 — UI Review

**Audited:** 2026-10-09
**Baseline:** Abstract 6-pillar standards; no `UI-SPEC.md` found.
**Screenshots:** Not captured. The CLI reached `localhost:8080`, which is a Traefik dashboard rather than the native SDL app; all three Playwright captures failed. The actual native window and F1 dialog were not visually inspected.
**Interaction captures:** off (workflow.ui_interaction_capture is false)

**Follow-up (2026-10-09):** The F1 failed-transition retry finding below was corrected after this audit: help now distinguishes `S` for manual/background-save retry from `R` to retry a blocked reset, replacement, or quit, with `C` to continue without saving and Escape to cancel. The incremental source review found no issue with the mapping, and the current player/package verifier passed 50/50 including built-help assertions. Treat the finding and score rows below as the audit snapshot before this correction; the other recommendations remain open. No native-window screenshot or physical/perceptual result was produced.

This re-audit covers the current integrated player source after `de96686`, the built player's `--help` output, its F1/title/status code paths, and the consumer documentation. Phase summaries establish automated state and package coverage, not native-window appearance or perceptual audio quality.

## Pillar Scores

| Pillar | Score | Key Finding |
|--------|-------|-------------|
| 1. Copywriting | 3/4 | Keyboard and gamepad mappings are discoverable, but F1 incorrectly says S retries a failed save; the transition prompt requires R. |
| 2. Visuals | 2/4 | The game viewport is centered and unobstructed, but pause, gain, audio availability, and errors remain in the native title bar. |
| 3. Color | 3/4 | The shell uses one dark surround and gameplay pixels dominate; actual contrast and color distribution were not captured. |
| 4. Typography | 2/4 | F1 is a long unsectioned native message box whose wrapping and hierarchy are unverified. |
| 5. Spacing | 3/4 | The viewport has a consistent integer-scale geometry, while native help and title spacing are delegated to the OS. |
| 6. Experience Design | 2/4 | Focus, audio, and save recovery paths are explicit, but the F1 retry instruction is incorrect and key state feedback is title-only. |

**Overall: 15/24**

## Top 3 Priority Fixes

1. **Correct the F1 save retry instruction** — users following it during a failed final save press S, which is ignored while a transition is pending — change `Save now / retry: S` to distinguish normal save (`S`) from failed-transition retry (`R`), matching the preview guide and key handler.
2. **Add a compact in-window state indicator** — users can miss pause, current gain, audio sink failure, and recovery status in the OS title bar — render a restrained status/gain strip or transient overlay while preserving the 160×144 game image.
3. **Restructure and visually verify F1 help** — the single long message makes controls, recovery, model limits, and diagnostics hard to scan and may wrap poorly — use labeled sections and validate the native dialog on supported macOS display scales.

## Detailed Findings

### Pillar 1: Copywriting (3/4)

- **WARNING — F1 gives the wrong recovery key.** It says `Save now / retry: S` (`src/player/main.c:711`). While a final save transition is pending, the handler accepts only Escape, R, or C; S is ignored (`src/player/main.c:1206-1231`). The preview guide correctly says R retries and S is for an ordinary manual save (`docs/preview.md:52-56`). Align F1 with that distinction.
- Positive evidence: the current player CLI help and F1 list keyboard, gamepad, pause, volume, reset, and help controls (`src/player/main.c:368-387`, `697-720`). The gamepad mapping is also in the preview table (`docs/preview.md:40-54`).
- Audio copy carefully distinguishes the scoped DMG-CPU-B software model, unavailable sink behavior, application underflow, and hardware/perceptual limits (`src/player/main.c:377-384`).

### Pillar 2: Visuals (2/4)

- **WARNING — state feedback is outside the game surface.** Run/pause, gain, save/status, and audio-ready state are assembled only into the window title (`src/player/main.c:670-694`). The render path clears a dark surround and renders the game texture, without an in-window status/control layer (`src/player/main.c:787-795`). Keep the gameplay image as the focal point, but provide a visible status/gain cue within the app surface.
- Positive evidence: the presentation layout centers the image, preserves its aspect ratio, and uses the largest integer scale that fits (`src/player/presentation.c:5-23`). The prior audit's gamepad-discovery and persistent-gain source changes are present in the current F1/preview and title code.
- **Visual conclusions are code-derived.** No capture of the actual SDL app or F1 dialog was available, so window balance, legibility, dialog wrapping, and native file-dialog appearance remain unverified.

### Pillar 3: Color (3/4)

- The only player-shell color explicitly assigned is the dark clear color RGB `(8, 24, 32)` around game pixels (`src/player/main.c:787-795`). No accent palette or status colors are defined; primary colors therefore do not appear overused in the shell code.
- **WARNING — contrast and 60/30/10 distribution cannot be verified.** The game image supplies most color, while status states are text in native title chrome. No native screenshot was captured. If status moves in-window, retain text labels and check contrast rather than using color as the sole signal.

### Pillar 4: Typography (2/4)

- **WARNING — F1 help has weak scan hierarchy.** One `SDL_ShowSimpleMessageBox` string combines current ROM, controls, audio behavior, evidence limits, save recovery, status, and general limitations (`src/player/main.c:703-729`). It has paragraph breaks but no labeled sections. The long paragraph layout and inherited native font sizes cannot be checked without a capture.
- The player relies on OS title and message-box typography rather than defining a type scale. A 2048-byte message buffer bounds the content, but does not guarantee readable wrapping across supported display scales (`src/player/main.c:703-729`).

### Pillar 5: Spacing (3/4)

- The game image uses a consistent geometry rule: preserve 160×144 pixels, choose the largest integer scale that fits, and center it (`src/player/presentation.c:5-23`).
- **WARNING — help and status spacing are uncontrolled by the app.** The help uses the OS simple message box, and status uses the title bar (`src/player/main.c:670-729`). Their padding, wrapping, and clipping were not visually inspected. The code has no arbitrary CSS/Tailwind spacing because this is a native SDL UI.

### Pillar 6: Experience Design (2/4)

- **WARNING — failed-save retry guidance can strand a transition.** F1 directs users to press S to retry, but pending transitions ignore S; R is the only retry key (`src/player/main.c:711`, `1206-1231`). Correcting this is needed for the advertised recovery flow.
- **WARNING — important feedback is title-only.** Current gain is preserved in the title, and `set_status` updates transient status there; pause, focus loss/gain, device recovery, input errors, and save state do not appear in the viewport (`src/player/main.c:670-695`, `1247-1260`, `1363-1400`).
- Positive evidence: the player has explicit pause cleanup, focus-release recovery, gamepad source ownership, audio device recovery, and save retry/continue/cancel paths (`src/player/main.c:1213-1228`, `1363-1400`; `src/player/input.c:226-248`, `323-348`). Phase 5 summaries report automated coverage for these flows, but no live interaction state was captured because capture was off.

## Files Audited

- `AGENTS.md`, `.planning/STATE.md`, `.planning/PROJECT.md`, `.planning/research/SUMMARY.md`
- `.planning/phases/GB-05-dmg-audio-and-stable-playback/05-CONTEXT.md`
- `.planning/phases/GB-05-dmg-audio-and-stable-playback/05-01-PLAN.md` through `05-07-PLAN.md`
- `.planning/phases/GB-05-dmg-audio-and-stable-playback/05-01-SUMMARY.md` through `05-07-SUMMARY.md`
- `src/player/main.c`, `src/player/presentation.c`, `src/player/presentation.h`, `src/player/input.c`, `src/player/input.h`, `src/player/audio.c`, `src/player/audio.h`
- `docs/preview.md`, `docs/audio-and-playback.md`, `src/player/limitations.h`
- Built player `--help` output from `build/phase3-player/gabbaboy/gabbaboy-player`
