# Cartridge and battery save contract

GabbaBoy's cartridge and save behavior is scoped to its bootless DMG-CPU-B
software profile. The rules here describe the implementation and its tests;
they do not qualify a physical Game Boy, every MBC1/MBC2/MBC3/MBC5 board
revision, or every ROM that declares one of the supported types.

The CGB profile, ROM probe/info fields and RGB555 buffer contract are described
in the [native integration guide](native-integration.md). Timer cartridges
retain the same 21-byte `GBB_RTC_BLOCK_SIZE` clock block; the core never reads
the host clock, and the host decides when to pass elapsed seconds to
`gbb_rtc_catch_up`.

## Supported cartridge matrix

The loader accepts exact ROM lengths and validates the header checksum before
replacing an instance's active cartridge. It supports:

| Header type | Cartridge behavior | ROM size codes | RAM size codes |
|---|---|---|---|
| `$00` | ROM-only | `$00` (32 KiB) | `$00` (none) |
| `$01` | Standard MBC1, no RAM | `$00`–`$06` (32 KiB–2 MiB) | `$00` (none) |
| `$02` | Standard MBC1 with volatile RAM | `$00`–`$06` | `$02` (8 KiB), or `$03` (32 KiB) only through 512 KiB ROM |
| `$03` | Standard MBC1 with battery-backed RAM | `$00`–`$06` | `$02` (8 KiB), or `$03` (32 KiB) only through 512 KiB ROM |
| `$05` | MBC2 with 512 built-in 4-bit cells, volatile | `$00`–`$03` (32–256 KiB) | `$00` only; the 512 cells come from the type, not the header |
| `$06` | MBC2 with 512 built-in cells, battery-backed | `$00`–`$03` | `$00` only |
| `$0F` | MBC3 with timer and battery, no RAM | `$00`–`$06` (32 KiB–2 MiB) | `$00` (none) |
| `$10` | MBC3 with timer, RAM and battery | `$00`–`$06` | `$02` (8 KiB) or `$03` (32 KiB) |
| `$11` | MBC3, no RAM, no timer | `$00`–`$06` | `$00` (none) |
| `$12` | MBC3 with volatile RAM, no timer | `$00`–`$06` | `$02` or `$03` |
| `$13` | MBC3 with battery-backed RAM, no timer | `$00`–`$06` | `$02` or `$03` |
| `$19` | MBC5, no RAM | `$00`–`$08` (32 KiB–8 MiB) | `$00` (none) |
| `$1A` | MBC5 with volatile RAM | `$00`–`$08` | `$02` (8 KiB), `$03` (32 KiB), `$05` (64 KiB) or `$04` (128 KiB) |
| `$1B` | MBC5 with battery-backed RAM | `$00`–`$08` | as `$1A` |
| `$1C` | MBC5 with rumble, no RAM | `$00`–`$08` | `$00` (none) |
| `$1D` | MBC5 with rumble and volatile RAM | `$00`–`$08` | as `$1A` |
| `$1E` | MBC5 with rumble and battery-backed RAM | `$00`–`$08` | as `$1A` |

For MBC1 images larger than 512 KiB, the implementation accepts only 8 KiB
RAM. It rejects contradictory type/RAM declarations, other mapper types,
unsupported size codes, truncated images, and images whose actual length
differs from the declared ROM size. Recognized MBC1M candidates return
`GBB_UNSUPPORTED_CARTRIDGE_VARIANT`; the conservative alternate-bank
logo/header check does not identify every special-wiring image. MBC1M is
outside the support claim.

MBC3 types `$0F`–`$13` have a 4 MiB length ceiling, and ROM size codes `$07`
and above are not MBC3 sizes the core supports. The larger MBC30 variant
is **not supported**: after the length, size-code and header-checksum checks, a
header is a MBC30 candidate if its ROM code is `$07` (4 MiB, at exactly 4 MiB)
or its RAM code is `$05` (64 KiB) on a RAM-bearing type (`$10`, `$12`, `$13`),
and the loader returns `GBB_UNSUPPORTED_CARTRIDGE_VARIANT`, the same result as
a recognized MBC1M candidate. Other MBC3 size mistakes keep their size-class
error: RAM `$01`/`$04` on any MBC3 type, RAM `$05` on `$0F`/`$11` and RAM `$00`
on a RAM-bearing type are `GBB_UNSUPPORTED_RAM_SIZE`, ROM code `$08` and above is
`GBB_UNSUPPORTED_ROM_SIZE`, and a length above 4 MiB is `GBB_ROM_TOO_LARGE`.

