# Phase 18: Player Save Slots and Host Contract - Context

**Gathered:** 2026-10-28
**Status:** Ready for planning

<domain>
## Phase Boundary

Deliver PLAY-01 and HOST-01..03:
- numbered state slots in the SDL player, through the public API only, where a refused or mismatched slot leaves the running game untouched;
- a `--rom <path> --save-dir <dir>` host mode in the headless `gabbaboy-runner`:
  - atomic raw `{saveDir}/{romBaseName}.sav` with periodic flush;
  - SIGTERM save-and-exit, handled only in the adapter;
  - one tested exit-code table;
  - GabbaBoy-declared save-format ids and sizes in a machine-readable table, checked against the files the runner produces.

The plan cap is 10: at most 9 primary plans plus one gap slot, with a target of 8.

**Out of scope:**
- The Playstead AdapterPin, the continuation protocol and its exit 77, and live Playstead play (all INT-01b/RM-020).
- mGBA/BGB RTC footer interop (RM-021).
- libretro (RM-009).
- Rewind, thumbnails and state sync.
- The v0.3.0 release, which is Phase 19.

The owner directed deep multi-lens fan-out, an adversarial pass and automatic adoption of coherent recommendations. The fan-out was six parallel tracks:
- A: host binary;
- B: player slots;
- C: atomic writes;
- D: signals and exits;
- E: save-format table;
- G: a gap sweep.

An independent adversarial review then examined the merged draft. Every decision below is adopted. Revisit one only on a concrete contradiction, a failed prototype or discriminator, changed evidence, or owner direction. Small direct code or copied helpers are preferred over new dependencies.
</domain>

<decisions>
## Implementation Decisions

### Host binary and shared module

- **D-01: The headless runner owns the host contract; the contract logic lives in a reusable module.**
  - HOST-01..03 land in `gabbaboy-runner`, as the requirement text and D-104 ("host-process runner contract") say.
  - All contract logic goes in a new SDL-free, public-API-only static library `gabbaboy_host` (`src/host/`), linked by the runner and by the player's slot code. It covers:
    - the basename rule;
    - the dir-fd atomic writer;
    - the bounded reader and import;
    - the dirty rule and cadence;
    - the exit table;
    - the signal flag;
    - save-format id lookup.
  - The docs state plainly that host mode is a headless conformance adapter, not a play surface. Live play through a host (player host mode, Playstead) is deferred to RM-020, where it reuses `gabbaboy_host` unchanged.
  - Rejected: putting host mode in the player. The player is macOS-only, never runs under ASan and is absent from release workflows, and it would need SDL signal-hint and quit-prompt bypass work.
  - **Reversibility:** costly. Moving the contract later means re-plumbing the player, but the module boundary keeps that cheap.
- **D-02: Host-mode grammar.**
  - Syntax: `gabbaboy-runner --rom P --save-dir D [--profile dmg|cgb] [--frames N]`.
  - Arguments may come in any order, and `--rom` and `--save-dir` are both required.
  - Dispatch host mode before acceptance parsing and before the `argc==2` tracer route (`src/runner/main.c:451`).
  - Each of these exits 2: an unknown, duplicate, empty or missing value; a `--flag=value` form; any acceptance-mode flag; any positional argument.
  - `--print-save-format --rom P [--profile dmg|cgb]` prints `save_format=<id>` and `bytes=<n>`, creates nothing, and works on every platform.
  - The existing acceptance grammar and its 0/1/2/3/4 meanings are untouched.
- **D-03: Two run shapes; a "frame" is one fixed step.**
  - A frame is one fixed `gbb_run` step of 140,448 half-dots. This one definition is used for `--frames`, cadence and signal checks, and it removes the LCD-off special case.
  - **Paced** (no `--frames`): runs in real time until a signal. Pacing lives in one adapter function on `CLOCK_MONOTONIC`, with relative `nanosleep` and deadline correction (macOS has no `clock_nanosleep`). A signal wakes the sleep with EINTR.
  - **Batch** (`--frames N`): runs N frames unpaced, does the final flush and exits 0. It is used by the HOST-03, continuation and replay tests.
  - Host mode has no input; `--input-script` waits for RM-020.
- **D-04: Runner integration traps.**
  - Host mode has its own bounded ROM reader up to the core's `GBB_MAX_ROM_SIZE` (8 MiB), not the acceptance `MAX_ROM 32768u`.
  - Host and slot code includes only `gabbaboy/gabbaboy.h` and libc/POSIX headers, never `gabbaboy_test.h` or `gbb_accept.h`. A CTest compares the undefined `gbb_*` symbols of the `gabbaboy_host` and slot objects against the public header, and a seam-calling mutant must fail it.
  - Every new runner and `gabbaboy_host` source joins the `GBB_BUILD_QUALIFIED` dirty list (`CMakeLists.txt:85-87`). A CMake `-P` check asserts the runner's SOURCES are a subset of that list.
  - `src/host` compiles on MSVC through `#ifndef _WIN32` stubs.
  - Each POSIX file defines its own feature macros: `_POSIX_C_SOURCE 200809L`, plus `_DARWIN_C_SOURCE` on Apple. It must compile under `C_EXTENSIONS OFF` on glibc and macOS.

