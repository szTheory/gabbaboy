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
- `gbb_get_input_clock` reads, without changing anything, the clock that
  admits input events. Use it to re-anchor input after `gbb_load_state`, which
  restores the saved emulated time and up to 64 queued events. Set
  `struct_size` to `sizeof(gbb_input_clock)` before the call; a value below
  `GBB_INPUT_CLOCK_SIZE_V1`, a NULL instance or a NULL output returns
  `GBB_INVALID_ARGUMENT` and leaves the struct unchanged, and a larger struct
  keeps its extra bytes. The call fills `queued_count`, `now_half_dots` and
  `last_queued_half_dots`, which equals `now_half_dots` when nothing is queued.
  After a load, queue new events at or after the larger of `now_half_dots` and
  `last_queued_half_dots`; an earlier time returns `GBB_INVALID_EVENT` from
  `gbb_queue_events`.
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

## Qualify a relocated C and C++ installation

The release consumer verifier exercises the repository's installed C and C++
clients against package bytes after moving a fresh install outside the
checkout and build tree. It configures each client separately through
`find_package(GabbaBoy CONFIG REQUIRED)` and links only `GabbaBoy::core`:

```sh
cmake --preset phase1
cmake --build --preset phase1
python3 -I tests/scripts/verify-v02-consumers.py --run \
  --output build/v02-consumers.json
python3 -I tests/scripts/verify-v02-consumers.py --self-test
```

The receipt is published only after both programs run successfully. It records
the package tree SHA-256, the source revision reported by the installed
runner, the C and C++ compiler identities, and the profile, probe/info,
RGB555, and RTC behaviors completed by each client. The self-test also runs
the production CLI against missing-prefix, missing-package-config, and
failing-consumer controls. A positive installed-consumer result proves those
software calls against the tested package; it does not promise a stable ABI
or establish game compatibility.

To verify an installation already extracted outside the checkout and build
tree, pass its directory as `--prefix` and choose a fresh receipt path:

```sh
python3 -I tests/scripts/verify-v02-consumers.py \
  --prefix "$TMPDIR/gabbaboy-v0.2.0" \
  --output build/v02-downloaded-consumers.json
```

This checks the same CMake package and executes both clients against that
prefix. The core remains filesystem- and clock-agnostic; your host owns save
paths, save-file envelopes, and the wall-clock seconds passed to
`gbb_rtc_catch_up`.

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
  Budgets, `consumed_half_dots`, and frame intervals use master half-dots at both speeds:
  one frame is 140448 half-dots. The speed-switch pause is
  consumed across calls; each call returns `GBB_STOP_BUDGET` with progress,
  never `GBB_STOP_STOPPED` or `GBB_STOP_HALTED_IDLE`. A budget below one
  instruction or one stall M-cycle returns `GBB_STOP_BUDGET` with
  `consumed_half_dots` equal to zero. Speed is guest-visible through KEY1 bit 7;
  there is no public speed getter.
- CGB DMA: guest writes to FF51-FF55 start GDMA (bit 7 clear) or HBlank DMA
  (bit 7 set) in the selected CGB-CPU-E software model. GDMA holds the CPU
  until its requested blocks complete. HBlank DMA can grant one initial
  16-byte block while the LCD is off or in visible mode 0; later blocks wait
  for a visible mode-3-to-0 edge. VBlank does not grant a block. FF55 reports
  the active remaining count and reads `$FF` at completion. Cancelling a
  waiting transfer with bit 7 clear discards its remaining work, keeps its
  advanced cursors, and reads back `$80 | written_low7`; the adopted `$00`
  sequence reads `$80`.
- The unchanged `gbb_run` consumer path advances these guest operations. The
  current instruction retires before a latched HBlank request is serviced;
  the bounded DMA steal is applied before interrupt dispatch or the next
  opcode. This instruction-boundary pending-steal model is an approximation,
  not bus-cycle timing. In HALT, an admitted block continues, a timer
  IF/IE condition can wake the CPU, and an HBlank edge seen during HALT is not
  replayed; the guest waits for another visible edge.
- Each selected 16-byte block uses 64 half-dots of data: one byte commits every
  four master half-dots, with no modeled startup or teardown. Each block's
  source and destination window is validated before its first byte. Invalid
  windows and destination overflow stop with `GBB_STOP_UNSUPPORTED_BUS`
  before that block mutates VRAM; completed earlier blocks remain committed.
  These transfer boundaries and cadence are software policy, not a hardware
  measurement.
