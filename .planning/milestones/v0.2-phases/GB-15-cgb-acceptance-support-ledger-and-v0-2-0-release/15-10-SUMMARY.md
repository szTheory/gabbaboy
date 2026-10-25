---
phase: 15-cgb-acceptance-support-ledger-and-v0-2-0-release
plan: "10"
subsystem: release
tags:
  - protected-merge
  - hosted-rehearsal
  - exact-tag-release
  - published-readback
requires:
  - phase: "Phase 15 Plan 09"
    provides:
      - "release.yml exact-tag evidence producers, eleven v02 contracts, verify-v02-delivery.py and the gate self-test"
provides:
  - "Phase 15 merged through protected PR #72 at exact head 6b83695 with required-native, fixture-repro and preview-package-smoke green"
  - "v0.2.0 published from tag source ab301aa with 22 assets, independently read back against live GitHub state"
  - "A documented non-publishing hosted rehearsal (release-rehearsal.yml) of the exact-tag producers and the aggregate evidence gate"
  - "15-DELIVERY.md and two live-checked receipts: 15-delivery-receipt-phase-pr.json and 15-delivery-receipt.json"
affects:
  - "Phase 15 verification (/gsd-verify-work 15); no later phase or milestone started"
actuals:
  tokens: 14700
  tasks: 2
  commits: 14
commits: 14
plan_head_before: 1e4f2d3a6cd1ac091632547c40580f61bfd45888
plan_head_after: 9ab8303b876aa9ca3a1f188ebbeb447727c50d37
tech-stack:
  added: []
  patterns:
    - "A pre-tag hosted rehearsal runs the tagged-source producers and the release gate's owner validators on a rehearsal/** branch with a read-only token and a runner-local tag"
    - "Control-plane verifiers for tagged data come from the workflow commit, not the tag, so a defect in a tagged verifier cannot burn a release"
key-files:
  created:
    - .github/workflows/release-rehearsal.yml
    - .planning/phases/GB-15-cgb-acceptance-support-ledger-and-v0-2-0-release/15-DELIVERY.md
    - .planning/phases/GB-15-cgb-acceptance-support-ledger-and-v0-2-0-release/15-delivery-receipt.json
    - .planning/phases/GB-15-cgb-acceptance-support-ledger-and-v0-2-0-release/15-delivery-receipt-phase-pr.json
  modified:
    - .gitattributes
    - .github/workflows/ci.yml
    - .github/workflows/preview.yml
    - .github/workflows/release.yml
    - cmake/RunInstalledConsumer.cmake
    - tests/CMakeLists.txt
    - tests/scripts/verify-v02-consumers.py
    - tests/scripts/verify-v02-performance.py
    - tests/scripts/verify-v02-fuzz.py
    - tests/scripts/verify-v02-delivery.py
    - tests/scripts/verify-v02-source-archive.py
    - tests/scripts/verify-release-candidate.sh
    - docs/release.md
    - docs/support/v0.2.0.md
    - docs/cgb-corpus.md
key-decisions:
  - "Merge the version PR only after the rehearsal was green on its exact tree; the rehearsal was extended until it ran every evidence producer and the owner-validator gate on real output."
  - "Resume the failed first release run through the existing retry path on the same unpublished draft, tag, source and release id; nothing was replaced, deleted or re-tagged."
  - "Run the workflow commit's copies of the release-candidate control-plane verifiers over tagged data."
  - "Keep two receipts (phase-pr and published) because each stage's checker requires its own stage field."
requirements-completed:
  - CGB-11
  - SHIP-09
  - SHIP-10
  - SHIP-11
