---
phase: "GB-06"
slug: "qualified-dmg-release-and-consumer-handoff"
status: validated
nyquist_compliant: true
wave_0_complete: true
created: "2026-10-08"
---

# Phase GB-06 — Validation Strategy

> Execution audit: all Phase 6 task rows now have recorded automated evidence. Cross-platform package qualification and publication are tied to the exact frozen `v0.1.0` tag; manual-only hardware, perceptual, signing, and live Playstead claims remain explicitly unqualified.

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

Plan IDs, waves, and threat references match all seven Phase 6 plans. The 14 planned task rows are covered by the recorded local and exact-head hosted evidence.

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command / Evidence | Existing Coverage | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-----------------------------|-------------------|--------|
| 06-01-01 | 01 | 1 | SHIP-01, SHIP-03, SHIP-08 | T-06-01/02/03 | Release-please's one unpublished draft and immediate tag reach downloaded Linux C/C++ smoke | Release tracer | `bash tests/scripts/verify-release-candidate.sh --self-test`; hosted existing-draft download/consumer receipt | Existing preview relocation verifier | covered |
| 06-01-02 | 01 | 1 | SHIP-03, SHIP-08 | T-06-01/03 | Manifest uses draft plus forced tag; same-workflow outputs route candidate; protected merge follows final source | Workflow contract | Candidate self-test; live merge/draft/tag deferred to 06-06-01 | Existing exact-head PR verifier | covered |
| 06-05-01 | 05 | 1 | SHIP-07 | T-06-11/12 | Loader/battery/API boundary failure remains atomic and bounded | ASan/UBSan regression | `cmake --preset phase1-asan && cmake --build --preset phase1-asan && ctest --preset phase1-asan --output-on-failure --no-tests=error -R '^(battery_api_fuzz|loader_)'` | Existing loader/battery inventory | covered |
| 06-05-02 | 05 | 1 | SHIP-07 | T-06-11/12 | Fuzz input/work/time/memory caps and replay are explicit | Compiler-integrated fuzz | `bash tests/scripts/run-bounded-fuzz.sh --self-test`; available Clang libFuzzer lane | Existing battery deterministic seed | covered |
| 06-02-01 | 02 | 2 | SHIP-01, SHIP-03 | T-06-04/05 | Three downloaded core archives resolve only public GabbaBoy::core on tested matrix | Package integration | `ctest --preset phase1 --output-on-failure --no-tests=error -R '^preview_package_smoke$'`; hosted Linux/macOS/Windows asset receipts | Existing native Windows C/C++ relocated CI | covered |
| 06-02-02 | 02 | 2 | SHIP-02, SHIP-03 | T-06-05/06 | Exact macOS player bytes pass legal load/input/frame/PCM/save/exit/reopen | Player integration | `bash tests/scripts/verify-phase3-player.sh`; downloaded asset receipt | Existing pinned SDL package verifier | covered |
| 06-04-01 | 04 | 3 | SHIP-05, SHIP-03 | T-06-09 | Tracked ledger holds stable scope/corpus; separate post-tag sidecar binds tagged ledger blob digest to exact source SHA without self-reference | Ledger and sidecar validation | `python3 tests/scripts/verify-support-ledger.py --self-test`; post-tag sidecar check | Existing fixture/corpus manifests | covered |
| 06-04-02 | 04 | 3 | SHIP-06, SHIP-03 | T-06-10 | Fixed workload trace pair has equal digest and measured variance | Baseline receipt | `bash tests/scripts/measure-release-baseline.sh --self-test` | Existing audio measurement receipt | covered |
| 06-03-01 | 03 | 4 | SHIP-01, SHIP-04 | T-06-07/08 | Native C example uses relocated public API and host-owned battery | Consumer integration | `ctest --preset phase1 --output-on-failure --no-tests=error -R '^preview_package_smoke$'` | Existing C/C++ relocated smoke | covered |
| 06-03-02 | 03 | 4 | SHIP-04 | T-06-07/08 | Docs match example, tracked ledger/release-sidecar relationship, save/API behavior and Playstead boundary | Documentation + consumer | Relocated package smoke and documented build invocation | Existing README and cartridge/save docs | covered |
| 06-07-01 | 07 | 5 | SHIP-03, SHIP-04 | T-06-16 | Tracked release notes, notices and guide are final before tag | Release documentation | Candidate self-test; notice/ledger link validation | Existing fixture manifests | covered |
| 06-07-02 | 07 | 5 | SHIP-08 | T-06-16 | GitHub API coverage decisions include draft creation/status, forced tag and guarded retry before tag | API coverage | Candidate self-test; coverage matrix validation before seal | Existing workflow API calls | covered |
| 06-06-01 | 06 | 6 | SHIP-08, SHIP-03 | T-06-13 | Final bot PR has all live exact-head checks; protected merge yields one unpublished draft/immediate tag; same-workflow outputs route candidate | Hosted gate | `bash .github/scripts/verify-release-gates.sh --self-test`; live `gh` merge/draft/tag/output evidence | Existing PR gate scripts | covered |
| 06-06-02 | 06 | 6 | SHIP-01–SHIP-08 | T-06-13/14/15/17 | Existing draft stays unpublished through downloaded-byte smoke; only then exact qualified bytes and sidecar are published | Final release | Candidate and gate self-tests; release API draft-before/published-after, download/hash, sidecar and asset smoke | Draft release path planned in 06-01 | covered |

