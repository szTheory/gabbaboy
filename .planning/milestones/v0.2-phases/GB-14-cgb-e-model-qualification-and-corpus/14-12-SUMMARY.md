---
phase: 14-cgb-e-model-qualification-and-corpus
plan: "12"
subsystem: testing
tags: [CGB, CTest, CMake, corpus, receipts, CI]
requires:
  - phase: "14-11"
    provides:
      - "Frozen source IDs and AGE row-consumer corrections"
      - "Full prior-wave native CTest baseline"
  - phase: "14-08"
    provides:
      - "Pinned CGB fixture selection and disposition contracts"
provides:
  - "Build-input-stamped 107-case receipt from one complete CTest stream"
  - "Recurring inventory, reproduction, and package-boundary contracts"
affects: [Phase 14 aggregate verification, native CI, fixture reproduction]
actuals:
  tokens: 25768
  tasks: 3
  commits: 12
plan_head_before: 30fcb3a9bb6b8ed36f3f4e29225807c298d3e993
plan_head_after: e21112c259a10d1d6c6a049eddb852435104facc
commits: 12
tech-stack:
  added: []
  patterns:
    - "Nonce-bound CTest Test.xml and JUnit receipt from one full test stream"
    - "Manifest-hash package exclusion with renamed ROM and PNG controls"
    - "Privacy-checked JSON artifact allowlist while raw CTest XML stays local"
key-files:
  created:
    - tests/CheckCgbCorpusPackageControls.cmake
    - .planning/phases/GB-14-cgb-e-model-qualification-and-corpus/14-12-red-task1.json
    - tests/scripts/verify-cgb-corpus-artifacts.py
  modified:
    - .github/workflows/ci.yml
    - .github/workflows/fixture-repro.yml
    - cmake/ScanForbiddenFixtures.cmake
    - docs/cgb-corpus.md
    - docs/native-integration.md
    - tests/CMakeLists.txt
    - tests/expected-tests.txt
    - tests/scripts/test-cgb-corpus-report.py
    - tests/scripts/verify-cgb-corpus-inventory.py
    - tests/scripts/verify-cgb-corpus-report.py
    - tests/scripts/verify-cgb-hdma-claims.py
key-decisions:
  - "Use --bindings for static selection/output/test identity; keep --complete's terminal-observation requirement strict and use the fresh execution receipt for runtime completeness."
  - "Collect at most 16 MiB from each passing CTest case so the bounded receipt retains complete guest output."
  - "Keep audio observations guest-only and digital; add no PCM getter, UI, or physical-device claim."
patterns-established:
  - "CTest Test.xml result records are distinguished from TestList paths and must have one captured output measurement."
  - "A nonce-bound receipt consumes Test.xml and JUnit from the same CTest execution without rerunning corpus tests."