### Windows

- **D-05: Windows refuses host mode.**
  - On `_WIN32`, `--save-dir` mode exits 2 with a stderr reason before any filesystem access. `--print-save-format` still works.
  - A Windows CTest asserts the refusal. The POSIX-only tests are excluded in both `cmake/ExpectedTests.cmake` and `verify-test-inventory.sh` (GB-CGB-007).
  - Exemption text: "HOST-01/02 are POSIX-only in v0.3. Windows never generates SIGTERM and TerminateProcess cannot be handled; no console control handler is installed."
  - The precedent is LIM-WINDOWS-POSIX-CONTROLS. A Windows host mode is deferred.

### Atomic raw `.sav` persistence (HOST-01)

- **D-06: Save directory.**
  - It must already exist and is never created.
  - Open it once with `O_RDONLY|O_DIRECTORY|O_CLOEXEC`. Every later operation is `*at(dirfd, …)`.
  - Symlinks anywhere in the save-dir path are allowed: macOS `/tmp`, `/var` and Playstead containers use them. They are resolved once into the fd, so they cannot be swapped later.
  - A missing path or a non-directory exits 2.
  - Positive control: a save dir under macOS `/tmp`.
- **D-07: Basename: validate, never rewrite.**
  - Take the last path component of `--rom`. If it has a final `.ext` of 1–8 ASCII alphanumerics, strip it; otherwise use the whole name. This matches mGBA and Playstead's `deletingPathExtension`.
  - Refuse, with exit 2, any stem that:
    - is empty;
    - starts with `.` (this covers `.`, `..` and `..gb`, and keeps the dot-prefixed temp namespace clear);
    - contains a byte below 0x20 or equal to 0x7F;
    - contains `\`;
    - is not valid UTF-8;
    - is longer than 200 bytes, so the longest temp name still fits NAME_MAX.
  - Do not apply Unicode normalisation.
  - A mutant that transforms instead of refusing must fail its test.
- **D-08: Bounded import; a refusal means refuse to start.**
  - Size: get `want` from `gbb_battery_size` after the ROM loads. Apply a defensive cap (≤ 131,072 + 21) before allocating.
  - No-battery carts: never read or create a `.sav`, and ignore a stray one.
  - Open: `openat(dirfd, "<stem>.sav", O_RDONLY|O_NOFOLLOW|O_NONBLOCK|O_NOCTTY|O_CLOEXEC)`. ENOENT means a fresh image.
  - Read checks:
    - `fstat` reports `S_ISREG` and a size of exactly `want`;
    - an EINTR-safe read of up to `want+1` bytes returns exactly `want`;
    - a second `fstat` shows the same dev, inode and size;
    - then call `gbb_import_battery`.
  - Every other outcome exits 2 before the first frame. This covers:
    - a short, long or zero-byte file;
    - an mGBA 48-byte-footer file (32,816 B);
    - a bad RTC block;
    - a symlink, FIFO, directory or device at the `.sav` path.
  - On refusal the file stays byte-, inode- and mtime-identical and the directory listing is unchanged.
  - Never move a rejected file aside in a host-owned directory, and never fall back to fresh RAM.
- **D-09: One atomic writer, `save_io_replace(dirfd, name, bytes, len)`.**
  1. Create the temp file `.<stem>.sav.tmp-<pid>-<seq>` with `openat(O_WRONLY|O_CREAT|O_EXCL|O_NOFOLLOW|O_CLOEXEC, 0600)`. On EEXIST, bump `seq`, up to 16 tries.
  2. Write in an EINTR- and short-write-safe loop.
  3. Sync: `F_FULLFSYNC` on Apple, falling back to `fsync` on ENOTSUP/ENOTTY/EINVAL; `fsync` elsewhere. Never retry `fsync` on the same fd after EIO; discard that temp and rewrite from memory next time.
  4. `close` is checked and never retried.
  5. The target must be absent or `S_ISREG` (`fstatat AT_SYMLINK_NOFOLLOW`).
  6. `renameat`.
  7. `fsync(dirfd)`, tolerating EINVAL and ENOTSUP/EOPNOTSUPP.

  Any failure before the rename unlinks the temp. A directory-fsync failure after the rename reports failure and leaves the image dirty. Fault-injection seams exist in test builds only.
- **D-10: Stale-temp sweep, durability and single writer.**
  - The sweep runs once, after all refusal checks pass and before the first frame. It unlinks (without following links) every entry with the exact prefix `.<stem>.sav.tmp-`. There is no pid-liveness heuristic, because the contract is one writer per (save dir, stem).
  - Durability claim: old-or-new atomicity against process death or crash only. Power-loss durability is best effort, with no claim.
  - The contract documents the single writer. No lock files go in the host directory.
- **D-11: Dirty rule and cadence (frames per D-03).**
  - **First write:** for a battery cart whose `.sav` is absent, the first flush creates it, at the latest at the final flush even if the image is all `$FF`. HOST-03 needs every row to produce a file, including the 21 B `$0F` row.
  - **Generation trigger:** when `gbb_battery_generation` changes (compare with `!=`), flush after 16 quiet frames, or when the first unflushed change is 300 frames old.
  - **RTC drift:** RTC ticking does not bump the generation. Every 3,600 frames, and at the final flush, export the image and compare it with the last persisted bytes. Write only if they differ, so an identical image is never rewritten (Playstead's `confirm_count`).
  - **Declared loss windows:** 300 frames plus one write (≈5.1 s paced) for SRAM writes, and 3,600 frames (≈1 min) for RTC-only drift.
  - Update `flushed` only after the writer succeeds. A failed periodic flush is retried at the next cadence point.
- **D-12: No wall-clock RTC catch-up in host mode.** A raw `.sav` has no timestamp, and its 32,789 B size leaves no room for one. The game clock advances only while the runner runs. Declare this in the docs, the table and the limitations. Do not use `--clock-unix` or mtime heuristics.

### Signals and exit codes (HOST-02)

- **D-13: Handlers only in host mode.**
  - Install a `sigaction` that sets a file-static `volatile sig_atomic_t g_host_stop = sig`:
    - SIGTERM: always;
    - SIGINT and SIGHUP: unless inherited as `SIG_IGN` (the background-job and `nohup` convention).
  - Ignore SIGPIPE. Explicitly unblock TERM, INT and HUP.
  - Flags are `SA_RESTART|SA_RESETHAND`: a repeated signal takes the default action, and atomic rename protects the old file.
  - The runner is single-threaded, so a plain `volatile sig_atomic_t` is well defined. Document it as the adapter's one global; the no-hidden-globals rule targets the core.
  - The handler body is only the store (CERT SIG30-C/SIG31-C). I/O loops still handle EINTR.
- **D-14: Stopping.**
  - Poll the flag at frame boundaries. When it is set, start no new frame, run the final flush (D-11), print `gbb-host: exit status=clean reason=<sig> stopped_at_frame=K flush=written|unchanged|none`, free all memory (LSan) and exit.
  - A signal before the first frame exits 0 and writes nothing.
  - A core stop mid-run (unsupported opcode, lockup) attempts a final flush, then exits 1.
  - Print `gbb-host: ready` with `fflush` only after the handlers are installed and the ROM and save are loaded.
  - Stderr `gbb-host:` lines are diagnostics that tests use. They are not part of the host contract, which is files, exit codes and signals.
- **D-15: Host-mode exit table.**

  | Code | Name | Meaning |
  |---|---|---|
  | 0 | clean | Signal or `--frames` end; the flush succeeded or there was nothing to write. |
  | 1 | failure | I/O or flush failure (including the final flush), allocation failure, or a core stop mid-run. |
  | 2 | refusal | Refused before any save mutation: usage, unreadable or unsupported ROM, basename, symlinked or non-regular target, import out of bounds, `--save-dir` on Windows. |
  | crash | — | Death by signal (shells show 128+N). The `.sav` is the last completed flush. |

  - Host mode never emits 3 (MSVC `abort()` exits 3) or 4.
  - 77 is not used; it belongs to Playstead's continuation script (RM-020).
  - The documented table is split by mode. Acceptance-mode codes are listed separately and unchanged.
- **D-16: One machine-readable host contract.**
  - `docs/host-contract.json` is hand-written in canonical JSON form (`indent=2`, trailing newline, enforced).
  - Sections: `exit_codes`, `save_formats`, `cadence` (frames and loss windows) and `rtc_wall_clock: "not-recorded"`.
  - The X-macro header `src/host/host_exit.h` and the docs tables are checked against it by one checker. There is no help-text equality check.
  - Install the file under `share/gabbaboy/`.
- **D-17: Real-signal POSIX tests** (a Python harness run with `-I`, wired into CTest). The fixture is a synthetic SRAM-writing ROM that writes a per-frame counter.
  - **Finish-the-frame proof is a deterministic replay, not a clock.** A paced run stopped by SIGTERM reports `stopped_at_frame=K`. A fresh `--frames K` batch run in a new directory must produce a byte-identical `.sav`.
  - **Timing:**
    - Lanes without sanitizers assert the HOST-02 2.0 s ceiling from `kill()` to `waitpid` (the contract constant, a ceiling, not a quota).
    - Sanitizer lanes assert the replay check and exit 0 only, bounded by the CTest timeout, and claim nothing about 2 s.
  - **Rows:**
    - SIGTERM: exit 0.
    - SIGINT: exit 0.
    - Failure: make the save dir read-only after ready, then send SIGTERM. Expect exit 1, the old `.sav` byte-identical and no temp left. The test hard-fails when run as root.
    - Refusal: reuse the HOST-01 negatives.
    - Crash: send repeated SIGKILL during heavy flush activity (an RTC cart in batch mode, `RLIMIT_CORE=0`). The `.sav` must always be the old or the new exact-size image, and the next start must sweep the temps. A decoy that writes in place must fail.
  - **Decoys that must fail the harness:**
    - no flush on SIGTERM;
    - flush with a partial frame;
    - exit 0 after a failed flush.
  - No in-process SA_RESETHAND test. If one is wanted, query the disposition with `sigaction`.
  - No crash backdoor in any shipped binary.
- **D-18: Core no-signal check.** Extend `cmake/CheckCoreNoHostClock.cmake`; do not write a new script.
  - Add to the call and `nm` symbol deny lists: `signal|sigaction|raise|kill|sigprocmask|pthread_sigmask|alarm|setitimer`.
  - Its four-header allowlist already rejects `<signal.h>`.
  - Add one seeded control, compiled with the project's real strict-C17 flags.
  - Host files are not added to the no-host-clock check.

### Save-format ids (HOST-03)

- **D-19: Id grammar and rows.**
  - Ids follow `gabbaboy-<mapper>[-rtc]-<payload>-v<N>` and match `^gabbaboy-[a-z0-9-]{1,48}-v[1-9][0-9]*$`.
  - Ids carry no release version (Playstead matches strings exactly) and no gb/gbc axis (proven by running both profiles). Rumble is not an axis.
  - `vN` changes only when the bytes change meaning. For RTC rows, v1 is tied to GBRT block version 1.
  - Rows are keyed by (type, RAM code, ROM-code constraint). Ids are not unique per row; the rule is "same id ⇒ same bytes and layout". 16 rows, 12 distinct ids:

  | Type | RAM code | Id | Bytes |
  |---|---|---|---|
  | `$03` | `$02` | gabbaboy-mbc1-sram-8k-v1 | 8,192 |
  | `$03` | `$03` (ROM code ≤ `$04`) | gabbaboy-mbc1-sram-32k-v1 | 32,768 |
  | `$06` | `$00` | gabbaboy-mbc2-nibble-512-v1 | 512 |
  | `$0F` | `$00` | gabbaboy-mbc3-rtc-only-v1 | 21 |
  | `$10` | `$02` | gabbaboy-mbc3-rtc-sram-8k-v1 | 8,213 |
  | `$10` | `$03` | gabbaboy-mbc3-rtc-sram-32k-v1 | 32,789 |
  | `$13` | `$02` | gabbaboy-mbc3-sram-8k-v1 | 8,192 |
  | `$13` | `$03` | gabbaboy-mbc3-sram-32k-v1 | 32,768 |
  | `$1B`, `$1E` | `$02` | gabbaboy-mbc5-sram-8k-v1 | 8,192 |
  | `$1B`, `$1E` | `$03` | gabbaboy-mbc5-sram-32k-v1 | 32,768 |
  | `$1B`, `$1E` | `$05` | gabbaboy-mbc5-sram-64k-v1 | 65,536 |
  | `$1B`, `$1E` | `$04` | gabbaboy-mbc5-sram-128k-v1 | 131,072 |

  - Each row also stores `ram_bytes` and `rtc_bytes`, with the invariant `bytes == ram_bytes + rtc_bytes`.
  - Types with no battery are listed under `no_battery_types`.
  - There is no save-state row; states are release-bound (see `docs/state-format.md`).
  - Claim no interoperability with mGBA or other emulators. Correct the "non-RTC SRAM byte-identical to mGBA" sentence in `PLAYSTEAD-CONTRACT.md`: MBC2 differs, 256 vs 512 B.
  - **Reversibility:** one-way once released. Ids become a published host contract, which is why the append-only rule exists.
- **D-20: The `verify-save-formats.py` CTest.**
  - **Completeness, in process:** enumerate type × RAM code through `gbb_probe_rom` and `gbb_battery_size` in a small test binary, rather than hundreds of runner spawns. Every admitted battery combination needs a row, and every row must be admitted.
  - **Produced files:** for the 16 rows only, generate synthetic ROMs in the build directory. Each writes `$5A` to `$A000`; nothing is committed. Run `--print-save-format` and a `--frames` batch run on both profiles, then check:
    - the id and size match the JSON;
    - the `.sav` size matches;
    - SRAM byte 0 is `$5A`, or `$FA` with every byte ≥ `$F0` for MBC2;
    - RTC rows end with a `GBRT`/`0x01` block, checked structurally only (no fixed digest, because RTC bytes vary);
    - no-battery carts create no file;
    - both profiles agree.
  - **Platforms:** the file-producing leg is POSIX-only. `--print-save-format` also runs on Windows. Both inventories list the exemptions.
  - **Freeze:** compare with `git show <latest v* tag>:docs/host-contract.json`.
    - Tags present but the file absent: an explicit pass (`baseline=none`).
    - No tags available: fail.
    - One synthetic temp-repo control.
  - **Seeded controls that must fail:**
    - `$10/$03` set to 32,816;
    - a changed id;
    - a deleted row;
    - an admitted-check failure for an MBC30 `$10/$05` row;
    - a release-versioned or uppercase id;
    - `bytes ≠ ram + rtc`;
    - one id with two sizes;
    - a shim that writes a file 1 byte short;
    - a shim that reports a different id under the cgb profile;
    - a freeze mismatch;
    - non-canonical JSON;
    - a shim that creates a `.sav` for `$1A`.

### Player state slots (PLAY-01)

- **D-21: Slot model and keys (select, then act).**
  - Nine slots, 1–9. Selection starts at slot 1 on each launch and is not saved. 0 is reserved.
  - Keys:
    - **Select:** `SDL_SCANCODE_1..9` with no GUI, Ctrl or Alt modifier. Shift is allowed because Right Shift is the Select button.
    - **Save:** ⌘S.
    - **Load:** ⌘L.
    - **Undo last load:** ⌘Z, a swap.
  - Slot keys are handled before the bare R and S branches, and those branches gain a `!command` guard so ⌘S does not save the battery and ⌘R does not reset.
  - Slot keys are ignored on key repeat and while a transition, dialog or save-failure prompt is pending. They work while paused, and pause is kept across a load.
  - Decoding is a pure, unit-tested `player_slot_key_action(...)`.
  - The ⌘Z keydown is consumed; a later Z key-up must be harmless.
  - Rejected: one chord per slot. ⇧⌘3/4/5 collide with macOS screenshot shortcuts, F1 is Help, and the shift-means-save/load confusion is a known problem (SameBoy #196).
- **D-22: Storage.**
  - Slot files live under `SDL_GetPrefPath("GabbaBoy","GabbaBoy")`. File names:
    - slots: `{rom_sha256}-{dmg|cgb}-slot{N}.gbbs`;
    - undo: `{rom_sha256}-{dmg|cgb}-undo.gbbs`;
    - battery backup: `{rom_sha256}-{dmg|cgb}-battery-preload.bin`.
  - `dmg|cgb` is the profile actually created. No part of a name is user-controlled.
  - Slot and undo files hold the raw `gbb_save_state` bytes with no wrapper, because the header already carries identity and a CRC.
  - Writes use the `gabbaboy_host` dir-fd writer with the pref dir as dirfd.
  - Reads use `O_NOFOLLOW` and `S_ISREG` and read at most `gbb_state_size(live)+1` bytes; never size an allocation from `st_size`.
  - The player's existing `.gbb` battery code in `session.c` is unchanged.
- **D-23: Load sequence (all-or-nothing).**
  1. Read the slot.
  2. Snapshot the live machine in memory with `gbb_save_state`.
  3. **Battery guard:** if the live battery bytes differ from the battery recorded right after the last slot load (or this is the first load this session), atomically write them to the battery-preload file.
  4. `gbb_load_state`. On refusal, show the mapped message and stop; the instance, the battery generation and the slot, undo, preload and `.gbb` files are all untouched.
  5. On success, atomically write the snapshot to the undo file. If that fails, roll back with `gbb_load_state(snapshot)` and report.
  6. Re-anchor input (D-24), release all buttons, clear audio and force a redraw. Run no RTC catch-up and no `saved_at` re-stamp.

  Undo uses the same sequence with the undo file as its source, so pressing ⌘Z twice returns to where you were.

  The battery guard means "load A, then load B" still keeps the pre-A in-game save. The help text says: `Saving replaces the slot. Loading also replaces the game's battery save; ⌘Z undoes the last load.`
