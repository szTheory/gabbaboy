---
phase: 13-cgb-hdma
plan: "12"
subsystem: testing
tags: [cgb-hdma, ctest, provenance, handoff]
requires:
  - phase: 13-11
    provides: "Completed native, player, workflow and release evidence surfaces"
  - phase: 13-08
    provides: "CGB-E software fixtures and model applicability boundaries"
provides:
  - "Machine-checked Phase 13 prohibition proof and current-revision handoff"
  - "Five Python-only recurring lane and claim contracts in native CTest"
  - "Measured local, hosted and mutant lane-cost record"
affects: [phase-13-verification, phase-14-cgb-e-qualification]
actuals:
  tokens: 22919
  tasks: 2
  commits: 18
plan_head_before: 1983270701934d2bac7203757cfa3ac0c149d665
plan_head_after: 8e56893042b7fd769a1f30f353b46fb354b9dd3f
tech-stack:
  added: []
  patterns:
    - "Local Python CTest contracts remain independent of Node and the installed OpenGSD runtime"
    - "Windows nested shell checks use the configured Bash executable and MSYS paths"
key-files:
  created:
    - "tests/scripts/cgb-hdma-prohibition.test.cjs"
    - "tests/scripts/phase13-handoff-continuity.test.cjs"
    - ".planning/phases/GB-13-cgb-hdma/verify-hdma-closure.py"
    - ".planning/phases/GB-13-cgb-hdma/13-BENCH.md"
  modified:
    - ".gitattributes"
    - "tests/CMakeLists.txt"
    - "tests/expected-tests.txt"
    - "tests/scripts/reproduce-samesuite.sh"
    - ".planning/phases/GB-13-cgb-hdma/13-01-PLAN.md"
    - ".planning/STATE.md"
    - ".planning/PROJECT.md"
    - ".planning/phases/GB-13-cgb-hdma/continue.md"
key-decisions:
  - "Keep all five recurring Python contracts independent of Node and OpenGSD; run local prohibition closure separately."
  - "Resolve the Windows SameSuite launcher through CMake and convert drive paths for MSYS Bash without changing pinned bytes or expectations."
requirements-completed: []
coverage:
  - id: D1
    description: "Current source revision has machine-proven HDMA claim prohibition and fail-first/clean/live-checkout evidence."
    requirement: CGB-07
    verification:
      - kind: unit
        ref: "tests/scripts/cgb-hdma-prohibition.test.cjs#actual OpenGSD prohibition producer proof"
        status: pass
      - kind: other
        ref: "python3 -I .planning/phases/GB-13-cgb-hdma/verify-hdma-closure.py --prohibitions-self-test"
        status: pass
    human_judgment: false
  - id: D2
    description: "The exact native and player inventories, unchanged parallelism/timeouts, and installed consumers pass at the recorded source revision."
    verification:
      - kind: integration
        ref: "build/build/phase13-wave10-native-690c081.xml#993 tests, zero failures/errors/skips"
        status: pass
      - kind: integration
        ref: "build-player/build-player/phase13-wave10-player-690c081.xml#1086 tests, zero failures/errors/skips"
        status: pass
      - kind: integration
        ref: "build/phase13-wave10-installed-690c081.xml#six relocated consumer/package targets, zero failures/errors/skips"
        status: pass
    human_judgment: false
  - id: D3
    description: "Fixture provenance controls reject altered rights, source, tool and ROM claims while admitted fixtures reproduce byte-identically."
    verification:
      - kind: unit
        ref: "bash tests/scripts/reproduce-samesuite.sh --self-test"
        status: pass
      - kind: e2e
        ref: "GitHub Actions run 38662784222 at 690c081, 8/8 fixture and reproduction jobs passed"
        status: pass
    human_judgment: false
  - id: D4
    description: "Phase 13 handoff names automated verification as the next stage and keeps Phase 14 unstarted."
    verification:
      - kind: unit
        ref: "tests/scripts/phase13-handoff-continuity.test.cjs#handoff stage and exact route"
        status: pass
      - kind: other
        ref: "python3 -I .planning/phases/GB-13-cgb-hdma/verify-hdma-closure.py --handoff"
        status: pass
    human_judgment: false
  - id: D5
    description: "Required source-revision CI and package preview workflows complete successfully at the tested source revision."
    verification:
      - kind: e2e
        ref: "GitHub Actions PR-event run 38662784214 at 690c081, all eight jobs success"
        status: pass
      - kind: e2e
        ref: "GitHub Actions preview-package-smoke run 38662784151 at 690c081, all four jobs success"
        status: pass
    human_judgment: false
