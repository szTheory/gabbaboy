---
phase: 15-cgb-acceptance-support-ledger-and-v0-2-0-release
plan: "06"
subsystem: testing
tags:
  - fuzzing
  - libfuzzer
  - sanitizers
  - ci
  - receipts
requires:
  - phase: "Phase 15 Plan 01"
    provides:
      - "Phase 15 evidence and receipt conventions"
provides:
  - "run-bounded-fuzz.sh --explore --receipt: an actual 60-second Clang/libFuzzer ASan/UBSan campaign with a strict receipt"
  - "verify-v02-fuzz.py: strict receipt validator, 19 negative controls, and --verify-hosted exact-source verification"
  - "Linux sanitizer CI job pinned to clang-18 that runs the campaign, validates the receipt and uploads it"
affects:
  - "Phase 15 release plans that must re-run the same campaign recipe on exact-tag inputs"
actuals:
  tokens: 30000
  tasks: 2
  commits: 9
plan_head_before: 0cbecc9bc1582e76c88153dfb4f898b116e6bafd
plan_head_after: bd7a7f579d92387bf99801ee91c15123fa2d4c04
tech-stack:
  added: []
  patterns:
    - "Hosted evidence is accepted only for the exact pushed SHA, push event, ci.yml path, completed linux-asan-ubsan job and an artifact whose receipt, run, attempt, job and source-input digests all agree"
    - "Fuzz oracles are gated on model applicability: KEY1 speed scenarios apply to the CGB profile only"
key-files:
  created: []
  modified:
    - tests/scripts/run-bounded-fuzz.sh
    - tests/scripts/verify-v02-fuzz.py
    - .github/workflows/ci.yml
    - tests/fuzz_core.c
    - tests/test_fuzz_core.c
key-decisions:
  - "The first hosted campaign (run 38947419636) failed after 4 executions on a harness oracle bug, not an emulator defect: fuzz_speed() demanded a KEY1 speed switch and KEY1 reads on the DMG profile, where KEY1 is not a guest register. DMG now falls back to the STOP/wake twin (scenario 7) except the held-button scenario 3; CGB expectations are unchanged."
  - "The validator's hosted download had never worked: urllib forwarded the bearer token to the signed blob redirect (HTTP 401, and a credential leak), and the unfiltered 1.2 MB runs listing was intermittently truncated. Authorization is now dropped on redirects and runs are queried by exact head SHA and push event."
  - "The validator hashes itself into the receipt, so fixing it required a new push and a new hosted campaign; the earlier run a208c2f was not reused as proof."
requirements-completed:
  - SHIP-11
coverage:
  - id: D1
    description: "A Clang 18 libFuzzer ASan/UBSan fuzz_core binary performed an actual bounded campaign on the hosted Linux sanitizer job for the exact pushed source, recording nonzero executions, elapsed time over 60 seconds, exit code 0, a non-synthetic result and the bounded libFuzzer arguments, and the existing validator accepted it for that SHA."
    requirement: SHIP-11
    human_judgment: false
    verification:
      - kind: e2e
        ref: "python3 -I tests/scripts/verify-v02-fuzz.py --verify-hosted --source-sha bd7a7f579d92387bf99801ee91c15123fa2d4c04"
        status: pass
  - id: D2
    description: "Unsupported runtime, absent or zero-run campaigns, fast-only checks, fabricated or stale receipts, relaxed bounds, and a workflow that drops the exploration, the strict validator or the pinned compiler or broadens workers are each rejected by the real production entry points."
    requirement: SHIP-11
    human_judgment: false
    verification:
      - kind: integration
        ref: "python3 -I tests/scripts/verify-v02-fuzz.py --self-test"
        status: pass
      - kind: integration
        ref: "bash tests/scripts/run-bounded-fuzz.sh --self-test"
        status: pass
  - id: D3
    description: "The DMG-profile speed scenarios that the first hosted campaign minimized to a 518-byte input no longer fail the harness, while the CGB-profile speed seeds still require a speed switch and KEY1 reads and the inverted-oracle mutant is still rejected."
    requirement: SHIP-11
    human_judgment: false
    verification:
      - kind: unit
        ref: "build/tests/test_fuzz_core cgb_speed"
        status: pass
      - kind: integration
        ref: "ctest fuzz and v02 selection of 15 tests in build"
        status: pass
duration: "multi-session; this continuation about 2 hours including two hosted runs"
completed: "2026-10-20"
status: complete
---

