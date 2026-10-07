---
phase: GB-02-dmg-cpu-bus-and-time
verified: 2026-10-07T12:39:59Z
status: passed
score: 5/5 roadmap truths verified
covered_files:
  - .planning/phases/GB-02-dmg-cpu-bus-and-time/02-01-PLAN.md
  - .planning/phases/GB-02-dmg-cpu-bus-and-time/02-01-SUMMARY.md
  - .planning/phases/GB-02-dmg-cpu-bus-and-time/02-02-PLAN.md
  - .planning/phases/GB-02-dmg-cpu-bus-and-time/02-02-SUMMARY.md
  - .planning/phases/GB-02-dmg-cpu-bus-and-time/02-03-PLAN.md
  - .planning/phases/GB-02-dmg-cpu-bus-and-time/02-03-SUMMARY.md
  - .planning/phases/GB-02-dmg-cpu-bus-and-time/02-04-PLAN.md
  - .planning/phases/GB-02-dmg-cpu-bus-and-time/02-04-SUMMARY.md
  - .planning/phases/GB-02-dmg-cpu-bus-and-time/02-05-PLAN.md
  - .planning/phases/GB-02-dmg-cpu-bus-and-time/02-05-SUMMARY.md
  - .planning/phases/GB-02-dmg-cpu-bus-and-time/02-06-PLAN.md
  - .planning/phases/GB-02-dmg-cpu-bus-and-time/02-06-SUMMARY.md
  - .planning/phases/GB-02-dmg-cpu-bus-and-time/02-07-PLAN.md
  - .planning/phases/GB-02-dmg-cpu-bus-and-time/02-07-SUMMARY.md
  - .planning/phases/GB-02-dmg-cpu-bus-and-time/02-08-PLAN.md
  - .planning/phases/GB-02-dmg-cpu-bus-and-time/02-08-SUMMARY.md
  - .planning/phases/GB-02-dmg-cpu-bus-and-time/02-09-PLAN.md
  - .planning/phases/GB-02-dmg-cpu-bus-and-time/02-09-SUMMARY.md
  - .planning/phases/GB-02-dmg-cpu-bus-and-time/02-10-PLAN.md
  - .planning/phases/GB-02-dmg-cpu-bus-and-time/02-10-SUMMARY.md
  - .planning/phases/GB-02-dmg-cpu-bus-and-time/02-11-PLAN.md
  - .planning/phases/GB-02-dmg-cpu-bus-and-time/02-11-SUMMARY.md
  - .planning/phases/GB-02-dmg-cpu-bus-and-time/02-12-PLAN.md
  - .planning/phases/GB-02-dmg-cpu-bus-and-time/02-12-SUMMARY.md
  - .planning/phases/GB-02-dmg-cpu-bus-and-time/02-13-PLAN.md
  - .planning/phases/GB-02-dmg-cpu-bus-and-time/02-13-SUMMARY.md
  - .planning/phases/GB-02-dmg-cpu-bus-and-time/02-14-PLAN.md
  - .planning/phases/GB-02-dmg-cpu-bus-and-time/02-14-SUMMARY.md
  - .planning/phases/GB-02-dmg-cpu-bus-and-time/02-15-PLAN.md
  - .planning/phases/GB-02-dmg-cpu-bus-and-time/02-15-SUMMARY.md
  - .planning/phases/GB-02-dmg-cpu-bus-and-time/02-16-PLAN.md
  - .planning/phases/GB-02-dmg-cpu-bus-and-time/02-16-SUMMARY.md
  - .planning/phases/GB-02-dmg-cpu-bus-and-time/02-17-PLAN.md
  - .planning/phases/GB-02-dmg-cpu-bus-and-time/02-17-SUMMARY.md
  - .planning/phases/GB-02-dmg-cpu-bus-and-time/02-18-PLAN.md
  - .planning/phases/GB-02-dmg-cpu-bus-and-time/02-18-SUMMARY.md
  - tests/CMakeLists.txt
  - tests/expected-tests.txt
  - tests/test_cpu.c
covered_digest: "v3:sha256:594ba565963913973e72ff4e20cdc9406bde18b1e7279dc54f35d557fb0fc59a"
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: gaps_found
  previous_score: 4/5
  gaps_closed:
    - "D-01: Every documented legal unprefixed base opcode now has value-level semantic coverage, with branch, address, arithmetic-boundary, and timed-bus assertions."
  gaps_remaining: []
  regressions: []