duration: "not captured; earliest persisted task boundary was the Task 1 RED commit"
completed: 2026-10-14
status: complete
---

# Phase 13 Plan 12: Current-revision lane closure and Phase 14 pause Summary

**HDMA claim-language prohibition, exact-revision lane evidence, Windows fixture closure, and automated Phase 13 handoff are recorded without starting Phase 14.**

## Performance

- **Duration:** Exact executor start was not retained; elapsed duration is not stated as a precise measurement.
- **Started:** Not captured. The first persisted Task 1 RED commit is `e8308d2`.
- **Completed:** 2026-10-14.
- **Tasks:** 2.
- **Files modified:** 12 tracked paths from the pinned plan base.
- **Plan commits:** 18, measured with `git rev-list --count 1983270701934d2bac7203757cfa3ac0c149d665..8e56893042b7fd769a1f30f353b46fb354b9dd3f`.
- **Current tested source:** `690c081e3714aa1039263255d572b6d0d06dad8e`.
- **Local final metadata head:** `8e56893042b7fd769a1f30f353b46fb354b9dd3f`; this documentation head is not published and has no exact-head CI claim.

## Accomplishments

- Added the installed OpenGSD prohibition producer path with regenerated bad/clean subjects, semantic fail-first, clean-subject, live-checkout checks and parser-projection round-trip validation. The producer result is green, unflagged, located, and includes non-empty `failFirstProof: violation-fixture` evidence.
- Registered five recurring Python-only CTest targets: three claim surfaces and two structural lane contracts. Native and player lane policy remains parallel 4 with existing timeout values.
- Recorded one-sample native, player, installed-package, Linux ASan/UBSan and mutant build-cost observations with revision/build/workload/digest details; the BENCH states no warm-up and uncertainty not quantified (not zero), and labels these lane-cost observations rather than emulator-speed claims.
- Fixed Windows checkout and nested shell invocation issues without changing fixture digests or expectations. The e9bc Windows run exposed `WinError 193` in the recursive `.sh` launch; CMake now passes the configured Bash executable, and Windows drive paths are normalized to MSYS form before invocation.
- Updated the current Phase 13 stage, route and evidence navigation. `--handoff` passes with `/gsd-verify-work 13`, Phase 14 unstarted, and both GSD auto flags false.

## TDD evidence

- Task 1 RED `e8308d2` contains the executable Node contract and failed its semantic CGB-C/physical-CGB-E diagnostic assertion in an isolated committed snapshot; its fail-first record passed `tdd-red-evidence`. GREEN is `16c9d53`, with `41bb9bf` strengthening the missing-requirement negative control.
- Task 2 RED `a2153b0` contains the executable continuity contract and reproduces the premature Phase 14 route failure; `0d5bb9c` corrects the predicate and `d08313d` records the matching verification-pending handoff.
- The malformed-subject setup control `adapter-malformed-red-committed.json` is `INVALID_RED`, not semantic fail-first evidence. `4eab951` adds preflight before registering the semantic target, and producer controls prove malformed setup exits nonzero without running or passing that target.
- The Windows LF contract RED `f67812a` reproduced in an isolated committed snapshot as CTest 439 `samesuite_repro_selfcheck`, with named diagnostic `raw-hashed license notice lacks LF checkout policy`; GSD classified the captured result as `RED_EVIDENCE_OK`. `e9bc47e` adds explicit LF attributes for digest-pinned text closures and leaves expected digests unchanged. A CRLF checkout simulation passed for 13 representative files. Later exact-source Windows evidence found the separate launcher defect; commits `7413a64` and `690c081` fixed it, and the exact-source Windows lane passed.
- The runtime `tdd-review-checkpoint` reports zero `type: tdd` plans because this plan retains `type: execute` frontmatter. That checkpoint is non-applicable and is not TDD certification; task-level RED/GREEN evidence above is the audit.

## Plan commits

