# Phase 1: Portable Foundation and Original ROM Tracer - Pattern Map

**Mapped:** 2026-10-02  
**Files analyzed:** 20 implementation, fixture, validation, packaging, and workflow file groups inferred from CONTEXT.md and RESEARCH.md  
**Analogs found:** 0 / 20 implementation analogs

## File Classification

The phase artifacts name directories and responsibilities rather than committing to exact source filenames. The paths below are planning targets inferred from the recommended structure and BASE-01 through BASE-08. The planner should settle exact filenames and avoid treating this list as existing repository structure.

| New/Modified File or Group | Role | Data Flow | Closest Analog | Match Quality |
|----------------------------|------|-----------|----------------|---------------|
| `CMakeLists.txt` | config | transform/build | None | no analog |
| `include/gabbaboy/gabbaboy.h` (or equivalent public header) | model/API | request-response | None | no analog |
| `src/core/*` (instance lifecycle, profile, CPU, bus, cartridge, stepping) | service/model | request-response, CRUD | None | no analog |
| `src/runner/*` (headless executable) | controller | file-I/O, request-response | None | no analog |
| `fixtures/tracer/*` (RGBDS assembly, checked ROM, notice/license, manifest) | fixture/config | transform | None | no analog |
| `tests/*` (API/lifecycle, loader, tracer, digest, negative controls) | test | request-response, file-I/O | None | no analog |
| `tests/consumers/c/*` | test | request-response | None | no analog |
| `tests/consumers/cpp/*` | test | request-response | None | no analog |
| `cmake/*` (install/export config and test helpers) | config/utility | transform | None | no analog |
| `.github/workflows/*` (native CI, fixture regeneration, required gate, artifact) | config | event-driven, batch | None | no analog |
| `README.md` (build/install/API/limitations/PR and artifact workflow docs) | documentation | request-response | `README.md` | weak documentation-only |

**Repository evidence:** `git ls-files` contains only project/planning documentation, `.gitignore`, `LICENSE`, and `README.md`. There are no tracked C/C++ sources, CMake files, fixture files, tests, or workflow files. `01-CONTEXT.md` also explicitly says no reusable implementation assets or established implementation patterns exist. No path under `.planning/research/.cache/` or other runtime/cache location is used as an analog.

## Pattern Assignments

There are no existing implementation analogs or code excerpts to copy. Apply the following grounded design constraints from the phase artifacts when planning the first implementation:

### Public API and core (`include/gabbaboy/*`, `src/core/*`)

**Analog:** None. This is a new C17 library, not an extension of existing code.

- Keep core runtime dependencies to the C standard library. Use opaque, instance-owned state; no hidden process globals, host clock, file I/O, formatting, or callbacks.
- Model/profile initialization must name DMG-CPU-B and represent a deterministic post-boot contract. Reject unsupported profiles explicitly; do not imply boot-ROM execution.
- ROM loading must validate bounds, header, and supported cartridge type before mutating an existing instance. Unsupported/truncated/oversized inputs return explicit errors.
- Public run operations use a `uint64_t` half-dot budget, return actual ticks and structured stop reason, and stop at instruction boundaries without starting an instruction that exceeds the remaining budget.
- Trace records are fixed-size, optional, structured, caller-owned, and bounded. Capacity exhaustion is explicit and preserves already-written records. Core status is separate from fixture pass/fail interpretation.
- Implement only the exact instruction subset reached by the assembled original tracer fixture; unsupported execution is explicit. The final opcode inventory depends on the source and assembled bytes and remains a planning/implementation deliverable.

### Headless runner (`src/runner/*`)

**Analog:** None.

- This host adapter owns ROM file access and bounded host-side trace formatting. It interprets only the named fixture's guest-visible RAM result protocol.
- Pass/fail must result from normal CPU/bus execution and the fixture-produced state; do not add a special success opcode, synthetic display result, or host-side shortcut.
- Apply an explicit emulated-time timeout and report unsupported, failure, and timeout distinctly.

### Original fixture (`fixtures/tracer/*`)

**Analog:** None.

