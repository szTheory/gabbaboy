---
phase: GB-17-native-save-state-core
plan: "05"
subsystem: testing
tags: [C, save-state, snapshot-fork, mutation-testing, CTest]
requires:
  - phase: GB-17-native-save-state-core
    provides: [versioned public state codec, 198-field descriptor ledger, transactional state load]
provides:
  - Complete snapshot-fork coverage for the admitted corpus and generated in-flight cases
  - Model-applicable census and exact omission controls for all 198 serialized fields
  - Validated reachable pulse/noise timer bounds without changing APU timing or wire widths
affects: [GB-17-native-save-state-core, GB-18-player-save-slots]
actuals:
  tokens: 56374
  tasks: 3
  commits: 9
tech-stack:
  added: []
  patterns: [immutable-revision source-copy mutants, bounded CTest shards, poisoned-target snapshot forks]
key-files:
  created:
    - tests/test_state_fork.c
    - tests/data/state-forks.json
    - tests/scripts/verify-state-forks.py
    - tests/scripts/test-state-fork-mutant-controls.py
  modified:
    - src/core/gabbaboy.c
    - docs/state-format.md
    - tests/test_state_internal.c
    - tests/CMakeLists.txt
    - tests/expected-tests.txt
    - .planning/phases/GB-17-native-save-state-core/17-05-PLAN.md
key-decisions:
  - "Keep snapshot equivalence distinct from original oracle replay and from run-slice invariance."
  - "Require DMG and CGB witnesses wherever a category applies to both models; census absence does not establish inapplicability."
  - "Use immediate public load/save canonical equality for cache fields whose consuming path refreshes them before the next guest sample."
  - "Accept only the audited reachable pulse and noise timer maxima; preserve runtime timing, counter widths, and the state format."
patterns-established:
  - "Mutation checkers bind immutable 40-hex source revisions, field witnesses, fixture identities, and named discrepancies."
  - "Observer deltas use receiver RAM/RTC projections and rumble line as pre-load baselines; local counters are compared separately."
requirements-completed: [STATE-02, STATE-04, STATE-06]
coverage:
  - id: D1
    description: "All admitted corpus cases fork through public save/load calls into fresh poisoned targets and compare future outputs, metadata, observer projections, and final canonical bytes."
    requirement: STATE-02
    verification:
      - kind: integration
        ref: "CTest state_fork_matrix, all 16 matrix shards, and state_slice_invariance at immutable revision 64377a4222e4585a888ac5b5217f94a5e31739bb; included in the named fork/census/mutation selection (38/38 passed)."
        status: pass
    human_judgment: false
  - id: D2
    description: "Every save-boundary category and every serialized field has a discriminating witness or exact tested treatment, with model applicability and missing-category controls."
    requirement: STATE-04
    verification:
      - kind: integration
        ref: "CTest state_fork_census and state_fork_census_controls at immutable revision 64377a4222e4585a888ac5b5217f94a5e31739bb; 14/14 categories and 198/198 fields, including negative controls, passed."
        status: pass
    human_judgment: false
  - id: D3
    description: "Every declared serialized-field omission is exercised on the designated poisoned target restore and rejected by its named canonical or continuation discrepancy; absent/unexercised manifest controls fail."
    requirement: STATE-04
    verification:
      - kind: integration
        ref: "CTest state_fork_mutants, all 16 omission shards, state_fork_mutant_controls, and summary gate at immutable revision 64377a4222e4585a888ac5b5217f94a5e31739bb; included in the 38/38 passing selection."
        status: pass
    human_judgment: false
  - id: D4
    description: "Reachable pulse/noise timer values round-trip with equal continuation; CRC-valid above-bound values are rejected without receiver mutation."
    requirement: STATE-06
    verification:
      - kind: unit
        ref: "CTest state_apu_pulse_timer, state_apu_noise_timer, state_semantic_bounds, state_refusal, and state_audio_bound at immutable revision 64377a4222e4585a888ac5b5217f94a5e31739bb; targeted state/APU/audio selection passed 13/13."
        status: pass
      - kind: integration
        ref: "cmake --preset phase1 && cmake --build --preset phase1 at immutable revision 64377a4222e4585a888ac5b5217f94a5e31739bb; build passed."
        status: pass
    human_judgment: false
