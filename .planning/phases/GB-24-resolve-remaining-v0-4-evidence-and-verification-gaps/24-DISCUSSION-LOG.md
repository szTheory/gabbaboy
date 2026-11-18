# Phase 24: Resolve remaining v0.4 evidence and verification gaps - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in `24-CONTEXT.md` — this log preserves the alternatives considered.

**Date:** 2026-11-17; updated 2026-11-18
**Phase:** 24-Resolve remaining v0.4 evidence and verification gaps
**Areas discussed:** Additive verification evidence, Read-only candidate research, Phase exit with gaps, BOM normalization and plan-cap regression, post-T6 Acid2 mismatch, literal RIGHTS-01/DIAG-01/DIAG-02 reconciliation, FIXT-01 execution boundary, D-211 protected CI boundary, D-213 integrated recovery, D-215 post-review correction scope, review limits, CI efficiency and conditional merge, and D-216's four exact-head path/Git/census findings and execution extension

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
