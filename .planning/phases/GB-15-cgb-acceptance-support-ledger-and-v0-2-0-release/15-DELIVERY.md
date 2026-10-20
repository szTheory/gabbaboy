# Phase 15 Delivery Record

Machine-readable counterparts: `15-delivery-receipt-phase-pr.json` (stage `phase-pr`) and `15-delivery-receipt.json` (stage `published`). Both are read back live with `tests/scripts/verify-v02-delivery.py --stage ...`; a local self-test is not accepted as a substitute.

## Outcome

| Item | Evidence |
|---|---|
| Phase 15 pull request | #72, squash-merged as `04fe3c61188851db5d68488fce731061ee3dedb3` at exact head `6b83695aeec9926162814521beedc53bf01147c6` |
| Required checks at that head | `required-native`, `fixture-repro`, `preview-package-smoke`, each `success` from the GitHub Actions app, strict and admin-enforced protection, no bypass |
| Version pull request | #70 `chore(main): release 0.2.0`, squash-merged as `ab301aa69b1f085050fd66bf7b1378863a0821f2` at exact head `b53d82e2667980a21006cea8b521521df1825a04`, required checks `success` (approved with the supported run-approval API after `action_required`) |
| Tag and source | `v0.2.0` resolves to `ab301aa69b1f085050fd66bf7b1378863a0821f2` |
| Release | id `418219852`, published `2026-10-20T10:25:34Z`, `draft: false`, 22 assets, unsigned and not notarized, https://github.com/szTheory/gabbaboy/releases/tag/v0.2.0 |
| Publishing run | `release-please` workflow run `39406047351` attempt 1 (`workflow_dispatch` retry of the same draft, workflow commit `08e7309`); every job `success`, including the corpus, fuzz, performance, macOS, Windows, platform-manifest and final-gate-and-publish jobs |
| Independent readback | `--stage published` over a fresh download of all 22 published assets (sizes and SHA-256 equal live API digests and `SHA256SUMS`), the live tag, the live release, and a fresh GitHub tag archive checked by `verify-v02-source-archive.py --check-receipt` |
| Published notes | `verify-v02-adoption.py --release-notes` over the live release body: 8 checks pass |

## Qualified evidence hashes (published assets)

| Asset | SHA-256 |
|---|---|
| `cgb-corpus-receipt.json` | `c9fbb22c37dc3f273cd94264d24cb29ea0493a496b9c1e8b001a53972dbc6bfa` |
| `support-ledger.json` | `335a5be3d4a8bd5493e3d69337b17a1c109e6a8382dd804b386926d6ffbf92ca` |
| `v02-performance-receipt.json` | `c59d052bc4e86ae8003f942a8460656ceadcbf41946c0c5b6de6b4c9506795d3` |
| `v02-fuzz-receipt.json` | `7200b34a09ecb941850b39d5f1fbc96a535cebfbb9d7545a99b5c06ceb773ecb` |
| `source-archive-receipt.json` | `6bd05b89fad60a9469a8f39aaf3380d3f482475bc7b57bd952434cb90a3c3266` |
| `v02-consumer-receipt.json` | `c72a5dd16fa6f95c45ca9075a6a72e63037f789fe6b3e4853feaf1d59d3c1efb` |
| `gabbaboy-core-linux-x64.tar.gz` | `fb5bcc5d015d06351520f57c1b7e89010cb9a066ec39a3d87efbed589950392a` |
| `gabbaboy-core-macos-arm64.tar.gz` | `f02c54ef4a82b3a7e6efd7a2c7845f9101ff94cd20f774582b72525e454be926` |
| `gabbaboy-core-windows-x64.tar.gz` | `ee386086f0084649f02920f8cd2ff4b85ba8be39c239ae583a88337a6da2d446` |
| `gabbaboy-preview-macos-arm64.tar.gz` | `03bc445aedcefc5b6d5afa0b0b47cd2922be3dc50279c0285f888ff1e7c233da` |

The full inventory with sizes is in `15-delivery-receipt.json`.

## What the protected-merge stage found (Phase 15 PR #72)

Pushing the phase branch showed the new v0.2 contracts failing on hosted Windows, sanitizer and shallow checkouts. All were fixed on the branch before the merge, and the merge head's checks are green:

