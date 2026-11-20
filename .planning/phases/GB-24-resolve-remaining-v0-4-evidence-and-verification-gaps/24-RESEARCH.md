# Phase 24: Resolve remaining v0.4 evidence and verification gaps — Research

**Researched:** 2026-11-19 (D-220 baseline; D-221 refresh)
**Domain:** Python standard-library static analysis, immutable Git evidence, planning-contract checkers, and protected CI qualification
**Confidence:** HIGH for current in-repository contracts; MEDIUM for implementation patterns grounded in official Python, Git, argparse, and GitHub documentation

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions (verbatim)

### Additive verification evidence
- **D-01:** Keep the Phase 20/21 verification reports and their source identities unchanged. Record current checks in an additive Phase 24 evidence record pinned to an exact commit; label them as point-in-time checks, not refreshed phase verification.
- **D-02:** Run only the existing focused checks that cover changed in-scope contracts, after cheaper identity/consistency checks. Do not run the broad CTest suite, claim the full Phase 20/21 criteria are refreshed, or change their GSD stale statuses. The D-103 exact-final-head suite remains a separate milestone gate.

### Read-only candidate research
- **D-03:** If source metadata helps explain the current gaps, consult only first-party pages for Potion Panic, µCity 1.3, dmg-acid2, cgb-acid2, and the pinned gbmicrotest upstream. Record source identity and page-access results as facts. Do not search a third game candidate, fetch ROM/source payloads, build, run, or admit fixture bytes, or draw a legal/rights conclusion from metadata labels.
- **D-04:** Treat upstream-page access failures as access failures, not evidence that a source or permission is absent. A later rights determination or fixture action requires separate explicit authorization.

### Phase exit with gaps
- **D-05:** Phase 24 can pass when its additive evidence map and automated controls are complete while FIXT-01 remains Pending and Phase 20/21 remain marked stale. Seven of eight original v0.4 requirements are complete under D-209. Keep the milestone audit at `gaps_found`; do not accept gaps, close v0.4, or imply that phase completion satisfies FIXT-01.
- **D-06:** Preserve the 40-plan total ceiling. The roadmap currently has 39 plan files, so Phase 24 has one plan available; no plan, review, gap, test-suite, lifecycle, release, fixture, or rights budget is reset by this rescope.

### Bounded recovery for Critical CR-01

- **D-07:** The owner accepted one bounded recovery for the fresh review finding in [24-REVIEW.md](24-REVIEW.md): append one correction task to the existing 24-01 plan and obtain one clean independent review of the exact committed candidate. Do not add a plan or renew any earlier review or test budget.
- **D-08:** In the existing plan classifier, remove exactly one leading UTF-8 BOM (U+FEFF) before matching the canonical frontmatter fence. If another U+FEFF remains at the beginning, treat the input as malformed and fail closed; do not let an unrecognized prefix classify a gap plan as ordinary.
- **D-09:** Exercise the immutable production plan-cap CLI with paired Phase 24 fixtures that share the same plan path and BOM-prefixed canonical frontmatter, differing only in gap_closure: true versus gap_closure: false. The first must fail specifically with the Phase 24 D-205 gap-plan refusal; the ordinary-plan twin must pass. A helper-only test is insufficient.
- **D-10:** Keep the existing Python standard-library checker and CTest identities. After cheap syntax/direct controls, run only plan_cap and planning_hygiene_controls, preserving the 30-second timeout and 125-control floor. Do not run Phase 24 verification until this focused regression hook and the one independent review are clean. If review finds a Critical/correctness/security issue or a new blocker, stop before verification.

### D-213 post-T10 recovery decisions

- **D-11 — Measure semantics, not a stale lexical count.** `verify-no-phase-paths.py` must keep its general lexical scan, must-scan list, exact historical JSON exception, stale-row rejection, and over-limit rejection. Replace only the `verify-planning-hygiene.py` count-only allowance with a narrow structural/context contract that classifies its immutable Git reads and disposable self-test paths. Do not set the pin to 30 or exempt the file. Add negative controls for an unclassified path literal and a same-count change that turns an approved fixture/source value into a live filesystem read. Use the Python standard library; no dependency or new CTest identity.
- **D-12 — Put the route in the immutable candidate.** The active Phase 24 route and matching handoff must exist in the committed candidate used by `git show <rev>:<path>` checks. Before implementation, allow a local, unpushed documentation-only planning commit that includes the route and coherent Phase 24 state/plan records. Stage only approved `.planning/` files; explicitly verify no `tests/` source edits entered that commit. Verify the route and archived v0.4 blobs from the boundary commit, then verify each implementation candidate descends from it. A dirty-worktree route does not satisfy an immutable-revision check.
- **D-13 — Replan the stopped round and permit local correction cycles.** Do not resume the failed T10–T12 execution attempt or continue at T11. Replan the same sole Phase 24 plan to include the stale count contract, committed-route prerequisite, and all six D-212 integration blockers. Within a later separately authorized execution, treat cheap and focused local failures as diagnose/fix/retest feedback inside this one bounded scope; freeze only after those gates pass. Keep the unused D-212 allowance of one fresh exact-head review and one protected PR matrix for the frozen candidate; any unresolved review finding or failed/missing required matrix context stops for owner discussion. This does not authorize Task 7, Phase 24 verification, milestone audit/archive, requirement changes, broad local suites, or excluded ROM/Acid2 execution.
- **D-14 — Apply the measured CI efficiency policy.** Follow `.planning/context/WORKFLOW.md#cicd-efficiency`: record actual job/step duration and dependency waits; run cheap changed-contract checks before long suites; retain required test membership and branch protection. Keep the full workflow matrix. Track the D-211 preview-waiter cost as a follow-up; do not fold a cross-workflow waiter redesign into this recovery plan without separate scope.

### D-214 — Execution authorization (2026-11-18)

The owner explicitly authorized the fresh D-213 execution: make the plan's local, unpushed `.planning/`-only boundary commit; execute T10, T11, and T12; iterate in-scope local diagnosis, fixes, and relevant retests until scoped checks pass; then obtain at most one fresh exact-head independent review and run at most one protected PR matrix. This authority does not resume the stopped D-212 attempt. The plan's exact whitelist, task scope, no-broad-suite/no-replay boundaries, and final review/matrix stop conditions remain binding. Phase verification, milestone audit/archive, merge, v0.5, and worktree cleanup are not included.

### D-215 — Recovery scope after the D-214 exact-head review (2026-11-18)

The owner selected one same-plan correction proposal for all four blockers and both warnings in the fresh D-214 review. This requires a Phase 24-only exception to the already-spent normal two-review-fix/one-gap limits; the global caps remain unchanged. Permit up to two post-correction review-fix passes for these six findings and direct corrections. In-scope local diagnosis, fixes, and relevant retests may converge without an arbitrary attempt count. New out-of-scope trust/correctness findings stop for owner discussion.

After local checks converge, run one initial fresh exact-head independent review. If it identifies scoped findings/direct corrections, allow up to two post-correction fix-and-re-review passes with relevant local checks and fresh review of each corrected candidate. Local diagnosis/retesting does not spend this review allowance. Stop on any new out-of-scope trust/correctness issue, unavailable review or finding unresolved after those two passes. Run one full protected PR matrix only after a clean final review, preserving every required context and branch-protection rule. Any failed, skipped, stale or missing required context stops without another matrix. If the exact reviewed and matrix-tested head passes every required context, conditionally merge it through the protected PR and reconcile to main; do not alter the qualified candidate.

This discussion authorizes planning only; a separate owner authorization is required before executing the updated plan. Keep D-209's accepted gaps, original requirement owners/statuses, FIXT-01 Pending, Task 7 deferral, failed unreplayed Acid2 comparison, excluded gbmicrotest cases, published v0.4.0 bytes, D-103 stop, no broad local suite, and no worktree cleanup. Phase 24 verification, milestone audit/archive, and v0.5 remain separate.

### D-215 implementation recommendations from the review synthesis

- Keep the repository-wide lexical path scan and harden only its structural contract for the planning-hygiene checker. Use the Python standard-library AST to inspect decoded literal values, fold only safe literal forms, and follow protected paths through local helper parameters/calls. Prove lexical component containment for the complete derived path beneath the verified temporary root; reject absolute components, parent traversal, unproven dynamic components and root rebinding. Runtime filesystem symlink resolution is outside this finite static-analysis seam: claim no symlink containment and add no symlink test or platform dependency. If execution reveals an actual symlink-based read escape in the target seam, stop as a new out-of-scope trust/correctness issue. Do not execute inspected source or add a dependency.
- For current candidate validation, require both archived v0.4 blobs and the active Phase 24 route; do not infer historical mode from both archive files being absent. Keep historical validation behind an explicit, full-revision boundary selector.
- Read admission pins as raw Git blob bytes and accept only exactly 40 lowercase hexadecimal ASCII bytes, optionally followed by LF or CRLF; also accept the exact 40 bytes with no terminator. Reject bare CR, whitespace, extra bytes, uppercase, and non-ASCII. Sanitize repository-redirection `GIT_*` variables for temporary-repository operations and assert the selected Git directory and candidate HEAD.
- Add causal negative controls for escaped/concatenated paths, helper-argument flow, temporary-root escape, paired archive removal, malformed pin terminators, and Git environment redirection; retain positive controls for the approved immutable reads, historical boundary, exact archive pair, and valid pin forms. Reuse existing self-test/CTest identities and run cheap checks before longer gates.


### D-219 — Integrated recovery after the D-218 NO-GO (historical; superseded by D-220)

The owner selected all three discussion areas and instructed the agent to follow the fan-out recommendation. The D-218 candidate and NO-GO review remain immutable history. This addendum reopens the sole Phase 24 plan for one integrated recovery. The next step is `$gsd-plan-phase 24`; implementation and checks begin after that plan is updated, independently checked, and committed. The user's prior “extend and execute” authorization applies only to the exact scope and limits below.

#### Python proof boundary and revision integrity

Keep a small, closed, standard-library AST contract for the fixed checker proof surfaces. Reject aliased dynamic-import routes and function `__globals__` access that can replace trusted runtime bindings; reject reflective mutation of proof-sensitive module bindings, including `V04_D209_ARCHIVE_REV`. Refactor self-tests that swap module globals to pass fixture values explicitly. Preserve the approved exact adapter, standard-library full-commit validator, validated revision, and D-209 pin as positive controls. At the Git-facing archive reader, require a full commit identity and prove the exact validated revision and pin reach each immutable read without rebinding. Account for ordinary stores, nested scope shadowing, `MatchAs.name`, `MatchStar.name`, and `MatchMapping.rest`.

Add causal static negatives for the reported `from importlib import import_module as load_module` mutation, `function.__globals__` replacement of `git_run`, direct and `update`-based mutation of `V04_D209_ARCHIVE_REV`, validator-module mutation, and each revision-rebinding form. Parse injected source; never execute the mutation payloads. Avoid general-purpose alias/data-flow analysis and new dependencies. If rejecting all reflective namespace writes in the proof surface is too broad, use a complete finite inventory of proof-sensitive names with one narrow, exact test-only allowance; do not grow a string-key exception list opportunistically.

#### Git environment isolation and inventory-mode CLI

Across the affected immutable-Git checker adapters, preserve the explicit `--no-replace-objects` option and run with a minimal environment that excludes Git variables able to redirect the repository, worktree, common directory, index, object store, alternates, or namespace. Git documents that replacement refs are active by default and that variables such as `GIT_DIR`, `GIT_WORK_TREE`, `GIT_COMMON_DIR`, `GIT_INDEX_FILE`, and object-directory variables change repository or object selection. Reuse the existing small environment helpers where they fit; do not add a general Git wrapper. Add decoy-repository, alternate-index/object-store, and replacement-ref controls that prove the intended immutable object is read and decoy state remains untouched.

For state-fork inventory controls, make inventory mode exclusive with every other operation and all mode-specific inputs. Reject conflicts before Git access or output creation. Exercise the production CLI with one conflicting-argument negative per operation/input class and a valid inventory positive; keep materialization-only parsing as a positive. This addresses argument combinations without altering the admitted manifest set or running excluded diagnostic cases.

#### Recovery, validation, and CI efficiency

The integrated correction is limited to the six checker files already reviewed in D-218: `verify-dense-input.py`, `verify-diagnostic-evidence.py`, `verify-no-phase-paths.py`, `verify-planning-hygiene.py`, `verify-state-forks.py`, and `verify-workflow-policy-coverage.py`. Keep all seven existing focused CTests, their identities, ordering, deadlines, control floors, and required branch-protection contexts. Add causal controls in the existing self-test/CTest seams. Run cheap syntax, immutable-input, source-scope, and direct controls first; then run only the focused seven CTests. Do not run the broad suite, Acid2, any other ROM, or excluded gbmicrotest case. Keep Task 7, FIXT-01, D-103, requirement dispositions, release assets, and milestone closure unchanged.

After the current D-218 NO-GO, allow up to two scoped correction/review passes in this recovery. The first corrected exact-head review is pass one; one in-scope correction and re-review may be pass two. Local diagnosis and targeted retesting may iterate within these findings before review. Stop for any out-of-scope or unresolved correctness/security blocker after pass two. Allow at most one protected PR matrix, and only after a clean final exact-head review. Once that matrix starts, any failed, skipped, stale, or missing required context ends the recovery without a matrix retry. Merge only the identical reviewed head after all required contexts pass under existing branch protection.

