# Phase 23 Adversarial Review

**Reviewed implementation:** 48d8e501872b9a19138a4653830a40b983199adc
**Role:** adversarial
**Reviewer:** adversarial-d155
**Review posture:** I re-reviewed the owner-approved D-164 macOS cap amendment at 48d8e501 against the exact two-slot candidate c9a6320671b56d1092b2884aeac15d6a9320b60f, current Plan 23-04, and the amended rescope, and rechecked prior findings. I verified the prior exact-head run and its macOS logs, the 50-minute YAML/ledger pair, and its positive and mismatch controls. I found and reported a source-binding defect in the first D-164 control implementation at d3811b8e; 48d8e501 fixes it by seeding the fixture from the resolved candidate commit. At 48d8e501 the exact-source coverage self-test passes 528 controls and the workflow-policy production check passes. The full local suite and a hosted attempt on 48d8e501 have not run yet.

## Result

ADV-01 through ADV-29 remain fixed at or before this commit. The D-164 change raises only native macOS from 40 to 50 minutes, pairs the YAML value with the timeout-ledger row, preserves its historical p50 citation, and records the measured incomplete run as non-sample evidence. It leaves other job caps and every per-test timeout unchanged. All 200 docs controls remain at two slots with their existing 90-second timeout and `v02` label; non-doc reservations remain at four slots. The 528-control self-test now reads the complete workflow inventory, ledger, and CMake version from the immutable `--rev`; it accepts the exact 50-minute pair and rejects a stale 40-minute ledger value. The exact-source policy check passes. ADV-30, the mutable-worktree source-binding defect found in the first D-164 control implementation, is fixed at 48d8e501. No correctness or security finding remains open. The prior hosted run on the two-slot candidate c9a63206 did not qualify because macOS hit its 40-minute cap; hosted qualification of the 50-minute amendment remains pending.

## D-155 path and selector attacks

The notice checker resolves each inline path and requires it to remain below the repository root; it also rejects empty, dot, parent, absolute, and backslash components. Fixture manifests and license files use the same root check. copy_inputs() validates source paths and target paths after resolving symlinks, including after creating parents, before copying bytes.

The earlier exact-source shard-0 CTest exercises a valid baseline, notice traversal, an in-root symlink to an external source, copy-source traversal, and a copy-target symlink; its controls require the path-confinement diagnostics and verify the outside destination remains absent. The exact-source shard-199 CTest also passed with positive and negative selected child checks. Direct probes at the preceding source accepted baseline and additional in-root inputs, rejected traversal and external symlinks with notice-path-outside-root, and rejected a target symlink with self-test-copy-path-outside-root without writing outside. The adoption checker blob is unchanged through the reviewed SHA.

The exact Plan 23-04 selector dry-run selected 218 tests, including all 200 docs-control shards through 199. The selector uses [0-9]+; CMake registers numbered shards 1–199 and the shard-0 test separately. The 90-second shard ceilings and complete inventory remain unchanged.

## D-156 recovery pin and D-068/D-069 budget mapping

The lifecycle checker pins RECOVERY_ADOPTION_PIN_SHA to 9166ab60d25c6d246761b4aa33a0ceb35dd83f5c and preserves comparisons against both that immutable pin and --rev. The adoption checker blobs at that pin and the reviewed implementation are byte-identical. Its post-tag recovery control passed at the preceding exact source with 99 controls and 12 positives; the lifecycle checker is unchanged here.

The docs-shard rows cite D-068, which exists and was unused in both the plan-pinned and PR bases. The exact plan-base and PR-base budget checks passed at 7c6; the allowlist and checker are unchanged here. D-069 remains the governing timeout policy.

## D-157 CI triggers, job caps, and scheduling

The CI workflow retains pull-request opened/synchronize/reopened triggers and filters branch pushes to main. Its policy checker requires that exact trigger map, and a paired mutation removes the main-only filter. At the reviewed source, the CI policy group passed 112 negative controls and one positive; the timeout-ledger group passed 20 negative controls and one positive. The new branch-filter mutation is registered in the policy-coverage manifest.

The measured job caps are raised only for native Linux (31 to 60 minutes), CMake floor (40 to 50), and native Windows (50 to 60). The three exact-head preview waiters use a 3,900-second deadline and 75-minute job cap. Historical p50 values and cited run IDs remain unchanged; the timeout-ledger rows disclose the changed job bodies and the incomplete PR #146 runs. No per-test timeout changed.

The configured CTest inventory reports PROCESSORS=4 for phase21_fixture_admission_controls, release_disclosure_controls, release_version_v04_controls, and support_claims_v04_controls. Their TIMEOUT values remain 60, 60, 90, and 60 seconds. The native CTest workflows set CTEST_PARALLEL_LEVEL=4, so these reservations hold the full worker pool for each measured slow control.

## D-157 workflow-policy coverage snapshot

At 01370352 the workflow-policy checker source had changed, but verify-workflow-policy-coverage.py still pinned the older checker blob. Its exact-source self-test rejected with “candidate workflow-policy source differs from the exact reviewed snapshot.” The reviewed follow-up pins the D-157 checker blob at 01370352, records only the functions changed by D-157 as historical AST exceptions, and continues comparing the rest against the immutable baseline. At b7d86939, the 136-control self-test passed, including all ten D-161 reservations and the seven wrong-label controls. At b677a36e, the 160-control self-test passed with the D-162 shard reservation and label negatives; the exact configured production check passed 540 controls across six groups and the local coverage CTest pair passed 2/2. At 61f08de3, the expanded self-test passes 526 controls, the production check passes 540/6, and the focused coverage CTest pair passes 2/2.

## D-157 Windows planning-label path comparison

The correction applies `_norm` to the renderer's `--repo` and `--output` values and to the review-evidence `--repo` value before comparing them with expected paths. `_same_file` checks the outer CMake executable and wrapped Python interpreter by file identity. The self-test rejects a renderer pointed at a different repository and a review command pointed at a different repository, while accepting exact commands.

On POSIX, `python3.14 -I tests/scripts/verify-planning-labels.py --self-test` passes all 33 controls. Its simulated-Windows branch case-varies the renderer output, renderer repository, and review-evidence repository paths; all three positive controls pass. The native Windows branch additionally case-varies the Python and CMake executable identities and the same three path arguments. The CMake-floor CI comment now describes a 50-minute floor, matching the configured cap. The full D-157 diff retains the measured timeout disclosures and exact-head waiter bounds, the main-only push filter, and four-slot reservations for the four slow controls without changing their per-test timeouts.

## D-158 sanitizer cap, ledger disclosure, and CTest reservation

The `linux-sanitizers-tests` job cap changes from 45 to 55 minutes. Its ledger row preserves the historical p50 of 21.55 minutes, cited run `40163270595`, and cited SHA; the new disclosure names exact-head run `42504839710`, the 1,843/1,853 result, and the cap change. `python3.14 -I .github/scripts/verify-workflow-policy.py --check --root . --git-root . --main-ref af5b719ed90b8e294ee9f00ae526ce605262c5de --disclosure-base b75ecb97d8ab11cda5dcb3cc94a87363e60f0cae` passes, confirming the changed job block has the required disclosure against the prior source. The cap remains inside the 3,900-second exact-head waiter.

