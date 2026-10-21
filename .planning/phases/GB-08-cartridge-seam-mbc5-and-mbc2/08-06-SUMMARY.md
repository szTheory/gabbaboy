---
phase: 08-cartridge-seam-mbc5-and-mbc2
plan: 06
subsystem: testing
tags: [mooneye, mbc5, mbc2, cmake, ctest, provenance, negative-controls]

requires:
  - phase: 08-cartridge-seam-mbc5-and-mbc2
    provides: 15 admitted Mooneye mbc2/mbc5 derivatives and the multi-suite runner (plan 08-05)
provides:
  - cmake/VerifyMooneyeMbc.cmake with digest, inventory and pc-table modes
  - 22 mooneye_mbc_ CTests including per-case receipts and four fail-closed controls
  - SOURCES.md, ELIGIBILITY.md and a THIRD_PARTY_NOTICES.md row for the sibling set
affects: [08-07 hosted Linux digest match, installed/package inventory proof]

actuals:
  tokens: 9800
  tasks: 3
  commits: 3
plan_head_before: 5037043d49a1f5143514c17127e7f5ccaf6a18f3
plan_head_after: 0082ae26c03ba2dcd9044183cd20e7028069a8fc
commits: 3

tech-stack:
  added: []
  patterns:
    - "Runner-table agreement checked by CMake regex over one-row-per-line C initialisers between marker comments"
    - "Exact-exit-code controls through tests/expect_exit.cmake, with the control proven to fail when the guarded condition is absent"

key-files:
  created:
    - cmake/VerifyMooneyeMbc.cmake
    - fixtures/mooneye-mbc/SOURCES.md
    - fixtures/mooneye-mbc/ELIGIBILITY.md
  modified:
    - THIRD_PARTY_NOTICES.md
    - tests/CMakeLists.txt
    - tests/expected-tests.txt
    - tests/test_runner.c

key-decisions:
  - "Builder pin is read from the digest-checked parent manifest and the sibling manifest must carry no builder object (D-24: referenced, not copied)"
  - "Every runner test keeps TIMEOUT 30: measured wall time is at most 1.9 s (mbc2_bits_ramg 1.59 s in CTest), so none needs 120"
  - "type-mutation test runs the unmutated image first and requires pass, so the mutated non-pass is attributable to the type byte alone"

requirements-completed: [CART-02, CART-03]

duration: 30min
completed: 2026-10-11
status: complete
coverage:
  - id: D1
    description: "Digest, inventory and runner-PC agreement verifier"
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest --test-dir build -R ^mooneye_mbc_ --output-on-failure"
        status: pass
  - id: D2
    description: "15 per-case receipts and fail-closed manifest/type/PC controls"
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest --test-dir build -R ^mooneye_mbc_ --output-on-failure"
        status: pass
  - id: D3
    description: "Sibling fixture rights, eligibility and notices document the named software profile"
    human_judgment: false
    verification:
      - kind: other
        ref: "python3 -I tests/scripts/verify-phase8-closure-contract.py --self-test"
        status: pass
---

# Phase 8 Plan 06: Mooneye mbc2/mbc5 verifier, CTests and provenance Summary

**A three-mode fail-closed CMake verifier plus 22 mooneye_mbc_ CTests (suite 15/15, per-case receipts pinning callback and result PCs, tamper, unknown-manifest and mapper-type controls) and provenance, eligibility and notices documents bounded to a local-rebuild, no-compatibility claim.**

## Performance

- **Duration:** about 30 min
- **Completed:** 2026-10-11T15:19Z
- **Tasks:** 3
- **Files modified:** 7 (3 created, 4 modified)

## Accomplishments

- `cmake/VerifyMooneyeMbc.cmake`: digest mode checks sizes, SHA-256, path guards, the Mooneye revision and tree, three real `parent_references` files with their own digests, and the WLA-DX pin through the parent manifest; inventory mode pins mbc2=7, mbc5=8 and required_roms equal to the eligible set; pc-table mode compares every manifest field with the compiled `mbc_cases[]` rows.
- 22 new CTests: `mooneye_mbc_fixture_digest`, `_eligible_inventory`, `_pc_table`, `_pc_table_tamper`, `_required_suite`, `_unknown_manifest`, `_type_mutation`, and 15 `mooneye_mbc_case_<alias>`. Full local `ctest` (phase1 preset): 309/309 passed (287 before this plan + 22). The inventory check in configure agrees with `tests/expected-tests.txt` (22 added lines, zero removed or changed, `installed_` count unchanged at 6).
- ELIGIBILITY.md records the measured half-dot counts, host, method and final budgets from the 08-05 SUMMARY, the per-ROM PC table, and the D-30 evidence class (author-attested upstream hardware results, bootless DMG-CPU-B profile, no model or CGB claim, never game compatibility, MBC2A caveat, no MBC5 RAM or rumble coverage).
- THIRD_PARTY_NOTICES.md has a Mooneye mbc2/mbc5 row (MIT, revision, manifest SHA-256 `9800c795...5801`, LICENSE.txt SHA-256 `8a9a9fe1...ae88`, repository test fixtures only).

