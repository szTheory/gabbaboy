# Phase 9: MBC3, Deterministic RTC and Cartridge Persistence - Research

**Researched:** 2026-10-11
**Domain:** Portable-C Game Boy core cartridge mapper (MBC3 + lazy RTC), battery image contract, SDL3 macOS player save envelope, CI evidence gates
**Confidence:** HIGH for code anchors, test-registration mechanics, fixture digests and risks (all read or probed this session); MEDIUM for Windows/MSVC object-scan portability and the legacy-RGBDS reproduction legs (not runnable here)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

### A. MBC3 mapping and loader policy (CART-04)
- **D-01:** Five type-table rows are added to `cart_type_table` in `src/core/gabbaboy.c`, following the Phase 8 seam (in-file section, `cart_kind` switch, no vtables). `CART_MBC3` is appended to `cart_kind`. A new RAM rule `CART_RAM_MBC3` accepts only RAM codes `$02` (8 KiB) and `$03` (32 KiB).

  | Type | Battery | Timer | RAM rule |
  |---|---|---|---|
  | `$0F` | yes | yes | none (code `$00` only) |
  | `$10` | yes | yes | `CART_RAM_MBC3` |
  | `$11` | no | no | none |
  | `$12` | no | no | `CART_RAM_MBC3` |
  | `$13` | yes | no | `CART_RAM_MBC3` |

  - Every row has `ram_window_mapped=1`, `has_rumble=0`, maximum ROM code `$07`, and a ceiling of **4 MiB**.
  - MBC3 has no RAM-size versus ROM-size coupling.
  - `$08`/`$09` remain `GBB_UNSUPPORTED_CARTRIDGE`.
- **D-02: MBC30 and variant rejection.** All existing D-05 header checks (Phase 8) run unchanged: length, type, ROM code, RAM rule, truncation and mismatch, checksum. Only after the checksum passes is an MBC3 header checked for MBC30. It is a candidate if either:
  - its ROM code is `$07` (4 MiB, at exactly 4 MiB length), or
  - its RAM code is `$05` (64 KiB) on a RAM-bearing type (`$10/$12/$13`).

  A candidate returns `GBB_UNSUPPORTED_CARTRIDGE_VARIANT`, in the same slot as MBC1M (Phase 8 D-20: VARIANT = "recognised but unsupported wiring"). Every other bad size keeps its size-class error:
  - RAM `$01/$04` on any MBC3 type: `UNSUPPORTED_RAM_SIZE`.
  - RAM `$05` on `$0F/$11`: `UNSUPPORTED_RAM_SIZE`.
  - RAM `$00` on a RAM type: `UNSUPPORTED_RAM_SIZE`.
  - ROM code `$08` and above: `UNSUPPORTED_ROM_SIZE`.
  - Length above 4 MiB: `ROM_TOO_LARGE`.

  The legacy `ROM_TOO_LARGE`-at-2-MiB+1 rule applies only to ROM-only and MBC1. The Phase 8 "preserve return codes" rule covers types that loaded before Phase 8, not `$0F-$13`. Pan Docs lists the MBC30 as 4 MiB ROM and 64 KiB RAM; the exact Pokémon Crystal JP header bytes were not confirmed, and the rule covers both signatures.
- **D-03: MBC3 write decode.**
  - `$0000-$1FFF`: `(v & 0x0F) == 0x0A` enables both RAM and RTC.
  - `$2000-$3FFF`: `bank = v & 0x7F`, then bank 0 becomes 1, then `&= rom_banks-1` (translate before mask, as in Phase 8 D-18).
  - `$4000-$5FFF`: decodes the whole byte.
    - `$00-$03` selects a RAM bank. On an 8 KiB cart the index is masked to `ram_banks-1`, so banks 1-3 alias bank 0, which MagenTests requires.
    - `$08-$0C` selects an RTC register.
    - Every other value (`$04-$07`, `$0D-$FF`) maps nothing: reads return `$FF` and writes are ignored. Each new selection replaces the previous one.
  - `$6000-$7FFF`: latch (D-08).
  - When disabled, reads return `$FF` and writes are ignored, RTC included.
  - Absent RAM (`$0F`, `$11`) reads `$FF`.
  - An RTC select on a type without a timer (`$11-$13`) maps nothing. The RTC never appears without a timer (V2-16).
  - Reset sets ROM bank 1, RAM bank 0, disabled, and leaves RAM alone.
  - The battery generation bumps only on a changed byte with battery present.
  - The unmapped `$04-$07` choice is labelled **software-model decision, not hardware-qualified**. SameBoy aliases with `& 3` on non-timer MBC3, and mGBA decodes the low nibble.
- **D-04: MagenTests admission.** A new sibling directory `fixtures/magentests/` holds:
  - the three 32 KiB release ROMs `mbc_oob_sram_mbc{1,3,5}.gbc`, with SHA-256 `83f1fc44…a8bb`, `03e13fa7…f7dd` and `e99f5263…f54b` (full digests are in the research handback; recompute at admission);
  - `manifest.json` in the `fixtures[].{alias,size_bytes,sha256}` shape, so the existing scan reads it;
  - `LICENSE.txt` (MIT, 2022 alloncm);
  - `SOURCES.md`, pinning upstream `3f9c090f16e5a721db776febb9ba7d773e1c819c`, RGBDS v0.6.1 `69a5739…`, and gbdev hardware.inc `21ef22d…` (CC0);
  - `ELIGIBILITY.md`;
  - a `THIRD_PARTY_NOTICES.md` entry.

  `tests/scripts/reproduce-magentests.sh --compare` becomes a `fixture-repro` leg. "Release bytes equal the rebuild" is claimed only after the hosted Linux leg matches.
- **D-05: MagenTests oracle.** The ROMs are screen-only: the BG is uniform, shade 0 for pass and shade 3 for fail. Frames 1-3 are white whatever the result, so an early sample is vacuous. A new C test on the public API, `tests/test_magentests.c`:
  - runs at least **10 frames** and requires all 23040 pixels at shade 0;
  - always pairs the run with a **negative control**: the same ROM with `$149=$03` and its checksum recomputed in the test, which must be all shade 3 at the same frame count.

  CTests: `magentests_fixture_digest`, `magentests_oob_sram_mbc1`, `_mbc3`, `_mbc5`, `magentests_oob_sram_negative_control`. These stay out of the `--observe` baseline set. The ROMs write CGB registers, which the DMG profile ignores, so no CGB profile is needed.
- **D-06: Install exclusion.** Add `magentests_not_installed` and a renamed-ROM self-test. Both reuse `cmake/ScanForbiddenFixtures.cmake` with `GBB_FORBIDDEN_MANIFEST=fixtures/magentests/manifest.json`. Add an optional label parameter so failure messages are not hard-coded to "mooneye". Package scans are unchanged.

### B. Deterministic RTC core model (RTC-01)
- **D-07: Lazy RTC anchored on `time_half_dots`.** There is no per-half-dot work. This choice also stays correct across the STOP fast-forward, which bumps `time_half_dots` without calling `advance_devices_to`.
  - State is plain integers in `cart_state`:
    - `rtc_s`, `rtc_m`, `rtc_h`, `rtc_dl`, `rtc_dh` (DH bits: 0 = day bit 8, 6 = halt, 7 = carry);
    - the latched copy `rtc_l[5]`;
    - `rtc_sub` (u32, half-dots into the current second, < 2^23);
    - `rtc_synced_at` (u64);
    - `rtc_latch_prev` (u8, the last value written to `$6000-$7FFF`).
  - Sync:
    - `el = now - synced_at` (treated as 0 if `now < synced_at`), then `synced_at = now`.
    - If halted, return after updating `synced_at`.
    - Otherwise compute `secs = (el>>23) + ((el & mask) + sub)>>23` and the new `sub`, which is overflow-safe for `el` near 2^64.
    - Apply `secs` through one closed-form `rtc_add_seconds`, which is O(1) and equals naive per-second stepping, including out-of-range fields.
  - Sync happens at every RTC register write, halt toggle, latch, and export projection. Reads return the latched bytes, so `read8` stays `const`.
- **D-08: Behaviour table, pinned to rtc3test v004 (R3), Pan Docs (PD) or a project decision (DEC).**
  - **Rate:** exactly 2^23 half-dots per second (R3, measured 1000.0 ms).
  - **Seconds write:** stores `v&0x3F` and resets `rtc_sub` to 0 (R3 RTCS/500, RTCS/900).
  - **Writes to M/H/DL/DH and halt toggles:** do not touch `rtc_sub` (R3).
  - **Write while running:** sync first, then store. The latched bytes are unchanged.
  - **Read masks:** S and M `&0x3F`, H `&0x1F`, DL 8 bits, DH `&0xC1`; unused bits read 0 (R3). Write masks are the same; DH stores only bits 0, 6 and 7.
  - **Out-of-range values** (S/M 60-63, H 24-31) are stored as written (R3). A field carries only when it steps from exactly 59/59/23. Otherwise it becomes `(v+1)&mask` with no carry: S=63 wraps to 0 with no carry, and seconds 59 to 0 still carries into M even if M ≥ 60 (R3 `Invalid rollovers`, `High minutes`, `High hours`).
  - **Day counter:** 9 bits. 511+1 wraps to 0 and sets the carry. The carry is sticky and clears only when a guest writes DH with bit 7 = 0 (R3, PD).
  - **Halt:** while halted, no time is credited, though `synced_at` still advances (R3 "RTC off").
  - **Latch:** copies live to latched after a sync, only when the previous `$6000-$7FFF` write was exactly `$00` and this one is exactly `$01`. Every write updates `latch_prev`. Load and mapper reset set `latch_prev=$FF` (unprimed).
    - The `00`→`01` sequence is PD; everything else is DEC. Sources disagree here: SameBoy latches on any write, and mGBA on `01` unless already latched.
    - rtc3test does not detect latch edge cases, so original unit tests own them.
  - **Gating:** RTC access requires RAMG `$0A`. `$0F` works with RAM size 0.
- **D-09: Reset and load.**
  - `gbb_reset` syncs first, then runs `reset_state` (which zeroes `time_half_dots`), then sets `synced_at = 0`. Reset preserves the live and latched RTC, halt, carry and `sub`, as it preserves RAM. It resets the mapper registers and `latch_prev`.
  - A successful `gbb_load_rom` starts a fresh RTC (00:00:00, day 0, running, latched zero) through the existing cart `memset`.
- **D-10: Battery generation.**
  - A guest RTC register write bumps the generation when it changes stored state. The rule is: snapshot `{S,M,H,DL,DH, sub}` after sync, apply the write, compare. A same-value seconds write with non-zero `sub` counts as a change.
  - Elapsed ticks never bump, and neither does a tick-set carry.
  - **The latch does not bump.** This resolves a conflict: ARCHITECTURE §180 said it should, but a game that polls a latched clock once a second would otherwise defeat the quiet-period save.
  - `gbb_rtc_catch_up` bumps once if it changed state.
- **D-11: rtc3test gate.** rtc3test v004 (Unlicense, `80ae792bf1b3c3387929b912e6df001af3511e24`) is used with the release ROM. Its SHA-256 is `a271013fb37ea1d927b854798401320b220d57abb3ca77f3d318ceb8a9def30d`; it is 32768 B, type `$0F`. It lives in `fixtures/rtc3test/` with a manifest, license, sources, eligibility and a reproduction script using legacy RGBDS 0.4.x as a `fixture-repro` leg.
  - rtc3test is screen-only and menu-driven, and records results as BG-map tiles at `$9C00`: pass tiles are `glyph|0x40`, fail tiles `glyph|0x80`. Pixel shades are unreliable on DMG.
  - **Oracle:** a white-box single-TU test, `tests/test_rtc3test.c`, that includes `src/core/gabbaboy.c` (precedent `tests/test_mbc5_internal.c`). It includes `src/accept/input_script.c` and `sha256.c` as source and replays three digest-pinned `.input` scripts:
    - Basic: `wait 60f`, `tap A`.
    - Range: `wait 60f`, `tap DOWN`, `wait 8f`, `tap A`.
    - Sub-second: two DOWNs, then A.
  - Each suite stops at the `* Return` marker (tiles `C1 3F 1B 28 37 38 35 31` at row 17, col 6) or fails at a 60 s emulated budget. Measured emulated run lengths: Basic about 13.5 s, Range 9.3 s, Sub-second 27.1 s.
  - **Predicate:**
    - the marker appears;
    - zero tiles fall in `$80-$BF`;
    - green-cell counts are 36, 28 and 57;
    - the decoded transcript equals a committed expected transcript, including exact numerics such as `1000.0ms`, `50.0ms` and `400.0ms`. These catch a 0.1% rate error that the ROM's own ±1 ms tolerance misses. Re-derive them at implementation time.
  - CTests: `rtc3test_basic`, `rtc3test_range`, `rtc3test_subsecond`, plus `rtc3test_fixture_digest` and a negative control in which a missing scripted A means the marker never appears.
  - rtc3test is labelled a hardware-derived test (author-attested).
