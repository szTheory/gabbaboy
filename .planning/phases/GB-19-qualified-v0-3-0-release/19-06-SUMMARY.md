---
phase: GB-19-qualified-v0-3-0-release
plan: "06"
subsystem: release
tags: [v0.3.0, release, pre-flight, docs, CI, security]
requires:
  - phase: GB-19-qualified-v0-3-0-release/19-01..19-05
    provides: release policy, rehearsal, lifecycle, evidence and consumer gates
provides:
  - Initial synthetic v0.3.0 pre-flight and documentation-contract evidence
  - Review-fix controls for publication inventory, closure paths and judge CLI
affects: [GB-19-qualified-v0-3-0-release/19-06-final-preflight, GB-19-qualified-v0-3-0-release/19-07]
actuals:
  tokens: 35230
  tasks: 3
  commits: 13
plan_head_before: a3b5f8c88dfe5c0e3aa22867e75e38ed4cc4b438
plan_head_after: 33d3d63d1a079e6c4ce72b863e25033cc80c43de
tech-stack:
  added: []
  patterns: [immutable-source release checks, synthetic release-tree qualification, production-shaped negative controls]
key-files:
  created:
    - tests/scripts/verify-judge-outcome.py
    - tests/scripts/verify-changelog-heading.py
    - tests/scripts/verify-doc-links.py
    - .planning/phases/GB-19-qualified-v0-3-0-release/19-release-change-row.json
    - .planning/phases/GB-19-qualified-v0-3-0-release/19-notes-preface.md
  modified:
    - .github/scripts/release-evidence-lifecycle.sh
    - .github/scripts/verify-published-release-assets.py
    - .github/ci-timeouts.json
    - docs/release.md
    - docs/native-integration.md
    - docs/state-format.md
    - docs/support/unreleased.md
    - CHANGELOG.md
    - tests/CMakeLists.txt
    - tests/scripts/verify-state-pins.py
    - tests/scripts/verify-state-contract.py
    - tests/scripts/verify-v02-adoption.py
    - tests/scripts/verify-v03-dispositions.py
    - tests/scripts/verify-release-lifecycle.py
    - tests/expected-tests.txt
    - .planning/phases/GB-19-qualified-v0-3-0-release/19-REVIEW.md
    - .planning/phases/GB-19-qualified-v0-3-0-release/19-SECURITY.md
key-decisions:
  - "D-09 / 19-02-D1 remains an unadopted amendment candidate pending owner acknowledgment."
  - "REL-01 remains pending until exact-tag publication and readback."
  - "The initial hosted rehearsal and local qualification are historical evidence; final exact-head pre-flight is still required."
patterns-established:
  - "Use named refusal contracts and their recorded reason codes as negative evidence; a healthy workflow policy check is not forced to fail."
  - "Bind pre-publication and readback checks to the complete immutable release-asset inventory."
requirements-completed: []
coverage:
  - id: D1
    description: Initial synthetic v0.3.0 release tree and hosted producer rehearsal were qualified at immutable source 29f6ae2b; this evidence is historical pending the final settled-source rerun.
    requirement: REL-01
    verification:
      - kind: integration
        ref: "Historical chain: source 29f6ae2b818fdc4dac8b73b3107b5a9722e10578, H0 b1c268153c9e8aee02de8e98c1994892f3c38ea9, H1 532335e8eda1859b59ec95c241635ef3635cd90e, H-prime 0070895c1ace5067c67398f34888d1f726bbb28d. Installed-prefix suite 1690/1690; player Release 108/108 and Debug plus linkage 110/110."
        status: pass
      - kind: integration
        ref: "GitHub Actions release-rehearsal run 41015650680 at H-prime 0070895c: all six producer lanes succeeded; hosted judge result matched the predicted refusal; transient rehearsal branch deletion was confirmed. Historical evidence only."
        status: pass
    human_judgment: false
  - id: D2
    description: Release, host-integration, state-format, unreleased and changelog documentation describe v0.3.0 and retain automated adoption checks.
    requirement: REL-01
    verification:
      - kind: integration
        ref: "Immutable synthetic release tree at 29f6ae2b: v0.3 release-note adoption 22 checks and documentation adoption 446 checks passed. Historical evidence only."
        status: pass
    human_judgment: false
  - id: D3
    description: Changelog first-heading and versioned documentation-link contracts reject stale release metadata.
    requirement: REL-01
    verification:
      - kind: integration
        ref: "Immutable synthetic release tree at 29f6ae2b: changelog first-heading and doc-links checks passed; their controls are included in the installed-prefix suite. Historical evidence only."
        status: pass
    human_judgment: false
  - id: D4
    description: Round-one review fixes cover full publication inventory readback, pre-publication inventory drift, canonical closure paths, and the documented judge CLI.
    requirement: REL-01
    verification:
      - kind: unit
        ref: "Source b0beb4fd: verify-v03-dispositions readback controls 48; disposition controls 39; judge-outcome controls 22; published-assets self-test passed."
        status: pass
      - kind: integration
        ref: "Source b0beb4fd: post-tag lifecycle controls passed 3 positives, 84 controls and 23 endpoints; four wired controls passed 4/4. Evidence in build/preflight/runs/b0beb4fd8d1c2290d89b707860bf23c899e12fac/review/round1-evidence.md."
        status: pass
    human_judgment: false
