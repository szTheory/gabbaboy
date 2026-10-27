---
phase: GB-17-native-save-state-core
plan: "06"
subsystem: testing
tags: [C, save-state, canonical-bytes, fuzzing, CTest, GitHub-Actions]
requires:
  - phase: GB-17-native-save-state-core
    provides: [versioned state codec, transactional loading, snapshot-fork evidence]
provides:
  - Compiled canonical state pins for DMG, CGB compatibility, and CGB native fixtures
  - A semantic state-load fuzz target with bounded hostile inputs, whole-instance refusal checks, and accepted-load closure
  - An immutable-base compatibility ratchet and source/build/fixture-bound native CI receipts
affects: [GB-17-native-save-state-core, GB-18-player-save-slots]
actuals:
  tokens: 31859
  tasks: 3
  commits: 6
tech-stack:
  added: []
  patterns: [compiled-byte pin emission, immutable-base compatibility dispositions, semantic fuzz witnesses, path-free platform receipts]
key-files:
  created:
    - tests/baseline/state-goldens-v1.json
    - tests/data/state-compatibility.json
    - tests/scripts/verify-state-pins.py
  modified:
    - src/core/gabbaboy.c
    - tests/test_state_codec.c
    - tests/fuzz_core.c
    - tests/scripts/verify-v02-fuzz.py
    - tests/CMakeLists.txt
    - tests/expected-tests.txt
    - .github/workflows/ci.yml
    - .github/scripts/verify-workflow-policy.py
    - docs/state-format.md
key-decisions:
  - "Keep source/build/platform identity outside the portable state bytes and compare compiled output with exact committed fixture pins."
  - "Bind native jobs to pull_request.base.sha or the nonzero push event.before; only an all-zero new-branch push may use merge-base with origin/main."
  - "Record the first 0.2.1 baseline as a delegated phase decision, including absent pre-state tokens as null and no arbitrary unreleased-build interoperability claim."
  - "Treat byte pins as regression evidence, not proof of semantic equivalence; preserve the STATE-05 unclassified edge."
patterns-established:
  - "State-load fuzz controls compare exact opaque instance bytes and the complete owned battery image; an observer-only mutant must be detected while an accepted-load control passes."
  - "Native pin receipts contain only immutable revisions, digest identities, fixture descriptors, and a platform label; they do not contain host paths."
requirements-completed: [STATE-01, STATE-02, STATE-03, STATE-05]
coverage:
  - id: D1
    description: "The compiled codec emits exact canonical bytes for all pinned hardware-mode fixtures, and an altered output or undisposed compatibility change is rejected."
    requirement: STATE-01
    verification:
      - kind: integration
        ref: "CTest state_portable_pins and state_pin_controls at source fdf7b2ac91d5db24f77725cc87588d3c57e26eb7, checked against immutable mainline base 5ca03b394f2a3e0640f69d94e5eda5622753b36c and Phase 17 entry base f192100c4cc89427575f32785a4221bfca7337d7; both selections passed 2/2."
        status: pass
      - kind: unit
        ref: "verify-state-pins.py --self-test at immutable source fdf7b2ac91d5db24f77725cc87588d3c57e26eb7; 14 compatibility, altered-pin, receipt, and immutable-revision controls passed."
        status: pass
    human_judgment: false
  - id: D2
    description: "The real fuzz dispatcher reaches semantic invalid-state checks, whole-instance refusal, and accepted-state resave/closure with named witnesses."
    requirement: STATE-02
    verification:
      - kind: integration
        ref: "CTest state_load_fuzz and state_fuzz_controls at immutable source 0521a33d483211725118f1b117b8e1df371ddb94; 2/2 passed."
        status: pass
      - kind: other
        ref: "The observer-only mutant command exited 1 with `refused state load changed opaque instance bytes or excluded observers`; its unrelated state_control accepted-state-closure control exited 0."
        status: pass
      - kind: unit
        ref: "run-bounded-fuzz.sh --self-test passed; local Clang libFuzzer runtime was unavailable, so the live campaign remains hosted-required."
        status: pass
    human_judgment: false
  - id: D3
    description: "Existing Linux, macOS, and Windows native jobs require immutable event-base pin checks, retain platform receipts, and keep the installed consumer route."
    requirement: STATE-05
    verification:
      - kind: integration
        ref: "verify-workflow-policy.py --check passed and --self-test passed at immutable source fdf7b2ac91d5db24f77725cc87588d3c57e26eb7 with 271 negative and 4 positive controls, including missing OS, own-source base, event.before bypass, ignored pin target, and dropped installed inventory gate."
        status: pass
      - kind: integration
        ref: "Local compiled pin checks against both immutable bases passed and wrote three-fixture receipts; these single-host runs do not qualify cross-platform equality."
        status: pass
    human_judgment: false
  - id: D4
    description: "Relocated installed C/C++ consumers and the preview package smoke continue to execute beside the state pin test."
    requirement: STATE-03
    verification:
      - kind: integration
        ref: "CTest preview_package_smoke, installed_consumer_c, installed_consumer_cpp, and state_portable_pins at immutable source fdf7b2ac91d5db24f77725cc87588d3c57e26eb7; 4/4 passed after install."
        status: pass
    human_judgment: false