- **D-24: Add one read-only public getter for input re-anchoring.**
  - **Why it is needed:** `gbb_queue_events` admits an event only at or after both the instance time and the last queued event (`src/core/gabbaboy.c:3975-3986`). A state load restores the time and up to 64 queued events. No existing public call exposes either:
    - frame info gives only a lower bound, which stalls while the LCD is off;
    - run results are relative;
    - reset zeroes the time;
    - parsing state bytes ties the player to the format.
  - **Shape:** `gbb_error gbb_get_input_clock(const gbb_instance *, gbb_input_clock *out)`.
    - Uses the existing `struct_size` handshake.
    - Fields: `uint32_t struct_size; uint32_t queued_count; uint64_t now_half_dots; uint64_t last_queued_half_dots`, where the last field equals `now` when the queue is empty.
    - `GBB_INPUT_CLOCK_SIZE_V1 24`.
    - Read-only; outputs are unchanged on error; NULL or a short `struct_size` returns `GBB_INVALID_ARGUMENT`.
  - **Player use after a load:**
    - set the cursor and anchor to `now`;
    - seed the pending-count mirror from `queued_count`;
    - queue the releases at `max(now, last_queued)`;
    - if `last_queued - now` exceeds one frame × queue capacity, restore the snapshot and show `<Subject> contains unsafe queued input; nothing changed`.
  - **What changes:** the header, both installed C/C++ consumers, the API docs in `docs/native-integration.md`, and one core test. The state bytes, pins, tokens and perf gates are unchanged.
  - This is the only core/API change in Phase 18. Any other core change is a rescope trigger.
  - **Reversibility:** costly. It is public ABI, but additive and versioned by `struct_size`.
