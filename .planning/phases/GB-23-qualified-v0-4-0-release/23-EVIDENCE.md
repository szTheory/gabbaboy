# Phase 23 Qualification Evidence

## Revisions and PR

| Identity | Commit | Meaning |
|---|---|---|
| Reviewed implementation | bc282cc229c887d7034e533175249861db846154 | Exact two-slot scheduling and checker source reviewed independently by all three roles. |
| Review reports and local gate source | dd5d29654fc5964f27dfdde0ea97f6973e1f1a13 | All three reports bind the implementation above; configure/build, focused and full local CTest were run at this source. |
| Prior non-qualifying PR head | 343606f0cb105c837e928dc58d2ecea8b37e9670 | Historical four-slot hosted run; no longer the candidate schedule. |
| PR base | f2b05c9fb3ba314cfe46959b64073ce9441724ca | main base observed for PR #146 and used by the local immutable state-pin and timeout-budget checks. |

PR #146 is open at [the phase PR](https://github.com/szTheory/gabbaboy/pull/146), based on main at f2b05c9fb3ba314cfe46959b64073ce9441724ca. Its remote branch has not yet been advanced to the two-slot candidate. The next step is one fast-forward push, followed by fresh exact-head hosted qualification. The PR remains unmerged; no version PR, tag or publication is claimed.

## Earlier local verification at f595fb05 (historical)

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

## Local requalification at `7e0a252e` (2026-11-09)

This later local run supersedes the earlier local-suite result for the current implementation. It does not update the old PR #146 hosted evidence above: the current local commits have not been pushed, and no hosted run has been started for them.

| Check | Result |
|---|---|
| Reviewed implementation | `61f08de30b4f74ae539f827c5b04e1188fc3ea79`, independently reviewed in all three roles. |
| Review evidence / local candidate | `7e0a252e710d76688a60dd3aeafb82fd945ab382`. The immutable real-report gate passed with 3 reports and 68 findings. |
| Fresh configure and build | `cmake -S . -B build` and `cmake --build build --parallel 4` passed; configure recorded the exact `7e0a252e` source revision. |
| Initial stale-build diagnostics | The first full run at this checkout had 1,940 passes and two source-stamp failures (`cgb_corpus_report_controls`, `state_purity`). Both reported generated artifacts from an older checkout, not assertion failures. After reconfigure/build, the two isolated controls passed 2/2. |
| Final full configured CTest | `ctest --test-dir build --output-on-failure -j4` passed 1,942/1,942 with no failures in 2,360.76 seconds. |
| Open finding | SEC-23-09 remains a low-severity Git-output resource-bound hardening note. The exact real-report gate accepts it; no source change was made for that separate finding. |
| Hosted qualification | Not run for `7e0a252e`; this local candidate is not the recorded PR #146 head. Required exact-head hosted checks and protected merge therefore remain unproven. |

No candidate game or diagnostic fixture was fetched, built, run or admitted. REL-01 and publication remain Pending.

## Exact-candidate full local run at `9f38c43e` (2026-11-09)

The `7e0a252e` to `9f38c43e` change contains only the two allowlisted evidence documents. The build was reconfigured at `9f38c43e`, rebuilt, and the full suite was run against that exact configured revision.

| Check | Result |
|---|---|
| Immutable real-report gate | Passed at `9f38c43ecc312f7ef868e4f359a8d30eee21760e`: 3 independent reports, 68 findings, reviewed implementation `61f08de30b4f74ae539f827c5b04e1188fc3ea79`. |
| Configure/build | `cmake -S . -B build` and `cmake --build build --parallel 4` passed; CMake captured `9f38c43e` as the immutable source revision. |
| Full configured CTest | `ctest --test-dir build --output-on-failure -j4` passed 1,942/1,942 in 2,237.57 seconds. |
| Hosted qualification | Not run for this local candidate. PR #146 still points to `6ae7a46777348d02bf4e20419df0bfc8a5929591`, so no protected exact-head result covers the current local commits. |

