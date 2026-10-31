---
phase: GB-19-qualified-v0-3-0-release
reviewed: 2026-10-31T17:11:32Z
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
review_head: e292db8c651e6f297ba6eb77049d2ca6f021304f
prior_review_head: e46023c53bdff9e7ac44fcfb33a9e237ceec0430
prior_review_report_commit: acc4049f
post_tag_diff_base: d61a25ea54364e0e26ef89bb7467c72089361d49
scope_resolution: degraded
bounded_rescope_base: 0953f61951732951dcc655527655e0a5ec2d6d36
bounded_rescope_head: d2c0dc95ecc7c5eb34a85bdc541f5ac3918190dc
d135_rescope_base: 524ba3f7bf0614c26e00443ac6eafe162ad021ba
d135_rescope_head: e46023c53bdff9e7ac44fcfb33a9e237ceec0430
d136_rescope_base: 6c99ff0b908de282343a16a96aeebc9a176537e4
d136_rescope_head: e292db8c651e6f297ba6eb77049d2ca6f021304f
---

# Phase GB-19: Code Review Report

**Reviewed:** 2026-10-31T17:11:32Z
**Depth:** standard
**Files Reviewed:** 73
**Status:** clean

## Summary

The phase-scope resolver reported `degraded` because the original task commits were not reachable after the phase changes were squashed. The initial standard-depth audit therefore used the recorded 72-file fallback union from `f80bdf54c6c7d81e8e21f0275b43cda6edf6c8c4`; that full file list and the D-134/D-135 rechecks remain preserved above. This bounded D-136 recheck covers only `tests/scripts/verify-v02-consumers.py`, the single implementation path changed from `6c99ff0b908de282343a16a96aeebc9a176537e4` to current head `e292db8c651e6f297ba6eb77049d2ca6f021304f`. The file is already in the prior 73-file list. I did not repeat that audit or start an unrelated scan.

The approved patch digest matches `build/prb-approved-schema.diff` (`33c3646e59618a4f68f99fed16674f5240744d4493a534f79fb53ae7d5b4325b`). The exact-integer guards now reject non-integer JSON schema values at the previously affected inventory, disposition, registry, recovery fixture, API capture, coverage manifest, and support-ledger boundaries. The policy registry validates its root type before reading fields and the production CLI emits a controlled rejection. Existing integer-schema positives remain; the new negative controls exercise booleans, floats, strings, null, arrays, and non-object roots. The recovery CTest verifies the published-asset helper's bytes against the immutable revision before invoking its self-test. The parent-provided focused CTest log records the eight affected tests passing; source inspection, rather than the test result alone, supports closure of the original findings.

The earlier stale CTest marker failure (expected 62 controls while the corrected self-test measures 72) remains recorded in `build/phase19-window/posttag-recovery/schema-rescope-prep/initial-ctest-marker-mismatch.md`; it was corrected by raising the existing exact marker. The initial review's erroneous inclusion of `verify-v03-dispositions.py:328` is expressly excluded: that embedded performance receipt check already required `type(perf.get("schema_version")) is int`, and this recheck confirmed it remains strict. The original reproduction is retained at `build/prb-review-reproduction.json`.

The D-135 patch contains exactly the approved `.gitattributes` and `tests/CMakeLists.txt` changes; its computed two-path diff digest matches `fa768f81a6cb57157b9815f91cec689d4a03c33048b5123f13f1c1306b64aa66`. The readback CTest now derives a repository-relative path from `PROJECT_SOURCE_DIR` and `GBB_LIVE_PHASES_DIR`; the unchanged `Source.read` path validates it as a clean Git path and reads from the supplied immutable `--rev`. The call preserves the same `--rev`, `--tag`, exit/output contract, label and timeout. The single root-anchored `.gitattributes` entry pins only the helper compared against its immutable Git blob. Its exact-byte guard and helper source are unchanged; `git check-attr` reports `text` and `eol=lf` for that helper, while the rule does not overlap the APU `.src` negative fixture. The fixed line-ending attribute preserves the blob comparison instead of weakening it.

The parent-provided local evidence records 23 affected readback, recovery, EOL-negative, contract and installed-consumer tests passing without skips. The forced-autocrlf reproducer and its true/false checkout controls are documented in `build/phase19-window/posttag-recovery/windows-wiring-prep/README.md`. The original Windows failures remain retained; the actual D-135 Windows jobs subsequently passed at their then-current head. That evidence does not qualify the later D-136 head. The parent-provided focused checks and source inspection found no defect introduced by this two-file wiring patch.

## D-136 Bounded Recheck

The exact D-136 source diff is limited to `tests/scripts/verify-v02-consumers.py`; the current file bytes match the approved prototype `8fdc1e633435109fa9b06c3e76657369e3b72843`, and the pinned patch digest matches `6f8455b70e8e3f5d988d27d8ef39ec454a03ee5b62876642e0875ee70e24870b`. The retained baseline probe reproduces the CI `JSONDecodeError` deterministically: the direct `write_text` opens and truncates the readiness path before its contents are complete, while the polling reader treats path existence as readiness. The fixed probe confirms the final name remains absent during empty and partial writes and exposes the full expected JSON only after publication. The old-writer regression control fails at the intended assertion; the prototype passes it.

