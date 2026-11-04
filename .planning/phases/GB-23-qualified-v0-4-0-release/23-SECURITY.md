# Phase 23 Security Review — Qualified v0.4.0 Release

## Review scope and conclusion

I reviewed the implementation at exact commit `276f317d199cdd3246e9a90ce72a1f3a1235af1c`, including the Phase 23 plans 23-01 through 23-04, review-evidence and version-window checkers, support-ledger/release-disclosure validation, and relevant release workflows. I focused on bounded immutable inputs, revision identity, trusted-source and package authority, and the T-23-07, T-23-08, and T-23-09 mitigations.

The final source has useful controls: blob size is checked before content is read, report and source inputs are read from immutable Git objects, qualification rejects unlisted source drift, and the release workflow binds the expected tag to the source revision. The report checker enforces declared role/schema/identity/disposition fields. Those checks do not establish reviewer quality or cryptographically authenticate reviewers; substantive independence is supplied by the separately dispatched source-reading reviewers described in Plan 23-04. I found one remaining correctness gap in the visibility gate: an incomplete raw-HTML block opener can hide a ledger link while the release-note validator accepts it. That finding remains open.

The implementation diff does not add or change package dependencies, package installation, release token permissions, or publisher authority. Workflow scope remains constrained: `version-pr-gate.yml:14,23-38,47-55` scopes the gate to the canonical same-repository version PR and treats the PR head as data; `release.yml:85-110` checks the expected tag against the exact source revision. This review does not establish hosted branch protection, live required-check status, release-please output, or downloaded package bytes.

## Findings

### SEC-23-01 — Reviewer identity authentication is outside the checker contract

**Disposition:** Rejected as a finding; not an assertion that reviewer identity is cryptographically authenticated.

Plan 23-04 explicitly separates declared report validation from substantive review quality: `23-04-PLAN.md:78-80` says the checker validates the report contract while independent source-reading reviewers perform substantive review, and `:85-90` assigns separate reviewer lanes. The checker validates declared evidence fields and `independent` (`tests/scripts/verify-review-evidence.py:142-153`) and requires distinct reviewer/report identifiers (`:318` onward). It does not authenticate an individual through a signature or external identity provider. Under the stated trust boundary, that is not a defect: the workflow obtains independence by separately dispatching reviewers who read source, not by treating the checker as an identity authority. This report likewise makes no claim of cryptographic reviewer authentication.

### SEC-23-02 — Qualification diff output is bounded before materialization

**Disposition:** Fixed in `1b7a01f30bd0b3c9330c3e633e4f60319e7b6712`.

The qualification check now uses `git diff --quiet --no-renames` with the evidence-path exclusions (`tests/scripts/verify-review-evidence.py:218-225`), so it does not capture and split an attacker-sized changed-path list. Immutable blob reads check the object size before reading (`:63-85`); the version-window checker follows the same bounded object-read pattern (`tests/scripts/verify-version-window.py:118-153`). The review-evidence self-test passed 32 positive cases and 27 controls, including accepting evidence-only qualification and rejecting README or unlisted same-phase drift.

### SEC-23-03 — Ledger-link matchers reject URL lookalikes

**Disposition:** Fixed in `9a193975fb32ae69bd09be2cf847e3271d078733`.

The changelog and adoption checkers now accept only the exact relative ledger destination or the repository’s canonical version-tag URL. The bounded URL/link parsing is in `tests/scripts/verify-v02-adoption.py:1006-1127`; the corresponding version-window link logic is in `tests/scripts/verify-version-window.py:315-429`. Controls cover query/prefix spoofing, titles, malformed destinations, and external URLs. Direct probes rejected those lookalikes and accepted the exact supported destinations.

### SEC-23-04 — Inline delimiter scanning has bounded pass behavior

**Disposition:** Fixed in `276f317d199cdd3246e9a90ce72a1f3a1235af1c`.

The inline-link parser precomputes escaped and bracket-index data and scans delimiter positions in one pass (`tests/scripts/verify-v02-adoption.py:1018-1035`; corresponding version-window helper at `tests/scripts/verify-version-window.py:320-335`). This removes repeated rescanning of suffixes for unmatched bracket input. In a direct probe, unmatched bracket inputs of 5,000, 10,000, and 20,000 characters completed in approximately 0.0004, 0.0008, and 0.0015 seconds. The version-window controls include a large unmatched-bracket case (`:1340-1350`).

### SEC-23-05 — Markdown masking covers tested containers and malformed visibility cases

**Disposition:** Fixed in `276f317d199cdd3246e9a90ce72a1f3a1235af1c` for the tested cases.

