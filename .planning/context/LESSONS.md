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
| XFER-007 | Review-fix loops that each expose new gate holes never converge. Glueyneo Phase 04 ran 11 rounds over 65 plans, about 59 of them on tooling; nesturbator Phase 16 ran to 59 plans. Sources: glueyneo `.planning/METHODOLOGY.md`, nesturbator `16-RECOVERY.md` (both read 2026-10-24) | Adopted as D-102 round and plan caps, enforced by a CTest with a negative control | Adopted at v0.3 kickoff; enforcement check lands in Phase 16 |
| XFER-008 | Self-imposed quotas, wall-clock allowances and run counters became the work. Genewhip Phase 6: 44 planning commits against 6 `src/` commits. Glueyneo old Phase 05: 157 "rerun N" commits | D-102: none of these counts as verification evidence | Adopted |
| XFER-009 | A state codec silently misses fields unless the full state is machine-checked. Glueyneo has a struct-inventory checker and an `nm` writable-global CTest | Land both before the STATE-01 codec (Phase 17 first plan) | Imported; implementation pending |
| XFER-010 | A single field list driving size, write, validate and apply keeps save and load symmetric. Nesturbator v3 Phase 12 shipped it in 10 plans; cogmaster uses a visitor with `_Static_assert` tripwires | STATE-01 codec design (research/v0.3/SAVE-STATES.md) | Imported; implementation pending |
| XFER-011 | A state with a valid CRC but a 64-bit tick count near 2^64 hung the next frame (nesturbator `12-REVIEW.md`, fix `c6c1c69`) | Bound every 64-bit time field at 2^62 during state validation | Imported; implementation pending |
| XFER-012 | A loader accepted counter limits that one frame of execution could exceed, so the state it saved next was rejected (schwaystation `01-REVIEW.md`, fix `b7c658a`) | Closure property test: any accepted state, run N steps, still saves to an accepted state | Imported; implementation pending |
| XFER-013 | 69 offline checks passed while the real compiled path never ran (genewhip `ea0c6ef`) | D-105: the first plan of a feature exercises the compiled public API | Adopted |
| XFER-014 | Playstead sends SIGTERM and then SIGKILL about 2 s later; mGBA and RetroArch on macOS do not flush saves on SIGTERM (Playstead `AdapterHost.swift`, read 2026-10-24) | INT-01a: save-and-exit 0 well under 2 s, handled in the adapter only, tested with real signals | Imported; implementation pending |
| XFER-015 | Decide the closeout and freshness policy before work starts, not after verification goes stale (muhtari `GSD-HANDOFF.md`, cogmaster `GSD-HANDOFF.md`) | D-103: re-verify at the exact final head and aim for a verified closeout | Adopted, with GabbaBoy's stricter variant |
| XFER-016 | Duplicate lesson ids go unnoticed without a check (schwaystation `policy.lessons_unique`). GabbaBoy had GB-FIXTURE-001 three times and GB-TEST-001 twice (renumbered in Phase 16: the later duplicates are now GB-FIXTURE-003, GB-FIXTURE-004 and GB-TEST-007) | Phase 16: renumber the duplicates and add a uniqueness test | Imported; implemented in Phase 16 (`lessons_unique_ids`) |
| XFER-017 | A rolling product roadmap with stable ids, statuses, promotion triggers and a snapshot at each close keeps milestones scoped (nesturbator `v3-PRODUCT-ROADMAP.md`, muhtari `v1.0-PRODUCT-ROADMAP.md`) | FUTURE-MILESTONES.md revision 3 | Adopted |
| XFER-018 | Muhtari MU-GSD-014 at `7b83b3b` distinguishes summarized slots, accepted outcomes and historical task counts; an aggregate can miscount completion | Audit actual requirements/outcomes and immutable source evidence; preserve the halted 19-06 snapshot and reconcile it through later accepted records | Observed sibling mechanism; applied in the v0.3 audit |
| XFER-019 | Playstead Phase 16 lessons at `bcd93b6` require a failure-path remedy and tests of the real default I/O provider, not only injected providers | Preserve real host filesystem, signal, rollback and installed-package continuation checks; a software remedy is implementable work, not an external prerequisite | Source-inspected; GabbaBoy host/slot controls provide local evidence |
| XFER-020 | Cogmaster XFER-078 at `1336d3f` records configure-time revision staleness; the current audit reproduced it in state_fuzz_controls after a documentation commit | Reconfigure/build/install before final-head verification; retain the original failure instead of weakening the immutable revision check | Reproduced locally; final suite evidence in v0.3 milestone audit |
| XFER-021 | Glueyneo methodology at `b96c78d`, Nesturbator active-core lessons at `89a042b` and Genewhip seam analysis at `18df6d7` separate retained records, fresh execution and product/model claims | Reuse adequate unchanged evidence, distinguish oracle/gate failures from core defects, and scope future game observations to model/scene/source | Observed; confirms D-069/D-103 and existing evidence classes |

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
- **Source:** `.github/scripts/verify-test-inventory.sh`, `.github/workflows/ci.yml`, `.planning/milestones/v0.1-phases/GB-01-portable-foundation-and-original-rom-tracer/01-04-SUMMARY.md`.
- **Status:** Reproduced and adopted.

### GB-GSD-001 / 2026-10-03 / Phase 1 closeout

- **Symptom and reproduction:** OpenGSD 1.15.0 reported Phase 1 as `7/5` plans at `phase.complete`, while the roadmap contains five plans. The directory has five distinct `*-PLAN.md` files and five unique summaries; two tracked `01-01-SUMMARY.md` and `01-02-SUMMARY.md` paths are symlinks to the matching `GB-01-*` summary files and were counted twice.
- **Root cause / invariant:** The phase uses both the milestone-prefixed summary names and legacy plan-ID aliases. A raw count of summary paths is not a count of completed plans when aliases point to the same content.
- **Fix and evidence:** Reconciled completion against plan IDs, kept the compatibility symlinks, and corrected ROADMAP/STATE to 5/5. All eight Phase 1 truths passed the independent verifier; the exact plan inventory has five plans and five unique summaries.
- **Applies when:** A phase retains legacy summary-name symlinks after a milestone/plan naming migration.
- **Does not establish:** A fix to OpenGSD's alias-counting behavior; the runtime may still display an inflated raw summary-path count.
- **Suggested check:** Compare unique plan IDs and resolved summary targets, not only the number of `*-SUMMARY.md` paths.
- **Source:** `.planning/milestones/v0.1-phases/GB-01-portable-foundation-and-original-rom-tracer/01-VERIFICATION.md`, `.planning/ROADMAP.md`, `.planning/STATE.md`.
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
- **Source:** `tests/scripts/verify-phase3-player.sh`, `.github/workflows/ci.yml`, `.github/workflows/preview.yml`, and `.planning/milestones/v0.1-phases/GB-03-visible-interactive-dmg/03-09-SUMMARY.md`.
- **Status:** Fixed and verified for the SDL3 preview package; it does not establish general macOS signing or distribution behavior.

### GB-GSD-002 / 2026-10-07 / Phase 3 gap-plan test selection

- **Cause and evidence:** The first independent plan review found that enumerated CTest regexes could match existing DMA/JOYP tests while omitting newly added collision or sampling cases, so the planned commands could pass without running the cases they were meant to verify.
- **Remedy:** Require new DMA cases to use the `dma_*` family and new JOYP cases to use `joypad_*`; use family-wide CTest filters in each relevant task and checkpoint.
- **Applies when:** A plan adds registered tests to an existing CTest suite and its verification command selects cases by regex.
- **Verification:** The independent re-review passed all 11 plan structures, 14 tracked decisions, and seven probe-edge dispositions. The failure-direction probe found 23 commands with explicit failure statements and zero findings. This validates the plan filters and naming contract; implementation-level selection remains pending execution.
- **Source:** `.planning/milestones/v0.1-phases/GB-03-visible-interactive-dmg/03-10-PLAN.md` and `03-PLAN-CHECK.md`.
- **Status:** Corrected in the executable gap plan; implementation evidence is pending.

### GB-EVIDENCE-001 / 2026-10-07 / Plan GB-03-10 source trace

- **Cause and evidence:** Text extraction flattened the Nintendo manual's superscript `2^4` to `24`, and the earlier DMG-CPU-B schematic URL used a commit SHA that did not resolve upstream. The printed manual page shows the exponent, while the verified schematic commit provides the referenced FF00, clock/reset, and FF0F source files.
- **Remedy:** Visually inspect scanned notation when typography changes a technical value, independently resolve immutable source revisions, and fetch the cited files before pinning a source claim. Keep derived-circuit connectivity separate from a validated timing trace.
- **Applies when:** Evidence is transcribed from scanned PDFs or OCR, or technical claims depend on external immutable revision links and reverse-engineered diagrams.
- **Verification:** The printed manual page was checked visually; all three schematic files were fetched from the verified commit. The JOYP/event CTest filter passed 8/8; exact CPU-B JOYP sample timing remains open.
- **Source:** `.planning/milestones/v0.1-phases/GB-03-visible-interactive-dmg/03-RESEARCH.md`, `docs/dmg-video-evidence.md`, and the linked Nintendo manual and pinned schematic source.
- **Status:** Transcription and source pin corrected; no unsupported interrupt behavior was promoted.

### GB-GSD-003 / 2026-10-07 / Phase 3 gap loop

- **Cause and evidence:** Phase 3 had summaries for all 12 plans, but its latest goal check still found external hardware and visible-window evidence missing. Re-running gap planning without new evidence could only restate those gaps. An invalid MVP story format had also blocked the verifier before it could report the true 2/5 result.
- **Remedy:** Keep the phase goal in the required user-story format, run goal verification once after a meaningful implementation change, and write the exact missing evidence in plain English. Do not plan or execute another gap wave until a qualifying source, identified-hardware test record, or display-based observation changes the evidence. Keep automatic phase advancement off.
- **Applies when:** Plans are complete but acceptance still depends on hardware, a live display, credentials, or another external observation unavailable in the current environment.
- **Verification:** OpenGSD 1.16.0 accepted the normalized story; current Phase 3 verification reports `gaps_found` at 2/5; fresh `phase1` CTest passed 134/134; SDL could not create a window because this environment has no display. The reviewed CPU-B circuit model did not establish the missing collision or joypad-interrupt result.
- **Source:** `.planning/milestones/v0.1-phases/GB-03-visible-interactive-dmg/03-VERIFICATION.md`, `.planning/milestones/v0.1-phases/GB-03-visible-interactive-dmg/03-RESEARCH.md`, and `.planning/ROADMAP.md`.
- **Status:** Superseded by GB-GSD-004: its rule to wait for new CPU-B evidence was too strict for documented, reverse-engineered behavior where a deterministic software model was explicitly authorized.

### GB-GSD-004 / 2026-10-07 / Use confidence-qualified software models to close documented behavior gaps

- **Cause and evidence:** Phase 3 gap planning repeated because exact DMG-CPU-B collision and JOYP sampling values were unavailable, even though pinned Pan Docs describes broad OAM-DMA/PPU behavior, Nintendo's manual documents JOYP matrix/negative-edge behavior, and established emulators provide implementation cross-checks. The owner explicitly directed the project to use the best supported published information and label uncertainty; D-025 records that decision.
- **Remedy:** For behavior supported at a useful level by primary docs or reverse-engineering sources, select the narrowest deterministic software model, cross-check it against established implementations, explain policy choices in code/evidence, and add original guest controls. Keep chip-specific phases and unavailable physical observations open. After meaningful code and current tests change, run a fresh goal-backward audit before changing requirement status or planning another gap wave; stop at the phase boundary.
- **Applies when:** Published Game Boy documentation and pinned emulator/reverse-engineering sources support broad behavior but do not settle exact silicon revision, phase, lane, or collision outcomes.
- **Verification:** Plan 03-13 adds the selected JOYP IF.4 edge matrix, all active-DMA VRAM/OAM CPU access cells in PPU modes 0–3, mode-2 scan overlap controls, before/after DMA word-boundary pixels, the same-half-dot DMA/PPU/CPU guest collision, and partition-equivalence checks. Follow-up review fixed entry-39 scanning and reset-cursor handling, with guest regressions for both. Focused JOYP/DMA/PPU review checks passed 17/17; the full SDL-free `phase1` suite passed 141/141. Final UAT passed 33/33 after the user confirmed the packaged Z press/release behavior; goal-backward verification passed 5/5. A historic CPU-B-only UAT checkpoint was reconciled to D-025's adopted software-model acceptance rather than misrepresented as a hardware measurement. Exact CPU-B electrical timing, byte lane, low-pulse qualification, and PPU-revision parity remain unmeasured.
- **Source:** D-025 in `.planning/context/DECISIONS.md`, the 2026-10-07 addendum in `.planning/milestones/v0.1-phases/GB-03-visible-interactive-dmg/03-RESEARCH.md`, `.planning/milestones/v0.1-phases/GB-03-visible-interactive-dmg/03-13-SUMMARY.md`, and `docs/dmg-video-evidence.md`.
- **Status:** Applied to VIDEO-02/03 in Phase 3 under confidence-qualified software behavior; VIDEO-04 passed the user's live packaged-preview check. The full project still makes no exact CPU-B timing or silicon-parity claim.

### GB-FIXTURE-003 / 2026-10-08 / Preserve fixture bytes across Windows checkout

- **Cause and evidence:** The first Phase 4 Windows installed-package run failed only at the authored MBC1 fixture digest checks. Git's Windows text conversion rewrote `continuation.asm` because the fixture directory had no path-specific attributes; expected assembly/ROM digests remained stable on macOS/Linux. This was a checkout transformation, not a mismatch in the fixture recipe.
- **Remedy:** Add narrow `.gitattributes` rules forcing LF for the assembly, manifest, and license, and `-text` for the generated ROM. Keep digest checks fail-closed and print expected plus observed hashes when they differ. Do not normalize checked-in binary fixtures or weaken manifest validation.
- **Applies when:** Checked-in fixture source and generated binary artifacts are hash-verified across Git clients with differing `core.autocrlf` settings.
- **Verification:** A fresh checkout with `core.autocrlf=true` retained the source SHA-256 `ad82e0cd51eeb6d536421d20c4a5b88ee0c019a4e699c2c75de077a20c82ba94` and ROM SHA-256 `f89bf3884ff10a702aa117f2963e6fe9ea8aeac3a9bc003f52b6c5ca6abfbbd2`. The exact PR-head Windows inventory passed, and RGBDS 1.0.1 fixture reproduction passed in hosted CI run 37728192634.
- **Source:** `.gitattributes`, `cmake/VerifyInstalledPackage.cmake`, `fixtures/mbc1-continuation/manifest.json`, Phase 4 review and validation.
- **Status:** Fixed and verified for the authored MBC1 fixture across the exercised Windows, macOS, and Linux paths.

### GB-TEST-007 / 2026-10-08 / Isolate macOS preference storage in sandboxed player tests

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
- **Source:** `.planning/milestones/v0.1-phases/GB-06-qualified-dmg-release-and-consumer-handoff/06-VERIFICATION.md`, `.planning/STATE.md`, and `.planning/.continue-here.md`.
- **Status:** Phase 6 validation is evidenced; configure the GSD test command as follow-up workflow maintenance, without editing preserved owner scratch during this closeout.

### GB-GSD-007 / 2026-10-09 / Check canonical freshness and solo-maintainer merge policy at milestone handoff