The D-218 run did not reach CI and provides no new timing evidence. Apply `.planning/context/WORKFLOW.md#cicd-efficiency` if the authorized matrix runs: capture measured queue, job/step, dependency-wait, package-step, and timeout-headroom data while retaining all required coverage. Make a CI efficiency change only when current measurements prove a safe improvement; do not change triggers, required jobs, timeouts, caches, or concurrency speculatively. Keep the D-211 package-waiter redesign separate.

### D-220 — Scope-bounded convergence after D-219 pass-two NO-GO (verbatim)

The exact-head review of `28ab38f2346a12ef68a07e8a2d403dbfd81b8ba5` returned NO-GO with two Critical findings. The direct frame-namespace denylist can be bypassed by aliasing `getattr` and assembling `_getframe`, `f_globals`, or `f_locals` from string fragments. This permits replacement of `git_run` or the pinned D-209 revision, and a Python 3.13+ write-through `frame.f_locals` mutation can replace a guarded revision after validation. Keep the pass-two report and candidate as immutable failed-review history; D-219’s two-pass authorization is exhausted.

The owner selected **scope-bounded convergence**. Reopen only the existing Phase 24 plan and preserve the same six-checker source boundary plus additive closeout evidence. Within this fixed trust invariant, allow local diagnosis/fix/retest and fresh independent exact-head review to converge without a numerical review-count cap. Every review finding must lead to a changed candidate and a causal source-only control; do not submit an unchanged candidate. If a correction cannot establish concrete progress, or a finding requires a new trust boundary, extra source files, a dependency, a new CTest identity, broader claims, or weaker requirements, stop for owner discussion instead of broadening scope.

Use a small fail-closed standard-library proof boundary rather than a growing list of spellings or a general alias-analysis dependency. Keep valid proof paths as explicit positives. Add causal static mutants for the aliased `getattr`/split-name forms that replace the D-209 pin and `git_run`, and for post-guard `f_locals` revision mutation in `read_rev`, `commit_snapshot`, and `immutable_blob`. Require the intended proof-specific refusal before any Git read. The existing seven focused CTests, deadlines, identities, control floors, original-object Git selection, sanitized Git environments, replacement-ref rejection, archive-pin checks, inventory-mode refusals, and 153-case census remain unchanged. Run the cheapest source/scope/identity controls first, then the seven existing tests serially as already qualified; the local D-219 run took about 61 seconds and provides no evidence for weakening coverage or deadlines. If the protected matrix runs, record real queue, job/step, dependency-wait and timeout-headroom measurements under `.planning/context/WORKFLOW.md#cicd-efficiency`; do not change CI speculatively.

After local qualification, require a fresh independent exact-head review. Only a clean review permits the one protected PR matrix; any failed, skipped, stale, or missing required context ends qualification without a matrix retry. If every required context passes, merge only that identical reviewed head under branch protection. This selected scope authorizes planning only; the revised sole plan must be independently checked and separately authorized for execution before code changes or CI.

Preserve the archived D-209 requirement dispositions, FIXT-01 Pending, the failed and unreplayed Acid2 mismatch, all diagnostic exclusions, D-103, Task 7 deferral, published v0.4.0 bytes, and the administrative v0.4 closeout. No broad suite, ROM/fixture replay, UAT/SUMMARY closure, phase verification, milestone audit/archive, v0.5 start, branch switch, or worktree cleanup follows from this discussion.

**Next route:** `$gsd-plan-phase 24` updates the existing sole plan. Phase 24 remains incomplete; v0.4 remains administratively closed with D-209 gaps.

### the agent's Discretion (verbatim)

### the agent's Discretion
- Select the existing focused CTest targets that match the files and claims touched by the one plan; keep the existing test identities and CMake/Python standard-library patterns.
- Use machine-checkable positive and negative controls for the Phase 24 report so false requirement completion, ownership changes, or milestone closure are rejected.
- Keep source facts, evaluator/reviewer outcomes, current freshness, and remaining authority gates in separate fields to avoid conflating a focused control pass with requirement completion.
- Add no dependency or new CTest identity unless the plan demonstrates a concrete recurring need and stays within this one-plan scope.


### Deferred Ideas (OUT OF SCOPE)

- Candidate-specific rights determination, fixture/source payload acquisition, build/run/admission, and any new candidate require separate explicit owner authorization.
- The D-103 exact-final-head broad suite and milestone archival remain separate owner-controlled gates.
- Other frontmatter prefixes or YAML spellings are outside this BOM-specific recovery; if the authorized independent review identifies a distinct plan-cap bypass or blocker, preserve the stop and return it to the owner rather than extending this correction cycle.
- The D-211 package-preview waiter redesign remains a separate measured follow-up. This recovery records the next run's efficiency evidence but does not change cross-workflow triggers or reduce required contexts.

</user_constraints>

## Summary

D-220 is the current planning authority after the D-219 pass-two exact-head NO-GO. That review found two Critical proof gaps: an aliased `getattr` with constructed attribute strings can reach module globals and replace the approved Git adapter or D-209 pin, and the same path can mutate a validated reader local through `frame.f_locals`. The candidate and review remain failed history. Its seven focused local CTests passed at that exact candidate, but that result does not establish the static proof; no protected matrix or push ran. [VERIFIED: build/phase24/d219-final-review-28ab38f2346a12ef68a07e8a2d403dbfd81b8ba5.md:29-37; build/phase24/d219-final-qualification-28ab38f2346a12ef68a07e8a2d403dbfd81b8ba5.md:22-36]