verification_history:
  - verified: 2026-10-07T08:12:48Z
    status: gaps_found
    score: 4/5
    gap: "D-01 base-opcode matrix lacked sufficiently broad value-level semantic assertions."
  - verified: 2026-10-07T08:12:48Z
    status: gaps_found
    score: 1/5
    gaps_closed_later:
      - "CR-01 through CR-05, Windows manifest distinctions, and deterministic fixture-byte qualification."
  - verified: 2026-10-07T12:39:59Z
    status: passed
    score: 5/5
    gap_closed: "D-01/CPU-01 base-opcode semantic evidence."
---

# Phase 2: DMG CPU, Bus, and Time Verification Report

**Phase Goal:** As a core integrator, I want to run the declared DMG instruction and timing behavior deterministically, so that I can reproduce diagnostic failures.
**Verified:** 2026-10-07T12:39:59Z
**Implementation revision:** `cf28e90270be24d9528bfa8a1e4055a2b8485989`; current branch HEAD `8891b4d9965338954ec6cfe0133270761e9b34dc` adds only the audited security document.
**Status:** passed
**Re-verification:** Yes — after closure of the prior D-01/CPU-01 gap by Plan 02-18.

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|---|---|---|
| 1 | Declared DMG profile produces expected base/CB instruction, flag, arithmetic, address and bus-timing results, with explicit illegal-opcode behavior. (CPU-01) | ✓ VERIFIED | The new legal-base matrix checks full register/flag/SP/PC post-state for every documented legal base encoding against a separately authored expected-state function. Additional tests enumerate taken and untaken JR/JP/CALL/RET conditions, arithmetic/carry boundaries, address effects, stack bytes, and timed observer values/order/half-dot offsets. Eleven unused opcodes remain separate lockup cases. All five focused CPU base tests passed; see test-quality audit below. |
| 2 | Model-applicable cases observe expected interrupt entry, EI delay, HALT/HALT-bug, STOP, reset and deterministic post-boot results. (CPU-02) | ✓ VERIFIED | Prior gap closure regressions cover checksum-selected F on load/reset, RET/RETI phase timing, consecutive EI, interrupt ordering/priority, HALT/HALT-bug, STOP, lockup persistence and reset. These passed the recorded full local inventory and exact-revision hosted gates. |
| 3 | Guests observe declared mapping, divider/timer edges/reload races, and disconnected serial at timed boundaries. (CPU-03) | ✓ VERIFIED | Direct bus, timer selector/write/reload/collision, and disconnected serial regressions assert guest-visible values and timed boundaries. Strict corpus includes two timer cases and passes. |
| 4 | Equal timestamped inputs/time yield equal supported state/output across partitions; HALT/STOP/lockup/output exhaustion remain bounded. (CPU-04) | ✓ VERIFIED | Queue order/atomicity, partition snapshots, deadline, HALT timer partition, diagnostic chronology, output-capacity canary, and distinct stop results are covered by named tests and the complete local inventory. |
| 5 | Headless runs report pass/fail/timeout/unsupported against a pinned eligible CPU/timer corpus with model/boot/protocol identity and replay evidence. (CPU-05) | ✓ VERIFIED | The fixed denominator is three derived reporting closures (one CPU, two timer); runner verifies callback then exact result PC, source/tool/patch/ROM digests, bootless DMG-CPU-B profile, finite budget, and bounded diagnostics. The exact hosted fixture run passes. Original upstream PPU-dependent reporting paths remain excluded and are not described as hardware-qualified. |

**Score:** 5/5 roadmap truths verified; behavior-unverified: 0.

### Re-verification of Prior Gaps and Plan Must-Haves

The earlier verification first reported seven implementation/provenance gaps at 1/5. Those were closed and carried into the 2026-10-07 08:12 verification, which scored 4/5 and isolated D-01. Plan 02-18 closes that remaining gap. The original 1/5 and subsequent 4/5 outcomes are retained in `verification_history` above.

