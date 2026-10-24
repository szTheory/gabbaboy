# GabbaBoy rolling roadmap research (v0.3 → v1.0)

Prepared 2026-10-24 as input to `/gsd-new-milestone`. This is research and recommendation, not adopted scope. It does not authorize advancing into a milestone or phase.

**Inputs read:** `.planning/PROJECT.md`, `.planning/context/FUTURE-MILESTONES.md`, `.planning/milestones/v0.2-REQUIREMENTS.md` (Future and Out of scope), `.planning/context/DECISIONS.md` (D-001..D-101, especially D-005, D-007, D-026, D-082, D-101), `.planning/research/INDEX.md`, `.planning/research/v0.2/SUMMARY.md` (rights gates G1–G7), Phase 15 context and research (Rebound attempt), `.planning/STATE.md`. Sibling evidence came from Playstead `.planning/ROADMAP.md` (Phase 4.6), `.planning/spikes/GB-GBC-REPORT.md` and `PRODUCT.md`, read only.

**External checks (2026-10-24):** primary repository pages and licence files for cgb-acid2, mgblib, Mealybug Tearoom, gbmicrotest, µCity, Geometrix, gbhack, Shock Lobster, Tobu Tobu Girl DX, Potion Panic and GBDK-2020. I also took a sparse metadata-only clone of `gbdev/database`, the Homebrew Hub dataset, and filtered its 1,369 `game.json` entries by `platform == "GBC"` and the `license` field.

**Evidence confidence:** licence statements are taken from the repositories' own pages and files, which is HIGH confidence for what those pages say. Per-asset rights are not established by a root licence; every candidate still needs a full audit. Statements about which hardware revisions behave which way are MEDIUM confidence (author-asserted or emulator-source-derived).

---

## 0. The five findings that matter most

1. **Playstead does not need save states for its first GabbaBoy integration.** Playstead integrates emulators through a client-side process adapter. It currently runs a pinned mGBA 0.10.5, and Phase 4.6 qualified GB/GBC play through it. Its contract separates persistent battery saves from emulator save states ("Persistent saves and emulator save states are different artifacts", PRODUCT.md). Its qualified GB matrix uses MBC1 8 KiB SRAM, MBC5 32 KiB SRAM, and MBC3 32 KiB SRAM plus a **48-byte RTC suffix** (the VBA-M/mGBA footer). GabbaBoy writes a native 21-byte RTC block (D-064). So the shortest route to INT-01 runs through **battery and RTC interop plus a launchable adapter contract**, not through STATE-01. The "BGB/VBA-M RTC footer adapter" deferred in Phase 9 becomes a direct INT-01 dependency rather than a nice-to-have.
2. **Rights-clear CGB game candidates exist beyond Rebound.** The Homebrew Hub dataset lists 451 GBC entries, and only 25 declare a licence. Among those, **Potion Panic** (DevEd, MIT, RGBDS, GBCompo 2025) and **µCity** (GPL-3.0+ code, CC BY-SA 4.0 media, CGB-only, v1.3 2025) are the strongest. Potion Panic is by Rebound's author but is newer, so it is more likely to build with current RGBDS (Rebound failed with RGBDS v1.0.1). GBDK-2020's runtime is GPLv2 with a linking exception, so ROMs built with GBDK-2020, such as gbhack (MIT), carry no runtime encumbrance. That clears the G2-type concern for modern GBDK titles, though not for Tobu's GBDK 2.96.
3. **acid2 and Mealybug are blocked only by the font, and the font can be engineered around.** cgb-acid2, dmg-acid2, Mealybug and mgblib are all MIT at the repository level. The open item (G1) is the provenance of the bitmap font inside mgblib. Because the ROM source is MIT, a **font-substituted derivative build** is permitted: replace the glyph bytes with an original or CC0 font, then compare with the text region masked, or against a reference regenerated only in the text tiles. This is the same pattern Mooneye derivatives already use (G6, zeroed font). It unlocks the highest-value PPU qualification targets without waiting for the font author. Caveat: Mealybug ships references for DMG, CGB-C and CGB-D only, **not CGB-E**, so its CGB results against the CGB-E profile are a model-mismatch evidence class (§3).
4. **"Slower than v0.1" is the wrong frame for the performance regression.** The DMG path is 15–24% slower than v0.1. That matters only relative to an absolute budget: realtime headroom on a declared low-end reference, such as Wasm in a browser, a Raspberry Pi-class ARM board, or the hosted CI runners. The next accuracy work (a pixel-FIFO fetcher and mid-scanline effects) will cost more per dot. Recovering 20% now and spending 40% in v0.5 is churn. Recommendation: set an **absolute realtime-multiple budget, plus a deterministic cost proxy** (instruction count) gate for unexplained regressions, then recover only what the budget demands.
5. **v0.2's size came mostly from the evidence and process machinery, not from emulation.** v0.2 ran 10 phases and 170 plans, and Phase 15.1 alone ran 19 plans of release hardening. Small milestones therefore need both fewer tracks and explicit plan budgets per phase, with a rescope trigger on overrun.

