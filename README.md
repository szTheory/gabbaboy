# GabbaBoy

GabbaBoy is an original portable C17 Game Boy / Game Boy Color project. The
current implementation is only a headless DMG-CPU-B tracer foundation. It is
not a general emulator and does not execute a Nintendo boot ROM, support CGB,
or run commercial games.

## Build and run the tracer

Requirements: CMake 3.25 or newer, Ninja, and a C17 compiler. RGBDS is needed
only to reproduce the checked-in fixture; the normal configure, build, test,
and install flow uses checked-in files and does not access the network. Install
these tools explicitly before starting. The schema-6 preset accepts CMake 3.25,
but that minimum is not yet qualified: this checkout has been exercised locally
with CMake 4.4.3, Ninja 1.13.2, Apple Clang 21.0.0, and macOS 26.6.2. The CMake
3.25.3 floor and other OS/compiler combinations remain unverified until native
CI completes.

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
directory. These are local macOS smoke results; Linux and Windows native
consumer results are pending CI.

The runner reads the ROM file; the core receives a validated copy through its
public C API. The guest starts at cartridge entry 0x0100, stores 0x5A at 0xA000,
reads and compares it, then writes 0xA5 (success) or 0xEE (failure) at 0xA001.
The core executes only the fixture's listed instruction subset through its ROM
and RAM bus. Runs use a 200,000 half-dot maximum and a 256-record caller-owned
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

This evidence proves only that this original fixture reaches its guest RAM
success state under the named deterministic profile. It is not hardware-backed
validation, boot execution, broad DMG CPU coverage, CGB support, or gameplay.
