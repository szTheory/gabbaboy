---
phase: GB-15-cgb-acceptance-support-ledger-and-v0-2-0-release
reviewed: 2026-10-20T00:00:00Z
depth: standard
files_reviewed: 24
files_reviewed_list:
  - .gitattributes
  - .github/scripts/verify-published-release-assets.py
  - .github/scripts/verify-release-gates.sh
  - .github/workflows/ci.yml
  - .github/workflows/preview.yml
  - .github/workflows/release-rehearsal.yml
  - .github/workflows/release.yml
  - CMakeLists.txt
  - cmake/RunInstalledConsumer.cmake
  - include/gabbaboy/gabbaboy.h
  - tests/CMakeLists.txt
  - tests/fuzz_core.c
  - tests/scripts/measure-release-baseline.sh
  - tests/scripts/run-bounded-fuzz.sh
  - tests/scripts/verify-cgb-corpus-claims.py
  - tests/scripts/verify-release-candidate.sh
  - tests/scripts/verify-support-ledger.py
  - tests/scripts/verify-v02-adoption.py
  - tests/scripts/verify-v02-consumers.py
  - tests/scripts/verify-v02-delivery.py
  - tests/scripts/verify-v02-fuzz.py
  - tests/scripts/verify-v02-performance.py
  - tests/scripts/verify-v02-source-archive.py
  - tests/test_fuzz_core.c
findings:
  critical: 0
  warning: 8
  info: 8
  total: 16
status: issues_found
---

# Phase 15: Code Review Report

**Reviewed:** 2026-10-20
**Depth:** standard
**Files Reviewed:** 24
**Status:** issues_found

## Summary

I read the Phase 15 diff (`git diff c771b1b`) for the release workflows, gate scripts, archive inspector, delivery/evidence validators and the fuzz oracle change. I read the large Python validators (`verify-support-ledger.py`, `verify-v02-performance.py`, `verify-v02-adoption.py`) selectively. I skimmed them for fail-open paths and unsafe constructs and did not trace every branch.

No blocking defects found. What I checked and found sound:
- No `pull_request_target`, no untrusted PR text or tag name interpolated into `run:` blocks. The new `${{ steps.corpus_run.outputs.run_nonce }}` in `run:` comes from a repo-controlled script.
- Tag and SHA inputs are regex-validated before use.
- Evidence jobs hard-check `GITHUB_REF == refs/heads/main` and the repository.
- Publication paths never overwrite an existing asset.
- The archive inspector bounds entry count, member size, total size and path length. It rejects traversal, absolute paths, NUL, backslash, hard links, devices, sparse files and duplicates, and it never extracts.
- The `|| return $?` additions in `verify-release-gates.sh` fix real masked-exit-code hazards.

The concerns are mainly that several "evidence" families are self-attested or only shape-checked, token scope is wider than needed for jobs that execute tagged code, and a few gate designs can false-fail or never fail.

**Why `include/gabbaboy/gabbaboy.h` changed:** this is a comment-only edit to the `gbb_create` documentation. It adds that the profile names describe software-profile behavior, not game compatibility or physical silicon equivalence, and that no stable ABI is promised. There are no declaration, type, enum or signature changes. It is not an API or ABI change. It is documentation-only, aligned with the claims verifier, and the doc text is itself checked by `verify-cgb-corpus-claims.py`.

## Warnings

### WR-01: Evidence jobs run tagged source (build, full CTest, fuzz binary) with a job-level `contents: write` token

**File:** `.github/workflows/release.yml:~860-1130` (jobs `candidate-corpus`, `candidate-fuzz`, `candidate-performance`)
**Issue:** Each job sets `permissions: contents: write` and `GH_TOKEN: ${{ github.token }}` at job level. `actions/checkout` also persists the token in `.git/config` by default. The same jobs then run `cmake --build`, the entire `ctest` stream, the libFuzzer binary and `measure-release-baseline.sh`. Those steps execute code from the tagged tree, and the corpus and fuzz steps process ROM-like inputs. Any test, build script or fuzz target compromise therefore holds a token that can upload or replace release assets and push refs. The token is only needed for the short attach and readback steps. In `ci.yml` the sanitizer job also forwards `GITHUB_TOKEN` to the fuzz campaign step (read-only `actions: read`, lower risk).
**Fix:** Split producers from attachers. Build and measure in a `contents: read` job and upload the receipt as a run artifact. Do the `gh release upload` in a small job that holds the write token and does not execute tagged code. At minimum, set `persist-credentials: false` on checkout and move `GH_TOKEN` from job `env:` to the individual steps that call `gh`.

