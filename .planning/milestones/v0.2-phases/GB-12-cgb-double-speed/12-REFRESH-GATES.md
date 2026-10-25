# Phase 12 — Verification Refresh Gates

**Refreshed:** 2026-10-20T22:53:30Z
**Refresh target:** `3930668cb49dba7289dff34696d8de2ee96492ed`
**Result:** No new proven defect in the bounded Phase 12 review, security, validation, or UI scope.

This supplement refreshes applicability evidence for the completed Phase 12 implementation. It does not replay Phase 12 or replace its historical review, security, Nyquist, or UI reports.

## Scope and boundary

The installed runtime identified as `@opengsd/gsd-core` 1.18.0. `check evaluation-scope --phase 12 --raw` returned `status: degraded`, `source: phase-range`, and `reason: no-reachable-task-commits`, with range base `70c441bebbee6294fb2c019ad5b606005c47a8d7`. The resolver therefore does not establish an exact Phase 12 task-commit file set. This refresh is manually bounded to the three recorded code-review findings and the current CGB speed core, timeout policy, inventory and fixture-reproduction paths. The current core also contains Phase 13 HDMA integration; only its interaction with the existing speed-switch pause was considered here.

Boundary-only closeout evidence is tied to immutable commit `da98d56ef8fadadf34ae951b337dcdecce495936`. The parent refreshed the canonical UAT to 73 automated rows with 19 negative controls and freshly ran the original closeout checker against an archive of that boundary, where its 17 mutation controls passed. Running the original checker against live HEAD is not boundary evidence: its exact historical fixture count and Phase 12 handoff fields are superseded by later Phase 14/15 state. That live-state rejection is not counted as a Phase 12 defect.

## Historical review findings

All three previously identified findings remain fixed in the current files. The original `12-REVIEW-DISPOSITION.md` correctly retains two rows; WR-02 was added by the independent follow-up and remains recorded there rather than being retroactively inserted into the historical ledger.

| Finding | Historical disposition | Current evidence |
|---|---|---|
| CR-01 [BLOCKER] — inherited `TMPDIR` could inject shell commands through the cleanup trap | Fixed in `be53c43` and `d979ba5` | `.github/scripts/verify-test-inventory.sh:30-32` uses a literal EXIT trap and a script-scope path. `.github/scripts/test-inventory-cleanup.sh:11-18,39-60` confines the unsafe mutant and marker beneath its own scratch directory. The fresh inventory self-test passed and detected the unsafe trap control. |
| WR-01 [WARNING] — late parent-directory timeouts missed sanitizer scaling | Fixed in `fe61e2f` | `tests/CMakeLists.txt:4503-4509` runs the shared scaler after test registration; `tests/check_sanitizer_timeout_policy.cmake:67-111` checks unchanged normal values, expected scaling, and early/double/parent-only controls. |
| WR-02 [WARNING] — the parent timeout pass did not reach child-directory player tests | Fixed in `40e7f08` | `tests/player/CMakeLists.txt:494-511` runs the shared scaler after player registration and checks the scaled speed, CLI, and model-auto limits. This retains CMake 3.25 directory-property scope. |

No new correctness or security finding was proven in the checked speed-switch and speed-stall paths. The present integration still has explicit coverage for a speed pause with active/pending HDMA (`tests/test_cgb_hdma_internal.c:1080-1084` and `tests/test_cgb_hdma_partition.c:47-50`); the parent-owned full regression is responsible for the broader current suite.

## Security and validation applicability

The 2026-10-14 security report records 34 closed threats at `d979ba5`. This refresh rechecked the two review-linked mitigations: T-12-15's parent and child timeout scaling, and T-12-33's hostile-`TMPDIR` cleanup boundary. It is a bounded applicability check, not a new audit of the other 32 threat rows or a claim of a fresh full security scan. The fixture script continues to validate recipe names and arguments before invoking RGBDS with argument arrays; hosted workflow pin checks retain a positive pin case and a digest-mismatch control.

The historical Nyquist report accounts for all 49 tasks and 73 coverage entries as automated checks with negative controls. The refreshed UAT has a separate canonical closure receipt against the current SUMMARYs; only historical closeout facts use the immutable boundary above. Fresh focused checks in this refresh passed:

- `bash -n` individually passed for both inventory scripts and both CGB speed reproduction scripts.
- `bash .github/scripts/verify-test-inventory.sh --self-test` passed, including hostile-`TMPDIR` cleanup, the original-trap mutant, platform-filter checks, and missing-test rejection.
- `bash tests/scripts/test-reproduce-cgb-speed.sh tool-failure` and `bash tests/scripts/test-reproduce-cgb-speed.sh missing-pin` passed. Each also accepted the embedded workflow's pinned RGBDS value and rejected a mutated archive digest; the tool-failure and missing-pin paths returned `result=error` rather than reporting a byte difference.

