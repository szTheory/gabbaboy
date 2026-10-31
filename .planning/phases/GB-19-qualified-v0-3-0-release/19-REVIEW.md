---
phase: GB-19-qualified-v0-3-0-release
reviewed: 2026-10-31T15:01:32Z
depth: standard
files_reviewed: 73
files_reviewed_list:
  - .github/ci-timeouts.json
  - .github/scripts/release-evidence-lifecycle.sh
  - .github/scripts/verify-published-release-assets.py
  - .github/scripts/verify-release-source-proof.py
  - .github/scripts/verify-test-inventory.sh
  - .github/scripts/verify-workflow-policy.py
  - .github/workflows/ci.yml
  - .github/workflows/libbet-repro.yml
  - .github/workflows/preview.yml
  - .github/workflows/release-please.yml
  - .github/workflows/release-rehearsal.yml
  - .github/workflows/release.yml
  - .github/workflows/version-pr-gate.yml
  - .release-please-manifest.json
  - CHANGELOG.md
  - CMakeLists.txt
  - README.md
  - cmake/CheckContractRevWiring.cmake
  - cmake/ExpectedTests.cmake
  - cmake/ResolveContractRevision.cmake
  - docs/native-integration.md
  - docs/preview.md
  - docs/release.md
  - docs/state-format.md
  - docs/support/unreleased.md
  - docs/support/v0.3.0.md
  - src/core/gabbaboy.c
  - tests/CMakeLists.txt
  - tests/baseline/perf-attribution-v1.json
  - tests/baseline/state-goldens-v1.json
  - tests/ci/test-budget-allowlist
  - tests/cmake/ci-lanes.cmake
  - tests/cmake/host-contract.cmake
  - tests/cmake/hygiene.cmake
  - tests/cmake/perf.cmake
  - tests/cmake/save-formats.cmake
  - tests/data/release-api/SOURCES.md
  - tests/data/release-api/captured.json
  - tests/data/release-api/v030-draft-association-restoration.json
  - tests/data/release-api/v030-notes-failure.json
  - tests/data/release-lifecycle-post-tag-coverage.json
  - tests/data/state-compatibility.json
  - tests/data/state-forks.json
  - tests/data/support-claims-v0.3.json
  - tests/data/workflow-policy-controls.json
  - tests/expected-tests.txt
  - tests/player/CMakeLists.txt
  - tests/scripts/run-perf-gate.sh
  - tests/scripts/test_installed_host.py
  - tests/scripts/verify-changelog-heading.py
  - tests/scripts/verify-doc-links.py
  - tests/scripts/verify-judge-outcome.py
  - tests/scripts/verify-no-interop-claims.py
  - tests/scripts/verify-perf-gate.py
  - tests/scripts/verify-phase3-player.sh
  - tests/scripts/verify-planning-hygiene.py
  - tests/scripts/verify-release-lifecycle.py
  - tests/scripts/verify-state-contract.py
  - tests/scripts/verify-state-forks.py
  - tests/scripts/verify-state-mutants.py
  - tests/scripts/verify-state-pins.py
  - tests/scripts/verify-support-ledger.py
  - tests/scripts/verify-v02-adoption.py
  - tests/scripts/verify-v02-consumers.py
  - tests/scripts/verify-v02-delivery.py
  - tests/scripts/verify-v02-fuzz.py
  - tests/scripts/verify-v02-performance.py
  - tests/scripts/verify-v03-dispositions.py
  - tests/scripts/verify-version-window.py
  - tests/scripts/verify-workflow-policy-coverage.py
  - tests/test_cgb_profile.c
  - tests/test_state_codec.c
  - tests/test_state_fork.c
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
status: clean
review_base: f80bdf54c6c7d81e8e21f0275b43cda6edf6c8c4
review_head: d2c0dc95ecc7c5eb34a85bdc541f5ac3918190dc
prior_review_head: 535cdf796cccaf22520fa7b1f85c6d69c31af00c
prior_review_report_commit: acc4049f
post_tag_diff_base: d61a25ea54364e0e26ef89bb7467c72089361d49
scope_resolution: degraded
bounded_rescope_base: 0953f61951732951dcc655527655e0a5ec2d6d36
bounded_rescope_head: d2c0dc95ecc7c5eb34a85bdc541f5ac3918190dc
---

# Phase GB-19: Code Review Report

**Reviewed:** 2026-10-31T15:01:32Z
**Depth:** standard
**Files Reviewed:** 73
**Status:** clean

## Summary