---

## 1. Capability ladder: what mature GB emulators climb, and what matters here

The project goal is a **trustworthy, evidence-bounded, embeddable core for Playstead and other frontends**. The value rating below is judged against that goal, not against feature parity with SameBoy or mGBA.

| Rung | What mature cores do (SameBoy / Gambatte / mGBA / Mesen2 / GateBoy) | GabbaBoy now | Value for this project | Rationale |
|---|---|---|---|---|
| CPU instruction and timing | Universal baseline; Blargg `cpu_instrs`, `instr_timing`, `mem_timing`; Mooneye acceptance | Mooneye-derived closures pass; Blargg is local-only (unlicensed) | Done; keep | Already qualified |
| **PPU mode-3 length, pixel FIFO/fetcher, mid-scanline register effects, window quirks, OBJ penalties** | SameBoy, Gambatte and GateBoy model the FIFO and fetcher closely; mGBA is close; dmg-acid2, cgb-acid2, Mealybug, gbmicrotest and Mooneye `ppu/` are the qualification targets | Deferred (D-083); most of the 82 CGB expected failures cluster here and in timing (AGE `m3-*`, `ly-cgbE`, `lcd-align`) | **Very high** | Largest gap between "runs test ROMs" and "renders games correctly". Raster effects in many games depend on it. It is the main producer of expected failures |
| **APU accuracy** (frame sequencer, wave RAM quirks, zombie mode, NRx2 writes, CGB PCM12/PCM34) | SameBoy is the reference; SameSuite APU tests; Blargg `dmg_sound` and `cgb_sound` | Scoped four-channel; CGB PCM digital I/O done (CGB-08) | **High** | Audio is user-perceptible in every game, and SameSuite is already admitted |
| CGB-specific timing (double-speed edge cases, HDMA timing, separate CPU/DMA buses, OAM DMA conflicts) | SameBoy models CGB-0..E; AGE tests | Speed switch and HDMA done to a software model; separate buses deferred | High (narrowing) | Remaining edges carry many expected failures, but games rarely depend on them |
| Other revisions: DMG-0, MGB, SGB/SGB2, CGB-0/A/B/C/D, AGB | SameBoy models most; mGBA and Gambatte model fewer | DMG-B and CGB-E only (D-026) | **Medium for CGB-D (evidence unlock) and MGB**; low for others | Most public reference images (Mealybug, much hardware evidence) are CGB-C/D. A CGB-D profile may cost little if D and E differ in few observable ways, which is unverified. AGB mostly matters for games that detect GBA. DMG-0 and CGB-0 are vanity |
| Boot ROM, optional user-supplied | All mature cores accept one; none ship Nintendo's | Bootless only | **Medium** | Also resolves G4: a user-supplied CGB boot ROM gives the authentic title-hash DMG-compat palette with no repository distribution, and gives exact post-boot state. It must stay optional, with the hash only verified locally |
| SGB borders, palettes and packets | SameBoy and mGBA support them. They need packet decoding and border rendering, not full SNES emulation | None | Medium-low | Visible improvement for many DMG titles, but it is a frontend-facing presentation feature that needs host layout (256×224). Better after v1.0 |
| Link cable | SameBoy (two instances), mGBA, BGB (network) | Serial exists, single instance | Low-medium | Two-instance lockstep stepped by a host is clean in this architecture. Real demand is low |
| IR (CGB RP port) | SameBoy (between instances) | Fails closed | Low / vanity | Rarely used |
| MBC1M multicart | Common | Rejected; Mooneye `multicart_rom_8Mb` excluded | Low-medium, **cheap** | Small mapper delta plus an existing fixture: a good filler task, never a milestone driver |
| MBC6, MBC7 (accelerometer), HuC1/HuC3 (IR/RTC), Camera, TAMA5, MMM01 | mGBA and SameBoy cover subsets | Rejected | Low / vanity | Few titles, all commercial (no rights-clear fixtures), and they need host peripherals. Keep explicit rejection |
| Rumble (MBC5) host haptics | Common | State query exists | Low | Adapter concern; needs device policy |
| **Save states** | Universal; SameBoy's BESS is a cross-emulator interchange block | None (STATE-01) | **High as an enabler** | Enables rewind, runahead, frontend suspend/resume and test acceleration. It also gives a strong metamorphic test: snapshot at a random point, restore, then compare digests, which finds hidden state. No current consumer requires it |
| Rewind / runahead | Frontend features built on fast states | None | Medium (after states) | Core obligation: fast, bounded, allocation-free state save and load. The features themselves belong to frontends |
| Netplay | mGBA and RetroArch (rollback via states) | None | Vanity for now | Needs states, determinism and a network host. Determinism already exists; demand does not |
| **libretro core** | mGBA, SameBoy and Gambatte all ship one | None (D-005: later) | **Medium-high for "other frontends"** | Cheapest reach to RetroArch-class frontends. Its global-callback API conflicts with "no hidden globals", but only inside an adapter, which is acceptable |
| **Wasm / web build** | mGBA, SameBoy (web) and Gambatte variants | None | Medium, cheap | Portable C17 plus an Emscripten CI leg is a strong portability proof. It also gives a natural low-end performance reference |
| Battery and RTC interop (VBA-M/mGBA 48-byte footer, BGB 44-byte) | Universal | Native 21-byte block; footer deferred | **High (INT-01 dependency)** | Playstead's qualified MBC3 layout uses the 48-byte footer (§0.1) |
| Debugger, tracing, memory inspection | SameBoy, BGB, Emulicious, Mesen2 | Tracer exists | Medium | The FUTURE-MILESTONES "developer tools" horizon. Useful for diagnosing expected failures |

