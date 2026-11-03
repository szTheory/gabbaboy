---
status: complete
phase: GB-22-composition-and-microtest-evidence
source: 22-01-SUMMARY.md, 22-02-SUMMARY.md, 22-10-SUMMARY.md, 22-11-SUMMARY.md
started: 2026-11-03T12:11:17.991662+00:00
updated: 2026-11-03T12:11:17.991662+00:00
---

## Automated Evidence

# Phase 22 Final Evidence

**Scope:** Owner-approved D-141 synthetic-plus-metadata closeout. DIAG-01, DIAG-02, and RIGHTS-01 remain Pending with their original definitions. The seven real-fixture evidence gates remain a no-go; no license prohibition is inferred.

## Immutable Source and Metadata

The metadata assessment retains its historical source revision `559b5f7296f957a1a1fea278056a908f9a3d9339`. The current source and local evidence checks below use commit `25f8966cdbb34733b7e51f58f97182caa2b9ea39`; the exact final boundary source and its full-suite result are recorded with the PR run record.

The generated local snapshot is `build/phase22/evidence.json`, SHA-256 `9f06ec7c479524f9ea8bfaf6b9ef1f71c92d17f07d75bb6da81ab123b1d93cec`. At the recorded source it reports:

- 513 named metadata cases: 480 shared-macro, two inline, and 31 initial no-protocol exclusions.
- 482 candidates remain blocked/not observed; final suite accounting is incomplete.
- All seven required gates are unresolved; admitted = 0 and executed = 0.
- Real approval exits 2 with `scope-resolution-required` and the exact seven-gate list.
- Requirement definitions and source/package boundaries remain unchanged; DIAG-01/02 and RIGHTS-01 are Pending.

## Local Checks

| Check | Source | Result |
|---|---|---|
| `verify-diagnostic-evidence.py --check --repo-root . --source-revision HEAD --write-evidence build/phase22/evidence.json` | `25f8966c` | Passed; immutable inventory, claims, no-go, requirement and source/product boundary checks. |
| `verify-diagnostic-evidence.py --self-test-controls --repo-root . --source-revision 25f8966cdbb34733b7e51f58f97182caa2b9ea39` | `25f8966c` | Passed; roster/gate/boundary mutations, renamed payloads, UTF-8/UTF-16 SVG, AVIF/HEIC/ICO/ROM, bounded subprocess, source archive, and checker self-scan. |
| `verify-diagnostic-admission.py --self-test-controls --repo-root . --source-revision HEAD` | `25f8966c` | Passed 12 controls, including mutable assessment, inventory, Phase 20 checker, and policy substitutions. |
| `verify-diagnostic-admission.py --require-approved --repo-root . --source-revision HEAD` | `25f8966c` | Correctly refused with exit 2 and all seven unresolved gates. |
| Focused phase1 CTest fixture repository/product and Phase 22 controls | `25f8966c` | Passed; zero newly admitted fixture changes against the existing baseline and package/control boundaries pass. |
| `verify-summary-coverage.py --file 22-01/02/10-SUMMARY.md` | current summaries | Passed; D2 in Plan 22-02 has automated passing references and `human_judgment: false`. |

The latest complete focused CTest selection at source `25f8966c` passed 14/14 in 59.08 seconds. It included fixture-admission controls, core/player package controls, budget controls, and Phase 22 synthetic/evidence contracts. The final full CTest result and exact-head CI outcomes are carried in the final PR run record, which is the completion gate for the committed boundary.

## Review and Security

The independent scoped code and security reviews are recorded in `22-REVIEW.md` and `22-SECURITY.md` at exact reviewed source `25f8966cdbb34733b7e51f58f97182caa2b9ea39`. They confirm the immutable checker/policy and renamed-payload controls, with no unresolved source finding. The live exact-head PR gate remains a separate required check and is recorded with the PR run record.

## Build and Feedback Cost

The latest focused run measured a 13.5-second configure and rebuilt 339 targets because the configured evidence identity changed. The selected CTests took 59.08 seconds; fixture-admission controls took 16.45 seconds, core/player product controls about 11.15 seconds each, and Phase 22 evidence controls 13.48 seconds. No evidence supports changing existing budgets, adding a cache, or changing job scheduling. The exact final full-suite and CI durations are recorded with the PR's final run record.

## Exact-Head Qualification

The final source and immutable boundary ID are recorded in the committed state and this evidence file. The PR record carries sanitized exact-head local/remote run, job, package artifact, review, and merge-tree identities; `build/phase22/remote-evidence.json` is the local machine-readable capture. A failed, inaccessible, stale, skipped, or unsuccessful required lane leaves Phase 22 unclosed.

**Phase 23 handoff:** Phase 23 — Qualified v0.4.0 Release — remains unstarted. The owner-controlled next command is `/gsd-discuss-phase 23`; both automatic-advance flags stay false.

## Current Test

[testing complete]

## Tests

### 1. Original synthetic composition traverses admission, compiled runner, exact unmasked comparison, receipt binding, and product exclusion.
expected: "Original synthetic composition traverses admission, compiled runner, exact unmasked comparison, receipt binding, and product exclusion."
result: pass
source: automated
summary_file: 22-01-SUMMARY.md
coverage_id: D1
evidence: ["ctest --preset phase1 --output-on-failure --no-tests=error -R '^phase22_(acid2_(tracer|contract|controls)|fixture_admission_(contract|controls))$'"]

### 2. Changed identities, broadened masks, malformed images and admission pins are refused with specific controls.
expected: "Changed identities, broadened masks, malformed images and admission pins are refused with specific controls."
result: pass
source: automated
summary_file: 22-01-SUMMARY.md
coverage_id: D2
evidence: ["phase22_acid2_contract, phase22_acid2_controls, phase22_fixture_admission_contract, phase22_fixture_admission_controls"]

