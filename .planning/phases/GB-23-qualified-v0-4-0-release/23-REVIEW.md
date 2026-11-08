# Phase 23 Independent Release / Consumer Review

**Reviewed implementation:** 8f6f7cf3184828b1d0aa9d50528a8fa029b1ced6
**Review delta:** f833e181 through 8f6f7cf3184828b1d0aa9d50528a8fa029b1ced6, with prior D-157 through D-159 review evidence retained
**Role:** release-consumer
**Reviewer:** release-consumer-d160-8f6f7cf3

## Scope and conclusion

I reviewed D-160's nine CTest reservation changes, the source-bound workflow-policy coverage update, and the follow-up that corrects platform scoping and host signal processor counts. The nine D-160 controls reserve four slots while retaining their original assertions and timeouts. RC-01 through RC-20 retain their identities and fixed dispositions; each recorded fix SHA is an ancestor of the reviewed source.

The earlier D-160 reservation checker was corrected before this review: the host helper again assigns two slots to `host_signal_term`, `host_signal_int`, and `host_signal_inherited_ign`, while `host_exit_crash_storm` has an explicit four-slot override. The Windows checker path excludes the two POSIX-only reserved registrations, `host_exit_crash_storm` and `save_format_controls`, and its self-test accepts their absence while rejecting a missing cross-platform reservation and an unexpected POSIX-only registration. The exact-source coverage checks pass. I found no remaining correctness, security, high, critical, or blocking finding.

## D-160 source and verification

The D-160 CMake delta adds docs shards 112, 115, 118, 119, and 122 to the existing four-slot slow-shard group; adds `PROCESSORS 4` to `v02_fuzz_controls`, `v03_dispositions_controls`, and `save_format_controls`; and explicitly reserves all four slots for `host_exit_crash_storm`. Their existing timeouts remain 90 seconds for the five docs shards, 180 for fuzz controls, and 60 for the remaining controls. The diff changes CTest scheduling only; commands and assertions are unchanged.

The host helper continues to apply `PROCESSORS 2` to the three sibling signal tests. Only the crash-storm test receives a subsequent `PROCESSORS 4` override. The configured CTest JSON confirms the three siblings remain at two slots and 60 seconds, while `host_exit_crash_storm` has four slots and a 60-second timeout.

The workflow-policy checker includes all nine reservations in its exact inventory and registration checks and requires `PROCESSORS=4`. Its self-test has a three-slot negative mutation for each reservation. For Windows it removes the POSIX-only crash-storm and save-format controls from the configured-test fixture, accepts that inventory, rejects a missing cross-platform reservation, and rejects an unexpected POSIX-only registration. The self-test passes 118 controls.

A fresh normal configure at the reviewed source passed `verify-workflow-policy-coverage.py --check` with 540 controls across six groups. The registered workflow-policy coverage check and its self-test passed 2/2. Configured CTest properties confirm all nine D-160 reservations have four slots and their existing timeouts. I did not run the full suite or a Windows hosted job; the Windows inventory cases are exercised by the source checker self-test, and the orchestrator owns final qualification.

## Prior release and consumer findings

RC-01 through RC-19 retain their recorded identities, fixed dispositions, fix SHAs, and source-linked verification references. RC-20 remains fixed at d0fb with current checker evidence recorded in its verification reference. All fixed SHAs resolve and are ancestors of this implementation.

The release/version-window, lifecycle, product/consumer, fixture, notice-path, adoption matcher, and planning-label implementations reviewed previously are unchanged by the f833-to-current source delta. D-160 changes test scheduling and its coverage contract only.
<!-- gbb-review-evidence:start -->
```json
{
  "schema_version": 1,
  "report_id": "gb-23-release-consumer-8f6f7cf3-20261108-01",
  "role": "release-consumer",
  "reviewer_id": "release-consumer-d160-8f6f7cf3",
  "independent": true,
  "reviewed_sha": "8f6f7cf3184828b1d0aa9d50528a8fa029b1ced6",
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
      "rationale": "The corrected inventory maps shards 01\u201331 to D-069 and 32\u2013199 to D-068. Both decisions exist in the plan-pinned f2b base and PR base 1ab65414; D-068 records the all-build-leg inventory provenance and D-069 remains the timeout policy. The exact plan command and PR-base checker both pass against the reviewed source.",
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
      "verification_ref": "At b75ecb97d8ab11cda5dcb3cc94a87363e60f0cae, a fresh configure-bound workflow_policy_coverage check passed with 540 controls across six groups; its self-test passed 94 controls. The exact D-157 policy snapshot remains pinned to 013703528fcba6bce371887d5e6dec757e103ecf."
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
      "verification_ref": "At 8f6f7cf3184828b1d0aa9d50528a8fa029b1ced6: exact workflow-policy coverage check passed with 540 controls across six groups; coverage self-test passed 118 controls, including the real support-ledger environment/labels, timeout scaling, and processor negatives. The two coverage CTests passed. The d0fb68361f3ffd82e1205e16609f644d4f733df2 fix remains an ancestor and its configured support-ledger contract is included in the current checker."
    }
  ]
}
```
<!-- gbb-review-evidence:end -->
