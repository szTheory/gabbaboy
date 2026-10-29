---
phase: GB-18-player-save-slots-and-host-contract
plan: "08"
subsystem: host-contract
tags: [host, save-format, contract, checker, completeness, freeze]
requires:
  - phase: GB-18-player-save-slots-and-host-contract
    provides: "18-01 host runner, bounded ROM reader and host_fixture write5a ROMs; 18-04 gabbaboy_host library and qualified-source list; 18-07 exit table in host_exit.h and the signal-stop runner"
provides:
  - "docs/host-contract.json: canonical hand-written host contract with exit_codes (4 rows), cadence (6 values), rtc_wall_clock not-recorded and save_formats (16 rows, 12 ids, no_battery_types)"
  - "host_save_format.c: the 16-row table and host_save_format_lookup / host_save_format_count"
  - "gabbaboy-runner --print-save-format --rom P [--profile dmg|cgb]: prints save_format=<id> bytes=<n>, or save_format=none bytes=0 for a no-battery cartridge; works on every platform; exits 2 with --save-dir or --frames"
  - "test_save_format_completeness: in-process enumeration of 256 types x 6 RAM codes x 9 ROM codes through gbb_probe_rom and gbb_battery_size (258 admitted combinations, 123 with a battery)"
  - "verify-save-formats.py --check | --check-print | --check-completeness | --freeze | --self-test and verify-host-contract.py --check | --self-test"
affects: [18-09]
actuals:
  tokens: 22000
  tasks: 3
  commits: 7
commits: 7
plan_head_before: 9ee054baf79eccb9878a8744e1f13f3e6955da2e
plan_head_after: c2239bef9dd83f3472cde554753e31e1548f00d8
tech-stack:
  added: []
  patterns:
    - "A published table is checked three ways: structurally (grammar, byte sum, same id same bytes, order), against the producer in both directions (core enumeration, runner print and produced files on both profiles), and against history (append-only vs the latest strict release tag)."
    - "A runner shim generated per control emulates the CLI from the contract rows with exactly one seeded defect, so each produced-file check fails for its own REJECT code."
    - "Canonical-JSON checking never re-sorts keys; a re-sorted copy is detected by key order (the sorted text is itself a valid canonical dump of the sorted document)."
key-files:
  created:
    - docs/host-contract.json
    - src/host/host_save_format.c
    - tests/test_save_format_completeness.c
    - tests/scripts/verify-save-formats.py
    - tests/scripts/verify-host-contract.py
    - tests/cmake/save-formats.cmake
  modified:
    - src/host/gbb_host.h
    - src/host/host_run.c
    - CMakeLists.txt
    - tests/cmake/areas.cmake
    - tests/expected-tests.txt
    - cmake/ExpectedTests.cmake
    - .github/scripts/verify-test-inventory.sh
key-decisions:
  - "Rows are ordered ascending by (type, ram_code) as numbers, so each of $1B and $1E lists RAM code $04 (128 KiB) before $05 (64 KiB); the CONTEXT table lists them the other way round."
  - "The cadence loss windows are checked against the constants they derive from: sram_loss_window_frames equals GBB_HOST_MAX_DIRTY_FRAMES and rtc_loss_window_frames equals GBB_HOST_RTC_COMPARE_FRAMES."
  - "save_format_freeze accepts baseline=none or baseline=vX.Y.Z, so the test keeps passing once a release tag carries the file (the plan's regex would have broken at the first release)."
  - "The table claims no interoperability with any other emulator, enforced as a checker rule (REJECT interop-claim on the word mGBA) with a seeded control rather than only a grep."
patterns-established:
  - "tests/cmake fragments that need a pinned git revision resolve their own (areas.cmake is included before tests/CMakeLists.txt defines GBB_STATE_SOURCE_REV)."
