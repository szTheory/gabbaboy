---
phase: GB-17-native-save-state-core
verified: 2026-10-28T23:00:00Z
status: passed
score: 8/8 must-haves verified
covered_files:
  - ".github/scripts/verify-workflow-policy.py"
  - ".planning/phases/GB-17-native-save-state-core/17-01-PLAN.md"
  - ".planning/phases/GB-17-native-save-state-core/17-01-SUMMARY.md"
  - ".planning/phases/GB-17-native-save-state-core/17-02-PLAN.md"
  - ".planning/phases/GB-17-native-save-state-core/17-02-SUMMARY.md"
  - ".planning/phases/GB-17-native-save-state-core/17-03-PLAN.md"
  - ".planning/phases/GB-17-native-save-state-core/17-03-SUMMARY.md"
  - ".planning/phases/GB-17-native-save-state-core/17-04-PLAN.md"
  - ".planning/phases/GB-17-native-save-state-core/17-04-SUMMARY.md"
  - ".planning/phases/GB-17-native-save-state-core/17-05-PLAN.md"
  - ".planning/phases/GB-17-native-save-state-core/17-05-SUMMARY.md"
  - ".planning/phases/GB-17-native-save-state-core/17-06-PLAN.md"
  - ".planning/phases/GB-17-native-save-state-core/17-06-SUMMARY.md"
  - ".planning/phases/GB-17-native-save-state-core/17-07-PLAN.md"
  - ".planning/phases/GB-17-native-save-state-core/17-07-SUMMARY.md"
  - ".planning/phases/GB-17-native-save-state-core/17-08-PLAN.md"
  - ".planning/phases/GB-17-native-save-state-core/17-08-SUMMARY.md"
  - ".planning/phases/GB-17-native-save-state-core/17-09-PLAN.md"
  - ".planning/phases/GB-17-native-save-state-core/17-09-SUMMARY.md"
  - ".planning/phases/GB-17-native-save-state-core/17-10-PLAN.md"
  - ".planning/phases/GB-17-native-save-state-core/17-10-SUMMARY.md"
  - ".planning/phases/GB-17-native-save-state-core/17-11-PLAN.md"
  - ".planning/phases/GB-17-native-save-state-core/17-11-SUMMARY.md"
  - "docs/state-format.md"
  - "include/gabbaboy/gabbaboy.h"
  - "src/core/gabbaboy.c"
  - "tests/CMakeLists.txt"
  - "tests/scripts/state_boundary.py"
  - "tests/scripts/verify-release-gates.py"
  - "tests/test_state_codec.c"
covered_digest: "v4:sha256:8b9d6232ada106dd42e0105293c82cdc0ce7a76a9c85d864a2efc9e274899e87"
behavior_unverified: 0
overrides_applied: 0
deferred:
  - truth: "RM-027: six release_bound timeout citations replaced with verified tree-equality evidence"
    addressed_in: "Phase 19 (entry blocker by design)"
    evidence: "REQUIREMENTS.md inherited-obligations table and ROADMAP SC8 name RM-027 as a Phase 19 entry blocker, not closed by Phase 17"
---

# Phase 17: Native Save State Core Verification Report

**Phase Goal:** Embedders can save a running instance to bytes and restore it into any instance with the same ROM and mode, continuing exactly as if never interrupted, with refused loads leaving the instance untouched and completeness, bounds and portability machine-checked.
**Verified:** 2026-10-28
**Verified head:** a9b43eb (source head e9e2d57)
**Status:** passed (local evidence); one outstanding automated item, the hosted exact-head CI run, is still pending (see below)
**Re-verification:** No, initial verification

## Goal Achievement

