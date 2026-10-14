# AGE eligibility

## Evidence class

The upstream `Verified:` lines are author-attested hardware observations. They
are not reproducible receipts, and this repository has not independently tested
physical hardware. The target model is CGB-E. Tests report numeric results; no
screenshot comparison is used.

`expected_role` records the D-19 expectation in `12-CONTEXT.md`; final
dispositions are decided by measurement on the committed core. A measured
failure of a pass target may be retained only as a named expected failure with
its reason. The three single-speed controls failed on the pre-phase core per
research and are re-measured.

## Scope and exclusions

The AGE warning is preserved verbatim, with its emulator-only context recorded
in `SOURCES.md`. The Phase 11 dispositions keep `m3-bg-*` as `vendored: false`;
those ROMs remain excluded. Also excluded are `_in-progress/*`, `m3-bg-*-ds`,
the broader single-speed corpus, and `spsw-interrupts-cgbBC`.

Fixtures are repository test data only. They are not installed or packaged.
