---
phase: 14-cgb-e-model-qualification-and-corpus
plan: "13"
subsystem: testing
tags:
  - CGB
  - CGB-CPU-E
  - corpus
  - claims
  - receipts
  - privacy
requires:
  - phase: "14-12"
    provides: Nonce-bound full-stream corpus receipt, exact test inventory, and public-artifact allowlist
  - phase: "14-10"
    provides: Stable AGE source-row identities, exact observations, and model-gate ownership ledger
  - phase: "14-03"
    provides: Guest-qualified CGB APU sample latch and transition evidence
provides:
  - Source-bound CGB profile, audio, corpus, and model-gate claims with current-receipt validation
  - Product and player limitation text scoped to the CGB-CPU-E software model and named evidence limits
  - Durable source, assertion, receipt, privacy, and task-history links with automated negative controls
affects:
  - Phase 14 aggregate verification
  - Native CI and corpus reporting
  - Future CGB support and compatibility claims
actuals:
  tokens: 25162
  tasks: 3
  commits: 6
commits: 6
plan_head_before: b1ff601e665a45816a9606f1af5c5035e5ee8668
plan_head_after: a29f8c92c84e072cb23775bdfecd88a8a839bc39
tech-stack:
  added: []
  patterns:
    - Separate static source/test binding checks from current-run receipt completeness
    - Validate claims against one nonce-bound receipt after the full CTest stream
    - Keep author expectations, guest observations, evaluator status, and emulator comparison distinct
key-files:
  created:
    - tests/scripts/verify-cgb-corpus-claims.py
    - tests/scripts/test-cgb-red-evidence-privacy.py
    - tests/scripts/run-cgb-red-evidence-privacy-test.py
    - docs/cgb-corpus.md
    - .planning/phases/GB-14-cgb-e-model-qualification-and-corpus/14-13-task3-red-evidence.json
  modified:
    - docs/cgb-profile.md
    - docs/audio-and-playback.md
    - docs/model-gates.md
    - README.md
    - docs/preview.md
    - docs/support/unreleased.md
    - src/player/limitations.h
    - .github/workflows/ci.yml
    - tests/CMakeLists.txt
    - tests/expected-tests.txt
    - tests/scripts/verify-cgb-corpus-inventory.py
    - tests/scripts/verify-age-phase14-contract.py
    - tests/scripts/test-cgb-corpus-report.py
    - .planning/research/INDEX.md
    - .planning/context/DECISIONS.md
    - .planning/context/LESSONS.md
    - .planning/phases/GB-14-cgb-e-model-qualification-and-corpus/14-03-SUMMARY.md
    - .planning/phases/GB-14-cgb-e-model-qualification-and-corpus/14-07-SUMMARY.md
    - .planning/phases/GB-14-cgb-e-model-qualification-and-corpus/14-09-SUMMARY.md
    - .planning/phases/GB-14-cgb-e-model-qualification-and-corpus/14-10-SUMMARY.md
    - .planning/phases/GB-14-cgb-e-model-qualification-and-corpus/14-11-SUMMARY.md
key-decisions:
  - Keep static `--bindings` separate from terminal observations; the fresh complete receipt owns runtime counts.
  - Derive changing counts from the current receipt and keep physical, analog/perceptual, peer-IR, and general-game claims outside scope.
  - Preserve valid historical RED evidence, redact only captured workspace prefixes, and do not reconstruct the missing 14-12 RED gate.
patterns-established:
  - The static claims test is cycle-safe; CI validates dynamic claims after receipt creation without rerunning corpus guests.
  - Public artifact privacy and RED traceback privacy each have a clean path plus a named path-leak negative control.
requirements-completed: []
coverage:
  - id: D1
    description: CGB profile, audio, corpus, and gate claims bind to source expectations, stable identities, exact mode cells, and a fresh complete receipt.
    human_judgment: false
    verification:
      - kind: unit
        ref: cgb_corpus_claims and cgb_corpus_claims_controls; 15 semantic controls cover wrong cells, xfail inflation, oracle swaps, missing gates, hardware claims, and omitted limits.
        status: pass
      - kind: integration
        ref: python3 -I tests/scripts/verify-cgb-corpus-claims.py --receipt build/cgb-corpus-receipt.json; 107/107 cases, 25 observed passes, 82 matched xfails, 2,845/4,959 assertion rows passed.
        status: pass
      - kind: unit
        ref: cgb_corpus_report_contract; native CI contract verifies the claims consumer runs after receipt construction.
        status: pass
  - id: D2
    description: README, preview, unreleased notes, and player limitation claims agree with the qualified software model and explicit exclusions.
    human_judgment: false
    verification:
      - kind: unit
        ref: player_claims_agree, player_claims_agree_mutated, player_limitations, cgb_speed_docs_no_stale_claims, cgb_hdma_claims_contract_native.
        status: pass
      - kind: unit
        ref: cgb_corpus_claims_controls rejects omitted compatibility policy, removed analog limits, and hardware overclaims.
        status: pass
  - id: D3
    description: Persisted RED records and public evidence artifacts contain no workstation paths while preserving the original test evidence.
    human_judgment: false
    verification:
      - kind: unit
        ref: cgb_corpus_red_evidence_privacy; checks five sanitized historical records and detects a synthetic absolute path.
        status: pass
      - kind: other
        ref: OpenGSD 1.16.0 check tdd-red-evidence classified all five historical records and the new Task 3 record RED_EVIDENCE_OK.
        status: pass
      - kind: integration
        ref: verify-cgb-corpus-artifacts.py --check --build-dir build; three allowlisted JSON files passed, raw Test.xml/JUnit stayed local.
        status: pass
  - id: D4
    description: The registered exact test inventory and durable research, decision, lesson, and plan-history links pass automated contracts.
    human_judgment: false
    verification:
      - kind: integration
        ref: Full nonce-bound CTest stream: 1,136/1,136 tests passed with none skipped; required-test set was checked before filtering.
        status: pass
      - kind: unit
        ref: summary_coverage and summary_coverage_selftest validate block-style coverage with no human checkpoints.
        status: pass
      - kind: other
        ref: All twelve earlier plan_head_before/after windows are ancestors of the phase branch; 14-03 head fields are top-level and dependency descriptions match their source summaries.
        status: pass