| Prior plan truth | Status | Evidence |
|---|---|---|
| D-01: Legal base instruction registers, flags, addresses, branch paths and timed bus phases are tested. | ✓ VERIFIED | `base_matrix` loops over all 256 encodings, separately classifies the eleven illegal bytes, and checks all architectural registers, flags, SP, and PC for every legal opcode. `base_conditional_paths` covers taken/untaken paths for all conditions in JR/JP/CALL/RET. `base_arithmetic_edges` covers ADC/SBC/CP, DAA, INC/DEC, 16-bit and signed-SP arithmetic, and rotate boundaries. `base_address_effects` checks indirect, HL post-update, high-memory, absolute, read-modify-write, stack and bus observer timing/value/order. Expected states are authored in test code and do not read output to populate the oracle. |
| D-02: Unused opcodes lock persistently with PC/opcode until reset. | ✓ VERIFIED | `illegal_lockup` asserts zero consumed time, exact PC/opcode, persistence on a second run, and reset behavior; the matrix keeps illegal cases distinct. |
| D-03: ROM-only WRAM/echo/HRAM and absent-cartridge behavior are explicit. | ✓ VERIFIED | Bus guest and unsupported-read tests assert mapping and bounded unsupported behavior; peek scope is documented. |
| D-04: Divider falling edges, writes, reload and collision rules are tested. | ✓ VERIFIED | Timer selector, DIV/TAC writes, overflow/reload and TIMA/TMA collision cases assert exact state/timing. |
| D-05: Disconnected serial behavior is explicit; host runner interprets LD B,B. | ✓ VERIFIED | Serial regressions and runner protocol tests distinguish core instruction execution from host callback/result interpretation. |
| D-06: Full operation/deadline preflight preserves state and consumes no time on incomplete operations. | ✓ VERIFIED | Bus, stack, CB, event, timer and diagnostic-capacity boundary tests compare state snapshots/canaries and zero-consumption outcomes. |
| D-07: Timestamped queue validation and partition equality hold. | ✓ VERIFIED | Equal-time order, atomic rejection and partition snapshot tests assert resulting state/output. |
| D-08: Lockup, HALT/STOP, unsupported bus and output-full results are bounded/distinct. | ✓ VERIFIED | Named public result and output-capacity cases assert stop reasons and caller-bound behavior. |
| D-09/D-10: Fixed eligible corpus is reviewed and pinned candidate fixtures reproduce exactly. | ✓ VERIFIED | Eligibility/rights/source provenance, callback protocol, immutable original blobs, candidate digests, and local/hosted byte identity are recorded. The original PPU-dependent ROM result path remains explicitly ineligible. |
| D-11/D-12 and Plans 02-16/02-17: Runner statuses, denominator, relocated consumers, exact-host evidence, fixture binding. | ✓ VERIFIED | Runner negative controls, strict denominator, installed C/C++ consumers and hosted artifact binding pass. The prior verification documents the evidence and limitations; a quick regression check found the relevant artifacts still present. |

### Required Artifacts

| Artifact | Expected | Status | Details |
|---|---|---|---|
| `src/core/gabbaboy.c`, `include/gabbaboy/gabbaboy.h` | CPU, bus, timer, serial, interrupt, event behavior and public bounded contract | ✓ VERIFIED | Substantive core is wired through `gbb_run`; existing direct regressions and consumer tests exercise it. Plan 02-18 makes no core/API changes. |
| `tests/test_cpu.c` | CPU semantic, flag, address and timing evidence | ✓ VERIFIED | New cases are registered in CTest and dispatch through `main`; their implementations use fixed test programs and expected values. Focused tests passed 5/5. |
| `tests/CMakeLists.txt`, `tests/expected-tests.txt` | Registered and fail-closed required inventory | ✓ VERIFIED | Three new named tests are registered and required; saved full-suite report verifies 104 executed with zero skipped. |
| Runner, manifest, fixture provenance and CI scripts | Strict source-qualified corpus and exact-revision evidence | ✓ VERIFIED | Prior artifacts remain present and tied to passing hosted CI and fixture runs for the implementation SHA. |
| Relocated installed package and C/C++ consumers | Public package adoption path | ✓ VERIFIED | Recorded installed verification passed 109/109 after fresh relocation. |

### Key Link Verification

