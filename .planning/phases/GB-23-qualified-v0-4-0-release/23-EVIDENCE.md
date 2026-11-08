# Phase 23 Qualification Evidence

## Revisions and PR

| Identity | Commit | Meaning |
|---|---|---|
| Reviewed implementation | `b75ecb97d8ab11cda5dcb3cc94a87363e60f0cae` | Exact source independently reviewed by release-consumer, security and adversarial reviewers. |
| Review evidence / local qualification | `f595fb0572fe65e9b4df91069c97470af6b02a04` | Committed review reports; the exact configured source for the focused and full local runs. |
| PR base | `f2b05c9fb3ba314cfe46959b64073ce9441724ca` | `main` base observed for PR #146 and used for local state-pin and timeout-budget checks. |

PR #146 is open at `https://github.com/szTheory/gabbaboy/pull/146`. At the last GitHub read, its remote head was still `308b02fbaade17e4e5ff9bc7a4fbe9a3b699ff7a`; the local reviewed commits had not yet been pushed. Hosted exact-head checks are pending. The PR is not merged, and no v0.4.0 version PR, tag or publication is claimed.

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
| Direct real-report gate | Passed at `f595fb05`: 3 independent reports, 60 findings, implementation exactly `b75ecb97`; no open correctness, security, high, critical or blocking finding. SEC-23-09 remains a low-severity resource-bound note. |
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

One current PR run remains necessary for required native Linux, macOS and Windows checks, the CMake floor, fixture reproduction, installed consumers, player package, sanitizers, fuzz and performance lanes. Running these checks locally avoided repeated hosted runs, but a macOS local run cannot prove Windows behavior, GitHub branch protection or exact-head workflow status. Record the current PR head, required run/job IDs and measured queue/dependency waits when that hosted run finishes.

No candidate game or diagnostic fixture was fetched, admitted or run for Phase 23 qualification. REL-01, DIAG-01, DIAG-02 and RIGHTS-01 remain Pending where their evidence gates are unresolved. Local tests do not qualify or publish v0.4.0.
