# Native C integration

The installed `GabbaBoy::core` target is a small C17 embedding boundary. The
core owns each opaque instance and a private copy of the loaded ROM; the host
owns the bytes it passes in and every output buffer. Calls on one instance must
be serialized. The core has no filesystem, wall-clock, SDL, or shared mutable
process state. The API and ABI may evolve; this preview makes no stable ABI
promise.

## Build the relocated example

The package includes original, project-owned MIT fixtures. Move the install
prefix, then configure the example from a separate directory:

```sh
cmake --preset phase1
cmake --build --preset phase1
cmake --install build --prefix build/package-prefix
cmake -E rename build/package-prefix build/relocated-prefix
cmake -S examples/relocated-c -B build/native-consumer \
  -DCMAKE_PREFIX_PATH="$PWD/build/relocated-prefix" \
  -DGBB_ROM_PATH="$PWD/build/relocated-prefix/share/gabbaboy/fixtures/visible-demo/demo.gb" \
  -DGBB_BATTERY_ROM_PATH="$PWD/build/relocated-prefix/share/gabbaboy/fixtures/mbc1-continuation/continuation.gb"
cmake --build build/native-consumer
cd build/native-consumer
./relocated-c \
  "$PWD/../relocated-prefix/share/gabbaboy/fixtures/visible-demo/demo.gb" \
  "$PWD/../relocated-prefix/share/gabbaboy/fixtures/mbc1-continuation/continuation.gb" \
  "$PWD/continuation.sav"
./relocated-c \
  "$PWD/../relocated-prefix/share/gabbaboy/fixtures/visible-demo/demo.gb" \
  "$PWD/../relocated-prefix/share/gabbaboy/fixtures/mbc1-continuation/continuation.gb" \
  "$PWD/continuation.sav"
```

The example links only `GabbaBoy::core`. It loads the visible demo into one
instance, queues timestamped A-button press/release events, advances no more
than 200,000 half-dot ticks, copies a 160x144 shade-index frame into host
storage, and emits 48 kHz signed-16 stereo frames into a host array. It then
loads the MBC1 continuation fixture into the same instance. Its first run
exports 8 KiB of raw battery RAM; its next run imports that exact-size file and
checks the fixture's resume marker. The package smoke repeats the same
sequence from an unrelated working directory.

The core battery API transfers bounded cartridge RAM bytes only (for MBC2 type
`$06`, a canonical 512-byte image whose upper nibbles are `$F`; import
normalises each byte to `$F0 | (b & $0F)` and packed 256-byte saves are not
supported). Your host must
choose the save location, validate its exact expected length, retain any
recovery copy, and use a safe replacement method. The example writes a sibling
temporary file, flushes it, then atomically replaces the prior save; a failed
write leaves the previous complete file in place. The demonstration file is
not the SDL player's versioned/checksummed save envelope, and the raw API does
not authenticate data or detect same-size corruption. See the
[save contract](cartridge-and-saves.md) before designing production persistence.

## API and errors

- `gbb_create` selects the explicit bootless `GBB_PROFILE_DMG_CPU_B` profile;
  `gbb_destroy` releases the opaque instance.
- `gbb_load_rom` copies input bytes on success. The loader accepts exact
  supported lengths up to 8 MiB for MBC5 types (`$19`-`$1E`), up to 4 MiB for
  MBC3 types (`$0F`-`$13`; the MBC30 variant is rejected with
  `GBB_UNSUPPORTED_CARTRIDGE_VARIANT`) and up to 2 MiB for every other type; an
  oversized length returns `GBB_ROM_TOO_LARGE`, and a
  loaded cartridge needs at most 8 MiB of ROM plus 128 KiB of RAM. Failed
  replacement leaves active guest state unchanged. Read the full file under a
  host-selected bound before loading.
- `gbb_rumble_state` reports the MBC5 rumble line (`$1C`-`$1E`) as an on/off
  value plus a saturating transition count; sample it once per frame.
  Other cartridges return `GBB_NO_RUMBLE`. The core drives no haptics.
