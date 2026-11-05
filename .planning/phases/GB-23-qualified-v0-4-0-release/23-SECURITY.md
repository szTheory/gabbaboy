# Phase 23 Security Review — Qualified v0.4.0 Release

## Review scope and conclusion

I reviewed the committed source at 0a7b2b37644f20e43da813b67561587bbd0f86e5, including the CMake-floor policy/test changes since 1f97d44fd7d43c1edc88588f404de9b9322d33fb and the T2 harness changes since aecf09cc02ae81bdb2047087014f1bc66b71aa06. I inspected the T1 report and qualification gates, the adoption and version-window validators, D-145 through D-154 Markdown claim handling, the version-PR gate, and release workflow authority and package-validation paths.

The adoption checker reads Markdown through a root-confined, size-limited UTF-8 reader. Ordinary documents are capped at 1 MiB, the historical support ledger at 8 MiB, and release notes at 256 KiB. The D-154 reference-label parser scans once to precompute paired-opening counts. Each candidate then uses the prefix counts and label-length check to reject empty, over-999-character, or nested-bracket spans before copying or normalizing them; only valid labels of at most 999 characters are normalized. D-152's emphasis matcher uses a fixed set of six candidate buckets per marker; it examines those buckets for each closing delimiter and pushes or removes each candidate at most once, so the previous repeated backward scan is gone.

I reviewed the production claim flow across game-acceptance, README, release and other required surfaces, notices, and release notes. Their caller paths pass uncollapsed visible prose with rendered inline and reference link labels exposed, after masking code spans. The matcher decodes visible CommonMark references, normalizes hard line breaks and paired emphasis, and strips literal Cf characters plus the frozen Unicode 18.0 Default_Ignorable_Code_Point ranges. D-153 correctly treats Unicode symbol categories as punctuation for delimiter flanking; the paired emoji, underscore, rule-of-three, escaped-punctuation, destination/title, and code controls cover these cases.

The T2 test-harness delta adds a docs-only `--shard INDEX COUNT` option. Argument validation permits it only with `--self-test docs` and requires a valid nonempty index range. `child_result` assigns each CLI call by its deterministic zero-based call index modulo the requested shard count; the final formula recomputes the number assigned to that shard and rejects an empty selection, a mismatch between the selected count and recorded results, or a shard without both positive and negative checks. Release-note controls run only on shard 0. CMake registers shard 0 and shards 01–31, with each output regex bound to its expected shard label and a 90-second timeout; `expected-tests.txt` and the timeout allowlist contain the corresponding names. The direct docs `--self-test docs` path remains unsharded. Each shard still walks the fixed mutation/setup inventory, while only its assigned production-CLI checks run; that is finite harness work over the bounded document set, not a new input-driven production path.

The final T2 harness changes are confined to the planning-label exception, test labels, review-evidence registration checking, the historical-path allowlist, lifecycle self-test pins, and phase-cap bookkeeping. The planning-label checker permits the v0.4 notes test's one build-tree output only when its outer CMake executable resolves to the configured `CMAKE_COMMAND`, its inner `--rev` equals the revision from the unique registered review-evidence CTest command, and its interpreter, script, flags, success regex, and sole output path match exactly. Its controls reject a different test name, output path, stale 40-hex revision, injected executable path, fake executable named `cmake`, and removal of the planning label. Both `v02` and `planning` labels are retained for the affected tests. The planning-label self-test and live inventory check passed on 1f97; the configured CTests passed 2/2.

The exact-source review-evidence self-test passed with 33 positives and 28 controls. Registration validation now counts only actual `gbb_add_v02_contract` declarations, while a duplicate declaration control still rejects duplicates; label property references no longer appear to be duplicate registrations. The historical-path scanner's new rows are exact-count pins with reasons. The pinned Phase 21/22 inputs are read by fixed revision/path/blob identities through a size-bounded immutable Git reader; review report paths are fixed, size-bounded blobs, and the additional fixture paths are in disposable committed test repositories. The phase-path scan and self-test passed on 1f97. The lifecycle recovery check now compares the live adoption checker against its immutable `aecf09cc...` blob while preserving the historical v0.3.0 source and tag. Its positive adoption paths expect 24 checks each and 97 aggregate checks; the final recovery control run passed with 99 controls and 12 positives.

