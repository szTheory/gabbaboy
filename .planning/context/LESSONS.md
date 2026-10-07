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