The ROM length ceiling is type-aware. Images of MBC5 types `$19`–`$1E` may be up
to 8 MiB; MBC3 images are bounded by the 4 MiB ceiling
above; every other type, including a type byte the loader does not recognize,
keeps the earlier 2 MiB ceiling and the same
`GBB_ROM_TOO_LARGE` result as before this change. A length above 8 MiB is always `GBB_ROM_TOO_LARGE`, and size codes
above a type's maximum return `GBB_UNSUPPORTED_ROM_SIZE`. After validation the
core allocates at most 8 MiB of ROM plus 128 KiB of cartridge RAM. The header's
CGB flag at `$143` is ignored; an MBC5 image with `$143 = $C0` loads on the
DMG-CPU-B profile, which does not change.

MBC5 keeps the ROM bank as two independent registers: writes to
`$2000`–`$2FFF` set the low eight bits and writes to `$3000`–`$3FFF` set bit 8
from value bit 0 only, so write order does not matter and neither write clears
the other register. The bank is the nine-bit value masked by the ROM's bank
count. Bank 0 is selectable in the `$4000`–`$7FFF` window (there is no 0-to-1
remap), while `$0000`–`$3FFF` always reads bank 0. The RAM gate opens when the
low nibble written to `$0000`–`$1FFF` is `$A`. `$4000`–`$5FFF` selects the RAM
bank with four bits on `$19`–`$1B` and three bits on rumble types `$1C`–`$1E`,
masked by the loaded bank count; writes to `$6000`–`$7FFF` are ignored. Every
MBC5 type maps `$A000`–`$BFFF`, so disabled or absent RAM reads `$FF` and
writes are ignored.

MBC3 decodes writes as follows. A write to `$0000`–`$1FFF` opens the RAM and
clock gate when the low nibble is `$A` (so `$AA` opens it), and any other value
closes it; while closed, reads return `$FF` and writes are ignored, clock
registers included. Writes to `$2000`–`$3FFF` select the ROM bank from the low
seven bits, a zero selection becomes bank one, and the result is masked by the
ROM's bank count. Writes to `$4000`–`$5FFF` select by the whole byte: `$00`–`$03`
selects a RAM bank (an 8 KiB cart aliases banks 1–3 onto bank 0), `$08`–`$0C`
selects a clock register (S, M, H, DL, DH) on timer types `$0F` and `$10`, and
every other value (`$04`–`$07`, `$0D`–`$FF`, and `$08`–`$0C` on types without a
timer) maps nothing: reads return `$FF` and writes are ignored. That choice of
unmapped selections is a software-model decision, not a hardware finding. A
reset sets ROM bank 1, RAM bank 0 and a closed gate and leaves RAM alone.

MBC2 decodes writes to `$0000`–`$3FFF` by address bit 8. With bit 8 clear the
write is the RAM gate (low nibble `$A` opens it); with bit 8 set the low four
bits select the ROM bank, a zero selection becomes bank one, and the result is
then masked by the ROM's bank count. Writes to `$4000`–`$7FFF` do nothing. The
512 cells are stored as `$F0 | nibble` and echoed across the whole
`$A000`–`$BFFF` window by the low nine address bits, so an enabled read of a
cell written with `$A5` returns `$F5` (the upper nibble reads as 1s, matching a
genuine MBC2A in the author-attested Mooneye `ram` test). Disabled reads return
`$FF` and disabled writes are ignored.

