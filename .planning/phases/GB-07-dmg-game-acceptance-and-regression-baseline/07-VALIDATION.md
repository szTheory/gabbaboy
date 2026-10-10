---
phase: "7"
slug: "dmg-game-acceptance-and-regression-baseline"
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-10-10"
---

# Phase 7 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Source: `07-RESEARCH.md` § Validation Architecture.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | CTest over in-repo C test executables (`REQUIRE`/`PASS`), Python `-I` stdlib scripts, `cmake -P` checks; no new dependency |
| **Config file** | `tests/CMakeLists.txt`, `tests/acceptance/CMakeLists.txt` (new), inventories `tests/expected-tests.txt` and `tests/player/expected-tests.txt` |
| **Quick run command** | `cmake --build build && ctest --test-dir build -R 'acceptance_parse\|libbet_admission\|acceptance_predicate\|runner_' --output-on-failure` |
| **Full suite command** | `ctest --test-dir build --output-on-failure --no-tests=error --output-junit ctest.xml && bash .github/scripts/verify-test-inventory.sh build/ctest.xml tests/expected-tests.txt --installed` |
| **Estimated runtime** | quick <30 s (Debug); full suite several minutes (Libbet cases ~11 s Debug, ~90 s ASan) |

---

## Sampling Rate

- **After every task commit:** quick run command for the touched area (Libbet cases excluded)
- **After every plan wave:** full suite command; Linux ASan for waves touching runner or core
- **Before `/gsd-verify-work`:** full suite green on all native CI jobs at the exact head, `macos-player-package` green on the PR, baseline check green
- **Max feedback latency:** 30 seconds (quick run)

---

## Per-Task Verification Map

Requirement-level map; task IDs are bound by the plans' `<verify>` blocks.

| Requirement | Behavior | Test Type | Automated Command | File Exists | Status |
|-------------|----------|-----------|-------------------|-------------|--------|
| GAME-01 | Admission passes; each mutated manifest fails with a distinct message | python + CTest | `ctest --test-dir build -R libbet_admission` | ❌ W0 | ⬜ pending |
| GAME-01 | Licence text and notices row present | CTest | `ctest --test-dir build -R libbet_notice` | ❌ W0 | ⬜ pending |
| GAME-02 | Scripted input reaches predicate with frame + PCM digests | CTest runner | `ctest --test-dir build -R acceptance_libbet` | ❌ W0 | ⬜ pending |
| GAME-02 | N1/N2/N3 controls and core mutant fail the gate | CTest + exit wrapper | `ctest --test-dir build -R 'acceptance_.*(control\|mutant)'` | ❌ W0 | ⬜ pending |
| GAME-02 | Predicate truth table and ROM anchor bytes | C unit | `ctest --test-dir build -R acceptance_predicate` | ❌ W0 | ⬜ pending |
| EVID-01 | Case/script parser boundaries and negative files | C unit | `ctest --test-dir build -R acceptance_parse` | ❌ W0 | ⬜ pending |
| EVID-01 | Applicability: unsupported-model exit 4, target-revision exclusion | CTest + exit wrapper | `ctest --test-dir build -R 'acceptance_.*_excluded_'` | ❌ W0 | ⬜ pending |
| EVID-01 | RGB digest equals independent Python vector; PPM only on failure | C unit + python | `ctest --test-dir build -R acceptance_rgb_digest` | ❌ W0 | ⬜ pending |
| EVID-01 | `LD B,B` frame capture / `not-ready` reporting | CTest | `ctest --test-dir build -R acceptance_ldbb` | ❌ W0 | ⬜ pending |
| GAME-03 | Packaged player scripted smoke; PCM digest equals headless | package script (macOS) | `bash tests/scripts/verify-phase3-player.sh --build-package` | extend | ⬜ pending |
| GAME-03 | Session-level negative controls | player CTest | `ctest --test-dir build -R player_session_script` | ❌ W0 | ⬜ pending |
| EVID-02 | Ledger byte-identity on Linux/macOS/Windows; frozen inventory superset | cmake script | `ctest --test-dir build -R dmg_baseline` | ❌ W0 | ⬜ pending |
| EVID-02 | Checker self-tests (modified/missing/extra/removed) fail | cmake script | `ctest --test-dir build -R 'dmg_baseline_(modified\|missing\|extra\|inventory)'` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/acceptance/CMakeLists.txt` and the new test executables/scripts above
- [ ] `tests/expect_exit.cmake` — exact exit-code wrapper
- [ ] Windows CI spike: `find_package(Python3)` and `cmake -P` comparison on `windows-2022`
- [ ] Independent Python hashlib RGB-digest vector for a synthetic frame (D-26)
- [ ] PCM threshold calibration record from the first CI run

---

## Manual-Only Verifications

All phase behaviors have automated verification. One-time recorded inspection of each failure-path PPM before blessing digests (D-26) is an evidence record, not a gate.

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
