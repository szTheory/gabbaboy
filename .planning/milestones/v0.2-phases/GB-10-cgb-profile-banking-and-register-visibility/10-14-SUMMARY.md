---
phase: 10-cgb-profile-banking-and-register-visibility
plan: 14
subsystem: fixtures-tests
tags: [cgb, mooneye, fixture, wla-dx, provenance, compat-mode]
requires: [10-13]
provides: [fixtures/mooneye-cgb four digest-pinned Mooneye derivatives, reproduce-mooneye-cgb.sh with --build/--compare/--facts, ELIGIBILITY record]
affects: [15, 16]
key-files:
  created: [fixtures/mooneye-cgb/manifest.json, fixtures/mooneye-cgb/ELIGIBILITY.md, fixtures/mooneye-cgb/SOURCES.md, fixtures/mooneye-cgb/LICENSE.txt, fixtures/mooneye-cgb/FONT-LICENSE.txt, fixtures/mooneye-cgb/boot_regs-cgb.gb, fixtures/mooneye-cgb/boot_div-cgbABCDE.gb, fixtures/mooneye-cgb/boot_hwio-C.gb, fixtures/mooneye-cgb/unused_hwio-C.gb, tests/scripts/reproduce-mooneye-cgb.sh]
  modified: [.gitattributes, .gitignore]
requirements-completed: []
status: complete
commits: 2
plan_head_before: df7c2e84db4fe3788f5048338b89afc1d9c2b7c9
plan_head_after: ebdc39761870f7960f217231ec00fc7b7ef681b9
actuals:
  tokens: 30000
  tasks: 2
  commits: 2
duration: 25 min
completed: 2026-10-12
coverage:
  - id: 10-14-mooneye-rebuild
    description: "Four Mooneye CGB derivatives rebuilt byte-identically from pinned Mooneye 31510e12 and WLA-DX 91c52b1f with the parent patch (fuzz=0) and zero font"
    human_judgment: false
    verification:
      - kind: other
        ref: "bash tests/scripts/reproduce-mooneye-cgb.sh --compare fixtures/mooneye-cgb"
        status: pass
  - id: 10-14-manifest-digests
    description: "Manifest sha256 equals each committed ROM; original_sha256 recomputed by the script"
    human_judgment: false
    verification:
      - kind: unit
        ref: "ctest --test-dir build/phase15_1_14 --output-on-failure -R '^cgb_mooneye_fixture_digest$'"
        status: pass
      - kind: other
        ref: "bash tests/scripts/reproduce-mooneye-cgb.sh --compare fixtures/mooneye-cgb"
        status: pass
  - id: 10-14-compat-header
    description: "Compat-mode check: every ROM has $143 bit 7 clear"
    human_judgment: false
    verification:
      - kind: other
        ref: "bash tests/scripts/reproduce-mooneye-cgb.sh --compare fixtures/mooneye-cgb"
        status: pass
  - id: 10-14-tamper-control
    description: "Historical reference 'manual tamper-and-restore run, Task 1' remains recorded; the current digest tamper control is separate because --compare accepts only the canonical fixture directory"
    human_judgment: false
    verification:
      - kind: unit
        ref: "ctest --test-dir build/phase15_1_14 --output-on-failure -R '^cgb_mooneye_digest_tamper$'"
        status: pass
---

# Phase 10 Plan 14: Mooneye CGB fixtures Summary

Four Mooneye CGB-profile derivatives (boot_regs-cgb, boot_div-cgbABCDE, boot_hwio-C, bits/unused_hwio-C) built from pinned Mooneye 31510e12 with the parent headless patch and zero font, committed with rights files, a sibling manifest and a networked byte-identical reproduction script.

## Accomplishments

- `tests/scripts/reproduce-mooneye-cgb.sh` (`--build`, `--compare`, `--facts`), copied from the mbc analog: outside-repo guard, parent files pinned by sha256, WLA-DX built from the pinned source with version check, patch `--batch --fuzz=0 -p1`. It asserts `$143` bit 7 clear per ROM, rebuilds each unpatched original for the manifest `original_sha256`, and prints `result=byte-identical roms=N` only when all ROMs match.
- Tracer (boot_regs-cgb) committed first with rights files, SOURCES.md, manifest and `.gitattributes` binary line; then the other three ROMs and ELIGIBILITY.md.
- Manifest: suite revision/tree, three parent_references, replacement_asset, per-fixture id, rom, size_bytes, sha256, original_sha256, source_path, category, model_pass `cgb-cpu-e`, target_revision (`CGB-A..E` for boot_div, never CGB-E alone), expect (`pass` for boot_regs-cgb and boot_div-cgbABCDE; `expected-unsupported`, stop `unsupported-bus` at `0xFF76` for boot_hwio-C and unused_hwio-C).
- ELIGIBILITY.md: inventory with `$143` values, evidence class per source header, the C3 paragraph (FF76 proves earlier rows for boot_hwio-C only), and the not-admitted list (unused_hwio-GS, oam_dma/sources-GS, boot_*-cgb0 and -A, AGE, SameSuite).