The docs checker masks comments, fenced and indented code, and inline code before evaluating visible prose, rejects unsupported raw HTML constructs, and fails closed on tabs (`tests/scripts/verify-v02-adoption.py:510-518,521-650`; raw-HTML construct pattern at `:50-52`). The version-window checker applies the corresponding tab/raw-HTML rejection to the judged changelog prefix (`tests/scripts/verify-version-window.py:300-312`). Controls exercise same-line list fences, nested quote/list fences and indented code, tabs, malformed link spacing, hidden attributes, declarations, processing instructions, CDATA, and raw HTML before the selected changelog section (`tests/scripts/verify-version-window.py:1291-1358`; docs controls at `tests/scripts/verify-v02-adoption.py:1838` onward). The docs self-test passed 466 checks, including 100 negative controls; release-note controls passed 2 positives and 54 controls; version-window controls passed 39 positives and 48 controls.

### SEC-23-06 — Incomplete raw-HTML block opener can hide release proof

**Category:** Correctness
**Severity:** High
**Disposition:** Open

The visibility gate rejects completed raw-HTML constructs, but its `RAW_HTML_CONSTRUCT` pattern requires a completed tag delimiter (`tests/scripts/verify-v02-adoption.py:50-52`; copied to `tests/scripts/verify-version-window.py:310-312`). The Markdown masking path then leaves an incomplete opener such as `<script` as ordinary prose (`verify-v02-adoption.py:510-518`), and the ledger matcher can find a Markdown link later in the raw block (`:1013-1127`). In CommonMark, a type-1 raw-HTML block may start with `<script`, `<pre`, or `<style` when the opener is followed by whitespace, `>`, or end of line; subsequent lines are raw block content and Markdown links within them are not rendered as links.

**Reproduced probe:** In a disposable committed fixture, I wrote this changelog and invoked the production `validate_version_outputs(repo, commit, "0.4.0")` path:

```markdown
# Changelog

## [0.4.0]

<script
[ledger](docs/support/v0.4.0.md)
```

The validator accepted the hidden ledger link. Direct probes also showed `<pre` and `<style` variants pass the raw-HTML pattern while the link matcher returns a match. The required property is that changelog, release-note, and public-document evidence must be visibly rendered Markdown, so content hidden in a valid raw-HTML block cannot satisfy the ledger/disclosure contract. The parser needs to reject or mask raw-HTML block openers even when the opening tag is incomplete; equivalent controls should cover script, pre, and style blocks. This finding is open at the reviewed SHA.

## Verification evidence and limits

At the reviewed source SHA, these direct controls passed:

- `python3 -I tests/scripts/verify-v02-adoption.py --self-test docs` — 466 checks, including 100 negative controls.
- `python3 -I tests/scripts/verify-v02-adoption.py --self-test-release-notes-v04 --repo .` — 2 positives, 54 controls.
- `python3 -I tests/scripts/verify-version-window.py --self-test-version-v04 --repo .` — 39 positives, 48 controls.
- `python3 -I tests/scripts/verify-review-evidence.py --self-test --rev 276f317d199cdd3246e9a90ce72a1f3a1235af1c --repo .` — 32 positives, 27 controls.
- `python3 -I tests/scripts/verify-v04-release-policy.py --self-test --rev 276f317d199cdd3246e9a90ce72a1f3a1235af1c --repo .` — 11 positives, 11 controls.

The direct production-path fixture probe above demonstrates a gap despite those controls passing. A duplicate CTest batch run during concurrent validation hit timeouts in three control targets; the parallel run is not evidence of a source failure or a pass. The direct self-tests above completed and passed. The checker schema and mechanical controls establish only their stated behavior; they do not by themselves establish review independence or overall security.

The report-evidence checker and plan address the threat boundary as follows: T-23-07 binds evidence to immutable source revision and rejects source drift; T-23-08 relies on separately dispatched reviewer lanes while checking declared report identity; T-23-09 preserves workflow authority boundaries (`23-04-PLAN.md:111-116`). Source-object bounds are explicit in `verify-review-evidence.py:63-85` and `verify-version-window.py:118-153`. The unresolved raw-HTML acceptance is the only actionable issue recorded in this bounded review pass.

