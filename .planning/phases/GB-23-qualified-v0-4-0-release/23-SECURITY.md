# Phase 23 Security Review — Qualified v0.4.0 Release

## Scope and conclusion

I re-reviewed the exact committed tree at `950c78b0bac936992403511a3cfa41f7cb1069c6`, using the writable clone as the Git evidence root. The final D-167 review includes the full source delta from the original candidate, the current Plan 23-04 T2 contract, and the D-157 through D-167 rescope. I rechecked the D-155 path confinement, D-156 lifecycle pin, D-068/D-069 budget mapping, the D-157 through D-163 workflow and CTest scheduling controls, the D-164 macOS timeout amendment, and the approved Windows path comparison.

The input-path, source-revision, and package-authority boundaries remain intact. D-161 historically added four-slot reservations for five existing CTest controls; the owner-approved D-163 amendment now assigns two slots to all 200 docs controls, while every non-doc reservation stays at four. Commands, assertions, environments, labels, fixtures, and per-test timeouts remain unchanged. No product behavior or fixture data changed.

At the prior 48d8e501 review source, the workflow-policy coverage self-test passed with 528 controls and the production check passed with 540 controls across six groups. The timeout control accepts the source-bound 50-minute macOS workflow/ledger pair and rejects a stale 40-minute ledger value; the same self-test rejects the historical c9 candidate, whose macOS cap is 40 minutes. D-163 still reserves exactly two CTest slots for each of the 200 docs controls, while all other reserved registrations remain at `PROCESSORS 4`; docs retain their `v02` label and 90-second timeout. The approved Windows path normalization and its slash/case positive and wrong-path negative remain covered. SEC-23-17 remains fixed, SEC-23-18 records the corrected immutable-candidate control, and SEC-23-09 is the only open finding: a low-severity Git-output resource-bound concern. T-23-SC remains accepted under the plan's explicit no-dependency-change scope, recorded below.

## Input, path and source boundaries

The docs checker reads ordinary public documents through `read_bounded`: it resolves the supplied root and input path, checks that the resolved file remains beneath the root, checks the file size before reading, and requires strict UTF-8 round-tripping. The ordinary document limit is 1 MiB and the historical support ledger limit is 8 MiB. Release-note inputs use a 256 KiB bound. As intended for this offline contract checker, its file root is the explicitly supplied `--root`; the CLI resolves that directory before checking documents. A child symlink that resolves outside that chosen root is rejected.

For notices, the inline digest pattern only captures fixture-relative paths. `safe_relative_parts` rejects empty, `.` and `..` components, absolute paths, and backslashes. `notice_fixture_path` additionally requires the path to start with `fixtures/`; `confined_source_file` resolves the path strictly, verifies it is beneath the resolved source root, and requires a regular file. Fixture inventory resolution applies the same containment rule to `fixtures` and to each manifest. The digest-table manifest and license paths also use the confined reader. Thus an inline row cannot make the docs checker hash an external file by adding traversal components or a symlink whose resolved target is outside the checkout.

`copy_inputs` first validates the source notice's inline paths, then checks every source through `confined_source_file`. For each output path it resolves against the canonical target root with `strict=False`, which follows existing and dangling symlink paths, and checks containment both before and after parent creation. A static symlink under the destination therefore cannot redirect the copy outside its designated root. The D-155 controls construct an external traversal notice, an outside-target notice symlink, a traversal source for `copy_inputs`, and a symlinked destination fixture directory. These controls preserve ordinary in-root fixture files and check for external writes.

The same path can be represented with separators or aliases on different hosts, but the implementation combines component checks with the host path resolver and a post-resolution containment check. Drive-relative or other platform-specific spellings that survive the text checks still have to resolve below the canonical root. I found no static path spelling that bypasses the containment check. The helper is used to create a disposable self-test snapshot, not as an atomic copy primitive against a concurrent process that can mutate the same temporary directory.

The review-evidence checker reads fixed report blobs from full commit IDs, disables replace objects and lazy fetch, checks each Git object size before materializing its blob, and applies a 30-second timeout to Git subprocesses. It compares implementation and qualification trees with `git diff --quiet` and fixed evidence exclusions instead of buffering a changed-path list. The version-window checker likewise requires full commit IDs, disables replacements/lazy fetch, validates safe repository-relative paths, size-checks blobs before reading them, and times out Git commands. The workflow-policy coverage checker also captures fixed baseline, reviewed and candidate Git blobs with timeouts but no pre-read size cap. These less-hardened paths remain in SEC-23-09.

## Release and package authority

The version-PR gate checks out the trusted PR base separately from the version-PR head, disables persisted checkout credentials, and runs the base checkers against candidate data with read-only permissions. The release path ties the tag to the exact release-please source commit and version. The trusted workflow checkout supplies the final downloaded-package validators; the tagged tree is treated as data at the final publication gate, and publication remains a single gated transition after candidate, source, and downloaded-byte checks.

The existing workflow policy and release documentation explicitly retain residual write authority in five named release jobs while candidate code is built or release state is judged. The policy classifies and constrains those jobs; it does not claim that this residual is closed. D-155 changes no package or publisher authority. D-157 changes only CI event selection, job/waiter bounds and test scheduling; the workflow permissions and protected release/package authority paths are unchanged. The branch-trigger contract requires PR updates and main-only pushes, with a causal negative for unfiltered pushes.

## D-157 CI triggers, execution bounds and Windows planning labels

The CI workflow now accepts exactly `pull_request` updates of type opened/synchronize/reopened and pushes to `main`. The read-only CI permissions and PR event remain in place. `_check_ci_planning_lane` enforces that closed trigger set; its controls include the existing `pull_request_target` refusal and a new mutation that removes the push branch filter. The workflow-policy coverage inventory includes that new mutation for both POSIX and Windows.

The timeout changes are recorded in `.github/ci-timeouts.json`: native Linux and Windows are 60 minutes, the CMake-floor job is 50 minutes, and the three preview exact-head wait/build jobs are 75 minutes with 3,900-second waits. Their cited run IDs, SHAs, samples and p50 values are unchanged; each changed workflow body has a disclosure. The ledger checker still requires YAML/ledger agreement, a timeout at least twice the cited p50, a full-run p50 at or below 30 minutes, and a disclosure when a job body changed after its cited run. Its negative controls were updated so stale-value, ratio and whole-run mutations still target their intended failures under the new caps. The failed PR #146 observations are disclosed as the reason for increasing headroom and are not substituted for successful timing samples.

CTest now reserves all four configured workers for `phase21_fixture_admission_controls`, `release_disclosure_controls`, `release_version_v04_controls` and `support_claims_v04_controls` through `PROCESSORS 4`. The existing 60/90-second test ceilings and control bodies are unchanged. The Phase 21 fixture control no longer uses `RUN_SERIAL`; with the configured four-worker CI invocation, the processor reservation keeps it exclusive from other tests.

