---
phase: GB-19-qualified-v0-3-0-release
verified: 2026-10-31T17:16:01Z
status: gaps_found
score: "87/88 must-haves verified"
covered_files:
  - .gitattributes
  - .github/ci-timeouts.json
  - .github/scripts/release-evidence-lifecycle.sh
  - .github/scripts/verify-published-release-assets.py
  - .github/scripts/verify-release-source-proof.py
  - .github/scripts/verify-test-inventory.sh
  - .github/scripts/verify-workflow-policy.py
  - .github/workflows/ci.yml
  - .github/workflows/libbet-repro.yml
  - .github/workflows/preview.yml
  - .github/workflows/release-please.yml
  - .github/workflows/release-rehearsal.yml
  - .github/workflows/release.yml
  - .github/workflows/version-pr-gate.yml
  - .planning/phases/GB-19-qualified-v0-3-0-release/19-01-PLAN.md
  - .planning/phases/GB-19-qualified-v0-3-0-release/19-01-SUMMARY.md
  - .planning/phases/GB-19-qualified-v0-3-0-release/19-02-PLAN.md
  - .planning/phases/GB-19-qualified-v0-3-0-release/19-02-SUMMARY.md
  - .planning/phases/GB-19-qualified-v0-3-0-release/19-03-PLAN.md
  - .planning/phases/GB-19-qualified-v0-3-0-release/19-03-SUMMARY.md
  - .planning/phases/GB-19-qualified-v0-3-0-release/19-04-PLAN.md
  - .planning/phases/GB-19-qualified-v0-3-0-release/19-04-SUMMARY.md
  - .planning/phases/GB-19-qualified-v0-3-0-release/19-05-PLAN.md
  - .planning/phases/GB-19-qualified-v0-3-0-release/19-05-SUMMARY.md
  - .planning/phases/GB-19-qualified-v0-3-0-release/19-06-PLAN.md
  - .planning/phases/GB-19-qualified-v0-3-0-release/19-06-SUMMARY.md
  - .planning/phases/GB-19-qualified-v0-3-0-release/19-07-PLAN.md
  - .planning/phases/GB-19-qualified-v0-3-0-release/19-07-SUMMARY.md
  - .planning/phases/GB-19-qualified-v0-3-0-release/19-08-PLAN.md
  - .planning/phases/GB-19-qualified-v0-3-0-release/19-08-SUMMARY.md
  - .planning/phases/GB-19-qualified-v0-3-0-release/19-CONSUMER-MARKER-RESCOPE.md
  - .planning/phases/GB-19-qualified-v0-3-0-release/19-DRAFT-TAG-DRIFT-RESCOPE.md
  - .planning/phases/GB-19-qualified-v0-3-0-release/19-DRAFT-TAG-RESTORATION-RESCOPE.md
  - .planning/phases/GB-19-qualified-v0-3-0-release/19-ENTRYPOINT-UTF8-RESCOPE.md
  - .planning/phases/GB-19-qualified-v0-3-0-release/19-POST-TAG-FAILURE.md
  - .planning/phases/GB-19-qualified-v0-3-0-release/19-READBACK-RUN-LINK-RESCOPE.md
  - .planning/phases/GB-19-qualified-v0-3-0-release/19-REVIEW-DISPOSITION.md
  - .planning/phases/GB-19-qualified-v0-3-0-release/19-REVIEW.md
  - .planning/phases/GB-19-qualified-v0-3-0-release/19-SCHEMA-VALIDATION-RESCOPE.md
  - .planning/phases/GB-19-qualified-v0-3-0-release/19-SECURITY.md
  - .planning/phases/GB-19-qualified-v0-3-0-release/19-VALIDATION.md
  - .planning/phases/GB-19-qualified-v0-3-0-release/19-WINDOWS-READBACK-WIRING-RESCOPE.md
  - .planning/phases/GB-19-qualified-v0-3-0-release/19-release-change-row.json
  - .planning/phases/GB-19-qualified-v0-3-0-release/19-release-readback.json
  - .release-please-manifest.json
  - CHANGELOG.md
  - CMakeLists.txt
  - README.md
  - cmake/CheckContractRevWiring.cmake
  - cmake/ExpectedTests.cmake
  - cmake/ResolveContractRevision.cmake
  - docs/native-integration.md
  - docs/preview.md
  - docs/release.md
  - docs/state-format.md
  - docs/support/unreleased.md
  - docs/support/v0.3.0.md
  - src/core/gabbaboy.c
  - tests/CMakeLists.txt
  - tests/baseline/perf-attribution-v1.json
  - tests/baseline/state-goldens-v1.json
  - tests/ci/test-budget-allowlist
  - tests/cmake/ci-lanes.cmake
  - tests/cmake/host-contract.cmake
  - tests/cmake/hygiene.cmake
  - tests/cmake/perf.cmake
  - tests/cmake/save-formats.cmake
  - tests/data/release-api/SOURCES.md
  - tests/data/release-api/captured.json
  - tests/data/release-api/v030-draft-association-restoration.json
  - tests/data/release-api/v030-notes-failure.json
  - tests/data/release-lifecycle-post-tag-coverage.json
  - tests/data/state-compatibility.json
  - tests/data/state-forks.json
  - tests/data/support-claims-v0.3.json
  - tests/data/version-window.json
  - tests/data/workflow-policy-controls.json
  - tests/expected-tests.txt
  - tests/player/CMakeLists.txt
  - tests/scripts/run-perf-gate.sh
  - tests/scripts/test_installed_host.py
  - tests/scripts/verify-changelog-heading.py
  - tests/scripts/verify-doc-links.py
  - tests/scripts/verify-judge-outcome.py
  - tests/scripts/verify-no-interop-claims.py
  - tests/scripts/verify-perf-gate.py
  - tests/scripts/verify-phase3-player.sh
  - tests/scripts/verify-planning-hygiene.py
  - tests/scripts/verify-release-lifecycle.py
  - tests/scripts/verify-state-contract.py
  - tests/scripts/verify-state-forks.py
  - tests/scripts/verify-state-mutants.py
  - tests/scripts/verify-state-pins.py
  - tests/scripts/verify-support-ledger.py
  - tests/scripts/verify-v02-adoption.py
  - tests/scripts/verify-v02-consumers.py
  - tests/scripts/verify-v02-delivery.py
  - tests/scripts/verify-v02-fuzz.py
  - tests/scripts/verify-v03-dispositions.py
  - tests/scripts/verify-version-window.py
  - tests/scripts/verify-workflow-policy-coverage.py
  - tests/test_cgb_profile.c
  - tests/test_state_codec.c
  - tests/test_state_fork.c
