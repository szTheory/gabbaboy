# AGE eligibility

## Evidence class

The upstream `Verified:` lines are author-attested hardware observations. They
are not reproducible receipts, and this repository has not independently tested
physical hardware. The target model is CGB-E. Reference PNGs are pinned source
data for the later automated pixel oracle; no human screenshot judgment is used.

`expected_role` records the D-19 expectation in `12-CONTEXT.md`; final
dispositions are decided by measurement on the committed core. A measured
failure of a pass target may be retained only as a named expected failure with
its reason. The three single-speed controls failed on the pre-phase core per
research and are re-measured.

## Scope and exclusions

The AGE warning is preserved verbatim, with its emulator-only context recorded
in `SOURCES.md`. Phase 14 admits six source-bound mode-3 ROM/reference pairs:
native and DMG-compatibility LCDC/SCX cases at normal speed, plus separately
identified native double-speed LCDC/SCX siblings. Their upstream CGB-E
`Verified:` lines are expected outcomes, not emulator results; all six remain
admitted but unexecuted until the automated pixel checks in 14-09. The broader
single-speed corpus and `_in-progress/*` remain excluded.

Fixtures are repository test data only. They are not installed or packaged.
