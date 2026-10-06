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
- **Status:** Boundary defect corrected; corpus admission/completion remains open in CR-05 and T-02-15.

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
- **Verification:** CR-01..04 are structured in the current goal report and remain open; no passing targeted regression yet closes them.
- **Status:** Observed; gap planning required.

### GB-FIXTURE-001 / 2026-10-06 / Phase 2 fixture admission

- **Cause and evidence:** Mooneye's root MIT license did not close redistribution rights for every included asset. The pinned common include identifies Darkrose's font and links to an asset page, but the pinned suite tree has no font source or font-specific license.
- **Remedy:** Plan 02-07 replaces only the bundled 2032-byte font asset with an original zero-filled image, preserving ROM layout and test instructions/protocol. It records source/include closure, notices, replacement digest, immutable WLA-DX pin, and generated ROM digests.
- **Applies when:** Compiling third-party diagnostic ROMs whose common includes embed independently licensed artwork.
- **Verification:** `font-source.c` generated the recorded 2032-byte asset; three ROMs were assembled from Mooneye commit `31510e12eea6286d36eea060a6adde755e1067aa` with WLA-DX commit `91c52b1f4ef3cc8ba3c0638f7536539579af6a9f`. Offline digest/inventory checks and the full 72-case CTest suite passed. Generic-runner timeout/unsupported-bus results do not qualify guest behavior; Plan 02-08 owns protocol-aware results.
- **Status:** Original replacement and offline digest checks implemented; corpus applicability and runtime completion are blocked. Hosted byte reproduction later failed, superseding any general reproducibility claim.

### GB-CI-002 / 2026-10-06 / Phase 2 planning review

- **Cause and evidence:** Plan 02-09 repeated the relative JUnit path error recorded in GB-CI-001 despite passing structural review. A fresh temporary one-test CTest run confirmed that `--test-dir <dir> --output-junit build/probe.xml` writes beneath `<dir>/build/`, not the caller's directory.
- **Remedy:** Use report basenames for preset/test-dir invocations, then verify the corresponding selected-directory path; clear cached installed-prefix configuration for a core-only inventory. Plan 02-09 now states both rules.
- **Applies when:** Planning CTest evidence commands for fresh or reused build configurations.
- **Verification:** Temporary tooling probe passed 1/1 and the predicted report existed. Phase 2 tests and installed inventory remain pending; structural review alone does not prove runnable command behavior.
- **Status:** Reproduced and reconciled in the plan.

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
- **Verification:** PR-head `a91d8e7` CI and fixture runs complete with failure; Linux/macOS native 95/99, sanitizer/floor 90/94 and Windows 93/99. Tracer reproduction passes while Mooneye reproduction fails. These two additional gaps are persisted in the goal report.
- **Status:** Observed; both qualification gaps remain open.
