# Phase 1: Portable Foundation and Original ROM Tracer - Context

**Gathered:** 2026-10-02
**Status:** Ready for planning

<domain>
## Phase Boundary

Deliver a portable C17 core and headless runner that developers can build, install, and embed through a documented bounded C API, and that executes one original GB ROM through the real CPU/bus path to produce a deterministic bounded trace. Include the fixture provenance, external C/C++ installed-consumer checks, required CI evidence, and a revision-linked foundation-preview artifact. This is a narrow DMG tracer slice: it does not claim a complete CPU, boot-ROM execution, interactive gameplay, CGB support, or general Game Boy compatibility.

</domain>

<decisions>
## Implementation Decisions

### Tracer startup and proof
- **D-01:** Expose one named DMG-CPU-B deterministic post-boot profile. Start cartridge execution at the documented entry point; do not ship or require a boot ROM. Reject unsupported model profiles explicitly.
- **D-02:** Use an original GabbaBoy ROM that writes a known value to guest RAM, reads and checks it, then branches to distinct success and failure loops. The headless runner recognizes the outcome from guest-visible state and retains a bounded trace. The declared opcode subset is exactly what this ROM needs; unsupported execution is explicit. Do not special-case an opcode as a hidden success signal or substitute synthetic display output for guest execution.
- **D-03:** Describe this evidence as execution of the named model/profile and fixture only. It does not establish boot, hardware-timing, full CPU, or broad game-compatibility behavior. Keep the exact post-boot values and opcode inventory tied to model-applicable evidence during planning.

### Public run and trace contract
- **D-04:** Bound public execution by a `uint64_t` half-dot tick budget, report actual ticks consumed and a structured stop reason, and preserve a strict upper bound. Stop at instruction boundaries; do not begin an instruction that would exceed the remaining budget. Document that a budget too small for the next supported instruction can return without progress.
- **D-05:** Trace output is optional, fixed-size, structured, and written into caller-owned storage. Records identify instruction-boundary time, PC/opcode bytes, and CPU state. Capacity exhaustion is explicit and never overwrites earlier records, silently drops output, or allocates. The host formats records. The core reports execution status; the headless runner interprets this fixture's success/failure protocol.
- **D-06:** Keep diagnostics and lifecycle behavior instance-owned, bounded, and free of hidden process globals. Do not expose callback reentrancy or output formatting as part of the Phase 1 API.

### Fixture build and provenance
- **D-07:** Keep the authored assembly, exact generated ROM bytes, and a fixture manifest together. Record source identity, license and notice, assembler/build recipe and version, ROM digest, model/boot applicability, result protocol, and timeout.
- **D-08:** Ordinary build/test flows use the checked-in ROM and verify its digest without needing an assembler or network. A required isolated CI check uses a pinned RGBDS release to regenerate and byte-compare the ROM. RGBDS is a fixture-verification tool only, not a core, runtime, or routine offline-build dependency. Review fixture rights separately from tool licensing; a matching hash establishes identity, not redistribution permission.

### Host checks and downloadable artifacts
- **D-09:** Require native Linux x64, macOS arm64, and Windows x64 CI coverage. Concentrate ASan/UBSan on Linux; run installed C and C++ consumer smokes on macOS and Windows. Pin explicit runner and OS floors based on the versions actually tested; make no claim for untested OS releases or architectures.
- **D-10:** Publish only Linux x64 and macOS arm64 core/runner preview packages after matching installed-package smoke succeeds. Windows is build/consumer-tested in CI but has no Phase 1 downloadable package. Attach artifacts to the tested workflow run and identify the source revision, digest, and smoke result. Disclose the retention policy; a run artifact is not a durable release archive.

### Cross-cutting preference
- **D-11:** Keep the emulator core on the C standard library only and keep dependency trees small and flat. Add a dependency only when its concrete security, readability, or evidence value justifies the cost. The accepted RGBDS use is limited to the required fixture regeneration check in CI.

