# Third-party notices

GabbaBoy's core and original project-authored fixtures are licensed under the
MIT License in [`LICENSE`](LICENSE). The three ROMs used in release and
consumer smoke tests are original project-authored material; they are not
commercial game images or third-party ROMs. The separately listed Libbet fixture
is a third-party, zlib-licensed game used only by repository acceptance tests;
it is not installed or packaged. The MIT-licensed Mooneye mbc2/mbc5 derivative ROMs are likewise repository test fixtures only. Each fixture's source, rights, build identity,
and ROM digest are recorded in its manifest and local notice.

GitHub generated source archives retain the admitted licensed fixtures and
their notices, so every third-party fixture below travels with a source archive
together with its license text. The installed and downloaded product packages
remain fixture-free: they carry only the original project-authored tracer,
visible demo and MBC1 continuation fixtures. No fixture below is derived from a
Nintendo boot ROM or a commercial game image, and the table lists only material
that is actually present in the repository tree.

| Material | Rights and distribution | Source / manifest SHA-256 | ROM SHA-256 | Notice SHA-256 |
|---|---|---|---|---|
| Original WRAM tracer | GabbaBoy contributors, MIT; RGBDS 1.0.1 is a build-time tool and is not bundled | `fixtures/tracer/manifest.json`: `59284b6087dc6cb3bf08169b0c3e58444197494521750fac11839632c652cf5c`; source `tracer.asm`: `0c50c8020a7b18d65b17730bd599f1e55754ceb749b3bb2895cfb123e0f58d0b` | `ded6a499118b57539710892d58b4d7ced2269f08d447eed1451201d8ad65ec8d` | `fixtures/tracer/LICENSE.txt`: `8eb246a5af0a83cbc4a264018ea0af31a859540fe5dcf2ec65a46c067d4d144a` |
| Original visible demo | GabbaBoy contributors, MIT; RGBDS 1.0.1 is build-time only | `fixtures/visible-demo/manifest.json`: `8c695ef04d4f65e286aa444d0dfbbc98b354b944fef0dc6ac6dc453c264a31a3`; source `demo.asm`: `930a92621fe3b5a862a50aee6f79bdae3f6bb8d8fe24f546a5d5ab737782d1ee` | `38afb54b40f4b6612906c7a68e367199d8bff135508a39d7acdc996bf3d86530` | `fixtures/visible-demo/LICENSE.txt`: `3ba0e4a2894cdab4de168266be80463105cde267051443fd046946e846d12e96` |
| Original MBC1 continuation fixture | GabbaBoy contributors, MIT; original software fixture, not derived from a commercial game | `fixtures/mbc1-continuation/manifest.json`: `1c25c570be98ece42ff9069635fb07cf4559b578817373ec3bd4d3552e8809d1`; source `continuation.asm`: `ad82e0cd51eeb6d536421d20c4a5b88ee0c019a4e699c2c75de077a20c82ba94` | `f89bf3884ff10a702aa117f2963e6fe9ea8aeac3a9bc003f52b6c5ca6abfbbd2` | `fixtures/mbc1-continuation/LICENSE.txt`: `dcd87663c88f74f55d61a403e752985e8bc63cfa1341d499bb7a521e22a91b20` |
| Libbet and the Magic Floor v0.08 test fixture | Third-party game, zlib; credits Damian Yerrick (program, 2018-2024) and Martin Korth (concept, 2002, 2012); `src/hardware.inc` in its build closure is CC0-1.0; per-asset rights rest on single-author history plus the repository-wide zlib licence, not a per-asset upstream grant; repository test fixture only, not installed or packaged | `fixtures/libbet/manifest.json`: `512d1b4de7656795dba07dc81b025593bd57a74288605eac88684da6b744f08a`; pinned upstream commit `46a765a2c01701bffb8c0b7dd6e4be3a6b193090` | `3607412031c8287cf878299ce96e581e85b852dde703806343b95576fa3ff1a9` | `fixtures/libbet/LICENSE.txt`: `e4fb3c0ef61a0258517e2df3dea5cd7df9d2a2f2c51c9b5082de922b35eea65c` |
| Mooneye mbc2/mbc5 derivative test ROMs (15) | Mooneye Test Suite revision `31510e12eea6286d36eea060a6adde755e1067aa` (Gekkio), MIT; headless-report derivatives with a zero-filled font replacement (see `fixtures/mooneye-mbc/FONT-LICENSE.txt`); WLA-DX is a GPL-2.0-or-later build tool that is not bundled or linked; ROM digests are a local rebuild until the hosted match in Plan 08-07; repository test fixtures only, not installed or packaged | `fixtures/mooneye-mbc/manifest.json`: `9800c795fcf033abd6bda2e171af6c22d27e745f2b5946fc49bd0f9ce2fb5801`; per-ROM digests in `fixtures/mooneye-mbc/SOURCES.md` | see `fixtures/mooneye-mbc/SOURCES.md` | `fixtures/mooneye-mbc/LICENSE.txt`: `8a9a9fe1603b7566d56978c89a6442ae1db2dd96042fb94c20b9647c47afae88` |
| MagenTests out-of-bounds SRAM ROMs (3) | MagenTests release 0.5.0 at pinned commit `3f9c090f16e5a721db776febb9ba7d773e1c819c` (alloncm), MIT; build-time `hardware.inc` (gbdev, commit `21ef22d`) is CC0-1.0; hardware-derived, author-attested; repository test fixtures only, not installed or packaged | `fixtures/magentests/manifest.json`; per-ROM digests in `fixtures/magentests/SOURCES.md` | mbc1 `83f1fc44cc26581163b58fe3df426f119dd5813c2e94a187ee0909d6ace1a8bb`; mbc3 `03e13fa796a9e06fa90f9b396b728c1de9f6e7351aa47a038e33c11d3a8df7dd`; mbc5 `e99f526386f72a8992a72137d0bd9a431b380807b551747bb3baa03421d6f54b` | `fixtures/magentests/LICENSE.txt` |
| AGE CGB speed-switch ROMs | AGE test ROMs by Christoph Sprenger, MIT (Copyright (c) 2021); the Cellphone Font by domsson is CC0; `hardware.inc` is an equates-only CC0 copy with no code bytes; author-attested hardware, repository test fixtures only, not installed or packaged | `fixtures/age/manifest.json`; pinned commit and source paths in `fixtures/age/SOURCES.md` | `spsw-div-cgbBCE.gb` `2c836288b58651f72a335417f11ba346863145dd9996048979ad8e5b9cd0aa7b` | `fixtures/age/LICENSE.txt`; upstream caution in `fixtures/age/WARNING.md` |
| rtc3test MBC3 real-time-clock ROM and `tests.md` | rtc3test release v004 at pinned commit `80ae792bf1b3c3387929b912e6df001af3511e24` (aaaaaa123456789), Unlicense; build-time RGBDS v0.4.2 only; hardware-derived, author-attested; repository test fixture only, not installed or packaged | `fixtures/rtc3test/manifest.json`; details in `fixtures/rtc3test/SOURCES.md` | ROM `a271013fb37ea1d927b854798401320b220d57abb3ca77f3d318ceb8a9def30d`; tests.md `1937b614b49cff4e2e9b3e36aaa888e754ece6eb141ce46406a28f8f005d4172` | `fixtures/rtc3test/LICENSE.txt` |
| Original CGB banking, colour, HBlank-DMA and speed guests | GabbaBoy contributors, MIT; original project-authored assembly, not derived from a commercial game or third-party ROM; RGBDS 1.0.1 is build-time only; repository test fixtures only, not installed or packaged | `fixtures/cgb-banking`, `fixtures/cgb-colour`, `fixtures/cgb-hdma`, `fixtures/cgb-speed` manifests; digests in the manifest and notice digest table below | per-ROM digests in each manifest | each directory's `LICENSE.txt`; digests in the table below |
| Original MBC2, MBC3 RTC and MBC5 battery/banking guests and the v0.1.2 save-envelope vectors | GabbaBoy contributors, MIT; original project-authored software fixtures; repository test fixtures only, not installed or packaged | `fixtures/mbc2-continuation`, `fixtures/mbc3-rtc-continuation`, `fixtures/mbc5-banking`, `fixtures/mbc5-continuation`, `fixtures/save-envelope-v1` manifests | per-ROM digests in each manifest | each directory's `LICENSE.txt`; digests in the table below |
| Mooneye DMG and CGB test ROMs (3 and 9) | Mooneye Test Suite revision `31510e12eea6286d36eea060a6adde755e1067aa` (Gekkio), MIT; headless-report derivatives with a zero-filled font replacement (see `FONT-LICENSE.txt` in each directory); WLA-DX is a GPL-2.0-or-later build tool that is not bundled or linked; repository test fixtures only, not installed or packaged | `fixtures/mooneye` and `fixtures/mooneye-cgb` manifests; digests in the table below | per-ROM digests in each manifest and `SOURCES.md` | each directory's `LICENSE.txt`; digests in the table below |
| SameSuite CGB DMA and APU test ROMs (4 and 70) | SameSuite revision `f15645fb049a47ea235f6d2c9a033e72d8087901` (Lior Halphon), X11 licence; the build-time `hardware.inc` is CC0-1.0 and `hexdigits.2bpp` is covered by the repository X11 licence; RGBDS 1.0.1 is build-time only; repository test fixtures only, not installed or packaged | `fixtures/samesuite/manifest.json`; digest in the table below | per-ROM digests in the manifest | `fixtures/samesuite/LICENSE.txt`; digest in the table below |

