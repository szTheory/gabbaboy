---
phase: GB-06-qualified-dmg-release-and-consumer-handoff
reviewed: 2026-10-10T00:00:00Z
depth: standard
files_reviewed: 4
files_reviewed_list:
  - .github/workflows/release.yml
  - tests/scripts/verified_player_output_dir.py
  - tests/scripts/test_verified_player_output_dir.py
  - tests/scripts/verify-release-candidate.sh
findings:
  critical: 0
  warning: 1
  info: 0
  total: 1
status: issues_found
---

# Phase GB-06: Code Review Report

**Reviewed:** 2026-10-10
**Depth:** standard
**Files Reviewed:** 4
**Status:** issues_found

## Summary

Reviewed the diffs since fd562c0 and their interaction with the surrounding files.

- **release.yml.** The job that lost its job-level `GBB_VERIFIED_OUTPUT_DIR` now relies on the default in `tests/scripts/verify-phase3-player.sh:16`, which is `${RUNNER_TEMP:-${TMPDIR:-/tmp}}/gabbaboy-preview-verified-artifact`. That is outside the checkout, so the change is safe. The `--build-package` step (line 589) and the downloaded-package step (line 620) now write to distinct directories, so they cannot collide. Nothing else in the repository references the removed `build/release-player-verified` path.
- **verified_player_output_dir.py.** `_report_withdrawal_failure` runs inside the `except` handler and is itself guarded against a broken stderr. The original publication exception is still re-raised, so it is not masked. I found no defect. The test suite (20 tests) passes.
- **verify-release-candidate.sh.** The static contract has no false accepts on the forms I probed:
  - `..` segments, `/etc`, an empty value, and checkout-relative paths are all rejected.
  - A second, comment-only mention of the variable fails closed through the `count != len(assignments)` check.
  - The `$RUNNER_TEMP/..x/../..` case is rejected.

  It does have one false reject, described below.

## Warnings

### WR-01: Verified-output contract falsely rejects the unquoted YAML expression form

**File:** `tests/scripts/verify-release-candidate.sh:140-146`
**Issue:** The regex's bare alternative is `([^\s"']*)`, which stops at whitespace. For the idiomatic YAML env form `GBB_VERIFIED_OUTPUT_DIR: ${{ runner.temp }}/x`, which `.github/workflows/preview.yml:216` already uses, the captured value is just `${{`. That value fails the `\$\{\{\s*runner\.temp\s*\}\}` branch. The contract therefore raises a "not rooted at runner temp" error for a compliant assignment, even though the pattern list explicitly intends to allow the `runner.temp` form. It fails closed, so the release gate is not weakened. But anyone who adds the natural YAML env form to release.yml gets a misleading failure. The mutation self-check does not exercise this form, so the bug is untested.
**Fix:** Let the bare alternative match a whole `${{ ... }}` expression, for example:
```python
r"""\s*[:=]\s*(?:"([^"\n]*)"|'([^'\n]*)'|((?:\$\{\{.*?\}\}|[^\s"'])*))"""
```
Also add a positive self-check that the unquoted `: ${{ runner.temp }}/x` form is accepted.

---

_Reviewed: 2026-10-10_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
