---
phase: 09-mbc3-deterministic-rtc-and-cartridge-persistence
plan: 15
subsystem: loader-test-strength
tags: [loader, contradiction-matrix, oracle, mutation-controls, rtc, ctest]
requires:
  - phase: 09-09
    provides: RTC comment-tagged mutation anchors and the GBB_CORE_SOURCE_PATH white-box hook
  - phase: 09-12
    provides: battery and RTC block API used by the guard instance
provides:
  - "tests/test_loader_matrix.c: independent expected_result oracle, guard instance and untouched twin"
  - "Six loader_* CTests (contradiction_mbc2/mbc3/mbc5, mbc30_variant, type_byte_sweep, bad_checksum)"
  - "Five configure-time RTC mutants with paired in-mutant controls (10 rtc_mutant_* CTests)"
affects: [09-17, 09-18]
requirements-completed: [RTC-01]
coverage:
  - id: D1
    description: Loader precedence matrix and paired RTC mutation controls
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest --test-dir build --output-on-failure --no-tests=error -R '^(loader_(contradiction_mbc[235]|mbc30_variant|type_byte_sweep|bad_checksum)|rtc_mutant_.*)$'"
        status: pass
key-decisions:
  - "Oracle typed from D-27 and docs/cartridge-and-saves.md tables; it neither includes nor calls the core validator"
  - "Mutant anchors are full tagged statement lines; the clamp mutant adds the untagged M and H store lines as extra exactly-once anchors"
status: complete
commits: 3
plan_head_before: 7bf6deb89dd0c439c9629c19d9caf0839ba876c9
plan_head_after: 07e579c4b71c649c612b7b6446640875545e7ac0
actuals:
  tokens: 14500
  tasks: 3
  commits: 3
duration: 45 min
completed: 2026-10-11
---

# Phase 9 Plan 15: Loader contradiction matrix and RTC mutation controls Summary

An independent-oracle loader matrix (D-27) shows `gbb_load_rom` agrees with the written precedence on every MBC2/MBC3/MBC5 combination with no partial mutation, and five configure-time RTC mutants are each killed by a named original test while an unrelated case still passes inside the same mutant.

## Accomplishments

- `tests/test_loader_matrix.c`: `expected_result(type, rom_code, ram_code, length, checksum_ok)` implements the nine-step D-27 precedence over its own family table. Each case writes only the header into one 8 MiB + 1 heap buffer, recomputes the checksum (and also runs a corrupted-checksum twin of every case, which exercises the ordering edge for all combinations), and loads into the guard (expected rejection) or a scratch instance (expected OK).
- Guard instance: MBC1 `$03` with an imported 8 KiB save and a WRAM canary. After every rejection the test checks battery size, bytes, generation, `GBB_NO_RUMBLE`, `GBB_NO_RTC` and the canary after a short run; at the end the guard equals an untouched twin.
- Cases executed per test: `loader_contradiction_mbc2` 1344, `loader_contradiction_mbc3` 3360 (plus 4 direct must-be-OK loads), `loader_contradiction_mbc5` 4032, `loader_mbc30_variant` 31, `loader_type_byte_sweep` 256 (accepted set exactly `$00 $01-$03 $05-$06 $0F-$13 $19-$1E`), `loader_bad_checksum` 11 (including NULL ROM, size 0 and size `0x14F`).
- Must-be-OK rows asserted directly: MBC5 code `$08` at 8 MiB, MBC3 `$06` at 2 MiB, MBC2 `$03` at 256 KiB.
- **No core defect was found.** `src/core/gabbaboy.c` is unchanged (`git diff --exit-code src/core` clean after every control).
- RTC mutants (`gbb_rtc_mutant` in `tests/CMakeLists.txt`): each anchor must occur exactly once or configure fails naming the anchor.

| Mutant | Kills (REQUIRE text) | Control (exit 0) |
|---|---|---|
| prescaler_kept | `rtc_prescaler_rules`: `rreg(m, 0u) == 0u` | rtc_write_masks |
| prescaler_reset_every_write | `rtc_prescaler_rules`: `rreg(m, 0u) == 1u` | rtc_write_masks |
| prescaler_reset_on_halt | `rtc_prescaler_rules`: `rreg(m, 0u) == 1u` | rtc_write_masks |
| out_of_range_clamped | `rtc_out_of_range_rollover`: `out[1] == 5u` row | rtc_rate_exact |
| latch_any_write | `rtc_latch_edges`: `rreg(m, 0u) == cases[i].expect` | rtc_write_masks |

## Deviations from Plan

**1. [Rule 3 - Structure] Whole matrix file written in Task 1.** `tests/test_loader_matrix.c` was committed with all six case bodies in the Task 1 commit; Task 1 registered only `loader_contradiction_mbc3` and Task 2 registered the other five. Behaviour and scope are as planned.

**2. [Rule 2 - Strength] Extra anchors for the clamp mutant.** Only the seconds store carries a Plan 09-09 tag, so the minute and hour store statements (`case 1u: ...` and `case 2u: ...`) are additional exactly-once anchors in `out_of_range_clamped`.

**3. [Minor] `GBB_CORE_SOURCE_PATH` count.** The acceptance grep counts lines (at least 5); two explanatory comment lines in `tests/CMakeLists.txt` name the macro to meet it honestly alongside the real definition.

## Evidence

- Full suite: 401 of 401 CTest cases passed locally (`ctest` 166 s) and `verify-test-inventory.sh ... --installed` reported "Verified 401 executed CTest cases; none skipped."
- The linux-asan-ubsan leg was not run locally; the matrix is plain C99 on the public API and runs there at the phase evidence head (plan verification item). Not claimed here.
- Evidence class: synthetic headers against an independent oracle; no hardware claim.

## Known Stubs

None.

## Threat Flags

None. T-09-28 (guard plus twin after every rejection), T-09-29 (single reused 8 MiB + 1 buffer) and T-09-30 (five mutants, exactly-once anchors, paired controls) are implemented.

## Self-Check: PASSED

- `tests/test_loader_matrix.c` exists; commits 7589de1, 97c478d, 07e579c are ancestors of HEAD; 16 new names are in `tests/expected-tests.txt` and in the executed inventory.

## Fresh Focused Evidence (15.1-12)

- Reused the existing `build` tree. The loader and RTC mutant/control selection passed 16/16 CTest cases in 1.17 seconds.
- The historical full-suite and sanitizer statements above remain producer evidence; this plan did not rerun the full suite or sanitizer leg and makes no new hardware claim.