### Manifest and notice digests

Every admitted fixture directory has exactly one row below. The digests are the
SHA-256 of that directory's `manifest.json` and `LICENSE.txt` as committed, so a
changed manifest or notice makes this table stale and fails the adoption check.

| Fixture directory | `manifest.json` SHA-256 | `LICENSE.txt` SHA-256 |
|---|---|---|
| `age` | `52a022327cc9b6eb9df2a6383b77cf8c006fca26e789c757c15dc2c58e1e4791` | `f369002da7f08e78ebfc2d9febbfb0316c78f535569e63b84cca8804a234fcef` |
| `cgb-banking` | `99777e6c8ea35df41c25dab2c9e68d72ba3e7255bf174373492d7c2dd5d2cb2d` | `e9c731fc409c8d8d54d361a2bc8fec6029a65119f5508ce111c8a14f7c42985f` |
| `cgb-colour` | `d5ea2b36abb53b9efea4f004bdfaae70dc4e126eb323008e559196adea1854bc` | `8f193ab468875468a514ac17a6cfec9a2e99a7cb9e2c5222f57dd9c646cab6e4` |
| `cgb-hdma` | `450a022cf8afdc6d6b061ac6188dc7ebe18c8c6e8871f0a7751bd291963871e6` | `9fd820fe0ec08928f54ddf9075b64b1a6f0184809de3d145396f124477760564` |
| `cgb-speed` | `5306847c203c018e76752be188658182b16a6efa12347eb8048f8c55d6767383` | `828c9ee2e3b32830dbd8e280a2133da48590490d4314a5778f112d6977cfd3da` |
| `libbet` | `512d1b4de7656795dba07dc81b025593bd57a74288605eac88684da6b744f08a` | `e4fb3c0ef61a0258517e2df3dea5cd7df9d2a2f2c51c9b5082de922b35eea65c` |
| `magentests` | `73478d75c229fee715917e9e415dfd0285944f84cf4c14b65e18e88bc8bf2d77` | `71f1c43ae2cf958dbdec53f0eecb6524a9d7ccaab15785b3f27825abcf43fd1b` |
| `mbc1-continuation` | `1c25c570be98ece42ff9069635fb07cf4559b578817373ec3bd4d3552e8809d1` | `dcd87663c88f74f55d61a403e752985e8bc63cfa1341d499bb7a521e22a91b20` |
| `mbc2-continuation` | `7dd0f0eada9a87e061b33c020669f52e0cafd2311598e599889e47bd2805d2e5` | `dcd87663c88f74f55d61a403e752985e8bc63cfa1341d499bb7a521e22a91b20` |
| `mbc3-rtc-continuation` | `f92e89fb6466fbcafe448d2eab594baa374f5d8bde7b773dfe78263ddd85838e` | `dcd87663c88f74f55d61a403e752985e8bc63cfa1341d499bb7a521e22a91b20` |
| `mbc5-banking` | `017ff445bbd8d26ff542d556062be030b99c961c8b080009d5f0e15ba70472ad` | `6e5513880954a1586eb5f617fda1b92f16ec15c1843edce640e31c18196e2750` |
| `mbc5-continuation` | `125038120297a6367b561b9c0fa200f9f825c9b96d7a6db402966701a4f83a09` | `dcd87663c88f74f55d61a403e752985e8bc63cfa1341d499bb7a521e22a91b20` |
| `mooneye` | `98a1799b8be9c022ac13467a552890fb12bdd706017e42e12c944ec618d60527` | `8a9a9fe1603b7566d56978c89a6442ae1db2dd96042fb94c20b9647c47afae88` |
| `mooneye-cgb` | `6efe380d1eae6f2ef1cfc17375d7e71610c9135fdeb67a1452ecf72b26e02fe9` | `8a9a9fe1603b7566d56978c89a6442ae1db2dd96042fb94c20b9647c47afae88` |
| `mooneye-mbc` | `9800c795fcf033abd6bda2e171af6c22d27e745f2b5946fc49bd0f9ce2fb5801` | `8a9a9fe1603b7566d56978c89a6442ae1db2dd96042fb94c20b9647c47afae88` |
| `rtc3test` | `796d52f1da3af600e10d0a23c96d6dac7e6f7ff26077d1e29b3ce650da459443` | `88d9b4eb60579c191ec391ca04c16130572d7eedc4a86daa58bf28c6e14c9bcd` |
| `samesuite` | `19334fff5cd1427dff335ad22dba7436f58596bf07d5fd48167e4524e07195eb` | `0ec39366cbff2aeed9f06f43941c98974355db52d72940ba1ddc5b7e0de925af` |
| `save-envelope-v1` | `fb4b85d23251a6d259b372424d8ad440966f3ee01ac3d6b6fd4bc7f7b36bbecc` | `af934f0a7ba608ccce037f0b631b41ba1e0b11f3a94ad70c730023953f8b4d94` |
| `tracer` | `59284b6087dc6cb3bf08169b0c3e58444197494521750fac11839632c652cf5c` | `8eb246a5af0a83cbc4a264018ea0af31a859540fe5dcf2ec65a46c067d4d144a` |
| `visible-demo` | `8c695ef04d4f65e286aa444d0dfbbc98b354b944fef0dc6ac6dc453c264a31a3` | `3ba0e4a2894cdab4de168266be80463105cde267051443fd046946e846d12e96` |

The optional macOS player bundles SDL 3.4.18 as a runtime library. SDL is
licensed under its zlib license, copyright Sam Lantinga, 1997–2026. The exact
release source archive is
[`SDL3-3.4.18.tar.gz`](https://github.com/libsdl-org/SDL/releases/download/release-3.4.18/SDL3-3.4.18.tar.gz),
SHA-256 `9c75cf16330322c217dedd2e0609f1124f1b54b8633e763467b4684d0f4334a3`.
Its unmodified `LICENSE.txt` is included in the player package at
`share/licenses/SDL3/LICENSE.txt`; the pinned source's license bytes have
SHA-256 `1c040b8271b37e5076359f8fd54240e371114112924d2df81ef87c7d6a1dfdfd`.
The package verifier compares the bundled license against this digest. SDL is
not a dependency of the portable core or native C/C++ package.

The release's `gabbaboy-notices.txt` attachment is the root MIT license. The
macOS player archive also carries the SDL and fixture notices at the paths
above. The full license texts remain in the source release and the extracted
player package. Verify each downloaded archive against the release's SHA-256
manifest/checksum files before use; see [release and recovery guidance](docs/release.md).
