---
phase: 08-cartridge-seam-mbc5-and-mbc2
plan: 09
subsystem: docs
tags: [docs, evidence-ledger, support-ledger, decisions, lessons]
requires: [08-04, 08-07, 08-08]
provides:
  - "docs/mbc2-mbc5-evidence.md requirement-to-evidence ledger (CART-01..03)"
  - "Public cartridge contract: type-aware ceiling, MBC2/MBC5 matrix, rumble query, MBC2 canonical battery image, player gap"
  - "Pending support-ledger section, package capability text, DECISIONS D-049..D-062, LESSONS GB-CART-001..006"
affects: [08-10]
key-files:
  created:
    - docs/mbc2-mbc5-evidence.md
  modified:
    - docs/cartridge-and-saves.md
    - docs/native-integration.md
    - docs/preview.md
    - README.md
    - docs/support/unreleased.md
    - .github/workflows/preview.yml
    - fixtures/mooneye-mbc/SOURCES.md
    - fixtures/mooneye-mbc/ELIGIBILITY.md
    - .planning/context/DECISIONS.md
    - .planning/context/LESSONS.md
    - .planning/context/FUTURE-MILESTONES.md
    - .planning/research/INDEX.md
key-decisions:
  - "D-062: ninth-bit discriminator is mbc5_bank_1ff plus unit tests, not Mooneye rom_64Mb (D-29 amendment recorded)"
requirements-completed: [CART-01, CART-02, CART-03]
status: complete
duration: 40 min
completed: 2026-10-11
commits: 2
plan_head_before: 83311772ed797010d06d2cad01f4fd3bcdfb4cbb
plan_head_after: 62638aceb36e6c3b06616e577c301ae452b52e5b
actuals:
  tokens: 40000
  tasks: 2
  commits: 2
coverage:
  - deliverable: "Public cartridge docs, README and preview text match Phase 8 behavior and limits"
    verification:
      - {kind: command, ref: "Task 1 automated verify and acceptance greps", status: pass}
    human_judgment: true
    rationale: "Prose accuracy is checked against the SUMMARYs and source by grep, not by a test that asserts the wording."
  - deliverable: "Support entry, capability text, decisions, lessons and deferred direction recorded"
    verification:
      - {kind: command, ref: "verify-support-ledger.py --self-test; actionlint preview.yml", status: pass}
    human_judgment: false
---

# Phase 8 Plan 09: Documentation and durable records Summary

One evidence ledger (`docs/mbc2-mbc5-evidence.md`) now maps CART-01..03 to executed test names, fixtures and evidence classes, and the public docs, package capability text, pending support entry and planning memory describe exactly what Plans 08-01..08-08 built, including the D-29 amendment and the player persistence gap.

## Accomplishments

- **Ledger:** CART-01 (differential cells=86016/85344/83328, differences=0, frozen digest `4c7a57ff3d50d228`), CART-02 (`mbc5_*`, Mooneye mbc5 8/8, `mbc5_banking_*`, `mbc5_bank_1ff`, the two real ninth-bit mutant tests), CART-03 (`mbc2_*`, Mooneye mbc2 7/7). Mooneye evidence class is author-attested hardware results run on the bootless DMG-CPU-B profile, with the MBC2A caveat and the hosted Linux 15/15 match (run 38151282870). The original fixture is described as an original software fixture plus synthetic oracle, not hardware evidence. Ninth bit: stated that no Mooneye mbc5 ROM (`rom_64Mb` included) selects banks 256 and above.
- **cartridge-and-saves.md / native-integration.md:** matrix rows for `$05/$06` and `$19-$1E`, type-aware 8 MiB / 2 MiB ceiling and the 8 MiB + 128 KiB allocation bound, MBC5 and MBC2 behavior, battery API for MBC2 (canonical 0xF0|nibble, normalising import, packed 256-byte unsupported; the stale "raw RAM bytes" wording corrected), rumble section and `gbb_rumble_state` bullet, player section naming the gap.
- **preview.md / README.md:** no longer MBC1-only; state that MBC2 `$06` and MBC5 `$1B/$1E` run without saving and that persistence is MBC1 type `$03` only (CART-06 is Phase 9).
- **Honest limitation:** 08-04's on-screen status line has no automated UI test (source branches plus the pinned limitations text only). This is stated in the player section, the ledger and the support entry; no manual UAT was created.
- **Support entry:** "Cartridge breadth (Phase 8)" in `docs/support/unreleased.md`, including the source-archive note (Open Question 3). `docs/support/v0.1.0.md` is untouched.
- **Records:** DECISIONS D-049..D-062 (Open Questions 1-7, D-08, D-10, A4, D-32, D-17, D-29 anchor, D-29 amendment), LESSONS GB-CART-001..006 (including the research-premise-versus-loop-bounds lesson from 08-07), FUTURE-MILESTONES deferred items, research INDEX bullet.

## Evidence

- `python3 -I tests/scripts/verify-support-ledger.py --self-test` passes; `git diff main...HEAD -- docs/support/v0.1.0.md` is empty.
- `actionlint .github/workflows/preview.yml` is clean; `grep -c 'standard MBC1, MBC2 and MBC5'` is 2.
- Task 1 acceptance greps: CART-0x count 4 (needs 3), "not game compatibility" 1, `8 MiB` 5, `512` 8, README `standard MBC1 battery-backed RAM` 0, `without saving` 3, home-path grep prints nothing.
- Task 2: DECISIONS has 14 new "Phase 8" rows (needs 12), none Pending; `Applies when` count 50 (44 before, plus 6); support ledger data block count 0.
- Local ctest subset (`cartridge_`, `mbc2_`, `mbc5_`, `mooneye_mbc`, `installed_`, `dmg_baseline`): 89/89 pass. The full suite was not rerun; this plan changes no code.

## Deviations from Plan

**1. [Rule 1 - Bug] Unescaped `$03` in preview.yml heredoc**
- **Found during:** Task 2 verify (actionlint reported shellcheck SC1037)
- **Issue:** `capability_limits` sits inside an unquoted shell heredoc, so the plan's literal "type $03" would have expanded to the script name plus `3` at runtime.
- **Fix:** wrote `\$03`, which the heredoc emits as a literal `$03`; actionlint is clean.
- **Files modified:** .github/workflows/preview.yml
- **Commit:** 62638ac

**2. [Rule 1 - Stale claim] fixtures/mooneye-mbc SOURCES.md and ELIGIBILITY.md**
- **Found during:** Task 1 (reading the provenance wording for the ledger)
- **Issue:** both still said the hosted Linux digest match and the package-inventory proof were pending Plan 08-07, which has since landed (run 38151282870 15/15; scans in 08-07).
- **Fix:** updated the two sentences to the measured outcome. Not in the plan's file list.
- **Files modified:** fixtures/mooneye-mbc/SOURCES.md, fixtures/mooneye-mbc/ELIGIBILITY.md
- **Commit:** 6d64b86

**3. [Orchestrator correction] Names and counts** — used the real mutant test names (`mbc5_ninth_bit_mutant_*`), 319 total tests and 21 `mbc5_` names rather than the plan's wording; added D-062 and GB-CART-002 for the D-29 amendment.

**Total deviations:** 2 auto-fixed, 1 orchestrator-directed wording change. **Impact:** none on scope.

## Known Stubs

None.

## Threat Flags

None. Documentation only; no new endpoints or file access.

## Self-Check: PASSED

- FOUND: docs/mbc2-mbc5-evidence.md, docs/cartridge-and-saves.md
- Commits 6d64b86 and 62638ac are ancestors of HEAD (`git rev-list --count` from the ledger base is 2).
