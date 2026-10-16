# Phase 14 unpublished evidence history sanitization

Five captured RED tracebacks contained personal workspace prefixes. Before publication, the unpublished commits were replayed with only those prefixes removed from captured output. Assertion text, target, exit status, expected/actual behavior and source fixture pins were preserved. Normal commit hooks remained enabled. The final tracked tree was byte-identical before and after replay; three pre-existing owner modifications were restored byte-for-byte. The previously published base `74bad9a53867584190e7be66c32d6c387b9f03b3` is unchanged. No published history was rewritten.

Top-level SUMMARY commit windows below use the sanitized ancestry so automated bounded-window checks remain reachable. Historical execution receipts retain the revision IDs on which those commands actually ran; this table is a correspondence, not a claim that tests ran again during replay. A fresh build, full stream, receipt and phase verification follow sanitization.

The original privacy RED was observed before the original data cleanup. Publication redaction also sanitizes its earlier inputs, so that historical private-data failure is not claimed reproducible from the sanitized public history. Its recorded failure and semantic assessment remain preserved, and current synthetic privacy negative controls independently prove rejection. No RED evidence was reconstructed.

| Original unpublished commit | Sanitized commit |
| --- | --- |
| `401b6e096d0781e7028471a64cd47b077b334f34` | `79c355060636e316be16316f7e699ad1c8732c6a` |
| `fb1b4d4d877a32ecf4bd7a37d56d7b350a4557ef` | `5f4c9bd9bdffbfd130f1dd5e36b5adf8a8b03f45` |
| `52cd2ec3a355c32afa8162e53a6ce2a813c489b4` | `3c3404f9a00ba70bc76374b557c8dc4b2b5bc08d` |
| `b0224028f3e77aad09e3cfd9e2164086cc90d134` | `4c927c4bf87dbabc41042c6757340d4e04f757ea` |
| `8b9bb46dc15a956374a737f18bd07255806c04b8` | `165eecff2ec88da05a4f1b06c819dbf7b27d2f4f` |
| `cc7a2cefd7b8d7961bc064a8629355725fdff9e3` | `e566a7fcd149ac7b6e801a61c0ed2ce15ca7044f` |
| `ef3b0c7ff18004ccccabe1879d522117ff163b71` | `e1022dd8e46ed7552d765b3b28fb5a89b9515cd9` |
| `b46bfc9e8a6ae5a8bd93d2289445bf5179080443` | `12b29fe7f516a684096f08040d03db29b8a5a6a4` |
| `85f72fa6c490bbab4fb70eeb6aab068f5802fc5d` | `6f1bd384b47be5cc4bd3f25c77dded57e82ec951` |
| `ddad93a2294ff9ee8ffd4200231c5055fca4fb49` | `98a075b0d61ded6e0c6d2d3364e1c73908907aff` |
| `048723cff5b686a8a7858ddb226fa36ce7cf5c94` | `cb54cc62c2985eaef63d4f6f2d820d21ddde1c09` |
| `dbef2383304d1c5f14063e996040be7ff246c0ce` | `a9b41f9e5c58f77caf21a31f7f758dd1c9c69cd6` |
| `3953b9429fe01d1ef8de4375df2818f24f7c91ba` | `ff3367ca22eac6f87cf8bbcb542264dd0c50bafe` |
| `e2850a5556d98035372409a65925902ff8770c2b` | `abba5248f6a14a2b9e3d0d2affde85152206e65a` |
| `5f4b6b805fbe93d98dd384342e41b9926bf36150` | `05507d18e9c7214ec76fe62bd5fce72dcd795a29` |
| `a94b94cfc2951a8f8d8b631b5a5f7802e9ff2eee` | `7ef6b243fc802c6dfd0c294b2bbd176ca0f41b8b` |
| `d9a9bfaec6d81f801e131f0505a29c26d05daa37` | `f3827cc56b9198edc38d8f3c6215697ccbe9c662` |
| `8ae187324f101393b35153f1b180b769d4ecefc3` | `408eefdb8f81318c4d952916b14c18bd2e1e9b79` |
| `f035813fc4fab2539d5bf913b645f8bd214824c8` | `affaa4f28665e2e5a4c655cf67b199bf8088c37a` |
| `9a5134b75ab13805101cbb3ce9a2dd3ee6015b96` | `275e1271a5419d77a1f8e082f665bacad49f542b` |
| `7faab0d1289de913397aed000a1194d8275d28ae` | `027825c059d6c9b1fd2db689779ebd4aebef335b` |
| `4ca9346cba09f23d779c7aa6f3589036029a96ca` | `07c922529ab36ccae68c9099220eab1a099ec639` |
| `43b166833c6167d0f2dc93735c2f0a2f62c466c5` | `e1f708d665dea08a5387bb82ebb1a6d647312efe` |
| `8083b255c4145b27ae39226d298a951351467043` | `7721a5cefe05eaf4ce43188441ac82f8c42c61c3` |
| `65bcbbc5872f17322ebae998c0653b4849490f74` | `a9214214ef29050ef971fe3e50d5644f42495772` |
| `e5bd88f9ac63a69fc493d45f510d82ce56e2be6d` | `b78ba07c2f36d1fa837a90cbcd7d1d13742805d2` |
| `38c6a5bed69757cbd485657e14a0f32d305a8840` | `2f01e432e4627fbce3553a3bb6db91446c261117` |
| `0b03fd502d86040086f3dcd73aa58a0d46036609` | `2fd86f2063a2b0f7ce25607b19661e1b6edffe90` |
| `ef0394d976740daa066e6f4f968fd85400442f75` | `975175b3b27430d950e0c24f0b2a388d65a5f008` |
| `95da9af2360c374f7d267ec7ccf1db1434b1c12c` | `3e7b9b9eee94a2fb0765f25415dadcc15ce68b60` |
| `89c966e629b45531a3359e5f27b84de682e53761` | `71fe45985ec4f9d4945343e9306b24a662e11dea` |
| `64fc4880810f3208c1c3ae629001ad1dd094a923` | `d23aea501426825282dd6c1906de2d5bd55f949f` |
| `d963f75008071e09d5740dfcade638eb222bc467` | `8b1f120fa296ae1212bdf68e6147e0da3c5db47f` |
| `de43a64686c6c8a4ef596cccea2e0256a4fa2b34` | `bd0c1045358222f23d8d9cbbe62f0a10acf2813b` |
| `4ac2120ecf41f8b96e999f2adb89b816bd184123` | `30fcb3a9bb6b8ed36f3f4e29225807c298d3e993` |
| `fb85ec8dc4aac2bc8867fa98da62c12c08091d3c` | `3fe1338e0ec7897d2e42ea9c7b37873f74d3ef72` |
| `82a0dd5a65e98adf800618676c963e374579cc5a` | `3b50304b6169c5eb138178fd4dcbab03f4a77224` |
| `5a9c8ae35ec5191592b337ecab98d839aaedcfba` | `58fb19a237b9c270e5bb3b12c7457e42e5c4f8f0` |
| `6aa0609f63217651b5e08623a5236646a016073a` | `9b6a23f07c4e9317c9ac73e73ea731aa241acf2f` |
| `da8c20171c252aeca4c1f01611947c124a546d7d` | `c7ddb6aeaeec0e2b01ba891e683ef56ac7dda3e9` |
| `ffa2c9688048c06951d18f80b3612a633fbd9928` | `c1d819c76b633d4a6bd8beb540899cfee33a0e44` |
| `b4c6baabaf996fd8e2aaf1616efdedadb19d83c8` | `6c202462e8e58e78473297cca787691c7101c406` |
| `a8f2dfa801f5275c650818cd2d7896b054d024b3` | `7d51e0bad0c8eeb37ba97861a0f50996b906b091` |
| `591a189f39a3bf5756b19ed78fa1996926810d4c` | `4f5752e10b0cc8b5e4724ee5cf7e4cf4229fbdc9` |
| `9086e1de4a5e1e520cd3dc2c7dce352989df6d67` | `d3767a4b93af07c254bda1278cc968fe1583d718` |
| `24a579a74197a3563a3d1e54c479329bc0c2b02c` | `2a342083aec7e3b10503ed7c5e37583b7b1c26f9` |
| `019cb00fb6f62f6dac0ff085dfc8c1019209677e` | `e21112c259a10d1d6c6a049eddb852435104facc` |
| `50b28b1490201615185ce3b50c2d77427043ea02` | `3bf36f8324acdc59b3ec6fe8acf03479ab78dfd7` |
| `a332e67b6b570c4e47f79a83b28b943dbff7d4d9` | `b1ff601e665a45816a9606f1af5c5035e5ee8668` |
| `df80965da83799c2c109f1a7bbe7f99c09c28c49` | `725815334f8fc9700b692b59d0e10300e669f05a` |
| `b8ad34ac5f1928cb024fe3c1a4978b3821dd4c5f` | `585136a9b815dc08fc50354560d7c02f977b1d0b` |
| `6e40ab4115b828b388e7fe772844658c77cc3a80` | `f69dd9edda9c2ae6ef6816b59e624a745e6c7d05` |
| `b7a7f46cd2f705b863cd56a872819227a0b40b8d` | `0641099346aa9d9985e80293ca0c80e08eb0b8ec` |
| `cbfc64036cae7c0b98504c872b31b0245df9707d` | `8d843f69d9515a58eefe3e8dc832ed1d1124d56a` |
| `42ff03c2611d5704ee7d0ca410e7ec4803a60e0e` | `a29f8c92c84e072cb23775bdfecd88a8a839bc39` |
| `55d062f0a703a83bdd97eeb14abd783ac2e00dcf` | `8ba8c87de752d494875170a3797e68a07cbc1866` |
