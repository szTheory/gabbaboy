---
phase: GB-21-cgb-game-progress-and-scene-regressions
reviewed: 2026-11-02T08:24:05Z
source_revision: 893ecac8f70b2b6484c17686548f5ad091b7733b
depth: deep
files_reviewed: 12
files_reviewed_list:
  - docs/cgb-profile.md
  - docs/game-acceptance.md
  - docs/support/unreleased.md
  - tests/CMakeLists.txt
  - tests/cmake/game-evidence.cmake
  - tests/data/state-forks.json
  - tests/expected-tests.txt
  - tests/scripts/verify-cgb-candidates.py
  - tests/scripts/verify-cgb-game-evidence.py
  - tests/scripts/verify-cgb-progress.py
  - tests/scripts/verify-fixture-admission.py
  - tests/scripts/verify-scene-report.py
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
status: clean
---

# Phase GB-21 Plan 21-07: Code Review Report

**Reviewed:** 2026-11-02T08:24:05Z
**Depth:** deep
**Files Reviewed:** 12
**Status:** clean

## Summary

Earlier findings WR-01 through WR-06 are closed. At `893ecac8`, the pin parser accepts only no terminator, LF, or CRLF; malformed and symbolic pins reject, while immutable commit, ancestry, manifest, and blob checks remain intact.

## Narrative Findings (AI reviewer)

### WR-01: Admitted outcome can coexist with no-game documentation — CLOSED

**Severity:** WARNING
**Original issue:** The admitted-result branch required an `Admitted game:` marker but did not reject the existing no-game claim. I reproduced the acceptance before the fix with synthetic admitted/not-needed records and the committed no-game documentation.
**Fix verified:** Commit `213c9081` rejects outcome-incompatible markers in both directions and adds mutation controls. The current self-test passes with `rejected_controls=17`.

### WR-02: Candidate MIT and BSD license names bypass the prohibition filter — CLOSED

**Severity:** WARNING
**Original issue:** The license prohibition patterns did not include every license name present in the candidate records, leaving MIT and BSD-2-Clause wording unfiltered after the prior fix.
**Fix verified:** Commit `1e328e66` includes those identifiers and adds four mutation controls. The current self-test passes with `rejected_controls=21`. Direct checks rejected both forward and inverse claims for `MIT License`, `CC BY-NC-SA 4.0`, `Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International`, `GPLv3+`, `BSD-2-Clause`, and `CC BY-SA 4.0`. Five explicit-negation statements were accepted.

## Follow-up Review — 948d414a

- **Mutation-harness optimization:** `verify-cgb-candidates.py` now runs the admitted baseline once before its mutation set, rejects each invalid mutated record without invoking the synthetic runner, restores the exact baseline bytes in `finally`, and verifies the normal positive case after fallback-identity mutation. The correction in `948d414a` removes a runner-count assertion for fallback identity rejection because the preceding admitted primary is expected to run before fallback validation; the restored positive case is still required to invoke it exactly once. No correctness gap found.
- **Measured focused evidence:** Configure/build succeeded. `phase21_fixture_admission_controls` passed in 13.51 s (the earlier local run at the pre-optimization source was 42.66 s); `phase21_game_evidence` passed in 6.80 s; `phase21_game_evidence_controls` passed in 0.33 s. The evidence receipt identifies source `948d414a4eb34d68b4107630e431a9382983032a`, result `not-admitted`, model `CGB-CPU-E`, native `cgb` mode.
- **Canonical output path:** Generated CTest invokes `--write-evidence /Users/jon/projects/gabbaboy/build/phase21-evidence/result.json`; the integrated evidence test passed and wrote the receipt there.

## Follow-up Review — 15cb0c31

- **Sentence-scoped prohibition filter:** The license-pattern spans now stop at sentence punctuation/newlines, and negation is considered only in the sentence containing the matched claim. The three new mutations reject GPL, BSD, and CC claims after an unrelated negation in a preceding sentence. Same-sentence explicit negations still pass, including the candidate record's scoped no-go wording.
- **Verification:** `python3 -I tests/scripts/verify-cgb-game-evidence.py --self-test-controls --repo-root . --source-revision HEAD` passed with `rejected_controls=24`. Direct checks rejected three cross-sentence false claims and accepted three same-sentence explicit negations. No new findings.

## Follow-up Review — a0a82f99

### WR-03: Unrelated same-clause negation still suppresses an unsupported claim — CLOSED

**Severity:** WARNING
**Original issue:** The direct-modifier checks searched broad same-clause text and let an unrelated negation suppress a later prohibition claim. The contrastive cases `This is not a conclusion that the rights are settled, but GPL-3.0 prohibits this use.` and `GPL-3.0 does not prohibit documenting its terms, but it prohibits this use.` passed the prior checker.
**Fix verified:** Commit `72845e23` scans each prohibition verb against each nearby license match and scopes negation to the relevant verb/clause. Both contrastive cases now reject, with regression controls added at `tests/scripts/verify-cgb-game-evidence.py:586-600`.

