---
phase: GB-22-composition-and-microtest-evidence
plan: "12"
subsystem: testing
tags: [diagnostics, C1-OSC, sanitizer, exact-head, phase-boundary]
requires:
  - phase: GB-22-composition-and-microtest-evidence
    provides: D-141 synthetic-plus-metadata evidence and completed D-142 Windows checker remediation
provides:
  - C1 OSC diagnostic payload removal and causal byte regression in the existing evidence control
  - Fresh exact-source independent code and ASVS 1 reviews for the D-143 exception
  - Final full-suite qualification and Phase 22 exact-head boundary evidence
affects: [diagnostic-evidence, phase-23-release-evidence]
tech-stack:
  added: []
  patterns:
    - Remove complete C1 OSC spans after UTF-8 decoding and before generic control cleanup
    - Keep fail-first and correction-disabled mutation evidence inside an existing CTest identity
key-files:
  created:
    - .planning/phases/GB-22-composition-and-microtest-evidence/22-12-SUMMARY.md
  modified:
    - tests/scripts/verify-diagnostic-evidence.py
    - .planning/phases/GB-22-composition-and-microtest-evidence/22-12-PLAN.md
    - .planning/phases/GB-22-composition-and-microtest-evidence/22-EVIDENCE.md
    - .planning/phases/GB-22-composition-and-microtest-evidence/22-VALIDATION.md
    - .planning/phases/GB-22-composition-and-microtest-evidence/22-REVIEW.md
    - .planning/phases/GB-22-composition-and-microtest-evidence/22-SECURITY.md
    - .planning/phases/GB-22-composition-and-microtest-evidence/22-UAT.md
    - .planning/phases/GB-22-composition-and-microtest-evidence/.continue-here.md
    - .planning/STATE.md
    - .planning/state.json
    - .planning/ROADMAP.md
actuals:
  tasks: 3
  commits: 3
key-decisions:
  - "D-143 permits exactly one C1-only correction and fresh review cycle; ordinary review and gap counts remain used."
  - "Keep DIAG-01, DIAG-02, and RIGHTS-01 Pending with all seven real-fixture gates unresolved."
  - "Keep final full-suite and exact-head PR qualification as phase-level closure gates; Phase 23 stays owner-controlled."
requirements-completed: []
coverage:
  - id: C1
    description: "The C1 OSC sanitizer removes the full UTF-8 payload and delimiters, preserves surrounding text and redacts roots within 700 characters; the regression proves fail-first and correction-disabled behavior."
    human_judgment: false
    verification:
      - kind: integration
        ref: "At pre-correction source, the augmented direct control refused with diagnostic-sanitization-control-failed; ignored record: build/phase22/c1-fail-first.json."
        status: pass
      - kind: integration
        ref: "At 93004a65143a4bc3199e1f028b003e2d3dd11ef6, direct control passed; disabling only C1_OSC_ESCAPE produced the same refusal and restoring it passed; see build/phase22/c1-direct-and-mutation.json."
        status: pass
      - kind: integration
        ref: "phase22_evidence_controls passed at the C1 source with its existing identity and 60-second limit; the in-control fail-first/mutation and all retained controls ran."
        status: pass
      - kind: other
        ref: "22-REVIEW.md and 22-SECURITY.md record fresh exact-source clean code and ASVS 1 reviews, zero findings, and the consumed D-143 exception."
        status: pass
  - id: D142-REGRESSION
    description: "The completed D-142 checker remediation remains intact and passes its retained local focused, alternate-build, and broader Phase 21/22 controls without changing test identity, membership, policy, or timeouts."
    human_judgment: false
    verification:
      - kind: integration
        ref: "The retained ten-test selection passed 10/10 after configure and the 339-target build at C1 source 93004a65143a4bc3199e1f028b003e2d3dd11ef6."
        status: pass
      - kind: integration
        ref: "The cmake-3.25.3 alternate-build selection passed 4/4 at the same C1 source."
        status: pass
      - kind: integration
        ref: "The Task 2 Phase 21/22/planning/budget CTest selection passed 19/19 at the same C1 source."
        status: pass
      - kind: other
        ref: "The exact failed-head invariant diff passed for expected tests, CMake policy, registrations, presets, and CI workflow."
        status: pass
  - id: D141-NOGO
    description: "The C1 correction leaves the real-fixture no-go and requirement boundary unchanged: 513 metadata cases, seven unresolved gates, zero admission/execution, Pending requirements, and an owner-controlled Phase 23 route."
    human_judgment: false
    verification:
      - kind: other
        ref: "verify-diagnostic-evidence.py --check at the C1 source passed with assessment=blocked, cases=513, unresolved_gates=7, admitted=0, executed=0."
        status: pass
      - kind: integration
        ref: "phase22_evidence_controls passed its retained immutable-boundary, public-claim, source/package, and mutation controls at the C1 source."
        status: pass
metrics:
  completed: "2026-11-03"
status: complete
plan_head_before: e82f5cc4a709d77740935539841e5daf216ebee8
plan_head_after: d867cbaf60c2c68a6664b633fc43f3a7c11c327a
commits: 3
---

# Phase 22 Plan 12: C1 Diagnostic Sanitizer and Final Qualification

**The C1 OSC diagnostic payload is removed with a causal byte regression and fresh independent review; final full-suite and exact-head qualification passed for PR #142.**

## Accomplishments

- Added the UTF-8 C1 OSC regression to the existing diagnostic sanitizer control, including surrounding sentinels, native/Windows/home-root redaction, control removal, and the 700-character bound.
- Removed the complete U+009D…U+009C span before generic C0/C1 cleanup. The direct regression failed against the old sanitizer, passed after the correction, and refused again when only the C1 matcher was disabled in memory.
- Preserved the D-142 source changes as verification-only. The ten-test local selection, alternate CMake selection, broader 19-test selection, and metadata-only source check passed without changing registrations, inventory, policy, CI, or timeout limits.
- Obtained one fresh independent code review and ASVS 1 security review at `93004a65143a4bc3199e1f028b003e2d3dd11ef6`. Both are clean with zero findings; D-143 did not reset the two ordinary review-fix rounds or the used gap round.

## Verification

- `phase22_evidence_controls` passed, and the augmented sanitizer control retains its fail-first and C1-disabled mutation controls in that existing CTest identity.
- The retained ten-test selection passed 10/10 after configure/build; the alternate configured selection passed 4/4; the broader Phase 21/22/planning/budget selection passed 19/19.
- The immutable metadata check reports 513 cases, seven unresolved gates, admitted=0, and executed=0. DIAG-01, DIAG-02, and RIGHTS-01 remain Pending.
- The exact failed-head diff guard found no changes to expected-test membership, CMake policy, CTest registrations, presets, or CI workflow. The new code review and security verdicts identify the same C1 source.

## Limits and Remaining Qualification

This summary records the completed C1 correction, review cycle, focused local evidence, and final phase qualification. The configured suite passed 1,732/1,732 at PR #142's qualified head `9cb92b0f344b884d5f3e7179740ff5bc87eae379`; exact-head required CI, fixture reproduction, package artifacts, clean source/security reviews, strict branch protection, and merge-tree equality passed before squash merge as `ca2f0be6b38e7dd22e0eb3296b9a21cceed1a765`. PR #143 separately records post-merge Windows scheduling cleanup.

No upstream diagnostic payload was fetched, built, run, admitted, or claimed. No license prohibition is inferred. Phase 23 remains unstarted and owner-controlled through `/gsd-discuss-phase 23`; do not auto-advance.