### WR-02: `--check-receipt` accepts a source-archive receipt that was never bound to the Git tree

**File:** `tests/scripts/verify-v02-source-archive.py:~418-437` (`check_receipt`), `build_receipt` line ~407
**Issue:** `build_receipt` records `"tree_bound_to_git": repo is not None`, but `check_receipt` never requires it to be `true`. It re-derives the receipt with `repo=None` and compares only `archive_sha256`, `source_tree_sha256`, `notice_sha256`, `archive_root`, fixture identities and `inspected_members`. The only tag binding left is the commit ID in the archive's own pax comment, which comes from the very archive under inspection. The final gates (`check_v02_evidence`, `--verify-final`) use only `--check-receipt`. A receipt produced without `--repo` therefore satisfies the final gate. The rehearsal and release producers pass `--repo .`, so this is latent, but the validator would not catch the omission.
**Fix:** In `check_receipt`, add `if receipt.get("tree_bound_to_git") is not True: raise Reject("receipt-invalid", "receipt was not bound to the tagged Git tree")`. Add a negative control for a `repo=None` receipt to the self-test.

### WR-03: Fuzz receipt is self-attested, so the "forged evidence" checks are shape-only

**File:** `tests/scripts/verify-v02-fuzz.py:516-610` (`validate_receipt`), `ci.yml`, `release.yml` (`--verify`)
**Issue:** `--verify` checks field presence and format only. `workflow.run_id`, `job`, `job_id`, `event`, `compiler.binary_sha256`, `compiler_sha256`, `cmake_cache_sha256`, `output_sha256` and `execution_count` are never tied to anything checkable. `workflow.run_id` and `job_id` are not checked against GitHub (`verify_hosted` does that, but the release path calls only `--verify`). `source_commit()` also honours `GBB_SOURCE_SHA` from the environment. The source-manifest comparison does force the labelled commit to match the worktree, which stops a mislabelled stale run. Anyone able to write a draft asset can hand-write a passing receipt. For the claimed "campaign ran on the tagged source" guarantee, the release gate needs a hosted cross-check.
**Fix:** In the draft and final gates, call the hosted verification (`verify_hosted`) for the recorded run/attempt, or at least confirm via `gh api repos/$REPO/actions/runs/$run_id/attempts/$attempt` that the run exists, is `completed/success`, has `head_sha == source_sha` and the expected workflow path. Reject `run_id == "local"` outright.

### WR-04: Performance regression gate can never fail (standing pre-written "review")

**File:** `.github/workflows/release.yml` (`candidate-performance` env `PERFORMANCE_REGRESSION_REVIEW`), `.github/workflows/release-rehearsal.yml` (two copies), `tests/scripts/measure-release-baseline.sh:474-495`
**Issue:** The `+5%` trigger result is `accepted-with-disclosed-regression` whenever any non-empty review note is supplied. The workflow bakes in a constant note stating the slowdown "is accepted and disclosed". The note is supplied regardless of magnitude, and `verify-v02-performance.py` only checks that the disposition fields are consistent. A 50% or 5x slowdown therefore qualifies identically to 6%. The "review" is not tied to the measured numbers or to a person or time, and the same sentence is copy-pasted in three places.
**Fix:** Add an upper bound that no note can override (for example, reject when `median - margin > 125%`, or require the note to embed the measured median and margin). Alternatively, make the note a `workflow_dispatch` input recorded per run, and keep a single source of truth for the text.

### WR-05: Source-archive receipt depends on GitHub producing byte-identical tarballs across downloads

**File:** `.github/workflows/release.yml:~470-496`, `.github/scripts/verify-release-gates.sh:~560` (`fetch_source_archive`), `verify-v02-source-archive.py` (`archive_sha256`)
**Issue:** The workflow downloads `https://github.com/$REPO/archive/refs/tags/$TAG.tar.gz` several times: at inspection, in the manifest job, at the draft gate and at the final gate. It compares the receipt's `archive_sha256` with a fresh download each time. GitHub documents that archive checksums are not guaranteed stable (compression or backend changes). A change between download times makes the final gate fail for a correct release, and the tag cannot be re-cut. The retry path's `cmp -s` on the stored receipt shares the same assumption.
**Fix:** Bind on the stable properties (`source_tree_sha256`, the tree-to-git comparison and the embedded commit) and treat `archive_sha256` as informational. Or record the downloaded archive as a release asset so later gates verify retained bytes instead of re-downloading.