The standard MBC1 model has two banking modes. It keeps the low and upper ROM
bank registers separate, translates a zero low-bank selection to bank one
before applying the ROM-size mask, and uses the upper register for the lower
ROM window in mode 1. Mode 1 also selects a RAM bank when the cartridge has
multiple RAM banks. The RAM gate opens when the low nibble written in the
control range is `$A`; disabled or absent RAM reads return `$FF` and writes
are ignored as deterministic software policy where hardware references leave
the value undefined.

## MBC3 real-time clock

Timer types `$0F` and `$10` carry a clock with seconds, minutes, hours and a
nine-bit day counter. It advances only from emulated time, at exactly 2^23
half-dots per second; the core never reads the host clock, and a CI check
(`no_host_clock`) scans the core sources and object file for host-clock calls.
Wall-clock time reaches the clock only through `gbb_rtc_catch_up`.

- **Registers.** Reads and writes go through `$A000`–`$BFFF` after selecting
  `$08`–`$0C` (S, M, H, DL, DH) with the gate open. S and M keep 6 bits, H 5
  bits, DL 8 bits, and DH only bit 0 (day bit 8), bit 6 (halt) and bit 7
  (carry); unused bits read 0. Out-of-range values (seconds or minutes 60–63,
  hours 24–31) are stored as written. A field carries only when it steps from
  exactly 59, 59 or 23; otherwise it wraps within its mask with no carry.
- **Prescaler.** A seconds write restarts the sub-second count. Writes to M, H,
  DL, DH and halt toggles keep it.
- **Day counter.** It wraps from 511 to 0 and sets the carry, which stays set
  until a guest writes DH with bit 7 clear.
- **Halt.** A halted clock credits no time.
- **Latch.** Writes to `$6000`–`$7FFF` copy the live registers into the
  readable latched copy only when the previous write was exactly `$00` and this
  one is exactly `$01`. Reads of the clock registers return the latched copy.
  The `$00`-then-`$01` sequence follows the cartridge documentation; the edge
  cases around it (any other value, repeated writes, a fresh load or reset
  starting unprimed) are project decisions, because emulators disagree.
- **Battery generation.** A guest write that changes stored clock state
  (including a same-value seconds write when the sub-second count is non-zero)
  advances the generation; elapsed time, a carry set by ticking and the latch do
  not.
- **Reset and load.** A successful `gbb_load_rom` starts a fresh clock
  (00:00:00, day 0, running). `gbb_reset` keeps the live and latched clock,
  halt, carry and sub-second count, as it keeps RAM, and re-anchors them to the
  restarted emulated time.

RTC-capable cartridges are evidence-limited: the model is checked against the
author-attested rtc3test v004 and MagenTests ROMs plus original tests; see
[mbc3-rtc-evidence.md](mbc3-rtc-evidence.md). No physical clock is claimed.

New cartridge RAM starts filled with `$FF` as emulator policy, not a hardware
power-on claim. Volatile type `$02` RAM lasts for the loaded session and is
not battery-exportable. Type `$03` RAM is eligible for the battery API. A
soft reset preserves the loaded cartridge RAM and its generation counter;
successful ROM replacement starts a fresh `$FF` RAM image. Failed ROM
replacement leaves the current machine state intact.

## Core battery API

The opaque `gbb_instance` owns its cartridge RAM. Query `gbb_battery_size`,
then transfer bytes with `gbb_copy_battery` or `gbb_import_battery` using
caller-owned buffers. The core has no filesystem or save-format dependency,
returns no mutable pointer into its state, and each instance may be called by
one thread at a time.

Battery APIs work only for a loaded battery-backed cartridge: MBC1 type `$03`,
MBC2 type `$06`, MBC3 types `$0F`, `$10` and `$13`, or MBC5 types `$1B` and
`$1E`. They return
`GBB_INVALID_ARGUMENT` for invalid pointers, `GBB_NO_BATTERY` when the loaded
cartridge has no battery-backed RAM, `GBB_BUFFER_TOO_SMALL` when the copy
destination cannot hold all RAM, and `GBB_BATTERY_SIZE_MISMATCH` unless an
import is exactly the cartridge's RAM size. A rejected operation leaves output
and live RAM unchanged. An import is checked completely before any mutation;
it advances the generation once only if at least one byte changes. Guest RAM
writes advance the generation when a byte's value actually changes. The counter
saturates at `UINT64_MAX`. Successful ROM replacement resets it to zero, and
reset preserves it. The caller owns each buffer; serialize calls to an
individual instance. Different instances share no mutable state.