- **Cause and evidence:** The v0.1 audit found that historical passing reports for Phases 1–4 no longer pass OpenGSD's current `verification.status` gate because covered files changed after their digests were recorded. The audit snapshot also showed a one-approval rule with admin enforcement disabled; PR #34 had no recorded approval, though required exact-head CI passed. Follow-up readback showed the approval rule absent.
- **Remedy:** At milestone audit, query canonical verification status for every phase instead of trusting report frontmatter alone. For a solo-maintainer repository, keep the human approval count at zero and enforce strict required CI contexts for admins; preserve the project's AI/code-review and test evidence in the normal workflow. Reassess approval requirements if independent maintainers join.
- **Applies when:** OpenGSD verification uses covered-file digests, or a single maintainer uses GitHub branch protection without a second human reviewer.
- **Verification:** OpenGSD 1.16.0 reports Phases 1–4 stale and Phases 5–6 passed. Follow-up GitHub readback reports `required_pull_request_reviews: null`, `enforce_admins: true`, and the unchanged strict contexts `required-native`, `fixture-repro`, and `preview-package-smoke`.
- **Source:** `.planning/milestones/v0.1-MILESTONE-AUDIT.md`, phase `VERIFICATION.md` reports, and PR #34 branch-protection/check evidence.
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
- **Source:** `tests/player/CMakeLists.txt`, `tests/scripts/verify-phase3-player.sh`, `src/player/main.c`, and existing lesson GB-TEST-007.
- **Status:** Adopted and exact-revision hosted validation passed.

### GB-GSD-008 / 2026-10-09 / Audit runtime freshness, summary parseability, and state source

- **Cause and evidence:** Saved VERIFICATION.md frontmatter can continue to say `passed` after its covered-file digest changes. On the v0.1 audit, OpenGSD 1.16.0 accepted only Phases 2 and 4 and returned stale for Phases 1, 3, 5, and 6. The same audit found CPU-02/CPU-05 absent from all parseable `requirements-completed` summaries and `summary-extract` errors for `03-12-SUMMARY.md` and `04-02-SUMMARY.md`. `init.milestone-op` reported two completed phases although ROADMAP.md records six; `.planning/state.json` was modified owner scratch and intentionally preserved.
- **Remedy:** At milestone audit, query `verification.status` for every phase, run `summary-extract` for every summary, and compute requirement status from the live gate plus valid summary metadata plus traceability. Treat `state.json`/ROADMAP disagreement as a signal to reconcile, not permission to overwrite owner scratch. Repair summary metadata only with a corresponding verification refresh when covered-file digests change.
- **Applies when:** OpenGSD uses covered-file verification fingerprints and plan-summary metadata for milestone aggregation, especially in a checkout with preserved local planning edits.
- **Verification:** The v0.1 audit recorded the exact six phase gates, all 35 requirement IDs, both summary parser errors, 6/6 wired flows, and the conflicting init/ROADMAP phase counts. The follow-up route refreshed Phase 1; the remaining route is `$gsd-execute-phase 3`, then Phases 5 and 6 one at a time, then re-audit.
- **Source:** `.planning/milestones/v0.1-MILESTONE-AUDIT.md`, `.planning/milestones/v0.1-REQUIREMENTS.md`, phase VERIFICATION.md and SUMMARY.md files, and OpenGSD 1.16.0 query results.
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
- **Source:** Glueyneo: `.planning/workstreams/first-playable-game/phases/05-selected-mvs-boot/05-03-SUMMARY.md` and `.planning/preparation/2026-10-04-gsd-verification-loop.md`; GabbaBoy: `.planning/milestones/v0.1-phases/GB-03-visible-interactive-dmg/03-VERIFICATION.md`, `.planning/milestones/v0.1-phases/GB-03-visible-interactive-dmg/03-UAT.md`, `.planning/context/FUTURE-MILESTONES.md`, and `AGENTS.md`.
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

### GB-GSD-013 / 2026-10-10 / Give each milestone a versioned ROADMAP heading before close

- **Cause and evidence:** At v0.1 close, `milestone.complete v0.1 --dry-run` failed with `no phases found for milestone v0.1 in ROADMAP.md`. ROADMAP.md named the milestone only in a bullet under `## Milestones`, so OpenGSD 1.16.0's `sliceMilestoneWindow` found no `v0.1` heading and refused to archive. The same run showed that moving phase directories to `milestones/v0.1-phases/` breaks every relative link into `phases/GB-*` in `docs/`, `DECISIONS.md`, `LESSONS.md`, `research/INDEX.md` and `STATE.md`.
- **Remedy:** Add a `## v0.1 Limited DMG Preview` heading above `## Phases`, re-run `--dry-run`, then archive. After archiving, run `git grep "phases/GB-"` outside `milestones/`, repoint each hit to `milestones/vX.Y-phases/`, and check that every rewritten link resolves.
- **Applies when:** Closing any milestone with OpenGSD's `milestone.complete`; new roadmaps should carry a `## vX.Y <Name>` heading from the start.
- **Verification:** After the heading was added, the dry run reported 7 phases, 64 plans and 104 tasks, and the confirmed run archived the roadmap, requirements, audit, phases and quick tasks. A link-existence check over the five rewritten files found no broken targets.
- **Source:** `.planning/milestones/v0.1-ROADMAP.md`, OpenGSD 1.16.0 `bin/lib/roadmap-parser.cjs` (`getMilestonePhaseFilter`), `docs/mbc1-evidence.md`.
- **Status:** Adopted.

### GB-AUDIO-001 / 2026-10-10 / Check mixer full scale against the documented DAC and NR50 model before freezing PCM

- **Cause and evidence:** The core mixed `volume * 2048 - 16384` per channel (one unit = 16384 counts) times the NR50 `(volume + 1)` multiplier with no headroom divisor. Pan Docs defines each DAC as -1..1, a four-channel side as -4..4 and NR50 as a (volume+1)/8 scale, so s16 full scale must hold four units at volume 7. A scratch probe over `libbet.gb` (Start tap at f500, 1500 frames) measured a pre-saturation peak of 229376 counts, 73284 of 2410954 resampled samples (3.04%) clipped at s16 and output reaching -32768. The existing `audio_saturation` test only drove the post-mix kernel with INT32 extremes, so it could not see the scale error, and earlier audio digests had frozen it.
- **Remedy:** Divide each channel term by 16 (exact: terms are multiples of 2048) in `audio_current_mix`; after the fix the same run peaks at 14336 with 0 clipped samples and output -9277..10115. `audio_saturation` now runs two full-volume guest pulses at NR50 `$77` and requires a peak between 8192 and 32766. The guest partition digest moved from `b5bb127cdda6a035` to `c89a0db6f083c345`.
- **Applies when:** Any change to APU channel levels, NR50/NR51 scaling or the PCM digests; and before blessing PCM or game-acceptance audio evidence. Probe with a real ROM rather than only synthetic kernel inputs, and count clipped samples before the high-pass stage (after it, clipping can hide as only a couple of rail-valued samples).
- **Verification:** Full CTest suite (200 tests) passes after the change; the scratch probe reports 0 saturated mixer samples on Libbet. The probe is not committed.
- **Source:** [audio-and-playback](../../docs/audio-and-playback.md), D-027 in DECISIONS.md, Pan Docs Audio details (Mixer), mGBA `src/gb/audio.c` (read only).
- **Status:** Adopted.

### GB-GAME-002 / 2026-10-10 / Explain a game's input-timing oddity from its source before suspecting the joypad model

- **Cause and evidence:** An earlier exploratory run reported that repeated Start taps started Libbet by f270 while single taps at f290-f440 did nothing, which looked like a JOYP defect. The pinned source (`pinobatch/libbet` commit `46a765a2c01701bffb8c0b7dd6e4be3a6b193090`) explains it: `intro.z80` ignores input for the 64-frame roll and a further 120 unskippable frames, then accepts Start/A during a 180-frame skippable window; `pads.z80` `read_pad` derives `new_keys` from successive polls; the title needs its own Start. A scratch probe over `libbet.gb` logged every write of a non-zero `new_keys` and the LCD/state frames: taps f100-f230 ignored, tap f240 skips the intro (title f277), tap f280 starts the game (f287); isolated single taps at f290/f350/f440 reached or sat at the title (f327/f387/f447), and f470 started the game (f478). Each tap produced exactly one `new_keys=$08` edge in the press frame, so the core's JOYP reporting matched what the guest code implies.
- **Remedy:** No core change. Record the intro/title input windows in D-028 and keep D-13's Start at f500 (after the title is ready at about f447). Separate "the game ignored input" from "the emulator dropped input" by logging guest-side `new_keys` edges against frame numbers before touching the joypad path.
- **Applies when:** An acceptance or replay script gives different outcomes for similar taps at different frames, or an early input appears to be ignored; also whenever a game reads input only inside timed windows.
- **Verification:** Scratch probe (not committed) reproduced all three schedules deterministically; `cmake --build --preset phase1` plus the full CTest suite pass; `git diff --quiet src/core/gabbaboy.c`; the select-line anchor occurs once and matches main.
- **Source:** D-028 in DECISIONS.md; Libbet `src/intro.z80`, `src/pads.z80`, `src/instructions.z80` at the pinned commit (read only).
- **Status:** Adopted.

### GB-GAME-003 / 2026-10-11 / Compare structs with padding field by field, never with memcmp

- **Cause and evidence:** `acceptance_parse_script_errors` passed on Linux and macOS but failed on `native-windows-x64` at `tests/test_acceptance_lib.c:262` (`memcmp(a.events, b.events, ...)`, CI run 38096251361, head da2a028). `gbb_input_event` has padding after `kind` and `value`; the parser fills fields, not padding, so the padding bytes of two parses can differ (here on MSVC) even though every field is equal. The same test had passed at the previous head by chance.
- **Remedy:** Compare `at_half_dots`, `kind` and `value` individually (commit "fix(07-11): compare parsed script events field-wise"). This also follows the project rule against raw structure dumps for comparison and serialization.
- **Applies when:** Any test, digest or equality check reads a C structure's object bytes (`memcmp`, hashing, `fwrite`), especially structures with mixed-width members or enums.
- **Verification:** `ctest -R acceptance_parse_script` passes locally; exact head b6f982b run 38097373433 passed `native-windows-x64`, `native-linux-x64` and `native-macos-arm64`.
- **Source:** CI run 38096251361 log for job native-windows-x64; AGENTS.md engineering rules (explicit portable serialization).
- **Status:** Adopted.

### GB-GAME-004 / 2026-10-10 / The exact test inventory sees only the tests directory's own TESTS property

- **Cause and evidence:** `ExpectedTests.cmake` reads the `TESTS` property of the `tests` directory only. Tests registered through `add_subdirectory` live in another directory scope and would be absent from the inventory check, so a deleted or renamed test could pass unnoticed. Plan 07-02 therefore pulls `tests/acceptance/CMakeLists.txt` in with `include()`.
- **Remedy:** Use `include()` for CMake sub-lists that register CTests, and keep every registered name in `tests/expected-tests.txt`. Recorded as D-037.
- **Applies when:** Any new test list is split into its own CMake file, or an inventory check reads directory properties.
- **Verification:** `ctest --test-dir build -N` lists the acceptance tests (258 names at the baseline freeze) and the inventory check passes; the JUnit inventory check in CI (`baseline junit=ok inventory=core names=258`) finds every frozen name.
- **Source:** Plan 07-02 summary, `tests/CMakeLists.txt`, `cmake/ExpectedTests.cmake`.
- **Status:** Adopted.

### GB-GAME-005 / 2026-10-10 / Deadline steppers must treat idle and output-full stops as continuable

- **Cause and evidence:** `gbb_run_audio` returns `GBB_STOP_HALTED_IDLE` while a halted CPU waits for an eligible tick and `GBB_STOP_OUTPUT_FULL` (the same value family as a full trace buffer) when the caller's PCM buffer fills. Neither means the guest stopped. A stepper that treated them as terminal would end an acceptance run early with a misleading reason.
- **Remedy:** `src/accept/stepper.c` accepts both as continuable, drains the sunk frames and keeps stepping to the deadline. Recorded in D-045.
- **Applies when:** Any new driver loop around `gbb_run`, `gbb_run_audio` or `gbb_run_ex`, including the player adapter and benchmarks.
- **Verification:** `acceptance_lib_libbet_replay` and `acceptance_libbet` pass; the packaged player's PCM digest equals the headless digest.
- **Source:** `src/accept/stepper.c`, Plans 07-02 and 07-12.
- **Status:** Adopted.

### GB-GAME-006 / 2026-10-10 / Take frame-boundary time from the master timeline, not from completed frames

- **Cause and evidence:** A completed-frame count stops advancing while the LCD is off, so a script timed in frames would drift. Frame boundaries in the stepper are multiples of 140448 half-dots on the master timeline, and checkpoints use the first frame completed at or after the requested time (the Libbet `play_start` checkpoint completed at 71336360 for a request at 70645344 and is a legitimate mid-load frame).
- **Remedy:** Script times, `T_hit` and checkpoints are all in master-timeline half-dots; the baseline records both the requested and the completion half-dot.
- **Applies when:** Any replay, input script or frame-digest oracle for a game that turns the LCD off.
- **Verification:** The baseline lines `acceptance.libbet.checkpoint.<label>.requested_half_dots` and `.completion_half_dots` are byte-identical on Linux, macOS and Windows at the exact head.
- **Source:** 07-RESEARCH time-base decision, `src/accept/stepper.c`, Plan 07-15 summary.
- **Status:** Adopted.

### GB-GAME-007 / 2026-10-10 / A 160x144 P6 image alone exceeds a 64 KiB cap

- **Cause and evidence:** A P6 PPM of 160 by 144 pixels is 69,135 bytes, more than 65,536. The original D-18 wording capped the whole stall diagnosis, image included, at 64 KiB, which could never hold. The owner amended it so the cap applies to the text report and one image is written on top.
- **Remedy:** Size every bounded output from its fixed parts first, state which artefacts the cap covers, and test the real size (the stall report was 1984 bytes for the dropped-START case).
- **Applies when:** Any size budget over diagnostics that include a frame image.
- **Verification:** `acceptance_stall_diagnosis` asserts a maximum report size and byte-identical output across two runs; the PPM is 69,135 bytes.
- **Source:** 07-CONTEXT D-18 owner amendment, D-032, Plan 07-11.
- **Status:** Adopted.

### GB-GAME-008 / 2026-10-10 / A suite denominator needs a declared exclusion count

- **Cause and evidence:** A suite that silently drops cases because of model or revision applicability can shrink its denominator and still print pass. The runner's `--suite` mode now requires `--expect-excluded <n>`, reports `eligible`, `executed`, `excluded` and `xfail`, and fails on an undeclared count; exclusion has its own exit code (4) instead of a CTest skip.
- **Remedy:** Declare the exclusion count at registration time and compare it to the observed count. Recorded in D-041.
- **Applies when:** Any aggregate that counts cases across models or revisions, including the Phase 8 and later suites.
- **Verification:** `acceptance_suite_declared_exclusion`, `acceptance_suite_undeclared_exclusion` and `acceptance_suite_missing_expect_excluded`; `acceptance_suite` expects `eligible=3 executed=3 excluded=0 xfail=2`.
- **Source:** Plan 07-08 summary, `tests/acceptance/negative/suite-exclusion.txt`.
- **Status:** Adopted.

### GB-GAME-009 / 2026-10-10 / Say which evidence was not shown to fail, and which locked rules were relaxed

- **Cause and evidence:** Four phase-close claims need explicit limits. (1) The 07-03 `audio_saturation` assertion was written after the fix and was not shown to fail against the pre-fix core; the evidence for the defect is the scratch probe. (2) D-029 relaxed locked D-25's shade-count rule for the title and play_start checkpoints and is pending owner confirmation. (3) The Mooneye `daa` LD B,B frame is all shade 0, so its digest guards "still blank" only. (4) The Libbet reproduction script is byte-identical on macOS arm64 only; the Linux path and the dispatch-only workflow are unverified, and `frame-digest@t` has no CTest.
- **Remedy:** State these limits in `docs/game-acceptance.md` and the decision rows rather than in a summary alone, and treat a pending owner confirmation as open until recorded.
- **Applies when:** Closing a phase whose evidence includes regression-class digests, post-fix assertions or unexercised paths.
- **Verification:** `grep -c 'pending' docs/game-acceptance.md` and the D-029 row; Plan 07-16 summary.
- **Source:** Plans 07-03, 07-04, 07-07, 07-09, 07-15.
- **Status:** Adopted.

