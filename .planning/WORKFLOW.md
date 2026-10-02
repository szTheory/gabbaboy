# OpenGSD workflow and operating policy

Recorded 2026-10-02. Authority: the owner's founding request and confirmed endpoint. This policy applies to GabbaBoy, not to other projects.

## Runtime and reproducibility

The installed runtime returned `{"packageName":"@opengsd/gsd-core","version":"1.14.0"}` from `runtime-identity --raw` during initialization. The installed `gsd-new-project` skill and `new-project.md` workflow were read. [OpenGSD's official repository](https://github.com/open-gsd/gsd-core) describes the discuss → plan → execute → verify → ship loop and the `@opengsd/gsd-core` package (retrieved 2026-10-02). Local installed behavior is the authority for the current session; recheck upstream changes at a future upgrade.

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
