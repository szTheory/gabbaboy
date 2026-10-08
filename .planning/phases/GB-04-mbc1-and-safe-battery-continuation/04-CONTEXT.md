# Phase 4: MBC1 and Safe Battery Continuation - Context

**Gathered:** 2026-10-08
**Status:** Ready for planning

<domain>
## Phase Boundary

Deliver declared standard MBC1 support for the existing bootless DMG-CPU-B profile, including bounded ROM/RAM banking and battery-backed cartridge RAM, then persist that RAM safely in the optional macOS SDL player. An original, reproducible Game Boy fixture must write meaningful guest progress, exit, reopen in a distinct fresh process, and take behavior that depends on the previous bytes. The exact supported cartridge matrix, save identity, recovery behavior, and evidence contract below bound the work.

This phase does not add MBC1M support, MBC2/MBC3/MBC5, RTC, CGB, full machine snapshots, a game library, general save-management UI, raw cross-emulator `.sav` import/export, or claims of physical hardware measurement. Existing C17, bounded-call, explicit-ownership, no-telemetry, no-unlicensed-fixture, and phase-pause constraints continue to apply.
</domain>

<decisions>
## Implementation Decisions

### Standard MBC1 support envelope

- **D-01:** Support ordinary documented MBC1 wiring up to 2 MiB ROM. Accept cartridge types `$01` (MBC1 without RAM), `$02` (MBC1 with volatile RAM), and `$03` (MBC1 with battery-backed RAM), subject to a strict header matrix. Accept power-of-two ROM size codes `$00`–`$06` (32 KiB–2 MiB). Accept RAM size codes for no RAM, 8 KiB, or 32 KiB only where the declared wiring supports them: 32 KiB RAM only through 512 KiB ROM; 1–2 MiB MBC1 RAM configurations are limited to 8 KiB. Reject contradictory type/RAM declarations, 2 KiB and larger uncommon RAM codes, irregular ROM sizes `$52`–`$54`, ROMs above 2 MiB, and all other mapper types before allocation or live-state mutation.
- **D-02:** Implement the standard MBC1 registers and both modes from the documented address-line behavior. Preserve the low and upper bank-register values separately; translate low ROM bank `$00` to `$01` before applying ROM-size masking. Mode 0 fixes the lower ROM/RAM windows to bank zero; mode 1 applies the secondary register to the lower ROM window and, where present, banked RAM. The RAM gate enables on a low nibble of `$A`; disabled RAM writes are ignored. Where hardware references leave unmapped/disabled reads undefined, use the core's deterministic `$FF` software policy and do not call it a universal hardware value.
- **D-03:** MBC1M is outside the support claim. Its header type is not distinct from standard MBC1. Use a conservative documented alternate-bank logo/header check to reject clearly recognized multicart candidates with an explicit unsupported-variant result; do not infer wiring from a title or apply broad content heuristics. Document that no ROM-header-only rule identifies every MBC1M dump, so an unrecognized special-wiring image is outside the qualified support set.
- **D-04:** Cross-check mapping and loader behavior against Pan Docs, Gekkio's cartridge reference, and established emulator source, but keep source agreement separate from hardware-backed proof. Mooneye `emulator-only/mbc1` cases are candidate software regressions only; pin and review any admitted case's exact source, rights, applicability, protocol, and expected result before adding it to a required denominator.

### Cartridge RAM and public API boundary

- **D-05:** Keep cartridge RAM instance-owned and bounded to the supported maximum of 32 KiB. A missing battery file initializes RAM to `$FF` as a deterministic emulator policy, not a claim about physical SRAM power-up. Volatile MBC1 RAM remains available during the loaded session but is not exported as a battery save. A soft `gbb_reset` resets CPU and mapper controls while preserving that cartridge's RAM; successful ROM replacement starts an independent RAM image. The player flushes dirty battery RAM before reset, replacement, and orderly exit.
- **D-06:** Expose battery data through bounded caller-owned size/copy/import/export operations. Do not return a mutable pointer or add filesystem operations to the portable core. Imports require the exact supported length and validate completely before any live RAM changes; malformed input leaves the instance unchanged. File identity, envelope parsing, atomic replacement, and error presentation belong to the player adapter. Keep the core standard-library-only and do not add a third-party persistence or serialization dependency.

### Player save identity, file format, and feedback

