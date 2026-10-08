---
phase: "GB-06"
slug: "qualified-dmg-release-and-consumer-handoff"
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-10-08"
---

# Phase GB-06 — Validation Strategy

> Draft validation contract for the Phase 6 planning and execution work. No Phase 6 checks have been run.

## Test Infrastructure

| Property | Value |
|----------|-------|
| Framework | Existing CMake/CTest C17 suite, package/player verification scripts, and hosted GitHub Actions checks |
| Config files | CMakePresets.json, tests/CMakeLists.txt, tests/expected-tests.txt, .github/workflows/ci.yml, .github/workflows/preview.yml, .github/workflows/fixture-repro.yml |
| Quick baseline | cmake --preset phase1 -DGABBABOY_BUILD_PLAYER=OFF && cmake --build --preset phase1 --parallel 2 && ctest --preset phase1 --output-on-failure --no-tests=error |
| Existing package/player evidence | bash tests/scripts/verify-phase3-player.sh |
| Existing audio receipt | bash tests/scripts/measure-audio-playback.sh |
| Phase 6 runtime estimate | Not measured. Keep focused CTest feedback under 60 seconds; record package, fuzz, hosted workflow, and measurement durations separately. |

The existing commands are starting points, not evidence that Phase 6 requirements have passed. Plans must add exact focused commands and observable failure conditions for every new validation task.

## Sampling Rate

- After each task commit, run the task’s focused automated check when its target exists.
- After each plan wave, run affected CTest inventory and package/fixture gates.
- Before phase verification, run the complete applicable local inventory and exact-revision hosted checks, qualify the final downloaded release bytes, and reconcile each public claim with an evidence receipt.
- Keep fuzzing and fixed-workload measurement bounded. Do not set performance budgets before repeated samples establish variance.
- No physical DMG, perceptual audio/video, real-device hotplug, live Playstead integration, signing credential, or notarization result is implied by software-path checks.

## Requirement Validation Map

The planned checks below remain pending. Plan IDs, waves, and threat references match the six Phase 6 plans; no Phase 6 implementation check has run.

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command / Evidence | Existing Coverage | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-----------------------------|-------------------|--------|
| 06-01-01 | 01 | 1 | SHIP-01, SHIP-03, SHIP-08 | T-06-01/02/03 | Trusted tag and exact downloaded Linux archive reach relocated C/C++ smoke | Release tracer | `bash tests/scripts/verify-release-candidate.sh --self-test`; hosted draft download/consumer receipt | Existing preview relocation verifier | pending |
| 06-01-02 | 01 | 1 | SHIP-03, SHIP-08 | T-06-01/03 | Version PR and v tag share CMake version and exact source; required PR checks cannot be bypassed | Workflow contract | Candidate self-test plus target repository bot PR evidence | Existing exact-head PR verifier | pending |
| 06-05-01 | 05 | 1 | SHIP-07 | T-06-11/12 | Loader/battery/API boundary failure remains atomic and bounded | ASan/UBSan regression | `cmake --preset phase1-asan && cmake --build --preset phase1-asan && ctest --preset phase1-asan --output-on-failure --no-tests=error -R '^(battery_api_fuzz|loader_)'` | Existing loader/battery inventory | pending |
| 06-05-02 | 05 | 1 | SHIP-07 | T-06-11/12 | Fuzz input/work/time/memory caps and replay are explicit | Compiler-integrated fuzz | `bash tests/scripts/run-bounded-fuzz.sh --self-test`; available Clang libFuzzer lane | Existing battery deterministic seed | pending |
| 06-02-01 | 02 | 2 | SHIP-01, SHIP-03 | T-06-04/05 | Three downloaded core archives resolve only public GabbaBoy::core on tested matrix | Package integration | `ctest --preset phase1 --output-on-failure --no-tests=error -R '^preview_package_smoke$'`; hosted Linux/macOS/Windows asset receipts | Existing native Windows C/C++ relocated CI | pending |
| 06-02-02 | 02 | 2 | SHIP-02, SHIP-03 | T-06-05/06 | Exact macOS player bytes pass legal load/input/frame/PCM/save/exit/reopen | Player integration | `bash tests/scripts/verify-phase3-player.sh`; downloaded asset receipt | Existing pinned SDL package verifier | pending |
| 06-03-01 | 03 | 3 | SHIP-01, SHIP-04 | T-06-07/08 | Native C example uses relocated public API and host-owned battery | Consumer integration | `ctest --preset phase1 --output-on-failure --no-tests=error -R '^preview_package_smoke$'` | Existing C/C++ relocated smoke | pending |
| 06-03-02 | 03 | 3 | SHIP-04 | T-06-07/08 | Docs match example, save/API behavior and Playstead boundary | Documentation + consumer | Relocated package smoke and documented build invocation | Existing README and cartridge/save docs | pending |
| 06-04-01 | 04 | 3 | SHIP-05, SHIP-03 | T-06-09 | Ledger binds scope, denominator and exclusions to exact source/corpus | Ledger validation | `python3 tests/scripts/verify-support-ledger.py --self-test` | Existing fixture/corpus manifests | pending |
| 06-04-02 | 04 | 3 | SHIP-06, SHIP-03 | T-06-10 | Fixed workload trace pair has equal digest and measured variance | Baseline receipt | `bash tests/scripts/measure-release-baseline.sh --self-test` | Existing audio measurement receipt | pending |
| 06-06-01 | 06 | 4 | SHIP-08, SHIP-03 | T-06-13 | Exact bot PR head has all live required contexts and merge eligibility | Hosted gate | `bash .github/scripts/verify-release-gates.sh --self-test`; live `gh` evidence | Existing PR gate scripts | pending |
| 06-06-02 | 06 | 4 | SHIP-01–SHIP-08 | T-06-13/14/15 | Exact qualified bytes and truthful notices/trust/report sidecars are published | Final release | Candidate and gate self-tests; published release API/download/hash and asset smoke | Draft release path planned in 06-01 | pending |

