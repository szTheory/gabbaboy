---
phase: GB-10-cgb-profile-banking-and-register-visibility
reviewed: 2026-10-12T00:00:00Z
depth: standard
files_reviewed: 49
files_reviewed_list:
  - .gitattributes
  - .github/scripts/verify-test-inventory.sh
  - .github/workflows/fixture-repro.yml
  - .gitignore
  - cmake/ExpectedTests.cmake
  - cmake/VerifyMooneyeCgb.cmake
  - docs/cgb-profile.md
  - docs/model-gates.md
  - docs/native-integration.md
  - docs/support/unreleased.md
  - fixtures/cgb-banking/LICENSE.txt
  - fixtures/cgb-banking/banking.asm
  - fixtures/cgb-banking/manifest.json
  - fixtures/mooneye-cgb/ELIGIBILITY.md
  - fixtures/mooneye-cgb/FONT-LICENSE.txt
  - fixtures/mooneye-cgb/LICENSE.txt
  - fixtures/mooneye-cgb/SOURCES.md
  - fixtures/mooneye-cgb/manifest.json
  - include/gabbaboy/gabbaboy.h
  - src/core/gabbaboy.c
  - src/runner/acceptance.c
  - src/runner/acceptance.h
  - src/runner/main.c
  - tests/CMakeLists.txt
  - tests/acceptance/CMakeLists.txt
  - tests/consumers/c/main.c
  - tests/consumers/cpp/main.cpp
  - tests/expected-tests.txt
  - tests/fuzz_core.c
  - tests/runner_profile_identity.cmake
  - tests/scripts/measure-release-baseline.sh
  - tests/scripts/reproduce-cgb-banking.sh
  - tests/scripts/reproduce-mooneye-cgb.sh
  - tests/scripts/verify-model-gates.py
  - tests/test_banking.c
  - tests/test_banking_internal.c
  - tests/test_cgb_postboot.c
  - tests/test_cgb_postboot_internal.c
  - tests/test_cgb_profile.c
  - tests/test_cgb_tables.c
  - tests/test_cgb_visibility.c
  - tests/test_fuzz_core.c
  - tests/test_instance_concurrency.c
  - tests/test_loader_fuzz.c
  - tests/test_loader_matrix.c
  - tests/test_mooneye_cgb_div_sweep.c
  - tests/test_rtc3test.c
  - tests/test_runner.c
  - tests/verify_runner_help.cmake
findings:
  critical: 0
  warning: 4
  info: 5
  total: 9
status: issues_found
---

# Phase 10: Code Review Report

**Reviewed:** 2026-10-12
**Depth:** standard
**Files Reviewed:** 49
**Status:** issues_found

## Summary

The main hotspot, `src/core/gabbaboy.c` (diff against `d7e2e0a`), was read in full, as were the public header diff and the `src/runner/` diffs. I also read the two reproduce scripts, the A/B baseline mode, the workflow diff, and the white-box and fuzz tests. I spot-checked `test_cgb_tables.c` and `test_cgb_visibility.c` for vacuous passes. I did not audit the other test sources (`test_cgb_profile.c`, `test_cgb_postboot.c`, `test_banking.c`, the loader tests) or the fixture and doc files line by line.

No bank-index out-of-bounds, ABI/`struct_size` handling bug, or partial-mutation-on-failure bug was found.

- **Bank indices.** `wram_byte` masks the offset to 13 bits and selects bank 0 or `wram_bank`. `wram_bank` is only written from `svbk & 7` mapped to 1..7, or pinned by the post-boot table. `vram_bank` is `value & 1`. The fuzz harness asserts these bounds after every step.
- **Struct size handshake.** `gbb_probe_rom` and `gbb_get_info` check the `struct_size` floor, write field by field, and leave outputs untouched on error.
- **Load failure.** `gbb_load_rom` commits `exec_mode` and the header facts only after both allocations succeed.
- **Read pre-flight vs. read8.** The CGB `read_supported_map` agrees with the old DMG chain for every EXISTING row in FF00-FF4B, so there is no pre-flight/read8 mismatch.
- **Tests.** The tests that I sampled have negative controls. The visibility sweep checks completeness, so truncation at `MAX_CELLS` would be caught.

