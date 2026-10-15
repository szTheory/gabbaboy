---
phase: 14-cgb-e-model-qualification-and-corpus
plan: "08"
subsystem: testing
tags: [age, rgbds, fixtures, provenance, cgb-e, cmake]
requires:
  - phase: 14-05
    provides:
      - Frozen AGE mode-3 source and reference selection at the pinned upstream tree
provides:
  - Six source-bound AGE mode-3 ROM and PNG admissions
  - Closed manifest validation and pinned ROM/image reproduction checks
  - Explicit AGE fixture protocol routing with 13 row-oracle cases and six pending image references
affects:
  - 14-09
  - 14-11
  - 14-12
actuals:
  tokens: 13305
  tasks: 2
  commits: 4
commits: 4
plan_head_before: b04f2378d8a4f931006d90b7415262a432baaf22
plan_head_after: 3b2813cbede9c1a5a1f291608e03b687a7f0bb05
tech-stack:
  added: []
  patterns:
    - Independent expected identities for each pinned ROM, ASM source, and reference PNG
    - Offline digest checks plus exact pinned-source rebuild and image comparison
    - CMake consumes row metadata only for age-row-oracle fixtures
key-files:
  created:
    - fixtures/age/m3-bg-lcdc-cgbBCE.gb
    - fixtures/age/m3-bg-lcdc-nocgb-ncmBCE.gb
    - fixtures/age/m3-bg-lcdc-ds-cgbBCE.gb
    - fixtures/age/m3-bg-scx-cgbBCE.gb
    - fixtures/age/m3-bg-scx-nocgb-ncmBCE.gb
    - fixtures/age/m3-bg-scx-ds-cgbBCE.gb
    - fixtures/age/references/m3-bg-lcdc-cgbBCE.png
    - fixtures/age/references/m3-bg-lcdc-nocgb-ncmBCE.png
    - fixtures/age/references/m3-bg-lcdc-ds-cgbBCE.png
    - fixtures/age/references/m3-bg-scx-cgbBCE.png
    - fixtures/age/references/m3-bg-scx-nocgb-ncmBCE.png
    - fixtures/age/references/m3-bg-scx-ds-cgbBCE.png
    - cmake/AgeFixtureProtocol.cmake
    - tests/scripts/check-age-fixture-protocol.cmake
  modified:
    - fixtures/age/manifest.json
    - fixtures/age/SOURCES.md
    - fixtures/age/ELIGIBILITY.md
    - tests/scripts/reproduce-age.sh
    - tests/scripts/test-reproduce-age.sh
    - tests/CMakeLists.txt
    - tests/expected-tests.txt
key-decisions:
  - CGB-E author Verified lines remain independent expectations; fixture admission does not imply emulator execution or a passing pixel result.
  - Native CGB, CGB-E DMG compatibility mode, and double-speed cases retain separate identities.
  - The versioned protocol registers only 13 row-oracle fixtures; six image references remain admitted-not-executed for Plan 14-09.
patterns-established:
  - The AGE reproducer checks a closed source and image mapping against independent expected values.
  - The report keeps six admitted-but-not-executed targets separate from future pixel outcomes.
  - Unknown fixture classes fail during CMake configuration before row metadata is read.
requirements-completed: []
coverage:
  - id: D1
    description: Six AGE mode-3 ROMs and reference PNGs are admitted with pinned source, rights, digests, CGB-E expectations, and distinct mode and speed identities.
    requirement: CGB-10
    human_judgment: false
    verification:
      - kind: integration
        ref: "bash tests/scripts/reproduce-age.sh --self-check && bash tests/scripts/reproduce-age.sh --compare"
        status: pass
  - id: D2
    description: AGE fixture validation rejects altered, missing, cross-paired, misclassified, or stale-provenance inputs with named diagnostics.
    requirement: CGB-10
    human_judgment: false
    verification:
      - kind: unit
        ref: "bash tests/scripts/test-reproduce-age.sh compare-tampered"
        status: pass
      - kind: unit
        ref: "bash tests/scripts/test-reproduce-age.sh selfcheck-tampered"
        status: pass
  - id: D3
    description: CMake registers all 13 AGE row-oracle cases, keeps six mode-3 image fixtures pending, and rejects unknown fixture classes.
    requirement: CGB-10
    human_judgment: false
    verification:
      - kind: integration
        ref: "cmake -S . -B /tmp/gabbaboy14-wave2-fresh -G Ninja -DCMAKE_BUILD_TYPE=Debug -DBUILD_TESTING=ON && cmake --build /tmp/gabbaboy14-wave2-fresh --parallel 8 && ctest --test-dir /tmp/gabbaboy14-wave2-fresh --output-on-failure -R '^(age_|cgb_tables_|model_gates|summary_coverage|fixture_digest$)'"
        status: pass
      - kind: unit
        ref: "ctest --test-dir /tmp/gabbaboy14-wave2-fresh --output-on-failure -R '^age_manifest_unknown_class$'"
        status: pass
