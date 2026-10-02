# GabbaBoy technology stack

Researched: 2026-10-02. Scope: Game Boy / Game Boy Color core, development player, integration and packaging. Status: proposed decisions for project initialization; no implementation is claimed.

Evidence confidence: **MEDIUM**, returned by OpenGSD `query classify-confidence --provider websearch --verified`. Official sources were opened and cross-checked where practical; exact dependency/compiler pins still require phase-specific verification. Context7 was selected by the research seam but unavailable as either MCP or CLI, so official web documentation was used. Recommendations below are engineering judgments, distinguished from documented tool capabilities.

## Recommended decisions

| Decision | Recommendation | Rationale and tradeoff |
|---|---|---|
| Language | ISO C17 for core and tools; required standard, extensions disabled | Portable baseline across Apple Clang, Clang, GCC and MSVC. C23 has useful features, but adds no necessary emulator capability and would narrow the supported toolchain set. MSVC documents `/std:c17` and an experimental `/std:clatest`; reassess C23 by tested feature support, not the standard's age. [S1][S2] |
| Build | CMake minimum **3.25**, Ninja default, CTest, committed preset schema **6** | This floor supports configure/build/test/package/workflow presets. It is a deliberate minimum, not a claim about the latest release. Ordinary `cmake -S/-B` use must also work. [S1][S3] |
| Core dependencies | C standard library only; no SDL, network, filesystem, process-global configuration or runtime plugin discovery | Makes Playstead, other frontends, fuzzers and embedded-style integrations possible. This does not initially promise a freestanding C implementation. |
| First player | Optional SDL3 application, with SDL API floor 3.2 and an exact stable release pinned when implemented | Portable C integration and an early macOS build; keep interface small: open ROM, input, video, audio, save status, reset/pause, scaling and useful errors. SDL3 is already a distinct API from SDL2. [S4][S5] |
| Public library | `GabbaBoy::core` CMake target, static build first; one opaque instance type and a narrow public C header | Straightforward embedding. Support a shared build with explicit exports when delivering binary core packages; source API stability and binary ABI stability are separate promises. |
| Additional frontend | Optional libretro adapter after basic playable DMG and reliable state restoration | Broad integration opportunity, but do not make libretro's lifecycle or global entrypoints the internal architecture. The header is permissively licensed separately from the frontend implementation. [S8] |
| Testing | CTest driving small C contract tests, hardware fixtures and standalone consumers; plain assertions that stay active in test builds | Avoid a large framework until features require it. Tests need useful failure output and nonzero failures in Release builds; C `assert` alone disappears with `NDEBUG`. |
| Dynamic analysis | Dedicated Clang ASan+UBSan build; libFuzzer-compatible narrow harnesses | Detect memory and integer/alignment errors without burdening release consumers. LLVM notes libFuzzer receives fixes rather than major feature development; retain engine-independent harness logic. [S9][S10][S11] |
| Formatting / static analysis | Pinned clang-format; focused clang-tidy or Clang analyzer checks when source exists | One formatting convention; avoid competing linters and blanket suppression churn. Pin tool versions independently of consumer compiler minimums. |
| Benchmarks | Small headless C workload runner emitting structured results | Measures the actual core without introducing C++ into the library or GUI timing into CPU throughput. Add a separate host playback benchmark for audio/video latency. |
| Project license | MIT for original code; preserve each dependency/fixture's actual terms | Short permissive terms suit a reusable core. Apache-2.0 offers an explicit contributor patent grant with additional distribution obligations; it is a valid alternative if that policy outweighs simplicity. [S12][S13] |

## C engineering contract