## Spec-less Edge Probe Assumptions

The deterministic probe supplied 18 unresolved items and no resolved predicates. They remain explicit planning assumptions until the named tasks exercise them; no unclassified item is silently counted as covered. SHIP-01 and SHIP-03 are unclassified and require the package/release verifier to inspect malformed, absent, and contradictory identity data. SHIP-02 idempotency and concurrency require unchanged bytes on retry and an unpublished draft after interruption. SHIP-04 idempotency and concurrency require repeatable example runs and safe host battery replacement. SHIP-05 adjacency, empty, encoding, and ordering require duplicate/equal case handling, nonempty denominator, valid UTF-8, and stable case order. SHIP-06 boundary and precision require raw sample count/overflow/clock-precision handling. SHIP-07 boundary, precision, and concurrency require exact input/work/memory caps and deterministic finding replay. SHIP-08 adjacency, empty, and ordering require exact check-set equality, rejection of zero/missing checks, and current-head ordering. These assumptions are specified in tasks 06-01-01, 06-02-02, 06-03-01, 06-04-01/02, 06-05-01/02, and 06-06-01 respectively; execution must retain negative evidence and resolve the probe before claiming phase completion.

The prohibition recall pass surfaced product-specific claim boundaries: do not portray the three-case corpus as game compatibility, software dummy devices as physical/perceptual proof, an unsigned player as Apple-verified, a preview Actions artifact as the release, or a future Playstead seam as live integration. These are carried as reviewable negative criteria in the support, player, release, and adopter tasks. Generic archive traversal, source authorization, and secret handling route to the STRIDE threat register rather than a fabricated prohibition check descriptor.

## Wave 0 Requirements

- Define a release receipt/manifest schema and verifier tying version, tag, source SHA, toolchain, fixture/corpus identity, archive SHA-256, notices, and downloaded-byte smoke to one candidate.
- Recheck the target repository’s required checks, bot-token behavior, merge eligibility, release credentials, and release trigger on the exact candidate revision.
- Add or extend the final macOS package smoke to test load/input/video/audio/save/exit/reopen on the downloaded release archive.
- Qualify the exact downloaded Windows x64 core release archive; native Windows installed-consumer CI already exists, so no duplicate native consumer lane is planned.
- Add the Playstead-oriented relocated C example and verify it from outside the source/build tree.
- Add a versioned support ledger and a structural check against corpus/fixture identity.
- Add a fixed core measurement receipt for speed, memory/allocation, and trace/no-trace digest pairing; record variance before any budget.
- Add bounded loader and stateful battery/API fuzz coverage only where the existing harnesses leave a concrete gap; keep compiler-integrated fuzzing optional when the matching runtime is unavailable.
- Produce the decided GitHub API capability matrix before phase seal; the planner's file-edit scope leaves COVERAGE.md for task 06-06-02.

## Manual-Only / External Evidence

| Behavior | Requirement | Why not established by local automation | Evidence boundary |
|----------|-------------|-------------------------------------------|------------------|
| Developer ID signing/notarization | SHIP-03 | Suitable project credentials and an applicable distributable format are unverified | Claim only after verification of the exact final contents; otherwise record unsigned status and observed launch friction |
| Physical device or perceptual audio/video quality | SHIP-02 | Scripted SDL devices establish software behavior, not physical presentation or perception | Report the existing device/perceptual limitations separately; no such claim is required for this phase’s automated smoke |
| Live Playstead Game Boy adapter | SHIP-04 | Current inspected Playstead adapter uses an external GBA/mGBA process and is not a GabbaBoy GB integration | The native C example documents a future seam only; no live integration pass |

## Validation Sign-Off

- [ ] Every planned task has an automated verifier or a specific Wave 0 dependency.
- [ ] No three consecutive planned tasks lack automated verification.
- [ ] Wave 0 covers all missing validation references.
- [ ] Every executable verification command states an observable failing condition in its plan.
- [ ] Exact candidate SHA, release asset bytes, and public claims are linked by receipts.
- [ ] No manual-only or hardware limitation is presented as a passing automated result.
- [ ] Set nyquist_compliant to true only after the plan map is complete and the validation audit has evidence.

**Status:** Draft. Planning must replace requirement-level rows with plan/task/wave assignments; execution must record actual results before this strategy can be marked validated.
