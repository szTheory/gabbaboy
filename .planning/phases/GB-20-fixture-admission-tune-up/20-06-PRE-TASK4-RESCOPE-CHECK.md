# Phase 20 Plan 20-06: Final-Review Rescope Review

**Reviewed revision:** `f2a0df34fb4a3c9f27cd1da28df0cbdb1cabeb5e`  
**Result:** PASS  
**Scope:** Static post-plan review of Task 3 against CR-01 and WR-01, the Phase 20 goal and RIGHTS-01, locked decisions D-01–D-03, active caps, and the existing CTest/coverage workflow.

## Decision

Task 3 covers both remaining review findings through the production product-archive path. It defines bounded decompression and pre-parser extension-metadata limits, independently checks each rejection reason, tests cleanup and same-destination retry, and refreshes the immutable source/AST/control registry contract. It does not admit a fixture, change rights dispositions or legal policy, publish anything, open another plan/gap round, or enter Phase 21.

No blocker or warning requires revision before execution.

## Findings and evidence

| Required outcome | Plan evidence | Assessment |
|---|---|---|
| Close CR-01 before tar metadata can bypass decompressed-work limits | Task 3 assigns a 1,152 MiB product decompressed-stream ceiling, 64 KiB per extension header, 4 MiB aggregate metadata, 128 extension headers, and 64 KiB reader requests. It requires the extension type/count/declared-size checks before the superclass parser consumes payloads, bounded gzip streaming, two bounded validation/extraction passes, and rejection on inventory drift. | Covered. The limits preserve the existing 1 GiB regular-payload ceiling and allow explicit header/padding headroom. |
| Prove semantic resource failures through the production gate | `_product_archive_controls` must exercise per-header, aggregate-byte, count, and decompressed-stream failures through the production extractor. Each asserts its specific `Reject` reason; setup and unrelated parse failures cannot count as success. The existing installed-product positive and allowed-metadata positive are retained. | Covered. Four independent resource negatives plus existing archive policy controls and positive cases are specified. |
| Close WR-01 and allow retry | The trusted checker is preflighted before extraction; extraction and checker invocation share cleanup handling. A valid archive with a missing trusted checker must leave the destination absent; retrying the same archive at that destination with the real trusted root must pass. Late resource/parser failures after a member is accepted must also clean up. | Covered. |
| Keep independent coverage/source authority | Task 3 pins `REVIEWED_POLICY_COMMIT` to the full immutable implementation commit and hashes its exact source bytes; it retains `BASELINE_COMMIT`, `POLICY_SHA256`, and historical AST checks. AST exceptions are limited to reviewed additions/changes. Distinct stable control marks and registry entries make each new boundary control independently required. | Covered. |
| Run the relevant registered checks at the committed head | The plan orders configure/build before CTest and reconfiguration at the committed implementation/coverage head. It runs `workflow_policy_group_release_jobs`, `workflow_policy_coverage`, `workflow_policy_coverage_controls`, the bounded-extractor self-test, and the plan-cap, planning-hygiene, and summary-coverage checks. These named CTest entries exist in the current project registration. Final full-suite, review/security, and automated closure remain the phase-level gate. | Covered. |
| Preserve authorization and rights boundaries | The action confines changes to the trusted extraction/helper/coverage files; explicitly prohibits fixture admission, legal/right changes, policy changes, unrelated cleanup, live publication, and Phase 21 work. It retains RIGHTS-01 as pending and preserves D-01–D-03. | Covered. |

## Scope and sequencing

- The plan structure check returned `valid: true`: 3 tasks, each with files, action, verification, and done criteria. The plan touches 6 files overall.
- The revised plan adds Task 3 to 20-06 in place. Phase 20 remains at its exact 9-plan cap; no tenth plan or new gap round is introduced. The four active milestone caps are 9 + 12 + 10 + 9 = 40, within the 40-plan limit.
- The 32,000-token estimate is 32% of the configured 100,000-token smart-zone budget. Confidence is low with zero completed-phase samples, so it is not calibrated; the task/file counts remain within the defined thresholds.
- Wave 5 dependencies on 20-05 and 20-07 remain correctly declared. The other Wave 5 plan, 20-09, has no shared modified files with 20-06.

## Review basis note

The target commit contains the revised plan and Phase 20 roadmap entry. The referenced final code-review report is untracked and the focused research addendum is a worktree change at this revision. I checked those current worktree artifacts to confirm the CR-01/WR-01 names and provenance; the plan itself repeats the limits, required controls, cleanup/retry behavior, and boundaries needed to execute Task 3, so their commit absence does not leave an implementation requirement unspecified.

No implementation, build, or tests were run for this static plan review.