### GB-CART-001 / 2026-10-11 / Choose a single-line mutant anchor when the code is written

- **Cause and evidence:** A configure-time core mutant needs a text anchor that occurs exactly once. The MBC5 ninth-bit anchor `& 1u) << 8` exists only because Plan 08-03 put the bank composition in one helper on one line; Plan 08-08 then replaced it with `& 0u) << 8` and the configure step fails unless the count is exactly one.
- **Remedy:** Decide the anchor while writing the code under test, keep it on one line, and make the build fail when the occurrence count changes.
- **Applies when:** Any test-only mutant generated from production source text.
- **Verification:** `grep -c '& 1u) << 8' src/core/gabbaboy.c` is 1; `mbc5_ninth_bit_mutant_bank_1ff` fails the `$1FF` check and `mbc5_ninth_bit_mutant_control_below_100` passes.
- **Source:** Plans 08-03, 08-07, 08-08; D-061.
- **Status:** Adopted.

### GB-CART-002 / 2026-10-11 / Check an upstream test's loop bounds before planning a mutant on it

- **Cause and evidence:** The research premise was that Mooneye `mbc5_rom_64Mb` is the only proof of the ninth bank bit. Plan 08-07 measured that the shared harness loop selects banks 0..255 and stops at bc=`$0100`, every `$3000` write is `$FE`, so no bank at or above 256 is ever read: the ninth-bit mutant passed `rom_64Mb` while a `return 1u` control mutant failed it.
- **Remedy:** Before building a negative control on an upstream test, read its loop bounds or instrument it to record which inputs it actually reaches; keep a control mutant that proves the test is sensitive at all. The discriminator moved to the original `mbc5_bank_1ff` case (D-062).
- **Applies when:** Any plan that relies on a third-party test exercising a specific code path.
- **Verification:** The 08-07 measurement (257 bank selections) and the 08-08 mutant outcomes: bank_1ff fails, control passes.
- **Source:** Plans 08-07, 08-08; 08-CONTEXT D-29 amendment; D-062.
- **Status:** Adopted.

### GB-CART-003 / 2026-10-11 / Serialize plans that share an exact test inventory

- **Cause and evidence:** Plans 08-02 (MBC2) and 08-03 (MBC5) both edit `gabbaboy.c`, `gabbaboy.h`, `tests/CMakeLists.txt` and `tests/expected-tests.txt`. The inventory check requires the executed set to equal the file exactly, and additions are line-ordered, so parallel edits collide in a single file that cannot be merged mechanically.
- **Remedy:** Run such plans in sequence and append only `+` lines to the inventory; recorded in D-056.
- **Applies when:** Parallel plans touch the same exact-list file or the same source section.
- **Verification:** Each plan's full ctest equalled `tests/expected-tests.txt` (272, then 287, ... 319) with additions only.
- **Source:** Plans 08-02, 08-03; D-056.
- **Status:** Adopted.

### GB-CART-004 / 2026-10-11 / Select a suite by manifest digest so legacy receipts stay byte-identical

- **Cause and evidence:** Generalising the headless runner to a second suite risked changing the parent suite's output. Plan 08-05 selects the compiled case table by the SHA-256 of the raw manifest bytes through a `suite_def` table; an unknown digest prints `invalid-manifest` and exits 2, and the three parent cases print the same receipt as before.
- **Remedy:** Key suite selection on a pinned digest, fail closed on anything else, and add a category line only for the new suite.
- **Applies when:** One runner serves several digest-pinned fixture sets.
- **Verification:** `mooneye_mbc_unknown_manifest` (exit exactly 2) and the unchanged parent `mooneye_case_*` and `mooneye_required_suite` tests.
- **Source:** Plans 08-05, 08-06; D-028.
- **Status:** Adopted.

### GB-CART-005 / 2026-10-11 / A rebuilt-fixture digest from one host is indicative until a second host matches

- **Cause and evidence:** The 15 Mooneye derivative digests were first captured from a Darwin/arm64 rebuild, and the pinned linker's tied-section ordering is libc-dependent in its default mode. Plan 08-05 and 08-06 therefore stated no cross-host claim; the hosted ubuntu-22.04 leg (run 38151282870, `wla-gb` 10.7, `wlalink` 5.22) later printed 15 of 15 `match` lines against the same digests.
- **Remedy:** Record the host of each digest capture, add a hosted rebuild leg that compares against the pinned values, and only then remove the caveat from the source notes.
- **Applies when:** Any fixture reproduced from a toolchain whose output could depend on host libraries.
- **Verification:** The `mooneye-mbc-repro` job output and `fixtures/mooneye-mbc/SOURCES.md`.
- **Source:** Plans 08-05, 08-06, 08-07; D-024, D-025.
- **Status:** Adopted.

### GB-CART-006 / 2026-10-11 / Sticky flags, not 8-bit counters, for guest-side sweeps

- **Cause and evidence:** Plan 08-02's first echo test counted mismatches in an 8-bit WRAM byte. Exactly 8192 or 4096 mismatches wrap to zero, so a wrong echo mask passed; the mutation check exposed it.
- **Remedy:** Record failure as a sticky flag in guest code and run the mutation check on every new sweep.
- **Applies when:** Guest programs that compare a large range in 8-bit arithmetic.
- **Verification:** Changing the MBC2 read mask `0x1FF` to `0x0FF` fails `mbc2_ram_echo`.
- **Source:** Plan 08-02 summary.
- **Status:** Adopted.

### GB-CART-007 / 2026-10-11 / A new fixture ROM needs its own `.gitignore` exception or it is never committed

- **Cause and evidence:** `.gitignore` ignores `*.gb` and `*.gbc` so that no commercial image is committed by accident. Plans 09-05 and 09-06 built the MBC3+RTC and MBC2 continuation guests and committed their sources, manifests and reproduction scripts, but `git add` silently skipped the ROMs. The local suite stayed green because the files existed on disk. Plan 09-10 noticed that the ROMs were untracked and committed them with per-file exceptions in commit 5f9f866.
- **Remedy:** Whenever a plan adds a redistributable ROM, add a `!/fixtures/<dir>/<file>.gb` exception in the same commit. Then confirm that `git check-ignore` prints nothing for that file, and that `git ls-files` lists it before the plan is called complete.
- **Applies when:** Any plan that adds or regenerates a fixture ROM under `fixtures/`.
- **Verification:** `git check-ignore fixtures/*/*.gb` prints nothing, and `git ls-files fixtures | grep -c '\.gb$'` equals the number of `.gb` files on disk (27 of 27 at plan 09-15). A clean CI checkout passing the fixture tests confirms it remotely.
- **Source:** Plans 09-05, 09-06, 09-10.
- **Status:** Adopted.

### GB-CART-008 / 2026-10-12 / A source-anchored mutant makes an unrelated edit a configure failure

- **Cause and evidence:** The MBC5 ninth-bit mutant requires the text `& 1u) << 8` to occur exactly once in the core. Plan 09-09's first day-counter expression for the RTC matched it and failed configure.
- **Remedy:** Write the new expression differently (`(c->rtc_dh & 0x01u) * 256u`, commit 14caf9d) rather than loosen the anchor; the exactly-once check is the safeguard.
- **Applies when:** Adding code to a file that carries mutation-test anchors.
- **Verification:** Configure succeeds and the MBC5 mutant tests still fail the mutated build.
- **Source:** Plan 09-09; D-061.
- **Status:** Adopted.

### GB-CART-009 / 2026-10-12 / Order of `readdir` is not creation order in tests

- **Cause and evidence:** `player_session_v2_max_size` picked the preserved recovery file by directory-enumeration order and failed about half of the runs in Plan 09-16.
- **Remedy:** Select the file by an attribute the test controls (size of the damaged variant); 20 consecutive runs passed after the fix (commit 5477099).
- **Applies when:** A test must find one of several files created in a directory.
- **Verification:** Repeated runs of the test.
- **Source:** Plan 09-16.
- **Status:** Adopted.

### GB-CART-010 / 2026-10-12 / A hosted reproduction claim is made from the result line at the evidence head only

- **Cause and evidence:** Plan 09-17 wrote the MagenTests and rtc3test "release bytes equal the rebuild" claim as pending, because the earlier green job was at a different head. Plan 09-18 records it only from the `result=` line at the evidence head.
- **Remedy:** Keep the ledger entry pending until the exact-head job prints `result=byte-identical`; if it prints `result=differs`, do not change committed bytes and leave the claim unmade.
- **Applies when:** Third-party fixtures rebuilt in CI.
- **Verification:** The job log at the evidence head SHA; see `docs/mbc3-rtc-evidence.md`.
- **Source:** Plans 09-17, 09-18.
- **Status:** Adopted.

### GB-GSD-014 / 2026-10-12 / Turn every "human reading" UAT item into a contract check before verify-work

- **Cause and evidence:** Plan 09-14 marked the integration guide's RTC catch-up wording `human_judgment: true`, so `/gsd-verify-work 9` presented it to the owner as UAT test 14 after 13 automated passes. The judgment was structural: does the guide name only declared symbols and state every behavior the header promises. `cmake/VerifyDocContract.cmake` now decides it; mutants that drop "two calls add twice" or rename `gbb_rtc_catch_up` both fail.
- **Remedy:** When planning, give every deliverable an automated check and a negative control. For prose that restates an API, use `VerifyDocContract.cmake` (declared-name check plus required behavior phrases). At verify-work, run the cited checks at the exact head and record them as `source: automated`; if an item still looks human, write the check first, then rerun. Present a human checkpoint only for perceptual, hardware, credential or owner-decision items, and say why no check can decide it. Write SUMMARY `coverage:` entries with `id`, `description` and a `kind` from unit, integration, e2e, automated_ui or other; the classifier rejected the `deliverable:`/`ctest` shape used in 09-04, 09-11, 09-13 and 09-16, which turned automated items into manual mapping work.
- **Applies when:** Planning any phase, writing SUMMARY `coverage:` blocks, and running `/gsd-verify-work`.
- **Verification:** `native_guide_rtc_contract` and its six `doc_contract_*_selftest` controls (each fails on a weaker script); a verify-work session with zero human checkpoints unless one of the four exceptions applies. See DECISIONS D-069.
- **Source:** Phase 9 verify-work, owner directive.
- **Status:** Adopted.

### GB-GSD-015 / 2026-10-12 / A recorded lesson that agents do not read is not a control; enforce it with a test

- **Cause and evidence:** GB-GSD-014 already said to write SUMMARY `coverage:` entries in the classifier schema, but all 20 Phase 10 SUMMARYs used `deliverable:` keys, `kind: ctest` and flow-style `{...}` items. `uat.classify-coverage` rejected every entry, so `/gsd-verify-work 10` again mapped 118 cited tests to UAT rows by hand. Executors read AGENTS.md and the plan, not LESSONS.md. The classifier also keeps a trailing `# comment` as part of a value, so `status: pass  # latest run` is invalid even though the GSD template shows inline comments. In the same session `preview-package-smoke` timed out at two heads: its jobs waited 1500 s for `required-native`, but `linux-asan-ubsan` takes about 29 minutes, so each head needed a manual rerun. The verify:pre api-coverage gate also blocked once, because the COVERAGE.md opt-out reason was over 200 characters.
- **Remedy:** `tests/scripts/verify-summary-coverage.py` copies the classifier rules and adds the D-069 rule (`human_judgment: false` needs at least one verification, all `pass`). CTests: `summary_coverage` checks every SUMMARY from Phase 11 on, `summary_coverage_selftest` rejects 12 mutants, and `summary_coverage_phase10_rejected` is the negative control on the real Phase 10 files. Executors run the full suite before finishing a plan, so a bad block fails there, not at verify-work. AGENTS.md states the schema in one line. The preview wait is now 2700 s with a 55-minute job timeout. Keep COVERAGE.md opt-out reasons under 200 characters.
- **Applies when:** A recurring mistake survives a written lesson: add a check that fails, not more prose. Also applies to writing SUMMARY coverage blocks and to CI jobs that wait on slower jobs.
- **Verification:** The good self-test sample auto-passes D1 in `uat.classify-coverage`, and every mutant the script rejects is also not auto-passed there (checked locally against @opengsd/gsd-core 1.16.0). The Phase 10 negative control fails with `flow-style-not-supported`.
- **Source:** Phase 10 verify-work, owner directive.
- **Status:** Adopted.

### GB-CGB-001 / 2026-10-12 / The runner labelled every run `model=dmg-cpu-b`; one model-to-profile mapping removes the duplicate literals

- **Cause and evidence:** Before Phase 10 the model string literal `dmg-cpu-b` appeared 17 times in `src/runner/acceptance.c` and the profile constant `GBB_PROFILE_DMG_CPU_B` three times in `src/runner/main.c`, so a CGB run would still have printed `model=dmg-cpu-b` and been filed as DMG evidence. After the change the literal occurs 5 times in `acceptance.c`, the constant once, and an unsupported profile is rejected by the acceptance runner instead of silently downgraded.
- **Remedy:** One model-to-profile mapping consulted by the runner entry point, the manifest loader and the acceptance runner; CTests assert both the accepted DMG identity and the rejection of unknown, conflicting and CGB-excluded inputs, each with a `FAIL_REGULAR_EXPRESSION` negative control.
- **Applies when:** Any adapter or runner that labels evidence by hardware model or profile.
- **Verification:** `cgb_runner_profile_unknown`, `cgb_runner_profile_model_conflict`, `cgb_runner_profile_manifest_cgb_excluded`, `cgb_runner_profile_acceptance_cgb_excluded` and the three `cgb_runner_profile_dmg_identity_*` tests in `tests/expected-tests.txt`.
- **Source:** Phase 10, plans 10-03 and 10-05 (D-28).
- **Status:** Adopted.

### GB-CGB-002 / 2026-10-13 / A deliberately failing C negative control leaks under LeakSanitizer and the expected exit code is lost

- **Cause and evidence:** Phase 11 mutant tests exit 1 through an early `REQUIRE` return that never destroys the instance. Under `phase1-asan` LeakSanitizer reports the leak and replaces exit 1 with its own code, so the expect-exit control failed at three successive CI heads (two or three mutants each). macOS cannot run `phase1-asan`, so local runs passed.
- **Remedy:** Set `ASAN_OPTIONS=detect_leaks=0` on the failing mutant run only (commit 361256d); the paired control keeps leak checking. Simulate or run the sanitizer leg early when adding any expect-exit harness.
- **Applies when:** Any C test that must exit with a specific non-zero code and is built under LSan.
- **Verification:** Mutant CTests such as `cgb_priority_mutant_opri_live` and `magentests_cgb_mutant_lcdc0_inverted` pass on `phase1-asan` in CI, and their controls still run with leak detection.
- **Source:** Phase 11 CI at three heads.
- **Status:** Adopted.

### GB-CGB-003 / 2026-10-13 / A guest that HALTs in its main loop never completes a frame

- **Cause and evidence:** `gbb_run` returns at every HALT, so a fixture guest that halts between frames stalls frame-based assertions (plans 11-07 and 11-08).
- **Remedy:** Original CGB fixture guests end in a `jr` spin loop instead of HALT.
- **Applies when:** Writing guest fixtures whose checks depend on frame completion or `gbb_copy_frame_rgb555`.
- **Verification:** `cgb_colour_attr`, `cgb_colour_hblank_rows` and `cgb_colour_fixture_digest` complete frames and pass.
- **Source:** Phase 11 plans 11-07 and 11-08.
- **Status:** Adopted.