1. Use fixed-width unsigned types for guest registers and explicitly wide intermediates for arithmetic; use `size_t` for host buffer lengths. Assert supported host assumptions such as `CHAR_BIT == 8` and required integer widths. Avoid signed overflow, implementation-dependent negative shifts, plain-`char` signedness assumptions and shifting beyond the operand width. Hardware wrap is deliberate; allocation-size wrap is an error. [S14][S15]
2. Decode external bytes with explicit endian helpers. Never cast ROM/save bytes to a wider integer pointer or packed struct; alignment and effective type rules still apply on permissive x86 hosts. Save states use explicit fields, lengths and versions, never a dump of C struct memory. [S16]
3. Ordinary control flow, named invariants and short functions beat macro metaprogramming. Use `static`/`static inline` helpers when appropriate; avoid macro arguments with repeated evaluation, undocumented aliasing promises, VLAs, unions used as serialization formats, and unbounded recursion.
4. Default compiler warnings: GCC/Clang `-Wall -Wextra -Wpedantic -Wconversion -Wsign-conversion -Wshadow -Wstrict-prototypes -Wmissing-prototypes`; MSVC `/W4`. Enable only supported flags for each compiler. `-Werror`/`/WX` belong to maintained CI presets and an opt-in developer switch, never exported consumer usage requirements. Treat intentional narrowing locally with an invariant, not a project-wide suppression. [S17][S18]
5. Keep compiler flags target-scoped. Release optimization starts at compiler-standard Release settings; no `-march=native`, blanket `-ffast-math`, computed-goto requirement or mandatory LTO. Profile before adding dispatch tricks or SIMD; retain a portable reference path and compare identical observable results.
6. ROM, boot ROM, battery save, state and future cheat inputs are untrusted. Validate actual buffer size before every field read; bound supported cartridge sizes, state section counts, allocations and emulated work. Parse into temporary state and commit after full validation so an error cannot corrupt the active session. Keep archive extraction out of the core.
7. Allocation failure and malformed input return explicit errors; the library never calls `exit`, aborts for guest input, writes unsolicited output, or overwrites a host file. Allocate machine storage at creation/load; avoid recurring heap allocations in the normal stepping path and measure this invariant.
8. Keep mutable machine state per instance. A single instance is externally serialized; distinct instances may run independently. Defer core threading. This simplifies determinism, multiple emulated consoles and fuzzing without making optional C atomics a portability requirement.

## Integration contract to lock before gameplay code

- Core accepts bytes, configuration and timestamped input, and advances a bounded amount of **emulated** work. Return actual work consumed and stop reason; a stalled guest or disabled display must not trap a frontend in a wait-for-frame loop.
- Define model selection, reset/boot behavior, output pixel layout and pitch, audio format/rate, callback thread, pointer lifetimes, buffer capacities, cancellation/stop semantics and error behavior in the public header.
- Prefer core-owned immutable ROM storage initially, with documented load-copy cost; expose borrowed access only where lifetime rules materially help an integrator. Frame/audio data may be borrowed until a documented next call, or written into caller-owned buffers with lengths.
- `create`/`destroy` pair within the library; do not require a frontend to `free` memory allocated across another runtime/CRT. Status values and sizes must have specified types. No C++ exceptions, STL types, bitfield layouts or private structs in the ABI; wrap declarations with `extern "C"` for C++ consumers.
- Separate library version, ABI version and serialized-state version. Add explicit structure sizes/version fields only for public extensible configurations that actually need them. In 0.x, document changes and migration rather than claiming indefinite ABI stability.
- File access, atomic battery-save replacement, host time, RTC catch-up policy, controller mapping, windowing and audio devices belong to the host. Deterministic replay records RTC/input events; reading wall time inside stepping would invalidate it.
- Complete snapshots contain all emulated in-flight state. Rewind/runahead restore emulated state and suppress speculative persistence, rumble, logging and audio presentation. Host device queues and wall-clock timestamps are not portable machine state.
- A later libretro adapter owns one context behind its required entrypoints. Direct C callers retain multi-instance capability. Do not copy frontend implementation code merely because `libretro.h` is permissively licensed. [S8]

## Build and packaging shape

Core-only configure must succeed offline with SDL absent. Use options such as `GABBABOY_BUILD_PLAYER=OFF`, `GABBABOY_BUILD_TESTS`, `GABBABOY_BUILD_BENCHMARKS`, `GABBABOY_BUILD_FUZZERS` and `GABBABOY_BUILD_LIBRETRO`; prefix all project options. The developer player preset opts into SDL. Prefer `find_package(SDL3 CONFIG REQUIRED)` for installed development dependencies; an explicit, pinned dependency-fetch mode may simplify release builds without hiding network access in ordinary core configuration. [S4]

Install public headers, the selected library, package/version config and exported targets using relative install paths. Keep private flags, source paths and SDL out of core's exported interface. Test package relocation and a fresh external C and C++ consumer, for example:

```cmake
find_package(GabbaBoy CONFIG REQUIRED)
add_executable(consumer main.c)
target_link_libraries(consumer PRIVATE GabbaBoy::core)
```

The same consumer must also work through `add_subdirectory` without GabbaBoy changing the parent project's warnings, build type, testing policy or installation prefix. `CMakeUserPresets.json` stays ignored; committed presets reproduce documented commands. [S3][S6]

