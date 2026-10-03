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

The first implementation-derived lesson follows; continue adding entries with evidence as phases ship.

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
