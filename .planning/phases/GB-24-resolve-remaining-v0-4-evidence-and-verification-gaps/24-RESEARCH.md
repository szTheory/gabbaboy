# Phase 24: Resolve remaining v0.4 evidence and verification gaps — Research

**Researched:** 2026-11-18
**Domain:** Python standard-library static analysis, immutable Git evidence, planning-contract checkers, and protected CI qualification
**Confidence:** HIGH for current in-repository contracts; MEDIUM for implementation patterns grounded in official Python and Git documentation

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

D-215 is a planning-only rescope of Phase 24 after the exact candidate review found four blockers and two warnings. The planner should revise the existing Plan 24-01 into one integrated correction for CR-01 through CR-04 and WR-01/WR-02, plus the still-in-scope stale path-count and immutable-route work already recorded in the same plan. Do not add a phase, plan, dependency, or CTest identity. D-215's latest authorization is the planning boundary; a separate owner authorization is required before executing the replanned scope. [VERIFIED: .planning/phases/GB-24-resolve-remaining-v0-4-evidence-and-verification-gaps/24-CONTEXT.md:57-70]

**Primary recommendation:** Keep the generic tracked-file lexical scan. Replace only the planning-hygiene file's count-based allowance with a narrow fail-closed AST contract that checks decoded string values, safe constant construction, direct local helper argument-to-parameter flow, and actual containment beneath the verified disposable root. Make current-versus-historical validation an explicit full-revision decision. Parse admission pins from raw bytes and run temporary Git operations under a sanitized environment, then assert the selected repository and candidate HEAD. Use the existing positive/negative self-test seams and focused CTests, with cheap identity and syntax checks first. This follows the approved D-215 implementation recommendations and the Python/Git APIs already in the toolchain. [VERIFIED: .planning/phases/GB-24-resolve-remaining-v0-4-evidence-and-verification-gaps/24-CONTEXT.md:65-70]

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

The current 24-01-PLAN.md, 24-VALIDATION.md, 24-PATTERNS.md, STATE.md, and root roadmap still describe D-214's earlier route. They must be reconciled to D-215 by the planning workflow before execution; this research updates only 24-RESEARCH.md. The phase roadmap has **Requirements: []**, so this phase has no new requirement IDs to map. [VERIFIED: .planning/ROADMAP.md:16-32; .planning/phases/GB-24-resolve-remaining-v0-4-evidence-and-verification-gaps/24-VALIDATION.md:12-33]

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

This is a planning architecture only. D-215 does not authorize execution; a separate owner authorization is required. No task before the freeze may start the hosted matrix, and any failed/skipped/stale/missing required context stops the qualification path. [VERIFIED: .planning/phases/GB-24-resolve-remaining-v0-4-evidence-and-verification-gaps/24-CONTEXT.md:59-63]

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
| A1 | Removed: runtime symlink creation/resolution is outside the selected CR-03 finite static-analysis seam. [RESOLVED] | Pattern 1, validation | No symlink portability or platform-permission assumption is needed; an actual symlink-based read escape revealed during execution stops as a new out-of-scope issue. |
| A2 | The configured CMake Python interpreter may differ from shell python3 3.14.4. [ASSUMED] | Standard Stack, Environment | A source check can pass under a different interpreter than CTest uses; inspect CMakeCache after configure as directed by workflow policy. |

## Open Questions

1. **RESOLVED — Review-fix pass accounting:** After local convergence, run one initial fresh exact-head independent review. If it identifies scoped findings/direct corrections, permit up to two post-correction fix-and-re-review passes, each with affected local checks and a fresh review of that corrected candidate. Local diagnosis/retesting is uncapped within scope. Stop on an unavailable review, new out-of-scope trust/correctness issue or anything unresolved after those two passes. Run one protected matrix only after a clean final review; no matrix retry is authorized.
2. **RESOLVED — CR-03 containment scope and symlink portability:** The approved seam proves lexical component containment in the source AST by rejecting absolute, parent, unproven dynamic and root-rebinding escapes. Runtime filesystem symlink resolution is outside these six findings and this finite seam. Claim no symlink containment, add no symlink test/platform dependency, and stop if execution reveals an actual symlink-based read escape as a new out-of-scope trust/correctness issue. Archive-blob symlink refusal remains part of the distinct current/archive contract.