The exception remains limited to the `release_notes_v04` test with both required labels, the exact CMake wrapper, exact Python renderer and script, fixed success regex, source root, output file, and a `--rev` equal to the full 40-hex revision extracted from the unique review-evidence contract. The output must be the one named file under the configured build directory, and no additional build-tree arguments are accepted. `_norm` applies `os.path.normcase` only on Windows; `_same_file` checks that CMake and Python resolve to the configured executables. The self-test rejects a wrong output, wrong repository, stale source revision, extra artifact and fake outer CMake. It adds case-variant positives for output, repository, interpreter and outer CMake paths on Windows, plus the review-contract repository path; POSIX simulates case-insensitive path strings only within the self-test and resets that mode in `finally`. `configured_source_revision` continues to validate the exact contract command and does not accept a changed repository or revision. I found no path exception broadening or workflow trust regression.

The final coverage harness pins `verify-workflow-policy.py` to commit `013703528fcba6bce371887d5e6dec757e103ecf` and blob SHA-256 `e0d6410b8263cb449d14bd0b36a7c5fdf5f3fc1c3af213193c68ac655082451d`. The final candidate policy blob is byte-identical to that snapshot. Relative to the prior pin, the policy diff contains exactly `_check_ci_planning_lane`, `_ledger_mutations` and `_mutations`; the harness adds only those three names to its changed-function set. It retains the original immutable baseline commit/hash and compares every other function and ordered module structure with the baseline AST. I invoked the checker's `verify_source_identity` against the final candidate; its exact snapshot and baseline AST checks passed.

## D-158 measured timeout and CTest reservation

The rescope records that exact-head run `42504839710` reached 1,843/1,853 sanitizer tests before the prior 45-minute cap, with no assertion failure reported before cancellation. It also records that `v02_support_ledger_controls` exceeded its existing 120-second Windows CTest bound in that run but passed locally in 29.89 seconds. These observations document the bounded change's rationale; they are not successful qualification or new timing samples.

The final ledger row keeps run `40163270595`, its SHA and p50 of 21.55 minutes, changes only the sanitizer job cap to 55 minutes, and discloses the observed incomplete run and changed job body. The timeout-ledger self-test passed at this SHA with 20 negative and one positive control, covering stale values, ratio, whole-run p50, schema and changed-body disclosure. The workflow changes do not touch sanitizer acceptance, fuzz jobs, branch filters, CTest parallelism or per-test ceilings.

The CTest registration keeps `v02_support_ledger_controls` at a 120-second native timeout, with sanitizer scaling to 360 seconds, and requires its build-directory environment and `planning;v02` labels plus `PROCESSORS 4`. The coverage checker requires the support control in the expected inventory and exactly one configured registration; it rejects unexpected properties, a changed working directory, timeout, environment, label set or processor count. It also requires `PROCESSORS 4` for each D-157 reservation and rejects an independent three-slot mutation for each. The exact-source self-test now passes with 128 controls, including reservation mutations for all reserved entries.

The following D-159 through D-162 sections record the original scheduling decisions and evidence at their source revisions. Their docs-shard four-slot assignments were superseded by the owner-approved D-163 amendment below; the non-doc reservations remain unchanged.

## D-159 measured full-suite CTest reservations

The rescope records that the full local suite had 1,940 passes and two timeout failures under four-worker load: `phase23_docs_controls_shard_183` exceeded its 90-second ceiling, and `preview_package_smoke` exceeded its 180-second ceiling. Each passed alone; no assertion failure was reported. I treated those as documented local contention observations, not repeatable functional failures or a new timing basis.

The implementation adds `phase23_docs_controls_shard_183` to the existing slow-doc reservation set, which applies `PROCESSORS 4`; its 90-second timeout remains unchanged. `preview_package_smoke` now has `PROCESSORS 4` alongside its unchanged 180-second timeout. The coverage checker adds both names to `PHASE23_RESERVED_TESTS`, requires each in the expected inventory and exactly one CTest registration, and rejects a three-slot mutation for each. The exact-source self-test passes with 128 controls, including reservation mutations for both policy groups. The production coverage check against the configured exact-SHA CTest registration passed with 540 controls. Global CTest parallelism and test behavior remain unchanged. No package or workflow trust boundary was widened.

## D-160 measured CTest scheduling and Windows inventory

The rescope records two full local 1,942-test runs at `f833e181` with different timeout sets under four-worker load. Each timed-out test passed sequentially, and no assertion failure occurred. The newly scheduled controls are docs shards 112, 115, 118, 119 and 122; `v02_fuzz_controls`; `v03_dispositions_controls`; `save_format_controls`; and `host_exit_crash_storm`. These results are documented local contention evidence, not a new per-test timing citation.

The five docs shards retain their 90-second ceilings and join the existing four-slot slow-shard set. `v02_fuzz_controls` keeps its 180-second bound; the v0.3 and save-format controls keep their 60-second bounds. `host_exit_crash_storm` retains its 60-second bound and is now explicitly assigned four slots. In the exact configured CTest metadata, `host_signal_term`, `host_signal_int`, and `host_signal_inherited_ign` each retain `PROCESSORS 2`; the shared helper was restored to two slots, with a separate four-slot override only for the crash-storm test.

The checker’s reserved set includes the nine named D-160 tests, requires their inventory rows and exact-once CTest registrations, and rejects a three-slot mutation for each. `host_exit_crash_storm` and `save_format_controls` are POSIX-only. The Windows simulation omits both, passes the remaining required reservations, rejects removal of a required cross-platform reservation, and rejects adding a POSIX-only reservation. The exact-source self-test passes with 128 controls, including reservation mutations for all reserved entries. The production coverage check passed against configured CTest registrations at the exact source with 540 controls. This scheduling change does not alter workflow or package authority.

## D-161 measured full-suite CTest reservations

The rescope records that a targeted 21-test four-worker selection reproduced timeouts in `fixture_admission_controls`, `v02_consumer_controls_c`, `v02_consumer_controls_cpp`, and `acceptance_dense_input_controls`; all four passed alone in 18.03, 29.05, 24.29, and 35.97 seconds. Earlier, `fixture_product_player_controls` exceeded its existing 30-second nested subprocess timeout under full-suite load but passed alone in 14.95 seconds. A later full four-worker run at `4844d39d` failed `fixture_product_core_controls`, `workflow_policy_group_ci`, `workflow_policy_group_rehearsal`, and docs shards 108 and 114 under load; each passed in an isolated four-worker CTest invocation (13.02, 14.03, 14.81, 6.46, and 6.44 seconds respectively). No assertion failure occurred and stopping CTest left no open build-clone processes.

The CMake changes reserve all four slots for the ten existing controls: `fixture_product_player_controls`, `fixture_product_core_controls`, `fixture_admission_controls`, both `v02_consumer_controls_*` builds, `acceptance_dense_input_controls`, `workflow_policy_group_ci`, `workflow_policy_group_rehearsal`, and docs shards 108 and 114. Exact configured CTest metadata confirms `PROCESSORS 4` for all ten and unchanged commands, labels/environments where configured, and outer timeouts of 120, 120, 90, 600, 600, 600, 180, 180, 90, and 90 seconds. Consumer and dense-input controls retain `COST 600`. All ten registrations are cross-platform. The diff changes only CTest scheduling, the reserved-name inventory, and its expected control count; product behavior, fixtures, timeout limits, and package/workflow authority remain unchanged.