### 3. The source-bound assessment and exact 513-case inventory remain blocked, with real-byte approval refused at the seven unresolved gates.
expected: "The source-bound assessment and exact 513-case inventory remain blocked, with real-byte approval refused at the seven unresolved gates."
result: pass
source: automated
summary_file: 22-02-SUMMARY.md
coverage_id: D1
evidence: ["ctest --preset phase1 --output-on-failure --no-tests=error -R '^phase22_(admission_assessment|fixture_admission_(contract|controls))$'", "python3 -I tests/scripts/verify-diagnostic-admission.py --check-assessment --repo-root . --source-revision HEAD", "python3 -I tests/scripts/verify-diagnostic-admission.py --require-approved --repo-root . --source-revision HEAD (assert exit 2 and scope-resolution-required)"]

### 4. The public evidence document states the approved synthetic-plus-metadata scope and accurately describes the no-go boundary.
expected: "The public evidence document states the approved synthetic-plus-metadata scope and accurately describes the no-go boundary."
result: pass
source: automated
summary_file: 22-02-SUMMARY.md
coverage_id: D2
evidence: ["phase22_evidence_controls CTest: public documentation and claim mutations are rejected", "python3 -I tests/scripts/verify-diagnostic-evidence.py --check --repo-root . --source-revision HEAD --write-evidence build/phase22/evidence.json"]

### 5. Immutable snapshot proves the 513-name metadata inventory and exact seven-gate real-fixture refusal.
expected: "Immutable snapshot proves the 513-name metadata inventory and exact seven-gate real-fixture refusal."
result: pass
source: automated
summary_file: 22-10-SUMMARY.md
coverage_id: D1
evidence: ["ctest --preset phase1 --output-on-failure --no-tests=error -R '^phase22_(evidence_(contract|controls)|acid2_(tracer|contract|controls)|fixture_admission_(contract|controls))$'", "python3 -I tests/scripts/verify-diagnostic-evidence.py --check --repo-root . --source-revision HEAD --write-evidence build/phase22/evidence.json"]

### 6. Public diagnostic documents state the metadata-only no-go disposition and retain evidence and compatibility limits.
expected: "Public diagnostic documents state the metadata-only no-go disposition and retain evidence and compatibility limits."
result: pass
source: automated
summary_file: 22-10-SUMMARY.md
coverage_id: D2
evidence: ["phase22_evidence_controls CTest: documentation and claim mutations are rejected", "phase1 preset configure/build and immutable diagnostic evidence check"]

### 7. Existing synthetic tracer and fixture-admission contracts remain passing, with boundary checks bound to an immutable supplied revision.
expected: "Existing synthetic tracer and fixture-admission contracts remain passing, with boundary checks bound to an immutable supplied revision."
result: pass
source: automated
summary_file: 22-10-SUMMARY.md
coverage_id: D3
evidence: ["ctest --preset phase1 --output-on-failure --no-tests=error -R '^phase22_(evidence_(contract|controls)|acid2_(tracer|contract|controls)|fixture_admission_(contract|controls))$'", "phase22_evidence_controls CTest: immutable historical boundary and later-HEAD mutation controls"]

### 8. The immutable diagnostic assessment retains 513 metadata cases and refuses real admission with all seven gates unresolved; renamed payload and dependency mutants are refused.
expected: "The immutable diagnostic assessment retains 513 metadata cases and refuses real admission with all seven gates unresolved; renamed payload and dependency mutants are refused."
result: pass
source: automated
summary_file: 22-11-SUMMARY.md
coverage_id: D1
evidence: ["ctest --preset phase1 --output-on-failure --no-tests=error -R '^phase22_.*$': immutable evidence contract, added-payload controls and source-archive control", "python3 -I tests/scripts/verify-diagnostic-evidence.py --check --repo-root . --source-revision HEAD --write-evidence build/phase22/evidence.json", "verify-diagnostic-admission.py --self-test-controls: 12 mutation controls; --require-approved exits 2 with all seven gates"]

### 9. Synthetic tracer, current fixture/product boundaries and fixed test budgets pass; independent code and security reviews close the source findings.
expected: "Synthetic tracer, current fixture/product boundaries and fixed test budgets pass; independent code and security reviews close the source findings."
result: pass
source: automated
summary_file: 22-11-SUMMARY.md
coverage_id: D2
evidence: ["cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error -R '^(phase22_.*|fixture_admission_(repository|controls)|fixture_product_(core|player)_controls|test_budget(_controls)?)$'", "22-REVIEW.md and 22-SECURITY.md: exact reviewed source 25f8966cdbb34733b7e51f58f97182caa2b9ea39; no unresolved source findings", "verify-summary-coverage.py for 22-01, 22-02, 22-10 and this block; D2 in 22-02 has human_judgment: false"]

### 10. The candidate boundary preserves Pending requirements, false automatic-advance flags, all seven no-go gates, and the exact owner-controlled Phase 23 route.
expected: "The candidate boundary preserves Pending requirements, false automatic-advance flags, all seven no-go gates, and the exact owner-controlled Phase 23 route."
result: pass
source: automated
summary_file: 22-11-SUMMARY.md
coverage_id: D3
evidence: ["verify-diagnostic-evidence.py --check-boundary at the immutable boundary commit recorded in 22-EVIDENCE.md", "verify-uat-closure.py for this phase: shared closure self-test and full live-summary coverage pass"]

## Summary

total: 10
passed: 10
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps

[none]