The phase-scope resolver reported `degraded` because the original task commits were not reachable after the phase changes were squashed. The initial standard-depth audit therefore used the recorded 72-file fallback union from `f80bdf54c6c7d81e8e21f0275b43cda6edf6c8c4`; that full file list is retained above. At the current head, I independently rechecked all seven implementation and CTest-registration paths in the approved D-134 diff (`0953f61951732951dcc655527655e0a5ec2d6d36..d2c0dc95ecc7c5eb34a85bdc541f5ac3918190dc`) and traced their CLI error paths. I also adjudicated an adjacent performance-receipt numeric-representation concern against the existing contract and a production-path probe; it is withdrawn as unsubstantiated.

The approved patch digest matches `build/prb-approved-schema.diff` (`33c3646e59618a4f68f99fed16674f5240744d4493a534f79fb53ae7d5b4325b`). The exact-integer guards now reject non-integer JSON schema values at the previously affected inventory, disposition, registry, recovery fixture, API capture, coverage manifest, and support-ledger boundaries. The policy registry validates its root type before reading fields and the production CLI emits a controlled rejection. Existing integer-schema positives remain; the new negative controls exercise booleans, floats, strings, null, arrays, and non-object roots. The recovery CTest verifies the published-asset helper's bytes against the immutable revision before invoking its self-test. The parent-provided focused CTest log records the eight affected tests passing; source inspection, rather than the test result alone, supports closure of the original findings.

The earlier stale CTest marker failure (expected 62 controls while the corrected self-test measures 72) remains recorded in `build/phase19-window/posttag-recovery/schema-rescope-prep/initial-ctest-marker-mismatch.md`; it was corrected by raising the existing exact marker. The initial review's erroneous inclusion of `verify-v03-dispositions.py:328` is expressly excluded: that embedded performance receipt check already required `type(perf.get("schema_version")) is int`, and this recheck confirmed it remains strict. The original reproduction is retained at `build/prb-review-reproduction.json`. No implementation file was modified during this review.

## Closed Review Findings

| ID | Original title | Recheck disposition | Evidence |
|----|----------------|---------------------|----------|
| WR-01 | Boolean schema versions are accepted as integer version 1 | Closed in the D-134 source recheck at `d2c0dc95`; the originally reproduced pre-publish inventory and registry paths now require exact integer types, as do the other previously listed unchecked schema boundaries. | Previous report at commit `acc4049f`; reproduction at `build/prb-review-reproduction.json`; exact approved patch at `build/prb-approved-schema.diff`. The strict `verify-v03-dispositions.py:328` site was already guarded and is excluded. |
| WR-02 | A non-object workflow-policy registry escapes as an uncaught exception | Closed in the D-134 source recheck at `d2c0dc95`; a non-dictionary root is rejected before `.get`, and the CLI converts `CoverageError` to `REJECT workflow-policy-coverage` with exit 1. | Previous report at commit `acc4049f`; current guard in `tests/scripts/verify-workflow-policy-coverage.py:500-504`. |

The original release failure evidence and actual published-release readback remain historical facts; this code review does not rewrite them or claim the remaining local, player, consumer, phase-goal, hosted-CI, PR B, or merge gates complete. The initial full audit and its source scope remain preserved in the previous report commit and the 72-file list above.

## WR-03 Adjudication

The concern was that `tests/scripts/verify-v02-performance.py:219` accepts `schema_version` by membership in `(1, 2, 3)`, so JSON `2.0` and `3.0` compare equal to those values in Python. The existing Phase 19 plan and receipt contract identify supported version values but do not require a lexical integer token or exact Python `int` at this separate legacy performance-receipt boundary. The existing exact-`int` pattern is scoped to named managed-input validators and the five D-134 boundaries; it is not a blanket wire-format rule.

JSON and JSON Schema define `3` and `3.0` as the same integral numeric value; JSON Schema treats a number with a zero fractional part as an integer ([JSON Schema numeric types](https://json-schema.org/understanding-json-schema/reference/numeric)). The parent's production-path probe confirms integer `3` and numeric `3.0` both pass with the same verified summary; `true` is rejected by `--verify` as legacy, while `false`, `3.1`, and string `"3"` are rejected as unsupported. A wrong workload digest still fails its specific check. No unsupported-version or source/measurement-validation bypass was demonstrated. WR-03 is therefore withdrawn as an unsubstantiated hardening suggestion, not deferred or accepted as a risk. Probe evidence is retained at `build/prb-performance-schema-adjudication.json`.

## Narrative Findings (AI reviewer)

All current findings from this review are closed or withdrawn as unsubstantiated. The D-134 recheck does not complete the remaining phase qualification or merge gates.

---

_Reviewed: 2026-10-31T15:01:32Z_
_Reviewer: the agent (gsd-code-reviewer)_
_Depth: standard_
