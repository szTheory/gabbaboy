# Phase 24: Resolve remaining v0.4 evidence and verification gaps - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in `24-CONTEXT.md` — this log preserves the alternatives considered.

**Date:** 2026-11-17
**Phase:** 24-Resolve remaining v0.4 evidence and verification gaps
**Areas discussed:** Additive verification evidence, Read-only candidate research, Phase exit with gaps, BOM normalization and plan-cap regression, post-T6 Acid2 mismatch, literal RIGHTS-01/DIAG-01/DIAG-02 reconciliation, FIXT-01 execution boundary, D-211 protected CI boundary and fresh recovery

---

## BOM normalization and plan-cap regression

| Option | Description | Selected |
|--------|-------------|----------|
| Strip one leading BOM and reject a repeated BOM | Normalize exactly one leading U+FEFF before the canonical frontmatter fence; fail closed if a second remains. | ✓ |
| Reject every BOM | Fail closed without normalization, which would reject BOM-prefixed plans accepted by the upstream reader. | |
| Decode all plan inputs with UTF-8-SIG | Centralize BOM removal at decoding, but changes multiple reader paths instead of the narrow classifier. | |

**User's choice:** The owner said to follow the bounded recovery recommendation after the fresh Critical review. This locks one same-plan correction and one clean independent review.

## D-206 bounded v0.4 closeout

The owner authorized a bounded closeout after asking how to finish the milestone and return to `main` through a PR. The decision reuses Phase 24's sole existing plan, preserves all eight original acceptance criteria and owners, uses only the named Potion Panic/µCity/Acid2/gbmicrotest sources, requires component-specific rights and notices before repository/public-CI staging, and spends one full exact-candidate PR CI matrix only after the candidate is frozen. Unresolved criteria remain Pending; no gap acceptance, extra plan/phase, broad local suite, additional full-CI retry, third lifecycle retest, release/tag/asset change, or unauthorized worktree removal is allowed. The exact route is `$gsd-execute-phase 24` after independent plan approval, then `$gsd-autonomous --from 24` for the remaining authorized milestone lifecycle.
**Notes:** The BOM policy stays local to the existing Python standard-library plan classifier. The independent advisor found that a repeated leading BOM must fail closed or it could remain unrecognized. Python's official [UTF-8-SIG codec documentation](https://docs.python.org/3.13/library/codecs.html#encodings.utf_8_sig) describes BOM handling at the start of the byte stream.

| Option | Description | Selected |
|--------|-------------|----------|
| Immutable production-CLI paired controls | Use the same BOM-prefixed Phase 24 plan path and fixture; vary only gap_closure true/false and require the specific D-205 gap refusal or ordinary-plan pass. | ✓ |
| Helper-only classifier control | Checks the parser helper but not immutable input, the D-205 rule, or CLI refusal behavior. | |
| Add a new CTest identity | Makes the gate surface larger despite an existing self-test and focused CTest. | |

**User's choice:** Follow the production-CLI regression recommendation and preserve the existing two CTest identities.
**Notes:** The negative must require the exact plan-cap-d205-phase24-gap refusal; the ordinary-plan twin must pass. Run only plan_cap and planning_hygiene_controls after cheap direct checks, retaining their existing timeout and control floor. A separate Critical or blocker found by the one fresh review returns the phase to the owner.

---

## Additive verification evidence

| Option | Description | Selected |
|--------|-------------|----------|
| Add focused current evidence additively | Write a commit-pinned point-in-time Phase 24 record, preserve the historical Phase 20/21 reports and stale statuses, and avoid the prohibited broad suite. | ✓ |
| Defer all freshness work to the final milestone gate | Leave the stale coverage unexplored until the exact-final-head D-103 gate. | |

**User's choice:** The owner selected this discussion area and instructed a multi-role fan-out with automatic adoption of the synthesized recommendation. The additive evidence recommendation was adopted.
**Notes:** Focused checks are not full Phase 20/21 re-verification. The broad-suite gate remains separate and unresolved.

---

## Read-only candidate research

| Option | Description | Selected |
|--------|-------------|----------|
| Repository records only | Use committed candidate and diagnostic records without new source-page research. | |
| First-party metadata for existing items | Consult only creator/upstream metadata for the existing candidates and diagnostic sources; do not fetch payloads, make a rights decision, or add candidates. | ✓ |

**User's choice:** The owner selected this discussion area and instructed automatic adoption of the synthesized recommendation. The bounded first-party metadata recommendation was adopted.
**Notes:** The Potion Panic creator page links to Codeberg and displays page-level license labels; linked Codeberg pages for Potion Panic and µCity could not be fetched by the browser. The µCity GitHub v1.3 release page exposes tag metadata and a short commit prefix. These observations do not establish payload identity, component rights, or permission.

