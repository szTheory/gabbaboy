---
phase: GB-02-dmg-cpu-bus-and-time
plan: 09
subsystem: api-installation-and-ci
tags: [public-api, installed-consumers, junit-inventory, fixture-reproduction]
requires:
  - phase: GB-02-dmg-cpu-bus-and-time/02-08
    provides: timestamped event and diagnostic APIs plus strict CPU/timer runner
provides:
  - C and C++ installed consumers exercising timestamped input and diagnostics
  - Fresh relocated-install and independent core-only JUnit inventory verification
  - Offline required CI inventory and manually triggered pinned fixture reproduction
affects: [GB-02-verification, phase-3-planning]
tech-stack:
  added: []
  patterns: [populated-prefix relocation, exact CTest JUnit inventories, pinned manual fixture regeneration]
key-files:
  created: [tests/scripts/verify-phase2-installed.sh]
  modified: [README.md, include/gabbaboy/gabbaboy.h, tests/consumers/c/main.c, tests/consumers/cpp/main.cpp, tests/CMakeLists.txt, tests/expected-tests.txt, cmake/ExpectedTests.cmake, .github/workflows/ci.yml, .github/workflows/fixture-repro.yml]
key-decisions:
  - "Installed C and C++ consumers exercise the fixed input queue, atomic capacity failure, bounded run result, trace, WRAM marker, and caller-owned chronological diagnostics."
  - "The fixture reproduction lane is manual-only and fetches immutable WLA-DX and Mooneye revisions; routine test runs use checked-in ROM bytes offline."
metrics:
  duration: 8 min
  completed: 2026-10-06
  tasks: 2
  files: 10
  commits: 2
  plan_head_before: c263c536de8ed4e6721f25f182ab076256a462c4
  plan_head_after: da876a654a3306e44794b2cec7e90b3bb607bee9
actuals:
  tokens: 6470
  tasks: 2
  commits: 2
requirements-completed: []
coverage:
  - id: D-12
    description: "Installed C/C++ consumers use only the exported public header and timestamped APIs."
    verification:
      - kind: integration
        ref: "fresh relocated install; installed_consumer_phase2_c and installed_consumer_phase2_cpp"
        status: pass
    human_judgment: false
  - id: D-09
    description: "Required tests execute the fixed offline CPU/timer corpus and reject missing, skipped, or unexpected cases."
    verification:
      - kind: integration
        ref: "core-only JUnit 87/87 and relocated installed JUnit 92/92; exact expected-test comparison"
        status: pass
    human_judgment: false
  - id: D-11
    description: "Documentation reports scoped DMG evidence and fixture receipts without asserting physical-hardware or general-game compatibility."
    verification:
      - kind: review
        ref: "README and public header contract review; strict suite receipt identifies matching final core/runner SHA"
        status: pass
    human_judgment: false
status: complete
---

# Phase 2 Plan 09: Installed Consumers, CI, and API Contract Summary

**The timestamped API now has relocated C/C++ consumer coverage, fresh exact JUnit inventories, and documented evidence limits with offline required tests.**

## Accomplishments

- Expanded the installed public header contract for absolute event timestamps, the fixed 64-event queue, atomic admission, equal-time ordering, consumed-event capacity, caller-owned diagnostics, and distinct bounded stop outcomes.
- Updated both independent C and C++ consumers to queue timestamped input, check the queue-full result without partial admission, call `gbb_run_ex`, verify chronological diagnostics and bounded trace output, and assert the tracer's WRAM marker using only the installed package.
- Registered `installed_consumer_phase2_c` and `installed_consumer_phase2_cpp` only when an installed prefix exists. Updated the exact expected inventory and its absent-prefix filter.
- Added `tests/scripts/verify-phase2-installed.sh`. It clears the normal build's install-prefix cache, installs into a populated prefix, renames that package, and uses independent fresh build trees for the relocated installed inventory and the core-only inventory.
- Updated the README to describe the implemented bootless DMG-CPU-B CPU, bus, timer, serial, timestamped-input, and diagnostic contracts, the fixed three-case CPU/timer denominator, the legacy A000 tracer limitation, and the difference between scoped emulator results and hardware/game compatibility claims.
- Kept ordinary CI offline and exact. The sanitizer configuration explicitly clears a cached install prefix. Converted fixture reproduction to `workflow_dispatch`, pinned both WLA-DX and Mooneye source revisions, verified the WLA archive and replacement font digests, and regenerated/compared each eligible ROM.

