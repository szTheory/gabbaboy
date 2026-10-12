# Phase 9: MBC3, Deterministic RTC and Cartridge Persistence - Context

**Gathered:** 2026-10-11
**Status:** Ready for planning
**Method:** Four advisor researchers ran in parallel, each from several angles and each with an adversarial pass. The areas were:
1. MBC3 mapping, variant rejection, MagenTests and the loader matrix.
2. The RTC core model and the rtc3test gate.
3. The RTC public API and the battery block.
4. The player envelope and fresh-process continuation.

The RTC researcher prototyped the recommended model on a scratch copy of the core and ran pinned rtc3test v004 on it: 23/23 tests passed across the three suites. Mutations of the model failed where expected. The MBC3 researcher ran the MagenTests ROMs against the current core.

Per the owner's standing instruction (discuss fan-out, auto-follow), the reconciled recommendations were adopted without asking about each area. The only escalation candidate was the public RTC prototype, judged an append-only addition (see D-17). Conflicts and their resolutions are recorded in the decisions and in `09-DISCUSSION-LOG.md`.

<domain>
## Phase Boundary

Phase 9 delivers:
- MBC3 (`$0F-$13`): 7-bit ROM banking, RAM banks `00-03`, and an RTC that advances only from emulated time (2^23 half-dots per second).
- Explicit, host-applied wall-clock catch-up (`gbb_rtc_catch_up`).
- RTC state persisted as a versioned little-endian block inside the battery image.
- Player battery persistence for MBC2, MBC3 and MBC5 across fresh processes: envelope v2 for new types, with v1 kept for MBC1.
- The full loader contradiction matrix, and fuzzing up to the 8 MiB bound.

Requirements: CART-04, CART-05, CART-06, RTC-01, RTC-02, RTC-03.

**Not in this phase:**
- MBC30 support. It is rejected with an explicit error.
- The CGB profile and CGB double-speed RTC independence. Phase 11 asserts double-speed independence.
- BGB/VBA-M 44/48-byte RTC footer interop. D-026 makes this a host adapter, deferred.
- Mealybug `mbc3_rtc` in required CI (G1) and gbclock (G3).
- Host haptics.
- `gbb_probe_rom` / `gbb_get_cartridge_info` (CGB phases or SHIP-10).
- Save states.
- The Mooneye MBC1 backfill.

</domain>

<decisions>
## Implementation Decisions

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

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Scope and requirements
- `.planning/ROADMAP.md` §Phase 9: goal, five success criteria, rights gates (G1, G3), research flag DEEP.
- `.planning/REQUIREMENTS.md`: CART-04, CART-05, CART-06, RTC-01, RTC-02, RTC-03; SHIP-10 (consumers exercise RTC catch-up); future list (BGB footer, haptics, gbclock).
- `.planning/context/DECISIONS.md`: D-009 (half-dot timeline), D-012 (injected RTC elapsed input), D-026 (core-native RTC block, footer interop deferred, MBC30 unsupported, mgblib font out of required CI).
- `AGENTS.md`: fixture rights and digests, no host clock in core, stop after phase.

### v0.2 research
- `.planning/research/v0.2/SUMMARY.md`: P5 (MBC3 + RTC) deliverables, gates G1/G3/G7, rtc3test and MagenTests pins.
- `.planning/research/v0.2/FEATURES.md`: MBC3/RTC behaviour and save sections.
- `.planning/research/v0.2/ARCHITECTURE.md` §7–8: lazy RTC and the public API sketch. §180's latch-bumps-generation is superseded by D-10, and the `uint64_t` catch-up sketch by D-14.
- `.planning/research/v0.2/PITFALLS.md`: V2-13..V2-16.
- `.planning/research/v0.2/STACK.md`: legacy RGBDS 0.4.x (rtc3test) and 0.6.1 (MagenTests) reproduction.

### Prior phase decisions and evidence
- `.planning/phases/GB-08-cartridge-seam-mbc5-and-mbc2/08-CONTEXT.md`: seam shape (D-01..D-03), D-05 header check order, D-18 translate-then-mask, D-20 VARIANT meaning, sibling fixture directories, install scan.
- `.planning/phases/GB-08-cartridge-seam-mbc5-and-mbc2/08-REVIEW-DISPOSITION.md`: WR-02, closed by D-23.
- `docs/mbc2-mbc5-evidence.md`, `docs/mbc1-evidence.md`: ledger style for the new `docs/mbc3-rtc-evidence.md`.
- `docs/cartridge-and-saves.md`: v1 envelope contract and the migration promise.
- `.planning/milestones/v0.1-phases/`: Phase 4 battery continuation, atomic save and fault hooks.

