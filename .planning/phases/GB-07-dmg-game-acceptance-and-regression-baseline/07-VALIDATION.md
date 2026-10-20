---
phase: "7"
slug: "dmg-game-acceptance-and-regression-baseline"
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# A validated record is compliant only when nyquist_compliant is true.
status: validated
nyquist_compliant: true
wave_0_complete: true
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
| **Config file** | `tests/CMakeLists.txt`, `tests/acceptance/CMakeLists.txt`, inventories `tests/expected-tests.txt` and `tests/player/expected-tests.txt` |
| **Quick run command** | `python3 -I tests/scripts/verify-stall-report.py --self-test && cmake --build build && ctest --test-dir build -R 'acceptance_parse\|libbet_admission\|acceptance_predicate\|runner_' --output-on-failure` |
| **Full suite command** | `ctest --test-dir build --output-on-failure --no-tests=error --output-junit ctest.xml && bash .github/scripts/verify-test-inventory.sh build/ctest.xml tests/expected-tests.txt --core-only` |
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
| GAME-01 | Admission passes; each mutated manifest fails with a distinct message | python + CTest | `ctest --test-dir build -R 'libbet_(admission\|not_installed\|install_tree)'` (07-01) | ✅ | ✅ green |
| GAME-01 | Licence text and notices row present | CTest | `ctest --test-dir build -R libbet_notice` (07-01) | ✅ | ✅ green |
| GAME-02 | Scripted input reaches predicate with frame + PCM digests | CTest runner | `ctest --test-dir build -R 'acceptance_(lib_)?libbet'` (07-02, 07-05, 07-07) | ✅ | ✅ green |
| GAME-02 | N1/N2/N3 controls and core mutant fail the gate | CTest + exit wrapper | `ctest --test-dir build -R 'acceptance_(core_mutant\|libbet_drop_start\|suite)'` (07-10) | ✅ | ✅ green |
| GAME-02 | Fresh bounded stall report has meaningful count-matched trace, I/O and histogram sections; two runs produce identical report and failure image; weakened reports fail | integration + Python self-test | `ctest --test-dir build -R '^acceptance_stall_diagnosis$' --output-on-failure --no-tests=error` (07-11 Task 2) | ✅ | ✅ green |
| GAME-02 | Predicate truth table and ROM anchor bytes | C unit | `ctest --test-dir build -R acceptance_predicate_` (07-02) | ✅ | ✅ green |
| EVID-01 | Case/script parser boundaries and negative files | C unit | `ctest --test-dir build -R 'acceptance_(parse_\|negative_)'` (07-02, 07-06) | ✅ | ✅ green |
| EVID-01 | Applicability: unsupported-model exit 4, target-revision exclusion | CTest + exit wrapper | `ctest --test-dir build -R 'acceptance_(suite_\|target_revision\|unknown_model\|unexpected_pass\|libbet_excluded)'` (07-08) | ✅ | ✅ green |
| EVID-01 | RGB digest equals independent Python vector; PPM only on failure | C unit + python | `ctest --test-dir build -R 'acceptance_(digest_vectors\|failure_dir)'` (07-07) | ✅ | ✅ green |
| EVID-01 | `LD B,B` frame capture / `not-ready` reporting | CTest | `ctest --test-dir build -R acceptance_ldbb_` (07-09) | ✅ | ✅ green |
| GAME-03 | Packaged player scripted smoke; PCM digest equals headless | package script (macOS) | `bash tests/scripts/verify-phase3-player.sh --build-package` (07-12, 07-14) | ✅ | ✅ green |
| GAME-03 | Session-level negative controls | player CTest | `ctest --test-dir build/phase3-player/gabbaboy -R 'player_(session_script\|script_smoke_surface)' --no-tests=error` (07-14) | ✅ | ✅ green |
| EVID-02 | Ledger byte-identity on Linux/macOS/Windows; frozen inventory superset | cmake script | `ctest --test-dir build -R dmg_baseline` (07-13, 07-15) | ✅ | ✅ green |
| EVID-02 | Checker self-tests (modified/missing/extra/removed) fail | cmake script | `ctest --test-dir build -R 'dmg_baseline_(modified\|missing\|extra\|inventory\|changes\|empty\|header\|junit)'` (07-13) | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `tests/acceptance/CMakeLists.txt` and the new test executables/scripts above
- [x] `tests/expect_exit.cmake` — exact exit-code wrapper
- [x] Windows CI spike: `find_package(Python3)` and `cmake -P` comparison on `windows-2022`
- [x] Independent Python hashlib RGB-digest vector for a synthetic frame (D-26)
- [x] PCM threshold calibration record from the first CI run

