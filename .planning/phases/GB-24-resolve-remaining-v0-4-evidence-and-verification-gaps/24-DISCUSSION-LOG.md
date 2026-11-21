# Phase 24: Resolve remaining v0.4 evidence and verification gaps - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in `24-CONTEXT.md` — this log preserves the alternatives considered.

**Date:** 2026-11-17; updated 2026-11-20
**Phase:** 24-Resolve remaining v0.4 evidence and verification gaps
**Areas discussed:** Additive verification evidence, requirement closure with gaps, bounded recovery, Python immutable-loader execution context, source provenance, review and protected-CI controls, CI efficiency, automated verification, conditional merge, and D-209-compatible milestone closeout

---

## BOM normalization and plan-cap regression

| Option | Description | Selected |
|--------|-------------|----------|
| Strip one leading BOM and reject a repeated BOM | Normalize exactly one leading U+FEFF before the canonical frontmatter fence; fail closed if a second remains. | ✓ |
| Reject every BOM | Fail closed without normalization, which would reject BOM-prefixed plans accepted by the upstream reader. | |
| Decode all plan inputs with UTF-8-SIG | Centralize BOM removal at decoding, but changes multiple reader paths instead of the narrow classifier. | |

**User's choice:** The owner said to follow the bounded recovery recommendation after the fresh Critical review. This locks one same-plan correction and one clean independent review.

## D-206 bounded v0.4 closeout

The owner authorized a bounded closeout after asking how to finish the milestone and return to `main` through a PR. The decision reuses Phase 24's sole existing plan, preserves all eight original acceptance criteria and owners, uses only the named Potion Panic/µCity/Acid2/gbmicrotest sources, requires component-specific rights and notices before repository/public-CI staging, and spends one full exact-candidate PR CI matrix only after the candidate is frozen. Unresolved criteria remain Pending; no gap acceptance, extra plan/phase, broad local suite, additional full-CI retry, third lifecycle retest, release/tag/asset change, or unauthorized worktree removal is allowed. The exact route is `$gsd-execute-phase 24` after independent plan approval, then `$gsd-autonomous --from 24` for the remaining authorized milestone lifecycle.
**Notes:** The BOM policy stays local to the existing Python standard-library plan classifier. The independent advisor found that a repeated leading BOM must fail closed or it could remain unrecognized. Python's official [UTF-8-SIG codec documentation](https://docs.python.org/3.13/library/codecs.html#encodings.utf_8_sig) describes BOM handling at the start of the byte stream.

| Option | Description | Selected |
|--------|-------------|----------|
| Immutable production-CLI paired controls | Use the same BOM-prefixed Phase 24 plan path and fixture; vary only gap_closure true/false and require the specific D-205 gap refusal or ordinary-plan pass. | ✓ |
| Helper-only classifier control | Checks the parser helper but not immutable input, the D-205 rule, or CLI refusal behavior. | |
| Add a new CTest identity | Makes the gate surface larger despite an existing self-test and focused CTest. | |

**User's choice:** Follow the production-CLI regression recommendation and preserve the existing two CTest identities.
**Notes:** The negative must require the exact plan-cap-d205-phase24-gap refusal; the ordinary-plan twin must pass. Run only plan_cap and planning_hygiene_controls after cheap direct checks, retaining their existing timeout and control floor. A separate Critical or blocker found by the one fresh review returns the phase to the owner.

---

## Additive verification evidence

| Option | Description | Selected |
|--------|-------------|----------|
| Add focused current evidence additively | Write a commit-pinned point-in-time Phase 24 record, preserve the historical Phase 20/21 reports and stale statuses, and avoid the prohibited broad suite. | ✓ |
| Defer all freshness work to the final milestone gate | Leave the stale coverage unexplored until the exact-final-head D-103 gate. | |

**User's choice:** The owner selected this discussion area and instructed a multi-role fan-out with automatic adoption of the synthesized recommendation. The additive evidence recommendation was adopted.
**Notes:** Focused checks are not full Phase 20/21 re-verification. The broad-suite gate remains separate and unresolved.

---

## Read-only candidate research

| Option | Description | Selected |
|--------|-------------|----------|
| Repository records only | Use committed candidate and diagnostic records without new source-page research. | |
| First-party metadata for existing items | Consult only creator/upstream metadata for the existing candidates and diagnostic sources; do not fetch payloads, make a rights decision, or add candidates. | ✓ |

**User's choice:** The owner selected this discussion area and instructed automatic adoption of the synthesized recommendation. The bounded first-party metadata recommendation was adopted.
**Notes:** The Potion Panic creator page links to Codeberg and displays page-level license labels; linked Codeberg pages for Potion Panic and µCity could not be fetched by the browser. The µCity GitHub v1.3 release page exposes tag metadata and a short commit prefix. These observations do not establish payload identity, component rights, or permission.

---

## Phase exit with gaps

| Option | Description | Selected |
|--------|-------------|----------|
| Require original requirement criteria to be satisfied | Keep Phase 24 blocked until the four Pending requirements meet their original evidence criteria, which needs separate fixture/rights authority and more evidence. | |
| Complete the bounded reassessment with gaps retained | Complete Phase 24 only when its additive evidence map and controls pass; keep all four requirements Pending and v0.4 open. | ✓ |

**User's choice:** The owner selected this discussion area and instructed automatic adoption of the synthesized recommendation. The bounded reassessment recommendation was adopted.
**Notes:** Phase completion does not imply requirement satisfaction or milestone completion. The existing 40-plan total ceiling remains in force; Phase 24 has one plan slot.

---

## the agent's Discretion

- Choose existing focused CTest targets based on the covered files and claims touched by the one plan; keep identities stable and run cheap checks first.
- Use exact-commit evidence and automated negative controls to prevent false requirement-completion or milestone-closure claims.
- Reuse existing Python standard-library and CMake/CTest patterns; add no dependency without demonstrated need.

## Deferred Ideas

- Candidate-specific rights determination and any fixture/source payload acquisition, build, run, or admission require separate explicit authorization.
- The D-103 exact-final-head broad suite and v0.4 milestone archival remain separate owner-controlled gates.

---

## Post-T6 results and original-criterion reconciliation (2026-11-17)

The owner directed a full fan-out across the relevant product, rights/security, emulator/rendering, QA, architecture, and operations perspectives, and asked to follow the synthesized recommendations. Read-only source inspection and three independent criterion reviews completed. No code implementation edits, tests, emulator runs, or rights outreach occurred in this discussion.

### Acid2 mismatch: preserve the failure, separate the criterion

| Option | Description | Selected |
|--------|-------------|----------|
| Require all three profile comparisons to pass DIAG-01 | Treat the 19,840/19,840 DMG-on-CGB mismatch as a blocker for the original requirement. This matches the active plan's stricter gate but adds a condition absent from the original criterion. | |
| Apply DIAG-01 literally; track the cross-model result separately | Keep the mismatch as a failed runtime result; reconcile the requirement against admitted derivatives, glyph replacement, text mask, provenance, rights, and composition labeling. Do not claim a cross-model pass or timing qualification. | ✓ |
| Rerun, modify the mask, or change the reference | Could produce more diagnostic information but repeats a prohibited Acid2 run or changes independently pinned evidence. | |

**Owner direction:** Follow the literal-criterion recommendation. The exact DMG-on-CGB comparison remains failed. Static inspection found the recorded fixed DMG compatibility palette has no colors in common with the pinned CGB reference after RGB expansion, which can explain the all-pixel result through color encoding. Because the temporary rendered PPM was deleted and no pixel map is retained, that explanation is an inference, not a verified geometry diagnosis. The active plan's all-profile match gate must be explicitly reconciled before formal DIAG-01 status promotion; no replay, mask/reference edit, or core fix is authorized.

### RIGHTS-01 and DIAG-02

| Requirement | Option selected | Scope and boundary |
|---|---|---|
| RIGHTS-01 | Mark Complete in formal reconciliation using the admitted diagnostic alternative under D-207. | Applies only to exact admitted Acid2/gbmicrotest diagnostic components and recorded notices/package exclusions; it does not clear unadmitted games or other cases. D-207 is an owner-accepted bounded interpretation. |
| DIAG-02 | Mark Complete in formal reconciliation for the selected case and roster accounting. | One eligible/executed `div_inc_timing_a` case, 512 explicit exclusions, exact source/bytes/terms, and DMG-CPU-B software scope; no full-suite or hardware claim. |

**Owner direction:** Adopt both literal-criterion recommendations and retain their original Phase 20/22 owners. The tracker remains unchanged until the authorized formal reconciliation updates all linked records consistently.

### FIXT-01 remains the blocking owner decision

| Option | Description | Selected |
|--------|-------------|----------|
| Preserve FIXT-01 and stop with the gap visible | Keep it Pending because neither named candidate has all required build/ROM/header/mode/runtime evidence. Keep excluded inputs excluded and v0.4 open. | ✓ |
| Treat current no-go records as satisfying FIXT-01 | Would claim evidence the criterion explicitly requires but the records do not contain. | |
| Expand or relax the candidate/acceptance scope | Changes the original requirement boundary or requires using excluded material; needs a separate explicit owner decision. | |

**Owner direction:** Follow the recommendation to preserve the original criterion and Pending disposition, leaving v0.4 open. Task 7 cannot start under the current plan. No third candidate, excluded converter, unlicensed `hardware.inc`, or other gap acceptance is inferred. Revisit only if the owner later directs a material change to the FIXT-01 acceptance/scope policy.

**Additional closeout note:** `THIRD_PARTY_NOTICES.md` still contains a pre-T6 sentence saying no Acid2 comparison occurred; update it to the recorded three-profile result during any later authorized closeout. Keep the fixed compatibility palette and reference fixture untouched in the meantime.

