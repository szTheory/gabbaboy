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

## D-164 local requalification at `b8619f99` (2026-11-09)

This candidate applies the owner-approved native-macOS CI cap change from 40 to 50 minutes. Only the native macOS job value changed; all other hosted job caps, per-test timeouts, CTest reservations, assertions, labels, and the preview wait policy remain unchanged. The existing timeout-budget citation values are preserved and the ledger discloses the changed workflow body. The PR remains open until one fresh exact-head hosted qualification completes.

| Check | Result |
|---|---|
| Reviewed implementation | `48d8e501872b9a19138a4653830a40b983199adc`; three independent release-consumer, security, and adversarial reports bind this exact source. The corrected candidate-source binding was re-reviewed by all three roles. |
| Review evidence / candidate | `b8619f99683bd07412286373823c989798eccfcb`. The immutable real-report gate passed with 3 reports and 71 findings; no blocking correctness/security finding is open. SEC-23-09 remains a low-severity resource-bound note. |
| Configure and build | `cmake --preset phase1` and `cmake --build --preset phase1` passed at `b8619f99`. |
| Workflow and timeout gates | Workflow-policy check passed. The source-bound workflow-policy self-test passed 528 controls, including the 50-minute positive and stale 40-minute negative. Test-budget validation passed for 1,942 tests and 288 allowlisted timeout rows. |
| Focused Phase 23 selection | 223/224 passed in 1,313.09 seconds; `support_claims_v04_controls` reached its unchanged 60-second ceiling. That control passed alone immediately afterward in 35.14 seconds. Every selected test therefore has a passing result on this candidate; the timeout is retained here as load-sensitive evidence. |
| Full configured CTest | 1,934/1,942 passed in 4,688.23 seconds. Eight controls timed out without assertion output: `perf_gate_receipt_controls`, `perf_repeat_controls`, `perf_advisory_pipeline`, `perf_advisory_controls`, `classify_changes_controls`, `workflow_policy_group_release_jobs`, `workflow_policy_group_rehearsal`, and `support_claims_v04_controls`. Each passed when rerun alone on the same build (the seven-test recovery group passed 7/7 in 161.29 seconds; the remaining control passed in 3.24 seconds). The final focused-selection recovery also passed `support_claims_v04_controls` in 35.14 seconds. The timeout handler emitted `/bin/ps: Operation not permitted`; no source, CTest timeout, or CI cap was changed. All 1,942 tests have a passing result across the full run and these bounded isolated recoveries. |
| Hosted qualification | Pending one fresh exact-head run on the updated PR candidate. The prior hosted run at `c9a6320671b56d1092b2884aeac15d6a9320b60f` is not evidence for D-164. No merge, tag, or publication is claimed. |

No candidate game or diagnostic fixture was fetched, built, run, or admitted. REL-01, DIAG-01, DIAG-02, and RIGHTS-01 remain Pending where evidence gates are unresolved.


## D-164 exact-head hosted qualification at `029a77f5` (2026-11-10)

This is the single hosted attempt authorized for D-164. It confirms the macOS 50-minute cap is sufficient, but Phase 23 T3 remains blocked by the unchanged Windows cap. PR #146 remains open at the exact attempted candidate; this handoff record is local and was not pushed, so it does not trigger another run.

