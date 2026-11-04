# Phase 23 Release-Consumer Review

**Reviewed implementation:** `4c9c54f8b5a33e758624c997f107d1ffdd7c94a0`
**Role:** release-consumer
**Reviewer:** `codex-release-consumer-01`

## Review scope and outcome

I reviewed the immutable implementation at the exact SHA above, including the Plan 23-04 T2 contract and rescope decisions through D-154, Plan 23-09's version-window opener fix, the release workflows and guidance, and the installed/downloaded product and notice verifiers. The previous RC-01–RC-10 dispositions remain fixed at this source. I found no remaining release-consumer correctness or security issue.

The version-PR path keeps normal inactive-window development evaluation separate from the exact tracked `0.4.0` output and release-note checks. The version-PR and release-please jobs use trusted checkers against the PR head. The candidate release workflow binds `v0.4.0` to the returned source SHA, requires an active version window and validated notes, checks merged-PR exact-head evidence and the existing rehearsal, and keeps the candidate as an unpublished draft while it builds and verifies assets. The version-window checker requires the changelog ledger reference to be visible and exact; its incomplete raw-HTML opener cases are rejected through the production CLI while a visible ledger-link counterpart passes. Workflow source is present, but this review does not establish branch-protection configuration or any hosted run result.

The release guidance makes no v0.4.0 publication claim. It preserves the separate Potion Panic and µCity 1.3 source/rights-scope outcomes without asserting a license prohibition, states that neither candidate was built or run and no CGB game was admitted, and distinguishes harness-only RGB555/PCM results from game progress, rendering, physical-hardware, mode-3 timing, perceptual-quality, and general-compatibility claims. It retains the synthetic/metadata-only Phase 22 result, zero real fixtures admitted or executed, and the Pending requirements. It also preserves the established Linux x64, macOS arm64, and Windows x64 core packages and the macOS arm64 player, and states that artifacts are unsigned and not notarized.

The source archive and installed product package remain separate evidence boundaries. Source archives retain admitted licensed fixtures with their notices; product packages are limited to the project-authored tracer, visible demo, and MBC1 continuation fixtures, with policy checks against other fixture ROMs. The trusted release path binds receipts to tag/source/release identity, validates notice sidecars and package contents, downloads and checks the actual archive bytes, and runs C/C++ consumers against the downloaded product. The source-archive receipt is checked separately. These are implemented local contracts, not evidence that v0.4.0 has been built, downloaded, qualified, or published.

The disclosure and notice boundaries remain intact: required clauses and each third-party rights row must be visible prose, and rows remain bound to fixture manifest and license bytes. The unsupported-game claim path operates on code-masked visible prose in the README, game-acceptance guide, other public surfaces, notices, and release notes. D-149–D-153 keep hard breaks, valid entity references, inline and reference link labels, Unicode default-ignorables, and Unicode symbol emphasis visible to that matcher while preserving code masking and safe evidence. D-154 bounds reference-label candidate handling before copying or normalization: paired unescaped nested brackets and spans beyond CommonMark's 999-character label limit are rejected in constant time. Valid shortcut, full, and collapsed links continue to expose only their visible labels; destinations and titles remain excluded. D-152's candidate buckets and D-154's span guard change only checker parsing. Paired unsafe-claim and safe-prose controls cover README, notices, and release notes, including the new symbol and nested-bracket cases; valid docs and notice behavior remains unchanged.

## Verification at the reviewed source

- The production docs check passed with 473 checks. The docs self-test passed with 473 checks and all 255 negative controls rejected, including D-144–D-154 and notice-path controls.
- The release-note self-test passed with 2 positive cases and 72 controls.
- `python3 -I -m py_compile` passed, and the exact-source Phase 1 configure/build passed.
- The Plan 23-09 version-window self-test recorded 63 positives and 66 controls at `a63f1dc67654613e105ac1071b7445f21adea0bc`; the exact reviewed source still contains its production opener controls.
- The direct report gate and focused CTest are pending and are not claimed here.

These local checks establish only the behavior of their specified inputs. They do not establish review quality by themselves or qualify a release. I did not inspect live hosted checks, an actual v0.4.0 version PR, a v0.4.0 tag, downloaded v0.4.0 assets, or a publication. No real game or diagnostic fixture was fetched, built, run, or admitted.

