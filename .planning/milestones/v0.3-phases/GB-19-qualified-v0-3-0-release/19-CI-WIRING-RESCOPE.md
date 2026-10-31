# Approved bounded repair: current evidence links and Windows path identity

Status: owner-approved under D-129. The owner answered “yes i approve” to the bounded CI-wiring repair proposal. PR135 is frozen at reviewed/pushed `52fd7cad785fec0d7c7df5d752541894ade87900`; no new source fix or CI retry has been made. D-128 exact-source guard implementation is reviewed and its62 controls pass, including on actual Windows. Earlier scopes/rounds/bases and failed attempts remain historical.

## Verified fresh CI failures

PushCI41120861027 and PRCI41120867639 failed current-head native/floor qualification. Raw and cleaned individual-job logs are retained under ignored `build/phase19-window/source-guard/ci-failure/`; obtain them with the job-log API and strip terminal escapes before presentation. Independent diagnosis is in `diagnostic-review.md`.

1. The live v0.3 carry-over record `.planning/phases/GB-16-tune-up-and-v0-2-debt-closure/16-DISPOSITIONS.json`, row `LIM-REHEARSAL-FAILED`, still names `ctest:workflow_policy_controls`. D-127 retired that aggregate CTest. `v03_dispositions` correctly rejects the stale name against the current expected-test inventory; it is the sole CMake-floor/Linux failure. This record is current v0.3 data, not the digest-pinned v0.2 archived record.
2. Windows additionally fails `workflow_policy_coverage`: the checker semantically validates the group output path, then compares its raw string against native `str(Path(...))`. CMake emits forward slashes while Windows Path renders backslashes, so equivalent paths are incorrectly rejected. All six split policy groups passed on actual Windows at the existing180-second limits (largest observed73.22s), and the62 control suite passed. No assertion failure or original aggregate timeout remains in those groups.

The source pin closes the prior normalization/body gap; it is not reopened. Both source/attempt-bound performance receipts pass the unchanged1.10 Ir limit, and the successful Mac candidate is arm64/minOS15.0/SDK15.5. These positives cannot qualify failed native checks. Final preview consumer/core evidence remains unavailable.

## Concrete recommended scope

Authorize one additional consolidated CI-integration correction and independent review cycle within the same unmerged PR135. Preserve all earlier rounds and the single D125 main-merge allowance; no reserved19-08 use.

- In the existing coverage checker, compare only the already path-validated `GBB_EXPECT_FILE` field by filesystem identity. A one-field prototype preserves its validated raw value for the subsequent strict scalar/key comparison. Retain strict duplicate/override, executable/script/root/group, exit/marker/freshness, wrong-destination, candidate and source-pin checks. Add persistent equivalent-path positives for `/./` and CMake-style Windows forward slashes, retaining wrong-output negatives. No generic path-parser framework or relaxation of other fields.
- In the live16-DISPOSITIONS row, replace only the retired CTest evidence link with the six group names and the two coverage/control names. Keep the existing production-check link, all historical receipts, statuses, decision, basis and other rows byte/semantically unchanged. Do not rewrite frozen phase summaries, prior boundary commits or the v0.2 archive.
- Adjust only narrowly necessary existing CMake control marker/count wiring. Keep all current tests, production policy runner, frozen manifest, reviewed source digest/reference, baseline/oracle checks, timeouts/scaling/job/performance limits, permissions, dependencies, core/API and minimum-OS policy unchanged. Do not restore a misleading aggregate alias, suppress the disposition check or rebaseline any source pin.
- Run the complete affected local contract set, including v03_dispositions and controls, source/registry/registration/override controls, inventory/planning/budget checks and platform-equivalent path cases. Independently review the corrected immutable candidate and require fresh exact-head protected actual Windows/Mac/Linux CI, source-bound performance receipts and actual Mac/preview artifacts. Only then the existing guarded merge/regeneration/real discovery and fresh19-07 sequence may proceed. No extra main merge or tag/draft movement.

Ownership: existing `tests/scripts/verify-workflow-policy-coverage.py`, narrowly necessary `tests/cmake/ci-lanes.cmake` marker wiring, the one live16-DISPOSITIONS evidence row and related approved scope/decision/plan/STATE records. Any other correctness/security finding stops for another scope decision.

## Provisional evidence before approval

No project source was edited. The ignored `windows-path.proposed.patch` contains the one-field semantic-path remedy. In-memory tests accept the native and equivalent-path positives, reject a different destination, and retain all62 current controls (`windows-path-proposed-probe.log`). `ledger-retarget.proposed.patch` changes only that row’s evidence links; the frozen source is the rejecting negative and the proposed copy passes the unchanged disposition checker with receipts/status/decision/basis preserved (`ledger-retarget-probe.log`). These are prototypes, not hosted qualification.

## Why an owner decision is required

D128 allowed the exact-source guard and one focused correction/review cycle, now complete. This newly demonstrated integration repair needs a further cycle and changes a live disposition record outside that ownership. AGENTS.md requires unresolved correctness findings to force rescope. Keeping the existing release hold needs no acknowledgment; another correction/qualification attempt is not assumed.

Completed stage: Phase19 execution through19-06, D127 partition and D128 source-guard implementation/review. Active stage: Phase19 — Qualified v0.3.0 Release, PR135 qualification held. Approved exact continuation: `/gsd-execute-phase 19`. Final execution boundary stays `/gsd-verify-work 19`, not automatic; both auto-advance flags stay false.
