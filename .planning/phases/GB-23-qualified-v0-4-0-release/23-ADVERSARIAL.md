# Phase 23 Adversarial Review

**Reviewed implementation:** `9166ab60d25c6d246761b4aa33a0ceb35dd83f5c`
**Role:** adversarial
**Reviewer:** `adversarial-d155`
**Review posture:** I inspected the exact immutable commit in a clean detached checkout, including the Plan 23-04 and D-155 diffs, the execution contract, the notice checker and its controls, the focused CTest selector, and the source-bound release/profile/version controls. I did not use the concurrently modified working tree as implementation evidence.

## Result

The D-155 notice-path and focused-selector defects are fixed at the reviewed commit. I found no additional correctness or security issue in the reviewed T2 scope. Historical findings ADV-01 through ADV-20 remain fixed in ancestor commits and are re-evaluated below. ADV-21 and ADV-22 record the two D-155 defects and their exact-source fixes.

The production Markdown claim matcher and D-144 through D-154 parser logic are unchanged in the diff from the previous reviewed implementation. The current diff adds path confinement, the matching traversal/symlink controls, 200-way test sharding, and the focused-selector correction. I reran focused shards and the release/profile/disclosure/version/evidence controls; I did not repeat the already completed long unsharded docs self-test.

## D-155 path and selector attacks

The old notice checker joined inline notice paths to the repository root without checking the resolved path, and `copy_inputs()` repeated that relative path below its temporary target. The reviewed source now rejects empty, dot, parent, absolute, and backslash path components; resolves source paths and checks that they remain under the resolved repository root; and resolves destination paths both before and after creating parent directories. Notice digests must use a relative path below `fixtures/`. Fixture inventory manifests and license files receive the same source-root check.

I tested the production notice checker in a minimal temporary tree containing only its notice, manifests, licenses, and named digest inputs. The unmodified notice passed with 112 checks; an additional digest for an ordinary in-root license passed with 113 checks. A `fixtures/../../outside.txt` input and an in-root symlink to an external file both rejected with `notice-path-outside-root`. A normal `copy_inputs()` call copied its selected inputs. A target whose `fixtures` directory was a symlink to an external directory rejected with `self-test-copy-path-outside-root`, and the external directory remained empty. The exact-source shard-0 self-test also exercises notice traversal, a notice symlink, copy-source traversal, and a copy-target symlink; its selected production CLI baseline and negative cases passed.

The old Plan 23-04 selector used `[0-9]{2}`, which omitted shard numbers 100–199. The reviewed selector uses `[0-9]+`. An isolated CTest project using the exact Plan selector selected all 200 intended entries (the separate shard-zero test plus numbered shards 1–199), including shards 100 and 199. CMake's registration loop covers 1–199, and each corresponding test appears exactly once in the expected inventory and the D-069 90-second budget allowlist. I also ran shard `199/200`; it passed with two selected child checks, one positive and one negative.

These controls are causal. The production docs controls require the exact path-confinement diagnostic. The copy controls verify the outside destination does not appear and that a target symlink cannot receive copied files. The direct comparison against the parent source shows these checks guard the previous unchecked `root / path` and `target / relative` joins.

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

For each direct release-note mutation, the test helper first accepts the valid renderer-built baseline, then requires the mutant to fail for its expected reason. The immutable profile, version-window, disclosure, and review-evidence suites also pair accepted records with targeted rejected mutations. No real game or diagnostic fixture was fetched, built, run, or admitted; no release was signed, published, or promoted. REL-01 remains Pending.

## Verification evidence

All commands below ran against the clean checkout at the reviewed SHA. Python 3.13 was used for the complete control scripts because the system `python3` is 3.9; the configured Phase 23 build selects Python 3.14.

