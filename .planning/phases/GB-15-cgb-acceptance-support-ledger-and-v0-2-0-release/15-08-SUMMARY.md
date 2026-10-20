---
phase: 15-cgb-acceptance-support-ledger-and-v0-2-0-release
plan: "08"
subsystem: release
tags:
  - release-gate
  - delivery-evidence
  - idempotent-recovery
  - python
  - bash
requires:
  - phase: "Phase 15 Plan 02"
    provides:
      - "Schema-2 support sidecar and verify-support-ledger.py --verify-sidecar"
  - phase: "Phase 15 Plan 05"
    provides:
      - "Paired v0.1.0 performance receipt and verify-v02-performance.py --verify"
  - phase: "Phase 15 Plan 06"
    provides:
      - "Actual libFuzzer campaign receipt and verify-v02-fuzz.py --verify"
  - phase: "Phase 15 Plan 07"
    provides:
      - "Source archive receipt and verify-v02-source-archive.py --check-receipt"
provides:
  - "verify-v02-delivery.py: --check-evidence (owner validators plus cross-binding), --stage phase-pr|published (live readback), --self-test"
  - "Draft and final inventory gate requiring corpus, schema-2 sidecar, performance, fuzz, consumer and source-archive receipts"
  - "verify-release-gates.sh --check-v02-evidence and --check-recovery (live release state read first)"
  - "verify-published-release-assets.py --decide: published-verified, draft-reuse or draft-upload-missing, never overwrite"
affects:
  - "Plan 15-09 must wire the release workflow to upload the new evidence assets before this gate can pass on a real draft"
actuals:
  tokens: 18900
  tasks: 2
  commits: 2
commits: 2
plan_head_before: 1243222809c134b4ce5e4a8e041d9376a95c8db2
plan_head_after: e023e171151f68ddb3f2400b0c313a3fb55428cf
tech-stack:
  added: []
  patterns:
    - "Owner validators are invoked, never re-implemented; the delivery checker only adds identity cross-binding"
    - "A repo-root seam lets self-tests run the real checker against a private Git repository with stub owner scripts, while separate controls prove the real owners reject forged receipts"
    - "Recovery decisions are a pure function of live release state, assets and runs"
key-files:
  created:
    - tests/scripts/verify-v02-delivery.py
  modified:
    - .github/scripts/verify-release-gates.sh
    - .github/scripts/verify-published-release-assets.py
key-decisions:
  - "Reuse of an earlier performance or fuzz producer is accepted only with a record naming the receipt's own unaltered producer SHA, a substantive justification, tag-to-source resolution, ancestry, Git-object equality of every covered input, and the original producer's own validator run in a detached checkout."
  - "Published readback requires a final download directory distinct from, and not nested with, the earlier validation download, and hashes its bytes against the live API."
  - "The v0.2 evidence families replace release-performance-receipt.json in the required inventory; the workflow still uploads the old name until plan 15-09."
requirements-completed:
  - SHIP-09
  - SHIP-10
  - SHIP-11
coverage:
  - id: D1
    description: "A complete draft inventory with the schema-2 sidecar, corpus, performance, fuzz, consumer and source-archive evidence reaches the aggregate and final gates, and omitting any single required asset, altering bytes after the platform manifest, a schema-1 sidecar or an incomplete final inventory is rejected for the expected reason."
    requirement: SHIP-11
    human_judgment: false
    verification:
      - kind: integration
        ref: "bash .github/scripts/verify-release-gates.sh --self-test"
        status: pass
  - id: D2
    description: "The delivery checker runs the owner validators and binds every receipt to the exact tag and source; mismatched corpus, ledger, SHA, version, workflow attempt, unsupported or fast-only campaign, incompatible benchmark, missing C or C++ result and unjustified or covered-input-changing reuse are each rejected with the expected code."
    requirement: SHIP-11
    human_judgment: false
    verification:
      - kind: integration
        ref: "python3 -I tests/scripts/verify-v02-delivery.py --self-test"
        status: pass
  - id: D3
    description: "Stage receipts for the phase PR and the published release are compared with simulated live PR, check, run, tag, release and asset readback; stale, failed, forged, duplicated, extra and reused-validation evidence is rejected."
    requirement: SHIP-10
    human_judgment: false
    verification:
      - kind: integration
        ref: "python3 -I tests/scripts/verify-v02-delivery.py --self-test"
        status: pass
  - id: D4
    description: "Recovery reads live release state first and decides published-verified, draft-reuse or upload-only-missing; changed or resized attachments, duplicates, missing digests, concurrent or stale attempts and altered published assets are rejected and never overwritten."
    requirement: SHIP-10
    human_judgment: false
    verification:
      - kind: unit
        ref: "python3 -I .github/scripts/verify-published-release-assets.py --self-test"
        status: pass
      - kind: integration
        ref: "bash .github/scripts/verify-release-gates.sh --self-test"
        status: pass
