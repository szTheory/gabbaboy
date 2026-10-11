# Libbet and the Magic Floor fixture sources

This is a third-party, zlib-licensed game vendored as a repository test fixture for the Phase 7 acceptance gate. It is admission evidence for one game. It is not game compatibility, not hardware qualification and not a per-asset upstream licence grant.

## Immutable inputs

- Source: <https://github.com/pinobatch/libbet> at commit `46a765a2c01701bffb8c0b7dd6e4be3a6b193090` (tree `b3e4c329ae2d7b50e3a497f2fa432db5c4095b5d`). The tag `v0.08` is lightweight and mutable, so it is never pinned, and neither is `master`.
- Release asset (provenance only): <https://github.com/pinobatch/libbet/releases/download/v0.08/libbet.gb>, 32768 bytes, release published 2024-01-02T03:33:10Z.
- Vendored ROM `libbet.gb`: SHA-256 `3607412031c8287cf878299ce96e581e85b852dde703806343b95576fa3ff1a9`, 32768 bytes. Header: title `LIBBET`, cartridge type `$00`, CGB flag (`$143`) `$80`, SGB flag (`$146`) `$03`. It was downloaded once into an empty scratch directory and accepted only on that exact digest; required CI never fetches upstream.
- `LICENSE.txt`: the verbatim upstream zlib `LICENSE` followed by a project note that records the credit discrepancy and the Korth permission limitation (SHA-256 `e4fb3c0ef61a0258517e2df3dea5cd7df9d2a2f2c51c9b5082de922b35eea65c`).
- `manifest.json` carries the rights and provenance data and is checked by `tests/scripts/verify-libbet-admission.py` (`python3 -I`, standard library only).

## Asset rights

- Frozen build closure: the makefile plus every tracked file under `src/`, `tilesets/` and `tools/` at the pinned commit, minus `tools/bgrdedent.py` and `tools/unused.py` (45 files). `rights.embedded_assets` holds one record per closure file with path, kind, author, licence, evidence URL at the pinned commit and SHA-256. The ten `tilesets/*` inputs (graphics, the `Libbet.ec` cel map and the `vwf7_cp144p.png` font), the 23 `src/*.z80` ROM sources (including the synthesized-SFX audio driver), `src/global.inc`, `src/hardware.inc` (CC0-1.0) and nine build tools are all covered.
- There is no music. `07-biggar/` and `hopesup/` are outside the build closure.
- The closure rule is a conservative over-approximation. `tilesets/Libbet_title.png` is named by D-04c but no ROM rule in the makefile references it; `tools/uniq.py` is imported only in a disabled branch of `tools/makeborder.py`; `tools/zipup.py` serves only the zip packaging recipe. Their bytes do not reach the ROM, but they keep rights records.
- Credits: `LICENSE` names only "Damian Yerrick 2018". The README and the ROM text add "Martin Korth 2002, 2012; Damian Yerrick 2018, 2024". Both are preserved and the discrepancy is not resolved.
- Martin Korth's porting permission (private message, 2018-10-03, quoted in `05-burndown/note_from_nocash.md`: "Would be fine.") is recorded as a limitation. It is a permission to port the game, not a licence grant.
- Scope note: 285 of 286 upstream commits are by Damian Yerrick and one constants commit is by Eldred Habert. The rights of assets without a per-file notice (the ten tilesets files, `src/intro.z80`, `tools/makeborder.py`, `tools/pitchtable.py`) therefore rest on an inference from single-author history plus the repository-wide zlib licence. No upstream statement grants them per asset. Where a file carries its own notice (zlib, MIT for `tools/savescan.py`, all-permissive for the makefile and two tools, "no rights reserved" for `src/header.z80`, CC0-1.0 for `src/hardware.inc`) the record says so.
- Completeness is checked two ways. Required CI, which has no Libbet source tree, compares the SHA-256 of the sorted `closure_files` list with a constant in the verifier, so a dropped entry fails `closure-digest-mismatch`. The opt-in reproduction job re-derives the closure from the pinned source tree with `--derive-closure` and fails `closure-derivation-mismatch`, naming any omitted or extra path.

## Reproduction

- Local reproduction observed in Plan 07-04 (2026-10-10, macOS on an arm64 host): `bash tests/scripts/reproduce-libbet.sh --compare` rebuilt commit `46a765a2c01701bffb8c0b7dd6e4be3a6b193090` with RGBDS 0.7.0 (archive `rgbds-0.7.0-macos-x86_64.zip`, SHA-256 `f2aee8235db2e9f020708bcb3c74112366ca50f7eb880d7717d95e385a583a16`, x86_64 binaries under Rosetta), Pillow 12.3.0 (wheel `pillow-12.3.0-cp314-cp314-macosx_11_0_arm64.whl`, installed with `pip --require-hashes --no-deps`) and Python 3.14.4. The output was byte-identical: `libbet reproduction: identical sha256=3607412031c8287cf878299ce96e581e85b852dde703806343b95576fa3ff1a9`.
- Before extracting or installing anything the script verified provenance against the registries and printed `provenance verified pypi=https://pypi.org/pypi/pillow/12.3.0/json github=https://api.github.com/repos/gbdev/rgbds/releases/tags/v0.7.0`: every pinned Pillow hash is a published PyPI file digest, and the RGBDS archive is a published asset of the `gbdev/rgbds` v0.7.0 release under `https://github.com/gbdev/rgbds/releases/download/v0.7.0/` (the API reported no digest for it, so the D-02 SHA-256 pin on the downloaded archive is the check). It also re-derived the build closure from the pinned clone before `make` (`libbet closure derived files=45`).
- Commands: `bash tests/scripts/reproduce-libbet.sh --compare`, or the manually dispatched workflow `libbet-repro`. The workflow is `workflow_dispatch`-only, non-required, read-only (`contents: read`, no secrets, no artifact upload) and can be dispatched only once it exists on the default branch. Therefore no hosted Linux reproduction run URL exists yet (D-03) and `reproducibility.hosted_run_url` stays `null`; nothing here claims a hosted run. The Linux archive pin (`f67bc8fdd2b1521f0bed5a3750a09b206de760064fb95bb52790d375c3297210`) and the Linux wheel hashes are configured but not yet exercised.
- Pinned recipe: RGBDS 0.7.0 archives by SHA-256 (Linux `f67bc8fdd2b1521f0bed5a3750a09b206de760064fb95bb52790d375c3297210`, macOS as above), Pillow 12.3.0 hashes in `tests/scripts/libbet-repro-requirements.txt`, then `make libbet.gb` with the 0.7.0 tools and a byte comparison with `libbet.gb`. It never writes inside the repository.
- RGBDS 1.0.1, the single pin used by `fixture-repro.yml` (unchanged), fails to build this tag because it rejects `rgbasm -h`. The two reproductions are therefore separate. Promoting `libbet-repro` to a required check remains an owner choice (deferred).

## Redistribution

- The ROM is a repository test fixture only. It is not installed into the core package and is not shipped in any release or player archive.
- The registered CTests `libbet_not_installed` (digest and name scan of a real install into a scratch prefix) and `libbet_not_installed_selftest` (a copy of the ROM under a neutral name that the scan must find) enforce this. Plan 07-12 adds the packaged-player scan.

## Fallback

If any gate G5 item cannot be closed, admission stops and reports the exact missing item; no other game is substituted inside this phase (D-07). Tobu Tobu Girl becomes eligible only after gate G2 (GBDK 2.96a runtime terms) is separately documented as cleared, and it must then pass the same per-asset checklist. Any other candidate needs an owner decision.
