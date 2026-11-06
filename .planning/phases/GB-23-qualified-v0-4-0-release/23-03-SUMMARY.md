---
phase: GB-23-qualified-v0-4-0-release
plan: "03"
subsystem: release-evidence
tags: [version-window, release-please, immutable-content]
requires:
  - phase: GB-23-qualified-v0-4-0-release
    provides: Source-bound v0.4 support claims and concise release disclosure from Plans 23-01 and 23-02.
provides:
  - Immutable release content window covering v0.4 claim inputs and generated public outputs.
  - Exact expected-version gate for generated CMake, manifest, support-ledger and changelog identity.
affects: [23-04, 23-05, release-qualification]
actuals:
  tokens: 8792
  tasks: 2
  commits: 4
tech-stack:
  added: []
  patterns:
    - Explicit expected versions validate all generated identity from immutable Git blobs.
    - Release notes reuse the existing version-bound adoption checker.
key-files:
  created: []
  modified:
    - tests/scripts/verify-version-window.py
    - tests/CMakeLists.txt
    - tests/expected-tests.txt
key-decisions:
  - "Keep the tracked development version at 0.3.0 and the release window inactive until the actual release-please output is observed."
patterns-established:
  - "An explicit release version checks the CMake and manifest triplet, versioned ledger heading, first changelog section and its ledger link against the judged commit."
  - "Supplied release notes are delegated to the existing adoption checker after the active content window passes."
requirements-completed: []
coverage:
  - id: RELEASE-CONTENT-WINDOW
    description: "The immutable content window binds all managed v0.4 claims, generator inputs, generated public outputs, source, base, record and version-PR body, and rejects omitted or changed bindings."
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest --preset phase1 --output-on-failure --no-tests=error -R '^(release_window_contract|release_window_controls)$'"
        status: pass
      - kind: integration
        ref: "verify-version-window.py --self-test: 11 positive cases and 64 omission/mutation controls passed."
        status: pass
  - id: RELEASE-EXPECTED-VERSION
    description: "An explicit 0.4.0 request accepts the complete matching generated subject and rejects wrong or mixed versions, missing or mislabeled ledger output, wrong changelog identity/link, inactive freeze records, malformed expectations and invalid release notes."
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest --preset phase1 --output-on-failure --no-tests=error -R '^(release_window_contract|release_window_controls|release_version_v04_controls)$'"
        status: pass
      - kind: integration
        ref: "verify-version-window.py --self-test-version-v04: 4 positive subjects and 12 wrong-version/mixed-output controls passed."
        status: pass
status: complete
duration: 25min
completed: 2026-11-04
---

# Phase 23 Plan 03: Release content window and observed version gate

**The release window now binds all v0.4 public-copy inputs, and an explicit 0.4.0 request rejects mismatched generated output before release preparation.**

## Performance

- **Duration:** 25 min
- **Started:** 2026-11-04T03:05:06Z
- **Completed:** 2026-11-04T03:30:06Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- Bound both support-claim profiles, release disclosure, renderer and notes validator, release-please config, candidate assessments, diagnostic inventory, and inherited state evidence inputs into the immutable content window.
- Classified CMake, manifest, changelog and version-derived support ledger as generated outputs and added omission/mutation controls for every managed input and generated record entry.
- Added `--expect-version X.Y.Z` checks for CMake/manifest agreement, active-record identity, versioned ledger filename and heading, and the first changelog release section and ledger link. Supplied release notes use the existing adoption checker.
- Registered `release_version_v04_controls`; its disposable committed subjects accept complete 0.4.0 output and reject 0.3.0, 0.3.1, 0.4.1, mixed and incomplete output, and incorrect notes.
- Kept the real development version at 0.3.0, the window record inactive, and REL-01 Pending. The actual hosted release-please output remains unobserved.

## Task Commits

1. **Task 1: Bind the full v0.4 claim and public-copy input set into the content window** — `7a18c365` (RED), `484edb5b` (implementation).
2. **Task 2: Require observed exact 0.4.0 output before release preparation can proceed** — `1eb5f2f3` (RED), `d530bd88` (implementation).

## TDD Evidence

- **Task 1 RED:** `release_window_controls` failed because an active record could omit `tests/data/support-claims-v0.4.json`; the target assertion failed as intended. Evidence: `build/tdd-red-evidence/23-03-T1-red.json` and `23-03-T1-red.xml`; classifier returned `RED_EVIDENCE_OK`.
- **Task 1 GREEN:** The content-window contract and 64 omission/mutation controls passed. `cmake --preset phase1`, `cmake --build --preset phase1`, and the focused `release_window_contract` / `release_window_controls` CTests passed.
- **Task 2 RED:** `release_version_v04_controls` failed because the checker accepted an internally consistent 0.3.0 subject under `--expect-version 0.4.0`; classifier returned `RED_EVIDENCE_OK`. Evidence: `build/tdd-red-evidence/23-03-T2-red.json` and `23-03-T2-red.xml`.
- **Task 2 GREEN:** The version-window contract, existing controls and new v0.4 version controls passed 3/3. The version self-test passed four positive cases and twelve negative controls; Python compilation and `git diff --check` passed.

## Files Modified

- `tests/scripts/verify-version-window.py` — Adds full managed-input coverage, exact expected-version validation and disposable committed output controls.
- `tests/CMakeLists.txt` — Registers the exact v0.4 output control.
- `tests/expected-tests.txt` — Adds the control to the required test inventory.

## Decisions Made

- Kept the real source tree and inactive record at 0.3.0. Synthetic 0.4.0 subjects exercise the gate without claiming release-please behavior before its actual output exists.

## Deviations from Plan

None. The actual release-please output remains a later live gate as planned.

## Issues Encountered

The first RED run showed the intended defect: `--expect-version` was accepted by the parser but did not affect the judged tree. The exact-version implementation closed that gap, and the focused regression set passed.

## User Setup Required

None.

## Next Phase Readiness

Plan 23-03 is complete. Continue with Plan 23-04, **Independent review evidence and implementation-head qualification**. Plan 23-05 must still inspect actual release-please output before any freeze, rehearsal or tag; REL-01 remains Pending. Stop after Phase 23 and do not start the v0.4 milestone audit.

## Self-Check

PASSED — both TDD RED records classify as `RED_EVIDENCE_OK`; the focused three-test CTest selection passes; the summary coverage block is machine-classifiable; and the evaluation-scope resolver finds all four task commits.

---
*Phase: GB-23-qualified-v0-4-0-release*
*Completed: 2026-11-04*
