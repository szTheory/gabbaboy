# Phase 23 Adversarial Review

**Reviewed implementation:** `276f317d199cdd3246e9a90ce72a1f3a1235af1c`  
**Scope:** Plans 23-01 through 23-04; immutable claim/profile validation, release-note rendering and validation, version-window validation, review-report gate, and the PR pre-freeze workflow checks.  
**Review posture:** I read the implementation at the exact reviewed SHA and replayed the controls against temporary committed fixtures or renderer-built notes. No source files were changed. The three untracked user research files were left untouched.

## Control Results

| Attack | Automated control and observed causal result |
|---|---|
| Missing or swapped candidate reasons | `verify-support-ledger.py --self-test-claims --claims-version 0.4.0` passed 22 positives and 21 controls. The missing and swapped profile reasons require `candidate-reason-missing` and `candidate-reason-mismatch`. The release-note self-test also rejects missing/swapped rendered reasons as `release-notes-candidate-source-reason-missing` and `release-notes-candidate-reason-mismatch`; each negative is preceded by an accepted renderer-built note. |
| Fabricated game execution or admission | The profile control rejects a promoted run/admission claim as `candidate-claim-promoted`. Release-note controls reject candidate execution, CGB admission, and game-evidence promotion as `release-notes-candidate-claim-promoted`, `release-notes-cgb-admission-promoted`, and `release-notes-cgb-evidence-promoted`. These are claim checks; no game was fetched, built, or run. |
| Metadata presented as diagnostic results | The profile is pinned to 513 named entries, 7 unresolved gates, 0 fixtures admitted, and 0 fixtures executed. `verify-v02-adoption.py --self-test-release-notes-v04` rejects “All 513 diagnostic microtests were executed and passed.” as `release-notes-metadata-as-diagnostic`; the support-profile controls also reject count/evidence-ID drift. |
| Omitted or contradicted Pending statuses | The release-note control rejects replacing DIAG-01 Pending and rejects an appended “DIAG-01 is complete” as `release-notes-requirement-status-promoted`. I separately removed FIXT-01, RIGHTS-01, DIAG-01, DIAG-02, and REL-01 one at a time from renderer-built notes; each rejected with that same diagnostic. The accepted counterpart retained all five statuses. |
| Hidden or contradictory disclosure clauses | Release-note controls reject closed and unclosed HTML comments, fenced code, indented code, blockquote fences, list fences, list-then-blockquote fences, blockquote-then-list fences, and inline-code spans. They also reject a false legal conclusion that the candidates' licenses prohibit repository/public-CI use as `release-notes-license-prohibition-unsupported`. Each automated mutant is paired with accepted valid notes. |
| Inline-code span variants and unmatched delimiters | The changelog controls reject same-line and multiline backtick spans containing the ledger link as `window-version-output-mismatch`; release-note controls reject same-line and multiline spans around required clauses as `release-notes-candidate-name-missing`. A direct production-check probe confirmed a renderer-built note passes with 55 checks, and the same note passes with unmatched seven-tick and mismatched two/three-tick runs on mid-line text (55 checks each); those unclosed/mismatched delimiters remain visible text. The unmatched-run variants are exploratory probes, not separately registered self-test controls. |
| Changelog ledger link spoofing | Accepted relative and canonical GitHub ledger targets pass. Image destinations, an external URL with the ledger path in its query, a path in an external-link title, and malformed destination text reject as `window-version-output-mismatch`. Equivalent release-note mutations reject as `release-notes-ledger-version-mismatch`. The fixture resets to an accepted tracked 0.4.0 counterpart before each mutated changelog. |
| Stale profile, source, or version | `verify-support-ledger.py --check-claims --claims-version 0.4.0` passed against this SHA. Its 22-positive/21-control self-test covers source/profile and historical pins. `verify-version-window.py --self-test` passed 11 positives and 64 controls; `--self-test-version-v04` passed 20 positives and 28 controls, including wrong versions, mixed outputs, wrong ledger content, hidden links, and stale bindings. |
| Historical-ledger rewrite | The support-claims controls bind the historical v0.3 support profile and tagged ledger bytes; a changed historical rendering is refused as `ledger-not-generated`. This validates byte provenance and generation; no historical tag or ledger was modified. |
| Signing and platform promotion | Release-note controls reject signing/notarization claims as `release-notes-false-signing-or-notarization-claim` and “all platforms” claims as `release-notes-false-platform-guarantee`. These are statement checks; no v0.4 release artifact was signed, notarized, or promoted in this review. |
| PR pre-freeze workflow | `verify-v04-release-policy.py --self-test` passed 11 positives and 11 controls. Its accepted inactive pre-freeze counterpart proves the normal inactive window can pass; pinning that active-window check to 0.4.0 rejects as `release-policy-inactive-window-pin`. The policy also requires a separate exact 0.4.0 tracked-output check at `$PR_HEAD` and validates the exact event PR body with the trusted notes checker. The live policy check passed, and `verify-version-window.py --check-tracked` reported `state=inactive` for the current development tree. |
| Review-evidence report gate | `verify-review-evidence.py --self-test` passed 32 positives and 27 controls. It checks immutable role/schema/identity and finding dispositions; it does not prove substantive review quality. This source-reading review is separate evidence. |
| Incomplete raw-HTML block openers | The complete-tag/declaration/PI cases reject, but incomplete `<script`, `<pre`, and `<style` openers followed by whitespace/newline, plus incomplete `<!DOCTYPE` and `<?xml` openers, pass the production changelog and release-note checks while enclosing required content. These have no present executable negative control; see ADV-09. |

