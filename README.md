# GabbaBoy

GabbaBoy is an original portable C17 Game Boy / Game Boy Color project. The
current implementation is only a headless DMG-CPU-B tracer foundation. It is
not a general emulator and does not execute a Nintendo boot ROM, support CGB,
or run commercial games.

## Build and run the tracer

Requirements: CMake 3.25 or newer, Ninja, and a C17 compiler. RGBDS is needed
only to reproduce the checked-in fixture; the normal configure, build, test,
and install flow uses checked-in files and does not access the network. Install
these tools explicitly before starting. The schema-6 preset accepts CMake 3.25.
The CMake 3.25.3 floor script passed locally in an Ubuntu 22.04 x86_64
container and in the hosted Phase 1 PR run, including install relocation and
external consumers. This checkout has also been exercised locally with CMake
4.4.3, Ninja 1.13.2, Apple Clang 21.0.0, and macOS 26.6.2. Hosted runner
results are evidence for those runner images, not minimum supported OS claims.

```sh
cmake --preset phase1
cmake --build --preset phase1
ctest --preset phase1 --output-on-failure --no-tests=error
./build/gabbaboy-runner fixtures/tracer/tracer.gb
```

Install the public C library, headless runner, and licensed fixture data into a
staging prefix:

```sh
cmake -E rm -rf build/package-prefix build/relocated-prefix
cmake --install build --prefix build/package-prefix
cmake -E rename build/package-prefix build/relocated-prefix
cmake -S . -B build -G Ninja -DGBB_TEST_INSTALL_PREFIX=build/relocated-prefix
ctest --test-dir build --output-on-failure --no-tests=error -R 'installed_(runner|consumer_(c|cpp))'
```

The install-smoke sequence also verifies package files and metadata for private
source/build paths. The installed-runner check starts from an unrelated working
directory.

Each downstream project uses `find_package(GabbaBoy CONFIG REQUIRED)`, links
`GabbaBoy::core`, and includes only the installed public header. The installed
runner is launched with the installed fixture from a separate working
directory. The exact-revision hosted native run passed these consumer checks
on Linux x64, macOS arm64, and Windows x64.

The runner reads the ROM file; the core receives a validated copy through its
public C API. The guest starts at cartridge entry 0x0100, stores 0x5A at 0xA000,
reads and compares it, then writes 0xA5 (success) or 0xEE (failure) at 0xA001.
The core executes only the fixture's listed instruction subset through its ROM
and RAM bus. The current ROM-only loader accepts an exact-size 32 KiB image;
other declared ROM sizes are rejected until their address mapping is supported.
Runs use a 200,000 half-dot maximum and a 256-record caller-owned
trace; the core stops explicitly on trace exhaustion. The runner formats a
bounded portion of that trace.

## Embedding contract

Consumers create and destroy an opaque `gbb_instance`; successful ROM loads
copy the caller's bytes, and failed replacements leave active state unchanged.
Instances own independent state and may be called by one thread at a time;
there is no shared mutable process state. `gbb_run` accepts a `uint64_t`
half-dot budget and caller-owned fixed-capacity trace storage, stops only at
instruction boundaries, reports ticks consumed and a structured reason, and
never exceeds the budget. A budget too small for the next instruction may make
no progress. The host interprets the fixture's RAM marker and formats trace
records. Errors distinguish invalid arguments/profile, malformed or
unsupported ROMs, allocation failure, unsupported opcodes, and bounded trace
exhaustion. The API and ABI may evolve; no stable ABI promise is made.

`gbb_queue_events` copies up to 64 ordered absolute half-dot events into each
instance. Equal timestamps keep caller order. The core accepts modeled STOP
wake transitions and external serial input bits; it does not implement full
joypad selection. A STOP wait can advance the bounded master timeline while
the CPU, divider, timer, and internal serial oscillator stay frozen. A wake at
the budget boundary is consumed before the next instruction, which still needs
its full instruction budget. No wall clock participates.

## Profile and evidence limits