# Phase 15 Plan 06: Bounded libFuzzer Campaign Summary

**An actual 60-second Clang/libFuzzer ASan/UBSan campaign now runs on the existing Linux sanitizer job, produces a strict receipt, and is verified for its exact pushed SHA by the existing validator.**

## Hosted Evidence

- Source SHA: `bd7a7f579d92387bf99801ee91c15123fa2d4c04` on `gsd/phase-15-cgb-acceptance-support-ledger-and-v0-2-0-release`
- CI run: https://github.com/szTheory/gabbaboy/actions/runs/39357838513 (attempt 1, push event, conclusion success; macos-player-package skipped by design, all required jobs green)
- Sanitizer job id 118416686074, artifact `v02-fuzz-39357838513-1`
- Receipt SHA-256: `a658e06dc157a64a75fb613dc51cbedbdb5a6f56c9e5f29097df42304f28eeb7`
- Validator output: `hosted_campaign=pass source_sha=bd7a7f579d92387bf99801ee91c15123fa2d4c04 run=39357838513 attempt=1 job=118416686074 executions=390 elapsed=61.872s ci_workflow_conclusion=success`
- Throughput is low (390 executions in about 62 s) because speed scenarios run up to 600000 half-dots per input under ASan/UBSan. The requirement is nonzero real exploration within the declared bounds, which is met; it is not a coverage claim.
- A local campaign was not possible: Apple clang here has no libFuzzer runtime (`libfuzzer_runtime=unsupported`), so local runs covered only self-tests and deterministic regressions. Local results do not close the gate.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fuzz speed oracle ignored the DMG profile**
- **Found during:** hosted campaign run 38947419636 (failed after 0.479 s / 4 executions)
- **Issue:** minimized 518-byte input (sha256 `532b3bf198c578ebf2b97e05415208187a34a8aa5ecd0e5fc96b6609f12f8263`, data[0]=0x10, data[1]=1) is a DMG-profile speed scenario 1. `switch_expected` and the `key1_reads` expectation ignored `cgb_profile`. Reproduced locally for DMG scenarios 0, 1, 2, 4, 5 (switch and KEY1 reads) and 6 (a woken DMG guest reads KEY1 and stops with an unsupported-bus result, which is the designed DMG behavior).
- **Fix:** on DMG, scenarios other than the held-button scenario 3 fall back to the STOP/wake twin (scenario 7); `switch_expected` and the KEY1-read expectation require `cgb_profile`. CGB expectations are untouched. Regression seeds for the minimized prefix and DMG scenarios 0, 2, 4, 5, 6 were added to `cgb_fuzz_speed_regressions`; they failed before the fix (`DMG-profile speed seed 0 failed`, 2 contract failures) and pass after. The existing CGB seeds (minimum switches and reads) and the inverted-oracle mutant control remain the negative control that the oracle was not deleted.
- **Files modified:** tests/fuzz_core.c, tests/test_fuzz_core.c
- **Commit:** a208c2f (RED verified locally, then committed together with the GREEN fix as one commit)

**2. [Rule 3 - Blocking] Hosted verification could not download the artifact**
- **Found during:** step 5 on run 39353828855 (the campaign had passed there)
- **Issue:** `--verify-hosted` raised "malformed JSON" because the unfiltered all-runs listing (about 1.2 MB) was intermittently truncated, and its artifact download got HTTP 401 because urllib forwarded the bearer token to the signed blob redirect.
- **Fix:** drop `Authorization` on redirects and query runs with `head_sha` and `event=push`. Because the validator digest is bound into the receipt, run 39353828855 was not accepted as proof; a new push and campaign produced the evidence above.
- **Files modified:** tests/scripts/verify-v02-fuzz.py
- **Commit:** bd7a7f5

## Threat Flags

None. The credential-forwarding defect in the validator was removed (T-15-11 tampering surface), not introduced.

## Known Stubs

None.

## Self-Check: PASSED

- Commits a208c2f and bd7a7f5 are ancestors of HEAD and pushed (origin updated a175a39 to bd7a7f5, no force push).
- Local gates: `bash tests/scripts/run-bounded-fuzz.sh --self-test` pass; `python3 -I tests/scripts/verify-v02-fuzz.py --self-test` pass (19 negative controls, 10 rejected mutations); full fuzz/hostile/HDMA/speed CTest selection (267 tests) pass.
