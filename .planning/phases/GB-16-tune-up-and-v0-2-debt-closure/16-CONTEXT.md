# Phase 16: Tune-up and v0.2 Debt Closure - Context

**Gathered:** 2026-10-24
**Status:** Ready for planning

<domain>
## Phase Boundary

v0.3 feature work starts from a clean, fast and honest baseline:
- The v0.2 phase records are archived behind a lint (TUNE-01).
- The Phase 8 verifiers run in CTest (TUNE-02).
- DMG performance and CI budgets are gated (TUNE-03, TUNE-04).
- Planning hygiene is machine-checked (TUNE-05).
- `v0.2.1` is published from release-please PR #75, with the D-106 dispositions recorded (TUNE-06).

Phase 16 changes nothing under `src/` or `include/`. Save states (Phase 17), the host contract (Phase 18) and performance fixes are out of scope.

How these decisions were made:
- Five parallel advisor researchers (archive/lint, perf gate, CI budget, release path, gap sweep).
- Owner-delegated synthesis, following the standing "fan out, then auto-follow" preference.
- An adversarial review of the draft, which found 3 blockers and 7 major issues, all applied below.
- Three owner decisions: D-13, D-29 and D-07.

Measured facts come from read-only repo, `gh` and local cachegrind probes on 2026-10-24. Hosted receipts remain the authority.

</domain>

<decisions>
## Implementation Decisions

### Sequencing and plan partition
- **D-01: Release last.** Every `tests/`, `cmake/`, `.github/` and docs change lands on main before the v0.2.1 window opens (D-31).
  - Reason: the ledger pins `tests/CMakeLists.txt`, `tests/expected-tests.txt` and verifier scripts, so any later CTest addition invalidates it.
  - Reason: TUNE-06 requires the rehearsal and judge green at the exact head.
  - Rejected: release-first. It needs two ledger regenerations and a split of the archive.
- **D-02: Partition. Cap 8; target 7 plans, keeping one slot for the single gap round. The planner may merge plans but not exceed the cap.**
  1. 16-01: archive, phase-path lint, retargets, HDMA lane extraction, broken 15.1 rows (TUNE-01; D-05..D-10). This is the largest plan.
  2. 16-02: perf attribution receipt and Ir gate (TUNE-03; D-13..D-17).
  3. 16-03: per-test budget ratchet, ASan sharding, bounded PR replay, nightly lane, temp hygiene (TUNE-04 a, b; D-18, D-19, D-23).
  4. 16-04: timeout ledger, planning-only classifier with `required-native` branching, label lint (TUNE-04 c, d; D-20..D-22).
  5. 16-05: plan-cap, LESSONS-id and STATE-size checks, Playstead docs, Phase 8 verifiers (TUNE-05, TUNE-02; D-11, D-12, D-24..D-27).
  6. 16-06: release-path preparation. Covers version-agnostic checks, the two-digest ledger freeze, the perf review-disposition path, the release-notes needles, and the disposition-record schema with pending-release rows (D-28..D-30, D-33).
  7. 16-07 (closeout): release window, publication, readback, PR closures and the post-release disposition flip (D-31..D-33).
- **D-02a: Order and serialization.**
  - Order: 16-01 → 16-02 → 16-03 → 16-04 → 16-05 → 16-06 → 16-07.
  - 16-05 may run in parallel with 16-02 or 16-03 only if new CTests go in per-area `tests/cmake/*.cmake` includes. 16-01 owns the one-line `include()`.
  - Serialized hotspots: `tests/CMakeLists.txt`, `tests/expected-tests.txt`, `.github/workflows/ci.yml`, `.github/scripts/verify-workflow-policy.py`, and the `required-native` `needs` list.
  - 16-02 and 16-03 each add jobs. 16-04's timeout ledger then requires rows for them. A plan landing after 16-04 adds its own provisional rows (D-20).
  - Dispatch flows take two merges. A `workflow_dispatch` workflow must reach main first; a later PR commits its downloaded artifact (receipt or evidence). A dispatched job never pushes to protected main.
