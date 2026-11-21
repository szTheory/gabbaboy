---
phase: GB-22-composition-and-microtest-evidence
reconstructed: 2026-11-13
status: passed
score: "3/3 historical approved-scope criteria"
source_head: d18db4c56d2a79e6138df37a9d16e3d346a86e13
implementation_head: ca2f0be6b38e7dd22e0eb3296b9a21cceed1a765
implementation_tree: e768b7ec26d7c07542d6aa29aef53ae8fc826c5e
evidence_head: d18db4c56d2a79e6138df37a9d16e3d346a86e13
report_kind: boundary_reconstruction
current_freshness: not_evaluated
metadata_cases: 513
shared_macro_cases: 480
inline_cases: 2
initial_no_protocol_exclusions: 31
blocked_protocol_candidates: 482
admitted: 0
executed: 0
unresolved_gates:
  - acid2_derivative_build_reproducibility
  - acid2_component_rights_and_output_scope
  - acid2_profile_applicability
  - gbmicrotest_component_rights_and_output_scope
  - gbmicrotest_prebuilt_rom_sha256
  - gbmicrotest_case_applicability
  - gbmicrotest_independent_oracle
requirements_satisfied: []
requirements:
  FIXT-01: pending
  RIGHTS-01: pending
  DIAG-01: pending
  DIAG-02: pending
requirement_dispositions:
  - id: FIXT-01
    status: Pending
    original_owner: Phase 21
  - id: RIGHTS-01
    status: Pending
    original_owner: Phase 20
  - id: DIAG-01
    status: Pending
    original_owner: Phase 22
  - id: DIAG-02
    status: Pending
    original_owner: Phase 22
---

# Phase 22: Synthetic Composition and Diagnostic Gate Assessment Verification

**Historical reconstruction of the owner-approved synthetic-plus-metadata scope from immutable Phase 22 evidence; no current execution or milestone closure is claimed.**

## Historical Reconstruction Scope

This report reconstructs Phase 22's revised D-141 acceptance contract from the immutable evidence record at [`d18db4c56d2a79e6138df37a9d16e3d346a86e13`](22-EVIDENCE.md). The implementation merge is [`ca2f0be6b38e7dd22e0eb3296b9a21cceed1a765`](22-EVIDENCE.md), whose tree is `e768b7ec26d7c07542d6aa29aef53ae8fc826c5e`. The recorded PR #142 source head was `9cb92b0f344b884d5f3e7179740ff5bc87eae379`; that object is unavailable locally, so this report treats it only as a historical citation from the evidence record.

The selected historical evidence boundary contains the completed synthetic tracer, source-bound metadata assessment, C1 sanitizer correction, review records, and exact-head qualification results. Phase 22's implementation-merge evidence had still marked PR #142 qualification as pending; the later immutable evidence record documents the final PR #142 qualification. This report uses the later record for historical outcomes and does not imply that any source, test, remote check, artifact, review, or game observation was rerun for this reconstruction.

The assessment contains 513 named metadata cases: 480 shared-macro cases, two inline cases, and 31 initial no-protocol exclusions. The 482 protocol candidates remain blocked. Seven admission gates remain unresolved, admitted is zero, and executed is zero. The 31 initial exclusions and 482 blocked protocol candidates are metadata classifications, not completed diagnostic-suite accounting; final eligible/executed/excluded accounting remains incomplete. No upstream diagnostic payload was fetched, retained, built, run, admitted, or claimed.

## Goal Achievement

The historical score below applies only to the three revised Phase 22 roadmap criteria accepted under D-141. It does not mark the original DIAG requirements complete and does not close the v0.4 milestone.

| Phase 22 roadmap criterion | Historical status | Evidence and limits |
|---|---|---|
| 1. The original synthetic composition tracer runs through the compiled runner with its fixed source-cell mask, exact unmasked comparison, and negative controls for altered identities, masks, and images. | **VERIFIED** | The original compiled synthetic tracer, source-cell mask, identity, and image controls are recorded in [22-01-SUMMARY.md](22-01-SUMMARY.md) and [22-EVIDENCE.md](22-EVIDENCE.md). The recorded `phase22_acid2_tracer`, `phase22_acid2_contract`, and `phase22_acid2_controls` checks exercise this synthetic path; the final configured suite is recorded as 1,732/1,732 at the historical PR #142 head. These checks establish controlled synthetic composition only, not game, physical-hardware, glyph-accuracy, or mode-3 timing results. |
| 2. A source-bound metadata-only inventory retains all 513 named gbmicrotest source/ROM pairs and records each unresolved acid2/gbmicrotest admission gate; the approval command refuses while required evidence is unresolved. | **VERIFIED** | [22-02-SUMMARY.md](22-02-SUMMARY.md), [22-10-SUMMARY.md](22-10-SUMMARY.md), [22-11-SUMMARY.md](22-11-SUMMARY.md), [22-12-SUMMARY.md](22-12-SUMMARY.md), [22-SOURCE-AUDIT.md](22-SOURCE-AUDIT.md), and [22-EVIDENCE.md](22-EVIDENCE.md) record the 513-name inventory, seven unresolved gates, 482 blocked protocol candidates, 31 initial exclusions, admitted=0, and executed=0. The recorded assessment check passes for the metadata-only result, while `--require-approved` correctly refuses with exit 2 and all seven gates. No real fixture was approved or executed, and the complete suite accounting remains unresolved. |
| 3. Documentation and automated checks keep the tracer labeled synthetic-only, record the real-fixture no-go without asserting a license prohibition, and leave DIAG-01, DIAG-02, and RIGHTS-01 Pending. | **VERIFIED** | The public-claim and immutable-evidence controls are recorded in [22-10-SUMMARY.md](22-10-SUMMARY.md), [22-11-SUMMARY.md](22-11-SUMMARY.md), [22-12-SUMMARY.md](22-12-SUMMARY.md), and [22-EVIDENCE.md](22-EVIDENCE.md). They retain synthetic-only claims, all seven unresolved admission gates, zero admissions/executions, and the original Pending requirements. Missing evidence is not represented as a license prohibition or as fixture permission. |

