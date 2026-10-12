# MagenTests fixture sources

## Upstream

- Project: MagenTests, https://github.com/alloncm/MagenTests
- Pinned commit: `3f9c090f16e5a721db776febb9ba7d773e1c819c`
- Release: `0.5.0` (the three `mbc_oob_sram_mbc*.gbc` release assets)
- Source of the tests: `src/mbc_oob_sram/main.asm`
- Licence: MIT, Copyright (c) 2022 alloncm; verbatim text in `LICENSE.txt`

## Build identity of upstream

- Assembler: RGBDS v0.6.1 (commit `69a573923f208d625df589c7a54a18738b07969c`);
  the upstream Makefile passes `rgbasm -L`.
- Include: gbdev `hardware.inc` commit `21ef22d` (CC0).

## Admitted bytes

| File | Size | SHA-256 | Header $147 |
|---|---|---|---|
| `mbc_oob_sram_mbc1.gbc` | 32768 | `83f1fc44cc26581163b58fe3df426f119dd5813c2e94a187ee0909d6ace1a8bb` | $02 |
| `mbc_oob_sram_mbc3.gbc` | 32768 | `03e13fa796a9e06fa90f9b396b728c1de9f6e7351aa47a038e33c11d3a8df7dd` | $12 |
| `mbc_oob_sram_mbc5.gbc` | 32768 | `e99f526386f72a8992a72137d0bd9a431b380807b551747bb3baa03421d6f54b` | $1A |

Each file was downloaded from the release into a fresh empty scratch directory,
checked for size, digest and header byte, then copied. `manifest.json` carries
the same digests and is checked by `cmake/VerifyFixtureManifest.cmake`.

## Rebuild status

Release bytes equal the rebuild: claimed. The hosted `magentests-repro` job in `.github/workflows/fixture-repro.yml` printed `result=byte-identical` in pull-request run 38189871131 at head `fb8972d9e30e6bdf5ff2038e4508ecd3ebfb8522` (read in Plan 09-18). A mismatch is reported, never replaced by rebuilt bytes.

## CI toolchain archive pin

The reproduction job downloads this archive from the gbdev/rgbds v0.6.1 release
and must re-verify it before use. It was hashed without extraction or execution.

rgbds-0.6.1-linux-x86_64.tar.xz sha256 cfaff18e0db0006863de921d6f5a10eb5fb04dba453f967955a8b0f30bc7ba5b