The exact-source checker now passes its positive fixture and all reservation mutations. The prior version added synthetic records for every `PHASE23_RESERVED_TESTS` entry after creating one for each policy group, duplicating `workflow_policy_group_ci` and `workflow_policy_group_rehearsal`. This fix excludes `POLICY_TEST_NAMES` from that synthetic append loop while retaining both names in the reserved set, so their real group records receive the required processor checks and three-slot mutations. At this source the 128-control self-test passes, the production check passes with 540 controls, and both coverage CTests pass. The fdccc15a-to-4343d95 implementation delta changes only this checker fixture-generation expression; it changes no CMake registration, product code, fixture data, timeout, platform, or workflow-authority boundary.


## Exact existing labels for reserved CTest controls

The checker now requires the exact existing `LABELS ["v02"]` property for `fixture_product_core_controls`, `fixture_product_player_controls`, `fixture_admission_controls`, both v0.2 consumer controls, and docs shards 108 and 114. It adds one wrong-label mutation per test. The exact-source coverage self-test passed with 135 controls, confirming the seven mutations and accepted counterparts. After a fresh CMake configure pinned to `3c908d7f`, the production check passed with 540 controls across six groups; the full local suite and focused exact-source CTest gate also passed. The configured CTest inventory shows all seven with exactly `v02`, `PROCESSORS 4`, and their unchanged timeouts. No CMake property, test command, fixture, timeout, platform condition, or trust boundary changes in the `4343d95d` to `3c908d7f` delta.

## Windows support-ledger environment path comparison

The checker now compares the `GBB_TEST_BUILD_DIR` value using Windows path rules when validating a Windows inventory: it converts slash styles, applies `ntpath.normpath` and case normalization, and still requires the same normalized build path. The Windows positive control changes slash style and case and is accepted; the wrong-build-path negative is rejected. Exact-source self-test=136 confirms both controls. The CTest registration still has the existing `v02` label, four-slot reservation, and unchanged timeout; no CMake or runtime behavior changed.

The earlier hosted run at `6ae7a467` was not green: Linux native passed, Windows failed `workflow_policy_coverage` on the support-ledger `ENVIRONMENT` path comparison, native macOS was canceled at its 40-minute cap after 1,927/1,942 tests, and CMake-floor was canceled at its 50-minute cap after about 1,920/1,942. The current change addresses the Windows comparison failure, but no hosted rerun evidence was provided; I do not treat the earlier run as qualification success.

## D-162 docs-shard scheduling and coverage controls

D-162 adds twelve existing docs-control shards to the four-slot slow-test property set: `phase23_docs_controls_shard_05`, `_07`, `_89`, `_154`, `_155`, `_160`, `_181`, `_182`, `_191`, `_192`, `_198`, and `_199`. Their existing commands, `v02` labels, fixture inputs, and 90-second CTest timeouts are unchanged; the registrations are cross-platform. Exact configured CTest metadata confirms all twelve have `PROCESSORS 4`, `LABELS ["v02"]`, and `TIMEOUT 90`.

The immutable-source coverage checker adds all twelve names to `PHASE23_RESERVED_TESTS` and `EXPECTED_RESERVED_LABELS`. It requires one inventory row and one configured registration per name, `PROCESSORS 4`, and the exact `v02` label. Its existing mutation loop now produces one three-slot negative per reservation and one wrong-label negative per named test. The expected self-test count rises from 136 to 160. At b677 the self-test passed with 160 controls, the production check passed with 540 controls across six groups, and both workflow-policy coverage CTests passed (2/2). The final c09 amendment changes only `.planning/context/LESSONS.md`; executable and test-registration source remains identical to b677. These D-162 changes alter no product behavior, fixture contents, per-test timeout, CI job budget, workflow/package authority, or platform boundary.

The prior Windows support-ledger path correction remains unchanged: Windows comparison normalizes separators and case with `ntpath`, accepts the slash/case positive, and rejects a wrong build path. The existing Git-output paths without pre-read output caps also remain unchanged, so SEC-23-09 is still applicable.


## D-163 docs-shard two-slot scheduling amendment

The rescope records that a 224-test focused four-worker selection timed out sixteen docs shards (03, 04, 17, 35, 46, 50, 97, 103, 110, 123, 135, 144, 156, 158, 189, and 190); all passed sequentially on the same build in 91.02 seconds total, with the other focused gates passing. Earlier D-162 timeouts affected a different subset, consistent with contention moving across the inventory rather than assertion failures.

D-163 first reserved all 200 docs controls for four workers. The owner-approved amendment now reserves exactly two workers per docs control, including `v02_adoption_docs_controls` and shards 01–199, allowing at most two docs controls to run together under global `--parallel 4`. Exact configured metadata confirms all 200 retain their existing `v02` label and 90-second CTest timeout. Their commands, assertions, fixtures, platform registration, and CI job caps are unchanged. All other reserved registrations remain at `PROCESSORS 4`.

The immutable-source checker derives all 200 docs names, requires each inventory row and one CTest registration, and requires `PROCESSORS 2` plus the exact `v02` label for each. It rejects the former four-slot value and a wrong label per docs control; non-doc processor checks and their three-slot negatives remain at four slots. At this SHA, the self-test passed with 526 controls, the production check passed with 540 controls across six groups, and the focused coverage CTest pair passed 2/2. The Windows support-ledger path normalization positive and wrong-path negative remain covered. The amendment changes CTest scheduling only and introduces no new security or correctness issue.

The rescope cites hosted run `42654987218`: native Linux completed all 1,942 tests, while macOS, CMake-floor, sanitizer-inventory, and Windows reached their existing job caps. This is not a complete hosted qualification pass. The later D-164 macOS-only cap change is detailed below.

## D-164 native macOS timeout and ledger

The exact-head run `42679813590` reached the previous native macOS cap at 1,928/1,942 tests; all 200 docs controls passed and the cancellation log had no CTest assertion failure. The owner-approved amendment raises only this job's cap from 40 to 50 minutes. Its existing `17.80`-minute p50, cited run/SHA and five samples are unchanged. The disclosure identifies the macOS-15 runner migration and the incomplete exact-head run without treating that run as a timing sample. The workflow-policy checker still enforces YAML/ledger equality and the existing p50 ratio. No permissions, job dependencies, per-test timeout, other job cap, fixture scope, package, or dependency changed.

The coverage self-test now reads its workflow inventory, YAML files, timeout ledger and `CMakeLists.txt` from the exact `--rev` commit through Git-object commands, builds the temporary validation tree only from those committed bytes, accepts the matching 50-minute pair, and rejects a 40-minute ledger value as `timeout-ledger-stale`. This prevents dirty working-tree files from masking a stale candidate. The exact 48d self-test passes with 528 controls; the same self-test at c9 correctly refuses the 40-minute candidate. SEC-23-18 records and closes the source-binding defect in the first version of this control.

## Threat verification and accepted risk

| Plan threat | Disposition in the plan | Review evidence and remaining gate |
|---|---|---|
| T-23-07 — reviewed/hosted revision identity | Mitigate | The review-evidence gate checks immutable implementation/report identities and source drift. This report names the exact implementation SHA; final hosted exact-head verification remains a later qualification gate. |
| T-23-08 — review and adversarial disposition | Mitigate | The immutable gate is in place and exact-source reports are being reissued. The complete committed-report check and qualification remain prerequisites; this security report does not claim they have passed. |
| T-23-09 — workflow optimization privilege | Mitigate | D-164 changes only the native macOS timeout and paired ledger/test control. Workflow permissions, required job dependencies, and trusted release/package authority are unchanged. |
| T-23-SC — package-install tampering | **Accept (plan-approved)** | Plan 23-04 explicitly accepts this risk because no dependency changes are planned. The D-164 amendment changes no package inputs or dependencies. Revisit this acceptance if a dependency change enters scope; this report records the existing plan disposition and does not create new owner approval. |

