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

The core battery API transfers bounded raw RAM bytes only. Your host must
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
  supported lengths up to 2 MiB; failed replacement leaves active guest state
  unchanged. Read the full file under a host-selected bound before loading.
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

On a load error, keep the current session and report the returned `gbb_error`;
do not replace the active cartridge with partial input. Reject truncated,
oversized, malformed, unsupported, or wrong-size data before modifying
application state. The public header documents the full per-call behavior and
buffer contracts.

## Support and upgrade

The tracked [v0.1.0 support ledger](support/v0.1.0.md) describes the exact
bootless DMG-CPU-B model, ROM-only and standard MBC1 subset, three eligible
derived CPU/timer corpus cases, fixture identities, failures, exclusions, and
evidence classes. The tagged release publishes a separate
`support-ledger-v<version>.json` attachment binding the exact source SHA to the
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
