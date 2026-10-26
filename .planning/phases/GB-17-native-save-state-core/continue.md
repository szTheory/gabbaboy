# Phase 17 continuation

Completed stage: **Phase 17 execution, waves 1–3 of 11 locally verified**. Plans 17-01/02/03 are committed; full post-wave suite passes 1299/1299 at `1df0b1e`. Hosted integration fixes are in `38a86f2`; full local suite at `9d710b2` passes1299/1299. Draft PR #130 requires fresh successful current-revision hosted checks. Phase qualification and publication remain unclaimed.

Next stage: **Phase 17 — Native Save State Core, wave 4 / plan 17-04**. The prior C++ include, section-aware global scan and standalone perf version failures are locally corrected. Do not treat earlier failed hosted runs as current evidence; push/rerun current exact-head required checks. The next feature phase is **18 — Player Save Slots and Host Contract**, after this phase and owner choice.

Exact next command: `/gsd-execute-phase 17`

Read `17-01-SUMMARY.md`, `17-02-SUMMARY.md`, `17-03-SUMMARY.md`, `17-04-PLAN.md` and the existing source audit/context/research/patterns/validation. Reuse recorded decisions; do not repeat completed plans 17-01/02/03. Preserve model-gate tags on every new core function and the test-budget policy. The precodec receipt is a CTest fixture for the tracer; evidence checks still require an immutable revision while Git-free archive builds remain unqualified. The full parity loader matrix is retained with a parity-only optimized test core. Later mapper/semantic/horizon/corpus/hosted qualification remains ordered execution work.

All six STATE requirements and RM-026/028/029/030 are mapped. Eleven primary plans retain one gap slot within the cap of 12; at most two review-fix rounds and one gap round apply. A concrete scope/correctness/security overrun requires rescope, never omission or a seed. RM-027 remains a named Phase 19 entry blocker; RM-024/025 remain parked.

Both `workflow.auto_advance` and `workflow._auto_chain_active` stay false. The next feature phase is **18 — Player Save Slots and Host Contract**, after Phase 17 execution/verification and owner choice. No automatic advance.

The owner's pre-existing `.planning/config.json` edits remain uncommitted and unchanged by planning. Models/effort were passed explicitly from project configuration rather than stale installed static frontmatter.

Planning verification: all 11 structure/frontmatter checks pass; all 32 verification commands have failing directions, the path probe reports no findings (commands are outside its recognized target forms, not proof they ran), decision coverage is 25/25 and post-planning coverage 31/31. Independent review checks the unrecognized CMake commands. The four scoped CTests (`plan_cap`, `lessons_unique_ids`, `state_size`, `planning_hygiene_controls`) passed. STATE strict validation and ROADMAP validation reported no warnings. The artifact/route contract passed with controls for missing research, wrong continuation route, enabled auto-advance and missing roadmap plan; a stripped task verification is detected by runtime task flags/warnings. Configuration hash and unchanged source/test/workflow scope checks passed; `git diff --check` passed. No implementation/full-core suite, hosted state campaign, cross-platform state bytes or release is claimed.