### WR-04: Self-test reports more rejected controls than it executes — CLOSED

**Severity:** WARNING
**Original issue:** The previous self-test printed 26 rejected controls while instrumentation counted only 24 `_expect_reject` executions.
**Fix verified:** Commit `72845e23` adds the two missing contrastive rejection controls. Instrumenting `_expect_reject` during the current immutable self-test counts 26 executions, matching its `rejected_controls=26` output; the four explicit-negation positives are reported separately.

- **Prior verification:** Before commit `72845e23`, the checker printed `rejected_controls=26` while direct instrumentation counted 24 expected rejections. The four explicit-negation positives passed; same-clause contrastive claims exposed WR-03.

## Follow-up Review — 72845e23

- **Final focused verification:** The per-verb/per-license scan independently evaluates both contrastive claims; the source-bound immutable self-test at `72845e23cb351709c2fefd544dbdde6367b11a81` rejects both. The four explicit-negation positive controls remain accepted.
- **Contrastive false claims:** The two same-sentence cases from WR-03 now fail as unsupported prohibition claims. The three earlier cross-sentence unrelated-negation controls continue to pass.
- **Explicit negations:** All four positive negation checks pass: `GPL-3.0 does not prohibit this use`, `This use is not prohibited by BSD-2-Clause`, `This is not a conclusion that CC BY-NC-SA prohibits this use`, and `MIT never prohibits this use`.
- **Full immutable self-test:** `python3 -I tests/scripts/verify-cgb-game-evidence.py --self-test-controls --repo-root . --source-revision HEAD` passed and emitted `outcomes=3 accepted_negations=4 rejected_controls=26`. Direct instrumentation counted 26 `_expect_reject` executions.
- **Disposition:** No remaining findings.


## Follow-up Review — 9a0ab07d

- **Repeated-license/pronoun cases:** The immutable controls reject the claim following a semicolon after a negated license sentence, the pronoun claim after a sentence break, and the pronoun claim after a semicolon. These check that the previous license reference cannot make a later unqualified “it prohibits” assertion look explicitly negated.
- **Explicit negations:** All four accepted controls still pass.
- **Source-bound verification:** `python3 -I tests/scripts/verify-cgb-game-evidence.py --self-test-controls --repo-root . --source-revision 9a0ab07d2c0ba750f75797d84b5fff6d18d3dd25` passed with `outcomes=3 accepted_negations=4 rejected_controls=29 subjects=synthetic-only`.
- **Disposition:** No remaining findings.


## Follow-up Review — a58c52dd

- **Unrelated `and` clause:** The new mutation control `This is not a conclusion that rights are settled, and MIT License prohibits this use.` is rejected as an unsupported prohibition. The conjunction splits the unrelated negated conclusion from the prohibition claim.
- **Coordinated GPL/BSD negation:** The positive control `This is not a conclusion that GPL-3.0 and BSD-2-Clause terms prohibit this use.` remains accepted; the coordinated license names remain within the explicitly negated conclusion.
- **Other explicit negations:** The four previously accepted negation controls still pass.
- **Source-bound verification:** `python3 -I tests/scripts/verify-cgb-game-evidence.py --self-test-controls --repo-root . --source-revision a58c52dd15e3da2b9ef36a55c3e71c899b6941a4` passed with `outcomes=3 accepted_negations=5 rejected_controls=30 subjects=synthetic-only`.
- **Disposition:** No remaining findings.


## Follow-up Review — 6d14f9d1

- **CTest inventory and registration order:** The seven Phase 21 tests are present in `tests/expected-tests.txt`; `game-evidence.cmake` is included before `gabbaboy_verify_registered_tests()`, so configuration validates the complete inventory.
- **Debug scene-report control:** The synthetic promotion check invokes `ctest -C Debug`, which selects the configuration-specific executable on multi-configuration generators.
- **Focused verification:** `ctest --test-dir build -C Debug --output-on-failure -R '^(phase21_.*|acceptance_cgb_progress_(controls|tracer))$'` passed all nine tests on this revision.

### WR-05: Failure-dump path parser truncates Windows paths containing spaces — CLOSED

**Severity:** WARNING
**File:** `tests/scripts/verify-cgb-progress.py:920`
**Issue:** The `ppm=(\S+)` expression stops at whitespace. `run_observations` uses `tempfile.TemporaryDirectory`, whose Windows temp root can include a spaced user directory; the C runner emits the unquoted full `ppm=<path>`, so the captured value is truncated and normalized comparison fails even when the dump was written correctly. I reproduced the truncation with a synthetic `C:\Users\Jane Doe\...` output value.
**Fix verified:** Commit `d066a0fb` captures the complete `ppm=` field through line end before trimming trailing whitespace and normalizing host path separators/case. Its self-test includes an unquoted `C:\Users\Jane Doe\...` path with mixed separators, and passes.