The cap reconciliation keeps four phases and 38 plans within the 40-plan total: Phase 23 retains nine scheduled plans under cap 10 with one reserved gap slot, while Phase 21 moves from cap 10 to 9 without changing its eight plans or evidence. The planning-hygiene and cap controls passed. I did not run the entire focused T2 CTest selection or the direct report gate; the owner is running the remaining final gates. The production matcher and docs controls are unchanged from the previously reviewed matcher source, and no workflow file changes between aecf09cc and 1f97. These harness changes do not grant release authority or change candidate/package trust boundaries.

Since 1f97, the CMake 3.25.3 floor script keeps its focused adapter and `no_host_clock` checks on the base build, installs to the staging prefix, relocates the installation, configures/builds against it, then runs the full CTest suite once there and verifies the JUnit inventory with `--installed`. The CMake-floor policy checker parses active continued commands, counts all active CTest invocations and runner references, and requires exactly three CTest calls: the two retained base checks and one unfiltered relocated suite whose command must equal the canonical approved invocation byte-for-byte. It also requires the install/move/configure/build sequence and exactly one installed-inventory verification. Its controls reject duplicate base and relocated runs, indentation, semicolon, braced-variable, filtered, cwd-relative and bare-`ctest` forms, plus commented-out suite, adapter, clock, install, move, configure, build, or inventory commands. Filter controls cover short and long test, label, fixture, index, file-list and rerun-failed options, along with presets and show-only modes. Toolchain checks require the pinned 3.25.3 version and CMake/CTest paths under the extracted checksum-verified archive. The checker requires the exact active assignment lines, enforces one active assignment each, and pins the expected variable-reference counts; it rejects shell mechanisms that could dynamically alter those variables, including `printf -v`, `eval`, nameref and assignment builtins. It also rejects dot-sourcing with leading whitespace, in subshells, through `command`/`builtin`, or in conditionals, with paired controls for those forms. I ran the exact committed checker against the exact committed floor script; its self-test passed with 63 controls and its live policy check passed, and `bash -n` passed for the floor script. The relocated focused CTest selection passed 5/5 at this source per the orchestrator. I did not run the full CMake-floor job; no hosted floor result is claimed. These changes affect local CI test placement and policy checks only; they do not alter release workflow permissions, package validation, or publisher authority.

The de66945 delta from 4c9c54f is limited to the CMake review-evidence success regex and the matching registration-self-test expectation. Both now use one-or-more lowercase hex characters instead of a 12-character interval. The checker still validates the full reviewed commit ID and emits its first 12 hex characters in the status line; this regex only checks the test output and does not change the report identity or qualification decision. The exact-source checker self-test confirms the registration and invocation. The later T2 delta adds only docs self-test sharding and its CTest inventory/budget records; it leaves release-workflow authority and qualification evidence semantics unchanged.

The review-evidence checker resolves full commit IDs with lazy fetch and replacement objects disabled, reads fixed report blobs only after checking their size, enforces the closed schema, and uses git diff --quiet with fixed evidence exclusions for qualification drift. The version-window checker likewise uses immutable full commits, safe repository-relative paths, and size-before-read blob caps. SEC-23-09 remains open: several Git-output paths still capture data before enforcing an output bound or omit a subprocess timeout. The phase-path scanner also captures the complete `git ls-files -z` output without a timeout or output cap and reads each tracked regular file fully before scanning; this is the same low availability-hardening class, not a source-identity or policy-bypass finding.

