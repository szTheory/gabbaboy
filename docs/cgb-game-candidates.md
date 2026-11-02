# CGB game-candidate evidence contract

The candidate contract fixes the only two identities and their order: Potion Panic (GB Compo
2025) first, followed by µCity 1.3's `preferred-ucity.gbc` only after a final Potion Panic no-go.
This checker validates evidence accounting; it does not grant rights, establish compatibility, or
admit candidate bytes to product packages.

## Immutable contract inputs

Every check resolves one full `--source-revision` commit and reads the candidate checker,
Phase 20 admission checker, CMake registration and this contract from that commit. The checker
requires its executing source files to match those immutable blobs. Candidate records are mutable
inputs and may be staged during an attempt, but their project source and receipt references remain
bound to the selected commit.

Run the synthetic contract controls with:

```sh
python3 -I tests/scripts/verify-cgb-candidates.py --self-test --repo-root . \
  --source-revision "$(git rev-parse HEAD)"
```

Inspect one stage or both fixed records with `--check-record PATH` or `--check-all`. An in-progress
record must state `partial: true` and its current `stage`; `--require-final` rejects every partial
record. The record paths are fixed at `tests/data/cgb-candidates/potion-panic.json` and
`tests/data/cgb-candidates/ucity-1.3.json`.

## Cutoff and absence semantics

A stage that has not run is represented explicitly as `not_observed`, with the earlier gate and a
concrete reason. No digest, cartridge header, execution mode, predicate result or output is
invented for a field beyond that cutoff. A final no-go must name an evidence-backed rights, source,
build or predicate-feasibility cause. A reproduced harness, emulator or security defect is
`blocked-defect` and cannot close the candidate pair.

An admitted candidate must reference the exact Phase 20 manifest and adjacent immutable admission
pin. The candidate checker invokes `verify-fixture-admission.py --check-manifest` for that exact
manifest; it does not copy component-rights decisions into a second authority. Admission also
requires a source-qualified native-CGB progress result and its failing controls. Digests bind
observations for replay and do not establish rendering accuracy.

The fallback record is valid only after the primary no-go is fixed in an immutable commit and
referenced by the fallback. If the primary is admitted, the fallback may be `not-needed` and has no
invented ROM identity. No third candidate ID is accepted. Synthetic self-test records live only in
a temporary repository and are never candidate outcomes.