---

## D-206 bounded closeout authorization (2026-11-16)

| Lens | Evidence / risk | Adopted direction |
|---|---|---|
| Product | The v0.4 acceptance criteria already name a bounded game pair and diagnostic sources. | Keep the original eight criteria and requirement owners; no candidate expansion or gap acceptance. |
| Rights/security | Page labels do not establish every embedded component grant; unreviewed binaries or submodules can cross the public-repository/CI boundary. | Check pinned component terms/notices first; admit only exact, rights-supported payloads. Record no-go without inferring a license ban. |
| Architecture | Existing fixture admission, CGB candidate, RGBDS, acid2 mask, diagnostic, and immutable evidence tooling already cover most seams. | Extend existing standard-library/CMake/CTest paths; add no dependencies and reuse the existing Phase 24 plan. |
| QA | Phase 20/21 reports are historical and current GSD freshness is stale; focused checks and the final suite prove different things. | Add causal negatives, keep evidence labels distinct, run cheap checks first, and use one exact final-head CI matrix for D-103. |
| Operations | Opening the current branch as a PR triggers full CI; no current PR can safely precede the closeout. | Open the PR only after the final candidate and evidence are ready; merge after independent review and required checks, then verify clean `main`. |

**Owner choice:** “Authorize bounded closeout.” D-206 records reuse of the sole Phase 24 plan, the exact named candidate set, component-level rights review, one final required CI matrix, and the 40-plan ceiling. Existing Phase 24 evidence remains historical; no requirement is complete until its original criterion passes.

**Research already underway:** canonical Potion Panic and µCity source refs and exact µCity v1.3 commit were confirmed from upstream metadata. Acid2 v1.0/v1.1 and pinned gbmicrotest root LICENSE files are MIT, but these labels do not alone resolve font, image, ROM-header, or build-input scope. Those components remain under review.

## D-211 protected CI boundary and fresh recovery (2026-11-17)

| Lens | Evidence / risk | Adopted direction |
|---|---|---|
| Product | Avoid widening the original v0.4 requirements or adding game compatibility claims. | Permit only already-admitted fixture ROM cases in the existing required PR matrix. |
| Emulator QA | The Acid2 cross-model comparison is a recorded failure and must not replay. | Keep `phase22_admission_assessment` static; Acid2 remains excluded from all execution. |
| Security / test integrity | WR-01 double-counts positives as negatives and repeats one positive. | Count only rejected overlay cases and remove the redundant positive control. |
| Operations | Required CI cannot be bypassed; a new run after failure would exceed the bounded scope. | Allow one fresh exact-candidate review and one protected matrix; merge only the identical reviewed/tested head; any blocker stops without retry. |
| Architecture | The existing checker and sole plan already provide the right seams. | Reuse them without a dependency, new CTest identity, fixture, or local ROM run. |

**User's choice:** The owner said “follow your recommendations,” authorizing the revised bounded recovery. D-211 supersedes D-210 only for the existing protected matrix's already-admitted game/fixture ROM execution and the new one-review/one-matrix allowance. Task 7, Phase 24 verification, milestone audit/archive, requirement changes, broad local suite, Acid2 replay, and release changes remain unauthorized.

**Next route:** `$gsd-plan-phase 24` to replan the same `24-01-PLAN.md`; then execute only the D-211 correction task. The current recovery checkout remains active until the protected merge is reconciled to clean `main`.

## D-212 post-matrix integrated gap scope (2026-11-17)

The owner selected the integrated recovery scope after the one D-211 protected matrix attempt exposed blockers outside Task 9. This selection authorizes scoping/planning only; no implementation, push, review, second matrix, or merge is authorized here. PR #154 remains open and frozen at `96d502d`; run `44189691301` has hard required-job failures, including the CMake-floor job, while Windows is still running its required test-inventory step. Related package-preview run `44189691412` is waiting for successful matching CI. The candidate will remain unchanged until the original attempt concludes.

### Fan-out synthesis

| Lens | Finding | Adopted constraint |
|---|---|---|
| QA / test harness | The dense-input mutant source copy has no `.git`; the separate object store contains only the fixed baseline, while fixture admission must resolve pin commits and ancestry. | Repair only the harness Git context; keep admission pin and ancestry checks strict; prove the temporary context before CMake configure. |
| Planning / product | Evidence readers still require root requirements and roadmap data although D-209 keeps v0.4 closed and stores its detailed records in the v0.4 archive. | Keep D-209 authoritative; resolve exact archived records without restoring an active root tracker or promoting requirements. |
| Emulator validation | State-fork inventory demands all manifests, but adding Acid2 and gbmicrotest as ordinary cases would execute prohibited/unapproved diagnostic ROMs. | Track the two diagnostic manifests as explicit non-executed exclusions with exact identities/reasons; do not replay Acid2, `div_inc_timing_a`, or any of the 512 excluded gbmicrotest cases. |
| Security / provenance | The workflow-policy self-test detects that the current fixture checker differs from the v0.4.0 tagged trusted snapshot. | Preserve the tagged trust root; do not waive or refresh its pin. If the overlay cannot be separated while preserving this boundary, stop and return the issue. |
| CI / operations | A single planning-hygiene self-test timed out under a parallel macOS job; dependent state-fork tests were skipped after the manifest mismatch. | Diagnose time and failure ordering; do not blindly raise the timeout. Treat dependent skips as consequences, not additional root causes. |
| Architecture / dependency policy | Existing Python/CMake/CTest seams cover the recovery; no new runtime dependency is warranted. | Reuse the sole plan and existing test identities where possible; no new dependency, fixture, or broad local suite. |

**Chosen boundary:** Plan one integrated gap round in Phase 24's existing plan. If execution is later authorized, use cheap consistency checks before focused existing CTests, then at most one fresh exact-head review and one new protected PR matrix after the original run ends. Any focused failure, unresolved review finding, undiagnosed timeout, or failed/missing/skipped/stale required context stops without another fix/review/matrix. Keep the current recovery worktree until successful protected reconciliation to clean `main`; v0.5 remains unstarted. The next command is `$gsd-plan-phase 24`.

## 2026-11-17 — D-209 owner closeout decision

The owner chose to close v0.4 with remaining gaps recorded, rather than keep the milestone open for FIXT-01. The original tracker now completes RIGHTS-01, DIAG-01, and DIAG-02 for the exact admitted diagnostic scope; FIXT-01 remains Pending. The Acid2 cross-model comparison stays failed (19,840/19,840 differing pixels) and was not replayed. Phase 24 Task 7 and D-103's exact-final-head suite remain incomplete; stale verification is disclosed. Recommend `$gsd-new-milestone` for v0.5 DMG PPU Timing.

## D-213 — Post-T10 recovery gameplan (2026-11-18)

The owner asked for a full review of three areas and directed the agent to follow the synthesized recommendations. Independent advisor reviews covered the linter contract, immutable candidate boundary, and recovery scope. The current checkout and failed T10 edits remain untouched by implementation; this record updates planning context only.

| Area | Options considered | Recommendation | Adversarial check |
|---|---|---|---|
| Path linter | Raise the per-file count to 30; suppress the target file; structurally classify the finite safe occurrences | Keep the general lexical scanner. Replace only the target file's count-only pin with a standard-library structural/context contract for immutable Git reads and disposable self-test fixtures. Keep unknown and live filesystem reads rejected. | A same-count substitution from an approved fixture to a live `open`/`Path.read_*` use must fail. Also reject a new unclassified occurrence, a changed historical path, and a changed immutable revision. |
| Candidate boundary | Read the current dirty worktree; fold the roadmap into the T10 code commit; create a planning-boundary commit first | Allow a local, unpushed documentation-only commit with the active Phase 24 root route and coherent plan/state/handoff, then require the implementation commit to descend from it. Stage only approved `.planning/` files and prove no T10 source edits were swept in. | `git show <rev>:<path>` reads the committed object. Verify the root route, sole-plan pointer, archived v0.4 inputs, and ancestry at exact commits before configure or long tests. |
| Recovery after T10 | Resume T11/T12; abandon; or replan the integrated recovery | Keep the failed T10–T12 attempt spent. Replan the sole plan for the six D-212 blockers plus the stale count and route prerequisite. In a later authorized round, allow local diagnose/fix/retest cycles until scoped checks pass; retain one final exact-head review and one protected matrix. | A new trust/correctness issue outside scope, unresolved final review finding, or missing/failed required CI context stops. Do not promote requirements, run Task 7, replay excluded ROMs, or start milestone closure. |
| CI/CD efficiency | Reduce required tests; add unmeasured caches/concurrency; shift cheap gates before long work and record observed waits | Preserve the full matrix. Preflight changed contracts locally before pushing. Record measured job/step timing and keep a separate follow-up for safe early failure of dependent preview waiters. | Keep SHA/run/attempt identity, debounce/rerun handling, artifact binding, all required contexts, and the repository's ban on `workflow_run`. |

The source records establish that T10 saw 30 path spellings against a pin of 1: 28 were in the existing candidate and two were added by T10; the two additions were removed without a rerun. The exact candidate lacks the dirty root Phase 24 route. The former D-211 protected runs are now conclusively complete: CI lasted about 70 minutes; Linux's 1,943-test stream lasted about 37 minutes and reported 44 failures; three preview consumers each waited about 70 minutes, then skipped package work after the upstream run failed. The wait behavior is measured evidence, not authority to weaken branch protection or required checks.