| From | To | Via | Status | Details |
|---|---|---|---|---|
| `gbb_run` | Timed CPU/bus/device helpers | Preflight, timed access and device advancement | ✓ WIRED | Direct guest bus/timer/serial regressions exercise the shared run path. |
| Base/CB decoder | Execution, trace and timing | Decode metadata and instruction dispatch | ✓ WIRED | The legal base matrix asserts each encoding's resulting state and cost; CB matrix asserts all 256 CB operations. |
| Test executable cases | CTest and expected inventory | CMake registration, argv dispatch, inventory names | ✓ WIRED | Each of the five base semantic case names is present in registration, dispatch, and inventory; all five pass. |
| Candidate source/patch/tool | Checked-in ROM bytes | Pinned recipe, hosted qualification and digest lock | ✓ WIRED | Local and hosted candidate byte arrays were compared at the qualification head, and the exact current PR fixture run passed. |
| Manifest | Strict runner result | Fixed cases and callback/result protocol | ✓ WIRED | Runner emits pass only after the callback and exact result breakpoint; fixed eligible denominator remains 3. |
| Installed target | C/C++ external consumers | Relocated configure/link/run | ✓ WIRED | Fresh relocated installation and both consumers pass. |

### Data-Flow Trace

| Artifact | Data | Source | Real data | Status |
|---|---|---|---|---|
| Test vectors → core | Opcode bytes, operands and initial guest state | Test-authored finite ROM programs | Yes; deterministic guest execution | ✓ FLOWING |
| Core → semantic assertions | Registers, flags, SP, PC, bus events | Public trace records and test observer after execution | Yes; asserted against separately authored expected values | ✓ FLOWING |
| Runner → receipt | ROM execution status, callback/result PC, time and diagnostics | Digest-checked fixture bytes through public core | Yes | ✓ FLOWING |
| Installed consumers → package | Public API behavior | Fresh relocated install | Yes | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|---|---|---|---|
| New base semantic cases | `ctest --test-dir build --output-on-failure --no-tests=error -R '^cpu_base_(matrix|conditional_paths|arithmetic_edges|address_effects|semantic_tracer)$'` | 5/5 passed | ✓ PASS |
| Exact saved core inventory | `bash .github/scripts/verify-test-inventory.sh build/phase2-ctest.xml tests/expected-tests.txt --core-only` | 104 executed; none skipped | ✓ PASS |
| Relocated installed inventory | `bash tests/scripts/verify-phase2-installed.sh` (recorded Plan 02-18 evidence) | 109/109 passed, including installed C/C++ consumers | ✓ PASS |
| Exact hosted CI revision | `bash tests/scripts/verify-phase2-hosted.sh` (recorded Plan 02-18 evidence) | Implementation SHA `cf28e90270be24d9528bfa8a1e4055a2b8485989`; CI run 37620710587 passed | ✓ PASS |
| Exact hosted fixture reproduction | Included in exact hosted gate | Run 37620710600 passed | ✓ PASS |

Hosted evidence is attributed to the exact implementation SHA; the current branch head `8891b4d9965338954ec6cfe0133270761e9b34dc` adds only the audited security document, so it does not alter the tested source revision. The temporary upstream CMake download failure was rerun successfully on the same SHA.

### Probe Execution

The candidate protocol probe was declared by earlier active plans and is recorded as independently run by the previous verification. Plan 02-18 adds no probe-based acceptance.

| Probe | Command | Result | Status |
|---|---|---|---|
| Candidate protocol/PPU independence | `bash tests/scripts/probe-mooneye-candidate.sh` | Three positive cases plus induced failure; callback/result ordering correct; zero PPU access | PASS |
| Callback-order negative control | `bash tests/scripts/probe-mooneye-candidate.sh --self-test-order` | Accepts valid order and rejects callback-after-result | PASS |

### Test Quality Audit

