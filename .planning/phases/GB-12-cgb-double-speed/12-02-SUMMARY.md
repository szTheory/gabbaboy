---
phase: 12-cgb-double-speed
plan: 02
subsystem: fixtures
tags: [age, rgbds, reproducible-build, provenance, negative-controls]
requires:
  - phase: 12-01
    provides: "CGB speed-switch tracer core and private speed-state seam"
provides:
  - "Rights-documented AGE spsw-div fixture rebuilt byte-identically from its pinned source"
  - "Manifest-driven AGE self-check, source rebuild, byte comparator and offline tamper controls"
  - "Linux fixture-repro integration for the AGE source and RGBDS pins"
affects: [12-04, 12-09, 12-16]
actuals:
  tokens: 5734
  tasks: 2
  commits: 2
  plan_head_before: c6f18a4bc58e78098470f1e8106e82630edbabb5
  plan_head_after: 2e9782126e102399f00e000aa3c771347041b656
tech-stack:
  added: []
  patterns:
    - "Third-party test ROM provenance ties source commit, source tree, build archive digest and committed ROM digest"
    - "Offline negative controls exercise byte comparison and manifest path/digest validation"
key-files:
  created:
    - fixtures/age/ELIGIBILITY.md
    - fixtures/age/LICENSE.txt
    - fixtures/age/SOURCES.md
    - fixtures/age/WARNING.md
    - fixtures/age/manifest.json
    - fixtures/age/spsw-div-cgbBCE.gb
    - tests/scripts/reproduce-age.sh
    - tests/scripts/test-reproduce-age.sh
  modified:
    - .github/workflows/fixture-repro.yml
    - THIRD_PARTY_NOTICES.md
key-decisions:
  - "Pin RGBDS 1.0.1 and both platform archive digests to the established CGB fixture toolchain."
  - "The byte-difference negative control mutates the rebuilt copy; mutating committed fixture bytes would correctly fail self-check before reaching the byte comparator."
requirements-completed: [CGB-06]
coverage:
  - id: D1
    description: "The rights and manifest pin the first AGE ROM to its source commit, tree, license, source path and RGBDS 1.0.1 archive; local rebuild bytes match."
    requirement: CGB-06
    human_judgment: false
    verification:
      - kind: integration
        ref: "bash tests/scripts/reproduce-age.sh --compare"
        status: pass
      - kind: unit
        ref: "cmake -DMANIFEST=fixtures/age/manifest.json -P cmake/VerifyFixtureManifest.cmake"
        status: pass
      - kind: other
        ref: "shasum -a 256 fixtures/age/LICENSE.txt and fixtures/age/WARNING.md"
        status: pass
  - id: D2
    description: "Offline comparison and manifest validation reject tampered bytes, an escaping source path and a malformed digest."
    requirement: CGB-06
    human_judgment: false
    verification:
      - kind: unit
        ref: "bash tests/scripts/test-reproduce-age.sh compare-tampered"
        status: pass
      - kind: unit
        ref: "bash tests/scripts/test-reproduce-age.sh selfcheck-tampered"
        status: pass
  - id: D3
    description: "The hosted fixture-repro workflow enforces AGE RGBDS pin equality and schedules rebuild and offline controls."
    requirement: CGB-06
    human_judgment: false
    verification:
      - kind: other
        ref: "fixture-repro workflow YAML and required step/pin assertions"
        status: pass
duration: 7 min
completed: 2026-10-13
status: complete
---

# Phase 12 Plan 02: AGE fixture provenance and rebuild Summary

The first AGE CGB speed-switch oracle is licensed, pinned to its upstream source tree, and reproduced byte-for-byte with digest-pinned RGBDS 1.0.1; offline controls show the rebuild gate catches tampering.

## Performance

- **Duration:** 7 min
- **Started:** 2026-10-13T16:59:00Z
- **Completed:** 2026-10-13T17:05:19Z
- **Tasks:** 2
- **Files modified:** 10

## Accomplishments

- Rebuilt `spsw-div-cgbBCE.gb` from AGE commit `1f5bc10e2cb60b86c19f8d0287ff78f410c4f639` and tree `2fece1a678edb18c1664efd7328a430a79c70be4` with the RGBDS 1.0.1 archive whose macOS SHA-256 was verified before extraction. The ROM digest is `2c836288b58651f72a335417f11ba346863145dd9996048979ad8e5b9cd0aa7b`.
- Added verbatim MIT and caution files, source/eligibility evidence, the fixture manifest and third-party notice. The hardware `Verified:` lines are explicitly classified as author attestation.
- Added manifest-driven `--self-check`, pinned-source `--compare`, offline `--compare-built`, and offline negative controls; fixture-repro now enforces RGBDS pin equality and runs the AGE rebuild on Linux.

## Task Commits

1. **Task 1: AGE tracer ROM, provenance and rebuild script** - `a0aef81` (`feat`)
2. **Task 2: Eligibility, notices, negative controls and CI** - `2e97821` (`test`)

## Decisions Made

- RGBDS 1.0.1 uses the existing macOS and Linux archive pins shared with the CGB colour fixtures.
- The byte-difference negative control mutates a scratch rebuilt ROM. Mutating scratch committed fixture bytes would fail the integrity self-check before exercising the byte comparator.
- The branch was not pushed, so Linux hosted rebuild confirmation is pending; `SOURCES.md` retains the provisional note for later phase close-out.

## Deviations from Plan

The planned compare-tampered control described flipping the scratch committed ROM, while the same plan requires `--compare-built` to perform committed-digest self-check first. That sequence exits at self-check and cannot prove the byte comparator detects a mismatch. The control instead flips the scratch rebuilt ROM, preserving the intended byte-comparison negative test while leaving the committed fixture integrity check active.

## Issues Encountered

- The repository ignores `*.gb` as generated output. Only the explicitly plan-listed AGE fixture was force-added to its task commit.
- The hosted Linux workflow was not run because this branch was not pushed; the digest status remains explicitly provisional.

## Verification

- `bash tests/scripts/reproduce-age.sh --self-check`: passed.
- `cmake -DMANIFEST=fixtures/age/manifest.json -P cmake/VerifyFixtureManifest.cmake`: passed with the pinned ROM digest.
- `bash tests/scripts/reproduce-age.sh --compare`: passed with `result=byte-identical` using the verified RGBDS archive and source pins.
- Both offline negative controls passed; malformed CLI mode returned exit 2.
- Upstream MIT and WARNING SHA-256 values matched; privacy scan found no personal home paths or Gmail addresses.

## Known Stubs

None.

## Self-Check: PASSED

Both task commits are ancestors of the recorded plan head, all declared artifacts exist, and `summary_coverage` passed.

---
*Phase: 12-cgb-double-speed*
*Completed: 2026-10-13*