## Follow-up Review — d066a0fb

- **Windows path case:** The parser now captures `ppm=` through line end, preserving spaces. Its self-test verifies normalization of the mixed-separator path `C:\Users\Jane Doe\Temp\failure-dumps/control.ppm` against the expected Windows path.
- **Focused verification:** `ctest --test-dir build -C Debug --output-on-failure -R '^(phase21_.*|acceptance_cgb_progress_(controls|tracer))$'` passed all nine tests on this revision.
- **Disposition:** No remaining findings.


## Follow-up Review — b8f80f48

- **Line-ending handling:** LF and CRLF positive pin controls pass, as does the focused `fixture_admission_controls` CTest (1/1). The textual `refs/heads/main` symbolic pin is rejected. After pin parsing, `check_commit` still requires a full lowercase 40-hex commit object; ancestry and exact pinned manifest/file bytes are still checked, so LF/CRLF support does not loosen the immutable source binding.
- **Full-suite evidence:** The execution record for this head reports the full CTest suite passed 1724/1724; this review independently reran the fixture-admission controls.

### WR-06: Admission pin accepts a lone carriage return terminator — CLOSED

**Severity:** WARNING  
**File:** `tests/scripts/verify-fixture-admission.py:767`  
**Issue:** The expression `[0-9a-f]{40}\r?\n?` makes carriage return and newline independently optional, so it accepts 40 lowercase hex digits followed by a lone `\r`. `rstrip("\r\n")` then removes that character and `check_commit` accepts the otherwise valid commit. This format is outside the stated LF/CRLF normalization and malformed-pin rejection contract. Directly evaluating the parser pattern confirms LF, CRLF, and lone CR all match; the self-test only covers the first two positives and a symbolic negative.
**Fix verified:** Commit `893ecac8` uses `[0-9a-f]{40}(?:\n|\r\n)?` and adds a bare-CR negative mutation. LF and CRLF positives, plus symbolic and bare-CR rejection, pass in the fixture-admission controls.


## Follow-up Review — 893ecac8

- **Pin endings:** The grouped ending accepts no terminator, LF, and CRLF; it rejects a lone CR and symbolic content. The focused `fixture_admission_controls` CTest passed 1/1, and direct pattern checks confirmed each form.
- **Immutable admission binding:** The pin remains constrained to a full lowercase 40-hex commit; the checker still verifies that commit exists, is in current history, and contains byte-identical manifest and fixture blobs. The line-ending allowance applies only to the pin text.
- **Focused suite:** The execution record for this head reports the 10-test selection passed. This review independently reran `fixture_admission_controls` successfully.
- **Disposition:** No remaining findings.

---

_Reviewed: 2026-11-02T08:24:05Z_
_Reviewer: the agent (gsd-code-reviewer)_
_Depth: deep_

## Executor Follow-up — e0b5305d

- The final delta normalizes the configured CMake source directory using the host platform's path rules before comparison. It reads one cache value and continues rejecting a source/build mismatch.
- Synthetic admission manifests/notices are serialized directly to UTF-8 bytes, preserving exact Git-pinned bytes on Windows. Production notice and admission policy are unchanged.
- Focused scene and candidate controls pass locally; the full final-head CTest suite passes 1724/1724. This change adds no network, filesystem, or authorization surface.
- **Disposition:** No new findings. Independent review remains at `893ecac8`; the exact-head Windows PR rerun is pending.

## Executor Follow-up — 9bed35ce

- Windows CI showed that `.py` synthetic runners cannot be launched directly as Win32 executables. The candidate checker now invokes them with the current Python interpreter in isolated mode.
- The synthetic scene checker ran CTest with `-C Debug`, but its inventory query omitted the configuration. The inventory query now uses the same `Debug` configuration.
- The two focused Phase 21 controls pass, and the complete serial local suite passes 1,724/1,724 under the unchanged 60-second CTest cap. The source-bound receipt identifies this source as `game=not-admitted`, `CGB-CPU-E`, native `cgb`.
- The changes add no network, file-access, authorization, or dependency surface. Independent review at `893ecac8` remains clean; final exact-head PR Windows and installed-consumer checks remain necessary.

## Executor Follow-up — 66ee663b

- The exact-head Windows diagnostic at `6d552502` found that the scene control compared a CTest JSON path using forward slashes against a Windows-native `pathlib.Path` string using backslashes. The checker now normalizes both sides and the synthetic control exercises mixed separators.
- The fix only changes local path matching inside the source-bound test checker; it adds no new inputs, filesystem access, network, authorization, or dependency surface.
- The synthetic controls report 17 passing controls. Configure, build, and all 1,724 CTests pass at the unchanged 60-second project budget on this revision. Exact-head Windows PR status must be read on PR #140's current head.
- **Disposition:** No security or correctness findings remain locally; the PR event must confirm the Windows behavior on the hosted runner.