- **D-03: No `feat:` titles before the v0.2.1 tag.** Commit and squash titles use `fix`, `perf`, `test`, `ci`, `docs`, `chore` or `build`.
  - Reason: before 1.0, one `feat` turns PR #75 into 0.3.0.
  - Fallback if a `feat` slips through: a `Release-As: 0.2.1` footer.
  - No title lint is added.
- **D-04: No `src/` or `include/` change in Phase 16.**
  - v0.2.1's source delta over v0.2.0 is exactly the five `src/` files changed by `09805f3` (#93), `2d25a47` (#94) and `79e20f3` (#97): `gabbaboy.c`, `gbb_accept_input.h`, `gbb_accept.h`, `stepper.c` and `acceptance.c`. `include/` is unchanged.
  - The perf gate uses external tooling only.
  - The DMG baseline stays green with zero changed rows. The full-suite `dmg_baseline` result is the receipt, recorded as a normal `automated` coverage item.
  - If any TUNE item turns out to need `src/` (for example bounding the ASan replay), stop and escalate to the owner.

### Archive and phase-path lint (TUNE-01)
- **D-05: Archive.** `git mv` exactly the 10 directories GB-07 … GB-15.1 (578 tracked files) to `.planning/milestones/v0.2-phases/`. This is the same layout `/gsd-cleanup` and v0.1 use, and the GSD phase locator already scans it.
  - Leave GB-16 in place.
  - Move the stray `.planning/verify-v02-milestone-audit.py` beside the v0.2 audits.
  - Do not rewrite archived contents: they are digest-pinned by the 15.1 records. Add one archive README note.
  - Repoint only live docs (STATE, PROJECT, research/INDEX, HANDOFF.json and similar).
  - Keep each commit green, and keep the move atomic with its retargets.
- **D-06: Lint `tests/scripts/verify-no-phase-paths.py` plus a CTest.**
  - Scope: all git-tracked text (`grep -I`) outside `.planning/`.
  - Spellings caught: the literal, joined path segments, backslashes, and `${PROJECT_SOURCE_DIR}`-prefixed forms.
  - Allowed: `.planning/milestones/v<N>.<M>-phases/`.
  - Allowlist: a count-pinned (file, max, reason) table, so stale zero-hit entries fail. It starts with:
    - the single CMake variable `GBB_LIVE_PHASES_DIR`;
    - the `PHASE` constant in `verify-phase8-closure-contract.py` (the player verifier has no hit, so no row);
    - the `verify-closeout-scan.py` temp-fixture layout strings.
  - Anti-vacuity: a scanned-text-file floor measured at plan time (404 text files exist today, for example ≥ 380), plus named must-scan files: `tests/CMakeLists.txt` and two or three scripts.
  - Controls: each spelling and each scope root rejects, and a clean `milestones/v0.2-phases` string passes.
- **D-07 (owner: disclosed interpretation, 2026-10-24).** TUNE-01 forbids tests from reading completed-milestone records from `.planning/phases`. Live reads of the current milestone go through the one allowlisted `GBB_LIVE_PHASES_DIR`, which the lint enforces; live `summary_coverage` and the D-24 plan-cap check need it.
  - REQUIREMENTS.md and D-105 are not edited. Record this interpretation in the phase verification and the discussion log.
  - Remove the Python default `--phases-dir .planning/phases` (`verify-summary-coverage.py:300`).
- **D-08: Retargeting v0.2 readers.**
  - Point frozen-record readers through `GBB_V02_PHASES_DIR` at the archive: dispositions, historical-limitations, red-evidence privacy, the `uat_closure_*` tracked phase, and the v0.2 `summary_coverage --since 9` sweep.
  - Embedded paths (`scope.file`, `published_receipt`): strip the `.planning/phases/` prefix and rejoin under the archive dir, failing if the file is missing. No basename search. Pinned JSON bytes stay untouched.
  - Every directory-sweeping test gets a minimum count (`--min-files` or `GBB_EXPECT_MIN_KEY`). Summary coverage today is `files=143 entries=546`, and it passes vacuously on an empty dir.
  - Copy only the 2.4 KB `14-UAT-REVIEW.md` seed into `tests/data` for `verify-closeout-scan.py`.