- Keep authored assembly, generated ROM bytes, and manifest together. The manifest records source identity, rights/notice, assembler/build recipe and version, digest, model/boot applicability, result protocol, and timeout.
- The guest writes a known value to RAM, reads/checks it, and enters different success and failure loops with guest-visible results.
- Normal offline build/test uses the checked-in ROM and verifies its digest. A separate required CI lane uses pinned RGBDS to regenerate and byte-compare it; RGBDS is not a runtime or normal-build dependency.

### Tests and installed consumers (`tests/*`)

**Analog:** None. CTest, test framework/config, and consumer projects do not yet exist.

- Derive expected tracer behavior independently from fixture source/assembled bytes; include negative controls for bad read/compare/branch, failure marker, unsupported opcode, and timeout.
- Test bounds, non-destructive load errors, independent instances, lifecycle/reset, tick no-overshoot, trace capacity, and explicit unsupported results.
- Build standalone C and C++ consumer projects against an installed and relocated package, resolving `GabbaBoy::core` without source-tree/private include paths; execute the tracer.
- Treat installed consumers and package smoke as integration evidence, distinct from emulator correctness evidence.

### CMake/package config (`CMakeLists.txt`, `cmake/*`)

**Analog:** None.

- Establish the first build system using the research recommendation CMake 3.25, Ninja, and CTest. Offline configure/build/test/install must not fetch network content or require SDL/RGBDS.
- Use standard CMake install/export and a namespaced `GabbaBoy::core` target; test a relocated install from independent consumer projects.
- Exact minimum tool and host OS versions remain to be pinned based on successful smoke evidence.

### CI and artifact workflows (`.github/workflows/*`)

**Analog:** None. No CI workflow or configured Git remote exists.

- Create explicit native Linux x64, macOS arm64, and Windows x64 lanes. Concentrate ASan/UBSan on Linux; run installed C and C++ consumer smoke on macOS and Windows.
- Pin actions to reviewed immutable full SHAs and runner images to explicit labels. A required aggregate gate must check the expected test/job inventory and fail closed for missing, skipped, failed, or timed-out evidence.
- Publish only Linux x64 and macOS arm64 preview artifacts after installed-package smoke. Bind artifact, source revision, digest, and smoke result; disclose run-artifact retention. Windows is tested but not packaged in this phase.
- No live remote/PR/required-check evidence can be inherited from this repository; report remote/credential limitations if they remain.

### Documentation (`README.md`)

**Analog:** `README.md` is tracked, but it is a project-status and navigation page only. It has no build, API, or emulator-use procedures to copy.

- Update documentation with verified configure/build/test/install commands, consumer integration, exact tested platforms, API ownership/time/error rules, and evidence limitations. Do not describe the project as runnable before implementation evidence exists.

## Shared Patterns

No code-level cross-cutting patterns exist yet. Phase decisions establish these constraints for all relevant new files:

- **Ownership and bounded work:** instance state belongs to each core instance; public operations and trace storage have explicit finite bounds.
- **Error behavior:** invalid or unsupported input/execution is explicit; failed ROM loading must preserve prior valid state.
- **Layering:** core executes deterministic guest behavior; runner owns host files, fixture protocol, and formatting; build/test/CI adapters remain outside the core.
- **Evidence language:** label results as named model/profile and fixture behavior. Do not claim boot execution, complete CPU behavior, timing accuracy, CGB support, or broad compatibility from this slice.
- **Dependency boundary:** no SDL in the core/headless path; RGBDS only in isolated fixture regeneration verification.

## No Analog Found

| File/Group | Role | Data Flow | Reason |
|------------|------|-----------|--------|
| Public C header and core modules | model/service | request-response, CRUD | No source code or API exists. |
| Headless runner | controller | file-I/O, request-response | No executable or host adapter exists. |
| Original ROM fixture and manifest | fixture/config | transform | No ROM, assembly, or fixture metadata exists. |
| Core/runner tests and C/C++ consumers | test | request-response, file-I/O | No test suite or consumer project exists. |
| CMake build/install/export | config | transform | No CMake project or package config exists. |
| GitHub Actions CI and artifact workflows | config | event-driven, batch | No workflow exists and no remote is configured. |

## Metadata

**Analog search scope:** repository root and tracked files; `.planning` context/research artifacts; `README.md`; `LICENSE`; tracked-file inventory via `git ls-files`.  
**Files scanned:** all tracked paths; phase context and research sections covering structure, validation, requirements, and implementation patterns.  
**Pattern extraction date:** 2026-10-02
