# MBC3, deterministic RTC and cartridge persistence evidence

This ledger maps Phase 9's requirements (CART-04, CART-05, CART-06, RTC-01,
RTC-02 and RTC-03) to the implementation, registered test names, fixtures and
evidence class. It describes the bootless DMG-CPU-B software profile. Test-ROM
passes, software-model decisions and emulator comparisons recorded here are
**not physical-hardware evidence, not game-compatibility evidence, not CGB
support and not hardware qualification**. The user-facing contract is in
[cartridge-and-saves.md](cartridge-and-saves.md); the host integration notes
are in [native-integration.md](native-integration.md); the earlier ledgers are
[mbc1-evidence.md](mbc1-evidence.md) and
[mbc2-mbc5-evidence.md](mbc2-mbc5-evidence.md).

## Scope and model

- MBC3 header types `$0F`-`$13` (timer, timer with RAM, plain, RAM, RAM with
  battery) load through the cartridge seam with 7-bit ROM banking, RAM banks
  `0`-`3` and ROM sizes up to 2 MiB (a 4 MiB declaration is refused as the
  MBC30 variant).
- The MBC30 variant is **rejected** with `GBB_UNSUPPORTED_CARTRIDGE_VARIANT`,
  after the length, size-code and header-checksum checks. ROM code `$07`
  (4 MiB) exists in the MBC3 rows only to reach that variant slot, so that a
  4 MiB MBC30 candidate is recognised and refused rather than reported as an
  unsupported size (research Open Question 5). It is not a claim that 4 MiB
  MBC3 images are supported.
- The clock advances only from emulated time (2^23 half-dots per second). The
  core never reads the host clock; wall-clock time enters through the explicit
  `gbb_rtc_catch_up(instance, int64_t)` call, which the host applies once per
  open.
- Battery images of timer cartridges are the cartridge RAM followed by a
  21-byte versioned little-endian block (`GBB_RTC_BLOCK_SIZE`); `$0F` has no
  RAM, so its image is the block alone.
- The macOS player persists MBC1, MBC2, MBC3 and MBC5 battery cartridges in a
  checksummed envelope (version 2 for everything except MBC1 `$03`, which keeps
  the v0.1 version 1 file).

## Evidence classes

| Label | Meaning |
|---|---|
| **hardware-derived (author-attested)** | A third-party test ROM whose author states it was validated on physical hardware. Here it is executed on this project's software profile. This project made no physical observation. |
| **original differential / metamorphic / regression** | A test written for this project: a closed form checked against a naive model, an invariance property, or a pinned fixture. It is evidence about this software, not about a cartridge. |
| **DEC (project decision)** | A behavior the model chose where sources disagree or no source covers it. It is labelled as a decision in the source and is not hardware-qualified. |
| **R3 / PD** | Provenance tags used in the claim table: R3 is rtc3test v004 and its `tests.md`; PD is the Pan Docs cartridge-header and MBC3 description. |

## Claim table

Every name cited in the last column of these tables is a registered CTest
(checked by `mbc3_rtc_evidence_ledger_names`, with
`mbc3_rtc_evidence_ledger_selftest` as its negative control) in
[`tests/expected-tests.txt`](../tests/expected-tests.txt) or
[`tests/player/expected-tests.txt`](../tests/player/expected-tests.txt).
The decision labels (D-NN) are those in the phase context.

### Mapping, variants and header matrix (CART-04; D-01 to D-03)