The repair writes to a unique temporary beside the marker, then replaces the readiness path and removes any remaining temporary in `finally`. Since the temporary and final path share a parent, the replace stays on the same filesystem. Both callers still use this helper only behind the existing private opt-in environment variables: the extraction path pauses after its first extracted file, and the install path pauses after staging completes. Their readers still poll for the final marker and consume the same JSON schema. `safe_extract_archive` still removes the partial extraction on `InterruptedRun`; the normal run still unwinds its `TemporaryDirectory`, and the existing output reservation releases the lock. Existing no-receipt, lock-cleanup, temporary-tree cleanup and successful-retry assertions are unchanged.

The deterministic marker regression is in `SELF_TEST_STATIC`. `select_self_tests` continues to require every test method be classified exactly once, so both existing C and C++ consumer CTests run this regression alongside their respective heavy half. It checks that the final marker is readable with the exact expected fields and that no sibling temporary remains. No assertion, marker schema, normal receipt publication, signal behavior, deadline, CTest timeout, floor, target, or product/source-identity condition was weakened or changed. No security boundary or product code changed.

The parent-provided local evidence records configure, build, install and all25 selected CTests passing without skips at `e292db8c`; both consumer halves passed. The local sanitizer configure was refused by the existing Linux-only guard on this macOS host, so there is no local Linux sanitizer pass. The original Linux sanitizer failure remains a failure record. Fresh exact-head hosted Linux sanitizer, Windows and all other protected checks are still required; this review does not claim them green. I ran no tests and made no implementation changes.

## Closed Review Findings

| ID | Original title | Recheck disposition | Evidence |
|----|----------------|---------------------|----------|
| WR-01 | Boolean schema versions are accepted as integer version 1 | Closed in the D-134 source recheck at `d2c0dc95`; the originally reproduced pre-publish inventory and registry paths now require exact integer types, as do the other previously listed unchecked schema boundaries. | Previous report at commit `acc4049f`; reproduction at `build/prb-review-reproduction.json`; exact approved patch at `build/prb-approved-schema.diff`. The strict `verify-v03-dispositions.py:328` site was already guarded and is excluded. |
| WR-02 | A non-object workflow-policy registry escapes as an uncaught exception | Closed in the D-134 source recheck at `d2c0dc95`; a non-dictionary root is rejected before `.get`, and the CLI converts `CoverageError` to `REJECT workflow-policy-coverage` with exit 1. | Previous report at commit `acc4049f`; current guard in `tests/scripts/verify-workflow-policy-coverage.py:500-504`. |

The original release failure evidence and actual published-release readback remain historical facts; this code review does not rewrite them or claim the remaining local, player, consumer, phase-goal, hosted-CI, PR B, or merge gates complete. The initial full audit and its source scope remain preserved in the previous report commit and the 72-file list above.

The D-135 Windows jobs passed at their tested head, before D-136. Actual hosted Windows, Linux sanitizer and all other required protected CI instances for D-136 head `e292db8c651e6f297ba6eb77049d2ca6f021304f` still need to pass before the existing guarded PR B squash; neither the earlier red Linux sanitizer job nor prior-head green jobs qualify this head.

## WR-03 Adjudication

The concern was that `tests/scripts/verify-v02-performance.py:219` accepts `schema_version` by membership in `(1, 2, 3)`, so JSON `2.0` and `3.0` compare equal to those values in Python. The existing Phase 19 plan and receipt contract identify supported version values but do not require a lexical integer token or exact Python `int` at this separate legacy performance-receipt boundary. The existing exact-`int` pattern is scoped to named managed-input validators and the five D-134 boundaries; it is not a blanket wire-format rule.

JSON and JSON Schema define `3` and `3.0` as the same integral numeric value; JSON Schema treats a number with a zero fractional part as an integer ([JSON Schema numeric types](https://json-schema.org/understanding-json-schema/reference/numeric)). The parent's production-path probe confirms integer `3` and numeric `3.0` both pass with the same verified summary; `true` is rejected by `--verify` as legacy, while `false`, `3.1`, and string `"3"` are rejected as unsupported. A wrong workload digest still fails its specific check. No unsupported-version or source/measurement-validation bypass was demonstrated. WR-03 is therefore withdrawn as an unsubstantiated hardening suggestion, not deferred or accepted as a risk. Probe evidence is retained at `build/prb-performance-schema-adjudication.json`.

## Narrative Findings (AI reviewer)

No current findings remain from the D-134, D-135 or D-136 bounded rechecks. These reviews do not complete the remaining phase qualification or merge gates.

---

_Reviewed: 2026-10-31T17:11:32Z_
_Reviewer: the agent (gsd-code-reviewer)_
_Depth: standard_
