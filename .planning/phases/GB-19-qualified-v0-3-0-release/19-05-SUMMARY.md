---
phase: GB-19-qualified-v0-3-0-release
plan: "05"
subsystem: release
tags: [v0.3.0, ci, perf-gate, release-receipts, host-smoke, readback]
requires:
  - phase: GB-19-qualified-v0-3-0-release/19-04
    provides: exact-source release rehearsal binding and post-tag endpoint replay inventory
provides:
  - CI-bound perf-gate receipts with same-run trusted verification and retry evidence
  - Host-smoke results bound to Linux/macOS archive bytes and explicit Windows applicability
  - A tag-bound, source-inventory readback checker with digest, ledger-blob, privacy and idempotency controls
affects: [GB-19-qualified-v0-3-0-release/19-06, GB-19-qualified-v0-3-0-release/19-07]
actuals:
  tokens: 35936
  tasks: 4
  commits: 8
plan_head_before: 0022a3e5dc9ecef487cd2466d69d8cb770a774a5
plan_head_after: 59305f4ea79d8f5f8c11164972eba7805f6540a9
tech-stack:
  added: []
  patterns: [same-run CI artifact receipts, archive-byte host smoke, pre-publish inventory sourcing, exact-schema readback verification]
key-files:
  created: []
  modified:
    - .github/scripts/release-evidence-lifecycle.sh
    - .github/scripts/verify-workflow-policy.py
    - .github/workflows/ci.yml
    - .github/workflows/release-rehearsal.yml
    - .github/workflows/release.yml
    - tests/CMakeLists.txt
    - tests/cmake/ci-lanes.cmake
    - tests/cmake/perf.cmake
    - tests/expected-tests.txt
    - tests/scripts/run-perf-gate.sh
    - tests/scripts/test_installed_host.py
    - tests/scripts/verify-perf-gate.py
    - tests/scripts/verify-release-lifecycle.py
    - tests/scripts/verify-v02-consumers.py
    - tests/scripts/verify-v02-delivery.py
    - tests/scripts/verify-v03-dispositions.py
key-decisions:
  - "OQ-2: embed the verified perf_gate block in the existing release-receipt.json and leave the published asset list unchanged."
  - "Consumer receipts carry an explicit platform so not-applicable host smoke is accepted only for Windows."
  - "Readback asset identity comes from the raw pre-publish artifact; only the two final metadata assets are added at publication."
  - "REL-01 stays pending until exact-tag publication and committed readback are verified."
patterns-established:
  - "A release artifact is bound to the exact producer workflow run, attempt, source SHA and immutable limits blob."
  - "Readback checks consume an immutable revision and compare published digests to independently sourced pre-publish inventory."
