# Phase 22: Composition and Microtest Evidence — Research

**Researched:** 2026-11-02  
**Domain:** Game Boy diagnostic fixtures, image comparison, fixture provenance and test accounting  
**Confidence:** MEDIUM

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

### Acid2 derivatives and independent image oracle

- **D-01: Build both derivatives from pinned upstream source and preserve the upstream image as the pass/fail reference.** Use `dmg-acid2` v1.0 and `cgb-acid2` v1.1 as the current source candidates, resolve and pin immutable source/submodule commits, patch/build inputs, toolchain, resulting ROM bytes, and upstream reference-image bytes. Reuse the project's existing RGBDS reproduction pin where it applies. The current `tests/acid2/manifest.json` only records upstream ROM/reference identities and explicitly keeps those files out of the repository while the `mgblib` font rights gate is open.
- Replace the upstream font data with original project-authored glyphs. Do not copy or retain the `mgblib` font in the derivative. Record the replacement glyph source and identity. Review rights for upstream code, all remaining art, reference images, build tools, and the derivative separately under Phase 20; font replacement alone does not clear those gates.
- Compare the derivative against the unchanged upstream reference using the documented DMG shade mapping and CGB RGB555 expansion. The reference must not be generated from GabbaBoy output. A second emulator may inform investigation, but is not the pass/fail oracle. Do not add a source-derived PPU renderer for this phase; testing replacement-glyph rendering would require a separately scoped independent expectation.
- Label the result as controlled composition evidence. The upstream CGB test explicitly says it is not a mode-3 timing torture test, and the mask excludes glyph rendering from this comparison.

### Text mask scope and validation

- **D-02: Define the mask from the pinned source's text tile layout.** Keep a readable allowlist of only the text tile cells affected by the replacement, mapped to fixed screen coordinates. Generate a fixed-size mask and a reviewable overlay from that allowlist. Include each displayed text area affected by substitution, including the greeting and footer when present; do not mask adjacent anatomy, background, or other composition.
- Pin the allowlist, generated mask identity, and the source/layout identity used to derive coordinates. Enforce a bounded masked area and a minimum unmasked comparison area. Compare every remaining pixel exactly; do not use a tolerance that could hide unrelated differences.
- The mask intentionally makes text pixels outside the comparison claim. Check replacement-glyph source and identity separately. Automated controls must reject an altered/broadened mask and still detect a one-pixel mismatch outside the mask; changed ROM/reference/mask identities must not silently pass.

### gbmicrotest cohort, model applicability, and accounting

- **D-03: Start from one immutable upstream inventory and keep exclusions visible.** Use upstream `aappleby/gbmicrotest` commit `463eb6bc0fe31d61781ef63060ad6d74090c0255` as the candidate inventory. Scouting found 513 source/ROM pairs at that revision; retain all names in the roster. The 482 cases using the shared verdict protocol are the initial runnable candidates. Keep the other 31 explicitly excluded unless a case-specific independent oracle is reviewed. Planning must verify the inventory and counts against the pinned commit before implementation.
- Bind every case to its exact source path/commit, ROM path/size/digest, redistribution evidence, expected-result protocol, and declared applicability. The upstream README makes a suite-wide, uncertain DMG-CPU-08 hardware claim; it does not provide per-case revision qualification. Record that upstream reference model separately from GabbaBoy's execution profile. A DMG-CPU-B run may be reported as a cross-model diagnostic, never as CPU-B hardware qualification. Do not infer CGB-CPU-E applicability; a case needs source-backed evidence for any additional profile or it remains excluded with a reason.
- The MIT file is not by itself proof that generated ROM bytes or every embedded component are covered. Review the exact source and binary scope, including the shared `.nintendologo` header directive, under Phase 20's component-rights rules. The upstream build script does not pin WLA-DX; do not claim reproducible ROM builds unless the assembler/build closure is pinned and verified. Exact prebuilt ROM identities may be recorded separately from any build claim.
- Require complete, disjoint eligible/executed/excluded case sets. Every eligible case must execute; every exclusion must name a concrete rights, oracle, or applicability reason. Missing, duplicated, reclassified, or unexecuted required cases fail the suite accounting. Add negative controls for altered source/ROM identity, incorrect applicability, dropped/duplicated cases, unexplained exclusion, and missing execution.
- If rights or model applicability cannot be established, do not imply successful fixture admission by running a partial or relabeled suite. Record the blocker and trigger scope resolution.

### the agent's Discretion

- Preserve Phase 20's fixture manifests, notices, source-archive/binary-product separation, and package exclusions. Keep original authored code under the existing MIT license; third-party terms remain separate.
- Prefer existing CMake/CTest and Python standard-library tooling. Do not add a dependency unless research demonstrates a need that the existing tools cannot meet.
- The owner asked for parallel, role-relevant analysis, primary sources where useful, an adversarial pass, and automatic adoption of the coherent recommendation. The areas discussed were the independent acid2 oracle, text-mask scope, and microtest cohort/accounting; the decisions above apply that instruction.
- The implementation may choose manifest field names, checker organization, exact mask encoding/overlay generation, and plan decomposition within the 10-plan cap, provided the invariants above remain automated and include meaningful negative controls.

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within Phase 22 scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| RIGHTS-01 | An admitted game or diagnostic fixture has verified redistribution permission for repository and public-CI use, with per-component code, art, audio-driver, build-input, and notice terms recorded; game ROMs are excluded from installed and product-release packages, and GabbaBoy's root MIT license remains unchanged. | Apply the existing Phase 20 admission and package checks; record each relevant component and its terms separately; keep rights adjudication separate from byte identity. |
| DIAG-01 | The admitted dmg-acid2 and cgb-acid2 derivatives replace glyph tiles and mask the text region, with source/build provenance and rights recorded; their evidence is labeled as controlled composition, not mode-3 timing. | Preserve upstream image bytes as independent expectations; pin derivative build inputs and output; source-anchor the glyph-cell allowlist and check exact unmasked pixels. |
| DIAG-02 | Each admitted gbmicrotest case is tied to exact source and bytes, redistribution terms, and declared model applicability; suite results retain explicit eligible, executed, and excluded cases. | Bind case rows to commit, source and ROM digests, component rights, protocol and model; verify full roster and execution/exclusion accounting against the immutable upstream inventory. |
</phase_requirements>

## Summary

Build Phase 22 around two repository-local evidence pipelines: extend the existing acid2 runner/manifest for font-substituted derivatives and an explicit text mask, and add a source-bound gbmicrotest inventory/accounting checker. Keep both on Python's standard library plus existing CMake/CTest; the repository already uses those tools for fixture admission, package exclusion, synthetic negative controls and corpus accounting. No new package is justified by the reviewed needs. [VERIFIED: `tests/scripts/run-acid2-local.py:1-6`, `tests/scripts/verify-fixture-admission.py:1-23`, `tests/CMakeLists.txt:1355-1370`]

