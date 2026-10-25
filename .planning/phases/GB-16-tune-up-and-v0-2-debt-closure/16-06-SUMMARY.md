---
phase: 16-tune-up-and-v0-2-debt-closure
plan: "06"
subsystem: release-path-preparation
tags: [ledger-freeze, version-binding, rehearsal-dispatch, performance-review-path, release-notes-disclosure, v03-dispositions, timeout-ledger, tune-06, tune-03, tune-01]
requires:
  - phase: 16-04
    provides: the timeout ledger with its provisional rows, the planning-only lane and the policy script this plan re-cites and extends
  - phase: 16-05
    provides: the planning label and hygiene checks that the new planning tests join
provides:
  - verify-support-ledger.py --check-freeze, --self-test-freeze, --check-binding, --self-test-binding, --derive-rehearsal-tag and --print-version
  - ledger, adoption and rehearsal checks bound to the tree version (CMake project VERSION equal to the release-please manifest)
  - release-rehearsal.yml workflow_dispatch inputs measurement_run_id and performance_decision, a retained paired-performance artifact and a ref-derived rehearsal tag
  - verify-v02-performance.py --verify-reuse and the release.yml reuse step
  - the +8.3% instruction-count needle in verify-v02-adoption.py --release-notes
  - 16-DISPOSITIONS.json and verify-v03-dispositions.py with receipts read at a commit
  - a timeout ledger with no provisional row, so --check --release-head passes
affects: [16-07]
actuals:
  tokens: 37119
  tasks: 3
  commits: 4
commits: 4
plan_head_before: bdb352515128bcb70e26cd8ff6aff22484d6f1e2
plan_head_after: bd43d7b2d384020159480289f91bbbc8fbbdc213
tech-stack:
  added: []
  patterns:
    - A frozen document is pinned by the tag blob digest, the working digest and the offset, length and digest of the one disclosed insertion, and every mutation control re-pins the mutated digest so only the structural rule can reject it.
    - A producer job that must call gh splits the token step (gh only, no tagged code) from the step that runs tagged code, and the policy names the one token step per job.
    - A disposition record is read with git show REV:path for the record and every receipt, so a boundary check sees point-in-time facts and never calls gh.
key-files:
  created:
    - tests/scripts/verify-v03-dispositions.py
    - .planning/phases/GB-16-tune-up-and-v0-2-debt-closure/16-DISPOSITIONS.json
  modified:
    - tests/scripts/verify-support-ledger.py
    - tests/scripts/verify-v02-adoption.py
    - tests/scripts/verify-v02-performance.py
    - .github/workflows/release-rehearsal.yml
    - .github/workflows/release.yml
    - .github/scripts/verify-workflow-policy.py
    - .github/ci-timeouts.json
    - tests/CMakeLists.txt
    - tests/expected-tests.txt
    - docs/release.md
    - .planning/context/DECISIONS.md
key-decisions:
  - "D-111 (recommended, awaiting ratification): release-rehearsal.yml corpus, performance and aggregate become release_bound ledger rows under D-110's rules, because no green run of them can exist before the version-bound ledger and the owner-recorded review, and a provisional row would make the rehearsal judge's own --release-head check circular."
  - "The paired-performance token step is separate from the step that runs tagged code, in both the rehearsal and release.yml, and the policy exempts exactly that named step."
