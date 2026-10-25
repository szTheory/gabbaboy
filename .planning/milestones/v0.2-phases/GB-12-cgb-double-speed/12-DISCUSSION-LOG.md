# Phase 12: CGB Double Speed - Discussion Log

> **Audit trail only.** Do not use as input to planning, research or execution agents.
> Decisions are captured in CONTEXT.md. This log keeps the alternatives that were considered.

**Date:** 2026-10-13
**Phase:** 12-CGB Double Speed
**Areas discussed:**
- switch sequence and pause
- clock domains and model gates
- oracles and fixtures
- host API, player and docs
- cross-emulator gap sweep
- robustness, security and verification automation
- adversarial review of the draft

**Mode:** advisor fan-out with auto-follow, per the owner's standing instruction.
- The owner re-pasted the "fan out, adversarial pass, synthesize, auto-follow; prefer copy over dependency; primary sources" boilerplate while the fan-out was running. A sixth lens (robustness, security and verification automation) was added in response.
- No per-area questions were asked.
- Calibration tier: `minimal_decisive` (USER-PROFILE: opinionated, technical).

---

## A. Switch sequence

| Option | Description | Selected |
|--------|-------------|----------|
| SameBoy `stop()` decision table (held button, pending IRQ, switch plus stall) | Matches AGE hardware rows where they discriminate; the rest is ORACLE_SAMEBOY, tagged UNKNOWN | ✓ |
| mGBA/ares instant toggle, no stall | Fails AGE `spsw-div`, `spsw-tima` and `spsw-stop-prefetch`; contradicts success criterion 2 | |
| Keep fail-closed (`bus_unsupported`) | Does not meet the phase goal | |
| Held button: switch anyway (gap sweep) | No source supports it | |
| Held button: cancel, no stall, no sleep (first draft) | Corrected by the adversarial review: SameBoy enters HALT | (amended) |

## B. Pause length and model

| Option | Description | Selected |
|--------|-------------|----------|
| 0x20008 T at the destination speed, pinned as the DIV-reset-to-resume distance | AGE TIMA `$80` and `spsw-div` (hardware); SameBoy; Gambatte agrees for switches to normal | ✓ |
| Pan Docs 2050 M (8200 T), DIV frozen | Refuted by AGE hardware rows; 8200 = `0x2008` looks like a dropped digit | |
| Fixed, non-wakeable stall | Deterministic, but contradicts every source that models the pause | |
| Wakeable stall (an interrupt ends it) | SameBoy, plus AGE `caution/` with IME = 1 | ✓ |
| Atomic long instruction | 262160 half-dots exceeds a frame budget, so it never completes | |
| Stall stepped by `min(budget, stall, event)` | Wake time would depend on where the host cuts the budget | (rejected in review) |
| Separate stall branch with the halt-branch shape, M-cycle steps | Partition-invariant; reports BUDGET, not HALTED_IDLE | ✓ |
| Reuse `halted = 1` (SameBoy/Gambatte representation) | The HALTED_IDLE reason and halt-bug handling would leak in | |

## C. Clock domains and gates

| Option | Description | Selected |
|--------|-------------|----------|
| `cpu_ticks` scaling; the APU tap moves to bit 13; CPU-side countdowns in T-ticks | D-070, Pan Docs Audio, SameBoy `timing.c` | ✓ |
| Rescale the whole machine | Breaks PPU/APU rates | |
| Keep the half-dot reload/serial countdowns | Leaves fractional remainders at a switch | |
| Resolve, reassign or expected-fail every `research:12` gate; add a `cpu_ticks` scaling row | Rule R2 requires every model difference to be declared | ✓ |

## D. Host surface

| Option | Description | Selected |
|--------|-------------|----------|
| No ABI change; KEY1 bit 7 is the truth | Matches SameBoy (no public getter) | ✓ |
| A `gbb_info` field or getter | One-way ABI that no CGB-06 behaviour needs | (deferred) |
| A new stop reason `GBB_STOP_SPEED_SWITCH` | A switch is not an error; it would force every host loop to handle it | |
| Player unchanged, enforced by a smoke test with digests and mutants | | ✓ |

## E. Oracles and fixtures

| Option | Description | Selected |
|--------|-------------|----------|
| 13 AGE ROMs (speed-switch, ds STAT, single-speed controls) | Rights-clear (MIT, CC0 font) and exactly the roadmap list | ✓ |
| All 50 AGE ROMs | Mostly the Phase 14 corpus | |
| A digest-only local runner | No required-CI evidence | |
| Gambatte `speedchange` | GPL-2.0, CGB-C results | |
| Original per-scanline ROM with a host-recomputed verdict from first principles | | ✓ |
| A new dispositions JSON with signature and flip rule | | ✓ |

## F. Verification automation

| Option | Description | Selected |
|--------|-------------|----------|
| A full stride-8 interior partition sweep | About 8 minutes per scenario in the normal build; does not fit ASan | (rejected in review) |
| Boundary windows plus fixed interior points plus 256 seeded cases, with a per-test cap | | ✓ |
| A `slow` label tier | No infrastructure exists for it | |
| 16 mutants in at most 6 builds, anchors matched exactly once | | ✓ |
| A fuzz `cgb_speed` mode with positive-reach controls | | ✓ |

## Adversarial review

The review amended D-02 (held button → HALT; case-2 basis), D-04, D-05 (Gambatte asymmetry; the binding DIV-reset-to-resume distance; SameBoy freeze), D-06 (M-cycle steps), D-08, D-09, D-10, D-12, D-13, D-19, D-21, D-22 (line bounds were off by 2×), D-25, D-26, D-27 and D-29. It added D-34 to D-36.

## Claude's Discretion

- Internal names.
- The fixture layout.
- Mutant build merging.
- Plan granularity.

## Deferred Ideas

- Phase 13: HDMA across the stall.
- Phase 14: DMG STOP wake, `spsw-ch2-lc-delay`, the SameSuite PCM ROMs, CGB mode-3 length and the STOP OAM bug.
- v0.3: save-state fields.
- Future: a public speed getter.
