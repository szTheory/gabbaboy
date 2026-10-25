---
phase: 13-cgb-hdma
reviewed: 2026-10-15T02:06:17Z
depth: standard
files_reviewed: 68
files_reviewed_list:
  - .gitattributes
  - .github/workflows/fixture-repro.yml
  - .github/workflows/preview.yml
  - .gitignore
  - README.md
  - cmake/P12Mutants.cmake
  - cmake/P13Mutants.cmake
  - cmake/PreviewPackageSmoke.cmake
  - cmake/RunInstalledConsumer.cmake
  - cmake/ScanForbiddenFixtures.cmake
  - docs/cgb-profile.md
  - docs/model-gates.md
  - docs/native-integration.md
  - docs/preview.md
  - docs/support/unreleased.md
  - fixtures/cgb-hdma/LICENSE.txt
  - fixtures/cgb-hdma/hblank.asm
  - fixtures/cgb-hdma/hblank.gb
  - fixtures/cgb-hdma/manifest.json
  - fixtures/magentests/ELIGIBILITY.md
  - fixtures/magentests/LICENSE.txt
  - fixtures/magentests/SOURCES.md
  - fixtures/magentests/hblank_vram_dma.gbc
  - fixtures/magentests/manifest.json
  - fixtures/samesuite/ELIGIBILITY.md
  - fixtures/samesuite/LICENSE.txt
  - fixtures/samesuite/gbc_dma_cont.gb
  - fixtures/samesuite/gdma_addr_mask.gb
  - fixtures/samesuite/hdma_lcd_off.gb
  - fixtures/samesuite/hdma_mode0.gb
  - fixtures/samesuite/manifest.json
  - src/core/gabbaboy.c
  - src/player/limitations.h
  - src/player/main.c
  - tests/CMakeLists.txt
  - tests/consumers/c/main.c
  - tests/consumers/cpp/main.cpp
  - tests/expected-tests.txt
  - tests/external/cgb-hdma-dispositions.json
  - tests/external/cgb-speed-dispositions.json
  - tests/fuzz_core.c
  - tests/player/CMakeLists.txt
  - tests/player/cgb_smoke.cmake
  - tests/player/claims_agree.cmake
  - tests/player/expected-tests.txt
  - tests/player/test_limitations.c
  - tests/scripts/cgb-hdma-prohibition.test.cjs
  - tests/scripts/phase13-handoff-continuity.test.cjs
  - tests/scripts/reproduce-cgb-hdma.sh
  - tests/scripts/reproduce-magentests.sh
  - tests/scripts/reproduce-samesuite.sh
  - tests/scripts/test_magentests_hdma_registration.py
  - tests/scripts/test_reproduce_magentests.py
  - tests/scripts/verify-cgb-hdma-claims.py
  - tests/scripts/verify-cgb-hdma-dispositions.py
  - tests/test_cgb_hdma.c
  - tests/test_cgb_hdma_internal.c
  - tests/test_cgb_hdma_partition.c
  - tests/test_cgb_partition.c
  - tests/test_cgb_speed_internal.c
  - tests/test_cgb_visibility.c
  - tests/test_magentests.c
  - tests/test_samesuite_hdma.c
  - .planning/phases/GB-13-cgb-hdma/verify-hdma-closure.py
  - .planning/phases/GB-13-cgb-hdma/verify-hdma-source-revision.py
  - .planning/phases/GB-13-cgb-hdma/COVERAGE.md
  - .planning/phases/GB-13-cgb-hdma/verify-uat-contract.py
  - tests/scripts/phase13-handoff-continuity.test.cjs
findings:
  critical: 2
  warning: 2
  info: 0
  total: 4
status: issues_found
---

# Phase 13: Code Review Report

**Reviewed:** 2026-10-15T02:06:17Z  
**Depth:** standard  
**Files Reviewed:** 65  
**Status:** issues_found

## Summary