requirements-completed: []
coverage:
  - id: D1
    description: "The v0.2.0 ledger is frozen: the tag blob, the working file and the one disclosed #93 block are each pinned by SHA-256, a missing tag fails, and controls reject a flipped byte, a wrong pin, an insertion or equal-length edit outside the block, a removed or edited block and an unreadable tag."
    requirement: "TUNE-06"
    human_judgment: false
    verification:
      - kind: unit
        ref: "python3 -I tests/scripts/verify-support-ledger.py --check-freeze and --self-test-freeze (controls=9)"
        status: pass
      - kind: integration
        ref: "ctest --test-dir build -R '^(ledger_freeze|ledger_freeze_controls)$'"
        status: pass
  - id: D2
    description: "The ledger, adoption and rehearsal checks take the tree version from CMake cross-checked with the manifest, README must link the ledger that version selects, and fixtures reject a README linking an older or future ledger, a manifest and CMake disagreement and a version without a ledger."
    requirement: "TUNE-06"
    human_judgment: false
    verification:
      - kind: unit
        ref: "python3 -I tests/scripts/verify-support-ledger.py --check-binding, --self-test-binding (controls=6) and --self-test"
        status: pass
      - kind: integration
        ref: "ctest --test-dir build -R '^(support_ledger_binding|support_ledger_binding_controls|v02_support_ledger|v02_support_ledger_controls|v02_adoption_docs|v02_adoption_docs_controls)$'"
        status: pass
  - id: D3
    description: "verify-v02-adoption.py --release-notes requires the head-versus-v0.2.0 instruction-count disclosure (+8.3%) and the attribution receipt path, and its self-test rejects notes that drop either or hide the line in a comment."
    requirement: "TUNE-06"
    human_judgment: false
    verification:
      - kind: unit
        ref: "python3 -I tests/scripts/verify-v02-adoption.py --self-test docs (51 negative controls)"
        status: pass
  - id: D4
    description: "A recorded performance review can be applied in the rehearsal by dispatch and carried to the release by tree equality: verify-v02-performance.py --verify-reuse rejects an unequal tree, a pending receipt and an unreadable candidate, the paired gate is unchanged, and the policy rejects a decision applied without the tree, workflow or branch checks, a decision file inside the checkout, a token on the apply step, a write permission and a reuse without --verify-reuse."
    requirement: "TUNE-06"
    human_judgment: false
    verification:
      - kind: unit
        ref: "python3 -I tests/scripts/verify-v02-performance.py --self-test (32 tests)"
        status: pass
      - kind: unit
        ref: "python3 -I .github/scripts/verify-workflow-policy.py --self-test (259 negative controls)"
        status: pass
      - kind: e2e
        ref: "rehearsal run 40216415155 on rehearsal/v0.2.0 at bd43d7b: the tag derivation step succeeded in corpus, package and aggregate, and the pending paired measurement was retained as artifact rehearsal-performance-40216415155-1 although the job failed"
        status: pass
  - id: D5
    description: "16-DISPOSITIONS.json holds 26 rows with the release-linked rows pending-release, verify-v03-dispositions.py accepts closure only with tag-bound receipts read at a commit, and closeout_dispositions_scope_v03 shows the v0.2 owner_accepted=0 expectation stays scoped to the archived record."
    requirement: "TUNE-06"
    human_judgment: false
    verification:
      - kind: unit
        ref: "python3 -I tests/scripts/verify-v03-dispositions.py --check on the live record (rows=26 pending=5 closed=1 owner_accepted=7) and --self-test (controls=35)"
        status: pass
      - kind: integration
        ref: "ctest --test-dir build -R '^(v03_dispositions|v03_dispositions_controls|closeout_dispositions_controls|closeout_dispositions_scope_v03)$'"
        status: pass
  - id: D6
    description: "Every provisional timeout row is gone: changes and planning-checks cite main push runs, fuzz and package cite a probe rehearsal at an ancestor of main, the three rehearsal rows that cannot be green become release_bound, and the policy passes at the release head."
    requirement: "TUNE-03"
    human_judgment: false
    verification:
      - kind: unit
        ref: "python3 -I .github/scripts/verify-workflow-policy.py --check --release-head"
        status: pass
      - kind: other
        ref: "jq '[.[] | select(.provisional == true)] | length' .github/ci-timeouts.json prints 0"
        status: pass
  - id: D7
    description: "The full suite passes with the new tests, the exact head is green on every required context and heavy job, and src and include are unchanged against the plan base."
    requirement: "TUNE-01"
    human_judgment: false
    verification:
      - kind: integration
        ref: "cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error (1233 of 1234 first run, the one no_phase_paths failure fixed and the file's tests rerun green)"
        status: pass
      - kind: e2e
        ref: "PR 114 head bd43d7b: ci pull_request 40216403568, ci push 40216384921, fixture-repro pull_request 40216403570, fixture-repro push 40216384890 and preview-package-smoke pull_request 40216403621 all concluded success"
        status: pass
      - kind: other
        ref: "git diff --quiet bdb352515128bcb70e26cd8ff6aff22484d6f1e2 bd43d7b2d384020159480289f91bbbc8fbbdc213 -- src include"
        status: pass
duration: not captured at dispatch; about 4 hours including hosted CI waits
completed: 2026-10-25
status: complete
---

