---
phase: GB-03-visible-interactive-dmg
plan: "08"
subsystem: fixture-reproduction
tags: [rgbds, provenance, sha256, github-actions]

# Dependency graph
requires:
  - phase: GB-03-visible-interactive-dmg
    provides: Original interactive demo ROM and pinned RGBDS 1.0.1 fixture path
provides:
  - Local source-to-byte reproduction with exact size, digest, and byte comparison
  - Pinned Linux RGBDS archive identity and source SHA in the fixture manifest
  - Exact-revision hosted receipt binding source, tool, archive, and ROM digests
affects: [GB-03-09, phase-3-verification]

# Actuals
actuals:
  tokens: 3920
  tasks: 2
  commits: 2

# Tech tracking
tech-stack:
  added: []
  patterns: [opt-in fixture reproduction, fail-closed run-scoped provenance receipt]

key-files:
  created:
    - tests/scripts/reproduce-visible-demo.sh
  modified:
    - fixtures/visible-demo/manifest.json
    - .github/workflows/fixture-repro.yml

key-decisions:
  - "Keep RGBDS outside ordinary builds; the opt-in reproducer checks all three tool versions and leaves only its task-owned temporary directory for cleanup."
  - "Record source, ROM, and Linux archive digests in the fixture manifest and bind hosted evidence to the exact checkout SHA and run attempt."
  - "Keep byte reproducibility separate from gameplay, PPU behavior, and physical-hardware applicability claims."

patterns-established:
  - "A fixture reproducer validates readable source identity, tool version, exact output size, digest, and full byte equality before reporting success."
  - "Hosted evidence is uploaded only after exact-revision checks pass and contains no runner path or machine identity."

requirements-completed: [VIDEO-05]

coverage:
  - id: D1
    description: "The authored visible-demo source rebuilds to the exact checked-in 32 KiB ROM with its manifest digest using pinned RGBDS 1.0.1."
    requirement: VIDEO-05
    verification:
      - kind: integration
        ref: "bash tests/scripts/reproduce-visible-demo.sh; local pinned macOS archive and fail-closed negative controls"
        status: pass
    human_judgment: false
  - id: D2
    description: "Fixture CI verifies the exact source revision and uploads a small receipt naming the run, RGBDS archive, source SHA, ROM size, and ROM SHA."
    requirement: VIDEO-05
    verification:
      - kind: integration
        ref: "https://github.com/szTheory/gabbaboy/actions/runs/37683636738 — fixture-repro passed on 53f9f56cacbe6676b2c0db1dddf12dd0e44fa4f3; uploaded receipt contents verified"
        status: pass
    human_judgment: false

# Metrics
duration: 12 min
completed: 2026-10-07
status: complete
---

# Phase GB-03 Plan 08 Summary

**The original interactive demo now reproduces byte-for-byte locally and in pinned fixture CI with an exact-revision identity receipt.**

## Performance

- **Duration:** 12 min
- **Started:** 2026-10-07T20:28:30Z
- **Completed:** 2026-10-07T20:40:21Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- Added an opt-in local script that checks RGBDS 1.0.1, validates source and manifest identity, builds in a private temporary directory, and requires a 32,768-byte output matching both the checked-in ROM and SHA-256.
- Recorded the assembly source digest and official Linux CI archive pin alongside the existing macOS archive pin, applicability, MIT rights, protocol, ROM digest, and build recipe.
- Extended fixture CI without removing tracer or Mooneye reproduction checks. The new lane checks the exact checkout revision, rejects empty evidence identities, and uploads only a run-scoped receipt after reproduction succeeds.
- Downloaded and verified the hosted receipt: it names source revision `53f9f56cacbe6676b2c0db1dddf12dd0e44fa4f3`, RGBDS 1.0.1, Linux archive SHA-256 `80a5cad8dae27e24e46a93041352c47cadbc165103983f41c2b3082c42f6dad9`, and ROM SHA-256 `38afb54b40f4b6612906c7a68e367199d8bff135508a39d7acdc996bf3d86530`.
- Confirmed ordinary offline CTest remains independent of RGBDS: the full inventory passed 132/132.

## Task Commits

1. **Task 1: Rebuild the demo from source and fail closed on any byte mismatch** — `291ccdc` (`chore(GB-03-08): add reproducible visible demo fixture check`)
2. **Task 2: Run the same fail-closed reproduction in pinned fixture CI** — `53f9f56` (`ci(GB-03-08): reproduce visible demo in pinned fixture CI`)

Plan metadata is recorded in the follow-up documentation commit.

## Files Created/Modified

- `tests/scripts/reproduce-visible-demo.sh` — pinned-version reproduction, exact byte/digest checks, exact-revision validation, and bounded receipt creation.
- `fixtures/visible-demo/manifest.json` — source and platform-specific RGBDS archive identities, recipe, and existing scope metadata.
- `.github/workflows/fixture-repro.yml` — pinned archive validation, exact-revision reproduction, and success-only receipt upload.

## Decisions Made

- Keep fixture generation opt-in; normal build and CTest continue using checked-in bytes without network access or an assembler dependency.
- The checked-in demo remains project-authored MIT material and a bootless DMG-CPU-B fixture. Reproducible bytes establish source identity only, not gameplay correctness or physical hardware behavior.

## Deviations from Plan

None. The existing source and rights notice already met the plan; the manifest now records the source digest and Linux CI archive pin, while the unchanged MIT notice remains checked by the reproducer.

## Issues Encountered

- This arm64 macOS host cannot execute the Linux CI tool archive. The local check used the already pinned universal macOS RGBDS archive; hosted CI verified the pinned Linux archive and exact receipt on the same source revision.
- Negative controls confirmed that an RGBDS version mismatch and a one-byte rebuilt-ROM mutation both fail closed. Temporary-directory cleanup was also verified.

## User Setup Required

None. RGBDS is needed only when explicitly running the fixture reproduction script.

## Next Phase Readiness

Plan 03-09 owns exact-revision macOS preview package qualification. Phase 3 remains open: VIDEO-02 simultaneous PPU/DMA applicability, D-08 JOYP interrupt behavior, live desktop perception, and physical DMG-CPU-B evidence remain unresolved or unavailable. VIDEO-05 remains pending until the package lane is complete and phase traceability is verified.

---
*Phase: GB-03-visible-interactive-dmg*
*Completed: 2026-10-07*

## Self-Check: PASSED

- All created key files exist, and the Plan 03-08 commit scope resolves to both task commits.
- The local reproducer passed; wrong-version and mutated-byte negative controls failed as intended; temporary build output was removed.
- The full offline CTest inventory passed 132/132.
- Hosted fixture-repro passed on exact source SHA `53f9f56cacbe6676b2c0db1dddf12dd0e44fa4f3`, and the uploaded run-scoped receipt was downloaded and checked field-by-field.
