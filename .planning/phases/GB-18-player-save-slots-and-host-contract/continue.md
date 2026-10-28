# Phase 18 continuation

Completed stage: **Phase 18 discussion**. [18-CONTEXT.md](18-CONTEXT.md) records decisions D-01..D-31, adopted as D-114. They came from six parallel advisor tracks plus an independent adversarial review. [18-DISCUSSION-LOG.md](18-DISCUSSION-LOG.md) keeps the alternatives that were considered.

Phase 17 boundary: PR130 was squash-merged to main as `f4082a6`. Its tree is identical to the verified head `605eb8f`, where exact-head CI passed 33/33 required checks with 11 path-skipped. The Phase 18 branch `gsd/phase-18-player-save-slots-and-host-contract` starts from `f4082a6`.

Next stage: **Phase 18 — Player Save Slots and Host Contract, planning**. Command: `/gsd-plan-phase 18`, run only when the owner chooses.

Constraints:
- Cap 10: 8 primary plans plus 1 gap slot.
- The only core/API change allowed is `gbb_get_input_clock` (D-24).
- The v0.3.0 release-please PR stays unmerged, with no VERSION bump.
- No release workflow edits.
- RM-027, WR-C03 and the `candidate-performance` re-citation stay Phase 19 entry blockers.
- Both automatic advance flags stay false.