The version-PR workflow is restricted to the canonical same-repository release-please branch, has read-only permissions, checks out the base and candidate with persisted credentials disabled, and runs trusted base checkers against the candidate as data. Release workflow checks tie tags to exact source commits. Static policy enforcement distinguishes the known residual jobs that execute tagged code from trusted judge and publisher jobs; the publisher uses the trusted workflow checkout to validate downloaded candidate bytes. This review does not claim that residual authority is closed or that hosted release checks were run.

I found no unresolved correctness or security finding. One low, non-blocking availability-hardening finding remains open. I did not inspect hosted required-check state, publish or exercise the release path, fetch/build/run/admit real fixtures, or inspect downloaded package bytes.

## Findings

### SEC-23-01 — Reviewer authentication is outside the checker contract

**Disposition:** Rejected as a finding.

Plan 23-04 assigns substantive review to separate source-reading reviewers and says the report checker validates declared identity and schema. The verifier checks the declared role, independent flag, report/reviewer identifiers, reviewed commit, and finding shape; it does not cryptographically authenticate the person behind a reviewer ID. That separation is explicit in the plan and is not represented as cryptographic authentication here.

### SEC-23-02 — Qualification diff output is not materialized

**Disposition:** Fixed in 1b7a01f30bd0b3c9330c3e633e4f60319e7b6712.

The review-evidence checker uses git diff --quiet with a fixed evidence-path exclusion list when comparing implementation and qualification commits. It does not capture an attacker-sized changed-path list. Its immutable blob reader checks object size before reading, and its self-test exercises evidence-only acceptance and source-drift rejection.

### SEC-23-03 — Ledger-link destinations reject lookalikes

**Disposition:** Fixed in 9a193975fb32ae69bd09be2cf847e3271d078733.

The release-note and version-window validators accept only the expected relative ledger path or its canonical version-tag URL. Their controls reject external URLs, query/prefix lookalikes, images, malformed links and links hidden in comments/code, while retaining visible supported destinations.

### SEC-23-04 — Unmatched Markdown delimiters have bounded scanning

**Disposition:** Fixed in 276f317d199cdd3246e9a90ce72a1f3a1235af1c.

The ledger-link parser precomputes escaped-character and bracket-index data, then processes delimiters in a single pass instead of rescanning suffixes for every unmatched bracket. The version-window self-test includes a 5,000-character unmatched-bracket control and verifies it does not create a ledger link.

### SEC-23-05 — Tested Markdown containers and malformed visibility cases fail closed

**Disposition:** Fixed in 276f317d199cdd3246e9a90ce72a1f3a1235af1c for the enumerated cases.

The validators mask comments, fenced code (including tested list and blockquote containers), indented code, and inline code. They reject tabs and unsupported raw HTML. The docs and version-window controls cover nested/container code, malformed link spacing, hidden attributes, declarations, processing instructions and CDATA. Later incomplete-HTML, inline-code phrase and attribution-row cases have separate findings.

### SEC-23-06 — Incomplete raw-HTML openers cannot hide release proof

**Disposition:** Fixed in a63f1dc67654613e105ac1071b7445f21adea0bc.

Both validators reject incomplete script, pre and style starts, declarations, and processing-instruction openers after code/comment masking. Production controls require scope-specific raw-HTML diagnostics and include a causal old-matcher fixture that accepted the hidden-link case.

### SEC-23-07 — Inline-code spans cannot supply required disclosures

**Disposition:** Fixed in c4ed9eed86871db9f9dc225565a85a55ab0a8036.

Required prose matching masks inline-code spans, while allowing exact code tokens explicitly required by a phrase. Production-path controls cover README physical-hardware limits, game-acceptance absence, release signing limits, the evidence-name clause, µCity rights scope, and a nested-backtick rights clause. Release-note controls reject an inline-code-wrapped reason and host limit.

### SEC-23-08 — Required third-party attribution rows must be visible

**Disposition:** Fixed in 05a9023bc38d487eca5de8502de4b0708165f0e8.