- **D-09: HDMA helpers.**
  - Extract only `lane_contract`, `lane_self_test` and the remote-evidence validators into `tests/scripts/verify-hdma-lane.py`. Keep the existing CTest names.
  - Drop the ASan `timeout-minutes: 45`, `--parallel 4` and `TIMEOUT` assertions and their two mutants (TUNE-04 supersedes them). Add one fixture-repro needle control.
  - Retire the orphaned, already-red `tests/scripts/phase13-handoff-continuity.test.cjs` and the non-lane GB-13 modes. The other GB-13 scripts stay archived.
- **D-10: Broken 15.1-VALIDATION rows.** Rows 34-1, 34-2, 35-2, 35-3, 36-1, 36-2 and 36-3 read live or HEAD-relative state. Convert the ones that run in CTest to boundary-commit reads. Rows that are not executed get a "superseded by Phase 16 archive" disposition in the D-33 record. No archived file is edited.

### Phase 8 verifiers (TUNE-02)
- **D-11: Wire six CTests through `expect_exit.cmake`:** a plain pass, `--self-test`, and a `--boundary v0.2.0` rejection for each of `verify-phase8-closure-contract.py` and `verify-phase8-player-contract.py`.
  - Add a `--boundary <rev>` argument.
  - Closure self-test: assert the minimum `rejected_controls >= 157`. The plain run prints `=0`, so a bare regex would be vacuous.
  - Wrong boundary: closure expects `missing historical clause`; player expects `phase8-player-contract: FAIL`.
- **D-12: Pin the boundary.** `96d5eec` is not an ancestor of main. It lives only on `gsd/phase-08-cartridge-seam-mbc5-and-mbc2`, whose PR #64 is already merged. #91's branch does not contain it.
  - Push the annotated tag `historical/phase-08-boundary` on `96d5eec` before any branch cleanup.
  - The verifiers default to that tag and fail closed if it is unreadable.
  - **Reversibility:** costly — deleting both the tag and that branch orphans the verifiers' only input.

### Performance (TUNE-03)
- **D-13 (owner decision 2026-10-24): accept with attribution. No performance fix in Phase 16.**
  - Facts (local cachegrind, deterministic Ir):
    - v0.2.0 is +25.7% over v0.1.0. Two thirds of that is Phase 7: exactly 32 Ir per half-dot in `advance_devices_to`. The audio-mix ÷16 cause is a hypothesis to annotate, not a fact.
    - Post-v0.2.0 src work adds +8.3% (`apply_input_events_now` polling with an empty queue).
    - HEAD/v0.1.0 is 1.36.
  - The v0.2.1 release notes disclose the +8.3% against v0.2.0. That is checked (D-30).
  - New seed RM-023 (perf recovery): an empty-queue input early-out (about 8% of v0.2.0) and the Phase 7 mixer cost (about 17% of v0.1.0). Trigger: before v0.5 PPU/FIFO work, or any milestone touching the hot path.
- **D-14: Gate design.**
  - Proxy: cachegrind `Ir` (`--cache-sim=no`) on a Release build. Install `apt-get install valgrind` on pinned `ubuntu-24.04`, retried once inline. Record the gcc and valgrind versions.
  - Workload: `measure_core` with tracer, libbet and visible-demo at 1,000,000 half-dots, DMG-CPU-B. Pinned digests are `4c7a57ff3d50d228`, `7d992ad8eee13c40` and `3c5797f6525df9c7`.
  - Baseline: built in the same job from `v0.2.0`, with the tag verified to equal `ab301aa69b1f085050fd66bf7b1378863a0821f2`.
  - Ir limit: fail if head Ir / v0.2.0 Ir exceeds 1.10 on any ROM (today 1.081–1.083).
  - Validity guards:
    - two head runs agree within 0.02%, else `proxy-nondeterministic`;
    - Ir above 100M and `consumed_half_dots=1000000`, else `proxy-vacuous`;
    - digest equal to the pin, else `workload-digest-mismatch`.
  - Realtime floor: min-of-9 native Release wall time with one retry; floor = max(2.0×, 0.6 × the realtime multiple recorded by the D-17 hosted dispatch). It gates from the day it lands.
  - Limits live in `tests/baseline/perf-gate-v1.txt`. Raising a limit needs a DECISIONS entry; lowering one is free.
  - The limitation note names the blind spots: PPU, sprite, DMA and banking are barely exercised (about 87% of Ir is `advance_devices_to`), and Ir misses cache and branch effects. CGB `colour-attr` is informational only.