- **D-25: Messages.** Shown through `set_status`. While `save_status_active` is set, the status reads `<save_status> · <slot message>`. Each slot operation also writes one stderr line, including the `gbb_error` number.

  `<Subject>` is `Slot N`, or `The undo backup` when the source is the undo file.

  | Case | Message |
  |---|---|
  | Select, empty slot | `Slot N selected: empty` |
  | Select, used slot | `Slot N selected: saved YYYY-MM-DD HH:MM` (local time from mtime; `Slot N selected: saved` if stat fails) |
  | Save succeeded | `Saved slot N` |
  | Save failed | `Slot N not saved: the file could not be written` |
  | Load succeeded | `Loaded slot N (⌘Z undoes)` |
  | Missing file | `Slot N is empty; nothing changed` |
  | `GBB_STATE_IDENTITY_MISMATCH` | `<Subject> is from a different game or model; nothing changed` |
  | `GBB_STATE_UNSUPPORTED_VERSION` | `<Subject> is from another GabbaBoy version; nothing changed` |
  | `GBB_STATE_BAD_FORMAT` | `<Subject> is not a GabbaBoy state; nothing changed` |
  | `GBB_STATE_SIZE_MISMATCH`, `GBB_STATE_CORRUPT`, `GBB_STATE_INVALID_CONTENT` | `<Subject> is damaged; nothing changed` |
  | Any other error | `<Subject> could not be loaded; nothing changed` |
  | Open, read or allocation failure, symlink | `<Subject> could not be read; nothing changed` |
  | Undo backup write failed | `Slot N not loaded: undo backup failed; nothing changed` |
  | Undo succeeded | `Undid the last load (⌘Z switches back)` |
  | No undo file | `Nothing to undo` |
  | Unsafe queued input | `<Subject> contains unsafe queued input; nothing changed` |

  - **Limitation:** the window title is hidden in fullscreen and VoiceOver does not announce it.
  - **Limitation:** every release refuses older slots, because states carry the exact release triplet.
