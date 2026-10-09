# GabbaBoy DMG preview

The optional SDL3 player opens the original project-owned 32 KiB demo on startup. It presents copied frames from the core at a 10:9 aspect ratio with nearest-neighbor integer scaling, including on high-density displays. It accepts 32 KiB ROM-only images and the core's documented standard-MBC1 header matrix; MBC1M remains unsupported, with a conservative detector that cannot identify every special-wiring image. The optional player also plays the core's scoped DMG-CPU-B digital APU output as 48 kHz signed 16-bit interleaved stereo.

See [Cartridge and battery save contract](cartridge-and-saves.md) for the exact supported header matrix, save envelope, recovery behavior, and integration API.

For a relocated installed C consumer, including bounded stepping, timestamped
input, caller-owned video/audio, and host battery import/export, see the
[native integration guide](native-integration.md). Its Playstead section
describes a possible future adapter seam; no live Game Boy integration exists.
The tracked [v0.1.0 support ledger](support/v0.1.0.md) states the model and
corpus limits. The release's separate `support-ledger-v<version>.json`
attachment binds that ledger to the exact tagged source revision.

The portable core and its normal tests do not need SDL. To build and verify the optional player with the official, digest-checked SDL3 3.4.18 source on macOS, run:

```sh
bash tests/scripts/verify-phase3-player.sh
```

The verifier forces SDL's dummy audio driver before initialization and requires
the built stream to open, accept PCM, close, and recover. For a separate
five-second authored workload receipt after the verifier, run:

```sh
bash tests/scripts/measure-audio-playback.sh
```

It checks PCM identity across two core-call partitions and writes its JSON
receipt and PCM bytes under `build/phase3-player/audio-measurement/`.

Every pull request runs the hosted macOS package lane. It checks out the exact pull-request head, builds with the pinned SDL source, runs the nonempty player test inventory, packages the executable with SDL, both original fixtures, and license notices, then uploads a short-lived candidate. The player smoke injects SDL Z-down and Z-up events, samples the rendered demo tile while held and after release, and checks the matching guest results. A separate macOS consumer job downloads that exact candidate, checks its digest and source/SDL/fixture/license metadata, extracts it, and reruns the same SDL event, guest-response, rendered-pixel, and MBC1 battery-continuation smoke before uploading the qualified preview artifact. The continuation smoke runs the packaged ROM in one process to write progress and a fresh process to resume it. The candidate is retained for one day; the qualified preview and receipt are retained for 14 days.

The macOS package contains `bin/gabbaboy-player`, its bundled `lib/libSDL3.0.dylib`, the demo fixture and the reproducible MBC1 continuation source/ROM/manifest under `share/gabbaboy`, license notices, preview documentation, and provenance metadata. Package metadata records the standard MBC1 type `$03`/8 KiB battery fixture digests and the implemented scoped DMG audio model. The package is unsigned and not notarized. The verification smoke uses an offscreen software renderer and isolated temporary preferences; it verifies software file-backed continuation and the SDL dummy audio path, not physical hardware behavior, native-window appearance, or audible quality.

After a local build succeeds, launch `build/phase3-player/gabbaboy/gabbaboy-player` on a desktop. For a qualified hosted artifact, download and extract the `.tar.gz` package, then launch `installed-prefix/bin/gabbaboy-player`; the player locates its bundled demo relative to its executable.

## Controls

| Action | Control |
|---|---|
| Open a ROM | Command-O |
| Quit | Command-Q |
| D-pad | Arrow keys |
| D-pad | Gamepad D-pad |
| A / B | Z / X |
| A / B | Gamepad bottom/South / right/East buttons |
| Start / Select | Return / Right Shift |
| Start / Select | Gamepad Start / Back |
| Pause / resume | Space |
| Host volume down / up | [ / ] (10% steps) |
| Reset the current ROM | R |
| Save battery RAM now / retry a failed background save | S |
| Retry a reset, replacement, or quit blocked by a failed save | R; continue without saving: C; cancel: Escape |
| Show controls and limitations | F1 |

The window title shows the active ROM filename, run/pause state, current host gain, Open/Quit shortcuts, audio sink status, and the current status. Host gain defaults to 100% and ranges from 0% to 200%; it does not change guest APU registers. If no audio device opens, the player discards and counts PCM while keeping guest execution host-paced. Changed battery RAM autosaves after 2 seconds without a change or after 10 seconds at most. A failed autosave stays visible in the title and F1 help until a save succeeds. Before reset, ROM replacement, or quit, a failed final save pauses the transition: press R to retry, C to continue without saving, or Escape to cancel. During that prompt, R means retry; otherwise it resets the ROM. The F1 help panel shows keyboard and gamepad mappings, 48 kHz s16 stereo format, gain range, recovery behavior, status, and evidence limits.

## Supported images and limits

The player accepts exact 32 KiB ROM-only images and standard MBC1 images supported by the core (types `$01`–`$03`, ROM size codes `$00`–`$06`, and the documented no-RAM/8-KiB/32-KiB header matrix). Battery persistence applies only to type `$03` with 8 or 32 KiB RAM. Type `$02` RAM is volatile for the loaded session. Save files use GabbaBoy's versioned, identity-bound envelope in the SDL per-user preferences directory. Malformed or wrong-identity saves are preserved under a recovery name before fresh `$FF` RAM is used; if preservation fails, persistence is disabled and the original file remains untouched. A stable per-save advisory lock blocks a second cooperating GabbaBoy writer; external tools do not honor this lock automatically. The file-dialog filter is only a hint; every selected file goes through the bounded core loader. If a replacement is truncated, malformed, unsupported, too large, cannot be read, or its save lock cannot be acquired, the current ROM and guest state remain active and the window title reports the issue.

## Audio behavior and limits

The core's four-channel digital APU model follows the emulated divider and
produces caller-owned 48 kHz signed 16-bit interleaved stereo frames. The
player applies host-only volume control through a bounded SDL3 stream. Pause
and focus cleanup, reset, successful ROM replacement, and device recovery
follow the queue-clear and save-ordering rules in
[Audio and playback contract](audio-and-playback.md). The SDL queued-input
byte count is not playback latency; application PCM underflow is not proof of
hardware starvation.

The preview does not implement MBC1M, RTC, CGB, VIN, full-machine snapshots, or
arbitrary raw `.sav` import/export. Its digital audio is a deterministic
DMG-CPU-B software model; physical hotplug, board/revision equivalence, analog
output, and listening quality are not qualified. Passing software tests does
not establish physical DMG/MBC1 behavior, current live-window appearance,
signing, notarization, or release readiness.