duration: "about 1 hour"
completed: "2026-10-20"
status: complete
---

# Phase 15 Plan 08: Exact-Evidence Release Qualification and Recovery Summary

**A stdlib delivery checker runs the plan 02/05/06/07 owner validators, cross-binds every receipt to the exact tag, source and workflow attempt, and a live-state-first recovery decision reuses identical draft bytes and never overwrites changed or published assets.**

## Accomplishments

- Added `tests/scripts/verify-v02-delivery.py`. `--check-evidence DIR --tag --source-sha --source-archive` calls `verify-support-ledger.py --verify-sidecar`, `verify-v02-performance.py --verify`, `verify-v02-fuzz.py --verify` and `verify-v02-source-archive.py --check-receipt`, and separately binds the sidecar to the corpus receipt bytes, the performance and fuzz receipts to the tag source, the fuzz run and attempt to positive integers, and the downloaded C and C++ consumer receipt to the source and all four behaviours.
- Producer reuse is explicit: `evidence-reuse.json` must name the receipt's own producer SHA, justify itself, resolve the tag to the frozen source, prove ancestry and Git-object equality of every covered input, and the producer's own validator judges its receipt in a detached checkout. A producer SHA label is never rewritten.
- `--stage phase-pr|published --receipt PATH` re-derives PR state, exact-head required checks (GitHub Actions app), workflow run attempts, tag target, release state, published asset names, sizes and digests from read-only `gh api` GETs, and hashes a separate final download directory. Self-reported success-only fields carry no weight.
- `verify-release-gates.sh`: one `REQUIRED_ASSETS` list now drives the draft inventory, the final count and the self-test fixture; the schema-2 sidecar is mandatory; `check_v02_evidence` is routed from both `--check-draft` and `--check-draft-final` (the source archive is fetched from the GitHub generated archive URL); new `--check-v02-evidence` and `--check-recovery` modes. Validators now `|| return $?`, so a failing Python check cannot be masked when called inside a conditional.
- `verify-published-release-assets.py --decide` classifies live state and rejects partial-with-changed, duplicate, unexpected, digest-less, concurrent and stale cases.

## Task Commits

1. **Task 1 (tracer): complete draft inventory qualifies through the final gate** - `da50e62` (`feat`). This commit also carries the gate's `--check-recovery` shell mode and its stubbed-`gh` self-test, which belong to Task 2.
2. **Task 2: published readback, idempotency and collision recovery** - `e023e17` (`feat`)

## Verification Evidence

- `bash .github/scripts/verify-release-gates.sh --self-test` passed (exit 0): 20 single-asset omission controls, stale-manifest, schema-1 and incomplete-final controls, the delivery and published-asset self-tests, and six recovery scenarios whose gh call log proves the live release read precedes every decision.
- `python3 -I .github/scripts/verify-release-source-proof.py --self-test` passed.
- `python3 -I tests/scripts/verify-v02-delivery.py --self-test` passed: 4 positives, 36 rejected controls (each asserting its exact rejection code) and 2 real-owner rejections of a forged receipt.
- `python3 -I .github/scripts/verify-published-release-assets.py --self-test` passed: 3 recovery positives and 11 rejected controls.
- No tag, release, asset, push or merge was created; PR #70 is untouched. No hosted or live GitHub execution was performed: published-readback logic is tested only against private simulated fixtures, and v0.2.0 is not published.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Gate validators could be masked inside conditionals**
- **Found during:** Task 1 (first omission control reported "accepted")
- **Issue:** `check_asset_inventory` ended with a succeeding sidecar helper, so under `if`/`$(...)` where `set -e` is ignored a failing Python block returned success.
- **Fix:** the eight validator Python blocks in functions now end `|| return $?`.
- **Files modified:** `.github/scripts/verify-release-gates.sh`
- **Commit:** `da50e62`

**Total deviations:** 1 auto-fixed (Rule 1). Impact: none on scope.

## Known Limitations

- The positive path of the delivery self-test uses stub owner scripts in a private Git repository. The real owners are exercised by their own self-tests (plans 02/05/06/07) and here by forged-receipt rejection only; a positive run of the real owners over a real tagged draft awaits plan 15-09 and the hosted release lane.
- `--check-draft` and `--check-draft-final` will reject the current workflow's draft until plan 15-09 uploads `cgb-corpus-receipt.json`, `v02-performance-receipt.json`, `v02-fuzz-receipt.json`, `source-archive-receipt.json` and `v02-consumer-receipt.json`. This is intended: the gate requires the new evidence.
- The two task commits are not cleanly separated by file: the gate edits for both tasks landed in the first commit.

## Known Stubs

None.

## Threat Flags

None. The checker makes only read-only `gh api` requests and the source archive download uses HTTPS with a size bound.

## Next

Ready for 15-09 (release workflow wiring and CTest registration). Phase 15 is not complete; no auto-advance.

## Self-Check: PASSED
