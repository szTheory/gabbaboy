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
  tokens: 12456
  tasks: 3
  commits: 10
plan_head_before: 4ac2120ecf41f8b96e999f2adb89b816bd184123
plan_head_after: 9086e1de4a5e1e520cd3dc2c7dce352989df6d67
commits: 10
tech-stack:
  added: []
  patterns:
    - "Nonce-bound CTest Test.xml and JUnit receipt from one full test stream"
    - "Manifest-hash package exclusion with renamed ROM and PNG controls"
key-files:
  created:
    - tests/CheckCgbCorpusPackageControls.cmake
    - .planning/phases/GB-14-cgb-e-model-qualification-and-corpus/14-12-red-task1.json
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
        ref: "build/cgb-corpus-receipt.json: complete 107/107 cases from 108 selected tests in the 1,132-test stream"
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
duration: 42min
completed: 2026-10-15
status: complete
---

# Phase 14 Plan 12: CGB corpus and consumer closure

**A build-identity-bound 107-case CGB receipt now comes from one full CTest stream, with pinned reproduction and package-exclusion controls.**

## Performance

- **Duration:** About 42 minutes from the earliest recorded plan commit, the Task 1 RED test (`fb85ec8`); executor setup preceded that timestamp.
- **Started:** 2026-10-15T19:13:34-04:00, earliest saved plan artifact.
- **Completed:** 2026-10-15.
- **Tasks:** 3.
- **Files modified:** 14 including this summary.
- **Full CTest:** 1,132/1,132 passed in 317.54 seconds; 108 receipt-selected tests took 15.27 process-seconds.
- **Receipt parser:** Test.xml and nonce-specific JUnit parsing took 0.0399 seconds; inputs were 2,444,978 and 1,027,852 bytes.
- **Measured local costs:** configure 11.2 seconds; prior warm build/stamp 0.86–0.88 seconds; AGE reproduction 1.77 seconds, SameSuite 4.69 seconds, and Mooneye CGB 4.04 seconds.

## Accomplishments

- The native Linux workflow stamps compiled inputs, starts a nonce-bound run, executes the complete CTest stream once, retains Test.xml and JUnit, and derives the receipt from those same results. Passing-test output is bounded at 16 MiB per test; the measured APU aggregate was 617,531 bytes for 70 guest records and 4,784 assertion rows.
- The final receipt contains 107/107 completed cases, 25 observed guest passes, 82 matched expected failures, and 2,845/4,959 passing assertion rows. AGE image comparisons retain 18,208 mismatched pixels out of 138,240. These remain software-model results, not hardware qualification.
- Static `--bindings` validates all 181 selected sources, 109 admitted outputs, and 107 case/test bindings. `--complete` continues to reject `complete-case-not-terminal:magentests:bg_oam_priority`; runtime completeness is established by the fresh receipt instead of fabricating a static terminal observation.
- Pinned local reproduction was byte-identical for the six AGE PNG references, 74 SameSuite outputs, and nine Mooneye CGB ROMs. Existing tamper checks passed. Workflow syntax and membership were checked offline; no hosted run is claimed.
- Relocated C/C++ consumers and package smoke passed. The new package scan covers all four manifests and AGE reference PNG hashes; renamed ROM and PNG controls prove the scanner rejects identical fixture bytes independently of filename. The native guide documents guest-only FF76/FF77 samples and the unqualified physical and analog audio boundary.

## Task Commits

1. **Task 1: Native CTest receipt** — RED `fb85ec8`; implementation `82a0dd5`.
2. **Task 2: Sanitizer and pinned reproduction contracts** — `5a9c8ae`.
3. **Task 3: Installed consumer and package boundary** — `6aa0609`.

The real CTest XML format exposed parser defects during full-stream validation. Regression/fix pairs were committed as `da8c201`/`ffa2c96` for TestList records, `b4c6baa`/`a8f2dfa` for unnamed captured output, and `591a189`/`9086e1d` for missing or duplicate output measurements. The plan commit count of 10 is measured from `plan_head_before` to `plan_head_after` above.

