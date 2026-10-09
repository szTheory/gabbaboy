# Phase 3 — UI Review

**Audited:** 2026-10-09
**Baseline:** Abstract six-pillar standards adapted to the native SDL3/C DMG player; no UI-SPEC.md exists.
**Screenshots:** not captured (port 8080 answered, but desktop, mobile, and tablet Playwright captures all failed; native SDL display unavailable)
**Interaction captures:** off (workflow.ui_interaction_capture is false)

---

## Pillar Scores

| Pillar | Score | Key Finding |
|--------|-------|-------------|
| 1. Copywriting | 3/4 | Status and ROM errors are specific, but key controls and limitations require opening F1. |
| 2. Visuals | 2/4 | The game image is the clear focal point, while all player controls and state are outside the viewport in the title/help dialog. |
| 3. Color | 3/4 | DMG pixels remain the accent and the letterbox is restrained; no current live rendering was available to inspect. |
| 4. Typography | 2/4 | Application UI relies on the OS title bar and message box; the long title carries several unrelated status fields. |
| 5. Spacing | 3/4 | Integer scaling and letterboxing are explicit, but the OS-level controls/status have no app-controlled layout to tune. |
| 6. Experience Design | 3/4 | Core keyboard/session flows and recovery messages are implemented; current-checkout live behavior was not captured. |

**Overall: 16/24**

---

## Top 3 Priority Fixes

1. **Put essential controls and run/pause state in a persistent player surface** — users must discover controls from the title or summon F1; add a compact, readable status/control strip or an always-visible first-run hint.
2. **Shorten and separate the window title fields** — ROM name, run state, gain, shortcuts, audio availability, and status compete in one string; keep the title concise and move changing status into a dedicated visible area.
3. **Repeat the current packaged-window and mapped-key check on this revision** — prior UAT observed the demo responding to Z, but no current native screenshot or interaction capture is available; launch the current package, confirm the fixture appears, then verify press/release response.

---

## Detailed Findings

### Pillar 1: Copywriting (3/4)

- **WARNING:** Copy for failure/recovery is concrete and preserves user state. Examples include “The selected file is truncated; choose a complete supported Game Boy ROM” and “ROM loaded; input and display state reset” in [session.c](/private/tmp/gabbaboy-phase3-refresh/src/player/session.c:55) and [main.c](/private/tmp/gabbaboy-phase3-refresh/src/player/main.c:915).
- **WARNING:** Keyboard mappings, gamepad mapping, audio behavior, and software-model limitations are only discoverable through F1 or documentation; the framebuffer itself does not label the controls. The F1 text is assembled in [main.c](/private/tmp/gabbaboy-phase3-refresh/src/player/main.c:700).
- The phase's original audio/persistence-absent notice is no longer applicable to the current implementation: current preview code implements scoped digital audio and standard-MBC1 battery saves, and labels their remaining evidence limits in [limitations.h](/private/tmp/gabbaboy-phase3-refresh/src/player/limitations.h:4) and [preview.md](/private/tmp/gabbaboy-phase3-refresh/docs/preview.md:62).

### Pillar 2: Visuals (2/4)

- **WARNING:** The 160×144 game frame is the only content rendered into the window. `draw_frame` clears to a dark letterbox color and draws the frame, with no visible controls, ROM/status label, or pause indicator in the client area ([main.c](/private/tmp/gabbaboy-phase3-refresh/src/player/main.c:780)).
- **WARNING:** The title provides an F1 discovery route, but concentrates ROM, state, gain, shortcuts, status, and audio availability in one OS title string ([main.c](/private/tmp/gabbaboy-phase3-refresh/src/player/main.c:666)). The controls/limitations message box is on demand rather than part of the play surface ([main.c](/private/tmp/gabbaboy-phase3-refresh/src/player/main.c:693)).
- No current screenshots were captured. The historical UAT records a user-observed Z press darkening the demo tile and release restoring it; Phase 3's latest summary says the current packaged-window/key observation remains outstanding. This review does not treat that historical observation as a current visual capture.

### Pillar 3: Color (3/4)

- **WARNING:** The renderer uses a single dark teal letterbox color `(8, 24, 32)` and otherwise displays the emulated shade-index image ([main.c](/private/tmp/gabbaboy-phase3-refresh/src/player/main.c:783)). This keeps the rendered picture focused, but the 60/30/10 balance and contrast cannot be verified against a live window here.
- There are no Tailwind/CSS color tokens in this native SDL player. The fixed host color is intentionally limited to the clear color; pixel colors come from the core's shade conversion. A static screenshot was unavailable to inspect actual contrast or color perception.

### Pillar 4: Typography (2/4)

- **WARNING:** The application does not render an in-window text hierarchy; it relies on the platform title bar plus a modal native message box. The title concatenates up to a 159-byte ROM basename with state, gain, shortcuts, status, and audio state ([main.c](/private/tmp/gabbaboy-phase3-refresh/src/player/main.c:666)). Long names/statuses can make this OS-managed line difficult to scan or truncate.
- No application font sizes or weights are defined, which avoids inconsistent custom typography but leaves no control over the visibility/readability of essential player status. No visual capture was available to judge platform rendering.

### Pillar 5: Spacing (3/4)

- **WARNING:** Frame layout follows a strong pixel constraint: 160×144 logical presentation, integer scaling, nearest-neighbor filtering, and a 160×144 minimum window are set in [main.c](/private/tmp/gabbaboy-phase3-refresh/src/player/main.c:529) and [main.c](/private/tmp/gabbaboy-phase3-refresh/src/player/main.c:548).
- The player-owned layout is only the game viewport; the help and status content use OS-managed title/message-box layout. There is no app-owned spacing system for persistent controls or status, so the player cannot tune their proximity or grouping. This is a quality limitation rather than a frame-scaling defect.

### Pillar 6: Experience Design (3/4)

- **WARNING:** Code provides mapped keyboard/gamepad input, repeat suppression, focus-loss release handling, pause/reset, an async ROM picker, and actionable replacement/save failures. The controls are handled in [main.c](/private/tmp/gabbaboy-phase3-refresh/src/player/main.c:1172); bounded ROM errors preserve the current session in [session.c](/private/tmp/gabbaboy-phase3-refresh/src/player/session.c:169).
- The current code does not provide an in-window control legend or state indicator; users depend on F1 and OS title updates. The title is refreshed on status changes ([main.c](/private/tmp/gabbaboy-phase3-refresh/src/player/main.c:681)).
- **WARNING:** Live evidence is incomplete for this checkout. Historical UAT reports a Z hold/release visual change; the latest Phase 3 summary explicitly retains the packaged-window/key check as open. This audit attempted the documented local capture path: port 8080 answered, but all three browser captures failed; native SDL visual/interaction capture was unavailable. Interaction capture was off by configuration.

---

## Files Audited

- `src/player/main.c`
- `src/player/session.c`
- `src/player/limitations.h`
- `docs/preview.md`
- `.planning/phases/GB-03-visible-interactive-dmg/03-CONTEXT.md`
- `.planning/phases/GB-03-visible-interactive-dmg/03-UAT.md`
- `.planning/phases/GB-03-visible-interactive-dmg/03-13-SUMMARY.md`
- `.planning/phases/GB-03-visible-interactive-dmg/03-01-PLAN.md` through `03-13-PLAN.md`
- `.planning/phases/GB-03-visible-interactive-dmg/03-01-SUMMARY.md` through `03-13-SUMMARY.md`
