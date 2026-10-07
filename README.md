# GabbaBoy

GabbaBoy is an original portable C17 Game Boy / Game Boy Color project. The
current headless core implements a declared, bootless DMG-CPU-B CPU, bus, timer,
serial and deterministic-time profile, exercised by owned tests and three
source-pinned CPU/timer diagnostic ROMs. It does not execute a Nintendo boot
ROM, render video, support CGB or establish general game compatibility.

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

The default test preset is offline and uses only checked-in fixture bytes. For
an exact installed-package check, run `bash tests/scripts/verify-phase2-installed.sh`;
it installs and relocates the package, then verifies fresh installed and
core-only CTest inventories.

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

The original tracer remains a narrow API/install smoke fixture. Its historical
use of the cartridge external-RAM window at 0xA000 was fixture policy, not
hardware behavior; its current protocol uses WRAM at 0xC000. It runs from the
cartridge entry point with a 200,000 half-dot maximum and bounded caller-owned
trace storage.

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

`gbb_queue_events` atomically copies up to 64 absolute half-dot events into each
instance. Timestamps cannot be in the past or move backward; equal timestamps
keep caller order. Empty batches, including `NULL, 0`, succeed. Invalid and
over-capacity batches do not partially append. The core accepts modeled STOP
wake transitions and external serial input bits; it does not implement full
joypad selection. Runs preflight a whole CPU operation and never overshoot the
requested budget. `NO_PROGRESS`, `STOPPED`, `HALTED_IDLE`, lockup, unsupported
bus behavior and output exhaustion are separate outcomes. A STOP wait can
advance the bounded master timeline while CPU, divider, timer and internal
serial oscillator work stays frozen. A wake at the budget boundary is
consumed before the next instruction, which still needs its full instruction
budget. No wall clock participates.

`gbb_run_ex` optionally writes chronological instruction, bus and timer
diagnostics into caller-owned storage. It reserves space for a complete
operation before mutation; insufficient capacity returns output-full without
writing that operation's records. The core does not allocate or format
diagnostics.

## Profile and evidence limits

