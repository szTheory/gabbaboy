# Phase 14 — Verification Refresh Gates

**Refreshed:** 2026-10-20T23:41:40Z; **Refresh target:** `b52a4dabf244b7e37d4fc7bd22d8830927d65955`
**Result:** The eight historical review findings remain fixed in the inspected paths. Focused source, receipt, inventory, AGE, Mooneye, PCM/APU, and copy controls pass. This bounded refresh proves no new blocker in those paths; it is not a replay of the phase gates.

## Scope and runtime

`GSD_RUNTIME=codex gsd_run runtime-identity --raw` identifies the installed runtime as `@opengsd/gsd-core` **1.18.0**. The Phase 14 evaluation-scope resolver is **degraded**: `source=phase-range`, `reason=no-reachable-task-commits`, with 24 unreachable commit IDs and range base `261c660396db65712dabb5f65b3e81ee5b0a3453`. That union is not independent proof of Phase 14 ownership. The historical standard review covers 70 cumulative unique paths, but this refresh did not reread all 70. It checks the eight recorded findings and selected current cross-platform, identity, receipt, and CGB audio paths.

The installed `code-review`, Nyquist, security, and UI-review capabilities are enabled in project config. The project's `agent_skills` map is empty, the skills-only query returned no additions, and neither `.codex/skills/` nor `.agents/skills/` exists locally. Existing reports remain the canonical historical gate records; this file records the bounded applicability checks without regenerating those reports. No source file was changed.

## Historical code-review findings

`14-REVIEW-DISPOSITION.md` records **CR-01 through CR-08 fixed, zero open**. Current source still contains the safeguards, and focused controls pass:

| Finding | Current safeguard | Refresh evidence |
|---|---|---|
| CR-01 — Windows executable suffix | `build_executable_path()` applies the native executable suffix to the tracer and all seven build artifacts in `verify-cgb-corpus-report.py`. | The 13-test report contract passes native POSIX/Windows path selection, missing-native-path rejection, all-artifact suffix selection, and tracer invocation checks. |
| CR-02 — Windows pipe handling | `run_bounded()` selects a bounded threaded pipe reader on Windows, with output cap, deadline, child cleanup, and reader cleanup. | `cgb_corpus_report_platform_controls` passes the eight executable/subprocess regression methods, including overflow, timeout, and reader-error rejection. |
| CR-03 — Configured build directory | CMake passes `PROJECT_BINARY_DIR` and `CMAKE_CTEST_COMMAND` into the report and APU adapters. | Report and inventory controls pass from the nondefault `build-player` tree with its current source stamp. |
| CR-04 — Raw source bytes on Windows | `.gitattributes` pins both digest-bound APU sources to LF. | `test-cgb-apu-source-eol.py` confirms unchanged staged and checked-out bytes under `core.autocrlf=true`, and a deliberately unpinned source checks out as CRLF. |
| CR-05 — AGE Windows path identity | `age_case_name()` selects the last slash or backslash and checks the output bound. | `cgb_age_assertion_identity` passes all 13 cases / 142 rows. The registered `age_stat_mode_cgbE_phase14_controls` command also passes directly, printing `spellings=4 invalid=7 bounds=2` and detecting its intended row mutant. |
| CR-06 — Missing-ROM manifest control | `VerifyMooneyeCgb.cmake` copies the manifest byte-for-byte and compares SHA-256 before invoking the expected missing-fixture case. | `cgb_corpus_mooneye_controls` passes, preserving the intended missing-fixture rejection. |
| CR-07 — Configured CTest identity | The build-stamp target and consumers use the configured CTest executable. A changed CTest digest fails with `build-input-stamp-mismatch`. | `cgb_corpus_report_controls` passes against the real nondefault build stamp and its substituted-CTest negative control. |
| CR-08 — Sanitizer child deadline | The AGE adapter accepts only integer child deadlines from 1–45 seconds; CMake supplies 15 seconds normally and 45 with sanitizers. | `test_age_phase14_inherited_contract.py` passes 2/2 unit tests for all 13 calls, invalid timeout values, and timeout propagation. |

The current source identity check is anchored to `b52a4dabf244b7e37d4fc7bd22d8830927d65955`: both `build/cgb-corpus-build-stamp.json` and `build-player/cgb-corpus-build-stamp.json` name this revision, matching HEAD. The report contract revalidates the default build stamp and rejects a changed CTest hash. The nondefault `build-player` CTest run covers the configured-build path without sharing the parent-owned `build` test stream.

## Focused current controls