- `gbb_queue_events` copies up to 64 absolute, nondecreasing half-dot events.
  Timestamps cannot be earlier than current emulated time. This is guest time,
  not host wall-clock scheduling.
- `gbb_run` and `gbb_run_audio` accept a half-dot budget and stop at whole
  instruction boundaries. Check both `reason` and `consumed_half_dots`;
  output-full, no-progress, stopped, and unsupported/invalid states need caller
  handling. A too-small budget may make no progress.
- `gbb_copy_frame` writes one DMG shade index per pixel into caller memory;
  check dimensions and generation. It may return `GBB_FRAME_NOT_READY` until
  the guest has completed a frame.
- `gbb_run_audio` writes caller-owned 48 kHz signed-16 stereo frames. Capacity
  is counted in complete frames; preserve or consume written samples before
  reusing the storage. The core allocates no audio buffer.
- `gbb_battery_size`, `gbb_copy_battery`, and `gbb_import_battery` transfer
  exact-size bytes for supported battery-backed cartridges. They do not do
  file I/O or define a raw-save file format.
- `gbb_rtc_catch_up` applies host wall-clock time to MBC3 timer cartridges
  (`$0F`, `$10`). Compute a non-negative whole-second elapsed value from your
  own clock between runs and call it once per open, on the instance, between
  `gbb_run*` calls; two calls add twice. Record the value as an input event so
  replays reproduce it. A negative value returns `GBB_INVALID_ARGUMENT` and
  changes nothing, so you decide what a clock rollback means; a cartridge
  without a timer (or no ROM) returns `GBB_NO_RTC`. Importing a battery image
  never catches up: import restores the saved clock exactly and never advances
  it, so call `gbb_rtc_catch_up` yourself afterwards if time passed. Persist
  the whole battery image through `gbb_battery_size`, `gbb_copy_battery` and
  `gbb_import_battery`: timer cartridges export RAM followed by a
  `GBB_RTC_BLOCK_SIZE`-byte clock block (the block alone for `$0F`). The core
  never reads the host clock.

On a load error, keep the current session and report the returned `gbb_error`;
do not replace the active cartridge with partial input. Reject truncated,
oversized, malformed, unsupported, or wrong-size data before modifying
application state. The public header documents the full per-call behavior and
buffer contracts.

## CGB-CPU-E profile

- The CGB-CPU-E profile is selected with `GBB_PROFILE_CGB_CPU_E` passed to
  `gbb_create`; destroy the instance and create a new one to change profile.
  It starts in the bootless CGB-CPU-E post-boot state (see the
  [CGB profile](cgb-profile.md)) and runs original and admitted test ROMs. It
  renders colour frames, read with `gbb_copy_frame_rgb555` (below), and is not a
  game-compatibility claim.
- Classify a ROM before loading with `gbb_probe_rom`, which needs no instance,
  or ask a loaded instance with `gbb_get_info`. Both fill a `gbb_info`. Set
  `struct_size` to `sizeof(gbb_info)` before the call: the core writes only
  within that size, sets it to 28 (`GBB_INFO_SIZE_V1`) on success, and leaves
  any extra bytes of a larger caller struct untouched. A size below 28 is
  `GBB_INVALID_ARGUMENT`, with outputs unchanged on error.
- `mode` is `GBB_MODE_NONE` (no ROM loaded), `GBB_MODE_DMG`, `GBB_MODE_CGB` or
  `GBB_MODE_CGB_DMG_COMPAT`. It comes from the profile and header byte `$143`,
  never from a host toggle. `cgb_support` is `GBB_CGB_SUPPORT_NONE`,
  `GBB_CGB_SUPPORT_ENHANCED` (`$80`), `GBB_CGB_SUPPORT_ONLY` (`$C0`),
  `GBB_CGB_SUPPORT_OTHER` or `GBB_CGB_SUPPORT_PGB`. `flags` combines
  `GBB_INFO_HAS_ROM`, `GBB_INFO_CGB_ONLY_ON_DMG`, `GBB_INFO_HAS_BATTERY`,
  `GBB_INFO_HAS_RTC` and `GBB_INFO_HAS_RUMBLE`; `GBB_INFO_CGB_ONLY_ON_DMG` is
  informational and the load still succeeds.
