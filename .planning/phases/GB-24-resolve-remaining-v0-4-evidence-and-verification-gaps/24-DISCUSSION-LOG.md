# Phase 24: Resolve remaining v0.4 evidence and verification gaps - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in `24-CONTEXT.md` — this log preserves the alternatives considered.

**Date:** 2026-11-16
**Phase:** 24-Resolve remaining v0.4 evidence and verification gaps
**Areas discussed:** Additive verification evidence, Read-only candidate research, Phase exit with gaps

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
