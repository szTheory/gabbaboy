# Cartridge and battery save contract

GabbaBoy's cartridge and save behavior is scoped to its bootless DMG-CPU-B
software profile. The rules here describe the implementation and its tests;
they do not qualify a physical Game Boy, every MBC1 board revision, or every
ROM that declares an MBC1 type.

## Supported cartridge matrix

The loader accepts exact ROM lengths and validates the header checksum before
replacing an instance's active cartridge. It supports:

| Header type | Cartridge behavior | ROM size codes | RAM size codes |
|---|---|---|---|
| `$00` | ROM-only | `$00` (32 KiB) | `$00` (none) |
| `$01` | Standard MBC1, no RAM | `$00`–`$06` (32 KiB–2 MiB) | `$00` (none) |
| `$02` | Standard MBC1 with volatile RAM | `$00`–`$06` | `$02` (8 KiB), or `$03` (32 KiB) only through 512 KiB ROM |
| `$03` | Standard MBC1 with battery-backed RAM | `$00`–`$06` | `$02` (8 KiB), or `$03` (32 KiB) only through 512 KiB ROM |

For MBC1 images larger than 512 KiB, the implementation accepts only 8 KiB
RAM. It rejects contradictory type/RAM declarations, other mapper types,
unsupported size codes, ROMs above 2 MiB, truncated images, and images whose
actual length differs from the declared ROM size. Recognized MBC1M candidates
return `GBB_UNSUPPORTED_CARTRIDGE_VARIANT`; the conservative alternate-bank
logo/header check does not identify every special-wiring image. MBC1M is
outside the support claim.

The standard MBC1 model has two banking modes. It keeps the low and upper ROM
bank registers separate, translates a zero low-bank selection to bank one
before applying the ROM-size mask, and uses the upper register for the lower
ROM window in mode 1. Mode 1 also selects a RAM bank when the cartridge has
multiple RAM banks. The RAM gate opens when the low nibble written in the
control range is `$A`; disabled or absent RAM reads return `$FF` and writes
are ignored as deterministic software policy where hardware references leave
the value undefined.

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

Battery APIs work only for a loaded type `$03` cartridge. They return
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

This API transfers raw RAM bytes in memory. It does not define an on-disk
format and does not import arbitrary emulator `.sav` files.

## Player save identity and version 1 format

The macOS player stores saves under the per-user application directory returned
by `SDL_GetPrefPath("GabbaBoy", "GabbaBoy")`, not beside the ROM. Its filename
contains the lowercase SHA-256 of the exact ROM bytes plus the cartridge type
and RAM size. Identical ROM bytes therefore use the same save identity when
moved or renamed; a byte-different ROM gets a different identity even if its
filename and cartridge header match. SHA-256 here is an identity key, not an
authentication mechanism.

The player-managed file is a field-by-field, little-endian version 1 envelope.
It has a 51-byte header followed by exactly 8 KiB or 32 KiB of raw battery RAM:

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
source, while the required regressions use synthetic banked ROMs and a
project-authored continuation ROM. The original fixture is MIT-licensed and
its source and 32 KiB ROM digests are recorded in
[`fixtures/mbc1-continuation/manifest.json`](../fixtures/mbc1-continuation/manifest.json).
These results establish software behavior under the named bootless profile.
No physical DMG-CPU-B/MBC1 observation, boot-ROM execution, CGB, RTC, MBC1M,
other mapper, general game-compatibility, or raw save-interchange claim is
made. Process-interruption tests exercise old-or-new complete file outcomes;
they do not simulate power loss.

Further evidence and named test coverage are in
[`docs/mbc1-evidence.md`](mbc1-evidence.md).