---

## Manual-Only Verifications

All phase behaviors have automated verification. One-time recorded inspection of each failure-path PPM before blessing digests (D-26) is an evidence record, not a gate.

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 30s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** validated 2026-10-10 — every requirement row maps to registered tests that pass locally (258/258 core CTest at 30a539b) and in exact-head CI run 38108289289 (all eight jobs, including player tests on macos-player-package). Player rows run in the player build, not the core preset.

## Validation Audit 2026-10-11

| Metric | Count |
|---|---|
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |

## Retroactive reconciliation — 2026-10-20

The owner selected **fix all gaps** after discovery. Review covered all **17 plans and 40 tasks**, with all five requirement contracts mapped to automation. One supporting task was partial: 07-11 Task 2's file existence/size check would accept an empty diagnostic report. `tests/scripts/verify-stall-report.py` now runs the actual dropped-START case twice, requires the expected exit/reason and fresh report/PPM each time, validates section schemas, record counts and caps (4096 trace, 64 I/O, eight histogram), checks useful input writes and complete-trace histogram agreement, and compares both artifacts byte for byte. No implementation file changed.

The fast self-test (`python3 -I tests/scripts/verify-stall-report.py --self-test`, also run automatically by `acceptance_stall_diagnosis`) rejects **19 malformed report controls plus one repeated-byte mismatch**. Controls include empty, missing/truncated sections, wrong counts, invalid I/O address, missing input writes, wrong histogram order/counts, absent/invalid truncation flag, wrong id/reason, cap overruns and an oversized report. The real report has 111 trace records, five I/O writes and eight histogram entries in 1,984 bytes; the accompanying P6 image is 69,135 bytes. The old frontmatter/sign-off contradiction is reconciled only after these checks passed.

### Plan-to-task reconciliation

| Plan | Tasks | Requirements | Automated coverage / bounded evidence |
|---|---|---|---|
| 07-01 | 1–3 | GAME-01 | `libbet_admission_*`, `libbet_notice`, install-tree absence and its negative control; historical exact-head Windows receipt |
| 07-02 | 1–3 | GAME-02, EVID-01 | `acceptance_lib_libbet_replay`, parser bounds/errors, predicate truth table and anchors |
| 07-03 | 1–2 | GAME-02 | `audio_saturation`; D-027 retains its historical RED-evidence limitation |
| 07-04 | 1–2 | GAME-01 | `reproduce-libbet.sh --compare` and admission-checked reproduction statement; local reproduction scope only |
| 07-05 | 1–2 | GAME-02, EVID-01 | `acceptance_libbet` and parser/runner regressions |
| 07-06 | 1–2 | EVID-01 | `acceptance_negative_*`, parser cases bounds/errors/paths |
| 07-07 | 1–2 | GAME-02, EVID-01 | Libbet observations, digest vectors, unwritable-failure-dir control and pinned baseline |
| 07-08 | 1–2 | EVID-01 | Model/revision and suite-exclusion controls, unknown-model refusal, unexpected-pass rejection |
| 07-09 | 1–2 | EVID-01 | `acceptance_ldbb_*` and independent digest reference |
| 07-10 | 1–2 | GAME-02 | Raw no-input/SELECT rejection, strict xfail twins, dropped START and actual core mutant |
| 07-11 | 1–3 | GAME-02 | SGB tolerance; strengthened `acceptance_stall_diagnosis` with its automatic checker self-test; historical cross-OS calibration receipt |
| 07-12 | 1–2 | GAME-03 | Extracted-package smoke, guest predicate, headless PCM equality and fixture absence scan |
| 07-13 | 1–3 | EVID-02 | `dmg_baseline_*` comparator/change/JUnit negative controls |
| 07-14 | 1–3 | GAME-03 | Packaged no-input failure, player session/script-surface controls |
| 07-15 | 1–2 | EVID-02 | Frozen `dmg_baseline` and native/player inventory enforcement |
| 07-16 | 1–3 | All five | Historical documentation/decision/handoff checks at their boundary, plus current support-ledger automation |
| 07-17 | 1–2 | GAME-02 | D-028 source/probe receipt establishes expected early-tap behavior; no fix branch was needed; current input controls remain registered |