requirements-completed: []
coverage:
  - id: D1
    description: "Native CI validates exact corpus bindings and creates a fresh complete receipt from one full CTest execution."
    requirement: CGB-08
    verification:
      - kind: integration
        ref: "Fresh committed-head receipt: 107/107 cases from the nonce-bound 1,133-test CTest stream; 1133 executed, none skipped"
        status: pass
      - kind: unit
        ref: "tests/scripts/test-cgb-corpus-report.py: TestList, captured output, omission, duplication, stale identity controls"
        status: pass
      - kind: other
        ref: "python3 -I tests/scripts/verify-cgb-corpus-inventory.py --ci-contract"
        status: pass
    human_judgment: false
  - id: D2
    description: "Inventory binding checks and pinned reproduction paths preserve exact selection, rights, output digests, and tamper rejection."
    requirement: CGB-08
    verification:
      - kind: unit
        ref: "python3 -I tests/scripts/verify-cgb-corpus-inventory.py --bindings"
        status: pass
      - kind: unit
        ref: "python3 -I tests/scripts/verify-cgb-corpus-inventory.py --self-test; verifies strict --complete rejection for magentests:bg_oam_priority"
        status: pass
      - kind: integration
        ref: "AGE, SameSuite, and Mooneye CGB pinned reproduction commands and their tamper controls"
        status: pass
    human_judgment: false
  - id: D3
    description: "Relocated C and C++ consumers and package smoke remain valid, and corpus ROM/reference bytes stay outside installed packages."
    requirement: CGB-10
    verification:
      - kind: integration
        ref: "Full CTest stream: installed_consumer_c, installed_consumer_cpp, installed_consumer_phase2_c, installed_consumer_phase2_cpp, preview_package_smoke"
        status: pass
      - kind: unit
        ref: "cgb_corpus_not_installed_controls: renamed ROM and renamed AGE PNG rejected by digest"
        status: pass
      - kind: unit
        ref: "cgb_consumer_symbol_coverage and cgb_hdma_claims_contract_native"
        status: pass
    human_judgment: false
  - id: D4
    description: "Native integration documentation limits audio observations to guest digital registers and states physical and analog exclusions."
    requirement: CGB-10
    verification:
      - kind: unit
        ref: "cgb_hdma_claims_contract_native scans native-integration.md for FF76/FF77 and explicit analog/physical limits"
        status: pass
    human_judgment: false
  - id: D5
    description: "Native CI uses one nonce-specific JUnit path for receipt, required inventory, and DMG checks, and publishes only privacy-safe corpus evidence."
    requirement: CGB-08
    verification:
      - kind: unit
        ref: "cgb_corpus_ci_contract and inventory self-tests reject stale JUnit consumers, raw XML uploads, and a missing hashed build target"
        status: pass
      - kind: integration
        ref: "python3 -I tests/scripts/verify-cgb-corpus-artifacts.py --check --build-dir build: 3 privacy-safe JSON payloads; raw Test.xml and JUnit excluded"
        status: pass
      - kind: unit
        ref: "python3 -I tests/scripts/verify-cgb-corpus-artifacts.py --self-test rejects host paths in Test.xml and JUnit"
        status: pass
      - kind: integration
        ref: "Clean Ninja build and covered-input rebuild proved stamp ordering; cgb_corpus_report_tracer rejected a stale runner and passed after fresh configure/build"
        status: pass
    human_judgment: false
duration: 68min
completed: 2026-10-15
status: complete
---

# Phase 14 Plan 12: CGB corpus and consumer closure

**A build-identity-bound 107-case receipt comes from one committed-head CTest stream, with exact nonce consumers, privacy-safe CI evidence, pinned reproduction, and package-exclusion controls.**

## Performance

- **Duration:** About 68 minutes from the earliest recorded plan commit, the Task 1 RED test (`fb85ec8`); executor setup preceded that timestamp.
- **Started:** 2026-10-15T19:13:34-04:00, earliest saved plan artifact.
- **Completed:** 2026-10-15.
- **Tasks:** 3.
- **Files modified:** 15 including this summary.
- **Full CTest:** 1,133/1,133 passed in 264.61 seconds; the 108 corpus-labeled tests took 11.36 process-seconds.
- **Receipt:** 107/107 terminal corpus cases; 25 observed guest passes and 82 matched expected failures.
- **Measured local costs:** fresh configure 10.6 seconds; final stamp build and tracer check completed successfully; AGE reproduction 1.77 seconds, SameSuite 4.69 seconds, and Mooneye CGB 4.04 seconds.

## Accomplishments

- The native Linux workflow stamps compiled inputs, starts a nonce-bound run, executes the complete CTest stream once, and derives the receipt and required-test inventory from that run's Test.xml and nonce-specific JUnit. Those raw reports remain local because they contain host names and absolute paths. CI publishes only the privacy-checked receipt, build stamp, run metadata, and public artifact manifest. Passing-test output is bounded at 16 MiB per test; the measured APU aggregate was 617,531 bytes for 70 guest records and 4,784 assertion rows.
- The final receipt contains 107/107 completed cases, 25 observed guest passes, 82 matched expected failures, and 2,845/4,959 passing assertion rows. AGE image comparisons retain 18,208 mismatched pixels out of 138,240. These remain software-model results, not hardware qualification.
- Static `--bindings` validates all 181 selected sources, 109 admitted outputs, and 107 case/test bindings. `--complete` continues to reject `complete-case-not-terminal:magentests:bg_oam_priority`; runtime completeness is established by the fresh receipt instead of fabricating a static terminal observation. The full stream omits that case and the receipt rejects incompleteness if any required case is missing.
- Pinned local reproduction was byte-identical for the six AGE PNG references, 74 SameSuite outputs, and nine Mooneye CGB ROMs. Existing tamper checks passed. Workflow syntax and membership were checked offline; no hosted run is claimed.
- Relocated C/C++ consumers and package smoke passed. The new package scan covers all four manifests and AGE reference PNG hashes; renamed ROM and PNG controls prove the scanner rejects identical fixture bytes independently of filename. The native guide documents guest-only FF76/FF77 samples and the unqualified physical and analog audio boundary.
- Native-linux's DMG JUnit check now consumes the same exact nonce file as the receipt and required-inventory check. Offline CI contracts reject the stale fixed filename, raw XML uploads, and removal of any hashed executable from stamp target dependencies. A clean Ninja build and a covered-source change/rebuild proved the already-existing target ordering produces current build identities.
- The artifact privacy checker passed on the actual upload payload (three JSON evidence files, 1,488,355 bytes) and its negative controls reject host paths in both raw Test.xml and JUnit. The manifest is generated from the safe allowlist; the local raw-report digest claims remain intact.

