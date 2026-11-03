# GabbaBoy contributor and agent instructions

## Working preferences

### Communication and workflow preferences

- Speak to the user as a software engineer and colleague. Use plain, direct language. Keep necessary technical terms and explain unfamiliar workflow language through its practical consequence.
- End with the actual outcome, what remains broken or blocked, and the next useful action. Usually one short paragraph or at most three short bullets is enough. State clearly when no user action is needed.
- Keep hashes, internal task and threat IDs, exhaustive test counts, audit history, and workflow metadata in linked artifacts unless they are needed for a real decision or explicitly requested. Say what the checks establish in ordinary language.
- Give progress updates when there is new information. When a required update interval arrives during a long wait, use one brief factual line; do not repeat the whole plan or invent progress.
- Ask for user input only when the answer changes scope, authority, risk, cost, an irreversible action, or a required phase/milestone boundary. Explain the concrete choice and why it matters. Continue routine authorized work and bookkeeping without asking for acknowledgments or exact phrases.
- Preserve an existing safety stop automatically when its cause remains unresolved. A confirmation merely to keep work stopped is unnecessary. Removing redundant confirmation does not authorize live tests, accept risk, renew a budget/window, or start another phase.
- Record explicit user corrections in durable instructions. Apply these preferences to OpenGSD planning, execution, reviews, progress updates, and final summaries. Keep detailed evidence available without making the user translate process records into takeaways.
- When authorized work remains and no user action is needed, keep working. Carry planning through implementation, tests and review within the selected phase; stop for a real decision or phase/milestone boundary. Removing an unnecessary confirmation is not a reason to leave the task idle.
- At every pause or handoff, state in chat what is happening, the concrete blocker and consequence, your recommended next step, and exactly who acts next. Explicitly say when waiting for the user versus continuing work.
- Summarize every risk or decision in plain language before asking; make linked documents optional detail. When the user has no strong preference, recommend a concrete path. An uninformed or indifferent response is not risk acceptance.
- Prefer the least disruptive evidence-supported remedy. For stuck project tests, inspect attributable processes and consider targeted cleanup first; recommend a whole-machine restart only when its necessity and impact are established.

- For lightweight delegated work in Codex, prefer GPT-6 Luna (`gpt-6-luna`) with extra-high (`xhigh`) reasoning effort for cost efficiency. Delegate only when authorized; reserve stronger-model synthesis or review for consequential tradeoffs.

## Identity and current state

GabbaBoy targets **Game Boy and Game Boy Color**. Copied NES/Neo Geo/Elixir examples are background, not implementation requirements. Read `.planning/STATE.md`, `.planning/PROJECT.md`, and `.planning/research/SUMMARY.md` before substantial work. If a file is missing during bootstrap, read `.planning/context/BRIEF.md` and continue initialization; never claim an unimplemented emulator works.

## Workflow contract