- **D-12: Original RTC tests, `tests/test_mbc3_rtc.c`.** These cover what rtc3test does not:
  - **Differential:** closed-form add equals naive stepping on random states, including out-of-range ones.
  - **Metamorphic:** add(a)+add(b) equals add(a+b), and sliced versus unsliced `gbb_run` give an identical RTC.
  - **CPU independence:** busy-loop, HALT and STOP ROMs give an identical RTC after equal half-dots.
  - **Edges:** latch edge cases, halt, carry stickiness, the 511-day wrap, `time_half_dots` near `UINT64_MAX`, and reset rebase.
  - **Mutation controls:** a compile-time test hook proves each of the following fails a test: prescaler not reset on a seconds write, reset on every write, reset on halt toggle, out-of-range values clamped, and latch on any write.
- **D-13: CI proof of no host clock.** `cmake/CheckCoreNoHostClock.cmake` runs as a CTest on every leg, with a negative control (a scratch source containing `#include <time.h>` and `time(NULL)` must fail). It has two layers:
  - **Source layer:** `src/core` and `include/gabbaboy` may include only `<stddef.h> <stdint.h> <stdlib.h> <string.h>` and `"gabbaboy/gabbaboy.h"`. A call-pattern denylist covers `time|clock|clock_gettime|gettimeofday|timespec_get|localtime|gmtime|mktime|difftime|nanosleep|usleep|sleep|getenv`, plus `QueryPerformance`, `GetSystemTime`, `GetTickCount`, `GetLocalTime`, `mach_absolute_time` and `__rdtsc`.
  - **Object layer:** the undefined symbols of the core object, via `${CMAKE_NM} -u` or `dumpbin /SYMBOLS` on MSVC, with `_` and `__imp_` stripped. A missing tool fails the leg; a skip counts as a failure.
  - **Behavioural complement:** the D-12 slice-invariance test.

### C. RTC public API and battery block (RTC-02, RTC-03 core)
- **D-14: `gbb_rtc_catch_up(gbb_instance *instance, int64_t elapsed_seconds)`.**
  - **Negative values:** `GBB_INVALID_ARGUMENT`, no mutation. The host decides how to treat clock rollback.
  - **Zero:** a no-op with no generation bump.
  - **Halted clock:** `GBB_OK`, no change.
  - **Otherwise:** sync to the current emulated time, then add exactly through the shared `rtc_add_seconds`. The arithmetic is O(1) and modular with no saturation: days wrap at 512 and set the sticky carry, and `catch_up(a)` then `catch_up(b)` equals `catch_up(a+b)`.
  - **Unchanged by catch-up:** the latched registers, `sub` and `time_half_dots`.
  - **Generation:** bumps once if live state changed (D-10).
  - **Errors:** no ROM, or a cartridge without a timer, returns the new `GBB_NO_RTC`. It is the only enum addition, appended after `GBB_NO_RUMBLE`.
  - **When to call:** documented as "between `gbb_run*` calls", and recorded as an input event in replay logs.
  - **Reconciled:** the player research planned a `uint64_t` delta, and ARCHITECTURE sketched `uint64_t`. Signed was adopted because `(uint64_t)(now - saved)` silently becomes a huge advance on rollback. The player clamps a forward delta above `INT64_MAX` to `INT64_MAX` (about 292 billion years). — **Reversibility:** costly — this is a new public prototype on the 0.x preview library. Changing it after v0.2 ships breaks installed consumers. Until the release it is a header edit plus two consumers.
- **D-15: Unified battery image.** For timer carts (`$0F`, `$10`) the image is `cartridge RAM || RTC block`. For `$0F` it is the block alone.
  - All other battery carts are exactly RAM-sized, as in v0.1, so MBC1 blobs are unchanged.
  - `gbb_battery_size`, `gbb_copy_battery`, `gbb_import_battery` and `gbb_battery_generation` treat timer types as battery-backed. `has_battery_ram` generalises to "has battery image", because `$0F` has no RAM.
  - New macro: `GBB_RTC_BLOCK_SIZE 21u`.
  - **Export** projects the RTC to the current emulated time on a local copy, keeping the `const` instance unmutated. Two exports at the same emulated time are byte-identical.
  - **Import** parses and validates RAM and the block into locals, then commits both together with `synced_at = now`. **Import never advances the RTC.** A test runs N half-dots, imports, exports, and requires the imported bytes back.
  - Separate `gbb_copy_rtc`/`gbb_import_rtc` were rejected: two persistence paths would mean two generations and risk RAM/RTC skew. — **Reversibility:** costly — this fixes the battery-image contract for MBC3 hosts after release.
- **D-16: RTC block v1, 21 bytes, written field by field, little-endian.**

  | Offset | Size | Field | Valid on import |
  |---|---|---|---|
  | 0 | 4 | magic `GBRT` | exact |
  | 4 | 1 | version | `1` |
  | 5 | 4 | u32 `sub` (half-dots) | < 2^23 |
  | 9-13 | 5 | live S, M, H, DL, DH | S, M ≤ `0x3F`; H ≤ `0x1F`; DL any; `(DH & 0x3E) == 0` |
  | 14-18 | 5 | latched S, M, H, DL, DH | same masks |
  | 19 | 1 | `latch_prev` | any |
  | 20 | 1 | reserved | `0` |

  - Out-of-range but hardware-legal values (S=63, H=31) are accepted, because guests can reach them (rtc3test writes them).
  - **Rejections:** bad magic, unknown version, masked bits set, or reserved byte non-zero all return `GBB_INVALID_ARGUMENT`. The wrong total length returns `GBB_BATTERY_SIZE_MISMATCH`. In every case nothing is mutated, RAM included.
  - **Versioning:** a version bump implies a size change, so older cores fail on size.
  - **Reconciled:** the API research proposed a 0/1 "latch armed" byte; the stored full `latch_prev` from the RTC research carries the same information exactly.
  - BGB/VBA-M footer interop remains expressible host-side: the block has every footer field, and the reverse direction sets `sub=0`, `latch_prev=$FF`, reserved 0.
- **D-17: Public API escalation judgement.** The additions are one function, one appended enum value, one macro, and a larger battery size only for types that previously failed to load. No existing call changes behaviour for any v0.1-supported cartridge. Like the Phase 8 rumble API, this is treated as an append-only addition inside the active phase and auto-followed, not an owner question. The owner can still veto the signed signature before the phase PR merges.
- **D-18: Consumers and docs (feeds SHIP-10).**
  - **Consumers:** the installed C and C++ consumers in `tests/consumers/{c,cpp}` synthesise a tiny original `$10` ROM and check:
    - battery size equals RAM + 21;
    - `catch_up(3661)` yields live S/M/H = 1/1/1 at block offsets 9-11;
    - importing into a fresh instance gives byte-identical output (no advance);
    - `GBB_NO_RTC` on MBC1;
    - `GBB_INVALID_ARGUMENT` for a negative value.
  - **Docs:** update the header doc comments, `docs/cartridge-and-saves.md` (image wording, block layout, error table, the "never catch up on import" rule, the interop note, envelope v2) and an MBC3/RTC evidence ledger, `docs/mbc3-rtc-evidence.md`, in the style of `docs/mbc2-mbc5-evidence.md`.
  - **Core tests:**
    - catch-up: zero, negative, `INT64_MAX`, halted, carry stickiness, composability;
    - round-trip across a fresh instance and across `gbb_reset`;
    - an import corruption matrix with before/after byte comparison.

### D. Player persistence and continuation (CART-06, RTC-03 player)
- **D-19: Envelope v1/v2 split.**
  - MBC1 `$03` with 8 or 32 KiB RAM keeps writing **v1 byte-identically**, so a v0.1 player still reads it. Every other battery type writes v2.
  - Readers load v1 forever, for `$03` only, and accept v2 for every core-supported battery type, including `$03`. A v2 file is never rewritten as v1.
  - Option B (all new saves in v2) was rejected because a v0.1 player would treat the file as corrupt and rename it, which looks like lost progress. The v0.1 contract requires keeping access to older files. — **Reversibility:** costly — before v0.2 ships no v2 file exists on any user's disk, so the layout can still change. After release every later player must keep reading v2 files, so changes then need a migration path.
- **D-20: v2 layout, 64-byte header, little-endian, field by field.**

  | Offset | Size | Field |
  |---|---|---|
  | 0-7 | 8 | `GBBBSAVE` |
  | 8-9 | 2 | version 2 |
  | 10-41 | 32 | ROM SHA-256 |
  | 42 | 1 | cartridge type |
  | 43 | 1 | flags: bit0 RTC present; bit1 `saved_at` valid, only allowed with bit0; other bits 0 |
  | 44-47 | 4 | `ram_len`, equal to the RAM part of `gbb_battery_size`: 0, 512, 8192, 32768, 65536 or 131072 |
  | 48-51 | 4 | `rtc_len`: 0, or exactly `GBB_RTC_BLOCK_SIZE`, never more than 64 |
  | 52-59 | 8 | `saved_at`, i64 Unix UTC seconds; 0 unless bit1 is set |
  | 60-63 | 4 | CRC-32 (IEEE) over bytes 0-59 plus the payload |
  | 64- | | payload: RAM then the RTC block, opaque to the player |

  - The file must be exactly `64 + ram_len + rtc_len` bytes, at most 131200. Buffers go on the heap, not the current stack arrays.
  - Every rejection takes the existing preserve-then-fresh path with no mutation: truncation, trailing bytes, unknown version, reserved bits set, a non-canonical zero field, identity mismatch, size mismatch with the core, or a bad CRC.
  - The CRC covers the header, unlike v1, so a flipped `saved_at` cannot inject a catch-up. It detects accidents only and is not authentication.
- **D-21: Clock seam.**
  - The player reads `time(NULL)` only in the adapter. `-1` means unavailable, and the value converts to `int64_t`.
  - A pure `player_catch_up_policy(saved_at, saved_valid, now, now_valid)` computes the action and status. It is table-tested on Linux, macOS and Windows, including the int64 extremes.
  - Tests inject the clock with `--clock-unix <i64>`, accepted **only** by the `--battery-smoke-*` / continuation child modes and rejected in normal play. An environment variable was rejected as ambient state.
- **D-22: Catch-up policy on reopen.** Catch-up runs at most once per open: after battery import, before the first guest instruction. The status appears on the existing status line, with no modal.

  | Condition | Action | Status |
  |---|---|---|
  | No RTC, no file, or a rejected file | none | none, or the existing rejected-save warning |
  | `saved_at` invalid | none | "Game clock not advanced: the save has no time stamp." |
  | Host clock unavailable | none | "...the system clock is unavailable." |
  | `now < saved_at` | none; the next save re-stamps `now` | "...the system clock is earlier than the save." |
  | `now == saved_at` | none | none |
  | Delta > 0 | `gbb_rtc_catch_up(min(delta, INT64_MAX))` | "Game clock advanced by 1d 2h 3m 4s", adding "(day counter overflowed)" if the carry became set |
  | Halted RTC | the core ignores the delta | "Game clock is halted; not advanced." |

  - Every save writes `saved_at = now` together with an RTC block from the same instant.
  - After a catch-up changes state, the generation bump marks the save dirty, so the next save re-stamps it.
  - The policy matches BGB/VBA-M: a future timestamp means no advance. SameBoy instead resets the RTC on a future timestamp, and mGBA moves the clock backwards; both were rejected as data-destroying.
  - **Known limitation, documented:** time spent paused while the player is open is not recovered.
- **D-23: One source of truth for classification (closes WR-02).**
  - After `gbb_load_rom` succeeds, the player derives battery-backed status, RAM length and RTC presence from the core (`gbb_battery_size` and `GBB_RTC_BLOCK_SIZE` for timer types). The header type byte is used only for the filename and envelope identity.
  - Remove `battery_unsupported` and the hard-coded 8192/32768 mapping in `src/player/session.c`. Update `limitations.h` and the docs.
  - `PLAYER_SESSION_MAX_ROM_SIZE` becomes 8 MiB, guarded by a test that compares it with the core bound. `PLAYER_SESSION_MAX_RAM_SIZE` becomes 131072.
  - **Guards:**
    - Core half: `loader_type_byte_sweep` (D-27) asserts the accepted set is exactly `$00,$01-$03,$05-$06,$0F-$13,$19-$1E`.
    - Player half: `player_session_classification_drift` sweeps all 256 type bytes × RAM codes `$00-$05` against the core's outcomes.