covered_digest: "v4:sha256:3636b006229d37af9ad12bafb7843d1cbe3aaf10e5d8cca37138bc03529b44d1"
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: gaps_found
  previous_score: "87/88 must-haves verified"
  gaps_closed: []
  gaps_remaining:
    - "D-28 PR B publication/readback closure is merged and the post-squash phase-boundary handoff is complete."
  regressions: []
gaps:
  - truth: "D-28 PR B publication/readback closure is merged and the post-squash phase-boundary handoff is complete."
    status: failed
    reason: "PR137 remains open at older source 6c99ff0b. D135's fresh native Windows checks passed at its then-current head, but D136 is not yet on the PR and has no fresh exact-head native Windows, Linux sanitizer or all-required protected CI result. The six old 6c99ff0b runs are terminal and triaged; their red results are preserved and are not qualification of D136. The guarded squash, actual main-boundary checks and owner-workspace adoption remain pending."
    artifacts:
      - path: .planning/phases/GB-19-qualified-v0-3-0-release/19-07-PLAN.md
        issue: "The D-28 terminal PR B and post-squash boundary steps are still pending."
      - path: .planning/phases/GB-19-qualified-v0-3-0-release/19-07-SUMMARY.md
        issue: "The recorded route to phase verification follows PR B completion."
      - path: .planning/phases/GB-19-qualified-v0-3-0-release/19-WINDOWS-READBACK-WIRING-RESCOPE.md
        issue: "D135's two native Windows checks passed, but fresh exact-head checks for the newer D136 candidate and all protected jobs remain required before the planned guarded merge."
      - path: .planning/phases/GB-19-qualified-v0-3-0-release/19-CONSUMER-MARKER-RESCOPE.md
        issue: "D136's local consumer-marker regression passes; native Linux sanitizer and all required exact-head PR checks have not yet run on this candidate."
    missing:
      - "Update PR137 to current D136 source 87520382 and obtain fresh exact-head native Windows, Linux sanitizer and all required protected CI checks under the production duplicate-check guard; then perform only the planned guarded squash, verify the actual main boundary and negative-base predicate, adopt the owner workspace, and record the continuation boundary SHA before stopping at /gsd-verify-work 19."
