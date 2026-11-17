# Diagnostic Evidence Admission

Phase 22 delivers synthetic composition tracing and source-bound diagnostic metadata only. The approved Phase 22 scope is a no-go for real acid2 or gbmicrotest fixture admission: no real diagnostic bytes are admitted or executed, and no rights, hardware, game-progress, or broad compatibility claim follows from the synthetic evidence.

## Current gate result

Plan 22-02 rechecked source identifiers without fetching ROM or reference-image payloads and without running upstream tools. The assessment is **blocked**. The approved no-go preserves seven unresolved evidence gates:

1. `acid2_derivative_build_reproducibility` — exact-source RGBDS compatibility, replacement glyph inputs, and derivative output identities are unverified.
2. `acid2_component_rights_and_output_scope` — positive repository/public-CI scope for footer art, reference images, and derivative outputs is unresolved.
3. `acid2_profile_applicability` — the references are not tied to DMG-CPU-B and CGB-CPU-E.
4. `gbmicrotest_component_rights_and_output_scope` — rights for all generated ROMs, embedded Nintendo logo bytes, and derivative outputs are unresolved.
5. `gbmicrotest_prebuilt_rom_sha256` — SHA-256 values for all 513 prebuilt ROMs were not observed.
6. `gbmicrotest_case_applicability` — the suite-wide, qualified DMG-CPU-08 statement does not establish case-level applicability; CGB-CPU-E applicability is unknown.
7. `gbmicrotest_independent_oracle` — expected results are not independently established per case.

These gaps make the evidence insufficient for admission; they are not a finding that an upstream license prohibits use. No fixture was admitted or executed, and this record does not complete DIAG-01, DIAG-02, or RIGHTS-01. The two source-identity checks are supported, but do not clear any of the seven gates above.

The pinned acid2 tags still resolve to `dmg-acid2` v1.0 commit `dc2295408f881637ff69f784d8d93f3d2db30181` and `cgb-acid2` v1.1 commit `fa5b7f86d6fb599f79e55169494d981a7af75a31`. Both source trees contain the `mgblib` gitlink at `5d829bf2ffa1447dcfd63c5dab2c44488632617e`. The upstream READMEs describe DMG and CGB PPU test intent and image conversion, but do not identify the exact DMG-CPU-B and CGB-CPU-E reference revisions. Their statements also limit the tests to composition/PPU behavior; they do not support mode-3 timing claims.

The pinned `gbmicrotest` commit `463eb6bc0fe31d61781ef63060ad6d74090c0255` has 513 exact source/ROM pairs in complete Git tree metadata. The inventory records every source path, ROM path, byte size, Git blob identity, and reviewed protocol class. This assessment did not calculate SHA-256 values from raw ROM payloads; those remain required before Phase 20 can admit any ROM bytes.

## Phase 24 diagnostic continuation status

The current Task 6 record is [diagnostic-closeout.json](../tests/external/diagnostic-closeout.json), bound to the unchanged T5 component-rights record. Both Acid2 variants remain blocked before derivative creation because the footer/reference-image scope is unresolved. The upstream font data remains excluded. No Acid2 replacement glyph, derivative, reference image, fixture manifest, or admission snapshot was created. T6 did locally acquire one pinned gbmicrotest ROM and create a bootless derivative in the ignored review area; neither is a fixture or an admitted, staged, or executed payload.

