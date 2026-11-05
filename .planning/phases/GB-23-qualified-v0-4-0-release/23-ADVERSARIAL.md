# Phase 23 Adversarial Review

**Reviewed implementation:** `aecf09cc02ae81bdb2047087014f1bc66b71aa06`
**Scope:** Plans 23-01 through 23-04 and Plan 23-09, including immutable support claims, release-note and changelog validation, Markdown visibility, profile/source/version bindings, and the D-144–D-154 corrections in the unsupported CGB-game matcher.
**Review posture:** I read the validator and release-window source from the exact commit, examined the current controls, and ran targeted mutations against production functions. No real CGB game or diagnostic fixture was fetched, built, run, or admitted. No release artifact was signed, notarized, or promoted; no hosted release evidence is claimed.

## Results

No unresolved correctness or security issue remains in this reviewed scope. All retained findings ADV-01 through ADV-20 are fixed in full ancestor commits and have exact-source verification references below. The focused 50-test selection passed on the source-identical implementation parent noted below; the direct real-report gate remains pending because the independent reports are not committed yet.

### Review-evidence CMake regex correction

The review-evidence success regex correction from the prior review remains intact: the checker prints a 12-character implementation prefix, and the CMake `PASS_REGULAR_EXPRESSION` and immutable registration expectation use `[0-9a-f]+`. The prior `{12}` form did not match in CMake’s regex dialect. The registration self-test still compares the complete required registration string against immutable `tests/CMakeLists.txt`. The report-gate self-test passed 32 positives and 27 controls at the previously reviewed exact SHA. The current commit changes only `.planning/STATE.md` and `.continue-here.md` relative to its tested parent; the test and implementation blobs are identical to that parent.

### Deterministic docs self-test shards

I read the exact diff from `de66945db318d7aeb7acdb13a0bd0203fed1bd31` to this implementation. The validator change adds only deterministic partitioning around existing docs `child_result` calls and a shard-0 condition around the existing shared release-note sweep; the D-144–D-154 parser, matcher, and control definitions are unchanged. Each docs child call increments the global-invocation index before applying `index % shard_count`, so for the registered count of 32 every call index is assigned to exactly one shard. The selected-count formula `1 + (calls - 1 - shard) // shard_count` gives the exact cardinality for that residue class. Each shard requires a nonempty selection with at least one successful positive and one rejected negative, and checks that the observed selected count equals the formula. The original fixed docs control-inventory check remains in place.

The release-note control function has one call site in `run_self_test_docs`; it runs when the invocation is unsharded or shard index is 0, and is skipped for indices 1–31. CMake registers exactly one shard-0 test (`v02_adoption_docs_controls`) and shards 01–31 once each. `tests/expected-tests.txt` and `tests/ci/test-budget-allowlist` each contain the same 32 registered names; all shard entries have a 90-second timeout. `ctest -N` listed the complete set. The current `verify-test-budget.py --build-dir build --base f2b05c9fb3ba314cfe46959b64073ce9441724ca --repo .` check passed with 1,767 tests and 120 budgeted rows, confirming the configured inventory and timeout ceilings agree.

I probed invalid boundaries (`-1/32`, `32/32`, `0/1`, and `0/0`), missing/extra values, and use with `--check docs`, the game self-test, release-note self-test, and claim-boundary self-test. Each was rejected by argparse with the corresponding shard validation diagnostic. The valid final shard `31/32` passed the production docs check (473 checks), assigned 13 child calls, and reported three negative controls alongside successful positive calls. The owner’s full 50-test focused CTest selection passed on the source-identical parent commit `1a7558d9749538a894e23a9cf965210d57bb77dd`; that selected set includes all 32 shard tests, so the aggregate confirms the original controls remain covered and the shard-0 release-note sweep passes once. I did not repeat the complete shard set.

### D-153 and D-154 production probes