**Historical approved-scope score: 3/3 criteria.** The score records the completed synthetic-plus-metadata scope and its refusal behavior only. The original DIAG-01, DIAG-02, and RIGHTS-01 requirements remain Pending; FIXT-01 also remains Pending under its original owner. Full milestone closure remains unsatisfied.

## Recorded Qualification Evidence

The immutable evidence record describes the final PR #142 local qualification as configure, build, and the full configured suite passing 1,732/1,732 in 1,424.19 seconds at recorded source head `9cb92b0f344b884d5f3e7179740ff5bc87eae379`. Required exact-head CI, fixture-reproduction, package artifacts, reviews, protection checks, and merge-tree identity are recorded as passing before the squash merge at `ca2f0be6b38e7dd22e0eb3296b9a21cceed1a765`. The record also documents the later C1 correction and fresh reviews. These are outcomes preserved by the immutable evidence record, not fresh checks performed while writing this report.

The detailed local checks, source identities, and recorded outputs are in [22-EVIDENCE.md](22-EVIDENCE.md), with plan-level records in [22-01-SUMMARY.md](22-01-SUMMARY.md), [22-02-SUMMARY.md](22-02-SUMMARY.md), [22-10-SUMMARY.md](22-10-SUMMARY.md), [22-11-SUMMARY.md](22-11-SUMMARY.md), and [22-12-SUMMARY.md](22-12-SUMMARY.md). The source coverage, seven-gate roster, and dispositions are in [22-SOURCE-AUDIT.md](22-SOURCE-AUDIT.md).

## Exact Game No-Go Facts

Potion Panic's creator-linked repository failed before a ref/commit was returned, and its fork is not source authority. Its source, build, ROM, header, mode, predicate, and observations remain unobserved.

For µCity 1.3, source `d1880a2a112d7c26f16c0fc06a15b6c32fdc9137` was inspected, but the required `source/engine/hardware.inc` lacks an identified grant/notice under the recorded scope. No upstream tool or ROM ran, and no ROM, header, mode, predicate, or receipt was produced. These are missing-evidence no-go outcomes; they establish neither a license prohibition nor permission.

## Requirement Truth and Preserved Limits

| Requirement | Original owner | Historical disposition | Evidence limit |
|---|---|---|---|
| FIXT-01 | Phase 21 | Pending | The two bounded game-candidate attempts stopped before source/build, ROM digest, header, native-mode, predicate, and observation facts were established. |
| RIGHTS-01 | Phase 20 | Pending | No fixture was admitted and no candidate-specific grant scope was established. No license prohibition or permission is inferred. |
| DIAG-01 | Phase 22 | Pending | The metadata-only assessment does not provide an admitted acid2 derivative, build/provenance, or rights evidence. |
| DIAG-02 | Phase 22 | Pending | Metadata names do not provide admitted case bytes, rights, model applicability, or complete eligible/executed/excluded accounting. |

The root MIT license remains unchanged. Evidence is limited to synthetic composition and metadata; it does not establish physical hardware behavior, perceptual results, mode-3 timing, broad game compatibility, or per-case hardware applicability. Linux and Steam Deck player support and live Playstead integration remain unqualified. No source absence is treated as a license prohibition, and no public MIT statement is treated as fixture permission.

The historical Phase 20 and Phase 21 verification reports and the milestone audit snapshot were not rewritten or refreshed. The execution-start audit recorded Phase 20 and Phase 21 verification as stale and Phase 22 verification as missing. This reconstructed report supplies the missing historical Phase 22 report only; it does not refresh the other reports or assert current runtime freshness. The current runtime freshness verdict is not evaluated by this historical report and must remain separate from the historical approved-scope score.

## Boundary

Phase 22's owner-approved synthetic-plus-metadata scope is historically documented as complete at its recorded evidence boundary. The report does not satisfy FIXT-01, RIGHTS-01, DIAG-01, or DIAG-02, and full milestone closure remains unsatisfied. The separate D-103 exact-final-head full-suite milestone gate is not established by this reconstruction.
