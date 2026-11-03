---
phase: "22"
slug: "composition-and-microtest-evidence"
status: complete
nyquist_compliant: true
wave_0_complete: true
created: "2026-11-02"
---

# Phase 22 — Validation Strategy

> D-141 narrows Phase 22 to the original synthetic composition tracer, the metadata-only 513-case assessment, and a machine-checked real-fixture no-go. The original DIAG-01, DIAG-02, and RIGHTS-01 meanings remain unchanged and Pending.

## Test Infrastructure

| Property | Value |
|---|---|
| Framework | CMake/CTest and isolated Python standard-library checkers. |
| Preset | `phase1`; registration and exact inventory live in `tests/CMakeLists.txt` and `tests/expected-tests.txt`. |
| Focused set | `phase22_*`, fixture repository/product controls, and fixed test-budget controls; use `--no-tests=error`. |
| Final set | `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error`. |
| Evidence identity | Each final checker resolves the full source commit. Boundary claims read the explicitly retained boundary commit. |
| No-go contract | Approval exits 2 with all seven unresolved gates; admitted and executed real cases remain zero. |

## Revised Roadmap Criteria

| Criterion | Evidence and causal controls | Live plans |
|---|---|---|
| Original synthetic composition runs through the compiled runner with its fixed source-cell mask, exact unmasked comparison, and identity/mask/image controls. | `phase22_acid2_tracer`, `phase22_acid2_contract`, `phase22_acid2_controls`, and fixture-admission contract/control tests; changed identities, widened masks, malformed images, unsafe paths, and altered pins are refused. | 22-01; preserved and rechecked by 22-10/11. |
| Immutable metadata retains all 513 source/ROM names and each unresolved admission gate; real-byte approval refuses while required evidence is absent. | `phase22_admission_assessment`, fixture-admission controls, `verify-diagnostic-evidence.py --check`, and `verify-diagnostic-admission.py --require-approved`; roster, gate, status, eligibility, and fake-approval mutants are refused. | 22-02, 22-10, 22-11. |
| Public claims keep the tracer synthetic-only, record no-go without inventing a license prohibition, and preserve DIAG-01/02 and RIGHTS-01 as Pending. | Immutable documentation checks, requirement definition/disposition comparisons, summary block coverage, shared closure writer, and historical boundary mutants. | 22-02, 22-10, 22-11. |

## Live Plan Validation Map

| Plan | Scope and status | Required evidence |
|---|---|---|
| 22-01 | Complete. Original project-authored synthetic DMG composition and exact receipt identity controls. | D1/D2 coverage in `22-01-SUMMARY.md`; compiled-runner and source-cell comparison CTests. |
| 22-02 | Complete. Source-bound metadata assessment and public no-go. | D1/D2 coverage in `22-02-SUMMARY.md`; D2 now has `human_judgment: false` and passing document-contract plus immutable evidence references. |
| 22-10 | Complete. Immutable inventory/no-go snapshot, claims, exact test membership, and boundary checker. | D1–D3 coverage in `22-10-SUMMARY.md`; eight registered Phase 22 checks and mutation controls. |
| 22-11 | Final live plan. Local review/security, exact source/build, generated closure and phase boundary, full local suite, and exact-head PR evidence. | Block-style coverage in `22-11-SUMMARY.md`; immutable no-go and boundary checks, all configured CTests, `verify-pr-evidence.sh`, same-head runs/artifacts, review dispositions, and merge-tree comparison. |

Plans 22-03 through 22-09 are marked `superseded` in the roadmap under D-141. Their original real-fixture build, game/diagnostic, cohort execution, distribution, and lifecycle expectations are outside the approved phase scope; they are neither missing deliverables nor passing claims.

## Threat and Control Dispositions

| Threat | Control and evidence |
|---|---|
| T-22-01 / T-22-02 / T-22-03 | Fixed source-cell allowlist and independent receipt identities; bounded image, JSON, subprocess, and admission paths; Phase 20 CLI refuses before real runner use. Verified by 22-01 contract/control coverage. |
| T-22-04 / T-22-05 / T-22-06 / T-22-26 / T-22-27 | Full named metadata projection, seven unresolved gates, exact Pending dispositions, and source/history accounting. Verified by 22-02 assessment and immutable evidence checks. |
| T-22-28 / T-22-29 / T-22-30 / T-22-31 | Full-commit snapshots, exact roster and refusal, unchanged source/product boundary, no added payloads, bounded per-blob inspection, claim and historical-boundary mutations. Verified by 22-10/11 controls. |
| CR-07 | Planning-label exception is bound to the exact evidence checker invocation, immutable revision, active build directory and configured Python interpreter; negative controls reject executable/output/argument substitutions. Verified by the planning-label self-test and configured inventory CTest. |
| T-22-32 | Exact local HEAD equals PR head; required same-head CI, fixture, preview jobs and package artifacts; independently inspect current runs/reviews and merge-tree equivalence. The exact-head outcome is recorded in the final PR record. |
| T-22-33 / T-22-34 / T-22-35 | Automated coverage and Pending definitions, exact Phase 23 owner route with both automatic flags false, and sanitized repository-relative records. Verified by closure and immutable boundary controls. |
| T-22-SC | No package install or new dependency; use the existing Python, Git, CMake, and CTest toolchain. |

## Sampling and Cost

After a task commit, run its direct contract and negative control. Before final qualification, run the configured full preset once at the final tracked source, with the exact expected inventory and `--no-tests=error`. Preserve the existing platform, sanitizer, fuzz, fixture, consumer, player-package, and budget policy.

The latest broad focused run passed 23/23 selected tests in 42.98 seconds at four-way parallelism; its longest controls were Phase 21 fixture admission (22.67 seconds) and repository admission (18.34 seconds). At reviewed source `06d2cbc1`, the configured planning/evidence selection passed 4/4 in 13.10 seconds, and the real planning inventory check counted 1,732 tests / 47 planning tests. Configure took 12.6 seconds; the 339-target build passed. The full suite passed 1,732/1,732 in 495.43 seconds at commit `042e7f34`; record the final tracked-head configure/build/full-suite result and hosted durations in `build/phase22/remote-evidence.json`. This does not establish a safe cache or parallelism improvement; keep existing budgets and scheduling.

## UAT and Limitations

No manual or game/perceptual/hardware UAT is planned. The shared closure is generated from live SUMMARY block coverage and its self-test proves that weakened coverage is refused. Synthetic runner evidence and metadata are not a real diagnostic result. No upstream ROM/reference payload, upstream build/program, real fixture admission, license prohibition, or completed DIAG/RIGHTS requirement is claimed.

Final validation is governed by Plan 22-11's immutable local and exact-head remote gates. This validation document remains conditional while either gate is outstanding. Phase 23 remains unstarted and owner-controlled at `/gsd-discuss-phase 23`.
