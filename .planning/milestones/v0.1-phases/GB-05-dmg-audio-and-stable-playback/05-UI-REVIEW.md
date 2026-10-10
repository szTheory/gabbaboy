# Phase 5 — UI Review

**Audited:** 2026-10-09
**Baseline:** Abstract 6-pillar standards; no `05-UI-SPEC.md` exists.
**Screenshots:** Not captured. The required localhost probe reached only `localhost:8080`, whose response identifies itself as the Traefik Proxy dashboard. That is not the native SDL player; no legitimate browser capture target was available. Findings about appearance are code-derived.
**Interaction captures:** off (workflow.ui_interaction_capture is false)

This is a fresh audit of the current native SDL source and consumer help. The corrected retry instructions are accurate: `S` saves or retries a failed background save, while `R` retries a reset, replacement, or quit blocked by a failed save. The built player's `--help`, F1 source text, transition handler, and `docs/preview.md` agree. No stale claim that `S` retries a blocked transition was found.

## Pillar Scores

| Pillar | Score | Key Finding |
|--------|-------|-------------|
| 1. Copywriting | 3/4 | Save and transition retry keys are correctly distinguished, but `R` has two context-dependent meanings and the distinction takes a sentence to explain. |
| 2. Visuals | 2/4 | The game image is the sole in-window content; pause, gain, save recovery, and audio availability are reported through native title chrome. |
| 3. Color | 3/4 | A restrained four-shade green game palette and dark teal surround are explicit, but color balance and contrast cannot be verified without a native capture. |
| 4. Typography | 2/4 | F1 uses a long unsectioned message string and OS-default dialog typography; wrapping and scan hierarchy are unverified. |
| 5. Spacing | 3/4 | The 160×144 image is centered at integer scale, while help and status spacing are delegated to native OS chrome. |
| 6. Experience Design | 2/4 | Input, audio, and save recovery paths are explicit, but key gameplay state is title-only and F1 is ignored during a pending save transition. |

**Overall: 15/24**

## Top 3 Priority Fixes

1. **Show essential state within the app window** — users can miss pause, gain, audio loss, or a save error while focused on gameplay — add a compact, transient status treatment in the SDL render surface with text labels, keeping the game image unobstructed.
2. **Give F1 help a scan hierarchy** — the controls, save recovery, audio behavior, limitations, and status currently form one long native message — divide the text into short labeled sections and keep the distinct `S` and conditional `R` meanings adjacent.
3. **Reduce title-bar dependence and length** — the title combines ROM name, run state, gain, status, shortcuts, and sink state in one line, which is liable to clip on ordinary title bars — shorten it to identity and run state, and put actionable status in the window surface or a concise native notification.

## Detailed Findings

### Pillar 1: Copywriting (3/4)

- **WARNING — `R` is reused across two actions.** F1 says `Reset current ROM: R` and separately says `If reset, ROM replacement, or quit is blocked by a failed save: R retries; C continues without saving; Escape cancels` (`src/player/main.c:713-716`). This is accurate and matches the pending-transition handler (`src/player/main.c:1211-1235`), but users must retain the current context to know whether `R` resets or retries. Keep the conditional distinction prominent in any shorter help treatment.
- **Verified correction:** F1 says `Save battery RAM now / retry a failed background save: S` (`src/player/main.c:714`); the built consumer help says `S saves or retries a failed background save` and separately assigns `R` to blocked transitions. The preview guide states the same mapping (`docs/preview.md:51-57`). The current title status also names `R`, `C`, and Escape during a blocked transition (`src/player/main.c:965-972`).
- Positive evidence: keyboard, gamepad, pause, gain, audio-unavailable behavior, and evidence limits are described with concrete labels in F1 and CLI help (`src/player/main.c:368-390`, `700-730`).

### Pillar 2: Visuals (2/4)

- **WARNING — gameplay state is outside the rendered surface.** The render path clears the surround and draws only the game texture (`src/player/main.c:788-805`). Pause, gain, save status, shortcuts, and audio readiness are composed into the native window title (`src/player/main.c:673-697`). A player looking at the game image has no in-surface cue for those states.
- **WARNING — title content is likely to clip.** The title concatenates a ROM basename, run state, gain, status, shortcuts, and audio state (`src/player/main.c:679-685`); the 512-byte buffer bounds memory but does not bound rendered title width (`src/player/main.c:27`). There is no native-window screenshot to confirm the actual clipping point. Audio readiness is last in the string, after variable-length status text.
- Positive evidence: the 160×144 game image is centered, aspect-preserving, and integer-scaled (`src/player/presentation.c:5-23`); the desktop window starts at 3× native dimensions (`src/player/main.c:540-543`). This gives the game a clear focal point, but does not replace state feedback.