The CMake registration preserves `v02_support_ledger_controls` at 120 seconds and adds `PROCESSORS 4`; it retains the `planning;v02` labels and build-directory environment, and remains in the expected inventory. The exact control passed locally in 27.52 seconds. The coverage checker now expects the exact labels and environment for native and sanitizer configurations. The exact configured inventory reports 120 seconds and four processors for this test, and 60/60/90/60 seconds and four processors for the four D-157 controls.

The 160-control self-test rejects the native support-ledger timeout of 119 seconds, the sanitizer-scaled timeout of 120 rather than 360 seconds, one three-slot mutation per D-157–D-162 reservation, and one wrong-label mutation per label-constrained reservation. The exact-source configured inventory passes 540 controls across six groups, and the local coverage CTest pair passes 2/2.

## D-160 additional CTest reservations

At the D-160 source, the nine reservations were docs shards 112, 115, 118, 119 and 122; `v02_fuzz_controls`; `v03_dispositions_controls`; `save_format_controls`; and `host_exit_crash_storm`. The CMake registrations changed only `PROCESSORS` properties and comments; test commands, assertions, expected inventory entries, and TIMEOUT values remained unchanged. Exact metadata then reported timeouts 90/180/60/60/60 seconds with four processors. Under the later D-163 amendment, those five docs shards now use two processors; the non-doc reservations remain four.

`host.cmake` leaves `host_signal_term`, `host_signal_int`, and `host_signal_inherited_ign` at two processors and adds a separate four-slot property only for `host_exit_crash_storm`. The coverage checker lists the nine tests, and the D-160 118-control self-test applies an isolated PROCESSORS=3 mutation to each reservation. Its Windows path removes POSIX-only `host_exit_crash_storm` and `save_format_controls` from the accepted inventory; it rejects a missing cross-platform reservation and an unexpected POSIX-only registration. The exact POSIX configured inventory check reports 540 controls across six groups, and both coverage CTests pass. Windows behavior is exercised by the checker self-test, not by a hosted Windows run in this review.

## D-161 ten CTest reservations

The ten controls were `fixture_product_core_controls`, `fixture_product_player_controls`, `fixture_admission_controls`, `v02_consumer_controls_c`, `v02_consumer_controls_cpp`, `acceptance_dense_input_controls`, `workflow_policy_group_ci`, `workflow_policy_group_rehearsal`, and docs shards 108 and 114. At the D-161 source, exact CTest JSON reported four processors for every registration. Under the later D-163 amendment, docs shards 108 and 114 use two; the other eight D-161 controls remain at four. The fixture controls retain 120/120/90-second timeouts; the two consumer controls and dense-input control retain 600-second timeouts (with existing `COST=600` on those three); policy groups retain 180 seconds; docs shards retain 90 seconds. Existing `v02` labels and `GBB_TEST_BUILD_DIR` environments remain on fixture, consumer, and docs controls. The dense-input working directory and lack of label/environment, and the policy groups' existing working directories and completion-file arguments, remain unchanged.

The D-161 CMake delta from 4343d95d was empty, so it changed no commands, expected output patterns, assertions, timeouts, labels, environments, or inventory entries. The new checker requires exact `LABELS=[\"v02\"]` for the seven reserved fixture, consumer, and docs controls; the two policy groups, acceptance dense-input test, and other reservations have no new label requirement. Its self-test creates each label fixture with `v02`, then applies one `LABELS=[\"unexpected\"]` negative per named test. At b7d86939 the self-test passed 136 controls, including all seven D-161 wrong-label negatives.

At b7d86939 the self-test passed 136 controls, including Windows environment-path variants; its local workflow-policy coverage CTest pair passed 2/2 and production check passed 540 controls across six groups. At b677a36e, the self-test passed 160 controls and the local coverage CTest pair passed 2/2. At 61f08de3, the self-test passes 526 controls and the local coverage CTest pair passes 2/2. The full 1,942-test local suite passed at preceding source 3c908d7f and was not rerun at either source.

## Windows support-ledger environment path comparison

The checker now compares `GBB_TEST_BUILD_DIR` with Windows path normalization (`ntpath.normpath` and `normcase`) after slash conversion, while retaining exact checks for environment variable names and other values. Its simulated-Windows positive control accepts an uppercase path using backslashes; the paired wrong-directory negative rejects. At b7d86939 the exact self-test passed 136 controls and the local coverage CTest pair passed 2/2. The b7 checker delta changed no CMake registration, timeout, or CI budget; b677 adds only the D-162 shard scheduling list and checker controls. At b677, the exact self-test passed 160 controls and the local coverage CTest pair passed 2/2. At 61f08de3, the 526-control self-test and focused coverage CTest pair pass; the Windows case/slash positive and wrong-directory negative remain included.

The hosted run at 6ae7a467 was not green: Linux native passed; Windows failed `workflow_policy_coverage` on the support-ledger `ENVIRONMENT` path comparison; native macOS was canceled at the 40-minute cap after 1,927/1,942 tests; and CMake-floor was canceled at the 50-minute cap after about 1,920/1,942 tests. These outcomes are for 6ae7a467, not passing evidence for b7d86939, b677a36e, c09e06e9, or 61f08de3; no exact 61f08de3 hosted success is established.

## D-162 twelve docs-shard reservations

At b677, D-162 added shards 05, 07, 89, 154, 155, 160, 181, 182, 191, 192, 198, and 199 to the four-slot set. Its exact configured CTest inventory reported each once with `PROCESSORS=4`, `TIMEOUT=90`, `LABELS=["v02"]`, and its existing build-directory environment. That CMake change appended those names to the measured slow-shard list without changing commands, assertions, timeout, label, or environment. D-163 supersedes that subset with all 200 docs controls.

The checker adds all twelve names to both `PHASE23_RESERVED_TESTS` and `EXPECTED_RESERVED_LABELS`. Its per-reservation loop lowers each to three processors and rejects, and its per-label loop changes each label to `unexpected` and rejects. At b677, the exact-source self-test passed 160 controls, including twelve reservation and twelve wrong-label negatives; the production check passed 540 controls across six groups and the local exact coverage CTest pair passed 2/2. These twelve checks remain included in the 526-control self-test at 61.

## D-163 original all-200 four-slot reservation at 61

At source 61, the configured CTest inventory contained the base docs control (`v02_adoption_docs_controls`, shard 0) and numbered shards 1–199 exactly once. Each had `TIMEOUT=90`, `PROCESSORS=4`, `LABELS=["v02"]`, the existing `GBB_TEST_BUILD_DIR` environment, and its matching `--self-test docs --shard N 200` command. `tests/expected-tests.txt` contained each name exactly once. That CMake change added four-slot reservations for every numbered shard and shard 0 while leaving the existing `gbb_add_v02_contract` invocations and 90-second ceilings unchanged.

