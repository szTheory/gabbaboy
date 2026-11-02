---
phase: GB-21-cgb-game-progress-and-scene-regressions
plan: "01"
subsystem: testing
tags: [CGB, acceptance-runner, RGB555, source-pinned-rom]
requires: []
provides:
  - Source-bound native-CGB progress tracer using a generated original ROM and scripted RIGHT input
  - API-reported CGB execution-mode gate and compatibility-mode refusal control
  - CGB-specific RGB555 and PCM observations while retaining the Libbet DMG baseline
affects: [GB-21-02, CGB acceptance, game progress evidence]
tech-stack:
  added: []
  patterns:
    - Generated original ROMs stay in private temporary test directories and are pinned by digest and source anchors
    - Acceptance evidence checks the loaded execution mode and separates observation policy by predicate
key-files:
  created:
    - tests/scripts/verify-cgb-progress.py
  modified:
    - src/accept/gbb_accept.h
    - src/accept/predicate.c
    - src/runner/acceptance.c
    - tests/acceptance/CMakeLists.txt
    - tests/expected-tests.txt
key-decisions:
  - "The compatibility refusal control derives a valid compatibility-header variant from the same authored ROM so the loaded API mode is independently observable."
metrics:
  duration: 16min
  completed: 2026-11-02
status: complete
actuals:
  tokens: 14514
  tasks: 2
  commits: 6
commits: 6
plan_head_before: bf2e2b76dbde462d24773dbe06ec05584c143fb5
plan_head_after: 7e345595ecc3d1e0bdb075d0a31c34b895389930
requirements-completed: [GAME-01, GAME-02]
coverage:
  - id: D1
    description: The actual runner accepts source-bound native-CGB guest progress and emits CGB RGB555 and PCM observations; no-input and impossible-predicate controls fail.
    requirement: GAME-01
    verification:
      - kind: integration
        ref: "ctest --preset phase1 --output-on-failure --no-tests=error -R '^(acceptance_cgb_progress_tracer|cgb_runner_profile_dmg_identity_acceptance|dmg_baseline)$'"
        status: pass
    human_judgment: false
  - id: D2
    description: Loaded compatibility mode is refused explicitly, and the exact ROM, script, predicate, profile, execution mode, and observations are bound in source-qualified evidence.
    requirement: GAME-02
    verification:
      - kind: integration
        ref: "ctest --preset phase1 --output-on-failure --no-tests=error -R '^(acceptance_cgb_progress_tracer|acceptance_cgb_progress_compat_rejected|cgb_runner_profile_dmg_identity_acceptance|dmg_baseline)$'"
        status: pass
      - kind: other
        ref: "python3 -I tests/scripts/verify-cgb-progress.py --self-test --repo-root ."
        status: pass
    human_judgment: false
---

# Phase 21 Plan 01: Native CGB Progress Tracer Summary

**A generated original CGB ROM now proves input-driven guest progress through the real runner with source-bound RGB555 and PCM evidence.**

## Performance

- **Duration:** 16 minutes
- **Started:** 2026-11-02T01:49:53Z
- **Completed:** 2026-11-02T02:06:09Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments

- Added a deterministic, 32-KiB original native-CGB control ROM generated in a private temporary directory. A scripted RIGHT press changes source-derived WRAM progress and the displayed palette from blue to green; a no-input route and impossible predicate remain negative controls.
- The real acceptance runner checks `gbb_get_info` after load, requires native CGB mode, captures bounded RGB555 frames and PCM observations, and records mode/profile/checkpoint evidence. A source-qualified compatibility control is rejected with exit 3 before guest execution.
- Preserved the existing Libbet DMG policy and frozen baseline. The explicit/default profile identity pair and DMG baseline passed.

## TDD Gate Compliance

- **Task 1 RED:** The test-only tracer commit `3e19a388` preceded implementation. The real runner rejected the positive route with exit 2 and `reason=predicate-not-bound`; CTest failed on the intended positive tracer assertion. This was an attributable missing-predicate failure, not a setup or discovery failure.
- **Task 1 GREEN:** The predicate registry, observation policy, loaded-mode check, and RGB555/PCM runner path made the positive route pass while no-input and impossible-predicate controls returned `predicate-not-reached`.
- **Task 2:** The initial compatibility assumption was disproved by the checked-in Libbet header, which declares native CGB. The corrected control uses a checksum-valid compatibility header variant of the same authored program and verifies the API-reported `cgb-dmg-compat` refusal. The checker self-test and focused integration suite pass.
- **Refactor:** No separate refactor commit was needed.

## Source-Qualified Evidence

The final checker run used source revision `7e345595ecc3d1e0bdb075d0a31c34b895389930`, checker SHA-256 `76da129c1def1a9955426a635ef46a8845855085c2d0119b192510c4c2a09835`, and runner SHA-256 `1dd06ba75715ad9ec1473c3f3d10746b32f5b8c0947c7f6750a67967db52491c`.

