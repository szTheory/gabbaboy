---
phase: GB-22-composition-and-microtest-evidence
plan: "11"
subsystem: testing
tags: [diagnostics, immutable-evidence, no-go, exact-head, phase-boundary]
requires:
  - phase: GB-22-composition-and-microtest-evidence
    provides: Synthetic tracer, metadata assessment, immutable no-go checker and mutation controls
provides:
  - Independently reviewed synthetic-plus-metadata evidence and Phase 22 boundary evidence
  - Exact record-blob and ancestry controls for the Phase 21 squash-reference mapping
  - Narrow configured-inventory planning classification with interpreter and argv controls
affects: [diagnostic-admission, phase-23-release-evidence]
tech-stack:
  added: []
  patterns:
    - Bind admission checker, policy, evidence records and interpreter to immutable identities
    - Keep fixture no-go separate from synthetic runner and metadata evidence
    - Planning inventory exceptions require the exact configured checker invocation
key-files:
  created:
    - .planning/phases/GB-22-composition-and-microtest-evidence/22-UAT.md
  modified:
    - CMakeLists.txt
    - tests/scripts/verify-diagnostic-admission.py
    - tests/scripts/verify-diagnostic-evidence.py
    - tests/scripts/verify-cgb-progress.py
    - tests/scripts/verify-cgb-candidates.py
    - tests/scripts/verify-planning-labels.py
    - tests/scripts/verify-no-phase-paths.py
    - tests/scripts/run-acid2-local.py
    - tests/CMakeLists.txt
    - tests/cmake/ci-lanes.cmake
    - tests/data/cgb-candidates/ucity-1.3.json
    - tests/expected-tests.txt
    - .planning/ROADMAP.md
    - .planning/STATE.md
    - .planning/state.json
    - .planning/phases/GB-22-composition-and-microtest-evidence/.continue-here.md
    - .planning/phases/GB-22-composition-and-microtest-evidence/22-EVIDENCE.md
    - .planning/phases/GB-22-composition-and-microtest-evidence/22-VALIDATION.md
    - .planning/phases/GB-22-composition-and-microtest-evidence/22-REVIEW.md
    - .planning/phases/GB-22-composition-and-microtest-evidence/22-SECURITY.md
actuals:
  tokens: 35845
  tasks: 3
  commits: 21
key-decisions:
  - "Keep all seven real-fixture gates unresolved and stop at Phase 22; Phase 23 remains owner-controlled."
  - "Retarget the Phase 21 primary-record pointer to PR #140's squash commit only after exact record-blob identity was established; keep digest and ancestry mutants."
  - "Reduce the completed Phase 21 plan cap to 10, preserving two reserve slots and a four-phase combined cap of 40."
  - "Allow the planning lane to inspect only the configured CTest inventory through a tightly pinned command; compiled artifacts remain excluded."
requirements-completed: []
coverage:
  - id: D1
    description: "The immutable assessment retains 513 metadata cases and refuses real admission with all seven gates unresolved; payload and dependency mutants are refused."
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest --preset phase1 --output-on-failure --no-tests=error -R '^(phase22_.*)$': immutable evidence contract, payload controls, and source-archive controls"
        status: pass
      - kind: other
        ref: "python3 -I tests/scripts/verify-diagnostic-evidence.py --check --repo-root . --source-revision 06d2cbc1e0ceaa100cc0ecc28826e39794a73f04 --build-dir build"
        status: pass
      - kind: other
        ref: "verify-diagnostic-admission.py --self-test-controls passed 12 controls; --require-approved exited 2 with the seven unresolved gates"
        status: pass
  - id: D2
    description: "Synthetic composition, existing fixture/product boundaries and fixed budgets pass; independent source and security reviews found no unresolved source issue."
    human_judgment: false
    verification:
      - kind: integration
        ref: "Focused phase1 CTest selection at 24c4e191 passed 23/23, including Phase 22, Phase 21 candidate/history, fixture repository, core/player product, planning-label, cap, path and budget controls"
        status: pass
      - kind: integration
        ref: "At reviewed source 06d2cbc1, the configured planning/evidence CTest selection passed 4/4; the planning inventory check passed for 1732 tests / 47 planning labels"
        status: pass
      - kind: integration
        ref: "Configured full CTest suite at 042e7f34 passed 1732/1732 tests in 495.43 seconds; the exact final tracked head is checked once more before PR qualification"
        status: pass
      - kind: other
        ref: "22-REVIEW.md and 22-SECURITY.md: exact reviewed source 06d2cbc1e0ceaa100cc0ecc28826e39794a73f04; source findings clean"
        status: pass
      - kind: other
        ref: "verify-summary-coverage.py passed for 22-01, 22-02, 22-10 and this block; Plan 22-02 D2 is automated with human_judgment false"
        status: pass
  - id: D3
    description: "The point-in-time boundary preserves Pending requirements, false automatic advance, all seven no-go gates and the owner-controlled Phase 23 route."
    human_judgment: false
    verification:
      - kind: other
        ref: "verify-diagnostic-evidence.py --check-boundary --repo-root . --source-revision 06d2cbc1e0ceaa100cc0ecc28826e39794a73f04 --boundary-revision 4ac46e7406329efbd4fb6ac0dc39c86c14156691"
        status: pass
      - kind: other
        ref: "verify-uat-closure.py generated 10/10 automated entries; self-test passed 21 controls"
        status: pass
