---
phase: 12-cgb-double-speed
plan: 04
subsystem: fixtures
tags: [age, rgbds, provenance, cgb]
requires:
  - phase: 12-02
    provides: "Pinned AGE source, manifest-driven reproduction script and offline tamper controls"
provides:
  - "Thirteen admitted AGE ROM fixtures rebuilt from the pinned upstream tree"
  - "Per-ROM source paths, linker symbols, digests, Verified attestations and D-19 expected roles"
affects: [12-05, 12-09, 12-16]
actuals:
  tokens: 3422
  tasks: 2
  commits: 2
  plan_head_before: 0b0b8df0182f6dd31e6c7c79c0ee0ee8181329fb
  plan_head_after: ec5dc8ac17999c04bc66e43b0d1d0745262da15c
tech-stack:
  added: []
  patterns:
    - "AGE ROMs are rebuilt with digest-pinned RGBDS 1.0.1 and compared against manifest digests"
key-files:
  created:
    - fixtures/age/spsw-tima-cgbE.gb
    - fixtures/age/spsw-tima-cgbBC.gb
    - fixtures/age/spsw-stop-prefetch-cgbBCE.gb
    - fixtures/age/spsw-interrupts-cgbE.gb
    - fixtures/age/spsw-mode0-cgbBCE.gb
    - fixtures/age/spsw-ch2-lc-delay-cgbBCE.gb
    - fixtures/age/stat-mode-ds-cgbBCE.gb
    - fixtures/age/stat-mode-cgbE.gb
    - fixtures/age/stat-mode-sprites-ds-cgbBCE.gb
    - fixtures/age/stat-mode-sprites-dmgC-cgbBCE.gb
    - fixtures/age/stat-mode-window-ds-cgbBCE.gb
    - fixtures/age/stat-mode-window-cgbBCE.gb
  modified:
    - fixtures/age/manifest.json
    - fixtures/age/SOURCES.md
key-decisions:
  - "Preserved upstream Verified lines as author-attested hardware observations and encoded D-19 expected roles separately."
requirements-completed: [CGB-06]
coverage:
  - id: GB-12-04-01
    description: "The 13-ROM manifest has complete source, digest, linker-layout, attestation, and expected-role records, with no excluded or private files."
    requirement: CGB-06
    human_judgment: false
    verification:
      - kind: integration
        ref: "cmake -DMANIFEST=fixtures/age/manifest.json -P cmake/VerifyFixtureManifest.cmake"
        status: pass
      - kind: other
        ref: "Python manifest assertions; ROM-count, D-19 exclusion, and privacy scans"
        status: pass
  - id: GB-12-04-02
    description: "All admitted ROMs reproduce byte-identically with pinned RGBDS 1.0.1, and offline negative controls still detect fixture tampering."
    requirement: CGB-06
    human_judgment: false
    verification:
      - kind: integration
        ref: "PATH=<digest-pinned RGBDS 1.0.1> GBB_RGBDS_ARCHIVE=<verified macOS archive> GBB_RGBDS_ARCHIVE_SHA256=2f6f13c6ec984313656c07b08d97dfcd3a471c7d3901d3ff486e5814bb503645 bash tests/scripts/reproduce-age.sh --compare"
        status: pass
      - kind: unit
        ref: "bash tests/scripts/test-reproduce-age.sh compare-tampered"
        status: pass
      - kind: unit
        ref: "bash tests/scripts/test-reproduce-age.sh selfcheck-tampered"
        status: pass
      - kind: unit
        ref: "ctest --test-dir build -R '^summary_coverage$' --output-on-failure"
        status: pass
duration: 14 min
completed: 2026-10-13
status: complete
commits: 2
---

# Phase 12 Plan 04: Remaining AGE ROM fixture corpus Summary

All 13 D-19 AGE ROMs are now vendored with source provenance and expected roles, and rebuild byte-identically from the pinned upstream tree with digest-pinned RGBDS 1.0.1.

## Performance

- **Duration:** 14 min
- **Started:** 2026-10-13T17:28:35Z
- **Completed:** 2026-10-13T17:42:35Z
- **Tasks:** 2
- **Files modified:** 14

## Accomplishments

- Added the 12 remaining admitted ROMs and completed the manifest and source inventory with linker `.sym` addresses, SHA-256 digests, exact upstream `Verified:` lines, and the D-19 expected roles.
- Rebuilt all 13 fixtures from AGE commit `1f5bc10e2cb60b86c19f8d0287ff78f410c4f639`, tree `2fece1a678edb18c1664efd7328a430a79c70be4`, using the verified RGBDS 1.0.1 archive.
- Confirmed exclusions: no `_in-progress` or `m3-bg` ROMs and no `spsw-interrupts-cgbBC` bytes. Privacy scan found no personal home paths or Gmail addresses.

## Task Commits

1. **Task 1: CGB E TIMA tracer ROM and manifest row** - `6673c74` (`feat`)
2. **Task 2: Remaining 11 ROMs, provenance rows, and exclusions** - `ec5dc8a` (`test`)

## Verification

- `bash tests/scripts/reproduce-age.sh --self-check`: passed.
- `cmake -DMANIFEST=fixtures/age/manifest.json -P cmake/VerifyFixtureManifest.cmake`: passed for all 13 fixtures.
- `bash tests/scripts/reproduce-age.sh --compare`: all 13 ROMs passed byte-identical comparison using the verified RGBDS archive.
- `bash tests/scripts/test-reproduce-age.sh compare-tampered` and `selfcheck-tampered`: both offline negative controls passed.
- Manifest role and size assertions, 13-ROM inventory check, D-19 exclusion scan, and privacy scan passed.
- Hosted Linux rebuild remains unrun; this plan makes no hosted evidence claim.

## Decisions Made

- Upstream hardware `Verified:` lines are retained verbatim as source attestations; manifest expected roles describe D-19 expectations and are not emulator results.

## Deviations from Plan

None - plan executed as written.

## User Setup Required

None - local digest-pinned archive and network access to the pinned source were sufficient.

## Next Phase Readiness

The AGE corpus is ready for later budget measurement plans. Next within Phase 12 is plan 12-05, device scaling; this executor stops here.

## Self-Check: PASSED

- Both task commits are ancestors of the current plan head.
- All 14 declared artifacts exist and `summary_coverage` passed after this summary was written.

---
*Phase: 12-cgb-double-speed*
*Completed: 2026-10-13*