- A PGB-flagged `$143` (bit 7 set with bit 2 or bit 3 set) returns
  `GBB_UNSUPPORTED_EXECUTION_MODE` from `gbb_load_rom` and `gbb_probe_rom` on the
  CGB profile; the DMG profile probes it as `GBB_CGB_SUPPORT_PGB` with `GBB_OK`.
- `gbb_copy_frame` returns `GBB_UNSUPPORTED_PROFILE` on the CGB profile, because
  one shade byte per pixel cannot express the background, OBJ0 and OBJ1
  palettes; invalid arguments still return `GBB_INVALID_ARGUMENT`. Read colour
  with `gbb_copy_frame_rgb555` instead.
- Colour summary (details in the next section): the minimum pitch is 320 bytes
  and sizes are in bytes; for `gbb_set_compat_palette`, bit 15 is rejected, not
  masked, and a set never recolours a completed frame.
- CGB mode has two VRAM banks and eight WRAM banks, selected by the guest
  through VBK and SVBK. `gbb_peek_ram` follows the selected WRAM bank for
  `$D000`-`$DFFF` and its echo, so read it after the guest has set SVBK.
- On the CGB profile, guest code can switch to double speed with KEY1 and STOP.
  Budgets, `consumed_half_dots`, and frame intervals use master half-dots at
  both speeds: one frame is 140448 half-dots. The speed-switch pause is
  consumed across calls; each call returns `GBB_STOP_BUDGET` with progress,
  never `GBB_STOP_STOPPED` or `GBB_STOP_HALTED_IDLE`. A budget below one
  instruction or one stall M-cycle returns `GBB_STOP_BUDGET` with
  `consumed_half_dots` equal to zero. Speed is guest-visible through KEY1 bit 7;
  there is no public speed getter.
- Limitations: no HDMA, and CGB mode-3 timing is not claimed. Registers whose
  behaviour is owned by a later phase stop with `GBB_STOP_UNSUPPORTED_BUS`
  rather than invent a value. DMG addresses `$FF4C`-`$FF7F` stay fail-closed.
  IE bits 5-7 are stored on the CGB profile only. The DMG rule that OAM DMA
  blocks the CPU outside HRAM is kept on the CGB profile although real CGB
  hardware has separate buses. See [CGB profile](cgb-profile.md) and
  [model gates](model-gates.md).

### Colour frames and the compatibility palette

`gbb_copy_frame_rgb555` copies the latest completed 160x144 frame as
native-endian `uint16_t` values `R | G << 5 | B << 10` with bit 15 always
clear. It serves the CGB profile in CGB mode and in compatibility mode, and
returns `GBB_UNSUPPORTED_PROFILE` on the DMG profile, where `gbb_copy_frame`
is the call to use. Both sizes are in bytes: the minimum pitch is 320 bytes
(an even number, one 160-pixel row), the capacity must cover
`143 * pitch + 320` bytes, and the destination must be 2-byte aligned. Every
check runs before any write: an invalid pointer, alignment, pitch, capacity or
overlap with the `gbb_frame_info` output returns `GBB_INVALID_ARGUMENT`, then
the profile check, then `GBB_FRAME_NOT_READY` before a frame completes or after
`gbb_reset`. On any error nothing is written. The core never allocates, and
`gbb_frame_info` is the same unchanged struct `gbb_copy_frame` fills. While the
LCD is off the last completed frame stays readable and the generation does not
advance.

