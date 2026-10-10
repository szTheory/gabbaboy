# Cross-project lesson exchange

Created 2026-10-02. This ledger is intentionally small. Detailed imported evidence is in `research/PRECEDENT.md`; hardware and upstream evidence are in the corresponding research topics.

## Rule for incoming lessons

A lesson from another emulator is a hypothesis until its mechanism applies to GabbaBoy and evidence supports the adaptation. Record the source project and revision/date, whether it was implemented or merely planned, how the target differs, the smallest local reproduction, and the resulting decision. Preserve corrections by superseding old entries instead of silently erasing the reasoning.

## Rule for outgoing lessons

At meaningful phase/milestone boundaries, produce a short pasteable transfer when requested. Exclude absolute personal paths, identities, private ROM names/hashes, credentials, and conversation transcripts. Do not imply another console shares the same timing behavior simply because the bug category sounds similar.

## Transfer template

```text
Lesson ID / date / originating project revision:
Symptom and reproduction:
Root cause / invariant:
Fix and evidence:
Applies when:
Does not establish:
Suggested check in the receiving project:
Source paths or public URLs:
Status: observed / reproduced / adopted / superseded
```

## Imported safeguards to validate locally

| ID | Lesson | GabbaBoy action | Status |
|---|---|---|---|
| XFER-001 | A promising homebrew fixture may be private, unlicensed for redistribution, or for a different console | Admit GB fixtures only after license/system/protocol review; add an original persistence fixture | Imported; implementation pending |
| XFER-002 | A save test can pass without reading previously persisted bytes | Reload in a fresh instance/process and assert behavior that depends on old save contents; include wrong-save control | Imported; implementation pending |
| XFER-003 | Green orchestration is weaker than evidence tied to a source revision and packaged bytes | Assert mandatory gate execution, tested revision, install/consumer smoke, and artifact digest | Imported; implementation pending |
| XFER-004 | Timing and save correctness require hidden in-flight state, not only visible registers | Exercise split-run equivalence and save/load continuation at intermediate device events | Proposed adaptation; implementation pending |
| XFER-005 | Upstream automation behavior changes; copied CI folklore can be stale | Recheck official GitHub token/event rules during workflow implementation and verify target-repo behavior | Source-checked recommendation; repository verification pending |
| XFER-006 | Subsystem suites and a synthetic display demo do not establish a supported game's end-to-end progress | Before future cartridge/CGB breadth claims, require one rights-clear ROM-only/MBC1 game to reach a defined playable state in the existing player; diagnose stalls with bounded traces and keep private inputs/traces local | Sanity-checked; adopted as a future planning gate, not a v0.1 completion claim |

The implementation and planning lessons follow; retain their distinct evidence classes.

### GB-CORPUS-001 / 2026-10-06 / Phase 2 verification

- **Cause and evidence:** A read guard covered only some addressing families; other unsupported reads returned `FF`. This let three CPU/timer ROMs traverse an unsupported PPU reporting dependency and appeared to qualify a corpus excluded by the phase contract.
- **Remedy:** Preflight every instruction/fetch/conditional-stack read, reject unsupported access without partial mutation, and audit the whole fixture path through assertion callbacks and result reporting. Keep failed IDs and denominator intact while planning a qualified completion path.
- **Applies when:** A narrow emulator or protocol implementation admits third-party diagnostics with shared setup/reporting code.
- **Verification:** Corrective read-family, wrap and HALT regressions pass. At `c583e33`, normal and sanitizer suites each fail four of 94 cases; all three required ROMs stop at `F0 44` before their result protocol. Prior corpus passes are superseded, not completion evidence.
- **Status:** The unsupported-read boundary and source-qualified derived corpus are verified. Original PPU/LY-dependent upstream reporting remains ineligible; the admitted derived denominator is three cases, verified by current offline and hosted gates.

### GB-CI-003 / 2026-10-06 / Failed test inventories

- **Cause and evidence:** Exact testcase names alone allowed a synthetic report containing a failed testcase to pass the inventory checker.
- **Remedy:** Reject JUnit failure and error elements before accepting exact nonempty names and no skips. Set an explicit CMake policy baseline in standalone verification scripts.
- **Applies when:** CI uses a second report parser to certify mandatory test execution.
- **Verification:** Synthetic failure/error reports now return nonzero; the passing control returns zero. Current failing corpus reports are rejected. The CMake 3.28 script-mode fixture checks execute after the 3.25 policy baseline correction.
- **Status:** Reproduced and corrected in `c583e33`.

### GB-CPU-001 / 2026-10-06 / Instruction matrices

- **Cause and evidence:** Broad opcode matrices asserted totals and final state but missed RET/RETI bus phases, consecutive EI, ROM-dependent startup flags, and interrupt diagnostic chronology. Independent source review found all four gaps while registered focused cases passed.
- **Remedy:** Qualify transition and timed-access claims with independent sequences, including device deadlines inside CPU operations and consecutive control instructions.
- **Applies when:** Instruction totals or final registers stand in for internal observable timing behavior.
- **Verification:** Plans 02-10 and 02-11 added startup-F, RET/RETI phase, consecutive-EI and interrupt-diagnostic regressions; Plan 02-18 added full legal base-opcode state/branch/address/bus assertions. The final verifier passed 5/5 roadmap truths at code SHA `cf28e90270be24d9528bfa8a1e4055a2b8485989`.
- **Status:** Closed by targeted regressions and independent verification; preserve the separation between test coverage and hardware qualification.

### GB-FIXTURE-001 / 2026-10-06 / Phase 2 fixture admission