### GB-CGB-004 / 2026-10-13 / The host package-manager assembler differed from the pinned toolchain; the pinned archive rebuilt byte-identically

- **Cause and evidence:** Homebrew RGBDS was 1.0.4 while the fixture pin is 1.0.1. Fetching the pinned release archive and checking its SHA-256 gave byte-identical rebuilds.
- **Remedy:** The reproduce script refuses any version other than the pin and builds from the digest-checked archive.
- **Applies when:** Fixture reproduction scripts and CI jobs that depend on an external assembler.
- **Verification:** `fixture-repro` reports `byte-identical` for the colour fixtures; the script exits non-zero on a wrong version.
- **Source:** Phase 11 plan 11-07.
- **Status:** Adopted.

### GB-CGB-005 / 2026-10-13 / A negative control must assert the specific failure reason, not only failure

- **Cause and evidence:** In plan 11-13 a CMake list split on `;` silently corrupted a mutated claims control, so it failed for the wrong reason and still read as a pass.
- **Remedy:** Pair each mutant with a `FAIL_REGULAR_EXPRESSION` (or exit-code check) naming the intended failure, and avoid passing `;`-joined text through CMake lists.
- **Applies when:** Any CTest negative control, especially ones driven through CMake script arguments.
- **Verification:** `player_claims_agree_mutated` matches its specific reason string.
- **Source:** Phase 11 plan 11-13.
- **Status:** Adopted.

### GB-CGB-006 / 2026-10-13 / Per-line resolve timing, overlap and table-first mirrors need their own fixtures and controls

- **Cause and evidence:** Resolving colour per dot is only proved by a fixture that changes the colour on every line (`cgb_colour_hblank_rows`) with a seam mutant that resolves at frame completion; an X-order control cannot be proved on a ROM whose objects never overlap; mirroring docs from the code table (table-first) kept the DEFERRED cell flips consistent; manifest-driven rebuild scripts let fixture plans split without editing the script.
- **Remedy:** Add a per-line fixture and a seam mutant for any copy-time versus resolve-time claim, give every ordering control an overlapping-object case, generate or diff doc tables against code tables, and drive fixture rebuilds from the manifest.
- **Applies when:** Renderer features with timing-dependent state and fixture suites spanning several plans.
- **Verification:** `cgb_colour_mutant_frame_resolve` with its control, `cgb_priority_mutant_compat_bg_set_for_objects`, `cgb_tables_compat_palette_mutated_doc`.
- **Source:** Phase 11 plans 11-05 to 11-12.
- **Status:** Adopted.

### GB-CGB-007 / 2026-10-13 / A bash-only test must be excluded in two places, or the Windows inventory fails

- **Cause and evidence:** `cmake/ExpectedTests.cmake` leaves bash-only tests unregistered on Windows, but `.github/scripts/verify-test-inventory.sh` keeps its own Windows exclusion list. Phase 10 (`cgb_mooneye_repro_requires_manifest`) and Phase 11 (`cgb_colour_repro_tool_failure`, `cgb_colour_repro_missing_pin`, added by a review fix) each failed native-windows-x64 at the exact PR head with an inventory diff. Every other leg was green, and the package smokes failed only because they wait on that CI run.
- **Remedy:** When a test is registered only on non-Windows hosts, add it to both lists in the same commit. Grep `verify-test-inventory.sh` whenever `ExpectedTests.cmake` gains a Windows-only exclusion.
- **Applies when:** Adding any bash-only or POSIX-only CTest, especially late in a phase (review fixes) after the last hosted run.
- **Verification:** native-windows-x64 green at fb7d14c (ci run 38355327717).
- **Source:** Phase 11 execute-phase tail, PR #67.
- **Status:** Adopted.

### GB-CI-004 / 2026-10-13 / Hosted ASan outgrew its job timeout and its per-test limits

- **Cause and evidence:** `linux-asan-ubsan` ran `ctest --preset phase1-asan` serially under a 30-minute job timeout. At b314686 the push-event run took 1194 s of test time (ci run 38360819833); the pull_request run of the same commit hit a runner about 1.6x slower and was cancelled at 30 minutes with 504 of 684 tests passed and none failing (ci run 38360825378). Running four tests in parallel (eb6f36e) cut test time to 826-915 s, but `acceptance_stall_diagnosis` and `acceptance_core_mutant` then exceeded their 300 s TIMEOUT (ci runs 38396258662, 38396266543). Serially the slowest already took 275 of 300 s on the slow runner, so the per-test limits were sized for normal builds, not Debug ASan.
- **Remedy:** Run the ASan step with `--parallel 4` (pinned by `ci_asan_parallel_contract`, negative control `ci_asan_parallel_serial_selftest`) and, in sanitizer builds only, multiply every explicit test TIMEOUT by three at the end of `tests/CMakeLists.txt`. Normal builds keep their limits.
- **Applies when:** A hosted job's duration grows with the test inventory, or a test's limit is set from a normal-build timing. Check job and per-test headroom at each phase tail rather than re-running a timeout.
- **Verification:** Hosted ASan result is recorded in the Phase 11 UAT.
- **Source:** Phase 11 verify-work, PR #67.
- **Status:** Adopted.

### GB-CGB-008 / 2026-10-13 / A borrowed speed constant failed the ROM that was meant to bind it

- **Cause and evidence:** The imported `0x20008` T-cycle stall literal failed AGE `spsw-div-cgbBCE` in all five starts, while the committed-core pass window is `[0x20004, 0x20007]`; the low bits are not discriminated by that fixture. `age_stall_window` records the window and selected aligned constant.
- **Remedy:** Derive a model-scoped, M-aligned constant from the measured window, retain the low-bit uncertainty, and keep the result distinct from physical-hardware evidence.
- **Applies when:** A fixed timing value is borrowed from an emulator or document and a fixture is expected to qualify the implementation.
- **Verification:** `age_stall_window`, `age_sensitivity_m6`, `cgb_speed_stall_length`.
- **Source:** Phase 12 plans 12-08, 12-09 and 12-17 (D-37).
- **Status:** Adopted.

### GB-CGB-009 / 2026-10-13 / Runtime-mask variants keep mutation builds inside the test budget

- **Cause and evidence:** Phase 12 has several independent timing mutations; compiling a core per mutation would consume the build ceiling before the full suite. The runtime-mask and shared-mutant targets keep the phase at five distinct core variants, under D-25's six-build cap.
- **Remedy:** Group non-interacting mutations behind named runtime masks and share their compiled core where the source change permits it; record the configured variant count and measured configure/build cost.
- **Applies when:** A regression matrix explores multiple independent core mutations under a CI wall-time budget.
- **Verification:** `cgb_speed_mutant_m27_divider_reset_omitted`, `cgb_speed_mutant_m22_switch_headroom_omitted`, `cgb_partition_mutant_m16`, `player_cgb_speed_smoke_mutant_ppu_follows_cpu`.
- **Source:** Phase 12 plans 12-03, 12-09, 12-14 and 12-17 (D-25/D-26).
- **Status:** Adopted.

### GB-CGB-010 / 2026-10-13 / Keep a pre-change identity pin separate from the plan execution base

- **Cause and evidence:** The eight single-speed output pins use the pre-phase source revision `fb45111`, while plan 12-01 execution began at `aac4772` after research and handoff commits. The relevant core and public-header files are identical across those two revisions; the different hashes name different provenance, not a changed pin.
- **Remedy:** Record the pin's source revision and the plan's `plan_head_before` independently, check their relevant source diff, and never re-record identity values to absorb later implementation changes.
- **Applies when:** A regression identity is captured at a pre-change baseline that differs from the planning or executor start head.
- **Verification:** `cgb_speed_identity_pin`, `cgb_speed_identity_pin_flipped`, and `git diff fb45111..aac4772 -- src/core/gabbaboy.c include/gabbaboy/gabbaboy.h`.
- **Source:** Phase 12 plan 12-01 and its recorded execution ledger.
- **Status:** Adopted.

### GB-CI-005 / 2026-10-14 / Scale sanitizer timeouts after registration in each CMake test directory

- **Cause and evidence:** The old scaler ran before late Phase 12 registrations. Moving it to the parent directory's end fixed those tests but still missed `tests/player`: CMake 3.25 test properties are directory-scoped. Independent review reproduced a child TIMEOUT of 120 under sanitizer mode.
- **Remedy:** Call one shared scaler after the final registration in each test directory; remove individual sanitizer multipliers. Assert representative late and player values during configure.
- **Applies when:** CMake tests are appended or registered in optional subdirectories, especially at the CMake 3.25 floor.
- **Verification:** `sanitizer_timeout_policy_selftest` proves unchanged normal limits and once-only parent/child scaling, and rejects early, double and parent-only passes. The actual player directory's missing-call mutant fails its property assertion. Full post-fix CTest passed 898/898; the configure-only player probe used stub link targets and is not runtime sanitizer evidence.
- **Source:** Phase 12 CR/WR review fixes `fe61e2f`, `40e7f08`; `12-REVIEW-FOLLOWUP.md`.
- **Status:** Adopted.

### GB-CI-006 / 2026-10-14 / Keep environment paths out of shell source, including unsafe regression copies

- **Cause and evidence:** An interpolated EXIT trap converted a TMPDIR-derived cleanup path into shell source. A deliberately unsafe regression copy initially inherited its caller's TMPDIR too, so its confinement needed the same scrutiny as the production fix.
- **Remedy:** Use a literal trap body with quoted variable expansion. Construct unsafe negative-control paths only under a fixture-owned scratch prefix; never let caller environment text contribute shell source to the mutant.
- **Applies when:** Shell cleanup paths or deliberately vulnerable test copies contain environment-supplied values.
- **Verification:** Inventory self-test cleanup and original-trap marker controls pass; a nested hostile caller TMPDIR creates no parent marker, while the old inherited-prefix helper control does.
- **Source:** Phase 12 CR-01 fixes `be53c43`, `d979ba5` and `.github/scripts/test-inventory-cleanup.sh`.
- **Status:** Adopted.

### GB-GSD-016 / 2026-10-14 / Close automated UAT once and reuse its bounded evidence

- **Cause and evidence:** Phase 12 already had 73 auto-passable deliverables and 898 registered regressions. Replacing the workflow's confirmation-only summary with another owner checkpoint would repeat the Phase 9 toil despite D-069. The bounded commit audit also found plan 12-04's full `plan_head_after` mistyped; `git rev-parse ec5dc8a` identifies the real two-task window.
- **Remedy:** Derive UAT directly from the classifier, preserve every SUMMARY/coverage-id/evidence mapping, and run the actual behavioral, integration, seam, e2e and smoke checks with their negative controls. Record completed UAT plus canonical freshness and exact-head CI receipts. An unchanged completed session is a no-op; do not replan, rerun every review, or ask a confirmation-only question without changed evidence. Correct metadata from measured Git objects, then let the verification owner refresh its covered digest. Keep session-specific closure checks local when existing CI already covers recurring behavior; add CI only for recurring value.
- **Applies when:** Every verify-work handoff, future phase planning and SUMMARY authoring. Only true perceptual, physical-hardware, credential and owner-decision limits may require the smallest necessary owner action. A qualified unsupported behavior outside the adopted scope is a recorded limit, not invented manual UAT.
- **Verification:** `12-UAT.md` records 73 automated passes, zero human checkpoints and no gaps. `verify-uat-contract.py --self-test` rejects nine missing/weaker/misrouted closure mutations; `summary_coverage` and its twelve schema mutants remain recurring CI gates. All 19 bounded commit windows reconcile after the SHA correction.
- **Phase 13 reuse (2026-10-15):** 45/45 deliverables close automatically; `13-UAT.md` retains the exact mapping and `verify-uat-contract.py --self-test` rejects 17 weaker records, including unparsed human checkpoints. Canonical completed-stage parsing rejects contradictory or stale handoffs. Preserve the next command `/gsd-discuss-phase 14`, and reopen only changed covered behavior or evidence. Existing recurring CI stays in place; local GSD closure adds no duplicate hosted lane.
- **Phase 19 reuse (2026-10-31):** 39/39 deliverables close automatically after 184 focused tests, installed-host smoke, immutable requirement positive/original-base negative and live release identity reconciliation; the shared closure rejects 21 weakened records. Preserve the historical halted 19-06 SUMMARY and use its later 19-07/08/final-audit outcomes. Original task counts reconcile through recorded squash merges. CI/CD efficiency is now an explicit active/finished-run and release-handoff procedure in WORKFLOW.md, reached from AGENTS.md and INDEX.md; the UAT records measured timing and a bounded duplicate-self-test candidate. Reopen only changed covered evidence or concrete failures, and stop before `/gsd-audit-milestone`.
- **Source:** Phase 12 verify-work and renewed owner automation directive; DECISIONS D-069, GB-GSD-014 and GB-GSD-015.
- **Status:** Adopted. Reopen only for a concrete new regression, changed covered behavior, stale/unavailable evidence, or an owner scope change.

### GB-CGB-011 / 2026-10-14 / Inspect the actual run boundary before adding a device steal

- **Cause and evidence:** Phase 13 discussion found that `execute` calls `advance_devices_to` inside timed bus reads/writes, while `gbb_run` preflights and reports only nominal whole-instruction cost. The public header promises whole instructions and full-cost preflight; no persisted micro-op cursor exists. A proposed “set a stall flag at HBlank” or “copy the block immediately” therefore cannot be assumed correct from the existing speed-pause branch. The milestone research also describes live counters, while the actual FF51–54 contract is CPU write-only.
- **Remedy:** Lock the observable budget/time, bus/IRQ order and partition contracts first. Require a focused mechanism prototype with a HBlank between later bus accesses, output-capacity/headroom cases and a discriminator for omitted/delayed stealing. Separate internal cursors from CPU register observations and preserve independently ending stall causes. Keep an unproven exact boundary model-tagged UNKNOWN rather than presenting an implementation's scheduling choice as hardware fact.
- **Applies when:** A new DMA/device event can interrupt synchronous execution or share a scheduler stall reason; current code/API contracts take precedence over architecture sketches.
- **Verification:** Source inspection plus the reproducible Phase 13 `13-D09-boundary-prototype.c`: real synchronous `LD (a16),SP` accesses at +24/+32 bracket a visible HBlank at +26, and CB memory accesses at +16/+24 bracket one at +18; matched no-edge controls retain accesses without the transition. Both runs conserve nominal whole-instruction time. This uses synthetic private PPU setup and does not execute DMA; candidate scheduling arithmetic is not runtime or silicon evidence. `13-01-PLAN.md` gates expansion on actual transfer, output/order/budget and partition checks; CONTEXT D-03/D-09 and DECISIONS D-097 retain that gate.
- **Source:** Phase 13 code-seam investigation and adversarial reconciliation, `13-DISCUSSION-LOG.md`.
- **Status:** Adopted prevention rule; implementation evidence pending.

### GB-GSD-017 / 2026-10-14 / Require every named test, not merely a nonempty filter

- **Cause and evidence:** A Phase 13 draft combined new CTest names and existing regression names in one regex and claimed `--no-tests=error` would detect missing new cases. A temporary one-test CTest inventory proved that `-R '^(existing|missing)$' --no-tests=error` exits zero when only `existing` exists.
- **Remedy:** Before running a focused group, inspect `ctest --show-only=json-v1` and require every intended test name. Preserve the complete expected-inventory contract as well. A nonempty group and a complete required set answer different questions.
- **Applies when:** New tests share a filter with existing tests, or conditional configure/install options control registration.
- **Verification:** The temporary CTest case passes the existing-name positive guard; the explicit set-membership guard detects `missing` despite the regex run succeeding. Phase 13 task commands now include required-name guards; installed-consumer tasks explicitly configure their installation prefix.
- **Source:** Phase 13 plan review and independent command/inventory checks.
- **Status:** Adopted automation default. No new hosted lane or dependency is needed.

