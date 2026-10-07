# GabbaBoy DMG preview

The optional SDL3 player opens the original project-owned 32 KiB demo on startup. It presents copied frames from the core at a 10:9 aspect ratio with nearest-neighbor integer scaling, including on high-density displays.

The portable core and its normal tests do not need SDL. To build and verify the optional player with the official, digest-checked SDL3 3.4.18 source, run:

```sh
bash tests/scripts/verify-phase3-player.sh
```

After that succeeds, launch `build/phase3-player/gabbaboy/gabbaboy-player` on a desktop. The verification smoke uses an offscreen software renderer and does not replace a live-window visual check.

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

The preview targets the bootless DMG-CPU-B profile. It does not implement audio or battery-save persistence. This player smoke does not establish physical DMG behavior. The native window has not been visually checked in the current environment because no desktop display is available.