| Claim | Evidence class | Tests |
|---|---|---|
| Types `$0F`-`$13` load; guest-visible ROM and RAM bytes follow the mapper (end-to-end tracer) | original regression (synthetic ROMs) | `mbc3_tracer` |
| Header matrix: accepted type, ROM-code and RAM-code combinations; a 2 MiB image loads, a 4 MiB image returns the variant error and 4 MiB + 1 is too large | original regression | `mbc3_header_matrix` |
| 7-bit ROM bank, zero translated to one before the bank-count mask | original regression; PD for the translation | `mbc3_rom_banking` |
| RAM banks `0`-`3`; banks alias on an 8 KiB cart | original regression; the aliasing is required by MagenTests | `mbc3_ram_banking` |
| RAM gate opens on `(v & $0F) == $0A` (so `$AA` enables); disabled reads `$FF`, writes ignored | PD; original regression | `mbc3_ram_gate` |
| Selections `$04`-`$07` and `$0D`-`$FF` map nothing (reads `$FF`, writes ignored) | **DEC**, not hardware-qualified (SameBoy aliases with `& 3` on non-timer MBC3 and mGBA decodes the low nibble) | `mbc3_unmapped_select` |
| Absent RAM (`$0F`, `$11`) reads `$FF`; `$0F` has a 21-byte image, `$11` has no battery | original regression | `mbc3_absent_ram` |
| Reset restores ROM bank 1, RAM bank 0 and a closed gate, keeps the RAM contents, and an identical rewrite afterwards does not advance the generation | original regression | `mbc3_reset` |
| Battery generation advances only on a changed byte | original regression | `mbc3_battery_generation` |

### MagenTests out-of-bounds SRAM (CART-04; D-04 to D-06)

| Claim | Evidence class | Tests |
|---|---|---|
| Three MagenTests ROMs (MIT, pinned commit) match their recorded SHA-256 | fixture provenance | `magentests_fixture_digest` |
| The MBC1, MBC3 and MBC5 ROMs paint shade 0 on all 23040 pixels after 16 frames | **hardware-derived (author-attested)**, screen oracle | `magentests_oob_sram_mbc1`, `magentests_oob_sram_mbc3`, `magentests_oob_sram_mbc5` |
| The oracle can fail: with `$149 = $03` and the header checksum recomputed, every ROM paints shade 3 | original negative control | `magentests_oob_sram_negative_control` |
| The ROMs are not in the install tree, including a renamed copy (caught by digest) | original regression | `magentests_not_installed`, `magentests_not_installed_selftest` |

The ROMs are screen-only and volatile-RAM only. They write CGB registers that
the DMG profile ignores.

### RTC model (RTC-01; D-07 to D-10)

| Claim | Evidence class | Tests |
|---|---|---|
| End-to-end: a guest sets 23:59:58 on day 511, waits about 2.5 s of VBlanks, latches and reads 00:00:00 day 0 with the carry set | original regression | `rtc_tracer` |
| RTC register access needs the RAM gate and a timer cartridge; fresh load starts at 00:00:00 day 0, running | original regression; DEC for the gate on `$0F` | `rtc_gate_and_select`, `rtc_load_fresh` |
| Exactly 2^23 half-dots per second | **hardware-derived (author-attested)** (R3, measured 1000.0 ms) plus original arithmetic | `rtc_rate_exact`, `rtc3test_basic`, `rtc3test_subsecond` |
| The closed-form second adder equals naive per-second stepping on 100000 seeded states (out-of-range fields included) and 2000 long-count states | original differential | `rtc_closed_form_differential` |
| add(a) then add(b) equals add(a + b), including sums above `INT64_MAX` | original metamorphic | `rtc_add_composes` |
| A seconds write restarts the sub-second prescaler; M, H, DL, DH writes and halt toggles keep it | R3 (RTCS/500, RTCS/900); original regression | `rtc_prescaler_rules` |
| Write and read masks (S, M `$3F`; H `$1F`; DL 8 bits; DH `$C1`) | R3; original regression | `rtc_write_masks` |
| Out-of-range S, M, H are stored as written and a field carries only from exactly 59, 59, 23 | R3 (`Invalid rollovers`, `High minutes`, `High hours`) | `rtc_out_of_range_rollover` |
| Day counter is 9 bits; the carry is sticky and clears only by a DH write with bit 7 clear | PD; R3; original regression | `rtc_day_carry_sticky` |
| A halted clock credits no time | R3 ("RTC off") | `rtc_halt_freezes` |
| Latch copies live to latched only for a `$00` write followed by `$01`; every write updates the edge state | PD for `00` then `01`; **DEC** for the edge cases (SameBoy latches on any write, mGBA on `01` unless already latched; rtc3test does not detect these) | `rtc_latch_edges` |
| Battery generation advances when a guest write changes stored state; elapsed ticks, tick-set carry and the latch never advance it | **DEC** (the latch not bumping the generation resolves a conflict in favor of a quiet-period save) | `rtc_generation_rules` |
| Emulated time near `UINT64_MAX` credits the exact second count, and a timestamp behind the clock's anchor credits nothing and does not wrap | original regression | `rtc_time_near_max` |
| `gbb_reset` rebases: live and latched clock, halt, carry and sub-second remainder are preserved | original regression | `rtc_reset_rebase` |
| Slicing `gbb_run` differently gives identical clock state; busy loop, HALT and STOP give identical clock state after equal half-dots | original metamorphic | `rtc_slice_invariance`, `rtc_cpu_independence` |

