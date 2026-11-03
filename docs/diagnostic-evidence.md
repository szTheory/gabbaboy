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

## Component and build scope

| Component | Current evidence | Admission status |
|---|---|---|
| acid2 source code | MIT terms are recorded for the two pinned repositories; evidence is limited to source code. | Supported for repository/public-CI source use. |
| acid2 footer graphics | No reviewed component grant establishes repository and public-CI scope for the retained art. | Unresolved. |
| acid2 reference images | The READMEs identify these as comparison references, but do not grant copying/distribution scope. | Unresolved. |
| mgblib font | Both source commits pin the same `mgblib` gitlink; the derivative plan excludes its font data. | Excluded by design; no font bytes used. |
| original replacement font | No project-authored replacement has been created or built. | Not created; outside the approved Phase 22 scope. |
| gbmicrotest source code | MIT terms are recorded for source-code use at the pinned commit. | Supported for repository/public-CI source use. |
| gbmicrotest ROMs | Source-tree blob IDs and sizes are known, but output scope and all 513 SHA-256 values are not. | Unresolved. |
| embedded Nintendo logo | The pinned sources use the `.nintendologo` header directive; no explicit grant for the resulting logo bytes was identified. | Unresolved. |
| notices and derivative outputs | No complete positive component scope is available while art, references, ROMs, and logo remain unresolved. | Unresolved; no notice row or admitted derivative was created. |

The acid2 Makefiles use RGBDS tools. The project already pins RGBDS 1.0.1, but compatibility and output reproduction for these source commits have not been verified. This remains an unresolved evidence gate; no upstream build or derivative work is part of the approved Phase 22 scope. The pinned `gbmicrotest` README instructs users to install WLA-DX and run `build.sh`; it does not pin the tool version or build closure. WLA-DX is treated as a build-only tool and is not copied, linked, or shipped. No reproducible-build claim is made. Exact prebuilt identities remain separate from any build claim, though their current SHA-256 values are also not observed here.

## Microtest roster and accounting

The source review recorded 480 cases using shared verdict macros, two MBC1 cases with inline FF80–FF82 verdict output, and 31 initial exclusions without either reviewed protocol. The excluded source names remain explicitly present in the inventory. A separate constant in `verify-diagnostic-admission.py` pins the canonical projection of all 513 names, source/ROM paths, sizes, Git blob IDs, and protocol classes, so changing rows and summary totals together does not clear the roster check.

Eligibility is a predicate over reviewed protocol, component rights, and case-specific applicability. The final `executed` and `excluded` sets are disjoint terminal outcomes; every eligible case must execute. At this assessment stage, 31 no-protocol cases are initial exclusions, zero cases are declared eligible or executed, and 482 protocol candidates are blocked and not observed. These are pre-admission facts, not a completed suite accounting or successful partial admission.

The upstream README says the suite was checked on real hardware and qualifies DMG-CPU-08 with “I believe.” This is an uncertain suite-wide claim, not case-level evidence. No DMG-CPU-B or CGB-CPU-E result is claimed. A future real-fixture attempt requires new source-backed evidence for the applicable gates and a separately selected scope.

## Verification

The metadata contract and its rights, model, roster, and eligibility mutation controls are registered as CTests. The real-byte approval command is:

```sh
python3 -I tests/scripts/verify-diagnostic-admission.py --require-approved --repo-root . --source-revision HEAD
```

It returns exit status 2 with `scope-resolution-required` while any required evidence is unresolved. Owner approval of the metadata-only scope does not satisfy or alter any admission gate. The synthetic tracer and its controls establish only synthetic mask/comparison behavior; they do not establish real glyph accuracy, mode-3 timing, hardware behavior, game progress, or broad compatibility. Future real-fixture work requires the missing evidence and a separately selected scope. Requirements DIAG-01, DIAG-02, and RIGHTS-01 remain Pending.

Primary source references: [DMG acid2 v1.0 README](https://github.com/mattcurrie/dmg-acid2/blob/dc2295408f881637ff69f784d8d93f3d2db30181/README.md), [CGB acid2 v1.1 README](https://github.com/mattcurrie/cgb-acid2/blob/fa5b7f86d6fb599f79e55169494d981a7af75a31/README.md), and [gbmicrotest README at the pinned commit](https://github.com/aappleby/gbmicrotest/blob/463eb6bc0fe31d61781ef63060ad6d74090c0255/README.md). Hashes establish identity only; they do not establish rights or model applicability.
