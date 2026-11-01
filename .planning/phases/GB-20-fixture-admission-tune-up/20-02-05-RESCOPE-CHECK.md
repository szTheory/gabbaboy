# Phase 20 Follow-up Plan Check

**Commit reviewed:** `166febc79937918f9c68a1e6fa8e5b172ccab0eb`  
**Verdict:** PASS  
**Scope:** New follow-up tasks 20-02 Task 4 (T-20-07) and 20-05 Task 3 (T-20-08), plus plan-count, cap, and phase-goal boundaries.

## Findings

| Check | Result | Evidence |
|---|---|---|
| T-20-07 trusted parser boundary | PASS | Task 4 edits only `tests/scripts/verify-v02-source-archive.py`; it explicitly requires local bounded-reader and guarded-TarInfo primitives, and forbids importing or executing tagged sibling helpers or adding workflow/CLI/dependency plumbing. It retains the trusted-checker relocation and hostile-sibling controls. |
| T-20-07 limits before metadata payload parsing | PASS | Task 4 specifies bounded decompression and streaming TAR parsing; per-extension (64 KiB), aggregate (4 MiB), extension-count (128), stream (1 GiB payload ceiling plus 128 MiB), and read-request limits; pre-payload PAX/GNU checks; and bounded trailing-stream draining. It covers local/global/Solaris PAX, GNU long-name/link/sparse metadata, headers, padding, and trailing bytes. |
| T-20-07 release-path negatives | PASS | The task requires oversized metadata to reject through both the source receipt CLI and the actual core product CLI before receipt creation or product-policy evaluation, with exact resource rejection codes. The Linux release `--verify` path invokes `--check-product-archive`; the task exercises that product CLI path, and retains `v02_source_archive_controls` plus the release-candidate self-test in its verify list. |
| T-20-08 forbidden digest ordering | PASS | Task 3 requires forbidden-digest validation for every regular file before allowed, expected, generated, and `one_of` path handling, while preserving subsequent identity and path checks. |
| T-20-08 semantic production-path negatives | PASS | The task requires four isolated cases: required-generated and `one_of` paths in both core and player layouts, built through `product_tree_entries()` and rejected by `_validate_product_entries()` specifically as `product-fixture-leak`, with clean positives and exact-one alternatives preserved. Both registered product-control CTests and integration checks are listed. |
| Plan structure and wiring | PASS | OpenGSD `verify.plan-structure` returned valid for both plans. Task 4 is in 20-02's `tests/scripts/verify-v02-source-archive.py` ownership; Task 3 is in 20-05's `tests/scripts/verify-fixture-admission.py` ownership. Their file changes are disjoint. |
| Rights, fixtures, dependencies, and goal boundary | PASS | Both additions expressly preserve rights and fixture dispositions, make no legal-clearance claim, and prohibit fixture admission and dependency changes. No `depends_on` change was introduced. The Phase 20 goal and success criteria are unchanged in the commit; the roadmap diff only updates follow-up descriptions and rescope status. |
| Plan count and caps | PASS | OpenGSD reports exactly nine Phase 20 plans (`20-01` through `20-09`); the roadmap retains caps `9/12/10/9` for Phases 20–23 (40 total). The follow-ups add tasks to existing plans, not plan files or another gap round. |
| Scope estimate | PASS | Calibrated estimates: 20-02 = 42,000/100,000 tokens (low confidence, zero samples); 20-05 = 19,000/100,000 (low confidence, zero samples). Neither exceeds budget. Three earlier task records in each reopened plan are explicitly historical; only the appended follow-up task is active. |

## Summary

The plans specify the required bounded trusted TAR parser, pre-payload PAX/GNU checks, and source/Linux-core archive negatives for T-20-07. They also specify forbidden-digest precedence and semantic required/`one_of` controls for both product layouts for T-20-08. The work remains within Phase 20's existing scope and caps. No plan blocker was found.

This was a static plan review; implementation tests were not run.
