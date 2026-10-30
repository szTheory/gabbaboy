# Proposed bounded migration: supported macOS ARM64 hosted runners

Status: approved by the owner on 2026-10-30 as D-126, selecting “Approve bounded runner migration (Recommended)”. PR #135 remains unmerged and the release window remains held until fresh qualification. This proposal expands the existing unmerged repair; it does not authorize an additional main merge or a new phase.

## Verified infrastructure blocker

PR #135's reviewed guard repair is at `b65b1efffe2990e3b4d3113bf593de6db5519bbc`. Its five required macOS job instances were cancelled before runner allocation (runner ID zero, empty steps), with annotations identifying GitHub's scheduled macOS 14 brownout. These cancellations are not test failures or passing evidence. Unaffected jobs may finish; none can substitute for the missing Mac qualification.

GitHub's [retirement announcement](https://github.com/actions/runner-images/issues/13518) schedules today's interruption from October 30 14:00 UTC through October 31 00:00 UTC and full retirement on November 2, 2026. Its [runner-image matrix](https://github.com/actions/runner-images/blob/main/README.md) identifies both `macos-14` and supported `macos-15` as ARM64. A pinned `macos-15` migration keeps the tested architecture while changing the hosted OS/toolchain. Waiting until 00:00 UTC permits a fresh macOS 14 attempt but leaves the imminent retirement unresolved.

## Recommended bounded scope

Expand the existing PR #135 before its one already-authorized guarded merge:

1. Change the five active job labels from `macos-14` to `macos-15`: `native-macos` and `macos-player-package` in `.github/workflows/ci.yml`; both Mac package jobs in `.github/workflows/preview.yml`; `candidate-macos` in `.github/workflows/release.yml`. Change the release build receipt's runner field with its job. Update README's current tested-host description.
2. Extend `.github/scripts/verify-workflow-policy.py` to require those five exact labels and the corresponding receipt value, with a positive control and a rejecting mutation for every pin and receipt drift. Use existing CTest/self-test wiring; update only its necessary inventory/floors if the added cases require it. Keep all prior controls and test budgets.
3. Independently review the expanded diff and run fresh exact-head protected CI, actual Mac package/consumer/player smoke, Windows/Linux checks and the unchanged performance gate. Preserve the brownout attempt as cancelled. No skipped or previous-head check qualifies the migration.
4. After qualification, follow D-125's existing guarded merge, real component-PR discovery/inactive judgment, release-please regeneration and fresh version-window sequence. Rehearsal and release must use the newly qualified runner configuration; no old artifact is relabeled as a new build.

## Compatibility and evidence limits

The documented matrix is a tested runner/configuration combination, explicitly not a minimum macOS version guarantee (`docs/release.md`). Neither the core nor SDL/player build currently sets a deployment target or verifies a minimum OS. This proposal does not invent or silently claim preservation of an unsupported minimum-OS promise. Inspect the actual previously qualified and new package binaries' architecture/minimum-version metadata, retain the observed values with their source/artifact identities, and accurately disclose the tested-host change. If evidence reveals an existing explicit compatibility promise or an unrelated correctness/security problem, stop for scope resolution rather than waiving it.

Read-only inspection of the actual qualified PR #134 player/core artifacts verified their API ZIP and embedded package digests and source identities. The player, SDL library, core runner and core archive object are ARM64 with minimum OS metadata 14.0 / SDK 14.5. This is an observed prior artifact baseline, not a promise that a macOS 15 rebuild retains it. New artifacts must be inspected and any difference disclosed. Detailed provenance and raw artifacts are retained in ignored `build/phase19-window/runner-migration-proposal/pr134-artifact-inspection.md`.

Leave historical digest-bound API captures and cited timing samples/budgets unchanged. The existing policy requires explanatory disclosure when a cited job body changes: add only the necessary disclosure strings to changed Mac job rows in `.github/ci-timeouts.json`, retaining every historical citation and numeric value. No emulator/API changes, dependency upgrades, deployment-target policy, permissions changes, timeout/performance weakening, assertion removal, tag/draft moves, additional main merge, or use of reserved post-tag plan 19-08. Owner JSON and automatic-advance flags remain untouched.

The owner approved this expansion because D-125 explicitly limits PR #135 to the discovery/policy/routing repair and excludes unrelated changes; migrating the hosted qualification environment broadens that approved scope. Keeping the release held requires no confirmation.

Completed stage: Phase 19 execution through Plan 19-06 and the D-123/D-124 hardening merge. Active stage: Phase 19 — Qualified v0.3.0 Release, pre-tag repair qualification. After approval, exact continuation: `/gsd-execute-phase 19`. Stop after Phase 19 execution at `/gsd-verify-work 19`; do not run it automatically or start another phase.
