---
phase: GB-17-native-save-state-core
plan: "01"
subsystem: state-persistence
tags: [save-state, serialization, crc32, sha256, c-api, installed-package]
requires: []
provides:
  - Complete versioned machine-state API over an explicit 198-field wire ledger
  - Immutable inventory, writable-global, size, audio, format and installed-tracer checks
  - Installed C and C++ state clients and the documented wire/API contract
affects: [17-02, native-integration, state-format]
actuals:
  tokens: 50216
  tasks: 3
  commits: 12
commits: 12
plan_head_before: f530a99aab986d0f42a42fa14115981a76f8b78f
plan_head_after: e9a13af264f02ca9a0e8c4a1e75a5e568ee1ee14
tech-stack:
  added: []
  patterns:
    - Explicit little-endian descriptors drive size, encode, validation and apply walks.
    - Immutable-revision proof gates bind source inventory and executable evidence before decode acceptance.
    - Installed-package C and C++ clients exercise error precedence, no-write refusals and continuation.
key-files:
  created:
    - cmake/StateVersion.cmake
    - docs/state-format.md
    - tests/scripts/verify-state-contract.py
    - tests/test_state_api.c
  modified:
    - CMakeLists.txt
    - docs/cartridge-and-saves.md
    - include/gabbaboy/gabbaboy.h
    - src/core/gabbaboy.c
    - tests/CMakeLists.txt
    - tests/consumers/c/main.c
    - tests/consumers/cpp/main.cpp
    - tests/expected-tests.txt
key-decisions:
  - "The GBBS v1 header is 64 bytes and binds state to the exact release triplet, behavior version, profile, execution mode and complete ROM SHA-256."
  - "One typed descriptor ledger governs the complete field walk; load validates the full buffer before applying it and performs no per-call allocation or ROM hash."
  - "The host owns filesystem policy and thread serialization; core calls use stable, non-overlapping caller buffers."
