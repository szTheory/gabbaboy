---
phase: 13-cgb-hdma
plan: "06"
subsystem: testing
tags: [cgb, hdma, samesuite, rgbds, fixtures]
requires:
  - phase: 13-01
    provides: Pinned fixture provenance and CGB HDMA test conventions
provides:
  - Four digest-pinned SameSuite CGB DMA ROMs with X11/G7 and CC0 include rights recorded
  - Isolated RGBDS 1.0.1 reproduction, exact-set self-checks, and provenance negative controls
  - Eligibility record that preserves the D-06/Pan Docs conflict and hardware evidence limits
affects: [13-03, 13-09, CGB-07, fixture-repro]
actuals:
  tokens: 41929
  tasks: 2
  commits: 4
commits: 4
plan_head_before: fb1d96812d345a4d67b916b3af40a8cb77087ee1
plan_head_after: 3f6f58e5bc463e339157e6c89b22e8f5dba6802b
tech-stack:
  added: []
  patterns:
    - RGBDS 1.0.1 archives are digest-verified and extracted into isolated temporary tool/build directories
    - Default reproduction requires the complete approved fixture set; --case is admission-only
key-files:
  created:
    - fixtures/samesuite/manifest.json
    - fixtures/samesuite/LICENSE.txt
    - fixtures/samesuite/ELIGIBILITY.md
    - fixtures/samesuite/gbc_dma_cont.gb
    - fixtures/samesuite/gdma_addr_mask.gb
    - fixtures/samesuite/hdma_lcd_off.gb
    - fixtures/samesuite/hdma_mode0.gb
    - tests/scripts/reproduce-samesuite.sh
  modified:
    - .github/workflows/fixture-repro.yml
key-decisions:
  - Only gbc_dma_cont, gdma_addr_mask, hdma_lcd_off, and hdma_mode0 are admitted from SameSuite revision f15645fb049a47ea235f6d2c9a033e72d8087901.
  - D-06 author-encoded expectations remain unchanged and do not establish physical CGB-E behavior.
patterns-established:
  - SameSuite manifest rows pin the full assembly include closure, rights basis, tool archives/options, model applicability, and byte digests.
  - The existing fixture-repro job runs the full-set default and compare-built path without adding jobs or dependencies.
requirements-completed: []
coverage:
  - id: D1
    description: Four approved SameSuite DMA ROMs and their complete source/license provenance reproduce byte-identically.
    human_judgment: false
    verification:
      - kind: integration
        ref: bash tests/scripts/reproduce-samesuite.sh --compare-pinned
        status: pass
      - kind: unit
        ref: bash tests/scripts/reproduce-samesuite.sh --self-check
        status: pass
  - id: D2
    description: Provenance, exact-set, D-06 expectation, and rebuilt-byte mutations are rejected with specific diagnostics.
    human_judgment: false
    verification:
      - kind: unit
        ref: bash tests/scripts/reproduce-samesuite.sh --self-test
        status: pass
  - id: D3
    description: The existing fixture-repro job requires the full SameSuite set, its pinned RGBDS archive, and independent build comparison.
    human_judgment: false
    verification:
      - kind: integration
        ref: bash tests/scripts/reproduce-samesuite.sh
        status: pass
      - kind: other
        ref: .github/workflows/fixture-repro.yml#Reproduce all approved SameSuite DMA fixture bytes; workflow job-set and pin-parser contract
        status: pass
  - id: D4
    description: Eligibility records rights, bootless software-model applicability, the retained D-06/Pan Docs conflict, and the absence of physical CGB-E proof.
    human_judgment: false
    verification:
      - kind: unit
        ref: bash tests/scripts/reproduce-samesuite.sh --self-check && bash tests/scripts/reproduce-samesuite.sh --self-test
        status: pass
duration: 13 min
completed: 2026-10-14
status: complete
---

# Phase 13 Plan 06: SameSuite CGB DMA Admission Summary

**Four rights-qualified SameSuite CGB DMA ROMs rebuild byte-identically with the pinned RGBDS 1.0.1 toolchain.**

## Performance

- **Duration:** 13 min
- **Started:** 2026-10-14T19:43:44Z
- **Completed:** 2026-10-14T19:57:05Z
- **Tasks:** 2
- **Files modified:** 9

## Accomplishments

- Admitted exactly `gbc_dma_cont`, `gdma_addr_mask`, `hdma_lcd_off`, and `hdma_mode0` from SameSuite revision `f15645fb049a47ea235f6d2c9a033e72d8087901`.
- Pinned each ROM, source file, include, license notice, RGBDS archive, options, model label, and bootless applicability in the manifest.
- Wired the existing fixture-repro job to run the full-set default, pinned rebuild, and independent `--compare-built` check.

## Task Commits

Each task followed a RED/GREEN commit pair. These numbered rows are the machine-readable task commit references used by the scope parser.

1. **Task 1: Tracer: reproduce and validate one admitted SameSuite ROM** — `82b067c` (RED), `903dfff` (GREEN).
2. **Task 2: Expand exactly the remaining three admitted cases and recurring rebuild lane** — `4938d21` (RED), `3f6f58e` (GREEN).

| Task | RED commit | GREEN commit | Result |
|---|---|---|---|
| 1 | `82b067c` | `903dfff` | First pinned `gbc_dma_cont` fixture and isolated reproducer |
| 2 | `4938d21` | `3f6f58e` | Exact four-case set, eligibility ledger, full CI path |

