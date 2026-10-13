# Mooneye CGB-profile derivative fixture sources

These ROMs are the Phase 10 sibling of the frozen `fixtures/mooneye` set and of `fixtures/mooneye-mbc` (D-26). They are built from the same pinned Mooneye revision with the same headless-report patch and zero font, referenced by relative path and SHA-256 from the parent fixture rather than copied.

## Upstream files (Mooneye Test Suite commit `31510e12eea6286d36eea060a6adde755e1067aa`)

| ROM | Upstream source | Upstream header result |
|---|---|---|
| `boot_regs-cgb.gb` | `misc/boot_regs-cgb.s` | pass: CGB |
| `boot_div-cgbABCDE.gb` | `misc/boot_div-cgbABCDE.s` | pass: CGB ABCDE (fail: CGB 0) |
| `boot_hwio-C.gb` | `misc/boot_hwio-C.s` | pass: CGB, AGB, AGS |
| `unused_hwio-C.gb` | `misc/bits/unused_hwio-C.s` | pass: CGB, AGB, AGS |

Note the `misc/bits/` subpath of `unused_hwio-C`. None of the four defines `CART_CGB`, so `common.s` links the DMG-compatible header and `$143` is `0x00` (CGB-profile compat mode). The reproduction script asserts bit 7 of `$143` is clear for every ROM and prints the byte.

## Immutable inputs and builder

- Mooneye Test Suite: commit `31510e12eea6286d36eea060a6adde755e1067aa`, tree `2b8c52424a49a2a7466cf631fd8992c53d0de2fa`. The source declares MIT; the notice is retained in `LICENSE.txt`.
- WLA-DX builder pin: commit `91c52b1f4ef3cc8ba3c0638f7536539579af6a9f`, built from source (wla-gb 10.7, wlalink 5.22). It is not copied into this directory; `manifest.json` carries no `builder` object and the pin (revision, tree and `git archive` digest) is read from the digest-checked parent manifest `../mooneye/manifest.json`. The GPL-2.0-or-later license covers the build tool only, which is not linked into the fixtures.
- Parent references, each a real repository file with a SHA-256:
  - `../mooneye/headless-report.patch`: `c3679ab53b59da14a0f6af1fdd552316ba922762c3a91988f7f8ac4440516e5d` (applied with `patch --batch --fuzz=0 -p1`; it applies to all four sources without a reject)
  - `../mooneye/font-source.c`: `5e5b21a1ff66f226e0e3d3ea1630ad4e2d16edbc9fcbb76b70a26b44c2271f52` (emits the 2032-byte zero replacement for `common/font.bin`, digest `23ba65cb93433b65e7ddcae5f8a7dd2ca232491793848644e625875c6dd6ae43`)
  - `../mooneye/manifest.json`: `98a1799b8be9c022ac13467a552890fb12bdd706017e42e12c944ec618d60527` (builder pin)
- No sibling patch exists; the parent patch is used unchanged.
- The ROMs link with `wlalink -nS -d -S` (input-order sections), exactly as the parent derivatives do.
- `original_sha256` in the manifest is the digest of the same source assembled without the patch and with the upstream font. The reproduction script recomputes it; the unpatched ROMs and the upstream font are never committed.

## Derivation steps

1. Fetch the pinned Mooneye and WLA-DX revisions into a temporary directory outside the repository and verify their tree hashes and the WLA-DX archive digest.
2. Build `wla-gb` and `wlalink` and check their version strings.
3. Generate the zero font from `../mooneye/font-source.c` and check its digest.
4. Apply the parent headless-report patch with `--fuzz=0`.
5. Assemble each source with `wla-gb -I common` and link with `wlalink -nS -d -S`.
6. Assert `$143` bit 7 is clear, then compare byte for byte with the committed ROM.

## Reproduction

```
bash tests/scripts/reproduce-mooneye-cgb.sh --compare fixtures/mooneye-cgb
```

The command is explicitly networked, refuses to write build products inside the working tree, and prints `result=byte-identical` only when every rebuilt ROM equals its checked-in bytes and the unpatched-original digests match the manifest. Ordinary CTest consumes only the checked-in `.gb` files.

## Redistribution scope

The ROMs, `LICENSE.txt` and `FONT-LICENSE.txt` are repository test fixtures only. They are not installed, not packaged and not part of any release artifact (the install-tree scan is added in Plan 10-15). No Nintendo boot ROM is involved: the tests check state a boot ROM would leave, which the core supplies by policy.
