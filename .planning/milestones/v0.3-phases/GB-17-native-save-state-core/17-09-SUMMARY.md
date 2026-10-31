---
phase: GB-17-native-save-state-core
plan: "09"
subsystem: testing
tags: [release-evidence, lifecycle-replay, github-api-shapes, release-please, workflow-policy, CTest]

requires:
  - phase: GB-17-native-save-state-core/17-07
    provides: "The triggered advisory performance receipt semantics that the replay carries through attach, manifest and final receipt"
  - phase: GB-17-native-save-state-core/17-08
    provides: "Generated disclosure and the version-window gate; this plan owns the lifecycle-replay part of RM-028"
provides:
  - "The attach, platform-manifest, final-gate and publish steps of release.yml are modes of one production script that the workflow and a local replay both execute"
  - "A bounded gh stand-in and download stand-in replay a full first attempt and a retry from a non-git workspace with GH_REPO explicit, ending in one recorded publish decision and no live mutation"
  - "Sanitized, digest-bound captures of real run, job, artifact, check-run, pull-request, release and asset responses drive the production source-proof, asset-set, recovery and final-receipt checks"
  - "Retry validates the attached evidence independently before any regenerated copy is replaced, and the workflow policy requires that order"
affects: [GB-17, release-evidence, workflow-policy, GB-17-10, GB-17-11]

actuals:
  tokens: 75975
  tasks: 3
  commits: 5

tech-stack:
  added: []
  patterns:
    - "A step body moved verbatim into a script is judged by the workflow policy as if it were still inline, with mutants that edit the script"
    - "A replacement transport serves recorded shapes, pins their key sets, and refuses by exit code 97 whatever it was not told about"
    - "A control is credited only when the run exited non-zero with the intended diagnostic, and an ordering mutant is credited only when it behaves differently from the real code"

key-files:
  created:
    - .github/scripts/release-evidence-lifecycle.sh
    - tests/scripts/verify-release-lifecycle.py
    - tests/data/release-api/captured.json
    - tests/data/release-api/SOURCES.md
  modified:
    - .github/workflows/release.yml
    - .github/scripts/verify-release-gates.sh
    - .github/scripts/verify-release-source-proof.py
    - .github/scripts/verify-workflow-policy.py
    - .github/scripts/verify-test-inventory.sh
    - cmake/ExpectedTests.cmake
    - tests/CMakeLists.txt
    - tests/expected-tests.txt
    - .gitattributes
    - docs/release.md

key-decisions:
  - "The replay runs the production lifecycle script and gates unchanged. Only two transports are replaced: a gh executable that serves captured shapes, and the archive download helper for the one expected URL. The owner validators of the corpus, fuzz, performance and archive families are the delivery fixture's stub owners; the delivery self-test remains the place the real owners run."
  - "The lifecycle replay is POSIX-only (bash, jq, a gh shim) because the lifecycle runs on ubuntu-22.04 only; the two tests are registered under if(NOT WIN32) and added to the Windows inventory filter."
  - "The independent retry check reads only the attachments and a fresh live asset list. It binds identity, the sidecar to the attached corpus receipt bytes, each digest GitHub reports and the allowed inventory; semantic owner validation of the same bytes stays downstream in the platform-manifest step."
  - "A refused retry leaves the regenerated evidence untouched, and that is the observable the ordering control uses."

patterns-established:
  - "Step bodies extracted into BEGIN/END regions of a script that the policy expands into the calling step"
  - "Snapshot stages of the stub state (attached, manifested, finalized) let each control start where it applies"

requirements-completed: []

