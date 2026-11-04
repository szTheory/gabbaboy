# Phase 23 Plan 23-04 T2 bounded rescope

**Status:** Owner approved 2026-11-04. This amends Plan 23-04 T2 in place; it adds no plan.

## Evidence and exact scope

At implementation commit `d98b4af34627dbd0d6a18d2edc2a1e93f3b3e91c`, independent review reproduced five CommonMark parsing interactions that let false CGB-game claims or required disclosures pass through Markdown metadata:

1. An explicit image label containing only spaces or tabs (`![claim][ ]`, `![claim][\t]`) fell back to the image alt label as though the suffix were the truly empty collapsed form `[]`.
2. `container_content_start()` counted a tab after a list marker as one column. In `-\t[unused]: /url` followed by a two-space continuation, it treated the continuation as a reference title even though tab expansion places the list content at column four.
3. Removing HTML comments before reference-label matching made nonmatching source labels match after comment removal. This affected explicit and shortcut image references. The correction must also preserve comment identity: `alt` and `def` comment payloads between otherwise identical label text must not collapse to the same reference label.
4. Removing a leading HTML comment before block parsing turned trailing backticks on that line into a false fenced-code opener, hiding following prose through end of document.
5. The bracket scanner treated `]` inside a URI autolink in link text as the outer link-text close. The actual inline-link title then remained visible to the checker and could supply a required disclosure.

Reviewers and the orchestrator reproduced these cases through the production `--check docs` path using disposable copies of the repository inputs. The autolink case removes all ordinary copies of the required disclosure and leaves it only in the link title.

The implementation change is limited to `tests/scripts/verify-v02-adoption.py` and its self-test controls. Correct the parser ordering and Markdown context handling for only the cases above. Do not add a parser library, dependency, release path, product claim, fixture, or unrelated source change. Preserve the existing whitespace normalization and visible/masked-copy contract. Keep the security review's separate low Git-output-bound finding explicit; this exception does not include its remediation.

## Required paired controls

- Reject all-whitespace explicit image labels when their alt text contains an unsupported game claim; accept a valid collapsed `[]` reference with a matching definition.
- Keep a two-space title continuation visible after a `-\t` marker; mask a valid continuation at the expanded list-content column.
- Keep claims visible when comments make explicit or shortcut labels differ; preserve a valid matching-comment reference and ordinary non-comment reference.
- Reject the false fence created by `<!-- -->```markdown` followed by an unclosed claim line; mask a real fenced block after an ordinary comment line.
- Reject a disclosure found only in an inline-link title when the link text contains a URI autolink with `]`; confirm a valid title after the same autolink form is masked.

Every negative must fail for its intended cause, and every paired valid case must pass. Keep the older Plan 23-09 exact-opener, malformed-title, reference-definition, and raw-HTML controls intact.

## D-145 owner-approved extension

At implementation commit `4bb708fd137f7831b9af720220a09cee57e8d47c`, security reproduced a further bypass through the production docs checker: appending `CGB\u200b game passes all acceptance checks.` to README passed with the same success summary as the baseline. U+200B is invisible and is not Python `\s`. Follow-up disposable checks also accepted U+2060 WORD JOINER and U+200C ZERO WIDTH NON-JOINER in the same position.

On 2026-11-04 the owner approved a narrow D-145 correction in the same existing T2. Normalize Unicode format-category characters only when evaluating the unsupported CGB-game claim pattern, and add causal docs and release-note controls for U+200B, U+2060, and U+200C. Include an ordinary safe-text counterpart. Preserve the D-144 parser cases, including a distinct-comment-payload reference mismatch, and do not broaden normalization to required disclosures or unrelated claim rules.

A separate inline-comment fence hypothesis was withdrawn after checking CommonMark 0.31.2: a comment that starts mid-paragraph does not meet the type-2 HTML block start condition, and a fenced block may interrupt a paragraph (§§4.5–4.6). It is not part of D-145.

## D-146 owner-approved extension

At implementation commit `742bf1bb5dd3a6e71ab93dbdb420bca2ec94d16a`, security reproduced another unsupported-game-claim bypass through the production docs checker: `CGB\u034f game passes all acceptance checks.` was accepted with the baseline summary. U+034F is a combining mark (`Mn`) with no visible display of its own; Unicode 18.0 classifies it as `Default_Ignorable_Code_Point`.

On 2026-11-04 the owner approved D-146 to extend only the unsupported CGB-game claim matcher to remove Unicode 18.0 `Default_Ignorable_Code_Point` characters, while retaining D-145's removal of all `Cf` characters. Add paired docs and release-note rejection controls for U+034F and representative non-`Cf` default-ignorable ranges, plus an ordinary safe-text counterpart. Do not normalize required disclosures or any other claim matcher. The range table is frozen to Unicode 18.0 `DerivedCoreProperties.txt`; record its version in code and keep the matcher scoped to this single claim pattern. The [Unicode 18.0 UCD](https://www.unicode.org/Public/18.0.0/ucd/DerivedCoreProperties.txt) lists U+034F as default-ignorable, and [Unicode Standard §5.21](https://www.unicode.org/versions/Unicode18.0.0/core-spec/chapter-5/) describes default-ignorable characters as having no visible fallback glyph.

## D-147 owner-approved extension

At implementation commit `a6bc0a824bce55de57422e2b6b73b94ed0f841d1`, security reproduced another bypass through the production docs checker: `CGB&#x200b; game passes all acceptance checks.` was accepted with the baseline summary. CommonMark treats valid entity and numeric character references as their corresponding Unicode characters in ordinary prose; this hexadecimal reference renders as U+200B. The [CommonMark 0.31.2 §2.5](https://spec.commonmark.org/0.31.2/#entity-and-numeric-character-references) specifies valid HTML5 named entities, decimal references, and hexadecimal references, while leaving code spans and code blocks literal.

