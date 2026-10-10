# Phase 4: MBC1 and Safe Battery Continuation — Research

**Researched:** 2026-10-07
**Domain:** Portable C17 cartridge mapping and macOS SDL3 battery-save adapter
**Confidence:** HIGH for the project contracts and software-model design; MEDIUM for mapping documented in reverse-engineering sources; LOW for any claim of physical DMG-CPU-B hardware qualification.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### Standard MBC1 support envelope

- **D-01:** Support ordinary documented MBC1 wiring up to 2 MiB ROM. Accept cartridge types `$01` (MBC1 without RAM), `$02` (MBC1 with volatile RAM), and `$03` (MBC1 with battery-backed RAM), subject to a strict header matrix. Accept power-of-two ROM size codes `$00`–`$06` (32 KiB–2 MiB). Accept RAM size codes for no RAM, 8 KiB, or 32 KiB only where the declared wiring supports them: 32 KiB RAM only through 512 KiB ROM; 1–2 MiB MBC1 RAM configurations are limited to 8 KiB. Reject contradictory type/RAM declarations, 2 KiB and larger uncommon RAM codes, irregular ROM sizes `$52`–`$54`, ROMs above 2 MiB, and all other mapper types before allocation or live-state mutation.
- **D-02:** Implement the standard MBC1 registers and both modes from the documented address-line behavior. Preserve the low and upper bank-register values separately; translate low ROM bank `$00` to `$01` before applying ROM-size masking. Mode 0 fixes the lower ROM/RAM windows to bank zero; mode 1 applies the secondary register to the lower ROM window and, where present, banked RAM. The RAM gate enables on a low nibble of `$A`; disabled RAM writes are ignored. Where hardware references leave unmapped/disabled reads undefined, use the core's deterministic `$FF` software policy and do not call it a universal hardware value.
- **D-03:** MBC1M is outside the support claim. Its header type is not distinct from standard MBC1. Use a conservative documented alternate-bank logo/header check to reject clearly recognized multicart candidates with an explicit unsupported-variant result; do not infer wiring from a title or apply broad content heuristics. Document that no ROM-header-only rule identifies every MBC1M dump, so an unrecognized special-wiring image is outside the qualified support set.
- **D-04:** Cross-check mapping and loader behavior against Pan Docs, Gekkio's cartridge reference, and established emulator source, but keep source agreement separate from hardware-backed proof. Mooneye `emulator-only/mbc1` cases are candidate software regressions only; pin and review any admitted case's exact source, rights, applicability, protocol, and expected result before adding it to a required denominator.

#### Cartridge RAM and public API boundary

- **D-05:** Keep cartridge RAM instance-owned and bounded to the supported maximum of 32 KiB. A missing battery file initializes RAM to `$FF` as a deterministic emulator policy, not a claim about physical SRAM power-up. Volatile MBC1 RAM remains available during the loaded session but is not exported as a battery save. A soft `gbb_reset` resets CPU and mapper controls while preserving that cartridge's RAM; successful ROM replacement starts an independent RAM image. The player flushes dirty battery RAM before reset, replacement, and orderly exit.
- **D-06:** Expose battery data through bounded caller-owned size/copy/import/export operations. Do not return a mutable pointer or add filesystem operations to the portable core. Imports require the exact supported length and validate completely before any live RAM changes; malformed input leaves the instance unchanged. File identity, envelope parsing, atomic replacement, and error presentation belong to the player adapter. Keep the core standard-library-only and do not add a third-party persistence or serialization dependency.

#### Player save identity, file format, and feedback

- **D-07:** Store player-managed saves under SDL3's per-user, per-application writable data path (`SDL_GetPrefPath`), not beside the ROM. Key each file by the exact ROM-byte SHA-256 plus mapper/type/RAM identity so read-only ROM folders, duplicate filenames, and moving a ROM do not redirect its save. Compute the digest in the macOS player with the platform-provided crypto API; do not add a third-party package or put crypto/filesystem dependencies in the core. A digest is an identity key, not an authentication mechanism.
- **D-08:** Use one small, fixed-endian, versioned GabbaBoy save envelope containing a magic/version, exact ROM digest, cartridge type, RAM length, payload checksum, and raw battery RAM. Reject truncation, trailing bytes, unsupported versions, wrong ROM/type/length, and checksum failures. Bound reads to the maximum supported payload plus the fixed header. Do not serialize native C structures. Do not auto-detect or import raw `.sav` files in this phase; later interchange must be an explicit, separately documented format with its own validation and migration contract. **Reversibility:** costly — changing the saved-file format later must preserve existing player progress through a reviewed migration or retain the older file.
- **D-09:** Keep player UX small: show concise loading/saved/saving/failure status through the existing window title/help surface, and document where managed saves live. Do not add a library, preferences screen, manual file picker, or general save manager. A write failure remains visible until success or an explicit exit choice; the status must distinguish a durable success from dirty data still held only in memory.

#### Save cadence, recovery, and writer conflicts

