# Phase 14 refresh evidence

Source producer: `b52a4dabf244b7e37d4fc7bd22d8830927d65955`. Installed runtime: `@opengsd/gsd-core` 1.18.0. No source, test, fixture, CI or public-document change was made during this refresh.

## Fresh execution

- Configured and rebuilt with `cmake --preset phase1` and `cmake --build --preset phase1`; configured one-shot regression ran under the 600-second gate: **1,144/1,144**, **385.46 seconds**, zero failures/errors/skips. Logs: `build/14-refresh-configure.log`, `build/14-refresh-build.log`, `build/14-refresh-regression.log`.
- Rebuilt `build-player`; `ctest --test-dir build-player -R '^player_' --output-on-failure --no-tests=error`: **98/98**, **17.10 seconds**, zero skips. Transient logs: `/tmp/gabbaboy-phase14-player-build.log` and `/tmp/gabbaboy-phase14-player.log`.
- The inherited core cache names a removed temporary install prefix, so its 1,144-test stream omits five optional installed-package tests. The original core-JUnit inventory check correctly rejected their absence. Fresh install to `build/14-refresh-package`, separately configured `build/14-refresh-consumers`, and `ctest -R '^installed_(consumer|runner)'` pass **5/5**, **1.80 seconds**. The combined JUnit explicitly concatenates those five testcases with the original 1,144; it is not claimed as a single 1,149-test run. Frozen core inventory **258/258** and player inventory **55/55** pass on these respective reports. `verify-dmg-baseline.sh --build-dir build` reports **zero changed rows**.
- `python3 -I tests/scripts/verify-v02-consumers.py --run --output build/14-refresh-v02-consumers.json`: fresh-install-relocated C/C++ consumers pass profile selection, probe/info, RGB555 copy and RTC catch-up; package build isolated and source producer matches above. Core regression also exercises required package-exclusion and consumer-contract controls.

## Fresh corpus and claim ancestry

A direct `--run` receipt executed the cases but was rejected by the public claim checker with `receipt-nonce-or-stream-mismatch`. It is not the qualified final receipt. The final producer uses `--begin-run`, the exact 108 CTest names from its metadata, `ctest -T Test --no-compress-output --test-output-size-passed 16777216` with nonce-named JUnit, then `--from-ctest`. This is a **selected 108-test stream**, independent of the full regression above. All **108/108** pass in **13.03 seconds**. Log: `build/14-refresh-corpus-nonce.log`.

`verify-cgb-corpus-claims.py --receipt build/14-refresh-corpus-receipt.json` accepts the final nonce-bound receipt. Run ID `fcf26481f97d0bcb1841d3dbbf5c4e60069dfb9cb088ee2ee95ae97bfc96f9c4`; nonce digest `d885941d9b147a996ee1ead4691f5926de492788a5607bef4e3354393eebf59f`. Required cases **107/107**; observed passes **25**, matched expected failures **82**; assertions **2,845/4,959**; pixels **138,240**, mismatches **18,208**. Exact expected failures are retained, not counted as observed passes.

| Suite | Cases | Observed passes | Matched expected failures |
|---|---:|---:|---:|
| AGE | 19 | 2 | 17 |
| MagenTests | 5 | 5 | 0 |
| Mooneye | 9 | 6 | 3 |
| SameSuite | 74 | 12 | 62 |

Inventory `--bindings` passes **181 sources, 109 admitted outputs, 107 cases**. Claim self-test rejects **15** controls. Artifact privacy check passes for the public default-named artifacts; the custom final receipt above is separately validated by the claim checker. The privacy check is not claimed to enumerate the custom filename.

## Closure and boundaries

Canonical UAT is generated and checked with the shared `tests/scripts/verify-uat-closure.py`: **49/49** individual deliverables, **19** rejected controls, zero human checkpoints. The historical phase-local self-test independently passes **17** closure, **10** immutable-handoff and **2** commit controls; all **13** bounded commit windows reconcile with **4** legacy nested-count warnings. Boundary facts are read from `c771b1b9c143d7589f8bb40c163c2e9f89ca1168`, with historical phase head `8c09f9697aabc96424280aa14544ba68ff3f2fd4`; they do not assert live routes or current ancestry. Existing `14-UAT-REVIEW.md` remains historical; the refresh gates preserve its resolved machine-route warning.

See `14-REFRESH-GATES.md` for focused current review/security/Nyquist/UI applicability and their limitations. No new hosted, native Windows, CMake-floor, sanitizer-runtime, RGBDS rebuild, performance, hardware, analog, perceptual or game qualification is claimed. Historical receipts retain their actual producer revisions. The scope resolver is degraded after squash history; bounded windows and current behavior are independent evidence.

## Artifact digests

Local files may be cleaned later; hashes identify the execution receipts inspected for this refresh.

| Artifact | SHA-256 |
|---|---|
| `build/14-refresh-regression.xml` | `7076a8090fd3d9260f3f89ae57eff5894aab448002cee62ee079a9642ed678fe` |
| `build-player/14-refresh-player.xml` | `c58e0ff7aa620cade90aa47db5879ae734b3786fcd40677b0484ba715695f462` |
| `build/14-refresh-consumers.xml` | `f20f849126c4baad6abca0d1f6509b88ae0fc86a36934a83e5d8416574d07723` |
| `build/14-refresh-core-and-consumers.xml` | `0c43b1ffa90833e096ed086b630543c49f128be39535b8be7048839850cd254e` |
| `build/14-refresh-corpus-receipt.json` | `d929ed0ce8f2640d97bfc6c8e84533ee0d5dc7f104e9c9e9ca72bafafdab02ca` |
| `build/14-refresh-v02-consumers.json` | `9450d3054e220da87c38573bf6edfbed11b2474fd7cb0893746922ec04b91f00` |

## Delivery boundary

Phase 15 — CGB Acceptance, Support Ledger and v0.2.0 Release is already complete, with current verification `passed`; no new numbered phase starts. The final cross-phase freshness check found **Phase 8 — Cartridge Seam, MBC5 and MBC2** stale over `cmake/PreviewPackageSmoke.cmake`, changed later by Phase 10 commit `1ba2346` to enforce CGB fixture exclusion. Phase 12 is also stale over lessons/index metadata from the prior Phase 13 refresh; all remaining reports pass. Next corrective stage: Phase 8 verification refresh only, `/gsd-execute-phase 8`. Do not replay completed implementation. The existing audit retains **21 debt items** and **28/28 requirements**; milestone completion review remains pending and no debt is accepted here. No archive, tag or release occurs. Both auto flags remain false. Boundary triage: zero open issues; PRs #78–89 and release-please #75 remain open at refresh start. This stacked branch builds on Phase 13 PR #89; no merge occurs without exact reviewed-head required checks.

The final live handoff checker verifies STATE/current-session, project overview, continuation, this evidence and machine routing, with ten rejected controls for stale routes, either auto flag, excess phase count and incorrect Phase 15 status. Historical boundary handoff checks remain pinned to their own commit. Existing research index and lessons remain unchanged because Phase 12's fingerprint covers them; this avoids adding new edits to that already-stale metadata coverage. Current routing is owned by STATE and the continuation above.