### WR-06: Trust-boundary overlay covers three files, but the gate delegates to many more tagged files

**File:** `.github/workflows/release.yml:~436-445` (overlay step), `.github/scripts/verify-release-gates.sh:~557` (`check_v02_evidence`)
**Issue:** The workflow overlays `verify-release-candidate.sh`, `verify-v02-source-archive.py` and `VerifyReleaseReceipt.cmake` from `GITHUB_SHA` because the v0.2.0 tag shipped a defective checker that could not be repaired. `check_v02_evidence` and `run_owner` then execute `verify-v02-delivery.py`, `verify-support-ledger.py`, `verify-v02-performance.py`, `verify-v02-fuzz.py` and `verify-cgb-corpus-claims.py` from the tagged checkout. A defect in any of those is again unfixable without a new tag. They are also the validators judging the evidence, so a bad tag can supply its own lenient judge. Also, `git show "$GITHUB_SHA:$path" > "$path"` writes into the tagged tree after build steps, and the `candidate` job's later steps mix producer and judge versions.
**Fix:** Either overlay all the judge scripts the final gates call (delivery plus the four owners and their imports), or run the gate from a separate trusted checkout of the workflow commit with `--repo-root` pointing at the tag.

### WR-07: DMG KEY1 oracle fix leaves scenario 3 (held button) exposed to the same failure and the new DMG seeds are weak controls

**File:** `tests/fuzz_core.c:539-540, 561-575, 796`; `tests/test_fuzz_core.c:166-190`
**Issue:** The fix forces every DMG-profile scenario except 3 to scenario 7 (STOP/wake twin). Scenario 3 on DMG still emits the `LDH ($4D)` KEY1 write and a later `LDH A,($4D)` read, which is the guest `$FF4D` access the comment says "stops on an unsupported bus access by design". No seed covers `data[0]=0x10, data[1]=0x03`. The existing held-button seed is CGB (`0x90`). The same hosted-fuzz failure class can therefore still be reached by DMG scenario 3. The DMG regression seeds assert `min_switches=0, min_reads=0, check_key1=0`, so they prove only "no contract failure and STOP observed" and would pass if the fallback silently stopped exercising anything. The fix also removes coverage of DMG KEY1 behaviour (a deliberate trade-off that should be recorded, for example that DMG `$FF4D` handling is covered elsewhere).
**Fix:** Add `{0x10u, 0x03u, 0x0Fu}` as a DMG seed. Either route DMG scenario 3 away from KEY1 as well, or assert its expected outcome explicitly. Add positive-control assertions for the fallback (for example `scenario==7`, `key1_reads==0`, expected mode and profile) so a mis-routed seed fails.

### WR-08: Consumer receipt `source_sha` is self-reported by the package under test

**File:** `tests/scripts/verify-v02-consumers.py:~308-322` (`source_identity`), `verify-v02-delivery.py` (`consumer.get("source_sha") != source`)
**Issue:** `core_revision` is parsed from the stdout of the extracted package's own `gabbaboy-runner --acceptance ... --receipt`, then compared with the frozen source SHA. A tampered or wrongly built package can print any 40-hex string. The check is only meaningful if the package digest is separately bound to the build receipt, which this receipt does not enforce. `build_qualified` is likewise self-reported.
**Fix:** Bind the consumer receipt to the package archive SHA-256 (already computed as `package_hash`). Have the delivery check require that hash to equal the downloaded `gabbaboy-core-linux-x64.tar.gz` digest and the candidate receipt. Document that `source_sha` here is an informational self-report.

## Info

### IN-01: `--check-recovery` and `--decide` are not wired into any workflow

**File:** `.github/scripts/verify-release-gates.sh:~570-588, 855-858`; `.github/scripts/verify-published-release-assets.py:93-123`
**Issue:** No workflow calls `--check-recovery`, so the live-state recovery decision is exercised only by self-tests. Under `set -e`, a rejected `--decide` exits before `rm -rf "$tmp"`, leaking the temp dir (the self-test runs inside `$(...) && ... ||`, which masks this). `decide` also treats any queued or in-progress run for the same `head_sha` as a concurrent publication attempt. That includes unrelated workflows (CI, rehearsal) and would false-reject.
**Fix:** Wire it into the retry path or remove it. Use a `trap`-based cleanup, and filter runs to the release workflow (add `path` or `name` to the `--jq` projection).