# Phase 16 Plan 06: Ledger freeze, review path and v0.3 dispositions Summary

**The v0.2.0 ledger bytes are frozen by three digests, the ledger, adoption and rehearsal checks follow the tree's own version, a recorded performance review can be dispatched through the rehearsal and reused by the release only on tree equality, and the v0.3 carry-over record sits in a validated pending-release state.**

## Delivery state

- **PR A:** https://github.com/szTheory/gabbaboy/pull/114, head `bd43d7b2d384020159480289f91bbbc8fbbdc213`, branch `gsd/phase-16-06-ledger-freeze-and-dispositions`, cut from origin/main `bdb3525`. Not merged (the orchestrator merges). `mergeStateStatus` reads UNSTABLE only because the probe rehearsal on the same sha shows failing non-required checks.
- **Exact-head runs, all success:** ci pull_request 40216403568 and ci push 40216384921 (every heavy job success; `planning-checks` and, on push, `macos-player-package` skipped by design), fixture-repro pull_request 40216403570 and push 40216384890, preview-package-smoke pull_request 40216403621. Required contexts `required-native`, `fixture-repro`, `preview-package-smoke` confirmed with `gh api`.
- **Probe branch `rehearsal/v0.2.0`** at the same head (deleted afterwards): ci push 40216415167 and fixture-repro push 40216415210 success; release-rehearsal run **40216415155 failure**. Success: fuzz (2.73 min), package (0.25), perf-gate (0.83). Failure: corpus and aggregate (the `--check-current` step: the v0.2.0 ledger pins sources that moved), performance (review trigger, median 118.35 percent, pending). Judge skipped. No fix round was needed (0 of 2 used).
- **Rehearsal outcome:** not green, as expected for this tree. A green rehearsal needs the v0.2.1 ledger and the owner's review decision, both of which belong to the D-31 window. The judge row therefore stays `release_bound` and its re-citation moves to 16-07.

## Commits

| Commit | Message |
| ------ | ------- |
| 82789c5 | test(phase-16): freeze the v0.2.0 ledger bytes and bind the ledger checks to the tree version |
| 3b9563f | ci(phase-16): carry a recorded performance review through the rehearsal and into the release by tree equality |
| 7548874 | test(phase-16): record the v0.3 carry-over dispositions and re-cite the timeout ledger from main runs |
| bd43d7b | test(phase-16): keep the disposition checker fixture off the live phases path |

## Ledger rows changed (`.github/ci-timeouts.json`)

