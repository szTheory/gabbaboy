---
phase: 10-cgb-profile-banking-and-register-visibility
plan: 02
subsystem: testing
tags: [model-gates, cgb, dmg, audit, ctest, comment-only]
requires: ["10-01"]
provides:
  - "src/core/gabbaboy.c: GATE-00 function tag on all 126 functions plus 66 unique branch gates (GATE-01..GATE-66)"
  - "docs/model-gates.md: 67 table rows mirroring the code, plus a Release status section"
  - "CTests model_gates, model_gates_real_deleted_tag, model_gates_real_untagged_function, model_gates_real_doc_mismatch, model_gates_release_blocked"
affects: [10-04, 10-06, 10-09, 10-20]
tech-stack:
  added: []
  patterns: ["configure-time mutants of the real source/doc with exactly-once anchors (forward and REVERSE)"]
key-files:
  created: []
  modified:
    - src/core/gabbaboy.c
    - docs/model-gates.md
    - tests/CMakeLists.txt
    - tests/expected-tests.txt
key-decisions:
  - "OAM-DMA CPU bus-conflict branches in read8 and write8 are UNKNOWN expected-failure:cgb-separate-buses (D-17)"
  - "Gate numbers are assigned in source order; the deleted-STOP-tag mutant anchors on the tag prose with a regex gate number so later renumbering cannot break it"
  - "A deleted branch tag is caught by R2 (doc row without a code tag, gate-doc-mismatch), which fires before any untagged-function finding; the test pins that token"
requirements-completed: [CGB-02]
duration: 40 min
completed: 2026-10-12
status: complete
commits: 2
plan_head_before: ee717df4e070af2482fa8d244ce69da2d4d3f370
plan_head_after: 13afbdc2364ca91fd01159ac2ea5b5273da2730b
actuals:
  tokens: 30000
  tasks: 2
  commits: 2
coverage:
  - deliverable: "Every function and model-differing branch in the core is tagged and the doc mirrors the code"
    human_judgment: false
    verification:
      - {kind: ctest, ref: "model_gates", status: pass}
  - deliverable: "Core diff is comment-only and the DMG behaviour is unchanged"
    human_judgment: false
    verification:
      - {kind: script, ref: "tests/scripts/verify-dmg-baseline.sh (baseline status=pass)", status: pass}
      - {kind: ctest, ref: "full suite 419/419", status: pass}
  - deliverable: "Mutations of the real source and doc are rejected with named tokens"
    human_judgment: false
    verification:
      - {kind: ctest, ref: "model_gates_real_deleted_tag", status: pass}
      - {kind: ctest, ref: "model_gates_real_untagged_function", status: pass}
      - {kind: ctest, ref: "model_gates_real_doc_mismatch", status: pass}
  - deliverable: "Release mode records the open research items"
    human_judgment: false
    verification:
      - {kind: ctest, ref: "model_gates_release_blocked", status: pass}
---

# Phase 10 Plan 02: Tag the core by model Summary

**All 126 functions in `src/core/gabbaboy.c` carry a MODEL tag and 66 model-differing branches carry unique GATE ids, mirrored row-for-row in `docs/model-gates.md`; the diff is comments only and the scanner plus four real-file negative controls run in CTest.**

## Accomplishments

- Tracer: reset_state's header-checksum F line (UNKNOWN research:10) and the STOP case (UNKNOWN research:12) were tagged first, then the scanner was run on the real file before tagging the rest.
- Function tags use the shared `GATE-00 BOTH basis=` (cartridge-side, host-side-mixing, diagnostics-only, host-api, `"no SM83 opcode difference"` for the CPU core, D-24 for validate_header, see-branch-gates or model-neutral otherwise).
- Branch gates cover the research inventory: post-boot literals (research:10), PPU lock windows and timing (research:11), DMA, DIV and STOP (research:12), timer, serial, STAT, JOYP, APU and wave RAM (research:14), the DMA bus conflict (expected-failure), and BOTH gates with a basis for cartridge, WRAM, JOYP select, LCDC literals, header checksum, profile argument, HALT, illegal opcode and interrupt entry.
- The scanner reports `model-gates pass functions=126 gates=67 unknown=51`.
- Real-file controls: STOP tag deleted, untagged `gbb_model_gate_probe` appended, read8 bus-conflict row changed to research:14, and `--release` on the real files (expected to fail until Phase 14/15).
- Doc gained a "Release status" section naming the phases that own the open `research:` rows.

## Deviations from Plan

None - plan executed as written. One pinned detail: the plan allowed either `gate-untagged-function` or `gate-doc-mismatch` for the deleted-tag control; the observed (and pinned) token is `gate-doc-mismatch`.

## Verification

- `ctest -R '^model_gates'`: 8/8 pass; full `ctest --preset phase1`: 419/419 pass.
- `bash tests/scripts/verify-dmg-baseline.sh`: `baseline status=pass`.
- `git diff main -- src/core/gabbaboy.c`: zero non-comment changed lines; JOYP select anchor and `& 1u) << 8` anchor each still occur once; `expected-failure:cgb-separate-buses` occurs twice.

## Known Stubs

None.

## Self-Check: PASSED