- **D-10:** Save only when battery RAM has changed, and mark it dirty only when a write changes a byte. Coalesce guest writes with a short quiet debounce and a maximum dirty-age checkpoint; use 2 seconds quiet and 10 seconds maximum as the initial product defaults. Flush dirty data before orderly quit, ROM replacement, and soft reset. Do not write the disk once per guest store. Exact timing may be tuned during implementation if measurements show a practical issue, while retaining a documented upper bound on ordinary crash-loss exposure.
- **D-11:** Replace files by creating a unique temporary file in the same directory, writing the full bounded envelope, syncing the temporary data, atomically renaming it over the target, and syncing the containing directory where supported. Never truncate the current target in place. A failure before replacement leaves the prior complete save intact; retain dirty RAM in memory, show the error, and retry. If a final flush blocks quit/reset/replacement, offer retry, cancel, or an explicit continue-without-saving path rather than silently dropping progress. Atomic rename protects readers from partial files; do not claim power-loss durability beyond the actual filesystem sync guarantees and tests.
- **D-12:** Read only bounded regular save files, use exclusive temporary creation, and reject symlink or special-file targets. If a save is malformed, wrong-version, or identity-mismatched, never import or overwrite it silently. Preserve it under a unique recovery name before starting from fresh `$FF` RAM and show a clear warning. If preservation cannot be completed, leave the original untouched and keep persistence disabled for that session rather than replacing it. Do not create zero-byte save files for cartridges without battery-backed RAM.
- **D-13:** Hold a nonblocking exclusive OS advisory lock on a stable per-save lock file for the life of a battery-backed player session. If another GabbaBoy process owns that save, reject the second writable session with an actionable message; do not use last-writer-wins or attempt to merge state. Document that advisory locks protect cooperating GabbaBoy processes only, not external editors.

#### Acceptance evidence

- **D-14:** Build a project-authored original MBC1 battery fixture using the existing pinned RGBDS 1.0.1 reproduction path. One process must execute the guest behavior that changes cartridge RAM and persist it; a separate process must load the same ROM/save and take a success path that depends on those prior bytes. Missing-save and wrong-ROM controls must take distinguishable paths. Preserve fixture source, notice/license, exact bytes/digest, build recipe/tool identity, DMG-CPU-B/bootless applicability, protocol, and timeout. No commercial ROM or private save enters the repository.
- **D-15:** Keep mapper, save API, file-adapter, and guest-continuation assertions separate. Use original synthetic bank-pattern ROMs with independently authored expected values for bank windows, mode changes, zero-bank translation, RAM enable/disable, RAM mirroring/banking, and supported header combinations. Test exact-size 8/32 KiB battery round trips, no-RAM/nonbattery behavior, fresh initialization, reset/replacement semantics, wrong identity, malformed/oversized/truncated inputs, unchanged state on rejection, output bounds, and concurrent instances. Compile relocated installed C and C++ consumers against the new battery API. Fault-inject temp creation, short write, sync, rename, lock, and recovery failures; verify process interruption yields the old complete save or the new complete save, never a partial target. Keep tests named in CTest inventory and run bounded battery/API fuzzing under the existing sanitizer setup. Public logs/artifacts must not expose local ROM/save paths or private save contents.
- **D-16:** Label documented, inferred/software-model, emulator-differential, and physical-hardware evidence separately. Phase 4 may make a deterministic software-model claim from high-quality cartridge documentation and source cross-checks; it must not claim physical CPU-B/MBC1 qualification without an identified hardware observation.

### the agent's Discretion

- Select internal mapper and RAM representations and public API symbol/error names, provided the decisions above, existing per-instance ownership, and failure atomicity hold.
- Choose the exact byte layout for version 1 after documenting the field sizes, endianness, checksum purpose, and maximum accepted file size; use platform SHA-256 for ROM identity and a bounded checksum for accidental save corruption, not a MAC or security claim.
- Choose the smallest stable status wording and recovery filename suffix that fit the existing player. Preserve rejected data and make the consequence obvious without introducing a UI framework.
- Pin and classify any optional external MBC1 oracle before admission; owned tests remain the required baseline if rights or applicability are not closed.

### Deferred Ideas (OUT OF SCOPE)

- MBC1M emulation, broader MBC support, RTC, CGB, and native save states remain in later roadmap scope.
- Raw `.sav` interchange, user-selected save paths, save browsing/management UI, and conflict merging require a separate explicit design and are not implied by this envelope.
- No phase-matching pending todos were found.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| SAVE-01 | Core supports declared standard MBC1 ROM/RAM/battery configurations with tested banking and enable rules; excluded variants and mappers error explicitly. | Header/banking model, transactional loader approach, synthetic bank-pattern and bounds cases. |
| SAVE-02 | Frontend imports/exports bounded battery data under documented identity/size rules; malformed imports are non-mutating. | Caller-owned exact-length copy API and import staging contract. |
| SAVE-03 | Player safely persists saves with atomic replacement, recovery, and concurrency policy; failures preserve last good save and are visible. | Envelope, bounded file adapter, lock lifecycle, temp-write-sync-rename procedure and fault injection. |
| SAVE-04 | Original fixture demonstrates fresh-process progress continuation, with missing-save and wrong-ROM controls. | Reproducible original fixture, machine-readable protocol, separate process orchestration, and explicit evidence labels. |
</phase_requirements>

## Summary