coverage:
  - id: RM-028-lifecycle-replay
    description: "The production attach, manifest, final-gate, publish-decision and retry steps run from the extracted lifecycle script that release.yml calls, in a non-git attacher workspace with GH_REPO explicit and no repository fallback, against a bounded transport that records the publish command as a decision only. A first attempt uploads exactly the four evidence assets, the manifest and the two final receipts and records one decision; a retry with different regenerated sidecars reuses the identical attached bytes, uploads nothing and records one decision."
    requirement: RM-028
    verification:
      - kind: integration
        ref: "32321eda15f05d85608c205ffa0dbe457501f8bc: ctest --test-dir build -R '^release_lifecycle_replay$' --output-on-failure --no-tests=error (passed; modes=7 publish_decisions=2 live_mutations=0 uploads=7 calls=54)"
        status: pass
      - kind: integration
        ref: "32321eda15f05d85608c205ffa0dbe457501f8bc: python3 -I tests/scripts/verify-release-lifecycle.py --self-test (controls positives=4 controls=85; wrong GH_REPO, missing GH_REPO fallback, skipped attach, removed final gate, unexpected endpoint and a non-intercepted publish command each refused with the intended diagnostic)"
        status: pass
    human_judgment: false
  - id: RM-028-captured-shapes
    description: "Sanitized, bounded, digest-bound captures of real GitHub run, job, artifact, check-run, pull-request, release and asset responses with documented endpoints, API version and transform drive the production source proof, draft asset-set check, recovery decision and final-receipt gate. Stale head, wrong App id or slug, check-run url or html_url of another repository or lookalike prefix, a missing check_suite, the old repository-only shape, altered and replaced bytes, stale identities, partial, duplicated and unknown assets, a moved tag, concurrent runs and duplicate, malformed, path-like or unterminated SHA256SUMS lines are each refused after the real shapes pass."
    requirement: RM-028
    verification:
      - kind: integration
        ref: "32321eda15f05d85608c205ffa0dbe457501f8bc: python3 -I tests/scripts/verify-release-lifecycle.py --self-test && python3 -I .github/scripts/verify-release-source-proof.py --self-test (7 captured-shape defects rejected; capture contract and sanitizer controls pass)"
        status: pass
      - kind: integration
        ref: "32321eda15f05d85608c205ffa0dbe457501f8bc: bash .github/scripts/verify-release-gates.sh --self-test (exit 0; duplicate, malformed, path-like and unterminated SHA256SUMS and the attached-evidence check controls)"
        status: pass
    human_judgment: false
  - id: RM-028-retry-order
    description: "On a retry the attached evidence is downloaded and judged independently of the regenerated copies before any copy is replaced, and only identical qualified bytes are then reused. Nine tampered or stale attachment forms are refused before reuse and before the recovery decision; a removed check lets the altered attachment reach the recovery decision; a check moved after the reuse destroys the regenerated evidence before it refuses; downstream owner, manifest and asset-set refusals precede the publish decision. The workflow policy requires the lifecycle wiring and this order."
    requirement: RM-028
    verification:
      - kind: integration
        ref: "32321eda15f05d85608c205ffa0dbe457501f8bc: python3 -I tests/scripts/verify-release-lifecycle.py --self-test (retry tamper, ordering mutant and downstream controls)"
        status: pass
      - kind: integration
        ref: "32321eda15f05d85608c205ffa0dbe457501f8bc: python3 -I .github/scripts/verify-workflow-policy.py --check && python3 -I .github/scripts/verify-workflow-policy.py --self-test (300 negative controls including 14 lifecycle mutants, 4 positive controls)"
        status: pass
    human_judgment: false
  - id: phase17-09-no-regression
    description: "The extraction, the stricter final-receipt parse and the new tests leave every existing test green, including the test inventory, test budget and summary coverage checks."
    verification:
      - kind: integration
        ref: "32321eda15f05d85608c205ffa0dbe457501f8bc: cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 -j8 --output-on-failure --no-tests=error (1488/1488 passed)"
        status: pass
    human_judgment: false

duration: 44min
completed: 2026-10-28
status: complete
plan_head_before: 246b7d430a2081ec27380e0fb63d99a312aa97f4
plan_head_after: 32321eda15f05d85608c205ffa0dbe457501f8bc
---