## Commands and Results

The following controls were run with `--rev 276f317d199cdd3246e9a90ce72a1f3a1235af1c` where the command accepts an immutable revision:

```sh
python3 -I tests/scripts/verify-support-ledger.py --check-claims --claims-version 0.4.0 --rev 276f317d199cdd3246e9a90ce72a1f3a1235af1c --repo .
python3 -I tests/scripts/verify-support-ledger.py --self-test-claims --claims-version 0.4.0 --rev 276f317d199cdd3246e9a90ce72a1f3a1235af1c --repo .
python3 -I tests/scripts/verify-support-ledger.py --self-test-tracer --rev 276f317d199cdd3246e9a90ce72a1f3a1235af1c --repo .
python3 -I tests/scripts/verify-v02-adoption.py --self-test-release-notes-v04 --repo . --rev 276f317d199cdd3246e9a90ce72a1f3a1235af1c
python3 -I tests/scripts/verify-v02-adoption.py --self-test docs --root .
python3 -I tests/scripts/verify-version-window.py --self-test-version-v04
python3 -I tests/scripts/verify-version-window.py --self-test
python3 -I tests/scripts/verify-v04-release-policy.py --self-test --rev 276f317d199cdd3246e9a90ce72a1f3a1235af1c --repo .
python3 -I tests/scripts/verify-v04-release-policy.py --check --rev 276f317d199cdd3246e9a90ce72a1f3a1235af1c --repo .
python3 -I tests/scripts/verify-version-window.py --check-tracked --rev 276f317d199cdd3246e9a90ce72a1f3a1235af1c --repo .
python3 -I tests/scripts/verify-review-evidence.py --self-test --rev 276f317d199cdd3246e9a90ce72a1f3a1235af1c --repo .
```

Observed summaries: support claims passed; profile controls passed with 22 positives/21 controls; tracer passed with one positive/one control; release-note controls passed with 2 positives/54 controls; the docs self-test passed with 466 checks and 100 negative controls; v0.4 version controls passed with 39 positives/48 controls; the complete version-window suite passed with 11 positives/64 controls; release-workflow controls passed with 11 positives/11 controls; the live release-policy pin check passed; the current tracked record passed as inactive with 12 managed inputs; and review-evidence controls passed with 32 positives/27 controls.

The changelog destination and nested-container attacks were additionally replayed through `verify-version-window.py`'s production `validate_version_outputs` against disposable Git commits built by its `build_fixture`. The notes visibility probes used a renderer-produced v0.4 preface and the production `check_release_notes` function. Accepted baselines passed; hidden/spoofed variants returned the diagnostics listed above. These direct probes did not mutate repository source or tracked test files.

