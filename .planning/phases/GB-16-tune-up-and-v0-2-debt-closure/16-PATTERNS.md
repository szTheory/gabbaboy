# Phase 16: Tune-up and v0.2 Debt Closure - Pattern Map

**Mapped:** 2026-10-24
**Files analyzed:** 38 new/modified (grouped by plan)
**Analogs found:** 36 / 38 (two have no repo analog: the hosted valgrind job and the `gh`-driven release/PR actions)

**Plan revision 1 (2026-10-24): the file layout changed. Where this map disagrees with the plans, the plans win.**
- The Phase 8 CTests register in `tests/cmake/hygiene.cmake`, not `tests/cmake/phase8.cmake`.
- The receipt checker is `verify-perf-gate.py --check-attribution`, not a separate `verify-perf-attribution.py`.
- The ledger freeze is `verify-support-ledger.py --check-freeze`, not `verify-ledger-freeze.py`.
- The lint, budget, temp-clean and release CTests register in `tests/CMakeLists.txt`, not in archive, cibudget or release fragments.
- `GBB_LIVE_PHASES_DIR` and `GBB_V02_PHASES_DIR` are set in `tests/CMakeLists.txt`.
- The workflow-policy CTests live in `tests/cmake/ci-lanes.cmake` (16-04).

The analog patterns themselves are unchanged.

All analog paths below were verified git-tracked (`git ls-files --error-unmatch`). No gitignored mirror paths are used. Line numbers are at the 2026-10-24 HEAD (`83cee09`) and will drift after 16-01 moves things; re-grep anchors, do not trust numbers across plans.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `tests/scripts/verify-no-phase-paths.py` (16-01) | checker (lint) | batch (scan tracked text) | `tests/scripts/verify-uat-closure.py` + `verify-summary-coverage.py` | role-match |
| `tests/scripts/verify-hdma-lane.py` (16-01) | checker (extracted) | transform | `.planning/phases/GB-13-cgb-hdma/verify-hdma-closure.py` (lines 80, 150, 679, 701) | exact (extraction) |
| `tests/cmake/*.cmake` per-area includes + one `include()` (16-01..) | config (CTest registration) | n/a | `tests/CMakeLists.txt` `gbb_add_v02_contract` (1377-1391) and `gbb_add_summary_coverage_test` (2668-2679) | role-match |
| `tests/CMakeLists.txt` edits (1208, 2670, 2687, 1405) | config | n/a | itself | modify |
| `tests/expected-tests.txt` (every plan) | config (inventory) | n/a | lines 1178-1179 (`expect_exit_min_count_*`) | exact |
| Retargeted readers (`verify-closeout-dispositions.py`, `verify-historical-limitations.py`, `test-cgb-red-evidence-privacy.py`, `verify-closeout-scan.py`, `verify-summary-coverage.py:300`) | checker | batch | themselves (add `--min-files`/env path) | modify |
| `tests/scripts/verify-phase8-closure-contract.py`, `verify-phase8-player-contract.py` + `--boundary` (16-05) | checker | transform (git show) | `verify-phase8-player-contract.py` (read in full) | exact |
| 6 Phase 8 CTests in `tests/cmake/phase8.cmake` (16-05) | test registration | request-response | `uat_closure_controls` + `expect_exit_min_count_*` (tests/CMakeLists.txt 2704-2719) | exact |
| `tests/scripts/verify-perf-gate.py` (+ parser, Ir arithmetic) (16-02) | checker | transform | `tests/scripts/measure-release-baseline.sh` `--ab` PYAB block (lines 37-151) | role-match |
| `tests/baseline/perf-gate-v1.txt` (16-02) | config | n/a | `tests/baseline/dmg-cpu-b-v1.txt` | role-match |
| `tests/scripts/verify-perf-attribution.py` + receipt JSON (16-02) | checker | transform | `verify-v02-performance.py` receipt binding + `verify-closeout-dispositions.py` self-test | role-match |
| `tests/data/*` canned cachegrind/timing outputs | fixture | n/a | `tests/data/invalid-summary-coverage.md` + SHA pin (CMakeLists 2723-2730) | exact |
| `perf-gate` job in `.github/workflows/ci.yml` (16-02) | CI job | batch | `linux-sanitizers-acceptance` / `cmake-floor-3-25-3` jobs | role-match |
| attribution `workflow_dispatch` workflow (16-02) | CI workflow | batch | `.github/workflows/fixture-repro.yml` | role-match |
| `tests/scripts/verify-test-budget.py` + `tests/ci/test-budget-allowlist` (16-03) | checker | batch (json-v1) | `verify-cgb-apu-dispositions.py:153` json-v1 reader | role-match |
| `.github/workflows/nightly-asan.yml` (16-03) | CI workflow | event-driven | `.github/workflows/ci.yml` ASan jobs (+ `check_nightly()` in policy) | partial |
| `tests/acceptance/CMakeLists.txt` stall sharding (16-03) | config | request-response | `acceptance_stall_diagnosis` (536-545) | exact |
| `tests/check_sanitizer_timeout_policy.cmake` (D-23) | utility | file-I/O | itself (lines 1-10) | modify |
| `.github/ci-timeouts.json` + ledger check (16-04) | config + checker | batch | `_check_fuzz_wait_budget` (policy 301-334) | role-match |
| `.github/scripts/verify-workflow-policy.py` edits (16-02/03/04) | checker | transform | itself (constants at 1225-1251, 1343, 1607) | modify |
| CTest wrappers for workflow-policy `--check`/`--self-test` (16-04) | test registration | request-response | `closeout_dispositions_controls` (CMakeLists 1461-1464) | exact |
| `changes` + `planning-checks` jobs + `required-native` branching (16-04) | CI job | event-driven | `required-native` (ci.yml 395-435) | role-match |
| planning classifier script (16-04) | utility | transform | `.github/scripts/check-player-result.sh` (small gate script) | partial |
| planning-label lint (16-04) | checker | batch | `verify-test-budget.py` json-v1 reader (same technique) | role-match |
| plan-cap / LESSONS-id / STATE-size / Playstead-docs checkers (16-05) | checker | batch | `verify-summary-coverage.py` (check_text/MUTANTS/self_test) | role-match |
| `docs/support/v0.2.1.md`, ledger freeze checker (16-06/07) | checker + doc | transform | `verify-support-ledger.py` (`select_ledger` 64-84, `--write-current`) | role-match |
| version-agnostic edits (`verify-support-ledger.py`, `verify-v02-adoption.py`, `release-rehearsal.yml`, CMakeLists 1405) | modify | n/a | themselves | modify |
| v0.3 disposition record + checker + CTest (16-06) | checker + data | batch | `verify-closeout-dispositions.py` + `closeout_dispositions_controls` | exact |
| release-notes needle (16-06) | checker | transform | `verify-v02-adoption.py --release-notes` | exact |
| 16-07 release readback / post-release boundary checker | checker | request-response | `verify-uat-closure.py` (boundary style) | partial |
| `gh pr close` of #78-92, tag push, PR #75 body edit | operational | n/a | none (no repo analog) | none |
| hosted valgrind install + seeded-regression patch step | CI step | batch | none (no valgrind step exists) | none |

