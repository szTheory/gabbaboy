# Native machine state format

The native state API serializes a complete, bounded GabbaBoy machine state to a
caller-owned byte buffer. It has no filesystem access and does not replace the
cartridge battery API. The public calls are:

```c
gbb_error gbb_state_size(const gbb_instance *instance, size_t *out_size);
gbb_error gbb_save_state(const gbb_instance *instance, uint8_t *out_bytes,
                         size_t capacity_bytes);
gbb_error gbb_load_state(gbb_instance *instance, const uint8_t *bytes,
                         size_t size_bytes);
```

## Wire header

All integers are unsigned little-endian unless a body field is explicitly
signed. The header is exactly 64 bytes:

| Offset | Width | Field | Required value or meaning |
|---:|---:|---|---|
| 0 | 4 | Magic | ASCII `GBBS` |
| 4 | 2 | Format version | `1` |
| 6 | 2 | Header size | `64` |
| 8 | 2 | Release major | Exact `PROJECT_VERSION` major |
| 10 | 2 | Release minor | Exact `PROJECT_VERSION` minor |
| 12 | 2 | Release patch | Exact `PROJECT_VERSION` patch |
| 14 | 2 | Behavior version | `1` |
| 16 | 1 | Profile | Exact destination profile |
| 17 | 1 | Execution mode | Exact destination mode |
| 18 | 2 | Reserved flags | Both bytes zero |
| 20 | 32 | ROM identity | SHA-256 of the complete loaded ROM |
| 52 | 4 | Body size | Exact descriptor-derived size; at most `524288` |
| 56 | 4 | Total size | Exactly `64 + body size`; at most `524352` |
| 60 | 4 | CRC-32 | CRC described below |

Each release component must be a nonnegative decimal integer no greater than
65535. CMake rejects a version that does not have exactly three components or
that exceeds the wire range. A state can load only with the same release
triplet, behavior and format versions, profile, execution mode, and ROM digest.
The digest is an identity check, not authentication. Builds with the same
release triplet are qualified together by the project; an unreleased or
locally modified build has no cross-build compatibility promise unless it
retains the same state contract.

CRC is CRC-32/ISO-HDLC: reflected polynomial `0xEDB88320`, initial value
`0xFFFFFFFF`, reflected input and output, and final XOR `0xFFFFFFFF`. It covers
header bytes `0..59` followed by the body. The CRC field itself is excluded.
The check value for ASCII `123456789` is `0xCBF43926`. CRC detects accidental
corruption; it is not a MAC or signature.

## Body order and scalar encoding

The body has no C structure padding, pointers, host handles, or implicit
alignment. It walks 198 typed descriptors in this order:

1. Cartridge RAM bytes, with the length derived from the matching ROM.
2. Mapper registers, rumble state and MBC3 RTC state.
3. WRAM, HRAM, VRAM, OAM and bank/register state.
4. Both DMG frame buffers, both CGB RGB555 buffers, compatibility palette and
   frame metadata.
5. PPU scan/FIFO/fetch state, OAM DMA and CGB HDMA in-flight state.
6. Joypad, CPU registers and mode, interrupt, timer, divider, serial, lockup,
   and emulated-time state.
7. Input event count and all 64 fixed queue slots.
8. APU registers, channel/sequencer state, sample phase, signed audio event
   ring, mix levels and high-pass filter history.

Each descriptor contributes its fixed element count times its 1-, 2-, 4- or
8-byte wire width. Multi-byte values are little-endian. The ordered names,
counts, widths, and typed source fields are the `STATE_FIELDS` ledger in
[`src/core/gabbaboy.c`](../src/core/gabbaboy.c); its order is part of the wire
contract. A change to that ledger changes the body and requires a compatible
versioned format decision. Derived machine identity, ROM contents, observer
counters, test-only fields, pointers and host output buffers are not body data.

