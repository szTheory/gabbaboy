# Phase 13 continuation

Completed stage: **Phase 13: CGB HDMA, planning** (2026-10-14).
Next stage: **Phase 13: CGB HDMA, execution** — **`/gsd-execute-phase 13`**.

12 plans / 24 tasks / 10 waves are independently checked. Read `13-PLAN-CHECK.md`, `13-PLAN-COVERAGE.md`, `13-RESEARCH.md` and `13-VALIDATION.md`. Execute `13-01-PLAN.md` first: actual-transfer conservation, bus order, outputs and partitions must pass before expansion. The research probe demonstrates the CPU/PPU seam, not implemented DMA or physical timing.

Use the recorded policies and source pins. CGB-07, fixture admission and HDMA implementation remain pending. Mealybug remains optional G1/CGB-C evidence. Physical UNKNOWNs are limits, not owner UAT. D-069 zero routine human UAT, D-096 flat dependencies, D-098 and GB-GSD-017/018 apply. GSD-specific producer proof runs automatically locally; native CI adds no GSD/Node install.

Phase 12 PR #68 is merged; its completed UAT stays closed absent changed covered behavior or contradictory evidence. Branch: `gsd/phase-13-cgb-hdma`. Preserve the owner's unstaged model/runtime config edits.

Both auto-advance flags remain false. Stop before execution. Phase 14: CGB-E Model Qualification and Corpus remains unstarted.