metrics:
  duration: "about two hours through the final local suite"
  completed: "2026-11-03"
status: complete
plan_head_before: 7f57dcc3542fb274f74257f48c6cd9d1c7e49741
plan_head_after: 042e7f34e6d759d97e06a6460dcfc922aec4dbfd
commits: 21
---

# Phase 22 Plan 11: Final Qualification and Boundary Summary

**The immutable diagnostic no-go and synthetic evidence are independently checked; exact-head PR evidence determines whether the Phase 22 boundary closes.**

## Accomplishments

- Closed the renamed-payload and mutable Phase 20 dependency findings with negative controls. Admission remains bound to immutable source blobs and refuses added payload variants.
- Fixed Phase 21 history checks to skip commits predating the checker, isolated synthetic history tests from global Git hooks/signing, and kept controls for stale source bytes and hook non-execution.
- Retargeted only the fallback's primary no-go commit pointer to PR #140's squash merge after verifying that the referenced JSON record's Git blob and SHA-256 match. Candidate controls reject non-ancestor references and digest mismatches.
- Added a narrowly scoped planning-inventory classification for the immutable Phase 22 contract. Its 17 controls reject missing classification, binary paths, extra output flags, `python -c` substitution and an absolute Python stub; the active configured Python and build directory are pinned.
- Recorded the Phase 21 cap reduction to 10: eight plan files leave two reserve slots, keeping the four-phase total at 40.
- Refreshed source review, security, evidence, validation and automated closure while retaining all Pending requirements and the Phase 23 owner route.

## Verification

- The broad focused CTest selection passed 23/23 in 42.98 seconds. The latest source-specific planning/evidence selection passed 4/4, and the configured inventory contained 1,732 tests with 47 planning-labelled tests.
- The configured full CTest suite passed 1,732/1,732 in 495.43 seconds at `042e7f34`; the authoritative final-head configure/build/full-suite result is recorded in `build/phase22/remote-evidence.json`.
- The immutable diagnostic evidence check reports 513 metadata cases, seven unresolved gates, zero admitted, and zero executed. The admission mutation suite passed 12/12; real approval correctly refuses with exit 2.
- Phase21 candidate/history, no-phase-path, plan-cap, Acid2 malformed-manifest, fixture-admission, core/player product, and budget controls passed. Plan cap check reports four phases and 28 plan files.
- Independent code and security reviews are clean at source `06d2cbc1e0ceaa100cc0ecc28826e39794a73f04`. The exact final local rerun and PR #142 exact-head outcomes are recorded in `build/phase22/remote-evidence.json`; those required checks, artifacts, reviews, protection checks, and merge-tree equality passed before the PR merged as `ca2f0be6`.

## Decisions and Limits