The report gate and exact-head protected checks are still required before Phase 23 qualification or merge.

## Findings

### SEC-23-01 — Declared reviewer identity is not cryptographic authentication

**Disposition:** Rejected.

The alleged defect does not apply to the declared trust boundary. Plan 23-04 assigns substantive review to independent source-reading reviewers and the checker to mechanical validation of role, identity fields, schema, source identity and disposition. The checker makes no cryptographic identity claim.

### SEC-23-02 — Qualification comparison must not buffer an unbounded diff

**Disposition:** Fixed in `1b7a01f30bd0b3c9330c3e633e4f60319e7b6712`.

The report checker asks Git whether unexpected source changes exist with `diff --quiet`; it does not materialize an attacker-sized path list. Its report/blob reader checks the object size before reading. Controls exercise evidence-only qualification acceptance and source-drift rejection.

### SEC-23-03 — Ledger-link destinations must be exact

**Disposition:** Fixed in `9a193975fb32ae69bd09be2cf847e3271d078733`.

The release-note and version-window validators accept only the supported relative ledger path or canonical version-tag URL. Their controls reject external URLs, lookalikes, malformed links, images and links hidden in code, while preserving the supported visible destinations.

### SEC-23-04 — Unmatched Markdown delimiters must not rescan suffixes

**Disposition:** Fixed in `276f317d199cdd3246e9a90ce72a1f3a1235af1c`.

The version-window link parser precomputes escape and bracket data and processes delimiters without repeatedly rescanning suffixes. Its unmatched-bracket control cannot create a qualifying ledger link.

### SEC-23-05 — Non-visible Markdown cannot supply disclosure proof

**Disposition:** Fixed in `276f317d199cdd3246e9a90ce72a1f3a1235af1c` for the enumerated containers and malformed forms.

The required-doc and version-window validators mask comments and code containers or reject unsupported tabs and raw HTML. Paired controls cover nested/list/blockquote code, malformed links, and hidden HTML forms. The later visibility bypasses have their own findings below.

### SEC-23-06 — Incomplete raw-HTML openers cannot hide required proof

**Disposition:** Fixed in `a63f1dc67654613e105ac1071b7445f21adea0bc`.

Both validators reject incomplete `script`, `pre` and `style` starts, declarations and processing-instruction openers after masking comments and code. Production-path controls require the scoped failure for these forms.

### SEC-23-07 — Inline code cannot satisfy required natural-language disclosure

**Disposition:** Fixed in `c4ed9eed86871db9f9dc225565a85a55ab0a8036`.

Phrase matching masks inline code except for exact code tokens required by a clause. Production controls cover the README hardware limits, game-acceptance absence, release limits, evidence-name wording and nested-backtick rights language.

### SEC-23-08 — Third-party attribution rows must remain visible

**Disposition:** Fixed in `05a9023bc38d487eca5de8502de4b0708165f0e8`.

All required fixture attribution rows require visible provenance, rights and repository-only distribution wording. The docs controls hide each required row in a code fence and require its specific diagnostic; digest rows are parsed outside comments, code blocks and inline code.

### SEC-23-09 — Some Git output paths can consume unbounded runner resources

**Severity:** Low. **Disposition:** Open, non-blocking.

This is a bounded-availability concern, not a source-identity or release-policy bypass. `identity_at_revision` captures fixed `git show` blobs and a support-tree listing without output caps. `immutable_blob` captures a Git blob before applying its 4 MiB limit and has no subprocess timeout; its paired tree listing is also uncapped. The version-window checker captures all `git diff --name-only -z` paths before filtering them, without an output/count cap. `verify-no-phase-paths.py` captures the full `git ls-files -z` listing without a timeout or output cap, then reads tracked regular files in full. The lifecycle helper's fixed `git show` calls have timeouts but no output caps. Oversized repository objects or trees can consume memory or time in a runner. These paths do not change the checked source identity or grant release authority.

### SEC-23-10 — Visible CommonMark claim forms must normalize before matching

**Disposition:** Fixed in `b798781105b8f6f803e85aa2ad766d2b2fdbec22`.

The CGB-game claim matcher removes literal format/default-ignorable characters, decodes valid CommonMark character references in visible prose, normalizes hard line breaks and paired emphasis, and exposes inline and shortcut/full/collapsed reference-link labels while excluding destinations, titles and masked code. Docs, notice and release-note controls pair these claims with escaped, unresolved, destination/title-only and inline/fenced-code counterparts.

### SEC-23-11 — Emphasis matching must remain bounded on dense input

**Disposition:** Fixed in `6876fab06bf746fdaab67beaa4d52a6b1c70ac06`.

The prior closer loop searched earlier delimiter runs repeatedly. The fixed matcher checks a constant set of six candidate buckets per closer and inserts/removes candidates once. Dense unmatched-marker controls cover docs, notices and release notes, with safe-prose counterparts.

### SEC-23-12 — Unicode symbols must count as emphasis punctuation

**Disposition:** Fixed in `4c9c54f8b5a33e758624c997f107d1ffdd7c94a0`.

The delimiter classifier recognizes Unicode punctuation and symbol categories, as CommonMark requires. Symbol-adjacent underscore and rule-of-three claim controls reject, while safe symbol/emphasis prose remains accepted.

### SEC-23-13 — Nested reference labels must be rejected before repeated normalization

**Disposition:** Fixed in `4c9c54f8b5a33e758624c997f107d1ffdd7c94a0`.

The parser precomputes paired-opening counts and rejects empty, over-999-character or nested candidate spans in constant time before copying or normalizing them. Only valid labels within the CommonMark limit proceed. Dense nested-bracket controls cover docs, notices and release notes, with safe-prose counterparts.

### SEC-23-14 — Inline notice paths and self-test copies must stay under their roots

**Severity:** Medium. **Disposition:** Fixed in `9166ab60d25c6d246761b4aa33a0ceb35dd83f5c`.

At the preceding implementation source, a notice digest path such as `fixtures/../../...` could resolve outside the repository; `copy_inputs` used that path for both the source and isolated copy. At the reviewed source, path components are checked and the resolved source must be a regular file beneath the canonical root. Notice manifest/license paths and inline digest rows use that same confinement. Self-test source paths are validated before copy; destination symlinks are resolved and checked under the destination root before and after parent creation. The committed D-155 controls target traversal, an external symlink as a notice input, a traversal source passed through `copy_inputs`, and a symlinked copy target. The shard-0 production docs self-test passed at `7c6f01ad`; the adoption checker and those controls are unchanged in the D-157 diff. The complete 200-shard CTest selector was not run by this reviewer.

### SEC-23-15 — New timeout-budget rows must resolve and remain distinct at immutable bases

**Severity:** Medium. **Disposition:** Fixed in `7c6f01ad5ecf3b6736bf694324acc1671d9e20cc`.

