# Phase 10: CGB Profile, Banking and Register Visibility - Discussion Log

> **Audit trail only.** Do not use as input to planning, research or execution agents.
> Decisions are captured in CONTEXT.md. This log preserves the alternatives considered.

**Date:** 2026-10-12
**Phase:** 10-CGB Profile, Banking and Register Visibility
**Areas discussed:** profile/mode API, post-boot and visibility with the model-gate audit, banking/echo/DMA source, half-dot ADR and benchmark, gap sweep.

**Mode:** advisor fan-out with auto-follow, per the owner's standing instruction. The owner re-pasted the "fan out, adversarial pass, synthesize, auto-follow; prefer copy over dependency; primary sources" boilerplate during this discussion, and a fifth gap-sweep researcher was added in response. No per-area questions were asked. The calibration tier was `minimal_decisive` (USER-PROFILE: opinionated, technical).

---

## A. Profile selection and the model/mode API

| Option | Description | Selected |
|--------|-------------|----------|
| A. One sized `gbb_info` struct, filled by both `gbb_probe_rom(profile, ...)` and `gbb_get_info` | Single derivation; `struct_size` allows growth; no new error codes | ✓ |
| B. Scalar getters plus a separate probe struct | Matches the ARCHITECTURE sketch; more symbols; probe and instance can diverge | |

**Choice:** A. PGB-flagged headers were reconciled toward rejection on the CGB profile (see Conflicts), which adds one appended error code.
**Notes:** Peers (SameBoy model at init; mGBA and Gambatte autodetect `$143` bit 7 or a forced model) were checked from memory only.

## B. Post-boot state, the visibility matrix and the model-gate audit

| Option | Description | Selected |
|--------|-------------|----------|
| A. C tables as the single source of truth, a doc mirror with a diff test, and a stdlib scanner with negative controls | Docs cannot drift; provenance is checked per cell | ✓ |
| B. Docs-only tables plus grep tag checks | Smaller `reset_state` diff; silent drift (V2-20) | |

**Draft post-boot table (researcher):**
- Compat CPU row: A=11 F=80 B=00 C=00 D=00 E=08 H=00 L=7C. Mooneye `boot_regs-cgb`, hardware.
- CGB CPU row: A=11 F=80 B=00 C=00 D=FF E=56 H=00 L=0D. Pan Docs.
- P1: `$FF` on CGB (hardware compat). SC: compat `$7E`, CGB `$7F`. DMA: `$00`. KEY1: CGB `$7E`, compat `$FF`. VBK: `$FE` in both.
- SVBK: CGB `$F8`, compat `$FF`. OPRI: CGB `$FE`, compat `$FF`. BCPS/OCPS: compat `$C8`/`$D0`.
- FF72-75: `00 00 00/FF 8F`. FF76/77: hardware `$00`, deferred.
- DIV phase: compat from `boot_div-cgbABCDE`.
- LY and STAT: no oracle (policy).

## C. Banking, echo and DMA source

| Option | Description | Selected |
|--------|-------------|----------|
| A. `vram[2][8192]`, `wram[8][4096]`; DMG pins `wram_bank=1`, `vram_bank=0` | DMG layout identical; no per-access profile branch | ✓ |
| B. Flat arrays with offsets | Smaller diff; cross-bank PPU read risk (V2-21) | |

## D. Half-dot ADR and benchmark

| Option | Description | Selected |
|--------|-------------|----------|
| Keep the half-dot master clock; `cpu_ticks = t >> double_speed` | Exact at both speeds; zero DMG churn; SameBoy uses the same model | ✓ |
| Quarter-dot unit or speed multiplier | Rebaselines DMG / V2-03 failure | |
| Advisory interleaved A/B benchmark plus an automated digest/receipt self-test | No timing gate; no flakes | ✓ |
| Hosted timing gate | sd about 4% at n=10; flaky | |
| valgrind instruction-count proxy | New dependency; not a time measure | |

## E. Gap sweep

Recommendations adopted:
- Fail closed for unbuilt registers.
- `gbb_copy_frame` returns an error on the CGB profile.
- Keep the shared STOP/HALT path, tagged.
- Header validation unchanged.
- Runner model threading, which fixes the hard-coded `model=dmg-cpu-b`.
- Mooneye `C`-group-only admission.
- Fuzz and consumer parameterisation.
- Docs in the same PR.
- Wave order with the audit first.

---

## Conflicts reconciled (adversarial pass)

1. **VBK read in compat.** Banking researcher: `$FF` (V2-07 reading of Pan Docs) or `$FE` (SameBoy), undecided. Visibility researcher: Mooneye `boot_hwio-C`, a hardware test, expects `$FE`. **Resolved `$FE`**, because the hardware test outranks the prose generalisation.
2. **PGB `$143` (bit 7 with bit 2 or 3).** API researcher: run as CGB, flag OTHER. Visibility researcher and V2-06: reject. **Resolved: reject on the CGB profile only** with appended `GBB_UNSUPPORTED_EXECUTION_MODE`. The DMG profile is unchanged, since DMG ignores `$143`.
3. **DMG FF4C-FF7F.** Visibility researcher: change to `$FF` (hardware-correct per `unused_hwio-GS`). Gap sweep: the DMG row is untouched. **Resolved: unchanged (fail-closed)**, because the phase goal forbids DMG behaviour change. Deferred, and listed in the veto window.
4. **Unbuilt CGB registers.** Gap sweep: fail closed for all of them. Visibility researcher: store KEY1, HDMA1-4, BCPS/OCPS, OPRI, RP and FF72-75. **Resolved by rule:** implement only pure storage or constant reads pinned by hardware or Pan Docs with no later subsystem (KEY1 bit 0, HDMA1-4 sink, BCPS/OCPS, FF72-75, VBK, SVBK, KEY0). Fail closed where the effect or value belongs to a later phase or is disputed: HDMA5 start, BCPD/OCPD in CGB mode, OPRI, RP (`$3E` vs `$2E`), FF76/77, and STOP with KEY1 armed.
5. **RP CGB-E value.** Pan Docs `$3E` vs SameBoy-implied `$2E`, with no hardware oracle. **Resolved: `DEFERRED(14)`** rather than choosing a value.
6. **Benchmark comparison points.** The criterion names only the Phase 7 baseline. **Resolved:** baseline `5a55f19` is the headline, and Phase 9 `d7e2e0a` is added for attribution.

## Claude's Discretion

- Helper names, GATE numbering, the doc table markup and the fixture guest layout.
- The plan split. The suggested waves are recorded in CONTEXT.

## Deferred Ideas

- DMG FF4C-FF7F `$FF` and `unused_hwio-GS` admission (Phase 14 candidate).
- The CGB CPU/DMA separate-bus model.
- DMG OAM DMA E0-FF and ROM sources.
- RP and PCM12/34 (Phase 14).
- STOP, KEY1 switch and stall (Phase 12).
- HDMA (Phase 13).
- Palettes, OPRI and colour output (Phase 11).
- An instruction-count benchmark proxy.
- AGE LY/STAT ROMs (Phase 14).
