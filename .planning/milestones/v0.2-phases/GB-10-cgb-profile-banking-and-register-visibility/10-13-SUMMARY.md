---
phase: 10-cgb-profile-banking-and-register-visibility
plan: 13
subsystem: fixtures-tests
tags: [cgb, fixture, rgbds, vbk, svbk, echo-ram, oam-dma, negative-control]
requires: [10-12]
provides: [fixtures/cgb-banking original guest, byte-identical reproduction script, cgb_banking_* CTests]
affects: [17, 18, 19, 20]
key-files:
  created: [fixtures/cgb-banking/banking.asm, fixtures/cgb-banking/banking-cgb.gb, fixtures/cgb-banking/banking-dmg.gb, fixtures/cgb-banking/manifest.json, fixtures/cgb-banking/LICENSE.txt, tests/scripts/reproduce-cgb-banking.sh]
  modified: [tests/test_banking.c, tests/CMakeLists.txt, tests/expected-tests.txt, .gitattributes, .github/workflows/fixture-repro.yml]
requirements-completed: []
status: complete
commits: 3
plan_head_before: 3c405c4a411b81af3fa45876edd7802a69373d03
plan_head_after: fc359d9cabe6cb834a9c9ecd70ea8bdc8381efc1
actuals:
  tokens: 45000
  tasks: 3
  commits: 3
duration: 45 min
completed: 2026-10-12
coverage:
  - id: 10-13-banking-fixtures
    description: "Original fixtures/cgb-banking guest (two ROMs from one source) built with pinned RGBDS 1.0.1, digest-verified"
    human_judgment: false
    verification:
      - kind: unit
        ref: "ctest --test-dir build/phase15_1_14 --output-on-failure -R '^cgb_banking_fixture_digest$'"
        status: pass
      - kind: other
        ref: 'PATH="/private/tmp/gabbaboy-phase15_1/rgbds-v1.0.1/tools:$PATH" bash tests/scripts/reproduce-cgb-banking.sh --compare fixtures/cgb-banking'
        status: pass
  - id: 10-13-profile-cells
    description: "All D-18 cells on CGB mode, compat mode and the DMG profile"
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest --test-dir build/phase15_1_14 --output-on-failure -R '^cgb_banking_guest_cgb$'"
        status: pass
      - kind: integration
        ref: "ctest --test-dir build/phase15_1_14 --output-on-failure -R '^cgb_banking_guest_compat$'"
        status: pass
      - kind: integration
        ref: "ctest --test-dir build/phase15_1_14 --output-on-failure -R '^cgb_banking_guest_dmg$'"
        status: pass
  - id: 10-13-negative-controls
    description: "Three negative controls (patched expected value, CGB build on DMG profile, skipped SVBK write)"
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest --test-dir build/phase15_1_14 --output-on-failure -R '^cgb_banking_patched_expected$'"
        status: pass
      - kind: integration
        ref: "ctest --test-dir build/phase15_1_14 --output-on-failure -R '^cgb_banking_cgb_on_dmg$'"
        status: pass
      - kind: integration
        ref: "ctest --test-dir build/phase15_1_14 --output-on-failure -R '^cgb_banking_skip_svbk$'"
        status: pass
---

# Phase 10 Plan 13: Original CGB banking fixture Summary

One original `banking.asm` assembled into `banking-cgb.gb` (`$143 = $80`) and `banking-dmg.gb` (`$143 = $00`) with RGBDS 1.0.1 runs nine result cells (VBK, SVBK, echo per bank, E000 mirror, OAM DMA from D0, 80, E0/FE and page 00, and the frozen compat/DMG cell) on three profile/mode combinations, with three detected negative controls and a byte-identical pinned rebuild.

## Accomplishments

