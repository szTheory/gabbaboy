# Phase 23 Release-Consumer Review

**Reviewed implementation:** `276f317d199cdd3246e9a90ce72a1f3a1235af1c`  
**Role:** release-consumer  
**Reviewer:** `codex-release-consumer-01`

I inspected the implementation, tests, release workflows, and plans at the exact reviewed commit. The release path now separates the normal inactive version-window check from the exact tracked `0.4.0` output assertion and version-PR disclosure check. The final release workflow also requires an active exact-version record and validates the release notes. These checks close RC-01 and RC-03. The mutation controls exercise the workflow pins, and the workflow-policy coverage checker binds its reviewed policy source to an immutable snapshot.

One Markdown visibility defect remains. In `tests/scripts/verify-version-window.py:300-307,310-312` and `tests/scripts/verify-v02-adoption.py:510-518`, the raw-HTML rejection pattern recognizes complete tags that end in `>`. It does not recognize a CommonMark type-1 HTML block opener such as `<script `, `<pre `, or `<style ` without a closing `>`. A changelog section can therefore contain an opener followed by `[ledger](docs/support/v0.4.0.md)` and satisfy `has_markdown_ledger_link`, even though CommonMark treats the following lines as raw HTML and does not render the link as Markdown. The same bypass works in the managed version-PR release notes. This violates the release-consumer requirement that the ledger reference be a visible Markdown link.

I replayed the prior quote/list nested-code, tab-indented code, nested link-title, adjacency/blank-line, complete raw-HTML, and hidden-attribute cases against both changelog and release-notes validation. The committed controls reject those forms. The incomplete HTML block openers remain accepted, including `<script `, `<pre `, and `<style ` followed by a newline and a valid-looking ledger link. CommonMark specifies these block openers as starting raw HTML when the tag name is followed by whitespace, `>`, or end of line, with the block continuing through the appropriate closing tag or end of document ([CommonMark 0.31.2, HTML blocks](https://spec.commonmark.org/0.31.2/#html-blocks)). RC-02 remains open; no source fix was applied in this review.

Verification at the reviewed commit:

- `python3 -I tests/scripts/verify-version-window.py --self-test-version-v04` — version-window positives and negative controls pass.
- `python3 -I tests/scripts/verify-v02-adoption.py --self-test-release-notes-v04 --repo .` — 2 positives and 54 controls pass.
- `python3 -I tests/scripts/verify-v04-release-policy.py --check --rev 276f317d199cdd3246e9a90ce72a1f3a1235af1c --repo .` and `--self-test` — policy pin passes; 11 positives and 11 controls pass.
- `python3 -I tests/scripts/verify-workflow-policy-coverage.py --self-test --root . --rev 276f317d199cdd3246e9a90ce72a1f3a1235af1c` — 94 controls pass.
- The inactive pre-freeze route accepts an inactive window while the separate tracked-output and release-note calls keep the exact `0.4.0` assertions in place.

These controls establish the behavior of their specified mutations; they do not establish review quality or close the remaining HTML-block visibility gap.

<!-- gbb-review-evidence:start -->
```json
{
  "schema_version": 1,
  "report_id": "gb-23-release-consumer-01",
  "role": "release-consumer",
  "reviewer_id": "codex-release-consumer-01",
  "independent": true,
  "reviewed_sha": "276f317d199cdd3246e9a90ce72a1f3a1235af1c",
  "findings": [
    {
      "id": "RC-01",
      "category": "correctness",
      "severity": "high",
      "required_property": "The version-PR workflows must require the exact tracked 0.4.0 generated output and validate the version-PR disclosure body, while allowing the normal inactive development window check to pass.",
      "disposition": "fixed",
      "rationale": "The committed release-please and version-pr-gate workflows keep the inactive-window check separate from --check-tracked --expect-version 0.4.0 and the trusted release-notes validator. The release policy checker confirms the exact-version and notes-call pins and their mutation controls pass at the reviewed SHA.",
      "fix_sha": "9e09eef8b379ca8d329cb13bf354058661296daa",
      "verification_ref": "At 276f317d199cdd3246e9a90ce72a1f3a1235af1c: .github/workflows/release-please.yml:131-133; .github/workflows/version-pr-gate.yml:53-55; verify-v04-release-policy.py --check and --self-test (11 positives, 11 controls); verify-version-window.py --self-test-version-v04."
    },
    {
      "id": "RC-02",
      "category": "correctness",
      "severity": "high",
      "required_property": "The changelog and version-PR release notes must contain a rendered, visible Markdown link to the exact support ledger; hidden or raw-HTML content must not satisfy the link requirement.",
      "disposition": "open",
      "rationale": "Both validators reject complete raw HTML constructs, but their regex requires a closing >. A CommonMark type-1 opener such as <script followed by whitespace and a newline is therefore accepted. The following Markdown-looking ledger link is inside a raw HTML block through its closing tag or EOF, so it is not rendered as a Markdown link. The changelog path still accepts it through validate_version_outputs and has_markdown_ledger_link; the release-notes path still accepts it through prose and check_v04_release_notes. Reproduced with <script , <pre , and <style  openers followed by a valid ledger link. See https://spec.commonmark.org/0.31.2/#html-blocks.",
      "fix_sha": null,
      "verification_ref": null
    },
    {
      "id": "RC-03",
      "category": "correctness",
      "severity": "medium",
      "required_property": "An inactive pre-freeze window must pass normal version-PR evaluation while exact generated-output and disclosure checks remain enforced separately.",
      "disposition": "fixed",
      "rationale": "At the reviewed SHA, the workflows call the inactive-window check without an expected-version pin, then run the exact tracked-output check and release-notes validator as separate required steps. The inactive fixture passes; the release policy mutation controls reject moving the exact-version pin onto the inactive-window call or omitting notes validation.",
      "fix_sha": "9e09eef8b379ca8d329cb13bf354058661296daa",
      "verification_ref": "At 276f317d199cdd3246e9a90ce72a1f3a1235af1c: verify-version-window.py --self-test-version-v04 inactive fixture; verify-v04-release-policy.py --check and --self-test (11 positives, 11 controls); .github/workflows/release-please.yml:131-133; .github/workflows/version-pr-gate.yml:53-55."
    }
  ]
}
```
<!-- gbb-review-evidence:end -->
