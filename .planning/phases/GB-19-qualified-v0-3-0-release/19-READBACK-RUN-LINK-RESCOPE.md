# Proposed D-130 — bounded final readback and repository-contract repair

Status: **OWNER-APPROVED D-130**. The owner selected “Approve bounded repair (Recommended)” for this concrete proposal. Apply only the scope below; qualification and the existing live-recovery gates remain mandatory. This grants no additional live retry or gap.

## Decision in plain language

Normal-publication readback can cite an evidence-attaching job from a different run than the release run. The final independent review reproduced that false acceptance. The complete local suite also found two hygiene defects: optional planning-document paths violate the phase-path lint, and the recovery instructions contain a Markdown example that the document checker resolves as a broken link.

**Recommendation:** approve one additional consolidated correction and independent recheck on the current corrective branch, within reserved19-08. The remedy is already tested in a disposable local prototype. It keeps the one planned corrective main merge and existing one-retry release route; it adds no plan or gap.

## Why a scope decision is required

[AGENTS.md](../../../AGENTS.md) requires: “At most 2 review-fix rounds and 1 gap round per phase. An unresolved correctness or security finding forces a rescope, never a seed.” D-102 records the same cap. The two independent recovery review rounds are recorded; the final code review still has a provenance blocker. Prior rounds and owner-approved recoveries remain historical, with no reset.

The final security audit cleared its scoped implementation checks before the peer reported the remaining normal-run linkage gap. It is not permission to ignore that later finding, failed full-suite contracts or any live gate.

## Frozen facts

- Held corrective source: `913bab5ef7f249b9240ab9b712d5cc154ded8fae`, clean and not pushed; no corrective PR has been opened.
- Main and immutable tagv0.3.0 remain productS `a3f3390451f9a893aa47475f15a722ada86daaa6`.
- Existing release429606490 is still an unpublished, non-prerelease draft with zero assets. Fresh APIs were captured at2026-10-31T02:03:13Z; no competing release run was active.
- Only the original live notes failure has occurred. No body PATCH, retry dispatch, tag/draft replacement or post-merge rehearsal push/rerun has occurred.
- The full local suite ran1706 tests with zero skips:1703 passed; `no_phase_paths`, `doc_links_versions` and `doc_links_versions_controls` failed. This is **not** a qualified revision.

## Exact bounded remedy

1. In `tests/scripts/verify-v03-dispositions.py`, require the normal attacher run ID to equal the selected release run ID. Add its negative in both working-tree and immutable-readback cases; preserve all existing normal/retry checks and diagnostics. Retry already enforces its run linkage.
2. Remove the three optional planning-file entries from that checker's corrective allowlist. Defer the three planning copies (`19-08-PLAN.md`, `COVERAGE.md`, `19-POST-TAG-FAILURE.md`) from the planned corrective Git tree to PR B. Preserve the canonical local copies byte-for-byte. The corrective S-to-G diff is then limited to the seven implementation/docs/test files; there is no phase-path lint exception or spelling workaround.
3. In `docs/release.md`, describe the exact relative URL replacement and unchanged link label as code text, without writing a Markdown-link example that resolves from the wrong directory. The actual notes-repair algorithm, two hashes and tag-pinned target stay identical.
4. In `tests/CMakeLists.txt`, bind the existing readback test to its measured108 negative controls instead of106. Keep its60-second timeout and every other budget unchanged.
5. Record the adopted scope in the existing local planning/continuation artifacts; carry the consolidated decision/proposal and deferred planning files in PR B. Do not expand the source checker to admit additional planning paths.

Runtime changes are limited to the existing readback checker, its CTest registration and release documentation. The only additional branch-file operations defer the three optional planning copies. No core/header/state/API, workflow, permission, dependency, policy-authority, performance limit, fixture thinning or source-pin change is authorized.

## Tested concrete result

Disposable prototype only: `d71af975b10d2939afb8a604cbc0c4b03397f76d`. The held source remains unchanged.

- The baseline real-repository probe accepts a mismatched normal attacher run. The prototype rejects it with `readback-attacher-run-mismatch`, while valid normal and retry records still pass using actual immutable S/prototype Git objects and the already qualified S performance receipt. Publication/API metadata remains synthetic.
- All8 affected contract CTests pass, including the readback/recovery controls, phase-path lint, both document-link checks, budget, planning labels and generic count-rejection test.
- The prototype readback self-test passes108 controls; all prior controls remain.
- The candidate phase-path lint and all86 document links pass without changing either checker.
- The complete proposed patch passes `git apply --check` against held913; that branch is still clean.

Ignored local evidence: `build/phase19-window/posttag-recovery/proposed-bounded-fix/`. The complete reviewable patch is `proposed-qualified-fix.patch` (SHA256 `69f59477c74fae10e1e412b2fd7c7bf3fa1823e83b0259128c57d3196efb83e3`). `qualification-summary.json`, contract logs and the corrected-input actual-source probe record the results. One wrapper used the wrong private perf-file path; that harness attempt was excluded and the correctly supplied actual artifact passed separately. No failed attempt is counted as a pass.

## Conditions after approval

Apply only this bounded remedy on the same held corrective branch. Obtain fresh independent code/security recheck, a complete final-head local suite, all exact-head protected hosted checks and explicit coverage for skips before the single planned guarded corrective merge. Preserve every earlier failure, source and review record. Any unrelated or unresolved correctness/security finding stops for another owner scope decision; this is not an unlimited extension.

After the qualified corrective merge, retain the existing guarded body-only repair and single pipeline retry against productS. Preserve the tag, draft identity, existing no-post-merge-rehearsal rule and all source/asset checks. A tagged product defect or a second live failure still goes to the owner. Successful recovery resumes incomplete19-07 publication/readback/PR B, then stops at `/gsd-verify-work 19`. Neither automatic advance flag changes.