- **D-15: Gate verification.**
  - A valgrind-free CTest runs everywhere on canned cachegrind and timing outputs in `tests/data/`. It covers the parser, Ir-limit arithmetic, schema, and a realtime case whose canned multiple is below the floor and must fail.
  - In the hosted `perf-gate` job, an anchored scratch-tree patch adds about 12 Ir per half-dot inside `advance_devices_to`. It must fail with `ir-budget-exceeded` while the digest stays equal.
  - A no-op twin patch must pass, and a missing anchor fails loudly. A missing valgrind fails the job.
- **D-16: Placement.** The `perf-gate` job runs on non-planning PRs (D-21 classifier), on push to main, and in the tag-bound release rehearsal. It feeds `required-native` and is not a new required context. It has a timeout-ledger row (D-20).
- **D-17: Attribution receipt.**
  - A hosted `workflow_dispatch` job (two-step flow, D-02a) measures:
    - every first-parent merge in `v0.1.0..v0.2.0`;
    - every first-parent commit in `v0.2.0..HEAD` that touches `src/` (`09805f3`, `2d25a47`, `79e20f3`);
    - HEAD.
  - The job also records the hosted realtime multiple.
  - Its artifact is committed as one JSON receipt naming revision, build, runner, workload, model, digests and uncertainty (0 across repeats).
  - A valgrind-free CTest checks:
    - the commit set equals the `git rev-list --first-parent` selection;
    - every delta recomputes from the raw per-commit rows;
    - the digests are constant.
  - Controls: a dropped commit, an altered raw row, and an altered delta are each rejected.
  - This closes LIM-PERF-REVIEW.

### CI budget (TUNE-04)
- **D-18: Per-test budget is a static `TIMEOUT` ratchet** (deterministic, no wall clock, per D-102).
  - A checker reads `ctest --show-only=json-v1`. A test's base `TIMEOUT` must be at most 60 s; under the sanitizer ×3 scale that is an effective 180 s, inside the 300 s sanitizer budget.
  - A larger timeout needs a row in `tests/ci/test-budget-allowlist`: name, ceiling, `expires` (project minor), `ref` and shrink trigger.
  - A ratchet against the base commit blocks raising a ceiling.
  - Seed the allowlist only from the json-v1 scan. A static grep finds about 40 literal values over 60.
  - A non-gating "10 slowest" list is printed in the job log.
  - Do not extend the CGB-specific GB-CI-007 parser.
- **D-19: ASan critical path.**
  - Shard `acceptance_stall_diagnosis` into single-replay named tests, and split `v02_consumer_controls` into per-consumer tests.
  - The PR lane runs a bounded stall replay with a negative control. The full ASan replay moves to `nightly-asan.yml` (`schedule` plus `workflow_dispatch`).
  - The bounded replay is mandatory (success criterion 3). If no frame cap exists, add a short-budget stall case under `tests/data`. If bounding needs `src/`, escalate (D-04).
  - Red nightly: an inline `if: failure()` step uses `gh issue` to open or comment on one `nightly-red` issue (job-scoped `issues: write`).
  - Release binding: the rehearsal dispatches `nightly-asan.yml --ref` at the rehearsal head, and that run must be green. It binds to the squash-merged commit by tree equality (D-31). A scheduled run is never required on a non-main SHA.
  - The PR-time negative control checks the lane definition.
  - This closes LIM-ASAN-STALL-TIMING.
- **D-20: Timeout ledger.**
  - Add `.github/ci-timeouts.json`, checked in `verify-workflow-policy.py`.
  - Scope: every job with `timeout-minutes` in every workflow.
  - Each row holds `timeout_minutes`, `cited_run_id`, `cited_sha`, `p50_minutes` and `samples`.
  - Rules:
    - timeout ≥ ceil(2 × p50), which also satisfies the ≤ 60% rule;
    - the ledger value equals the YAML value;
    - every job has a row;
    - whole-run budget: the maximum p50 over the jobs gating `required-native` is ≤ 30 min (static, on ledger values).
  - New jobs may cite a provisional PR run, marked `provisional`. Those rows are re-cited from a main run before the D-31 window. A `provisional` row at the release head fails.
  - Seeds come from real runs: Windows p50 23 → at least 46 (use 50); macOS 40; ASan tests 45. ASan acceptance rows come only from post-shard runs.
  - Controls: edited timeout, missing row, p50 over 50% of the timeout, stale value, a new job with no row, `provisional` at the release head.
  - Optional online `--verify-cited` runs as an advisory step at boundaries, never in CTest.