SEC-23-09 remains a low availability-hardening note about unbounded captured Git output; the accepted review gate does not classify it as a blocking correctness finding. CI budgets and per-test timeouts remain unchanged. REL-01 and publication remain Pending.


## Exact-head hosted attempt at `343606f0` (2026-11-09)

PR #146 remained at `343606f0cb105c837e928dc58d2ecea8b37e9670`. The exact-head attempt completed without merge eligibility.

| Lane | Run / result |
|---|---|
| Native Linux | CI run `42654987218`: passed 1,942/1,942; job duration 47m56s. |
| Native macOS arm64 | Cancelled at the existing 40-minute job cap after 1,895/1,942 tests. |
| CMake 3.25.3 floor | Cancelled at the existing 50-minute job cap after 1,839/1,942 tests. |
| ASan/UBSan test inventory | Cancelled at the existing 55-minute job cap after 1,785/1,853 tests; sanitizer build/fuzz and acceptance lanes passed. |
| Native Windows x64 | Cancelled at the existing 60-minute job cap after 1,746/1,804 tests. |
| Fixture reproduction | Run `42654987232`: passed. |
| Preview package smoke | Run `42654987242`: failed because the matching required CI run did not succeed. |
| Performance and macOS player package | CI run `42654987218`: passed. |

The canceled CTest logs show docs shards passing in sequence until the workflow job ended; no assertion failure was reported in those lanes. Native Linux completed the same 200-shard suite under its existing 60-minute limit. The current four-slot reservation for every docs shard serializes the group on slower native/floor runners. Two independent docs shards passed concurrently on the local macOS host in 9.5 seconds total; this is a diagnostic probe, not full concurrency qualification.

D-163 explicitly prohibits changing CI job budgets and per-test timeouts. No job cap, test timeout, source behavior, or test assertion was changed in response to this attempt. The PR remains open and unmerged. A new hosted qualification requires an owner-approved scheduling rescope, followed by updated source-bound review and local gates. REL-01 and publication remain Pending.


## Owner-approved two-slot local qualification (2026-11-09)

The D-163 amendment changes only CTest processor reservations: all 200 generated docs controls now reserve two of four global slots. Their commands, assertions, v02 labels and 90-second timeouts remain unchanged; non-doc reservations remain at four, and hosted job caps are unchanged.

| Check | Result |
|---|---|
| Exact-source report reissue | Three independent reports committed at dd5d29654fc5964f27dfdde0ea97f6973e1f1a13, each reviewing implementation bc282cc229c887d7034e533175249861db846154. No new correctness or security finding. |
| Report gate | Passed: 3 reports and 68 findings; SEC-23-09 remains the accepted low resource-bound note. |
| Workflow-policy coverage | Self-test passed 526 controls; configured inventory check passed 540 controls across six groups. Exact CTest metadata confirms 200 docs controls at PROCESSORS 2, LABELS [v02], TIMEOUT 90; all other reserved tests remain at four processors. |
| Test budget and timeout ledger | Passed: 1,942 configured tests and 288 allowlisted timeout rows; no timeout or CI budget change. |
| Focused Phase 23 T2 CTest selection | Passed 224/224 in 986.32 seconds with four global workers. All 200 docs controls ran; maximum docs-control duration was 18.01 seconds. |
| Full configured CTest | Passed 1,942/1,942 in 1,679.55 seconds with four global workers and no skips. All 200 docs controls ran; maximum docs-control duration was 19.22 seconds. |
| Workflow-policy CTest wrappers | Passed 3/3, including source-bound coverage and review-evidence controls. |
| Hosted qualification | Pending: the prior PR head 343606f0 is not valid evidence for the two-slot schedule. The final two-slot branch candidate must pass a fresh exact-head required CI, fixture-reproduction and preview-package run. |

The focused log is /private/tmp/gabbaboy-phase23-two-slot-focused.log; the full-suite log is /private/tmp/gabbaboy-phase23-two-slot-full.log. Neither is repository content. No game or diagnostic fixture was fetched, built, run or admitted. REL-01, DIAG-01, DIAG-02 and RIGHTS-01 remain Pending where their evidence gates are unresolved. No merge, tag or publication is claimed yet.