requirements-completed: [HOST-03]
coverage:
  - id: D1
    description: "--print-save-format prints save_format=gabbaboy-mbc1-sram-8k-v1 bytes=8192 for the committed MBC1 fixture, save_format=none bytes=0 for the tracer (no battery; the sentinel is not an id), exits 2 with print-save-format-extra when combined with --save-dir, and prints no ready line."
    requirement: HOST-03
    human_judgment: false
    verification:
      - kind: e2e
        ref: "ctest -R ^(save_format_print|save_format_print_none|host_grammar_print_extra)$"
        status: pass
  - id: D2
    description: "For all 16 rows on both the dmg and cgb profiles the runner prints the JSON id and bytes, a --frames 2 run produces a .sav of exactly that size with SRAM byte 0 equal to $5A ($FA with every byte >= $F0 for MBC2), RTC rows end in a structurally valid GBRT version-1 block (the $0F row is that block alone), both profiles agree, MBC1 ROM code 4 is also admitted, and $1A and $01 cartridges create no file; the checker prints rows=16 ids=12 profiles=2 files=32."
    requirement: HOST-03
    human_judgment: false
    verification:
      - kind: e2e
        ref: "ctest -R ^save_format_files$ (verify-save-formats.py --check)"
        status: pass
  - id: D3
    description: "Every admitted battery (type, RAM code, ROM code) combination reported by the core maps to exactly one JSON row with equal bytes and RTC presence, every row has an admitted combination (including the MBC1 ROM-code-4 boundary), the admitted no-battery types equal no_battery_types, and $10/$05 (MBC30) is never admitted."
    requirement: HOST-03
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest -R ^save_format_completeness$ (test_save_format_completeness + verify-save-formats.py --check-completeness)"
        status: pass
  - id: D4
    description: "The table is append-only against the latest strict-semver v* tag: the current latest tag v0.2.1 carries no docs/host-contract.json, so the freeze passes with baseline=none; no strict tag fails with no-tags; a baseline row that changed or vanished fails with freeze-mismatch."
    requirement: HOST-03
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest -R ^save_format_freeze$ (verify-save-formats.py --freeze)"
        status: pass
  - id: D5
    description: "docs/host-contract.json is canonical (text equals json.dumps(json.loads(text), indent=2, ensure_ascii=True) plus newline, keys never re-sorted), has exactly the four sections in order, its numbered exit_codes rows equal GBB_HOST_EXIT_TABLE in host_exit.h with one final crash row of code null, and its cadence values equal the constants in gbb_host.h."
    requirement: HOST-03
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest -R ^host_contract_json$ (verify-host-contract.py --check)"
        status: pass
  - id: D6
    description: "Twenty-six save-format controls each fail for their own REJECT code (size-mismatch for $10/$03 at 32,816, row-missing, row-not-admitted for a $10/$05 row, id-grammar for a release-versioned and an uppercase id, sum-mismatch, id-size-conflict, row-order, non-canonical for tabs and sorted keys, interop-claim, enumerator-output, file-size, profile-id-mismatch, no-battery-file, no-tags twice, freeze-mismatch twice) beside the positive controls; ten host-contract controls do the same for canonical form, sections, exit table and cadence."
    requirement: HOST-03
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest -R ^save_format_controls$ (save-formats self-test pass controls=26)"
        status: pass
      - kind: integration
        ref: "ctest -R ^host_contract_controls$ (host-contract self-test pass controls=10)"
        status: pass
  - id: D7
    description: "The 9 new CTest names are in tests/expected-tests.txt, the 2 POSIX-only ones (save_format_files, save_format_controls) are removed from the Windows expectation in both cmake/ExpectedTests.cmake and the inventory script, and the full phase1 suite is green at the plan's last code commit."
    requirement: HOST-03
    human_judgment: false
    verification:
      - kind: other
        ref: "bash .github/scripts/verify-test-inventory.sh --self-test"
        status: pass
      - kind: integration
        ref: "ctest --test-dir build -j8 at befd624c: 1637 of 1637 passed"
        status: pass
duration: 17min
completed: 2026-10-29
status: complete
---

# Phase 18 Plan 08: Save-Format Ids, `--print-save-format` and the Host Contract JSON Summary

**GabbaBoy's own save-format ids and byte sizes (MBC3+RTC 32 KiB is 32,789 B) are published in `docs/host-contract.json`, printed by `gabbaboy-runner --print-save-format`, and proven against the core's admitted cartridges in both directions, against the files the runner actually produces on both profiles, against the latest release tag, and by 36 seeded controls that each fail for their own named reason.**

## Performance

- **Duration:** about 17 min
- **Started:** 2026-10-29T05:02Z
- **Completed:** 2026-10-29T05:20Z
- **Tasks:** 3
- **Files modified:** 13 (6 created, 7 modified, excluding planning files)

## Accomplishments

