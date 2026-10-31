# OpenGSD workflow and operating policy

Recorded 2026-10-02. Authority: the owner's founding request and confirmed endpoint. This policy applies to GabbaBoy, not to other projects.

## Runtime and reproducibility

The installed runtime returned `{"packageName":"@opengsd/gsd-core","version":"1.14.0"}` from `runtime-identity --raw` during initialization. The installed `gsd-new-project` skill and `new-project.md` workflow were read. [OpenGSD's official repository](https://github.com/open-gsd/gsd-core) describes the discuss → plan → execute → verify → ship loop and the `@opengsd/gsd-core` package (retrieved 2026-10-02). Local installed behavior is the authority for the current session; recheck upstream changes at a future upgrade.

During Phase 1 planning on 2026-10-02, the active `gsd_run` PATH launcher reported version 1.15.0, while a separately invoked direct tool path reported 1.14.0. All phase workflow actions and final plan-structure checks use `gsd_run` 1.15.0; the alternate-path invocation was read-only and is not the workflow runtime. Recheck `gsd_run runtime-identity` if the launcher or runtime path changes.

Use Codex skill commands such as `$gsd-progress`, `$gsd-discuss-phase 1`, and `$gsd-plan-phase 1`. Do not rerun `$gsd-new-project` against a completed initialization. Do not install a similarly named predecessor or silently upgrade the working runtime as part of emulator implementation.

## Authorized execution and stopping rule

The owner approved adopting recommended defaults, parallel research, automated verification, PRs, green-check merges, and frequent releases. Therefore project setup does not need repetitive approvals for the brief, recommended requirements, or roadmap. The owner separately confirmed that this task ends **before Phase 1**.

For each later phase, execute the authorized scope and applicable research/review/verification/ship work, then stop. Never interpret `mode: yolo` as permission to start the next phase. Maintain both `workflow.auto_advance: false` and `workflow._auto_chain_active: false`. A skill's automatic next-command branch is subordinate to this owner instruction.

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
2. Prefer existing unit, integration, seam, e2e and smoke checks with meaningful negative controls. Move a check into existing CI when it prevents a recurring regression; keep one-off closure bookkeeping local. Reuse completed, unchanged UAT and source-bound receipts. Reopen only changed covered behavior, concrete failures or newly discovered evidence gaps.
3. Implement a small improvement within authorized scope when measured benefit is clear, then run its affected contracts and negative controls. Preserve test membership, platform/configuration coverage, sanitizer/fuzz policy, source/artifact binding, required checks and release authority. Assess cache correctness and all downstream waiter deadlines before changing scheduling or reuse.
4. When an improvement needs broader scope or lacks evidence, record a bounded follow-up with its trigger and expected benefit. A finding of no justified safe change is a valid outcome. Never retry an unchanged timed-out run as a substitute for diagnosis or inflate deadlines merely to hide wasted work.
5. At handoff, report material bottlenecks or the absence of an actionable change in one sentence; retain detailed timings in linked evidence. Human work is limited to irreducible perception/hardware/credential constraints and owner decisions. Required phase/milestone pauses remain in force.

## Git, PRs, and releases

- Initial local planning is committed with a generic project author. Future public commits should retain privacy-safe metadata; never copy a local identity into documentation.
- Phase 1 establishes the remote and actual CI/release automation. Until that exists, document that remote checks, protection, and release status are unavailable.
- Use PRs after bootstrap. Review the actual diff; require passing checks for the relevant head/merge revision and ensure branch/ruleset requirements are respected.
- Bot-triggered CI and release chaining must be verified on the target repository. Current GitHub event/token details belong in `research/QUALITY-AND-DELIVERY.md`; do not perpetuate older assumptions from sibling projects.
- Prefer the smallest scoped GitHub App permission set when unattended bot PR checks need it. Keep untrusted fork execution away from write credentials. Local secrets stay in ignored `.env.local`, never in `.planning/`.
- Promote verified bytes; record artifact digest, source revision, version, license inventory, release notes, and rollback path. Do not describe signing/notarization as configured until credentials and successful checks exist.

## Continuous maintenance

At every phase: assess the weakest relevant quality dimension, fix a high-value gap within scope or add a concrete follow-up, update docs, inspect issue/PR status if a remote exists, and retain failure evidence. Do not run a full expensive audit simply because a phase ended.

At every milestone: review the support matrix, correctness corpus coverage, performance/CI trends, adoption friction, API/state evolution, security boundaries, and release reliability. Refresh the current and proposed future milestones. Keep numerical goals grounded in recorded measurements rather than invented precision.

## Simplicity reference

The requested [Ponytail reference](https://ponytail.dev/) advocates avoiding speculative functionality and preferring existing or standard mechanisms before adding code (retrieved 2026-10-02). GabbaBoy adopts that principle as design judgment. It does not adopt promotional benchmark claims or minimize code at the expense of safety, hardware correctness, or readability.
