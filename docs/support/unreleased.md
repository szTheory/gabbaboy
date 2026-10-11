# GabbaBoy unreleased support-ledger entries

These entries are pending inclusion in the next versioned support ledger, `docs/support/v0.2.0.md`, which is authored with the v0.2.0 release in Phase 15. The release workflow binds only `docs/support/vX.Y.Z.md` files, so this file is not a release claim. The released `docs/support/v0.1.0.md` is unchanged.

## Libbet acceptance scope

- Libbet and the Magic Floor v0.08 has headless acceptance on the deterministic, bootless DMG-CPU-B software profile.
- This is one game. It is not a game-compatibility claim and not hardware qualification. See [Game acceptance](../game-acceptance.md) for the evidence classes, controls and limits.

## Player-platform limitation

- The packaged-player game smoke runs only in the macOS packaged player. Linux and Windows player packaging, and therefore Linux and Windows packaged-player game smoke, are not provided.
- Headless acceptance runs on Linux, macOS and Windows.

## Reproduction

- No hosted Libbet reproduction run exists yet. The reproduction workflow is dispatch-only and has not been dispatched from the default branch.

## Cartridge breadth (Phase 8)

- The core supports MBC2 (types `$05`/`$06`) and MBC5 (types `$19`-`$1E`) on the bootless DMG-CPU-B software profile, alongside ROM-only and standard MBC1. Evidence ledger: [MBC2 and MBC5 evidence](../mbc2-mbc5-evidence.md).
- The Mooneye emulator-only mbc2 (7 of 7) and mbc5 (8 of 8) test ROMs, built from revision `31510e12eea6286d36eea060a6adde755e1067aa`, pass on that profile. The upstream results are author-attested hardware results; here they run on the software profile. They are test-ROM pass counts, not game compatibility, and do not cover CGB, MBC5 RAM or the rumble line.
- The core's ROM length bound is 8 MiB for MBC5 types only; every other type keeps its 2 MiB ceiling and error result. The player's own file bound stays 2 MiB.
- `gbb_rumble_state` exposes the MBC5 rumble line and a saturating transition count. No host haptics exist in the player or runner, and no physical rumble behavior is claimed.
- Player persistence gap: the player runs MBC2 `$06` and MBC5 `$1B`/`$1E` battery cartridges without saving progress and says so in its status and on stderr (the status line has no automated UI test). Saving them is CART-06, planned for Phase 9.
- MBC2 battery images are a canonical 512 bytes; import normalises upper nibbles, and packed 256-byte saves are unsupported.
- GitHub's automatically generated source archives include the `fixtures/mooneye-mbc` directory (about 17 MiB of test ROMs). The install tree and release packages do not contain it; no `export-ignore` is added in Phase 8 and the question is revisited at the release boundary.