The earlier mapping used D-154, which did not exist in the plan-pinned base and therefore could not authorize those new allowlist rows. The approved correction maps the 168 newly introduced shard 32–199 rows to D-068, present and unused in both the plan-pinned and PR bases. The 90-second ceiling and shard coverage stay the same, and D-069 remains the timeout-policy decision. The plan-pinned budget checker passed against `f2b05c9fb3ba314cfe46959b64073ce9441724ca`; the orchestrator also confirmed a pass against PR base `1ab65414d60828fa9505babeaeea9de0571f016c`.

### SEC-23-16 — D-157 CTest slot reservations require causal regression controls

**Severity:** Low. **Disposition:** Fixed in `d0fb68361f3ffd82e1205e16609f644d4f733df2`.

The prior checker verified only the support-ledger and separate release-policy reservations, although the four D-157 qualification controls had `PROCESSORS 4` in CMake. At this source, `PHASE23_RESERVED_TESTS` includes all four controls; inventory and exact-once registration are required, and the checker rejects a three-slot mutation for each. The exact-source self-test passed all 105 controls, including those four reservation negatives. This closes the regression-control gap; it does not change the runtime scheduling or security authority boundary.


### SEC-23-17 — Workflow-policy reservation self-test duplicates existing group tests

**Severity:** Medium. **Disposition:** Fixed in `4343d95dde8597253994efff2e030ae25089d288`.

At the preceding source `fdccc15a`, the self-test appended synthetic reserved-test records after it had already created records for each `GROUPS` entry. Since `workflow_policy_group_ci` and `workflow_policy_group_rehearsal` were in both sets, the positive fixture contained duplicate test names and rejected before running reservation mutations. The fix excludes `POLICY_TEST_NAMES` from the synthetic append loop but leaves both groups in the processor-reserved set and the mutation loop. The exact-source 128-control self-test and production check passed, and both coverage CTests passed. The ten CTest reservations and their runtime properties are unchanged.

### SEC-23-18 — macOS timeout control must read the immutable candidate

**Severity:** Medium. **Disposition:** Fixed in `48d8e501872b9a19138a4653830a40b983199adc`.

The first D-164 control read the live worktree's workflow, timeout ledger, and `CMakeLists.txt`. A caller could supply an older candidate with a 40-minute cap while a dirty worktree supplied the new 50-minute values, causing a false pass. The corrected control enumerates the workflow files and reads each input from the resolved candidate commit before constructing its temporary fixture. The exact-candidate self-test accepts 48d's 50-minute pair and rejects c9's stale 40-minute candidate; it also mutates the committed 50-minute ledger to 40 and verifies the intended `timeout-ledger-stale` diagnostic.

## Verification and limits

This review is bound to `48d8e501872b9a19138a4653830a40b983199adc`. At this exact SHA, `python3 -I tests/scripts/verify-workflow-policy-coverage.py --self-test --root . --rev 48d8e501872b9a19138a4653830a40b983199adc` passed with 528 controls. The production `--check` passed with 540 controls across six groups. The same self-test with `--rev c9a6320671b56d1092b2884aeac15d6a9320b60f` rejected the historical 40-minute macOS cap. The focused CTest pair was not rerun by this reviewer at 48d; the implementation commit's local qualification will bind it separately. Configured CTest metadata from the prior reviewed source confirms all 200 docs controls have `PROCESSORS 2`, `LABELS ["v02"]`, and `TIMEOUT 90`; all other reserved registrations retain `PROCESSORS 4`.

The D-163 rescope cites hosted run `42654987218`: native Linux completed 1,942/1,942; macOS, CMake-floor, sanitizer-inventory, and Windows reached their existing job caps while docs shards passed in sequence. This is not a complete hosted qualification pass. The earlier hosted run `6ae7a46777348d02bf4e20419df0bfc8a5929591` was also not green: Windows failed workflow-policy coverage on the support-ledger path spelling, native macOS was canceled at its 40-minute cap after 1,927/1,942 tests, and CMake-floor was canceled at its 50-minute cap after about 1,920/1,942. The current checker retains the approved Windows path comparison. No full local CTest run at this SHA is included in this review; the previous complete local run passed 1,942/1,942 at `3c908d7f`.

SEC-23-09 remains the only open finding. The plan-approved T-23-SC package-install risk is explicitly recorded above as accepted; no dependency changes are present. The D-155 docs shard-0 self-test and D-156 recovery control passed at `7c6f01ad`; their validators remain unchanged. The plan-pinned budget check passed against `f2b05c9fb3ba314cfe46959b64073ce9441724ca`, and the orchestrator confirmed the PR-base check against `1ab65414d60828fa9505babeaeea9de0571f016c`; budget files remain unchanged. This review does not inspect live branch protection or exercise publication, and does not fetch/build/run/admit real fixtures.

## D-167 exact-source re-review

I re-reviewed `950c78b0bac936992403511a3cfa41f7cb1069c6`, compared with original candidate `029a77f5a87682cee545aa99edc1fe5263e5a77c` and the D-167 delta from `170b7eb2ba24ea166376ddf2088ce3d731fddc37`. ACCEPT. The Linux preview runner is pinned to `ubuntu-22.04`, and the profile rejects `container` and `services` for all three waiter jobs. The existing policy check pins the two macOS preview jobs to `macos-15`. The false-branch, function-shadow, comment/variable deadline, disabled-step, folded YAML, and pre-wait `GITHUB_ENV` controls remain. Exact checkout-to-waiter ordering, literal argv, and closed environments remain enforced. The waiter script hash is unchanged from the original candidate; required-native dependencies and permissions are unchanged. The source-bound coverage self-test passed 573 controls; workflow-policy `ci` and `ledger` groups passed; the configured focused Plan 23-04 selection passed 224/224 at this implementation source. No D-167 bypass remains; no hosted CI ran during review. Existing low-severity SEC-23-09 remains disclosed.