---

# Phase 19: Qualified v0.3.0 Release Verification Report

**Phase Goal:** v0.3.0 is published from its exact tag with save-state and host-contract claims scoped by model, corpus and platform, and every receipt bound to that tag; release hardening happens before the tag, not after.
**Verified:** 2026-10-31T17:16:01Z
**Status:** gaps_found
**Re-verification:** Yes — same audit refreshed after D136; the original PR B boundary gap remains.
**Candidate:** implementation HEAD 87520382c44e55930607df6b6bb58c773c011552; it records D136 independent checks and phase evidence updates.

## Goal Achievement

### Roadmap Success Criteria

| # | Truth | Status | Evidence |
|---|---|---|---|
| 1 | The exact-tag producer rehearsal is green on the reviewed version-PR head before tagging, and the gate refuses an ineligible or postdated rehearsal. | ✓ VERIFIED | Actual R1 run 41135937384 succeeded at H=5948b0c3. R2 run 41140523418 succeeded at W=c4c0258b; W gate 41143678963 records the active verdict and exact R2/W binding. Its wrong-run and inactive-output controls reject, and the raw-log observer excludes echoed shell patterns. |
| 2 | The v0.3.0 support ledger scopes save-state and host-contract claims by model, corpus and platform, and rejects an unscoped claim. | ✓ VERIFIED | Current checks report 9 scoped claims and 10 non-claims; the tagged ledger is generated from managed claim input, and the claim checker controls are in the final passing CTest run. Published text limits evidence to the software profiles and platforms actually exercised. |
| 3 | Consumer, package, fuzz and performance receipts bind to the tag and reconcile with the published assets. | ✓ VERIFIED | Tag v0.3.0 resolves to S=a3f33904 with tree c796da0d, exactly equal to W's tree. Release 429606490 is published from S; retry workflow G=d61a25ea and actual attach/final jobs are separately recorded. The sourced pre-publish artifact is from run 41205021983 attempt 1; the committed readback and actual API capture reconcile all 22 asset IDs, names and SHA-256 digests. Wrong-source/readback controls pass. |

**Roadmap score:** 3/3. **Combined score:** 87/88 truths verified (85 plan truths plus 3 roadmap truths; no plan truth was dropped for restating a broader criterion).

The original required-artifact query passed all 25 declared artifacts. Full core/player/package qualification at implementation HEAD 17920163182d4af453c3255b20913be0c08a9e54 recorded 1,707 CTest cases with zero failures or skips, plus the installed inventory, player package, separate Debug linkage, extracted package bytes and no-input negative check. D135 changes only tests/CMakeLists.txt and .gitattributes; D136 changes only the consumer-test marker checker. Compiled core, API, player and fixture sources remain byte-identical through 87520382. At e46023c53bdff9e7ac44fcfb33a9e237ceec0430, the focused D135 configure/build/install and 23 affected CTests passed without skips. At e292db8c651e6f297ba6eb77049d2ca6f021304f, the D136 source-bound configure/build/install and 25 selected tests passed with no skips. HEAD 87520382 records fresh rechecks and phase evidence. The full suite was not rerun.

### Plan-Level Truths