The final raw-HTML probes used production validators at the reviewed revision. A visible changelog baseline passed; prepending `<script\n`, `<pre \n`, `<style \n`, `<!DOCTYPE html\n`, or `<?xml version="1.0"\n` still passed `validate_version_outputs` with the ledger link present. The same incomplete tag openers prepended to renderer-built release notes still passed `check_release_notes` with 55 checks. Complete tags, declarations, and processing instructions reject as expected, while the incomplete openers do not emit `window-version-output-mismatch` or a release-note rejection. The README checker rejects complete raw-HTML constructs as `markdown-raw-html-unsupported`, but the incomplete block openers are not represented by a negative control. CommonMark defines these openers as HTML block starts and continues the block to the document or container end when the matching terminator is absent ([CommonMark 0.31.2, HTML blocks](https://spec.commonmark.org/0.31.2/#html-blocks)).

The pre-freeze checks validate workflow structure and disposable positive/negative cases. No live version PR, hosted workflow run, or actual release-please output was exercised here. Likewise, claim controls do not establish that a game was executed or that artifacts were signed or published.

## Findings and Dispositions

ADV-01 through ADV-08 were real bypasses in earlier reviewed Phase 23 revisions and are fixed in ancestors of the exact SHA reviewed here. ADV-09 remains open at `276f317d199cdd3246e9a90ce72a1f3a1235af1c`.

### ADV-01: Indented Markdown code satisfied release-note disclosures — fixed

Earlier notes accepted the complete required preface when every line was indented as Markdown code. Commit `9e09eef8b379ca8d329cb13bf354058661296daa` masks indented code; the accepted baseline and negative now reject through `release-notes-empty`.

### ADV-02: A Complete claim could contradict a required Pending status — fixed

Earlier notes accepted an appended positive completion claim while preserving the exact Pending sentence. The same commit added a causal contradiction control requiring `release-notes-requirement-status-promoted`.

### ADV-03: Metadata-only inventory could be described as executed diagnostics — fixed

Earlier notes accepted a claim that all 513 diagnostic microtests had executed and passed despite the zero-execution profile. The same commit added the `release-notes-metadata-as-diagnostic` control.

### ADV-04: Rights-scope no-go could be described as a license prohibition — fixed

Earlier notes accepted a legal-prohibition claim alongside the required scope disclaimer. The same commit added the `release-notes-license-prohibition-unsupported` control.

### ADV-05: Inline code and image destinations could satisfy visible disclosures — fixed

Earlier validators counted same-line/multiline inline-code contents as prose and could accept an image destination as the ledger link. Commit `9e09eef8b379ca8d329cb13bf354058661296daa` masks inline spans and distinguishes links from images; final causal controls reject hidden clauses and image destinations while accepting visible counterparts.

### ADV-06: A ledger path substring could spoof the required link — fixed

At an earlier revision, a remote URL query containing `docs/support/v0.4.0.md` satisfied the link regex. Commit `9a193975fb32ae69bd09be2cf847e3271d078733` restricts the accepted destination to the repository-relative ledger or its canonical GitHub URL. Final controls reject external-query, title, and malformed-destination cases as `window-version-output-mismatch` or `release-notes-ledger-version-mismatch`.

### ADV-07: An unclosed HTML comment could hide the remaining disclosures — fixed

At an earlier revision, a valid note prefixed with an unclosed `<!--` still passed, and a changelog link after the unclosed comment also passed. Commit `9a193975fb32ae69bd09be2cf847e3271d078733` masks an unterminated comment through end of input. The final paired controls reject the note and changelog variants.

### ADV-08: Fenced code in list and nested containers could satisfy visibility checks — fixed

At revision `9a193975fb32ae69bd09be2cf847e3271d078733`, same-line list-item backtick and tilde fences still left their contents visible to the checker. Commit `46f5ce4a515daa65bb9850a28a1ee4be9b9b8c5a` tracks list/blockquote containers while scanning fences. Final controls reject same-line backtick and tilde list fences, list-then-blockquote and blockquote-then-list fences, and the previously covered blockquote/list forms.

### ADV-09: Incomplete raw-HTML openers hide required content — open

The `RAW_HTML_CONSTRUCT` checks reject complete tags, declarations, processing instructions, and CDATA openers, but incomplete openers still pass the production visibility validators. In disposable changelog fixtures, each of `<script\n`, `<pre \n`, `<style \n`, `<!DOCTYPE html\n`, and `<?xml version="1.0"\n` before the section/link was accepted; the same incomplete tag openers inside the release-note preface left the renderer-built note accepted at 55 checks. These must cause the changelog check to reject as `window-version-output-mismatch` and release-note validation to fail closed; currently there is no executable negative control for them. The accepted baseline succeeds as well. CommonMark treats the tag/declaration/PI forms as HTML block openers, with an unclosed block extending to its end condition, so text after an opener can be hidden from readers while satisfying the checker. Add paired negative controls for each incomplete opener and require the intended raw-HTML rejection diagnostic.

## Structured Evidence

<!-- gbb-review-evidence:start -->
```json
{
  "schema_version": 1,
  "report_id": "gbb-phase23-adversarial-276f317d",
  "role": "adversarial",
  "reviewer_id": "codex-adversarial-reviewer-01",
  "independent": true,
  "reviewed_sha": "276f317d199cdd3246e9a90ce72a1f3a1235af1c",
  "findings": [
    {
      "id": "ADV-01",
      "category": "correctness",
      "severity": "high",
      "required_property": "Only visible Markdown prose may satisfy required release-note disclosures.",
      "disposition": "fixed",
      "rationale": "Earlier source accepted the full required release-note preface when indented as Markdown code. The final release-note controls accept the renderer-built baseline and reject the indented preface as release-notes-empty.",
      "fix_sha": "9e09eef8b379ca8d329cb13bf354058661296daa",
      "verification_ref": "python3 -I tests/scripts/verify-v02-adoption.py --self-test-release-notes-v04 --repo . --rev 276f317d199cdd3246e9a90ce72a1f3a1235af1c: PASS positives=2 controls=54"
    },
    {
      "id": "ADV-02",
      "category": "correctness",
      "severity": "high",
      "required_property": "Release notes must not claim a requirement is complete while also claiming that it remains Pending.",
      "disposition": "fixed",
      "rationale": "Earlier source accepted an appended DIAG-01 completion claim with the required Pending sentence intact. The final causal control rejects it as release-notes-requirement-status-promoted; omission of each of the five statuses also produced that diagnostic.",
      "fix_sha": "9e09eef8b379ca8d329cb13bf354058661296daa",
      "verification_ref": "python3 -I tests/scripts/verify-v02-adoption.py --self-test-release-notes-v04 --repo . --rev 276f317d199cdd3246e9a90ce72a1f3a1235af1c: PASS positives=2 controls=54; direct five-status omission probes rejected"
    },
    {
      "id": "ADV-03",
      "category": "correctness",
      "severity": "high",
      "required_property": "Metadata-only diagnostic inventories must not be presented as executed or passing diagnostic tests.",
      "disposition": "fixed",
      "rationale": "Earlier notes accepted an appended claim that all 513 diagnostic microtests executed and passed despite the pinned zero-execution profile. The final causal control rejects that statement as release-notes-metadata-as-diagnostic.",
      "fix_sha": "9e09eef8b379ca8d329cb13bf354058661296daa",
      "verification_ref": "python3 -I tests/scripts/verify-v02-adoption.py --self-test-release-notes-v04 --repo . --rev 276f317d199cdd3246e9a90ce72a1f3a1235af1c: PASS positives=2 controls=54"
    },
    {
      "id": "ADV-04",
      "category": "correctness",
      "severity": "high",
      "required_property": "A source/rights-scope no-go must not be reported as a legal license prohibition without evidence.",
      "disposition": "fixed",
      "rationale": "Earlier notes accepted a legal-prohibition claim beside the required scope disclaimer. The final causal control rejects that contradiction as release-notes-license-prohibition-unsupported.",
      "fix_sha": "9e09eef8b379ca8d329cb13bf354058661296daa",
      "verification_ref": "python3 -I tests/scripts/verify-v02-adoption.py --self-test-release-notes-v04 --repo . --rev 276f317d199cdd3246e9a90ce72a1f3a1235af1c: PASS positives=2 controls=54"
    },
    {
      "id": "ADV-05",
      "category": "correctness",
      "severity": "high",
      "required_property": "Inline-code content and image destinations must not satisfy visible-prose or ledger-link requirements.",
      "disposition": "fixed",
      "rationale": "Earlier source counted same-line/multiline backtick content as prose and could count an image destination as the required ledger link. The final controls reject hidden inline spans and images with their intended release-notes-candidate-name-missing or ledger-version-mismatch diagnostics, while accepting visible counterparts.",
      "fix_sha": "9e09eef8b379ca8d329cb13bf354058661296daa",
      "verification_ref": "python3 -I tests/scripts/verify-v02-adoption.py --self-test-release-notes-v04 --repo . --rev 276f317d199cdd3246e9a90ce72a1f3a1235af1c and python3 -I tests/scripts/verify-version-window.py --self-test-version-v04 --rev 276f317d199cdd3246e9a90ce72a1f3a1235af1c --repo .: PASS positives=39 controls=48; direct note probes rejected same-line, multiline, and double-backtick spans"
    },
    {
      "id": "ADV-06",
      "category": "correctness",
      "severity": "high",
      "required_property": "A required support-ledger link must target the ledger itself, not merely contain its path in unrelated URL or malformed text.",
      "disposition": "fixed",
      "rationale": "Earlier source accepted an external URL query containing docs/support/v0.4.0.md. Final controls accept the relative and canonical ledger targets and reject external-query, title, and malformed destinations for the exact ledger-link diagnostic.",
      "fix_sha": "9a193975fb32ae69bd09be2cf847e3271d078733",
      "verification_ref": "python3 -I tests/scripts/verify-version-window.py --self-test-version-v04 --rev 276f317d199cdd3246e9a90ce72a1f3a1235af1c --repo .: PASS positives=39 controls=48; python3 -I tests/scripts/verify-v02-adoption.py --self-test-release-notes-v04 --repo . --rev 276f317d199cdd3246e9a90ce72a1f3a1235af1c: PASS positives=2 controls=54"
    },
    {
      "id": "ADV-07",
      "category": "correctness",
      "severity": "high",
      "required_property": "Text hidden from Markdown by an unterminated HTML comment must not satisfy release-note or changelog requirements.",
      "disposition": "fixed",
      "rationale": "Earlier source accepted a valid note and changelog link after an unclosed HTML comment. Final controls reject both variants; the release-note diagnostic is release-notes-empty or the first missing required clause, and the changelog diagnostic is window-version-output-mismatch.",
      "fix_sha": "9a193975fb32ae69bd09be2cf847e3271d078733",
      "verification_ref": "python3 -I tests/scripts/verify-v02-adoption.py --self-test-release-notes-v04 --repo . --rev 276f317d199cdd3246e9a90ce72a1f3a1235af1c and python3 -I tests/scripts/verify-version-window.py --self-test-version-v04: PASS; both include accepted counterparts"
    },
    {
      "id": "ADV-08",
      "category": "correctness",
      "severity": "high",
      "required_property": "Fenced code nested in list and blockquote containers must not satisfy release-note or changelog visibility requirements.",
      "disposition": "fixed",
      "rationale": "At the prior fix revision, same-line list-item backtick and tilde fences still passed with hidden links. Final controls reject same-line list fences, blockquote/list nesting in both orders, and visible baselines pass; direct fixture cases return window-version-output-mismatch.",
      "fix_sha": "46f5ce4a515daa65bb9850a28a1ee4be9b9b8c5a",
      "verification_ref": "python3 -I tests/scripts/verify-version-window.py --self-test-version-v04 and python3 -I tests/scripts/verify-v02-adoption.py --self-test-release-notes-v04 --repo . --rev 276f317d199cdd3246e9a90ce72a1f3a1235af1c: PASS positives=39 controls=48 and positives=2 controls=54"
    },
    {
      "id": "ADV-09",
      "category": "correctness",
      "severity": "high",
      "required_property": "Incomplete raw-HTML block openers must not allow hidden changelog links or release-note disclosures to satisfy visibility requirements.",
      "disposition": "open",
      "rationale": "At the reviewed SHA, disposable changelog probes with <script followed by newline, <pre followed by whitespace/newline, <style followed by whitespace/newline, <!DOCTYPE html followed by newline, and <?xml followed by newline were accepted with the ledger link present. Renderer-built release notes prefixed by incomplete script/pre/style openers also passed all 55 checks. Complete constructs reject, but there is no executable negative control for these incomplete openers; accepted counterparts pass too. CommonMark 0.31.2 defines these forms as HTML block starts that can continue to the document/container end when unterminated, allowing required text to be hidden from readers.",
      "fix_sha": null,
      "verification_ref": null
    }
  ]
}
```
<!-- gbb-review-evidence:end -->
