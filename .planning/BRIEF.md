# GabbaBoy — founding brief

Recorded: 2026-10-02. Source: the project owner's kickoff request. This is a normalized brief, not a claim that any emulator functionality exists.

## Identity and purpose

GabbaBoy is a new emulator for **Nintendo Game Boy and Game Boy Color**, written in C. Earlier NES and Neo Geo descriptions in the founding prompt are examples from sibling projects; they do not define this hardware target. Game Boy Advance is a separate architecture and is not implicitly included in “Game Boy etc.”

The core should be correct, fast, portable, safe with untrusted inputs, easy to embed, and unusually pleasant to read and learn from. Its long-term ambition is excellent compatibility across the Game Boy family, with honest evidence for every support claim. It should integrate with Playstead and other frontends through clear video, audio, input, persistence, timing, and diagnostic interfaces. A small usable macOS player is needed while Playstead is still developing.

## Product priorities

1. Correct emulated behavior and preservation of users' saves.
2. A deterministic, reusable C core with explicit ownership and no frontend dependency.
3. Early downloadable releases that progressively play useful software.
4. Measured speed, resource use, responsiveness, and regression resistance.
5. Readable educational code, simple architecture, current documentation, and effortless integration.

“Ultimate” is an aspiration to improve measurable quality continuously, not permission to claim universal compatibility or to build every feature before the first release.

## Development workflow

- Use **OpenGSD**, the `@opengsd/gsd-core` lineage, with a searchable, source-linked `.planning/` second brain.
- **Stop after every completed phase. Do not auto-advance, begin the next phase, or automatically begin another milestone.** The owner wants a checkpoint to inspect results and optionally change the session model. This is a workflow pause, not a mandatory manual software acceptance test.
- Within an authorized phase, use judgment and recommended defaults; avoid repeated approval questions. Research, plan review, implementation, automated verification, fixes, documentation, and release preparation belong in the workflow.
- Parallel specialist research and independent execution are explicitly authorized when useful. Consider architecture, low-level C, hardware emulation, security, testing, performance, build engineering, DevOps, adopter experience, and maintainability; synthesize decisions rather than accumulating disconnected advice.
- Prefer PRs, green main, prompt issue/PR triage, automated merging after required checks, and frequent automated releases. This authorization persists; a green check must actually cover the revision being merged and the artifact being shipped.
- Maintain detailed current work, provisional next milestones, and a revisable long-term direction. Refresh this at phase and milestone boundaries.

## Quality and engineering expectations

- Portable idiomatic C, CMake, clear contracts, minimal dependencies, KISS/YAGNI. Elixir/Phoenix/Ecto/Hex and database examples in the generic prompt do not apply to the emulator implementation.
- Test happy paths, real error paths, boundary conditions, and integration seams. Add property tests, sanitizers, fuzzing, differential checks, deterministic test ROMs, and packaged-consumer checks where they detect meaningful failures.
- Automate verification as far as possible. Keep human checks for irreducible perceptual/hardware/credential questions; convert repeatable checks into automation when it has recurring value.
- Establish correctness, compatibility, performance, memory, build-time, and CI-time baselines with useful workloads, provenance, and regression budgets. Extreme tail percentiles require enough samples and controlled conditions; avoid decorative statistics or noisy gates.
- Fast deterministic CI: parallelize useful work, avoid redundant matrix jobs and oversubscription, use safe caches, pin dependencies, separate quick PR gates from expensive scheduled exploration, and preserve failure evidence.
- Document architecture, public API and lifetime rules, tutorials, build/install, supported hardware, known limitations, testing, release/recovery, and upgrade compatibility as the implementation changes.
- Optional bounded diagnostics should help integration and debugging without mandatory network services or avoidable hot-loop overhead.

## Sources and sibling projects

Review recent planning and actual implementation in `glueyneo`, `nesturbator`, and `playstead`. Review active relevant OSS practices in `lattice_stripe` and `exifcleaner/exifcleaner-electron`. Treat these as evidence with dates and implementation status, not as mature infallible templates. Inspect Playstead's homebrew fixture and CI practices without assuming a fixture for another console is valid for Game Boy.

Use hardware research, test authors, official documentation, upstream code/history, and maintainers' issue discussions as primary sources whenever possible. Record source URL or repository-relative path, revision/date when available, confidence, applicability, and contradictions. Cross-project lessons must be portable, auditable, and safe to paste into other emulator sessions.

## Distribution, privacy, and licensing

- Public repository intended; do not include personal information, machine-specific home paths, private conversations, credentials, or proprietary ROM/boot images.
- MIT is the initial recommendation, subject to a source/dependency/license audit; retain third-party notices and investigate licenses per asset, including ROMs and artwork.
- Local credentials, if ever needed, belong in ignored `.env.local`; automation credentials belong in GitHub Actions secrets or suitable short-lived credentials. The emulator core should not require secrets or read environment configuration.
- The owner can personally exercise legally obtained game images. Private game collections are not repository fixtures or public CI dependencies.

## Initialization endpoint

Prepare durable research and a coherent OpenGSD project foundation. The owner confirmed: **research and initialize now, then stop before Phase 1**. Include a precise fresh-context continuation command. Do not begin emulator implementation during this foundation task.