<!-- gbb-review-evidence:start -->
```json
{
  "schema_version": 1,
  "report_id": "gb-23-release-consumer-4c9c54f8-01",
  "role": "release-consumer",
  "reviewer_id": "codex-release-consumer-01",
  "independent": true,
  "reviewed_sha": "4c9c54f8b5a33e758624c997f107d1ffdd7c94a0",
  "findings": [
    {
      "id": "RC-01",
      "category": "correctness",
      "severity": "high",
      "required_property": "The version-PR workflows must validate the exact tracked 0.4.0 output and release-note disclosure against the PR head using trusted verifiers.",
      "disposition": "fixed",
      "rationale": "At the reviewed source, both the direct version-PR gate and the regenerated-version-PR path run the active-window check, the separate --check-tracked --expect-version 0.4.0 assertion, and the release-note validator from the trusted workflow checkout. The release policy self-test also checks these workflow pins and their weakened counterparts.",
      "fix_sha": "9e09eef8b379ca8d329cb13bf354058661296daa",
      "verification_ref": "At 4c9c54f8b5a33e758624c997f107d1ffdd7c94a0: .github/workflows/version-pr-gate.yml:47-55 and .github/workflows/release-please.yml:119-133; verify-v04-release-policy.py --check/--self-test recorded 11 positives and 11 controls at 05a9023bc38d487eca5de8502de4b0708165f0e8."
    },
    {
      "id": "RC-02",
      "category": "correctness",
      "severity": "high",
      "required_property": "A changelog ledger reference must be a visible Markdown link to the exact support ledger; incomplete raw-HTML openers cannot make a hidden link satisfy the contract.",
      "disposition": "fixed",
      "rationale": "The immutable version-window checker masks comments and code, rejects incomplete tag/declaration/processing-instruction openers in the judged changelog prefix, and checks the selected release section for an exact supported ledger destination. Its committed controls test each opener before the heading and inside the section, with visible-link counterparts and the intended window-version-output-mismatch diagnostic.",
      "fix_sha": "a63f1dc67654613e105ac1071b7445f21adea0bc",
      "verification_ref": "At 4c9c54f8b5a33e758624c997f107d1ffdd7c94a0: tests/scripts/verify-version-window.py production incomplete-opener matcher and paired visible-link/hidden-link CLI controls; Plan 23-09 SUMMARY records 63 positives and 66 controls at a63f1dc67654613e105ac1071b7445f21adea0bc."
    },
    {
      "id": "RC-03",
      "category": "correctness",
      "severity": "medium",
      "required_property": "Normal inactive-window development evaluation must pass while exact generated output and release-note requirements remain separately enforced for a version PR.",
      "disposition": "fixed",
      "rationale": "The regenerated-version-PR workflow exits normally when no version PR exists. When one exists, the separate tracked-output and release-note checks still run. This keeps the inactive development record usable without weakening the version PR's exact 0.4.0 requirements.",
      "fix_sha": "9e09eef8b379ca8d329cb13bf354058661296daa",
      "verification_ref": "At 4c9c54f8b5a33e758624c997f107d1ffdd7c94a0: .github/workflows/release-please.yml inactive-window early exit and separate tracked-output/notes checks; the active/inactive version-window and workflow-policy controls are recorded in the Phase 23 release-policy and version-window artifacts."
    },
    {
      "id": "RC-04",
      "category": "correctness",
      "severity": "high",
      "required_property": "Required public support and limitation disclosures must be visible prose; an entire clause hidden in inline code, including clauses containing literal code tokens, cannot satisfy it.",
      "disposition": "fixed",
      "rationale": "The shared visible-phrase checker masks code spans, link titles, image markup, and reference metadata before checking README, game-acceptance, and release-guide clauses. Paired mutations require the expected missing-disclosure diagnostic while the original visible wording passes.",
      "fix_sha": "c4ed9eed86871db9f9dc225565a85a55ab0a8036",
      "verification_ref": "At 4c9c54f8b5a33e758624c997f107d1ffdd7c94a0: tests/scripts/verify-v02-adoption.py shared visible-phrase checker and the README/game-guide/release-guide masking controls; the exact-source docs self-test passed 473 checks with all 255 negative controls rejected."
    },
    {
      "id": "RC-05",
      "category": "correctness",
      "severity": "high",
      "required_property": "Every required third-party attribution and rights statement must appear in visible notice prose and remain bound to the admitted fixture's manifest and license bytes.",
      "disposition": "fixed",
      "rationale": "The notice checker excludes fenced, indented, inline-code, comment, link-title, image, and reference-definition content from proving a rights row. It requires the visible row for each actual fixture and checks the manifest and LICENSE.txt digests against that row. The docs controls hide each of the seven rows separately and require its intended disclosure failure.",
      "fix_sha": "3083aa7184719108c6b8ae4cdca22986329bfea7",
      "verification_ref": "At 4c9c54f8b5a33e758624c997f107d1ffdd7c94a0: check_notices/visible_notice_matches and the seven per-row hide controls in tests/scripts/verify-v02-adoption.py; exact-source docs self-test passed 473 checks with all 255 negative controls rejected."
    },
    {
      "id": "RC-06",
      "category": "correctness",
      "severity": "high",
      "required_property": "Markdown masking must not hide unsupported game claims through the five reviewed interactions: all-whitespace explicit image labels, tab-expanded list continuation, comment-sensitive reference labels, comment-created false fences, or a closing bracket in a URI autolink.",
      "disposition": "fixed",
      "rationale": "The source handles those cases in the bounded Markdown masker and pairs each negative with the valid collapsed-reference, list-continuation, matching-comment, real-fence, or autolink-title counterpart. The production docs self-test rejects the malformed claim cases for their intended diagnostics.",
      "fix_sha": "4bb708fd137f7831b9af720220a09cee57e8d47c",
      "verification_ref": "At 4c9c54f8b5a33e758624c997f107d1ffdd7c94a0: tests/scripts/verify-v02-adoption.py D-144 reference-label/list/comment/autolink controls, including distinct-comment-payload and tab-expanded-list-continuation cases; exact-source docs self-test passed with all 255 negative controls rejected."
    },
    {
      "id": "RC-07",
      "category": "correctness",
      "severity": "high",
      "required_property": "Visible unsupported CGB-game claims must be recognized across literal Cf/default-ignorable characters and valid CommonMark entity and numeric references, while code spans remain non-prose.",
      "disposition": "fixed",
      "rationale": "The matcher uses a frozen Unicode 18.0 default-ignorable table, removes format/default-ignorable characters, and decodes valid CommonMark references after prose masking. This normalization is scoped to this single claim matcher. Controls cover invisible and visible references, encoded CGB text, safe evidence, and code-span behavior.",
      "fix_sha": "fc0ba4ff9626e06e04d8800800561b51414166bf",
      "verification_ref": "At 4c9c54f8b5a33e758624c997f107d1ffdd7c94a0: tests/scripts/verify-v02-adoption.py frozen Unicode 18.0 table, visible-reference decoder, and paired README/release-note controls; exact-source docs self-test passed with all 255 negative controls rejected."
    },
    {
      "id": "RC-08",
      "category": "correctness",
      "severity": "high",
      "required_property": "Unsupported CGB-game claims rendered across a backslash hard line break must be detected in all public docs, third-party notices, and managed release notes, after code masking.",
      "disposition": "fixed",
      "rationale": "The matcher turns odd runs of backslashes immediately before LF, CR, or CRLF into whitespace. README, game-acceptance, public-surface, notice, and release-note callers supply an uncollapsed code-masked visible copy. Controls cover all three endings, a following encoded space, a soft break, safe text, and inline/fenced code.",
      "fix_sha": "e26757fafc818a92ddf7ca45f1a409658a5a5bdd",
      "verification_ref": "At 4c9c54f8b5a33e758624c997f107d1ffdd7c94a0: COMMONMARK_HARD_LINE_BREAK/unsupported_game_claim_match and the uncollapsed, code-masked check_notices caller; exact-source docs controls cover LF, CR, CRLF, encoded space, soft-break and code counterparts, and passed with all 255 negative controls rejected."
    },
    {
      "id": "RC-09",
      "category": "correctness",
      "severity": "high",
      "required_property": "Visible unsupported CGB-game claims cannot evade matching through CommonMark emphasis delimiters or an inline link label, and claim text in link destinations/titles or code remains non-prose.",
      "disposition": "fixed",
      "rationale": "The matcher removes paired CommonMark emphasis markers and exposes inline-link label text only on the unsupported-game-claim path. Production callers first mask code, and the link masker omits destination/title content. Paired controls cover strong and intraword emphasis, underscore emphasis, a split inline-link label, and the accepted escaped, intraword-underscore, destination-only, code-span, and fenced-code counterparts.",
      "fix_sha": "e017078b72e78b38fb596faced3af3e35c2ca0ce",
      "verification_ref": "At 4c9c54f8b5a33e758624c997f107d1ffdd7c94a0: normalize_commonmark_emphasis and D-150/D-153 paired docs, notice and release-note controls; source applies CommonMark punctuation/symbol flanking only in the unsupported-game matcher. Exact-source docs self-test passed with all 255 negative controls rejected; release-note self-test passed 2 positives and 72 controls."
    },
    {
      "id": "RC-10",
      "category": "correctness",
      "severity": "high",
      "required_property": "Visible unsupported CGB-game claims split across valid shortcut, full, or collapsed CommonMark reference-link labels must be detected, while destinations, titles, unresolved labels, escaped brackets, and code remain non-prose.",
      "disposition": "fixed",
      "rationale": "Production callers build a code-masked visible claim copy with render_link_labels enabled. Valid shortcut, full, and collapsed references are reduced to their rendered label text before claim matching; reference suffixes, destinations, and titles are excluded. The D-151 controls exercise all three forms in docs, release notes, and notices, with accepted unresolved/escaped labels, destination/title-only claims, and code examples. The production docs path also rejects the nested-link probe: its caller renders valid link labels before invoking the claim matcher.",
      "fix_sha": "b798781105b8f6f803e85aa2ad766d2b2fdbec22",
      "verification_ref": "At 4c9c54f8b5a33e758624c997f107d1ffdd7c94a0: prose(..., render_link_labels=True), unsupported_game_claim_match, check_notices, and shortcut/full/collapsed reference-link controls; exact-source docs self-test passed with all 255 negative controls rejected and release-note self-test passed 2 positives and 72 controls."
    },
    {
      "id": "RC-11",
      "category": "security",
      "severity": "high",
      "required_property": "Attacker-controlled unmatched CommonMark emphasis runs must not cause quadratic rescanning in the public documentation checker, while paired emphasis and rule-of-three matching remain correct for docs, notices, and release notes.",
      "disposition": "fixed",
      "rationale": "D-152 replaces repeated backward opener scans with per-marker candidate buckets indexed by opener role and original delimiter-length modulo. The fixed number of candidate buckets is checked per closing run, and consumed candidates are removed from their stack. The change is confined to unsupported-game claim normalization. Dense unmatched-marker claim controls reject through README, notices, and release notes; paired dense safe-prose controls remain accepted. The current D-153 symbol tests and the earlier star/underscore/escape/code controls also remain present.",
      "fix_sha": "6876fab06bf746fdaab67beaa4d52a6b1c70ac06",
      "verification_ref": "At 4c9c54f8b5a33e758624c997f107d1ffdd7c94a0: tests/scripts/verify-v02-adoption.py normalize_commonmark_emphasis candidate buckets and DENSE_UNMATCHED_EMPHASIS_GAME_CLAIM controls in README, check_notices, and run_self_test_release_notes; exact-source docs self-test passed 473 checks with all 255 negative controls rejected, and release-note self-test passed 2 positives and 72 controls. No timing or size quota is used as proof."
    },
    {
      "id": "RC-12",
      "category": "correctness",
      "severity": "high",
      "required_property": "Visible unsupported CGB-game claims with a Unicode symbol immediately before an emphasis delimiter must be recognized according to CommonMark flanking rules, while safe symbol-emphasized prose stays accepted.",
      "disposition": "fixed",
      "rationale": "D-153 treats both Unicode punctuation and symbol categories as punctuation when computing emphasis flanking, only in the unsupported-game matcher. Paired controls cover strong underscore with a leading emoji, the rule-of-three case with a leading emoji, and safe symbol-emphasized evidence across README, notices, and release notes.",
      "fix_sha": "4c9c54f8b5a33e758624c997f107d1ffdd7c94a0",
      "verification_ref": "At 4c9c54f8b5a33e758624c997f107d1ffdd7c94a0: normalize_commonmark_emphasis uses Unicode categories P and S; COMMONMARK_EMPHASIS_GAME_CLAIMS and the paired Unicode-symbol safe-prose controls exercise README, notice and release-note production paths. Exact-source docs self-test passed 473 checks with all 255 negative controls rejected; release-note self-test passed 2 positives and 72 controls."
    },
    {
      "id": "RC-13",
      "category": "security",
      "severity": "high",
      "required_property": "Reference-label candidates must be rejected in constant time when they contain paired unescaped nested brackets or exceed the CommonMark 999-character limit, so malformed documentation cannot trigger repeated label copying and normalization; valid reference links and visible claim detection must remain unchanged.",
      "disposition": "fixed",
      "rationale": "D-154 builds a prefix count over paired unescaped opening brackets and uses that count plus the label-length bound before copying or normalizing any candidate. Valid shortcut, full, and collapsed references still resolve through the same normalized labels. Paired dense nested-bracket game-claim and safe-prose controls exercise docs, notices, and release notes.",
      "fix_sha": "4c9c54f8b5a33e758624c997f107d1ffdd7c94a0",
      "verification_ref": "At 4c9c54f8b5a33e758624c997f107d1ffdd7c94a0: tests/scripts/verify-v02-adoption.py normalized_reference_label_span checks the span bound and paired-opening prefix before joining label text, with call sites for image, full/collapsed, and shortcut references; D-154 dense game-claim/safe-prose controls cover README, check_notices and release notes. Exact-source docs self-test passed 473 checks with all 255 negative controls rejected; release-note self-test passed 2 positives and 72 controls."
    }
  ]
}
```
<!-- gbb-review-evidence:end -->