### GB-GSD-018 / 2026-10-14 / Close mechanical GSD flags through their actual producer

- **Cause and evidence:** OpenGSD 1.16.0's spec-less fallback projects an unwired prohibition as unresolved. Its `dispositionForProhibition` returns `status: unverified, flagged: true`; the verifier cannot pass that flag merely because a separate claim-checker self-test exists. Phase 13 review caught this for the mechanically checkable ban on presenting differential agreement as physical CGB-E qualification.
- **Remedy:** Preserve the initial fail-closed projection. Once the real check and clean/violating subjects exist, wire the test-tier descriptor through the owning serializer and run the actual prohibition-enforcement producer. Require its independently observed fail-first proof and nonvacuous clean pass, then verify an unflagged green disposition. Keep physical UNKNOWNs as evidence limits. Run GSD-specific enforcement automatically in the GSD workflow; keep recurring Python claim checks in native CI without requiring a GSD installation there. Do not silently dismiss the flag, fabricate hardware proof or assign the owner a mechanical review.
- **Applies when:** A GSD-generated flag can be mechanically checked and the project requires zero routine human UAT; a generic workflow template is not a reason to leave that route unfinished.
- **Verification:** Direct runtime call reproduced the unresolved entry's flagged-unverified result. Phase 13 execution subsequently passed the actual producer fail-first, clean-subject and live-checkout proof, with nine producer controls; the resolved/test descriptor was serialized and re-projected through the installed runtime. See 13-12-SUMMARY and 13-BENCH for the exact receipts.
- **Source:** Installed prohibition producer/probe/verifier contracts and independent Phase 13 plan review.
- **Status:** Adopted and exercised in Phase 13; the separate generic fallback edge and physical UNKNOWNs remain distinct from the cleared machine-checkable claim safeguard.

### GB-CGB-012 / 2026-10-14 / Prime mapped HDMA addresses in register-visibility guests

- **Cause and evidence:** Wave 2's full suite exposed three older visibility guests that wrote FF55 before programming FF51–FF54. The zero-initialized destination cursor is not a legal VRAM address, so whole-block prevalidation correctly stopped admission; the stop seam reports the current source cursor `$0000`, which obscured that the invalid field was the destination. The affected guests were the LCD-off FF55 readback, the CGB FF55 matrix, and an interrupt-entry stack push into FF55 after the retained `$FF56` deferred write.
- **Remedy:** Any guest that expects an FF55 request to be accepted must set a mapped source and VRAM destination first. Keep the LCD-off initial-kick status explicit, and retain separate controls proving that a genuine `$FF56` neighbor still stops and CGB/compatibility FF55 outcomes remain distinguishable.
- **Applies when:** A test reaches a newly implemented DMA or device-control path through ordinary IO or stack side effects; register visibility alone no longer isolates the instruction from the triggered device behavior.
- **Verification:** Exact CTest inventory found all 13 `cgb_visibility_*` and 18 `cgb_hdma_*` names, including named controls. The combined visibility, HDMA, CGB-speed and model-gate set passed 199/199; `cgb_visibility_cross_column_control`, `cgb_visibility_deferred_latch_interrupt`, and the HDMA address/overflow controls passed.
- **Source:** Phase 13 Wave 2 integration follow-up; `.planning/phases/GB-13-cgb-hdma/13-02-SUMMARY.md`.
- **Status:** Adopted for guest fixtures that exercise accepted FF55 writes.

### GB-GSD-019 / 2026-10-15 / Bind execution evidence to every input and the exact PR revision

- **Cause and evidence:** Phase 13 security review reproduced acceptance of a core-only change after a measured source revision. A second review reproduced an optional CI receipt accepting omitted contexts, duplicate failure/success rows and wrong-event data. Narrow path comparisons and caller-declared required-job sets both made stale evidence appear current.
- **Remedy:** Compare committed, index, working-tree and non-ignored untracked paths independently with NUL delimiters; allow only named closeout metadata. Require the exact repository context set and PR event, head, workflow and run provenance, reject duplicates, and bound receipt reads. Keep local receipts diagnostic; query actual GitHub jobs at the final published head before merge. Preserve historical measurements under their original revision when retesting.
- **Applicability:** Test, benchmark, package or workflow evidence reused across later commits, especially after metadata closeout.
- **Verification:** Test-only RED `03292b1` preceded source-gate fix `5459b7c`; 26 controls pass. Receipt RED `42e330f` preceded `ec54205`; positive plus 16 negative controls pass. Independent re-audits closed both findings. Handoff RED `1d45145` precedes `3cdcef2`; the completed execution stage preserves the exact verification route and rejects a wrong stage.

### GB-CGB-013 / 2026-10-16 / Sweep every source and receipt consumer when a model contract changes

- **Cause and evidence:** Phase 14 changed AGE row classifications, stable assertion identities, and the wording of GATE-49's current-receipt evidence. The corpus inventory contract and AGE research14 contract both consume those facts; changing only one validator left a stale cross-check. AGE identity checks also bind each source row to an exact observation ID, so prose-equivalent renaming could disconnect an assertion chain.
- **Remedy:** For each model-visible change, trace consumers across runner/report adapters, gate tables, manifest/disposition validators, stable assertion-ID checks, documentation checks, CMake registrations, expected-test inventory, and CI. Keep source expectations and guest observations distinct at every layer.
- **Applies when:** A source pin, manifest classification, model/mode cell, gate disposition, row ID, or receipt schema changes.
- **Verification:** `verify-cgb-corpus-inventory.py --bindings` and `--self-test`; `verify-age-phase14-contract.py --research14` and `--research14-controls`; CTest `cgb_age_assertion_identity`, `cgb_research14_dispositions`, and `cgb_phase14_inherited_contract_unit`. Static bindings cover 181 sources, 109 outputs, and 107 cases; stable AGE assertion identities remain checked.
- **Player-copy supplement (2026-10-16):** UI scope review found that the core-only build omitted the player exact-string consumer after the limitation copy changed. Refresh the intended string and run `player_limitations`, `player_claims_agree`, and `player_claims_agree_mutated` in a player-enabled build; all 3 passed. Include optional adapters in the consumer sweep even when no UI layout changes.
- **Source:** Phase 14 plans 14-10 through 14-13; `14-10-SUMMARY.md`, `14-12-SUMMARY.md`, and `14-13-SUMMARY.md`.
- **Status:** Adopted.

### GB-CGB-014 / 2026-10-16 / Separate static inventory from live receipt completeness

- **Cause and evidence:** Static inventory cannot truthfully assign a terminal result to every admitted case; `--complete` correctly rejects the unexecuted `magentests:bg_oam_priority` row. Full CTest `--begin-run` also invalidates the prior receipt before testing starts, so requiring a complete current receipt from an ordinary CTest contract creates a cycle.
- **Remedy:** Use `--bindings` for static source, rights, output, and test identity. Keep static CTest checks limited to independently checkable contract semantics. After the single full CTest stream, derive the fresh receipt with `--from-ctest`, then validate terminal cases, actual counts, pass cohorts, and current build identity against that receipt.
- **Applies when:** Fixture admission is stable but terminal observations are produced only by a bounded test run.
- **Verification:** `verify-cgb-corpus-inventory.py --bindings` passes while its self-test preserves strict `--complete` rejection for the nonterminal Magen case; `verify-cgb-corpus-claims.py --receipt <fresh-receipt>` validates dynamic claims after receipt construction without rerunning guest tests.
- **Source:** `14-12-SUMMARY.md` static-completeness correction and `14-13-SUMMARY.md` post-receipt claim check.
- **Status:** Adopted.

### GB-CI-007 / 2026-10-16 / Parse actual CTest output measurements and keep one nonce across consumers

- **Cause and evidence:** CTest's real `Test.xml` includes path-only `TestList` records, stores captured output in an unnamed `<Measurement>`, and defaults passing output to 1 KiB. Parser runs passed CTests but could not derive complete evidence; the default cap also truncated APU output. A separate fixed JUnit path would let the receipt, required inventory, and DMG baseline consume different runs.
- **Remedy:** Parse status-bearing results and the single unnamed output measurement, reject missing or duplicate measurements, and set a finite 16 MiB per-test output cap. Use the same nonce-specific JUnit for the receipt, required-test inventory, and DMG baseline. Measure actual aggregate output before changing the bound.
- **Applies when:** CTest reports are converted into compatibility receipts or several evidence consumers share one test execution.
- **Verification:** `test-cgb-corpus-report.py` covers TestList records, unnamed output, and missing/duplicate measurements. The 14-12 run measured 617,531 bytes for 70 APU records and 4,784 assertion rows under the 16 MiB cap. `cgb_corpus_report_contract` and the native CI contract require receipt construction before the post-receipt claim check and keep downstream JUnit paths nonce-bound.
- **Source:** `14-12-SUMMARY.md` parser fixes and measured run; `14-13-SUMMARY.md` recurring consumer contract.
- **Status:** Adopted.

### GB-GSD-020 / 2026-10-16 / Reconfigure after the source revision changes

- **Cause and evidence:** CMake embeds the Git revision during configure. A build after a commit can retain the previous revision in the runner while a new receipt observes the new HEAD, making an otherwise correct runner fail an exact-head check. Phase 14 also relies on a build-input stamp whose clean and incremental dependency order must remain intact.
- **Remedy:** After source commits, run the configure and build presets before the exact-head CTest stream. Preserve the stamp's executable dependencies and verify clean and covered-input rebuild ordering if that contract changes; do not accept a stale runner as current evidence.
- **Applies when:** Executable or test identity contains a configure-time source revision, or a build stamp consumes generated inputs.
- **Verification:** `cmake --preset phase1 && cmake --build --preset phase1`; `cgb_corpus_report_tracer` and its stale-runner control; the 14-12 clean/incremental stamp checks and 14-13 exact-head receipt.
- **Source:** `14-12-SUMMARY.md` stale-runner correction and build-stamp evidence; `14-13-SUMMARY.md` exact-head run.
- **Status:** Adopted.

### GB-GSD-021 / 2026-10-16 / Keep public evidence allowlisted and RED tracebacks repository-relative

- **Cause and evidence:** Raw CTest XML and JUnit contain host paths. Five valid historical RED JSON records also captured absolute workspace paths in traceback output. The records had no output-hash field, so one could not claim a hash-verified redaction without changing their evidence contract.
- **Remedy:** Publish only the established allowlist of privacy-checked JSON artifacts; keep raw reports local. Replace only the known workspace prefix in current RED tracebacks, preserve target/assertion/expected/actual/exit code and semantic failure text, and do not invent absent hashes. Verify path privacy with a generic negative control.
- **Applies when:** CI artifacts, failure logs, or persisted TDD evidence might disclose host-specific paths.
- **Verification:** The artifact scanner accepts the three public JSON files and rejects host paths in synthetic XML/JUnit. `test-cgb-red-evidence-privacy.py` checks the five preserved records and detects a synthetic absolute path; OpenGSD classifies all five historical records and the new real Task 3 record as `RED_EVIDENCE_OK`.
- **Source:** `14-12-SUMMARY.md` artifact allowlist; `14-13-task3-red-evidence.json`; `14-13-SUMMARY.md` privacy verification.
- **Status:** Adopted.

### GB-GSD-022 / 2026-10-16 / Do not reconstruct a missing historical RED gate

- **Cause and evidence:** Plan 14-12 Task 3 lacked a pre-implementation RED commit while its package-boundary implementation was already present. A test run after implementation cannot prove the earlier test-first sequence.
- **Remedy:** Preserve the 14-12 deviation in its original summary. Do not fabricate or backdate a failure; for a new TDD task, capture and classify a real failing test before the current data or behavior fix, then keep the original failure record unchanged.
- **Applies when:** A continued phase discovers that a previous task skipped its RED gate or a historical fixture/result is missing.
- **Verification:** The current Task 3 privacy assertion failed against the five actual leaking records and was classified `RED_EVIDENCE_OK` before the sanitization commit; the records then pass the privacy test. The 14-12 summary still explicitly reports its missing RED.
- **Source:** `14-12-SUMMARY.md` Task 3 deviation; `14-13-task3-red-evidence.json`; `14-13-SUMMARY.md` TDD gate record.
- **Status:** Adopted.

### GB-CI-008 / 2026-10-16 / Exercise native artifact names and subprocess pipes before declaring tooling portable

- **Cause and evidence:** Phase 14 independent review found that the default build-stamp target assumed extensionless binaries and registered anonymous pipes with selectors. Both assumptions fail on Windows, even though the native C code and local macOS corpus passed.
- **Remedy:** Use the native executable suffix at every artifact and launch path. Use a bounded Windows pipe reader with a capped queue, deadline and process/reader cleanup; retain POSIX process-group cleanup. Keep the existing Windows CI job as actual platform evidence, with local simulations catching these defects earlier.
- **Applies when:** A Python build or evidence adapter hashes or launches native binaries or captures subprocess output across platforms.
- **Verification:** The report adapter's 8 focused positive/negative controls and all 13 report-contract tests passed; the independent fix recheck found no remaining material issues. Actual Windows execution must be established by the exact-head hosted job, not inferred from the simulations.
- **Source:** `14-REVIEW.md`, `14-REVIEW-FIX.md`, `14-REVIEW-RECHECK.md`; fixes `e1deb42` and `bfd6f09`.
- **Status:** Adopted.

### GB-CI-009 / 2026-10-16 / Test configured paths, byte identity and nested deadlines at the real producer boundary

- **Cause and evidence:** Phase 14 hosted floor/sanitizer builds exposed five adapters hardcoded to `build`; Windows exposed CRLF drift in raw-digested sources, a slash-only row identity and a reserialized control manifest. Independent review then found the stamp hashing PATH CTest while consumers used pinned CTest. The sanitizer adapter retained an unscaled 15-second child deadline inside a scaled outer CTest.
- **Remedy:** Propagate the actual binary directory and configured CTest through producer and consumers; verify the real stamp and reject a substituted tool hash. Pin only raw-digested source bytes, copy admitted manifests byte-for-byte, reuse the bounded portable basename helper, and scale child deadlines explicitly while keeping strict finite caps. Put cheap seam checks before the floor's full suite.
- **Applies when:** Evidence tooling runs across build presets, host platforms, pinned tools or sanitizer configurations. Parser-only fixtures and a successful default local build do not establish these integration contracts.
- **Verification:** Nondefault-build five-test RED/GREEN; temporary Git autocrlf positive/negative control; four path spellings, seven invalid paths and capacity boundaries; exact missing-ROM failure; failing PATH CTest decoy RED/GREEN; actual-stamp substituted-tool rejection; all-child timeout propagation and invalid-limit rejection. Final hosted jobs must bind their own exact source head.
- **Source:** Phase 14 CR-03 through CR-08, their fix/recheck reports and the exact-head CI failure receipts.
- **Status:** Adopted. No new dependency or hosted job.

- **GB-CI-009 default-run supplement:** Existing regression methods are now wired into the required `cgb_corpus_report_platform_controls` CTest and the early floor gate, so the eight suffix/reader controls run by default. Verify registration and the required inventory as well as a direct unittest pass. The pre-wiring aggregate stream was intentionally stopped before its inputs changed; its incomplete receipt is not a pass.

### GB-GSD-023 / 2026-10-16 / Close automated UAT across every live handoff surface