- **D-24: Original continuation fixtures.** These are MIT RGBDS guests modelled on `fixtures/mbc1-continuation`, each with `.asm`, `.gb`, `manifest.json` (source and ROM SHA-256), `LICENSE.txt`, and a reproduce script in the `fixture-repro` leg.
  - `fixtures/mbc3-rtc-continuation` (`$10`, 32 KiB ROM, 8 KiB RAM):
    - run 1 sets a known clock and writes an SRAM marker;
    - run 2 latches and publishes the registers and marker at fixed WRAM addresses;
    - a mode byte at SRAM `$A010` selects halted and carry variants.
  - `fixtures/mbc2-continuation` (`$06`): nibble pattern; upper nibbles read `$F`.
  - `fixtures/mbc5-continuation` (`$1B`, RAM code `$04`, 128 KiB): markers in banks 0 and 15, which exercises the maximum envelope.
- **D-25: v0.1 save corpus.** `fixtures/save-envelope-v1/` holds 8 KiB and 32 KiB envelopes **actually written by the v0.1 player**, generated once from the v0.1.2 tag, with the generation recorded in the manifest. The files are original, MIT, and carry a SHA-256 manifest. Tests:
  - `player_session_v1_corpus_load`: the embedded ROM digest matches a synthetic in-memory ROM, and the current player loads the file.
  - `player_session_v1_mbc1_write_identical`: re-encoding through the current v1 writer reproduces the bytes exactly.
- **D-26: Player test inventory** (`tests/player/expected-tests.txt`):
  - `player_continuation_mbc3_rtc_resume`
  - `player_continuation_mbc3_rtc_delta`: asserts `result(N) - result(0) == N` for N = 0, 1, 59, 3600, one day, and a value crossing the 511-day carry, so the emulated portion cancels and the test cannot flake.
  - `player_continuation_mbc3_rtc_rollback`
  - `player_continuation_mbc3_rtc_halted`
  - `player_continuation_mbc3_rtc_no_clock`
  - `player_continuation_mbc3_wrong_rom`
  - `player_continuation_mbc2_resume`
  - `player_continuation_mbc5_resume`
  - `player_session_v2_reject_matrix`
  - `player_session_v2_max_size` (exact, one under, one over)
  - v2 fault-injection tests reusing the Phase 4 `PLAYER_SESSION_TEST_FAULT_*` hooks: temp-create, short-write, file-sync, rename and directory-sync failures, interrupt before and after rename. Each proves the old file's digest is unchanged and still loads.
  - `player_session_v1_corpus_load`
  - `player_session_v1_mbc1_write_identical`
  - `player_session_classification_drift`
  - `player_session_rom_cap_8mib`
  - `player_catch_up_policy`
  - `player_session_clock_flag_scope`

  The fresh-process driver reuses the `--child` posix_spawn pattern of `tests/player/test_continuation.c`, passing the clock as an argument.

### E. Loader contradiction matrix and fuzzing (CART-05)
- **D-27: One table-driven test, `tests/test_loader_matrix.c`, with an independent expected-result oracle inside the test.**
  - **CTests:** `loader_contradiction_mbc2`, `_mbc3`, `_mbc5`, `loader_mbc30_variant`, `loader_type_byte_sweep`, `loader_bad_checksum`. These add only a few `expected-tests.txt` lines, so the exact-inventory gate is preserved. One CTest per combination was rejected.
  - **Families:** MBC2 `$05/$06`, MBC3 `$0F-$13`, MBC5 `$19-$1E`.
  - **Header values:** ROM codes `0-8`, `$09`, `$52-$54`, `$FF`; RAM codes `0-6`, `$FF`.
  - **Lengths:** declared, declared-1, declared+1, with a 32 KiB base for unsupported codes. The header checksum is recomputed for every case, and each family gets one bad-checksum probe.
  - **Oracle precedence:**
    1. Over 8 MiB: `ROM_TOO_LARGE`.
    2. Type not in the table: `ROM_TOO_LARGE` above 2 MiB, otherwise `UNSUPPORTED_CARTRIDGE`.
    3. Over the family ceiling (MBC2 2 MiB, MBC3 4 MiB, MBC5 8 MiB): `ROM_TOO_LARGE`.
    4. ROM code above the family maximum: `UNSUPPORTED_ROM_SIZE`.
    5. Bad RAM rule: `UNSUPPORTED_RAM_SIZE`.
    6. Short length: `ROM_TRUNCATED`; long length: `ROM_SIZE_MISMATCH`.
    7. Bad checksum: `INVALID_ROM`.
    8. MBC30 candidate: `UNSUPPORTED_CARTRIDGE_VARIANT`.
    9. Otherwise `OK`.
  - **Explicit must-be-OK rows** guard against the oracle mirroring a core bug: MBC5 code `$08` at exactly 8 MiB, MBC3 `$06` at exactly 2 MiB, MBC2 `$03` at exactly 256 KiB.
  - **No partial mutation:** an MBC1 `$03` instance with an imported non-trivial save is checked after **every** rejection: battery size, bytes and generation; `GBB_NO_RUMBLE`; a WRAM canary after a short run; and finally equality with an untouched twin instance.
  - The matrix also runs under the ASan/UBSan preset.
- **D-28: Fuzz on the 8 MiB bound.** `fuzz_core.c` gets a "synthesised length" mode, `data[0] & 3 == 2`. The input chooses the type, ROM code, RAM code and a length class:
  - declared, declared±1;
  - 2 MiB, 2 MiB+1;
  - 4 MiB, 4 MiB+1;
  - 8 MiB, 8 MiB+1;
  - `SIZE_MAX`.

  The header is written into one lazily zeroed static 8 MiB+1 buffer, and only the first `0x150` bytes are reset per input. Fuzz data is never copied to that length.
  - Add matching deterministic seeds to `tests/test_fuzz_core.c`.
  - Keep `FUZZ_INPUT_LIMIT 65536u` and the other literals unchanged, because `run-bounded-fuzz.sh --self-test` greps for them.
  - Memory stays under the 512 MB RSS limit.

### Claude's Discretion

- Exact player status wording, the `--clock-unix` flag name, and internal helper names.
- Plan split and wave order. Suggested order:
  1. The MBC3 mapper and loader with the D-27 matrix.
  2. The RTC core and the D-13 check.
  3. Battery image and catch-up.
  4. rtc3test and MagenTests admission.
  5. Player v2 and continuation fixtures.
  6. Docs, consumers and the evidence ledger.
- Whether `rtc_add_seconds` lives as one helper or per-field helpers, provided catch-up and sync share it.

### Deferred Ideas (OUT OF SCOPE)

- BGB/VBA-M 44/48-byte footer import/export host adapter (D-026). The D-16 block keeps it expressible.
- Mealybug `mbc3_rtc` as required evidence, once G1 (mgblib font) clears.
- gbclock RTC game, once G3 plugin licences are checked.
- CGB double-speed RTC independence assertion (Phase 11).
- Recovering paused-while-open time in the player (documented limitation; no second mode now).
- `gbb_probe_rom` / cartridge info with a `has_rtc` flag (CGB phases or SHIP-10).
- Mooneye MBC1 backfill; splitting the cartridge section into `src/core/cartridge.c`; a generalised suite verifier. All carried from Phase 8.
- Runner `frame-digest` receipts for rtc3test (option b), only if runner receipts are wanted later.

</deferred>
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| CART-04 | MBC3 `$0F-$13`, 7-bit ROM banking, RAM `00-03`; MBC30/unsupported rejected; MagenTests OOB SRAM passes for MBC1/MBC3/MBC5 | Sections "Code Anchors", "Pattern 1", "Fixtures", "Pitfalls 1-3"; MagenTests ROMs fetched and digest-verified this session |
| CART-05 | Loader rejects every contradictory type/ROM/RAM/length combo for MBC2/MBC3/MBC5 (exact, one-under, one-over), no partial mutation; fuzz covers 8 MiB bound | "Existing tests that must change", "Loader matrix", "Fuzz", verified `validate_header` structure |
| CART-06 | MBC2/MBC3/MBC5 battery data survives fresh-process continuation in the player; every v0.1 save loads unchanged | "Player persistence", "v0.1 corpus recipe", WR-02 removal list |
| RTC-01 | RTC advances only from emulated time; latch/halt/carry/9-bit day; rtc3test passes; CI proves no host clock | "Pattern 2 (lazy RTC)", "rtc3test gate", "No-host-clock check" |
| RTC-02 | Explicit catch-up call with negative/overflow/rollback policy; never a side effect of import | "Pattern 3 (catch-up and battery image)", "Pitfalls 6-9" |
| RTC-03 | Versioned LE core RTC block; player envelope records save time and applies catch-up; original RTC continuation fixture passes across fresh processes | "Pattern 3", "Player persistence", "Fixtures" |
</phase_requirements>

## Summary

The discuss phase already fixed 28 decisions; this research does not reopen them. It grounds them in the code as it exists at `gsd/phase-09-discuss` (parent `30230b2`, Phase 8 merged) and answers the planning questions: where each edit lands, how tests are registered, what existing tests the new rules will break, how fixtures are admitted, what the CI platforms can actually run, and how to order the work.

The core change is small and local. Phase 8's cartridge seam (`cart_kind` enum, `cart_type_table`, `switch (m->cart.kind)` in `read8`/`write8`, `cart_reset_registers`) takes one new kind (`CART_MBC3`) and one new RAM rule, plus a lazy RTC whose only clock is `time_half_dots`. No per-half-dot work is added, so `advance_devices_to` (the hot loop) is untouched and the STOP fast-forward needs no special case. The larger cost is the surrounding evidence: a white-box rtc3test oracle (measured about 7 s per 20 emulated seconds on a Debug build, so budget timeouts accordingly), the MagenTests/rtc3test fixture admissions, a toolchain-portable no-host-clock scan, the loader matrix, player envelope v2, and a v0.1 corpus that must be generated from the `v0.1.2` tag.

Three findings the planner must act on that CONTEXT does not state: (1) existing tests pin behaviour the new rules change (`tests/test_mbc5.c:552` lists type `$0F` as a legacy 2 MiB type; the player has a `player_session_battery_unsupported` test and a `limitations.h` string that must change); (2) the player is macOS-only (CommonCrypto, SDL3, `posix_spawn`), so a "Linux, macOS and Windows" table test of the catch-up policy must live in the core test leg, and a core-registered test named `player_*` would break the player inventory check; (3) the CMake regex dialect has no `\b`, and the core has a function named `apu_sequencer_clock(`, so a naive `clock\(` denylist false-positives.

**Primary recommendation:** Land MBC3 mapper + loader + MagenTests as the tracer slice first (one end-to-end vertical, externally oracled), then RTC core, then battery image/catch-up, with rtc3test, loader matrix, fuzz and the no-host-clock check running in parallel streams that do not edit `src/core/gabbaboy.c`; player v2 and fixtures follow the public API; docs, consumers and the evidence ledger close the phase.

## Project Constraints (from AGENTS.md)

- Original portable C core; explicit ownership/error behaviour; bounded public operations; no hidden globals. Host timing, filesystem, UI and env config stay in adapters (so `time(NULL)` lives only in `src/player`).
- Guard ROM/save/state boundaries against overflow, truncation, excess allocation/work and partial mutation; explicit portable serialization, never raw struct dumps (RTC block and envelope are field-by-field LE).
- Distinguish hardware-backed tests, differential oracles, metamorphic properties, regression fixtures; declare model applicability and expected-failure reasons (label rtc3test "hardware-derived, author-attested"; MagenTests the same; originals are regression/metamorphic).
- No Nintendo boot ROMs, commercial images or unlicensed homebrew. Every third-party fixture needs documented redistribution rights and a digest (MagenTests MIT, rtc3test Unlicense; mgblib-font Mealybug `mbc3_rtc` stays out, gate G1; gbclock stays out, gate G3).
- Automate verification; do not invent manual UAT. Record true perceptual/hardware limits.
- Stop after the phase; never auto-advance. Phase branch + PR; merge only exact-head green CI; squash merge pre-authorized.
- Prefer copy over dependency (user memory): no new packages; inline small code (the 21-byte block, CRC-32 and policy are project code).
- Keep source, API docs, examples, tests and limitation notes in sync (header comments, `docs/cartridge-and-saves.md`, `limitations.h`, consumers).
- Update `.planning/context/LESSONS.md` for concrete lessons (cause/evidence/remedy).

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| MBC3 banking, RAM/RTC register decode, latch | Core (`src/core/gabbaboy.c` cartridge section) | — | Bus-visible hardware behaviour; deterministic; no host input |
| RTC time base (2^23 half-dots/s) | Core, anchored on `time_half_dots` | — | AGENTS.md: emulated time only; D-012 |
| Wall-clock catch-up policy (negative, rollback, overflow) | Player/host adapter (`catch_up_policy`) | Core arithmetic (`gbb_rtc_catch_up`) | Host owns the clock; core exposes only a signed, modular add |
| RTC block serialization (21 B) | Core | — | Part of the battery image contract (D-15/D-16) |
| Save envelope v1/v2, CRC, `saved_at`, atomic write | Player (`src/player/session.c`) | — | File format and filesystem are adapter concerns |
| `time(NULL)` read | Player `main`/clock seam only | — | Core must not link a clock; proven by CI scan |
| Loader contradiction matrix | Core (`validate_header`) | Test-only oracle | Pure function of bytes |
| Fixture admission, digests, install exclusion | Repo/CMake/CI | — | Rights gates; exact-inventory gate |
| No-host-clock proof | CI/CMake (`cmake/CheckCoreNoHostClock.cmake`) | Behavioural slice-invariance test | Static proof plus dynamic complement |

