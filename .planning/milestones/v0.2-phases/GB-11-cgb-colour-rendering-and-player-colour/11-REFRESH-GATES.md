# Phase 11 refresh gates

**Snapshot:** `e444dd2320acf0e4e0d83fb89009311edcaa5e13`, 2026-10-20. Installed runtime: `@opengsd/gsd-core` 1.18.0 (identity established by the orchestrator).

This supplement assesses current applicability of the completed Phase 11 gates. It preserves the original REVIEW, REVIEW-DISPOSITION, SECURITY and VALIDATION receipts. It does not claim a full review of later-phase source, a new hosted exact-head pass, physical hardware qualification or perceptual display qualification. All 15 implementation plans were already complete.

## Scope and review disposition

The installed `check evaluation-scope --phase 11 --raw` returns `status: degraded`, `source: phase-range`, `reason: no-task-commit-rows`: 306 files and 135 commits, including subsequent phases and verification refreshes. That is not a trustworthy Phase 11-only diff. The preserved 46-file `11-REVIEW.md` scope remains the historical review baseline. This refresh reads the current colour-specific paths within that scope; it does not represent all 306 resolver files, or even every unchanged line of all 46 historical files, as newly reviewed.

Current direct inspection covers the core CRAM lock/index operations, bank-explicit tile/map/OBJ fetches, priority composition, RGB555 frame-copy arithmetic and compat palette APIs; acceptance RGB555 validation/digests and runner format selection; player colour conversion, model tokens and status precedence; acid2 input pin/read/decode/run boundaries; colour reproducer manifest/tool invocation guards; and the relevant current CMake registrations and test assertions. Primary paths are `src/core/gabbaboy.c`, `src/accept/digest.c`, `src/accept/gbb_accept.h`, `src/runner/acceptance.c`, `src/player/colour.[ch]`, `src/player/main.c`, `tests/player/test_colour.c`, `tests/scripts/run-acid2-local.py`, `tests/scripts/reproduce-cgb-colour.sh` and `tests/CMakeLists.txt`.

No new BLOCKER or WARNING source defect was proven in this bounded inspection. The historical review's seven fixes and one no-change disposition remain supported:

- WR-01: both MagenTests LCD-off baseline variants and the mode-0-removal mutant/control pairs pass their current expected verdicts. The compat mutant is required to exit 1 with the specific `magentests_cgb_ppu_disabled_state_compat: pixel 0,0 expected` diagnostic; it cannot merely succeed through an unrelated exit.
- WR-02/03: acid2 reads and hashes the bytes it subsequently uses, and malformed-manifest errors remain distinct from mismatch; reproduction rejects missing pins and reports tool errors distinctly. Current refusal, malformed-manifest, missing-pin and tool-failure controls pass.
- IN-01/02/03: current code retains player status precedence, unknown capture-format refusal and RGB555 scratch-size assertion, plus misalignment and NULL binary-output/path guards. RGB555 vector/API checks pass.
- IN-04/05: current registered controls retain specific Magen diagnostics, and the unknown benchmark profile uses the rejected-profile case. The associated focused controls pass. This does not assert a new exhaustive audit of every historical mutant diagnostic.

## Focused fresh checks

These use the existing configured Debug build; the orchestrator owns rebuild and full regression evidence.

| Command | Result |
| --- | --- |
| `ctest --preset phase1 -R '^(acceptance_digest_rgb555_vectors|cgb_priority_truth_(regen|selftest|regen_mutated)|cgb_rgb555_|palette_compat_api_|palette_compat_mutant_mask_bit15|cgb_external_dispositions|cgb_acid2_local_|cgb_colour_repro_|model_gates_no_phase11)' --output-on-failure --no-tests=error` | Pass, 29/29, 1.24 seconds, zero skips. |
| `ctest --preset phase1 -R '^(magentests_cgb_(ppu_disabled_state|mutant_lcd_off_no_mode0)|cgb_measure_core_unknown_profile)' --output-on-failure --no-tests=error` | Pass, 7/7, 0.49 seconds, zero skips. |