The deterministic profile is named `DMG-CPU-B` and skips boot at 0x0100. The
CPU handoff values for this fixture are A=01, F=B0, B=00, C=13, D=00, E=D8,
H=01, L=4D, PC=0100, SP=FFFE. The nonzero header checksum selects F=B0 under the
profile rule. DIV=AB and STAT=85 are recorded as DMG/MGB handoff values, but
this tracer does not implement I/O behavior. WRAM/HRAM are hardware-volatile;
zero fill is an emulator policy, not a hardware claim. These applicable DMG
values follow [Pan Docs: Power Up Sequence](https://raw.githubusercontent.com/gbdev/pandocs/master/src/Power_Up_Sequence.md).

The fixture provenance, exact RGBDS v1.0.1 regeneration command, SHA-256,
success/failure protocol, reachable instruction inventory, authored license,
and exclusions are in [fixtures/tracer/manifest.json](fixtures/tracer/manifest.json).
`fixture_digest` verifies the committed ROM identity without requiring RGBDS.
The fixture is authored project material under the root MIT license; it does
not contain a boot ROM or the Nintendo logo.

## Continuous integration and fixture reproduction

Pull requests run `native-linux-x64` on Ubuntu 22.04, `native-macos-arm64` on
macOS 14, and `native-windows-x64` on Windows Server 2022. Each lane installs
the package and checks the required CTest inventory, including the installed
runner and external C/C++ consumers. `linux-asan-ubsan` runs the core suite
with AddressSanitizer and UndefinedBehaviorSanitizer. `cmake-floor-3.25.3`
downloads the official Linux x64 archive, verifies its published SHA-256, and
checks configure, build, test, install, relocation, and consumer use. The
`required-native` aggregate fails if any required evidence job is missing,
skipped, failed, or timed out. The separate `fixture-repro` status check uses
RGBDS v1.0.1 and compares regenerated bytes and the manifest digest.

### Pull requests and preview packages

Push a branch to this repository (or a fork) and open a pull request against
`main`. For a write-enabled clone, the command sequence is:

```sh
git switch -c feature/my-change
git push -u origin feature/my-change
gh pr create --base main
gh pr checks --required
```

The required contexts are `required-native`, `fixture-repro`, and
`preview-package-smoke`. Once the exact PR revision passes the required native
gate, the preview workflow tests the installed package on Linux x64 and macOS
arm64. Download the named `preview-linux-x64` or `preview-macos-arm64` artifact
from that PR's `preview-package-smoke` Actions run. No Windows preview package
is published.

These are temporary, run-scoped artifacts, not release archives. Each includes
the extracted-and-smoked package, a source SHA and package SHA-256 sidecar, the
smoke result, capability limits, and the configured 14-day retention. GitHub's
artifact API reports each run's actual `expires_at`; expiry belongs to that run
and does not promise durable availability.

The hosted implementation sample below was verified from PR #1 at source
revision `8396096ad17500974b30657af91fd2ef9ad51237`. The CI run, fixture-reproduction
run, required contexts, both artifacts, and downloaded package bytes all
matched that exact SHA. See the [PR](https://github.com/szTheory/gabbaboy/pull/1)
and its [preview workflow run](https://github.com/szTheory/gabbaboy/actions/runs/37141965332).

| Artifact | GitHub artifact digest | Smoked package SHA-256 | API created at | API expires at |
|----------|------------------------|------------------------|----------------|----------------|
| `preview-linux-x64` | `sha256:b2e3d57aa5cc8527bd05c2ee11d8e006495dd30193b38a08e828e11e60bd092b` | `045c5c063c48f5e125452f7053f670a75474059fa2e26e84dd365f88994a2726` | `2026-10-03T17:51:15Z` | `2026-10-17T17:51:14Z` |
| `preview-macos-arm64` | `sha256:d95990eab682cae084a5992777167a5fc6c71011eafa2326d8b74a5311499097` | `62462139dc88d4228b29cf2ea47d26176f3047dfc968a11f870d1a1f1143aef3` | `2026-10-03T17:51:19Z` | `2026-10-17T17:51:18Z` |

To reproduce the ROM locally, prepare RGBDS v1.0.1 explicitly and run the
three commands recorded in the manifest. Ordinary builds and `fixture_digest`
do not install or invoke RGBDS. Runner labels describe CI images; they do not
by themselves establish GabbaBoy's minimum supported operating systems. The
public repository is `https://github.com/szTheory/gabbaboy`, and `main` requires
the three contexts listed above. For the recorded sample, CI run `37141965336`
passed `required-native`, fixture run `37141965338` passed `fixture-repro`, and
preview run `37141965332` passed both platform smoke jobs and the aggregate
`preview-package-smoke` context. The CMake 3.25.3 floor and Linux/Windows native
consumer checks therefore have hosted evidence on this revision.

This evidence proves only that this original fixture reaches its guest RAM
success state under the named deterministic profile. It is not hardware-backed
validation, boot execution, broad DMG CPU coverage, CGB support, or gameplay.
