---
phase: 14-cgb-e-model-qualification-and-corpus
plan: "09"
subsystem: testing
tags:
  - cgb-e
  - age
  - rgb555
  - corpus
requires:
  - phase: 14-04
    provides: APU lifecycle, split-run CH3 behavior, and bounded execution coverage
  - phase: 14-07
    provides: pinned SameSuite APU outputs, independent author expectations, and exact case bindings
  - phase: 14-08
    provides: six admitted AGE mode-3 ROM/reference pairs and pending image-case protocol
provides:
  - Bounded AGE mode-3 RGB555 guest capture and independent PNG pixel oracle
  - Exact executed dispositions for six native, compatibility, and double-speed image cases
  - Cross-consumer identity and negative-control checks for AGE image receipts
affects:
  - phase 14-11 corpus aggregation
  - CGB-E model qualification
tech-stack:
  added: []
  patterns:
    - Bounded guest output is compared to source-derived reference pixels
    - Evaluator protocol success remains separate from observed emulator pass status
    - Stable case and assertion identities bind output, mode, speed, and source ancestry
key-files:
  created:
    - tests/test_age_m3.c
    - tests/scripts/verify-age-m3-pixels.py
    - .planning/phases/GB-14-cgb-e-model-qualification-and-corpus/14-09-red-task1.json
    - .planning/phases/GB-14-cgb-e-model-qualification-and-corpus/14-09-red-task2.json
  modified:
    - fixtures/age/manifest.json
    - tests/external/cgb-ppu-dispositions.json
    - tests/external/cgb-corpus-inventory.json
    - tests/scripts/verify-cgb-corpus-inventory.py
    - tests/scripts/verify-cgb-speed-dispositions.py
    - tests/scripts/verify-external-dispositions.py
    - cmake/AgeFixtureProtocol.cmake
    - tests/CMakeLists.txt
    - tests/expected-tests.txt
    - tests/scripts/reproduce-age.sh
    - tests/scripts/test-reproduce-age.sh
    - docs/cgb-corpus.md
    - docs/cgb-profile.md
    - fixtures/magentests/ELIGIBILITY.md
    - .planning/phases/GB-14-cgb-e-model-qualification-and-corpus/14-CORPUS-INVENTORY.md
key-decisions:
  - Keep source PNGs as the independent oracle; derive RGB555 expectations from guest palette setup and the documented compatibility palette.
  - Preserve each author pass target while recording measured mismatches as case-specific expected failures.
  - Bind model, execution mode, and speed independently, including for the native SCX references whose PNG digests are identical.
metrics:
  duration: 22min
  completed: 2026-10-15
status: complete
actuals:
  tokens: 34452
  tasks: 2
  commits: 4
plan_head_before: ff3367ca22eac6f87cf8bbcb542264dd0c50bafe
plan_head_after: f3827cc56b9198edc38d8f3c6215697ccbe9c662
requirements-completed: []
coverage:
  - id: D1
    description: Bounded public-API guest capture and source-derived RGB555 PNG oracle reject malformed or altered images.
    human_judgment: false
    verification:
      - kind: integration
        ref: cgb_age_m3_tracer and cgb_age_m3_pixel_controls in the phase1 CTest suite
        status: pass
      - kind: unit
        ref: python3 -I tests/scripts/verify-age-m3-pixels.py --self-test
        status: pass
      - kind: integration
        ref: cgb_age_m3_early_frame_control in the phase1 CTest suite
        status: pass
  - id: D2
    description: Six exact AGE image identities are executed and compared with preserved author targets and measured dispositions.
    human_judgment: false
    verification:
      - kind: integration
        ref: six cgb_age_m3_m3_bg_* CTest cases and cgb_age_m3_membership
        status: pass
      - kind: integration
        ref: tests/scripts/verify-age-m3-pixels.py case, signature, model, mode, and speed checks
        status: pass
      - kind: integration
        ref: cgb_external_dispositions and cgb_speed_dispositions CTest checks
        status: pass
  - id: D3
    description: Image receipts remain consistent across AGE manifests, inventory, disposition validators, and reproduction controls.
    human_judgment: false
    verification:
      - kind: integration
        ref: 22 focused phase1 CTest checks covering AGE pixels, inventory, external dispositions, speed, and reproduction controls
        status: pass
      - kind: unit
        ref: python3 -I tests/scripts/verify-cgb-corpus-inventory.py --selection-only
        status: pass
      - kind: unit
        ref: bash tests/scripts/reproduce-age.sh --self-check
        status: pass