metrics:
  duration: 32min
  completed: 2026-10-16
status: complete
---

# Phase 14 Plan 13: CGB claims and evidence handoff Summary

**Source-bound CGB-CPU-E profile and audio claims now distinguish independent expectations from current receipt observations, with product limits, CI consumers, privacy checks, and durable evidence links aligned.**

## Performance

- **Duration:** 32 minutes.
- **Started:** 2026-10-16T00:34:13Z.
- **Completed:** 2026-10-16T01:05:59Z.
- **Tasks:** 3.
- **Files modified:** 32, including this summary.
- **Full CTest:** 1,136/1,136 passed in 307.91 seconds; the exact inventory reported no skipped tests.
- **Fresh receipt at code commit `42ff03c`:** 107/107 cases completed; 25 observed passes and 82 matched expected failures; 2,845/4,959 assertion rows passed. AGE image evidence retains 18,208 pixel mismatches across 138,240 pixels.
- **Static corpus bindings:** 181 sources, 109 outputs, and 107 case/test identities. The research14 disposition check reports 31 gates, 4 resolved, and 27 still unknown or limited.
- **Artifact privacy:** three allowlisted JSON files totaling 1,488,355 bytes passed; raw CTest XML and JUnit remained local.

## Accomplishments

- Added a standard-library claims validator that cross-checks the FF76/FF77 mode matrix, the live core, independent source expectations, SameSuite APU identities and guest assertions, author results versus evaluator status, the gate ledger, and receipt version/ancestry. Its negative controls reject a wrong mode cell, xfail-inflated totals, oracle swaps, hardware or analog overclaims, missing gate rows, and omitted limitations.
- Updated CGB, audio, gate, corpus, README, preview, unreleased, and player limitation claims. Counts are receipt-driven; the docs preserve the `$FF` compatibility read policy, the CGB-CPU-E software-model scope, guest-only digital audio evidence, and physical/analog/game exclusions.
- Registered claims and RED-privacy tests in CTest and `expected-tests.txt`. Native CI checks dynamic claims only after it builds the nonce-bound receipt, while static checks remain cycle-safe during the full stream.
- Sanitized five earlier RED traceback outputs by replacing only the workspace prefix. All original target names, assertions, expected and actual text, exit codes, and failure meanings remain intact; no absent output hash was added. A newly captured Task 3 RED proves the privacy assertion failed against those actual records before the sanitizer commit.
- Updated the research index, decision register, and lessons, and corrected inaccurate `requires` / `provides` labels in prior summaries. All twelve earlier plan-head windows remain ancestor-reachable; the 14-03 head fields are now top-level.
- Kept the independent 15/34 DMG fixture/baseline obligation and two unclassified edge-probe rows visible in the research evidence. No routine human UAT, hardware qualification, hosted run, or Phase 15 work is claimed.

## Task Commits

1. **Task 1: Tracer source-bound claims** — `df80965`.
2. **Task 2: Product limitation claims** — `b8ad34a`.
3. **Task 3: Durable evidence and exact verification inventory** — RED `6e40ab4`; privacy sanitization `b7a7f46`; tests, CI, memory, and metadata `cbfc640`.
4. **Task 3 Rule 1 correction:** receipt CTest-name ancestry and its omission control — `42ff03c`.

**Plan window:** `a332e67` through `42ff03c`, six commits measured with the persisted ledger. The summary metadata commit is outside that measured task window.

## Decisions Made