| Plan | Truths verified | Evidence summary |
|---|---:|---|
| 19-01 | 13/13 | Timeout ledger, immutable Git-object checks, judge checkout/policy wiring and negative controls pass; player linkage and measured policy floors are covered by the full suite. |
| 19-02 | 9/9 | State validation precedes mutation; shared raw conversion is wired; state pins, continuations and mutant controls pass. The documented GBB_MAYBE_UNUSED deviation is present in the plan summary. |
| 19-03 | 10/10 | Managed claims render the ledger; fixed-point, sidecar binding, evidence coverage, no-interop and seeded omission controls pass. |
| 19-04 | 10/10 | Candidate and nightly gates call the trusted rehearsal-source checker with the PR head, merge time and attempt jobs; version-PR gate calls the immutable version-window checker. Actual H/W/R1/R2 captures satisfy the release sequence. |
| 19-05 | 12/12 | Same-source performance artifact upload/download and receipt validation are wired; retry, exact ratio, host smoke, published readback, sourced pre-publish inventory and privacy controls pass. Actual receipt source is S. |
| 19-06 | 12/12 | Reviewed release content, notes/adoption controls and operational preflight are evidenced. The frozen 19-06 SUMMARY remains its historical pre-merge halt as required; actual PR A #133 closure, renewed preflight, exact CI/performance evidence and regeneration are recorded in 19-07 and captured facts, so the frozen status was not treated as current operational evidence. |
| 19-07 | 12/13 | The tag, readback, ledger freeze, boundary snapshots and REL-01 trace are present and verified. D135's Windows caller/EOL correction and D136's atomic consumer-test marker correction pass their local affected checks. New exact-head Windows/Linux sanitizer/all-protected CI and the D-28 guarded-squash/boundary handoff remain pending as the single failed truth below. |
| 19-08 | 6/6 | The original missing-notes failure is preserved; approved recovery kept the same tag and release identity; the one retry and actual G/S distinction are recorded. No retry renewal, tag move, new release or additional corrective merge occurred. |

All 13 plan prohibitions were checked separately: 12 test-tier negative requirements are exercised by the final passing suite; the single judgment-tier stop instruction was preserved (this verifier did not run verify-work, a milestone audit or another phase). The non-inferable retry backstop is supported by observed API/Git facts: the sole retry published the same release ID and exact existing tag without moving either.

### Approved Post-Tag Exceptions

The goal's general rule that release hardening happens before tagging was not literally true for the bounded recovery and readback/schema repairs. The first post-tag release run 41148606886 failed because the generated notes were absent. Owner approvals D130-D134 then authorized specific readback/run-link corrections, diagnosis of the same-draft association drift, one conditional tag-only restoration and the already-authorized retry, two UTF-8 entrypoint conversions, and the exact seven-path schema validation repair with fresh tests and independent reviews. The actual read-only preflight TypeError happened before any write and is preserved as a failure, not represented as a successful preflight.

The captured history shows one tag-only restoration of the existing draft association with the body unchanged, then one original retry on workflow G; release 429606490 was published from S with 22 reconciled assets. The phase candidate's diff from S changes no core, public API, state format/pins, release workflow, timeouts, policy authority or performance limits. D134 changes are limited to the approved validators/tests. D135 is a separate owner-approved repair to the final readback test caller and the exact helper checkout representation; it changes no validator, release workflow, product behavior, release asset or release state. D136 is a separate owner-approved repair to the private consumer-test pause marker's publication and its regression; real interruption assertions, marker schema and deadlines are unchanged. No release action or retry was performed for D135 or D136. These are recorded narrow exceptions, not evidence that no post-tag work occurred or a general risk waiver.

### D135 Windows Readback Wiring

PR137's earlier exact-head Windows jobs at 524ba3f7 exposed two strict-gate failures: the readback CTest supplied a drive-absolute filesystem path to an immutable Git reader, and Windows CRLF checkout bytes failed the recovery helper's exact Git-blob guard. Those original failures remain preserved and were not rerun unchanged.

