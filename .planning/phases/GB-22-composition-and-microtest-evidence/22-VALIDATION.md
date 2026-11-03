---
phase: "22"
slug: "composition-and-microtest-evidence"
status: complete
nyquist_compliant: true
wave_0_complete: true
created: "2026-11-02"
---

# Phase 22 — Validation Strategy

> D-141 narrows Phase 22 to the original synthetic composition tracer, the metadata-only 513-case assessment, and a machine-checked real-fixture no-go. D-143 allows one C1 OSC diagnostic correction and independent review in the existing 22-12 plan. The original DIAG-01, DIAG-02, and RIGHTS-01 meanings remain unchanged and Pending.

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

## D-142 Windows Remediation Validation

The bounded Windows repair preserves the revised D-141 acceptance contract and all existing CTest names, assertions, Windows inventory membership, expected-test policy, required CI contexts, and the 60-second `phase22_evidence_*` CTest limits. No test is skipped or waived, no child or CTest limit is raised, and no checker assertion is weakened. The Windows baseline is 1,594 configured tests; the local Phase 1 inventory is 1,732. [VERIFIED: `build/phase22/remote-evidence.json`; `.planning/phases/GB-22-composition-and-microtest-evidence/22-CONTEXT.md`]

Run the ten previously failing CTests as a focused local selection after each relevant fix:

```sh
ctest --preset phase1 --output-on-failure --no-tests=error -R '^(acceptance_cgb_progress_(discrimination|observations|controls|tracer|compat_rejected)|phase21_fixture_admission_controls|phase21_game_evidence|phase22_evidence_contract|phase22_evidence_controls|planning_labels_controls)$'
```

The existing tests must retain positive and causal negative controls: native and Windows-separator command paths; temporary Git initialization with hostile global hooks/signing configuration and proof that hooks do not run; exact expected-test inventory acceptance plus missing/duplicate/unexpected membership refusal; and the evidence checker’s immutable-boundary, archive, and timeout controls. Time the existing evidence-control stages to identify the near-limit cost without removing a control or increasing its timeout. The configured inventory and exact test names remain unchanged. [VERIFIED: `22-RESEARCH.md` D-142 Validation Architecture; `tests/CMakeLists.txt`; `tests/cmake/ci-lanes.cmake`; `tests/expected-tests.txt`]

Because this host is macOS, Windows behavior is qualified only by the updated PR’s fresh `native-windows-x64` run. After independent code and security review, run the full local Phase 1 configure/build/CTest command once at the final tracked source. Then require fresh exact-head `required-native`, `fixture-repro`, and `preview-package-smoke` results, their required artifacts, and a successful `.github/scripts/verify-pr-evidence.sh` check. A failed, skipped, stale, missing, or different-head result leaves Phase 22 open. [VERIFIED: `22-RESEARCH.md` D-142 Validation Architecture; `.planning/phases/GB-22-composition-and-microtest-evidence/22-EVIDENCE.md`]

Under D-143, one additional independent code/security review was authorized only for the C1 OSC diagnostic correction and its new causal control. The two earlier review-fix rounds and one gap round remain used; the ledger was not reset. The single C1 correction and its fresh code/ASVS reviews are complete and clean at `93004a65143a4bc3199e1f028b003e2d3dd11ef6`. Any further blocking correctness/security finding stops Phase 22 for owner scope resolution rather than opening another fix or gap round. Continue only the already-authorized local and exact-head qualification on the same PR.

## Live Plan Validation Map

| Plan | Scope and status | Required evidence |
|---|---|---|
| 22-01 | Complete. Original project-authored synthetic DMG composition and exact receipt identity controls. | D1/D2 coverage in `22-01-SUMMARY.md`; compiled-runner and source-cell comparison CTests. |
| 22-02 | Complete. Source-bound metadata assessment and public no-go. | D1/D2 coverage in `22-02-SUMMARY.md`; D2 now has `human_judgment: false` and passing document-contract plus immutable evidence references. |
| 22-10 | Complete. Immutable inventory/no-go snapshot, claims, exact test membership, and boundary checker. | D1–D3 coverage in `22-10-SUMMARY.md`; eight registered Phase 22 checks and mutation controls. |
| 22-11 | Final live plan. Local review/security, exact source/build, generated closure and phase boundary, full local suite, and exact-head PR evidence. | Block-style coverage in `22-11-SUMMARY.md`; immutable no-go and boundary checks, all configured CTests, `verify-pr-evidence.sh`, same-head runs/artifacts, review dispositions, and merge-tree comparison. |
| 22-12 | D-142 Windows CI remediation plus the D-143 C1 OSC correction and review. Both corrections are locally implemented; the C1 reviews and focused local checks are clean. Final full-suite and exact-head qualification remain pending. | C1 fail-first and disabled-matcher mutation in `diagnostic_sanitization_control`; the existing `phase22_evidence_controls` identity; the ten-test and alternate-build selections; the 19-test Task 2 selection; exact-source code/ASVS reports; one final full local suite; and fresh exact-head required PR contexts and artifacts. |