---

## Phase exit with gaps

| Option | Description | Selected |
|--------|-------------|----------|
| Require original requirement criteria to be satisfied | Keep Phase 24 blocked until the four Pending requirements meet their original evidence criteria, which needs separate fixture/rights authority and more evidence. | |
| Complete the bounded reassessment with gaps retained | Complete Phase 24 only when its additive evidence map and controls pass; keep all four requirements Pending and v0.4 open. | ✓ |

**User's choice:** The owner selected this discussion area and instructed automatic adoption of the synthesized recommendation. The bounded reassessment recommendation was adopted.
**Notes:** Phase completion does not imply requirement satisfaction or milestone completion. The existing 40-plan total ceiling remains in force; Phase 24 has one plan slot.

---

## the agent's Discretion

- Choose existing focused CTest targets based on the covered files and claims touched by the one plan; keep identities stable and run cheap checks first.
- Use exact-commit evidence and automated negative controls to prevent false requirement-completion or milestone-closure claims.
- Reuse existing Python standard-library and CMake/CTest patterns; add no dependency without demonstrated need.

## Deferred Ideas

- Candidate-specific rights determination and any fixture/source payload acquisition, build, run, or admission require separate explicit authorization.
- The D-103 exact-final-head broad suite and v0.4 milestone archival remain separate owner-controlled gates.

---

## Post-T6 results and original-criterion reconciliation (2026-11-17)

The owner directed a full fan-out across the relevant product, rights/security, emulator/rendering, QA, architecture, and operations perspectives, and asked to follow the synthesized recommendations. Read-only source inspection and three independent criterion reviews completed. No code implementation edits, tests, emulator runs, or rights outreach occurred in this discussion.

### Acid2 mismatch: preserve the failure, separate the criterion

| Option | Description | Selected |
|--------|-------------|----------|
| Require all three profile comparisons to pass DIAG-01 | Treat the 19,840/19,840 DMG-on-CGB mismatch as a blocker for the original requirement. This matches the active plan's stricter gate but adds a condition absent from the original criterion. | |
| Apply DIAG-01 literally; track the cross-model result separately | Keep the mismatch as a failed runtime result; reconcile the requirement against admitted derivatives, glyph replacement, text mask, provenance, rights, and composition labeling. Do not claim a cross-model pass or timing qualification. | ✓ |
| Rerun, modify the mask, or change the reference | Could produce more diagnostic information but repeats a prohibited Acid2 run or changes independently pinned evidence. | |

**Owner direction:** Follow the literal-criterion recommendation. The exact DMG-on-CGB comparison remains failed. Static inspection found the recorded fixed DMG compatibility palette has no colors in common with the pinned CGB reference after RGB expansion, which can explain the all-pixel result through color encoding. Because the temporary rendered PPM was deleted and no pixel map is retained, that explanation is an inference, not a verified geometry diagnosis. The active plan's all-profile match gate must be explicitly reconciled before formal DIAG-01 status promotion; no replay, mask/reference edit, or core fix is authorized.

### RIGHTS-01 and DIAG-02

| Requirement | Option selected | Scope and boundary |
|---|---|---|
| RIGHTS-01 | Mark Complete in formal reconciliation using the admitted diagnostic alternative under D-207. | Applies only to exact admitted Acid2/gbmicrotest diagnostic components and recorded notices/package exclusions; it does not clear unadmitted games or other cases. D-207 is an owner-accepted bounded interpretation. |
| DIAG-02 | Mark Complete in formal reconciliation for the selected case and roster accounting. | One eligible/executed `div_inc_timing_a` case, 512 explicit exclusions, exact source/bytes/terms, and DMG-CPU-B software scope; no full-suite or hardware claim. |

**Owner direction:** Adopt both literal-criterion recommendations and retain their original Phase 20/22 owners. The tracker remains unchanged until the authorized formal reconciliation updates all linked records consistently.

### FIXT-01 remains the blocking owner decision

| Option | Description | Selected |
|--------|-------------|----------|
| Preserve FIXT-01 and stop with the gap visible | Keep it Pending because neither named candidate has all required build/ROM/header/mode/runtime evidence. Keep excluded inputs excluded and v0.4 open. | ✓ |
| Treat current no-go records as satisfying FIXT-01 | Would claim evidence the criterion explicitly requires but the records do not contain. | |
| Expand or relax the candidate/acceptance scope | Changes the original requirement boundary or requires using excluded material; needs a separate explicit owner decision. | |