- `docs/host-contract.json` holds the four sections in canonical form: `exit_codes` (clean, failure, refusal, crash), `cadence` (six values), `rtc_wall_clock: "not-recorded"` and `save_formats` (16 rows, 12 distinct ids, 10 no-battery types). It contains no mention of any other emulator.
- `host_save_format.c` carries the same 16 rows as a static table. `--print-save-format` is a valueless flag handled in the grammar (requires `--rom`, allows `--profile`, `print-save-format-extra` for `--save-dir` or `--frames`), runs before the Windows gate, reads the ROM through the existing bounded reader and the core's own validation, and writes nothing. A table miss or a size disagreement with `gbb_battery_size` is `gbb-host: no save-format row`, exit 1.
- `test_save_format_completeness` enumerates 13,824 header combinations in 0.03 s: 258 are admitted, 123 of them with a battery. It cross-checks the load path for every admitted combination at ROM code 0 and for the MBC1 `$03/$03` boundary (admitted at ROM code 4, refused at 5), and refuses to run if `$10/$05` is ever admitted.
- `verify-save-formats.py` checks, in order: canonical form, row structure (grammar, `bytes == ram + rtc`, same id same bytes, ascending order), then per mode the printed ids, the produced files, the completeness of the table and the freeze. `verify-host-contract.py` ties `exit_codes` to the X-macro in `host_exit.h` and `cadence` to the constants in `gbb_host.h`.
- Both checkers read the contract and the C sources with `git show <rev>:<path>` at the configure-time HEAD. The self-tests build private git repositories (a synthetic `v9.9.9` baseline tag, a stray `v0.1`, a numerically-later `v9.10.0`) and generated runner shims with exactly one defect.

## Task Commits

1. **Task 1 (tracer): contract JSON to C table to `--print-save-format` to produced `.sav` files on both profiles** - `be811f32` (test, RED) then `1db65c18` (feat, GREEN). Tracer gate: the verify line was re-run end to end after the commit (7 of 7 tests, including `host_windows_refusal`, `host_api_surface` and `host_qualified_sources`); tracer verified end-to-end, expanding.
2. **Task 2: completeness, freeze and the host-contract checker** - `58a68dfd` (test, RED) then `f71e1bc6` (feat, GREEN)
3. **Task 3: seeded controls for every drift mode** - `2ad26d56` (test, RED) then `befd624c` (feat, GREEN)
4. **Hardening: interoperability claim as a checker rule** - `c2239bef` (feat; see Deviations)

**Plan metadata:** recorded in the following docs commit.

## Files Created/Modified

- `docs/host-contract.json` - the machine-readable host contract
- `src/host/host_save_format.c`, `src/host/gbb_host.h` - the table, `host_save_format_row`, lookup and count
- `src/host/host_run.c` - `--print-save-format`
- `CMakeLists.txt` - `host_save_format.c` in `gabbaboy_host` and in the qualified-build dirty list
- `tests/test_save_format_completeness.c` - the enumerator
- `tests/scripts/verify-save-formats.py`, `tests/scripts/verify-host-contract.py` - the checkers with their self-tests
- `tests/cmake/save-formats.cmake`, `tests/cmake/areas.cmake` - nine registrations and one include line
- `tests/expected-tests.txt`, `cmake/ExpectedTests.cmake`, `.github/scripts/verify-test-inventory.sh` - inventory bookkeeping (9 names, 2 POSIX-only in both Windows lists)

## Decisions Made

- **Row order.** Rows ascend by `(type, ram_code)` as numbers, so `$1B` and `$1E` list RAM code `$04` (128 KiB) before `$05` (64 KiB). The CONTEXT table prints them in the other order; the plan's "ascending" rule governs and the checker enforces it with `row-order`.
- **Loss windows.** The two `*_loss_window_frames` values are checked against `GBB_HOST_MAX_DIRTY_FRAMES` and `GBB_HOST_RTC_COMPARE_FRAMES`, the constants they derive from, so a cadence change cannot leave the published windows behind.
- **Freeze output.** The CTest accepts `baseline=none` or `baseline=vX.Y.Z`. At the current revision the output is `baseline=none` (latest strict tag `v0.2.1` has no contract file).
- **`none` is a sentinel.** `save_format=none bytes=0` never appears in `save_formats` rows, does not match the id grammar (no `gabbaboy-` prefix) and is documented as such in the `host_save_format.c` header comment; the user-facing sentence is 18-09's docs task.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical] Extra REJECT codes for failure modes the plan's list did not name**
- **Found during:** Task 1 and Task 2
- **Issue:** The planned vocabulary (17 codes) has no code for a malformed row, a runner that exits non-zero, a wrong SRAM byte or GBRT block, a print that changed the working directory, a garbled enumerator output, two overlapping rows or a missing option. Reusing a planned code for those would blur which control failed for which reason.
- **Fix:** Added `row-malformed`, `runner-failed`, `file-content`, `print-side-effect`, `enumerator-output`, `row-overlap`, `usage` and (below) `interop-claim`. The 17 planned codes all exist and each has its own control.
- **Files modified:** `tests/scripts/verify-save-formats.py`
- **Commit:** `be811f32`, `f71e1bc6`, `c2239bef`

