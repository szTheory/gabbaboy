# Phase 23 Independent Release / Consumer Review

**Reviewed implementation:** 7b2ecaf6adcb62590295045d997b451f943ec21f
**Review delta:** 88102b338a70503e345c821a098b3beece623235 through 7b2ecaf6adcb62590295045d997b451f943ec21f, with earlier Phase 23 review findings retained
**Role:** release-consumer
**Reviewer:** balanced-release-20261111

## Scope and conclusion

At exact implementation `7b2ecaf6adcb62590295045d997b451f943ec21f`, I independently reviewed the immutable D-176 delta from `88102b338a70503e345c821a098b3beece623235`. The change balances unchanged release-note CLI cases over existing docs shards, runs five independent disclosure CLI cases in a two-worker pool after the serial baseline, removes one duplicate Linux preflight while strengthening the full-suite CTest contract, and advances only the lifecycle recovery adoption-source pin to exact committed bytes. The existing per-call, CTest, and job limits and release/consumer authority remain unchanged. ACCEPT for this bounded release/consumer review: no new correctness, security, or release blocker was proven. This review does not qualify a new full local run or hosted CI; the 881 attempt remains failed evidence, and no retry is authorized here.

The prior review at `b312148d23993a210e3adbc943882d923eab8f36` covered the D-168 harness changes, D-169 worker lifecycle and release-reader correction, D-170 complete CI dependency window, D-171 fixture trigger reduction, D-172 extension of immutable blob caching into the isolated archive CLI worker, D-173 overlap of the unchanged lifecycle baseline sequence with independent controls inside the existing worker bound, and D-174 integration of the exact reviewed archive-harness snapshot into Phase 22's preservation guard. Its reader budgets matched the owner-approved values, worker cleanup preceded synthetic-directory removal even on exceptions, and immutable policy controls rejected the superseded budgets and lost fixture triggers. The cache retained only successful bounded immutable reads while fresh CLI namespaces and mutable product checks remained active. Lifecycle scenarios owned their mutable state, and baseline/control exceptions still prevented success. The preservation guard accepted only historical bytes or the specifically reviewed archive snapshot; every other preserved path remained baseline-exact. The existing release provenance, version-window, installed-consumer, product, and notice implementations had no source changes since the prior reviewed baseline. RC-01 through RC-23 retain their identities, fixes, and historical verification; RC-24 records the corrected release-reader dependency-window defect. Full final local and hosted qualification are separate pending gates, not established by either review.

The historical correctness/security findings were **BLOCKER** findings before remediation; the two historical low-severity quality records (RC-18 and RC-23) were **WARNING** findings. All structured records below are fixed. No necessity finding is asserted.

## Reserved-label contract

The seven exact label checks cover `fixture_product_core_controls`, `fixture_product_player_controls`, `fixture_admission_controls`, both `v02_consumer_controls_*` tests, and docs shards 108 and 114. Each expects the single label `v02`. Configured CTest inventories at the earlier reviewed revisions reported exactly that label for all seven. Their commands, timeouts, environments, COST settings, and working directories remain unchanged; the later D-162/D-163 scheduling updates alter docs-shard processor reservations, as described below.

The self-test fixture assigns each of the seven tests its expected label, then mutates each label to `unexpected` and requires rejection. The count increases from 128 to 135. Its positive Windows inventory still removes only `host_exit_crash_storm` and `save_format_controls`; these seven cross-platform tests remain required. The Windows-positive case and existing Windows negative cases pass within the 135-control self-test.

## Windows support-ledger environment-path contract

The checker parses CTest's support-ledger `ENVIRONMENT` property into unique key/value entries and requires the exact expected key set. It applies Windows path normalization only to `GBB_TEST_BUILD_DIR`; sanitizer options and all other environment values remain exact. The self-test retains the Windows inventory with POSIX-only registrations omitted, accepts an uppercase backslash spelling of the configured build path, and rejects a wrong Windows build directory. This exercises the Windows comparison on the local POSIX host through `ntpath`.

## D-162 scheduling and checker contract

The D-162 rescope records twelve docs shards that timed out without assertion output in the four-worker run and passed in isolated reruns. The implementation adds only `PROCESSORS 4` for those existing tests. Their CTest commands, positive/negative assertions, labels, and 90-second ceilings remain unchanged. The source-bound checker adds all twelve to both the reservation set and exact `v02` label map. Its existing generic reservation loop supplies one three-slot negative per shard, and the label loop supplies one wrong-label negative per shard. The Windows inventory continues to require these cross-platform docs shards; only the established POSIX-only tests are omitted. The later D-163 all-shard policy and two-slot amendment supersede this subset reservation.

## D-163 two-slot scheduling and checker contract

D-163 records that four-worker runs timed out different docs shards, while affected shards passed in isolation. The first all-shard change reserved four slots per docs test; the owner-approved amendment now reserves exactly two slots for all 200 controls. The rescope records a later exact-head run where native Linux completed all 1,942 tests, while macOS, CMake-floor, sanitizer-inventory, and Windows hit their existing job caps as docs shards continued in sequence. Two independent docs shards passed concurrently on the local Mac in 9.5 seconds. This evidence motivates the two-slot schedule but is not full qualification at bc282.

CMake sets `PROCESSORS 2` inside the registration loop for shards 1–199 and separately on `v02_adoption_docs_controls` (shard 0). The former four-slot settings are gone. Test registration commands, assertion regexes, `v02` labels, 90-second timeouts, and global `--parallel 4` are unchanged. The checker generates all 200 docs test names, requires exactly two slots and each exact label, rejects `PROCESSORS=4` for every docs test, and has a wrong-label negative per entry. Non-doc reserved controls retain four-slot requirements. The D-163 change itself did not edit CI workflows; D-164's separate native macOS cap amendment is reviewed below. Windows includes all 200 cross-platform docs controls and retains the existing support-ledger path-normalization controls.

## D-164 native macOS cap and ledger contract

At `48d8e501872b9a19138a4653830a40b983199adc`, only `native-macos` changes from a 40-minute to a 50-minute job cap. Its ledger row matches 50, retains the historical citation run `40156247875`, cited SHA, `p50_minutes=17.80`, and five samples. The disclosure explains the macOS-15 runner move and the exact-head run `42679813590` stopping at 1,928/1,942; the workflow comment explicitly says this run is workload evidence, not a new timing sample. The cap remains above `ceil(2 x 17.80)=36`. No other job timeout or per-test ceiling changed.

