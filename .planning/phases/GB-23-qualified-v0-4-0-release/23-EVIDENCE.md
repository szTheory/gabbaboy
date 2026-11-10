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
