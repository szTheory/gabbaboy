# Playstead consumer contract for GabbaBoy INT-01 / STATE-01 (research, 2026-10-24)

Scope: read-only inspection of the Playstead repository (no checkout/build/commit/fetch), sibling cores (read-only grep), and GabbaBoy planning. Paths below are repo-relative.

## Revisions inspected

| Repo | Revision | Notes |
|---|---|---|
| Playstead local checkout | HEAD `c65726a6` on branch `feat/dev-standup-and-uat7-closure`, ~1,460 uncommitted/untracked paths | Local `main` is stale (`24491a69`, 2026-09-12). Several cited files are **uncommitted** here (marked WT). |
| Playstead remote `main` (via read-only `gh api`) | `234bd45b21` (2026-10-15, "Phase 4.7 ... (#13)") | Contains `playstead-mac/Playstead/Adapter/CartridgeQualification.swift` (blob `6b5a372c`), i.e. the GB/GBC slice is on main. |
| GB/GBC implementation commit | `4d66b374` "feat(04.6-02): qualify GB and GBC save layouts"; closure `ee18c9f7` | Phase 4.6 completed 2026-10-12 (`.planning/ROADMAP.md:20,406-435`). |
| GabbaBoy | `02776e5` | |
| Siblings | glueyneo `51373b0b`, nesturbator `2a7fde8`, genewhip `684fdd5`, schwaystation `384ee9d`, muhtari `84f7f0d`, cogmaster `1336d3f` | |

## 1. What Playstead expects from an emulator today

**Mechanism: external-process adapter, one hash-pinned emulator app per pin. No libretro, native C ABI, WASM, or in-process host in the product.**