## Standard Stack

No external packages are added; the core is C17 with only `<stddef.h> <stdint.h> <stdlib.h> <string.h>` [VERIFIED: src/core/gabbaboy.c includes, grep this session: `#include "gabbaboy/gabbaboy.h"`, `#include <stdlib.h>`, `#include <string.h>`]. The player already depends on SDL3 `3.4.18` (exact) and CommonCrypto [VERIFIED: CMakeLists.txt `find_package(SDL3 3.4.18 EXACT CONFIG REQUIRED)`; src/player/session.c line 3 `#include <CommonCrypto/CommonDigest.h>`].

### Core
| Tool | Version | Purpose | Why |
|------|---------|---------|-----|
| C17, CMake | CMake floor 3.25.3 (`cmake-floor-3-25-3` CI job); local probe 4.4.3 | build/test | `string(JSON)`, `file(COPY_FILE)`, `file(CREATE_LINK)` already used by scan scripts [VERIFIED: cmake/ScanForbiddenFixtures.cmake] |
| RGBDS 1.0.1 | pinned (macOS zip + Linux x86_64 archive digests in `fixtures/mbc1-continuation/manifest.json`) | project-authored continuation fixtures | Existing pin; do not bump (bumping changes owned-fixture bytes) [CITED: .planning/research/v0.2/STACK.md]. Local `rgbasm` is v1.0.4 [VERIFIED: probe], so local rebuilds of fixture bytes need the pinned 1.0.1 (CI downloads it) |
| RGBDS 0.4.2 (source build, commit `ede982b50a68a6253ffbab17dc4184710b08032f`) | legacy, reproduction only | rtc3test rebuild | rtc3test assembles only on 0.4.x; v0.4.2 release ships a source tarball and Windows zips only (no Linux binary) [VERIFIED: GitHub releases API this session; STACK.md] |
| RGBDS 0.6.1 (commit `69a573923f208d625df589c7a54a18738b07969c`) | legacy, reproduction only | MagenTests rebuild | Makefile passes `rgbasm -L`; release has `rgbds-0.6.1-linux-x86_64.tar.xz` [VERIFIED: releases API]. Record its archive SHA-256 at implementation time |
| Docker | 29.5.2 present locally | optional local legacy-RGBDS source builds (as STACK.md did) | CI uses `ubuntu-22.04` apt build deps (bison flex libpng-dev pkg-config) |

### Package Legitimacy Audit

No npm/PyPI/crates packages are installed in this phase; `package-legitimacy check` is not applicable. Downloaded third-party artifacts are ROM binaries admitted by SHA-256:

| Artifact | Source | Size | SHA-256 | Verdict |
|----------|--------|------|---------|---------|
| `mbc_oob_sram_mbc1.gbc` | alloncm/MagenTests release 0.5.0 | 32768 | `83f1fc44cc26581163b58fe3df426f119dd5813c2e94a187ee0909d6ace1a8bb` | matches CONTEXT D-04 prefix [VERIFIED: curl + shasum this session] |
| `mbc_oob_sram_mbc3.gbc` | same | 32768 | `03e13fa796a9e06fa90f9b396b728c1de9f6e7351aa47a038e33c11d3a8df7dd` | matches [VERIFIED] |
| `mbc_oob_sram_mbc5.gbc` | same | 32768 | `e99f526386f72a8992a72137d0bd9a431b380807b551747bb3baa03421d6f54b` | matches [VERIFIED] |
| `rtc3test.gb` | aaaaaa123456789/rtc3test release `v004` (tag commit `80ae792bf1b3c3387929b912e6df001af3511e24`) | 32768 | `a271013fb37ea1d927b854798401320b220d57abb3ca77f3d318ceb8a9def30d` | matches D-11; header bytes `$147..$149` = `0f 00 00` [VERIFIED: curl + shasum + xxd] |

The rtc3test repo tree at the pinned commit contains no committed ROM (only `.gitignore LICENSE Makefile README.md src tests.md`); the ROM exists only as a release asset, so the `fixture-repro` leg must rebuild with RGBDS 0.4.2 using the repo Makefile recipe (`rgbasm -E -Wno-truncation -Wextra -Wshift-amount -p 0xff -h`, then `rgblink -p 0xff` and `rgbfix -c -i RTC3 -j -k XX -m 0x0f -n 1 -p 0xff -r 0 -t MBC3RTCTEST -v`) [VERIFIED: Makefile fetched at the pinned commit]. License text is the Unlicense ("This is free and unencumbered software released into the public domain.") [VERIFIED]. MagenTests LICENSE is MIT, "Copyright (c) 2022 alloncm" [VERIFIED].

**MagenTests headers** (all three are CGB-compatible `$143=$80`, RAM code `$02`): mbc1 type `$02`, mbc3 type `$12`, mbc5 type `$1A`; the guest compares `[$149]` with 2, writes/reads SRAM in banks 0,1,2 and passes only if bank 2 aliases bank 0 [VERIFIED: xxd of the downloaded ROMs; `src/mbc_oob_sram/main.asm` fetched at pinned commit]. All three are volatile (non-battery) types, so they exercise no battery path. The negative control `$149=$03` changes the guest's `cp a, EXPECTED_SRAM_BANKS` result, so it fails by design in every mapper.

## Code Anchors (verified this session)

Line numbers are for `src/core/gabbaboy.c` at HEAD `03579a4` unless stated.

| Anchor | Where | Verbatim evidence |
|--------|-------|-------------------|
| ROM ceilings | :52-53 | `#define GBB_MAX_ROM_SIZE ((size_t)8u * 1024u * 1024u)` / `#define GBB_LEGACY_MAX_ROM_SIZE ((size_t)2u * 1024u * 1024u)` |
| `cart_kind` | :56 | `typedef enum { CART_ROM_ONLY = 0, CART_MBC1 = 1, CART_MBC2 = 2, CART_MBC5 = 3 } cart_kind;` (ROM_ONLY must stay 0: calloc-zeroed instance) |
| RAM rule enum | :58-63 | `CART_RAM_NONE = 0`, `CART_RAM_8K_OR_32K = 1`, `CART_RAM_MBC2 = 2`, `CART_RAM_MBC5 = 3` |
| `cart_state` | :69-81 | fields `kind, ram_window_mapped, has_battery, has_rumble, rom_bank_lo, rom_bank_hi, ram_bank, ram_enabled, mbc1_mode, rumble_on, rumble_changes(u64)`. `has_timer` is **not** in `cart_state` or `cartridge_info`; add both |
| `cart_type_row` | :83-94 | `{type, kind, ram_window_mapped, has_battery, has_timer, has_rumble, max_rom_code, ram_rule, ram32_max_rom_code, early_ceiling_bytes}`; `has_timer` already exists in the row and is `0u` in every row |
| Table | :96-110 | e.g. `{ 0x1Bu, CART_MBC5, 1u, 1u, 0u, 0u, 0x08u, CART_RAM_MBC5, 0u, GBB_MAX_ROM_SIZE },` |
| `cart_reset_registers` | :120-126 | sets `rom_bank_lo=1`, `rom_bank_hi=0`, `ram_bank=0`, `ram_enabled=0`, `mbc1_mode=0`; "safe on an unloaded (calloc-zeroed) instance". Put `rtc_latch_prev = 0xFF` here (D-08/D-09) |
| `cartridge_info` | :154-161 | `{type, kind, ram_window_mapped, has_battery, has_rumble, ram_size}`; add `has_timer` |
| `struct gbb_instance` | :165- | `rom, rom_size, cartridge_ram, cartridge_ram_size, battery_generation, cart` first; `uint64_t time_half_dots;` at :237 |
| `reset_state` | :520-615 | begins `cart_reset_registers(&m->cart);`; zeroes time at :610 `m->time_half_dots = 0;`. Called from `gbb_create` (:1890), `gbb_reset`, `gbb_load_rom` |
| `read8` | :700 `static uint8_t read8(const gbb_instance *m, uint16_t address)` (**const**); ROM switch :762-786, RAM switch :787-812 |
| `write8` | :858; MBC control-range switch :861-912; RAM-write switch :919-966; non-const `gbb_instance *m` |
| `bus_write` | :1146-1155: computes `timestamp`, calls `advance_devices_to(m, timestamp)` **before** `write8`, so `m->time_half_dots` equals the write's timestamp inside `write8` |
| `read_supported` | :1157-1160: `(address >= 0xA000 && address <= 0xBFFF && m != NULL && ((m->cartridge_ram != NULL && m->cartridge_ram_size != 0u) || m->cart.ram_window_mapped))`. Row `ram_window_mapped=1` is therefore what lets `$0F`/`$11` (no RAM) read the window without `GBB_STOP_UNSUPPORTED_BUS` |
| `advance_devices_to` | :1653 `static void advance_devices_to(gbb_instance *m, uint64_t target)`; per-half-dot loop. Do **not** add RTC work here |
| STOP fast-forward | :2361-2371: `if (instance->stopped) {` ... `instance->time_half_dots += step;` bypasses `advance_devices_to`; a lazy `time_half_dots` anchor is already correct |
| `validate_header` | :1832-1888; order: null/size<0x150, `ceiling` check (`if (size > ceiling) return GBB_ROM_TOO_LARGE;`), `row == NULL` -> `GBB_UNSUPPORTED_CARTRIDGE`, ROM-code>max -> `GBB_UNSUPPORTED_ROM_SIZE`, RAM rule switch, `declared` truncated/mismatch, checksum, MBC1M variant, fill `out_info` |
| `gbb_reset` | :1909; only handles rumble, then `reset_state(instance);` |
| `gbb_load_rom` | :1921; validates, mallocs ROM and `new_ram` (filled `0xFF`), then `memset(&instance->cart, 0, sizeof(instance->cart));` then `reset_state` (so a successful load already gives a fresh RTC; rejected loads mutate nothing) |
| battery API | :1955 `has_battery_ram` (requires `cartridge_ram != NULL && cartridge_ram_size != 0u`; **must change** because `$0F` has no RAM), :1962 size, :1969 copy, :1978 import, :2006 generation |
| `gbb_rumble_state` | :2014: capability-query pattern returning `GBB_NO_RUMBLE`; template for `GBB_NO_RTC` |
| `gbb_run_internal` | :2354 |
| Header enum | `include/gabbaboy/gabbaboy.h:37`: `GBB_NO_RUMBLE             /* loaded cartridge has no rumble line (or no ROM) */` is the last `gbb_error` member; append `GBB_NO_RTC` after it |

**Header comment drift to fix with the change** (verified text): `GBB_ROM_TOO_LARGE` comment says "8 MiB for MBC5 types $19-$1E, 2 MiB for every other type"; `gbb_load_rom` comment lists supported types and the ceiling; the battery comment says "MBC2 type $06 battery images are exactly 512 bytes..." and "Battery RAM is available only for supported battery-backed cartridges" [VERIFIED: include/gabbaboy/gabbaboy.h]. All must be updated for MBC3 (4 MiB ceiling), the timer image and `gbb_rtc_catch_up`.

## Architecture Patterns

### System Architecture (data flow)

```
 Host (player/runner/consumer)                      Core (src/core/gabbaboy.c, no clock)
 ─────────────────────────────                      ──────────────────────────────────────
 ROM bytes ──gbb_load_rom──► validate_header ──► [type row lookup → ceiling → ROM code → RAM rule
                                                   → length → checksum → MBC1M / MBC30 variant]
                                                   │ ok: memset(cart); reset_state (fresh RTC)
 gbb_run(budget) ────────────────────────────────► advance_devices_to / STOP fast-forward
                                                   └─ time_half_dots (u64, the only clock)
 CPU bus write ► bus_write ► advance to timestamp ► write8 ► CART_MBC3 decode
                                                   ├─ $0000 gate  ├─ $2000 ROM bank (7-bit, 0→1, mask)
                                                   ├─ $4000 select (RAM 00-03 | RTC 08-0C | none)
                                                   ├─ $6000 latch: rtc_sync(now); copy live→latched
                                                   └─ $A000 RTC write: rtc_sync(now); store; gen bump if changed
 CPU bus read  ► read8 (const) ► A000: latched byte / RAM byte / $FF
 host clock ──(now - saved_at)──► gbb_rtc_catch_up(int64 secs) ► rtc_sync; rtc_add_seconds (modular)
 gbb_copy_battery ► RAM ‖ RTC block v1 (projected to now on a local copy; const instance)
 gbb_import_battery ◄ RAM ‖ RTC block (validate all → commit together; synced_at = now; never advances)

 Player: file ⇄ envelope v1 (MBC1 $03 only) / v2 (64-byte header + RAM + RTC block, CRC-32 over header+payload)
         time(NULL) → player_catch_up_policy(saved_at,…) → gbb_rtc_catch_up → status line
```