- **D-26: Slot tests.**
  - **Where they run:**
    - Slot file I/O, the load/undo/backup sequence and the error→message mapping live in SDL-free `src/player/slots.c`. Their portable CTest runs in the main inventory, including Linux ASan.
    - Key decoding and event-pump behaviour run in the macOS player suite through the real event pump, with `player_session_test_set_pref_path` and an isolated `HOME`/`CFFIXED_USER_HOME`.
  - **Required tests:**
    1. **Round trip:** the bytes of a saved slot equal the post-load `gbb_save_state`.
    2. **Wrong-ROM control:** these are all byte-identical before and after the refusal:
       - `gbb_save_state`;
       - `gbb_copy_battery`;
       - the generation;
       - the SHA-256 of the slot, undo, preload and `.gbb` files.
    3. **The same refusal assertions for each generated refusal:**
       - a DMG state in a cgb slot;
       - a patched version token with a recomputed CRC;
       - a text file;
       - a flipped body byte;
       - a truncated file;
       - a file of size+4096;
       - a symlinked slot.

       No committed state bytes: they embed the release token and go stale at Phase 19.
    4. **Undo-write failure:** rolls back to byte-identical.
    5. **Undo swap:** pressing ⌘Z twice restores.
    6. **Battery guard:** load A, then load B, then check that the preload file still holds the pre-A battery.
    7. **Input re-anchor:** after loading a later-time state and after loading an earlier-time state, a key press is accepted and reaches the guest within one frame. A mutant without the rebase must fail.
    8. **Unsafe queued input:** a slot whose queued event is far in the future is refused.
    9. **Key decoder:** ⌘S does not save the battery; ⌘R does not reset; keys are ignored during transitions and on repeat.
    10. **Message table:** iterates every `GBB_STATE_*` code and asserts the exact strings. A mutant that maps a code wrongly must fail.
    11. **Order mutant:** writing the undo file before `gbb_load_state` must fail the "refusal touches no files" check.
  - No UI-SPEC: the UI is a status line, and this key and message table is its contract.