- **D-21: Planning-only lane.**
  - A job-level `changes` classifier feeds the existing inline aggregator `required-native`.
  - `kind=full`: all heavy jobs `success`.
  - `kind=planning`: `changes` and a real `planning-checks` job (configure, then `ctest -L planning --no-tests=error`) succeed, and every heavy job is exactly `skipped`.
  - Anything else counts as full.
  - Allowlist: only `.planning/**` and `AGENTS.md`. Not `*.md` in general, because tests read README and docs.
  - The classifier fails closed to full on:
    - renames out of `src/` (`--name-status --no-renames`);
    - `..`, case variants, symlinks or submodules;
    - an empty diff, too many files, or a missing or zero `before`;
    - tags.
  - It runs on push-to-main too. The base commit's copy of the classifier decides.
  - Branch protection is unchanged: `required-native`, `fixture-repro` and `preview-package-smoke` keep their names. `changes` and `planning-checks` are never required contexts.
  - `fixture-repro` and `preview` still run on planning PRs in Phase 16 (deferred).
  - No `pull_request_target` and no third-party actions (D-096).
- **D-22: Planning-label lint.** Any test reading `.planning/` or `AGENTS.md` must carry the `planning` label, and no planning-labelled test may need a built target. Control: an unlabelled fixture test that reads `.planning/`.
- **D-23: Temp hygiene.** `check_sanitizer_timeout_policy.cmake` removes its `sanitizer-timeout-policy-<nonce>` dir on success, keeps it on failure, and sweeps stale siblings at start. A control asserts none remain after a pass.

### Planning hygiene (TUNE-05)
- **D-24: Plan-cap check.**
  - Scope: phases of the active ROADMAP milestone only (v0.2 had no cap lines).
  - Parse `**Plan cap**: N` under each active phase heading, and count `NN-NN-PLAN.md` files via `GBB_LIVE_PHASES_DIR`. Gap-closure plans count; decimal phases count against their parent unless they have their own cap line.
  - A plan count above the cap fails. The 50% "rescope" threshold in D-102 is a planning rule, not this check.
  - Also require each cap ≤ 12 and the milestone sum ≤ 40. An active phase without a cap line fails.
  - Applies to Phase 16 from the plan that lands it. Control: an over-cap fixture.
- **D-25: LESSONS ids.**
  - Keep the earliest occurrence of each duplicated id and renumber the later ones:
    - `GB-FIXTURE-001` at line 225 becomes `GB-FIXTURE-003`;
    - `GB-FIXTURE-001` at line 846 becomes `GB-FIXTURE-004`;
    - `GB-TEST-001` at line 234 becomes `GB-TEST-007`.
  - Fix the inbound reference at line 294.
  - Leave historical mentions (XFER-016, SIBLING-YOUNGER-CORES) with a "renumbered in Phase 16" note.
  - A checker rejects any duplicate `### ID`.
- **D-26: STATE.md bound.**
  - Move the historical handoff, verification-refresh, Decisions and Performance-Metrics blocks (now 639 lines, 76.8 KB) to `.planning/milestones/v0.2-STATE-ARCHIVE.md`.
  - Keep the GSD frontmatter and Current Position byte-compatible with what the runtime writes.
  - Size the bound from STATE.md growth per phase in git history (`git log -p` over Phases 15/15.1), with roughly one milestone of headroom. Target about 250 lines and 40 KiB.
  - The control is an oversized fixture, never the live file.
  - Keep `auto_prune_state` false.