I independently appended the two D-153 claims—`😀__CGB__ game passes all acceptance checks.` and `😀**CGB* game passes all acceptance checks.`—to README, game-acceptance, and third-party notices, and to a valid renderer-built v0.4 release-note preface. All four production paths rejected each claim with their intended `unsupported-cgb-game-qualification` diagnostic. A renderer-built release-note baseline passed its 55 checks. The matching safe Unicode-symbol evidence phrase, rule-of-three safe phrase, dense-bracket evidence phrase, escaped punctuation, intraword underscores, inline code, and fenced code all passed in each path.

I also appended the 512-level balanced bracket sample followed by the valid unused `[dense-control]: /target` reference definition and the unsupported game claim. README, game-acceptance, notices, and release notes rejected it with the intended unsupported-game diagnostic; the same bracket/reference prefix followed by safe test-ROM evidence passed in each path. These controls exercise the production readers and matcher, not just a helper. The release-note and docs self-test controls also cover link destinations/titles and valid shortcut, full, and collapsed references.

The complexity review is structural. `mask_markdown_nonrendered` computes bracket pairs once using a stack, builds a prefix count once, and tests nested/overlong label spans before slicing or normalizing. Only a valid span of at most 999 source characters can reach case-folding. Candidate endpoint lookup is constant-time. The emphasis matcher uses a fixed set of marker/modulo/open-close candidate buckets rather than rescanning all earlier delimiter runs. The dense controls are regression inputs, not timing thresholds.

### D-144–D-152 parser cases

The exact-source control set preserves the paired cases added under the bounded rescope. All attacks fail for the intended cause and their valid counterparts pass:

| Case | Negative and intended result | Accepted counterpart |
|---|---|---|
| Explicit image labels and list continuation | Whitespace-only explicit image labels leave an unsupported claim visible and fail as `unsupported-cgb-game-qualification`; tab label syntax fails closed as `markdown-tab-unsupported`. A list/blockquote reference title in the wrong continuation column leaves the claim visible and fails as `unsupported-cgb-game-qualification`. | A collapsed `[]` image reference resolves and masks alt text; a title at the CommonMark tab-expanded content column is masked. |
| Comment-aware reference labels | Differing comment payloads between the label and definition do not resolve; visible claim is rejected. | Matching comments inside labels still resolve. |
| Comment/fence interaction | `<!-- -->` cannot create a false fence that hides a claim. | A standalone comment followed by a genuine fenced block still masks the block claim. |
| Autolink and title parsing | A URI autolink containing `]` cannot hide a required hardware disclosure in the link title; the missing-disclosure diagnostic is preserved. | A valid title after the same autolink form remains non-rendered. |
| Malformed links and reference definitions | Invalid/empty destinations, invalid escapes, unterminated or malformed titles, NULs, over-nested destinations, blank-line titles, malformed inline links, and unresolved links do not hide claims. Malformed inline links fail closed as `markdown-inline-link-malformed`; valid-but-unresolved visible labels fail as the unsupported-game diagnostic. | Valid titles, escaped parentheses, matching references, code spans, and genuine fences remain accepted/masked according to their rendered role. |
| Invisible characters and references | Literal `Cf`, Unicode 18.0 default-ignorables, and valid entity references to invisible characters fail as unsupported-game claims. Encoded visible spaces or CGB letters also fail after decoding. | Safe text, safe visible references, and code spans retain their prior behavior. |
| Hard breaks, emphasis, and links | LF/CR/CRLF CommonMark hard-break claims, encoded-space joins, emphasis-split CGB text, and inline/reference-link label claims fail as unsupported game qualification, including through the notices caller. | Soft breaks where the claim does not form, escaped punctuation, intraword underscores, unresolved/escaped labels, code spans/fences, and destination/title-only claims remain accepted. |
| Dense delimiter controls | Dense unmatched emphasis cannot prevent claim detection. | Its safe evidence counterpart passes. |

