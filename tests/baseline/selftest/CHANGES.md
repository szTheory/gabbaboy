# Synthetic CHANGES table for the baseline comparator self-tests

This file is a fixture, not a record of real baseline changes. The real table is
`tests/baseline/CHANGES.md`. Rows are appended oldest first; the comparator reverse-applies them
newest first to the ledger body and the result must reproduce `frozen_body_sha256`.

The single row below is used only by the `dmg_baseline_changes_recorded` variant, which changes
`acceptance.libbet.pcm_sha256` in a generated ledger copy. The configure step copies this header
without the row for every other variant.

| key | old | new | reason | evidence class and citation | approver |
| --- | --- | --- | --- | --- | --- |
| acceptance.libbet.pcm_sha256 | aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa | bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb | synthetic self-test change | regression fixture (self-test only) | self-test |