Phase 4 should extend the existing ROM-only path with one validated standard MBC1 cartridge descriptor and instance-owned cartridge RAM, then expose that RAM through small caller-owned battery operations. Keep the core standard-library-only. Its loader already validates before allocation and commits the copied ROM only after all current checks pass; the MBC1 loader should preserve this transaction boundary by validating type, ROM/RAM matrix, exact byte length, and any clear MBC1M marker before allocating the ROM and initial RAM candidate. [VERIFIED: src/core/gabbaboy.c:1070-1119]

The SDL player should own the persistence protocol: use SDL3's per-user application path, derive a stable filename from ROM-byte SHA-256 plus cartridge identity, validate a fixed-endian envelope into temporary RAM, and only then import it through the core API. Writes should go to an exclusively created same-directory temporary file, be completely written and synced before replacement, and leave the previous target intact on any pre-rename failure. A stable per-save advisory lock prevents competing GabbaBoy writers. The original authored fixture must prove continuation across separate processes; mapper-unit tests, API safety tests, file fault tests, and guest behavior remain distinct evidence. [CITED: SDL_GetPrefPath; POSIX rename(); Apple flock(2)]

**Primary recommendation:** Implement a narrow explicit MBC1 state machine and exact matrix, keep save bytes behind a transactional bounded C API, and place all hashing, filesystem, locking, debounce, recovery, and user feedback in the player adapter.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Header/type/size validation and bank mapping | API / Backend (portable core) | — | Guest-visible mapping and supported cartridge claims belong to the deterministic machine instance. |
| Cartridge RAM ownership and battery byte copy/import/export | API / Backend (portable core) | Database / Storage (caller-owned buffer) | Core owns guest RAM; caller owns transfer buffers. Core must expose no mutable storage pointer or filesystem behavior. |
| Save identity, envelope, disk IO, locking, recovery, debounce | Browser / Client (SDL player host adapter) | Database / Storage (filesystem) | Host-specific SHA, SDL path, POSIX/macOS syscalls, lifecycle decisions, and status stay outside the portable core. |
| Continuation proof and fixture reproduction | API / Backend + test harness | Frontend Server / SDL process harness | Guest logic proves stored bytes affect later behavior; harness proves an independent process boundary and fixture provenance. |

## Standard Stack

### Core

