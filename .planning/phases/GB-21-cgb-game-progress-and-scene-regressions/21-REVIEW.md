---
phase: GB-21-cgb-game-progress-and-scene-regressions
reviewed: 2026-11-02T18:13:04Z
depth: standard
files_reviewed: 25
files_reviewed_list:
  - CMakeLists.txt
  - docs/cgb-game-candidates.md
  - docs/cgb-profile.md
  - docs/game-acceptance.md
  - docs/scene-feedback.md
  - docs/support/unreleased.md
  - src/accept/gbb_accept.h
  - src/accept/predicate.c
  - src/runner/acceptance.c
  - tests/CMakeLists.txt
  - tests/acceptance/CMakeLists.txt
  - tests/acceptance/cases-cgb-colour.txt
  - tests/ci/test-budget-allowlist
  - tests/cmake/game-evidence.cmake
  - tests/data/cgb-candidates/potion-panic.json
  - tests/data/cgb-candidates/ucity-1.3.json
  - tests/data/state-forks.json
  - tests/expected-tests.txt
  - tests/scripts/test_cgb_candidate_order.py
  - tests/scripts/verify-cgb-candidates.py
  - tests/scripts/verify-cgb-game-evidence.py
  - tests/scripts/verify-cgb-progress.py
  - tests/scripts/verify-fixture-admission.py
  - tests/scripts/verify-scene-report.py
  - tests/test_acceptance_lib.c
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
source_revision: abed700d77e490f2de2ea1635234b65b68d2e9d4
status: clean
---

# Phase GB-21: Code Review Report

**Reviewed:** 2026-11-02T18:13:04Z  
**Depth:** standard  
**Files Reviewed:** 25  
**Source boundary:** `abed700d77e490f2de2ea1635234b65b68d2e9d4`  
**Status:** clean

## Summary

The original evaluation scope contained 24 explicit source files and was reported `degraded` solely because the resolver had no task-commit rows; it used `phase-range` from base `a0b81749e19056bf0d8555256e5d64da89017555`. Plan 21-08 adds `CMakeLists.txt` to the phase diff, so this review covered the full 25-file source union. I also inspected the two transitive runner inputs added by CR-06, `src/core/gbb_accept_input.h` and `cmake/StateVersion.cmake`.

All prior review findings are closed at this boundary:

- **CR-01 closed:** replay requires the CGB CPU E model and validates exact acceptance and receipt field sets, CGB profile, native CGB mode, and shared hit time.
- **CR-02 closed:** the supplied runner must match the independently qualified canonical CMake target and stay byte-identical through replay; structured observations are parsed and checked, so success-marker-only output is rejected.
- **CR-03 closed:** replay loads case and input bytes from the admitted historical Git revision and requires the working copies to match before candidate execution.
- **CR-04 closed:** historical receipt source IDs and runner hashes remain immutable. Current replay uses a separate qualification bound to the selected source revision, build qualification, input hashes, writer, canonical runner path, and runner digest.
- **CR-05 closed:** replay compares checkpoint timing/RGB555 and all supported aggregate end-time, rolling RGB555, and PCM values. Synthetic valid-but-changed observations are rejected with the observation-mismatch reason.
- **CR-06 closed:** CMake and Python each contain the same 24 unique runner inputs. The compiled runner dependency closure has no project-local C/C++ input missing from the manifest; the root CMake file's runner-relevant local include is the listed `cmake/StateVersion.cmake`. Both newly added inputs have separate dirty-source and post-qualification drift controls, which verify rejection before runner invocation.

The synthetic control suite passed with 69 negative controls and six positive replay controls. I configured and rebuilt only `gabbaboy-runner` at the exact review boundary, generated its current qualification receipt, and independently validated that receipt at `abed700d`; no candidate game ROM or candidate upstream source was executed. The current receipt binds the exact 24 inputs and the runner artifact. `21-08-SUMMARY.md` now lists only `GAME-02` as completed and explicitly says `FIXT-01` remains Pending; the requirements ledger also retains that pending status.