The coverage self-test accepts the source-bound 50-minute workflow/ledger pair and rejects a 40-minute ledger row as `timeout-ledger-stale`. Its first implementation read those files from the mutable working tree; that allowed `--rev c9a6320671b56d1092b2884aeac15d6a9320b60f` to pass while the checkout held the 50-minute change. RC-23 records this test defect. The fix at `48d8e501` loads the workflow inventory, workflow YAML, timeout ledger, and `CMakeLists.txt` from the supplied candidate commit using Git object reads before applying the negative mutation. At the reviewed SHA, the direct workflow-policy check passes and the 528-control coverage self-test passes; invoking the same self-test with c9 now rejects because that candidate still has a 40-minute cap.

## Verification

At 3c908d7, after a fresh configure pinned to that commit, the workflow-policy production check passed 540 controls across six groups, its self-test passed 135 controls, the focused exact-source CTest gate passed 14/14, and full local CTest passed 1,942/1,942. At b7d86939c25fca93dc928c494b9834513e5c1bc5, the direct exact-source self-test passed 136 controls and the two configured coverage CTests passed 2/2.

At b677a36e6523f65f838f2c53447b5a00394625d1, the direct production check passed 540 controls across six groups, the exact-source self-test passed 160 controls, and focused workflow-policy CTest passed 2/2. The configured inventory showed the twelve then-reserved shards with `PROCESSORS=4`, `TIMEOUT=90`, and `LABELS=[v02]`.

At 61f08de30b4f74ae539f827c5b04e1188fc3ea79, the production check passed 540 controls across six groups and the self-test passed 526 controls. Its configured inventory had all 200 docs controls at `PROCESSORS=4`, `TIMEOUT=90`, and `LABELS=[v02]`; focused CTest passed 2/2.

At exact source `bc282cc229c887d7034e533175249861db846154`, direct production check passed 540 controls across six groups, and the self-test passed 526 controls. After fresh `cmake --preset phase1` configuration, the focused workflow-policy CTest pair passed 2/2 with both commands pinned to bc282. The configured inventory has one registration per docs control; all 200 have `PROCESSORS=2`, `TIMEOUT=90`, and `LABELS=[v02]`, while all other reserved registrations remain at `PROCESSORS=4`. The self-test rejects `PROCESSORS=4` and wrong labels for each docs control and retains the Windows path-normalization positive and negative cases.

At `48d8e501872b9a19138a4653830a40b983199adc`, the direct workflow-policy check passes. The coverage self-test passes 528 controls against the reviewed candidate. Running that self-test with c9 as the candidate rejects the historical 40-minute macOS cap, confirming the timeout check reads the immutable candidate rather than the checkout.

Earlier hosted evidence remains historical: the 6ae run had a Windows support-ledger path-comparison failure and macOS/CMake-floor cancellations; the later four-slot exact-head run completed native Linux but hit existing job caps on macOS, CMake-floor, sanitizer-inventory, and Windows while shards continued in sequence. Neither establishes hosted success for bc282. No hosted result for bc282 was available in this review.

## Prior release and consumer findings

RC-01 through RC-22 retain their recorded identities, fixed dispositions, fix SHAs, and source-linked verification references. RC-22 is fixed at b7d86939c25fca93dc928c494b9834513e5c1bc5. RC-23 is fixed at 48d8e501872b9a19138a4653830a40b983199adc. All fixed SHAs resolve and are ancestors of this implementation.

The release/version-window, lifecycle, product/consumer, fixture, notice-path, adoption matcher, and planning-label implementations reviewed previously are unchanged. The D-163 amendment changes only CTest processor reservations and their coverage evidence; CI job caps and release, consumer, package, notice, and version-window boundaries remain intact.

## D-167 exact-source re-review

I re-reviewed `950c78b0bac936992403511a3cfa41f7cb1069c6`, compared with original candidate `029a77f5a87682cee545aa99edc1fe5263e5a77c` and the D-167 delta from `170b7eb2ba24ea166376ddf2088ce3d731fddc37`. ACCEPT; no release or consumer blocker. Windows remains 70 minutes; all three preview jobs retain 4,500-second waiters, 85-minute caps, and matching ledger entries. The disclosures correctly call ten minutes nominal, account for checkout/preflight time, and state that expiry fails the package job. The Linux runner is pinned to `ubuntu-22.04`; all three waiter jobs reject containers and services. Package build, smoke, receipt, artifact upload, version, and required release gates are unchanged. The source-bound coverage self-test passed 573 controls; workflow-policy `ci` and `ledger` groups passed; the configured focused Plan 23-04 selection passed 224/224 at this implementation source. No hosted CI ran during review.

## D-168 through D-171 exact-source review

This section records the review performed at `10fee4515c9db0e8b259e089ef2ec41f0453b811`. Its source delta is retained at the current implementation apart from the source-archive cache amendment reviewed separately below.

The changed source scope is `.github/ci-timeouts.json`, `.github/scripts/verify-workflow-policy.py`, the CI/preview/release/fixture-repro workflows, `tests/CMakeLists.txt`, and the candidate, support-ledger, source-archive, and workflow-policy-coverage checkers. I inspected their delta from the prior reviewed baseline and traced the worker/CLI, adoption-copy, immutable-blob, scheduling, and reader-policy call paths. Unchanged product/notice paths were cross-referenced through `verify-fixture-admission.py` and `verify-v02-adoption.py`. No source implementation was edited during this review.

### Harness behavior and cleanup

`verify-cgb-candidates.py:1809-2030` reuses one isolated interpreter but calls the actual CLI `main(args)` after a fresh `runpy.run_path` namespace load. The parent retains the 30-second queue deadline; each captured stream has its own 1,048,576-byte UTF-8 limit. Timeout kills and reaps the worker before a later invocation starts another worker. `:1915-1921` encloses the synthetic directory in a context manager whose `finally` stops the worker before `TemporaryDirectory` cleanup; this covers an exception anywhere in the test body. The causal cleanup control first substitutes a no-op stop and requires `candidate-subprocess-stop-failed`, then performs real cleanup. Its separate exception control verifies process exit and directory deletion after a synthetic exception. These are test-harness changes; admission/source/rights checks and the real outer CLI remain in place.