coverage:
  - id: D1
    description: "The Phase 15 PR merged under strict, admin-enforced protection at the exact reviewed and tested head with the three required checks successful from the GitHub Actions app, and an independent live read confirms the merge, head, checks and workflow attempts; wrong head, stale attempt and narrowed required checks are each rejected."
    requirement: CGB-11
    human_judgment: false
    verification:
      - kind: integration
        ref: "python3 -I tests/scripts/verify-v02-delivery.py --stage phase-pr --receipt .planning/phases/GB-15-cgb-acceptance-support-ledger-and-v0-2-0-release/15-delivery-receipt-phase-pr.json"
        status: pass
      - kind: integration
        ref: "python3 -I tests/scripts/verify-v02-delivery.py --self-test"
        status: pass
  - id: D2
    description: "The v02 contracts hold on hosted Linux, macOS, Windows, sanitizer and CMake-floor jobs at the merged head; the full local inventory of 1144 cases passes on the final tree."
    requirement: CGB-11
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest --preset phase1 --output-on-failure --no-tests=error"
        status: pass
      - kind: e2e
        ref: "GitHub ci workflow run 39385131364 on head 6b83695 (required-native success)"
        status: pass
  - id: D3
    description: "The exact-tag producers (corpus and schema-2 sidecar, Clang 18 libFuzzer campaign, paired performance, relocated consumers, source archive) and the release gate's owner-validator aggregate ran hosted before tagging in a non-publishing rehearsal on the version PR tree, and found three defects that were fixed before and after the tag."
    requirement: SHIP-11
    human_judgment: false
    verification:
      - kind: e2e
        ref: "GitHub release-rehearsal workflow run 39396554673 on head b53d82e (five jobs success)"
        status: pass
      - kind: integration
        ref: "bash .github/scripts/verify-release-gates.sh --self-test"
        status: pass
  - id: D4
    description: "v0.2.0 is published from the tag source after the bounded final gate; the live release, tag, 22 assets and a fresh download agree with the receipt, and altered-digest, other-tag and shared-directory controls are rejected through the production entry point."
    requirement: SHIP-09
    human_judgment: false
    verification:
      - kind: integration
        ref: "python3 -I tests/scripts/verify-v02-delivery.py --stage published --receipt .planning/phases/GB-15-cgb-acceptance-support-ledger-and-v0-2-0-release/15-delivery-receipt.json --published-dir PUBLISHED_FINAL_DIR --validation-dir EARLIER_DRAFT_DIR"
        status: pass
      - kind: e2e
        ref: "GitHub release-please workflow run 39406047351 attempt 1 (all jobs success, release published)"
        status: pass
  - id: D5
    description: "The published release notes carry the exact version, the absence sentence, the unsigned and not-notarized limit and the exact-version ledger link, and the downloaded product package is fixture-free in its shipped layout."
    requirement: SHIP-10
    human_judgment: false
    verification:
      - kind: integration
        ref: "python3 -I tests/scripts/verify-v02-adoption.py --release-notes LIVE_RELEASE_BODY"
        status: pass
      - kind: integration
        ref: "python3 -I tests/scripts/verify-v02-source-archive.py --self-test"
        status: pass
duration: "about 9 hours elapsed, dominated by hosted CI waits"
completed: "2026-10-20"
status: complete
---

# Phase 15 Plan 10: Protected Delivery and v0.2.0 Publication Summary

**Phase 15 merged through protected PR #72, and v0.2.0 was published from tag source `ab301aa` with 22 assets after a pre-tag hosted rehearsal and one resumed release run; the live release is independently read back.**

## Accomplishments

