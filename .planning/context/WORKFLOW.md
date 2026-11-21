# OpenGSD workflow and operating policy

Recorded 2026-10-02. Authority: the owner's founding request and confirmed endpoint. This policy applies to GabbaBoy, not to other projects.

## Runtime and reproducibility

The installed runtime returned `{"packageName":"@opengsd/gsd-core","version":"1.14.0"}` from `runtime-identity --raw` during initialization. The installed `gsd-new-project` skill and `new-project.md` workflow were read. [OpenGSD's official repository](https://github.com/open-gsd/gsd-core) describes the discuss → plan → execute → verify → ship loop and the `@opengsd/gsd-core` package (retrieved 2026-10-02). Local installed behavior is the authority for the current session; recheck upstream changes at a future upgrade.

During Phase 1 planning on 2026-10-02, the active `gsd_run` PATH launcher reported version 1.15.0, while a separately invoked direct tool path reported 1.14.0. All phase workflow actions and final plan-structure checks use `gsd_run` 1.15.0; the alternate-path invocation was read-only and is not the workflow runtime. Recheck `gsd_run runtime-identity` if the launcher or runtime path changes.

Use Codex skill commands such as `$gsd-progress`, `$gsd-discuss-phase 1`, and `$gsd-plan-phase 1`. Do not rerun `$gsd-new-project` against a completed initialization. Do not install a similarly named predecessor or silently upgrade the working runtime as part of emulator implementation.

## Authorized execution and stopping rule

The owner approved adopting recommended defaults, parallel research, automated verification, PRs, green-check merges, and frequent releases. Therefore project setup does not need repetitive approvals for the brief, recommended requirements, or roadmap. The owner separately confirmed that this task ends **before Phase 1**.

For each later phase, execute the authorized scope and applicable research/review/verification/ship work, then stop unless the owner explicitly authorizes an autonomous multi-phase run. Never interpret `mode: yolo` alone as permission to start the next phase. Maintain both `workflow.auto_advance: false` and `workflow._auto_chain_active: false`; GSD Autonomous can manage its explicitly authorized sequence without enabling these flags.

### Owner directive for the remaining v0.4 milestone (2026-11-15)

The owner wants the remaining v0.4 work to proceed with `$gsd-autonomous` through milestone audit, completion, and cleanup. D-206 supersedes the earlier Phase 23.1 route for this bounded closeout: Phase 24 is reopened in its sole existing plan; the current route is `$gsd-autonomous --from 24`. Do not restart completed Phase 23.1 work. Autonomous work must stop on unresolved correctness/security findings, exhausted budgets, safety stops, unmet original criteria, or failed required gates. This directive is specific to completing the remaining v0.4 milestone.

On 2026-11-15, the owner supplied the Phase 23.1 recovery discussion and verification defaults. That recovery is historical and complete. D-206 now authorizes the bounded Phase 24 closeout using only its existing plan and named candidates; resume with `$gsd-autonomous --from 24`. Preserve D-103's one exact final PR matrix, no extra full retry, third lifecycle retest, release/tag/asset changes, or gap acceptance. Stop if any original criterion, required right, correctness/security finding, or required gate remains open. At milestone closeout, reconcile through the approved PR/merge flow, return to `main`, verify the expected merged head and clean working tree, and close/remove only the clean worktree.

The configuration uses `model_profile: inherit` so a new session's model choice carries into research and execution. Hardcoded model aliases from older installations must not override that choice. Use `git.branching_strategy: phase`, the canonical nested setting; a legacy top-level setting can conflict with defaults.

## Verification without unnecessary UAT

1. Turn observable acceptance criteria into executable assertions at the appropriate boundary: core, headless runner, installed consumer, or packaged player.
2. Use legal deterministic fixtures and record revision, model, inputs, seeds/time, pass protocol, output digest, and timeout. Missing fixtures are setup failures rather than green skips in required lanes.
3. Exercise the actual release artifact from a clean extraction/install, not only the build tree.
4. Compare perceptual audio/video manually only when automation cannot establish the intended quality; keep routine mechanics automated. Hardware experiments are a separate evidence class.
5. Distinguish a user's requested phase pause from a software acceptance gate. Phase completion still needs evidence; a pause never justifies marking unverified behavior complete.

`workflow.human_verify_mode: end-of-phase` is the runtime's supported setting. No fictional `none` value is introduced. Planning instructions instead suppress unnecessary human-check tasks and reserve them for genuinely irreducible work.

## CI/CD efficiency

Owner directive renewed at Phase 19 verification (2026-10-31); D-069 remains the standing automation-first policy. Apply this section whenever observing an active or finished CI run, changing workflows, preparing a PR, or qualifying a release/CD handoff.

1. Inspect available job/step durations, queue/dependency waits and timeout headroom. Identify cheap, evidence-supported improvements: repeated setup/build/download work, serial independent checks, redundant full streams, oversized fetches/artifacts and unnecessary polling. Record the relevant run/revision and finding once in the phase evidence; an active run supports only provisional timing conclusions.
2. Prefer existing unit, integration, seam, e2e and smoke checks with meaningful negative controls. Move a check into existing CI when it prevents a recurring regression; keep one-off closure bookkeeping local. Reuse completed, unchanged UAT and source-bound receipts. Reopen only changed covered behavior, concrete failures or newly discovered evidence gaps. After configuration, run Python checks with the interpreter recorded in `CMakeCache.txt` and prepend its binary directory when checks launch `python3` children. Record the interpreter/environment with results; a different interpreter’s source-check pass does not establish configured CTest timing.
3. Implement a small improvement within authorized scope when measured benefit is clear, then run its affected contracts and negative controls. Preserve test membership, platform/configuration coverage, sanitizer/fuzz policy, source/artifact binding, required checks and release authority. Assess cache correctness and all downstream waiter deadlines before changing scheduling or reuse.
4. When an improvement needs broader scope or lacks evidence, record a bounded follow-up with its trigger and expected benefit. A finding of no justified safe change is a valid outcome. Never retry an unchanged timed-out run as a substitute for diagnosis or inflate deadlines merely to hide wasted work.
5. At handoff, report material bottlenecks or the absence of an actionable change in one sentence; retain detailed timings in linked evidence. Human work is limited to irreducible perception/hardware/credential constraints and owner decisions. Required owner-decision and blocker pauses remain in force; an explicitly authorized GSD Autonomous run may cross routine phase boundaries only within its declared scope.
6. Before proposing a targeted job retry, inspect consumers of artifacts named by run attempt. A copied successful job record may carry a newer attempt label while its execution times, artifact name and verified receipt still identify the old producer. Check the actual frozen waiter selection and artifact/receipt binding before spending consumer jobs. Include any necessary producer refresh in the concrete bounded budget proposal; never relabel old bytes, waive identity checks, count copied records as new executions, or extend an exact attempt limit through this guidance.
7. Within current task authority, stop obsolete prerequisite-only waiters when their upstream attempt cannot qualify and an approved recovery will run their required consumers after upstream success. Preserve a pre-cancel snapshot establishing that product work did not run, keep every required consumer gate, and start the approved consumer recovery only after upstream qualification. Cancellation is resource cleanup, not a pass or a renewed retry allowance.

8. At a repeated release-recovery frontier, preflight the actual remaining executable commands against all existing digest-checked products before consuming another expensive hosted attempt. Include option parsing, real archive roots, the same trusted checker path, and refusal controls for added game bytes or outer payloads. A static wiring pass and a helper-only test do not establish that the real command can consume the real package. Record measured execution separately from projected savings; preserve protected CI, source identity, all limits and the explicit retry allowance.

## Discuss and verification defaults

- For each substantive phase discussion, adapt the owner's fan-out prompt to the project's actual technical domain. Consider independent stakeholder and engineering lenses, useful primary sources, pros/cons, common footguns, established patterns, and an adversarial pass. Continue parallel exploration only while it yields independent information, then give one synthesized recommendation. Prefer existing APIs and small standard-library implementations before adding dependencies.
- For verification, automate observable contracts early and include meaningful negative controls. Run cheap consistency checks before expensive suites. Use throwaway local checks when they provide useful feedback; put checks in CI when they prevent recurring regressions, not merely to make every local check permanent. Reserve human validation for genuine perception, hardware, credential, or owner decisions.
- When CI or release runs occur, inspect measured queue/dependency/run durations and critical paths, recommend only evidence-supported savings, and preserve all required coverage and release gates.

## Git, PRs, and releases

- Initial local planning is committed with a generic project author. Future public commits should retain privacy-safe metadata; never copy a local identity into documentation.
- Phase 1 establishes the remote and actual CI/release automation. Until that exists, document that remote checks, protection, and release status are unavailable.
- Use PRs after bootstrap. Review the actual diff; require passing checks for the relevant head/merge revision and ensure branch/ruleset requirements are respected.
- Bot-triggered CI and release chaining must be verified on the target repository. Current GitHub event/token details belong in `research/QUALITY-AND-DELIVERY.md`; do not perpetuate older assumptions from sibling projects.
- Prefer the smallest scoped GitHub App permission set when unattended bot PR checks need it. Keep untrusted fork execution away from write credentials. Local secrets stay in ignored `.env.local`, never in `.planning/`.
- Promote verified bytes; record artifact digest, source revision, version, license inventory, release notes, and rollback path. Do not describe signing/notarization as configured until credentials and successful checks exist.
- At milestone closeout, reconcile reviewed/required work onto `main` using the established branch/PR flow, then leave the milestone worktree and verify the expected merged `main` head plus a clean working tree. Close/remove the milestone worktree only after reconciliation and only when it has no uncommitted work; retain evidence of the final branch, head, and clean status.

## Continuous maintenance

At every phase: assess the weakest relevant quality dimension, fix a high-value gap within scope or add a concrete follow-up, update docs, inspect issue/PR status if a remote exists, and retain failure evidence. Do not run a full expensive audit simply because a phase ended.

At every milestone: review the support matrix, correctness corpus coverage, performance/CI trends, adoption friction, API/state evolution, security boundaries, and release reliability. Refresh the current and proposed future milestones. Keep numerical goals grounded in recorded measurements rather than invented precision.

## Simplicity reference

The requested [Ponytail reference](https://ponytail.dev/) advocates avoiding speculative functionality and preferring existing or standard mechanisms before adding code (retrieved 2026-10-02). GabbaBoy adopts that principle as design judgment. It does not adopt promotional benchmark claims or minimize code at the expense of safety, hardware correctness, or readability.
