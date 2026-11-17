# Phase 24 current closeout evidence

**Updated:** 2026-11-17

**Scope:** T5 rights review and ordered-game gate, plus T6's bounded local gbmicrotest source/ROM review. This additive point-in-time record does not recreate `24-01-SUMMARY.md`, refresh historical Phase 20/21/22/23 reports, or close Phase 24 or v0.4.

## Original requirement criteria

| Requirement | Original owner | Current status | Evidence and remaining gate |
|---|---|---|---|
| GAME-01 | Phase 21 | Complete in preserved Phase 21 history; not revalidated by T5 | Existing CGB frame-observation and guest-progress implementation remains historical evidence. See [24-01-HISTORICAL.md](24-01-HISTORICAL.md). |
| GAME-02 | Phase 21 | Complete in preserved Phase 21 history; not revalidated by T5 | Existing ROM/model/mode/input/predicate receipt and negative controls remain historical evidence. T5 produced no game execution receipt. |
| FIXT-01 | Phase 21 | **Pending** | The exact primary source and sole fallback are pinned in [the closeout record](../../../tests/data/v04-closeout.json). Potion Panic assets, music and converter rights are unresolved; µCity's required `hardware.inc` grant is unresolved. No build, ROM, header or native mode was observed for either candidate. The pair cannot yet be closed as an admission or a bounded no-game absence. |
| RIGHTS-01 | Phase 20 | **Pending** | Source-specific grants and notices are recorded in [the closeout record](../../../tests/data/v04-closeout.json). No game payload was staged; only the selected gbmicrotest derivative was admitted with its complete pinned notice. Other game and diagnostic components remain unresolved for repository/public-CI use. |
| DIAG-01 | Phase 22 | **Pending** | dmg-acid2 v1.0 and cgb-acid2 v1.1 source and mgblib code notices are pinned. Footer/reference-image scope remains unresolved; excluded upstream font data has not been replaced and no derivative was created. |
| DIAG-02 | Phase 22 | **Pending** | T6 bound upstream issue #1/comment 2080090499 and commit 463eb6b (“Create LICENSE,” only root `LICENSE` changed) to the selected prebuilt ROM and its bootless derivative, admitting only `div_inc_timing_a` with the full MIT notice. The case passed its one bounded DMG-CPU-B software run (`actual=00`, `expected=00`, terminal `01`); 512 names remain excluded. T5's source-wide prebuilt-ROM and Nintendo-logo outcomes remain unresolved. The derivative contains no logo bytes. No hardware, DMG-CPU-08, or CGB claim is made. |
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
| gbmicrotest generated ROM output | T5 recorded 513 Git-identified ROMs and unresolved source-wide output scope. Upstream issue #1 asks “Under what license are these provided?”; author `aappleby` replies “License added.” The pinned source commit is titled “Create LICENSE” and changes only root `LICENSE`. T6 uses these exact facts for one selected prebuilt ROM and its source-bound bootless derivative, with the full MIT notice. | **Supported for the one selected case under a bounded interpretation.** The selected case passed its bounded runtime. Other 512 ROMs remain outside scope; original ROM and logo bytes are excluded from the bundle. |
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

Stage B did not modify either game-candidate attempt record: no candidate build was lawful until its applicable local-build grants are established, and no public game payload could be staged without repository/public-CI grants. T5 did not acquire or stage a game ROM or diagnostic fixture payload. T6 later acquired one pinned gbmicrotest ROM only in the ignored local review area and produced a local bootless derivative for byte inspection. Based on the exact issue and license-adding commit evidence, the derivative-only bundle is admitted for one source-selected diagnostic with the full notice; the original ROM and logo bytes are excluded. No game payload runtime, upstream build script, unpinned toolchain, or broad suite was run.

## Task 6: bounded gbmicrotest source and ROM review

The current diagnostic record is [diagnostic-closeout.json](../../../tests/external/diagnostic-closeout.json). T5's rights input remains pinned and unchanged. The review directory `build/phase24/source-review/gbmicrotest` is ignored, bounded, contains no symlinks or tracked files, and is used only for local inspection.

The pinned `bin/div_inc_timing_a.gb` at commit `463eb6bc0fe31d61781ef63060ad6d74090c0255` is 32,768 bytes, Git blob `8ff913924540b1bbc4363744f020b38e96c94a3a`, SHA-256 `1530b5a34af78e182c8b1f5f9043f8e5ae3e9f2fac13d43f3c5714eece282706`. Its header and global checksums validate. A bootless derivative has SHA-256 `53b0624af64524fe7cdf9b0aed3456ca60c7b30fe25cd5202b6b77855f57ffa8`. The transform zeroed only `0x0104–0x0133` and recomputed only the global checksum at `0x014E–0x014F`; 44 bytes differ, all inside those ranges. The header checksum at `0x014D` is preserved, every other byte matches the original, and the derivative global checksum is valid (`0x16F8`). The original remains in ignored local review; only the derivative is in the admitted bundle.

