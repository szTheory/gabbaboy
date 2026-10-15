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
at this pinned commit; the rebuild is the provenance. The exact-head Linux
`fixture-repro` run 38502094682 (PR job 115651190879, source revision
`301f1b05577e6d35a4c3a756ded1ec15a4082c8d`) used the digest-pinned RGBDS
1.0.1 Linux archive and reported `result=byte-identical` for all 13
manifest-listed ROMs. The compare-tampered and selfcheck-tampered negative
controls also passed. This closes the provisional macOS-versus-Linux byte
reproduction check; it establishes fixture bytes, not hardware behavior.

`bash tests/scripts/reproduce-age.sh --self-check` validates this record and
the committed digests offline. `--compare` fetches the pinned source, rebuilds
all manifest-listed ROMs, and byte-compares each admitted reference with its
source PNG. `--compare-built DIR` compares an already rebuilt ROM directory
without network access or RGBDS.

## Committed-core verdict measurements

The following software measurements were taken with `test_age --print-signature`
on core revision `db1dd7b9635752c96f99f76fd9f2594ad80af5d1`. Wall times are
local elapsed seconds; they are not hardware observations. Each manifest budget
is twice the measured half-dots rounded up to the next million.

| ROM | Verdict and passing rows | Half-dots to verdict | Wall time (s) |
|---|---|---:|---:|
| `spsw-div-cgbBCE.gb` | pass, 5/5 rows | 22,702,928 | 0.328 |
| `spsw-tima-cgbE.gb` | expected failure, 5/8 rows pass | 12,550,888 | 0.200 |
| `spsw-tima-cgbBC.gb` | expected failure, 7/8 rows pass | 12,549,832 | 0.200 |
| `spsw-stop-prefetch-cgbBCE.gb` | pass, 1/1 row | 1,318,104 | 0.039 |
| `spsw-interrupts-cgbE.gb` | expected failure, 9/11 rows pass | 759,328 | 0.024 |
| `spsw-mode0-cgbBCE.gb` | expected failure, 3/15 rows pass | 1,697,720 | 0.048 |
| `spsw-ch2-lc-delay-cgbBCE.gb` | expected failure, 3/8 rows pass | 35,229,976 | 0.532 |
| `stat-mode-ds-cgbBCE.gb` | expected failure, 0/14 rows pass | 20,731,712 | 0.983 |
| `stat-mode-cgbE.gb` | expected failure, 5/14 rows pass | 11,609,032 | 0.407 |
| `stat-mode-sprites-ds-cgbBCE.gb` | expected failure, 2/16 rows pass | 1,823,912 | 0.094 |
| `stat-mode-sprites-dmgC-cgbBCE.gb` | expected failure, 3/10 rows pass | 1,528,248 | 0.055 |
| `stat-mode-window-ds-cgbBCE.gb` | expected failure, 0/16 rows pass | 2,803,884 | 0.146 |
| `stat-mode-window-cgbBCE.gb` | expected failure, 0/16 rows pass | 2,970,040 | 0.110 |

## Admitted bytes