The source inspection confirms the pinned upstream candidates and composition are implementable, but admission has real gates: acid2's `mgblib` font and other components need separate rights decisions, and gbmicrotest's broad uncertain DMG-CPU-08 claim does not establish per-case silicon applicability. Its build script asks for WLA-DX but gives no version pin. Exact ROM digests can identify bytes without proving permission or a reproducible build. If those gates remain open, record the blockers and request scope resolution instead of labeling a partial or relabeled cohort as admitted. [CITED: https://github.com/mattcurrie/dmg-acid2/blob/v1.0/Makefile; https://github.com/mattcurrie/cgb-acid2/blob/v1.1/Makefile; https://github.com/aappleby/gbmicrotest/blob/463eb6bc0fe31d61781ef63060ad6d74090c0255/README.md; https://github.com/aappleby/gbmicrotest/blob/463eb6bc0fe31d61781ef63060ad6d74090c0255/build.sh]

**Primary recommendation:** First verify the source roster and independently pin all inputs; then implement immutable manifest checks and synthetic negative controls; only execute or admit fixtures after Phase 20's component-rights and model applicability gates have evidence. Use upstream acid2 images unchanged as the only pass/fail reference, mask only source-mapped substituted text cells, and keep all remaining pixels exact. [VERIFIED: `.planning/phases/GB-22-composition-and-microtest-evidence/22-CONTEXT.md:22-39`; `tests/scripts/run-acid2-local.py:168-172`]

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Fixture provenance and rights records | Repository test tooling | Notices/package policy | Manifests bind source and bytes; admission and package checkers already validate provenance and exclude controlled fixture bytes from binary products. [VERIFIED: `tests/scripts/verify-fixture-admission.py:1-3,26-61`; `cmake/ScanForbiddenFixtures.cmake:1-7`] |
| Acid2 capture and masked image comparison | Test harness / host adapter | Emulator runner | Existing Python harness validates pinned ROM/reference bytes, calls the runner, decodes bounded images and compares pixels; it is optional locally and synthetic-only in required CI today. [VERIFIED: `tests/scripts/run-acid2-local.py:1-6,32-53,168-192`; `tests/CMakeLists.txt:3652-3656`] |
| gbmicrotest case applicability and accounting | Repository test tooling | Emulator runner / CTest | A source-bound inventory checker should decide eligibility and accounting; named CTest execution records actual run outcomes separately from model and rights evidence. Existing CGB corpus patterns provide precedent. [VERIFIED: `tests/scripts/verify-cgb-corpus-inventory.py:120-155`; `tests/CMakeLists.txt:1355-1370`] |
| Installed and release package boundary | Build/package policy | Fixture manifest | Reuse actual-tree scans keyed by forbidden path and exact byte identity, then bind the new records to existing notices and product policy. [VERIFIED: `cmake/ScanForbiddenFixtures.cmake:3-7,62-93`] |

## Standard Stack

### Core

| Tool | Version | Purpose | Why Standard |
|------|---------|---------|--------------|
| Python standard library | Use repository's discovered Python interpreter; local research environment is Python 3.14.4. | Bounded JSON/source validation, SHA-256 identity, mask generation, image comparison, synthetic mutation controls. | The acid2 runner, fixture admission and CGB corpus verifier already use only standard-library code. [VERIFIED: `tests/scripts/run-acid2-local.py:8-18`; `tests/scripts/verify-fixture-admission.py:4-23`; `tests/scripts/verify-cgb-corpus-inventory.py:3-13`] |
| CMake + CTest | Repository uses CMake 3.25-compatible primitives; local tools are CMake/CTest 4.4.3. | Register all new checker/self-tests and package-policy checks in the existing test workflow. | Existing corpus and acid2 controls are registered with `add_test`; the forbidden-fixture scanner states its minimum as CMake 3.25. [VERIFIED: `cmake/ScanForbiddenFixtures.cmake:21-22`; `tests/CMakeLists.txt:1355-1370,3652-3670`] |
| RGBDS | Existing project reproduction pin is 1.0.1; use only if the acid2 source builds with that pinned release and the build is verified. | Rebuild DMG/CGB acid2 derivative ROMs from source. | Acid2 Makefiles call RGBDS tools. The repository's existing AGE reproducer pins RGBDS archives and checks each executable's version. Compatibility and output identity for these acid2 revisions remain to be verified; the pin itself is not proof. [CITED: https://github.com/mattcurrie/dmg-acid2/blob/v1.0/Makefile; https://github.com/mattcurrie/cgb-acid2/blob/v1.1/Makefile] [VERIFIED: `tests/scripts/reproduce-age.sh:56-63,314-320`] |

### Supporting

| Tool | Version | Purpose | When to Use |
|------|---------|---------|-------------|
| SHA-256 from `hashlib` | Python standard library | Fingerprint source, ROM, reference, glyph source, allowlist, generated mask and overlay bytes. | Use for stable byte identity only; do not treat a digest as a rights grant or model claim. The existing checker uses `hashlib.sha256(data).hexdigest()`. [VERIFIED: `tests/scripts/verify-fixture-admission.py:70-72`] [CITED: https://docs.python.org/3.14/library/hashlib.html] |
| Git immutable commits/tree IDs | Installed Git; upstream commit values are fixed in the locked context. | Bind source files and generated candidate inventory to reviewed source snapshots. | Use Git tree/blob identities plus per-ROM digests. Do not use branch names or a moving default branch as the identity. [VERIFIED: `.planning/phases/GB-22-composition-and-microtest-evidence/22-CONTEXT.md:22,35-38`] |

### Verified Upstream Identities

The existing manifest's exact upstream release pins are:

```text
    "cgb-acid2": {
      "repository": "https://github.com/mattcurrie/cgb-acid2",
      "release_tag": "v1.1",
      "licence": "MIT License",
      "rom_url": "https://github.com/mattcurrie/cgb-acid2/releases/download/v1.1/cgb-acid2.gbc",
      "rom_asset": "cgb-acid2.gbc",
      "rom_size": 32768,
      "rom_sha256": "197fb0bcec544f0400527fc707e0a94f55435974986e6986b424ace5de81720e",
      "reference_url": "https://raw.githubusercontent.com/mattcurrie/cgb-acid2/v1.1/img/reference.png",
      "reference_asset": "img/reference.png",
      "reference_sha256": "9ea9c262c5383353e77d715d021a0f7c5ccbe438f88082cb225756e50c4fdf01",
      "profile": "CGB-CPU-E",
      "runner_model": "cgb-cpu-e",
      "comparison": "RGB555 frame expanded per channel with (c << 3) | (c >> 2), as the upstream README prescribes",
      "comparison_source": "https://github.com/mattcurrie/cgb-acid2/blob/v1.1/README.md"
    },
    "dmg-acid2": {
      "repository": "https://github.com/mattcurrie/dmg-acid2",
      "release_tag": "v1.0",
      "licence": "MIT License",
      "rom_url": "https://github.com/mattcurrie/dmg-acid2/releases/download/v1.0/dmg-acid2.gb",
      "rom_asset": "dmg-acid2.gb",
      "rom_size": 32768,
      "rom_sha256": "464e14b7d42e7feea0b7ede42be7071dc88913f75b9ffa444299424b63d1dff1",
      "reference_url": "https://raw.githubusercontent.com/mattcurrie/dmg-acid2/v1.0/img/reference-dmg.png",
      "reference_asset": "img/reference-dmg.png",
      "reference_sha256": "ca966d50895c7efef05838590d148c2cbfd7fba57dab986f25b35b4da71abb57",
      "profile": "DMG-CPU-B",
      "runner_model": "dmg-cpu-b",
      "comparison": "DMG shades mapped to greyscale 255, 170, 85, 0 for shades 0 to 3 (the upstream values $FF, $AA, $55, $00)",
      "comparison_source": "https://github.com/mattcurrie/dmg-acid2/blob/v1.0/README.md"
    }
```

[VERIFIED: `tests/acid2/manifest.json:7-37`]

Directly fetched release ROM bytes and reference files matched those four manifest digests: each ROM is 32,768 bytes; `img/reference.png` is 870 bytes and `img/reference-dmg.png` is 787 bytes; both references are 160×144. These are upstream release/reference identities, not derivative build identities or rights evidence. [VERIFIED: direct SHA-256, byte-size and image-header checks against the pinned upstream release assets; manifest quote above]

The `dmg-acid2` v1.0 tag resolves to `dc2295408f881637ff69f784d8d93f3d2db30181`; `cgb-acid2` v1.1 resolves to `fa5b7f86d6fb599f79e55169494d981a7af75a31`; both source trees point to `mgblib` commit `5d829bf2ffa1447dcfd63c5dab2c44488632617e`. Git tags/source trees and reference assets were fetched directly from their upstream repositories. Record these immutable commits and submodule commit in derivative build provenance, while retaining the locked source candidates/tags. [VERIFIED: direct upstream Git tag and gitlink inspection; https://github.com/mattcurrie/dmg-acid2/tree/v1.0; https://github.com/mattcurrie/cgb-acid2/tree/v1.1]

The upstream acid2 Makefiles convert `img/footer.png` with `rgbgfx`, assemble sources with RGBDS, link and fix ROM headers; font data comes from the `mgblib` submodule. Replace the font source with original glyph bytes, but separately track rights for remaining source, footer/reference art, build tools and derivatives. [CITED: https://github.com/mattcurrie/dmg-acid2/blob/v1.0/Makefile; https://github.com/mattcurrie/dmg-acid2/tree/v1.0/mgblib; https://github.com/mattcurrie/cgb-acid2/blob/v1.1/Makefile; https://github.com/mattcurrie/cgb-acid2/tree/v1.1/mgblib]

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Python stdlib + existing CTest | A new image-processing or schema-validation dependency | No reviewed need requires a dependency; adding one expands package/security surface and complicates reproducible CI. [VERIFIED: `tests/scripts/run-acid2-local.py:8-18`; `AGENTS.md:47-53`] |
| Pinned upstream acid2 image | A golden frame captured from GabbaBoy or a second emulator | This would make expected output depend on the implementation under test or an unqualified second model; the locked decision requires the unchanged upstream image as pass/fail oracle. [VERIFIED: `.planning/phases/GB-22-composition-and-microtest-evidence/22-CONTEXT.md:22-25`] |
| Explicit source-cell mask | A broad rectangle or image tolerance | A broad mask can hide unrelated composition defects; tolerance can hide unmasked pixel differences. [VERIFIED: `.planning/phases/GB-22-composition-and-microtest-evidence/22-CONTEXT.md:29-31`] |

**Installation:** None. Do not add packages. Use installed Python, CMake/CTest, the repository's existing RGBDS pin where applicable, and upstream prebuilt ROM identities only if their rights are cleared. [VERIFIED: `.planning/phases/GB-22-composition-and-microtest-evidence/22-CONTEXT.md:43-46`]

## Package Legitimacy Audit

Not applicable: this phase should install no external package. Python standard library, CMake/CTest, Git and the existing project-pinned RGBDS toolchain are already in scope; WLA-DX is not to be added as an unpinned reproducible-build dependency. [VERIFIED: `.planning/phases/GB-22-composition-and-microtest-evidence/22-CONTEXT.md:43-46`; `tests/scripts/reproduce-age.sh:56-63`]

## Architecture Patterns

### System Architecture Diagram

```text
Pinned upstream source/commit ─┐
Pinned source/build inputs ─────┼─> rights + identity manifest ──┬─> admission / package checks
Pinned ROM/reference bytes ─────┘                               │
                                                                └─> acid2 runner -> bounded frame decode
                                                                    -> source-cell mask
                                                                    -> exact unmasked comparison
                                                                    -> controlled composition report

Pinned gbmicrotest tree ────────> complete case roster ──> rights + protocol + model classification
Pinned ROM identities ───────────────────────────────────> eligible/executed/excluded accounting
                                                           -> named CTest cases / cohort report

Synthetic fixture/reference/mask/accounting mutants ───────> negative controls -> CTest
```

The flow extends the existing local acid2 runner and admission/package controls; it does not place fixture policy inside the emulator core. [VERIFIED: `tests/scripts/run-acid2-local.py:32-53,175-192`; `tests/scripts/verify-fixture-admission.py:1-3`; `cmake/ScanForbiddenFixtures.cmake:1-7`]

### Recommended Project Structure

Follow the existing repository seams rather than create a parallel framework. [VERIFIED: `.planning/phases/GB-22-composition-and-microtest-evidence/22-CONTEXT.md:68-72`]

```text
tests/
├── acid2/                         # Derivative manifest, source-cell allowlist, generated mask/overlay if admitted
├── external/                      # Pinned gbmicrotest inventory and rights/applicability records
├── scripts/                       # Bounded source, identity, mask, accounting, and self-test checkers
└── CMakeLists.txt                 # CTest wiring for all checkers and negative controls
cmake/
└── ScanForbiddenFixtures.cmake    # Extend actual product-tree scans for admitted ROM/reference identities
THIRD_PARTY_NOTICES.md             # Component terms and exact admitted identities
```

Treat paths above as recommendations from the locked integration points, not new schema constants. [VERIFIED: `.planning/phases/GB-22-composition-and-microtest-evidence/22-CONTEXT.md:68-72,97-100`]

### Pattern 1: Source-Anchored Acid2 Mask

**What:** Keep a readable list of text tile cells and their fixed on-screen cell coordinates derived from the pinned source/layout. Generate a fixed-size mask and a reviewable overlay; hash the source/layout identity, allowlist, mask, overlay, ROM and unchanged upstream image. Apply established DMG shade mapping or CGB RGB555 expansion, then compare every unmasked pixel exactly. [VERIFIED: `.planning/phases/GB-22-composition-and-microtest-evidence/22-CONTEXT.md:29-31`; `tests/acid2/manifest.json:7-37`; `tests/scripts/run-acid2-local.py:168-172`]

Acid2 references use a 160×144 image; the existing parser already fixes that shape and has bounded PNG input. [VERIFIED: `tests/scripts/run-acid2-local.py:20-25,78-103`]

The upstream source shows the greeting in object tiles and the footer in the map; generate the exact allowlist from both source/layout paths and include only cells whose glyph bytes are replaced. Review overlay and allowlist as generated artifacts; the mask must not include anatomy, background, or adjacent text-independent composition. [CITED: https://github.com/mattcurrie/dmg-acid2/blob/v1.0/src/dmg-acid2.asm; https://github.com/mattcurrie/dmg-acid2/blob/v1.0/inc/oam.asm; https://github.com/mattcurrie/dmg-acid2/blob/v1.0/inc/window.asm; https://github.com/mattcurrie/cgb-acid2/blob/v1.1/src/cgb-acid2.asm; https://github.com/mattcurrie/cgb-acid2/blob/v1.1/inc/oam.asm; https://github.com/mattcurrie/cgb-acid2/blob/v1.1/inc/window.asm]

The upstream README specifies DMG grayscale mapping and CGB RGB555 channel expansion; both also state that acid2 is not a mode-3 timing torture test. Keep the resulting evidence label at controlled composition. [CITED: https://github.com/mattcurrie/dmg-acid2/blob/v1.0/README.md; https://github.com/mattcurrie/cgb-acid2/blob/v1.1/README.md]

### Pattern 2: Case Inventory With Separate Evidence Dimensions

**What:** Bind every case to the immutable source path and commit, ROM path/size/SHA-256, expected-result protocol, component-rights decision/evidence, upstream reference-model statement, GabbaBoy execution profile and terminal accounting outcome. Verify the roster against the upstream tree and compare complete normalized inventories, not counts alone. [VERIFIED: `.planning/phases/GB-22-composition-and-microtest-evidence/22-CONTEXT.md:35-39`; `tests/scripts/verify-cgb-corpus-inventory.py:120-155`]

The upstream checkout at the locked commit contains 513 matching `.s`/`.gb` pairs. Direct inspection found 480 sources using the shared macros, two MBC1 cases with inline FF80–FF82 pass/fail output, and 31 cases with neither protocol; therefore 482 are initial protocol candidates and 31 are initial exclusions. The 31 source names are: `000-oam_lock.s`, `000-write_to_x8000.s`, `001-vram_unlocked.s`, `002-vram_locked.s`, `004-tima_boot_phase.s`, `004-tima_cycle_timer.s`, `007-lcd_on_stat.s`, `400-dma.s`, `500-scx-timing.s`, `800-ppu-latch-scx.s`, `801-ppu-latch-scy.s`, `802-ppu-latch-tileselect.s`, `803-ppu-latch-bgdisplay.s`, `audio_testbench.s`, `cpu_bus_1.s`, `dma_basic.s`, `flood_vram.s`, `lcdon_write_timing.s`, `ly_while_lcd_off.s`, `minimal.s`, `mode2_stat_int_to_oam_unlock.s`, `oam_sprite_trashing.s`, `poweron.s`, `ppu_scx_vs_bgp.s`, `ppu_sprite_testbench.s`, `ppu_spritex_vs_scx.s`, `ppu_win_vs_wx.s`, `ppu_wx_early.s`, `temp.s`, `toggle_lcdc.s`, and `wave_write_to_0xC003.s`. Treat the two MBC1 programs as independently structured verdicts, not shared-macro use; verify the inventory and candidate list again in implementation before pinning it. [VERIFIED: direct checkout of `https://github.com/aappleby/gbmicrotest/tree/463eb6bc0fe31d61781ef63060ad6d74090c0255/tests`; `tests/macros.inc:266-313` at that checkout; `tests/mbc1_ram_banks.s`; `tests/mbc1_rom_banks.s`]

**Accounting interpretation to resolve in planning:** eligibility is a property/selection decision, while execution is an event and can only be a subset of eligible cases. For each roster entry, model eligibility and execution separately, with a terminal disposition of executed or excluded; require every eligible case to execute and every exclusion to carry a specific reason. A checker cannot require the `eligible` set and `executed` set to be mutually disjoint while also requiring every eligible case to execute. This appears to be a wording conflict in D-03; preserve both the complete accounting and the execution requirement, and make the representation explicit in the plan rather than silently encoding an impossible set rule. [VERIFIED: `.planning/phases/GB-22-composition-and-microtest-evidence/22-CONTEXT.md:38`; `tests/scripts/verify-cgb-corpus-inventory.py:130-155`]

The upstream README says the cases were checked on real hardware and adds “I believe” to the DMG-CPU-08 revision. Treat this as an uncertain suite-wide author statement; it does not provide case-by-case silicon qualification. Keep it distinct from GabbaBoy's selected profile and do not infer CPU-B hardware or CGB-CPU-E validity. [CITED: https://github.com/aappleby/gbmicrotest/blob/463eb6bc0fe31d61781ef63060ad6d74090c0255/README.md]

The two MBC1 source files encode their result inline; for every initially eligible row, the plan should specify a protocol/source review criterion rather than infer protocol membership from a macro-name grep. [VERIFIED: upstream pinned `tests/mbc1_ram_banks.s` and `tests/mbc1_rom_banks.s`; pinned `tests/macros.inc:266-313`]

### Anti-Patterns to Avoid

- **Generating expected images from GabbaBoy:** creates a self-confirming oracle; use the unchanged upstream reference. [VERIFIED: `.planning/phases/GB-22-composition-and-microtest-evidence/22-CONTEXT.md:22-25`]
- **Masking a large rectangle or applying a color tolerance:** can hide unrelated changes; derive only the text cells and compare all remaining pixels exactly. [VERIFIED: `.planning/phases/GB-22-composition-and-microtest-evidence/22-CONTEXT.md:29-31`]
- **Treating “MIT” or SHA-256 as admission:** a license label and digest establish neither grant scope/authority nor model applicability. Record the terms per component and request scope resolution when unresolved. [VERIFIED: `.planning/phases/GB-22-composition-and-microtest-evidence/22-CONTEXT.md:23,35-39`; `tests/scripts/verify-fixture-admission.py:35-42`]
- **Claiming WLA-DX reproducibility from a build script that only says to install it:** no assembler version or closure is pinned upstream. Pin and verify the assembler/build closure first; otherwise report exact prebuilt ROM identities without a build-reproducibility claim. [CITED: https://github.com/aappleby/gbmicrotest/blob/463eb6bc0fe31d61781ef63060ad6d74090c0255/build.sh; https://github.com/aappleby/gbmicrotest/blob/463eb6bc0fe31d61781ef63060ad6d74090c0255/README.md]
- **Inferring hardware qualification from cross-model runs:** DMG-CPU-B results for the suite may be diagnostic comparisons only; no physical CGB-E or mode-3 claim follows. [VERIFIED: `.planning/phases/GB-22-composition-and-microtest-evidence/22-CONTEXT.md:25,36`; `.planning/ROADMAP.md:103-109`]
- **Counting tests without binding names:** equal totals can conceal dropped/replaced cases. Pin the complete roster and negative-test deletion, duplication, reclassification and missing execution. [VERIFIED: `.planning/phases/GB-22-composition-and-microtest-evidence/22-CONTEXT.md:35,38`; `tests/scripts/verify-cgb-corpus-inventory.py:157-180`]

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|------------|-------------|-----|
| Image decoding/comparison | A new image library, perceptual score or tolerance comparator | Extend `run-acid2-local.py`'s bounded standard-library PNG/PPM parser and exact comparison, adding mask semantics. | Existing code already checks dimensions, bounds input and compares all pixels exactly. [VERIFIED: `tests/scripts/run-acid2-local.py:20-25,56-103,168-172`] |
| Fixture admission and product exclusion | Another generic rights registry or a path-only package check | Extend Phase 20 manifests/notices and `ScanForbiddenFixtures.cmake` actual-tree byte/path scan. | Current policy binds exact bytes and checks actual product trees; reuse avoids divergent gates. [VERIFIED: `.planning/phases/GB-22-composition-and-microtest-evidence/22-CONTEXT.md:43`; `cmake/ScanForbiddenFixtures.cmake:1-7,62-93`] |
| Case corpus accounting | Ad hoc counts or CTest skips as exclusions | Source-bound inventory checker and explicit disposition/reason rows; register its self-tests in CTest. | Existing CGB verifier validates tree pins, full rosters, counts, case identities and applicability. [VERIFIED: `tests/scripts/verify-cgb-corpus-inventory.py:120-180`; `tests/CMakeLists.txt:1355-1370`] |
| Hashes/rights decisions | Custom cryptography or deriving permission from a digest | `hashlib.sha256` for fingerprints; per-component terms and separate rights adjudication. | Hashes are byte identity. The existing fixture notice itself says package identity checks do not decide whether the grantor had authority. [VERIFIED: `tests/scripts/verify-fixture-admission.py:35-42,70-72`] |

**Key insight:** Keep independent concerns in separate fields and checks: identity, rights, build reproducibility, expected-result protocol and applicability answer different questions. A digest can validate one of these (identity) and must not be allowed to clear the others. [VERIFIED: `.planning/phases/GB-22-composition-and-microtest-evidence/22-CONTEXT.md:23,35-39`; `tests/scripts/verify-fixture-admission.py:35-42`]

## Common Pitfalls

### Pitfall 1: A reference pin is mistaken for a right to redistribute

**What goes wrong:** A source tag, ROM/reference hash or suite-wide MIT label is treated as sufficient permission to copy source, generated ROMs, images or embedded assets.  
**Why it happens:** Identity records are easy to automate while grant scope and authority require separate evidence.  
**How to avoid:** Record per-component code, art, audio driver, build inputs and notices under Phase 20; separately review source and output/binary scope, including `.nintendologo` and acid2 `mgblib`/footer assets; preserve package scans.  
**Warning signs:** A fixture is called admitted with a blank rights component or only a suite-wide `MIT` label. [VERIFIED: `.planning/phases/GB-22-composition-and-microtest-evidence/22-CONTEXT.md:23,37,43`; `tests/scripts/verify-fixture-admission.py:26-61`]

### Pitfall 2: Mask shape drifts away from the replacement glyph cells

**What goes wrong:** A mask includes unrelated picture area or hides a mismatch because it was regenerated from an unpinned layout.  
**Why it happens:** A hand-edited rectangle is simpler than deriving screen cells from object/background/window layout.  
**How to avoid:** Pin source/layout and the readable cell allowlist; regenerate a fixed-size bitmap and overlay; bound masked pixels and minimum compared pixels; check a one-pixel mismatch outside the mask plus altered/broadened masks and identities.  
**Warning signs:** The mask is accepted after its digest changes, or the negative control mutates only a pixel that is supposed to be masked. [VERIFIED: `.planning/phases/GB-22-composition-and-microtest-evidence/22-CONTEXT.md:29-31`]

### Pitfall 3: Suite counts conceal missing or misclassified cases

**What goes wrong:** A total of 482 eligible candidates is reported while names disappear, an excluded case has no reason, or a required case never executed.  
**Why it happens:** Aggregate counts are easier to compare than source-bound case identities and output accounting.  
**How to avoid:** Verify the pinned commit roster, stable case identifiers and ROM digests; require per-case explicit disposition and make missing, duplicate, changed-model, unexplained-exclusion and not-executed mutants fail.  
**Warning signs:** Exclusions exist only as skipped CTests or the report includes totals without case IDs. [VERIFIED: `.planning/phases/GB-22-composition-and-microtest-evidence/22-CONTEXT.md:35-39`; `tests/scripts/verify-cgb-corpus-inventory.py:130-180`]

### Pitfall 4: Upstream model or build wording is stronger than its evidence

**What goes wrong:** The uncertain suite-wide CPU-08 note becomes a claim for each test, a CPU-B software run becomes CPU-B hardware qualification, or an unpinned WLA build is called reproducible.  
**Why it happens:** README-level shorthand obscures per-case/model differences and build-tool provenance.  
**How to avoid:** Carry upstream reference model and GabbaBoy execution profile in separate columns, require case-specific evidence for additional profiles, and distinguish prebuilt ROM hash identity from reproducible source-build evidence.  
**Warning signs:** An evidence label says “hardware pass,” “CGB-E qualified,” or “reproducible” without the corresponding source/build record. [CITED: https://github.com/aappleby/gbmicrotest/blob/463eb6bc0fe31d61781ef63060ad6d74090c0255/README.md; https://github.com/aappleby/gbmicrotest/blob/463eb6bc0fe31d61781ef63060ad6d74090c0255/build.sh] [VERIFIED: `.planning/phases/GB-22-composition-and-microtest-evidence/22-CONTEXT.md:36-39`]

## Code Examples

### Case Accounting Check

Model eligibility and execution as linked facts, then require every eligible row to execute and every non-eligible row to have a specific exclusion reason. This sketch is illustrative; phase planning should choose exact fields while retaining the locked invariants. [VERIFIED: `.planning/phases/GB-22-composition-and-microtest-evidence/22-CONTEXT.md:35-39`]

```python
def validate_case_accounting(roster, eligible_ids, executed_ids, exclusions):
    all_ids = {row["id"] for row in roster}
    assert len(all_ids) == len(roster)                 # no duplicate case identity
    assert eligible_ids <= all_ids
    assert executed_ids <= eligible_ids                # no execution outside eligibility
    assert set(exclusions) == all_ids - eligible_ids   # every excluded case is named
    assert eligible_ids <= executed_ids                # no eligible case is missing
    assert all(exclusions[case_id] for case_id in exclusions)
```

The illustrative `id` field spelling follows the existing corpus checker, which states `need(row["id"] not in source_by_id, "duplicate-source-id")`. [VERIFIED: `tests/scripts/verify-cgb-corpus-inventory.py:141-155`]

The invariant set above intentionally does not assert `eligible_ids.isdisjoint(executed_ids)`: that would contradict the requirement that every eligible case execute. Make this semantic resolution explicit in the plan. [VERIFIED: `.planning/phases/GB-22-composition-and-microtest-evidence/22-CONTEXT.md:38`]

### Masked Exact Comparison

Extend the existing exact comparator so the mask decides which pixels are outside the comparison claim; do not change colors with tolerances or make expected pixels from the emulated output. Require bounds and identity checks before this loop. [VERIFIED: `tests/scripts/run-acid2-local.py:168-172`; `.planning/phases/GB-22-composition-and-microtest-evidence/22-CONTEXT.md:22-31`]

```python
def compare_unmasked(actual, reference, mask):
    assert len(actual) == len(reference) == len(mask)
    differing = sum(
        1 for got, want, masked in zip(actual, reference, mask)
        if not masked and got != want
    )
    return differing == 0, differing
```

Each new checker must have at least one meaningful negative control and be registered with CTest, per project rule D-069. [VERIFIED: `AGENTS.md:27-43`; `tests/CMakeLists.txt:1355-1370,3652-3670`]

## State of the Art

| Existing Approach | Phase 22 Extension | Impact |
|--------------------|--------------------|--------|
| Acid2 runner pins a release ROM/reference and compares every pixel. [VERIFIED: `tests/scripts/run-acid2-local.py:32-53,168-172`] | Add derivative source/build/rights identities, source-derived mask allowlist/overlay, mask identity, masked area bound and out-of-mask negative control. [VERIFIED: `.planning/phases/GB-22-composition-and-microtest-evidence/22-CONTEXT.md:22-31`] | Keeps the upstream image independent while explicitly excluding replacement glyph rendering from the composition claim. |
| Existing CGB corpus verifier checks immutable source trees, applicability and complete named rows. [VERIFIED: `tests/scripts/verify-cgb-corpus-inventory.py:120-180`] | Apply the pattern to the pinned gbmicrotest cohort and distinguish eligibility, execution, exclusion and model evidence. [VERIFIED: `.planning/phases/GB-22-composition-and-microtest-evidence/22-CONTEXT.md:35-39`] | Missing, duplicated or unexplained cases become machine-detectable. |
| Existing product checks exclude controlled fixtures by path and exact bytes. [VERIFIED: `cmake/ScanForbiddenFixtures.cmake:3-7,62-93`] | Include admitted diagnostic ROM/reference bytes and preserve source archive vs binary product separation. [VERIFIED: `.planning/phases/GB-22-composition-and-microtest-evidence/22-CONTEXT.md:43`] | Fixture admission does not accidentally place ROM bytes in installed products. |

**Deprecated/outdated:** Do not extend release-only acid2 pins into claims of derivative reproducibility; the current manifest explicitly has no ROM or image bytes in the repo and records only upstream identities. Do not use the current all-pixel comparator unchanged as proof once text replacement causes an expected text difference. [VERIFIED: `tests/acid2/manifest.json:2-5,7-37`; `tests/scripts/run-acid2-local.py:168-172`]

## Project Constraints (from AGENTS.md)

- Target evidence is Game Boy and Game Boy Color only; do not import unrelated emulator examples or claim an unimplemented capability. [VERIFIED: `AGENTS.md:23-24`]
- Keep emulator code portable and direct; host tools and filesystem policy belong in adapters/test tooling. Preserve explicit ownership/error behavior and bounded file sizes, paths, subprocess time and work. [VERIFIED: `AGENTS.md:47-53`; `tests/scripts/verify-fixture-admission.py:44-60`]
- Do not add Nintendo boot ROMs, commercial game images, unlicensed homebrew or private data. Every third-party fixture needs a digest and documented redistribution rights. Keep diagnostic ROMs out of installed/binary products while rights are unresolved. [VERIFIED: `AGENTS.md:51-53`; `.planning/phases/GB-22-composition-and-microtest-evidence/22-CONTEXT.md:11,43`]
- Every deliverable needs an automated check with a meaningful negative control; wire checkers into CTest and place them in `tests/scripts/`. Check immutable commits, not live branch state. [VERIFIED: `AGENTS.md:27-43`]
- No manual UAT should be invented for an automatable contract. Rights or applicability that cannot be established are true owner/scope decisions and must remain gates. [VERIFIED: `AGENTS.md:27-43`; `.planning/phases/GB-22-composition-and-microtest-evidence/22-CONTEXT.md:37-39`]
- Keep the plan within the Phase 22 cap and stop at the phase boundary; do not auto-advance. Exact roadmap value: `**Plan cap**: 10`. [VERIFIED: `.planning/ROADMAP.md:97-109`]
- Preserve Phase 20 manifests, notices, product exclusions and root MIT terms; don't change the root license to cover third-party material. [VERIFIED: `.planning/phases/GB-22-composition-and-microtest-evidence/22-CONTEXT.md:43`; `AGENTS.md:51-59`]
- No new dependency unless required by evidence; preserve existing component-level rights records and ensure all public artifact claims state their evidence limits. [VERIFIED: `.planning/phases/GB-22-composition-and-microtest-evidence/22-CONTEXT.md:43-46`; `AGENTS.md:47-53`]

Project skills discovery found no project-local `SKILL.md` files under `.codex/skills` or `.agents/skills`; no additional project skill rules were available. [VERIFIED: project skill discovery in this research session]

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | The existing RGBDS 1.0.1 pin can build both acid2 source versions without patches beyond font replacement. | Standard Stack | Build plans or expected ROM bytes may be wrong; verify with a reproducible build before admission. |
| A2 | Acid2's remaining source/art/reference/build-tool components will receive redistribution approval under Phase 20. | Summary / rights | Fixtures cannot be admitted or included in public CI. |
| A3 | The 482 protocol candidates can be made model-applicable or explicitly excluded with source-backed reasoning. | Pattern 2 | The required cohort may shrink or require scope resolution. |
| A4 | The proposed `gb22_.*(selftest|controls)` CTest name pattern will match the names eventually selected by the planner. | Validation Architecture | The sample quick command could select no tests or the wrong tests; choose names and verify the command during implementation. |

## Open Questions

1. **How should “eligible,” “executed,” and “excluded” satisfy both disjointness and “every eligible case executes”?**
   - What we know: D-03 calls the sets disjoint and requires every eligible case to execute, which mathematically means executed cases are a subset of eligible cases.
   - What's unclear: Whether “disjoint” means disjoint terminal outcomes (`executed` vs `excluded`) while eligibility is a predicate.
   - Recommendation: Represent eligibility and terminal outcome as separate dimensions; have the checker enforce eligible ⇒ executed and excluded ⇒ concrete reason, with no unaccounted case. Call out this interpretation in the plan.
   - **Planning disposition: RESOLVED for planning.** 22-02-T1 records eligibility as an evidence-derived predicate and executed/excluded as disjoint terminal outcomes covering the immutable roster. 22-05-T1/T2 and 22-06-T2 enforce every eligible case's required registration and execution, named exclusions and causal missing-case controls. This preserves both mandatory execution and terminal disjointness without silently reducing the roster.

2. **Which component rights are cleared for the acid2 derivative and microtest generated ROMs?**
   - What we know: The acid2 manifest states that the mgblib font rights gate is open; gbmicrotest has an MIT LICENSE but its source uses a `.nintendologo` header directive, and locked decisions require reviewing source and binary scope separately. [VERIFIED: `tests/acid2/manifest.json:2-3`; `tests/header.inc:3-9` at pinned upstream commit]
   - What's unclear: Whether all relevant authors/rightsholders authorized repository and public-CI redistribution for generated bytes, art, source and build inputs.
   - Recommendation: Keep the fixtures out of the repository and binary products until each component has evidence and the owner resolves any remaining rights gate.
   - **Planning disposition: RESOLVED for planning.** 22-02-T1 reviews every component's exact source/binary/art/reference/logo/derivative scope; 22-02-T2 and --require-approved block downstream builds, admission and execution until positive evidence passes review or the owner explicitly rescopes and replans. 22-04-T1 and 22-06-T1 reassert that approval before committing any real fixture. The external rights facts remain unresolved; this disposition claims no grant or permission.

3. **Can exact WLA-DX toolchain provenance be established for gbmicrotest ROM rebuilds?**
   - What we know: The upstream script invokes WLA-DX and does not pin its version; WLA-DX is not installed in this research environment. [CITED: https://github.com/aappleby/gbmicrotest/blob/463eb6bc0fe31d61781ef63060ad6d74090c0255/build.sh]
   - What's unclear: A pinned version/build closure and whether it reproduces the prebuilt ROM bytes.
   - Recommendation: Do not claim reproducibility until toolchain closure and output bytes are verified; record prebuilt byte identity separately.
   - **Planning disposition: RESOLVED for planning.** 22-02-T1/T2 and 22-06-T1 distinguish exact prebuilt identity from reproducibility and require truthful compliance with the unchanged Phase 20 provenance/build contract. If neither verified tool/output closure nor an allowed identity-only import record meets that contract, stop for evidence or explicit scope resolution. No WLA-DX install, version pin or reproducibility is assumed. For acid2, 22-03-T2 proves the existing RGBDS 1.0.1 pin works or stops before any toolchain policy change. Both external compatibility/rebuild facts remain execution gates.

4. **Which microtest cases have defensible model applicability?**
   - What we know: README's suite-level real-hardware claim names DMG-CPU-08 with “I believe”; per-case revision qualification is absent. [CITED: https://github.com/aappleby/gbmicrotest/blob/463eb6bc0fe31d61781ef63060ad6d74090c0255/README.md]
   - What's unclear: Case-level behavior, hardware revision and model-specific expectations across the 482 initial protocol candidates.
   - Recommendation: Require each additional applicability claim to cite case/source evidence; leave unsupported cases excluded with reason and trigger scope resolution if this prevents the requested admission.
   - **Planning disposition: RESOLVED for planning.** 22-02-T1/T2 requires source-backed case-level diagnostic applicability before real use; unsupported cases retain concrete exclusions, and inability to deliver the requested admitted cohort triggers the blocking scope-resolution route. 22-05/22-06 check the exact approved profile and 22-09 reconciles actual observations without elevating the uncertain CPU-08 statement into CPU-B/CGB hardware qualification. Per-case external model facts remain unresolved until evidence is reviewed; this disposition qualifies no hardware model.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|-------------|-----------|---------|----------|
| Python 3 | Existing and planned checkers | Yes | 3.14.4 | None needed; no external Python package. [VERIFIED: local availability probe] |
| CMake / CTest | Register and run required controls | Yes | 4.4.3 / 4.4.3 | Existing project preset and minimum-compatible CMake primitives. [VERIFIED: local availability probe] |
| Git | Pin immutable sources and inspect case tree | Yes | 2.41.0 | None for repository/source-tree checks. [VERIFIED: local availability probe] |
| RGBDS | Rebuild acid2 derivative | Installed | 1.0.4 locally; repository pin is 1.0.1. | Obtain/use the existing pinned 1.0.1 archive; local 1.0.4 does not prove pinned reproduction. [VERIFIED: local availability probe; `tests/scripts/reproduce-age.sh:56-63`] |
| WLA-DX (`wla-gb`, `wlalink`) | Rebuild gbmicrotest ROMs | No | — | Pin and provision a verified toolchain before any reproducible-build claim; otherwise record exact prebuilt ROM digests separately if rights clear. [VERIFIED: local availability probe] |

No project tests or builds were run as part of this research. [VERIFIED: research session command history]

## Validation Architecture

Nyquist validation is enabled; the configured test command is exactly `"test_command": "cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error"`. [VERIFIED: `.planning/config.json:20-25,48-54`]

### Test Framework

| Property | Value |
|----------|-------|
| Framework | CMake/CTest with Python standard-library checkers. [VERIFIED: `tests/CMakeLists.txt:1355-1370,3652-3670`] |
| Config file | Existing root `CMakeLists.txt`, `tests/CMakeLists.txt`, and `CMakePresets.json`; add CTest entries in the existing test CMake file. [VERIFIED: `tests/CMakeLists.txt:1355-1370,3652-3670`] |
| Quick run command | After names are implemented, `ctest --preset phase1 -R 'gb22_.*(selftest|controls)' --output-on-failure`. The regex is a planning recommendation, not an existing test-name contract. [ASSUMED] |
| Full suite command | `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error`. [VERIFIED: `.planning/config.json:54`] |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DIAG-01 | Validate source/build/rights/reference/glyph/mask identities; render or compare only admitted bytes; require exact unmasked equality. | Unit + integration | New CTest-wired acid2 checker self-test with synthetic reference/mask inputs; include changed ROM/reference/mask identity, broadened mask and one-pixel unmasked mismatch mutants. | No — phase work. Existing base runner at `tests/scripts/run-acid2-local.py`. [VERIFIED: `tests/scripts/run-acid2-local.py:1-6,168-237`] |
| DIAG-02 | Verify complete source roster and per-case source/ROM/rights/protocol/model links; require eligible executions and justified exclusions. | Unit + integration | New inventory verifier `--self-test` plus CTest-wired binding/accounting check. Include altered source/ROM, wrong model, dropped/duplicated case, unexplained exclusion and missing execution controls. | No — phase work. Reuse CGB corpus verifier patterns. [VERIFIED: `tests/scripts/verify-cgb-corpus-inventory.py:120-180`; `tests/CMakeLists.txt:1355-1370`] |
| RIGHTS-01 | Verify rights fields are complete and product install/release layouts contain no restricted fixture bytes. | Integration | Extend Phase 20 fixture admission and package-layout self-tests / repository checks; run through existing CTest/package check targets. | Phase 20 checkers exist; GB-22 records and package identities are not yet wired. [VERIFIED: `tests/scripts/verify-fixture-admission.py:1-3,26-61`; `tests/CMakeLists.txt:1440-1454`] |

### Sampling Rate

- **Per task commit:** Run the new narrowly selected checker CTests once their names exist. The candidate regex above is illustrative. [ASSUMED]
- **Per wave merge:** Run focused acid2/microtest controls and package exclusion controls via CTest. [VERIFIED: `AGENTS.md:27-43`; `tests/CMakeLists.txt:1355-1370,1440-1454,3652-3670`]
- **Phase gate:** Run the configured full preset command; final review must check requirement traceability and rights/model evidence, not just green scripts. [VERIFIED: `.planning/config.json:54`; `AGENTS.md:27-43`]

### Wave 0 Gaps

- [ ] Confirm microtest inventory count and lock the case roster/digests from the pinned upstream tree.
- [ ] Create a component-rights record and resolve distribution gates before admitting third-party fixture bytes.
- [ ] Produce derivative source/build records and original glyph source identities; verify the existing RGBDS pin against both acid2 sources.
- [ ] Create the text-cell allowlist, generated fixed-size mask and reviewable overlay; pin each input/output identity.
- [ ] Add checker self-tests for mutated source/ROM/reference/mask, mask widening, unmasked one-pixel diff, incorrect model, dropped/duplicated case, unexplained exclusion and missing execution.
- [ ] Wire all new controls to CTest and extend actual binary package checks for every admitted ROM/reference digest.

## Security Domain

Security enforcement is enabled at ASVS level 1. The config quote is:

```json
"security_enforcement": true,
"security_asvs_level": 1
```

[VERIFIED: `.planning/config.json:48-50`]

OWASP ASVS 5.0.0 is the current standard identified from OWASP's primary source. Applicable topics for these offline repository tools are V1 Encoding and Sanitization, V2 Validation and Business Logic, V5 File Handling, and a narrow V11 Cryptography use for SHA-256 fingerprints only. Authentication, sessions, access control and network API chapters have no corresponding surface in this phase. [CITED: https://asvs.owasp.org/; https://github.com/OWASP/ASVS/blob/v5.0.0/5.0/docs_en/OWASP_Application_Security_Verification_Standard_5.0.0_en.csv]

| Threat | Mitigation |
|--------|------------|
| Manifest paths escape the repository, follow an unintended symlink or select an unbounded file. | Enforce normalized relative paths, reject traversal, bound JSON/file/image sizes and use the existing symlink-aware package scanner pattern. [VERIFIED: `tests/scripts/verify-fixture-admission.py:44-60,102-108`; `cmake/ScanForbiddenFixtures.cmake:99-160`] |
| A fixture, mask or reference changes while its bytes are being checked. | Hash the exact bytes that will be consumed, pin immutable source and generated artifacts, and add changed-identity mutants. Existing acid2 runner already reads once, hashes, then returns those same bytes. [VERIFIED: `tests/scripts/run-acid2-local.py:32-44`] |
| Command injection through manifest-controlled runner or tool arguments. | Use argument arrays with `subprocess.run`, never a shell command string; validate paths and apply timeouts. [VERIFIED: `tests/scripts/verify-fixture-admission.py:111-117`; `tests/scripts/run-acid2-local.py:175-192`] |
| Forbidden ROM/reference bytes leak into product packages under a renamed path. | Reuse scans over actual install/staged package trees, checking both forbidden path components and exact size/SHA identity. [VERIFIED: `cmake/ScanForbiddenFixtures.cmake:3-7,62-100`] |
| Model/rights claims are rewritten to pass a check. | Bind accepted baseline/source facts independently from the candidate manifest and mutate applicability, accounting and rights rows in negative controls. [VERIFIED: `tests/scripts/verify-fixture-admission.py:26-42`; `tests/scripts/verify-cgb-corpus-inventory.py:120-180`] |

## Sources

### Primary (HIGH confidence for source behavior and checked repository facts)

- `tests/acid2/manifest.json` — existing release tags, ROM/reference digests, profiles and explicit no-bytes-in-repository note. [VERIFIED: `tests/acid2/manifest.json:2-37`]
- `tests/scripts/run-acid2-local.py` — current pin check, bounds, PNG/PPM decode, exact comparator and synthetic controls. [VERIFIED: `tests/scripts/run-acid2-local.py:20-53,78-103,168-237`]
- `tests/scripts/verify-fixture-admission.py`, `cmake/VerifyFixtureManifest.cmake`, `cmake/ScanForbiddenFixtures.cmake` — Phase 20 component and package patterns. [VERIFIED: `tests/scripts/verify-fixture-admission.py:26-61`; `cmake/ScanForbiddenFixtures.cmake:1-7,62-100`]
- `tests/scripts/verify-cgb-corpus-inventory.py`, `tests/external/cgb-corpus-inventory.json`, `tests/CMakeLists.txt` — source-bound corpus/accounting and CTest precedent. [VERIFIED: `tests/scripts/verify-cgb-corpus-inventory.py:120-180`; `tests/CMakeLists.txt:1355-1370`]
- Direct checkouts of dmg-acid2 tag v1.0, cgb-acid2 tag v1.1, and gbmicrotest commit `463eb6bc0fe31d61781ef63060ad6d74090c0255` — source/build inputs, counts, macros, model statement and build script.

### Official upstream sources (MEDIUM confidence for rights and applicability)

- [DMG acid2 v1.0 README](https://github.com/mattcurrie/dmg-acid2/blob/v1.0/README.md), [source](https://github.com/mattcurrie/dmg-acid2/tree/v1.0/src), [Makefile](https://github.com/mattcurrie/dmg-acid2/blob/v1.0/Makefile), [license](https://github.com/mattcurrie/dmg-acid2/blob/v1.0/LICENSE) — image reference, DMG conversion, source layout, build commands and upstream license text.
- [CGB acid2 v1.1 README](https://github.com/mattcurrie/cgb-acid2/blob/v1.1/README.md), [source](https://github.com/mattcurrie/cgb-acid2/tree/v1.1/src), [Makefile](https://github.com/mattcurrie/cgb-acid2/blob/v1.1/Makefile), [license](https://github.com/mattcurrie/cgb-acid2/blob/v1.1/LICENSE) — RGB555 conversion, composition/timing scope, build commands and license text.
- [gbmicrotest README](https://github.com/aappleby/gbmicrotest/blob/463eb6bc0fe31d61781ef63060ad6d74090c0255/README.md), [build script](https://github.com/aappleby/gbmicrotest/blob/463eb6bc0fe31d61781ef63060ad6d74090c0255/build.sh), [LICENSE](https://github.com/aappleby/gbmicrotest/blob/463eb6bc0fe31d61781ef63060ad6d74090c0255/LICENSE), [sources](https://github.com/aappleby/gbmicrotest/tree/463eb6bc0fe31d61781ef63060ad6d74090c0255/tests) and [prebuilt ROMs](https://github.com/aappleby/gbmicrotest/tree/463eb6bc0fe31d61781ef63060ad6d74090c0255/bin) — inventory, protocol, uncertain hardware statement, build requirement and license file. These sources do not settle rights or per-case model qualification. [CITED: same URLs]
- [Python `hashlib`](https://docs.python.org/3.14/library/hashlib.html) — standard-library SHA-256 API.
- [CMake `add_test`](https://cmake.org/cmake/help/v3.25/command/add_test.html) and [CTest test timeout](https://cmake.org/cmake/help/v3.25/prop_test/TIMEOUT.html) — test registration and runtime bounding.
- [OWASP ASVS](https://asvs.owasp.org/) and [ASVS 5.0.0 control catalog](https://github.com/OWASP/ASVS/blob/v5.0.0/5.0/docs_en/OWASP_Application_Security_Verification_Standard_5.0.0_en.csv) — applicable validation/file-handling/security categories.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — current Python/CMake/CTest patterns, RGBDS pin and no-dependency boundary are directly present in the repository. [VERIFIED: `tests/scripts/run-acid2-local.py:1-18`; `tests/scripts/reproduce-age.sh:56-63`; `AGENTS.md:27-43`]
- Architecture: HIGH — existing fixture admission, package scans, acid2 runner and CGB corpus verifier expose matching extension points. [VERIFIED: local sources cited above]
- Pitfalls: MEDIUM — upstream readmes and builds directly establish their authored statements/commands, while fixture redistribution rights and case-level model behavior need separate owner/source evidence. [CITED: upstream URLs above]

**Research date:** 2026-11-02  
**Valid until:** 2026-12-02 for repository patterns; verify upstream tags/rights and tool versions again before execution.

## RESEARCH COMPLETE