The exact case source comment says `pass - dmg`, its pinned header uses `.romdmg`, and its shared macro reads DIV after clearing it and executing 60 NOPs, compares against zero, then reports actual/expected/status in `FF80–FF82`. This supports a declared **DMG-CPU-B software diagnostic scope only** for the selected test vector. The README's “DMG-CPU-08 I believe” statement is uncertain and suite-wide; it is not used to claim case-specific hardware behavior, DMG-CPU-08 applicability, or CGB applicability. The terminal macro enters a VRAM loop; the qualified adapter stopped on its source-defined terminal marker under bounded guest work.

Upstream issue [#1](https://github.com/aappleby/gbmicrotest/issues/1#issuecomment-2080090499) asks “Under what license are these provided?” and author `aappleby` replies “License added.” The pinned commit `463eb6b` is titled “Create LICENSE” and changes only root `LICENSE`. Together with the README's prebuilt-ROM inventory and the included full MIT notice, this supports a bounded output scope for the selected prebuilt ROM and its bootless derivative. This scope does not generalize to the other 512 ROMs or other sources. The original upstream `embedded-logo` rights fact remains unresolved in the unchanged T5 record; the admitted derivative contains no logo bytes. The pinned README also instructs users to install WLA-DX and run `build.sh` without pinning the tool version; no reproducible-build claim is made.

The current record accounts for all 513 names: one eligible and executed case with an observed original-ROM SHA-256 and derivative digest, and 512 exclusions. The adapter's synthetic positive/negative controls pass. A fresh runner qualification was generated and validated for source commit `7acfc7828393ad41a429a80af81dd9c612105781`; the one authorized runtime passed with `actual=00`, `expected=00`, terminal `01`, 72 instructions, 77 events, and 736 half-dots. The current machine record binds the receipt to the source commit, fixture admission, runner, qualification, and evidence-file digest. DIAG-02 remains Pending under Phase 22 ownership. Acid2 remains independently blocked on footer/reference-image rights.

| Gate | Current result | Consequence |
|---|---|---|
| Potion Panic primary rights | Visual assets, music assets and converter code unresolved | Stop before local build, execution and admission; source/build/ROM/header/native-mode facts remain `not_observed`. |
| µCity 1.3 sole fallback rights | Required `hardware.inc` scope unresolved | Keep fallback blocked; its build cannot establish the original criterion. |
| Acid2 derivatives | Footer/reference-image rights unresolved; font replacement/output absent | Keep DIAG-01 Pending; no build or derivative staging. |
| gbmicrotest | One selected case is admitted under a bounded source-backed MIT interpretation; it passed once, and 512 names remain excluded. Original/logo bytes remain excluded. | One-case runtime accounting is complete; keep DIAG-02 Pending until the original criterion is evidenced. |
| Original requirement ownership | FIXT-01 Phase 21; RIGHTS-01 Phase 20; DIAG-01/02 Phase 22 | Keep each Pending; no milestone closure. |

The one-case gbmicrotest lane is complete. The combined gate still cannot close because Acid2 footer/reference-image rights remain unresolved, and game-source rights remain unresolved. T6 stops before T7 with the overall closeout incomplete; resolve the Acid2 component scope before attempting the combined diagnostic gate.

## Owner-directed best-faith rights dispositions (D-207)

The preceding sections record the T5/T6 evidence state before the owner's D-207 direction. No external messages will be sent. This additive decision supersedes only the listed rights findings; it does not accept gaps or complete any original requirement.

For the exact creator-linked Potion Panic source, the creator page's CC BY-NC-SA 4.0 asset category covers the pinned `GFX`, `Levels`, `Tilesets`, and `Audio/Modules` components under the owner's bounded best-faith interpretation. The repository retains the CC deed/link and attribution in `fixtures/v04-games/LICENSE.txt`. Use remains noncommercial, identifies changes, preserves attribution, and treats adaptations as share-alike. The separately attributed Pigu/AYCE WLE converter is excluded. µCity's pinned `source/engine/hardware.inc` remains excluded because no grant was found and the available CC0 source is not byte-identical.

For dmg-acid2 v1.0 and cgb-acid2 v1.1, the owner accepts each exact pinned repository root MIT grant as covering only that repository's pinned `img/` tree. This is a repository-level inference, not an image-specific upstream statement. Retain both full MIT notices and the README credit to Håkon Wium Lie and Ian Hickson. `mgblib` font data remains excluded.

These dispositions clear the prior rights-only stop for Acid2 composition and Potion Panic asset/music inspection. They do not establish a creator-ROM sidecar, ROM bytes/digest/header, source/build relationship, native mode, or guest progress. They also do not create Acid2 replacement glyphs, source-anchored text masks, reproducible outputs, admissions, or independent comparisons. The gbmicrotest scope remains one admitted/executed case; 512 ROMs and embedded-logo source scope remain unresolved. FIXT-01, RIGHTS-01, DIAG-01, and DIAG-02 remain Pending until their original criteria are actually evidenced. T7, final CI, PR, merge, main handoff, and milestone completion remain unstarted.