## Negative controls (each run and observed to fail closed)

| Control | Mutation | Observed |
|---|---|---|
| ROM byte appended | `mbc5_rom_1Mb.gb` +1 byte | digest: size 131073/131072 mismatch |
| Parent ref content | one byte appended to `headless-report.patch` | `parent-reference-digest: ../mooneye/headless-report.patch` |
| Parent ref missing | `font-source.c` removed | `parent-reference-invalid: ../mooneye/font-source.c` |
| Builder pin | parent manifest builder revision zeroed and its ref digest refreshed | `builder-pin-mismatch` |
| Inventory | required ROM dropped / extra name / mbc5 category 7 / empty fail PC list | each rejected with an `inventory:` message |
| pc-table tamper (CTest) | first `result_pc` changed in a copied manifest | `pc-table-mismatch ... result_pc`, exit 1; the same command on the untouched manifest makes `expect_exit` fail (control is not vacuous) |
| pc-table runner source | altered fail PC / budget / size / pass PC / source path in a scratch copy of `main.c` | `pc-table-mismatch` naming the field |
| Unknown manifest (CTest) | one appended space | runner prints `invalid-manifest`, exit exactly 2 |
| Type byte (CTest) | `$147` -> `$01`, header checksum recomputed | status `unsupported`, not `pass`; with the mutation replaced by a no-op (`$19`) the test fails (REQUIRE at the status line) |

## Task Commits

1. **Task 1: Tracer, provenance documents, notices row and digest verifier** - `b126ec7` (feat)
2. **Task 2: Inventory, pc-table, suite, per-case and control CTests** - `08fb22c` (feat)
3. **Task 3: Type-byte mutation control and 22-name inventory** - `0082ae2` (test)

## Deviations from Plan

**1. [Plan detail] Verifier modes committed together in Task 1**
- The file `cmake/VerifyMooneyeMbc.cmake` was written with all three modes before the Task 1 commit, so the inventory and pc-table code first appears in `b126ec7` while only `mooneye_mbc_fixture_digest` was registered there. Task 2 registered and exercised them (and refined the pc-table field attribution).

**2. [Plan detail] Count wording**
- Task 2 text says "append the 20 new names" while its acceptance criterion says 21 at that point; 21 is correct (6 verifier/suite/control tests plus 15 cases), and Task 3 adds the 22nd.

**3. [Plan addition] Unmutated baseline in the type-mutation test**
- The test first requires the admitted image to pass, then the mutated image to not pass, so the control cannot be satisfied by a broken fixture load.

**Total deviations:** 0 rule-based auto-fixes, 3 plan-detail notes. **Impact:** none on scope or requirements.

## Issues Encountered

- First pc-table field attribution grouped neighbouring columns, so a `result_pc` tamper was reported as `pass_callback_pc`; the checks were re-split so each field is named correctly (verified with scratch mutations).
- Mutating `$147` to `$1a` also yields non-pass (the RAM header mismatches), so it is not a valid proof that the control can fail; the no-op `$19` mutation was used instead.

## Verification

- `ctest -R '^mooneye_mbc_'`: 22/22; `-R '^(mooneye_|runner_|dmg_baseline)'`: 60/60; parent `mooneye_case_*` and `mooneye_required_suite` unchanged and passing; full suite 309/309.
- `bash tests/scripts/verify-dmg-baseline.sh`: `baseline status=pass`.
- No home paths in `fixtures/mooneye-mbc/*.md`, THIRD_PARTY_NOTICES.md or the verifier; `git check-attr text fixtures/mooneye-mbc/SOURCES.md` reports set.
- Not claimed: the digests are a Darwin local rebuild; the hosted Linux match, installed/package non-inclusion proof and exact-head CI are Plan 08-07.

## Known Stubs

None.

## Threat Flags

None. No new network endpoints, auth paths or runtime file access; the verifier only reads repository files.

## Next Phase Readiness

Plan 08-07 can read exact-head CI for 08-02..08-07 and record the hosted Linux digest match that SOURCES.md and ELIGIBILITY.md currently state as outstanding.

## Self-Check: PASSED

- Created files exist: `cmake/VerifyMooneyeMbc.cmake`, `fixtures/mooneye-mbc/SOURCES.md`, `fixtures/mooneye-mbc/ELIGIBILITY.md`.
- Commits `b126ec7`, `08fb22c` and `0082ae2` are ancestors of HEAD.
