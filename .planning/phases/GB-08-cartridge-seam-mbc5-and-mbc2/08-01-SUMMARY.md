---
phase: 08-cartridge-seam-mbc5-and-mbc2
plan: 01
subsystem: cartridge
tags: [mapper-seam, mbc1, loader, differential]
requires: []
provides:
  - "Delimited Cartridge mapper section in src/core/gabbaboy.c (cart_kind, cart_state, type table, switch dispatch)"
  - "Reusable old-versus-new differential harness (--exclude-types)"
affects: [08-02, 08-03]
tech-stack:
  added: []
  patterns: ["static const type table looked up once at load", "switch (kind) dispatch, no function pointers"]
key-files:
  created:
    - .planning/phases/GB-08-cartridge-seam-mbc5-and-mbc2/differential/loader-mapper-diff.c
    - .planning/phases/GB-08-cartridge-seam-mbc5-and-mbc2/differential/run-differential.sh
  modified:
    - src/core/gabbaboy.c
key-decisions:
  - "Mapper section placed before the gbb_instance struct; its helpers take cart_state plus sizes instead of the instance so the whole section stays contiguous"
requirements-completed: [CART-01]
status: complete
duration: 1h 10m
completed: 2026-10-11
commits: 2
plan_head_before: 1a49a04f0726c028879135d0d4b8dd48ab685754
plan_head_after: 25e5d6e2639f27c668e263aeeed3dece7c01cfaa
actuals:
  tokens: 14000
  tasks: 3
  commits: 2
coverage:
  - deliverable: "Table-driven Cartridge mapper seam with no observable DMG change"
    verification:
      - {kind: command, ref: "run-differential.sh", status: pass}
      - {kind: command, ref: "ctest -R ^(cartridge_|battery_|loader_|mbc1_continuation|dmg_baseline)", status: pass}
    human_judgment: false
---

# Phase 8 Plan 01: Cartridge Seam Summary

All cartridge decisions in `src/core/gabbaboy.c` now go through one delimited "Cartridge mapper" section with a `cart_state` sub-struct, a static type table ($00-$03) and `switch (kind)` dispatch, with zero observed differences against 5673bed.

## Accomplishments

- Section holds `cart_kind` (CART_ROM_ONLY = 0, CART_MBC1), `cart_state` (fixed-width integers only), `cart_type_row` table with `has_timer` 0 everywhere, `cart_row_for_type`, `cart_reset_registers` (mapper registers only, safe on an unloaded instance) and the moved MBC1 bank/RAM helpers. `recognized_mbc1m_candidate` is byte-identical to 5673bed.
- read8/write8 keep branch order; only cartridge branches became `switch (m->cart.kind)`. Battery generation, `read_supported` (A000-BFFF window) and `has_battery_ram` read stored flags; `git grep 'cartridge_type == 0x03u' -- src` prints nothing.
- `validate_header` is table-driven with the D-05 precedence (early ceiling slot before UNSUPPORTED_CARTRIDGE; ROM-size code rejected before the shift). `gbb_load_rom` stays validate, allocate, commit.
- Differential harness committed under the phase directory (not a CTest).

## Evidence

- Differential: `cells=86016 lines=213114 old_sha256=d171c90db94218aa0378d457578657bd9e8bbdf94745f1a83f91f717307800b6 new_sha256=d171c90db94218aa0378d457578657bd9e8bbdf94745f1a83f91f717307800b6 differences=0` (86,016 loader cells; seeded xorshift32 MBC1 sequences for types $01-$03, ROM codes 0-6, RAM codes 0-3, 4096 steps each; MBC1M candidates at 512 KiB, 1 MiB, 2 MiB rejected with code 8 and previous ROM intact). Sanity: 35 grid cells load OK. A local ASan+UBSan build of the harness against the new core reproduced the same output digest (the phase1-asan preset is Linux-only and ran in CI).
- Frozen digest: `correctness_digest_fnv1a64=4c7a57ff3d50d228` in all 5 after runs; `verify-dmg-baseline.sh` prints `baseline status=pass`.
- Local ctest: 261/261 pass; `verify-test-inventory.sh --installed` verified 261 cases, none skipped. Target subset (cartridge_, battery_, loader_, mbc1_continuation, dmg_baseline) 47/47 pass.
- Timing (advisory only): measure_core --no-trace, 5 runs each. Before (5673bed) elapsed_ns median 22.46 ms, range 21.87-25.50 ms. After median 21.45 ms, range 20.91-21.65 ms. This is not a performance claim: the 32 KiB tracer exercises only the ROM-only kind and no baseline workload exercises MBC1 reads.
- Purity: `git diff --name-only main...HEAD` lists only `src/core/gabbaboy.c` and `.planning/` paths; tests/, fixtures/, cmake/, .github/, CMakeLists.txt, include/ and tests/baseline untouched; `grep -c 'if ((m->joypad_select & 0x20u) == 0)'` is 1.

## Exact-head CI

Draft PR: https://github.com/szTheory/gabbaboy/pull/64 (branch gsd/phase-08-cartridge-seam-mbc5-and-mbc2, draft).
Head SHA: 25e5d6e2639f27c668e263aeeed3dece7c01cfaa. Run (pull_request event): https://github.com/szTheory/gabbaboy/actions/runs/38146578485, attempt 1. `wait-exact-head-ci.py` printed PASS with all eight `--require` names.

| Job | Conclusion |
|-----|------------|
| native-linux-x64 | success |
| native-macos-arm64 | success |
| native-windows-x64 | success |
| linux-asan-ubsan | success |
| cmake-floor-3.25.3 | success |
| player-gate | success |
| macos-player-package | success |
| required-native | success |

`baseline status=pass` observed in the native-linux-x64, native-macos-arm64 and native-windows-x64 logs. Docs-only commits pushed after this head (SUMMARY/STATE) change no code; a fresh CI run on them is not part of this evidence.

## Task Commits

1. Task 1 (tracer, seam): 2cfdc77
2. Task 2 (differential harness): 25e5d6e. validate_header was table-ized in Task 1's commit because the row lookup was needed to fill `cartridge_info`; Task 2 therefore added only the harness files.
3. Task 3 (purity, push, PR, CI): no file change.

## Deviations from Plan

**1. [Rule 3 - Blocking] ASan preset unusable on macOS.** `phase1-asan` is Linux-only (CMakeLists.txt:8), and the stale ignored `build-asan` cache (created under a different path) was removed. Substituted a local `-fsanitize=address,undefined` build of the differential harness against the new core (clean, identical digest); the Linux ASan/UBSan job passed in CI.

**2. [Rule 3 - Blocking] Local inventory check needs `--installed`.** The local build tree has the install prefix configured, so `verify-test-inventory.sh` was run with `--installed` per the plan's own condition.

**3. Task split.** Table-driven validate_header landed in Task 1 rather than Task 2 (see Task Commits). No behavioural impact.

**Total deviations:** 3 (2 blocking-environment, 1 ordering). **Impact:** none on the evidence.

## Known Stubs

None. `has_rumble`, `rumble_on`, `rumble_changes`, `ram_bank` and `has_timer` fields exist for Plans 08-02/08-03 and Phase 9; they are intentionally unused in this plan.

## Threat Flags

None.

## Self-Check: PASSED

- FOUND: src/core/gabbaboy.c, differential/loader-mapper-diff.c, differential/run-differential.sh
- FOUND commits 2cfdc77 and 25e5d6e (ancestors of HEAD)