- `playstead-mac/Playstead/Adapter/AdapterPin.json` (last commit `30a4c9ac`, 2026-09-14): `system`, `emulator` (`mgba`), `version` (`0.10.5`), `download_url` + `sha256` of a macOS **DMG**, `launch.executable_relative_path` (`Contents/MacOS/mGBA`), `argument_template` (`["-C","savegamePath={saveDir}","{romPath}"]`), `config_injection` (save dir, BIOS path; controller mapping "unsupported_until_sdl_device_identity..."), `save_contract`, `exit_detection`.
- `save_contract`: `artifact_glob: {saveDir}/{romBaseName}.sav` (raw file in a Playstead-owned directory), `on_demand_flush_supported: false`, `worst_case_loss_seconds: 24`, `save_kind: battery`, `size_is_medium_identity: true`, `accepts_foreign_medium: false`, `max_artifact_bytes: 131072`, `binding_fields: [system_id, save_kind, medium_id, artifact_bytes, rom_sha256]`, `provenance_fields: [emulator, emulator_version, core_version, adapter_pin_sha256]`.
- Exit classification: `0/exit` = clean (user quit); `11/uncaughtSignal` = crash; `9` and `15/uncaughtSignal` = killed. `AdapterHost.terminateAll()` sends SIGTERM, then SIGKILL after a ~2 s grace (`AdapterHost.swift:83-104`, WT-modified). mGBA does **not** flush on SIGTERM; Playstead relies on periodic flush only.
- Installer: `AdapterInstaller.swift:306-340` mounts a disk image with `hdiutil` and copies its single `.app`. A zip/tar CLI package is not supported (also flagged by muhtari's `.planning/preparation/HOSTS-AND-INTEGRATION.md:154,162,219`).
- Catalog: `AdapterCatalog.swift:31-65` (WT-modified) builds supported systems/extensions from **one pin** plus Swift-coded `CartridgeQualification.supportedDeclarations`. Only one emulator adapter can exist at a time.
- System ids already frozen in the client: `gb`, `gbc` (`Design/DesignTokens.swift:99-100`, `Design/SystemAccent.swift:10-11`). The server also has a GB format validator (`playstead-server/lib/playstead/formats/validators/gb.ex`).
- ROM identity: full-file SHA-256 (`rom_sha256`), plus optional DAT/reference-pack title identity for cross-dump restore (`SaveCompatibilityGate.swift`, `sameTitle` verdict).
- Video/audio/input: not specified. The emulator owns its window, audio, and input. Playstead's controller work is an SDL binding bridge into mGBA config (`Adapter/MGBAInputBridge.swift`; `.planning/debug/dualsense-mgba-input-mapping.md`, still investigating).
- Protocol versioning sits on the server wire contract (`/api/v1`, client hello with adapter capabilities; `.planning/discovery/TECHNICAL-RISKS.md:63-80`; PROT-03 done). Per-adapter versioning is the pin plus `adapter_version`/`save_format` fields on each save revision.
- Out of scope in Playstead's own requirements: **"Building emulator cores or a new emulation ABI"** (`.planning/REQUIREMENTS.md:110`). Playstead will not design an ABI for GabbaBoy. GabbaBoy has to fit Playstead's adapter model.

**Test-only exception (libretro):** Phase 6 plan 06-20 (`.planning/phases/06-recovery-proof-ci-and-e2e-pipeline/06-20-PLAN.md`) builds a test-only libretro frontend over the official mGBA 0.10.5 core, because the GUI app could not be driven deterministically. On 2026-10-03 it passed the synthetic capability contract (input, save, fresh-process Continue, repeated framebuffer oracle). The private-fixture stage is blocked because the fixture source is missing (`06-CONTINUATION-QUALIFICATION.md:44-51`, WT-modified; last commit `181fdec7`). Overall: still `qualification / blocked-capability`. The protocol is `playstead-mac/docs/CONTINUATION-PROTOCOL.md` + `scripts/ci/continuation_protocol.py`, both **untracked (WT only)**. Its actions are `qualify`, `initial-run`, `continue`, run under network denial with a fresh private dir. Exit codes: 0 pass, 77 capability refusal, 1 failure.

## 2. Sibling cores in Playstead

- **None is integrated or registered in Playstead.** A repo-wide grep finds no gabbaboy/glueyneo/nesturbator/genewhip/schwaystation/muhtari/cogmaster in code or manifests. They appear only in two documentation records (2026-10-21):
  - `.planning/workstreams/phoenix-console/quick/261020-v5y-.../261020-v5y-CONTEXT.md:108,120,128-132` (`c98a253e`): the owner named gabbaboy, nesturbator and glueyneo as "possible RetroArch-compatible cores". The record says to inspect the facts rather than assume compatibility, and that no emulator integration is authorized.
  - `design-system/EXPERIENCE.md:76-84` (`f8dd77d5`): "Nesturbator and Glueyneo have libretro adapter targets ... GabbaBoy's inspected README/build interface declares a native core and SDL player, without a libretro target." A Playstead playback host with an in-game overlay is "a candidate, not a selected runtime". Libretro is "one possible frontend/core API".
- The siblings are converging on one shape: a headless `<core>-run` CLI for automation and Playstead, plus a libretro core for RetroArch, plus a "Playstead adapter pin", plus "Playstead continuation (qualify, initial-run, continue)". Libretro modules exist in nesturbator, glueyneo, schwaystation, muhtari and cogmaster; genewhip has none. Examples: cogmaster REQUIREMENTS PORT-01/STATE-02, schwaystation STATE-02/PORT-01, and muhtari HOSTS-AND-INTEGRATION §4 with a field-by-field pin mapping.
- Footguns recorded by Playstead and siblings:
  1. SIGTERM is not graceful for mGBA. A core whose player saves and exits 0 on SIGTERM inside the 2 s grace is better (muhtari's recommendation).
  2. The installer accepts only a DMG with one `.app`. Playing through RetroArch plus a core would need a Playstead-side "two-artifact pin".
  3. Assigning a save medium by byte count gave GB 8 KiB the GBA `eeprom_8k` medium and gave RTC files no medium. Phase 4.6 replaced this with header-qualified cartridge tuples (`spikes/GB-GBC-REPORT.md:17-19`; `.codex/skills/spike-findings-playstead/references/production-integration.md:38`).
  4. Controller config overrides were silently ignored by the emulator (DualSense debug).
  5. A green test process with an uninvoked validator, and a GUI emulator that could not be scripted, both block continuation proof.

## 3. Save-data and save-state continuity expectations (constraints on STATE-01)

**Battery saves (what Playstead actually syncs):**
- Each upload is an immutable revision in a parent-pointer DAG (`playstead-server/lib/playstead/saves/revision.ex`). A save line is keyed `(user_id, content_key, save_kind, slot)` with `save_kind` defaulting to `battery` (`saves/save.ex:18-34`; migration `20260904000001`).
- Each revision stores `blob_sha256`, `size_bytes`, `adapter_id`, `adapter_version`, `save_format`, `format_confidence`, base evidence and device times. Concurrent offline writes create **multiple heads** that the user resolves by choice, never last-write-wins (`SaveStateModel.swift`, D-35/D-38). A byte-identical recapture on the same device bumps `confirm_count` instead of creating a new revision (D-30), so deterministic byte-identical exports matter.
- Restore gate (`SaveCompatibilityGate.swift`, WT-modified): system, save kind, **declared `save_format` string equality**, medium id, exact artifact bytes, then exact ROM SHA-256 or a certain title match on both sides. Every mismatch is a hard block. Restore never overwrites in place: the current file is captured first, and SHA-256 is re-hashed at restore (`docs/SUPPORT-MATRIX.md`, "Save restore support").
- The qualified GB/GBC matrix is hard-coded (`CartridgeQualification.swift`). The save_format strings embed the emulator version:
  - `gb` MBC1 `$03`/RAM `$02`: 8,192 B, `mgba-0.10.5-gb-mbc1-sram-8k`
  - `gbc` MBC5 `$1B`/`$03`: 32,768 B, `mgba-0.10.5-gbc-mbc5-sram-32k`
  - `gbc` MBC3+RTC `$10`/`$03`: **32,816 B** (RAM + mGBA's 48-byte RTC suffix), `mgba-0.10.5-gbc-mbc3-rtc-sram-32k-v1`
- RTC rule: "Never strip the RTC suffix, normalize imported original bytes, or imply cross-emulator clock portability" (`references/battery-rtc-continuity.md:33`). The battery and RTC data form **one artifact**, which is consistent with GabbaBoy's unified blob (v0.2 ARCHITECTURE.md:178).
- **Direct conflict:** a GabbaBoy MBC3 timer image is RAM + `GBB_RTC_BLOCK_SIZE` 21 B = **32,789 B** (`include/gabbaboy/gabbaboy.h:184-198`), against mGBA's 32,816 B. The GabbaBoy player also writes an enveloped `.gbb` under SDL's per-user preferences directory, not a raw `{romBaseName}.sav` in a host-given directory (`docs/cartridge-and-saves.md:277-309`). Either difference fails the Playstead glob and the gate.

**Save states:**
- v1 does not support save states at all: they are not captured, synced, restored or exported (`docs/SUPPORT-MATRIX.md`, Save restore support).
- Future **SAVE-05** (v2, deferred; `.planning/REQUIREMENTS.md:101`): opt-in transfer "only for an exact content, emulator/core build, platform, options, and state-format compatibility fingerprint that has passed restore tests".
- TECHNICAL-RISKS.md:63-66: states are experimental, keyed by emulator id + core name/version/build + platform/arch + content SHA-256 + core-options fingerprint, local-only by default, with **no cross-core/cross-version/cross-platform promise**.
- UX decisions (Q13, Q14, Q16 in 261020-v5y-CONTEXT): state save/load happens primarily in an in-game overlay owned by the host. Auto-load of the last state is **off by default**, per device, and not synced. Play never silently loads a snapshot.
- SEED-019 open question: conflict between a newer state and a game save. Loading a state rewrites cartridge RAM, so the host must capture the battery save first.
- What Playstead implies for GabbaBoy: Playstead treats the state blob as **opaque**. It needs a stable, self-describing **compatibility fingerprint** it can compare without parsing, deterministic bytes, a bounded size, and import that is validated all-or-nothing. Migration across versions is the core's own choice. Playstead will only ever trust fingerprints that have passed restore tests, so refusing an incompatible state is always safe and must leave the instance unchanged.

## 4. Playstead roadmap and readiness

- **GB/GBC already ships in Playstead through mGBA 0.10.5** (Phase 4.6 complete 2026-10-12; PROJECT.md:44; on remote main `234bd45b21`). There is no GabbaBoy, SameBoy or Gambatte entry. mGBA is the GB/GBC adapter.
- Current Playstead activity:
  - phoenix-console v1.2 "Player and Server Management", Phase 15 executing (workstream STATE.md, 2026-10-24).
  - Browser play is an explicit mockup with no emulator (`v1.2-CONTEXT.md:27`). v1.2 excludes "emulator integration" (`ROADMAP.md:230`).
  - Root v1.0 is parked, with Phases 3, 5 and 6 open and Apple/HID parked.
- What INT-01 depends on, on Playstead's side:
  - **CLNT-01** (v2, deferred): "a second independent native client **or emulator adapter**" (`REQUIREMENTS.md:91`), together with multi-pin catalog support.
  - Possibly **SAVE-05** (states) and **WEBP-01** (browser core).
  - None is scheduled, and the next Playstead milestone is unselected.
- Playstead-side changes needed for GabbaBoy as a live adapter:
  - more than one adapter pin, or a per-system pin
  - pin-driven (not Swift-coded) cartridge declarations and save_format ids
  - installer support for a non-DMG or unsigned artifact, or a notarized GabbaBoy DMG
  - possibly a two-artifact pin if GabbaBoy is played through RetroArch
- **Conclusion:** Playstead cannot consume a GabbaBoy adapter in GabbaBoy's v0.3 timeframe without owner-scheduled Playstead work. INT-01 should be a GabbaBoy-side **Playstead-conformant adapter, qualified against Playstead's recorded contract**. It should not claim live integration.

## 5. Stale GabbaBoy notes

| Location | Stale claim | Current fact |
|---|---|---|
| `README.md:46-47`; `docs/native-integration.md:277-281` | Playstead adapter is "GBA/mGBA" at pinned `a102d608` | GBA+GB+GBC through mGBA 0.10.5, on Playstead main `234bd45b21` (Phase 4.6) |
| `.planning/research/PRECEDENT.md:24,98-104` | Playstead `1de3e95` (2026-09-28); continuation blocked at the loader | Still blocked overall, but the libretro test-frontend synthetic capability **passed** 2026-10-03; the fixture stage is blocked on a missing source (WT evidence) |
| `.planning/research/SUMMARY.md:73`; DECISIONS D-005 "revisit against actual Playstead contract" | Contract unknown | Contract is now inspectable (pin + save gate + continuation protocol); libretro is not consumed by Playstead |
| `.planning/research/SUMMARY.md:42`; v0.2 `ARCHITECTURE.md:178,255` | "concrete Playstead integration when its consumer contract is available"; confirm the RTC blob with the contract owner | Playstead keeps RAM+RTC as one raw artifact; the mGBA layout is 48-byte suffix / 32,816 B, not GabbaBoy's 21-byte block |
| DECISIONS D-026 | VBA-M/BGB footer interop "deferred to a host adapter" | INT-01 *is* that host adapter; decide here |
| `FUTURE-MILESTONES.md:8-9` | "proven Playstead/libretro path" | No Playstead libretro path exists; owner calls libretro a candidate only |

## Recommendation

### INT-01 definition (v0.3)

"GabbaBoy ships a Playstead-conformant external-process adapter candidate for `gb`/`gbc` battery continuity, qualified by an automated GabbaBoy-side conformance harness against Playstead's recorded pin, save and continuation contract. No live Playstead integration is claimed."

Scope:
1. **Player/runner adapter mode, kept in adapters with no core change.** Add CLI flags `--save-dir DIR --rom PATH`. Write the raw `{romBaseName}.sav` (exact battery bytes) to DIR with an atomic temp file → fsync → rename, using periodic dirty flushes with a declared worst-case loss window. SIGTERM triggers a final save and exit 0 in well under 2 s; a crash keeps the last flushed file.
2. **Raw battery layout decision for timer carts.** Either:
   - (a) the adapter converts GabbaBoy's 21-byte block to and from mGBA's 48-byte suffix for import compatibility only, with honest "clock not portable" scope; or
   - (b) the adapter declares its own GabbaBoy-specific `save_format`/medium ids and size (32,789 B).

   Recommend (b) as the default, because Playstead's gate keys on format string equality and refuses cross-emulator clock claims. Record (a) as a later, evidence-gated interop item. Non-RTC SRAM is byte-identical to mGBA and can be documented as such.
3. **A GabbaBoy-authored candidate pin JSON** in Playstead's schema: system, version, artifact digest, argument template, save_contract with GabbaBoy media/format ids, exit_detection, and the cartridge tuple matrix from GabbaBoy's support ledger. Validate it with a schema/contract test that has negative controls (wrong glob, size, format id, exit code).
4. **Continuation-protocol conformance.** An adapter script implementing `qualify` / `initial-run` / `continue` over the headless runner with a public original GB fixture: network-free, fresh directory, distinct process, repeated agreeing frame-digest oracle after Continue. Exit codes are 0, 77 and 1.
5. **Acceptance evidence**, all automated: CTest lanes for flush/SIGTERM/SIGKILL timing, byte-exact .sav round-trip into a fresh process with a game-visible readback (not just a hash), pin-schema conformance, and continuation 0/77/1 controls.
6. **Out of scope:** live install into Playstead, Playstead code changes, DMG/notarized distribution (unless the owner provides signing), controller mapping via Playstead, state sync, browser/WASM, libretro.

### Libretro
Not in v0.3. Its value for Playstead is **not demonstrated**: there is no product consumer, and the owner's record calls it a candidate. The only Playstead use is a test harness, and GabbaBoy's native API plus headless runner already gives the same deterministic control. Revisit in the following "Interoperability" milestone if (i) Playstead selects a core-wrapping host or two-artifact RetroArch pin, or (ii) the owner wants RetroArch play. Every other sibling ships libretro, which shows low cost but is not evidence of Playstead value. To keep that later step cheap, design STATE-01 so its API maps onto `retro_serialize_size`/`retro_serialize`/`retro_unserialize`: a size bound fixed per loaded ROM and a caller-owned buffer.

### STATE-01 constraints derived from Playstead
- Opaque blob with a self-describing header: magic, format version, core version/build id, model/profile, ROM SHA-256, and a fingerprint of the options and RTC policy, so a host can derive SAVE-05's compatibility fingerprint without parsing machine state.
- Deterministic byte-identical output for identical state, a bounded size queried in advance, and all-or-nothing import that leaves the instance unchanged on refusal (wrong ROM, model, version, truncation, corruption).
- Explicit policy: v0.3 accepts the exact format version only. Migration is optional and documented, with no cross-version promise.
- Document that loading a state replaces cartridge RAM and RTC. Hosts must capture the current battery save first, the same as Playstead's never-overwrite-in-place restore, and keep battery saves as the durable progress path.

### Sequencing
The STATE-01 format design must precede any INT-01 work that covers states. INT-01's battery/launch/continuation lane does **not** depend on STATE-01 and can run in parallel or first, because Playstead consumes only battery saves today. Suggested order:
1. STATE-01 serialization (complete machine state).
2. INT-01 battery adapter and conformance, in parallel.
3. A thin INT-01 addendum that declares the state fingerprint for a future SAVE-05, with no sync.

Live Playstead integration is gated on Playstead's CLNT-01 multi-adapter work, which is the owner's choice of timing.
