---
phase: 14-cgb-e-model-qualification-and-corpus
plan: "08"
subsystem: testing
tags: [age, rgbds, fixtures, provenance, cgb-e]
requires:
  - phase: 14-05
    provides:
      - Frozen AGE mode-3 source and reference selection at the pinned upstream tree
provides:
  - Six source-bound AGE mode-3 ROM and PNG admissions
  - Closed manifest validation and pinned ROM/image reproduction checks
affects:
  - 14-09
  - 14-11
  - 14-12
actuals:
  tokens: 13861
  tasks: 2
  commits: 2
commits: 2
plan_head_before: b04f2378d8a4f931006d90b7415262a432baaf22
plan_head_after: cbb8158aeddfbd02569e4809bf36d85b4acd1f75
tech-stack:
  added: []
  patterns:
    - Independent expected identities for each pinned ROM, ASM source, and reference PNG
    - Offline digest checks plus exact pinned-source rebuild and image comparison
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
  modified:
    - fixtures/age/manifest.json
    - fixtures/age/SOURCES.md
    - fixtures/age/ELIGIBILITY.md
    - tests/scripts/reproduce-age.sh
    - tests/scripts/test-reproduce-age.sh
key-decisions:
  - CGB-E author Verified lines remain independent expectations; fixture admission does not imply emulator execution or a passing pixel result.
  - Native CGB, CGB-E DMG compatibility mode, and double-speed cases retain separate identities.
patterns-established:
  - The AGE reproducer checks a closed source and image mapping against independent expected values.
  - The report keeps six admitted-but-not-executed targets separate from future pixel outcomes.
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
duration: 10min
completed: 2026-10-15
status: complete
---

# Phase 14 Plan 08: AGE Mode-3 Source and Reference Admission Summary

**Six pinned AGE mode-3 ROMs and source PNGs are admitted with fail-closed RGBDS reproduction and separate CGB-E mode and speed identities.**

## Performance

- **Duration:** 10 minutes
- **Started:** 2026-10-15T18:06:29Z
- **Completed:** 2026-10-15T18:16:23Z
- **Tasks:** 2
- **Files modified:** 17

## Accomplishments

- Admitted six 32,768-byte ROMs from AGE commit `1f5bc10e2cb60b86c19f8d0287ff78f410c4f639`, each bound to its exact ASM source and reference PNG with source, output, and image byte counts and SHA-256 digests.
- Recorded four normal-speed targets across native CGB and CGB-E DMG compatibility modes, plus two separately identified native double-speed siblings. All six remain `admitted-not-executed` for the pixel checks owned by Plan 14-09.
- Extended the offline manifest gate and pinned RGBDS 1.0.1 reproducer to reject incorrect membership, mode labels, source/image mappings, bytes, and tool provenance.

## Verification

The exact planned verification command passed with the digest-verified RGBDS 1.0.1 macOS archive:

```text
bash tests/scripts/reproduce-age.sh --self-check && bash tests/scripts/test-reproduce-age.sh compare-tampered && bash tests/scripts/test-reproduce-age.sh selfcheck-tampered && bash tests/scripts/reproduce-age.sh --compare
```

The rebuild checked all 19 manifest ROMs, including the 13 previously admitted files, and reported `result=byte-identical`. All six reference images reported `result=reference-source-identical`. The negative controls produced these expected diagnostics:

- Rebuilt ROM mutation: `result=differs m3-bg-lcdc-cgbBCE.gb`.
- Traversal and malformed digest: `source_path-outside-allow-list`; `invalid-sha256-spsw-div-cgbBCE.gb`.
- Cross-pair reference, missing ROM, and altered PNG: `m3-reference-file-mismatch-m3-bg-lcdc-cgbBCE.gb`; `committed-file-missing-m3-bg-lcdc-cgbBCE.gb`; `committed-reference-digest-mismatch-m3-bg-lcdc-cgbBCE.gb`.
- Stale RGBDS archive pin, wrong compatibility mode, and omitted sibling: `RGBDS-build-pin-mismatch`; `m3-mode-mismatch-m3-bg-lcdc-nocgb-ncmBCE.gb`; `m3-manifest-membership-mismatch`.

The admitted set has 6 distinct ROM digests, 6 distinct ASM source digests, and 6 reference paths. Two SCX references at the pinned AGE commit have identical PNG bytes and therefore share digest `6895b6111d432ea5f0422991a1d7143f1fe133481e018b3c8652616af759085d`; their source paths and native speed identities remain separate. The mode counts are 4 native-CGB and 2 DMG-compatibility cases; the speed counts are 4 normal and 2 double speed.

## Task Commits

1. **Task 1: Tracer: one AGE ASM and PNG pair reproduces to admitted bytes** — `57b7d59` (`feat(14-08)`).
2. **Task 2: Expand the other five source/image pairs** — `cbb8158` (`feat(14-08)`).

## Files Created and Modified

- `fixtures/age/manifest.json` — independent output, source, image, model, mode, speed, and author-expectation records for the six additions.
- `fixtures/age/SOURCES.md` and `fixtures/age/ELIGIBILITY.md` — rights, exact source/image identities, admission status, and expectation boundaries.
- `tests/scripts/reproduce-age.sh` and `tests/scripts/test-reproduce-age.sh` — pinned rebuild, source-image byte checks, and positive and negative controls.
- Six ROMs and six reference PNGs under `fixtures/age/` — pinned upstream artifacts listed in the manifest.

## Decisions Made

CGB-E `Verified` lines are preserved as author expectations, with no physical hardware or emulator result inferred. Normal-speed compatibility cases use the CGB-E silicon model in DMG compatibility mode; double-speed siblings remain distinct inputs. CGB-10 remains open at the phase level until the corpus reporting plans complete, so this summary does not mark the requirement complete.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Preserve the exact upstream `Verified` wording**

- **Found during:** Task 1
- **Issue:** The initial source assertion expected a normalized `pass:` label, while the pinned AGE source records only the date and model. The source-bound verification correctly rejected that mismatch.
- **Fix:** Store and validate the exact author line from the pinned source.
- **Files modified:** `tests/scripts/reproduce-age.sh`, `fixtures/age/manifest.json`, `fixtures/age/SOURCES.md`.
- **Verification:** The full pinned-source rebuild and all negative controls passed.
- **Committed in:** `57b7d59`.

**Total deviations:** 1 auto-fixed bug.
**Impact on plan:** The correction made the author expectation more faithful to its source and did not change the selected corpus.

## Issues Encountered

The managed sandbox blocked direct writes to `.git` for the required plan-head ledger and index lock. The task commits were staged and committed through the authorized git path with hooks enabled; the task commit count and head range were measured from the persisted execution baseline. No hook bypass was used.

## User Setup Required

None - no external service configuration required.

## Next Plan Readiness

Plan 14-09 has six exact source-bound ROM/image pairs ready for its automated pixel oracle. This plan reports fixture identity and reproducibility only; it does not claim pixel matches, emulator execution, physical CGB-E qualification, or game-level support.

---
*Phase: 14-cgb-e-model-qualification-and-corpus*
*Completed: 2026-10-15*

## Self-Check: PASSED

- All 12 fixture outputs and the summary file exist.
- Task commits `57b7d59` and `cbb8158` are ancestors of the current branch head.
- The summary coverage script, CTest, and GSD coverage classifier all pass; both deliverables auto-pass without human judgment.
- No new stub patterns were found in the modified scripts, manifest, or eligibility/source documentation.