**Policy references:** The standing [CI/CD efficiency policy](../../context/WORKFLOW.md#cicd-efficiency) requires measured timings and cheap checks before long suites. Git's [`<rev>:<path>` syntax](https://git-scm.com/docs/gitrevisions) reads a path from a committed object. The proposed structural check can use Python's standard-library [AST module](https://docs.python.org/3/library/ast.html), but it must test actual use sites and cannot treat parsing alone as proof of safe behavior.

**Scope and next route:** Discussion and replanning only; no tests, code edits, commits, review, push, new CI, merge, phase verification, or milestone close. Reuse the existing plan with `$gsd-plan-phase 24 --skip-research`. After plan verification, the owner decides separately whether to authorize execution with `$gsd-execute-phase 24`.

## D-214 — Execution authorization (2026-11-18)

After reviewing the D-213 plan and its independent plan-check result, the owner explicitly authorized the new T10–T12 execution. This authorizes one local, unpushed planning-boundary commit from the exact plan whitelist, in-scope local diagnosis/fix/retest convergence without an arbitrary numeric cap, then at most one exact-head review and one protected PR matrix after all local checks pass. The prior D-212 T10 attempt remains stopped. D-209 statuses and gaps, Task 7 deferral, Acid2 and excluded-ROM limits, D-103, the broad-suite stop, and worktree boundary remain unchanged. Merge, Phase 24 verification, milestone audit/archive, v0.5, and cleanup are not part of this execution authorization.

**Route:** The agent runs `$gsd-execute-phase 24`, starting with the explicit-whitelist local planning-boundary commit and full-tree preflight. No D-214 source check or CI run had started when this authorization record was written.

## D-215 recovery scope and review authority (2026-11-18)

| Option | Description | Selected |
|--------|-------------|----------|
| All six findings | Correct CR-01–CR-04 and WR-01–WR-02 together in the existing Phase 24 plan. | ✓ |
| Four blockers only | Leave the two Git-context warnings unaddressed. | |
| Different scope | Owner-defined alternative. | |

**User's choice:** All six findings.
**Notes:** The candidate reviewed was `feb195f5e50eb4669b5bdb8b62e50459ec84121d`, tree `a28ca6b6644e90bde15b7ecc5c6e10bc94e7e0a6`. The review found three path-contract bypasses, a paired-archive fallback that skips current-route validation, raw pin parsing weakness, and inherited Git environment redirection.

| Option | Description | Selected |
|--------|-------------|----------|
| Request a narrow phase-local exception | Reuse the sole plan for these six findings; change no global caps and add no plan. | ✓ |
| Preserve the stop | Make no further recovery proposal. | |
| Different boundary | Owner-defined alternative. | |

**User's choice:** Request the narrow exception; this discussion authorizes planning only, not execution.

| Option | Description | Selected |
|--------|-------------|----------|
| Up to two scoped review-fix passes | Local diagnosis/retest is uncapped; if review finds scoped issues, use the second pass; stop on out-of-scope issues or unresolved findings after two. | ✓ |
| One pass, then stop | One fix/review pass for the six findings. | |
| Different bound | Owner-defined alternative. | |

**User's choice:** Up to two passes.

## D-215 protected qualification and merge boundary

| Option | Description | Selected |
|--------|-------------|----------|
| One full protected PR matrix after a clean review | Preserve every required context; stop on failed, skipped, stale, or missing contexts. | ✓ |
| Stop before CI | Do not run the new matrix. | |
| Different boundary | Owner-defined alternative. | |

**User's choice:** One full protected matrix after a clean final review.

| Option | Description | Selected |
|--------|-------------|----------|
| Conditional merge | Merge/reconcile the exact reviewed and matrix-tested head through branch protection if all required checks pass. | ✓ |
| Stop after matrix | Keep merge as a separate owner decision. | |
| Different boundary | Owner-defined alternative. | |

**User's choice:** Conditional merge to `main`; phase verification, Task 7, milestone audit/archive, D-103, and v0.5 remain separate.

## CI efficiency and required coverage

**Owner direction carried forward:** Measure actual CI job/step times, queue/dependency waits, and timeout headroom. Run cheap checks before long gates. Preserve the complete required matrix and branch protection. Record run-specific findings in Phase 24 evidence and keep package-waiter workflow redesign separate from this checker recovery. The standing policy is `.planning/context/WORKFLOW.md#cicd-efficiency`.

## D-216 — Extend and execute the four-finding recovery (2026-11-18)

The fresh independent D-215 review is bound to candidate `e1d3200b1568fb619759c0f31cf4a8605e57ea06` / tree `1dd6999e95076662c21eb79c63c4baf3188cdb1e`. It found the following exact gaps; the receipt is [D-215 review](../../../build/phase24/d215-review-e1d3200b.md):

| Finding | Risk | Recommendation | Control |
|---|---|---|---|
| Protected path built by `chr()` plus literal concatenation is invisible to the path checker's protected-value seed | A live phase path reader can evade the semantic check while adding no protected string literal | Fold only a one-argument integer-literal `chr()` call in the bounded constant evaluator; keep all other calls unresolved and fail closed at readers | Production-source mutant `Path(chr(46) + "planning/phases/private.md").read_text()` must be refused specifically as a live-phase reader; the approved source/read positives stay accepted |
| A helper named `git_run` is exempt without body inspection | An adapter can introduce a live filesystem traversal while retaining its trusted name | Validate the helper body against the narrow approved immutable-Git adapter behavior; do not treat names alone as trust | Mutate the real `git_run(*args)` body to read/traverse `(repo / args[-1])`; require a causal refusal even with lexical count held constant |
| Diagnostic boundary control inherits `GIT_DIR` and `GIT_WORK_TREE` into synthetic repo writes | Git may select or mutate a decoy/external repository during an isolation control | Isolate Git subprocesses through a small environment allowlist; leave non-Git `run()` behavior unchanged | Inject hostile vars with candidate and decoy repos; assert subject absolute Git-dir/HEAD before writes and unchanged decoy refs/index/status; restore env in `finally` |
| State-fork inventory uses newline-delimited text path output | Git quoting/splitting may omit a tracked manifest whose filename contains a newline | Enumerate with `git ls-tree -rz --name-only`, parse NUL-delimited bytes, and strictly decode manifest paths | Add a synthetic newline-bearing non-manifest positive and newline-bearing manifest negative in the existing non-executing inventory-control seam; preserve exact 153 real cases and exclusions |

**Owner choice:** “Extend and execute.” The D-215 review marked the census finding out of scope under the earlier plan; this explicit extension covers that exact finding and no broader fixture or admission work. Update the existing context and sole plan, add one same-plan correction task, execute the four corrections and focused local retests, then obtain a fresh review with the remaining two review-fix passes available for in-scope follow-up. One full protected matrix remains available only after a clean final review, and conditional merge is allowed only for the identical head with every required context passing. Existing branch protection and all prior stop conditions remain.

**Unchanged boundaries:** Do not modify the fixture specification or fixture bytes, execute any Acid2 or excluded gbmicrotest case, alter production admission policy/rights, change requirements, widen the PR matrix or change workflow triggers/coverage/timeouts/caches/concurrency. Task 7, phase verification, D-103, milestone audit/archive, v0.5 and worktree cleanup remain separate. Local checks and CTests must stay ordered cheap-to-expensive; after the protected run, use measured timings to record either a safe concrete CI efficiency change or “no justified safe change.”

**Next route:** The owner has authorized the extended correction and execution. Update/check the existing sole plan, commit the coherent planning boundary, then execute the new D-216 correction task followed by final T12 qualification. The exact handoff is `$gsd-execute-phase 24` in this same worktree.

**Independent plan check:** PASS after correcting the first review's route/status mismatch and adding T12's immutable-head dense-input control. The checker confirmed only T13 then T12 are active; T10/T11 are historical; the dense-input Git/raw-pin and exact inventory controls run against `PHASE24_D216_REV`; and all seven existing CTests, floors, timeouts, exclusions, and protected qualification limits remain consistent. This was a read-only document review; no tests, configure, build, or CI ran during planning.

## Cross-role synthesis

- **Security and static analysis:** Decode AST literal values, track protected paths through local helper arguments, and reject dynamic or parent/absolute path forms that cannot be proven beneath the temporary root.
- **Evidence integrity:** Require the archive pair and active route for current candidates; permit historical checks only at an explicit full-revision boundary.
- **Git reliability:** Validate pin blobs as raw bytes containing exactly 40 lowercase hex ASCII bytes, optionally followed by LF or CRLF (or with no terminator); reject bare CR and any extra/invalid bytes. Sanitize repository-redirection environment variables and assert the temporary subject repository identity.
- **QA and CI operations:** Add causal positive and negative controls in existing CTest/self-test seams, run cheap checks first, preserve full matrix membership, and inspect measured run timing rather than changing coverage by guesswork.
- **Dependency policy:** Reuse Python standard-library AST/path tools and Git; add no package or CTest identity.

## D-218 — Three-blocker recovery discussion and owner authorization (2026-11-18)

D-217's final independent review of `4239a8bdb0ddd33d0904c8e05eb30bc5787302fb` found three blockers in the path checker's proof of runtime trust and revision identity. The owner directed the agent to fan out, synthesize the best bounded recovery, and proceed under that recommendation.

### Fan-out findings

| Lens | Recommendation | Trade-off considered |
|---|---|---|
| Security / namespace trust | Fail closed on reflective namespace writes that can replace the approved Git adapter, including direct namespace-dict methods and builtin-dict forms; reject reflective mutation of the imported regex module regardless of attribute key. | This may refuse future reflection in the proof-bearing checker, which is preferable to silently trusting mutable runtime bindings; general alias analysis would be larger and harder to audit. |
| Python / AST semantics | Explicitly model the finite binding fields in `MatchAs`, `MatchStar`, and `MatchMapping.rest`; verify the exact validated revision passes through the known helper chain and guard again at the archive Git-reader boundary. | A closed helper-specific contract requires deliberate maintenance if the route changes, but avoids building a broad Python data-flow engine or adding a dependency. |
| QA / recovery governance | Add causal controls for all three issues, preserve the seven existing focused tests and their time limits, use one clean independent go/no-go review, then one protected matrix; stop after any blocker. | One new explicit exception acknowledges the spent D-217 limit without converting it into a general cap increase or retry loop. |
| CI / release operations | Measure queue, job/step and dependency waits, timeout headroom, and package-step behavior during the protected matrix; retain full coverage and existing release gates. | Make efficiency changes only when the run data proves a safe improvement; keep the package-waiter redesign separate. |

The Python primary sources confirm that `globals()` exposes the current module namespace dictionary, `setattr` mutates the selected attribute, and match patterns bind names. Links and implementation implications are recorded in the D-218 section of `24-CONTEXT.md` and the D-218 addendum in `24-RESEARCH.md`.

### Adopted D-218 scope

The owner authorizes one correction in the two existing checkers `verify-no-phase-paths.py` and `verify-planning-hygiene.py`, causal positive/negative controls, the same seven focused CTests, one new independent exact-head review, one protected PR matrix only after a clean review, and conditional protected merge of that identical head if all required checks pass. Any review blocker or failed/skipped/stale/missing required context stops without another correction, review, or matrix. This is a one-time Phase 24 exception, not a global allowance reset.

No new plan, dependency, analyzer framework, CTest identity, source payload, fixture, admission change, release change, broad suite, Acid2/ROM replay, Task 7, Phase 24 verification, milestone audit/archive, v0.5 start, or worktree cleanup is authorized. Keep FIXT-01 Pending, all D-209 dispositions, the D-217 blocked review, D-211 failures, and D-103 unchanged.

The CI/CD efficiency policy is already discoverable from `AGENTS.md` through `.planning/context/WORKFLOW.md#cicd-efficiency`; D-218 requires measured run evidence, preserves all required contexts, and does not authorize speculative workflow changes.

**Next route:** The sole plan was revised as T14 correction followed by T12 qualification. Independent plan checking passed with no findings. Commit the reviewed D-218 planning boundary, run its immutable-route preflight, then execute `$gsd-execute-phase 24` in this worktree. Phase 24 and v0.4 remain open.

## D-219 — Integrated recovery after the D-218 NO-GO

**Date:** 2026-11-18
**Areas discussed:** Python proof boundary and revision integrity; Git environment isolation and inventory-mode CLI; bounded recovery and CI efficiency

### Python proof boundary and revision integrity

| Option | Description | Selected |
|---|---|---|
| Alias/provenance tracking | Resolve arbitrary Python import aliases, function-global references, scopes, and value flow | |
| Closed AST contract | Reject unmodeled aliases/reflection in the fixed proof surfaces, refactor global-mutating self-tests, and preserve exact positive/negative controls | ✓ |
| General analysis dependency | Add a broad static-analysis library to model Python semantics | |

**Owner's direction:** Follow the synthesized recommendation. Keep the proof surface finite and standard-library-only. Close aliased `import_module`, function `__globals__`, reflective archive-pin writes, and revision rebinding at every protected Git reader. Refactor test fixtures away from module-global mutation where practical.

### Git environment isolation and inventory-mode CLI

| Option | Description | Selected |
|---|---|---|
| Working-directory isolation | Rely on `-C` and expected repository layout | |
| Minimal Git environment | Keep explicit `--no-replace-objects`, remove Git-controlled repository/index/object redirection, assert the subject object identity, and reject inventory-mode conflicts before side effects | ✓ |
| General Git wrapper | Add a broad wrapper abstraction around every Git invocation | |

**Owner's direction:** Apply the recommendation across affected checker adapters. Retain replacement-ref protections, add decoy/index/object redirection controls, and ensure state-fork inventory mode rejects all conflicting operations and mode-specific inputs before Git or output effects.

### Bounded recovery and CI efficiency

| Option | Description | Selected |
|---|---|---|
| One correction/review pass | Lowest review cost; a new finding ends the attempt | |
| Up to two correction/review passes | One in-scope re-review if the first D-219 candidate review finds a fixable in-scope issue; keep hosted matrix to one clean-review-gated run | ✓ |
| Multiple protected matrices | Retry hosted qualification after a failure | |

**Owner's direction:** Follow the two-pass recommendation, consistent with the owner's prior up-to-two-pass choice. The D-218 NO-GO is historical and does not consume this new exception. Use one protected matrix after a clean final review, and merge only the same reviewed/passing head through branch protection. The user's earlier “extend and execute” authorization applies after the sole plan is updated, independently checked, and committed. Preserve all other stop conditions.

**CI efficiency:** D-218 did not reach CI, so no current timing or optimization claim is available. If the authorized matrix runs, record actual queue, job/step, dependency-wait, package-step, and timeout-headroom data. Keep the existing `.planning/context/WORKFLOW.md#cicd-efficiency` policy and required coverage; make no speculative workflow changes. The D-211 package-waiter redesign remains separate.

**Deferred:** No broader analyzer, dependency, CTest identity, CI topology change, Task 7, Phase 24 closure, milestone audit/archive, v0.5 start, or worktree cleanup.

**Next route:** Update and independently check the sole Phase 24 plan with D-219's integrated findings, commit the planning boundary without `.planning/state.json`, then execute only the scoped recovery and existing focused qualification. The current handoff is `$gsd-plan-phase 24` in this worktree.


## D-220 — Scope-bounded convergence after D-219 pass-two NO-GO

| Option | Description | Selected |
|--------|-------------|----------|
| Scope-bounded convergence | Reuse the same six-checker trust boundary; let local corrections and exact-head review converge on evidence without a numeric pass cap; retain one matrix only after a clean review. | ✓ |
| One more fixed correction/review cycle | Permit one final attempt, then stop even if the same invariant remains open. | |
| Keep the NO-GO stop | Make no further recovery proposal. | |

**User's choice:** Scope-bounded convergence.
**Notes:** The D-219 two-pass allowance is exhausted. This selection authorizes updating context and replanning only, not code changes or CI. Keep each cycle tied to a concrete review finding or failing causal control and a changed candidate; stop for owner discussion if scope expands, a correction makes no concrete progress, or a new dependency/test identity/broader claim is required. A fresh independent exact-head review remains mandatory before the one protected matrix; a failed, skipped, stale, or missing required context ends that matrix route without retry. Conditional merge applies only to the identical reviewed and fully passing head under branch protection.

### Cross-role synthesis

| Lens | Recommendation |
|---|---|
| Security / Python runtime | Reject unmodeled dynamic namespace access in the proof-bearing source; do not grow an exact-spelling blacklist. Python documents arbitrary string names for `getattr` and write-through optimized-scope `frame.f_locals` since 3.13 ([`getattr`](https://docs.python.org/3.14/library/functions.html#getattr), [PEP 667](https://peps.python.org/pep-0667/)). |
| Test design | Add source-only causal mutants for aliased `getattr` plus split names targeting `git_run` and the D-209 pin, and post-guard local mutation in `read_rev`, `commit_snapshot`, and `immutable_blob`; assert the intended refusal before Git access and keep approved positives. |
| Maintainability | Keep the existing Python standard-library AST contract; avoid a general alias-analysis dependency and preserve all six checker boundaries. |
| CI / operations | Run cheap source/scope checks before the same seven focused CTests, then review the frozen exact head. Do not spend hosted CI before clean review; measure real job and wait timings if the matrix runs. |

**Retained limits:** one existing Phase 24 plan; same six checker files plus additive closeout evidence; no new dependency, CTest identity, timeout, weakened control floor, broad suite, ROM/fixture/Acid2 replay, Task 7, phase/milestone closure, v0.5, or worktree cleanup. D-209 dispositions remain unchanged; FIXT-01 stays Pending and Acid2 remains failed/unreplayed.

**Next route:** `$gsd-plan-phase 24` updates the existing plan. Execution requires a separately authorized handoff after plan review.


## D-221 failure-informed recovery scope

**Date:** 2026-11-19
**Areas discussed:** portable hosted-test failures; exact-head package-waiter efficiency; bounded qualification authority

| Option | Description | Selected |
|--------|-------------|----------|
| Raise the path timeout or trim controls | Quickest way to suppress one failure, but hides variance or reduces coverage | |
| Preserve 201 controls and current timeout; remove measured duplicate work | Diagnose first and reuse the existing parsed AST only where it addresses the measured hot path | ✓ |
| Rebuild the Git fixture with an owned object database | Avoid alternates and verify the exact pinned commit is available | ✓ |
| Keep a filesystem newline filename | Works on POSIX but cannot be created on Windows for control characters | |
| Represent the newline path directly in Git index/tree data | Retain the manifest refusal contract without an OS-invalid file | ✓ |
| Wait only for the final aggregate | Preserves semantics but repeats 69–73 minutes of known package-runner waste | |
| Fail fast on a debounced exact-head required-component failure | Saves wait time but keeps aggregate/player success as the only path to package work | ✓ |
| One new protected matrix candidate | Cheapest, but an unrelated in-scope platform failure would stop recovery again | |
| Up to two changed, reviewed matrix candidates | Permit one concrete in-scope correction after the first new matrix; never replay an unchanged head | ✓ |
| Uncounted matrix convergence | Allows ongoing recovery but leaves hosted compute spend open-ended | |

**Owner's choice:** Follow the recommendation and use up to two matrix candidates under D-221. The second is permitted only after a concrete in-scope failure, a causal fix, focused qualification, and fresh independent code/security review of the changed candidate. No execution or matrix has yet been authorized by this discussion response; the plan must be updated and independently checked first.

### Cross-role synthesis

| Lens | Recommendation | Trade-off |
|---|---|---|
| Test engineering | Preserve all 201 path controls and the 60-second timeout; remove demonstrated duplicate parsing before considering broader optimization. | Reusing AST state needs source/tree identity discipline; profiling must confirm it addresses runtime variance. |
| Windows/Git portability | Own the required pinned object in the temporary fixture; exercise newline paths through Git index/tree plumbing. | More fixture setup, but deterministic across OS filesystems and no missing alternate object store. |
| CI operations | Debounce current-attempt component failures and stop preview waiters early; require aggregate and player receipts for success. | Polling can save runner time; incomplete API data must still wait and fail closed at the existing deadline. |
| Security/release | Preserve all three protected contexts, exact-head binding, artifact receipts, and branch protection. | No gate reduction; only earlier failure reporting changes. |
| Product/scope | Keep this in Phase 24's sole plan and preserve D-209/v0.4 closeout dispositions. | Fixes the blocked closeout path without reopening FIXT-01 or v0.5. |

**Deferred:** No matrix topology, required-context, timeout, trigger, cache or concurrency change; no dependency, new CTest identity, broad suite, ROM replay, Task 7, phase closure, milestone closure, v0.5 start or worktree cleanup.

## D-222 — Enforceable promotion gate after the D-221 review stop

**Date:** 2026-11-20
**Areas discussed:** trusted promotion boundary; exact-head review and CI evidence; bounded repair of the fresh review findings

| Option | Description | Selected |
|---|---|---|
| Keep D-221 stopped | Preserve the rejected 9bab candidate and do not attempt to qualify it | |
| Replan integrated gate | Add an executable, least-privilege promotion guard to the sole Phase 24 plan; fix the two direct review defects and preserve existing contexts and candidate cap | ✓ |

**Owner's choice:** Replan integrated gate.
**Notes:** The owner authorized updating and independently checking the sole Phase 24 plan. The previously authorized GSD Autonomous route continues only within the expanded boundary. No push or matrix until clean fresh code/security reviews on the same SHA/tree; no live GitHub protection/ruleset changes, GitHub App creation, or new credentials under this authorization.

### Cross-role synthesis

| Lens | Recommendation | Trade-off |
|---|---|---|
| Security / trust boundary | Load a local promotion guard from the immutable D-222 planning commit, not the candidate's editable copy. Bind review receipts, exact SHA/tree, current protected contexts, and candidate history. Stop if reviewers require server-side enforcement. | Controls the authorized GSD actor's path and prevents accidental promotion; it cannot stop a separate manual bypass or malicious PR that rewrites its workflow. |
| GitHub Actions / DevOps | Preserve the three required contexts and all existing jobs. Avoid `workflow_run` and `pull_request_target` with PR code; GitHub warns these privileged triggers can expose secrets and write tokens. | A PR workflow can run a gate early but cannot be its independent trust root if the PR can edit that workflow. |
| Test engineering | Correct duplicate-job fixtures with valid records, distinct IDs, and incremented `total_count`; prove the named duplicate guard is reached. Convert `TimeoutExpired` to transient uncertainty and stop by the existing waiter deadline. | Reuses existing self-test and CTest identities, no dependency, no timeout extension. |
| Operations / CI efficiency | Run cheap identity, syntax, and causal checks before focused suites; read current protection and matrix results before any costly hosted run. Measure actual job/wait/headroom if a matrix is reached. | Adds a local preflight step but avoids spending runner time on an unpromotable candidate. |
| Maintainability | Prefer the standard library and existing policy/control seams; keep the old candidate/review/matrix records immutable. | The guard requires explicit updates when the Phase 24 promotion contract changes, but avoids a general workflow framework or dependency. |

Primary references: [GitHub secure-use guidance](https://docs.github.com/en/actions/reference/security/secure-use), [branch-protection API](https://docs.github.com/en/rest/branches/branch-protection), and [ruleset available rules](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets). These show the risk of privileged workflows with untrusted PR content and the external nature of app-bound checks/ruleset gates.

**Retained limits:** One existing Phase 24 plan; no external protection/app/credential changes; preserve three required contexts and at most two changed protected matrix candidates. Candidate two requires a concrete in-scope first-matrix failure and causal fix. Keep FIXT-01 Pending, the Acid2 mismatch failed and unreplayed, D-103, Task 7, all ROM/fixture exclusions, no broad suite, and separate phase/milestone closure.

**Next route:** `$gsd-plan-phase 24` updates and independently checks the sole plan. Then continue `$gsd-autonomous --from 24` only if the repo-only guard can be independently reviewed without an unresolved security finding. If the stronger external gate is required, stop and ask before changing GitHub settings or creating an app.

## D-223 — Repair the immutable gate launcher and finish the owner-authorized milestone route

**Date:** 2026-11-20
**Areas discussed:** Python module execution context; immutable source and test provenance; phase/milestone closeout boundaries

| Option | Description | Selected |
|---|---|---|
| Keep D-222 stopped | Preserve its direct test pass and immutable-loader failure without another gate attempt | |
| Same-plan loader correction and one replacement gate | Fix module registration and pinned-byte self-test behavior, independently check/commit the existing sole plan, then freeze one replacement gate and retain all promotion limits | ✓ |
| Repeatedly repin until it passes | Permit multiple committed replacement gates if fresh-process tests keep failing | |

**Owner's choice:** The owner authorized the recommended D-223 replan and directed GSD Autonomous through the v0.4 milestone finish. The existing sole plan is the only plan to update.

### Evidence and root cause

The direct command `python3 -I .github/scripts/phase24-promotion-gate.py --self-test` passed all 26 controls. The same original gate bytes run through the immutable loader failed 17 subcases. The loader passed a fresh globals dictionary named `__main__`, but `unittest.mock.patch` resolves the registered module from `sys.modules`; the test fixture also expects `__file__`. The remedy must make the executing namespace a real, registered module without reading candidate files. `build/phase24/d222-t24-red.json` captures an earlier red-stage failure where `fixed_push_argv` was incomplete; it remains historical and is not the latest direct-test result.

### Cross-role synthesis

| Lens | Finding | Selected recommendation |
|---|---|---|
| Python runtime | `exec` can populate an explicit namespace, but that dictionary is not automatically the registered import target. Reusing `__main__` would put gate internals in the wrapper namespace. | Create a unique `types.ModuleType`; inject the already verified gate bytes and a sentinel `__file__`, set `__package__`, register it before execution, execute into its `__dict__`, then call `module.main()` with the intended argv. |
| Security | A correct module context must not permit a second source read from the candidate checkout or execute bytes different from the pinned digest. | Immutable self-tests use `__phase24_gate_bytes__`; only direct `__main__` mode may read the local script. A missing injected byte value in immutable mode denies. Controls cover exact byte identity, module registration, mock target resolution, candidate-copy refusal, and zero mutation. |
| Test engineering | The runtime loader path itself is the failed seam, so a direct self-test cannot prove it. | Run cheap syntax/source-identity checks, the direct suite, then the exact fresh-process immutable loader suite before freezing. After one replacement gate commit, verify its receipt and repeat immutable self-test against the original object. No protected matrix slot is consumed by this local fix. |
| Operations / CI | A deterministic local loader error does not justify hosted CI or a workflow redesign. | Keep current contexts and all ten T26 CTests. Measure queue/job/step/dependency waits and timeout headroom if the authorized protected matrix runs; do not trade away coverage. `act` may be useful only where its semantics match the relevant workflow and can never replace hosted required checks. |
| Product / milestone | The owner's broad authorization supersedes the earlier prohibition on milestone audit/completion/cleanup, but accepted D-209 evidence gaps remain accepted. | After exact merge reconciliation, run objective automated Phase 24 verification and the milestone audit/completion/cleanup. Keep FIXT-01 Pending, Task 7 deferred, D-103 unfulfilled, the Acid2 result failed/unreplayed, and v0.4 claims/assets unchanged. Do not run the historical source/rights/ROM work or start v0.5. |

### Authorization boundary

First independently check and commit the D-223 update to the sole plan. Before the replacement gate is frozen, local diagnosis and retesting may correct the known module-context issue within the exact gate/loader boundary. Commit one gate-only child, write `build/phase24/d223-bootstrap.json` without replacing the D-222 receipt, and require both direct and immutable tests to pass. A frozen replacement failure stops without a second repin. Then resume existing T25/T26: valid duplicate-name fixtures, absolute-deadline subprocess behavior, cheap checks before the same ten serial CTests, distinct clean same-SHA/tree code and security reviews, current protection readback, existing candidate/matrix limits, and conditional exact-head merge. No live protection/app/credential change, new dependency, CTest identity, replay, broad suite, or weaker gate.

**Next route:** Independent plan check and planning-boundary commit; then `$gsd-autonomous --from 24`. After successful T24–T26 and exact merge, run automated phase verification and D-209-compatible milestone audit/completion/cleanup, reconcile onto main, and finish with clean status. No user action is needed while these gates pass; a fresh blocker or failed protected check stops at its gate.

## D-224 — Inherited gate commit-boundary proof

**Date:** 2026-11-20
**Areas discussed:** Discussion-boundary tree inheritance; exact replacement-gate diff and causal fixture fidelity

| Option | Description | Selected |
|---|---|---|
| Reject any discussion commit tree containing the gate; require the next gate diff to be an addition | Simple checks, but incompatible with this history because the planning commit inherits the prior gate and the replacement modifies it | |
| Trust pinned commit/tree/blob values without checking the parent delta | Minimal logic, but does not directly prove the gate stayed unchanged between the pinned parent and discussion commit | |
| Pin a single parent; compare complete original-object diffs; allow unchanged inheritance and require one exact old-to-new regular-file modification | Matches actual Git history, proves the discussion commit left the gate unchanged, and binds the replacement transition to its expected old blob | ✓ |
| Generalize to arbitrary roots, merges, renames, and file types | More flexible but broadens the trusted boundary without serving this recovery | |

**Owner's choice:** The owner authorized one D-224 recovery scope. The synthesized recommendation is to correct both adjacent predicates and test the true inherited-file transition together in the sole plan.

### Evidence and exact boundary

The D-223 planning commit `06d2e06…` inherited `.github/scripts/phase24-promotion-gate.py` from its parent; its gate entry was unchanged. The frozen D-223 replacement at `d6c33ec…` remains at the current Phase 24 head as regular file mode `100644`, blob `575b450769b395f7df6b28caabed294f32b3efee`, SHA-256 `8820ce491597d98d9985b474602c28890e20349d28746b119cc65efb57f1f64a`. Thus checking for path absence rejects the real discussion boundary, and expecting `A` rejects the real gate-only replacement. The existing test fixture hid both contradictions by modeling no inherited gate and a fabricated add.

### Cross-role synthesis

| Lens | Finding | Recommendation |
|---|---|---|
| Git/object model | A commit tree is a snapshot, so inherited path presence does not imply the commit changed the path. Comparing two trees/commits exposes mode/content transitions; merge comparisons have different semantics. | Pin the discussion commit's exact single parent and compare the full parent-to-commit delta. Reject any change to the gate entry while allowing the identical pinned file to be inherited. |
| Security/trust boundary | Tree pinning alone leaves the no-change claim implicit; ambiguous rename/type/mode transitions or a wrong base blob could otherwise satisfy an incomplete predicate. | Use original-object reads and the existing full raw NUL diff with `--no-renames`; require the exact D-223 old blob/mode and reject merge/root topology, gate deletion/rename/type/mode changes, malformed diff, and replacement refs. |
| Test engineering | The current `FixtureGit` claims the gate is absent and synthesizes an added file, so the self-test does not match the production history. | Add production-predicate positives for inherited unchanged gate and one exact `M 100644→100644`; add causal negatives for changed/deleted/renamed/type/mode-changed discussion file, wrong prior blob, `A`/`D`/`T`, extra path, invalid parent count, and malformed diff; prove rejected cases call no action. |
| Operations/OpenGSD | A post-freeze failure cannot be repaired by silently changing the pinned source; CI is not useful to detect an offline deterministic predicate failure. | Diagnose and test both seams locally before the single freeze; after freeze, verify the receipt and stop without repinning if any gate check fails. Keep T25/T26 and all promotion gates behind success. |
| Product/scope | This is a recovery-path defect, not a reason to reopen v0.4 requirements or change release claims. | Preserve D-209 status, FIXT-01 Pending, Acid2 failed/unreplayed, Task 7, D-103, current branch protection, and later exact-merge/phase/milestone boundaries. |
| Maintainability/CI | The existing Git adapter and standard library can express the contract; speculative parser or workflow changes create risk without evidence. | Reuse the original-object/raw-diff seam, add no dependency, CTest identity, or CI topology change. If a hosted matrix is later reached, measure actual queue, job/step, dependency-wait and package-work timing without weakening checks. `act` can assist locally but cannot replace hosted protected results. |

Official [Git `diff-tree` documentation](https://git-scm.com/docs/git-diff-tree) describes raw changes, file modes/status, NUL-terminated path output, and special merge behavior. Official [replacement-ref documentation](https://git-scm.com/docs/git-replace) supports explicit `--no-replace-objects` for original-object reads. These primary sources support the narrow comparison; no dependency or generalized Git framework is needed.

**Authorization boundary:** This scope authorizes the same-plan D-224 replan, independent plan check, and one gate-only replacement commit. It does not authorize T25/T26 until that frozen gate passes bootstrap verification and immutable self-test. Once those gates pass, the earlier GSD Autonomous authorization continues under its existing matrix, review, merge, requirement, and closeout limits. No additional gate freeze, repin, CI run, matrix, or branch switch is created by this discussion.


## D-225 — Preserve the lexical path gate with immutable tree lookup

**Date:** 2026-11-20
**Areas discussed:** Scanner/gate compatibility; immutable Git object selection; local verification order; bounded recovery and autonomous routing

### Trigger and evidence

D-224 T26 stopped at required `no_phase_paths` on candidate `7761be6f90041efd0bb6928279c002a369962d7f`. The scanner rejected the gate's Phase 24 path spelling at line 33 in 2.81 seconds; the receipt records the actual CTest output. The same source has three planning-file constants and one matching path in the embedded fresh-process loader. The gate currently reads pinned Git objects, but the lexical checker rejects the source spelling before its semantic controls run. D-224's gate, its failed result, and all earlier receipts remain immutable history. No reviews, push, matrix, merge, or phase/milestone closeout ran for this candidate.

### Options considered

| Option | Benefits | Costs / failure mode | Decision |
|---|---|---|---|
| Keep the failed gate unchanged | No source change or new risk | The mandatory scanner continues to fail, so Phase 24 cannot advance | Reject |
| Add exact scanner allowlist entries or exempt the gate | Smallest immediate diff | Weakens the repository-wide lexical contract and teaches future code to bypass the guard at its trust boundary | Reject |
| Split/escape/hex-encode path strings | Avoids the raw scanner match with little Git code | Conceals security-sensitive paths from reviewers and makes correctness depend on a decode path the scanner cannot see | Reject |
| Broaden or redesign the lexical scanner | Could recognize immutable reads structurally | Expands a gate-only recovery into scanner behavior and its 201-control surface; risks false confidence without solving exact object selection | Reject |
| Select files by pinned path digest from immutable Git tree metadata, then read the verified blob by OID | Keeps the scanner strict; proves tree membership, uniqueness, file mode/type and exact content identity; needs no dependency | Adds a small NUL-safe tree-record resolver, bounded output handling and denial tests | **Select** |
| Re-anchor all seven source pins to incoming candidate 7761 | Appears to match the latest candidate state | Would make the D-221/PLAN_REV baseline inconsistent or require a circular exception; it could pin out the existing two-path correction allowance and block a causal candidate-two fix | Reject |
| Keep the existing D-221/PLAN_REV source pins and two-path T25 correction allowlist | Preserves the proven five-unchanged/two-correction structure, allows exactly the existing waiter/coverage corrections, and keeps candidate-two causal fixes in scope | Requires keeping the source baseline distinct from the new D-225 execution-route commit | **Select** |
| Reuse or overwrite the D-224 bootstrap receipt for D-225 | Avoids touching the existing direct-control receipt consumer | Mislabels a new gate/plan boundary or destroys immutable failure history; receipts must remain distinguishable by boundary | Reject |
| Keep the T24 gate replacement commit gate-only, then adapt only the existing receipt path/kind/schema/handoff in the already-allowlisted coverage direct seam after T24 passes | Preserves D-224 evidence and keeps the new bootstrap identity truthful while using an existing correction path | Requires a sequential, narrowly scoped T25 integration edit | **Select** |

### Cross-role synthesis

| Lens | Adversarial finding | Recommendation |
|---|---|---|
| Security / trust boundary | A lexical exception or hidden path encoding would make the scanner's source-level promise weaker exactly where the promotion guard is most sensitive. Path selection must not fall back to a worktree, revision expression, replacement ref, or redirected Git environment. Rebinding baseline pins to the current candidate could also weaken the candidate boundary. | Leave scanner and allowlist unchanged. Select one entry by a pinned SHA-256 of its raw path bytes from a pinned original commit, validate `100644 blob` and the exact expected object ID, then read only with `git cat-file blob`. Use sanitized Git environment and `--no-replace-objects`; preserve D-221/PLAN_REV pins and the exact two-file correction allowlist. |
| Git / architecture | `ls-tree -z` preserves path bytes and NUL-terminates records; paths cannot safely be split on newline or decoded under host path conventions. A commit tree is the authoritative immutable namespace. | Parse output as bytes and split only on NUL and the first metadata/path tab. Hash the entire raw path byte string. Require exactly one digest match; avoid path reconstruction and ordinary filesystem joins. Keep the helper narrowly scoped to the three pinned planning blobs. |
| Test engineering | A helper-only test could pass while production still uses a path-bearing `rev:path` read, or malformed tree output could be mistaken for a usable entry. | Tests must call the production resolver and immutable gate path. Cover exact positive selection plus missing/duplicate digest, malformed NUL/header, wrong mode/type/OID, bounded-output refusal, hostile Git environment and replacement-ref cases; assert every refusal causes zero promotion calls. |
| Test/receipt integration | Reusing the old receipt path would overwrite or mislabel immutable D-224 evidence; the existing direct-control consumer expects its D-224 schema. | Keep the T24 source commit gate-only. Only after its immutable checks pass, adapt the existing coverage direct seam's receipt path/kind/schema and trusted handoff within its already-approved correction path; retain its CTest IDs and do not replay waiter logic. |
| Operations / GSD | The failed test was cheap, while the preceding self-test controls cost substantially more. Waiting for the full focused suite to discover this lexical failure wastes iteration time. | Before the next freeze, run syntax/direct controls and `verify-no-phase-paths.py --check`; only then freeze one gate-only child and require bootstrap plus immutable self-test. Run the existing ten CTests serially in their established order. A new frozen failure stops without another replacement. |
| CI / release engineering | A local pass cannot satisfy the three hosted protected contexts, and shorter wall time is not justification to remove coverage. CI delays need measured attribution. | Preserve matrix membership, contexts, timeout budgets and protected merge. If the hosted matrix runs, record queue, job/step, dependency wait and package execution/skips; propose only an evidenced change that preserves release proof. `act` remains an optional local approximation, never hosted status evidence. |
| Product / scope | This blocker is in the recovery guard and does not change emulation behavior, accepted release claims or requirement evidence. | Preserve D-209 dispositions, FIXT-01 Pending, the failed unreplayed Acid2 result, Task 7, D-103, released bytes, archive pins, and all phase/milestone boundaries. Do not begin v0.5. |
| Maintainability | A general Git abstraction or new dependency would add surface without solving a broader product need. | Use the existing original-object Git adapter and Python standard library; retain one existing plan, CTest identities and CI topology. |

### Immutable path pins

The selected resolver compares raw Git path bytes against these SHA-256 pins and then validates the pinned blob object: plan `981d088bc4d660fbb67e39db130bb8ec6bba081e6717b99ab9ec825388cdc72e`; closeout `56f44d6804c1ae7ca224578d88d51d10a3bc086f9844bae48bcfaae0f044f703`; discussion `c0600dcc6a37ca945963f6e2d89a3c0509c324cca4c07f143f92916e49703657`. The failed candidate remains `7761be6f90041efd0bb6928279c002a369962d7f`; the frozen D-224 gate is `dc321ba3fe51a7391ed9d1c9680cfc621d626d9d`, with old blob `a97a45121d2c4550a853febff6674cbeb32ccd34` and mode `100644`. The D-225 planning commit must inherit that gate unchanged; the sole replacement child must contain exactly one gate-source `M 100644→100644` from the old blob. Keep the existing D-221/PLAN_REV baseline and exact two-file T25 correction allowlist. T25 changes already in 7761 remain in scope for T26 qualification and are not replayed; the new D-225 route commit does not re-anchor source pins. Once the T24 receipt passes, T25 may update only the already-allowlisted direct seam to consume the distinct D-225 receipt; preserve the D-224 receipt.

Primary references: Git documents verbatim NUL-delimited output and recursive full-tree listing in [`git ls-tree`](https://git-scm.com/docs/git-ls-tree), and raw object-ID reads in [`git cat-file`](https://git-scm.com/docs/git-cat-file). The existing adapter's `--no-replace-objects` behavior is grounded in [`git replace`](https://git-scm.com/docs/git-replace). These references support the narrow object protocol; they do not justify a generalized scanner exception.

**Owner's choice:** The owner approved the new bounded recovery and instructed the agent to follow the synthesized recommendation autonomously. Use the immutable tree resolver; do not ask another preference question.

**Authorization boundary:** This discussion authorizes one same-plan D-225 replan, one independent plan check, and one new gate-only replacement after local checks pass. The failing D-224 receipt remains unchanged; do not retry the unchanged candidate. Before the replacement is committed, local diagnosis and retesting may converge within the resolver and gate-source boundary. After it is frozen, any direct, bootstrap, immutable, or required qualification failure stops without another replacement. After T24 passes, T25 may update only the existing direct receipt seam in the already-allowlisted coverage file to consume the new receipt; it does not reopen waiter logic. No new dependency, plan, CTest, CI context, scanner exception, protected matrix candidate, or candidate-two entitlement is created. Once the gate passes, continue the previously authorized `$gsd-autonomous --from 24` route through existing T25/T26, clean same-head code/security reviews, the protected matrix, conditional merge, active-scope automated verification, and D-209-compatible milestone closure. Finish on clean `main` after approved reconciliation.

### D-225 frozen outcome — stopped

The single gate-only replacement `e1f072f23d2d6a6fcfb328f0b30f224fe006c533` has the expected parent and exact one-file raw diff, but bootstrap denied `d221_source_drift` before writing `d225-bootstrap.json`. The two mismatched sources are precisely the existing correction-allowlisted paths; their D-221 expected and D-225 actual OIDs, plus the six matching pins and pre-freeze checks, are recorded in [`d225-bootstrap-denied.md`](../../../build/phase24/d225-bootstrap-denied.md). `validate_plan_anchor` enforces the D-221 pins unconditionally, exposing a mismatch with the stated two-path correction allowance.

The frozen-failure stop applies: no gate edit/replacement, post-freeze immutable test, T25/T26, review, push, matrix, merge, verification, or milestone closeout ran. D-222 and D-224 receipts remain unchanged. Any further correction needs a new owner-approved scope; this discussion does not authorize another replacement.

## D-226 — Bind correction pins to the original parent

**Date:** 2026-11-20
**Areas discussed:** Source-baseline provenance; gate boundary identity; adversarial controls; bounded execution and stop rule

### Trigger and evidence

D-225's sole gate-only replacement `e1f072f23d2d6a6fcfb328f0b30f224fe006c533` passed its pre-freeze checks but its frozen bootstrap denied `d221_source_drift` before writing a receipt. The first mismatch is `.github/scripts/wait-exact-head-ci.py`: D-221 expects `67c78ff306e3338cfefbabe8b6512dc7a62da6b8`, while pinned source parent `7761be6f90041efd0bb6928279c002a369962d7f` contains `0eda5971bf059cbdba560c3b9d9bd8d6cb1ecb8d`. The second is `tests/scripts/verify-workflow-policy-coverage.py`: D-221 expects `81b388795eec982d5b73b1dc71e007af70b597ba`, while parent 7761 contains `771e64dd919f91dcdb8ef4163d985c517b82e6cb`. Both are exactly the existing correction-allowlisted paths; the other five of seven source paths match D-221. The gate's `validate_plan_anchor` compares all seven to D-221 unconditionally. The frozen failure and absence of a D-225 bootstrap receipt are preserved in [`d225-bootstrap-denied.md`](../../../build/phase24/d225-bootstrap-denied.md).

The source-pin audit also inspected candidate qualification: `_verify_candidate_scope` bases candidate content on the checked plan revision and exempts only the two exact correction paths. Therefore re-anchoring to parent 7761 is not needed to preserve candidate-two eligibility; the reason to keep D-221 is its historical baseline role and the narrower, auditable proof.

### Options considered

| Option | Benefits | Costs / failure mode | Decision |
|---|---|---|---|
| Re-anchor all seven source pins to parent 7761 | Removes the immediate mismatch | Rewrites the historical D-221 source baseline even though five files are identical; expands trust changes beyond the two intended corrections | Reject |
| Skip the D-221 comparison for any correction-allowlisted path | Small code change | Accepts any content at those paths without proving which already-admitted correction object is intended | Reject |
| Keep D-221 for five files; require the two plan blobs to equal exact original-object entries in pinned parent 7761 | Preserves historical provenance and exactly admits existing correction bytes; no new manifest or dependency | Must pin and verify the separate source parent/tree and two modes/OIDs, distinct from the new D-226 planning boundary | **Select** |
| Add a new correction manifest or broader source abstraction | Could externalize source facts | Adds another mutable artifact and more trust wiring without improving on three exact constants in the existing gate | Reject |

### Cross-role synthesis

| Lens | Adversarial finding | Recommendation |
|---|---|---|
| Security / provenance | A path-only exemption leaves correction contents mutable; comparing to the mutable checked plan itself would make the assertion circular. | Read the exact parent `7761be6...` as an original commit, verify its tree and both path entries' mode/type/OID, then require the checked plan's two correction entries to match those exact objects. Keep D-221 comparisons for the other five paths. |
| Architecture / Git boundary | The D-226 documentation boundary is a child of the D-225 stop commit, while source corrections originate at 7761. Treating these as one parent would confuse execution-route identity with source provenance. | Pin separate constants: D-226 plan revision and immediate parent for the route boundary; source parent/tree 7761 for the two correction blobs; D-221 remains the five-file baseline. |
| Candidate qualification | The current candidate validator compares candidate blobs to `PLAN_REV` and permits only the two fixed correction paths; the candidate-two rule independently requires an in-scope first-matrix failure and causal path. | Leave `_verify_candidate_scope`, source allowlist, correction allowlist and candidate-two rules unchanged. Do not claim a full re-anchor is required to keep candidate two eligible. |
| Test engineering | A broad positive could mask accepting arbitrary bytes at correction paths; a fixture-only test could miss production use. | Exercise the production `validate_plan_anchor` path. Prove exact parent-bound positives plus causal refusal for wrong parent/tree, changed correction OID, wrong mode/type, any of five non-correction drift, allowlist drift, and redirected/malformed Git reads; assert zero promotion calls. |
| Operations / GSD | The frozen failure has a strict stop; expensive local CTests or CI cannot fix it after freeze. | Before the single new replacement, run syntax/scope/direct controls and the unchanged cheap scanner. After freeze, T27 requires direct and bootstrap checks; T28 then runs the existing receipt seam against the immutable D-227 gate. Only if all pass continue T29. Any failure stops with no further replacement. |
| Maintainability / cost | A new package, manifest, or scanner exception would widen the trust surface. | Add the two exact pins to the existing standard-library gate and reuse its current test seam. Add no dependency, CTest, CI context, or workflow topology change. |
| Product / release | This is a promotion-proof defect, not new emulation evidence. | Keep D-209 dispositions, FIXT-01 Pending, failed unreplayed Acid2, Task 7, D-103, release bytes, archives, branch protection and milestone boundary unchanged. |

**Owner's choice:** The owner selected **Authorize D226** on 2026-11-20. The approved bounded scope is one same-plan update, one independent plan check, and one gate-only replacement using D-221 for five files and exact parent-bound objects for two correction files.

**Authorization boundary:** D-226 supersedes D-225's no-further-replacement stop only for one new gate-only replacement after the D-226 checked planning boundary. It does not alter the failed D-225 replacement or receipt state. Pre-freeze local diagnosis may converge within the described gate proof. After freeze, any direct, bootstrap, immutable, or required qualification failure stops without another replacement. T25/T26 stay held until frozen direct/bootstrap/immutable checks pass. All D-209, D-103, Task 7, Acid2, candidate, review, matrix, CI, merge and cleanup limits remain unchanged. If T24 passes, resume the existing authorized `$gsd-autonomous --from 24` route.

## D-227 — Correct the frozen direct-control marker contract

**Date:** 2026-11-20

**Areas discussed:** Raw marker contract; immutable recovery boundary; final qualification and stop behavior

### Trigger

D-226's exact final candidate `febaa91c969daf2f82ac85424eb4623684ecdfc7` (tree `5f903b66071ec9f2bdbc6d007e9b917c4079c45c`) failed the frozen gate's `promotion_coverage_controls` direct-control check. The exact fixed command exited zero and its preserved raw transcript `build/phase24/d226-t26-promotion_coverage_controls.log` contains `PASS: phase24-promotion-controls gate=<64 lowercase hex> controls=<integer>`. The gate's matcher instead expects `phase24-promotion-controls pass gate=… controls=…`; `_validate_direct_control` refuses with `qualification_direct_marker_missing`. The D-226 gate replacement is `f9ccf6b4a211bc33270f6f8172e40a4e4cb22cba`, blob `d37be8847ca654b0b318103fef07e130ad918a56`, SHA-256 `ea6c281eee7f3161235b235d6d67e9f4d11ebcbb230f42b9a51ee491a85afb9e`. The final-candidate CTests did not start. Preserve the candidate, gate, raw transcript, digest and ignored stop report without edits.

### Options considered

| Option | Benefits | Cost / failure mode | Decision |
|---|---|---|---|
| Change the immutable gate consumer/sample to match the actual raw PASS line, then rebind the existing direct coverage seam to D-227's receipt after freeze | Fixes the stale marker and keeps the existing direct seam connected to the new immutable gate receipt; preserves producer output and raw evidence | Requires one gate-only freeze followed by one already-allowlisted correction-path update | **Select** |
| Change the coverage checker to emit the gate's stale synthetic wording | Satisfies the existing expression | Changes a correct producer and increases scope across the already-qualified correction seam | Reject |
| Rewrite/normalize/append transcript text before validation | Can manufacture a matching line | Digest would no longer attest to exact command output; weakens evidence provenance | Reject |
| Retry the unchanged D-226 candidate or remove the control | Avoids a new gate commit | Repeats deterministic failure or weakens the gate | Reject |

### Cross-role synthesis

| Lens | Concern | Selected control |
|---|---|---|
| Security/provenance | A transformed transcript or loosely matched substring could accept output different from the fixed command's exact evidence. | Anchor the complete expected line: literal `PASS:`, exact marker name, 64 lowercase hex gate digest and integer count. Preserve exact command, raw transcript bytes, SHA-256, exit code and declared marker list. |
| Architecture/integration | Only the gate's marker grammar is stale, but the existing coverage seam also pins the D-226 receipt and gate identities. Updating only the matcher would leave the next actual direct-control command bound to old bootstrap evidence. | Keep producer output unchanged; after the D-227 gate freeze, update only the coverage seam receipt path/kind/schema/plan/gate pins in its existing correction allowance. Preserve D-226's receipt and leave waiter logic untouched. |
| Test engineering | The embedded sample shared the same stale grammar, so the direct suite was self-consistent but not representative. | Use the actual captured line as a positive and reject the former synthetic line, missing marker, bad digest, nonzero result and altered fixed command. Assert no reservation/promotion side effect on refusal. |
| Operations/CI | The mismatch was found before CTest and remote qualification. Hosted CI adds no diagnostic value until the frozen local gate is clean. | Run cheap syntax/scope/direct controls plus the unchanged scanner check before freeze. After freeze T27 requires direct self-test and bootstrap verification; T28 then runs the existing receipt seam against original immutable bytes, followed by the existing ten CTests serially. Measure real queue/job/step/dependency/package time only if the protected matrix runs; preserve every required check. |
| Maintainability/supply chain | New parsing dependencies, transcript filters or CTest identities add maintenance and trust surface without recurring value. | Use the existing Python standard library and current self-test/CTest seams; add no dependency or workflow change. |
| Product/release | A gate-format defect does not create new PPU/emulator evidence or change the accepted milestone gaps. | Retain D-209 requirement dispositions, FIXT-01 Pending, failed unreplayed Acid2, Task 7, D-103, released bytes and archive pins. |

### Owner direction and bounded route

The owner instructed the agent to follow the synthesized recommendations and continue through the milestone. The D-227 scope is one same-plan update, one independent plan check and one gate-only replacement after the checked documentation boundary. That boundary is a single-parent child of the D-226 stop candidate and proves inherited D-226 gate blob `d37be8847ca654b0b318103fef07e130ad918a56`/mode `100644` unchanged while revalidating the historical D-225→D-226 chain. The replacement is its single-parent child with exactly one raw NUL-diff `M 100644→100644` entry on `.github/scripts/phase24-promotion-gate.py`. Refresh gate plan/discussion pins from the checked boundary; do not change the raw-path resolver or source baseline. After T27 freezes D-227 and its direct self-test plus bootstrap verification pass, T28 updates only the existing coverage direct seam to consume `d227-bootstrap.json` and exact D-227 pins. That call executes the immutable self-test against original gate bytes; preserve the D-226 receipt and do not replay waiter code.

D-227 does not reset candidate, review, matrix, required-context, or merge limits. A failed frozen direct/bootstrap/immutable check ends the attempt without another replacement, retry, CI run, promotion or closure claim. Once the existing receipt seam passes with D-227 evidence, resume exact-head qualification, all ten existing focused CTests, fresh independent code/security reviews, the one existing protected matrix, and conditional merge of the identical reviewed head. Then run active-scope automated Phase 24 verification and D-209-compatible milestone audit/completion/cleanup after approved reconciliation to `main`. Do not start v0.5, run D-103, replay ROM/Acid2, execute Task 7, change requirements, or alter protected coverage.

**Canonical references:** `.github/scripts/phase24-promotion-gate.py`; `tests/scripts/verify-workflow-policy-coverage.py`; `build/phase24/d226-t26-promotion_coverage_controls.log`; `build/phase24/d226-t26-frozen-gate-marker-stop.json`; `.planning/phases/GB-24-resolve-remaining-v0-4-evidence-and-verification-gaps/24-01-PLAN.md`; `.planning/context/WORKFLOW.md#cicd-efficiency`.

## D-228 — Match the CTest JSON-v1 inventory version contract

**Date:** 2026-11-20

**Areas discussed:** Producer schema, fail-closed version validation, bounded correction, qualification order

### Trigger

D-227 T27/T28 passed, but T29 stopped before CTest when the immutable validator required a `patch` key. The retained raw CTest 4.4.3 `json-v1` inventory has `version: {major: 1, minor: 0}`. The official CMake 3.25 documentation and published schema define these as the model-version fields and allow additional properties. The raw inventory and stop receipt are retained at the paths and digests in 24-CONTEXT.md; no CTests or remote/promotional actions occurred.

### Options and selected recommendation

Require an object containing integer major 1 and minor 0, reject booleans and all missing/mistyped/wrong values, and neither require nor interpret `patch`. The official JSON Schema does not forbid extra properties, so ignore an inert extra field such as `patch` while continuing to validate every other inventory field exactly. Reject an exact-two-key policy as unnecessarily stricter than the producer schema; reject an optional/synthesized patch because that model component is not documented; reject broad version acceptance because it would hide schema drift.

### Cross-role synthesis

| Lens | Risk | Recommendation |
|---|---|---|
| Security/evidence | Weakening the version gate could admit an unsupported inventory model. | Strict JSON parser; exact integer major/minor checks; unchanged strict inventory cardinality, identity, command, properties and duplicate-key contracts; refusal controls before action. |
| Architecture | Confusing CTest's 4.4.3 binary version with JSON model 1.0 couples unrelated version domains. | Keep producer, command and raw transcript unchanged; correct only consumer/sample/controls. |
| Testing | Synthetic samples can hide a real producer/schema mismatch. | Promote the preserved raw transcript as the positive; negative tests cover missing, wrong, mistyped, negative, boolean, and obsolete synthetic versions; extra-property acceptance matches the official schema. |
| Operations | Running long qualification or CI before a cheap schema preflight wastes feedback time. | Syntax/scope/schema/self-tests/scanner first; frozen direct/bootstrap, then existing immutable seam, then the same focused serial tests. No check is removed or reordered inside protected CI. |
| Supply chain/maintenance | A general schema library would add dependency surface for a two-integer check. | Use existing Python stdlib and current test seams; no new dependency, CTest, or workflow. |
| Product/release | The checker defect is not new emulator proof. | Preserve every D-209 disposition, accepted gap, failure and published byte. |

The owner authorized one same-plan D-228 update, independent check and gate-only correction and directed continuation through the existing autonomous milestone route. The checked boundary is the sole-parent child of D-227 stop candidate `2e9d8cf1ed3e9889dd0199a9d30acdb06635661d`, inheriting gate blob `ac061190a7696134dd777d114fcce5228c58036d`. D-228 permits no retry or second gate replacement and resets no candidate/review/matrix/context/merge/closure limit. The existing receipt seam may be rebound after the gate freeze; T29's ten focused serial CTests remain blocked until both frozen gate and immutable seam checks pass. Continue to exact-head reviews, the existing eligible protected matrix and conditional merge only after qualification. Then verify the active Phase 24 scope, reconcile to main, and run the already-authorized D-209-compatible closeout. No v0.5, D-103, Task 7, ROM, or Acid2 replay.

**Sources:** [CMake 3.25 CTest JSON object model](https://cmake.org/cmake/help/v3.25/manual/ctest.1.html#show-as-json-object-model); [official CTest JSON schema](https://cmake.org/cmake/help/latest/_downloads/a23288746b718529293c28c8c3fad9df/show-only-schema.json).
