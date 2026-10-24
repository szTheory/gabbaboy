# Changelog

## Unreleased

### Features

* **MBC3 and RTC (Phase 9):** the core loads MBC3 types `$0F`-`$13` with a deterministic real-time clock driven only by emulated time; MBC30 is rejected with `GBB_UNSUPPORTED_CARTRIDGE_VARIANT`.
* **API (append-only):** `gbb_rtc_catch_up(gbb_instance *, int64_t)` applies host wall-clock seconds to a timer cartridge, `GBB_NO_RTC` is appended after `GBB_NO_RUMBLE`, and `GBB_RTC_BLOCK_SIZE` (21) sizes the clock block. The signed catch-up signature is reviewable before the phase pull request merges (D-17); after a release it would break installed consumers.
* **Battery image:** timer cartridges (`$0F`, `$10`) export cartridge RAM followed by a versioned 21-byte clock block, and importing an image never advances the clock; other battery types and MBC1 images are unchanged.
* **Player persistence:** the macOS player saves MBC1, MBC2, MBC3 (with the game clock) and MBC5 battery cartridges, reads ROMs up to 8 MiB, and catches a timer cartridge's clock up from the save time on reopen. Save envelope version 2 is used for every battery type except MBC1 `$03`, whose v0.1 file is unchanged. Time spent paused while the player stays open is not recovered.

## [0.2.1](https://github.com/szTheory/gabbaboy/compare/v0.2.0...v0.2.1) (2026-10-24)


### Bug Fixes

