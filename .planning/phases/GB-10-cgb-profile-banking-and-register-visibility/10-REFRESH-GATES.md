# Phase 10 refresh gates

**Snapshot:** `8129c5e53230e19ebc22267b7c80f37a14d6f383` (`gsd/phase-10-verification-refresh`), 2026-10-20. Runtime identity verified as `@opengsd/gsd-core` 1.18.0. A follow-up review also examined the uncommitted guard-script diff against this snapshot.

This is a current-applicability supplement. It preserves `10-VALIDATION.md`, `10-SECURITY.md`, `10-REVIEW.md`, `10-REVIEW-DISPOSITION.md`, `10-UAT.md`, and `10-VERIFICATION.md` as historical receipts; it does not rewrite their results or claim a new full-suite or hosted exact-head pass. All 20 plans remain complete; this refresh does not reexecute or advance Phase 10.

## Scope and evidence reuse

The installed evaluation-scope resolver returned `status: degraded`, `source: phase-range`, `reason: no-task-commit-rows` for Phase 10 and widened to 334 files from `d7e2e0a` across later phases. That is not a reliable phase-only current diff. I used the preserved 49-file scope in `10-REVIEW.md` as the baseline and checked current Phase 10 behavior through the focused commands below, including the post-review CGB runner, model-gate, banking, visibility, loader, fixture, documentation-contract, and baseline paths. The original 49-file review and its disposition remain intact. This supplement does not assert that all 334 resolver-returned files were re-reviewed.

The historical validation record reports four Nyquist gaps resolved and none escalated; the historical UAT records 12/12 deliverables at exact head `3c0d6bc` and hosted 541/541. These remain historical results. Current focused evidence below supports reuse of the applicable Phase 10 checks; no full CTest or current hosted UAT was rerun.

The security register has 33 closed entries (`T-10-01`–`T-10-32`, `T-10-SC`) and zero open threats at the original audit. Current applicability was checked against that ledger and the focused tests. One edge case below reopens a gap in the `T-10-21` out-of-tree build-output mitigation; the other closed dispositions are retained as recorded, not represented as a fresh execution of every threat test.

## Focused current-head checks

| Command | Result |
| --- | --- |
| `cmake --build --preset phase1` | Pass, exit 0. |
| `ctest --preset phase1 -R '^(cgb_profile_|cgb_probe_|cgb_info_|cgb_copy_frame|cgb_tables_(postboot|io)|cgb_postboot_|cgb_visibility_|cgb_key0_|cgb_stop_|banking_|cgb_banking_|cgb_mooneye_|cgb_runner_profile_|acceptance_unknown_model_refused|cgb_fuzz_|cgb_loader_|cgb_instance_|cgb_adr_half_dot_|cgb_native_guide_|cgb_bench_ab_|model_gates)' --output-on-failure --no-tests=error` | Pass, 136/136 in 13.39 s. |
| `bash tests/scripts/verify-dmg-baseline.sh` | Pass; baseline inventory, Mooneye, acceptance, and benchmark checks passed; `changes=ok rows=0`, `status=pass`. |
| `ctest --preset phase1 -R '^summary_coverage_phase10_rejected$' --output-on-failure --no-tests=error` | Pass, 1/1. This is the intentional negative control for legacy Phase 10 summary coverage syntax. |
| `python3 -I tests/scripts/verify-model-gates.py` | Pass; 186 functions, 100 gates, 34 unknown. |
| `python3 -I tests/scripts/verify-model-gates.py --self-test` | Pass; all 18 mutants detected. |
| `python3 -I tests/scripts/verify-model-gates.py --release` | Fails closed on `GATE-01`, `src/core/gabbaboy.c:547`, `UNKNOWN research:14`. This is an existing owned limitation, not a Phase 10 regression: `docs/model-gates.md` records the uncalibrated DMG/CGB-E analog high-pass-filter reference and its revisit condition, and Phase 14's disposition retains GATE-01 as a limitation. Release mode must continue to reject it until that evidence exists. |

## New finding