## TDD Evidence

- **Task 1: RED:** `test_gbc_dma_cont_is_pinned_and_committed` failed on the intended missing-manifest-row assertion; `gsd-tools check tdd-red-evidence` returned `RED_EVIDENCE_OK`. GREEN passed selected-case self-check, clean-copy positive control, all provenance mutations, and the pinned byte comparison.
- **Task 2: RED:** `test_exact_four_cases_and_roms_are_admitted` failed on the intended exact-set assertion while only the tracer row existed; the classifier returned `RED_EVIDENCE_OK`. GREEN passed with all four rows and ROMs present.
- The temporary RED predicates and evidence records were removed after their GREEN commits. The committed reproducer retains the ongoing positive and negative controls.

## Reproduction Evidence

The final default run, `--compare-pinned`, and independent `--compare-built` run all reported byte-identical output for all four cases. The build used the isolated macOS RGBDS 1.0.1 archive SHA-256 `2f6f13c6ec984313656c07b08d97dfcd3a471c7d3901d3ff486e5814bb503645`; CI checks the Linux archive SHA-256 `80a5cad8dae27e24e46a93041352c47cadbc165103983f41c2b3082c42f6dad9` in the existing fixture-repro job.

| Case | Size | ROM SHA-256 |
|---|---:|---|
| `gbc_dma_cont` | 32768 | `cd20f67ff24d4cc90815bdd9b2c41bbeec5ec9a8abedb949f2fc704ff6d61512` |
| `gdma_addr_mask` | 32768 | `d409c95ddf291c2d9debc0fc3f9bf0d49b24adbcef7f560aa2ae8f6e8299e5f3` |
| `hdma_lcd_off` | 32768 | `637a3612dcb99bd5f2b0739fb31ad26ce390361e6878b193b894b40f882e44eb` |
| `hdma_mode0` | 32768 | `53f8d643548cecfc8ba5bd03721e4609571fa6a5ac383c96a2342b058fb5f2a1` |

The self-test passed clean temporary-copy validation and rejected missing license, changed ROM digest, changed source digest, wrong source revision, wrong RGBDS pin, an extra case row, a changed D-06 expectation, and tampered rebuilt bytes with the named provenance diagnostic.

## Files Created/Modified

- `fixtures/samesuite/manifest.json` — exact source closure, build/tool pins, rights, model applicability, and ROM digests.
- `fixtures/samesuite/LICENSE.txt` — pinned SameSuite X11 license plus the included hardware definitions' CC0-1.0 notice excerpt.
- `fixtures/samesuite/ELIGIBILITY.md` — four-case scope, G7/CC0 rights basis, D-06 contradiction, and evidence limits.
- `fixtures/samesuite/*.gb` — the four pinned ROM artifacts.
- `tests/scripts/reproduce-samesuite.sh` — offline checks, negative controls, and isolated pinned/independent builds.
- `.github/workflows/fixture-repro.yml` — full-set reproduction in the existing job with the existing RGBDS 1.0.1 pin.

## Decisions Made

- The manifest admits only the four cases named by D-16; the `--case` option is an admission-stage selector, while default and CI require the complete set.
- The `hdma_lcd_off` and `hdma_mode0` author-expected `$83 → $02 → $00 → $80` sequence remains unchanged despite the retained Pan Docs conflict.
- ROM reproduction proves provenance and bytes only. It is not a core pass and provides no independent physical CGB-E evidence.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Corrected SameSuite source-path selection and source-check argument binding**
- **Found during:** Task 1
- **Issue:** The include-closure builder selected applicability text as a source path, and the pinned-source checker read the script path from the wrong argument position.
- **Fix:** Derive each assembly path from its approved case alias and pass the pinned source directory through the correct argument slot.
- **Files modified:** `tests/scripts/reproduce-samesuite.sh`
- **Verification:** Selected-case self-check, provenance self-test, and pinned RGBDS 1.0.1 rebuild all passed.
- **Committed in:** `903dfff`

**2. [Rule 1 - Bug] Made eligibility checks tolerant of Markdown line wrapping**
- **Found during:** Task 2
- **Issue:** A required eligibility phrase split across a Markdown newline was falsely reported missing.
- **Fix:** Normalize whitespace before checking required provenance terms and add a negative control for changed D-06 expectations.
- **Files modified:** `tests/scripts/reproduce-samesuite.sh`
- **Verification:** Full-set self-check and self-test passed, including the changed-D-06 negative control.
- **Committed in:** `3f6f58e`

**Total deviations:** 2 auto-fixed (Rule 1: 2).
**Impact on plan:** Both fixes strengthen the planned provenance checks; no core code, dependency, CTest inventory, or workflow job was added.

## Issues Encountered

- The repository's general `*.gb` ignore rule excludes fixture ROMs by default. The four explicitly licensed and digest-pinned SameSuite ROMs were force-added individually; no ignore policy was changed.

## User Setup Required

None.

## Next Phase Readiness

Plan 13-06 execution is complete. Phase 13 remains active and CGB-07 remains open. Continue with **Phase 13 plan 13-03 execution — Real HALT wake and independent competing stalls** using `/gsd-execute-phase 13`. Phase 14 remains unstarted.

## Self-Check: PASSED

All nine plan deliverables exist, all four task commits are ancestors of HEAD, coverage classification reports all four deliverables auto-covered, and `git diff --check` passes.

---
*Phase: 13-cgb-hdma*
*Completed: 2026-10-14*
