# Phase 18: Player Save Slots and Host Contract - Research

**Researched:** 2026-10-28
**Domain:** Portable-C emulator host adapters: POSIX atomic file persistence, signal-driven save-and-exit, a machine-readable save-format table, and SDL player state slots over the Phase 17 public API.
**Confidence:** HIGH (decisions are locked in CONTEXT; every code fact below was read this session; POSIX behaviour was probed on macOS and Linux/glibc)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

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

### Deferred Ideas (OUT OF SCOPE)

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
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| PLAY-01 | The SDL player saves and loads numbered state slots through the public API only. | `gbb_state_size/save_state/load_state` refusal codes verified (see Verified Code Facts F1). The input-clock getter (D-24) is required because `gbb_queue_events` rejects events earlier than instance time or the last queued event (F6). Slot engine is SDL-free (`src/player/slots.c`) so its tests run in the portable inventory and Linux ASan; key decoding runs in the embedded-`main.c` macOS player suite (Pattern 6, 7). |
| HOST-01 | Runner mode `--rom <path> --save-dir <dir>` writes battery saves as raw `{saveDir}/{romBaseName}.sav`. | Dir-fd `openat/renameat` writer, O_NOFOLLOW import, strict basename validation (Patterns 1-3). Probes show a dangling symlink opens with `ELOOP`, never `ENOENT` (Pattern 2), so "ENOENT means fresh" is safe. |
| HOST-02 | On SIGTERM the runner finishes the current frame, flushes, exits 0 well within 2 s. | Flag-poll at frame boundaries; `nanosleep` returns `EINTR` even with `SA_RESTART` (Pattern 4); Python real-signal harness with deterministic replay proof (Pattern 4, 8). |
| HOST-03 | GabbaBoy-declared save-format ids and byte sizes per cartridge kind (MBC3+RTC is 32,789 B), machine-readable, CTest-checked against produced files. | 32,789 B verified in code (F3); the 16 admitted battery rows verified against `cart_type_table` and `validate_header` (F4); completeness enumerates `gbb_probe_rom` + `gbb_battery_size` (Pattern 9). |
</phase_requirements>

## Summary