- **D-27: Playstead docs.**
  - Correct README:46, `docs/native-integration.md:278-281` and `.planning/research/PRECEDENT.md:24,98-104` to PLAYSTEAD-CONTRACT §5: GB, GBC and GBA through mGBA 0.10.5 on Playstead main `234bd45b21`; process adapters, not libretro or FFI.
  - Keep the true limit sentences that `verify-v02-adoption.py:143,152` requires.
  - The check rejects the stale pin `a102d608`, the "GBA/mGBA" wording and the `1de3e95` "blocked-capability" claim.

### v0.2.1 release (TUNE-06)
- **D-28: Ledger and version binding.**
  - Create `docs/support/v0.2.1.md` (schema 2, `--write-current`). `select_ledger` and the `LEDGER_NAME` pattern then bind it to tag v0.2.1.
  - In 16-06, parameterize the hardcoded `0.2.0` and `v0.2.0.md` in `verify-support-ledger.py`, in `verify-v02-adoption.py` (`RELEASE_VERSION`, ledger link, release-notes checks) and in the rehearsal `REHEARSAL_TAG`.
  - Make the CTest regexes version-agnostic. For example, `tests/CMakeLists.txt:1405` pins `version=0.2.0` today.
  - Binding rule: the newest ledger ≤ the CMake/manifest version, and README links that ledger.
    - On main (CMake 0.2.0) that is v0.2.0.md.
    - On the #75 head (0.2.1) it is v0.2.1.md.
  - The version-bound edits (the `v0.2.1.md` ledger and the README link repoint) are committed onto the #75 branch in the D-31 window, after release-please's last regeneration. They never land on main beforehand.
  - The trusted judge checks out main, so it takes the version from the tag input and cross-checks the tagged tree. It never falls back to v0.2.0 (D-101).
  - The `--check-current` mismatch on main after the tag is expected; the v0.3.0 ledger replaces it.
- **D-29 (owner decision 2026-10-24): accept and pin both v0.2.0 ledger digests.**
  - #93 (`09805f3`) appended a 12-line performance-history paragraph to `docs/support/v0.2.0.md` after the tag, and `verify-v02-adoption.py:109-127,162-163` now requires it.
  - The freeze CTest asserts:
    - the `v0.2.0` tag blob = `a542a5c0…2b8f` (full digest in the checker);
    - the working file = `c47ff12b089fd386ebe1dd1a16d4ceaefc9fd60d072acdce510267c3dff19a9e`;
    - the diff from tag to working file is exactly that one appended block.
  - The tag compare is mandatory in CI; a missing tag fails.
  - Controls: a flipped byte, a wrong pin, and an extra edit outside the block.
  - The #93 append is recorded in the D-33 record as a disclosed exception to D-106's "never rewritten". No revert.
- **D-30: Release performance qualification uses the existing D-101 path.**
  - `verify-v02-performance.py:144-175,398-407` already accepts a receipt-bound reviewed disposition (`accepted-with-disclosed-regression`); v0.2.0 shipped through it at +14.86%.
  - v0.2.1 keeps the paired wall-clock gate. It satisfies the trigger with a separately recorded, receipt-bound review decision citing D-13 and the D-17 receipt.
  - The D-14 Ir gate runs as an additional check. No gate is weakened.
  - Parameterize the baseline only where the review path needs the v0.2.1 version.
  - `verify-v02-adoption.py --release-notes` gains a required +8.3%/attribution needle with a negative control.
- **D-31: Release window (closeout plan 16-07). Any main push during the window regenerates #75 and wipes hand edits.**
  1. Make the last Phase 16 merge to main, then freeze main merges.
  2. Let release-please regenerate #75, then bring the branch up to date with main (strict protection).
  3. Edit the **PR #75 body** (where v0.2.0's preface lived in #70), not CHANGELOG. It needs the version token, "No CGB game-level evidence exists.", "unsigned and not notarized", the exact-version ledger link and the +8.3% disclosure.
  4. Push the version-bound commits (D-28: generate `v0.2.1.md` from that tree, repoint README) under a user identity, so `pull_request` CI starts. A `GITHUB_TOKEN` push starts nothing.
  5. Push `rehearsal/v0.2.1` at that head. The rehearsal, the trusted judge and the dispatched `nightly-asan` (D-19) must be green there.
  6. Squash-merge #75 once the required checks pass on the exact head. Verify that the merged tree equals the rehearsed tree (`git rev-parse <sha>^{tree}`).
  7. Let `release.yml` publish, then reconcile the asset readback.