## Narrative Findings (AI reviewer)

No findings. The reviewed source scope meets the phase contracts at the stated boundary.

---

_Reviewed: 2026-11-02T18:13:04Z_  
_Reviewer: the agent (gsd-code-reviewer)_  
_Depth: standard_

## Supplemental Delta Review

**Reviewed source:** `ca17216b22d0d9f2fb742c8baed3e1543bc307e1`  
**Scope:** the post-review fixture-control optimization in `tests/scripts/verify-cgb-candidates.py`.  
**Status:** clean; no correctness or security findings.

All 17 runner text controls still execute `_run_admitted_candidate` and check their expected rejection codes, including optional validator detail suffixes; this count includes the separate `unqualified-build` mutation. Existing CLI and end-to-end controls remain registered. The focused synthetic control test passed with 69 negative controls and six replay positives. No candidate ROM or upstream source was executed.

The delta review made no source edits.

## Supplemental Delta Review — Windows CMake paths and fixture bytes

**Reviewed source:** `bbd8f8390cb197840ad4091de8bd70170015516a` (delta from `ca17216b22d0d9f2fb742c8baed3e1543bc307e1`).
**Scope:** `tests/scripts/verify-cgb-candidates.py` and `tests/scripts/test_cgb_candidate_order.py`; Windows CMake path matching and synthetic fixture byte serialization are the changed behavior.
**Result at reviewed HEAD:** 1 warning; the current working-diff follow-up below resolves it.

The supplied local full-suite evidence is 1,718/1,718 CTests at this HEAD. That local result does not qualify Windows behavior.

### WARNING — Path keys fold case on case-sensitive filesystems

**File:** `tests/scripts/verify-cgb-candidates.py:2245-2247,2444-2449`
**Issue:** `cmake_source_path_key` case-folds every path, including POSIX paths where case distinguishes files. If a compile database contains distinct case-only source paths, the `next` lookup can select the wrong translation unit and inspect its `GBB_BUILD_QUALIFIED` flag. The new unit control rejects a different suffix, but does not test a case-only neighbor.
**Fix:** Normalize slash styles, then use `os.path.normcase(PureWindowsPath(...).as_posix())` so case folding follows the host platform. Add a case-only neighbor negative control.

The LF-byte changes write the synthetic JSON, case file, runner, and admission pin as explicit bytes, avoiding Windows text-mode newline translation before Git pinning. Existing synthetic fixture controls exercise those files. The Windows path unit control covers slash variants and a non-case-only neighbor. **Pre-existing context:** subprocess timeout cleanup still targets only the direct child, and its unit control uses a single sleeping child; both are unchanged from the prior reviewed source and excluded from delta findings. No Windows qualification is claimed here.

### Follow-up — case-aware path normalization

The current working diff resolves the warning above: `cmake_source_path_key` now applies `os.path.normcase` after slash normalization with `PureWindowsPath`. Its unit control asserts that backslash and forward-slash variants match, a different suffix does not match, case variants match on Windows, and case variants remain distinct on POSIX.

Focused unit evidence after this edit: 11 tests passed. A full CTest rerun is pending. The earlier 1,718/1,718 result predates this working edit and does not qualify it or establish Windows qualification.

## Supplemental Delta Review — compile-database source matching

**Reviewed delta:** `ff7e51a22e8176c90ee7a166354dafed7ea4d88d` through `34acbc99783fc796d3632017fb1d07d41b77bf30`.
**Scope:** `tests/scripts/verify-cgb-candidates.py` and `tests/scripts/test_cgb_candidate_order.py`.
**Result:** The POSIX case-preservation warning above is resolved. Two warnings remain in compile-command validation and failure diagnostics.

The source-entry matching changes correctly resolve relative compile-database paths, use Windows filesystem identity for short/long path variants, and preserve lexical case distinctions on POSIX. The unit controls cover slash variants, wrong-suffix rejection, Windows case-insensitive identity, and POSIX case-sensitive identity. Local evidence reports 13 Python unit tests and the focused fixture-admission CTest passing. The final full-suite run and fresh hosted qualification are still in progress; this review does not claim Windows qualification.