---

# Phase 14 Plan 09: AGE CGB-E Mode-3 Model Qualification Summary

**Six source-pinned AGE images now have bounded RGB555 captures and exact CGB-E dispositions; the software model mismatches all six references.**

## Performance

- **Duration:** 22 min
- **Started:** 2026-10-15T17:17:13-04:00
- **Completed:** 2026-10-15T17:39:18-04:00
- **Tasks:** 2
- **Files modified:** 20 before this summary

## Accomplishments

- Added a bounded C17 harness that runs admitted AGE guests through the public API, captures RGB555 frames and terminal metadata under the build tree, and enforces the source-derived frame boundary.
- Added a Python standard-library PNG decoder and pixel oracle with bounded input, chunks, decompression, dimensions, and output; malformed, swapped, wrong-mode, corrupted, blank, stale-identity, and incomplete-frame controls fail named predicates.
- Executed all six native, compatibility, and double-speed image cases and propagated their exact measured failures through the manifest, inventory, CTest protocol, disposition validators, reproduction checks, and supporting documentation.

## Task Commits

1. **Task 1 RED:** `e2850a5` (PNG oracle test failed against the initial pending contract).
2. **Task 1 GREEN:** `5f4b6b8` (bounded AGE mode-3 RGB555 tracer and oracle).
3. **Task 2 RED:** `a94b94c` (six executed-disposition contract assertions failed against pending records).
4. **Task 2 GREEN:** `d9a9bfa` (six AGE image targets qualified with stable identities and exact dispositions).

## Actual Qualification Results

Every case evaluated 23,040 RGB555 pixels. All six CTest cases passed because the observed mismatch, identity, model, mode, speed, and signature matched the declared expected-failure protocol. These are **zero guest image passes out of six**; the protocol passes do not count as emulator passes.

| AGE case | Model mode / speed | Mismatched pixels | Exact mismatch signature |
| --- | --- | ---: | --- |
| `m3-bg-lcdc-cgbBCE` | native CGB / normal | 4,736 | `f872cd7b88efd0e650abbe6b6e665c520db922680393cbb03ae961ff88cadba9` |
| `m3-bg-lcdc-nocgb-ncmBCE` | DMG compatibility / normal | 4,736 | `f8e73561af491063f68efbca0ce1db1c54385587bbc4d98f80a0661ff49e3949` |
| `m3-bg-lcdc-ds-cgbBCE` | native CGB / double | 6,944 | `2caeb6b70a0dc22096be7a9ac3283d4428166e31dd224cda21caa8432baa8917` |
| `m3-bg-scx-cgbBCE` | native CGB / normal | 672 | `f35aeda05f98fb815d1bc19a8d83a1dea0400c2b7c1e775efeedf8ef3646d97c` |
| `m3-bg-scx-nocgb-ncmBCE` | DMG compatibility / normal | 672 | `1da05a373b6bc39943f657ddb63a07bb6e62d13335e4af10e461ecfd73c3d611` |
| `m3-bg-scx-ds-cgbBCE` | native CGB / double | 448 | `639c32dd649abd954020590d056cf41900536f37c704a7f3888a6393455b65f0` |

Total: 138,240 pixel assertions, 18,208 mismatches, and 120,032 matching pixels across the six captures. The compatibility expectation uses documented palette values `(0x639F, 0x4275, 0x254B, 0x0421)` and the source BGP mapping. The two native SCX references share a PNG digest; case identity still independently binds the ROM, model, mode, and speed, and the wrong-speed control rejects swapped metadata.

The six image receipts are terminal and preserve their author `pass` targets with the narrow `expected-failure:cgb-e-mode3-reference-mismatch` reason, exact signature, and promotion rule. The 13 existing AGE row registrations and speed dispositions are preserved. The inventory remains at 181 sources, 109 admitted outputs, 107 fixed cases, and zero pending output bytes; suite-level assertion aggregation remains for plan 14-11.

## Verification

