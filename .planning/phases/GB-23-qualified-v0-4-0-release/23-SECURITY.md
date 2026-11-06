# Phase 23 Security Review — Qualified v0.4.0 Release

## Scope and conclusion

I reviewed the exact committed tree at `9166ab60d25c6d246761b4aa33a0ceb35dd83f5c`, including the D-155 notice-path and self-test-copy correction, the immutable review/version-window validators, the version-PR gate, and the release/package authority paths. I read the Phase 23 execution contract, Plan 23-04 and its T2 rescope, and checked the relevant committed source and control definitions directly at that SHA.

D-155 closes the previously reproduced notice-path escape. Inline digest paths are now constrained to regular files under the resolved repository root, including after symlink resolution. Self-test input reads and copy destinations receive the same root checks; a destination is resolved again after its parent is created. The committed controls cover `..` traversal, an external symlink used as a notice input, a traversal path through `copy_inputs`, and a symlinked copy destination. I found no additional correctness or security issue in the reviewed scope. The existing low-severity availability-hardening issue SEC-23-09 remains open because several Git-output paths still lack output caps.

This review does not claim the controls were executed here, hosted checks passed, release publication was exercised, or any real fixture was fetched, built, run, or admitted. The orchestrator is running the phase gates separately.

## Input, path and source boundaries

The docs checker reads ordinary public documents through `read_bounded`: it resolves the supplied root and input path, checks that the resolved file remains beneath the root, checks the file size before reading, and requires strict UTF-8 round-tripping. The ordinary document limit is 1 MiB and the historical support ledger limit is 8 MiB. Release-note inputs use a 256 KiB bound. As intended for this offline contract checker, its file root is the explicitly supplied `--root`; the CLI resolves that directory before checking documents. A child symlink that resolves outside that chosen root is rejected.

For notices, the inline digest pattern only captures fixture-relative paths. `safe_relative_parts` rejects empty, `.` and `..` components, absolute paths, and backslashes. `notice_fixture_path` additionally requires the path to start with `fixtures/`; `confined_source_file` resolves the path strictly, verifies it is beneath the resolved source root, and requires a regular file. Fixture inventory resolution applies the same containment rule to `fixtures` and to each manifest. The digest-table manifest and license paths also use the confined reader. Thus an inline row cannot make the docs checker hash an external file by adding traversal components or a symlink whose resolved target is outside the checkout.

`copy_inputs` first validates the source notice's inline paths, then checks every source through `confined_source_file`. For each output path it resolves against the canonical target root with `strict=False`, which follows existing and dangling symlink paths, and checks containment both before and after parent creation. A static symlink under the destination therefore cannot redirect the copy outside its designated root. The D-155 controls construct an external traversal notice, an outside-target notice symlink, a traversal source for `copy_inputs`, and a symlinked destination fixture directory. These controls preserve ordinary in-root fixture files and check for external writes.

The same path can be represented with separators or aliases on different hosts, but the implementation combines component checks with the host path resolver and a post-resolution containment check. Drive-relative or other platform-specific spellings that survive the text checks still have to resolve below the canonical root. I found no static path spelling that bypasses the containment check. The helper is used to create a disposable self-test snapshot, not as an atomic copy primitive against a concurrent process that can mutate the same temporary directory.

The review-evidence checker reads fixed report blobs from full commit IDs, disables replace objects and lazy fetch, checks each Git object size before materializing its blob, and applies a 30-second timeout to Git subprocesses. It compares implementation and qualification trees with `git diff --quiet` and fixed evidence exclusions instead of buffering a changed-path list. The version-window checker likewise requires full commit IDs, disables replacements/lazy fetch, validates safe repository-relative paths, size-checks blobs before reading them, and times out Git commands. Several related paths remain less hardened and are recorded as SEC-23-09.

## Release and package authority

The version-PR gate checks out the trusted PR base separately from the version-PR head, disables persisted checkout credentials, and runs the base checkers against candidate data with read-only permissions. The release path ties the tag to the exact release-please source commit and version. The trusted workflow checkout supplies the final downloaded-package validators; the tagged tree is treated as data at the final publication gate, and publication remains a single gated transition after candidate, source, and downloaded-byte checks.

The existing workflow policy and release documentation explicitly retain residual write authority in five named release jobs while candidate code is built or release state is judged. The policy classifies and constrains those jobs; it does not claim that this residual is closed. D-155 changes neither workflows nor package/publisher authority. No new authority was introduced by the notice validator or its self-test.

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

At the preceding implementation source, a notice digest path such as `fixtures/../../...` could resolve outside the repository; `copy_inputs` used that path for both the source and isolated copy. At the reviewed source, path components are checked and the resolved source must be a regular file beneath the canonical root. Notice manifest/license paths and inline digest rows use that same confinement. Self-test source paths are validated before copy; destination symlinks are resolved and checked under the destination root before and after parent creation. The committed D-155 controls target traversal, an external symlink as a notice input, a traversal source passed through `copy_inputs`, and a symlinked copy target. I inspected these causal controls and their named expected failure paths; this review does not claim that the orchestrator's CTest execution has completed.

## Verification and limits

The source review is bound to `9166ab60d25c6d246761b4aa33a0ceb35dd83f5c`. Static inspection confirms the D-155 helpers are used by production notice hashing and self-test copying, and that the four D-155 negative paths are present in the docs self-test. I did not run CTest or the direct report gate in this reviewer turn; the orchestrator is running the approved gates. I did not inspect hosted required-check state, exercise release publication, fetch/build/run/admit real fixtures, or inspect downloaded package bytes.

<!-- gbb-review-evidence:start -->
```json
{
  "schema_version": 1,
  "report_id": "phase23-security-9166ab60-20261106-d155",
  "role": "security",
  "reviewer_id": "security-d155",
  "independent": true,
  "reviewed_sha": "9166ab60d25c6d246761b4aa33a0ceb35dd83f5c",
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
      "rationale": "identity_at_revision captures fixed Git blobs and a tree listing without output caps; adoption immutable_blob captures blob bytes before checking its 4 MiB limit and omits timeouts; version-window changed_paths captures the full diff path list; verify-no-phase-paths captures all tracked paths without timeout/output caps and reads files in full; lifecycle git_show has timeouts but no output caps. This remains a low availability-hardening concern, not a source-identity or authority bypass.",
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
      "rationale": "The previous implementation accepted traversal in a notice digest path and reused it as a copy input/output. The reviewed source rejects unsafe components, resolves source files strictly beneath the root, and resolves copy destinations beneath the target before and after creating parents. D-155 includes traversal, external-source-symlink, traversal-copy and symlinked-destination controls; this report confirms those code paths are present without claiming their CTest execution.",
      "fix_sha": "9166ab60d25c6d246761b4aa33a0ceb35dd83f5c",
      "verification_ref": "tests/scripts/verify-v02-adoption.py:1898-2005,2481-2498,3106-3129,4121-4165; D-155 source controls"
    }
  ]
}
```
<!-- gbb-review-evidence:end -->
