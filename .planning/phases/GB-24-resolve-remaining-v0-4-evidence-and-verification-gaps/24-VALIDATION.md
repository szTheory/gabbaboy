---
phase: "24"
slug: "resolve-remaining-v0-4-evidence-and-verification-gaps"
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-11-18"
---

# Phase 24 — Validation Strategy

Updated for D-220 on 2026-11-19. This is planning evidence only. The independently checked and committed planning boundary must be followed by separate owner execution authorization before source work, tests or CI. D-220 supersedes stale D-219 recovery limits; the fixed six-checker source allowlist and sole plan remain unchanged.

D-219's candidate `28ab38f2346a12ef68a07e8a2d403dbfd81b8ba5` (tree `7b872747c42fb214be72e793d2e1eaec542d3b4a`) passed the seven focused local CTests and then received a final independent NO-GO for aliased getter/split-string frame-global replacement and post-guard frame-local mutation. Its local qualification receipt and NO-GO report are distinct immutable history. No push, protected matrix or merge ran. T15/T16 are completed implementation attempts with rejected proof acceptance; T17 completed local qualification and stopped at review, so none may be dispatched again. T7 remains deferred.

## Test Infrastructure and Grounding

| Property | Existing contract |
|---|---|
| Framework | Existing Python standard library, Git and CMake/CTest; no dependency, public flag or CTest identity added |
| Scope | Six existing checker paths in the plan's source_allowlist; intended D-220 correction only in the two proof checkers; execution evidence additive in 24-CLOSEOUT.md |
| Current production seam | validate_planning_hygiene_source(source), adapter/revision predicates and self_test_planning_hygiene_path_contract in verify-no-phase-paths.py |
| Causal requirement | Every new source-only mutant reaches the full production predicate, refuses for REJECT planning-path-git-command, and records zero protected reads; same-seam clean positive actually reaches its permitted immutable reader |
| Payload policy | Parse/analyze mutant source only; never import/execute it |
| Cheap run | Syntax, immutable scope/identity/archive/ancestry, affected source-only controls, dense-input Git-context and state-fork inventory controls |
| Focused run | Exactly the same seven existing CTests, serially and in the explicit order below |
| Full suite/build | No broad suite or emulator/runner build; D-103 stays a separate gate |
| Python | Read interpreter from build/CMakeCache.txt; prepend its directory for python3 children. Python 3.14.4 is a historical observation; formal support range remains unknown |
| Configure | Current generated build/tests/CTestTestfile.cmake still binds immutable arguments to rejected 28ab38f. After cheap gates, configure-only `cmake --preset phase1` is required to bind the corrected candidate; no build target runs |
| Retained metadata fixture behavior | phase22_evidence_controls retains its existing disposable nested metadata CMake fixtures; that is no authorization for fixture/ROM execution |

Current tracked source paths, helper signatures and CTest registrations were inspected during planning; the historical D-219 PATTERNS map is not treated as current proof. CMakePresets.json places phase1 in build/, not build/phase1/. The PATH launcher proves OpenGSD 1.21.0; the older direct-home runtime is not the workflow launcher.

## Per-Task Verification Map

| Task ID | Contract | Existing seam / execution command | Status |
|---|---|---|---|
| T10/T11 | Historical archive/path/raw-pin/candidate-Git implementation and local evidence | Prior source-bound controls | Completed history; do not replay |
| T12/T13/T14 | Earlier correction/qualification and rejected reviews | Candidate-specific receipts and NO-GO reports | Historical; do not dispatch |
| T15/T16 | D-219 runtime/archive and six-checker Git/CLI implementations; direct controls and seven local CTests passed | 24-CLOSEOUT.md; ae9da48/b65062e/dcd4af9 through rejected 28ab38f | Implementation attempts completed, static-proof acceptance rejected; retain controls without redispatch |
| T17 | D-219 exact-head qualification succeeded locally; independent review blocked | build/phase24/d219-final-qualification-28ab38f2346a12ef68a07e8a2d403dbfd81b8ba5.md and matching final-review report | Local pass/NO-GO history, no matrix/merge |
| 24-01-T18-aliased-namespace-proof | Aliased getattr/split-name global replacement of git_run and D-209 pin, production predicate + zero reads, same-path exact positive | `python3 -I tests/scripts/verify-no-phase-paths.py --self-test`; existing full tracked scan | Pending separate execution authorization; T-24-34/T-24-36 |
| 24-01-T19-guarded-local-proof | Same aliased/split-name local write after guard in read_rev, commit_snapshot and immutable_blob; specific refusal, zero reads and valid exact reader positives | Same existing source-only production self-test/full scan | Pending; T-24-35/T-24-36 |
| 24-01-T20-d220-qualification | Immutable identity/scope, retained Git/CLI/census controls, seven focused tests, changed-candidate review convergence and conditional matrix/merge | Commands in sole plan; current protected PR contexts | Pending; T-24-37/T-24-38 |

The plan carries exact runnable commands and an adjacent observable fails_when for each automated verification. No new test scaffold is needed. T18 leads with a production-quality tracer from source through the actual predicate to the permitted reader boundary. T19 expands its reader cases. T20 consumes their combined committed output. Shared proof source makes the slices sequential; no extra plan is created.

## Execution Order and Limits