### rtc3test (RTC-01; D-11)

rtc3test v004 (Unlicense; SHA-256 `a271013fb37ea1d927b854798401320b220d57abb3ca77f3d318ceb8a9def30d`,
32768 bytes, type `$0F`) is screen-only and menu-driven. The oracle
(`tests/test_rtc3test.c`) replays three digest-pinned input scripts, stops at
the `* Return` marker tiles, decodes the 20x18 background map through the ROM's
own charmap and requires the marker, zero red cells, the exact green-cell
count and a byte-identical transcript.

| Suite | Marker frame | Green cells | Red cells | Test |
|---|---|---|---|---|
| Basic | 749 | 36 | 0 | `rtc3test_basic` |
| Range | 496 | 28 | 0 | `rtc3test_range` |
| Sub-second | 1561 | 57 | 0 | `rtc3test_subsecond` |

- Every displayed millisecond value equals the expectation parsed from the
  digest-checked upstream `tests.md` (Tick 1000 ms; RTCS/500 and RTCS/900
  1000 ms; RTCM/50 50 ms; RTCM/600 600 ms; RTCH/200 200 ms; RTCDL/800 800 ms;
  RTCDH/300 300 ms; RTC off/400 400 ms). The comparison is part of the test, so
  a ROM tolerance of one millisecond cannot hide a rate error. A mutated
  transcript (`1000.1ms`) failed `rtc3test_basic` when tried by hand in
  Plan 09-12.
- `rtc3test_fixture_digest` pins the ROM and `tests.md` digests;
  `rtc3test_negative_control` removes the scripted A tap and requires that the
  marker never appears within 60 emulated seconds while the menu is drawn.
- Budgets: each suite has a 60 emulated-second limit and `TIMEOUT 300`. Local
  wall times on the phase1 preset were 2.4 s (Basic), 1.5 s (Range) and 5.3 s
  (Sub-second).
- **Evidence class: hardware-derived (author-attested).** The ROM's author
  states it passes on hardware; GabbaBoy ran it on a software profile. Passing
  it is not a statement about any cartridge or game.

### Originals and mutation controls (RTC-01; D-12)

Five configure-time mutants of `src/core/gabbaboy.c` (each anchor must occur
exactly once or configure fails) are each killed by a named original test, and
an unrelated case still passes inside the same mutant.

| Mutant | Killed by (via the mutant test) | Paired control |
|---|---|---|
| seconds write does not restart the prescaler | `rtc_mutant_prescaler_kept` (`rtc_prescaler_rules`) | `rtc_mutant_prescaler_kept_control` |
| prescaler restarts on every write | `rtc_mutant_prescaler_reset_every_write` | `rtc_mutant_prescaler_reset_every_write_control` |
| prescaler restarts on a halt toggle | `rtc_mutant_prescaler_reset_on_halt` | `rtc_mutant_prescaler_reset_on_halt_control` |
| out-of-range fields are clamped | `rtc_mutant_out_of_range_clamped` (`rtc_out_of_range_rollover`) | `rtc_mutant_out_of_range_clamped_control` |
| latch on any write | `rtc_mutant_latch_any_write` (`rtc_latch_edges`) | `rtc_mutant_latch_any_write_control` |

Evidence class: original mutation control.

### No host clock (RTC-01; D-13)

