---
phase: GB-16-tune-up-and-v0-2-debt-closure
reviewed: 2026-10-26T00:00:00Z
depth: standard
files_reviewed: 62
files_reviewed_list:
  - .gitattributes
  - .github/ci-timeouts.json
  - .github/scripts/check-required-native.py
  - .github/scripts/classify-changes.py
  - .github/scripts/produce-release-evidence.sh
  - .github/scripts/verify-release-gates.sh
  - .github/scripts/verify-release-source-proof.py
  - .github/scripts/verify-workflow-policy.py
  - .github/scripts/wait-exact-head-ci.py
  - .github/workflows/ci.yml
  - .github/workflows/nightly-asan.yml
  - .github/workflows/perf-attribution.yml
  - .github/workflows/preview.yml
  - .github/workflows/release-rehearsal.yml
  - .github/workflows/release.yml
  - CMakeLists.txt
  - README.md
  - docs/native-integration.md
  - docs/preview.md
  - docs/release.md
  - docs/support/v0.2.1.md
  - tests/CMakeLists.txt
  - tests/acceptance/CMakeLists.txt
  - tests/check_sanitizer_timeout_policy.cmake
  - tests/ci/test-budget-allowlist
  - tests/cmake/areas.cmake
  - tests/cmake/ci-lanes.cmake
  - tests/cmake/hygiene.cmake
  - tests/cmake/perf.cmake
  - tests/data/closeout-scan-14-uat-review.md
  - tests/data/planning-hygiene/lessons-duplicates.md
  - tests/data/planning-hygiene/roadmap-over-cap.md
  - tests/data/repaired-summary-coverage.md
  - tests/data/stall-bounded-cases.txt
  - tests/expected-tests.txt
  - tests/fuzz_core.c
  - tests/player/CMakeLists.txt
  - tests/scripts/run-perf-gate.sh
  - tests/scripts/test-cgb-red-evidence-privacy.py
  - tests/scripts/test_hdma_remote_evidence.py
  - tests/scripts/verify-cgb-corpus-inventory.py
  - tests/scripts/verify-closeout-dispositions.py
  - tests/scripts/verify-closeout-scan.py
  - tests/scripts/verify-hdma-lane.py
  - tests/scripts/verify-historical-limitations.py
  - tests/scripts/verify-no-phase-paths.py
  - tests/scripts/verify-perf-gate.py
  - tests/scripts/verify-phase8-closure-contract.py
  - tests/scripts/verify-phase8-player-contract.py
  - tests/scripts/verify-planning-hygiene.py
  - tests/scripts/verify-planning-labels.py
  - tests/scripts/verify-stall-report.py
  - tests/scripts/verify-summary-coverage.py
  - tests/scripts/verify-support-ledger.py
  - tests/scripts/verify-test-budget.py
  - tests/scripts/verify-v02-adoption.py
  - tests/scripts/verify-v02-consumers.py
  - tests/scripts/verify-v02-delivery.py
  - tests/scripts/verify-v02-fuzz.py
  - tests/scripts/verify-v02-performance.py
  - tests/scripts/verify-v03-dispositions.py
  - tests/test_fuzz_core.c
findings:
  critical: 0
  warning: 5
  info: 4
  total: 9
status: issues_found
---

# Phase GB-16: Code Review Report

**Reviewed:** 2026-10-26
**Depth:** standard
**Files Reviewed:** 62
**Status:** issues_found

## Summary

Reviewed the Phase 16 gate, workflow and verifier changes. Full reads: the workflows (`ci`, `nightly-asan`, `perf-attribution`, `preview`, `release-rehearsal`), the `release.yml` Phase 16 hunks, the release gate and source-proof scripts, the exact-head waiter, the classifier, the required-native judge, the perf gate runner and evaluator, the test-budget checker, the CMake fragments, the HDMA lane checker, the phase-path lint, and the planning hygiene checker. The remaining verifiers (`verify-v03-dispositions`, `verify-stall-report`, `verify-v02-adoption`, `verify-v02-consumers`, the fixture and doc files) and the long tail of `verify-workflow-policy.py` were only diff-skimmed and not read line by line; the workflow-policy `check_nightly` function was read in full.

No false-pass path was found in the central CI gates. Some of the design is solid:
- Every `uses:` is pinned to a full SHA.
- `persist-credentials: false` is set on every checkout.
- The classifier fails toward `kind=full` on every doubt, and the workflow runs the base commit's copy of it.
- `required-native` judges job results, with a missing or unknown value never counting as success.
- The `GITHUB_ENV` write of the rehearsal tag is strictly validated by `derive_rehearsal_tag`, so a crafted branch name cannot inject environment lines.
- The perf gate uses exact `Fraction` arithmetic and fails closed on digest, pin and Ir-floor guards.
- Workflow inputs reach shell only through `env:`.

The weaknesses are in evidence provenance, ratchet strength and a few counting loopholes. There are no BLOCKERs. The five WARNINGs are the ones that can let a defective or unreviewed input read as a pass.