## Files Created/Modified

- `tests/scripts/verify-cgb-corpus-report.py` and `tests/scripts/verify-cgb-corpus-inventory.py` — build identity, receipt parsing, exact bindings, and offline CI contracts.
- `.github/workflows/ci.yml` and `.github/workflows/fixture-repro.yml` — same-stream receipt and existing pinned reproduction coverage.
- `tests/CMakeLists.txt`, `tests/expected-tests.txt`, and `tests/CheckCgbCorpusPackageControls.cmake` — required tests and renamed fixture controls.
- `cmake/ScanForbiddenFixtures.cmake` — digest scanning for ROMs and AGE reference PNGs.
- `docs/cgb-corpus.md` and `docs/native-integration.md` — receipt limits, observed counts, and audio boundary.

## Decisions Made

- `--bindings` is the static selection/admission/output/test contract. `--complete` retains its requirement for terminal observed evidence; the exact Magen case rejection is preserved as a negative control. The runtime receipt is the completeness source for the fresh execution.
- CTest's default passing-test output limit would truncate the APU aggregate. The native lane uses the CTest-supported `--test-output-size-passed 16777216` option, and the receipt enforces the same per-test bound. The measured output is well below that limit.
- Build-stamp dependencies cover the actual corpus executables and their input files; unrelated intentionally failing ADR mutant targets are excluded from the stamp build dependency set.

## Deviations from Plan

### Contract correction

**Static terminal status for Magen `bg_oam_priority` is unavailable before execution.** `python3 -I tests/scripts/verify-cgb-corpus-inventory.py --complete` returns the exact diagnostic `complete-case-not-terminal:magentests:bg_oam_priority`. Weakening `--complete` or inventing a static observed disposition would change its contract. The separate `--bindings` check now verifies frozen source/output/test selection and binding truth, while the fresh receipt requires every selected test to have a terminal passing CTest result and every corpus case to have a terminal guest record. The inventory self-test asserts the exact static rejection, and the full receipt verifies 107/107 runtime cases.

### Automatic correctness fixes

**1. CTest TestList paths were mistaken for result records.** The first full CTest run passed 1,132/1,132 tests but receipt parsing returned `ctest-xml-test-identity` because `Test.xml` contains path-only `<Test>` entries alongside status-bearing result records. A RED fixture derived from the actual XML shape and the parser fix now distinguish those records. Commits: `da8c201`, `ffa2c96`.

**2. CTest output measurement was not retained completely.** The next full test run also passed 1,132/1,132 but receipt normalization returned `apu-membership-control`: captured output is stored in an unnamed `<Measurement>`, not `name="Test Output"`, and CTest's default 1 KiB pass-output limit truncates the APU guest output. The native invocation now sets a finite 16 MiB limit; the parser requires exactly one captured output measurement for every selected test and rejects missing or duplicate measurements. The APU stream was measured at 617,531 bytes. Commits: `b4c6baa`, `a8f2dfa`, `591a189`, `9086e1d`.

**3. Task 3 did not receive a pre-implementation RED commit.** The package-boundary implementation and controls were already present when this execution segment resumed, so I did not claim a retroactive RED result. The installed-tree check and known-clean renamed-ROM/renamed-PNG negative controls passed after implementation in the focused 11-test run and the final complete CTest run.

**4. The initial build-stamp dependency set included intentionally excluded ADR mutants.** That caused the first stamp build to compile a deliberately failing mutant target. Dependencies were narrowed to the actual corpus runner and selected test executables; subsequent configure and build completed successfully.

**Total deviations:** 4 documented contract/correctness adjustments. The receipt/parser fixes add no public API, package, or dependency.

## Issues Encountered

- The two early full-stream attempts had complete passing CTest results but incomplete receipts, for the parser reasons described above. A third fresh nonce-bound stream produced the complete receipt and passed the independent required-test inventory check.
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
- All ten measured plan commits are ancestors of the recorded `plan_head_after`.
- `summary_coverage` passes with four entries; the installed GSD coverage classifier reports all four auto-covered.