**2. [Rule 1 - Bug] The planned freeze regex would fail at the first release**
- **Found during:** Task 2
- **Issue:** Pinning `baseline=none` in the CTest is correct today and wrong the moment `v0.3.0` carries the file.
- **Fix:** `PASS_REGULAR_EXPRESSION` accepts `baseline=(none|vX.Y.Z)`; the checker still prints `baseline=none` now, and the self-test pins both outcomes.
- **Files modified:** `tests/cmake/save-formats.cmake`
- **Commit:** `58a68dfd`

**3. [Rule 1 - Bug] A re-sorted JSON file is itself canonical**
- **Found during:** Task 3 (the first self-test run)
- **Issue:** `json.dumps(json.loads(sorted_text), indent=2)` reproduces the sorted text, so the plan's text-equality rule alone cannot reject a sorted copy.
- **Fix:** Section, cadence and row key sets must appear in the written order; the same keys in another order is `non-canonical`, a different set is `section-missing` or `row-malformed`. The control uses `sort_keys=True` and a tab-indented copy.
- **Files modified:** `tests/scripts/verify-save-formats.py`, `tests/scripts/verify-host-contract.py`
- **Commit:** `f71e1bc6`, `befd624c`

**4. [Rule 2 - Missing critical] The no-interoperability prohibition was only a grep**
- **Found during:** Task 3 review of the threat model (T-18-28)
- **Issue:** The acceptance check is a manual `grep -ci mgba`; AGENTS.md asks for an automated check with a negative control.
- **Fix:** `load_rows` rejects any case-insensitive `mgba` in the contract (`interop-claim`) and the self-test seeds one.
- **Files modified:** `tests/scripts/verify-save-formats.py`
- **Commit:** `c2239bef`

### Planned-form differences

- **CLI spelling.** The plan says `--completeness PATH` on `--check`; the completeness leg is its own mode, `--check-completeness`, taking `--enumerator EXE` (the CTest) or `--completeness FILE` (controls, with captured output). The `save_format_files` pass line is unchanged.
- **Self-test seed.** `--self-test` also takes `--rev`/`--repo` and then reads its seed contract from that commit, so a boundary check never reads the live tree. CTest passes the configure-time revision.
- **Own revision variable.** `save-formats.cmake` resolves `GBB_SAVE_FORMATS_REV` itself because `areas.cmake` is included before `tests/CMakeLists.txt` defines `GBB_STATE_SOURCE_REV`.
- **Exit-table row shape.** The X-macro rows have four fields (`X(code, IDENT, "name", "meaning")`, from 18-07), so the checker's regex differs from the plan's three-field spelling.
- **TDD shape.** Each task has a RED commit before its GREEN. Task 1's RED failed on the planned behavior (`REJECT runner-failed: --print-save-format exited 2 ... reason=unknown-flag`; the print tests failed on `expected exit code 0 but ... '2'`). Tasks 2 and 3 are checker deliverables, so their REDs fail on the missing mode (`error: one of the arguments ... is required`, a missing script) rather than on a behavioral assertion; the enumerator itself ran and printed its output before the checker existed. CTest output is not a format `gsd_run check tdd-red-evidence` supports, so the classifier was not run; the logs are `build/18-08-task1-red.log`, `18-08-task2-red.log` and `18-08-task3-red.log`.
- **Deviation 6 (recorded as requested).** `--print-save-format` prints `save_format=none bytes=0` for a no-battery cartridge (assumption A5 adopted, exit 0). `none` is a sentinel, not an id: it does not match the id grammar and never appears in `save_formats`.
- **Docs.** The user-facing sentence that `save_format=none` is not an id, the save-format table in `docs/native-integration.md` and the `share/gabbaboy/` install of the JSON are 18-09 tasks (its must-haves list all three), so no doc file was touched here.

