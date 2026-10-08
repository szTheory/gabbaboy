---
phase: GB-06-qualified-dmg-release-and-consumer-handoff
plan: 07
subsystem: release
tags: [release-notes, legal-notices, GitHub-Releases, provenance, adopter-docs]

requires:
  - phase: GB-06-qualified-dmg-release-and-consumer-handoff
    provides: Downloaded-byte release workflow and packaged native consumer/save behavior from Plans 06-03 and 06-04
provides:
  - Reviewable v0.1 changelog and release/trust/recovery guide
  - Digest-indexed MIT fixture and SDL runtime notices
  - 23-capability GitHub API matrix with an explicit draft-to-published lifecycle
affects: [06-06, release-automation, adopters]

actuals:
  tokens: 3290
  tasks: 2
  commits: 2
commits: 2
plan_head_before: 34fadcdcb81eb33b3ba06a491a977b0d44e382c7
plan_head_after: 6017b8ffc3a7e623b52672578b364aa0873e5324

tech-stack:
  added: []
  patterns:
    - Separate the stable tracked support ledger from the source-bound post-tag sidecar.
    - State tested runner combinations and scoped model evidence without promising minimum OS or broad game support.

key-files:
  created:
    - CHANGELOG.md
    - THIRD_PARTY_NOTICES.md
    - docs/release.md
  modified:
    - .planning/phases/GB-06-qualified-dmg-release-and-consumer-handoff/COVERAGE.md

key-decisions: []
requirements-completed: [] # SHIP-03/04/08 remain gated on the exact-tag release work in Plan 06-06.

coverage:
  - id: D1
    description: Release notes, fixture/SDL notices, downloads, support scope, save recovery, and trust state are documented with manifest-backed digests.
    requirement: SHIP-03
    verification:
      - kind: integration
        ref: "bash tests/scripts/verify-release-candidate.sh --self-test (relocated C/C++ consumers and 10 negative receipt/extraction cases)"
        status: pass
      - kind: other
        ref: "Fixture ROM/manifest/license and pinned SDL license SHA-256 comparison against local bytes"
        status: pass
    human_judgment: true
    rationale: A reviewer must confirm legal/trust wording and adopter clarity; the release self-test validates bytes and workflows but does not interpret the public prose.
  - id: D2
    description: Every in-scope GitHub release API capability has an INTEGRATE or reasoned OPT-OUT disposition and explicit publication gates.
    requirement: SHIP-08
    verification:
      - kind: other
        ref: "gsd-tools check api-coverage.verify-pre .planning/phases/GB-06-qualified-dmg-release-and-consumer-handoff (23 capabilities: 17 integrate, 6 opt-out)"
        status: pass
      - kind: integration
        ref: "bash tests/scripts/verify-release-candidate.sh --self-test"
        status: pass
    human_judgment: false

duration: 7min
completed: 2026-10-08
status: complete
---

# Phase 6 Plan 7: Release Documentation and API Coverage Summary

**The v0.1 release docs now bind original fixture and pinned SDL notice digests to truthful DMG support, recovery, and a fully decided GitHub release lifecycle.**

## Performance

- **Duration:** 7 min
- **Started:** 2026-10-08T23:33:04Z
- **Completed:** 2026-10-08T23:39:50Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- Added a release-please-managed changelog, adopter release guide, and third-party notice ledger. Fixture manifest, ROM, source, and local notice digests match the checked-in bytes; the bundled SDL 3.4.18 license digest matches the pinned SDL source archive.
- Documented package verification, tested runner combinations, unsigned/not-notarized state, support limits, native API and host save ownership, upgrade/rollback recovery, and Playstead's future integration seam.
- Expanded the API matrix with the exact version PR, tag, single unpublished draft, exact-SHA candidate, byte-identical retry, one-way publication, readback, and post-publication lifecycle gates.

## Task Commits

Each task was committed atomically:

1. **Task 06-07-01: Finalize release notes, legal notices and adopter guide** — `57039c8` (`docs`)
2. **Task 06-07-02: Decide GitHub API capability coverage before tag** — `6017b8f` (`docs`)

**Plan metadata:** pending parent phase orchestration.

## Files Created/Modified

- `CHANGELOG.md` — release-please version PR owns numbered release notes.
- `THIRD_PARTY_NOTICES.md` — original MIT fixture identities and pinned SDL 3.4.18 runtime/license digests.
- `docs/release.md` — downloads, checksums, provenance, trust, upgrades, rollback, save recovery, and troubleshooting.
- `.planning/phases/GB-06-qualified-dmg-release-and-consumer-handoff/COVERAGE.md` — 23 API decisions, including lifecycle transitions and exact-byte gates.

## Decisions Made

Followed the locked Phase 6 decisions: the tracked support ledger stays versioned and source-independent, while a generated post-tag sidecar binds its tagged Git blob to the exact source SHA. Claims remain limited to the bootless DMG-CPU-B software model and observed runner combinations.

## Deviations from Plan

The `.git` directory is read-only in the workspace sandbox, so the plan-head ledger was persisted temporarily under this owned phase directory instead of `.git`. Task commits were made on the authorized phase branch with the approved Git-metadata operation. The temporary ledger will be removed after measuring the plan commit range.

**Total deviations:** 1 execution-environment workaround. **Impact:** no source or owner scratch was changed by the workaround.

## Issues Encountered

The state updater reported the parent session's Phase 6 milestone lock and skipped `state.update-progress` because the phase is not complete. The plan counter, session, metric, and roadmap handlers updated their respective files; progress remains 5/6 phases (83%), and this plan's 6/7 status is current. `.planning/state.json` was restored byte-for-byte (SHA-256 `c0c9f8c8071f7686db6a82e7e99b97b21da7f6a25c2dc018c139a8ca6ca041ef`). The required candidate self-test passed twice; the API coverage gate passed with 23 capabilities, 17 integrated and 6 reasoned opt-outs.

## User Setup Required

None - no external service configuration was required by this documentation and coverage plan.

## Next Phase Readiness

The pre-tag release documentation and API decisions are ready for inclusion in the protected version PR. Plan 06-06 remains the final gated work: verify the target repository's exact-head checks and merge eligibility, then qualify and publish only the same unpublished draft's downloaded assets. This plan did not create a tag or publish a release.

## Self-Check: PASSED

All four plan artifacts and this summary exist; both task commits are ancestors of the current branch. The changed artifacts contain no stub markers.

---
*Phase: GB-06-qualified-dmg-release-and-consumer-handoff*
*Completed: 2026-10-08*