- **D-07:** Store player-managed saves under SDL3's per-user, per-application writable data path (`SDL_GetPrefPath`), not beside the ROM. Key each file by the exact ROM-byte SHA-256 plus mapper/type/RAM identity so read-only ROM folders, duplicate filenames, and moving a ROM do not redirect its save. Compute the digest in the macOS player with the platform-provided crypto API; do not add a third-party package or put crypto/filesystem dependencies in the core. A digest is an identity key, not an authentication mechanism.
- **D-08:** Use one small, fixed-endian, versioned GabbaBoy save envelope containing a magic/version, exact ROM digest, cartridge type, RAM length, payload checksum, and raw battery RAM. Reject truncation, trailing bytes, unsupported versions, wrong ROM/type/length, and checksum failures. Bound reads to the maximum supported payload plus the fixed header. Do not serialize native C structures. Do not auto-detect or import raw `.sav` files in this phase; later interchange must be an explicit, separately documented format with its own validation and migration contract. **Reversibility:** costly — changing the saved-file format later must preserve existing player progress through a reviewed migration or retain the older file.
- **D-09:** Keep player UX small: show concise loading/saved/saving/failure status through the existing window title/help surface, and document where managed saves live. Do not add a library, preferences screen, manual file picker, or general save manager. A write failure remains visible until success or an explicit exit choice; the status must distinguish a durable success from dirty data still held only in memory.

### Save cadence, recovery, and writer conflicts

- **D-10:** Save only when battery RAM has changed, and mark it dirty only when a write changes a byte. Coalesce guest writes with a short quiet debounce and a maximum dirty-age checkpoint; use 2 seconds quiet and 10 seconds maximum as the initial product defaults. Flush dirty data before orderly quit, ROM replacement, and soft reset. Do not write the disk once per guest store. Exact timing may be tuned during implementation if measurements show a practical issue, while retaining a documented upper bound on ordinary crash-loss exposure.
- **D-11:** Replace files by creating a unique temporary file in the same directory, writing the full bounded envelope, syncing the temporary data, atomically renaming it over the target, and syncing the containing directory where supported. Never truncate the current target in place. A failure before replacement leaves the prior complete save intact; retain dirty RAM in memory, show the error, and retry. If a final flush blocks quit/reset/replacement, offer retry, cancel, or an explicit continue-without-saving path rather than silently dropping progress. Atomic rename protects readers from partial files; do not claim power-loss durability beyond the actual filesystem sync guarantees and tests.
- **D-12:** Read only bounded regular save files, use exclusive temporary creation, and reject symlink or special-file targets. If a save is malformed, wrong-version, or identity-mismatched, never import or overwrite it silently. Preserve it under a unique recovery name before starting from fresh `$FF` RAM and show a clear warning. If preservation cannot be completed, leave the original untouched and keep persistence disabled for that session rather than replacing it. Do not create zero-byte save files for cartridges without battery-backed RAM.
- **D-13:** Hold a nonblocking exclusive OS advisory lock on a stable per-save lock file for the life of a battery-backed player session. If another GabbaBoy process owns that save, reject the second writable session with an actionable message; do not use last-writer-wins or attempt to merge state. Document that advisory locks protect cooperating GabbaBoy processes only, not external editors.

### Acceptance evidence

- **D-14:** Build a project-authored original MBC1 battery fixture using the existing pinned RGBDS 1.0.1 reproduction path. One process must execute the guest behavior that changes cartridge RAM and persist it; a separate process must load the same ROM/save and take a success path that depends on those prior bytes. Missing-save and wrong-ROM controls must take distinguishable paths. Preserve fixture source, notice/license, exact bytes/digest, build recipe/tool identity, DMG-CPU-B/bootless applicability, protocol, and timeout. No commercial ROM or private save enters the repository.
- **D-15:** Keep mapper, save API, file-adapter, and guest-continuation assertions separate. Use original synthetic bank-pattern ROMs with independently authored expected values for bank windows, mode changes, zero-bank translation, RAM enable/disable, RAM mirroring/banking, and supported header combinations. Test exact-size 8/32 KiB battery round trips, no-RAM/nonbattery behavior, fresh initialization, reset/replacement semantics, wrong identity, malformed/oversized/truncated inputs, unchanged state on rejection, output bounds, and concurrent instances. Compile relocated installed C and C++ consumers against the new battery API. Fault-inject temp creation, short write, sync, rename, lock, and recovery failures; verify process interruption yields the old complete save or the new complete save, never a partial target. Keep tests named in CTest inventory and run bounded battery/API fuzzing under the existing sanitizer setup. Public logs/artifacts must not expose local ROM/save paths or private save contents.
- **D-16:** Label documented, inferred/software-model, emulator-differential, and physical-hardware evidence separately. Phase 4 may make a deterministic software-model claim from high-quality cartridge documentation and source cross-checks; it must not claim physical CPU-B/MBC1 qualification without an identified hardware observation.

### the agent's Discretion