## Task Commits

1. **Task 1: Native CTest receipt** — RED `fb85ec8`; implementation `82a0dd5`.
2. **Task 2: Sanitizer and pinned reproduction contracts** — `5a9c8ae`.
3. **Task 3: Installed consumer and package boundary** — `6aa0609`.

The real CTest XML format exposed parser defects during full-stream validation. Regression/fix pairs were committed as `da8c201`/`ffa2c96` for TestList records, `b4c6baa`/`a8f2dfa` for unnamed captured output, and `591a189`/`9086e1d` for missing or duplicate output measurements. The final privacy and CI-consumer fixes are in `019cb00`. The plan commit count of 12 is measured from `plan_head_before` to `plan_head_after` above.

## Files Created/Modified

- `tests/scripts/verify-cgb-corpus-report.py` and `tests/scripts/verify-cgb-corpus-inventory.py` — build identity, receipt parsing, exact bindings, and offline CI contracts.
- `tests/scripts/verify-cgb-corpus-artifacts.py` — allowlisted public artifact scan with host-path rejection controls.
- `.github/workflows/ci.yml` and `.github/workflows/fixture-repro.yml` — same-stream receipt and existing pinned reproduction coverage.
- `tests/CMakeLists.txt`, `tests/expected-tests.txt`, and `tests/CheckCgbCorpusPackageControls.cmake` — required tests and renamed fixture controls.
- `cmake/ScanForbiddenFixtures.cmake` — digest scanning for ROMs and AGE reference PNGs.
- `docs/cgb-corpus.md` and `docs/native-integration.md` — receipt limits, observed counts, and audio boundary.

## Decisions Made

- `--bindings` is the static selection/admission/output/test contract. `--complete` retains its requirement for terminal observed evidence; the exact Magen case rejection is preserved as a negative control. The runtime receipt is the completeness source for the fresh execution.
- CTest's default passing-test output limit would truncate the APU aggregate. The native lane uses the CTest-supported `--test-output-size-passed 16777216` option, and the receipt enforces the same per-test bound. The measured output is well below that limit.
- Build-stamp dependencies cover all seven hashed executables and their input files. The existing target ordering was verified by a clean build and covered-input rebuild; a contract mutant rejects removing a hashed executable dependency.
- The DMG baseline inventory, required-test inventory, and receipt parser all consume the same nonce-specific JUnit produced by the full CTest stream.
- Only the public JSON allowlist is uploaded. Raw Test.xml/JUnit stay in the runner workspace to avoid exposing host identifiers and absolute build paths.

## Deviations from Plan

### Contract correction

**Static terminal status for Magen `bg_oam_priority` is unavailable before execution.** `python3 -I tests/scripts/verify-cgb-corpus-inventory.py --complete` returns the exact diagnostic `complete-case-not-terminal:magentests:bg_oam_priority`. Weakening `--complete` or inventing a static observed disposition would change its contract. The separate `--bindings` check now verifies frozen source/output/test selection and binding truth, while the fresh receipt requires every selected test to have a terminal passing CTest result and every corpus case to have a terminal guest record. The inventory self-test asserts the exact static rejection, and the full receipt verifies 107/107 runtime cases.

### Automatic correctness fixes