The notice checker requires complete visible rights/provenance wording for Libbet, Mooneye MBC, MagenTests, AGE, rtc3test, Mooneye DMG/CGB, and SameSuite. The docs controls move each required row into a fenced block and require its specific missing-disclosure diagnostic. Notice digest rows are parsed outside comments, code blocks and inline-code spans.

### SEC-23-09 — Some Git output paths can consume unbounded runner resources

**Disposition:** Open, low severity, non-blocking.

The immutable identity reader captures git show output for CMakeLists.txt and the release manifest, and git ls-tree output for docs/support, without output-size caps. Those calls have timeouts, but no output limits. The adoption checker's immutable_blob helper captures a Git blob before checking its 4 MiB limit and has no subprocess timeout; its paired ls-tree output is also unbounded. The version-window checker captures the full git diff --name-only -z output before filtering it, with no changed-path count or byte cap, although its subprocess timeout is set. The phase-path scanner captures all `git ls-files -z` output without a timeout or output cap, then reads each tracked regular file in full. The lifecycle helper also captures fixed `git show` blobs without an output cap, though those calls have timeouts. A large candidate tree or blob can increase memory/CPU use and fail a runner. These paths do not bypass source identity or release authority; the version-PR workflow is read-only and treats the candidate as data. This remains low availability hardening.

### SEC-23-10 — Visible CommonMark claim forms must normalize before qualification matching

**Disposition:** Fixed in b798781105b8f6f803e85aa2ad766d2b2fdbec22.

The claim matcher now handles Cf and frozen Unicode 18.0 default-ignorable separators, valid character references, hard line breaks, paired emphasis delimiters, and visible inline plus shortcut/full/collapsed reference-link labels. Production callers supply uncollapsed visible prose with link labels exposed and inline code masked; destinations, titles, and code remain excluded. Docs, notices and release-note controls pair emphasis/reference-link claims with escaped punctuation, unresolved references, destination/title-only claims, and inline/fenced-code counterparts.

### SEC-23-11 — Emphasis delimiter matching must stay linear on dense input

**Disposition:** Fixed in 6876fab06bf746fdaab67beaa4d52a6b1c70ac06.

The earlier emphasis normalizer searched all preceding delimiter runs for each closer, so many close-only markers caused quadratic work. D-152 replaces that scan with fixed marker/flanking/modulo buckets. Each closer checks a constant six buckets; runs are pushed or removed once, and the total delimiter characters marked is bounded by input length. Paired dense-unmatched claim and safe-prose controls exercise the docs, notices and release-note paths.

### SEC-23-12 — Unicode symbols must count as emphasis punctuation

**Disposition:** Fixed in 4c9c54f8b5a33e758624c997f107d1ffdd7c94a0.