## Warnings

### WR-01: Release reuses a performance receipt from an unauthenticated rehearsal-branch artifact

**File:** `.github/workflows/release.yml:1159-1181`
**Issue:** The new `candidate-performance` steps pick the newest successful run of `release-rehearsal.yml` on branch `rehearsal/$RELEASE_TAG` with `gh run list --status success --limit 1`, then download `rehearsal-performance-*` from it. `--verify-reuse` then checks only the receipt's self-declared `candidate.sha`/`tree_sha` against the tag tree, plus the receipt schema and numbers. Nothing authenticates the producing run:
- Any user with push access can create a `rehearsal/v…` branch. That branch runs its own copy of the workflow and can upload any artifact with that name.
- The measured numbers are self-reported and not recomputed.
- The run's `headSha`, `event`, `conclusion` and `workflowName` are never compared to the tag's tree.

The rehearsal workflow's own dispatch path (`release-rehearsal.yml:167-171`) does exactly these checks (workflow name, branch, tree equality of the run head) before trusting a retained measurement. The release path skips them. A forged "passed" receipt for a tree that is the tag's tree would be accepted by the delivery judge, whose `--verify-reuse` is the same content-only check. `|| true` on the download is fail-safe (it falls back to a fresh measurement) but also hides a download error entirely.
**Fix:** Bind the artifact to a run before reuse, mirroring the rehearsal dispatch checks:
```bash
run_json=$(gh run view "$run_id" --repo "$GITHUB_REPOSITORY" --json headSha,headBranch,workflowName,event,conclusion)
# require workflowName == release-rehearsal, headBranch == rehearsal/$RELEASE_TAG, conclusion == success
[[ "$(git rev-parse "$run_sha^{tree}")" == "$(git rev-parse "$SOURCE_SHA^{tree}")" ]] || run_id=""
```
Also require that the receipt's `candidate.sha` equals the run's `headSha`. Print a notice instead of `|| true` when the download fails. Consider making the reuse opt-in through a reviewed input rather than ambient.

### WR-02: Phase 8 boundary pinned by a mutable tag with no expected-SHA assertion

**File:** `tests/scripts/verify-phase8-closure-contract.py:14-16, 81-89`; `tests/scripts/verify-phase8-player-contract.py:16-18, 30-42`
**Issue:** The literal commit `96d5eec9…` was replaced by the tag `historical/phase-08-boundary`. The tag currently resolves to the right commit (checked locally and on `origin`). Nothing in either checker asserts that, and the success line only echoes whatever the tag resolves to. Anyone with tag-write access can retarget the tag to a commit that satisfies the clause list, and both "historical" contracts keep passing against different evidence. The comment says it never falls back to a literal SHA; that removes the only immutable anchor.
**Fix:** Keep the SHA as a constant and assert the tag resolves to it, or at least verify it equals the pinned value:
```python
EXPECTED_BOUNDARY = "96d5eec977bee99a0629499b89c737415e24184c"
...
if boundary is None or (args.boundary == DEFAULT_BOUNDARY and boundary != EXPECTED_BOUNDARY):
    print("... FAIL: boundary tag was retargeted", file=sys.stderr); return 1
```
The `--boundary` override used by the wrong-boundary controls keeps working.

### WR-03: `check_final_receipt` silently collapses duplicate `SHA256SUMS` entries

**File:** `.github/scripts/verify-release-gates.sh:277-287`
**Issue:** `listed[name.lstrip("* ")] = digest` overwrites on a repeated name. A manifest with a bad first line and a good second line for the same asset passes every check: the digest equality, the set equality, and the receipt's `sha256sums_sha256` binding, which hashes the file as written. `sha256sum -c SHA256SUMS`, which consumers will run on the published file, fails on the bad line. A blank line also raises an unhandled `ValueError` traceback from `line.split(None, 1)`. That one fails closed, but it is a crash and not a diagnostic. The same file already rejects duplicate asset names for the API inventory, so this is an inconsistency in an otherwise strict gate.
**Fix:**
```python
for line in (root / "SHA256SUMS").read_text().splitlines():
    parts = line.split(None, 1)
    if len(parts) != 2:
        raise SystemExit("SHA256SUMS contains a malformed line")
    name = parts[1].lstrip("* ")
    if name in listed:
        raise SystemExit(f"SHA256SUMS lists {name} more than once")
    listed[name] = parts[0]
```
Add a negative control to `inventory_fixture` (a `final-dup` defect).

### WR-04: Test-budget ratchet does not bound new allowlist rows