The deterministic profile is named `DMG-CPU-B` and skips boot at 0x0100. The
CPU handoff values for this fixture are A=01, F=B0, B=00, C=13, D=00, E=D8,
H=01, L=4D, PC=0100, SP=FFFE. The nonzero header checksum selects F=B0 under the
profile rule. DIV=AB and STAT=85 are recorded as DMG/MGB handoff values, but
this tracer does not implement I/O behavior. WRAM/HRAM are hardware-volatile;
zero fill is an emulator policy, not a hardware claim. The implementation
executes documented legal base and CB instructions, interrupt entry and delay,
HALT/HALT-bug, STOP/wake, reset, WRAM/echo/HRAM and IE/IF behavior. The
ROM-only profile rejects cartridge RAM and does not emulate a responding
device in 0xA000–0xBFFF. Guest reads from that absent window stop as unsupported before instruction
mutation; side-effect-free peek returns 0xFF outside exposed RAM. The electrical
value without a responding device is unspecified and is not a qualified claim. DIV/TAC timer increments
use selected divider falling edges, including the tested reset-edge and reload
collision behavior. Disconnected internal serial shifts in high bits;
external-clock transfers wait for supplied edges. Unqualified active serial
register overlap stops as unsupported. These are scoped bootless profile
results, not physical hardware replication. The applicable CPU handoff values
follow [Pan Docs: Power Up Sequence](https://raw.githubusercontent.com/gbdev/pandocs/master/src/Power_Up_Sequence.md).

The tracer provenance and digest are in
[fixtures/tracer/manifest.json](fixtures/tracer/manifest.json). The three
eligible Mooneye fixtures cover one CPU case (`daa`) and two timer cases
(`tim00`, `tim00_div_trigger`). Their exact source revision, source closure,
MIT notice, replacement-asset notice, builder pin, digests, boot/model scope,
result protocol and finite per-case budgets are documented in
[fixtures/mooneye/manifest.json](fixtures/mooneye/manifest.json) and
[fixtures/mooneye/SOURCES.md](fixtures/mooneye/SOURCES.md). The strict runner
keeps the fixed denominator at three and fails if any case is missing,
unsupported, times out or fails its register protocol. Runner outcomes remain
separate as `pass`, `fail`, `timeout` and `unsupported`; receipts record the
fixture and manifest digests, immutable Mooneye source revision/tree and test
path, report-patch and builder identities, original and derived ROM digests,
exact core/runner revision, profile, boot mode, callback and `LD B,B` result
locations, consumed ticks, finite budget, eligible/executed counts and recent
bounded diagnostics. A pass requires the source-qualified callback followed by
the exact symbol-addressed `LD B,B` result breakpoint with the expected
registers; matching values at another instruction cannot pass.

The checked-in candidates are derived headless reporting closures. Their patch
removes PPU-only reporting setup while preserving the pinned acceptance roots,
assertions, callbacks and result protocol. Candidate receipts report both the
original upstream ROM digest and the derived ROM digest, so their result scope
is explicit. The original upstream-built ROMs still reach an unsupported LY
read before their callback in this PPU-free phase. Candidate success therefore
does not claim that the original ROM bytes ran unchanged or that a physical
Game Boy was tested. The fixed one-CPU/two-timer denominator remains three, and
CPU-01 through CPU-05 remain pending fresh exact-PR-SHA checks and independent
Phase 2 verification.
`mooneye_required_suite` and the per-case CTests run offline against the
checked-in derived bytes. Fixture reproduction runs separately with pinned
RGBDS/WLA-DX sources and reports original-ROM diagnostics alongside exact
candidate byte comparison. Ordinary core tests remain offline.

## Continuous integration and fixture reproduction

Pull requests run `native-linux-x64` on Ubuntu 22.04, `native-macos-arm64` on
macOS 14, and `native-windows-x64` on Windows Server 2022. Each lane installs
the package and checks the exact required CTest inventory, including the
installed runner and external C/C++ consumers of the timestamped API.
`linux-asan-ubsan` runs the core suite with AddressSanitizer and
UndefinedBehaviorSanitizer. `cmake-floor-3.25.3`
downloads the official Linux x64 archive, verifies its published SHA-256, and
checks configure, build, test, install, relocation, and consumer use. The
`required-native` aggregate fails if any required evidence job is missing,
skipped, failed, or timed out. The separate `fixture-repro` workflow rebuilds
the original tracer, retains diagnostics for the immutable upstream Mooneye
ROMs, and compares the derived candidates on pull requests, pushes, and manual
dispatch. Its network and assembler preparation stay outside ordinary test
jobs. Run `bash tests/scripts/verify-phase2-hosted.sh` to require completed,
successful CI and fixture-reproduction jobs plus all required PR contexts at
the exact open-PR head SHA.

### Pull requests and preview packages

Push a branch to this repository (or a fork) and open a pull request against
`main`. For a write-enabled clone, the command sequence is:

```sh
git switch -c feature/my-change
git push -u origin feature/my-change
gh pr create --base main
gh pr checks --required
```

The required contexts include `required-native` and
`preview-package-smoke`; repository branch protection is the source of truth
for the active list. Hosted Phase 2 checks and artifacts must be inspected for
the exact reviewed source SHA before the phase can be verified. Once the exact
PR revision passes the required native gate, the preview workflow tests the
installed package on Linux x64 and macOS arm64. Download the named
`preview-linux-x64` or `preview-macos-arm64` artifact
from that PR's `preview-package-smoke` Actions run. No Windows preview package
is published.

These are temporary, run-scoped artifacts, not release archives. Each includes
the extracted-and-smoked package, a source SHA and package SHA-256 sidecar, the
smoke result, capability limits, and the configured 14-day retention. GitHub's
artifact API reports each run's actual `expires_at`; expiry belongs to that run
and does not promise durable availability.

The earlier Phase 1 implementation sample below was verified from PR #1 at source
revision `8396096ad17500974b30657af91fd2ef9ad51237`. That historical CI run,
fixture-reproduction run, required contexts, both artifacts, and downloaded
package bytes matched that exact SHA. It is not Phase 2 evidence. See the
[PR](https://github.com/szTheory/gabbaboy/pull/1)
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