duration: "not recorded; work continued across sessions"
completed: 2026-10-30
status: halted
---

# Phase 19 Plan 06: Synthetic 0.3.0 Pre-flight and Documentation Summary

**The initial synthetic release tree, documentation contracts, and first review-fix controls have passing evidence; the final settled-source pre-flight and PR A readiness remain pending.**

## Performance

- **Duration:** Not recorded; this plan continued across sessions.
- **Started:** Not recorded.
- **Prepared:** 2026-10-30.
- **Tasks:** 3 of 4 complete; Task 4 remains in progress.
- **Files modified:** 30 tracked files in the measured plan interval, before this summary and STATE update.
- **Plan interval:** 13 committed changes from `a3b5f8c88dfe5c0e3aa22867e75e38ed4cc4b438` through `33d3d63d1a079e6c4ce72b863e25033cc80c43de`.

## Accomplishments

- Built and qualified an initial synthetic v0.3.0 tree at H-prime `0070895c1ace5067c67398f34888d1f726bbb28d`, rooted at source `29f6ae2b818fdc4dac8b73b3107b5a9722e10578`. Historical local evidence includes 1,690/1,690 installed-prefix tests, CGB corpus 107/107 cases, player Release 108/108, and Debug plus linkage 110/110.
- Ran hosted rehearsal [41015650680](https://github.com/szTheory/gabbaboy/actions/runs/41015650680): all six producer lanes succeeded. The trusted judge's expected refusal matched the locally predicted result; the run-scoped fuzz artifact was used for the judge differential, and the transient `rehearsal/v0.3.0` branch was deleted and confirmed absent. This run predates the review fixes and is not final settled-source qualification.
- Updated release and host documentation, v0.3.0 changelog ordering, ledger links, release-note adoption pins, changelog-heading checks, and versioned doc-link checks. The installed-prefix suite exercised those contracts at the historical synthetic tree.
- Fixed the four reconciled round-one findings at `b0beb4fd8d1c2290d89b707860bf23c899e12fac`: full API asset inventory coverage in readback, frozen inventory comparison before publication, canonical closure-path validation, and the documented judge-helper CLI grammar. Their seeded positive and negative controls pass; review report `19-REVIEW.md` is clean for all 56 reviewed paths.
- Recorded the security audit at `33d3d63d1a079e6c4ce72b863e25033cc80c43de`: 26/35 threats closed, 9 operationally pending, including 4 blocking threats. Existing plan-time acceptance AR-19-01 is recorded; this is not a security or phase-completion sign-off.

## Initial bump-only and judge record

The following exact results are from the preserved historical run directory `build/preflight/runs/29f6ae2b818fdc4dac8b73b3107b5a9722e10578-resolved-rev-python310/`. Its H0 was `b1c268153c9e8aee02de8e98c1994892f3c38ea9`; this was the tree with only PR #131's three-file version bump. The selected CTest command returned exit 8 for 13 tests. CTest listed nine failed tests: `v02_game_claims`, `v02_game_claims_controls`, `v02_adoption_docs`, `v02_adoption_docs_controls`, `v02_support_ledger`, `v02_support_ledger_controls`, `support_ledger_binding`, `release_disclosure_generator`, and `release_disclosure_controls`. `state_pin_planning` also failed with `REJECT release-token-mismatch: golden release/format/behavior tokens differ from immutable source`; its dependent `state_portable_pins` was `Not Run`. The separate `workflow_policy_check` **passed** with `PASS: workflow privilege and trust wiring residual_write_jobs=5`; that healthy result is not counted as negative evidence.

The judge's (a) phase-branch run passed all three steps. Judge (b) used main/f80bdf54's own workflow arguments, attempted all three steps, and had no usage error. Its recorded lines are verbatim:

```text
Judge workflow privilege and trust wiring from the trusted checkout|1|REJECT workflow-unlisted
Confirm the rehearsal ref names the rehearsed tree's own version|0|pass
Verify the retained rehearsal campaign receipt with the trusted validator|1|receipt rejected: source input manifest does not match the required build inputs
```

For judge (c), the local prediction and hosted normalized outcome matched byte-for-byte:

```text
failure|Judge workflow privilege and trust wiring from the trusted checkout|2|usage unrecognized --git-root
```

The hosted job used main's trusted judge scripts; this recognized pre-PR-A usage refusal was the expected outcome. The downloaded fuzz artifact was the input to the three local judge worktrees. The local worktrees had full history; hosted trusted-judge fetch depth was 0 and hosted subject default fetch depth was 1, so shallow-subject history behavior remains unexercised.

The same synthetic H-prime `0070895c1ace5067c67398f34888d1f726bbb28d` produced the following exact step results:

```text
derive rehearsal/v0.3.0: REHEARSAL_TAG=v0.3.0
derive rehearsal/preflight-v0.3.0: rejected with REJECT rehearsal-ref: 'rehearsal/preflight-v0.3.0' is not rehearsal/vX.Y.Z
verify-subject: SOURCE_SHA=0070895c1ace5067c67398f34888d1f726bbb28d; RELEASE_TAG=v0.3.0
```

### Version-sensitive literal inventory

This is the concrete changed/retained inventory; it does not claim a fixture-only constant was changed.

| Classification | File and value | Evidence or reason |
|---|---|---|
| Changed behavior in 19-06 | `tests/scripts/verify-state-contract.py`: the positive cache test now reads `release_version` from immutable `CMakeLists.txt`, derives its expected triplet, and appends `.4` for the malformed control instead of hardcoding `0.2.1` in those two checks. | Commit `29adbaeb`; verified by the historical synthetic pre-flight and round-one controls. |
| Changed behavior in 19-06 | `tests/scripts/verify-v02-adoption.py`: the false-publication-claim matcher derives from `RELEASE_VERSION`; release text and the other adoption phrases are checked against the synthetic tree identity. | See the immutable-source checks in the historical synthetic run. |
| Changed behavior in 19-06 | `tests/scripts/verify-support-ledger.py` and the synthetic v0.3.0 tree: v0.3 ledger rendering/validation is added while the v0.2.1 tagged-ledger validator remains version-specific. The release documentation and ledger links point to the v0.3.0 ledger in that synthetic tree. | The version-bound ledger and documentation adoption checks passed at H-prime `0070895c`. |
| Changed earlier in Phase 19 | `.github/ci-timeouts.json`: six job rows' old `0.2.1` sizing prose was replaced by the D-04 run citations. | This is the Phase 19-01 ledger conversion, retained in the synthetic tree. |
| Deliberately retained | `.github/scripts/verify-workflow-policy.py`: `LEDGER_BOUND_LAST_VERSION = (0, 2, 1)`. | No `release_bound` rows remain; this boundary still makes the expiry and seventh-row controls reject a reintroduced row at v0.3.0. |
| Deliberately retained | `.github/scripts/verify-release-source-proof.py`: `REHEARSAL_TAG = "v0.2.1"`. | Research classifies this as a self-test fixture only; production selection receives the tag as an argument. It was not edited. |
| Deliberately retained | `tests/scripts/verify-state-pins.py`'s historical pre-first-release rule and fixture references to `0.2.1`; `tests/scripts/verify-state-contract.py`'s valid historical parser input `0.2.1`. | These describe the initial published state baseline and parser compatibility. `verify-state-pins.py` changed for immutable D-113/D-120 decision references, not to replace its historical version rule. |
| Deliberately retained | `tests/scripts/state_boundary.py`, historical rows in `tests/data/state-compatibility.json`, `tests/data/release-disclosure.json`'s `applies_after_version: 0.2.1`, and the `+@PERCENT@% versus v0.2.0` performance baseline. | These bind prior release evidence and are not v0.3.0 labels. The synthetic release-change row was added only to H-prime's scratch tree. |

## Task Commits

Measured plan-interval commits, oldest first:

1. `0a9a6c13` — add judge outcome preflight controls.
2. `81c78d35` — resolve immutable release decisions.
3. `d380644b` — reconcile v0.3.0 release documentation.
4. `8be8f909` — add stale changelog-heading contract.
5. `4ac83c69` — add immutable release-documentation checks.
6. `3fe0a5b7` — preserve historical release controls.
7. `29adbaeb` — bind state-version controls to the immutable revision.
8. `aab39829` — disclose timeout-ledger body drift.
9. `4c6c17ba` — prepare v0.3.0 release-window drafts.
10. `dbcf5197` — pin boundary revisions and Python 3.10 compatibility.
11. `29f6ae2b` — require the aggregate host-smoke receipt.
12. `b0beb4fd` — guard publication against inventory drift.
13. `33d3d63d` — record the pre-merge review and security audit.

The summary/STATE metadata commit is separate. It does not complete Task 4.

## Review-fix RED/GREEN evidence

The round-one RED evidence at source `29f6ae2b` reproduced all four defects: the production-shaped full inventory was rejected by readback; traversal through `pr-closures` was accepted; a post-gate asset removal was not refused before the draft-to-published transition; and the documented `--key STDERR_FILE --exit N` invocation was rejected by the helper parser.

At immutable source `b0beb4fd`, readback controls passed 48, disposition controls passed 39 (including Python 3.10 grammar and traversal controls), judge-outcome controls passed 22, the published-assets self-test passed, and the lifecycle replay passed 3 positives, 84 controls and 23 endpoints. Four wired controls passed 4/4. Full commands and unedited outputs are retained in `build/preflight/runs/b0beb4fd8d1c2290d89b707860bf23c899e12fac/review/`.

## Decisions Made

- `19-02-D1` / D-09 remains a candidate amendment only. `GBB_MAYBE_UNUSED` was not adopted into project decisions; owner acknowledgment is still required.
- `REL-01` remains pending until exact-tag publication and readback.
- Historical `LEDGER_BOUND_LAST_VERSION=(0, 2, 1)` remains unchanged because it drives expiry and seventh-row controls after RM-027 removed all `release_bound` rows.
- The initial bump-only `workflow_policy_check` passed. Negative evidence is based on the current named refusal contracts and their reason codes, not an invented failure count.
- Hosted trusted-judge fetch depth was 0; the hosted subject default depth was 1; local subject worktrees had full history. Shallow-subject history behavior was not exercised and remains an R1 coverage limitation.

## Deviations from Plan

### Plan-recorded deviations

- **19-06-D1:** the initial “fix every version literal” wording was applied only where evidence justified a change. The source-version-derived state-contract control and the current-version adoption behavior are recorded above. `verify-state-pins.py` was changed to resolve immutable D-113/D-120 decision references, not to relabel historical rows. `REHEARSAL_TAG="v0.2.1"` remains an unchanged self-test-only fixture, and `LEDGER_BOUND_LAST_VERSION=(0, 2, 1)` remains unchanged to preserve its refusal controls. The historical and performance literals retained are enumerated above.
- **19-06-D2:** H-prime was pushed to transient `rehearsal/v0.3.0` to exercise hosted producer steps past their tag-derivation checks. The historical branch was removed and its absence verified. The final settled-source rehearsal must repeat this and confirm deletion again before PR A.
- **19-03-D1:** the pre-PR-A OQ-3 `perf-attribution.yml` dispatch on main was executed as authorized by 19-03; run `40936934189` completed at `f80bdf54c6c7d81e8e21f0275b43cda6edf6c8c4` and its receipt is committed for PR A.
- **19-02-D1:** the D-09 amendment candidate is explicitly not adopted and remains for owner acknowledgment.

### Template attribution correction

The copied plan text requests a Claude Code footer. The PR body will use truthful Codex/OpenGSD attribution instead; the copied footer is treated as a template-only deviation, not a factual authorship claim.

### Interim GSD status

This summary records completed local and initial pre-flight evidence only. It uses `status: halted` because the required final settled-source pre-flight, PR A creation and exact-head CI readiness are not yet complete. STATE remains on executing Plan 19-06. Operational PR/merge facts belong in `build/phase19-window/facts.env` and `continue.md`; no merge, tag, publication, REL-01 completion, or 19-07 execution is claimed here.

## Issues Encountered and Limitations

- The initial hosted judge failure was a designed pre-PR-A refusal from the main-side judge scripts; its normalized line matched the local prediction. A hosted failure in a `uses:` step is outside the local `run:`-step emulation and must fail the final comparison closed.
- The independent review and security audit ran after the initial synthetic H-prime. The final H0/H-prime chain, H0 receipt, final-source full suite, current CGB receipt, player gates, hosted six-producer run and judge comparison must all be rebuilt or rerun at the settled source before PR A.
- The final exact-head CI, PR A, owner D-09 acknowledgment, squash merge and #131 regeneration have not occurred. No v0.3.0 release tag exists as of this interim summary.
- The optional `gsd-tools windows append --kind unrun-verify` did not write an entry: the runtime rejected the existing Windows ledger's entry 20 because its status is `resolved`, which this runtime does not accept. No unrelated ledger entry was changed; the final verification remains explicit above.

## Next Phase Readiness

Continue **Plan 19-06 — Synthetic 0.3.0 pre-flight, docs and doc checks, PR A readiness**. Resume with `/gsd-execute-phase 19`; first update the ignored runner's source pin to the committed summary head, then run the fresh coherent H0-to-H-prime construction and final local/hosted gates. Do not start Plan 19-07. After a reviewable PR A and exact-head CI readiness exist, stop for the D-09 owner acknowledgment before any squash merge.

## Self-Check: PASSED

The plan-interval base and head are ancestors of the current branch; the committed source controls and review/security reports cited above exist. This summary is intentionally halted and does not claim the remaining Task 4 outcomes.

---
*Phase: GB-19-qualified-v0-3-0-release*
*Plan: 06 — interim summary; final preflight and PR A readiness pending*
