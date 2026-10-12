---
phase: 09-mbc3-deterministic-rtc-and-cartridge-persistence
plan: 13
subsystem: player-persistence
tags: [save-envelope, v2, rtc, battery, player, clock-adapter]
requires:
  - phase: 09-04
    provides: v0.1 save-envelope corpus (fixtures/save-envelope-v1)
  - phase: 09-11
    provides: battery image with RTC block, gbb_rtc_catch_up
provides:
  - Player save envelope v2 (64-byte header, RAM then RTC block, saved_at stamp)
  - Core-derived cartridge classification (player_session_classify_cartridge)
  - player_session_set_clock plus the single time adapter in main.c
  - 8 MiB player ROM read bound and 128 KiB RAM bound
affects: [09-16, 09-17, 09-18]
status: complete
commits: 2
plan_head_before: 8a779990da1ae4288c05fb7c9975befdd922bcad
plan_head_after: 7d262c140097e0d6799f1ae196d2a534127bef9e
actuals:
  tokens: 60000
  tasks: 3
  commits: 2
requirements-completed: [CART-06, RTC-03]
key-files:
  modified:
    - src/player/session.c
    - src/player/session.h
    - src/player/main.c
    - src/player/limitations.h
    - tests/player/test_session.c
    - tests/player/test_limitations.c
    - tests/player/CMakeLists.txt
    - tests/player/expected-tests.txt
    - docs/mbc2-mbc5-evidence.md
key-decisions:
  - "MBC1 $03 with 8 or 32 KiB RAM keeps writing v1 under the unchanged -mbc1- name; every other battery type writes v2 under -cart-; a $03 save read from v2 stays v2"
  - "player_session_identify_rom now fills only digest and type; player_session_classify_cartridge fills battery, RAM size and rtc_present from gbb_battery_size and gbb_rtc_catch_up(machine, 0)"
  - "A rejected save leaves the core's fresh image alone: only the RAM part is reset to $FF and the clock block the core holds is kept"
duration: 55 min
completed: 2026-10-11
coverage:
  - deliverable: "Envelope v2 codec, reject matrix, max size, seven fault points"
    verification: [{kind: ctest, ref: "tests/player/test_session.c#player_session_v2_*", status: pass}]
    human_judgment: false
  - deliverable: "v0.1 corpus loads and re-encodes byte-identically"
    verification: [{kind: ctest, ref: "tests/player/test_session.c#player_session_v1_corpus_load,player_session_v1_mbc1_write_identical", status: pass}]
    human_judgment: false
  - deliverable: "Core-derived classification and 8 MiB cap"
    verification: [{kind: ctest, ref: "tests/player/test_session.c#player_session_classification_drift,player_session_rom_cap_8mib", status: pass}]
    human_judgment: false
---

# Phase 9 Plan 13: Player envelope v2, core classification and clock adapter Summary

Every new battery type (MBC2, MBC3 with RAM and clock, MBC5 up to 128 KiB) now persists in a validated 64-byte-header v2 envelope stamped with the host save time, MBC1 `$03` v1 files stay byte-identical, and the player takes battery status, RAM size and clock presence from the core instead of the header byte.

## Accomplishments

- v2 codec in `src/player/session.c`: field-by-field little-endian header, allow-listed `ram_len`/`rtc_len` checked before the uint64 total, exact file size, CRC-32 over header bytes 0-59 plus payload, heap buffers on every path. Rejections of any kind use the existing preserve-then-fresh path and leave generation unchanged.
- Version choice is deterministic: v1 only for `$03` with 8 or 32 KiB RAM that was not loaded from a v2 file; everything else v2. Idempotent save (unchanged generation writes nothing) is preserved.
- Classification: `player_session_classify_cartridge` after `gbb_load_rom`; WR-02 field and the 8192/32768 mapping removed; `PLAYER_SESSION_MAX_ROM_SIZE` 8 MiB, `PLAYER_SESSION_MAX_RAM_SIZE` 131072.
- Clock: one `player_clock_now` adapter in `main.c` (outside the scripted-smoke slice) feeding `player_session_set_clock` before every save; timer carts stamp `saved_at` with flags bit1, other carts record none.
- Tests added: `player_session_v2_max_size`, `_reject_matrix` (17 mutations, structural ones with CRC recomputed so the field check itself rejects), seven `_v2_*` fault tests (one on `$1B`), `player_session_v1_corpus_load`, `player_session_v1_mbc1_write_identical`, `player_session_classification_drift` (256 types x RAM codes 0-5), `player_session_rom_cap_8mib`, and an extra `player_session_v1_v2_stickiness`. `player_session_battery_unsupported` is removed; limitations text and its test updated.

## Task Commits

1. Tasks 1-3 code and tests: `ea827a0` (session, header, main.c adapter, all session tests, CMake, inventory)
2. Task 3 text: `7d262c1` (limitations text, test_limitations, MBC2/MBC5 evidence doc)

## Deviations from Plan

**1. [Ordering] Tasks committed as two commits, not three**
- The three tasks share `session.c` and `test_session.c`, and the tracer cannot compile without removing the WR-02 branches in `main.c`, so tracer, reject/fault/corpus tests and the adapter landed in one commit; the limitations/doc text is the second.

**2. [Rule 3 - Blocking] write_smoke_rom identity needed core classification**
- `main.c` `write_smoke_rom` used `player_session_identify_rom` for a full identity (lock, remove); added `identify_rom_with_core` (scratch instance, load, identify, classify). Caught by `player_smoke` and `player_reset_transition` failing, fixed before commit.

**3. [Rule 2] Extra test and error text**
- Added `player_session_v1_v2_stickiness` (D-19 "never written back as v1", plus no-write on unchanged save) and updated the 2 MiB ROM error strings to the new 8 MiB bound; existing `player_session_replacement_failure` now probes 8 MiB + 1 and + 2.

**Total deviations:** 1 blocking fix, 1 addition, 1 ordering note.

## Known Stubs

None. The loaded file's `saved_at` is decoded but not yet exposed on the identity; Plan 09-16 owns catch-up and will add that field. `docs/preview.md` and `docs/cartridge-and-saves.md` still describe the 2 MiB read bound and MBC1-only saves; Plan 09-17 owns those docs.

## Verification

- `cmake --preset phase1` build, `ctest` 385/385 pass, `verify-test-inventory.sh ... --installed` verified 385 cases.
- `bash tests/scripts/verify-phase3-player.sh --build-package`: 70/70 player tests pass, inventory exact (`names=55` baseline check), package smoke passed.
- All task acceptance greps re-run: counts match (1/1/1/1/1, 9, 2, >=1, 2); `time(` absent from `session.c` and `catch_up_policy.c`; `battery_unsupported` absent from `src`, `tests/player` and `docs`.

## Threat Flags

None beyond the register: T-09-24 (allow-lists, uint64 total, exact size), T-09-25 (CRC covers saved_at, flipped-byte case tested), T-09-26 (seven fault tests), T-09-27 (drift sweep) are mitigated and tested.

## Self-Check: PASSED

Modified files exist; commits ea827a0 and 7d262c1 are on the branch.
