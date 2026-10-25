---
phase: 08-cartridge-seam-mbc5-and-mbc2
plan: 05
subsystem: testing
tags: [mooneye, mbc5, mbc2, fixtures, runner, wla-dx]

requires:
  - phase: 08-cartridge-seam-mbc5-and-mbc2
    provides: MBC5 and MBC2 mapper in the core (plans 08-02, 08-03)
provides:
  - 15 pinned Mooneye emulator-only mbc2/mbc5 derivative ROMs with sibling manifest and notices
  - Multi-suite headless runner (suite_def selection by manifest digest, per-case size_bytes, bounded fail PC array)
  - tests/scripts/reproduce-mooneye-mbc.sh (--build, --compare, --facts)
  - Measured suite receipt mbc2 7/7 and mbc5 8/8
affects: [08-06 sibling verifier and CTests, 08-07 hosted Linux digest match]

actuals:
  tokens: 100000
  tasks: 2
  commits: 2

tech-stack:
  added: []
  patterns:
    - "Runner admits a suite by SHA-256 of raw manifest bytes via a static suite_def table"
    - "mbc_cases[] rows are one per line, starting with the id literal, so a CMake check can parse them"

key-files:
  created:
    - fixtures/mooneye-mbc/manifest.json
    - fixtures/mooneye-mbc/LICENSE.txt
    - fixtures/mooneye-mbc/FONT-LICENSE.txt
    - fixtures/mooneye-mbc/*.gb (15 ROMs)
    - tests/scripts/reproduce-mooneye-mbc.sh
  modified:
    - src/runner/main.c
    - .gitattributes
    - .gitignore

key-decisions:
  - "Pass callback is located via the enclosing label of the single quit_ok invocation; all other quit_inline sites are fail callbacks (matches the RESEARCH fact table for all 15 ROMs)"
  - "Budget = ceil(2 * measured ticks / 100000) * 100000, written to manifest and compiled row"
  - "original_rom_sha256 for the sibling suite is the literal none: no upstream binary digest is pinned"

patterns-established:
  - "Fixture admission through explicit per-file !/ negations in .gitignore plus binary/-text attributes"

requirements-completed: [CART-02, CART-03]

duration: 40min
completed: 2026-10-11
status: complete
coverage:
  - id: D1
    description: "15 digest-pinned Mooneye MBC2/MBC5 derivative ROMs with redistribution notices"
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest --test-dir build -R ^mooneye_mbc_ --output-on-failure"
        status: pass
  - id: D2
    description: "Bounded multi-suite runner selects admitted manifest digests and records callback results"
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest --test-dir build -R ^mooneye_mbc_ --output-on-failure"
        status: pass
  - id: D3
    description: "Fixture reproduction recipe and provenance retain builder pins and measured 7/7 MBC2, 8/8 MBC5 historical receipt"
    human_judgment: false
    verification:
      - kind: other
        ref: "python3 -I tests/scripts/verify-phase8-closure-contract.py --self-test"
        status: pass
---

# Phase 8 Plan 05: Mooneye mbc2/mbc5 admission and multi-suite runner Summary

**15 digest-pinned Mooneye mbc2/mbc5 derivatives pass through the unchanged LD B,B oracle: suite eligible=15 executed=15 status=pass, mbc2=7/7 mbc5=8/8 on the bootless DMG-CPU-B profile.**

## Performance

- **Tasks:** 2
- **Files modified:** 22 in task 1 (15 ROMs, manifest, notices, script, runner, attributes, gitignore), 2 in task 2

## Accomplishments

- Pinned rebuild (Mooneye 31510e12, WLA-DX 91c52b1f, parent patch and zero font by digest) reproduced all 15 ROMs; every SHA-256 equals the D-25 indicative digest and every length equals `32768 << $148`. `--compare` re-ran afterwards and matched byte for byte (Darwin/arm64 local rebuild; no hosted-reproduction claim until Plan 08-07).
- Result PCs, pass callback PC and fail callback PCs extracted from the linker `.sym` match the RESEARCH fact table exactly (result_pc 407e / 4071 / 4072; mbc2_ram has 6 fail sites).
- Runner generalised in `src/runner/main.c` only: `suite_def` table selected by manifest SHA-256, per-case `size_bytes` (buffer size_bytes + 1, capped at 8 MiB), `fail_callback_pcs[6]`, category receipt line. Unknown manifest digest prints `invalid-manifest` and exits 2 (verified by hand with an appended space).
- D-27 tracer: `mbc5_rom_512kb` passed on the first real run, then all 15 passed; the `$c000` print pointer did not corrupt any pass path, so **no `headless-report-mbc.patch` was created and `src/core/gabbaboy.c` was not touched**.

## Suite receipt (measured)

```
suite eligible=15 executed=15 status=pass
suite categories mbc2=7/7 mbc5=8/8
```

Measured ticks (half-dots at the runner's chunked LD B,B detection) and the budgets written to manifest and compiled rows. Host: Darwin 26.6.2 arm64, build type Debug (preset phase1). Wall time was at most 1.9 s per ROM (mbc2_bits_ramg), so the default CTest timeout of 30 s suffices.

| ROM | ticks | budget_half_dots |
|-----|-------|------------------|
| mbc2_bits_ramg | 48558168 | 97200000 |
| mbc2_bits_romb | 24779552 | 49600000 |
| mbc2_bits_unused | 23073192 | 46200000 |
| mbc2_ram | 2646176 | 5300000 |
| mbc2_rom_512kb / 1Mb / 2Mb | 31792 each | 100000 |
| mbc5_rom_512kb .. 64Mb (8 ROMs) | 421568 each | 900000 |

## Task Commits

1. **Task 1: Tracer, pinned rebuild, sibling manifest, suite_def runner** - `2b154fc` (feat)
2. **Task 2: Measured budgets and category receipt** - `69f1a90` (feat)

Plan metadata commit follows this file.

## Decisions Made

See key-decisions. Open Question 1 (bounded fail PC array, scalar kept for the parent rows) and Open Question 2 (budget formula) were implemented as planned.

## Deviations from Plan

**1. [Rule 3 - Blocking] `.gitignore` ignores `*.gb`**
- **Found during:** Task 1 (staging the ROMs)
- **Issue:** the repository allow-lists each admitted ROM explicitly; the new ROMs were ignored.
- **Fix:** added 15 explicit `!/fixtures/mooneye-mbc/<rom>.gb` negations, matching the existing style, in the same commit as the ROMs.
- **Files modified:** .gitignore
- **Committed in:** 2b154fc

**2. [Plan detail] `source_closure` includes the harness file only for `rom_*` ROMs**
- The `bits_*` and `ram` tests do not include `common/harness/mbcN_rom.s`, so listing it would be inaccurate.

`tests/test_runner.c` compiled unchanged and was not edited.

**Total deviations:** 1 auto-fixed (Rule 3). **Impact:** none on scope.

## Issues Encountered

- First facts extraction mis-identified the pass label for sources whose labels have no colon (`test_round1`) and used `wc -l` padding on macOS; both fixed in the script before any commit.

## Verification

- `mbc2` 7/7 and `mbc5` 8/8 via `--suite --receipt`; parent suite output has no `suite categories` line.
- Full local `ctest` (phase1 preset): 287/287 passed; `^(mooneye_|runner_|dmg_baseline|mbc2_|mbc5_)` subset 65/65.
- `fixtures/mooneye`, `cmake/VerifyMooneye.cmake`, `tests/scripts/reproduce-mooneye.sh`, `tests/baseline` unchanged versus main.
- No `.sym/.lnk/.log` committed; no home paths in committed files. Sibling manifest has 3 `parent_references` with matching digests and no `builder` object.
- `& 1u) << 8` anchor in `src/core/gabbaboy.c` still occurs exactly once.

## Known Stubs

None.

## Threat Flags

None. No new network endpoints; the reproduce script fetches pinned sources only.

## Next Phase Readiness

Plan 08-06 owns the sibling verifier, the 22 `mooneye_mbc_*` CTests, SOURCES.md, ELIGIBILITY.md (copy the table above) and the THIRD_PARTY_NOTICES.md row. Plan 08-07 records the hosted Linux digest match.

## Self-Check: PASSED

- fixtures/mooneye-mbc: 15 ROMs, manifest.json, LICENSE.txt, FONT-LICENSE.txt present; reproduce script present.
- Commits 2b154fc and 69f1a90 are ancestors of HEAD.