<!-- gbb-review-evidence:start -->
```json
{
  "schema_version": 1,
  "report_id": "phase23-security-reservation-20261110-5eefa412",
  "role": "security",
  "reviewer_id": "reservation-security-20261110",
  "independent": true,
  "reviewed_sha": "5eefa412e679afe6044e3a80f93a73d269ec0c9d",
  "findings": [
    {
      "id": "SEC-23-01",
      "category": "security",
      "severity": "low",
      "required_property": "Mechanical report validation must remain distinct from substantive source review and must not be represented as cryptographic reviewer authentication.",
      "disposition": "rejected",
      "rationale": "Plan 23-04 assigns substantive review to independent source-reading reviewers and the checker to declared identity, role, schema and disposition validation. The verifier validates those declared fields but does not claim cryptographic authentication, so this alleged defect does not apply to the specified trust boundary.",
      "fix_sha": null,
      "verification_ref": "23-04-PLAN.md task 23-04-T1; tests/scripts/verify-review-evidence.py:142-157,318-330"
    },
    {
      "id": "SEC-23-02",
      "category": "security",
      "severity": "medium",
      "required_property": "Qualification must reject non-evidence source drift without buffering an unbounded changed-path list.",
      "disposition": "fixed",
      "rationale": "The checker compares implementation and qualification trees with git diff --quiet and fixed evidence exclusions; immutable report blobs are size-checked before materialization. Its controls accept evidence-only changes and reject source drift.",
      "fix_sha": "1b7a01f30bd0b3c9330c3e633e4f60319e7b6712",
      "verification_ref": "tests/scripts/verify-review-evidence.py:71-84,218-225,401-406; source-bound self-test controls"
    },
    {
      "id": "SEC-23-03",
      "category": "correctness",
      "severity": "medium",
      "required_property": "Only the exact supported relative ledger destination or canonical version-tag URL may satisfy the release ledger-link requirement.",
      "disposition": "fixed",
      "rationale": "The release-note and version-window link validators constrain accepted destinations; their controls reject external, lookalike, malformed, image and hidden-code links while preserving supported visible destinations.",
      "fix_sha": "9a193975fb32ae69bd09be2cf847e3271d078733",
      "verification_ref": "tests/scripts/verify-v02-adoption.py:2061-2180; tests/scripts/verify-version-window.py:318-432,1338-1364; source-bound ledger-link controls"
    },
    {
      "id": "SEC-23-04",
      "category": "security",
      "severity": "medium",
      "required_property": "Unmatched Markdown delimiters must not cause repeated suffix rescanning during ledger-link parsing.",
      "disposition": "fixed",
      "rationale": "The version-window parser precomputes bracket and escape data and processes delimiters without repeated suffix scans. Its unmatched-bracket control does not create a qualifying ledger link.",
      "fix_sha": "276f317d199cdd3246e9a90ce72a1f3a1235af1c",
      "verification_ref": "tests/scripts/verify-version-window.py:318-432,1353-1364; unmatched-bracket control"
    },
    {
      "id": "SEC-23-05",
      "category": "correctness",
      "severity": "medium",
      "required_property": "Only visible Markdown may satisfy required disclosures and ledger clauses; tested code containers, malformed links and HTML constructs must fail closed.",
      "disposition": "fixed",
      "rationale": "The enumerated comments, fenced/indented/inline code, tabs and raw HTML are masked or rejected by the bounded validators. Later visibility cases have separate source-bound findings.",
      "fix_sha": "276f317d199cdd3246e9a90ce72a1f3a1235af1c",
      "verification_ref": "tests/scripts/verify-v02-adoption.py:699-790,1404-1618; tests/scripts/verify-version-window.py:435-615; docs controls"
    },
    {
      "id": "SEC-23-06",
      "category": "correctness",
      "severity": "high",
      "required_property": "An incomplete raw-HTML block opener must not hide a required release disclosure or ledger link from rendered public proof.",
      "disposition": "fixed",
      "rationale": "Both validators reject incomplete script/pre/style starts, declarations and processing-instruction openers after code and comment masking; production controls require the scoped raw-HTML diagnostic.",
      "fix_sha": "a63f1dc67654613e105ac1071b7445f21adea0bc",
      "verification_ref": "tests/scripts/verify-v02-adoption.py:55,734-747,2775-2788,2969-2975; tests/scripts/verify-version-window.py:310-315,1373-1398; reviewed-source controls"
    },
    {
      "id": "SEC-23-07",
      "category": "correctness",
      "severity": "high",
      "required_property": "Required natural-language disclosures must remain visible outside inline code while preserving explicitly required code tokens.",
      "disposition": "fixed",
      "rationale": "Phrase matching masks inline code except exact tokens required by a clause. Production-path controls cover README, game acceptance, release limits, evidence-name wording and nested-backtick rights text.",
      "fix_sha": "c4ed9eed86871db9f9dc225565a85a55ab0a8036",
      "verification_ref": "tests/scripts/verify-v02-adoption.py:734-747,1640-1665,1714-1734,3585-3600,3770-3785; docs and notice controls"
    },
    {
      "id": "SEC-23-08",
      "category": "correctness",
      "severity": "medium",
      "required_property": "Every required third-party attribution row must remain visible with its source, rights, license and repository-only distribution wording.",
      "disposition": "fixed",
      "rationale": "All seven attribution rows require complete visible wording. Controls move each row into a fence and require its specific missing-disclosure diagnostic; digest rows are parsed outside comments and code.",
      "fix_sha": "05a9023bc38d487eca5de8502de4b0708165f0e8",
      "verification_ref": "tests/scripts/verify-v02-adoption.py:655-689,1980-2014; source-bound docs controls"
    },
    {
      "id": "SEC-23-09",
      "category": "other",
      "severity": "low",
      "required_property": "Git-derived blobs, repository listings and changed-path lists should be bounded before materialization, and their subprocesses should have explicit timeouts.",
      "disposition": "open",
      "rationale": "identity_at_revision captures fixed Git blobs and a tree listing without output caps; adoption immutable_blob captures blob bytes before checking its 4 MiB limit and omits timeouts; version-window changed_paths captures the full diff path list; verify-no-phase-paths captures all tracked paths without timeout/output caps and reads files in full; lifecycle git_show has timeouts but no output caps. This remains a low availability-hardening concern, not a source-identity or authority bypass. The workflow-policy coverage checker also captures fixed baseline/reviewed/candidate Git blobs with subprocess timeouts but no pre-read output cap; this is the same low availability-hardening concern.",
      "fix_sha": null,
      "verification_ref": null
    },
    {
      "id": "SEC-23-10",
      "category": "correctness",
      "severity": "medium",
      "required_property": "Visible unsupported CGB-game claims must be rejected after CommonMark character, line-break, emphasis and inline/reference-link rendering, while destinations, titles and code remain excluded.",
      "disposition": "fixed",
      "rationale": "The production callers provide code-masked visible prose. The matcher handles literal format/default-ignorable characters, valid character references, hard breaks, emphasis and visible inline/reference-link labels while excluding destinations, titles and code; paired controls preserve escaped, unresolved and safe counterparts.",
      "fix_sha": "b798781105b8f6f803e85aa2ad766d2b2fdbec22",
      "verification_ref": "tests/scripts/verify-v02-adoption.py:165-370,699-790,1714-1919,3461-3468,3713-3716,2677-2686; docs/notice/release-note control definitions"
    },
    {
      "id": "SEC-23-11",
      "category": "other",
      "severity": "low",
      "required_property": "Emphasis normalization must process bounded documents without repeatedly scanning all prior delimiter runs.",
      "disposition": "fixed",
      "rationale": "The implementation checks a fixed six candidate buckets per closer and each run is pushed or removed once. Dense unmatched-marker and safe-prose controls exercise docs, notices and release notes.",
      "fix_sha": "6876fab06bf746fdaab67beaa4d52a6b1c70ac06",
      "verification_ref": "tests/scripts/verify-v02-adoption.py:228-239,260-357,2682-2686,3517-3524,3738-3744; dense marker controls"
    },
    {
      "id": "SEC-23-12",
      "category": "correctness",
      "severity": "medium",
      "required_property": "Unicode symbol punctuation must participate in CommonMark emphasis delimiter flanking so visible claims cannot pass between symbol-adjacent delimiters.",
      "disposition": "fixed",
      "rationale": "The delimiter classifier recognizes Unicode P and S categories. Symbol-adjacent strong-underscore and rule-of-three claim controls reject while safe symbol/emphasis prose remains accepted.",
      "fix_sha": "4c9c54f8b5a33e758624c997f107d1ffdd7c94a0",
      "verification_ref": "tests/scripts/verify-v02-adoption.py:212-218,260-305,3461-3464,3479-3480,3706-3712; paired symbol controls"
    },
    {
      "id": "SEC-23-13",
      "category": "other",
      "severity": "low",
      "required_property": "Nested reference-label candidates must be rejected before repeated string copies or normalization, with total work bounded by document size.",
      "disposition": "fixed",
      "rationale": "The parser precomputes paired-opening counts and rejects empty, over-999-character and paired-nested-bracket spans before copying or normalization. Dense nested-bracket claim rejection is paired with safe prose across docs, notices and release notes.",
      "fix_sha": "4c9c54f8b5a33e758624c997f107d1ffdd7c94a0",
      "verification_ref": "tests/scripts/verify-v02-adoption.py:1278-1298,1322-1389,232-239,2684-2686,3525-3530,3746-3751; paired nested-label controls"
    },
    {
      "id": "SEC-23-14",
      "category": "security",
      "severity": "medium",
      "required_property": "Inline notice paths and self-test source/destination paths must resolve to regular files beneath their respective canonical roots, including when symlinks are present.",
      "disposition": "fixed",
      "rationale": "The reviewed source rejects unsafe path components, resolves source files strictly beneath the canonical repository root, and resolves copy destinations beneath the target before and after parent creation. The D-155 traversal and symlink controls remain unchanged; the shard-0 production docs self-test passed at 7c6f01ad.",
      "fix_sha": "9166ab60d25c6d246761b4aa33a0ceb35dd83f5c",
      "verification_ref": "tests/scripts/verify-v02-adoption.py:1922-1970,2002-2004,2481-2498,3106-3129,4121-4165; python3 -I tests/scripts/verify-v02-adoption.py --self-test docs --shard 0 200 --repo . passed at 7c6f01ad; git diff 7c6f01ad..3c908d7f: no adoption-checker changes"
    },
    {
      "id": "SEC-23-15",
      "category": "correctness",
      "severity": "medium",
      "required_property": "Every newly added test-budget row must cite a distinct decision reference present in each immutable base used by the plan and PR checkers, while D-069 remains the governing timeout policy.",
      "disposition": "fixed",
      "rationale": "D-154 was absent from the plan-pinned base, so the new rows did not resolve. The approved correction maps the 168 new shard 32\u2013199 rows to D-068, which exists and is unused in both checker bases. The 90-second ceilings and shard inventory are unchanged, and D-069 remains the timeout policy. Both exact-base budget checks passed.",
      "fix_sha": "7c6f01ad5ecf3b6736bf694324acc1671d9e20cc",
      "verification_ref": "python3 -I tests/scripts/verify-test-budget.py --build-dir build --base f2b05c9fb3ba314cfe46959b64073ce9441724ca --repo . (pass); same checker against PR base 1ab65414d60828fa9505babeaeea9de0571f016c (pass); tests/ci/test-budget-allowlist: 168 rows use D-068; D-068 exists and is unused at both bases; git diff 7c6f01ad..3c908d7f: no test-budget checker or allowlist changes"
    },
    {
      "id": "SEC-23-16",
      "category": "other",
      "severity": "low",
      "required_property": "All four D-157 CTest slot reservations must be asserted by a registration control with a negative mutation so scheduling regressions cannot pass qualification controls silently.",
      "disposition": "fixed",
      "rationale": "The prior checker verified only the support-ledger and separate release-policy reservations, while the four D-157 qualification controls were configured with PROCESSORS 4 but had no causal check. At this source all four are in PHASE23_RESERVED_TESTS, present in the expected inventory, registered exactly once, and required to reserve four slots. Independent three-slot mutations for all four are rejected by the coverage self-test, which passed with 105 controls.",
      "fix_sha": "d0fb68361f3ffd82e1205e16609f644d4f733df2",
      "verification_ref": "tests/scripts/verify-workflow-policy-coverage.py:37-44,952-957,1286-1289; python3 -I tests/scripts/verify-workflow-policy-coverage.py --self-test --root . --rev d0fb68361f3ffd82e1205e16609f644d4f733df2 (pass, 105 controls); production --check against configured CTest registrations (pass, 540 controls)"
    },
    {
      "id": "SEC-23-17",
      "category": "correctness",
      "severity": "medium",
      "required_property": "The exact-source workflow-policy coverage self-test must accept its complete positive CTest inventory and execute a causal three-slot rejection for every measured reservation.",
      "disposition": "fixed",
      "rationale": "At fdccc15a, the self-test appended synthetic reserved-test records after it had already created records for each GROUPS entry. Since workflow_policy_group_ci and workflow_policy_group_rehearsal were in both sets, the positive fixture contained duplicate test names and rejected before reservation mutations. The fix excludes POLICY_TEST_NAMES from the synthetic append loop while retaining both groups in the processor-reserved set and mutation loop. The exact-source 128-control self-test and 540-control production check passed, and both coverage CTests passed.",
      "fix_sha": "4343d95dde8597253994efff2e030ae25089d288",
      "verification_ref": "tests/scripts/verify-workflow-policy-coverage.py:1212-1216,1318-1323; python3 -I tests/scripts/verify-workflow-policy-coverage.py --self-test --root . --rev 4343d95dde8597253994efff2e030ae25089d288 (pass, 128 controls); --check --root . --rev 4343d95dde8597253994efff2e030ae25089d288 --build-dir build (pass, 540 controls); ctest --test-dir build --output-on-failure --no-tests=error -R \"^workflow_policy_coverage(_controls)?$\" (2/2 pass)"
    },
    {
      "id": "SEC-23-18",
      "category": "correctness",
      "severity": "medium",
      "required_property": "The native macOS cap control must read the workflow, timeout ledger, and project version from the exact candidate commit rather than the mutable working tree.",
      "disposition": "fixed",
      "rationale": "The first D-164 coverage control could validate dirty 50-minute worktree files while the supplied candidate still had a 40-minute cap. The corrected self-test enumerates candidate workflow paths with git ls-tree and reads each fixture input with git show from the resolved candidate SHA before validation and mutation.",
      "fix_sha": "48d8e501872b9a19138a4653830a40b983199adc",
      "verification_ref": "python3 -I tests/scripts/verify-workflow-policy-coverage.py --self-test --root . --rev 48d8e501872b9a19138a4653830a40b983199adc (pass, 528 controls); same command with --rev c9a6320671b56d1092b2884aeac15d6a9320b60f rejects the stale 40-minute candidate; the 48d fixture also rejects a 40-minute ledger row as timeout-ledger-stale."
    },
    {
      "id": "SEC-23-19",
      "category": "security",
      "severity": "high",
      "required_property": "The shell-policy check must reject dead-branch decoys and a function that shadows the literal Python waiter command.",
      "disposition": "fixed",
      "rationale": "At 07bdf08, in-memory attacks showed that the exact command could be made unreachable or shadowed by a shell function. The source-bound parser now requires one unconditional shell event and exact literal argv; the negatives reject for every waiter lane.",
      "fix_sha": "e5a2f71dbf2ed27912d0ba810d434e95b9fc8c4c",
      "verification_ref": "At 950c78b0bac936992403511a3cfa41f7cb1069c6, the 573-control exact-source coverage self-test rejects dead-branch and Python-shadow mutations on all three preview jobs."
    },
    {
      "id": "SEC-23-20",
      "category": "security",
      "severity": "high",
      "required_property": "A prior step cannot inject BASH_ENV through GITHUB_ENV before the exact-head waiter executes.",
      "disposition": "fixed",
      "rationale": "At e5a2f71d, a step before the waiter could write a Python wrapper and set BASH_ENV through GITHUB_ENV. The profile now requires the waiter immediately after the exact pinned checkout, and the per-lane predecessor mutation rejects.",
      "fix_sha": "170b7eb2ba24ea166376ddf2088ce3d731fddc37",
      "verification_ref": "At 950c78b0bac936992403511a3cfa41f7cb1069c6, exact-source coverage self-test passed 573 controls, including the poisoned BASH_ENV predecessor negative for each preview lane."
    },
    {
      "id": "SEC-23-21",
      "category": "security",
      "severity": "high",
      "required_property": "The Linux waiter execution environment must be pinned, and no waiter lane may introduce an unreviewed job container or service.",
      "disposition": "fixed",
      "rationale": "At 170b7eb2, a job-level Linux container could set BASH_ENV and shadow python3 while the waiter-step checks still passed. The profile pins the Linux lane to ubuntu-22.04 and rejects container/services keys on all three lanes, with causal negatives for each.",
      "fix_sha": "950c78b0bac936992403511a3cfa41f7cb1069c6",
      "verification_ref": "At 950c78b0bac936992403511a3cfa41f7cb1069c6, exact-source coverage self-test passed 573 controls, workflow-policy ci and ledger groups passed, and independent security/adversarial reviews accepted."
    }
  ]
}
```
<!-- gbb-review-evidence:end -->