- CGB audio observations are guest-only digital register samples. Guest code
  can read FF76 and FF77 to observe the selected model's channel DAC inputs and
  include those values in its own test result. There is no public PCM getter,
  UI, or physical audio-device observation path. The existing `gbb_run_audio`
  buffer contains generated software-model PCM; analog output, mixing quality,
  and physical CGB-E audio remain unqualified.
- The selected bootless CGB-CPU-E software model has no physical CGB-E
  qualification; physical CGB-E remains UNKNOWN/POLICY. The D-06 `$83` ->
  `$02` -> `$00` -> `$80` readback follows the pinned SameSuite sequence and
  remains in contradiction with Pan Docs. Optional Mealybug CGB-C cases are
  `not-run:rights-gate-G1`, informational only, and outside the CGB-E
  denominator. CGB mode-3 timing remains unclaimed; the CGB profile's APU is
  still the DMG APU software model, and no general game compatibility is
  claimed. Registers whose behaviour belongs to a later phase stop with
  `GBB_STOP_UNSUPPORTED_BUS`. DMG addresses `$FF4C`-`$FF7F` stay fail-closed.
  See [CGB profile](cgb-profile.md) and [model gates](model-gates.md).

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


## Host process contract

`gabbaboy-runner` has a second invocation form for a process supervisor. Host mode is a headless
conformance adapter, not a play surface: it loads a ROM, imports an exact-size raw battery file,
runs fixed frames and publishes the battery image. It uses only the public C API and the same core
as every other mode.

```sh
gabbaboy-runner --rom ROM --save-dir DIR [--profile dmg|cgb] [--frames N]
gabbaboy-runner --print-save-format --rom ROM [--profile dmg|cgb]
```

`--rom` and `--save-dir` select host mode; `--profile` defaults to `dmg`. Without `--frames` the
runner is paced to real time and runs until it is stopped. With `--frames N` (a decimal count from 1
to 4,294,967,295) it runs exactly `N` frames as fast as it can and exits. One frame is 70,224 dots.
Each value flag takes its value as the next argument: `--flag=value`, positional arguments, unknown
flags, repeated flags, missing or empty values and acceptance-mode flags are refused with
`invalid-arguments: reason=<token>` and exit code 2. `--print-save-format` takes only `--rom` and
`--profile`.

### Save file and stem

The battery image is the raw file `{DIR}/{stem}.sav`: exactly the bytes of the core's battery API,
with no envelope. The stem is the last component of the ROM path with one final extension removed,
where an extension is a dot followed by 1 to 8 ASCII letters or digits; a dot in the first byte never
starts an extension. The stem is validated and never rewritten. These stems are refused with exit code
2 before any filesystem access: an empty stem, a stem that starts with a dot, one holding a control
character, DEL or a backslash, one that is not strict UTF-8, and one longer than 200 bytes. Playstead's
`deletingPathExtension` agrees with this rule for `.gb`, `.gbc`, `.GB`, `.GBC` and `.bin`, and differs
for other extensions, so a supervisor should name its ROM files with one of those. A missing `.sav`
is a fresh image. A `.sav` of any other size, a symlink, a special file, or a file that changes while
it is read is refused and left untouched. GabbaBoy makes no save interoperability claim with any other
emulator; the image is its own format, named by the table below.

### Durability and cadence

Each flush writes a temporary file in the save directory, syncs it, renames it over `{stem}.sav` and
syncs the directory. The result is an old-or-new image after process death or a crash; no power-loss guarantee
is made, and the tests do not establish one. The runner checks the battery generation at every frame
boundary. A change is flushed after 16 quiet frames, or once the first unflushed change is 300 frames old.
The runner also exports and compares the whole image every 3,600 frames, which catches clock-only drift on
timer cartridges. An abrupt stop therefore loses at most 300 frames plus one write of cartridge RAM changes,
and at most 3,600 frames of clock-only drift. After a failed flush the image stays dirty and the runner
retries 16 frames later. Before the first frame the runner removes stale temporary files named
`.{stem}.sav.tmp-` followed by anything, which only a crashed writer leaves.

Run one writer per save directory and ROM stem; a second runner on the same pair is unsupported and
its live temporary file may be swept.

The runner records no wall-clock time; the game clock advances only while the runner runs. It never
calls `gbb_rtc_catch_up`: an imported timer image resumes at its saved clock, and real time that
passes while no runner is running is not added to it. `gbb_get_input_clock` reports an
instance's input-admission clock (queued events, emulated time and the last queued time); it is the
public query a host uses to queue input after `gbb_load_state` restored a different time.

