# Phase 22: Composition and Microtest Evidence - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in `22-CONTEXT.md` — this log preserves the alternatives considered.

**Date:** 2026-11-02
**Phase:** 22-Composition and Microtest Evidence
**Areas discussed:** Acid2 independent oracle and derivatives, text mask scope, gbmicrotest cohort/model applicability/accounting

---

## Acid2 independent oracle and derivatives

| Option | Description | Selected |
|--------|-------------|----------|
| Pinned upstream reference with an explicit text mask | Uses the upstream fixed reference, leaves all unmasked pixels independently checked, and avoids another emulator dependency. | ✓ |
| Independent source-derived compositor | Could provide a separate expected image for replacement glyphs, but duplicates PPU behavior under test and expands the oracle. | |
| Second-emulator capture | Useful for debugging, but imports another emulator's model/version assumptions and is not hardware truth. | |

**User's choice:** The owner asked for parallel role-relevant review, primary-source research, an adversarial pass, and automatic adoption of the coherent recommendation. We applied the pinned upstream reference with explicit mask recommendation.
**Notes:** Use original project-authored replacement glyphs and pin immutable source/build inputs, derivative ROM, reference, and rights. The existing `mgblib` font rights gate remains open; replacement alone does not clear code/art/reference rights.

---

## Text mask scope

| Option | Description | Selected |
|--------|-------------|----------|
| Fixed text-band rectangles | Simple, but may mask adjacent composition and hide rendering defects. | |
| Source-anchored tile-cell allowlist | Keeps the mask readable and tied to the pinned source layout; generate a reviewable pixel mask/overlay and bound its area. | ✓ |
| Hand-edited full-resolution mask | Precise in principle, but opaque and vulnerable to unreviewed broadening or drift. | |

**User's choice:** Apply the synthesized recommendation automatically, per the owner's instruction.
**Notes:** Compare all pixels outside the exact text cells; mask identity changes and an unmasked one-pixel mismatch need automated negative controls. Text rendering itself remains outside the claim.

---

## gbmicrotest cohort, model applicability, and accounting

| Option | Description | Selected |
|--------|-------------|----------|
| Pinned upstream inventory with shared-verdict cohort | Preserve the exact source/ROM roster, run the shared-verdict candidates after rights/model review, and explicitly account for the remaining cases. | ✓ |
| Curated subsystem slice | Smaller, but the upstream has no per-case categories, so selection risks an arbitrary denominator. | |
| Defer admission pending rights/model review | Safest if gates remain unresolved, but requires scope resolution because the phase would not deliver DIAG-02. | |

**User's choice:** Apply the pinned-inventory recommendation, conditional on the adopted rights and applicability gates.
**Notes:** At the candidate commit `463eb6bc0fe31d61781ef63060ad6d74090c0255`, research found 513 source/ROM pairs, with 482 shared-verdict candidates and 31 cases requiring explicit exclusions or separate oracle review. The upstream's suite-wide DMG-CPU-08 statement is uncertain; comparisons on GabbaBoy DMG-CPU-B are diagnostic only, and no CGB-CPU-E applicability is inferred. The MIT source license does not by itself clear generated ROM or embedded-logo rights. The upstream build script does not pin WLA-DX, so no reproducible build claim is made without a pinned build closure.

---

## the agent's Discretion

- Choose the manifest schema, report field names, checker organization, mask encoding/overlay generation, and plan split within the Phase 22 cap.
- Reuse existing CMake/CTest and Python standard-library patterns; no added dependency without a demonstrated need.
- Keep all rights, exact identity, and model-applicability gates fail-closed.

## Deferred Ideas

None.