`no_host_clock` scans the core sources (include allow-list, denied call
patterns) and the core object's undefined symbols. `no_host_clock_selftest`,
`no_host_clock_symbol_selftest` and `no_host_clock_comment_selftest` are the
negative controls (a scratch source with `#include <time.h>` and `time(NULL)`,
a denied symbol, and a `clock()` call after a `//` comment that mentions `/*`,
must fail). A missing symbol tool or an empty symbol listing fails the leg. Observed in the job logs of the
exact-head `ci` run 38180044966 (head `2b4c22004e801272ebc1cff12b85312debb444b9`):

| Leg | Line |
|---|---|
| native-linux-x64 | `no-host-clock pass files=2 symbols=8 tool=nm` |
| native-macos-arm64 | `no-host-clock pass files=2 symbols=11 tool=nm` |
| native-windows-x64 | `no-host-clock pass files=2 symbols=7 tool=nm` |
| linux-asan-ubsan | `no-host-clock pass files=2 symbols=42 tool=nm` |
| cmake-floor-3.25.3 | `no-host-clock pass files=2 symbols=8 tool=nm` |

The Windows leg uses MinGW, so the `dumpbin` fallback path is implemented but
was not exercised in CI. The behavioral complement is `rtc_slice_invariance`
and `rtc_cpu_independence`. Evidence class: original static check plus
exact-head CI.

### Battery image, block and catch-up (RTC-02, RTC-03; D-14 to D-17)

| Claim | Evidence class | Tests |
|---|---|---|
| Export, import into a fresh instance and re-export are byte-identical; two exports at one emulated time are identical | original regression | `rtc_block_roundtrip` |
| Import never advances the clock: after N half-dots, import then export returns the imported bytes | original regression | `rtc_import_never_advances` |
| Every rejection (wrong length, bad magic, unknown version, out-of-range field, masked bit, non-zero reserved byte) leaves RAM, clock and generation unchanged | original regression (before/after byte comparison) | `rtc_block_corruption_matrix` |
| The block survives `gbb_reset`. Re-importing an identical image never advances the generation, a latch does not advance it, and `gbb_rtc_catch_up` advances it exactly once | original regression | `rtc_block_reset_roundtrip`, `rtc_block_generation` |
| Image sizes by type: `$0F` is the block alone, `$10` is RAM plus the block, `$13` and MBC1/MBC2/MBC5 stay RAM-sized | original regression | `rtc_battery_size_types` |
| `gbb_rtc_catch_up`: exact modular addition, zero is a no-op, negative is `GBB_INVALID_ARGUMENT`, `INT64_MAX` is accepted, a halted clock is unchanged, the carry is sticky, calls compose, latched registers and emulated time are untouched, `GBB_NO_RTC` without a timer | original regression and metamorphic | `rtc_catch_up_basic`, `rtc_catch_up_zero`, `rtc_catch_up_negative`, `rtc_catch_up_int64_max`, `rtc_catch_up_halted`, `rtc_catch_up_carry_sticky`, `rtc_catch_up_composes`, `rtc_catch_up_preserves`, `rtc_catch_up_errors` |
| The installed C and C++ consumers create a `$10` ROM, catch up 3661 s (live S/M/H = 1/1/1), re-import byte-identically and see `GBB_NO_RTC` and `GBB_INVALID_ARGUMENT` | original integration against the installed header and library | `installed_consumer_c`, `installed_consumer_cpp` |

Reversibility note (D-17): `gbb_rtc_catch_up(gbb_instance *, int64_t)` is a new
public prototype. The signed delta is reviewable before the phase pull request
merges; after a release it would break installed consumers.

### Host catch-up policy and the player (RTC-03, CART-06; D-19 to D-23, D-26)