1. Assert independent plan-check/committed-boundary evidence and separate owner execution authorization. Resolve full original-object planning/source SHAs, inspect complete scoped diffs and ancestry, compare exact D-209 archive/data objects, and assert coherent committed route/handoff. Keep generated .planning/state.json excluded.
2. Run cheap syntax and affected source-only/identity checks first. New mutants must preserve unrelated guard/adapter/path shape, reach the production predicate and fail for the intended proof-specific reason. Witness predicate entry and zero protected reads; require the clean twin to reach its permitted reader. Preserve every retained D-219 positive/negative, finite binder/caller proof and exact pin/archive.
3. At the committed integrated candidate, run only existing dense-input `--check-git-context --source-revision "$PHASE24_D220_REV"` and state-fork `--inventory-controls --rev "$PHASE24_D220_REV" --repo .` controls. Require original-object/selector/replacement/untouched-decoy behavior, 153 cases and unchanged diagnostic exclusions with configure/build/runner=0. Never run the ROM-bearing dense-input full self-test or fixture-bearing state-fork modes.
4. Regenerate the stale existing phase1 configuration only after cheap gates, without a build. Inspect `ctest --preset phase1 --show-only=json-v1` for exactly the selected names once each, current immutable arguments/interpreter, unchanged deadlines/floors and no unsafe dependencies. A later identical configuration/candidate requires no gratuitous regeneration.
5. Run each test in the following table as an individual `ctest --preset phase1 --output-on-failure --no-tests=error -j 1 -R '^NAME$'` invocation, waiting for success before the next. Do not rely on registration order or a combined regex to establish order.

| Serial order | Existing CTest | Existing timeout | Existing acceptance floor / control |
|---|---|---|---|
| First | plan_cap | 30 seconds | Existing phases floor 4; exact sole plan/40-plan/route/archive controls retained |
| Next | phase22_evidence_controls | 60 seconds | Existing positives/rejected-controls/immutable-boundary contract; RUN_SERIAL retained |
| Next | phase22_evidence_contract | 60 seconds | Existing immutable diagnostic evidence/inventory-only contract and exclusions |
| Next | no_phase_paths_controls | 60 seconds | Controls floor 16; every retained/new causal case must actually execute |
| Next | no_phase_paths | 60 seconds | Tracked-file floor 380, complete must-scan and exception/source proof |
| Next | workflow_policy_coverage_controls | 30 seconds | Existing trust/coverage self-test and Git controls unchanged |
| Last | planning_hygiene_controls | 30 seconds | Controls floor 125; exact source/archive/route/full-SHA positives and all retained controls |

6. Preserve actual failures and diagnose in scope before relevant retest. Counts/deadlines are guardrails, not acceptance proof; no unchanged resubmission or receipt-only rerun.
7. Add truthful candidate-bound local evidence to existing 24-CLOSEOUT.md, commit before freeze, and qualify the complete frozen SHA/tree. Final exact-head receipts remain outside the candidate to avoid self-reference. Earlier candidate passes remain history.
8. Obtain fresh independent exact-head review of the complete candidate and cumulative relevant six-checker diff. A concrete in-scope finding returns to changed-candidate correction with a causal control, relevant cheap checks, the same seven-test qualification and fresh review. D-220 uses scope-bounded convergence; stop for owner discussion if progress stalls, review is unavailable or correction needs a new trust boundary, extra source file, dependency, CTest identity, broader claim or weaker requirement. No numerical correction/review cap is imposed by this Phase 24 exception; global rules are unchanged.
9. Only a clean fresh review opens the single full protected matrix on existing PR #154. Read actual current required contexts/protection and bind head/run/attempt/producer/artifacts. Any failed, skipped, stale or missing required context stops without matrix retry. Merge only the identical reviewed/passing head through existing protection; no bypass and no new candidate/base change that invalidates qualification.
10. If hosted CI runs, record actual queue, job/step, dependency-wait, package-step and timeout-headroom evidence under WORKFLOW.md CI/CD efficiency. Preserve every required check. Change no workflow topology, trigger, membership, cache, timeout or concurrency here; keep the package-waiter redesign separate.

## Preserved Boundaries

No Phase 24 requirement IDs are assigned: requirements=[] and phase_req_ids=null remain explicit. Archived D-209 owners/statuses are authoritative: seven complete, FIXT-01 Pending. Preserve the failed unreplayed Acid2 mismatch, diagnostic exclusions, D-103, Task 7, released v0.4.0 bytes, administrative closeout and all earlier failed review/matrix history. No local ROM/fixture replay, broad suite, phase/security verifier, SUMMARY/UAT closure, milestone audit/archive, v0.5, branch switch or worktree cleanup.

Original-object Git reads, --no-replace-objects, minimal sanitized environments and repository/worktree/common-directory/index/object/alternate/namespace redirection controls remain separate preserved invariants. Inventory conflicts must still refuse before Git/output effects; valid inventory/materialization positives and the 153-case census remain unchanged. Lexical temporary-root containment has no new runtime symlink claim.

COVERAGE.md remains unchanged with its existing reasoned no-external-API declaration. No schema-push/ORM or AI integration applies. Assumption-delta assessment is no-change: only “additional” in a stale plan-cap sentence triggered the scan; it adds no identity model or second domain variant/source.

## Validation Sign-Off

- [x] Historical D-219 implementation/local qualification and final NO-GO are distinguished; T15/T16/T17 are not runnable.
- [x] D-220 global/local proof findings map to T18/T19 causal source-only production seams.
- [x] Seven-test serial order, exact existing command forms, configured-source rebinding requirement, deadlines and floors are grounded in current files.
- [x] D-209, one-plan/source allowlist, separate authorization and closure stops remain explicit.
- [x] Revised sole plan and this validation passed independent plan checking with no issues; the documentation-only boundary is committed.
- [ ] Owner separately authorizes execution.
- [ ] Changed candidate passes causal controls and all seven focused CTests at its exact head.
- [ ] Fresh exact-head independent review is clean.
- [ ] Single protected matrix passes every required context; identical head merges only under protection.

No manual UAT is introduced. Planning checkboxes assert document coverage only, never implementation or test success.
