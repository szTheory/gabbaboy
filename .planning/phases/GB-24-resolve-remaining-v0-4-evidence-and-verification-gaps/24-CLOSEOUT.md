# Phase 24 current closeout evidence

**Updated:** 2026-11-17

**Scope:** T5 rights review and ordered-game gate, plus T6's bounded local gbmicrotest source/ROM review. This additive point-in-time record does not recreate `24-01-SUMMARY.md`, refresh historical Phase 20/21/22/23 reports, or close Phase 24 or v0.4.

## Original requirement criteria

| Requirement | Original owner | Current status | Evidence and remaining gate |
|---|---|---|---|
| GAME-01 | Phase 21 | Complete in preserved Phase 21 history; not revalidated by T5 | Existing CGB frame-observation and guest-progress implementation remains historical evidence. See [24-01-HISTORICAL.md](24-01-HISTORICAL.md). |
| GAME-02 | Phase 21 | Complete in preserved Phase 21 history; not revalidated by T5 | Existing ROM/model/mode/input/predicate receipt and negative controls remain historical evidence. T5 produced no game execution receipt. |
| FIXT-01 | Phase 21 | **Pending** | The exact primary source and sole fallback are pinned in [the closeout record](../../../tests/data/v04-closeout.json). Potion Panic assets, music and converter rights are unresolved; µCity's required `hardware.inc` grant is unresolved. No build, ROM, header or native mode was observed for either candidate. The pair cannot yet be closed as an admission or a bounded no-game absence. |
| RIGHTS-01 | Phase 20 | **Pending** | Source-specific grants and notices are recorded in [the closeout record](../../../tests/data/v04-closeout.json). No payload was staged. Unresolved game and diagnostic components do not have repository/public-CI permission established. |
| DIAG-01 | Phase 22 | **Pending** | dmg-acid2 v1.0 and cgb-acid2 v1.1 source and mgblib code notices are pinned. Footer/reference-image scope remains unresolved; excluded upstream font data has not been replaced and no derivative was created. |
| DIAG-02 | Phase 22 | **Pending** | gbmicrotest source and root MIT notice are pinned. T6 hash-reviewed one exact prebuilt ROM and a local bootless derivative, but no case was admitted, staged, or run. Compiled-output redistribution scope remains unresolved; the derivative removes the logo bytes. The source supports a DMG-CPU-B software diagnostic scope for this case only, with no hardware/CGB claim. |
| FEED-01 | Phase 21 | Complete in preserved prior evidence; not revalidated by T5 | T5 made no changes to scene-feedback behavior or its evidence. |
| REL-01 | Phase 23 | Complete in preserved prior evidence; not revalidated by T5 | The published v0.4.0 release, tags and assets were not modified. T5 does not provide a final-head or release requalification. |

The four requirements with unresolved rights or missing required bytes remain Pending under their original owners. The repository requirements file and historical verification artifacts remain unchanged.

## Named-source rights findings

The machine-readable record pins five exact upstream identities, component tree/member identities, sizes, SHA-256 digests, notice objects and scopes. The candidate checker pins the current allowlisted identities and rejects a changed source, component digest, notice digest, terms label, component set, or game order.

