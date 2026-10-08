# Phase 5 — UI Review

**Audited:** 2026-10-08  
**Baseline:** Abstract 6-pillar standards; no `UI-SPEC.md` found.  
**Screenshots:** Not captured. `localhost:8080` redirected to the Traefik dashboard; all three Playwright CLI captures failed. No rendered SDL player capture was available. Visual and perceptual conclusions below are code-derived and unverified.  
**Interaction captures:** off (workflow.ui_interaction_capture is false)

The phase implements a native SDL3 Game Boy player, not a web UI. The review compares the keyboard help, window-title status, rendered game viewport, lifecycle code, and preview/audio docs with the stated GB-05 user-facing contracts. The audited plans and summaries describe strong software transition coverage, but that evidence does not establish how the live window, native dialogs, contrast, or text wrapping appear.

## Pillar Scores

| Pillar | Score | Key Finding |
|--------|-------|-------------|
| 1. Copywriting | 3/4 | Keyboard controls and audio limitations are explicit, but the supported gamepad mapping is absent from help and preview controls. |
| 2. Visuals | 2/4 | The game frame is the focal point, while pause, volume, focus, and device feedback live only in the native window title. |
| 3. Color | 3/4 | The viewport has a dark surround; there is no custom state-color system, and rendered color distribution/contrast could not be checked. |
| 4. Typography | 2/4 | F1 help places controls, audio behavior, save recovery, and model caveats in one plain native message box without clear section hierarchy. |
| 5. Spacing | 3/4 | The game frame uses centered integer scaling; help/status spacing is delegated to OS chrome and was not visually verified. |
| 6. Experience Design | 2/4 | Focus/device recovery is explicit in code, but gamepad discovery is missing, current gain feedback is transient, and reset is immediate. |

**Overall: 15/24**

## Top 3 Priority Fixes

1. **Document gamepad controls in F1 and the preview guide** — controller users cannot discover that D-pad maps movement, South/East map A/B, and Start/Back map Start/Select — add the mappings already implemented in `input.c` to both user-facing control lists.
2. **Keep player state and gain visible in the app** — title-bar-only feedback can be missed, and the displayed `Volume N%` is replaced by the next status — add a compact in-window status/gain indicator for pause, focus, audio availability, and current gain.
3. **Guard reset when a session may contain volatile progress** — pressing `R` starts reset immediately when the save transition succeeds, with no confirmation — ask before clearing a session whose progress cannot be restored from battery RAM.

## Detailed Findings

### Pillar 1: Copywriting (3/4)

- **WARNING — gamepad input is implemented but undiscoverable.** F1 lists arrow keys, Z/X, Return, and Right Shift, but no controller controls (`src/player/main.c:671-675`). The preview table also lists only keyboard controls (`docs/preview.md:30-43`), while the implementation handles D-pad, South/East, Start, and Back (`src/player/input.c:150-161`). Add those mappings to both help surfaces.
- Positive evidence: the app names the audio format and gain range, explains unavailable-sink behavior, and distinguishes app underflow from hardware starvation (`src/player/main.c:338-355`, `663-688`). Lifecycle and ROM errors use concrete outcomes such as “current ROM unchanged” (`src/player/main.c:1020-1038`).

### Pillar 2: Visuals (2/4)

- **WARNING — in-app state feedback is absent.** `set_status` only updates the native window title (`src/player/main.c:641-660`); the render path clears the surround and draws the game texture without a status or controls layer (`src/player/main.c:746-763`). Pause and audio-device state are therefore outside the main visual focal area. Add a small status/gain strip or transient overlay that does not obscure gameplay.
- The integer-scaled game image is centered and nearest-neighbor filtered (`src/player/presentation.c:5-23`, `src/player/main.c:523-539`), which supports the emulator’s content as the screen focal point. Whether this balance, title visibility, and native help dialog work at actual window sizes is **unverified without a rendered capture**.

### Pillar 3: Color (3/4)

- **WARNING — shell-state contrast and accent use are not established.** The only explicit shell color found is the dark clear color RGB(8, 24, 32) around the game texture (`src/player/main.c:749-759`). Pause, audio-unavailable, and volume states are conveyed as title text rather than differentiated in the rendered surface (`src/player/main.c:649-655`, `1183-1192`). Because ROM pixels dominate the viewport and no screenshot was captured, the 60/30/10 distribution and actual contrast cannot be verified. If adding an in-window status, give it a deliberate, consistent palette and retain text labels so color is not the only signal.

### Pillar 4: Typography (2/4)

- **WARNING — the help surface has weak information hierarchy.** F1 builds one plain-text string for a native simple message box, combining control mappings, audio format and recovery, evidence limits, save-failure choices, current status, and the general limitations text (`src/player/main.c:669-691`). It has paragraph breaks but no separately titled Controls, Audio, Status, and Recovery sections. Split those topics into short labeled groups or a dedicated help surface; inspect wrapping on supported macOS display scales before treating typography as verified.
- The application relies on platform-rendered window titles and a platform-native message box rather than specifying a type scale. Font size, wrapping, and legibility are **unverified** here.