The checker derived the same 200 names, added them to `PHASE23_RESERVED_TESTS` and `EXPECTED_RESERVED_LABELS`, and required each registration exactly once, four processors, and the exact `v02` label. At 61, the 526-control self-test passed with one three-slot and one wrong-label negative per docs control; the configured check passed 540 controls across six groups and the focused coverage CTest pair passed 2/2. The simulated-Windows support-ledger path controls accepted the slash/case variant and rejected a wrong directory. This is the historical four-slot configuration superseded by the two-slot amendment below.

At source 61, D-163 replaced the changing slow-shard subset from D-159–D-162 with reservations for the complete docs-control set; non-doc reservations remained. Under the four-worker CTest budget, each four-slot docs test ran serially. The hosted attempt at evidence-only candidate `343606f0cb105c837e928dc58d2ecea8b37e9670` used the same implementation: Linux passed 1,942/1,942; macOS canceled at its 40-minute cap after 1,895/1,942; CMake-floor at 50 minutes after 1,839/1,942; sanitizer inventory at 55 minutes after 1,785/1,853; and Windows at 60 minutes after 1,746/1,804. Fixture reproduction passed, while preview package smoke failed because the required CI run did not complete successfully. The exact-head attempt was not merge-eligible. The canceled logs show docs shards passing in sequence. A separate local probe ran two docs shards concurrently in 9.5 seconds. These observations led to the owner-approved two-slot amendment; they are not qualification for the current source.

### Owner-approved amendment: two slots per docs control

The amended D-163 rescope requires exactly two CTest slots for all 200 docs controls, including shard 0, while preserving the global four-worker setting. At exact source bc, the configured inventory confirms each entry once with `PROCESSORS=2`, `TIMEOUT=90`, the existing `v02` label, build-directory environment, and unchanged shard command. `tests/expected-tests.txt` contains the complete 200-entry set exactly once. The CMake diff from 61 changes only `PROCESSORS 4` to `PROCESSORS 2` for the base control and numbered shards, plus explanatory comments.

The coverage checker sets the expected processor count to two for `DOC_CONTROL_TESTS` and four for every non-doc reservation. For each docs entry, its self-test changes the expected two slots back to four and requires rejection, then separately changes the label to `unexpected` and requires rejection. Its 526-control run passed; the exact configured inventory check passed 540 controls across six groups; the focused coverage CTest pair passed 2/2. A metadata audit confirmed all 200 docs entries have exactly two processors and all non-doc reserved controls remain at four. The Windows support-ledger slash/case positive and wrong-directory negative remain included and pass.

No command, assertion, existing label/environment, per-test timeout, CI job cap, or non-doc reservation changed. With four CTest workers, two docs shards can run concurrently; this review did not rerun the complete docs selection, full local suite, or hosted qualification on the two-slot source.



## D-164 native macOS timeout amendment

GitHub run `42679813590` is bound to candidate `c9a6320671b56d1092b2884aeac15d6a9320b60f` and PR #146. Its native macOS arm64 job was cancelled at the existing 40-minute cap. The job log shows 1,928/1,942 tests complete, with `workflow_policy_group_ci` the next test; all 200 docs-control tests passed and there is no failed CTest assertion before cancellation. The run supports adding completion headroom and is not treated as a timing sample.

At implementation source `48d8e501872b9a19138a4653830a40b983199adc`, `native-macos` alone is set to 50 minutes and its `ci.yml:native-macos` ledger row matches. The row retains the historical p50 `17.80`, cited run `40156247875`, and sample count 5; its disclosure identifies the runner migration and incomplete Phase 23 run. The D-164 diff does not change any other workflow cap, per-test timeout, CTest reservation, command, assertion, or label.

The first D-164 self-test implementation at `d3811b8e` read `ci.yml`, the ledger, and `CMakeLists.txt` from the mutable checkout, so dirty files could mask a mismatch with `--rev`. At `48d8e501`, the control enumerates `.github/workflows/*.yml` from the resolved candidate's Git tree and reads each workflow, `.github/ci-timeouts.json`, and `CMakeLists.txt` with `git show` at that commit. It accepts the candidate's 50-minute workflow/ledger pair and rejects a 40-minute ledger row with `timeout-ledger-stale`. The exact-source self-test passes 528 controls, and `python3 -I .github/scripts/verify-workflow-policy.py --check --root .` passes. No local full-suite or new hosted result exists for this implementation SHA yet.

## Required adversarial checklist

| Attack | Exact-source result |
|---|---|
| Omit or swap candidate-specific reasons; claim a candidate was built/run, admitted, or supplied game evidence | Rejected by the v0.4 support-claims and release-note controls with candidate-specific diagnostics; accepted renderer/profile baselines are paired with each mutation. |
| Present metadata as executed diagnostics | Rejected as `release-notes-metadata-as-diagnostic`; the 513 named entries remain metadata and the baseline keeps seven unresolved gates and zero executed/admitted real fixtures. |
| Omit or contradict Pending statuses | Promoted rows and contradictory completion prose are rejected; the valid Pending wording passes. |
| Hide or contradict disclosures | Comment-only, inline/fenced code, nested container code, and hidden raw-HTML cases reject; visible renderer-built clauses pass. Rights-scope outcomes cannot be restated as license prohibitions. |
| Use stale profile, source, version, review, or rehearsal facts | The immutable v0.4 profile self-test and version-window/version-v0.4 controls reject stale or mismatched inputs; exact-source accepted counterparts pass. |
| Rewrite historical ledger bytes or alter its reviewed window | The disclosure self-test binds tagged ledger bytes to their tag/generator output; version-window controls reject a historical ledger mutation after review. |
| Promote signing, notarization, publication, or platform support | The release-note controls reject each false promotion with its specific claim diagnostic while accepting the explicit unsigned, unpublished, and scoped-platform limits. |
| Reopen every D-144–D-154 case | The exact-source release-note controls and the existing source-bound docs controls retain the paired parser, invisible-character/reference, hard-break, emphasis/link-label, delimiter-complexity, Unicode P/S, and bounded-label cases. Their matcher code is unchanged by D-155. |
| Escape notice input or self-test copy roots; omit higher-numbered focused shards | Current traversal/symlink controls reject the path escapes; the corrected CTest selector and inventory include every numbered shard through 199. |
| D-157 CI trigger, timeout ledger, four-slot scheduling, Windows path, and coverage snapshot | CI and ledger controls pass their paired mutation sets; CTest assigns all four measured controls four slots without changing their timeouts; the coverage snapshot correction passes. The 33-control planning-label self-test accepts normalized case variants and rejects wrong repository paths. |
| D-158 sanitizer cap/disclosure and support-ledger CTest reservation | The 55-minute cap and disclosure pass the explicit b75 comparison. The support-ledger test passes at 120 seconds with four slots, and its environment/labels match the contract. The coverage self-test rejects native/scaled timeout and slot mutations; the configured-inventory CTest passes. |
| D-159 docs-shard and preview-package slot reservations | At the D-159 source, `phase23_docs_controls_shard_183` had a 90-second limit and four processors, while `preview_package_smoke` had 180 seconds and four processors; both passed their exact-source focused CTest run. The shard now has two processors under D-163, while preview smoke retains four. The 526-control self-test retains the reservation checks. |
| D-160 nine CTest reservations | At the D-160 source, the five docs shards used four processors with 90-second limits; v0.2 fuzz, v0.3 dispositions, save-format, and host crash-storm also used four with their existing limits. The D-160 three-slot negatives and Windows POSIX-only inventory controls passed in the 118-control self-test. D-163 changes the docs shards to two slots; the non-doc reservations remain four and the three sibling host signal tests remain at two. |
| D-161 ten reservations and exact labels | At the D-161 source all ten reservations used four slots and the seven designated `v02` labels. The 136-control self-test at b7 passed one wrong-label mutant per designated control; later 160- and 526-control self-tests retain those negatives and the Windows support-ledger path pair. D-163 moves the two docs entries to two slots; the other eight remain four. The exact bc coverage CTest pair passes. |
| D-162 twelve docs shards | At b677, all twelve shards had exact `v02` labels, 90-second timeouts, and four-slot reservations, with one three-slot and one wrong-label negative per shard. The 526-control self-test at 61 retains those checks; bc now requires two slots and rejects four for every docs shard. |
| D-163 all 200 docs controls | At 61, all 200 entries were four-slot; the owner-approved bc amendment requires two slots per entry. Exact bc inventory and `expected-tests.txt` contain every entry exactly once with 90-second timeout and `v02` label. The 526-control self-test rejects one former-four-slot and one wrong-label mutation per entry; non-doc reservations remain four-slot. |

