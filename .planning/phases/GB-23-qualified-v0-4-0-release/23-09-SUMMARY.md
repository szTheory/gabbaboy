---
phase: GB-23-qualified-v0-4-0-release
plan: "09"
subsystem: release-evidence
tags: [markdown, raw-html, release-notes, version-window]
requires:
  - phase: GB-23-qualified-v0-4-0-release
    provides: Immutable v0.4 claim inputs, generated release notes and the exact-version changelog gate.
provides:
  - Bounded refusal of incomplete raw-HTML openers in release-note and document evidence.
  - Matching changelog refusal with committed production-CLI controls before and inside the selected release section.
affects: [23-04, release-qualification, public-documents]
actuals:
  tokens: 4300
  tasks: 2
  commits: 4
tech-stack:
  added: []
  patterns:
    - Mask comments and code before applying a bounded fail-closed raw-HTML visibility check.
    - Exercise changelog visibility through the production CLI against disposable committed subjects.
key-files:
  created: []
  modified:
    - tests/scripts/verify-v02-adoption.py
    - tests/scripts/verify-version-window.py
key-decisions:
  - "Preserve the existing fail-closed diagnostics and Markdown masking; reject incomplete type-1, declaration and processing-instruction openers without adding a parser or dependency."
patterns-established:
  - "For each malformed changelog opener, accept the visible baseline immediately before committing a one-file hidden-proof fixture and require the exact visibility diagnostic."
requirements-completed: []
coverage:
  - id: RELEASE-NOTES-AND-DOCS-HTML-VISIBILITY
    description: "Release-note and README proof rejects incomplete raw-HTML openers while preserving renderer-built notes, visible disclosures and harmless masked examples."
    requirement: REL-01
    human_judgment: false
    verification:
      - kind: integration
        ref: "At 532535ec the notes self-test failed on the intended accepted `<script` reproducer; at 6369b051 the notes self-test passed with 2 positives and 72 controls, and the docs self-test passed with 466 checks and 109 rejected controls."
        status: pass
      - kind: integration
        ref: "At a63f1dc6 the focused phase1 CTest selection passed 9/9, including release_notes_v04_controls and v02_adoption_docs_controls."
        status: pass
  - id: CHANGELOG-HTML-VISIBILITY
    description: "The immutable 0.4.0 changelog gate rejects each reproduced incomplete opener before the release heading and before its ledger link, while visible relative/canonical links and masked examples pass."
    requirement: REL-01
    human_judgment: false
    verification:
      - kind: integration
        ref: "At 3fed435e the production-CLI self-test failed because `<script` before the heading hid the ledger link and was accepted. At a63f1dc6 `python3 -I tests/scripts/verify-version-window.py --self-test-version-v04 --repo .` passed with 63 positives and 66 controls; all nine opener variants were checked in both placements with `window-version-output-mismatch`, and the old matcher accepted the causal fixture."
        status: pass
      - kind: integration
        ref: "`cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error -j 1 -R '^(release_notes_v04|release_notes_v04_controls|v02_adoption_docs|v02_adoption_docs_controls|release_window_contract|release_window_controls|release_version_v04_controls|release_disclosure_generator|release_disclosure_controls)$'` passed 9/9 at a63f1dc67654613e105ac1071b7445f21adea0bc."
        status: pass
status: complete
duration: 10min
completed: 2026-11-04
---

# Phase 23 Plan 09: Close incomplete raw-HTML visibility bypasses

**Release notes, public disclosures and the immutable changelog gate now reject the reproduced incomplete raw-HTML openers with their existing scope-specific diagnostics.**

## Performance

- **Duration:** 10 min
- **Started:** 2026-11-04T13:07:05Z
- **Completed:** 2026-11-04T13:17:00Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- Extended the existing release-note and README visibility guard to reject incomplete script, pre and style starts, declarations and processing instructions after comment/code masking.
- Added production-path controls for all nine opener forms, visible counterparts, harmless masked examples and a causal legacy-matcher check.
- Extended the immutable changelog guard and committed-fixture CLI self-test to check every opener before the selected heading and inside its section before the only ledger link.
- Kept the existing relative/canonical destination parser, version-window schema, diagnostics, generated text, historical ledger and release authority unchanged.

## Task Commits

1. **Task 1: Release-note and document visibility controls/fix** — `532535ec` (red tests), `6369b051` (fix).
2. **Task 2: Immutable changelog visibility controls/fix** — `3fed435e` (red tests), `a63f1dc6` (fix).

## TDD Evidence

- **Task 1 RED:** The release-note self-test failed because the incomplete `<script` reproducer was accepted. The docs self-test also failed because the required disclosure remained accepted under the old matcher.
- **Task 1 GREEN:** At `6369b051`, release-note controls passed with 2 positives and 72 controls; docs controls passed with 466 checks and 109 rejected controls. Closed comments, fenced/indented/inline code, and escaped tag-like examples remained accepted.
- **Task 2 RED:** At `3fed435e`, the production CLI accepted a committed changelog with `<script` before the release heading, so the new `window-version-output-mismatch` assertion failed as intended.
- **Task 2 GREEN:** At `a63f1dc6`, the version self-test passed 63 positives and 66 controls, including both placements for all nine openers, relative and canonical ledger links, masked examples and the legacy-matcher causal control.
- **Focused build and CTest:** Configure and build completed at `a63f1dc6`; the nine selected notes, docs, window and disclosure tests passed serially.

## Files Modified

- `tests/scripts/verify-v02-adoption.py` — Rejects incomplete raw-HTML openers in release-note and document proof while preserving masking behavior.
- `tests/scripts/verify-version-window.py` — Rejects the same openers in immutable changelog validation and exercises each through committed production-CLI fixtures.

## Decisions Made

Followed the approved bounded fix: retain the standard-library implementation and existing fail-closed policy, diagnostics and masking rules. No parser, dependency, release mechanism or registration was added.

## Deviations from Plan

None. The causal test helper needed a `global` declaration for its temporary matcher swap; that test-only correction was included before the green run.

## Issues Encountered

The red changelog case reproduced the bypass. The first green attempt exposed a Python scoping error in the causal test helper; after correcting the declaration, the complete self-test passed.

## User Setup Required

None.

## Next Phase Readiness

Plan 23-09 is complete. Plan 23-04 is next: keep its historical reports unchanged until three independent reviewers reissue them against the final implementation head, then require the direct report gate and registered review tests. REL-01 remains Pending; no release qualification or publication is claimed.

## Self-Check: PASSED

Both intended red outcomes were observed; the notes/docs and version self-tests pass at their committed fixes; configure/build and the focused 9/9 CTest gate pass at the fixed changelog source; and the coverage block follows the Phase 23 schema.

---
*Phase: GB-23-qualified-v0-4-0-release*
*Completed: 2026-11-04*
