# GabbaBoy DMG preview

The optional SDL3 player opens the original project-owned 32 KiB demo on startup. It presents copied frames from the core at a 10:9 aspect ratio with nearest-neighbor integer scaling, including on high-density displays. It accepts 32 KiB ROM-only images and the core's documented standard-MBC1 header matrix; MBC1M remains unsupported, with a conservative detector that cannot identify every special-wiring image.

See [Cartridge and battery save contract](cartridge-and-saves.md) for the exact supported header matrix, save envelope, recovery behavior, and integration API.

The portable core and its normal tests do not need SDL. To build and verify the optional player with the official, digest-checked SDL3 3.4.18 source on macOS, run:

```sh
bash tests/scripts/verify-phase3-player.sh
```

On a pull request, apply the `run-macos-player` label to request the hosted macOS package lane. It checks out the exact pull-request head, builds with the pinned SDL source, runs the nonempty player test inventory, packages the executable with SDL, both original fixtures, and license notices, then uploads a short-lived candidate. A separate macOS consumer job downloads that candidate, checks its digest and source/SDL/fixture/license metadata, extracts it, and reruns the SDL event, guest-response, completed-frame, and MBC1 battery-continuation smoke before uploading the qualified preview artifact. The continuation smoke runs the packaged ROM in one process to write progress and a fresh process to resume it. The candidate is retained for one day; the qualified preview and receipt are retained for 14 days.

The package contains `bin/gabbaboy-player`, its bundled `lib/libSDL3.0.dylib`, the demo fixture and the reproducible MBC1 continuation source/ROM/manifest under `share/gabbaboy`, license notices, preview documentation, and provenance metadata. Package metadata records the supported standard MBC1 type `$03`/8 KiB battery fixture and its source and ROM digests. The package is unsigned and not notarized. The verification smoke uses an offscreen software renderer; it verifies software file-backed continuation, not physical hardware behavior or live-window appearance.

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
| Save battery RAM now / retry a failed save | S |
| Show controls and limitations | F1 |

The window title shows the active ROM filename, run/pause state, Open/Quit shortcuts, and the current status. Changed battery RAM autosaves after 2 seconds without a change or after 10 seconds at most. A failed autosave stays visible in the title and F1 help until a save succeeds. Before reset, ROM replacement, or quit, a failed final save pauses the transition: press R to retry, C to continue without saving, or Escape to cancel. During that prompt, R means retry; otherwise it resets the ROM. The F1 help panel shows the complete key map and ROM name.

## Supported images and limits

The player accepts exact 32 KiB ROM-only images and standard MBC1 images supported by the core (types `$01`–`$03`, ROM size codes `$00`–`$06`, and the documented no-RAM/8-KiB/32-KiB header matrix). Battery persistence applies only to type `$03` with 8 or 32 KiB RAM. Type `$02` RAM is volatile for the loaded session. Save files use GabbaBoy's versioned, identity-bound envelope in the SDL per-user preferences directory. Malformed or wrong-identity saves are preserved under a recovery name before fresh `$FF` RAM is used; if preservation fails, persistence is disabled and the original file remains untouched. A stable per-save advisory lock blocks a second cooperating GabbaBoy writer; external tools do not honor this lock automatically. The file-dialog filter is only a hint; every selected file goes through the bounded core loader. If a replacement is truncated, malformed, unsupported, too large, cannot be read, or its save lock cannot be acquired, the current ROM and guest state remain active and the window title reports the issue.

The preview targets the bootless DMG-CPU-B profile. It does not implement audio, MBC1M, RTC, CGB, full-machine snapshots, or arbitrary raw `.sav` import/export. Passing software tests does not establish physical DMG/MBC1 behavior, current live-window appearance, signing, notarization, or release readiness. The package smoke uses an offscreen software renderer and verifies file-backed continuation rather than perceptual quality.