### Recommended structure (additions only)

```
src/core/gabbaboy.c                 # CART_MBC3, CART_RAM_MBC3, rtc_* helpers in the cartridge section
include/gabbaboy/gabbaboy.h         # GBB_NO_RTC, GBB_RTC_BLOCK_SIZE, gbb_rtc_catch_up, comments
src/player/session.c|.h             # v2 envelope, heap buffers, classification from the core, 8 MiB cap
src/player/catch_up_policy.{c,h}    # pure, no SDL/CommonCrypto (testable on all three OS legs)
cmake/CheckCoreNoHostClock.cmake    # source layer + object layer + negative control
cmake/ScanForbiddenFixtures.cmake   # add optional label parameter
fixtures/magentests/                # 3 ROMs + manifest/LICENSE/SOURCES/ELIGIBILITY
fixtures/rtc3test/                  # ROM + 3 .input scripts + expected transcripts + provenance
fixtures/mbc3-rtc-continuation/ mbc2-continuation/ mbc5-continuation/
fixtures/save-envelope-v1/          # real v0.1.2-written envelopes
tests/test_mbc3.c  test_mbc3_rtc.c  test_loader_matrix.c  test_magentests.c  test_rtc3test.c
tests/scripts/reproduce-{magentests,rtc3test,mbc3-rtc-continuation,mbc2-continuation,mbc5-continuation}.sh
tests/scripts/generate-save-envelope-v1.sh
docs/mbc3-rtc-evidence.md
```

### Pattern 1: MBC3 on the Phase 8 seam (D-01..D-03)

Follow the MBC5 branch shape exactly. Write decode (control range) and RAM-window decode live in the two existing `switch (m->cart.kind)` blocks; add `case CART_MBC3`. Reuse `ram_bank` to hold the raw `$4000` selection byte (reset sets 0) so `cart_state` grows only by the RTC fields. Reuse `rom_bank_lo` for the stored translated-and-masked bank (as MBC2 does at :882) or recompute at read; masking must be `bank = v & 0x7F; if (bank == 0) bank = 1; bank &= rom_banks - 1` (translate before mask) [CITED: 09-CONTEXT D-03]. Reads of `$0000-$3FFF` always bank 0.

RAM index for RAM-bearing carts: `(ram_bank & (banks-1)) * 0x2000 + (address & 0x1FFF)` only when the selection is `0x00-0x03`; `0x08-0x0C` returns the latched RTC byte (timer carts only), anything else returns `0xFF`. Writes follow the MBC5 changed-byte generation bump (`if (previous != value) { store; if (has_battery && gen != UINT64_MAX) ++gen; }`) [VERIFIED: pattern at :948-961].

### Pattern 2: Lazy RTC (D-07..D-10)

Make the RTC a self-contained value type so the `const` export path can copy and project it:

```c
/* Sketch — shapes from D-07/D-08/D-16; implement as plain integers in cart_state. */
typedef struct {
    uint8_t  s, m, h, dl, dh;      /* live: dh bit0=day8, bit6=halt, bit7=carry */
    uint8_t  l[5];                 /* latched copy */
    uint8_t  latch_prev;           /* last value written to $6000-$7FFF; $FF = unprimed */
    uint32_t sub;                  /* half-dots into current second, < 2^23 */
    uint64_t synced_at;            /* time_half_dots at last sync */
} rtc_state;

static void rtc_sync(rtc_state *r, uint64_t now);          /* mutating: used by writes/latch/catch-up/reset */
static void rtc_add_seconds(rtc_state *r, uint64_t secs);  /* shared by sync and catch_up */
```

Sync arithmetic (overflow-safe for `el` near 2^64): `el = now >= synced_at ? now - synced_at : 0; synced_at = now; if halted return; secs = (el >> 23) + (((el & 0x7FFFFF) + sub) >> 23); sub = ((el & 0x7FFFFF) + sub) & 0x7FFFFF;` [CITED: 09-CONTEXT D-07]. `(el & mask) + sub < 2^24`, no overflow.

`rtc_add_seconds` closed form, per field with out-of-range handling (derived from the D-08 behaviour table, which is rtc3test-pinned; the differential test against a naive stepper is the correctness guard, not this sketch):

- Field with carry limit `L` (60, 60, 24) and mask `M` (0x3F, 0x3F, 0x1F), incoming ticks `n`:
  - if `f >= L` (out of range): `t0 = (M + 1) - f`; if `n < t0` then `f += n`, no carry-out, done; else `n -= t0; f = 0` (no carry-out for the wrap itself) and continue;
  - normal: `carries = (f + n) / L; f = (f + n) % L`.
- Cascade: seconds carries -> minutes ticks -> hours ticks -> days. Days: `total = day9 + hour_carries`; carry set if `total >= 512` (stays set; sticky); `day9 = total & 511`. Use `uint64_t` throughout. `INT64_MAX` seconds yields about 1.07e14 days, which fits `uint64_t` [VERIFIED by arithmetic: 9.22e18 / 86400].
- Halt: neither `sync` nor `catch_up` credits time while `dh & 0x40`.

Write path (`$A000-$BFFF` with an RTC register selected, gate open): `rtc_sync(now)`; snapshot `{s,m,h,dl,dh,sub}`; apply masked store (S/M `&0x3F`, H `&0x1F`, DL 8-bit, DH `&0xC1`); a seconds write also sets `sub = 0`; compare and bump generation only when changed (D-10). Latch (`$6000-$7FFF`): `if (latch_prev == 0x00 && value == 0x01) { rtc_sync(now); copy live->latched; } latch_prev = value;` no generation bump.

Reset (D-09): `gbb_reset` must run `rtc_sync(now)` **before** `reset_state` (which zeroes `time_half_dots`), then set `synced_at = 0` after. Only for timer carts. Load: existing `memset(&cart,0)` + `reset_state` already yields a fresh RTC with `latch_prev=0xFF` via `cart_reset_registers`.

### Pattern 3: Battery image, catch-up, block (D-14..D-16)

- `has_battery_ram` becomes "has battery image": `loaded && cart.has_battery && (cartridge_ram_size != 0 || cart.has_timer)`. Image size = `cartridge_ram_size + (has_timer ? GBB_RTC_BLOCK_SIZE : 0)`.
- Export: copy RAM, then on a stack copy of `rtc_state` call `rtc_sync(&copy, instance->time_half_dots)` and serialize field by field (offsets in D-16). The instance is `const`; nothing mutates.
- Import: validate size, then decode and validate RAM (MBC2 normalisation does not apply to timer types) and the block into locals; only then commit both and set `synced_at = time_half_dots`. Compare-before-commit so an identical image is a no-op with no generation bump (existing behaviour for RAM at :1978-2003).
- Block validation (`magic GBRT`, version 1, `sub < 2^23`, masks, reserved 0): all failures `GBB_INVALID_ARGUMENT`; wrong length `GBB_BATTERY_SIZE_MISMATCH` (D-16). Note this makes the **return code for a bad RTC block differ from the existing size-mismatch code**: test the exact code per case.
- `gbb_rtc_catch_up(gbb_instance*, int64_t)`: NULL -> `GBB_INVALID_ARGUMENT`; `!loaded || !has_timer` -> `GBB_NO_RTC` (check this before the negative-value check? CONTEXT lists negative as `GBB_INVALID_ARGUMENT` "no mutation" and no-RTC as `GBB_NO_RTC`; pick one order and test it: recommend NULL, then NO_RTC, then negative, matching `gbb_rumble_state`, which validates pointers then capability). Zero -> `GBB_OK` no-op; halted -> `GBB_OK` no change; else `rtc_sync(now)` then `rtc_add_seconds((uint64_t)n)`; generation bump once if live state changed.

### Pattern 4: Pure catch-up policy (D-21/D-22)

`player_catch_up_policy(saved_at, saved_valid, now, now_valid)` returns `{action, status_kind, delta}`; table-tested including `INT64_MIN`/`INT64_MAX` for both timestamps. Compute `delta` as `uint64_t` or with an explicit overflow check (`now - saved_at` overflows `int64_t` when `saved_at < 0 < now`); clamp a forward delta above `INT64_MAX` to `INT64_MAX`. Implement the subtraction as `(uint64_t)now - (uint64_t)saved_at` after establishing `now > saved_at` in signed comparison. [ASSUMED: this exact formulation; the table test must prove it at the extremes.]

### Anti-patterns to avoid
- Per-half-dot RTC stepping in `advance_devices_to` (hot-loop cost, breaks STOP fast-forward).
- Reading `time(NULL)` anywhere under `src/core` or in a `catch_up` convenience wrapper.
- Letting import call catch-up, or mutating the `const` instance on export.
- Registering a core-leg test whose name starts `player_` (see Pitfall 11).
- A CMake `\b` regex in the no-host-clock scan (Pitfall 10).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Per-second RTC stepping | A per-half-dot or per-second loop | One closed-form `rtc_add_seconds` shared by sync and catch-up; naive stepper only inside tests as the oracle | O(1) at `INT64_MAX`; sliced runs identical |
| SHA-256 in new tests | New hash | `src/accept/sha256.c` (`gbb_accept_sha256_hex`) [VERIFIED: gbb_accept.h] | Already the project's digest |
| Scripted input for rtc3test | A new input format | `src/accept/input_script.c` (`gbinput 1`, `wait Nf`, `tap A`) and `tests/acceptance/inputs/*.input` layout [VERIFIED: libbet-no-input.input header `gbinput 1`] | Existing parser, 64-event queue handling |
| CRC-32 for envelope v2 | New implementation | Existing `crc32_bytes` in `src/player/session.c` (IEEE, `0xEDB88320`) [VERIFIED: :221-229] | Same polynomial v1 uses |
| Atomic save / fault hooks | New writer | Existing `atomic_save` and `PLAYER_SESSION_TEST_FAULT_*` [VERIFIED: session.h] | Phase 4 hardened path |
| Install exclusion for new ROMs | New scanner | `cmake/ScanForbiddenFixtures.cmake` with a label parameter | Follows links, checks size+digest |
| Test inventory | Ad-hoc | `tests/expected-tests.txt` + `cmake/ExpectedTests.cmake` | Exact-inventory gate |

## Existing Tests and Text That Will Break (planner must schedule the edits)

| Item | Evidence | Why it breaks | Fix |
|------|----------|---------------|-----|
| `tests/test_mbc5.c:552` | `static const uint8_t legacy[] = {0x00u, 0x01u, 0x03u, 0x05u, 0x06u, 0x0Fu, 0x18u, 0x20u, 0xFFu};` loops both `2 MiB + 1` and `4 MiB` expecting `GBB_ROM_TOO_LARGE` | `$0F` now has a 4 MiB ceiling: with ROM code 6 (declared 2 MiB), length `2 MiB + 1` returns `GBB_ROM_SIZE_MISMATCH`; `4 MiB` returns `GBB_ROM_SIZE_MISMATCH` as well (not too large) | Remove `0x0Fu` from that list and cover `$0F-$13` in the new matrix (D-02, D-27) |
| `tests/test_battery_fuzz.c:127` | `static const uint8_t types[] = {0x01u, 0x02u, 0x03u, 0x13u};` with `new_size == 8192u \|\| new_size == 32768u` assertion | `$13` was a rejected type; it now loads with RAM codes 2/3 (8/32 KiB) and `size_result == GBB_OK`, so loads can now succeed through the `$13` branch; the size assertion still holds. Re-run; likely no edit, but confirm the ROM-code/RAM-code draws do not hit a new accepted combination with a different RAM size (`$13` + code 5 -> `GBB_UNSUPPORTED_CARTRIDGE_VARIANT`) | Run once and update the digest if the seeded output digest is pinned |
| `tests/player/test_session.c:1141-1205` | `session_battery_unsupported` registered as `player_session_battery_unsupported` | The `battery_unsupported` field is removed (D-23) | Delete the test and its line in `tests/player/expected-tests.txt` (last line of the file) |
| `src/player/limitations.h` + `tests/player/test_limitations.c` | text says "MBC2 type $06 and MBC5 types $1B and $1E battery cartridges run, but their progress is not saved yet" | No longer true | New text; keep the `player_limitations` test in sync |
| `src/player/main.c:517,965` | `app->save_identity.battery_unsupported` status branches (two places: `create_machine`, `replace_session_rom`) | field removed | delete both branches |
| `tests/player/test_continuation.c` | hard-codes `CONTINUATION_ROM_SIZE 32768u`, `SAVE_HEADER_SIZE 51u`, `-mbc1-%02x-%08x.gbb` path calc, RAM from `$149` 2/3 only | MBC3/MBC2/MBC5 fixtures differ in size/type | generalise per fixture; keep the "intentionally independent" path calc but extend it |
| `tests/CMakeLists.txt:607` | `set(GBB_MBC_SCAN_DIRS "tracer\|visible-demo\|mbc1-continuation")` exact installed fixture dirs | adding install rules for new fixture dirs would trip `fixture-dirs-mismatch` | Do **not** install the new fixtures (only `tracer`, `visible-demo`, `mbc1-continuation` install today [VERIFIED: CMakeLists.txt install(FILES) blocks]); keep them repo-only |
| `docs/mbc2-mbc5-evidence.md` | cites `player_session_battery_unsupported` | stale | update when the test is removed |
| Public header comments | see above | stale ceilings/types | update in the same change |