- **Cause and evidence:** Mooneye's root MIT license did not close redistribution rights for every included asset. The pinned common include identifies Darkrose's font and links to an asset page, but the pinned suite tree has no font source or font-specific license.
- **Remedy:** Plan 02-07 replaces only the bundled 2032-byte font asset with an original zero-filled image, preserving ROM layout and test instructions/protocol. It records source/include closure, notices, replacement digest, immutable WLA-DX pin, and generated ROM digests.
- **Applies when:** Compiling third-party diagnostic ROMs whose common includes embed independently licensed artwork.
- **Verification:** The original replacement/font rights and source closure are recorded; candidate bytes match across local and hosted runs, and the protocol-aware runner passes its fixed 1-CPU/2-timer denominator. Current exact hosted fixture run 37620710600 passed at implementation SHA `cf28e90270be24d9528bfa8a1e4055a2b8485989`.
- **Status:** Derived headless corpus admission and reproduction are verified. Original PPU-dependent ROM paths remain excluded and are not hardware-qualified.

### GB-CI-002 / 2026-10-06 / Phase 2 planning review

- **Cause and evidence:** Plan 02-09 repeated the relative JUnit path error recorded in GB-CI-001 despite passing structural review. A fresh temporary one-test CTest run confirmed that `--test-dir <dir> --output-junit build/probe.xml` writes beneath `<dir>/build/`, not the caller's directory.
- **Remedy:** Use report basenames for preset/test-dir invocations, then verify the corresponding selected-directory path; clear cached installed-prefix configuration for a core-only inventory. Plan 02-09 now states both rules.
- **Applies when:** Planning CTest evidence commands for fresh or reused build configurations.
- **Verification:** Temporary tooling probe passed 1/1 and the predicted report existed. Phase 2 tests and installed inventory remain pending; structural review alone does not prove runnable command behavior.
- **Status:** Reproduced, reconciled in the plan, and included in passing current CTest inventory checks.

## GabbaBoy implementation lessons

### GB-CI-001 / 2026-10-03 / Plan GB-01-04

- **Symptom and reproduction:** CTest ran the full suite, but the inventory checker reported a missing JUnit file when `--output-junit build/ctest.xml` was combined with `--test-dir build`; CTest placed the relative path under its selected build directory.
- **Root cause / invariant:** JUnit report paths are interpreted from CTest's selected test working directory. Conditional package tests also mean the required inventory depends on whether a relocated prefix exists at configure time.
- **Fix and evidence:** Use a report basename for test-dir/preset runs, then check the corresponding build-directory file. Store all 24 required test names in `tests/expected-tests.txt`, and select the 21-case core subset only for sanitizer and pre-install runs. The skipped and incomplete report controls failed closed; local macOS and Ubuntu x86_64 runs verified 24 installed tests, 21 ASan/UBSan cases, and 24 relocated CMake 3.25.3 cases.
- **Applies when:** CTest reports are used to enforce a cross-platform, conditionally registered test inventory.
- **Does not establish:** Hosted GitHub check state, branch protection, Windows results, or an OS support floor.
- **Suggested check:** Verify every expected testcase name appears exactly once, reject `<skipped>` entries, and require nonempty test execution before accepting the report.
- **Source:** `.github/scripts/verify-test-inventory.sh`, `.github/workflows/ci.yml`, `.planning/phases/GB-01-portable-foundation-and-original-rom-tracer/01-04-SUMMARY.md`.
- **Status:** Reproduced and adopted.

### GB-GSD-001 / 2026-10-03 / Phase 1 closeout

- **Symptom and reproduction:** OpenGSD 1.15.0 reported Phase 1 as `7/5` plans at `phase.complete`, while the roadmap contains five plans. The directory has five distinct `*-PLAN.md` files and five unique summaries; two tracked `01-01-SUMMARY.md` and `01-02-SUMMARY.md` paths are symlinks to the matching `GB-01-*` summary files and were counted twice.
- **Root cause / invariant:** The phase uses both the milestone-prefixed summary names and legacy plan-ID aliases. A raw count of summary paths is not a count of completed plans when aliases point to the same content.
- **Fix and evidence:** Reconciled completion against plan IDs, kept the compatibility symlinks, and corrected ROADMAP/STATE to 5/5. All eight Phase 1 truths passed the independent verifier; the exact plan inventory has five plans and five unique summaries.
- **Applies when:** A phase retains legacy summary-name symlinks after a milestone/plan naming migration.
- **Does not establish:** A fix to OpenGSD's alias-counting behavior; the runtime may still display an inflated raw summary-path count.
- **Suggested check:** Compare unique plan IDs and resolved summary targets, not only the number of `*-SUMMARY.md` paths.
- **Source:** `.planning/phases/GB-01-portable-foundation-and-original-rom-tracer/01-VERIFICATION.md`, `.planning/ROADMAP.md`, `.planning/STATE.md`.
- **Status:** Observed and reconciled locally.

### GB-CORE-001 / 2026-10-03 / Phase 1 code review

- **Symptom and reproduction:** The loader accepted a valid ROM-only image declaring 64 KiB even though the implementation maps only the first 32 KiB; the address window at 0xA000 is used for emulator-owned fixture RAM, so a larger image was not mapped as declared.
- **Root cause / invariant:** Header size validation admitted a capacity the mapper did not implement. A successful load must mean every advertised byte is reachable according to the selected cartridge mapping.
- **Fix and evidence:** Reject ROM-only size codes above 0 before allocation or mutation, document exact 32 KiB support, and add a valid-checksum 64 KiB regression that confirms the prior loaded guest remains usable. The regression passed local CTest, ASan/UBSan, the CMake-floor lane, and exact-revision native CI.
- **Applies when:** Cartridge headers or file formats declare capacity beyond what the current mapper can address.
- **Does not establish:** Mapper behavior, hardware-qualified A000 mapping, or support for larger ROMs.
- **Suggested check:** For every supported size code, prove exact-length acceptance and for the next unsupported code prove bounded rejection without mutating a loaded instance.
- **Source:** `src/core/gabbaboy.c`, `tests/test_loader.c`, `include/gabbaboy/gabbaboy.h`, Phase 1 review and verification artifacts.
- **Status:** Reproduced and adopted.