The local RGBDS is v1.0.4 while these fixtures require v1.0.1, so this refresh did not claim a local byte-identical rebuild. No CMake reconfigure/build, full CTest run, or ASan/UBSan run was performed here; the parent owns current full regression. Historical suite and hosted receipts remain tied to their recorded revisions and are not presented as fresh evidence for this refresh target.

## UI applicability

The Phase 12 UI review remains applicable: the phase adds no browser frontend or browser interaction surface. The player exposes the bounded statement “CGB double speed is implemented” (`src/player/main.c:404`) alongside the hardware and timing exclusions in `src/player/limitations.h:5`. A UI screenshot or native RGBA digest does not establish visual quality or physical CGB behavior; neither claim is made by the historical UI review.

## Parent regression and closure receipts

At unchanged source `3930668`, the parent configured/rebuilt and passed the full configured core suite **1,144/1,144** in **414.22 seconds**, and rebuilt/passed native SDL player **98/98** in **25.28 seconds**; zero skips. The frozen DMG baseline has zero changed rows. Canonical UAT closes 73 rows with 19 rejected controls. All 19 recorded plan windows reconcile; immutable `da98d56` closeout has 17 rejected controls. No new hosted, sanitizer runtime, benchmark, physical hardware or perceptual qualification is claimed.

Final handoff contract check reads current STATE/continuation notes, requires the Phase 12 verification-refresh stage and `/gsd-execute-phase 13` route, and verifies both automatic-advance flags false. It passes and rejects five stale-route/flag mutations. This current route check is separate from immutable historical closeout facts.

## Metadata-only follow-up, 2026-10-21

The earlier route above is historical. This follow-up starts at `45add7e43c185029f2ec31240b2e3402f00dbe41`; all 19 implementation plans remain complete. OpenGSD reports the only stale inputs as `.planning/context/LESSONS.md` and `.planning/research/INDEX.md`. Their changes add the later Phase 13 verification receipt and boundary-check limitation; neither changes the Phase 12 behavior, decisions, fixture rights or expected-failure dispositions. Comparing the prior Phase 12 producer `3930668` against this producer finds no changes under `src/`, `include/`, `cmake/`, `.github/`, or the root build files. Under `tests/`, only the unrelated Phase 8 historical closure checker changed.

Active `verify:post` hooks are Nyquist validation, security and UI review; `execute:post` enables code review. Reuse of completed audit evidence follows AGENTS.md's instruction to reuse recorded research and decisions unless a concrete gap appears. Nyquist remains validated with 49 automated tasks and 73 coverage entries; the current supported SUMMARY gate and its 12 weakening controls pass. Security remains ASVS L1, authored-at-plan-time, 34 closed threats and zero open threats; the workflow's clean-L1 short circuit applies. No new threat flags or implementation surface were added. UI applicability remains unchanged, with no new browser or native interaction surface. The three historical review findings retain their verified fixed dispositions. The generic evaluation-scope resolver still reports degraded phase-range/no-reachable-task-commits; it is not treated as an exact source scope.

Fresh bounded controls again pass inventory/platform/hostile-TMPDIR cleanup and its unsafe-trap mutant; fixture reproduction tool-failure and missing-pin paths each accept the pinned workflow and reject its digest mutation. DMG baseline reports zero changed rows. The original closeout checker executes against `git archive da98d56` and rejects all 17 weakened boundary records. All 19 original before/after task windows reconcile. The shared canonical UAT checker, rather than the old phase-local UAT checker, regenerates and checks 73 deliverables and rejects 19 controls. Full current core/player regression and receipt hashes are recorded in [12-METADATA-REFRESH-EVIDENCE.md](12-METADATA-REFRESH-EVIDENCE.md).

The current six-surface handoff separately requires the completed Phase 12 metadata verification refresh, `/gsd-complete-milestone v0.2`, 21 retained debt items, no next numbered implementation phase, 9/9 phases and 134/134 plans, and both auto flags false. It rejects ten mutations: one stale route per prose/machine surface, either auto flag, an excess phase count and an excess plan count. No historical route assertion uses live HEAD. No fresh full security/source/UI audit, pinned RGBDS rebuild, hosted sanitizer/Windows job, performance, hardware or perceptual qualification is claimed.