1. `e8308d2` — executable failing HDMA prohibition contract.
2. `16c9d53` — actual OpenGSD fail-first/clean/live-checkout proof and lane inventory.
3. `41bb9bf` — missing-requirement mutation control.
4. `a2153b0` — failing phase handoff continuity contract.
5. `0d5bb9c` — scoped premature Phase 14 detection.
6. `0bff701` — local lane and mutant-cost record.
7. `d08313d` — Phase 13 execution handoff.
8. `0fef599` — malformed claim-subject setup control.
9. `4eab951` — preflight malformed subjects before semantic target.
10. `f67812a` — failing Windows text-closure checkout-normalization contract.
11. `e9bc47e` — explicit LF attributes for digest-pinned text closures.
12. `e40649c` — benchmark source binding.
13. `baaff1f` — STATE/PROJECT/continuation handoff refresh.
14. `7413a64` — explicit Bash launcher for recursive SameSuite checks.
15. `690c081` — configured Bash and Windows/MSYS path handling.
16. `e56ead2` — bind local lane-cost record to tested source `690c081`.
17. `09bf48e` — record completed exact-source hosted CI and preview evidence in BENCH.
18. `8e56893` — refresh Phase 13 project/state/continuation handoff from exact-source evidence.

## Measured evidence and hosted status

- Native Debug on Darwin arm64, Apple clang 21.0.0, CMake 4.4.3, Ninja: 993/993 passed at source `690c081`, CTest wall 85.16 s, JUnit SHA-256 `616e607d867b3184078cf7929f0806abf38fbcd6d197e22014bcf11b58baf1e1`.
- SDL3 player Debug (SDL 3.4.18): 1,086/1,086 passed at source `690c081`, CTest wall 100.35 s, JUnit SHA-256 `27e32fd1dfc4e663810ea0fedecbc4f6fbef80e994b01f47531c5d80024f1976`.
- Relocated installed consumers/package: six exact targets passed at source `690c081`, CTest wall 1.78 s, JUnit SHA-256 `e6444ccf70ce75a894218ba762099750ca8781a869e311bd930efefe9c406082`.
- CTest inventory increased from Phase 12's 898 names to 993 at this source: 95 added, none removed. The 29 `cgb_hdma_mutant_*` tests total 0.39712 s in the native report; the representative no-copy mutant/control pair totals 0.021629 s, rounded to 0.022 s in BENCH. Costs are single observations without warm-up, and uncertainty is not quantified.
- The local Darwin sanitizer preset stops at the supported-platform guard. No local ASan run or local libFuzzer campaign is claimed.
- Historical run `38661411340` at source `e9bc47e` passed Linux ASan/UBSan 988/988, no skips, CTest wall 847.53 s; its Windows job failed with `WinError 193`. This is historical failure evidence, not current-source proof.
- Exact-source PR-event run `38662784214` at `690c081e3714aa1039263255d572b6d0d06dad8e` completed successfully across all eight jobs: Linux ASan/UBSan 988 executed, none skipped, CTest wall 676.28 s; CMake 3.25.3 inventories 988 base cases in 632.69 s and 993 relocated installed cases in 650.32 s; macOS 993/993 in 628.13 s; Windows 981/981 in 495.80 s; native Linux 993/993 in 475.61 s; player gate, macOS player package and aggregate `required-native` passed. No-host-clock checks passed on Linux/macOS. Windows `samesuite_repro_selfcheck` passed in 4.87 s.
- Linux ASan/UBSan also passed its bounded fuzz self-test and three deterministic fuzz regressions; the log states configured `fuzz_core` is unavailable. This is test-harness evidence only, not a host-fuzzer campaign.
- macOS player-package job `116187733769` passed 98 player-specific tests in 17.34 s and extracted SDL 3.4.18 package smoke; package SHA-256 `3cb71a0118f5d60c81efad862406360c8999785c2aa3bb72a3d6ac433bd4d18b`.
- Fixture/reproduction run `38662784222` at `690c081` passed all 8/8 jobs, including SameSuite and MagenTests rebuilds. Preview-package run `38662784151` completed successfully with all four jobs green: Linux/macOS installed-package smoke and external consumers passed (CTest targets 1.38 s and 2.47 s), the macOS player package smoke passed, and aggregate `preview-package-smoke` passed.
- Hosted results above are source-revision evidence for `690c081`. The final review/verification metadata head remains unpublished and requires separate exact-head checks during parent closeout.

## 13-02 bounded evidence span

The 13-02 summary's original task window remains four commits from `1062a6c8222cfa97071ee05db3e821bcb3cabe89` through `b257ac8d0400fbe325b2eb8859ad72e3a07855a3` (`git rev-list --count` = 4). Its later completion summary was committed as `fb1d968`; the independent visibility-fixture repair `a6b115bc41fb6ec0d890ee20f9a36d5bcf6e2740` followed the 13-06 admission work, amended the 13-02 summary, and added the corresponding LESSONS entry. The full span from the original `plan_head_before` to `a6b115b` is 11 commits because it crosses 13-06; that follow-up is retained as post-plan evidence and is not folded into the 13-02 task commit count.