For MBC1, MBC3 type `$13` and MBC5 the API transfers the cartridge RAM bytes
unchanged. For
MBC2 the image is exactly 512 bytes in the core's canonical form, every byte
`$F0 | nibble`; export is a plain copy of the live cells. Import requires
exactly 512 bytes (otherwise `GBB_BATTERY_SIZE_MISMATCH`) and then normalises
each byte to `$F0 | (b & $0F)`, so a file from another emulator with arbitrary
upper nibbles is accepted and canonicalised. The normalised image is compared
with live RAM before anything is written; the generation advances once only if
it differs, and a rejected import changes nothing. Packed 256-byte MBC2 saves
(two nibbles per byte) are not supported. A guest write advances the generation
only when the canonical byte changes, so writing `$A5` over a `$F5` cell does
not.

### Timer cartridge battery image and the clock block

For the timer types `$0F` and `$10` the battery image is the cartridge RAM
followed by a clock block of `GBB_RTC_BLOCK_SIZE` (21) bytes. Type `$0F` has no
RAM, so its image is the block alone (`gbb_battery_size` returns 21); type `$10`
is 8 KiB or 32 KiB of RAM plus 21 bytes. Every other battery type keeps the
RAM-sized image described above, so MBC1 images are unchanged. The block is
written field by field, little-endian:

| Offset | Size | Field | Valid on import |
|---|---|---|---|
| 0 | 4 | magic `GBRT` | exact |
| 4 | 1 | version | `1` |
| 5 | 4 | sub-second count (half-dots) | below 2^23 |
| 9–13 | 5 | live S, M, H, DL, DH | S, M ≤ `$3F`; H ≤ `$1F`; DL any; `(DH & $3E) == 0` |
| 14–18 | 5 | latched S, M, H, DL, DH | same masks |
| 19 | 1 | last write to `$6000`–`$7FFF` (latch edge state) | any |
| 20 | 1 | reserved | `0` |

Export projects the clock to the instance's current emulated time on a local
copy, so the instance is not changed and two exports at the same emulated time
are byte-identical. Import checks the whole image (length, then magic, version,
every range and the reserved byte) before changing anything and then commits RAM
and clock together:

| Condition | Result |
|---|---|
| Image length is not exactly RAM size plus 21 | `GBB_BATTERY_SIZE_MISMATCH` |
| Bad magic, unknown version, sub-second count at or above 2^23, a field above its mask, DH bits `$3E` set, or a non-zero reserved byte | `GBB_INVALID_ARGUMENT` |
| Loaded cartridge has no battery image | `GBB_NO_BATTERY` |

A rejected import leaves RAM, the clock and the generation unchanged. Out-of-range
values that guests can produce (seconds 63, hours 31) are accepted. A version
change implies a size change, so an older core fails on size.

**Import never catches up.** Importing restores the saved clock exactly as of
the instant of the import and never advances it, so a host that wants the
wall-clock time since the save to count must apply it deliberately:

```c
gbb_error gbb_rtc_catch_up(gbb_instance *instance, int64_t elapsed_seconds);
```

`gbb_rtc_catch_up` adds whole seconds to the live clock. A NULL instance or a
negative value returns `GBB_INVALID_ARGUMENT` and changes nothing (the host
decides what a clock rollback means); no ROM or a cartridge without a timer
returns `GBB_NO_RTC`; zero is a no-op; a halted clock returns `GBB_OK` and does
not change. Otherwise the addition is exact, modular and O(1) with no
saturation: the day counter wraps at 512 and sets the sticky carry, and
`catch_up(a)` then `catch_up(b)` equals `catch_up(a + b)`. The latched
registers, the sub-second count and emulated time are unchanged, and the battery
generation advances once if the live clock changed. Call it between `gbb_run*`
calls, once per open (two calls add twice), and record the value as an input
event if you keep replay logs. The signed prototype is new in Phase 9 and
reviewable before the phase pull request merges.