Negative controls in these runs include altered truth-table regeneration, skewed RGB555 argument validation, mask-on-reject palette mutation, altered external dispositions, unpinned acid2 input, malformed acid2 manifest, failed RGBDS tools, missing reproduction pins, reintroduced Phase 11 research rows and removed LCD-off mode-0 transition. Positive companion cases remain green. These bounded tests support the cited dispositions; a green regression suite alone is not a proof of correctness.

## Security and validation applicability

The historical security register contains 43 distinct closed threats and zero open threats at its original audit. Current inspected mitigations retain masked 64-byte CRAM indices; bounded map/tile/palette lookup; full palette validation before stores; frame destination size/stride/overflow/overlap validation before writes; fixed-size player conversion buffers; pinned input bytes; bounded PNG decode; a runner subprocess timeout; constrained reproduction argv; and error-specific harness outcomes. No newly contradicted mitigation was identified in this focused review. This is applicability reuse, not a fresh 43-threat execution or a new whole-project security certification.

The validated Nyquist record has 25 behaviour rows and no escalated gaps. Its colour, API, fixture, digest, documentation and player checks remain registered. Historical UAT reports 91 SUMMARY coverage entries grouped into 11 completed automated deliverables. The orchestrator identified a current shared closure-checker incompatibility with those old grouped headings; the canonical tool has now migrated the closure to 91 individual automated rows while preserving the original local/hosted receipt prose. `verify-uat-closure.py --self-test` passes all 91 rows and rejects 19 weakened controls. This resolves the closure-format gap without claiming implementation replay or a new hosted run.

Phase boundary facts are point-in-time facts. `git show 4811033:.planning/STATE.md` records the Phase 11 execute-phase handoff to `/gsd-verify-work 11`, with Phase 12 named as the following unstarted phase; the same commit's config has both automatic advance flags false, and its tree contains no Phase 12 directory. Later phases now exist, so no live-HEAD absence or routing assertion is substituted for that boundary evidence. The original security audit's T-11-42 wording is historical and does not establish today's route.

The existing model-gate limitations remain explicit: CRAM lock-edge offsets, mode-3 raster timing and analog display/filter behaviour are not upgraded by colour composition tests or this refresh. No new physical CGB-E or acid2 rights-qualified run is claimed.

## Native player UI evidence

The Phase 11 player is SDL native. There is no historical Phase 11 UI-REVIEW artifact or browser UI to audit; the historical execute-phase tail explicitly skipped the web six-pillar audit. Do not manufacture screenshots, browser/DOM checks or numerical visual scores. The applicable automated evidence is the native model-selection seam, exhaustive 32,768-value RGB555 conversion with tight/padded rows, channel-swap control, model-title tokens, claims agreement and real player colour smoke with forced-wrong-path controls. The orchestrator's rebuilt full player suite passed 98/98 in 21.72 seconds with zero skips, superseding its focused 19/19 selection (3.04 seconds). This establishes automated behaviour within those contracts, not monitor colour accuracy or a new perceptual/hardware claim.

## Ownership and remaining closure

This reviewer changes only this supplement; source, configuration, state and historical audits remain untouched. Full current-source regression, canonical UAT migration, requirement traceability, final handoff and exact-head remote readiness belong to the orchestrator. No phase advance, merge or new risk acceptance is authorized by this supplement itself.

## Final local regression and closure receipts

After the unchanged source was configured and rebuilt, the configured full regression passed **1,144/1,144**, zero skips, in **486.68 seconds**. The source snapshot remains `e444dd2320acf0e4e0d83fb89009311edcaa5e13`; all refresh changes are planning records. The rebuilt full SDL player suite passed **98/98**, zero skips, in **21.72 seconds**. Local logs are `/tmp/gabbaboy-phase11-regression.log` and `/tmp/gabbaboy-phase11-player-all.log`.

The shared canonical closure tool wrote **91 automated deliverables**, zero human checkpoints, and its self-test rejected **19 controls**. Original evidence prose remains in `11-UAT.md`, with its historical revisions and limits. The pre-migration grouped UAT failed the same shared checker with `unparsed or misnumbered test heading`; that observed negative establishes the format gap rather than an emulator defect. These receipts supersede the pending full-regression and migration items above. Requirement traceability and final goal verification remain the verifier/orchestrator responsibilities; remote exact-head checks remain a separate merge gate.