## Decisions and limitations

- Physical CGB-E remains UNKNOWN/POLICY. Optional CGB-C material is rights-gated, informational, and outside the CGB-E denominator; software fixture evidence is 5/5.
- The D-06/Pan Docs contradiction remains explicit. Timing beyond the selected CGB-CPU-E software model, APU, mode-3 behavior, and commercial-game compatibility remain unqualified. No physical measurement or local libFuzzer campaign is claimed. No Mealybug bytes were fetched.
- CGB-07 remains open until goal verification. `requirements-completed` stays empty for this handoff.
- The owner's dirty `.planning/config.json`, `.planning/state.json`, and `.planning/milestone.lock` were preserved; `.planning/state.json` was not rewritten by a state helper. STATE.md and `continue.md` persist the exact verification route. The OpenGSD ROADMAP helper records 12/12 plans executed while leaving Phase 13 In Progress pending verification.

## Deviations from plan

### Auto-fixed issues

**1. [Rule 1 - Bug] Reject malformed subject setup before semantic fail-first registration**
- **Found during:** Task 1.
- **Issue:** A malformed producer JSON could otherwise be misclassified as semantic fail-first evidence.
- **Fix:** Preflight subject JSON before registering the descriptive Node test and retain an isolated malformed-setup non-semantic control.
- **Files modified:** `.planning/phases/GB-13-cgb-hdma/verify-hdma-closure.py`, `tests/scripts/cgb-hdma-prohibition.test.cjs`.
- **Verification:** Local `--prohibitions-self-test` controls pass; malformed setup exits nonzero without running the semantic target.
- **Committed in:** `4eab951`.

**2. [Rule 1 - Bug] Preserve digest-pinned text on Windows checkouts**
- **Found during:** Task 1 Windows PR-event lane.
- **Issue:** Git CRLF conversion changed the raw-hashed SameSuite license notice, causing self-check to report a digest mismatch.
- **Fix:** Added narrow LF attributes to all newly digest-pinned text closures and a checkout-normalization negative control; no digest changed.
- **Files modified:** `.gitattributes`, `tests/scripts/reproduce-samesuite.sh`.
- **Verification:** Isolated RED at CTest 439 reproduced the named failure; 13-file `core.autocrlf=true` checkout control passed after the fix; exact-source Windows CI passed after the separate launcher repair.
- **Committed in:** `f67812a`, `e9bc47e`.

**3. [Rule 1 - Bug] Invoke recursive SameSuite checks with configured Bash on Windows**
- **Found during:** Task 1 exact-source Windows PR-event run `38661411340`.
- **Issue:** Python attempted to execute `.sh` directly and raised `WinError 193`.
- **Fix:** Use CMake's discovered Bash executable and normalize Windows drive paths to MSYS form for nested script and temporary-path arguments.
- **Files modified:** `tests/CMakeLists.txt`, `tests/scripts/reproduce-samesuite.sh`.
- **Verification:** Exact-source run `38662784214` passed the Windows inventory 981/981 and `samesuite_repro_selfcheck` in 4.87 s.
- **Committed in:** `7413a64`, `690c081`.

**Total deviations:** 3 Rule 1 fixes. All were directly required to complete the current plan's fail-first, provenance, or Windows lane behavior.

## Issues encountered

The Windows failures were confirmed from exact job logs and fixed. The exact-source rerun passed. State-helper advancement was intentionally left to the parent-owned verification handoff; the markdown state route is current, while the owner's dirty state JSON was preserved.

## User setup required

None.

## Next phase readiness

Plan 13-12 execution is complete; Phase 13 automated goal verification and parent review remain. Run `/gsd-verify-work 13`. Keep Phase 14 unstarted; after Phase 13 verification/review and exact-head checks, its route is `/gsd-discuss-phase 14` for **CGB-E Model Qualification and Corpus**.

## Self-Check: PASSED

- The 12 tracked changed paths and all 18 plan commits exist from the pinned base through `8e56893`.
- The five coverage entries pass `verify-summary-coverage.py`; the OpenGSD coverage classifier reports all entries automated.
- Required deliverable paths exist, ROADMAP shows 12/12 plans with Phase 13 still In Progress, and physical qualification and CGB-07 remain open; the next route is `/gsd-verify-work 13`.

---
*Phase: 13-cgb-hdma*
*Completed: 2026-10-14*