| Library / facility | Version | Purpose | Why standard |
|-------------------|---------|---------|---------------|
| Existing portable C17 core | C17 (already declared) | Mapper, cartridge RAM, bounded public transfer calls | Satisfies the project's portable embed boundary and adds no core dependency. |
| C standard library | Existing | checked allocation, byte operations, fixed-width arithmetic | Enough for fixed mapper state and bounded RAM; no serializer or crypto library is needed. |
| SDL3 filesystem API | Existing optional SDL3 player | Locate per-user/per-application saves | SDL documents `SDL_GetPrefPath` specifically for application user files including save games; it returns an owned UTF-8 path to free with `SDL_free`. [CITED: https://wiki.libsdl.org/SDL3/SDL_GetPrefPath] |
| macOS CommonCrypto | System framework/API | SHA-256 ROM-byte identity | Locked decision D-07 selects platform crypto and excludes a third-party dependency. [CITED: https://developer.apple.com/library/archive/documentation/System/Conceptual/ManPages_iPhoneOS/man3/CC_crypto.3cc.html] |
| POSIX/macOS file APIs | System | bounded regular-file reads, exclusive lock/temp files, write/sync/rename | Host persistence belongs to player; same-directory replacement and advisory locking are available without adding a package. [CITED: https://pubs.opengroup.org/onlinepubs/9799919799/functions/rename.html; https://developer.apple.com/library/archive/documentation/System/Conceptual/ManPages_iPhoneOS/man2/flock.2.html] |

### Alternatives Considered

| Instead of | Could use | Tradeoff |
|------------|-----------|----------|
| Project-owned envelope in SDL preference directory | Raw `.sav` beside ROM | Rejected by locked scope: breaks identity across duplicate/moved ROMs, assumes writable ROM directory, and has no version or corruption check. |
| Platform CommonCrypto | New bundled SHA-256 package | Rejected: increases dependency tree and duplicates a platform facility; digest is only identity, not authentication. |
| POSIX/macOS adapter code | Add a persistence/serialization library | Rejected by D-06 and owner preference for a small dependency tree; this envelope is fixed-size/simple enough to audit directly. |

**Installation:** No external package installation is required for this phase. Reuse the repository's pinned SDL3 and RGBDS fixture-reproduction setup; the ordinary build continues to use checked-in fixture bytes offline. [VERIFIED: fixtures/visible-demo/manifest.json:7-14] The manifest says verbatim: `"assembler": "RGBDS", "version": "1.0.1"`.

## Architecture Patterns

### Pattern 1: Cartridge descriptor validated before mutation

**What:** Decode header fields into a temporary cartridge descriptor: controller/type, exact ROM bank count and byte length, RAM size/bank count, battery capability, and explicit special-variant status. Check multiplication/shift and allocation bounds before constructing state. Do not use declared sizes until validated against the decision matrix and supplied image length. [CITED: https://gbdev.io/pandocs/The_Cartridge_Header.html; https://gbdev.io/pandocs/MBC1.html; Gekkio, §12–13, https://gekkio.fi/files/gb-docs/gbctr.pdf]

**When to use:** ROM replacement and every synthetic malformed-header case.

**Example (design sketch):** validate header and exact length → select supported descriptor → allocate/copy candidate ROM and RAM → initialize candidate RAM policy → swap candidate into the instance → reset guest/mapper controls. Every failure before final swap leaves prior machine and cartridge intact.

### Pattern 2: Separate MBC1 register state from effective bank selection

**What:** Store low five ROM-bank bits, upper two bank bits, mode, and RAM enable independently. Calculate visible ROM/RAM bank at access time from mode plus physical ROM/RAM address-line mask. For the switchable ROM window, transform raw low-bank zero before applying physical mask, per locked D-02. Do not “repair” bank zero after masking. Pan Docs and Gekkio describe the address-line coupling and mode-dependent lower window; upper bits disconnected on smaller ROMs must naturally be ignored by size masking. [CITED: https://gbdev.io/pandocs/MBC1.html; https://gekkio.fi/files/gb-docs/gbctr.pdf, §13.2]

**When to use:** CPU reads in ROM windows and external RAM accesses; each register write should only update mapper state and not mutate ROM bytes.

**Code shape:** Keep helper names narrow (`effective_rom_bank`, `effective_ram_bank`, `cartridge_read`, `cartridge_write`) and use unsigned fixed-width fields. Mode-zero lower window maps bank zero; mode-one lower window uses upper bits. RAM gate controls reads and writes; disabled writes do nothing and disabled/unmapped reads use the locked deterministic `$FF` policy.

### Pattern 3: Transactional import/export using caller buffers

**What:** Query the exact export size for the loaded battery cartridge; export only into a caller buffer whose capacity is sufficient. Import accepts exactly the expected cartridge RAM size, checks arguments and identity as applicable at the host boundary, stages/validates bytes, then copies the complete image into instance RAM once. Bad input returns an error without touching live RAM. Volatile MBC1 RAM is not battery-exportable.

**Why:** This repeats existing API behavior: caller-owned outputs and validation-before-write. Current API header explicitly says `"On every error, pixels and out_info remain unchanged."` [VERIFIED: include/gabbaboy/gabbaboy.h:142-151] For ROM validation, exact current behavior is stated as `"A failed replacement leaves the current ROM and machine state unchanged."` [VERIFIED: include/gabbaboy/gabbaboy.h:122-125]. Preserve those guarantees for battery operations.

### Pattern 4: Versioned host envelope and atomic replace

**What:** Encode explicit fields in a fixed byte order, never a native C structure. Fix and document field lengths, checksum algorithm/purpose, and maximum file length. Read at most `header_size + 32768` bytes plus one sentinel byte to detect excess; require an exact format length and reject trailing bytes. Validate magic/version, exact ROM digest, type/RAM identity, exact declared payload length, and checksum before importing. A checksum detects accidental corruption only.

**Write path:** Open the preference directory, acquire a nonblocking exclusive lock on a stable identity-derived lock file, create a unique temp in that directory with exclusive/no-follow semantics, write all envelope bytes, sync temp, rename over target, then sync directory where supported. Never open/truncate the target for writes. POSIX `rename()` describes atomic name replacement when successful; `fsync()` documentation explains durability is implementation/storage dependent, so acceptance must not equate rename with power-loss durability. [CITED: https://pubs.opengroup.org/onlinepubs/9799919799/functions/rename.html; https://pubs.opengroup.org/onlinepubs/009695399/functions/fsync.html]

**Recovery path:** Only accept bounded regular files. For malformed, wrong-version or wrong-identity files, first preserve the original under a unique recovery name, then initialize deterministic fresh RAM and show warning. If preservation fails, leave the original untouched and disable persistence for that session. A valid-but-different ROM file is never selected because ROM digest participates in identity.

### Pattern 5: Explicit lifecycle flush state

**What:** Track battery-capable, dirty, last-change/quiet deadline, max-dirty deadline, last save outcome, lock held, and persistence enabled/disabled in player session state. A RAM byte write marks dirty only if the byte value changes. The chosen initial cadence is 2s quiet / 10s maximum dirty age; timer values are host policy and must not affect emulated time. On reset, replace, or quit, flush before changing/destroying the machine. If final flush fails, keep the dirty machine state and provide retry/cancel/continue-without-saving resolution.

**Current seam:** `player_session_replace_rom(...)` reads a bounded ROM into a temporary buffer and only then calls `gbb_load_rom`, committing the path on success [VERIFIED: src/player/session.c:91-119]. `reset_session`, `replace_session_rom`, and `request_quit` in `src/player/main.c` are the three lifecycle points to route through save coordination [VERIFIED: src/player/main.c:376-404, 521-524].

## Recommended Project Structure

Extend current ownership boundaries rather than adding a persistence framework:

```text
include/gabbaboy/gabbaboy.h       # bounded battery API and error contract
src/core/gabbaboy.c               # mapper registers, validated cartridge, cart RAM
src/player/session.h/.c           # save identity/envelope/read/write/lock/recovery
src/player/main.c                 # debounce, lifecycle flush decisions, status text
tests/test_loader.c               # header/type/size and non-destructive replacement
tests/test_bus.c or new test_cartridge.c  # independently expected bank/RAM behavior
tests/test_api.c or new test_battery.c    # caller-buffer import/export behavior
tests/player/test_session.c       # isolated file-system and fault-path tests
fixtures/mbc1-continuation/        # original source, bytes, manifest, rights notice
tests/scripts/reproduce-mbc1-continuation.sh
```

Prefer a focused cartridge test binary over making loader, API, or player tests share a large fixture harness. Avoid new dependencies and avoid moving file operations into `src/core`.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|------------|-------------|-----|
| Generic mapper plugin framework | A registry/vtable/plugin layer for a single new mapper | A small explicit MBC1 cartridge state and dispatch | The project calls for clear targeted abstractions; broader mappers are deferred. |
| File format serialization framework | Generic object serializer/native struct dumps | Explicit fixed-endian envelope encode/decode | The format is one versioned header plus at most 32 KiB; explicit code is auditable and avoids padding/ABI hazards. |
| ROM cryptography implementation | Handwritten SHA-256 | macOS CommonCrypto | Crypto algorithms are easy to get subtly wrong; a system API is already the locked choice. |
| General save manager | Library, picker, browsing and merge UI | One identity-bound managed save and concise current status | User explicitly bounded Phase 4 UX. |

**Key insight:** This phase has two distinct transactional boundaries: core import and ROM replacement preserve the live instance on rejection; host file replacement preserves the last complete on-disk save on failure. Keep their tests separate so one cannot mask the other.

## Common Pitfalls

### Header declarations treated as trustworthy allocation instructions

**What goes wrong:** Contradictory type/RAM fields, oversized sizes, bad exact lengths, unchecked shifts, or special wiring can allocate incorrectly or map out of bounds. **Avoid:** build/validate a bounded descriptor, reject contradictions before allocation, and stage the candidate before replacement. **Detect:** table-driven exact and one-over sizes, malformed type/RAM combinations, truncated/long images, and failed replacement preserving old guest state. [CITED: Pan Docs cartridge header and MBC1; project F-07]

### Banking transform applied in the wrong order

**What goes wrong:** low register zero may map an inaccessible bank, mask/OR expressions can lose physical address-line behavior, and mode 1 lower-window/RAM behavior can diverge. **Avoid:** retain raw registers, derive effective banks with the order fixed by D-02, and test every supported ROM size with bank-pattern bytes. **Detect:** independent expected bank IDs at `$0000`, `$4000`, and `$A000` after each register write; include banks whose high address lines are disconnected. [CITED: Gekkio §13.2; Pan Docs MBC1]

### Mutable RAM pointer or partial import

**What goes wrong:** a caller can bypass dirty tracking or hold a pointer across replacement; a truncated import partially corrupts progress. **Avoid:** exact-size query and bounded copy calls, with complete validation before one commit copy. **Detect:** canary buffers, short/long input, null arguments, and unchanged export bytes after a rejected import.

### Save file identity based on path or filename

**What goes wrong:** same-named ROMs collide and moving a ROM disconnects progress. **Avoid:** digest exact bytes and include supported cartridge identity in the key and file. Treat digest as identity, never integrity/authenticity. **Detect:** same basename/different ROM, same bytes at different paths, ROM replacement, and digest mismatch controls.

### “Atomic rename” overstated as full durability

**What goes wrong:** a partial target or stale data may survive due to failed writes/syncs; rename atomicity alone is not a hardware power-loss guarantee. **Avoid:** temp file in same directory, complete write, sync-before-rename, directory sync when supported, explicit failure state. **Detect:** inject open/create, short-write, file-sync, rename, directory-sync failures; verify target is old complete or new complete. Process-kill testing demonstrates interruption recovery, not actual storage power-loss behavior. [CITED: POSIX rename and fsync]

### Recovery accidentally destroys the only evidence/save

**What goes wrong:** malformed or wrong-ROM bytes are silently replaced with fresh `$FF` RAM. **Avoid:** preserve the rejected file under a unique recovery name before initializing; disable persistence if preservation fails. Reject symlink/special-file targets and bound reads. **Detect:** read-only directory, collision in recovery names, symlink target, oversized file, failed rename, then inspect that the original bytes remain unchanged.

### Two sessions overwrite each other's progress

**What goes wrong:** last-writer-wins silently loses updates. **Avoid:** hold nonblocking exclusive advisory lock file for full battery session lifetime. Explain advisory scope: only cooperating GabbaBoy processes are protected. **Detect:** child process opens same identity while parent holds lock, then succeeds only after parent closes/releases it. [CITED: Apple flock(2)]

### RAM progress mistaken for verified guest continuation

**What goes wrong:** an export/import byte round trip passes while guest behavior never depends on persisted data. **Avoid:** original fixture writes a meaningful value, process 1 exits, process 2 opens a fresh core/player and branches on that value. Missing save and wrong-ROM controls must take distinguishable paths. **Detect:** deliberately remove/corrupt prior bytes and assert the continuation success protocol does not occur. This is owned end-to-end software evidence, not a hardware oracle.

## Code Examples

### MBC1 mapping reasoning sketch

Use the exact mapping contract already quoted under user constraints: raw low and upper register values remain separately stored; raw low bank zero is translated before ROM-size mask; mode selects fixed/upper-window and RAM bank behavior. Implement access-time helpers rather than mutating effective bank fields on each write. Keep calculations unsigned and bounded by a validated cartridge descriptor. This sketch deliberately avoids inventing public enum/symbol names before the planner chooses them.

### Transactional byte import sketch

```c
/* Design pseudocode; names and error enum are left for implementation. */
if (instance == NULL || input == NULL || input_size != expected_battery_size)
    return error;
/* No instance writes occur before complete validation. */
memcpy(candidate_ram, input, expected_battery_size);
memcpy(instance_ram, candidate_ram, expected_battery_size);
return success;
```

Use actual API names/error values only after adding them to the public header. Its currently read definitions include `GBB_INVALID_ARGUMENT`, `GBB_INVALID_ROM`, `GBB_ROM_TRUNCATED`, `GBB_ROM_TOO_LARGE`, `GBB_ROM_SIZE_MISMATCH`, `GBB_UNSUPPORTED_CARTRIDGE`, `GBB_UNSUPPORTED_ROM_SIZE`, `GBB_UNSUPPORTED_RAM_SIZE`, and `GBB_OUT_OF_MEMORY`. [VERIFIED: include/gabbaboy/gabbaboy.h:17-32; quoted verbatim here]

### Fixture reproduction

Follow existing visible-demo pattern: source plus explicit notice/license, checked-in ROM bytes, manifest with source/ROM hashes, immutable build tool/archive identity, build recipe, profile/boot applicability, protocol, timeout, scope limits, and a reproduction script. Keep ordinary CTest offline; separate pinned-tool fixture reproduction in the existing fixture-repro CI lane. Current source states `"profile": { "name": "DMG-CPU-B"` and `"boot": "Skipped; bootless profile starts at cartridge entry 0x0100."` [VERIFIED: fixtures/visible-demo/manifest.json:19-23]. The MBC1 fixture must declare its own software-only applicability and guest save protocol.

## Validation Architecture

### Existing Framework

| Property | Value |
|----------|-------|
| Framework | CTest, with C17 test executables |
| Test inventory | `tests/expected-tests.txt`; separate optional player inventory `tests/player/expected-tests.txt` |
| Sanitizers | Existing ASan+UBSan CI preset and explicit inventory verification |
| Fixture reproduction | Existing RGBDS v1.0.1 fixture-reproduction workflow; routine tests use checked-in bytes |
| External API check | Relocated installed C and C++ consumers already run in core CI; extend their battery API calls |

### Requirement to Evidence Map

| Requirement | Required named evidence | Layer |
|-------------|-------------------------|-------|
| SAVE-01 | Supported-header matrix, unsupported cases, ROM/RAM bank patterns, modes, gate behavior, mirroring and bank limits | Core contract; software model |
| SAVE-02 | Exact 8/32 KiB battery transfer, caller-buffer bounds, no battery/volatile behavior, malformed import unchanged-state check, relocated C/C++ API consumers | Core/API contract |
| SAVE-03 | Envelope round-trip and reject matrix; old/new-complete target assertion for all injected write failures; recovery preservation; two-process lock conflict; visible status path | Player adapter integration |
| SAVE-04 | Process A guest writes; orderly close; Process B fresh instance loads; resumed success protocol; missing-save and wrong-ROM controls fail differently; fixture identity reproduction | Owned end-to-end guest fixture; not physical hardware proof |

### Required test additions and validation gaps

Add named cases to both inventory files and keep optional-player tests conditional only through existing CMake rules. Recommended grouped binaries:

- Core cartridge tests: ROM bank windows and every supported size mask; low-zero translation; mode switch; enable/disable; 8 KiB mirror; 32 KiB bank select; absent RAM; header contradiction matrix; explicit unsupported variant; non-destructive invalid replacement.
- Core battery API tests: no battery vs volatile RAM vs battery-backed RAM; exact capacity/length; too-small output no-write; malformed import no mutation; import/export round trip; reset retention; ROM replacement independence; multiple-instance independence.
- Player save-adapter tests: versioned envelope round trip and exact maximum bound; truncation/trailing/corrupt/wrong-identity rejection; regular-file/symlink/special-file checks; recovery uniqueness and preservation; failure injection at create/write/sync/rename/recovery; lock held/released across separate processes; identity behavior for renamed/duplicate ROM files.
- Continuation executable test: orchestrate two distinct processes and assert the guest protocol result and negative controls. Ensure child time and resource use have explicit limits; process kill only tests process-interruption behavior.
- Run existing ASan+UBSan required lane and bounded API/battery fuzz target. A fuzz harness must impose both input byte and execution limits; retain each minimized bug in named regression tests.

## Security Domain

This phase reads attacker-controlled ROM and save bytes and writes into a user-specific directory. Apply validation and resource bounds at both boundaries. Never treat SHA/checksum as authentication. For filesystem writes, reject symlink/special-file destinations, use exclusive temp creation and a stable lock file, avoid following attacker-controlled path components where APIs permit, and keep diagnostic text bounded and privacy-safe. Public artifacts should identify fixtures by repo-relative identity/hash, not local paths or save contents. [ASSUMED: applying the project's existing untrusted-input/security rules to these new parser and filesystem boundaries; see AGENTS.md and Phase 4 D-12/D-15]

### Applicable ASVS-style categories

| Category | Applies | Control in this phase |
|----------|---------|-----------------------|
| Authentication / session | No user accounts or network session | No authentication subsystem is introduced. |
| Access control | Limited | OS file permissions and advisory lock coordinate local cooperating processes; do not claim protection from external tools/users. |
| Input validation | Yes | Header matrix, exact lengths, bounded reads, fixed format/version, checksum and identity checks before commit. |
| Cryptography | Limited | Platform SHA-256 only for stable ROM identity; checksum for accidental payload corruption. Neither is an authenticity control. |
| Error handling | Yes | Preserve prior valid in-memory/on-disk state on failure; make dirty-unsaved and disabled-persistence status visible. |

## Environment Availability

| Dependency | Required by | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| CMake / C17 toolchain | Core, CTest, consumers | Existing configured project dependency; exact host version not re-probed for this research | — | Existing project preset/toolchain requirements |
| SDL3 | Optional player persistence path | Existing optional player target | — | Core remains usable without player |
| RGBDS | Fixture regeneration only | Existing repository workflow pins it; routine build consumes checked-in bytes | 1.0.1 in existing fixture manifest | Use checked-in fixture for ordinary offline tests |
| macOS CommonCrypto | ROM digest in player | Platform facility selected by locked decision | OS-provided | No external crypto package; player package already targets macOS |

## Project Constraints (from AGENTS.md)

- Target Game Boy/Game Boy Color; copied NES, Neo Geo, Elixir, and other examples are not implementation requirements.
- Use portable original C17 core code, explicit ownership/error behavior, bounded public operations, and no hidden globals.
- Keep host timing, filesystem, UI, audio devices, and environment configuration in adapters; the core remains dependency-light.
- Prefer small direct code and targeted abstractions; comment hardware reasons and subtle invariants.
- Guard ROM/save/state boundaries against overflow, truncation, excess allocation/work, and partial mutation; use explicit portable serialization rather than raw struct dumps.
- Distinguish hardware-backed tests, differential oracle results, metamorphic properties, regression fixtures, and private game observations; declare applicability, exclusions, and expected failures.
- Do not add Nintendo boot ROMs, commercial game images, unlicensed homebrew, private data, or mandatory telemetry. Third-party fixtures need redistribution rights and a digest.
- Do not claim unimplemented emulator behavior; keep the required phase pause and stop after this planning/implementation phase.
- Keep privacy-sensitive local paths, identities, and save contents out of public artifacts.

## Planning Resolutions (Open Questions Closed)

- **Public battery API (D-05/D-06):** Add `gbb_error gbb_battery_size(const gbb_instance *instance, size_t *out_size)`, `gbb_error gbb_copy_battery(const gbb_instance *instance, uint8_t *out_bytes, size_t capacity_bytes)`, `gbb_error gbb_import_battery(gbb_instance *instance, const uint8_t *bytes, size_t size_bytes)`, and `gbb_error gbb_battery_generation(const gbb_instance *instance, uint64_t *out_generation)` to the existing C header. A null required pointer returns `GBB_INVALID_ARGUMENT`; an unloaded, ROM-only, or volatile-RAM cartridge returns new `GBB_NO_BATTERY`; insufficient export capacity returns new `GBB_BUFFER_TOO_SMALL`; import length unequal to the exact 8 or 32 KiB returns new `GBB_BATTERY_SIZE_MISMATCH`. Error outputs and live RAM remain unchanged. Export writes exactly the queried length, leaving excess caller capacity unchanged. Successful import copies all bytes atomically and advances generation only if bytes change; changed guest RAM writes advance it once per changed byte, unchanged writes do not. Player records the generation after a successful import/save; reset preserves RAM and generation, successful ROM replacement starts FF RAM and generation zero. The core never validates a ROM digest or accesses files.
- **v1 envelope (D-08):** The header is exactly 51 bytes: 8 ASCII bytes `GBBBSAVE`, little-endian uint16 version `1`, 32 raw SHA-256 ROM digest bytes, uint8 cartridge type, little-endian uint32 RAM length, and little-endian uint32 IEEE CRC-32 of the payload (reflected polynomial `0xEDB88320`, initial/final XOR `0xFFFFFFFF`). Follow with exactly 8192 or 32768 raw RAM bytes. Read at most 32820 bytes, including a one-byte excess sentinel, and accept at most 32819 bytes total. Encode/decode each field, never copy a native structure. CRC-32 detects accidental corruption and does not authenticate the file. Format changes later require a reviewed migration or retention of the old save.
- **Conservative MBC1M candidate predicate (D-03):** For a primary MBC1 type `$01`–`$03` ROM with a present bank `$10` (at least 512 KiB), inspect the alternate local header at absolute byte offset `0x40000 + 0x0100`. Reject with new `GBB_UNSUPPORTED_CARTRIDGE_VARIANT` only when the canonical Nintendo logo matches at alternate header offsets `$0104`–`$0133`, the alternate header checksum over `$0134`–`$014C` validates against `$014D`, and the alternate cartridge type at `$0147` is also `$01`–`$03`. This is a conservative operational form of [Pan Docs' MBC1M identification note](https://gbdev.io/pandocs/MBC1.html), which points to a Nintendo copyright header in bank `$10`; the live Pan Docs page returned HTTP 403 in this planning runtime, so the cited research/owner-provided note is the source available here. A negative check does not prove standard wiring; unrecognized special-wiring images remain outside the qualified set. No title/content heuristic or MBC1M emulation is introduced.
- **Fault injection seam (D-15):** In `src/player/session.c`, define one test-only, one-shot fault-stage hook behind a test compile definition for temp creation, short write, file sync, rename, directory sync, recovery rename, and lock acquisition. The release adapter follows direct OS calls; tests compile the same adapter with the hook enabled and assert old/new complete-file invariants. This keeps failure injection deterministic without a general filesystem abstraction.

These choices resolve the implementation questions raised by research and retain the locked support matrix, save directory, ROM-byte SHA-256 identity, dependency boundary, and physical-evidence exclusion.

## Sources

### Primary technical sources

- [Pan Docs — MBC1](https://gbdev.io/pandocs/MBC1.html) — documented registers, modes, RAM gate, bank behavior, MBC1M distinctions; live page fetch was blocked in this research runtime, so use citation as the canonical reference rather than claiming a fresh page verification.
- [Pan Docs — cartridge header](https://gbdev.io/pandocs/The_Cartridge_Header.html) — type/ROM/RAM size fields.
- [Gekkio, Game Boy: Complete Technical Reference, §12–13](https://gekkio.fi/files/gb-docs/gbctr.pdf) — MBC1 address-line mapping and bank masks. Search result excerpt confirmed how the two ROM windows depend on mode and physical address lines; treat this as documentation evidence, not hardware test evidence.
- [SDL3 `SDL_GetPrefPath`](https://wiki.libsdl.org/SDL3/SDL_GetPrefPath) — official API states the returned per-user/per-app directory is intended for save games and is freed with `SDL_free`; retrieved during this research.
- [POSIX `rename()`](https://pubs.opengroup.org/onlinepubs/9799919799/functions/rename.html) and [`fsync()`](https://pubs.opengroup.org/onlinepubs/009695399/functions/fsync.html) — replacement and synchronization semantics; filesystem/storage guarantees remain implementation-dependent.
- [Apple `flock(2)`](https://developer.apple.com/library/archive/documentation/System/Conceptual/ManPages_iPhoneOS/man2/flock.2.html) — advisory shared/exclusive lock semantics and cooperating-process limit.
- [Apple CommonCrypto](https://developer.apple.com/library/archive/documentation/System/Conceptual/ManPages_iPhoneOS/man3/CC_crypto.3cc.html) — platform cryptographic API reference.

### Repository evidence

- [AGENTS.md](../../../AGENTS.md), [Phase 4 context](04-CONTEXT.md), [requirements](../../REQUIREMENTS.md), [roadmap](../../ROADMAP.md), [project architecture](../../research/ARCHITECTURE.md), [hardware validation](../../research/HARDWARE-AND-VALIDATION.md), [pitfalls](../../research/PITFALLS.md), [quality and delivery](../../research/QUALITY-AND-DELIVERY.md).
- Public API and current ROM-only loader: `include/gabbaboy/gabbaboy.h:113-125`, `src/core/gabbaboy.c:365-400,439-499,1070-1119`.
- Player replacement and lifecycle: `src/player/session.c:91-119`, `src/player/main.c:376-404,521-524`.
- Test inventory and existing sanitizer/fixture lanes: `tests/CMakeLists.txt`, `tests/player/CMakeLists.txt`, `tests/expected-tests.txt`, `tests/player/expected-tests.txt`, `.github/workflows/ci.yml`, `.github/workflows/fixture-repro.yml`.
- Fixture reproduction precedent: `fixtures/visible-demo/manifest.json`, `fixtures/visible-demo/demo.asm`, `tests/scripts/reproduce-visible-demo.sh`.

## Assumptions Log

| # | Claim | Section | Risk if wrong |
|---|-------|---------|---------------|
| A1 | Current macOS player can use CommonCrypto without a new package under its deployment target. | Standard Stack | Build may require a small platform conditional or deployment-target adjustment. Verify in the actual macOS build. |
| A2 | A narrowly scoped file-operation seam can inject failures for tests without becoming a generic filesystem abstraction. | Validation Architecture | Tests may otherwise rely on brittle permission/environment failures and miss write stages. |
| A3 | There is no existing battery persistence format that needs migration. | Summary | If implementation work or local user data already exists, overwriting/migration policy must be revisited first. |

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — existing C17/SDL3 seam and locked no-dependency policy; external APIs cited to primary docs.
- Architecture: HIGH — current per-instance core, bounded API and transactional replacement are directly present in source.
- MBC1 mapping: MEDIUM — primary reverse-engineering documentation is strong but does not constitute a GabbaBoy physical measurement; MBC1M detection has a known incomplete-detection limit.
- Persistence durability: MEDIUM — OS API rules are documented, but filesystem and power-loss properties are platform/configuration dependent and must be tested without overclaiming.
- Fixture/evidence strategy: HIGH — follows established project fixture and inventory patterns; the Phase 4 guest fixture does not yet exist.

**Research date:** 2026-10-07
**Valid until:** 2026-11-06 for stable architecture; recheck SDL/Apple platform details and fixture/tool pins during implementation.