`verify-support-ledger.py:4213-4418` copies the adoption inputs once into a private self-test workspace. Each case rewrites that workspace's ledger, then invokes the unchanged adoption CLI in a separate process. I traced the generator and all existing altered-value, omission, handwritten-edit, and relocated-disclosure calls: they all retain their assertions and intended diagnostics. The adoption docs check reads these inputs; mutations from an earlier ledger do not survive the next explicit ledger overwrite. Production callers without a workspace retain a fresh temporary copy.

`verify-v02-source-archive.py:713-751` caches only successful immutable Git blob reads keyed by resolved repository, revision, and path, with 1 MiB per blob and 16 MiB total bounds. The source contract, current policy bytes, worktree checks, archive inspection, inventory, and notice checks are still executed. `:890-1085` reuses the real CLI parser/main in a fresh namespace per request, with separate output limits and a bounded response deadline; the existing overflow/deadline controls prove worker reuse after both failures. Unlike the CGB worker, this worker does not select the synthetic directory as its cwd. No Windows process-directory cleanup obstruction was found in this path. All original archive cases remain; the new worker controls add coverage.

The two consumer controls retain four CTest slots, their normal 600-second ceilings, and existing sanitizer timeout scaling. Only their COST hint becomes 1800 in sanitizer builds (`tests/CMakeLists.txt:1582-1591`). The registration checker requires the correct native/sanitizer COST and rejects native 601 and unscaled sanitizer 600. Its Windows fixture retains both controls. The only producer job-cap change in this delta is the approved sanitizer-inventory increase from 55 to 65 minutes. These scheduling hints do not prove final hosted completion.

### Complete reader dependency windows

RC-24 closes the prior short release-reader wait. All three preview waiters now use literal 4800-second deadlines with 90-minute job caps; `candidate-fuzz` uses 160 attempts at 30 seconds, a 4800-second deadline, and a 142-minute job cap (`release.yml:1152-1173`). The configured dependency path is five minutes for changes, 70 for Windows, and five for required-native. A shorter reader wait could expire before that successful path completed because the reader's prerequisites do not guarantee a head start. The release budget check accepts 4800 + 60 + 30 + 2700 + 900 = 8490 seconds within 8520. Preview's nominal ten-minute margin is reduced by checkout/preflight, as the ledger discloses. Hosted queue/service delays remain unbounded by this arithmetic; deadline expiry fails the gate.

The release reader still selects the exact-source main push run, validates its tag/source binding through the trusted checkout, downloads that run and attempt's fuzz/performance receipts, and uses the trusted validators. No publication privilege, receipt identity, package boundary, or release gate was weakened. Historical p50/run citations remain unchanged, and all four reader ledger rows disclose the changed budgets. The coverage checker loads workflows, CMake, and ledger through immutable Git reads before applying stale-value mutations. It rejects the prior 150-attempt/4500-second/137-minute release profile, the older 90-attempt/3000-second/112-minute profile, each former preview deadline/cap, and stale ledger rows. The final policy snapshot matches the actual approved D-170 mutation anchors; its independent baseline AST proof remains active.

### Fixture reproduction triggers

D-171 changes only `fixture-repro.yml:6` by limiting push branches to main. Every PR and manual dispatch still runs, and all seven job bodies are byte-identical to the prior source. This preserves required PR evidence, post-merge main evidence, and manual recovery while removing the measured duplicate feature-branch push matrix. Feature branches without a PR now need manual dispatch or a PR to obtain this evidence, as the decision records. The source-bound checker requires the exact event mapping in both its production check and self-test. Four causal mutations independently reject unrestricted pushes, missing PR coverage, missing dispatch recovery, and the wrong push branch.

### Evidence produced by this reviewer

Against final `10fee4515c9db0e8b259e089ef2ec41f0453b811`, an isolated Python check loaded the coverage verifier and candidate workflow bytes directly from Git objects. The exact reviewed-policy identity and independent baseline AST comparison passed. The approved timeout and fixture-trigger positive cases passed, as did the production release worst-case budget check; all thirteen targeted stale-budget/trigger mutations were rejected. Four mutations exercised the fixture triggers, three the release budget, and six the preview deadlines/caps. This was a focused boundary check, not another full coverage run.

Separate cheap worker reproductions passed: stdout overflow, stderr overflow, shortened timeout, reuse after timeout/overflow, exact exit-code/stdout/stderr preservation, the no-op cleanup negative, and cleanup after a synthetic exception for the CGB worker; source-archive's own overflow, shortened deadline, reuse, and explicit-stop controls passed. The shortened timeouts make these causal reproductions fast; source inspection confirms the real 30-second candidate deadline remains unchanged. They do not claim a live Windows execution or a full-suite timing result.

Prior fixed SHAs were checked for existence and ancestry to the final implementation. The recorded historical verification above remains historical. The parent qualification run owns the final configured/focused/full suite and hosted attempt; no expensive suite or hosted run was launched by this reviewer. Those gates must pass at the actual qualification head before merge/release authority is exercised.

## D-172 isolated archive-worker cache delta

I inspected the complete immutable delta from `10fee4515c9db0e8b259e089ef2ec41f0453b811` to `b50f0c10e0794591a212edbfd083f10084805532`. Only `verify-v02-source-archive.py` and the decision/rescope records change. The unchanged 90-second CTest timeout at 10fee remains failure evidence; the timing profile motivates this cache extension but does not establish the new head's qualification.

`verify-v02-source-archive.py:713-751` now shares the same cache wrapper between the parent harness and fresh CLI helper namespaces. Each process has its own 8 MiB retained-data budget, preserving the previous combined 16 MiB ceiling; each retained entry is at most 1 MiB. A cache key contains the checker source digest, canonical repository root, full lowercase 40-character revision, and path. Symbolic revisions bypass caching. The original bounded blob read completes successfully before an entry is added, so errors are not retained. The wrapper substitutes only `blob()`; I traced `verify-fixture-admission.py:934-949` and confirmed that source policy, repository, notice, and current worktree-byte comparisons continue to run. A cache hit does not substitute a previous product verdict.

The worker still loads the actual script and helper into a fresh namespace for every parser/main invocation (`:991-1003`). It retains one bounded immutable-byte dictionary outside those namespaces, not prior CLI globals or mutable check results. Each returned cache hit/byte statistic is type-checked, negative hits and excess bytes reject, and the self-test requires real worker cache reuse (`:1127-1140`, `:1912-1913`). Every original archive/product/notice case and CLI call remains in the delta; timeout/output handling, job caps and CTest registration are unchanged.