- `verify-v02-adoption.py --self-test docs --repo . --root . --shard 0 200`: passed; shard `0/200`, four selected child checks, 473 reported checker checks, two selected negative CLI controls rejected. The shard also ran D-155's source-copy and destination-symlink assertions.
- `verify-v02-adoption.py --self-test docs --repo . --root . --shard 199 200`: passed; shard `199/200`, two selected child checks, one selected negative control rejected.
- Direct `check_notices()` path probes: baseline and added in-root path passed; traversal and external symlink rejected with `notice-path-outside-root`.
- Direct `copy_inputs()` path probes: ordinary copy passed; destination symlink rejected with `self-test-copy-path-outside-root`, with zero writes in the external directory.
- Exact Plan regex through CTest's `-N -R`: selected 200 intended entries and included both shard 100 and shard 199. Static registration/inventory/budget inspection found 199 unique numbered entries, each budgeted at 90 seconds.
- `verify-v02-adoption.py --self-test-release-notes-v04 --repo .`: passed, 2 positives and 72 controls.
- `verify-support-ledger.py --self-test-claims --claims-version 0.4.0 --rev 9166ab60d25c6d246761b4aa33a0ceb35dd83f5c --repo .`: passed, 22 positives and 21 controls.
- `verify-support-ledger.py --self-test-disclosure --repo .`: passed, 4 positives and 20 controls.
- `verify-version-window.py --self-test --repo .`: passed, 11 positives and 64 controls.
- `verify-version-window.py --self-test-version-v04 --repo .`: passed, 63 positives and 66 controls.
- `verify-review-evidence.py --self-test --rev 9166ab60d25c6d246761b4aa33a0ceb35dd83f5c --repo .`: passed, 33 positives and 28 controls.

These checks establish local parser, statement, path-confinement, source-binding, and test-selection behavior. They do not establish hardware or gameplay behavior, rights beyond the recorded policy, hosted CI success, signing, publication, or platform promotion.

## Findings and dispositions

ADV-01 through ADV-20 preserve the Phase 23 review history and remain fixed by ancestor commits. ADV-21 and ADV-22 are the owner-approved D-155 corrections fixed in the reviewed commit. No unresolved correctness or security finding remains in this review.

