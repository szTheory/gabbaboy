# rtc3test fixture sources

## Upstream

- Project: rtc3test, https://github.com/aaaaaa123456789/rtc3test (aaaaaa123456789)
- Pinned commit: `80ae792bf1b3c3387929b912e6df001af3511e24`
- Release asset: `v004` `rtc3test.gb` (32768 bytes, header $147..$149 = `0F 00 00`)
- Licence: Unlicense; verbatim text from the pinned commit in `LICENSE.txt`

The repository tree at the pinned commit contains no ROM; the ROM is a release
asset only.

## Admitted bytes

| File | Size | SHA-256 |
|---|---|---|
| `rtc3test.gb` | 32768 | `a271013fb37ea1d927b854798401320b220d57abb3ca77f3d318ceb8a9def30d` |
| `tests.md` | 6877 | `1937b614b49cff4e2e9b3e36aaa888e754ece6eb141ce46406a28f8f005d4172` |

`rtc3test.gb` was downloaded from the v004 release into a fresh empty scratch
directory, checked for size, digest and header bytes, then copied.

`tests.md` is the upstream `tests.md` at the pinned commit, committed verbatim
and unmodified as the expectation source: every stated millisecond expectation
of the RTC oracle (Plan 09-12) is taken from it. `manifest.json` carries both
digests and is checked by `cmake/VerifyFixtureManifest.cmake`.

## Build identity of upstream

- Assembler: RGBDS v0.4.2, commit `ede982b50a68a6253ffbab17dc4184710b08032f`,
  built from source (no Linux binary release exists for this version).
- Upstream Makefile recipe:
  - `rgbasm -E -Wno-truncation -Wextra -Wshift-amount -p 0xff -h`
  - `rgblink -p 0xff`
  - `rgbfix -c -i RTC3 -j -k XX -m 0x0f -n 1 -p 0xff -r 0 -t MBC3RTCTEST -v`

## Rebuild status

Release bytes equal the rebuild: claimed. The hosted `rtc3test-repro` job in `.github/workflows/fixture-repro.yml` printed `result=byte-identical` in pull-request run 38189871131 at head `fb8972d9e30e6bdf5ff2038e4508ecd3ebfb8522` (read in Plan 09-18). A mismatch is reported, never replaced by rebuilt bytes.