- **D-32: PRs #78–92.**
  - Close all 15 as superseded by #93, each with a one-line comment naming #93 and the archive location.
  - Verified: none touches `src/` or `include/`, and every test, CMake or AGENTS delta is already on main or superseded.
  - Authorized by D-106. Do it after the D-12 tag exists; branch deletion is optional.
- **D-33: Disposition record and the Phase 16 boundary.**
  - In 16-06, land a new v0.3 disposition record (do not edit the digest-pinned v0.2 `15.1-DISPOSITIONS.json`) and its CTest. Release-linked rows sit in a validated `pending-release` state.
  - The `closeout_dispositions` expectations update, with a control, so they stop asserting `owner_accepted=0` for the new record.
  - Rows:
    - Pending until release: LEDGER-PIN (D-28/D-29), PERF-REVIEW (D-17), REHEARSAL-FAILED and TRUSTED-JUDGE (D-31).
    - Closed by D-19: ASAN-STALL-TIMING.
    - Accepted for later: the three D-106 items. Dropped as accepted: the four D-106 items.
    - The #93 ledger append (D-29) and the D-10 superseded rows.
  - Unmapped audit items:
    - Phase 13 `13-VERIFICATION.md` padding loss: accepted as history.
    - GR-IN-03 and GR2-IN-01 Info items: seeds.
    - 15.1-31/32/33 `requirements:` key and the 47 legacy Phase 9/10 SUMMARY problems: accepted as history.
  - After publication, a planning-only commit flips the release-linked rows to closed. The checker accepts closure only with tag-bound receipt digests: the rehearsal run, the judge, and the release readback.
  - **That post-release commit is the Phase 16 verification boundary (D-103).** At that commit, every success-criterion-5 fact (published, readback reconciled, PRs closed, dispositions recorded) is point-in-time.

### Claude's Discretion
- Exact script names, the per-area CMake fragment layout, allowlist file formats, the measured lint floor and the STATE bound, all within the rules above.
- Whether to merge plans further below 7.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Scope and decisions
- `.planning/ROADMAP.md` §Phase 16 — goal, five success criteria, plan cap 8, milestone-wide rules
- `.planning/REQUIREMENTS.md` — TUNE-01..06 (TUNE-01 read per D-07)
- `.planning/context/DECISIONS.md` — D-069, D-096, D-101, D-102..D-106
- `.planning/phases/GB-15-cgb-acceptance-support-ledger-and-v0-2-0-release/15-CONTEXT.md` D-22 (paired perf trigger; moves to `milestones/v0.2-phases/` in 16-01)
- `.planning/research/v0.3/DELIVERY-VELOCITY.md` — CI durations, LIM table, P5/P8
- `.planning/research/v0.3/SUMMARY.md`, `ADVERSARIAL-REVIEW.md`, `PLAYSTEAD-CONTRACT.md` (§5 for D-27)
- `.planning/milestones/v0.2-MILESTONE-AUDIT.md` — tech debt (D-33); its line 124 covers the 15.1-VALIDATION live rows (D-10)
- `.planning/context/LESSONS.md` — GB-GSD-024, GB-GSD-026, GB-CI-004, GB-CI-007, GB-CI-010, XFER-016
- `.planning/context/FUTURE-MILESTONES.md` — add RM-023 (D-13)

### Code touched
- `tests/CMakeLists.txt` (1208, 1405, 2670, 2687, 4653), `tests/expected-tests.txt`, `tests/expect_exit.cmake`, `cmake/ExpectedTests.cmake`
- `tests/scripts/`:
  - `verify-summary-coverage.py`, `verify-closeout-dispositions.py`, `verify-historical-limitations.py`, `verify-closeout-scan.py`
  - `test-cgb-red-evidence-privacy.py`, `test_hdma_remote_evidence.py`, `phase13-handoff-continuity.test.cjs`
  - `verify-phase8-closure-contract.py`, `verify-phase8-player-contract.py`, `verify-uat-closure.py`
  - `verify-support-ledger.py`, `verify-v02-adoption.py`, `verify-v02-performance.py`, `measure-release-baseline.sh`