<!-- gbb-review-evidence:start -->
```json
{
  "schema_version": 1,
  "report_id": "gbb-phase23-adversarial-9166ab60d25c6d246761b4aa33a0ceb35dd83f5c-20261106-d155",
  "role": "adversarial",
  "reviewer_id": "adversarial-d155",
  "independent": true,
  "reviewed_sha": "9166ab60d25c6d246761b4aa33a0ceb35dd83f5c",
  "findings": [
    {
      "id": "ADV-01",
      "category": "correctness",
      "severity": "high",
      "required_property": "Only visible Markdown prose may satisfy required release-note disclosures.",
      "disposition": "fixed",
      "rationale": "The exact-source renderer-built release-note baseline passes. The current controls reject disclosures hidden in inline and block code, comments, and container code; removing a required visible clause fails with its specific diagnostic.",
      "fix_sha": "9e09eef8b379ca8d329cb13bf354058661296daa",
      "verification_ref": "At reviewed SHA: verify-v02-adoption.py --self-test-release-notes-v04: positives=2 controls=72; verify-version-window.py --self-test-version-v04: positives=63 controls=66."
    },
    {
      "id": "ADV-02",
      "category": "correctness",
      "severity": "high",
      "required_property": "Release notes must not claim a requirement is complete while its required status remains Pending.",
      "disposition": "fixed",
      "rationale": "The exact-source release-note controls reject both a promoted Pending row and contradictory completion prose; the valid Pending baseline passes before each mutation.",
      "fix_sha": "9e09eef8b379ca8d329cb13bf354058661296daa",
      "verification_ref": "At reviewed SHA: verify-v02-adoption.py --self-test-release-notes-v04: positives=2 controls=72; verify-support-ledger.py --self-test-disclosure: positives=4 controls=20."
    },
    {
      "id": "ADV-03",
      "category": "correctness",
      "severity": "high",
      "required_property": "Metadata-only diagnostic inventories must not be presented as executed or passing diagnostics.",
      "disposition": "fixed",
      "rationale": "The exact-source release-note controls reject the claim that all 513 named diagnostic microtests executed and passed, while accepting the metadata-only baseline with seven unresolved gates and zero real fixtures executed or admitted.",
      "fix_sha": "9e09eef8b379ca8d329cb13bf354058661296daa",
      "verification_ref": "At reviewed SHA: verify-v02-adoption.py --self-test-release-notes-v04: positives=2 controls=72; the named metadata-as-diagnostic mutant checks its specific diagnostic."
    },
    {
      "id": "ADV-04",
      "category": "correctness",
      "severity": "high",
      "required_property": "A rights-scope no-go must not be represented as a legal license prohibition without evidence.",
      "disposition": "fixed",
      "rationale": "The exact-source notes controls reject an unsupported claim that both candidates' licenses prohibit repository and public-CI use; the source/rights-scope baseline remains accepted.",
      "fix_sha": "9e09eef8b379ca8d329cb13bf354058661296daa",
      "verification_ref": "At reviewed SHA: verify-v02-adoption.py --self-test-release-notes-v04: positives=2 controls=72; rights-scope-presented-as-license-prohibition mutant."
    },
    {
      "id": "ADV-05",
      "category": "correctness",
      "severity": "high",
      "required_property": "Inline code, image destinations, and hidden markup cannot satisfy visible-prose or ledger-link requirements.",
      "disposition": "fixed",
      "rationale": "Visible prose and a real ledger link pass. Code-only disclosure evidence, image-ledger destinations, and hidden titles/alt text fail the required visibility or ledger checks.",
      "fix_sha": "9e09eef8b379ca8d329cb13bf354058661296daa",
      "verification_ref": "At reviewed SHA: verify-v02-adoption.py --self-test-release-notes-v04 and verify-version-window.py --self-test-version-v04 pass their paired visibility controls."
    },
    {
      "id": "ADV-06",
      "category": "correctness",
      "severity": "high",
      "required_property": "A required support-ledger link must target the ledger itself, not contain its path in unrelated URL text or a title.",
      "disposition": "fixed",
      "rationale": "Relative and canonical ledger links are accepted; external-query, title-only, image, and malformed destinations reject for ledger mismatch or malformed-link reasons.",
      "fix_sha": "9a193975fb32ae69bd09be2cf847e3271d078733",
      "verification_ref": "At reviewed SHA: verify-v02-adoption.py --self-test-release-notes-v04 and verify-version-window.py --self-test-version-v04 passed."
    },
    {
      "id": "ADV-07",
      "category": "correctness",
      "severity": "high",
      "required_property": "Text hidden by closed or unterminated HTML comments cannot satisfy release-note or changelog requirements.",
      "disposition": "fixed",
      "rationale": "Closed- and open-comment mutants cannot satisfy candidate or required-clause checks; a hidden changelog ledger link fails the version-output check. Visible counterparts pass.",
      "fix_sha": "9a193975fb32ae69bd09be2cf847e3271d078733",
      "verification_ref": "At reviewed SHA: verify-v02-adoption.py --self-test-release-notes-v04: positives=2 controls=72; verify-version-window.py --self-test: positives=11 controls=64."
    },
    {
      "id": "ADV-08",
      "category": "correctness",
      "severity": "high",
      "required_property": "Fenced and indented code inside list and blockquote containers cannot satisfy disclosure or changelog visibility requirements.",
      "disposition": "fixed",
      "rationale": "The current controls cover same-line and nested list/blockquote fences plus indented code. Hidden disclosures and links reject; visible disclosures and genuine code masking remain accepted.",
      "fix_sha": "46f5ce4a515daa65bb9850a28a1ee4be9b9b8c5a",
      "verification_ref": "At reviewed SHA: verify-v02-adoption.py --self-test-release-notes-v04 and verify-version-window.py --self-test-version-v04 passed."
    },
    {
      "id": "ADV-09",
      "category": "correctness",
      "severity": "high",
      "required_property": "Incomplete raw-HTML block openers cannot hide required changelog links or release-note disclosures.",
      "disposition": "fixed",
      "rationale": "Script, pre, style, doctype, and XML processing-instruction openers fail at the required paths while comments, code, and escaped examples remain valid when visible evidence is present. The legacy-matcher controls establish causality.",
      "fix_sha": "a63f1dc67654613e105ac1071b7445f21adea0bc",
      "verification_ref": "At reviewed SHA: verify-version-window.py --self-test-version-v04: positives=63 controls=66; verify-v02-adoption.py --self-test-release-notes-v04: positives=2 controls=72."
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
      "verification_ref": "At reviewed SHA: verify-v02-adoption.py --self-test-release-notes-v04: positives=2 controls=72; exact-source docs shards 0/200 and 199/200 pass; matcher unchanged by D-155."
    },
    {
      "id": "ADV-12",
      "category": "correctness",
      "severity": "high",
      "required_property": "Unicode 18.0 Default_Ignorable_Code_Point characters, including non-Cf characters, cannot split a visible unsupported CGB-game claim.",
      "disposition": "fixed",
      "rationale": "The matcher includes the frozen Unicode 18.0 default-ignorable ranges; current paired controls cover U+034F and representative non-Cf ranges with safe-text counterparts.",
      "fix_sha": "a6bc0a824bce55de57422e2b6b73b94ed0f841d1",
      "verification_ref": "At reviewed SHA: verify-v02-adoption.py --self-test-release-notes-v04: positives=2 controls=72; docs matcher is unchanged by D-155."
    },
    {
      "id": "ADV-13",
      "category": "correctness",
      "severity": "high",
      "required_property": "Valid CommonMark references to invisible characters cannot split an unsupported CGB-game claim after rendering.",
      "disposition": "fixed",
      "rationale": "Hexadecimal, decimal, and named references to invisible/default-ignorable characters are decoded for the claim matcher; code spans remain masked and visible safe-reference prose remains accepted.",
      "fix_sha": "fc0ba4ff9626e06e04d8800800561b51414166bf",
      "verification_ref": "At reviewed SHA: verify-v02-adoption.py --self-test-release-notes-v04: positives=2 controls=72; parser/matcher code unchanged by D-155."
    },
    {
      "id": "ADV-14",
      "category": "correctness",
      "severity": "high",
      "required_property": "All valid CommonMark character references in visible prose are normalized before unsupported-game matching.",
      "disposition": "fixed",
      "rationale": "The claim matcher decodes valid visible references to spaces and CGB letters as well as invisible separators. Safe visible references and masked code spans retain their intended behavior.",
      "fix_sha": "fc0ba4ff9626e06e04d8800800561b51414166bf",
      "verification_ref": "At reviewed SHA: verify-v02-adoption.py --self-test-release-notes-v04: positives=2 controls=72; exact-source claim/profile controls pass 22 positives/21 controls."
    },
    {
      "id": "ADV-15",
      "category": "correctness",
      "severity": "high",
      "required_property": "CommonMark hard line breaks and encoded spaces are joined for unsupported-game matching in docs, release notes, and notices after code masking.",
      "disposition": "fixed",
      "rationale": "LF, CR, CRLF, encoded-space, soft-break, safe-prose, and code controls remain paired; the notices caller supplies uncollapsed visible prose to the shared matcher.",
      "fix_sha": "e26757fafc818a92ddf7ca45f1a409658a5a5bdd",
      "verification_ref": "At reviewed SHA: release-note controls pass 2/72; docs shard 0/200 passes notice-path child controls; notice caller and matcher are unchanged except D-155 path checks."
    },
    {
      "id": "ADV-16",
      "category": "correctness",
      "severity": "high",
      "required_property": "Visible CGB claim text split by CommonMark emphasis or inline-link labels cannot evade unsupported-game matching.",
      "disposition": "fixed",
      "rationale": "Strong, intraword-star, underscore-emphasis, and inline-link-label claims are rejected. Intraword underscores, escaped punctuation, code, and destination/title-only claims remain accepted.",
      "fix_sha": "e017078b72e78b38fb596faced3af3e35c2ca0ce",
      "verification_ref": "At reviewed SHA: verify-v02-adoption.py --self-test-release-notes-v04: positives=2 controls=72; matcher code unchanged by D-155."
    },
    {
      "id": "ADV-17",
      "category": "correctness",
      "severity": "high",
      "required_property": "Visible shortcut, full, and collapsed reference-link labels participate in unsupported-game matching while destinations and titles do not.",
      "disposition": "fixed",
      "rationale": "The matcher resolves each valid reference-label form and excludes its destination/title; unresolved and escaped labels, code, and destination-only claims remain accepted counterparts. Notice uses the same claim matcher.",
      "fix_sha": "b798781105b8f6f803e85aa2ad766d2b2fdbec22",
      "verification_ref": "At reviewed SHA: release-note controls pass 2/72; docs shards 0/200 and 199/200 pass; parser/matcher diff is empty for D-155."
    },
    {
      "id": "ADV-18",
      "category": "security",
      "severity": "high",
      "required_property": "Delimiter matching must not rescan all prior unmatched runs for each closer in bounded public Markdown input.",
      "disposition": "fixed",
      "rationale": "The matcher uses fixed per-marker candidate buckets and exhausts candidates rather than scanning all prior delimiter runs; dense unmatched-marker controls assert claim detection without timing thresholds.",
      "fix_sha": "6876fab06bf746fdaab67beaa4d52a6b1c70ac06",
      "verification_ref": "At reviewed SHA: release-note controls pass 2/72; source inspection confirms the candidate-stack implementation is unchanged by D-155."
    },
    {
      "id": "ADV-19",
      "category": "correctness",
      "severity": "high",
      "required_property": "CommonMark emphasis flanking treats Unicode punctuation and symbol categories P and S as punctuation for unsupported-game matching.",
      "disposition": "fixed",
      "rationale": "The exact-source matcher uses Unicode P/S categories. The paired Unicode-symbol claim and safe-prose controls are retained; current release-note controls pass.",
      "fix_sha": "4c9c54f8b5a33e758624c997f107d1ffdd7c94a0",
      "verification_ref": "At reviewed SHA: release-note controls pass 2/72; historical exact-source D-153 probes rejected both claims on four production paths and accepted paired safe/code controls; matcher is unchanged by D-155."
    },
    {
      "id": "ADV-20",
      "category": "security",
      "severity": "high",
      "required_property": "Impossible nested or over-999-character reference-label candidates are rejected before copying or normalization.",
      "disposition": "fixed",
      "rationale": "A bracket stack and prefix count check nested/overlong spans before slicing or normalization; only valid labels at or below CommonMark's 999-character limit are normalized. Dense-bracket controls retain safe prose counterparts.",
      "fix_sha": "4c9c54f8b5a33e758624c997f107d1ffdd7c94a0",
      "verification_ref": "At reviewed SHA: release-note controls pass 2/72; historical exact-source D-154 probes reject the 512-level attack on four production paths and accept safe counterparts; source is unchanged by D-155."
    },
    {
      "id": "ADV-21",
      "category": "security",
      "severity": "high",
      "required_property": "Notice inputs and self-test copy destinations must resolve inside their respective roots, including when paths traverse or follow symlinks.",
      "disposition": "fixed",
      "rationale": "The old inline notice path could read outside the checkout and be reused as a copy destination. The reviewed code rejects traversal components, resolves source symlinks and enforces repository containment, and re-resolves copy destinations after parent creation. Current minimal-tree probes accept baseline/in-root paths, reject traversal and external symlink inputs as notice-path-outside-root, and reject a target symlink as self-test-copy-path-outside-root with zero external writes. The exact-source docs shard runs its matching traversal, symlink, and copy controls.",
      "fix_sha": "9166ab60d25c6d246761b4aa33a0ceb35dd83f5c",
      "verification_ref": "At reviewed SHA: docs shard 0/200 passed; direct check_notices baseline=112 and safe in-root=113, traversal/symlink rejected; direct copy_inputs normal copy passed and destination symlink rejected with external_files=0."
    },
    {
      "id": "ADV-22",
      "category": "other",
      "severity": "medium",
      "required_property": "The focused Plan 23-04 CTest selector must include every registered numbered docs shard, including 100–199.",
      "disposition": "fixed",
      "rationale": "The former two-digit selector omitted the high-numbered shards. The corrected `[0-9]+` selector matched all 199 numbered tests in an isolated CTest run, including 100 and 199; shard 199/200 itself passed. CMake registration, expected inventory, and timeout allowlist contain each numbered shard once.",
      "fix_sha": "9166ab60d25c6d246761b4aa33a0ceb35dd83f5c",
      "verification_ref": "At reviewed SHA: exact Plan regex through ctest -N -R selected 200 total entries; CMake range/inventory/budget inspection matched shards 1–199 exactly; production docs shard 199/200 passed."
    }
  ]
}
```
<!-- gbb-review-evidence:end -->