| Claim | Evidence class | Tests |
|---|---|---|
| The pure policy (signed comparison, clamp to `INT64_MAX`, status text) covers every reopen row including the `INT64_MIN` and `INT64_MAX` extremes. It runs on all three operating systems because it is registered in the core inventory (documented deviation from D-26, which listed it in the player inventory) | original table test | `catch_up_policy_table` |
| Envelope v2 at its maximum size (exactly, one under, one over) | original regression | `player_session_v2_max_size` |
| Envelope v2 rejects each malformed variant (17 mutations, structural ones with the CRC recomputed so the field check itself rejects) and preserves the file | original regression | `player_session_v2_reject_matrix` |
| Seven fault points leave the previous complete file intact and loadable | original fault injection | `player_session_v2_temp_create_failure`, `player_session_v2_short_write_failure`, `player_session_v2_file_sync_failure`, `player_session_v2_rename_failure`, `player_session_v2_directory_sync_failure`, `player_session_v2_interrupt_before_rename`, `player_session_v2_interrupt_after_rename` |
| A v1 file written by the released v0.1.2 player loads and re-encodes byte-identically; a v2 file is never rewritten as v1 | regression against a corpus generated by the v0.1.2 tag (`fixtures/save-envelope-v1`) | `player_session_v1_corpus_load`, `player_session_v1_mbc1_write_identical`, `player_session_v1_v2_stickiness` |
| The player takes battery status, RAM size and clock presence from the core, for all 256 type bytes by RAM codes `$00`-`$05` | original differential against the core | `player_session_classification_drift`, `loader_type_byte_sweep` |
| The player reads ROMs up to the core's 8 MiB bound | original regression | `player_session_rom_cap_8mib` |
| `--clock-unix` is accepted only by the battery smoke modes and refused elsewhere (12 negative cases plus a store/resume pair) | original regression | `player_session_clock_flag_scope` |
| MBC3 timer save, fresh process, reopen: `result(N) - result(0) == N` for N = 0, 1, 59, 3600, 86400 and a value crossing the 511-day carry (with "(day counter overflowed)" in the status) | original fresh-process regression with an injected clock | `player_continuation_mbc3_rtc_resume`, `player_continuation_mbc3_rtc_delta` |
| A host clock earlier than the save leaves the file bytes unchanged; a halted clock is not advanced; an unavailable clock and a missing stamp advance nothing | original regression | `player_continuation_mbc3_rtc_rollback`, `player_continuation_mbc3_rtc_halted`, `player_continuation_mbc3_rtc_no_clock` |
| A save from a different ROM is rejected and preserved, and the original ROM still resumes | original regression | `player_continuation_mbc3_wrong_rom` |
| MBC2 (512 nibbles) and MBC5 (128 KiB, banks 0 and 15) continue across fresh processes | original regression | `player_continuation_mbc2_resume`, `player_continuation_mbc5_resume` |

The reopen policy and the paused-time limitation are in
[cartridge-and-saves.md](cartridge-and-saves.md). Applying the catch-up delta
by one extra second fails `player_continuation_mbc3_rtc_resume`,
`player_continuation_mbc3_rtc_delta` and `player_continuation_mbc3_wrong_rom`
(mutation check recorded in Plan 09-16).

### Continuation fixtures and the v0.1 corpus (D-24, D-25)

| Fixture | Class | Tests |
|---|---|---|
| `fixtures/mbc3-rtc-continuation` (type `$10`, original MIT guest, RGBDS 1.0.1, ROM SHA-256 `2a6e1922...44a9`) | original fixture, byte-identical rebuild | `mbc3_rtc_continuation_fixture_digest` |
| `fixtures/mbc2-continuation` (type `$06`, ROM SHA-256 `314e05b4...50aa`) | original fixture | `mbc2_continuation_fixture_digest` |
| `fixtures/mbc5-continuation` (type `$1B`, 128 KiB RAM, ROM SHA-256 `34e80d0c...a667`) | original fixture | `mbc5_continuation_fixture_digest` |
| Core-level store, export, import, catch-up, resume for the three guests (halted and carry variants for the clock; a damaged image does not resume) | original regression | `continuation_guest_mbc3_rtc`, `continuation_guest_mbc3_rtc_halted`, `continuation_guest_mbc3_rtc_carry`, `continuation_guest_mbc2`, `continuation_guest_mbc5` |

The core carries no ROM identity, so it accepts a same-size image from a
different ROM; identity is enforced by the player envelope
(`player_continuation_mbc3_wrong_rom`). `fixtures/save-envelope-v1` holds the
8243-byte and 32819-byte envelopes written by the v0.1.2 tag; its checker is
`tests/scripts/generate-save-envelope-v1.sh --check`.

### Loader matrix and fuzz (CART-05; D-27, D-28)