For each direct release-note mutation, the test helper first accepts the valid renderer-built baseline, then requires the mutant to fail for its expected reason. The immutable profile, version-window, disclosure, and review-evidence suites also pair accepted records with targeted rejected mutations. No real game or diagnostic fixture was fetched, built, run, or admitted; no release was signed, published, or promoted. REL-01 remains Pending.

## Verification evidence

At exact implementation source 48d8e501, the workflow-policy coverage self-test passes 528 controls and the workflow-policy production check passes. D-164's positive control reads workflow files, ledger, and CMakeLists.txt from that immutable candidate; its negative requires `timeout-ledger-stale` for a 40-minute macOS ledger row. GitHub run 42679813590 is bound to c9a63206, not 48d8e501. Its macOS arm64 job stopped at the old 40-minute cap after 1,928/1,942 tests; all 200 docs controls passed, and no assertion failure appears before cancellation. It does not qualify the new 50-minute cap.

Evidence boundary: at source 61, the 526-control self-test, 540-control production check, and focused coverage CTest pair validated the original four-slot D-163 setting. At exact source bc, I freshly configured CTest and reran those bounded checks; its 526-control self-test now rejects the former four-slot setting per docs entry. I did not run the full docs selection, complete local suite, or hosted qualification at bc.

- At b677, the exact-source workflow-policy coverage self-test passed 160 controls, including one three-slot negative per prior reserved test, seven D-161 wrong-label negatives, twelve D-162 wrong-label negatives, and the Windows environment path controls.
- At 61, the exact-source self-test passed 526 controls with one three-slot and one wrong-label negative for each of the 200 four-slot docs reservations.
- At bc282cc229c887d7034e533175249861db846154, the exact-source self-test passes 526 controls, including one former-four-slot and one wrong-label negative for each docs control, plus the Windows path variants.
- At bc, the exact configured production check passes 540 controls across six groups and the focused workflow-policy coverage CTest pair passes 2/2.
- Exact bc CTest JSON and `tests/expected-tests.txt` contain all 200 docs controls exactly once; each retains its expected command, `TIMEOUT=90`, `PROCESSORS=2`, `LABELS=["v02"]`, and build-directory environment. All non-doc reserved tests retain four processors.
- Exact-source workflow-policy production check passes 540 controls across six groups; the local exact coverage CTest pair passes 2/2.
- Exact-source workflow-policy CI group: 112 negative controls and 1 positive pass, including the unfiltered-push mutation.
- Exact-source timeout-ledger group: 20 negative controls and 1 positive pass, including stale timeout, p50-ratio, and whole-run ceiling controls.
- Exact-source POSIX planning-label self-test: 33 controls pass, including simulated Windows case variants for renderer `--repo`, renderer `--output`, and review-evidence `--repo`; wrong-repository negative controls reject.
- Exact-source CI comment says the CMake floor suite's 20–40 minute observed duration is measured against its 50-minute cap. Review of the full D-157 diff confirms only the three measured CI job caps and three exact-head waiters were extended, all four slow controls reserve four slots, and per-test timeouts remain 60/60/90/60 seconds.
- Exact configured CTest metadata: all four D-157 controls reserve four slots; their existing TIMEOUT values remain 60/60/90/60 seconds.
- Exact-source ledger group passes 20 negative controls and 1 positive; helper group passes 66 negative and 19 positive controls, including changed-body disclosure refused/accepted cases. The D-158 disclosure comparison against b75 passes.
- The local exact workflow-policy coverage CTest pair passes 2/2. The full local CTest suite passed 1,942/1,942 at exact candidate 9f38c43e with the four-slot implementation unchanged from 61; it was not rerun at the two-slot source bc. The D-158 support-ledger test passed in a preceding exact-source selection.
- Exact-source D-159 focused CTest selection at c08d18ef passed `phase23_docs_controls_shard_183` and `preview_package_smoke` (2/2, 87.57 seconds total); configured metadata then showed 90/180-second limits and four processors for both. D-163 now sets the docs shard to two processors; preview smoke remains four.
- D-160 metadata at its reviewed source confirmed the nine tests had four processors with unchanged timeouts: docs shards 112/115/118/119/122 at 90 seconds; `v02_fuzz_controls` at 180; `v03_dispositions_controls` and `save_format_controls` at 60; `host_exit_crash_storm` at 60. D-163 now sets the docs shards to two; the non-doc reservations remain four. The three sibling signal tests remain at 60 seconds and two processors.
- Exact bc CTest metadata confirms all 200 docs controls use two slots and retain 90-second timeouts; all non-doc reserved controls keep their four-slot reservations. `host_exit_crash_storm` remains separately reserved while its three sibling signal tests remain at two processors.
- Earlier D-155 shard 0 and shard 199 runs, exact selector dry-run, D-156 recovery run, D-068 plan/PR base budget checks, and D-069 self-test remain applicable because their implementation/checker/allowlist inputs did not change from 7c6 to the reviewed SHA.
- Earlier exact-source release/profile/version/disclosure/evidence controls remain applicable: the matcher, support-ledger, version-window, review-evidence, CTest registration, and inventory sources are unchanged from their cited reviewed revisions.