### Pillar 3: Color (3/4)

- **WARNING — color balance and contrast are unverified.** Source defines four green-tinted game shades and a deep teal surround (`src/player/main.c:32-35`, `791-792`). State messages remain in the OS title bar, so the app has no explicit state-color palette. Without a native capture, the perceived 60/30/10 balance, contrast at the actual window size, and any color-management effects cannot be assessed.
- Code evidence shows a restrained palette with no repeated accent-color calls across UI controls; this is preferable to adding color-only status distinctions. Keep future state cues textual as well as colored.

### Pillar 4: Typography (2/4)

- **WARNING — F1 has weak scan hierarchy.** A single `snprintf` string places controls, gamepad mapping, reset/save recovery, audio format, lifecycle behavior, evidence limits, and current status in one simple native message box (`src/player/main.c:706-734`). Blank lines separate topics, but there are no labels or headings, and no project-controlled type scale or emphasis.
- **WARNING — native text fit is unknown.** Both F1 wrapping and the long title depend on the OS (`src/player/main.c:679-685`, `731-734`). The browser probe could not capture this SDL surface, so readable wrapping, truncation, and display-scale behavior remain unverified.

### Pillar 5: Spacing (3/4)

- **WARNING — help spacing is OS-defined.** The help is passed to `SDL_ShowSimpleMessageBox` as a plain string (`src/player/main.c:731-734`); the application controls line breaks but not the dialog's padding or line spacing. This limits consistency across supported desktop environments.
- Positive evidence: layout uses the largest integer scale that fits and centers the image (`src/player/presentation.c:10-22`); the SDL renderer uses integer logical presentation (`src/player/main.c:559-563`). Source also exercises odd and even software-renderer dimensions (`src/player/main.c:1641-1647`), although those checks do not establish native-window appearance.

### Pillar 6: Experience Design (2/4)

- **WARNING — recovery instructions are not available through F1 at the failure moment.** While a save-blocked transition is pending, the key handler accepts only Escape, `R`, and `C`, then returns (`src/player/main.c:1211-1235`); F1 therefore does nothing in that state. The title does display the retry/continue/cancel choices (`src/player/main.c:965-972`), but that same title is the only visible guidance during gameplay and may clip.
- **WARNING — important feedback is title-only.** Pause, focus recovery, input queue errors, save failure, and audio device changes update the title (`src/player/main.c:673-697`, `1186-1203`, `1281-1289`, `1372-1405`). There is no in-window status area in `draw_frame` (`src/player/main.c:788-805`), so these conditions compete with long ROM and shortcut text in native chrome.
- Positive evidence: F1 pauses/clears host input/audio and restores prior run state afterward (`src/player/main.c:700-738`); focus and gamepad releases are tracked, and device removal/recovery has explicit status and cleanup paths (`src/player/main.c:1352-1405`). The transition mapping was verified against current source and built consumer help. No live interaction state was captured because interaction capture is off.

## Files Audited

- `AGENTS.md`, `.planning/STATE.md`, `.planning/PROJECT.md`, `.planning/research/SUMMARY.md`
- `.planning/phases/GB-05-dmg-audio-and-stable-playback/05-CONTEXT.md`
- `.planning/phases/GB-05-dmg-audio-and-stable-playback/05-01-PLAN.md` through `05-07-PLAN.md`
- `.planning/phases/GB-05-dmg-audio-and-stable-playback/05-01-SUMMARY.md` through `05-07-SUMMARY.md`
- `src/player/main.c`, `src/player/presentation.c`, `src/player/presentation.h`, `src/player/input.c`, `src/player/input.h`, `src/player/audio.c`, `src/player/audio.h`, `src/player/limitations.h`
- `docs/preview.md`, `docs/audio-and-playback.md`
- Built player `--help` output from `build/phase3-player/gabbaboy/gabbaboy-player`