### Cross-cutting

- **D-27: Branch and release hygiene.**
  - Phase 18 branches from `main` after PR130 is squash-merged with exact-head checks green. Phase 17's boundary SHA goes in `continue.md`/STATE only.
  - The v0.3.0 release-please PR stays unmerged throughout Phase 18. There is no VERSION bump: a bump would expire the RM-027 ledger rows and change the state release token.
  - No edits to `release.yml` or `release-rehearsal.yml`, no new workflow jobs and no job-timeout edits.
  - New tests use the base 60 s TIMEOUT, with no allowlist rows and the ASan ×3 factor.
  - At the phase tail, check that no hosted test is above about 75% of its budget (GB-CI-012).
  - Plans that edit the same inventory file run serially (GB-CART-003).
- **D-28: Installed and package evidence.** Add an installed host-mode smoke CTest on Linux and macOS: a relocated prefix, an unrelated cwd, a temp save dir, and a two-process continuation with a game-visible readback (XFER-002). Phase 19 binds it as a receipt.
- **D-29: Docs, updated together, each with a contract check.**
  - `README.md`: host-mode usage, and "headless, not a play surface".
  - `docs/native-integration.md`, a "Host process contract" section covering:
    - flags and naming;
    - atomicity scope;
    - cadence and loss windows;
    - the exit table, split by mode;
    - signals;
    - the Windows refusal;
    - no RTC catch-up;
    - the single writer;
    - the getter.
  - `docs/cartridge-and-saves.md`:
    - raw `.sav` vs the player's `.gbb`;
    - slots;
    - a load replacing the battery save, and the preload backup.
  - Player help text and `src/player/limitations.h`.
  - `docs/support/unreleased.md` entries, with destination v0.3.0.
  - Docs tables are generated from or checked against `docs/host-contract.json`.
  - `CHANGELOG.md` is left to release-please. `docs/support/v0.3.0.md` is Phase 19's.
