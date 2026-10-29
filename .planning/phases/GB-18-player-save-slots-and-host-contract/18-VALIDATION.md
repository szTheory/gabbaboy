---
phase: "18"
slug: "player-save-slots-and-host-contract"
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-10-28"
---

# Phase 18 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Source of the check map: `18-RESEARCH.md` § Validation Architecture (success criterion → automated check → negative control).

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | CTest + project C test binaries + Python `-I` checkers/harness + CMake `-P` contract checks |
| **Config file** | `tests/CMakeLists.txt`, `tests/player/CMakeLists.txt`, `tests/expected-tests.txt`, `tests/player/expected-tests.txt` |
| **Quick run command** | `cmake --build --preset phase1 && ctest --preset phase1 -R '^(host_|slot_|save_format_|no_host_clock|runner_help)' --output-on-failure` |
| **Full suite command** | `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error` |
| **Estimated runtime** | quick ~30 s; full several minutes (ASan lane ×3 timeouts) |

---

## Sampling Rate

- **After every task commit:** quick `-R` run above plus any touched checker `--self-test`
- **After every plan wave:** full `phase1` suite; for the player-slot plan also `bash tests/scripts/verify-phase3-player.sh --build-package` (macOS)
- **Before `/gsd-verify-work`:** full suite green at the exact PR head on all required CI contexts, plus `phase1-asan`, inventory self-test and `tests/scripts/verify-uat-closure.py --self-test`
- **Max feedback latency:** ~60 s for the quick run

Timing note (research finding 2): runner end-to-end tests must not wait out the 3,600-frame RTC cadence; cadence is a pure function covered by synthetic unit tests, and runner tests use one write-driven flush plus the final flush.

---

## Per-Task Verification Map

Filled by the planner from PLAN.md `<automated>` commands; every success criterion row in RESEARCH § "Success Criterion -> Automated Check Map" (1a–1g, 2a–2h, 3a–3f, 4a–4d, X1–X3) must map to at least one task with a negative control.

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| (planner fills) | | | PLAY-01 / HOST-01 / HOST-02 / HOST-03 | | | | | | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `src/host/*`, `gabbaboy_host` target (include dirs only, no core link), `src/player/slots.c` skeleton
- [ ] `tests/test_host_save_io.c`, `tests/test_host_cadence.c`, `tests/test_slots.c`, core input-clock test
- [ ] `tests/scripts/test_host_signals.py`, `tests/scripts/verify-save-formats.py` (+ `--self-test`)
- [ ] `cmake/CheckHostApiSymbols.cmake`, `cmake/CheckRunnerSourcesQualified.cmake`, extended `cmake/CheckCoreNoHostClock.cmake`
- [ ] `docs/host-contract.json` skeleton; inventory and Windows-exemption edits (`ExpectedTests.cmake`, `.github/scripts/verify-test-inventory.sh`)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| None by default (D-069) | — | ⌘S/⌘L/⌘Z reaching the app under SDL3's default macOS menu is research assumption A2; the planner should make this an automated check or record it as a declared limitation, not manual UAT | — |

*All phase behaviors have automated verification unless a planner-declared perceptual/hardware limitation is recorded.*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
