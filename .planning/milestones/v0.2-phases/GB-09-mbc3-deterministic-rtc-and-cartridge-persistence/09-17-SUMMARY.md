---
phase: 09-mbc3-deterministic-rtc-and-cartridge-persistence
plan: 17
subsystem: docs
tags: [docs, evidence-ledger, capability-text, mbc3, rtc, persistence]
requires:
  - phase: 09-14
    provides: installed C/C++ RTC consumers and the host integration guide section
  - phase: 09-15
    provides: loader contradiction matrix and RTC mutation controls
  - phase: 09-16
    provides: catch-up on reopen, --clock-unix scope, fresh-process continuation
provides:
  - "docs/mbc3-rtc-evidence.md: MBC3/RTC evidence ledger citing 104 registered test names with evidence classes"
  - "docs/cartridge-and-saves.md: MBC3 matrix and mapper, clock model, timer battery image and block, catch-up, envelope v2, reopen policy"
  - "Public capability text (README, preview guide, preview.yml capability_limits, unreleased support ledger, CHANGELOG) matching the shipped scope"
affects: [09-18]
key-files:
  created:
    - docs/mbc3-rtc-evidence.md
  modified:
    - docs/cartridge-and-saves.md
    - docs/mbc2-mbc5-evidence.md
    - docs/native-integration.md
    - README.md
    - docs/preview.md
    - .github/workflows/preview.yml
    - docs/support/unreleased.md
    - CHANGELOG.md
key-decisions:
  - "Reproduction of the third-party ROMs is recorded as pending: the hosted magentests-repro and rtc3test-repro jobs reported success at 2b4c220 but the byte-identical claim is made only from a result line at the final evidence head (Plan 09-18)"
requirements-completed: [CART-05, CART-06, RTC-01, RTC-02, RTC-03]
status: complete
commits: 2
plan_head_before: ee8540c77114c5ee47b8b71db0536aa5a827ae16
plan_head_after: b339a72a63c5d035737ea0687ea7f9c331d63de5
actuals:
  tokens: 40000
  tasks: 2
  commits: 2
duration: 60 min
completed: 2026-10-12
coverage:
  - id: D1
    description: Evidence-ledger name inventory and native integration RTC contract
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest --test-dir build --output-on-failure --no-tests=error -R '^(mbc3_rtc_evidence_ledger_names|mbc3_rtc_evidence_ledger_selftest|native_guide_rtc_contract)$'"
        status: pass
---

# Phase 9 Plan 17: Evidence ledger, contract docs and capability text Summary

The MBC3/RTC evidence ledger cites 104 registered CTest names with their evidence class (hardware-derived author-attested, original differential/metamorphic/regression, project decision), the cartridge-and-saves contract now documents the timer battery image, block layout, catch-up, envelope v2 and the reopen policy, and every public capability sentence names MBC3 and four-mapper player persistence without a hardware or game claim.

## Accomplishments

- **Ledger (`docs/mbc3-rtc-evidence.md`).** Claim tables for mapping and variants, MagenTests (with the negative control), the RTC model rows, rtc3test (marker frames 749/496/1561, green counts 36/28/57, millisecond fields equal to `tests.md`), the five RTC mutants with paired controls, the no-host-clock proof with the per-leg lines read from CI run 38180044966, the battery block and catch-up, the player envelope and reopen policy, continuation fixtures with their ROM digests, the loader matrix (1344/3360/4032 cases) and fuzz seeds. It states the ROM code `$07` MBC30-slot note, the D-26 placement deviation (`catch_up_policy_table` in the core inventory), the pending reproduction status and the limits.
- **Contract (`docs/cartridge-and-saves.md`).** MBC3 rows, the MBC30 rule and error table, MBC3 write decode, an "MBC3 real-time clock" section, the timer battery image wording ($0F block only), the 21-byte block table and its error table, "import never catches up", `gbb_rtc_catch_up` semantics and when to call it, the BGB/VBA-M interop note, the `-mbc1-` versus `-cart-` file names, the 64-byte v2 envelope (CRC covers the header and is not authentication), the reopen policy table, the paused-time limitation and the `--clock-unix` scope. The old "Player support for MBC2 and MBC5" section is replaced.
- **Capability text.** README, `docs/preview.md` (including the stale 2 MiB bound and MBC1-only wording), both `preview.yml` `capability_limits` strings, `docs/support/unreleased.md` (new Phase 9 section; Phase 8 persistence-gap and 2 MiB lines marked as closed or raised) and an Unreleased CHANGELOG entry listing `gbb_rtc_catch_up`, `GBB_NO_RTC`, `GBB_RTC_BLOCK_SIZE`, the timer battery image, envelope v2 and the D-17 veto note.