**1. CTest TestList paths were mistaken for result records.** The first full CTest run passed 1,132/1,132 tests but receipt parsing returned `ctest-xml-test-identity` because `Test.xml` contains path-only `<Test>` entries alongside status-bearing result records. A RED fixture derived from the actual XML shape and the parser fix now distinguish those records. Commits: `da8c201`, `ffa2c96`.

**2. CTest output measurement was not retained completely.** The next full test run also passed 1,132/1,132 but receipt normalization returned `apu-membership-control`: captured output is stored in an unnamed `<Measurement>`, not `name="Test Output"`, and CTest's default 1 KiB pass-output limit truncates the APU guest output. The native invocation now sets a finite 16 MiB limit; the parser requires exactly one captured output measurement for every selected test and rejects missing or duplicate measurements. The APU stream was measured at 617,531 bytes. Commits: `b4c6baa`, `a8f2dfa`, `591a189`, `9086e1d`.

**3. Task 3 did not receive a pre-implementation RED commit.** The package-boundary implementation and controls were already present when this execution segment resumed, so I did not claim a retroactive RED result. The installed-tree check and known-clean renamed-ROM/renamed-PNG negative controls passed after implementation in the focused 11-test run and the final complete CTest run.

**4. The initial build-stamp dependency set included intentionally excluded ADR mutants.** That caused the first stamp build to compile a deliberately failing mutant target. Dependencies were narrowed to the actual corpus runner and selected test executables; subsequent configure and build completed successfully.

**5. The existing native workflow still used a fixed JUnit path for the final DMG inventory and uploaded raw XML.** Updated the DMG consumer to the run nonce and added offline mutants for the stale path and raw-report upload. Added an allowlist checker and a CI upload contract; actual artifacts passed privacy scanning while synthetic raw XML/JUnit containing host paths were rejected. The existing stamp-target dependency ordering was verified and protected with a missing-target mutant; no redundant dependency was added.

**Total deviations:** 6 documented contract, privacy, and verification adjustments. The receipt/parser fixes add no public API, package, or dependency.

## TDD Gate Compliance

- **Task 1:** RED `fb85ec8` captured the uniquely named native-receipt contract test failing on the intended missing `--begin-run` behavior; GREEN implementation followed in `82a0dd5`.
- **Task 3:** The task was marked `tdd="true"`, but its package scanner and controls were already implemented before this execution segment resumed. No pre-implementation RED evidence exists, so no retroactive RED is claimed. Installed-consumer checks and renamed-ROM/renamed-PNG controls passed afterward.

## Issues Encountered

- Two early full-stream attempts passed all CTests but produced incomplete receipts: one rejected actual TestList path records; the next rejected the unnamed captured-output measurement and the truncated default output. The subsequent parser fixes have explicit regression fixtures.
- A post-commit full stream attempted after `cmake --build` without reconfiguring failed `cgb_corpus_report_tracer`: the binary still embedded the prior configure-time Git revision while the receipt identity saw the new HEAD. A fresh `cmake -S . -B build ...` configure, stamp build, and focused tracer test passed; the final 1,133-test stream then produced the complete committed-head receipt. Hosted CI already configures before building.
- The local CMake configuration reported that the matching Clang libFuzzer runtime was unavailable. Deterministic sanitizer regressions remained enabled; no local ASan/UBSan pass or hosted CI execution is claimed.

## User Setup Required

None.

## Next Phase Readiness

Plan 14-12 is complete. The parent workflow owns the aggregate Phase 14 verification and handoff. Requirements remain open until that phase-level gate is completed; no Phase 15 work or physical CGB-E claim is included here.

---
*Phase: 14-cgb-e-model-qualification-and-corpus*
*Completed: 2026-10-15*

## Self-Check: PASSED

- Summary file exists at the required plan path.
- All twelve measured plan commits are ancestors of the recorded `plan_head_after`.
- `summary_coverage` passes with five entries; all coverage verification items are automated and marked `human_judgment: false`.

## Sanitized ancestry

The top-level commit windows use sanitized unpublished ancestry. Historical execution revision IDs and task IDs above remain as originally recorded; [14-HISTORY-REDACTION.md](14-HISTORY-REDACTION.md) maps them to the equivalent sanitized commits. Fresh final qualification is recorded separately after this rewrite.
