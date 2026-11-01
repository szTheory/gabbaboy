---
phase: GB-20-fixture-admission-tune-up
reviewed: 2026-11-01T02:36:07Z
depth: standard
files_reviewed: 20
files_reviewed_list:
  - .github/scripts/verify-workflow-policy.py
  - .github/workflows/ci.yml
  - .github/workflows/fixture-repro.yml
  - .github/workflows/preview.yml
  - .github/workflows/release.yml
  - CMakeLists.txt
  - THIRD_PARTY_NOTICES.md
  - cmake/FixtureAdmissionPolicy.json
  - cmake/PreviewPackageSmoke.cmake
  - cmake/VerifyInstalledPackage.cmake
  - docs/fixture-admission.md
  - tests/CMakeLists.txt
  - tests/data/workflow-policy-controls.json
  - tests/expected-tests.txt
  - tests/scripts/test_player_package_policy.py
  - tests/scripts/verify-fixture-admission.py
  - tests/scripts/verify-phase3-player.sh
  - tests/scripts/verify-release-candidate.sh
  - tests/scripts/verify-v02-source-archive.py
  - tests/scripts/verify-workflow-policy-coverage.py
findings:
  critical: 3
  warning: 0
  info: 0
  total: 3
status: issues_found
---

# Phase 20: Code Review Report

**Reviewed:** 2026-11-01T02:36:07Z  
**Depth:** standard  
**Files Reviewed:** 20  
**Status:** issues_found

## Summary

The Phase 20 implementation and both fix rounds were re-reviewed at current HEAD. CR-06, CR-07, WR-04 and WR-05 are corrected; CR-01 through CR-04 and WR-01 through WR-03 also appear resolved in the current code. CR-05's environment and temporary-path override was removed from the wrapper, and the isolated publisher checks the uploaded Linux product with trusted files. The macOS and Windows product checks still trust a writable checker and policy from the tagged build workspace. Two additional admission bypasses remain in the mutable product policy and workflow command matcher. Three blocking findings remain. The fix report records the focused controls as passing; this review was static and did not rerun them.

## Narrative Findings (AI reviewer)

### Critical Issues

#### CR-05: BLOCKER — macOS and Windows release product checks still trust the tagged workspace

**File:** `.github/workflows/release.yml:728-737, 781-792, 850-861, 922-928, 968-979, 1041-1051`; `.github/scripts/release-evidence-lifecycle.sh:224-293`

**Issue:** The macOS and Windows jobs copy the admission checker from the workflow revision into writable `RUNNER_TEMP` before running the tagged source's CMake configure, build and install steps. They then invoke that temporary checker against the staged and downloaded packages. Tagged build code runs in the same job before those checks and can replace the checker. The checker also receives `--repo-root .`, so its package allowlist is read from the tagged checkout. The isolated publisher rechecks only the Linux archive; its later draft validation hashes and inventories platform assets but does not verify their product layouts. A tagged macOS or Windows build can therefore add an excluded fixture and make the same-job check accept and publish it.

**Fix:** Re-download and safely extract the macOS and Windows product archives in the trusted publisher job, then validate them with the trusted checkout's checker and policy before draft validation/publication. Keep same-job checks as early feedback, not the final product authorization.

#### CR-08: BLOCKER — Product allowlist is loaded from an unpinned mutable file

**File:** `tests/scripts/verify-fixture-admission.py:847-875, 922-983, 1042-1074`; `cmake/FixtureAdmissionPolicy.json:1-115`

**Issue:** `_product_rules` reads the current `cmake/FixtureAdmissionPolicy.json` and validates its shape and baseline commit, but does not bind the `products` bytes to an immutable approved identity. `_product_source_expectations` then treats every fixture source listed in that file as allowed, and `_validate_product_entries` accepts its declared product destination when its bytes match the baseline. A change can add a repository-only game or diagnostic fixture, such as a `fixtures/mooneye-cgb/...` file, to the policy and install it into the package; the policy check and stage inventory will then approve the same change. The inventory hashes this mutable policy but does not independently establish that it is the approved policy.

**Fix:** Pin the complete product-policy digest to an independently reviewed identity in the checker or load the policy from a trusted immutable checkout. Add a negative control that adds a forbidden baseline fixture and destination to a candidate policy and requires rejection.

#### CR-09: BLOCKER — Workflow policy accepts redirected fixture-admission commands

**File:** `.github/scripts/verify-workflow-policy.py:852-877, 1760-1818`; `tests/scripts/verify-fixture-admission.py:2278-2285`

**Issue:** `_fixture_call` delegates to `require_call`, which accepts any shell command whose words start with the expected command and whose expected assignments are only a subset of the observed assignments. The repository-admission commands checked for `ci.macos-player-package` and `fixture-repro` are not matched exactly. A modified workflow can prefix `PATH=/tmp/attacker` and pass policy while selecting an untrusted `python3`, or append a duplicate `--repo-root /tmp/attacker`; argparse uses the last `--repo-root`, so the gate checks a controlled tree instead of the checkout. Existing exact-command checks and mutations cover product commands, but not these repository-admission calls.

**Fix:** Require exact words and assignments for the repository-admission invocations, including exactly one `--repo-root .`. Add mutation controls for both a prefixed PATH assignment and a repeated `--repo-root` option.

---

_Reviewed: 2026-11-01T02:36:07Z_  
_Reviewer: the agent (gsd-code-reviewer)_  
_Depth: standard_