- Native CGB ROM SHA-256: `17822873ec8641280d9504229d96850414e872bc90de5431469a498e5271db7e`
- Compatibility-header control SHA-256: `6a1d4a1ed58e8a51f3a5be1283a2226775867fc1373b628ecbc798d12d3ca5fc`
- Positive input script SHA-256: `0ccfce12e082a0d6bf52ee6a0867b62beb096f5b9403d715e0c5b354c3b14fc2`
- Native tracer result: positive pass; no-input and impossible predicate both `predicate-not-reached`.
- Compatibility result: `actual=cgb-dmg-compat`, refused before driving the guest.
- The receipt validator checks CGB profile/mode, RGB555 frame format, named checkpoint digests/times, and PCM sample count.

## Checks Run

- `cmake --preset phase1` and `cmake --build --preset phase1` passed.
- `python3 -I tests/scripts/verify-cgb-progress.py --self-test --repo-root .` passed its source-revision, ROM-identity, script-identity, anchor, and native-mode-receipt controls.
- Focused CTest selection passed all five tests: `dmg_baseline`, `cgb_runner_profile_dmg_identity_acceptance`, `acceptance_cgb_progress_tracer`, `acceptance_cgb_progress_compat_rejected`, and the retained `acceptance_cgb_colour_progress_refused` case.
- No full-suite run was part of this plan; full-suite qualification remains assigned to Phase 21 Plan 21-07.

## Task Commits

1. **Task 1 RED: native-CGB progress tracer** — `3e19a388` (`test`)
2. **Task 1 checker identity controls** — `c4ff0dd2` (`test`)
3. **Task 1 RGB555 digest assertions** — `b1c11a35` (`test`)
4. **Task 1 runner and predicate implementation** — `3ea7aef6` (`feat`)
5. **Task 2 compatibility-mode control** — `88c2b6eb` (`test`)
6. **Compatibility control case-path correction** — `7e345595` (`fix`)

## Files Created/Modified

- `tests/scripts/verify-cgb-progress.py` — Generates both original control ROMs, drives the actual runner, checks negative controls, and verifies committed source identity.
- `src/accept/gbb_accept.h`, `src/accept/predicate.c` — Adds immutable CGB predicate evaluators, source anchors, and explicit observation policy metadata.
- `src/runner/acceptance.c` — Adds bounded RGB555 capture, native-mode gating, CGB observations, and mode-aware receipts.
- `tests/acceptance/CMakeLists.txt`, `tests/expected-tests.txt` — Registers the tracer and compatibility control and retains the corrected historical Libbet outcome.

## Decisions Made

The plan's Libbet-based compatibility control was replaced with a generated compatibility-header variant of the authored test ROM. The checked-in Libbet image has header flag `0x80`, and the loaded API correctly reports native CGB mode for it; the generated variant isolates the compatibility refusal while retaining identical program bytes and source anchors.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking test correction] Use a true compatibility-mode image for the refusal control**
- **Found during:** Task 2
- **Issue:** The plan's existing Libbet case declares native CGB in its header, so it cannot exercise the expected compatibility-mode refusal.
- **Fix:** Derived a checksum-valid compatibility-header variant of the authored ROM, pinned its digest, registered a matching predicate, and updated the historical Libbet case expectation to its actual `predicate-not-reached` result while retaining the case.
- **Files modified:** `src/accept/predicate.c`, `tests/scripts/verify-cgb-progress.py`, `tests/acceptance/CMakeLists.txt`, `tests/expected-tests.txt`
- **Verification:** Compatibility control reports `actual=cgb-dmg-compat` and exits 3; the retained Libbet case, profile identity pair, and DMG baseline pass.
- **Committed in:** `88c2b6eb` and `7e345595`

**2. [Rule 1 - Bug] Write the compatibility ROM using the case file's pinned path**
- **Found during:** Task 2 verification
- **Issue:** Shared case-file generation names `control.gb`, while the compatibility helper initially wrote `compat.gb`, causing `rom-missing` before the mode assertion.
- **Fix:** Write the compatibility image as `control.gb` in its private temporary directory.
- **Files modified:** `tests/scripts/verify-cgb-progress.py`
- **Verification:** The compatibility CTest and direct source-qualified checker invocation pass.
- **Committed in:** `7e345595`

**Total deviations:** 2 auto-fixed. **Impact:** Both corrections make the planned mode gate test the loaded API state; no product scope or external game evidence was added.

## Issues Encountered

The compatibility test initially failed because its planned Libbet fixture was not a compatibility-mode image. A subsequent checker run caught the temporary case path mismatch. Both issues were corrected and the final focused suite passed.

## Known Stubs

None.

## Threat Flags

None. The work adds no public endpoint, new trust boundary, or persistent ROM payload; the test controls are generated in private temporary directories, and the runner's receipt binds the loaded mode and observations.

## User Setup Required

None.

## Next Phase Readiness

Plan 21-01 is complete. The original-harness control is explicitly harness-only and makes no claim about rendering accuracy, physical hardware behavior, or commercial-game compatibility. Phase 21 remains in progress; Plan 21-02 is the next planned slice and requires its own dispatch.

---
*Phase: GB-21-cgb-game-progress-and-scene-regressions*
*Completed: 2026-11-02*

## Self-Check: PASSED

- All six implementation files and this summary exist.
- All six task commits are ancestors of the current plan head.
