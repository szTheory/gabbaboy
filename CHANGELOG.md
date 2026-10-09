# Changelog

## [0.1.0](https://github.com/szTheory/gabbaboy/releases/tag/v0.1.0) (2026-10-09)


### Features

* **01-01:** run original guest RAM tracer through core ([1e22f70](https://github.com/szTheory/gabbaboy/commit/1e22f709356a159206919d4991241f3ff3981db6))
* **01-02:** lock instance lifecycle and run bounds ([410ffd8](https://github.com/szTheory/gabbaboy/commit/410ffd852de6c54217a3ddd9a7bdfc9d6a022ac4))
* **01-02:** reject malformed ROMs and distinguish tracer outcomes ([c69fd16](https://github.com/szTheory/gabbaboy/commit/c69fd162eea188bc9a3069324ca4e7f32ec06aa7))
* **01-05:** add smoke-qualified preview package pipeline ([8d536a6](https://github.com/szTheory/gabbaboy/commit/8d536a6eee6570dae164e7a5c1075725b0c565f2))
* **02-03:** execute CB BIT and RES memory operations ([d56d411](https://github.com/szTheory/gabbaboy/commit/d56d4113053b4c0395c2c843ef24a07443ec7875))
* **02-03:** implement full CB opcode semantics ([180042c](https://github.com/szTheory/gabbaboy/commit/180042cb77c6b8749a3748b221c7609dd48e59b4))
* **02-04:** complete bounded CPU control states ([83ca2f7](https://github.com/szTheory/gabbaboy/commit/83ca2f768c4ea12bd7ca7b4e9b80942ad871317e))
* **02-04:** dispatch timed prioritized interrupts ([0575bf1](https://github.com/szTheory/gabbaboy/commit/0575bf14aa05dedc1c4f1b224b24e6e37c519c90))
* **02-05:** model timer collisions and disconnected serial ([2754cac](https://github.com/szTheory/gabbaboy/commit/2754cac0188b616f3018c2cc564b1acdba2bfe2e))
* **02-05:** process timer edges on timed CPU phases ([be3ccf3](https://github.com/szTheory/gabbaboy/commit/be3ccf3297373408359cc549f3d1b73d1724045c))
* **02-06:** advance stopped time to timestamped wake ([f71d445](https://github.com/szTheory/gabbaboy/commit/f71d445f4924f5d7e1f1f8b71046538a5fad983e))
* **02-08:** add bounded diagnostic receipts and manifest case runner ([060dace](https://github.com/szTheory/gabbaboy/commit/060daced7ad9bbfc0d25522db646b1710a72a588))
* **02-08:** qualify complete bounded Mooneye corpus ([4d3115e](https://github.com/szTheory/gabbaboy/commit/4d3115e8944262686e4944575295691ab9df2180))
* **03-01:** render timed BG frames and polling input ([60f6498](https://github.com/szTheory/gabbaboy/commit/60f6498f1f2e8228bf1ac78455eafd945e537625))
* **03-12:** allow active DMA FF46 restart and readback ([bb9f59d](https://github.com/szTheory/gabbaboy/commit/bb9f59d513b0b418c3bfc6381c351be52ff13e5a))
* **06-02:** qualify macOS and Windows release archives ([b429b4e](https://github.com/szTheory/gabbaboy/commit/b429b4ece00624a65f2e8a3a9e65d8f6e7839106))
* **06-05:** add bounded compiler-integrated fuzzing ([61074d6](https://github.com/szTheory/gabbaboy/commit/61074d6097804a39b69f4f6c50b2c6f8ee9b5bf8))
* **3-13:** model per-object DMA PPU interactions ([4435f45](https://github.com/szTheory/gabbaboy/commit/4435f456d812279d4c73f4f6aa5d2c3b3acd4a8c))
* **3-13:** request IF on selected JOYP falling edges ([00bfceb](https://github.com/szTheory/gabbaboy/commit/00bfceb6c716581b362563c7488106d059c5d893))
* **GB-01-03:** install relocatable core package ([b32ef4a](https://github.com/szTheory/gabbaboy/commit/b32ef4af97205ef61e7aebb71f08b8b78bd0ded8))
* **GB-01-03:** verify relocated C and C++ consumers ([775444f](https://github.com/szTheory/gabbaboy/commit/775444fd42959499baa4e63715040b6139d317ed))
* **GB-01-04:** add fixture reproducibility gate ([918d555](https://github.com/szTheory/gabbaboy/commit/918d555d2f8551326068c2d1cec02e43d75ea55f))
* **GB-01-04:** require native CI evidence ([c8007a7](https://github.com/szTheory/gabbaboy/commit/c8007a751432b6b3d1912df56992acb7b2fb2e6a))
* **GB-02-01:** implement bounded ROM-only memory bus ([dbeb0fb](https://github.com/szTheory/gabbaboy/commit/dbeb0fbd6c42c9c983f3927a23c5d36af096314f))
* **GB-02-01:** move tracer protocol into WRAM ([7b58f89](https://github.com/szTheory/gabbaboy/commit/7b58f895c669985f5c2cb1f45b0fe38514f7a6b8))
* **GB-02-02:** execute conditional call stack path ([6a972fe](https://github.com/szTheory/gabbaboy/commit/6a972feb847c5e5c9ed6254dc41aedc904fb9bba))
* **GB-02-02:** implement base opcode execution and lockup ([e7c55ce](https://github.com/szTheory/gabbaboy/commit/e7c55cef0db2b7a87cb15b9f91668c531690f5e7))
* **GB-02-07:** add source-qualified timer diagnostics ([a26c59e](https://github.com/szTheory/gabbaboy/commit/a26c59e42143831cebf34bf5b1812df13f04626d))
* **GB-02-07:** admit source-qualified CPU diagnostic fixture ([4f03896](https://github.com/szTheory/gabbaboy/commit/4f038960add48c47a4a7860fd0a5a50ba330b27c))
* **GB-02-13:** diagnose pinned Mooneye byte reproduction ([6afd54b](https://github.com/szTheory/gabbaboy/commit/6afd54ba713501118cf8dfc2e2e30a9fc46bcd55))
* **GB-02-16:** qualify admitted Mooneye runner results ([0e38a7a](https://github.com/szTheory/gabbaboy/commit/0e38a7ac48c4134ad02f6e6a23a77e01a325d4d6))
* **GB-02-17:** admit qualified Mooneye candidates ([b088b3e](https://github.com/szTheory/gabbaboy/commit/b088b3e145d61a72697fbdd04aaf8952058bdd6d))
* **GB-02-17:** pin deterministic Mooneye candidate recipe ([0a69676](https://github.com/szTheory/gabbaboy/commit/0a696767fb12eb07d01980dbeba35eb7e64f39f4))
* **GB-02-17:** verify hosted candidate byte identity ([e2bdaa5](https://github.com/szTheory/gabbaboy/commit/e2bdaa5197b7587a8514aaf638a732f343cd4c5a))
* **GB-03-02:** compose DMG background window and objects ([e5a16f6](https://github.com/szTheory/gabbaboy/commit/e5a16f68a2eec93c5491bfb1d6650ad7fc0d64b3))
* **GB-03-02:** model LCD and variable transfer timing ([2e1fdc8](https://github.com/szTheory/gabbaboy/commit/2e1fdc8bbf862133ca4c06ca3f50cc55a3accb87))
* **GB-03-03:** add bounded DMG OAM DMA ([d34d181](https://github.com/szTheory/gabbaboy/commit/d34d181f15def773587b991d20d652769f3ddfb4))
* **GB-03-03:** map timed VRAM and OAM accesses ([6bf7457](https://github.com/szTheory/gabbaboy/commit/6bf745760f5a3ec337ba987209d484df6d1abce4))
* **GB-03-05:** add optional SDL player smoke ([a5aae82](https://github.com/szTheory/gabbaboy/commit/a5aae825cc4233adb5476ec14616f9c756ef1cc9))
* **GB-03-05:** make player input timeline deterministic ([9ef104a](https://github.com/szTheory/gabbaboy/commit/9ef104ab9f4d9c159efacf79f40f462d5d60221a))
* **GB-03-06:** add ROM controls and integer presentation ([cd12a52](https://github.com/szTheory/gabbaboy/commit/cd12a52ee9d9b9015fbca1faef66d5a7a5340c31))
* **GB-03-07:** reject overlapping frame copy outputs ([cc316c3](https://github.com/szTheory/gabbaboy/commit/cc316c3bb94958f873576029f9f47ef38a44e653))
* **GB-03-09:** package optional macOS SDL player ([ee43cf9](https://github.com/szTheory/gabbaboy/commit/ee43cf975a13658aa1ee0be33a5b0567f641ff00))
* **GB-06-01:** qualify Linux release candidate ([5647ba0](https://github.com/szTheory/gabbaboy/commit/5647ba0c637658210a2e84d57243bf720bb032b5))
* **GB-06-01:** wire protected version PR draft release ([94cd5b6](https://github.com/szTheory/gabbaboy/commit/94cd5b6f6526272dbff0432aa7f67b1ca2f22313))
* **GB-06-03:** add relocated native C integration example ([04acbab](https://github.com/szTheory/gabbaboy/commit/04acbab6abcea0fe1b0fbe6929bd39fde6a8e4fd))
* **GB-06-04:** add reproducible release measurement receipt ([1011cd7](https://github.com/szTheory/gabbaboy/commit/1011cd7cf6680b474d6e70974f22812f114aa5ba))
* **GB-06-04:** add versioned support ledger verifier ([abbe52c](https://github.com/szTheory/gabbaboy/commit/abbe52c6efd91c78ae5e95631c0856e24c0f24a4))
* **GB-06-06:** gate exact-head checks and final publication ([ef523fe](https://github.com/szTheory/gabbaboy/commit/ef523fe01c1c823aa699f4434f7c31dfbcdb5d47))


### Bug Fixes

* **01-05:** harden exact hosted preview evidence ([e753da2](https://github.com/szTheory/gabbaboy/commit/e753da27f0393d58b39da30eab31f9ee71520657))
* **01-05:** honor forwarded executable suffix in package smoke ([2071ef3](https://github.com/szTheory/gabbaboy/commit/2071ef3bffb4d712a3748632c26c494e357c3343))
* **01-05:** normalize Windows test inventory line endings ([59b104e](https://github.com/szTheory/gabbaboy/commit/59b104ef5ba95f7dd48e6dd3f4732f49f4cc77de))
* **01:** CR-01 reject unsupported ROM sizes ([0d2579e](https://github.com/szTheory/gabbaboy/commit/0d2579e4c798facf8ccb22ad18400176c977a8e8))
* **01:** CR-02 safely extract preview packages ([809ee1a](https://github.com/szTheory/gabbaboy/commit/809ee1a53047e4086e471acd3a4739c78258a9ef))
* **01:** WR-01 verify RGBDS release digest ([7ba40dc](https://github.com/szTheory/gabbaboy/commit/7ba40dc8f3daf630d8a497b194f71e5a62066bc5))
* **01:** WR-02 bound package archive extraction ([da58af3](https://github.com/szTheory/gabbaboy/commit/da58af35180cb7fb5d0227ae4027066a041cf1b0))
* **01:** WR-02 cap tar parser decompression ([000f3a7](https://github.com/szTheory/gabbaboy/commit/000f3a7fa3c2b1f040e5057a3f21529de7460921))
* **01:** WR-03 bound archive path depth ([a34b990](https://github.com/szTheory/gabbaboy/commit/a34b99015cf3398e71a25a4520902caa1cbd6b18))
* **01:** WR-04 create private evidence staging directory ([784b7ca](https://github.com/szTheory/gabbaboy/commit/784b7ca2a0c56eb832de22d96179d1836b807d7d))
* **02-10:** place return stack reads on opcode phases ([3066a56](https://github.com/szTheory/gabbaboy/commit/3066a5665164363c849f9f045c0563c401de6f18))
* **02-10:** select post-boot flags from ROM checksum ([e08b160](https://github.com/szTheory/gabbaboy/commit/e08b160aae6817e7d7b66b22977754155261c0c5))
* **02:** preflight all guest reads and sample HALT wake cycles ([2af612c](https://github.com/szTheory/gabbaboy/commit/2af612ce83c6d2f36baed348664c34df82272950))
* **02:** preserve required tracer fixture reproduction ([d6e6aee](https://github.com/szTheory/gabbaboy/commit/d6e6aeef350522d4d0e7f8db421de883b42b2158))
* **02:** reject failed inventories and expose corpus qualification gap ([c583e33](https://github.com/szTheory/gabbaboy/commit/c583e338a48f70e83573da700722dcbefa4b705a))
* **03-12:** preserve the first DMA startup cycle ([a1a084a](https://github.com/szTheory/gabbaboy/commit/a1a084a3e961276abb0e2495d35be40ae0b77679))
* **03-13:** reset OAM scan cursor ([eb31afd](https://github.com/szTheory/gabbaboy/commit/eb31afd002133fa48e78a57c56a21e0b9f3a732c))
* **03-13:** sample final OAM entry ([e66afee](https://github.com/szTheory/gabbaboy/commit/e66afeef30e369a883a6694748de962e6deb8094))
* **06-02:** force scripted SDL backends for player smoke ([619f7d1](https://github.com/szTheory/gabbaboy/commit/619f7d1b3fe19e13af5ba162b9443a8dc7601a67))
* **06-02:** include Linux provenance in platform manifest ([c3b584f](https://github.com/szTheory/gabbaboy/commit/c3b584fd1b9c1f6fc507bfc7f355f1b2fd7d1bcc))
* **06-02:** reuse qualified platform candidate bytes on retry ([087bc4b](https://github.com/szTheory/gabbaboy/commit/087bc4ba1aaaf842e30cb87503fe3045e9175902))
* **06-05:** bound fuzz decoder and replay minimized finding ([c73b6ef](https://github.com/szTheory/gabbaboy/commit/c73b6ef903b15ac2fe70d821ac828176f3a35fb1))
* **GB-02-07:** preserve source-based fixture exclusions ([7cedd9c](https://github.com/szTheory/gabbaboy/commit/7cedd9c8aecba9ea3ddd3458651d3b48dfaa0f86))
* **GB-02-11:** advance timer before interrupt IF diagnostic ([0e09138](https://github.com/szTheory/gabbaboy/commit/0e09138b093281b01e70a05023aca391d91c0102))
* **GB-02-11:** preserve pending EI enable across repeated EI ([d5414e7](https://github.com/szTheory/gabbaboy/commit/d5414e7f39f22500a621640bfb0a5572704fbb2a))
* **GB-02-12:** preserve manifest bytes and distinguish fixture failures ([22a0136](https://github.com/szTheory/gabbaboy/commit/22a0136dbe5da1a687a231bb1c3982dd07cba43a))
* **GB-02-16:** validate phase-required PR contexts ([8481d60](https://github.com/szTheory/gabbaboy/commit/8481d603b780af7889832ea3a8d3ad84d2439ba5))
* **GB-02-17:** fetch baseline blobs for original fixture diagnostics ([10c9766](https://github.com/szTheory/gabbaboy/commit/10c976615d993c289af2ea66f2c4d9bcb044b11c))
* **GB-02-17:** select exact push workflow evidence ([93647ac](https://github.com/szTheory/gabbaboy/commit/93647ac98b7f8437cc9640e3dec437bba4f11e9c))
* **GB-02:** bind candidate promotion to hosted evidence ([03a2291](https://github.com/szTheory/gabbaboy/commit/03a22919417303dc9df2906c4135bf5ff124e7aa))
* **GB-03-09:** restrict packaged SDL rpath ([fd62c48](https://github.com/szTheory/gabbaboy/commit/fd62c48d84b8339435fefd008147f0c06f696e0e))
* **GB-03-11:** enforce preview limitation metadata ([fb1b335](https://github.com/szTheory/gabbaboy/commit/fb1b335f2b941aaaad59c4c0d44917c47f825783))
* **GB-03-11:** honor default package verifier mode ([38d7ea4](https://github.com/szTheory/gabbaboy/commit/38d7ea4cc0af07cf4262113c0f6a662a6cfce3a1))
* **GB-03:** clarify bounded gap-plan scope ([c3ab6bf](https://github.com/szTheory/gabbaboy/commit/c3ab6bfa9ba06900821e13b3ef3e35a0d766172b))
* **GB-03:** expand CPU PPU DMA gap coverage ([02f4b26](https://github.com/szTheory/gabbaboy/commit/02f4b265aeabf1486d3c385b5c611f1d9c1a2da9))
* **GB-03:** revise DMA PPU contention gap plan ([c62bead](https://github.com/szTheory/gabbaboy/commit/c62beadd798e089c4d5da9e8794538073d770750))
* **GB-06-03:** keep native example to one instance ([3dfb7b1](https://github.com/szTheory/gabbaboy/commit/3dfb7b163539c104464480c4fbff6fc19cb03ed5))
* **GB-06-03:** reuse one instance across packaged fixtures ([cda6387](https://github.com/szTheory/gabbaboy/commit/cda638779c0be3a2835cf6b5448450782bc20272))
* **GB-06-04:** test source-bound sidecar mismatch rejection ([1caeb4a](https://github.com/szTheory/gabbaboy/commit/1caeb4a552999606808a78ea697980b614ad42fc))
* **GB-06-06:** bind hosted durations to exact PR head ([8ae17d5](https://github.com/szTheory/gabbaboy/commit/8ae17d5383066e899759133328869e41f4b78d6b))
* **GB-06-06:** link relocated example with sanitizer runtimes ([049db69](https://github.com/szTheory/gabbaboy/commit/049db694422b25540546de7d8a698f7aa81ea810))
* **GB-06-06:** repair release workflow gates ([d832194](https://github.com/szTheory/gabbaboy/commit/d832194639add4dec2e4da81db35176e9494ee16))


### Documentation

* **release:** define initial v0.1.0 bootstrap ([12dab69](https://github.com/szTheory/gabbaboy/commit/12dab69a821d0e820ba40e91eba86911371591ec))

## Changelog

Notable GabbaBoy changes are recorded here. The protected release-please version
pull request creates the numbered release section from merged commits; that
reviewed file and the release notes attached to the matching draft are the
source for the tagged release. Do not edit or publish a numbered entry outside
that version pull request. The first qualified release is v0.1.0; its initial
Release-As marker is a one-time bootstrap, and later versions follow merged
conventional commits.

## Unreleased

### Added

- A limited DMG-CPU-B software preview with a relocatable native C/C++ package,
  a macOS SDL3 player, and exact-byte release qualification.
- A versioned support ledger and release evidence that identify the scoped
  model, fixture/corpus revisions, tested runner combinations, and known limits.
- Consumer guidance for package use, host-owned battery data, recovery, and a
  future Playstead adapter seam.

### Scope and limitations

- The boot ROM is skipped. The preview does not claim physical DMG qualification,
  CGB support, broad game compatibility, minimum OS versions, or a stable ABI.
- The macOS player is distributed as a CLI tar archive. It is unsigned and not
  notarized unless the exact final artifact is separately verified otherwise.
- See [the release guide](docs/release.md) and the versioned
  [support ledger](docs/support/v0.1.0.md) for downloads, provenance, evidence,
  and exclusions.
