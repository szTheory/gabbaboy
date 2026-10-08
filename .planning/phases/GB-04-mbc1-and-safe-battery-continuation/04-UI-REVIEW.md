# Phase 4 — UI Review

**Audited:** 2026-10-08
**Baseline:** Abstract six-pillar standards; no Phase 4 UI-SPEC.md exists. Review scope is the player battery-save status and final-flush choice UI.
**Screenshots:** Not captured (localhost:8080 answered, but Playwright screenshot failed at desktop 1440×900, mobile 375×812, and tablet 768×1024; code-only audit).
**Interaction captures:** off (workflow.ui_interaction_capture is false)

---

## Pillar Scores

| Pillar | Score | Key Finding |
|--------|-------|-------------|
| 1. Copywriting | 3/4 | Save state and failure choices are explicit, but title/status messages are long and platform terminology varies. |
| 2. Visuals | 2/4 | Save feedback is confined to the native window title or an F1 message box; no in-window status or focused final-save prompt is drawn. |
| 3. Color | 2/4 | Four DMG shades are used for the emulated image, but save success, dirty state, and failure have no color or other persistent in-window visual distinction. |
| 4. Typography | 2/4 | Native system typography avoids custom-font inconsistency, but status hierarchy, emphasis, and truncation cannot be controlled in the title/message box. |
| 5. Spacing | 2/4 | Help copy uses manually embedded newlines, while title status has no layout control; no save-state spacing or responsive treatment is implemented. |
| 6. Experience Design | 2/4 | Retry, continue-without-saving, and cancel are implemented and named, but an error requires discovering keyboard choices through the title or F1 help. |

**Overall: 13/24**

---

## Top 3 Priority Fixes

1. **Make a failed final flush an unmistakable, focused choice state** — users may miss the title-bar error while facing a blocked quit/reset/replacement — show an in-window or native confirmation with Retry, Continue without saving, and Cancel controls, including keyboard focus and a clear consequence.
2. **Keep dirty and saved state visible without relying on transient title text** — a user can otherwise mistake in-memory progress for durable progress after the success message is replaced — add a compact persistent status indicator and retain the existing precise “in memory” and “saved to disk” distinctions.
3. **Give status copy a constrained, testable layout** — long errors and ROM names compete in a platform-controlled title whose truncation point varies — place status in a fixed UI surface, shorten primary copy, and expose full details through help or an accessible description.

---

## Detailed Findings

### Pillar 1: Copywriting (3/4)

- **WARNING** — `src/player/main.c:539-545` spells out the failure and maps `R`, `C`, and `Esc` to retry, continue without saving, and cancel. `src/player/main.c:342` repeats the final-flush choices in F1 help. These labels communicate consequence and action clearly.
- **WARNING** — `src/player/main.c:164`, `531`, `567`, and `937` distinguish loaded, changed-but-unsaved, and saved-to-disk states. The careful wording is good, but repeated variants (“changes are in memory until saved”, “progress is in memory until saved”, “remains only in memory”) make the status vocabulary less consistent than necessary.
- **WARNING** — `src/player/main.c:320-323` combines the ROM basename, run state, save/error status, keyboard shortcuts, and unavailable-audio note in the native title. The status can be as long as 192 bytes, so the most important failure detail may be clipped by the window manager.
- No generic “OK”, “Submit”, or empty-state copy was found in the player implementation. This is a native emulator UI, so web empty/loading patterns do not apply.

### Pillar 2: Visuals (2/4)

- **WARNING** — `src/player/main.c:322-324` presents battery feedback only through `SDL_SetWindowTitle`; the game frame rendering at `405-424` contains no status overlay. A title can be hidden or elided by the host window manager and is not part of the game viewport.
- **WARNING** — `src/player/main.c:332-350` exposes fuller status only after F1 opens a generic information message box. It is useful as a secondary explanation, but it does not visually direct the user toward the required choice when a final flush fails.
- Static screenshots were not captured: the detected localhost endpoint was not a usable Playwright page, and this native SDL player was therefore reviewed from source only. No visual layout claim is inferred from a screenshot.

### Pillar 3: Color (2/4)

- **WARNING** — The rendered display uses a deliberate four-color DMG palette at `src/player/main.c:269-272`; this is appropriate for emulated pixels. Battery status is outside that render path and has no distinct in-window color, icon, or other visual state at `311-325` and `405-424`.
- No Tailwind or CSS custom properties apply. The native title/message-box theme is controlled by the operating system; the app cannot promise a 60/30/10 distribution there. The missing save-status visual state is the concrete gap, rather than the DMG palette itself.

### Pillar 4: Typography (2/4)

- **WARNING** — The player uses native system title and message-box fonts (`src/player/main.c:319-324`, `348-350`), so font family/size adapts to the host. However, there is no typographic hierarchy between ordinary status, dirty progress, and failure, and no control over wrapping or emphasis.
- **WARNING** — The title format appends status to a long fixed string and a variable ROM basename (`src/player/main.c:313-323`). Because native title clipping varies by platform and window width, critical save details have no guaranteed visible position.
- Web font-size/weight counts are not applicable: the audited UI is SDL-native C, with no JSX, CSS, or font declarations.

### Pillar 5: Spacing (2/4)

- **WARNING** — F1 help uses literal newline spacing in a single message string (`src/player/main.c:337-347`); there is no component layout contract or control over native wrapping. This is serviceable for short help but fragile as status and limitation text grow.
- **WARNING** — Save feedback has no dedicated layout bounds, spacing, or responsive behavior; the title is one line and the save state is not drawn in the resizable render area (`src/player/main.c:191-194`, `311-324`, `405-424`).
- CSS spacing utilities and arbitrary pixel-value checks do not apply to this native SDL interface.

### Pillar 6: Experience Design (2/4)

- **WARNING** — The transition flow blocks completion on save failure and offers retry, explicit continue-without-saving, or cancel (`src/player/main.c:623-650`, `773-803`). The code keeps the current session on cancel and records unsaved RAM after choosing to continue (`src/player/main.c:572-603`). This is a sound safety model.
- **WARNING** — The failure choice is keyboard-only: `R`, `C`, and Escape are handled during a pending transition (`src/player/main.c:778-803`). The title mentions the choices (`539-546`), and F1 help documents them (`332-347`), but there is no visible dialog/control, focus treatment, mouse action, or immediate prompt in the game window. That makes a high-consequence decision easy to miss and harder for users unfamiliar with keyboard shortcuts.
- **WARNING** — Successful save feedback is deliberately concise (`src/player/main.c:567`) and failures remain active until success or a user choice (`539-546`, `549-569`). However, success status is transient and the UI does not keep a durable “saved/currently dirty” badge visible after later status updates.
- The implementation includes automated save-transition smoke assertions (`src/player/main.c:1157-1227`), but interaction capture was off and no live manual interaction was observed in this audit.

---

## Files Audited

- `src/player/main.c` — window creation/rendering, title status, F1 help, save success/failure state, final transition choices, and smoke assertions.
- `src/player/limitations.h` — save cadence and limitation copy.
- `src/player/session.c` and `src/player/session.h` — save error outcomes that feed user-facing status.
- `tests/player/test_limitations.c` — asserted public limitation wording.
- `.planning/phases/GB-04-mbc1-and-safe-battery-continuation/04-CONTEXT.md` — Phase 4 UX decisions, especially D-09 through D-13.
- `.planning/phases/GB-04-mbc1-and-safe-battery-continuation/04-01-PLAN.md` through `04-07-PLAN.md` and corresponding `04-01-SUMMARY.md` through `04-07-SUMMARY.md` — intended and delivered scope.
