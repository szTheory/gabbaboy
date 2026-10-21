---
phase: 10-cgb-profile-banking-and-register-visibility
plan: 15
subsystem: fixtures-tests-ci
tags: [cgb, mooneye, verifier, install-scan, ci, tamper-control]
requires: [10-14]
provides: [cmake/VerifyMooneyeCgb.cmake digest and inventory modes, six cgb_mooneye_* CTest cases, mooneye-cgb-repro CI job]
affects: [16, 20]
key-files:
  created: [cmake/VerifyMooneyeCgb.cmake]
  modified: [tests/CMakeLists.txt, tests/expected-tests.txt, .github/workflows/fixture-repro.yml]
key-decisions:
  - "pc-table mode and the gbb:cgb-rows markers are deferred to Plan 10-16; the verifier rejects any other mode"
  - "The scan keeps the default 'mooneye' label, so the existing 'mooneye-installed:' token and success line are reused for the CGB manifest"
requirements-completed: []
status: complete
commits: 3
plan_head_before: da99c31ed373dece48ef5a9e85cc592f88a62bc8
plan_head_after: 8c08fbb2f9fd81cc6190b4b46b4020ce57b5b774
actuals:
  tokens: 14000
  tasks: 3
  commits: 3
duration: 15 min
completed: 2026-10-12
coverage:
  - id: 10-15-digest-verifier
    description: "Digest verifier: every committed CGB Mooneye ROM is size- and SHA-256-checked against its manifest row, plus parent-reference digests and suite pin"
    human_judgment: false
    verification:
      - kind: unit
        ref: "ctest --test-dir build/phase15_1_14 --output-on-failure -R '^cgb_mooneye_fixture_digest$'"
        status: pass
      - kind: unit
        ref: "ctest --test-dir build/phase15_1_14 --output-on-failure -R '^cgb_mooneye_digest_tamper$'"
        status: pass
  - id: 10-15-inventory
    description: "Inventory verifier: exact four ids, categories, expect values and 0xFF76 stop address on the two expected-unsupported rows"
    human_judgment: false
    verification:
      - kind: unit
        ref: "ctest --test-dir build/phase15_1_14 --output-on-failure -R '^cgb_mooneye_inventory$'"
        status: pass
      - kind: unit
        ref: "ctest --test-dir build/phase15_1_14 --output-on-failure -R '^cgb_mooneye_inventory_tamper$'"
        status: pass
  - id: 10-15-install-exclusion
    description: "Install-exclusion scan over the install tree with a planted-ROM control"
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest --test-dir build/phase15_1_14 --output-on-failure -R '^cgb_mooneye_not_installed$'"
        status: pass
      - kind: integration
        ref: "ctest --test-dir build/phase15_1_14 --output-on-failure -R '^cgb_mooneye_not_installed_selftest$'"
        status: pass
  - id: 10-15-ci-wiring
    description: "fixture-repro.yml parses and contains the mooneye-cgb-repro job and compare command; hosted execution remains unverified"
    human_judgment: false
    verification:
      - kind: other
        ref: "/usr/bin/ruby -e 'require \"yaml\"; source=File.read(\".github/workflows/fixture-repro.yml\"); YAML.parse(source); abort unless [\"mooneye-cgb-repro:\", \"bash tests/scripts/reproduce-mooneye-cgb.sh --compare fixtures/mooneye-cgb\"].all? { |item| source.include?(item) }'"
        status: pass
---

# Phase 10 Plan 15: Mooneye CGB Verification Wiring Summary

A fail-closed CMake verifier for the four Mooneye CGB derivatives, an install-tree exclusion scan with a planted-ROM control, and a CI rebuild job.

## Accomplishments

- `cmake/VerifyMooneyeCgb.cmake` (adapted from the mbc verifier): digest mode checks size, SHA-256, required corpus files, the three parent references and the suite pin; inventory mode pins the four ids, categories, `pass`/`expected-unsupported` expectations and `0xFF76` stop address, and requires `required_roms` to equal the fixture ROMs in order.
- Six CTest names, all `cgb_`-prefixed (D-27): `cgb_mooneye_fixture_digest`, `cgb_mooneye_inventory`, `cgb_mooneye_digest_tamper`, `cgb_mooneye_inventory_tamper`, `cgb_mooneye_not_installed`, `cgb_mooneye_not_installed_selftest`. All in `tests/expected-tests.txt`.
- Tamper controls are configure-time mutants of the manifest (one flipped digest nibble; one duplicated fixture id), each expecting exit code exactly 1 and a named token.
- `cgb_mooneye_not_installed` runs `ScanForbiddenFixtures.cmake` with the CGB manifest over the libbet install tree; the selftest plants `boot_regs-cgb.gb` as `share/payload.bin` and requires detection by bytes.
- `.github/workflows/fixture-repro.yml` gains `mooneye-cgb-repro` (copy of `mooneye-mbc-repro`, same pinned actions, env names match `reproduce-mooneye-cgb.sh`), running `bash tests/scripts/reproduce-mooneye-cgb.sh --compare fixtures/mooneye-cgb` and uploading evidence.

## Verification

- Full suite `ctest --preset phase1`: 100% passed, 512 of 512 (169.9 s).
- The hosted `mooneye-cgb-repro` job has NOT been run; only YAML syntax and structure were validated locally. Hosted proof is left to the phase PR (10-20).

## Fresh evidence recheck (2026-10-21)

All six mapped `cgb_mooneye_*` CTests passed in the isolated build, including digest and inventory rejection controls and the install-tree scan. `/usr/bin/ruby` parsed the current workflow YAML, and the expected job and compare command are present. The hosted `mooneye-cgb-repro` job remains unrun; the checks here establish local configuration only.

## Deviations from Plan

None - plan executed exactly as written. The tracer verify re-ran end to end before expansion.

## Known Stubs

None.

## Threat Flags

None.

## Self-Check: PASSED

Created/modified files exist; commits 61956f8, 9d6c42f, 8c08fbb are ancestors of HEAD; acceptance greps passed (`mooneye-cgb-repro:` count 1, scan names count 2).
