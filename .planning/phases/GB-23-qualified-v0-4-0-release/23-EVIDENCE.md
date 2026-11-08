# Phase 23 Qualification Evidence

## Revisions and PR

| Identity | Commit | Meaning |
|---|---|---|
| Reviewed implementation | `b75ecb97d8ab11cda5dcb3cc94a87363e60f0cae` | Exact source independently reviewed by release-consumer, security and adversarial reviewers. |
| Review reports / full local run source | `f595fb0572fe65e9b4df91069c97470af6b02a04` | Committed review reports and the configured source for the focused and full local runs. |
| Current qualification candidate | `0996981cb1ced18665b45770bb0fe725a3d29867` | Exact PR #146 head; contains only the reviewed implementation and allowlisted evidence records. The direct real-report gate passes here. |
| PR base | `f2b05c9fb3ba314cfe46959b64073ce9441724ca` | `main` base observed for PR #146 and used for local state-pin and timeout-budget checks. |

PR #146 is open at `https://github.com/szTheory/gabbaboy/pull/146`, based on `main` at `f2b05c9fb3ba314cfe46959b64073ce9441724ca`, with exact head `0996981cb1ced18665b45770bb0fe725a3d29867`. The PR is not merged, and no v0.4.0 version PR, tag or publication is claimed.

## Local verification

The final local build was configured at the review-evidence commit with the native-CI install prefix and immutable main-base state pin:

```text
cmake --preset phase1 \
  -DGBB_TEST_INSTALL_PREFIX=build/package-prefix \
  -DGBB_STATE_PIN_BASE_REV=f2b05c9fb3ba314cfe46959b64073ce9441724ca
cmake --build --preset phase1 --parallel 4
```

| Check | Result |
|---|---|
| Direct real-report gate | Passed at both `f595fb05` and qualification candidate `0996981c`: 3 independent reports, 60 findings, implementation exactly `b75ecb97`; no open correctness, security, high, critical or blocking finding. SEC-23-09 remains a low-severity resource-bound note. |
| Planning-label path controls | Passed: 33 controls, including wrong-repository negatives and simulated Windows case variants on POSIX. |
| Workflow-policy coverage | Passed: 94 self-test controls and 540 configured controls across 6 groups. The CI group passed 112 negative plus 1 positive; the ledger group passed 20 negative plus 1 positive. |
| Timeout-budget check | Passed: 1,942 configured tests, 288 allowlisted rows, 11 existing player rows skipped under policy. |
| State-pin checks | Passed 2/2 on this macOS host with the `macos-arm64` platform identity. |
| Installed package | `cmake --install build --prefix build/package-prefix` passed; the package includes the public library, headers, runner, CMake package files and licensed public fixtures. |
| Focused Phase 23 CTest selection | Passed 223/223 in 679.93 seconds with four workers. It included all 200 docs-control shards, the committed review contract and controls, release/consumer controls, fixture controls, planning labels and workflow-policy groups. |
| Full configured CTest stream | Passed 1,942/1,942 in 980.81 seconds with four workers. No test was skipped. |
| Installed test inventory | Passed: the same full-run JUnit verified 1,942 executed cases and no skips. |
| CGB corpus receipt and public claims | Passed: 107/107 cases, 25 observed passes, 82 expected failures, 4,959 assertions. The privacy check passed for 3 artifacts (1,488,355 bytes). |
| Acceptance/Mooneye observations | The two Libbet observations and the declared Mooneye suite completed successfully. They are repeatability/regression observations, not accuracy or game-compatibility qualification. |

CTest's full-run JUnit was written under `build/build/` because the local command passed a `build/...` relative output path with `--test-dir build`. The exact JUnit bytes were copied to the canonical `build/` path before receipt and inventory validation; the CTest dashboard XML and JUnit both came from the same 1,942-test run. No tests were rerun to create the receipt.

## Sandbox diagnosis

The first sandboxed full-suite attempt stopped after four performance/review controls could not create temporary Git worktrees under `.git/worktrees`. The same four tests passed 4/4 with local Git metadata access. The complete suite was then rerun with that access and passed 1,942/1,942. This was an execution-permission issue; no source change was needed.

## Hosted checks and evidence limits

The exact-head hosted checks for PR #146 are running on candidate `0996981cb1ced18665b45770bb0fe725a3d29867`:

| Workflow | Run | Observed state |
|---|---:|---|
| `fixture-repro` | 42504378712 (run 941) | Passed. |
| `ci` | 42504378731 (run 942) | In progress; native Linux/macOS/Windows, CMake floor, installed consumers, player package, sanitizer, fuzz and performance jobs are included. |
| `preview-package-smoke` | 42504378802 (run 352) | In progress; waits for the matching successful CI and package artifacts. |
| `version-pr-gate` | 42504378789 (run 86) | Skipped by its non-version-PR condition; not a qualification check for this PR. |

The required CI and preview jobs are still in progress, so no merge eligibility or hosted qualification is claimed. A local macOS run cannot establish Linux/Windows results, GitHub branch protection or exact-head workflow status. Record completed required job IDs, conclusions and measured queue/dependency waits after these runs finish.

No candidate game or diagnostic fixture was fetched, admitted or run for Phase 23 qualification. REL-01, DIAG-01, DIAG-02 and RIGHTS-01 remain Pending where their evidence gates are unresolved. Local tests do not qualify or publish v0.4.0.