requirements-completed: [STATE-01, STATE-02, STATE-03, STATE-04, STATE-05]
coverage:
  - id: D1
    description: "The installed C and C++ clients compile against all three state APIs, freeze error values 0 through 27, and exercise size, save and load behavior."
    requirement: STATE-01
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest --test-dir build -R '^(installed_consumer_(c|cpp)|preview_package_smoke)$' --output-on-failure --no-tests=error at 04e37bcc0786893f26d26ee78a71673b87546e64"
        status: pass
  - id: D2
    description: "Malformed and mismatched states return typed errors without mutating the destination or writing poisoned outputs; size and tail bounds are preserved."
    requirement: STATE-03
    human_judgment: false
    verification:
      - kind: integration
        ref: "installed_consumer_c and installed_consumer_cpp refusal/no-write controls at 04e37bcc0786893f26d26ee78a71673b87546e64"
        status: pass
      - kind: unit
        ref: "state_size_bound, state_audio_bound and state_format_contract at immutable source 04e37bcc0786893f26d26ee78a71673b87546e64"
        status: pass
  - id: D3
    description: "A running non-default DMG instance saves, resets and loads through the installed package, then matches uninterrupted future run results, PCM and canonical bytes."
    requirement: STATE-02
    human_judgment: false
    verification:
      - kind: e2e
        ref: "state_tracer --rev e9a13af264f02ca9a0e8c4a1e75a5e568ee1ee14; state_bytes=189176, prefix_audio=572, future_audio=1144"
        status: pass
  - id: D4
    description: "The qualified instance inventory and writable-global scan reject seeded missing-treatment, nested-field and global mutants."
    requirement: STATE-04
    human_judgment: false
    verification:
      - kind: integration
        ref: "state_inventory, state_inventory_controls, state_globals, state_globals_controls and state_precodec_gate at 04e37bcc0786893f26d26ee78a71673b87546e64"
        status: pass
  - id: D5
    description: "The documented GBBS header, CRC, descriptor size and caller ownership contract match the implementation; an altered magic claim is rejected."
    requirement: STATE-05
    human_judgment: false
    verification:
      - kind: unit
        ref: "state_format_contract at immutable source 04e37bcc0786893f26d26ee78a71673b87546e64; docs_control=pass, version_controls=8, CRC=CBF43926"
        status: pass
  - id: D6
    description: "Git-less source archives configure and build as unqualified while state evidence rejects absent or unresolved immutable revisions; a selected tracer regenerates its receipt before use."
    human_judgment: false
    verification:
      - kind: integration
        ref: "At immutable source 6b69a3579fd0f6e89b47ca4942954a1596e24dfb, state_revision_controls and acceptance_dense_input_controls passed; the archive core compiled with GBB_BUILD_REVISION=unknown and GBB_BUILD_QUALIFIED=0."
        status: pass
      - kind: integration
        ref: "After deleting state-precodec-proof.json, ctest --test-dir build -R '^state_tracer$' -j8 --output-on-failure --no-tests=error ran state_precodec_gate first and passed 2/2 at 6b69a3579fd0f6e89b47ca4942954a1596e24dfb."
        status: pass
  - id: D7
    description: "Every core function has an accurate model gate; the full CGB probe/load matrix still covers accepted and rejected headers, while the parity harness fits its test budget."
    human_judgment: false
    verification:
      - kind: integration
        ref: "At immutable source e9a13af264f02ca9a0e8c4a1e75a5e568ee1ee14, the model-gate suite and all real-file negative controls passed 12/12; model_gates_selftest counted 235 functions with no upper cap."
        status: pass
      - kind: integration
        ref: "At immutable source e9a13af264f02ca9a0e8c4a1e75a5e568ee1ee14, test_budget and test_budget_controls passed 2/2; state CTests use 30s normal limits, except the installed tracer at 60s."
        status: pass
      - kind: integration
        ref: "Parallel CTest selection passed 26/26 at e9a13af264f02ca9a0e8c4a1e75a5e568ee1ee14, including cgb_probe_parity in 9.46s; it asserts >100,000 entries and calls the real loader for every entry."
        status: pass
  - id: D8
    description: "Hosted native builds inspect writable storage by object section across Mach-O, GNU/LLVM ELF and COFF, accept const relocation tables, retain external/static/TLS global controls, and compile perf probes with per-revision validated release components."
    human_judgment: false
    verification:
      - kind: integration
        ref: "At immutable commit 38a86f212093033a9541f1fb0fb681c21f6986c7, state_globals_controls passed synthetic Mach-O/GNU-ELF/LLVM-ELF/COFF cases, including const relocations, TLS globals, ASan metadata and an ordinary ASan-name lookalike; the compiler-generated Mach-O ASan fixture retained real writable globals."
        status: pass
      - kind: integration
        ref: "The focused CTest selection passed 7/7 at 38a86f212093033a9541f1fb0fb681c21f6986c7; state_precodec_gate wrote a receipt bound to that commit with negative_controls=pass, and its fixture ran before state_tracer."
        status: pass
      - kind: integration
        ref: "run-perf-gate.sh --attribution-dry-run passed for immutable source 38a86f212093033a9541f1fb0fb681c21f6986c7 and historical v0.2.0 ab301aa69b1f085050fd66bf7b1378863a0821f2; each CMake project version matched its immutable CMakeLists.txt and passed cmake/StateVersion.cmake validation."
        status: pass
  - id: D9
    description: "State evidence locates Windows executables and multi-config artifacts, and the installed tracer carries sanitizer runtime link flags when its core was instrumented."
    human_judgment: false
    verification:
      - kind: integration
        ref: "At checker commit dbff3baca61aaa1b9ce4d3fee40a5486b4b2648f, Windows .exe, single/multi-config selection, ambiguity refusal, missing-artifact refusal, and sanitizer-option positive/negative controls pass; state_precodec_gate and state_tracer pass directly in an independent normal Ninja build with a receipt bound to that commit."
        status: pass
      - kind: integration
        ref: "The checker read GABBABOY_ENABLE_SANITIZERS=ON from build/17-03-followup-asan/CMakeCache.txt and returned -fsanitize=address,undefined. In the existing x86-64 Linux tool image, a client linked and ran against that actual instrumented archive (state_bytes=189176); omitting the flags failed on __ubsan_handle_shift_out_of_bounds."
        status: pass
duration: 61min
completed: 2026-10-26
status: complete
---

# Phase 17 Plan 01: Native Save State Core Summary

**A bounded, versioned native state codec now restores full machine continuation through installed C and C++ APIs.**

## Performance

- **Duration:** 61 min
- **Started:** 2026-10-26T19:50:48Z
- **Completed:** 2026-10-26T20:52:16Z
- **Tasks:** 3
- **Files modified:** 13

## Accomplishments

- Added fail-closed instance-field and writable-global inventories, executable maximum-size and audio arithmetic proofs, and a receipt binding those checks to an immutable source commit.
- Implemented the 64-byte GBBS header, CRC-32, cached ROM SHA-256 identity, typed 198-field descriptor walk and validate-before-apply state loading.
- Exercised the real installed package from C and C++ clients, verified exact future continuation, and documented the wire and caller ownership contracts.

## Task Commits

1. **Task 1: Pre-codec proof gates** - `2c29a35`, `004bd45`, `dbe7d1a`.
2. **Task 2: Versioned codec and installed tracer** - `1ce81ff`, `c2d0a7c`, `a29906d`.
3. **Task 3: Installed C/C++ clients and format docs** - `bffa064`, `04e37bc`.
4. **Post-summary regression follow-ups** - `6b69a35`, `e9a13af`.