### Observable Truths (ROADMAP Success Criteria 1-8)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Struct-inventory checker and `nm` global check exist before the codec, reject seeded fixtures, and pass on the tree | VERIFIED | `state_inventory`, `state_inventory_controls`, `state_globals`, `state_globals_controls`, `state_precodec_gate` registered and passed in my run (270/270 of the state/consumer/perf/release subset). |
| 2 | Installed C and C++ consumers call `gbb_state_size/save_state/load_state`; size fixed per ROM+mode; mutating/allocating save rejected; typed errors appended; docs updated | VERIFIED | `include/gabbaboy/gabbaboy.h:187-190` declares the three calls and appends `GBB_STATE_NO_ROM=21` through `GBB_STATE_INVALID_CONTENT=27`. C consumer has 2 and C++ consumer 17 call sites. `installed_consumer_c/cpp`, `preview_package_smoke`, `state_size`, `state_purity` and `state_purity_controls` passed. `docs/state-format.md` documents the API and the error table. |
| 3 | Fork matrix over the admitted corpus (random and targeted in-flight points, fresh corrupted target, frame/PCM/result/battery/state-byte equality), coverage gate, and every field-drop mutant caught | VERIFIED | `state_fork_matrix` (16 shards), `state_fork_census`, `state_fork_census_controls`, `state_fork_mutants` (16 shards), `state_fork_mutant_controls` and `state_slice_invariance` all passed. |
| 4 | Every refused load leaves the instance byte-identical; closure property; state-load fuzz target in the hosted campaign | VERIFIED | `state_refusal`, `state_refusal_controls`, `state_semantic_bounds`, `state_horizon*` (closure shards 1-126+), `state_load_fuzz`, `state_fuzz_controls` passed. `tests/fuzz_core.c:1225-1405` calls `gbb_load_state` and `gbb_save_state` in the existing `fuzz_core` campaign, and `state_fuzz_controls` binds that wiring. WR-A03 closed the heap-state gap in the refusal oracle (cartridge RAM). |
| 5 | Little-endian, canonical resave, pinned digests on three OSes, RAM and RTC carried without wall clock or catch-up, battery generation behaviour, docs | VERIFIED locally; hosted exact-head confirmation pending | `state_canonical`, `state_portable_pins`, `state_pin_controls`, `state_pin_planning`, `state_rtc_palette`, `state_observers` passed locally. `docs/state-format.md:408` and `docs/cartridge-and-saves.md:280-281` state that loading replaces cartridge RAM, RTC and palette. The ci.yml native Linux, macOS and Windows jobs each run `state_portable_pins`. The cross-platform clause rests on hosted CI at the exact head, which is pending. |
| 6 | Advisory paired timing end to end; Ir and realtime floor stay blocking; ratchets reject widening and state-golden refresh without disposition (RM-026, RM-029) | VERIFIED | `perf_advisory_*`, `perf_limit_ratchet`, `perf_repeat_controls`, `perf_gate_canned_ir_over_limit`, `perf_gate_canned_realtime_under_floor` passed. WR-B03 fix (skipped advisory self-test reports as a skip) is in the round 1 range. |
| 7 | Generated disclosure; production-path lifecycle replay; version-window rule (RM-028) | VERIFIED | `release_disclosure_generator/controls`, `release_window_contract/controls`, `release_lifecycle_replay` (18 s) and `release_lifecycle_controls` (28 s) passed. |
| 8 | WR-01..05 and IN-01..04 fixed; `--review-approval` (8 mutants) and `--nightly-gate` (6 mutants) wired in CTest and production gates; boundary checks immutable; RM-027 remains a Phase 19 blocker (RM-030) | VERIFIED | `release_review_approval/controls`, `release_nightly_gate/controls`, `state_boundary_controls`, `workflow_policy_check` and `workflow_policy_controls` (47 s) passed. RM-027 is correctly left open (deferred). |

**Score:** 8/8 truths verified (0 present-but-behavior-unverified).

### Review-fix round 1 re-verification (the goal depends on these)

| Finding | Check | Result |
|---|---|---|
| CR-A01 (stale `ppu_objects_stalled` made live mid-frame state un-saveable) | `src/core/gabbaboy.c` clears `ppu_objects_stalled` in `ppu_begin_object_scan` and on the LCD-off path. I reverted exactly those two lines in a scratch worktree, built it, and ran the tests. `state_reachable_saveable_dmg` failed (5 failures) and `state_reachable_saveable_cgb` failed (10 failures). The fix is caught by an independent negative control, and the scratch worktree is removed. | VERIFIED |
| CR-A02 (CGB palette high byte with bit 7 made the machine un-saveable) | The `bg_cram`/`obj_cram` bit-7 rule is removed from `state_field_value_valid`, matching `cram_data_write` storing the whole byte. Covered by `state_reachable_saveable_cgb` and `state_semantic_bounds`, both passing. | VERIFIED |
| CR-A03 (`dma_active=1, dma_index>=160` caused an OOB write) | Two layers exist: a relation check in `state_validate_relations` (`dma_active && dma_index >= GBB_OAM_BYTES` returns invalid), and a defensive guard in `dma_advance_half_dot`. Round 1 added a `test_state_codec.c` negative control (+591 lines). `state_codec_matrix` and `state_semantic_bounds` passed. | VERIFIED |
| WR-A01/A02 (`ly` range, HDMA destination) | `ly < GBB_LINES_PER_FRAME` and active HDMA `destination >= 0x8000` are enforced in the diff. The cursor rule is widened only for reachable idle values. | VERIFIED |
| CR-B01 (three purity mutants were the same CRC-omission mutant) | In `build/tests`, the three `state_alloc_mutant_*.c` files have distinct MD5s and each differs from the core by a different single edit (a `malloc`/`free` pair, a `state_sha256` call, an `out_bytes[total_size] = 0` write). `gbb_state_alloc_mutant()` checks `ARGC==4` and that the anchor is unique. Each mutant expects its own diagnostic regex, with an unmutated control per mutant. All six `state_purity_mutant_*` tests passed. | VERIFIED |
| CR-C01 (approval could be forged from committed files) | `verify-release-gates.py` now takes `--repository` from the caller. It rejects an issue URL in another repository (`review-wrong-repository`), an OWNER comment by another login, and a comment link in another repository. The expected repository is never read from the decision file. The release gate passes `--repository "${GITHUB_REPOSITORY:-szTheory/gabbaboy}"`, and `verify-workflow-policy.py` carries mutants CR-C01-1 and CR-C01-2 that remove or redirect that binding. `release_review_approval`, `release_review_controls` and `workflow_policy_controls` passed. | VERIFIED |

