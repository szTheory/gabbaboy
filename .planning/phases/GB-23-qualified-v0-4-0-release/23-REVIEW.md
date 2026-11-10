# Phase 23 Independent Release / Consumer Review

**Reviewed implementation:** 950c78b0bac936992403511a3cfa41f7cb1069c6
**Review delta:** 029a77f5a87682cee545aa99edc1fe5263e5a77c through 950c78b0bac936992403511a3cfa41f7cb1069c6, with earlier Phase 23 review findings retained
**Role:** release-consumer
**Reviewer:** release-consumer-48d8e501

## Scope and conclusion

I re-reviewed the exact implementation at `950c78b0bac936992403511a3cfa41f7cb1069c6` in `/private/tmp/gabbaboy-phase23.t6o3vA`. The D-163 amendment sets `PROCESSORS=2` for all 200 docs controls, including shard 0 and shards 1–199. Their commands, assertions, `v02` labels, 90-second limits, and global four-worker CTest setting are unchanged. The checker requires exactly two slots and has a former-four-slot negative plus a wrong-label negative for each docs control; the non-doc reservations remain at four slots. D-164 raises only the native macOS job cap to 50 minutes and synchronizes its ledger row; all per-test ceilings and other job caps remain unchanged. The approved Windows support-ledger path correction remains intact. The source delta does not touch release, consumer, package, notice, or version-window implementation. RC-01 through RC-22 retain their identities and fixed dispositions; RC-23 records and closes a source-binding gap in the new timeout control. No finding remains open.

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

<!-- gbb-review-evidence:start -->
```json
{
  "schema_version": 1,
  "report_id": "gb-23-release-consumer-950c78b0-20261110-d167",
  "role": "release-consumer",
  "reviewer_id": "release-consumer-48d8e501",
  "independent": true,
  "reviewed_sha": "950c78b0bac936992403511a3cfa41f7cb1069c6",
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
    }
  ]
}
```
<!-- gbb-review-evidence:end -->
