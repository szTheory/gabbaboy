---
phase: GB-09-mbc3-deterministic-rtc-and-cartridge-persistence
reviewed: 2026-10-12T13:02:54Z
depth: standard
files_reviewed: 2
files_reviewed_list:
  - cmake/VerifyDocContract.cmake
  - tests/CMakeLists.txt
findings:
  critical: 0
  warning: 5
  info: 3
  total: 8
status: issues_found
---

# Phase 9: Code Review Report (scoped re-review: host-guide contract check)

**Reviewed:** 2026-10-12T13:02:54Z
**Depth:** standard
**Files Reviewed:** 2
**Status:** issues_found

> **Scope note.** This is a scoped re-review. It covers only the host-guide contract check added after Phase 9's main review: `cmake/VerifyDocContract.cmake` (whole file) and the lines of `tests/CMakeLists.txt` changed since `a3dae02`, which are the `native_guide_rtc_contract`, `doc_contract_undeclared_selftest` and `doc_contract_missing_selftest` registrations. The earlier full-phase review is preserved at commit `486c7bd`, and its findings and dispositions are in `09-REVIEW-DISPOSITION.md`. This file replaces that review and does not reopen it.

## Summary

The check does what it says on the current inputs. `ctest --test-dir build -R 'native_guide_rtc_contract|doc_contract_'` passes 3/3, and the positive test prints `doc-contract pass identifiers=23 phrases=12`. Every one of the 23 `gbb_*`/`GBB_*` identifiers in `docs/native-integration.md` is declared in real code, not just in comments: I checked this with comments stripped from `gabbaboy.h`, plus `examples/relocated-c/CMakeLists.txt`. Each of the 12 phrases appears exactly once in the whitespace-collapsed guide.

Things that hold up:
- Identifiers are captured by `[A-Za-z0-9_]+`, so they cannot carry regex metacharacters into the whole-word `MATCHES`.
- `$0F`/`$10` in the phrases survive CMake and CTestTestfile escaping (the phrase count of 12 proves the list arrived intact).
- The semicolon-joined `GBB_DECLARATIONS` and `GBB_REQUIRED` `-D` arguments split correctly.
- `PASS_REGULAR_EXPRESSION` cannot hide a failure, because the pass line is only printed after the last `FATAL_ERROR` gate.
- Whole-word matching works: a probe guide naming the prefix `gbb_rtc` was rejected.
- Every construct used exists in CMake 3.25. The only local CMake is 4.4.3, so I could not run the check on 3.25 itself.

The defects are ways the check can **pass without checking**. A name that survives only in a header comment counts as "declared". Empty phrase elements count as satisfied phrases. Phrases hidden in HTML comments or in unrelated sections satisfy the contract. Non-prefixed API names the guide relies on (struct fields) are never checked. The self-tests lock in none of the subtle invariants. Each of these was reproduced with `cmake -P` probes (commands summarised under each finding).

## Warnings

### WR-01: A name that survives only in a comment counts as "declared", so the rename drift the check targets can pass

**File:** `cmake/VerifyDocContract.cmake:33-37,48`
**Issue:** `declared` is the raw text of each declaring file, comments included. The header's prose restates API names in comments, for example `gabbaboy.h:186`, "wall-clock catch-up happens only through gbb_rtc_catch_up". Suppose `gbb_rtc_catch_up` is renamed in the prototype at line 219 and the line-186 comment is missed. The guide's stale `gbb_rtc_catch_up` still matches the comment, and the check passes. That is exactly the "renamed or removed name" drift the file header (lines 3-6) says it catches.
Reproduced: a declaring file containing only `/* gbb_removed_fn is gone */` and a guide using `` `gbb_removed_fn` `` gives `doc-contract pass identifiers=1 phrases=1`, rc=0. The same hole applies to `#` comments in the example `CMakeLists.txt`.
**Fix:** Strip comments before building `declared`. Choose the syntax from the file extension:
```cmake
foreach(declaring_file IN LISTS GBB_DECLARATIONS)
  file(READ "${declaring_file}" contents)
  if(declaring_file MATCHES "\\.(h|c)$")
    string(REGEX REPLACE "/\\*([^*]|\\*+[^*/])*\\*+/" " " contents "${contents}")
    string(REGEX REPLACE "//[^\n]*" " " contents "${contents}")
  else()
    string(REGEX REPLACE "#[^\n]*" " " contents "${contents}")
  endif()
  string(APPEND declared " ${contents} ")
endforeach()
```
Then add a self-test where the only occurrence of a name is inside a comment, and expect `doc-contract-undeclared`.

