# Phase 23 Release-Consumer Review

**Reviewed implementation:** 7c6f01ad5ecf3b6736bf694324acc1671d9e20cc
**Role:** release-consumer
**Reviewer:** release-consumer-d068

## Scope and conclusion

I verified that the shared checkout is at the exact implementation commit, 7c6f01ad5ecf3b6736bf694324acc1671d9e20cc. I rechecked Plan 23-04, the T2 rescope, timeout-budget mapping, and the final implementation delta from bd5ab993a3f09307e6a5ef31185f554740a0787b. That delta changes only DECISIONS.md, the Phase 23 plan and rescope, and the timeout-budget allowlist; release, lifecycle, version-window, product/consumer, fixture, and notice implementation files are unchanged. I re-evaluated those exact source paths alongside the previously approved D-144–D-156 work.

The source satisfies RC-01–RC-15. The D-155 adoption-checker blob at this commit is identical to the blob at 9166ab60d25c6d246761b4aa33a0ceb35dd83f5c. D-156 points the post-tag recovery verifier at that exact checker and retains its immutable-source byte comparisons. The final D-068 mapping correction resolves RC-16: the Plan 23-04 pinned check and PR-base budget check both pass, and all shard rows resolve their decision references. I found no remaining open correctness or security issue in this review scope.

The version-PR gate reads generated content as data and runs trusted checkers from the PR base against the exact version-PR head. It checks the active content window, exact tracked 0.4.0 version, and rendered notes. The version-window checker masks comments and code, rejects raw HTML constructs in the judged changelog prefix, and requires a visible exact ledger link. Its controls cover incomplete HTML openers both before the version heading and inside the selected section, with visible-link counterparts and a causal comparison against the prior matcher.

The release lifecycle binds the tag to release-please's source SHA and version, requires a single unpublished draft, and downloads named assets for validation by trusted workflow code. Publication requires successful platform candidate jobs, downloaded-byte product checks, final receipt/API checks, and the exact-tree nightly gate. Release guidance remains explicit that v0.4.0 is preparation only, that the reviewed game candidates were neither built nor run, and that the current harness and software-model evidence do not establish game compatibility, physical hardware behavior, or perceptual output. The product policy keeps source archives with admitted notices distinct from binary packages with only the approved authored fixtures. Installed and downloaded consumer evidence remains separate.

The D-155 notice checker strictly resolves fixture paths, rejects traversal/backslashes, checks the resolved file stays within the repository root, and confines self-test copy destinations before and after parent-directory creation. The existing controls cover traversal, source symlinks, and a symlinked fixture destination. The claim matcher remains limited to unsupported CGB-game claims after Markdown code masking; I reread its D-144 parser cases, D-145–D-149 invisible/reference/hard-break handling, D-150–D-153 emphasis and link-label behavior, and D-154 bounded label-span checks. The focused selector still uses [0-9]+; CMake registers 200 shards, and the immutable inventory and budget cover every added shard 01–199.

At 7c6f01ad5ecf3b6736bf694324acc1671d9e20cc, RECOVERY_ADOPTION_PIN_SHA remains 9166ab60d25c6d246761b4aa33a0ceb35dd83f5c. The post-tag recovery control reads the adoption checker at the requested implementation revision and the pinned revision, then checks both against the working-tree bytes. This is the intended source binding; its targeted control passes at the reviewed commit.

The final timeout-budget mapping is coherent with both immutable checker bases. Shards 01–31 cite D-069; shards 32–199 cite D-068. D-068 and D-069 are present in the plan-pinned base f2b05c9fb3ba314cfe46959b64073ce9441724ca and the PR base 1ab65414d60828fa9505babeaeea9de0571f016c. The D-068 note documents all-build-leg inventory provenance for the new rows, while D-069 remains the governing timeout policy. The current checker passes the exact Plan 23-04 command against f2b, and the checker copied from the immutable PR base passes against that base. This closes the prior RC-16 finding.

## Verification at the reviewed source