## Pattern Assignments

### Universal checker skeleton (applies to every new `tests/scripts/*.py`)

**Analog:** `tests/scripts/verify-uat-closure.py` (260 lines) and `tests/scripts/verify-summary-coverage.py`.

**Header and -O refusal** (uat-closure 1-47): module docstring that states the contract, `#!/usr/bin/env python3`, stdlib-only imports, and the python -O refusal, because `assert` is stripped under -O.
```python
if not __debug__ or sys.flags.optimize:
    raise SystemExit('verify-uat-closure must not run with python -O')
ROOT = Path(__file__).resolve().parents[2]
class ClosureError(Exception): ...
# need(cond, msg) raises ClosureError instead of using assert
```
Copy: custom error class plus a `need()` helper, never `assert`.

**Self-test = positive control + named mutants + "inactive mutation" guard** (uat-closure 195-232; summary-coverage 255-296):
```python
for filename, label, mutate in controls:
    with tempfile.TemporaryDirectory(prefix='gbb-uat-closure-') as name:
        scratch = Path(name) / directory.name
        shutil.copytree(directory, scratch)
        original = path.read_text(encoding='utf-8')
        changed = mutate(original)
        need(changed != original, f'{label}: inactive mutation')   # mutant must actually change the input
        path.write_text(changed, encoding='utf-8')
        try:
            check(scratch)
        except ClosureError:
            continue
        raise ClosureError(f'{label}: accepted weakened closure')
```
Every checker needs the three pieces: the unchanged fixture passes, every mutant is rejected, and a mutant identical to its input is itself a failure.

**Single-line, count-bearing success output** so `expect_exit.cmake` can parse a minimum (summary-coverage 296, uat-closure 233, phase8 player 210):
```python
print("summary-coverage self-test pass mutants=%d" % len(MUTANTS))
print(f'uat-closure self-test pass automated={total} controls={len(controls) + 3}')
print("summary-coverage pass files=%d entries=%d" % (files, count))
```
Print each KEY=<digits> exactly once (expect_exit requires exactly one match). Do not echo the key in a second line.

**CLI** (uat-closure 236-260): `argparse`, one mutually exclusive mode group (`--write` / `--self-test` / default check), `main()` wrapped so `ClosureError` prints `uat-closure rejected: ...` to stderr and exits 1. summary-coverage (300-314) uses `--phases-dir` with a `default=".planning/phases"`; D-07 requires removing that default (make `--phases-dir` required).

**Reject-code style (alternative)** `verify-closeout-dispositions.py:590-614`: `except Rejected as exc: print(f"REJECT {exc.code}: {exc.message}", file=sys.stderr); return 1`. Use this when the CTest must distinguish failure classes by code (perf gate: `ir-budget-exceeded`, `proxy-nondeterministic`, `proxy-vacuous`, `workload-digest-mismatch`; workflow policy uses the same `REJECT <code>:` form).

**Fix for `verify-no-phase-paths.py` specifically:** the 404-file floor should be printed as `files=N` and enforced with `GBB_EXPECT_MIN_KEY=files` in the CTest, plus the in-script must-scan list. Fixture-per-spelling controls follow the mutants pattern above; the clean `milestones/v0.2-phases` case is the positive control, and `docs/mbc1-evidence.md:64-93` (links into `.planning/milestones/v0.1-phases/`) is a real accepted example.

---

### CTest registration (every plan)

**Analog:** `tests/CMakeLists.txt` 2668-2719 (summary_coverage, uat_closure, `expect_exit_min_count_*`) and 1377-1391 (`gbb_add_v02_contract`); `tests/expect_exit.cmake`; `cmake/ExpectedTests.cmake`; `tests/expected-tests.txt`.

**Wrapper function (exact analog for Phase 8 six-CTest group and every new checker)** (CMakeLists 2688-2701):
```cmake
function(gbb_add_uat_closure_test name code regex)
  set(command "${Python3_EXECUTABLE}" -I ${ARGN})
  list(JOIN command "$<SEMICOLON>" joined)
  add_test(NAME ${name}
    COMMAND ${CMAKE_COMMAND}
      "-DGBB_CMD=${joined}"
      -DGBB_EXPECT_CODE=${code}
      "-DGBB_EXPECT_REGEX=${regex}"
      ${GBB_UAT_EXTRA_ARGS}
      -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
  set_tests_properties(${name} PROPERTIES TIMEOUT 120)
endfunction()
```
Use `code=1` for rejection tests (`uat_closure_optimize_refused` at 2720 is the exact pattern: `gbb_add_uat_closure_test(uat_closure_optimize_refused 1 "must not run with python -O" ...)`).