The remaining findings are runner honesty and robustness issues, shell-script and verification weaknesses, and stale comments.

## Warnings

### WR-01: Runner silently falls back to the DMG profile for an unrecognised model but still prints the unknown label

**File:** `src/runner/acceptance.c:26-30` (`run_profile`) and `:23-25` (`run_model`)
**Issue:** `run_profile()` maps an unknown `options->model` to `GBB_RUNNER_PROFILE_DMG`, while `run_model()` returns the raw unknown string for every printed `model=` field.

- A caller that reaches `gbb_acceptance_run_case` with a model that did not pass `gbb_case_model_known` would execute on DMG and report `model=<whatever>`.
- That contradicts the stated D-25 intent ("a CGB run can never carry a DMG label" and "never falls back").
- `main.c` validates the model first, so today this is only reachable by a direct library caller or a future refactor. It is still a latent evidence-mislabelling path.

**Fix:** Make an unknown model a hard error instead of a fallback:
```c
static int run_profile(const gbb_acceptance_options *o, gbb_profile *out) {
    return gbb_runner_profile_for_model(run_model(o), out);
}
/* callers: if (!run_profile(options, &profile)) { print status=unsupported reason=unknown-model; return EXIT_UNSUPPORTED; } */
```

### WR-02: `suite categories` line counts expected-unsupported rows as passes

**File:** `src/runner/main.c` (suite loop, about line 506 in the post-change file: `if(code==0)category_pass[k]++`)
**Issue:**
- `run_one` returns 0 for a row that met its declared unsupported-bus stop (`expected-unsupported`).
- The loop increments `category_pass` for it. A receipt such as `suite categories post-boot-hwio=1/1 unused-hwio=1/1` therefore reads as a plain pass.
- In fact those two ROMs never reached their `ld b,b` verdict. They stopped at FF76, and their remaining assertions did not run.
- The separate `suite expected-unsupported=2/2` line mitigates this. The categories line is the one a script or reader is most likely to take as the score.

**Fix:** Count expected-unsupported rows separately. For example, have `run_one` expose `final_status`, and increment `category_pass` only when `final_status` is `"pass"`. Print `expected-unsupported` as its own per-category figure, or change the CGB categories line format.

### WR-03: `reproduce-mooneye-cgb.sh --compare` can pass without verifying `original_sha256`, and leaks temp dirs on failure

**File:** `tests/scripts/reproduce-mooneye-cgb.sh:176-181` (the `if [[ -f "$manifest_file" ]]` guard) and `:111-114` (`mktemp -d` with no trap)
**Issue:**
- If `fixtures/mooneye-cgb/manifest.json` is missing, the original-ROM digest check is skipped and the script can still print `result=byte-identical`.
- The committed-ROM-count check does not cover this case. The manifest is the trust anchor for the `original_sha256` binding, so skipping silently makes the comparison weaker than it claims.
- Separately, `build_dir` and (when `GBB_REPRO_OUTPUT_DIR` is unset) `work_dir` are only removed or kept on the success path. Any `set -e` abort between creation and the final `rm -rf` leaks the temp tree.

**Fix:** Treat a missing manifest as a failure in `--compare`:
```bash
[[ -f "$manifest_file" ]] || { echo "missing fixture manifest: $manifest_file" >&2; failed=1; }
```
Also register `trap 'rm -rf -- "$build_dir"' EXIT` in compare mode right after `build_dir` is created.

### WR-04: Test-seam function is declared by hand in the runner and exported from the shipped library

