# Phase GB-03 — UI Review

**Audited:** 2026-10-09
**Baseline:** Abstract six-pillar standards adapted to the native SDL3/C DMG player; no UI-SPEC.md exists.
**Screenshots:** Not captured — this environment has no native SDL window capture. The earlier browser capture attempt reached a web port, but all three Playwright captures failed and could not show the native player.
**Interaction captures:** off (workflow.ui_interaction_capture is false)
**Scope note:** The current output-directory safety change adds `O_NONBLOCK` to ROM file opens in `src/player/session.c`; it does not change the player UI. No new UI implementation change was found in this refresh.

---

## Pillar Scores

| Pillar | Score | Key Finding |
|--------|-------|-------------|
| 1. Copywriting | 3/4 | Error and limitation copy is specific, but controls and the technical help are concentrated in a dense F1 modal. |
| 2. Visuals | 2/4 | The game image is the only client-area content; controls, ROM identity, and run state have no persistent in-window presentation. |
| 3. Color | 3/4 | Code uses four DMG shades and a single dark teal surround; live contrast and rendered distribution were not captured. |
| 4. Typography | 2/4 | No in-window text hierarchy exists; changing status, controls, and audio information compete in the OS title and modal help. |
| 5. Spacing | 3/4 | Integer pixel scaling and native-size minimum are explicit, but there is no app-owned layout for controls or status. |
| 6. Experience Design | 2/4 | Input, pause/reset, ROM replacement, and recovery are implemented; key discovery and state visibility depend on OS chrome or F1. |

**Overall: 15/24**

---

## Top 3 Priority Fixes

1. **Add persistent controls and run/ROM status to the player surface** — users cannot see the key map or current state while playing; add a compact in-window strip or unobtrusive overlay.
2. **Shorten the title and move changing details into the player surface** — ROM basename, pause state, gain, status, shortcuts, and audio availability compete in one OS-managed string; reserve the title for app and ROM identity.
3. **Restructure F1 help into scannable sections** — the current message combines controls, save recovery, audio operation, model limits, and status; group controls and capability notes with short headings or separate concise dialogs.

---

## Detailed Findings

### Pillar 1: Copywriting (3/4)

- **WARNING:** ROM errors are actionable and specific, including “The selected file is truncated; choose a complete supported Game Boy ROM.” The replacement path retains the current session when opening or loading fails (`src/player/session.c:55`, `src/player/session.c:166-202`).
- **WARNING:** F1 text accurately lists keyboard/gamepad mappings, pause/reset/save actions, audio format and gain, unavailable-device handling, scoped audio-model limits, and battery-save recovery (`src/player/main.c:700-734`, `src/player/limitations.h:4-78`). The content is useful but lengthy and available only on demand.
- `docs/preview.md:38-85` repeats controls and capability limitations. This supports accurate documentation but does not make controls discoverable inside the running player.

### Pillar 2: Visuals (2/4)

- **WARNING:** `draw_frame` clears the renderer to `(8, 24, 32)` and draws only the emulated frame. No ROM label, controls, or pause/status indicator is rendered in the client area (`src/player/main.c:788-802`).
- **WARNING:** The window title concatenates ROM name, Running/Paused, gain, status, Open/Quit/F1 shortcuts, and audio availability (`src/player/main.c:673-697`). Help is a separate native modal (`src/player/main.c:700-734`).
- **Evidence distinction:** The audit has no native screenshot. Separately, the owner observation recorded in `03-UAT.md` reports that the packaged player displayed the demo and the target tile darkened while Z was held, then returned to light when released (test 34, observed 2026-10-09). This is retained owner-observed interaction evidence, not a screenshot or an audit capture.

### Pillar 3: Color (3/4)

- **WARNING:** The code maps four shade indices to a light-to-dark green palette and uses one fixed dark teal renderer clear color (`src/player/main.c:32-35`, `src/player/main.c:791-799`). This is restrained in source, but the 60/30/10 distribution, contrast, and platform rendering cannot be judged without a native capture.
- This is a native SDL player, so CSS/Tailwind token counts do not apply. There is no evidence of multiple host accent colors in the audited renderer path.

### Pillar 4: Typography (2/4)

- **WARNING:** No text is rendered in the game client area. State and shortcuts are placed in the OS title; help and limitations appear in a native message box, so the app has no controllable text hierarchy (`src/player/main.c:673-734`).
- The title includes a ROM basename of up to 159 bytes before adding pause state, gain, status, shortcut text, and audio state (`src/player/main.c:27`, `src/player/main.c:673-685`). The window manager may truncate this line, and no screenshot was available to inspect actual platform treatment.

### Pillar 5: Spacing (3/4)

- **WARNING:** The player creates a 3× native-size window, enforces a 160×144 minimum, uses 160×144 logical integer presentation, and selects nearest-neighbor texture scaling (`src/player/main.c:540-573`). These are concrete pixel geometry constraints.
- The app-owned layout contains only the frame; controls and status are delegated to OS chrome and a modal. Consequently, the player has no spacing or grouping system for persistent affordances. Native spacing was not visually captured.

### Pillar 6: Experience Design (2/4)

- **WARNING:** Source implements keyboard/gamepad handling, repeat suppression, focus-loss releases, pause/reset, asynchronous ROM selection, and bounded replacement failures (`src/player/main.c:700-735`, `src/player/main.c:1186-1248`, `src/player/session.c:166-205`). These support the core play and recovery paths.
- **WARNING:** State updates refresh the window title, but the client area shows no current ROM or run/pause status. The control map is available through F1 and documentation rather than a persistent in-player cue (`src/player/main.c:688-697`, `src/player/main.c:700-734`).
- **Retained owner evidence:** `03-UAT.md` records 34/34 checks passed and separately records the 2026-10-09 user observation of packaged demo visibility and Z press/release feedback. That owner observation does not substitute for native screenshots in this audit. Interaction capture was off by configuration.
- No loading-state issue applies to the static local renderer. ROM selection, cancellation, and load errors are handled in the SDL flow; no new UI regression was identified in the output-directory safety change.

---

## Files Audited

- `src/player/main.c`
- `src/player/session.c`
- `src/player/limitations.h`
- `docs/preview.md`
- `.planning/phases/GB-03-visible-interactive-dmg/03-CONTEXT.md`
- `.planning/phases/GB-03-visible-interactive-dmg/03-UAT.md`
- `.planning/phases/GB-03-visible-interactive-dmg/03-01-PLAN.md` through `03-13-PLAN.md`
- `.planning/phases/GB-03-visible-interactive-dmg/03-01-SUMMARY.md` through `03-13-SUMMARY.md`