Reviewed the 63 phase source, fixture, documentation, test, and workflow paths in the supplied scope, plus the two requested closure-checker scripts. Core HDMA admission, timing, address bounds, cancellation, PPU edge ordering, IRQ service, HALT behavior, and double-speed progression showed no concrete software-contract defect. One closure-checker flaw can accept incomplete or contradictory remote check evidence as green; the player help also retains the already-recorded dense claims paragraph warning. Binary fixture contents were checked through manifests and digests. Physical CGB-E remains `UNKNOWN/POLICY`, which is an explicit limitation rather than a software defect.

Task-level RED/GREEN evidence was checked against the recorded commit sequence. The malformed-subject event in Phase 13-12 is correctly classified as `INVALID_RED`, and commit `4eab951` adds preflight and controls so malformed setup cannot count as semantic fail-first evidence. The plan is `type: execute`, so the built-in TDD review reporting zero TDD plans is non-applicable and is not treated as TDD certification. The known pending rebind of historical BENCH source `690c081` is not reported as a new production finding.

## Critical Issues

### CR-01: Remote check evidence can pass with omitted, wrong-event, or contradictory results

**Classification:** BLOCKER  
**File:** `.planning/phases/GB-13-cgb-hdma/verify-hdma-closure.py:642-656`

**Issue:** `validate_remote_evidence` trusts the payload's nonempty `requiredJobs` list instead of comparing it with the authoritative required PR contexts, and it checks only `headSha`, `status`, and `conclusion`; a successful run for the same commit from a `push` or `workflow_dispatch` event therefore qualifies. It also builds `index` with a dictionary comprehension, so repeated rows for one job silently overwrite one another. I called this function directly with a passing `required-native` row only, omitting `fixture-repro` and `preview-package-smoke`; it accepted the record. It also accepted a failed `required-native` row followed by a successful duplicate. This allows the closure check to represent incomplete or conflicting remote evidence as green, contrary to the plan's exact-head PR-event requirement.

**Fix:** Derive or validate the exact required PR context set used by the repository evidence contract, require each result to identify the `pull_request` event and expected head, and reject duplicate or unrecognized result names. If reruns are retained, bind run IDs/attempts and select the latest result deterministically instead of allowing list order to decide.

## Warnings

### WR-01: Player help compresses support claims and exclusions into one hard-to-scan paragraph

**Classification:** WARNING  
**File:** `src/player/main.c:401`

**Issue:** The help line combines model selection, compatibility palette, color correction, audio, speed, DMA support, and mode-3, hardware, and compatibility limits in one semicolon-heavy paragraph. The claims are materially qualified and checked across surfaces; the issue is scanability, as already recorded by the Phase 13 UI review.

**Fix:** Split the help into short labeled lines such as `Models`, `Video`, `Audio`, `Transfers`, and `Limits`, keeping all current qualifications and updating the phrase contract in the same change.

---

_Reviewed: 2026-10-15T02:06:17Z_  
_Reviewer: the agent (gsd-code-reviewer)_  
_Depth: standard_

## Focused UAT automation review — 2026-10-15

The unchanged emulator/fixture scope retains the prior full review. Five automation files introduced by `e556c1b` were independently reviewed at standard depth (three new unique files; total union 68). Both findings below were fixed and independently reproduced as rejected at `0f1bb34`; no additional open findings remain.

### CR-UAT-01: Unparsed manual checkpoints escaped the UAT closure parser

**Classification:** BLOCKER. A scratch complete record containing an extra unnumbered `### Manual checkpoint` with pending/human fields was accepted as 45 passes. Fixed in `eeb1ce9`: require exactly sequential headings, no test prelude and only known row fields; 17 negative controls include unparsed/manual content. Independent re-review reproduced rejection at `0f1bb34`.

### WR-UAT-01: Conflicting or compound stage declarations permitted a stale route

**Classification:** WARNING. Substring matching accepted inconsistent current/completed fields, then prefix matching accepted a compound declaration with a stale verify-work route. Fixed in `eeb1ce9` and `0f1bb34`: one standalone normalized exact stage, matching STATE/continuation, and one exact stage-specific command. CJS controls reject both original counterexamples and the compound residual; the actual completed-UAT handoff passes. Independent re-review confirms all three bypasses closed.
