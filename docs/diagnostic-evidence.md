# Diagnostic Evidence Admission

Phase 22 delivers synthetic composition tracing and source-bound diagnostic metadata only. The approved Phase 22 scope is a no-go for real acid2 or gbmicrotest fixture admission: no real diagnostic bytes are admitted or executed, and no rights, hardware, game-progress, or broad compatibility claim follows from the synthetic evidence.

## Phase 22 baseline gate result

Plan 22-02 rechecked source identifiers without fetching ROM or reference-image payloads and without running upstream tools. The assessment is **blocked**. The approved no-go preserves seven unresolved evidence gates:

1. `acid2_derivative_build_reproducibility` — exact-source RGBDS compatibility, replacement glyph inputs, and derivative output identities are unverified.
2. `acid2_component_rights_and_output_scope` — positive repository/public-CI scope for footer art, reference images, and derivative outputs is unresolved.
3. `acid2_profile_applicability` — the references are not tied to DMG-CPU-B and CGB-CPU-E.
4. `gbmicrotest_component_rights_and_output_scope` — rights for all generated ROMs, embedded Nintendo logo bytes, and derivative outputs are unresolved.
5. `gbmicrotest_prebuilt_rom_sha256` — SHA-256 values for all 513 prebuilt ROMs were not observed.
6. `gbmicrotest_case_applicability` — the suite-wide, qualified DMG-CPU-08 statement does not establish case-level applicability; CGB-CPU-E applicability is unknown.
7. `gbmicrotest_independent_oracle` — expected results are not independently established per case.

These gaps made the Phase 22 evidence insufficient for fixture admission; they are not a finding that an upstream license prohibits use. At that baseline, no fixture was admitted or executed. The two source-identity checks did not clear the seven gates above. Task 6 later admitted and ran one narrowly scoped gbmicrotest case. D-207 then accepted a bounded image-tree inference for the two exact Acid2 pins, and the Acid2 derivatives and fixture snapshot were prepared. The later bounded Acid2 run passed DMG-on-DMG and CGB-on-CGB, but DMG-on-CGB differed at all 19,840 compared pixels. This mismatch leaves DIAG-01 Pending; DIAG-02 and RIGHTS-01 also remain Pending under their original owners.

The pinned acid2 tags still resolve to `dmg-acid2` v1.0 commit `dc2295408f881637ff69f784d8d93f3d2db30181` and `cgb-acid2` v1.1 commit `fa5b7f86d6fb599f79e55169494d981a7af75a31`. Both source trees contain the `mgblib` gitlink at `5d829bf2ffa1447dcfd63c5dab2c44488632617e`. The upstream READMEs describe DMG and CGB PPU test intent and image conversion, but do not identify the exact DMG-CPU-B and CGB-CPU-E reference revisions. Their statements also limit the tests to composition/PPU behavior; they do not support mode-3 timing claims.

The pinned `gbmicrotest` commit `463eb6bc0fe31d61781ef63060ad6d74090c0255` has 513 exact source/ROM pairs in complete Git tree metadata. The inventory records every source path, ROM path, byte size, Git blob identity, and reviewed protocol class. This assessment did not calculate SHA-256 values from raw ROM payloads; those remain required before Phase 20 can admit any ROM bytes.

## Phase 24 diagnostic continuation status

The current Task 6 record is [diagnostic-closeout.json](../tests/external/diagnostic-closeout.json). The accepted D-207 inference supports only the `img/` trees at the exact pinned Acid2 commits; it does not extend to other repository content. The project-authored glyph table replaces the unreviewed mgblib font include. Both 32 KiB derivatives were built twice from the exact pinned source closures with pinned RGBDS 0.4.2, and the resulting outputs match. Their digests are DMG `6d3e5aca5f6d2ba31337ae61c1994e56f1780196c96cc645d54de378d39bbe82` and CGB `62a93fce12ef60938eefce81d02113a75e1a52b2631aa3d6f16388dc697837e2`. Both have valid checksums, start at `0x0100`, and contain zero bytes throughout the Nintendo logo range. The deterministic 55-member archive, member-level build manifest, local MIT notice, generic admission manifest, and immutable fixture pointer are recorded under `fixtures/acid2/`; the outer manifest binds the archive and local notice, while the inner manifest binds each archive member.

