# Release, downloads, and recovery

GabbaBoy v0.1 is a limited, bootless DMG-CPU-B software preview. Find the
current candidate or published release under the repository's GitHub Releases
page. The release notes identify the version and list assets. The package
matrix is Linux x64, macOS arm64, and Windows x64 core archives; the optional
SDL3 player archive is macOS arm64 only. These are tested runner/configuration
combinations, not minimum OS versions, all-architecture promises, or general
platform support floors. The C core itself has no SDL runtime dependency.

## Verify and unpack

Download the asset for your runner and its matching `.sha256` file where
provided. Check it before extraction (for example,
`sha256sum --check gabbaboy-core-macos-arm64.tar.gz.sha256`; use the platform's
SHA-256 utility on macOS/Windows). The release's candidate/platform manifest,
build receipts, and `support-ledger-v0.1.0.json` provide additional provenance;
compare each asset name and digest with the downloaded bytes. The support
sidecar is generated after the tag. It records the exact source SHA and the
Git blob digest of the tagged
[`docs/support/v0.1.0.md`](support/v0.1.0.md), plus fixture and corpus identity.
The source ledger intentionally does not contain its future commit SHA, so its
own source can be reviewed before tagging without a self-reference.

Extract an archive into a new directory. Keep the core's `include`, `lib`, and
CMake package metadata together; configure consumers with
`-DCMAKE_PREFIX_PATH=<that-prefix>` and link `GabbaBoy::core`. The installed C
example in [`native-integration.md`](native-integration.md) shows instance
ownership, half-dot bounded execution, timestamped input, caller-owned frame
and audio buffers, and host-managed battery import/export. It is designed to
build and run outside the source and build trees. For source builds, follow the
top-level [build instructions](../README.md); SDL is only needed for the
optional player.

## Trust and macOS launch state

The macOS player is a command-line `.tar.gz` package, not a disk-image installer
or signed app bundle. The release is unsigned and not notarized unless its
release record explicitly reports successful verification of the exact final
bytes. A successful compile or smoke test does not establish Apple signing or
notarization. macOS security policy may warn or refuse execution of a
downloaded unsigned binary. Do not disable Gatekeeper globally. If policy
blocks the binary, use a locally built trusted binary or request a properly
signed release; the project does not claim a universal bypass procedure.

The package smoke uses SDL dummy audio/video and an offscreen software renderer.
It exercises the documented software path, including guest input, frame/audio
delivery, and save continuation; it does not establish physical-device,
perceptual, or hardware equivalence.

## Saves, upgrades, rollback, and recovery

The C core owns emulated cartridge RAM only. The embedding host owns save-file
location, format, validation, backup, and atomic replacement. The example
documents these responsibilities and transfers exactly the byte count
reported by `gbb_battery_size`; the core does not read or write files.

The SDL player stores identity-bound battery saves in its per-user preferences
directory. Before an upgrade, quit the player cleanly and back up that
application's save directory. Keep the backup until the new version opens the
same ROM and confirms progress. If rolling back, quit first and restore the
matching backup; do not run two writers against one save. The player's save
envelope is versioned and tied to the exact ROM bytes. A malformed or
wrong-identity save is preserved under a recovery name when safe preservation
succeeds; the player starts with fresh RAM and shows a warning instead of
silently importing it. Recovery files are not automatically loaded. See
[`cartridge-and-saves.md`](cartridge-and-saves.md) for the envelope and
recovery limits.

If a final save fails, the player pauses quit, reset, or ROM replacement and
offers retry, continue without saving, or cancel. Continuing without saving
may lose recent progress. Cancel keeps the session available for another save
attempt. See [`preview.md`](preview.md) for controls and player behavior.

## Support and troubleshooting

The versioned [support ledger](support/v0.1.0.md) records the bootless
DMG-CPU-B profile, ROM-only and documented standard MBC1 scope, eligible
derived CPU/timer denominator, exclusions, and known issues. The three passed
derived cases are a small scoped software corpus; they are not a game
compatibility percentage. There are no physical DMG observations, no CGB
qualification, and no broad game-library claim. Do not infer a minimum OS from
a runner label or one successful build.

- **Package not found by CMake:** point `CMAKE_PREFIX_PATH` at the extracted
  install prefix and keep its directory layout intact.
- **ROM rejected:** check the exact supported cartridge scope in
  [`cartridge-and-saves.md`](cartridge-and-saves.md); the file picker filter is
  not a compatibility promise.
- **No player audio:** check the player status/help. If no output device opens,
  the player discards and counts PCM while guest execution continues. Dummy
  audio is only a test backend.
- **Save warning or lock conflict:** close other GabbaBoy processes. Copy any
  recovery file before inspecting it; malformed records are not auto-loaded.
  Do not replace a save while another process is using it.
- **Unsigned player blocked:** use a local trusted build or await a signed
  release. Do not disable system security globally.
- **Unexpected behavior:** retain the version, platform, asset name and
  checksum, and report the issue through the repository's normal issue
  process. Never attach commercial ROMs, save files containing private data,
  or secrets.

The version PR is the final review point for `CHANGELOG.md`; release-please may
update it there. The merged, tagged changelog and that tag's release notes are
the public notes. The candidate is kept as one unpublished draft while exact
tag bytes are built, attached, downloaded, and smoked. Publication is a single
gated transition after all required checks and downloaded-byte tests pass.
Retries can reuse only that same draft, tag, source SHA, and previously
qualified byte-identical assets.