- Use the installed **OpenGSD** runtime (`@opengsd/gsd-core`); check runtime identity when a different install or tool path is encountered.
- User authorization permits research agents and parallel work where ownership is independent. Recommended routine decisions, meaningful tests, fixes, PRs, merges after required checks, and releases are authorized within the active phase.
- **Stop after each phase. Never auto-advance into another phase or milestone.** Keep `workflow.auto_advance` and `workflow._auto_chain_active` false. Report evidence and the exact next command, then yield for the owner to choose when to continue.
- At every workflow handoff, name the stage and phase actually completed (initialization is not Phase 1), the next phase by number and title, and one specific copy-paste GSD command derived from current artifacts. Persist that route in STATE.md and the continuation note. Do not substitute a generic progress/next command or restart completed work. Reuse recorded research and decisions; revisit them only for a concrete gap or changed evidence.
- Preserve the phase pause even when a workflow's `--auto` branch would chain commands. Initial project setup stops before Phase 1.
- Automate verification and shift it left (DECISIONS D-069): every deliverable gets an automated check with a negative control, so `/gsd-verify-work` needs zero human checkpoints by default. Do not invent manual UAT merely to satisfy a workflow template; if an item looks like a human reading, write the contract check instead. Hand off only true perceptual/hardware/credential limitations and owner decisions, with the smallest necessary human action. Write every plan SUMMARY `coverage:` entry in the GSD block schema (`id`, `description`, `human_judgment`, block-style `verification` items with `kind` unit/integration/e2e/automated_ui/other, `ref`, `status: pass`; no `{...}` flow items, no `ctest` kind, no inline `#` comments); the `summary_coverage` CTest rejects anything verify-work could not auto-pass. At verify-work, write and check the closure with `tests/scripts/verify-uat-closure.py <phase-dir> --write <evidence> | --self-test` instead of hand-writing UAT.md or copying a phase-local checker. Boundary checks must read point-in-time facts from the boundary commit, never assert live routes or ancestry from the current HEAD.
- Keep phases small and convergent (DECISIONS D-102–D-105):
  - At most 4 phases and about 40 plans per milestone, and at most 12 plans per phase. A 50% overrun triggers a rescope.
  - At most 2 review-fix rounds and 1 gap round per phase. An unresolved correctness or security finding forces a rescope, never a seed.
  - No quotas, clocks or run counters as evidence.
  - Checkers live in `tests/scripts/`, read an immutable commit and are wired into CTest when created.
  - Re-verify once at the final head rather than refreshing each phase.
- At every milestone boundary, scan the sibling emulator cores and Playstead for transferable lessons (LESSONS.md XFER rows), then refresh the rolling roadmap in `.planning/context/FUTURE-MILESTONES.md`.
- During CI runs and CI/release handoffs, follow [CI/CD efficiency](.planning/context/WORKFLOW.md#cicd-efficiency): assess measured bottlenecks and recurring automation value while preserving required coverage and release gates.
- Use phase branches and PRs when a remote exists. Merge only the reviewed/tested revision with required checks satisfied; never treat skipped checks, stale runs, or a local pass as proof that a remote revision is green. Do not bypass branch protection.
- Keep main releasable; update source, API docs, examples, tests, and limitation notes together. Triage open issues/PRs at phase and release boundaries; record access failures honestly.
- Before marking work complete, inspect its current verification evidence, release/consumer evidence where relevant, and requirement traceability. An earlier agent's completion claim is not sufficient evidence.

## Engineering rules

- Original portable C core, explicit ownership and error behavior, bounded public operations, no hidden globals. Host timing, filesystem, UI, audio devices, and environment configuration stay in adapters.
- Prefer small direct code and targeted abstractions. Explain hardware reasons and subtle invariants; do not obscure them with generic frameworks or clever compression.
- Require evidence before performance complexity. Benchmarks identify revision, build, hardware, workload, model, output digest, warm-up, samples, and uncertainty.
- Guard ROM/save/state boundaries against overflow, truncation, excess allocation/work, and partial mutation. Use explicit portable serialization rather than raw C structure dumps.
- Distinguish hardware-backed tests, differential oracle results, metamorphic properties, regression fixtures, and private game observations. Declare model applicability, exclusions, and expected-failure reasons.
- No Nintendo boot ROMs, commercial game images, unlicensed homebrew, private data, or mandatory telemetry in the repository. Every third-party fixture needs documented redistribution rights and a digest.
- Local secrets use ignored `.env.local`; Actions secrets or short-lived credentials serve automation. Never add personal home paths, emails, machine identifiers, or secret values to public artifacts. Use a privacy-safe Git author for project automation.

## Durable memory

Keep `.planning/research/INDEX.md` as the navigation entry point, topic documents as evidence, `.planning/context/DECISIONS.md` as adopted choices, `.planning/ROADMAP.md` as active milestone detail, and `.planning/context/FUTURE-MILESTONES.md` as revisable direction. Update `.planning/context/LESSONS.md` with concrete cause, evidence, remedy, applicability, and verification; export only concise sanitized lessons for sibling projects. Local precedent may be incomplete or superseded.

No phase is complete solely because documents were written, tests were listed, or a video/audio screenshot looked plausible.