requirements-completed: []
coverage:
  - id: SC3-PERF-RECEIPT
    description: The deterministic performance gate emits a receipt before its verdict, retries only realtime misses, retains the deciding attempt, and the release reader verifies the same CI run.
    requirement: REL-01
    human_judgment: false
    verification:
      - kind: unit
        ref: "d91fae38e108ab65b93695a5350a418c1dddc547: verify-perf-gate.py --self-test-receipt and run-perf-gate.sh --self-test-retry; exact ratio boundary, malformed timing with Ir-overrun precedence, receipt-on-red, and deciding-attempt controls passed."
        status: pass
      - kind: integration
        ref: "d91fae38e108ab65b93695a5350a418c1dddc547: workflow_policy_controls final run 47.11 s, 437 negative controls; registered TIMEOUT remains 180 s. Runtime and control count are separate measurements."
        status: pass
  - id: SC3-PRE-PUBLISH-INVENTORY
    description: The final pre-publish asset inventory is persisted before publication, sourced into the readback, and the new post-tag API forms are replayed or policy-pinned.
    requirement: REL-01
    human_judgment: false
    verification:
      - kind: integration
        ref: "59305f4ea79d8f5f8c11164972eba7805f6540a9: ctest --test-dir build -R '^(release_lifecycle_post_tag_controls)$' --output-on-failure --no-tests=error; passed in 26.20 s with the existing TIMEOUT=60 and registered 80-control minimum."
        status: pass
      - kind: unit
        ref: "b04fdab368c086b1875f426ed80e3b74340ff49d: release-pre-publish-inventory-${{ github.run_id }}-${{ github.run_attempt }} is uploaded before nightly-gate/publish-draft; POST_TAG_ENDPOINTS adds `gh api repos/{}/actions/runs/{}` as replayed:ci_run and `gh run download {} --name perf-gate-{}-{}` as pinned:perf_gate_artifact_name."
        status: pass
      - kind: integration
        ref: "b04fdab368c086b1875f426ed80e3b74340ff49d: final workflow_policy_controls run 43.16 s, 441 negative controls; policy TIMEOUT remains 180 s."
        status: pass
  - id: SC3-HOST-SMOKE
    description: Linux and macOS consumer receipts require a passing smoke against extracted release archive bytes; Windows records host smoke as not applicable.
    requirement: REL-01
    human_judgment: false
    verification:
      - kind: unit
        ref: "98f84196074ab9c8fd331180521a80762a2e1e01: installed_host_smoke and v02_delivery_controls passed; Linux/macOS missing or failed smoke and Windows passed-mode mutants are refused."
        status: pass
      - kind: integration
        ref: "98f84196074ab9c8fd331180521a80762a2e1e01: v02_consumer_controls_c passed in 28.31 s and v02_consumer_controls_cpp passed in 26.03 s."
        status: pass
      - kind: integration
        ref: "98f84196074ab9c8fd331180521a80762a2e1e01: workflow_policy_controls final run 44.97 s, 446 negative controls; policy TIMEOUT remains 180 s. Runtime and control count are separate measurements."
        status: pass
  - id: SC3-READBACK
    description: The v0.3 readback reconciles tag/tree, sourced asset ids and digests, SHA256SUMS, release-receipt, support-ledger blob and private-text rules deterministically.
    requirement: REL-01
    human_judgment: false
    verification:
      - kind: unit
        ref: "59305f4ea79d8f5f8c11164972eba7805f6540a9: v03_readback_controls passed with 44 negative controls on working-tree and --rev paths; two positive runs produced byte-identical output."
        status: pass
      - kind: integration
        ref: "59305f4ea79d8f5f8c11164972eba7805f6540a9: focused CTest passed 4/4 for v03_dispositions, v03_dispositions_controls, v03_readback_controls and release_lifecycle_post_tag_controls; verify-test-inventory.sh --self-test passed."
        status: pass
  - id: D24-IMMUTABLE-LIMIT
    description: The v0.2.0 Ir policy baseline remains byte-identical; the receipt binds that policy at its immutable source revision.
    requirement: REL-01
    human_judgment: false
    verification:
      - kind: other
        ref: "59305f4ea79d8f5f8c11164972eba7805f6540a9: git diff --quiet f80bdf54c6c7d81e8e21f0275b43cda6edf6c8c4 HEAD -- tests/baseline/perf-gate-v1.txt; LIMITS_BASE_REV is 947d6a9d177af6c04a5f9ea6abcc2c470ab9be57."
        status: pass
metrics:
  duration: "not recorded; executor start timestamp was not persisted"
  completed: 2026-10-29
status: complete
---

# Phase GB-19-qualified-v0-3-0-release Plan 05: Perf-gate receipt and trusted reader Summary

**A same-run performance receipt, shipped-archive host smoke, pre-publish asset source and deterministic v0.3 readback checker are wired into the release path.**

## Performance

- **Duration:** Not recorded; the executor start timestamp was not persisted.
- **Started:** unavailable
- **Completed:** 2026-10-29T23:08:09Z
- **Tasks:** 4
- **Files modified:** 16

## Accomplishments

- The CI perf gate emits a source- and limits-bound receipt before returning a verdict, preserves the deciding retry attempt, uploads even after a red gate, and the release candidate verifies it against the exact push run. OQ-2 is resolved by embedding `perf_gate` in the existing `release-receipt.json`; the asset list and Ir limit stay unchanged.
- The rehearsal and release candidate run host-contract smoke on extracted archive bytes for Linux and macOS. Consumer receipts carry `host_smoke` and `platform`; Windows records `not-applicable`.
- The final-gate persists `release-pre-publish-inventory-${{ github.run_id }}-${{ github.run_attempt }}` before publication. Readback checks use the embedded raw artifact as the expected inventory, and the post-tag inventory covers the `ci_run` GET and same-run perf artifact download forms.
- `verify-v03-dispositions.py --check-readback PATH --rev REV --tag vX.Y.Z` now checks tag commit/tree, published asset ids/digests, inventory provenance, SHA256SUMS, the release receipt, the tag's support-ledger blob and copied privacy-pattern identity. Its self-test has 44 named rejection controls across working-tree and immutable-revision reads, plus deterministic positive output.
- D-24 remains intact: `tests/baseline/perf-gate-v1.txt` is byte-identical to `f80bdf54`; the performance receipt is bound to `LIMITS_BASE_REV=947d6a9d177af6c04a5f9ea6abcc2c470ab9be57`. The separately refreshed release-notes attribution receipt reports +9.6%.