| Source and component | Recorded finding | Scope/status |
|---|---|---|
| Potion Panic `gbcompo25`: project code | Creator page labels code MIT; pinned source archive and root `LICENSE` are identified separately. | Supported for local build, repository and public CI as recorded. |
| Potion Panic: `Audio/GBMod_Player.asm` | Pinned driver file identifies DevEd; root MIT notice is pinned. | Supported for local build, repository and public CI as recorded. |
| Potion Panic: `hardware.inc` submodule | Exact gitlink commit and its CC0 notice are pinned. | Supported for local build, repository and public CI as recorded. |
| Potion Panic: visual assets and music | Creator page labels assets CC BY-NC-SA 4.0. Exact asset mapping and component grant scope are not established. | **Unresolved.** No candidate build or payload staging. |
| Potion Panic: map converter | The pinned tools tree includes `convertmap.py`, which attributes its WLE encoder to Pigu/AYCE; no separate grant or notice was found. | **Unresolved.** No candidate build or payload staging. |
| µCity 1.3: GPL-header source | Exact v1.3 commit/tree, GPL text and README are pinned. The README limits GPL coverage to files carrying the GPL header. | Supported for the identified GPL-header files and scopes recorded. |
| µCity 1.3: GBT Player and media | The three GBT Player files are recorded under BSD-2-Clause; the release README identifies graphics/music as CC BY-SA 4.0. Their cited notice objects are pinned. | Supported for repository and public CI as recorded. |
| µCity 1.3: required `source/engine/hardware.inc` | Exact file identity is pinned; it has no GPL header or separate license notice and credits prior hardware.inc ideas. | **Unresolved** for local build, repository and public CI. This blocks fallback build/admission. |
| dmg-acid2 v1.0 and cgb-acid2 v1.1: source and mgblib code | Exact tags, source trees, mgblib gitlink and MIT notice identities are pinned. | Supported for these identified code components and scopes recorded. |
| Acid2 footer/reference images | Both pinned image trees are inventoried; no component-specific repository/public-CI grant was established. | **Unresolved.** No derivative was created or staged. |
| Acid2 font data and derivative output | Upstream font data is explicitly excluded; project-authored replacement glyphs and masked outputs have not been created. | Excluded by design / not created. |
| gbmicrotest source | Exact commit/tree and root MIT notice are pinned. | Supported for source as recorded. |
| gbmicrotest generated ROM output | T5 recorded 513 Git-identified ROMs and unresolved output scope. T6 acquired only `div_inc_timing_a.gb` into the ignored local review area, matched its pinned Git blob, and calculated its SHA-256. The pinned MIT license grants broad rights to “Software” but does not define whether prebuilt/generated ROM output is included; README only says prebuilt ROMs are in `bin/`. | **Unresolved.** A component-specific repository/public-CI output grant is still missing. The reviewed original and derivative were not staged, admitted, or run. |
| gbmicrotest embedded logo | Pinned `tests/header.inc` contains `.nintendologo`; T5's unresolved status for original/prebuilt ROMs remains unchanged. T6's local derivative zeroes the full logo range `0x0104–0x0133`, and its byte diff confirms no other changed bytes except global checksum `0x014E–0x014F`. | No logo bytes remain in the review derivative; this does not grant redistribution rights for the remaining compiled ROM output. |

No inspected component was classified as incompatible with the intended distribution. “Unresolved” records missing component-specific scope or authority; it is not a license prohibition. Build-tool versions remain unpinned/not observed, so no build is claimed reproducible.

