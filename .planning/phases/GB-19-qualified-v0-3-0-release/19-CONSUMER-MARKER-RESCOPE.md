# Phase 19 bounded consumer-test marker repair

Status: approved under D-136. The owner answered “Yeah, I give you approval. Follow your recommendations.” to this concrete tested one-file repair. Its implementation and required qualification are authorized; no further scope approval is pending. D135 remains approved and implemented. This is a new exact one-file scope decision, not a general review/gap reset or another release retry.

## Problem and consequence

The D135 Windows repair passed both fresh native Windows jobs at the new PR137 head. Linux and macOS native tests and the macOS player package also passed. The PR's Linux sanitizer test shard then failed an existing installed-consumer interruption test: it sees a readiness file exist and reads it before its JSON has been written. The resulting JSONDecodeError fails the shard. It is a test synchronization race, not an emulator sanitizer finding, and the published v0.3.0 tag and22 assets are unaffected.

A fresh read-only hold capture in `build/phase19-window/posttag-recovery/consumer-marker-prep/current-hold/proof.json` confirms unchanged published release/body and all22 asset identities/digests, main G/tag S unchanged, PR137 open/unmerged, no open issue and no other open PR.

The merge stays held. Keep the red run as a failure; do not rerun unchanged source, bypass protection or treat other green jobs as proof of this missing result. Remaining current jobs can finish; their terminal outcomes must be retained and triaged before any new push.

Observed source:6c99ff0b908de282343a16a96aeebc9a176537e4. PR CI41220480730 attempt1, Linux sanitizer job124593833896, test v02_consumer_controls_c / test_interrupted_extraction_removes_partial_tree_and_retries. Logs are retained under `build/phase19-window/posttag-recovery/prb-current-failure/`. Both native Windows jobs124593812724 and124593833992 passed the repaired readback/recovery checks and APU unpinned-EOL negative; their logs are under `windows-wiring-hosted/`.

## Exact proposed change

Permit one bounded implementation and fresh independent recheck of **only tests/scripts/verify-v02-consumers.py**, on the same unmerged PR137 branch:

1. In the existing private maybe_test_pause helper, write the complete marker JSON to a unique sibling temporary, then replace the readiness name atomically. Always remove any remaining temporary.
2. Add the deterministic regression to the existing static self-test partition. It forces the empty and partial write points, requires the readiness name to stay absent, then verifies the exact complete payload and temporary cleanup. Both existing C and C++ consumer CTests execute it.

Keep both real interruption tests, their cleanup/retry/lock assertions, marker schema, signal behavior, normal receipt publication, private opt-in environment variables and all deadlines unchanged. No new target, inventory edit, floor change, timeout/job/permission/dependency change, product/API/state behavior, performance-policy change or release action. The helper is a private self-test synchronization hook; normal consumer behavior is unchanged.

## Concrete tested prototype

- Base:6c99ff0b908de282343a16a96aeebc9a176537e4.
- Isolated clean prototype:8fdc1e633435109fa9b06c3e76657369e3b72843, under `build/phase19-window/posttag-recovery/consumer-marker-prototype`.
- Exact patch: `build/phase19-window/posttag-recovery/consumer-marker-prep/consumer-marker.patch`.
- Patch SHA-256: `6f8455b70e8e3f5d988d27d8ef39ec454a03ee5b62876642e0875ee70e24870b`.
- Diagnosis and test report: `build/phase19-window/posttag-recovery/consumer-marker-prep/README.md`.
- Report SHA-256: `d9c98f9c88be11c00fde16d6cd50f85ba58c1bbab201fbfd31dd6cac1eb24e8d`.

The controlled probe invokes the actual writer and reproduces the exact empty-file JSONDecodeError on the unchanged baseline. On the prototype the final name remains absent during empty and partial writes, then its complete expected JSON is readable. The added regression rejects the exact original function for the intended assertion and accepts the prototype. Both full existing consumer CLI halves pass at the prototype's own configured/built source and installed package, including real interruption cleanup/retry and the new regression. Commands, source, exit codes and log hashes are pinned in commands.json/proof.json. This local prototype is not a native Linux sanitizer result. The local sanitizer configure correctly refuses this macOS host under the existing Linux-only guard; no bypass or sanitizer pass is claimed.

An independent read-only diagnosis/design check confirms the readiness race and recommends this one-file scope. No assertion/deadline weakening was found. At the proposal snapshot the approved PR source was unchanged and the prototype was unapplied. D136 now authorizes the exact patch on the same branch; fresh qualification remains required before a push/merge.

## Required continuation after approval

Record the owner decision without resetting prior rounds. Apply only the pinned patch to the same PR137 branch and commit with explicit paths. Run both existing affected consumer CTests at the new clean source, including sanitizer-linked installed consumers where available, preserve all current failed runs and triage any remaining terminal failure. Obtain fresh independent code/security rechecks of this exact change and its interruption/cleanup interfaces. Requalify the final candidate appropriately, refresh the same goal audit/fingerprint including this new source/scope, and keep every SUMMARY unchanged, especially frozen19-06.

Update the existing PR before pushing the new reviewed head. Require fresh exact-head native Windows, Linux sanitizer and all protected run/check instances, with concrete coverage for intentional skips. Only then run the production check-pr guard and perform the original single guarded PR B squash. Check the immutable actual main boundary, reviewed-tree equality, inactive window, REL-01 positive/pending-base negative and unchanged publication identity. Adopt the owner workspace while preserving local instructions/settings/evidence, then finalize the sole operational boundary truth from actual facts.

Stop after Phase19 execution at `/gsd-verify-work 19`. Do not run verification, a milestone audit or another phase automatically. Keep both automatic-advance flags false and preserve authority/rehearsal refs. No further release/body/tag/asset write, dispatch or retry is authorized or needed. The sole original release retry already succeeded. Any unrelated unresolved correctness/security finding requires another scope decision.

## Why a new decision is required

D135 explicitly authorized only .gitattributes and tests/CMakeLists.txt. This existing consumer checker is outside that scope. AGENTS.md requires: “At most 2 review-fix rounds and 1 gap round per phase. An unresolved correctness or security finding forces a rescope, never a seed.” The allowance is exhausted; this proposal requests only the one-file remedy and its required requalification.

Recommendation: approve this bounded one-file repair on PR137. The alternative is to leave closure stopped with the published release unchanged. No risk acceptance, new plan/gap slot or additional live release operation is requested.
