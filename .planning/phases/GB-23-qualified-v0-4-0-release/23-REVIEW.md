# Phase 23 Release-Consumer Review

**Reviewed implementation:** b75ecb97d8ab11cda5dcb3cc94a87363e60f0cae
**Role:** release-consumer
**Reviewer:** release-consumer-d157b75

## Scope and conclusion

I verified the checkout at the exact implementation commit, b75ecb97d8ab11cda5dcb3cc94a87363e60f0cae. I reviewed the complete source delta since 7c6f01ad, including D-157's CI trigger and measured timeout changes, exact-head preview waits, four-slot CTest reservations, Windows path normalization, and the final workflow-policy coverage snapshot correction. The final follow-up changes the planning-label path checks and adds POSIX-simulated Windows case controls; it also updates the CMake-floor timeout comment. Release, lifecycle, version-window, product/consumer, fixture, notice, and adoption implementation paths remain unchanged from the prior exact-source review. RC-01 through RC-17 remain fixed.

RC-18 and RC-19 are fixed at b75ecb97. The floor-job comment now says the current 50-minute cap. The planning-label checker normalizes both configured repository and output paths, and the 33-control self-test passes on POSIX with simulated Windows casing for the renderer output, renderer repository, and review-evidence repository paths. I found no remaining correctness, security, high, critical, or blocking finding.

The version-PR gate reads generated content as data and runs trusted checkers from the PR base against the exact version-PR head. It checks the active content window, exact tracked 0.4.0 version, and rendered notes. The version-window checker masks comments and code, rejects raw HTML constructs in the judged changelog prefix, and requires a visible exact ledger link. Its controls cover incomplete HTML openers both before the version heading and inside the selected section, with visible-link counterparts and a causal comparison against the prior matcher.

The release lifecycle binds the tag to release-please's source SHA and version, requires a single unpublished draft, and downloads named assets for validation by trusted workflow code. Publication requires successful platform candidate jobs, downloaded-byte product checks, final receipt/API checks, and the exact-tree nightly gate. Release guidance remains explicit that v0.4.0 is preparation only, that the reviewed game candidates were neither built nor run, and that the current harness and software-model evidence do not establish game compatibility, physical hardware behavior, or perceptual output. The product policy keeps source archives with admitted notices distinct from binary packages with only the approved authored fixtures. Installed and downloaded consumer evidence remains separate.

The D-155 notice checker strictly resolves fixture paths, rejects traversal/backslashes, checks the resolved file stays within the repository root, and confines self-test copy destinations before and after parent-directory creation. The existing controls cover traversal, source symlinks, and a symlinked fixture destination. The claim matcher remains limited to unsupported CGB-game claims after Markdown code masking; I reread its D-144 parser cases, D-145–D-149 invisible/reference/hard-break handling, D-150–D-153 emphasis and link-label behavior, and D-154 bounded label-span checks. The focused selector still uses [0-9]+; CMake registers 200 shards, and the immutable inventory and budget cover every added shard 01–199.

At b75ecb97d8ab11cda5dcb3cc94a87363e60f0cae, RECOVERY_ADOPTION_PIN_SHA remains 9166ab60d25c6d246761b4aa33a0ceb35dd83f5c. The post-tag recovery control reads the adoption checker at the requested implementation revision and the pinned revision, then checks both against the working-tree bytes. This is the intended source binding; its targeted control passes at the reviewed commit.

The final timeout-budget mapping is coherent with both immutable checker bases. Shards 01–31 cite D-069; shards 32–199 cite D-068. D-068 and D-069 are present in the plan-pinned base f2b05c9fb3ba314cfe46959b64073ce9441724ca and the PR base 1ab65414d60828fa9505babeaeea9de0571f016c. The D-068 note documents all-build-leg inventory provenance for the new rows, while D-069 remains the governing timeout policy. The current checker passes the exact Plan 23-04 command against f2b, and the checker copied from the immutable PR base passes against that base. This closes the prior RC-16 finding.

The CI workflow retains its pull-request update trigger and runs branch-push CI only for `main`; the policy check accepts that exact trigger shape and its CI controls reject an unfiltered push. The native Linux and Windows job limits are 60 minutes, the CMake-floor limit is 50, and the three preview waiters use a 3,900-second exact-head deadline with 75-minute job limits. Historical p50 citations remain unchanged, with disclosures explaining changed job bodies and observed Phase 23 run caps. The four near-limit CTest controls reserve `PROCESSORS 4`; an exact-source CMake configure confirms their original 60/90-second timeouts. The floor comment matches its 50-minute cap.

The planning-label checker now normalizes the `--repo` and `--output` path arguments using Windows host rules, and `configured_source_revision` applies the same comparison to its `--repo` argument. It retains executable identity checks through `samefile`, wrong-repository and fake-CMake negatives, and adds case-variant positives for these paths. The POSIX self-test simulates Windows case-insensitive comparisons for renderer output, renderer repository, and review-evidence repository paths; all 33 controls pass.

The final workflow-policy coverage fix pins the judged policy checker to its exact D-157 source commit, adds only the changed policy functions to the reviewed-function set, and continues comparing the rest of the checker against its immutable baseline. This closes the previously observed exact-source coverage failure without bypassing the coverage inventory or mutation controls.

## Verification at the reviewed source

- `python3 -I tests/scripts/verify-workflow-policy-coverage.py --check --root . --build-dir /private/tmp/gabbaboy-review-b75 --rev b75ecb97d8ab11cda5dcb3cc94a87363e60f0cae` passed with 540 controls across six groups on POSIX. Its self-test passed 94 controls.
- `python3 -I .github/scripts/verify-workflow-policy.py --check --root .` passed. The CI policy group completed 112 controls and the timeout-ledger group completed 20 controls; the ledger controls reject stale values, ratio violations, and a required-matrix p50 above its ceiling.
- `python3 -I tests/scripts/verify-planning-labels.py --self-test` passed 33 controls. This POSIX run simulated case-insensitive Windows paths for renderer output, renderer repository, and review-evidence repository arguments. A fresh CMake configure at the reviewed SHA confirmed all four reserved tests use `PROCESSORS=4` and retain their original timeouts.
- The plan-pinned budget check and the checker copied from PR base `1ab65414d60828fa9505babeaeea9de0571f016c` both passed with 1,936 tests and 288 allowlisted rows.
- The docs shard-0 self-test passed with 4 selected calls, 473 checks, and two negative controls rejected. The post-tag recovery control passed with 99 controls and 12 positives.
- I did not run the full CTest suite or hosted qualification. Local checks do not establish the Windows hosted context or release qualification.

<!-- gbb-review-evidence:start -->
```json
{
  "schema_version": 1,
  "report_id": "gb-23-release-consumer-b75ecb97-20261108-01",
  "role": "release-consumer",
  "reviewer_id": "release-consumer-d157b75",
  "independent": true,
  "reviewed_sha": "b75ecb97d8ab11cda5dcb3cc94a87363e60f0cae",
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
    }
  ]
}
```
<!-- gbb-review-evidence:end -->