### IN-02: Wiring validators rely on substring counts, which comments and echoes can satisfy

**File:** `.github/scripts/verify-release-gates.sh:~271-319` (`validate_v02_producers`, `V02_PRODUCER_CALLS`)
**Issue:** Checks such as `text.count("verify-v02-fuzz.py --verify") == 2` match anywhere in the file, including comments or `echo` strings. `text.rfind(call) > publish ... "RELEASE_TAG" not in call` has exemptions that skip several calls. `validate_retained_platforms` slices with `text.find(...)` results that may be `-1`, silently producing wrong slices. The mutation controls prove deletion is noticed, not that a commented-out call is.
**Fix:** Parse the workflow YAML and assert per-job step `run:` contents, or at least strip comment lines before counting.

### IN-03: `--evidence-only` skips build-artifact digest checks for any absent path

**File:** `tests/scripts/verify-support-ledger.py:~926-931` (`validate_source_bindings`), `build_v2_sidecar`
**Issue:** In evidence-only mode a build-artifact row whose path does not exist is skipped (`continue`), and the receipt path is taken from the ledger data instead of the filesystem. This is intended for downloaded receipts. It means build-artifact digests in the receipt are verified only by comparing derived data to the in-tag ledger snapshot. A path that does not exist locally is never checked.
**Fix:** Record in the PASS output how many build artifacts were skipped, and fail if all were skipped.

### IN-04: `check_tree` does not compare file modes; unwrapped-symlink depth math is off by one

**File:** `tests/scripts/verify-v02-source-archive.py:~163-175, 304-316`
**Issue:** `check_tree` compares only blob OIDs and symlink-ness, so an executable-bit change between archive and tree is invisible. In `register`, `depth = len(parts) - 2` assumes a wrapper directory. For `unwrapped=True` (product package) it should be `len(parts) - 1`, so legitimate in-root links like `lib/cmake/x -> ../../y` are rejected. This is harmless today because `check_product` rejects all links.
**Fix:** Compare `mode` (100644 against 100755) in `check_tree`, and compute symlink depth from `inspection.unwrapped`.

### IN-05: `curl --max-filesize` does not bound chunked downloads

**File:** `.github/workflows/release.yml` (source-archive download steps), `.github/scripts/verify-release-gates.sh` (`fetch_source_archive`)
**Issue:** `--max-filesize` is enforced only when Content-Length is known. A chunked response can exceed it before `inspect_archive` rejects it by size.
**Fix:** Add `--max-time`, and stream through `head -c` or check the size after download before inspection (already done post hoc by `os.path.getsize`).

### IN-06: `check_runs` binds workflow runs only to head SHA and success, not to a workflow

**File:** `tests/scripts/verify-v02-delivery.py:~332-346`
**Issue:** Any successful run with `head_sha == head` satisfies the `workflow_runs` list. Required-check binding is done separately in `check_pr` (app ID plus name), which is the real guard. The run list adds little assurance as written.
**Fix:** Require `path`/`name` to match the CI or release workflow.

### IN-07: Duplicate `Create the local-only rehearsal tag` and corpus scripts across rehearsal and release jobs

**File:** `.github/workflows/release-rehearsal.yml:~175-183, 286-294, 338-346`; `release.yml`
**Issue:** The corpus, tag, fuzz and package sequences are copied across three rehearsal jobs and the release jobs, so drift between rehearsal and release is likely. `git tag -f` on a PR-branch runner is safe (local only). The `aggregate` job repeats the whole pipeline a second time at 75 minutes.
**Fix:** Extract composite actions or reusable workflow steps.

### IN-08: `.gitattributes` forces `eol=lf` on whole globs and `gbb_add_v02_contract` embeds counts in regex

**File:** `.gitattributes:1-28`; `tests/CMakeLists.txt:~826-873`
**Issue:** `tests/scripts/*.sh`, `*.py` and similar globs are forced to LF. That is appropriate for digest-bound text, but `LICENSE*`/`NOTICE*`/`THIRD_PARTY*` also catch any future binary-like or CRLF-licensed vendored file silently. `v02_support_ledger` hard-codes `cases=107` in the expected-output regex, so any legitimate corpus change breaks this test with a message that does not say why.
**Fix:** Derive the case count from the inventory, or assert only `cases=[1-9][0-9]*` here and assert the exact count in the ledger validator.

---

_Reviewed: 2026-10-20_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