- **Cause and evidence:** Phase 14 execution and goal verification were complete, but PROJECT still routed to execution and INDEX called execution underway. The API gate selected a hardware source-coverage document as an external API matrix. All 49 deliverables already classified as automated, so confirmation-only UAT would add toil without evidence.
- **Remedy:** Reconcile each SUMMARY against its bounded ancestor window, retain legacy count-location warnings, and map every coverage id, exact criterion and verification reference into automated UAT. Record the existing reasoned no-external-integration declaration. Check the live STATE, continuation, PROJECT and false auto flags together; keep historical receipts bounded and preserve their actual producer revisions. Reuse completed UAT unless covered contracts, contrary evidence or freshness change.
- **Applies when:** A phase has deterministic SUMMARY coverage and several durable continuation surfaces; no human judgment or external credential/hardware action is needed for its declared deliverables.
- **Verification:** Phase 14 `verify-uat-contract.py --self-test` rejects 17 weakened closure records, ten stale handoff/auto-advance records and two invalid commit claims; the API matrix accepts the reasoned declaration and rejects missing-reason and undecided opt-out controls. Existing CI retains recurring behavioral, integration, e2e, seam, smoke, package and schema checks; no new dependency or duplicate lane.
- **Source:** `14-UAT.md`, `COVERAGE.md` and `verify-uat-contract.py` in the Phase 14 directory.
- **Status:** Adopted; D-069 remains the standing zero-routine-human-UAT default. Stop before Phase 15.

### GB-RELEASE-002 / 2026-10-16 / Inspect evidence producers before treating reusable gates as release readiness

- **Cause and evidence:** Phase 15 source inspection found a ledger validator fixed to one DMG model/three cases/four manifests, tag selection that can fall back to the old ledger, A/B receipts accepting unknown revision labels, and a fuzz helper that can succeed after reporting unsupported. An initial delivery recommendation overstated existing generic support/performance sidecars as v0.2 and v0.1-comparison evidence; the adversarial pass corrected it before context was adopted.
- **Remedy:** Reuse the mechanisms while adding separate strict v0.2 validation, exact ledger selection, actual baseline/candidate binary/build identities and a real bounded Clang/libFuzzer campaign receipt. Preserve the old release validation and source-bound history. Local unavailability routes to eligible hosted execution; unsupported success cannot close a mandatory evidence requirement. Keep game absence as the specific CGB-11 alternative, not a general release waiver.
- **Applies when:** A new release broadens supported models or evidence scope while reusing older CI, sidecar, benchmark and fuzz tooling. A successful helper exit is only as strong as the producer's actual contract.
- **Verification:** Discussion uses local scope/reference/handoff contract checks and negative controls; implementation remains pending. Phase 15 plans must reject old-ledger fallback, xfail inflation, unknown/incompatible benchmark identities, unsupported/no-run campaigns and stale tag/source/package evidence through their real producers.
- **Source:** `.planning/research/phase15-evidence-consumers.md`, `.planning/research/phase15-release-delivery.md` and `15-CONTEXT.md` D-08–D-23.
- **Status:** Adopted planning lesson; no release qualification or product change is claimed. D-069/D-096 remain defaults; next command is `/gsd-plan-phase 15`.

### GB-RELEASE-003 / 2026-10-16 / Separate a stable support claim from each execution receipt

- **Cause and evidence:** Phase 15's first schema2 sidecar self-test read ignored local receipt/binary files, so clean Linux CI failed `receipt:unavailable`. Equality against the historical ledger also rejected valid independent runs and full-stream CTest totals.
- **Remedy:** Keep the tracked producer snapshot historical. Compare stable membership, assertion outcomes and covered inputs; independently validate fresh source/build artifacts and place actual run/byte identity in the generated sidecar. Generate complete synthetic contract fixtures in an isolated repository, without weakening production inventory validators.
- **Applies when:** One versioned support claim is qualified by different hosts, independent run nonces or a later exact tag. Synthetic fixtures test validators; they are not execution evidence.
- **Verification:** Repair `3d451b3` passed two real 1138/1138 native streams with 108 selected corpus tests and independent accepted receipts; clean no-build clone self-test passed with 15 schema and 21 sidecar rejections. Actual hosted native Linux/macOS/Windows and floor jobs passed at `a175a39`; the separate campaign assertion remains unresolved.
- **Source:** Phase 15 `15-02-SUMMARY.md` supplemental repair and pause handoff; `tests/scripts/verify-support-ledger.py`.

### GB-GSD-024 / 2026-10-20 / One shared UAT closure tool; boundary checks must not read live state

- **Cause and evidence:** Phases 12-14 each copied and hand-edited a phase-local `verify-uat-contract.py`, and Phase 15 verify-work did it again: a throwaway generator, then sed edits to the Phase 13 checker. The Phase 14 checker had also gone red on main. It compared the live STATE.md and `state.json` route with `/gsd-discuss-phase 15`, and required plan commits to be ancestors of HEAD. Both facts change legitimately after the boundary: later handoffs advance the route, and squash merges leave plan commits only on the phase branch.
- **Remedy:** `tests/scripts/verify-uat-closure.py <phase-dir>` does the work for any phase. `--write <evidence-file>` builds `{N}-UAT.md` from the SUMMARY coverage blocks and refuses while any deliverable needs a human or has a schema error, listing each one. The default mode checks the closure, and `--self-test` runs 19 negative controls plus a regeneration round trip. The Phase 14 checker now reads its handoff from merge commit `c771b1b` and bounds its windows by the PR #71 head `8c09f96`. Every one of its controls still fails. Commit windows and routes are reconciled once at verify-work and recorded in the UAT prose; they are not re-asserted against HEAD.
- **Applies when:** Running `/gsd-verify-work`, or writing any check that encodes a phase-boundary fact.
- **Verification:** The shared tool's self-test passes on the Phase 13, 14 and 15 UAT records (45, 49 and 42 deliverables, 19 controls each), and `--write` refuses a SUMMARY with `human_judgment: true`. The Phase 14 checker passes again, keeping all 29 of its controls. It stays local, not CI: the recurring SUMMARY side already runs in CI through `summary_coverage`, and the tool is exercised at every verify-work.
- **Refresh verification (2026-10-20, Phase 12):** The shared checker rejected the old UAT prelude with `unparsed test prelude`; canonical `--write` preserved its revision-qualified receipts and produced 73 accepted rows with 19 controls. Running the original closeout checker against a `git archive` of boundary `da98d56` passed all 17 controls, without reading live phase routes or requiring later phases to be absent from HEAD.
- **Refresh verification (2026-10-20, Phase 13):** Canonical closure accepts 45 rows and rejects 19 controls. The completed `e7ba52c` archive's pure handoff contract passes with four route/flag controls, while its full wrapper cannot execute under OpenGSD 1.18.0 because it pins 1.16.0. Preserve that limitation. The current actual prohibition producer can be independently invoked with the saved parsed/projected descriptor and must prove fail-first/clean/live behavior; this passed without changing the historical wrapper. Current routes remain a separate handoff contract; the Phase 13 refresh handoff passes with six stale-route/stage/auto-flag rejection controls.
- **Source:** Phase 15 verify-work, owner automation directive.


### GB-GSD-025 / 2026-10-20 / Passing verification does not repair completion metadata

- **Cause and evidence:** The v0.2 milestone audit read all 134 SUMMARY fields and nine goal reports. CGB-05, CGB-09 and CGB-07 were SATISFIED centrally and in verification but absent from every completing SUMMARY. Phase 7's validated record retained `nyquist_compliant: false` while its sign-off claimed true.
- **Remedy:** Cross-reference all three independent sources at closure; record partial traceability without relabeling passing behavior as missing implementation. Reconcile validated/false records through validate-phase, then update the relevant closing metadata from actual evidence. Keep immutable producer and boundary facts distinct from current routes.
- **Applies when:** Requirements close only after the final execution SUMMARY, or generated status fields and prose are maintained separately.
- **Verification:** `.planning/verify-v02-milestone-audit.py --self-test` reconciles 28 central rows, 134 summary lists and nine phase reports; 16 controls reject inflated scores, hidden partials, false Nyquist claims, changed source rows and premature milestone routing. Independent focused core/player checks passed 63/63; no new human UAT.
- **Source:** `.planning/v0.2-MILESTONE-AUDIT.md`; closure-record corrections remain pending, with `/gsd-validate-phase 7` as the next command.

### GB-TEST-006 / 2026-10-20 / Existence and size do not prove useful diagnostics

- **Cause and evidence:** Phase 7's stall-report CTest checked fresh file existence and a 64 KiB cap, so an empty report satisfied its file assertions. The validation frontmatter also contradicted its checked sign-off; rediscovery from all 17 plans / 40 tasks found the supporting task's unasserted sections and determinism contract.
- **Remedy:** Check the actual failing producer twice, require complete count-matched trace/I/O/histogram sections with declared caps, expected identity/reason and fresh bounded artifacts, then compare repeated bytes. Run cheap malformed-report controls automatically inside the existing registered CTest, with a direct fast self-test command. Preserve an inventory pinned by release evidence: the first separate CTest entry failed the hosted support-ledger binding, so the repair retained the original inventory byte for byte and passed the full ledger self-test. Reconcile metadata only after executable evidence passes.
- **Applies when:** Diagnostic, receipt or failure-artifact tests currently assert only file existence, size or successful command exit. Keep historical evidence limitations separate from missing behavioral assertions.
- **Verification:** `acceptance_stall_diagnosis` passes two real dropped-START runs; its automatic checker self-test rejects 19 malformed reports plus a byte mismatch. Focused native 97/97, player 98/98 and packaged input/PCM/no-input controls pass. The frozen DMG baseline is unchanged; no emulator implementation changed.
- **Source:** Phase 7 `07-VALIDATION.md`; `tests/scripts/verify-stall-report.py`; test revision `5f9bfbd`.
- **Status:** Adopted; Phase 11/13 completion metadata and milestone re-audit remain separate owner-selected work.

### GB-FIXTURE-004 / 2026-10-20 / Validate output paths before creating directories

- **Cause and evidence:** Phase 10's fixture rebuild script called `mkdir` before rejecting an in-tree build path. Its first repair covered explicit destinations but still called `mktemp` before checking an in-tree `TMPDIR`. Disposable-repository tests reproduced both rejected-write side effects.
- **Remedy:** Canonicalize missing destinations and existing symlink parents before directory creation; validate both build and evidence destinations, including the temporary root. Keep the offline checks in the existing registered guard test so the release-bound test inventory stays unchanged.
- **Applies when:** Build, fixture or evidence tooling promises to keep generated artifacts outside a checkout. A refusal exit alone does not prove absence of side effects.
- **Verification:** The expanded offline guard passes nested, symlink, `..`, evidence-override and both default-TMPDIR rejection cases, and accepts missing external destinations up to a deliberate pre-network stop. The same guard fails against the original script with `refused output created a directory`. Independent bounded review also passes.
- **Source:** Phase 10 `10-REFRESH-GATES.md`; `tests/scripts/reproduce-mooneye-cgb.sh`; `tests/scripts/test-reproduce-mooneye-cgb-guard.sh`.

### GB-FIXTURE-002 / 2026-10-20 / Test exclusions through the actual package scan

- **Cause and evidence:** Phase 10's CGB ROM exclusion scanned the install tree, while preview smoke supplied only the MBC manifest. A clean package and an isolated scanner self-test both passed, yet a renamed CGB ROM in the extracted preview passed its actual scan.
- **Remedy:** Supply both manifests to one preview scan command. Exercise that same command against a planted CGB ROM outside the fixture-directory allowlist, require its exact digest-based rejection, and remove the control file before consumers run.
- **Applies when:** A prohibition spans several distribution trees or a new fixture family reuses an older package check. Scanner capability alone does not prove every producer invokes it with the required inputs.
- **Verification:** The new control failed with the original MBC-only scan accepting the payload. The combined-manifest scan passed the focused package/install/ledger selection 6/6; independent bounded review found no defect. Existing test registration and inventory are unchanged.
- **Source:** Phase 10 plan 10-15 G1; `10-REFRESH-GATES.md`; `cmake/PreviewPackageSmoke.cmake`.

### GB-EVID-001 / 2026-10-21 / A closeout record must be bound to the original, not to a claim about it

- **Cause and evidence:** Phase 15.1 had to disposition 24 inherited items without rewriting them. A record that only restated each item could drop an ID, soften its text, count a hosted receipt label as a run, count a skipped required check as a pass, or fold an unrecoverable historical fact into a green row, and a stub checker that only parsed the JSON accepted all of them (`15.1-17-RED-task1.txt`).
- **Remedy:** Pin the scope inventory by digest, re-read the original text at the immutable audit commit, require hosted identities to equal API-read run records, keep limitations as open rows that cannot count as passes or owner acceptance, and pin the shipped release identity. Drive every defect through the real CLI over a private fixture repository.
- **Applies when:** A phase closes inherited debt, historical unknowns or external limitations, or a receipt-style record could be edited together with the text it vouches for.
- **Verification:** `verify-closeout-dispositions.py --self-test` rejects 30 defects, each with its own REJECT code and no success line; `--check` passes over the real records. The merge receipt is read from the hosting API, never written from memory.
- **Source:** Phase 15.1 plan 17; `tests/scripts/verify-closeout-dispositions.py`; `15.1-DISPOSITIONS.json`.

### GB-VERIFY-001 / 2026-10-22 / A verifier that uses assertion statements fails open under python -O

- **Cause and evidence:** `verify-uat-closure.py` enforced its contract with 24 `assert` statements. Under `python3 -O` they are stripped, and the checker exited 0 printing `uat-closure pass automated=42` at HEAD without checking anything (review finding WR-05).
- **Remedy:** Raise a named exception (`ClosureError`) for every rule and refuse optimize mode at module top, before any check, with exit 1 and a fixed message.
- **Applies when:** Any gate, verifier or judge script whose pass depends on `assert`, or that can be launched under `-O` or `PYTHONOPTIMIZE`.
- **Verification:** CTest `uat_closure_optimize_refused` requires exit 1 and `verify-uat-closure must not run with python -O`; an AST walk counts 0 `ast.Assert` nodes (baseline 24); `uat_closure_controls` keeps 18 weakened-closure rejections.
- **Source:** Phase 15.1 plan 15.1-21; `tests/scripts/verify-uat-closure.py`.

### GB-EVID-002 / 2026-10-22 / Bind evidence to the merge commit, not to a pre-merge branch commit

- **Cause and evidence:** After the squash merge of gap PR 94, evidence bound to branch commits had no ancestry on `main`, so strict-head and hosted-run identities no longer matched the source of record (15.1-26).
- **Remedy:** Bind hosted and historical evidence to the merge commit M on `main`, record strict-head as a row per boundary commit, and re-evaluate each row in a detached worktree at that commit.
- **Applies when:** Evidence is produced on a branch that is later squash-merged, or a check compares against HEAD.
- **Verification:** 15.1-strict-head-boundaries.tsv rows 15.1-26 and 15.1-27 reproduce byte for byte in detached worktrees; the historical `--check` rejects the old source until re-produced.
- **Source:** Phase 15.1 plans 15.1-26 and 15.1-27; `tests/scripts/verify-historical-limitations.py`.

### GB-VERIFY-002 / 2026-10-23 / A verifier that binds the subject to commit S but reads S's describing inputs from the trusted checkout fails open, then closed, after main moves

- **Cause and evidence:** `verify_hosted` in `verify-v02-fuzz.py` pinned the receipt to source commit S but judged the workflow contract against HEAD's `ci.yml`, `run-bounded-fuzz.sh` and FUZZ_ARGS literals. A weak S passed after main was strengthened (`AssertionError: 0 != 1 : fixture_hosted=pass qualification=none`), and a conforming S failed after main changed (`receipt rejected: selected sanitizer job timeout must remain bounded between 30 and 45 minutes`). It was latent because the files were identical at M and HEAD (GR-CR-01, 15.1-31).
- **Remedy:** Read the files that describe the campaign from S as data through a bounded `commit_blob`, and keep the judging code and required limits at HEAD. Controls diverge those inputs between S and HEAD in both directions through the real CLI, and a mutant that reads HEAD must fail them.
- **Applies when:** Any verifier that takes a commit identity and also reads configuration, workflow or fixture files describing that commit from the working tree.
- **Verification:** `verify-v02-fuzz.py --self-test` prints `negative-control=weak-source-workflow-rejected-after-main-strengthened`, `positive-control=conforming-source-workflow-accepted-after-main-changed`, `negative-control=weak-source-fuzz-args-rejected` and `negative-control-sensitivity=head-read-contract-mutant-fails-open`.
- **Source:** Phase 15.1 plan 15.1-31; `tests/scripts/verify-v02-fuzz.py`; `15.1-GAP2-CLOSURE-EVIDENCE.md`.

