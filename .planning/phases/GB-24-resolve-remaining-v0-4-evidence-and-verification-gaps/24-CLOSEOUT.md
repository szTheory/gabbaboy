# Phase 24 current closeout evidence

**Updated:** 2026-11-17

**Scope:** T5 rights review and ordered-game gate only. This is an additive point-in-time record. It does not recreate `24-01-SUMMARY.md`, refresh historical Phase 20/21/22/23 reports, or close Phase 24 or v0.4.

## Original requirement criteria

| Requirement | Original owner | Current status | Evidence and remaining gate |
|---|---|---|---|
| GAME-01 | Phase 21 | Complete in preserved Phase 21 history; not revalidated by T5 | Existing CGB frame-observation and guest-progress implementation remains historical evidence. See [24-01-HISTORICAL.md](24-01-HISTORICAL.md). |
| GAME-02 | Phase 21 | Complete in preserved Phase 21 history; not revalidated by T5 | Existing ROM/model/mode/input/predicate receipt and negative controls remain historical evidence. T5 produced no game execution receipt. |
| FIXT-01 | Phase 21 | **Pending** | The exact primary source and sole fallback are pinned in [the closeout record](../../../tests/data/v04-closeout.json). Potion Panic assets, music and converter rights are unresolved; µCity's required `hardware.inc` grant is unresolved. No build, ROM, header or native mode was observed for either candidate. The pair cannot yet be closed as an admission or a bounded no-game absence. |
| RIGHTS-01 | Phase 20 | **Pending** | Source-specific grants and notices are recorded in [the closeout record](../../../tests/data/v04-closeout.json). No payload was staged. Unresolved game and diagnostic components do not have repository/public-CI permission established. |
| DIAG-01 | Phase 22 | **Pending** | dmg-acid2 v1.0 and cgb-acid2 v1.1 source and mgblib code notices are pinned. Footer/reference-image scope remains unresolved; excluded upstream font data has not been replaced and no derivative was created. |
| DIAG-02 | Phase 22 | **Pending** | gbmicrotest source and root MIT notice are pinned. Bytes/digests and distribution terms for 513 generated ROMs, and rights for the embedded logo, remain unresolved. No case was admitted or run. |
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
| gbmicrotest generated ROMs and embedded logo | The `bin` tree has 513 Git-identified ROMs, but their payload bytes/digests were not fetched; logo output rights were not identified. | **Unresolved.** No ROM payload was acquired or staged. |

No inspected component was classified as incompatible with the intended distribution. “Unresolved” records missing component-specific scope or authority; it is not a license prohibition. Build-tool versions remain unpinned/not observed, so no build is claimed reproducible.

The creator metadata for [Potion Panic](https://deved.itch.io/potion-panic) is treated as page metadata only. Exact source URLs, refs, commits, object identities, notice hashes, evidence and blockers are in [v04-closeout.json](../../../tests/data/v04-closeout.json).

## Stage A validation and Stage B stop

Stage A is committed at `e930e3d7f8d2f8b2fc38be5cffb91985354f0ec4`. These checks passed against that immutable commit:

- Python AST parsing for both changed checkers and the focused closeout CLI argument test.
- The rights-stage checker accepted the five exact named sources and reported eight unresolved components.
- Candidate self-test controls passed, including source, rights-scope, component-digest, notice-digest, extra-source, component-set, order and requirement-status mutants.
- Diagnostic self-test controls passed, including the control that reaches the candidate rights refusal.

The admission gate refused for the intended cause. `--check-closeout --closeout-stage games --require-satisfied` reported the unresolved Potion Panic visual assets, music and converter, plus µCity `hardware.inc`. The diagnostic `--require-approved` path returned its scope-resolution refusal naming those same components. These are expected blockers, not passing game admissions.

Stage B did not modify either candidate attempt record: no candidate build was lawful until its applicable local-build grants are established, and no public payload could be staged without repository/public-CI grants. No downloaded game source hook was executed, no external dependency was installed, no game ROM or diagnostic fixture payload was acquired or staged, and no build, runner execution, or broad suite was run.

| Gate | Current result | Consequence |
|---|---|---|
| Potion Panic primary rights | Visual assets, music assets and converter code unresolved | Stop before local build, execution and admission; source/build/ROM/header/native-mode facts remain `not_observed`. |
| µCity 1.3 sole fallback rights | Required `hardware.inc` scope unresolved | Keep fallback blocked; its build cannot establish the original criterion. |
| Acid2 derivatives | Footer/reference-image rights unresolved; font replacement/output absent | Keep DIAG-01 Pending; no build or derivative staging. |
| gbmicrotest | ROM payload identity and embedded-logo grant unresolved | Keep DIAG-02 Pending; no ROM acquisition, execution or staging. |
| Original requirement ownership | FIXT-01 Phase 21; RIGHTS-01 Phase 20; DIAG-01/02 Phase 22 | Keep each Pending; no milestone closure. |

The next useful action is to obtain authoritative, component-specific scope/notice evidence for Potion Panic visual assets, music and converter code and for µCity's required hardware include. Once the primary's required grants are established, the exact primary attempt can proceed; the fallback remains sequenced after a committed primary disposition. Acid2 image/font and gbmicrotest ROM/logo gates require their own evidence before their affected work.