**Resolved warning — rejected build/evidence paths no longer create in-tree directories.** The original finding was reproduced in the pre-fix `tests/scripts/reproduce-mooneye-cgb.sh:101-103`: `--build <repo>/rejected-output` exited 2 after creating the path. The first follow-up canonicalized explicit build/evidence paths before `mkdir`, and `bash tests/scripts/test-reproduce-mooneye-cgb-guard.sh "$PWD"` passed its path-alias cases. A second review found and reproduced the remaining `TMPDIR` case: default evidence `mktemp -d` created an in-tree path before the later refusal. The final diff adds `make_temp_dir`, which canonicalizes and rejects an in-tree `TMPDIR` before `mktemp`, for both `--compare`'s temporary build directory and default evidence. The expanded guard now tests both operations and asserts no temp or build output is left; it also retains tests for explicit paths, symlink/`..` aliases, and valid missing external destinations. Follow-up verification passed: `bash tests/scripts/test-reproduce-mooneye-cgb-guard.sh "$PWD"`, `bash -n tests/scripts/reproduce-mooneye-cgb.sh tests/scripts/test-reproduce-mooneye-cgb-guard.sh`, and `git diff --check -- tests/scripts/reproduce-mooneye-cgb.sh tests/scripts/test-reproduce-mooneye-cgb-guard.sh`. This closes the observed T-10-21/Pitfall P20 output-path gap.

**Resolved verifier finding G1 — preview package scan now rejects Mooneye CGB ROMs.** The previous `PreviewPackageSmoke.cmake` scan supplied only the Mooneye MBC manifest; a renamed CGB ROM at `share/payload.bin` passed that scan. The pre-fix negative-control run failed `preview_package_smoke` because the planted ROM was accepted (log: `/tmp/gabbaboy-phase10-package-red.log`, scanner returned 0 with `mooneye-mbc absent from scanned tree files=18`). The reviewed working-tree change supplies both MBC and CGB manifests to the same extracted-preview scan, checks the clean scan, then plants `boot_regs-cgb.gb` under an innocuous name and requires the exact `mooneye-installed: share/payload.bin` rejection. It removes the planted file before proceeding to consumer checks. The focused follow-up selection passed 6/6: `v02_support_ledger`, `v02_support_ledger_controls`, `preview_package_smoke`, `libbet_install_tree`, `cgb_mooneye_not_installed`, and `cgb_mooneye_not_installed_selftest` (log: `/tmp/gabbaboy-phase10-package-green.log`). This closes the Phase 10 plan 10-15 preview-package coverage gap and strengthens current applicability of T-10-22; the existing install-tree checks remain in the selection.

## Refresh disposition

The focused Phase 10 behavior checks pass, the DMG baseline is unchanged, and the model-gate scanner plus its negative controls pass. Both the out-of-tree output-path warning and verifier finding G1 are resolved by reviewed follow-up changes and focused negative controls. Historical UAT and audit receipts are preserved. This is not a claim of full current-head review: the resolver's degraded 334-file scope means this supplement is bounded to the preserved Phase 10 review scope and focused current-head paths. The follow-up source diffs were read-only reviewed; no source, configuration, state, or historical audit record was changed by this reviewer. UI audit is not applicable to this core/runner phase.

## Final regression receipt

The reviewed fix is committed at `b56b97f` (no emulator source change). After the final script edits, the configured regression gate `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error` passed **1,144/1,144** in **369.06 seconds**, with no skipped tests. The existing `cgb_mooneye_repro_requires_manifest` entry executes the expanded guard; test registration and `tests/expected-tests.txt` remain unchanged. Full output is local at `/tmp/gabbaboy-phase10-regression.log`.

The rebuilt SDL player selection `ctest --test-dir build-player -R '^(player_session_model_|player_cgb_|player_claims_agree)' --output-on-failure --no-tests=error` passed **19/19** in **2.55 seconds**. No physical/perceptual output is claimed. Local output is `/tmp/gabbaboy-phase10-player.log`.

After the full suite, the shell guard and `git diff --check` passed again. Running the same expanded guard against the original HEAD script failed with exit 1 and `refused output created a directory`; this is the direct negative control for the repaired side effect. Independent bounded rereview of the final fix found no further issue. The release-mode GATE-01 limitation and bounded review scope above remain unchanged; neither the new local receipts nor historical hosted results establish current remote-head readiness.

Boundary triage found no open GitHub issues. PRs #78–85 remain in the existing review stack; release-please PR #75 remains unmerged. This refresh branch builds on Phase 9 refresh PR #85. Exact reviewed-head remote checks remain required before any merge.

## Final package-repair regression receipt

After the final G1 package-scan edit, the same configured regression command passed **1,144/1,144**, zero skips, in **377.12 seconds** (`/tmp/gabbaboy-phase10-final-regression.log`). This supersedes the earlier run for final-source regression coverage; the 369.06-second receipt above remains the pre-G1 snapshot. The final run executes the clean extracted-package scan and the planted renamed CGB ROM control through the shared combined-manifest command, followed by the relocated consumers. No emulator code or test inventory changed. The 19/19 focused SDL receipt remains applicable because G1 changes only the CMake package-smoke script. Both repairs received independent bounded rereview; current remote-head checks still remain a separate merge gate.