## Recovery exact-source security re-review (2026-11-10)

I independently reviewed the exact committed implementation at `10fee4515c9db0e8b259e089ef2ec41f0453b811`, including the delta from the previously reviewed `950c78b0` baseline and the relevant unchanged source-identity, input and release-authority boundaries. D-168 through D-171 introduce bounded self-test reuse, approved scheduling and reader-budget changes, and removal of duplicate feature-branch fixture pushes. Earlier verification observations remain historical evidence.

The candidate-checker worker executes the actual CLI parser and `main()` in a fresh script namespace for each case. Its parent retains the 30-second response deadline and separate 1 MiB captured stdout/stderr limits. The context manager stops the worker before synthetic-directory cleanup, including exception exits. At the reviewed source, I ran the production live-worker refusal and exception-cleanup controls; both passed. Independent stdout and stderr overflow probes each rejected with `candidate-subprocess-output-limit`. A synthetic short-deadline probe rejected with `candidate-subprocess-timeout` and confirmed that the worker had been stopped.

The source-archive worker retains a 90-second call bound and separate 1 MiB captured streams. I ran its production overflow, timeout and subsequent-recovery controls; both controls passed. Its immutable blob cache is scoped to the synthetic test and retains at most 1 MiB per entry and 16 MiB total. Disclosure controls reuse only their private copied inputs and continue launching the actual adoption CLI for each case. Neither change expands publication authority.