- Static source/rights/output/test binding is the job of `--bindings`; current terminal completeness and changing counts come from the single fresh receipt. The strict static `--complete` rejection for `magentests:bg_oam_priority` remains covered rather than weakened.
- CGB author expectations, observed guest results, evaluator status, matched xfails, and emulator differential evidence remain separate. No result here implies physical CGB-E behavior, analog or perceptual audio/color qualification, peer IR, or general game compatibility.
- Persisted RED traces use repository-relative test paths. Historical failures remain their original evidence; a missing prior RED is disclosed instead of reconstructed.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking consumer fix] Updated stale inventory and AGE claims consumers.**
- **Found during:** Task 1.
- **Issue:** Existing inventory and AGE contract checks still required old fixed xfail wording and a stale GATE-49 description after docs moved to current-receipt counts.
- **Fix:** Updated those direct consumers to require current complete-receipt/pass/xfail semantics and the live GATE-49 projection, while keeping static and live responsibilities separate.
- **Files modified:** `tests/scripts/verify-cgb-corpus-inventory.py`, `tests/scripts/verify-age-phase14-contract.py`.
- **Verification:** Inventory `--bindings` and `--self-test`; AGE `--research14` and `--research14-controls`; full CTest.
- **Committed in:** `df80965`.

**2. [Rule 1 - Bug] Made the RED privacy wrapper independent of CTest's working directory.**
- **Found during:** Task 3 CTest registration.
- **Issue:** CTest launches from `build/tests`, so a deliberately relative traceback filename was also resolved relative to the build tree when opening the five evidence files.
- **Fix:** The wrapper changes to the repository root before executing the unittest, while preserving the repository-relative traceback filename.
- **Files modified:** `tests/scripts/run-cgb-red-evidence-privacy-test.py`.
- **Verification:** The wrapper passed when launched from `build/tests`, and `cgb_corpus_red_evidence_privacy` passed in the focused and full suites.
- **Committed in:** `cbfc640`.

**3. [Rule 1 - Bug] Fixed receipt CTest-name composition.**
- **Found during:** Post-receipt validation after an initial 1,136/1,136 passing stream.
- **Issue:** Python cannot add `dict_values` directly to a list while assembling source-bound and aggregate CTest names.
- **Fix:** Added a list-safe ancestry helper plus a positive fixture and a negative control for an omitted aggregate test.
- **Files modified:** `tests/scripts/verify-cgb-corpus-claims.py`, `.planning/context/DECISIONS.md`.
- **Verification:** The 15-control claims self-test and focused report/claims tests passed; after the fix commit, the fresh 1,136/1,136 CTest stream built a 107/107 complete receipt and the post-receipt claims, inventory, and privacy checks passed.
- **Committed in:** `42ff03c`.

**4. [Contract adaptation] Use static bindings plus the receipt for completeness.**
- **Found during:** Task 3 final verification.
- **Issue:** The plan's `--complete` command would reject `magentests:bg_oam_priority`, which has no static terminal observation; CTest `--begin-run` also invalidates prior receipt state before the stream, so requiring a current complete receipt inside static CTest would cycle.
- **Fix:** Kept `--complete` strict and used `--bindings` for frozen static identity, followed by `--from-ctest` and the explicit claims `--receipt` validation for live completeness.
- **Files modified:** CI consumer and claim/inventory contracts.
- **Verification:** Inventory self-test preserves the exact static rejection; fresh receipt validates all 107 selected cases without rerunning the corpus.
- **Committed in:** `cbfc640`, `42ff03c`.

**Total deviations:** 4 documented consumer, working-directory, receipt-validation, and contract adaptations. The fixes preserve the planned scope and add no dependency, public API, UI redesign, or new fixture.

## TDD Gate Compliance

- **Task 3 RED:** `6e40ab4` records the real unittest run failing `test_records_have_only_repository-relative-paths` against the five workspace-path leaks while the synthetic-path detector passed. OpenGSD classified the record as `RED_EVIDENCE_OK` (`target_test_failed`) before sanitization.
- **GREEN:** `b7a7f46` sanitized the five existing records; both privacy tests then passed. OpenGSD still classifies all five historical REDs and the new Task 3 RED as valid target-test failures.
- **Historical 14-12 deviation:** The missing Task 3 RED remains disclosed in `14-12-SUMMARY.md`; this plan did not recreate or backdate it.

## Issues Encountered

The first full stream passed all tests but its post-receipt consumer exposed the CTest-name composition bug; the corrected implementation was then verified with a fresh stream at `42ff03c`. The configure step reported that the matching Clang libFuzzer runtime was unavailable, so this plan claims its deterministic CTest and corpus evidence only, not a local fuzzing-runtime or hosted result.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Plan 14-13 is complete. The parent workflow still owns Phase 14 aggregate verification, requirement traceability, review, and handoff; its exact current-head evidence must be refreshed after this documentation commit. Phase 15 remains unstarted, and no release or physical-hardware claim is made.

---
*Phase: 14-cgb-e-model-qualification-and-corpus*
*Completed: 2026-10-16*

## Self-Check: PASSED

- All newly created files listed in this summary exist.
- All six task commits and all twelve earlier plan-head windows are ancestors of the current code head.
- Strict `summary_coverage` and `summary_coverage_selftest` pass for this block-style summary.

## Sanitized ancestry

The top-level commit windows use sanitized unpublished ancestry. Historical execution revision IDs and task IDs above remain as originally recorded; [14-HISTORY-REDACTION.md](14-HISTORY-REDACTION.md) maps them to the equivalent sanitized commits. Fresh final qualification is recorded separately after this rewrite.