<!-- gbb-review-evidence:start -->
```json
{
  "schema_version": 1,
  "report_id": "phase23-security-review-276f317d",
  "role": "security",
  "reviewer_id": "codex-security-reviewer-01",
  "independent": true,
  "reviewed_sha": "276f317d199cdd3246e9a90ce72a1f3a1235af1c",
  "findings": [
    {
      "id": "SEC-23-01",
      "category": "security",
      "severity": "low",
      "required_property": "The report checker must validate declared identity and schema fields, while substantive independence comes from separately dispatched source-reading reviewers under the plan's trust boundary.",
      "disposition": "rejected",
      "rationale": "Plan 23-04:78-90 assigns substantive source review to separate reviewer lanes and explicitly separates review quality from mechanical report validation. The checker validates declared fields but does not authenticate reviewers cryptographically; that is outside its stated authority and this review does not claim otherwise.",
      "fix_sha": null,
      "verification_ref": "23-04-PLAN.md:78-90; tests/scripts/verify-review-evidence.py:142-153"
    },
    {
      "id": "SEC-23-02",
      "category": "security",
      "severity": "medium",
      "required_property": "Qualification must reject implementation drift without buffering attacker-sized Git diff output before enforcing its bound.",
      "disposition": "fixed",
      "rationale": "The qualification check uses git diff --quiet with explicit evidence-path exclusions, avoiding materialization of the changed-path output. The immutable blob path checks size before reading; self-test controls accept evidence-only changes and reject README and unlisted same-phase drift.",
      "fix_sha": "1b7a01f30bd0b3c9330c3e633e4f60319e7b6712",
      "verification_ref": "tests/scripts/verify-review-evidence.py:63-85,218-225; verify-review-evidence self-test at reviewed SHA: 32 positives, 27 controls"
    },
    {
      "id": "SEC-23-03",
      "category": "correctness",
      "severity": "medium",
      "required_property": "Only the exact supported relative ledger destination or canonical version-tag URL may satisfy the ledger-link requirement.",
      "disposition": "fixed",
      "rationale": "Both matchers constrain accepted destinations and controls reject query/prefix lookalikes, external URLs, malformed destinations, and spoofed titles while retaining the exact supported link forms.",
      "fix_sha": "9a193975fb32ae69bd09be2cf847e3271d078733",
      "verification_ref": "tests/scripts/verify-v02-adoption.py:1006-1127; tests/scripts/verify-version-window.py:315-429; direct self-tests and URL negative controls"
    },
    {
      "id": "SEC-23-04",
      "category": "security",
      "severity": "medium",
      "required_property": "Unmatched Markdown delimiters must not cause repeated unbounded suffix rescanning during link parsing.",
      "disposition": "fixed",
      "rationale": "The parser uses precomputed escaped/bracket index data and a single delimiter-indexing pass. Direct timings scaled linearly over 5,000, 10,000, and 20,000 unmatched brackets; the version-window controls include a large unmatched-bracket input.",
      "fix_sha": "276f317d199cdd3246e9a90ce72a1f3a1235af1c",
      "verification_ref": "tests/scripts/verify-v02-adoption.py:1018-1035; tests/scripts/verify-version-window.py:320-335,1340-1350"
    },
    {
      "id": "SEC-23-05",
      "category": "correctness",
      "severity": "medium",
      "required_property": "Only visibly rendered Markdown may satisfy disclosure and ledger requirements; tested code containers, malformed links, tabs, and raw HTML constructs must fail closed.",
      "disposition": "fixed",
      "rationale": "The final implementation masks tested nested fence/indent contexts, rejects tabs and completed raw HTML constructs, and its targeted controls cover malformed links, HTML attributes, declarations, processing instructions, CDATA, and hidden disclosures. This fixed the enumerated cases but does not cover the incomplete raw-HTML block opener recorded separately as SEC-23-06.",
      "fix_sha": "276f317d199cdd3246e9a90ce72a1f3a1235af1c",
      "verification_ref": "tests/scripts/verify-v02-adoption.py:50-52,510-650,1838 onward; tests/scripts/verify-version-window.py:300-312,1291-1358; direct controls"
    },
    {
      "id": "SEC-23-06",
      "category": "correctness",
      "severity": "high",
      "required_property": "A ledger or disclosure link hidden inside a valid incomplete raw-HTML block opener must not satisfy the visible Markdown proof contract.",
      "disposition": "open",
      "rationale": "The raw-HTML pattern requires a completed tag, so a changelog containing '<script' followed by a newline and '[ledger](docs/support/v0.4.0.md)' is accepted by the production validate_version_outputs path even though CommonMark treats the subsequent lines as raw HTML content. Equivalent '<pre' and '<style' probes also evade the current raw-HTML pattern.",
      "fix_sha": null,
      "verification_ref": null
    }
  ]
}
```
<!-- gbb-review-evidence:end -->