commits: 6
plan_head_before: f192100c4cc89427575f32785a4221bfca7337d7
plan_head_after: fdf7b2ac91d5db24f77725cc87588d3c57e26eb7
duration: 1h
completed: 2026-10-26
status: complete
---

# Phase GB-17 Plan 06: Native Save State Core Summary

**Compiled state pins, semantic hostile-load fuzzing, and immutable-base CI receipts now guard portable save-state bytes without claiming semantic equivalence from hashes alone.**

## Performance

- **Duration:** About 1 hour; the first recorded task commit was at 22:08 local time and final local verification completed around 22:52.
- **Tasks:** 3
- **Files modified:** 13, measured from the persisted Plan 17-06 ledger base.
- **Commits:** 6, measured from f192100 through implementation head fdf7b2a.
- **Actual token estimate:** 31,859 chars/4 from the zero-context realized diff; the plan estimated 58,000 on the same scale.

## Accomplishments

- Added deterministic compiled pins for DMG ROM-only, CGB compatibility MBC3/RTC, and native CGB MBC5 fixtures. The immutable-source checker binds release, format, behavior, fixture, ROM, state-byte, source-input, and executable identities.
- Added the actual semantic state-load fuzz dispatcher path. Bounded inputs exercise header corruption, late semantic rejection, premature apply, cap and timer sentinels, signed audio, event ordering, RTC/palette state, and accepted load/resave closure. Refusal compares the complete opaque instance plus the full owned battery image.
- Added a private bounded snapshot seam because canonical serialization omits observer counters and pointers. The new fuzz-path mutant changes only the local no-rumble observer; the exact discrepancy is rejected and an unrelated accepted-state control passes.
- Updated the existing Linux, macOS, and Windows jobs to use immutable pull-request or push event bases and retain path-free, run-scoped pin receipts. The policy checker covers all three jobs, their state target, the receipt artifacts, and the installed C/C++/preview consumer path.
- Recorded two explicit initial no-pin bases. Mainline `5ca03b3` has application release 0.2.1 but no state format/behavior declarations; the Phase 17 entry `f192100` has format/behavior 1/1 but no pins. The delegated decision adds initial pins without promising interoperability among arbitrary unreleased commits.

## Verification

- `cmake --preset phase1 -DGBB_STATE_PIN_BASE_REV=5ca03b394f2a3e0640f69d94e5eda5622753b36c && cmake --build --preset phase1` — passed at source `fdf7b2ac91d5db24f77725cc87588d3c57e26eb7`.
- `state_portable_pins` and `state_pin_controls` against base `5ca03b394f2a3e0640f69d94e5eda5622753b36c` — 2/2 passed; the path-free receipt named source `fdf7b2a`, the exact base, three fixtures, and golden digest `ab3ef83a47e33005218fe2f2b9acb3150c16caf972800c6babb82aa2263b06b1`.
- The same pin/control tests against base `f192100c4cc89427575f32785a4221bfca7337d7` — 2/2 passed with the same source, three fixture identities, and golden digest.
- Installed package verification after `cmake --install build` — `preview_package_smoke`, `installed_consumer_c`, `installed_consumer_cpp`, and `state_portable_pins` passed 4/4.
- `python3 -I .github/scripts/verify-workflow-policy.py --check` — passed. `--self-test` — passed 271 negative and 4 positive controls, including the five state-specific wiring mutations.
- `python3 -I tests/scripts/verify-state-pins.py --self-test` — 14 controls passed. Task 2 `state_load_fuzz` and `state_fuzz_controls` — 2/2 passed; `run-bounded-fuzz.sh --self-test` passed with the local runtime reported as unsupported.
- `ctest --test-dir build -R '^summary_coverage$' --output-on-failure --no-tests=error` — passed 1/1 for this summary's block-schema coverage.
- The prior full settled-suite result, 1473/1473 at f192100, is baseline evidence only and was not rerun for this plan. Full post-wave and hosted checks remain with the parent executor.