# Phase GB-17 Plan 09: Evidence Lifecycle Replay Summary

**The release workflow's attach, manifest, final-gate and publish steps now live in one production script that a bounded local replay executes, with real captured GitHub response shapes, a retry that judges attached evidence before reusing it, and a recorded publish decision that never reaches the network.**

## Performance

- **Duration:** about 44 minutes from the first to the last task commit (12:59 to 13:43 EDT); reading and design predated the first commit.
- **Tasks:** 3/3, plus the fail-first commit and one follow-up.
- **Commit ledger:** 5 commits measured from the persisted plan base to the final code head (one RED, three feature commits, one setup-trim follow-up).
- **Diff-size proxy:** 75,975 (303,900 changed characters divided by four, the summary actuals scale; this includes the 108,510-byte generated `captured.json`, and is not measured model-token use and not comparable to the raw plan projection of 61,000).
- **Local timings (host under load average above 20):** inside the full `-j8` run `release_lifecycle_replay` took 19.5 s and `release_lifecycle_controls` 33.6 s wall (about 65 s of CPU spread over a pool of up to 8 workers; roughly 18 s wall when run alone). Both keep the default 60 s TIMEOUT and `test_budget` passes with no new allowlist row, but the controls margin on a slow or oversubscribed hosted runner is a real risk to watch at the exact-head CI.

## Accomplishments

