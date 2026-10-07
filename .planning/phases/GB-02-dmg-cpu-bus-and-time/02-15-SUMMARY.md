---
phase: GB-02-dmg-cpu-bus-and-time
plan: 15
subsystem: testing
tags: [mooneye, fixture-reproduction, blocked-admission]
requires:
  - phase: GB-02-14
    provides: Source-audited headless CPU/timer candidate and local protocol probe
provides:
  - Explicit admission halt and preserved three-case denominator
affects: [GB-02-16, CPU-01, CPU-03, CPU-05, T-02-14, T-02-26]
tech-stack:
  added: []
  patterns: [fail-closed fixture admission]
key-files:
  created: [.planning/phases/GB-02-dmg-cpu-bus-and-time/02-15-SUMMARY.md]
  modified: []
key-decisions:
  - Keep original ROMs, manifest, and three-case denominator unchanged while cross-host candidate bytes are unqualified.
  - Halt before verifier/workflow alignment because there is no final admitted candidate manifest to validate.
requirements-completed: []
actuals:
  tokens: 0
  tasks: 0
  commits: 0
commits: 0
plan_head_before: cabe4ce6f32b82d08dbdc1b619f8493ebafc2e7f
plan_head_after: cabe4ce6f32b82d08dbdc1b619f8493ebafc2e7f
duration: 5min
completed: 2026-10-06
status: halted
---

# Phase GB-02 Plan 15: Fixture Admission Halt Summary

**No candidate ROM was admitted because the pinned tool recipe has not produced identical bytes on macOS and Linux, and the current compare mode rebuilds only the ineligible original ROMs.**

## Task status

| Task | Status | Evidence |
|---|---|---|
| 1. Rebuild and record qualified bytes | Blocked before mutation | Plan 02-14 locally source-qualified a derivative, but there is no exact cross-host derivative byte comparison. The pinned WLA-DX linker has a confirmed host-dependent tied-section order. |
| 2. Verify final manifest and hosted bytes | Not started | No final admitted bytes exist to validate or put into the hosted compare job. |

No task commits were made. No ROM, manifest, source/tool patch, verifier, workflow, or denominator was changed. The fixed original IDs remain `mooneye-acceptance-instr-daa`, `mooneye-acceptance-timer-tim00`, and `mooneye-acceptance-timer-tim00-div-trigger` (one CPU, two timer), with their original manifest SHA-256 values; they remain **ineligible as built** because the original reporting path reads LY before callback. There are zero newly admitted candidates. The Plan 02-14 derivative retains Mooneye MIT rights, preserves acceptance assertions and the register protocol, and passed local positive/negative probes; that is candidate evidence, not admission.

## Exact byte evidence

At local Darwin/arm64 revision `cabe4ce6f32b82d08dbdc1b619f8493ebafc2e7f`, `bash tests/scripts/reproduce-mooneye.sh --compare fixtures/mooneye` passed for all three **original** checked-in ROMs, each 32,768 bytes, with zero differing offsets. That command does not apply `headless-report.patch` in compare mode, so its pass cannot qualify derivative bytes. The derivative `--candidate` mode records a patch digest and builds candidates, but does not compare them against a final manifest or hosted output.

The previous exact hosted Linux/x86_64 [fixture run 37548730397](https://github.com/szTheory/gabbaboy/actions/runs/37548730397) at revision `95fdabac8c6b41a43ea2b4877cf1f59b41ed63d4` failed `mooneye-fixture-repro` after building and comparing all three original ROMs. The source/tool/font pins matched; the original DAA differed at 83 bytes, and each original timer differed at 209 bytes, including payload bytes. Plan 02-13 traced this to pinned WLA-DX `_sections_sort` returning `-1` for equal priority/size sections passed to `qsort`, yielding host-dependent section positions. This result cannot be repaired by selecting a checksum or replacing a manifest digest with the Linux output. There is **no fresh hosted candidate run at the current head**; no exact-hosted pass is claimed.

## Blocking condition and route

The plan requires final candidate bytes to pass `--compare` on both local and hosted pinned recipes. That currently needs a reviewed deterministic WLA-DX tool recipe and candidate-aware all-case comparison before any manifest/ROM replacement. The reproduction script and tool recipe are outside Plan 02-15's declared file boundary; changing the acceptance/report patch or inventing a host-specific digest here would violate D-10. The dependency for Plan 02-16 is therefore unresolved. T-02-14, T-02-25, T-02-26, CR-05 and CPU-05 remain open. Phase GB-02 remains executing; this summary is a halt record, not a phase completion claim.

## Deviations from Plan

The intended fixture admission and final verifier/workflow changes were not attempted because the exact-byte precondition failed. The existing corpus and owner/runtime files were preserved.

## Self-Check: PASSED

This summary exists; the plan base remains HEAD with zero task commits; the manifest still contains three original entries; `git diff --check` passed. The current CMake verifier reports one CPU and two timer entries, which verifies manifest consistency only and does not cure their known LY-dependent ineligibility.
