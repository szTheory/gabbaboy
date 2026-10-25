---
phase: 07-dmg-game-acceptance-and-regression-baseline
plan: 04
subsystem: testing
tags: [libbet, reproducibility, rgbds, pillow, github-actions, provenance]

requires:
  - phase: 07-dmg-game-acceptance-and-regression-baseline
    provides: "Plan 07-01 Libbet admission, manifest closure and --derive-closure verifier"
provides:
  - "Registry-verified, hash-pinned Libbet rebuild-and-compare script"
  - "Opt-in workflow_dispatch-only libbet-repro workflow"
  - "Recorded local byte-identical reproduction in fixtures/libbet/SOURCES.md"
affects: [GB-07 acceptance gate, release evidence]

actuals:
  tokens: 9000
  tasks: 2
  commits: 2

plan_head_before: 97cb9871adb2dbcc916557613917bbb9c4d0df14
plan_head_after: 5784d97a2e5de9472c2749af21e348f4c82748c6

tech-stack:
  added: []
  patterns: ["fail-closed provenance check against PyPI JSON and GitHub release API before any install", "opt-in non-required reproduction job separate from required CI"]

key-files:
  created:
    - tests/scripts/reproduce-libbet.sh
    - tests/scripts/libbet-repro-requirements.txt
    - .github/workflows/libbet-repro.yml
  modified:
    - fixtures/libbet/SOURCES.md

key-decisions:
  - "Pillow hashes cover CPython 3.10-3.14 manylinux x86_64 and macOS arm64 wheels so the ubuntu-22.04 runner and the local host both resolve under --require-hashes"
  - "GitHub reports no digest for the RGBDS 0.7.0 assets, so the D-02 SHA-256 pin on the downloaded archive is the binding check; the API check confirms asset name and URL prefix"
  - "No hosted reproduction run is claimed; hosted_run_url stays null until the workflow exists on the default branch and is dispatched"

requirements-completed: [GAME-01]

coverage:
  - id: D1
    description: "Provenance-checked pinned rebuild reproduces vendored Libbet ROM byte-identically locally"
    requirement: GAME-01
    verification:
      - kind: integration
        ref: "bash tests/scripts/reproduce-libbet.sh --compare"
        status: pass
    human_judgment: false
  - id: D2
    description: "libbet-repro workflow is dispatch-only, read-only, secret-free and absent from ci.yml and fixture-repro.yml"
    requirement: GAME-01
    verification:
      - kind: other
        ref: "plan acceptance checks (python3 -I trigger/permission checks, git diff --quiet PLAN_BASE..HEAD on fixture-repro.yml and ci.yml)"
        status: pass
    human_judgment: false
  - id: D3
    description: "SOURCES.md records the local result and states that no hosted run exists"
    requirement: GAME-01
    verification:
      - kind: unit
        ref: "python3 -I tests/scripts/verify-libbet-admission.py"
        status: pass
    human_judgment: false

duration: 20min
completed: 2026-10-10
status: complete
---

# Phase 07 Plan 04: Libbet Reproduction Summary

**Fail-closed, hash-pinned RGBDS 0.7.0 + Pillow 12.3.0 rebuild of pinned Libbet commit 46a765a that reproduces the vendored ROM byte-identically locally, wired into a dispatch-only workflow, with no hosted run claimed.**

## Performance

- **Duration:** about 20 min
- **Completed:** 2026-10-10
- **Tasks:** 2
- **Files modified:** 4 (3 created, 1 modified)
- **PLAN_BASE:** `97cb9871adb2dbcc916557613917bbb9c4d0df14`

## Accomplishments

- `tests/scripts/reproduce-libbet.sh --compare` verifies provenance first (every pinned Pillow hash is a published PyPI digest; the RGBDS archive is a published `gbdev/rgbds` v0.7.0 asset under the official download prefix), verifies the archive SHA-256 before extraction, installs with `pip --require-hashes --no-deps`, checks out and verifies the pinned commit, runs `--derive-closure` (files=45) before `make`, and compares bytes. It never writes inside the repository.
- Local run (macOS arm64, RGBDS 0.7.0 under Rosetta, Pillow 12.3.0 cp314 wheel, Python 3.14.4): exit 0, `libbet reproduction: identical sha256=3607412031c8287cf878299ce96e581e85b852dde703806343b95576fa3ff1a9`.
- `.github/workflows/libbet-repro.yml`: `workflow_dispatch` only, `contents: read`, no secrets, checkout pinned to the SHA already used in `fixture-repro.yml`; `ci.yml` and `fixture-repro.yml` untouched.
- `fixtures/libbet/SOURCES.md` records the local result, provenance URLs, commands and the absence of a hosted run (D-03), and restates that RGBDS 1.0.1 cannot build this tag.

## Task Commits

1. **Task 1: provenance-checked rebuild script, requirements, workflow** - `1d4eb86` (feat)
2. **Task 2: SOURCES.md reproduction statement** - `5784d97` (docs)

## Decisions Made

See key-decisions. The only plan-adjacent judgment: the GitHub release API reported no `digest` field for the RGBDS assets, so that optional comparison was inert and the D-02 archive pin carries the integrity check (the macOS pin was additionally confirmed by independent download here).

## Deviations from Plan

None - plan executed exactly as written. The Linux path (archive pin, Linux wheel hashes) is configured but was not exercised locally.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Known Stubs

None.

## Threat Flags

None.

## Next Phase Readiness

Opt-in reproduction is available. A hosted Linux run requires the workflow to exist on the default branch first; promoting it to a required check is a deferred owner choice.

## Self-Check: PASSED

Files exist (script, requirements, workflow, SOURCES.md); commits `1d4eb86` and `5784d97` are on the branch; verify command and acceptance criteria re-run and passing.