The independent source review selected `div_inc_timing_a` before observing any emulator outcome. Its pinned [assembly](https://github.com/aappleby/gbmicrotest/blob/463eb6bc0fe31d61781ef63060ad6d74090c0255/tests/div_inc_timing_a.s) says `pass - dmg`, clears DIV, waits 60 NOPs, reads DIV, and expects zero. Its pinned [header](https://github.com/aappleby/gbmicrotest/blob/463eb6bc0fe31d61781ef63060ad6d74090c0255/tests/header.inc) selects `.romdmg`, and the pinned [shared macros](https://github.com/aappleby/gbmicrotest/blob/463eb6bc0fe31d61781ef63060ad6d74090c0255/tests/macros.inc) write actual, expected, and pass/fail bytes to FF80–FF82. These exact per-case software semantics support a declared **DMG-CPU-B software diagnostic scope only**. The README's uncertain DMG-CPU-08 statement is suite-wide and is not used as case-specific hardware evidence; no hardware or CGB applicability is claimed. The terminal macro loops while drawing to VRAM, so a future runner still needs an explicit terminal observation and bounded guest-work limit. No runtime result exists.

The pinned `bin/div_inc_timing_a.gb` is 32,768 bytes, Git blob `8ff913924540b1bbc4363744f020b38e96c94a3a`, SHA-256 `1530b5a34af78e182c8b1f5f9043f8e5ae3e9f2fac13d43f3c5714eece282706`. Its header and global checksums validate. The local derivative has SHA-256 `53b0624af64524fe7cdf9b0aed3456ca60c7b30fe25cd5202b6b77855f57ffa8`. Only the logo range `0x0104–0x0133` was zeroed and the global checksum at `0x014E–0x014F` recomputed: 44 changed bytes, all within those ranges; the header checksum at `0x014D` is unchanged, all other bytes match, and the new global checksum `0x16F8` validates. The original and derivative remain ignored local-review artifacts and were not admitted, staged, or run.

The root [MIT notice at the pinned commit](https://github.com/aappleby/gbmicrotest/blob/463eb6bc0fe31d61781ef63060ad6d74090c0255/LICENSE) grants broad rights to “the Software” but does not define whether prebuilt/generated ROM outputs are included. The pinned README says prebuilt ROMs are in `bin/` and instructs users to install WLA-DX and run `build.sh`; it gives no output-specific license scope, and the tool version is not pinned. This does not establish a prohibition, but it also does not establish repository/public-CI redistribution permission for the compiled derivative. The specific missing evidence is a component-level grant or source statement that covers the pinned prebuilt/compiled ROM output. T5's unresolved finding for the upstream embedded logo remains unchanged; the local bootless derivative contains no logo bytes.

The current record accounts for all 513 pinned names: one candidate has an observed original-ROM digest and derivative identity but remains blocked by unresolved compiled-output redistribution scope; the other 512 are excluded from this candidate cohort because their oracle/model scope was not selected for review or their recorded protocol is unsupported. Zero cases are eligible or executed. Runtime adapter qualification and bounded execution have not been attempted. This is complete roster accounting for the blocked review, not a completed runtime result. DIAG-01 and DIAG-02 remain Pending under their original owners.

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
| acid2 source code | MIT terms are recorded for the two pinned repositories; evidence is limited to source code. | Supported for repository/public-CI source use. |
| acid2 footer graphics | No reviewed component grant establishes repository and public-CI scope for the retained art. | Unresolved. |
| acid2 reference images | The READMEs identify these as comparison references, but do not grant copying/distribution scope. | Unresolved. |
| mgblib font | Both source commits pin the same `mgblib` gitlink; the derivative plan excludes its font data. | Excluded by design; no font bytes used. |
| original replacement font | No project-authored replacement has been created or built. | Not created; outside the approved Phase 22 scope. |
| gbmicrotest source code | MIT terms are recorded for source-code use at the pinned commit. | Supported for repository/public-CI source use. |
| gbmicrotest ROMs | Source-tree blob IDs and sizes are known; T6 computed the original SHA-256 and local derivative digest for `div_inc_timing_a` only. Output scope and 512 payload digests remain unresolved. | Unresolved; no ROM fixture admitted. |
| embedded Nintendo logo | The pinned header uses `.nintendologo`; T5's upstream component-rights result remains unresolved. The local derivative zeros the entire logo range and includes no logo bytes. | Unresolved for original/prebuilt ROMs; excluded from this local derivative. |
| notices and derivative outputs | No complete positive component scope is available while art, references, ROMs, and logo remain unresolved. | Unresolved; no notice row or admitted derivative was created. |

The acid2 Makefiles use RGBDS tools. The project already pins RGBDS 1.0.1, but compatibility and output reproduction for these source commits have not been verified. This remains an unresolved evidence gate; no upstream build or derivative work is part of the approved Phase 22 scope. The pinned `gbmicrotest` README instructs users to install WLA-DX and run `build.sh`; it does not pin the tool version or build closure. WLA-DX is treated as a build-only tool and is not copied, linked, or shipped. No reproducible-build claim is made. Exact prebuilt identities remain separate from any build claim, though their current SHA-256 values are also not observed here.

## Microtest roster and accounting

The source review recorded 480 cases using shared verdict macros, two MBC1 cases with inline FF80–FF82 verdict output, and 31 initial exclusions without either reviewed protocol. The excluded source names remain explicitly present in the inventory. A separate constant in `verify-diagnostic-admission.py` pins the canonical projection of all 513 names, source/ROM paths, sizes, Git blob IDs, and protocol classes, so changing rows and summary totals together does not clear the roster check. T6 additionally pins the observed SHA-256 for the single local review ROM; the other 512 ROM payloads remain uninspected.

Eligibility is a predicate over reviewed protocol, component rights, and case-specific applicability. The final `executed` and `excluded` sets are disjoint terminal outcomes; every eligible case must execute. At this assessment stage, 31 no-protocol cases are initial exclusions, zero cases are declared eligible or executed, and 482 protocol candidates are blocked and not observed. These are pre-admission facts, not a completed suite accounting or successful partial admission.

The upstream README says the suite was checked on real hardware and qualifies DMG-CPU-08 with “I believe.” This is an uncertain suite-wide claim, not case-level hardware evidence. The selected case's source supports a DMG-CPU-B software diagnostic scope only; no DMG-CPU-B hardware observation or CGB-CPU-E claim is made. A future real-fixture attempt still requires the compiled-output grant, a qualified bounded runner, and an actual source-defined execution result.

## Verification

The metadata contract and its rights, model, roster, and eligibility mutation controls are registered as CTests. The real-byte approval command is:

```sh
python3 -I tests/scripts/verify-diagnostic-admission.py --require-approved --repo-root . --source-revision HEAD
```

It returns exit status 2 with `scope-resolution-required` while any required evidence is unresolved. Owner approval of the metadata-only scope does not satisfy or alter any admission gate. The synthetic tracer and its controls establish only synthetic mask/comparison behavior; they do not establish real glyph accuracy, mode-3 timing, hardware behavior, game progress, or broad compatibility. Future real-fixture work requires the missing evidence and a separately selected scope. Requirements DIAG-01, DIAG-02, and RIGHTS-01 remain Pending.

Primary source references: [DMG acid2 v1.0 README](https://github.com/mattcurrie/dmg-acid2/blob/dc2295408f881637ff69f784d8d93f3d2db30181/README.md), [CGB acid2 v1.1 README](https://github.com/mattcurrie/cgb-acid2/blob/fa5b7f86d6fb599f79e55169494d981a7af75a31/README.md), and [gbmicrotest README at the pinned commit](https://github.com/aappleby/gbmicrotest/blob/463eb6bc0fe31d61781ef63060ad6d74090c0255/README.md). Hashes establish identity only; they do not establish rights or model applicability.