| File | Size | SHA-256 | Source path | Header `$143` |
|---|---:|---|---|---|
| `spsw-div-cgbBCE.gb` | 32768 | `2c836288b58651f72a335417f11ba346863145dd9996048979ad8e5b9cd0aa7b` | `src/speed-switch/spsw-div-cgbBCE.asm` | `C0` |
| `spsw-tima-cgbE.gb` | 32768 | `3cb0918fb194d2704bb57f2afd5af3be21b5e97e269fde5224c34914d5f5936e` | `src/speed-switch/spsw-tima-cgbE.asm` | `C0` |
| `spsw-tima-cgbBC.gb` | 32768 | `2fcfdc0d8595b642cfc1c16cab42f619a13b9a0d20e668a9c471436573a2e860` | `src/speed-switch/spsw-tima-cgbBC.asm` | `C0` |
| `spsw-stop-prefetch-cgbBCE.gb` | 32768 | `df782c73f08c6778c7b926c6a4ebbd0816c58b53faf4b6abf5b2b812766eab4f` | `src/speed-switch/spsw-stop-prefetch-cgbBCE.asm` | `C0` |
| `spsw-interrupts-cgbE.gb` | 32768 | `bd240315c0b8e7fd5f0d0521785c6c5a10769dae36339e88d777fc507bca44b6` | `src/speed-switch/caution/spsw-interrupts-cgbE.asm` | `C0` |
| `spsw-mode0-cgbBCE.gb` | 32768 | `07eefc27d8bdd98569510ebef662aba388715bbe5ddf9993763fbf1aab290f2e` | `src/speed-switch/spsw-mode0-cgbBCE.asm` | `C0` |
| `spsw-ch2-lc-delay-cgbBCE.gb` | 32768 | `76920fa2f63f5a5b9b8b907b98a78e06410d88fb09491826f3930dedf96cff19` | `src/speed-switch/spsw-ch2-lc-delay-cgbBCE.asm` | `C0` |
| `stat-mode-ds-cgbBCE.gb` | 32768 | `c371664f71cb95b6de9cf9a1ecd4ff80147b5603b08deacea7c9495eb45d1cf0` | `src/stat-mode/stat-mode-ds-cgbBCE.asm` | `C0` |
| `stat-mode-cgbE.gb` | 32768 | `b2789ba04e79c25aba7a947e0d4b7938171457960264702dbaa4826acfdb2fc3` | `src/stat-mode/stat-mode-cgbE.asm` | `80` |
| `stat-mode-sprites-ds-cgbBCE.gb` | 32768 | `3ee5bb3fc7fa724a832a082dd8c4979af5abb3f837dbc489a2f04cdf2332a64d` | `src/stat-mode-sprites/stat-mode-sprites-ds-cgbBCE.asm` | `C0` |
| `stat-mode-sprites-dmgC-cgbBCE.gb` | 32768 | `173ff267a4ecbd2e5bb3bd209f7b08c971900d54382bd6281969c7a3a98507c1` | `src/stat-mode-sprites/stat-mode-sprites-dmgC-cgbBCE.asm` | `80` |
| `stat-mode-window-ds-cgbBCE.gb` | 32768 | `055c641aaf9464b637f6206126a165fa23433fbced0d5fbafa0d3cdb813aaa41` | `src/stat-mode-window/stat-mode-window-ds-cgbBCE.asm` | `C0` |
| `stat-mode-window-cgbBCE.gb` | 32768 | `69fb62868aa256ff79e77cabb88caab9db43dbe302eb6f4628550d99b7ef12da` | `src/stat-mode-window/stat-mode-window-cgbBCE.asm` | `80` |

The source's `Verified:` lines are author-attested hardware observations, not a
reproducible receipt. The new reference PNGs are source data for a later
automated pixel oracle, not targets for human screenshot judgment. Emulator-only
context: the build and digest establish bytes, not hardware behavior.

## Admitted mode-3 source and reference pairs

The first Phase 14 pair is the native normal-speed LCDC case. The ROM and PNG
were copied from the exact pinned commit above and are covered by the upstream
MIT license in `LICENSE.txt`. Source-referenced assets retain the licenses
listed in the upstream record above. The CGB-E `Verified:` line records the
author's expected model result; fixture admission does not mean the emulator
has executed or passed the pixel check.

| ROM | ROM bytes / SHA-256 | ASM source bytes / SHA-256 | Reference PNG / bytes / SHA-256 | Mode and source expectation |
|---|---|---|---|---|
| `m3-bg-lcdc-cgbBCE.gb` | 32768 / `fabdfd1c3f21df7543186a7303ad645a6b342f9c1ea7c1a4b26b4bb9b821b9f4` | `src/m3-bg-lcdc/m3-bg-lcdc.asm` / 287 / `2f2ba3ecd5135265e9b8033ce967135df928d649fc17ad83c6aea073851e54c7` | `references/m3-bg-lcdc-cgbBCE.png` / 587 / `69a0b85a82eddc884ec225a3c6353622876afe589125809d6517439cbeb91cef` | Native CGB, normal speed; `2021-11-29: CPU CGB E - CPU-CGB-06` |