**Anti-vacuity minimum** (CMakeLists 2703-2705; use for Phase 8 `rejected_controls >= 157`):
```cmake
set(GBB_UAT_EXTRA_ARGS -DGBB_EXPECT_MIN_KEY=controls -DGBB_EXPECT_MIN_VALUE=21)
gbb_add_uat_closure_test(uat_closure_controls 0 "uat-closure self-test pass automated=[0-9]+ controls=[0-9]+" ...)
set(GBB_UAT_EXTRA_ARGS)       # reset
```
For Phase 8: `-DGBB_EXPECT_MIN_KEY=rejected_controls -DGBB_EXPECT_MIN_VALUE=157` on the `--self-test` test only; the plain run prints `rejected_controls=0` so never put the min on it (it would fail the minimum).

**Proof the minimum mechanism itself works** (2707-2719): `expect_exit_min_count_rejects_lower` uses `PASS_REGULAR_EXPRESSION "controls=19 is below the minimum 20"`; already present and registered at `expected-tests.txt:1178-1179`. Do not duplicate.

**Plain-execution and PASS_REGULAR_EXPRESSION style (no expect_exit)** (1461-1464):
```cmake
add_test(NAME closeout_dispositions_controls
  COMMAND "${Python3_EXECUTABLE}" -I ".../verify-closeout-dispositions.py" --self-test)
set_tests_properties(closeout_dispositions_controls PROPERTIES TIMEOUT 120
  PASS_REGULAR_EXPRESSION "closeout-dispositions self-test pass positives=3 rejected_controls=[1-9][0-9]*")
```
Use for workflow-policy `--check` / `--self-test` wrappers (self-test takes about 15 s, `negative_controls=164`; set TIMEOUT 120, label `planning` is not applicable because it reads `.github/` only, so check D-22 intent before labelling).

**Labelled group registration** (`gbb_add_v02_contract` 1377-1391): `set_tests_properties(... LABELS "v02" ...)`. For the `planning` label (D-21/D-22) copy: `set_tests_properties(${name} PROPERTIES TIMEOUT 60 LABELS "planning")`. No existing `planning` label; 16-01 introduces the convention.

**Per-area include mechanism (does not exist yet; 16-01 owns it):** include the fragment inside `tests/CMakeLists.txt` before `gabbaboy_verify_registered_tests()` (line ~4653). Fragments run in directory scope, so `get_property(DIRECTORY PROPERTY TESTS)` sees them. Shape to copy for the include line is the existing one at CMakeLists ~4659: `include("${PROJECT_SOURCE_DIR}/cmake/ScaleSanitizerTimeouts.cmake")`. The new line is `include("${PROJECT_SOURCE_DIR}/tests/cmake/<area>.cmake")` and must precede both the verify call and the sanitizer scaling call (4659-4660) so new TIMEOUTs are scaled.

**Two-file rule** (`cmake/ExpectedTests.cmake:1-34`): every `add_test` name must also be a line in `tests/expected-tests.txt` (a flat one-name-per-line list, sorted at compare time). Mismatch fails configure with `Registered CTest cases differ from tests/expected-tests.txt`. Windows has an exclusion list in the same file for bash-only tests: any new test that needs bash or valgrind must be added to the `if(WIN32)` `list(REMOVE_ITEM ...)` block (lines 13-21) or the Windows lane fails configure.

**Immutable test-data pin** (CMakeLists 2723-2730): for each canned file in `tests/data/`, pin `file(SHA256 ...)` and fail configure on mismatch, plus `CMAKE_CONFIGURE_DEPENDS`:
```cmake
set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS "${GBB_INVALID_SUMMARY_FIXTURE}")
file(SHA256 "${GBB_INVALID_SUMMARY_FIXTURE}" gbb_invalid_summary_sha256)
if(NOT gbb_invalid_summary_sha256 STREQUAL GBB_INVALID_SUMMARY_FIXTURE_SHA256)
  message(FATAL_ERROR "... is immutable test data: ... Do not repair the fixture; fix the checker or add a second fixture.")
```
Apply to the 14-UAT-REVIEW seed copy and the canned cachegrind/timing files.

**Archive retarget points** (tests/CMakeLists.txt): line 1208 (`GBB_HDMA_CLOSURE_CHECKER`; becomes `tests/scripts/verify-hdma-lane.py`, keep test names `cgb_hdma_lane_contract`, `cgb_hdma_lane_contract_selftest`, `cgb_hdma_remote_evidence_selftest` at 1213-1222, TIMEOUT 30 at 1223); line 2670 (`--phases-dir "${PROJECT_SOURCE_DIR}/.planning/phases"` inside `gbb_add_summary_coverage_test`; becomes `${GBB_V02_PHASES_DIR}` for the v0.2 sweep with a `--min-files` and a separate live test via `${GBB_LIVE_PHASES_DIR}`); line 2687 (`GBB_UAT_CLOSURE_PHASE`, the GB-15 dir, becomes `${GBB_V02_PHASES_DIR}/GB-15-...`); line 1405 (`version=0.2.0` regex; make `version=0\.[0-9]+\.[0-9]+`).

---

### `tests/scripts/verify-phase8-*-contract.py` `--boundary` (16-05, D-11/D-12)

**Analog:** `tests/scripts/verify-phase8-player-contract.py` (read in full).