---

**Total deviations:** 4 auto-fixed (2 bugs, 2 missing critical), 5 planned-form differences
**Impact on plan:** No scope change. Every edited file is in the plan's `files_modified` list.

## Evidence Recorded for the Acceptance Criteria

- Task 1: `save_format_files` prints `save-formats pass rows=16 ids=12 profiles=2 files=32`; the canonical-form one-liner exits 0; `grep -c '"id": "gabbaboy-mbc3-rtc-sram-32k-v1"'` prints 1 and that row has `"bytes": 32789`; `grep -ci mgba docs/host-contract.json` prints 0; the `-D_WIN32` syntax proxy exits 0 for every `src/host/*.c`; `build/gabbaboy-runner --print-save-format --rom fixtures/tracer/tracer.gb --frames 3` prints `invalid-arguments: reason=print-save-format-extra` and exits 2; `--profile cgb` on the MBC1 fixture prints the same id; a duplicate `--print-save-format` is `duplicate-flag`.
- Task 2: `save_format_completeness` prints `save-formats completeness pass rows=16 battery_combinations=123 no_battery_types=10`; `save_format_freeze` prints `save-formats freeze pass baseline=none`; `host_contract_json` prints `host-contract pass exit_codes=4 cadence=6`. The enumerator's admitted no-battery types are `00 01 02 05 11 12 19 1A 1C 1D`, equal to the JSON list, and no line is printed for `type=0x10 ram=0x05`.
- Task 3: `save_format_controls` prints `save-formats self-test pass controls=26` (minimum 15) in about 5.6 s; `host_contract_controls` prints `host-contract self-test pass controls=10` (minimum 5). A scratch mutant of the checker with the id-grammar test disabled fails the self-test with `self-test accepted a release-versioned id`, so the controls discriminate.
- Plan verification: `ctest -R '^(save_format_.*|host_contract_.*|host_grammar_print_extra)$'` 9 of 9; `ctest -R '^(save_format_|host_|no_host_clock)'` 107 of 107; `bash .github/scripts/verify-test-inventory.sh --self-test` passes; full phase1 suite after reconfiguring with `-DGBB_STATE_PIN_BASE_REV=7c1f257...`: 1637 of 1637 at `befd624c` (`build/18-08-full-ctest.txt`); the final control addition at `c2239bef` re-ran the nine tests (9 of 9, `build/18-08-final-verify.log`).
- Local wall time against the 60 s budget: `save_format_files` 0.8 s, `save_format_controls` 5.6 s, `host_contract_controls` 0.9 s, the rest under 0.1 s.
- Windows: `save_format_print`, `save_format_print_none`, `save_format_completeness`, `save_format_freeze`, `host_contract_json`, `host_contract_controls` and `host_grammar_print_extra` are registered on every platform and were not run on Windows locally; `save_format_files` and `save_format_controls` are POSIX-only in both exclusion lists.

## Issues Encountered

None beyond the deviations above.

## Known Stubs

None.

## Threat Flags

None. T-18-27 (freeze, id grammar, sum and same-id rules, produced-file check on both profiles, seeded controls), T-18-28 (no interoperability wording, now a checker rule with a control; the 32,816 B size gate is 18-04) and T-18-29 (the print path opens only the ROM, through the 8 MiB bounded reader and `gbb_load_rom`) are mitigated as planned.

## Next Phase Readiness

- Next plan: 18-09 (documentation, install, closing traceability). It extends `verify-host-contract.py` with `--docs`, installs `docs/host-contract.json` under `share/gabbaboy/`, and writes the user-facing text, including the sentence that `save_format=none` is a no-battery sentinel and not an id. HOST-03 stays open until 18-09's closing traceability.
- Once a release tag carries `docs/host-contract.json`, `save_format_freeze` starts enforcing append-only against it; CI native jobs already fetch tags (`fetch-depth: 0`).

## Self-Check: PASSED

- FOUND: docs/host-contract.json, src/host/host_save_format.c, tests/test_save_format_completeness.c, tests/scripts/verify-save-formats.py, tests/scripts/verify-host-contract.py, tests/cmake/save-formats.cmake
- FOUND commits: be811f32, 1db65c18, 58a68dfd, f71e1bc6, 2ad26d56, befd624c, c2239bef

---
*Phase: GB-18-player-save-slots-and-host-contract*
*Completed: 2026-10-29*
