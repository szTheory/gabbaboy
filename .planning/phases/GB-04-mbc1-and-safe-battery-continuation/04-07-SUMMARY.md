---
phase: GB-04-mbc1-and-safe-battery-continuation
plan: 07
subsystem: cartridge-and-battery-contract
tags: [MBC1, battery-save, documentation, evidence, phase-closeout]
requires:
  - phase: GB-04-mbc1-and-safe-battery-continuation
    provides: standard MBC1 implementation, bounded battery API, player persistence, and original continuation fixture
provides:
  - Public cartridge and battery-save contract linked from README and preview guidance
  - Evidence ledger mapping SAVE-01 through SAVE-04 to named tests and provenance classes
  - Phase validation record with local run counts and an explicit exact-head hosted gate
affects: [phase-verification, adopter-guidance, release-evidence]
actuals:
  tasks: 2
  commits: 2
tech-stack:
  added: []
  patterns: [evidence-classification, exact-head-ci-gate, privacy-safe-support-ledger]
key-files:
  created:
    - docs/cartridge-and-saves.md
    - docs/mbc1-evidence.md
  modified:
    - README.md
    - docs/preview.md
    - .github/workflows/preview.yml
    - .planning/phases/GB-04-mbc1-and-safe-battery-continuation/04-VALIDATION.md
requirements-completed: []
coverage:
  - id: D1
    description: Public support, ownership, persistence, recovery, and concurrency claims match the implementation and identify the supported software profile and exclusions.
    requirement: SAVE-01/SAVE-02/SAVE-03
    verification:
      - kind: integration
        ref: "docs/cartridge-and-saves.md; full core CTest 155/155 at 918ec265d1ab2a94292fe12c52a16563de8926b1; actionlint .github/workflows/preview.yml"
        status: pass
    human_judgment: false
  - id: D2
    description: The evidence ledger separates required cases, installed consumers, fixture provenance, software-model results, emulator comparisons, and absent physical observations.
    requirement: SAVE-01/SAVE-02/SAVE-03/SAVE-04
    verification:
      - kind: integration
        ref: "docs/mbc1-evidence.md; privacy and whitespace checks; exact hosted PR-head checks remain pending"
        status: pass
    human_judgment: false
  - id: D3
    description: Relocated consumers and the packaged macOS player resume the original fixture from saved progress in a fresh process.
    requirement: SAVE-02/SAVE-04
    verification:
      - kind: e2e
        ref: "verify-phase2-installed.sh: 160/160 relocated plus 155/155 core-only; verify-phase3-player.sh: 37/37 at 918ec265d1ab2a94292fe12c52a16563de8926b1; package SHA-256 dc2b8ebdeee56fb73a5d14bbfa5c2872ab2cfcbebd2180cd3740814fedded9d2"
        status: pass
    human_judgment: false
  - id: D4
    description: The original project-authored MBC1 fixture reproduces byte-for-byte with the pinned RGBDS archive and documented provenance.
    requirement: SAVE-04
    verification:
      - kind: integration
        ref: "RGBDS 1.0.1 macOS archive SHA-256 2f6f13c6ec984313656c07b08d97dfcd3a471c7d3901d3ff486e5814bb503645; fixture source and ROM digests recorded in docs/mbc1-evidence.md"
        status: pass
    human_judgment: false
duration: 18min
completed: 2026-10-08
status: complete
---

# Phase 4 Plan 07: Cartridge Contract and Evidence Ledger

## Outcome

Published the exact supported cartridge matrix, battery API ownership and
error contract, versioned save envelope, path identity, autosave cadence,
recovery behavior, and cooperating-process lock limit. Updated preview copy
and artifact capability metadata to describe the installed bootless DMG-CPU-B
core and battery API without implying that the package includes the SDL player
or save UI. Added a requirement-oriented evidence ledger and upgraded the
validation matrix from a planning contract to locally executed evidence.

## Task Commits

1. **Task 1: Document precise cartridge and battery contracts for adopters** —
   `918ec26` (`docs(04-07): publish cartridge and battery contract`)
2. **Task 2: Reconcile requirement traceability and current Phase 4 evidence** —
   `b9b0737` (`docs(04-07): record cartridge and battery evidence`)

## Test Results

- The phase1 core inventory passed **155/155** cases at source revision
  `918ec265d1ab2a94292fe12c52a16563de8926b1`.
- The relocated package verifier passed **160/160** cases, including external
  C and C++ consumers; its core-only subset passed **155/155** with no skips.
- The macOS player/package verifier passed **37/37** tests and confirmed
  fresh-process continuation from the extracted package. Candidate package
  SHA-256: `dc2b8ebdeee56fb73a5d14bbfa5c2872ab2cfcbebd2180cd3740814fedded9d2`.
- Pinned RGBDS 1.0.1 reproduced the original fixture byte-for-byte. Its archive,
  source, and ROM digests are recorded in the evidence ledger.
- `actionlint` passed for the preview workflow. Tracked and new-file whitespace
  checks passed, and a privacy scan found no local home paths or personal
  identifiers in the public evidence documents.
- This macOS host did not run Linux ASan/UBSan. Hosted exact-head checks and
  downloaded package receipts remain required before the phase can be marked
  complete. No physical MBC1/DMG observation or power-loss qualification is
  claimed.

## Decisions and Evidence Limits

- Keep the cartridge support statement scoped to the documented standard
  MBC1 matrix and the emulator's bootless software profile. The conservative
  MBC1M candidate check is not universal multicart detection.
- Distinguish synthetic software-model tests, original guest continuation,
  external installed consumers, and hosted sanitizer results. Emulator
  source agreement and fixture byte identity are not physical evidence.
- Process interruption covers named write stages; it does not establish
  storage behavior after power loss. CRC-32 detects accidental damage and is
  not authentication.
- GitHub triage on 2026-10-08 found no pre-existing open issues or pull
  requests. The new Phase 4 PR is created after all plan artifacts are
  committed.

## Requirement Traceability

This plan maps SAVE-01 through SAVE-04 to named executable cases and public
claims. Shared requirements remain unmarked as completed until the exact
hosted PR head, sanitizer lane, and package receipts are inspected during phase
verification.

## Next

Open the Phase 4 PR and inspect the exact-head hosted gates, then run phase
verification. The phase boundary remains in force; after Phase 4 is complete,
stop before Phase 5 — DMG Audio and Stable Playback. Its discussion command is
`$gsd-discuss-phase 5`.

---
*Phase: GB-04-mbc1-and-safe-battery-continuation*
*Completed: 2026-10-08*