### Exit codes and signals

Host mode emits exactly these exit codes. The table is checked cell by cell against
`docs/host-contract.json` (backticks are formatting only).

| Code | Name | Meaning |
|---|---|---|
| `0` | `clean` | Signal or `--frames` end; the flush succeeded or there was nothing to write |
| `1` | `failure` | I/O or flush failure, allocation failure, or a core stop mid-run |
| `2` | `refusal` | Refused before any save mutation |
| none (death by signal) | `crash` | Death by signal (shells show 128+N); the `.sav` is the last completed flush |

Acceptance mode (ROM, manifest-case and manifest-suite invocations) keeps its own exit codes, which
host mode never emits and does not change. The runner stops on `SIGTERM` always, and on `SIGINT` and
`SIGHUP` unless they were ignored at start. It checks for a stop at frame boundaries, finishes no
partial frame, flushes the image, prints `gbb-host: exit` and returns 0 when the flush succeeded; a
second signal takes the default action. A refusal prints `gbb-host: refused reason=<token>` and never
prints `gbb-host: ready`. Diagnostics name stems and reason tokens, never a caller path.

### Windows

HOST-01/02 are POSIX-only in v0.3. Windows never generates SIGTERM and TerminateProcess cannot be handled; no console control handler is installed.
On Windows `--save-dir` mode is refused with
`gbb-host: refused reason=windows-unsupported` and exit code 2 before any filesystem access.
`--print-save-format` runs on every platform because it writes nothing.

### Save-format ids

`--print-save-format --rom ROM` prints one line, `save_format=<id> bytes=<n>`, and exits 0 without
creating any file. The id and byte count come from this table, which is published as
`share/gabbaboy/host-contract.json` in an installed package and as `docs/host-contract.json` in the
source tree. An id always means the same bytes; a new layout gets a new id, and rows are only ever appended. The Bytes column is the whole `.sav`: cartridge RAM, followed by the 21-byte clock block for
timer cartridges. The MBC1 32 KiB row covers header ROM codes `0x00` through `0x04`.

| Type | RAM code | Id | Bytes |
|---|---|---|---|
| `0x03` | `0x02` | `gabbaboy-mbc1-sram-8k-v1` | 8,192 |
| `0x03` | `0x03` | `gabbaboy-mbc1-sram-32k-v1` | 32,768 |
| `0x06` | `0x00` | `gabbaboy-mbc2-nibble-512-v1` | 512 |
| `0x0F` | `0x00` | `gabbaboy-mbc3-rtc-only-v1` | 21 |
| `0x10` | `0x02` | `gabbaboy-mbc3-rtc-sram-8k-v1` | 8,213 |
| `0x10` | `0x03` | `gabbaboy-mbc3-rtc-sram-32k-v1` | 32,789 |
| `0x13` | `0x02` | `gabbaboy-mbc3-sram-8k-v1` | 8,192 |
| `0x13` | `0x03` | `gabbaboy-mbc3-sram-32k-v1` | 32,768 |
| `0x1B` | `0x02` | `gabbaboy-mbc5-sram-8k-v1` | 8,192 |
| `0x1B` | `0x03` | `gabbaboy-mbc5-sram-32k-v1` | 32,768 |
| `0x1B` | `0x04` | `gabbaboy-mbc5-sram-128k-v1` | 131,072 |
| `0x1B` | `0x05` | `gabbaboy-mbc5-sram-64k-v1` | 65,536 |
| `0x1E` | `0x02` | `gabbaboy-mbc5-sram-8k-v1` | 8,192 |
| `0x1E` | `0x03` | `gabbaboy-mbc5-sram-32k-v1` | 32,768 |
| `0x1E` | `0x04` | `gabbaboy-mbc5-sram-128k-v1` | 131,072 |
| `0x1E` | `0x05` | `gabbaboy-mbc5-sram-64k-v1` | 65,536 |

save_format=none marks a cartridge without a battery; it is not a save-format id. A cartridge
of that kind creates no `.sav` file.

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
Playstead adapter, at Playstead main
[`234bd45b21`](https://github.com/szTheory/playstead/commit/234bd45b21),
runs GB, GBC and GBA through mGBA 0.10.5 as an external process adapter, not
through libretro or an FFI binding. This native C example shows a possible
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