**Boundary read** (lines 15, 27-36): module constant `BOUNDARY = "96d5eec..."` and
```python
def read_boundary(path: str) -> str:
    result = subprocess.run(["git", "show", f"{BOUNDARY}:{path}"], check=False, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"could not read {path} at Phase 8 boundary: {result.stderr.strip()}")
    return result.stdout
```
Change: default becomes the tag `historical/phase-08-boundary` resolved with `git rev-parse --verify <tag>^{commit}`, fail closed with a message that also starts `phase8-player-contract: FAIL`; take the revision as a parameter (`--boundary`), do not fall back to the literal SHA.

**CLI to extend** (137-140): add `parser.add_argument("--boundary", default=BOUNDARY_TAG)` beside `--self-test`. Failure output (153, 159) is already `phase8-player-contract: FAIL: ...` on stderr, exit 1: that is the D-11 regex for the wrong-boundary test. `expect_exit.cmake` matches the combined stdout+stderr, so stderr output is matched.

**Closure verifier:** has `OLD = '5673bed'` (`:77`) for `'old:'+path` reads which must stay reachable independent of `--boundary`; only the `BOUNDARY` reads change. Its plain run prints `rejected_controls=0`, `--self-test` prints `=157`. Wrong boundary (`v0.2.0`) must produce `missing historical clause`, not `cannot read`; confirm against real output before pinning the regex.

**Self-test mutant pattern** (player 166-210): `original.replace(X, "", 1)`; assert `mutated != original` and `verify_contract(mutated)` is non-empty. Matches the universal skeleton.

---

### Perf gate: `tests/scripts/verify-perf-gate.py`, `tests/baseline/perf-gate-v1.txt`, canned data (16-02)

**Analog:** `tests/scripts/measure-release-baseline.sh` (783 lines). Hosted valgrind part has no analog.

**Embedded-Python receipt style and constants** (lines 37-151): arg parse via `sys.argv`, `WORKLOAD = "original-wram-tracer-1m-half-dots-v1"` (line ~50), `expected_digest = "4c7a57ff3d50d228"` (61, also 196), digest check on parsed `fields.get("correctness_digest_fnv1a64")` (81, 275), test hooks honoured only when `GBB_AB_TEST_HOOKS=1` (65-67):
```python
if os.environ.get("GBB_AB_TEST_HOOKS") == "1":
    expected_digest = os.environ.get("GBB_AB_EXPECT_DIGEST", expected_digest)
```
Copy: do not let a test hook weaken a digest guard unless an explicit second env var is set. The D-14 gate is a new Python script (not shell): do not stretch this one (RESEARCH says so).

**Output record**: `measure_core` prints one line with `workload=... consumed_half_dots=... correctness_digest_fnv1a64=...` (tests/measure_core.c:95-150). Parse as key=value fields; the same parse is used at 81/275 above. ROM cap is 32768 bytes (`MAX_ROM_BYTES`); check the visible-demo ROM size (A2).

**Limits file** `tests/baseline/perf-gate-v1.txt`: follow `tests/baseline/dmg-cpu-b-v1.txt` (key=value baseline text). Read it at plan time for the exact grammar; mirror it.

**CTest (valgrind-free)**: wrap with `expect_exit.cmake` using Reject-code regexes (`ir-budget-exceeded` etc.) at exit 1, and `KEY=` minimum on the self-test. Canned outputs go in `tests/data/` with SHA pins (see CTest section).

**Hosted job (no analog):** add a `perf-gate` job to `ci.yml`. Copy the shape (checkout with `persist-credentials: false`, `fetch-depth: 0`, pinned `actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2` as in ci.yml:411-414) from existing ci.yml jobs. `verify-workflow-policy.py` forbids tabs, flow maps, anchors and unpinned `uses:`; run `python3 -I .github/scripts/verify-workflow-policy.py --check` after editing. The job must be added to `required-native.needs` AND `CI_REQUIRED_NATIVE_NEEDS` (policy line 1251) in the same commit.

**Receipt (D-17):** JSON receipt checker recomputes deltas from raw rows. Style analog: `verify-closeout-dispositions.py` self-test (drive the real CLI over a private fixture, reject each named defect with its own diagnostic and no success line; CMakeLists 1456-1464 comment). Selection rule must be recomputed with `git rev-list --first-parent <range> -- src include`.

---

### Per-test budget ratchet `tests/scripts/verify-test-budget.py` + `tests/ci/test-budget-allowlist` (16-03, D-18)

**Analog:** the json-v1 TIMEOUT reader in `tests/scripts/verify-cgb-apu-dispositions.py:153` (and `verify-cgb-corpus-report.py:520`). Read those ranges when writing; do not import them (GB-CI-007 parser is CGB-specific, D-18 says not to extend it). The data shape: `ctest --test-dir build --show-only=json-v1` gives `tests[].properties[]` with `name == "TIMEOUT"`.

**Base-commit ratchet:** use `git show <base>:tests/ci/test-budget-allowlist` (immutable-commit read pattern, same as `read_boundary` in the Phase 8 verifier). On push-to-main the base is the parent; on PR the merge base.

**Seeding rule:** only from json-v1; the static grep of 40 values (acceptance_stall_diagnosis 1200, v02_consumer_controls 900, cgb_samesuite_apu_suite 600) is not authoritative.

**Interaction with sanitizers:** `cmake/ScaleSanitizerTimeouts.cmake` multiplies TIMEOUT x3 after all registration, and `tests/CMakeLists.txt` ~4662-4680 asserts exact scaled values for six tests (`age_stall_window=720` etc.). Keep those six tests and their bases intact when splitting.

---

### ASan sharding / bounded stall / nightly (16-03, D-19, D-23)