Booleans encode only `0` or `1`. The input count is at most 64; active events
are time ordered, cannot precede saved emulated time, and must have a valid kind
and value. Unused queue slots are encoded as zero and a decoder rejects
nonzero unused slots. CGB frame pixels and palette entries are at most `0x7FFF`;
DMG frame indices are `0..3`; MBC2's 512 RAM bytes use canonical `$F0 | nibble`
values. RAM is at most 131072 bytes. RTC fields must satisfy the timer cartridge
invariants; RTC state is zero for cartridges without a timer. Ordinary emulated
times are at most `2^62`; `timer_reloaded_at` may also use `UINT64_MAX` as its
validated sentinel.

Signed values use an explicit modulo-`2^64` representation rather than dumping
native signed objects. The decoder reconstructs negative values as
`-1 - (UINT64_MAX - encoded)`, after checking that the magnitude is representable;
out-of-range casts are not used. Audio limits are checked as a reachable
invariant, not as a guessed general-purpose numeric range:

| Bound | Derived limit |
|---|---:|
| Audio mix level | `-32768..28672` |
| Maximum mix delta | `61440` |
| Maximum coefficient delta | `32767` |
| Maximum edge contribution | `2013204480` |
| Maximum single edge half-dot lifetime | `2797` |
| Maximum ring lifetime envelope | `5630932930560` |
| High-pass input/output history | `INT16_MIN..INT16_MAX` |

The 16-slot ring check accounts for each slot's position relative to the head
and current sample phase. It bounds additions over the slot's remaining
lifetime. The executable `state_audio_bound` proof checks channel mix, edge,
coefficient, rounding, high-pass and lifetime arithmetic at the limiting
domains. The maximum admitted descriptor body is 320184 bytes, including the
maximum 131072-byte cartridge RAM; with the header the maximum emitted state is
320248 bytes. The separate 524288-byte format ceiling is an additional bound.
The installed DMG tracer currently emits 189176 bytes for its ROM and profile.

## Validation and mutation behavior

`gbb_state_size` and `gbb_save_state` require a loaded ROM and a live machine
that satisfies the state invariants. `gbb_save_state` writes exactly the
reported byte count and preserves any caller buffer tail. `gbb_load_state`
requires the exact state length; it validates the complete header, CRC, every
field and cross-field invariant before applying any state. A rejected load does
not mutate the destination. The API checks in this order:

| Condition | Result |
|---|---|
| Null required pointer | `GBB_INVALID_ARGUMENT` |
| State shorter than 64 bytes or wrong magic | `GBB_STATE_BAD_FORMAT` |
| Unsupported format/header/release/behavior version | `GBB_STATE_UNSUPPORTED_VERSION` |
| Destination has no ROM | `GBB_STATE_NO_ROM` |
| Profile, mode or ROM digest differs | `GBB_STATE_IDENTITY_MISMATCH` |
| Declared body/total or supplied exact length differs | `GBB_STATE_SIZE_MISMATCH` |
| CRC mismatch | `GBB_STATE_CORRUPT` |
| Reserved bytes or semantic invariant invalid | `GBB_STATE_INVALID_CONTENT` |
| Save buffer is shorter than the required size | `GBB_BUFFER_TOO_SMALL` |
| State bytes overlap the destination instance | `GBB_INVALID_ARGUMENT` |

The first seven state errors use the frozen public values 21 through 27 in the
order shown by the API enum. `out_size` and save output remain untouched on an
error. Input/output state buffers must be stable for the call and must not
overlap the instance. Calls on one instance must be externally serialized;
separate instances and their caller-owned buffers are independent. The codec
does not allocate memory or hash the ROM per call; the digest is computed once
after a successful ROM load. Loading replaces serialized machine state,
including cartridge RAM, RTC and compatibility palette, while host-side
observer history remains local to the receiving instance.

The format is evidence for the bootless DMG-CPU-B and modeled CGB profiles,
including the installed continuation tests. It does not claim physical-device
equivalence or acceptance of arbitrary third-party state containers. See
[`cartridge-and-saves.md`](cartridge-and-saves.md) for the API ownership
contract and the separate battery persistence formats.