- `.planning/phases/GB-13-cgb-hdma/verify-hdma-closure.py` (lane code source)
- `tests/measure_core.c`, `tests/baseline/dmg-cpu-b-v1.txt`
- `tests/acceptance/CMakeLists.txt`, `tests/check_sanitizer_timeout_policy.cmake`, `cmake/ScaleSanitizerTimeouts.cmake`
- `.github/workflows/`: `ci.yml`, `preview.yml`, `fixture-repro.yml`, `libbet-repro.yml`, `release.yml`, `release-rehearsal.yml`, `release-please.yml`
- `.github/scripts/verify-workflow-policy.py`, `check-player-result.sh`
- `docs/support/v0.2.0.md`, `README.md`, `docs/native-integration.md`, `.planning/research/PRECEDENT.md`

### External
- release-please README ("Release-As") and `docs/manifest-releaser.md` (`bump-patch-for-minor-pre-major`, `always-update`)
- Valgrind cachegrind manual; the rustc-perf `instructions:u` rationale
- GitHub docs: troubleshooting required status checks (path-filtered workflows stay Pending; `if:`-skipped jobs report success); `GITHUB_TOKEN` pushes do not trigger workflows

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `required-native` in `ci.yml` is already an `if: always()` inline aggregator over `needs.*.result`, pinned by mutation controls in `verify-workflow-policy.py`. Extend it; do not add a required check.
- `verify-workflow-policy.py` already checks `fuzz-wait-budget` arithmetic against `timeout-minutes`, which is the D-20 precedent.
- `expect_exit.cmake` with `GBB_EXPECT_MIN_KEY`/`GBB_EXPECT_MIN_VALUE` serves anti-vacuity minimums.
- `measure_core` plus `measure-release-baseline.sh --ab` supplies the frozen D-22 workloads.
- `verify-v02-performance.py` has the reviewed-disposition path (D-30).
- `verify-uat-closure.py <phase-dir>` takes the directory as an argument.

### Established Patterns
- `gabbaboy_verify_registered_tests()` (tests/CMakeLists.txt:4653) makes every test addition a two-file change with `expected-tests.txt`.
- Checkers read immutable commits via `git show <sha>:path`. CI checkouts use `fetch-depth: 0`.
- Sanitizer lanes multiply `TIMEOUT` ×3.

### Integration Points
- Branch protection requires `required-native`, `fixture-repro` and `preview-package-smoke` (strict, admins enforced, no required reviews). PR #75 currently reports no checks and is based on `79e20f3`.
- The trusted judge checks out default-branch code, so judge-side changes must be on main before the rehearsal.
- Pre-existing uncommitted `.planning/config.json` edits belong to the owner. Stage by path and never sweep them into a phase PR.

</code_context>

<specifics>
## Specific Ideas

- Rehearsal at 79e20f3 (run 40043165875) failed on `--check-current` (two jobs) and the perf trigger (median 130.42%, pending a receipt-bound review). The judge was skipped through `needs`.
- Local Ir by revision:

  | Revision | Ir |
  |---|---|
  | v0.1.0 | 185.78M |
  | Phase 7 | 217.78M (+32.0M) |
  | Phase 12 | 234.12M |
  | v0.2.0 | 233.52M |
  | `2d25a47` | 252.94M |

  Output digests are constant across all 15 builds.
- Hosted job minutes (4 green main runs), against their limits:

  | Job | Minutes | Limit |
  |---|---|---|
  | Windows | 17–23 | 30 |
  | macOS | 18–20 | 30 |
  | ASan tests | 17–22 | 45 |
  | ASan acceptance | 11–26 | 45 |

</specifics>

<deferred>
## Deferred Ideas

- RM-023 perf recovery: an empty-queue input early-out and the Phase 7 mixer cost (D-13).
- A PPU-heavy, cleanly licensed perf workload and a longer workload id, before v0.5 PPU/FIFO work.
- Extending planning-only classification to `fixture-repro` and `preview`, after measuring the savings.
- Folding the three required contexts into one aggregator. This needs an owner branch-protection change.
- A title lint for `feat` before patch releases (Release-As is the fallback).

</deferred>

---

*Phase: 16-tune-up-and-v0-2-debt-closure*
*Context gathered: 2026-10-24*