commits: 9
plan_head_before: 83351ab901e38bbf32b1e48832fce5ecc7e8d114
plan_head_after: 64377a4222e4585a888ac5b5217f94a5e31739bb
duration: 69min
completed: 2026-10-26
status: complete
---

# Phase GB-17 Plan 05: Native Save State Core Summary

**Public snapshot forks now cover the complete admitted corpus, all 198 serialized fields, and 14 in-flight categories, with exact field-omission evidence and corrected reachable APU timer bounds.**

## Accomplishments

- Implemented the fork runner using public save/load calls, a fresh target with serialized storage poisoned, and comparisons of every later frame and metadata, PCM sample, run-result field, battery/RTC projection, rumble line, observer counter delta, and final canonical state bytes. Slice invariance remains a separately named property.
- Enumerated 153 cases: 147 ROM rows from all 20 admitted fixture manifests plus 6 rows from the two existing acceptance manifests. Original pass, expected-failure, prior-observation, and acceptance labels remain attached; the result proves snapshot equivalence and does not claim original oracle replay. The optional Acid2 corpus remains excluded because it is rights-gated and its ROM bytes are absent.
- Required all 14 in-flight categories with their declared model applicability and a predicate-backed boundary. DMG+CGB categories receive witnesses on both models. APU sequencer applies to both models; CGB coverage comes from admitted corpus cases. Guest-generated cuts and accepted-state metamorphic seeds are identified separately. Supported nonzero DMA, STOP, and unsupported-bus representations remain accepted and tested; no generic zero-only validator tightening was added.
- Added 23 generated field fixtures and an exact 198-entry field-mutant manifest. Each source-copy mutant skips only its named assignment while consuming the wire bytes once, is disabled during accepted-state seed loads, and is armed for the designated poisoned target restore. The target's field difference is checked before continuation, and setup errors, initial-load failures, crashes, and timeouts cannot count as semantic kills.
- Kept observer histories distinct: RAM/RTC projection and rumble line are compared against the receiving instance immediately before load, while local counters use separate baselines. The named DIV omission discrepancy is the immediate public load/save status and canonical bytes; the subsequent timed FF04 read refreshes the cache before a guest sample, and later continuation checks still run.
- Corrected the audited state validator bounds for pulse timers to 65,472 (0xFFC0) and noise timers to 7,340,032. Tests enumerate the 2,048 pulse trigger frequencies and all 256 NR43 values, exercise reset/expiry reload paths and high-timer save/load continuation, and reject CRC-recomputed above-bound states transactionally. Wave, envelope, and sweep limits remain unchanged. APU runtime timing, field widths, and format are unchanged.

## Verification

- `cmake --preset phase1 && cmake --build --preset phase1` — passed at `64377a4222e4585a888ac5b5217f94a5e31739bb`.
- Fork, matrix shards, census, census negative controls, slice invariance, 16 omission shards, mutation summary, and omission negative controls — 38/38 passed.
- Targeted state, APU pulse/noise, semantic bounds, refusal, observer, RTC/palette, audio-bound, and CGB APU lifecycle tests — 13/13 passed.
- `dmg_baseline` — passed (1/1).
- `summary_coverage` — passed (1/1); the GSD classifier auto-covers all four deliverables.
- Mutation comparator classes (non-exclusive): immediate post-load canonical contract 198; final canonical bytes 150; PCM 31; run result 22; frame plus metadata 10; battery projection/generation 8; rumble line/counter 8; battery local counter 1; rumble local counter 1.
- Representative causal kills include APU noise to PCM/final bytes, CGB palette to frame metadata/final bytes, cartridge RAM to battery observer counter, MBC5 rumble to rumble observer counter, CGB speed-switch stall to run result, RTC subsecond to battery/rumble projections, and DIV to its named immediate canonical discrepancy.
- The pre-plan full local suite was 1,321/1,321 at `048b35a`; a full post-plan phase suite is left to the orchestrator's final-head pass. The expensive full horizon ASan selection was not repeated after its prior 180-second timeout under local emulation; native hosted evidence remains pending.