- Select internal mapper and RAM representations and public API symbol/error names, provided the decisions above, existing per-instance ownership, and failure atomicity hold.
- Choose the exact byte layout for version 1 after documenting the field sizes, endianness, checksum purpose, and maximum accepted file size; use platform SHA-256 for ROM identity and a bounded checksum for accidental save corruption, not a MAC or security claim.
- Choose the smallest stable status wording and recovery filename suffix that fit the existing player. Preserve rejected data and make the consequence obvious without introducing a UI framework.
- Pin and classify any optional external MBC1 oracle before admission; owned tests remain the required baseline if rights or applicability are not closed.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Scope and owner constraints
- `AGENTS.md` — portable C17, dependency, privacy, evidence, and phase-pause rules.
- `.planning/PROJECT.md` — GB/GBC identity, core/player boundary, and safety constraints.
- `.planning/REQUIREMENTS.md` §Cartridge banking and battery continuation — locked SAVE-01 through SAVE-04 acceptance.
- `.planning/ROADMAP.md` §Phase 4 — phase goal, success criteria, scope, and dependency.
- `.planning/STATE.md` — current Phase 4 handoff and workflow state.
- `.planning/context/BRIEF.md` — owner priorities, including a small dependency tree.
- `.planning/context/DECISIONS.md` — D-006 (scoped MBC1), D-011 (host-owned battery files separate from snapshots), D-013 (original fixture), D-015 (evidence classes), D-025 (confidence-qualified software models).
- `.planning/context/WORKFLOW.md` — authorized phase progression and pause policy.

### Hardware, evidence, and safety research
- `.planning/research/INDEX.md` — research routing, provenance, and confidence rules.
- `.planning/research/HARDWARE-AND-VALIDATION.md` §Cartridge validation — header checks, model applicability, fixture and oracle policy.
- `.planning/research/ARCHITECTURE.md` §Cartridges, time and persistence — mapper/core/host seams and battery versus snapshot boundaries.
- `.planning/research/PITFALLS.md` — false oracle, untrusted input, save loss, and test-gate failure modes.
- `.planning/research/QUALITY-AND-DELIVERY.md` — current CI, sanitizer, fixture-reproduction, and package-smoke conventions.

### Prior phase contracts and implementation surfaces
- `.planning/phases/GB-01-portable-foundation-and-original-rom-tracer/01-CONTEXT.md` — bounded caller-owned API, instance ownership, dependency rule, and fixture provenance.
- `.planning/phases/GB-02-dmg-cpu-bus-and-time/02-CONTEXT.md` — cartridge-space error behavior, timed bus, and model-qualified test decisions.
- `.planning/phases/GB-03-visible-interactive-dmg/03-CONTEXT.md` and `03-RESEARCH.md` — SDL player behavior, transactional ROM replacement, fixture workflow, and D-025 evidence boundary.
- `include/gabbaboy/gabbaboy.h` and `src/core/gabbaboy.c` — public API, loader, current ROM-only mapping, bus access, reset, and instance lifecycle.
- `src/player/session.c`, `src/player/session.h`, and `src/player/main.c` — bounded ROM file load, current session replacement/reset, status, and quit integration points.
- `tests/test_loader.c`, `tests/test_bus.c`, `tests/test_api.c`, `tests/CMakeLists.txt`, `tests/player/CMakeLists.txt`, and `tests/expected-tests.txt` — negative-input, bus, API, inventory, and player test patterns.
- `fixtures/visible-demo/manifest.json`, `fixtures/visible-demo/demo.asm`, and `tests/scripts/reproduce-visible-demo.sh` — original fixture and pinned RGBDS reproduction precedent.
- `.github/workflows/ci.yml`, `.github/workflows/fixture-repro.yml`, and `.github/workflows/preview.yml` — existing required-test, fixture, and packaged-player CI paths.