## Spec-less Edge Probe Assumptions

The deterministic probe supplied 18 unresolved items and no resolved predicates. The named tasks exercised the applicable cases with negative fixtures, bounded fuzzing, repeatable relocated package/player smokes, exact source/check receipts, and unchanged-byte guarded retries. The final release reconciliation verified the published asset inventory and all digests. SHIP-01 and SHIP-03 are unclassified and require the package/release verifier to inspect malformed, absent, and contradictory identity data. SHIP-02 idempotency and concurrency require unchanged bytes on retry and an unpublished draft after interruption. SHIP-04 idempotency and concurrency require repeatable example runs and safe host battery replacement. SHIP-05 adjacency, empty, encoding, and ordering require duplicate/equal case handling, nonempty denominator, valid UTF-8, and stable case order. SHIP-06 boundary and precision require raw sample count/overflow/clock-precision handling. SHIP-07 boundary, precision, and concurrency require exact input/work/memory caps and deterministic finding replay. SHIP-08 adjacency, empty, and ordering require exact check-set equality, rejection of zero/missing checks, and current-head ordering. These assumptions are specified in tasks 06-01-01, 06-02-02, 06-03-01, 06-04-01/02, 06-05-01/02, and 06-06-01 respectively; execution must retain negative evidence and resolve the probe before claiming phase completion.

The prohibition recall pass surfaced product-specific claim boundaries: do not portray the three-case corpus as game compatibility, software dummy devices as physical/perceptual proof, an unsigned player as Apple-verified, a preview Actions artifact as the release, or a future Playstead seam as live integration. These are carried as reviewable negative criteria in the support, player, release, and adopter tasks. Generic archive traversal, source authorization, and secret handling route to the STRIDE threat register rather than a fabricated prohibition check descriptor.

## Wave 0 Requirements

- Define a release receipt/manifest schema and verifier tying version, tag, source SHA, toolchain, fixture/corpus identity, archive SHA-256, notices, and downloaded-byte smoke to one candidate.
- Recheck required checks, bot-token behavior, merge eligibility and credentials on the exact candidate; require release-please `draft: true` plus `force-tag-creation: true`, same-workflow `release_created`/`tag_name`/`sha` candidate routing and guarded retry of the existing unpublished draft.
- Add or extend the final macOS package smoke to test load/input/video/audio/save/exit/reopen on the downloaded release archive.
- Qualify the exact downloaded Windows x64 core release archive; native Windows installed-consumer CI already exists, so no duplicate native consumer lane is planned.
- Add the Playstead-oriented relocated C example and verify it from outside the source/build tree.
- Add a tracked versioned support ledger for stable scope/corpus facts, plus a post-tag generated release sidecar binding the exact source SHA and tagged ledger blob digest without cyclic hashes.
- Add a fixed core measurement receipt for speed, memory/allocation, and trace/no-trace digest pairing; record variance before any budget.
- Add bounded loader and stateful battery/API fuzz coverage only where the existing harnesses leave a concrete gap; keep compiler-integrated fuzzing optional when the matching runtime is unavailable.
- Produce the decided GitHub API capability matrix in task 06-07-02 before the final release PR/tag; validate it again before phase seal.

## Manual-Only / External Evidence

| Behavior | Requirement | Why not established by local automation | Evidence boundary |
|----------|-------------|-------------------------------------------|------------------|
| Developer ID signing/notarization | SHIP-03 | Suitable project credentials and an applicable distributable format are unverified | Claim only after verification of the exact final contents; otherwise record unsigned status and observed launch friction |
| Physical device or perceptual audio/video quality | SHIP-02 | Scripted SDL devices establish software behavior, not physical presentation or perception | Report the existing device/perceptual limitations separately; no such claim is required for this phase’s automated smoke |
| Live Playstead Game Boy adapter | SHIP-04 | Current inspected Playstead adapter uses an external GBA/mGBA process and is not a GabbaBoy GB integration | The native C example documents a future seam only; no live integration pass |

## Validation Sign-Off

- [x] Every planned task has an automated verifier or a specific Wave 0 dependency.
- [x] No three consecutive planned tasks lack automated verification.
- [x] Wave 0 covers all missing validation references.
- [x] Every executable verification command states an observable failing condition in its plan.
- [x] Exact candidate SHA, release asset bytes, and public claims are linked by receipts.
- [x] No manual-only or hardware limitation is presented as a passing automated result.
- [x] Set nyquist_compliant to true only after the plan map is complete and the validation audit has evidence.

**Status:** Validated. All 14 planned task rows have automated checks or exact hosted evidence. The release is explicitly unsigned/not notarized and limited to the documented software evidence; physical and perceptual qualification and live Playstead integration remain excluded.

## Validation Audit 2026-10-09

| Metric | Count |
|---|---|
| Gaps found | 0 |
| Resolved | 14 |
| Escalated | 0 |