* **15.1:** close GR-CR-01 and the gap re-review findings ([#97](https://github.com/szTheory/gabbaboy/issues/97)) ([79e20f3](https://github.com/szTheory/gabbaboy/commit/79e20f356ac953fa7dcd3aa5e2b7d96eb9b747e1))
* **15.1:** close review warnings WR-01..WR-07 and info findings ([#94](https://github.com/szTheory/gabbaboy/issues/94)) ([2d25a47](https://github.com/szTheory/gabbaboy/commit/2d25a47f1b05844b4da829aa9d0978f2cb348df1))
* accept the shipped product package layout and run trusted release verifiers on tagged data ([#74](https://github.com/szTheory/gabbaboy/issues/74)) ([08e7309](https://github.com/szTheory/gabbaboy/commit/08e7309aab699333d73f7ffeae58a5332133f242))

## [0.2.0](https://github.com/szTheory/gabbaboy/compare/v0.1.2...v0.2.0) (2026-10-20)


### Features

* **13-01:** implement bounded CGB HBlank HDMA tracer ([aab4a86](https://github.com/szTheory/gabbaboy/commit/aab4a865c325f21a86f0b989ee527eb202ce7e00))
* **13-02:** bound HDMA source maps and overflow ([b257ac8](https://github.com/szTheory/gabbaboy/commit/b257ac8d0400fbe325b2eb8859ad72e3a07855a3))
* **13-02:** implement bounded CGB HDMA policies ([736d785](https://github.com/szTheory/gabbaboy/commit/736d785bb1d16a57cc5ee5c0dd18377c9dfa0c20))
* **13-03:** add public CGB HALT and DMA guest tests ([8aee46a](https://github.com/szTheory/gabbaboy/commit/8aee46acfdaaa30e0ccc08facc8b2a308678fc2b))
* **13-03:** preserve HDMA and speed pause independently ([22a35ba](https://github.com/szTheory/gabbaboy/commit/22a35bade8550d8978fa67f154313cc965e96874))
* **13-05:** add bounded HDMA runtime fault pairs ([4f1e3df](https://github.com/szTheory/gabbaboy/commit/4f1e3dfcacdfc63d2eaf4bee31c5351006716449))
* **13-05:** enable runtime no-steal mask ([cebca68](https://github.com/szTheory/gabbaboy/commit/cebca682c86350a906b9d4220f4ed1273678608d))
* **13-06:** admit remaining SameSuite DMA cases ([3f6f58e](https://github.com/szTheory/gabbaboy/commit/3f6f58e5bc463e339157e6c89b22e8f5dba6802b))
* **13-06:** pin first SameSuite DMA fixture ([903dfff](https://github.com/szTheory/gabbaboy/commit/903dfffbee241cfb6fc4a0764c474d9dff6f1209))
* **13-07:** add source-derived Magen HDMA oracle ([75f4547](https://github.com/szTheory/gabbaboy/commit/75f4547ae58cab700fba83ee5b7385f9aac4751d))
* **13-07:** admit pinned Magen HDMA fixture ([d481d7b](https://github.com/szTheory/gabbaboy/commit/d481d7b1b6284648cbf53dd2d1c4bf26e45694cc))
* **13-08:** add reproducible original CGB HDMA guest ([af88ae4](https://github.com/szTheory/gabbaboy/commit/af88ae44be0d85d3d5db9642eb6e0c0a08890c8d))
* **13-08:** validate original HDMA fixture in player ([eb87c27](https://github.com/szTheory/gabbaboy/commit/eb87c27fb2abfa380342579b6f20eb6398faa30b))
* **13-09:** execute all CGB HDMA disposition cases ([12a5a63](https://github.com/szTheory/gabbaboy/commit/12a5a63eb1f4884eb742c12c20b66018c4e968ae))
* **13-09:** verify CGB HDMA tracer disposition ([293621b](https://github.com/szTheory/gabbaboy/commit/293621b40a42cef6e358a0fb5bea8dae3918ebfb))
* **13-10:** pin relocated consumer package resolution ([0cbac03](https://github.com/szTheory/gabbaboy/commit/0cbac03632ebeacc96f6b9a8f45c75d7ea0c2499))
* **13-10:** scan CGB DMA package boundaries ([d33d967](https://github.com/szTheory/gabbaboy/commit/d33d967ff6267201fef0033427a29514c5199c45))
* **13-11:** align player HDMA scope claims ([d271508](https://github.com/szTheory/gabbaboy/commit/d271508cee8c4740de782586d17e4c02481a1903))
* **13-11:** document bounded CGB HDMA behavior ([5774aca](https://github.com/szTheory/gabbaboy/commit/5774aca78ac92331af4174eb0229823addd49c33))
* **13-12:** close HDMA prohibition proof and lane inventory ([16c9d53](https://github.com/szTheory/gabbaboy/commit/16c9d534a834396c9eb2f0bcb4d904cfd3b833e1))
* CGB KEY1/STOP double-speed switching with bounded stalls ([#68](https://github.com/szTheory/gabbaboy/issues/68)) ([8091fb5](https://github.com/szTheory/gabbaboy/commit/8091fb591de7fb68e666be01d344f5f26ebedc5c))
* qualify CGB acceptance outcome, v0.2.0 support ledger and exact-tag release evidence ([#72](https://github.com/szTheory/gabbaboy/issues/72)) ([04fe3c6](https://github.com/szTheory/gabbaboy/commit/04fe3c61188851db5d68488fce731061ee3dedb3))
* qualify CGB-E model and corpus ([#71](https://github.com/szTheory/gabbaboy/issues/71)) ([c771b1b](https://github.com/szTheory/gabbaboy/commit/c771b1b9c143d7589f8bb40c163c2e9f89ca1168))


### Bug Fixes

* **13-04:** guard finite HDMA work against time overflow ([f8aeaca](https://github.com/szTheory/gabbaboy/commit/f8aeacae7b6a10888e90143d311e8f353ee7c196))
* **13-07:** preserve reproducer executable mode ([225a260](https://github.com/szTheory/gabbaboy/commit/225a260653ea3e0767dc51af3dedf8367ab01047))
* **13-11:** preserve double-speed support phrase ([074249a](https://github.com/szTheory/gabbaboy/commit/074249a8f85a0474f9d99ca6f5c5b75172426985))
* **13-12:** launch SameSuite self-check through bash on Windows ([7413a64](https://github.com/szTheory/gabbaboy/commit/7413a64a50ab9eac10039cb14fadc7bd66619ce4))
* **13-12:** pass configured bash to SameSuite self-check ([690c081](https://github.com/szTheory/gabbaboy/commit/690c081e3714aa1039263255d572b6d0d06dad8e))
* **13-12:** preflight claim subjects before semantic target ([4eab951](https://github.com/szTheory/gabbaboy/commit/4eab9514b350a0e8b506561619c1858f02d224fb))
* **13-12:** preserve HDMA fixture bytes on Windows ([e9bc47e](https://github.com/szTheory/gabbaboy/commit/e9bc47ed30f5eb4ee1303c06153303c2deb6bea3))
* **13-12:** scope premature Phase 14 detection ([0d5bb9c](https://github.com/szTheory/gabbaboy/commit/0d5bb9cbfc5dcc730c2d9ce45c6358b79154aaa9))
* **13-12:** strengthen missing requirement control ([41bb9bf](https://github.com/szTheory/gabbaboy/commit/41bb9bf9258f529e394ac14cf1396928281cdee0))
* **13:** accept verified execution handoff without advancing phase ([3cdcef2](https://github.com/szTheory/gabbaboy/commit/3cdcef2831ae71564b75186e976296275f59b68d))
* **13:** CR-01 validate exact PR check evidence ([ec54205](https://github.com/szTheory/gabbaboy/commit/ec54205aedcabc07b08e073b56aeec73d84cd1d7))
* **13:** reject unparsed UAT rows and conflicting handoffs ([eeb1ce9](https://github.com/szTheory/gabbaboy/commit/eeb1ce94dec208b1baf7b1aae1b4c966f1b290ee))
* **13:** require an exact completed stage for handoff routing ([0f1bb34](https://github.com/szTheory/gabbaboy/commit/0f1bb34340d8aa4a1c71cb5f913170dd9d3fa9da))
* **13:** WR-01 split player CGB help claims ([f052ea3](https://github.com/szTheory/gabbaboy/commit/f052ea3806bb34fc531bb176755bab99822de53f))
* bind the real fuzz receipt run id and rehearse the aggregate v0.2 evidence gate ([#73](https://github.com/szTheory/gabbaboy/issues/73)) ([4b092a9](https://github.com/szTheory/gabbaboy/commit/4b092a90fb1f50e76da83dfefcdf30c56369b693))
* **phase-13:** reject untested behavior and evidence inputs ([5459b7c](https://github.com/szTheory/gabbaboy/commit/5459b7ce227016b36e2e8f65172e97f5134e59f0))

## [0.1.2](https://github.com/szTheory/gabbaboy/compare/v0.1.0...v0.1.2) (2026-10-10)


### Bug Fixes

* **release:** bind the newest applicable support ledger for patch releases ([#59](https://github.com/szTheory/gabbaboy/issues/59)) ([c9d8026](https://github.com/szTheory/gabbaboy/commit/c9d802629583e9b01d0da95024c5dae2fea6c023))

## 0.1.1 (2026-10-10)

Not published: the v0.1.1 candidate failed its release gate. These fixes shipped in 0.1.2.


### Bug Fixes

* **GB-03:** assert rendered player input in smoke ([de96686](https://github.com/szTheory/gabbaboy/commit/de966868057c1fb5b3bca5b4cdac50cadf3bae57))
* **GB-03:** automate visible player input smoke ([#40](https://github.com/szTheory/gabbaboy/issues/40)) ([8c80d59](https://github.com/szTheory/gabbaboy/commit/8c80d5988da8ad2a5417ffd8b42c2e694ad903a6))
* **GB-03:** keep release verified output outside the checkout ([91d11d4](https://github.com/szTheory/gabbaboy/commit/91d11d4ea8a60fbaf3af274faee469cbb3a240b8))
* **GB-03:** never let withdrawal reporting mask publication errors ([8151a75](https://github.com/szTheory/gabbaboy/commit/8151a752df27a30a9121767c9271d31360ab1879))
* **GB-03:** preserve verified output directory contents ([e4edf31](https://github.com/szTheory/gabbaboy/commit/e4edf315909cb4d1068defe24e832b9f669d4be3))
* **GB-04:** reject blocking ROM special files ([#43](https://github.com/szTheory/gabbaboy/issues/43)) ([bce8564](https://github.com/szTheory/gabbaboy/commit/bce85641fe4ee7a7657bcf35aeedf8883c9af09b))
* **GB-05:** clarify save recovery keys and refresh verification ([bb8fd65](https://github.com/szTheory/gabbaboy/commit/bb8fd654d03969e3d207fcdc92c345cc60be3298))
* **GB-05:** clarify save recovery keys and refresh verification ([#45](https://github.com/szTheory/gabbaboy/issues/45)) ([2463a38](https://github.com/szTheory/gabbaboy/commit/2463a382be687cecaf5bf233645b1d0d4d5130b2))
* **GB-06:** accept unquoted runner.temp YAML values in the output contract ([320fcc5](https://github.com/szTheory/gabbaboy/commit/320fcc5c87359890ed429160e95994073ab2c719))
* **GB-06:** publish verified player artifacts as one set ([eb96902](https://github.com/szTheory/gabbaboy/commit/eb96902fd531b7a001e4fd7d429e5dc56f8cb2ee))

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
