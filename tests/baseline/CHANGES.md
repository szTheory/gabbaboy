# DMG-CPU-B baseline change record (D-34)

`tests/baseline/dmg-cpu-b-v1.txt` is the frozen DMG-CPU-B regression ledger (EVID-02). The CTest
`dmg_baseline` recomputes every observation and fails if any frozen line differs. This file is the
only way a frozen line may legitimately change.

## Protocol

- There is no update mode. `bash tests/scripts/verify-dmg-baseline.sh --print-candidate` writes a
  candidate ledger to standard output only; a baseline moves only through a reviewed edit of the
  ledger together with one row below.
- A change lands in a dedicated commit whose subject starts `baseline:` and which touches nothing
  under `src/`. The source change that causes it lands in an earlier commit, so the reason and the
  evidence can be reviewed separately from the new bytes.
- Add exactly one table row per changed ledger line, oldest first, with these cells: key, old value,
  new value (`<absent>` for a line that was added or removed), reason, evidence class and citation,
  approver. Every cell is required. The evidence class is one of hardware-backed, differential
  oracle, metamorphic property, regression fixture, or private game observation, with a citation a
  reviewer can follow. A regression-class line alone is not evidence that the new bytes are right.
- The comparator reverse-applies the rows, newest first, to the ledger body and the result must
  reproduce `frozen_body_sha256`. A changed digest without a row fails as `unrecorded-change`; a row
  that does not match the ledger fails as `changes-inconsistent`; a row with equal old and new
  values fails as `changes-noop`.
- Header keys (`schema`, `model`, `frozen_revision`, `frozen_date`, `frozen_body_sha256`,
  `coverage`) are not changed through this table. `bench.advisory.*` lines are provenance, not
  identity, and are never compared.
- Default for Phase 8 and Phases 11 and later: zero changed lines. Output for DMG must stay
  byte-identical to the ledger. A phase that must change a line records the row and its evidence
  first.

## Changes

| key | old | new | reason | evidence class and citation | approver |
| --- | --- | --- | --- | --- | --- |
