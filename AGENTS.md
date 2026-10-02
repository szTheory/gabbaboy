# GabbaBoy contributor and agent instructions

## Identity and current state

GabbaBoy targets **Game Boy and Game Boy Color**. Copied NES/Neo Geo/Elixir examples are background, not implementation requirements. Read `.planning/STATE.md`, `.planning/PROJECT.md`, and `.planning/research/SUMMARY.md` before substantial work. If a file is missing during bootstrap, read `.planning/BRIEF.md` and continue initialization; never claim an unimplemented emulator works.

## Workflow contract

- Use the installed **OpenGSD** runtime (`@opengsd/gsd-core`); check runtime identity when a different install or tool path is encountered.
- User authorization permits research agents and parallel work where ownership is independent. Recommended routine decisions, meaningful tests, fixes, PRs, merges after required checks, and releases are authorized within the active phase.
- **Stop after each phase. Never auto-advance into another phase or milestone.** Keep `workflow.auto_advance` and `workflow._auto_chain_active` false. Report evidence and the exact next command, then yield for the owner to choose when to continue.
- Preserve the phase pause even when a workflow's `--auto` branch would chain commands. Initial project setup stops before Phase 1.
- Automate verification. Do not invent manual UAT merely to satisfy a workflow template. Record true perceptual/hardware/credential limitations and propose the smallest necessary human action.
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

Keep `.planning/research/INDEX.md` as the navigation entry point, topic documents as evidence, `DECISIONS.md` as adopted choices, `ROADMAP.md` as active milestone detail, and `FUTURE-MILESTONES.md` as revisable direction. Update `LESSONS.md` with concrete cause, evidence, remedy, applicability, and verification; export only concise sanitized lessons for sibling projects. Local precedent may be incomplete or superseded.

No phase is complete solely because documents were written, tests were listed, or a video/audio screenshot looked plausible.
