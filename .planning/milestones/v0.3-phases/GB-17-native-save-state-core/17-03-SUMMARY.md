---
phase: GB-17-native-save-state-core
plan: "03"
subsystem: state-persistence
tags: [save-state, RTC, observer-counters, refusal-atomicity, allocation-probe, CTest]
requires:
  - phase: GB-17-native-save-state-core/17-02
    provides:
      - Versioned state codec, cached ROM identity, canonical field validation, and installed tracer
provides:
  - Exact RTC, palette, RAM, and continuation restore with receiver-local saturating observers
  - Whole-instance and owned-buffer refusal oracle with complete truncation and error-precedence coverage
  - Allocation/hash-free public state API probe bound to an immutable implementation revision
affects: [native-integration, state-persistence]
actuals:
  tokens: 18945.5
  tasks: 3
  commits: 3
commits: 3
plan_head_before: 032ea013aeaa8a65d8ed098743e44f3b2ce1838b
plan_head_after: 30f2151769a770f13853bf4a292c196e3ee85c23
tech-stack:
  added: []
  patterns:
    - White-box snapshots compare raw instance bytes and all owned ROM/RAM buffers on refused operations.
    - Disposable mutation builds require the named assertion to fail and an unrelated control to pass.
    - Immutable state evidence verifies source files and the compiled probe against one exact Git revision.
key-files:
  created:
    - tests/test_state_internal.c
    - tests/test_state_alloc.c
  modified:
    - src/core/gabbaboy.c
    - tests/CMakeLists.txt
    - tests/expected-tests.txt
    - docs/cartridge-and-saves.md
    - tests/scripts/verify-state-contract.py
key-decisions:
  - Keep lazy RTC wire fields and receiver-local observer histories exact across successful loads.
  - Compare projected battery-visible RTC bytes at each emulated instant without normalizing stored RTC representation.
  - Preserve existing fail-closed validation and bounded write behavior, and make their guarantees mutation-sensitive.
requirements-completed: [STATE-01, STATE-02, STATE-03, STATE-06]
coverage:
  - id: GB17-03-01
    description: "A fresh compatibility-mode target resumes the saved RAM, raw RTC representation, palette, future audio, frame output, and canonical state bytes."
    requirement: STATE-01
    human_judgment: false
    verification:
      - kind: e2e
        ref: "state_rtc_palette and state_tracer at immutable implementation revision 30f2151769a770f13853bf4a292c196e3ee85c23; the tracer's precodec receipt was generated before execution."
        status: pass
  - id: GB17-03-02
    description: "Battery generation changes only for changed projected battery bytes, rumble observers track line transitions, and both counters saturate without entering the wire state."
    requirement: STATE-02
    human_judgment: false
    verification:
      - kind: unit
        ref: "state_observers at immutable implementation revision 30f2151769a770f13853bf4a292c196e3ee85c23 checks equal lazy RTC projections, changed and repeated RAM/RTC loads, separate receivers, rumble transitions, serialized-counter immunity, and saturation."
        status: pass
      - kind: integration
        ref: "The 11 state observer mutants and their unrelated passing controls all passed at immutable implementation revision 30f2151769a770f13853bf4a292c196e3ee85c23."
        status: pass
  - id: GB17-03-03
    description: "Every refused load preserves the complete destination and owned buffers; error precedence, every truncated prefix, short-save atomicity, and exact output extent are checked."
    requirement: STATE-03
    human_judgment: false
    verification:
      - kind: unit
        ref: "state_refusal, state_refusal_controls, and state_semantic_bounds at immutable implementation revision 30f2151769a770f13853bf4a292c196e3ee85c23; the refusal case checks all 197,368 truncated lengths for its fixture."
        status: pass
      - kind: integration
        ref: "Apply-before-validation, invalid-content counter mutation, short-save prefix write, and trailing save write mutants were each rejected by the intended whole-state or output assertion; all four unrelated controls passed at revision 30f2151769a770f13853bf4a292c196e3ee85c23."
        status: pass
  - id: GB17-03-04
    description: "State size, save, and load make no heap calls or ROM hashes, size/save remain observationally pure, and independent receiving instances keep separate state."
    requirement: STATE-06
    human_judgment: false
    verification:
      - kind: unit
        ref: "The immutable state_purity probe at revision 30f2151769a770f13853bf4a292c196e3ee85c23 reports heap_calls=0 and hashes=0 for success and error paths; its allocator/hash hooks pass the sensitivity control."
        status: pass
      - kind: integration
        ref: "Allocation-in-save, hash-in-save, and save-tail-overwrite mutants were rejected by state_purity while all three state_purity_controls passed at revision 30f2151769a770f13853bf4a292c196e3ee85c23."
        status: pass
      - kind: integration
        ref: "state_globals and state_globals_controls pass at immutable implementation revision 30f2151769a770f13853bf4a292c196e3ee85c23."
        status: pass