Two selections in `build-player` passed **20/20 CTests** at the current stamped source revision. The 15-test selection covered PCM channel/read-only/host-invariance behavior, PCM nibble/routing/writability mutants, APU transition/lifecycle/partition controls, SameSuite APU membership, and player limitations/claims. The five-test selection covered corpus inventory and receipt controls, Windows/report adapter controls, AGE assertion identity, and Mooneye manifest controls.

Independent negative-control suites also passed:

- `python3 -I tests/scripts/test-cgb-corpus-report.py`: **13/13** report-contract tests, including stale receipt, altered identity, incomplete/duplicate CTest membership, oversized input, and substituted CTest digest rejection.
- `verify-cgb-corpus-inventory.py --self-test`: source, membership, denominator, model/mode, expected-failure, hardware-claim, required-test, and missing-build-target mutations rejected.
- `verify-cgb-apu-dispositions.py --self-test --build-dir build`: **8** APU roster, digest, expected-result, xfail-inflation, and empty-cohort controls rejected.
- `test-cgb-apu-source-eol.py`: pinned LF and unpinned CRLF controls pass.
- `verify-age-phase14-contract.py --assertions-controls`: all named AGE identity, fixture, row, xpass, and signature mutations rejected; `--research14-controls`: **7** research-gate mutations rejected.
- `test_age_phase14_inherited_contract.py`: **2/2** timeout contract tests pass.

The inspected CGB PCM path still reports the digital DAC input before host mixing: `apu_digital_output()` derives channel values, `apu_pcm_read()` packs the two channel nibbles, and the CGB register table exposes FF76/FF77 while compatibility mode reads `$FF`. The current controls separately reject nibble swap, routing coupling, and writable-register mutants. The audio controls verify software behavior only; they do not establish analog sound quality or hardware equivalence.

## Security, Nyquist, and boundary applicability

The historical security register records **27/27 threats closed**, no accepted or transferred risks, at evidence revision `f8260549009f3150dc82de801373f40de3a02aa0`. The selected current checks exercise input bounds, source and executable identity, receipt-membership and stale-run controls, inventory pins, manifest integrity, and APU controls. This is a bounded mitigation refresh, not a new audit of all 27 threats.

The historical Nyquist map covers **31 tasks**, all 13 plans and 11 waves, with positive behavior evidence and a named negative discriminator for each task. It records no routine human-only checkpoint. The current research-disposition controls reject missing/duplicate gates, missing ownership/applicability, removed DMG-retention obligations, and unsupported gate promotion. The historical local full stream remains bound to producer `4fe97f8784ee9c8382dc014c13bc8bbff6f777c4` (1,138/1,138 CTests and its 107-case receipt); this refresh did not produce a new full corpus receipt or replay the stream.

The parent-owned boundary and shared-UAT refresh reports 13 task windows, two checker controls, four legacy nested-count warnings, ten boundary-handoff mutation controls, 17 closure controls, and 49 shared UAT rows with 19 rejected controls. Phase-local `verify-uat-contract.py` reads its recorded handoff facts through `git show` at `HANDOFF_COMMIT`; those route checks apply to that immutable historical boundary, not the live route. The earlier UAT-review warning about the machine-readable route is fixed by `projection_values()` and its route/phase-pause negative controls. Parent-owned full core regression and current corpus receipt remain outside this supplement.

## UI applicability

The installed UI safety-gate API applied to the current Phase 14 roadmap section returns `hasUI=false`, no tokens, and no matched line. The historical UI review found no UI-SPEC or changed frontend/layout files; the only applicable surface was player copy in `src/player/limitations.h`. Its stale exact-string test finding was fixed. The copywriting pillar is now 4/4; visuals, color, typography, spacing, and experience design remain N/A. Current `player_limitations` and `player_claims_agree` CTests pass. No screenshot, perceptual result, physical CGB-E result, or analog-audio claim is made.

## Evidence limits

This refresh does not claim a fresh standard review of every scoped file, a full 27-threat re-audit, a rebuilt 31-task map, a new 107-case corpus receipt, or a complete current-head regression. The historical Phase 14 closure explicitly leaves final exact-head hosted Windows/floor/sanitizer evidence unclaimed; simulated Windows controls are not native Windows execution. No physical CGB-E, analog/perceptual, IR-peer, performance, or game-compatibility qualification is added here.

The old `build-cmake-3.25.3` cache cannot be used from this checkout because it records `/work/build-cmake-3.25.3` as its binary directory. The current nondefault `build-player` stamp and focused controls pass, but that does not replace a fresh CMake-floor build. The parent owns the current full regression, corpus receipt, canonical UAT closure, and final state update.