## TDD Gate Compliance

- **Task 1 RED:** The altered compiled pin was rejected with a digest mismatch after the emitter schema had a positive compiled control; the unrelated codec matrix remained passing. The regression and implementation were committed separately, followed by a schema correction.
- **Task 2 RED:** The immutable-source observer-only mutant caused the new whole-instance oracle to fail with the named byte discrepancy while the unrelated accepted-load control passed. The unmutated semantic target and its closure/refusal controls then passed.
- **GREEN:** The two exact immutable-base checks, receipt controls, semantic fuzz selection, workflow-policy controls, and installed consumer selection pass as recorded above.
- **REFACTOR:** The workflow-policy budget mutation anchor was narrowed after adding the earlier state-base step, so its original negative control still judges the intended budget-base fallback.

## Task Commits

1. **Task 1: Compiled canonical pins and compatibility ratchet** — `89640f0` (RED), `24d658f` (feature), `c7c6b1b` (emitter-schema fix).
2. **Task 2: Semantic state-load fuzzing** — `57e6a38` (plan registry/deviation record), `0521a33` (feature).
3. **Task 3: Native platform wiring and initial compatibility dispositions** — `fdf7b2a` (feature).

## Decisions Made

- Portable bytes contain no host/platform/source identity. Receipts carry those identities separately.
- A local receipt from one host does not qualify Linux, macOS, and Windows together. Same-head hosted results are required before cross-platform qualification.
- State byte equality remains a regression pin. It does not establish semantic equivalence for unclassified state behavior.

## Deviations from Plan

### Owner-authorized correctness and evidence refinements

1. **Task 2 private snapshot seam:** The earlier canonical and selected-field seams could not prove refusal left local observers and pointer identity untouched. The parent authorized a private-only, caller-buffer snapshot of the complete instance. The separate battery export asserts all 8192 RAM bytes plus the RTC block. This adds no public API or wire fields.
2. **Task 3 compatibility and receipt binding:** The initial CMake default used source as its own base. CI now uses the actual PR base or push-before SHA; only all-zero new-branch pushes use a validated `origin/main` merge base. The compatibility checker records the mainline base’s absent tokens as `null`, and the phase-entry base’s existing tokens explicitly. The orchestrator delegated this exact initial 0.2.1 disposition under the AGENTS.md in-phase authorization; later changed-pin dispositions still require exact immutable-base evidence and applicable token changes.
3. **Task 3 pin checker addition:** The task file registry was extended to include `verify-state-pins.py` so platform receipts and the delegated approval basis are generated and validated by the existing ratchet rather than an untracked workflow-only projection.

**Total deviations:** 3 owner-authorized refinements. No requirement was removed or deferred from the implementation. Hosted qualification remains an explicit evidence limitation, not a local pass claim.

## Issues Encountered

- The local toolchain reports that the matching Clang libFuzzer runtime is unavailable. Deterministic state-fuzz controls pass locally; the real campaign must run on the hosted sanitizer lane.
- The newly wired Linux/macOS/Windows hosted jobs have not run at `fdf7b2a`. Their exact-head receipts and equality are pending; no cross-platform qualification is claimed here.
- No full-suite run was started because the parent owns the post-wave full-suite and hosted checks. The 1473/1473 result at f192100 remains only the pre-plan baseline.

## User Setup Required

None.

## Next Phase Readiness

Plan 17-06 implementation is complete. Phase 17 remains active and awaits the parent executor’s independent spotcheck, post-wave suite, and exact-head hosted evidence before phase qualification. The `STATE-05` unclassified semantic edge remains visible; pins and continuation controls do not infer broader equivalence.

## Self-Check: PASSED

- The summary file exists at the required phase path.
- All six commits measured from the persisted Plan 17-06 base are ancestors of `plan_head_after` `fdf7b2ac91d5db24f77725cc87588d3c57e26eb7`.
- `summary_coverage` passed 1/1, and coverage entries use the required block schema with automated evidence at immutable implementation revisions.
- Parent-owned STATE.md, ROADMAP.md, REQUIREMENTS.md, config, and state files remain untouched by this plan execution.

---
*Phase: GB-17-native-save-state-core*
*Completed: 2026-10-26*