The owner-approved D135 patch changes exactly .gitattributes and tests/CMakeLists.txt from the reviewed PR head. The CTest now derives a repository-relative Git path from PROJECT_SOURCE_DIR and GBB_LIVE_PHASES_DIR while retaining the same immutable --rev, tag, exit/output contract, planning label and timeout. The root-anchored EOL rule applies only to the byte-compared published-asset helper. The immutable reader still refuses missing, wrong-root, drive-absolute and traversal paths; the helper and raw-byte guard are unchanged, and the APU unpinned EOL negative stays outside the rule. The forced-autocrlf baseline/fixed true/false controls show the conversion is handled without weakening byte identity.

The approved patch matches the isolated prototype and digest recorded in the D135 rescope. Captured configure/build/install and focused CTest evidence at e46023c53bdff9e7ac44fcfb33a9e237ceec0430 records 23 affected tests passing with no skips. Four documentation, summary-coverage and planning-label checks also pass after the D135 evidence documents were appended. Both native Windows checks passed at the D135 PR head. Since D136 changed source afterward, current-head protected checks are still required before merge.

### D136 Consumer-Test Marker Publication

The existing private pause hook exposed a race in Linux sanitizer CI: the parent test harness could observe the marker file after creation but before its JSON payload was written, producing a JSONDecodeError. The original CI failure is retained. The remaining six runs for source 6c99ff0b finished and were triaged: push CI and both fixture jobs passed, PR CI failed on the marker race and required-native aggregate, and preview producer gates refused that same failed PR CI. No unchanged run was retried or merged, and no unrelated failure was found. D135's two native Windows jobs passed on that prior head, but they do not qualify this newer D136 source.

The owner-approved D136 change is limited to tests/scripts/verify-v02-consumers.py. It writes complete private marker JSON to a unique sibling temporary file, atomically replaces the readiness path, and removes a leftover temporary in all cases. Its deterministic regression observes the actual writer at the empty and partial write points, requires the ready path to remain absent, checks the exact completed payload and cleanup, rejects the original writer, and accepts the fixed writer. Both real interruption tests, their cleanup/retry/lock assertions, the marker schema, signal behavior, normal receipt publication, opt-in variables and deadlines remain unchanged.

The exact approved patch matches prototype 8fdc1e63 and the recorded patch SHA in 19-CONSUMER-MARKER-RESCOPE.md. Source-bound configure, build and install at e292db8c651e6f297ba6eb77049d2ca6f021304f all succeeded; 25 affected tests passed with zero skips, including both complete C and C++ consumer controls that run the regression and real interruption coverage. Compiled core, API, player and fixture inputs remain byte-identical to the prior full qualification. The fresh independent code review is clear and the independent security recheck remains 41/41. This is local evidence only: Linux sanitizer CI and all other required exact-head protected checks for D136 are pending. No new release operation was performed.

### Required Artifacts