### GB-CI-010 / 2026-10-24 / Re-running a hosted job that is near its timeout is toil, not a fix

- **Cause and evidence:** Docs PR #98 (head `6a4f3b1`) needed seven full CI attempts. `cmake-floor-3.25.3` ran its whole suite serially and took 20-40 minutes against a 40-minute timeout across 2026-10-22..24 runs. `linux-asan-ubsan` already ran 4 tests at once and took 1203-1693 s of test time, but one runner was uniformly about 1.55x slower (`acceptance_stall_diagnosis` 1164 s vs 1838 s, `v02_consumer_controls` 770 s vs 1184 s) and was cancelled at 45 minutes with no hung test (ci run 40045420290 attempt 6). GB-CI-004 already said to check headroom instead of re-running; the round-2 executor re-ran five times.
- **Remedy:** The floor job sets `CTEST_PARALLEL_LEVEL: 4` so both of its full runs are parallel, pinned by `ci_floor_parallel_contract` with negative control `ci_floor_parallel_serial_selftest`; locally the whole suite passed 1183/1183 in 121 s at four tests at once. The full ASan inventory moved out of `linux-asan-ubsan` into two complementary shards, `linux-asan-ubsan-tests` (`-E '^acceptance_'`) and `linux-asan-ubsan-acceptance` (`-R '^acceptance_'`), each under the original 45-minute bound and each checking exactly its `grep` slice of `tests/expected-tests.txt`; `required-native` gates on both. The first attempt (one 75-minute inventory job, 329407b) passed CI but made the whole ci run outlast the preview waiters' 2700 s deadline (`exact-head-ci: FAIL deadline reached`) and would have outlasted the release fuzz reader's pinned 2700 s poll, so it was replaced: a job split must keep the whole run inside every waiter's budget, not just its own timeout. The fuzz campaign job keeps its pinned 30-45 minute bound unchanged, so no policy was weakened. Workflow policy requires each shard's exact commands and has six new mutants (needs, result read, inventory call, non-complementary filter, whole-list slice); the corpus CI contract requires both shard commands, and the GB-13 HDMA lane contract now requires every ASan JUnit run to stay parallel (its mutant stopped biting once there were two such lines).
- **Applies when:** A required hosted job fails on its timeout more than once for the same head. Compare per-test durations from the job logs across runs before re-running again; a uniform ratio means the runner, a skewed one means the code. Also keep a long local run awake (`caffeinate -ims`): macOS maintenance sleep during this verify made six tests "time out" together at the sleep length.
- **Verification:** `ci_floor_parallel_contract`, `ci_floor_parallel_serial_selftest`, `ci_asan_parallel_contract`, `verify-workflow-policy.py --self-test` (164 negative controls), `cgb_hdma_lane_contract_selftest`, `verify-cgb-corpus-inventory.py --ci-contract`; hosted durations on PR #98.
- **Source:** Phase 15.1 verify-work; ci runs 40045416222, 40045420290.
- **Status:** Adopted.

### GB-GSD-026 / 2026-10-24 / Keep test-consumed files out of phase directories that milestone close will move

- **Cause and evidence:** At the v0.2 close, `milestone.complete --confirm` archives phase directories by default and moved all ten v0.2 phase directories (`GB-07`..`GB-15.1`) to `milestones/v0.2-phases/`. But `tests/CMakeLists.txt` registers `.planning/phases/GB-13-cgb-hdma/verify-hdma-closure.py` (line 1208) and the GB-15 UAT-closure phase (line 2687), and seven test scripts open files under the GB-08, GB-13, GB-14, GB-15 and GB-15.1 phase directories. Main would have lost those tests. At v0.1 nothing in `tests/` referenced a phase directory, so archiving there was safe.
- **Remedy:** The move was reverted. The diff of the archived copy against the restored tree showed only `__pycache__` and the acknowledgement marker. The close then went ahead with phase directories in place (equivalent to `--no-archive-phases`). Only the roadmap, requirements, audits and quick task were archived, and links in the archived documents were repointed.
- **Applies when:** A plan puts a verifier, fixture or record that CTest or CI reads inside a phase directory, or a milestone close is about to archive phases. Put reusable checkers in `tests/scripts/`. Before archiving, run `grep -rn 'planning/phases' tests .github CMakeLists.txt cmake`, and archive only when the grep is empty (or once the references point at the archive path).
- **Verification:** the grep above lists 9 consumer files at v0.2 close; `ctest` over the affected tests passes with phase directories in place.
- **Source:** v0.2 `/gsd-complete-milestone`.
- **Status:** Adopted. Follow-up: move the helpers into `tests/`, then archive the v0.2 phase records.

### GB-GSD-027 / 2026-10-26 / Record post-merge boundary facts outside the verifier's covered files

- **Cause and evidence:** Plan 16-07 told the orchestrator to append `boundary_sha` to `16-07-SUMMARY.md` after the boundary PR merged. The verifier had already fingerprinted that SUMMARY into `16-VERIFICATION.md` (`covered_digest`). The appended lines changed nothing else (no source, test or workflow change between `92364c7` and `be4cee8`), yet `verification.status` read `stale` at verify-work and `phase uat-passed --require-verification` blocked. That forced a full verifier re-run whose only finding was the same pass.
- **Remedy:** Write post-merge facts (the boundary SHA, merge commits, hosted run ids) only to `continue.md`, the UAT `## Automated Evidence` prose, or STATE.md, none of which the verifier covers. Never write them to a `*-SUMMARY.md`, `*-PLAN.md` or other file listed in `covered_files`. If a plan needs one in a covered file, write it before dispatching the verifier. A SHA that cannot exist yet belongs in `continue.md`.
- **Applies when:** Writing a plan's closing tasks or an orchestrator handoff that records facts known only after a merge.
- **Verification:** At Phase 16 verify-work, `verification.status` returned `stale` with `16-07-SUMMARY.md` as the only covered change. After the verifier re-ran, it returned `passed` (digest `d7e63dc2…`). Check at the next verify-work: `verification.status` on the unmodified report reads `passed`, not `stale`.
- **Source:** Phase 16 `/gsd-verify-work`, owner automation directive (reduce toil).

### GB-CORE-002 / 2026-10-28 / Resolve per-field rules once, not per element, in bulk codec walks

- **Cause and evidence:** `state_field_value_valid` chose its range rule by comparing `field->path` against about 120 rule names with `strcmp`, and `state_walk` called it for every element of every field. A 197,368-byte format-v1 state spent most of its validation time in `strcmp` (macOS `sample`: about 1,400 of 2,300 top-of-stack samples). Debug `gbb_save_state`/`gbb_load_state` took 15/29 ms. The fuzz state target saves four times and loads twice per input, so hosted Clang 18 ASan + libFuzzer at `b3e57bc` hit the pinned 2 s per-input timeout on an ordinary accepted-closure input (`F0 00 07 ...`, DMG scenario 7, 24 executions in 24 s). Locally the same input took 0.09 s unsanitized, which hid the cost.
- **Remedy:** `f0591f4` routes every path comparison through `state_value_path_is`, which records a match. `state_walk` resolves on a field's first checked element whether any path rule applies, and checks later elements of rule-free fields (VRAM, WRAM) with `state_field_kind_valid` only. Debug save/load dropped to about 6/6 ms and the fuzz input to 0.04 s. The fuzz timeout was not raised, because the receipt verifier rejects weakened fuzz arguments.
- **Applies when:** Any per-element loop over a large serialized body (state, battery, frame) calls a helper whose behaviour depends only on the field. Hoist the field-dependent decision out of the element loop. When a hosted sanitizer fuzz job times out, time the public calls one by one before suspecting a hang; the ratio between unsanitized local and hosted ASan cost is roughly 10-20x.
- **Verification:** `state_semantic_bounds` rejects late-element values in `frame_completed`, `frame_working`, `obj_cram` and `rgb_working`; forcing `path_rule = 0` after the first element makes it fail at `compat_rgb555[1]`. Hosted `linux-asan-ubsan` passed at `ec8287d` and `0c8fd56`.
- **Source:** Phase 17 PR130 hosted run 40693803431 (job 122835214740, artifact `timeout-702c0d62…`); `src/core/gabbaboy.c`.
- **Status:** Adopted.

### GB-CI-011 / 2026-10-28 / Windows breaks checkers on text-mode writes, CRLF checkouts and reopened temp files

- **Cause and evidence:** `native-windows-x64` passed at Phase 16's end (`2eea1e8`) and failed on every Phase 17 head from `032ea01` to `ec8287d`, while Linux and macOS passed. Three independent checker bugs: `verify-perf-gate.py` reopened an open `NamedTemporaryFile` (`[Errno 13] Permission denied`, seven perf tests); `verify-state-forks.py` wrote the fork mutant core with `write_text`, so newline translation changed the bytes whose digest every mutant shard must match (`mutant shard metadata mismatch: 0`); `verify-v02-fuzz.py` compared raw worktree bytes with the committed blob, so the runner's `core.autocrlf` checkout of an unchanged `CMakeLists.txt` looked stale. Separately, two POSIX-only advisory producer controls (shell-script cmake and measurement binary) ran on Windows: one failed with `qualify-v02-measurement-binary-missing` after 48 s, and a full `git clone --no-hardlinks` in the delivery control pushed `v02_performance_controls` and `v02_delivery_controls` past their 90 s budgets.
- **Remedy:** `be8ec08` parses a closed file in a `TemporaryDirectory`, writes the mutant core as bytes, and asks `git diff --quiet <commit> -- <path>` (which applies eol conversion) instead of hashing raw bytes. `0c8fd56` skips both advisory producer controls on `os.name == "nt"` with the same documented reason as the existing pipeline skip; Linux lanes still run them and delivery still clears its positive and control minimums. PR130 was fully green at `0c8fd56` (41 pass).
- **Applies when:** A checker writes a file whose bytes are later digested, compares worktree files with git blobs, or hands a temp file name to another reader; or a self-test drives a POSIX shell fixture. Write bytes (or `newline="\n"`), compare through git, close temp files before reopening, and skip POSIX fixtures on Windows explicitly. When one lane fails across a whole phase, find the last green run of that lane (`gh run view <id> --json jobs`), since `main` may have path-skipped it, and diff per-test durations against it.
- **Verification:** `test_worktree_source_check_is_eol_aware_and_rejects_edits` in `verify-v02-fuzz.py --self-test` (an autocrlf CRLF checkout of an unchanged blob is accepted; an edit is rejected as stale); hosted `native-windows-x64` at `0c8fd56`.
- **Source:** Phase 17 PR130 ci runs at `ec8287d`, `be8ec08`, `0c8fd56`.
- **Status:** Adopted.

### GB-GSD-028 / 2026-10-28 / A runtime switch leaves a stale lock and an unpersisted route behind

- **Cause and evidence:** When the owner moved from Codex to Claude Code mid-Phase 17, the old session (PID gone) left `.planning/milestone.lock` and an uncommitted `.planning/state.json` that marked completed Phase 16 `in_progress` and replaced the route `/gsd-execute-phase 17` with a generic `$gsd-progress --next`. Its last full suite had been deliberately stopped and could not count as a pass, and its final "completed" message was a worker status, not evidence.
- **Remedy:** On resume, check the lock's PID, diff `state.json` against HEAD before trusting the route, and treat the prior session's last suite as absent unless its log shows a finished pass at the current head. Re-run the settled suite at HEAD, then record it in STATE.md and `continue.md`.
- **Applies when:** Resuming after a runtime, machine or session change, or after any interrupted orchestrator.
- **Verification:** At resume, `ps -p <lock pid>` returned nothing, `git diff .planning/state.json` showed the regressed route, and the fresh suite at `7cb5739` surfaced a real `test_budget` failure (fixed in `5701130`) that the stopped run had not reached.
- **Source:** Phase 17 resume under Claude Code, 2026-10-28.
- **Status:** Adopted.

### GB-CI-012 / 2026-10-28 / A CTest budget passed at 96% is a pending failure

- **Cause and evidence:** `v02_support_ledger_controls` passed in 115.71 s against its 120 s TIMEOUT on hosted `native-windows-x64` at `0c8fd56` (run 40707388400), the first green Windows lane of Phase 17. Plan 17-08 then added disclosure controls (about +2 s on macOS) and the same test timed out at `246b7d4` (run 40729489427). Seven more checks failed in cascade, because package smoke and `required-native` wait for a green exact-head CI run. The self-test spawned one `git show tag:path` per covered source input per sidecar build: 1,398 git processes, 436 distinct. Process spawn costs several times more on Windows runners.
- **Remedy:** `e5064c3` reads each sidecar build's tagged inputs through one `git cat-file --batch` process. Tag binding, path guard, per-file size limit and digest checks are unchanged. Names with CR/LF keep the single-file path. Locally the self-test dropped from 30.1 s to 12.4 s and git calls from 1,398 to 209. The budget was not raised.
- **Applies when:** A green hosted run shows any test above about 75% of its TIMEOUT, especially Windows tests that spawn many processes. Treat it as a defect at once rather than waiting for the next control to tip it over. Check the per-test time in the previous green Windows log before blaming the newest change.
- **Verification:** Mutants that misframe the batch output, truncate a blob, or read `HEAD` instead of the tag each make `verify-support-ledger.py --self-test` fail. The full suite passed 1488/1488 at `e5064c3`. The next hosted Windows run at the pushed head should show the test well under 60 s.
- **Source:** Phase 17 PR130, plans 17-08/17-09; `tests/scripts/verify-support-ledger.py`.
- **Status:** Adopted.

### GB-GSD-029 / 2026-10-28 / Existence audits pass controls that cannot fail; review the controls themselves

- **Cause and evidence:** Phase 17's Nyquist audit (32/32 rows green) and security audit (29/29 closed) checked that each planned test or mitigation existed and passed. Three independent code reviewers then found 5 critical defects at `e8ea47a`. Three CTests, `state_purity_mutant_*`, built one identical wrong mutant: an unquoted `;` in a CMake argument split it. A generic failure regex let all three pass. 7 of 14 horizon mutants passed a witness check that matched a line the probe always printed. The Ir OWNER approval was not bound to the repository, and no policy rule stopped a workflow from supplying it. The state validator was wrong both ways: valid live states were un-saveable (stale stalled-object bits, palette bit 7), and a hostile `dma_active=1, dma_index=160` state loaded and wrote past `oam[]`. No test asserted that every reachable state is saveable.
- **Remedy:** Review-fix round 1 (`b2acaa7`..`e9e2d57`) fixed every critical and 10 of 13 warnings. Each fix has a negative control that fails on the defect: per-mutant regexes plus an ARGC check, an assertion-anchored horizon witness, repository binding plus the `ir-exception-env` policy rule, and new `state_reachable_saveable_dmg`/`_cgb` properties. Before the fix those properties failed 5 and 72 times.
- **Applies when:** Closing any phase whose deliverables are checkers or negative controls. Prove each control is discriminating: make the defect, see the control fail for its intended reason. A matching name and a pass are not enough. For any validator of host-supplied state, pair the hostile-input refusals with a reachable-state saveability property. Run an independent code review before marking the security audit verified, because existence-level threat checks will not see a control that cannot fail.
- **Verification:** At `e9e2d57` the full suite passed 1496/1496. The three purity mutant sources differ, and each is killed only by its own regex. A tree copy with `GBB_IR_EXCEPTION_DECISION` injected into `ci.yml` is refused with `ir-exception-env`. Next check: the Phase 18 review finds no control that a mutant cannot fail.
- **Source:** Phase 17 `17-REVIEW.md`, `17-REVIEW-DISPOSITION.md`.
- **Status:** Adopted.