## Common Pitfalls

### Pitfall 1: Dropping `time_half_dots` rebase on reset
**What goes wrong:** `reset_state` zeroes time, so un-synced elapsed time since the last RTC access is lost; or `synced_at` > 0 after reset makes `el` = 0 for a long time.
**How to avoid:** `gbb_reset`: `rtc_sync` first, `reset_state`, then `synced_at = 0`. Test: run N half-dots, reset, run M, RTC advanced by (N+M) exactly.
**Warning signs:** RTC "pauses" after the player's reset key.

### Pitfall 2: STOP/HALT paths
**What goes wrong:** Per-half-dot designs miss STOP, whose fast-forward at :2371 bypasses `advance_devices_to`.
**How to avoid:** lazy anchor (already chosen). D-12 CPU-independence test must include a STOP ROM with a queued wake event.

### Pitfall 3: Write timestamp
`write8` sees `time_half_dots == timestamp` only because `bus_write` advances first [VERIFIED :1146-1155]. A white-box test that calls `write8` directly (like `test_mbc5_internal.c`) must set/advance time itself.

### Pitfall 4: `read8` is `const`
RTC reads must return the latched bytes without syncing. Anything that needs a sync (latch, RTC write, export) happens in non-const paths or on a local copy.

### Pitfall 5: `has_battery_ram` still requires RAM
`$0F` has no RAM; leaving the `cartridge_ram_size != 0u` clause makes `gbb_battery_size` return `GBB_NO_BATTERY` for `$0F`. Also `gbb_battery_generation` uses the same helper.

### Pitfall 6: int64 negative / overflow
`gbb_rtc_catch_up` takes `int64_t`; check `< 0` before casting to `uint64_t`. `INT64_MAX` must not overflow day arithmetic (use `uint64_t`, see Pattern 2). Test `catch_up(a)` then `catch_up(b)` equals `catch_up(a+b)` including a pair summing past `INT64_MAX` (use two calls; do not form `a+b` in `int64_t` in the test).

### Pitfall 7: Out-of-range stored values
Guests can store S=60..63, H=24..31, and rtc3test does. Import validation must accept them (D-16) and the arithmetic must handle them (Pattern 2). A "clamp" implementation passes simple tests and fails rtc3test `Invalid rollovers`.

### Pitfall 8: Import advancing the clock
Import sets `synced_at = now`. If it left the old `synced_at`, the next sync would credit all elapsed emulated time again. Test: run N half-dots, export, import into the same instance, export again: identical bytes.

### Pitfall 9: Generation semantics
Latch and elapsed ticks must not bump (D-10); a same-value seconds write with non-zero `sub` **must** bump (sub changed). Catch-up bumps once. Save-cadence tests depend on this.

### Pitfall 10: CMake regex and the denylist
CMake regex has no `\b`; the core contains `apu_sequencer_clock(` (:856) [VERIFIED]. Use an explicit left-context class: `(^|[^A-Za-z0-9_])(time|clock)[ \t]*\(`. Strip `/* */` and `//` comments (or accept comment false-positives knowingly) before the include/pattern scan. The negative control must contain `#include <time.h>` and `time(NULL)`.

### Pitfall 11: Core-leg test names starting `player_`
The player gate runs `ctest -R '^player_'` and checks the JUnit against `tests/player/expected-tests.txt` [VERIFIED: tests/scripts/verify-phase3-player.sh :471-474]. The player build also builds `tests/CMakeLists.txt`, so a test named `player_catch_up_policy` registered in the core inventory would appear in the player junit and fail the exact-inventory diff. See Open Question 1.

### Pitfall 12: Player fresh-process driver argument counts
`main()` requires `argc == 3` for `--battery-smoke-store|resume` [VERIFIED: src/player/main.c:2205-2230 usage check]. Adding `--clock-unix <i64>` changes that check; `player_session_clock_flag_scope` must prove the flag is rejected for normal play and every non-smoke mode.

### Pitfall 13: `time(NULL)` placement vs the smoke-surface guard
`tests/player/verify_script_smoke_surface.cmake` slices `main.c` between `static bool script_scancode(` and `static void destroy_player(player *app) {` and forbids env/network/file-write/persistence tokens [VERIFIED]. Put the clock seam outside that slice (or in `session.c`/a new file).

### Pitfall 14: Oversize buffers on the player stack
v1 uses `uint8_t bytes[PLAYER_SAVE_MAX_SIZE + 1u]` and `uint8_t ram[PLAYER_SESSION_MAX_RAM_SIZE]` on the stack [VERIFIED :464, :483, :681]. v2 reaches 131,200 bytes; use heap with checked `64 + ram_len + rtc_len` (compute in `uint64_t`, validate each length against allowed values before adding).

### Pitfall 15: Filename literal `mbc1`
`battery_file_path` formats `"-mbc1-%02x-%08x.gbb"` for every identity [VERIFIED :249-300]. `$03` must keep this name (v0.1 players read it). Other types may use a different literal (Open Question 3). Mixed-version safety: a v0.1 player never sees a v2 file because only `$03` shares a name and `$03` keeps writing v1.

### Pitfall 16: 8 MiB in the player
`PLAYER_SESSION_MAX_ROM_SIZE` is `(2u * 1024u * 1024u)` today [VERIFIED :19]; `read_rom_file` allocates `MAX + 1`. Raising to 8 MiB also changes the `player_session_max_size`-style tests' assumptions, and `CC_SHA256` takes `CC_LONG` (32-bit) which still fits. A test must tie the constant to the core bound (D-23).

### Pitfall 17: Fuzz memory
A valid 8 MiB MBC5 load mallocs and copies 8 MiB per input. D-28's synthesised mode must not copy fuzz bytes to that length; it hands `gbb_load_rom` a pointer to one static 8 MiB+1 buffer with only the first `0x150` bytes rewritten per input. Keep the `FUZZ_INPUT_LIMIT 65536u`, `FUZZ_OPERATION_LIMIT 16u`, `FUZZ_RUN_LIMIT UINT64_C(2048)`, `FUZZ_INPUT_HALF_DOT_LIMIT UINT64_C(8192)` literals: `run-bounded-fuzz.sh --self-test` greps them [VERIFIED: tests/scripts/run-bounded-fuzz.sh:34-40]. Note `fuzz_core.c` currently selects the mode with `(data[0] & 1u) == 0u` -> `fuzz_loader`, else `fuzz_stateful_api` [VERIFIED: fuzz_core.c `gbb_fuzz_core_one_input`], so D-28's `data[0] & 3 == 2` branch must be tested first and the existing meaning kept for the other residues (`& 3 == 0` loader, `== 1` and `== 3` stateful); the committed `minimized_decoder_crash` seed starts with `0xFF` (residue 3, stateful) and must still reach the same path. Also `make_battery_rom` in the fuzz harness is MBC1 `$03`; the stateful mode only exercises battery import when `battery_size == FUZZ_BATTERY_BYTES` (8192) and otherwise `continue`s, so a fuzz-loaded `$10` (8192 + 21 bytes) is skipped rather than failing a contract; add a timer-cart import case there if RTC block fuzzing is wanted.

### Pitfall 18: Windows object scan
The `native-windows-x64` leg runs `cmake --preset phase1` (Ninja, no explicit toolchain) [VERIFIED: ci.yml], while release builds use the Visual Studio 17 2022 x64 generator with MSVC [VERIFIED: release.yml]. Which compiler the Ninja leg picks is not determinable from the repo. Scan the built static library via `$<TARGET_FILE:gabbaboy_core>`; try, in order, `${CMAKE_NM}`, `nm`, `llvm-nm`, and (MSVC) `dumpbin.exe` found next to `CMAKE_LINKER` or via `find_program`; use `dumpbin /SYMBOLS` and parse `UNDEF` lines. Missing tool = test failure (D-13). Prefer a **denylist** over an allowlist on undefined symbols (sanitizer runtimes `__asan_*`, `__ubsan_*`, `___stack_chk_*`, `___memcpy_chk`, MSVC `__security_check_cookie`/`_fltused` appear legitimately). Observed macOS Debug set: `___memcpy_chk ___memmove_chk ___memset_chk ___stack_chk_fail ___stack_chk_guard _calloc _free _malloc _memcmp _memcpy _memset` [VERIFIED: `nm -u build/libgabbaboy_core.a`]. Plan a Wave-1 spike that adds the check and observes all five CI legs before relying on it.

## Code Examples

### MBC3 RAM/RTC read dispatch (shape)
```c
/* Source: pattern from existing CART_MBC5 branch (gabbaboy.c:800-807); semantics [CITED: 09-CONTEXT D-03]. */
case CART_MBC3:
    if (!m->cart.ram_enabled) return 0xFFu;
    if (m->cart.ram_bank <= 0x03u) {                       /* RAM bank */
        if (m->cartridge_ram == NULL || m->cartridge_ram_size == 0u) return 0xFFu;
        const size_t banks = m->cartridge_ram_size / 0x2000u;
        return m->cartridge_ram[((size_t)m->cart.ram_bank & (banks - 1u)) * 0x2000u
                                + (size_t)(address & 0x1FFFu)];
    }
    if (m->cart.ram_bank >= 0x08u && m->cart.ram_bank <= 0x0Cu && m->cart.has_timer)
        return rtc_read_latched(&m->cart, m->cart.ram_bank);   /* reads masks per D-08 */
    return 0xFFu;                                          /* $04-$07, $0D-$FF: maps nothing */
```

### Battery block field-by-field write (D-16 offsets)
```c
/* Source: [CITED: 09-CONTEXT D-16]. Never memcpy the struct. */
out[0]='G'; out[1]='B'; out[2]='R'; out[3]='T'; out[4]=1;
put_u32_le(out + 5, r.sub);
out[9]=r.s; out[10]=r.m; out[11]=r.h; out[12]=r.dl; out[13]=r.dh;
out[14]=r.l[0]; out[15]=r.l[1]; out[16]=r.l[2]; out[17]=r.l[3]; out[18]=r.l[4];
out[19]=r.latch_prev; out[20]=0;                           /* GBB_RTC_BLOCK_SIZE == 21 */
```

### Fresh-process continuation delta assertion (D-26)
Run 1 (injected clock `T`) sets a known RTC and a SRAM marker and exits through the normal save path. Run 2 (injected clock `T+N`) latches and publishes registers at fixed WRAM addresses. Convert to total seconds modulo 512 days with the carry flag and assert `result(N) - result(0) == N`; the emulated portion cancels because it is identical in every run.

## State of the Art / Comparison notes