duration: 20min
completed: 2026-10-15
status: complete
---

# Phase 14 Plan 08: AGE Mode-3 Source and Reference Admission Summary

**Six pinned AGE mode-3 ROMs and source PNGs are admitted with fail-closed RGBDS reproduction and separate CGB-E mode and speed identities.**

## Performance

- **Duration:** 20 minutes
- **Started:** 2026-10-15T18:06:29Z
- **Completed:** 2026-10-15T18:26:20Z
- **Tasks:** 2
- **Files modified:** 21

## Accomplishments

- Admitted six 32,768-byte ROMs from AGE commit `1f5bc10e2cb60b86c19f8d0287ff78f410c4f639`, each bound to its exact ASM source and reference PNG with source, output, and image byte counts and SHA-256 digests.
- Recorded four normal-speed targets across native CGB and CGB-E DMG compatibility modes, plus two separately identified native double-speed siblings. All six remain `admitted-not-executed` for the pixel checks owned by Plan 14-09.
- Extended the offline manifest gate and pinned RGBDS 1.0.1 reproducer to reject incorrect membership, mode labels, source/image mappings, bytes, and tool provenance.

## Verification

The exact planned verification command passed with the digest-verified RGBDS 1.0.1 macOS archive:

```text
bash tests/scripts/reproduce-age.sh --self-check && bash tests/scripts/test-reproduce-age.sh compare-tampered && bash tests/scripts/test-reproduce-age.sh selfcheck-tampered && bash tests/scripts/reproduce-age.sh --compare
```

The first Phase 14 wave-2 CMake configure failed before build because the existing registration loops treated all 19 AGE manifest entries as row-oracle fixtures. The configure error reported missing `test_results_address`, `expected_address`, `rows`, and `budget_half_dots` for each of the six new entries at indices 13 through 18; the original diagnostic is preserved in `/tmp/gabbaboy14-wave2.log`. This integration gap was missed because Plan 14-08's verification exercised source reproduction and manifest checks but did not reconfigure the full CMake test tree after adding image-only entries.

The follow-up adds manifest protocol `gabbaboy-age-fixture-protocol-v1`, classifies the existing 13 entries as `age-row-oracle` and the six new entries as `age-m3-reference`, and validates fixed 13/6 membership, required/forbidden row metadata, pending qualification status, and unknown types before CMake reads row fields. All row disposition and sensitivity loops now consume only the validated 13 row indices. The six image references remain explicitly `admitted-not-executed`; none are registered as row tests or counted as executed.

A fresh configure in `/tmp/gabbaboy14-wave2-fresh` passed and printed `AGE fixture protocol pass row-oracle=13 image-pending=6`. The fresh build completed all 270 targets. The focused AGE/table/model/corpus/summary CTest selection passed 52/52, including the exact original set of 13 AGE row registrations, all four sensitivity sweeps, and the new `age_manifest_unknown_class` negative control. The CTest inventory check found 13/13 expected row cases and zero image fixtures registered as row tests. The reproduction self-check negative control also rejected `age-unknown-protocol` with `unsupported-fixture-class-age-unknown-protocol`.

The rebuild checked all 19 manifest ROMs, including the 13 previously admitted files, and reported `result=byte-identical`. All six reference images reported `result=reference-source-identical`. The negative controls produced these expected diagnostics:

- Rebuilt ROM mutation: `result=differs m3-bg-lcdc-cgbBCE.gb`.
- Traversal and malformed digest: `source_path-outside-allow-list`; `invalid-sha256-spsw-div-cgbBCE.gb`.
- Cross-pair reference, missing ROM, and altered PNG: `m3-reference-file-mismatch-m3-bg-lcdc-cgbBCE.gb`; `committed-file-missing-m3-bg-lcdc-cgbBCE.gb`; `committed-reference-digest-mismatch-m3-bg-lcdc-cgbBCE.gb`.
- Stale RGBDS archive pin, wrong compatibility mode, and omitted sibling: `RGBDS-build-pin-mismatch`; `m3-mode-mismatch-m3-bg-lcdc-nocgb-ncmBCE.gb`; `m3-manifest-membership-mismatch`.

The admitted set has 6 distinct ROM digests, 6 distinct ASM source digests, and 6 reference paths. Two SCX references at the pinned AGE commit have identical PNG bytes and therefore share digest `6895b6111d432ea5f0422991a1d7143f1fe133481e018b3c8652616af759085d`; their source paths and native speed identities remain separate. The mode counts are 4 native-CGB and 2 DMG-compatibility cases; the speed counts are 4 normal and 2 double speed.

## Task Commits