Plans 22-03 through 22-09 are marked `superseded` in the roadmap under D-141. Their original real-fixture build, game/diagnostic, cohort execution, distribution, and lifecycle expectations are outside the approved phase scope; they are neither missing deliverables nor passing claims.

## Threat and Control Dispositions

| Threat | Control and evidence |
|---|---|
| T-22-01 / T-22-02 / T-22-03 | Fixed source-cell allowlist and independent receipt identities; bounded image, JSON, subprocess, and admission paths; Phase 20 CLI refuses before real runner use. Verified by 22-01 contract/control coverage. |
| T-22-04 / T-22-05 / T-22-06 / T-22-26 / T-22-27 | Full named metadata projection, seven unresolved gates, exact Pending dispositions, and source/history accounting. Verified by 22-02 assessment and immutable evidence checks. |
| T-22-28 / T-22-29 / T-22-30 / T-22-31 | Full-commit snapshots, exact roster and refusal, unchanged source/product boundary, no added payloads, bounded per-blob inspection, claim and historical-boundary mutations. Verified by 22-10/11 controls. |
| CR-07 | Planning-label exception is bound to the exact evidence checker invocation, immutable revision, active build directory and configured Python interpreter; negative controls reject executable/output/argument substitutions. Verified by the planning-label self-test and configured inventory CTest. |
| T-22-38 | D-143's C1 OSC payload-disclosure edge is closed at `93004a65143a4bc3199e1f028b003e2d3dd11ef6`: UTF-8 byte regression, fail-first and disabled-matcher refusal run in the existing evidence control; fresh independent code and ASVS 1 reviews report clean/SECURED with zero findings. Remaining D-142 controls and all output/time limits are preserved. |
| T-22-32 | Exact local HEAD equals PR head; required same-head CI, fixture, preview jobs and package artifacts; independently inspect current runs/reviews and merge-tree equivalence. The exact-head outcome is recorded in the final PR record. |
| T-22-33 / T-22-34 / T-22-35 | Automated coverage and Pending definitions, exact Phase 23 owner route with both automatic flags false, and sanitized repository-relative records. Verified by closure and immutable boundary controls. |
| T-22-SC | No package install or new dependency; use the existing Python, Git, CMake, and CTest toolchain. |

## Sampling and Cost

After a task commit, run its direct contract and negative control. Before final qualification, run the configured full preset once at the final tracked source, with the exact expected inventory and `--no-tests=error`. Preserve the existing platform, sanitizer, fuzz, fixture, consumer, player-package, and budget policy.

The D-143 source `93004a65143a4bc3199e1f028b003e2d3dd11ef6` passed the ten-test selection (57.27 seconds), alternate four-test selection (16.25 seconds), and broader 19-test selection (56.00 seconds). Configure took 14.0 seconds and all 339 build targets passed. `phase22_evidence_controls` took 14.16 seconds in the ten-test run, below the unchanged 60-second limit. The prior 1,732/1,732 suite at `042e7f34` predates the C1 source and is historical only; the final full-suite run at the final tracked head and fresh hosted durations remain required in `build/phase22/remote-evidence.json`. No evidence supports a cache or scheduling change; preserve current budgets.

## UAT and Limitations

No manual or game/perceptual/hardware UAT is planned. The shared closure is generated from live SUMMARY block coverage and its self-test proves that weakened coverage is refused. Synthetic runner evidence and metadata are not a real diagnostic result. No upstream ROM/reference payload, upstream build/program, real fixture admission, license prohibition, or completed DIAG/RIGHTS requirement is claimed.

Final validation is governed by Plans 22-11 and 22-12's immutable local and exact-head remote gates. This validation document remains conditional while either gate is outstanding. Phase 23 remains unstarted and owner-controlled at `/gsd-discuss-phase 23`.