**BGB and VBA-M footers.** Those emulators append a 44- or 48-byte clock footer
to a save. The core neither reads nor writes it, but the block carries every
footer field, so a host adapter can convert in both directions; when building a
block from a footer, set the sub-second count to 0, the latch edge state to
`$FF` (unprimed) and the reserved byte to 0. No such adapter exists in this
repository and no interchange with those emulators is tested.

The API does not define an on-disk format and does not import arbitrary emulator
`.sav` files beyond the MBC2 normalisation above.
The host chooses and bounds the file, checks that its length exactly matches
`gbb_battery_size`, and decides how to preserve and atomically replace prior
data. The runnable installed C example in
[native-integration.md](native-integration.md) demonstrates raw transfer and
a temporary-file replacement; it is not the SDL player's checksummed envelope
or a general-purpose save manager.

## Native machine states

`gbb_state_size`, `gbb_save_state` and `gbb_load_state` transfer a complete
versioned machine state through caller-owned buffers. This includes the
machine's cartridge RAM and RTC state and is separate from the battery API's
raw RAM/clock image. Query the exact size, provide a stable buffer of at least
that capacity to save, and provide exactly that many bytes to load. A short
save destination returns `GBB_BUFFER_TOO_SMALL` without writing; a rejected
load validates the whole input before mutation. State bytes are tied to the
loaded ROM SHA-256, profile, execution mode and release version. The ordered
64-byte header, body contract, semantic limits and CRC are specified in
[`state-format.md`](state-format.md).

Loading a state restores the RTC's raw live and latched registers, latch-edge
state, subsecond phase and emulated-time anchor exactly. It reads no host clock
and does not call `gbb_rtc_catch_up`. A host opening a save should load the ROM,
optionally import a battery image and apply its chosen clock catch-up, then load
the state; the state replaces the machine RAM and RTC values. This leaves the
battery image format unchanged. Battery-generation and rumble-change counters
remain local to the receiving instance: a load increments battery generation
once only if the projected RAM-plus-RTC battery bytes change, and increments
rumble changes once only if the motor line changes. Both counters saturate at
`UINT64_MAX`; repeated identical loads add no observer changes.

Null arguments return `GBB_INVALID_ARGUMENT`. After pointer validation,
`gbb_state_size` and `gbb_save_state` return `GBB_STATE_NO_ROM` if no ROM is
loaded. Load validation reports short/bad magic as `GBB_STATE_BAD_FORMAT`, an
unsupported format/header/release/behavior version as
`GBB_STATE_UNSUPPORTED_VERSION`, then checks ROM presence, machine identity,
exact size, CRC and content in order (`GBB_STATE_NO_ROM`,
`GBB_STATE_IDENTITY_MISMATCH`, `GBB_STATE_SIZE_MISMATCH`,
`GBB_STATE_CORRUPT`, `GBB_STATE_INVALID_CONTENT`). Size and save outputs stay
untouched on failure. Calls on one instance must be externally serialized;
buffers must remain valid during the call and must not overlap the instance.
The API has no filesystem access, does not allocate or hash per call, and does
not synchronize threads for the caller.

## Rumble line query

MBC5 rumble types `$1C`–`$1E` expose the motor line through
`gbb_rumble_state(instance, &on, &changes)`. `on` is bit 3 of the last
`$4000`–`$5FFF` write, independent of the RAM gate; `changes` counts line
transitions and saturates at `UINT64_MAX`. A reset turns the line off, counting
one change only if it was on; a successful ROM load zeroes both. The call
returns `GBB_INVALID_ARGUMENT` for a NULL argument and `GBB_NO_RUMBLE` when no
ROM is loaded or the type has no rumble line, leaving outputs unchanged on any
error. A host should sample once per frame; the counter conveys duty-cycle
intensity without timestamps. The player and the headless runner do not drive
any haptics, and the query is not evidence of physical rumble-motor behavior.