I executed the cache's exact-source boundary controls from the b50 Git object in isolation. They passed identity separation for repository/revision/path/checker bytes, moved symbolic refs, exact aggregate capacity, excess capacity, and oversized entries. I also reran the cheap worker overflow, shortened deadline, reuse, and explicit-stop controls successfully with the new response fields. No full archive self-test, expensive suite or hosted run was started by this reviewer. Final configured CTest timing and full local/hosted qualification remain the parent's responsibility; no success at b50 is inferred from the previous head's results.

## D-173 lifecycle scheduling delta

I inspected the immutable implementation delta from b50 to `33a1e7faf0c4126a4840e3c1c55ee9d1589d2593`. Its only source change is `verify-release-lifecycle.py:3761-3772`: the unchanged serial `positive_baselines(ctx)` sequence is submitted as one task to the existing `ThreadPoolExecutor(max_workers=PARALLEL)`. The baseline result is awaited and added to the positive count, and every negative-control future is still awaited on a successful path. A baseline or control exception escapes `controls()`; the executor context waits for pending work during unwinding, so no failure can be converted to a passing result. The baseline uses one slot of the same pool, without a nested executor or an increased worker ceiling.

I traced all three baseline functions through `Context.scenario`, `Scenario`, and their production gate helpers. Each baseline creates its own scenario; scenario numbering uses `_COUNTER_LOCK` (`:2041-2052`), copied stub state, separate workspaces/home/temp directories, and per-process environment dictionaries. `build_stages(ctx)` and judge-integrity checks complete before task submission. Baselines read the finalized `manifested`/`finalized` stage trees and judge repository; their gate execution mutates only their scenario copies. They do not call `snapshot()`, write `Template.stages`, or alter shared context/files. The existing task2/task3 control builders only assemble independent callables. Thus the new overlap introduces no shared mutable release state or prerequisite race. The baseline sequence, actual production script calls, case membership, counts, `PARALLEL`, CTest RUN_SERIAL and 60-second ceiling are unchanged.

For cheap causal evidence, I extracted the exact committed `controls()` AST and ran its orchestration with synthetic dependencies and two worker slots. A baseline that waited for a negative task to start completed, proving overlap without an increased pool. Separate injected baseline and negative-control exceptions both propagated with their original marker; the successful case retained the expected positive/control totals. This probe checks scheduling and failure propagation, not real release behavior or timing. The earlier d5b 60-second CTest failure remains failure evidence; the matching-environment 64.09-second diagnostic is historical. The parent owns the affected real CTest and final focused/full/hosted qualification at the new head; none was duplicated by this reviewer.

## D-174 exact archive snapshot integration

Before implementation I compared the complete f2542c80-to-b50 archive-checker delta and every PRESERVED path at the failed qualification source `68c144be`. Only `verify-v02-source-archive.py` differed among preserved files. Its changed existing definitions were the self-test helpers `run_cli`, `_synthetic_core_product`, and `self_test`; additions implement the bounded worker/cache already reviewed under D-168/D-172. Production archive/fixture validation was unchanged. I recommended applying that already approved harness change through an exact immutable snapshot exception, with the original baseline retained and no arbitrary successor acceptance. The full-run refusal remains recorded failure evidence; the integration does not convert that run to a pass.

I reviewed the exact implementation delta from 33a to `b312148d23993a210e3adbc943882d923eab8f36`. `verify-diagnostic-evidence.py:25-30` keeps BASELINE unchanged and names only the archive checker, full b50 revision, and the independently checked SHA-256 `5a3083b6a7d32c0692672645564241a81d9be0b0939c9ee198afb951f43f183a`. PRESERVED is unchanged. `:840-858` accepts baseline bytes first; otherwise only the archive path can match the exact pinned blob, whose missing object or digest mismatch rejects. No current checkout, descendant commit, caller-supplied policy, or generic source-equivalence exception is used. Both `validate_boundaries()` and `validate_preserved()` reach this one path rule, avoiding separate acceptance policies.

The delta leaves added-payload detection, forbidden fixture directories, the synthetic source requirement, all seven unresolved gates, assessment/inventory facts, Pending requirements, historical boundary checks, and CTest inventory/timeouts intact. Self-test controls accept the whole baseline set and the baseline set with the reviewed archive substituted, then mutate every preserved file independently. They require the exact offending-path rejection, preventing credit from an unrelated preserved-file failure; separate missing-pin and wrong-digest controls remain closed.

Using the b312 checker read directly from its Git object, I ran only the isolated preservation rule: both full-set positive counterparts passed, all twelve preserved-file mutations rejected with their exact path, and both invalid-pin controls rejected with their intended diagnostic. This is fourteen targeted negative checks, not the complete Phase 22 control/contract or a full qualification run. Historical findings remain fixed and unchanged; no new open release/consumer finding was proven. The parent owns the affected configured checks and final local/hosted qualification. No source changes, expensive duplicate suite, or hosted attempt was made by this reviewer.

## D-175 release-consumer reservation delta

The exact `b312148d23993a210e3adbc943882d923eab8f36` to `5eefa412e679afe6044e3a80f93a73d269ec0c9d` source delta adds `phase23_review_evidence_controls` to the existing CMake `PROCESSORS 4` property group. Its registered command, marker, `v02;planning` labels, 60-second timeout, and expected-test inventory entry are unchanged. The D-175 rescope records that this unchanged control passed isolated at 22.71 seconds, while a full 1,942-test run with no skips reached its existing 60-second timeout at 60.02 seconds under competing load; the reservation uses the existing four-slot ceiling and does not increase CTest's global parallelism.

The immutable workflow-policy checker adds this test to `PHASE23_RESERVED_TESTS`, which feeds the processor-reservation validator. The validator requires one CTest registration, an inventory entry, and exactly four slots for this non-doc control. Its self-test fixture now includes the reservation with four slots; the generic reservation mutation changes it to three and calls the same validator, producing one additional causal negative and changing the expected control total from 598 to 599. A cheap source-bound probe compared the immutable b312 and 5eef blobs and confirmed the inventory/property membership, validator rule, synthetic fixture, three-slot mutation, and count change. The parent reports that fresh exact-source configure/build and registration checks passed; the review-evidence controls completed in 34.47 seconds under the unchanged 60-second limit, both workflow-policy coverage checks passed, and the 599-control immutable self-test passed. I did not duplicate those checks or the expensive full suite. No new release/consumer correctness or security finding was found.

