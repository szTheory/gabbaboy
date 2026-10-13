# Phase 11: CGB Colour Rendering and Player Colour - Discussion Log

> **Audit trail only.** Do not use as input to planning, research or execution agents.
> Decisions are captured in CONTEXT.md. This log keeps the alternatives that were considered.

**Date:** 2026-10-12
**Phase:** 11-CGB Colour Rendering and Player Colour
**Areas discussed:**
- PPU rendering, priority and OPRI
- palette RAM
- RGB555 API and compat palette
- oracles and fixtures
- player and smoke
- gap sweep
- cross-emulator pixel pipeline
- adversarial review of the draft

**Mode:** advisor fan-out with auto-follow, per the owner's standing instruction.
- The owner re-pasted the "fan out, adversarial pass, synthesize, auto-follow; prefer copy over dependency; primary sources" boilerplate while the fan-out was running. In response, a seventh lens (the cross-emulator pixel pipeline) was added, along with an adversarial review of the synthesised draft.
- No per-area questions were asked.
- Calibration tier: `minimal_decisive` (USER-PROFILE: opinionated, technical).

---

## A. Pixel path

| Option | Description | Selected |
|--------|-------------|----------|
| A. Dual store, resolved per dot | Keeps the `uint8_t` DMG shade buffers and adds `uint16_t` RGB555 buffers written only on CGB; resolved against live CRAM | ✓ |
| B. Single RGB555 buffer; shades derived from it | One buffer, but DMG byte-identity would depend on an invertible map; rebaselines DMG | |
| C. Per-pixel tuple resolved at copy time | Smallest storage; breaks per-scanline palette effects; no peer does it | |
| D. A plus a hoisted model check | Only with benchmark evidence | (deferred, D-04) |

## B. Priority, attributes and OPRI

| Option | Description | Selected |
|--------|-------------|----------|
| Compositor-level CGB path with a pure `ppu_compose_cgb` | Low DMG risk; exhaustively testable | ✓ |
| A FIFO carrying full metadata, SameBoy-style | Closest to hardware; rewrites the DMG fetcher | |
| OPRI live at render time | Effect unverified after boot | |
| OPRI stored, no effect; ordering latched to the mode | Matches SameBoy's read-back and Pan Docs' "no effect" | ✓ (amended by the adversarial review) |

## C. Palette RAM

| Option | Description | Selected |
|--------|-------------|----------|
| A blocked write drops data but increments; plain mode-3 lockout | Pan Docs (explicit) and SameBoy | ✓ |
| A blocked write without increment | Contradicts both sources | |
| SameBoy's lock edges | No hardware oracle; recorded as UNKNOWN | |

## D. API and compat palette

| Option | Description | Selected |
|--------|-------------|----------|
| `gbb_copy_frame_rgb555` with byte pitch, native uint16 values, DMG profile unsupported | Symmetric with `gbb_copy_frame` and with SDL/libretro | ✓ |
| Pixel-unit pitch | Type-safe, but a unit footgun next to `gbb_copy_frame` | |
| Host RGB encode callback (SameBoy) | Breaks bounded, no-callback copies | |
| RGB555 on the DMG profile through the compat palette | One host path, but couples the DMG profile to a palette | (deferred; additive) |
| Compat palette written into CRAM on set | Mutates emulation state at a host-chosen moment | (rejected by the adversarial review) |
| Compat palette as instance configuration read at resolve time | Not emulation state; DMG function untouched | ✓ |

## E. Oracles

| Option | Description | Selected |
|--------|-------------|----------|
| Truth table, three MagenTests ROMs and original fixtures, all required; acid2 optional-local | Clears G1 and G4 | ✓ |
| Also vendor acid2 | Blocked by G1 | |
| AGE `m3-bg-*` required | Out of colour scope; needs CGB mode-3 timing | (expected-unsupported) |

**Finding:** AGE has no CGB colour, attribute or priority ROMs. The success criterion's "AGE/MagenTests" wording is met by MagenTests plus originals, and the deviation is recorded.

## F. Player

| Option | Description | Selected |
|--------|-------------|----------|
| Expand to the existing RGBA32 texture | DMG path untouched; no dependence on renderer format support | ✓ |
| `SDL_PIXELFORMAT_XBGR1555` upload | Renderer support varies; needs a second texture | |
| Default `--model auto` | Moves dual-mode Libbet (the Phase 7 baseline) onto CGB | (rejected by the adversarial review) |
| Default `--model dmg`; `auto` opt-in | Keeps the baseline; Phase 15 may flip it | ✓ |

---

## Conflicts reconciled

1. **When colour is resolved.** The PPU researcher said "compose at output"; the pipeline researcher said "resolve per dot". In GabbaBoy the compositor runs per dot, so the two agree. **Resolved: per dot, against live CRAM.**
2. **RGB555 on the DMG profile.** The API researcher said yes; the PPU and gap researchers said unsupported. **Resolved: unsupported.** It is narrow and symmetric, and widening later is additive.
3. **Compat palette in CRAM vs mapped at output.** The palette and PPU researchers wanted CRAM. The adversarial review found that a host set would then mutate emulation state. **Resolved: instance configuration read at resolve time.**
4. **OPRI.** The draft said "writes ignored, per SameBoy". The review read SameBoy `memory.c`: the register is stored but has no effect. **Resolved: stored and read back, with no priority effect.**
5. **Player default.** The draft said `auto`. The review found Libbet has `$143=$80`. **Resolved: `dmg`.**
6. **LCD off.** The draft said "clear both buffers". The DMG code clears only the working buffer. **Resolved: mirror the DMG policy, with white `0x7FFF`.**
7. **Pitch.** Pixels vs bytes. **Resolved: bytes, with alignment and even-pitch validation.**

## Claude's Discretion

- The compat ramp values within the D-18 rule.
- Internal names.
- Fixture layout and frame counts.
- Expansion helper sharing.
- Plan granularity.

## Deferred Ideas

- CGB mode-3, WX and CRAM lock-edge quirks (Phase 14).
- Player default `auto` (Phase 15).
- A player palette flag.
- Colour correction.
- G1 clearance.
- RGB555 on the DMG profile.