### GB-ARTIFACT-001 / 2026-10-03 / Phase 1 code review

- **Symptom and reproduction:** Checking archive member names alone did not prevent a tar link from writing outside the install prefix; hidden extension headers and oversized/deep archives also create parser and resource pressure before ordinary member extraction.
- **Root cause / invariant:** Downloaded workflow artifacts and tool archives are untrusted input. Validate member type, normalized path, expansion limits, metadata headers, and the actual package digest before writing or executing files.
- **Fix and evidence:** Pin the RGBDS release archive SHA-256; use a streaming extractor that permits only regular files/directories and enforces compressed/decompressed byte, member, extension, and path-depth limits; stage evidence under an atomically created private temporary directory. The adversarial extractor self-test and exact hosted artifact verification passed.
- **Applies when:** CI downloads or republishes archives that will be extracted or used as build tools.
- **Does not establish:** General safety of every archive parser or a broader supply-chain guarantee beyond the pinned bytes and exercised paths.
- **Suggested check:** Maintain traversal, link, special-file, duplicate, parent-conflict, size, member-count, metadata-header, depth, and truncation controls, and verify digest before extraction or execution.
- **Source:** `.github/scripts/safe_extract_package.py`, `.github/scripts/verify-pr-evidence.sh`, `.github/workflows/fixture-repro.yml`, Phase 1 review and verification artifacts.
- **Status:** Reproduced and adopted.

### GB-QUALIFICATION-001 / 2026-10-06 / Phase 2 hosted checks

- **Cause and evidence:** Local qualification missed two cross-host boundaries. Hosted Windows rejects manifest bytes before intended negative-control reasons, and pinned Linux fixture reproduction differs in DAA beginning at byte 335. Neither cause is established; line endings are only a Windows hypothesis.
- **Remedy:** Capture actual consumed/generated bytes, compare all differences, and qualify deterministic checkout/build recipes before changing expected digests or weakening strict validation.
- **Applies when:** Exact byte hashes and generated fixtures cross checkout, compiler, assembler or host boundaries.
- **Verification:** The later deterministic `wlalink -nS -d -S` recipe produced exact candidate bytes across local and hosted runs. Windows manifest distinctions and exact inventory controls were corrected. The current implementation SHA `cf28e90270be24d9528bfa8a1e4055a2b8485989` passed hosted CI run 37620710587 and fixture reproduction run 37620710600.
- **Status:** Closed for the documented derived headless corpus. Original upstream reporting paths remain excluded.

### GB-CPU-002 / 2026-10-07 / Base-opcode semantic evidence

- **Cause and evidence:** The earlier base-opcode matrix visited every encoding but mostly asserted dispatch, PC/cost and flag shape. Independent verification scored CPU-01/D-01 incomplete because those checks did not prove each legal operation's register, flag, branch, address and bus effects.
- **Remedy:** Keep a test-authored expected architectural state independent from core execution, assert each legal opcode's state, enumerate taken and untaken conditional paths, add boundary arithmetic and timed address-effect vectors, and keep the eleven illegal encodings in separate lockup cases. Do not force a failing baseline when existing behavior is already correct.
- **Applies when:** An instruction matrix is used as evidence for semantic completeness or timing behavior.
- **Verification:** Five focused Plan 02-18 tests passed; the local suite and inventory passed 104/104 with no skips; installed C/C++ and inventory passed 109/109; independent verification passed 5/5 at implementation SHA `cf28e90270be24d9528bfa8a1e4055a2b8485989`.
- **Status:** Resolved with an independent expected-state oracle and exact-revision evidence; physical hardware behavior remains a separate limitation.

### GB-VIDEO-001 / 2026-10-07 / Plan GB-03-03 bus reachability

- **Cause and evidence:** `read8` and `write8` already applied PPU mode restrictions to VRAM/OAM, but `read_supported` excluded those addresses. Guest instructions stopped during preflight, so the timed lockout logic could not be observed.
- **Remedy:** Admit only mapped VRAM `$8000–$9FFF` and OAM `$FE00–$FE9F` in the bus preflight; keep cartridge RAM and unusable `$FEA0–$FEFF` unsupported. Retarget unsupported-boundary tests and exercise mode access through guest bus timestamps.
- **Applies when:** A device read/write path exists but instruction preflight separately declares which guest addresses can participate.
- **Verification:** DMA/PPU integration filter passed 23/23, full local CTest passed 125/125, and the current DMA/bus ASan/UBSan subset passed 13/13. Exact CPU-B contention remains outside these software results.
- **Source:** `src/core/gabbaboy.c`, `tests/test_bus.c`, `tests/test_dma.c`, and `docs/dmg-video-evidence.md`.
- **Status:** Fixed and verified for the declared model behavior; hardware applicability limits remain explicit.

### GB-TEST-001 / 2026-10-07 / Plan GB-03-03 HRAM guest fixture

- **Cause and evidence:** Extending a copied HRAM guest routine past 32 bytes caused its `$FFA0` scratch slot to overwrite byte 32 of the executing routine. The routine then read `$FF` as a loop immediate and restarted rather than reaching the post-transfer checks.
- **Remedy:** Move scratch bytes to `$FFB0+`, outside the routine, and reject generated probe routines larger than the 48-byte space before that scratch region.
- **Applies when:** A test program is copied into emulated memory and shares that address space with test scratch storage.
- **Verification:** `dma_hram` and all nine DMA cases pass; the Linux ASan/UBSan DMA/bus subset passed 13/13.
- **Source:** `tests/test_dma.c` and the captured guest bus/trace during fixture debugging.
- **Status:** Reproduced, bounded, and verified.

### GB-PLAYER-001 / 2026-10-07 / Plan GB-03-06 integer-scaled presentation