On 2026-11-04 the owner approved D-147 to decode valid CommonMark character references only when their decoded output consists entirely of `Cf` or Unicode 18.0 `Default_Ignorable_Code_Point` characters, and only for unsupported CGB-game claim matching. Add paired docs and release-note controls for hexadecimal, decimal, and named references, including the reproduced U+200B case and a reference to U+034F. Preserve a visible-entity counterpart and code-span behavior. Do not add a Markdown/HTML parser or dependency, decode ordinary visible entity text for claim matching, or normalize required disclosures or other claim matchers.

## D-148 owner-approved extension

At implementation commit `a6bc0a824bce55de57422e2b6b73b94ed0f841d1`, security also reproduced a visible-reference bypass through the production docs checker: `CGB&#x20; game passes all acceptance checks.` was accepted with the same 473-check success summary as baseline. CommonMark renders `&#x20;` as a space, so restricting D-147 to invisible decoded characters did not cover the visible claim.

On 2026-11-04 the owner approved D-148 to decode all valid CommonMark entity and numeric character references in already-visible prose before applying the unsupported CGB-game claim matcher. Keep the change confined to that matcher; `prose()` must continue masking code spans and code blocks before it runs. Add paired docs and release-note controls for invisible hex/decimal/named references, a visible encoded space, and an encoded `CGB` letter. Keep safe visible-reference prose and code-span examples accepted. Add no parser library, and do not change the other claim matchers or disclosures.

## D-149 owner-approved extension

At implementation commit `fc0ba4ff9626e06e04d8800800561b51414166bf`, the adversarial review reproduced two production docs-checker bypasses: a claim split by a backslash hard line break before `game passes all acceptance checks.`, and the same construction followed by `&#x20;game`. CommonMark renders a backslash immediately before a line ending as a hard line break, so the phrase remains visible although the collapsed source keeps a backslash that prevents the claim matcher from joining it. The [CommonMark 0.31.2 §6.7](https://spec.commonmark.org/0.31.2/#hard-line-breaks) defines this behavior.

On 2026-11-04 the owner approved D-149 to normalize CommonMark backslash hard line breaks as whitespace only for the unsupported CGB-game claim matcher. Preserve code-span and code-block masking before matching, and do not change other claim matchers or disclosures. Add paired docs and release-note rejection controls for LF, CR, CRLF, and a hard break followed by an encoded visible space. The same matcher also runs on third-party notices, so pass that caller uncollapsed visible prose and add notice-path hard-break controls. Keep a soft-break control, safe evidence prose, and inline/fenced-code examples as valid counterparts. Add no parser library or plan, and do not reset review/gap counts or budgets.

## Phase and review limits

These owner-approved in-place exceptions do not add a plan, extend the nine-plan cap, reset review-fix/gap counts, or renew any phase budget. Plan 23-04 T2's one-time file scope remains four files: the existing validator plus its three independently owned reports. D-144 covers the five Markdown interactions above; D-145 covers literal `Cf` claim separators; D-146 covers literal Unicode 18.0 default-ignorable separators; D-147 covers references to invisible characters; D-148 extends matching to every valid CommonMark character reference in visible prose; D-149 normalizes CommonMark backslash hard line breaks only for the same claim matcher. If any further correctness/security finding remains after this bounded correction, stop T2 and obtain a new explicit owner decision before further source changes.

After the fixes, commit the implementation, set `IMPLEMENTATION_SHA` to that exact commit, and have all three independent reviewers reissue their reports at that SHA. Do not commit or qualify stale `d98b4af3` or `4bb708fd` reports. Run the full docs self-test, normal configure/build, the direct real-report gate, and Plan 23-04 T2's exact focused CTest selection. T3 remains held until all reports and mechanical gates pass.

No real CGB game or diagnostic fixture is fetched, built, run, or admitted. REL-01 remains Pending; this exception changes no release, rights, platform, hardware, or publication claim.

## Primary syntax reference

The correction follows [CommonMark 0.31.2](https://spec.commonmark.org/0.31.2/), particularly its tab-stop rules (§2.2), fenced-code block rules (§4.5), link-label rules (§6.3), and autolink/link-text precedence (§§6.3, 6.5).