### WR-02: Empty phrase elements are counted and pass, which defeats the "nonempty" requirement

**File:** `cmake/VerifyDocContract.cmake:23-27,55-62`
**Issue:** The input guard only rejects an empty *string*. `-DGBB_REQUIRED=;` passes the guard, and `foreach(... IN LISTS ...)` then iterates two empty elements. `string(FIND doc "" at)` returns 0, so each empty element counts as a found phrase.
Reproduced: `cmake -DGBB_DOC=a.md -DGBB_DECLARATIONS=gabbaboy.h "-DGBB_REQUIRED=;" -P VerifyDocContract.cmake` prints `doc-contract pass identifiers=1 phrases=2`, rc=0.
The registered test pins `phrases=12`, so an accidental `""` *replacing* a phrase is caught there. But adding a 13th phrase as an empty element would bump the count. Either way, the script's own contract ("required, nonempty") is false, and any future caller without a count pin can be satisfied vacuously.
**Fix:**
```cmake
foreach(phrase IN LISTS GBB_REQUIRED)
  if(phrase STREQUAL "")
    message(FATAL_ERROR "doc-contract-empty-phrase: GBB_REQUIRED has an empty element")
  endif()
  ...
```

### WR-03: Phrases match anywhere, including inside HTML comments and unrelated sections

**File:** `cmake/VerifyDocContract.cmake:29-31,57`
**Issue:** The guide text is only whitespace-collapsed before `string(FIND)`. If a required behaviour is moved into an `<!-- ... -->` block, it no longer renders, yet it still satisfies the contract.
Reproduced: a guide whose only "once per open" sits in `<!-- once per open -->` passes, rc=0.
Several phrases are also generic enough to be satisfied by an unrelated sentence elsewhere in the guide: "once per open", "never advances it", "as an input event". Today each occurs once, in the RTC bullet (lines 88-100). But nothing ties a phrase to the `gbb_rtc_catch_up` paragraph, so deleting that paragraph's sentence while another section says "...once per open..." still passes.
**Fix:** Strip HTML comments before matching:
```cmake
string(REGEX REPLACE "<!--([^-]|-[^-]|--+[^->])*--+>" " " doc "${doc}")
```
Then do one of the following:
- anchor generic phrases with neighbouring text, e.g. `"the host clock once per open"`; or
- make the script take an optional `GBB_SECTION_START` literal and restrict `doc` to the text after it (up to the next `\n- \`` bullet or heading) before checking the phrases.

### WR-04: The identifier check covers only `gbb_`/`GBB_` names, so struct fields the guide tells hosts to read are never checked

**File:** `cmake/VerifyDocContract.cmake:39`; `docs/native-integration.md:76`
**Issue:** The guide tells hosts to "Check both `reason` and `consumed_half_dots`". These are fields of the run-result struct. Renaming either field in `gabbaboy.h` leaves the guide stale and the check green, because line 39 only extracts `(gbb|GBB)_...` tokens. The file header (lines 3-4) claims the check catches "a renamed or removed name (API symbol ...)", but non-prefixed API names are not covered.
**Fix:** Also extract back-ticked C identifiers (`` `([A-Za-z_][A-Za-z0-9_]*)` ``) and require them to be declared too. Use a short explicit allowlist (e.g. `GBB_IGNORED_NAMES`) for non-API tokens such as `find_package` and `CMAKE_PREFIX_PATH`. Alternatively, add `"\`reason\` and \`consumed_half_dots\`"` to a phrase list and check the field names with the identifier pass.

