# GabbaBoy DMG preview

The optional SDL3 player opens the original project-owned 32 KiB demo on startup. It presents copied frames from the core at a 10:9 aspect ratio with nearest-neighbor integer scaling, including on high-density displays.

The portable core and its normal tests do not need SDL. To build and verify the optional player with the official, digest-checked SDL3 3.4.18 source on macOS, run:

```sh
bash tests/scripts/verify-phase3-player.sh
```

On a pull request, apply the `run-macos-player` label to request the hosted macOS package lane. It checks out the exact pull-request head, builds with the pinned SDL source, runs the nonempty player test inventory, packages the executable with SDL, the demo fixture, and license notices, then uploads a short-lived candidate. A separate macOS consumer job downloads that candidate, checks its digest and source/SDL/license metadata, extracts it, and reruns the SDL event, guest-response, and completed-frame smoke before uploading the qualified preview artifact. The candidate is retained for one day; the qualified preview and receipt are retained for 14 days.

The package contains `bin/gabbaboy-player`, its bundled `lib/libSDL3.0.dylib`, the demo fixture and manifest under `share/gabbaboy`, license notices, preview documentation, and provenance metadata. It is unsigned and not notarized. The verification smoke uses an offscreen software renderer and does not replace a live-window visual check.

After a local build succeeds, launch `build/phase3-player/gabbaboy/gabbaboy-player` on a desktop. For a qualified hosted artifact, download and extract the `.tar.gz` package, then launch `installed-prefix/bin/gabbaboy-player`; the player locates its bundled demo relative to its executable.

## Controls

| Action | Control |
|---|---|
| Open a ROM | Command-O |
| Quit | Command-Q |
| D-pad | Arrow keys |
| A / B | Z / X |
| Start / Select | Return / Right Shift |
| Pause / resume | Space |
| Reset the current ROM | R |
| Show controls and limitations | F1 |

The window title shows the active ROM filename, run/pause state, Open/Quit shortcuts, and the current status. The F1 help panel shows the complete key map and ROM name.

## Supported images and limits

The player accepts exact 32 KiB ROM-only images with no cartridge RAM and a valid header checksum. The file-dialog filter is only a hint; every selected file goes through the bounded core loader. If a replacement is truncated, malformed, unsupported, too large, or cannot be read, the current ROM and guest state remain active and the window title reports the error.

The preview targets the bootless DMG-CPU-B profile. It does not implement audio or battery-save persistence. Passing the event/frame smoke does not establish physical DMG behavior, a live-window perceptual review, signing, notarization, or release readiness. The native window has not been visually checked in the current environment because no desktop display is available.