## Player save identity and version 1 format

The macOS player stores saves under the per-user application directory returned
by `SDL_GetPrefPath("GabbaBoy", "GabbaBoy")`, not beside the ROM. Its filename
contains the lowercase SHA-256 of the exact ROM bytes plus the cartridge type
and RAM size: MBC1 type `$03` saves end in `-mbc1-<type>-<ram size>.gbb`, and every
other battery type uses `-cart-<type>-<ram size>.gbb`, so a v1 file and a v2 file
never share a name. Identical ROM bytes therefore use the same save identity when
moved or renamed; a byte-different ROM gets a different identity even if its
filename and cartridge header match. SHA-256 here is an identity key, not an
authentication mechanism.

The player-managed file is a field-by-field, little-endian version 1 envelope.
It has a 51-byte header followed by exactly 8 KiB or 32 KiB of raw battery RAM.
Only MBC1 type `$03` writes this version, and the bytes are exactly what the
v0.1 player wrote (a v0.1.2-written corpus is tested to load and to re-encode
byte-identically), so an older player still reads them:

| Byte offsets | Field | Encoding |
|---|---|---|
| `0..7` | Magic | ASCII `GBBBSAVE` |
| `8..9` | Version | Unsigned 16-bit little-endian, currently `1` |
| `10..41` | ROM identity | SHA-256 of the exact ROM bytes |
| `42` | Cartridge type | One byte, currently `$03` for battery saves |
| `43..46` | RAM length | Unsigned 32-bit little-endian, `8192` or `32768` |
| `47..50` | Payload checksum | IEEE CRC-32 of the RAM bytes, unsigned 32-bit little-endian |
| `51..end` | RAM payload | Exactly the declared RAM length |

The accepted file sizes are exactly 8,243 bytes for 8 KiB RAM or 32,819 bytes
for 32 KiB RAM. The CRC detects accidental corruption; it is not a MAC and
does not protect against deliberate modification. Truncation, trailing bytes,
unsupported versions, a different ROM digest, cartridge type, RAM length, or a
bad CRC reject the envelope. The player does not auto-detect raw `.sav` files.
Any future envelope change must migrate existing progress or retain access to
the older file.

## Player battery persistence and the version 2 envelope

