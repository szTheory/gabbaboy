---
phase: 07-dmg-game-acceptance-and-regression-baseline
plan: 01
subsystem: testing
tags: [libbet, fixture-admission, rights-manifest, python-stdlib, ctest, gitattributes, windows-ci]

requires:
  - phase: 06.1
    provides: exact-head CI gate (wait-exact-head-ci.py), exact CTest inventory, fixture manifest conventions
provides:
  - Vendored digest-pinned Libbet v0.08 ROM with a G5 rights/provenance manifest (45 closure records)
  - Fail-closed admission verifier with --self-test, --check-notices, --scan-dir and --derive-closure
  - tests/expect_exit.cmake exact exit-code plus reason wrapper reused by later plans
  - Eleven libbet_* CTests in the exact inventory and an open draft phase PR (#63) with Windows evidence
affects: [07-02, 07-03, 07-04, 07-12, 07-16]

actuals:
  tokens: 23000
  tasks: 3
  commits: 2
plan_head_before: b47fa6fd26a90fdbf2b0a915ef6f3900386b5272
plan_head_after: 8805bafbf82113741ed8d2191240906243d83e4e

tech-stack:
  added: []
  patterns:
    - "Fail-closed Python verifier with stable message tokens and a self-test that rejects every mutation with its own token"
    - "CTest negative controls assert an exact exit code and reason through tests/expect_exit.cmake, never plain non-zero"
    - "Closure completeness proven twice: a digest constant in required CI, a source-tree derivation in the opt-in repro job"

key-files:
  created:
    - fixtures/libbet/libbet.gb
    - fixtures/libbet/manifest.json
    - fixtures/libbet/LICENSE.txt
    - fixtures/libbet/SOURCES.md
    - tests/scripts/verify-libbet-admission.py
    - tests/expect_exit.cmake
  modified:
    - tests/CMakeLists.txt
    - tests/expected-tests.txt
    - .gitattributes
    - .gitignore
    - THIRD_PARTY_NOTICES.md

key-decisions:
  - "The notice row pins the manifest.json SHA-256 as well as the ROM and LICENSE.txt digests, and libbet_notice checks all three, so a manifest edit forces a notice update"
  - "Prerequisite rule accepts a derived closure path (the makefile itself) in addition to variables, obj/gb/ and src/tilesets/tools paths"
  - "Predicate addresses and ROM anchors are enforced by the verifier as constants, so the compiled table in Plan 07-02 cannot drift from the manifest"

patterns-established:
  - "Mutated manifest copies are generated at configure time with string(JSON) and the verifier resolves rom.path against the repository root"
  - "GBB_CMD travels as a list joined with $<SEMICOLON> so it survives the add_test argument split on all platforms"

requirements-completed: [GAME-01]

coverage:
  - id: D1
    description: "Libbet ROM, LICENSE and G5 manifest (45 closure records, credits, Korth limitation, provenance, scope note, predicate addresses) pass the fail-closed verifier"
    requirement: GAME-01
    verification:
      - kind: unit
        ref: "ctest -R '^libbet_admission_pass$' (python3 -I tests/scripts/verify-libbet-admission.py)"
        status: pass
    human_judgment: false
  - id: D2
    description: "Five D-05 mutated manifests and further self-test mutations each fail with their own distinct token"
    requirement: GAME-01
    verification:
      - kind: unit
        ref: "ctest -R '^libbet_admission_(empty_assets|missing_record|unknown_licence|bad_digest|bad_header|self_test)$'"
        status: pass
    human_judgment: false
  - id: D3
    description: "Closure omission is detectable: EXPECTED_CLOSURE_SHA256 in required CI and --derive-closure on the pinned source (45 files)"
    requirement: GAME-01
    verification:
      - kind: unit
        ref: "libbet_admission_self_test (closure-digest-mismatch, closure-derivation-mismatch, exclusion-referenced cases)"
        status: pass
      - kind: other
        ref: "python3 -I tests/scripts/verify-libbet-admission.py --derive-closure <pinned clone> -> libbet closure derived files=45"
        status: pass
    human_judgment: false
  - id: D4
    description: "The ROM is absent from an install tree; the scan fails on a neutral-name copy"
    requirement: GAME-01
    verification:
      - kind: integration
        ref: "ctest -R '^libbet_(install_tree|not_installed|not_installed_selftest)$'"
        status: pass
    human_judgment: false
  - id: D5
    description: "Notices row, intro sentence and .gitattributes lines (ROM -text, Libbet/acceptance/baseline eol=lf)"
    requirement: GAME-01
    verification:
      - kind: unit
        ref: "ctest -R '^libbet_notice$'"
        status: pass
    human_judgment: false
  - id: D6
    description: "Windows spike: native-windows-x64 ran the Python-backed libbet_* tests and the cmake -P wrapper at the exact PR head"
    verification:
      - kind: e2e
        ref: "https://github.com/szTheory/gabbaboy/actions/runs/38092426274 (head 8805bafbf82113741ed8d2191240906243d83e4e)"
        status: pass
    human_judgment: false

duration: 18min
completed: 2026-10-10
status: complete
---

# Phase 7 Plan 01: Libbet admission and G5 verifier Summary

**Digest-pinned Libbet v0.08 ROM admitted behind a fail-closed stdlib verifier over a 45-record rights manifest, with eleven exact-code CTests, an install-tree exclusion guard and green exact-head CI on Linux, macOS and Windows**

## Performance

- **Duration:** 18 min (start approximated from the first scratch download; exact start not captured)
- **Started:** 2026-10-10T22:28:00Z (approximate)
- **Completed:** 2026-10-10T22:46:00Z
- **Tasks:** 3 (one tracer, two auto)
- **Files modified:** 11

## Accomplishments

- `fixtures/libbet/libbet.gb` is the upstream v0.08 release image (32768 bytes, SHA-256 `3607412031c8287cf878299ce96e581e85b852dde703806343b95576fa3ff1a9`, header LIBBET / `$00` / `$143=$80` / `$146=$03`), downloaded once into an empty scratch directory and accepted only on that digest. The pinned identity is upstream commit `46a765a2c01701bffb8c0b7dd6e4be3a6b193090`, never the mutable tag.
- The manifest carries every G5 item (a) to (f): the verbatim zlib LICENSE plus the credit discrepancy, the README credit excerpt and Korth's "Would be fine." recorded as a limitation, one `rights.embedded_assets` record per frozen-closure file, release provenance, the reproducibility statement and recipe (local observation only, `hosted_run_url` null), and the single-author scope note. It also records the eight predicate addresses with derivations and the five ROM anchors, which the verifier checks against the ROM bytes.
- `verify-libbet-admission.py` fails closed with stable tokens. The self-test rejects the five D-05 mutations, duplicate keys, malformed UTF-8, a byte-order mark, a dropped `src/global.inc`, a wrong size, commit, licence digest, classification, hosted URL and anchor, and exercises a synthetic source tree for the derivation rules and the install-tree scan.
- Closure completeness is detectable in both places: `EXPECTED_CLOSURE_SHA256` (`5e8b363d75611d265a31de54da0cc46228548364dfc368adc50eebe1274d09ab`) in required CI, and `--derive-closure` on a source tree. On the pinned clone it printed `libbet closure derived files=45 sha256=5e8b363d75611d265a31de54da0cc46228548364dfc368adc50eebe1274d09ab`, exactly the 45 paths the plan listed, so nothing was stopped or edited to match.
- Eleven new CTests (`libbet_admission_pass`, `_empty_assets`, `_missing_record`, `_unknown_licence`, `_bad_digest`, `_bad_header`, `_self_test`, `libbet_notice`, `libbet_install_tree`, `libbet_not_installed`, `libbet_not_installed_selftest`) are in `tests/expected-tests.txt` and the exact-inventory configure check passes. Full local suite: 195/195, and `verify-test-inventory.sh --installed` verified 195 executed cases, none skipped.
- Draft PR [#63](https://github.com/szTheory/gabbaboy/pull/63) is open. Exact-head CI [run 38092426274](https://github.com/szTheory/gabbaboy/actions/runs/38092426274) at head `8805bafbf82113741ed8d2191240906243d83e4e` concluded success; `wait-exact-head-ci.py --require required-native` printed PASS for that SHA. Jobs: native-linux-x64 success, native-macos-arm64 success, native-windows-x64 success, linux-asan-ubsan success, cmake-floor-3.25.3 success, player-gate success, macos-player-package success, required-native success.
- Windows spike result: the native-windows-x64 log shows CMake found `C:/hostedtoolcache/windows/Python/3.14.8/x64/python3.exe` through `find_package(Python3)`, and all eleven `libbet_*` tests passed (195/195 overall), including `libbet_admission_pass`, `libbet_not_installed` and the exact-exit negatives through `expect_exit.cmake`.

## Task Commits

1. **Task 1: Tracer - vendored ROM, G5 manifest and fail-closed verifier** - `5720573` (feat)
2. **Task 2: Register admission, redistribution and notice controls, plus notices and SOURCES** - `8805baf` (test)
3. **Task 3: Push the phase branch, open the draft PR, read the Windows spike** - no tracked file changed (CI was green on the first push)

**Plan metadata:** the docs commit that adds this SUMMARY, STATE.md and ROADMAP.md (made after the measured `commits: 2` above).

## Files Created/Modified

- `fixtures/libbet/libbet.gb` - vendored release ROM, byte-identical to upstream
- `fixtures/libbet/manifest.json` - G5 rights and provenance manifest (LF, strict UTF-8 JSON, no duplicate keys)
- `fixtures/libbet/LICENSE.txt` - verbatim upstream zlib LICENSE plus a separated project note on the credit discrepancy and the Korth limitation
- `fixtures/libbet/SOURCES.md` - immutable inputs, asset rights, reproduction, redistribution and fallback (D-07)
- `tests/scripts/verify-libbet-admission.py` - verifier and self-test
- `tests/expect_exit.cmake` - exact exit-code plus reason-regex wrapper (GBB_CMD, GBB_EXPECT_CODE, GBB_EXPECT_REGEX, GBB_WORKDIR)
- `tests/CMakeLists.txt`, `tests/expected-tests.txt` - Python3 discovery, five configure-time mutated manifests, eleven registrations, the install-tree fixture
- `.gitattributes` - ROM `-text`; Libbet text files, `tests/acceptance/**` and `tests/baseline/**` `text eol=lf`
- `.gitignore` - admits only `!/fixtures/libbet/libbet.gb` through the project's explicit-admission list
- `THIRD_PARTY_NOTICES.md` - Libbet row (zlib, credits, CC0 note, three digests) and an intro that no longer claims every ROM is project-authored

## Decisions Made

- Pin the manifest digest in the notice row, not only the ROM and LICENSE digests; `libbet_notice` checks all three. A later manifest edit must update the notice in the same change.
- Enforce the eight predicate addresses and five ROM anchors in the verifier as constants (token `predicate-anchor-mismatch`), so Plan 07-02's compiled table and this manifest cannot diverge silently.
- Evidence URLs must equal the pinned-commit blob URL for the record's path, so an evidence pointer cannot drift to a branch.
- Records carry an extra `basis` field (`file-header-notice` or `repo-wide-licence-inference`) so the inference behind each licence is explicit, plus optional `note` fields.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] `.gitignore` ignores every `*.gb`**
- **Found during:** Task 1 (staging the ROM)
- **Issue:** `git add` refused `fixtures/libbet/libbet.gb` because `*.gb` is ignored; the repository admits each public fixture ROM with an explicit negation, and `.gitignore` was not in the plan's file list.
- **Fix:** Added `!/fixtures/libbet/libbet.gb` next to the other fixture negations. No `git add -f` was used.
- **Files modified:** `.gitignore`
- **Verification:** `git check-ignore -v` reports the negation rule; the ROM is tracked and `git show HEAD~1:fixtures/libbet/libbet.gb | shasum -a 256` equals the pinned digest.
- **Committed in:** `5720573`

**2. [Rule 1 - Bug] The literal prerequisite rule would reject the real makefile**
- **Found during:** Task 1 (designing `--derive-closure`)
- **Issue:** The pinned makefile has `obj/gb/index.txt: makefile`. The plan's rule allows only variables, `obj/gb/` paths and paths under `src/`, `tilesets/` or `tools/`, so the real makefile would have failed `prerequisite-outside-closure`.
- **Fix:** A prerequisite that is itself a derived closure path (here `makefile`) is also allowed. Path traversal (`..`) and absolute prerequisites are still rejected, and a `$(wildcard ...)` prerequisite must glob under the three build directories.
- **Files modified:** `tests/scripts/verify-libbet-admission.py`
- **Verification:** `--derive-closure` on the pinned clone passes (files=45); the self-test rejects `/etc/passwd` as a prerequisite.
- **Committed in:** `5720573`

**3. [Rule 2 - Missing critical functionality] Additional distinct tokens for gaps the plan left implicit**
- **Found during:** Task 1
- **Issue:** The plan listed 21 tokens, but several fail-closed paths had no token: a missing ROM file, duplicate or extra asset records, a malformed predicate table or anchor, a hosted-reproduction claim with no run URL, an invalid exclusion entry and an unreadable source tree.
- **Fix:** Added `rom-missing`, `embedded-asset-duplicate`, `embedded-asset-extra`, `predicate-addresses-invalid`, `predicate-anchor-mismatch`, `reproducibility-claim-invalid`, `closure-exclusion-invalid` and `source-tree-invalid`. The self-test covers each that a manifest or tree mutation can reach.
- **Files modified:** `tests/scripts/verify-libbet-admission.py`
- **Verification:** `libbet_admission_self_test` passes locally and on all three native CI jobs.
- **Committed in:** `5720573`

---

**Total deviations:** 3 auto-fixed (1 blocking, 1 bug, 1 missing critical)
**Impact on plan:** All three were needed for correctness or to commit the ROM; no scope creep and no change to any D-xx decision.

## Closure rule is a conservative over-approximation

Recorded as the plan requires: `tilesets/Libbet_title.png` is named by D-04c but referenced by no ROM rule in the pinned makefile, `tools/uniq.py` is imported only in a disabled branch of `tools/makeborder.py`, and `tools/zipup.py` is used only by the zip packaging recipe. Their bytes do not reach the ROM, but they keep rights records. The exclusions `tools/bgrdedent.py` and `tools/unused.py` are valid: no makefile token, glob or pattern-rule expansion names them, no closure tool imports them and no src include or incbin target names them (the word `unused` appears only in src comments, which the rule never matches).

## Rights limitations carried forward

- Per-asset rights for files with no per-file notice (the ten tilesets files, `src/intro.z80`, `tools/makeborder.py`, `tools/pitchtable.py`) rest on an inference from single-author history (285 of 286 commits by Damian Yerrick, one constants commit by Eldred Habert) plus the repository-wide zlib licence. The `vwf7_cp144p.png` font has no stated origin beyond the commit that added it. This was accepted by D-04f; it is not an upstream per-asset grant.
- The upstream LICENSE names only Damian Yerrick 2018 while the README and ROM text also credit Martin Korth; the discrepancy is preserved, not resolved.
- Korth's porting permission is recorded as a limitation, not a licence grant. `tools/savescan.py` is MIT, the makefile and two tools carry an all-permissive notice, and `src/hardware.inc` is CC0-1.0; all are recorded per file.
- Reproducibility is a local macOS observation only. No hosted run URL exists, so no hosted reproduction is claimed (D-03); Plan 07-04 owns that job.

## Issues Encountered

- My first `wait-exact-head-ci.py` call omitted the required `--require` argument and exited with a usage error; the rerun with `--require required-native` waited and passed. No other problems.
- The plan's `<action>` for the verifier lists the checks "in order"; the closure-digest check runs before the extra-record check so that removing a path from `closure_files` reports `closure-digest-mismatch` as the plan requires.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Ready for Plans 07-02, 07-03 and 07-04. Plan 07-02 binds its compiled predicate table to the ROM digest and the manifest `predicate_addresses` (both enforced here); Plan 07-04's repro job can call `--derive-closure` on its pinned clone; every later plan can reuse `tests/expect_exit.cmake` and the `tests/acceptance/**` and `tests/baseline/**` LF rules without further `.gitattributes` edits.
- The draft PR #63 head `8805baf` carries this plan's code; the docs commit that adds this SUMMARY is local until a later plan pushes. No blocker.

## Threat Flags

None. The verifier only reads files under fixed repository paths and the optional source tree it is given, never executes anything from them and never follows symlinks.

## Known Stubs

None.

## Self-Check: PASSED

- Created files exist: libbet.gb, manifest.json, LICENSE.txt, SOURCES.md, verify-libbet-admission.py, expect_exit.cmake (all FOUND).
- Commits `5720573` and `8805baf` are ancestors of HEAD; the committed ROM blob digest equals the pinned SHA-256.
- Acceptance and verify commands re-run after the final task commit: `verify-libbet-admission.py` and `--self-test` exit 0, `--check-notices` exit 0, `ctest -R '^libbet_'` 11/11, full suite 195/195, inventory verified (195, none skipped).

---
*Phase: 07-dmg-game-acceptance-and-regression-baseline*
*Completed: 2026-10-10*