The core applies no colour correction. A host that wants 8-bit channels expands
each 5-bit channel `c` with `(c << 3) | (c >> 2)` and applies any display
correction itself. To digest a frame, write each value as an explicit
little-endian byte pair rather than hashing host memory.

In compatibility mode the shade indices of a DMG game resolve through a
`gbb_compat_palette` (`GBB_COMPAT_PALETTE_SIZE_V1`, 28 bytes: `struct_size`
then four RGB555 values each for `bg`, `obj0` and `obj1`). Set `struct_size`
before `gbb_get_compat_palette`; it writes within that size and sets it to 28.
A size below 28, a NULL instance or a NULL output returns `GBB_INVALID_ARGUMENT`
with nothing written. `gbb_set_compat_palette` validates the whole struct
before it stores anything: a `struct_size` below 28 or any entry with bit 15 set
returns `GBB_INVALID_ARGUMENT` and leaves the palette unchanged, because
bit 15 is rejected, not masked. A larger struct is accepted and its extra bytes are
ignored. A NULL palette restores the default. Both profiles accept the calls,
but only compatibility mode shows an effect; CGB mode colours come from the
guest's CRAM. The palette is instance configuration that survives `gbb_reset`
and `gbb_load_rom`. A set never recolours a completed frame: it applies to


## Support and upgrade

The tracked [v0.1.0 support ledger](support/v0.1.0.md) describes the exact
bootless DMG-CPU-B model, ROM-only and standard MBC1 subset, three eligible
derived CPU/timer corpus cases, fixture identities, failures, exclusions, and
evidence classes. The tagged release publishes a separate
`support-ledger.json` attachment binding the exact source SHA to the
tagged ledger blob digest and fixture/corpus identities. The three-case corpus
is not a game compatibility percentage. No physical DMG observation, CGB,
MBC1M, RTC, broad game-library, or perceptual claim is made.

The optional macOS SDL3 player is the current interactive host. The inspected
Playstead adapter at pinned revision
[`a102d6082968bc09ca00fefbf5c552ecf979fd63`](https://github.com/szTheory/playstead/blob/a102d6082968bc09ca00fefbf5c552ecf979fd63/playstead-mac/Playstead/Adapter/AdapterHost.swift)
uses an external process for GBA/mGBA. This native C example shows a possible
future Game Boy adapter seam; it is not a live GabbaBoy/Playstead integration.

To upgrade, install the new package into a clean prefix, reconfigure the host
project with that prefix, rebuild, and rerun its package smoke before replacing
the deployed consumer. Treat each preview as an API/ABI change opportunity;
there is no stable ABI or binary compatibility guarantee. Keep the exact
versioned ledger and source-bound sidecar with the release being adopted.

## Troubleshooting

| Symptom | Check |
|---|---|
| `find_package` cannot locate GabbaBoy | Set `CMAKE_PREFIX_PATH` to the relocated install prefix and verify `lib/cmake/GabbaBoy/GabbaBoyConfig.cmake` exists. |
| Build finds an unexpected header/library | Remove stale build output, configure into a fresh directory, and inspect compile/link commands for source or original build paths. |
| ROM load is rejected | Confirm exact file length and the supported ROM-only/standard-MBC1 matrix in the [save and cartridge contract](cartridge-and-saves.md). |
| Frame copy returns `GBB_FRAME_NOT_READY` | Continue bounded execution until the guest has completed a frame; do not read pixels after an error. |
| Audio returns output-full | Consume/preserve caller-owned frames and retry with available capacity; the core does not queue or overwrite them. |
| Battery import fails | Confirm the cartridge is battery-backed and the host file contains exactly the queried RAM size. Preserve the old file while investigating. |
| A previous save seems missing | Check the host-selected path and permissions. The core never chooses or searches a filesystem path. |

The examples and tests establish software behavior for the declared model.
They do not establish physical DMG behavior, universal ROM compatibility,
physical audio quality, platform floors beyond the measured runner matrix, or
signing/notarization of a release asset.