| Artifact | Expected | Status | Details |
|---|---|---|---|
| .github/ci-timeouts.json | Converted timeout ledger | ✓ VERIFIED | Present; full policy and Git-object controls pass. |
| .github/scripts/verify-workflow-policy.py | Ledger and trusted-judge enforcement | ✓ VERIFIED | Present and wired into rehearsal, with refusing mutants. |
| tests/player/CMakeLists.txt | Single-core player linkage | ✓ VERIFIED | Present; Debug linkage tests pass. |
| src/core/gabbaboy.c | Validated state apply and shared raw conversion | ✓ VERIFIED | Present; full state suite and mutant controls pass. |
| tests/scripts/verify-state-mutants.py | State range-check mutation control | ✓ VERIFIED | Present; fifth mutant is exercised by CTest. |
| tests/scripts/verify-planning-hygiene.py | Deferred decision pins | ✓ VERIFIED | Present; planning-hygiene controls pass. |
| tests/data/support-claims-v0.3.json | Managed scoped claims | ✓ VERIFIED | Present; 9 claims, 10 required non-claims. |
| tests/scripts/verify-support-ledger.py | Ledger generation and binding | ✓ VERIFIED | Present; source-S claims and ledger checks pass. |
| tests/baseline/perf-attribution-v1.json | Measured performance attribution | ✓ VERIFIED | Present; final full suite and source-S receipt checks pass. |
| .github/workflows/version-pr-gate.yml | Pre-tag version PR gate | ✓ VERIFIED | Present; invokes trusted version-window validation. |
| .github/scripts/verify-release-source-proof.py | Rehearsal/source/time binding | ✓ VERIFIED | Present; PR-head and timestamp checks are in candidate and nightly paths. |
| tests/data/release-api/captured.json | API response contract fixtures | ✓ VERIFIED | Present; replay contracts pass. |
| tests/scripts/verify-perf-gate.py | Exact-source performance receipt | ✓ VERIFIED | Present; receipt and exact-ratio controls pass. |
| tests/scripts/verify-v03-dispositions.py | Tag-bound release/readback validation | ✓ VERIFIED | Present; actual 22-asset readback passes. |
| .github/scripts/release-evidence-lifecycle.sh | Release lifecycle gate wiring | ✓ VERIFIED | Present; actual release run completed its qualified publish path. |
| .planning/phases/GB-19-qualified-v0-3-0-release/19-release-change-row.json | Reviewed release-change row | ✓ VERIFIED | Present and covered by the planning/contract suite. |
| tests/scripts/verify-judge-outcome.py | Preflight judge outcome checker | ✓ VERIFIED | Present; outcome controls run in the full suite. |
| tests/scripts/verify-changelog-heading.py | Version-first changelog contract | ✓ VERIFIED | Present; positive and seeded-omission tests pass. |
| tests/scripts/verify-doc-links.py | Tag-aware release documentation links | ✓ VERIFIED | Present; live and negative contract tests pass. |
| docs/support/v0.3.0.md | Scoped v0.3.0 support ledger | ✓ VERIFIED | Present; generated ledger and tag blob binding pass. |
| .planning/phases/GB-19-qualified-v0-3-0-release/19-release-readback.json | Actual publication and pre-publish readback | ✓ VERIFIED | Present; strict readback passes at this candidate. |
| tests/scripts/verify-v02-consumers.py | Private consumer-test pause marker and interruption checks | ✓ VERIFIED | D136 atomically publishes the complete marker; both C and C++ consumer controls pass with the deterministic partial-write regression. |
| tests/data/release-api/v030-notes-failure.json | Original missing-notes regression | ✓ VERIFIED | Present; actual first failure is preserved as refusal evidence. |
| tests/scripts/verify-release-lifecycle.py | Post-tag lifecycle replay | ✓ VERIFIED | Present; lifecycle and post-tag endpoint controls pass. |
| tests/data/release-api/v030-draft-association-restoration.json | Same-draft tag restoration case | ✓ VERIFIED | Present; restoration and refusal controls pass. |
| docs/release.md | Operator release/host contract instructions | ✓ VERIFIED | Present; required phrases and scoped claims pass. |
| tests/CMakeLists.txt | Windows-safe immutable readback test path | ✓ VERIFIED | D135 derives a repository-relative Git path from the configured phase root while preserving revision, tag, result contract, label and timeout. |
| .gitattributes | Exact helper bytes across Windows checkout | ✓ VERIFIED | D135 pins only the byte-checked published-asset helper to LF; the APU unpinned EOL negative remains outside the rule. |

### Key Link Verification

The link-query utility mechanically verified four direct links. The other source labels include function names or runtime facts instead of file paths, so the utility cannot resolve them; I traced those paths in source and the captured workflow/API evidence. The one partial link shares the D-28 PR B gap above.