| Claim | Evidence class | Tests |
|---|---|---|
| Every MBC2, MBC3 and MBC5 header combination agrees with an independent expected-result oracle typed from the written precedence (not by calling the core validator), with a bad-checksum twin of each case | original table test against an independent oracle | `loader_contradiction_mbc2` (1344 cases), `loader_contradiction_mbc3` (3360 cases), `loader_contradiction_mbc5` (4032 cases) |
| The MBC30 candidates (ROM `$07` at 4 MiB; RAM `$05` on `$10`/`$12`/`$13`) return the variant error after the checksum | original regression | `loader_mbc30_variant` |
| The accepted type set is exactly `$00 $01-$03 $05-$06 $0F-$13 $19-$1E` over all 256 type bytes | original regression | `loader_type_byte_sweep` |
| Checksum and degenerate-argument ordering | original regression | `loader_bad_checksum` |
| After every rejection a guard instance (MBC1 `$03` with an imported save and a WRAM canary) equals an untouched twin: no partial mutation | original regression | the matrix tests above |
| Headers synthesised at the 2, 4 and 8 MiB bounds, one past each, and `SIZE_MAX` give a bounded result set and leave the previous ROM intact | original fuzz seeds | `fuzz_core_regressions`, `loader_boundary_fuzz` |

The libFuzzer bounded run executes on the Linux sanitizer leg only; it was not
run on the local macOS host. The peak resident size of one deterministic fuzz
run was about 19.7 MB.

## Reproduction status of the third-party ROMs

- **MagenTests** (`fixtures/magentests`) and **rtc3test** (`fixtures/rtc3test`)
  are admitted by digest with their licences (MIT and Unlicense) and pinned
  upstream commits. A reproduction script for each rebuilds the ROM with the
  legacy toolchain (RGBDS 0.6.1 and 0.4.2) and compares bytes without
  overwriting the committed file. A local ubuntu:22.04 container printed
  `result=byte-identical` for each; that is **not** the hosted claim.
- The hosted `fixture-repro` jobs `magentests-repro` and `rtc3test-repro`
  each printed `result=byte-identical` in pull-request run 38189871131 at head
  `fb8972d9e30e6bdf5ff2038e4508ecd3ebfb8522`. The release bytes of the
  MagenTests ROMs and of rtc3test therefore equal the rebuild from the pinned
  sources and legacy toolchain at that head. This is a reproducibility claim,
  not a hardware or compatibility claim. The Phase 9 evidence head repeats the
  jobs; a later `result=differs` would withdraw the claim.
- The three original continuation guests are rebuilt byte-identically by their
  reproduce scripts (pinned RGBDS 1.0.1 archives) and by the hosted
  `fixture-repro` steps.

## Limits

- No physical MBC3, RTC crystal or cartridge observation by this project.
  rtc3test and MagenTests results are author-attested and were executed here
  on a software profile.
- CGB RTC independence from CPU speed is covered by the software-profile tests
  `cgb_speed_ppu_apu_rtc_unscaled` and `cgb_speed_mutant_m12_rtc_reads_speed`;
  this is not a physical CGB or RTC observation. The DMG profile ignores the
  CGB flag and registers.
- No BGB or VBA-M footer import or export. The block holds every footer field,
  so a host adapter can map them (see the interop note in
  [cartridge-and-saves.md](cartridge-and-saves.md)); the core does not.
- Mealybug mbc3_rtc and the gbclock test are excluded by rights gates G1
  and G3 and are not run.
- MBC30 is rejected. MBC3 ROM images larger than 2 MiB (size code `$06`) are not supported.
- The latch edge cases, unmapped selections `$04`-`$07` and `$0D`-`$FF`, the
  "latch does not bump the generation" rule and the `-cart-` save file name are
  project decisions, not hardware findings.
- Time spent paused while the player stays open is not recovered; only the
  time between a save and its reopen is.
- The CRC in the player envelope detects accidents and is not authentication.
- The player's on-screen status text for catch-up has no pixel-level UI test;
  the status string is produced by the pure policy and checked through the
  continuation tests' result files.
- The libFuzzer run and the AddressSanitizer/UndefinedBehaviorSanitizer preset
  run on Linux hosted CI, not on the local macOS host.
- None of this is a statement about any game's behavior.