All four requirements are implementable with the locked D-01..D-31 design and **no new dependencies**: C17, POSIX.1-2008 (`openat`, `renameat`, `fstatat`, `unlinkat`, `sigaction`, `nanosleep`), the already pinned SDL3 3.4.18 for the player, CMake (floor 3.25) and Python stdlib run with `-I`. I confirmed on this Mac (Apple clang, `-std=c17 -pedantic`, `_POSIX_C_SOURCE 200809L` + `_DARWIN_C_SOURCE`) and in a `gcc:13` Linux container (strict `-std=c17`, only `_POSIX_C_SOURCE 200809L`) that every call, flag and macro the design needs compiles (`O_DIRECTORY`, `O_NOFOLLOW`, `O_CLOEXEC`, `SA_RESTART|SA_RESETHAND`, `renameat`, `fstatat`, `clock_gettime`), that macOS lacks `clock_nanosleep` (so D-03's relative `nanosleep` is forced), and that the dangling-symlink / FIFO behaviours D-08 depends on hold on both platforms.

The risk in this phase is **not the POSIX mechanics**; it is test-suite plumbing and plan sequencing. Five things will bite a planner who follows D-31 literally: (1) the "parallel" plan pairs 18-01‖18-02 and 18-03‖18-04 all append to the same `tests/expected-tests.txt` and `tests/CMakeLists.txt`, which GB-CART-003 says must be serial; (2) the D-09 atomic writer is needed by the 18-01 tracer (final flush) but hardened in 18-03, so the writer's API must be frozen in 18-01; (3) Debug-build emulation costs about 3-4 ms per frame, so any end-to-end test that waits for the 3,600-frame RTC cadence takes 11-14 s plain and about 3x that under ASan, which breaks GB-CI-012 (stay under about 75% of 60 s); cadence must therefore be a pure, unit-tested function; (4) the HOST-01/03 "game-visible readback" can be done with an SRAM counter fixture and the persisted `.sav` bytes, with no new runner flag; (5) the player's `limitations.h` text is pinned byte-for-byte by `tests/player/test_limitations.c` and referenced by several checkers, so editing it is a multi-file change.

**Primary recommendation:** Build `gabbaboy_host` as a core-less static library (include dirs only, so `verify-core-linkage.py` is unaffected), freeze `host_save_io_replace(dirfd, name, bytes, len)` in 18-01, express cadence/exit/format tables as pure functions or X-macro data tested without wall clock, serialize every plan that edits the two test inventories, and give every deliverable a negative control that fails for its own named reason.

## Project Constraints (from AGENTS.md)

- Original portable C core, explicit ownership/error behaviour, bounded public operations, **no hidden globals** in the core; host timing, filesystem, UI and environment stay in adapters. (The single `volatile sig_atomic_t` is an adapter global, D-13.)
- Guard ROM/save/state boundaries against overflow, truncation, excess allocation/work and **partial mutation**; explicit portable serialization, never raw struct dumps.
- Automated verification shifted left (D-069): every deliverable has an automated check **with a negative control**; `/gsd-verify-work` must need zero human checkpoints. Plan SUMMARY `coverage:` entries use the GSD block schema (`id`, `description`, `human_judgment`, block-style `verification` items with `kind` unit/integration/e2e/automated_ui/other, `ref`, `status: pass`; no `{...}` flow items, no `ctest` kind, no inline `#` comments). Closure via `tests/scripts/verify-uat-closure.py <phase-dir> --write <evidence> | --self-test`.
- D-102-D-105: <= 12 plans per phase (cap 10 here), <= 2 review-fix rounds, <= 1 gap round; unresolved correctness/security finding forces a rescope. No quotas/clocks/run counters as evidence. Checkers live in `tests/scripts/`, read an immutable commit, are wired into CTest when created.
- Stop after the phase; never auto-advance; `workflow.auto_advance` and `workflow._auto_chain_active` stay false.
- No Nintendo boot ROMs, commercial/unlicensed images or private data; every third-party fixture needs documented rights and a digest. (All Phase 18 fixtures are original and generated at test time.)
- No personal home paths, emails or machine identifiers in public artifacts (so `gbb-host:` stderr lines and docs must not print absolute user paths into committed receipts).
- Update source, API docs, examples, tests and limitation notes together; keep main releasable.
- Memory (user): prefer inlining small code over new dependencies/actions; squash-merge phase PRs on exact-head green; automate verification, zero UAT.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| State save/load, battery export/import, input clock read | Core (public API, `gabbaboy.c`) | - | Pure functions of instance state; no filesystem or signals (D-18 enforces). Only `gbb_get_input_clock` is added (D-24). |
| Basename rule, dir-fd atomic writer, bounded reader/import, cadence, exit table, signal flag, save-format lookup | `gabbaboy_host` (SDL-free, public-API-only static lib) | Runner, Player slot code | Single reusable contract module (D-01); reused unchanged by RM-020 later. |
| Host-mode CLI grammar, frame loop, pacing, `ready`/exit lines | Runner adapter (`src/runner/main.c` dispatch + `src/host/`) | - | Headless conformance adapter; owns process lifecycle. |
| Slot engine (file I/O, load/undo/battery-guard sequence, error-to-message map, re-anchor) | Player adapter, SDL-free (`src/player/slots.c`) | `gabbaboy_host` writer | Must be portable-testable without SDL (player suite is macOS-only, no ASan). |
| Key decoding, status line, help text, event pump | Player adapter (`src/player/main.c`, SDL) | - | Only place SDL events exist; thin over `slots.c`. |
| Save-format ids and sizes (declaration) | `docs/host-contract.json` (data) | `src/host/` table | JSON is the contract; C table + X-macros are checked against it. |
| Conformance checking | CI tooling (`tests/scripts/*.py`, `cmake/*.cmake`, CTest) | - | Checkers read immutable commits and carry negative controls. |
| Durability / atomicity | OS filesystem (POSIX `rename` + `fsync`) | Writer | Claim is old-or-new atomicity against process death only (D-10). |
| Signal delivery | OS | Runner adapter flag | Handler body is only the `sig_atomic_t` store (D-13). |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| C17 + POSIX.1-2008 | `-std=c17`, `C_EXTENSIONS OFF`, `_POSIX_C_SOURCE 200809L` (+`_DARWIN_C_SOURCE` on Apple) | Host and slot code | Project convention; probed OK on Apple clang 21 and gcc 13 (Pitfall 4). |
| SDL3 | 3.4.18 EXACT (`find_package(SDL3 3.4.18 EXACT CONFIG REQUIRED)`, `CMakeLists.txt:` player block) | Player only; `SDL_GetPrefPath("GabbaBoy","GabbaBoy")` for slot directory | Already pinned; the slot engine does not link it. |
| CMake | floor 3.25; local 4.4.3 | Targets, CTest, `-P` checks | Existing; `cmake-floor-3-25-3` CI job. |
| Python 3 stdlib (`-I`) | write for >= 3.9; local 3.14.4 | Signal harness, `verify-save-formats.py`, contract checker | Existing checkers are stdlib-only and run `python3 -I`. [ASSUMED: CI ubuntu-22.04 ships Python 3.10, so avoid 3.11+ only features] |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `gabbaboy_accept_bare` `sha256.c` | in-repo | ROM SHA-256 for slot file names (player already holds `rom_sha256` in `player_save_identity`) | Reuse; do not add a hash dependency. |
| `tests/expect_exit.cmake` | in-repo | Exact exit code + regex + `KEY=<digits>` minimum for CLI negatives | Wrap every negative-control CTest. |
| `cmake/VerifyDocContract.cmake` | in-repo | Every `gbb_*`/`GBB_*` identifier in a guide must be declared in the header; required phrases present | Docs plan (18-08). |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Relative `nanosleep` + deadline correction | `clock_nanosleep(TIMER_ABSTIME)` | Not declared on macOS (probe: "call to undeclared function 'clock_nanosleep'"), so rejected (D-03). |
| `volatile sig_atomic_t` flag poll | `signalfd`/self-pipe/`sigwait` thread | Linux-only or adds threads; single-threaded flag is the minimal portable form (D-13). |
| Hand-written canonical JSON | A JSON library | None needed; Python `json` checks canonical form; C reads no JSON. |

**Installation:** none. No package is added to any ecosystem.

**Version verification:** `cmake --version` 4.4.3, `python3 --version` 3.14.4, `cc --version` Apple clang 21.0.0, `ninja --version` 1.13.2, Docker 29.5.2 with `gcc:13` (used only for the Linux probes). SDL3 is already pinned and unchanged by this phase.

## Package Legitimacy Audit

No external packages are installed or recommended by this phase (C/POSIX/CMake/Python stdlib only; SDL3 3.4.18 is an existing pin). The `package-legitimacy` gate is therefore not applicable.

**Packages removed due to [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

## Verified Code Facts

Values here were read from source this session; quotes are verbatim.

| # | Fact | Source (opened with Read/sed this session) | Verbatim quote |
|---|------|---------|----------------|
| F1 | State refusal codes (note the explicit `= 21`..`27`; `GBB_STATE_NO_ROM` has no row in the D-25 message table so it falls under "Any other error") | `include/gabbaboy/gabbaboy.h:42-48` | `GBB_STATE_NO_ROM = 21,` `GBB_STATE_BAD_FORMAT = 22,` `GBB_STATE_UNSUPPORTED_VERSION = 23,` `GBB_STATE_IDENTITY_MISMATCH = 24,` `GBB_STATE_SIZE_MISMATCH = 25,` `GBB_STATE_CORRUPT = 26,` `GBB_STATE_INVALID_CONTENT = 27` |
| F2 | `gbb_load_state` validation order (decides which message a generated refusal shows) | `src/core/gabbaboy.c:4913-4945` | size `< GBB_STATE_HEADER_BYTES` or `"GBBS"` mismatch -> `GBB_STATE_BAD_FORMAT`; version/release/behaviour mismatch -> `GBB_STATE_UNSUPPORTED_VERSION`; `bytes[16] != instance->profile \|\| bytes[17] != instance->exec_mode \|\| memcmp(bytes + 20u, instance->rom_sha256, ...)` -> `GBB_STATE_IDENTITY_MISMATCH`; length fields -> `GBB_STATE_SIZE_MISMATCH`; CRC -> `GBB_STATE_CORRUPT`; reserved bytes / `state_validate` -> `GBB_STATE_INVALID_CONTENT`; only then `state_apply`. Overlap of `bytes` with the instance returns `GBB_INVALID_ARGUMENT`. |
| F3 | RTC image size | `src/core/gabbaboy.c:5468-5471`; `gabbaboy.h:220` | `return instance->cartridge_ram_size +` `(instance->cart.has_timer ? (size_t)GBB_RTC_BLOCK_SIZE : 0u);` and `#define GBB_RTC_BLOCK_SIZE 21u`. 32,768 + 21 = **32,789**. |
| F4 | Battery-bearing cartridge rows (type, mapper, window, battery, timer, rumble, max ROM code, RAM rule) | `src/core/gabbaboy.c:265-284` | `{ 0x03u, CART_MBC1, 1u, 1u, 0u, 0u, 0x06u, CART_RAM_8K_OR_32K, 0x04u, ...}`, `{ 0x06u, CART_MBC2, 1u, 1u, 0u, 0u, 0x03u, CART_RAM_MBC2, ...}`, `{ 0x0Fu, CART_MBC3, 1u, 1u, 1u, 0u, 0x07u, CART_RAM_NONE, ...}`, `{ 0x10u, CART_MBC3, 1u, 1u, 1u, 0u, 0x07u, CART_RAM_MBC3, ...}`, `{ 0x13u, CART_MBC3, 1u, 1u, 0u, 0u, 0x07u, CART_RAM_MBC3, ...}`, `{ 0x1Bu, CART_MBC5, 1u, 1u, 0u, 0u, 0x08u, CART_RAM_MBC5, ...}`, `{ 0x1Eu, CART_MBC5, 1u, 1u, 0u, 1u, 0x08u, CART_RAM_MBC5, ...}`. All other rows have battery `0u`. This is exactly the 7 types behind the D-19 rows (2+1+1+2+2+4+4 = 16). |
| F5 | RAM-size rules per rule (basis for the 16 rows and for rejecting `$10/$05`) | `src/core/gabbaboy.c:5225-5254` | MBC1: `ram_size_code == 0x02u` -> 8192, `0x03u && rom_size_code <= row->ram32_max_rom_code` -> 32768, else `GBB_UNSUPPORTED_RAM_SIZE`; MBC3: `case 0x02u: ram_size = 8192u;` `case 0x03u: ram_size = 32768u;` `case 0x05u: mbc30_ram_marker = 1;` (later `GBB_UNSUPPORTED_CARTRIDGE_VARIANT`); MBC5: `0x02u`/`0x03u`/`0x05u`/`0x04u` = 8192/32768/65536/131072; MBC2: `ram_size = MBC2_RAM_BYTES;` (`#define MBC2_RAM_BYTES 512u`). |
| F6 | Why a getter is needed | `src/core/gabbaboy.c:3969-3994` | `event->at_half_dots < instance->time_half_dots \|\| event->at_half_dots < previous` -> `return GBB_INVALID_EVENT;` where `previous` starts at `instance->time_half_dots` and becomes the last queued event's `at_half_dots`; `#define GBB_INPUT_EVENT_CAPACITY 64u` is core-private (`gabbaboy.c:128`), so the player must use its own `PLAYER_INPUT_QUEUE_CAPACITY 64u` (`src/player/input.h:12`). |
| F7 | `GBB_MAX_ROM_SIZE` is core-private; host mode needs its own constant | `src/core/gabbaboy.c:204` | `#define GBB_MAX_ROM_SIZE ((size_t)8u * 1024u * 1024u)`; `grep` over `include/`, `src/runner`, `src/player`, `src/accept` finds no occurrence. |
| F8 | Runner dispatch point (CONTEXT says 451; it is now line **455**) | `src/runner/main.c:455` | `if(argc==2&&strncmp(argv[1],"--",2)!=0)return run_original_tracer(argv[1]);` Runner already includes `"../core/gabbaboy_test.h"` and `MAX_ROM 32768u`; host code must live in `src/host/`, not in `main.c`. |
| F9 | Dirty list for `GBB_BUILD_QUALIFIED` | `CMakeLists.txt:84-87` | `git diff --quiet HEAD -- CMakeLists.txt include/gabbaboy/gabbaboy.h src/core/gabbaboy.c src/core/gabbaboy_test.h src/runner/main.c src/runner/acceptance.h src/runner/cases.c src/runner/acceptance.c src/accept/gbb_accept.h src/accept/sha256.c ...` |
| F10 | Frame stop reasons the host loop must treat as normal | probe against `build/libgabbaboy_core.a` (this session) | `di; halt` and `di; stop` ROMs: `reason=6 consumed=48` (first call) then `reason=6 consumed=140448`; `reason=7 consumed=48` then `consumed=140448`. `GBB_STOP_HALTED_IDLE` and `GBB_STOP_STOPPED` are normal, not failures. |
| F11 | Playstead stem derivation | `~/projects/playstead/playstead-mac/Playstead/Saves/SaveSessionCoordinator.swift:17` | `let base = URL(fileURLWithPath: romFileName).deletingPathExtension().lastPathComponent` |
| F12 | Core already free of signal calls | `grep -nE "(^\|[^A-Za-z0-9_])(signal\|sigaction\|raise\|kill\|sigprocmask\|pthread_sigmask\|alarm\|setitimer)[ \t]*\(" src/core/*.c src/core/*.h include/gabbaboy/gabbaboy.h` | no output. The D-18 deny-list extension will not false-positive on the current core. |
| F13 | Existing deny-list/allowlist shape to extend | `cmake/CheckCoreNoHostClock.cmake:41-62` | `set(gbb_allowed_includes "<stddef.h>" "<stdint.h>" "<stdlib.h>" "<string.h>" ...)`, `set(gbb_denied_calls time clock clock_gettime ...)`, `set(gbb_denied_symbols time _time32 ...)`. Controls are `no_host_clock_selftest`, `no_host_clock_symbol_selftest`, `no_host_clock_comment_selftest` (`tests/CMakeLists.txt:2374-2415`). |
| F14 | Limitations text is pinned | `tests/player/test_limitations.c`; `tests/scripts/verify-phase8-player-contract.py:129-210` | `test_limitations.c` does `strcmp(GBB_PLAYER_LIMITATIONS_TEXT, expected)` against a full literal; the phase8 checker reads both files. `tests/player/claims_agree.cmake` requires listed phrases in `limitations.h`, README and `preview.yml`. |
| F15 | Hosted CI runs ctest 4-wide and with full history | `.github/workflows/ci.yml:78,229,318` (comment text "every ctest call runs 4 at once"); `fetch-depth: 0` on the native jobs | Timing tests must not assume an idle machine; the freeze check's `git show <tag>:path` works because tags are fetched. Local tags: `v0.1.0 v0.1.2 v0.2 v0.2.0 v0.2.1` (note the stray `v0.2`). |

## Architecture Patterns

### System Architecture Diagram

```
                           host process (Playstead / test harness)
                                    |  spawns, SIGTERM/SIGINT/SIGKILL, reads exit code + files
                                    v
 argv --> [runner main.c: host-mode dispatch (before argc==2 tracer, before acceptance parse)]
              |  grammar errors / Windows --save-dir / bad ROM -> exit 2 (no fs access)
              v
        [gabbaboy_host]  parse ROM (own 8 MiB reader) -> gbb_probe_rom/gbb_load_rom
              |             open save dir ONCE: O_RDONLY|O_DIRECTORY|O_CLOEXEC  --> dirfd
              |             basename validate (refuse, never rewrite)
              |             gbb_battery_size -> want; openat(O_NOFOLLOW|O_NONBLOCK) -> fstat/read/fstat
              |             import refusal => exit 2 BEFORE first frame; stale-temp sweep
              |             install sigaction (TERM always; INT/HUP unless SIG_IGN); ignore SIGPIPE
              |             print "gbb-host: ready"  (flush)
              v
   +---> frame loop:  gbb_run(140448 half-dots)  == 1 "frame"
   |        |  stop reason in {BUDGET, HALTED_IDLE, STOPPED} -> continue; else final flush, exit 1
   |        |  cadence (pure fn): generation changed? 16 quiet / 300 old ; every 3600 export-and-compare
   |        |  pacing (paced mode): relative nanosleep to a CLOCK_MONOTONIC deadline; EINTR wakes
   |        |  poll g_host_stop (volatile sig_atomic_t) at the frame boundary
   |        v
   +--  stop? --no--> loop            --yes--> final flush -> "gbb-host: exit status=clean ..." -> free -> exit 0
                                                    |
                          save_io_replace(dirfd, name, bytes, len):
                          openat(.<stem>.sav.tmp-<pid>-<seq>, O_EXCL|O_NOFOLLOW) -> write loop -> fsync/F_FULLFSYNC
                          -> close -> fstatat(target, NOFOLLOW): absent or S_ISREG -> renameat -> fsync(dirfd)

 Player (macOS, SDL):  key -> player_slot_key_action() -> slots.c: read slot (O_NOFOLLOW, S_ISREG, <= size+1)
                       -> snapshot live (gbb_save_state) -> battery guard (atomic preload write)
                       -> gbb_load_state (refusal => stop, nothing touched) -> atomic undo write (fail => roll back)
                       -> gbb_get_input_clock -> re-anchor input, release buttons, clear audio, redraw -> set_status
```

### Recommended Project Structure
```
src/host/
├── host_basename.c/.h     # stem rule + strict UTF-8 validator (pure, no fs)
├── host_save_io.c/.h      # dirfd open, save_io_replace, bounded read/import, stale-temp sweep (POSIX; _WIN32 stubs)
├── host_cadence.c/.h      # pure step function: (frame, generation, last_flushed, ...) -> action
├── host_exit.h            # X-macro: code, name, meaning (checked against docs/host-contract.json)
├── host_signal.c/.h       # sigaction install, g_host_stop, pacing helper (POSIX; _WIN32 stubs)
├── host_save_format.c/.h  # (type, ram code, rom code) -> id, bytes, ram_bytes, rtc_bytes
└── host_run.c/.h          # frame loop, ready/exit lines; main.c only dispatches
src/player/slots.c/.h      # SDL-free slot engine (D-23), links gabbaboy_host
docs/host-contract.json    # canonical, hand-written (D-16)
tests/scripts/verify-host-contract.py      # JSON canonical form + X-macro + docs tables
tests/scripts/verify-save-formats.py       # D-20
tests/scripts/test_host_signals.py         # D-17 real-signal harness (python3 -I)
tests/test_host_*.c, tests/test_slots.c    # unit/portable tests
cmake/CheckHostApiSymbols.cmake            # undefined gbb_* symbols vs public header (D-04)
cmake/CheckRunnerSourcesQualified.cmake    # runner/host SOURCES subset of dirty list (D-04)
```
Every new `.c/.h` above joins the `GBB_BUILD_QUALIFIED` list at `CMakeLists.txt:85-87` (F9).

### Pattern 1: Dir-fd atomic writer (D-09) - freeze the API in 18-01
**What:** One function, `save_io_replace(int dirfd, const char *name, const uint8_t *bytes, size_t len)`, used by the runner final/periodic flush **and** the player's slot/undo/preload writes.
**When:** Every persisted artifact of this phase. The 18-01 tracer needs it for its final flush, so 18-01 lands the full signature and the straight-line sequence (O_EXCL temp, write loop, `F_FULLFSYNC`/`fsync`, checked `close`, target check, `renameat`, `fsync(dirfd)`); 18-03 adds fault-injection seams, the `seq` retry, the stale-temp sweep and the negative suite.
**Example:**
```c
/* Source: 18-CONTEXT D-09; flag set probed on macOS (Apple clang 21) and gcc:13 */
#define _POSIX_C_SOURCE 200809L
#ifdef __APPLE__
#define _DARWIN_C_SOURCE
#endif
#include <fcntl.h>
#include <sys/stat.h>
#include <unistd.h>

static int sync_file(int fd) {
#ifdef F_FULLFSYNC
    if (fcntl(fd, F_FULLFSYNC) == 0) return 0;
    if (errno != ENOTSUP && errno != ENOTTY && errno != EINVAL) return -1;
#endif
    return fsync(fd);               /* on EIO the caller discards this temp and rewrites from memory */
}
/* temp: openat(dirfd, tmp, O_WRONLY|O_CREAT|O_EXCL|O_NOFOLLOW|O_CLOEXEC, 0600); EEXIST -> bump seq (<=16) */
/* target: fstatat(dirfd, name, &st, AT_SYMLINK_NOFOLLOW) must be ENOENT or S_ISREG */
/* publish: renameat(dirfd, tmp, dirfd, name); then fsync(dirfd) tolerating EINVAL/ENOTSUP/EOPNOTSUPP */
```
Probe results on this Mac: 32,789 B write + `F_FULLFSYNC` + `renameat` + `fsync(dir)` averaged 4.3 ms (worst 7.0 ms over 20) [VERIFIED: local probe, dev machine; hosted runners differ], comfortably inside the 2 s HOST-02 ceiling even with a final flush.

### Pattern 2: Bounded read + import with a TOCTOU re-check (D-08)
`openat(..., O_RDONLY|O_NOFOLLOW|O_NONBLOCK|O_NOCTTY|O_CLOEXEC)`; `ENOENT` -> fresh image; **any other errno including `ELOOP` -> refusal (exit 2)**. Then `fstat` (`S_ISREG`, `st_size == want`), EINTR-safe read of up to `want+1`, a second `fstat` comparing dev/inode/size, then `gbb_import_battery`. Probes show on both platforms: a **dangling symlink** gives `ELOOP` ("Too many levels of symbolic links"), `O_CREAT|O_EXCL|O_NOFOLLOW` onto it gives `EEXIST`, and a **FIFO opens successfully** with `O_NONBLOCK` and reports `S_ISREG=0` (so the `fstat` check, not the open, rejects it, and the process never blocks). `gbb_import_battery` itself is atomic on refusal (`GBB_BATTERY_SIZE_MISMATCH`, bad RTC block -> `GBB_INVALID_ARGUMENT`, live RAM unchanged; `gabbaboy.h` comment), so a host refusal does not need to undo core state.

### Pattern 3: Strict basename (D-07) - validate, never rewrite
Pure function `host_stem(const char *rom_path, char *out, size_t cap)` -> `{OK, REFUSE}`. Needs a **strict UTF-8 validator** (reject overlongs `C0/C1`, surrogates `ED A0..BF`, `> U+10FFFF` i.e. `F4 90+`/`F5+`, truncated sequences) of about 30 lines; copy a small DFA rather than add a dependency. Trailing-slash paths (`dir/`) have an empty last component -> refuse. Negative controls: a mutant that strips instead of refusing must fail; each refusal class (empty, leading `.`, byte `< 0x20`, `0x7F`, `\`, bad UTF-8, `> 200` bytes) has its own CTest with its own stderr reason token (GB-GSD-029).

Longest temp name check: `.` + 200 + `.sav.tmp-` (9) + up to 10 pid digits + `-` + 2 seq digits = 223 < 255.

### Pattern 4: Signal flag, frame-boundary poll, EINTR-aware pacing (D-13/D-14)
`static volatile sig_atomic_t g_host_stop;` handler body is `g_host_stop = sig;` only. `sigaction` with `SA_RESTART|SA_RESETHAND`, empty `sa_mask`. Pacing uses relative `nanosleep` to a `CLOCK_MONOTONIC` deadline.
Probe (identical on macOS and gcc:13/glibc): with `SA_RESTART|SA_RESETHAND` installed, `nanosleep(5 s)` interrupted by `SIGALRM` after 1 s returned `-1`, `errno == EINTR`, flag set to 14, elapsed 1.00 s, and the disposition afterwards was `SIG_DFL`. So SA_RESTART does **not** hide the signal from `nanosleep` [VERIFIED: probe, macOS arm64 + gcc:13 Linux], matching POSIX ("until ... a signal is delivered to the calling thread", `nanosleep` ERRORS: "was interrupted by a signal") [CITED: pubs.opengroup.org/onlinepubs/9699919799/functions/nanosleep.html]. Order (prescriptive): install handlers first, then load ROM and save, then check the flag (a signal before the first frame exits 0 and writes nothing, D-14), and print `gbb-host: ready` (with `fflush`) only after both; a SIGTERM that arrives before the handler exists takes the default action and the harness would see a signal death, so the harness must wait for `ready` before signalling.
`stop reason` handling: treat `GBB_STOP_BUDGET`, `GBB_STOP_HALTED_IDLE`, `GBB_STOP_STOPPED` as normal (F10); every other reason (`UNSUPPORTED_OPCODE`, `UNSUPPORTED_BUS`, `LOCKUP`, `INVALID_STATE`, `NO_PROGRESS`, `TRACE_FULL`) is a core stop -> attempt final flush, exit 1.

### Pattern 5: Cadence as a pure function (D-11) - the key time-budget decision
Measured Debug cost on this Mac: 600 `gbb_run(140448)` frames took 1.73 s on the LCD-off continuation ROM (2.88 ms/frame) and 2.31 s on `visible-demo/demo.gb` (3.86 ms/frame) [VERIFIED: probe against `build/libgabbaboy_core.a`, CMAKE_BUILD_TYPE=Debug]. Therefore:
- 300 frames (generation trigger) is about 1 s, fine end-to-end.
- 3,600 frames (RTC-drift cadence) is **11-14 s** plain Debug and roughly 3x under ASan: an end-to-end wait for it would exceed the 75%-of-60 s guardrail (GB-CI-012) on a slow hosted runner.
So implement `host_cadence_step(&state, frame, generation, ...) -> {NONE, FLUSH, EXPORT_COMPARE}` as a pure function and test the 16-quiet / 300-old / 3,600 thresholds and the `!=` generation compare with synthetic sequences (including off-by-one controls and a mutant that uses `>` instead of `!=`). The runner end-to-end tests then need only one write-driven flush (< 400 frames) plus the final flush. RTC drift is also covered end-to-end by the **final flush** export-and-compare, which needs no 3,600-frame wait.

### Pattern 6: Slot load as an all-or-nothing sequence (D-23)
Order is the contract: read -> snapshot (`gbb_state_size` + `gbb_save_state`) -> battery guard -> **`gbb_load_state` first** -> only on success write the undo file (fail => `gbb_load_state(snapshot)` rollback) -> re-anchor. The D-26 "order mutant" (undo written before `gbb_load_state`) must fail the "a refusal touches no files" test: that test snapshots SHA-256 of slot, undo, preload and `.gbb` files plus `gbb_save_state`, `gbb_copy_battery` and `gbb_battery_generation` before and after. Allocate state buffers on the heap (state is about 190 KB for the DMG tracer and up to 524,352 B by the format ceiling, `docs/state-format.md`); read at most `gbb_state_size(live)+1` bytes so a size+4096 file maps to `GBB_STATE_SIZE_MISMATCH` -> "is damaged" (F2).
Generated refusals map as follows (F2 order): DMG state in a CGB slot -> `IDENTITY_MISMATCH`; patched version token with recomputed CRC -> `UNSUPPORTED_VERSION`; text file (no `GBBS` or `< 64` B) -> `BAD_FORMAT`; flipped body byte -> `CORRUPT`; truncated >= 64 B -> `SIZE_MISMATCH`; size+4096 -> `SIZE_MISMATCH`; symlinked slot -> read failure -> "could not be read".

### Pattern 7: Input re-anchor with `gbb_get_input_clock` (D-24)
Add the getter with the `gbb_info` `struct_size` handshake (`GBB_INFO_SIZE_V1 28u`, `gabbaboy.h:376`). Required repo hygiene for a new core function: a `/* MODEL: BOTH GATE-00 basis=host-api */` tag directly above it (rule R1 of `tests/scripts/verify-model-gates.py`: every top-level function needs a MODEL tag), a `static_assert` of `GBB_INPUT_CLOCK_SIZE_V1 24` against `sizeof`, use of the symbol in **both** `tests/consumers/c/main.c` and `tests/consumers/cpp/main.cpp` (the Phase 11 pattern in `tests/cgb_consumer_symbol_coverage.cmake` fails with `consumer-symbol-missing` otherwise), the docs mention in `docs/native-integration.md` (VerifyDocContract requires the identifier to be declared in the header), and one core test. Re-run `verify-state-contract.py`, `verify-state-horizon.py`, `verify-state-pins.py` and the model-gates scan to prove "state bytes, pins, tokens unchanged".
Player after a load: `player_input_reset`-style re-anchor to `now`, seed `pending_count` from `queued_count`, queue releases at `max(now, last_queued)`; if `last_queued - now` exceeds one frame x `PLAYER_INPUT_QUEUE_CAPACITY` (64), restore the snapshot and show the "unsafe queued input" message. Mutant: omit the rebase and the "key accepted within one frame after loading a later-time / earlier-time state" test must fail.

### Pattern 8: Real-signal Python harness (D-17)
Run with `python3 -I`, stdlib only, Python >= 3.9. Practical rules the CONTEXT does not spell out:
- Read `gbb-host: ready` from the child's stderr with a watchdog (timer or `select`), never an unbounded `readline()`; the C side must `fflush` (D-14).
- Before `Popen`, set the harness's own `SIGINT`/`SIGHUP` to `SIG_DFL` so the child inherits default dispositions; add one **inherited-`SIG_IGN` row** (set `SIG_IGN` before `Popen`, send SIGINT, assert the runner keeps running until SIGTERM) because D-13 promises the `nohup`/background convention, and shells start async jobs with SIGINT ignored.
- Assert the 2.0 s ceiling only from `kill()` to `wait()` and only in non-sanitizer lanes; CI runs ctest 4-wide (F15), so mark these tests `PROCESSORS 2` (or `RESOURCE_LOCK`) to avoid load-induced flakes, and keep each under ~25 s so they stay below 75% of the 60 s base TIMEOUT.
- Deterministic replay proof: paced run stopped by SIGTERM prints `stopped_at_frame=K`; a fresh `--frames K` batch run in a new directory must produce a byte-identical `.sav` (fixture writes a per-frame counter so a partial frame would differ). Decoys required to fail: no flush on SIGTERM; flush mid-frame; exit 0 after a failed flush; in-place write on the SIGKILL row.
- Failure row: `chmod 0500` the save dir after `ready`, send SIGTERM, expect exit 1, old `.sav` byte-identical, no temp left; hard-fail with a clear message if `os.geteuid() == 0`. (This session runs as uid 501, so it is satisfiable here; hosted runners are non-root.)
- SIGKILL row: loop kills at pseudo-random delays against an RTC cart in `--frames` batch mode with `RLIMIT_CORE=0`, after each kill assert size is exactly `bytes` and content equals one of the previously valid images, then restart and assert the sweep removed `.<stem>.sav.tmp-*`.
- Windows: the harness and the file-producing rows are POSIX-only; exclude them in `cmake/ExpectedTests.cmake` **and** `.github/scripts/verify-test-inventory.sh` in the same commit (GB-CGB-007). That script has the exclusion `sed` list **and** two self-test lists (`_self_test_platform_filter_cases`); update all and run `bash .github/scripts/verify-test-inventory.sh --self-test`.

### Pattern 9: Save-format table and completeness (D-16/D-19/D-20)
- `docs/host-contract.json` in canonical form: define canonical as `json.dumps(json.loads(text), indent=2, ensure_ascii=True) + "\n" == text` (key order preserved) and have the checker enforce it; the seeded "non-canonical JSON" control is the same file with CRLF or tab indentation.
- Completeness in process: a small C test enumerates `type` in the 256 byte space (cheap) x RAM codes `00..06` x ROM codes `00..08` **restricted to ROM sizes that are cheap or necessary** (MBC1 32 KiB RAM needs ROM codes 0..6 -> up to a 2 MiB `calloc`; fine), builds a header-valid ROM like `tests/test_battery.c:make_rom` (`rom[0x147]=type; rom[0x148]=rom_code; rom[0x149]=ram_code;` + checksum loop over `0x134..0x14C`), calls `gbb_probe_rom` (flags `GBB_INFO_HAS_BATTERY`, `ram_size_bytes`, `GBB_INFO_HAS_RTC`), then `gbb_create/gbb_load_rom/gbb_battery_size` and compares to the JSON-derived table. Every admitted battery combination needs a row and every row must be admitted; `$10/$05` must be non-admitted (`GBB_UNSUPPORTED_CARTRIDGE_VARIANT`).
- Generated fixture ROMs (Python, written under the build dir, nothing committed): tiny hand-assembled program at `$0150`: `ld a,$0A; ld ($0000),a` (`3E 0A EA 00 00`), `ld a,$5A; ld ($A000),a` (`3E 5A EA 00 A0`), `jr -2` (`18 FE`), with `$0100: 00 C3 50 01`. This works for MBC1/MBC3/MBC5 (RAM enable at `$0000`) and MBC2 (A8 = 0). MBC2 byte 0 reads back `$FA` (canonical `0xF0 | nibble`, F5). For `$0F` there is no RAM, so rely on the 21 B block structure.
- `--print-save-format` for a no-battery cartridge: recommend `save_format=none bytes=0` and exit 0 (so the completeness/negative rows can assert it). Print on a single line `save_format=<id> bytes=<n>` so `tests/expect_exit.cmake` (`GBB_EXPECT_MIN_KEY=bytes`, exactly one `bytes=<digits>`) can assert it.
- Freeze: select "latest `v*` tag" with a strict `^v[0-9]+\.[0-9]+\.[0-9]+$` filter and numeric sort (local tags include a stray `v0.2`, F15). Tags exist (v0.2.1) but the file does not -> `baseline=none` pass; zero tags -> fail; temp-repo control.
- Add the id-grammar regex `^gabbaboy-[a-z0-9-]{1,48}-v[1-9][0-9]*$`, `bytes == ram_bytes + rtc_bytes`, and "same id => same bytes" as table invariants with one seeded control each.

### Pattern 10: Game-visible readback without a new flag (XFER-002)
D-02 fixes the grammar (no `--print-wram`). Use a **counter fixture** instead: the guest reads `$A000`; if `$FF` (fresh) it writes `$01`, else it writes `old+1`, then spins. Run 1 persists `01`; run 2 (fresh process, same save dir) persists `02`. The persisted byte *depends on the previously persisted bytes*, which is the XFER-002 requirement; wrong-save control: preload `$41` -> `$42`, and a mutant that ignores the import yields `01`. This also serves the installed-package smoke (D-28), using a generated ROM so no installed fixture is needed beyond the runner (or the already-installed `fixtures/mbc1-continuation` for the tracer, which writes `$47 $42 $17` and is not a counter).

### Anti-Patterns to Avoid
- **Linking a core into `gabbaboy_host`:** `verify-core-linkage.py` requires an acceptance-linked executable to name exactly one core archive exactly once. Give `gabbaboy_host` include directories only (like `gabbaboy_accept_bare`) and let the executable supply `GabbaBoy::core`.
- **Using `gabbaboy_test.h` or `gbb_accept.h` in host/slot code:** the runner's `main.c` includes them; `src/host` must not (D-04 symbol CTest).
- **Reading with `st_size` as allocation size** or reading a FIFO/device before `fstat` (D-08, D-22).
- **Rewriting an unsafe basename** (strip/replace) instead of refusing (D-07).
- **Treating `ENOENT` and `ELOOP` the same** at import (Pattern 2 probe: a dangling symlink gives `ELOOP`).
- **In-handler I/O, `printf`, or `exit()`** (CERT SIG30-C/SIG31-C; D-13).
- **Counting wall-clock in assertions** other than the one documented 2.0 s ceiling.
- **A manual "look at the title bar" check** for slot messages: the status text is a pure string table and must be asserted by string equality.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Atomic persist | `fopen("w")` + `rename` by path | `save_io_replace` on a dirfd (one implementation shared by runner and player slots) | TOCTOU on path components, symlink swaps, partial files, missed dir fsync. |
| Save-state serialization | New slot wrapper/format | Raw `gbb_save_state` bytes (header already has identity + CRC) | D-22; a wrapper would add a second format to keep in sync. |
| RTC wall-clock catch-up in host mode | `--clock-unix`/mtime heuristics | Nothing (D-12); declare "not-recorded" | Raw `.sav` has no timestamp; heuristics create nondeterminism. |
| Exit-code docs | Prose tables maintained by hand in three places | X-macro `host_exit.h` + `docs/host-contract.json`, checked by one script | Drift between code, docs and tests. |
| JSON parser in C | A parser | Python checker validates; C uses a static table | No runtime JSON need. |
| Hashing | A new SHA-256 | `src/accept/sha256.c` / `player_save_identity.rom_sha256` | Already in repo and tested. |
| Signal-safe logging | `fprintf` in handler | Flag + main-loop logging | Async-signal-safety. |
| Test ROMs | Committing ROM binaries | Generate in Python at test time (original, redistributable, no digest churn) | AGENTS.md fixture-rights rule; states embed the release token and go stale at Phase 19. |

**Key insight:** every hazardous step (path resolution, partial writes, signals) is solved once, at the lowest layer, and the tests attack that layer with decoys; higher layers (runner, player slots) only compose it.

## Common Pitfalls

### Pitfall 1: Parallel plans that share the exact test inventory
**What goes wrong:** D-31 marks 18-01‖18-02 and (conditionally) 18-03‖18-04 parallel, but every plan appends names to `tests/expected-tests.txt` (and registers tests in `tests/CMakeLists.txt`); `cmake/ExpectedTests.cmake` fails configure if registered != expected (GB-CART-003 caused this in Phase 8).
**How to avoid:** Sequence plans that edit these two files: 18-01 -> 18-02 (small) and 18-03 -> 18-04, or have the parallel plan write only inside a `# --- Phase 18 plan 18-0X begin/end ---` block and merge by a single agent. Player-suite tests (18-05) use `tests/player/expected-tests.txt`, a different file.
**Warning signs:** Configure error "Registered CTest cases differ from tests/expected-tests.txt".

### Pitfall 2: Debug frame cost makes cadence tests blow the budget
See Pattern 5. 3,600 frames is 11-14 s Debug; ASan lane scales timeouts x3 (`cmake/ScaleSanitizerTimeouts.cmake`) but not runtime. **How to avoid:** pure cadence function + one write-driven e2e flush; check the per-test hosted time at the phase tail (GB-CI-012).

### Pitfall 3: Windows inventory failure for POSIX-only tests
GB-CGB-007. Any CTest registered only `if(NOT WIN32)` must be removed from the Windows expected set in `cmake/ExpectedTests.cmake` **and** `.github/scripts/verify-test-inventory.sh`. Also `tests/CMakeLists.txt` test-budget uses `--partial-inventory` on Windows. Includes the portable-looking slot test, because it links the POSIX dir-fd writer (stubs under `_WIN32` cannot run the file tests).

### Pitfall 4: Feature macros under `C_EXTENSIONS OFF`
Strict `-std=c17` hides POSIX names. Define `_POSIX_C_SOURCE 200809L` (and `_DARWIN_C_SOURCE` on Apple) **before the first include in each POSIX file**. Probed: with exactly that, gcc:13 strict C17 exposes `O_DIRECTORY`, `O_NOFOLLOW`, `O_CLOEXEC`, `SA_RESTART`, `SA_RESETHAND`, `renameat`, `fstatat`, `clock_gettime`, `nanosleep`; `F_FULLFSYNC` exists only on Apple (guard with `#ifdef`). `mkfifoat` and `symlinkat` (test helpers) compiled on both. [VERIFIED: probes]. Unused-variable warnings from test probes show warnings are on; keep new files warning-clean.

### Pitfall 5: `limitations.h` and help text are pinned in several places
Editing `GBB_PLAYER_LIMITATIONS_TEXT` requires updating `tests/player/test_limitations.c` (full-literal `strcmp`), and re-checking `tests/scripts/verify-phase8-player-contract.py` (reads both files), `tests/player/claims_agree.cmake` (phrases across README and `preview.yml`), `tests/scripts/verify-cgb-corpus-claims.py` and `verify-cgb-hdma-claims.py`. `preview.yml` is a workflow file; D-27 forbids release workflow edits, so **add slot wording to the player help dialog (`show_help`, `main.c:807`) and to `limitations.h` only in ways that do not require new `claims_agree` phrases**, and grep every consumer of the string before editing. Also `check_no_stale_speed_claims.cmake` scans `native-integration.md`, `unreleased.md`, `preview.md`, `cartridge-and-saves.md`, README and `limitations.h` for stale speed phrases; avoid "no double speed" wording in new text.

### Pitfall 6: Doc contract rejects undeclared identifiers
`VerifyDocContract.cmake` fails with `doc-contract-undeclared: <identifier>` for any `gbb_*`/`GBB_*` token in `native-integration.md` not declared in `gabbaboy.h`. The "Host process contract" section may therefore name `gbb_get_input_clock`, `gbb_battery_generation` etc. only after the header declares them, and must not mention core-private names such as `GBB_MAX_ROM_SIZE` or `GBB_INPUT_EVENT_CAPACITY` (F6, F7). Write `8 MiB` instead.

### Pitfall 7: Signal-test fragility
Child inherits `SIG_IGN` for SIGINT if the harness was started as an async job; handler install must come before `ready`; a second signal during final flush kills (by design `SA_RESETHAND`) so the harness must send exactly one; under ASan the 2 s claim is not asserted (D-17). `SIGPIPE` is ignored so a closed stderr pipe cannot kill the process mid-flush.

### Pitfall 8: Core stop vs halted guest
`GBB_STOP_HALTED_IDLE`/`GBB_STOP_STOPPED` are normal (F10); mapping them to exit 1 would fail every guest that halts in a loop (including the SRAM counter fixture if it halts). Frame 0 of a halting ROM may consume only 48 half-dots; that is why D-03 defines a frame as one fixed `gbb_run` step, not as consumed time.

### Pitfall 9: Stem differs from Playstead for odd extensions
F11 shows Playstead strips *any* last extension (`deletingPathExtension`); D-07 strips only a final `.ext` of 1-8 ASCII alphanumerics. They agree for `.gb/.gbc/.GB/.GBC/.bin` but diverge for e.g. `game.v2-final` (Playstead -> `game`, GabbaBoy -> `game.v2-final`). Locked decision; add a differential test table of agreeing cases and **document the divergence** in the host contract so the adapter pin author is not surprised.

### Pitfall 10: Core-internal constants leak into adapters
`GBB_MAX_ROM_SIZE` and `GBB_INPUT_EVENT_CAPACITY` are not public (F6, F7). Host code defines its own `8u*1024u*1024u` and the player uses `PLAYER_INPUT_QUEUE_CAPACITY`. The D-04 symbol CTest only checks undefined `gbb_*` symbols, so a header-level `#include "gabbaboy_test.h"` must be caught by an include scan too (add it to the same script).

### Pitfall 11: Local-time formatting in tests
"Slot N selected: saved YYYY-MM-DD HH:MM" uses local time from mtime. Tests must set `TZ=UTC` (and call `tzset`) and `utimensat`/`utimes` a known mtime; otherwise the assertion flakes across runners.

### Pitfall 12: Existing code drifted from CONTEXT line numbers
`main.c` tracer route is line 455, not 451 (F8). Re-grep before editing; reference anchors by text, not line number, in plans.

## Code Examples

### Host-mode dispatch (before the tracer route and acceptance parse)
```c
/* Source: 18-CONTEXT D-02; anchor text from src/runner/main.c:455 (F8) */
int main(int argc, char **argv) {
    if (gbb_host_is_host_invocation(argc, argv))   /* any of --rom, --save-dir, --print-save-format, incl. "--rom=..." */
        return gbb_host_main(argc, argv);          /* all grammar errors exit 2 inside */
    if (argc == 2 && strncmp(argv[1], "--", 2) != 0) return run_original_tracer(argv[1]);
    /* ... unchanged acceptance grammar and 0/1/2/3/4 codes ... */
}
```

### Exit table as X-macro (checked against `docs/host-contract.json`)
```c
/* Source: 18-CONTEXT D-15 */
#define GBB_HOST_EXIT_TABLE(X) \
    X(0, clean,   "Signal or --frames end; flush succeeded or nothing to write") \
    X(1, failure, "I/O or flush failure, allocation failure, or core stop mid-run") \
    X(2, refusal, "Refused before any save mutation")
```

### Proposed read-only getter (D-24)
```c
/* Source: 18-CONTEXT D-24 (proposed; not yet in gabbaboy.h) */
typedef struct {
    uint32_t struct_size;            /* IN: caller sets GBB_INPUT_CLOCK_SIZE_V1 or more */
    uint32_t queued_count;
    uint64_t now_half_dots;
    uint64_t last_queued_half_dots;  /* == now_half_dots when the queue is empty */
} gbb_input_clock;
#define GBB_INPUT_CLOCK_SIZE_V1 24u
/* MODEL: BOTH GATE-00 basis=host-api */
gbb_error gbb_get_input_clock(const gbb_instance *instance, gbb_input_clock *out);
```
`4 + 4 + 8 + 8 = 24`; outputs unchanged on any error; NULL or short `struct_size` -> `GBB_INVALID_ARGUMENT`.

### Harness skeleton (real signal, replay proof)
```python
# python3 -I tests/scripts/test_host_signals.py <runner> <workdir>
import os, signal, subprocess, sys, time
signal.signal(signal.SIGINT, signal.SIG_DFL); signal.signal(signal.SIGHUP, signal.SIG_DFL)
p = subprocess.Popen([runner, "--rom", rom, "--save-dir", d], stderr=subprocess.PIPE, text=True)
ready = wait_for_line(p.stderr, "gbb-host: ready", timeout=20)      # watchdog, not bare readline()
t0 = time.monotonic(); p.send_signal(signal.SIGTERM); rc = p.wait(timeout=10); dt = time.monotonic() - t0
# assert rc == 0; (non-sanitizer lanes) assert dt < 2.0; parse stopped_at_frame=K from the exit line
# replay: runner --rom rom --save-dir d2 --frames K  ->  bytes(d/x.sav) == bytes(d2/x.sav)
```

## State of the Art

| Old Approach | Current Approach | Impact |
|--------------|------------------|--------|
| Player-only `.gbb` envelope via path-based `mkstemp`+`rename` (`session.c` `atomic_save`) | Dir-fd `openat/renameat` writer in `gabbaboy_host` | New code uses the stricter writer; the `.gbb` path stays unchanged (seed: converge later). |
| mGBA-style RTC footer (32,816 B) | GabbaBoy `GBRT` block (32,789 B), id-versioned | No interoperability claim; correct the "non-RTC SRAM byte-identical" sentence for MBC2 (256 vs 512 B) in `PLAYSTEAD-CONTRACT.md` (D-19). |

**Deprecated/outdated within the repo:** the CONTEXT note "main.c line 451" (now 455); PLAYSTEAD-CONTRACT's MBC2 byte-identity claim.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | CI `ubuntu-22.04` ships Python 3.10, so new checkers must avoid 3.11+-only syntax | Standard Stack | Low: a newer-only feature fails one hosted lane; mitigated by writing to >= 3.9 and `from __future__ import annotations`. |
| A2 | SDL3's default macOS menu does not bind Cmd+S / Cmd+L / Cmd+Z, so those keys reach `handle_key` | Pattern 6 / D-21 | Medium: if bound, slot keys never fire; the macOS embedded-main key test calls `handle_key` directly and would not catch it, so add one real-window smoke row if the owner wants proof. |
| A3 | `v0.2`-style stray tags are the only irregular tags; "latest" by strict semver filter is stable through Phase 19 | Pattern 9 | Low. |
| A4 | Hosted macOS/Windows runner `F_FULLFSYNC`/`fsync` latency stays well under the 2 s HOST-02 ceiling | Pattern 1 | Low: local mean 4.3 ms; the ceiling is asserted only in non-sanitizer lanes and a failure would be visible. |
| A5 | `--print-save-format` for a no-battery cartridge prints `save_format=none bytes=0` and exits 0 | Pattern 9 | Low: CONTEXT leaves the case unspecified (Claude's discretion); recommendation only. |
| A6 | An SRAM-counter fixture is an acceptable "game-visible readback" for D-28/XFER-002 without a new flag | Pattern 10 | Low-Medium: if the owner insists on WRAM readback, the grammar (D-02) must change. |
| A7 | C17 says a signal handler may store only to `volatile sig_atomic_t` (plus lock-free atomics); CERT SIG30-C/SIG31-C | Pattern 4 | Low (training knowledge; consistent with D-13). |

## Open Questions (RESOLVED)

1. **Stem divergence from Playstead for non-alphanumeric or > 8-char extensions (F11 vs D-07).**
   - Known: D-07 is locked and agrees for ordinary ROM extensions.
   - Unclear: whether the future Playstead pin should pass a normalized `--rom` name.
   - Recommendation: keep D-07; document the divergence in `host-contract.json`/docs and add a differential test over `.gb/.gbc/.GB/.GBC/.bin`.
   - RESOLVED: D-07 kept as locked. The rule is implemented in 18-01 Task 1 (a dot at byte 0 never separates an extension, matching deletingPathExtension); the `.gb/.gbc/.GB/.GBC/.bin` differential table and the `game.v2-final` divergence row are `host_stem_accepts` in 18-02 Task 1; the divergence sentence is in the native guide's Host process contract section, 18-09 Task 2. A future Playstead pin passing a normalised name is RM-020's concern.
2. **Should 18-02 (getter) precede 18-01 or follow it?**
   - Recommendation: 18-01 first, 18-02 immediately after (serial), since both touch the shared inventories; 18-02 is small. 18-04 depends on 18-02 and on 18-01's writer.
   - RESOLVED (plan numbers after the 18-01 split): serial. 18-01 host tracer (wave 1), 18-02 grammar/stem/API checks (wave 2), 18-03 input-clock getter (wave 3, depends on 18-02 because all three append to `tests/expected-tests.txt`); the slot engine 18-05 depends on 18-03 (getter) and 18-04 (writer seams and host hardening).
3. **Real-window proof that Cmd+S/L/Z reach the app (A2).**
   - Recommendation: accept the embedded-`handle_key` coverage; record the unproven SDL-menu assumption as a limitation line rather than inventing a manual UAT.
   - RESOLVED differently from the recommendation: A2 is proven by an automated menu scan, not declared as a limitation. 18-06 Task 3 (numbered 18-05 before the 18-01 split) adds `player_slot_menu_shortcuts`, which walks the SDL-created macOS main menu through the Objective-C runtime and fails on any Command-only S, L or Z key equivalent, and `player_slot_menu_shortcuts_control`, which seeds a Command-S item and must fail. Both are mandatory; if the macOS player lane cannot create the Cocoa menu, the executor stops and reports to the owner. No manual UAT.
4. **Stale-temp sweep and a second writer.** D-10 deliberately documents single-writer; nothing to resolve, but the docs must say that a second runner on the same (dir, stem) can have its live temp swept.
   - RESOLVED: the sweep (exact prefix, after all refusal checks) is 18-04 Task 1 (`host_sweep_after_checks`) with the unit table in 18-04 Task 2 (`host_sweep_exact_prefix`); the single-writer sentence, including that a second runner's live temp may be swept, is pinned in the native guide by 18-09 Task 2 (`native_guide_host_contract`).

## Runtime State Inventory

Not a rename/refactor/migration phase. Omitted. (New persisted artifacts are created fresh; no existing stored string is renamed.)

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| CMake | build/CTest | yes | 4.4.3 (floor 3.25 checked by CI job) | - |
| Ninja | presets | yes | 1.13.2 | - |
| C compiler (strict C17) | all | yes | Apple clang 21.0.0 | gcc via Docker |
| Python 3 | harness + checkers | yes | 3.14.4 | - |
| Docker + `gcc:13` | Linux/glibc probes (dev only) | yes | Docker 29.5.2 | CI `ubuntu-24.04` job |
| `nm`/`llvm-nm` | D-04/D-18 symbol layers | yes | llvm-nm (GNU-compatible) | `dumpbin` on MSVC (existing script handles it) |
| SDL3 3.4.18 | player build | `build-player/` exists | pinned EXACT | player suite is macOS-only anyway |
| RGBDS | not needed (fixtures generated in Python) | yes (`rgbasm`) | - | - |
| Non-root user | read-only-dir failure row | yes (uid 501) | - | test hard-fails as root by design |
| Hosted Windows | MSVC compile of `src/host` stubs | CI only | - | `#ifndef _WIN32` stubs; refusal CTest |

**Missing dependencies with no fallback:** none.

## Validation Architecture

> `workflow.nyquist_validation` is `true` in `.planning/config.json` (verified this session).

### Test Framework
| Property | Value |
|----------|-------|
| Framework | CTest + project C test binaries (`REQUIRE`-style) + Python `-I` checkers/harness + CMake `-P` contract checks |
| Config file | `tests/CMakeLists.txt`, `tests/player/CMakeLists.txt`, inventories `tests/expected-tests.txt` and `tests/player/expected-tests.txt` |
| Quick run command | `cmake --build --preset phase1 && ctest --preset phase1 -R '^(host_|slot_|save_format_|no_host_clock|runner_help)' --output-on-failure` |
| Full suite command | `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error` (the configured `workflow.test_command`) |
| Player suite | macOS: `bash tests/scripts/verify-phase3-player.sh --build-package` (CI `macos-player-package`) |
| ASan lane | `ctest --preset phase1-asan` (timeouts x3 via `ScaleSanitizerTimeouts.cmake`) |

Proposed test-name prefixes (Claude's discretion): `host_*` (runner/library), `slot_*` (SDL-free engine), `player_slot_*` (macOS), `save_format_*`.

### Success Criterion -> Automated Check Map

| SC | Behavior | Test Type | Automated Command (proposed name) | Negative control (must fail) | Wave 0 gap |
|----|----------|-----------|-----------------------------------|------------------------------|------------|
| 1a | Slot round trip, bytes of a saved slot equal post-load `gbb_save_state` | unit (portable, ASan) | `ctest -R slot_roundtrip` | mutant that saves a stale snapshot | `tests/test_slots.c`, `src/player/slots.c` |
| 1b | Refused/mismatched/wrong-ROM slot leaves `gbb_save_state`, `gbb_copy_battery`, generation and slot/undo/preload/`.gbb` SHA-256 byte-identical | unit | `ctest -R slot_refusal_untouched` (one case per generated refusal: DMG-in-CGB, patched version+CRC, text file, flipped byte, truncated, size+4096, symlinked slot) | order mutant: write undo before `gbb_load_state` | same |
| 1c | Exact message per `GBB_STATE_*` code and per fs error | unit | `ctest -R slot_message_table` | mutant mapping one code wrongly | - |
| 1d | Undo swap, undo-write failure rollback, battery guard (load A then B keeps pre-A battery) | unit | `ctest -R 'slot_undo\|slot_battery_guard'` | rollback-removed mutant; guard-removed mutant | - |
| 1e | Input re-anchor (later and earlier state), unsafe queued input refused | unit/core | `ctest -R 'input_clock\|slot_reanchor'` | mutant without rebase; getter returning `now` always | 18-02 core test + consumer coverage |
| 1f | Key decode: cmd+S does not save battery, cmd+R does not reset, ignore on repeat/transition; select 1-9 | macOS player suite (embedded `main.c`) | `ctest -R player_slot_keys` (macOS) | decoder mutant ignoring GUI modifier | `tests/player/test_slots.c` + `tests/player/expected-tests.txt` |
| 1g | Getter ABI: struct_size handshake, outputs unchanged on error, consumers call it | core + installed consumers | `ctest -R 'input_clock_api\|installed_consumer_(c\|cpp)'`, `cgb_consumer_symbol_coverage` list | short `struct_size` still writes -> fail | - |
| 2a | Atomic writer: temp is O_EXCL in save dir, rename, dir fsync; failure unlinks temp; old file intact | unit with fault seams (test builds only) | `ctest -R host_atomic_writer` | in-place-write decoy; fsync-error decoy; "rename without target check" decoy | `tests/test_host_save_io.c` |
| 2b | Basename: each refusal class exits 2 with its own reason token, no fs access; positive `.gb/.gbc/.GB` stems | CLI | `ctest -R host_basename_*` via `expect_exit.cmake` | transform-instead-of-refuse mutant | - |
| 2c | Symlinked target (incl. dangling), FIFO, directory, device at `.sav` -> exit 2, file inode/mtime/bytes and dir listing unchanged | CLI + Python | `ctest -R host_import_hostile` | mutant that follows symlinks / opens FIFO blocking | - |
| 2d | Import size: 0, N-1, N+1, mGBA 32,816 B footer, 8 MiB+1, bad RTC block refused; exact N accepted | CLI | `ctest -R host_import_sizes` | mutant accepting prefix | - |
| 2e | Cadence thresholds (16 quiet / 300 old / 3,600 compare, `!=` generation, identical image never rewritten) | pure unit | `ctest -R host_cadence` | `>` vs `!=` mutant; off-by-one mutants | `tests/test_host_cadence.c` |
| 2f | Save dir semantics: missing/non-dir exits 2; symlink-in-path allowed (positive: `/tmp`-style); never created | CLI | `ctest -R host_savedir` | mutant that `mkdir`s | - |
| 2g | API-only: undefined `gbb_*` symbols of `gabbaboy_host` and slot objects subset of public header; no `gabbaboy_test.h`/`gbb_accept.h` include | CMake `-P` | `ctest -R host_api_surface` | seam-calling mutant object | `cmake/CheckHostApiSymbols.cmake` |
| 2h | Runner/host SOURCES subset of `GBB_BUILD_QUALIFIED` list | CMake `-P` | `ctest -R host_qualified_sources` | mutant with an unlisted source | `cmake/CheckRunnerSourcesQualified.cmake` |
| 3a | Real SIGTERM: current frame finished, save flushed, exit 0, kill-to-wait < 2.0 s (non-sanitizer lanes) | Python harness, POSIX | `ctest -R host_signal_term` | decoys: no flush; mid-frame flush; exit 0 after failed flush | `tests/scripts/test_host_signals.py` |
| 3b | Replay proof: `stopped_at_frame=K` equals `--frames K` batch `.sav` | Python harness | `ctest -R host_signal_replay` | partial-frame decoy | - |
| 3c | Exit-table rows: 0 (SIGTERM, SIGINT, `--frames`), 1 (read-only dir after ready; core stop), 2 (each refusal), crash (SIGKILL storm) | Python harness + CLI | `ctest -R 'host_exit_*'` | in-place-write decoy fails the SIGKILL row; exit-0-after-failed-flush decoy | - |
| 3d | Inherited `SIG_IGN` SIGINT honoured; SIGPIPE ignored | Python harness | `ctest -R host_signal_inherited_ign` | handler installed unconditionally mutant | - |
| 3e | No signal code in the core (source + object layers) | CMake `-P` (extend `CheckCoreNoHostClock.cmake`) | `ctest -R no_host_clock` + new `no_host_clock_signal_selftest` | seeded control compiled with strict-C17 flags calling `signal()`/`kill()` | - |
| 3f | Windows exemption: `--save-dir` exits 2 before fs access; `--print-save-format` works; POSIX tests excluded in both inventories | Windows CTest + inventory self-test | `ctest -R host_windows_refusal` (Windows), `bash .github/scripts/verify-test-inventory.sh --self-test` | inventory lists out of sync -> fails | edits to `ExpectedTests.cmake`, `verify-test-inventory.sh` |
| 4a | JSON canonical, ids grammar, `bytes == ram_bytes + rtc_bytes`, same id => same bytes, X-macro and docs tables agree | Python checker | `ctest -R host_contract_json` + `--self-test` | the 12 seeded controls in D-20 (32,816, changed id, deleted row, `$10/$05`, versioned/uppercase id, sum mismatch, one id two sizes, short file, per-profile id, freeze mismatch, non-canonical JSON, `$1A` file) | `tests/scripts/verify-save-formats.py` |
| 4b | Completeness: every admitted battery combination has a row and vice versa | C test + Python | `ctest -R save_format_completeness` | deleted-row and extra-row controls | small C enumerator |
| 4c | Produced files: 16 rows x 2 profiles: id/size, SRAM byte 0 `$5A` (MBC2 `$FA`/`>= $F0`), RTC rows end with `GBRT`/`0x01` block, no-battery creates no file, profiles agree | Python + CLI (POSIX) | `ctest -R save_format_files` | shim 1 byte short; shim with cgb-only id | - |
| 4d | Freeze vs latest `v*` tag (`baseline=none` now) | Python + temp-repo control | `ctest -R save_format_freeze` | freeze mismatch control | - |
| X1 | Installed host-mode smoke (relocated prefix, unrelated cwd, temp save dir, two-process counter readback, wrong-save control) | CTest (Linux/macOS) | `ctest -R installed_host_smoke` | wrong preloaded save yields different result; mutant ignoring import | `GBB_TEST_INSTALL_PREFIX` run |
| X2 | Docs say what is promised (flags, atomicity scope, cadence, exit table by mode, signals, Windows refusal, no RTC catch-up, single writer, getter) | CMake `-P` doc contract | `ctest -R 'host_docs_*'` | phrase-removed copy | docs edits |
| X3 | Test budget: no new test above ~75% of its TIMEOUT at the phase tail | `verify-test-budget.py` + hosted timings | `ctest -R test_budget` | n/a (existing ratchet) | - |

### Sampling Rate
- **Per task commit:** the quick `-R` prefix run above plus any directly touched checker `--self-test`.
- **Per wave merge:** full `phase1` suite; on 18-05 also the macOS player suite.
- **Phase gate:** full suite green at the exact PR head on all required CI contexts, plus `phase1-asan`, Windows inventory self-test, `verify-core-linkage.py`, `verify-model-gates.py`, state checkers (`verify-state-contract/horizon/pins`) and `verify-uat-closure.py --self-test`, before `/gsd-verify-work`.

### Wave 0 Gaps
- [ ] `src/host/*`, `gabbaboy_host` target, `src/player/slots.c` (skeleton so tests can link)
- [ ] `tests/test_host_save_io.c`, `tests/test_host_cadence.c`, `tests/test_slots.c`, `tests/test_input_clock.c` (core)
- [ ] `tests/scripts/test_host_signals.py`, `tests/scripts/verify-save-formats.py` (+ `--self-test`), `tests/scripts/verify-host-contract.py`
- [ ] `cmake/CheckHostApiSymbols.cmake`, `cmake/CheckRunnerSourcesQualified.cmake`, extended `cmake/CheckCoreNoHostClock.cmake`
- [ ] `docs/host-contract.json` skeleton and inventory/Windows-exemption edits

## Security Domain

> `security_enforcement` is `true`, ASVS level 1 (`.planning/config.json`).

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | - (no identities) |
| V3 Session Management | no | - |
| V4 Access Control | yes (file-system) | `0600` temp files, no group/world exposure, refuse non-regular/symlink targets, single-writer contract |
| V5 Input Validation | yes | Strict basename + UTF-8 validator, bounded ROM reader (8 MiB), exact-size import, `read <= want+1`, pure unit-tested key decoder, state refusal map |
| V6 Cryptography | no (SHA-256 only for identity names; CRC is accident detection, not authentication) | reuse `sha256.c` |
| V7 Error handling/logging | yes | stderr `gbb-host:` diagnostics carry reason tokens, never secrets or absolute personal paths in committed receipts |
| V12 Files and resources | yes | `openat` on a once-resolved dirfd, `O_NOFOLLOW`, `O_EXCL`, `O_NONBLOCK|O_NOCTTY` for reads, `fstat` before read, no allocation from `st_size`, bounded work |
| V14 Configuration | yes | feature macros per file, `SIGPIPE` ignored, `O_CLOEXEC` everywhere |

### Known Threat Patterns for {C + POSIX file host + SDL player}

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Path traversal via ROM name (`..`, separators, `\`) | Tampering | Last-component only; refuse leading `.`, `\`, controls, bad UTF-8, > 200 B (D-07) |
| Symlink / TOCTOU swap of `.sav` or save dir | Tampering / EoP | Dir resolved once to a fd, `*at` calls, `O_NOFOLLOW`, `lstat`-equivalent `fstatat(AT_SYMLINK_NOFOLLOW)`, dev/inode re-check |
| FIFO/device as `.sav` blocks or reads unbounded data | DoS | `O_NONBLOCK`, `S_ISREG` check before read, exact-size gate (probe: FIFO opens, `S_ISREG=0`) |
| Oversized or hostile import | DoS | `want` from `gbb_battery_size`, cap <= 131,072 + 21 before allocation, read <= `want+1`, hostile sweep (0, N-1, N, N+1, 8 MiB+1) |
| Predictable temp name / clobber | Tampering | `O_EXCL` + pid/seq names with dot prefix, stale sweep only for the exact prefix |
| Partial/torn save on crash or kill | Repudiation / integrity | write + fsync + `renameat` + dir fsync; SIGKILL storm test |
| Async-signal-unsafe handler | Tampering (UB) | Handler body only stores a `sig_atomic_t`; checked by review and the harness |
| State-file attack (crafted slot) | Tampering / DoS | `gbb_load_state` validates whole body before apply; player reads <= `gbb_state_size+1`; symlink rejected; no committed state bytes |
| Slot name injection | Tampering | File names built only from `{rom_sha256}`, `dmg|cgb`, slot digit; nothing user-controlled (D-22) |
| Information disclosure in logs | Information disclosure | Reason tokens only; no home paths in public receipts (AGENTS.md) |

## Plan-Shape Review (D-31)

D-31 stays within the cap (8 primary + 1 gap = 9 of 10). Recommended adjustments, all inside the locked decisions:

| Wave | Plan | Reqs | Notes from research |
|------|------|------|---------------------|
| W1 | 18-01 host tracer | HOST-01 | Includes the **frozen** `save_io_replace` signature and straight-line sequence; `gabbaboy_host` is core-less (include dirs only); generated-ROM helper in Python reused by later plans; Windows refusal CTest; dirty-list + API-symbol checks. |
| W1 (serial after 18-01) | 18-02 getter | PLAY-01 | Not truly parallel: it adds a core test to the shared inventories. Needs MODEL tag, `static_assert`, both consumers, docs identifier, state-checker re-run. |
| W2 | 18-03 file safety + cadence | HOST-01 | Fault seams (test builds only), sweep, hostile sweep, pure cadence function and unit tests. |
| W2 (serial after 18-03) | 18-04 slot engine | PLAY-01 | Needs 18-01 writer + 18-02 getter. POSIX-only in the Windows inventory. |
| W3 | 18-05 player integration | PLAY-01 | Uses `tests/player/expected-tests.txt` (separate file). Mind the limitations/help pins (Pitfall 5). |
| W3 | 18-06 signals + exits | HOST-02 | Harness, decoys, `CheckCoreNoHostClock.cmake` extension, inventory edits (serial with other inventory editors). |
| W4 | 18-07 contract JSON + save-format CTest | HOST-03 | `--print-save-format` for all rows; freeze; 12 seeded controls. |
| W5 | 18-08 installed smoke + docs | all | Install rule for `share/gabbaboy/host-contract.json`; doc-contract checks; `docs/support/unreleased.md` entries; PLAYSTEAD-CONTRACT MBC2 correction. |
| gap | 18-09 reserved | - | A 50% overrun means rescope (>= 13 plans is out of cap anyway). |

18-05 and 18-06 can run in parallel only if 18-06's inventory edits happen in a different commit window than 18-05's player inventory (they touch different inventory files: `tests/player/expected-tests.txt` vs `tests/expected-tests.txt`).

## Sources

### Primary (HIGH confidence)
- Repository files read this session: `18-CONTEXT.md`, `include/gabbaboy/gabbaboy.h`, `src/core/gabbaboy.c` (cartridge table, battery/state API, queue), `src/runner/main.c`, `CMakeLists.txt`, `cmake/CheckCoreNoHostClock.cmake`, `cmake/ExpectedTests.cmake`, `.github/scripts/verify-test-inventory.sh`, `.github/workflows/ci.yml`, `tests/CMakeLists.txt`, `tests/player/CMakeLists.txt`, `tests/player/test_limitations.c`, `tests/player/claims_agree.cmake`, `tests/expect_exit.cmake`, `cmake/VerifyDocContract.cmake`, `cmake/VerifyInstalledPackage.cmake`, `tests/scripts/verify-core-linkage.py`, `tests/scripts/verify-model-gates.py`, `src/player/{main,session,input}.{c,h}`, `.planning/context/LESSONS.md` (GB-CGB-007, GB-CART-003, GB-CI-012, GB-GSD-029), `~/projects/playstead/.../SaveSessionCoordinator.swift`.
- Local probes (scratchpad, this session): macOS arm64 Apple clang 21 and Docker `gcc:13` strict `-std=c17` for POSIX calls/flags, dangling symlink and FIFO behaviour, `nanosleep` EINTR under `SA_RESTART|SA_RESETHAND`, `clock_nanosleep` absence on macOS, fsync cost, Debug frame cost, halted/stopped `gbb_run` results.
- POSIX.1-2017 `nanosleep` and `sigaction` pages (opengroup.org) - SA_RESETHAND/SA_RESTART definitions, EINTR semantics.

### Secondary (MEDIUM confidence)
- `.planning/research/v0.3/PLAYSTEAD-CONTRACT.md` (pin shape, SIGTERM then SIGKILL ~2 s); CERT SIG30-C/SIG31-C as cited in CONTEXT D-13.

### Tertiary (LOW confidence)
- None used as a basis for a recommendation; unverified items are in the Assumptions Log.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - no new dependencies; compile and runtime behaviour probed on both Unix families.
- Architecture: HIGH - follows locked decisions; module boundaries checked against `verify-core-linkage.py`, dirty list and symbol-check conventions.
- Pitfalls: HIGH for repo-specific ones (read in source); MEDIUM for hosted-runner timing (A4) and SDL menu key binding (A2).

**Research date:** 2026-10-28
**Valid until:** 2026-11-27 (stable POSIX/C; re-check line anchors if `src/runner/main.c` or the inventories change before planning)