No additional requirement-status, rights, release, suite, or milestone decision is needed for planning; the exact scope and limits are in the D-215 context. [VERIFIED: .planning/phases/GB-24-resolve-remaining-v0-4-evidence-and-verification-gaps/24-CONTEXT.md:57-70]

## Environment Availability

| Dependency | Required by | Available in this research environment | Version/observed state | Fallback |
|---|---|---:|---|---|
| Python 3 | Syntax, AST, and checker controls | Yes | 3.14.4 | Use the CMake-configured interpreter during later CTest validation. |
| Git | Immutable snapshots and temporary repo controls | Yes | 2.41.0 | None for Git-backed contracts. |
| CMake / CTest | Existing focused validation | Yes | 4.4.3 | None for registered project targets. |
| GitHub protected PR checks | Final exact-head matrix | Not probed; no CI was started | D-215 requires one complete protected matrix after a clean exact-head review | No local result substitutes for protected checks. |

Versions are read-only environment probes; no configure, build, CTest, source execution, GitHub query, review, push, or CI run occurred during this research.

## Validation Architecture

> Planning guidance for regenerating 24-VALIDATION.md. D-215 authorizes planning only; this section does not authorize implementation, tests, CI, review, push, or merge.

### Test Framework

| Property | Value |
|---|---|
| Framework | Existing Python standard library and CMake/CTest |
| Config file | Existing CMake preset and CTest registrations |
| Quick run command | The current validation document's syntax-only command over the six affected Python checkers: python3 -I -c 'import ast,pathlib; paths=("tests/scripts/verify-dense-input.py","tests/scripts/verify-diagnostic-evidence.py","tests/scripts/verify-planning-hygiene.py","tests/scripts/verify-state-forks.py","tests/scripts/verify-no-phase-paths.py","tests/scripts/verify-workflow-policy-coverage.py"); [ast.parse(pathlib.Path(p).read_text(encoding="utf-8"), filename=p) for p in paths]'. This is only a proposed post-authorization cheap gate, not run here. [VERIFIED: .planning/phases/GB-24-resolve-remaining-v0-4-evidence-and-verification-gaps/24-VALIDATION.md:16-23] |
| Focused run command | Inspect exact registered commands using CTest's --show-only=json-v1; run only existing targets mapped below, after source revision, route/archive, candidate ancestry, and non-ROM identity checks pass. |
| Full suite | Excluded from this scope; D-103 remains separate. |
| Phase verification | Separate boundary after recovery gates; not authorized by D-215. |

The phase has no requirement IDs: root roadmap says “**Requirements:** []”. There is no phase requirement-to-test table to fabricate. [VERIFIED: .planning/ROADMAP.md:20]

### Finding-to-Validation Map

| D-215 finding / contract | Existing control surface | Purpose |
|---|---|---|
| CR-01 decoded/escaped path strings; CR-02 helper argument flow; CR-03 complete path containment | no_phase_paths_controls and no_phase_paths | Self-test causal negatives plus the complete tracked-file scan and must-scan floor. Existing registration lines quote the names exactly: add_test(NAME no_phase_paths_controls ...) and add_test(NAME no_phase_paths ...). [VERIFIED: tests/CMakeLists.txt:3004-3020] |
| CR-04 current/archive selection | phase22_evidence_controls and phase22_evidence_contract | Paired archive-removal negative and current-route positive in existing immutable evidence checker controls/contract. [VERIFIED: tests/CMakeLists.txt:3785-3799] |
| WR-01 raw byte pin parsing; WR-02 Git environment redirection | Existing non-ROM candidate Git-context controls in the dense-input harness; full fixture-bearing behavior stays in the protected matrix | Controls must mutate pin bytes/environment and assert exact rejection before any fixture execution. Do not invent a CTest target or run the fixture-bearing self-test locally. [VERIFIED: tests/scripts/verify-dense-input.py:134-202; .planning/phases/GB-24-resolve-remaining-v0-4-evidence-and-verification-gaps/24-VALIDATION.md:30] |
| Stale lexical allowance and full prior-route/trust checks | plan_cap, phase22_evidence_controls, phase22_evidence_contract, no_phase_paths_controls, no_phase_paths, workflow_policy_coverage_controls, and planning_hygiene_controls | Reuse the previously selected existing set; retain the plan-cap first and hygiene-control last order, 30-second hygiene timeout, and 125-control floor unless the later measured diagnosis justifies a same-coverage change. [VERIFIED: .planning/phases/GB-24-resolve-remaining-v0-4-evidence-and-verification-gaps/24-VALIDATION.md:20-31; tests/cmake/hygiene.cmake:73-85; tests/cmake/ci-lanes.cmake:144-148] |