## D-176 exact-source release-consumer review

I reviewed the complete immutable source delta from `88102b338a70503e345c821a098b3beece623235` to `7b2ecaf6adcb62590295045d997b451f943ec21f`, including the actual parent commits that implement the D-176 preparation and bind its lifecycle source snapshot.

`verify-v02-adoption.py` keeps the same 21 positive and 49 negative release-note cases, with stable IDs and unchanged payloads and expected diagnostics. `release_notes_case_schedule()` stores only buckets containing assigned cases, so its work and memory scale with the 70-case inventory rather than the configured shard count. The validator requires every intended ID exactly once in its ordinal modulo bucket; the self-test rejects a missing, duplicate, or misplaced case. Each selected case still writes its own payload and invokes a fresh production `--release-notes` CLI process, then the runner checks that the executed IDs match the selected IDs. With no shard argument, the original full case set runs; the standalone release-note route still runs that same set. The one-off manifest comparison against the 881 baseline checks exact IDs, payloads, and diagnostics without adding a version-pinned production hash. The parent supplied targeted evidence that docs shards 0, 20, 21, and 199 and the standalone 70-case route passed.

`verify-support-ledger.py` retains the initial adoption CLI in its serial generator check. The next five named actual CLI cases run through `run_disclosure_adoption_cases()` with `max_workers=2`; each receives its own copy of the same checked baseline and a fresh isolated Python CLI with the existing 45-second per-call deadline. The parent imports immutable path metadata before starting threads. Every worker result and exception is collected before the thread pool and temporary workspace close, then all expected return codes and rejection diagnostics are checked. The four original positive outcomes and 20 original controls remain, with two schedule negatives added. The parent reports that the configured disclosure CTest passed in 14.46 seconds and retained the original outcome counts.

The Linux workflow removes only its duplicate pre-build support-ledger self-test. The full CTest registration still runs the real `verify-support-ledger.py --self-test`; the immutable coverage checker now requires the exact script, self-test mode, zero exit expectation, and complete output marker. Its causal controls reject a wrong checker, missing mode, weakened expected exit, and weakened marker. The parent reports the 603-control workflow-policy self-test and configured policy checks passed. The timeout ledger changes only its explanation of the Linux job body: its 60-minute cap and historical citation fields are unchanged. No CI job cap, per-test timeout, reader budget, workflow publication authority, package/product path, or release/consumer contract changed.

The lifecycle change advances only `RECOVERY_ADOPTION_PIN_SHA` to `75797dd6de40491b7345a304d49c1920b73e6ffb`, the exact source commit containing the new adoption self-test. The lifecycle checker still compares the requested revision's adoption checker bytes with the immutable pin and separately with the current checkout bytes. The original historical recovery pin and all other recovery assertions remain intact. The parent reports that the stale-pin negative refused the old pin and the new pin control and lifecycle CTest passed.

These are bounded source-review conclusions with owner-supplied focused-check evidence. I did not run a CPU-heavy suite or hosted workflow. The new source's full local and hosted qualification remain unproven; the failed 881 attempt is not converted to a pass, and this review does not authorize another hosted attempt. The existing historical RC-01 through RC-24 structured records and their provenance values below are unchanged from 881.

