---
phase: GB-17-native-save-state-core
plan: "07"
subsystem: testing
tags: [performance, release-evidence, CTest, GitHub-Actions]

requires:
  - phase: GB-17-native-save-state-core/17-06
    provides: "Existing release performance receipts, evidence consumers, and workflow policy checks"
provides:
  - "Triggered paired wall-clock receipts pass through production as advisory observations"
  - "Immutable-base deterministic Ir ratio and realtime limits remain independent blocking gates"
  - "Rehearsal, aggregate, attachment, and release evidence consumers preserve advisory timing semantics"
affects: [GB-17, release-evidence, performance-gates]

actuals:
  tokens: 24213
  tasks: 3
  commits: 8

tech-stack:
  added: []
  patterns:
    - "Advisory paired wall-clock evidence is separate from deterministic and realtime release gates"
    - "Performance policy evaluation reads its baseline from an immutable commit"

key-files:
  created: []
  modified:
    - tests/scripts/measure-release-baseline.sh
    - tests/scripts/verify-v02-performance.py
    - tests/cmake/perf.cmake
    - tests/expected-tests.txt
    - tests/scripts/verify-perf-gate.py
    - tests/scripts/run-perf-gate.sh
    - tests/baseline/perf-gate-v1.txt
    - .github/workflows/release.yml
    - .github/workflows/release-rehearsal.yml
    - tests/scripts/verify-v02-delivery.py
    - .github/scripts/verify-workflow-policy.py

key-decisions:
  - "Valid paired wall-clock measurements are successful advisory receipts; ordinary timing approval is removed from rehearsal and release routing."
  - "Ir ratio 1.10 and realtime floor 4.02 remain blocking; their baseline values were not changed."
  - "A deterministic limit exception remains bound to immutable source, workload, build, repeated output and correctness evidence; OWNER authorization remains for Plan 17-11."

patterns-established:
  - "Receipt self-tests start with the production measurement producer and pass the result through production verifier or consumer functions."
  - "Workflow mutations test intended advisory-path failures while preserving native state-pin, receipt, permission, and consumer controls."

requirements-completed: [RM-026, RM-029]

coverage:
  - id: RM-026
    description: "A valid triggered paired timing receipt succeeds as advisory through the producer, verifier, reuse, and release evidence consumer while source and workload binding remain enforced."
    requirement: RM-026
    verification:
      - kind: integration
        ref: "411889324953d20bb3c88c516d3826bc6dfe98bd: ctest --test-dir build/phase17-07 -R '^perf_' --output-on-failure --no-tests=error (11/11 passed)"
        status: pass
      - kind: integration
        ref: "411889324953d20bb3c88c516d3826bc6dfe98bd: python3 -I tests/scripts/verify-v02-delivery.py --self-test (7 positives, 48 rejected controls, 2 real-owner rejections)"
        status: pass
    human_judgment: false
  - id: RM-029
    description: "Deterministic Ir ratios and native realtime remain blocking, both repeats bind output digest and consumption, and a limit change cannot be approved from live policy or ordinary timing evidence."
    requirement: RM-029
    verification:
      - kind: integration
        ref: "7be6885: python3 -I tests/scripts/verify-perf-gate.py --self-test-limit-ratchet (6/6 passed, 5 controls)"
        status: pass
      - kind: integration
        ref: "7be6885: python3 -I tests/scripts/verify-perf-gate.py --self-test-repeat-controls (4/4 passed, 3 controls)"
        status: pass
      - kind: integration
        ref: "411889324953d20bb3c88c516d3826bc6dfe98bd: ctest --test-dir build/phase17-07 -R '^perf_' --output-on-failure --no-tests=error (11/11 passed)"
        status: pass
    human_judgment: false
  - id: release-advisory-policy
    description: "Release workflows consume advisory timing while retaining independent deterministic gates and the existing source-specific evidence checks."
    verification:
      - kind: integration
        ref: "411889324953d20bb3c88c516d3826bc6dfe98bd: python3 -I .github/scripts/verify-workflow-policy.py --check (residual_write_jobs=5)"
        status: pass
      - kind: integration
        ref: "411889324953d20bb3c88c516d3826bc6dfe98bd: python3 -I .github/scripts/verify-workflow-policy.py --self-test (266 negative controls, 4 positive controls)"
        status: pass
      - kind: integration
        ref: "411889324953d20bb3c88c516d3826bc6dfe98bd: bash .github/scripts/verify-release-gates.sh --self-test (exit 0)"
        status: pass
    human_judgment: false

duration: 26min
completed: 2026-10-26
status: complete
plan_head_before: b8946493d405378210d9d4923f1dd67b191056d0
plan_head_after: 411889324953d20bb3c88c516d3826bc6dfe98bd
---

# Phase GB-17 Plan 07: Advisory Timing and Deterministic Performance Ratchet Summary

**Paired wall-clock timing now passes end to end as advisory evidence, while immutable-baseline Ir and realtime limits remain blocking.**