The exact existing registered CTest identifiers are `plan_cap`, `phase22_evidence_controls`, `phase22_evidence_contract`, `no_phase_paths_controls`, `no_phase_paths`, `workflow_policy_coverage_controls`, and `planning_hygiene_controls`. The source-of-truth registrations quote `gbb_add_hygiene_test(plan_cap ...)` and `gbb_add_hygiene_test(planning_hygiene_controls ...)`, `add_test(NAME no_phase_paths_controls ...)` and `add_test(NAME no_phase_paths ...)`, `add_test(NAME phase22_evidence_contract ...)` and `add_test(NAME phase22_evidence_controls ...)`, plus `gbb_add_ci_lane_test(workflow_policy_coverage_controls ...)`. [VERIFIED: tests/cmake/hygiene.cmake:73-84; tests/CMakeLists.txt:3004-3020,3785-3791; tests/cmake/ci-lanes.cmake:147-148]

**Order:** First verify exact candidate/revision identity, syntax, current route/archive blobs, no unexpected source changes, candidate ancestry, and direct non-executing controls. Then inspect configured CTest JSON. Run the cheap plan-cap check first, the relevant focused controls/contracts next, the path tree scan as needed, and the 30-second planning_hygiene_controls last. Keep failure causes, test identities, environment, candidate SHA/tree, and any timeout stage in evidence. No test was run during this research. [VERIFIED: .planning/phases/GB-24-resolve-remaining-v0-4-evidence-and-verification-gaps/24-VALIDATION.md:20-23,35-49; .planning/context/WORKFLOW.md:41-49]

### Sampling Rate

- **Before each task's focused tests:** cheap syntax/identity checks and direct positive/negative controls for the specific changed seam.
- **Before CTest:** full candidate preflight from immutable Git objects, then --show-only=json-v1 inspection; no ROM-bearing local command.
- **Before remote qualification:** freeze the complete candidate SHA/tree, obtain a clean independent exact-head review, and only then run one full protected matrix with all current required contexts.
- **Stop:** any unresolved out-of-scope trust/correctness issue, blocker after the authorized review-fix passes, unavailable review, or failed/skipped/stale/missing required CI context. No extra review or matrix is implied.
- **Timeout policy:** preserve current limits until measured stage evidence identifies the cause; do not raise timeout to hide the failed step.

### Wave 0 Gaps

None. Existing standard-library controls and registered CTests are the intended implementation seams. No dependency, checker, CTest identity, phase, or plan is needed.

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
| Stale/missing CI context treated as green | Tampering / repudiation | Bind check runs to exact reviewed head and require all protected contexts to pass. |

Security claims about ASVS category applicability are task-domain mapping, not certification or a claim of completed security verification.

## CI and CD Efficiency

D-211's recorded 37-minute Linux stream with 44 failures and three preview consumers waiting roughly 70 minutes each is historical, not a current run measurement. The immediate safe improvement is faster feedback before the hosted matrix: syntax/identity checks, direct causal controls, immutable boundary checks, then only the existing focused CTests. The matrix itself stays complete and protected. [VERIFIED: .planning/phases/GB-24-resolve-remaining-v0-4-evidence-and-verification-gaps/24-01-PLAN.md:142; .planning/context/WORKFLOW.md:41-49]

