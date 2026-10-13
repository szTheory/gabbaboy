---
phase: 11-cgb-colour-rendering-and-player-colour
plan: 11
subsystem: external-cgb-ppu-suite-records
tags: [age, mealybug, acid2, d-09, d-20, d-24, dispositions, g1]
status: complete
requires:
  - phase: 11-cgb-colour-rendering-and-player-colour
    provides: "11-09 runner RGB555 failure PPM path, 11-10 D-20 AGE statement"
provides:
  - "tests/external/cgb-ppu-dispositions.json: six AGE m3-bg-* expected-unsupported rows and 30 Mealybug m3_* unsupported-model rows with pins"
  - "Offline verifier with docs mirror and tracked-file checks, plus a mutated-record negative control"
  - "Digest-pinned optional local acid2 runner and manifest, with synthetic self-tests in required CI"
affects: [11-12, 11-15]
requirements-completed: []
plan_head_before: b05d5ca80d6ef4d22f8bf9a6e87aae6e8e8408ce
plan_head_after: 15c2248be890636a3844b4aa78f8acf8b0be1d41
actuals:
  tokens: 30000
  tasks: 2
  commits: 2
coverage:
  - id: C1
    description: "The six AGE m3-bg-lcdc and m3-bg-scx variants carry expected-unsupported with reason mode-3-pixel-timing, every Mealybug m3_* case at the pinned tree carries unsupported-model, the docs mirror equals the record, and no tracked fixture carries such a ROM or image"
    requirement: CGB-04
    human_judgment: false
    verification:
      - kind: integration
        ref: "cgb_external_dispositions"
        status: pass
  - id: C2
    description: "A changed AGE reason is rejected by the verifier with disposition-mismatch"
    requirement: CGB-04
    human_judgment: false
    verification:
      - kind: integration
        ref: "cgb_external_dispositions_mutated"
        status: pass
  - id: C3
    description: "The local acid2 runner decodes and compares synthetic data correctly: PNG round trip, equal frames, a one-pixel mismatch reported as pixels=1, and a fake ROM refused"
    requirement: CGB-04
    human_judgment: false
    verification:
      - kind: unit
        ref: "cgb_acid2_local_selftest"
        status: pass
  - id: C4
    description: "An unpinned ROM is refused with exit 2 before anything is run or decoded"
    requirement: CGB-04
    human_judgment: false
    verification:
      - kind: integration
        ref: "cgb_acid2_local_refuses_unpinned"
        status: pass
---

# Phase 11 Plan 11: External CGB PPU suite records and local acid2 runner Summary

Machine-checked records that AGE m3-bg-* are expected-unsupported (mode-3 pixel timing) and Mealybug m3_* are unsupported-model (no CGB-E expectation), asserted offline with a mutated-record control, plus a SHA-256-pinned optional local acid2 runner; no third-party bytes are tracked.

## Accomplishments

- `tests/external/cgb-ppu-dispositions.json` enumerated from the pinned trees via the read-only tree API: AGE at `1f5bc10e` gives exactly six `m3-bg-{lcdc,scx}` x `{cgbBCE,ds-cgbBCE,nocgb-ncmBCE}` expected images; Mealybug at `70e88fb9` gives 30 `src/ppu/m3_*.asm` sources (matches the planned 30). Both repositories are MIT licensed at the pin; vendored is false and Mealybug carries rights gate G1.
- `tests/scripts/verify-external-dispositions.py` checks the case set, dispositions, reasons, the stored upstream count, the `docs/cgb-profile.md` mirror block and `git ls-files` for stray ROMs or images. It reads no ROM bytes and uses no network.
- `docs/cgb-profile.md` gained "External CGB PPU suites not run in Phase 11" and "Optional acid2 local runs".
- `tests/acid2/manifest.json` pins cgb-acid2 v1.1 and dmg-acid2 v1.0 ROM and reference SHA-256 values (downloaded 2026-10-12 into a scratch directory outside the repository, never committed).
- `tests/scripts/run-acid2-local.py` refuses unpinned inputs (exit 2), runs the ROM to its `ld b,b` through `gabbaboy-runner --failure-dir`, and compares the PPM with the decoded reference. A local run against the real pinned upstream files (outside the repository) matched on both: cgb-acid2 on the CGB profile and dmg-acid2 on DMG-CPU-B reported `acid2 result=match`. This is a differential check against upstream reference images, recorded here as an observation and not as CI evidence.

## Deviations from Plan

**1. [Rule 1 - Bug] PNG decoder colour types.** The plan specified 8-bit RGB/RGBA only. The pinned references are an 8-bit palette PNG (cgb-acid2) and a 2-bit greyscale PNG (dmg-acid2), which that decoder would have rejected. The decoder now also accepts colour types 0, 3 and 4 at the bit depths PNG allows for them, still bounded to 160x144 non-interlaced with CRC and size checks. Commit 15c2248.

**2. [Rule 3 - Blocking] ld b,b oracle instead of a fixed t.** The plan suggested `frame-digest@t=<n>` with a settle count in the manifest. The runner already supports `frame-digest@ldbb`, which captures the frame at the ROM's own completion signal, so the manifest records only `ldbb_budget_half_dots` (4213440). Commit 15c2248.

**3. Mealybug count.** The pinned tree shows 30 `m3_*` sources, equal to the planned count.

## Verification

- `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error`: 677/677 tests passed (about 180 s). The `phase1-asan` preset is Linux-only and is not run on this host.
- `git ls-files -- 'fixtures/*m3-bg-*' 'fixtures/*m3_*'` and `git ls-files -- '*acid2*.gb' '*acid2*.gbc' '*acid2*.png'` print nothing.
- No edit touched `src/core/gabbaboy.c`, `src/runner/*` or `src/accept/*`, so the DMG baseline script was not re-run for this plan.

## Known Stubs

None.

## Threat Flags

None. The new surface (a PNG decoder on user-supplied local files) is the one the plan's threat model T-11-19/T-11-20 covers: pins are checked before decode and the decoder is bounded.

## Self-Check: PASSED

- FOUND: tests/external/cgb-ppu-dispositions.json, tests/scripts/verify-external-dispositions.py, tests/scripts/run-acid2-local.py, tests/acid2/manifest.json
- FOUND commits 82192e5 and 15c2248