1. **Task 1: Tracer: one AGE ASM and PNG pair reproduces to admitted bytes** — `57b7d59` (`feat(14-08)`).
2. **Task 2: Expand the other five source/image pairs** — `cbb8158` (`feat(14-08)`).
3. **Original summary metadata snapshot** — `a9176e8` (`docs(14-08)`).
4. **Wave-2 integration correction: route fixture metadata by protocol** — `3b2813c` (`fix(14-08)`).

The measured `commits: 4` range includes this original summary snapshot; the refreshed summary below is committed after the measured plan head.

## Files Created and Modified

- `fixtures/age/manifest.json` — independent output, source, image, model, mode, speed, and author-expectation records for the six additions.
- `fixtures/age/SOURCES.md` and `fixtures/age/ELIGIBILITY.md` — rights, exact source/image identities, admission status, and expectation boundaries.
- `tests/scripts/reproduce-age.sh` and `tests/scripts/test-reproduce-age.sh` — pinned rebuild, source-image byte checks, and positive and negative controls.
- `tests/CMakeLists.txt`, `tests/expected-tests.txt`, `cmake/AgeFixtureProtocol.cmake`, and `tests/scripts/check-age-fixture-protocol.cmake` — fail-closed registration classes, pending-image exclusion, and unknown-class control.
- Six ROMs and six reference PNGs under `fixtures/age/` — pinned upstream artifacts listed in the manifest.

## Decisions Made

CGB-E `Verified` lines are preserved as author expectations, with no physical hardware or emulator result inferred. Normal-speed compatibility cases use the CGB-E silicon model in DMG compatibility mode; double-speed siblings remain distinct inputs. CGB-10 remains open at the phase level until the corpus reporting plans complete, so this summary does not mark the requirement complete.

The versioned manifest protocol distinguishes row-oracle cases from source-image references. Plan 14-09 owns pixel judgments; this protocol change does not run or imply those checks.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Preserve the exact upstream `Verified` wording**

- **Found during:** Task 1
- **Issue:** The initial source assertion expected a normalized `pass:` label, while the pinned AGE source records only the date and model. The source-bound verification correctly rejected that mismatch.
- **Fix:** Store and validate the exact author line from the pinned source.
- **Files modified:** `tests/scripts/reproduce-age.sh`, `fixtures/age/manifest.json`, `fixtures/age/SOURCES.md`.
- **Verification:** The full pinned-source rebuild and all negative controls passed.
- **Committed in:** `57b7d59`.

**2. [Rule 3 - Blocking integration issue] Route AGE CMake consumers through explicit fixture classes**

- **Found during:** Phase 14 wave-2 configure.
- **Issue:** The new image-reference entries were intentionally missing row-oracle metadata, but CMake's disposition and sensitivity registration loops read row fields from every manifest entry and stopped configuration.
- **Fix:** Added a versioned AGE fixture protocol, fail-closed type and metadata checks, and row-only iteration. The image fixtures stay pending Plan 14-09 and receive no fabricated row values.
- **Files modified:** `fixtures/age/manifest.json`, `cmake/AgeFixtureProtocol.cmake`, `tests/CMakeLists.txt`, `tests/expected-tests.txt`, `tests/scripts/check-age-fixture-protocol.cmake`, `tests/scripts/reproduce-age.sh`, `tests/scripts/test-reproduce-age.sh`.
- **Verification:** Fresh configure/build passed; focused CTest passed 52/52; unknown-class negative controls failed with the expected diagnostic.
- **Committed in:** `3b2813c`.

**Total deviations:** 2 auto-fixed issues.
**Impact on plan:** The original admission corpus and 13 row-test registrations remain unchanged. The follow-up repairs configure-time integration and preserves the six image-only entries for Plan 14-09.

## Issues Encountered

The initial wave-2 configure failure is documented above; it stopped before build. The managed sandbox also blocked direct writes to `.git` for the plan-head ledger and index lock. The task and integration commits were made through the authorized git path with hooks enabled; the measured commit count and head range use the persisted execution baseline. No hook bypass was used.

## User Setup Required

None - no external service configuration required.

## Next Plan Readiness

Plan 14-09 has six exact source-bound ROM/image pairs ready for its automated pixel oracle. This plan reports fixture identity and reproducibility only; it does not claim pixel matches, emulator execution, physical CGB-E qualification, or game-level support.

---
*Phase: 14-cgb-e-model-qualification-and-corpus*
*Completed: 2026-10-15*

## Self-Check: PASSED

- All 12 fixture outputs and the summary file exist.
- Commits `57b7d59`, `cbb8158`, and `3b2813c` are ancestors of the current branch head.
- The 13 existing row registrations remain present; none of the six image fixtures appears as a row test.
- The summary coverage script and focused CTest gate pass; all three coverage entries auto-pass without human judgment.
- No new stub patterns were found in the modified scripts, manifest, CMake protocol, or fixture documentation.