For the next authorized PR matrix, record candidate SHA/tree, each job and step duration, queue time, dependency wait, timeout headroom, and whether package steps actually executed or were skipped. Assess whether the expensive root failure could have been detected before downstream waiters, but do not redesign cross-workflow waiters here, change triggers, add speculative cache/concurrency, or reduce required contexts. The D-211 package-waiter redesign is a separate measured follow-up. [VERIFIED: .planning/context/WORKFLOW.md:39-49; .planning/phases/GB-24-resolve-remaining-v0-4-evidence-and-verification-gaps/24-CONTEXT.md:61-70]

## Sources

### Primary repository sources

- [VERIFIED: .planning/phases/GB-24-resolve-remaining-v0-4-evidence-and-verification-gaps/24-CONTEXT.md:57-76] — D-215 six-finding scope, implementation recommendations, discretion, and planning-only authority.
- [VERIFIED: /private/tmp/24-D214-REVIEW.md:17-67] — Exact D-214 review text for CR-01–CR-04 and WR-01–WR-02; no tests or CI were run for that review.
- [VERIFIED: .planning/milestones/v0.4-REQUIREMENTS.md:56-71] — Authoritative archived requirement ownership/status and D-209 closeout.
- [VERIFIED: tests/scripts/verify-no-phase-paths.py:216-265,292-306,394-509] — Existing AST/token/source-site and path-reader implementation with the reviewed gaps.
- [VERIFIED: tests/scripts/verify-diagnostic-evidence.py:277-289,630-655] — Archive-pair fallback and current route conditional.
- [VERIFIED: tests/scripts/verify-dense-input.py:134-202] — Text-mode Git helper, pin validation, and temporary candidate repository setup.
- [VERIFIED: tests/scripts/verify-planning-hygiene.py:220-224] — Existing sanitized Git environment helper.
- [VERIFIED: .planning/context/WORKFLOW.md:37-49] — CI efficiency rules.
- [VERIFIED: .planning/phases/GB-24-resolve-remaining-v0-4-evidence-and-verification-gaps/24-01-PLAN.md:142] — Historical D-211 duration and waiter evidence.
- [VERIFIED: tests/cmake/hygiene.cmake:73-85; tests/CMakeLists.txt:3004-3020,3785-3799; tests/cmake/ci-lanes.cmake:144-148] — Current existing CTest identities and local floors/timeouts.

### Official documentation

- Python AST: [ast — Abstract Syntax Trees](https://docs.python.org/3/library/ast.html)
- Python lexical rules: [Lexical analysis](https://docs.python.org/3/reference/lexical_analysis.html)
- Python paths: [pathlib](https://docs.python.org/3/library/pathlib.html)
- Python subprocess behavior: [subprocess](https://docs.python.org/3/library/subprocess.html)
- Git environment behavior: [git documentation](https://git-scm.com/docs/git)
- OWASP ASVS 5.0.0 taxonomy: [official ASVS overview](https://asvs.owasp.org/); [official OWASP ASVS 5.0.0 CSV](https://github.com/OWASP/ASVS/blob/master/5.0/docs_en/OWASP_Application_Security_Verification_Standard_5.0.0_en.csv)

### Sources not used

No external package, product recommendation, or third-party fixture research was needed for this checker-and-CI recovery. Context7 tools were unavailable in this agent environment; official Python and Git documentation was opened directly as the documentation fallback.

## Metadata

**Confidence breakdown:**
- In-repository decisions and current test seams: HIGH — source-of-truth files were opened and exact task/CTest contracts were read.
- Python/Git behavior: MEDIUM — confirmed against official documentation; implementation must use the interpreter and OS configuration selected by the actual CMake build.
- CI efficiency opportunities: MEDIUM — the D-211 data is a recorded historical run; measure the next authorized exact-head matrix before claiming a current bottleneck or savings.

**Research date:** 2026-11-18
**Valid until:** Revisit if Python/Git version requirements, D-215 authority, phase requirements, or CI matrix membership change.
**Research execution boundary:** The original D-215 research did not authorize implementation. The additive D-216 research below records the owner's later authorization only for the four exact findings and focused local execution; protected review/matrix, merge and phase/milestone boundaries remain governed by current decisions.

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
