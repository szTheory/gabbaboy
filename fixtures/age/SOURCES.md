# AGE fixture sources

## Upstream identity

- Project: AGE test ROMs, https://github.com/c-sp/age-test-roms
- Pinned commit: `1f5bc10e2cb60b86c19f8d0287ff78f410c4f639`
- Pinned tree: `2fece1a678edb18c1664efd7328a430a79c70be4`
- License: MIT, Copyright (c) 2021 Christoph Sprenger; verbatim in `LICENSE.txt`.
- `src/_include/hardware.inc` is copied for its equates only under CC0; it contributes no code bytes.
- The included Cellphone Font is by domsson under CC0.

## Reproduction

The upstream Makefile recipe is `rgbasm -Weverything -I src -I src/_include`,
`rgblink -t`, and `rgbfix -v -p 255`, using RGBDS 1.0.1. Sources are used only
at this pinned commit; the rebuild is the provenance. The macOS digests are
provisional until the Linux `fixture-repro` leg confirms them.

`bash tests/scripts/reproduce-age.sh --self-check` validates this record and
the committed digest offline. `--compare` fetches the pinned source and rebuilds
all manifest-listed ROMs. `--compare-built DIR` compares an already rebuilt
directory without network access or RGBDS.

## Admitted bytes

| File | Size | SHA-256 | Source path | Header `$143` |
|---|---:|---|---|---|
| `spsw-div-cgbBCE.gb` | 32768 | `2c836288b58651f72a335417f11ba346863145dd9996048979ad8e5b9cd0aa7b` | `src/speed-switch/spsw-div-cgbBCE.asm` | `C0` |
| `spsw-tima-cgbE.gb` | 32768 | `3cb0918fb194d2704bb57f2afd5af3be21b5e97e269fde5224c34914d5f5936e` | `src/speed-switch/spsw-tima-cgbE.asm` | `C0` |

The source's `Verified:` lines are author-attested hardware observations, not a
reproducible receipt. Emulator results are numeric; no screenshot comparison is
used. Emulator-only context: the build and digest establish bytes, not hardware
behavior.