## Measured facts (for Plan 10-16)

`--facts` on the built ROMs (Darwin/arm64): all four `size=32768`, `header143=00`, `header147=00`. `result_pc`: boot_regs-cgb `4327`, boot_div-cgbABCDE `4327`, boot_hwio-C `4067`, unused_hwio-C `4070`. Quit sites: boot_regs-cgb `invalid_sp@quit_inline_1=01da`; boot_hwio-C `01ce`, `01f5`; unused_hwio-C `1a02`, `1a31`; boot_div-cgbABCDE none (shared quit_check_asserts). These are not yet written into the manifest or the ELIGIBILITY table; the plan leaves them to Plan 10-16.

## Deviations from Plan

**1. [Rule 3 - Blocking] `.gitignore` ignored the new ROMs**
- **Found during:** Task 1 commit (`git add` refused `boot_regs-cgb.gb`; `*.gb` is ignored with per-file negations).
- **Fix:** Added four negation lines for `fixtures/mooneye-cgb/*.gb`, matching the mooneye-mbc convention.
- **Files modified:** `.gitignore` (committed with Task 1, 7f60a8e).

**2. [Scope note] original_sha256 computation added to the script**
- The plan lists `original_sha256` per fixture but the mbc analog has none. The script now assembles the unpatched source with the upstream font in the work directory (never committed) and `--compare` fails with `DIFFERENT-ORIGINAL` if the manifest value differs.

**3. [Scope note] No result_pc in the manifest rows**
- The plan says result_pc is filled by `--facts` in Plan 10-16, so the rows omit it and the ELIGIBILITY table cells read "pending Plan 10-16".

**4. Tracer stage used a one-ROM list**
- The Task 1 commit had `roms=(boot_regs-cgb)` so its `--compare` verify passed with one committed ROM; Task 2 extended the list to four.

**Total deviations:** 1 auto-fixed (Rule 3), 3 scope notes. **Impact:** none on plan outputs.

## Evidence and verification

- `--compare fixtures/mooneye-cgb`: four `match` lines, `result=byte-identical roms=4`, all `header143` values `00`. The parent patch applied with `--fuzz=0` and no reject (A3 not triggered).
- Manifest digest check: `manifest digests ok 4`.
- Acceptance greps: `CGB-A..E` count 1 in manifest; `unused_hwio-GS` present in ELIGIBILITY.md; `boot_hwio-C only` count 1; `git check-attr binary` prints `set`.
- Negative control: flipping one byte in the committed boot_regs-cgb.gb made `--compare` print `DIFFERENT ...` and `result=different` (exit 1); file restored and verified with `cmp`.
- Full suite after the last change: `ctest --preset phase1` 506 of 506 passed. No CTest names were added (registered in Plan 10-15), so `tests/expected-tests.txt` is unchanged.
- Hosted Linux rebuild is not yet recorded: the digests come from a local Darwin/arm64 build; the CI leg is added in Plan 10-15 (as with the mbc fixtures, D-25 provenance status: local rebuild only).

## Fresh evidence recheck (2026-10-21)

The current `--compare` run reported `result=byte-identical roms=9`; it included all four Plan 10-14 fixture IDs, and all nine current ROM headers reported `$143=00`. The current manifest digest CTest and the separate digest-tamper CTest passed. A fresh raw-ROM byte-flip attempt on a temporary copy was refused before comparison because the script requires the canonical `fixtures/mooneye-cgb` directory. The original Task 1 byte-flip result above remains historical; no fresh raw-ROM mutation or hosted/hardware result is claimed.

## Known Stubs

None. ELIGIBILITY.md per-ROM program-counter cells say "pending Plan 10-16" by design (documented hand-off, not a code stub).

## Threat Flags

None. T-10-21 mitigations applied: pinned revisions and trees, parent patch and font by sha256, `--fuzz=0`, temp-dir builds outside the repo, byte-identical compare. T-10-SC: no package installs.

## Self-Check: PASSED

All ten created files exist; commits 7f60a8e and ebdc397 are ancestors of HEAD; plan-level verification re-run green.