- **D-30: No new fuzz target.** Core battery import is already fuzzed. Host-side reads get a hostile-file sweep instead: sizes 0, N−1, N, N+1 and 8 MiB+1, plus a FIFO, a directory, a device and a symlink. Each negative asserts its own specific reason (GB-GSD-029).
- **D-31: Plan shape** (≤9 primary plus 1 gap; target 8).

  | Wave | Plan | Requirements | Scope |
  |---|---|---|---|
  | W1 | 18-01 host tracer | HOST-01 | `gabbaboy_host` library skeleton; runner host-mode dispatch and grammar; bounded ROM reader; import; batch `--frames` with final flush; two-process continuation; Windows refusal; dirty-list and API-symbol checks |
  | W1 (parallel) | 18-02 input-clock getter | PLAY-01 | Getter, consumers, API docs. Touches only core, header and consumer files. |
  | W2 | 18-03 host file safety and cadence | HOST-01 | D-06..D-11, D-30 |
  | W2 (parallel, if inventories are disjoint) | 18-04 slot engine | PLAY-01 | `slots.c`: load, undo, battery guard, re-anchor, messages, portable CTest |
  | W3 | 18-05 player slot integration | PLAY-01 | Keys, event pump, help text, limitations, macOS suite |
  | W3 | 18-06 signals and exit table | HOST-02 | Including the core no-signal check |
  | W4 | 18-07 host contract JSON and save-format CTest | HOST-03 | |
  | W5 | 18-08 installed smoke and docs | all | Installed smoke and docs contract checks |

  The gap slot is reserved. A 50% overrun means rescope.

### Claude's Discretion
- Exact file and function names inside `src/host/` and `src/player/slots.c`, and the CMake target layout.
- Exact stderr `gbb-host:` wording, apart from the `ready` and `exit … stopped_at_frame=K` fields the tests rely on.
- Synthetic fixture ROM layout, as long as it is original, generated at test time and redistributable.
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Scope and requirements
- `.planning/ROADMAP.md` "### Phase 18": goal, success criteria 1–4, plan cap 10.
- `.planning/REQUIREMENTS.md`: PLAY-01 and HOST-01..03 (lines ~70–90).
- `.planning/context/DECISIONS.md` D-104: INT-01a/INT-01b split; RM-020/021/009 parked.
- `.planning/context/DECISIONS.md` D-102..D-105, D-112, D-113: convergence limits and Phase 17 compatibility rules.
- `AGENTS.md`: engineering rules, automated verification, phase stop.

### Consumer contract and research
- `.planning/research/v0.3/PLAYSTEAD-CONTRACT.md`: pin shape, save_contract, restore gate, SIGTERM→SIGKILL ~2 s, mGBA ids and sizes. Its MBC2 byte-identity claim needs correcting (D-19).
- `.planning/research/v0.3/SUMMARY.md` and `ADVERSARIAL-REVIEW.md`: Phase 18 scope line.
- `.planning/research/v0.3/SIBLING-NESTURBATOR-MUHTARI.md` (~290–330) and `SIBLING-YOUNGER-CORES.md` (~190–210): sibling host contracts and the real-signal EINTR lesson.
- `.planning/research/v0.3/SAVE-STATES.md`: player-slot notes; `gbb_probe_state` remains deferred.

### State and battery API
- `include/gabbaboy/gabbaboy.h`:
  - state calls (lines 187–190);
  - battery API and `GBB_RTC_BLOCK_SIZE` (lines 192–227);
  - `gbb_queue_events` (line 268);
  - `gbb_get_info` struct_size pattern (line 396).
