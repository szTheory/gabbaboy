# Walking Skeleton — GabbaBoy

**Phase:** GB-01
**Generated:** 2026-10-02

## Planned End-to-End Capability

This is the Phase 1 acceptance target, not a current capability or verification claim. No emulator implementation or runnable CMake project exists yet. The plan must deliver a CMake 3.25 minimum project with a schema-6 `CMakePresets.json`, an installable headless native C17 core, and a relocated external consumer that runs the original tracer through the public API and observes the guest RAM result with a bounded trace.

## Architectural Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Core language | Portable C17 | Opaque instance-owned API, bounded operations, and no hidden globals. |
| Build minimum/preset schema | CMake 3.25 minimum with committed preset schema 6 | Match the project stack contract; an exact 3.25.3 configure/build/test/install and relocated-consumer lane must pass before documenting the floor as supported. |
| Data layer | Not applicable | The emulator state is owned in memory by each core instance; this phase defines no database or persistence. |
| Auth | Not applicable | The local native library and runner have no user identity or authentication surface. |
| Deployment target | CMake install/export package `GabbaBoy::core`; revision-linked CI run artifacts for Linux x64 and macOS arm64 | External consumers prove package relocation; run artifacts identify the tested revision and disclose retention. |
| Directory layout | `include/gabbaboy/`, `src/core/`, `src/runner/`, `fixtures/tracer/`, `tests/`, `cmake/`, `.github/workflows/` | Keeps public contract, emulator, host file adapter, fixture, validation, package, and CI boundaries explicit. |
| Model profile | Named deterministic DMG-CPU-B post-boot profile | Starts at cartridge entry without a boot ROM; emulator-defined deterministic values are not hardware-random RAM or boot-ROM evidence. |
| Run/trace boundary | `uint64_t` half-dot budget; instruction-boundary stop; optional fixed caller-owned structured trace | Prevents overshoot and unbounded host work without core allocation or formatting. |
| Guest result | Fixture-specific guest-visible RAM success/failure states; unsupported and timeout are separate outcomes | Proves real CPU/bus execution and avoids a hidden success opcode. |

## Stack Touched in Phase 1

- [ ] Project scaffold: C17, CMake/Ninja/CTest, `CMakePresets.json` schema 6, install/export target
- [ ] Headless runner entry point
- [ ] Guest RAM write/read/compare path exercised through the core and bus
- [ ] External C and C++ consumers use the relocated installed package
- [ ] Documented local configure/build/test/install/run commands
- [ ] Database — not applicable to the in-memory native core
- [ ] Authentication — not applicable to a local library/runner
- [ ] Interactive UI — not applicable; SDL player is owned by Phase 3
- [ ] Deployment evidence — documented local full-stack command and tested workflow artifacts when remote access is available

## Out of Scope

- Nintendo boot-ROM execution, full CPU/gameplay, CGB support, MBC, persistence, SDL/player UI, and stable ABI promise.
- A database, authentication, web route, or interactive UI.
- Windows preview package; Windows remains native build and installed-consumer CI coverage only.

## Subsequent Slice Plan

- Phase 2: Execute the declared DMG CPU, bus, and timing behavior with bounded deterministic progress.
- Phase 3: Run a visible interactive DMG fixture through the SDL player.
- Phase 4: Add scoped MBC1 and safe battery continuation.
- Phase 5: Add DMG audio and stable playback.
- Phase 6: Qualify the limited-DMG release and consumer handoff.
