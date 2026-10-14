# MagenTests fixture sources

## Upstream

- Project: MagenTests, https://github.com/alloncm/MagenTests
- Pinned commit: `3f9c090f16e5a721db776febb9ba7d773e1c819c`
- Release: `0.5.0`
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

Phase 11 additions (release 0.5.0, downloaded 2026-10-12 into a fresh scratch directory, size, digest and `$143` checked before copying):

| File | Size | SHA-256 | Header $143 | Source dir |
|---|---|---|---|---|
| `bg_oam_priority.gbc` | 32768 | `1b2132b354370b1eff22d867da67d8f59eb94872fdad00c277203d8d8b67b84c` | $C0 | `src/color_bg_oam_priority` |
| `oam_internal_priority.gbc` | 32768 | `f54fb6366b3ea8597d07917729aeb358d961ae6ece7cecd003fe9c45dcb97fe7` | $C0 | `src/oam_internal_priority` |
| `ppu_disabled_state.gbc` | 32768 | `4808fe834ea6a6344d74f007a45628c405aca5acd13d6c25f76d02f442f1eea6` | $80 | `src/ppu_disabled_state` |

Each file was downloaded from the release into a fresh empty scratch directory,
checked for size, digest and header byte, then copied. `manifest.json` carries
the same digests and is checked by `cmake/VerifyFixtureManifest.cmake`.

## Reproduction

`bash tests/scripts/reproduce-magentests.sh --self-check` (offline) checks that the manifest rows
(`source_dir`, `rgbfix_options`) and the script's per-ROM rebuild table name the same files and
that committed digests match. `--compare` rebuilds all six ROMs with RGBDS v0.6.1 at the pinned
commit and prints `result=byte-identical` or `result=differs <file> <rebuilt> <committed>`. The
hosted `magentests-repro` job in `.github/workflows/fixture-repro.yml` reports the result for the
three Phase 11 ROMs; a "differs" result is reported, never fixed by replacing committed bytes
(RESEARCH A4). Until that job has run on this branch the Phase 11 ROMs are admitted by release
digest only, not by a verified rebuild.

## Rebuild status

Release bytes equal the rebuild: claimed. The hosted `magentests-repro` job in `.github/workflows/fixture-repro.yml` printed `result=byte-identical` in pull-request run 38189871131 at head `fb8972d9e30e6bdf5ff2038e4508ecd3ebfb8522` (read in Plan 09-18). A mismatch is reported, never replaced by rebuilt bytes.

## CI toolchain archive pin

The reproduction job downloads this archive from the gbdev/rgbds v0.6.1 release
and must re-verify it before use. It was hashed without extraction or execution.

rgbds-0.6.1-linux-x86_64.tar.xz sha256 cfaff18e0db0006863de921d6f5a10eb5fb04dba453f967955a8b0f30bc7ba5b

## CGB HBlank VRAM DMA admission

`hblank_vram_dma.gbc` is the MagenTests 0.5.0 release asset from the pinned
repository revision above. Its release bytes are 32768 bytes with SHA-256
`e8124ce687d37a2402e20af92af1299610bfbda0871d605084c0bba2bf57135c`; the
ROM header is cartridge type `$00` and CGB flag `$C0`. The source Makefile's
RGBDS v0.6.1 recipe uses `rgbasm -L`, include paths `src/hblank_vram_dma` and
`hardware.inc/`, then `rgblink`, followed by `rgbfix -v -p 0 --color-only
--mbc-type ROM`.

The complete build and rights closure is pinned in `manifest.json`:

| Pinned input | SHA-256 | License / role |
|---|---|---|
| `Makefile` | `f1c9d27f09fd751f853d91f458a222851ae5c7ea61f6ec53572a4cf779814418` | MagenTests build recipe |
| `LICENSE` | `cfff09304691f49ac2ffb3453b5adc3a4abe9605387b4b89b4f0d384963a2042` | MagenTests MIT notice, copied verbatim to `LICENSE.txt` |
| `src/common.asm` | `88fc0a6ca5af136a3e948e5b8abab2700140442cf0c0f1871244c835cfd23abb` | Shared routines included by the guest |
| `src/hblank_vram_dma/main.asm` | `e242af4afb63702a41960de4863d732d51220ac649b2e6b8697bedfddc1e9f77` | Guest program and HDMA/status flow |
| `src/hblank_vram_dma/graphics_data.asm` | `37c55f20c064b9b4dce00516b9938057a342019b7b850c2014e7c3c1cad6cba9` | Guest tiles and transfer maps |
| `hardware.inc/hardware.inc` | `6463577e5aba17cdf678eebf206f9fc40e0372c8d8a26a6dc7647c9e7a5c3964` | Include from gbdev/hardware.inc commit `21ef22d01ac55151160f3d98110c2da8846a96b2` |
| `hardware.inc/LICENSE` | `36ffd9dc085d529a7e60e1276d73ae5a030b020313e6c5408593a6ae2af39673` | CC0-1.0 notice excerpt is retained in `LICENSE.txt` |

The release's root `LICENSE` is MIT, Copyright (c) 2022 alloncm. The included
`hardware.inc` file carries CC0-1.0; both notices are present in
`LICENSE.txt`. The row is applicable to the bootless
`GBB_PROFILE_CGB_CPU_E` selected model and is marked SameBoy-assisted
differential evidence. It does not qualify physical CGB-E timing or hardware.

RGBDS v0.6.1 official release archives used by `--compare-pinned` are
verified before private-cache extraction (no global installation):

rgbds-0.6.1-macos-x86-64.zip sha256 65929a5483c89b20955df0d78ceb87744d8ad0cf7c80919f6ee9ef90fc55c08d

On Apple Silicon the pinned x86-64 binaries run under Rosetta. `--compare-pinned`
rebuilds the full seven-ROM table and compares every output byte with its
committed release asset. `--self-test` validates a clean copy and rejects
changed release digest, missing row or source pin, missing license, and altered
build options with distinct diagnostics.
