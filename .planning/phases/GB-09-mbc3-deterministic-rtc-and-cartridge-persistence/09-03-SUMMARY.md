---
phase: 09-mbc3-deterministic-rtc-and-cartridge-persistence
plan: 03
subsystem: testing
tags: [fuzz, loader, rom-bound, cart-05]
requires: []
provides:
  - synthesised-length fuzz mode covering the 2/4/8 MiB bounds and SIZE_MAX
  - ten length-class seeds plus a short-input seed in fuzz_core_regressions
affects: [09-15]
tech-stack:
  added: []
  patterns: [header-only rewrite into one static zero-initialised buffer]
key-files:
  created: []
  modified: [tests/fuzz_core.c, tests/test_fuzz_core.c]
key-decisions:
  - "D-28: residue (data[0] & 3u) == 2u selects synthesised-length mode; 0 keeps loader, 1/3 keep stateful"
requirements-completed: [CART-05]
coverage:
  - id: D1
    description: "Deterministic fuzz regression tests cover synthetic ROM length bounds and API boundary behavior"
    verification:
      - kind: integration
        ref: "Fresh Phase 15.1-11 focused CTest: fuzz_core_regressions, loader_boundary_fuzz, and battery_api_fuzz (3/3 passed)"
        status: pass
    human_judgment: false
status: complete
commits: 2
plan_head_before: cbc7633
plan_head_after: f0e12fa
actuals:
  tokens: 6000
  tasks: 2
  commits: 2
duration: 8 min
completed: 2026-10-11
---

# Phase 9 Plan 03: Fuzz Coverage of the 8 MiB ROM Bound Summary

Fuzz target now synthesises header-only inputs with ten length classes (declared, +/-1, 2/4/8 MiB and +1, SIZE_MAX) from one static 8 MiB + 1 buffer, asserting a bounded result set, GBB_ROM_TOO_LARGE above 8 MiB, and previous ROM intact on any rejected load.

## Tasks

| Task | Commit | Notes |
| ---- | ------ | ----- |
| 1 Tracer: fuzz_synth_length + 8 MiB+1 seed | b1a8f69 (fuzz_core.c), f0e12fa (seeds) | Tracer verify (3 ctest cases + self-test) passed |
| 2 Ten class seeds + short seed | f0e12fa | 15 gbb_fuzz_core_one_input( occurrences |

## Evidence

- ctest fuzz_core_regressions, loader_boundary_fuzz, battery_api_fuzz pass; `run-bounded-fuzz.sh --self-test` prints `self-test=pass libfuzzer_runtime=unsupported`, so the libFuzzer bounded run (`--fast`) was not run locally; it executes on the Linux sanitizer leg.
- Peak RSS of `build/tests/test_fuzz_core` (one full deterministic run): 20,660,224 bytes (about 19.7 MB), far below the 512 MB limit (static buffer pages stay untouched except the header).
- The four FUZZ_ literals are unchanged (65536u, 16u, 2048, 8192).

## Deviations from Plan

None - plan executed exactly as written. Both tasks' source was written together and committed as two commits (harness change, then seeds); the SIZE_MAX pointer is the buffer start with length SIZE_MAX, relying on the core rejecting before reading past the header.

## Known Stubs

None.

## Self-Check: PASSED

tests/fuzz_core.c and tests/test_fuzz_core.c exist; commits b1a8f69 and f0e12fa are on the branch.

## Current Verification — 15.1-11

The three deterministic fuzz regression CTests passed in the focused batch. `run-bounded-fuzz.sh --self-test` remains only the recorded script self-test: it reports `libfuzzer_runtime=unsupported` and requires a hosted campaign; no local libFuzzer campaign or campaign receipt is claimed.