### Fresh execution evidence

- Final test-only revision: `5f9bfbd46b7794f64669f0a747164ac9919c79cc`, including the original test addition `8c00c8d` and the release-inventory repair. No core/player implementation changed. These are local execution receipts, not a hosted result for the later documentation commit.
- `cmake --preset phase1` and `cmake --build --preset phase1` succeeded. `ctest --test-dir build -R '^(acceptance_|libbet_|dmg_baseline|runner_|audio_saturation$)' --output-on-failure --no-tests=error --output-junit phase7-validation-current.xml`: **97/97 passed**, zero failures/skips, 188.20 s. The strengthened diagnosis (including its 20 negative controls) took 64.69 s and remains outside the quick feedback path. The direct checker self-test is included in the quick command.
- Configured core inventory exactly matches **1,144 registered tests**, excluding five install-only entries. The inventory is byte-identical to the source base. This is registration evidence, not a claim that all 1,144 tests were rerun.
- `bash tests/scripts/verify-phase3-player.sh --build-package`: **98/98 player tests**, clean-source build receipt at `5f9bfbd46b7794f64669f0a747164ac9919c79cc`, extracted-byte Libbet predicate and non-silent PCM pass; PCM SHA-256 `3d051cb0a0a4ced82706126c5cbcaddcd22dbe2cc2e61c92d0c5717f1e8aaae5` matches headless; no-input control exits 1 with predicate failure. Archive SHA-256 `f1224d9fae8a0cd361fbb99999956e9eeaf1f6235d4241313f9588b9a4083895` matches the generated build receipt.
- `python3 tests/scripts/verify-support-ledger.py --self-test`: release/ledger binding, 15 v0.2 schema controls, 24 sidecar controls and three static-ledger controls pass. `--check-ledger` passes all 132 covered source identities and the 107-case support claim without changing the ledger.
- `python3 .planning/verify-v02-milestone-audit.py --self-test`: historical audit still reconciles 28 requirements, 134 summaries and nine phase reports, rejecting **16 negative controls**. It reads its recorded boundary commit, so this later closure does not rewrite its earlier findings.

### Hosted failure and repair

The first draft added a separate CTest name. Linux CI at `ff25ad0` rejected it before configure because the published support ledger binds `tests/expected-tests.txt`. Local reproduction confirmed `self-test tagged source differs from the tracked ledger:tests/expected-tests.txt`. The repair restores that inventory byte for byte and runs the same checker self-test automatically inside the existing `acceptance_stall_diagnosis` CTest. The direct `--self-test` command remains available for fast feedback. No assertion or release gate was weakened, and the ledger was not rewritten. Superseded CI runs were cancelled; fresh remote checks must certify the final PR head before any merge.

### Evidence limits retained

No new hardware, perceptual or cross-platform execution claim is made. Hosted Linux Libbet reproduction (D-039) and the missing pre-fix audio saturation RED demonstration (D-027) remain recorded limitations. Dense scripts already fail explicitly; driver back-pressure remains deferred. The former missing `frame-digest@t` control is superseded by the registered Phase 11 `acceptance_cgb_colour_hblank` and `acceptance_cgb_colour_flipped_ppm` tests, both included in the fresh run. Historical handoff checks are evaluated at their boundary revisions; later routes are not failures of those earlier closures. No manual-only gap remains.

## Validation Audit 2026-10-20

| Metric | Count |
|---|---|
| Gaps found | 1 |
| Resolved | 1 |
| Escalated | 0 |