**Analog (shard):** `tests/acceptance/CMakeLists.txt:536-545`:
```cmake
add_test(NAME acceptance_stall_diagnosis
  COMMAND ${Python3_EXECUTABLE} -I ${PROJECT_SOURCE_DIR}/tests/scripts/verify-stall-report.py
    --runner-timeout ${GBB_STALL_RUNNER_TIMEOUT}
    --runner $<TARGET_FILE:gabbaboy-runner>
    --cases ${PROJECT_SOURCE_DIR}/${GBB_CASES}
    --workdir ${PROJECT_SOURCE_DIR}
    --failure-dir ${GBB_STALL_FAIL_DIR})
set_tests_properties(acceptance_stall_diagnosis PROPERTIES TIMEOUT 1200 COST 1200 WORKING_DIRECTORY ${PROJECT_SOURCE_DIR})
```
Shard by adding a single-replay argument to `verify-stall-report.py` (it currently runs the runner twice) and one named test per replay; keep `COST` so parallel ctest starts long tests first. New tests whose names start `acceptance_` are automatically run by the `linux-sanitizers-acceptance` shard (policy `CI_SANITIZER_SHARDS`, filter `-R '^acceptance_'`; the other shard uses `-E '^acceptance_'`). The inventory check `verify-test-inventory.sh` must see both. Do not put a bounded-case file at `tests/acceptance/cases.txt` (other tests count it); use a separate cases file in `tests/data` (RESEARCH).

**Analog (v02_consumer_controls split):** `gbb_add_v02_contract(v02_consumer_controls 900 ... verify-v02-consumers.py --self-test)` at CMakeLists ~1410-1414 with `set_tests_properties(v02_consumer_controls PROPERTIES COST 900)`. `verify-v02-consumers.py` has no per-consumer selector today; add one argument.

**Contract tests that read ci.yml text and break on YAML change** (RESEARCH): `ci_asan_parallel_contract`, `ci_asan_parallel_serial_selftest`, `ci_floor_parallel_contract`, `ci_floor_parallel_serial_selftest`, and `verify-cgb-corpus-inventory.py:716`. Update in the same commit as any `ci.yml` ASan edit.

**Temp hygiene (D-23)** `tests/check_sanitizer_timeout_policy.cmake` lines 1-10 (current):
```cmake
string(RANDOM LENGTH 8 ALPHABET 0123456789abcdef gbb_policy_nonce)
set(gbb_policy_root "${GBB_BINARY_DIR}/sanitizer-timeout-policy-${gbb_policy_nonce}")
file(MAKE_DIRECTORY "${gbb_policy_root}")
```
Change: before this, `file(GLOB stale LIST_DIRECTORIES true "${GBB_BINARY_DIR}/sanitizer-timeout-policy-*")` then `file(REMOVE_RECURSE ...)`; at the end (success path only) `file(REMOVE_RECURSE "${gbb_policy_root}")`. Failure paths already use `message(FATAL_ERROR ...)` (lines 22-26) so failures keep the dir. Add a CTest that asserts none remain after a pass.

**nightly-asan.yml:** no scheduled workflow exists. Copy job structure from the `linux-sanitizers-acceptance` job in `ci.yml` and the pinned-action style at ci.yml:411-414. It needs `issues: write` on one job; `check_ci` forbids any write permission in ci.yml only (policy 1359-1383), so judge nightly via a new `check_nightly()` and add it to `WORKFLOWS` (policy line 1607), not to `READONLY_WORKFLOWS` (line 1343).

---

### Timeout ledger `.github/ci-timeouts.json` + check (16-04, D-20)

**Analog:** `_check_fuzz_wait_budget` in `.github/scripts/verify-workflow-policy.py:301-334`: reads a job's `timeout-minutes` and compares arithmetic against configured values, raising `Reject("fuzz-wait-budget", f"{where} worst case {worst}s exceeds timeout-minutes {minutes} ({minutes * 60}s)")`. Copy the `Reject(code, message)` form and the integer-literal validation at 297 (`must be a positive integer literal`).

**Parsing:** use `read_workflow(path)` (policy ~44-172), the restricted YAML reader; do not add a YAML library.

**Wiring:** add `check_timeout_ledger(root)` and call it from the same dispatch as `check_ci`. Add mutations to `_mutations()` (list consumed in `self_test` at 2003-2040: tuples `(label, workflow, [(after, old, replacement)], expected_code)`) for: edited timeout, missing row, p50 over 50%, stale value, new job with no row, `provisional` at release head. Each mutation needs a unique anchor; a missing anchor raises `self-test anchor missing`. The ledger is a data file, not a workflow, so extend `_copy_fixture` (1610-1618) and the `target()` helper to copy `.github/ci-timeouts.json`.

**CTest reachability:** policy is not in CTest today (RESEARCH). Wrap with the `closeout_dispositions_controls` style (see CTest section) running `--check` and `--self-test`.

---

### Constants to update in `verify-workflow-policy.py` (serialized hotspot; D-02a)

**Source:** `.github/scripts/verify-workflow-policy.py`.