- **Protected merge (Task 1).** PR #72 was reviewed internally, squash-merged at exact head `6b83695` with strict, admin-enforced required checks `required-native`, `fixture-repro` and `preview-package-smoke` successful from the GitHub Actions app. `15-delivery-receipt-phase-pr.json` is read back live (`--stage phase-pr`: PASS).
- **Hosted compatibility.** Eight defects in the 15-09 contracts and workflow wiring surfaced only on hosted runners (Windows CRLF digests, shallow history, sanitizer consumer link and budget, Windows consumer configuration, Windows lock liveness, WSL `bash`, `GITHUB_SHA` override, Clang 18 runner) and were fixed before tagging.
- **Pre-tag rehearsal.** `release-rehearsal.yml` ran the exact-tag producers and the aggregate `--check-v02-evidence` gate hosted without publishing. Its aggregate job found that `verify-v02-delivery.py` rejected the real fuzz receipt (#73).
- **Publication (Task 2).** #70 was merged only after the rehearsal was green on its exact tree. The first release run created the tag and draft, then failed at the tagged product-package check; #74 fixed the checker and moved the control-plane verifiers to the workflow commit, and a retry of the same draft produced all jobs and published v0.2.0 (run `39406047351`).
- **Readback.** `15-delivery-receipt.json` (`--stage published`) matches the live release, tag, all 22 assets and a fresh download; altered digest, other tag and a shared validation directory are rejected.

## Task Commits

1. **Task 1 (tracer): protected Phase 15 merge** - phase-branch commits `e96a6ad`, `ce4e813`, `14cf208`, `097d148`, `a49a90a`, `0c757ab`, `ed62123`, `8091dfd`, `6b83695`; squash merge `04fe3c6` (#72)
2. **Task 2: version PR, tag, publication** - fix PRs `4b092a9` (#73) and `08e7309` (#74); version merge and tag source `ab301aa` (#70)
3. **Bookkeeping** - `9ab8303` merge of main into the phase branch; delivery record, receipts, summary and state commits follow it

`commits: 14` is measured with `git rev-list --count 1e4f2d3..9ab8303` and includes the three squash merges, the version merge and the main merge; the recorded `plan_head_after` is the head the count was taken at.

## Verification Evidence

- Local: full `ctest --preset phase1` (1144 cases) passes on the final tree; `python3 -I tests/scripts/verify-v02-delivery.py --self-test`: 4 positives, 37 rejected controls, 2 real-owner rejections; `bash .github/scripts/verify-release-gates.sh --self-test`, `bash tests/scripts/verify-release-candidate.sh --self-test` and `python3 -I tests/scripts/verify-v02-source-archive.py --self-test` pass.
- Hosted, exact head `6b83695`: `ci` run `39385131364` (every lane success, `required-native` success), `fixture-repro` run `39385131440`, `preview-package-smoke` run `39385131354` attempt 2 (attempt 1 failed on its 30-minute wait; recorded as superseded).
- Hosted rehearsal on the version PR tree `b53d82e`: `release-rehearsal` run `39396554673`, five jobs success.
- Hosted release: first run `39400383894` (failed, recorded), retry run `39406047351` attempt 1, all jobs success, release published `2026-10-20T10:25:34Z`.
- Live readback: `--stage phase-pr` PASS, `--stage published` PASS; fresh download of 22 assets matches `SHA256SUMS`; live notes pass `verify-v02-adoption.py --release-notes`; fresh GitHub tag archive matches `source-archive-receipt.json`.
- Negative controls through the production entry point on the live receipts: wrong PR head (`pr-mismatch`), stale attempt (`runs-mismatch`), narrowed required checks (`receipt-malformed`), altered asset digest (`readback-mismatch`), other tag (`publication-mismatch`), validation directory shared with the final download (`readback-mismatch`).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] v0.2 contracts failed on hosted Windows, sanitizer and shallow checkouts**
- **Found during:** Task 1 (first push of the phase branch)
- **Issue:** CRLF changed digest-bound text on Windows; shallow clones lacked the v0.1.0 baseline; the sanitizer-built package could not be linked by consumers and exceeded waits; Windows consumers used the wrong configuration; Windows stale-lock detection used `os.kill(pid, 0)`; `bash` resolved to WSL.
- **Fix:** path-pinned LF in `.gitattributes`, full-history checkouts, sanitizer link options and scaled waits, installed-configuration build, kernel liveness probe, Git bash launch; ledger snapshot refreshed twice.
- **Files modified:** `.gitattributes`, `.github/workflows/ci.yml`, `cmake/RunInstalledConsumer.cmake`, `tests/CMakeLists.txt`, `tests/scripts/verify-v02-consumers.py`, `tests/scripts/verify-v02-performance.py`, `docs/support/v0.2.0.md`, `docs/cgb-corpus.md`
- **Commits:** `e96a6ad`, `ce4e813`, `14cf208`, `a49a90a`, `0c757ab`

**2. [Rule 1 - Bug] Fuzz producer identity depended on an ignored `GITHUB_SHA` override; the fuzz job needed Clang 18**
- **Found during:** pre-tag hosted rehearsal
- **Fix:** explicit `GBB_SOURCE_SHA` (unit-controlled), fuzz job on `ubuntu-24.04`.
- **Files modified:** `tests/scripts/verify-v02-fuzz.py`, `.github/workflows/release.yml`
- **Commits:** `ed62123`, `8091dfd`

**3. [Rule 1 - Bug] Delivery checker rejected the real fuzz receipt**
- **Found during:** aggregate rehearsal before merging the version PR
- **Fix:** accept the producer's decimal `run_id` string; fixture and a placeholder control updated; macOS preview wait lengthened to 45 minutes.
- **Files modified:** `tests/scripts/verify-v02-delivery.py`, `.github/workflows/preview.yml`, `.github/workflows/release-rehearsal.yml`
- **Commit:** `4b092a9` (#73)

**4. [Rule 1 - Bug] Tagged product-package check rejected the shipped package layout**
- **Found during:** first release run (the rehearsal had not run this step)
- **Fix:** inspect the unwrapped layout, rebuild the self-test package in the shipped layout with a rejecting wrapped control, run the workflow commit's control-plane verifiers over tagged data, then resume the same draft.
- **Files modified:** `tests/scripts/verify-v02-source-archive.py`, `tests/scripts/verify-release-candidate.sh`, `.github/workflows/release.yml`, `.github/workflows/release-rehearsal.yml`
- **Commit:** `08e7309` (#74)

**5. [Rule 2 - Missing critical functionality] The version PR body lacked the required release statements**
- **Found during:** pre-merge check of PR #70
- **Fix:** the required adoption statements were added to the version PR body (not its head), so the draft body carried them and passed `--release-notes`; the PR body was re-applied after each release-please refresh.

**6. [Scope] Added files beyond `files_modified`**
- `15-delivery-receipt-phase-pr.json` (each stage's checker requires its own stage field) and `.github/workflows/release-rehearsal.yml`, plus the fix files above.

**Total deviations:** 6. Impact: the tag was created and its first release run failed once at a control-plane verifier; no release was published before every gate passed, no asset was replaced and no tag was moved.

## Known Stubs

None.

## Threat Flags

| Flag | File | Description |
|------|------|-------------|
| threat_flag: ci-trigger | .github/workflows/release-rehearsal.yml | Push-triggered workflow on `rehearsal/**`; read-only token, no secrets, no release or upload, runner-local tag only |

## Issues Encountered

- Hosted jobs: the ASan lane takes about 35 minutes; `preview-package-smoke` attempt 1 timed out on its wait (attempt 2 passed; wait lengthened).
- Release-please opened #75 `release 0.2.1` after the follow-up fixes; it is open and intentionally not merged.
- Not rehearsable without a real draft and exercised only in the live run: draft-bound download and attach, macOS and Windows candidate archives, the final gate and publish.
- Physical hardware and perceptual limits are unchanged: no CGB game-level evidence, no physical device observation, unsigned and not notarized.

## Next

Phase 15 execution stops here; `workflow.auto_advance` and `workflow._auto_chain_active` remain `false` and no next milestone was started. Next command: `/gsd-verify-work 15`.

## Self-Check: PASSED