- `python3 -I tests/scripts/verify-release-lifecycle.py --rev 7c6f01ad5ecf3b6736bf694324acc1671d9e20cc --self-test-post-tag-recovery` passed with 99 controls and 12 positives.
- `python3 -I tests/scripts/verify-v02-adoption.py --self-test docs --shard 0 200` passed with 4 selected CLI calls, 473 checks, and two selected negative controls rejected. This is shard 0 only; I did not run the complete 200-shard selection.
- The Plan 23-04 pinned command, `python3 -I tests/scripts/verify-test-budget.py --build-dir build --base f2b05c9fb3ba314cfe46959b64073ce9441724ca --repo .`, passed at the exact implementation checkout: 1,936 registered tests and 288 allowlisted rows.
- The checker copied from PR base `1ab65414d60828fa9505babeaeea9de0571f016c` also passed when run against that base on the reviewed source, as confirmed by the orchestrator's bounded check. The CI workflow uses this immutable-base checker pattern.
- The exact source inventory contains 199 rows for shards 01–199: 31 cite D-069 and 168 cite D-068. The focused selector includes the full numbered shard range.
- I did not run the full CTest suite, hosted checks, or any live version PR/tag/download/publication workflow. These controls establish the scoped source and budget contracts; they do not claim release qualification or game compatibility.

The previous base-reference failure is resolved by the approved D-068 mapping. No open correctness/security finding remains in this release-consumer review.

<!-- gbb-review-evidence:start -->
```json
{
  "schema_version": 1,
  "report_id": "gb-23-release-consumer-7c6f01ad-20261106-01",
  "role": "release-consumer",
  "reviewer_id": "release-consumer-d068",
  "independent": true,
  "reviewed_sha": "7c6f01ad5ecf3b6736bf694324acc1671d9e20cc",
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
      "verification_ref": "At the reviewed source, the D-155 adoption checker blob is unchanged from 9166ab60d25c6d246761b4aa33a0ceb35dd83f5c; its shard-0 self-test passed with the D-155 path controls."
    },
    {
      "id": "RC-15",
      "category": "correctness",
      "severity": "high",
      "required_property": "The post-tag recovery control pins and byte-compares the exact reviewed adoption checker while preserving the original historical recovery source pin.",
      "disposition": "fixed",
      "rationale": "D-156 updates only RECOVERY_ADOPTION_PIN_SHA to the D-155 implementation source. The checker still compares bytes from the requested revision, the immutable pin, and the working tree; the recovery control passes at this revision.",
      "fix_sha": "bd5ab993a3f09307e6a5ef31185f554740a0787b",
      "verification_ref": "At 7c6f01ad5ecf3b6736bf694324acc1671d9e20cc: python3 -I tests/scripts/verify-release-lifecycle.py --rev 7c6f01ad5ecf3b6736bf694324acc1671d9e20cc --self-test-post-tag-recovery passed with 99 controls and 12 positives."
    },
    {
      "id": "RC-16",
      "category": "correctness",
      "severity": "high",
      "required_property": "Timeout-budget rows must cite a decision present in the plan-pinned and PR-base commits used by the immutable checker, while retaining documented timeout policy and shard-inventory provenance.",
      "disposition": "fixed",
      "rationale": "The corrected inventory maps shards 01–31 to D-069 and 32–199 to D-068. Both decisions exist in the plan-pinned f2b base and PR base 1ab65414; D-068 records the all-build-leg inventory provenance and D-069 remains the timeout policy. The exact plan command and PR-base checker both pass against the reviewed source.",
      "fix_sha": "7c6f01ad5ecf3b6736bf694324acc1671d9e20cc",
      "verification_ref": "At 7c6f01ad5ecf3b6736bf694324acc1671d9e20cc, the plan-pinned current checker passed with tests=1936 and allowlisted=288. The checker copied from PR base 1ab65414d60828fa9505babeaeea9de0571f016c also passed against that base. Exact inventory: 199 shard rows, 31 D-069 and 168 D-068; .github/workflows/ci.yml uses the checker copied from BUDGET_BASE."
    }
  ]
}
```
<!-- gbb-review-evidence:end -->