### External primary sources
- Pan Docs MBC3: https://gbdev.io/pandocs/MBC3.html
- rtc3test v004 at `80ae792bf1b3c3387929b912e6df001af3511e24`: https://github.com/aaaaaa123456789/rtc3test (`tests.md`, `src/*.asm`)
- MagenTests at `3f9c090f16e5a721db776febb9ba7d773e1c819c`: https://github.com/alloncm/MagenTests (`src/mbc_oob_sram/main.asm`, `Makefile`)
- BGB RTC save format: https://bgb.bircd.org/rtcsave.html
- SameBoy `Core/memory.c` and `Core/gb.c`; mGBA `src/gb/mbc/mbc.c`. These are comparison only and are not hardware evidence.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `cart_type_table` / `cart_kind` / `cart_state` in `src/core/gabbaboy.c` (~lines 96-115). Add the MBC3 rows and RTC fields here. `GBB_MAX_ROM_SIZE` is already 8 MiB (line 52).
- `has_battery_ram`, `gbb_copy_battery`, `gbb_import_battery` (~1955-2012): generalise these to the battery image.
- `gbb_rumble_state` (~2018): pattern for a capability query returning a `GBB_NO_*` code.
- `reset_state` (~520) and `gbb_reset` (~1909): the RTC rebase hook point (D-09).
- `validate_header` (~1832): add the MBC30 check after the checksum, next to MBC1M.
- `tests/test_mbc5_internal.c`: precedent for a white-box single-TU test (rtc3test oracle).
- `src/accept/input_script.c` and `sha256.c`: scripted input and digests for rtc3test.
- `cmake/ScanForbiddenFixtures.cmake`: install-exclusion scan. It follows links; give it a label parameter.
- `tests/player/test_continuation.c`: fresh-process `--child` pattern.
- `src/player/session.c`/`.h`: v1 envelope, atomic write, `PLAYER_SESSION_TEST_FAULT_*` hooks, and `battery_unsupported` (to remove).
- `tests/fuzz_core.c`, `tests/test_fuzz_core.c`, `tests/scripts/run-bounded-fuzz.sh`: fuzz harness and literal greps.
- `tests/consumers/{c,cpp}`: installed consumers.
- `fixtures/mbc1-continuation/`: original fixture layout. `fixtures/mooneye-mbc/`: sibling third-party fixture layout.

### Established Patterns
- Enum plus `switch` dispatch, plain-integer sub-structs, and no vtables or function pointers in the instance.
- Append-only public enum and API; `const` exports never mutate.
- Exact-inventory gate on `tests/expected-tests.txt` and `tests/player/expected-tests.txt`.
- Third-party fixtures need a manifest, license, sources, eligibility, a digest CTest, a `fixture-repro` leg, and install exclusion.
- Evidence classes are labelled: hardware-derived, differential, metamorphic, regression, DEC.

### Integration Points
- Core: the cartridge section of `gabbaboy.c`, `include/gabbaboy/gabbaboy.h`.
- Player: `src/player/session.c`, `main.c` (clock flag), `limitations.h`.
- CI: `.github/workflows/ci.yml` (no-host-clock CTest runs everywhere), `.github/workflows/fixture-repro.yml` (rtc3test, MagenTests and continuation fixture rebuilds).

</code_context>

<specifics>
## Specific Ideas

- Pin rtc3test's exact numeric transcript, not only PASS/FAIL. The ROM's ±1 ms tolerance cannot see a 0.1% rate error.
- Every new third-party screen oracle needs a paired negative control, because blank early frames make a pass vacuous.
- Delta-based continuation assertions (`result(N) - result(0)`) cancel emulated time and remove flake.

</specifics>

<deferred>
## Deferred Ideas

- BGB/VBA-M 44/48-byte footer import/export host adapter (D-026). The D-16 block keeps it expressible.
- Mealybug `mbc3_rtc` as required evidence, once G1 (mgblib font) clears.
- gbclock RTC game, once G3 plugin licences are checked.
- CGB double-speed RTC independence assertion (Phase 11).
- Recovering paused-while-open time in the player (documented limitation; no second mode now).
- `gbb_probe_rom` / cartridge info with a `has_rtc` flag (CGB phases or SHIP-10).
- Mooneye MBC1 backfill; splitting the cartridge section into `src/core/cartridge.c`; a generalised suite verifier. All carried from Phase 8.
- Runner `frame-digest` receipts for rtc3test (option b), only if runner receipts are wanted later.

</deferred>

---

*Phase: 09-mbc3-deterministic-rtc-and-cartridge-persistence*
*Context gathered: 2026-10-11*