| From | To | Via | Status | Details |
|---|---|---|---|---|
| release-rehearsal workflow | verify-workflow-policy.py and ci-timeouts.json | Trusted full-history judge | ✓ WIRED | Both machine-verified and run by the suite. |
| state_apply | state_raw_to_host | One infallible conversion after whole-state validation | ✓ WIRED | Calls are present in source; state mutant/refusal tests pass. |
| verify-state-mutants.py | test_state_codec | Build/run mutated core against refusal case | ✓ WIRED | Machine-verified; all state controls pass. |
| verify-support-ledger.py | render_v3_ledger | Version dispatch from validated claims | ✓ WIRED | Generator source and 107-case ledger test pass. |
| verify-version-window.py | support-claims-v0.3.json | Managed-input digest in frozen window | ✓ WIRED | The four-input inactive window check passes at this candidate. |
| release.yml candidate | verify-release-source-proof.py | Trusted checker binds rehearsal to PR head and merge time | ✓ WIRED | Source call and captured pre-tag run evidence agree. |
| release lifecycle nightly-gate | verify-release-source-proof.py | Same PR-head and attempt-time binding | ✓ WIRED | Source call is present; full release controls pass. |
| version-pr-gate.yml | verify-version-window.py | Trusted checker judges the PR tree | ✓ WIRED | Machine-verified and current tracked window is inactive. |
| ci.yml perf-gate | release candidate fuzz | Run/attempt artifact upload and download | ✓ WIRED | Names match in both workflows; actual S perf receipt validates. |
| release candidate fuzz | release-evidence-lifecycle.sh | Downloaded exact-run perf receipt | ✓ WIRED | Candidate verifies the receipt before use; actual receipt binds S. |
| preflight synthetic tree | version PR content | Same render, pins, row and links replayed at H | ✓ WIRED | Actual #133 operational closure and refreshed preflight are recorded in phase 19-07. |
| host-contract CMake fragment | doc-link and changelog checkers | Revision-pinned registration | ✓ WIRED | CMake registers both checkers and their omission controls. |
| version-window record at W | R1 and CI at H | Digest and release window | ✓ WIRED | Actual R1/H/W capture sequence and window check are present. |
| published source/tag S | R2 at W | Exact-tree rehearsal binding | ✓ WIRED | S tree equals W tree; actual R2 and gate W evidence agree. |
| actual release notes body | tagged S changelog/support text | Adoption checker and tag-pinned ledger link | ✓ WIRED | Actual recovery evidence and unchanged adoption checker validate the published copy. |
| retry workflow G | product source S | Explicit dispatch and raw receipts/readback | ✓ WIRED | Current readback distinguishes G from S and validates both. |
| corrective PR G | 19-07 publication/readback continuation | Same draft, sole retry and readback | PARTIAL | Retry and readback are complete; PR B's guarded close and boundary handoff remain pending. |
| v03_readback CTest | verify-v03-dispositions.py immutable Source.read path | Repository-relative Git path derived from PROJECT_SOURCE_DIR and configured phase root | ✓ WIRED | D135 keeps --rev, --tag, exit/output, label and timeout intact; local affected CTest passes. |
| Exact LF attribute for published-asset helper | Recovery test byte comparison against immutable Git blob | Root-anchored one-file EOL rule | ✓ WIRED | The helper and byte guard are unchanged; forced-autocrlf baseline/fixed controls and local recovery tests pass. |
| C/C++ installed-consumer controls | tests/scripts/verify-v02-consumers.py | Existing static self-test and pause hook | ✓ WIRED | Both full consumer CTests execute D136's marker regression and existing interruption checks; both passed in the 25-test local run. |

### Data-Flow Trace

