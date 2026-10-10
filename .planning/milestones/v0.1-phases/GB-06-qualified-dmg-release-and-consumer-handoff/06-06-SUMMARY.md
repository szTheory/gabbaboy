---
phase: GB-06-qualified-dmg-release-and-consumer-handoff
plan: 06
subsystem: release
tags: [github-actions, release-please, sha256, exact-head, consumer-smoke]
requires:
  - phase: GB-06-qualified-dmg-release-and-consumer-handoff
    provides: platform packages, support ledger, performance/safety evidence, release documentation
provides:
  - Published v0.1.0 release with source-bound evidence and 18 verified assets
  - Protected exact-head source proof and post-publication inventory verifier
affects: [release, consumer-handoff, phase-verification]
actuals:
  tokens: 2100
  tasks: 2
  commits: 2
tech-stack:
  added: []
  patterns: [guarded single publish transition, direct JSON API inventory readback]
key-files:
  created: [.github/scripts/verify-published-release-assets.py]
  modified: [.github/workflows/release.yml, tests/scripts/verify-release-candidate.sh]
key-decisions:
  - "Published v0.1.0 remains bound to frozen product source e30d168f7fc61de8db0a3801e7b1736362912cb7."
  - "The exact player remains explicitly unsigned, not notarized, and not hardware-qualified."
patterns-established:
  - "Parse API response JSON as data; never probe a potentially large response string as a filesystem path."
  - "Self-test the ordering of the one-way publication command after the final downloaded-byte gate."
requirements-completed: [SHIP-01, SHIP-02, SHIP-03, SHIP-04, SHIP-05, SHIP-06, SHIP-07, SHIP-08]
coverage:
  - id: D1
    description: "Publish exact qualified limited-DMG packages and evidence for v0.1.0."
    requirement: SHIP-03
    verification:
      - kind: integration
        ref: "GitHub release 407367131; tag v0.1.0 at e30d168f7fc61de8db0a3801e7b1736362912cb7"
        status: pass
      - kind: integration
        ref: "Fresh 18-asset download compared with API IDs, sizes, and SHA-256 digests; SHA256SUMS checked"
        status: pass
    human_judgment: false
  - id: D2
    description: "Protect publication with exact-head checks, byte qualification, and fail-closed postpublish readback."
    requirement: SHIP-08
    verification:
      - kind: integration
        ref: "PR #31 merged at 360c3988ef1c58d549b090f8f61dc5447ce9c22c after exact-head protected checks"
        status: pass
      - kind: unit
        ref: "verify-release-gates.sh --self-test; verify-release-candidate.sh --self-test; verify-published-release-assets.py --self-test"
        status: pass
    human_judgment: false
duration: 95min
completed: 2026-10-09
status: complete
plan_head_before: a252c6bbbbe4a181a93479a8272c01732882bc34
plan_head_after: df1def9aa956b4ff8e9ea13b591225ff8b4c5336
commits: 2
---

# Phase GB-06 Plan 06: Qualified DMG Release and Consumer Handoff Summary

**Published the exact, smoke-qualified v0.1.0 release and reconciled its complete downloaded inventory to the frozen source and pre-publish evidence.**

## Accomplishments