The source-derived DMG mask covers 50 cells (3,200 masked and 19,840 compared pixels); the CGB mask covers 52 cells (3,328 masked and 19,712 compared pixels). The exact comparisons were DMG-on-DMG, DMG-on-CGB in DMG mode, and CGB-on-CGB. The two same-model comparisons had zero differing compared pixels. DMG-on-CGB had 19,840 differing compared pixels and is recorded as a runtime mismatch. The independent gbmicrotest lane then passed its one admitted case. No hardware, glyph-accuracy, or mode-3 timing claim follows from these results.

The pinned gbmicrotest issue asks “Under what license are these provided?” and author `aappleby` replies “License added”; the pinned commit is titled “Create LICENSE” and changes only the root `LICENSE`. This supports admitting the selected prebuilt ROM for one diagnostic and its logo-free derivative with the full MIT notice, under a bounded source-backed interpretation. The original ROM and Nintendo logo bytes remain excluded from the bundle, and the other 512 ROMs remain outside this scope.

The independent source review selected `div_inc_timing_a` before observing any emulator outcome. Its pinned [assembly](https://github.com/aappleby/gbmicrotest/blob/463eb6bc0fe31d61781ef63060ad6d74090c0255/tests/div_inc_timing_a.s) says `pass - dmg`, clears DIV, waits 60 NOPs, reads DIV, and expects zero. Its pinned [header](https://github.com/aappleby/gbmicrotest/blob/463eb6bc0fe31d61781ef63060ad6d74090c0255/tests/header.inc) selects `.romdmg`, and the pinned [shared macros](https://github.com/aappleby/gbmicrotest/blob/463eb6bc0fe31d61781ef63060ad6d74090c0255/tests/macros.inc) write actual, expected, and pass/fail bytes to FF80–FF82. These exact per-case software semantics support a declared **DMG-CPU-B software diagnostic scope only**. The README's uncertain DMG-CPU-08 statement is suite-wide and is not used as case-specific hardware evidence; no hardware or CGB applicability is claimed. The terminal macro loops while drawing to VRAM, so the adapter stops on its source-defined terminal marker under bounded guest work.

The pinned `bin/div_inc_timing_a.gb` is 32,768 bytes, Git blob `8ff913924540b1bbc4363744f020b38e96c94a3a`, SHA-256 `1530b5a34af78e182c8b1f5f9043f8e5ae3e9f2fac13d43f3c5714eece282706`. Its header and global checksums validate. The bootless derivative has SHA-256 `53b0624af64524fe7cdf9b0aed3456ca60c7b30fe25cd5202b6b77855f57ffa8`. Only the logo range `0x0104–0x0133` was zeroed and the global checksum at `0x014E–0x014F` recomputed: 44 changed bytes, all within those ranges; the header checksum at `0x014D` is unchanged, all other bytes match, and the new global checksum `0x16F8` validates. The original remains ignored local-review material; only the derivative is in the admitted bundle.

The root [MIT notice at the pinned commit](https://github.com/aappleby/gbmicrotest/blob/463eb6bc0fe31d61781ef63060ad6d74090c0255/LICENSE), together with [issue #1 and the author's reply](https://github.com/aappleby/gbmicrotest/issues/1#issuecomment-2080090499), supports a bounded output scope for the selected prebuilt ROM. The exact pinned source commit is titled “Create LICENSE” and changes only `LICENSE`. This is source-backed evidence for the one selected prebuilt ROM and its source-bound bootless derivative when the full notice travels. It does not resolve the T5 suite-wide prebuilt-ROM or embedded-logo components, and it does not extend to the other 512 ROMs or other sources. The pinned README lists prebuilt ROMs in `bin/` and instructs users to install WLA-DX and run `build.sh`; the tool version is not pinned, so no reproducible-build claim is made. The bundle contains only the transformed derivative, with Nintendo logo bytes removed.

The current record accounts for all 513 pinned names: `div_inc_timing_a` is the one eligible and executed case, selected by its source-defined shared verdict and DMG-CPU-B software scope; 512 names are excluded with source/model/oracle or protocol reasons. The case passed with actual `00`, expected `00`, terminal `01`, after 72 instructions and 77 events. A fresh runner qualification and the runtime receipt are bound to the candidate and fixture admission in [the machine record](../tests/external/diagnostic-closeout.json); the recorded runtime evidence file is `build/phase24/gbmicrotest-runtime-preflight.json` and remains ignored. This completes runtime accounting for the one-case cohort only. DIAG-01 and DIAG-02 remain Pending under their original owners until their original criteria are evidenced.

## Phase 22 disposition

| Claim area | Phase 22 disposition |
|---|---|
| synthetic composition | supported: original synthetic DMG composition and controls passed |
| source metadata | supported: metadata-only assessment retained all 513 source/ROM names |
| real diagnostic bytes/results | unsupported: no real diagnostic payload or real diagnostic result exists |
| rights and profile applicability | unresolved: the metadata does not supply output rights or model qualification |
| DIAG/RIGHTS requirement completion | pending: DIAG-01 and DIAG-02 remain Pending; RIGHTS-01 remains Pending under Phase 20 ownership |

The original synthetic DMG composition and controls passed. The metadata-only assessment retained all
513 source/ROM names. No real upstream diagnostic payload was fetched, retained, built, run, or
admitted. No real diagnostic result exists.

The seven unresolved gates are acid2_derivative_build_reproducibility,
acid2_component_rights_and_output_scope, acid2_profile_applicability,
gbmicrotest_component_rights_and_output_scope, gbmicrotest_prebuilt_rom_sha256,
gbmicrotest_case_applicability, and gbmicrotest_independent_oracle.

The inventory retains 480 shared-macro verdict cases, two inline FF80–FF82 cases, 31 initial
exclusions, and 482 blocked and not observed protocol candidates. There are zero admitted
and zero executed cases; final suite accounting is incomplete. Git blob IDs and sizes do not provide
ROM SHA-256 values, reproducibility, or redistribution rights.

The source review's DMG-CPU-08 statement is uncertain and suite-wide only. It does not establish
per-case applicability to DMG-CPU-B or CGB-CPU-E. The synthetic result establishes only its
project-authored mask and comparison control; glyph rendering, mode-3 timing, hardware
qualification, game behavior, and broad compatibility remain unqualified. This is insufficient
evidence and does not conclude that license terms prohibit use.

D-141 accepts the revised Phase 22 acceptance criteria only. The original DIAG-01 and DIAG-02
definitions remain unchanged and Pending, and RIGHTS-01 remains Pending under Phase 20 ownership.
Any future real-fixture attempt requires new source-backed evidence and a separately selected scope.

## Component and build scope

| Component | Current evidence | Admission status |
|---|---|---|
| acid2 source code | Pinned DMG v1.0 and CGB v1.1 root MIT notices are retained; only the exact source closures are bundled. | Supported for this repository/public-CI fixture scope. |
| acid2 footer graphics and reference images | D-207 accepts the root MIT grant for only the `img/` tree at each exact pinned source commit; full notices and README credit travel with the fixture. | Supported by a bounded inference for these exact trees only. |
| mgblib font | Both source commits pin the same `mgblib` gitlink; the derivative plan excludes its font data. | Excluded by design; no font bytes used. |
| project replacement glyphs | A project-authored 128-tile glyph table replaces only the old font include. | Built; visual glyph accuracy is not claimed. |
| acid2 derivatives | Two clean builds per model match the same 32 KiB digest; header and global checksums validate; all logo bytes are zero. | Build identity supported; same-model comparisons pass, while DMG-on-CGB mismatches all 19,840 compared pixels. DIAG-01 remains Pending. |
| gbmicrotest source code | MIT terms are recorded for source-code use at the pinned commit. | Supported for repository/public-CI source use. |
| gbmicrotest ROMs | T5's source-wide 513-ROM outcome remains unresolved. T6 bound issue #1/comment 2080090499 and commit 463eb6b (“Create LICENSE,” only `LICENSE` changed) to the selected `div_inc_timing_a` ROM and its bootless derivative. | One source-bound case admitted with the full MIT notice; the other 512 ROMs remain outside this scope and have not been fetched. |
| embedded Nintendo logo | The pinned header uses `.nintendologo`; T5's upstream component-rights result remains unresolved. The local derivative zeros the entire logo range and includes no logo bytes. | Unresolved for original/prebuilt ROMs; excluded from this local derivative. |
| notices and derivative outputs | Acid2 art/reference scope and the upstream logo remain unresolved. The selected gbmicrotest derivative is admitted with the complete pinned MIT notice; logo bytes are absent. | The selected gbmicrotest case passed; the Acid2 cross-model mismatch remains unresolved. |

The Acid2 build uses the exact pinned RGBDS 0.4.2 source commit `ede982b50a68a6253ffbab17dc4184710b08032f`. Two clean builds per variant reproduce the recorded output digests. The recipe uses `rgbfix -f hg`, which sets checksums without inserting Nintendo logo bytes; the build receipt records tool hashes, source closure, outputs, and header facts. RGBDS remains a build-only tool and is not included in the fixture. The pinned `gbmicrotest` README instructs users to install WLA-DX and run `build.sh`; it does not pin the tool version or build closure. WLA-DX is treated as a build-only tool and is not copied, linked, or shipped. No reproducible-build claim is made for gbmicrotest.

## Microtest roster and accounting

The source review recorded 480 cases using shared verdict macros, two MBC1 cases with inline FF80–FF82 verdict output, and 31 initial exclusions without either reviewed protocol. The excluded source names remain explicitly present in the inventory. A separate constant in `verify-diagnostic-admission.py` pins the canonical projection of all 513 names, source/ROM paths, sizes, Git blob IDs, and protocol classes, so changing rows and summary totals together does not clear the roster check. T6 additionally pins the observed SHA-256 for the single local review ROM; the other 512 ROM payloads remain uninspected.

Eligibility is a predicate over reviewed protocol, component rights, and case-specific applicability. The final `executed` and `excluded` sets are disjoint terminal outcomes; every eligible case must execute. Task 6 accounts for one source-selected eligible and executed case and 512 cohort exclusions with specific source/model/oracle or protocol reasons. This completes the selected cohort's runtime accounting, not qualification of the other ROMs or the full suite.

The upstream README says the suite was checked on real hardware and qualifies DMG-CPU-08 with “I believe.” This is an uncertain suite-wide claim, not case-level hardware evidence. The selected case's source supports a DMG-CPU-B software diagnostic scope only; no DMG-CPU-B hardware observation or CGB-CPU-E claim is made. The current runner was freshly qualified and the single selected case passed its bounded execution. Source-wide ROM/logo scope, Acid2, hardware, DMG-CPU-08, and CGB claims remain unresolved or excluded.

## Verification

The metadata contract and its rights, model, roster, and eligibility mutation controls are registered as CTests. The real-byte approval command is:

```sh
python3 -I tests/scripts/verify-diagnostic-admission.py --require-approved --repo-root . --source-revision HEAD
```

The independent gbmicrotest-only admission check and one-case runtime passed; the runtime observed `actual=00`, `expected=00`, and terminal `01` in 0.44 seconds with the current qualified runner. The Acid2 triplet ran once: DMG-on-DMG and CGB-on-CGB each had zero differing compared pixels, while DMG-on-CGB differed at all 19,840 compared pixels. The mismatch is preserved in the machine record; Acid2 was not rerun. The synthetic Acid2 tracer and its controls establish only synthetic mask/comparison behavior; neither those controls nor this runtime result establish hardware behavior, mode-3 timing, game progress, or broad compatibility. Requirements DIAG-01, DIAG-02, and RIGHTS-01 remain Pending.

Primary source references: [DMG acid2 v1.0 README](https://github.com/mattcurrie/dmg-acid2/blob/dc2295408f881637ff69f784d8d93f3d2db30181/README.md), [CGB acid2 v1.1 README](https://github.com/mattcurrie/cgb-acid2/blob/fa5b7f86d6fb599f79e55169494d981a7af75a31/README.md), and [gbmicrotest README at the pinned commit](https://github.com/aappleby/gbmicrotest/blob/463eb6bc0fe31d61781ef63060ad6d74090c0255/README.md). Hashes establish identity only; they do not establish rights or model applicability.
