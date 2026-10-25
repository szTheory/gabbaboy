---
phase: 99-immutable-malformed-summary-fixture
plan: 01
subsystem: testing
tags: [fixture, negative-control]
requires: []
provides:
  - "A deliberately malformed plan summary that summary coverage checking must reject"
affects: []
requirements-completed: []
status: complete
coverage:
  - id: D1
    description: "Coverage written in the rejected Phase 9 and 10 flow-style shape"
    requirement: FIXTURE-01
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest -R '^fixture$'"
        status: pass
---

# Phase 99 Plan 01: Immutable malformed summary fixture

This file is test data for `tests/scripts/verify-summary-coverage.py --file`. It reproduces the flow-style
`{kind: ..., ref: ..., status: ...}` verification item and the `ctest` kind that early plan summaries used
and that the GSD coverage classifier cannot read. It is not a plan summary and is never edited to make a
live summary pass; `tests/CMakeLists.txt` pins its SHA-256 at configure time.