| Test File / Area | Requirement | Active | Assertion and oracle review | Verdict |
|---|---|---:|---|---|
| `tests/test_cpu.c:base_matrix` | CPU-01 / D-01 | Yes | Iterates every byte, separates all eleven illegal encodings, and compares legal instruction post-state to expected values. The expected-state helper derives values from test setup and opcode contract, not from the observed trace. | Adequate |
| `base_conditional_paths` | CPU-01 / D-01 | Yes | Exercises both outcomes for NZ/Z/NC/C in JR, JP, CALL and RET; checks flags, PC, SP, path cost, stack bytes and timed accesses. | Adequate |
| `base_arithmetic_edges` | CPU-01 / D-01 | Yes | Independent expected vectors cover ADC/SBC carry and half-carry/borrow, CP, DAA, INC/DEC, ADD HL, signed SP offsets and rotations. | Adequate |
| `base_address_effects` | CPU-01 / D-01 | Yes | Checks indirect loads/stores, HL post-increment/decrement, high-memory/absolute access, read-modify-write, exact bus address/direction/value/order/time, and memory result. | Adequate |
| `illegal_lockup` and base matrix holes | CPU-01 / D-02 | Yes | Eleven illegal bytes remain distinct from legal semantic expectations; lockup persistence/reset is asserted. | Adequate |
| Existing control, bus, timer, serial, event, runner and CB tests | CPU-02..CPU-05 | Yes | Assertions cover guest-visible state, traces, timing, bounded outcomes, protocol and fixed corpus behavior. | Adequate |

Disconfirmation pass: a test that could pass without proving its named behavior was addressed by checking the new state oracle against authored data and verifying the executable is both CTest-registered and included in the expected inventory. The error/negative paths remain covered by illegal-opcode lockup, branch untaken paths, induced runner failure, malformed manifest/digest controls, unsupported bus behavior, and bounded-capacity cases. No unresolved blocker was found.

### Requirements Coverage

| Requirement | Source plans | Description | Status | Evidence |
|---|---|---|---|---|
| CPU-01 | 02-02, 02-03, 02-07, 02-09, 02-10, 02-16, 02-17, 02-18 | Base/CB semantics, flags, addresses, timing, explicit illegal behavior | SATISFIED | All legal base opcode state assertions, CB value matrix, branch/address/timed-bus cases, and eleven illegal lockups are covered; full/local and exact hosted checks pass. |
| CPU-02 | 02-04, 02-06, 02-09, 02-10, 02-11, 02-16 | Interrupts, EI, HALT/STOP, reset and bootless profile | SATISFIED | Focused model-applicable regressions pass in the verified inventory. |
| CPU-03 | 02-01, 02-05, 02-06, 02-07, 02-09, 02-11, 02-14, 02-16 | Memory map, timer races and disconnected serial | SATISFIED | Direct bus/device tests and two eligible timer diagnostics pass. |
| CPU-04 | 02-01, 02-02, 02-04, 02-06, 02-08, 02-09, 02-10, 02-11, 02-16 | Partition equivalence and bounded outcomes | SATISFIED | Partition comparisons and distinct bounded-result tests pass. |
| CPU-05 | 02-07, 02-08, 02-09, 02-14, 02-16, 02-17 | Fixed eligible corpus, honest statuses and replay evidence | SATISFIED | Three-case fixed denominator, protocol receipts, fixture provenance, exact digest identity, and hosted fixture reproduction pass. |

No orphaned Phase 2 requirements were found: ROADMAP.md maps CPU-01 through CPU-05 and all five are declared by the phase plans and covered above.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|---|---:|---|---|---|
| None | — | No unreferenced TBD/FIXME/XXX markers, placeholder implementations, empty implementations, or hardcoded empty user-facing data were found in the Plan 02-18 changed test files. | — | No anti-pattern gap. |

### Human Verification Required

None. Phase 2 is automated core and diagnostic behavior. No physical Game Boy hardware run is claimed; the project records that limitation explicitly, and hardware interaction is not a roadmap criterion for this phase.

### Gaps Summary

No remaining gaps. Plan 02-18 closes the sole D-01/CPU-01 evidence gap with independent semantic assertions for the legal unprefixed base instruction set, explicit conditional outcomes, boundary arithmetic, address effects and timed bus accesses. The prior CPU-02 through CPU-05 truths remain verified. Local inventories, relocated consumers, and exact-SHA hosted CI and fixture-reproduction checks pass. The scope remains the declared bootless DMG profile and fixed derived diagnostic corpus; it does not establish physical hardware qualification or general game compatibility.

---

_Verified: 2026-10-07T12:39:59Z_
_Verifier: the agent (gsd-verifier)_
