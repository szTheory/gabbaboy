# Acid2 controlled-composition fixture sources

This fixture builds the exact pinned dmg-acid2 v1.0 and cgb-acid2 v1.1 sources with a GabbaBoy-authored replacement glyph table. It retains only the unchanged footer and reference PNGs needed by the tests.

Pinned repositories: [dmg-acid2](https://github.com/mattcurrie/dmg-acid2/tree/dc2295408f881637ff69f784d8d93f3d2db30181) at `dc2295408f881637ff69f784d8d93f3d2db30181`; [cgb-acid2](https://github.com/mattcurrie/cgb-acid2/tree/fa5b7f86d6fb599f79e55169494d981a7af75a31) at `fa5b7f86d6fb599f79e55169494d981a7af75a31`; and [mgblib](https://github.com/mattcurrie/mgblib/tree/5d829bf2ffa1447dcfd63c5dab2c44488632617e) at `5d829bf2ffa1447dcfd63c5dab2c44488632617e`.

The upstream README credit is retained: “Håkon Wium Lie and Ian Hickson for creation of the original Acid2 web standards compliance test.” The two Acid2 repositories carry identical pinned root MIT notices; the mgblib code notice is also retained. D-207 accepts the root MIT grant for each exact `img/` tree as a bounded repository-level inference, not an image-specific upstream statement. This scope covers only these exact pinned sources and image trees.

The no-logo build uses pinned RGBDS `rgbfix -f hg` to set both checksums without inserting Nintendo's logo. The runner starts the guest at `0x0100`, so these emulator-only derivatives do not claim standard boot-ROM or hardware startup behavior.

The rights evidence input is the immutable project snapshot `508f37f191ec76506d75921e97430148f4909209` (`tests/data/v04-closeout.json`, 39,813 bytes, SHA-256 `e44695dc2b5efebdbc01aed9179466d25ac8f5a55bc99a8ce94217b4adf262f9`), with D-207 at `169c062cd97764e2cea4052ce285209e8a886ff0`.

The unreviewed `mgblib/src/old_skool_outline_thick.asm` font bytes are absent. `project/glyphs.asm` is project-authored; the patch replaces only the old font include with that file. Footer pixels and expected references remain source-bound. The comparisons establish controlled composition only; they do not establish glyph accuracy, mode-3 timing, hardware behavior, or additional model scope.

The reproduced DMG-CPU-B output is `6d3e5aca5f6d2ba31337ae61c1994e56f1780196c96cc645d54de378d39bbe82`; the CGB-CPU-E output is `62a93fce12ef60938eefce81d02113a75e1a52b2631aa3d6f16388dc697837e2`. Both are 32 KiB, have valid header/global checksums, start at `0x0100`, and keep all 48 logo-range bytes zero. RGBDS `rgbfix -f hg` sets the checksums without writing Nintendo logo bytes.

The masks are derived from pinned source positions and the LCD scroll schedule. DMG has 50 masked cells (3,200 masked and 19,840 compared pixels; mask SHA-256 `bfc6ae61c3ab4753ac5c11f5c5bac8a7d6d6873767737a72e6c5d31ae0937098`). CGB has 52 masked cells (3,328 masked and 19,712 compared pixels; mask SHA-256 `95219a5b1d6d5df70de9af7896cb9bc9c2194e133e1070c67e4414aa58d227a9`). The planned reference set covers DMG-on-DMG, DMG-on-CGB in DMG mode, and CGB-on-CGB. These are comparison scopes, not runtime outcomes; no Acid2 ROM has been run in the current admission lane.

`build-manifest.json` inside `derivatives.tar` records each member digest, the exact source/submodule pins, one-line source patches, glyph input, masks, reference/overlay identities, RGBDS binaries, and two clean build receipts. The outer generic `manifest.json` binds the archive and complete local MIT notice; `admission.commit` points to the immutable fixture snapshot commit.