The production codec is in `c2d0a7c797942a0decffc73c328c718dfa440a0e`. Core verification passed at immutable head `04e37bcc0786893f26d26ee78a71673b87546e64`. Follow-up CMake and test-harness fixes are in immutable heads `6b69a3579fd0f6e89b47ca4942954a1596e24dfb` and `e9a13af264f02ca9a0e8c4a1e75a5e568ee1ee14`; the latter's regenerated pre-codec receipt binds source, descriptor/range/constants and proof-input digests, and records passing negative controls.

## Files Created/Modified

- `src/core/gabbaboy.c` - ROM identity cache, state descriptors, codec, semantic checks and CRC.
- `include/gabbaboy/gabbaboy.h` - three public state APIs and appended error values 21 through 27.
- `cmake/StateVersion.cmake` and `CMakeLists.txt` - validated release components in the state header.
- `tests/test_state_api.c` - executable format, size and signed audio-domain proofs.
- `tests/scripts/verify-state-contract.py` - immutable inventory, global, format, docs and installed-tracer checks.
- `tests/CMakeLists.txt` and `tests/expected-tests.txt` - immediate CTest and inventory registration.
- `tests/test_cgb_profile.c` - exhaustive CGB probe/load parity matrix and skew-order negative control.
- `tests/consumers/c/main.c` and `tests/consumers/cpp/main.cpp` - public installed API, refusal and continuation smoke checks.
- `docs/state-format.md` - header, body, CRC, bounds and compatibility contract.
- `docs/cartridge-and-saves.md` - relationship to battery persistence and state ownership/error behavior.

## TDD Gate Compliance

- RED records `build/17-01-tdd-red.json`, `build/17-01-tdd-empty-red.json` and `build/17-01-tdd-format-red.json` each returned `RED_EVIDENCE_OK` from the installed OpenGSD checker. Their target assertions failed on the immutable baseline for the missing inventory, empty descriptor acceptance and absent state error contract.
- GREEN is supplied by the metadata/codec implementation commits, with the final format and installed tracer checks passing against immutable head `04e37bcc0786893f26d26ee78a71673b87546e64`.
- Task 3 adds installed-client qualification after the API was already implemented in Task 2; it introduced no new production behavior, so its consumer tests were expected green. No implementation was rolled back to manufacture a failure.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Test harness bug] Corrected the installed synthetic ROM entry and C++ smoke success value**

- **Found during:** Task 3
- **Issue:** The embedded program was placed at `$0150` without a jump from the CPU entry point, and the C++ smoke helper returned nonzero on success.
- **Fix:** Added `JP $0150` at `$0100` in both fixtures and made the C++ helper return the same zero-on-success convention as its caller expects.
- **Files modified:** `tests/consumers/c/main.c`, `tests/consumers/cpp/main.cpp`
- **Verification:** `installed_consumer_c` and `installed_consumer_cpp` pass.
- **Committed in:** `bffa064`.

**2. [Rule 2 - Missing critical check] Added automated coverage for the state documentation**

- **Found during:** Final acceptance review
- **Issue:** D-069 requires an automated check and negative control for each deliverable; the format and API documentation had no direct content assertion.
- **Fix:** Extended the existing immutable-revision format checker to verify required wire/API claims in both docs and reject a seeded wrong-magic claim. The check runs inside the already registered `state_format_contract` CTest.
- **Files modified:** `tests/scripts/verify-state-contract.py`
- **Verification:** `state_format_contract` reports `docs_control=pass` and passes on the final immutable revision.
- **Committed in:** `04e37bc`.

**Total deviations:** 2 auto-fixed (1 test harness bug, 1 missing documentation check).
**Impact on plan:** Both changes close direct verification gaps; production API scope is unchanged.

## Issues Encountered