**File:** `src/runner/main.c:236` (prototype) and `src/core/gabbaboy.c:3606-3608` (`gbb_test_last_unsupported_address`, non-static)
**Issue:**
- The runner declares `uint16_t gbb_test_last_unsupported_address(const gbb_instance *)` locally instead of via a shared internal header. A signature change in the core would compile and link-fail or misbehave silently, depending on the toolchain.
- The symbol is an exported global of the core library. That follows the existing `gbb_test_*` pattern, so it is not new, but the runner now depends on it for D-26 evidence.
- The "address" is also overwritten by every failed read pre-flight and every deferred write. A single instruction can issue two deferred writes (for example `PUSH` or `CALL` with SP near FF76/FF77) and the report names only the last one. Expected-unsupported rows only compare against one address.

**Fix:** Put the test-seam prototypes in an internal header (for example `src/core/gabbaboy_test.h`) included by both the core and the runner/tests. For the multi-write case, either document "last refused address" or latch the first refused address.

## Info

### IN-01: Stale comments contradict the shipped state

**File:** `src/runner/acceptance.h:94-97`, `src/core/gabbaboy.c:1611,2004`, `tests/scripts/reproduce-mooneye-cgb.sh:4`
**Issue:**
- `acceptance.h` still says `GBB_PROFILE_CGB_CPU_E` "does not exist in the public header until Plan 10-05" and that "the core's gbb_create still rejects it". Both statements are now false.
- `GATE-23` and `GATE-38` say "CGB WRAM banking is added by a later plan", but `wram_byte` already implements it.
- `reproduce-mooneye-cgb.sh` says "Adapted from reproduce-mooneye-cgb.sh", a self-reference that presumably should name `reproduce-mooneye-mbc.sh`.

**Fix:** Update or remove these comments. The gate-comment text is also mirrored in `docs/model-gates.md`, so change both together to keep `verify-model-gates.py` green.

### IN-02: Redundant `test -s` in the new CI step

**File:** `.github/workflows/fixture-repro.yml:142-146`
**Issue:** The new "Reproduce CGB banking fixture bytes" step begins with `test -s tests/expected-tests.txt`. That is copy-pasted from the neighbouring steps and has no relation to the banking reproduction.
**Fix:** Remove it from the new step, or leave it and note why it is there.

### IN-03: A/B mode accepts overrides and can crash with a raw traceback

**File:** `tests/scripts/measure-release-baseline.sh` (PYAB block: `run_once`, env overrides)
**Issue:**
- `run_once` does `int(fields["elapsed_ns"])`. If the binary prints a `mode=` line with a matching workload and digest but no `elapsed_ns`, the script dies with a `KeyError` traceback instead of a controlled `ab-...` error token.
- Production code reads `GBB_AB_EXPECT_DIGEST` and `GBB_AB_DROP_FIELD` from the environment. These are test hooks, and a stray exported `GBB_AB_EXPECT_DIGEST` weakens the digest guard.
- `root` is unpacked but unused.

**Fix:** Validate `elapsed_ns` presence and numeric form and `SystemExit("ab-field-missing: ...")` otherwise. Consider restricting the hook variables to a `--self-test` path.

### IN-04: Acceptance output reads "pass" semantics for staged-not-run evidence only through a secondary line

**File:** `src/runner/main.c` (the `suite eligible=... status=pass` line)
**Issue:** With two of four CGB rows only meeting a declared stop, `status=pass` appears together with `executed=4`. The `expected-unsupported=2/2` line is present and asserted by CTest, so this is by design.
**Fix:** No change required. Consider printing `status=pass-with-expected-unsupported` when the tally is non-zero, so the headline cannot be mistaken for a full pass.

### IN-05: Upstream maintainer e-mail in a committed license file

**File:** `fixtures/mooneye-cgb/LICENSE.txt:1`
**Issue:** The file carries the upstream author's e-mail inside the required MIT copyright line. AGENTS.md says to avoid emails in public artifacts. This is the upstream copyright notice, which the license requires to be preserved, so it is probably acceptable.
**Fix:** None needed if this matches the sibling `fixtures/mooneye/LICENSE.txt`. Otherwise confirm the project's policy covers third-party notices.

---

_Reviewed: 2026-10-12_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