**Do next:** PPU FIFO/fetcher qualification, APU qualification, save states, battery and RTC interop, a Playstead adapter, Wasm and libretro reach, and an optional user boot ROM.
**Do opportunistically:** MBC1M and a CGB-D profile, if a spike shows small deltas and large evidence gains.
**Post-1.0 or demand-only:** SGB, link cable, other revisions, exotic mappers, IR, netplay, camera.

---

## 2. Candidates for the first CGB game-level evidence (D-026 style)

D-026 and Libbet set the bar: an admitted rights-clear ROM with a recorded build recipe and digest, a guest-observable start or progress predicate taken from source-visible state, meaningful scripted input, a visible or audio response, failing controls (no input, wrong input), and an applicability label. The predicate source matters most: a candidate needs source-visible WRAM/HRAM variables for level, score or state.

### 2.1 Homebrew Hub (`gbdev/database`) scan, 2026-10-24

1,369 entries; 451 have `platform: GBC`. Of those, 428 declare no licence. The licensed GBC games are listed below. Tools and demos (mostly TeamKNOx peripheral tools, MIT, which need hardware) are omitted.

| Candidate | Licence (as declared) | CGB use | Toolchain | Predicate potential | Main risk | Verdict |
|---|---|---|---|---|---|---|
| **Potion Panic** (DevEd, GBCompo 2025) — [repo](https://codeberg.org/DevEd/potion-panic/src/branch/gbcompo25) | MIT root (`Copyright (c) 2025 DevEd`) | GBC single-screen platformer | RGBDS + Python 3 + SuperFamiconv (MIT); submodules | Level and objective state in source (`GameModes/`, `Levels/`) | Audio driver submodule and asset rights unaudited; the README warns macOS builds are unverified; DevEd's Rebound failed on RGBDS 1.0.1 | **Primary**: newest, MIT, native CGB |
| **µCity** (AntonioND / SkyLyrac) — [GitHub](https://github.com/AntonioND/ucity), [Codeberg releases](https://codeberg.org/SkyLyrac/ucity/releases) | GPL-3.0+ (only files carrying the header); GBT Player BSD-2; media CC BY-SA 4.0 | **CGB-only**, two ROMs (`ucity.gbc`, `ucity_compat.gbc`), SRAM saves | Recent RGBDS (unversioned) | City data, funds and date in WRAM; menu to new city to build actions | GPL and BY-SA fixture policy (owner decision, §2.3); a slow-progress simulation makes predicate budgets long | **Primary alternate**; also exercises CGB plus battery |
| Geometrix (AntonioND) — [repo](https://github.com/AntonioND/geometrix) | GPL-3.0 | All models (`.gbc`); CGB colour | RGBDS | Score and combo counters | GPL policy; dual-mode, so less CGB-specific | Secondary |
| gbhack (statico) — [repo](https://github.com/statico/gbhack) | MIT code; Kenney art CC0; **music "per original licence terms"** | GBC roguelike, MBC5 + 32 KiB battery SRAM | GBDK 4.3.0 (runtime GPLv2 with linking exception, so ROMs are unencumbered) | Turn counter, dungeon level, auto-save every 50 turns | Music rights unclear; procedural RNG needs seeded input | Secondary (MBC5 + battery + CGB in one) |
| Aevilia (ISSOtm et al.) — [repo](https://github.com/ISSOtm/Aevilia-GB) | Apache-2.0 | GBC RPG | Old RGBDS | Map and state variables | Pre-alpha; likely the same RGBDS drift as Rebound | Tertiary |
| Tobu Tobu Girl DX — [repo](https://github.com/SimonLarsen/tobutobugirl-dx) | MIT code, CC BY 4.0 assets | GB + GBC + SGB | GBDK 2.96 + SDCC 3.8 + custom tools ("a huge mess") | Height and score | G2 (GBDK 2.96 runtime terms) plus build reproducibility | Only if G2 clears |
| Rebound (DevEd) | MIT root | Native CGB, MBC5 | RGBDS (failed on 1.0.1 with 494 errors) | Level, screen and coin | D-07 cutoff already reached in Phase 15 | Reopen only with a pinned older RGBDS (for example the 0.6/0.7 series) as an owner decision |
| Escape Obliterizer DX — [repo](https://github.com/jcnmsg/escape-obliterizer-gbc) | GPL-3.0 | ships as `.gb` | ? | ? | Likely DMG-first | Low |
| Europa Rescue / Labirinth (godai) | CC BY-SA 4.0 | `.gbc` | Probably GB Studio (unverified) | Engine variables | GB Studio engine and plugin rights (as in G3) | Low |
| Petris (bbbbbr) | **CC BY-NC-SA** | GBC | GBDK | — | NonCommercial conflicts with MIT-repo redistribution | **Reject** |
| Shock Lobster (tbsp) — [repo](https://github.com/tbsp/shock-lobster) | Zlib; music CC BY 4.0 | DMG-designed, no CGB features stated | RGBDS | — | Not CGB | Not a CGB candidate (possible second DMG game) |

### 2.2 Recommended procedure (time-boxed, avoiding a repeat of the Rebound sink)

- **Time-box:** at most two candidates, at most one plan each for the rights, build and digest gate. Order: Potion Panic, then µCity (or gbhack if the owner rejects GPL fixtures).
- **Gate order:** (a) per-asset licence audit, including submodules and audio drivers; (b) a pinned toolchain build reproduced in CI (RGBDS version pinned by digest); (c) the ROM digest matches any upstream release binary, or the build is declared canonical; (d) predicate feasibility from source symbols, read from the `.sym` file emitted by RGBDS; (e) only then, runner integration.
- **Fallback if both fail:** keep CGB game-level evidence explicitly absent. If absence recurs, the D-026 premise is in question. Then either (i) author an original CGB mini-game fixture, a project-owned "game-shaped" ROM that is not a third-party game and must be labelled as such, or (ii) adopt a **local-only private game observation** lane (AGENTS.md permits it as a distinct evidence class) that never enters public CI.

### 2.3 Owner policy question surfaced: GPL and copyleft fixtures

The v0.2 out-of-scope table lists "GPL Gambatte tests" among unlicensed fixtures. GPL is a redistribution licence. Shipping a GPL ROM plus its corresponding source (or a written offer) as test data next to MIT code is ordinary aggregation and does not relicense the core. The real costs are a source-availability obligation per fixture, CC BY-SA attribution, and keeping such bytes out of installed packages, which the repository already does for fixtures. A one-time owner decision ("copyleft fixtures admitted with source mirror and attribution; never installed or packaged") would unlock µCity, Geometrix and the **Gambatte hwtests** (GPL-2; a very large DMG and CGB timing corpus with expected outputs encoded in file names; CGB results are reportedly hardware-verified, mostly on CGB-C/D-era units, which needs checking). This is the single highest-leverage rights decision available.

---

## 3. Next qualification suites and their redistribution status

| Suite | Licence / redistribution | Automation | Model applicability | Current status | Next-step value |
|---|---|---|---|---|---|
| **dmg-acid2** ([repo](https://github.com/mattcurrie/dmg-acid2)) | MIT; mgblib MIT; **font provenance unknown (G1)** | Screenshot on `LD B,B`, exact compare | DMG reference (hardware photo provided) | Local-only runner (D-082) | **Very high.** Single-frame PPU composition: window, OBJ priority, 10-OBJ limit, 8×16, flips. Build a font-substituted derivative and mask or regenerate text tiles |
| **cgb-acid2** ([repo](https://github.com/mattcurrie/cgb-acid2)) | Same as above; v1.1 release ROM | Same | CGB (reference from hardware) | Local-only, pinned SHA-256 (`cgb_acid2_local_*` CTests) | **Very high**, same route. Directly tests CGB attribute and priority paths already built in Phase 11. **Note:** acid2 is composition, not timing, so it should already pass, and a pass is cheap credibility |
| **Mealybug Tearoom** ([repo](https://github.com/mattcurrie/mealybug-tearoom-tests)) | MIT (repo); G1 font; prebuilt zip in repo | Screenshot on `LD B,B`, ImageMagick AE = 0; CGB channel expansion `(r<<3)\|(r>>2)` | References for **DMG, CGB-C, CGB-D**; **no CGB-E** | `not-run:rights-gate-G1` | **High** for DMG mid-scanline (mode-3) work. Against CGB-E it can only be "differential vs CGB-D reference" unless a CGB-D profile exists |
| **gbmicrotest** ([repo](https://github.com/aappleby/gbmicrotest)) | MIT | Result at `$FF80`, expected at `$FF81`, status at `$FF82` (`$01` pass / `$FF` fail): **ideal for headless CTest** | DMG ("DMG-CPU-08 I believe": revision uncertain); GateBoy's gate-level source is the cross-check | Not admitted | **High, cheap.** Hundreds of single-cycle probes of PPU, timer and DMA edges. Admission needs a font and asset check and a model label of "DMG, revision unconfirmed" |
| SameSuite | MIT (G7 notice: `hexdigits.2bpp`) | Register-dump pass/fail | Mostly CGB (verify per ROM) | Admitted in Phase 13 (four HDMA cases) | **High** for the APU milestone: expand to its APU and PPU directories |
| AGE test ROMs | Admitted (CC0 font) | Pass/fail protocol | Per-ROM `Verified:` lines, many CGB-E | 13 ROMs admitted; `m3-*`, `ly-cgbE`, `lcd-align-ly-cgbE` expected-fail | High: the CGB-E-native timing targets |
| Mooneye acceptance `ppu/*`, `oam_dma/*`, `instr/*` | MIT; font replaced (G6) | `LD B,B` Fibonacci registers | Per-ROM model tags | CPU, timer, MBC and CGB subsets admitted | Medium-high: extend to `ppu/` when the fetcher lands |
| Blargg (`cpu_instrs`, `instr_timing`, `mem_timing`, `dmg_sound`, `cgb_sound`, `oam_bug`, `halt_bug`) | **No licence statement**; not redistributable | Serial and `$A000` text output | DMG and CGB | Local-only | Keep local-only. Useful as a private oracle, never as public evidence |
| Gambatte hwtests | GPL-2 (copyleft, redistributable with source) | Expected value in file name; screenshot or text | DMG and CGB | Excluded as "unlicensed" (policy question §2.3) | **Potentially very high** if copyleft fixtures are admitted |
| MagenTests, rtc3test | Admitted | — | — | In corpus | Maintain |
| TurtleTests, MBC3 Tester | Unlicensed | — | — | Excluded | Keep excluded |
| 240p Test Suite (Pinobatch, GB/GBC) | zlib (per author; verify) | Visual and manual | Both | Not admitted | Low (visual only) |
| daid's GBEmulatorShootout | Results matrix (check licence) | — | — | — | Use as a *target list and cross-emulator status*, never as evidence |

**Recommended qualification order:** (1) acid2 pair via a font-substituted derivative, an immediate credibility win that requires no timing work; (2) gbmicrotest admission, which is cheap and automatable and gives a DMG timing denominator before the fetcher rewrite; (3) Mealybug DMG plus Mooneye `ppu/` with the fetcher rewrite; (4) AGE `m3-*` and `ly-cgbE` plus cgb-acid2 regressions with CGB mode-3; (5) SameSuite APU, plus local Blargg sound as a private oracle, for the APU milestone.

---

## 4. Proposed milestone sequence

### Guiding rules

- **Size:** at most 4 phases and roughly 40 plans per milestone. Each phase gets a plan budget; **a 50% overrun is a rescope trigger**, not a reason to push on. Release hardening is a planned final phase with its own budget, so it cannot balloon into a 15.1.
- **Track count:** at most two substantive tracks per milestone (for example, one emulation track and one integration track).
- Every milestone ends with a qualified release scoped to its corpus, under the existing D-015, D-069 and phase-stop rules.
- **Pre-1.0 save state compatibility is same-version only:** versioned, with explicit rejection of mismatches. This makes states before the PPU rewrite cheap; cross-version migration is a v1.0 obligation.

### Recommended (Option A): v0.3 = consumer first, save states second

| Milestone | User outcome | Scope (phases) | Exit evidence | Rescope triggers |
|---|---|---|---|---|
| **v0.3 Playstead-Ready Continuity** | A Playstead user can play supported GB/GBC titles through a GabbaBoy adapter, and battery/RTC saves exchange with mGBA-layout files; the first CGB game evidence exists, or its absence is re-justified | P1 **Performance floor**: define an absolute realtime budget on named reference hosts plus a deterministic instruction-count proxy gate; profile and recover only what the budget requires. P2 **Battery/RTC interop**: VBA-M/mGBA 48-byte and BGB 44-byte RTC footer import/export as a *host-side adapter* (core block unchanged), with named fixtures and negative cases. P3 **INT-01 adapter**: launchable headless or player adapter honouring Playstead's adapter contract (system descriptors, battery path, exit receipts), qualified by **Playstead's CI consuming a GabbaBoy release artifact** against Playstead's authored GB/GBC fixtures. P4 **Time-boxed CGB game evidence** (§2.2) plus v0.3.0 release. Carry-over: triage the 12 LIM rows, PR #75 and #78–92, and wire the Phase 8 verifiers, as P1 hygiene with a fixed budget | Playstead-side journey (import, play, battery capture, fresh-profile restore, readback) green on GabbaBoy; footer round-trip and rejection fixtures; performance budget receipt; CGB game acceptance, or a recorded absence plus fallback decision | Playstead's own pipeline is blocked (its Phase 3 and HID gates) and cannot consume an artifact within the P3 budget: ship the GabbaBoy-side contract plus a contract-test harness and record the integration as `not_verified`. Both CGB candidates fail their gates: the absence fallback decision (§2.2) becomes mandatory input to v0.4. The performance budget is already met: P1 shrinks to the gate only |
| **v0.4 Native Save States** | Frontends can suspend, resume and rewind deterministically | STATE-01: complete DMG+CGB state including in-flight PPU, APU, DMA, HDMA, speed-switch and RTC; explicit portable little-endian serialization; transactional load (no partial mutation); bounded size and work; fuzzed loader; random-point snapshot equivalence across the **whole admitted corpus** (a metamorphic test of hidden state); a measured save/load cost for runahead feasibility. Optional: BESS export block for interchange | Snapshot at N random points per corpus case, restore and compare frame/PCM digests (with a negative control: deliberately omit one field and require failure); fuzz campaign; consumer C/C++ API tests | State completeness forces large refactors of hidden state: split into "state model" and "public API plus format" milestones. BESS conformance proves costly: drop it to post-1.0 |
| **v0.5 DMG PPU Timing Qualification** | DMG games with raster effects render correctly within a declared corpus | Pixel-FIFO and fetcher, mode-3 length (SCX, window, OBJ penalties), mid-scanline register writes, STAT edge timing; admit gbmicrotest; dmg-acid2 derivative; Mealybug DMG; Mooneye `ppu/`; re-budget performance | Declared denominators with pass and expected-failure counts per suite; Libbet baseline either byte-identical or re-frozen with a justified diff; performance within the v0.3 budget | Fetcher rewrite exceeds budget: land behind a profile flag and keep the old renderer as reference. Performance falls below budget: insert a performance phase before CGB work |
| **v0.6 CGB Timing and Colour Qualification** | CGB games render and time correctly within a declared corpus; the expected-failure count drops substantially | CGB mode-3 differences, AGE `m3-*`, `ly-cgbE`, `lcd-align`, cgb-acid2 regression, CGB OAM/DMA separate buses, a second CGB game; an optional user-supplied boot ROM (exact post-boot state, authentic compat palettes locally); a spike on a CGB-D profile for Mealybug CGB references | The 82 expected failures cut to an owner-chosen target (for example ≤40), each remaining one reason-coded; two CGB games pass | CGB-D spike shows a large divergence: keep CGB-E only and label Mealybug CGB as differential |
| **v0.7 Audio Qualification** | Accurate audio for the declared corpus | APU edge behaviour (frame sequencer, wave RAM, NRx2 zombie writes, length and trigger quirks, CGB differences); SameSuite APU admission; local Blargg sound oracle; PCM digests | SameSuite APU denominators; PCM regression digests; no perceptual claim | — |
| **v0.8 Reach** | Use GabbaBoy in RetroArch-class frontends and in a browser | libretro core adapter (globals confined to the adapter; states via STATE-01); Emscripten/Wasm CI leg with a performance budget; optional MBC1M | libretro API conformance smoke (headless frontend harness); Wasm realtime receipt | No demonstrated adopter demand: keep only the Wasm leg (portability evidence) and defer libretro |
| **v1.0 Stable Embeddable Core** | Adopters can depend on GabbaBoy with SemVer guarantees | API/ABI freeze and deprecation policy; save state forward migration (v1 format guaranteed); a support matrix per model, mapper and suite; signed and notarized macOS player (if credentials exist); a security and fuzz baseline; adopter documentation | See §5 | — |

**Post-1.0 (evidence- and demand-driven):** SGB borders and palettes; two-instance link cable; rewind and runahead in the player; MGB and AGB profiles; exotic mappers (MBC7, HuC, camera) only with rights-clear fixtures and an adopter request; IR, netplay and TAMA5 stay unscheduled.

### Option B: v0.3 = STATE-01 + INT-01 only (the current provisional definition)

This works if the owner values designing serialization before Playstead integration. Cost: STATE-01 has no consumer requirement today; Playstead needs battery and RTC interop, which this option omits. That makes "qualified INT-01" either hollow or forced to absorb the footer work anyway. The option also defers CGB game evidence and the performance budget a third milestone in a row.

### Option C: v0.3 = evidence floor (CGB game + acid2 + gbmicrotest + performance budget), then v0.4 States & Integration

This gives the most honesty per unit of work: it fixes the two credibility gaps the v0.2 release discloses. Cost: Playstead waits longer, and acid2 depends on the derivative-font approach being accepted.

**Recommendation: Option A.** It gives the first real consumer what it actually needs, keeps STATE-01 as its own milestone so serialization is designed once, and carries a time-boxed CGB game attempt. If the owner wants acid2 early, the font-substituted acid2 pair fits as an add-on to v0.3 P4 (roughly 3–5 plans), because acid2 needs no timing work.

---

## 5. What "v1.0" should mean for GabbaBoy

v1.0 is a **stability and evidence promise, not a compatibility promise.**

1. **Stable public C API/ABI** with SemVer: additive-only within 1.x; sized structs (`struct_size` already exists); a deprecation window documented and tested by installed C and C++ consumers against the previous minor release.
2. **Stable save state format v1** with forward loading guaranteed across 1.x (old states load in newer cores, or are rejected explicitly with a reason code), fuzzed and transactional. Battery formats, native and interop footers, are guaranteed the same way.
3. **Declared support matrix:** models (DMG-CPU-B, CGB-CPU-E, plus any added profiles), mappers (ROM, MBC1/2/3/5, ±MBC1M), each with executed denominators and reason-coded expected failures. Minimum qualification: dmg-acid2 and cgb-acid2 pass (derivative builds); Mooneye acceptance applicable subset; gbmicrotest and Mealybug DMG within declared exceptions; AGE CGB-E timing subset; SameSuite APU subset; **at least two rights-clear DMG and two CGB games** with game-level acceptance.
4. **At least one live consumer integration qualified:** Playstead in its CI against a release artifact, plus libretro or Wasm if those milestones ran.
5. **Performance budget met** on declared reference hosts (including one low-end host or Wasm), with the deterministic cost-proxy gate in required CI.
6. **Security baseline:** fuzzed ROM, battery and state loaders with recorded campaigns; bounded work and allocation proofs as now.
7. **Distribution:** exact-tag qualified release; the player is signed and notarized if credentials exist, otherwise stated as unsigned. Never a "plays all games" claim.

---

## 6. Adversarial critique of the recommended sequencing

1. **INT-01 depends on another project's health.** Playstead's Phase 3 is `gaps_found`, with Apple HID and provisioning parked, and its adapter contract is shaped around launching mGBA. Making v0.3's exit depend on Playstead CI consuming a GabbaBoy artifact couples two release trains. *Mitigation:* define INT-01's GabbaBoy-side exit as a published adapter contract plus a contract-test harness replaying Playstead's journey headlessly. The Playstead-side qualification is a stretch exit that is recorded honestly when blocked. *Residual risk:* that is the "local pass is not remote proof" pattern the project already warns about.
2. **The "absolute performance budget" may be a rationalization for not fixing a real regression.** A budget can always be set loosely enough to pass. *Mitigation:* choose the budget before measuring, from a declared low-end target (Wasm in a mid-range browser, or a Pi-class ARM board). Keep the instruction-count proxy gate for *unexplained* regressions regardless of budget.
3. **Save states before the PPU rewrite means serialization churn.** The v0.5 fetcher rewrite will replace most PPU hidden state. *Counter:* same-version-only states pre-1.0 make churn a code change, not a compatibility break. The random-point equivalence test then *protects* the rewrite, because it catches state the new fetcher forgets. *Residual risk:* each PPU change pays a serialization tax. If v0.5 is likely to start within one milestone, swapping v0.4 and v0.5 is defensible.
4. **A third consecutive CGB game attempt may fail again.** Rebound burned a bounded attempt. Potion Panic shares its author and RGBDS lineage. µCity depends on an unmade GPL policy decision. *Mitigation:* the two-candidate, one-plan time-box plus a pre-decided fallback (an original CGB game-shaped fixture or the local-only private lane). Make the GPL decision at milestone definition, not mid-phase.
5. **The font-substituted acid2 derivative weakens the evidence.** Masking the text region removes exactly the pixels whose rendering includes the "Hello World" OBJ/BG mix. Regenerating them makes the reference partly project-authored. *Mitigation:* label it "derivative of `<commit>`, glyph tiles replaced, text tiles masked (N px)", the same as Mooneye G6. Keep the original local-only runner as a cross-check (D-082). Ask the author in parallel; if the font clears, drop the derivative.
6. **The Mealybug and CGB-D references tempt profile sprawl.** Adding a CGB-D profile to harvest evidence contradicts D-026's single-revision discipline and may be "vanity with extra steps". *Mitigation:* spike only; adopt only if the delta list is small and source-backed (SameBoy revision branches), with an explicit model gate.
7. **Plan budgets may be fiction.** v0.2's 170 plans came partly from verification and closeout machinery that applies to every phase. Capping plans without reducing per-plan overhead just yields fewer, bigger plans. *Mitigation:* v0.3 P1 hygiene should also consolidate verifiers (the generalised suite verifier deferred from Phase 8) and move phase-directory helpers into `tests/` so phase records can be archived. That treats process cost as debt to pay down, not only scope to cut.
8. **libretro sits too late at v0.8.** "Other frontends" is half of the stated goal, and libretro is the cheapest multiplier. *Counter:* libretro without save states, accurate PPU and audio gives a poor first impression in a crowded ecosystem (SameBoy, Gambatte and mGBA cores already exist), and there is no named libretro adopter. Revisit if one appears.
9. **APU work at v0.7 is late for a project with audio in every release.** Audio regressions are user-perceptible, while PPU edge cases often are not. *Counter:* PPU timing produces most expected failures and gates more suites. If Playstead users report audio defects, swap v0.6 and v0.7.
10. **Option A spreads v0.3 over four tracks** (performance, interop, adapter, CGB game) despite the two-track rule. *Honest answer:* performance and hygiene in P1 and the CGB attempt in P4 are budget-capped side tracks. If the owner enforces two tracks strictly, move the CGB attempt to v0.4 and keep v0.3 as performance-gated interop and adapter work.

---

## 7. Decisions to put to the owner at `/gsd-new-milestone`

1. Option A, B or C for v0.3.
2. Copyleft fixture policy (GPL and CC BY-SA, with source mirror and attribution, never installed). This unlocks µCity, Geometrix and Gambatte hwtests.
3. Accept font-substituted derivatives for acid2 and Mealybug (G1 workaround), plus a parallel request to the mgblib author.
4. Performance policy: an absolute realtime budget on named hosts plus an instruction-count proxy gate, versus recovering to the v0.1 baseline.
5. Pre-1.0 save state compatibility: same-version only.
6. Whether INT-01's required exit is the Playstead-side CI run or the GabbaBoy-side contract harness.
7. Whether to reopen Rebound with a pinned older RGBDS (it would revisit D-101's cutoff).
8. Disposition of the 12 LIM rows and the PR backlog (#75, #78–92) as P1 hygiene with a fixed budget.

---

## Sources

- Pan Docs: https://gbdev.io/pandocs/ ; Homebrew Hub: https://hh.gbdev.io/ ; dataset: https://github.com/gbdev/database (per-entry `license` and `platform` fields; repository GPLv3, content licensed per entry)
- cgb-acid2: https://github.com/mattcurrie/cgb-acid2 ; dmg-acid2: https://github.com/mattcurrie/dmg-acid2 ; mgblib: https://github.com/mattcurrie/mgblib ; Mealybug Tearoom: https://github.com/mattcurrie/mealybug-tearoom-tests
- gbmicrotest: https://github.com/aappleby/gbmicrotest ; GateBoy: https://github.com/aappleby/metroboy
- SameSuite: https://github.com/LIJI32/SameSuite ; SameBoy and BESS: https://github.com/LIJI32/SameBoy/blob/master/BESS.md ; Mooneye: https://github.com/Gekkio/mooneye-test-suite ; Gambatte: https://github.com/sinamas/gambatte (hwtests, GPL-2)
- µCity: https://github.com/AntonioND/ucity , https://codeberg.org/SkyLyrac/ucity ; Geometrix: https://github.com/AntonioND/geometrix ; gbhack: https://github.com/statico/gbhack ; Potion Panic: https://codeberg.org/DevEd/potion-panic/src/branch/gbcompo25 ; Aevilia: https://github.com/ISSOtm/Aevilia-GB ; Tobu Tobu Girl DX: https://github.com/SimonLarsen/tobutobugirl-dx ; Shock Lobster: https://github.com/tbsp/shock-lobster ; Rebound: https://github.com/DevEd2/Rebound
- GBDK-2020 runtime licence (GPLv2 with linking exception): https://github.com/gbdk-2020/gbdk-2020/tree/develop/licenses
- Local: Playstead `.planning/ROADMAP.md` Phase 4.6, `.planning/spikes/GB-GBC-REPORT.md`, `PRODUCT.md` (sibling; read only)
