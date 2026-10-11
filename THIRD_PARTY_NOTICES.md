# Third-party notices

GabbaBoy's core and original project-authored fixtures are licensed under the
MIT License in [`LICENSE`](LICENSE). The three ROMs used in release and
consumer smoke tests are original project-authored material; they are not
commercial game images or third-party ROMs. The separately listed Libbet fixture
is a third-party, zlib-licensed game used only by repository acceptance tests;
it is not installed or packaged. Each fixture's source, rights, build identity,
and ROM digest are recorded in its manifest and local notice.

| Material | Rights and distribution | Source / manifest SHA-256 | ROM SHA-256 | Notice SHA-256 |
|---|---|---|---|---|
| Original WRAM tracer | GabbaBoy contributors, MIT; RGBDS 1.0.1 is a build-time tool and is not bundled | `fixtures/tracer/manifest.json`: `59284b6087dc6cb3bf08169b0c3e58444197494521750fac11839632c652cf5c`; source `tracer.asm`: `0c50c8020a7b18d65b17730bd599f1e55754ceb749b3bb2895cfb123e0f58d0b` | `ded6a499118b57539710892d58b4d7ced2269f08d447eed1451201d8ad65ec8d` | `fixtures/tracer/LICENSE.txt`: `8eb246a5af0a83cbc4a264018ea0af31a859540fe5dcf2ec65a46c067d4d144a` |
| Original visible demo | GabbaBoy contributors, MIT; RGBDS 1.0.1 is build-time only | `fixtures/visible-demo/manifest.json`: `8c695ef04d4f65e286aa444d0dfbbc98b354b944fef0dc6ac6dc453c264a31a3`; source `demo.asm`: `930a92621fe3b5a862a50aee6f79bdae3f6bb8d8fe24f546a5d5ab737782d1ee` | `38afb54b40f4b6612906c7a68e367199d8bff135508a39d7acdc996bf3d86530` | `fixtures/visible-demo/LICENSE.txt`: `3ba0e4a2894cdab4de168266be80463105cde267051443fd046946e846d12e96` |
| Original MBC1 continuation fixture | GabbaBoy contributors, MIT; original software fixture, not derived from a commercial game | `fixtures/mbc1-continuation/manifest.json`: `1c25c570be98ece42ff9069635fb07cf4559b578817373ec3bd4d3552e8809d1`; source `continuation.asm`: `ad82e0cd51eeb6d536421d20c4a5b88ee0c019a4e699c2c75de077a20c82ba94` | `f89bf3884ff10a702aa117f2963e6fe9ea8aeac3a9bc003f52b6c5ca6abfbbd2` | `fixtures/mbc1-continuation/LICENSE.txt`: `dcd87663c88f74f55d61a403e752985e8bc63cfa1341d499bb7a521e22a91b20` |
| Libbet and the Magic Floor v0.08 test fixture | Third-party game, zlib; credits Damian Yerrick (program, 2018-2024) and Martin Korth (concept, 2002, 2012); `src/hardware.inc` in its build closure is CC0-1.0; per-asset rights rest on single-author history plus the repository-wide zlib licence, not a per-asset upstream grant; repository test fixture only, not installed or packaged | `fixtures/libbet/manifest.json`: `512d1b4de7656795dba07dc81b025593bd57a74288605eac88684da6b744f08a`; pinned upstream commit `46a765a2c01701bffb8c0b7dd6e4be3a6b193090` | `3607412031c8287cf878299ce96e581e85b852dde703806343b95576fa3ff1a9` | `fixtures/libbet/LICENSE.txt`: `e4fb3c0ef61a0258517e2df3dea5cd7df9d2a2f2c51c9b5082de922b35eea65c` |

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