| Artifact | Value | Source | Produces real evidence | Status |
|---|---|---|---|---|
| docs/support/v0.3.0.md | Scoped claims and support ledger | Validated managed JSON, evidence registry and tag-source blobs | Yes; generator and tag/blob checks pass | ✓ FLOWING |
| release-receipt.json and platform receipts | Source, platform, corpus, fuzz and performance facts | Exact-S workflow jobs and downloaded same-source artifacts | Yes; actual run/job capture and receipt fields bind to S | ✓ FLOWING |
| 19-release-readback.json | Release identity and published asset inventory | Actual retry G, raw receipt, sourced pre-publish artifact and published API assets | Yes; IDs, names and digests reconcile for all 22 assets | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command or evidence | Result | Status |
|---|---|---|---|
| Full core/player qualification of unchanged implementation | Captured qualification at HEAD 17920163182d4af453c3255b20913be0c08a9e54 | 1,707 executed tests; zero failure/skip; installed/player/package checks pass; implementation bytes are unchanged by D135 | ✓ PASS |
| D135 Windows readback wiring and checkout representation | Captured configure/build/install and focused CTest at e46023c53bdff9e7ac44fcfb33a9e237ceec0430 | 23 affected readback, recovery, EOL-negative, contract and installed tests passed; no skips | ✓ PASS |
| D136 consumer marker publication and regression | Captured configure/build/install and affected CTest at e292db8c651e6f297ba6eb77049d2ca6f021304f | 25 affected tests passed with zero skips; C and C++ consumer controls include the exact marker regression and real interruption checks | ✓ PASS |
| Committed readback reflects actual publication | verify-v03-dispositions.py --check-readback at candidate with tag v0.3.0 | v03-readback pass, 22 assets | ✓ PASS |
| Scoped claims and ledger are bound to S | verify-support-ledger.py --check-claims and --check-ledger at S | 9 claims/10 non-claims; 107 static cases, 132 source inputs | ✓ PASS |
| Version window is closed after release | verify-version-window.py --check-tracked | Inactive at exact candidate; four managed inputs checked | ✓ PASS |
| D-134 malformed inventory/schema controls refuse bad input | verify-published-release-assets.py --self-test | Five positives; 18 recovery refusals; six schema refusals | ✓ PASS |
| Tag/release and asset inventory remain unchanged in latest saved capture | Read-only API capture at 2026-10-31T15:13:37Z | Main G and tag S match; all 22 assets unchanged; zero open PRs/issues | ✓ PASS |

No full suite was rerun. The unchanged implementation is covered by the prior complete run; D135 is covered by its focused e460 run and hosted native Windows checks, and D136 by the focused e292 run. No native Linux sanitizer or other exact-head protected result is claimed for D136. No live release mutation was performed.

### Probe Execution

No documented probe path or conventional scripts/*/tests/probe-*.sh probe exists for this phase.

### Requirements Coverage

| Requirement | Source plan | Description | Status | Evidence |
|---|---|---|---|---|
| REL-01 | Plans 19-01 through 19-08 | Publish v0.3.0 from the exact tag, scope claims, and bind/reconcile receipts | ✓ SATISFIED | Roadmap criteria 1-3 pass; release/readback source S and all 22 assets reconcile. PR B remains a separate phase-boundary gap. |

No additional Phase 19 requirement is mapped in REQUIREMENTS.md; no orphaned requirement was found. No later milestone phase covers the remaining PR B boundary step, so it is not deferred.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|---|---:|---|---|---|
| None | — | No user-visible stub, unresolved debt marker or placeholder output found | — | Raw grep hits were normal mktemp X templates and explicit test-fixture placeholders. |
| 19-VALIDATION.md | 7, 101 | Validation status metadata | Resolved | Frontmatter now says nyquist_compliant: true and matches the checked closure item. |

### Human Verification Required

None. This is a release/infrastructure phase with no visual or hardware claim to validate manually. Hardware qualification, physical DMG observations, signing and notarization are explicitly not claimed. The remaining PR B item is an automated remote gate and guarded merge, listed as a gap above.

### Gaps Summary

The release outcome itself meets all three roadmap success criteria: exact-tag rehearsal, appropriately scoped support claims, and source-bound published receipts/readback. The bounded D130-D136 post-tag exceptions are documented above and preserve the tag and product tree. PR137 remains open at older source 6c99ff0b. D135's native Windows checks passed at its then-current head, while D136's local marker fix passes; fresh exact-head Windows, Linux sanitizer and all required protected CI for 87520382 remain pending. The old failure runs are preserved and triaged, not reused as qualification. The guarded squash, actual main boundary and owner-workspace handoff remain pending. No user decision is needed; the parent agent owns the next operational step and must not claim future CI or merge completion.

---

_Verified: 2026-10-31T17:16:01Z_
_Verifier: the agent (gsd-verifier)_