CommonMark 0.31.2 §6.2 treats Unicode symbols as punctuation for emphasis delimiter flanking ([specification](https://spec.commonmark.org/0.31.2/#emphasis-and-strong-emphasis)). The matcher now includes Unicode P and S categories, so a symbol such as an emoji cannot prevent paired emphasis delimiters from being normalized and hide the visible claim. Paired symbol/underscore and rule-of-three claim controls reject, while safe symbol/emphasis prose remains accepted.

### SEC-23-13 — Reference-label candidate spans must avoid nested rescans

**Disposition:** Fixed in 4c9c54f8b5a33e758624c997f107d1ffdd7c94a0.

Before D-154, shortcut/reference matching copied and normalized nested candidate labels repeatedly. The checker now precomputes paired-opening counts over source text and rejects a candidate span in constant time if it is empty, over CommonMark's 999-character label limit, or contains a paired opening bracket. Those checks happen before any candidate substring is copied. Only valid labels of at most 999 characters proceed to normalization. Docs, notices and release-note controls pair dense nested-bracket claim rejection with safe-prose acceptance.

## Verification evidence and limits

The production docs matcher and release-workflow sources are unchanged from 4c9c54f8b5a33e758624c997f107d1ffdd7c94a0; the previously recorded evidence for that matcher revision includes:

- Python syntax check passed.
- Production docs check passed with 473 checks.
- The unsharded docs self-test passed with its full control inventory before the CTest-only sharding amendment.
- Release-note self-test passed with 2 positives and 72 controls.
- phase1 configure/build passed.
- Static workflow policy check passed with five residual write-authority jobs; the subsequent reviewed diff has no workflow changes.
- The earlier de66945 review-evidence self-test passed with 32 positives and 27 controls. The current T2 checker and registration were re-read and their exact-source self-test passed on 1f97 with 33 positives and 28 controls, including duplicate registration rejection.
- Direct D-153 symbol probes matched expected decisions. The D-154 constant-time rejected-span guard is supported by paired nested-bracket claim-rejection and safe-prose controls across docs, notices and release notes.

Exact-1f97 local evidence supplied by the orchestrator remains applicable to its unchanged source files: configure/build; review-evidence self-test (33 positives, 28 controls); planning-label self-test (27 controls) and live inventory (1,767 tests, 63 planning); planning-label CTests (2/2); phase-path check/self-test (597 files, 12 exact allowlists, 19 controls); plan-cap/planning-hygiene checks (4 phases, 38 plans, 96 controls); and post-tag recovery (99 controls, 12 positives). At exact 0a7b2b, I verified the CMake-floor policy self-test (63 controls), live check and Bash syntax; the relocated focused CTest selection passed 5/5 per the orchestrator. I did not run the full focused T2 CTest selection, full CMake-floor job, or direct report gate, and none is claimed here. Earlier matcher checks apply to unchanged matcher and docs-control bytes, not to the final T2 harness as a whole. These checks establish local source behavior only. No hosted evidence, release publication, real fixture operation, or downloaded-package result is claimed.

<!-- gbb-review-evidence:start -->
```json
{
  "schema_version": 1,
  "report_id": "phase23-security-0a7b2b37-20261104-codex-15",
  "role": "security",
  "reviewer_id": "codex-security-reviewer-01",
  "independent": true,
  "reviewed_sha": "0a7b2b37644f20e43da813b67561587bbd0f86e5",
  "findings": [
    {
      "id": "SEC-23-01",
      "category": "security",
      "severity": "low",
      "required_property": "Mechanical report validation must remain distinct from substantive source review and must not be represented as cryptographic reviewer authentication.",
      "disposition": "rejected",
      "rationale": "Plan 23-04 assigns substantive review to separate reviewers and the checker to declared role/schema/identity validation. The verifier validates declared fields but makes no cryptographic identity claim, so the alleged defect does not apply under the specified trust boundary.",
      "fix_sha": null,
      "verification_ref": "23-04-PLAN.md:85-90; tests/scripts/verify-review-evidence.py:142-157,318-330"
    },
    {
      "id": "SEC-23-02",
      "category": "security",
      "severity": "medium",
      "required_property": "Qualification must reject non-evidence source drift without buffering an unbounded changed-path list.",
      "disposition": "fixed",
      "rationale": "The exact source compares qualification trees with git diff --quiet --no-renames and a fixed evidence exclusion list. The immutable report reader checks size before reading. The source-bound self-test accepts evidence-only changes and rejects source drift.",
      "fix_sha": "1b7a01f30bd0b3c9330c3e633e4f60319e7b6712",
      "verification_ref": "tests/scripts/verify-review-evidence.py:71-84,218-225,254-275,401-406; exact-source self-test: 32 positives, 27 controls"
    },
    {
      "id": "SEC-23-03",
      "category": "correctness",
      "severity": "medium",
      "required_property": "Only the exact supported relative ledger destination or canonical version-tag URL may satisfy the release ledger-link requirement.",
      "disposition": "fixed",
      "rationale": "The release-note and version-window link validators constrain accepted destinations; controls reject external, lookalike, malformed, image and hidden-code links while accepting supported visible destinations.",
      "fix_sha": "9a193975fb32ae69bd09be2cf847e3271d078733",
      "verification_ref": "tests/scripts/verify-v02-adoption.py:2000-2120; tests/scripts/verify-version-window.py:318-432,1338-1364; release-note and version-window controls at reviewed source"
    },
    {
      "id": "SEC-23-04",
      "category": "security",
      "severity": "medium",
      "required_property": "Unmatched Markdown delimiters must not cause repeated suffix rescanning during ledger-link parsing.",
      "disposition": "fixed",
      "rationale": "The parser precomputes escaped-character and bracket-index data and processes delimiters without repeated suffix scans. Its unmatched-bracket control does not produce a ledger link.",
      "fix_sha": "276f317d199cdd3246e9a90ce72a1f3a1235af1c",
      "verification_ref": "tests/scripts/verify-version-window.py:318-338,1353-1364; the unmatched-bracket negative control is defined in the version-window self-test"
    },
    {
      "id": "SEC-23-05",
      "category": "correctness",
      "severity": "medium",
      "required_property": "Only visible Markdown may satisfy required disclosures and ledger clauses; tested code containers, malformed links and HTML constructs must fail closed.",
      "disposition": "fixed",
      "rationale": "The enumerated comments, fenced/indented/inline code, tabs and raw HTML are masked or rejected by the bounded validators. Later visibility cases are handled in SEC-23-06 through SEC-23-10.",
      "fix_sha": "276f317d199cdd3246e9a90ce72a1f3a1235af1c",
      "verification_ref": "tests/scripts/verify-v02-adoption.py:734-790,1404-1618; tests/scripts/verify-version-window.py:435-615; full sharded docs CTest selection at implementation source"
    },
    {
      "id": "SEC-23-06",
      "category": "correctness",
      "severity": "high",
      "required_property": "An incomplete raw-HTML block opener must not hide a required release disclosure or ledger link from rendered public proof.",
      "disposition": "fixed",
      "rationale": "Both validators reject incomplete script/pre/style starts, declarations and processing-instruction openers after code/comment masking; production controls require the scoped raw-HTML failure.",
      "fix_sha": "a63f1dc67654613e105ac1071b7445f21adea0bc",
      "verification_ref": "tests/scripts/verify-v02-adoption.py:55,734-745,2229-2244; tests/scripts/verify-version-window.py:310-315,1373-1398; reviewed-source docs and release-note controls"
    },
    {
      "id": "SEC-23-07",
      "category": "correctness",
      "severity": "high",
      "required_property": "Required natural-language disclosures must remain visible outside inline code while preserving explicitly required code tokens.",
      "disposition": "fixed",
      "rationale": "Phrase matching masks inline code except exact tokens that form part of an expected clause. The tested production paths include README, game acceptance, release limits, evidence-name wording and nested-backtick rights text.",
      "fix_sha": "c4ed9eed86871db9f9dc225565a85a55ab0a8036",
      "verification_ref": "tests/scripts/verify-v02-adoption.py:1558-1660,1990-2080; exact-source docs/release-note evidence"
    },
    {
      "id": "SEC-23-08",
      "category": "correctness",
      "severity": "medium",
      "required_property": "Every required third-party attribution row must remain visible with its source, rights, license and repository-only distribution wording.",
      "disposition": "fixed",
      "rationale": "All seven attribution rows require complete visible wording; production docs controls hide each row in a fence and require its own diagnostic, while digest rows are parsed outside comments and code.",
      "fix_sha": "05a9023bc38d487eca5de8502de4b0708165f0e8",
      "verification_ref": "tests/scripts/verify-v02-adoption.py:655-669,1948-1960; full sharded docs CTest selection at implementation source"
    },
    {
      "id": "SEC-23-09",
      "category": "other",
      "severity": "low",
      "required_property": "Git-derived blobs, repository listings, and changed-path lists should be bounded before materialization, and their subprocesses should have explicit timeouts.",
      "disposition": "open",
      "rationale": "identity_at_revision captures git show and git ls-tree outputs without output caps; immutable_blob captures a Git blob before applying its 4 MiB check and has no timeout, and its ls-tree listing is unbounded; version-window changed_paths captures the full git diff --name-only -z list without a byte/count cap; verify-no-phase-paths captures all git ls-files output and reads tracked files without per-file caps; and lifecycle git_show captures fixed blobs without an output cap. These paths can cause runner memory/time pressure, but they do not bypass source identity or release authority and the version-PR gate is read-only.",
      "fix_sha": null,
      "verification_ref": null
    },
    {
      "id": "SEC-23-10",
      "category": "correctness",
      "severity": "medium",
      "required_property": "Visible unsupported CGB-game claims must be rejected after CommonMark character, line-break, emphasis and inline/reference-link rendering, while destinations, titles and code remain excluded.",
      "disposition": "fixed",
      "rationale": "The production callers provide code-masked rendered prose and the shared matcher handles literal Cf, frozen Unicode 18.0 default-ignorables, valid character references, hard breaks, paired emphasis and inline plus shortcut/full/collapsed reference-link labels. Paired docs, notice and release-note controls reject claim forms and preserve escaped, unresolved, destination/title-only and code counterparts.",
      "fix_sha": "b798781105b8f6f803e85aa2ad766d2b2fdbec22",
      "verification_ref": "tests/scripts/verify-v02-adoption.py:232-370,734-745,780-1398,1756-1919,2229-2244; full sharded docs CTest selection including shard-0 release-note controls"
    },
    {
      "id": "SEC-23-11",
      "category": "other",
      "severity": "low",
      "required_property": "Emphasis normalization must process bounded documents without repeatedly scanning all prior delimiter runs.",
      "disposition": "fixed",
      "rationale": "The previous closer loop searched backward across earlier delimiter runs. The fixed implementation examines a constant six candidate buckets per closer and each run is inserted or removed once; paired dense unmatched-marker and safe-prose controls exercise the production paths.",
      "fix_sha": "6876fab06bf746fdaab67beaa4d52a6b1c70ac06",
      "verification_ref": "tests/scripts/verify-v02-adoption.py:260-357,226-229,3413-3426,3634-3647; full sharded docs CTest selection including shard-0 release-note controls"
    },
    {
      "id": "SEC-23-12",
      "category": "correctness",
      "severity": "medium",
      "required_property": "Unicode symbol punctuation must participate in CommonMark emphasis delimiter flanking so visible claims cannot pass between symbol-adjacent delimiters.",
      "disposition": "fixed",
      "rationale": "The delimiter classifier now recognizes Unicode P and S categories. Symbol-adjacent strong underscore and rule-of-three claim controls reject; safe symbol/emphasis prose remains accepted.",
      "fix_sha": "4c9c54f8b5a33e758624c997f107d1ffdd7c94a0",
      "verification_ref": "tests/scripts/verify-v02-adoption.py:212-217,260-305,3357-3375,3602-3608; full sharded docs CTest selection including shard-0 release-note controls"
    },
    {
      "id": "SEC-23-13",
      "category": "other",
      "severity": "low",
      "required_property": "Nested reference-label candidates must be rejected before repeated string copies or normalization, with total work bounded by document size.",
      "disposition": "fixed",
      "rationale": "The parser precomputes paired-opening counts in one pass and the span helper rejects empty, over-999-character and paired-nested-bracket spans in constant time before copying. Only short valid spans proceed to normalization; dense nested-bracket claim and safe controls cover docs, notices and release notes.",
      "fix_sha": "4c9c54f8b5a33e758624c997f107d1ffdd7c94a0",
      "verification_ref": "tests/scripts/verify-v02-adoption.py:1278-1298,1322-1389,234-240,3420-3426,3641-3647; full sharded docs CTest selection including shard-0 release-note controls"
    }
  ]
}
```
<!-- gbb-review-evidence:end -->