These checks establish the exact-source timeout-ledger control and workflow-policy check for 48d8e501, plus the previously reviewed path-confinement and release controls. They do not establish full local-suite or hosted cross-platform success for the 50-minute source; exact-head qualification remains pending.

## Findings and dispositions

ADV-01 through ADV-29 remain fixed at or before the reviewed commit. ADV-29 was open at fdccc15a after the duplicate-fixture self-test failure and is fixed at 4343d95d. ADV-30 was open at d3811b8e because the new timeout self-test read live checkout configuration instead of its immutable revision; 48d8e501 fixes it. D-163 and D-164 have no open correctness or security finding at this source.

<!-- gbb-review-evidence:start -->
```json
{
  "schema_version": 1,
  "report_id": "gbb-phase23-adversarial-48d8e501872b9a19138a4653830a40b983199adc-20261109-d164-macos-cap",
  "role": "adversarial",
  "reviewer_id": "adversarial-d155",
  "independent": true,
  "reviewed_sha": "48d8e501872b9a19138a4653830a40b983199adc",
  "findings": [
    {
      "id": "ADV-01",
      "category": "correctness",
      "severity": "high",
      "required_property": "Only visible Markdown prose may satisfy required release-note disclosures.",
      "disposition": "fixed",
      "rationale": "The exact-source renderer-built release-note baseline passes. The current controls reject disclosures hidden in inline and block code, comments, and container code; removing a required visible clause fails with its specific diagnostic.",
      "fix_sha": "9e09eef8b379ca8d329cb13bf354058661296daa",
      "verification_ref": "At b677 (historical evidence; D-163 changes only docs CTest scheduling and its coverage checker, leaving this finding\u2019s behavior controls unchanged): verify-v02-adoption.py --self-test-release-notes-v04: positives=2 controls=72; verify-version-window.py --self-test-version-v04: positives=63 controls=66."
    },
    {
      "id": "ADV-02",
      "category": "correctness",
      "severity": "high",
      "required_property": "Release notes must not claim a requirement is complete while its required status remains Pending.",
      "disposition": "fixed",
      "rationale": "The exact-source release-note controls reject both a promoted Pending row and contradictory completion prose; the valid Pending baseline passes before each mutation.",
      "fix_sha": "9e09eef8b379ca8d329cb13bf354058661296daa",
      "verification_ref": "At b677 (historical evidence; D-163 changes only docs CTest scheduling and its coverage checker, leaving this finding\u2019s behavior controls unchanged): verify-v02-adoption.py --self-test-release-notes-v04: positives=2 controls=72; verify-support-ledger.py --self-test-disclosure: positives=4 controls=20."
    },
    {
      "id": "ADV-03",
      "category": "correctness",
      "severity": "high",
      "required_property": "Metadata-only diagnostic inventories must not be presented as executed or passing diagnostics.",
      "disposition": "fixed",
      "rationale": "The exact-source release-note controls reject the claim that all 513 named diagnostic microtests executed and passed, while accepting the metadata-only baseline with seven unresolved gates and zero real fixtures executed or admitted.",
      "fix_sha": "9e09eef8b379ca8d329cb13bf354058661296daa",
      "verification_ref": "At b677 (historical evidence; D-163 changes only docs CTest scheduling and its coverage checker, leaving this finding\u2019s behavior controls unchanged): verify-v02-adoption.py --self-test-release-notes-v04: positives=2 controls=72; the named metadata-as-diagnostic mutant checks its specific diagnostic."
    },
    {
      "id": "ADV-04",
      "category": "correctness",
      "severity": "high",
      "required_property": "A rights-scope no-go must not be represented as a legal license prohibition without evidence.",
      "disposition": "fixed",
      "rationale": "The exact-source notes controls reject an unsupported claim that both candidates' licenses prohibit repository and public-CI use; the source/rights-scope baseline remains accepted.",
      "fix_sha": "9e09eef8b379ca8d329cb13bf354058661296daa",
      "verification_ref": "At b677 (historical evidence; D-163 changes only docs CTest scheduling and its coverage checker, leaving this finding\u2019s behavior controls unchanged): verify-v02-adoption.py --self-test-release-notes-v04: positives=2 controls=72; rights-scope-presented-as-license-prohibition mutant."
    },
    {
      "id": "ADV-05",
      "category": "correctness",
      "severity": "high",
      "required_property": "Inline code, image destinations, and hidden markup cannot satisfy visible-prose or ledger-link requirements.",
      "disposition": "fixed",
      "rationale": "Visible prose and a real ledger link pass. Code-only disclosure evidence, image-ledger destinations, and hidden titles/alt text fail the required visibility or ledger checks.",
      "fix_sha": "9e09eef8b379ca8d329cb13bf354058661296daa",
      "verification_ref": "At b677 (historical evidence; D-163 changes only docs CTest scheduling and its coverage checker, leaving this finding\u2019s behavior controls unchanged): verify-v02-adoption.py --self-test-release-notes-v04 and verify-version-window.py --self-test-version-v04 pass their paired visibility controls."
    },
    {
      "id": "ADV-06",
      "category": "correctness",
      "severity": "high",
      "required_property": "A required support-ledger link must target the ledger itself, not contain its path in unrelated URL text or a title.",
      "disposition": "fixed",
      "rationale": "Relative and canonical ledger links are accepted; external-query, title-only, image, and malformed destinations reject for ledger mismatch or malformed-link reasons.",
      "fix_sha": "9a193975fb32ae69bd09be2cf847e3271d078733",
      "verification_ref": "At b677 (historical evidence; D-163 changes only docs CTest scheduling and its coverage checker, leaving this finding\u2019s behavior controls unchanged): verify-v02-adoption.py --self-test-release-notes-v04 and verify-version-window.py --self-test-version-v04 passed."
    },
    {
      "id": "ADV-07",
      "category": "correctness",
      "severity": "high",
      "required_property": "Text hidden by closed or unterminated HTML comments cannot satisfy release-note or changelog requirements.",
      "disposition": "fixed",
      "rationale": "Closed- and open-comment mutants cannot satisfy candidate or required-clause checks; a hidden changelog ledger link fails the version-output check. Visible counterparts pass.",
      "fix_sha": "9a193975fb32ae69bd09be2cf847e3271d078733",
      "verification_ref": "At b677 (historical evidence; D-163 changes only docs CTest scheduling and its coverage checker, leaving this finding\u2019s behavior controls unchanged): verify-v02-adoption.py --self-test-release-notes-v04: positives=2 controls=72; verify-version-window.py --self-test: positives=11 controls=64."
    },
    {
      "id": "ADV-08",
      "category": "correctness",
      "severity": "high",
      "required_property": "Fenced and indented code inside list and blockquote containers cannot satisfy disclosure or changelog visibility requirements.",
      "disposition": "fixed",
      "rationale": "The current controls cover same-line and nested list/blockquote fences plus indented code. Hidden disclosures and links reject; visible disclosures and genuine code masking remain accepted.",
      "fix_sha": "46f5ce4a515daa65bb9850a28a1ee4be9b9b8c5a",
      "verification_ref": "At b677 (historical evidence; D-163 changes only docs CTest scheduling and its coverage checker, leaving this finding\u2019s behavior controls unchanged): verify-v02-adoption.py --self-test-release-notes-v04 and verify-version-window.py --self-test-version-v04 passed."
    },
    {
      "id": "ADV-09",
      "category": "correctness",
      "severity": "high",
      "required_property": "Incomplete raw-HTML block openers cannot hide required changelog links or release-note disclosures.",
      "disposition": "fixed",
      "rationale": "Script, pre, style, doctype, and XML processing-instruction openers fail at the required paths while comments, code, and escaped examples remain valid when visible evidence is present. The legacy-matcher controls establish causality.",
      "fix_sha": "a63f1dc67654613e105ac1071b7445f21adea0bc",
      "verification_ref": "At b677 (historical evidence; D-163 changes only docs CTest scheduling and its coverage checker, leaving this finding\u2019s behavior controls unchanged): verify-version-window.py --self-test-version-v04: positives=63 controls=66; verify-v02-adoption.py --self-test-release-notes-v04: positives=2 controls=72."
    },
    {
      "id": "ADV-10",
      "category": "correctness",
      "severity": "high",
      "required_property": "Markdown visibility and claim matching must follow the paired D-144 parser cases for labels, continuations, comments, fences, and autolinks.",
      "disposition": "fixed",
      "rationale": "The source-bound controls reject whitespace-only image labels, invalid tab-expanded continuations, mismatched reference-label comment payloads, false comment-created fences, and a title-only hardware disclosure around an autolink. Valid collapsed labels, matching comments, correct continuations, genuine fences, and valid titles remain accepted.",
      "fix_sha": "3d27596b341877d9a19cb82409e178f9eae0d1e9",
      "verification_ref": "D-144 source-bound docs controls at 4c9c54f8b5a33e758624c997f107d1ffdd7c94a0 passed 473 checks/255 rejected controls; reviewed-source diff leaves the parser unchanged; current release-note controls pass 2/72."
    },
    {
      "id": "ADV-11",
      "category": "correctness",
      "severity": "high",
      "required_property": "Unicode Cf characters cannot split a visible unsupported CGB-game claim.",
      "disposition": "fixed",
      "rationale": "The claim-only matcher removes Cf characters, rejecting U+200B, U+2060, and U+200C claims while leaving unrelated disclosures and safe prose unchanged.",
      "fix_sha": "742bf1bb5dd3a6e71ab93dbdb420bca2ec94d16a",
      "verification_ref": "At b677 (historical evidence; D-163 changes only docs CTest scheduling and its coverage checker, leaving this finding\u2019s behavior controls unchanged): verify-v02-adoption.py --self-test-release-notes-v04: positives=2 controls=72; exact-source docs shards 0/200 and 199/200 pass; matcher unchanged by D-155."
    },
    {
      "id": "ADV-12",
      "category": "correctness",
      "severity": "high",
      "required_property": "Unicode 18.0 Default_Ignorable_Code_Point characters, including non-Cf characters, cannot split a visible unsupported CGB-game claim.",
      "disposition": "fixed",
      "rationale": "The matcher includes the frozen Unicode 18.0 default-ignorable ranges; current paired controls cover U+034F and representative non-Cf ranges with safe-text counterparts.",
      "fix_sha": "a6bc0a824bce55de57422e2b6b73b94ed0f841d1",
      "verification_ref": "At b677 (historical evidence; D-163 changes only docs CTest scheduling and its coverage checker, leaving this finding\u2019s behavior controls unchanged): verify-v02-adoption.py --self-test-release-notes-v04: positives=2 controls=72; docs matcher is unchanged by D-155."
    },
    {
      "id": "ADV-13",
      "category": "correctness",
      "severity": "high",
      "required_property": "Valid CommonMark references to invisible characters cannot split an unsupported CGB-game claim after rendering.",
      "disposition": "fixed",
      "rationale": "Hexadecimal, decimal, and named references to invisible/default-ignorable characters are decoded for the claim matcher; code spans remain masked and visible safe-reference prose remains accepted.",
      "fix_sha": "fc0ba4ff9626e06e04d8800800561b51414166bf",
      "verification_ref": "At b677 (historical evidence; D-163 changes only docs CTest scheduling and its coverage checker, leaving this finding\u2019s behavior controls unchanged): verify-v02-adoption.py --self-test-release-notes-v04: positives=2 controls=72; parser/matcher code unchanged by D-155."
    },
    {
      "id": "ADV-14",
      "category": "correctness",
      "severity": "high",
      "required_property": "All valid CommonMark character references in visible prose are normalized before unsupported-game matching.",
      "disposition": "fixed",
      "rationale": "The claim matcher decodes valid visible references to spaces and CGB letters as well as invisible separators. Safe visible references and masked code spans retain their intended behavior.",
      "fix_sha": "fc0ba4ff9626e06e04d8800800561b51414166bf",
      "verification_ref": "At b677 (historical evidence; D-163 changes only docs CTest scheduling and its coverage checker, leaving this finding\u2019s behavior controls unchanged): verify-v02-adoption.py --self-test-release-notes-v04: positives=2 controls=72; exact-source claim/profile controls pass 22 positives/21 controls."
    },
    {
      "id": "ADV-15",
      "category": "correctness",
      "severity": "high",
      "required_property": "CommonMark hard line breaks and encoded spaces are joined for unsupported-game matching in docs, release notes, and notices after code masking.",
      "disposition": "fixed",
      "rationale": "LF, CR, CRLF, encoded-space, soft-break, safe-prose, and code controls remain paired; the notices caller supplies uncollapsed visible prose to the shared matcher.",
      "fix_sha": "e26757fafc818a92ddf7ca45f1a409658a5a5bdd",
      "verification_ref": "At b677 (historical evidence; D-163 changes only docs CTest scheduling and its coverage checker, leaving this finding\u2019s behavior controls unchanged): release-note controls pass 2/72; docs shard 0/200 passes notice-path child controls; notice caller and matcher are unchanged except D-155 path checks."
    },
    {
      "id": "ADV-16",
      "category": "correctness",
      "severity": "high",
      "required_property": "Visible CGB claim text split by CommonMark emphasis or inline-link labels cannot evade unsupported-game matching.",
      "disposition": "fixed",
      "rationale": "Strong, intraword-star, underscore-emphasis, and inline-link-label claims are rejected. Intraword underscores, escaped punctuation, code, and destination/title-only claims remain accepted.",
      "fix_sha": "e017078b72e78b38fb596faced3af3e35c2ca0ce",
      "verification_ref": "At b677 (historical evidence; D-163 changes only docs CTest scheduling and its coverage checker, leaving this finding\u2019s behavior controls unchanged): verify-v02-adoption.py --self-test-release-notes-v04: positives=2 controls=72; matcher code unchanged by D-155."
    },
    {
      "id": "ADV-17",
      "category": "correctness",
      "severity": "high",
      "required_property": "Visible shortcut, full, and collapsed reference-link labels participate in unsupported-game matching while destinations and titles do not.",
      "disposition": "fixed",
      "rationale": "The matcher resolves each valid reference-label form and excludes its destination/title; unresolved and escaped labels, code, and destination-only claims remain accepted counterparts. Notice uses the same claim matcher.",
      "fix_sha": "b798781105b8f6f803e85aa2ad766d2b2fdbec22",
      "verification_ref": "At b677 (historical evidence; D-163 changes only docs CTest scheduling and its coverage checker, leaving this finding\u2019s behavior controls unchanged): release-note controls pass 2/72; docs shards 0/200 and 199/200 pass; parser/matcher diff is empty for D-155."
    },
    {
      "id": "ADV-18",
      "category": "security",
      "severity": "high",
      "required_property": "Delimiter matching must not rescan all prior unmatched runs for each closer in bounded public Markdown input.",
      "disposition": "fixed",
      "rationale": "The matcher uses fixed per-marker candidate buckets and exhausts candidates rather than scanning all prior delimiter runs; dense unmatched-marker controls assert claim detection without timing thresholds.",
      "fix_sha": "6876fab06bf746fdaab67beaa4d52a6b1c70ac06",
      "verification_ref": "At b677 (historical evidence; D-163 changes only docs CTest scheduling and its coverage checker, leaving this finding\u2019s behavior controls unchanged): release-note controls pass 2/72; source inspection confirms the candidate-stack implementation is unchanged by D-155."
    },
    {
      "id": "ADV-19",
      "category": "correctness",
      "severity": "high",
      "required_property": "CommonMark emphasis flanking treats Unicode punctuation and symbol categories P and S as punctuation for unsupported-game matching.",
      "disposition": "fixed",
      "rationale": "The exact-source matcher uses Unicode P/S categories. The paired Unicode-symbol claim and safe-prose controls are retained; current release-note controls pass.",
      "fix_sha": "4c9c54f8b5a33e758624c997f107d1ffdd7c94a0",
      "verification_ref": "At b677 (historical evidence; D-163 changes only docs CTest scheduling and its coverage checker, leaving this finding\u2019s behavior controls unchanged): release-note controls pass 2/72; historical exact-source D-153 probes rejected both claims on four production paths and accepted paired safe/code controls; matcher is unchanged by D-155."
    },
    {
      "id": "ADV-20",
      "category": "security",
      "severity": "high",
      "required_property": "Impossible nested or over-999-character reference-label candidates are rejected before copying or normalization.",
      "disposition": "fixed",
      "rationale": "A bracket stack and prefix count check nested/overlong spans before slicing or normalization; only valid labels at or below CommonMark's 999-character limit are normalized. Dense-bracket controls retain safe prose counterparts.",
      "fix_sha": "4c9c54f8b5a33e758624c997f107d1ffdd7c94a0",
      "verification_ref": "At b677 (historical evidence; D-163 changes only docs CTest scheduling and its coverage checker, leaving this finding\u2019s behavior controls unchanged): release-note controls pass 2/72; historical exact-source D-154 probes reject the 512-level attack on four production paths and accept safe counterparts; source is unchanged by D-155."
    },
    {
      "id": "ADV-21",
      "category": "security",
      "severity": "high",
      "required_property": "Notice inputs and self-test copy destinations must resolve inside their respective roots, including when paths traverse or follow symlinks.",
      "disposition": "fixed",
      "rationale": "The old inline notice path could read outside the checkout and be reused as a copy destination. The reviewed code rejects traversal components, resolves source symlinks and enforces repository containment, and re-resolves copy destinations after parent creation. Current minimal-tree probes accept baseline/in-root paths, reject traversal and external symlink inputs as notice-path-outside-root, and reject a target symlink as self-test-copy-path-outside-root with zero external writes. The exact-source docs shard runs its matching traversal, symlink, and copy controls.",
      "fix_sha": "9166ab60d25c6d246761b4aa33a0ceb35dd83f5c",
      "verification_ref": "At b677 (historical evidence; D-163 changes only docs CTest scheduling and its coverage checker, leaving this finding\u2019s behavior controls unchanged): docs shard 0/200 passed; direct check_notices baseline=112 and safe in-root=113, traversal/symlink rejected; direct copy_inputs normal copy passed and destination symlink rejected with external_files=0."
    },
    {
      "id": "ADV-22",
      "category": "other",
      "severity": "medium",
      "required_property": "The focused Plan 23-04 CTest selector must include every registered numbered docs shard, including 100\u2013199.",
      "disposition": "fixed",
      "rationale": "The former two-digit selector omitted the high-numbered shards. The corrected `[0-9]+` selector matched all 199 numbered tests in an isolated CTest run, including 100 and 199; shard 199/200 itself passed. CMake registration, expected inventory, and timeout allowlist contain each numbered shard once.",
      "fix_sha": "9166ab60d25c6d246761b4aa33a0ceb35dd83f5c",
      "verification_ref": "At b677 (historical evidence; D-163 changes only docs CTest scheduling and its coverage checker, leaving this finding\u2019s behavior controls unchanged): exact Plan regex through ctest -N -R selected 200 total entries; CMake range/inventory/budget inspection matched shards 1\u2013199 exactly; production docs shard 199/200 passed."
    },
    {
      "id": "ADV-23",
      "category": "other",
      "severity": "medium",
      "required_property": "Every new 90-second docs-shard budget row must resolve against both the plan-pinned and PR-base checker, while D-069 remains the governing timeout policy.",
      "disposition": "fixed",
      "rationale": "At the preceding source the 168 shard rows cited D-154, which did not resolve at the immutable plan base. The exact reviewed source remaps those rows to D-068. D-068 exists and was unused in both checker bases; D-069 still governs the timeout. The immutable budget checker passes against both the plan-pinned base and exact PR base.",
      "fix_sha": "7c6f01ad5ecf3b6736bf694324acc1671d9e20cc",
      "verification_ref": "python3.14 -I tests/scripts/verify-test-budget.py --build-dir build --base f2b05c9fb3ba314cfe46959b64073ce9441724ca --repo . (pass); same command with --base 1ab65414d60828fa9505babeaeea9de0571f016c (pass); tests/scripts/verify-test-budget.py --self-test (54 controls pass)."
    },
    {
      "id": "ADV-24",
      "category": "other",
      "severity": "medium",
      "required_property": "The post-tag recovery control must pin the exact D-155 adoption-checker bytes and preserve comparisons against both the immutable pin and the reviewed revision.",
      "disposition": "fixed",
      "rationale": "The lifecycle checker pin now names 9166ab60d25c6d246761b4aa33a0ceb35dd83f5c. The adoption checker at that pin and at the reviewed source has identical SHA-256 bytes, and the recovery self-test passed with both immutable checks retained.",
      "fix_sha": "bd5ab993a3f09307e6a5ef31185f554740a0787b",
      "verification_ref": "At b677 (historical evidence; D-163 changes only docs CTest scheduling and its coverage checker, leaving this finding\u2019s behavior controls unchanged): python3.14 -I tests/scripts/verify-release-lifecycle.py --rev 7c6f01ad5ecf3b6736bf694324acc1671d9e20cc --self-test-post-tag-recovery (controls=99 positives=12); verify-v02-adoption.py blob SHA-256 at 9166ab60d25c6d246761b4aa33a0ceb35dd83f5c and b677 both 4d0ac0c724e10c7cbca3f22d57c35dd90e98dddde396f47eda23f7289ab29e93."
    },
    {
      "id": "ADV-25",
      "category": "other",
      "severity": "medium",
      "required_property": "The workflow-policy coverage verifier must pin the exact D-157 policy source while retaining baseline AST checks for functions outside the approved change set.",
      "disposition": "fixed",
      "rationale": "At 01370352 the D-157 policy source changed but the coverage checker still pinned the earlier snapshot, so its self-test rejected the candidate source. The follow-up commit pins the exact 01370352 policy blob and lists only the reviewed changed functions for the historical AST exception. The exact-source self-test and configured-inventory check now pass.",
      "fix_sha": "ecdde9d5f63500dd0ad32d9e101f47e29ded0eb2",
      "verification_ref": "At exact source bc282cc229c887d7034e533175249861db846154: workflow-policy coverage self-test passes 526 controls, including one former-four-slot and one wrong-label negative for each of 200 docs controls; configured --check passes 540 controls/6 groups; focused coverage CTest pair passes 2/2."
    },
    {
      "id": "ADV-26",
      "category": "correctness",
      "severity": "high",
      "required_property": "The Windows planning-label exception must compare all repository and output path arguments using the same case-insensitive host normalization, and its case-variant positive control must pass.",
      "disposition": "fixed",
      "rationale": "The reviewed correction normalizes both renderer --repo/--output values and the review-evidence --repo value before comparison. Wrong-repository renderer and review-command negatives reject. The exact-source POSIX self-test passes all 33 controls, including simulated Windows case variants for renderer output, renderer repository, and review repository paths.",
      "fix_sha": "b75ecb97d8ab11cda5dcb3cc94a87363e60f0cae",
      "verification_ref": "At preceding exact source b75ecb97d8ab11cda5dcb3cc94a87363e60f0cae: verify-planning-labels.py --self-test (33 controls pass, including POSIX simulated-Windows path cases). This source does not change that checker."
    },
    {
      "id": "ADV-27",
      "category": "correctness",
      "severity": "high",
      "required_property": "The exact configured CTest coverage checker must accept the actual v02_support_ledger_controls registration while enforcing its 120-second timeout and four-slot reservation.",
      "disposition": "fixed",
      "rationale": "The coverage checker now accepts and validates the exact support-ledger test properties, including LABELS=[planning,v02] and ENVIRONMENT=[GBB_TEST_BUILD_DIR=<configured build>], while retaining timeout=120 and PROCESSORS=4 checks. Exact configured-inventory validation passes at this source; the targeted CTest selection passes all three tests.",
      "fix_sha": "d0fb68361f3ffd82e1205e16609f644d4f733df2",
      "verification_ref": "At exact source bc, configured coverage check passes 540 controls/6 groups and focused coverage CTest pair passes 2/2; the 526-control self-test retains the Windows environment-path positive and wrong-directory negative. All docs reservations are two slots; non-doc reservations remain four."
    },
    {
      "id": "ADV-28",
      "category": "other",
      "severity": "medium",
      "required_property": "The workflow-policy coverage self-test must causally reject a wrong native or sanitizer-scaled timeout for v02_support_ledger_controls.",
      "disposition": "fixed",
      "rationale": "The checker self-test now changes the support-ledger native timeout to 119 seconds and the sanitizer-scaled timeout to 120 instead of 360; both mutations are rejected. It also reduces PROCESSORS to 3 for each of the four D-157 controls and the D-158 support-ledger control, and those mutations reject. Accepted native/scaled fixtures retain the exact labels and environment.",
      "fix_sha": "d0fb68361f3ffd82e1205e16609f644d4f733df2",
      "verification_ref": "At exact source bc, the 526-control self-test rejects native/scaled support-ledger timeout mutants, three-slot non-doc mutants, former-four-slot docs mutants, all docs wrong-label mutants, and the Windows wrong-directory mutant; configured check and focused coverage CTest pair pass."
    },
    {
      "id": "ADV-29",
      "category": "correctness",
      "severity": "high",
      "required_property": "The source-bound workflow-policy coverage self-test must create one synthetic CTest entry per policy or reserved test and execute a three-slot negative for every reserved control.",
      "disposition": "fixed",
      "rationale": "At fdccc15a, adding workflow_policy_group_ci and workflow_policy_group_rehearsal to PHASE23_RESERVED_TESTS made _self_test append each twice: once from GROUPS and once from the generic reserved-test loop. The initial validation rejected before any reservation mutation and the coverage CTest pair failed 1/2. At 4343d95d, the fixture generator subtracts POLICY_TEST_NAMES from only the generic synthesis loop. Both policy tests remain in PHASE23_RESERVED_TESTS and in the per-reservation mutation loop, so all ten D-161 three-slot negatives still execute.",
      "fix_sha": "4343d95dde8597253994efff2e030ae25089d288",
      "verification_ref": "At exact source bc, the 526-control self-test and 2/2 coverage CTest pair pass. The expanded inventory includes 200 unique docs controls and exercises one former-four-slot and one wrong-label mutation per entry without duplicate fixtures."
    },
    {
      "id": "ADV-30",
      "category": "correctness",
      "severity": "medium",
      "required_property": "The native macOS timeout self-test must read workflow YAML, timeout ledger, and project version from its immutable --rev instead of mutable checkout files.",
      "disposition": "fixed",
      "rationale": "At d3811b8e the positive pair check and mismatch fixture copied live .github/workflows, .github/ci-timeouts.json, and CMakeLists.txt after resolving --rev, allowing dirty configuration to mask a committed mismatch. At 48d8e501 the fixture lists workflow paths from the candidate tree and reads every workflow, the timeout ledger, and CMakeLists.txt with git show at the resolved candidate commit before running the positive and stale-ledger negative.",
      "fix_sha": "48d8e501872b9a19138a4653830a40b983199adc",
      "verification_ref": "At exact source 48d8e501872b9a19138a4653830a40b983199adc: python3 -I tests/scripts/verify-workflow-policy-coverage.py --self-test --root . --rev 48d8e501872b9a19138a4653830a40b983199adc passed with 528 controls; python3 -I .github/scripts/verify-workflow-policy.py --check --root . passed."
    }
  ]
}
```
<!-- gbb-review-evidence:end -->