<!-- gbb-review-evidence:start -->
```json
{
  "schema_version": 1,
  "report_id": "gb-23-release-consumer-7b2ecaf6-20261111-balanced-release",
  "role": "release-consumer",
  "reviewer_id": "balanced-release-20261111",
  "independent": true,
  "reviewed_sha": "7b2ecaf6adcb62590295045d997b451f943ec21f",
  "findings": [
    {
      "id": "RC-01",
      "category": "correctness",
      "severity": "high",
      "required_property": "Version-PR checks validate the exact tracked 0.4.0 output and release-note disclosures against the generated PR head using trusted verifiers.",
      "disposition": "fixed",
      "rationale": "The direct version-PR gate and regenerated-version-PR path invoke the trusted window checker, the separate tracked-version assertion, and the release-note checker against the exact PR head.",
      "fix_sha": "9e09eef8b379ca8d329cb13bf354058661296daa",
      "verification_ref": "Reviewed source: .github/workflows/version-pr-gate.yml and .github/workflows/release-please.yml; paired workflow-policy and version-window controls are registered in tests/CMakeLists.txt."
    },
    {
      "id": "RC-02",
      "category": "correctness",
      "severity": "high",
      "required_property": "A changelog ledger reference is visible Markdown linking the exact supported ledger; incomplete raw-HTML openers cannot hide it.",
      "disposition": "fixed",
      "rationale": "The production version-window checker masks comments and code, rejects raw HTML constructs in the judged prefix, and requires an exact ledger link. Its controls cover incomplete openers before the heading and inside the release section, visible-link counterparts, and a causal former-matcher comparison.",
      "fix_sha": "a63f1dc67654613e105ac1071b7445f21adea0bc",
      "verification_ref": "Reviewed source: tests/scripts/verify-version-window.py validate_version_outputs, RAW_HTML_CONSTRUCT, and incomplete_html_openers controls."
    },
    {
      "id": "RC-03",
      "category": "correctness",
      "severity": "medium",
      "required_property": "Normal inactive-window development evaluation passes while exact 0.4.0 output and release-note rules remain enforced when a version PR exists.",
      "disposition": "fixed",
      "rationale": "The release-please version-window job exits normally when no version PR exists; when one exists, it checks the active window, exact tracked 0.4.0 output, and generated notes.",
      "fix_sha": "9e09eef8b379ca8d329cb13bf354058661296daa",
      "verification_ref": "Reviewed source: .github/workflows/release-please.yml version-window discovery, inactive early exit, and exact PR-head checks."
    },
    {
      "id": "RC-04",
      "category": "correctness",
      "severity": "high",
      "required_property": "Required public support and limitation disclosures must be visible prose and cannot be satisfied by hidden code or Markdown metadata.",
      "disposition": "fixed",
      "rationale": "The shared visible-phrase checker masks code spans, link titles, image syntax, and reference metadata before checking required clauses; paired mutations expect the missing-disclosure diagnostic.",
      "fix_sha": "c4ed9eed86871db9f9dc225565a85a55ab0a8036",
      "verification_ref": "Reviewed source: tests/scripts/verify-v02-adoption.py visible_phrase_source, check_phrases, public-surface controls, and current release-guide checks."
    },
    {
      "id": "RC-05",
      "category": "correctness",
      "severity": "high",
      "required_property": "Third-party fixture rights rows are visible and bound to the corresponding fixture manifest and license bytes.",
      "disposition": "fixed",
      "rationale": "The notice checker extracts only visible rows, matches them to the actual fixture inventory, and verifies manifest and LICENSE.txt digests before accepting each row.",
      "fix_sha": "3083aa7184719108c6b8ae4cdca22986329bfea7",
      "verification_ref": "Reviewed source: tests/scripts/verify-v02-adoption.py check_notices, visible_notice_matches, fixture_directories, and per-row disclosure controls."
    },
    {
      "id": "RC-06",
      "category": "correctness",
      "severity": "high",
      "required_property": "Unsupported game claims cannot be hidden by the five reviewed Markdown interactions involving image labels, tab-expanded list continuation, HTML comments, false fences, or a bracket inside a URI autolink.",
      "disposition": "fixed",
      "rationale": "The production prose matcher preserves those distinctions and pairs each unsafe case with a valid collapsed reference, list continuation, matching-comment reference, real fence, or valid autolink-title case.",
      "fix_sha": "4bb708fd137f7831b9af720220a09cee57e8d47c",
      "verification_ref": "Reviewed source: tests/scripts/verify-v02-adoption.py Markdown masking and the D-144 paired production CLI controls, including distinct comment payloads."
    },
    {
      "id": "RC-07",
      "category": "correctness",
      "severity": "high",
      "required_property": "Visible unsupported CGB-game claims are detected across literal format/default-ignorable characters and valid CommonMark character references while code remains masked.",
      "disposition": "fixed",
      "rationale": "The claim-specific matcher uses the frozen Unicode 18.0 default-ignorable set, removes the scoped invisible characters, and decodes valid references after prose masking without changing disclosure matching.",
      "fix_sha": "fc0ba4ff9626e06e04d8800800561b51414166bf",
      "verification_ref": "Reviewed source: tests/scripts/verify-v02-adoption.py unsupported_game_claim_match, Unicode 18.0 table, reference decoding, and paired README/release-note controls."
    },
    {
      "id": "RC-08",
      "category": "correctness",
      "severity": "high",
      "required_property": "Unsupported CGB-game claims split by CommonMark backslash hard line breaks are detected in public documents, notices, and release notes after code masking.",
      "disposition": "fixed",
      "rationale": "The claim matcher normalizes backslash hard breaks across LF, CR, and CRLF. The notices caller supplies uncollapsed code-masked prose, and controls preserve soft breaks, safe text, and code as valid counterparts.",
      "fix_sha": "e26757fafc818a92ddf7ca45f1a409658a5a5bdd",
      "verification_ref": "Reviewed source: tests/scripts/verify-v02-adoption.py COMMONMARK_HARD_LINE_BREAK, check_notices, and D-149 production controls."
    },
    {
      "id": "RC-09",
      "category": "correctness",
      "severity": "high",
      "required_property": "Visible unsupported claims cannot evade matching through CommonMark emphasis or inline-link labels; destinations, titles, and code remain non-prose.",
      "disposition": "fixed",
      "rationale": "The claim-only normalization strips paired emphasis delimiters and exposes inline-link labels after code masking while excluding destination and title text; escaped, intraword, destination-only, and code counterparts remain accepted.",
      "fix_sha": "e017078b72e78b38fb596faced3af3e35c2ca0ce",
      "verification_ref": "Reviewed source: tests/scripts/verify-v02-adoption.py normalize_commonmark_emphasis, inline-link label handling, and D-150 paired controls."
    },
    {
      "id": "RC-10",
      "category": "correctness",
      "severity": "high",
      "required_property": "Claims split across valid shortcut, full, or collapsed reference-link labels are detected while destinations, titles, unresolved labels, escaped brackets, and code remain non-prose.",
      "disposition": "fixed",
      "rationale": "Production callers render valid link labels only for the unsupported-game claim matcher, which excludes reference suffixes, destinations, and titles. Paired controls cover all three forms and their safe counterparts in docs, notices, and release notes.",
      "fix_sha": "b798781105b8f6f803e85aa2ad766d2b2fdbec22",
      "verification_ref": "Reviewed source: tests/scripts/verify-v02-adoption.py prose(..., render_link_labels=True), check_notices, and D-151 paired shortcut/full/collapsed-reference controls."
    },
    {
      "id": "RC-11",
      "category": "security",
      "severity": "high",
      "required_property": "Attacker-controlled unmatched emphasis runs do not cause quadratic work in claim normalization, while paired emphasis and rule-of-three behavior remain correct.",
      "disposition": "fixed",
      "rationale": "The matcher uses per-marker delimiter candidate stacks rather than rescanning all earlier runs. Dense unmatched-marker controls cover docs, notices, and release notes, with paired safe emphasis cases.",
      "fix_sha": "6876fab06bf746fdaab67beaa4d52a6b1c70ac06",
      "verification_ref": "Reviewed source: tests/scripts/verify-v02-adoption.py normalize_commonmark_emphasis and D-152 dense unmatched-marker and safe-prose controls."
    },
    {
      "id": "RC-12",
      "category": "correctness",
      "severity": "high",
      "required_property": "Unicode punctuation and symbol flanking cannot hide an unsupported CGB-game claim around CommonMark emphasis markers.",
      "disposition": "fixed",
      "rationale": "Emphasis flanking treats Unicode punctuation and symbol categories as punctuation only in the unsupported-game matcher; paired symbol-emphasis claims and safe-prose cases are covered.",
      "fix_sha": "4c9c54f8b5a33e758624c997f107d1ffdd7c94a0",
      "verification_ref": "Reviewed source: tests/scripts/verify-v02-adoption.py normalize_commonmark_emphasis and D-153 docs, notice, and release-note controls."
    },
    {
      "id": "RC-13",
      "category": "security",
      "severity": "high",
      "required_property": "Impossible reference-label candidates are rejected before copying or normalization so nested or overlong spans cannot cause repeated quadratic work.",
      "disposition": "fixed",
      "rationale": "The checker uses constant-time nested-bracket prefix and 999-character span checks before candidate normalization, while valid reference-link labels retain their existing rendering.",
      "fix_sha": "4c9c54f8b5a33e758624c997f107d1ffdd7c94a0",
      "verification_ref": "Reviewed source: tests/scripts/verify-v02-adoption.py normalized_reference_label_span, shortcut/full/collapsed link call sites, and D-154 dense claim/safe controls."
    },
    {
      "id": "RC-14",
      "category": "security",
      "severity": "high",
      "required_property": "Notice fixture reads and self-test copies remain confined to their repository and isolated destination roots, including traversal and symlink paths.",
      "disposition": "fixed",
      "rationale": "D-155 rejects traversal and backslash components, resolves source inputs and copy destinations, checks containment, and keeps failures closed. The reviewed implementation contains paired traversal and symlink controls for notice inputs and copy destinations.",
      "fix_sha": "9166ab60d25c6d246761b4aa33a0ceb35dd83f5c",
      "verification_ref": "At b75ecb97d8ab11cda5dcb3cc94a87363e60f0cae, the D-155 checker blob is byte-identical to 9166ab60d25c6d246761b4aa33a0ceb35dd83f5c; docs shard 0 passed 473 checks with two selected negative controls rejected."
    },
    {
      "id": "RC-15",
      "category": "correctness",
      "severity": "high",
      "required_property": "The post-tag recovery control pins and byte-compares the exact reviewed adoption checker while preserving the original historical recovery source pin.",
      "disposition": "fixed",
      "rationale": "D-156 updates only RECOVERY_ADOPTION_PIN_SHA to the D-155 implementation source. The checker still compares bytes from the requested revision, the immutable pin, and the working tree; the recovery control passes at this revision.",
      "fix_sha": "bd5ab993a3f09307e6a5ef31185f554740a0787b",
      "verification_ref": "At b75ecb97d8ab11cda5dcb3cc94a87363e60f0cae: python3 -I tests/scripts/verify-release-lifecycle.py --rev b75ecb97d8ab11cda5dcb3cc94a87363e60f0cae --self-test-post-tag-recovery passed with 99 controls and 12 positives."
    },
    {
      "id": "RC-16",
      "category": "correctness",
      "severity": "high",
      "required_property": "Timeout-budget rows must cite a decision present in the plan-pinned and PR-base commits used by the immutable checker, while retaining documented timeout policy and shard-inventory provenance.",
      "disposition": "fixed",
      "rationale": "The corrected inventory maps shards 01–31 to D-069 and 32–199 to D-068. Both decisions exist in the plan-pinned f2b base and PR base 1ab65414; D-068 records the all-build-leg inventory provenance and D-069 remains the timeout policy. The exact plan command and PR-base checker both pass against the reviewed source.",
      "fix_sha": "7c6f01ad5ecf3b6736bf694324acc1671d9e20cc",
      "verification_ref": "At b75ecb97d8ab11cda5dcb3cc94a87363e60f0cae, the plan-pinned checker passed with tests=1936 and allowlisted=288. The checker copied from PR base 1ab65414d60828fa9505babeaeea9de0571f016c also passed against that base. The inventory has 199 shard rows: 31 D-069 and 168 D-068; CI reads the checker from BUDGET_BASE."
    },
    {
      "id": "RC-17",
      "category": "correctness",
      "severity": "high",
      "required_property": "The workflow-policy coverage gate must pin the exact reviewed D-157 policy source and preserve baseline checks for unchanged policy functions.",
      "disposition": "fixed",
      "rationale": "At 013703528fcba6bce371887d5e6dec757e103ecf, the policy checker changed while the coverage verifier still pinned the older 9e09eef snapshot, so the exact coverage check rejected the candidate source. ecdde9d5 updates the immutable snapshot to the D-157 policy blob at 01370352 and adds the changed functions to the exact reviewed-function set while retaining the baseline AST comparison for the remaining functions.",
      "fix_sha": "ecdde9d5f63500dd0ad32d9e101f47e29ded0eb2",
      "verification_ref": "At 3c908d7f5a927953b84dd6123c497ec9907cac8b, after a fresh configure pinned to the reviewed commit, the workflow-policy production check passed 540 controls across six groups and the self-test passed 135 controls; the focused exact-source CTest gate passed 14/14. The exact D-157 policy snapshot remains pinned to 013703528fcba6bce371887d5e6dec757e103ecf."
    },
    {
      "id": "RC-18",
      "category": "other",
      "severity": "low",
      "required_property": "The CMake-floor workflow comment should state the current 50-minute job cap or clearly identify the 40-minute figure as historical.",
      "disposition": "fixed",
      "rationale": "The CMake-floor job has timeout-minutes: 50 and the adjacent comment now says \"20-40 of these 50 minutes,\" removing the cap mismatch.",
      "fix_sha": "b75ecb97d8ab11cda5dcb3cc94a87363e60f0cae",
      "verification_ref": "At b75ecb97d8ab11cda5dcb3cc94a87363e60f0cae, .github/workflows/ci.yml sets the floor job to 50 minutes and its comment references those same 50 minutes."
    },
    {
      "id": "RC-19",
      "category": "correctness",
      "severity": "high",
      "required_property": "The release-notes planning exception must compare the configured repository argument using Windows host path case rules, just like its output path.",
      "disposition": "fixed",
      "rationale": "The checker now compares normalized wrapped[9] to normalized source for the renderer --repo path, normalizes the renderer --output path, and normalizes the review-evidence --repo path. The self-test includes a wrong-repository negative plus simulated Windows case variants for renderer output, renderer repository, and review-evidence repository; all 33 controls pass on POSIX.",
      "fix_sha": "b75ecb97d8ab11cda5dcb3cc94a87363e60f0cae",
      "verification_ref": "At b75ecb97d8ab11cda5dcb3cc94a87363e60f0cae, python3 -I tests/scripts/verify-planning-labels.py --self-test passed with controls=33; the POSIX simulation exercises case-insensitive renderer output, renderer repository and review-evidence repository paths."
    },
    {
      "id": "RC-20",
      "category": "correctness",
      "severity": "high",
      "required_property": "The workflow-policy coverage checker must accept the actual D-158 CTest registration for v02_support_ledger_controls, including its existing helper-generated ENVIRONMENT and LABELS properties, while enforcing PROCESSORS=4 and the normal/sanitizer timeout mapping.",
      "disposition": "fixed",
      "rationale": "The d0fb checker now models and validates the actual support-ledger test contract: exact 120-second normal/360-second sanitizer timeout, PROCESSORS=4, GBB_TEST_BUILD_DIR (plus the sanitizer link-option environment when enabled), and the planning/v02 labels. The self-test fixture includes the real environment and labels; it rejects a missing planning label, unexpected environment entry, a 119-second native timeout, an unscaled 120-second sanitizer timeout, and PROCESSORS=3 for the support control and each D-157 reservation. The exact configured coverage check and all three selected CTests pass at d0fb, closing the af5 mismatch.",
      "fix_sha": "d0fb68361f3ffd82e1205e16609f644d4f733df2",
      "verification_ref": "At 3c908d7f5a927953b84dd6123c497ec9907cac8b: after fresh configure, the exact workflow-policy production check passed 540 controls across six groups; self-test passed 135 controls; the focused exact-source CTest gate passed 14/14; and full local CTest passed 1,942/1,942. The current Windows fixture retains cross-platform support-ledger tests and runs its positive inventory path; the d0fb fix for actual ENVIRONMENT/LABELS remains an ancestor."
    },
    {
      "id": "RC-21",
      "category": "correctness",
      "severity": "high",
      "required_property": "The workflow-policy coverage self-test must construct exactly one synthetic CTest registration for each reserved test, including reserved policy groups that already have a group fixture.",
      "disposition": "fixed",
      "rationale": "The self-test fixture builder now appends only reserved names that are not already policy-group registrations, so workflow_policy_group_ci and workflow_policy_group_rehearsal each appear once. Both remain in PHASE23_RESERVED_TESTS and the common three-slot mutation loop, preserving their individual reservation negatives. The Windows inventory positive and negative cases now execute after the initial POSIX fixture validates. The exact checker self-test reaches 128 controls, the configured coverage check passes, and both coverage CTests pass.",
      "fix_sha": "4343d95dde8597253994efff2e030ae25089d288",
      "verification_ref": "At 3c908d7f5a927953b84dd6123c497ec9907cac8b, after fresh configure, workflow-policy production check passed 540 controls across six groups, self-test passed 135 controls (including one wrong-label negative per reserved v02 test and Windows inventory fixtures), focused exact-source CTest passed 14/14, and full local CTest passed 1,942/1,942. The configured CTest inventory reports LABELS=[v02] for all seven reserved v02 tests; CMake registration/properties are unchanged in the 4343-to-3c source delta."
    },
    {
      "id": "RC-22",
      "category": "correctness",
      "severity": "high",
      "required_property": "The Windows workflow-policy coverage check accepts case- and separator-equivalent spellings of the configured support-ledger build-directory environment path, while rejecting a different directory and preserving exact non-path environment values.",
      "disposition": "fixed",
      "rationale": "At 6ae, the required Windows workflow_policy_coverage check failed because the checker compared the support-ledger ENVIRONMENT path as a raw string. The b7 checker parses unique environment entries, applies ntpath normalization only to GBB_TEST_BUILD_DIR on Windows, and keeps the expected environment-key set and other values exact. Its self-test accepts an uppercase backslash path variant in a Windows inventory and rejects a wrong build-directory path.",
      "fix_sha": "b7d86939c25fca93dc928c494b9834513e5c1bc5",
      "verification_ref": "At b7d86939c25fca93dc928c494b9834513e5c1bc5, python3 -I tests/scripts/verify-workflow-policy-coverage.py --self-test --root . --rev b7d86939c25fca93dc928c494b9834513e5c1bc5 passed with 136 controls. The configured workflow_policy_coverage and workflow_policy_coverage_controls CTests both pin --rev to b7 and passed 2/2. The hosted 6ae Windows failure predates this fix; hosted results at b7 were not available."
    },
    {
      "id": "RC-23",
      "category": "other",
      "severity": "low",
      "required_property": "The D-164 macOS timeout positive and mismatch controls must read workflow, ledger, and project-version inputs from the immutable candidate passed through --rev.",
      "disposition": "fixed",
      "rationale": "At d3811b8, the new controls parsed the current working tree while using the supplied revision only for the policy checker source. This let an old 40-minute candidate pass when the checkout contained the new 50-minute cap. The fix reads the candidate's workflow inventory and each required file with git ls-tree/git show, then applies the stale-ledger mutation only in a temporary fixture.",
      "fix_sha": "48d8e501872b9a19138a4653830a40b983199adc",
      "verification_ref": "At 48d8e501872b9a19138a4653830a40b983199adc: workflow-policy coverage self-test passes 528 controls; the same self-test with --rev c9a6320671b56d1092b2884aeac15d6a9320b60f rejects the 40-minute candidate; the direct workflow-policy check passes."
    },
    {
      "id": "RC-24",
      "category": "correctness",
      "severity": "high",
      "required_property": "The exact-source release CI reader can wait through the complete approved producer dependency path, with a reachable attempt/deadline budget, sufficient job cap and matching immutable ledger controls.",
      "disposition": "fixed",
      "rationale": "At 3c0489d7 the 3000-second release wait could expire before the 65-minute sanitizer or 70-minute Windows producer plus aggregator completed, with no guaranteed prerequisite head start. D-169 increased the reader budget; D-170 includes the five-minute changes job as well. Final source uses 160 attempts at 30 seconds and a 4800-second deadline, matching the complete 5+70+5-minute path. Its 142-minute cap admits the checked 8490-second worst case. All three preview readers use the same deadline and 90-minute caps, with historical citations preserved and changed-body disclosures. Superseded attempts, deadlines, caps and ledger rows have immutable source-bound negatives.",
      "fix_sha": "03fb184930754aa845308ea714869cc3c2deef0c",
      "verification_ref": "At 10fee4515c9db0e8b259e089ef2ec41f0453b811, this reviewer loaded candidate workflows and coverage source directly from Git objects: approved timeout/trigger positives, exact policy snapshot plus baseline AST, production fuzz-wait budget, and thirteen targeted stale-budget/trigger negatives passed. D-169's initial release correction is ancestor 3af81d66d1503f6ae4766d6a411f7604e5d4bd1d; D-170 completes the dependency window at the recorded fix SHA. Final local and hosted qualification remain separate gates."
    }
  ]
}
```
<!-- gbb-review-evidence:end -->
