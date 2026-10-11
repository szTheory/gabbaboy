# Mooneye mbc2/mbc5 derivative fixture sources

These 15 ROMs are the Phase 8 sibling of the frozen `fixtures/mooneye` set. They are built from the same pinned Mooneye revision with the same headless-report patch and zero font, referenced by relative path and SHA-256 from the parent fixture rather than copied (D-24).

## Immutable inputs and builder

- Mooneye Test Suite: commit `31510e12eea6286d36eea060a6adde755e1067aa`, tree `2b8c52424a49a2a7466cf631fd8992c53d0de2fa`. The source declares MIT; the notice is retained in `LICENSE.txt`.
- WLA-DX builder pin: commit `91c52b1f4ef3cc8ba3c0638f7536539579af6a9f`. It is not copied into this directory. `manifest.json` carries no `builder` object; the pin (revision, tree and `git archive` digest) is read from the digest-checked parent manifest `../mooneye/manifest.json`, and `cmake/VerifyMooneyeMbc.cmake` fails with `builder-pin-mismatch` if the parent pin drifts. The GPL-2.0-or-later license covers the build tool only, which is not linked into the fixtures.
- Parent references, each a real repository file with a SHA-256 verified by the digest test:
  - `../mooneye/headless-report.patch`: `c3679ab53b59da14a0f6af1fdd552316ba922762c3a91988f7f8ac4440516e5d` (applied with `patch --batch --fuzz=0 -p1`)
  - `../mooneye/font-source.c`: `5e5b21a1ff66f226e0e3d3ea1630ad4e2d16edbc9fcbb76b70a26b44c2271f52` (emits the 2032-byte zero replacement for `common/font.bin`, digest `23ba65cb93433b65e7ddcae5f8a7dd2ca232491793848644e625875c6dd6ae43`)
  - `../mooneye/manifest.json`: `98a1799b8be9c022ac13467a552890fb12bdd706017e42e12c944ec618d60527` (builder pin)
- No sibling patch exists: the Plan 08-05 tracer showed the `$c000` print pointer does not corrupt any of the 15 pass paths, so the parent patch is used unchanged.
- The ROMs link with `wlalink -nS -d -S` (input-order sections), exactly as the parent derivatives do.

## Source closure

Per ROM, `manifest.json` `source_closure` lists the acceptance source and every file reached through it at the pinned revision:

- `emulator-only/mbc2/*.s` (7 ROMs) and `emulator-only/mbc5/*.s` (8 ROMs);
- `common/harness/mbc2_rom.s` or `common/harness/mbc5_rom.s`, only for the `rom_*` ROMs (the `bits_*` and `ram` tests do not include a harness file);
- `common/common.s`, `common/hardware.s`, `common/macros.s` and the listed `common/lib/*.s` files.

The only modified harness files are the two the parent patch already changes (`common/common.s`, `common/lib/quit.s`). Test assertions, constants and callbacks are unchanged. `common/font.bin` is the sole substituted asset (see `FONT-LICENSE.txt`).

## ROM table

| ROM | Size (bytes) | SHA-256 |
|---|---:|---|
| `mbc2_bits_ramg.gb` | 32768 | `7eb87a09e2214693d978b754957f6dc09f79095fb1bbca7089c9ca7e563115ae` |
| `mbc2_bits_romb.gb` | 65536 | `f382f82c0025093b52575bcd35715131b681392f28a81d88180db973b5ff8090` |
| `mbc2_bits_unused.gb` | 262144 | `d33bed573c162b3384048dddc10c3b0d0d89dbb9023d1608cd70286988c0fa77` |
| `mbc2_ram.gb` | 32768 | `5b82d04e284a0c396271e4df0d345c7383d1c86467675a272d9a4e286f790f13` |
| `mbc2_rom_512kb.gb` | 65536 | `4c7a8a58e3bf5a45afb71b079aead912f336a13972ff93b59f964bedbc87fda5` |
| `mbc2_rom_1Mb.gb` | 131072 | `7eba692d8f426d1b6187095a9c14a99ef5ea80534d996949bca8bf0bd9e77cc3` |
| `mbc2_rom_2Mb.gb` | 262144 | `32530509d8182718b005e183259cb6eaeeb7db15c6b634ebdc362016591dadec` |
| `mbc5_rom_512kb.gb` | 65536 | `701cce7a923f2291756c364ad587b0f3a1ca3c12ed904e61323614ce6ddddc0b` |
| `mbc5_rom_1Mb.gb` | 131072 | `9d9d21129bfc91b5c22d9d6a30a08bdee309786ad21532cb8817e19295fffe69` |
| `mbc5_rom_2Mb.gb` | 262144 | `5a152aa873f104f6acf865f642b1cf86abc5f2cceea81118f238794aaf9f70ab` |
| `mbc5_rom_4Mb.gb` | 524288 | `4173c92d61533ed5f3cdd8f2ca83d3701ca042b28bceeed1021a79065368fa86` |
| `mbc5_rom_8Mb.gb` | 1048576 | `176cd6f9a16519ba30f7d0cec3d46226ef304f3ad54e41d6d23974a03e6157a1` |
| `mbc5_rom_16Mb.gb` | 2097152 | `65602bf590e9c2f5d22e3db3597c95d763a8fe562556bac9c8a82baf3ed3a59e` |
| `mbc5_rom_32Mb.gb` | 4194304 | `f37b1e7af46d69e5c42df0e7e421e306b48b6c6e789cb35e091e41c0fe67e668` |
| `mbc5_rom_64Mb.gb` | 8388608 | `f1148d3cc631e330b991b3f34d728de5b3789b00b80b9778fb08a9bbb59efef7` |

Each size equals `32768 << $148` for the ROM's header. The runner admits this suite only by the SHA-256 of the raw bytes of `manifest.json`.

## Provenance status of the digests (D-25)

These digests are a **local rebuild** (Darwin/arm64, pinned WLA-DX 91c52b1f). The hosted Linux/x86_64 leg that must reproduce the same bytes is Plan 08-07; until it matches, the digests carry no cross-host reproduction claim. The pinned linker's tied-section ordering is libc-dependent in its default mode (see `../mooneye/SOURCES.md`); the `-nS` recipe is what is expected to make the hosted bytes agree, and that is exactly what 08-07 must show rather than assume.

## Reproduction

```
bash tests/scripts/reproduce-mooneye-mbc.sh --compare fixtures/mooneye-mbc
```

The command is explicitly networked (it fetches the pinned sources), refuses to write build products inside the working tree, and fails unless every rebuilt ROM equals its checked-in bytes. Ordinary CTest consumes only the checked-in `.gb` files and never invokes a network, compiler or assembler.

## Redistribution scope

The ROMs, `LICENSE.txt` and `FONT-LICENSE.txt` are repository test fixtures only. They are not installed, not packaged and not part of any release artifact; the installed-prefix and package inventories that prove this are Plan 08-07's.
