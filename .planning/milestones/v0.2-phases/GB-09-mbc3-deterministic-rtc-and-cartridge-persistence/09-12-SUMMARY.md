---
phase: 09-mbc3-deterministic-rtc-and-cartridge-persistence
plan: 12
subsystem: testing
tags: [rtc3test, mbc3, rtc, continuation, ctest, oracle]
requires:
  - phase: 09-05
    provides: MBC3 timer continuation guest fixture
  - phase: 09-06
    provides: MBC2 continuation guest fixture
  - phase: 09-08
    provides: digest-pinned rtc3test ROM and verbatim tests.md
  - phase: 09-10
    provides: MBC5 continuation guest fixture
  - phase: 09-11
    provides: unified battery image with RTC block and gbb_rtc_catch_up
provides:
  - rtc3test Basic, Range and Sub-second suites passing headless from digest-pinned scripts
  - Exact decoded transcripts whose millisecond fields equal tests.md expectations
  - Paired negative control for the screen oracle
  - Core-level cross-instance continuation of the MBC3 timer, MBC2 and MBC5 guests
affects: [09-16, 09-18]
actuals:
  tokens: 8600
  tasks: 3
  commits: 3
plan_head_before: 2a29b8cc3ef0038474c9ee63510cb4dc829dedbf
plan_head_after: 73450248838a4562d9a9257b5370cad93b4f9b1f
tech-stack:
  added: []
  patterns: ["white-box single-TU screen oracle decoding the BG map through the ROM's own charmap, with expectations parsed from a digest-pinned upstream document"]
key-files:
  created:
    - tests/test_rtc3test.c
    - tests/test_continuation_guests.c
    - tests/rtc3test/basic.input
    - tests/rtc3test/range.input
    - tests/rtc3test/subsecond.input
    - tests/rtc3test/expected-basic.txt
    - tests/rtc3test/expected-range.txt
    - tests/rtc3test/expected-subsecond.txt
  modified:
    - tests/CMakeLists.txt
    - tests/expected-tests.txt
key-decisions:
  - "Transcript groups coloured cells as [+...] (pass) and [!...] (fail) runs instead of prefixing every cell, so numerics like 1000.0ms stay one contiguous token for the source-comparison check"
  - "Menu taps use an explicit 4f hold because gbinput 1 requires a duration on tap"
requirements-completed: [RTC-01, RTC-03, CART-06]
coverage:
  - id: D1
    description: "rtc3test Basic, Range and Sub-second suites pass headless with end marker, zero fail tiles, exact green counts (36, 28, 57) and exact transcripts"
    requirement: RTC-01
    verification:
      - kind: integration
        ref: "ctest --test-dir build --output-on-failure --no-tests=error -R '^rtc3test_(basic|range|subsecond)$'"
        status: pass
    human_judgment: false
  - id: D2
    description: "Every millisecond field equals fixtures/rtc3test/tests.md, verified by an automated parse of the digest-checked file"
    requirement: RTC-01
    verification:
      - kind: other
        ref: "ctest --test-dir build --output-on-failure --no-tests=error -R '^rtc3test_(basic|range|subsecond)$' (asserts parsed tests.md expectations against displayed values)"
        status: pass
    human_judgment: false
  - id: D3
    description: "rtc3test_negative_control: Basic script without its A tap never shows the end marker in 60 s"
    requirement: RTC-01
    verification:
      - kind: integration
        ref: "ctest --test-dir build --output-on-failure --no-tests=error -R '^rtc3test_negative_control$'"
        status: pass
    human_judgment: false
  - id: D4
    description: "Cross-instance continuation of the three original guests with exact catch-up deltas, halted and carry behaviour"
    requirement: RTC-03
    verification:
      - kind: integration
        ref: "ctest --test-dir build --output-on-failure --no-tests=error -R '^continuation_guest_(mbc3_rtc|mbc3_rtc_halted|mbc3_rtc_carry|mbc2|mbc5)$'"
        status: pass
    human_judgment: false
  - id: D5
    description: "Different-ROM same-size battery image is accepted by the core (identity lives in the player envelope)"
    requirement: CART-06
    verification:
      - kind: integration
        ref: "ctest --test-dir build --output-on-failure --no-tests=error -R '^continuation_guest_mbc3_rtc$'"
        status: pass
    human_judgment: false
duration: 55min
completed: 2026-10-11
status: complete
---

# Phase 9 Plan 12: rtc3test Oracle and Core Continuation Summary

**rtc3test v004 passes headless from digest-pinned scripts with exact BG-map transcripts whose millisecond fields equal the ROM author's tests.md values, plus store/export/import/catch-up/resume continuation of the MBC3 timer, MBC2 and MBC5 guests.**

## Performance

- **Duration:** 55 min
- **Tasks:** 3
- **Files modified:** 10 (8 created, 2 modified)

## Accomplishments