### Requirements Coverage

| Requirement | Plans | Status | Evidence |
|---|---|---|---|
| STATE-01 | 01, 02, 03, 06, 11 | SATISFIED | Truth 2. |
| STATE-02 | 01, 02, 03, 04, 05, 06, 11 | SATISFIED | Truths 3 and 4 (fork matrix, census, mutants, horizon closure). |
| STATE-03 | 01, 02, 03, 04, 06, 11 | SATISFIED | Truth 4. |
| STATE-04 | 01, 05, 10, 11 | SATISFIED | Truth 1. |
| STATE-05 | 01, 02, 06, 07, 08, 11 | SATISFIED locally | Truth 5. Hosted three-OS confirmation is pending. |
| STATE-06 | 03, 05, 11 | SATISFIED | Truth 5 (`state_rtc_palette`, `state_observers`, docs). |
| RM-026, RM-029 | 07 | SATISFIED | Truth 6. |
| RM-028 | 08, 09 | SATISFIED | Truth 7. |
| RM-030 | 09, 10, 11 | SATISFIED | Truth 8. |
| RM-027 | none (Phase 19 entry blocker) | DEFERRED by design | Not claimed. |

All six STATE IDs appear in plan frontmatter and in REQUIREMENTS.md. No ORPHANED requirements.

### Key Link and Wiring Checks

- Header, core, consumers and docs are coordinated, and `gbb_state_*` are exported and used by the installed C/C++ consumers.
- `fuzz_core` (the existing hosted campaign target) calls the public state API, and `state_fuzz_controls` binds it.
- The pin test runs in the Linux, macOS and Windows native jobs of ci.yml.
- Production release gates call `--review-approval` with the repository binding and `--nightly-gate`. The workflow-policy mutant sets reject their removal.

### Behavioral Spot-Checks

Run at `a9b43eb` after `cmake --preset phase1 && cmake --build --preset phase1`:

| Behavior | Command | Result | Status |
|---|---|---|---|
| State, consumer, package, release and perf test families | `ctest -R '^(state_\|installed_consumer\|preview_package\|release_review\|release_nightly\|release_disclosure\|release_window\|release_lifecycle\|perf_)'` | 270/270 passed | PASS |
| Reachable-saveable, pins, fuzz controls, boundary, policy, coverage | 20 named tests | 20/20 passed | PASS |
| Workflow policy check | `verify-workflow-policy.py --check` | PASS | PASS |
| CR-A01 negative control (independent) | revert the fix in a scratch worktree | reachable-saveable DMG and CGB fail | PASS |

The orchestrator's full suite (1496/1496 at e9e2d57) was not re-run in full by me. I re-ran the 290 phase-relevant tests above.

### Anti-Patterns

No unreferenced TBD/FIXME/XXX markers surfaced in the phase-critical files I read. The review's remaining deferred items are info or hardening items, none an open correctness or security defect (see 17-REVIEW-DISPOSITION.md: open 0, total 26).

### Outstanding Items (automated, not human)

1. **Hosted exact-head CI for a9b43eb is still running.** At my last read, `gh pr checks 130` showed 21 pass, 17 pending and 3 skipped, with no failures. Pending jobs include native Linux, macOS and Windows, `linux-asan-ubsan-tests`, `perf-gate` and the package smoke jobs. The earlier hosted run at 6199487 was red only for reasons round 1 fixed (the Windows `workflow_policy_controls` floor and the Windows `sanitizer_timeout_policy_selftest` cost). The truth-5 clause "pinned digests match on Linux, macOS and Windows CI" and the authoritative sanitizer lane are not confirmed until this completes green. The merge gate must read the completed run, not this report.
2. **`release.yml:candidate-performance` citation.** `--verify-cited` fails because the job was renamed, and re-citing needs the next release run (recorded in 17-SECURITY.md and the 17-11 summary). It is a release precondition, not a Phase 17 goal blocker.
3. **Deferred by design:** RM-027 (Phase 19 entry blocker), WR-C03 (re-cite the provisional `nightly-asan.yml:report-red` row from a main run before any release), WR-C04 (run the budget checker from the base commit), WR-A05 (refactor `state_apply`) and the info items IN-01..08.
4. **Bookkeeping:** ROADMAP.md still shows `17-11-PLAN.md` unchecked and "0/11 complete", and REQUIREMENTS.md STATE-01..06 are unchecked and "Pending". These are for `phase.complete` to update, not a code gap. The validation sign-off lines for the final-head suite, hosted checks and `verify-uat-closure.py` remain open until the verify-work step.

### Human Verification Required

None. Per D-069 every deliverable has an automated check with a negative control.

### Gaps Summary

No goal-blocking gaps. The save/load API, transactional refusal, completeness checks, canonical bytes, battery/RTC semantics and the inherited RM-026/028/029/030 obligations are implemented, wired and machine-checked with negative controls. The five critical review findings were fixed with controls that I reproduced or inspected. Proceeding to merge depends on the pending hosted exact-head checks completing green.

---

_Verified: 2026-10-28_
_Verifier: Claude (gsd-verifier)_