`CI_REQUIRED_NATIVE_NEEDS` (line 1251) must equal the `needs:` list of `required-native` (ci.yml 395-407) as a set; add `perf-gate`, `changes`, `planning-checks` per the plan that adds them:
```python
CI_REQUIRED_NATIVE_NEEDS = {"native-linux", "native-macos", "native-windows", "linux-sanitizers", "linux-sanitizers-tests", "linux-sanitizers-acceptance", "cmake-floor-3-25-3", "player-gate", "macos-player-package"}
```
`CI_SANITIZER_SHARDS` (1234-1247): exact `ctest ... --parallel 4 -E|-R '^acceptance_'` command lines (tuple of exact strings). Any shard change (D-19) edits these strings and the `ci.yml` run lines identically; D-09 removes the HDMA assertions on `--parallel 4`/`timeout-minutes: 45`.
`required-native` per-job `env` mapping (1371-1376 inside `check_ci`): the loop requires env vars `LINUX_SANITIZERS`, `LINUX_SANITIZER_TESTS`, `LINUX_SANITIZER_ACCEPTANCE`, `NATIVE_LINUX`, `CMAKE_FLOOR` each mapped to `${{ needs.<job>.result }}`. Adding a heavy job or the `kind=planning` branch needs matching entries. `str(gate.get("if", "")).strip() != "always()"` pin stays.
The aggregator currently treats `skipped` as failure (ci.yml 421-427 loop requires `success`). The planning branch is a deliberate loosening; add mutation controls for: `src/` file offered to the classifier, heavy job `skipped` when `kind=full`, and planning checks skipped.
`WORKFLOWS` (line 1607) lists workflow files copied into the self-test fixture; add `nightly-asan.yml` and any dispatch workflow here, otherwise their presence is never judged.
`READONLY_WORKFLOWS` (1343) and `CREDENTIAL_EXEMPT` (1344): `changes`, `planning-checks`, `perf-gate` must stay read-only and use `persist-credentials: false`.

After every workflow edit run `python3 -I .github/scripts/verify-workflow-policy.py --check` (about 0.1 s); after policy edits run `--self-test` (about 15 s).

---

### Planning-only classifier (16-04, D-21)

**Analog (aggregator side):** `ci.yml:395-435` `required-native` (job-level `if: always()`, `needs:`, step `env:` mapping `needs.<job>.result`, `run: |` bash loop). Extend rather than add a context.

**Analog (script side):** `.github/scripts/check-player-result.sh` (small gate called as `bash .github/scripts/check-player-result.sh "$PLAYER_GATE" "$PLAYER_REQUIRED" "$PLAYER_RESULT"`, pinned by `require_call` in policy). Put the classifier in `.github/scripts/` as pure Python so a CTest can feed name-status fixtures. For the classifier's CTest copy the Reject-code + `expect_exit.cmake` pattern. No existing classifier exists; the fail-closed conditions are in CONTEXT D-21.

---

### Hygiene checkers (16-05, D-24..D-27): plan-cap, LESSONS ids, STATE size, Playstead docs

**Analog:** `tests/scripts/verify-summary-coverage.py` (check_text, MUTANTS tuple of `(expected_prefix, mutated_text)`, `self_test`, `check_tree`, count output). Pattern at 255-296:
```python
MUTANTS = (
    ("duplicate-id D1", GOOD.replace("id: D2", "id: D1")),
    ("missing-ref D1", GOOD.replace(...)),
)
def self_test():
    count, errors = check_text(GOOD)
    ...
    for expected, text in MUTANTS:
        if text == GOOD: print("... FAIL mutant unchanged"); return 1
        _, errors = check_text(text)
        if not any(error.startswith(expected) for error in errors): ...
```
Each hygiene checker exposes `check_text(text) -> (count, errors)` with errors starting with a stable code, plus a temp-dir fixture test for tree-level behavior (as at 273-293). Controls are fixtures, never the live file (STATE size, D-26).

Details to pin:
- plan-cap: parse `**Plan cap**: N` under each active heading in `.planning/ROADMAP.md` (lines 76, 89, 102, 115 are 8/12/10/8); count `*-PLAN.md` via `GBB_LIVE_PHASES_DIR` (passed as an argument, no default).
- LESSONS: heading format is `### <ID> /` (RESEARCH). Duplicates today: `GB-FIXTURE-001` (lines 75, 225, 846), `GB-TEST-001` (162, 234).
- Playstead: edit targets README.md:46-47, `docs/native-integration.md:278-281`, `.planning/research/PRECEDENT.md:24,98-104`; required sentences "Playstead remains a future integration" (README) and "it is not a live GabbaBoy/Playstead integration" (native-integration.md) are asserted by `verify-v02-adoption.py:143,152` and must survive verbatim.

---

### Ledger freeze and version-agnostic edits (16-06, D-28/D-29)

**Analog:** `tests/scripts/verify-support-ledger.py`.

**`select_ledger`** (lines 64-84):
```python
def select_ledger(names: list[str], tag: str) -> str:
    tag_match = TAG.fullmatch(tag); release = version_key(tag_match)
    candidates = []
    for name in names:
        match = LEDGER_NAME.fullmatch(name)
        version = version_key(match) if match else None
        if version and version[:2] == release[:2] and version <= release:
            candidates.append((version, name))
    if not candidates:
        if release == (0, 2, 0):
            fail("exact v0.2.0 support ledger is missing")
        fail("no support ledger exists in this release's major/minor scope")
    return f"{LEDGER_DIR}/{max(candidates)[1]}"
```
This already implements most of D-28's binding. Hard-coded `0.2.0` sites (RESEARCH list): verify-support-ledger.py 378, 827, 872-874, 961-963, 1108-1141, 1239-1240, 1437, 1469-1502, 1633-1707, 1755-1766 (self-test encodes `("v0.2.1", "v0.2.0.md")` at 1757, which flips once `v0.2.1.md` exists), 1823-1824, 1896-1899, 2013-2046. Also `verify-v02-adoption.py:41,45,140,198,220,225,552,666-691,817,935`; `.github/workflows/release-rehearsal.yml:23` (`REHEARSAL_TAG: v0.2.0`, also 42, 156, 212).

**CLI** (`verify-support-ledger.py:2300-2311`): `--check-ledger` (static, CTest-visible, `v02_support_ledger`), `--check-current` and `--write-current` both need `--receipt` (hosted only), `--tag`, `--source-sha`, `--output`. `docs/support/v0.2.1.md` is created with `--write-current` in the D-31 window on the #75 branch, never on main earlier.

**CTest regex that pins the version** (CMakeLists 1405): `[=[support-ledger static pass version=0.2.0 cases=...]=]` in `gbb_add_v02_contract(v02_support_ledger 60 ...)`. Make `version=0\.[0-9]+\.[0-9]+`; the controls test at 1407-1410 pins a literal list of five control names (`unparseable-ledger` etc.), leave it.