### Pillar 5: Spacing (3/4)

- The game image has a consistent geometry rule: preserve 160×144 pixels, use the largest integer scale that fits, and center it (`src/player/presentation.c:5-23`). The window also requests high-density support and a 160×144 minimum (`src/player/main.c:504-517`).
- **WARNING — spacing for help and status is not controlled by the app.** Those elements use the OS title bar and `SDL_ShowSimpleMessageBox` (`src/player/main.c:641-655`, `663-691`); their spacing and long-message wrapping have not been captured. Keep critical state messages short and verify the native dialog on the target macOS display sizes.

### Pillar 6: Experience Design (2/4)

- **WARNING — reset can clear non-persistent play without a confirmation.** The help says `R` resets (`src/player/main.c:674-675`), and that key immediately starts a reset transition (`src/player/main.c:1195-1197`). The transition prompts only when saving fails; successful save or non-battery sessions proceed to reset (`src/player/main.c:977-1003`, `948-957`). Add confirmation when current progress is volatile or otherwise cannot be restored.
- **WARNING — gain feedback is temporary.** Bracket keys change host gain in 10-point steps and publish `Volume N%` as the current status (`src/player/main.c:1183-1192`), but any subsequent status overwrites it (`src/player/main.c:658-660`). Show the current gain persistently, including when the sink is unavailable, so users can tell whether a key press reached 0% or 200%.
- Positive evidence: pause clears host PCM while retaining guest/APU history, focus loss releases inputs and pauses, focus regain respects intentional pause, device loss reports unavailable, and reset/replacement status paths are explicit in code (`src/player/main.c:783-810`, `1114-1131`, `1300-1333`). The docs also explain the transition rules (`docs/audio-and-playback.md:72-85`). These are code findings; no interactive state was captured because interaction capture was off.

## Files Audited

- `.planning/STATE.md`, `.planning/PROJECT.md`, `.planning/research/SUMMARY.md`
- `.planning/phases/GB-05-dmg-audio-and-stable-playback/05-CONTEXT.md`
- `.planning/phases/GB-05-dmg-audio-and-stable-playback/05-01-PLAN.md` and `05-01-SUMMARY.md`
- `.planning/phases/GB-05-dmg-audio-and-stable-playback/05-02-PLAN.md` and `05-02-SUMMARY.md`
- `.planning/phases/GB-05-dmg-audio-and-stable-playback/05-03-PLAN.md` and `05-03-SUMMARY.md`
- `.planning/phases/GB-05-dmg-audio-and-stable-playback/05-04-PLAN.md` and `05-04-SUMMARY.md`
- `.planning/phases/GB-05-dmg-audio-and-stable-playback/05-05-PLAN.md` and `05-05-SUMMARY.md`
- `.planning/phases/GB-05-dmg-audio-and-stable-playback/05-06-PLAN.md` and `05-06-SUMMARY.md`
- `.planning/phases/GB-05-dmg-audio-and-stable-playback/05-07-PLAN.md` and `05-07-SUMMARY.md`
- `README.md`, `docs/preview.md`, `docs/audio-and-playback.md`
- `src/player/main.c`, `src/player/presentation.c`, `src/player/presentation.h`, `src/player/input.c`, `src/player/input.h`, `src/player/audio.c`, `src/player/audio.h`, `src/player/limitations.h`

## Orchestrator Disposition

The scores above describe the pre-fix audit baseline. The recommendations were reviewed against the phase decisions and applied as follows:

1. **Gamepad discovery — applied.** F1 help and `docs/preview.md` now list the implemented D-pad, South/East, and Start/Back mappings. The packaged-player verifier asserts that the shipped help contains those mappings.
2. **Persistent state/gain — adapted and applied within D-08.** The native title now keeps current host gain visible independently of transient status, alongside run/pause and audio availability. F1 explains this behavior, and the player smoke checks both the default 100% and an adjusted gain. No in-window overlay was added: D-08 calls for existing title/help surfaces, the phase excludes a generic settings UI, and the 160×144 game image remains unobstructed. A rendered native-window inspection is still unverified.
3. **Reset confirmation — deferred.** `R` remains a direct emulator reset shortcut. Phase D-10 orders battery-save handling before reset, while adding a modal confirmation to an intentional frequent control would add friction without current evidence of accidental-reset harm. The F1 map discloses the shortcut and the existing save-failure prompt remains intact; revisit if user evidence shows accidental resets or volatile progress loss is a recurring problem.

These source/help changes are software-tested. They do not resolve the audit's native-dialog wrapping, rendered contrast, or live-window appearance limitations because no target-macOS capture was available.