| Lane | Result |
|---|---|
| Native Linux | CI run [42718334209](https://github.com/szTheory/gabbaboy/actions/runs/42718334209): passed 1,942/1,942 in 2,265.80 seconds. |
| Native macOS arm64 | Passed 1,942/1,942 in 2,167.82 seconds under the D-164 50-minute cap. |
| CMake 3.25.3 floor | Passed 1,942/1,942 in 2,572.12 seconds. |
| Native Windows x64 | Cancelled at the unchanged 60-minute cap after 1,799/1,804 tests. All 200 docs shards passed; the next workflow-policy test had just started, and no assertion failure appeared before cancellation. |
| Other required lanes | Sanitizer build/fuzz and acceptance, performance gate, and macOS player package passed. |
| Fixture and preview | Fixture-reproduction run [42718333927](https://github.com/szTheory/gabbaboy/actions/runs/42718333927) passed. Preview-package run [42718333948](https://github.com/szTheory/gabbaboy/actions/runs/42718333948) failed because required CI did not complete. The version-only gate was skipped by condition. |

The previous exact-head run `42679813590` completed the same Windows inventory, 1,804/1,804, in 2,129.15 seconds. Parsing the 199 docs-shard duration lines present in each job log gives mean/median times of 9.99/7.19 seconds previously and 18.66/12.97 seconds on this run. The evidence shows substantial hosted-runner slowdown; it does not establish that the approved two-slot reservation caused it. No low-risk coverage-preserving CI optimization is supported by these two runs, so the 200-control schedule and required checks remain unchanged.

**Owner-approved D-165 (2026-11-10):** raise native Windows 60→70 minutes; all three preview exact-head wait deadlines 3,900→4,500 seconds; and all three preview job caps 75→85 minutes. The 85-minute caps are ten minutes above the wait deadline before checkout and preflight time. If exact-head CI passes near the deadline, less than ten minutes remain for package checks; if the waiter expires before success, the job fails and package steps do not run. The configured ceilings increase by up to 40 runner-minutes per attempt. Add paired positive/stale-value policy controls, re-review exact source, rerun local gates, and use one fresh exact-head attempt. This does not renew or reset any plan, review, gap, or other phase counter. Implementation and exact-source review are in progress. No Phase 24 work is authorized.

REL-01 and fixture-related release claims remain Pending. Do not advance into Phase 24; resume Plan 23-04 T3 after the owner decision.

## D-168 follow-up review and local stop at `3c0489d7` (2026-11-10)

The current implementation candidate is `3c0489d722728c23f2369a0dced49c996b9ac9dc`. The owner-approved D-167 Linux runner/container guard is already present in this source: the Linux waiter is pinned to `ubuntu-22.04`, all three waiter jobs reject `container` and `services`, and the source-bound self-test exercises those mutations. The three current reviewers found no remaining D-167 bypass.

| Check | Result |
|---|---|
| Configure/build | `cmake --preset phase1` had configured this checkout; `cmake --build --preset phase1 -j4` passed and regenerated the exact CGB runner qualification for `3c0489d7`. |
| Exact-source reviews | Security accepted the D-168 worker timeout/output bounds. Adversarial review blocked on a Windows cleanup issue: the reusable worker keeps the synthetic `TemporaryDirectory` as its current directory until `atexit`, after the directory context exits. Release-consumer review blocked on the separate `candidate-fuzz` release waiter budget. These reviews are on the exact current source; the formal report files still need reissue after the owner-approved corrections. |
| Targeted local CTests | 11/12 passed, including fixture-admission, release-disclosure, workflow-policy, test-budget, and review-evidence controls. `v02_source_archive_controls` timed out at its unchanged 90-second ceiling without an assertion diagnostic. It reserves all four CTest processors, and an isolated rerun also timed out at 90 seconds. |
| Focused/full local suite | Not run at this candidate because the exact-source review found a correctness blocker and the source-archive gate is not passing. |
| Hosted qualification | Not started. No D-168 exact-head attempt has been used. |

The release-consumer finding is specific: `.github/workflows/release.yml` lets `candidate-fuzz` wait 3,000 seconds (50 minutes) for exact-source CI. Its `needs: [release, candidate]` creates no guaranteed lead time, while CI may run the 65-minute sanitizer lane or the 70-minute Windows lane plus the required-native aggregate. The current 112-minute release job cap also cannot accommodate a 75-minute wait plus its existing post-CI poll and margins. No release workflow or budget change has been made.

Per the D-168 rescope stop rule, do not make further source changes until the owner decides whether to approve (a) stopping the worker before synthetic temporary-directory cleanup and (b) a bounded candidate-fuzz budget correction, recommended as a 4,500-second wait and 137-minute job cap with paired source-bound controls and ledger disclosure. If approved, preserve all other budgets and investigate the source-archive timeout within its existing 90-second limit before focused/full qualification. Phase 23 remains active at Plan 23-04 T3; stop at the Phase 23 boundary.


## D-165 owner-approved scope and implementation status (2026-11-10)

The owner approved the Windows cap, downstream preview waiter, and preview job-cap changes described in [23-04-T2-RESCOPE.md](23-04-T2-RESCOPE.md#d-165-owner-approved-windows-and-preview-runner-windows). The D-164 hosted attempt at `029a77f5` is complete and cannot qualify the new D-165 policy. The corrected implementation at `e5a2f71dbf2ed27912d0ba810d434e95b9fc8c4c` requires its own exact-source reports, local gates, and one new exact-head CI plus fixture/preview workflow attempt. If that attempt does not pass, stop for another owner decision. Keep all user-visible release claims and REL-01 pending until exact-head release gates pass; do not start Phase 24.


## D-165 exact-source review corrections at `e5a2f71d` (2026-11-10)

The first adversarial review of `6774831810824740a10b6644f7452eb33091a1f1` found that the new preview-wait regex scanned raw workflow text: an old variable-backed 3,900-second waiter could pass if a shell comment contained `--deadline-seconds 4500`. Commit `07bdf08d17d253abe8d1f2ac63c6bfdf16bf40b1` used the pinned workflow reader, matched each exact folded `run: >-` block to its parsed step, and used the pinned shell parser to inspect active arguments. Re-review then found two more bypasses: an unreachable waiter inside `if false`, and a `python3()` shell function that appended a stale deadline after the checked literal. These were control-coverage defects, not hosted CI failures.

Commit `e5a2f71dbf2ed27912d0ba810d434e95b9fc8c4c` now requires exactly one parsed shell event with the full expected literal argv, no shell frames/assignments/connectors, and the expected unconditional waiter step, environment, and working directory. It rejects workflow/job/step shell or Python environment overrides. Negative controls cover stale comment and variable values, dead-branch waiters, `python3()` shadowing, disabled waiter steps, BASH_ENV injection at workflow/job/step scope, and shell-default changes.

At `e5a2f71d`, the workflow-policy coverage self-test passes 563 controls; direct workflow-policy CI and timeout-ledger checks pass; the timeout ledger parses as JSON; and syntax/diff checks pass. The first release-consumer review accepted `07bdf08d`, but all three roles are now re-reviewing the final exact source `e5a2f71d`. The immutable real-report gate, configure/build/full local CTest, and the single D-165 hosted attempt remain pending; no D-165 hosted attempt has started.

## D-167 exact-source review and local qualification (2026-11-10)

The owner approved the narrow environment-binding correction recorded in [D-167](23-04-T2-RESCOPE.md#d-167-owner-approved-preview-execution-environment-binding). Implementation `950c78b0bac936992403511a3cfa41f7cb1069c6` pins the Linux preview job to `ubuntu-22.04` and rejects `container`/`services` on all three waiter jobs. The D-165 timing values, package flow, test inventory, and per-test ceilings remain unchanged.

| Check | Result |
|---|---|
| Independent exact-source reviews | Release-consumer, security, and adversarial reports all ACCEPT `950c78b0bac936992403511a3cfa41f7cb1069c6`; the immutable report gate passed at `7c9067ed5b2822748f611915119c61a1b4290f25` with 3 reports and 78 findings. SEC-23-09 remains the previously disclosed low-severity resource-bound note; no blocking finding is open. |
| Workflow policy and budget | Source-bound workflow-policy coverage self-test passed 573 controls. The production `ci` and `ledger` groups passed. Test-budget validation passed for 1,942 tests and 288 allowlisted rows. |
| Configure and build | `cmake --preset phase1` and `cmake --build --preset phase1` passed at the report-evidence candidate. |
| Focused Phase 23 T2 selection | Passed 224/224 in 1,173.12 seconds at the report-evidence candidate, including both review-evidence CTests and all 200 docs controls. |
| Full configured CTest | Passed 1,942/1,942 in 1,891.20 seconds with four workers and no skips. All 200 docs controls passed. The 199 numbered docs shards averaged 5.70 seconds (median 5 seconds, maximum 14 seconds). |
| CI efficiency assessment | The two-slot docs schedule and four-worker overall run completed without timeout or assertion failure. These local timings do not justify a coverage change or speculative scheduler adjustment; assess hosted queue/job/step timing after the exact-head run. |
| Hosted qualification | Pending. At the read-only check, PR #146 remained open on `gsd/phase-23-qualified-v0-4-0-release` at old head `029a77f5a87682cee545aa99edc1fe5263e5a77c`. The single D-165 exact-head attempt has not started. Push only the final allowlisted qualification candidate after its report gate, then inspect all required exact-head workflows to completion. |

No game or diagnostic fixture was fetched, built, run, or admitted. REL-01 and publication remain Pending. Do not advance beyond Phase 23.


## D-165 exact-head hosted qualification at `0916cb46` (2026-11-10)

The single D-165 attempt ran on PR #146 at exact head `0916cb465211a97b09bf970971f113861adb7141`. It did not qualify. CI run [42854792963](https://github.com/szTheory/gabbaboy/actions/runs/42854792963) ended failed/cancelled; preview run [42854792759](https://github.com/szTheory/gabbaboy/actions/runs/42854792759) failed because its required exact-head CI run did not pass. Fixture-reproduction run [42854793507](https://github.com/szTheory/gabbaboy/actions/runs/42854793507) passed. The push event also ran the same short fixture matrix at [42854068884](https://github.com/szTheory/gabbaboy/actions/runs/42854068884), a duplicate trigger observation with seven short jobs; no trigger change is made in this attempt.

| Lane | Result |
|---|---|
| Native Linux x64 | Failed at CTest `release_disclosure_controls` timeout 60.05s; 1,941/1,942 tests passed. CTest real time 3,079.67s; job time 3,407s. |
| Native macOS arm64 | Passed 1,942/1,942 in 2,758s (45m58s). |
| Native Windows x64 | Failed at `phase21_fixture_admission_controls` 60.03s, `release_disclosure_controls` 60.02s, and `v02_source_archive_controls` 90.01s timeouts; 1,801/1,804 tests passed. CTest real time 4,031.70s; job time 4,163s. |
| Linux ASan/UBSan inventory | Job hit its existing 55-minute cap and was cancelled at 1,819/1,853 completed tests. `v02_consumer_controls_c` was active when the job ended. |
| Other CI lanes | CMake 3.25.3 passed in 1,787s; sanitizer build/fuzz passed in 224s; sanitizer acceptance passed in 1,290s; performance gate passed in 63s; macOS player package passed in 491s. |
| Preview | The three waiters observed the required CI failure and failed before their 4,500-second wait deadline; the aggregate preview gate failed. |

The timed-out controls are existing tests, not changed by the D-167 correction. Local full CTest at the qualified source passed 1,942/1,942 in 1,891.20s; local recorded mean costs are 5.41s for `release_disclosure_controls`, 58.70s for `phase21_fixture_admission_controls`, and 14.96s for `v02_source_archive_controls`. Those local costs do not explain the Linux/Windows hosted timeouts. No code assertion failure or review finding was reported. The ASan job cap and the three test-level timeouts did not complete the required inventory.

D-165 authorized one exact-head hosted attempt and explicitly requires a new owner decision after failure. PR #146 remains open and unmerged. The current approval does not authorize a retry or further budget change. Do not merge, tag, publish, or advance to Phase 24. The next step is an owner decision on an in-place, evidence-bounded T2 rescope for the timed-out controls and incomplete ASan inventory, followed by exact-source reviews and local qualification before any newly authorized hosted attempt. REL-01 and publication remain Pending.


## D-168 profiled T2 correction status (2026-11-10)

The owner approved the profile-driven correction in [23-04-T2-RESCOPE.md](23-04-T2-RESCOPE.md#d-168-profiled-control-and-sanitizer-schedule-correction). No hosted attempt has started. The scope preserves the three 60/60/90-second CTest ceilings, all control cases, all CTest inventory, four-worker execution, and D-165 Windows/preview limits.

Local profiles identified:

- `phase21_fixture_admission_controls`: the full profile run was about 50 seconds under cProfile. Its synthetic cases invoked the checker CLI 54 times, with those child invocations accounting for about 27 seconds cumulatively. The CTest's historical mean is 58.70 seconds. The corrected harness reuses one isolated worker, runs the real parser and `main()` in a fresh script namespace per case, preserves the hard 30-second per-call kill and separate 1 MiB stdout/stderr caps, and keeps the same exit-code/output assertions. An earlier in-process prototype passed locally in 35.76 seconds but was rejected in review for losing those subprocess bounds; it is not qualification evidence for the corrected worker.
- `release_disclosure_controls`: six calls recreated the same read-only adoption input tree; the profiled copies and verifier calls accounted for about 22.6 seconds under cProfile. The self-test now creates one fresh private input workspace and still launches the adoption CLI for every existing positive and negative case. Direct concurrent execution passed 4 positives and 20 negatives.
- `v02_source_archive_controls`: the profile showed repeated `git show` retrieval of immutable fixture-policy blobs. A self-test-local cache now caps each blob at 1 MiB and aggregate bytes at 16 MiB, and asserts reuse while ordinary worktree checks continue. The self-test passed 17 cases and 92 negative controls during the concurrent direct run.

The sanitizer job was cancelled at 1,819/1,853 tests under the existing 55-minute cap, with one four-slot consumer test still active. D-168 therefore sets the lane to the approved 65-minute maximum (+10), preserves its existing historical p50 and discloses the changed job body, and raises only the two sanitizer-build CTest scheduling COST hints to 1,800 (normal builds remain 600). Their `PROCESSORS 4` reservations and test timeouts are unchanged. Source-bound policy controls now cover the ordinary/sanitizer costs and reject a stale 55-minute workflow/ledger value.

| Gate | Result |
|---|---|
| Disclosure self-test | Passed: positives=4, controls=20. |
| Source-archive self-test | Passed: accepted=17, negative controls=92; the bounded-cache-reuse assertion passed. |
| Candidate-checker controls | Pending exact-source rerun at the corrected worker commit. A throwaway worker probe confirmed hard timeout, output-cap rejection, and worker reuse; the earlier in-process CTest result is superseded. |
| Configure/build, workflow and budget checks | Pending. |
| Exact-source reviews and immutable real-report gate | Initial D-168 source `8a6e1536` received BLOCK from security/adversarial/release-consumer review. The timeout/output-bound issue is corrected in a follow-up; the separate release `candidate-fuzz` wait-budget question needs owner direction before changing release workflow budgets. |
| Focused Phase 23 CTest and full local CTest | Pending. |
| New hosted qualification | Authorized once, only after the preceding reviews and local gates pass. |

No release claim is qualified by these local control results. REL-01 and publication remain Pending; no game or diagnostic fixture was fetched, built, run, or admitted. After T3 completes, continue only with plans 23-07, 23-05, 23-06, and 23-08; stop at the Phase 23 boundary.


## D-169 implementation and local checks (2026-11-10)

The owner approved both narrow D-169 corrections recorded in [23-04-T2-RESCOPE.md](23-04-T2-RESCOPE.md#d-169-owner-approved-worker-cleanup-and-release-reader-budget). Implementation is in the current working tree; exact-source review and full qualification have not yet completed.

| Check | Result |
|---|---|
| Candidate-checker worker | `tests/scripts/verify-cgb-candidates.py --self-test --repo-root .` passed; cleanup now stops the bounded worker before the synthetic temporary directory exits, with a negative control for a live worker. |
| Source-archive controls | Direct isolated self-test passed 17 positive cases and 94 negative controls. `v02_source_archive_controls` passed in 72.71 seconds, below its unchanged 90-second CTest ceiling. |
| Workflow policy | Production workflow-policy check passed. The immutable-source coverage checker now validates the candidate-fuzz 4,500-second wait, 137-minute cap and ledger row, including stale-value negatives. |
| Syntax and diff | In-memory Python compilation and JSON parsing passed before documentation reconciliation; rerun syntax and `git diff --check` on the exact commit. |
| Exact-source reports | Pending. All three reports must bind to the implementation commit before the immutable report gate can pass. |
| Focused/full local qualification | Pending. |
| Hosted qualification | Not started. The single already-authorized exact-head CI/fixture/preview attempt remains conditional on reviews and all local gates. |

The release-reader worst-case budget is 8,190 seconds within the 137-minute (8,220-second) cap. The 4,500-second exact-CI waiter allows for required CI lanes with no guaranteed head start, including the 65-minute sanitizer inventory and 70-minute Windows lane plus the required-native aggregate. The candidate-fuzz timeout-ledger citation and historical p50 remain unchanged; its disclosure records that the job body changed after the cited run. No unrelated timeout, assertion, inventory, release claim, or fixture policy changes. No merge, tag, publication, or Phase 24 work is eligible before exact-head hosted qualification.

## Session recovery and measured CI efficiency (2026-11-10)

The interrupted Codex task ended with the generic error `{"detail":"Bad Request"}` and no specific API diagnostic. Its later authorized work was in an isolated checkout, while the original workspace still had an older D-163 handoff and uncommitted changes. Recovery read the actual task history, retained the owner's D-169 approval, verified the old task was no longer running, and confirmed OpenGSD runtime identity `@opengsd/gsd-core` version 1.20.0. The original workspace now points locally to the active checkout. No global Codex configuration was changed and no API root cause is inferred from the cumulative token counter.

The owner approved D-170's complete configured dependency path: five-minute change classification, 70-minute Windows lane, five-minute required-native aggregation. Reader waits are 4,800 seconds, preview caps 90 minutes, and candidate-fuzz has 160 attempts at 30 seconds and a 142-minute cap. The incremental configured maximum is 20 runner-minutes across four readers relative to D-169. Producer/test caps and the single existing hosted-attempt allowance remain unchanged. Actual queue/service availability can still cause a closed failure.

D-171 removes the observed duplicate fixture workflow on ordinary PR branch pushes: recorded PR run 42854793507 and branch-push run 42854068884 ran the same seven-job matrix. Push events now select main; every PR, manual dispatch, job body and required gate remains. The registered immutable workflow-coverage check rejects unrestricted pushes, missing PR/dispatch, and wrong push branches. No additional safe scheduling or dependency change was established by the available measurements; sanitizer artifact sharing and broader caches/concurrency are not justified here.

At implementation `10fee4515c9db0e8b259e089ef2ec41f0453b811`, configure/build, the production workflow policy, 598-control immutable policy self-test, configured 540-control policy check, and the 1,942-test budget check passed. Independent release, security and adversarial source reviews found no new blocker. Targeted CTest passed candidate admission in 36.87 seconds and disclosure controls in 35.67 seconds; source-archive controls timed out at their unchanged 90-second ceiling. The failed local attempt is retained in `build/phase23-recovery-harness.log`; no full or hosted run followed that failure.

D-172 addresses the measured cause rather than increasing the limit. A diagnostic Python 3.9 profile completed all 17 original positives and 94 negatives in 82.53 seconds; this is a diagnostic result, distinct from configured Python 3.14 CTest qualification. Four actual product CLI invocations consumed 14.40, 15.30, 14.44 and 16.95 seconds rereading immutable baseline blobs. The parent-only self-test cache did not reach fresh CLI namespaces. The worker now reuses successful immutable blobs keyed by checker-source digest, canonical root, full commit and path; the parent and worker each retain at most 8 MiB, preserving the existing combined 16 MiB bound and 1 MiB per-entry limit. Every actual CLI parser/main invocation, fresh namespace, policy/archive computation, worktree read and original assertion remains. Identity separation, source changes, symbolic refs, exact/overflow capacity, oversized entries and real worker reuse are checked. The initial configured-Python direct run retained all 17/94 cases; final affected/focused/full CTest and exact-source review remain qualification gates.

No new hosted attempt, merge, version PR, tag or publication has occurred during recovery. Continue Phase 23 only; Phase 24 remains out of scope.

### D-172 affected-test result

At exact implementation `b50f0c10e0794591a212edbfd083f10084805532`, fresh configure/build passed and the configured Python 3.14 `v02_source_archive_controls` CTest passed in 33.42 seconds (33.48 seconds total), retaining the unchanged 90-second limit. The earlier 90.01-second timeout remains recorded. All three independent roles accepted this final implementation; their cache identity/resource, failure, reuse, namespace, stream and deadline probes found no new correctness/security blocker. Historical findings remain with their original provenance, including the existing low nonblocking SEC-23-09 resource note. The final immutable policy self-test passes 598 controls and the unchanged test-budget gate passes the 1,942-test inventory. Full qualification and hosted evidence are still pending.

### D-173 focused failure and affected-test result

The focused 224-test selection at candidate `d5b5a70940846ea56ade1432436caeaa82c8cebb` did not qualify: candidate admission passed in 42.75 seconds, but `release_lifecycle_controls` hit its unchanged 60-second ceiling without assertion output. The identified focused CTest subtree was stopped before running the remaining selection; other projects' tests were preserved. The `/bin/ps` permission message appeared during CTest timeout cleanup and is not established as the cause. No full or hosted attempt started.

An initial direct diagnostic used an unsupported Python 3.9 for shell children and failed with a `Path.write_text(newline=...)` compatibility error; it is invalid qualification evidence. Repeating the diagnostic with the exact configured Python 3.14 and PATH passed all four positives and 101 controls in 64.09 seconds. Stage setup occupied about 13 seconds, the serial positive sequence 9.75 seconds, then independent controls used their existing bounded pool for about 38 seconds. D-173 puts that unchanged positive sequence into one existing pool slot while retaining its order, private scenario state, every future's result, actual production scripts, the existing worker ceiling and RUN_SERIAL property.

At implementation `33a1e7faf0c4126a4840e3c1c55ee9d1589d2593`, fresh configure/build passed and `release_lifecycle_controls` passed in 45.78 seconds (45.83 seconds total) within its unchanged 60-second limit. No cache, dependency, inventory, assertion, producer budget or release authority changed. Independent review and full qualification remain source-bound gates; the single existing hosted attempt remains unused.

### Consolidated local qualification without duplicate execution

The owner requested measured reductions in duplicate work. At frozen qualification head `68c144bef4453ecaab1d5817d86f2918d30356df`, the final focused run passed admission (40.57s), lifecycle (51.61s), release-workflow policy (140.20s), version (73.50s), CI-policy (30.68s), support-ledger (58.07s) and disclosure (32.51s) controls. The remaining focused selection was intentionally stopped to avoid executing those same tests again before the full suite; this partial run is not reported as a focused pass.

The configured full inventory was checked against `tests/expected-tests.txt` read from this immutable commit, by exact test identities and uniqueness. Every one of the 224 focused identities belongs to the required full inventory. One full CTest execution now writes JUnit for both gates. Result review requires exact complete/unique full identities, successful statuses and no failures/errors/skips, then preserves each focused testcase in a canonical XML projection and verifies its exact focused identity set. The existing `.github/scripts/verify-test-inventory.sh` checks both full and projected results. No test, assertion, platform, timeout, reservation, source identity or hosted gate is omitted or weakened.

The existing inventory self-test passed. Additional one-off causal checks accepted a complete result and rejected failed, errored, skipped, missing and duplicate cases. These are result-review controls, not additional product qualification. A compact XML duplicate fixture exposed the existing shell parser's line-oriented serialization limitation: it accepted two same-line elements as one. This is not credited as a rejecting shell control. Production callers consume canonical CTest XML; the local projection explicitly preserves that format and additionally parses XML structurally to reject duplicate/missing/unexpected identities before the shell check. The independent adversarial reviewer confirmed this producer-bound interpretation and the strict projection requirements. Canonical duplicate XML is rejected by both checks. The limitation is preserved in `build/phase23-recovery-combined-result-controls.json` rather than hidden.

Full execution and its complete result reconciliation are still pending; the single existing hosted attempt remains unused. This change consolidates evidence from the same complete test execution and introduces no repository source checker or production workflow change. Carry the duplicate-work lesson into phase closeout.

### D-174 full-run boundary refusal and integration result

The consolidated full run at `68c144be` refused `phase22_evidence_contract` with `source-package-boundary-changed:tests/scripts/verify-v02-source-archive.py`; its partial log is preserved as `build/phase23-recovery-68c144be-full.log`. This was the only observed substantive refusal before stopping that run. It is not a full/focused pass. Historical Phase 22 comparison rejected the intentionally approved D-168/D-172 harness changes, not an admitted fixture or a changed production archive validator.

Independent release review confirmed the exact baseline-to-b50 delta changes only three pre-existing harness definitions (`run_cli`, `self_test`, `_synthetic_core_product`) and adds self-test support; no existing production validator definition is changed or removed. Only this file differs in PRESERVED. D-174 therefore applies the already approved harness snapshot rather than waiving the preservation boundary: old baseline bytes remain valid, and only the archive path additionally accepts exact reviewed b50 bytes bound by SHA-256. Every other file remains historical-byte exact. The rule is shared by both entrypoints; arbitrary edits, unavailable pins and digest mismatches are refused. Whole-set counterpart controls and exact-path mutation controls exercise the actual shared rule.

At implementation `b312148d23993a210e3adbc943882d923eab8f36`, fresh configure/build passed. `phase22_evidence_controls` and `phase22_evidence_contract` passed in 46.81 seconds total; the contract took 4.83 seconds. Their original 60-second ceilings remain unchanged. All three independent roles accepted the new exact source and retained their historical findings. Remaining qualification uses one complete full execution with exact full/focused inventory validation; no hosted attempt, merge, tag or publication has started.

### Current full-run contention diagnosis (in progress)

At qualification `1626388a`, `phase23_review_evidence_controls` reached its unchanged 60-second ceiling while other large controls were active. The identical checker and synthetic fixture inputs passed in 35.98 seconds during the earlier 68c144be run. The current test has no processor reservation (default one slot); surrounding controls include delivery (49.11s) and support claims (42.77s). The fixed Phase 22 archive-boundary contract passed in 5.65 seconds. This full run remains diagnostic and is being allowed to finish to collect the complete failure set before one batch remedy.

Independent read-only scheduling analysis recommends a four-slot reservation for the review-evidence self-test only if an isolated bounded run confirms it passes. This follows the existing reservation mechanism, keeps its command/assertions/labels/60-second ceiling and global four-worker cap, and avoids changing merge-gate logic. The exact mechanical follow-up would add the test to the existing CMake four-slot reservation and PHASE23_RESERVED_TESTS, letting the existing registration validator and three-slot causal negative cover it; the coverage self-test total would increase from 598 to 599. This is a candidate remedy, not implemented or qualified evidence. Gather all full-run failures first, diagnose and retest the affected set without increasing limits, then review/finally qualify the resulting exact source. The single hosted attempt remains unused.

### D-175 complete failure set and reservation result

The full `1626388a564df8700278a0e0e8b433927aae9bdd` diagnostic completed in 2,182.74 seconds. Structural JUnit reconciliation found every required identity exactly once, no skipped case, and only `phase23_review_evidence_controls` failed (60.02-second timeout). All other required cases passed, including the fixed Phase 22 boundary contract, all docs controls, source archive, release lifecycle, package/consumer, fixture and policy controls. This failed run is preserved and does not qualify either full or focused gates.

The unchanged review-evidence checker, CMake fixture and expected inventory match 68c144be byte-for-byte; the same control passed there in 35.98 seconds. An isolated invocation at 1626388a passed in 22.71 seconds. D-175 applies only an existing four-slot CTest reservation, its mirrored PHASE23_RESERVED_TESTS membership and the resulting additional causal wrong-slot control (598 to599). It changes no checker logic, command, assertion, label, test identity, timeout, global concurrency, hosted cap or merge authority.

At exact implementation `5eefa412e679afe6044e3a80f93a73d269ec0c9d`, fresh configure/build passed. The review self-test passed in 34.47 seconds under its unchanged 60-second ceiling; both configured workflow-coverage CTests passed, for 39.69 seconds total. The immutable-source coverage self-test passed all 599 controls, including the new wrong-processor negative. Three independent delta reviewers accepted the source; role/report identity, size, schema and fixed-ancestor checks passed, and the historical 24/21/35 structured finding arrays remain unchanged in values and provenance. Final consolidated full/focused local qualification and the one existing hosted attempt remain pending.


## Recovery final local qualification and hosted attempt at88102b33

Qualification revision `88102b338a70503e345c821a098b3beece623235` contains three independent ACCEPT reports bound to implementation `5eefa412e679afe6044e3a80f93a73d269ec0c9d`. The immutable report gate passed all3 reports and80 preserved findings after the last source change. Configure/build passed. Full CTest with four workers passed all1,942 required identities in2,341.16 seconds with no skip. Strict structural JUnit reconciliation and the existing canonical inventory gate also establish all224 focused identities from that same execution. Failure/error/skip/missing/duplicate causal result controls reject. The existing line-oriented shell gate alone accepts an unsupported compact duplicate serialization; strict XML validation rejects it first. Supported canonical CTest input remains unchanged; this is recorded as an existing parser limitation rather than hidden or claimed fixed.

The one authorized hosted attempt started after those local gates, without advancing the frozen head: [CI42924124706](https://github.com/szTheory/gabbaboy/actions/runs/42924124706), [fixture42924124648](https://github.com/szTheory/gabbaboy/actions/runs/42924124648), and [preview42924124663](https://github.com/szTheory/gabbaboy/actions/runs/42924124663). Fixture reproduction passed; CI and preview are in progress. The non-version PR gate is conditionally skipped and supplies no qualification. PR146 remains unmerged. A failed hosted attempt requires evidence/diagnosis and a new owner decision before retry; no tag/publication is claimed.

Local ignored receipts: phase23-recovery-final-full.log/.junit.xml, phase23-recovery-combined-results.json, phase23-recovery-combined-result-controls.json, phase23-recovery-focused-from-full.junit.xml, phase23-recovery-final-report-gate.log. Full JUnit SHA-256:40e2410d2569b0c1c2abb960f90378600f7061735ad87ba5f8f8e7df0ab1c626. Do not commit these evolving observations into the frozen PR while its single attempt runs.


### Final hosted result at88102b33 — qualification refused

The single approved attempt completed without qualification. CI42924124706 was cancelled because native-linux-x64 hit its unchanged60-minute job cap (job3619s) after1936/1942 completed cases. It had already timed out v02_adoption_docs_controls90.02s and release_disclosure_controls60.07s; six test completions were unavailable. No incomplete stream is treated as an inventory pass. The three preview jobs failed downstream; required-native failed. No retry, merge, version PR, tag or publication was performed.

Passing producer evidence: native Windows1804/1804/no skips3078.88s test/3196s job; native macOS1942/1942/no skips2623.08s test/2722s job; CMake3.25.3 floor1942/1942/no skips2580.16s test/2673s job; sanitizer inventory1853/1853/no skips3156.69s test/3234s job; sanitizer acceptance80/80/no skips1201.67s test; sanitizer/fuzz202s job, performance57s, player package631s, and all7 fixture-reproduction jobs passed. The fixture workflow ran exactly once for this head (PR event), with no duplicate branch-push run.

The measured archive correction passed its unchanged90s test ceiling on every observed lane: Linux12.40s, Windows19.86s, macOS10.32s, sanitizer9.80s. The review reservation likewise passed6.24s/30.32s/13.73s/5.18s. The sanitizer consumer controls still appeared near the tail despite the COST hint, so no claim of actual first execution is made. Failed Linux logs and final run/job snapshots are retained in ignored build. Read-only source/log analysis and a disclosure profiler are active; no speculative producer-cap increase or hosted retry is made.


### D-176 targeted local preparation

Changed existing function ASTs are confined to the adoption self-test routines `run_self_test_release_notes`/`run_self_test_docs` and support-ledger `_self_test_disclosure`; production parser, claim and generator functions are unchanged. The source has no hardcoded version-dependent note-payload hash. The ignored baseline manifest compares exact case identities, outcomes, intended diagnostics and payload digests against `88102b33`. Real docs shards 0/20/21/199 and the standalone notes routine passed; the latter retained all 70 fresh calls (21 positive/49 negative) and its original return contract. Sparse note scheduling avoids work/allocation proportional to a caller-supplied shard count.

The disclosure CTest passed in 14.46 seconds under its unchanged 60-second ceiling. Its original 4 positives/20 controls and 6 real adoption CLI processes remain, with 2 additional pre-execution schedule controls. A first uncommitted helper run caught a NameError during refactoring; it was corrected before this passing run. The full-suite replacement ledger wrapper's wrong-checker control was accepted before the new binding; the corrected coverage self-test passed 603 controls, including intended wrong-checker/missing-mode/weakened-exit/weakened-marker refusals. Production workflow policy passed after removing only the duplicate Linux ledger preflight. The historical timeout citation and 60-minute cap remain.

These are targeted working-tree checks, not final source or hosted qualification. The lifecycle's strict adoption snapshot still requires the new immutable self-test bytes. Then the exact implementation must receive all three source reviews and one final consolidated full/focused local qualification before any new hosted-attempt decision. No push, retry, merge, tag or publication occurred.


### D-176 immutable snapshot integration

Commit `75797dd6de40491b7345a304d49c1920b73e6ffb` binds the locally checked harness changes. Its adoption script is byte-exact to the working file (SHA-256 `8268945bec5ccb69cb08af1519ce81f9faca2a4490bff4b236b498515aba6f6b`). Fresh configure/build passed at this source. The lifecycle main control also passed in 30.91 seconds; it does not exercise the recovery snapshot boundary and is not the pin refusal evidence.

The correct existing `release_lifecycle_post_tag_recovery_controls` test rejected the changed source in 0.21 seconds with `recovery-adoption-source` under the old pin. Only `RECOVERY_ADOPTION_PIN_SHA` advanced to the exact commit above; both immutable/current byte comparisons and all historical source/claims constants remain unchanged. The recovery control then passed in 1.62 seconds. Configured workflow coverage and its controls passed in 1.00/3.15 seconds (3.17 seconds total for the three tests), exercising the new candidate's CI body and the actual configured ledger command/marker. No source pin accepts arbitrary future bytes.

One configure/build invocation was started out of order during orchestration. The attributable build was interrupted, configuration was rerun to completion, and the build then completed successfully before these tests. No result from the interrupted build qualifies the candidate. The broader full run and exact-source reviews are still pending; no hosted retry was started.


### D-176 independent source review

Release/consumer, security and adversarial reviewers independently accepted exact implementation `7b2ecaf6adcb62590295045d997b451f943ec21f` with no new correctness/security blocker. Root independently reran the actual report parser and finding/ancestry validator after all writers finished. All80 historical finding records/provenance match88102b33 exactly; the existing low category-other resource note remains open. Distinct report/reviewer identities and all size bounds pass, including the compacted security narrative. Only report/evidence paths may change in the qualification commit; final local and any new hosted qualification remain unclaimed.

## D-176 final local results and bounded retests

Qualification source remains `76e32ae12d7717ce00e6360e1c787f1ba84ba944`, with reviewed implementation `7b2ecaf6adcb62590295045d997b451f943ec21f`. No source, assertion, scheduling property or timeout changed after the reviews. A fresh immutable report gate accepted all three reports and80 preserved findings.

The configured full run completed in3232.43seconds with all1942 required identities present once and no skips. It exited nonzero for five timeouts: release_version_v04_controls90.02s, workflow_policy_group_release_jobs180.01s, support_claims_v04_controls60.02s, release_lifecycle_controls60.01s and release_lifecycle_post_tag_publication_controls60.03s. The original full log/JUnit/process receipt and failed-full-summary are retained; this was not an all-green first stream.

Diagnosis found no attributable lingering worker. All seven production judge files used by lifecycle replay are byte-identical to88102b33. An exact-environment diagnostic ran the previous source in50.12seconds and current source in80.80seconds; current unchanged CTest subsequently passed in44.36seconds. The earlier ordinary-PATH trace used an older shell Python, failed a compatibility call, and is invalid evidence. The matching results demonstrate temporal execution variance; reported shared-host load supports contention, but CPU versus filesystem pressure is not established. No unrelated process was stopped and no foreground activation or machine restart was used.

Under T3's explicit preserve/diagnose/bounded-retest rule, the remaining four tests passed once with unchanged properties: workflow release jobs136.46s/180, release version65.59s/90, support claims53.58s/60 and post-tag publication24.66s/60. Together with the actual lifecycle44.36s/60 result, all required cases now have passing evidence at the same source. Strict reconciliation preserves the five initial failures and every original receipt; it establishes1942 full and224 focused identities, no skips and exact bounded-retest coverage. Ten targeted negative controls reject duplicate/missing identities, skips, errors, failed retests, nonzero exit and stale source. This is full-suite evidence with diagnosed bounded retests, not a rewritten green first run.

Ignored receipts: phase23-d176-final-full.log/.junit.xml, phase23-d176-failed-full-summary.json, phase23-d176-lifecycle-production-equality.json, phase23-d176-lifecycle-matching-trace.log/.json, phase23-d176-lifecycle-baseline-trace.log/.json, build/phase23-d176-lifecycle-after-baseline.junit.xml (relative to the build directory), phase23-d176-bounded-retest.log/.junit.xml/.json and phase23-d176-bounded-reconciliation.json. The original checkout's recovery backup contains copies plus the complete source bundle.

Local preparation is ready for the owner’s new hosted-attempt decision using existing configured caps. The prior single attempt was spent at88102b33; no new push, run, merge, tag or publication is authorized or performed. Keep the candidate frozen while waiting.

The owner subsequently approved one new hosted attempt. The frozen76e32ae1 push succeeded; current CI42948757274/preview42948757341 are running and fixture42948757366 passed all seven jobs. PR146 is unmerged. Synthetic merge70be2ce5350bd161ea73a43789349d4baeed1bc7 and the candidate have identical trees. No additional attempt is authorized.

## Current hosted attempt: floor deadline interruption (provisional)

CI42948757274 at76e32ae1 cannot qualify: job130287840113 (CMake3.25.3 floor) hit its configured50-minute cap. Its log contains1923/1942 unique passed completions, no failed/timeout/skipped completion, and19 unavailable results; incomplete evidence is not accepted. The full downloaded log and interruption/remaining-case comparison are retained. No source, cap or hosted retry changed.

Native Linux completed all1942 required cases in2522.14seconds, including docs56.42s/90 and disclosure31.84s/60; native macOS completed all1942 in2679.87seconds (docs32.73s, disclosure24.45s). Both jobs’ required inventory gates passed. These results establish the corrected controls fit their deadlines; overall timing differences cannot be attributed solely to the source changes because execution variance is observed. Fixture reproduction, sanitizer acceptance, sanitizer/fuzz campaign, performance and player package passed. Windows and sanitizer inventory remain in progress at this observation.

The unapplied build/phase23-floor-window-proposal.patch/.md proposes only floor50→60minutes and a corresponding historical-citation-preserving ledger disclosure. It passes git apply --check against the frozen source. The configured80-minute reader windows already cover a60-minute floor producer;70-minute Windows remains the dominant producer. Any adoption requires the owner’s new scope/cost decision, causal policy controls, exact-source reviews, local qualification and one new hosted-attempt authority. No cap, assertion, gate or source is waived by the proposal.

## D-176 terminal hosted result and complete budget proposal

All qualification workflows are terminal at76e32ae1, each required workflow attempt1 exactly once. CI42948757274 concluded cancelled; fixture42948757366 succeeded; preview42948757341 failed downstream. Required-native refused qualification. No retry, merge, tag or publication occurred.

Linux1942/1942/no skips2522.14s tests (job2763s), macOS1942/1942/no skips2679.87s tests (job2784s), Windows1804/1804/no skips3848.49s tests (job3993s). All earlier docs/disclosure failures are fixed at original limits: Linux56.42/31.84s, macOS32.73/24.45s and Windows63.93/41.37s (limits90/60). Original case coverage remains intact. Sanitizer acceptance, sanitizer/fuzz campaign, performance, macOS player producer and all seven fixture jobs passed. Downloaded preview qualification remains unavailable because required CI failed.

Floor job130287840113 reached its50-minute cap at1923/1942 unique passed completions,19 unavailable; sanitizer job130287840033 reached65minutes at1841/1853 unique passed completions,12 unavailable, with host_exit_crash_storm active. Both incomplete logs have no failed/timeout/skipped completion line. This establishes interruption, not success for the missing cases. Full logs/digests and strict count/name/index reconciliation are saved in phase23-d176-hosted-results-summary.json and hosted-final-jobs/runs.json. Variable runner execution remains the supported explanation; no new assertion failure is demonstrated.

The superseding unapplied phase23-window-proposal.md/.patch specifies floor50→60, sanitizer65→75, readers80→85, preview caps90→95 and release fuzz-reader142→147 with170 polls. Configured dependency path5+75+5=85minutes; release-reader bound8790s within8820s. Maximum extra configured runner budget is40minutes:10+10+four readers×5. Historical ledger citations/p50 fields stay unchanged. The patch passes git apply --check and changes no frozen source. Adoption requires a new owner scope/cost decision, paired stale-value controls, three independent source reviews, local full/focused evidence and one fresh hosted-attempt authority. No speculative cache, concurrency, dependency, test reduction or release-authority change is proposed.

Efficiency finding: remove measured duplicate work and balance existing cases first; those corrections passed on every native platform. Preserve successful unchanged local cases and retest only diagnosed failures where T3 explicitly permits it. Do not treat residual configured job-budget interruptions as assertions passing, or repeat an unchanged timed-out hosted run without resolving its cause and authority. Preview waiters already failed downstream promptly; no extra waiter cancellation or implementation change was necessary.

## D-177 approved implementation and source checks

The owner approved the bounded extension and one fresh hosted attempt after controls/reviews/local checks. Workflow/policy snapshot56ff25b6a9a9cad4bb19e4a367e3f7c937975a88 changes exactly the approved five files. The policy blob SHA256 is77d78361fd8005d61c9cb605549293ec6869cc40b4cfb5cc92a4d20c60fcf568. Its only AST changes are three self-test mutation-anchor literals; restoring those literals reproduces the prior AST, with all control labels/IDs intact. Producer/reader budgets and historical-citation-preserving ledger fields match D-177.

Direct source checks passed: production policy judge, CI112 controls, ledger20 and release_jobs186 manifest controls/167 negative controls. They used shell-selected Python3.9.6, not CTest’s configured Python3.14. In particular release_jobs’ approximate log duration206.4seconds is not a configured CTest timing or pass. No per-test deadline changed or blind rerun occurred. Exact configured qualification remains required.

The coverage owner retained the historical negatives and added17 current-old controls (11 profile and six ledger cases), with an explicit floor60 guard. A red probe confirmed the frozen old checker accepted floor50; green scoped probes refused every new old-value mutation, with exact-argv diagnostics retained for waiter changes and timeout-ledger-stale for ledger rows. The exact56ff25b6 policy byte pin is now integrated. Root reproduced the red/11-profile/six-ledger probes using the same Python3.14 binary configured by CMake; the receipt records requested and actual executable aliases. The committed620-control self-test remains pending final implementation selection. Source reviews and full/focused local qualification remain pending; no hosted attempt has started under D-177.

D-177 implementation is72b5db1b0a5f30017ba8404bffc564466af33bb3. The explicit immutable report gate refused old reports with review-implementation-mismatch, as intended. The immutable coverage self-test passed620 controls at that implementation using CMake-configured Python/PATH in3.91seconds. Three independent source reviews are active; no final qualification or hosted attempt is claimed. Receipts: build/phase23-d177/implementation-source.json, stale-reports-refused.log, coverage-immutable-selftest.log/.json, probe-configured.log/.json and policy-snapshot-proof.json.

The final reviewed implementation is96505505594612bec77f811acb7d0084cccffb94. Its only change after72b5db1b is four standalone sanitizer comments; non-comment workflow lines are identical. The configured production policy judge passes, and the immutable620-control self-test passes at this final source in3.61seconds. Stale prior reports again reject with review-implementation-mismatch. The earlier206.4second figure is an approximate file-timestamp interval under another interpreter, not a measured CTest runtime. All three reviewers were notified of the final immutable source.

All three independent D-177 roles accepted exact implementation96505505594612bec77f811acb7d0084cccffb94. Root waited for all writers to terminate, then ran the actual report parser/finding validators and compared all80 historical finding objects/provenance values with76e32ae1: unchanged. Reviewer/report identities are pairwise distinct; report sizes60835/63487/56643bytes remain below65536. The resolved scheduling-comment drift changes no non-comment line. No new correctness/security finding remains. The final report qualification commit and full configured local/hosted evidence are still required; this acceptance is not a CI pass.