The parser and matcher portions of `verify-v02-adoption.py` are unchanged from `4c9c54f8b5a33e758624c997f107d1ffdd7c94a0`, where the owner-run complete docs self-test passed 473 checks with 255/255 negative controls rejected. The exact diff adds only the deterministic shard wrapper and release-note sweep condition described above. The current valid shard-31 invocation reran the production docs check (473 checks); the owner-run full focused CTest selection on the source-identical parent covered all shard indices and the shard-0 release-note sweep. Targeted D-153/D-154 probes exercised README, game-acceptance, notices, and renderer-built notes at the previous exact matcher source. No parser or matcher bypass was found in the sharding change.

### Plan 23-09 visibility and opener matrix

I re-evaluated prior ADV-09 against the current source. The exact opener set is `<script` newline/space forms, `<pre` newline/space forms, `<style` newline/space forms, mixed-case `<ScRiPt`, incomplete `<!DOCTYPE html`, and incomplete `<?xml version="1.0"`. On the changelog path, every opener is tried before the heading and inside the section; each hidden-link mutant must fail as `window-version-output-mismatch`, while its visible-ledger-link baseline passes. Comments, fenced/indented/inline-code samples, and escaped opener examples are accepted when the real ledger link stays visible. The current self-test temporarily restores the old matcher and confirms it accepts the causal hidden-link sample before verifying the corrected matcher rejects it.

On the release-note path, every opener is tried both before the preface and around the ledger link, and fails as `release-notes-raw-html-unsupported`; the renderer-built notes, and examples masked by comment/fence/indent/code/escape syntax, pass. The v0.4 note self-test passed 2 positive baselines and 72 negative controls. The v0.4 version-window self-test passed 63 positives and 66 controls; the general version-window self-test passed 11 positives and 64 controls. The docs controls reject raw HTML as `markdown-raw-html-unsupported`; those controls remain in the current shard set, whose source-identical full CTest selection passed.

### Release, profile, and provenance attacks

The current support-claims check passed for v0.4 and reports the pinned two candidates, CGB-CPU-E harness, diagnostics `513/7/0/0`, nine inherited claims, and three explicit non-claims at this source. Its causal test passed 22 positives and 21 controls. Candidate reasons cannot be omitted or swapped; fabricated candidate build/run, game admission, or game evidence is rejected with its candidate/admission/evidence diagnostic. Metadata is not accepted as execution evidence. The renderer-built note is the accepted counterpart.

Release-note controls reject each missing or promoted required Pending status and contradictions that assert completion while the Pending row remains. They reject disclosure clauses hidden in code/comments/container fences and unsupported claims of signing/notarization, publication, or platform coverage with their respective diagnostics. Historical v0.3 claim and ledger bytes remain pinned; the support-ledger controls reject rewritten historical output as `ledger-not-generated`. The exact-source release-policy self-test passed 11 positives and 11 controls, and its live pin check passed. The tracked version window is inactive for the current development tree, which is accepted; no active version PR or hosted run was exercised.

`verify-review-evidence.py --self-test` passed 32 positives and 27 controls. It validates the report contract and is not a substitute for this source review. No v0.4 release, hosted evidence, actual game execution, fixture admission, signing, notarization, or platform promotion is asserted.

## Findings and Dispositions

ADV-01 through ADV-08 were real visibility/claim bypasses in earlier Phase 23 revisions and are fixed by their recorded ancestor commits. ADV-09 was independently re-evaluated at the exact SHA and is now fixed. ADV-10 through ADV-20 record the owner-approved D-144–D-154 corrections; each was independently source-checked, with targeted production probes for D-153 and D-154 and the exact-source paired control suites cited above.

### ADV-01–ADV-08: Previously found visibility and disclosure bypasses — fixed