### WARNING — Flattened compiler arguments can produce a false macro match

**File:** `tests/scripts/verify-cgb-candidates.py:2284-2292,2493-2497`
**Issue:** `cmake_compile_command` joins the standard `arguments` array with spaces, and the following regular expression searches the flattened text without respecting argument or shell-quote boundaries. A single argument such as `-DOTHER=x -DGBB_BUILD_QUALIFIED=1` can therefore look like a separate qualification flag even though the compiler receives it as one argument. This can make the synthetic CMake control accept an unqualified compile command.
**Fix:** Preserve argv boundaries for `arguments` entries and inspect exact flag tokens; parse the `command` string into argv with platform-appropriate quoting before applying the same token check. Add a negative control with a macro-looking substring inside one argument.

### WARNING — Candidate paths are count-bounded but not length-bounded in diagnostics

**File:** `tests/scripts/verify-cgb-candidates.py:2499-2506`
**Issue:** The diagnostic limits output to four candidate paths and 512 command characters, but it does not truncate each candidate path. Since `compile_commands.json` is accepted up to the checker’s 8 MiB file limit, a malformed or synthetic entry can still produce a multi-megabyte error message and flood test logs.
**Fix:** Truncate each displayed candidate path and cap the complete diagnostic string to a small fixed size while retaining the total match count. Add an oversized-path negative control that asserts the diagnostic limit.

## Supplemental Delta Review — exact compile-command semantics

**Reviewed delta:** `34acbc99783fc796d3632017fb1d07d41b77bf30` through `0ddacc0d597a341a95abcacb071f20bc2b981992`.
**Scope:** `tests/scripts/verify-cgb-candidates.py` and `tests/scripts/test_cgb_candidate_order.py`.
**Result:** The two prior warnings are resolved: compiler arguments retain token boundaries, and candidate-path diagnostics are capped at 96 characters per path, four paths, and 384 characters total. Source-entry matching also rejects a source resolved under the declared build directory when that is not the expected source. Three warnings remain: two in define interpretation and one in diagnostic escaping.

The matching controls cover relative entries with and without a declared directory, a wrong directory, wrong suffix, slash variants, and the expected Windows/POSIX case behavior. The oversized-path control checks the total diagnostic cap. Local evidence reports 15 Python unit tests and the focused fixture-admission CTest passing at `0ddacc0d`; the final full suite and fresh exact-head hosted checks are still running or pending.

### WARNING — Later undefines and unsupported define values are ignored

**File:** `tests/scripts/verify-cgb-candidates.py:2286-2320`
**Issue:** `cmake_build_qualified_value` records only matching `-D`/`/D` tokens whose value is `0` or `1`; it ignores later `-U`/`/U` tokens and other definitions of the same macro. A command containing `-DGBB_BUILD_QUALIFIED=1 -UGBB_BUILD_QUALIFIED` or `-DGBB_BUILD_QUALIFIED=1 -DGBB_BUILD_QUALIFIED=2` still returns `1`, even though the effective compile definition is not `1`.
**Fix:** Track the target macro's definition and undefinition operations in command order, or reject any undefinition, malformed value, or duplicate definition. Add controls for both `-U`/`/U` and a later non-binary value.

### WARNING — Literal quotes in argv entries are stripped

**File:** `tests/scripts/verify-cgb-candidates.py:2302-2315`
**Issue:** Quote stripping is applied to entries from the compile-database `arguments` array, whose elements are already individual argv values. An argv element such as `"'-DGBB_BUILD_QUALIFIED=1'"` is therefore converted into a valid-looking define even though the literal quote characters are part of the argument. This leaves a false-positive path in the exact-token check.
**Fix:** Treat `arguments` elements as literal argv tokens without stripping quotes. Apply quote handling only while parsing the `command` string, with syntax appropriate to the host command format, and add a quoted-literal argv negative control.