The player saves MBC1 `$03`, MBC2 `$06`, MBC3 `$0F`, `$10` and `$13` and MBC5
`$1B` and `$1E` battery cartridges. It reads battery status, RAM length and
whether a clock is present from the core after `gbb_load_rom`, not from the
header byte; the header type only names the file and its identity. The player
reads ROM files up to 8 MiB (the core's bound) and handles up to 131072 bytes of
RAM; larger inputs are refused. MBC1 `$03` with 8 or 32 KiB RAM keeps writing
version 1. Every other battery type writes version 2, and a version 2 file is
never rewritten as version 1. Readers accept version 1 only for `$03` and
version 2 for every supported battery type.

The version 2 envelope is a 64-byte little-endian header followed by the
battery RAM and then the clock block (the payload is exactly the core's battery
image):

| Byte offsets | Field | Encoding |
|---|---|---|
| `0..7` | Magic | ASCII `GBBBSAVE` |
| `8..9` | Version | Unsigned 16-bit, `2` |
| `10..41` | ROM identity | SHA-256 of the exact ROM bytes |
| `42` | Cartridge type | One byte |
| `43` | Flags | Bit 0: clock block present. Bit 1: `saved_at` valid (only with bit 0). Other bits 0 |
| `44..47` | RAM length | `0`, `512`, `8192`, `32768`, `65536` or `131072`, equal to the RAM part of the core's image |
| `48..51` | Clock length | `0` or exactly 21 |
| `52..59` | `saved_at` | Signed 64-bit Unix UTC seconds; 0 unless bit 1 is set |
| `60..63` | Checksum | IEEE CRC-32 of header bytes 0–59 followed by the payload |
| `64..end` | Payload | RAM, then the clock block |

The file must be exactly 64 + RAM length + clock length bytes (at most 131,157).
Unlike version 1, the CRC covers the header, so a flipped `saved_at` cannot
inject a catch-up; it still detects accidents only, **is not authentication**,
and does not stop deliberate modification. Truncation, trailing bytes, an
unknown version, reserved flag bits, a non-canonical zero field, a different ROM
digest or type, lengths that differ from what the core reports for the loaded
cartridge, or a bad CRC reject the envelope through the recovery path described
below, with no change to the running game. Every timer cartridge save records
the time of the save in `saved_at` together with a clock block taken at the same
instant; cartridges without a clock record no time. If the system clock is
unavailable when a timer cartridge is saved, the save carries no stamp.

### Reopen policy for timer cartridges

After the battery image is loaded and before the first guest instruction, the
player applies the clock catch-up at most once per open, and reports the result
in the status line (no dialog). The decision is the pure function tested by
`catch_up_policy_table`:

| Condition | Action | Status line |
|---|---|---|
| No clock, no save file, or a rejected save | none | none, or the existing rejected-save warning |
| The save has no time stamp | none | "Game clock not advanced: the save has no time stamp." |
| The system clock is unavailable | none | "Game clock not advanced: the system clock is unavailable." |
| The system clock is earlier than `saved_at` | none; the next save stamps the current time | "Game clock not advanced: the system clock is earlier than the save." |
| The system clock equals `saved_at` | none | none |
| The system clock is later | `gbb_rtc_catch_up(min(difference, INT64_MAX))` | "Game clock advanced by 1d 2h 3m 4s", plus " (day counter overflowed)" if the carry became set |
| The game clock is halted | the core ignores the delta | "Game clock is halted; not advanced." |

After a catch-up changes the clock, the generation change marks the save dirty,
so the next save stamps it afresh. A clock moved backwards never rewinds the
game clock (this matches BGB and VBA-M; other emulators reset or rewind it).

**Limitation: time spent paused while the player stays open is not recovered.**
Only the time between a save and its reopen is added; a paused session, a
sleeping laptop with the player left open, or a changed system clock during a
session is not caught up.

The player's `--clock-unix <seconds>` option exists only for the
`--battery-smoke-store` and `--battery-smoke-resume` test modes, to inject a
clock into fresh-process tests. Any other use is refused with a usage error.
The player's own on-screen status line has no pixel-level UI test; the status
text is checked through the continuation tests.

## Host raw saves and player state slots

Two surfaces keep saves outside the player's `.gbb` envelope, and they are different things.

**Host raw saves.** `gabbaboy-runner --save-dir DIR` (see the [host process
contract](native-integration.md#host-process-contract)) reads and writes
`{saveDir}/{stem}.sav`: the exact battery bytes of the core's battery API with no
envelope and no checksum. The size is fixed by the cartridge, and a timer
cartridge's file ends in the 21-byte clock block. The player's `.gbb` files
under its per-user directory are a separate format with a header, an identity
and a checksum, and the player never reads or writes a host `.sav`.

**Player state slots.** The macOS player keeps nine numbered machine-state
slots per game and model. Keys `1` to `9` select a slot (selecting changes nothing and
shows whether the slot is empty or saved), `⌘S` saves the selected slot, `⌘L` loads it and `⌘Z`
undoes the last load; a held key does not repeat the action. A slot holds the
core's native machine state (see [Native machine states](#native-machine-states)),
so it is tied to the exact ROM bytes, the profile and the GabbaBoy release that
saved it. A release-bound slot from any other release, a slot from a different
game or model, and a damaged slot are refused with a message and change
nothing. Slot files live beside the player's saves in the per-user directory,
named from the ROM digest, the model and the slot digit alone.

Loading a slot also replaces the game's battery save: the state includes the
machine's cartridge RAM and clock, and the player's autosave then writes that
RAM as the battery save like any other change. Before the first load, and
whenever the battery has changed since the previous load, the player writes the
in-game battery to a battery-preload backup file, so loading slot A and then slot
B still keeps the save you had before A. The player remembers the battery each
load left behind in a small guard file beside the slots, so the next session's
first load does not mistake it for an in-game save and overwrite that backup. Each load also writes the state it
replaced to an undo file; `⌘Z` swaps the live state with it, so pressing it twice
returns to where you started. If either backup cannot be
written the load is not applied and the live game is unchanged. Loading a slot
restores the saved clock exactly and never catches it up to the host clock.

## Save timing, replacement, and failure behavior

The player saves only when battery RAM has changed. It coalesces writes until
the RAM has been quiet for 2 seconds, with a 10-second maximum dirty age; both
limits use host monotonic time, not guest emulated time. It also attempts a
final save before orderly quit, ROM replacement, and soft reset. A successful
save status distinguishes bytes on disk from progress still held only in
memory. Press `S` to save now or retry a failed save.

Each replacement is written to a unique temporary file in the save directory,
with owner-only permissions. The player writes the complete bounded envelope,
syncs the file, renames it over a regular-file target atomically, and syncs the
containing directory where supported. It never truncates the active target in
place. A failure before rename leaves the prior complete target in place and
keeps dirty progress in memory for retry. If directory sync fails after rename,
the new complete file may already be visible while the player reports failure;
retry is safe. Atomic replacement prevents readers from observing a partially
written target, but these software tests do not establish power-loss durability
for every filesystem.

If a final save blocks quit, replacement, or reset, the transition waits for a
choice: press `R` to retry, `C` to continue without saving, or `Escape` to
cancel the transition and keep the current session active. A failed save never
silently authorizes the transition. Continuing unsaved may lose the newest
progress if the process exits; canceling preserves the active session so the
user can retry later.

## Recovery and concurrent sessions

The player reads only bounded regular files without following symlinks. A
malformed, wrong-version, checksum-failing, or identity-mismatched save is not
imported or silently overwritten. When the existing file is safely readable
and can be preserved, the player renames it to a unique `.recovery-...` file
beside the active save, starts with fresh `$FF` RAM, and shows a warning. It
does not automatically load recovery files. Keep a copy before investigating
one; the player has no save-management or recovery UI. If a file is unsafe to
read or cannot be preserved, the original is left in place and persistence is
disabled for that session.

For each battery-backed session, the player holds a nonblocking exclusive
advisory lock on a sibling `.lock` file. A second GabbaBoy process that uses
the same save is refused as a writable session rather than using last-writer-
wins behavior. Advisory locks coordinate cooperating GabbaBoy processes only;
external editors, other emulators, network filesystems, or tools that ignore
the lock can still race with the player. Close all GabbaBoy sessions before
manually handling a save or recovery file.

## Evidence limits

The mapper model is checked against cartridge documentation and emulator
source, while the required regressions use synthetic banked ROMs, a
project-authored continuation ROM, an original MBC5 banking guest, and the
digest-pinned Mooneye emulator-only mbc2/mbc5 derivatives (author-attested
hardware results, executed here on the bootless profile). The original fixture is MIT-licensed and
its source and 32 KiB ROM digests are recorded in
[`fixtures/mbc1-continuation/manifest.json`](../fixtures/mbc1-continuation/manifest.json).
These results establish software behavior under the named bootless profile.
No physical DMG-CPU-B/MBC1/MBC2/MBC3/MBC5, real-time-clock or CGB/double-speed
observation, boot-ROM execution, MBC30, MBC1M, other mapper, physical rumble,
general game-compatibility, or arbitrary
save-interchange claim is made. The MBC3 clock is evidenced by author-attested
test-ROM results, original tests and project decisions; see
[`docs/mbc3-rtc-evidence.md`](mbc3-rtc-evidence.md). Process-interruption tests exercise old-or-new complete file outcomes;
they do not simulate power loss.

Further evidence and named test coverage are in
[`docs/mbc1-evidence.md`](mbc1-evidence.md) and
[`docs/mbc2-mbc5-evidence.md`](mbc2-mbc5-evidence.md) and
[`docs/mbc3-rtc-evidence.md`](mbc3-rtc-evidence.md).