- `fixtures/cgb-banking/`: source, both ROMs (32 KiB ROM-only), `manifest.json` (same RGBDS pin as `fixtures/mbc5-banking`, `fixtures[]` with size and sha256 for both ROMs, build recipe, protocol with result-byte map and patch offsets, `evidence_class` "original software fixture plus synthetic oracle, not hardware evidence", scope limits), `LICENSE.txt`. `.gitattributes` marks both ROMs `-text` (`git check-attr text` prints `unset`).
- Guest design: expectations come from its own `$0143` and entry A (`$11` CGB profile, `$01` DMG). FF4F/FF70 are accessed only when A is `$11` (those accesses stop the core on the DMG profile, D-09). C000 is the `$A5`/`$EE` verdict, C001 the run kind, C002..C00A one byte per cell. The page-00 DMA cell compares OAM against non-zero ROM bytes planted at `$0000-$009F` and read back by the CPU, so a transfer that returned zeros cannot pass; OAM is cleared before each transfer so a transfer that did nothing cannot pass.
- `tests/test_banking.c`: fixture driver (read exact 32 KiB image, assert header bytes, load, run to halt within the manifest timeout of 2000000 half dots, read C000..C00A with `gbb_peek_ram`). Expected cell tables are written from the protocol, not from core output.
- `tests/scripts/reproduce-cgb-banking.sh` and a `fixture-repro.yml` step "Reproduce CGB banking fixture bytes"; the pin-consistency block also loads the new manifest. The script additionally cross-checks the manifest patch offsets against the linker `.sym` file.

## Verification

- `ctest -R '^cgb_banking_'`: 7/7 pass. Full suite `ctest --preset phase1`: 506/506 pass. `bash tests/scripts/verify-dmg-baseline.sh`: `baseline status=pass`, rows=0.
- `reproduce-cgb-banking.sh` with the pinned toolchain: `result=byte-identical roms=2`. With the host's rgbasm 1.0.4 it refuses ("rgbasm version mismatch"), proving the version guard works.
- Controls (all assert exact per-cell bytes, not just the verdict): (i) patching the `cp $10` operand at `0x01F1` gives C002 `$FF`, every other cell `$01`, verdict `$EE`; (ii) `banking-cgb.gb` on the DMG profile gives `$FF` for C002, C003, C004, C006, C007, C009, `$01` for C005 and C008, `$00` for C00A, verdict `$EE`; (iii) NOPing the SVBK write at `0x023A` gives C003 `$FF` only, verdict `$EE`. Offsets are asserted (opcode bytes) before patching, so layout drift fails loudly.

## Fresh behavior recheck (2026-10-21)

The current isolated build passed all seven mapped `cgb_banking_*` CTests. With the pinned RGBDS 1.0.1 tools, `reproduce-cgb-banking.sh --compare fixtures/cgb-banking` again reported `result=byte-identical roms=2`. These are current local software-fixture checks; the original full-suite and producer statements above remain historical.

## Toolchain note

The committed ROM bytes were produced by the pinned RGBDS v1.0.1 macOS archive (`rgbds-macos.zip`, sha256 `2f6f13c6...3645`, digest-verified after download into a temp directory outside the repo). The host's Homebrew rgbasm 1.0.4 was not used. The reproduction script rebuilds with the pinned tools and compares byte for byte, and CI runs it with the Linux archive.

## Deviations from Plan

**1. Compatibility with the plan's control (ii) wording.** The plan says the CGB build on the DMG profile "fails exactly the CGB-only cells". To make that true the guest selects CGB expectations from the header OR the profile, and only a DMG header on the DMG profile expects the frozen DMG behaviour; hence the page-00 DMA cell fails for `banking-cgb.gb` on the DMG profile (ROM expected, `$FF` observed) while `banking-dmg.gb` on the DMG profile passes it. Documented in the manifest `expectation_selection` and the asm header.

**2. Cell layout.** The plan's cell letters map to nine result bytes (C002..C00A) because (c) and (d) split into independently reportable sub-cells so control (ii) can name exactly which cells differ. Documented in the manifest `result_bytes`.

**3. Task 1 tracer content.** The tracer committed (981df8d) holds cell (b) only; Task 2 replaced the ROM bytes and manifest digests in a92464e as the plan describes.

**4. Test dispatch.** `test_banking` gained a 3-argument form (`<case> <fixture dir>`) for the fixture guests; the existing 2-argument core-mutant cases are unchanged.

None of these changes behaviour or scope. No requirement is marked complete: CGB-03 is still declared by plans 10-17 to 10-20.

## Known Stubs

None.

## Threat Flags

None. T-10-19: the pinned archive digest is verified before use, the archive was extracted outside the repository, versions are checked, and CI rebuilds byte-identically. T-10-20: the manifest recipe uses `<work>` placeholders; no home paths or names appear in the fixture files.

## Self-Check: PASSED