- The pre-codec receipt initially named the Task 2 implementation revision. The installed tracer correctly rejected it after Task 3 advanced HEAD. Reran `state_precodec_gate` at final head `04e37bcc0786893f26d26ee78a71673b87546e64`; the receipt and tracer then passed at the same immutable revision.
- The first installed C client run found the missing entry jump, and the next C++ run exposed the helper return convention. Both harness faults were fixed in the Task 3 commit and both installed tests pass.
- The post-wave suite exposed two harness regressions: a Git-less disposable source copy was rejected during CMake configure, and `state_tracer` could run before its receipt-producing gate. Commit `6b69a35` restores unqualified archive builds while keeping state evidence revision checks fail-closed, adds explicit missing/unknown/nonexistent revision controls, and wires a CTest fixture from `state_precodec_gate` to `state_tracer`. The `phase1` configure/build passed; the parallel regression selection passed 4/4, and a clean-receipt `-R '^state_tracer$' -j8` run passed 2/2 with the gate first.
- The next full suite found untagged profile-neutral state helpers, a stale 120–199 model-gate count regex, 180-second state test limits, and a 60-second parity timeout. Commit `e9a13af` tags the 37 state functions with GATE-00 and specific neutral bases, checks the 126-function lower bound without an upper cap, gives state tests 30-second normal limits (60 seconds for the installed tracer), and compiles the same core source at `-O2` for the full parity matrix in Debug builds. The matrix still calls the real loader for every accepted and rejected entry; one selected PGB/bad-checksum case now witnesses the intentionally wrong precedence without repeating the 4.3 GiB full matrix. The isolated test passed in 11.05 seconds; the parallel targeted suite passed 26/26, with parity in 9.46 seconds.
- PR 130's hosted integration run found three portability regressions. Follow-up commit `38a86f2` adds `<cstdint>` to the public C++ consumer, replaces Mach-only `nm -m` parsing with object-and-section-aware `objdump -h -t` classification and synthetic Mach-O/ELF/COFF controls, and preserves const relocation and sanitizer metadata handling without broad writable-symbol exemptions. The perf harness now configures each archived source tree, binds `CMAKE_PROJECT_VERSION` to immutable `--rev`, validates the release triplet through `cmake/StateVersion.cmake`, and supplies those exact values to standalone compiler invocations; the historical v0.2.0 baseline and seeded source tree include the CMake files needed for that check. After committing, the phase1 build passed and the focused CTest selection passed 7/7. Current and v0.2.0 attribution dry-runs both passed. Remote CI for this correction remains for the orchestrator to run against the exact commit.
- The hosted follow-up run found that the pre-codec check omitted the Windows `.exe` suffix, the tracer's temporary installed client dropped the configured ASan/UBSan runtime link options, and receipt reporting assumed the build directory was inside the repository. Commit `dbff3ba` reads typed CMake cache entries, resolves single- and multi-configuration executable/library paths, propagates the configured sanitizer flags, and keeps receipt output safe for external build directories. The build-consumer controls, immutable pre-codec proof and installed continuation tracer passed in a separate normal Ninja build. The full CMake-driven ASan tracer could not run locally: the native macOS project configuration rejects sanitizers by policy, the available x86-64 Linux image has no CMake, and the existing Linux-tools image cannot execute under the available emulation. The actual instrumented Linux archive did link and run with the helper-derived sanitizer flags, while the no-flags control failed on an unresolved UBSan runtime symbol; fresh hosted validation remains for the orchestrator.

## User Setup Required

None - no external service configuration is required.

## Next Phase Readiness

Plan 17-01 is complete. Phase 17 remains active; planned follow-on Plan 17-02 expands identity, profile/mode, mapper and canonical field discriminators. The full corpus fork matrix and hosted cross-platform state-digest qualification remain phase-level work. No later plan or phase was executed here.

## Self-Check: PASSED

- Summary, format documentation, contract checker and proof executable exist.
- All twelve commits measured from the persisted plan ledger are ancestors of implementation head `e9a13af264f02ca9a0e8c4a1e75a5e568ee1ee14`; this includes the original summary record and both regression fixes.
- Hosted integration follow-up `38a86f212093033a9541f1fb0fb681c21f6986c7` is recorded separately from the original plan ledger, is an ancestor of current HEAD, and matches `build/state-precodec-proof.json` source_commit with negative controls passing.
- Hosted path/sanitizer integration follow-up `dbff3baca61aaa1b9ce4d3fee40a5486b4b2648f` is recorded separately from the original plan ledger and binds the normal pre-codec receipt and installed tracer evidence; the external build-directory receipt label is intentionally reduced to its filename.
- The original immutable-head verification set passed 13/13 at `04e37bcc0786893f26d26ee78a71673b87546e64`. The archive/tracer regression controls passed at `6b69a3579fd0f6e89b47ca4942954a1596e24dfb`. At `e9a13af264f02ca9a0e8c4a1e75a5e568ee1ee14`, the phase1 build passed and the combined parallel targeted selection passed 26/26, including all model-gate controls, the budget check, all state checks with fixture ordering, and the complete probe/load parity matrix.
- After the hosted correction commit, the phase1 build and focused selection passed at immutable head `38a86f212093033a9541f1fb0fb681c21f6986c7`; current and v0.2.0 perf attribution dry-runs also passed with immutable source-version validation.
- `verify-summary-coverage.py --file` passed with nine entries; all entries use automated verification.

---
*Phase: GB-17-native-save-state-core*
*Completed: 2026-10-26*