The immutable D-170 profile accepts all four 4,800-second readers, the three 90-minute preview caps and candidate-fuzz's 160 attempts, 30-second interval and 142-minute cap. Direct probes rejected the preceding release attempt/deadline/cap values and a 4,500-second waiter in each preview lane. Candidate-fuzz's declared worst-case work remains 8,490 seconds within its 8,520-second job cap. Hosted queue or service delays can still cause closed failures.

D-171 changes only fixture-repro's push branch filter to main; PR and manual dispatch coverage and every job body remain present. I exercised the exact immutable trigger validator: the accepted workflow passed, and unrestricted pushes, missing PR coverage, missing manual dispatch and the wrong push branch each rejected for the trigger diagnostic.

I also executed the exact policy snapshot identity and independent historical AST comparison; both passed. The snapshot re-pin changes no production policy behavior beyond the previously inspected mutation anchors. Existing waiter shell/environment protections remain present. Validation of the preserved 21-finding structured record against the new implementation SHA passed, including fix-commit ancestry.

These were cheap targeted probes against source loaded from the reviewed Git commit. I did not run the full suite, complete workflow self-tests, live hosted checks, publication operations or Windows execution. They remain required qualification evidence and are not implied by this security verdict.

No new correctness or security finding. All 21 existing structured findings retain their provenance. SEC-23-09 remains open, low and nonblocking: the cache bounds retained storage but does not cap every Git-output read before materialization.

## D-172 exact-source security delta review

I independently reviewed the D-172 delta at `b50f0c10e0794591a212edbfd083f10084805532`, following my review of `10fee451`. Only the source-archive self-test implementation and its decision records changed; workflow authority and the previously verified threat dispositions remain unchanged.

The parent and worker each retain at most 8 MiB of blob payloads, preserving the combined 16 MiB budget and 1 MiB entry limit. Keys include the helper-source digest, canonical repository, full commit and path. Symbolic revisions bypass caching, and failed reads cannot populate it. The wrapper changes only immutable blob retrieval during self-testing; actual CLI/main calls, fresh namespaces, archive/policy computation and mutable worktree checks remain.

I ran the production cache identity/resource controls against this exact source. They passed root/revision/path separation, changed checker identity, symbolic-ref bypass, exact capacity, excess capacity and oversized-entry checks. An additional probe confirmed failed reads are retried. A small synthetic probe through the actual worker demonstrated cache reuse across fresh namespaces and refusal to reuse bytes after checker-source changes. Existing worker overflow, timeout and recovery controls also passed.

No new correctness/security issue was found. SEC-23-09 remains open and non-blocking. I did not run the full archive self-test, CTest suite, Windows execution or hosted qualification; those remain separate qualification gates.

## D-173 exact-source security delta review

I independently reviewed the D-173 delta at `33a1e7faf0c4126a4840e3c1c55ee9d1589d2593`. An AST comparison confirmed that executable code outside `controls()` is unchanged. Stage snapshots are finalized before pool submission; each baseline creates private Scenario roots, copied stub state and separate workspaces. The baseline sequence occupies one existing executor slot without increasing its worker ceiling. Its result and every negative-control result remain required for success; executor shutdown waits for submitted work when a failure propagates. Cheap probes using the actual Scenario implementation confirmed unique concurrent roots and isolated state. The exact `controls()` orchestration, exercised with inexpensive case stand-ins, demonstrated overlap, complete success accounting, and propagation of both baseline and negative-control failures. No security or correctness regression was found. These probes do not establish production-suite timing; the affected CTest and remaining qualification gates still require separate evidence.

## D-174 exact-source security delta review

D-174 at `b312148d23993a210e3adbc943882d923eab8f36` retained baselines/bounds and allowed only historical or exact SHA-pinned b50 archive bytes. Probes covered both accepted snapshots, every preserved-path edit, missing/mismatched pins and later edits. No regression; full qualification remained separate.

## D-175 exact-source security delta review

Reviewed `5eefa412e679afe6044e3a80f93a73d269ec0c9d` against accepted `b312148d23993a210e3adbc943882d923eab8f36`. The diff only reserves `phase23_review_evidence_controls` at four slots, mirrors it in `PHASE23_RESERVED_TESTS`, and updates the coverage self-test count from 598 to 599. Its CTest command, assertions, labels, 60-second timeout, global four-worker cap, inventory and merge authority are unchanged. D-175 records the timeout was load-only; isolated runs passed in 35.98 and 22.71 seconds. No new security issue; all 21 structured findings and provenance remain unchanged, including open, low, non-blocking SEC-23-09.