- **Extraction.** `.github/scripts/release-evidence-lifecycle.sh` holds six modes (`attach-evidence`, `validate-evidence`, `build-manifest`, `validate-draft`, `final-gate`, `publish-draft`) moved verbatim from `release.yml`. The workflow calls each as `bash trusted/.github/scripts/release-evidence-lifecycle.sh MODE`. The workflow policy reads each BEGIN/END region as the body of the calling step, so all 286 earlier rules and mutants still judge the exact text that runs, and 14 new lifecycle mutants judge the wiring and the retry order.
- **Replay.** `tests/scripts/verify-release-lifecycle.py` builds a judge repository from the revision's production files, a tag-checkout workspace and a non-git attacher workspace, and runs the modes with `GH_REPO` explicit. The `gh` stand-in serves only the endpoints the production code uses, applies `--jq` with the real `jq`, pins each served object to the key set of the capture, bounds bodies and lists, and refuses everything else with exit 97. `gh release edit --draft=false --verify-tag` is accepted only in that exact form and recorded as the decision.
- **Captured shapes.** `tests/data/release-api/captured.json` (108,510 bytes) holds sanitized responses for release, assets, workflow runs, a run, its jobs and artifacts, check runs, a pull request and a commit. `SOURCES.md` records endpoints, API version, the sanitization transform and the file digest. The check-run objects carry `url`, `html_url`, `check_suite` and `app` and no `repository` member; the source proof was extended to validate these real objects and reject seven reshaped forms.
- **Retry order (IN-01).** `verify-release-gates.sh --check-attached-evidence` judges the downloaded attachments against the tag, the sidecar-to-corpus binding, each digest GitHub reports and the allowed inventory. The lifecycle runs it after the downloads and before the copy that reuses the bytes and before the recovery decision. A refusal leaves the regenerated evidence untouched.
- **Production defects found and fixed by the rehearsal.** A retry after the final receipts were attached could not pass the platform-manifest asset-set check; the check now accepts the final receipts only together with the manifest and never requires them. `SHA256SUMS` was parsed into a dict, so a repeated name collapsed and a malformed line was read leniently; it is now parsed strictly before any map is built (the part of WR-03 that this plan's controls need; 17-10 rechecks it).

## Task Commits

1. **Task 1 RED: fail-first registration** — `1281c8c` (`test`). `release_lifecycle_replay` and `release_lifecycle_controls` failed with `REJECT lifecycle-missing` because the script did not exist.
2. **Task 1 GREEN: extract and replay the lifecycle** — `cf700a2` (`feat`).
3. **Task 2: captured shapes and stale, tampered and partial rejection** — `1a294dd` (`feat`).
4. **Task 3: retry validation order and final-decision refusal** — `09e8cbf` (`feat`).
5. **Follow-up: drop control setup the controls do not need** — `32321ed` (`test`). No control changed meaning.

## CLI Registry

- Production: `release-evidence-lifecycle.sh attach-evidence | validate-evidence | build-manifest | validate-draft | final-gate | publish-draft`; `verify-release-gates.sh --check-attached-evidence TAG SOURCE_SHA LIVE_ASSETS_JSON ATTACHED_ROOT`.
- Checker: `verify-release-lifecycle.py [--rev SHA] --replay | --self-test | --check-capture | --sanitize-capture RAW_DIR OUTPUT` (without `--rev`, HEAD is resolved to its commit id once and only that commit's objects are read).
- CTests: `release_lifecycle_replay`, `release_lifecycle_controls` (POSIX only).

## Verification

- `ctest --test-dir build -R '^release_lifecycle_(replay|controls)$' --output-on-failure --no-tests=error` after `cmake --preset phase1` passed 2/2.
- `python3 -I tests/scripts/verify-release-lifecycle.py --self-test` passed with `positives=4 controls=85`; `--replay` with `modes=7 publish_decisions=2 live_mutations=0 uploads=7 calls=54`; `--check-capture` with `responses=9 bytes=108510`.
- `bash .github/scripts/verify-release-gates.sh --self-test`, `python3 -I .github/scripts/verify-release-source-proof.py --self-test`, `python3 -I .github/scripts/verify-workflow-policy.py --check` (`residual_write_jobs=5`) and `--self-test` (300 negative, 4 positive controls) passed. `verify-test-inventory.sh --self-test` and `verify-v02-adoption.py --check docs` passed.
- Discriminating power: 13 mutants of the production check and the extracted script were run through the whole control suite and each was refused by a control (corpus binding, fuzz source, sidecar tag, API digest comparison, allowed inventory, performance result, repository prefix check, duplicate `SHA256SUMS` name check, manifest asset set in three forms, silent manifest overwrite). Two ordering mutants are built into the controls: a removed check reaches the recovery decision, a check moved after the reuse destroys the regenerated evidence.
- Full suite at `32321eda15f05d85608c205ffa0dbe457501f8bc`: `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 -j8 --output-on-failure --no-tests=error` passed 1488/1488 (172.6 s; the same command at `09e8cbf` passed 1488/1488 before the setup-trim follow-up). `test_budget` and `summary_coverage` (including this file, `verify-summary-coverage.py --phases-dir .planning/phases --since 16`: files=16 entries=91) pass.

## Decisions Made

- The executor kept the workflow policy's literal command checks by judging expanded bodies instead of rewriting them, because the existing tables and mutants encode security properties of the exact commands.
- Stub owners stand in for the four evidence-family validators in the replay. The advisory receipt is the triggered schema-3 advisory shape and is carried through attach, manifest and the final receipt, and a non-advisory disposition is refused, but the real performance owner runs in the delivery self-test (`actual_advisory_delivery_controls`), not here.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] A retry could not pass the platform-manifest asset-set check once final receipts were attached**
- **Found during:** Task 1, first retry replay.
- **Issue:** `build-manifest` accepted only the required set or the required set plus the manifest, so a draft that already carried `SHA256SUMS` and `release-receipt.json` from an earlier attempt could never reach the publish job's recovery decision.
- **Fix:** accept the final receipts only together with the manifest, never require them, and refuse any unknown asset; three controls cover the forms.
- **Files modified:** `.github/scripts/release-evidence-lifecycle.sh`.
- **Commit:** `cf700a2`.

**2. [Rule 1 - Bug] `SHA256SUMS` duplicates and malformed lines were not rejected**
- **Found during:** Task 2, while writing the duplicate and malformed `SHA256SUMS` controls the plan requires.
- **Issue:** `check_final_receipt` built a dict from `line.split(None, 1)`, so a repeated name collapsed and odd spacing or a path-like name was accepted.
- **Fix:** strict per-line parse (`<64 hex>  <name>`, safe name, no repeats, final newline) before any map is built, with four gate self-test controls and six replay controls. 17-10 WR-03 still owns the remaining consumers and rechecks this.
- **Files modified:** `.github/scripts/verify-release-gates.sh`.
- **Commit:** `1a294dd`.

**3. [Rule 3 - Blocking issue] The plan's file lists omit files the extraction and registration must touch**
- **Issue:** extracting the steps broke `verify-workflow-policy.py` and `verify-release-gates.sh --self-test` (both read inline step text), a new bash-bound CTest needs the Windows inventory exemption, and the captured files need LF rules.
- **Fix:** minimal policy expansion in Task 1 (the wiring and ordering rules the plan lists for Task 3 followed in Task 3); `verify-release-gates.sh` judges the workflow plus the script text; `cmake/ExpectedTests.cmake`, `.github/scripts/verify-test-inventory.sh` and `.gitattributes` updated.
- **Commits:** `1281c8c`, `cf700a2`.

**4. [Scope] `captured.json` and `SOURCES.md` landed in Task 1, not Task 2**
- The tracer needs the real shapes to serve; Task 2 added the capture contract, sanitizer controls and the production binding controls.

**5. [Diagnostic] The silent manifest comparison now names its refusal**
- `cmp -s ... || exit 1` became a message (`The attached platform manifest differs from the regenerated one and is never replaced.`) so the control can require the intended reason.

### Auth gates

None. The captures used the maintainer's existing authenticated `gh` session for read-only GET requests on a public repository.

## Known Stubs

None in production. The replay's stand-ins are the declared test transport (`gh`, the archive download helper) and the delivery fixture's stub owners.

## Deferred Verification and Limits

- The replay proves deterministic logic. It does not prove live GitHub permissions, rate limits, token scopes, hosted runner behavior or real asset upload semantics, and a throwaway live draft was not used (no remaining material API gap justified it; no credentials beyond read-only `gh api` were used).
- The preflight step "Require trusted source and all candidate jobs" (tag, version and draft lookup that sets `RELEASE_ID`) and the candidate build jobs remain inline in the workflow and are not replayed; the replay supplies `RELEASE_ID` as that step would.
- The real corpus, fuzz, performance and source-archive owner validators are not run by the replay; the delivery aggregation of the real advisory performance receipt remains covered by `verify-v02-delivery.py --self-test`.
- Hosted Linux, macOS and Windows runs of the changed checkers are pending the parent's exact-head CI; no hosted result is claimed. The lifecycle tests are not registered on Windows by design.
- WR-03 (all consumers of `SHA256SUMS`), WR-01/WR-02, IN-02 to IN-04 and the review-approval and nightly gates remain Plan 17-10; RM-027 remains a Phase 19 entry blocker; no version PR, tag, release or push was made.

## Threat Flags

| Flag | File | Description |
|------|------|-------------|
| threat_flag: ci-script-extraction | .github/scripts/release-evidence-lifecycle.sh | The attach, manifest, final-gate and publish steps now execute from a script file under `trusted/` instead of inline `run:` text. Mitigated by the policy requiring the exact call form from the trusted checkout, exactly once per mode in the expected job, with the body judged by every existing command rule and mutant. |

## Self-Check: PASSED

The five commits (`1281c8c`, `cf700a2`, `1a294dd`, `09e8cbf`, `32321ed`) are ancestors of the recorded task head and `plan_head_after` equals that head. The created files `.github/scripts/release-evidence-lifecycle.sh`, `tests/scripts/verify-release-lifecycle.py`, `tests/data/release-api/captured.json` and `tests/data/release-api/SOURCES.md` exist. The `summary_coverage` check is run against this file before it is committed.

---
*Phase: GB-17-native-save-state-core*
*Plan: 09*
*Completed: 2026-10-28*