| Topic | Choice | Note |
|-------|--------|------|
| Latch | `00` then `01` exact | Pan Docs wording; SameBoy latches on any write, mGBA on `01` unless latched. rtc3test cannot detect this, so original unit tests own it (D-08) |
| Unmapped `$4000` values `$04-$07` | map nothing | Software-model decision, not hardware-qualified (D-03). Label it so in the evidence ledger |
| Future timestamp on reopen | no advance | Matches BGB/VBA-M; SameBoy resets and mGBA goes backwards (rejected as data-destroying) |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Exact overflow-safe formulation of the player policy delta (`(uint64_t)now - (uint64_t)saved_at` after a signed `now > saved_at` test) | Pattern 4 | Wrong clamp at the extremes; the mandated table test catches it |
| A2 | On the `native-windows-x64` CI leg the Ninja preset resolves to MSVC or MinGW (unknown); `dumpbin` or `nm` reachable | Pitfall 18 | Object scan fails on that leg; a Wave-1 spike removes the uncertainty |
| A3 | `test_battery_fuzz` pinned digest may or may not change when `$13` begins to load | Existing tests table | One test needs a digest update; run once to find out |
| A4 | Emulated run time of rtc3test suites in ASan CI stays under a 300 s TIMEOUT (Debug measured about 0.26 s wall per emulated second; ASan factor not measured) | Validation | Raise TIMEOUT or split; D-11 already budgets 60 s emulated per suite |
| A5 | Recommended `GBB_NO_RTC` vs `GBB_INVALID_ARGUMENT` check order (NULL, NO_RTC, negative) | Pattern 3 | Cosmetic, but pick one and test it |
| A6 | `-cart-` filename literal for non-`$03` v2 files | Open Question 3 | Cosmetic; changing later orphans saves, so decide before release |
| A7 | RGBDS 0.4.2 source build fits the 15-minute `fixture-repro` job timeout when added as its own job | Fixtures | Add a separate job with a longer timeout (STACK.md built it in Alpine containers) |

## Open Questions

1. **Where does `player_catch_up_policy` (the pure table test) live?**
   - Known: D-21 wants it tested on Linux, macOS and Windows; D-26 lists it in `tests/player/expected-tests.txt`; the player target is macOS-only and its inventory gate runs `-R '^player_'`.
   - Recommendation: put the pure policy in `src/player/catch_up_policy.{c,h}` with no SDL; register the cross-OS table test in the **core** inventory under a non-`player_` name (for example `catch_up_policy_table`); keep `player_session_*` tests for the integration. This is a documented deviation from D-26's inventory placement but satisfies D-21's explicit cross-OS requirement.
2. **Check order for `gbb_rtc_catch_up` errors** (A5). Recommend NULL -> NO_RTC -> negative.
3. **Filename literal for non-`$03` envelopes.** Recommend `-cart-%02x-%08x.gbb` for v2-only types, `-mbc1-...` unchanged for `$03` (A6).
4. **Does `player_session_identify_rom` survive?** It is used for ROM-only smoke identification (main.c ~1686) before any machine exists. D-23 derives classification from the core after load. Recommend splitting: `identify_rom` yields digest + type only; `replace_rom` fills `ram_size`, `battery_backed`, `rtc_present` from `gbb_battery_size` after `gbb_load_rom`.
5. **MBC3 4 MiB ceiling and ROM code `$07`.** Under D-02 any `$07` header is a MBC30 candidate (variant) after the checksum, so MBC3 effectively loads ROM codes `$00-$06`; the row's `max_rom_code=$07` exists only so `$07` reaches the variant check instead of `GBB_UNSUPPORTED_ROM_SIZE`. Document this in the evidence ledger so it does not read as an inconsistency.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| cmake, ninja | build/test | yes | 4.4.3 / 1.13.2 | CI floor job covers 3.25.3 |
| python3 | repro scripts, scratch tooling | yes | 3.14.4 | — |
| curl, git, gh | fixture fetch, tag archive | yes | 8.7.1 / 2.41.0 / 2.101.0 | — |
| `nm` | object scan (macOS dev) | yes (llvm-nm 'GNU compatible') | — | Windows: `dumpbin` (unverified, A2) |
| rgbasm | fixture rebuilds | yes but v1.0.4, not the 1.0.1 pin | 1.0.4 | download pinned 1.0.1 archives (digests in manifests) |
| RGBDS 0.4.2 / 0.6.1 | rtc3test / MagenTests reproduction | no (build/download needed) | — | Docker present locally; CI apt/source or release archive |
| SDL3 3.4.18 | player tests | built from source by `verify-phase3-player.sh` | — | none; macOS arm64 only |
| Network access | fetching ROMs | yes (used this session) | — | — |

**Missing with fallback:** legacy RGBDS binaries (build in CI or Docker). **Blocking:** none.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | CTest (C test executables with REQUIRE macros; CMake `-P` scripts for fixture/scan checks) |
| Config | `tests/CMakeLists.txt`; exact inventory `tests/expected-tests.txt` (320 names today [VERIFIED: wc]) enforced at configure time by `gabbaboy_verify_registered_tests()` and in CI by `.github/scripts/verify-test-inventory.sh`; player inventory `tests/player/expected-tests.txt` (57 names) |
| Presets | configure `cmake --preset phase1`; build `cmake --build --preset phase1`; test `ctest --preset phase1`; sanitizers `phase1-asan` (Linux only); floor `cmake-3.25.3` (+ `-relocated`) [VERIFIED: CMakePresets.json] |
| Quick run | command **Q** below |
| Full suite | commands **F1-F3** below |
| Player (macOS arm64) | command **P** below |
| CMake floor | `bash .github/scripts/verify-cmake-floor.sh` |

```bash
# Q  quick slice (everything except the slow rtc3test and player cases)
cmake --preset phase1 && cmake --build --preset phase1
ctest --preset phase1 -R '^(mbc3_|magentests_|loader_|rtc_|no_host_clock|catch_up_)'

# F1 full core suite with the exact-inventory check (same as CI)
ctest --test-dir build --output-on-failure --no-tests=error --output-junit ctest.xml
bash .github/scripts/verify-test-inventory.sh build/ctest.xml tests/expected-tests.txt --installed

# F2 sanitizer leg (Linux only; GABBABOY_ENABLE_SANITIZERS is rejected elsewhere)
cmake --preset phase1-asan -DGBB_TEST_INSTALL_PREFIX= && cmake --build --preset phase1-asan
ctest --preset phase1-asan --output-junit ctest.xml
bash tests/scripts/run-bounded-fuzz.sh --self-test
GBB_BUILD_DIR=build-asan bash tests/scripts/run-bounded-fuzz.sh --fast

# F3 rtc3test slice (slow)
ctest --preset phase1 -R '^rtc3test_'

# P  player (macOS arm64; builds SDL3 3.4.18, runs -R '^player_', checks tests/player/expected-tests.txt)
bash tests/scripts/verify-phase3-player.sh --build-package
```

New CTest names are the CONTEXT names (D-05, D-06, D-11, D-12, D-13, D-18, D-26, D-27). Proposed additional core names for items CONTEXT does not name: `mbc3_*` mapper cases (`mbc3_header_matrix`, `mbc3_rom_banking`, `mbc3_ram_banking`, `mbc3_ram_gate`, `mbc3_unmapped_select`, `mbc3_absent_ram`, `mbc3_reset`, `mbc3_tracer`), `rtc_*` model cases (`rtc_closed_form_differential`, `rtc_add_composes`, `rtc_slice_invariance`, `rtc_cpu_independence`, `rtc_latch_edges`, `rtc_halt_carry_wrap`, `rtc_time_near_max`, `rtc_reset_rebase`, `rtc_mutation_*`), `rtc_catch_up_*`, `rtc_block_*` (round-trip, corruption matrix), `no_host_clock`, `no_host_clock_selftest`, `catch_up_policy_table`.

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| CART-04 | MBC3 banking/RAM/RTC select, variants rejected | unit + hardware-derived (MagenTests) | `ctest --preset phase1 -R '^mbc3_'` and `-R '^loader_mbc30_variant$'` | Wave 0 |
| CART-04 | MagenTests OOB SRAM mbc1/3/5 + negative control + digest + not installed | oracle + scan | `ctest --preset phase1 -R '^magentests_'` | Wave 0 (`fixtures/magentests/`, `tests/test_magentests.c`) |
| CART-05 | Full contradiction matrix, no partial mutation, ASan too | table-driven oracle | `ctest --preset phase1 -R '^loader_'`; `ctest --preset phase1-asan -R '^loader_'` | Wave 0 (`tests/test_loader_matrix.c`) |
| CART-05 | 8 MiB fuzz bound | deterministic seeds + bounded libFuzzer | `ctest --preset phase1 -R '^fuzz_core_regressions$'`; the two `run-bounded-fuzz.sh` commands in F2 | edit existing |
| CART-06 | MBC2/MBC3/MBC5 fresh-process continuation, v1 unchanged, v2 reject matrix, fault injection | player integration (macOS) | command P | Wave 0 |
| RTC-01 | rate, latch, halt, carry, 9-bit day | hardware-derived (rtc3test) + metamorphic/differential originals | `ctest --preset phase1 -R '^rtc3test_'`; `ctest --preset phase1 -R '^rtc_'` | Wave 0 |
| RTC-01 | no host clock in core | static scan + negative control + behavioural | `ctest --preset phase1 -R '^no_host_clock'` | Wave 0 (`cmake/CheckCoreNoHostClock.cmake`) |
| RTC-02 | catch-up: zero/negative/INT64_MAX/halted/carry/composability; import never advances | unit | `ctest --preset phase1 -R '^rtc_(catch_up_|import_)'` | Wave 0 |
| RTC-03 | RTC block round-trip across instance and reset; corruption matrix | unit | `ctest --preset phase1 -R '^rtc_block_'` | Wave 0 |
| RTC-03 | player `saved_at`, catch-up on reopen, rollback, halted, no clock | player integration | command P (names `player_continuation_mbc3_*`) | Wave 0 |
| Cross | installed C/C++ consumers see new API | installed consumer | `ctest --preset phase1 -R '^installed_consumer'` (needs `GBB_TEST_INSTALL_PREFIX`; CI passes it) | edit `tests/consumers/{c,cpp}` |

### Sampling Rate
- **Per task commit:** the plan's own `-R` slice (under 30 s except rtc3test).
- **Per wave merge:** `ctest --preset phase1` (full; rtc3test about 3 x 10-30 s Debug) plus `phase1-asan` for core-touching waves.
- **Phase gate:** CI exact-head green on all required legs (`native-linux`, `native-macos`, `native-windows`, `linux-sanitizers`, `cmake-floor`, `macos-player-package`, `fixture-repro`) before `/gsd-verify-work`.
- **rtc3test timing:** measured about 5.1 s wall for 20 emulated seconds (`libbet-no-input`) on a Debug build on this machine, so about 14 s total for the three suites in Debug; give each `TIMEOUT 300` to cover ASan [VERIFIED: timed run this session; ASan factor ASSUMED, A4].