## Performance

- **Duration:** 26 minutes from first task commit to Task 3 commit; preparation and context reads predated the first commit.
- **Tracked implementation window:** 2026-10-26 23:18–23:44 EDT.
- **Tasks:** 3/3.
- **Plan files modified:** 11.
- **Commit ledger:** 8 commits from the persisted plan base to the task head. This shared-branch count includes concurrent Plan 17-05 commits; four Plan 17-07 task commits are listed below.
- **Actual token estimate:** 24,213, measured as changed-file diff characters divided by four.

## Accomplishments

- The paired timing producer emits a successful schema 3 advisory receipt when triggered measurements are valid. Verification and reuse preserve legacy receipt meanings and reject malformed measurements, changed digests, or unbound identities.
- The deterministic performance ratchet evaluates only the baseline committed at `947d6a9d177af6c04a5f9ea6abcc2c470ab9be57`. Both repeats bind workload, output digest, and consumed half-dots. The existing Ir ratio limit `110/100` and realtime floor `4.02` remain unchanged and blocking.
- Rehearsal and release workflows no longer route ordinary wall-clock timing through an approval decision. The actual delivery evidence consumer accepts the producer-generated advisory receipt while rejecting malformed disposition and source-tree mismatches. Native state-pin, receipt, workflow permission, and consumer mutation controls remain present.

## Task Commits

1. **Task 1: Produce and verify a real advisory timing receipt** — `5c5d38c` (`feat`).
2. **Task 2 RED: Add immutable performance ratchet controls** — `0ed670d` (`test`).
3. **Task 2: Retain blocking Ir/realtime and ratchet deterministic limits** — `7be6885` (`feat`).
4. **Task 3: Carry advisory evidence through aggregate, attachment, and release consumers** — `4118893` (`feat`).

## Files Modified

- `tests/scripts/measure-release-baseline.sh` and `tests/scripts/verify-v02-performance.py` — produce, validate, and reuse advisory paired timing receipts.
- `tests/scripts/verify-perf-gate.py`, `tests/scripts/run-perf-gate.sh`, and `tests/baseline/perf-gate-v1.txt` — immutable-base deterministic ratchet and unchanged blocking limits.
- `tests/cmake/perf.cmake` and `tests/expected-tests.txt` — register the four targeted performance tests and exact inventory entries.
- `.github/workflows/release-rehearsal.yml` and `.github/workflows/release.yml` — carry advisory receipt evidence through rehearsal and release consumers without ordinary timing approval.
- `tests/scripts/verify-v02-delivery.py` and `.github/scripts/verify-workflow-policy.py` — exercise actual receipt consumers and protect the workflow contract with positive and negative controls.

## Verification

- Targeted CTest performance set at `411889324953d20bb3c88c516d3826bc6dfe98bd`: **11/11 passed**.
- Deterministic ratchet controls: **6/6 passed**; repeat digest and consumption controls: **4/4 passed**; existing perf-gate self-test: **33 controls passed**.
- Workflow policy check passed with `residual_write_jobs=5`; workflow policy self-test passed with **266 negative and 4 positive controls**.
- Delivery self-test passed with **7 positives, 48 rejected controls, and 2 real-owner rejections**. The release-gates self-test exited successfully.
- Python compilation and `git diff --check` passed.

## Decisions Made

- Paired wall-clock timing is advisory after evidence validation; it does not need ordinary owner approval.
- Ir ratio `1.10` and realtime floor `4.02` stay independent blocking release gates.
- A deterministic widening still requires bound deterministic evidence and cannot be manufactured from timing data. Plan 17-11 will add OWNER authorization to this conditional path; no exception or baseline change was made here.
- `STATE-05` remains an unclassified semantic edge. This performance plan makes no completion or coverage claim for it; requirement tracking remains with the phase owner.

## Deviations from Plan

None. The task 2 RED commit is the planned discriminating control slice. A delivery-fixture source-tree binding was corrected after its negative produced a fixture mismatch rather than the intended owner rejection; the corrected producer-generated receipt tests then passed through the actual delivery consumer.

## Known Stubs

None. The measured-process stub is confined to the planned underlying timing-process boundary; tests drive the production receipt producer and verifier/consumer functions.

## Deferred Verification and Limits

- The settled full project suite, cross-platform qualification, and hosted campaign are pending the parent executor. This plan ran only its targeted performance CTests and release evidence self-tests.
- No live release publication, tag change, version pull request, or push was performed.
- The summary does not update parent-owned `STATE.md`, `ROADMAP.md`, `REQUIREMENTS.md`, config, state JSON, or continuation tracking.

## Self-Check: PASSED

The summary file exists, all four Plan 17-07 task commits are ancestors of the recorded task head, and `plan_head_after` matches that immutable head. The GSD coverage classifier reports all three deliverables auto-covered; the `summary_coverage` CTest passes.

---
*Phase: GB-17-native-save-state-core*
*Plan: 07*
*Completed: 2026-10-26*
