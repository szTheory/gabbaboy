# Phase 8: Cartridge Seam, MBC5 and MBC2 - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-10-11
**Phase:** 08-cartridge-seam-mbc5-and-mbc2
**Areas discussed:** Mapper seam and no-change proof; Mooneye mbc2/mbc5 admission and 8 MiB policy; MBC2 semantics and battery image; MBC5 behaviour, rumble API and original fixtures

**How the decisions were made:**
- All four areas were selected under the owner's standing fan-out, auto-follow instruction, recorded in memory from Phases 06.1 and 7.
- Each area was researched by a parallel advisor researcher at the `minimal_decisive` tier, with multi-lens and adversarial instructions.
- The Mooneye researcher rebuilt all 28 `emulator-only/mbc{1,2,5}` derivatives in scratch to confirm sizes, digests and that the patch applies.
- Recommendations were reconciled into one set. Nothing was asked area by area, and no owner-only question was raised.

---

## Mapper seam and no-change proof

| Option | Description | Selected |
|--------|-------------|----------|
| A. Delimited section in `gabbaboy.c` | `cart_state` + `cart_kind` + static type table + `switch`; no build edits | ✓ |
| B. New `src/core/cartridge.c/.h` | ARCHITECTURE.md proposal; must be wired into six single-TU build sites (incl. JOYP mutant text-copy) | |

**Choice:** A, auto-followed. The seam plan touches only `gabbaboy.c`. The no-change proof combines the unchanged tests, fixture and baseline, a one-off old-versus-new loader and MBC1 differential, and advisory `measure_core` with the frozen correctness digest. New CTests need no baseline row because the ledger flags only removals. Region-decode of `read8` is deferred.

## Mooneye mbc2/mbc5 admission and 8 MiB policy

| Option | Description | Selected |
|--------|-------------|----------|
| A. Extend `fixtures/mooneye/` (3 → 18) | Changes pinned manifest digest, ledger lines, cpu/timer-only verifier | |
| B. Sibling `fixtures/mooneye-mbc/` | Own manifest and denominators; references parent patch/font by digest | ✓ |
| C. Generalised suite verifier now | Refactors frozen v0.1 verification | |

| Option (8 MiB ROM) | Description | Selected |
|--------|-------------|----------|
| Commit raw | ~13 KiB packed, offline CTest | ✓ |
| Regenerate at build | Needs network/toolchain in CTest | |
| Compressed in-tree | Extra codec and digest relationship | |

**Choice:** B with raw commit, install exclusion proven by a scan with a planted-payload self-test, MBC1 backfill deferred.

## MBC2 semantics and battery image

| Option | Description | Selected |
|--------|-------------|----------|
| Store canonical `0xF0 \| nibble`, export 512 B with `$F` nibble, normalise on import | Hardware-backed by Mooneye `ram` round 6; plain-copy export | ✓ |
| Store raw, mask on read/export | Two masking sites; invisible-bit generation bumps | |
| Reject non-canonical imports | Rejects real third-party saves | |

| Option (Phase 8 player) | Description | Selected |
|--------|-------------|----------|
| Run without persistence and say so | No save file touched; explicit status | ✓ |
| Refuse to load | Contradicts "caller can run" | |
| Widen envelope now | Takes Phase 9 CART-06 | |

## MBC5 behaviour, rumble API and original fixtures

| Option | Description | Selected |
|--------|-------------|----------|
| `gbb_rumble_state(on, changes)` + `GBB_NO_RUMBLE` | Smallest ABI step, mirrors battery generation | ✓ |
| Fold into cartridge info / probe | Commits a struct layout before CGB fields exist | |
| Event/diagnostic stream | Larger surface, queue bounds | |

| Option (fixtures) | Description | Selected |
|--------|-------------|----------|
| RGBDS guest + in-memory 8 MiB inflation for `$1FF` | Original fixture via real CPU path, no repo bloat | ✓ (plus C unit tests) |
| C unit tests only | Weaker as an original-fixture claim | |
| Commit an 8 MiB original ROM | Repo bloat, install risk | |

**Reconciled conflicts:**

| Topic | Proposed by | Adopted | Why |
|-------|-------------|---------|-----|
| Where MBC5 lives | MBC5 research: beside MBC1 without extraction | Seam research: in-file seam first | CART-01 requires the seam; roadmap orders it first |
| ROM bound | Mooneye research: global 8 MiB, MBC1 oversize changes error class | Seam research: 8 MiB ceiling, per-type byte max keeps `ROM_TOO_LARGE` for non-MBC5 | "No observable change"; fuzz test stays untouched |
| MBC2 oversize error | FEATURES.md: `UNSUPPORTED_CARTRIDGE_VARIANT` | `UNSUPPORTED_ROM_SIZE` | Consistent with MBC1 size mapping; VARIANT reserved for wiring |

## Claude's Discretion

- Names and table layout; plan split around the seam-first rule; scan script language; feasibility of the ninth-bit core mutant.

## Deferred Ideas

- Mooneye MBC1 backfill.
- `cartridge.c` file split.
- `read8` region decode.
- Generalised suite verifier.
- Player 8 MiB cap and MBC2/MBC5 persistence (Phase 9).
- `gbb_probe_rom` and `gbb_get_cartridge_info`.
- Host haptics.
- Packed MBC2 saves.
