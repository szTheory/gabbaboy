# Phase 4 — UI Review

**Audited:** 2026-10-09
**Baseline:** Abstract six-pillar standards; no Phase 4 UI-SPEC.md exists. Review scope is the native SDL player’s MBC1 battery-save feedback and quit/reset/replacement choices.
**Screenshots:** Not captured (native SDL macOS player; no applicable browser page or visual capture was available. localhost:8080 returned HTTP 200, but it is not evidence of the SDL player UI; code-only audit).
**Interaction captures:** off (workflow.ui_interaction_capture is false)

---

## Pillar Scores

| Pillar | Score | Key Finding |
|--------|-------|-------------|
| 1. Copywriting | 3/4 | Durable versus in-memory state and save-failure choices are explicit, but similar statuses use several phrasings and share a constrained title surface. |
| 2. Visuals | 2/4 | The game image is the only in-window visual; save state and blocked-transition choices appear in the OS title, without an in-window prompt. |
| 3. Color | 2/4 | The four-shade DMG image has a coherent palette, but success, dirty, and failure save states have no distinct visual treatment. |
| 4. Typography | 2/4 | Native title and message-box typography is legible by platform convention, but the app cannot establish hierarchy or protect critical status from title clipping. |
| 5. Spacing | 2/4 | The emulated image uses integer-scaled presentation, while save feedback has no bounded layout; F1 copy relies on a long newline-delimited system message. |
| 6. Experience Design | 2/4 | Save retry/cancel/continue behavior is safety-conscious and smoke-asserted, but high-consequence choices are keyboard-only and not presented in a focused prompt. |

**Overall: 13/24**

---

## Top 3 Priority Fixes

1. **Make a failed final flush a focused, visible choice state** — users may not notice the title-bar failure before a quit, reset, or replacement is blocked — show the failure and Retry, Continue without saving, and Cancel actions in a native or in-window prompt, with the data consequence stated beside each action.
2. **Keep dirty/saved status visible independently of transient title text** — the title status is overwritten by unrelated updates and may be elided by the window manager — add a compact persistent status treatment or maintain an unambiguous dirty/saved indicator in the player surface.
3. **Constrain save-status copy to a predictable layout** — ROM basename, run state, gain, audio availability, and error text all compete in one variable-width title — shorten the title to essentials and show full status/error detail in a bounded help or status surface.

---

## Detailed Findings

### Pillar 1: Copywriting (3/4)

- **WARNING** — `src/player/main.c:510, 953, 989, 1020-1023, 1443-1444` communicates loaded, in-memory, saved-to-disk, and retry states with useful consequences. However, dirty state is phrased as “changes are in memory until saved,” “remains only in memory,” and “progress is in memory until saved,” which weakens consistency.
- **WARNING** — `src/player/main.c:961-968, 1069-1071` explains failed saves and names the transition choices. The selected action is clear, but the long title sentence must carry both error and instructions.
- **WARNING** — `src/player/limitations.h:4-5` gives a concise scope and limitation statement, including the supported MBC1 battery configuration and autosave cadence. No generic “OK”, “Submit”, or empty-state copy was found; web empty/loading patterns do not apply to this native player.

### Pillar 2: Visuals (2/4)

- **WARNING** — `src/player/main.c:784-803` clears and presents the logical game frame; the render path contains no save-status overlay. `src/player/main.c:670-690` sends status only to `SDL_SetWindowTitle`, which can be hidden or clipped by the platform window chrome.
- **WARNING** — `src/player/main.c:697-730` exposes detailed status and controls only through an F1 information message box. The message box is a usable secondary reference, but it does not appear when a final save failure blocks the requested transition.
- Screenshots were not captured because this is a native SDL interface without an applicable browser surface. The localhost:8080 response did not provide visual evidence of the player; all visual findings are code-derived.

### Pillar 3: Color (2/4)

- **WARNING** — `src/player/main.c:32-35` defines a consistent four-color DMG palette and `src/player/main.c:632-640` maps frame shades to it. This fits the emulated display, but no separate color, icon, or other persistent visual state communicates dirty, saved, or failed battery status (`src/player/main.c:670-690, 784-803`).
- CSS/Tailwind counts and a web-style 60/30/10 split do not apply to this native SDL surface. The concrete gap is the absence of any in-window save-state differentiation; the native title/message-box colors are OS-controlled.

### Pillar 4: Typography (2/4)

- **WARNING** — `src/player/main.c:670-690, 697-730` uses native title and message-box typography. The platform provides readable system text, but the application has no control over status emphasis, wrapping, or a hierarchy between ordinary, dirty, and failed-save states.
- **WARNING** — `src/player/main.c:670-682` truncates the ROM basename safely at a UTF-8 boundary, but combines that name, run state, gain, status/error, shortcuts, and audio availability in a single title capped by `PLAYER_TITLE_SIZE` (`src/player/main.c:27`). The OS may elide that title at different points, so critical save details have no guaranteed visible position.
- Web font-size/weight distributions are not applicable: the audited UI is SDL-native C with no CSS or custom font declarations.

### Pillar 5: Spacing (2/4)

- **WARNING** — `src/player/main.c:522-574, 737-803` establishes a 160×144 logical display with integer scaling and a minimum window size. This gives the game image a predictable layout, but no corresponding bounded area, spacing, or responsive behavior exists for battery status or transition choices.
- **WARNING** — `src/player/main.c:703-726` builds F1 help as one long newline-delimited message, with fixed status truncation at 160 characters. Native message-box wrapping and spacing vary by platform, and the status can compete with controls and limitations.
- CSS spacing utilities and arbitrary pixel-value checks do not apply to this native SDL interface.

### Pillar 6: Experience Design (2/4)

- **WARNING** — `src/player/main.c:994-1041, 1045-1072, 1206-1231` preserves the session on cancel and provides retry, continue-without-saving, and cancel behavior for blocked transitions. However, the choices are only handled by keyboard (`R`, `C`, Escape), while the user sees a title update rather than a focused prompt. This increases discovery cost for a decision that may discard the most recent progress.
- **WARNING** — `src/player/main.c:971-991, 1020-1023, 1430-1444` distinguishes saved, in-memory, and failed states. These are put in the title and can be replaced by later status such as volume or input state; there is no persistent in-window dirty/saved indicator.
- **Positive evidence** — `src/player/main.c:1680-1789` contains smoke assertions for retry, cancel, and continue paths. This is source evidence that the transitions are exercised, not a live interaction capture or a visual confirmation.
- No loading skeleton or web error boundary is applicable to this native player. Failure handling is present in the save/session layer and surfaces concise status text, but the presentation of those states remains weak.

---

## Files Audited

- `src/player/main.c` — window creation, integer-scaled frame rendering, title formatting, F1 help, battery status, and transition controls.
- `src/player/limitations.h` — player-facing battery and platform limitation copy.
- `src/player/session.c` and `src/player/session.h` — save outcomes and lifecycle states feeding player status.
- `tests/player/test_limitations.c` — asserted limitation wording.
- `.planning/phases/GB-04-mbc1-and-safe-battery-continuation/04-CONTEXT.md` — UX and persistence decisions, especially D-09 through D-13.
- `.planning/phases/GB-04-mbc1-and-safe-battery-continuation/04-01-PLAN.md` through `04-07-PLAN.md` and matching summaries — phase intent and delivered scope.