**Freeze CTest (new):** model on the universal skeleton; digests from RESEARCH: tag blob `a542a5c01e236246f83d4f1b67aba20f2a9200e74e5ffe70b930daf9f3af2b8f`, working file `c47ff12b089fd386ebe1dd1a16d4ceaefc9fd60d072acdce510267c3dff19a9e`; read the tag blob with `git show v0.2.0:docs/support/v0.2.0.md`. Missing tag must fail (as with D-12). Use `hashlib.sha256`; controls: flipped byte, wrong pin, extra edit outside block.

**Release-notes needle:** `verify-v02-adoption.py --release-notes PATH` (argparse at 925-928, `group.add_argument("--release-notes", type=Path, metavar="PATH")`). Add the +8.3%/attribution needle in the same list the existing needles use (version token, "No CGB game-level evidence exists.", "unsigned and not notarized", exact-version ledger link), with a negative-control mutation that removes it. Read the existing needle list at 198-225 when implementing.

**Perf qualification (D-30):** `verify-v02-performance.py:141-175` (`verify_reviewed_disposition`) and 398-407; requires `schema_version` 1, `https` `review_reference`, `review_type == "independent"`, `decision == "accepted-with-disclosed-regression"`, bindings to `measurement_receipt_sha256`, `source_pair`, `workload`. No new schema; supply a receipt-bound disposition file.

---

### v0.3 disposition record (16-06, D-33)

**Analog:** `tests/scripts/verify-closeout-dispositions.py` (CLI 590-614: `--self-test`, `--check`, `--root`, `--dispositions`, `--scope`, `--receipt`; `Rejected(code, message)` error type; `REJECT <code>: <msg>` stderr) and its CTest `closeout_dispositions_controls` (CMakeLists 1456-1464: self-test drives the real CLI over a private fixture repository and rejects each named defect with its own diagnostic and no success line).

Do not edit the digest-pinned v0.2 `15.1-DISPOSITIONS.json` (it moves to the archive, see D-05). Create a new record (e.g. `.planning/phases/GB-16-.../16-DISPOSITIONS.json`) and a new CTest with its own `--min` count. The `pending-release` state is new schema; the checker accepts closure only with tag-bound receipt digests, per CONTEXT.

---

### Archive move and lint (16-01)

**Move:** `git mv .planning/phases/GB-07-* ... GB-15.1-* .planning/milestones/v0.2-phases/` (10 dirs, 578 files; counts per directory in RESEARCH 235). v0.1 layout is the precedent: `.planning/milestones/v0.1-phases/` (linked from `docs/mbc1-evidence.md:64-93`).

**Readers that embed a phase path (retarget list, RESEARCH 237-251):**
`verify-closeout-dispositions.py:37,64` (`PHASE_REL`, `published_receipt`), `verify-closeout-scan.py:31,66,155,161,168,378,402`, `verify-historical-limitations.py:39,99,673`, `test-cgb-red-evidence-privacy.py:12`, `test_hdma_remote_evidence.py:13` (loads checker via `importlib` by path), `verify-phase8-closure-contract.py:15`. Not in scope: `.planning/verify-v02-milestone-audit.py` (inside `.planning/`; move beside v0.2 audits per D-05), `verify-dense-input.py:103` (not a phase-path read).

**HDMA extraction (D-09):** source `.planning/phases/GB-13-cgb-hdma/verify-hdma-closure.py` (becomes `.planning/milestones/v0.2-phases/GB-13-cgb-hdma/verify-hdma-closure.py`); extract `lane_contract` (80), `lane_self_test` (150), `load_remote_evidence` (679), `validate_remote_evidence` (701) into `tests/scripts/verify-hdma-lane.py`; invocation shape stays `verify-hdma-lane.py --lane` and `--lane-self-test`. Retire `tests/scripts/phase13-handoff-continuity.test.cjs` and the non-lane GB-13 modes (`--prohibitions`, `--self-test`, `--handoff`) from CTest. Remove the CTest names tied to retired scripts from both CMake and `expected-tests.txt` in the same commit.

**Allowlist shape for lint (count-pinned):**
```python
# (file, max_hits, reason); a row whose observed hits are below max is stale and fails
ALLOW = (("tests/CMakeLists.txt", 1, "GBB_LIVE_PHASES_DIR definition"),)
```

**CMake variables (new, do not exist yet):** `GBB_LIVE_PHASES_DIR` = `${PROJECT_SOURCE_DIR}/.planning/phases` (the single allowlisted spelling) and `GBB_V02_PHASES_DIR` = `${PROJECT_SOURCE_DIR}/.planning/milestones/v0.2-phases`. Define both once near the top of the new `tests/cmake/archive.cmake`, included before first use. Because the lint scans `tests/` for the literal `.planning/phases`, the definition line is the single allowlisted hit (join the segments elsewhere is also lint-flagged, so do not obfuscate).

**Vacuity guards (D-08):** `summary_coverage` prints `files=143 entries=546` today and passes on an empty dir. Add `--min-files` to `verify-summary-coverage.py` (new argparse arg next to `--since`, at the end of `main()` before the success print: fail if `files < min_files` with its own `summary-coverage FAIL` line) and use `GBB_EXPECT_MIN_KEY=files` in the CTest. Live GB-16 sweep must tolerate zero (separate test, no minimum, or conditional).

---

### Hosted valgrind job, PR-closure, tag push, PR #75 edit (no analog)

