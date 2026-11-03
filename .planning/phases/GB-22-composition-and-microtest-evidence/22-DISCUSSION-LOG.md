# Phase 22: Composition and Microtest Evidence - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in `22-CONTEXT.md` — this log preserves the alternatives considered.

**Date:** 2026-11-02
**Phase:** 22-Composition and Microtest Evidence
**Areas discussed:** Acid2 independent oracle and derivatives, text mask scope, gbmicrotest cohort/model applicability/accounting

## Follow-up: Windows exact-head CI rescope

**Date:** 2026-11-03
**Area:** Resolve the required Windows CI failures on PR #142 without weakening Phase 22 evidence or verification.

| Option | Description | Selected |
|--------|-------------|----------|
| Bounded Windows repair and fresh exact-head qualification | Fix the reported Windows command/configuration and timeout failures while keeping all tests, assertions, budgets, branch protection, and Phase 22 no-go claims intact. | ✓ |
| Waive or skip failing Windows checks | Would leave required protected checks red and weaken the acceptance evidence. | |
| Broaden into general CI/test refactoring | Would exceed the observed failure set and approved bounded rescope. | |

**User's choice:** The owner answered “Yes, I approve” to a bounded Windows-CI rescope after the exact-head PR #142 failure was recorded. This authorizes a revised Phase 22 plan for the reported Windows failures; it does not authorize a check waiver or reset prior review/fix/gap history.
**Notes:** PR head `46c6696e57299be9601e88c17f0a19709a7f7367` passed the local 1,732-test suite, while Windows CI failed ten tests: seven CGB progress/history self-tests with `self-test-source-history-git-init-failed`, `phase22_evidence_contract` with `expected-test-policy-failed`, `phase22_evidence_controls` at 58.81 seconds under its 60-second timeout, and `planning_labels_controls` on the configured build-directory reference. The preview failure was an aggregation consequence of required CI and produced no independent preview artifact. The exact job/run details are in `build/phase22/remote-evidence.json`.

## Final C1 OSC diagnostic finding and review limit

**Date:** 2026-11-03
**Area:** Resolve the C1 OSC payload leak found after D-142's final review.

| Option | Description | Selected |
|--------|-------------|----------|
| One-time scoped fix and independent review | Amend existing 22-12 in place to fix and test the `U+009D … U+009C` OSC payload leak, then obtain one fresh independent review. Keep all prior review/gap counts, preserve the 12-plan cap, and stop if another blocking finding remains. | ✓ |
| Keep Phase 22 stopped | Make no further source changes after the original review cap and leave the C1 finding for a future owner-selected scope. | |

**User's choice:** The owner asked for the recommendation and authorized it. The recommendation was one additional fix-and-independent-review cycle limited to the C1 OSC payload leak, with an in-place amendment to 22-12. This is a one-time Phase 22 exception; it does not reset the two-round cap or the used gap round.
**Notes:** If the C1 correction passes review, continue the already approved Phase 22 local and exact-head PR qualification. Any further blocking correctness/security finding returns to owner scope resolution. No new plan, gap round, check waiver, fixture admission, or Phase 23 work is authorized.

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