## Task Commits

1. **Run timestamped input through both installed consumers** — `02af8f0`.
2. **Require the complete CPU/timer corpus and document limits** — `da876a6`.

The persisted commit ledger measures two task commits from `c263c536de8ed4e6721f25f182ab076256a462c4` through `da876a654a3306e44794b2cec7e90b3bb607bee9`. The summary and state metadata commit are outside that range.

## Verification Evidence and Limits

- The final local core-only CTest report passed **87/87** with no skips and exactly matched `tests/expected-tests.txt` after filtering installed tests.
- The populated relocated-package report passed **92/92** with no skips and matched the installed inventory. The two Phase 2 C/C++ consumers were present there and absent from the independent core-only report.
- All three eligible Mooneye cases passed from the final task revision. Each receipt reported `core_revision=da876a654a3306e44794b2cec7e90b3bb607bee9`, the same runner revision, `build_qualified=true`, and the fixed `eligible=3 executed=3 status=pass` denominator.
- Locally fetched Mooneye commit `31510e12eea6286d36eea060a6adde755e1067aa` and WLA-DX commit `91c52b1f4ef3cc8ba3c0638f7536539579af6a9f`. The WLA source archive matched its recorded SHA-256; the built tools reported the manifest versions; the generated replacement font matched its digest; all three regenerated ROMs were byte-identical to checked-in files and matched their manifest hashes.
- Both workflow YAML files parsed with `yq` 4.53.2 and `git diff --check` passed. `actionlint` was unavailable.
- The ASan/UBSan workflow could not run on this macOS host; the project intentionally supports that preset only on Linux. Its hosted result remains pending.
- No hosted Actions result or exact-reviewed-PR-SHA evidence was obtained here. The local pass is not remote green. No physical DMG run was performed.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking issue] Fetch the pinned Mooneye sources as well as the WLA-DX builder.**
- **Found during:** Task 2
- **Issue:** WLA-DX provides the assembler and linker but not the source files for the eligible fixture ROMs; the original workflow only reproduced the Phase 1 tracer with RGBDS.
- **Fix:** The manual workflow now fetches the exact Mooneye source commit separately, generates the documented original replacement font into its source tree, builds the pinned WLA-DX tools, and compares regenerated bytes and manifest digests.
- **Files modified:** `.github/workflows/fixture-repro.yml`
- **Verification:** The same two pinned repositories and regeneration steps passed locally for DAA and both timer fixtures.
- **Commit:** `da876a6`.

**Total deviations:** 1 auto-fixed (Rule 3: 1). **Impact:** The manual fixture lane now reproduces the actual Phase 2 diagnostic ROMs while retaining their reviewed source and asset pins.

## Deferred Issues

- CPU-01 through CPU-05 remain unchecked in requirement traceability until independent Phase 2 goal-backward verification.
- Hosted native, sanitizer, and exact-reviewed-SHA results remain pending; branch protection is not inferred from local configuration.
- Physical DMG-CPU-B validation remains unavailable and is not implied by Mooneye author claims or emulator results.

## Next Phase Readiness

Phase GB-02 Plan 02-09 execution is complete; **Phase 2 remains pending independent verification**. The next implementation phase is **Phase 3 — Visible Interactive DMG**, gated on that verification and owner direction. The immediate next command is `$gsd-verify-work 2`. If execution is interrupted before the Plan 02-09 closeout is found on disk, resume this phase with `$gsd-execute-phase 2`; do not begin Phase 3 automatically. `workflow.auto_advance` and `workflow._auto_chain_active` remain false.

---
*Phase: GB-02-dmg-cpu-bus-and-time*
*Plan: 09*
*Completed: 2026-10-06*

## Self-Check: PASSED

- Both task commits are ancestors of the measured plan head.
- The installed-consumer helper and all recorded implementation files exist.
- The full core-only and relocated installed inventories passed at the final task SHA; the strict suite receipts carry the same SHA.
- The manual fixture reproduction reproduced all three checked-in ROMs and their recorded digests.
- No unfinished implementation stub was introduced by this plan.
