# Phase 1: Portable Foundation and Original ROM Tracer - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-10-02
**Phase:** 1-Portable Foundation and Original ROM Tracer
**Areas discussed:** Tracer startup and proof; Public run and trace contract; Fixture build and provenance; Host checks and downloadable artifacts

---

## Tracer startup and proof

| Option | Description | Selected |
|--------|-------------|----------|
| DMG-CPU-B post-boot + guest-visible RAM result | Named deterministic post-boot profile; original guest writes, reads, checks a result and branches to success/failure loops. | ✓ |
| Mooneye-style `LD B,B` breakpoint | Familiar test convention; risk of making a normal guest opcode a hidden emulator success signal. | |
| Caller-supplied boot ROM | Adds boot-to-cart evidence and input provenance, but expands scope and requires a separately identified boot image. | |

**User's choice:** Accepted the recommended decision.
**Notes:** Keep the claim limited to the named profile, fixture, and implemented opcode subset. No boot-ROM execution or synthetic output claim.

---

## Public run and trace contract

| Option | Description | Selected |
|--------|-------------|----------|
| Strict half-dot tick budget + caller-owned bounded trace | Return actual ticks and explicit stop reasons; structured fixed-size records; no overrun or silent output loss. | ✓ |
| Instruction-count-only limit | Easy to reason about for a CPU demo, but not aligned with the project’s emulated-time API direction. | |
| Callback/overwriting ring trace | Can stream or retain recent events, but adds lifetime/reentrancy rules or risks losing the failure prefix. | |

**User's choice:** Accepted the recommended decision.
**Notes:** Keep ROM-specific pass/fail in the runner, not the reusable core API. Too-small tick budgets may make no progress if the next whole instruction will not fit; document this behavior.

---

## Fixture build and provenance

| Option | Description | Selected |
|--------|-------------|----------|
| Check in source + binary + manifest; required pinned-tool CI comparison | Offline normal build; readable and reproducible source-to-binary path; assembler confined to CI verification. | ✓ |
| Check in generated binary and manifest only | Lowest tool burden, but source-to-ROM provenance cannot be independently reproduced. | |
| Generate ROM on every build/test | Reproducible source path, but makes assembler availability part of routine build and offline setup. | |

**User's choice:** Accepted the recommended decision.
**Notes:** Owner prefers copying a small necessary piece over adding a dependency. RGBDS is accepted only as an isolated pinned CI verification dependency; do not add it to the core or ordinary offline build.

---

## Host checks and downloadable artifacts

| Option | Description | Selected |
|--------|-------------|----------|
| Three native CI hosts, two preview packages | Linux x64, macOS arm64, Windows x64 checks; publish Linux x64 and macOS arm64 after install smoke. | ✓ |
| Linux-only CI/package | Smallest matrix, but weak evidence for the future macOS consumer and portable C/C++ integration. | |
| Broad OS/architecture package matrix | Wider reach, but creates more maintenance and support expectations before demand/evidence. | |

**User's choice:** Accepted the recommended decision.
**Notes:** Windows is CI build/consumer-tested only, without a Phase 1 downloadable package. Use source-revision-identified workflow artifacts with digest and smoke result; disclose run-artifact retention and do not imply a durable release archive. Pin explicit runner and OS floors when their native consumer checks are planned.

---

## the agent's Discretion

- Exact DMG-CPU-B post-boot values and opcode inventory, selected with model-applicable evidence.
- Exact RGBDS and build/action versions, pinned immutably.
- Exact OS release floors and runner labels, limited to versions receiving actual consumer smoke.
- Public field/enum names and package layout, so long as the accepted bounded and ownership contracts are preserved.

## Deferred Ideas

None.

---

## Research lenses and sources

The one-shot recommendation synthesized hardware/model evidence, emulator/API architecture, product/integrator behavior, test and fixture provenance, C portability, dependency and supply-chain risk, CI/release operations, and maintenance cost. No player UI decision applies to Phase 1.

Sources checked 2026-10-02: [Mooneye Test Suite](https://github.com/Gekkio/mooneye-test-suite/blob/main/README.markdown), [Pan Docs: Rendering](https://gbdev.io/pandocs/Rendering.html), [RGBDS](https://github.com/gbdev/rgbds), [CMake custom commands](https://cmake.org/cmake/help/latest/guide/tutorial/Custom%20Commands%20and%20Generated%20Files.html), [CMake install/export](https://cmake.org/cmake/help/latest/guide/tutorial/Installation%20Commands%20and%20Concepts.html), [GitHub-hosted runners](https://docs.github.com/en/actions/reference/runners/github-hosted-runners), [GitHub workflow artifacts](https://docs.github.com/en/actions/concepts/workflows-and-actions/workflow-artifacts), and [GitHub Actions secure use](https://docs.github.com/en/actions/reference/security/secure-use).