No repo code to copy. Source guidance is CONTEXT D-14/D-15/D-31/D-32 and RESEARCH Pitfalls 5/9. Style anchors that do exist: `.github/workflows/fixture-repro.yml` for a `workflow_dispatch`-style artifact workflow and ci.yml checkout/pinning conventions (`persist-credentials: false`, `fetch-depth: 0`, 40-hex pins). Tag push (`historical/phase-08-boundary` on `96d5eec977bee99a0629499b89c737415e24184c`) and PR closures are executor `git`/`gh` actions, not file changes.

---

## Shared Patterns

### Immutable-commit reads (never live HEAD)
**Source:** `tests/scripts/verify-phase8-player-contract.py:27-36`. **Apply to:** Phase 8 verifiers (tag), ledger freeze (`v0.2.0` tag blob), test-budget base-commit ratchet, D-10 converted rows, 16-07 post-release boundary checker. CI needs `fetch-depth: 0` (tags and history), including in the new `planning-checks` job. Failing to resolve the revision must be a hard error, never a fallback.

### Anti-vacuity
**Source:** `tests/expect_exit.cmake` (`GBB_EXPECT_MIN_KEY`/`GBB_EXPECT_MIN_VALUE`, requires exactly one `KEY=<digits>`) and CMakeLists 2703-2719. **Apply to:** every directory sweep, lint, inventory, and self-test count. A checker must also print the count exactly once. Use `GBB_FORBID_REGEX` (expect_exit line 50-55) to forbid `files=0`-style output when a minimum is not suitable.

### Negative-control self-test with inactive-mutation guard
**Source:** `verify-uat-closure.py:195-232`, `verify-summary-coverage.py:255-296`, `verify-workflow-policy.py:2003-2040` (`rejected += 1` with `REJECT <code>:` match and `PASS:` absent). **Apply to:** all new checkers. AGENTS.md: every deliverable gets an automated check with a negative control.

### Reject-code diagnostics
**Source:** `verify-closeout-dispositions.py:603-611`, `verify-workflow-policy.py` (`Reject(code, message)`), `verify-uat-closure.py:258-260`. **Apply to:** perf gate, timeout ledger, classifier, disposition record. Print `REJECT <code>: <message>` to stderr, exit 1; the CTest regex pins the code, so a changed failure class is never mistaken for the expected one.

### Two-file CTest rule + Windows exclusion
**Source:** `cmake/ExpectedTests.cmake:1-34`, `tests/expected-tests.txt`. **Apply to:** every plan that adds or removes a test. Bash- or valgrind-dependent tests need the Windows `list(REMOVE_ITEM ...)` entry.

### Immutable fixtures
**Source:** CMakeLists 2723-2730 (SHA-256 pin, configure fails on drift). **Apply to:** `tests/data/*` canned cachegrind/timing files, the 14-UAT-REVIEW seed copy, the short stall case file.

### Restricted workflow YAML
**Source:** `verify-workflow-policy.py:44-172` (restricted reader), `ci.yml:411-414` pinned `uses: actions/checkout@<40hex> # v4.2.2`. **Apply to:** every workflow/job edit: block mappings only, no tabs/anchors/flow maps, 40-hex pins, read-only permissions except the single nightly job, no `pull_request_target`, no third-party actions.

### SUMMARY coverage block schema (every plan's SUMMARY.md)
**Source:** `verify-summary-coverage.py` `check_text`; AGENTS.md. **Apply to:** all seven plans. Block-style `verification` items with `kind` of unit/integration/e2e/automated_ui/other, `ref`, `status: pass`, `human_judgment: false`; no flow `{...}`, no `ctest` kind, no inline `#`. The `summary_coverage` CTest rejects violations (the `inline-comment-not-supported` mutant). The `ref` style used by the existing fixtures is a quoted command string such as `"ctest -R '^tracer$'"`.

### Commit hygiene
Titles use `fix`/`perf`/`test`/`ci`/`docs`/`chore`/`build` only (D-03); stage by path and never include `.planning/config.json` (owner's uncommitted edits); privacy-safe author; no changes under `src/` or `include/` (D-04).

## No Analog Found

| File | Role | Data Flow | Reason |
|---|---|---|---|
| hosted `perf-gate` job valgrind steps | CI job | batch | No valgrind or cachegrind use exists anywhere; valgrind is not installed locally. Only canned-output logic is locally testable. Use CONTEXT D-14/D-15 plus ci.yml job conventions. |
| `nightly-asan.yml` `gh issue` step and `schedule` trigger | CI workflow | event-driven | No scheduled workflow or job-level `issues: write` exists. `check_ci` forbids any write permission in ci.yml; use a dedicated `check_nightly()`. |
| planning-only classifier script | utility | transform | No path classifier in the repo; `check-player-result.sh` only shows the gate-script calling convention. |
| tag push, PR closures, PR #75 body edit, publication readback | operational | request-response | `gh`/`git` actions at execution time; the nearest recorded precedent is the v0.2.0 flow in `15-*` summaries and `docs/support/v0.2.0.md`. |

## Metadata

**Analog search scope:** `tests/CMakeLists.txt`, `tests/expect_exit.cmake`, `cmake/ExpectedTests.cmake`, `tests/expected-tests.txt`, `tests/scripts/` (all verifiers listed), `tests/acceptance/CMakeLists.txt`, `tests/check_sanitizer_timeout_policy.cmake`, `.github/scripts/verify-workflow-policy.py`, `.github/workflows/ci.yml`, `release-please-config.json`, `.release-please-manifest.json`, `docs/support/`.
**Files scanned (read):** about 16 in full or by range; tracked-source gate verified for the key analogs.
**Pattern extraction date:** 2026-10-24
**Caveats:** Line numbers drift after 16-01; re-grep anchors. Windows exclusion list and `ctest.xml` shard inventory (`verify-test-inventory.sh`) were not opened here; the planner should read `.github/scripts/verify-test-inventory.sh` before changing shard filters.
