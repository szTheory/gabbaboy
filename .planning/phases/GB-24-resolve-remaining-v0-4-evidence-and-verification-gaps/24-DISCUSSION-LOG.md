# Phase 24: Resolve remaining v0.4 evidence and verification gaps - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in `24-CONTEXT.md` — this log preserves the alternatives considered.

**Date:** 2026-11-16
**Phase:** 24-Resolve remaining v0.4 evidence and verification gaps
**Areas discussed:** Additive verification evidence, Read-only candidate research, Phase exit with gaps, BOM normalization and plan-cap regression

---

## BOM normalization and plan-cap regression

| Option | Description | Selected |
|--------|-------------|----------|
| Strip one leading BOM and reject a repeated BOM | Normalize exactly one leading U+FEFF before the canonical frontmatter fence; fail closed if a second remains. | ✓ |
| Reject every BOM | Fail closed without normalization, which would reject BOM-prefixed plans accepted by the upstream reader. | |
| Decode all plan inputs with UTF-8-SIG | Centralize BOM removal at decoding, but changes multiple reader paths instead of the narrow classifier. | |

**User's choice:** The owner said to follow the bounded recovery recommendation after the fresh Critical review. This locks one same-plan correction and one clean independent review.
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