- **Cause and evidence:** SDL3 integer logical presentation computes a mathematically centered rectangle, which can have half-pixel x/y coordinates when an odd number of drawable pixels remain in the letterbox margins (for example, 327×299 produces a 320×288 viewport at 3.5,5.5). A pure geometry helper using integer origins would otherwise disagree with SDL or leave the final pixel placement untested.
- **Remedy:** Keep SDL's integer logical scale, derive the desired whole-pixel origin from drawable-pixel dimensions, and apply the difference as a logical-coordinate offset before rendering. Suppress the frame if a window surface falls below native dimensions.
- **Applies when:** A renderer uses integer logical scaling but requires pixel-aligned, centered presentation on odd output sizes.
- **Verification:** The optional SDL smoke compares helper and renderer geometry and reads software-rendered pixels at viewport edges for native, odd, letterboxed, and high-density sizes; all optional player cases pass 14/14.
- **Source:** `src/player/main.c`, `src/player/presentation.c`, `tests/player/test_presentation.c`, and [SDL3 logical presentation](https://wiki.libsdl.org/SDL3/SDL_SetRenderLogicalPresentation).
- **Status:** Reproduced and adopted; native desktop perception remains unverified because this environment has no desktop display.

### GB-ARTIFACT-002 / 2026-10-07 / Plan GB-03-09 relocated SDL package

- **Cause and evidence:** The package consumer originally compared the executable's RPATH to the consumer runner's expected build prefix. Separate hosted jobs need not share a workspace path, so that comparison could miss an extra build-host RPATH even while the expected package RPATH was present.
- **Remedy:** Parse every `LC_RPATH` entry and require the packaged executable to have exactly `@executable_path/../lib`; launch the binary after safe extraction to prove the bundled dylib and package-relative demo work together.
- **Applies when:** A native application is copied from one build machine to a separate artifact consumer or end-user installation.
- **Verification:** The extracted package passed locally; exact-head CI run 37686137977 built the clean arm64 candidate and preview run 37686137834 downloaded and smoke-tested its bytes. Both required aggregates passed.
- **Source:** `tests/scripts/verify-phase3-player.sh`, `.github/workflows/ci.yml`, `.github/workflows/preview.yml`, and `.planning/phases/GB-03-visible-interactive-dmg/03-09-SUMMARY.md`.
- **Status:** Fixed and verified for the SDL3 preview package; it does not establish general macOS signing or distribution behavior.

### GB-GSD-002 / 2026-10-07 / Phase 3 gap-plan test selection

- **Cause and evidence:** The first independent plan review found that enumerated CTest regexes could match existing DMA/JOYP tests while omitting newly added collision or sampling cases, so the planned commands could pass without running the cases they were meant to verify.
- **Remedy:** Require new DMA cases to use the `dma_*` family and new JOYP cases to use `joypad_*`; use family-wide CTest filters in each relevant task and checkpoint.
- **Applies when:** A plan adds registered tests to an existing CTest suite and its verification command selects cases by regex.
- **Verification:** The independent re-review passed all 11 plan structures, 14 tracked decisions, and seven probe-edge dispositions. The failure-direction probe found 23 commands with explicit failure statements and zero findings. This validates the plan filters and naming contract; implementation-level selection remains pending execution.
- **Source:** `.planning/phases/GB-03-visible-interactive-dmg/03-10-PLAN.md` and `03-PLAN-CHECK.md`.
- **Status:** Corrected in the executable gap plan; implementation evidence is pending.

### GB-EVIDENCE-001 / 2026-10-07 / Plan GB-03-10 source trace

- **Cause and evidence:** Text extraction flattened the Nintendo manual's superscript `2^4` to `24`, and the earlier DMG-CPU-B schematic URL used a commit SHA that did not resolve upstream. The printed manual page shows the exponent, while the verified schematic commit provides the referenced FF00, clock/reset, and FF0F source files.
- **Remedy:** Visually inspect scanned notation when typography changes a technical value, independently resolve immutable source revisions, and fetch the cited files before pinning a source claim. Keep derived-circuit connectivity separate from a validated timing trace.
- **Applies when:** Evidence is transcribed from scanned PDFs or OCR, or technical claims depend on external immutable revision links and reverse-engineered diagrams.
- **Verification:** The printed manual page was checked visually; all three schematic files were fetched from the verified commit. The JOYP/event CTest filter passed 8/8; exact CPU-B JOYP sample timing remains open.
- **Source:** `.planning/phases/GB-03-visible-interactive-dmg/03-RESEARCH.md`, `docs/dmg-video-evidence.md`, and the linked Nintendo manual and pinned schematic source.
- **Status:** Transcription and source pin corrected; no unsupported interrupt behavior was promoted.

### GB-GSD-003 / 2026-10-07 / Phase 3 gap loop

- **Cause and evidence:** Phase 3 had summaries for all 12 plans, but its latest goal check still found external hardware and visible-window evidence missing. Re-running gap planning without new evidence could only restate those gaps. An invalid MVP story format had also blocked the verifier before it could report the true 2/5 result.
- **Remedy:** Keep the phase goal in the required user-story format, run goal verification once after a meaningful implementation change, and write the exact missing evidence in plain English. Do not plan or execute another gap wave until a qualifying source, identified-hardware test record, or display-based observation changes the evidence. Keep automatic phase advancement off.
- **Applies when:** Plans are complete but acceptance still depends on hardware, a live display, credentials, or another external observation unavailable in the current environment.
- **Verification:** OpenGSD 1.16.0 accepted the normalized story; current Phase 3 verification reports `gaps_found` at 2/5; fresh `phase1` CTest passed 134/134; SDL could not create a window because this environment has no display. The reviewed CPU-B circuit model did not establish the missing collision or joypad-interrupt result.
- **Source:** `.planning/phases/GB-03-visible-interactive-dmg/03-VERIFICATION.md`, `.planning/phases/GB-03-visible-interactive-dmg/03-RESEARCH.md`, and `.planning/ROADMAP.md`.
- **Status:** Superseded by GB-GSD-004: its rule to wait for new CPU-B evidence was too strict for documented, reverse-engineered behavior where a deterministic software model was explicitly authorized.

### GB-GSD-004 / 2026-10-07 / Use confidence-qualified software models to close documented behavior gaps

- **Cause and evidence:** Phase 3 gap planning repeated because exact DMG-CPU-B collision and JOYP sampling values were unavailable, even though pinned Pan Docs describes broad OAM-DMA/PPU behavior, Nintendo's manual documents JOYP matrix/negative-edge behavior, and established emulators provide implementation cross-checks. The owner explicitly directed the project to use the best supported published information and label uncertainty; D-025 records that decision.
- **Remedy:** For behavior supported at a useful level by primary docs or reverse-engineering sources, select the narrowest deterministic software model, cross-check it against established implementations, explain policy choices in code/evidence, and add original guest controls. Keep chip-specific phases and unavailable physical observations open. After meaningful code and current tests change, run a fresh goal-backward audit before changing requirement status or planning another gap wave; stop at the phase boundary.
- **Applies when:** Published Game Boy documentation and pinned emulator/reverse-engineering sources support broad behavior but do not settle exact silicon revision, phase, lane, or collision outcomes.
- **Verification:** Plan 03-13 adds the selected JOYP IF.4 edge matrix, all active-DMA VRAM/OAM CPU access cells in PPU modes 0–3, mode-2 scan overlap controls, before/after DMA word-boundary pixels, the same-half-dot DMA/PPU/CPU guest collision, and partition-equivalence checks. Follow-up review fixed entry-39 scanning and reset-cursor handling, with guest regressions for both. Focused JOYP/DMA/PPU review checks passed 17/17; the full SDL-free `phase1` suite passed 141/141. Final UAT passed 33/33 after the user confirmed the packaged Z press/release behavior; goal-backward verification passed 5/5. A historic CPU-B-only UAT checkpoint was reconciled to D-025's adopted software-model acceptance rather than misrepresented as a hardware measurement. Exact CPU-B electrical timing, byte lane, low-pulse qualification, and PPU-revision parity remain unmeasured.
- **Source:** D-025 in `.planning/context/DECISIONS.md`, the 2026-10-07 addendum in `.planning/phases/GB-03-visible-interactive-dmg/03-RESEARCH.md`, `.planning/phases/GB-03-visible-interactive-dmg/03-13-SUMMARY.md`, and `docs/dmg-video-evidence.md`.
- **Status:** Applied to VIDEO-02/03 in Phase 3 under confidence-qualified software behavior; VIDEO-04 passed the user's live packaged-preview check. The full project still makes no exact CPU-B timing or silicon-parity claim.

### GB-FIXTURE-001 / 2026-10-08 / Preserve fixture bytes across Windows checkout

- **Cause and evidence:** The first Phase 4 Windows installed-package run failed only at the authored MBC1 fixture digest checks. Git's Windows text conversion rewrote `continuation.asm` because the fixture directory had no path-specific attributes; expected assembly/ROM digests remained stable on macOS/Linux. This was a checkout transformation, not a mismatch in the fixture recipe.
- **Remedy:** Add narrow `.gitattributes` rules forcing LF for the assembly, manifest, and license, and `-text` for the generated ROM. Keep digest checks fail-closed and print expected plus observed hashes when they differ. Do not normalize checked-in binary fixtures or weaken manifest validation.
- **Applies when:** Checked-in fixture source and generated binary artifacts are hash-verified across Git clients with differing `core.autocrlf` settings.
- **Verification:** A fresh checkout with `core.autocrlf=true` retained the source SHA-256 `ad82e0cd51eeb6d536421d20c4a5b88ee0c019a4e699c2c75de077a20c82ba94` and ROM SHA-256 `f89bf3884ff10a702aa117f2963e6fe9ea8aeac3a9bc003f52b6c5ca6abfbbd2`. The exact PR-head Windows inventory passed, and RGBDS 1.0.1 fixture reproduction passed in hosted CI run 37728192634.
- **Source:** `.gitattributes`, `cmake/VerifyInstalledPackage.cmake`, `fixtures/mbc1-continuation/manifest.json`, Phase 4 review and validation.
- **Status:** Fixed and verified for the authored MBC1 fixture across the exercised Windows, macOS, and Linux paths.

### GB-TEST-001 / 2026-10-08 / Isolate macOS preference storage in sandboxed player tests

- **Cause and evidence:** `player_smoke` stages a real battery lock through the production `SDL_GetPrefPath` path. The sandbox denied that write because SDL 3.4.18's Cocoa implementation resolves `NSApplicationSupportDirectory` through Foundation, which ignored a plain `HOME` override and pointed outside the writable workspace/temp roots. The exact test error was `Could not open the battery session lock safely.`
- **Remedy:** For local sandbox runs, set both `HOME` and `CFFIXED_USER_HOME` to a newly created directory under `/private/tmp`; do not weaken lock checks or change the product's save path to suit the test harness. The hosted macOS runner uses its normal writable account preferences path.
- **Applies when:** Native macOS tests exercise application-preference or save paths under restricted filesystem permissions.
- **Verification:** `HOME` alone reproduced the failure. With `CFFIXED_USER_HOME` redirected, targeted `player_smoke` passed, then the complete pinned SDL 3.4.18 package/player verifier passed 37/37 and fresh-process MBC1 continuation passed. The full core CTest regression suite passed 155/155.
- **Source:** `tests/scripts/verify-phase3-player.sh`, `src/player/main.c`, `src/player/session.c`, and pinned `SDL3-3.4.18/src/filesystem/cocoa/SDL_sysfilesystem.m`.
- **Status:** Environment root cause confirmed and local regression coverage restored; no product-code change required.

### GB-GSD-005 / 2026-10-08 / Verify composite player lifecycle paths

- **Cause and evidence:** HOST-02 combined pause, reset, replacement, and device transitions. Component tests and source tracing initially left the normal R-reset event path without combined behavior evidence; after that gap was closed, a fresh goal-backward pass found the normal Space pause/resume path also lacked app-level evidence that host PCM clears while guest APU history is retained.
- **Remedy:** For composite lifecycle requirements, drive each consequential app event through the real event pump. Assert host queue effects and session state directly; compare resumed guest output to an uninterrupted reference when preservation of emulated history is required.
- **Applies when:** A success criterion combines multiple user-triggered transitions and component-level tests do not prove their orchestration order.
- **Verification:** `tests/player/test_reset_transition.c` exercises Space pause/resume with exact PCM flush accounting and resumed PCM equality against an uninterrupted guest, plus R-reset save failure, cancel, retry, and persisted battery recovery. Final player/package CTest passed 50/50, and Phase 5 goal verification passed 22/22 at `d4d847abc9fd75229312c7530f2d69a7b2e08d94`.
- **Source:** `tests/player/test_reset_transition.c`, Phase 5 verification and validation reports.
- **Status:** Adopted for app-level lifecycle transition coverage; no hardware or perceptual claim follows from this software test.

### GB-RELEASE-001 / 2026-10-09 / Review first-release changelog comparison links

- **Cause and evidence:** The initial Release Please changelog rendered the `v0.1.0` entry as a comparison from `v0.1.0` to itself, which has an empty range and hides the release contents. The standard-depth Phase 6 review identified it at `CHANGELOG.md:3`.
- **Remedy:** For a first release with no prior version tag, link the changelog entry directly to the published release page. Keep comparison links only when there is a real previous tag.
- **Applies when:** Bootstrapping a repository's first generated changelog entry or another release stream whose previous comparison endpoint does not exist.
- **Verification:** `CHANGELOG.md:3` now links to the `v0.1.0` release page; `06-REVIEW-DISPOSITION.md` records WR-01 fixed and zero open findings; `git diff --check` passed.
- **Source:** `CHANGELOG.md`, `06-REVIEW.md`, and `06-REVIEW-DISPOSITION.md`.
- **Status:** Fixed and verified for the initial v0.1.0 release.

### GB-GSD-006 / 2026-10-09 / Make the project test gate explicit to GSD

- **Cause and evidence:** The repository is CMake/CTest-based, but no `workflow.test_command` was configured. The GSD regression gate therefore resolved to a no-op `true`, which is not evidence that tests ran. The closeout caught this before accepting phase completion.
- **Remedy:** Configure a project-specific test command for future phases, or make the workflow's documented fallback recognize CMake/CTest. Until corrected, invoke the repository's documented configure/build/CTest command directly and record the actual test denominator and result; do not count a no-op gate as validation. The owner-owned `.planning/config.json` scratch was preserved, not modified.
- **Applies when:** A project uses a non-default build/test system and workflow automation derives its test command from configuration.
- **Verification:** `cmake --preset phase1 -DGABBABOY_BUILD_PLAYER=OFF && cmake --build --preset phase1 --parallel 2 && ctest --preset phase1 --output-on-failure --no-tests=error` passed 176/176. The verifier report and `.planning/.continue-here.md` record the configured-command limitation and test result.
- **Source:** `.planning/phases/GB-06-qualified-dmg-release-and-consumer-handoff/06-VERIFICATION.md`, `.planning/STATE.md`, and `.planning/.continue-here.md`.
- **Status:** Phase 6 validation is evidenced; configure the GSD test command as follow-up workflow maintenance, without editing preserved owner scratch during this closeout.

### GB-GSD-007 / 2026-10-09 / Check canonical freshness and solo-maintainer merge policy at milestone handoff

- **Cause and evidence:** The v0.1 audit found that historical passing reports for Phases 1–4 no longer pass OpenGSD's current `verification.status` gate because covered files changed after their digests were recorded. The audit snapshot also showed a one-approval rule with admin enforcement disabled; PR #34 had no recorded approval, though required exact-head CI passed. Follow-up readback showed the approval rule absent.
- **Remedy:** At milestone audit, query canonical verification status for every phase instead of trusting report frontmatter alone. For a solo-maintainer repository, keep the human approval count at zero and enforce strict required CI contexts for admins; preserve the project's AI/code-review and test evidence in the normal workflow. Reassess approval requirements if independent maintainers join.
- **Applies when:** OpenGSD verification uses covered-file digests, or a single maintainer uses GitHub branch protection without a second human reviewer.
- **Verification:** OpenGSD 1.16.0 reports Phases 1–4 stale and Phases 5–6 passed. Follow-up GitHub readback reports `required_pull_request_reviews: null`, `enforce_admins: true`, and the unchanged strict contexts `required-native`, `fixture-repro`, and `preview-package-smoke`.
- **Source:** `.planning/v0.1-MILESTONE-AUDIT.md`, phase `VERIFICATION.md` reports, and PR #34 branch-protection/check evidence.
- **Status:** Superseded for freshness counts by GB-GSD-008; the branch-rule update remains verified, while the later 2026-10-09 audit found current Phase 1/3/5/6 gates stale and Phase 2/4 passing.

### GB-TEST-002 / 2026-10-09 / Make concurrent-instance tests distinguish state and bound hangs

- **Cause and evidence:** The supplemental Phase 1 review found that identical concurrent guest workloads could mask shared-state interference, a later reset could erase an unasserted run result, and the concurrency test had unbounded readiness/start waits without a process timeout.
- **Remedy:** Use distinct guest-visible values per instance, assert each run's stop reason, budget, trace bounds, and RAM effect before resetting again, and apply a CTest wall-clock timeout to threaded runner tests.
- **Applies when:** Tests exercise independent emulator instances concurrently or use host synchronization that could stall independently of guest instruction budgets.
- **Verification:** The reviewed tests passed in the full local CTest suite, 179/179; the final source recheck reported clean with all reset, concurrency, timeout, Windows cleanup, and help-output findings resolved. PR #35 head `d1e5fdb3b23256f06694cd8d91613638612bccb8` was merged as `96f76dec9a675ede45da8d75bd72a5141c7419e4`; all required exact-head contexts passed: `required-native` run `37928170860`, `fixture-repro` run `37928170722`, and `preview-package-smoke` run `37928170973`. The two preview artifacts were independently checked for sidecar provenance, retention, digest, and safe extraction.
- **Source:** `tests/test_api.c`, `tests/test_instance_concurrency.c`, `tests/CMakeLists.txt`, and Phase 1 `01-REVIEW.md` / `01-VALIDATION.md`.
- **Status:** Corrected locally; exact-revision hosted validation is pending.

### GB-SMOKE-001 / 2026-10-09 / Isolate SDL player smoke preferences

- **Cause and evidence:** The player smoke's synthetic battery lock uses SDL's per-user preferences path. On macOS, SDL 3.4.18 resolves this through Cocoa's `NSApplicationSupportDirectory`; a plain `HOME` override does not redirect Foundation, and a sandboxed run can fail or touch normal user saves.
- **Remedy:** Give the `player_smoke` CTest a build-local `HOME` and `CFFIXED_USER_HOME`. Give the downloaded-package smoke a unique temporary home and remove it on exit. Keep production save routing unchanged and do not weaken lock checks.
- **Applies when:** Native macOS tests or package smokes exercise application preferences, battery saves, or lock files in restricted environments.
- **Verification:** `player_smoke` passed under its CTest environment; all 50 player tests passed; the pinned SDL 3.4.18 package build and extracted-byte smoke passed with MBC1 continuation; the combined suite passed 229/229. Exact PR head `de966868057c1fb5b3bca5b4cdac50cadf3bae57` passed required-native, fixture-repro, and preview-package-smoke in runs 37942469774, 37942469816, and 37942469925.
- **Source:** `tests/player/CMakeLists.txt`, `tests/scripts/verify-phase3-player.sh`, `src/player/main.c`, and existing lesson GB-TEST-001.
- **Status:** Adopted and exact-revision hosted validation passed.

### GB-GSD-008 / 2026-10-09 / Audit runtime freshness, summary parseability, and state source

- **Cause and evidence:** Saved VERIFICATION.md frontmatter can continue to say `passed` after its covered-file digest changes. On the v0.1 audit, OpenGSD 1.16.0 accepted only Phases 2 and 4 and returned stale for Phases 1, 3, 5, and 6. The same audit found CPU-02/CPU-05 absent from all parseable `requirements-completed` summaries and `summary-extract` errors for `03-12-SUMMARY.md` and `04-02-SUMMARY.md`. `init.milestone-op` reported two completed phases although ROADMAP.md records six; `.planning/state.json` was modified owner scratch and intentionally preserved.
- **Remedy:** At milestone audit, query `verification.status` for every phase, run `summary-extract` for every summary, and compute requirement status from the live gate plus valid summary metadata plus traceability. Treat `state.json`/ROADMAP disagreement as a signal to reconcile, not permission to overwrite owner scratch. Repair summary metadata only with a corresponding verification refresh when covered-file digests change.
- **Applies when:** OpenGSD uses covered-file verification fingerprints and plan-summary metadata for milestone aggregation, especially in a checkout with preserved local planning edits.
- **Verification:** The v0.1 audit recorded the exact six phase gates, all 35 requirement IDs, both summary parser errors, 6/6 wired flows, and the conflicting init/ROADMAP phase counts. The follow-up route refreshed Phase 1; the remaining route is `$gsd-execute-phase 3`, then Phases 5 and 6 one at a time, then re-audit.
- **Source:** `.planning/v0.1-MILESTONE-AUDIT.md`, `.planning/REQUIREMENTS.md`, phase VERIFICATION.md and SUMMARY.md files, and OpenGSD 1.16.0 query results.
- **Status:** Adopted as the milestone-audit procedure; Phases 3, 5, 6 and CPU-02/CPU-05 metadata reconciliation remain pending.

### GB-GSD-009 / 2026-10-09 / Verify on the integrated tree, not a historical phase branch

- **Cause and evidence:** OpenGSD's computed Phase 1 and Phase 3 branches already existed but were historical checkpoints: Phase 1's branch had no Phase 2 verification artifact and its core was 164 lines versus 2,305 lines in the current tree; Phase 3's branch had no Phase 4 verification artifact. Switching would verify older source and risk losing the current dirty Phase 4 work.
- **Remedy:** Before reusing an existing phase branch for a freshness-only verification, confirm it contains the integrated source revision being audited. If it is historical, preserve the active worktree and run the read-only verifier there; do not force a checkout or carry unrelated dirty files onto the old branch.
- **Applies when:** Re-running verification for a previously completed phase after later phases changed shared source files and local worktree edits must be preserved.
- **Verification:** The Phase 1 verifier ran on the current integrated worktree, passed 21/21 truths and 29/29 focused CTest cases, and regenerated the canonical fingerprint. Both historical branches were left untouched; Phase 3 is the next refresh and carries the same branch guard.
- **Source:** OpenGSD 1.16.0 `init.execute-phase`, `git cat-file`, current phase VERIFICATION.md files, and source tree comparisons.
- **Status:** Adopted for Phase 1; apply the same revision check to the remaining stale phases.

### GB-GAME-001 / 2026-10-10 / Require game-level progress before breadth claims

- **Cause and evidence:** Glueyneo's selected guest ran through its bounded 256-chunk/32-million-instruction attempt without a guest-written attract/start predicate; subsystem tests and visible device activity did not prove game progress. GabbaBoy's original visible-demo fixture and Z-down/Z-up shade test prove the player input/render path, not compatibility with a representative supported game. These examples support an end-to-end acceptance gate, not any shared console behavior.
- **Remedy:** Before the future GB/GBC breadth milestone claims broader playable support, select one rights-clear ROM-only or standard-MBC1 game and define a guest-observable start/progress condition plus meaningful input and visible/audio response in the existing player. Keep commercial/private ROMs and derived traces out of the repository unless redistribution rights are documented. If it stalls, use a bounded PC/opcode/bus/interrupt trace to identify the first unsupported or incorrect operation, add a small rights-clear regression for that behavior, and rerun the bounded game check; more runtime or peripheral activity is not a pass signal.
- **Applies when:** A milestone expands cartridge or model support and intends to claim that users can play a supported game end to end.
- **Does not establish:** That GabbaBoy currently boots a complete game, that the tile demo is gameplay evidence, or that any DMG timing/model assumption applies to Neo Geo.
- **Suggested check:** Plan one lawful game-level acceptance target before broadening CGB/mapper claims; require its explicit guest progress signal and player-visible input/output, while preserving private content and evidence.
- **Source:** Glueyneo: `.planning/workstreams/first-playable-game/phases/05-selected-mvs-boot/05-03-SUMMARY.md` and `.planning/preparation/2026-10-04-gsd-verification-loop.md`; GabbaBoy: `.planning/phases/GB-03-visible-interactive-dmg/03-VERIFICATION.md`, `.planning/phases/GB-03-visible-interactive-dmg/03-UAT.md`, `.planning/context/FUTURE-MILESTONES.md`, and `AGENTS.md`.
- **Status:** Sanity-checked and adopted as a future milestone planning gate; no active phase or release claim changed.

### GB-GSD-010 / 2026-10-10 / Tightening a shared helper's input contract requires a caller sweep

- **Cause and evidence:** The verified-output helper changed from rejecting only the repository root to rejecting every repository descendant. `release.yml` still passed `build/release-player-downloaded`, so the next release's downloaded-player smoke would have failed at publication, after the expensive package checks. Neither the Phase 6 deep review of the helper nor local verification caught it, because local verifier mode never calls `--publish`. The Phase 3 refresh review found it by reading the workflow callers.
- **Remedy:** When a helper's accepted inputs narrow, grep every caller (workflows, scripts, docs) for the affected parameter before review sign-off. Add a regression test that asserts each workflow assignment satisfies the contract (here, a runner-temp child path), so the mismatch fails locally rather than during a release.
- **Applies when:** A safety check is tightened in a script that CI workflows invoke with caller-chosen paths or values.
- **Verification:** `test_workflows_place_verified_output_outside_the_checkout` failed on the two `release.yml` values and passed after commit `91d11d4`. The helper suite passed 20/20, both release self-tests passed, and PR #47 hosted checks passed 23/23 at `56c4915`.
- **Status:** Adopted.

### GB-GSD-011 / 2026-10-10 / Verify merge results for conflict markers and stash-only evidence

- **Cause and evidence:** Merging `origin/main` into the Phase 3 refresh branch left conflict markers in `.planning/.continue-here.md`, and no conflict was reported for that file. Separately, STATE.md said Phases 1 and 2–6 were fresh based on reports that existed only in an uncommitted worktree. The committed Phase 1 report was already stale at `c8b8426`.
- **Remedy:** After any merge, run `git grep -nE '^(<<<<<<<|>>>>>>>) '` before committing. Before routing or claiming freshness, query `verification.status` on committed content, not a dirty overlay. Commit or explicitly stash refreshed reports at the end of each refresh so the next session's starting point is reproducible.
- **Applies when:** Several verification refreshes run across sessions with preserved dirty worktrees, or a phase branch merges the default branch.
- **Verification:** The marker was found and replaced in commit `56c4915`. A detached worktree at `c8b8426` confirmed Phase 1 was stale. The stash contents were reconciled file by file before restoration.
- **Status:** Adopted.

### GB-GSD-012 / 2026-10-10 / A debt-closure phase must dispose of every audit line, not just the review findings

- **Cause and evidence:** ROADMAP criterion 1 for Phase 06.1 says "each audit tech-debt item is fixed or re-deferred with a recorded reason". `06.1-CONTEXT.md` and `06.1-DEBT-DISPOSITION.md` covered only the review info items and the audio gap. The first verifier pass returned `human_needed` because six of the twelve `tech_debt` lines in `v0.1-MILESTONE-AUDIT.md` had no row. These were scope limits and informational notes: Phase 1 `wave_0_complete`, thin CPU-03 credit, physical CPU-B timing, PR #41, PR-only player lanes, and no hardware qualification. Separately, `phase.complete` on the last phase set STATE `status: completed` and set the `state.json` next command to `/gsd:new-milestone`. That contradicted the recorded owner route of re-auditing first.
- **Remedy:** When planning a debt-closure phase, copy the audit's whole `tech_debt` list into the disposition table. Give each line fixed, re-deferred or accepted, with a reason and a revisit trigger, including lines that are already scope limits. After `phase.complete`, review the STATE frontmatter status and the `state.json` next command against the persisted route before committing.
- **Applies when:** A phase exists to close milestone-audit debt, or `phase.complete` runs on the last roadmap phase before the milestone is re-audited.
- **Verification:** Commit `05d4913` added the six rows. The re-run verifier compared all 12 audit lines with the disposition table and returned `passed` 4/4. STATE was kept `executing`, and the next command is `$gsd-audit-milestone v0.1`.
- **Status:** Adopted.
