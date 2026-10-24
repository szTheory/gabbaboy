# GabbaBoy delivery efficiency: v0.1 to v0.2, and input for v0.3 scoping

Analysis date 2026-10-24, repo head `02776e5` (main, v0.2 archived). Read-only. Sources: `.planning/RETROSPECTIVE.md`, `MILESTONES.md`, `milestones/v0.2-MILESTONE-AUDIT.md`, `milestones/v0.2-ROADMAP.md`, `context/LESSONS.md`, `STATE.md`, phase directories, `15.1-DISPOSITIONS.json`, `git log` and `git diff --numstat` across the phase merge commits, `gh pr list/view`, `gh run list/view` (409 `ci` runs since 2026-10-10), and `build/Testing/Temporary/LastTest.log` (the full local run on 2026-10-24).

Caveats: plan durations in STATE.md are self-reported and only partly recorded. Model mix and session counts were never recorded. Line counts are lines added, so they include generated JSON and pinned fixtures. "Wall minutes" for CI runs are created-to-updated times, not billed job minutes.

---

## 0. Headline numbers

| Metric | v0.1 | v0.2 | Change |
|---|---|---|---|
| Phases / plans | 7 / 64 | 10 / 170 | 2.7x plans |
| Requirements | 35 | 28 | — |
| **Plans per requirement** | 1.8 | **6.1** | **3.3x** |
| Calendar days | 9 | 15 (12 active; nothing ran 10-17..10-19) | — |
| Core C (`src/`+`include/`) at close | 7,029 | 14,644 (+7.6k) | — |
| Core lines added per plan | ~110 | ~45 | 0.4x |
| CTest cases | 184 | 1,183 | 6.4x |
| `tests/CMakeLists.txt` lines | 364 | 4,687 | 12.9x |
| Python verifiers in `tests/scripts` | — | 46 files / 25.3k lines (plus 8.2k sh/cjs) | larger than the core (14.6k) |
| `ci` run wall time, main push | ~1.5 min (10-10) | 22–27 min (10-24) | ~17x |
| Milestone closeout type | verified_closeout | override_closeout (Phase 7–15 verification stale) | regression |

**What the lines went into during v0.2** (lines added, `ab4d4ae..02776e5`):

| Bucket | Lines added | Note |
|---|---|---|
| Core + player C (`src/`, `include/`) | **8,049** | the product |
| `.planning/` | **93,538** | 11.6 lines per core line |
| `tests/scripts/` verifiers | 28,764 | |
| `.github/workflows` | 5,107 | CI yml is now 2,976 lines |
| `tests/` (C tests + generated data) | 154k | ~110k is generated corpus JSON (`cgb-corpus-inventory.json` 53k, `cgb-apu-dispositions.json` 51k) |
| `docs/` | 97k | ~95k is the v0.2.0 support-ledger JSON |

---

## 1. Where the effort went

### 1.1 Per phase

Calendar times run from the previous main merge to this phase's merge. "Closeout plans" are plans whose title is only gates, handoff, docs, lessons or route persistence. "Evidence plans" admit, verify or bind fixtures and receipts, and are mostly essential.

