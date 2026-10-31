# Phase 19 post-tag failure: generated draft notes lost the reviewed disclosures

This is the first post-tag failure and the trigger for the reserved D-27/19-08 gap. It is an execution checkpoint, not a completed verification or release claim.

## Immutable and live facts

- Version PR131 was guarded-squashed at reviewed W `c4c0258bcdd65cf026e1497dd2585b634d807bd5`; actual S is `a3f3390451f9a893aa47475f15a722ada86daaa6`, merged `2026-10-31T00:09:30Z`. S has exactly the W tree and is the single child of WINDOW_BASE `9c405b01fa40e177f9efc52752d835fee5a3c7c1`.
- Real tag `v0.3.0` points to S. Do not move, delete or recreate it. No push/rerun of rehearsal/v0.3.0 is permitted after the merge.
- Existing draft release id `429606490` targets S, draft=true, prerelease=false, published_at=null; it has zero assets. Preserve its identity; do not delete/recreate or publish outside the full qualified pipeline.
- Normal release-please run `41148606886` failed. The first Linux candidate job `124379552103` failed step `Require final release notes to satisfy the v0.2 adoption contract` with `release-notes-absence-missing`; configure/build/attachment/publication were skipped. The source window active contract passed at S immediately before it.
- At the failure snapshot main S CI `41148606861` was ongoing; it subsequently completed successfully on attempt1. Independent production readers verified its exact-S performance and fuzz artifacts, including API/run/attempt and downloaded-byte digests. Fixture run `41148606906` passed. The skipped push Mac-package job supplies no binary metadata; the retry must qualify its own shipped packages. Do not relabel W receipts as S.

## Cause and reproduction

The actual draft API body contains only the generated v0.3.0 heading and Features entries. It omits the preface that was reviewed and frozen on the version PR. Tagged CHANGELOG and reviewed PR body contain the required save, host, corpus, OS, unsigned-package and performance disclosures. Release-please extracted its generated notes and discarded the prefix placed before its generated PR body. The adoption guard correctly refused the resulting API metadata.

From the clean release checkout at `build/phase19-window/task1-live/task1-live-20261030-01/checkout` (W tree exactly equals S, S fetched):

```sh
python3 -I tests/scripts/verify-v02-adoption.py --release-notes <root>/build/phase19-window/release-S/draft-notes.md --root . --repo . --rev a3f3390451f9a893aa47475f15a722ada86daaa6
# exit1: release-notes-absence-missing
python3 -I tests/scripts/verify-v02-adoption.py --release-notes <root>/build/phase19-window/task1-live/task1-live-20261030-01/evidence/body.md --root . --repo . --rev a3f3390451f9a893aa47475f15a722ada86daaa6
# exit0: 22 checks, target0.3.0
```

Use the explicit v0.3 source checkout/root/repo: this checker reads the working root version even when --rev is supplied for immutable evidence; the outer checkout is still the older guard branch and is not an appropriate root for this check.

## Evidence and next work

Ignored `build/phase19-window/release-S/` holds actual draft-release.json, draft-assets.json, draft-notes.md, failed-linux-candidate-job.json, raw/clean failed job logs, release-run.json and tag JSON. API endpoint GET `/repos/szTheory/gabbaboy/releases/429606490` returns the actual draft; GET releases/tags/v0.3.0 returned404 because this is still unpublished. Capture the exact source list endpoint and a sanitized bounded real-response fixture into tests/data/release-api/ with provenance; do not replace the historical v0.2 fixture or invent published assets.

Use only reserved19-08, within active Phase19. Classify and plan the least disruptive metadata/control-plane remedy, replay all remaining stages before retry, preserve all assertions/budgets/source bindings, and keep the actual tag/draft fixed. D27 calls for one non-releasable corrective PR on main if code is needed, plus actual response capture and retry=true. Independent planning and recheck resolved the route in19-08: one non-releasable corrective main PR carries the captured regression, procedure and strict retry readback extension before the same-draft body-only repair and one retry. Carrying those only in later PR B would bypass D27. The approved plan passed recheck after exclusive-gap routing, privacy and tag-pinned ledger-link corrections; no owner approval is pending. If a main hotfix is necessary, inspect the readback retry workflow-head versus product-source distinction before dispatch: the current v0.3 checker requires head_sha=S, unlike the legacy v0.2 readback. Preserve truthful actual API metadata and strong source proof; never substitute S for a workflow run's actual head.

Do not change core/API/state/performance/permissions or weaken any guard. Any tagged product defect or a second live post-tag failure goes to the owner, with no second gap or waiver.19-07 remains incomplete at Task3; no premature19-07 SUMMARY.19-08 dependency must use the actual operational checkpoint, not pretend19-07 completed or let its pending state deadlock the gap. After successful recovery resume19-07 publication/readback/PR B, then stop at `/gsd-verify-work 19`; no automatic next phase/milestone.
