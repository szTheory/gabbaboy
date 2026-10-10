---
phase: GB-02-dmg-cpu-bus-and-time
observed: 2026-10-06
status: failing
pr_head: a91d8e72a9dff186f342cf487a70b91b17f3193d
---

# Phase 2 hosted qualification

[Draft PR #2](https://github.com/szTheory/gabbaboy/pull/2) is stacked on Phase 1 PR #1. The exact PR head above has completed failing checks. This is additional evidence after the initial goal report, not a passing remote qualification or a reason to advance.

## Native and sanitizer run

[PR CI run 37536888483](https://github.com/szTheory/gabbaboy/actions/runs/37536888483) reports:

| Job | Result | Executed tests | Failure detail |
|---|---|---|---|
| native-linux-x64 | failure | 95/99 pass | Four known corpus failures at unsupported LY |
| native-macos-arm64 | failure | 95/99 pass | Same four corpus failures |
| linux-asan-ubsan | failure | 90/94 pass | Same four corpus failures; no sanitizer finding marker in the inspected failed-step logs |
| cmake-floor-3.25.3 | failure | 90/94 pass | Same four corpus failures; helper stops before install/relocation |
| native-windows-x64 | failure | 93/99 pass | Runner returns `invalid-manifest`: missing-fixture/bad-digest negative controls fail for the wrong reason, and the four corpus tests fail |
| required-native | failure | aggregate | Correctly rejects failed evidence jobs |

Native Linux/macOS and Windows installed consumer cases pass, but no full native suite passes. PR jobs build GitHub's test merge revision; check runs are associated with the named PR head. Local normal/sanitizer evidence remains tied to source `c583e33`.

Windows manifest rejection is a separate portability gap. The runner hashes exact raw manifest bytes. Checkout line endings are a plausible cause, but the actual Windows manifest bytes have not been captured, so that cause is not confirmed. Plan a deterministic byte-preservation check and retain strict invalid-manifest controls rather than weakening validation.

## Fixture reproduction run

[PR fixture run 37536888492](https://github.com/szTheory/gabbaboy/actions/runs/37536888492) completes with `fixture-repro` success for the original tracer and `mooneye-fixture-repro` failure. The earlier equivalent [run 37536827063](https://github.com/szTheory/gabbaboy/actions/runs/37536827063) log verifies pinned WLA-DX versions and the replacement font digest, then `cmp` reports that DAA differs at byte 335 (the first global checksum byte). It stops before the timer comparisons.

Earlier local byte-reproduction claims do not establish cross-host reproduction. The recipe/tool/source/build differences must be investigated; do not update stored digests or bytes merely to match one failing build. Preserve provenance and guest logic, compare all differing bytes, and qualify a deterministic pinned recipe. This gap is independent of the unsupported LY completion path.

## Route

The five initial core/corpus findings plus these Windows and reproduction gaps block Phase 2. Keep all CPU requirements pending. Next command: `$gsd-plan-phase 2 --gaps`. Phase 3 — Visible Interactive DMG — remains paused.