| Phase | Plans | Calendar (h) | CI runs on branch (red) | Gap rounds | Core+player lines | `.planning` lines | Feature / evidence / closeout plans |
|---|---|---|---|---|---|---|---|
| 7 DMG acceptance + baseline | 17 | 16 | 34 (4) | 0 | 3,353 | 7,688 | 9 / 5 / 3 |
| 8 MBC5/MBC2 seam | 10 | 7.5 | 38 (12) | 0 | 447 | 6,013 | 4 / 3 / 3 |
| 9 MBC3 + RTC | 18 | 19 | 32 (3) | 0 | 939 | 7,666 | 9 / 7 / 2 |
| 10 CGB profile/banking | 20 | 10 | 20 (7) | 0 | 1,433 | 8,542 | 12 / 4 / 4 |
| 11 CGB colour | 15 | 13 | 25 (16) | 0 | 946 | 7,612 | 10 / 2 / 3 |
| 12 Double speed | 19 | 27 | 10 (2) | 0 (review follow-up) | 230 | 10,955 | 11 / 4 / 4 |
| 13 HDMA | 12 | 21 | 22 (8) | 0, but 110 commits, 42 of them handoff/route/closure/evidence | 447 | 8,884 | 8 / 2 / 2 |
| 14 CGB-E corpus | 13 | 23.5 | 8 (2) | 0 | 235 | 8,480 | 7 / 3 / 3 |
| 15 Release v0.2.0 | 10 | ~24 (10-20) | 20 (8) + 7 rehearsal | 0 | 4 | 4,983 | 0 / 7 / 3 |
| (refresh/audit stack #78–92) | — | ~24 (10-20..21) | 30 (28) | — | 0 | ~6.2k, never merged | 0 / 0 / 15 PRs |
| **15.1 Hardening + debt** | **36** | **~63** (10-21 18:00 → 10-24 09:00) | 45 (24) | **2** (11 + 6 plans) + Nyquist pass | 401 | **24,054** | 4 behaviour / 10 release-workflow security / 22 metadata, evidence binding, gates and merges |
| Close (2 re-audits, Nyquist, complete) | — | 10 | 8 | — | 0 | 1,222 | — |

Totals:
- Feature phases 7–14: 124 plans in ~137 h (5.7 days) of calendar time.
- Release and everything after it (15, the refresh stack, 15.1, close): 46 plans in about 4.5 days.
- That puts 27% of the plans and roughly 45% of the active calendar after the feature work was done. This matches the retrospective's own note.

### 1.2 Feature work vs verification plumbing

There are three ways to count it, and all three agree on the direction:
- **By plan title:** about 75 of 170 plans (44%) change emulator or player behaviour. About 50 (29%) are essential evidence: fixture admission, oracles, corpus. About 45 (26%) are closeout, metadata, evidence binding or release-workflow hardening.
- **By plans that touch `src/` or `include/` in `files_modified`:** 75 of 170. Phase 15.1 is 3 of 36, and Phase 15 is 1 of 10.
- **By lines:** 8k lines of product against about 127k lines of planning, verifier scripts and CI. Even with every verifier counted as essential, the `.planning` prose alone is 11.6x the product.

### 1.3 Top five sources of overhead

| # | Source | Quantity | Essential or accidental |
|---|---|---|---|
| 1 | **Phase 15.1 retrofits.** Boundary-commit verifiers and evidence re-binding after release. | 36 plans, about 63 h, 24k `.planning` lines, about 7k verifier lines, 3.8k CI lines, 45 CI runs (24 red). Two gap rounds existed because verifiers read live HEAD or trusted-checkout state (GB-GSD-024, GB-VERIFY-002, GB-EVID-002). 6 plans (15.1-11..14, 18, 19) only normalised SUMMARY `coverage:` schema. 6 plans (25–27, 34–36) were gate/merge/route plumbing. | **Mostly accidental.** About 10 release-security plans (token scoping, untrusted producers read-only) and about 4 behaviour fixes (dense input, STOP-resume, held-button fuzz) were essential. The schema normalisation and the "re-bind evidence to an immutable commit" rounds were process debt: verifiers written wrong the first time. |
| 2 | **Verification freshness churn.** | A 15-PR refresh/audit stack (#78–92, about 6.2k lines, about 24 h). Every PR in it is CI-red and stacked on a pre-15.1 base. Its content was redone inside #93 and later PRs (every file it touches already exists on main), so the stack is dead. Then at close the runtime still marked Phases 7–15 stale, which forced `override_closeout`. This is the same lesson as v0.1 (GB-GSD-008), and it repeated. | **Accidental.** The refresh work was spent twice and still did not produce a verified_closeout. |
| 3 | **CI wall time and retry toil.** | Run time went from 1.5 to 25 min. 409 `ci` runs, of which 99 failed and 23 were cancelled (30% red). PR #98 needed 7 attempts. 4 main pushes were cancelled at the timeout (10-21..10-24). The critical path is one test: `acceptance_stall_diagnosis` takes 1,164–1,838 s under ASan. About 20 docs/planning-only PRs (#76, #77, #95, #96, #99–#102 and the #78–92 stack) each ran the full 7-job matrix, about 120 job-minutes apiece. | **Mixed.** Cross-OS, sanitizer and exact-head checks are essential. Re-running timeouts without comparing durations (GB-CI-004, then again GB-CI-010) and running the full matrix for planning-only diffs are accidental. |
| 4 | **Evidence and receipt prose volume.** | 93.5k `.planning` lines. Phase directories hold 34–131 files (Phase 15.1: 131 files, 17.8k lines). VERIFICATION reports run 37–143 must-haves each. The local `build/` dir holds several hundred evidence logs and XML receipts plus about 120 leaked `sanitizer-timeout-policy-*` temp dirs. STATE.md is 636 lines. | **Mostly accidental.** The claim discipline (scoped model and corpus, measured expected failures) is essential and cheap. Restating it in every SUMMARY, VERIFICATION, UAT, VALIDATION and continuation note is not. |
| 5 | **Per-phase closeout plumbing.** | 2–4 closeout plans per phase (about 29 in total). Phase 13: 42 of 110 commits are handoff/route/continuity/evidence fixes, for example `fix(13): require an exact completed stage for handoff routing`. A dedicated `phase13-handoff-continuity.test.cjs` exists only to check the route text. | **Accidental beyond a floor.** The phase pause and recorded route are owner requirements, but they should be one generated artifact plus one check, not hand-maintained prose across six surfaces (GB-GSD-023). |

Essential costs that should **not** be cut:
- Exact-tag release rehearsal, which found 3 defects before tagging.
- The frozen DMG baseline gate.
- Measurement-pinned expected failures.
- Rights-gated fixture admission.
- The automated UAT closure (`verify-uat-closure.py`), which removed every human checkpoint.

---

## 2. Carry-over inventory and recommendations

### 2.1 The twelve open LIM decisions

Source: `15.1-DISPOSITIONS.json`, where every row has `owner_accepted: false`. Most are a single owner sentence. The four release-chain items resolve together in one small release-readiness phase.

| ID | What it is | Rec | Smallest action |
|---|---|---|---|
| LIM-SUPPORT-LEDGER-PIN | `docs/support/v0.2.0.md` pins digests that 15.1 changed, so `--check-current` fails | **v0.3 (first)** | Add a new versioned ledger for post-0.2.0 source. Never rewrite v0.2.0. |
| LIM-PERF-REVIEW | Hosted paired measurement at 79e20f3 gave median ratio 130.42; review pending | **v0.3 (first)** | Attribute the regression (see 2.4), then record a receipt-bound decision. |
| LIM-REHEARSAL-FAILED | Latest hosted rehearsal at 79e20f3 is red | **v0.3 (first)** | Rerun after the two items above. It resolves mechanically. |
| LIM-TRUSTED-JUDGE | Trusted judge skipped because its producers failed | **v0.3 (first)** | Exercised by the same rerun. |
| LIM-ASAN-STALL-TIMING | ASan stall replay is slower; three timeouts were raised | **v0.3** | Fold into test-suite hygiene (§3): this test is the CI critical path. |
| LIM-RESIDUAL-WRITE-JOBS | 5 release jobs keep write authority, as an enforced named set | **Later (accept now)** | Accept the named set. `verify-workflow-policy.py` already pins `residual_write_jobs=5`. Revisit when release jobs change. |
| LIM-HIST-AUDIO-RED | Pre-fix RED run for D-043 was never retained | **Drop (accept)** | Accept the fresh sensitivity evidence as a substitute. History cannot be recreated (GB-GSD-022). |
| LIM-HIST-M7 | M7 control failure has no diagnostic | **Drop (accept)** | Accept the 100 fresh repeats and the retention fixture. |
| LIM-SHIP11-UNCLASSIFIED | Unclassified SHIP-11 edge has no semantic predicate | **Drop (accept explicitly)** | Accept the edge. Reopen only if a predicate emerges. |
| LIM-NO-HOST-WRONG-ROM | Wrong-ROM Libbet negative control runs only locally | **Later** | Accept, or run one `libbet-repro` workflow_dispatch (about 20 min) whenever that workflow is next touched. |
| LIM-WINDOWS-POSIX-CONTROLS | 3 controls are POSIX-only | **Later (accept)** | Accept. Rework only if Windows becomes a release target for those paths. |
| LIM-PROHIBITION-FLAGS | 2 descriptor-less prohibitions remain reviewer flags | **Drop (accept as flags)** | Keep them as reviewer flags. They are policy, not behaviour. |

Three of these (AUDIO-RED, M7, SHIP11) were due at the v0.2 audit and were still not decided. Deferral without a decision is itself a source of overhead: each audit re-presents the same 12 rows.

### 2.2 Other carry-over

| Item | Evidence | Rec |
|---|---|---|
| Phase 8 contract verifiers not wired | `tests/scripts/verify-phase8-closure-contract.py` (201 lines) and `verify-phase8-player-contract.py` (215 lines). No CTest or CI caller. Both pass by hand today (`files=65 rejected_controls=157`; player self-test `controls=5`). Both read through `git show` at boundary `96d5eec`, so they survive phase archival. CI uses `fetch-depth: 0`. | **v0.3, trivial.** Add 4 `add_test` entries (check plus `--self-test` for each) and the matching `tests/expected-tests.txt` lines. |
| Test helpers in `.planning/phases` | See 2.3 | **v0.3 first phase.** Prerequisite for `/gsd-cleanup` of v0.2 phase dirs. |
| Release-please PR #75 (0.2.1) | Auto-maintained by release-please. Lists the #74, #94 and #97 fixes. A release is currently blocked by LEDGER-PIN, PERF-REVIEW and REHEARSAL-FAILED. | **v0.3 first phase decides.** Leave it open. Merge only after the three release LIMs are closed, or let v0.3.0 supersede it. Do not merge it as is. |
| Open PRs #78–92 (15) | Stacked on the pre-15.1 base, CI-red (4 failures each). Every file they touch already exists on main through #93 and later PRs; the v0.2 audits were moved to `milestones/` and quick task 261020-hr8 sits in `milestones/v0.2-quick/`. | **Drop.** Close all 15 as superseded, with a one-line comment naming #93. |
| Perf regression vs v0.1.0 | See 2.4 | **v0.3** |
| SUMMARY key drift (15.1-31..33 use `requirements:`) | audit tech_debt | **v0.3, trivial.** Fix the key, and extend `summary_coverage` to reject a missing `requirements-completed`. |
| 7 validation rows that read live state (15.1 rows 34-1, 34-2, 35-2, 35-3, 36-1, 36-2, 36-3) | audit tech_debt | **v0.3.** Rewrite them to read the boundary commit, or delete them while moving the helpers. |
| GR2-IN-01 (fuzz self-test prints literal totals) | 15.1-GAP2-REVIEW-DISPOSITION | **Later.** Fix on next edit of `verify-v02-fuzz.py`. |
| GR-IN-03 | Deferred to P15-09 | **Later** |
| 13-VERIFICATION cell padding | Cosmetic; the parser now tolerates it | **Drop** |
| Scanner false positive on `14-UAT-REVIEW.md` | STATE deferred items | **Later.** Upstream tooling. |

### 2.3 Test helpers living in `.planning/phases` (GB-GSD-026)

Registered directly in `tests/CMakeLists.txt`:
- **Line 1208:** `GBB_HDMA_CLOSURE_CHECKER` = `.planning/phases/GB-13-cgb-hdma/verify-hdma-closure.py` (981 lines). It is used by CTest `cgb_hdma_lane_contract` and `cgb_hdma_lane_contract_selftest`.
- **Line 2670:** `gbb_add_summary_coverage_test` passes `--phases-dir .planning/phases`. It is used by CTest `summary_coverage` and `summary_coverage_selftest`. This one reads live planning by design.
- **Line 2687:** `GBB_UAT_CLOSURE_PHASE` = `.planning/phases/GB-15-cgb-acceptance-support-ledger-and-v0-2-0-release`. It is used by `uat_closure_controls`, `uat_closure_optimize_refused` and the related `gbb_add_uat_closure_test` cases.

Scripts in `tests/scripts/` that open phase-dir paths:

| Script | Path it opens | Survives archive? |
|---|---|---|
| `test_hdma_remote_evidence.py` | GB-13 `verify-hdma-closure.py` | No |
| `phase13-handoff-continuity.test.cjs` | GB-13 checker and `continue.md` | No |
| `test-cgb-red-evidence-privacy.py` | GB-14 dir (via the `run-cgb-red-evidence-privacy-test.py` wrapper at CMake line 1354) | No |
| `verify-closeout-scan.py` | GB-14 `14-UAT-REVIEW.md` | No (working-tree read) |
| `verify-closeout-dispositions.py` | GB-15.1 dir, plus GB-15 `15-delivery-receipt.json` | Partly. It reads via `git show commit:path`; CTest line 1462. |
| `verify-historical-limitations.py` | GB-15.1 dir and GB-12 `12-REVIEW-FOLLOWUP.md` glob | No. CTest line 1453. |
| `verify-phase8-closure-contract.py` | GB-08 | **Yes.** It reads via `git show` at the boundary commit. |
| `verify-summary-coverage.py` | `.planning/phases` by default | No |

Executables still inside phase directories (2,220 lines in total; only the GB-13 closure checker is test-consumed):
- `GB-13/verify-hdma-closure.py` (981 lines)
- `GB-12/verify-closeout-contract.py` (373)
- `GB-14/verify-uat-contract.py` (258)
- `GB-13/verify-hdma-source-revision.py` (144)
- `GB-13/verify-uat-contract.py` (126)
- `GB-13/verify-discussion-contract.py` (116)
- `GB-12/verify-uat-contract.py` (111)
- `GB-15.1/verify-scope.py` (70)
- `GB-08/differential/run-differential.sh` (41)
- Also at the planning root: `.planning/verify-v02-milestone-audit.py` (244)

Recommendation:
1. Move `verify-hdma-closure.py` into `tests/scripts/`.
2. Copy the GB-15 UAT-closure inputs into an immutable `tests/data/uat-closure-fixture/`. This is the same pattern as `tests/data/invalid-summary-coverage.md`.
3. Convert the remaining working-tree readers to `git show <boundary>:<path>`, the way the phase-8 verifier already does.
4. Add a CTest lint that fails if `tests/` or `.github/` mentions `.planning/phases/` outside `git show` reads, with a negative control.
5. Then run `/gsd-cleanup`.

### 2.4 Performance regression vs v0.1.0

The measurements:
- v0.2.0 receipt (`ab301aa` vs `e30d168`, Linux x86_64, tracer workload, 30 pairs): **+14.86% mean ±1.62%**, recorded as `accepted-with-disclosed-regression`. MILESTONES.md cites a **23.96% median** for the same release.
- After 15.1 (79e20f3): **median ratio 130.42 (+30.4%)**.

The trend may be getting worse, or this may be runner variance. Nobody knows, because each phase only compared against its predecessor:
- Phase 10 fired the review trigger (105.6–107.3% vs the Phase 7 baseline). Its attribution run against Phase 9 was "within noise", so the cost was never pinned down.
- Phase 11 measured 98.5–100.2% against Phase 10.
- The roughly 3% per-phase noise floor hides a creeping cost that adds up across phases.

**Recommendation for v0.3:**
1. One plan: bisect the phase merge commits `5673bed, 30230b2, d7e2e0a, 3012e8f, 70c441b, 8091fb5, 261c660, c771b1b, 79e20f3` with the existing `measure-release-baseline.sh` on one quiet host. Report median, min-of-n and margin.
2. Fix it, or accept it with attribution. That closes LIM-PERF-REVIEW.
3. Add a **cumulative** budget against the last release (not per phase). Use the existing D-22 trigger style: fire at median >105% with lower bound >100%, against `v0.2.0` or `v0.1.0`.

---

## 3. Test-suite health

Facts:
- **Size:** 1,183 cases, 1,188 inventory lines.
  - 608 (51%) are `cgb_*`, most of them generated per-case corpus and disposition tests.
  - About 670 are native C tests, and they run in **78 s** of total CPU.
  - About 513 are script-driven (Python directly or through `cmake -P expect_exit.cmake`). They take **455 s, 85% of runtime**.
  - About 335 (28%) are negative controls or self-tests.
- **Local:** the full suite is 536 s serial and 121 s at `-j4` (GB-CI-010).
  - The top 10 tests take 54% of serial time and the top 30 take 80%. Only 4 tests exceed 30 s.
  - Those 4 are `acceptance_stall_diagnosis` 63 s, `v02_consumer_controls` 49 s, `v02_fuzz_controls` 39 s and `acceptance_dense_input_controls` 34 s.
  - 1,129 tests run under 1 s.
- **Hosted:** at 5356d38 the jobs took:
  - `linux-asan-ubsan-acceptance` 26.3 min (limit 45)
  - `native-windows-x64` 22.9 min (limit 30, **76% of budget**)
  - `native-macos-arm64` 18.9 min (limit 30)
  - `linux-asan-ubsan-tests` 17.9 min
  - `cmake-floor-3.25.3` 16.8 min (limit 40)
  - `native-linux-x64` 15.1 min (limit 30)
  - Under ASan, `acceptance_stall_diagnosis` alone is 1,164–1,838 s and `v02_consumer_controls` is 770–1,184 s (GB-CI-010).
  - The `preview` and release fuzz waiters impose a whole-run ceiling of 2,700 s.
- **Growth:** 6.4x tests and 12.9x CMake lines in one milestone. `tests/CMakeLists.txt` is one 4,687-line file, and the exact-inventory file serialises parallel plans (GB-CART-003).

Verdict: **the C test suite is healthy and fast.** The weight sits in about 10 long acceptance/consumer/fuzz controls and in the Python/CMake-script layer. The real risk is hosted headroom: Windows is at 76% of its timeout, and ASan acceptance depends on one 20–30 minute test. Another milestone growing at v0.2's rate would break the 2,700 s waiter budget.

Hygiene recommendations:
1. **Per-test budget, enforced.** Normal ≤60 s and sanitizer ≤300 s. A CTest-output parser (already present, GB-CI-007) should fail the run on any breach unless the test is on a named allowlist. Today's 4 long tests start on the allowlist with a trigger to shrink them.
2. **Split `acceptance_stall_diagnosis` and `v02_consumer_controls`.** These are the ASan critical path. Shard the replays into independently named tests, or run the full-length dense replay only in a scheduled `nightly-asan` lane, while PRs keep a bounded replay that has a negative control. This also closes LIM-ASAN-STALL-TIMING.
3. **CTest labels** (`core`, `acceptance`, `corpus`, `planning`, `release-contract`) so local loops and lanes can select by label instead of by regex. Planning/closeout checkers such as `summary_coverage`, `uat_closure_*`, `closeout_*` and `historical_limitations` get `planning`.
4. **Split `tests/CMakeLists.txt`** by area into `include()`d files. Generate the per-area slice of `expected-tests.txt`, so parallel plans stop colliding on one inventory.
5. **Temp-dir hygiene.** `sanitizer_timeout_policy_selftest` leaves about 120 `build/sanitizer-timeout-policy-*` dirs. Tests should clean up after themselves, or write under `${CMAKE_CURRENT_BINARY_DIR}/tmp`, which is cleared at configure time.
6. **Retire phase-scoped verifiers after the milestone.** `cgb_hdma_lane_contract`, the `phase13-handoff-continuity` checks and similar tests assert historical phase prose, not behaviour. After the move (§2.3), keep only the ones that guard a live invariant. Make the rest immutable, boundary-commit replays, or delete them.

---

## 4. Process changes for v0.3 (each tied to evidence)

| # | Change | Evidence | Rigor kept by |
|---|---|---|---|
| P1 | **Phase size cap: ≤12 plans, at most 2 of them closeout/plumbing.** If gap closure exceeds 6 plans, stop and re-scope instead of adding a wave. | v0.2 median 15 plans per phase. Phase 10 had 20, Phase 15.1 had 36 (17 of them gap). Plans per requirement rose from 1.8 to 6.1. | Same must-haves. Fewer, larger plans. |
| P2 | **Verifier convention, from the first commit.** Every checker lives in `tests/scripts/`, takes `--boundary <sha>`, reads its subject and describing inputs with `git show <sha>:path`, ships a `--self-test` with a negative control, and is registered in CTest in the same plan that creates it. A lint CTest rejects `.planning/phases` paths in `tests/` and `.github/`, and rejects `assert` used as a check (GB-VERIFY-001). | Two 15.1 gap rounds came from live-HEAD reads (GB-GSD-024, GB-VERIFY-002, GB-EVID-002). The Phase 8 verifiers were never wired. Archival would have broken main (GB-GSD-026). | It prevents the defect class instead of retrofitting it. |
| P3 | **Freshness strategy chosen at milestone start: no per-phase refresh PRs.** Each phase's VERIFICATION is bound to its merge commit and treated as point-in-time evidence. At close, run **one** cross-phase re-verification at the final head (acceptance slice, baseline, full CTest, exact-head CI). Record that as the closeout basis, ideally teaching the runtime freshness gate to accept "verified at merge commit X, plus milestone re-verification at Y". | Refresh stack #78–92: 15 PRs, about 6.2k lines, all red and abandoned. Close was still override_closeout. GB-GSD-008 has now repeated in two milestones. | The same final-head evidence the v0.2 audit actually relied on. |
| P4 | **Decide limitations when they are found.** Each phase ends with a batched owner-decision list (accept, fix in phase, or defer with a *named phase*). Nothing reaches an audit undecided. | 12 LIM rows, all `owner_accepted:false`. 3 were due at the audit and were still undecided. Each re-audit re-presented them. | `limitation_open` stays explicit. It just gets a decision. |
| P5 | **CI budget.** (a) Each required job stays ≤60% of its timeout at p50. A breach on two heads triggers a duration comparison, not a re-run (GB-CI-004/010). (b) The whole run stays ≤30 min to keep margin under the 2,700 s waiters. (c) A planning-only lane: a `changes` job proves positively that the diff touches only `.planning/**`, `*.md` outside `docs/support`, or `AGENTS.md`. `required-native` then accepts the result of `ctest -L planning` in place of the heavy jobs. It is an explicit pass, never a skipped check. (d) Heavy ASan acceptance replays move to a scheduled lane, with a bounded PR variant. | Run time went from 1.5 to 25 min, 30% of runs were red, PR #98 took 7 attempts, and 4 main runs were cancelled. About 20 planning-only PRs ran about 120 job-min each. | Required checks still report on every head. AGENTS.md's "skipped is not proof" holds because the planning lane really runs something. |
| P6 | **Evidence volume diet.** Raw logs, JUnit XML and receipts go to CI artifacts or `build/`, never into git. Each phase directory holds PLAN, SUMMARY, one VERIFICATION and a machine-readable receipt. Prose restates a claim once and links to it. Continuation and route text is generated from STATE by one tool and checked by one CTest, instead of six hand-edited surfaces. | 93.5k `.planning` lines against 8k product lines. Phase 15.1 has 131 files. Phase 13 has 42 handoff/route commits. GB-GSD-023 ("close UAT across every live handoff surface"). | Machine receipts stay. Duplicate prose goes. |
| P7 | **Release and hardening as one phase.** Put the release-workflow security work and the exact-tag rehearsal *before* tagging, and size it explicitly, rather than tagging and then inserting a hardening phase. | Phase 15 shipped v0.2.0 in about 1 day. 15.1 then spent about 2.6 days hardening the same release path, and now blocks v0.2.1. | The rehearsal found 3 pre-tag defects, so do more of it before the tag. |
| P8 | **Cumulative performance budget** against the last release tag, measured at every phase that touches the core hot path. | Phase 10's attribution was "within noise", yet the total reached +15–30%. | Same paired-sample method (D-22). |
| P9 | **Record cost telemetry.** Model per agent role, session count, and wall time per plan, written into SUMMARY frontmatter. | The retrospective says "not recorded" for both milestones. Plan durations exist for only about 115 of 170 plans and some lack units. | — |
| P10 | **Schema checks at write time.** Extend `summary_coverage` to require `requirements-completed` and reject `requirements:`. Fold it into the existing write-time check so normalisation plans never recur. | 6 15.1 plans only normalised coverage schema. 15.1-31..33 still drifted. | Already a CTest. Widen it. |

### Suggested v0.3 opening phase (debt, sized to the P1 cap)

"v0.3 Phase 16: release readiness and repository hygiene", about 8 plans:
1. Owner LIM decisions, batch accept: RESIDUAL-WRITE-JOBS, HIST-AUDIO-RED, HIST-M7, SHIP11, PROHIBITION-FLAGS, WINDOWS-POSIX, NO-HOST-WRONG-ROM.
2. Close PRs #78–92.
3. Move the helpers and add the lint (§2.3).
4. Wire the Phase 8 verifiers, fix the SUMMARY key, and fix or delete the 7 live-state validation rows.
5. Perf attribution bisect and decision.
6. New post-0.2.0 support ledger.
7. Rehearsal rerun, then a decision on #75: ship v0.2.1, or fold into v0.3.0.
8. CI budget changes: planning lane, per-test budget, ASan nightly split.

Then STATE-01 and INT-01 feature phases, each capped at 12 plans.