- Windows checkouts rewrote digest-bound text to CRLF: LF is pinned by path in `.gitattributes` (a global rule would break the APU source-eol negative control, which needs an unpinned file).
- Shallow clones lacked the v0.1.0 baseline commit and tag: the ctest jobs fetch full history.
- The sanitizer-built package needs the sanitizer runtime at consumer link time, and its waits and CTest budget scale; the Windows consumer build uses the installed package configuration; stale-lock liveness uses the Windows kernel because `os.kill(pid, 0)` is not a liveness probe on Windows; the performance producer is launched through Git bash because `bash` resolves to the WSL launcher.
- `tests/CMakeLists.txt` is a covered ledger input, so the ledger snapshot was refreshed twice from fresh nonce-bound corpus receipts (107/107 cases, 25 guest passes, 82 matched expected failures). No support claim changed.
- Attempt 1 of `preview-package-smoke` failed: its macOS job waits at most 30 minutes for the whole exact-head CI run, and the ASan lane takes about 35 minutes on the hosted runner. Attempt 2 re-ran the failed jobs after CI completed and passed; the receipt lists attempt 2 and records attempt 1 as superseded. The wait was lengthened to the other waits' 45 minutes in #73.

## Pre-tag hosted rehearsal (non-publishing)

`release.yml` runs only after release-please creates the tag, and a defect in tagged source cannot be repaired afterwards. `.github/workflows/release-rehearsal.yml` (push to `rehearsal/**`; read-only token; a runner-local tag; no release, upload or publish) ran the exact-tag producers hosted before the tag existed and found three defects that would have failed the real release:

1. A step-level `GITHUB_SHA` override is ignored by the runner, so the fuzz receipt would have recorded main's commit. The producer and `release.yml` now use an explicit `GBB_SOURCE_SHA`, with a unit control that it outranks `GITHUB_SHA`.
2. Clang 18 is not installed on `ubuntu-22.04`; the fuzz job runs on `ubuntu-24.04` like the CI sanitizer lane.
3. `verify-v02-delivery.py` required an integer fuzz `run_id`, but the producer records the decimal `GITHUB_RUN_ID` string. Found by an aggregate job that runs all six evidence producers and then the release gate's `--check-v02-evidence` over their real output (#73).

## The first release run and the recovery

The version PR was merged only after the rehearsal was green on its exact tree. The first release run (`39400383894`, attempt 1) created the tag and unpublished draft, built and attached the Linux core archive, then failed in `verify-release-candidate.sh --verify`: the tagged product-package check required one wrapper directory, but the shipped package is `include lib bin share` at its top level. The self-tests built a synthetic wrapped package, so no earlier check could see it. The rehearsal had not run that step.

Recovery followed the recorded rule for an unpublished draft: same tag, same source, same release id, byte-identical attachments only.

- #74 corrected the checker and its self-tests (a wrapped package is now a rejected control), and made the candidate job run the workflow commit's copies of `verify-release-candidate.sh`, `verify-v02-source-archive.py` and `VerifyReleaseReceipt.cmake` over the tagged data so a tagged control-plane verifier can no longer block a release.
- Before retrying, the fixed checker was run against the real draft asset and `--verify` and `--verify-final` were replayed locally over the draft's real attachments and the real GitHub tag archive: both passed.
- The retry reused the six already attached assets unchanged (the deterministic archive, notices, receipts compared byte-identical) and produced the rest.

## Remaining limits

- The v0.2.0 evidence is the software-model corpus (107 required cases; 25 guest passes and 82 matched expected failures), a bounded fuzz campaign, paired performance and relocated-consumer receipts. No CGB game-level evidence exists and no physical hardware observation exists. The macOS player is unsigned and not notarized.
- Release-please opened #75 `release 0.2.1` from the follow-up fixes. It is open and intentionally not merged by this plan.
- The rehearsal workflow stays in the repository as a documented pre-tag tool; it does not exercise the draft-bound download, attach, final-gate or publish steps.
- Open issues: none. Open pull requests at the end of this plan: #75 only.

## Phase stop

Phase 15 stops here. `workflow.auto_advance` and `workflow._auto_chain_active` remain `false`, no next milestone was started, and the next route is `/gsd-verify-work 15`.