## Task Commits

1. **Task 1: Perf-gate receipt tracer and trusted CI handoff** — `d91fae38` (feat)
2. **Task 2: Release receipt inventory, readback source artifact and endpoint replay** — `ea388594`, `0338b78a`, `1a549911`, `39da19fb`, `b04fdab3` (feat/fix)
3. **Task 3: Host smoke on shipped archives and consumer-receipt enforcement** — `98f84196` (feat)
4. **Task 4: Tag-bound v0.3 readback checker and controls** — `59305f4e` (test)

The eight task commits are measured from `0022a3e5dc9ecef487cd2466d69d8cb770a774a5` through `59305f4ea79d8f5f8c11164972eba7805f6540a9`.

## Carried Plan-Check Items

- `keep_receipt` creates the production destination directory, and the retry control starts from a scratch checkout without `build/` to verify receipt retention at the production path.
- Ir verdicts retain precedence over malformed timing data; reached verdicts still write receipts with `realtime_min: null` when timing cannot be parsed. A combined over-budget/malformed-timing control covers this order. `perf_gate_retry_controls` remains registered on Windows, with its first Windows pass assigned to PR A's `native-windows-x64` lane.

## L-4 Policy-Control Measurements

The registered `workflow_policy_controls` timeout stayed at 180 seconds. Control counts are the floor; elapsed seconds below are runtime measurements, not control counts.

| Task | Final measured run | Negative controls |
|---|---:|---:|
| 1 | 47.11 s | 437 |
| 2 | 43.16 s | 441 |
| 3 | 44.97 s | 446 |

At Task 2, the initial restricted-sandbox post-tag CTest invocation was distorted by denied `/bin/ps` access. The CTest property was confirmed at 60 seconds and left unchanged; an isolated scoped rerun passed in 23.60 seconds. The final focused Task 4 block also passed `release_lifecycle_post_tag_controls` in 26.20 seconds.

## Decisions Made

- The verified performance binding stays inside the current release receipt, so no additional release asset or asset-name-list change is needed.
- Platform is explicit in consumer receipts so the delivery verifier can allow `not-applicable` only for Windows while requiring `passed` for Linux/macOS.
- The published readback compares the original assets to the pre-publish artifact and treats `SHA256SUMS` and `release-receipt.json` as the two publication-time additions.
- The live `v03_readback` CTest is intentionally deferred to 19-07, when the published readback exists.

## Deviations from Plan

No release-scope or policy deviation. Task 2 needed follow-up fixes to keep the replay fixture bound to the perf source and to make the inventory omission/write controls exercise the real failure path; they are recorded as separate atomic commits above.

## Issues Encountered

- The sandbox initially denied `.git/index.lock` during the Task 4 commit and denied a temporary git worktree in the Task 3 delivery self-test. The authorized scoped escalations were limited to the task commit and that fixture test; both completed normally with hooks enabled.
- Task 2's first post-tag test invocation encountered the `/bin/ps` sandbox restriction described above. Scoped and final focused runs passed without changing its timeout or policy floor.

## User Setup Required

None. Hosted archive execution and the live release readback are exercised by the authorized release workflow in later plans.

## Next Plan Readiness

Plan 19-05 is complete; Phase 19 remains in progress. Proceed to **Plan 19-06 — Synthetic 0.3.0 pre-flight, docs and doc checks, PR A squash merge** with `/gsd-execute-phase 19`. REL-01 remains pending until publication and readback. D-09 owner acknowledgment remains pending at PR A review, and the two SDL menu-shortcut tests remain display-limited on this host.

## Self-Check: PASSED

The summary target and all eight task commits exist; the task commit range is measured from the recorded plan-head ledger. All cited test results are present in the retained execution evidence.

---
*Phase: GB-19-qualified-v0-3-0-release*
*Completed: 2026-10-29*
