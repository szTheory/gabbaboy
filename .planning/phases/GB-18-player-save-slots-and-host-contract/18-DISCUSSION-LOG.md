# Phase 18: Player Save Slots and Host Contract - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-10-28
**Phase:** 18-player-save-slots-and-host-contract
**Areas discussed:**
- A. Host binary and mode
- B. Player slot design
- C. Atomic `.sav` persistence
- D. Signals and exit codes
- E. Save-format ids
- G. Gap sweep (cross-cutting)

**Method:** the owner pasted the standing fan-out instruction (see the [[discuss-fanout-auto-follow]] memory). Six parallel advisor tracks ran, each across multiple lenses and with its own adversarial pass:
- C/POSIX;
- SDL frontend;
- security/TOCTOU;
- host integrator (Playstead);
- QA/CI;
- release;
- product/UX.

The tracks drew on primary sources: POSIX, Apple and Microsoft documentation, CERT, the SDL3 source, the mGBA, SameBoy, RetroArch and Dolphin sources, and sibling cores. The merged draft then went to an independent adversarial review. The resulting recommendations were adopted without per-question prompts.

---

## A. Host binary and mode

| Option | Description | Selected |
|--------|-------------|----------|
| SDL player host mode | The playable binary. macOS-only, no ASan, absent from release workflows, and needs SDL signal-hint and quit-prompt bypass work. | |
| Headless runner plus a reusable `gabbaboy_host` module | Matches the requirement text and D-104. Cross-platform, strict C17, single-threaded, release-built. The player and Playstead reuse the module later (RM-020). | ✓ |
| New small binary | Either headless, so the same limits as the runner, or a duplicate of the SDL frontend. | |

**Choice:** runner plus module. Pacing is real time by default, with a `--frames N` batch shape, and a frame is one fixed 140,448 half-dot step.
**Conflict resolved:** track A preferred the player. Tracks C, D, E and G and the adversarial review chose the runner; host mode is documented as "not a play surface".

## B. Player slot design

| Option | Description | Selected |
|--------|-------------|----------|
| Select then act: 1–9 select, ⌘S/⌘L, ⌘Z undo swap; raw state bytes in the pref dir | Picking a slot destroys nothing, and there are no key collisions. | ✓ |
| One chord per slot (SameBoy ⌘N/⇧⌘N, mGBA F-keys) | Collides with ⇧⌘3/4/5 screenshot shortcuts and F1 Help. No undo. | |

**Choice:** select, then act.
**Adversarial additions:**
- a guarded battery-preload backup, so "load A, then load B" keeps the in-game save;
- the read-only `gbb_get_input_clock` getter, reshaped by the review to return the queue count and the last queued time instead of the earliest.

The gap sweep wanted no core change at all. That was overridden on the evidence that input breaks after a load without the getter.

## C. Atomic `.sav` persistence

| Option | Description | Selected |
|--------|-------------|----------|
| Portable dir-fd helper (`openat` O_EXCL temp, F_FULLFSYNC/fsync, `renameat`, dir fsync) | No path TOCTOU, and concurrent writers cannot tear a file. | ✓ |
| Path-based writer (nesturbator-style), Windows included | Path re-resolution TOCTOU, a fixed temp name, no directory fsync. | |

**Choice:** the dir-fd helper. Adjustments:
- symlinks are allowed in save-dir path components (macOS `/tmp`);
- the basename strips any 1–8 alphanumeric extension rather than using an allow-list (review F9);
- the temp sweep has no pid-liveness heuristic (review F13);
- an absent file is always created at the first or final flush (review F4);
- the RTC-drift compare runs every 3,600 frames (review F12).

## D. Signals and exit codes

| Option | Description | Selected |
|--------|-------------|----------|
| `sigaction` flag with SA_RESTART\|SA_RESETHAND; exits 0 clean, 1 failure, 2 refusal; crash = signal death | Matches Dolphin NoGUI and the existing runner's use of 2. | ✓ |
| sysexits plus self-pipe plus a test crash hook | Conflicts with existing codes; 77 means "skip" to CTest; a crash hook is a backdoor. | |

**Choice:** option 1.
**Review changes:**
- "finished the frame" is proved by a deterministic `--frames K` replay instead of a self-reported counter;
- the 2 s ceiling is asserted only in lanes without sanitizers;
- SIGHUP honours an inherited SIG_IGN;
- the crash row uses repeated SIGKILL;
- the core no-signal check extends `CheckCoreNoHostClock.cmake` rather than adding a new script;
- three decoys instead of eight.

Track A's 2 = usage / 3 = refusal split was rejected, because MSVC's `abort()` exits 3.

## E. Save-format ids

| Option | Description | Selected |
|--------|-------------|----------|
| Hand-written canonical JSON checked against runner output and core admission | Not circular; ids are append-only. | ✓ |
| Runner-generated table with a diff check | Circular; makes breaking changes easy to approve silently. | |

**Choice:** a hand-written `docs/host-contract.json` that merges save formats and exit codes. Ids carry no release version and no gb/gbc axis. 16 rows, 12 ids.
**Review changes:**
- the completeness enumeration runs in process;
- the freeze distinguishes "file absent at tag" from "no tags".

## G. Gap sweep (adopted)

- Branch from `main` after the PR130 squash merge. The release-please PR stays unmerged and VERSION is not bumped.
- No committed state-byte fixtures.
- Public-API-only is enforced with a symbol check.
- The `GBB_BUILD_QUALIFIED` dirty-list subset check.
- Windows refusal.
- No RTC catch-up in host mode.
- Installed host smoke.
- Docs updated together.
- A hostile-file sweep instead of a new fuzz target.

## Claude's Discretion

- Internal file and function names.
- `gbb-host:` diagnostic wording, beyond the fields the tests rely on.
- Synthetic fixture layout.

## Deferred Ideas

See CONTEXT.md `<deferred>`: player and Playstead host play (RM-020), the mGBA RTC footer (RM-021), libretro, rewind and thumbnails, host RTC catch-up, a Windows host mode, power-loss durability, locking, player SIGTERM handling, writer convergence, and the Phase 19 entry items.
