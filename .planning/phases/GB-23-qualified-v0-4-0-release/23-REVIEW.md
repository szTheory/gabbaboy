# Phase 23 Release-Consumer Review

**Reviewed implementation:** 9166ab60d25c6d246761b4aa33a0ceb35dd83f5c
**Role:** release-consumer
**Reviewer:** release-consumer-d155

## Scope and conclusion

I reviewed the implementation from an isolated archive of the full reviewed commit and confirmed the shared checkout was at the same SHA before editing this report. I read the Phase 23 Plan 23-04 report contract, the D-144–D-155 rescope record, the release guidance, version-window checker and controls, trusted version/release workflows, installed-consumer and fixture-product policies, notice checker, and the exact D-155 source diff. The assigned scope is release provenance, version-window and lifecycle behavior, product/consumer boundaries, and notices.

The existing RC-01–RC-13 properties remain satisfied at this source. Their recorded fix commits are ancestors of the reviewed commit, and I verified the corresponding current source paths and controls. D-155's traversal and symlink boundaries are fixed in the reviewed source and have a focused passing control run recorded below. I found no remaining release-consumer correctness or security issue.

The version-PR workflows run the window, exact tracked 0.4.0 version, and release-note checks from the trusted base checkout while reading the generated version PR as data. The active window binds the main base, source, managed notes/ledger, generated PR body, and rehearsal identities. It is content-bound rather than time-bound; a changed source or regenerated content keeps the release held until exact-head checks and rehearsal are repeated. Plan 23-09's production version-window checker masks comments and code before checking the judged changelog, rejects raw HTML openers (including incomplete script/pre/style, doctype, and processing-instruction forms) before the version heading and within the selected release section, then requires the visible exact ledger link. Its self-test has visible-link counterparts, causal incomplete-opener cases, and a control showing the former matcher would accept the hidden-link fixture.

The candidate lifecycle keeps the tag and source SHA equal, checks the version from that exact source, requires one unpublished draft, downloads uniquely named assets, and judges the bytes with trusted checkers from the workflow revision. Publication depends on successful candidate jobs, downloaded product validation, final API/receipt checks, and the exact-tree nightly gate. Release guidance accurately says v0.4.0 is preparation only; no publication, game admission, game execution, signing, or notarization is claimed. It preserves the documented fixture-rights scope outcomes without claiming a license prohibition and distinguishes harness-only RGB555/PCM repeatability from gameplay, rendering accuracy, physical hardware, or broad compatibility.

Product and consumer boundaries remain separate. Source archives may include admitted, noticed test fixtures; binary products are checked against the pinned product policy and contain only the approved project-authored tracer, visible demo, and MBC1 continuation fixtures. The downloaded product archive is validated by the trusted workflow before consumers run against it; receipts bind the archive bytes, source, and build evidence. The installed-prefix path and downloaded-asset path are described as separate evidence. None of these source contracts establishes that v0.4.0 has actually been built, downloaded, qualified, or published.

For notices, D-155 now rejects traversal components and backslashes before path use, resolves source files strictly, and confirms the resolved target remains inside the repository root. The notice lookup is constrained to fixture paths and regular files, including symlink resolution. Self-test copies resolve destinations against their isolated root and check confinement before and after parent-directory creation. The controls exercise traversal and external symlink paths for notice inputs and a symlinked fixture directory for copy destinations; the ordinary in-root notice inputs remain the accepted counterpart. The release-note and documentation claim matcher remains separate from this path policy, and its D-144–D-154 normalization remains limited to unsupported CGB-game claims after code masking.

The focused Plan 23-04 selector now uses phase23_docs_controls_shard_[0-9]+. CMake generates shard 0/200 under the existing v02_adoption_docs_controls name and shards 1–199 in the phase23_docs_controls_shard_* family. I checked that the immutable test inventory and budget each contain exactly the 199 added shard names 01–199, including 100–199. This corrects the previous two-digit selector without changing CTest registration or dropping controls.

## Verification at the reviewed source

- The source review was bound to 9166ab60d25c6d246761b4aa33a0ceb35dd83f5c. The previously committed report in this path named a stale SHA; this report replaces it rather than preserving its structured evidence.
- I ran python3 -I tests/scripts/verify-v02-adoption.py --self-test docs --shard 0 200 at the reviewed checkout. It passed with shard 0/200, selected=4, checks=473, and two selected CLI negative controls rejected. The shard-0 path also executes the notice traversal, external notice symlink, source-copy traversal, and destination-symlink checks; those paths completed without a control failure.
- The focused selector, generated shard range, test inventory, and timeout-budget entries were source-inspected. I did not run the complete 200-shard CTest selection or the full suite in this review. I did not inspect live hosted checks, branch protection, a v0.4.0 version PR, tag, downloaded release assets, or publication.

These checks support the source-level review and the shard-0 controls only. They do not qualify a release or establish live release evidence.

<!-- gbb-review-evidence:start -->
```json
{
  "schema_version": 1,
  "report_id": "gb-23-release-consumer-9166ab60-20261106-01",
  "role": "release-consumer",
  "reviewer_id": "release-consumer-d155",
  "independent": true,
  "reviewed_sha": "9166ab60d25c6d246761b4aa33a0ceb35dd83f5c",
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
      "verification_ref": "At the reviewed source, python3 -I tests/scripts/verify-v02-adoption.py --self-test docs --shard 0 200 passed. This shard exercises notice traversal/symlink and copy-source/copy-destination path controls."
    }
  ]
}
```
<!-- gbb-review-evidence:end -->