- `docs/state-format.md`: header, release-triplet binding, field table (time and queue fields).
- `docs/cartridge-and-saves.md`: battery images, RTC projection, state-load semantics, player `.gbb` format (lines ~130–330).
- `.planning/phases/GB-17-native-save-state-core/17-CONTEXT.md`: D-01..D-07 compatibility and API contract.
- `.planning/phases/GB-17-native-save-state-core/17-REVIEW-DISPOSITION.md`: deferred items (not Phase 18 scope).
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/player/session.c` `atomic_save` (~842–917), `read_save_file` (~460) and `sync_save_directory`: patterns to copy (EINTR loops, re-fstat identity, fault stages). They stay macOS-only and unchanged.
- `src/player/session.c` `player_session_test_set_pref_path` and the fault-stage seams: slot test isolation.
- `cmake/CheckCoreNoHostClock.cmake`: an `nm` plus source denylist with two negative controls. Extend it for signals.
- `tests/test_battery.c` `make_rom`: synthetic header ROM generation for the HOST-03 fixtures.
- The existing original continuation fixtures for MBC1, MBC2, MBC3+RTC and MBC5, and `installed_runner_smoke` (`tests/CMakeLists.txt` ~1873).
- `tests/scripts/verify-uat-closure.py` and the summary coverage schema for verify-work.

### Established Patterns
- The `struct_size` handshake (`gbb_info`, `GBB_INFO_SIZE_V1`): use it for the new getter.
- The runner uses `C_EXTENSIONS OFF` and strict C17, so define the POSIX feature macros per file.
- Checkers live in `tests/scripts/`, read an immutable commit, are wired into CTest when created, and each has a `--self-test` or `WILL_FAIL` negative control.
- The player suite runs only in macOS `macos-player-package` on PRs, without ASan, so put portable logic in SDL-free files.

### Integration Points
- `src/runner/main.c`:
  - host dispatch before line 451 (`argc==2` tracer) and before acceptance parsing;
  - the `MAX_ROM 32768u` cap does not apply to host mode.
- `CMakeLists.txt`:
  - lines 69–70: the runner target;
  - lines 85–87: the `GBB_BUILD_QUALIFIED` dirty list;
  - lines 101–121: the optional player;
  - install rules for `share/gabbaboy/host-contract.json`.
- `src/player/main.c`:
  - `handle_key` (~1357–1430);
  - status and title (~766–791);
  - help (~807).
- `src/player/input.c` (~38–131): cursor and pending mirror, for re-anchoring.
- `src/core/gabbaboy.c`:
  - `gbb_queue_events` (~3969–3994);
  - queue fields in the state codec (~941–947, 4676–4686);
  - battery generation on load (~4853–4859).
- `tests/CMakeLists.txt` (~2898–2903): the partial-inventory and Windows exemption path.
- `cmake/ExpectedTests.cmake` and `tests/scripts/verify-test-inventory.sh`: inventory lists.
</code_context>

<specifics>
## Specific Ideas

- The flagship check is MBC3+RTC with 32 KiB of RAM: exactly 32,789 B, id `gabbaboy-mbc3-rtc-sram-32k-v1`. The mGBA 32,816 B footer file must be refused.
- Playstead derives `romBaseName` from `deletingPathExtension` (`SaveSessionCoordinator.swift:16-18`). The basename rule must give the same stem.
- Precedent for the signal mechanics is Dolphin NoGUI's `SA_RESTART|SA_RESETHAND` on SIGINT and SIGTERM. Nesturbator's real-signal tests found an EINTR abort that a simulated stop missed.
- Keys follow RetroArch's select-then-act model. mGBA has an undo-load precedent (F11).
</specifics>

<deferred>
## Deferred Ideas

- **Live host play:** player host mode and Playstead live play reuse `gabbaboy_host`. They are RM-020, together with the AdapterPin JSON and the continuation protocol (`qualify`/`initial-run`/`continue`, 0/77/1).
- **Interop and libretro:** mGBA/BGB RTC footer import and export (RM-021); libretro (RM-009); BESS (RM-022).
- **Slot extras:** rewind, run-ahead, slot thumbnails, state sync, `gbb_probe_state` for slot browsers.
- **New RM/LIM candidates:**
  - host-mode RTC wall-clock catch-up (host-supplied elapsed time or a sidecar);
  - a Windows host mode;
  - a power-loss durability claim;
  - advisory save-dir locking;
  - player SIGTERM save-and-exit;
  - DMG/.app packaging of the runner for Playstead;
  - fullscreen and VoiceOver announcement of slot status.
- **Seed:** converge the player's `.gbb` `atomic_save` with the `gabbaboy_host` writer.
- **Phase 19 entry items, not pulled in:**
  - WR-C03 `report-red` re-citation;
  - the RM-027 citations;
  - the `candidate-performance` re-citation;
  - `docs/support/v0.3.0.md`;
  - the VERSION bump.
- **Other open items:** WR-C04, WR-A05 and IN-01..08 from the Phase 17 review wait for the owner to schedule them.
</deferred>

---

*Phase: 18-player-save-slots-and-host-contract*
*Context gathered: 2026-10-28*