Earlier revisions allowed indented/inline code, images, external-query URLs, comments, or nested container fences to stand in for visible disclosures or a real ledger link. They also allowed contradictions against required Pending and rights-scope wording, and metadata to be stated as executed diagnostics. The recorded commits mask non-rendered content, require a real allowed ledger destination, preserve the precise pending/rights status, and reject false evidence promotions. Current release-note, support-profile, and version-window controls keep accepted baselines and reject each negative for its own diagnostic.

### ADV-09: Incomplete raw-HTML openers hid required content — fixed

The old changelog validator accepted incomplete tag/declaration/PI openers with the ledger link visually hidden later in the block. The current implementation rejects every opener and placement in the matrix above, while accepting ordinary visible examples in comments, code, and escaped prose. The current self-tests include the old matcher as a causal control.

### ADV-10–ADV-20: D-144–D-154 parser correctness and resource-bound fixes — fixed

The exact-source controls prevent Markdown parser disagreement from making hidden disclosures count or visible unsupported-game claims disappear. They retain CommonMark-aware matching for hard breaks, entities, emphasis, inline/reference labels, and Unicode P/S flanking, while keeping code, escapes, unresolved labels, destinations, and titles out of claim text. D-154 also bounds nested reference-label work before copying or normalization. The findings JSON records the specific fix commit and current-source verification for each issue.

## Evidence limits

All results are local software checks against the exact source identity named above. The checks establish parser, profile, provenance, and statement-validation behavior. They do not establish actual CGB gameplay, hardware behavior, fixture rights beyond the recorded policy, hosted CI success, signing/notarization, publication, or platform promotion. REL-01 remains Pending.

## Structured Evidence