- Published GitHub release [v0.1.0](https://github.com/szTheory/gabbaboy/releases/tag/v0.1.0), release ID `407367131`, with tag target `e30d168f7fc61de8db0a3801e7b1736362912cb7`. No product source or version changes were made after tagging.
- The release has exactly 18 assets. The original 16 qualified assets retain their pre-publish IDs, names, sizes, API digests, and bytes; `SHA256SUMS` and `release-receipt.json` are the only final additions. A fresh download matched all 18 API digests, all 16 manifest entries passed `sha256sum --check`, and both platform digest-only sidecars passed.
- Source receipt and merged PR #13 exact-head checks agree; the post-tag support sidecar verifies against the tagged ledger and source SHA. Candidate and platform manifests bind to the same source. The performance receipt records a passed run, equal trace-pair digest, and 12 successful exact-source hosted check records.
- The published metadata truthfully records unsigned, not notarized, and not hardware-qualified status. Downloaded Linux, macOS, Windows, and macOS player smoke lanes succeeded before publication.
- PR #31 merged through branch protection at `360c3988ef1c58d549b090f8f61dc5447ce9c22c`. Its Release Please workflow completed successfully and opened no product version PR.
- PR #33 added a negative ordering regression and merged through protection at `f6c7f0231b353e25bd0e9ee6c8d5b9c9026b5934`; its Release Please workflow also completed successfully without a product version PR.

## Task Commits

1. **06-06-01: Prove bot PR and release eligibility** — protected source PR #13 merged at `e30d168f7fc61de8db0a3801e7b1736362912cb7`; required exact-head checks passed and the immediate `v0.1.0` tag and draft were verified.
2. **06-06-02: Publish exact verified release and handoff** — one guarded publication transition completed in hosted run [37871929616](https://github.com/szTheory/gabbaboy/actions/runs/37871929616); later readback reconciliation passed after the CI-only repair in PR #31.

Plan control-plane repair commit: `fa5857d6e71c482c930feb17c3edf6fc583afb27` (`ci(06-06): fix published release verification`), merged by PR #31.

Publication-order regression commit: `df1def9aa956b4ff8e9ea13b591225ff8b4c5336` (`test(06-06): reject publish before byte gate`), rebased for PR #33 and merged through PR commit `f6c7f0231b353e25bd0e9ee6c8d5b9c9026b5934`.

## Files Created/Modified

- `.github/scripts/verify-published-release-assets.py` — verifies published API asset metadata against the frozen qualified inventory and includes direct-JSON and negative self-tests.
- `.github/workflows/release.yml` — routes published asset metadata through the dedicated verifier after the single guarded publication transition.
- `tests/scripts/verify-release-candidate.sh` — verifies the publication command occurs after the final draft-byte gate and tests the readback verifier contract.

## Decisions Made

- Keep the first release as `v0.1.0`, aligned with CMake, tagged support ledger, consumer documentation, receipts, and asset contract.
- Keep the release immutable after its one publish transition. Post-tag repairs were limited to CI and verifier control-plane code; no rebuild, replacement upload, source edit, or second publication occurred.
- Retain explicit unsigned/not-notarized and software-model-only qualifications.

## Deviations from Plan

### Post-tag control-plane corrections

1. Earlier guarded retries exposed workflow path, receipt identity, archive portability, compiler receipt, digest-sidecar, asset readback, and exact-head proof representation defects. Each correction was restricted to release-control-plane workflow/verifier paths and landed through protected exact-head PR checks before the single successful publish transition. Product source, version, tag, and already-qualified attachment bytes remained frozen.
2. The publish run completed the exact draft-byte gate and single publish transition, then its post-publish readback raised `OSError: [Errno 36] File name too long` because it called `Path.is_file()` on the JSON string returned by `gh api`. PR #31 replaced this with direct JSON parsing and a self-test; a fresh post-merge read-only download verified the live inventory.
3. The candidate self-test initially rejected any `gh release edit` occurrence, including the intended gated publish command. PR #31 changed it to assert that `--check-draft-final` precedes the one-way command. PR #33 added a negative test that moves the publish command ahead of the final gate and verifies rejection. The complete candidate self-test now passes.

**Impact:** All hosted release qualification and publication gates passed before the one-way transition. The final workflow run is marked failed solely because of the post-transition readback exception; live release API state and fresh downloaded bytes independently reconcile, and the repaired verifier passes local self-tests. No public release bytes were changed by the repair.

## Issues Encountered

- Early release attempts failed closed on stale/shared readback paths, runner evidence representation, API permission assumptions, and digest/readback contract mismatches. The final run was authorized only after those control-plane fixes were protected and the same draft/tag/source and existing attachment IDs/digests were rechecked.
- The owner’s planning scratch remains untouched and unstaged: `.planning/HANDOFF.json`, `.planning/config.json`, `.planning/context/DECISIONS.md`, Phase 3 context/research files, `.planning/state.json`, and `.planning/milestone.lock`. The state file SHA-256 remains `b87db442e46b4fee9d6ed1ddcd2315275acb449cfb238796a8b0887db6b36742`.

## User Setup Required

None. Apple signing and notarization credentials were not configured; the release is accurately labeled unsigned and not notarized.

## Next Phase Readiness

Plan 06-06 and Phase 6 goal-backward verification are complete: all five roadmap truths passed and SHIP-01 through SHIP-08 are satisfied. The published 18-asset inventory is reconciled, the current local CTest inventory passed 176/176, and code review has zero open findings. The milestone audit is the next workflow stage; do not begin a new milestone until the owner reviews that audit.

## Self-Check: PASSED

- Summary file exists at the plan output path.
- Control-plane commit `fa5857d6e71c482c930feb17c3edf6fc583afb27` is present in the current plan branch history.
- Publication-order test commit `df1def9aa956b4ff8e9ea13b591225ff8b4c5336` is present in the current plan branch history; its rebased equivalent merged as PR #33.
- Owner scratch remains unstaged, and `.planning/state.json` retains its original SHA-256.

---
*Phase: GB-06-qualified-dmg-release-and-consumer-handoff*
*Completed: 2026-10-09*