### WR-05: The self-tests do not lock in the check's subtle invariants

**File:** `tests/CMakeLists.txt` (the `doc_contract_undeclared_selftest` / `doc_contract_missing_selftest` block)
**Issue:** The two self-tests prove that an unknown name and an absent phrase fail. They also prove, via `FORBID doc-contract-missing`, that a phrase wrapped across lines still matches. Nothing in CI locks in:
- (a) **Whole-word matching.** A guide naming a declared prefix such as `gbb_rtc` must fail. If the `[^A-Za-z0-9_]` guards on line 48 were dropped, every prefix of a real symbol would pass, and no test would notice.
- (b) **`doc-contract-empty`.** A guide with no identifiers must fail.
- (c) **Multiple declaring files.** The `;`-joined `GBB_DECLARATIONS` list is only exercised by the positive test, which would also pass if just the header were read and the guide stopped using `GBB_ROM_PATH`.
- (d) **Comment-only and empty-phrase rejection,** once WR-01 and WR-02 are fixed.

Each of these is a vacuous-pass regression that would pass silently.
**Fix:** Add `expect_exit.cmake` cases with `GBB_EXPECT_CODE=1`, using the same pattern as the existing self-tests:
- a guide naming `` `gbb_rtc` ``, expecting `doc-contract-undeclared: gbb_rtc`;
- a guide with no identifiers, expecting `doc-contract-empty`;
- a two-file declarations case where the second file supplies the only declaration, run as a positive test with `GBB_EXPECT_CODE=0` and `GBB_EXPECT_REGEX=doc-contract pass identifiers=2`.

## Info

### IN-01: Phrases are not normalised the same way as the guide; Unicode spaces are not collapsed

**File:** `cmake/VerifyDocContract.cmake:31,57`
**Issue:** Only the guide is collapsed. A phrase containing a double space or a newline can never match (probe: `"Call  \`gbb"` gives `doc-contract-missing`). Also, `[ \t\r\n]` does not cover NBSP (U+00A0) or form feed, so an editor-inserted NBSP inside a phrase fails it (probe reproduced). Both fail closed, so neither is a vacuous pass, but each produces a confusing false failure.
**Fix:** Apply the same `string(REGEX REPLACE "[ \t\r\n]+" " " phrase "${phrase}")` to each phrase, and say in the header that the guide must use ASCII spaces.

### IN-02: Identifier extraction has no left word boundary

**File:** `cmake/VerifyDocContract.cmake:39`
**Issue:** `MATCHALL "(gbb|GBB)_..."` pulls `gbb_rtc_catch_up` out of `libgbb_rtc_catch_up` (probe: passes against the header). The token the guide actually shows the reader (`libgbb_...`) is never checked. The guide has no such token today, so this has no current effect.
**Fix:** Pad the guide and match `"[^A-Za-z0-9_](gbb|GBB)_[A-Za-z0-9_]+"`, then strip the leading character from each match. Alternatively, match `(^|[^A-Za-z0-9_])` and take `CMAKE_MATCH_*` in a loop.

### IN-03: `PASS_REGULAR_EXPRESSION` is unanchored on the phrase count

**File:** `tests/CMakeLists.txt` (`set_tests_properties(native_guide_rtc_contract ...)`)
**Issue:** `phrases=12` also matches `phrases=120`, and so on. This is harmless while the list is 12 long, but the pin is the main defence against the list-splitting and empty-element miscounts described in WR-02.
**Fix:** `PASS_REGULAR_EXPRESSION "doc-contract pass identifiers=[1-9][0-9]* phrases=12\n"`. CTest regexes see the raw output, and `message(STATUS)` ends the line with a newline.

---

_Reviewed: 2026-10-12T13:02:54Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