**Owner direction:** Follow the recommendation to preserve the original criterion and Pending disposition, leaving v0.4 open. Task 7 cannot start under the current plan. No third candidate, excluded converter, unlicensed `hardware.inc`, or other gap acceptance is inferred. Revisit only if the owner later directs a material change to the FIXT-01 acceptance/scope policy.

**Additional closeout note:** `THIRD_PARTY_NOTICES.md` still contains a pre-T6 sentence saying no Acid2 comparison occurred; update it to the recorded three-profile result during any later authorized closeout. Keep the fixed compatibility palette and reference fixture untouched in the meantime.

---

## D-206 bounded closeout authorization (2026-11-16)

| Lens | Evidence / risk | Adopted direction |
|---|---|---|
| Product | The v0.4 acceptance criteria already name a bounded game pair and diagnostic sources. | Keep the original eight criteria and requirement owners; no candidate expansion or gap acceptance. |
| Rights/security | Page labels do not establish every embedded component grant; unreviewed binaries or submodules can cross the public-repository/CI boundary. | Check pinned component terms/notices first; admit only exact, rights-supported payloads. Record no-go without inferring a license ban. |
| Architecture | Existing fixture admission, CGB candidate, RGBDS, acid2 mask, diagnostic, and immutable evidence tooling already cover most seams. | Extend existing standard-library/CMake/CTest paths; add no dependencies and reuse the existing Phase 24 plan. |
| QA | Phase 20/21 reports are historical and current GSD freshness is stale; focused checks and the final suite prove different things. | Add causal negatives, keep evidence labels distinct, run cheap checks first, and use one exact final-head CI matrix for D-103. |
| Operations | Opening the current branch as a PR triggers full CI; no current PR can safely precede the closeout. | Open the PR only after the final candidate and evidence are ready; merge after independent review and required checks, then verify clean `main`. |

**Owner choice:** “Authorize bounded closeout.” D-206 records reuse of the sole Phase 24 plan, the exact named candidate set, component-level rights review, one final required CI matrix, and the 40-plan ceiling. Existing Phase 24 evidence remains historical; no requirement is complete until its original criterion passes.

**Research already underway:** canonical Potion Panic and µCity source refs and exact µCity v1.3 commit were confirmed from upstream metadata. Acid2 v1.0/v1.1 and pinned gbmicrotest root LICENSE files are MIT, but these labels do not alone resolve font, image, ROM-header, or build-input scope. Those components remain under review.

## D-211 protected CI boundary and fresh recovery (2026-11-17)

| Lens | Evidence / risk | Adopted direction |
|---|---|---|
| Product | Avoid widening the original v0.4 requirements or adding game compatibility claims. | Permit only already-admitted fixture ROM cases in the existing required PR matrix. |
| Emulator QA | The Acid2 cross-model comparison is a recorded failure and must not replay. | Keep `phase22_admission_assessment` static; Acid2 remains excluded from all execution. |
| Security / test integrity | WR-01 double-counts positives as negatives and repeats one positive. | Count only rejected overlay cases and remove the redundant positive control. |
| Operations | Required CI cannot be bypassed; a new run after failure would exceed the bounded scope. | Allow one fresh exact-candidate review and one protected matrix; merge only the identical reviewed/tested head; any blocker stops without retry. |
| Architecture | The existing checker and sole plan already provide the right seams. | Reuse them without a dependency, new CTest identity, fixture, or local ROM run. |

**User's choice:** The owner said “follow your recommendations,” authorizing the revised bounded recovery. D-211 supersedes D-210 only for the existing protected matrix's already-admitted game/fixture ROM execution and the new one-review/one-matrix allowance. Task 7, Phase 24 verification, milestone audit/archive, requirement changes, broad local suite, Acid2 replay, and release changes remain unauthorized.

**Next route:** `$gsd-plan-phase 24` to replan the same `24-01-PLAN.md`; then execute only the D-211 correction task. The current recovery checkout remains active until the protected merge is reconciled to clean `main`.

## 2026-11-17 — D-209 owner closeout decision

The owner chose to close v0.4 with remaining gaps recorded, rather than keep the milestone open for FIXT-01. The original tracker now completes RIGHTS-01, DIAG-01, and DIAG-02 for the exact admitted diagnostic scope; FIXT-01 remains Pending. The Acid2 cross-model comparison stays failed (19,840/19,840 differing pixels) and was not replayed. Phase 24 Task 7 and D-103's exact-final-head suite remain incomplete; stale verification is disclosed. Recommend `$gsd-new-milestone` for v0.5 DMG PPU Timing.