**File:** `tests/scripts/verify-test-budget.py:149-184` (`evaluate`), `tests/ci/test-budget-allowlist`
**Issue:** The ratchet rejects only a raised ceiling for a row that already exists at the base (`name in base_rows`). A new row, or a renamed test, has no ceiling limit. It needs only a ref that resolves at the base, and `GB-CI-004`, which every existing row already uses, resolves. A change can therefore add a test with `TIMEOUT 3000` and an allowlist row of 3000 and pass, with no decision or lesson specific to it. This defeats the "180 s inside the 300 s hosted sanitizer budget" intent in the docstring. In addition, the checker and allowlist are read from the head tree (`ci.yml:120`), unlike the classifier, which is deliberately executed from the base commit. That is generic to the repo, but it makes the ratchet advisory against a hostile change.
**Fix:** Add a hard maximum for any row not present in the base (for example `NEW_ROW_CEILING_MAX = 300`) and reject a new row whose ref also already backs more than N rows. Alternatively run the checker from the base commit (`git show "$BUDGET_BASE:tests/scripts/verify-test-budget.py"`), as the `changes` job does for the classifier.

### WR-05: Plan-cap check can be bypassed by plan file names and does not enforce the 4-phase limit

**File:** `tests/scripts/verify-planning-hygiene.py:70-73, 106-117, 120-130`
**Issue:** `PLAN_FILE = ^(\d+(?:\.\d+)?)-\d+-PLAN\.md$` counts only purely numeric plan ids. A plan named `16-01a-PLAN.md` or `16-03-PLAN-extra.md` is not counted, so the 12-per-phase cap can be exceeded without a finding. AGENTS.md also sets "at most 4 phases … per milestone", but `check_plan_cap` enforces only the per-phase cap (≤12) and the sum (≤40), never `len(caps) <= 4`. Five phases with caps of 8 pass.
**Fix:** Count any `*-PLAN.md` file whose leading token matches the phase (`^(\d+(?:\.\d+)?)-.+-PLAN\.md$`) and add `if len(caps) > PHASE_MAX: errors.append("plan-cap-phase-count: …")` with `PHASE_MAX = 4`, plus a control fixture for each.

## Info

### IN-01: Retry replaces regenerated evidence with the attached bytes before the recovery judge reads them

**File:** `.github/workflows/release.yml:1251-1266`
**Issue:** On `RETRY`, the producer's `support-ledger.json`, corpus, fuzz and performance receipts are overwritten with the copies already attached to the draft, and then `verify-published-release-assets.py --inventory` runs. The recovery decision compares live assets to an inventory built from those same bytes. Its "attachment differs from the retained producer bytes" tamper check is then trivially satisfied on retry. The comment explains why (per-run nonces make byte equality impossible) and says the later `--check-v02-evidence` gate still judges them. That holds, but the recovery stage no longer detects anything on retry.
**Fix:** Optional. Record the attached digests in the inventory and verify them against the draft API digests, so a post-attachment swap is still caught at this stage.

### IN-02: Required-check app identity is a wildcard at PR time but hard-coded at release time

**File:** `.github/scripts/verify-release-gates.sh:193, 209`; `.github/scripts/verify-release-source-proof.py:13-17`
**Issue:** `check_required_checks` takes `app_id` from the branch rule, and `None` means any app. The self-test fixture itself uses `preview-package-smoke` with `app_id: None` next to a run from app 15368. `verify-release-source-proof.py` hard-codes id 15368 and slug `github-actions` for all three contexts. A check posted by some other app under a required name could satisfy the PR-time gate if branch protection leaves `app_id` null, though not the later source-proof gate.
**Fix:** Require a non-null `app_id` for the three recorded contexts in `check_required_checks`, matching the source-proof table.

### IN-03: `report-red` has no job timeout, and its dedupe search matches on a title phrase

**File:** `.github/workflows/nightly-asan.yml:45-66`
**Issue:** `report-red` sets no `timeout-minutes`. The policy checker requires one only for the replay job. The `gh issue list --search "\"$title\" in:title"` lookup can match an unrelated open issue that merely contains the phrase, and it does not use `--label` or `--author`. The result is a comment on the wrong issue and no new nightly-red issue.
**Fix:** Add `timeout-minutes: 5`. Create the issue with a dedicated label (`--label nightly-red`) and look up by `--label` and exact title.

### IN-04: Weak or incomplete controls in the perf-gate runner and the HDMA lane self-test

**File:** `tests/scripts/run-perf-gate.sh:63-68`; `tests/scripts/verify-hdma-lane.py:106-113`
**Issue:**
- `collect` keeps only `<rom>.line.1` and deletes the other repeat's line. The second head run's `consumed_half_dots` and digest are never validated, only its Ir, so a nondeterministic or divergent second run would pass unchecked.
- The `skipped-lane` control in `lane_self_test` passes `reason=None`, so any `ContractError` counts as the expected rejection. The mutation deletes the first line containing `cgb_hdma_lane_contract`, which also matches the `_selftest` registration. The control proves "something fails" but not why.

**Fix:** For the first, compare the digest and consumed fields across all repeat lines in `collect` or in the evaluator. For the second, pass an expected substring (`"CTest must register cgb_hdma_lane_contract"`) and anchor the mutation on `add_test(NAME cgb_hdma_lane_contract\n`.

---

_Reviewed: 2026-10-26_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