- `tests/test_rtc3test.c` is a single translation unit that includes the core plus the acceptance `sha256`, `input_script`, `predicate` and `stepper` sources. It verifies the ROM and script digests before replay, queues the script, steps frame by frame until the `* Return` marker tiles appear at `$9C00` row 17 column 6 (or 60 emulated seconds elapse), and decodes the 20x18 map through rtc3test's charmap. A pass needs the marker, no red cell, the exact green count, every displayed millisecond value equal to the stated expectation, and a byte-identical transcript.
- Marker frames observed: Basic 749, Range 496, Sub-second 1561. Green counts 36, 28 and 57 with zero red cells.
- `rtc3test_negative_control` removes the `tap` lines from basic.input in memory and requires that the marker never appears in 60 s, and that the menu was drawn (at least 20 non-blank cells), so a dead ROM cannot satisfy it.
- `tests/test_continuation_guests.c` stores in one instance, exports the battery image, imports it into a fresh instance, applies `gbb_rtc_catch_up`, and resumes. MBC3 timer: `result(N) - result(0) == N` modulo 512 days for N = 0, 1, 59, 3600, 86400. Halted mode keeps 12:34:56 day 0 for N = 0 and 86400. Carry mode shows no carry at N = 0 and carry set with day 0 at N = 20. MBC2 and MBC5 resume their markers, and a damaged image (MBC2 cell 300, MBC5 bank 15 marker) does not.
- Adjacency edge: the MBC3 image is accepted by an instance running the same guest with a different title byte and fixed header checksum (the core has no ROM identity).
- Three fixture digest tests registered: `mbc3_rtc_continuation_fixture_digest`, `mbc2_continuation_fixture_digest`, `mbc5_continuation_fixture_digest`.

## Independent numerics: field-by-field comparison with tests.md

Expectations parsed by the automated check from `fixtures/rtc3test/tests.md` (SHA-256 `1937b614...` verified against the manifest). The check printed `stated-expectations match []`.

| Suite | Label | Displayed | tests.md expectation | Equal |
|---|---|---|---|---|
| basic | Tick | 1000.0ms | 1000ms | yes |
| range | (none stated) | (none displayed) | none | yes |
| subsecond | RTCS/500 | 1000.0ms | 1000ms | yes |
| subsecond | RTCS/900 | 1000.0ms | 1000ms | yes |
| subsecond | RTCM/50 | 50.0ms | 50ms | yes |
| subsecond | RTCM/600 | 600.0ms | 600ms | yes |
| subsecond | RTCH/200 | 200.0ms | 200ms | yes |
| subsecond | RTCDL/800 | 800.0ms | 800ms | yes |
| subsecond | RTCDH/300 | 300.0ms | 300ms | yes |
| subsecond | RTC off/400 | 400.0ms | 400ms | yes |

Both the `stated_expectations` rows in the test and the millisecond fields of all three committed transcripts equal the parsed values. The transcripts were committed only after the numerics matched; they were not used to derive the expectations.

## Wall times (phase1 preset)

| Case | Wall time |
|---|---|
| rtc3test_basic | 2.4 s |
| rtc3test_range | 1.5 s |
| rtc3test_subsecond | 5.3 s |
| rtc3test_negative_control | 10.3 s (full 60 s emulated budget) |

Each suite is registered with TIMEOUT 300 (confirmed via `ctest --show-only=json-v1`).

## Task Commits

1. **Task 1 (tracer): Basic suite oracle** - `be21190`
2. **Task 2: Range, Sub-second, negative control** - `e3ef853`
3. **Task 3: Continuation digests and guests** - `7345024`

## Decisions Made

- Coloured cells are grouped into `[+...]` (green) and `[!...]` (red) runs rather than prefixed per cell, keeping numerics contiguous for the regex check while still recording which cells pass.
- Blank tile `$FF` (ClearScreen fill) and `$3F` both render as a space; the charmap source is `src/charmap.asm` at the pinned commit.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] `tap` requires a duration in gbinput 1**
- **Found during:** Task 1
- **Issue:** The plan wrote `tap A`; the parser requires a button and a time.
- **Fix:** Scripts use `tap A 4f` (and `tap DOWN 4f`), 4-frame holds.
- **Files modified:** tests/rtc3test/*.input
- **Commit:** be21190, e3ef853

**2. [Rule 3 - Blocking] Single TU needs `predicate.c` and a renamed decoder**
- **Found during:** Task 1
- **Issue:** `stepper.c` references predicate functions, so linking failed without `predicate.c`; the local `decode` collided with a static in `gabbaboy.c`.
- **Fix:** Included `src/accept/predicate.c` as well and named the helper `map_decode`.
- **Files modified:** tests/test_rtc3test.c
- **Commit:** be21190

**Total deviations:** 2 auto-fixed (both Rule 3). **Impact:** none on scope or evidence.

## Issues Encountered

None. The earlier CMake inventory mismatch during authoring was fixed by inserting the new names into tests/expected-tests.txt.

## Known Stubs

None.

## Threat Flags

None. T-09-22 (pass-claim repudiation) is mitigated by marker, red-cell, green-count, tests.md-derived numerics, exact transcript and negative control; T-09-23 by the 60 s budget and TIMEOUT 300.

## Verification

- `cmake --preset phase1`, build and full CTest: 385/385 passed.
- `verify-test-inventory.sh build/ctest.xml tests/expected-tests.txt --installed`: verified 385 executed cases, none skipped.
- A mutated transcript (`1000.1ms`) made rtc3test_basic fail, confirming the comparison bites.

## Next Phase Readiness

Plan 09-16 can build the macOS player continuation on these core-level guests; wrong-ROM identity rejection (`player_continuation_mbc3_wrong_rom`) remains there. The rtc3test evidence is author-attested hardware-derived, screen-only.

## Self-Check: PASSED

All created files exist and commits be21190, e3ef853, 7345024 are ancestors of HEAD.

## Fresh Focused Evidence (15.1-12)

- The available focused core CTest invocation passed 27/27 selected cases, including all three rtc3test suites, the no-tap negative control, the five continuation guest cases, and the RTC battery and catch-up controls.
- The rtc3test cases still compare decoded millisecond values with the digest-checked tests.md expectations. The historical screen-oracle and author-attested evidence classification above is unchanged; no hardware result is inferred.