- `cmake --build --preset phase1 -j2` — passed; build was up to date after Task 2.
- `ctest --preset phase1 -R 'cgb_age_m3_|cgb_corpus_inventory_(selection|selftest)|cgb_external_dispositions|cgb_speed_dispositions|age_repro_selfcheck|age_manifest_unknown_class' --output-on-failure -j2` — 22/22 passed.
- `ctest --preset phase1 -V -R '^cgb_age_m3_m3_bg_'` — all six exact expected-failure results and signatures reproduced.
- `python3 -I tests/scripts/verify-age-m3-pixels.py --self-test` — 13/13 positive and negative controls passed.
- `python3 -I tests/scripts/verify-cgb-corpus-inventory.py --selection-only` — passed with 181 sources, 109 outputs, 107 cases, zero pending outputs.
- `python3 -I tests/scripts/verify-cgb-speed-dispositions.py` — passed, 34 rows.
- `python3 -I tests/scripts/verify-external-dispositions.py --record tests/external/cgb-ppu-dispositions.json --doc docs/cgb-profile.md --repo-root .` — passed, AGE 6 and Mealybug 30.
- `bash tests/scripts/reproduce-age.sh --self-check` — passed.
- `git diff --check` — passed.
- Both TDD RED evidence records were accepted by `gsd-tools.cjs check tdd-red-evidence`; Task 1 and Task 2 each followed RED then GREEN commits.

These checks qualify the CGB-E software model against pinned source images. They make no physical-hardware or game-level claim. The full phase suite remains under the parent executor's verification ownership.

## Decisions Made

- Kept the upstream source-derived images as independent references and used only guest setup and documented palette mapping to derive RGB555 values.
- Captured all measured mismatches as exact case-specific expected failures while keeping author pass targets intact.
- Kept mode, speed, source, and case identity independent of PNG digest so identical reference bytes cannot make the wrong-speed case qualify.
- Left suite-wide assertion aggregation to plan 14-11; this plan provides stable case and assertion identities for that later report.

## Deviations from Plan

### Auto-fixed Issues

**1. Expanded the six-image execution update through every directly affected contract consumer.**
- **Found during:** Task 2.
- **Issue:** Updating only the plan-declared comparator and PPU disposition left the AGE manifest, corpus receipts, fixture protocol, speed/disposition validators, reproduction controls, and docs claiming the six images were still pending.
- **Fix:** Updated the exact six image identities and expected-failure evidence atomically across those consumers; retained all 13 row registrations and evolved the existing pending-image negative control to assert exact case identity.
- **Files modified:** AGE manifest, corpus inventory and validators, PPU dispositions, CMake fixture protocol, reproduction scripts, CTest registry, CGB docs, and Magentests eligibility notes.
- **Verification:** 22 focused CTests and the inventory, speed, external-disposition, and reproduction checks passed.
- **Committed in:** `d9a9bfa`.

**2. Closed the AGE harness output stream on every capture path.**
- **Found during:** Task 1.
- **Issue:** The early error path could skip closing the opened output stream.
- **Fix:** Made stream closure unconditional after capture writes.
- **Files modified:** `tests/test_age_m3.c`.
- **Verification:** Full phase1 build, tracer, early-frame control, and six image cases passed their exact protocols.
- **Committed in:** `5f4b6b8`.

**Total deviations:** 2 (scope integration and one resource-cleanup bug fix).
**Impact on plan:** Required to keep executed evidence and all existing consumers consistent; no public API, dependency, emulator behavior, or later reporting scope was added.

## Known Stubs

None found in files created or modified by this plan.

## Threat Flags

None. The new ROM and frame boundaries are bounded and remain within the plan's threat model; no new network, auth, persistence, or public API surface was added.

## Next Phase Readiness

Plan 14-09 is complete. Plan 14-11 can consume the stable six image case identities and per-case assertion signatures while aggregating suite evidence. These receipts do not claim hardware confirmation or six guest passes.

## Self-Check: PASSED

- Summary file exists at the required phase path.
- All four task commits are ancestors of the current plan head `d9a9bfa`.
- The summary's plan window records four measured task commits from `3953b9429fe01d1ef8de4375df2818f24f7c91ba` through `d9a9bfaec6d81f801e131f0505a29c26d05daa37`.

---
*Phase: 14-cgb-e-model-qualification-and-corpus*
*Completed: 2026-10-15*

## Sanitized ancestry

The top-level commit windows use sanitized unpublished ancestry. Historical execution revision IDs and task IDs above remain as originally recorded; [14-HISTORY-REDACTION.md](14-HISTORY-REDACTION.md) maps them to the equivalent sanitized commits. Fresh final qualification is recorded separately after this rewrite.