### Primary external technical references
- [Pan Docs — MBC1](https://gbdev.io/pandocs/MBC1.html) — documented bank registers, type/size restrictions, RAM gating, and MBC1M distinctions.
- [Pan Docs — cartridge header](https://gbdev.io/pandocs/The_Cartridge_Header.html) — cartridge type and declared ROM/RAM sizes.
- [Gekkio, Game Boy: Complete Technical Reference, §12–13](https://gekkio.fi/files/gb-docs/gbctr.pdf) — cartridge mapping, MBC1 modes, multicart wiring/detection, and undefined reads.
- [SDL3 `SDL_GetPrefPath`](https://wiki.libsdl.org/SDL3/SDL_GetPrefPath) — existing SDL API intended for per-user app files, including save games.
- [POSIX `rename()`](https://pubs.opengroup.org/onlinepubs/9799919799/functions/rename.html) — same-filesystem replacement semantics.
- [Apple `flock(2)`](https://developer.apple.com/library/archive/documentation/System/Conceptual/ManPages_iPhoneOS/man2/flock.2.html) — advisory exclusive-lock semantics and limits.
- [Apple File System Programming Guide](https://developer.apple.com/library/archive/documentation/FileManagement/Conceptual/FileSystemProgrammingGuide/FileSystemOverview/FileSystemOverview.html) — Application Support ownership and file placement.
- [Apple Common Crypto](https://developer.apple.com/library/archive/documentation/System/Conceptual/ManPages_iPhoneOS/man3/CC_crypto.3cc.html) — system-provided hashing available to the macOS player without a packaged dependency.

### Cross-checks, not hardware proof
- [SameBoy SDL frontend](https://github.com/LIJI32/SameBoy/blob/master/SDL/main.c) and [battery API](https://github.com/LIJI32/SameBoy/wiki/GB_save_battery) — established save API/frontend patterns; do not copy code or treat as hardware truth.
- [Mooneye emulator-only MBC1 tests](https://github.com/Gekkio/mooneye-test-suite/tree/main/emulator-only/mbc1) — candidate software regressions only; pin revision and inspect rights/applicability before admission.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `gbb_instance` in `src/core/gabbaboy.c` already owns machine state, a private ROM copy, and bounded RAM arrays; extend it for cartridge RAM and mapper registers without introducing globals.
- `gbb_load_rom` validates before allocating/replacing and leaves a loaded instance untouched on failure. Preserve this transactional replacement behavior while adding supported cartridge matrices and exact ROM lengths.
- `include/gabbaboy/gabbaboy.h` already defines bounded errors, explicit model profile, and copy-based output contracts. Add bounded battery APIs in the same style.
- `src/player/session.c` owns file loading and path replacement, while `src/player/main.c` handles reset/ROM swap/quit and already displays concise session status in the title and F1 help. These are direct host-persistence integration points.
- CTest has explicit inventories, a portable core suite, optional player tests, a pinned RGBDS fixture reproduction workflow, and package smoke checks. Extend those instead of adding a test framework or network-dependent ordinary build.

### Established Patterns
- The core has no SDL or filesystem dependency; host I/O stays in the adapter. Each core instance is single-threaded and independently owned.
- Inputs and frame outputs are bounded, caller-owned, and transactional. Rejected ROM replacement preserves the prior session. Apply that discipline to battery imports and failed save transitions.
- Normal builds use checked-in ROM bytes and run offline; fixture reproduction is separately pinned to RGBDS 1.0.1. Reuse this path for the original MBC1 continuation fixture.
- The declared profile remains bootless DMG-CPU-B. D-025 allows deterministic software choices with explicit evidence limits; no physical MBC1 measurement is present.

### Integration Points
- Extend loader validation and `read8`/`write8` mapping for ROM banks, MBC1 control registers, RAM enable/mode/bank, and bounded cartridge RAM.
- Add caller-owned battery size/copy/import/export boundaries and preserve cartridge RAM across soft reset while isolating ROM replacement.
- Extend player session lifecycle to locate, validate, lock, load, autosave, atomically replace, and report errors for one ROM's battery data.
- Add original fixture source/manifest/binary/reproduction, separate synthetic mapping tests, player file-failure and multi-process tests, test-inventory entries, docs, and exact-head CI coverage together.
</code_context>

<specifics>
## Specific Ideas

- The owner explicitly asked for breadth/depth across security, hardware, product, architecture, host filesystem, UX, and test/evidence roles, using primary sources where possible, and authorized the recommendation-led choices captured here.
- Three independent specialist reviews converged on strict standard-MBC1 support, bounded core battery APIs, application-owned identity-bound files, atomic writes, and single-writer protection. Pan Docs and Gekkio are the mapping basis; emulator sources are only cross-checks.
- SHA-256 and a payload checksum prevent accidental cross-ROM association and corruption from going unnoticed; neither authenticates a save against a malicious editor.
- A clean close or normal process restart is testable; CI process-kill tests do not establish physical power-loss behavior of storage hardware.
</specifics>

<deferred>
## Deferred Ideas

- MBC1M emulation, broader MBC support, RTC, CGB, and native save states remain in later roadmap scope.
- Raw `.sav` interchange, user-selected save paths, save browsing/management UI, and conflict merging require a separate explicit design and are not implied by this envelope.
- No phase-matching pending todos were found.
</deferred>

---

*Phase: 4-MBC1 and Safe Battery Continuation*
*Context gathered: 2026-10-08*
