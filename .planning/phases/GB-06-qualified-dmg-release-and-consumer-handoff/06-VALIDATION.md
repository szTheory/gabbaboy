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

Task and plan IDs are assigned after this draft is created. Replace these requirement-level rows with exact task IDs, waves, and threat references once the plans exist.

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command / Evidence | Existing Coverage | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-----------------------------|-------------------|--------|
| Pending plan assignment | Pending | Pending | SHIP-01 | Assigned in plan | Relocated C/C++ consumers resolve only GabbaBoy::core without SDL/private build paths | Native package integration | Native CI installed-package inventory and relocated C/C++ consumers on Ubuntu 22.04 x64, macOS 14 arm64, and Windows 2022 x64; final archive smoke for each published core asset | Existing native matrix already runs installed/relocated package consumers; verify whether a Windows archive is published | Pending |
| Pending plan assignment | Pending | Pending | SHIP-02 | Assigned in plan | Safe extraction and legal fixture path; exact packaged bytes exercise fresh-process save continuation | macOS package integration | Extend/qualify tests/scripts/verify-phase3-player.sh against the downloaded final macOS archive; require load, input, frame, PCM, save, exit, and reopen evidence | Existing extracted SDL package verifier and legal fixtures | Pending |
| Pending plan assignment | Pending | Pending | SHIP-03 | Assigned in plan | Version, source SHA, fixture/corpus identity, digest, notices, and trust claims agree with the final asset | Release workflow integration | Release receipt/manifest verifier plus downloaded-asset digest comparison and final-byte package smoke | Existing package receipt and digest checks; release flow is new | Pending |
| Pending plan assignment | Pending | Pending | SHIP-04 | Assigned in plan | Example respects caller ownership and host-managed battery operations; docs make the live-host boundary clear | Installed consumer and documentation checks | Compile/run the new C example outside source/build against relocated GabbaBoy::core; run documented structural/claim checks | Existing C and C++ consumer programs and public API docs | Pending |
| Pending plan assignment | Pending | Pending | SHIP-05 | Assigned in plan | Support claims disclose model, corpus, denominator, failures, exclusions, and known issues | Ledger validation | Validate the versioned support ledger against exact source SHA and fixture/corpus manifests; reject missing, stale, or inconsistent fields | Existing corpus and fixture manifests; ledger validator is new | Pending |
| Pending plan assignment | Pending | Pending | SHIP-06 | Assigned in plan | Trace-on/off performance evidence preserves output digest and reports environment, samples, memory scope, and uncertainty | Reproducibility/measurement | Repeat the fixed legal workload and compare receipts/digests; record raw samples and variance before proposing budgets | Existing audio measurement receipt; phase-wide core receipt is new | Pending |
| Pending plan assignment | Pending | Pending | SHIP-07 | Assigned in plan | Loader, battery, and API inputs have explicit size/work bounds and failed operations are atomic | Sanitizer regression and bounded fuzz | Run deterministic regression inventory under applicable ASan/UBSan; separately run any Clang libFuzzer target with explicit max length, time, memory, and jobs | Existing bounded battery API fuzz regression; loader coverage/fuzz target additions are new | Pending |
| Pending plan assignment | Pending | Pending | SHIP-08 | Assigned in plan | Publication fails closed on stale/missing/skipped/cancelled/timed-out checks or untrusted event paths | Hosted workflow integration | Inspect exact PR head SHA, event, required contexts, conclusion, and merge eligibility; exercise release trigger and failure paths on the target repository | Existing required PR contexts and package workflows; release-specific exercise is new | Pending |

## Wave 0 Requirements

- Define a release receipt/manifest schema and verifier tying version, tag, source SHA, toolchain, fixture/corpus identity, archive SHA-256, notices, and downloaded-byte smoke to one candidate.
- Recheck the target repository’s required checks, bot-token behavior, merge eligibility, release credentials, and release trigger on the exact candidate revision.
- Add or extend the final macOS package smoke to test load/input/video/audio/save/exit/reopen on the downloaded release archive.
- Confirm whether Phase 6 publishes a Windows core archive; if so, qualify its exact downloaded bytes. Native Windows installed-consumer CI already exists.
- Add the Playstead-oriented relocated C example and verify it from outside the source/build tree.
- Add a versioned support ledger and a structural check against corpus/fixture identity.
- Add a fixed core measurement receipt for speed, memory/allocation, and trace/no-trace digest pairing; record variance before any budget.
- Add bounded loader and stateful battery/API fuzz coverage only where the existing harnesses leave a concrete gap; keep compiler-integrated fuzzing optional when the matching runtime is unavailable.

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