**Primary recommendation:** In the existing standard-library AST proof, narrowly resolve simple aliases of dynamic attribute lookup and bounded string-literal concatenation only within the fixed proof-bearing source surface. Reject resolved frame/global/local namespace access, reflective writes to proof-sensitive bindings, and any alias or attribute expression whose origin/value cannot be established; keep the existing valid Git adapter, full-commit guard, D-209 pin, and archive-reader paths as positive controls. This gives a concrete refusal for the reported bypass without an expanding spelling denylist or a general Python analyzer. Require the proof-specific refusal before a protected candidate read. Keep the six-checker boundary, the seven existing focused CTests and their current deadlines/floors, and the single protected matrix gated on a clean fresh review. [CITED: https://docs.python.org/3.14/builtins/functions.html#getattr; https://docs.python.org/3.14/reference/datamodel.html#frame-objects; https://peps.python.org/pep-0667/; VERIFIED: .planning/phases/GB-24-resolve-remaining-v0-4-evidence-and-verification-gaps/24-CONTEXT.md:436-448]

An earlier Phase 24 context draft said “the four requirements remain Pending.” The D-215 context update corrects that stale sentence: the authoritative D-209 tracker has seven complete and one pending. Preserve the tracker and D-215 direction: **FIXT-01 remains Pending; do not change original requirement ownership or status.** The archived table states:

> | GAME-01 | Phase 21 | Complete |
> | GAME-02 | Phase 21 | Complete |
> | FIXT-01 | Phase 21 | Pending |
> | RIGHTS-01 | Phase 20 | Complete |
> | DIAG-01 | Phase 22 | Complete |
> | DIAG-02 | Phase 22 | Complete |
> | FEED-01 | Phase 21 | Complete |
> | REL-01 | Phase 23 | Complete |

[VERIFIED: .planning/milestones/v0.4-REQUIREMENTS.md:56-65]

The tracked milestone closeout also says “FIXT-01 remains Pending and deferred,” and that the D-103 gate and Phase 24 Task 7 remain incomplete. The Acid2 DMG-on-CGB mismatch stays failed and unreplayed; a Phase 24 checker pass is point-in-time closeout evidence, not requirement completion, a refreshed Phase 20/21 verification, or milestone closure. [VERIFIED: .planning/milestones/v0.4-REQUIREMENTS.md:67-71; .planning/phases/GB-24-resolve-remaining-v0-4-evidence-and-verification-gaps/24-CONTEXT.md:61-63]

The sole plan currently contains the superseded D-219 pass-count and task sequence; update that existing plan to D-220 before execution. Keep the root roadmap's Phase 24 requirement list empty and do not invent requirement IDs. D-220 authorizes this research and replanning only: the revised plan must pass independent plan checking, and execution still requires the separate authorized handoff. [VERIFIED: .planning/ROADMAP.md:12-32; .planning/phases/GB-24-resolve-remaining-v0-4-evidence-and-verification-gaps/24-CONTEXT.md:436-448]

## Architectural Responsibility Map

| Capability | Primary tier | Secondary tier | Rationale |
|---|---|---|---|
| Detect protected path spellings and readers | Test/checker tooling | CMake/CTest | A repository linter contract; no emulator runtime or user-facing tier is involved. |
| Select immutable historical facts and the live recovery route | Planning evidence checker | Git object database | Facts must come from the selected commit; current route and historical archive are distinct inputs. |
| Create and validate disposable candidate Git repositories | Test harness | Git CLI | Temporary object/HEAD setup is test infrastructure; production fixture admission remains fail-closed. |
| Verify requirement status and closeout limits | Owner decisions and archived tracker | Phase evidence checker | The checker reports evidence; it cannot promote requirements or close the milestone. |
| Assess hosted CI efficiency and qualification | Protected PR workflow | Phase evidence record | Measure the run and preserve all required matrix contexts and branch-protection rules. |

## Project Constraints (from AGENTS.md)

- Prefer existing APIs, Python standard-library code, and small direct helpers; avoid adding a dependency or general-purpose framework. [VERIFIED: AGENTS.md:35-40, 50-52]
- Any checker change belongs in the existing tests/scripts surface, reads immutable commits for boundary facts, uses causal negative controls, and keeps the current CTest identity set. [VERIFIED: AGENTS.md:35-40, 55; .planning/phases/GB-24-resolve-remaining-v0-4-evidence-and-verification-gaps/24-CONTEXT.md:67-70]
- Run cheap identity, syntax, and direct contract checks before longer checks. Do not run the broad local suite, execute excluded diagnostic inputs, change rights/requirement status, or represent phase completion as milestone completion. [VERIFIED: AGENTS.md:35-46; .planning/phases/GB-24-resolve-remaining-v0-4-evidence-and-verification-gaps/24-CONTEXT.md:61-70]
- CI efficiency is measured: retain full test membership and release gates, diagnose timings before changing timeouts, and do not use a faster result that weakens source/artifact binding or branch protection. [VERIFIED: AGENTS.md:42-46; .planning/context/WORKFLOW.md:37-49]
- Merge only the exact reviewed and tested revision after all required protected checks pass. A skipped, stale, or missing context is not a pass. [VERIFIED: AGENTS.md:42-45; .planning/phases/GB-24-resolve-remaining-v0-4-evidence-and-verification-gaps/24-CONTEXT.md:59-63]

## Standard Stack

### Core

| Component | Version observed | Purpose | Recommendation |
|---|---:|---|---|
| Python standard library (ast, tokenize, pathlib, subprocess, tempfile) | Python 3.14.4 in this shell | Parse checker source, track a small finite set of literals/aliases, validate paths, and create disposable Git fixtures. | Reuse the configured project interpreter and standard library; do not add a package. |
| Git CLI | 2.41.0 in this shell | Read immutable blobs/trees, initialize disposable repositories, and validate object/HEAD identity. | Preserve full commit identity and use a minimal, explicit environment for temporary repositories. |
| CMake and CTest | 4.4.3 in this shell | Configure the existing test inventory and run selected registered checks. | Keep existing target names and timeouts unless a measured diagnosis justifies a same-coverage change. |
| OpenGSD runtime | @opengsd/gsd-core 1.20.0, identity confirmed | Phase init, research lookup/cache, and planning workflow. | Continue using the installed project runtime. |

These versions are environment observations, not new minimum-version requirements. The project policy says post-configuration Python checks must use the interpreter recorded in CMakeCache.txt; the shell's python3 version does not prove the configured CTest interpreter or its runtime. [VERIFIED: command output for python3 --version, git --version, cmake --version, ctest --version, and gsd-tools runtime-identity; .planning/context/WORKFLOW.md:42]

### Supporting

| Component | Purpose | Use |
|---|---|---|
| Python ast | Parse Python syntax and inspect actual constant values and call structure. | Decode path strings and inspect the specific checker without executing it. |
| Python tokenize | Preserve lexical token boundaries/source spans. | Connect regex hits and AST nodes; account for byte offsets vs character offsets. |
| Python pathlib | Platform-aware path construction and canonicalization. | Check the complete candidate path after resolution, not a string prefix. |
| subprocess binary capture | Preserve exact Git blob bytes and explicit child environment. | Validate pin bytes before any text decoding, and isolate temporary Git operations. |
| Existing CTest self-tests and protected PR matrix | Regression controls and full cross-platform/release qualification. | Reuse the existing registrations, preserving their required membership. |

**Installation:** None. No package or new tool is required.

### Package Legitimacy Audit

Not applicable: this scope proposes no external package.

### Alternatives Considered

| Instead of | Could use | Tradeoff |
|---|---|---|
| Narrow AST contract and explicit local-call flow | Raw regex/count pin only | Smaller apparent implementation, but escape-decoded literals, literal concatenation, and same-count reader changes evade it. The current reviewer findings demonstrate those bypasses. |
| Narrow finite analyzer with fail-closed unknown flows | General Python static taint engine or executing the source under analysis | A broad analyzer adds complexity/dependency; executing source lets the inspected checker control the validation process. The approved scope needs only a bounded contract for one checker. |
| Validate complete static path components and verified root provenance | Accept a leftmost-root or string-prefix match | A later absolute/parent/dynamic component or rebound root defeats the prefix. Runtime symlink resolution is outside the selected static seam. |
| Raw-byte pin parsing | text=True, strip(), or permissive decoding | Text-mode newline conversion can transform invalid input into an allowed representation; broad trimming accepts more formats than the owner specified. |
| Explicit current/historical revision mode | Infer historical mode from archive absence | A broken current candidate can remove both archives and suppress current-route checks. |

## Architecture Patterns

### System Architecture Diagram

~~~text
Exact candidate revision + source tree
                 |
                 v
       Explicit revision selector
        /                       \
known historical boundary     current recovery candidate
        |                       |
historical snapshot         require archive pair + live route
        \                       /
                 v
        finite checker contracts
    /            |              \
decoded AST   path containment   raw Git pin bytes
    \            |              /
                 v
          causal positive/negative controls
                 |
        cheap identity/syntax checks
                 |
       selected existing focused CTests
                 |
      freeze exact commit and tree identity
                 |
       fresh exact-head independent review
                 |
        one full protected PR matrix
                 |
 exact same reviewed/tested head, all contexts pass
                 |
       conditional protected merge/reconcile
~~~

This is a planning architecture only. D-219 already authorizes the integrated execution after the revised sole plan is independently checked and committed. Local source work and focused tests must converge before the final candidate freeze; only a clean final review permits one protected matrix. A failed, skipped, stale, or missing required context ends the matrix route without retry. Phase and milestone closure remain separate. [VERIFIED: .planning/phases/GB-24-resolve-remaining-v0-4-evidence-and-verification-gaps/24-CONTEXT.md:383-405]

### Recommended Project Structure

No new files are recommended. Keep edits within the existing checker, self-test, CMake/CTest, state-fork inventory, and additive evidence surfaces already named in the sole Phase 24 plan. The canonical references list the current surfaces as tests/scripts/verify-no-phase-paths.py, tests/scripts/verify-diagnostic-evidence.py, tests/scripts/verify-dense-input.py, and tests/scripts/verify-planning-hygiene.py. [VERIFIED: .planning/phases/GB-24-resolve-remaining-v0-4-evidence-and-verification-gaps/24-CONTEXT.md:107-123]

### Pattern 1: Narrow AST path-use contract

**What:** Retain the lexical tracked-file scan, but validate the target Python file's decoded AST string values and finite semantic roles. For approved path-bearing values, bind each value to its exact module binding or named test helper, trace only direct local helper calls into their parameter slots, and reject unknown consumers of a protected path. Fold only constant string concatenation and path segments whose values are proven; do not evaluate arbitrary expressions or import/execute the source. The AST parser reports the value represented by a literal, while Python lexical rules interpret escapes and allow adjacent literal concatenation. [CITED: [Python AST documentation](https://docs.python.org/3/library/ast.html#ast.Constant); [Python lexical analysis](https://docs.python.org/3/reference/lexical_analysis.html)]

**Why this fits:** The existing checker already parses AST and token streams to associate lexical hits with functions/module bindings; the review found the missing contract is recognition of decoded values and flow across function scopes. _source_path_sites scans only text matches, _is_temporary_path accepts any division expression based on the leftmost root, and _validate_path_readers resolves names within each scope without mapping call arguments to callee parameters. [VERIFIED: tests/scripts/verify-no-phase-paths.py:216-265,292-306,394-475]

**Implementation shape:** Preserve SPELLINGS, MUST_SCAN, the historical JSON exception, stale-row rejection, and over-limit rejection. Replace only the verify-planning-hygiene.py count allowance. Use ast.Constant.value and source spans to catch decoded hex/Unicode escapes and adjacent literals, then propagate a protected value through a bounded local-call map. Treat formatted strings with unresolved interpolations, *args/**kwargs, ambiguous aliases, dynamic path components, and unknown callees as unproven and fail closed when they carry the protected path. Include same-count mutations so a matching lexical count cannot mask a switch from immutable Git reads to live filesystem reads. [VERIFIED: tests/scripts/verify-no-phase-paths.py:44-96,216-265,394-509; .planning/phases/GB-24-resolve-remaining-v0-4-evidence-and-verification-gaps/24-CONTEXT.md:67-70]

**Path containment:** The selected CR-03 contract is a finite static proof over complete path expressions and verified TemporaryDirectory root provenance. Reject absolute/drive/UNC right-hand components, parent traversal, unproven dynamic components and root rebinding; allow only supported components that establish lexical containment under that root. A leftmost-root or string-prefix match is insufficient, and PurePath.is_relative_to() alone does not interpret parent components, so reject those components explicitly. Runtime filesystem symlink resolution is outside this source AST seam; claim no symlink containment and add no symlink fixture/platform dependency. If execution reveals an actual symlink-based read escape in the target seam, stop as a new out-of-scope trust/correctness issue. [CITED: [Python pathlib containment documentation](https://docs.python.org/3/library/pathlib.html#pathlib.PurePath.is_relative_to)]

**Source-coordinate footgun:** Python AST col_offset and end_col_offset are UTF-8 byte offsets, while tokenize positions are character columns. Convert consistently or use APIs that honor AST offsets; add a source fixture with a multibyte character before the relevant token so a source-span mismatch cannot hide an escape. [CITED: [Python AST node location documentation](https://docs.python.org/3/library/ast.html)]

### Pattern 2: Explicit immutable historical versus current snapshot

**What:** Select historical behavior only for an explicitly enumerated full historical boundary revision. For every other current candidate, require both archived v0.4 blobs, reject restored root requirements, and validate the active Phase 24 route and sole-plan pointer. Do not let simultaneous archive absence select a permissive legacy fallback. Keep current evidence and historical facts separate in the report. [VERIFIED: tests/scripts/verify-diagnostic-evidence.py:277-289,630-655]

**Controls:** Keep a positive for the explicitly recognized historical boundary and a positive for the exact current archive pair plus route. Add causal negatives for removing both archive blobs, removing one archive, a missing/wrong route, restoring root requirements, and a revision that is not the declared historical boundary. The no-archive current candidate must fail as an incomplete current candidate, not be reclassified as legacy. [VERIFIED: .planning/phases/GB-24-resolve-remaining-v0-4-evidence-and-verification-gaps/24-CONTEXT.md:67-70]

### Pattern 3: Exact pin bytes and temporary Git isolation

**What:** Read the Git pin blob as bytes; accept only the exact forms copied in D-215's locked decision, and decode only after the byte pattern has passed. Do not use text-mode output, broad strip(), or error-replacing decoders. Python documents that subprocess text mode converts output line endings to LF, while default binary capture preserves bytes without newline conversion. [CITED: [Python subprocess documentation](https://docs.python.org/3/library/subprocess.html)]

**Existing helper precedent:** verify-planning-hygiene.py already builds a narrow child environment using only PATH, SYSTEMROOT, TMPDIR, TEMP, and TMP, then sets GIT_CONFIG_GLOBAL and GIT_CONFIG_SYSTEM to the null device. Reuse that isolation pattern for temporary Git operations and add assertions that Git resolves to the intended temporary repository, candidate full HEAD, and expected Git directory. [VERIFIED: tests/scripts/verify-planning-hygiene.py:220-224]

Git documents that GIT_DIR can replace the default repository directory, GIT_WORK_TREE selects another working tree, and other GIT_* variables can redirect index or object storage. Therefore sanitization plus explicit rev-parse assertions is an inference-backed defense for the harness; the Git documentation specifies the redirection behavior but does not prescribe this project's exact environment allowlist. [CITED: [Git environment variables](https://git-scm.com/docs/git#_environment_variables)]

**Controls:** Keep positive controls for valid exact pin forms and the correct temp repository. Reject bare CR, whitespace, uppercase, extra bytes, non-ASCII bytes, inherited repository-redirection variables, a redirected Git directory, missing candidate object, wrong HEAD, and missing pin ancestry. Assert the selected Git root and object context before using the temporary repo. [VERIFIED: .planning/phases/GB-24-resolve-remaining-v0-4-evidence-and-verification-gaps/24-CONTEXT.md:67-70; tests/scripts/verify-dense-input.py:134-137,158-202]

### Pattern 4: Measured CI efficiency without coverage changes

**What:** Run cheap changed-contract checks before the one expensive hosted matrix, then capture actual job and step durations, queue/dependency waits, and timeout headroom from the exact candidate's run. Preserve required matrix membership, platform coverage, branch protection, artifact identity, and release authority. Make no speculative cache, concurrency, trigger, or workflow-run change in this correction; the package-waiter redesign stays a separate follow-up. [VERIFIED: .planning/context/WORKFLOW.md:37-49; .planning/phases/GB-24-resolve-remaining-v0-4-evidence-and-verification-gaps/24-CONTEXT.md:59-70]

**Recorded baseline:** The plan records: “The Linux suite stream lasted about 37 minutes and reported 44 failures; three package consumers each waited about 70 minutes before package configure/build/smoke steps were skipped.” This is historical D-211 evidence, not a new measurement or proof that the same wait dominates the next run. It supports measuring the next run, but not changing matrix membership or workflow triggers. [VERIFIED: .planning/phases/GB-24-resolve-remaining-v0-4-evidence-and-verification-gaps/24-01-PLAN.md:142]

### Anti-Patterns to Avoid

- Raising the lexical allowance to match current hit count or exempting the whole Python checker.
- Treating a directory prefix, leftmost path operand, or lexical is_relative_to() test as proof that the final path stays under the temp root.
- Running code under analysis or accepting arbitrary helper calls without tracking the protected argument.
- Choosing historical mode because required archive paths are missing.
- Normalizing pin bytes with text=True, strip(), permissive decoding, or repeated rstrip() of CR/LF.
- Passing ambient GIT_* environment variables into a temporary repository and treating cwd alone as proof of repository identity.
- Using a clean local result, stale job record, skipped context, or pre-review SHA as evidence that the protected reviewed head is green.
- Changing Actions workflow triggers, required jobs, cache/concurrency behavior, or timeouts without measured evidence and separate scope.

## Don't Hand-Roll

| Problem | Don't build | Use instead | Why |
|---|---|---|---|
| Python source parsing | Regex-only source parser or eval of inspected code | ast plus tokenize and a finite contract | Python escapes, concatenation, source positions, helper calls, and f-strings require syntax-aware handling without executing source. |
| Static path components | String-prefix acceptance or a general runtime filesystem evaluator | Existing AST plus pathlib pure component APIs and explicit parent/absolute/dynamic rejection | The finite contract must validate every component and root binding; it does not claim runtime symlink containment. |
| Git blob integrity | Text-normalization and permissive string trimming | Binary subprocess capture plus exact bytes validation | Text I/O deliberately normalizes newlines. |
| General Python taint analysis | New package or broad interpreter | Small, scoped propagation for direct local helper calls; reject unknown flows | The source boundary is one checker, and unknown behavior should be visible instead of guessed. |
| CI optimization | Unmeasured caches or reduced required checks | Existing local gates before the full required matrix; retain timing evidence | Keep correctness and security coverage while cutting avoidable iteration delay. |

**Key insight:** The six findings are trust-boundary failures: source spelling versus decoded value, leftmost root versus complete static path components, current candidate versus historical snapshot, and child process intent versus ambient Git context. The smallest reliable solution makes each selected boundary explicit and verifies the consequence with a causal negative control.

## Common Pitfalls

### Pitfall 1: Counting text rather than checking decoded semantics

**What goes wrong:** An escaped or concatenated value can name the protected path without matching the raw spelling regex. A same-count edit can turn an approved fixture/source literal into a live filesystem read.
**Avoid:** Check decoded AST constants, explicit safe folds, semantic owner/consumer roles, and a same-count reader mutation.
**Warning sign:** The acceptance rule only compares hit count or raw source spelling. [VERIFIED: tests/scripts/verify-no-phase-paths.py:216-265,484-509]

### Pitfall 2: Losing protected taint at a call boundary

**What goes wrong:** A caller passes the protected path to a helper whose parameter becomes a Path reader; function-local assignment analysis never links the two scopes.
**Avoid:** Propagate exact positional/keyword arguments to known local parameters; reject unknown consumers, ambiguous binding, unpacking, and unsupported flows.
**Warning sign:** Tests cover only direct Path(...).read_text() in the same scope. [VERIFIED: tests/scripts/verify-no-phase-paths.py:394-475; /private/tmp/24-D214-REVIEW.md]

### Pitfall 3: Assuming the leftmost temporary root contains the final path

**What goes wrong:** Later static path components can escape through absolute path replacement, parent traversal, dynamic construction or root rebinding.
**Avoid:** Analyze the complete expression from proven components and root provenance, reject absolute/parent/unproven dynamic segments and root rebinding, and exercise causal component-escape negatives. Runtime symlink resolution is outside this finite AST contract.
**Warning sign:** A path is approved whenever its syntax begins with the temporary root. [VERIFIED: tests/scripts/verify-no-phase-paths.py:292-306; [Python pathlib documentation](https://docs.python.org/3/library/pathlib.html)]

### Pitfall 4: Missing archive pair silently selects weaker checks

**What goes wrong:** Removing both archives makes the selector treat a current candidate as legacy and skips current-route validation.
**Avoid:** Use an exact full revision allowlist for historical mode; all other candidates require the archive pair and active route.
**Warning sign:** Selector's only mode discriminator is the presence/absence of files. [VERIFIED: tests/scripts/verify-diagnostic-evidence.py:277-289,630-639]

### Pitfall 5: Text mode changes bytes before pin validation

**What goes wrong:** Python's text wrapper may normalize CR/CRLF output, causing an invalid byte sequence to appear acceptable.
**Avoid:** Capture the Git blob as bytes and compare against only the owner-approved exact byte forms.
**Warning sign:** stdout is a string or a parser strips all trailing whitespace. [VERIFIED: tests/scripts/verify-dense-input.py:134-165; [Python subprocess documentation](https://docs.python.org/3/library/subprocess.html)]

### Pitfall 6: Ambient Git environment points the harness elsewhere

**What goes wrong:** Temporary commands may use the main worktree, another .git directory, a separate index, or alternate object storage.
**Avoid:** Build the child environment from the existing safe allowlist, set Git config locations explicitly, and assert the selected temp repo/HEAD before checking pins.
**Warning sign:** Git command helper inherits os.environ and relies only on cwd. [VERIFIED: tests/scripts/verify-dense-input.py:134-137,189-202; tests/scripts/verify-planning-hygiene.py:220-224; [Git environment variables](https://git-scm.com/docs/git#_environment_variables)]

### Pitfall 7: Treating timing history as a current optimization result

**What goes wrong:** A prior failed matrix's durations may not describe the new candidate, runner state, or critical path.
**Avoid:** Preserve D-211 timings as historical evidence and measure the next authorized run before proposing a workflow change.
**Warning sign:** Projected savings are written as measured savings or justify dropping a required consumer. [VERIFIED: .planning/context/WORKFLOW.md:41-49; .planning/phases/GB-24-resolve-remaining-v0-4-evidence-and-verification-gaps/24-01-PLAN.md:142]

## Code Examples

Verified implementation patterns from official documentation. These are design sketches, not implementation authorization.

### Read string literal values through the AST

~~~python
tree = ast.parse(source_text)
values = [
    node.value
    for node in ast.walk(tree)
    if isinstance(node, ast.Constant) and isinstance(node.value, str)
]
~~~

ast.Constant.value represents the Python object encoded by the literal. Adjacent literal concatenation and escape processing are Python lexical behavior; dynamic f-string fields are not a constant whole and must not be evaluated. [CITED: [Python AST documentation](https://docs.python.org/3/library/ast.html#ast.Constant); [Python lexical analysis](https://docs.python.org/3/reference/lexical_analysis.html)]

### Prove static component containment without filesystem evaluation

The accepted analyzer follows a verified temporary-root binding through only supported AST expressions. For every suffix it determines the complete literal components, rejects absolute/drive/UNC forms and parent components, and refuses any unproven dynamic construction or root rebinding. It then checks the full derived component sequence rather than approving a leftmost-root prefix. Do not execute source or resolve runtime filesystem targets in this static analysis. PurePath containment APIs do not interpret parent components on their own; explicit rejection is part of the proof. [CITED: [Python pathlib containment documentation](https://docs.python.org/3/library/pathlib.html#pathlib.PurePath.is_relative_to)]

### Capture a Git integrity blob without text conversion

~~~python
result = subprocess.run(
    argv,
    cwd=repo,
    env=clean_environment,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    check=False,
)
raw_blob = result.stdout
~~~

With no text/encoding option, subprocess streams stay binary; validate exact bytes before decoding. [CITED: [Python subprocess documentation](https://docs.python.org/3/library/subprocess.html)]

## State of the Art

| Old approach | Recommended current approach | Why it matters here |
|---|---|---|
| Regex-only or count-only source exception | AST constants + finite semantic/path-use contract | Runtime string values can differ from raw spelling, and equal counts can hide changed behavior. |
| Leftmost-root prefix | Validate the full static component sequence and root binding | Later absolute/parent/dynamic components or a rebound root defeat the prefix; runtime symlink containment is not claimed. |
| Text output for integrity pins | Raw bytes, exact allowlist | Text I/O deliberately normalizes newlines. |
| Archive-presence inferred historical mode | Exact historical revision selection | Missing current state must fail closed. |
| Current process environment inherited by Git fixture | Narrow allowlisted child environment and identity assertions | GIT_* can redirect repository operations. |
| CI optimization by skipped work or guessed timeout | Measured stage costs with required coverage intact | Reliability depends on the full protected matrix, not a faster partial run. |

No new package or framework is indicated. The standard-library approach is sufficient for this finite checker contract; use the project's configured interpreter and existing CTest seams. [VERIFIED: AGENTS.md:35-43; .planning/config.json:20-38]

## Assumptions Log

| # | Claim | Section | Risk if wrong |
|---|---|---|---|
| A1 | Runtime symlink creation/resolution remains outside the finite static-analysis seam inherited from prior locked decisions. [RESOLVED; historical D-215 scope, retained only where still applicable] | Pattern 1, validation | No symlink portability or platform-permission assumption is needed; an actual symlink-based read escape revealed during execution stops as a new out-of-scope issue. |
| A2 | The configured CMake Python interpreter may differ from the shell interpreter. [ASSUMED] | Standard Stack, Environment | A source check can pass under a different interpreter than CTest uses; inspect CMakeCache after configure as directed by workflow policy. |
| A3 | The project's formal supported Python version range is unresolved. CMake's current `find_package` call requests an interpreter without a numeric minimum, while the D-219 qualification records one configured interpreter version, 3.14.4. [ASSUMED] | D-220 version scope | Treat 3.14.4 as a qualification observation, not a support matrix; a different supported-version claim needs a positive project declaration and matching validation. |

## Open Questions

1. **RESOLVED — D-219 review-pass count (historical; superseded by D-220):** D-219's two-pass cap is exhausted with the pass-two NO-GO. D-220 allows scope-bounded local diagnosis/fix/retest and fresh exact-head review to converge without a numeric review-count cap; every cycle requires a changed candidate and causal control, and lack of concrete progress or scope expansion stops for owner discussion. One protected matrix remains available only after a clean fresh review, with no retry after failed/skipped/stale/missing required context. [VERIFIED: .planning/phases/GB-24-resolve-remaining-v0-4-evidence-and-verification-gaps/24-CONTEXT.md:436-444]
2. **RESOLVED — CR-03 containment scope and symlink portability:** The approved seam proves lexical component containment in the source AST by rejecting absolute, parent, unproven dynamic and root-rebinding escapes. Runtime filesystem symlink resolution is outside these six findings and this finite seam. Claim no symlink containment, add no symlink test/platform dependency, and stop if execution reveals an actual symlink-based read escape as a new out-of-scope trust/correctness issue. Archive-blob symlink refusal remains part of the distinct current/archive contract.

No additional requirement-status, rights, release, suite, or milestone decision is needed for planning; D-219 and D-209 already define those boundaries. Preserve FIXT-01 as Pending, Task 7 and D-103 as separate, Acid2 failed and unreplayed, and v0.4 dispositions unchanged. [VERIFIED: .planning/phases/GB-24-resolve-remaining-v0-4-evidence-and-verification-gaps/24-CONTEXT.md:399-405; .planning/milestones/v0.4-REQUIREMENTS.md:56-71]

## Environment Availability

| Dependency | Required by | Available in this research environment | Version/observed state | Fallback |
|---|---|---:|---|---|
| Python 3 | Syntax, AST, and checker controls | Yes | 3.14.4 | Use the CMake-configured interpreter during later CTest validation. |
| Git | Immutable snapshots and temporary repo controls | Yes | 2.41.0 | None for Git-backed contracts. |
| CMake / CTest | Existing focused validation | Yes | 4.4.3 | None for registered project targets. |
| GitHub protected PR checks | Final exact-head matrix | Not probed; no CI was started | D-219 permits one complete protected matrix after a clean final exact-head review | No local result substitutes for protected checks. |

Versions are read-only environment probes; no configure, build, CTest, source execution, GitHub query, review, push, or CI run occurred during this research.

## Validation Architecture

> Planning guidance for regenerating 24-VALIDATION.md under D-219. This plan command does not itself start implementation, local tests, review, push, CI, or merge. The prior extend-and-execute authorization becomes actionable after the revised plan passes independent checking and is committed.

### Test Framework

| Property | Value |
|---|---|
| Framework | Existing Python standard library and CMake/CTest |
| Config file | Existing CMake preset and CTest registrations |
| Quick run command | The current validation document's syntax-only command over the six affected Python checkers: python3 -I -c 'import ast,pathlib; paths=("tests/scripts/verify-dense-input.py","tests/scripts/verify-diagnostic-evidence.py","tests/scripts/verify-planning-hygiene.py","tests/scripts/verify-state-forks.py","tests/scripts/verify-no-phase-paths.py","tests/scripts/verify-workflow-policy-coverage.py"); [ast.parse(pathlib.Path(p).read_text(encoding="utf-8"), filename=p) for p in paths]'. This is only a proposed post-authorization cheap gate, not run here. [VERIFIED: .planning/phases/GB-24-resolve-remaining-v0-4-evidence-and-verification-gaps/24-VALIDATION.md:16-23] |
| Focused run command | Inspect exact registered commands using CTest's --show-only=json-v1; run only existing targets mapped below, after source revision, route/archive, candidate ancestry, and non-ROM identity checks pass. |
| Full suite | Excluded from this scope; D-103 remains separate. |
| Phase verification | Separate boundary outside D-219; do not run it as part of this recovery. |

The phase has no requirement IDs: root roadmap says “**Requirements:** []”. There is no phase requirement-to-test table to fabricate. [VERIFIED: .planning/ROADMAP.md:20]

### Finding-to-Validation Map

| Earlier finding / current contract | Existing control surface | Purpose |
|---|---|---|
| CR-01 decoded/escaped path strings; CR-02 helper argument flow; CR-03 complete path containment | no_phase_paths_controls and no_phase_paths | Self-test causal negatives plus the complete tracked-file scan and must-scan floor. Existing registration lines quote the names exactly: add_test(NAME no_phase_paths_controls ...) and add_test(NAME no_phase_paths ...). [VERIFIED: tests/CMakeLists.txt:3004-3020] |
| CR-04 current/archive selection | phase22_evidence_controls and phase22_evidence_contract | Paired archive-removal negative and current-route positive in existing immutable evidence checker controls/contract. [VERIFIED: tests/CMakeLists.txt:3785-3799] |
| WR-01 raw byte pin parsing; WR-02 Git environment redirection | Existing non-ROM candidate Git-context controls in the dense-input harness; full fixture-bearing behavior stays in the protected matrix | Controls must mutate pin bytes/environment and assert exact rejection before any fixture execution. Do not invent a CTest target or run the fixture-bearing self-test locally. [VERIFIED: tests/scripts/verify-dense-input.py:134-202; .planning/phases/GB-24-resolve-remaining-v0-4-evidence-and-verification-gaps/24-VALIDATION.md:30] |
| D-218 Python binding and revision proof | no_phase_paths_controls and planning_hygiene_controls, with the approved exact adapter/runtime read positive | Parse injected mutations only; reject aliased dynamic import, `__globals__` replacement, proof-global mutation, match-capture/revision rebinding, changed helper arguments, weak/missing reader guard, and changed D-209 pin. Do not execute mutation payloads. |
| D-219 Git object integrity and inventory CLI | Existing controls in all six named checkers, selected through the same seven CTests | Add replacement-ref and hostile repository/index/object-store/namespace cases, checking both selected original objects and untouched decoys. Production CLI conflict negatives must refuse before Git operations or output effects; retain valid inventory and materialization-only positives. |
| Full current trust/route contract | `plan_cap`, `phase22_evidence_controls`, `phase22_evidence_contract`, `no_phase_paths_controls`, `no_phase_paths`, `workflow_policy_coverage_controls`, and `planning_hygiene_controls` | Keep the existing identities and qualified order, with `plan_cap` first and `planning_hygiene_controls` last. Preserve each registered deadline/floor, including the 30-second hygiene timeout and 125-control floor; do not increase timeout or weaken scan/control floors. [VERIFIED: tests/cmake/hygiene.cmake:73-85; tests/CMakeLists.txt:3004-3020,3785-3799; tests/cmake/ci-lanes.cmake:144-148] |

The exact existing registered CTest identifiers are `plan_cap`, `phase22_evidence_controls`, `phase22_evidence_contract`, `no_phase_paths_controls`, `no_phase_paths`, `workflow_policy_coverage_controls`, and `planning_hygiene_controls`. The source-of-truth registrations quote `gbb_add_hygiene_test(plan_cap ...)` and `gbb_add_hygiene_test(planning_hygiene_controls ...)`, `add_test(NAME no_phase_paths_controls ...)` and `add_test(NAME no_phase_paths ...)`, `add_test(NAME phase22_evidence_contract ...)` and `add_test(NAME phase22_evidence_controls ...)`, plus `gbb_add_ci_lane_test(workflow_policy_coverage_controls ...)`. [VERIFIED: tests/cmake/hygiene.cmake:73-84; tests/CMakeLists.txt:3004-3020,3785-3791; tests/cmake/ci-lanes.cmake:147-148]

**Order:** First verify exact candidate/revision identity, syntax for all six files, current route/archive blobs, no unexpected source changes, candidate ancestry, and changed-seam direct controls. Inspect configured CTest JSON before execution. Run the seven existing focused tests in the approved order, with the cheap `plan_cap` first and `planning_hygiene_controls` last. Preserve test membership and registered limits. Keep failure causes, test identities, environment, candidate SHA/tree, and any timeout stage in evidence. No test was run during this research. [VERIFIED: .planning/phases/GB-24-resolve-remaining-v0-4-evidence-and-verification-gaps/24-VALIDATION.md:20-23,35-49; .planning/context/WORKFLOW.md:41-49]

### Sampling Rate

- **Before each task's focused tests:** cheap syntax/identity checks and direct positive/negative controls for the specific changed seam.
- **Before CTest:** full candidate preflight from immutable Git objects, then --show-only=json-v1 inspection; no ROM-bearing local command.
- **Before remote qualification:** after local convergence freeze the complete candidate SHA/tree; allow at most two scoped correction/review passes total after D-218 NO-GO (the first corrected exact-head review is pass one, one correction/re-review is pass two); run one full protected matrix only after a clean final exact-head review, with all current required contexts.
- **Stop:** any out-of-scope trust/correctness issue, unresolved blocker after pass two, unavailable review, or failed/skipped/stale/missing required CI context. No review or matrix retry is implied.
- **Timeout policy:** preserve current limits until measured stage evidence identifies the cause; do not raise timeout to hide the failed step.

### Wave 0 Gaps

None. Existing standard-library controls and registered CTests are the intended implementation seams. No dependency, checker, CTest identity, phase, or second plan is needed. The six checker paths and exact seven-test inventory are already established.

### Manual-Only Verifications

None for the deliverable. Independent review and protected CI are later automated gates. Do not add manual UAT or claim a human review/CI result during planning.

## Security Domain

The project config contains `"security_enforcement": true`, `"security_asvs_level": 1`, and `"security_block_on": "high"`. These are project workflow settings, not evidence that this local checker is ASVS-certified. [VERIFIED: .planning/config.json:48-50]

Use OWASP ASVS 5.0.0 as a current taxonomy reference for this research only; this mapping does not adopt or change a project-standard version. The official standard names chapters V1 Encoding and Sanitization, V2 Validation and Business Logic, V5 File Handling, V11 Cryptography, and V13 Configuration. [CITED: https://asvs.owasp.org/; https://github.com/OWASP/ASVS/blob/master/5.0/docs_en/OWASP_Application_Security_Verification_Standard_5.0.0_en.csv]

### Applicable ASVS Categories

| Category | Applies | Control |
|---|---:|---|
| V1 Encoding and Sanitization | Relevant | Treat escaped/concatenated source literals as their runtime values; do not execute inspected source. |
| V2 Validation and Business Logic | Relevant | Fail closed on unknown helper flow, unsafe path components, malformed pin bytes, missing archives, and invalid candidate state. |
| V5 File Handling | Relevant | Prove lexical component containment beneath the verified temporary root in the finite source AST seam. |
| V11 Cryptography | Limited | Reuse Git object identity and existing digest checks; do not invent cryptography or treat a hash as a rights decision. |
| V13 Configuration | Relevant | Sanitize inherited Git redirection variables and assert the selected repository context. |

These are a threat-oriented mapping to current ASVS chapter names, not a claim that every chapter requirement applies or that compliance verification was performed. Authentication, session, authorization, API, and browser chapters have no relevant surface in this local checker scope. [CITED: https://asvs.owasp.org/]

### Known Threat Patterns

| Pattern | STRIDE | Mitigation |
|---|---|---|
| Encoded path hides a live-tree read | Tampering / Information disclosure | Inspect AST runtime string values and readers; use a causal negative. |
| Parameter flow hides a protected reader | Information disclosure | Propagate known local call arguments to parameters; refuse unknown flow. |
| Static path components escape temp root | Information disclosure | Validate complete components/root binding, reject absolute/parent/unproven dynamic/root-rebinding escape, and test the selected static contract. |
| Both archive blobs removed to trigger legacy branch | Tampering | Historical mode requires an explicit full revision; current mode requires pair and route. |
| CR-normalized pin accepted as exact identity | Tampering | Capture raw bytes and validate exact byte forms. |
| GIT_DIR/GIT_WORK_TREE redirects temporary operations | Tampering | Sanitize child environment and assert Git root/HEAD. |
| A namespace or aliased-import write replaces the checked runtime adapter, regex validator, or D-209 pin | Tampering / elevation of privilege | Use a closed source-only AST contract over the fixed proof surface; reject unsupported reflective forms and preserve exact accepted binding positives. |
| A full SHA is validated and then rebound, or Git substitutes another object through refs/replace | Tampering | Recheck the full commit at the Git reader, prove the finite caller-to-reader value flow, disable replacement refs on every trusted Git call, and retain replacement-object negatives. |
| Inherited Git variables redirect a candidate read to a decoy repository/index/object store | Tampering | Use the existing narrow Git environment helper, remove redirection selectors, and assert that the expected repository and untouched decoy are observed. |
| `--inventory-controls` is combined with a runner, materialization, or mode-specific path and still reports success | Tampering / denial of service | Refuse every conflicting mode and input before Git or filesystem effects; test the real CLI with side-effect sentinels and valid-mode positives. |
| Stale/missing CI context treated as green | Tampering / repudiation | Bind check runs to exact reviewed head and require all protected contexts to pass. |

Security claims about ASVS category applicability are task-domain mapping, not certification or a claim of completed security verification.

## CI and CD Efficiency

D-211's recorded 37-minute Linux stream with 44 failures and three preview consumers waiting roughly 70 minutes each is historical, not a D-219 matrix measurement; D-219 did not reach CI. The immediate safe improvement is shorter feedback before the single D-220-authorized hosted matrix: syntax/identity checks, immutable boundary/source-scope checks, direct causal controls, then only the existing seven focused CTests. The matrix itself remains complete and protected. [VERIFIED: .planning/phases/GB-24-resolve-remaining-v0-4-evidence-and-verification-gaps/24-CONTEXT.md:436-444; .planning/context/WORKFLOW.md:41-49]

For the sole authorized PR matrix, record candidate SHA/tree, each job and step duration, queue time, dependency wait, timeout headroom, and whether package steps actually executed or were skipped. Recommend a safe workflow change only if that run provides evidence; otherwise record “no justified safe change.” Do not redesign cross-workflow waiters here, change triggers, add speculative cache/concurrency, or reduce required contexts. The D-211 package-waiter redesign is a separate measured follow-up. [VERIFIED: .planning/context/WORKFLOW.md:39-49; .planning/phases/GB-24-resolve-remaining-v0-4-evidence-and-verification-gaps/24-CONTEXT.md:436-444]

## Sources

### Primary repository sources

- [VERIFIED: .planning/phases/GB-24-resolve-remaining-v0-4-evidence-and-verification-gaps/24-CONTEXT.md:383-405] — Current D-219 scope, limits, role synthesis, and extend-and-execute authorization boundary.
- [VERIFIED: /private/tmp/24-D214-REVIEW.md:17-67] — Exact D-214 review text for CR-01–CR-04 and WR-01–WR-02; no tests or CI were run for that review.
- [VERIFIED: .planning/milestones/v0.4-REQUIREMENTS.md:56-71] — Authoritative archived requirement ownership/status and D-209 closeout.
- [VERIFIED: tests/scripts/verify-no-phase-paths.py:216-265,292-306,394-509] — Existing AST/token/source-site and path-reader implementation with reviewed gaps and runtime-binding proof surface.
- [VERIFIED: tests/scripts/verify-diagnostic-evidence.py:277-289,630-655] — Archive-pair fallback and current route conditional.
- [VERIFIED: tests/scripts/verify-dense-input.py:134-202] — Text-mode Git helper, pin validation, and temporary candidate repository setup.
- [VERIFIED: tests/scripts/verify-planning-hygiene.py:221-268,271-281,320-406,514-526,4529-4558] — Existing small sanitized Git environment, immutable blob reader, exact D-209 pin, revision helpers, and production CLI.
- [VERIFIED: tests/scripts/verify-state-forks.py:73-86,1467-1527] — Existing Git environment, `--no-replace-objects` adapter, inventory CLI mode and pre-side-effect conflict check.
- [VERIFIED: tests/scripts/verify-workflow-policy-coverage.py:25-41] — Pinned workflow-policy source/revision contract in the sixth affected checker.
- [VERIFIED: .planning/context/WORKFLOW.md:37-49] — CI efficiency rules.
- [VERIFIED: .planning/phases/GB-24-resolve-remaining-v0-4-evidence-and-verification-gaps/24-01-PLAN.md:142] — Historical D-211 duration and waiter evidence.
- [VERIFIED: tests/cmake/hygiene.cmake:73-85; tests/CMakeLists.txt:3004-3020,3785-3799; tests/cmake/ci-lanes.cmake:144-148] — Existing focused CTest identities and local floors/timeouts.

### Official documentation

- Python AST: [ast — Abstract Syntax Trees](https://docs.python.org/3/library/ast.html)
- Python 3.14 dynamic attribute lookup and module namespaces: [Built-in Functions](https://docs.python.org/3.14/builtins/functions.html#getattr)
- Python 3.14 frame global and local namespaces: [Data Model — Frame Objects](https://docs.python.org/3.14/reference/datamodel.html#frame-objects)
- Python 3.14 frame and function namespace members: [inspect — Types and Members](https://docs.python.org/3.14/library/inspect.html#types-and-members)
- Python 3.13 write-through frame-local semantics: [PEP 667](https://peps.python.org/pep-0667/)
- Python 3.14 AST node model: [ast — Abstract Syntax Trees](https://docs.python.org/3.14/library/ast.html)
- Python lexical rules: [Lexical analysis](https://docs.python.org/3/reference/lexical_analysis.html)
- Python paths: [pathlib](https://docs.python.org/3/library/pathlib.html)
- Python subprocess behavior: [subprocess](https://docs.python.org/3/library/subprocess.html)
- Python function-global namespace: [data model — function `__globals__`](https://docs.python.org/3/reference/datamodel.html#function.__globals__)
- Python mutual exclusion for CLI arguments: [argparse — mutually exclusive groups](https://docs.python.org/3/library/argparse.html#mutual-exclusion)
- Git environment behavior: [git documentation](https://git-scm.com/docs/git)
- Git original-object behavior: [git-replace](https://git-scm.com/docs/git-replace)
- Git byte-safe tree paths: [git-ls-tree](https://git-scm.com/docs/git-ls-tree)
- Protected status-check behavior: [GitHub protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)
- OWASP ASVS 5.0.0 taxonomy: [official ASVS overview](https://asvs.owasp.org/); [official OWASP ASVS 5.0.0 CSV](https://github.com/OWASP/ASVS/blob/master/5.0/docs_en/OWASP_Application_Security_Verification_Standard_5.0.0_en.csv)

### Sources not used

No external package, product recommendation, or third-party fixture research was needed for this checker-and-CI recovery. Context7 tools were unavailable in this agent environment; official Python and Git documentation was opened directly as the documentation fallback.

## Metadata

**Confidence breakdown:**
- In-repository decisions and current test seams: HIGH — source-of-truth files were opened and exact task/CTest contracts were read.
- Python/Git behavior: MEDIUM — confirmed against official documentation; implementation must use the interpreter and OS configuration selected by the actual CMake build.
- CI efficiency opportunities: MEDIUM — the D-211 data is a recorded historical run; measure the next authorized exact-head matrix before claiming a current bottleneck or savings.

**Research date:** 2026-11-18
**Valid until:** Revisit if Python/Git version requirements, D-219 authority, phase requirements, or CI matrix membership change.
**Historical note:** D-215 through D-218 statements retain earlier decisions, review history, and technical findings. Any earlier scope, pass-count, or execution-boundary statement not reaffirmed by D-219 is historical, not current authority. The current scope, pass count, CI gate, and merge condition are stated in the D-219 addendum below, which supersedes contradictory earlier statements.

## D-216 Review Addendum — Escaped Paths, Git Isolation and Exact Tree Census

The D-215 review receipt at candidate `e1d3200b1568fb619759c0f31cf4a8605e57ea06` identified four new trust-boundary defects. Three are in already-scoped checker surfaces; the newline-bearing tree-path omission was newly out of scope until the owner explicitly extended the same plan. The owner now authorizes all four, but no wider inventory or admission change.

### Findings and bounded remedies

| Finding | Failure mode | Bounded remedy and causal control |
|---|---|---|
| Escaped path construction | Protected-value analysis does not see `Path(chr(46) + "planning/phases/private.md").read_text()` if the seed depends on recognized literal spellings. | Fold only a direct, one-integer-literal `chr()` call in the finite evaluator; leave arbitrary calls unresolved. Run the semantic reader detector even without a lexical hit. Inject this exact reader into disposable checker source and require the live-phase-reader refusal. |
| Helper name as trust | A resolved function named `git_run` is exempt even if its body adds live path traversal. | Inspect the narrow helper body or enforce an equally narrow structural contract for the reviewed immutable Git adapter. Mutate its body to use `(repo / args[-1]).iterdir()` and require a causal refusal while keeping the lexical count fixed. |
| Git environment inheritance | The diagnostic evidence helper's generic process runner forwards all `GIT_*`; its boundary-history control writes a synthetic repository. | Preserve generic non-Git execution; use a minimal allowlist for Git-only children, clear repository/index/object/config redirects, and assert candidate Git-dir/worktree/HEAD before writes under hostile `GIT_DIR` and `GIT_WORK_TREE`. Use a decoy and prove its refs/index/status remain unchanged; restore injected variables in `finally`. |
| Newline-bearing Git paths | Text-mode, line-delimited `ls-tree` output can be quoted or split so a tracked `.../manifest.json` path disappears from the inventory. | Capture `git ls-tree -rz --name-only` as raw bytes, split on NUL, select manifest suffixes at byte level, and decode selected paths strictly. In the existing inventory-control seam, add a harmless newline path and a synthetic newline-bearing manifest that must fail exact census comparison. Never execute the synthetic manifest. |

### Primary-source interpretation

The official [Git `ls-tree` documentation](https://git-scm.com/docs/git-ls-tree.html) specifies that `-z` emits path names verbatim and NUL-terminated without pathname quoting. That makes the byte delimiter unambiguous because a Git pathname cannot contain NUL. The official [Git environment documentation](https://git-scm.com/docs/git) documents `GIT_DIR` and `GIT_WORK_TREE` as repository/worktree selectors; tests that create or mutate temporary repositories must therefore remove those variables from child environments and assert the selected repository before writes. Python's standard-library [AST reference](https://docs.python.org/3/library/ast.html) supports inspection of syntax nodes; a bounded evaluator should fold only known literal constructs and must never execute analyzed checker source. These sources justify the test contract; they do not establish fixture execution, fixture rights, or broader Git-path policy.

### Integration and validation order

Keep the current candidate's exact state-fork list at 153 and both diagnostic exclusions intact. Do not edit `tests/data/state-forks.json`, run fixture-bearing commands, replay Acid2 or `div_inc_timing_a`, execute excluded gbmicrotest ROMs, change production admission policy, add a dependency, or register another CTest. Run syntax, direct path/diagnostic/census controls and immutable identity checks first; then the existing `plan_cap`, evidence/path/trust CTests, and `planning_hygiene_controls` last. Preserve configured timeouts and control floors. Only after local convergence freeze a source candidate and spend the authorized independent review cycle; only a clean final review permits the one protected matrix. Record the actual matrix timings and dependency waits without changing required membership or protection.

### D-216 source findings

- [VERIFIED: `build/phase24/d215-review-e1d3200b.md`] — exact CR-01, CR-02, WR-02 and fixture-census findings at the immutable D-215 review head.
- [VERIFIED: `tests/scripts/verify-no-phase-paths.py`] — bounded evaluator/reader rules and current `git_run` exemption under review.
- [VERIFIED: `tests/scripts/verify-diagnostic-evidence.py`] — generic `run()` and `boundary_history_control` Git process/write paths.
- [VERIFIED: `tests/scripts/verify-state-forks.py`] — line-delimited `ls-tree` path enumeration and existing `--inventory-controls` seam.
- [VERIFIED: `tests/scripts/verify-planning-hygiene.py`] — existing narrow allowlisted Git environment adapter for local precedent.

**D-216 validity:** Revisit if the four reviewed defects are replaced by new evidence, the Python/Git version contract changes, the state-fork inventory changes, or existing CTest membership/branch protection changes. This addendum records the authorized scope; successful verification remains pending execution.

## D-217 Review Addendum — Replacement Refs, Runtime Bindings and Alternate Index

The independent exact-head review at candidate `5652e488f7940e00b2b00893cd5dbbea8d620fc8` (tree `301a7f3818d3d31ab97bbcac8e162b9e8cdc7fe3`) identified five remaining defects: the static adapter proof ignores runtime rebinding; validated full-commit identity can be invalidated through a reflective regex replacement, a later local rebinding, or truncated formatting; candidate Git reads can honor `refs/replace`; tracked-source inventory can inherit `GIT_INDEX_FILE`; and one inventory-only CLI mode can silently supersede a simultaneous materialization request. The report is [D-216 fix-pass review](../../../build/phase24/d216-review-fix1-5652e48.md). Independent audits validated these reproductions and classified the replacement-ref/alternate-index findings as a scope extension rather than silently folding them into the prior authorization.

### Primary-source behavior

The official [Git replacement-ref manual](https://git-scm.com/docs/git-replace) states that replacement refs affect Git commands by default and can be disabled with `--no-replace-objects` immediately after `git` or `GIT_NO_REPLACE_OBJECTS`. Therefore, a full object ID does not alone prove that object reads see the original object; the checker’s Git adapter and candidate-object readers require an explicit replacement-ref policy. The official [Git environment manual](https://git-scm.com/docs/git) states that `GIT_INDEX_FILE` chooses an alternate index instead of `$GIT_DIR/index`; therefore, inventory commands must scrub repository/index selectors before reading the tracked path list.

### Affected checker surfaces and controls

| Surface | Required property | Causal control |
|---|---|---|
| `verify-no-phase-paths.py` adapter analysis | Only the exact immutable adapter function remains callable; regex and revision names cannot be rebound or formatted/truncated after validation. | Inject later `git_run` binding, reflective `FULL_COMMIT` replacement, guarded `rev` rebinding, and f-string format-spec mutants; require semantic reason-specific refusals and retain full-SHA positive reads. |
| `verify-no-phase-paths.py` tracked inventory | An inherited alternate index or repository selector cannot suppress a tracked source file. | Use a synthetic repository with a live-path reader plus an alternate index omitting it; set `GIT_INDEX_FILE` and decoy repository selectors, then require the ordinary repository’s complete source inventory still rejects the reader. |
| `verify-planning-hygiene.py` immutable Git adapter | Its actual runtime command disables replacement refs so the static proof corresponds to runtime behavior. | Create a synthetic replace ref mapping a pinned commit to a same-type mutant; prove the approved adapter reads original bytes, then prove the negative control demonstrates Git's default replacement behavior. |
| `verify-dense-input.py` | Candidate tree, pin, and ancestry reads cannot follow replacement refs or repository redirection. | Add synthetic replacement-ref and hostile selector controls; prove selected candidate, exact pins/ancestry, and decoy repository state remain unchanged. |
| `verify-diagnostic-evidence.py` | Revision-bound archive, route, and blob reads use the original Git objects under a minimal Git environment. | Add a replacement-ref mutation to the existing disposable candidate/decoy controls; ensure original evidence is selected, replacement data is not, and the decoy remains unchanged. |
| `verify-state-forks.py` | Immutable inventory/blob reads use the intended repository and original commit; inventory-control arguments cannot silently shadow other modes. | Add replacement-ref and redirected-repository controls; add an incompatible `--inventory-controls --materialize-mutant-core --output` negative that fails before reporting success. |
| `verify-workflow-policy-coverage.py` | Revision-bound workflow/source reads remain tied to the original candidate objects under hostile inherited selectors/replacements. | Use the existing self-test or mutation seam to install a replacement for a source commit and require exact original bytes; hostile Git selectors must not redirect the inspected repository. |

### Scope and validation order

D-217 authorizes one exact integrated correction in those six existing checker files and additive closeout evidence. It uses the second and final scoped fix/re-review pass already allowed by D-216. The initial review and first correction/re-review pass remain spent; no review count, plan, matrix, or CI retry is added. Use existing standard-library and Git/CMake seams. Do not change the tracked fixture inventory, admission data/policy, CTest registration/identity, dependency tree, source payloads, release artifacts, or protected job coverage. The local loop is limited to D-217 code and directly affected checker controls; preserve the seven existing focused CTests and the established timeout/control floors.

Run syntax and cheap immutable/source-scope checks first, then direct causal self-tests for the changed checkers, then the already inventoried seven focused CTests in their existing order. Freeze only after all direct controls pass. The last exact-head review decides whether the existing single protected PR matrix may start; no further repair/re-review/matrix cycle follows a blocker. If clean, run that one complete protected matrix and merge only its identical passing head through protection. CI efficiency remains measurement-only: record current job/step/queue/wait/headroom data without changing jobs, timeout, cache, or concurrency.

### D-217 source findings

- [VERIFIED: `build/phase24/d216-review-fix1-5652e48.md`] — candidate-bound four critical findings and one warning, including exact reproductions and proposed minimal remedies.
- [VERIFIED: `https://git-scm.com/docs/git-replace`] — replacement refs affect commands by default; the global `--no-replace-objects` option and `GIT_NO_REPLACE_OBJECTS` disable them.
- [VERIFIED: `https://git-scm.com/docs/git`] — `GIT_INDEX_FILE` selects an alternate index.
- [VERIFIED: read-only Git environment audit] — replacement reads affect the six checker surfaces recorded above; index-query redirection is a separate issue from replacement-ref resolution.
- [VERIFIED: read-only Git adapter audit] — runtime `git_run` rebinding, reflective regex mutation, revision rebinding, and formatted truncation invalidate the current static proof.
- [VERIFIED: read-only inventory-mode audit] — alternate-index scan suppression and incompatible inventory/materialization mode arguments are reproducible.

**D-217 validity:** Revisit only if the exact affected checker surface, immutable-Git contract, or existing focused CTest mapping changes. The scope does not imply successful correction; all new controls must pass at the frozen candidate before final review.

## D-218 Research Addendum — Python binding and runtime mutation semantics

The D-217 final review (`build/phase24/d217-final-review-4239a8b.md`) identifies three concrete weaknesses in the fixed Python checker proof surface: calling namespace-dictionary mutation methods can replace `git_run`; match-pattern captures can assign the validated revision after its guard; and reflective mutation can replace `re.compile` before `FULL_COMMIT` is constructed.

The official Python documentation confirms the relevant runtime semantics. [`globals()`](https://docs.python.org/3/library/functions.html#globals) exposes the current module namespace dictionary; [`setattr`](https://docs.python.org/3/library/functions.html#setattr) mutates the named object attribute; the [match statement reference](https://docs.python.org/3/reference/compound_stmts.html#match) defines pattern captures as bindings; and the [AST reference](https://docs.python.org/3.14/library/ast.html) represents `MatchAs`, `MatchStar`, and `MatchMapping.rest` captures in pattern-node fields rather than `ast.Name` store nodes.

The best fit is a small closed AST contract for the named checker functions, not a new general-purpose data-flow engine. Reject reflection and aliases that can mutate the protected namespace or regex module; explicitly enumerate all relevant pattern-binding fields; validate full commit IDs again at the Git-facing archive reader; and prove the validated argument or exact D-209 pin is not rebound before every Git read. This combination gives runtime defense at the reader and static provenance across the known helper chain without a new dependency or speculative analyzer abstraction.

Add reason-specific static negative controls for direct and builtin dictionary namespace mutation, reflective `re.compile`/module-dictionary mutation, each relevant match capture form, and an archive-helper revision reassignment. Retain positive controls for the exact approved adapter, standard-library validator, full validated revision, and D-209 pin. Mutated source must be parsed and checked without executing the injected operations.

For qualification, preserve the seven existing focused CTests and their established order, deadlines, and floors; run the cheap syntax/boundary/control checks first. A clean independent exact-head review is the only entry to the already authorized single protected PR matrix. Measure hosted efficiency from that run without reducing required coverage or making unmeasured workflow changes.

## D-219 Research Addendum — Integrated Runtime and Git Trust Boundary

D-218's focused local CTests passed, but its frozen exact-head review returned NO-GO for two critical Python proof gaps. No D-218 protected matrix ran. The review receipt remains historical evidence; D-219 is the current recovery authority and does not turn the D-218 candidate into an accepted candidate. [VERIFIED: 24-CONTEXT.md:3-4; .planning/STATE.md:24-27]

### Findings that matter to the plan

| Surface | Current evidence | Planning consequence |
|---|---|---|
| `verify-no-phase-paths.py` | The checker already uses AST/runtime literal reasoning and has `_reflectively_writes_binding`; its approved Git adapter uses `--no-replace-objects`. The same fixed source proof is the narrow seam for `git_run`, the regex/validator, and protected globals. [VERIFIED: tests/scripts/verify-no-phase-paths.py:158-160,398-421,501-560,650-663] | Keep a closed source contract: prove the accepted runtime binding, reject demonstrated alias/reflection forms, and make reason-specific static controls. Do not execute injected source or expand this into general Python taint analysis. |
| `verify-planning-hygiene.py` | `git_run` already filters the child environment and adds `--no-replace-objects`; `immutable_blob` has a full-commit guard; `validate_v04_archive_and_recovery` reads both current archive blobs and the pinned D-209 pair. The D-209 revision is a module-level exact pin. [VERIFIED: tests/scripts/verify-planning-hygiene.py:221-268,271-281,400-413] | Add a reader-level full-SHA guard and static provenance checks that prevent revision or pin rebinding through each reader/caller edge. Preserve the precise D-209 pin, accepted immutable reads, and the valid exact archive path. |
| `verify-dense-input.py` | `git_bytes` uses a standard-library subprocess with `--no-replace-objects` and `_git_environment`; several direct fixture-comparison reads intentionally use ordinary Git to demonstrate default behavior. [VERIFIED: tests/scripts/verify-dense-input.py:39-57,154-172,329-335] | Audit the production candidate readers and only those synthetic reads that are expected to represent the trusted adapter. Retain the ordinary-Git comparison as a negative demonstration; do not mechanically add flags to every Git command in fixture setup. |
| `verify-diagnostic-evidence.py` | Its `git_environment` allowlist is used by the `git` helper and archive command. It also uses direct subprocesses for synthetic Git comparisons. [VERIFIED: tests/scripts/verify-diagnostic-evidence.py:158-183,245-248,951-953,1308-1312] | Keep generic non-Git `run()` behavior; constrain Git-bound reads with the existing Git-specific helper, and test hostile repository selectors against a decoy. Distinguish trusted candidate reads from fixture setup/comparison. |
| `verify-state-forks.py` | Its `git_environment` / `git_read` helper already uses `--no-replace-objects`; the CLI exposes inventory, matrix, report, output, and mode-specific options. It checks conflicts before the inventory's Git calls, and has an existing mixed-mode negative. [VERIFIED: tests/scripts/verify-state-forks.py:68-86,1467-1527,854-862] | Exercise every mode and input class through the production CLI, including no Git/output side effect for a conflict, not just the existing materialization conflict. Keep valid inventory and materialization-only positives and the real manifest set unchanged. |
| `verify-workflow-policy-coverage.py` | `git_environment` and `git_read` already provide an isolated no-replace reader, while source/fixture controls also spawn synthetic Git subprocesses. [VERIFIED: tests/scripts/verify-workflow-policy-coverage.py:176-187,258-270] | Audit immutable candidate reads and add a replacement/reflection control using existing seams; preserve test-fixture Git commands whose expected role is to set up disposable histories. |

**Key Git footgun:** A full commit ID does not by itself guarantee original-object reads because replacement refs are active by default; Git supports `--no-replace-objects` after `git`. Separate environment risk also remains: `GIT_DIR`, `GIT_WORK_TREE`, `GIT_COMMON_DIR`, `GIT_INDEX_FILE`, `GIT_OBJECT_DIRECTORY`, and `GIT_ALTERNATE_OBJECT_DIRECTORIES` can change the repository/index/object context. Use an explicit option and a narrow environment allowlist on trusted readers, then prove behavior with both replacement refs and a hostile decoy/index/object store. This is an inference from Git's documented mechanisms and the reviewed project seams, not a claim that every `GIT_*` variable has the same effect. [CITED: [Git replacement refs](https://git-scm.com/docs/git-replace); [Git environment variables](https://git-scm.com/docs/git)]

**Key Python footgun:** `function.__globals__` is the dictionary of the function's defining module. Import aliases, namespace dictionary mutations, and structural pattern captures can change runtime bindings without the `ast.Name(Store)` shape a naïve scanner expects. The AST documentation represents `MatchAs`, `MatchStar`, and `MatchMapping.rest` captures in node fields; therefore those fields must be enumerated explicitly in the finite revision-binding proof. [CITED: [Python function globals](https://docs.python.org/3/reference/datamodel.html#function.__globals__); [Python AST](https://docs.python.org/3/library/ast.html); [Python match statement](https://docs.python.org/3/reference/compound_stmts.html#match)]

**CLI footgun:** The state-fork CLI currently checks `--inventory-controls` conflicts in `main` against all operation flags and a tuple of mode-specific inputs, but the check must be proven complete for the current parser surface. `argparse.add_mutually_exclusive_group()` can enforce mutually exclusive flags, but that alone cannot reject every optional input supplied alongside inventory mode. Use an explicit pre-dispatch validator (or equivalent) that also covers mode-specific inputs, then exercise the production CLI with per-class negatives and output sentinels. Check before Git access/output creation; where possible, perform this validation before path resolution as well. [VERIFIED: tests/scripts/verify-state-forks.py:1467-1527; CITED: [Python argparse mutual exclusion](https://docs.python.org/3/library/argparse.html#mutual-exclusion)]

### Recommended plan sequence and stopping logic

1. **One scoped source-correction task:** cover the six named checker files. First establish the runtime binding/revision proof and its causal mutants. Audit the existing Git readers and apply `--no-replace-objects` plus minimal environments where they select immutable source/candidate objects. Add decoy, replacement-ref, alternate-index/object-store and namespace negatives while retaining exact-original-object positives. Make inventory mode exclusive across the complete parser surface before Git/output side effects. Use only standard-library and current self-test seams; do not add dependencies, general wrappers/analyzers, fixture bytes, CTest identities, or production admission behavior.
2. **One qualification/evidence task:** run cheap syntax, candidate/route/archive identity, source-scope, ancestry and changed-contract controls first. Then inspect CTest `--show-only=json-v1`, and run only the existing set in the validated order: `plan_cap`, `phase22_evidence_controls`, `phase22_evidence_contract`, `no_phase_paths_controls`, `no_phase_paths`, `workflow_policy_coverage_controls`, `planning_hygiene_controls`. Preserve original deadlines and floors, including the 30-second planning-hygiene timeout and 125-control floor; add factual D-219 evidence to `24-CLOSEOUT.md` without erasing earlier failed results. The root roadmap has no Phase 24 requirements, so no new requirements trace is needed.
3. **Freeze, review, remote gate:** after local convergence, freeze full candidate SHA/tree and obtain an independent review. D-219 permits two correction/review passes total after D-218 NO-GO: the first corrected exact-head review is pass one, followed by at most one in-scope correction and fresh review as pass two. Stop on an out-of-scope or unresolved correctness/security issue after pass two. Only a clean final review permits the one full protected matrix. Any failed, skipped, stale or missing required context stops without a matrix retry. Merge only the same reviewed/passing head under existing protection. GitHub documents branch-protection status checks as merge conditions; preserve the required contexts and read them from current protection/run evidence rather than assuming a static list. [CITED: [GitHub protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)]

### Adversarial and maintainability review

- **Security:** Exact object identity must survive both runtime-binding mutation and Git's replace/selector mechanisms. Test the real adapters and CLI; helper-only coverage is insufficient.
- **Python/static analysis:** Fail closed only on the fixed, documented proof surface. Retain source-only mutation checking and direct positive controls; reject alias forms if their provenance is not fully modeled. Avoid a general analyzer and avoid broad exceptions for self-tests; pass fixture inputs explicitly where practical.
- **Git/repository integrity:** The `--no-replace-objects` option does not clear repository redirection variables. Keep object-selection policy and environment isolation as separate, tested invariants. Synthetic tests must prove intended bytes and untouched decoys.
- **QA/operations:** Keep cheap consistency and changed-contract controls ahead of the seven registered tests. Preserve timeouts/floors; diagnose local failures before review. Hosted qualification stays behind clean review.
- **Maintainability:** Reuse existing Git environment builders and CTest self-test entry points. Do not duplicate broad wrapper abstractions or add dependencies; do not change unrelated fixture/admission behavior.
- **CI efficiency:** D-218 yielded no hosted timings. Measure the one D-219 matrix if it occurs; recommend a workflow change only when current timings establish a safe improvement. Keep the D-211 package-waiter redesign separate.

### D-219 primary sources

- [Python AST](https://docs.python.org/3/library/ast.html) documents AST structure and capture fields used for finite static proof.
- [Python data model](https://docs.python.org/3/reference/datamodel.html#function.__globals__) documents function/module namespace relationships.
- [Python argparse](https://docs.python.org/3/library/argparse.html#mutual-exclusion) documents option mutual exclusion; project-specific mode/input validation remains necessary.
- [Git replacement refs](https://git-scm.com/docs/git-replace) documents default replacement behavior and `--no-replace-objects`.
- [Git environment](https://git-scm.com/docs/git) documents selectors for repository, worktree, index, and object storage.
- [Git `ls-tree`](https://git-scm.com/docs/git-ls-tree) documents `-z` NUL-delimited path output, preserving newline-bearing names.
- [GitHub protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches) describes required check gates and strict/loose head requirements.

**D-219 research execution boundary (historical):** The D-219 plan and its two-pass recovery authority are superseded by D-220. Its local qualification and review artifacts remain candidate-specific history.

## D-220 Research Addendum — Aliased reflection and guarded revision proof

### Current evidence and what it establishes

The frozen D-219 candidate remains a failed-review artifact. The exact review records the candidate and NO-GO state:

DATA_B7M4Q9C2_START
**Candidate:** `28ab38f2346a12ef68a07e8a2d403dbfd81b8ba5` (tree `7b872747c42fb214be72e793d2e1eaec542d3b4a`)
**Status:** issues_found — **NO-GO**
DATA_B7M4Q9C2_END

[VERIFIED: build/phase24/d219-final-review-28ab38f2346a12ef68a07e8a2d403dbfd81b8ba5.md:29-37]

The review's two Critical findings reduce to a single proof failure: checking direct spellings does not establish that the runtime binding remains unchanged when the source can alias dynamic lookup and synthesize its attribute name. The global path can replace `git_run` or `V04_D209_ARCHIVE_REV`; the local path can replace a revision after its full-commit guard. The qualification receipt records all seven existing focused CTests passing at this exact candidate and configured Python 3.14.4. Those test results remain valid only for that candidate and do not resolve the source-proof defects. There was no push or protected matrix. [VERIFIED: build/phase24/d219-final-review-28ab38f2346a12ef68a07e8a2d403dbfd81b8ba5.md:35-54; build/phase24/d219-final-qualification-28ab38f2346a12ef68a07e8a2d403dbfd81b8ba5.md:7,22-38]

### Python semantics and version scope

The Python 3.14.10 built-in documentation says `getattr` accepts a string naming an object's attribute and that the string need not be a Python identifier. `globals()` returns the module namespace dictionary. The data model documents `frame.f_globals` as the global lookup dictionary and says optimized-scope `frame.f_locals` may be a write-through proxy, changed in Python 3.13. PEP 667 is final for Python 3.13 and specifies read/write access through `frame.f_locals` in optimized scopes. Therefore, do not rely on the pre-3.13 behavior where a local-frame mapping write might not affect the live local. These are primary-source language/API semantics; they do not constitute a project compatibility declaration. [CITED: https://docs.python.org/3.14/builtins/functions.html#getattr; https://docs.python.org/3.14/reference/datamodel.html#frame-objects; https://peps.python.org/pep-0667/]

Python's AST is sufficient for the bounded proof. The 3.14 AST reference represents calls as a callee plus positional/keyword arguments, names with load/store/delete context, attributes with a source-level attribute string, and concatenation as a `BinOp`. Parsing these expressions produces a tree without executing the source. The grammar may change between Python releases, so execute checks with the configured project interpreter and preserve feature guards where the existing checker supports older AST shapes. [CITED: https://docs.python.org/3.14/library/ast.html]

The Phase 24 qualification receipt records the configured interpreter as:

DATA_J6R2V8N5_START
configured Python: 3.14.4
DATA_J6R2V8N5_END

[VERIFIED: build/phase24/d219-final-qualification-28ab38f2346a12ef68a07e8a2d403dbfd81b8ba5.md:7]

The build-testing block in `CMakeLists.txt` requests an interpreter with this exact call:

DATA_H3P9W1K6_START
find_package(Python3 COMPONENTS Interpreter REQUIRED)
DATA_H3P9W1K6_END

[VERIFIED: CMakeLists.txt:38-40]

This call supplies no numeric minimum [VERIFIED: CMakeLists.txt:38-40]. That is a fact about this call, not proof that every Python version is supported. The formal project support range is unresolved; keep the configured interpreter as the qualification target and do not promote Python 3.14.4 into a minimum, maximum, or tested-version matrix. [ASSUMED: a broader supported-version range has not been positively established in the project evidence reviewed for this phase]

### Recommended narrow proof contract

The current checker has a finite reflection policy, but the policy recognizes direct AST spellings. Its exact protected names and direct-call condition are:

DATA_L3P8Z0H5_START
forbidden_namespace_names = {
        "_getframe", "f_globals", "f_locals", "f_builtins", "__dict__",
        "__builtins__", "builtins", "__import__",
    }
DATA_L3P8Z0H5_END

[VERIFIED: tests/scripts/verify-no-phase-paths.py:1045-1064]

The current direct-call check includes this exact condition and refusal:

DATA_D4N8S6V1_START
and node.func.id in {"getattr", "vars"}:
raise LintError("REJECT planning-path-git-command: dynamic namespace lookup makes revision proof unprovable")
DATA_D4N8S6V1_END

[VERIFIED: tests/scripts/verify-no-phase-paths.py:1062-1064]

The revision check also detects ordinary AST binding nodes, while the review bypass writes through a mapping rather than a `Name(Store)` node. The source predicate is:

DATA_C5T1M8R4_START
if isinstance(node, ast.Name) and node.id == binding and isinstance(node.ctx, (ast.Store, ast.Del)):
DATA_C5T1M8R4_END

[VERIFIED: tests/scripts/verify-no-phase-paths.py:1009-1011]

Use a small capability-aware AST rule around the existing proof-bearing surface:

1. Resolve only simple name aliases and explicit import aliases whose source is the dynamic lookup/frame capability being checked. Keep the alias set local to the relevant lexical scope; a reassignment, branch merge, unknown expression, or alias escape that cannot be resolved becomes *unprovable* and is rejected. Do not build a general Python points-to or call-graph engine.
2. For a resolved dynamic getter, accept no unknown attribute-name expression. Either reject dynamic lookup in the proof-bearing code outright or recognize only bounded string constants and `+` concatenations. Detect the constructed `_getframe`, `f_globals`, and `f_locals` names, and reject the resulting frame/global/local namespace access before it can be used to alter protected bindings. This directly catches `lookup = getattr` plus split strings without depending on the spelling of the final attribute at the call site.
3. Keep the guard-to-reader proof closed: any unsupported call or alias that can change `rev`/`revision`, the approved Git adapter, the full-commit validator, or the D-209 pin before the immutable read yields the existing proof-specific refusal. Unknown values fail closed; they are not treated as safe because no exact forbidden string was found.
4. Keep the allowed runtime path explicit. The current checker names the full-commit-guarded readers and pins where revision rebinding is checked:

   DATA_R2F7N4Q8_START
   guarded = ("read_rev", "commit_snapshot")
   DATA_R2F7N4Q8_END

   [VERIFIED: tests/scripts/verify-no-phase-paths.py:1070-1074]

   DATA_N9K4W2F6_START
   ("immutable_blob", '    listed = git_run(repo, "ls-tree", revision, "--", path)\n', "revision"),
   DATA_N9K4W2F6_END

   [VERIFIED: tests/scripts/verify-no-phase-paths.py:2858-2868]

Adversarially, the current spelling denylist is inadequate: string splitting and a renamed getter evade it, so a new spelling list would keep growing and would still make completeness depend on enumerating equivalent syntax. A bespoke general alias/dataflow analyzer is also a poor fit: it would need to model Python scopes, control flow, mutation, call effects, imports, and evolving syntax across much more code than the demonstrated trust boundary. The bounded capability/alias rule is the narrow middle: it handles the observed alias and split-string forms, stops on unsupported flow, uses only `ast`, and leaves all other source outside this invariant untouched. Keep the scope local to the existing six checkers and additive Phase 24 closeout evidence.

### Causal source-only controls and accepted positives

In the existing self-test seam, construct source-text mutants for both D-220 classes: (a) alias `getattr`, assemble `_getframe` and `f_globals` from string fragments, then attempt to replace the approved Git adapter and the D-209 pin; (b) use the same aliased/split-name route to obtain `f_locals`, then attempt to replace the guarded revision after validation. Add the local-mutation variants in all three existing reader functions identified above. The D-219 review report contains the exact reproductions; the updated controls should keep them as source strings and parse/analyze them, never execute the injected operations. [VERIFIED: build/phase24/d219-final-review-28ab38f2346a12ef68a07e8a2d403dbfd81b8ba5.md:46-83]

Each mutant must reach the production proof predicate and fail for the proof-specific reason before a protected candidate Git read. Use a Git-reader sentinel/count in the existing test seam so the mutant's expected refusal is observed with zero protected reads; a helper-only assertion or an exception after the attempted read is not causal evidence. Retain positive controls for the current approved adapter, full-commit guard, valid immutable revision flow, exact D-209 pin and archive path. Keep the original Git-object, environment, inventory-mode, path and census positives/negatives already mapped to the seven existing CTests.

The qualification receipt records the unchanged seven CTest names, serial order, existing deadlines and 61.30-second local total at the rejected candidate. D-220 requires preserving those identities, deadlines and control floors; the historical pass is not a pass for a corrected candidate. The plan should run cheap syntax/source-scope/identity controls first, then the same seven CTests serially, with no new test identity and no broad suite, fixture/ROM replay, build, or CI in this research stage. [VERIFIED: build/phase24/d219-final-qualification-28ab38f2346a12ef68a07e8a2d403dbfd81b8ba5.md:22-38; .planning/phases/GB-24-resolve-remaining-v0-4-evidence-and-verification-gaps/24-CONTEXT.md:442-448]

### Planning sequence and stopping rule

The current 24-01 plan still carries D-219's three-task sequence and two-pass review cap. Mark that sequence historical and amend only the one existing plan to cover this proof gap within the existing source boundary. D-220 replaces the numeric review-pass count with scope-bounded convergence: every finding must produce a changed candidate and causal control; stop for owner discussion if a cycle makes no concrete progress or needs a new boundary, source file, dependency, CTest identity, broader claim, or weaker requirement. After local convergence, obtain a fresh exact-head independent review. Only a clean review opens the one protected PR matrix; any failed, skipped, stale, or missing required context stops with no matrix retry. Merge only the identical reviewed and fully passing head through branch protection. This is planning-only; implementation and CI require the separate authorized execution handoff. [VERIFIED: .planning/phases/GB-24-resolve-remaining-v0-4-evidence-and-verification-gaps/24-01-PLAN.md:18-20,38-41; .planning/phases/GB-24-resolve-remaining-v0-4-evidence-and-verification-gaps/24-CONTEXT.md:436-448]

Preserve the archived D-209 dispositions, FIXT-01 Pending, failed unreplayed Acid2 comparison, diagnostic exclusions, D-103, Task 7, published v0.4.0 artifacts, administrative closeout and separate phase/milestone closure. Do not start phase verification, milestone archival, v0.5 work, branch switching or worktree cleanup from this plan. The current route after research is `$gsd-plan-phase 24`. [VERIFIED: .planning/phases/GB-24-resolve-remaining-v0-4-evidence-and-verification-gaps/24-CONTEXT.md:446-448]

### D-220 sources and research boundary

- [CITED: https://docs.python.org/3.14/builtins/functions.html#getattr] — `getattr` accepts a string-named attribute even when the name is not an identifier; `globals()` exposes the module namespace dictionary.
- [CITED: https://docs.python.org/3.14/reference/datamodel.html#frame-objects] — `frame.f_globals` exposes global lookup; optimized-scope `frame.f_locals` may be a write-through proxy beginning in Python 3.13.
- [CITED: https://peps.python.org/pep-0667/] — Final PEP 667, Python-Version 3.13, specifies consistent frame-local views and write-through updates in optimized scopes.
- [CITED: https://docs.python.org/3.14/library/ast.html] — AST call, name context, attribute, and binary-operation structure; AST parsing supports source inspection without executing the payload.
- [VERIFIED: build/phase24/d219-final-review-28ab38f2346a12ef68a07e8a2d403dbfd81b8ba5.md:29-83] — Candidate-bound D-219 pass-two NO-GO and exact aliased-reflection bypasses.
- [VERIFIED: build/phase24/d219-final-qualification-28ab38f2346a12ef68a07e8a2d403dbfd81b8ba5.md:7-38] — Configured Python observation, exact candidate qualification, and the seven focused local CTest results.
- [VERIFIED: tests/scripts/verify-no-phase-paths.py:1000-1098,2858-2868] — Current source-only binding and immutable-revision proof predicates and reader-specific controls.
- [VERIFIED: CMakeLists.txt:38-40] — The testing build's Python interpreter requirement.

**Research execution boundary:** This refresh only updates planning evidence. No source, plan, context, or state file was changed; no test or build was run; no review, push, protected matrix, or merge was started. The updated sole plan must pass independent plan checking before any separate execution authorization.

## D-221 refresh — f19 hosted failure integration

### Observed evidence and limits

The D-220 candidate `f19d5ae2f5819d18074a68e1e80d959dc31b1302` passed fresh code and security reviews, then its one protected matrix failed: `required-native` and `preview-package-smoke` failed, while `fixture-repro` passed. The report records `no_phase_paths_controls` timing out in three lanes, Windows-only D-209 Git-fixture and newline-path control failures, and three preview consumers waiting about 69–73 minutes before package work was skipped. One local run of the 201-control path self-test took 39.61 seconds against its existing 60-second timeout. These are observations from the [candidate-bound hosted report](../../../build/phase24/f19d5ae2f5819d18074a68e1e80d959dc31b1302-hosted-matrix.md); they do not prove hosted timeout root cause or establish that every preview delay is avoidable.

### Implementation seams and recommendations

- **Path-control runtime:** `verify-no-phase-paths.py` parses the source in `validate_planning_hygiene_source`, then `_source_path_sites` parses it again before walking the tree (`tests/scripts/verify-no-phase-paths.py:276-310,2974-3003`). First measure the repeated work inside the same control; if duplicate parsing is material, pass the already parsed tree and its source identity through the existing path-site collector. Preserve decoded source/tree pairing, all 201 controls and their reasons, and the 60-second CTest deadline (`tests/CMakeLists.txt:3004-3011`). Do not optimize away a causal mutant or change its refusal just to reduce time. Further algorithm changes need measured evidence.
- **D-209 Windows Git fixture:** `verify-planning-hygiene.py` currently writes the source repository's object-directory path to the disposable fixture's `objects/info/alternates` and updates a ref to the pinned revision (`tests/scripts/verify-planning-hygiene.py:2685-2710`). Give the fixture its own required object database and verify the exact full object ID and `commit` type before using it. Avoid dependence on alternates: Git documents that alternate object stores can disappear with their source ([`git clone`](https://git-scm.com/docs/git-clone)). A full object ID is a valid fetch source ([`git fetch`](https://git-scm.com/docs/git-fetch)); local object transfer is also an option if it preserves a self-contained fixture and exact type check. The hosted failure is platform evidence, not proof that alternates alone caused it.
- **Newline Git paths:** `verify-state-forks.py` currently materializes `fixtures/odd\n...` paths in the synthetic repository's worktree before committing them (`tests/scripts/verify-state-forks.py:1097-1127`). Windows prohibits control characters 0x01–0x1f in filename components ([Microsoft file-name rules](https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-fscc/2917da5c-253c-4c0e-aaf6-9dddc37d2e6e)). Represent the newline-bearing path directly in Git index/tree metadata using `git update-index -z --index-info`; Git specifies NUL-delimited path input for this mode ([`git update-index`](https://git-scm.com/docs/git-update-index)). Keep the current exact refusal and verify the committed path bytes, including a benign newline-bearing non-manifest positive.
- **Exact-head preview waiters:** The existing `.github/scripts/wait-exact-head-ci.py` already selects the newest exact-SHA run and debounces terminal run conclusions across two polls; the same helper currently treats truncated run/job listings as immediate `FAIL`, despite its module contract saying uncertainty waits to the deadline (`.github/scripts/wait-exact-head-ci.py:1-10,76-138,234-360`). The matrix indicates the expensive case: a required upstream dependency can fail while the aggregate run is not yet terminal, leaving consumers waiting. Add an explicit opt-in early-failure mode and enable it at the existing three preview wait sites in `.github/workflows/preview.yml`. Early failure must bind to the newest exact-head PR run, its current attempt, and the same terminal failure of a `required-native` dependency on two consecutive polls. Reset the streak when attempt/run changes or data becomes inconclusive. Truncated/malformed/duplicate/missing data and transport errors must wait and ultimately fail at the existing deadline; they cannot grant an early pass. A child success can never pass the gate: package production still requires successful exact-head run and `required-native`, and the player lane must keep its exact player-job attempt, artifact and receipt checks. Preserve the three protected contexts and existing matrix membership. Official GitHub docs distinguish job status from downstream `needs` behavior and warn that skipped jobs can report success ([status checks](https://docs.github.com/en/pull-requests/reference/status-checks), [workflow syntax](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax)); retain the explicit aggregate and artifact gates.
- **CI iteration cost:** Run syntax, input/identity checks and the affected controls before any longer focused CTests, then run existing focused identities serially with current deadlines/floors. The observed ~213 runner-minutes across four native/floor streams and the 69–73 minute preview waits justify testing this targeted fail-fast path, but do not justify changing matrix membership, triggers, concurrency, caches or timeout budgets. At each newly authorized matrix, record actual queue, job/step, upstream dependency wait, package-step execution/skip and timeout headroom under `.planning/context/WORKFLOW.md#cicd-efficiency`. Compare measurements before suggesting any further optimization.

### Correct implementation boundary for planning

The current D-220 source list is not sufficient for D-221. The exact in-scope production/test files are `tests/scripts/verify-no-phase-paths.py`, `tests/scripts/verify-planning-hygiene.py`, `tests/scripts/verify-state-forks.py`, `.github/scripts/wait-exact-head-ci.py`, `.github/scripts/verify-workflow-policy.py`, `.github/workflows/preview.yml`, and `tests/scripts/verify-workflow-policy-coverage.py`, plus additive evidence in the existing `24-CLOSEOUT.md`. The helper and workflow-policy checker live under `.github/scripts/`, not `tests/scripts/`; preview call sites live in `.github/workflows/preview.yml`. Read these exact paths from the current checkout before planning.

Reuse existing control seams and CTest identities only. The current registered identities include `no_phase_paths_controls`, `planning_hygiene_controls`, `state_fork_census_controls`, and `wait_exact_head_ci_controls`; verify exact CMake registration and any existing CI self-test before assigning tasks. Add no dependency, CTest identity, file, or claim outside D-221. The active context is authoritative for the two-candidate budget: candidate one requires changed source, local qualification and clean fresh code/security reviews; candidate two is allowed only after a concrete in-scope first-matrix failure, causal fix, focused qualification and clean fresh reviews. No unchanged-head matrix retry. This planning refresh confers no source-execution or hosted-CI authority.