### the agent's Discretion
- Resolve the precise post-boot register/device values and opcode inventory from applicable references and tests; select the immutable RGBDS and build/action pins; set supported OS floors to versions that receive actual consumer smoke; and choose field/enum names and packaging layout. Preserve the decisions above, keep tool versions fixed rather than floating, and state unverified assumptions as limitations.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Scope, requirements, and workflow
- `AGENTS.md` — contributor rules, privacy, phase pauses, evidence and runtime identity.
- `.planning/PROJECT.md` — product purpose, accepted architecture direction, constraints, and current implementation status.
- `.planning/REQUIREMENTS.md` — BASE-01 through BASE-08 requirements and Phase 1 traceability.
- `.planning/ROADMAP.md` — Phase 1 goal, deliverables, and success criteria.
- `.planning/STATE.md` — current phase/session route and workflow state.
- `.planning/context/BRIEF.md` — owner priorities, expected adopter, and dependency preferences.
- `.planning/context/DECISIONS.md` — especially D-008 through D-010 for profile, timing, bounded API; recommendations remain distinct from implementation evidence.

### Emulator model, timing, and validation
- `.planning/research/INDEX.md` — navigation and evidence-use rules for the topic research.
- `.planning/research/SUMMARY.md` — project synthesis, Phase 1 research flags, and initial acceptance direction.
- `.planning/research/ARCHITECTURE.md` — half-dot timeline, bounded stepping, post-boot model direction, and API ownership seams.
- `.planning/research/HARDWARE-AND-VALIDATION.md` — fixture licensing/provenance, model applicability, result protocols, and corpus limits.
- `.planning/research/PITFALLS.md` — failure modes for false evidence, model confusion, unbounded work, and skipped CI.
- `.planning/research/PRECEDENT.md` — sibling project evidence and transferable lessons, with their limits.

### Build, API, and delivery
- `.planning/research/STACK.md` — C17/CMake baseline, core dependency policy, public C/C++ consumer contract, and tool pinning.
- `.planning/research/QUALITY-AND-DELIVERY.md` — sanitizer, required CI inventory, package smoke, workflow security, artifact identity, and delivery policy.

No separate external SPEC/ADR was found for this phase; the project requirements and decisions above define the current boundary.
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- None yet. The repository contains planning documents, `README.md`, and `LICENSE`; no emulator source, CMake project, ROM fixture, test suite, or CI workflow exists.

### Established Patterns
- No implementation patterns exist to reuse. Planning establishes portable C17, CMake/Ninja/CTest, an installed `GabbaBoy::core`, standard-library-only runtime core, and explicit instance ownership as the starting direction.

### Integration Points
- Phase 1 creates the public C header/library, headless runner, original ROM path, installed C and C++ consumers, required CI gate, and revision-linked core/runner artifact. The optional SDL macOS player belongs to Phase 3, not this phase. There is currently no configured Git remote.
</code_context>

<specifics>
## Specific Ideas

- Owner preference: “another copy and paste is better than another dep”; a dependency is acceptable when it is genuinely needed, with a preference for small, flat dependency trees and avoiding unnecessary abstractions.
- Apply that preference to keep RGBDS out of runtime and ordinary builds while retaining the isolated reproducibility check described above.
- Primary technical sources consulted on 2026-10-02: [Mooneye Test Suite](https://github.com/Gekkio/mooneye-test-suite/blob/main/README.markdown), [Pan Docs: Rendering](https://gbdev.io/pandocs/Rendering.html), [RGBDS](https://github.com/gbdev/rgbds), [CMake generated files](https://cmake.org/cmake/help/latest/guide/tutorial/Custom%20Commands%20and%20Generated%20Files.html), [CMake install/export](https://cmake.org/cmake/help/latest/guide/tutorial/Installation%20Commands%20and%20Concepts.html), [GitHub-hosted runners](https://docs.github.com/en/actions/reference/runners/github-hosted-runners), [GitHub workflow artifacts](https://docs.github.com/en/actions/concepts/workflows-and-actions/workflow-artifacts), and [GitHub Actions secure use](https://docs.github.com/en/actions/reference/security/secure-use).

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within Phase 1 scope.

</deferred>

---

*Phase: 1-Portable Foundation and Original ROM Tracer*
*Context gathered: 2026-10-02*