## Facts verified against code before writing

- `PLAYER_SESSION_MAX_ROM_SIZE` is 8 MiB and `PLAYER_SESSION_MAX_RAM_SIZE` is 131072 (`src/player/session.c`); the v2 maximum is 64 + 131072 + 21 = 131157 bytes.
- File name suffix is `-mbc1-%02x-%08x.gbb` for type `$03` and `-cart-%02x-%08x.gbb` otherwise.
- `catch_up_policy.c` status strings and the delta clamp match the reopen table; `limitations.h` already carries the paused-time sentence.
- `--clock-unix` is accepted only as argv[3..4] of the battery smoke modes (`main.c`).
- `GBB_RTC_BLOCK_SIZE` is 21 and the header comments match the block table written here.

## Task Commits

1. Task 1 (tracer): `8d2a1e0` ledger, contract, MBC2/MBC5 limits pointer, integration-guide ROM bound
2. Task 2: `b339a72` capability text and support ledger

## Verification

- Task 1 gate: ledger name check passed (104 distinct names, none missing from either inventory); `GBB_RTC_BLOCK_SIZE` and the ledger link present; acceptance counts met (`hardware-derived` 4, import-never-catches-up line 1, `GBRT` present).
- Task 2 gate: `verify-support-ledger.py --self-test` passed, `actionlint` clean, `git grep 'MBC1 type \$03 only'` prints nothing, both greps pass.
- Full build and CTest 401/401; `verify-test-inventory.sh build/ctest.xml tests/expected-tests.txt --installed` verified 401 executed cases, none skipped.
- `bash tests/scripts/verify-phase3-player.sh --build-package` passed (player tests, package smoke, extracted-byte smoke).
- Nothing pushed; stash count still 1; `.planning/milestone.lock` untouched.

## Deviations from Plan

**1. [Rule 2 - Missing] `docs/native-integration.md` ROM bound.** The stale sentence ("up to 8 MiB for MBC5 and 2 MiB for every other type") contradicted the new MBC3 4 MiB ceiling, so I corrected it. The file is not in the plan's `files_modified`.

**2. [Rule 2 - Missing] Phase 8 lines in `docs/support/unreleased.md`.** The Phase 8 section said the player file bound stays 2 MiB and that MBC2/MBC5 saving was planned; I rewrote those two bullets as closed or raised by Phase 9 rather than leave a contradiction.

**3. CART-04 not marked complete here.** `requirements.ready-ids` did not report CART-04 as ready, so only CART-05, CART-06 and RTC-01..03 were passed to `requirements.mark-complete`.

## Known Stubs

None.

## Threat Flags

None. T-09-34 is mitigated by the evidence-class labels, the automated name check and the limits list; T-09-35 by the "import never catches up" statement in the contract and the installed consumers of Plan 09-14.

## Self-Check: PASSED

- docs/mbc3-rtc-evidence.md exists; commits 8d2a1e0 and b339a72 are ancestors of HEAD.

## Fresh Focused Evidence (15.1-12)

- The evidence-ledger name, evidence-ledger self-test, and native-guide contract CTests passed 3/3 in 0.08 seconds.
- The historical `verify-support-ledger.py --self-test` pass above was not reproduced at the current HEAD. The command exited 1 at `self-test tagged source differs from the tracked ledger:src/core/gabbaboy.c`; the current source bytes do not match the v0.2.0 ledger's recorded source input. This plan leaves the unowned ledger and checker unchanged; exact current source reconciliation remains unresolved for Plan 15.1-07. Earlier successful self-test output and hosted claims remain historical producer evidence.