### WARNING — Bounded candidate paths are emitted without escaping

**File:** `tests/scripts/verify-cgb-candidates.py:2323-2328,2532-2535`
**Issue:** Candidate path strings are truncated and length-capped, but then joined and interpolated into the rejection message raw. A POSIX filename may contain newline or terminal control characters, so a crafted compile-database path can forge log lines or alter terminal output when this failure is reported.
**Fix:** Escape candidate strings with JSON encoding or `repr` before applying the total length cap. Add a control-character path case and assert the diagnostic contains escaped text only.

## Follow-up — ambiguous define and argv-quote correction

**Reviewed source:** `f94a8617efdd6cd82f477cd8b26f33e85a020a1f`, following `0ddacc0d597a341a95abcacb071f20bc2b981992`.
**Scope:** the same two CMake compile-database helper files.
**Result:** The duplicate/unsupported-define and literal-argv-quote warnings above are resolved by the follow-up. The diagnostic length cap and declared-directory rejection also remain in place. One effective-definition warning and one diagnostic-escaping warning remain.

The helper now preserves `arguments` entries verbatim, strips quote wrappers only after parsing the `command` form, and counts every definition of `GBB_BUILD_QUALIFIED`, rejecting duplicates and non-binary values. The controls cover a quoted argv item and a valid-plus-unsupported duplicate. Local evidence reports 15 Python unit tests passing after this edit. The build-bound fixture-admission CTest and final full suite are pending the GSD commit; no fresh exact-head hosted qualification is claimed.

### WARNING — Undefinitions are absent from the effective macro check

**File:** `tests/scripts/verify-cgb-candidates.py:2304-2327`
**Issue:** The parser counts `-D` and `/D` definitions but ignores `-U` and `/U` undefinitions. A command with `-DGBB_BUILD_QUALIFIED=1 -UGBB_BUILD_QUALIFIED` still returns `1`, although the compiler sees the macro undefined after the later option.
**Fix:** Include `-U`/`/U` operations in the ordered macro-state check, or reject any undefinition of this macro. Add a negative control for an undefine after the define.

### WARNING — Candidate path diagnostics still permit log-control injection

**File:** `tests/scripts/verify-cgb-candidates.py:2330-2335,2539-2542`
**Issue:** The helper now bounds path lengths and total diagnostic size, but it inserts raw path characters into the rejection text. POSIX filenames may contain newlines or terminal control characters, which can forge or alter test/CI log output.
**Fix:** Escape each path (for example with `repr` or JSON string encoding) before applying the existing per-path and total caps. Add a control-character path control.

## Owner-approved bounded rescope — final independent review

**Reviewed source:** `e0845db5841a1d56d8a297cbfaa3e0811af6ad67`.
**Scope:** The authorized Phase 21 parser and diagnostic correction recorded in [21-RESCOPE.md](21-RESCOPE.md), including a related Windows command-quoting refinement raised during review.
**Result:** No remaining scoped findings.

The qualification parser rejects target-macro undefinitions, duplicate or unsupported definitions, and ambiguous repeated operations across combined and split `-D`, `/D`, `-U`, and `/U` forms. A deterministic Windows-mode control confirms that a single-quoted command token is treated literally and rejected, while a double-quoted define remains accepted. Candidate path diagnostics use ASCII-safe JSON escaping before the existing per-path and total bounds.

Both the scoped code reviewer and security auditor independently checked `e0845db5` and found no remaining issue in this scope. The 18 Python unit tests, configure/build, and focused `phase21_fixture_admission_controls` CTest passed. The full serial CTest run at `e0845db5` passed 1,717/1,718; `v02_source_archive_controls` reached its existing 90-second timeout and then passed its isolated same-head retest in 77.17 seconds, with the limit unchanged. This means every registered test has passing evidence across the full run and focused retest; it does not mean one full invocation was all-green. Exact-head hosted qualification remains pending until PR #140's required checks finish.