## TDD Gate Compliance

- **RED:** Reachable pulse and noise reload values exposed validator ceilings below values produced by unchanged runtime logic. Assertion evidence was machine-classified and retained only in ignored `build/` files. The absent-mutant-record control also produced a machine-classified assertion RED (`build/state-fork-mutant-control-red.json`): the required record was absent and the checker rejected the manifest. The ordinary snapshot-fork baseline was already green, so no failing behavior was manufactured for that control.
- **GREEN:** Commits `2a19833` and `64377a4` implement the audited bounds and complete the 198-entry source-copy omission matrix; the positive fork controls, named discrepancy checks, and negative manifest controls pass.
- **REFACTOR:** No standalone refactor commit was needed. Follow-up commits tightened model-specific census requirements and bounded shard/control coverage without changing public API or runtime behavior.

## Decisions Made

- Keep original oracle replay, snapshot equivalence, and whole-versus-split slice invariance as distinct claims.
- Treat census completeness as inventory evidence, not physical reachability or hardware evidence.
- Use the immediate canonical public contract for cache-field omissions only when the actual consuming path refreshes that cache before later guest sampling.
- Preserve receiver observer projections and local counters as different comparisons.

## Deviations from Plan

### Owner-authorized correctness and evidence refinements

1. The validator's previous pulse and noise timer ceilings rejected reachable values emitted by unchanged APU reload paths. The exact maxima were derived from assignments and consumers, with exhaustive domain and transactional rejection tests; timing and format stayed unchanged. Committed in `2a19833`.
2. Model-applicable category evidence required additional generated DMG/CGB cuts and an explicit CGB witness for the globally applicable APU sequencer. Full corpus and category applicability were retained. Committed through `1dd3e95`.
3. DIV's consuming timed bus read refreshes the cache before sampling FF04, so that omission uses the named immediate load/save canonical-byte discrepancy while still running later output comparisons. The mutation hook is armed only for the target restore. Committed in `64377a4`.

**Total deviations:** 3 owner-authorized correctness/evidence refinements. No scope was removed and no unresolved in-scope correctness finding remains.

## Issues Encountered

- The full local horizon sanitizer selection previously timed out at 180 seconds under emulation. It was not repeated; native hosted evidence remains pending for the orchestrator to inspect.
- Shared STATE/ROADMAP/REQUIREMENTS tracking remains with the orchestrator as requested; this plan worker changed only its owned implementation files and this summary.

## Privacy and Publication Guard

**Do not push the current branch history.** The public base is `bac4694f08d69472c55d4137d356224779153ed7`. Two unpublished commits contain raw RED JSON blobs with host-specific data at `.planning/phases/GB-17-native-save-state-core/17-05-red-evidence.json` and `.planning/phases/GB-17-native-save-state-core/17-05-noise-red-evidence.json`. They were removed from the working tree in `83351ab`; original classified reports remain in ignored `build/`. The parent must replay/sanitize history and refresh immutable revision references before any push. No push was performed.

Original commit sequence from the public base through the current implementation tip: `1d8698b`, `846ced8`, `3300de5`, `6e53c5b`, `2a19833`, `83351ab`, `299a63c`, `513d47d`, `a233da6`, `e951a30`, `00c2e24`, `1dd3e95`, `258208f`, `7756b92`, `64377a4`.

## Next Phase Readiness

Plan 17-05 is complete. Phase 17 remains active; plans 17-06 through 17-11 are still listed as runnable. Do not advance to Phase 18 yet. The next milestone phase is Phase 18, **Player Save Slots and Host Contract**, after Phase 17 has been completed and verified.

## Self-Check: PASSED

- Summary file exists at the required phase path.
- All nine commits measured from the persisted Plan 17-05 ledger are ancestors of `plan_head_after` (`64377a4`).
- The summary's automated coverage entries are block-schema entries with passing unit/integration evidence at immutable revision `64377a4222e4585a888ac5b5217f94a5e31739bb`.
- `summary_coverage` passed for this summary (1/1).

---
*Phase: GB-17-native-save-state-core*
*Completed: 2026-10-26*