macOS: deliver a native architecture artifact as soon as the player is usable; publish separate arm64/x86_64 artifacts if both are tested. A universal binary is supported by SDL's build instructions but is not proof that both architectures were exercised. Select an explicit deployment target after checking runner SDKs and the intended supported macOS floor. Package SDL with the application, or statically link it where verified, so downloading a player does not require Homebrew. [S5]

## Audio and presentation boundaries

The emulated machine determines event timing; the host determines when to present outputs. Keep cycle/frame stepping independent of display refresh and audio device clocks. Provide bounded audio storage, queue-depth/underrun counters and a recovery policy for pause, seek, device changes and fast-forward. Use SDL audio streams for device-format conversion. `SDL_GetAudioStreamQueued` counts **input bytes**, not output frames or complete device latency; retain format knowledge and do not turn it directly into a latency claim. [S7]

The player may adjust host pacing and, with a measured small bounded correction, host-side resampling to maintain a target audio queue. It must not silently alter CPU/timer relationships. Rewind flushes stale presentation queues. Runahead must prove restore/replay equivalence before it becomes an advertised feature. Input-to-photon and input-to-audio latency require end-to-end measurement; core execution time alone does not establish them.

## Version and license gate for implementation

Before Phase 1 pins tools, record exact CMake/Ninja/compiler/SDL versions, immutable download hashes or commits, release dates, supported runner images, macOS deployment target and licenses in one manifest. Test the minimum supported build separately from the maintained CI compiler set; do not float release dependencies to `main` or assume a major-version action tag is immutable. A version that was not fetched and checked here is deliberately not called “latest.”

Apply MIT to original GabbaBoy code with a public-safe contributor attribution. SDL 2.0 and newer use zlib; retain bundled notices. Apache's patent grant comes from contributors and is not a blanket guarantee about unrelated patents. Keep third-party code and asset attribution explicit. Proprietary boot ROMs, commercial games and private save files are never release/test artifacts; every redistributable homebrew fixture requires its own license and hash record. [S8][S12][S13][S19]

## Sources

All retrieved 2026-10-02. Official living documentation unless noted; exact dependency versions are not frozen by these links. Confidence is MEDIUM under the research seam; the application choices above remain recommendations.

- [S1 — CMake C_STANDARD, required level and extension controls](https://cmake.org/cmake/help/latest/prop_tgt/C_STANDARD.html)
- [S2 — Microsoft C/C++ language-standard switches](https://learn.microsoft.com/en-us/cpp/build/reference/std-specify-language-standard-version?view=msvc-170) (page updated 2025-01-30)
- [S3 — CMake presets and schema version history](https://cmake.org/cmake/help/latest/manual/cmake-presets.7.html)
- [S4 — SDL3 CMake introduction](https://wiki.libsdl.org/SDL3/INTRO-cmake)
- [S5 — SDL3 macOS build instructions](https://wiki.libsdl.org/SDL3/README-macos)
- [S6 — CMake importing and exporting guide](https://cmake.org/cmake/help/latest/guide/importing-exporting/index.html)
- [S7 — SDL3 queued audio semantics](https://wiki.libsdl.org/SDL3/SDL_GetAudioStreamQueued)
- [S8 — Libretro API header and its specific license](https://github.com/libretro/RetroArch/blob/master/libretro-common/include/libretro.h), [core development overview](https://docs.libretro.com/development/cores/developing-cores/)
- [S9 — Clang AddressSanitizer](https://clang.llvm.org/docs/AddressSanitizer.html)
- [S10 — Clang UndefinedBehaviorSanitizer](https://clang.llvm.org/docs/UndefinedBehaviorSanitizer.html)
- [S11 — LLVM libFuzzer status and target contract](https://llvm.org/docs/LibFuzzer.html)
- [S12 — MIT license text](https://opensource.org/license/mit)
- [S13 — Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0)
- [S14 — SEI CERT signed integer overflow](https://cmu-sei.github.io/secure-coding-standards/sei-cert-c-coding-standard/rules/integers-int/int32-c/)
- [S15 — SEI CERT unsigned integer wrap](https://cmu-sei.github.io/secure-coding-standards/sei-cert-c-coding-standard/rules/integers-int/int30-c/)
- [S16 — SEI CERT alignment and pointer conversions](https://cmu-sei.github.io/secure-coding-standards/sei-cert-c-coding-standard/rules/expressions-exp/exp36-c/)
- [S17 — GCC warning options](https://gcc.gnu.org/onlinedocs/gcc/Warning-Options.html)
- [S18 — MSVC warning levels](https://learn.microsoft.com/en-us/cpp/build/reference/compiler-option-warning-level?view=msvc-170)
- [S19 — SDL license](https://www.libsdl.org/license.php)