### GB-GSD-030 / 2026-10-29 / "Pre-existing" must be shown at the phase boundary, not at an earlier in-phase commit

- **Cause and evidence:** After Phase 18 review-fix round 1, three `build-player` failures (`core_linkage_links`, `core_linkage_controls`, `test_budget`) were labelled pre-existing because they also failed at `72a88d97`. That commit is inside Phase 18. `test_budget` was a Phase 18 defect: six `player_slot_*` tests declared `TIMEOUT 120` with no allowlist row while the slowest ran in about 6 s. Only the linkage failures held up against the Phase 17 boundary `f4082a6` (same targets, unchanged checker). CI runs only `^player_` on the player-enabled build, so no hosted lane would have caught either defect.
- **Remedy:** `135c6cc5` restored the 60 s base timeout. The linkage debt went to RM-031 with its targets named.
- **Applies when:** Any failure is waved off as pre-existing, and any build configuration whose full CTest tree no CI lane runs. Re-run the failing test at the previous phase's boundary commit (or prove that the inputs are unchanged since then) before writing "pre-existing". Run the configuration's planning-label checks (`test_budget`, `core_linkage_*`) at phase close even when CI does not.
- **Verification:** `ctest --test-dir build-player -R '^(test_budget|player_slot)'` passed 10/10 at `135c6cc5`. Before the fix, `test_budget` failed with six `REJECT over-budget` lines.
- **Source:** Phase 18 verify-work, 2026-10-29.
- **Status:** Adopted.

### GB-CI-013 / 2026-10-29 / A checker that parses CMake's generated files must accept every CMake version's spelling

- **Cause and evidence:** WR-04's `contract_rev_wiring` read `CTestTestfile.cmake` with a regex for `add_test("name"`, the form the local CMake 4.4 writes. CMake 3.25.3 (the floor) and the hosted runners write `add_test([=[name]=]`, so hosted CI at `6f8e8f6a` failed it on Linux, Windows, ASan and the floor lane. The local suite was green, and the package smokes failed only as cascades (they wait for an exact-head green `ci` run). Nobody saw this until the PR was opened, because the branch had gone 88 commits without a push.
- **Remedy:** `abd8ceed` accepts quoted, bracket and bare names, and ends a name at a delimiter so a prefix cannot match a longer name. The two new controls are `contract_rev_wiring_bare_form` (it fails on the old checker) and `contract_rev_wiring_bare_prefix_control`.
- **Applies when:** A checker parses CMake-generated output (`CTestTestfile.cmake`, `compile_commands.json`, ninja files), or any tool output whose spelling varies by version. Add a fixture in every spelling the supported versions emit, and confirm it against a real file from the floor version. Push a phase branch and open its PR early, so hosted lanes run during execution rather than at verification.
- **Verification:** A CTestTestfile generated by the official CMake 3.25.3 (digest-checked macOS archive) passes the new checker and fails the old one with "not registered". The full suite passed 1678/1678 at `abd8ceed`.
- **Source:** Phase 18 verify-work, PR #132.
- **Status:** Adopted.

### GB-CI-014 / 2026-10-30 / Identify the selected Windows shell before diagnosing its script

- **Cause and evidence:** At E0 `e0ca6463c3b6379fe65f28bb1fa0673be79ee071`, `workflow_policy_controls` launched bare `bash` from Python on Windows. Both push job 123987812944 and PR job 123987817960 returned `Windows Subsystem for Linux has no installed distributions`, exit 1 and zero fake Git calls. The job itself also used Git for Windows' bundled Bash, so a usable shell was present while the nested process selected WSL. The initial absolute-log-path hypothesis was insufficient; added subprocess diagnostics exposed the actual failure before any guard script ran.
- **Remedy:** The owner approved the bounded rescope under D-121. The initial selector at `8f4deeddd07ddf06f9927a1c6c571b717732b06e` missed the runner's observed `ucrt64/bin/git.EXE` layout. The in-scope correction at `dedeb22a5528b0ec6bb3cb4845a535303f66ccd4` derives the correct installation root and selects its bundled Bash, with five refusal/five positive resolver controls and all three real tag scenarios retained. Inspect the actual runner path rather than assuming a historical Git layout. Production guards, timeout limits and prior assertions are unchanged.
- **Applies when:** Python or another native Windows process starts a shell by a bare executable name. A working parent shell does not prove that a nested process selects the same interpreter. Capture return code, selected executable, stdout/stderr and observable calls before diagnosing a platform-only failure.
- **Verification:** The actual E0 Windows failures falsify the first hypothesis and identify the WSL launcher. Full registered Windows controls and inventory must pass after any approved correction; local Bash success is not target-platform evidence. E0's local 1,690-case and six-producer preflight evidence remains separate from failed exact-head CI.
- **Source:** Phase 19, PR #133; CI runs 41033231735 and 41033238701; ignored rescope proposal `build/preflight/review/19-WINDOWS-RESCOPE.md`.
- **Status:** Implementation reviewed under D-121; actual Windows CI and renewed final-source qualification pending. No platform pass is inferred from local tests.

### GB-CI-015 / 2026-10-30 / Split broad checks by semantic domain without thinning coverage

- **Cause and evidence:** On exact D-123 source dcb2, the first PR CI attempt timed out in the combined CGB probe/load parity check at its unchanged 60-second limit. The one full same-source retry passed that check but timed out in the combined post-tag lifecycle controls at 60.06 seconds. The preceding lifecycle control completed in 45.48 seconds; the post-tag test was the only active CTest when it timed out, so its existing serial policy was working. Windows passed the new UTF-8 controls on both attempts, and no decoder defect was found.
- **Remedy:** D-124 partitions parity by its existing DMG/CGB model axis and post-tag controls by their existing semantic families. Keep every assertion, input and fixed limit; give each CTest an emitted model/group success marker and preserve the lifecycle control IDs in an immutable baseline manifest with complete/disjoint registration checks and omission/duplication/wrong-group negatives. Update the exact inventory and Windows POSIX exclusions with the registrations.
- **Applies when:** A broad required CI check approaches or exceeds its fixed limit while its constituent cases already have meaningful model or semantic boundaries. Partition only along those existing boundaries, and verify the exact executed set independently; do not raise the timeout or remove work to make the job green.
- **Verification:** At integrated revision `d609c98fe8dfb42cccbf0d8bebe29fab6a8f34e6`, the focused CTest selection passed 15/15, including all parity and lifecycle partitions, immutable 87-ID coverage, legacy lifecycle controls/replay, `summary_coverage` and `test_budget`. Inventory/platform-filter controls passed; wrong-model/group CTest metadata mutants were refused by the emitted-marker wrapper; a pre-manifest revision was refused without worktree fallback. Independent review and exact-head Windows/macOS hosted CI remain required.
- **Source:** Phase 19 D-123 logs and approved D-124 scope in `19-CI-PARTITION-RESCOPE.md`.
- **Status:** Approved; local implementation and integration checks pass. Independent final review and hosted qualification pending.

### GB-RELEASE-004 / 2026-10-31 / Preflight generated notes and read back every draft field before retrying publication

- **Cause and evidence:** The first v0.3.0 release run at tagged source S failed before build or attachment because the generated release body omitted the required reviewed preface. After corrective source qualification, a body-only release API update returned HTTP 200 with the repaired body but also changed the same draft's tag association. The guard stopped before retry dispatch. An explicitly approved tag-only restoration kept the same release ID and body bytes; one main-head workflow retry then published the existing tag's source. This phase used its one reserved D-27 gap slot. The original failed run and the later successful retry remain separate records.
- **Remedy:** Before a tag, exercise generated release notes through the production adoption check and a pre-tag gate. For any post-tag repair, preserve the original API response and verify the exact field-level request. Immediately reread the complete release identity, body, publication state and assets after every mutation; any unexpected field drift is a stop requiring explicit owner scope. Bind retry execution to actual workflow head G while independently binding tag, assets and receipts to product source S. Dispatch at most once and keep the failed run immutable.
- **Applies when:** A release uses generated notes, mutates a pre-existing draft or retries an already tagged source. A successful HTTP status alone does not prove that untouched release metadata stayed unchanged.
- **Verification:** The original notes fixture reproduces `release-notes-absence-missing`; the original tagged changelog section and exact single-link repair pass the production adoption check. `release_lifecycle_post_tag_recovery_controls`, `v03_readback_controls` and `v03_readback` pass with wrong-state, drift, duplicate-dispatch and G/S substitution negatives. Actual retry run 41205021983 completed on G, published release 429606490 from S, and its captured 22-asset readback passed. Evidence is in the 19-08 SUMMARY, `19-release-readback.json`, and ignored `build/phase19-window/release-S/published-41205021983/` captures.
- **Source:** Phase 19 plans 19-07/19-08; original release run 41148606886 and retry run 41205021983.
- **Status:** Adopted.

### GB-GSD-031 / 2026-10-31 / Retain branches that hold immutable review authorities

- **Cause and evidence:** Phase 19's frozen workflow-policy review authorities `70d3e42225c14e636876aad6697672ec08d861b3` and `2c4a66ad50b979bbfcf3bff6cf9f4e644a56d9b7` remain reachable through the retained `gsd/phase-19-window-discovery-repair` branch and full-history fetches. Deleting that branch during routine cleanup would remove the durable route to those exact reviewed objects unless they were re-anchored elsewhere.
- **Remedy:** Keep the authority branch and full-history references through phase and milestone cleanup. Before pruning, obtain an explicit reviewed authority rebaseline, verify the replacement objects and references, and record the new route in the continuation note.
- **Applies when:** A plan pins earlier source objects for policy, security, or regression review and those objects are not reachable from the release branch.
- **Verification:** At the Phase 19 boundary, both full object IDs were retained and remained reachable through the repair branch; branch cleanup is deferred until an authority rebaseline is reviewed.
- **Source:** Phase 19 D-125..D-129; `build/phase19-window/PR-B-RECOVERY-NOTES.md`.
- **Status:** Adopted.


### GB-RELEASE-005 / 2026-10-31 / Test schema type boundaries and adjudicate against the actual protocol

- **Cause and evidence:** Python equates True and1, allowing boolean schema fields through several version1 comparisons. A non-object registry also escaped as AttributeError. Actual v0.3.0 inventories used the correct integer schema, but final review exposed missing refusal controls. An adjacent legacy performance parser accepted numeric3.0 without bypassing any source/measurement check; no exact-token contract existed there.
- **Remedy:** At boundaries that declare exact integer representations, test booleans, floating forms, strings, nulls and arrays alongside valid integer positives. Verify error paths through the actual CLI and recompute dependent hashes in negative controls so an unrelated hash refusal cannot hide a missing type guard. Validate a review finding against the protocol before broadening a repair: equivalent integral JSON numbers alone do not establish a defect ([JSON Schema numeric semantics](https://json-schema.org/understanding-json-schema/reference/numeric)).
- **Applies when:** Python validates versioned evidence or configuration, especially when shared helpers have distinct legacy wire contracts.
- **Verification:** D134 source d2c0dc95 passes eight existing affected CTests, preserves all baseline assertions/timeouts and receives fresh independent code/security rechecks. Production probes reject malformed versions and incorrect workload digests; the unsupported legacy hardening finding was withdrawn with evidence.
- **Source:**19-SCHEMA-VALIDATION-RESCOPE.md,19-REVIEW.md and19-REVIEW-DISPOSITION.md.
- **Status:** Adopted.

### GB-CI-016 / 2026-10-31 / Keep immutable Git paths and checkout byte identity explicit

- **Cause and evidence:** Final release readback passed a filesystem-absolute path to an immutable Git reader. Native Windows correctly refused its drive-prefixed path. A separate helper byte guard refused an unpinned CRLF checkout although the helper source blob was unchanged.
- **Remedy:** Derive the Git path relative to the repository from the configured phase root, retaining the immutable revision and path refusals. Pin only the exact byte-compared helper to LF; preserve the byte guard and an unpinned line-ending negative rather than normalizing away the mismatch.
- **Applies when:** CMake passes configurable paths into Git-tree readers, or tests execute helpers whose working-tree bytes must equal their immutable blobs across platforms.
- **Verification:** Forced-autocrlf baseline/fixed controls distinguish the defect; wrong paths and changed helper bytes still reject. Both native Windows jobs at the reviewed PR137 source pass the readback, recovery and independent APU EOL negative. The guarded squash retains that source tree.
- **Source:**19-WINDOWS-READBACK-WIRING-RESCOPE.md; PR137 qualification and ignored posttag-recovery/d136-hosted-native evidence.
- **Status:** Adopted.

### GB-CI-017 / 2026-10-31 / Publish readiness files only after their contents are complete

- **Cause and evidence:** The installed-consumer interruption test treated marker existence as readiness while its child wrote JSON directly to that name. Linux sanitizer CI caught the creation-to-write window and raised JSONDecodeError on an empty marker; the checker was unchanged from the release source.
- **Remedy:** Write the complete marker to a unique sibling temporary, then replace the ready name atomically and clean up any remaining temporary. Preserve the real interruption, lock, cleanup and retry assertions and every deadline. Use deterministic empty/partial-write scheduling points instead of hoping repeated runs hit the race.
- **Applies when:** A parent process polls for a child-produced readiness file and immediately parses its payload. Atomic publication makes name visibility the completion signal without sleeps or weaker assertions.
- **Verification:** The controlled probe reproduces the exact empty-JSON failure; the regression rejects the exact original writer and passes the atomic writer. Both complete consumer halves, both native Windows jobs and both native Linux sanitizer test shards pass at the reviewed source. PR137 merged only after every protected check and downloaded-package gate passed.
- **Source:**19-CONSUMER-MARKER-RESCOPE.md;19-REVIEW.md; ignored consumer-marker-prep, consumer-marker-local and d136-hosted-native evidence.
- **Status:** Adopted.


## v0.3 milestone-boundary exchange / 2026-10-31

The read-only [sibling/Playstead scan](../research/v0.3/MILESTONE-BOUNDARY-LESSONS.md) records committed revisions, applicability, limits and a concise outgoing transfer. All six sibling cores plus Playstead were checked; Earthbound was an additional recent CI/history check. No sibling was modified or executed. Reuse the original kickoff hardware/state design research; these additions concern evidence accounting, real-provider failures and build freshness. No imported lesson establishes another console's behavior or live Playstead compatibility.

## v0.3 archival input correction / 2026-10-31

- **Cause and evidence:** Archival inspection found two existing CTest inputs still under the live phase-root variable: the Phase 16 disposition ledger and Phase 19 readback. A pure phase move would leave the first missing at runtime and the second missing at the configured Git revision.
- **Remedy:** Point both existing inputs and the disposition ledger's receipt paths at the named v0.3 archive root; retain repository-relative Git path derivation, immutable-revision reads, existing assertions and negative controls. Keep the future live SUMMARY sweep.
- **Applicability:** Milestone archives that move test-consumed records; historical boundary checks continue reading their original commits.
- **Verification contract:** Pre/post archive manifests preserve every SUMMARY/VERIFICATION byte; removed-summary and mutated-report controls fail. The existing disposition/readback checks and their controls must pass after committing the archive and reconfiguring at that exact revision.

- **Additional archival evidence:** The plan-cap gate rejected a deliberately collapsed roadmap, and the deferral omission control removed only one copy of a now-repeated marker. Read the matching archive only at an explicit completed boundary in the same commit with no active requirements/plans; reject missing archives and over-cap fixtures. Remove all marker copies for the omission mutant, with a repeated-marker positive twin. These changes extend the existing CTest checks rather than creating a new workflow.