- DIAG-01, DIAG-02 and RIGHTS-01 remain Pending with their original definitions; RIGHTS-01 remains owned by Phase 20.
- No upstream ROM/reference payload, upstream build or program, real fixture admission, real diagnostic result, or license prohibition is claimed.
- Phase 23 — Qualified v0.4.0 Release — remains unstarted. Its owner-controlled route is `/gsd-discuss-phase 23`; both automatic-advance flags remain false.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Reject renamed archives and diagnostic payloads**
- **Found during:** Task 1 review.
- **Issue:** The path guard accepted `.rar`, `.zst`, `.dat`, and extensionless payload variants.
- **Fix:** Added bounded path/content signature checks and negative controls for archive, image, ROM and SVG variants.
- **Files modified:** `tests/scripts/verify-diagnostic-evidence.py`.

**2. [Rule 2 - Security] Bind Phase 20 checker and policy to immutable source**
- **Found during:** Task 1 security review.
- **Issue:** Mutable Phase 20 checker/policy bytes could affect approval.
- **Fix:** Compare each worktree file with the selected commit blob before invoking the checker; add separate mutation refusals.
- **Files modified:** `tests/scripts/verify-diagnostic-admission.py`.

**3. [Rule 3 - Blocking issue] Preserve source-archive configuration while evidence fails closed**
- **Found during:** Source-archive control.
- **Issue:** Tests-enabled no-Git archives could not configure.
- **Fix:** Keep evidence source-bound and fail closed when revision identity is unavailable while allowing the existing source-archive control to configure.
- **Files modified:** `CMakeLists.txt`, `tests/CMakeLists.txt`.

**4. [Rule 1 - Bug] Skip history entries before the progress checker existed**
- **Found during:** Full-suite gap round.
- **Issue:** Missing historical paths were treated as invalid source bytes.
- **Fix:** Skip commits without the checker path; retain absent-path and stale-source controls. Synthetic commits explicitly suppress hooks and signing even under hostile global configuration.
- **Files modified:** `tests/scripts/verify-cgb-progress.py`.

**5. [Rule 3 - Blocking issue] Reconcile the Phase 21 squash-reference and planning inventory checks**
- **Found during:** Full-suite gap round and independent final review.
- **Issue:** The historical pointer was no longer an ancestor after squash merge; planning evidence used the active configured CTest inventory but the generic lane checker classified any build-directory argument as a built-artifact dependency.
- **Fix:** Retarget only the primary-record commit pointer after exact path/blob/digest verification and retain ancestry/digest mutants. Add an inventory-only classification pinned to one test name, exact checker, immutable source, active build directory, configured Python executable and exact argument sequence; keep executable/flag/interpreter bypass controls. The malformed Acid2 parser case remains a synthetic self-test; its production CTest asserts the earlier immutable scope refusal.
- **Files modified:** `tests/data/cgb-candidates/ucity-1.3.json`, `tests/scripts/verify-cgb-candidates.py`, `tests/scripts/verify-planning-labels.py`, `tests/CMakeLists.txt`, `tests/cmake/ci-lanes.cmake`, `tests/scripts/run-acid2-local.py`, `tests/expected-tests.txt`.

**Total deviations:** 5 scoped fixes within the authorized review/gap bounds. No package install, fixture addition, real diagnostic, or release action occurred.

## Deferred Issues

- The seven real-fixture evidence gates remain unresolved; no real diagnostic fixture was admitted or executed, and DIAG-01, DIAG-02, and RIGHTS-01 remain Pending. No license prohibition is inferred.

## Self-Check: PASSED

The summary exists, its recorded task commits are ancestors of the current branch head, and its coverage uses the required block schema with automated passing references.

## Final Phase Qualification

The final configured suite passed 1,732/1,732 at exact PR #142 head `9cb92b0f344b884d5f3e7179740ff5bc87eae379`. The required CI, fixture-reproduction, and package-preview checks and artifacts passed for that exact head; the fresh code and security reviews were clean; strict branch protection was satisfied without bypass; and the merged tree matched the qualified tree. PR #142 squash-merged as `ca2f0be6b38e7dd22e0eb3296b9a21cceed1a765`. Phase 22 is complete at the approved metadata-only scope. Phase 23 remains unstarted and owner-controlled through `/gsd-discuss-phase 23`.
