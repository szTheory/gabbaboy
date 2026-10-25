# Phase 9: MBC3, Deterministic RTC and Cartridge Persistence - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-10-11
**Phase:** 09-mbc3-deterministic-rtc-and-cartridge-persistence
**Areas discussed:**
- MBC3 mapping and loader matrix
- RTC core model and rtc3test gate
- RTC public API and battery block
- Player envelope and continuation

**How the decisions were made:**
- All four areas were selected under the owner's standing fan-out, auto-follow instruction.
- Each area went to a parallel advisor researcher at the `minimal_decisive` tier, with instructions to look from several angles and to argue against its own recommendation.
- The RTC researcher prototyped the model on a scratch copy and passed rtc3test v004 23/23. It also ran mutation controls.
- The MBC3 researcher ran MagenTests on the current core and found that the first frames are white whatever the result, so an early sample proves nothing.
- The API researcher raised the signed catch-up prototype as a possible owner question. It was judged an append-only addition (D-17) and auto-followed, like the Phase 8 rumble API.

---

## MBC3 mapping and loader matrix

| Option | Description | Selected |
|--------|-------------|----------|
| A. Size-class errors only | MBC30 indistinguishable from a corrupt header | |
| B. MBC30 signature gets `UNSUPPORTED_CARTRIDGE_VARIANT` after the checksum; other sizes keep size errors; MBC3 ceiling 4 MiB | Matches Phase 8 D-20 | ✓ |

| Option (`$04-$07`, `$0D-$FF` bank values) | Description | Selected |
|--------|-------------|----------|
| Unmapped (`$FF`, writes ignored) | Exact Pan Docs decode; labelled a software-model decision | ✓ |
| Alias `v & 3` | SameBoy-like; can corrupt a real bank | |

| Option (MagenTests oracle) | Description | Selected |
|--------|-------------|----------|
| Public-API C test, ≥10 frames, all shade 0, paired `$149=3` black control | Not vacuous | ✓ |
| Acceptance-harness frame digests | A white digest matches blank pre-LCD frames | |

| Option (CART-05 matrix) | Description | Selected |
|--------|-------------|----------|
| One table-driven test with an independent oracle and must-be-OK rows | Few inventory lines | ✓ |
| One CTest per combination | Thousands of inventory lines | |

**Choice:** auto-followed. WR-02 is split: the core sweep goes with CART-05 and the player drift guard with CART-06. Fuzzing uses a synthesised-length mode against one 8 MiB+1 buffer.

## RTC core model and rtc3test gate

| Option | Description | Selected |
|--------|-------------|----------|
| Lazy sync anchored on `time_half_dots` | No hot-loop cost; correct across the STOP fast-forward | ✓ |
| Tick in `advance_devices_to` | Hot-loop cost; misses skipped STOP time | |

| Option (rtc3test oracle) | Description | Selected |
|--------|-------------|----------|
| White-box single-TU test reading the BG tile map, with pinned numeric transcript | Independent verdict; catches 0.1% rate error | ✓ |
| Runner frame-digest with input script | Needs a runner extension; regression-class only | |
| `$FF80` / patched hook | No verdict / cannot patch pinned ROM | |

| Option (no host clock proof) | Description | Selected |
|--------|-------------|----------|
| Source include/denylist plus object undefined-symbol scan plus negative control | Two layers | ✓ |
| Either layer alone | Gaps | |

**Choice:** auto-followed. The adversarial pass changed one thing: **the latch does not bump the battery generation**, overriding ARCHITECTURE §180. Otherwise a game that polls a latched clock would defeat the quiet-period save.

## RTC public API and battery block

| Option | Description | Selected |
|--------|-------------|----------|
| `int64_t` elapsed time, negative rejected | Rollback cannot wrap into a huge advance | ✓ |
| `uint64_t` elapsed time | Cast footgun on rollback | |

| Option | Description | Selected |
|--------|-------------|----------|
| Unified image: RAM followed by a 21-byte RTC block | One path, one generation | ✓ |
| Separate `gbb_copy_rtc`/`gbb_import_rtc` | Skew risk, more surface | |

**Choice:** auto-followed. The corrupt-block case reuses `GBB_INVALID_ARGUMENT`, so `GBB_NO_RTC` is the only new enum value.

## Player envelope and continuation

| Option | Description | Selected |
|--------|-------------|----------|
| v1 kept for MBC1 `$03`, v2 for every other battery type, both loaded forever | No downgrade hazard | ✓ |
| v2 for all new saves | A v0.1 player would treat the file as corrupt | |

| Option (clock injection) | Description | Selected |
|--------|-------------|----------|
| `--clock-unix` only in smoke/child modes, plus a pure policy function | Explicit, testable on every OS | ✓ |
| Environment variable | Ambient state | |

| Option (v0.1 proof) | Description | Selected |
|--------|-------------|----------|
| Committed envelopes written by the real v0.1 player, read and byte-identical re-write tests | Tests what v0.1 actually wrote | ✓ |
| Hand-built loader bytes | Tests only our reading of the spec | |

**Choice:** auto-followed. Rollback policy: no advance, and the next save re-stamps the time (as BGB and VBA-M do). SameBoy's reset and mGBA's backwards move were rejected.

**Reconciled conflicts:**

| Topic | Proposed by | Adopted | Why |
|-------|-------------|---------|-----|
| Catch-up argument type | Player research and ARCHITECTURE: `uint64_t` | API research: `int64_t`; player clamps to `INT64_MAX` | Rollback must not become a huge advance |
| Latch state in block | API research: 0/1 "armed" byte | RTC research: full `latch_prev` byte | Same information, exact |
| Latch bumps generation | ARCHITECTURE §180: yes | RTC research: no | Polling games would defeat the quiet-period save |
| `$0F` battery with no RAM | MBC3 research flagged it | API research: unified image (the block alone) | `has_battery_ram` generalised |

## Claude's Discretion

- Status wording, flag name, helper names, plan split and wave order.

## Deferred Ideas

- BGB/VBA-M footer adapter
- Mealybug `mbc3_rtc` (G1)
- gbclock (G3)
- CGB double-speed RTC assertion (Phase 11)
- Recovering time spent paused while the player is open
- Probe/info `has_rtc`
- Phase 8 carry-overs
- Runner receipts for rtc3test