<!-- gbb-review-evidence:start -->
```json
{
  "schema_version": 1,
  "report_id": "gbb-phase23-adversarial-aecf09cc-shards-20261104-01",
  "role": "adversarial",
  "reviewer_id": "codex-adversarial-reviewer-01",
  "independent": true,
  "reviewed_sha": "aecf09cc02ae81bdb2047087014f1bc66b71aa06",
  "findings": [
    {
      "id": "ADV-01",
      "category": "correctness",
      "severity": "high",
      "required_property": "Only visible Markdown prose may satisfy required release-note disclosures.",
      "disposition": "fixed",
      "rationale": "An earlier revision accepted the complete required preface when every line was indented Markdown code. The current renderer-built baseline passes and the indented preface is rejected as release-notes-empty.",
      "fix_sha": "9e09eef8b379ca8d329cb13bf354058661296daa",
      "verification_ref": "python3 -I tests/scripts/verify-v02-adoption.py --self-test-release-notes-v04 --repo . at reviewed source 4c9c54f8b5a33e758624c997f107d1ffdd7c94a0: PASS positives=2 controls=72; accepted baseline paired with indented-code rejection"
    },
    {
      "id": "ADV-02",
      "category": "correctness",
      "severity": "high",
      "required_property": "Release notes must not claim a requirement is complete while its required status remains Pending.",
      "disposition": "fixed",
      "rationale": "The current control rejects both a promoted DIAG-01 status and an appended completion claim beside the required Pending row as release-notes-requirement-status-promoted. The renderer-built note remains the accepted counterpart.",
      "fix_sha": "9e09eef8b379ca8d329cb13bf354058661296daa",
      "verification_ref": "python3 -I tests/scripts/verify-v02-adoption.py --self-test-release-notes-v04 --repo . at reviewed source: PASS positives=2 controls=72; pending-status-promoted and contradictory-pending-status controls"
    },
    {
      "id": "ADV-03",
      "category": "correctness",
      "severity": "high",
      "required_property": "Metadata-only diagnostic inventories must not be presented as executed or passing diagnostics.",
      "disposition": "fixed",
      "rationale": "The current release-note control rejects the claim that all 513 diagnostic microtests executed and passed as release-notes-metadata-as-diagnostic. The accepted renderer output preserves 513 named entries, seven unresolved gates, and zero admitted or executed real fixtures.",
      "fix_sha": "9e09eef8b379ca8d329cb13bf354058661296daa",
      "verification_ref": "python3 -I tests/scripts/verify-v02-adoption.py --self-test-release-notes-v04 --repo . at reviewed source: PASS positives=2 controls=72; metadata-as-diagnostic negative"
    },
    {
      "id": "ADV-04",
      "category": "correctness",
      "severity": "high",
      "required_property": "A rights-scope no-go must not be represented as a legal license prohibition without evidence.",
      "disposition": "fixed",
      "rationale": "The current release-note control rejects the claim that both candidates' licenses prohibit repository and public-CI use as release-notes-license-prohibition-unsupported while accepting the required scope wording.",
      "fix_sha": "9e09eef8b379ca8d329cb13bf354058661296daa",
      "verification_ref": "python3 -I tests/scripts/verify-v02-adoption.py --self-test-release-notes-v04 --repo . at reviewed source: PASS positives=2 controls=72; unsupported license-prohibition negative"
    },
    {
      "id": "ADV-05",
      "category": "correctness",
      "severity": "high",
      "required_property": "Inline code, image destinations, and hidden markup cannot satisfy visible-prose or ledger-link requirements.",
      "disposition": "fixed",
      "rationale": "Current controls reject code-only disclosure evidence and image-ledger destinations while accepting visible prose and a real ledger link. Link titles and image alt text remain excluded from the relevant visibility proof.",
      "fix_sha": "9e09eef8b379ca8d329cb13bf354058661296daa",
      "verification_ref": "python3 -I tests/scripts/verify-v02-adoption.py --self-test-release-notes-v04 --repo . and --self-test-version-v04: PASS; current reviewed-source v0.4 note controls positives=2 controls=72 and version-output controls positives=63 controls=66"
    },
    {
      "id": "ADV-06",
      "category": "correctness",
      "severity": "high",
      "required_property": "A required support-ledger link must target the ledger itself, not contain its path in unrelated URL text or a title.",
      "disposition": "fixed",
      "rationale": "Relative and canonical ledger links remain accepted. External-query, link-title, nested-title, image, and malformed destinations reject with the ledger-version mismatch or malformed-link diagnostic.",
      "fix_sha": "9a193975fb32ae69bd09be2cf847e3271d078733",
      "verification_ref": "python3 -I tests/scripts/verify-v02-adoption.py --self-test-release-notes-v04 --repo . and python3 -I tests/scripts/verify-version-window.py --self-test-version-v04 --repo . at reviewed source: PASS; intended ledger-link diagnostics"
    },
    {
      "id": "ADV-07",
      "category": "correctness",
      "severity": "high",
      "required_property": "Text hidden by a closed or unterminated HTML comment cannot satisfy release-note or changelog requirements.",
      "disposition": "fixed",
      "rationale": "The current notes controls reject closed-comment hiding as release-notes-candidate-name-missing and unclosed-comment hiding as a missing required clause; version-window controls reject a hidden changelog ledger link as window-version-output-mismatch. Visible counterparts pass.",
      "fix_sha": "9a193975fb32ae69bd09be2cf847e3271d078733",
      "verification_ref": "python3 -I tests/scripts/verify-v02-adoption.py --self-test-release-notes-v04 --repo . and python3 -I tests/scripts/verify-version-window.py --self-test --repo . at reviewed source: PASS; version-window controls positives=11 controls=64"
    },
    {
      "id": "ADV-08",
      "category": "correctness",
      "severity": "high",
      "required_property": "Fenced and indented code inside list and blockquote containers cannot satisfy disclosure or changelog visibility requirements.",
      "disposition": "fixed",
      "rationale": "Current controls reject same-line list fences, nested list/blockquote fences in both orders, blockquote/list indented code, and hidden changelog links with window-version-output-mismatch. Visible disclosures and real fenced-code masking remain accepted.",
      "fix_sha": "46f5ce4a515daa65bb9850a28a1ee4be9b9b8c5a",
      "verification_ref": "python3 -I tests/scripts/verify-v02-adoption.py --self-test-release-notes-v04 --repo . and python3 -I tests/scripts/verify-version-window.py --self-test-version-v04 --repo . at reviewed source: PASS; notes positives=2 controls=72, version-output positives=63 controls=66"
    },
    {
      "id": "ADV-09",
      "category": "correctness",
      "severity": "high",
      "required_property": "Incomplete raw-HTML block openers cannot hide required changelog links or release-note disclosures.",
      "disposition": "fixed",
      "rationale": "I re-evaluated the prior finding against this source. Script/pre/style openers with whitespace or line endings, mixed-case script, incomplete doctype, and incomplete XML PI reject in changelog and release-note paths. Changelog controls cover before-heading and inside-section placements and require window-version-output-mismatch; note controls require release-notes-raw-html-unsupported. Comment, fence, indented-code, inline-code, and escaped examples remain accepted when visible evidence is present. A legacy matcher control reproduces the old acceptance, tying the current rejection to the fix.",
      "fix_sha": "a63f1dc67654613e105ac1071b7445f21adea0bc",
      "verification_ref": "python3 -I tests/scripts/verify-version-window.py --self-test-version-v04 --repo .: PASS positives=63 controls=66; python3 -I tests/scripts/verify-v02-adoption.py --self-test-release-notes-v04 --repo .: PASS positives=2 controls=72; exact-source docs check=473 and owner-run docs self-test=473 checks/255 rejected controls"
    },
    {
      "id": "ADV-10",
      "category": "correctness",
      "severity": "high",
      "required_property": "Markdown visibility and claim matching must distinguish valid labels, container continuations, comments, fences, and autolinks according to the paired D-144 cases.",
      "disposition": "fixed",
      "rationale": "The exact-source controls reject whitespace-only explicit image labels, tab-expanded invalid continuations, mismatched comment payloads, false comment-created fences, and a title-only hardware disclosure when a URI autolink contains a closing bracket. They accept the valid collapsed image reference, matching-comment labels, correct tab-expanded continuation, a genuine fence after a standalone comment, and a valid title after the autolink. Malformed destinations/titles fail closed with their intended parser diagnostics.",
      "fix_sha": "3d27596b341877d9a19cb82409e178f9eae0d1e9",
      "verification_ref": "Plan 23-04 D-144 controls in tests/scripts/verify-v02-adoption.py at 4c9c54f8b5a33e758624c997f107d1ffdd7c94a0; exact-source docs self-test recorded by owner: checks=473, negative_controls=255, rejected_controls=255; focused direct D-153/D-154 probes also exercised README/game surfaces"
    },
    {
      "id": "ADV-11",
      "category": "correctness",
      "severity": "high",
      "required_property": "Invisible Unicode format characters cannot split the unsupported CGB-game claim in visible prose.",
      "disposition": "fixed",
      "rationale": "The matcher removes Unicode Cf characters only for this unsupported-game pattern. Current controls reject U+200B, U+2060, and U+200C and accept ordinary safe text containing the same kind of separator; disclosure matching is not globally normalized.",
      "fix_sha": "742bf1bb5dd3a6e71ab93dbdb420bca2ec94d16a",
      "verification_ref": "python3 -I tests/scripts/verify-v02-adoption.py --self-test-release-notes-v04 --repo . at reviewed source: PASS positives=2 controls=72; exact-source docs self-test recorded as 473/255"
    },
    {
      "id": "ADV-12",
      "category": "correctness",
      "severity": "high",
      "required_property": "Unicode 18.0 Default_Ignorable_Code_Point characters, including non-Cf U+034F, cannot split the unsupported CGB-game claim.",
      "disposition": "fixed",
      "rationale": "The matcher uses the frozen Unicode 18.0 default-ignorable ranges in addition to Cf handling. Controls reject U+034F, Hangul filler, variation selector-16, and a reserved default-ignorable character, with safe-text counterparts accepted.",
      "fix_sha": "a6bc0a824bce55de57422e2b6b73b94ed0f841d1",
      "verification_ref": "python3 -I tests/scripts/verify-v02-adoption.py --self-test-release-notes-v04 --repo . at reviewed source: PASS positives=2 controls=72; exact-source docs self-test recorded as 473/255"
    },
    {
      "id": "ADV-13",
      "category": "correctness",
      "severity": "high",
      "required_property": "Valid CommonMark references to invisible characters cannot split an unsupported CGB-game claim after rendering.",
      "disposition": "fixed",
      "rationale": "Valid decimal, hexadecimal, and named references that render invisible format/default-ignorable characters are decoded before this matcher; code spans remain masked. Paired controls reject the resulting visible claim and accept safe visible-reference prose.",
      "fix_sha": "fc0ba4ff9626e06e04d8800800561b51414166bf",
      "verification_ref": "python3 -I tests/scripts/verify-v02-adoption.py --self-test-release-notes-v04 --repo . at reviewed source: PASS positives=2 controls=72; exact-source docs self-test recorded as 473/255"
    },
    {
      "id": "ADV-14",
      "category": "correctness",
      "severity": "high",
      "required_property": "Valid visible CommonMark character references, including encoded whitespace and letters, are normalized before unsupported-game claim matching.",
      "disposition": "fixed",
      "rationale": "A decimal/hex/named reference producing an invisible separator and visible references producing a space or CGB letter are covered. The claim is rejected; safe encoded evidence prose and code-span examples remain accepted. Other disclosure and claim matchers are unchanged.",
      "fix_sha": "fc0ba4ff9626e06e04d8800800561b51414166bf",
      "verification_ref": "python3 -I tests/scripts/verify-v02-adoption.py --self-test-release-notes-v04 --repo . at reviewed source: PASS positives=2 controls=72; exact-source docs self-test recorded as 473/255"
    },
    {
      "id": "ADV-15",
      "category": "correctness",
      "severity": "high",
      "required_property": "CommonMark hard line breaks and visible encoded spaces are joined for unsupported-game matching in docs, notes, and notices after code masking.",
      "disposition": "fixed",
      "rationale": "LF, CR, CRLF, hard-break-plus-encoded-space, and soft-break cases have paired diagnostics and safe/code counterparts. The notices caller now passes uncollapsed visible prose to the shared matcher, closing the previously separate caller bypass.",
      "fix_sha": "e26757fafc818a92ddf7ca45f1a409658a5a5bdd",
      "verification_ref": "python3 -I tests/scripts/verify-v02-adoption.py --self-test-release-notes-v04 --repo . at reviewed source: PASS positives=2 controls=72; exact-source docs self-test recorded as 473/255; notice caller controls assert unsupported-cgb-game-qualification:THIRD_PARTY_NOTICES.md"
    },
    {
      "id": "ADV-16",
      "category": "correctness",
      "severity": "high",
      "required_property": "Visible CGB claim text split by CommonMark emphasis or inline-link labels cannot evade unsupported-game matching.",
      "disposition": "fixed",
      "rationale": "Strong and intraword stars, underscore emphasis, and claim text split through an inline-link label reject through the intended unsupported-game diagnostic. Intraword underscore text, escaped punctuation, inline/fenced code, destination-only claims, and title-only claims remain accepted.",
      "fix_sha": "e017078b72e78b38fb596faced3af3e35c2ca0ce",
      "verification_ref": "python3 -I tests/scripts/verify-v02-adoption.py --self-test-release-notes-v04 --repo . at reviewed source: PASS positives=2 controls=72; exact-source docs self-test recorded as 473/255"
    },
    {
      "id": "ADV-17",
      "category": "correctness",
      "severity": "high",
      "required_property": "Visible shortcut, full, and collapsed reference-link labels participate in unsupported-game matching while destinations and titles do not.",
      "disposition": "fixed",
      "rationale": "The current matcher resolves all three valid reference forms and rejects CGB claims split through their labels. Unresolved or escaped labels, destinations and titles containing claim text, and code spans/blocks are accepted counterparts; notice controls cover its shared caller.",
      "fix_sha": "b798781105b8f6f803e85aa2ad766d2b2fdbec22",
      "verification_ref": "python3 -I tests/scripts/verify-v02-adoption.py --self-test-release-notes-v04 --repo . at reviewed source: PASS positives=2 controls=72; exact-source docs self-test recorded as 473/255"
    },
    {
      "id": "ADV-18",
      "category": "security",
      "severity": "high",
      "required_property": "Delimiter matching must not rescan all prior unmatched runs for each closer in bounded public Markdown input.",
      "disposition": "fixed",
      "rationale": "The implementation stores opener candidates in six fixed buckets per marker, inspects those bucket tops per close run, and removes exhausted candidates. Each run is pushed and exhausted at most once and work per pairing is constant; a dense unmatched-marker control rejects the hidden claim and accepts safe evidence without timing thresholds.",
      "fix_sha": "6876fab06bf746fdaab67beaa4d52a6b1c70ac06",
      "verification_ref": "python3 -I tests/scripts/verify-v02-adoption.py --self-test-release-notes-v04 --repo . at reviewed source: PASS positives=2 controls=72; exact-source docs self-test recorded as 473/255; source inspection confirms per-marker candidate stacks rather than repeated backwards scans"
    },
    {
      "id": "ADV-19",
      "category": "correctness",
      "severity": "high",
      "required_property": "CommonMark emphasis flanking must treat Unicode punctuation and symbol categories P and S as punctuation for the unsupported-game matcher.",
      "disposition": "fixed",
      "rationale": "The source now uses Unicode categories P and S. I independently injected both `😀__CGB__ game passes all acceptance checks.` and `😀**CGB* game passes all acceptance checks.` through README, game-acceptance, notice, and renderer-built release-note production paths; each rejected with its exact unsupported-game diagnostic. Unicode-symbol safe evidence and a rule-of-three safe phrase passed, as did escaped and code-masked controls.",
      "fix_sha": "4c9c54f8b5a33e758624c997f107d1ffdd7c94a0",
      "verification_ref": "Focused exact-source production probes through check_surface/check_game, check_notices, and check_release_notes: both D-153 claims rejected on all four paths; seven safe/code controls accepted per path. CommonMark 0.31.2 §§2.1 and 6.2 define P/S punctuation and delimiter flanking."
    },
    {
      "id": "ADV-20",
      "category": "security",
      "severity": "high",
      "required_property": "Impossible nested or over-999-character reference-label candidates must be rejected before their contents are copied or normalized.",
      "disposition": "fixed",
      "rationale": "The parser pairs brackets in one stack pass and builds a prefix count in one pass. Each candidate span checks length and nested paired-opening counts in constant time before slicing; only valid labels of at most 999 characters reach case-fold normalization. The balanced 512-level bracket attack with a valid unused reference definition is rejected as unsupported CGB game qualification through README, game-acceptance, notices, and release notes; the corresponding safe evidence passes in every path. Valid shortcut/full/collapsed references remain covered and accepted/normalized as appropriate.",
      "fix_sha": "4c9c54f8b5a33e758624c997f107d1ffdd7c94a0",
      "verification_ref": "Focused exact-source production probes through check_surface/check_game, check_notices, and renderer-built check_release_notes: dense nested-bracket game claim rejected with intended diagnostic and safe prose accepted in every path; release-note controls pass positives=2 controls=72. Complexity conclusion is from the one-pass stack/prefix structure, not timing."
    }
  ]
}
```
<!-- gbb-review-evidence:end -->