### Wave 0 Gaps
- [ ] `tests/test_mbc3.c`, `tests/test_mbc3_rtc.c`, `tests/test_loader_matrix.c`, `tests/test_magentests.c`, `tests/test_rtc3test.c`, `tests/test_rtc_battery.c` (or fold into `test_battery.c`)
- [ ] `cmake/CheckCoreNoHostClock.cmake` and its negative-control scratch source
- [ ] `fixtures/{magentests,rtc3test,mbc3-rtc-continuation,mbc2-continuation,mbc5-continuation,save-envelope-v1}/` with manifests, licenses, SHA-256 digests
- [ ] `tests/scripts/reproduce-{magentests,rtc3test,...}.sh`, `generate-save-envelope-v1.sh`; extend `.github/workflows/fixture-repro.yml` with legs (legacy RGBDS legs need their own job)
- [ ] label parameter in `cmake/ScanForbiddenFixtures.cmake` (default keeps "mooneye" strings so existing tests' regexes still match)
- [ ] mutation hook for the D-12 mutation controls (compile-time `GBB_RTC_MUTATION_*` defines on a mutant copy built the same way as the ninth-bit mutant at `tests/CMakeLists.txt:72-116`, which pattern-replaces text in `gabbaboy.c` with an exactly-once anchor check)
- [ ] registrations in `tests/expected-tests.txt` and `tests/player/expected-tests.txt` for every new name (the registered-vs-expected comparison fails configure otherwise)
- [ ] extend `tests/player/CMakeLists.txt` regex `^player_continuation_(resume|missing_save|wrong_rom|mutated_payload)$` and the `player_session_[a-z0-9_]+` dispatch

## Security Domain

`security_enforcement` is enabled (absent = enabled; `.planning/config.json` has `"security_enforcement": true`, `security_asvs_level: 1`).

### Applicable ASVS Categories
| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | — (local desktop app) |
| V3 Session Management | no | — |
| V4 Access Control | partly | per-user pref dir, advisory lock, existing symlink/target-type rejection tests (`player_session_symlink`, `player_session_target_type_rejection`) |
| V5 Input Validation | **yes** | exact-length checks before allocation; bounded loader; RTC block field validation; v2 header canonical-zero checks; fuzz targets |
| V6 Cryptography | no (CRC-32 is accident detection, not authentication; say so in docs) | — |
| V12 Files/Resources | yes | atomic same-directory replace, preserve-then-fresh on reject, no partial mutation |

### Known Threat Patterns
| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Crafted save with huge `ram_len`/`rtc_len` | DoS / Tampering | allow-list `ram_len` values (0, 512, 8192, 32768, 65536, 131072), `rtc_len` in {0,21}, compute total in `uint64_t`, require file size equal; heap-allocate after checks |
| Flipped `saved_at` to inject a catch-up | Tampering | CRC covers header (v2); worst case is a wrapped RTC (modular, bounded); documented as not authentication |
| Clock rollback / future timestamp | Tampering | policy: no advance, re-stamp on next save; negative core value rejected |
| Truncated/partial import corrupting RAM | Tampering | validate all, commit together; before/after byte comparison in the corruption matrix |
| Integer overflow in RTC math | Tampering | `uint64_t` closed form; `INT64_MAX` test; `time_half_dots` near `UINT64_MAX` test |
| 8 MiB ROM resource exhaustion | DoS | per-type ceiling checked before allocation; `SIZE_MAX` length returns `GBB_ROM_TOO_LARGE` |
| Ambient clock injection flag in normal play | Spoofing | `--clock-unix` only on smoke child modes; scope test |

## Fixtures: Admission Mechanics (verified patterns)

- **Manifest shape the scan reads:** `fixtures[].{size_bytes, sha256}` (`string(JSON GET ... fixtures <i> size_bytes|sha256)` in `cmake/ScanForbiddenFixtures.cmake`); failure tokens `scan-dir-empty`, `mooneye-installed: <path>`, `fixture-dirs-mismatch`, success line `mooneye-mbc absent from scanned tree files=N`. Existing tests assert those strings (`tests/CMakeLists.txt:635-645`), so add `GBB_FORBIDDEN_LABEL` defaulting to the current strings; for MagenTests the path-component check is `lowered MATCHES "magentests"` and the token `magentests-installed:`.
- **Pattern for the new scan tests** is the `gbb_add_mbc_scan_test` function at `tests/CMakeLists.txt:624-634` (runs the scan through `tests/expect_exit.cmake` with `GBB_EXPECT_CODE`/`GBB_EXPECT_REGEX`) and the `libbet_install_tree` fixture (`FIXTURES_SETUP libbet_install`). New `magentests_not_installed` must set `FIXTURES_REQUIRED libbet_install` the same way.
- **Original-fixture layout** (copy `fixtures/mbc1-continuation`): `continuation.asm`, `.gb`, `manifest.json` with `id/source/source_sha256/license/build{assembler,version,archive,archive_sha256,ci_archive,ci_archive_sha256,recipe}/rom/size_bytes/sha256/cartridge/profile/protocol/scope_limits`, `LICENSE.txt`; `tests/scripts/reproduce-mbc1-continuation.sh` asserts every manifest field then `cmp`s the rebuilt bytes [VERIFIED: file read]. The `fixture-repro.yml` first job reads the RGBDS pin from the existing manifests and fails if any fixture's pin differs, so the new fixtures must carry the same `build` object. rgbfix flags: MBC3+TIMER+RAM+BATT `-m 0x10`, RAM code `-r 2` for 8 KiB (`-r 3` is 32 KiB); `$06` MBC2 `-m 0x06 -r 0`; `$1B` `-m 0x1b -r 4` (128 KiB, RAM code `$04`).
- **mbc5-banking is not installed**, only `tracer`, `visible-demo`, `mbc1-continuation` [VERIFIED].
- **THIRD_PARTY_NOTICES.md** gets MagenTests (MIT, alloncm), rtc3test (Unlicense), and hardware.inc (CC0) entries; record the rtc3test font observation (G7: low risk).

## v0.1 Save Corpus Recipe (D-25)

`v0.1.2` exists locally (`git cat-file -t v0.1.2` = `commit`, `3fa00be9d8ad8ca12a9bc4672d4851db1eabfa8e`, 2026-10-10). Its `src/player/session.c` differs from HEAD only by the 3-line `battery_unsupported` block in `player_session_identify_rom` [VERIFIED: `git diff v0.1.2 HEAD -- src/player/session.c`], so v0.1.2's writer is byte-compatible with the current v1 writer; and it contains `tests/player/test_continuation.c`, `test_session.c` and the `mbc1-continuation` fixture [VERIFIED: ls-tree].

Reproducible recipe for `tests/scripts/generate-save-envelope-v1.sh` (macOS arm64, manual one-time; the player is macOS-only so this is not a CI leg):
1. `git archive v0.1.2 | tar -x -C "$(mktemp -d)"` (outside the repo; untrusted-extraction hygiene: fresh empty dir, pass paths as args).
2. Configure that tree with the same SDL prefix recipe as `verify-phase3-player.sh` (`-DGABBABOY_BUILD_PLAYER=ON -DBUILD_TESTING=ON`, SDL3 `3.4.18` built from the pinned archive `9c75cf16...334a3`).
3. Link a small throwaway driver (kept inside the generator script, not committed as product code) against that tree's `gabbaboy-player-session-test` target. For each of (a) `fixtures/mbc1-continuation/continuation.gb` (8 KiB RAM, type `$03`) and (b) a synthetic `$03` ROM with RAM code `$03` (32 KiB) written to a temp file: `player_session_test_set_pref_path(dir)`, create an instance, `player_session_replace_rom`, `player_session_load_battery`, put a non-trivial RAM pattern in with `gbb_import_battery`, then `player_session_save_battery`, which exercises the real v0.1.2 writer. Copy the two resulting `.gbb` files out of `dir`.
4. Record in `fixtures/save-envelope-v1/manifest.json`: tag, tag commit SHA, SDL version/digest, compiler, platform, ROM digests, envelope SHA-256 and sizes (51+8192 = 8243 and 51+32768 = 32819).
5. Tests: `player_session_v1_corpus_load` (embedded ROM digest equals the synthetic ROM digest; current player loads it), `player_session_v1_mbc1_write_identical` (current writer reproduces the file byte for byte).

## Wave / Plan Decomposition (recommended)

Constraint: `src/core/gabbaboy.c` and `include/gabbaboy/gabbaboy.h` are single-owner per wave (all core plans edit the same cartridge section). Streams that only add tests, fixtures, scripts or CMake files can run in parallel.

| Wave | Plan | Scope | Depends | Files owned (no overlap within wave) |
|------|------|-------|---------|--------------------------------------|
| 1 | 09-01 **Tracer slice**: MBC3 mapper + header validation + MBC30 variant + MagenTests admission end to end | `CART_MBC3`, `CART_RAM_MBC3`, five rows, `has_timer` plumbed, `read8`/`write8` MBC3 banking and RAM (RTC select decodes but maps `$FF`/ignored until Plan 03), fixture dir, `test_magentests.c`, `mbc3_*` unit tests, label param in scan script, `magentests_not_installed`; fix `test_mbc5.c:552`; `loader_mbc30_variant` | — | `gabbaboy.c`, `gabbaboy.h` (comments), `tests/test_mbc3.c`, `test_magentests.c`, `fixtures/magentests/`, `cmake/ScanForbiddenFixtures.cmake`, `tests/CMakeLists.txt` (MBC3 + magentests blocks), `expected-tests.txt` |
| 1 (parallel) | 09-02 No-host-clock check + fuzz 8 MiB | `cmake/CheckCoreNoHostClock.cmake` (+ negative control, CI spike on all legs), `fuzz_core.c` synthesised mode, `test_fuzz_core.c` seeds | — | new cmake file, `tests/fuzz_core.c`, `tests/test_fuzz_core.c`; its own CMake block |
| 2 | 09-03 RTC core | `rtc_state`, sync, `rtc_add_seconds`, latch/halt/write masks, reset rebase, generation rule, mutation hook, `test_mbc3_rtc.c` | 01 | `gabbaboy.c`, `tests/test_mbc3_rtc.c` |
| 2 (parallel) | 09-04 Loader matrix | `test_loader_matrix.c` with independent oracle, all `loader_*` D-27 names, no-partial-mutation checks, ASan run | 01 | `tests/test_loader_matrix.c` (+ fixes to `validate_header` only if the matrix finds a defect, coordinate with 09-03) |
| 3 | 09-05 Battery image + catch-up + block | `has_battery_ram` generalisation, 21-byte block, export projection, import, `gbb_rtc_catch_up`, `GBB_NO_RTC`, header API/comments, core tests (round trip, corruption matrix, catch-up edges) | 03 | `gabbaboy.c`, `gabbaboy.h`, `tests/test_rtc_battery.c` |
| 3 (parallel) | 09-06 rtc3test admission and oracle | `fixtures/rtc3test/`, three `.input` scripts and expected transcripts, `test_rtc3test.c`, negative control, legacy-RGBDS repro script | 03 | `fixtures/rtc3test/`, `tests/test_rtc3test.c`, scripts, CMake block |
| 4 | 09-07 Player v2 core | `catch_up_policy.{c,h}`, envelope v2 codec on the heap, classification from core (WR-02), 8 MiB cap, clock seam and `--clock-unix`, status line, remove `battery_unsupported`, update `limitations.h` and tests, fault-injection coverage for v2 | 05 | `src/player/*`, `tests/player/test_session.c`, `tests/player/CMakeLists.txt`, `expected-tests.txt` (player) |
| 4 (parallel) | 09-08 Continuation fixtures + v1 corpus | three original fixtures (+ repro scripts), `save-envelope-v1` corpus from `v0.1.2`, generalised `test_continuation.c` and `player_continuation_*` tests | 05 (API), integrates with 07 | `fixtures/*continuation*`, `fixtures/save-envelope-v1/`, `tests/player/test_continuation.c`, `tests/scripts/*` |
| 5 | 09-09 Docs, consumers, ledger, CI wiring | installed C/C++ consumers for D-18, `docs/cartridge-and-saves.md`, new `docs/mbc3-rtc-evidence.md`, update `docs/mbc2-mbc5-evidence.md`, `docs/support/unreleased.md`, `THIRD_PARTY_NOTICES.md`, `CHANGELOG`/limitations, `fixture-repro.yml` legs, LESSONS, requirement traceability | all | docs, consumers, workflow |

The tracer slice (09-01) is one vertical with an external oracle: fixture -> loader -> mapper -> screen -> CTest -> install exclusion. It deliberately lands before RTC so the Phase 8 seam pattern is proved for MBC3 and the legacy-ceiling test fix lands early.

## Sources

### Primary (HIGH confidence)
- Repository code read this session: `src/core/gabbaboy.c`, `include/gabbaboy/gabbaboy.h`, `src/player/session.c|.h`, `src/player/main.c`, `src/player/limitations.h`, `tests/CMakeLists.txt`, `tests/player/CMakeLists.txt`, `tests/player/expected-tests.txt`, `tests/fuzz_core.c`, `tests/test_fuzz_core.c`, `tests/test_mbc5_internal.c`, `tests/test_mbc5.c`, `tests/test_battery_fuzz.c`, `tests/test_loader_fuzz.c`, `cmake/ScanForbiddenFixtures.cmake`, `cmake/ExpectedTests.cmake`, `CMakePresets.json`, `CMakeLists.txt`, `.github/workflows/ci.yml`, `fixture-repro.yml`, `release.yml` (Windows build), `tests/scripts/reproduce-mbc1-continuation.sh`, `verify-phase3-player.sh`, `run-bounded-fuzz.sh`, `fixtures/mbc1-continuation/manifest.json`, `fixtures/mooneye-mbc/*`.
- MagenTests release 0.5.0 assets and repo at `3f9c090f16e5a721db776febb9ba7d773e1c819c` (downloaded, digested, headers read): https://github.com/alloncm/MagenTests
- rtc3test v004 release asset, repo Makefile and LICENSE at `80ae792bf1b3c3387929b912e6df001af3511e24`: https://github.com/aaaaaa123456789/rtc3test
- RGBDS releases API (v0.4.2, v0.6.1 asset lists, v0.6.1 commit): https://github.com/gbdev/rgbds

### Secondary (MEDIUM confidence)
- `.planning/research/v0.2/STACK.md` and `SUMMARY.md` (legacy RGBDS pins, rtc3test behaviour notes), `09-CONTEXT.md` (researcher prototype results: rtc3test 23/23, mutation controls), not re-run here.

### Tertiary (LOW confidence)
- Windows Ninja compiler selection on `windows-2022` (A2), ASan runtime factor for rtc3test (A4).

## Metadata

**Confidence breakdown:**
- Code anchors, test mechanics, fixture digests, existing-test breakage: HIGH (read/probed this session)
- RTC closed-form details: MEDIUM (derived from D-08; the differential test is the guard; CONTEXT reports a prototype passing 23/23)
- Windows object scan, legacy RGBDS CI legs, ASan timing: MEDIUM/LOW (not runnable here)
- Pitfalls: HIGH for 1-5, 8-18 (verified in code); MEDIUM for 6-7 (arithmetic reasoning)

**Research date:** 2026-10-11
**Valid until:** 2026-11-10 (stable; re-check only if `main` moves under Phase 9 or the pinned upstream commits change)
