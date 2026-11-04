---
phase: GB-23-qualified-v0-4-0-release
plan: "02"
subsystem: release-evidence
tags: [release-notes, source-bound-disclosure, docs-controls]
requires:
  - phase: GB-23-qualified-v0-4-0-release
    provides: Shared immutable v0.4 support claims and production ledger from Plan 23-01.
provides:
  - Concise v0.4 release notes rendered and judged from the same immutable claim profile as the support ledger.
  - Release guidance for the existing exact-head preparation route, recovery holds, product limits, and downloaded-artifact gates.
affects: [23-03, release-qualification]
actuals:
  tokens: 13326.5
  tasks: 2
  commits: 3
plan_head_before: 8739d5b1
plan_head_after: 50e574e9
tech-stack:
  added: []
  patterns:
    - Public release prose is checked against a version-bound profile and the exact judged Git revision.
    - Documentation omissions and promotion claims have explicit negative controls.
key-files:
  created: []
  modified:
    - docs/release.md
    - tests/scripts/verify-support-ledger.py
    - tests/scripts/verify-v02-adoption.py
    - tests/CMakeLists.txt
    - tests/expected-tests.txt
key-decisions:
  - "Render the concise preface from the validated support-claims-v0.4.json profile; no release-disclosure.json change was needed."
  - "REL-01 remains Pending until Plan 23-06 establishes actual release and consumer evidence."
patterns-established:
  - "The notes checker resolves version identity, generated ledger, and claims from the immutable judged revision."
  - "Release runbook requirements are paired with omission and false-publication controls."
requirements-completed: []
coverage:
  - id: RELEASE-NOTES-DISCLOSURE
    description: "Concise v0.4 release notes use shared immutable claims and reject omissions, contradictions, and promotion beyond the evidence."
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest --preset phase1 --output-on-failure --no-tests=error -R '^(release_notes_v04|release_notes_v04_controls)$'"
        status: pass
      - kind: integration
        ref: "Focused Plan 23-02 T1 CTest selection passed all 7 tests, including historical disclosure and source-bound claim controls."
        status: pass
  - id: RELEASE-PREPARATION-GUIDANCE
    description: "The release runbook documents exact version identity, supported products, recovery holds, the existing rehearsal sequence, and later downloaded-byte checks."
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest --preset phase1 --output-on-failure --no-tests=error -R '^(v02_adoption_docs|v02_adoption_docs_controls)$'"
        status: pass
status: complete
---

# Phase 23 Plan 02: Concise release disclosure

**The v0.4.0 release preface and preparation guide now share source-bound facts and reject missing disclosures or unsupported publication claims.**

## Performance

- **Duration:** about 1 h
- **Started:** 2026-11-04T01:53:15Z
- **Completed:** 2026-11-04T02:53:03Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments

- Added a concise release-notes preface generated from the same validated immutable v0.4 claim profile as the support ledger; the version-aware checker binds identity and the exact ledger link to the judged revision.
- Added adversarial release-note controls for candidate reason omissions and contradictions, evidence scope, counts and Pending statuses, platform and signing limits, source identity, and false publication claims while preserving historical v0.3 output.
- Documented the actual product matrix, inspected macOS deployment/SDK caveat, host/state compatibility, deterministic performance gates, H → R1 → W → R2 → nightly → pre-tag sequence, window invalidation, downloaded-artifact requirements, and recovery holds.
- Kept REL-01 Pending and made no release, game-admission, signing, notarization, or cross-platform player claim.

## Task Commits

1. **Task 1: Generate and check the concise release disclosure from shared immutable facts** — `b341960f` (RED test), `ba15a8e0` (implementation).
2. **Task 2: Document the existing v0.4 preparation route and verify omissions** — `50e574e9` (docs and controls).

## TDD Evidence

- **Task 1 RED:** `release_notes_v04_controls` failed because the candidate-reason omission was accepted. The target ran and failed on the intended semantic assertion; the GSD classifier returned `RED_EVIDENCE_OK`. Evidence: `build/tdd-red-evidence/23-02-T1-red.json` and `23-02-T1-red.xml`.
- **Task 1 GREEN:** The selected release-note, support-claim, historical-disclosure, and boundary-control suite passed all seven tests. The immutable profile was sufficient, so `tests/data/release-disclosure.json` remained unchanged.
- **Task 2:** The documentation checker passed 466 checks. Its 92 negative controls rejected all 92 mutations. The four focused CTest targets for docs and generated v0.4 notes passed after the final controls were added.

## Files Created/Modified

- `tests/scripts/verify-support-ledger.py` — Renders the concise preface from validated immutable v0.4 facts.
- `tests/scripts/verify-v02-adoption.py` — Judges version-bound note identity, required disclosures, and adversarial omission/promotion cases.
- `tests/CMakeLists.txt` — Registers the versioned release-note and documentation controls.
- `tests/expected-tests.txt` — Maintains the exact test inventory.
- `docs/release.md` — Records the v0.4 preparation contract and current evidence limits.

## Decisions Made

- Reused the validated support-claims profile because it already contained every managed v0.4 fact; no historical disclosure inputs or v0.3 outputs needed to change.
- Kept release workflow scheduling, token authority, supported platforms, and dependencies unchanged.
- REL-01 remains Pending until Plan 23-06 verifies actual release and consumer evidence.

## Deviations from Plan

None. The plan allowed extending `release-disclosure.json` only where needed; the immutable v0.4 profile already supplied the full managed copy.

## Issues Encountered

An earlier docs-check phrase matched negative publication wording as a positive claim. The guidance was reworded, and the checker now has a dedicated false-publication control. The final docs suite passes.

## User Setup Required

None.

## Next Phase Readiness

Plan 23-02 is complete. Continue to Plan 23-03, **Release content window and observed version gate**, which must inspect the actual release-please output before release preparation proceeds. REL-01 remains Pending; stop after Phase 23 and do not begin the milestone audit.

## Self-Check

PASSED — the RED assertion was semantic, all Plan 23-02 focused tests pass, coverage classifies both deliverables as automated, `verify-summary` passes, and the scope resolver finds all three task commits.

---
*Phase: GB-23-qualified-v0-4-0-release*
*Completed: 2026-11-04*