| Row | Old | New |
| --- | --- | --- |
| `ci.yml:changes` | run 40165925846, e624dad, p50 0.10, provisional | main push run 40211538920 at 60bd41c (kind=full, success), p50 0.09, 1 sample |
| `ci.yml:planning-checks` | run 40166565258, 1b7fa0c, p50 0.35, provisional | main push run 40205944089 at 6f4f4bf (PR #109, kind=planning: planning-checks success, every heavy job skipped), p50 0.59, 1 sample |
| `release-rehearsal.yml:fuzz` | run 39401388702, d6f74b5, p50 2.00, 4 samples, provisional | probe run 40166530630 at 2bd618d (ancestor of main), p50 2.40, 1 sample |
| `release-rehearsal.yml:package` | run 39382974145, 6b83695, p50 0.27, 4 samples, provisional | probe run 40166530630 at 2bd618d, p50 0.40, 1 sample |
| `release-rehearsal.yml:corpus` | run 39382974145, 6b83695, p50 6.57, provisional | `release_bound` (D-111), timeout 60 |
| `release-rehearsal.yml:performance` | run 39382974145, 6b83695, p50 0.50, provisional | `release_bound` (D-111), timeout 45 |
| `release-rehearsal.yml:aggregate` | run 39391950429, 56eaf1b, p50 12.42, provisional | `release_bound` (D-111), timeout 75 |
| `release-rehearsal.yml:judge` | `release_bound` | unchanged `release_bound` (no green rehearsal exists) |

`changes` could not cite the failed #107 run 40170850976, so it cites 60bd41c. Run 40211538920 was still reported `in_progress` by one `gh run view` call and `completed success` a few minutes later; the cited facts are the final ones. Nothing in the YAML timeouts changed, so no other row was re-cited.

**Native p50 observation after #111 (not re-sized).** Main push runs 40208707146 and 40211538920 show native-windows 9.07 and 12.13 min (ledger 18.59), native-macos 7.63 and 7.45 (ledger 17.80), and native-linux 11.33 (ledger 11.07, unchanged). Two rows went up: `cmake-floor-3.25.3` 18.62 to 18.90 (ledger 13.00, cap 40, so 47 percent of the cap) and `linux-sanitizers-acceptance` 18.00 to 19.22 (ledger 10.04, cap 45). Every row still satisfies ceil(2 x p50) at most the cap, so the policy and plan do not require a resize; the next re-cite should look at `cmake-floor` first.

## Deviations from Plan

**1. [Rule 4 - recommended, needs ratification] Three more `release_bound` keys (D-111).** The plan expected `--check --release-head` to pass with every provisional row re-cited from a real run, and the rehearsal rerun to supply the rehearsal rows. The rerun cannot be green (see Delivery state), and the rehearsal judge runs `--check --release-head` on the rehearsed tree, so a provisional row would make the judge's own check circular. I applied D-110's class to `corpus`, `performance` and `aggregate` (three keys added to `LEDGER_RELEASE_BOUND_KEYS`, same field rules and the same VERSION-above-0.2.1 expiry) and recorded it as D-111 in DECISIONS.md. The orchestrator should ratify or replace it. The alternative is a permanently failing `--release-head`.

**2. [Rule 3 - Blocking, flagged for 16-07] Delivery validator will not accept a reused receipt as built.** `verify-v02-delivery.py` accepts a performance receipt whose candidate sha differs from the tag source only through an `evidence-reuse.json` record naming a producer that is an ancestor of the tag source with every covered input byte-identical. A rehearsal head is never an ancestor of a squash-merged tag, and no workflow produces that record. The plan's reuse (tree equality through `--verify-reuse`) is implemented and tested as written, but the attach gate would still reject the receipt at `performance-binding`. Fixing it means editing `verify-v02-delivery.py` and the evidence collection, outside this plan's files. 16-07 needs an orchestrator decision before the window. Falling back to a fresh measurement does not help, because that measurement triggers the review again with a digest no earlier decision binds.

**3. [Rule 3 - Blocking] Token handling in producer jobs.** The policy forbade any token and any `gh run` command in a producer job. The plan requires `gh run download` in the rehearsal `performance` job and in release.yml's performance job. I split each into a gh-only fetch step (the one step holding `GH_TOKEN: ${{ github.token }}`, under job-level `actions: read`) and a tokenless step that runs tagged code and applies the decision. `_check_unprivileged` now exempts exactly that named step per job (`PERFORMANCE_TOKEN_STEPS`), and rejects tagged-tree code in it, any other token reference, any other permission and any write. docs/release.md says so.

**4. [Rule 1 - Bug in the plan] The #93 block is inserted, not appended.** It sits at byte offset 7233 of the tag blob, not at the end. The freeze pins the offset (7233), length (794 bytes, 12 lines) and block digest, and checks that removing the block gives back the tag blob.

**5. [Rule 1 - Bug] `no_phase_paths` failure.** The first full run failed one test: the disposition checker's fixture spelled the live phases directory. The fixture paths moved to `fixture/` (commit bd43d7b).

**6. [Rule 3] Files outside `files_modified`.** `.planning/context/DECISIONS.md` (D-111) and `docs/release.md` text beyond the two requested sentences (the rehearsal branch naming, the token description, the dispatch and reuse description). `verify-v03-dispositions.py` carries `--repo`, a hidden option for the self-test fixture repository.

**7. [Observation] Probe branch name.** The probe ran on `rehearsal/v0.2.0` because the tag is now derived from the branch and the tree is 0.2.0. That repoints the runner's `v0.2.0` tag, so four tests that read it fail inside the rehearsal's CTest stream: `ledger_freeze` and `ledger_freeze_controls` (`REJECT tag-blob-digest`) and `perf_attribution` and `perf_attribution_merges` (`REJECT attribution-git`). This cannot happen on `rehearsal/v0.2.1`, which does not touch `v0.2.0`. It is a probe artefact, not a defect, but it explains four extra failing tests in run 40216415155.

**8. [Minor] Commit trailer.** Commits end with `Co-Authored-By: Claude Opus 5.5` as instructed.

**Total deviations:** 8 (1 pending ratification, 1 needing an owner decision before 16-07, 3 blocking or bug fixes, 3 minor).

## Items needing ratification

- D-111 (deviation 1).
- The delivery-validator gap (deviation 2): decide who edits `verify-v02-delivery.py` and the evidence collection, or whether the release can ship another way.
- The owner must record the performance review decision for the exact v0.2.1 measurement. This plan only landed the plumbing and created no record.

## Facts 16-07 needs

- **Rehearsal branch:** the tag is derived from the branch, so it must be `rehearsal/v0.2.1` on a tree whose CMake VERSION and manifest both say 0.2.1. Keep the branch until the release publishes: `verify_receipt` and `--verify-reuse` read the candidate commit.
- **Window edits that must agree:** `docs/support/v0.2.1.md` generated with `verify-support-ledger.py --write-current`; README `[versioned support ledger](docs/support/v0.2.1.md)`; `docs/preview.md` `[v0.2.1 support ledger](support/v0.2.1.md)`; `docs/release.md` `[support ledger](support/v0.2.1.md)`. `--check-binding` and `verify-v02-adoption.py --check docs` follow the selected ledger and fail until all four agree. `docs/release.md` keeps the literal "makes no publication claim for v0.2.0".
- **Release notes (PR #75 body):** must contain the version token, the ledger link, "No CGB game-level evidence exists.", "unsigned and not notarized", the exact text `+8.3%` and `tests/baseline/perf-attribution-v1.json` (8.3 is computed from the committed receipt: libbet 8.12, tracer 8.31, visible-demo 8.09 percent, maximum 8.3).
- **Performance review:** run the rehearsal first (pending run, retained artifact `rehearsal-performance-<run>-<attempt>`), then dispatch `release-rehearsal.yml` on the same branch with `measurement_run_id` and `performance_decision`. The workflow file is on main once this PR merges.
- **Dispositions flip:** closure needs a top-level `receipts` object: `tag`, `tag_sha`, `rehearsal_run` {id, head_sha, head_tree, conclusion}, `trusted_judge` {id, conclusion}, `nightly_asan_run` {id, head_sha, head_tree, conclusion}, `release_readback` {path, sha256} and `pr_closures` {path, sha256}. The readback JSON needs `tag`, `tag_sha`, `is_draft: false`, a non-empty `assets` list and a non-empty `reconciliation` object. The pr-closures JSON is `{"prs": [{number, state: "CLOSED", closed_at, comment_url, changed_paths}]}` for exactly #78-#92. Boundary check: `python3 -I tests/scripts/verify-v03-dispositions.py --check <record path> --rev <boundary commit>`.
- **Ledger rows to re-cite after the release:** `release.yml:attach-v02-evidence`, `release.yml:candidate-fuzz`, `release-rehearsal.yml:judge`, `:corpus`, `:performance` and `:aggregate`, all `release_bound` and rejected once VERSION passes 0.2.1.
- **Last pre-window change (D-01):** this plan lands the final tests, cmake, `.github` and docs changes. After it, nothing ledger-pinned changes on main until the window.

## Known Stubs

None.

## Threat Flags

| Flag | File | Description |
|------|------|-------------|
| threat_flag: producer-token | .github/workflows/release-rehearsal.yml | The `performance` and `aggregate` jobs hold `actions: read` and a `github.token` in one gh-only step that fetches an earlier run's artifact; the policy pins the step, the run, branch and tree checks, and the tokenless apply step (T-16-17). |
| threat_flag: producer-token | .github/workflows/release.yml | `candidate-performance` holds `actions: read` and a token in one gh-only step that downloads the newest successful rehearsal run's receipt, accepted only through `--verify-reuse` (T-16-18). |

## Self-Check: PASSED

- Created files present: tests/scripts/verify-v03-dispositions.py and 16-DISPOSITIONS.json (on the PR branch).
- Commits 82789c5, 3b9563f, 7548874 and bd43d7b are ancestors of origin/gsd/phase-16-06-ledger-freeze-and-dispositions; the PR head is bd43d7b.
- `git diff --quiet bdb3525 bd43d7b -- src include` holds; `.planning/config.json` and `.planning/milestone.lock` were never staged and the config.json diff survived every branch switch.

---
*Phase: 16-tune-up-and-v0-2-debt-closure*
*Completed: 2026-10-25*
