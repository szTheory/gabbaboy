# Phase 4: MBC1 and Safe Battery Continuation - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in `04-CONTEXT.md` — this log preserves the alternatives considered.

**Date:** 2026-10-08
**Phase:** 4-MBC1 and Safe Battery Continuation
**Areas discussed:** Standard MBC1 support envelope; battery API and save identity; automatic saves and player feedback; failure recovery and concurrent use; continuation evidence.

The owner requested all areas be explored broadly and deeply, then explicitly authorized recommendation-led decisions without pausing for routine preference questions. Three independent specialist reviews covered MBC1 hardware scope, battery API/data safety, and player/filesystem behavior. Recommendations were checked against the current codebase and primary documentation. The selection marks below record the synthesized recommendation the owner authorized, not a claim that the owner separately selected each row in an interactive menu.

---

## Standard MBC1 support envelope

| Option | Description | Selected |
|--------|-------------|----------|
| Limit standard ROMs to 512 KiB | Simpler wiring and 32 KiB RAM combinations, but omits documented 1–2 MiB MBC1 configurations. | |
| Standard MBC1 through 2 MiB with a strict type/size matrix | Supports types `$01`/`$02`/`$03`, power-of-two ROMs through 2 MiB, and only documented 8/32 KiB RAM combinations. Clearly excludes uncommon sizes and other mappers. | ✓ |
| Guess broadly, or add MBC1M support now | More dumps may run, but MBC1M uses alternate wiring and shares ordinary header types; loose guessing can silently select wrong ROM banks and corrupt progress. | |

**Owner's direction:** Consider all alternatives and automatically follow the synthesized recommendation.
**Notes:** D-025 supports a deterministic documented software model while labeling evidence limits. Pan Docs describes the large-ROM/fixed-8 KiB RAM split; Gekkio documents MBC1M wiring and logo/header heuristics. MBC1M remains outside the support claim; clearly recognized candidates should fail explicitly, but detection is not described as universal. Emulator-only Mooneye cases are not physical proof.

---

## Battery API and save identity

| Option | Description | Selected |
|--------|-------------|----------|
| Raw `.sav` beside the ROM | Familiar and easy to transfer, but can fail in read-only folders, collide by filename, and cannot detect a wrong ROM with a same-sized raw file. | |
| Versioned app-owned save keyed by exact ROM identity | Uses SDL's app-specific writable path, content identity, a bounded versioned envelope, and exact RAM size; less directly interoperable with other emulators. | ✓ |
| Both wrapped native saves and automatic raw import/export | Adds user choice, but creates two formats and another path for wrong-ROM or malformed imports. | |

**Owner's direction:** Consider all alternatives and automatically follow the synthesized recommendation.
**Notes:** The core exposes bounded caller-owned battery data operations only; the player owns the file path and envelope. Use exact ROM SHA-256 plus mapper/type/RAM identity, a payload checksum, and fixed-endian serialization. Raw `.sav` interchange is deferred until a deliberate migration/import contract exists. Use system crypto in the macOS adapter rather than a third-party package or crypto implementation in the portable core.

---

## Automatic saves and player feedback

| Option | Description | Selected |
|--------|-------------|----------|
| Save only at quit | Few writes, but crashes can lose an entire session and replacement/reset handling is easy to miss. | |
| Write to disk after every guest RAM write | Small nominal loss window, but converts ordinary emulated stores into excessive host I/O. | |
| Debounced dirty saves with a maximum delay and transition flushes | Coalesces writes, bounds ordinary crash-loss exposure, and flushes before orderly quit, reset, or ROM replacement. | ✓ |

**Owner's direction:** Consider all alternatives and automatically follow the synthesized recommendation.
**Notes:** Start with a 2-second quiet debounce and a 10-second maximum dirty age; tune only with evidence while retaining a documented bound. Show concise save status and failure in the existing title/help surface; document the save location without adding a general settings or library UI. Soft reset preserves cartridge RAM, while a new ROM gets a separate RAM image.

---

## Failure recovery and concurrent use

| Option | Description | Selected |
|--------|-------------|----------|
| Overwrite in place and let the last writer win | Lowest code count, but a short write or two live processes can destroy a complete prior save. | |
| Temporary file plus atomic rename; preserve rejected files; one advisory writer lock | Keeps the old target until a complete new file is ready, retains malformed saves for recovery, and prevents competing GabbaBoy sessions from racing. | ✓ |
| Keep rolling timestamped backups and merge concurrent saves | More recovery history, but adds cleanup, conflict UI, and merge semantics that cartridge RAM does not define. | |

**Owner's direction:** Consider all alternatives and automatically follow the synthesized recommendation.
**Notes:** Create the temp file exclusively in the same directory, sync it before rename, and sync the directory where supported. Never claim this proves physical power-loss durability. A bad/mismatched file is not loaded or overwritten silently: preserve it under a unique recovery name, start from deterministic `$FF` RAM with a visible warning, and disable saves if preservation itself fails. Keep dirty data in memory and retry write failures; make final quit/reset/swap choices explicit. `flock` is advisory and protects only cooperating GabbaBoy processes.

---

## Continuation evidence

| Option | Description | Selected |
|--------|-------------|----------|
| API byte-copy round-trip | Verifies the buffer contract but can pass without proving guest progress resumes. | |
| Separate-process guest continuation plus negative controls | One process writes meaningful battery state; a fresh process branches on that state, while missing-save and wrong-ROM controls take different paths. | ✓ |
| Screenshot or visual demo | Useful for UI smoke only; cannot prove battery continuation. | |

**Owner's direction:** Consider all alternatives and automatically follow the synthesized recommendation.
**Notes:** Use an original project-authored fixture, the already-pinned RGBDS path, and synthetic independently expected bank-pattern tests. Keep API, mapper, file-failure, and fresh-process guest outcomes distinct. Do not add commercial ROMs, private saves, or unreviewed fixtures.

---

## the agent's Discretion

Choose internal mapper/RAM data structures, public API names and exact fixed-endian save-header layout, provided the bounds, identity checks, transactional behavior, and evidence requirements in `04-CONTEXT.md` remain intact. Keep the current core dependency-free. Pin and classify any optional third-party MBC1 test before admission; owned tests are the required floor.

## Deferred Ideas

MBC1M emulation, MBC2/MBC3/MBC5, RTC, CGB, snapshots, raw `.sav` interoperability, manual save management, and save conflict merging remain outside Phase 4.