The creator metadata for [Potion Panic](https://deved.itch.io/potion-panic) is treated as page metadata only. Exact source URLs, refs, commits, object identities, notice hashes, evidence and blockers are in [v04-closeout.json](../../../tests/data/v04-closeout.json).

## Stage A validation and Stage B stop

Stage A is committed at `e930e3d7f8d2f8b2fc38be5cffb91985354f0ec4`. These checks passed against that immutable commit:

- Python AST parsing for both changed checkers and the focused closeout CLI argument test.
- The rights-stage checker accepted the five exact named sources and reported eight unresolved components.
- Candidate self-test controls passed, including source, rights-scope, component-digest, notice-digest, extra-source, component-set, order and requirement-status mutants.
- Diagnostic self-test controls passed, including the control that reaches the candidate rights refusal.

The admission gate refused for the intended cause. `--check-closeout --closeout-stage games --require-satisfied` reported the unresolved Potion Panic visual assets, music and converter, plus µCity `hardware.inc`. The diagnostic `--require-approved` path returned its scope-resolution refusal naming those same components. These are expected blockers, not passing game admissions.

Stage B did not modify either game-candidate attempt record: no candidate build was lawful until its applicable local-build grants are established, and no public game payload could be staged without repository/public-CI grants. T5 did not acquire or stage a game ROM or diagnostic fixture payload. T6 later acquired one pinned gbmicrotest ROM only in the ignored local review area and produced a local bootless derivative for byte inspection; neither was staged, admitted, or run. No upstream build script, unpinned toolchain, or broad suite was run.

## Task 6: bounded gbmicrotest source and ROM review

The current diagnostic record is [diagnostic-closeout.json](../../../tests/external/diagnostic-closeout.json). T5's rights input remains pinned and unchanged. The review directory `build/phase24/source-review/gbmicrotest` is ignored, bounded, contains no symlinks or tracked files, and is used only for local inspection.

The pinned `bin/div_inc_timing_a.gb` at commit `463eb6bc0fe31d61781ef63060ad6d74090c0255` is 32,768 bytes, Git blob `8ff913924540b1bbc4363744f020b38e96c94a3a`, SHA-256 `1530b5a34af78e182c8b1f5f9043f8e5ae3e9f2fac13d43f3c5714eece282706`. Its header and global checksums validate. A local bootless derivative has SHA-256 `53b0624af64524fe7cdf9b0aed3456ca60c7b30fe25cd5202b6b77855f57ffa8`. The transform zeroed only `0x0104–0x0133` and recomputed only the global checksum at `0x014E–0x014F`; 44 bytes differ, all inside those ranges. The header checksum at `0x014D` is preserved, every other byte matches the original, and the derivative global checksum is valid (`0x16F8`). The original ROM and derivative remain local review-only artifacts; no payload is staged, admitted, or executed.

The exact case source comment says `pass - dmg`, its pinned header uses `.romdmg`, and its shared macro reads DIV after clearing it and executing 60 NOPs, compares against zero, then reports actual/expected/status in `FF80–FF82`. This supports a declared **DMG-CPU-B software diagnostic scope only** for the selected test vector. The README's “DMG-CPU-08 I believe” statement is uncertain and suite-wide; it is not used to claim case-specific hardware behavior, DMG-CPU-08 applicability, or CGB applicability. The terminal macro enters a VRAM loop, so a bounded runtime adapter and its qualification are still required before any comparison.

The root MIT notice at the exact source commit grants broad rights to “the Software,” but does not define whether prebuilt or generated ROM outputs are included. The pinned README says prebuilt ROMs are in `bin/` and asks users to install WLA-DX and run `build.sh`; it provides no component-specific output license, and the tool version is not pinned. This does not prove the license excludes the ROM. It also does not establish permission to redistribute the compiled bootless ROM in the repository or public CI, so that output-scope gate remains unresolved. The original upstream `embedded-logo` rights fact remains unresolved in the unchanged T5 record; the selected derivative contains no logo bytes.

The current record still accounts for all 513 names: one blocked candidate with an observed original-ROM SHA-256 and derivative digest, zero eligible and executed cases, and 512 exclusions. The output-scope grant is the blocker; runtime adapter/build qualification and bounded execution have not been attempted. DIAG-02 remains Pending under Phase 22 ownership. Acid2 remains independently blocked on footer/reference-image rights.

| Gate | Current result | Consequence |
|---|---|---|
| Potion Panic primary rights | Visual assets, music assets and converter code unresolved | Stop before local build, execution and admission; source/build/ROM/header/native-mode facts remain `not_observed`. |
| µCity 1.3 sole fallback rights | Required `hardware.inc` scope unresolved | Keep fallback blocked; its build cannot establish the original criterion. |
| Acid2 derivatives | Footer/reference-image rights unresolved; font replacement/output absent | Keep DIAG-01 Pending; no build or derivative staging. |
| gbmicrotest | One original ROM and derivative were inspected locally; compiled-output redistribution scope remains unresolved, logo bytes were removed, and no runtime evidence exists | Keep DIAG-02 Pending; no fixture admission, staging, or execution. |
| Original requirement ownership | FIXT-01 Phase 21; RIGHTS-01 Phase 20; DIAG-01/02 Phase 22 | Keep each Pending; no milestone closure. |

The next useful action is to obtain authoritative, component-specific scope/notice evidence for Potion Panic visual assets, music and converter code, µCity's required hardware include, and redistribution of gbmicrotest's compiled ROM output. Once the relevant grants are established, the affected stages can proceed within their existing limits; the ordered-game fallback remains sequenced after a committed primary disposition. Acid2 reference/footer rights remain a separate gate.