duration: 17min
completed: 2026-10-26
status: complete
---

# Phase 17 Plan 03: Native Save State Restore and Refusal Guarantees Summary

**Native state loads preserve full lazy RTC and palette state, update receiver-local observers exactly, and reject invalid data without touching the machine or caller output.**

## Performance

- **Duration:** 17 min
- **Started:** 2026-10-26T21:44:26Z
- **Completed:** 2026-10-26T22:01:01Z
- **Tasks:** 3
- **Files modified:** 7

## Accomplishments

- Added `state_battery_equal_projected` and `state_apply_observers`, retaining exact lazy RTC fields while comparing battery-visible projected state and saturating receiver-local counters.
- Added public-path RTC, RAM, palette, audio, frame, and canonical-resave coverage, plus controls for catch-up, raw RTC comparison, counter deltas, serialization, and saturation errors.
- Added whole-instance, ROM, and RAM snapshots for refused loads; swept every truncated length and pinned compound header, identity, size, CRC, and semantic error precedence.
- Verified poisoned size outputs, untouched short-save buffers, no-ROM-before-capacity ordering, and preserved successful-save tail bytes.
- Added allocator/SHA instrumentation across state API successes and errors, an immutable revision checker, and named allocation, hash, and tail-write mutants.

## Verification

- `cmake --preset phase1` passed at implementation revision `30f2151769a770f13853bf4a292c196e3ee85c23`.
- `cmake --build --preset phase1` passed at the same revision.
- The targeted state CTest selection passed 47/47, including the tracer and generated precodec receipt, observer and refusal matrices, semantic bounds, all new mutants and controls, immutable purity evidence, and writable-global scan.
- The immutable `state_purity` probe reports zero allocator calls and zero SHA calls; its executable revision string matches the 40-hex Git revision supplied to the checker.
- `git diff --check` passed. The full project CTest suite remains the phase orchestrator's post-wave check.

## Task Commits

1. **Track projected state-load observers and restore RTC/palette continuation** — `7841efd`.
2. **Prove save-state refusal atomicity and exact output bounds** — `39e1586`.
3. **Instrument save-state allocation and hash purity** — `30f2151`.

The plan ledger measured three implementation commits from `032ea013aeaa8a65d8ed098743e44f3b2ce1838b` through `30f2151769a770f13853bf4a292c196e3ee85c23`. The actual diff contained 75,782 characters, or 18,945.5 estimate tokens.

## Verification Notes

- The behavior already existed across the preceding state-codec plans, so the new contract tests passed against the existing implementation rather than producing an artificial RED. Task 1 extracted the settled observer behavior into explicit helpers; Tasks 2 and 3 required no production behavior change. Named disposable mutants and unrelated passing controls demonstrate that the tests detect the specified regressions.
- No new stubs, skipped tests, unrun task verifications, or security-relevant trust surfaces were introduced.

## Deviations from Plan

None. The existing load validation and save bounds already met Tasks 2 and 3; this plan added the requested whole-instance and instrumentation evidence without changing those production paths.

## Integration Follow-up

The Phase 17 wave review exposed four test and checker integration defects. At immutable integration revision `7c1b86f953dc467a1c2c82bea66d386600f79090`, the palette omission mutant now consumes one palette wire element per iteration while omitting its application; successful save fixtures reserve a guard byte so the tail-write mutant reaches the dedicated output-tail assertion; the global checker recognizes writable TLS symbols without objdump's optional `O` flag and maps GNU BFD PE/PEI zero-based sections correctly; and the event boundary test reaches the ordinary-time cap through a valid STOP wake.

- Normal focused CTest passed 14/14, including immutable `state_globals`, parser format controls, revision controls, state allocation/hash purity, the whole-instance refusal and observer cases, the palette and tail-write mutants with passing unrelated controls, and the cap-relative event test.
- A fresh Linux Docker build with `GABBABOY_ENABLE_SANITIZERS=ON` passed the same 14/14 focused CTests with the project's shared 3x timeout multiplier. ASan/UBSan remained enabled; passing mutant controls completed cleanly.
- The host Clang cross-target ELF fixture confirmed the `.tdata` TLS row without `O` is classified writable. GNU PEI section-table coverage, including the relocated `.rdata` control, passed in both focused runs.
- Windows execution was not available locally; no local Windows result is claimed.

The original three-task plan ledger above remains historical. The integration correction is an additional commit: `7c1b86f` (`test(17-03): repair save-state integration controls`).

## Self-Check: PASSED

- Summary file exists at the required phase path.
- Implementation commits `7841efd`, `39e1586`, and `30f2151` exist and are ancestors of the implementation head.
- Integration follow-up commit `7c1b86f` exists and is an ancestor of the current head.
- The `summary_coverage` CTest passes for the block-schema coverage entries in this file.
